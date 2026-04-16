#!/usr/bin/env python3
"""
Maha Web Client

Serves client/web/index.html on WEB_PORT (default 3000)
and opens a browser window automatically.

PyInstaller compatible: reads index.html from sys._MEIPASS when frozen.

Environment variables:
  WEB_HOST      Bind host   (default: 127.0.0.1)
  WEB_PORT      Bind port   (default: 3000)
  GATEWAY_URL   Shown in UI (default: http://localhost:8000)
"""

import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer


def _html_bytes() -> bytes:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "web", "index.html"), "rb") as f:
        return f.read()


_HTML: bytes = b""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(_HTML)))
        self.end_headers()
        self.wfile.write(_HTML)

    def log_message(self, *_):
        pass


def main():
    global _HTML
    _HTML = _html_bytes()

    host = os.environ.get("WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("WEB_PORT", "3000"))
    gateway = os.environ.get("GATEWAY_URL", "http://localhost:8000")

    server = HTTPServer((host, port), _Handler)
    url = f"http://{host}:{port}"
    print(f"Maha Web  →  {url}  (Gateway: {gateway})")
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
