"""
Tests for client/main.py

All HTTP calls are mocked; no real network connections.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import Client


class TestLogin(unittest.TestCase):
    def test_login_success(self):
        client = Client()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"token": "test-token"}
        mock_resp.raise_for_status = MagicMock()

        with patch.object(client._http, "post", return_value=mock_resp):
            result = client.login("user", "pass")

        self.assertTrue(result)
        self.assertEqual(client._token, "test-token")
        self.assertEqual(client._http.headers["Authorization"], "Bearer test-token")

    def test_login_http_error(self):
        client = Client()
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.raise_for_status.side_effect = requests.HTTPError(response=mock_resp)

        with patch.object(client._http, "post", return_value=mock_resp):
            result = client.login("bad", "creds")

        self.assertFalse(result)
        self.assertIsNone(client._token)

    def test_login_connection_error(self):
        client = Client()
        with patch.object(client._http, "post", side_effect=requests.ConnectionError):
            result = client.login("user", "pass")

        self.assertFalse(result)


class TestStartSession(unittest.TestCase):
    def test_start_session_success(self):
        client = Client()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"session_id": "sess-123"}
        mock_resp.raise_for_status = MagicMock()

        with patch.object(client._http, "post", return_value=mock_resp):
            result = client.start_session()

        self.assertTrue(result)
        self.assertEqual(client._session_id, "sess-123")

    def test_start_session_http_error(self):
        client = Client()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = requests.HTTPError(response=mock_resp)

        with patch.object(client._http, "post", return_value=mock_resp):
            result = client.start_session()

        self.assertFalse(result)


class TestEndSession(unittest.TestCase):
    def test_end_session_clears_state(self):
        client = Client()
        client._token = "tok"
        client._session_id = "sess"
        client._http.headers["Authorization"] = "Bearer tok"

        with patch.object(client._http, "post", return_value=MagicMock()):
            client.end_session()

        self.assertIsNone(client._session_id)
        self.assertIsNone(client._token)
        self.assertNotIn("Authorization", client._http.headers)

    def test_end_session_noop_when_no_session(self):
        client = Client()
        # Should not raise even with no session
        client.end_session()
        self.assertIsNone(client._session_id)


if __name__ == "__main__":
    unittest.main()
