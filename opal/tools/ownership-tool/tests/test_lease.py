# @header
# module: ownership_tool.tests.test_lease
# layer: test
# domain: ownership
# description: RED-first — ownership_tool.lease.claim/heartbeat/release/classify 공개 계약 검증 (S-4 lease, S-12) +
#   PLAN D-21 claim_source(session_start/state_transition) 기록·폐쇄enum 거부·승격(강등 없음)·하위호환 기본값 RED
# exports: (none — pytest module)
# depends: ownership_tool.lease (미구현), fixtures/runtime
"""RED 테스트 — 구현 전. ownership_tool.lease 미구현이므로 ImportError로 실패해야 한다."""
from __future__ import annotations

import json
import shutil
import tempfile
import time
from pathlib import Path

FIXTURES_ROOT = Path(__file__).parent / "fixtures"


def _clone_fixtures() -> tuple[Path, Path, Path]:
    tmp = Path(tempfile.mkdtemp(prefix="ownership-fixtures-"))
    shutil.copytree(FIXTURES_ROOT, tmp, dirs_exist_ok=True)
    hub_tmp = tmp / "hub_root"
    # 실물 동형화(W-2'): 워크트리 루트는 허브의 형제가 아니라
    # <hub_root>/.opal-worktrees/task_NNN이고 registry meta는
    # <hub_root>/.opal-worktrees/.meta/에 위치한다(worktree.md 발급 계약).
    wt_tmp = hub_tmp / ".opal-worktrees"
    hub_tmp.mkdir(parents=True, exist_ok=True)
    wt_tmp.mkdir(parents=True, exist_ok=True)
    for p in tmp.rglob("*.json"):
        text = p.read_text(encoding="utf-8")
        text = text.replace("{HUB}", str(hub_tmp)).replace("{WT}", str(wt_tmp))
        p.write_text(text, encoding="utf-8")
    return tmp, hub_tmp, wt_tmp


def test_lease_claim_writes_owner_json_schema():
    """<canonical_task>/run/.runtime/owner.json 스키마(D-5)로 claim이 기록된다.
    기본 TTL 14400s."""
    from ownership_tool import lease  # RED

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    task_path = hub_tmp / "tasks/999-lease-claim-test"
    task_path.mkdir(parents=True)

    result = lease.claim(task_path, session_id="sess-a", now="2026-09-17T15:00:00+09:00")
    owner_file = task_path / "run/.runtime/owner.json"
    assert owner_file.exists()
    data = json.loads(owner_file.read_text(encoding="utf-8"))
    for key in ("task_path", "owner_session_id", "generation", "claimed_at", "lease_expires_at", "status"):
        assert key in data
    assert result["owner_session_id"] == "sess-a"


def test_lease_ttl_override_via_ownership_config():
    """ownership.lease_ttl_sec 오버라이드가 기본 14400s를 대체한다."""
    from ownership_tool import lease  # RED

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    task_path = hub_tmp / "tasks/999-lease-ttl-test"
    task_path.mkdir(parents=True)

    result = lease.claim(
        task_path,
        session_id="sess-a",
        now="2026-09-17T15:00:00+09:00",
        ttl_sec=60,
    )
    assert result["lease_expires_at"] != None
    # 기본 TTL(14400s)이 아니라 오버라이드(60s)가 반영되어야 함
    assert result.get("ttl_sec", 60) == 60


def test_s4_two_leases_same_session_both_current_session_owned():
    """S-4: 세션 A가 X·Y 2건을 lease하면 classify가 둘 다 current_session_owned."""
    from ownership_tool import lease  # RED

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    owner_x = json.loads((tmp / "runtime/owner-current-session.json").read_text(encoding="utf-8"))
    owner_x["owner_session_id"] = "sess-a"
    owner_y = dict(owner_x)
    owner_y["task_path"] = str(hub_tmp / "tasks/201-multi-task-y")

    assert lease.classify(owner_x, "sess-a") == "current_session_owned"
    assert lease.classify(owner_y, "sess-a") == "current_session_owned"


def test_s12_heartbeat_updates_expiry_for_owning_session():
    """S-12: 세션 A heartbeat → heartbeat_at/lease_expires_at 갱신."""
    from ownership_tool import lease  # RED

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    task_path = hub_tmp / "tasks/999-heartbeat-test"
    task_path.mkdir(parents=True)
    claimed = lease.claim(task_path, session_id="sess-a", now="2026-09-17T15:00:00+09:00")

    updated = lease.heartbeat(task_path, session_id="sess-a", now="2026-09-17T15:05:00+09:00")
    assert updated["heartbeat_at"] != claimed["claimed_at"]
    assert updated["lease_expires_at"] != claimed["lease_expires_at"]


def test_s12_heartbeat_from_foreign_session_is_noop():
    """S-12: 세션 B heartbeat → X 무변경(no-op, 생성·이전 없음)."""
    from ownership_tool import lease  # RED

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    task_path = hub_tmp / "tasks/999-heartbeat-foreign-test"
    task_path.mkdir(parents=True)
    claimed = lease.claim(task_path, session_id="sess-a", now="2026-09-17T15:00:00+09:00")

    result = lease.heartbeat(task_path, session_id="sess-b", now="2026-09-17T15:05:00+09:00")
    owner_file = task_path / "run/.runtime/owner.json"
    data = json.loads(owner_file.read_text(encoding="utf-8"))
    assert data["owner_session_id"] == "sess-a"
    assert data["heartbeat_at"] == claimed["heartbeat_at"]
    assert result is None or result.get("noop") is True


def test_s12_release_marks_status_released():
    """S-12: SessionEnd(A) → registry closed, X released."""
    from ownership_tool import lease  # RED

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    task_path = hub_tmp / "tasks/999-release-test"
    task_path.mkdir(parents=True)
    lease.claim(task_path, session_id="sess-a", now="2026-09-17T15:00:00+09:00")

    lease.release(task_path, session_id="sess-a", now="2026-09-17T15:10:00+09:00")
    owner_file = task_path / "run/.runtime/owner.json"
    data = json.loads(owner_file.read_text(encoding="utf-8"))
    assert data["status"] == "released"


def test_s12_ttl_expiry_classified_lease_expired():
    """S-12: TTL 경과 후 classify가 lease_expired → unowned로 이어진다."""
    from ownership_tool import lease  # RED

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    expired = json.loads((tmp / "runtime/owner-expired-lease.json").read_text(encoding="utf-8"))
    result = lease.classify(expired, "sess-anyone", now="2026-09-17T15:00:00+09:00")
    assert result == "lease_expired"


# ─────────────────────────────────────────────────────────────────────────────
# PLAN D-21 — claim_source(session_start / state_transition) RED
# 현재 claim()은 claim_source 인자를 모른다(TypeError) — 아래 전건은 구현 전 RED다.
# ─────────────────────────────────────────────────────────────────────────────

def test_d21_claim_records_claim_source_session_start(monkeypatch):
    """PLAN D-21: W-7 SessionStart 자동 claim은 claim_source=session_start로 기록된다."""
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)
    from ownership_tool import lease  # RED: claim_source 인자 미구현

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    task_path = hub_tmp / "tasks/999-claim-source-session-start"
    task_path.mkdir(parents=True)

    result = lease.claim(
        task_path,
        session_id="sess-a",
        now="2026-09-17T15:00:00+09:00",
        claim_source="session_start",
    )
    assert result["ok"] is True
    assert result["claim_source"] == "session_start"
    owner_file = task_path / "run/.runtime/owner.json"
    data = json.loads(owner_file.read_text(encoding="utf-8"))
    assert data["claim_source"] == "session_start"


def test_d21_claim_records_claim_source_state_transition(monkeypatch):
    """PLAN D-21: W-9 state-tool 첫 상태 전이 claim은 claim_source=state_transition으로
    기록된다."""
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)
    from ownership_tool import lease  # RED: claim_source 인자 미구현

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    task_path = hub_tmp / "tasks/999-claim-source-state-transition"
    task_path.mkdir(parents=True)

    result = lease.claim(
        task_path,
        session_id="sess-a",
        now="2026-09-17T15:00:00+09:00",
        claim_source="state_transition",
    )
    assert result["ok"] is True
    assert result["claim_source"] == "state_transition"


def test_d21_claim_rejects_invalid_claim_source(monkeypatch):
    """PLAN D-21: claim_source 폐쇄 enum(session_start·state_transition) 밖 값은 예외가
    아니라 구조화 거부({"ok": False, "diagnostic": "claim_source_invalid"})다 — 기존
    foreign_owner 거부 관례를 따르며, 거부 시 owner.json을 새로 쓰지 않는다."""
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)
    from ownership_tool import lease  # RED: claim_source 인자 미구현

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    task_path = hub_tmp / "tasks/999-claim-source-invalid"
    task_path.mkdir(parents=True)

    result = lease.claim(
        task_path,
        session_id="sess-a",
        now="2026-09-17T15:00:00+09:00",
        claim_source="bogus_value",
    )
    assert result["ok"] is False
    assert result["diagnostic"] == "claim_source_invalid"
    owner_file = task_path / "run/.runtime/owner.json"
    assert not owner_file.exists()


def test_d21_claim_promotes_session_start_to_state_transition_same_session(monkeypatch):
    """PLAN D-21: 같은 세션이 이미 session_start lease를 가진 상태에서 state_transition으로
    재-claim하면 같은 lease의 claim_source가 state_transition으로 승격되고 generation·
    claimed_at·owner_session_id는 불변이다(새 lease를 만들지 않는다)."""
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)
    from ownership_tool import lease  # RED: claim_source 인자 미구현

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    task_path = hub_tmp / "tasks/999-claim-source-promotion"
    task_path.mkdir(parents=True)

    first = lease.claim(
        task_path,
        session_id="sess-a",
        now="2026-09-17T15:00:00+09:00",
        claim_source="session_start",
    )
    second = lease.claim(
        task_path,
        session_id="sess-a",
        now="2026-09-17T15:05:00+09:00",
        claim_source="state_transition",
    )
    assert second["claim_source"] == "state_transition"
    assert second["generation"] == first["generation"]
    assert second["claimed_at"] == first["claimed_at"]
    assert second["owner_session_id"] == first["owner_session_id"]


def test_d21_claim_does_not_demote_state_transition_to_session_start(monkeypatch):
    """PLAN D-21: state_transition으로 이미 승격된 lease에 session_start로 재-claim해도
    강등되지 않는다 — claim_source는 state_transition으로 유지된다."""
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)
    from ownership_tool import lease  # RED: claim_source 인자 미구현

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    task_path = hub_tmp / "tasks/999-claim-source-no-demotion"
    task_path.mkdir(parents=True)

    lease.claim(
        task_path,
        session_id="sess-a",
        now="2026-09-17T15:00:00+09:00",
        claim_source="state_transition",
    )
    second = lease.claim(
        task_path,
        session_id="sess-a",
        now="2026-09-17T15:05:00+09:00",
        claim_source="session_start",
    )
    assert second["claim_source"] == "state_transition"


def test_d21_resolve_claim_source_defaults_to_state_transition_for_legacy_record():
    """PLAN D-21: claim_source 키가 없는 기존(구버전) lease 레코드는 state_transition으로
    간주한다 — 하위호환, 현행 동작 보전. resolve_ttl_sec과 같은 결의 공개 헬퍼를 기대한다."""
    from ownership_tool import lease  # RED: resolve_claim_source 미구현

    legacy_record = {
        "task_path": "/tmp/legacy-task",
        "owner_session_id": "sess-a",
        "generation": 1,
        "claimed_at": "2026-09-17T15:00:00+09:00",
        "heartbeat_at": "2026-09-17T15:00:00+09:00",
        "lease_expires_at": "2026-09-18T15:00:00+09:00",
        "status": "active",
    }
    assert lease.resolve_claim_source(legacy_record) == "state_transition"
