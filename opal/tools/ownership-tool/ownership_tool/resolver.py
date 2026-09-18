"""
@header {
  "module": "ownership_tool.resolver",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "W-5 worktree/hub 후보 resolver. resolve_worktree는 registry meta가 발급한 exact canonical task_path 하나만 후보로 평가하며 cwd 문자열·워크트리 이름·부모 디렉터리 순회·시각 기반 정렬을 일절 하지 않는다(테스트가 os.walk/iterdir/parents 부재를 집행). resolve_hub는 <hub_root>/tasks/ 직계 자식 1단계만 열어 current_status가 in_progress·blocked인 태스크를 모은 뒤 registry 전건과 대조해 hub_canonical·worktree_owned_shadow·current_session_owned·foreign_session_owned·unowned·lease_expired·invalid_state로 분류한다. shadow 조건은 task_ownership_version 존재 + attribution_state가 active 3상태(키 부재·completed_unmerged·attribution_pending) + canonical task_path가 허브 사본 경로(<hub_root>/tasks/<task_folder>)와 realpath 정규화 후 다름(허브 밖 여부로 판정하지 않는다 — 실물 canonical은 <hub_root>/.opal-worktrees/task_NNN/tasks/… 로 허브 안에 있다) + 허브 동명 task_folder 사본 존재이며, attribution_state가 closed면 shadow가 아니라 hub_canonical이다(AC-11). D-14대로 shadow 후보는 강제 후보에서 제외(forced False)하고 canonical path를 task_path로 반환하지 않으며 task_path_ambiguous 동시 발화 사실만 evidence에 남긴다. hub_root는 호출자가 준 인자만 사용하고 cwd·.opal-worktrees 문자열·task_path 조상에서 추론하지 않는다. 손상 registry·손상 state는 예외 대신 invalid_registry·invalid_state 분류로 반환한다. registry 미대조 허브 후보는 lease 레코드가 있을 때 D-21 claim_source를 evidence에 노출한다(분류 기준 무변경). 후보 정렬은 task_id 사전순이다.",
  "exports": ["resolve_worktree", "resolve_hub", "classify"],
  "depends": ["ownership_tool.ownership_core", "ownership_tool.lease", "ownership_tool.decisions"]
}
"""
from __future__ import annotations

import os
import pathlib

from . import decisions, lease, ownership_core

# ownership_core.read_registry_meta와 동일한 registry 필수 키 계약(SSOT: ownership_core).
# 이 모듈은 파일이 아니라 이미 읽힌 registry 객체도 받으므로 같은 검사를 여기서 적용한다.
REGISTRY_REQUIRED_KEYS = ("allocator_root", "task_home", "task_folder", "task_path", "artifact_repo")

# worktree.md §상태 의존 해석 — attribution active 3상태(키 부재 포함). closed만 통과(AC-11).
ACTIVE_ATTRIBUTION_STATES = (None, "completed_unmerged", "attribution_pending")

# 허브 후보로 세울 수 있는 태스크 진행 상태
HUB_ACTIVE_STATUSES = ("in_progress", "blocked")

# 분류 라벨(후보 dict의 classification). D-3 DIAGNOSTICS와는 다른 축이며,
# diagnostics 목록에는 decisions.DIAGNOSTICS 폐쇄 enum 값만 넣는다.
CLASSIFICATION_INVALID_REGISTRY = "invalid_registry"
CLASSIFICATION_INVALID_STATE = "invalid_state"
CLASSIFICATION_WORKTREE_CANONICAL = "worktree_canonical"
CLASSIFICATION_HUB_CANONICAL = "hub_canonical"
CLASSIFICATION_WORKTREE_OWNED_SHADOW = "worktree_owned_shadow"

_LEASE_DIAGNOSTIC = {
    "foreign_session_owned": "foreign_owner",
    "lease_expired": "lease_expired",
}


# ─────────────────────────────────────────────────────────────────────────────
# 내부 헬퍼 — 경로·registry 정규화
# ─────────────────────────────────────────────────────────────────────────────

def _as_path_str(value):
    """경로 문자열로 정규화한다. 실패하면 None(예외를 던지지 않는다)."""
    if value is None:
        return None
    try:
        return str(pathlib.Path(str(value)))
    except (TypeError, ValueError):
        return None


def _is_inside(child, root):
    """child가 root와 같거나 root 아래에 있으면 True. 문자열 비교만 하며 디스크를 읽지 않는다."""
    if not child or not root:
        return False
    if child == root:
        return True
    return child.startswith(root.rstrip(os.sep) + os.sep)


def _same_path(left, right):
    """두 경로가 같은 위치를 가리키면 True.

    심볼릭 링크·후행 슬래시·상대 경로 차이로 오판하지 않도록 realpath로 정규화한 뒤
    비교한다. 어느 한쪽이라도 정규화에 실패하면 False(예외를 던지지 않는다).
    """
    left_text = _as_path_str(left)
    right_text = _as_path_str(right)
    if not left_text or not right_text:
        return False
    try:
        return os.path.realpath(left_text) == os.path.realpath(right_text)
    except (OSError, TypeError, ValueError):
        return False


def _registry_entries(registry):
    """registry 인자를 (유효 entry 목록, 무효 사유 목록)으로 정규화한다.

    dict 1건·entry 목록·meta 파일 경로·손상 원문 문자열을 모두 수용한다. 손상 JSON 원문이나
    필수 키 누락은 예외가 아니라 무효 사유로 수집된다.
    """
    items = registry if isinstance(registry, (list, tuple)) else [registry]
    valid = []
    invalid = []
    for item in items:
        data = item
        if isinstance(data, (str, bytes, os.PathLike)):
            read = ownership_core.read_json(_as_path_str(data) or "")
            data = read["data"] if read["ok"] else None
        if not isinstance(data, dict):
            invalid.append("registry_not_object")
            continue
        missing = [key for key in REGISTRY_REQUIRED_KEYS if not data.get(key)]
        if missing:
            invalid.append("missing_keys:" + ",".join(missing))
            continue
        valid.append(data)
    return valid, invalid


def _read_state(task_dir):
    """<task_dir>/state.json을 읽는다. (state 요약 | None, 읽기 오류 코드 | None)."""
    state_path = pathlib.Path(task_dir) / "state.json"
    read = ownership_core.read_json(state_path)
    if not read["ok"]:
        return None, read["error"]
    data = read["data"]
    if not isinstance(data, dict):
        return None, "invalid_json"
    return {
        "task_id": data.get("task_id"),
        "current_status": data.get("current_status"),
        "next_action": data.get("next_action"),
    }, None


def _candidate(task_path, task_id, classification, forced, diagnostics, evidence, state):
    return {
        "task_path": task_path,
        "task_id": task_id,
        "classification": classification,
        "forced": bool(forced),
        "diagnostics": [d for d in diagnostics if d in decisions.DIAGNOSTICS],
        "evidence": dict(evidence),
        "state": dict(state) if state else {},
    }


def _invalid_registry_candidate(root, details):
    return _candidate(
        task_path=None,
        task_id=None,
        classification=CLASSIFICATION_INVALID_REGISTRY,
        forced=False,
        diagnostics=["invalid_registry"],
        evidence={"requested_root": root, "detail": list(details)},
        state={},
    )


# ─────────────────────────────────────────────────────────────────────────────
# 공개 API
# ─────────────────────────────────────────────────────────────────────────────

def resolve_worktree(worktree_root, registry):
    """worktree_root에 대응하는 registry exact canonical task_path 1건만 후보로 반환한다.

    worktree_root 아래 `tasks/`를 스캔하지 않으므로 화석 태스크 폴더는 어떤 경우에도 후보가
    되지 않는다. registry가 손상 원문·비객체·필수 키 누락이거나 worktree_root가 발급된
    `task_home`과 다르거나 canonical `task_path`가 `task_home` 밖이면 `invalid_registry`
    분류 후보 1건을 반환한다. 예외를 던지지 않는다.
    """
    root = _as_path_str(worktree_root)
    valid, invalid = _registry_entries(registry)

    entry = None
    for item in valid:
        if _as_path_str(item.get("task_home")) == root:
            entry = item
            break
    if entry is None:
        details = list(invalid) or ["task_home_mismatch"]
        return [_invalid_registry_candidate(root, details)]

    raw_task_path = entry.get("task_path")
    task_path = _as_path_str(raw_task_path)
    if not _is_inside(task_path, root):
        return [_invalid_registry_candidate(root, ["task_path_outside_task_home"])]

    state, state_error = _read_state(task_path)
    diagnostics = []
    if state is None:
        diagnostics.append("invalid_state")
    evidence = {
        "source": "registry_meta",
        "task_home": entry.get("task_home"),
        "attribution_state": entry.get("attribution_state"),
        "legacy": entry.get("task_ownership_version") is None,
    }
    if state_error:
        evidence["state_error"] = state_error

    forced = bool(state) and state.get("current_status") in HUB_ACTIVE_STATUSES
    return [
        _candidate(
            task_path=raw_task_path,
            task_id=entry.get("task_folder"),
            classification=CLASSIFICATION_WORKTREE_CANONICAL,
            forced=forced,
            diagnostics=diagnostics,
            evidence=evidence,
            state=state or {},
        )
    ]


def resolve_hub(hub_root, registry_or_list, session_id, now=None):
    """<hub_root>/tasks/ 직계 자식만 1단계 열어 활성 허브 태스크 후보를 분류해 반환한다.

    hub_root는 호출자가 준 인자만 사용한다(cwd·`.opal-worktrees` 문자열·`task_path` 조상에서
    추론하지 않는다). registry 전건과 `task_folder`로 대조해 아래처럼 분류한다.

    - registry active(=`task_ownership_version` 존재 + `attribution_state`가 active 3상태) +
      canonical `task_path`가 허브 사본 경로(`<hub_root>/tasks/<task_folder>`)와 realpath
      정규화 후 다름 → `worktree_owned_shadow`(forced False, `task_path_ambiguous` 동시
      발화를 evidence에 기록, canonical path는 반환하지 않는다). 허브 밖 여부로 판정하지
      않는다 — 실물 canonical은 `<hub_root>/.opal-worktrees/task_NNN/tasks/…`로 허브 안이다.
    - `attribution_state: closed` 또는 canonical이 곧 허브 사본 경로 → `hub_canonical`.
    - registry에 없는 허브 태스크 → lease 판정(`current_session_owned`만 강제 후보). lease 레코드가
      있으면 D-21 `claim_source`를 evidence에 노출한다(분류 기준 자체는 바뀌지 않는다).

    정렬은 `task_id` 사전순이다. 예외를 던지지 않는다.
    """
    root = _as_path_str(hub_root)
    valid, _invalid = _registry_entries(registry_or_list)
    by_folder = {}
    for item in valid:
        folder = item.get("task_folder")
        if folder and folder not in by_folder:
            by_folder[folder] = item

    candidates = []
    if not root:
        return candidates

    tasks_dir = pathlib.Path(root) / "tasks"
    try:
        names = sorted(os.listdir(str(tasks_dir)))
    except OSError:
        return candidates

    for name in names:
        task_dir = tasks_dir / name
        task_path = str(task_dir)
        state, state_error = _read_state(task_dir)
        if state is None:
            if state_error == "invalid_json":
                candidates.append(
                    _candidate(
                        task_path=task_path,
                        task_id=name,
                        classification=CLASSIFICATION_INVALID_STATE,
                        forced=False,
                        diagnostics=["invalid_state"],
                        evidence={"state_error": state_error},
                        state={},
                    )
                )
            continue
        if state.get("current_status") not in HUB_ACTIVE_STATUSES:
            continue

        evidence = {
            "hub_root": root,
            "lease_path": str(ownership_core.hub_lease_path(task_path)),
        }
        entry = by_folder.get(name)
        if entry is not None:
            canonical = _as_path_str(entry.get("task_path"))
            attribution = entry.get("attribution_state")
            evidence["attribution_state"] = attribution
            evidence["registry_matched"] = True
            shadow = (
                entry.get("task_ownership_version") is not None
                and attribution in ACTIVE_ATTRIBUTION_STATES
                and not _same_path(canonical, task_path)
            )
            if shadow:
                # D-14 — canonical path는 반환하지 않고 동시 발화 사실만 근거로 남긴다.
                evidence["task_path_ambiguous"] = True
                evidence["canonical_task_path"] = entry.get("task_path")
                candidates.append(
                    _candidate(
                        task_path=task_path,
                        task_id=name,
                        classification=CLASSIFICATION_WORKTREE_OWNED_SHADOW,
                        forced=False,
                        diagnostics=["worktree_owned_shadow"],
                        evidence=evidence,
                        state=state,
                    )
                )
                continue
            candidates.append(
                _candidate(
                    task_path=task_path,
                    task_id=name,
                    classification=CLASSIFICATION_HUB_CANONICAL,
                    forced=True,
                    diagnostics=[],
                    evidence=evidence,
                    state=state,
                )
            )
            continue

        evidence["registry_matched"] = False
        lease_read = ownership_core.read_json(evidence["lease_path"])
        lease_record = lease_read["data"] if lease_read.get("ok") else None
        if isinstance(lease_record, dict):
            # D-21 — 판정 입력이 된 claim 출처를 근거로 노출한다(task_path_ambiguous와 같은 대칭).
            evidence["claim_source"] = lease.resolve_claim_source(lease_record)
        lease_class = classify(task_path, session_id, now=now)
        diagnostic = _LEASE_DIAGNOSTIC.get(lease_class)
        candidates.append(
            _candidate(
                task_path=task_path,
                task_id=name,
                classification=lease_class,
                forced=lease_class == "current_session_owned",
                diagnostics=[diagnostic] if diagnostic else [],
                evidence=evidence,
                state=state,
            )
        )

    return candidates


def classify(lease_record, session_id, now=None):
    """lease 레코드(dict) 또는 canonical task_path를 요청 세션 기준으로 판정한다.

    판정 규칙은 `lease.classify`가 소유하며 이 함수는 resolver 공개 표면으로 위임만 한다.
    반환값: current_session_owned | foreign_session_owned | unowned | lease_expired.
    """
    try:
        return lease.classify(lease_record, session_id, now=now)
    except Exception:  # noqa: BLE001 — 어떤 입력에서도 예외를 밖으로 던지지 않는다(C-8 fail-safe)
        return "unowned"
