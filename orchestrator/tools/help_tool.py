from typing import AsyncIterator, Dict
from .base import BaseTool


class HelpTool(BaseTool):
    name = "help"
    description = "사용 가능한 명령어 목록을 표시합니다."
    requires_approval = False

    def __init__(self, registry: Dict[str, "BaseTool"]):
        self._registry = registry

    async def execute(self, args: str, session_id: str) -> AsyncIterator[str]:
        lines = ["사용 가능한 명령어:\n"]
        for name, tool in sorted(self._registry.items()):
            approval_mark = " [승인 필요]" if tool.requires_approval else ""
            lines.append(f"  {name:<16} {tool.description}{approval_mark}\n")
        yield "".join(lines)
