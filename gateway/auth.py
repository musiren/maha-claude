"""
JWT-based authentication using pure Python (HMAC-SHA256).
No dependency on the cryptography package.

Users are loaded from GATEWAY_USERS env var (JSON: {username: bcrypt_hash})
or a dev-only default (admin/admin) when GATEWAY_ENV != "production".
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Optional

import bcrypt

logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("GATEWAY_SECRET_KEY", "change-me-in-production").encode()
TOKEN_EXPIRE_SECONDS = int(os.environ.get("GATEWAY_TOKEN_EXPIRE_MINUTES", "60")) * 60
GATEWAY_ENV = os.environ.get("GATEWAY_ENV", "development")


# ---------------------------------------------------------------------------
# JWT (HS256, pure Python)
# ---------------------------------------------------------------------------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


def create_access_token(username: str) -> str:
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url_encode(json.dumps({
        "sub": username,
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS,
    }).encode())
    signing_input = f"{header}.{payload}"
    sig = hmac.new(SECRET_KEY, signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(sig)}"


class JWTError(Exception):
    pass


def decode_token(token: str) -> str:
    """Return username or raise JWTError."""
    parts = token.split(".")
    if len(parts) != 3:
        raise JWTError("Malformed token")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}"

    expected_sig = hmac.new(SECRET_KEY, signing_input.encode(), hashlib.sha256).digest()
    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception:
        raise JWTError("Invalid signature encoding")

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise JWTError("Signature mismatch")

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        raise JWTError("Invalid payload")

    if payload.get("exp", 0) < time.time():
        raise JWTError("Token expired")

    username = payload.get("sub", "")
    if not username:
        raise JWTError("Missing subject")
    return username


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


_USERS: dict[str, str] = {}

_raw = os.environ.get("GATEWAY_USERS", "")
if _raw:
    try:
        _USERS = json.loads(_raw)
    except json.JSONDecodeError:
        logger.error("GATEWAY_USERS is not valid JSON — no users loaded")

if not _USERS and GATEWAY_ENV != "production":
    _USERS = {"admin": _hash_password("admin")}
    logger.warning("Using default dev credentials (admin/admin). "
                   "Set GATEWAY_USERS in production.")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def authenticate_user(username: str, password: str) -> bool:
    hashed = _USERS.get(username)
    if not hashed:
        return False
    return verify_password(password, hashed)
