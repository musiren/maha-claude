from typing import AsyncIterator, Dict
from .base import BaseTool


class HelpTool(BaseTool):
    name = "help"
    slash_command = "/help"
    description = "사용 가능한 명령어 목록을 표시합니다."
    requires_approval = False

    def __init__(self, slash_registry: Dict[str, "BaseTool"]):
        self._registry = slash_registry

    async def execute(self, args: str, session_id: str) -> AsyncIterator[str]:
        lines = ["사용 가능한 슬래시 명령어:\n\n"]
        for slash_cmd, tool in sorted(self._registry.items()):
            approval_mark = " [승인 필요]" if tool.requires_approval else ""
            lines.append(f"  {slash_cmd:<18} {tool.description}{approval_mark}\n")
        lines.append("\n일반 명령어도 동일하게 지원됩니다 (예: echo, help, status).\n")
        yield "".join(lines)
