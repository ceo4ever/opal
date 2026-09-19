"""
@header {
  "module": "cli",
  "layer": "interface",
  "domain": "opal-workspace",
  "description": "worktree-launcher의 CLI 표면. `launch`/`read`/`close` 3서브명령을 argparse로 노출하고 결과를 tool-output-contract의 단일 라인 JSON 하나로 stdout에 쓴다(성공 exit 0 / 실패 exit 1). `--adapter`는 **전 서브명령 필수**이며 값은 폐쇄 목록 `SUPPORTED_ADAPTERS`(현재 `orca` 1종)에서만 해석한다 — 누락은 `adapter_required`, 목록 밖은 `adapter_unsupported`로 거부하고 다른 어댑터로 자동 폴백하거나 OS·터미널을 자동 탐지하지 않는다(AC-1, D-E — 설정은 adapter를 소유하지 않고 이 인자가 단독 소유한다). `launch`는 `--project-root`·`--task`·`--worktree-root` 필수, `--agent`·`--command`·`--owner-session-id` 선택이며 어댑터 모듈을 그대로 `launcher_core.run()`에 주입한다. `--command` 미지정이면 `settings.load_launcher_settings(project_root)` + `resolve_command(settings, agent, task_path)`가 명령을 결정하고, 이때 `task_path`는 registry meta(`launcher_core.read_registry_meta`)가 발급한 canonical 값만 쓴다 — 없으면 `--worktree-root`로 대신하지 않고 `task_path_unresolved`로 거부한다(harness/worktree.md §canonical path 발급 계약, C-6: 경로를 추측하지 않는다). `read`는 `--terminal` 필수 + `--cursor`·`--limit`·`--screen` 선택, `close`는 `--terminal` 또는 `--worktree-root`+`--all` 중 **정확히 하나**만 받고 위반은 어댑터를 호출하기 전에 `close_scope_invalid`로 거부한다(`--json`은 worktree-tool 회수 스윕 호출 형태와의 호환용 no-op — 출력은 항상 JSON이다). argparse 자체 usage 오류도 exit 2 + 사람용 usage로 새지 않고 `invalid_arguments` 구조화 오류 + exit 1로 바뀐다. 어댑터 실패는 예외가 아니라 `exit_code != 0` 보고 dict이므로 그 `failure_reason`을 `error`로 싣는다(D-J). 이 모듈은 registry를 읽기만 하고 쓰지 않으며 상태 전이는 전부 `launcher_core`가 소유한다.",
  "exports": ["SUPPORTED_ADAPTERS", "build_parser", "main"],
  "depends": [
    "worktree_launcher/launcher_core.py(run·read_registry_meta·LauncherError)",
    "worktree_launcher/settings.py(load_launcher_settings·resolve_command)",
    "worktree_launcher/adapters/orca.py(launch·read·close 3동사)"
  ]
}
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys

from worktree_launcher import launcher_core, settings

TOOL_NAME = "worktree-launcher"

# 폐쇄 목록 — 어댑터 이름 → 모듈 경로. 목록에 없는 이름은 import를 시도조차 하지 않는다.
SUPPORTED_ADAPTERS = {
    "orca": "worktree_launcher.adapters.orca",
}

EXIT_OK = 0
EXIT_FAILURE = 1


# ─────────────────────────────────────────────────────────────────────────────
# 출력 — stdout에 단일 라인 JSON 객체 하나
# ─────────────────────────────────────────────────────────────────────────────


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def _fail(command: str, error: str, message=None, **extra) -> int:
    payload = {"ok": False, "command": command, "error": error}
    if message is not None:
        payload["message"] = message
    payload.update(extra)
    _emit(payload)
    return EXIT_FAILURE


def _succeed(command: str, report: dict) -> int:
    payload = {"ok": True, "command": command}
    payload.update({k: v for k, v in report.items() if k not in ("ok", "command")})
    _emit(payload)
    return EXIT_OK


# ─────────────────────────────────────────────────────────────────────────────
# argparse — usage 오류도 구조화 JSON으로 나간다
# ─────────────────────────────────────────────────────────────────────────────


class _UsageError(Exception):
    """argparse가 sys.exit(2) + 사람용 usage로 새지 않도록 잡아 되던지는 신호."""


class _Parser(argparse.ArgumentParser):
    def error(self, message):  # noqa: D102 - argparse 계약
        raise _UsageError(message)

    def exit(self, status=0, message=None):  # noqa: D102 - argparse 계약
        if status:
            raise _UsageError(message or "invalid_arguments")
        raise SystemExit(status)


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog=TOOL_NAME, add_help=False)
    subparsers = parser.add_subparsers(dest="command")

    def _with_adapter(sub):
        # 필수이지만 argparse `required`로 두지 않는다 — 누락과 목록 밖 값을 서로 다른
        # 안정 코드로 구분해 돌려주기 위해 검증은 명령 처리부가 한다.
        sub.add_argument("--adapter", default=None)
        return sub

    p_launch = _with_adapter(subparsers.add_parser("launch", add_help=False))
    p_launch.add_argument("--project-root", dest="project_root", default=None)
    p_launch.add_argument("--task", default=None)
    p_launch.add_argument("--worktree-root", dest="worktree_root", default=None)
    p_launch.add_argument("--agent", default=None)
    p_launch.add_argument("--command", dest="launch_command", default=None)
    p_launch.add_argument("--owner-session-id", dest="owner_session_id", default=None)

    p_read = _with_adapter(subparsers.add_parser("read", add_help=False))
    p_read.add_argument("--terminal", default=None)
    p_read.add_argument("--cursor", type=int, default=None)
    p_read.add_argument("--limit", type=int, default=None)
    p_read.add_argument("--screen", action="store_true")

    p_close = _with_adapter(subparsers.add_parser("close", add_help=False))
    p_close.add_argument("--terminal", default=None)
    p_close.add_argument("--worktree-root", dest="worktree_root", default=None)
    p_close.add_argument("--all", action="store_true")
    # 출력은 항상 단일 라인 JSON이다 — worktree-tool 회수 스윕이 실어 보내는 이 플래그는
    # 호출 형태 호환을 위해 받기만 하고 동작을 바꾸지 않는다.
    p_close.add_argument("--json", action="store_true")

    return parser


# ─────────────────────────────────────────────────────────────────────────────
# 어댑터 해석 — 폐쇄 목록 안에서만
# ─────────────────────────────────────────────────────────────────────────────


def _resolve_adapter(name):
    """이름 → 어댑터 모듈. 목록 밖이면 `(None, 오류 payload 필드)`를 돌려준다."""
    if not name:
        return None, ("adapter_required", {"supported": list(SUPPORTED_ADAPTERS)})
    if name not in SUPPORTED_ADAPTERS:
        return None, (
            "adapter_unsupported",
            {
                "adapter": name,
                "supported": list(SUPPORTED_ADAPTERS),
                # 다른 어댑터를 대신 시도하지 않았음을 응답이 스스로 밝힌다.
                "fallback_attempted": False,
            },
        )
    return importlib.import_module(SUPPORTED_ADAPTERS[name]), None


def _adapter_result(command: str, report) -> int:
    """어댑터 3동사 보고 dict → CLI 응답. 실패는 예외가 아니라 `exit_code != 0`이다(D-J)."""
    if not isinstance(report, dict):
        return _fail(command, "adapter_report_invalid")
    if report.get("exit_code") == 0:
        return _succeed(command, report)
    payload = {"ok": False, "command": command}
    payload.update({k: v for k, v in report.items() if k not in ("ok", "command")})
    payload["error"] = report.get("failure_reason") or "adapter_failed"
    _emit(payload)
    return EXIT_FAILURE


# ─────────────────────────────────────────────────────────────────────────────
# 서브명령
# ─────────────────────────────────────────────────────────────────────────────


def _resolve_launch_command(args) -> tuple:
    """`--command`가 있으면 그대로, 없으면 registry canonical `task_path`로 결정한다.

    canonical `task_path`를 얻지 못하면 `--worktree-root`를 대신 쓰지 않는다 —
    경로 추측 금지(harness/worktree.md §canonical path 발급 계약).
    """
    if args.launch_command:
        return args.launch_command, None

    try:
        meta = launcher_core.read_registry_meta(args.project_root, args.task)
    except launcher_core.LauncherError as exc:
        return None, ("registry_unreadable", {"message": str(exc)})

    task_path = meta.get("task_path")
    if not task_path:
        return None, (
            "task_path_unresolved",
            {
                "task": args.task,
                "message": "registry meta에 canonical task_path가 없습니다. "
                "worktree-root로 대체하지 않습니다.",
            },
        )

    resolved = settings.resolve_command(
        settings.load_launcher_settings(project_root=args.project_root),
        agent=args.agent,
        task_path=str(task_path),
    )
    return resolved, None


def _cmd_launch(adapter, args) -> int:
    missing = [
        flag
        for flag, value in (
            ("--project-root", args.project_root),
            ("--task", args.task),
            ("--worktree-root", args.worktree_root),
        )
        if not value
    ]
    if missing:
        return _fail("launch", "invalid_arguments", f"required: {' '.join(missing)}")

    command, error = _resolve_launch_command(args)
    if error is not None:
        code, extra = error
        return _fail("launch", code, **extra)

    try:
        report = launcher_core.run(
            adapter,
            hub_root=args.project_root,
            task=args.task,
            worktree_root=args.worktree_root,
            command=command,
            owner_session_id=args.owner_session_id,
        )
    except launcher_core.LauncherError as exc:
        return _fail("launch", "launcher_error", str(exc))

    if not isinstance(report, dict):
        return _fail("launch", "adapter_report_invalid")
    if report.get("ok"):
        return _succeed("launch", report)

    payload = {"ok": False, "command": "launch"}
    payload.update({k: v for k, v in report.items() if k not in ("ok", "command")})
    payload["error"] = report.get("error") or report.get("failure_reason") or "launch_failed"
    _emit(payload)
    return EXIT_FAILURE


def _cmd_read(adapter, args) -> int:
    if not args.terminal:
        return _fail("read", "terminal_required")
    report = adapter.read(
        args.terminal, cursor=args.cursor, limit=args.limit, screen=args.screen
    )
    return _adapter_result("read", report)


def _cmd_close(adapter, args) -> int:
    # 스코프는 정확히 둘이며 배타다(D-C). 위반은 어댑터를 호출하기 전에 거부한다.
    if bool(args.terminal) == bool(args.worktree_root):
        return _fail(
            "close",
            "close_scope_invalid",
            "exactly one of: --terminal | --worktree-root --all",
        )
    if args.terminal and args.all:
        return _fail(
            "close", "close_scope_invalid", "--all applies to --worktree-root scope only"
        )
    if args.worktree_root and not args.all:
        return _fail("close", "close_scope_invalid", "--worktree-root requires --all")

    if args.terminal:
        report = adapter.close(handle=args.terminal)
    else:
        report = adapter.close(worktree_root=args.worktree_root, all=True)
    return _adapter_result("close", report)


_HANDLERS = {"launch": _cmd_launch, "read": _cmd_read, "close": _cmd_close}


def main(argv=None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    except _UsageError as exc:
        return _fail(TOOL_NAME, "invalid_arguments", str(exc))

    command = getattr(args, "command", None)
    if command not in _HANDLERS:
        return _fail(
            TOOL_NAME, "invalid_arguments", "subcommand required: launch | read | close"
        )

    adapter, error = _resolve_adapter(args.adapter)
    if error is not None:
        code, extra = error
        return _fail(command, code, **extra)

    return _HANDLERS[command](adapter, args)


if __name__ == "__main__":
    raise SystemExit(main())
