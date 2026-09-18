"""
@header {
  "module": "launcher_core",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "허브에서 워크트리 실행 세션을 띄우는 launcher 공통 lifecycle. `run(adapter, hub_root=…, task=…, worktree_root=…, command=…)`이 preflight(registry meta 조회 → 등록된 worktree_root 동치 확인 → `hub_owned`이면 `session_launching`으로 전이, 이미 `session_launching`이면 그대로 이어받아 generation을 낭비하지 않는다) → `adapter.launch(worktree_root, command)` 1회 호출 → launch receipt({adapter, adapter_handle, reported_cwd, launched_at}) 수집 → reported_cwd가 registry worktree_root와 realpath 동치인지 검사 → handoff prompt 제출 receipt({prompt_id, submitted_at}) 수집 → `worktree_session_owned` 전이 순으로 진행한다. launch 실패·prompt 실패·cwd 불일치 어느 경로든 `failure_reason=launch_failed` + `hub_owned` + attribution 키 부재 + generation 증가를 단일 교체로 담는 원자 복귀를 호출해 dual owner·orphan `session_launching`을 남기지 않는다. 상태 쓰기는 전부 worktree-tool의 `ownership-set` 계약을 subprocess로 경유하며 이 모듈은 registry 쓰기 로직·lock·원자 교체를 복제하지 않는다(사설 ownership writer 금지). registry 읽기는 인자로 받은 hub_root·task로 만든 `<hub_root>/.opal-worktrees/.meta/task_{task}.json` 1경로에서만 하고 경로 문자열·basename·mtime으로 신원을 추론하지 않는다. adapter는 호출자가 명시 선택해 주입하며 OS·터미널 종류를 추측하지 않는다. 플랫폼 고유 env 변수명은 이 도구에 두지 않는다(C-15 — ownership-tool의 claude_adapter 전용).",
  "exports": [
    "WORKTREE_TOOL_PATH", "FAILURE_REASON_LAUNCH_FAILED",
    "LauncherError", "registry_meta_path", "read_registry_meta",
    "build_launch_receipt", "build_prompt_receipt", "ownership_set", "run"
  ],
  "depends": ["opal/tools/worktree-tool/worktree_tool.py(ownership-set CLI 계약)"]
}
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

# 상태 쓰기의 유일한 경로 — W-11(worktree_tool.cmd_ownership_set)이 소유하는 CLI 계약.
WORKTREE_TOOL_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "worktree-tool" / "worktree_tool.py"
)

# worktree_tool.py의 동명 상수와 같은 토큰을 쓴다(값 복제일 뿐 판정 로직은 그쪽이 소유).
EXEC_STATE_HUB_OWNED = "hub_owned"
EXEC_STATE_SESSION_LAUNCHING = "session_launching"
EXEC_STATE_WORKTREE_SESSION_OWNED = "worktree_session_owned"
ATTRIBUTION_TOKEN_ACTIVE = "active"
FAILURE_REASON_LAUNCH_FAILED = "launch_failed"

LAUNCH_RECEIPT_FIELDS = ("adapter", "adapter_handle", "reported_cwd", "launched_at")
PROMPT_RECEIPT_FIELDS = ("prompt_id", "submitted_at")

OWNERSHIP_SET_TIMEOUT_SEC = 60


class LauncherError(RuntimeError):
    """`ownership-set` 경유 호출 자체가 실패했을 때만 쓴다 — lifecycle 경로 실패는
    예외가 아니라 구조화 dict(`failure_reason=launch_failed`)로 반환한다."""


# ─────────────────────────────────────────────────────────────────────────────
# registry 읽기 — 쓰기는 하지 않는다
# ─────────────────────────────────────────────────────────────────────────────


def registry_meta_path(hub_root, task: str) -> pathlib.Path:
    """registry meta 경로. 허브 루트와 task 번호는 **인자로 발급받은 값**만 쓴다 —
    경로 문자열 접두·basename·mtime 추론을 하지 않는다(harness/worktree.md §canonical
    path 발급 계약, C-6)."""
    return pathlib.Path(hub_root) / ".opal-worktrees" / ".meta" / f"task_{task}.json"


def read_registry_meta(hub_root, task: str) -> dict:
    """registry meta를 읽기 전용으로 파싱한다. 부재·손상은 LauncherError다."""
    path = registry_meta_path(hub_root, task)
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LauncherError(f"registry_meta_unreadable: {path}") from exc
    if not isinstance(meta, dict):
        raise LauncherError(f"registry_meta_invalid: {path}")
    return meta


# ─────────────────────────────────────────────────────────────────────────────
# receipt 조립 — adapter가 보고한 값만 담는다(추측·기본값 주입 없음)
# ─────────────────────────────────────────────────────────────────────────────


def _complete(report: dict, fields) -> bool:
    return all(report.get(field) not in (None, "") for field in fields)


def build_launch_receipt(report: dict):
    """launch receipt {adapter, adapter_handle, reported_cwd, launched_at}.
    한 필드라도 비어 있거나 exit_code가 0이 아니면 None(=launch 실패)이다."""
    if report.get("exit_code") not in (0, None) or not _complete(
        report, LAUNCH_RECEIPT_FIELDS
    ):
        return None
    return {field: report[field] for field in LAUNCH_RECEIPT_FIELDS}


def build_prompt_receipt(report: dict):
    """handoff prompt 제출 receipt {prompt_id, submitted_at}. 비면 None(=prompt 실패)."""
    if not _complete(report, PROMPT_RECEIPT_FIELDS):
        return None
    return {field: report[field] for field in PROMPT_RECEIPT_FIELDS}


# ─────────────────────────────────────────────────────────────────────────────
# 상태 전이 — worktree-tool `ownership-set` 단일 경유
# ─────────────────────────────────────────────────────────────────────────────


def ownership_set(hub_root, task: str, state: str, **options) -> dict:
    """`worktree-tool ownership-set`을 subprocess로 호출하고 응답 JSON을 돌려준다.

    registry lock·원자 교체·허용 조합·generation 단조성·receipt 2종 요구는 전부 그쪽
    계약이 판정한다 — launcher는 인자를 넘길 뿐 registry 쓰기 로직을 복제하지 않는다.
    """
    argv = [
        sys.executable,
        str(WORKTREE_TOOL_PATH),
        "ownership-set",
        "--project-root",
        str(hub_root),
        "--task",
        str(task),
        "--execution-ownership",
        state,
        "--attribution-state",
        ATTRIBUTION_TOKEN_ACTIVE,
    ]
    for flag, value in (
        ("--owner-session-id", options.get("owner_session_id")),
        ("--adapter", options.get("adapter")),
        ("--adapter-handle", options.get("adapter_handle")),
        ("--failure-reason", options.get("failure_reason")),
    ):
        if value:
            argv += [flag, str(value)]
    for flag, receipt in (
        ("--launch-receipt", options.get("launch_receipt")),
        ("--prompt-receipt", options.get("prompt_receipt")),
    ):
        if receipt:
            argv += [flag, json.dumps(receipt, ensure_ascii=False, sort_keys=True)]

    completed = subprocess.run(
        argv, capture_output=True, text=True, timeout=OWNERSHIP_SET_TIMEOUT_SEC
    )
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise LauncherError(
            f"ownership_set_unparsable: rc={completed.returncode} "
            f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
        ) from exc
    return response


def _revert(hub_root, task: str, detail: str, adapter_name=None) -> dict:
    """원자 복귀 — `failure_reason=launch_failed` + `hub_owned` + attribution 키 부재 +
    generation 증가를 `ownership-set` 한 번의 교체로 담는다(owner·receipt 소거는 그쪽이
    같은 교체 안에서 수행하므로 중간 상태가 생기지 않는다)."""
    response = ownership_set(
        hub_root,
        task,
        EXEC_STATE_HUB_OWNED,
        adapter=adapter_name,
        failure_reason=FAILURE_REASON_LAUNCH_FAILED,
    )
    if not response.get("ok"):
        raise LauncherError(f"ownership_revert_failed: {response}")
    block = response.get("execution_ownership") or {}
    return {
        "ok": False,
        "status": block.get("state"),
        "failure_reason": FAILURE_REASON_LAUNCH_FAILED,
        "detail": detail,
        "task": task,
        "generation": block.get("generation"),
        "meta_path": response.get("meta_path"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# lifecycle
# ─────────────────────────────────────────────────────────────────────────────


def run(adapter, *, hub_root, task, worktree_root, command, owner_session_id=None) -> dict:
    """launcher 공통 lifecycle 1회 실행.

    `adapter`는 호출자가 명시 선택해 주입한 seam이며 `launch(worktree_root, command)`
    **한 번**으로 터미널 기동과 handoff prompt 제출을 수행하고 두 receipt의 원천 필드를
    한 보고 dict로 돌려준다(OS·터미널 추측 금지 — adapter가 그 지식을 소유한다).
    """
    hub_root = pathlib.Path(hub_root)
    task = str(task)
    worktree_root = pathlib.Path(worktree_root)

    meta = read_registry_meta(hub_root, task)
    registered_root = meta.get("worktree_root")
    if not registered_root:
        raise LauncherError(f"registry_worktree_root_missing: task={task}")
    if os.path.realpath(str(registered_root)) != os.path.realpath(str(worktree_root)):
        raise LauncherError(
            f"worktree_root_mismatch: registry={registered_root} arg={worktree_root}"
        )

    block = meta.get("execution_ownership") or {}
    prior_state = block.get("state")
    adapter_name = block.get("adapter") or getattr(adapter, "name", None)

    if prior_state == EXEC_STATE_HUB_OWNED:
        # 허브 소유에서만 launching을 새로 연다. 이미 session_launching이면 그 소유를
        # 이어받아 generation을 낭비하지 않는다(멱등 재진입).
        response = ownership_set(
            hub_root,
            task,
            EXEC_STATE_SESSION_LAUNCHING,
            owner_session_id=owner_session_id,
            adapter=adapter_name,
        )
        if not response.get("ok"):
            raise LauncherError(f"ownership_preflight_failed: {response}")
    elif prior_state != EXEC_STATE_SESSION_LAUNCHING:
        # hub_owned도 session_launching도 아니면 이 태스크는 이미 다른 소유자의 것이다 —
        # 상태를 건드리지 않고 거부한다(dual owner 금지).
        return {
            "ok": False,
            "status": prior_state,
            "error": "ownership_not_launchable",
            "task": task,
        }

    report = adapter.launch(worktree_root, command)
    if not isinstance(report, dict):
        return _revert(hub_root, task, "adapter_report_invalid", adapter_name)
    adapter_name = report.get("adapter") or adapter_name

    launch_receipt = build_launch_receipt(report)
    if launch_receipt is None:
        return _revert(hub_root, task, "launch_receipt_missing", adapter_name)

    # [MUST] reported_cwd가 registry worktree_root와 일치하지 않으면 전이하지 않는다.
    if os.path.realpath(str(launch_receipt["reported_cwd"])) != os.path.realpath(
        str(registered_root)
    ):
        return _revert(hub_root, task, "reported_cwd_mismatch", adapter_name)

    prompt_receipt = build_prompt_receipt(report)
    if prompt_receipt is None:
        return _revert(hub_root, task, "prompt_receipt_missing", adapter_name)

    response = ownership_set(
        hub_root,
        task,
        EXEC_STATE_WORKTREE_SESSION_OWNED,
        owner_session_id=owner_session_id,
        adapter=adapter_name,
        adapter_handle=launch_receipt["adapter_handle"],
        launch_receipt=launch_receipt,
        prompt_receipt=prompt_receipt,
    )
    if not response.get("ok"):
        return _revert(hub_root, task, f"ownership_set_rejected: {response}", adapter_name)

    owned = response.get("execution_ownership") or {}
    return {
        "ok": True,
        "status": owned.get("state"),
        "failure_reason": None,
        "task": task,
        "generation": owned.get("generation"),
        "adapter": owned.get("adapter"),
        "adapter_handle": owned.get("adapter_handle"),
        "launch_receipt": launch_receipt,
        "prompt_receipt": prompt_receipt,
        "meta_path": response.get("meta_path"),
    }
