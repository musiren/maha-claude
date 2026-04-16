"""
JWT-based authentication.

Secret key and algorithm are configured via environment variables.
Users are loaded from GATEWAY_USERS env var (JSON format) or a default
dev-only credential (disabled in production via GATEWAY_ENV=production).
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("GATEWAY_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.environ.get("GATEWAY_TOKEN_EXPIRE_MINUTES", "60"))
GATEWAY_ENV = os.environ.get("GATEWAY_ENV", "development")


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


# Users loaded from environment: JSON dict of {username: bcrypt_hashed_password}
# Generate hash: python3 -c "import bcrypt; \
#   print(bcrypt.hashpw(b'mypassword', bcrypt.gensalt()).decode())"
_USERS: dict[str, str] = {}

_raw = os.environ.get("GATEWAY_USERS", "")
if _raw:
    try:
        _USERS = json.loads(_raw)
    except json.JSONDecodeError:
        logger.error("GATEWAY_USERS is not valid JSON — no users loaded")

# Dev-only fallback: admin/admin (disabled in production)
if not _USERS and GATEWAY_ENV != "production":
    _USERS = {
        "admin": _hash_password("admin"),
    }
    logger.warning("Using default dev credentials (admin/admin). "
                   "Set GATEWAY_USERS in production.")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def authenticate_user(username: str, password: str) -> bool:
    hashed = _USERS.get(username)
    if not hashed:
        return False
    return verify_password(password, hashed)


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    """Return username or raise JWTError."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub", "")
    if not username:
        raise JWTError("Missing subject")
    return username
