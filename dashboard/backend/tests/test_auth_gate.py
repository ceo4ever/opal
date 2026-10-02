"""
@header {
  "module": "tests.test_auth_gate",
  "layer": "test",
  "domain": "console",
  "description": "Console 인증 게이트 공개 계약 RED-first 테스트(S-1~S-5). 실제 앱(main.app, 미들웨어 포함)과 TestClient(base_url=http://127.0.0.1:7823)로 검증한다. S-1: 상태 변경 라우트 4종(brain prime·query, config prewarm, 같은 앱에 붙인 테스트용 POST 라우트)에 대한 Host→Origin→세션→CSRF 거절 사다리(401 auth_required·403 origin_required·origin_not_allowed·host_not_allowed·csrf_invalid)와 거절 동안 Popen 0회·설정 바이트 불변·핸들러 미진입, 유효 세션 대조군 200. S-2: 테스트용 WebSocket 라우트 handshake 5변형(거절 4종은 accept 전 close 1008). S-3: CORS(credentials true, 정확 origin 반영, x-csrf-token 허용, 미허용 origin 거부, preflight는 세션 없이 통과). S-4: /health 키 3종과 /api/* GET 전수의 default-deny, 유효 세션 GET의 통과. S-5: POST /api/auth/exchange 계약(성공 응답·쿠키 속성, 재사용·만료·상한 초과·무효·디렉터리 위조 거절의 동일 401 entry_token_invalid, Origin 없는 교환 403, 로그·본문 비노출, GET /api/auth/session 모양). 실제 claude·사용자 ~/.opal·포트 7823은 건드리지 않는다(임시 OPAL_HOME·CONFIG_PATH, subprocess 가드, Popen 대체).",
  "task": "179-261001-opd-콘솔-POST-인증-게이트",
  "scenarios": ["S-1", "S-2", "S-3", "S-4", "S-5"],
  "exports": [],
  "depends": ["auth", "entry_token", "routers.auth", "main", "adapters.brain_policy", "tests.auth_helpers"]
}
"""
from __future__ import annotations

import hashlib
import importlib
import json
import logging
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from dashboard.backend.tests.auth_helpers import (  # noqa: F401  (fixture 등록)
    BASE_URL,
    ORIGIN,
    FakePopen,
    forbid_real_spawn,
    isolated_console_home,
    make_session,
    set_legacy_brain_policy,
)

SESSION_COOKIE = "opal_console_session"
EVIL_ORIGIN = "http://evil.example"
SECRET_NAME = "s4-secret-project-name"
SID = "aaaaaaaa-0001-0001-0001-000000000001"

PROBE_PATH = "/api/_gate_probe"
WS_PATH = "/api/_gate_ws"


# ── 공통 fixture ─────────────────────────────────────────────────────────────

def _app():
    return importlib.import_module("dashboard.backend.main").app


def _policy_off(config_path: Path) -> None:
    """구형 Brain 정책을 꺼짐(키 없음)으로 되돌린다. 정책 모듈이 아직 없으면 건너뛴다."""
    try:
        set_legacy_brain_policy(config_path, None)
    except ImportError:
        pass


class _Env:
    """격리된 설정 파일·프로젝트·핸들러 진입 카운터."""

    def __init__(self, config_path: Path, project: Path):
        self.config_path = config_path
        self.project = str(project)
        self.counters = {"prime": 0, "query": 0, "prewarm": 0, "probe": 0, "ws": 0}
        self.entered = threading.Event()

    def config_bytes(self) -> bytes:
        return self.config_path.read_bytes()


@pytest.fixture
def env(monkeypatch, isolated_console_home, forbid_real_spawn, tmp_path):
    """임시 설정·프로젝트·카운팅 스텁·Popen 대체를 갖춘 격리 환경. 앱에 테스트용 POST/WS 라우트를 붙인다."""
    from dashboard.backend.adapters.brain_session import brain_session_registry as reg

    project = tmp_path / "ws" / SECRET_NAME
    project.mkdir(parents=True)
    isolated_console_home.write_text(
        json.dumps(
            {"scan_roots": [str(tmp_path / "ws")], "scan_depth": 2, "prewarm_projects": []},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    state = _Env(isolated_console_home, project)

    class _FakeProject:
        def __init__(self, path):
            self.path = path
            self.is_opal = True

    fake_scan = lambda *a, **k: [_FakeProject(state.project)]  # noqa: E731
    monkeypatch.setattr("dashboard.backend.routers.brain.scan_projects", fake_scan)
    monkeypatch.setattr("dashboard.backend.routers.config.scan_projects", fake_scan)

    def _count(name, ret=None):
        def _stub(*a, **k):
            state.counters[name] += 1
            state.entered.set()
            return ret
        return _stub

    monkeypatch.setattr(reg, "prime", _count("prime"))
    monkeypatch.setattr(reg, "submit_job", _count("query", "job-1"))
    monkeypatch.setattr(reg, "prewarm", _count("prewarm"))

    popen = FakePopen()
    monkeypatch.setattr("subprocess.Popen", popen)
    state.popen = popen

    app = _app()

    def _probe():
        state.counters["probe"] += 1
        return {"ok": True}

    async def _ws(websocket):
        state.counters["ws"] += 1
        await websocket.accept()
        await websocket.send_text("hello")
        await websocket.close()

    before = len(app.router.routes)
    app.add_api_route(PROBE_PATH, _probe, methods=["POST"])
    app.router.add_websocket_route(WS_PATH, _ws)
    added = app.router.routes[before:]
    _policy_off(isolated_console_home)
    try:
        yield state
    finally:
        for r in added:
            if r in app.router.routes:
                app.router.routes.remove(r)
        _policy_off(isolated_console_home)


def _routes(env: _Env) -> dict:
    return {
        "prime": ("/api/brain/prime", {"project": env.project, "session_id": SID}),
        "query": ("/api/brain/query", {"question": "q", "project": env.project, "session_id": SID}),
        "prewarm": ("/api/config/prewarm", {"project": env.project, "enabled": True}),
        "probe": (PROBE_PATH, {}),
    }


def _code(resp) -> str | None:
    try:
        return resp.json()["error"]["code"]
    except Exception:
        return None


def _cookie_value(client: TestClient) -> str:
    value = client.cookies.get(SESSION_COOKIE)
    assert value, "session cookie missing after exchange"
    return value


# ── S-1 ─────────────────────────────────────────────────────────────────────

VARIANTS = [
    "no_session",
    "no_origin",
    "cross_origin_json",
    "cross_origin_form",
    "cross_origin_text",
    "bad_host",
    "csrf_missing",
    "csrf_wrong",
    "forged_cookie",
]

EXPECTED = {
    "no_session": (401, "auth_required"),
    "no_origin": (403, "origin_required"),
    "cross_origin_json": (403, "origin_not_allowed"),
    "cross_origin_form": (403, "origin_not_allowed"),
    "cross_origin_text": (403, "origin_not_allowed"),
    "bad_host": (403, "host_not_allowed"),
    "csrf_missing": (403, "csrf_invalid"),
    "csrf_wrong": (403, "csrf_invalid"),
    "forged_cookie": (401, "auth_required"),
}


def _send_variant(variant: str, path: str, body: dict):
    app = _app()
    if variant == "no_session":
        client = TestClient(app, base_url=BASE_URL)
        return client.post(path, json=body, headers={"Origin": ORIGIN})
    client, csrf = make_session(app)
    if variant == "no_origin":
        return client.post(path, json=body, headers={"X-CSRF-Token": csrf})
    if variant == "cross_origin_json":
        return client.post(path, json=body, headers={"Origin": EVIL_ORIGIN, "X-CSRF-Token": csrf})
    if variant == "cross_origin_form":
        return client.post(
            path,
            content="a=b",
            headers={
                "Origin": EVIL_ORIGIN,
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRF-Token": csrf,
            },
        )
    if variant == "cross_origin_text":
        return client.post(
            path,
            content=json.dumps(body),
            headers={"Origin": EVIL_ORIGIN, "Content-Type": "text/plain", "X-CSRF-Token": csrf},
        )
    if variant == "bad_host":
        evil = TestClient(app, base_url="http://evil.example:7823")
        return evil.post(
            path,
            json=body,
            headers={
                "Origin": "http://evil.example:7823",
                "X-CSRF-Token": csrf,
                "Cookie": f"{SESSION_COOKIE}={_cookie_value(client)}",
            },
        )
    if variant == "csrf_missing":
        return client.post(path, json=body, headers={"Origin": ORIGIN})
    if variant == "csrf_wrong":
        return client.post(path, json=body, headers={"Origin": ORIGIN, "X-CSRF-Token": "wrong-" + csrf})
    if variant == "forged_cookie":
        forged = TestClient(app, base_url=BASE_URL)
        return forged.post(
            path,
            json=body,
            headers={
                "Origin": ORIGIN,
                "X-CSRF-Token": csrf,
                "Cookie": f"{SESSION_COOKIE}=forged-value-0123456789",
            },
        )
    raise AssertionError(variant)


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("route", ["prime", "query", "prewarm", "probe"])
def test_s1_rejected_before_any_work(env, route, variant):
    path, body = _routes(env)[route]
    before = env.config_bytes()

    resp = _send_variant(variant, path, body)

    status, code = EXPECTED[variant]
    assert resp.status_code == status, f"{route}/{variant}: {resp.status_code} {resp.text}"
    assert _code(resp) == code, f"{route}/{variant}: {resp.text}"
    time.sleep(0.05)  # 백그라운드 스레드가 있었다면 시작할 시간
    assert env.popen.call_count == 0
    assert env.config_bytes() == before
    assert all(v == 0 for v in env.counters.values()), env.counters


@pytest.mark.parametrize("route", ["prime", "query", "prewarm", "probe"])
def test_s1_valid_session_control_group_enters_handler_once(env, route):
    path, body = _routes(env)[route]
    set_legacy_brain_policy(env.config_path, True)  # prime·query 대조군은 구형 Brain 켜짐이 전제
    client, csrf = make_session(_app())

    resp = client.post(path, json=body, headers={"Origin": ORIGIN, "X-CSRF-Token": csrf})

    assert resp.status_code == 200, resp.text
    deadline = time.time() + 2
    while env.counters[route] == 0 and time.time() < deadline:
        time.sleep(0.01)
    assert env.counters[route] == 1, env.counters


# ── S-2 ─────────────────────────────────────────────────────────────────────

def _ws_headers(variant: str, cookie: str) -> dict:
    """WebSocket handshake 헤더. TestClient.websocket_connect는 base_url의 Host를 쓰지 않으므로 Host를 명시한다."""
    host = "evil.example:7823" if variant == "bad_host" else "127.0.0.1:7823"
    headers = {"Host": host}
    if variant != "no_session":
        headers["Cookie"] = f"{SESSION_COOKIE}={cookie}"
    if variant == "no_origin":
        return headers
    if variant == "cross_origin":
        return {**headers, "Origin": EVIL_ORIGIN}
    if variant == "bad_host":
        return {**headers, "Origin": "http://evil.example:7823"}
    return {**headers, "Origin": ORIGIN}  # no_session·valid


@pytest.mark.parametrize("variant", ["no_session", "no_origin", "cross_origin", "bad_host"])
def test_s2_websocket_rejected_before_accept(env, variant):
    app = _app()
    sess, _csrf = make_session(app)
    headers = _ws_headers(variant, _cookie_value(sess))
    client = TestClient(app, base_url=BASE_URL)

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(WS_PATH, headers=headers) as ws:
            ws.receive_text()

    assert excinfo.value.code == 1008
    assert env.counters["ws"] == 0


def test_s2_websocket_valid_session_connects(env):
    app = _app()
    sess, _csrf = make_session(app)
    headers = _ws_headers("valid", _cookie_value(sess))
    client = TestClient(app, base_url=BASE_URL)

    with client.websocket_connect(WS_PATH, headers=headers) as ws:
        assert ws.receive_text() == "hello"

    assert env.counters["ws"] == 1


# ── S-3 ─────────────────────────────────────────────────────────────────────

EXTRA_ORIGIN = "http://127.0.0.1:5555"


@pytest.fixture
def cors_main(monkeypatch):
    """OPAL_CONSOLE_CORS_ORIGINS를 주입해 main을 reload하고 테스트 뒤 원복한다."""
    import dashboard.backend.main as m

    monkeypatch.setenv("OPAL_CONSOLE_CORS_ORIGINS", EXTRA_ORIGIN)
    importlib.reload(m)
    yield m
    monkeypatch.delenv("OPAL_CONSOLE_CORS_ORIGINS", raising=False)
    importlib.reload(m)


@pytest.mark.parametrize("origin", ["http://127.0.0.1:5173", EXTRA_ORIGIN])
def test_s3_preflight_without_session_passes_with_exact_origin(env, cors_main, origin):
    client = TestClient(cors_main.app, base_url=BASE_URL)

    resp = client.options(
        "/api/config/prewarm",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-token",
        },
    )

    assert 200 <= resp.status_code < 300, resp.text
    assert resp.headers["access-control-allow-origin"] == origin
    assert resp.headers["access-control-allow-credentials"] == "true"
    assert "x-csrf-token" in resp.headers["access-control-allow-headers"].lower()


def test_s3_credentialed_request_from_allowed_origin_succeeds(env, cors_main):
    client, csrf = make_session(cors_main.app)

    resp = client.post(
        "/api/config/prewarm",
        json={"project": env.project, "enabled": False},
        headers={"Origin": EXTRA_ORIGIN, "X-CSRF-Token": csrf},
    )

    assert resp.status_code == 200, resp.text
    assert resp.headers["access-control-allow-origin"] == EXTRA_ORIGIN
    assert resp.headers["access-control-allow-credentials"] == "true"


def test_s3_preflight_from_unlisted_origin_has_no_allow_origin(env, cors_main):
    client = TestClient(cors_main.app, base_url=BASE_URL)

    resp = client.options(
        "/api/config/prewarm",
        headers={
            "Origin": EVIL_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-token",
        },
    )

    assert "access-control-allow-origin" not in resp.headers


# ── S-4 ─────────────────────────────────────────────────────────────────────

def _get_paths(project: str) -> list[str]:
    q = f"project={project}&session_id={SID}"
    return [
        "/api/dashboard",
        "/api/projects",
        f"/api/projects/detail?{q}&path={project}",
        f"/api/projects/doc?{q}&path={project}&doc=README.md",
        "/api/tasks",
        f"/api/tasks/detail?{q}&task=1",
        f"/api/tasks/artifact?{q}&task=1&name=TASK.md",
        "/api/memory",
        "/api/doctor",
        "/api/config",
        "/api/brain/auth",
        f"/api/brain/status?{q}",
        f"/api/brain/job/job-1?{q}",
        "/api/docs/skills",
        "/api/docs/skills/opal-onboarding",
    ]


def test_s4_health_is_minimal_without_session(env):
    resp = TestClient(_app(), base_url=BASE_URL).get("/health")

    assert resp.status_code == 200
    assert set(resp.json().keys()) == {"status", "version", "auth"}
    assert resp.json()["auth"] == "required"
    assert SECRET_NAME not in resp.text and env.project not in resp.text


def test_s4_health_rejects_foreign_host(env):
    resp = TestClient(_app(), base_url="http://evil.example:7823").get("/health")

    assert resp.status_code == 403
    assert _code(resp) == "host_not_allowed"


def test_s4_every_api_get_is_401_without_session(env):
    client = TestClient(_app(), base_url=BASE_URL)
    paths = _get_paths(env.project) + ["/api/does-not-exist"]
    assert len(paths) == 16

    for path in paths:
        resp = client.get(path, headers={"Origin": ORIGIN})
        assert resp.status_code == 401, f"{path}: {resp.status_code} {resp.text[:200]}"
        assert _code(resp) == "auth_required", path
        assert SECRET_NAME not in resp.text and env.project not in resp.text, path


def test_s4_spa_and_static_are_not_gated(env):
    client = TestClient(_app(), base_url=BASE_URL)

    for path in ["/", "/assets/app.js", "/index.html"]:
        resp = client.get(path)
        assert resp.status_code not in (401, 403), f"{path}: {resp.status_code}"


def test_s4_valid_session_get_is_not_gated(env):
    client, _csrf = make_session(_app(), raise_server_exceptions=False)

    for path in _get_paths(env.project):
        resp = client.get(path)
        assert resp.status_code not in (401, 403), f"{path}: {resp.status_code} {resp.text[:200]}"


# ── S-5 (exchange 계약) ──────────────────────────────────────────────────────

def _entry_dir(config_path: Path) -> Path:
    return config_path.parent / "run" / "console-entry"


def _issue() -> str:
    from dashboard.backend import entry_token

    return entry_token.issue()


def _exchange(client: TestClient, token: str, origin: str | None = ORIGIN):
    headers = {"Origin": origin} if origin else {}
    return client.post("/api/auth/exchange", json={"token": token}, headers=headers)


def _assert_invalid(resp, secrets: list[str]):
    assert resp.status_code == 401, resp.text
    assert _code(resp) == "entry_token_invalid", resp.text
    assert "set-cookie" not in resp.headers
    for secret in secrets:
        assert secret not in resp.text


def test_s5_exchange_success_sets_hardened_cookie(env, caplog):
    caplog.set_level(logging.DEBUG)
    client = TestClient(_app(), base_url=BASE_URL)
    token = _issue()

    resp = _exchange(client, token)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["authenticated"] is True and body["csrf_token"]
    cookie = resp.headers["set-cookie"].lower()
    assert f"{SESSION_COOKIE}=" in cookie
    for attr in ("httponly", "samesite=strict", "path=/", "max-age=43200"):
        assert attr in cookie, cookie
    session_value = _cookie_value(client)
    assert session_value not in resp.text and token not in resp.text
    assert token not in caplog.text and session_value not in caplog.text
    assert body["csrf_token"] not in caplog.text


def test_s5_session_endpoint_shape(env):
    app = _app()
    anon = TestClient(app, base_url=BASE_URL).get("/api/auth/session")
    assert anon.status_code == 200
    assert anon.json() == {"authenticated": False}

    client, csrf = make_session(app)
    authed = client.get("/api/auth/session")
    assert authed.status_code == 200
    assert authed.json() == {"authenticated": True, "csrf_token": csrf}


def test_s5_token_replay_is_refused(env):
    client = TestClient(_app(), base_url=BASE_URL)
    token = _issue()
    assert _exchange(client, token).status_code == 200

    second = _exchange(TestClient(_app(), base_url=BASE_URL), token)

    _assert_invalid(second, [token])


def test_s5_expired_token_is_refused(env):
    token = _issue()
    path = _entry_dir(env.config_path) / hashlib.sha256(token.encode()).hexdigest()
    path.write_text(json.dumps({"expires_at": time.time() - 10}), encoding="utf-8")

    resp = _exchange(TestClient(_app(), base_url=BASE_URL), token)

    _assert_invalid(resp, [token])


def test_s5_token_file_beyond_ttl_cap_is_refused(env):
    token = _issue()
    path = _entry_dir(env.config_path) / hashlib.sha256(token.encode()).hexdigest()
    path.write_text(json.dumps({"expires_at": time.time() + 10_000}), encoding="utf-8")

    resp = _exchange(TestClient(_app(), base_url=BASE_URL), token)

    _assert_invalid(resp, [token])


def test_s5_unknown_token_is_refused_with_same_response_as_expired(env):
    client = TestClient(_app(), base_url=BASE_URL)
    unknown = _exchange(client, "x" * 43)
    _assert_invalid(unknown, ["x" * 43])

    token = _issue()
    path = _entry_dir(env.config_path) / hashlib.sha256(token.encode()).hexdigest()
    path.write_text(json.dumps({"expires_at": time.time() - 10}), encoding="utf-8")
    expired = _exchange(client, token)

    assert unknown.status_code == expired.status_code
    assert unknown.json() == expired.json()  # 사유 비구별


@pytest.mark.parametrize("tamper", ["symlink_dir", "mode_0755"])
def test_s5_tampered_entry_dir_is_refused_for_issue_and_exchange(env, tamper):
    entry_dir = _entry_dir(env.config_path)
    token = _issue()
    if tamper == "mode_0755":
        entry_dir.chmod(0o755)
    else:
        real = entry_dir.with_name("console-entry-real")
        entry_dir.rename(real)
        entry_dir.symlink_to(real, target_is_directory=True)

    resp = _exchange(TestClient(_app(), base_url=BASE_URL), token)
    _assert_invalid(resp, [token])

    try:
        reissued = _issue()
    except Exception:
        reissued = None
    assert not reissued, "issue must refuse a tampered entry directory"


def test_s5_exchange_requires_origin(env):
    token = _issue()

    resp = _exchange(TestClient(_app(), base_url=BASE_URL), token, origin=None)

    assert resp.status_code == 403
    assert _code(resp) == "origin_required"
    assert "set-cookie" not in resp.headers


def test_s5_concurrent_exchange_of_one_token_succeeds_once(env):
    token = _issue()
    app = _app()
    results: list[int] = []
    barrier = threading.Barrier(8)

    def worker():
        client = TestClient(app, base_url=BASE_URL)
        barrier.wait()
        results.append(_exchange(client, token).status_code)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    assert sorted(results) == [200] + [401] * 7


def test_s5_error_responses_never_echo_credentials(env, caplog):
    caplog.set_level(logging.DEBUG)
    app = _app()
    client, csrf = make_session(app)
    cookie = _cookie_value(client)

    bad = client.post(
        PROBE_PATH, json={}, headers={"Origin": ORIGIN, "X-CSRF-Token": "wrong-" + csrf}
    )

    assert bad.status_code == 403
    for secret in (csrf, cookie):
        assert secret not in bad.text
        assert secret not in caplog.text
