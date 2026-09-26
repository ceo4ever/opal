"""
@header {
  "module": "test_basic",
  "layer": "test",
  "domain": "todo-web",
  "description": "Base regression tests for the TODO web skeleton.",
  "exports": []
}
"""
import json
from pathlib import Path

from todo_web.app import make_handler


class DummyHandler:
    def __init__(self):
        self.status = None
        self.headers = {}
        self.body = bytearray()
        self.path = "/health"
        self.wfile = self

    def send_response(self, status):
        self.status = status

    def send_header(self, key, value):
        self.headers[key] = value

    def end_headers(self):
        return None

    def write(self, data):
        self.body.extend(data)


def test_health_endpoint_returns_ok(tmp_path):
    handler_type = make_handler(tmp_path / "todos.json")
    handler = DummyHandler()

    handler_type.do_GET(handler)

    assert handler.status == 200
    assert json.loads(handler.body.decode("utf-8")) == {"ok": True}


def test_home_page_contains_basic_todo_surface(tmp_path):
    handler_type = make_handler(Path(tmp_path) / "todos.json")
    handler = DummyHandler()
    handler.path = "/"

    handler_type.do_GET(handler)

    body = handler.body.decode("utf-8")
    assert handler.status == 200
    assert "Todo Web" in body
    assert "todo-form" in body
