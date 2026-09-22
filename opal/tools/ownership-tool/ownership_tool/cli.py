"""
@header {
  "module": "ownership_tool.cli",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "ownership-tool 공개 CLI 표면(run.sh가 위임하는 진입점). argparse 4서브명령 status·release·handoff·handoff-cancel을 제공하며 전 경로에서 stdout에 단일 라인 JSON {ok, command: 'ownership-tool', ...}만 내보낸다. status는 lease 레코드 전문·요청 세션 기준 lease.classify 결과·handoff_* 필드를 함께 돌려주고, release는 소유 세션 일치에만 해제를 수행한다 — 타 세션 소유 live lease는 not_owner 구조화 거부 + 0이 아닌 종료코드이고 레코드를 쓰지 않으며, 레코드 부재·released·만료는 noop true + 종료코드 0이다(강제 해제 표면 없음, C-3). handoff·handoff-cancel은 lease.handoff·lease.handoff_cancel에 그대로 위임한다. 세션 id는 --session-id 인자가 우선하고 없으면 ownership_core.resolve_session_id(os.environ)로 해석하며, 플랫폼 고유 환경변수명은 이 모듈에 두지 않는다(어댑터 전담, C-5). --task-path·--to-worktree-root의 상대경로는 cwd·task path 조상·워크트리 디렉터리명으로 보정하지 않고 path_not_absolute로 거부한다(worktree.md task root 계약, C-4). argparse 사용법 오류도 같은 단일 라인 JSON 계약을 따른다.",
  "exports": ["main", "build_parser"],
  "depends": ["ownership_tool.lease", "ownership_tool.ownership_core"]
}
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import lease, ownership_core

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
