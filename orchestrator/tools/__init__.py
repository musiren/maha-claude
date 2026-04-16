"""
Tool registry entry point.

To add a new slash command:
  1. Create orchestrator/tools/my_tool.py extending BaseTool
  2. Set name, slash_command, description on the class
  3. Add the class to ALL_TOOLS below — done.
"""

from .echo import EchoTool
from .status import StatusTool
from .test_runner import TestRunnerTool

# ─────────────────────────────────────────────────────────────
# ADD NEW TOOLS HERE
# ─────────────────────────────────────────────────────────────
ALL_TOOLS = [
    EchoTool,
    StatusTool,
    TestRunnerTool,
]
