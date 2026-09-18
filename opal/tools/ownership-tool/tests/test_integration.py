# @header
# module: ownership_tool.tests.test_integration
# layer: test
# domain: ownership
# description: W-20 통합 회귀 — 모듈 경계를 가로지르는 실행 경로만 검증한다(단위 테스트가 이미
#   덮은 단일 모듈 계약은 재검증하지 않는다, PRINCIPLES §2). 각 테스트는 fixture를 owner.json에
#   직접 주입하는 대신 session_start_hook.handle()·lease.claim()·session_end_hook.handle() 등
#   실제 공개 API를 순서대로 호출해 한 세션의 lifecycle을 재현한다 — SessionStart claim →
#   PostToolUse heartbeat → Stop 판정 → SessionEnd release 한 줄기, launcher와 무관한
#   PreToolUse guard·lease 상호작용, hub 자동(state_transition) claim → Stop 강제 후보 판정,
#   claim 거부 세션의 Stop이 foreign_owner 진단으로 비차단 통과하는지를 실측 API 호출 연쇄로
#   구성한다.
# exports: (none — pytest module)
# depends: ownership_tool.session_start_hook, ownership_tool.heartbeat_hook, ownership_tool.session_end_hook,
#   ownership_tool.pretooluse_guard_hook, ownership_tool.stop_evaluator, ownership_tool.lease,
#   ownership_tool.fingerprint, fixtures/hub, fixtures/registry, fixtures/hook-payloads, fixtures/fingerprint
"""통합 회귀 — 이미 GREEN인 모듈들의 실행 API를 실제 순서대로 연쇄 호출해 단일 모듈 단위
테스트로는 드러나지 않는 경계간 상호작용(레지스트리 파일 → lease → 판정 → 해제)을 검증한다.

[MUST] 시간 고정값 금지 — lease TTL·만료는 항상 실행 시점 기준 상대 계산(`_now_kst()`)을 쓴다.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

FIXTURES_ROOT = Path(__file__).parent / "fixtures"
_KST = timezone(timedelta(hours=9))


def _now_kst() -> datetime:
    return datetime.now(_KST).replace(microsecond=0)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _clone_fixtures() -> tuple[Path, Path, Path]:
    """fixtures 전체를 임시 디렉터리로 복제하고 {HUB}/{WT} 플레이스홀더를 치환한다
    (기존 test_*.py 전건과 동일한 실물 동형 레이아웃 — wt_tmp = hub_tmp/.opal-worktrees)."""
    tmp = Path(tempfile.mkdtemp(prefix="ownership-fixtures-integration-"))
    shutil.copytree(FIXTURES_ROOT, tmp, dirs_exist_ok=True)
    hub_tmp = tmp / "hub_root"
    wt_tmp = hub_tmp / ".opal-worktrees"
    hub_tmp.mkdir(parents=True, exist_ok=True)
    wt_tmp.mkdir(parents=True, exist_ok=True)
    for p in tmp.rglob("*.json"):
        text = p.read_text(encoding="utf-8")
        text = text.replace("{HUB}", str(hub_tmp)).replace("{WT}", str(wt_tmp))
        p.write_text(text, encoding="utf-8")
    return tmp, hub_tmp, wt_tmp


def _load(tmp: Path, rel: str) -> dict:
    return json.loads((tmp / rel).read_text(encoding="utf-8"))


def _write_task_ownership_copy(ownership_core, worktree_root: Path, registry_entry: dict) -> None:
    """D-20 발급값 사본 — worktree-tool이 내려보내는 <worktree_root>/.opal/task-ownership.json.
    session_start_hook·pretooluse_guard_hook의 root 해석이 이 사본을 읽는다."""
    copy_path = ownership_core.task_ownership_copy_path(worktree_root)
    copy_path.parent.mkdir(parents=True, exist_ok=True)
    copy_body = {
        "allocator_root": registry_entry["allocator_root"],
        "task_home": registry_entry["task_home"],
        "task_folder": registry_entry["task_folder"],
        "task_path": registry_entry["task_path"],
        "artifact_repo": registry_entry["artifact_repo"],
        "task_ownership_version": registry_entry["task_ownership_version"],
    }
    copy_path.write_text(json.dumps(copy_body, ensure_ascii=False), encoding="utf-8")


def _seed_worktree_registry(tmp, hub_tmp, wt_tmp, wt_fixture_name: str, task_num: str):
    """<wt_tmp>/.meta/task_<task_num>.json에 WT-<wt_fixture_name> registry 사본을 배치하고
    worktree_root를 만든다. 발급값 사본(task-ownership.json)도 함께 내려보낸다
    (test_session_start.py S-10 선례와 동일한 방식)."""
    from ownership_tool import ownership_core

    worktree_root = wt_tmp / f"task_{task_num}"
    worktree_root.mkdir(parents=True, exist_ok=True)
    meta_dir = wt_tmp / ".meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    src = tmp / "registry" / "active" / wt_fixture_name / ".meta" / f"task_{task_num}.json"
    dst = meta_dir / f"task_{task_num}.json"
    shutil.copy(src, dst)
    registry_entry = json.loads(dst.read_text(encoding="utf-8"))
    _write_task_ownership_copy(ownership_core, worktree_root, registry_entry)
    task_dir = Path(registry_entry["task_path"])
    task_dir.mkdir(parents=True, exist_ok=True)
    return worktree_root, task_dir, registry_entry


# ─────────────────────────────────────────────────────────────────────────────
# T1 — WT-138: SessionStart claim → PostToolUse heartbeat → 반복 Stop(fingerprint
# 영속 roundtrip 3종) → SessionEnd release. 단위 테스트는 이 흐름의 각 조각을 owner.json
# 직접 주입으로 독립 검증하지만, 여기서는 실제 공개 API 호출 연쇄가 만든 디스크 상태를
# 다음 단계가 그대로 읽게 해 경계간 데이터 흐름을 검증한다.
# ─────────────────────────────────────────────────────────────────────────────

def test_wt138_full_chain_session_start_heartbeat_stop_repeated_fingerprint_sessionend(monkeypatch):
    from ownership_tool import heartbeat_hook, ownership_core, session_end_hook, session_start_hook, stop_evaluator

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root, task_dir, _entry = _seed_worktree_registry(tmp, hub_tmp, wt_tmp, "WT-138", "138")

    # setup: 실제 state-tool show 응답(a/b/c)에서 "data" 부분만 real state.json으로
    # 실물 배치한다 — resolve_worktree._read_state가 읽는 파일은 show_json이 아니라
    # <task_path>/state.json이다.
    show_a = _load(tmp, "fingerprint/show-a-baseline.json")
    (task_dir / "state.json").write_text(
        json.dumps(show_a["data"], ensure_ascii=False), encoding="utf-8"
    )

    session_id = "sess-138-chain"
    now = _now_kst()

    # ① SessionStart — 실제 handle() 호출로 lease.claim + session_registry.register
    payload = _load(tmp, "hook-payloads/session-start.json")
    payload["cwd"] = str(worktree_root)
    payload["session_id"] = session_id
    r1 = session_start_hook.handle(
        payload, project_root=worktree_root, env_file_path=None, now=_iso(now)
    )
    assert r1["lease_claimed"] is True
    assert r1["registered"] is True

    # ② PostToolUse — heartbeat_hook이 ①이 만든 lease만 읽어 갱신한다(claim 재호출 없음).
    post_payload = _load(tmp, "hook-payloads/posttooluse.json")
    post_payload["cwd"] = str(worktree_root)
    post_payload["session_id"] = session_id
    r2 = heartbeat_hook.handle(post_payload, project_root=worktree_root, now=_iso(now + timedelta(minutes=1)))
    assert str(task_dir) in r2["refreshed"]
    assert r2["noop"] is False

    # ③ Stop #1 — stop_hook_active=False, forced worktree_canonical(1건) → block_continue.
    # 영속 receipt(fingerprint.save_receipt)가 디스크에 실제로 쓰인다.
    stop_payload = _load(tmp, "hook-payloads/stop.json")
    stop_payload["cwd"] = str(worktree_root)
    stop_payload["session_id"] = session_id
    stop_payload["stop_hook_active"] = False
    result1 = stop_evaluator.evaluate(
        stop_payload, project_root=worktree_root, now=_iso(now + timedelta(minutes=2)), show_json=show_a
    )
    assert result1["decision_kind"] == "block_continue"
    assert result1["block_count"] == 1
    receipt_path = ownership_core.stop_receipt_path(worktree_root, session_id)
    assert receipt_path.exists(), "stop receipt must be persisted to disk"

    # ④ Stop #2 — stop_hook_active=True, prior_receipt 미지정(자동 load_receipt) +
    # 동일 show_json → fingerprint 동일 → allow_no_progress_same_fingerprint.
    stop_payload["stop_hook_active"] = True
    result2 = stop_evaluator.evaluate(
        stop_payload, project_root=worktree_root, now=_iso(now + timedelta(minutes=3)), show_json=show_a
    )
    assert result2["decision_kind"] == "allow_no_progress_same_fingerprint"

    # ⑤ Stop #3 — note/run_log만 바뀐 변형(fingerprint 정규화에서 제외되는 필드) →
    # ④가 저장한 receipt와 여전히 동일 fingerprint → no-progress 유지("로그만 변경").
    show_c = _load(tmp, "fingerprint/show-c-note-runlog-only.json")
    result3 = stop_evaluator.evaluate(
        stop_payload, project_root=worktree_root, now=_iso(now + timedelta(minutes=4)), show_json=show_c
    )
    assert result3["decision_kind"] == "allow_no_progress_same_fingerprint"

    # ⑥ Stop #4 — 행 status가 실제로 바뀐 변형("의미 변경") → 재차단, block_count는
    # ③이 저장한 1에서 +1 = 2(④·⑤는 no-progress 경로라 block_count를 증가시키지 않는다).
    show_b = _load(tmp, "fingerprint/show-b-status-changed.json")
    result4 = stop_evaluator.evaluate(
        stop_payload, project_root=worktree_root, now=_iso(now + timedelta(minutes=5)), show_json=show_b
    )
    assert result4["decision_kind"] == "block_continue"
    assert result4["block_count"] == 2

    # ⑦ SessionEnd — 실제 release + registry close.
    end_payload = _load(tmp, "hook-payloads/sessionend.json")
    end_payload["cwd"] = str(worktree_root)
    end_payload["session_id"] = session_id
    r_end = session_end_hook.handle(end_payload, project_root=worktree_root, now=_iso(now + timedelta(minutes=6)))
    assert r_end["released"] is True
    assert r_end["registry_closed"] is True

    # ⑧ 이후 PostToolUse는 released lease를 owned로 보지 않으므로 no-op이다 —
    # heartbeat_hook이 ⑦의 release를 실제로 관측한다는 것을 확인한다.
    r3 = heartbeat_hook.handle(post_payload, project_root=worktree_root, now=_iso(now + timedelta(minutes=7)))
    assert r3["refreshed"] == []


# ─────────────────────────────────────────────────────────────────────────────
# T2 — WT-127: SessionStart claim(가벼운 변형) → PostToolUse → SessionEnd release →
# PostToolUse no-op. T1과 다른 registry 고정값(WT-127, attribution_state 키 부재)을 실측해
# 두 registry 변형이 같은 코드 경로로 처리됨을 확인한다.
# ─────────────────────────────────────────────────────────────────────────────

def test_wt127_session_start_claim_heartbeat_then_sessionend_release_heartbeat_noop(monkeypatch):
    from ownership_tool import heartbeat_hook, session_end_hook, session_start_hook

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root, task_dir, _entry = _seed_worktree_registry(tmp, hub_tmp, wt_tmp, "WT-127", "127")
    (task_dir / "state.json").write_text(
        json.dumps({"task_id": "127-260912-oppl-E2E-하네스-구현", "current_status": "in_progress",
                    "next_action": "EXECUTE 작업 진행 중"}, ensure_ascii=False),
        encoding="utf-8",
    )

    session_id = "sess-127-chain"
    now = _now_kst()

    payload = _load(tmp, "hook-payloads/session-start.json")
    payload["cwd"] = str(worktree_root)
    payload["session_id"] = session_id
    r1 = session_start_hook.handle(payload, project_root=worktree_root, env_file_path=None, now=_iso(now))
    assert r1["lease_claimed"] is True

    post_payload = _load(tmp, "hook-payloads/posttooluse.json")
    post_payload["cwd"] = str(worktree_root)
    post_payload["session_id"] = session_id
    r2 = heartbeat_hook.handle(post_payload, project_root=worktree_root, now=_iso(now + timedelta(minutes=1)))
    assert r2["noop"] is False

    end_payload = _load(tmp, "hook-payloads/sessionend.json")
    end_payload["cwd"] = str(worktree_root)
    end_payload["session_id"] = session_id
    r_end = session_end_hook.handle(end_payload, project_root=worktree_root, now=_iso(now + timedelta(minutes=2)))
    assert r_end["released"] is True

    r3 = heartbeat_hook.handle(post_payload, project_root=worktree_root, now=_iso(now + timedelta(minutes=3)))
    # lease는 release로 owned 목록에서 빠지므로 refreshed는 비어 있다 — session registry
    # 재등록(registry_refreshed) 자체는 heartbeat_hook의 별도 관심사(레코드 존재 여부만
    # 봄)이므로 여기서는 lease-레벨 no-op만 단언한다(test_heartbeat.py의 관용과 동일).
    assert r3["refreshed"] == []


# ─────────────────────────────────────────────────────────────────────────────
# T3 — SAME-WORKTREE-TWO-SESSIONS(task_220): PreToolUse guard와 lease 상태의 상호작용을
# 실측 claim/release 연쇄로 검증한다. 기존 test_pretooluse_guard.py는 owner.json을 직접
# 주입하지만, 여기서는 session_start_hook.handle()이 만든 실제 lease를 guard가 읽고,
# session_end_hook.handle()이 그 lease를 해제한 뒤 guard의 판정이 실제로 바뀌는지를 본다.
# ─────────────────────────────────────────────────────────────────────────────

def test_same_worktree_two_sessions_guard_blocks_then_unblocks_after_release(monkeypatch):
    from ownership_tool import pretooluse_guard_hook, session_end_hook, session_start_hook

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root = wt_tmp / "task_220"
    worktree_root.mkdir(parents=True, exist_ok=True)
    task_folder = "220-shared-worktree-task"
    task_dir = worktree_root / "tasks" / task_folder
    registry_entry = {
        "allocator_root": str(hub_tmp),
        "task_home": str(worktree_root),
        "task_folder": task_folder,
        "task_path": str(task_dir),
        "artifact_repo": ".",
        "task_ownership_version": 2,
    }
    meta_dir = wt_tmp / ".meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "task_220.json").write_text(json.dumps(registry_entry), encoding="utf-8")
    task_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        FIXTURES_ROOT / "worktrees" / "SAME-WORKTREE-TWO-SESSIONS" / "tasks" / task_folder / "state.json",
        task_dir / "state.json",
    )

    from ownership_tool import ownership_core

    _write_task_ownership_copy(ownership_core, worktree_root, registry_entry)

    now = _now_kst()

    # ① sess-1이 SessionStart로 이 worktree를 실제로 claim한다.
    start_payload = _load(tmp, "hook-payloads/session-start.json")
    start_payload["cwd"] = str(worktree_root)
    start_payload["session_id"] = "sess-1"
    r1 = session_start_hook.handle(start_payload, project_root=worktree_root, env_file_path=None, now=_iso(now))
    assert r1["lease_claimed"] is True

    # ② sess-2의 Edit·git commit은 foreign_session_owned로 차단된다(guard가 ①의 실제
    # lease를 읽는다 — owner.json을 이 테스트가 직접 쓴 적이 없다).
    edit_payload = _load(tmp, "hook-payloads/pretooluse.json")
    edit_payload["cwd"] = str(worktree_root)
    edit_payload["tool_name"] = "Edit"
    r_edit = pretooluse_guard_hook.handle(edit_payload, project_root=worktree_root, session_id="sess-2")
    assert r_edit["decision"] == "block"
    assert r_edit["classification"] == "foreign_session_owned"

    commit_payload = dict(edit_payload)
    commit_payload["tool_name"] = "Bash"
    commit_payload["tool_input"] = {"command": "git commit -m x"}
    r_commit = pretooluse_guard_hook.handle(commit_payload, project_root=worktree_root, session_id="sess-2")
    assert r_commit["decision"] == "block"

    # ③ sess-1이 SessionEnd로 실제 release한다.
    end_payload = _load(tmp, "hook-payloads/sessionend.json")
    end_payload["cwd"] = str(worktree_root)
    end_payload["session_id"] = "sess-1"
    r_end = session_end_hook.handle(end_payload, project_root=worktree_root, now=_iso(now + timedelta(minutes=1)))
    assert r_end["released"] is True

    # ④ 해제 후 sess-2의 같은 Edit은 더 이상 차단되지 않는다(classification이 unowned로
    # 바뀌었다는 것을 guard 자신의 판정으로 확인한다 — 두 모듈 간 상태 전달을 검증).
    r_edit_after = pretooluse_guard_hook.handle(edit_payload, project_root=worktree_root, session_id="sess-2")
    assert r_edit_after["decision"] != "block"
    assert r_edit_after["classification"] != "foreign_session_owned"


# ─────────────────────────────────────────────────────────────────────────────
# T4 — HUB-TWO-SESSIONS(task 210): 세션 A가 lease.claim(claim_source=state_transition)으로
# 자동 허브 claim을 실제로 수행하고, 세션 B의 같은 claim은 foreign_owner로 거부된다. A의
# claim이 stop_evaluator의 forced 후보 판정에 그대로 반영되는지(evidence.claim_source
# 노출 포함) 확인한다.
# ─────────────────────────────────────────────────────────────────────────────

def test_hub_two_sessions_real_claim_foreign_rejected_and_stop_forces_block_continue(monkeypatch):
    from ownership_tool import lease, stop_evaluator

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    shutil.copytree(
        FIXTURES_ROOT / "hub" / "HUB-TWO-SESSIONS" / "tasks", hub_tmp / "tasks", dirs_exist_ok=True
    )
    task_dir = hub_tmp / "tasks" / "210-two-session-x"
    now = _now_kst()

    claim_a = lease.claim(task_dir, session_id="sess-a", claim_source="state_transition", now=_iso(now))
    assert claim_a["ok"] is True

    claim_b = lease.claim(task_dir, session_id="sess-b", claim_source="state_transition", now=_iso(now))
    assert claim_b["ok"] is False
    assert claim_b["diagnostic"] == "foreign_owner"

    payload = _load(tmp, "hook-payloads/stop.json")
    payload["cwd"] = str(hub_tmp)
    payload["session_id"] = "sess-a"
    payload["stop_hook_active"] = False

    result = stop_evaluator.evaluate(payload, project_root=hub_tmp, now=_iso(now + timedelta(minutes=1)))
    assert result["decision_kind"] == "block_continue"
    forced = [c for c in result["candidates"] if c.get("forced")]
    assert any(c.get("task_id") == "210-two-session-x" for c in forced)
    candidate = next(c for c in result["candidates"] if c.get("task_id") == "210-two-session-x")
    assert candidate["evidence"].get("claim_source") == "state_transition"

    # ⑤ S-13 — sess-b(비소유·claim 거부 세션)의 Stop은 foreign_owner 진단과 함께
    # 비차단으로 통과해야 한다(구조적 방증이 아니라 stop_evaluator.evaluate 반환값 직접
    # 단언 — decisions.DECISION_KINDS 7종 중 block_continue만 제외하면 된다).
    payload_b = _load(tmp, "hook-payloads/stop.json")
    payload_b["cwd"] = str(hub_tmp)
    payload_b["session_id"] = "sess-b"
    payload_b["stop_hook_active"] = False
    result_b = stop_evaluator.evaluate(payload_b, project_root=hub_tmp, now=_iso(now + timedelta(minutes=1)))
    assert result_b["decision_kind"] != "block_continue"
    assert "foreign_owner" in result_b["diagnostics"]
    candidate_b = next(c for c in result_b["candidates"] if c.get("task_id") == "210-two-session-x")
    assert candidate_b.get("forced") is False
    assert candidate_b.get("classification") == "foreign_session_owned"


# ─────────────────────────────────────────────────────────────────────────────
# T5 — HUB-MULTI(200·201): 같은 세션이 두 허브 태스크를 실제 lease.claim()으로 확보하면
# stop_evaluator가 defer_to_pm으로 판정한다(단위 S-5는 owner.json을 양쪽 다 직접 써서
# 같은 결과를 만들지만, 여기서는 claim() 호출 자체가 만든 파일을 읽는다).
# ─────────────────────────────────────────────────────────────────────────────

def test_hub_multi_defer_to_pm_with_real_state_transition_claims(monkeypatch):
    from ownership_tool import lease, stop_evaluator

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    shutil.copytree(FIXTURES_ROOT / "hub" / "HUB-MULTI" / "tasks", hub_tmp / "tasks", dirs_exist_ok=True)

    now = _now_kst()
    for name in ("200-multi-task-x", "201-multi-task-y"):
        task_dir = hub_tmp / "tasks" / name
        claimed = lease.claim(task_dir, session_id="sess-multi", claim_source="state_transition", now=_iso(now))
        assert claimed["ok"] is True

    payload = _load(tmp, "hook-payloads/stop.json")
    payload["cwd"] = str(hub_tmp)
    payload["session_id"] = "sess-multi"
    payload["stop_hook_active"] = False

    result = stop_evaluator.evaluate(payload, project_root=hub_tmp, now=_iso(now + timedelta(minutes=1)))
    assert result["decision_kind"] == "defer_to_pm"
    assert "multiple_hub_tasks" in result["diagnostics"]
    forced = [c for c in result["candidates"] if c.get("forced")]
    assert len(forced) == 2


# ─────────────────────────────────────────────────────────────────────────────
# T6 — HUB-0: 활성 허브 태스크 0건. stop_evaluator와 pretooluse_guard_hook 양쪽이 같은
# 빈 상태에서 일관되게 "소유 태스크 없음"으로 판정하는지를 본다(두 모듈이 각자 다른 canonical
# 해석 경로 — resolver.resolve_hub vs session_start_hook._canonical_task_path — 를 쓰므로
# 결과 일치가 자명하지 않다).
# ─────────────────────────────────────────────────────────────────────────────

def test_hub_0_stop_allows_inactive_and_guard_noop_on_empty_hub(monkeypatch):
    from ownership_tool import pretooluse_guard_hook, stop_evaluator

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    shutil.copytree(FIXTURES_ROOT / "hub" / "HUB-0" / "tasks", hub_tmp / "tasks", dirs_exist_ok=True)

    payload = _load(tmp, "hook-payloads/stop.json")
    payload["cwd"] = str(hub_tmp)
    payload["session_id"] = "sess-empty"
    payload["stop_hook_active"] = False
    result = stop_evaluator.evaluate(payload, project_root=hub_tmp, now=_iso(_now_kst()))
    assert result["decision_kind"] == "allow_inactive"
    assert result["candidates"] == []

    guard_payload = _load(tmp, "hook-payloads/pretooluse.json")
    guard_payload["cwd"] = str(hub_tmp)
    guard_payload["tool_name"] = "Edit"
    guard_result = pretooluse_guard_hook.handle(guard_payload, project_root=hub_tmp, session_id="sess-empty")
    assert guard_result.get("decision") != "block"
    assert guard_result.get("task_path") is None


# ─────────────────────────────────────────────────────────────────────────────
# T7 — HUB-FOSSIL-AMBIGUOUS: registry가 132를 워크트리 canonical로 발급했는데 허브에도
# 동명 폴더 사본이 화석으로 남아 있다. stop_evaluator는 shadow로 판정해 강제하지 않는다
# (단위 S-1과 동일 전제) — 여기서는 그 사실이 guard의 독립적인 canonical 해석
# (session_start_hook._canonical_task_path, registry exact-match 기반)과 어긋나지 않는지,
# 즉 두 해석기가 서로 다른 코드를 쓰면서도 "허브 cwd는 이 화석 태스크를 소유하지 않는다"는
# 결론에서 일치하는지를 확인한다.
# ─────────────────────────────────────────────────────────────────────────────

def test_hub_fossil_ambiguous_shadow_not_forced_and_guard_resolves_no_canonical_task(monkeypatch):
    from ownership_tool import pretooluse_guard_hook, stop_evaluator

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    shutil.copytree(
        FIXTURES_ROOT / "hub" / "HUB-FOSSIL-AMBIGUOUS" / "tasks", hub_tmp / "tasks", dirs_exist_ok=True
    )
    meta_dir = wt_tmp / ".meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        tmp / "registry" / "active" / "WT-132" / ".meta" / "task_132.json", meta_dir / "task_132.json"
    )

    payload = _load(tmp, "hook-payloads/stop.json")
    payload["cwd"] = str(hub_tmp)
    payload["stop_hook_active"] = False
    result = stop_evaluator.evaluate(payload, project_root=hub_tmp, now=_iso(_now_kst()))
    assert result["decision_kind"] != "block_continue"
    assert "worktree_owned_shadow" in result["diagnostics"]
    forced = [c for c in result["candidates"] if c.get("forced")]
    assert not any("132" in (c.get("task_id") or "") for c in forced)

    guard_payload = _load(tmp, "hook-payloads/pretooluse.json")
    guard_payload["cwd"] = str(hub_tmp)
    guard_payload["tool_name"] = "Edit"
    guard_result = pretooluse_guard_hook.handle(guard_payload, project_root=hub_tmp, session_id="sess-fossil")
    assert guard_result.get("decision") != "block"
    assert guard_result.get("task_path") is None
