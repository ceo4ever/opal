"""
@header {
  "module": "ownership_tool.stop_evaluator",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "Stop hook 판정 조립기(W-6). cwd를 registry(<project_root>/.opal-worktrees/.meta/task_*.json)로 해석해 worktree/hub 후보를 고르고 분류는 resolver에 위임한다 — cwd 문자열 파싱·.opal-worktrees 문자열 추론·부모 디렉터리 순회·mtime·updated_at 최신순 선택을 하지 않는다. 현재 세션 강제 후보가 정확히 1건이면 그 태스크의 transition_action만 평가하고, 복수면 defer_to_pm + multiple_hub_tasks로 무소유·만료 후보까지 한 반환에 담는다(무조건 fail-open도, 임의 단일 선택도 하지 않는다). stop_hook_active면 먼저 직전 receipt의 block_count를 플랫폼 상한과 비교해 allow_block_cap_reached로 빠져나가고(상한 env 미설정이면 검사 생략, 자체 고정 상한 없음), 이어 직전 fingerprint와 같으면 allow_no_progress_same_fingerprint로 통과하며 달라졌을 때만 재차단한다. D-21대로 claim_source=session_start인 current_session_owned 후보(SessionStart 자동 claim만 있는 수동 소유)는 강제 후보에서 빼고 passive_ownership 진단만 남기며 소유권 분류 자체는 유지한다 — claim_source=state_transition일 때만 강제 후보다(hub_canonical·worktree_canonical 취급은 무변경). foreign_session_owned·worktree_owned_shadow 후보는 강제 후보가 아니므로 Stop을 통과시키고 진단에만 남는다. block_continue·defer_to_pm은 판정 대상 task_id 전건과 각 transition_action·next_action을 나열한 reason을 함께 반환한다. decision_kind·diagnostic은 decisions의 D-3 폐쇄 enum 값만 쓴다.",
  "exports": ["evaluate", "build_reason"],
  "depends": ["ownership_tool.decisions", "ownership_tool.fingerprint", "ownership_tool.ownership_core", "ownership_tool.resolver", "ownership_tool.claude_adapter"]
}
"""
from __future__ import annotations

import os
import pathlib

from . import claude_adapter, decisions, fingerprint, ownership_core, resolver

# registry meta 디렉터리 — 발급 계약이 정한 위치만 읽는다(추론하지 않는다).
_REGISTRY_META_GLOB = "task_*.json"

# 강제 후보(현재 세션이 이어가야 하는 태스크)로 인정하는 분류
_FORCED_CLASSIFICATIONS = ("hub_canonical", "worktree_canonical", "current_session_owned")

# D-21 — claim_source가 session_start인 current_session_owned만 강제 후보에서 뺀다.
# hub_canonical·worktree_canonical의 취급은 바뀌지 않는다.
_PASSIVE_ELIGIBLE_CLASSIFICATION = "current_session_owned"
_PASSIVE_CLAIM_SOURCE = "session_start"

# current_status → transition_action 파생. resolver가 후보로 세우는 상태는
# in_progress·blocked 2종뿐이므로 그 2종과 종료 상태만 다룬다.
_STATUS_TRANSITION = {
    "in_progress": "continue",
    "blocked": "await_user",
    "completed": "complete",
    "done": "complete",
}

# transition_action → D-3 decision_kind
_TRANSITION_DECISION = {
    "continue": "block_continue",
    "await_user": "allow_await_user",
    "complete": "allow_complete",
}


# ─────────────────────────────────────────────────────────────────────────────
# registry 로드 — 발급된 meta 디렉터리만 읽는다
# ─────────────────────────────────────────────────────────────────────────────

def _load_registry(project_root):
    """<project_root>/.opal-worktrees/.meta/task_*.json 전건을 이름순으로 읽어 반환한다.

    디렉터리 부재·손상 JSON은 예외가 아니라 빈 목록/해당 항목 생략으로 처리한다.
    """
    if not project_root:
        return []
    meta_dir = pathlib.Path(project_root) / ".opal-worktrees" / ".meta"
    try:
        names = sorted(p.name for p in meta_dir.glob(_REGISTRY_META_GLOB))
    except OSError:
        return []
    entries = []
    for name in names:
        read = ownership_core.read_json(meta_dir / name)
        if read.get("ok") and isinstance(read.get("data"), dict):
            entries.append(read["data"])
    return entries


def _registry_entry_for_home(entries, cwd):
    """cwd와 정확히 일치하는 `task_home`을 가진 registry entry를 찾는다. 없으면 None."""
    if not cwd:
        return None
    target = str(pathlib.Path(cwd))
    for entry in entries:
        home = entry.get("task_home")
        if home and str(pathlib.Path(str(home))) == target:
            return entry
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 후보 → 전이 해석
# ─────────────────────────────────────────────────────────────────────────────

def _state_view_transition(show_json):
    """state-tool show 응답에서 transition_action을 읽는다. 없으면 None."""
    if not isinstance(show_json, dict):
        return None
    value = show_json.get("transition_action")
    if value is None and isinstance(show_json.get("data"), dict):
        value = show_json["data"].get("transition_action")
    return value


def _state_view_next_action(show_json):
    if not isinstance(show_json, dict):
        return None
    value = show_json.get("next_action")
    if value is None and isinstance(show_json.get("data"), dict):
        value = show_json["data"].get("next_action")
    return value


def _candidate_transition(candidate):
    """후보 state의 current_status에서 transition_action을 파생한다."""
    state = candidate.get("state") or {}
    return _STATUS_TRANSITION.get(state.get("current_status"))


def build_reason(kind, rows):
    """차단 사유문을 만든다. rows는 (task_id, transition_action, next_action) 튜플 목록.

    PM이 어느 태스크에 대한 판정인지 알 수 있도록 판정 대상 task_id 전건과 각
    transition_action·next_action을 반드시 나열한다.
    """
    parts = []
    for task_id, transition_action, next_action in rows:
        parts.append(
            "task_id={} | transition_action={} | next_action={}".format(
                task_id or "(unknown)",
                transition_action or "(none)",
                next_action or "(none)",
            )
        )
    head = "OPAL Stop guard: {}. 판정 대상 {}건 — ".format(kind, len(rows))
    tail = " / ".join(parts)
    if kind == "defer_to_pm":
        return head + tail + " · 현재 세션이 복수 허브 태스크를 소유해 자동 선택하지 않는다. PM이 이어갈 태스크를 지정하라."
    return head + tail + " · 이 태스크가 아직 transition_action=continue다. 응답을 끝내지 말고 이어서 진행하라."


# ─────────────────────────────────────────────────────────────────────────────
# 공개 API
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(payload, project_root=None, now=None, show_json=None, prior_receipt=None, env=None):
    """Stop hook 봉투를 판정해 {decision_kind, diagnostics, candidates, evidence(+reason, block_count)}를 반환한다.

    판정 순서 — ① registry로 cwd 해석 후 resolver로 후보 분류 ② stop_hook_active면
    block_count 상한·직전 fingerprint 동일 여부로 통과 판정 ③ 강제 후보 0건이면 비활성 통과,
    복수면 defer_to_pm, 1건이면 그 태스크의 transition_action만 평가. 예외를 던지지 않는다.
    """
    payload = payload if isinstance(payload, dict) else {}
    env = os.environ if env is None else env
    session_id = ownership_core.resolve_session_id(env, payload)
    cwd = payload.get("cwd") or project_root
    stop_hook_active = bool(payload.get("stop_hook_active"))

    registry = _load_registry(project_root)
    home_entry = _registry_entry_for_home(registry, cwd)
    if home_entry is not None:
        candidates = resolver.resolve_worktree(home_entry.get("task_home"), registry)
    else:
        candidates = resolver.resolve_hub(project_root, registry, session_id, now=now)

    diagnostics = []
    ambiguous = False
    for candidate in candidates:
        for diagnostic in candidate.get("diagnostics") or []:
            if diagnostic not in diagnostics:
                diagnostics.append(diagnostic)
        if (candidate.get("evidence") or {}).get("task_path_ambiguous"):
            ambiguous = True

    # D-21 — SessionStart 자동 claim(claim_source=session_start)만 있는 소유는 수동
    # 소유권이다. 소유권 자체(classification·타 세션 거부·heartbeat)는 유지하되 강제
    # 후보에서만 빼고 passive_ownership 진단으로 남긴다.
    for candidate in candidates:
        if candidate.get("classification") != _PASSIVE_ELIGIBLE_CLASSIFICATION:
            continue
        if not candidate.get("forced"):
            continue
        claim_source = (candidate.get("evidence") or {}).get("claim_source")
        if claim_source == _PASSIVE_CLAIM_SOURCE:
            candidate["forced"] = False
            if "passive_ownership" not in diagnostics:
                diagnostics.append("passive_ownership")

    forced = [
        c for c in candidates
        if c.get("forced") and c.get("classification") in _FORCED_CLASSIFICATIONS
    ]

    evidence = {
        "session_id": session_id,
        "cwd": str(cwd) if cwd else None,
        "project_root": str(project_root) if project_root else None,
        "registry_entry_count": len(registry),
        "candidate_count": len(candidates),
        "forced_count": len(forced),
        "task_path_ambiguous": ambiguous,
        "stop_hook_active": stop_hook_active,
    }

    current_fingerprint = fingerprint.compute(show_json) if show_json is not None else None
    if current_fingerprint is not None:
        evidence["fingerprint"] = current_fingerprint

    receipt = prior_receipt
    if receipt is None and project_root is not None and session_id:
        receipt = fingerprint.load_receipt(project_root, session_id)
    prior_block_count = 0
    if isinstance(receipt, dict):
        try:
            prior_block_count = int(receipt.get("block_count") or 0)
        except (TypeError, ValueError):
            prior_block_count = 0

    # ② 반복 Stop 가드 — 상한 도달과 무진행을 차단 이전에 확인한다.
    if stop_hook_active and isinstance(receipt, dict):
        block_cap = claude_adapter.stop_hook_block_cap(env)
        if block_cap is not None and prior_block_count >= block_cap:
            evidence["block_cap"] = block_cap
            evidence["prior_block_count"] = prior_block_count
            return _finish("allow_block_cap_reached", diagnostics, candidates, evidence,
                           project_root, session_id, current_fingerprint, prior_block_count, now)
        if current_fingerprint is not None and current_fingerprint == receipt.get("fingerprint"):
            if "no_progress_same_fingerprint" not in diagnostics:
                diagnostics.append("no_progress_same_fingerprint")
            evidence["prior_block_count"] = prior_block_count
            return _finish("allow_no_progress_same_fingerprint", diagnostics, candidates, evidence,
                           project_root, session_id, current_fingerprint, prior_block_count, now)

    # ③ 강제 후보 수로 갈린다.
    view_transition = _state_view_transition(show_json)

    if len(forced) > 1:
        if "multiple_hub_tasks" not in diagnostics:
            diagnostics.append("multiple_hub_tasks")
        rows = [
            (
                c.get("task_id"),
                _candidate_transition(c),
                (c.get("state") or {}).get("next_action"),
            )
            for c in candidates
        ]
        return _finish("defer_to_pm", diagnostics, candidates, evidence,
                       project_root, session_id, current_fingerprint, prior_block_count, now,
                       reason=build_reason("defer_to_pm", rows),
                       block_count=prior_block_count + 1)

    if len(forced) == 1:
        target = forced[0]
        transition = view_transition or _candidate_transition(target)
        next_action = (target.get("state") or {}).get("next_action") or _state_view_next_action(show_json)
        rows = [(target.get("task_id"), transition, next_action)]
    elif show_json is not None:
        # 강제 후보를 세우지 못했지만 호출자가 대상 태스크의 state 뷰를 직접 준 경우
        # (반복 Stop 경로) 그 뷰의 transition_action만 평가한다.
        target = None
        transition = view_transition
        data = show_json.get("data") if isinstance(show_json.get("data"), dict) else {}
        rows = [(data.get("task_id"), transition, _state_view_next_action(show_json))]
    else:
        if "no_owned_task" not in diagnostics:
            diagnostics.append("no_owned_task")
        return _finish("allow_inactive", diagnostics, candidates, evidence,
                       project_root, session_id, current_fingerprint, prior_block_count, now)

    kind = _TRANSITION_DECISION.get(transition, "allow_inactive")
    if kind != "block_continue":
        return _finish(kind, diagnostics, candidates, evidence,
                       project_root, session_id, current_fingerprint, prior_block_count, now)
    return _finish("block_continue", diagnostics, candidates, evidence,
                   project_root, session_id, current_fingerprint, prior_block_count, now,
                   reason=build_reason("block_continue", rows),
                   block_count=prior_block_count + 1)


def _finish(kind, diagnostics, candidates, evidence, project_root, session_id,
            current_fingerprint, prior_block_count, now, reason=None, block_count=None):
    """판정 결과를 조립하고 다음 Stop과 비교할 receipt를 남긴다."""
    result = decisions.Decision(
        decision_kind=kind,
        diagnostics=list(diagnostics),
        candidates=list(candidates),
        evidence=dict(evidence),
    ).to_dict()
    effective_block_count = prior_block_count if block_count is None else block_count
    if reason is not None:
        result["reason"] = reason
    if block_count is not None:
        result["block_count"] = block_count

    if project_root is not None and session_id:
        fingerprint.save_receipt(
            project_root,
            {
                "session_id": session_id,
                "fingerprint": current_fingerprint,
                "decision_kind": kind,
                "decided_at": now,
                "block_count": effective_block_count,
            },
        )
    return result
