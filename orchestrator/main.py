"""
Maha Orchestrator

Endpoints:
  POST /run      Receive command from gateway, stream SSE response
  POST /approve  Receive approval decision from gateway
  GET  /health   Health check

Environment variables:
  ORCHESTRATOR_HOST   Bind host (default: 0.0.0.0)
  ORCHESTRATOR_PORT   Bind port (default: 9000)
  PYTEST_BIN          Path to pytest binary
  TEST_ROOT           Root directory for test runner
"""

import logging
import os

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from approval import approval_manager
from engine import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(title="Maha Orchestrator", version="1.0.0")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    session_id: str
    command: str
    username: str


class ApproveRequest(BaseModel):
    approval_id: str
    approved: bool


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/run")
async def run_command(req: RunRequest):
    return StreamingResponse(
        run(req.command, req.session_id, req.username),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/approve", status_code=204)
async def approve(req: ApproveRequest):
    approval_manager.resolve(req.approval_id, req.approved)


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("ORCHESTRATOR_HOST", "0.0.0.0")
    port = int(os.environ.get("ORCHESTRATOR_PORT", "9000"))
    uvicorn.run("main:app", host=host, port=port, reload=False)
