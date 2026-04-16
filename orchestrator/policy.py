"""
Policy engine: determines which commands require user approval.

Extend APPROVAL_KEYWORDS and BLOCKED_KEYWORDS as the system grows.
"""

# Commands matching these keywords require explicit user approval.
APPROVAL_KEYWORDS = [
    "run test", "run tests",
    "테스트 실행", "테스트 실행",
    "execute", "실행",
    "deploy", "배포",
    "delete", "삭제",
    "drop",
    "reset",
]

# Commands matching these are always blocked.
BLOCKED_KEYWORDS = [
    "rm -rf",
    "drop database",
    "format",
]


def is_blocked(command: str) -> bool:
    cmd = command.lower()
    return any(kw in cmd for kw in BLOCKED_KEYWORDS)


def requires_approval(command: str) -> bool:
    if is_blocked(command):
        return False  # Blocked, not just approval-needed
    cmd = command.lower()
    return any(kw in cmd for kw in APPROVAL_KEYWORDS)
