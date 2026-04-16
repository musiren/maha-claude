"""
Session store with Redis backend and in-memory fallback.

Each session stores:
  - username: str
  - created_at: float (unix timestamp)
  - pending_approval: optional dict with approval_id and asyncio.Event

Redis is used when REDIS_URL is set. Falls back to in-memory dict
with manual TTL enforcement (suitable for single-process deployments).
"""

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

SESSION_TTL = int(os.environ.get("SESSION_TTL_SECONDS", "3600"))
REDIS_URL = os.environ.get("REDIS_URL", "")

# ---------------------------------------------------------------------------
# Redis backend
# ---------------------------------------------------------------------------

_redis: Optional[object] = None

if REDIS_URL:
    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        logger.info("Session store: Redis at %s", REDIS_URL)
    except ImportError:
        logger.warning("redis package not installed — falling back to in-memory store")

# ---------------------------------------------------------------------------
# In-memory backend (single-process fallback)
# ---------------------------------------------------------------------------

# {session_id: {"username": str, "created_at": float}}
_store: dict[str, dict] = {}

# Approval events are always in-memory (not serialisable to Redis)
# {session_id: {approval_id: asyncio.Event}}
_approvals: dict[str, dict[str, asyncio.Event]] = {}
_approval_results: dict[str, dict[str, bool]] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def create_session(username: str) -> str:
    session_id = str(uuid.uuid4())
    data = {"username": username, "created_at": time.time()}

    if _redis:
        await _redis.setex(
            f"session:{session_id}",
            SESSION_TTL,
            json.dumps(data),
        )
    else:
        _store[session_id] = data
        _purge_expired()

    return session_id


async def get_session(session_id: str) -> Optional[dict]:
    if _redis:
        raw = await _redis.get(f"session:{session_id}")
        if not raw:
            return None
        return json.loads(raw)

    data = _store.get(session_id)
    if not data:
        return None
    if time.time() - data["created_at"] > SESSION_TTL:
        _store.pop(session_id, None)
        return None
    return data


async def delete_session(session_id: str):
    if _redis:
        await _redis.delete(f"session:{session_id}")
    else:
        _store.pop(session_id, None)
    _approvals.pop(session_id, None)
    _approval_results.pop(session_id, None)


async def create_approval(session_id: str) -> str:
    approval_id = str(uuid.uuid4())
    event = asyncio.Event()
    _approvals.setdefault(session_id, {})[approval_id] = event
    _approval_results.setdefault(session_id, {})[approval_id] = False
    return approval_id


async def wait_for_approval(session_id: str, approval_id: str,
                             timeout: float = 300.0) -> bool:
    event = _approvals.get(session_id, {}).get(approval_id)
    if not event:
        return False
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        return False
    return _approval_results.get(session_id, {}).get(approval_id, False)


async def resolve_approval(session_id: str, approval_id: str, approved: bool):
    results = _approval_results.setdefault(session_id, {})
    results[approval_id] = approved
    event = _approvals.get(session_id, {}).get(approval_id)
    if event:
        event.set()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _purge_expired():
    now = time.time()
    expired = [sid for sid, d in _store.items()
               if now - d["created_at"] > SESSION_TTL]
    for sid in expired:
        _store.pop(sid, None)
        _approvals.pop(sid, None)
        _approval_results.pop(sid, None)
