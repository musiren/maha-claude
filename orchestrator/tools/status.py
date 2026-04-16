"""
StatusTool: shows current session information.
Example of a minimal slash-command tool.
"""

import time
from typing import AsyncIterator

from .base import BaseTool


class StatusTool(BaseTool):
    name = "status"
    slash_command = "/status"
    description = "현재 세션 상태를 표시합니다."
    requires_approval = False

    async def execute(self, args: str, session_id: str) -> AsyncIterator[str]:
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        yield (
            f"세션 상태\n"
            f"  session_id : {session_id}\n"
            f"  현재 시각  : {now}\n"
        )
