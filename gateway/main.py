"""
Maha Gateway — FastAPI + Session Manager

Endpoints:
  POST /auth/login        Login and receive JWT token
  POST /session/start     Start a session (requires token)
  POST /session/end       End a session (requires token)
  POST /command           Send a command, receive SSE stream
  POST /command/approve   Submit approval decision

Environment variables:
  GATEWAY_SECRET_KEY      JWT signing secret (required in production)
  GATEWAY_TOKEN_EXPIRE_MINUTES  Token lifetime (default: 60)
  GATEWAY_ENV             "production" to disable dev defaults
  GATEWAY_USERS           JSON dict of {username: bcrypt_hash}
  GATEWAY_HOST            Bind host (default: 0.0.0.0)
  GATEWAY_PORT            Bind port (default: 8000)
  ORCHESTRATOR_URL        Orchestrator service URL (default: http://localhost:9000)
  REDIS_URL               Redis connection URL (optional)
  SESSION_TTL_SECONDS     Session lifetime in seconds (default: 3600)
"""

import asyncio
import json
import logging
import os
from typing import AsyncIterator

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from auth import JWTError, authenticate_user, create_access_token, decode_token
from models import (
    ApprovalRequest,
    CommandRequest,
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    SessionEndRequest,
    SessionStartResponse,
)
from session import (
    create_approval,
    create_session,
    delete_session,
    get_session,
    resolve_approval,
    wait_for_approval,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://localhost:9000")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Maha Gateway", version="1.0.0")
_bearer = HTTPBearer()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

async def _get_username(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    try:
        return decode_token(creds.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Invalid or expired token"},
        )


async def _require_session(session_id: str, username: str) -> dict:
    data = await get_session(session_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": "Session not found or expired"},
        )
    if data["username"] != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SESSION_FORBIDDEN", "message": "Session belongs to another user"},
        )
    return data


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    if not authenticate_user(req.username, req.password):
        logger.warning("Failed login attempt for user=%s", req.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_FAILED", "message": "Invalid username or password"},
        )
    token = create_access_token(req.username)
    logger.info("User logged in: %s", req.username)
    return LoginResponse(token=token)


@app.post("/session/start", response_model=SessionStartResponse)
async def session_start(username: str = Depends(_get_username)):
    session_id = await create_session(username)
    logger.info("Session started: user=%s session=%s", username, session_id)
    return SessionStartResponse(session_id=session_id)


@app.post("/session/end", status_code=status.HTTP_204_NO_CONTENT)
async def session_end(
    req: SessionEndRequest,
    username: str = Depends(_get_username),
):
    await _require_session(req.session_id, username)
    await delete_session(req.session_id)
    logger.info("Session ended: user=%s session=%s", username, req.session_id)


@app.post("/command")
async def command(
    req: CommandRequest,
    username: str = Depends(_get_username),
):
    await _require_session(req.session_id, username)
    logger.info("Command received: user=%s session=%s cmd=%r",
                username, req.session_id, req.command[:80])

    return StreamingResponse(
        _stream_command(req.session_id, req.command, username),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/command/approve", status_code=status.HTTP_204_NO_CONTENT)
async def command_approve(
    req: ApprovalRequest,
    username: str = Depends(_get_username),
):
    await _require_session(req.session_id, username)
    await resolve_approval(req.session_id, req.approval_id, req.approved)
    logger.info("Approval resolved: session=%s approval=%s approved=%s",
                req.session_id, req.approval_id, req.approved)


# ---------------------------------------------------------------------------
# SSE streaming
# ---------------------------------------------------------------------------

async def _stream_command(
    session_id: str,
    command: str,
    username: str,
) -> AsyncIterator[str]:
    """Forward command to orchestrator and stream SSE response back."""
    payload = {
        "session_id": session_id,
        "command": command,
        "username": username,
    }

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{ORCHESTRATOR_URL}/run",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        yield f"{line}\n\n"
    except httpx.ConnectError:
        logger.error("Orchestrator unreachable at %s", ORCHESTRATOR_URL)
        error = json.dumps({
            "type": "error",
            "content": f"Orchestrator unavailable ({ORCHESTRATOR_URL})",
        })
        yield f"data: {error}\n\n"
    except httpx.HTTPStatusError as e:
        logger.error("Orchestrator error: %s", e)
        error = json.dumps({
            "type": "error",
            "content": f"Orchestrator returned {e.response.status_code}",
        })
        yield f"data: {error}\n\n"
    finally:
        yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("GATEWAY_HOST", "0.0.0.0")
    port = int(os.environ.get("GATEWAY_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=False)
