"""
Orchestration engine.

Receives a user command, selects the appropriate tool, checks policy,
requests approval if needed, then streams results.
"""

import json
import logging
from typing import AsyncIterator, Dict

from approval import approval_manager
from policy import is_blocked, requires_approval
from tools.base import BaseTool
from tools.echo import EchoTool
from tools.help_tool import HelpTool
from tools.test_runner import TestRunnerTool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

def _build_registry() -> Dict[str, BaseTool]:
    registry: Dict[str, BaseTool] = {}

    for tool in [EchoTool(), TestRunnerTool()]:
        registry[tool.name] = tool

    # HelpTool needs a reference to the registry itself
    registry["help"] = HelpTool(registry)
    return registry


_REGISTRY = _build_registry()


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _sse_text(content: str) -> str:
    return f'data: {json.dumps({"type": "text", "content": content})}\n\n'


def _sse_approval(approval_id: str, message: str) -> str:
    return (
        f'data: {json.dumps({"type": "approval", "approval_id": approval_id, "message": message})}\n\n'
    )


def _sse_error(message: str) -> str:
    return f'data: {json.dumps({"type": "error", "content": message})}\n\n'


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def _parse_command(command: str):
    """Return (tool_name, args) by matching the longest tool name prefix."""
    cmd = command.strip()
    cmd_lower = cmd.lower()

    # Match longest tool name first
    for name in sorted(_REGISTRY.keys(), key=len, reverse=True):
        if cmd_lower == name or cmd_lower.startswith(name + " "):
            args = cmd[len(name):].strip()
            return name, args

    return None, cmd


async def run(command: str, session_id: str, username: str) -> AsyncIterator[str]:
    """Main entry point — yields SSE-formatted strings."""

    command = command.strip()
    logger.info("Run: user=%s session=%s cmd=%r", username, session_id, command[:80])

    # --- Blocked commands ---
    if is_blocked(command):
        yield _sse_error(f"명령이 정책에 의해 차단됐습니다: {command!r}")
        yield "data: [DONE]\n\n"
        return

    # --- Tool selection ---
    tool_name, args = _parse_command(command)

    if tool_name is None or tool_name not in _REGISTRY:
        yield _sse_error(
            f"알 수 없는 명령입니다: {command!r}\n"
            "'help'를 입력하면 사용 가능한 명령어를 확인할 수 있습니다."
        )
        yield "data: [DONE]\n\n"
        return

    tool = _REGISTRY[tool_name]

    # --- Approval check ---
    if requires_approval(command) or tool.requires_approval:
        approval_id = approval_manager.create()
        msg = f"'{command}' 명령을 실행하려면 승인이 필요합니다."
        yield _sse_approval(approval_id, msg)

        approved = await approval_manager.wait(approval_id)
        if not approved:
            yield _sse_text("실행이 취소됐습니다.\n")
            yield "data: [DONE]\n\n"
            return

        yield _sse_text("승인됐습니다. 실행을 시작합니다.\n\n")

    # --- Execute tool ---
    try:
        async for chunk in tool.execute(args, session_id):
            yield _sse_text(chunk)
    except Exception as e:
        logger.exception("Tool execution error: %s", tool_name)
        yield _sse_error(f"실행 오류: {e}")

    yield "data: [DONE]\n\n"
