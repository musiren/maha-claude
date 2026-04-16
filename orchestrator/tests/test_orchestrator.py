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
from engine import _parse_command, get_slash_commands, run


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
        assert requires_approval("rm -rf /") is False


# ---------------------------------------------------------------------------
# Command parsing tests
# ---------------------------------------------------------------------------

class TestParseCommand:
    def test_plain_echo(self):
        _, tool, args = _parse_command("echo hello world")
        assert tool is not None
        assert tool.name == "echo"
        assert args == "hello world"

    def test_slash_echo(self):
        _, tool, args = _parse_command("/echo hello world")
        assert tool is not None
        assert tool.slash_command == "/echo"
        assert args == "hello world"

    def test_slash_help(self):
        _, tool, args = _parse_command("/help")
        assert tool is not None
        assert tool.slash_command == "/help"

    def test_slash_status(self):
        _, tool, args = _parse_command("/status")
        assert tool is not None
        assert tool.slash_command == "/status"

    def test_slash_run_tests(self):
        _, tool, args = _parse_command("/run-tests client/")
        assert tool is not None
        assert tool.slash_command == "/run-tests"
        assert args == "client/"

    def test_plain_run_tests(self):
        _, tool, args = _parse_command("run tests client/")
        assert tool is not None
        assert tool.name == "run tests"

    def test_unknown(self):
        _, tool, args = _parse_command("unknown command")
        assert tool is None

    def test_case_insensitive_slash(self):
        _, tool, args = _parse_command("/ECHO hello")
        assert tool is not None

    def test_case_insensitive_plain(self):
        _, tool, args = _parse_command("ECHO hello")
        assert tool is not None


# ---------------------------------------------------------------------------
# Slash command registry tests
# ---------------------------------------------------------------------------

class TestSlashCommandRegistry:
    def test_get_slash_commands_returns_list(self):
        cmds = get_slash_commands()
        assert isinstance(cmds, list)
        assert len(cmds) > 0

    def test_all_commands_have_required_fields(self):
        for cmd in get_slash_commands():
            assert "command" in cmd
            assert cmd["command"].startswith("/")
            assert "description" in cmd
            assert "requires_approval" in cmd

    def test_echo_registered(self):
        cmds = {c["command"] for c in get_slash_commands()}
        assert "/echo" in cmds

    def test_help_registered(self):
        cmds = {c["command"] for c in get_slash_commands()}
        assert "/help" in cmds

    def test_status_registered(self):
        cmds = {c["command"] for c in get_slash_commands()}
        assert "/status" in cmds

    def test_run_tests_requires_approval(self):
        cmds = {c["command"]: c for c in get_slash_commands()}
        assert cmds["/run-tests"]["requires_approval"] is True


# ---------------------------------------------------------------------------
# Engine SSE output tests
# ---------------------------------------------------------------------------

async def _collect(gen) -> list[str]:
    return [chunk async for chunk in gen]


class TestEngine:
    def test_blocked_command(self):
        chunks = asyncio.get_event_loop().run_until_complete(
            _collect(run("rm -rf /", "sess-1", "admin"))
        )
        combined = "".join(chunks)
        assert '"type": "error"' in combined
        assert "[DONE]" in combined

    def test_unknown_command(self):
        chunks = asyncio.get_event_loop().run_until_complete(
            _collect(run("gibberish xyz", "sess-1", "admin"))
        )
        combined = "".join(chunks)
        assert '"type": "error"' in combined

    def test_plain_echo(self):
        chunks = asyncio.get_event_loop().run_until_complete(
            _collect(run("echo hello", "sess-1", "admin"))
        )
        assert "hello" in "".join(chunks)
        assert "[DONE]" in "".join(chunks)

    def test_slash_echo(self):
        chunks = asyncio.get_event_loop().run_until_complete(
            _collect(run("/echo hello", "sess-1", "admin"))
        )
        assert "hello" in "".join(chunks)

    def test_slash_help(self):
        chunks = asyncio.get_event_loop().run_until_complete(
            _collect(run("/help", "sess-1", "admin"))
        )
        combined = "".join(chunks)
        assert "/echo" in combined
        assert "[DONE]" in combined

    def test_slash_status(self):
        chunks = asyncio.get_event_loop().run_until_complete(
            _collect(run("/status", "sess-1", "admin"))
        )
        combined = "".join(chunks)
        assert "sess-1" in combined

    def test_approval_required_sends_event(self):
        async def _run():
            chunks = []
            async for chunk in run("/run-tests", "sess-2", "admin"):
                chunks.append(chunk)
                if "approval" in chunk:
                    break
            return chunks

        chunks = asyncio.get_event_loop().run_until_complete(_run())
        assert '"type": "approval"' in "".join(chunks)


# ---------------------------------------------------------------------------
# ApprovalManager tests
# ---------------------------------------------------------------------------

class TestApprovalManager:
    def test_resolve_approved(self):
        mgr = ApprovalManager()

        async def _test():
            aid = mgr.create()
            mgr.resolve(aid, True)
            return await mgr.wait(aid, timeout=1.0)

        assert asyncio.get_event_loop().run_until_complete(_test()) is True

    def test_resolve_rejected(self):
        mgr = ApprovalManager()

        async def _test():
            aid = mgr.create()
            mgr.resolve(aid, False)
            return await mgr.wait(aid, timeout=1.0)

        assert asyncio.get_event_loop().run_until_complete(_test()) is False

    def test_wait_timeout(self):
        mgr = ApprovalManager()

        async def _test():
            return await mgr.wait(mgr.create(), timeout=0.1)

        assert asyncio.get_event_loop().run_until_complete(_test()) is False

    def test_unknown_id(self):
        mgr = ApprovalManager()

        async def _test():
            return await mgr.wait("nonexistent", timeout=0.1)

        assert asyncio.get_event_loop().run_until_complete(_test()) is False
