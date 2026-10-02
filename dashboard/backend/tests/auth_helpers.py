"""
@header {
  "module": "tests.auth_helpers",
  "layer": "test",
  "domain": "console",
  "description": "Console 인증 게이트 테스트 공용 헬퍼. authed_client(app)는 임시 OPAL_HOME에 dashboard.backend.entry_token.issue()로 진입 token을 발급하고 POST /api/auth/exchange로 교환해 세션 쿠키를 가진 TestClient를 돌려준다(base_url은 항상 http://127.0.0.1:7823, 이후 상태 변경 요청에 Origin과 X-CSRF-Token 자동 부착). make_session은 같은 교환을 하되 헤더를 자동 부착하지 않는 원시 클라이언트와 csrf 값을 돌려준다. FakePopen은 subprocess.Popen 대체 객체(communicate가 (stdout, stderr)를 돌려주고 returncode 보유, 호출 횟수·인자 기록, 선택적 지연 이벤트). forbid_real_spawn은 실제 subprocess.run·subprocess.Popen 호출을 즉시 AssertionError로 만드는 가드 fixture이고 no_real_spawn은 이를 autouse로 적용하는 래퍼이며, isolated_console_home은 console.config.json 경로와 OPAL_HOME을 임시 디렉터리로 격리한다. set_legacy_brain_policy는 임시 설정 파일의 legacy_brain_enabled 키를 쓰고 정책을 설정에서 다시 읽게 한다. 실제 claude 프로세스·사용자 ~/.opal·포트 7823은 건드리지 않는다.",
  "task": "175-261001-opd-콘솔-POST-인증-게이트",
  "scenarios": ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-8", "S-9"],
  "exports": ["BASE_URL", "ORIGIN", "authed_client", "make_session", "FakePopen", "claude_json_output", "forbid_real_spawn", "no_real_spawn", "isolated_console_home", "set_legacy_brain_policy", "reset_registry"],
  "depends": ["entry_token", "adapters.brain_policy", "config"]
}
"""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import tempfile
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BASE_URL = "http://127.0.0.1:7823"
ORIGIN = "http://127.0.0.1:7823"

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


@contextlib.contextmanager
def _env(**values: str):
    """환경 변수를 잠시 바꾸고 원복한다."""
    saved = {k: os.environ.get(k) for k in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, old in saved.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


class AuthedTestClient(TestClient):
    """상태 변경 요청에 Origin·X-CSRF-Token을 자동으로 붙이는 TestClient."""

    csrf_token: str | None = None

    def request(self, method, url, **kwargs):  # type: ignore[override]
        if str(method).upper() not in _SAFE_METHODS:
            headers = dict(kwargs.get("headers") or {})
            lowered = {k.lower() for k in headers}
            if "origin" not in lowered:
                headers["Origin"] = ORIGIN
            if "x-csrf-token" not in lowered and self.csrf_token:
                headers["X-CSRF-Token"] = self.csrf_token
            kwargs["headers"] = headers
        return super().request(method, url, **kwargs)


def make_session(app, client_cls=TestClient, opal_home: Path | None = None, **client_kwargs):
    """진입 token 발급 → 교환까지 마친 (client, csrf_token)을 돌려준다.

    client_cls가 TestClient이면 헤더를 자동 부착하지 않는 원시 클라이언트다.
    """
    tmp = None
    if opal_home is None:
        tmp = tempfile.TemporaryDirectory(prefix="opal-console-auth-")
        opal_home = Path(tmp.name) / ".opal"
    with _env(OPAL_HOME=str(opal_home)):
        from dashboard.backend import entry_token

        token = entry_token.issue()
        client = client_cls(app, base_url=BASE_URL, **client_kwargs)
        resp = client.post(
            "/api/auth/exchange",
            json={"token": token},
            headers={"Origin": ORIGIN},
        )
    assert resp.status_code == 200, f"exchange failed: {resp.status_code} {resp.text}"
    csrf = resp.json()["csrf_token"]
    client.csrf_token = csrf  # type: ignore[attr-defined]
    client._opal_home_tmp = tmp  # type: ignore[attr-defined]  # 클라이언트 수명 동안 유지
    return client, csrf


def authed_client(app, **client_kwargs) -> AuthedTestClient:
    """세션 쿠키를 가진 TestClient. 상태 변경 요청에 Origin·CSRF 헤더가 자동 부착된다."""
    client, _csrf = make_session(app, client_cls=AuthedTestClient, **client_kwargs)
    return client  # type: ignore[return-value]


# ── subprocess.Popen 대체 ────────────────────────────────────────────────────

def claude_json_output(answer: str = "ok", session_id: str = "sid-fake") -> str:
    """claude --output-format json 이 stdout에 쓰는 성공 출력."""
    inner = json.dumps({"answer": answer, "citations": []}, ensure_ascii=False)
    return json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": f"```json\n{inner}\n```",
            "session_id": session_id,
        },
        ensure_ascii=False,
    )


class _FakeProc:
    def __init__(self, owner: "FakePopen", stdout: str, stderr: str, returncode: int):
        self._owner = owner
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode
        self.killed = False
        self.pid = 4242

    def communicate(self, input=None, timeout=None):  # noqa: A002
        gate = self._owner.release
        if gate is not None:
            if not gate.wait(timeout=timeout if timeout is not None else 30):
                raise subprocess.TimeoutExpired(cmd="claude", timeout=timeout or 30)
        if self._owner.timeout_on_communicate and not self.killed:
            raise subprocess.TimeoutExpired(cmd="claude", timeout=timeout or 0)
        return self._stdout, self._stderr

    def kill(self):
        self.killed = True

    def terminate(self):
        self.killed = True

    def wait(self, timeout=None):
        return self.returncode

    def poll(self):
        return self.returncode


class FakePopen:
    """subprocess.Popen 대체. 호출 횟수·인자를 기록한다.

    release: threading.Event를 주면 communicate가 이벤트가 켜질 때까지 대기한다(turn 진행 중 유지).
    timeout_on_communicate: True면 kill 전 첫 communicate가 TimeoutExpired를 던진다.
    """

    def __init__(
        self,
        stdout: str | None = None,
        stderr: str = "",
        returncode: int = 0,
        release: threading.Event | None = None,
        timeout_on_communicate: bool = False,
    ):
        self.stdout = stdout if stdout is not None else claude_json_output()
        self.stderr = stderr
        self.returncode = returncode
        self.release = release
        self.timeout_on_communicate = timeout_on_communicate
        self.calls: list[tuple[tuple, dict]] = []
        self.procs: list[_FakeProc] = []
        self._lock = threading.Lock()

    def __call__(self, *args, **kwargs):
        with self._lock:
            self.calls.append((args, kwargs))
            proc = _FakeProc(self, self.stdout, self.stderr, self.returncode)
            self.procs.append(proc)
        return proc

    @property
    def call_count(self) -> int:
        with self._lock:
            return len(self.calls)

    def argv(self, index: int = 0) -> list[str]:
        args, kwargs = self.calls[index]
        return list(args[0] if args else kwargs["args"])


# ── fixtures ────────────────────────────────────────────────────────────────

def _install_spawn_guard(monkeypatch) -> None:
    def _forbidden(*args, **kwargs):
        raise AssertionError(f"real subprocess spawn is forbidden in tests: args={args!r}")

    monkeypatch.setattr(subprocess, "run", _forbidden)
    monkeypatch.setattr(subprocess, "Popen", _forbidden)


@pytest.fixture
def forbid_real_spawn(monkeypatch):
    """실제 subprocess.run·Popen 호출은 즉시 실패시킨다(실제 claude 호출 0회 보장).

    spawn 검증이 필요한 테스트는 이 가드 위에 monkeypatch.setattr("subprocess.Popen", FakePopen(...))로 덮어쓴다.
    """
    _install_spawn_guard(monkeypatch)


@pytest.fixture(autouse=True)
def no_real_spawn(monkeypatch):
    """Brain 관련 테스트 파일이 import하면 모든 테스트에 적용되는 autouse 가드."""
    _install_spawn_guard(monkeypatch)


@pytest.fixture
def isolated_console_home(monkeypatch, tmp_path):
    """console.config.json 경로와 OPAL_HOME을 임시 디렉터리로 격리한다. 설정 파일 경로를 돌려준다."""
    from dashboard.backend import config as config_module

    opal_home = tmp_path / ".opal"
    opal_home.mkdir(parents=True, exist_ok=True)
    config_path = opal_home / "console.config.json"
    monkeypatch.setattr(config_module, "CONFIG_PATH", config_path)
    monkeypatch.setenv("OPAL_HOME", str(opal_home))
    monkeypatch.setenv("HOME", str(tmp_path))
    return config_path


def set_legacy_brain_policy(config_path: Path, enabled: bool | None) -> None:
    """임시 설정 파일의 legacy_brain_enabled 키를 쓰고(None이면 키 제거) 정책을 설정에서 다시 읽게 한다."""
    from dashboard.backend.adapters import brain_policy

    data: dict = {}
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except ValueError:
            data = {}  # 파손된 설정은 새로 쓴다
    if enabled is None:
        data.pop("legacy_brain_enabled", None)
    else:
        data["legacy_brain_enabled"] = enabled
    config_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    brain_policy.reload_from_config()


@pytest.fixture
def reset_registry():
    """전역 brain_session_registry의 세션·풀 상태를 테스트 전후로 비운다."""
    from dashboard.backend.adapters.brain_session import brain_session_registry as reg

    def _clear():
        with reg._lock:
            reg._sessions.clear()
        with reg._pool_lock:
            reg._pool.clear()
            reg._pool_inflight.clear()

    _clear()
    yield reg
    _clear()
