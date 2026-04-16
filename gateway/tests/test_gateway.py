"""
Tests for gateway/main.py

Uses FastAPI TestClient (synchronous) with mocked session store.
No real Redis or Orchestrator connections.
"""
import os
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# Set required env vars before importing app modules
os.environ.setdefault("GATEWAY_SECRET_KEY", "test-secret")
os.environ.setdefault("GATEWAY_ENV", "development")

from main import app
from auth import create_access_token

client = TestClient(app)


def _auth_header(username: str = "admin") -> dict:
    token = create_access_token(username)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# /auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self):
        resp = client.post("/auth/login", json={"username": "admin", "password": "admin"})
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_login_wrong_password(self):
        resp = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "AUTH_FAILED"

    def test_login_unknown_user(self):
        resp = client.post("/auth/login", json={"username": "nobody", "password": "x"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /session/start
# ---------------------------------------------------------------------------

class TestSessionStart:
    def test_start_session_success(self):
        with patch("main.create_session", new_callable=AsyncMock,
                   return_value="sess-abc"):
            resp = client.post("/session/start", headers=_auth_header())
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "sess-abc"

    def test_start_session_no_token(self):
        resp = client.post("/session/start")
        assert resp.status_code == 401

    def test_start_session_invalid_token(self):
        resp = client.post("/session/start",
                           headers={"Authorization": "Bearer bad.token.here"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /session/end
# ---------------------------------------------------------------------------

class TestSessionEnd:
    def test_end_session_success(self):
        session_data = {"username": "admin", "created_at": 0.0}
        with patch("main.get_session", new_callable=AsyncMock,
                   return_value=session_data), \
             patch("main.delete_session", new_callable=AsyncMock):
            resp = client.post("/session/end",
                               json={"session_id": "sess-abc"},
                               headers=_auth_header())
        assert resp.status_code == 204

    def test_end_session_not_found(self):
        with patch("main.get_session", new_callable=AsyncMock, return_value=None):
            resp = client.post("/session/end",
                               json={"session_id": "no-such"},
                               headers=_auth_header())
        assert resp.status_code == 404

    def test_end_session_wrong_user(self):
        session_data = {"username": "other_user", "created_at": 0.0}
        with patch("main.get_session", new_callable=AsyncMock,
                   return_value=session_data):
            resp = client.post("/session/end",
                               json={"session_id": "sess-abc"},
                               headers=_auth_header("admin"))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
