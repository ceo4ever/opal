"""
@header {
  "module": "run_log_tool",
  "layer": "util",
  "domain": "opal-tools",
  "description": "run-log-tool CLI — init/append/validate-run/import-agentic/import-oppl 5서브명령. surfaces.json의 run-log-tool.* 표면 request_shape를 argparse로 구현하고, 인자를 §1.1 payload dict로 조립해 run_log_core만 호출한다(자체 락 획득, lock_held=False). 응답은 CONTRACT §2.1 중첩 봉투({\"ok\":true,\"data\":{...}} / {\"ok\":false,\"error\":{...}})를 그대로 stdout에 낸다 — 상태 도구의 평면 봉투와는 다른 계열이다(F-1, README.md §응답 봉투 병존 참조). --data는 CLI가 먼저 JSON 파싱해 실패 시 append를 호출하지 않고 schema_invalid를 반환한다(부분 쓰기 방지). append의 --mode(shadow|active, 선택)는 run_log_core.append()의 키워드 전용 mode 인자로 그대로 전달한다(PM 판정② — active 전용 source 제약 게이트). import-agentic/import-oppl은 --task(필수)·--run-id(선택, 생략 시 조각에서 해석)·--dry-run·--format json을 받아 run_log_core의 동명 함수를 호출한다. run_log_core 밖의 상태 원천 파일을 읽거나 쓰지 않는다(D-5, AC-19/MV-24).",
  "exports": ["cmd_init", "cmd_append", "cmd_validate_run", "cmd_import_agentic",
              "cmd_import_oppl", "build_parser", "main"]
}
"""

# TASK C-4 / T-11 관례: 표준 라이브러리만 import.
import argparse
import json
import sys

import run_log_core


def _emit(result, fmt):
    """CONTRACT §2.1 중첩 봉투를 stdout에 내고 ok 여부로 exit code를 정한다."""
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        if result.get("ok"):
            print(f"ok: {json.dumps(result.get('data', {}), ensure_ascii=False, default=str)}")
        else:
            e = result.get("error", {})
            print(f"error[{e.get('code')}]: {e.get('message')}")
    sys.exit(0 if result.get("ok") else 1)


def cmd_init(args):
    result = run_log_core.init(args.task, args.run_id)
    _emit(result, args.format)


def _build_source(args):
    if not any([args.source_kind, args.source_id, args.source_sha256,
                args.source_observed_at, args.source_locator, args.upstream_event_id]):
        return None
    return {
        "kind": args.source_kind,
        "id": args.source_id,
        "sha256": args.source_sha256,
        "observed_at": args.source_observed_at,
        "locator": args.source_locator,
        "upstream_event_id": args.upstream_event_id,
    }


def cmd_append(args):
    data_value = None
    if args.data is not None:
        try:
            data_value = json.loads(args.data)
        except json.JSONDecodeError as e:
            _emit(run_log_core.err("schema_invalid", detail=f"--data가 유효한 JSON이 아님: {e}"),
                  args.format)
            return
        if not isinstance(data_value, dict):
            _emit(run_log_core.err("schema_invalid", detail="--data는 JSON object여야 함"),
                  args.format)
            return

    event = {
        "run_id": args.run_id,
        "request_id": args.request_id,
        "event": args.event,
        "actor": {
            "kind": args.actor_kind, "id": args.actor_id,
            "provider": None, "session_id": None,
        },
        "provenance": {
            "type": args.provenance_type,
            "recorded_by": {"kind": args.recorded_by_kind, "id": args.actor_id},
            "worker_log_token_id": None,
            "source": _build_source(args),
        },
        "worker_run_id": args.worker_run_id,
        "caused_by_event_id": args.caused_by_event_id,
        "stage": args.stage,
        "task_step": args.task_step,
        "work_item": args.work_item,
        "gate_id": args.gate_id,
        "summary": args.summary,
        "reason": args.reason,
        "reason_code": args.reason_code,
        "duration_ms": args.duration_ms,
        "duration_source": args.duration_source,
        "duration_unknown_reason": args.duration_unknown_reason,
        "refs": args.refs if args.refs else None,
        "parent_run_id": None,
    }
    if data_value is not None:
        event["data"] = data_value

    result = run_log_core.append(args.task, args.run_id, event, mode=args.mode)
    _emit(result, args.format)


def cmd_validate_run(args):
    result = run_log_core.validate_run(args.task, args.run_id)
    _emit(result, args.format)


def cmd_import_agentic(args):
    result = run_log_core.import_agentic(args.task, args.run_id, dry_run=args.dry_run)
    _emit(result, args.format)


def cmd_import_oppl(args):
    result = run_log_core.import_oppl(args.task, args.run_id, dry_run=args.dry_run)
    _emit(result, args.format)


def build_parser():
    parser = argparse.ArgumentParser(prog="run-log-tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="실행 디렉터리와 첫 조각 생성 (멱등)")
    p_init.add_argument("--task", required=True, dest="task")
    p_init.add_argument("--run-id", required=True, dest="run_id")
    p_init.add_argument("--format", choices=["json"], default=None)
    p_init.set_defaults(func=cmd_init)

    p_append = sub.add_parser("append", help="표준 사건 1건 append")
    p_append.add_argument("--task", required=True, dest="task")
    p_append.add_argument("--run-id", required=True, dest="run_id")
    p_append.add_argument("--request-id", required=True, dest="request_id")
    p_append.add_argument("--event", required=True, dest="event")
    p_append.add_argument("--actor-kind", required=True, dest="actor_kind")
    p_append.add_argument("--actor-id", required=True, dest="actor_id")
    p_append.add_argument("--provenance-type", required=True, dest="provenance_type")
    p_append.add_argument("--recorded-by-kind", required=True, dest="recorded_by_kind")
    p_append.add_argument("--worker-run-id", dest="worker_run_id")
    p_append.add_argument("--source-kind", dest="source_kind")
    p_append.add_argument("--source-id", dest="source_id")
    p_append.add_argument("--source-sha256", dest="source_sha256")
    p_append.add_argument("--source-observed-at", dest="source_observed_at")
    p_append.add_argument("--source-locator", dest="source_locator")
    p_append.add_argument("--upstream-event-id", dest="upstream_event_id")
    p_append.add_argument("--stage", dest="stage")
    p_append.add_argument("--task-step", dest="task_step")
    p_append.add_argument("--work-item", dest="work_item")
    p_append.add_argument("--gate-id", dest="gate_id")
    p_append.add_argument("--caused-by-event-id", dest="caused_by_event_id")
    p_append.add_argument("--summary", dest="summary")
    p_append.add_argument("--reason", dest="reason")
    p_append.add_argument("--reason-code", dest="reason_code")
    p_append.add_argument("--duration-ms", dest="duration_ms", type=int)
    p_append.add_argument("--duration-source", dest="duration_source")
    p_append.add_argument("--duration-unknown-reason", dest="duration_unknown_reason")
    p_append.add_argument("--refs", dest="refs", nargs="*")
    p_append.add_argument("--data", dest="data")
    p_append.add_argument("--mode", dest="mode", choices=["shadow", "active"], default=None)
    p_append.add_argument("--format", choices=["json"], default=None)
    p_append.set_defaults(func=cmd_append)

    p_validate_run = sub.add_parser("validate-run", help="run 단위 무결성 검증")
    p_validate_run.add_argument("--task", required=True, dest="task")
    p_validate_run.add_argument("--run-id", required=True, dest="run_id")
    p_validate_run.add_argument("--format", choices=["json"], default=None)
    p_validate_run.set_defaults(func=cmd_validate_run)

    p_import_agentic = sub.add_parser("import-agentic", help="legacy AGENTIC-LOG.md 단방향 가져오기")
    p_import_agentic.add_argument("--task", required=True, dest="task")
    p_import_agentic.add_argument("--run-id", dest="run_id", default=None)
    p_import_agentic.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_import_agentic.add_argument("--format", choices=["json"], default=None)
    p_import_agentic.set_defaults(func=cmd_import_agentic)

    p_import_oppl = sub.add_parser("import-oppl", help="Project Loop .oppl-run/ 단방향 가져오기")
    p_import_oppl.add_argument("--task", required=True, dest="task")
    p_import_oppl.add_argument("--run-id", dest="run_id", default=None)
    p_import_oppl.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_import_oppl.add_argument("--format", choices=["json"], default=None)
    p_import_oppl.set_defaults(func=cmd_import_oppl)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
