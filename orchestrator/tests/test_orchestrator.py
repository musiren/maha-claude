"""
Tests for orchestrator: policy, engine routing, approval flow.
"""
import asyncio
import os
import pytest

os.environ.setdefault("ORCHESTRATOR_HOST", "0.0.0.0")
os.environ.setdefault("ORCHESTRATOR_PORT", "9000")

from policy import is_blocked, requires_approval
from approval import ApprovalManager
from engine import _parse_command, run


# ---------------------------------------------------------------------------
# Policy tests
# ---------------------------------------------------------------------------

class TestPolicy:
    def test_blocked_command(self):
        assert is_blocked("rm -rf /") is True
        assert is_blocked("drop database") is True

    def test_not_blocked(self):
        assert is_blocked("echo hello") is False
        assert is_blocked("help") is False

    def test_requires_approval(self):
        assert requires_approval("run tests") is True
        assert requires_approval("테스트 실행") is True
        assert requires_approval("deploy") is True

    def test_no_approval_needed(self):
        assert requires_approval("echo hello") is False
        assert requires_approval("help") is False

    def test_blocked_not_approval(self):
        # Blocked commands are NOT "requires approval" — they're denied outright
        assert requires_approval("rm -rf /") is False


# ---------------------------------------------------------------------------
# Command parsing tests
# ---------------------------------------------------------------------------

class TestParseCommand:
    def test_echo(self):
        name, args = _parse_command("echo hello world")
        assert name == "echo"
        assert args == "hello world"

    def test_help(self):
        name, args = _parse_command("help")
        assert name == "help"
        assert args == ""

    def test_run_tests(self):
        name, args = _parse_command("run tests client/")
        assert name == "run tests"
        assert args == "client/"

    def test_unknown(self):
        name, args = _parse_command("unknown command")
        assert name is None

    def test_case_insensitive(self):
        name, args = _parse_command("ECHO hello")
        assert name == "echo"


# ---------------------------------------------------------------------------
# Engine SSE output tests
# ---------------------------------------------------------------------------

async def _collect(gen) -> list[str]:
    return [chunk async for chunk in gen]


class TestEngine:
    def test_blocked_command_returns_error(self):
        chunks = asyncio.get_event_loop().run_until_complete(
            _collect(run("rm -rf /", "sess-1", "admin"))
        )
        combined = "".join(chunks)
        assert '"type": "error"' in combined
        assert "[DONE]" in combined

    def test_unknown_command_returns_error(self):
        chunks = asyncio.get_event_loop().run_until_complete(
            _collect(run("gibberish command xyz", "sess-1", "admin"))
        )
        combined = "".join(chunks)
        assert '"type": "error"' in combined

    def test_echo_returns_text(self):
        chunks = asyncio.get_event_loop().run_until_complete(
            _collect(run("echo hello", "sess-1", "admin"))
        )
        combined = "".join(chunks)
        assert "hello" in combined
        assert "[DONE]" in combined

    def test_help_returns_text(self):
        chunks = asyncio.get_event_loop().run_until_complete(
            _collect(run("help", "sess-1", "admin"))
        )
        combined = "".join(chunks)
        assert "echo" in combined
        assert "[DONE]" in combined

    def test_approval_required_command_sends_approval_event(self):
        """run tests without approval → approval event emitted, then timeout → cancelled."""
        async def _run():
            chunks = []
            async for chunk in run("run tests", "sess-2", "admin"):
                chunks.append(chunk)
                if "approval" in chunk:
                    break  # Stop after getting approval event
            return chunks

        chunks = asyncio.get_event_loop().run_until_complete(_run())
        combined = "".join(chunks)
        assert '"type": "approval"' in combined


# ---------------------------------------------------------------------------
# ApprovalManager tests
# ---------------------------------------------------------------------------

class TestApprovalManager:
    def test_create_and_resolve_approved(self):
        mgr = ApprovalManager()

        async def _test():
            approval_id = mgr.create()
            mgr.resolve(approval_id, True)
            result = await mgr.wait(approval_id, timeout=1.0)
            return result

        result = asyncio.get_event_loop().run_until_complete(_test())
        assert result is True

    def test_create_and_resolve_rejected(self):
        mgr = ApprovalManager()

        async def _test():
            approval_id = mgr.create()
            mgr.resolve(approval_id, False)
            result = await mgr.wait(approval_id, timeout=1.0)
            return result

        result = asyncio.get_event_loop().run_until_complete(_test())
        assert result is False

    def test_wait_timeout(self):
        mgr = ApprovalManager()

        async def _test():
            approval_id = mgr.create()
            return await mgr.wait(approval_id, timeout=0.1)

        result = asyncio.get_event_loop().run_until_complete(_test())
        assert result is False

    def test_unknown_approval_id(self):
        mgr = ApprovalManager()

        async def _test():
            return await mgr.wait("nonexistent-id", timeout=0.1)

        result = asyncio.get_event_loop().run_until_complete(_test())
        assert result is False
