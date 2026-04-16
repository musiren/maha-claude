#!/usr/bin/env python3
"""
Windows Terminal Client

- Thin client: UI only, no execution logic
- Communicates with Gateway via HTTPS + SSE streaming
- Token stored in memory only, never persisted
- Supports /COMMAND slash command syntax
"""

import getpass
import json
import os
import signal
import sys
from urllib.parse import urljoin

import requests

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:8000")
SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT", "3600"))
CONNECT_TIMEOUT = 10


class Client:
    def __init__(self):
        self._token = None
        self._session_id = None
        self._http = requests.Session()
        self._slash_commands: list[dict] = []  # cached from gateway

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> bool:
        try:
            resp = self._http.post(
                urljoin(GATEWAY_URL, "/auth/login"),
                json={"username": username, "password": password},
                timeout=CONNECT_TIMEOUT,
            )
            resp.raise_for_status()
            self._token = resp.json()["token"]
            self._http.headers["Authorization"] = f"Bearer {self._token}"
            return True
        except requests.HTTPError as e:
            _print_error(f"로그인 실패 ({e.response.status_code})")
            return False
        except requests.ConnectionError:
            _print_error(f"서버에 연결할 수 없습니다: {GATEWAY_URL}")
            return False

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------

    def start_session(self) -> bool:
        try:
            resp = self._http.post(
                urljoin(GATEWAY_URL, "/session/start"),
                timeout=CONNECT_TIMEOUT,
            )
            resp.raise_for_status()
            self._session_id = resp.json()["session_id"]
            return True
        except requests.HTTPError as e:
            _print_error(f"세션 시작 실패 ({e.response.status_code})")
            return False

    def end_session(self):
        if not self._session_id:
            return
        try:
            self._http.post(
                urljoin(GATEWAY_URL, "/session/end"),
                json={"session_id": self._session_id},
                timeout=5,
            )
        except Exception:
            pass
        finally:
            self._session_id = None
            self._token = None
            self._http.headers.pop("Authorization", None)

    # ------------------------------------------------------------------
    # Slash command discovery
    # ------------------------------------------------------------------

    def fetch_commands(self):
        """Fetch available slash commands from gateway (best-effort)."""
        try:
            resp = self._http.get(
                urljoin(GATEWAY_URL, "/commands"),
                timeout=CONNECT_TIMEOUT,
            )
            resp.raise_for_status()
            self._slash_commands = resp.json()
        except Exception:
            pass  # Non-critical; fallback to /help command

    def show_slash_help(self):
        """Print locally cached slash command list."""
        if not self._slash_commands:
            print("  (명령어 목록을 불러올 수 없습니다. '/help'를 실행하세요)")
            return
        print("사용 가능한 슬래시 명령어:")
        for cmd in self._slash_commands:
            approval = " [승인 필요]" if cmd.get("requires_approval") else ""
            print(f"  {cmd['command']:<18} {cmd['description']}{approval}")

    # ------------------------------------------------------------------
    # Command
    # ------------------------------------------------------------------

    def send_command(self, command: str):
        if not self._session_id:
            _print_error("활성 세션이 없습니다.")
            return

        # Visual prefix for slash commands
        if command.startswith("/"):
            print(f"[/] {command}", flush=True)

        try:
            with self._http.post(
                urljoin(GATEWAY_URL, "/command"),
                json={"session_id": self._session_id, "command": command},
                stream=True,
                timeout=(CONNECT_TIMEOUT, SESSION_TIMEOUT),
            ) as resp:
                resp.raise_for_status()
                self._stream_response(resp)
        except requests.HTTPError as e:
            _print_error(f"명령 실패 ({e.response.status_code})")
        except requests.ConnectionError:
            _print_error("연결이 끊겼습니다.")
        except KeyboardInterrupt:
            print("\n[취소]")

    def _stream_response(self, resp: requests.Response):
        for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
            if not chunk:
                continue
            for line in chunk.splitlines():
                if line.startswith("data: "):
                    payload = line[6:]
                    if payload == "[DONE]":
                        print()
                        return
                    self._handle_payload(payload)
                elif line and not line.startswith(":"):
                    print(line, end="", flush=True)
        print()

    def _handle_payload(self, raw: str):
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            print(raw, end="", flush=True)
            return

        msg_type = obj.get("type", "text")
        if msg_type == "approval":
            self._handle_approval(obj)
        elif msg_type == "error":
            print(f"[오류] {obj.get('content', '')}", flush=True)
        else:
            print(obj.get("content", ""), end="", flush=True)

    def _handle_approval(self, obj: dict):
        message = obj.get("message", "승인이 필요합니다.")
        print(f"\n[승인 필요] {message}")
        answer = input("계속하시겠습니까? [y/N]: ").strip().lower()
        approved = answer in ("y", "yes")
        try:
            self._http.post(
                urljoin(GATEWAY_URL, "/command/approve"),
                json={
                    "session_id": self._session_id,
                    "approval_id": obj.get("approval_id"),
                    "approved": approved,
                },
                timeout=CONNECT_TIMEOUT,
            )
        except Exception as e:
            _print_error(f"승인 전송 실패: {e}")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _print_error(msg: str):
    print(f"[오류] {msg}", file=sys.stderr)


def _print_banner():
    print("=" * 50)
    print("  Maha Terminal Client")
    print(f"  Gateway: {GATEWAY_URL}")
    print("=" * 50)
    print("  종료    : 'exit' 또는 Ctrl+C")
    print("  명령 목록: '/' 단독 입력 또는 '/help'")
    print()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main():
    client = Client()

    def _shutdown(sig, frame):
        print("\n세션을 종료합니다...")
        client.end_session()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    _print_banner()

    username = input("사용자명: ").strip()
    password = getpass.getpass("비밀번호: ")

    if not client.login(username, password):
        sys.exit(1)

    if not client.start_session():
        sys.exit(1)

    client.fetch_commands()
    print("\n세션이 시작됐습니다.\n")

    while True:
        try:
            command = input("> ").strip()
        except EOFError:
            break

        if not command:
            continue

        # '/' 단독 입력 → 로컬 캐시된 명령어 목록 표시
        if command == "/":
            client.show_slash_help()
            continue

        if command.lower() in ("exit", "quit", "종료"):
            break

        client.send_command(command)

    client.end_session()
    print("종료됐습니다.")


if __name__ == "__main__":
    main()
