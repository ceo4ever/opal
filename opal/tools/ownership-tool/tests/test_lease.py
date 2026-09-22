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


# ─────────────────────────────────────────────────────────────────────────────
# TASK 150 — lease 이관(handoff) 계약 RED (S-1 · S-2 claim · S-4 · S-10)
#
# @header 보강: layer=test / domain=opal-pipeline. 이 절은 PLAN 150 W-1이 신설하는
# lease.handoff / lease.handoff_cancel / claim(claimant_root=) 공개 계약만 검증한다 —
# _is_live 같은 private 헬퍼를 직접 호출하지 않는다(harness/red-first.md §2).
# 시간 의존은 전부 고정 now 인자로 주입하고 datetime.now()에 의존하지 않는다.
# ─────────────────────────────────────────────────────────────────────────────

import os
from datetime import datetime, timedelta

HANDOFF_NOW = "2026-09-22T10:00:00+09:00"
HUB_SESSION = "sess-hub-150"
WT_SESSION = "sess-worktree-150"


def _build_registry_handoff_case(tmp_path, *, task_number="300", task_folder="300-lease-handoff"):
    """tmp_path 안에 허브 루트 · registry meta 발급값 · canonical task를 조립한다.

    실물 동형(worktree.md 발급 계약): worktree_root는 `<hub>/.opal-worktrees/task_NNN`,
    registry meta는 `<hub>/.opal-worktrees/.meta/task_NNN.json`, canonical task는
    `<worktree_root>/tasks/<task_folder>`다. 이관 대상 루트는 **registry 발급값**
    (`meta["worktree_root"]`)에서만 취한다 — 경로 문자열로 추론하지 않는다(C-4, D-4).
    """
    hub_root = tmp_path / "hub"
    wt_parent = hub_root / ".opal-worktrees"
    meta_dir = wt_parent / ".meta"
    worktree_root = wt_parent / ("task_" + task_number)
    task_dir = worktree_root / "tasks" / task_folder
    meta_dir.mkdir(parents=True, exist_ok=True)
    task_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "task": task_number,
        "worktree_root": str(worktree_root),
        "allocator_root": str(hub_root),
        "task_home": str(worktree_root),
        "task_folder": task_folder,
        "task_path": str(task_dir),
        "artifact_repo": ".",
        "task_ownership_version": 2,
    }
    (meta_dir / ("task_" + task_number + ".json")).write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )
    return hub_root, meta, task_dir


def _read_lease_record(task_dir):
    """저장 결과(owner.json)를 그대로 읽는다 — 반환 dict가 아니라 **디스크 상태**로 계약을
    관측하기 위한 경로다(red-first.md §2 '저장 결과')."""
    return json.loads(
        (task_dir / "run" / ".runtime" / "owner.json").read_text(encoding="utf-8")
    )


def _hub_owned_then_handoff(tmp_path, **kwargs):
    """허브 세션이 lease를 잡은 뒤 registry 발급 worktree_root로 이관한 상태를 만든다."""
    from ownership_tool import lease  # RED: lease.handoff 미구현

    hub_root, meta, task_dir = _build_registry_handoff_case(tmp_path, **kwargs)
    claimed = lease.claim(
        task_dir,
        session_id=HUB_SESSION,
        claim_source="state_transition",
        now=HANDOFF_NOW,
    )
    assert claimed["ok"] is True
    handed = lease.handoff(
        task_dir,
        session_id=HUB_SESSION,
        to_worktree_root=meta["worktree_root"],
        now=HANDOFF_NOW,
    )
    assert handed["ok"] is True
    return hub_root, meta, task_dir, claimed, handed


def test_s1_hub_reclaim_after_handoff_is_rejected_as_handoff_pending(tmp_path):
    """S-1(AC-1, C-3, H-2): 허브가 이관한 직후 허브 루트를 claimant로 재-claim하면 거부되고,
    진단은 정확히 `handoff_pending`이며 레코드는 무변경이다.

    [MUST] 진단이 `foreign_owner`가 아니라 `handoff_pending`이어야 한다. 이관 레코드는
    `owner_session_id`가 비어 있어 기존 foreign_owner 검사(`lease.py:141-147`)가 그대로
    먼저 걸린다 — 따라서 이 단언이 claim()의 이관 분기가 foreign_owner 검사보다 **앞**에
    놓였음을 관찰 가능한 형태로 고정한다. 순서가 뒤바뀌면 이 테스트가 즉시 깨진다.
    """
    from ownership_tool import lease

    hub_root, meta, task_dir, claimed, handed = _hub_owned_then_handoff(tmp_path)

    # 이관 상태의 원자 교체 결과 — D-3의 5필드가 모두 성립한다.
    record = _read_lease_record(task_dir)
    assert record["status"] == "handoff_pending"
    assert record["owner_session_id"] is None
    assert record["handoff_to_worktree_root"] == meta["worktree_root"]
    assert record["handoff_from_session_id"] == HUB_SESSION
    assert record["handoff_expires_at"]
    # generation은 이관으로 증가하지 않는다(D-3).
    assert record["generation"] == claimed["generation"]

    result = lease.claim(
        task_dir,
        session_id=HUB_SESSION,
        claim_source="state_transition",
        now=HANDOFF_NOW,
        claimant_root=str(hub_root),
    )
    assert result["ok"] is False
    assert result["diagnostic"] == "handoff_pending"

    # 거부는 레코드를 건드리지 않는다 — 이관 대상 루트는 registry 발급값 그대로다.
    assert _read_lease_record(task_dir) == record


def test_s2_claim_succeeds_from_target_root_subdirectory_and_symlink(tmp_path):
    """S-2(AC-2, C-2, H-1) claim 절반: claimant 루트가 (a) 이관 대상 루트와 realpath 동치
    (b) 그 하위 디렉터리 (c) symlink 경유 같은 실체일 때 claim이 모두 성공하고 generation이
    1 증가한다. 소비된 이관 필드는 레코드에 남지 않는다.

    symlink는 tmp_path 안에서 os.symlink로 만든다 — macOS `/tmp`→`/private/tmp` 실체 같은
    환경 의존 경로를 쓰지 않는다.
    """
    from ownership_tool import lease

    for index, kind in enumerate(("target_root", "subdirectory", "symlink")):
        case_root = tmp_path / ("case-" + kind)
        hub_root, meta, task_dir, claimed, _ = _hub_owned_then_handoff(
            case_root,
            task_number="30{}".format(index),
            task_folder="30{}-lease-handoff-{}".format(index, kind),
        )
        worktree_root = meta["worktree_root"]

        if kind == "target_root":
            claimant_root = worktree_root
        elif kind == "subdirectory":
            claimant_root = str(Path(worktree_root) / "tasks")
        else:
            link = case_root / "worktree-symlink"
            os.symlink(worktree_root, link)
            assert os.path.realpath(str(link)) == os.path.realpath(worktree_root)
            claimant_root = str(link)

        result = lease.claim(
            task_dir,
            session_id=WT_SESSION,
            claim_source="session_start",
            now=HANDOFF_NOW,
            claimant_root=claimant_root,
        )
        assert result["ok"] is True, "{}: {}".format(kind, result)
        assert result["owner_session_id"] == WT_SESSION
        assert result["generation"] == claimed["generation"] + 1

        after = _read_lease_record(task_dir)
        assert after["status"] == "active"
        assert after["owner_session_id"] == WT_SESSION
        assert after["generation"] == claimed["generation"] + 1
        # 소비된 이관은 레코드에 잔존하지 않는다 — 남으면 다음 claim 판정이 오염된다.
        assert after.get("handoff_to_worktree_root") is None
        assert after.get("handoff_from_session_id") is None
        assert after.get("handoff_expires_at") is None
        assert lease.classify(after, WT_SESSION, now=HANDOFF_NOW) == "current_session_owned"


def test_s4_third_party_root_and_omitted_claimant_root_are_rejected(tmp_path):
    """S-4(C-3): 이관 대상과 무관한 제3 경로의 claim과, claimant 루트를 생략한 claim은
    둘 다 거부되고 레코드가 변하지 않는다."""
    from ownership_tool import lease

    hub_root, meta, task_dir, _claimed, _handed = _hub_owned_then_handoff(
        tmp_path, task_number="304", task_folder="304-lease-handoff-third-party"
    )
    before = _read_lease_record(task_dir)

    third_root = tmp_path / "somewhere-else"
    third_root.mkdir(parents=True, exist_ok=True)
    rejected_third = lease.claim(
        task_dir,
        session_id="sess-third-150",
        claim_source="session_start",
        now=HANDOFF_NOW,
        claimant_root=str(third_root),
    )
    assert rejected_third["ok"] is False
    assert rejected_third["diagnostic"] == "handoff_pending"
    assert _read_lease_record(task_dir) == before

    rejected_omitted = lease.claim(
        task_dir,
        session_id="sess-third-150",
        claim_source="session_start",
        now=HANDOFF_NOW,
    )
    assert rejected_omitted["ok"] is False
    assert rejected_omitted["diagnostic"] == "handoff_pending"
    assert _read_lease_record(task_dir) == before


def test_s10_expired_handoff_folds_to_unowned_and_hub_can_reclaim(tmp_path):
    """S-10(H-5) 전반: 이관 만료 시각이 지난 레코드는 무소유로 판정되고 허브가 다시
    claim할 수 있다. 만료 기준 시각은 레코드의 `handoff_expires_at`에서 파생해 고정
    now로 주입한다 — 이관 TTL 상수값 자체를 테스트에 복제하지 않는다."""
    from ownership_tool import lease

    hub_root, meta, task_dir, claimed, _handed = _hub_owned_then_handoff(
        tmp_path, task_number="305", task_folder="305-lease-handoff-expiry"
    )
    record = _read_lease_record(task_dir)
    after_expiry = (
        datetime.fromisoformat(record["handoff_expires_at"]) + timedelta(minutes=1)
    ).isoformat()

    assert lease.classify(record, HUB_SESSION, now=after_expiry) == "unowned"
    assert lease.classify(record, "sess-anyone-150", now=after_expiry) == "unowned"

    reclaimed = lease.claim(
        task_dir,
        session_id=HUB_SESSION,
        claim_source="state_transition",
        now=after_expiry,
        claimant_root=str(hub_root),
    )
    assert reclaimed["ok"] is True, reclaimed
    assert reclaimed["owner_session_id"] == HUB_SESSION
    assert reclaimed["generation"] == claimed["generation"] + 1
    assert _read_lease_record(task_dir)["status"] == "active"


def test_s10_handoff_cancel_is_allowed_only_for_the_originating_session(tmp_path):
    """S-10(H-5) 후반: 이관취소는 이관을 수행한 세션에만 허용된다. 다른 세션의 취소는
    `not_handoff_owner`로 거부되고 레코드가 변하지 않으며, 출발 세션의 취소는 그 세션
    소유 lease로 되돌린다(generation 불변)."""
    from ownership_tool import lease

    hub_root, meta, task_dir, claimed, _handed = _hub_owned_then_handoff(
        tmp_path, task_number="306", task_folder="306-lease-handoff-cancel"
    )
    before = _read_lease_record(task_dir)

    rejected = lease.handoff_cancel(task_dir, session_id="sess-other-150")
    assert rejected["ok"] is False
    assert rejected["diagnostic"] == "not_handoff_owner"
    assert _read_lease_record(task_dir) == before

    cancelled = lease.handoff_cancel(task_dir, session_id=HUB_SESSION)
    assert cancelled["ok"] is True, cancelled

    after = _read_lease_record(task_dir)
    assert after["status"] == "active"
    assert after["owner_session_id"] == HUB_SESSION
    assert after["generation"] == claimed["generation"]
    assert after.get("handoff_to_worktree_root") is None
    assert after.get("handoff_from_session_id") is None
    assert after.get("handoff_expires_at") is None
    assert lease.classify(after, HUB_SESSION, now=HANDOFF_NOW) == "current_session_owned"


def test_s1_handoff_rejects_non_owner_and_noops_without_live_lease(tmp_path):
    """S-1(AC-1) 보조: `handoff` 자체의 거부·no-op 계약을 고정한다 — 소유자 불일치는
    `not_owner` 거부이고, live lease가 없으면 `{"ok": True, "noop": True,
    "diagnostic": "no_live_lease"}`다(파일을 새로 만들지 않는다)."""
    from ownership_tool import lease

    hub_root, meta, task_dir = _build_registry_handoff_case(
        tmp_path, task_number="307", task_folder="307-lease-handoff-guards"
    )

    # ① live lease 부재 — no-op이며 owner.json을 만들지 않는다.
    noop = lease.handoff(
        task_dir,
        session_id=HUB_SESSION,
        to_worktree_root=meta["worktree_root"],
        now=HANDOFF_NOW,
    )
    assert noop["ok"] is True
    assert noop["noop"] is True
    assert noop["diagnostic"] == "no_live_lease"
    assert not (task_dir / "run" / ".runtime" / "owner.json").exists()

    # ② 소유자 불일치 — not_owner 거부, 레코드 무변경.
    assert lease.claim(
        task_dir, session_id=HUB_SESSION, claim_source="state_transition", now=HANDOFF_NOW
    )["ok"] is True
    before = _read_lease_record(task_dir)
    rejected = lease.handoff(
        task_dir,
        session_id="sess-not-the-owner-150",
        to_worktree_root=meta["worktree_root"],
        now=HANDOFF_NOW,
    )
    assert rejected["ok"] is False
    assert rejected["diagnostic"] == "not_owner"
    assert _read_lease_record(task_dir) == before
