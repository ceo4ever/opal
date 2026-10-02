"""
@header {
  "module": "tests.test_brain_legacy_api",
  "layer": "test",
  "domain": "console",
  "description": "구형 Brain 정책 HTTP 계약 RED-first 테스트(S-6 HTTP 측·S-8). 정책 꺼짐 구성(키 없음·비불리언·prewarm만 있음)에서 POST /api/brain/prime·/api/brain/query는 403 legacy_brain_disabled(error envelope)이고 subprocess.Popen 대체 호출 0회이며, 켜짐 구성에서는 200으로 처리되어 Popen이 shell=False·--allowedTools Bash,Read,Grep,Glob로 호출되고 GET /api/brain/legacy가 enabled true를 돌려준다. S-8: POST /api/brain/legacy는 위험 확인(risk_acknowledged JSON true) 없이 켤 수 없고(400 risk_not_acknowledged, 상태·디스크 불변), 세션·CSRF 없이는 401/403이며, 유효 요청으로 켜면 응답·GET·console.config.json(legacy_brain_enabled JSON true, 다른 키 보존)이 일치하고, 끄면 false 저장·풀 핸들 폐기, 끄는 요청의 저장 실패 시에도 500이지만 메모리 상태는 꺼짐이어서 이후 prime·query가 403이다. 실제 claude 호출 0회(Popen 대체·spawn 가드), 임시 CONFIG_PATH·OPAL_HOME.",
  "task": "179-261001-opd-콘솔-POST-인증-게이트",
  "scenarios": ["S-6", "S-8"],
  "exports": [],
  "depends": ["routers.brain", "adapters.brain_policy", "adapters.brain_session", "config", "main", "tests.auth_helpers"]
}
"""
from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from dashboard.backend.tests.auth_helpers import (  # noqa: F401  (fixture 등록)
    BASE_URL,
    ORIGIN,
    FakePopen,
    authed_client,
    isolated_console_home,
    make_session,
    no_real_spawn,
    reset_registry,
    set_legacy_brain_policy,
)

SID = "aaaaaaaa-0001-0001-0001-000000000001"

OFF_CONFIGS = {
    "keyless": {},
    "string_true": {"legacy_brain_enabled": "true"},
    "int_one": {"legacy_brain_enabled": 1},
    "null": {"legacy_brain_enabled": None},
    "upgrade_prewarm_only": {"prewarm_projects": ["/p/one", "/p/two"]},
}


class _FakeScanProject:
    def __init__(self, path):
        self.path = path
        self.is_opal = True


@pytest.fixture
def env(monkeypatch, isolated_console_home, tmp_path, reset_registry):
    project = tmp_path / "ws" / "proj"
    project.mkdir(parents=True)
    state = type("Env", (), {})()
    state.project = str(project)
    state.config_path = isolated_console_home
    state.registry = reset_registry
    state.base_config = {
        "scan_roots": [str(tmp_path / "ws")],
        "scan_depth": 2,
        "prewarm_projects": [],
    }
    isolated_console_home.write_text(json.dumps(state.base_config), encoding="utf-8")
    fake_scan = lambda *a, **k: [_FakeScanProject(state.project)]  # noqa: E731
    monkeypatch.setattr("dashboard.backend.routers.brain.scan_projects", fake_scan)
    monkeypatch.setattr("dashboard.backend.routers.config.scan_projects", fake_scan)
    state.popen = FakePopen()
    monkeypatch.setattr("subprocess.Popen", state.popen)
    try:
        set_legacy_brain_policy(isolated_console_home, None)
    except ImportError:
        pass
    yield state
    try:
        set_legacy_brain_policy(isolated_console_home, None)
    except ImportError:
        pass


def _app():
    from dashboard.backend.main import app

    return app


def _prime_body(env):
    return {"project": env.project, "session_id": SID}


def _query_body(env):
    return {"question": "질문", "project": env.project, "session_id": SID}


def _code(resp):
    try:
        return resp.json()["error"]["code"]
    except Exception:
        return None


def _disk(env) -> dict:
    return json.loads(env.config_path.read_text(encoding="utf-8"))


def _wait(predicate, timeout=3.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


# ── S-6: HTTP ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", sorted(OFF_CONFIGS))
def test_s6_off_config_rejects_prime_and_query(env, name):
    from dashboard.backend.adapters import brain_policy

    cfg = {**env.base_config, **OFF_CONFIGS[name]}
    env.config_path.write_text(json.dumps(cfg), encoding="utf-8")
    brain_policy.reload_from_config()
    client = authed_client(_app(), raise_server_exceptions=False)

    for path, body in [
        ("/api/brain/prime", _prime_body(env)),
        ("/api/brain/query", _query_body(env)),
    ]:
        resp = client.post(path, json=body)
        assert resp.status_code == 403, f"{name} {path}: {resp.status_code} {resp.text}"
        assert _code(resp) == "legacy_brain_disabled"

    time.sleep(0.1)
    assert env.popen.call_count == 0
    legacy = client.get("/api/brain/legacy")
    assert legacy.status_code == 200
    assert legacy.json() == {"enabled": False, "running_turns": 0}


def test_s6_on_config_processes_prime_and_query_through_popen(env):
    set_legacy_brain_policy(env.config_path, True)
    client = authed_client(_app())

    prime = client.post("/api/brain/prime", json=_prime_body(env))
    assert prime.status_code == 200, prime.text
    assert prime.json() == {"priming": True}
    assert _wait(lambda: env.popen.call_count >= 1), "prime must reach Popen when enabled"

    query = client.post(
        "/api/brain/query", json={**_query_body(env), "session_id": "bbbbbbbb-0001-0001-0001-000000000001"}
    )
    assert query.status_code == 200, query.text
    job_id = query.json()["job_id"]
    assert _wait(lambda: env.popen.call_count >= 2)

    for index in range(env.popen.call_count):
        argv = env.popen.argv(index)
        assert argv[0] == "claude"
        assert argv[argv.index("--allowedTools") + 1] == "Bash,Read,Grep,Glob"
        _, kwargs = env.popen.calls[index]
        assert kwargs.get("shell") is False
        assert kwargs.get("cwd") == env.project

    done = {}
    assert _wait(
        lambda: done.update(
            client.get(
                f"/api/brain/job/{job_id}",
                params={"project": env.project, "session_id": "bbbbbbbb-0001-0001-0001-000000000001"},
            ).json()
        )
        or done.get("status") == "done"
    ), done
    legacy = client.get("/api/brain/legacy")
    assert legacy.status_code == 200
    assert legacy.json()["enabled"] is True
    assert _wait(lambda: client.get("/api/brain/legacy").json()["running_turns"] == 0)


def test_legacy_get_requires_session(env):
    resp = TestClient(_app(), base_url=BASE_URL).get("/api/brain/legacy")

    assert resp.status_code == 401
    assert _code(resp) == "auth_required"


def test_legacy_get_defaults_to_disabled(env):
    client = authed_client(_app())

    resp = client.get("/api/brain/legacy")

    assert resp.status_code == 200
    assert resp.json() == {"enabled": False, "running_turns": 0}


# ── S-8 ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "body",
    [
        {"enabled": True, "risk_acknowledged": False},
        {"enabled": True},
    ],
)
def test_s8_enable_without_risk_acknowledgement_is_400(env, body):
    client = authed_client(_app())
    before = env.config_path.read_bytes()

    resp = client.post("/api/brain/legacy", json=body)

    assert resp.status_code == 400, resp.text
    assert _code(resp) == "risk_not_acknowledged"
    assert client.get("/api/brain/legacy").json()["enabled"] is False
    assert env.config_path.read_bytes() == before


@pytest.mark.parametrize("value", ["true", 1, "yes"])
def test_s8_non_boolean_acknowledgement_does_not_enable(env, value):
    client = authed_client(_app())
    before = env.config_path.read_bytes()

    resp = client.post("/api/brain/legacy", json={"enabled": True, "risk_acknowledged": value})

    assert resp.status_code in (400, 422), resp.text
    assert client.get("/api/brain/legacy").json()["enabled"] is False
    assert env.config_path.read_bytes() == before


def test_s8_enable_requires_session_origin_and_csrf(env):
    app = _app()
    before = env.config_path.read_bytes()
    body = {"enabled": True, "risk_acknowledged": True}

    no_session = TestClient(app, base_url=BASE_URL).post(
        "/api/brain/legacy", json=body, headers={"Origin": ORIGIN}
    )
    no_origin = TestClient(app, base_url=BASE_URL).post("/api/brain/legacy", json=body)
    session_client, _csrf = make_session(app)
    no_csrf = session_client.post("/api/brain/legacy", json=body, headers={"Origin": ORIGIN})

    assert no_session.status_code == 401
    assert no_origin.status_code == 403
    assert no_csrf.status_code == 403
    assert env.config_path.read_bytes() == before
    assert authed_client(app).get("/api/brain/legacy").json()["enabled"] is False


def test_s8_enable_persists_and_preserves_other_keys(env):
    client = authed_client(_app())

    resp = client.post("/api/brain/legacy", json={"enabled": True, "risk_acknowledged": True})

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"enabled": True, "running_turns": 0}
    assert client.get("/api/brain/legacy").json() == {"enabled": True, "running_turns": 0}
    disk = _disk(env)
    assert disk["legacy_brain_enabled"] is True
    for key, value in env.base_config.items():
        assert disk[key] == value  # 다른 키 보존


def test_s8_disable_persists_false_and_drops_pool(env):
    client = authed_client(_app())
    client.post("/api/brain/legacy", json={"enabled": True, "risk_acknowledged": True})
    with env.registry._pool_lock:
        env.registry._pool[env.project] = ["warm-handle"]

    resp = client.post("/api/brain/legacy", json={"enabled": False})

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"enabled": False, "running_turns": 0}
    assert _disk(env)["legacy_brain_enabled"] is False
    with env.registry._pool_lock:
        assert not env.registry._pool.get(env.project)
    denied = client.post("/api/brain/prime", json=_prime_body(env))
    assert denied.status_code == 403 and _code(denied) == "legacy_brain_disabled"
    assert env.popen.call_count == 0


def test_s8_disable_with_save_failure_is_500_but_memory_is_off(env):
    client = authed_client(_app(), raise_server_exceptions=False)
    assert (
        client.post("/api/brain/legacy", json={"enabled": True, "risk_acknowledged": True}).status_code
        == 200
    )
    config_dir = env.config_path.parent
    config_dir.chmod(0o500)  # 임시 파일을 만들 수 없게 해 저장 실패를 주입한다
    try:
        resp = client.post("/api/brain/legacy", json={"enabled": False})
    finally:
        config_dir.chmod(0o700)

    assert resp.status_code == 500, resp.text
    assert client.get("/api/brain/legacy").json()["enabled"] is False
    for path, body in [
        ("/api/brain/prime", _prime_body(env)),
        ("/api/brain/query", _query_body(env)),
    ]:
        denied = client.post(path, json=body)
        assert denied.status_code == 403 and _code(denied) == "legacy_brain_disabled"
    time.sleep(0.1)
    assert env.popen.call_count == 0
