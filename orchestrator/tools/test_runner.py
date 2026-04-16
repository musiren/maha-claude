"""
TestRunnerTool: runs pytest in a subprocess and streams output line by line.

Requires approval before execution.
Working directory and pytest binary are configurable via environment variables.
"""

import asyncio
import logging
import os
from typing import AsyncIterator

from .base import BaseTool

logger = logging.getLogger(__name__)

PYTEST_BIN = os.environ.get("PYTEST_BIN", "/root/.local/bin/pytest")
TEST_ROOT = os.environ.get("TEST_ROOT", "/home/user/maha-claude")


class TestRunnerTool(BaseTool):
    name = "run tests"
    description = "pytest를 실행합니다. 사용법: run tests [경로]"
    requires_approval = True

    async def execute(self, args: str, session_id: str) -> AsyncIterator[str]:
        target = args.strip() if args.strip() else TEST_ROOT

        yield f"pytest 실행 중: {target}\n\n"

        cmd = [PYTEST_BIN, "--tb=short", "-v", target]
        logger.info("Running: %s (session=%s)", " ".join(cmd), session_id)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=TEST_ROOT,
            )

            async for line in proc.stdout:
                yield line.decode(errors="replace")

            await proc.wait()
            rc = proc.returncode
            if rc == 0:
                yield "\n테스트 완료: 모두 통과했습니다.\n"
            else:
                yield f"\n테스트 완료: 일부 실패했습니다 (exit code {rc}).\n"

        except FileNotFoundError:
            yield f"오류: pytest를 찾을 수 없습니다 ({PYTEST_BIN})\n"
        except Exception as e:
            logger.exception("Test runner error")
            yield f"오류: {e}\n"
