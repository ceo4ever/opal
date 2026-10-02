"""
@header {
  "module": "tests.test_legacy_brain_policy",
  "layer": "test",
  "domain": "console",
  "description": "구형 Brain 정책·spawn 게이트 공개 계약 RED-first 테스트(S-6 정책 측·S-7). console.config.json의 legacy_brain_enabled는 JSON true일 때만 켜짐(키 없음·문자열·1·null·prewarm_projects만 있음·파손은 꺼짐, 업그레이드 구성 포함). 꺼짐일 때 Registry(prime·ask·submit_job는 LegacyBrainDisabled, prewarm 무동작, checkout_warm_handle은 None)·풀 리필 진입점·opbr_adapter.prime_and_ask·서버 lifespan 선프라임이 모두 subprocess.Popen 대체 호출 0회임을 단언한다. 켜짐일 때 어댑터는 shell=False·cwd=project_path·--allowedTools Bash,Read,Grep,Glob로 Popen을 호출하고 turn 종료 시(정상·비JSON·타임아웃) running_turns가 0으로 돌아온다. S-7: turn 진행 중 끄기는 진행 중 turn을 보존하고 running_turns 1을 보고하며 이후 모든 경로가 거절되고 Popen 누적이 늘지 않는다. 여러 스레드가 동시에 spawn을 시도하는 동안 끄는 경합 100회에서 set_enabled(False) 반환 시점의 Popen 누적 횟수가 끝까지 변하지 않는다. 실제 claude 호출 0회(Popen 대체·실제 spawn 가드), 임시 CONFIG_PATH·OPAL_HOME.",
  "task": "175-261001-opd-콘솔-POST-인증-게이트",
  "scenarios": ["S-6", "S-7"],
  "exports": [],
  "depends": ["adapters.brain_policy", "adapters.opbr_adapter", "adapters.brain_session", "config", "main", "routers.brain", "tests.auth_helpers"]
}
"""
from __future__ import annotations

import json
import threading
import time

import pytest
from fastapi.testclient import TestClient

from dashboard.backend.tests.auth_helpers import (  # noqa: F401  (fixture 등록)
    BASE_URL,
    FakePopen,
    authed_client,
    isolated_console_home,
    no_real_spawn,
    reset_registry,
    set_legacy_brain_policy,
)

SID = "aaaaaaaa-0001-0001-0001-000000000001"
SID2 = "aaaaaaaa-0002-0002-0002-000000000002"

# 꺼짐으로 해석돼야 하는 구성(키 없음·비불리언·prewarm만 있음·false·파손)
OFF_CONFIGS = {
    "keyless": {"scan_roots": ["/nonexistent-root"]},
    "string_true": {"legacy_brain_enabled": "true"},
    "int_one": {"legacy_brain_enabled": 1},
    "null": {"legacy_brain_enabled": None},
    "false": {"legacy_brain_enabled": False},
    "upgrade_prewarm_only": {
        "scan_roots": ["/nonexistent-root"],
        "prewarm_projects": ["/p/one", "/p/two"],
    },
}


@pytest.fixture
def project(tmp_path):
    path = tmp_path / "proj"
    path.mkdir()
    return str(path)


@pytest.fixture
def popen(monkeypatch):
    fake = FakePopen()
    monkeypatch.setattr("subprocess.Popen", fake)
    return fake


@pytest.fixture(autouse=True)
def policy_off_after(isolated_console_home):
    """각 테스트 뒤 정책을 꺼짐으로 되돌린다(전역 싱글턴 상태 누수 방지)."""
    yield
    try:
        set_legacy_brain_policy(isolated_console_home, None)
    except ImportError:  # 정책 모듈 미구현 상태(RED)에서는 되돌릴 상태가 없다
        pass


def _write_config(path, data) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _wait(predicate, timeout=3.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


# ── 설정 해석 (D-15) ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", sorted(OFF_CONFIGS))
def test_loader_and_policy_treat_non_true_as_off(isolated_console_home, name):
    from dashboard.backend import config
    from dashboard.backend.adapters import brain_policy

    set_legacy_brain_policy(isolated_console_home, True)  # 먼저 켠 뒤
    _write_config(isolated_console_home, OFF_CONFIGS[name])  # 설정만 꺼짐 구성으로 바꾼다

    assert config.load_legacy_brain_enabled() is False
    brain_policy.reload_from_config()
    assert brain_policy.is_enabled() is False


def test_loader_off_for_missing_and_corrupt_file(isolated_console_home):
    from dashboard.backend import config
    from dashboard.backend.adapters import brain_policy

    assert not isolated_console_home.exists()
    assert config.load_legacy_brain_enabled() is False

    isolated_console_home.write_text("{not json", encoding="utf-8")
    assert config.load_legacy_brain_enabled() is False
    brain_policy.reload_from_config()
    assert brain_policy.is_enabled() is False


def test_loader_and_policy_on_only_for_json_true(isolated_console_home):
    from dashboard.backend import config
    from dashboard.backend.adapters import brain_policy

    _write_config(isolated_console_home, {"legacy_brain_enabled": True, "prewarm_projects": []})

    assert config.load_legacy_brain_enabled() is True
    brain_policy.reload_from_config()
    assert brain_policy.is_enabled() is True
    assert brain_policy.running_turns() == 0


def test_existing_load_config_contract_is_unchanged(isolated_console_home):
    from dashboard.backend import config

    _write_config(
        isolated_console_home,
        {"scan_roots": ["/r"], "prewarm_projects": ["/p"], "legacy_brain_enabled": True},
    )

    cfg = config.load_config()

    assert cfg.scan_roots == ["/r"] and cfg.prewarm_projects == ["/p"]
    assert not hasattr(cfg, "legacy_brain_enabled")  # 기존 ConsoleConfig 시그니처 불변


def test_legacy_brain_disabled_is_a_runtime_error():
    from dashboard.backend.adapters.brain_policy import LegacyBrainDisabled

    assert issubclass(LegacyBrainDisabled, RuntimeError)


# ── 꺼짐: 모든 진입점에서 spawn 0회 (D-16, D-17) ──────────────────────────────

@pytest.mark.parametrize("name", sorted(OFF_CONFIGS))
def test_s6_off_blocks_every_entry_point(isolated_console_home, project, popen, reset_registry, name):
    from dashboard.backend.adapters import brain_policy, opbr_adapter
    from dashboard.backend.adapters.brain_policy import LegacyBrainDisabled

    reg = reset_registry
    _write_config(isolated_console_home, OFF_CONFIGS[name])
    brain_policy.reload_from_config()
    threads_before = threading.active_count()

    with pytest.raises(LegacyBrainDisabled):
        reg.prime(SID, project)
    with pytest.raises(LegacyBrainDisabled):
        reg.ask(SID, "q", project)
    with pytest.raises(LegacyBrainDisabled):
        reg.submit_job(SID, "q", project)
    reg.prewarm(project)  # 무동작(예외 없음)
    with reg._pool_lock:
        reg._pool[project] = ["warm-handle"]
    assert reg.checkout_warm_handle(project) is None  # 풀을 비우고 리필하지 않는다
    with reg._pool_lock:
        reg._pool_inflight[project] = 1
    try:
        reg._prime_into_pool(project)  # 리필 스레드 진입점: 종료 또는 LegacyBrainDisabled
    except LegacyBrainDisabled:
        pass
    assert reg._pool_inflight.get(project, 0) == 0  # inflight는 정상 감소
    with pytest.raises(LegacyBrainDisabled):
        opbr_adapter.prime_and_ask("q", project, SID, cold=True)

    time.sleep(0.1)
    assert popen.call_count == 0
    assert threading.active_count() <= threads_before


# ── 꺼짐: lifespan 선프라임 (S-6 ②) ───────────────────────────────────────────

def _lifespan_prewarm_calls(monkeypatch, reg):
    from dashboard.backend.main import app

    calls: list[str] = []
    monkeypatch.setattr(reg, "prewarm", lambda p: calls.append(p))
    with TestClient(app, base_url=BASE_URL):
        time.sleep(0.3)  # 선프라임 스레드가 있었다면 실행될 시간
    return calls


@pytest.mark.parametrize("name", sorted(OFF_CONFIGS))
def test_s6_lifespan_does_not_preprime_when_off(
    monkeypatch, isolated_console_home, project, popen, reset_registry, name
):
    set_legacy_brain_policy(isolated_console_home, True)  # 메모리는 켜짐, 설정은 꺼짐 구성
    cfg = dict(OFF_CONFIGS[name])
    cfg["prewarm_projects"] = [project, project + "-2"]
    _write_config(isolated_console_home, cfg)

    calls = _lifespan_prewarm_calls(monkeypatch, reset_registry)

    assert calls == []  # lifespan이 설정에서 정책을 다시 읽어 선프라임 스레드를 만들지 않는다
    assert popen.call_count == 0


def test_s6_lifespan_preprimes_projects_when_on(
    monkeypatch, isolated_console_home, project, popen, reset_registry
):
    targets = [project, project + "-2"]
    _write_config(
        isolated_console_home, {"legacy_brain_enabled": True, "prewarm_projects": targets}
    )

    calls = _lifespan_prewarm_calls(monkeypatch, reset_registry)

    assert sorted(calls) == sorted(targets)


# ── 켜짐: 어댑터 계약 보존 + running_turns 회수 (D-16) ─────────────────────────

def test_s6_on_adapter_spawns_with_fixed_argv(isolated_console_home, project, popen):
    from dashboard.backend.adapters import brain_policy, opbr_adapter

    set_legacy_brain_policy(isolated_console_home, True)

    result = opbr_adapter.prime_and_ask("질문", project, SID, cold=True)

    assert result["answer"] == "ok" and result["session_id"]
    assert popen.call_count == 1
    argv = popen.argv(0)
    assert argv[0] == "claude"
    assert argv[argv.index("--allowedTools") + 1] == "Bash,Read,Grep,Glob"
    assert argv[argv.index("--session-id") + 1] == SID
    _, kwargs = popen.calls[0]
    assert kwargs.get("shell") is False
    assert kwargs.get("cwd") == project
    assert brain_policy.running_turns() == 0


def test_running_turns_returns_to_zero_after_failures(
    monkeypatch, isolated_console_home, project
):
    from dashboard.backend.adapters import brain_policy, opbr_adapter

    set_legacy_brain_policy(isolated_console_home, True)

    bad = FakePopen(stdout="not-json")
    monkeypatch.setattr("subprocess.Popen", bad)
    with pytest.raises(RuntimeError):
        opbr_adapter.prime_and_ask("q", project, SID, cold=True)
    assert brain_policy.running_turns() == 0

    slow = FakePopen(timeout_on_communicate=True)
    monkeypatch.setattr("subprocess.Popen", slow)
    with pytest.raises(RuntimeError, match="timeout"):
        opbr_adapter.prime_and_ask("q", project, SID2, cold=True, timeout=0.05)
    assert slow.procs[0].killed is True
    assert brain_policy.running_turns() == 0


# ── S-7 ─────────────────────────────────────────────────────────────────────

class _FakeScanProject:
    def __init__(self, path):
        self.path = path
        self.is_opal = True


def test_s7_disable_during_turn_keeps_turn_and_blocks_everything_after(
    monkeypatch, isolated_console_home, project, reset_registry
):
    from dashboard.backend.adapters import brain_policy, opbr_adapter
    from dashboard.backend.adapters.brain_policy import LegacyBrainDisabled
    from dashboard.backend.main import app

    reg = reset_registry
    monkeypatch.setattr(
        "dashboard.backend.routers.brain.scan_projects", lambda *a, **k: [_FakeScanProject(project)]
    )
    _write_config(isolated_console_home, {"scan_roots": [project], "legacy_brain_enabled": True})
    brain_policy.reload_from_config()
    release = threading.Event()
    popen = FakePopen(release=release)
    monkeypatch.setattr("subprocess.Popen", popen)
    with reg._pool_lock:
        reg._pool[project] = ["warm-handle"]

    outcome: dict = {}

    def turn():
        try:
            outcome["result"] = opbr_adapter.prime_and_ask("q", project, SID, cold=True)
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=turn, daemon=True)
    worker.start()
    assert _wait(lambda: brain_policy.running_turns() == 1), "turn must be in flight"
    client = authed_client(app)

    # ① 진행 중 끄기
    resp = client.post("/api/brain/legacy", json={"enabled": False})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"enabled": False, "running_turns": 1}
    with reg._pool_lock:
        assert not reg._pool.get(project)  # 풀 핸들 폐기

    # ② 끄기 응답 이후 모든 경로 거절, Popen 누적 불변
    spawned_at_off = popen.call_count
    assert spawned_at_off == 1
    for path, body in [
        ("/api/brain/prime", {"project": project, "session_id": SID2}),
        ("/api/brain/query", {"question": "q", "project": project, "session_id": SID2}),
    ]:
        denied = client.post(path, json=body)
        assert denied.status_code == 403, denied.text
        assert denied.json()["error"]["code"] == "legacy_brain_disabled"
    with pytest.raises(LegacyBrainDisabled):
        reg.prime(SID2, project)
    with pytest.raises(LegacyBrainDisabled):
        reg.submit_job(SID2, "q", project)
    with pytest.raises(LegacyBrainDisabled):
        reg.ask(SID2, "q", project)
    reg.prewarm(project)
    with pytest.raises(LegacyBrainDisabled):
        opbr_adapter.prime_and_ask("q", project, SID2, cold=True)
    time.sleep(0.1)
    assert popen.call_count == spawned_at_off

    # ③ 진행 중이던 turn은 정상 완료
    release.set()
    worker.join(timeout=5)
    assert "error" not in outcome, outcome.get("error")
    assert outcome["result"]["answer"] == "ok"
    assert _wait(lambda: brain_policy.running_turns() == 0)
    assert popen.call_count == spawned_at_off


def test_s7_disable_races_with_concurrent_spawn_attempts(
    monkeypatch, isolated_console_home, project
):
    from dashboard.backend.adapters import brain_policy, opbr_adapter
    from dashboard.backend.adapters.brain_policy import LegacyBrainDisabled

    unexpected: list[Exception] = []
    for i in range(100):
        set_legacy_brain_policy(isolated_console_home, True)  # 매회 새 정책 상태
        popen = FakePopen()
        monkeypatch.setattr("subprocess.Popen", popen)
        barrier = threading.Barrier(9)

        def attempt(n=i):
            barrier.wait()
            try:
                opbr_adapter.prime_and_ask("q", project, f"sid-{n}", cold=True)
            except LegacyBrainDisabled:
                pass
            except Exception as exc:  # noqa: BLE001
                unexpected.append(exc)

        threads = [threading.Thread(target=attempt) for _ in range(8)]
        for t in threads:
            t.start()
        barrier.wait()
        time.sleep((i % 5) * 0.0003)  # 끄기 시점을 매회 어긋나게 한다
        brain_policy.set_enabled(False)
        count_at_off = popen.call_count
        for t in threads:
            t.join(timeout=10)
        assert popen.call_count == count_at_off, f"iteration {i}: spawn after disable returned"

    assert unexpected == []
    assert brain_policy.running_turns() == 0
