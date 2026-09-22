"""
@header {
  "module": "launcher_core",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "허브에서 워크트리 실행 세션을 띄우는 launcher 공통 lifecycle. `run(adapter, hub_root=…, task=…, worktree_root=…, command=…)`이 preflight(registry meta 조회 → 등록된 worktree_root 동치 확인 → `hub_owned`이면 `session_launching`으로 전이, 이미 `session_launching`이면 그대로 이어받아 generation을 낭비하지 않는다) → `adapter.launch(worktree_root, command)` 1회 호출 → launch receipt({adapter, adapter_handle, reported_cwd, launched_at}) 수집 → reported_cwd가 registry worktree_root와 realpath 동치인지 검사 → handoff prompt 제출 receipt({prompt_id, submitted_at}) 수집 → `worktree_session_owned` 전이 순으로 진행한다. launch 실패·prompt 실패·cwd 불일치·전이 거부 어느 경로든(`adapter_report_invalid`·`launch_receipt_missing`·`reported_cwd_mismatch`·`prompt_receipt_missing`·`ownership_set_rejected` 5경로 전건) `failure_reason=launch_failed` + `hub_owned` + attribution 키 부재 + generation 증가를 단일 교체로 담는 원자 복귀를 호출해 dual owner·orphan `session_launching`을 남기지 않는다. 복귀는 그 직전에 `adapter.close(handle=…)`를 1회 호출해 launch가 띄웠을 수 있는 터미널을 정리한다 — handle은 launch 보고 dict의 `adapter_handle`에서만 취하고 없으면 시도하지 않으며(대상 추측 금지), 스코프는 D-C의 정밀 close 하나다(워크스페이스 스윕은 회수 경로 소유). close의 예외·미구현(`AttributeError`)·비-0 exit는 전부 삼켜 반환 dict의 `terminal_close` 로그 필드로만 남기고 `ownership-set` 복귀는 반드시 수행한다 — 복귀가 정리 성공에 종속되면 dual owner가 남는다. 실행 소유권(lease) 이관은 registry 발급 `task_path`·`worktree_root`만을 대상으로 preflight 전이 직후·`adapter.launch` 직전에 `lease_handoff`를 1회 호출하고, 응답이 `ok`도 `noop`도 아니면 기동하지 않고 복귀한다(`lease_handoff_failed`). 복귀 경로는 `ownership-set` 복귀 호출 **앞**에서 `lease_handoff_cancel`을 1회 호출하며 그 결과는 `terminal_close`와 동형의 `lease_handoff_cancel` 로그 필드로만 남는다 — 취소의 예외·거부는 삼켜 복귀를 막지 않는다. lease 판정·저장·lock은 ownership-tool의 `handoff`·`handoff-cancel` CLI 계약이 소유하며 이 모듈은 얇은 subprocess 위임자일 뿐이다(사설 lease writer 금지). 상태 쓰기는 전부 worktree-tool의 `ownership-set` 계약을 subprocess로 경유하며 이 모듈은 registry 쓰기 로직·lock·원자 교체를 복제하지 않는다(사설 ownership writer 금지). registry 읽기는 인자로 받은 hub_root·task로 만든 `<hub_root>/.opal-worktrees/.meta/task_{task}.json` 1경로에서만 하고 경로 문자열·basename·mtime으로 신원을 추론하지 않는다. adapter는 호출자가 명시 선택해 주입하며 OS·터미널 종류를 추측하지 않는다. 플랫폼 고유 env 변수명은 이 도구에 두지 않는다(C-15 — ownership-tool의 claude_adapter 전용).",
  "exports": [
    "WORKTREE_TOOL_PATH", "OWNERSHIP_TOOL_DIR", "FAILURE_REASON_LAUNCH_FAILED",
    "LauncherError", "registry_meta_path", "read_registry_meta",
    "build_launch_receipt", "build_prompt_receipt", "ownership_set",
    "lease_handoff", "lease_handoff_cancel", "run"
  ],
  "depends": [
    "opal/tools/worktree-tool/worktree_tool.py(ownership-set CLI 계약)",
    "opal/tools/ownership-tool/ownership_tool/cli.py(handoff·handoff-cancel CLI 계약)"
  ]
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

# 실행 소유권(lease) 이관의 유일한 경로 — ownership-tool CLI가 소유하는 계약.
# 배치 규칙은 WORKTREE_TOOL_PATH와 동형의 형제 디렉터리다(경로 추론 없음).
OWNERSHIP_TOOL_DIR = pathlib.Path(__file__).resolve().parents[2] / "ownership-tool"

# worktree_tool.py의 동명 상수와 같은 토큰을 쓴다(값 복제일 뿐 판정 로직은 그쪽이 소유).
EXEC_STATE_HUB_OWNED = "hub_owned"
EXEC_STATE_SESSION_LAUNCHING = "session_launching"
EXEC_STATE_WORKTREE_SESSION_OWNED = "worktree_session_owned"
ATTRIBUTION_TOKEN_ACTIVE = "active"
FAILURE_REASON_LAUNCH_FAILED = "launch_failed"

LAUNCH_RECEIPT_FIELDS = ("adapter", "adapter_handle", "reported_cwd", "launched_at")
PROMPT_RECEIPT_FIELDS = ("prompt_id", "submitted_at")

OWNERSHIP_SET_TIMEOUT_SEC = 60
LEASE_TIMEOUT_SEC = 60


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


def lease_handoff(task_path, worktree_root) -> dict:
    """`ownership-tool handoff` 1회. 대상은 **registry 발급값**만 받는다(C-4, D-4)."""
    return _lease_cli(
        "handoff",
        [
            "--task-path",
            str(task_path),
            "--to-worktree-root",
            str(worktree_root),
        ],
        "lease_handoff",
    )


def lease_handoff_cancel(task_path) -> dict:
    """`ownership-tool handoff-cancel` 1회 — 이관 출발 세션만 취소할 수 있다."""
    return _lease_cli(
        "handoff-cancel", ["--task-path", str(task_path)], "lease_handoff_cancel"
    )


def _lease_handoff_for_launch(task_path, worktree_root) -> dict:
    """기동 직전 이관 1회. registry가 `task_path`를 발급하지 않은 태스크는 이관 대상 자체가
    없으므로 noop으로 통과시킨다 — 경로를 cwd·문자열로 지어내지 않는다(C-4)."""
    if not task_path:
        return {"ok": True, "noop": True, "diagnostic": "registry_task_path_missing"}
    return lease_handoff(task_path, worktree_root)


def _cancel_lease_handoff(task_path) -> dict:
    """복귀 직전의 이관취소 1회. **어떤 실패도 올리지 않고** 로그 dict로만 돌려준다 —
    복귀가 취소 성공에 종속되면 dual owner가 남는다(`_close_terminal`과 동형)."""
    if not task_path:
        return {"attempted": False, "reason": "task_path_missing"}
    try:
        return lease_handoff_cancel(task_path)
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


def _revert(
    hub_root,
    task: str,
    detail: str,
    adapter_name=None,
    *,
    adapter=None,
    report=None,
    lease_task_path=None,
) -> dict:
    """원자 복귀 — `failure_reason=launch_failed` + `hub_owned` + attribution 키 부재 +
    generation 증가를 `ownership-set` 한 번의 교체로 담는다(owner·receipt 소거는 그쪽이
    같은 교체 안에서 수행하므로 중간 상태가 생기지 않는다).

    복귀 **직전**에 launch가 띄웠을 수 있는 터미널을 1회 정리하고, 그 결과는 `terminal_close`
    로그 필드로만 남긴다 — 복귀는 정리 성공 여부에 종속되지 않는다.

    같은 결로 `ownership-set` 복귀 호출 **앞**에서 lease 이관을 1회 취소하고, 그 결과는
    `lease_handoff_cancel` 로그 필드로만 남긴다 — 취소의 거부·예외·미구현은 전부 삼킨다."""
    terminal_close = _close_terminal(adapter, report)
    lease_cancel = _cancel_lease_handoff(lease_task_path)
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
        "terminal_close": terminal_close,
        "lease_handoff_cancel": lease_cancel,
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

    # [MUST] 이관 대상은 registry meta 발급값에서만 취한다(C-4, D-4) — cwd·경로 문자열·
    # `.opal-worktrees` 토큰으로 구성하지 않는다. 기동 **직전**에 정확히 1회 수행한다.
    lease_task_path = meta.get("task_path")
    lease_result = _lease_handoff_for_launch(lease_task_path, registered_root)
    if not (lease_result.get("ok") or lease_result.get("noop")):
        return _revert(
            hub_root, task, "lease_handoff_failed", adapter_name,
            lease_task_path=lease_task_path,
        )

    report = adapter.launch(worktree_root, command)
    if not isinstance(report, dict):
        return _revert(
            hub_root, task, "adapter_report_invalid", adapter_name,
            adapter=adapter, report=report, lease_task_path=lease_task_path,
        )
    adapter_name = report.get("adapter") or adapter_name

    launch_receipt = build_launch_receipt(report)
    if launch_receipt is None:
        return _revert(
            hub_root, task, "launch_receipt_missing", adapter_name,
            adapter=adapter, report=report, lease_task_path=lease_task_path,
        )

    # [MUST] reported_cwd가 registry worktree_root와 일치하지 않으면 전이하지 않는다.
    if os.path.realpath(str(launch_receipt["reported_cwd"])) != os.path.realpath(
        str(registered_root)
    ):
        return _revert(
            hub_root, task, "reported_cwd_mismatch", adapter_name,
            adapter=adapter, report=report, lease_task_path=lease_task_path,
        )

    prompt_receipt = build_prompt_receipt(report)
    if prompt_receipt is None:
        return _revert(
            hub_root, task, "prompt_receipt_missing", adapter_name,
            adapter=adapter, report=report, lease_task_path=lease_task_path,
        )

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
        return _revert(
            hub_root, task, f"ownership_set_rejected: {response}", adapter_name,
            adapter=adapter, report=report, lease_task_path=lease_task_path,
        )

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
        "lease_handoff": lease_result,
        "meta_path": response.get("meta_path"),
    }
