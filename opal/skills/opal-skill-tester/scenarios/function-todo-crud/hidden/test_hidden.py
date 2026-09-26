"""
@header {
  "module": "test_hidden_function_todo_crud",
  "layer": "test",
  "domain": "opal-skill-tester",
  "description": "function-todo-crud hidden acceptance tests. They verify the public HTTP/HTML contract of a small TODO CRUD app using only SUT_REPO.",
  "exports": []
}
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest


REPO = Path(os.environ["SUT_REPO"])


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    try:
        return sock.getsockname()[1]
    finally:
        sock.close()


class Client:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body=None, headers=None):
        data = None
        hdrs = dict(headers or {})
        if body is not None:
            if isinstance(body, bytes):
                data = body
            else:
                data = json.dumps(body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(self.base_url + path, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as res:
                raw = res.read()
                return res.status, dict(res.headers), raw
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()

    def json(self, method: str, path: str, body=None, headers=None):
        status, headers, raw = self.request(method, path, body, headers)
        payload = json.loads(raw.decode("utf-8")) if raw else None
        return status, headers, payload


@pytest.fixture
def server(tmp_path):
    port = free_port()
    data_path = tmp_path / "todos.json"
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "todo_web.app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--data",
            str(data_path),
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    client = Client(f"http://127.0.0.1:{port}")
    deadline = time.time() + 8
    while time.time() < deadline:
        if proc.poll() is not None:
            out, err = proc.communicate(timeout=1)
            raise AssertionError(f"server exited early\nstdout={out}\nstderr={err}")
        try:
            status, _, payload = client.json("GET", "/health")
            if status == 200 and payload == {"ok": True}:
                break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate()
        raise AssertionError("server did not become ready")
    try:
        yield client, data_path
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def restart_server(data_path: Path):
    port = free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "todo_web.app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--data",
            str(data_path),
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    client = Client(f"http://127.0.0.1:{port}")
    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            if client.json("GET", "/health")[0] == 200:
                return proc, client
        except Exception:
            time.sleep(0.1)
    proc.terminate()
    raise AssertionError("restarted server did not become ready")


def test_h01_crud_happy_path_and_other_item_unchanged(server):
    client, _ = server
    status, headers, first = client.json("POST", "/api/todos", {"title": " Buy milk ", "description": "2 bottles"})
    assert status == 201
    assert first["title"] == "Buy milk"
    assert first["description"] == "2 bottles"
    assert first["completed"] is False
    assert headers["Location"] == f"/api/todos/{first['id']}"

    status, _, second = client.json("POST", "/api/todos", {"title": "Read", "description": ""})
    assert status == 201

    status, _, todos = client.json("GET", "/api/todos")
    assert status == 200
    assert [todo["id"] for todo in todos] == [first["id"], second["id"]]

    status, _, updated = client.json(
        "PATCH",
        f"/api/todos/{first['id']}",
        {"title": "Buy oat milk", "description": "1 carton", "completed": True},
    )
    assert status == 200
    assert updated == {
        "id": first["id"],
        "title": "Buy oat milk",
        "description": "1 carton",
        "completed": True,
    }
    assert client.json("GET", f"/api/todos/{second['id']}")[2] == second


def test_h02_delete_removes_list_and_detail(server):
    client, _ = server
    first = client.json("POST", "/api/todos", {"title": "Keep", "description": ""})[2]
    doomed = client.json("POST", "/api/todos", {"title": "Delete", "description": ""})[2]

    status, _, raw = client.request("DELETE", f"/api/todos/{doomed['id']}")
    assert status == 204
    assert raw == b""
    assert client.json("GET", f"/api/todos/{doomed['id']}")[0] == 404
    assert client.json("GET", "/api/todos")[2] == [first]


def test_h03_persistence_across_restart(server):
    client, data_path = server
    first = client.json("POST", "/api/todos", {"title": "Persist", "description": "survives"})[2]
    second = client.json("POST", "/api/todos", {"title": "Remove me", "description": "temporary"})[2]
    status, _, updated = client.json("PATCH", f"/api/todos/{first['id']}", {"completed": True})
    assert status == 200
    status, _, raw = client.request("DELETE", f"/api/todos/{second['id']}")
    assert status == 204
    assert raw == b""

    proc, restarted = restart_server(data_path)
    try:
        status, _, todos = restarted.json("GET", "/api/todos")
        assert status == 200
        assert todos == [updated]
        assert restarted.json("GET", f"/api/todos/{first['id']}")[2] == updated
        assert restarted.json("GET", f"/api/todos/{second['id']}")[0] == 404
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_h04_validation_errors(server):
    client, _ = server
    for body in (
        {"title": "", "description": ""},
        {"title": "   ", "description": ""},
        {"description": "missing title"},
        {"title": "x" * 121, "description": ""},
        {"title": "ok", "description": "x" * 2001},
    ):
        status, _, payload = client.json("POST", "/api/todos", body)
        assert status == 400
        assert "error" in payload
    todo = client.json("POST", "/api/todos", {"title": "Patch me", "description": ""})[2]
    status, _, payload = client.json("PATCH", f"/api/todos/{todo['id']}", {})
    assert status == 400
    assert "error" in payload
    assert client.json("PATCH", f"/api/todos/{todo['id']}", {"title": " "})[0] == 400
    assert client.json("PATCH", f"/api/todos/{todo['id']}", {"completed": "yes"})[0] == 400


def test_h05_not_found_content_type_malformed_json_and_method(server):
    client, _ = server
    assert client.json("GET", "/api/todos/nope")[0] == 404
    assert client.json("PATCH", "/api/todos/nope", {"title": "x"})[0] == 404
    assert client.request("DELETE", "/api/todos/nope")[0] == 404

    status, _, payload = client.json(
        "POST",
        "/api/todos",
        b"{bad json",
        {"Content-Type": "application/json"},
    )
    assert status == 400
    assert "error" in payload

    status, _, payload = client.json("POST", "/api/todos", b"title=x", {"Content-Type": "text/plain"})
    assert status == 415
    assert "error" in payload

    status, _, payload = client.json("PUT", "/api/todos/1", {"title": "x"})
    assert status == 405
    assert "error" in payload


def test_h06_html_surface_and_existing_tests_pass(server):
    client, _ = server
    status, headers, raw = client.request("GET", "/")
    body = raw.decode("utf-8").lower()
    assert status == 200
    assert "text/html" in headers["Content-Type"]
    for token in ("todo", "form", "title", "description"):
        assert token in body

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests", "-p", "no:cacheprovider"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout[-500:] + result.stderr[-500:]
