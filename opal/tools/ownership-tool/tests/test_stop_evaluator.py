# @header
# module: ownership_tool.tests.test_stop_evaluator
# layer: test
# domain: ownership
# description: RED-first — ownership_tool.stop_evaluator.evaluate() 공개 계약 검증 (S-1, S-2, S-5, S-6) +
#   PLAN D-21 claim_source 기반 강제후보 판정(session_start→passive_ownership 비강제,
#   state_transition→기존 block_continue 보전 + evidence.claim_source 노출) RED
# exports: (none — pytest module)
# depends: ownership_tool.stop_evaluator (미구현), fixtures/hub, fixtures/registry, fixtures/hook-payloads, fixtures/runtime
"""RED 테스트 — 구현 전. ownership_tool.stop_evaluator가 아직 존재하지 않으므로
ImportError로 실패해야 한다. 실패 관찰 후 GREEN 구현자가 이 계약대로 구현한다."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

FIXTURES_ROOT = Path(__file__).parent / "fixtures"


def _clone_fixtures() -> tuple[Path, Path, Path]:
    """fixtures 전체를 임시 디렉터리로 복제하고 {HUB}/{WT} 플레이스홀더를 치환한다."""
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


def _load(tmp: Path, rel: str) -> dict:
    return json.loads((tmp / rel).read_text(encoding="utf-8"))


def test_s1_hub_fossil_ambiguous_not_forced_block_continue(monkeypatch):
    """S-1: HUB-FOSSIL-AMBIGUOUS, cwd=허브, 현재 세션 lease 없음, stop_hook_active=false.
    decision_kind != block_continue. diagnostics에 worktree_owned_shadow + task_path_ambiguous.
    반환 후보 목록에 132가 강제 후보로 없음. reason 미출력."""
    from ownership_tool import stop_evaluator  # RED: 모듈 미구현

    # setup(B-5): 앰비언트 CLAUDE_CODE_SESSION_ID/OPAL_SESSION_ID가 payload의
    # sess-live-0001을 덮어쓰지 않게 격리한다 — env -u 유무와 무관하게 동일 결과가 나와야 한다.
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    # setup: _clone_fixtures()는 hub_tmp를 빈 디렉터리로만 만든다. HUB-FOSSIL-AMBIGUOUS
    # 시나리오 트리를 hub_tmp/tasks 아래로 이 테스트 안에서 명시적으로 복제한다
    # (test_resolver.py S-4 선례와 동일한 방식).
    shutil.copytree(FIXTURES_ROOT / "hub" / "HUB-FOSSIL-AMBIGUOUS" / "tasks", hub_tmp / "tasks", dirs_exist_ok=True)

    # setup(B-1): registry meta를 발급 계약 위치(<hub_root>/.opal-worktrees/.meta/)에 배치해
    # evaluate()의 _load_registry가 실제로 읽도록 한다. task_path는 {WT} 치환을 거쳐
    # <hub_tmp>/.opal-worktrees/task_132/tasks/... — 허브 안쪽 nested 경로다.
    meta_dir = wt_tmp / ".meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(tmp / "registry" / "active" / "WT-132" / ".meta" / "task_132.json", meta_dir / "task_132.json")

    payload = _load(tmp, "hook-payloads/stop.json")
    payload["cwd"] = str(hub_tmp)
    payload["stop_hook_active"] = False

    result = stop_evaluator.evaluate(
        payload,
        project_root=hub_tmp,
        now="2026-09-17T15:20:00+09:00",
    )

    assert result["decision_kind"] != "block_continue"
    assert "worktree_owned_shadow" in result["diagnostics"]
    assert "task_path_ambiguous" in result["evidence"]
    forced = [c for c in result["candidates"] if c.get("forced")]
    assert not any("132" in c.get("task_id", "") for c in forced)
    assert "reason" not in result or result.get("reason") is None


def test_s2_closed_attribution_state_hub_canonical_block_continue(monkeypatch):
    """S-2: attribution_state=closed + 허브 merge 사본, transition_action=continue,
    현재 세션이 그 태스크를 lease. hub_canonical 분류 + block_continue. shadow 진단 없음."""
    from ownership_tool import stop_evaluator, resolver  # RED

    # setup(B-5): 앰비언트 세션 env 격리(S-1과 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    # setup: HUB-CLOSED-MERGED 시나리오 트리를 hub_tmp/tasks 아래로 이 테스트 안에서
    # 명시적으로 복제한다(test_resolver.py S-4 선례와 동일한 방식).
    shutil.copytree(FIXTURES_ROOT / "hub" / "HUB-CLOSED-MERGED" / "tasks", hub_tmp / "tasks", dirs_exist_ok=True)
    registry = _load(tmp, "registry/closed/WT-132-CLOSED/.meta/task_132.json")

    # setup(B-1): registry를 발급 계약 위치에도 배치해 evaluate()의 _load_registry가
    # 위에서 직접 검증한 것과 같은 값을 읽도록 한다(실물은 closed 태스크도 registry에 남는다).
    meta_dir = wt_tmp / ".meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        tmp / "registry" / "closed" / "WT-132-CLOSED" / ".meta" / "task_132.json", meta_dir / "task_132.json"
    )

    # setup: 현재 세션(stop.json의 session_id와 통일된 sess-live-0001)이 이 태스크를
    # lease 중인 상태를 배치한다. 만료 시각을 호출 시점(now=15:20)보다 뒤로 조정해
    # W-3 lease.classify 계약상 current_session_owned가 되도록 한다.
    current_lease = json.loads(
        (FIXTURES_ROOT / "runtime" / "owner-current-session.json").read_text(encoding="utf-8")
    )
    task_dir = hub_tmp / "tasks" / "132-260914-opd-oppb-프로젝트빌드-파일럿-신설"
    current_lease["task_path"] = str(task_dir)
    current_lease["owner_session_id"] = "sess-live-0001"
    current_lease["status"] = "hub_owned"
    owner_path = task_dir / "run" / ".runtime" / "owner.json"
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(json.dumps(current_lease), encoding="utf-8")

    classified = resolver.resolve_hub(hub_tmp, registry, "sess-live-0001", now="2026-09-17T15:20:00+09:00")
    assert any(c["classification"] == "hub_canonical" for c in classified)

    payload = _load(tmp, "hook-payloads/stop.json")
    payload["cwd"] = str(hub_tmp)
    result = stop_evaluator.evaluate(payload, project_root=hub_tmp, now="2026-09-17T15:20:00+09:00")
    assert result["decision_kind"] == "block_continue"
    assert "worktree_owned_shadow" not in result["diagnostics"]


def test_s5_hub_multi_defer_to_pm(monkeypatch):
    """S-5: HUB-MULTI — 현재 세션 lease 2건 모두 continue, 추가 무소유 1건 + lease_expired 1건.
    decision_kind=defer_to_pm, diagnostics에 multiple_hub_tasks + lease_expired.
    reason에 후보 전건의 task_id/transition_action/next_action 나열. 최신 updated_at 단일 선택 아님."""
    from ownership_tool import stop_evaluator  # RED

    # setup(B-5): 앰비언트 세션 env 격리(S-1과 동일 사유) — 200/201 lease가 sess-live-0001로
    # 고정되므로 실제 세션 ID가 새어들면 current_session_owned 판정이 어긋난다.
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    # setup: HUB-MULTI 시나리오 트리(200·201)를 hub_tmp/tasks 아래로 이 테스트 안에서
    # 명시적으로 복제한다(test_resolver.py S-4 선례와 동일한 방식).
    shutil.copytree(FIXTURES_ROOT / "hub" / "HUB-MULTI" / "tasks", hub_tmp / "tasks", dirs_exist_ok=True)

    # setup: 200·201에 현재 세션(sess-live-0001) lease를 배치한다(now=15:20 기준 live).
    for name in ("200-multi-task-x", "201-multi-task-y"):
        task_dir = hub_tmp / "tasks" / name
        lease_record = {
            "task_path": str(task_dir),
            "owner_session_id": "sess-live-0001",
            "generation": 1,
            "claimed_at": "2026-09-17 09:00:00+09:00",
            "heartbeat_at": "2026-09-17 09:30:00+09:00",
            "lease_expires_at": "2026-09-17 19:20:00+09:00",
            "status": "hub_owned",
        }
        owner_path = task_dir / "run" / ".runtime" / "owner.json"
        owner_path.parent.mkdir(parents=True, exist_ok=True)
        owner_path.write_text(json.dumps(lease_record), encoding="utf-8")

    # setup: 추가 무소유 1건 — registry 미등록 + lease 없음. 200 state.json을 템플릿으로
    # task_id만 바꿔 최소 조립한다.
    unowned_state = json.loads(
        (FIXTURES_ROOT / "hub" / "HUB-MULTI" / "tasks" / "200-multi-task-x" / "state.json").read_text(
            encoding="utf-8"
        )
    )
    unowned_state["task_id"] = "202-multi-task-unowned"
    unowned_dir = hub_tmp / "tasks" / "202-multi-task-unowned"
    unowned_dir.mkdir(parents=True, exist_ok=True)
    (unowned_dir / "state.json").write_text(json.dumps(unowned_state), encoding="utf-8")

    # setup: 추가 lease_expired 1건 — runtime/owner-expired-lease.json 계열의 만료 lease를
    # 이 태스크로 옮겨 배치한다(owner_session_id가 타 세션이고 lease_expires_at이 now 이전).
    expired_state = json.loads(
        (FIXTURES_ROOT / "hub" / "HUB-MULTI" / "tasks" / "201-multi-task-y" / "state.json").read_text(
            encoding="utf-8"
        )
    )
    expired_state["task_id"] = "203-multi-task-expired"
    expired_dir = hub_tmp / "tasks" / "203-multi-task-expired"
    expired_dir.mkdir(parents=True, exist_ok=True)
    (expired_dir / "state.json").write_text(json.dumps(expired_state), encoding="utf-8")

    expired_lease = json.loads(
        (FIXTURES_ROOT / "runtime" / "owner-expired-lease.json").read_text(encoding="utf-8")
    )
    expired_lease["task_path"] = str(expired_dir)
    owner_path = expired_dir / "run" / ".runtime" / "owner.json"
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(json.dumps(expired_lease), encoding="utf-8")

    payload = _load(tmp, "hook-payloads/stop.json")
    payload["cwd"] = str(hub_tmp)
    payload["stop_hook_active"] = False

    result = stop_evaluator.evaluate(payload, project_root=hub_tmp, now="2026-09-17T15:20:00+09:00")

    assert result["decision_kind"] == "defer_to_pm"
    assert "multiple_hub_tasks" in result["diagnostics"]
    assert "lease_expired" in result["diagnostics"]
    reason = result.get("reason", "")
    assert "task_id" in reason or all(
        any(cid in reason for cid in ("200", "201")) for cid in ("200",)
    )
    assert len(result["candidates"]) >= 2


@pytest.mark.parametrize(
    "variant,expected_kind",
    [
        ("show-a-baseline.json", "allow_no_progress_same_fingerprint"),
        ("show-c-note-runlog-only.json", "allow_no_progress_same_fingerprint"),
        ("show-b-status-changed.json", "block_continue"),
    ],
)
def test_s6_repeat_stop_fingerprint_variants(variant, expected_kind, monkeypatch):
    """S-6: stop_hook_active=true, 직전 receipt 존재. (a)/(c) 동일 fingerprint → no-progress.
    (b) 의미 변경 → 재차단 + block_count+1."""
    from ownership_tool import stop_evaluator  # RED

    # setup(B-5): 앰비언트 세션 env 격리(S-1과 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    show_json = _load(tmp, f"fingerprint/{variant}")
    receipt = _load(tmp, "runtime/stop-guard/stop-guard-sample.json")

    payload = _load(tmp, "hook-payloads/stop.json")
    payload["stop_hook_active"] = True
    payload["cwd"] = str(wt_tmp / "task_138")

    result = stop_evaluator.evaluate(
        payload,
        project_root=wt_tmp / "task_138",
        now="2026-09-17T15:40:00+09:00",
        show_json=show_json,
        prior_receipt=receipt,
    )
    assert result["decision_kind"] == expected_kind
    if expected_kind == "block_continue":
        assert result.get("block_count") == receipt["block_count"] + 1


def test_s6_block_cap_reached(monkeypatch):
    """S-6: block_count가 CLAUDE_CODE_STOP_HOOK_BLOCK_CAP env 이상이면 allow_block_cap_reached.
    env 미설정 시 상한 검사 건너뜀."""
    from ownership_tool import stop_evaluator  # RED

    # setup(B-5): 앰비언트 세션 env 격리(S-1과 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    receipt = _load(tmp, "runtime/stop-guard/stop-guard-sample.json")
    receipt["block_count"] = 5
    show_json = _load(tmp, "fingerprint/show-b-status-changed.json")
    payload = _load(tmp, "hook-payloads/stop.json")
    payload["stop_hook_active"] = True
    payload["cwd"] = str(wt_tmp / "task_138")

    os.environ["CLAUDE_CODE_STOP_HOOK_BLOCK_CAP"] = "3"
    try:
        result = stop_evaluator.evaluate(
            payload,
            project_root=wt_tmp / "task_138",
            now="2026-09-17T15:40:00+09:00",
            show_json=show_json,
            prior_receipt=receipt,
        )
    finally:
        del os.environ["CLAUDE_CODE_STOP_HOOK_BLOCK_CAP"]
    assert result["decision_kind"] == "allow_block_cap_reached"


def test_stop_hook_adapter_stdout_contract():
    """stop_hook 어댑터: stdout이 {"decision":"block","reason":...} 또는 무출력."""
    from ownership_tool import stop_hook  # RED

    assert hasattr(stop_hook, "main")


# ─────────────────────────────────────────────────────────────────────────────
# PLAN D-21 — claim_source 기반 강제 후보 판정 RED
# 현재 resolver/stop_evaluator는 claim_source를 전혀 읽지 않으므로(evidence에
# claim_source가 없고, session_start 여부와 무관하게 current_session_owned는 항상
# 강제 후보다) 아래 2건은 구현 전 RED다.
# ─────────────────────────────────────────────────────────────────────────────

def test_d21_current_session_owned_session_start_not_forced_passive_ownership(monkeypatch):
    """PLAN D-21: SessionStart 자동 claim(claim_source=session_start)만 있는
    current_session_owned 후보는 강제 후보가 아니다 — decision_kind != block_continue이고
    diagnostics에 passive_ownership이 남는다. 소유권 자체(classification)는 유지된다."""
    from ownership_tool import stop_evaluator  # RED

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    state = json.loads(
        (FIXTURES_ROOT / "hub" / "HUB-MULTI" / "tasks" / "200-multi-task-x" / "state.json").read_text(
            encoding="utf-8"
        )
    )
    state["task_id"] = "204-passive-ownership"
    task_dir = hub_tmp / "tasks" / "204-passive-ownership"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    lease_record = {
        "task_path": str(task_dir),
        "owner_session_id": "sess-live-0001",
        "generation": 1,
        "claimed_at": "2026-09-17 09:00:00+09:00",
        "heartbeat_at": "2026-09-17 09:30:00+09:00",
        "lease_expires_at": "2026-09-17 19:20:00+09:00",
        "status": "active",
        "claim_source": "session_start",
    }
    owner_path = task_dir / "run" / ".runtime" / "owner.json"
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(json.dumps(lease_record), encoding="utf-8")

    payload = _load(tmp, "hook-payloads/stop.json")
    payload["cwd"] = str(hub_tmp)
    payload["stop_hook_active"] = False

    result = stop_evaluator.evaluate(payload, project_root=hub_tmp, now="2026-09-17T15:20:00+09:00")

    assert result["decision_kind"] != "block_continue"
    forced = [c for c in result["candidates"] if c.get("forced")]
    assert not any(c.get("task_id") == "204-passive-ownership" for c in forced)
    assert "passive_ownership" in result["diagnostics"]
    candidate = next(c for c in result["candidates"] if c.get("task_id") == "204-passive-ownership")
    assert candidate["classification"] == "current_session_owned"
    assert candidate.get("evidence", {}).get("claim_source") == "session_start"


def test_d21_current_session_owned_state_transition_forced_block_continue(monkeypatch):
    """PLAN D-21: state-tool 첫 상태 전이로 승격된(claim_source=state_transition) lease는
    기존 동작대로 강제 후보 1건 → block_continue를 보전한다. 아울러 후보 evidence에
    claim_source가 노출되어야 한다(observability — passive_ownership 판정 근거 대칭)."""
    from ownership_tool import stop_evaluator  # RED

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    state = json.loads(
        (FIXTURES_ROOT / "hub" / "HUB-MULTI" / "tasks" / "200-multi-task-x" / "state.json").read_text(
            encoding="utf-8"
        )
    )
    state["task_id"] = "205-state-transition-forced"
    task_dir = hub_tmp / "tasks" / "205-state-transition-forced"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    lease_record = {
        "task_path": str(task_dir),
        "owner_session_id": "sess-live-0001",
        "generation": 1,
        "claimed_at": "2026-09-17 09:00:00+09:00",
        "heartbeat_at": "2026-09-17 09:30:00+09:00",
        "lease_expires_at": "2026-09-17 19:20:00+09:00",
        "status": "active",
        "claim_source": "state_transition",
    }
    owner_path = task_dir / "run" / ".runtime" / "owner.json"
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(json.dumps(lease_record), encoding="utf-8")

    payload = _load(tmp, "hook-payloads/stop.json")
    payload["cwd"] = str(hub_tmp)
    payload["stop_hook_active"] = False

    result = stop_evaluator.evaluate(payload, project_root=hub_tmp, now="2026-09-17T15:20:00+09:00")

    assert result["decision_kind"] == "block_continue"
    forced = [c for c in result["candidates"] if c.get("forced")]
    assert any(c.get("task_id") == "205-state-transition-forced" for c in forced)
    candidate = next(c for c in result["candidates"] if c.get("task_id") == "205-state-transition-forced")
    assert candidate.get("evidence", {}).get("claim_source") == "state_transition"
