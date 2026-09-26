"""
@header {
  "module": "todo_web.app",
  "layer": "application",
  "domain": "todo-web",
  "description": "Standard-library HTTP skeleton with health and HTML endpoints. CRUD is intentionally unimplemented in the base scenario.",
  "exports": ["main", "make_handler"]
}
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


def _send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _send_html(handler: BaseHTTPRequestHandler, status: int, body: str) -> None:
    raw = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def make_handler(data_path: Path) -> type[BaseHTTPRequestHandler]:
    class TodoHandler(BaseHTTPRequestHandler):
        server_version = "TodoWeb/0.1"

        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/health":
                _send_json(self, 200, {"ok": True})
                return
            if path == "/":
                _send_html(
                    self,
                    200,
                    """
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Todo Web</title></head>
<body>
  <h1>Todo Web</h1>
  <main id="app">
    <form id="todo-form">
      <label>Title <input name="title" /></label>
      <label>Description <textarea name="description"></textarea></label>
      <button type="submit">Create</button>
    </form>
    <section id="todo-list" aria-label="Todo list"></section>
  </main>
</body>
</html>
""".strip(),
                )
                return
            _send_json(self, 404, {"error": "not_found"})

        def do_POST(self) -> None:
            _send_json(self, 404, {"error": "not_found"})

        def do_PATCH(self) -> None:
            _send_json(self, 404, {"error": "not_found"})

        def do_DELETE(self) -> None:
            _send_json(self, 404, {"error": "not_found"})

    TodoHandler.data_path = data_path
    return TodoHandler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data", type=Path, default=Path("data/todos.json"))
    args = parser.parse_args(argv)
    args.data.parent.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(args.data))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
