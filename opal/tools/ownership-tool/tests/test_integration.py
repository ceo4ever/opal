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
#   태스크 150 W-8 추가분(T8~T13) — 허브→워크트리 lease 이관(D-3) end-to-end: lease.handoff →
#   워크트리 SessionStart claim → PreToolUse 가드 비차단 → state-tool 전이(실제 CLI 서브프로세스)
#   한 줄기(S-2), 같은 워크트리 루트의 세션 교체 경계 2케이스(SessionEnd 선행 성공 / 미선행 거부
#   후 해제 재시도 성공, S-18), 이관 만료가 종전 무소유로 접혀 허브가 되찾는 경로(S-10·H-5),
#   해제→무소유→타 세션 SessionStart claim(S-6), 이관 필드 없는 기존 형식 lease와 worktree 키
#   없는 허브 태스크의 비 `--wt` 회귀(S-11·AC-10)를 덮는다.
#   태스크 150 S-16 추가분(T14, C-1) — 이관 경로 fail-safe 유지 회귀: 이관 대기(handoff_pending)
#   lease에 예외 유발 조건 3종(손상 JSON / chmod 000 권한 없음 / 경로가 디렉터리)을 걸고 훅
#   진입점 5종(session_start·session_end·heartbeat·pretooluse_guard·stop)의 `__main__`을 각각
#   subprocess로 띄워 15조합 전건이 exit 0 · 차단 출력 없음 · 트레이스백 미전파인지 확인한다.
# exports: (none — pytest module)
# depends: ownership_tool.session_start_hook, ownership_tool.heartbeat_hook, ownership_tool.session_end_hook,
#   ownership_tool.pretooluse_guard_hook, ownership_tool.stop_evaluator, ownership_tool.stop_hook,
#   ownership_tool.lease, ownership_tool.ownership_core, ownership_tool.fingerprint,
#   ownership_tool.claude_adapter, state-tool state_tool.py (CLI subprocess),
#   fixtures/hub, fixtures/registry, fixtures/hook-payloads, fixtures/fingerprint
"""통합 회귀 — 이미 GREEN인 모듈들의 실행 API를 실제 순서대로 연쇄 호출해 단일 모듈 단위
테스트로는 드러나지 않는 경계간 상호작용(레지스트리 파일 → lease → 판정 → 해제)을 검증한다.

[MUST] 시간 고정값 금지 — lease TTL·만료는 항상 실행 시점 기준 상대 계산(`_now_kst()`)을 쓴다.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
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


# ═════════════════════════════════════════════════════════════════════════════
# 태스크 150 W-8 — 허브→워크트리 lease 이관(D-3) 통합 경로.
#
# 단위 테스트(test_lease.py·test_session_start.py·test_pretooluse_guard.py·
# test_state_tool_ownership.py)는 각 모듈의 이관 계약을 owner.json 직접 주입이나 단일
# 함수 호출로 독립 검증한다. 여기서는 그 조각들을 **손으로 조립하지 않고** 실제 함수를
# 이관 순서대로 태워, 한 모듈이 디스크에 남긴 상태를 다음 모듈이 그대로 읽는 경계간
# 데이터 흐름만 검증한다(PRINCIPLES §2 — 단일 모듈 계약을 재검증하지 않는다).
# ═════════════════════════════════════════════════════════════════════════════

# state-tool CLI 실물. 이관 소비의 마지막 고리(상태 전이 claim)는 ownership-tool 안에서
# 재현할 수 없으므로 실제 CLI를 서브프로세스로 태운다(test_state_tool_ownership.py와
# 같은 관례 — 경로만 반대 방향으로 참조한다).
_STATE_TOOL_PATH = Path(__file__).resolve().parent.parent.parent / "state-tool" / "state_tool.py"

# state-tool init이 요구하는 최소 rows-spec. 이관 경로 검증에 필요한 전이 1개만 있으면 된다.
_SIMPLE_ROWS_SPEC = json.dumps(
    [
        {"stage": "TASK", "item": "작업"},
        {"stage": "EXECUTE", "item": "작업"},
        {"stage": "CLOSE", "item": "State Gate"},
    ],
    ensure_ascii=False,
)


def _session_id_env_names():
    """세션 ID를 싣는 환경변수 이름 2종을 얻는다.

    플랫폼 고유 이름은 claude_adapter가 소유하므로(C-15) 이 테스트에 하드코딩하지 않고
    상수를 읽는다. OPAL 중립 이름은 session_start_hook이 소유한다."""
    from ownership_tool import claude_adapter, session_start_hook

    return (session_start_hook.SESSION_ID_ENV_LINE_KEY, claude_adapter.SESSION_ID_ENV)


def _run_state_tool(cwd, args, session_id=None):
    """state-tool CLI를 지정 cwd에서 실행한다 — claimant_root가 그 cwd에서 오기 때문이다.

    앰비언트 세션 변수는 항상 제거한 뒤 필요할 때만 주입한다(merge 방식으로는 부재 키를
    지울 수 없다 — test_state_tool_ownership.py `_run_at`의 선례와 같은 이유)."""
    env = dict(os.environ)
    neutral_key, platform_key = _session_id_env_names()
    env.pop(neutral_key, None)
    env.pop(platform_key, None)
    if session_id is not None:
        env[neutral_key] = session_id
    return subprocess.run(
        [sys.executable, str(_STATE_TOOL_PATH), *args],
        capture_output=True, text=True, env=env, cwd=str(cwd),
    )


def _seed_manual_worktree(tmp, hub_tmp, wt_tmp, task_num, task_folder):
    """registry 발급값을 직접 구성한 워크트리 1개를 조립한다(T3의 task_220 선례와 동일 방식).

    canonical task_path는 워크트리 안(`<worktree_root>/tasks/<task_folder>`)이다 — 실제
    `--wt` 태스크의 배치와 같다. 반환: (worktree_root, task_dir, registry_entry)."""
    from ownership_tool import ownership_core

    worktree_root = wt_tmp / "task_{}".format(task_num)
    worktree_root.mkdir(parents=True, exist_ok=True)
    task_dir = worktree_root / "tasks" / task_folder
    task_dir.mkdir(parents=True, exist_ok=True)
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
    (meta_dir / "task_{}.json".format(task_num)).write_text(
        json.dumps(registry_entry, ensure_ascii=False), encoding="utf-8"
    )
    _write_task_ownership_copy(ownership_core, worktree_root, registry_entry)
    return worktree_root, task_dir, registry_entry


def _session_start(tmp, worktree_root, session_id, now):
    """SessionStart 봉투를 실제 handle()에 태운다(봉투는 fixture 원본을 쓴다)."""
    from ownership_tool import session_start_hook

    payload = _load(tmp, "hook-payloads/session-start.json")
    payload["cwd"] = str(worktree_root)
    payload["session_id"] = session_id
    return session_start_hook.handle(
        payload, project_root=worktree_root, env_file_path=None, now=_iso(now)
    )


def _session_end(tmp, worktree_root, session_id, now):
    from ownership_tool import session_end_hook

    payload = _load(tmp, "hook-payloads/sessionend.json")
    payload["cwd"] = str(worktree_root)
    payload["session_id"] = session_id
    return session_end_hook.handle(payload, project_root=worktree_root, now=_iso(now))


def _guard_edit(tmp, cwd, session_id, now=None):
    """PreToolUse 가드를 Edit 봉투로 직접 호출한다 — 가드 판정은 구조적 방증이 아니라
    handle()의 반환값으로만 읽는다(coding-principles §4)."""
    from ownership_tool import pretooluse_guard_hook

    payload = _load(tmp, "hook-payloads/pretooluse.json")
    payload["cwd"] = str(cwd)
    payload["tool_name"] = "Edit"
    return pretooluse_guard_hook.handle(
        payload, project_root=cwd, session_id=session_id, now=None if now is None else _iso(now)
    )


def _read_lease(task_dir):
    from ownership_tool import ownership_core

    return json.loads(ownership_core.hub_lease_path(task_dir).read_text(encoding="utf-8"))


# ─────────────────────────────────────────────────────────────────────────────
# T8 — S-2(AC-2): 이관 → 워크트리 SessionStart claim → PreToolUse 가드 통과 →
# state-tool 전이. 네 모듈이 각각 소유한 판정이 한 owner.json을 거쳐 이어지는지를
# 실제 함수 호출 순서로 확인한다(어느 단계도 레코드를 손으로 쓰지 않는다).
# ─────────────────────────────────────────────────────────────────────────────

def test_s2_handoff_then_worktree_claim_guard_pass_and_state_tool_transition(monkeypatch):
    from ownership_tool import lease

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root, task_dir, _entry = _seed_manual_worktree(
        tmp, hub_tmp, wt_tmp, "150", "150-handoff-e2e")

    hub_session = "sess-150-hub"
    wt_session = "sess-150-wt"
    now = _now_kst()

    # setup — state-tool이 전이할 실제 태스크를 CLI로 만든다(state.json을 손으로 쓰지 않는다).
    init_result = _run_state_tool(
        worktree_root,
        ["init", str(task_dir), "--skill", "opds", "--mode", "agentic",
         "--task-title", "150 W-8 handoff e2e", "--rows-spec", _SIMPLE_ROWS_SPEC],
    )
    assert init_result.returncode == 0, init_result.stderr

    # ① 허브 세션이 canonical task lease를 실제로 확보한다.
    claimed = lease.claim(
        str(task_dir), session_id=hub_session, claim_source="state_transition", now=_iso(now))
    assert claimed["ok"] is True

    # ② 허브가 워크트리 루트 앞으로 이관한다(launcher가 adapter.launch 직전에 하는 호출).
    handed = lease.handoff(
        str(task_dir), session_id=hub_session,
        to_worktree_root=str(worktree_root), now=_iso(now + timedelta(seconds=1)))
    assert handed["ok"] is True
    pending = _read_lease(task_dir)
    assert pending["status"] == lease.HANDOFF_STATUS
    assert pending["owner_session_id"] is None
    # 이관 대기 동안 어느 세션도 소유자가 아니다 — 가드가 비차단이어야 터미널이 뜬다.
    assert lease.classify(str(task_dir), wt_session, now=_iso(now + timedelta(seconds=2))) == "unowned"

    # ③ 워크트리 세션의 SessionStart가 이관을 소비해 claim에 성공한다(claimant_root=cwd).
    started = _session_start(tmp, worktree_root, wt_session, now + timedelta(seconds=3))
    assert started["lease_claimed"] is True, started["diagnostics"]
    assert started["classification"] == "current_session_owned"
    assert started["task_path"] == str(task_dir)
    after_claim = _read_lease(task_dir)
    assert after_claim["owner_session_id"] == wt_session
    assert after_claim["status"] == "active"
    # 소비된 이관 필드는 레코드에 잔존하지 않는다.
    for field in ("handoff_to_worktree_root", "handoff_from_session_id", "handoff_expires_at"):
        assert field not in after_claim

    # ④ 같은 워크트리에서 그 세션의 쓰기는 가드를 통과한다(소유자 자신이므로 차단 없음).
    guard_owner = _guard_edit(tmp, worktree_root, wt_session)
    assert guard_owner["decision"] != "block", guard_owner
    assert guard_owner["classification"] == "current_session_owned"
    assert guard_owner["task_path"] == str(task_dir)

    # ④' 반대로 이관을 내보낸 허브 세션의 쓰기는 같은 lease를 foreign으로 보고 차단된다 —
    # ③의 claim이 실제로 소유권을 옮겼다는 것을 가드 자신의 판정으로 확인한다.
    guard_foreign = _guard_edit(tmp, worktree_root, hub_session)
    assert guard_foreign["decision"] == "block"
    assert guard_foreign["classification"] == "foreign_session_owned"

    # ⑤ 워크트리 cwd의 state-tool 전이가 같은 lease를 state_transition으로 승격한다.
    advance = _run_state_tool(
        worktree_root, ["advance", str(task_dir), "--row", "1"], session_id=wt_session)
    assert advance.returncode == 0, advance.stderr
    final = _read_lease(task_dir)
    assert final["owner_session_id"] == wt_session
    assert final["status"] == "active"
    assert final["claim_source"] == "state_transition"
    # 같은 세션 재-claim이므로 세대는 늘지 않는다(소유권 이동이 아니다).
    assert final["generation"] == after_claim["generation"]
    state = json.loads((task_dir / "state.json").read_text(encoding="utf-8"))
    assert state["rows"][0]["status"] == "in_progress"


# ─────────────────────────────────────────────────────────────────────────────
# T9 — S-18(C-2·C-3·AC-6) 세션 교체 (a): 같은 워크트리 루트에서 세션 A가 SessionEnd로
# 먼저 물러난 뒤 세션 B의 SessionStart가 claim에 성공한다.
# ─────────────────────────────────────────────────────────────────────────────

def test_s18_session_swap_after_session_end_lets_next_session_claim(monkeypatch):
    from ownership_tool import lease

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root, task_dir, _entry = _seed_manual_worktree(
        tmp, hub_tmp, wt_tmp, "151", "151-session-swap-clean")
    now = _now_kst()

    a = _session_start(tmp, worktree_root, "sess-151-a", now)
    assert a["lease_claimed"] is True
    generation_a = _read_lease(task_dir)["generation"]

    ended = _session_end(tmp, worktree_root, "sess-151-a", now + timedelta(minutes=1))
    assert ended["released"] is True
    assert str(task_dir) in ended["released_tasks"]
    assert lease.classify(str(task_dir), "sess-151-b", now=_iso(now + timedelta(minutes=2))) == "unowned"

    b = _session_start(tmp, worktree_root, "sess-151-b", now + timedelta(minutes=2))
    assert b["lease_claimed"] is True, b["diagnostics"]
    record = _read_lease(task_dir)
    assert record["owner_session_id"] == "sess-151-b"
    # 소유권이 실제로 이동했으므로 세대가 단조 증가한다.
    assert record["generation"] == generation_a + 1


# ─────────────────────────────────────────────────────────────────────────────
# T10 — S-18(C-2·C-3·AC-6) 세션 교체 (b): SessionEnd 없이 세션 B가 SessionStart를
# 발화하면 거부되고 진단이 남는다. 이후 A의 해제가 그 거부를 실제로 풀어준다.
# ─────────────────────────────────────────────────────────────────────────────

def test_s18_session_swap_without_session_end_is_rejected_then_release_unblocks(monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root, task_dir, _entry = _seed_manual_worktree(
        tmp, hub_tmp, wt_tmp, "152", "152-session-swap-dirty")
    now = _now_kst()

    a = _session_start(tmp, worktree_root, "sess-152-a", now)
    assert a["lease_claimed"] is True
    before = _read_lease(task_dir)

    # ① SessionEnd 없이 온 B는 claim에 실패하고 registry owner로도 등록되지 않는다(D-7).
    b_denied = _session_start(tmp, worktree_root, "sess-152-b", now + timedelta(minutes=1))
    assert b_denied["lease_claimed"] is False
    assert b_denied["classification"] == "foreign_owner"
    assert "foreign_owner" in b_denied["diagnostics"]
    assert "registry_owner_not_registered:foreign_owner" in b_denied["diagnostics"]
    assert b_denied["registry_owner_registered"] is False
    # 거부는 레코드를 건드리지 않는다(A의 소유가 그대로다).
    assert _read_lease(task_dir) == before

    # ② A가 해제하면 같은 B의 재시도가 성공한다 — 거부의 원인이 lease 하나임을 확인한다.
    ended = _session_end(tmp, worktree_root, "sess-152-a", now + timedelta(minutes=2))
    assert ended["released"] is True

    b_retry = _session_start(tmp, worktree_root, "sess-152-b", now + timedelta(minutes=3))
    assert b_retry["lease_claimed"] is True, b_retry["diagnostics"]
    assert _read_lease(task_dir)["owner_session_id"] == "sess-152-b"


# ─────────────────────────────────────────────────────────────────────────────
# T11 — S-10(H-5): 이관 만료. 워크트리 세션이 끝내 뜨지 않아 이관 TTL이 지나면 레코드는
# 종전 무소유와 동일 경로로 접히고 허브가 되찾는다(가드는 그 사이 비차단이다).
# ─────────────────────────────────────────────────────────────────────────────

def test_s10_expired_handoff_folds_to_unowned_and_hub_reclaims(monkeypatch):
    from ownership_tool import lease

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root, task_dir, _entry = _seed_manual_worktree(
        tmp, hub_tmp, wt_tmp, "153", "153-handoff-expiry")

    hub_session = "sess-153-hub"
    now = _now_kst()
    assert lease.claim(
        str(task_dir), session_id=hub_session,
        claim_source="state_transition", now=_iso(now))["ok"] is True
    assert lease.handoff(
        str(task_dir), session_id=hub_session,
        to_worktree_root=str(worktree_root), now=_iso(now))["ok"] is True

    expired_at = now + timedelta(seconds=lease.DEFAULT_HANDOFF_TTL_SEC + 1)

    # 만료 시점에도 판정은 무소유다 — 가드가 차단하지 않는다(이관 분기를 classify에 두지
    # 않았다는 계약이 통합 경로에서도 성립한다).
    assert lease.classify(str(task_dir), hub_session, now=_iso(expired_at)) == "unowned"
    guard = _guard_edit(tmp, worktree_root, "sess-153-passerby", now=expired_at)
    assert guard["decision"] != "block", guard
    assert guard["classification"] == "unowned"

    # 허브(=이관 대상 밖 루트)의 claim이 만료된 이관을 접고 성공한다.
    reclaimed = lease.claim(
        str(task_dir), session_id=hub_session, claim_source="state_transition",
        now=_iso(expired_at), claimant_root=str(hub_tmp))
    assert reclaimed["ok"] is True, reclaimed
    record = _read_lease(task_dir)
    assert record["owner_session_id"] == hub_session
    assert record["status"] == "active"
    for field in ("handoff_to_worktree_root", "handoff_from_session_id", "handoff_expires_at"):
        assert field not in record


# ─────────────────────────────────────────────────────────────────────────────
# T12 — S-6(AC-6): 해제 → 무소유 → 타 세션 claim. T9가 SessionEnd 경유 경로를 보는 것과
# 달리, 여기서는 lease.release 직접 호출이 만든 released 레코드를 SessionStart가 읽고
# 새 소유자로 전이하는지를 본다(released 레코드는 파일이 남아 있어도 무소유다).
# ─────────────────────────────────────────────────────────────────────────────

def test_s6_explicit_release_then_unowned_then_other_session_claims(monkeypatch):
    from ownership_tool import lease, ownership_core

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root, task_dir, _entry = _seed_manual_worktree(
        tmp, hub_tmp, wt_tmp, "154", "154-release-then-claim")
    now = _now_kst()

    owner = _session_start(tmp, worktree_root, "sess-154-owner", now)
    assert owner["lease_claimed"] is True

    released = lease.release(str(task_dir), session_id="sess-154-owner",
                             now=_iso(now + timedelta(minutes=1)))
    assert released["ok"] is True and not released.get("noop")
    assert ownership_core.hub_lease_path(task_dir).exists()
    assert _read_lease(task_dir)["status"] == "released"
    assert lease.classify(str(task_dir), "sess-154-next", now=_iso(now + timedelta(minutes=2))) == "unowned"

    nxt = _session_start(tmp, worktree_root, "sess-154-next", now + timedelta(minutes=2))
    assert nxt["lease_claimed"] is True, nxt["diagnostics"]
    assert _read_lease(task_dir)["owner_session_id"] == "sess-154-next"
    guard = _guard_edit(tmp, worktree_root, "sess-154-next")
    assert guard["decision"] != "block", guard


# ─────────────────────────────────────────────────────────────────────────────
# T13 — S-11(AC-10) 비 `--wt` 회귀: 이관 필드가 없는 기존 형식 lease와 worktree 키가
# 없는 허브 태스크의 동작·산출물이 이관 도입 전과 같아야 한다. 레코드 키 집합과 claim
# 판정, 허브 cwd의 가드·SessionStart 결과를 함께 고정한다.
# ─────────────────────────────────────────────────────────────────────────────

_LEGACY_LEASE_KEYS = {
    "task_path", "owner_session_id", "generation", "claimed_at",
    "heartbeat_at", "lease_expires_at", "status", "ttl_sec", "claim_source",
}


def test_s11_legacy_lease_and_non_worktree_task_behaviour_unchanged(monkeypatch):
    from ownership_tool import lease

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    # worktree 키가 없는 허브 직속 태스크 — registry 발급값이 이 태스크를 가리키지 않는다.
    (wt_tmp / ".meta").mkdir(parents=True, exist_ok=True)
    task_dir = hub_tmp / "tasks" / "155-plain-hub-task"
    task_dir.mkdir(parents=True, exist_ok=True)
    now = _now_kst()

    # ① claim 산출물에 이관 필드가 생기지 않는다(키 집합 고정).
    claimed = lease.claim(str(task_dir), session_id="sess-155-a",
                          claim_source="state_transition", now=_iso(now))
    assert claimed["ok"] is True
    record = _read_lease(task_dir)
    assert set(record) == _LEGACY_LEASE_KEYS

    # ② claimant_root 없이 온 타 세션 claim은 종전과 같이 foreign_owner로만 거부된다
    # (handoff_pending이 아니다 — 이관 분기를 타지 않았다는 실측).
    denied = lease.claim(str(task_dir), session_id="sess-155-b",
                         claim_source="state_transition", now=_iso(now + timedelta(minutes=1)))
    assert denied["ok"] is False
    assert denied["diagnostic"] == "foreign_owner"
    assert _read_lease(task_dir) == record

    # ③ 같은 세션 재-claim은 종전대로 멱등(세대 불변)이고 키 집합도 그대로다.
    again = lease.claim(str(task_dir), session_id="sess-155-a",
                        claim_source="state_transition", now=_iso(now + timedelta(minutes=2)))
    assert again["ok"] is True
    assert again["generation"] == record["generation"]
    assert set(_read_lease(task_dir)) == _LEGACY_LEASE_KEYS

    # ④ 허브 루트 cwd는 세션 시작만으로 태스크를 얻지 못하고, 가드도 차단하지 않는다.
    from ownership_tool import session_start_hook

    payload = _load(tmp, "hook-payloads/session-start.json")
    payload["cwd"] = str(hub_tmp)
    payload["session_id"] = "sess-155-b"
    started = session_start_hook.handle(
        payload, project_root=hub_tmp, env_file_path=None, now=_iso(now + timedelta(minutes=3)))
    assert started["lease_claimed"] is False
    assert started["task_path"] is None
    assert "no_owned_task" in started["diagnostics"]

    guard = _guard_edit(tmp, hub_tmp, "sess-155-b")
    assert guard["decision"] != "block", guard
    assert guard["task_path"] is None


# ─────────────────────────────────────────────────────────────────────────────
# T14 — S-16(C-1): 이관 경로에서 예외를 유발하는 조건 3종(손상 JSON / 권한 없음 /
# 경로가 디렉터리) × 훅 진입점 5종 = 15조합이 모두 fail-safe를 유지하는지 고정한다.
# C-1은 "fail-safe를 **유지**한다"는 불변 제약이다 — 이번 이관(D-3) 경로 추가로 새 예외
# 경로가 생기지 않았음을 보증하는 회귀 가드이며, 깨지면 훅이 세션을 막는다.
# 판정은 구조적 방증이 아니라 실제 진입점 프로세스의 exit code·stdout·stderr로만 한다
# (coding-principles §4, red-first §2) — 그래서 handle()이 아니라 `__main__` 경로를
# subprocess로 띄운다.
# ─────────────────────────────────────────────────────────────────────────────

_OWNERSHIP_TOOL_DIR = Path(__file__).resolve().parent.parent

# (훅 모듈, 그 훅이 stdin으로 받는 봉투 fixture) — 5개 진입점 전건.
_HOOK_ENTRYPOINTS = (
    ("session_start_hook", "hook-payloads/session-start.json"),
    ("session_end_hook", "hook-payloads/sessionend.json"),
    ("heartbeat_hook", "hook-payloads/posttooluse.json"),
    ("pretooluse_guard_hook", "hook-payloads/pretooluse.json"),
    ("stop_hook", "hook-payloads/stop.json"),
)


def _run_hook_entrypoint(module_name, payload, cwd, session_id):
    """훅 `.py`를 실제 진입점(`__main__`)으로 띄운다 — 봉투는 stdin, 출력은 stdout 1줄.

    PYTHONPATH는 run.sh가 훅에 주는 것과 같은 tool-dir이다."""
    hook_path = _OWNERSHIP_TOOL_DIR / "ownership_tool" / "{}.py".format(module_name)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_OWNERSHIP_TOOL_DIR)
    neutral_key, platform_key = _session_id_env_names()
    env.pop(platform_key, None)
    env[neutral_key] = session_id
    return subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True, text=True, cwd=str(cwd), env=env,
    )


def _assert_hook_is_fail_safe(module_name, completed):
    """exit 0 · 차단 출력 없음 · 트레이스백 미전파를 한 훅 실행에 대해 확인한다."""
    label = "{} exit={} stdout={!r} stderr={!r}".format(
        module_name, completed.returncode, completed.stdout, completed.stderr)
    assert completed.returncode == 0, label
    assert "Traceback" not in completed.stderr, label

    out = completed.stdout.strip()
    if not out:
        return
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        decoded = json.loads(line)  # 훅 출력 규약은 1줄 JSON이다 — 깨지면 그것도 결함이다.
        # Stop 훅의 차단 형식.
        assert decoded.get("decision") != "block", label
        # PreToolUse 가드의 차단 형식.
        specific = decoded.get("hookSpecificOutput") or {}
        assert specific.get("permissionDecision") != "deny", label


def _seed_handoff_pending_task(tmp, hub_tmp, wt_tmp, task_num, task_folder, hub_session):
    """이관 대기(handoff_pending) lease를 실제 공개 API 연쇄로 만든 워크트리를 돌려준다.
    (worktree_root, task_dir, lease_path)."""
    from ownership_tool import lease, ownership_core

    worktree_root, task_dir, _entry = _seed_manual_worktree(
        tmp, hub_tmp, wt_tmp, task_num, task_folder)
    now = _now_kst()
    claimed = lease.claim(str(task_dir), session_id=hub_session,
                          claim_source="state_transition", now=_iso(now))
    assert claimed["ok"] is True
    handed = lease.handoff(str(task_dir), session_id=hub_session,
                           to_worktree_root=str(worktree_root),
                           now=_iso(now + timedelta(seconds=1)))
    assert handed["ok"] is True
    return worktree_root, task_dir, ownership_core.hub_lease_path(task_dir)


def _run_all_hooks_against(tmp, worktree_root, session_id):
    """훅 5종 전건을 같은 워크트리 cwd에서 실행하고 각각 fail-safe를 확인한다."""
    ran = []
    for module_name, fixture_rel in _HOOK_ENTRYPOINTS:
        payload = _load(tmp, fixture_rel)
        payload.pop("_fixture", None)
        payload["cwd"] = str(worktree_root)
        payload["session_id"] = session_id
        completed = _run_hook_entrypoint(module_name, payload, worktree_root, session_id)
        _assert_hook_is_fail_safe(module_name, completed)
        ran.append(module_name)
    return ran


def test_s16_all_hooks_fail_safe_on_corrupt_handoff_lease_json(monkeypatch):
    """(a) 손상 JSON 레코드 — 이관 대기 lease 파일이 파싱 불가일 때 훅 5종 전건이 비차단 통과."""
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    _worktree_root, _task_dir, lease_path = _seed_handoff_pending_task(
        tmp, hub_tmp, wt_tmp, "161", "161-failsafe-corrupt-json", "sess-161-hub")
    worktree_root = _worktree_root

    # 이관 대기 레코드를 잘린 JSON으로 손상시킨다(부분 기록·디스크 오류 재현).
    lease_path.write_text('{"status": "handoff_pending", "owner_sess', encoding="utf-8")

    ran = _run_all_hooks_against(tmp, worktree_root, "sess-161-wt")
    assert len(ran) == len(_HOOK_ENTRYPOINTS)


def test_s16_all_hooks_fail_safe_on_unreadable_handoff_lease(monkeypatch):
    """(b) 권한 없음 — 이관 대기 lease 파일을 읽을 수 없을 때 훅 5종 전건이 비차단 통과."""
    import pytest

    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("root는 chmod 000을 무시하고 읽으므로 '권한 없음' 조건이 성립하지 않는다")

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root, _task_dir, lease_path = _seed_handoff_pending_task(
        tmp, hub_tmp, wt_tmp, "162", "162-failsafe-no-permission", "sess-162-hub")

    lease_path.chmod(0o000)
    # 조건이 실제로 성립했는지 먼저 확인한다(성립하지 않으면 이 케이스는 아무것도 증명하지 않는다).
    try:
        lease_path.read_text(encoding="utf-8")
    except PermissionError:
        pass
    else:
        lease_path.chmod(0o600)
        pytest.skip("이 파일시스템에서 chmod 000이 읽기를 막지 못한다")

    try:
        ran = _run_all_hooks_against(tmp, worktree_root, "sess-162-wt")
    finally:
        # 임시 디렉터리가 정리될 수 있도록 권한을 되돌린다.
        lease_path.chmod(0o600)
    assert len(ran) == len(_HOOK_ENTRYPOINTS)


def test_s16_all_hooks_fail_safe_when_lease_path_is_a_directory(monkeypatch):
    """(c) 경로가 디렉터리 — lease 파일 자리에 디렉터리가 있을 때 훅 5종 전건이 비차단 통과.

    읽기는 IsADirectoryError, 원자 교체(os.replace)는 OSError를 던지는 조건이다."""
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root, _task_dir, lease_path = _seed_handoff_pending_task(
        tmp, hub_tmp, wt_tmp, "163", "163-failsafe-path-is-dir", "sess-163-hub")

    lease_path.unlink()
    lease_path.mkdir()
    assert lease_path.is_dir()

    ran = _run_all_hooks_against(tmp, worktree_root, "sess-163-wt")
    assert len(ran) == len(_HOOK_ENTRYPOINTS)
