"""
@header {
  "module": "ownership_tool.cli",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "ownership-tool 공개 CLI: status·release·handoff·handoff-cancel·codex-start는 단일 JSON을 반환하고 session-launch는 부모 신원을 제거한 환경에서 명령을 exec하여 자식 stdout/종료 코드를 보존한다. CLI 신원은 명시 --session-id 이후 core resolver, codex-start는 native adapter의 실제 신원만 사용한다. 모든 대상 경로는 절대 경로를 요구하며 lease 판정·쓰기와 payload-only 훅 처리는 기존 소유 모듈에 위임한다.",
  "exports": [
    "main",
    "build_parser"
  ],
  "depends": [
    "ownership_tool.lease",
    "ownership_tool.ownership_core",
    "ownership_tool.codex_adapter"
  ]
}
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import codex_adapter, lease, ownership_core

COMMAND = "ownership-tool"
EXIT_OK = 0
EXIT_REJECTED = 1
EXIT_USAGE = 2

_HANDOFF_FIELDS = (
    "handoff_to_worktree_root",
    "handoff_from_session_id",
    "handoff_expires_at",
)


def _emit(payload, exit_code=EXIT_OK):
    """단일 라인 JSON 1줄만 stdout에 기록하고 종료코드를 돌려준다."""
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return exit_code


def _base(subcommand, ok):
    return {"ok": bool(ok), "command": COMMAND, "subcommand": subcommand}


def _merge(payload, result):
    """lease 반환값을 최상위에 펼친다 — noop·diagnostic이 최상위 키로 관측된다."""
    for key, value in result.items():
        if key in ("ok", "command", "subcommand"):
            continue
        payload[key] = value
    return payload


class _JsonArgumentParser(argparse.ArgumentParser):
    """사용법 오류도 단일 라인 JSON으로 거부한다(argparse 기본 stderr 다중 라인 금지)."""

    def error(self, message):
        payload = _base(self.prog, False)
        payload["error"] = "invalid_usage"
        payload["message"] = message
        raise SystemExit(_emit(payload, EXIT_USAGE))


def build_parser():
    parser = _JsonArgumentParser(prog=COMMAND, add_help=False)
    parser.add_argument("--help", "-h", action="help")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    def _with_task_path(name, help_text):
        sub = subparsers.add_parser(name, help=help_text, add_help=False)
        sub.add_argument("--help", "-h", action="help")
        sub.add_argument("--task-path", required=True)
        sub.add_argument("--session-id", default=None)
        return sub

    _with_task_path("status", "lease 레코드·판정·이관 필드 조회")
    _with_task_path("release", "소유 세션의 명시 해제")
    handoff = _with_task_path("handoff", "지정 워크트리 루트 앞으로 이관 대기 전환")
    handoff.add_argument("--to-worktree-root", required=True)
    _with_task_path("handoff-cancel", "이관 대기 취소")
    start = subparsers.add_parser("codex-start", help="Codex native 신원으로 등록·claim·heartbeat")
    start.add_argument("--cwd", required=True)
    launch = subparsers.add_parser("session-launch", help="부모 신원을 제거한 새 runtime 실행")
    launch.add_argument("--command", required=True)
    return parser


def _read_record(task_path):
    """owner.json을 읽는다. 부재·손상은 예외 없이 None으로 접는다."""
    read = ownership_core.read_json(ownership_core.hub_lease_path(task_path))
    if not read["ok"]:
        return None
    data = read["data"]
    return data if isinstance(data, dict) else None


def _reject_relative(subcommand, option, value):
    """상대경로는 추론 보정 없이 거부한다(C-4). 절대경로면 None."""
    if os.path.isabs(str(value)):
        return None
    payload = _base(subcommand, False)
    payload["error"] = "path_not_absolute"
    payload["option"] = option
    payload["value"] = str(value)
    return payload


def _cmd_status(args, session_id):
    record = _read_record(args.task_path)
    classification = lease.classify(record or {}, session_id)
    payload = _base("status", True)
    payload["task_path"] = str(args.task_path)
    payload["session_id"] = session_id
    payload["classification"] = classification
    payload["lease"] = record
    payload["handoff"] = {
        field: (record or {}).get(field) for field in _HANDOFF_FIELDS
    }
    return _emit(payload)


def _cmd_release(args, session_id):
    record = _read_record(args.task_path)
    classification = lease.classify(record or {}, session_id)

    if classification == "foreign_session_owned":
        payload = _base("release", False)
        payload["error"] = "not_owner"
        payload["task_path"] = str(args.task_path)
        payload["session_id"] = session_id
        payload["owner_session_id"] = record.get("owner_session_id")
        payload["classification"] = classification
        return _emit(payload, EXIT_REJECTED)

    if classification != "current_session_owned":
        # 부재·released·이관 대기(무소유)·타 세션 만료 — 해제할 live lease가 없다.
        payload = _base("release", True)
        payload["noop"] = True
        payload["task_path"] = str(args.task_path)
        payload["session_id"] = session_id
        payload["classification"] = classification
        return _emit(payload)

    result = lease.release(args.task_path, session_id=session_id)
    payload = _base("release", result.get("ok"))
    payload["session_id"] = session_id
    payload["classification"] = classification
    _merge(payload, result)
    return _emit(payload, EXIT_OK if result.get("ok") else EXIT_REJECTED)


def _cmd_handoff(args, session_id):
    result = lease.handoff(
        args.task_path,
        session_id=session_id,
        to_worktree_root=args.to_worktree_root,
    )
    payload = _base("handoff", result.get("ok"))
    payload["session_id"] = session_id
    _merge(payload, result)
    return _emit(payload, EXIT_OK if result.get("ok") else EXIT_REJECTED)


def _cmd_handoff_cancel(args, session_id):
    result = lease.handoff_cancel(args.task_path, session_id=session_id)
    payload = _base("handoff-cancel", result.get("ok"))
    payload["session_id"] = session_id
    _merge(payload, result)
    return _emit(payload, EXIT_OK if result.get("ok") else EXIT_REJECTED)


_HANDLERS = {
    "status": _cmd_status,
    "release": _cmd_release,
    "handoff": _cmd_handoff,
    "handoff-cancel": _cmd_handoff_cancel,
}


def main(argv=None):
    try:
        args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE

    if args.subcommand == "session-launch":
        os.execve("/bin/sh", ["sh", "-c", args.command], ownership_core.session_launch_env(os.environ))
    if args.subcommand == "codex-start":
        rejection = _reject_relative(args.subcommand, "--cwd", args.cwd)
        if rejection:
            return _emit(rejection, EXIT_REJECTED)
        result = codex_adapter.start(args.cwd, os.environ)
        return _emit(_merge(_base(args.subcommand, result["ok"]), result),
                     EXIT_OK if result["ok"] else EXIT_REJECTED)

    rejection = _reject_relative(args.subcommand, "--task-path", args.task_path)
    if rejection is None and args.subcommand == "handoff":
        rejection = _reject_relative(
            args.subcommand, "--to-worktree-root", args.to_worktree_root
        )
    if rejection is not None:
        return _emit(rejection, EXIT_REJECTED)

    # ① --session-id ② 중립 해석기. 플랫폼 고유 변수명은 어댑터가 소유한다(C-5).
    session_id = args.session_id or ownership_core.resolve_session_id(os.environ, {})
    if not session_id:
        payload = _base(args.subcommand, False)
        payload["error"] = "session_id_unresolved"
        return _emit(payload, EXIT_REJECTED)

    return _HANDLERS[args.subcommand](args, session_id)


if __name__ == "__main__":
    sys.exit(main())
