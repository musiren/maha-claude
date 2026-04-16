"""
In-process approval manager using asyncio Events.

The orchestrator's /run endpoint pauses execution when approval is needed,
waiting for the gateway to call /approve once the user responds.
"""

import asyncio
import uuid
from typing import Dict

APPROVAL_TIMEOUT = 300.0  # seconds


class ApprovalManager:
    def __init__(self):
        self._events: Dict[str, asyncio.Event] = {}
        self._results: Dict[str, bool] = {}

    def create(self) -> str:
        approval_id = str(uuid.uuid4())
        self._events[approval_id] = asyncio.Event()
        self._results[approval_id] = False
        return approval_id

    async def wait(self, approval_id: str, timeout: float = APPROVAL_TIMEOUT) -> bool:
        event = self._events.get(approval_id)
        if not event:
            return False
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return False
        finally:
            self._events.pop(approval_id, None)
        return self._results.pop(approval_id, False)

    def resolve(self, approval_id: str, approved: bool):
        self._results[approval_id] = approved
        event = self._events.get(approval_id)  # don't pop — wait() cleans up
        if event:
            event.set()


# Singleton shared across the process
approval_manager = ApprovalManager()
