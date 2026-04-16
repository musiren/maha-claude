"""
Orchestration engine.

Supports two command formats:
  /COMMAND [args]  — slash command (e.g. /echo hello)
  COMMAND [args]   — plain command (e.g. echo hello)

Adding a new command:
  1. Create orchestrator/tools/my_tool.py extending BaseTool
  2. Set name, slash_command, description on the class
  3. Add it to ALL_TOOLS in orchestrator/tools/__init__.py
"""

import json
import logging
from typing import AsyncIterator, Dict, List, Tuple

from approval import approval_manager
from policy import is_blocked, requires_approval
from tools import ALL_TOOLS
from tools.base import BaseTool
from tools.help_tool import HelpTool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Registry builder
# ---------------------------------------------------------------------------

def _build_registries() -> Tuple[Dict[str, BaseTool], Dict[str, BaseTool]]:
    """
    Returns (plain_registry, slash_registry).

    plain_registry  : {"echo": EchoTool(), ...}
    slash_registry  : {"/echo": EchoTool(), ...}
    """
    plain: Dict[str, BaseTool] = {}
    slash: Dict[str, BaseTool] = {}

    for tool_cls in ALL_TOOLS:
        tool = tool_cls()
        if tool.name:
            plain[tool.name] = tool
        if tool.slash_command:
            slash[tool.slash_command] = tool

    # HelpTool is special: it needs the slash registry for display
    help_tool = HelpTool(slash)
    plain[help_tool.name] = help_tool
    slash[help_tool.slash_command] = help_tool

    return plain, slash


_PLAIN, _SLASH = _build_registries()


def get_slash_commands() -> List[dict]:
    """Return slash command metadata for external consumers (e.g. gateway)."""
    return [
        {
            "command": cmd,
            "description": tool.description,
            "requires_approval": tool.requires_approval,
        }
        for cmd, tool in sorted(_SLASH.items())
    ]


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _sse_text(content: str) -> str:
    return f'data: {json.dumps({"type": "text", "content": content})}\n\n'


def _sse_approval(approval_id: str, message: str) -> str:
    return f'data: {json.dumps({"type": "approval", "approval_id": approval_id, "message": message})}\n\n'


def _sse_error(message: str) -> str:
    return f'data: {json.dumps({"type": "error", "content": message})}\n\n'


# ---------------------------------------------------------------------------
# Command parsing
# ---------------------------------------------------------------------------

def _parse_command(command: str) -> Tuple[str | None, BaseTool | None, str]:
    """
    Parse command string into (matched_key, tool, args).

    Slash commands (/echo) are looked up first.
    Falls back to plain name matching.
    Returns (None, None, command) if no match.
    """
    cmd = command.strip()
    cmd_lower = cmd.lower()

    # Try slash registry first
    registry = _SLASH if cmd_lower.startswith("/") else _PLAIN

    for key in sorted(registry.keys(), key=len, reverse=True):
        if cmd_lower == key or cmd_lower.startswith(key + " "):
            args = cmd[len(key):].strip()
            return key, registry[key], args

    return None, None, cmd


# ---------------------------------------------------------------------------
# Engine entry point
# ---------------------------------------------------------------------------

async def run(command: str, session_id: str, username: str) -> AsyncIterator[str]:
    """Main entry point — yields SSE-formatted strings."""

    command = command.strip()
    logger.info("Run: user=%s session=%s cmd=%r", username, session_id, command[:80])

    # Blocked commands
    if is_blocked(command):
        yield _sse_error(f"명령이 정책에 의해 차단됐습니다: {command!r}")
        yield "data: [DONE]\n\n"
        return

    # Tool selection
    key, tool, args = _parse_command(command)

    if tool is None:
        yield _sse_error(
            f"알 수 없는 명령입니다: {command!r}\n"
            "'/help'를 입력하면 사용 가능한 명령어를 확인할 수 있습니다."
        )
        yield "data: [DONE]\n\n"
        return

    # Approval check
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

    # Execute
    try:
        async for chunk in tool.execute(args, session_id):
            yield _sse_text(chunk)
    except Exception as e:
        logger.exception("Tool execution error: %s", key)
        yield _sse_error(f"실행 오류: {e}")

    yield "data: [DONE]\n\n"
