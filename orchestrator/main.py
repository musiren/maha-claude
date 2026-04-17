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

import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from approval import approval_manager
from engine import get_slash_commands, run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def _load_orchestrator_config() -> dict:
    """Return orchestrator section from the nearest config.json."""
    script_dir = Path(__file__).parent
    for path in [script_dir.parent / "config.json", script_dir / "config.json"]:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("orchestrator", data)
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            logger.warning("config.json parse error: %s", e)
    return {}


_cfg = _load_orchestrator_config()

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


@app.get("/commands")
async def list_commands():
    """Return available slash commands and their metadata."""
    return get_slash_commands()


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("ORCHESTRATOR_HOST", str(_cfg.get("host", "0.0.0.0")))
    port = int(os.environ.get("ORCHESTRATOR_PORT", str(_cfg.get("port", 9000))))
    uvicorn.run("main:app", host=host, port=port, reload=False)
