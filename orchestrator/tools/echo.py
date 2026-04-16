from typing import AsyncIterator
from .base import BaseTool


class EchoTool(BaseTool):
    name = "echo"
    slash_command = "/echo"
    description = "메시지를 그대로 반환합니다. 사용법: /echo <메시지>"
    requires_approval = False

    async def execute(self, args: str, session_id: str) -> AsyncIterator[str]:
        yield args if args else "(빈 메시지)"
