"""
@header {
  "module": "launcher_core",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "워크트리 launcher lifecycle: registry 발급 경로 검증, 명시 ID 또는 ownership resolver의 신원 preflight, session_launching 전이, 고정 ID handoff, 공개 session-launch 부모 신원 격리, terminal/command receipt·cwd 검증, 공개 ownership-set --owner-from-lease 최종 전이. 실패는 정확한 terminal handle만 close하고 같은 ID로 cancel한 뒤 hub_owned 원자 복귀한다. 진단은 cause·adapter·가용 identity source 이름을 포함한다. lease·registry private writer를 만들지 않고 공개 ownership-tool/worktree-tool 계약에 위임한다.",
  "exports": [
    "WORKTREE_TOOL_PATH",
    "OWNERSHIP_TOOL_DIR",
    "FAILURE_REASON_LAUNCH_FAILED",
    "LauncherError",
    "registry_meta_path",
    "read_registry_meta",
    "task_meta_dir_path",
    "build_launch_receipt",
    "build_prompt_receipt",
    "ownership_set",
    "lease_handoff",
    "lease_handoff_cancel",
    "run"
  ],
  "depends": [
    "opal/tools/worktree-tool/worktree_tool.py",
    "ownership_tool.ownership_core",
    "ownership_tool.cli"
  ]
}
"""

from __future__ import annotations

import json
import os
import pathlib
import shlex
import subprocess
import sys
import time

# 상태 쓰기의 유일한 경로 — W-11(worktree_tool.cmd_ownership_set)이 소유하는 CLI 계약.
WORKTREE_TOOL_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "worktree-tool" / "worktree_tool.py"
)

# 실행 소유권(lease) 이관의 유일한 경로 — ownership-tool CLI가 소유하는 계약.
# 배치 규칙은 WORKTREE_TOOL_PATH와 동형의 형제 디렉터리다(경로 추론 없음).
OWNERSHIP_TOOL_DIR = pathlib.Path(__file__).resolve().parents[2] / "ownership-tool"

# worktree_tool.py의 동명 상수와 같은 토큰을 쓴다(값 복제일 뿐 판정 로직은 그쪽이 소유).
EXEC_STATE_HUB_OWNED = "hub_owned"
EXEC_STATE_SESSION_LAUNCHING = "session_launching"
EXEC_STATE_WORKTREE_SESSION_OWNED = "worktree_session_owned"
ATTRIBUTION_TOKEN_ACTIVE = "active"
FAILURE_REASON_LAUNCH_FAILED = "launch_failed"
FAILURE_REASON_SESSION_BOOT_TIMEOUT = "session_boot_timeout"
EXEC_STATE_RECOVERY_REQUIRED = "recovery_required"

LAUNCH_RECEIPT_FIELDS = ("adapter", "adapter_handle", "reported_cwd", "launched_at")
PROMPT_RECEIPT_FIELDS = ("prompt_id", "submitted_at")

OWNERSHIP_SET_TIMEOUT_SEC = 60
LEASE_TIMEOUT_SEC = 60
# Kept deliberately small: this observes a child claim; it is not a readiness wait.
LEASE_POLL_INTERVAL_SEC = 0.05

sys.path.insert(0, str(OWNERSHIP_TOOL_DIR))
from ownership_tool import ownership_core
from worktree_launcher import settings



class LauncherError(RuntimeError):
    """`ownership-set` 경유 호출 자체가 실패했을 때만 쓴다 — lifecycle 경로 실패는
    예외가 아니라 구조화 dict(`failure_reason=launch_failed`)로 반환한다."""


# ─────────────────────────────────────────────────────────────────────────────
# registry 읽기 — 쓰기는 하지 않는다
# ─────────────────────────────────────────────────────────────────────────────


def task_meta_dir_path(hub_root, task: str) -> pathlib.Path:
    """태스크 전용 메타 폴더(`<hub_root>/.opal-worktrees/.meta/task_{NNN}/`) 절대경로.
    `{meta_dir}` 치환 값과 launch 기동 전 점검이 공유하는 유일한 경로 계산 지점이다.
    허브 루트·task 번호는 인자로 발급받은 값만 쓴다."""
    return pathlib.Path(hub_root) / ".opal-worktrees" / ".meta" / f"task_{task}"


def registry_meta_path(hub_root, task: str) -> pathlib.Path:
    """registry meta 경로(`task_{NNN}/meta.json`, 태스크 전용 폴더 안). 허브 루트와
    task 번호는 **인자로 발급받은 값**만 쓴다 — 경로 문자열 접두·basename·mtime 추론을
    하지 않는다(harness/worktree.md §canonical path 발급 계약, C-6)."""
    return task_meta_dir_path(hub_root, task) / "meta.json"


def read_registry_meta(hub_root, task: str) -> dict:
    """registry meta를 읽기 전용으로 파싱한다. 태스크 전용 폴더 안의 `meta.json`
    (`registry_meta_path`) 하나만 읽는다 — 구 구조 평면 파일 조합·폴백은 두지 않는다.
    부재·손상은 LauncherError다."""
    path = registry_meta_path(hub_root, task)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LauncherError(f"registry_meta_unreadable: {path}") from exc
    try:
        meta = json.loads(text)
    except json.JSONDecodeError as exc:
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
        ("--expected-owner", options.get("expected_owner")),
        ("--exclude-owner", options.get("exclude_owner")),
        ("--terminal-creation", options.get("terminal_creation")),
        ("--observed-lease-owner", options.get("observed_lease_owner")),
    ):
        if value:
            argv += [flag, str(value)]
    if options.get("owner_from_lease"):
        argv.append("--owner-from-lease")
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


# ─────────────────────────────────────────────────────────────────────────────
# 실행 소유권(lease) 이관 — ownership-tool `handoff`/`handoff-cancel` 단일 경유
# ─────────────────────────────────────────────────────────────────────────────


def _lease_cli(subcommand: str, argv_tail, label: str) -> dict:
    """ownership-tool CLI를 subprocess로 호출하고 단일 라인 JSON 응답만 해석한다.

    lease 판정·저장·lock·만료는 전부 그쪽 계약이 소유한다 — launcher는 인자를 넘기고
    응답을 읽을 뿐 lease 저장 로직을 복제하지 않는다(D-2, 사설 lease writer 금지).
    """
    argv = [sys.executable, "-m", "ownership_tool.cli", subcommand] + list(argv_tail)
    env = dict(os.environ)
    inherited = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(OWNERSHIP_TOOL_DIR) + (
        os.pathsep + inherited if inherited else ""
    )
    completed = subprocess.run(
        argv, capture_output=True, text=True, timeout=LEASE_TIMEOUT_SEC, env=env
    )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise LauncherError(
            f"{label}_unparsable: rc={completed.returncode} "
            f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
        ) from exc


def lease_handoff(task_path, worktree_root, session_id=None) -> dict:
    """`ownership-tool handoff` 1회. 대상은 **registry 발급값**만 받는다(C-4, D-4)."""
    return _lease_cli(
        "handoff",
        [
            "--session-id", str(session_id),
            "--task-path",
            str(task_path),
            "--to-worktree-root",
            str(worktree_root),
        ],
        "lease_handoff",
    )


def lease_handoff_cancel(task_path, session_id=None) -> dict:
    """`ownership-tool handoff-cancel` 1회 — 이관 출발 세션만 취소할 수 있다."""
    return _lease_cli(
        "handoff-cancel", ["--task-path", str(task_path), "--session-id", str(session_id)], "lease_handoff_cancel"
    )


def _lease_handoff_for_launch(task_path, worktree_root, session_id) -> dict:
    """기동 직전 이관 1회. registry가 `task_path`를 발급하지 않은 태스크는 이관 대상 자체가
    없으므로 noop으로 통과시킨다 — 경로를 cwd·문자열로 지어내지 않는다(C-4)."""
    if not task_path:
        return {"ok": True, "noop": True, "diagnostic": "registry_task_path_missing"}
    return lease_handoff(task_path, worktree_root, session_id=session_id)


def _cancel_lease_handoff(task_path, session_id) -> dict:
    """복귀 직전의 이관취소 1회. **어떤 실패도 올리지 않고** 로그 dict로만 돌려준다 —
    복귀가 취소 성공에 종속되면 dual owner가 남는다(`_close_terminal`과 동형)."""
    if not task_path:
        return {"attempted": False, "reason": "task_path_missing"}
    try:
        return lease_handoff_cancel(task_path, session_id=session_id)
    except Exception as exc:  # noqa: BLE001 — 취소 실패가 복귀를 막으면 dual owner가 남는다
        return {
            "ok": False,
            "attempted": True,
            "reason": "lease_handoff_cancel_failed",
            "detail": f"{type(exc).__name__}: {exc}",
        }


def _close_terminal(adapter, report) -> dict:
    """복귀 직전의 터미널 정리 1회. **어떤 실패도 올리지 않고** 로그 dict로만 돌려준다.

    handle은 launch 보고 dict의 `adapter_handle`에서만 취한다 — 보고가 dict가 아니거나
    handle이 비면 대상을 추측하지 않고 시도 자체를 하지 않는다. 스코프는 D-C의 정밀
    `close(handle=…)` 하나이며 워크스페이스 스윕(`worktree_root`+`all`)은 회수 경로의
    것이라 여기서 쓰지 않는다(사용자의 다른 탭 보존).
    """
    handle = report.get("adapter_handle") if isinstance(report, dict) else None
    if not handle:
        return {"attempted": False, "reason": "handle_missing"}
    try:
        close = adapter.close
    except AttributeError:
        # close seam이 없는 어댑터도 복귀를 막지 않는다(덕타이핑 — 상속 계층 없음).
        return {"attempted": False, "handle": handle, "reason": "close_unsupported"}
    try:
        close_report = close(handle=handle)
    except Exception as exc:  # noqa: BLE001 — 정리 실패가 복귀를 막으면 dual owner가 남는다
        return {
            "attempted": True,
            "ok": False,
            "handle": handle,
            "reason": "close_failed",
            "detail": f"{type(exc).__name__}: {exc}",
        }
    exit_code = close_report.get("exit_code") if isinstance(close_report, dict) else None
    if exit_code in (0, None):
        return {"attempted": True, "ok": True, "handle": handle}
    return {
        "attempted": True,
        "ok": False,
        "handle": handle,
        "reason": "close_rejected",
        "detail": f"exit_code={exit_code}",
    }


def _terminal_absent(adapter, handle, worktree_root) -> dict:
    """Confirm a close without treating an unavailable adapter as absence."""
    if not handle:
        return {"status": "unknown", "reason": "handle_missing"}
    status = getattr(adapter, "status", None)
    if not callable(status):
        return {"status": "unknown", "reason": "status_unsupported"}
    try:
        observed = status(handle, worktree_root=worktree_root)
    except Exception as exc:  # adapter observation is evidence, never a guess
        return {"status": "unknown", "reason": "status_failed", "detail": str(exc)}
    return observed if isinstance(observed, dict) else {"status": "unknown", "reason": "status_invalid"}


def _lease_status(task_path, owner_session_id):
    if not task_path:
        return {"classification": "unresolved", "reason": "task_path_missing"}
    try:
        return _lease_cli("status", ["--task-path", str(task_path), "--session-id", str(owner_session_id)], "lease_status")
    except Exception as exc:
        return {"classification": "unknown", "reason": "lease_status_failed", "detail": str(exc)}


def _foreign_lease_owner(status: dict):
    if status.get("classification") != "foreign_session_owned":
        return None
    return status.get("owner_session_id") or status.get("owner") or (status.get("lease") or {}).get("owner_session_id")


def _wait_for_child_claim(task_path, owner_session_id, timeout_sec=None):
    """Bounded polling for a foreign live lease, returning the last observation."""
    if not task_path:
        status = _lease_status(task_path, owner_session_id)
        return status, None
    timeout_sec = settings.DEFAULT_LEASE_POLL_TIMEOUT_SEC if timeout_sec is None else timeout_sec
    deadline = time.monotonic() + timeout_sec
    status = _lease_status(task_path, owner_session_id)
    while not _foreign_lease_owner(status) and time.monotonic() < deadline:
        time.sleep(LEASE_POLL_INTERVAL_SEC)
        status = _lease_status(task_path, owner_session_id)
    return status, _foreign_lease_owner(status)


def _revert(
    hub_root,
    task: str,
    detail: str,
    adapter_name=None,
    *,
    adapter=None,
    report=None,
    lease_task_path=None,
    owner_session_id=None,
    cause=None,
    terminal_creation="unknown",
    handoff_started=False,
    failure_reason=FAILURE_REASON_LAUNCH_FAILED,
    launch_receipt=None,
    prompt_receipt=None,
    handoff_result=None,
    registry_worktree_root=None,
) -> dict:
    """원자 복귀 — `failure_reason=launch_failed` + `hub_owned` + attribution 키 부재 +
    generation 증가를 `ownership-set` 한 번의 교체로 담는다(owner·receipt 소거는 그쪽이
    같은 교체 안에서 수행하므로 중간 상태가 생기지 않는다).

    복귀 **직전**에 launch가 띄웠을 수 있는 터미널을 1회 정리하고, 그 결과는 `terminal_close`
    로그 필드로만 남긴다 — 복귀는 정리 성공 여부에 종속되지 않는다.

    같은 결로 `ownership-set` 복귀 호출 **앞**에서 lease 이관을 1회 취소하고, 그 결과는
    `lease_handoff_cancel` 로그 필드로만 남긴다 — 취소의 거부·예외·미구현은 전부 삼킨다."""
    # An unknown creation state must never be converted to hub ownership.
    terminal_close = {"attempted": False, "reason": "not_created"}
    terminal_status = {"status": "absent", "reason": "not_created"}
    if terminal_creation == "created":
        terminal_close = _close_terminal(adapter, report)
        handle = report.get("adapter_handle") if isinstance(report, dict) else None
        terminal_status = _terminal_absent(adapter, handle, registry_worktree_root)
    elif terminal_creation != "not_created":
        terminal_status = {"status": "unknown", "reason": "terminal_creation_unknown"}

    lease_before_cancel = _lease_status(lease_task_path, owner_session_id)
    handoff = lease_before_cancel.get("handoff") or {}
    lease_record = lease_before_cancel.get("lease") or {}
    pending_by_this_session = (
        lease_record.get("status") == "handoff" + "_pending"
        and owner_session_id in handoff.values()
    )
    lease_cancel = {"attempted": False, "reason": "handoff_not_started"}
    if handoff_started or pending_by_this_session:
        lease_cancel = _cancel_lease_handoff(lease_task_path, owner_session_id)
    lease_after = _lease_status(lease_task_path, owner_session_id)
    safe = (
        terminal_status.get("status") == "absent"
        and (terminal_creation != "created" or terminal_close.get("ok") is True)
        and (not (handoff_started or pending_by_this_session) or lease_cancel.get("ok") is True)
        and lease_after.get("ok") is True
        and lease_after.get("classification") in (
            "current_session_owned", "unowned", "lease_expired"
        )
    )
    target = EXEC_STATE_HUB_OWNED if safe else EXEC_STATE_RECOVERY_REQUIRED
    response = ownership_set(
        hub_root,
        task,
        target,
        adapter=adapter_name,
        adapter_handle=(report or {}).get("adapter_handle") if isinstance(report, dict) else None,
        launch_receipt=launch_receipt,
        prompt_receipt=prompt_receipt,
        failure_reason=failure_reason,
        terminal_creation=terminal_creation,
        observed_lease_owner=_foreign_lease_owner(lease_after),
    )
    if not response.get("ok"):
        raise LauncherError(f"ownership_revert_failed: {response}")
    block = response.get("execution_ownership") or {}
    return {
        "ok": False,
        "status": block.get("state"),
        "failure_reason": failure_reason,
        "error": None if safe else "launch_recovery_required",
        "detail": detail,
        "cause": cause,
        "adapter": adapter_name,
        "available_identity_sources": ownership_core.available_session_sources(os.environ),
        "task": task,
        "generation": block.get("generation"),
        "terminal_close": terminal_close,
        "lease_handoff_cancel": lease_cancel,
        "lease_handoff": handoff_result,
        "lease_status": lease_after,
        "terminal_status": terminal_status,
        "meta_path": response.get("meta_path"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# lifecycle
# ─────────────────────────────────────────────────────────────────────────────


def run(adapter, *, hub_root, task, worktree_root, command, owner_session_id=None,
        lease_poll_timeout_sec=None) -> dict:
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

    owner_session_id = owner_session_id or ownership_core.resolve_session_id(os.environ)
    if not owner_session_id:
        return {"ok": False, "error": "session_id_unresolved", "cause": "identity_preflight",
                "adapter": adapter_name, "available_identity_sources":
                ownership_core.available_session_sources(os.environ), "task": task}

    if meta.get("task_path"):
        lease_status = _lease_cli("status", ["--task-path", str(meta["task_path"]),
                                 "--session-id", owner_session_id], "lease_preflight")
        if lease_status.get("classification") == "foreign_session_owned":
            return {"ok": False, "error": "foreign_session_owned", "cause": "lease_preflight",
                    "task": task, "adapter": adapter_name,
                    "available_identity_sources": ownership_core.available_session_sources(os.environ)}

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

    # [MUST] 이관 대상은 registry meta 발급값에서만 취한다(C-4, D-4) — cwd·경로 문자열·
    # `.opal-worktrees` 토큰으로 구성하지 않는다. 기동 **직전**에 정확히 1회 수행한다.
    lease_task_path = meta.get("task_path")
    try:
        lease_result = _lease_handoff_for_launch(lease_task_path, registered_root, owner_session_id)
    except Exception as exc:
        lease_result = {"ok": False, "error": type(exc).__name__, "message": str(exc)}
    if not (lease_result.get("ok") or lease_result.get("noop")):
        return _revert(
            hub_root, task, "lease_handoff_failed", adapter_name,
            lease_task_path=lease_task_path, owner_session_id=owner_session_id, cause=lease_result,
            terminal_creation="not_created", handoff_started=False,
            registry_worktree_root=registered_root,
        )
    handoff_started = not lease_result.get("noop", False)

    launch_command = shlex.join([str(OWNERSHIP_TOOL_DIR / "run.sh"),
                                 "session-launch", "--command", command])
    try:
        report = adapter.launch(worktree_root, launch_command)
    except Exception as exc:
        return _revert(hub_root, task, "adapter_launch_failed", adapter_name,
                       lease_task_path=lease_task_path, owner_session_id=owner_session_id,
                       cause={"error": type(exc).__name__, "message": str(exc)},
                       terminal_creation="unknown", handoff_started=handoff_started,
                       registry_worktree_root=registered_root)
    if not isinstance(report, dict):
        return _revert(
            hub_root, task, "adapter_report_invalid", adapter_name,
            adapter=adapter, report=report, lease_task_path=lease_task_path, owner_session_id=owner_session_id,
            terminal_creation="unknown", handoff_started=handoff_started,
            registry_worktree_root=registered_root,
        )
    adapter_name = report.get("adapter") or adapter_name

    launch_receipt = build_launch_receipt(report)
    if launch_receipt is None:
        return _revert(
            hub_root, task, "launch_receipt_missing", adapter_name,
            adapter=adapter, report=report, lease_task_path=lease_task_path, owner_session_id=owner_session_id,
            terminal_creation="created" if report.get("adapter_handle") else "unknown", handoff_started=handoff_started,
            registry_worktree_root=registered_root,
        )

    # [MUST] reported_cwd가 registry worktree_root와 일치하지 않으면 전이하지 않는다.
    if os.path.realpath(str(launch_receipt["reported_cwd"])) != os.path.realpath(
        str(registered_root)
    ):
        return _revert(
            hub_root, task, "reported_cwd_mismatch", adapter_name,
            adapter=adapter, report=report, lease_task_path=lease_task_path, owner_session_id=owner_session_id,
            terminal_creation="created" if report.get("adapter_handle") else "unknown", handoff_started=handoff_started,
            registry_worktree_root=registered_root,
        )

    prompt_receipt = build_prompt_receipt(report)
    if prompt_receipt is None:
        return _revert(
            hub_root, task, "prompt_receipt_missing", adapter_name,
            adapter=adapter, report=report, lease_task_path=lease_task_path, owner_session_id=owner_session_id,
            terminal_creation="created" if report.get("adapter_handle") else "unknown", handoff_started=handoff_started,
            registry_worktree_root=registered_root,
        )

    lease_status, lease_owner = _wait_for_child_claim(
        lease_task_path, owner_session_id, lease_poll_timeout_sec
    )
    if not lease_owner:
        # The polling deadline is not a close boundary.  A claim that lands at
        # that edge is still a live child and must be atomically finalized.
        lease_status = _lease_status(lease_task_path, owner_session_id)
        lease_owner = _foreign_lease_owner(lease_status)
    if not lease_owner:
        return _revert(
            hub_root, task, "child_lease_unresolved", adapter_name,
            adapter=adapter, report=report, lease_task_path=lease_task_path,
            owner_session_id=owner_session_id, cause=lease_status,
            terminal_creation="created", handoff_started=handoff_started,
            failure_reason=FAILURE_REASON_SESSION_BOOT_TIMEOUT,
            launch_receipt=launch_receipt, prompt_receipt=prompt_receipt,
            handoff_result=lease_result,
            registry_worktree_root=registered_root,
        )

    response = ownership_set(
        hub_root,
        task,
        EXEC_STATE_WORKTREE_SESSION_OWNED,
        owner_from_lease=True,
        expected_owner=lease_owner,
        exclude_owner=owner_session_id,
        adapter=adapter_name,
        adapter_handle=launch_receipt["adapter_handle"],
        launch_receipt=launch_receipt,
        prompt_receipt=prompt_receipt,
    )
    if not response.get("ok"):
        return _revert(
            hub_root, task, f"ownership_set_rejected: {response}", adapter_name,
            adapter=adapter, report=report, lease_task_path=lease_task_path, owner_session_id=owner_session_id,
            terminal_creation="created", handoff_started=handoff_started,
            launch_receipt=launch_receipt, prompt_receipt=prompt_receipt,
            registry_worktree_root=registered_root,
        )

    owned = response.get("execution_ownership") or {}
    if not lease_owner or owned.get("owner_session_id") != lease_owner:
        raise LauncherError("ownership_postcondition_violated")
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
        "lease_handoff": lease_result,
        "meta_path": response.get("meta_path"),
    }


def recover(adapter=None, *, hub_root, task, worktree_root, owner_session_id=None) -> dict:
    """Return a saved recovery state to the hub only after fresh absence evidence."""
    meta = read_registry_meta(hub_root, str(task))
    block = meta.get("execution_ownership") or {}
    if block.get("state") != EXEC_STATE_RECOVERY_REQUIRED:
        return {"ok": False, "error": "recovery_not_required", "task": str(task)}
    registered_root = meta.get("worktree_root")
    if not registered_root or os.path.realpath(str(worktree_root)) != os.path.realpath(str(registered_root)):
        return {"ok": False, "error": "worktree_root_mismatch", "task": str(task),
                "registry_worktree_root": registered_root}
    handle = block.get("adapter_handle")
    creation = block.get("terminal_creation", "unknown")
    if adapter is None:
        return {"ok": False, "error": "recovery_terminal_unconfirmed", "task": str(task)}
    if creation == "created":
        observed = _terminal_absent(adapter, handle, worktree_root)
    else:
        sweep = getattr(adapter, "status_worktree", None)
        if not callable(sweep):
            observed = {"status": "unknown", "reason": "status_unsupported"}
        else:
            try:
                observed = sweep(worktree_root)
            except Exception as exc:
                observed = {"status": "unknown", "reason": "status_failed", "detail": str(exc)}
    if observed.get("status") != "absent":
        return {"ok": False, "error": "recovery_terminal_unconfirmed", "terminal_status": observed, "task": str(task)}
    owner_session_id = owner_session_id or ownership_core.resolve_session_id(os.environ)
    # Recovery repeats the cancellation check before looking at the lease. A
    # pending handoff is only safe after it was cancelled, or after a fresh
    # read proves there was no handoff to cancel.
    cancel = _cancel_lease_handoff(meta.get("task_path"), owner_session_id)
    lease_status = _lease_status(meta.get("task_path"), owner_session_id)
    safe_classifications = {"current_session_owned", "unowned", "lease_expired"}
    if lease_status.get("ok") is not True or lease_status.get("classification") not in safe_classifications:
        return {"ok": False, "error": "recovery_lease_unconfirmed", "lease_status": lease_status, "task": str(task)}
    handoff = lease_status.get("handoff") or {}
    lease_record = lease_status.get("lease") or {}
    handoff_remains = any(value is not None for value in handoff.values())
    pending_handoff = lease_record.get("status") == "handoff" + "_pending"
    # `not_handoff_owner` is a no-op only after the fresh observation proves
    # that no handoff state remains.  A different session's pending handoff is
    # unowned for lease classification purposes, but is not safe to erase.
    if not cancel.get("ok") and (
        cancel.get("diagnostic") != "not_handoff_owner"
        or pending_handoff
        or handoff_remains
    ):
        return {"ok": False, "error": "recovery_handoff_unconfirmed", "lease_handoff_cancel": cancel,
                "lease_status": lease_status, "task": str(task)}
    response = ownership_set(hub_root, str(task), EXEC_STATE_HUB_OWNED,
                             adapter=block.get("adapter"),
                             failure_reason=block.get("failure_reason") or FAILURE_REASON_LAUNCH_FAILED)
    if not response.get("ok"):
        raise LauncherError(f"ownership_recover_failed: {response}")
    return {"ok": True, "status": EXEC_STATE_HUB_OWNED, "task": str(task),
            "generation": (response.get("execution_ownership") or {}).get("generation"),
            "meta_path": response.get("meta_path")}
