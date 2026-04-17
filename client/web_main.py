#!/usr/bin/env python3
"""
Maha Web Client

Serves client/web/index.html on WEB_PORT (default 3000)
and opens a browser window automatically.

Reads settings from the shared root config.json (client section).
Environment variables always override config file values.

Config lookup order (first found wins):
  1. CONFIG_PATH env var
  2. Beside the executable (when frozen)
  3. ../config.json  (repo root, one level up from client/)
  4. ./config.json   (same directory as this script)

PyInstaller compatible: resolves paths from sys._MEIPASS when frozen.

Environment variables (override config.json):
  GATEWAY_URL   Gateway address shown in UI
  WEB_HOST      Bind host (default: 127.0.0.1)
  WEB_PORT      Bind port (default: 3000)
  CONFIG_PATH   Explicit path to config.json
"""

import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

_BASE_DIR = (
    sys._MEIPASS  # type: ignore[attr-defined]
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)


def _load_config() -> dict:
    """Load client section from shared config.json."""
    if "CONFIG_PATH" in os.environ:
        candidates = [os.environ["CONFIG_PATH"]]
    elif getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates = [
            os.path.join(exe_dir, "config.json"),       # editable, beside exe
            os.path.join(_BASE_DIR, "config.json"),     # bundled default
        ]
    else:
        candidates = [
            os.path.join(_BASE_DIR, "..", "config.json"),  # repo root
            os.path.join(_BASE_DIR, "config.json"),        # client/
        ]

    raw: dict = {}
    for path in candidates:
        try:
            with open(os.path.normpath(path), encoding="utf-8") as f:
                raw = json.load(f)
            break
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            print(f"[경고] {path} 파싱 오류: {e}")
            break

    # Support both flat {"gateway_url": ...} and nested {"client": {...}}
    cfg: dict = raw.get("client", raw)

    # Environment variables take highest priority
    if "GATEWAY_URL" in os.environ:
        cfg["gateway_url"] = os.environ["GATEWAY_URL"]

    cfg.setdefault("gateway_url", "http://localhost:8000")
    cfg.setdefault("web_host", "127.0.0.1")
    cfg.setdefault("web_port", 3000)
    return cfg


_HTML: bytes = b""
_CONFIG: dict = {}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/config":
            body = json.dumps(_CONFIG).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(_HTML)))
            self.end_headers()
            self.wfile.write(_HTML)

    def log_message(self, *_):
        pass


def main():
    global _HTML, _CONFIG

    with open(os.path.join(_BASE_DIR, "web", "index.html"), "rb") as f:
        _HTML = f.read()

    _CONFIG = _load_config()

    host = os.environ.get("WEB_HOST", str(_CONFIG["web_host"]))
    port = int(os.environ.get("WEB_PORT", str(_CONFIG["web_port"])))

    server = HTTPServer((host, port), _Handler)
    url = f"http://{host}:{port}"
    print(f"Maha Web  →  {url}")
    print(f"Gateway   →  {_CONFIG['gateway_url']}")
    print("Ctrl+C 로 종료")

    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
