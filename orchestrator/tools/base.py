"""Base class for all orchestrator tools."""

from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    requires_approval: bool = False

    @abstractmethod
    async def execute(self, args: str, session_id: str) -> AsyncIterator[str]:
        """Yield text chunks to stream back to the user."""
        ...
