#!/usr/bin/env python3
"""
Maha Web Client

Serves client/web/index.html on WEB_PORT (default 3000)
and opens a browser window automatically.

Config file (config.json) is read from the same directory.
Values in config.json can be overridden by environment variables.

PyInstaller compatible: resolves paths from sys._MEIPASS when frozen.

Environment variables:
  WEB_HOST      Bind host (default: 127.0.0.1)
  WEB_PORT      Bind port (default: 3000)
  CONFIG_PATH   Path to config file (default: <script_dir>/config.json)
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

_HTML: bytes = b""
_CONFIG: dict = {}


def _load_config() -> dict:
    config_path = os.environ.get(
        "CONFIG_PATH", os.path.join(_BASE_DIR, "config.json")
    )
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        cfg = {}
    except json.JSONDecodeError as e:
        print(f"[경고] config.json 파싱 오류: {e}")
        cfg = {}

    # Environment variables override config file values
    if "GATEWAY_URL" in os.environ:
        cfg["gateway_url"] = os.environ["GATEWAY_URL"]

    cfg.setdefault("gateway_url", "http://localhost:8000")
    return cfg


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

    host = os.environ.get("WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("WEB_PORT", "3000"))

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
