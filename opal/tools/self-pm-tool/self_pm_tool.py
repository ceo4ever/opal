#!/usr/bin/env python3
"""
@header {
  "module": "self_pm_tool",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "opal-self-pm 경량 실행 기록 CLI — init/update/show 3서브명령. task 122 제안서 §7의 8필드(objective/status/decisions/open_questions/approved_scope/changed_files/validation/knowledge_impact) 스켈레톤을 `{task_root}/.opal/self-pm/{run_id}.json`에 결정론적으로 write/read한다. status는 폐쇄 집합(discovering/awaiting_approval/executing/awaiting_confirmation/done)만 허용. update는 status 전이뿐 아니라 6개 리스트 필드(decisions/open_questions/approved_scope/changed_files/validation/knowledge_impact)에 대해 --set-field(전체 교체)/--append-field(항목 추가)를 제공한다 — objective는 init 전용 소유. `--run-dir`로 저장 위치를 override할 수 있으나 해석된 경로가 `{task_root}` 밖이면 거부한다(경로 이탈 차단). 다른 3-SSOT 관리 파일(작업 상태·시나리오·백로그 저장소)은 절대 읽거나 쓰지 않는다(AC-10) — 이 도구는 오직 self-pm run 파일만 다룬다. 모든 경로 JSON \"ok\" 계약 보장, 크래시/traceback 없이 graceful 에러 반환.",
  "exports": ["cmd_init", "cmd_update", "cmd_show"],
  "depends": []
}

opal/tools/self-pm-tool/self_pm_tool.py — opal-self-pm 경량 기록 도구 (task 122)

PLAN.md D-8/W-3 근거로 구현 — `improve-tool`(opal/tools/improve-tool/improve_tool.py)의
CLI 골격(argparse 서브파서, graceful JSON stdout, run.sh 얇은 래퍼)을 그대로 답습한다.
새 프레임워크·의존성을 도입하지 않는다(PRINCIPLES §2 Simplicity First).

서브명령 (테스트 시나리오 S-5~S-8, opal/tools/self-pm-tool/tests/test_self_pm_tool.py
가 확정한 공개 인터페이스 계약):

  init   --task-root <path>(필수) --objective <text>(필수) [--run-id <id>] [--run-dir <path>]
         → `{task_root}/.opal/self-pm/{run_id}.json`(run_id 미지정 시 도구가 생성) 신설.
           8필드 스켈레톤을 모두 채우고 stdout에 `{"ok":true,"run_id":...}`를 보장한다.

  update --task-root <path>(필수) --run-id <id>(필수) [--status <value>]
         [--set-field <FIELD> <JSON배열>]... [--append-field <FIELD> <값>]...
         [--run-dir <path>]
         → --status/--set-field/--append-field 중 최소 하나는 있어야 한다(전부
           없으면 의미 없는 호출로 거부). --status는 폐쇄 집합 값만 허용. --set-field/
           --append-field의 FIELD는 6개 리스트 필드(decisions/open_questions/
           approved_scope/changed_files/validation/knowledge_impact)로 폐쇄 — objective는
           init 전용 소유라 update 대상이 아니다. set은 전체 교체(값은 JSON 배열이어야
           함), append는 기존 리스트 뒤에 항목 하나를 추가한다(값은 JSON으로 파싱 시도,
           실패하면 원문 문자열 그대로). 그 외 값·미지 FIELD·잘못된 타입·run 파일 8필드
           결손·run 파일 부재는 모두 `{"ok":false,...}` + exit != 0.

  show   --task-root <path>(필수) --run-id <id>(필수) [--run-dir <path>]
         → 8필드 중 하나라도 결손된 파일이면 `{"ok":false,...}` + exit != 0.

  공통 `--run-dir <path>`(선택) — run 파일이 위치한 디렉토리를 직접 지정하는 저수준
  override(기본값 `{task_root}/.opal/self-pm`). 해석된 경로가 `{task_root}` 밖이면
  경로 이탈로 거부한다(S-6(c)).

AC-10 무접촉 불변식 (S-7): 이 파일은 다른 3-SSOT 관리 파일들의 경로 문자열을 소스에
포함하지 않고, 어떤 서브명령도 그 파일들을 read/write하지 않는다.
3-SSOT 소유권 경계를 흐리지 않기 위해 조회·집계·목록 기능은 만들지 않는다(PLAN D-8).

JSON 계약: 모든 경로 stdout에 "ok" 키 보장. 실패는 크래시/스택트레이스 없이
{"ok":false,"error":"..."} + exit 1. argparse 필수 인자 누락도 커스텀 파서
(_GracefulArgumentParser)가 error()를 가로채 graceful JSON 에러로 응답한다
(improve_tool.py와 동일 패턴).

변경이력:
  v1.0 2026-09-12 초기 구현 — init/update/show 3서브명령, 8필드 스키마 검증,
                  --run-dir 경로 이탈 차단, SSOT 무접촉 (122/W-3)
  v1.1 2026-09-12 update에 --set-field/--append-field 추가 — 6개 리스트 필드 갱신
                  경로 제공(PM Gate 재지시), --status를 선택 인자로 완화하되 셋 중
                  최소 하나 필수로 무의미 호출 차단 (122/W-3)
"""

import argparse
import json
import pathlib
import sys
import uuid
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = [
    "objective", "status", "decisions", "open_questions",
    "approved_scope", "changed_files", "validation", "knowledge_impact",
]

CLOSED_STATUS_SET = (
    "discovering", "awaiting_approval", "executing",
    "awaiting_confirmation", "done",
)

# update --set-field/--append-field 대상 — 6개 리스트 필드로 폐쇄.
# objective(init 전용 소유)·status(--status 전용 경로)는 여기 포함하지 않는다.
UPDATABLE_LIST_FIELDS = (
    "decisions", "open_questions", "approved_scope",
    "changed_files", "validation", "knowledge_impact",
)

KST = timezone(timedelta(hours=9))


# ─────────────────────────────────────────────────────────────────────────────
# 응답 헬퍼 (improve-tool ok/err 동형)
# ─────────────────────────────────────────────────────────────────────────────

def ok(**kwargs):
    """성공 응답 — 단일 라인 JSON, exit 0(자연 종료)."""
    print(json.dumps({"ok": True, **kwargs}, ensure_ascii=False, default=str))


def err(message, **kwargs):
    """실패 응답 — 단일 라인 JSON, exit 1. 크래시·traceback 없이 항상 graceful."""
    payload = {"ok": False, "error": message}
    payload.update(kwargs)
    print(json.dumps(payload, ensure_ascii=False, default=str))
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# argparse 크래시 방지 (improve-tool과 동일 패턴)
# ─────────────────────────────────────────────────────────────────────────────

class _ArgumentError(Exception):
    """_GracefulArgumentParser.error()가 raise — main()에서 잡아 JSON 에러로 변환."""


class _GracefulArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise _ArgumentError(message)


# ─────────────────────────────────────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _new_run_id():
    """run_id 미지정 시 생성 — 시각(KST) + 짧은 랜덤 접미로 충돌 회피."""
    ts = datetime.now(KST).strftime("%Y%m%d-%H%M%S")
    return f"run-{ts}-{uuid.uuid4().hex[:6]}"


def _resolve_run_dir(task_root_path, run_dir_arg):
    """run 파일 저장 디렉토리를 해석하고, `{task_root}` 밖이면 거부한다(S-6(c)).

    반환: (run_dir_path, error_message). error_message가 None이 아니면 거부.
    """
    resolved_task_root = task_root_path.resolve()

    if run_dir_arg:
        candidate = pathlib.Path(run_dir_arg)
    else:
        candidate = task_root_path / ".opal" / "self-pm"

    resolved_candidate = candidate.resolve()

    if resolved_candidate != resolved_task_root:
        try:
            resolved_candidate.relative_to(resolved_task_root)
        except ValueError:
            return None, (
                f"--run-dir must resolve inside --task-root: "
                f"{resolved_candidate} is outside {resolved_task_root}"
            )

    return resolved_candidate, None


def _run_file_path(run_dir_path, run_id):
    return run_dir_path / f"{run_id}.json"


def _load_run_doc(run_file_path):
    """run 파일을 읽어 dict로 반환. 실패 시 (None, error_message)."""
    if not run_file_path.exists():
        return None, f"run file not found: {run_file_path}"
    try:
        text = run_file_path.read_text(encoding="utf-8")
    except OSError as e:
        return None, f"failed to read run file: {e}"
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        return None, f"run file is not valid JSON: {e}"
    if not isinstance(doc, dict):
        return None, "run file JSON root must be an object"
    return doc, None


def _missing_fields(doc):
    return [f for f in REQUIRED_FIELDS if f not in doc]


def _parse_set_field_value(raw_value):
    """--set-field 값 파싱 — 반드시 JSON 배열이어야 한다.

    반환: (parsed_list, error_message). error_message가 None이 아니면 거부.
    """
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return None, f"--set-field value must be valid JSON: {raw_value!r}"
    if not isinstance(parsed, list):
        return None, (
            f"--set-field value must be a JSON list, got "
            f"{type(parsed).__name__}: {raw_value!r}"
        )
    return parsed, None


def _parse_append_field_value(raw_value):
    """--append-field 값 파싱 — JSON으로 해석 가능하면 그 값을, 아니면 원문 문자열
    그대로 반환한다(자유 텍스트 항목을 JSON 따옴표 없이 넘길 수 있게)."""
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value


def _write_run_doc(run_file_path, doc):
    run_file_path.parent.mkdir(parents=True, exist_ok=True)
    run_file_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ─────────────────────────────────────────────────────────────────────────────
# cmd_init
# ─────────────────────────────────────────────────────────────────────────────

def cmd_init(args):
    task_root_raw = (args.task_root or "").strip()
    if not task_root_raw:
        err("--task-root is required (non-empty)")
        return

    objective = (args.objective or "").strip()
    if not objective:
        err("--objective is required (non-empty)")
        return

    task_root_path = pathlib.Path(task_root_raw)
    if not task_root_path.exists():
        err(f"--task-root does not exist: {task_root_path}")
        return

    run_dir_path, run_dir_error = _resolve_run_dir(task_root_path, args.run_dir)
    if run_dir_error:
        err(run_dir_error)
        return

    run_id = (args.run_id or "").strip() or _new_run_id()
    run_file_path = _run_file_path(run_dir_path, run_id)

    doc = {
        "objective": objective,
        "status": "discovering",
        "decisions": [],
        "open_questions": [],
        "approved_scope": [],
        "changed_files": [],
        "validation": [],
        "knowledge_impact": [],
    }

    try:
        _write_run_doc(run_file_path, doc)
    except OSError as e:
        err(f"failed to write run file: {e}")
        return

    ok(run_id=run_id, path=str(run_file_path))


# ─────────────────────────────────────────────────────────────────────────────
# cmd_update
# ─────────────────────────────────────────────────────────────────────────────

def cmd_update(args):
    task_root_raw = (args.task_root or "").strip()
    if not task_root_raw:
        err("--task-root is required (non-empty)")
        return

    run_id = (args.run_id or "").strip()
    if not run_id:
        err("--run-id is required (non-empty)")
        return

    status_raw = args.status
    set_fields_raw = args.set_fields or []
    append_fields_raw = args.append_fields or []

    if status_raw is None and not set_fields_raw and not append_fields_raw:
        err("at least one of --status/--set-field/--append-field is required")
        return

    status = None
    if status_raw is not None:
        status = status_raw.strip()
        if status not in CLOSED_STATUS_SET:
            err(
                f"--status must be one of {list(CLOSED_STATUS_SET)!r}, got {status!r}"
            )
            return

    # 대상 필드·값 전부를 파일을 건드리기 전에 검증한다(원자적 적용 — 부분 반영 없음).
    parsed_sets = []
    for field, raw_value in set_fields_raw:
        if field not in UPDATABLE_LIST_FIELDS:
            err(
                f"--set-field target must be one of {list(UPDATABLE_LIST_FIELDS)!r}, "
                f"got {field!r}"
            )
            return
        parsed_value, parse_error = _parse_set_field_value(raw_value)
        if parse_error:
            err(parse_error)
            return
        parsed_sets.append((field, parsed_value))

    parsed_appends = []
    for field, raw_value in append_fields_raw:
        if field not in UPDATABLE_LIST_FIELDS:
            err(
                f"--append-field target must be one of {list(UPDATABLE_LIST_FIELDS)!r}, "
                f"got {field!r}"
            )
            return
        parsed_appends.append((field, _parse_append_field_value(raw_value)))

    task_root_path = pathlib.Path(task_root_raw)
    if not task_root_path.exists():
        err(f"--task-root does not exist: {task_root_path}")
        return

    run_dir_path, run_dir_error = _resolve_run_dir(task_root_path, args.run_dir)
    if run_dir_error:
        err(run_dir_error)
        return

    run_file_path = _run_file_path(run_dir_path, run_id)
    doc, load_error = _load_run_doc(run_file_path)
    if load_error:
        err(load_error)
        return

    missing = _missing_fields(doc)
    if missing:
        err(f"run file missing required fields: {missing}")
        return

    # set 먼저(전체 교체) 적용한 뒤 append(항목 추가) — 같은 필드를 한 호출에서
    # set+append 둘 다 지정하면 "교체 후 추가"로 결정론적 처리.
    for field, value in parsed_sets:
        doc[field] = value

    for field, value in parsed_appends:
        if not isinstance(doc.get(field), list):
            err(f"cannot append to non-list field: {field!r}")
            return
        doc[field].append(value)

    if status is not None:
        doc["status"] = status

    try:
        _write_run_doc(run_file_path, doc)
    except OSError as e:
        err(f"failed to write run file: {e}")
        return

    ok(run_id=run_id, status=doc.get("status"), path=str(run_file_path))


# ─────────────────────────────────────────────────────────────────────────────
# cmd_show (read-only)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_show(args):
    task_root_raw = (args.task_root or "").strip()
    if not task_root_raw:
        err("--task-root is required (non-empty)")
        return

    run_id = (args.run_id or "").strip()
    if not run_id:
        err("--run-id is required (non-empty)")
        return

    task_root_path = pathlib.Path(task_root_raw)
    if not task_root_path.exists():
        err(f"--task-root does not exist: {task_root_path}")
        return

    run_dir_path, run_dir_error = _resolve_run_dir(task_root_path, args.run_dir)
    if run_dir_error:
        err(run_dir_error)
        return

    run_file_path = _run_file_path(run_dir_path, run_id)
    doc, load_error = _load_run_doc(run_file_path)
    if load_error:
        err(load_error)
        return

    missing = _missing_fields(doc)
    if missing:
        err(f"run file missing required fields: {missing}")
        return

    ok(run_id=run_id, doc=doc, path=str(run_file_path))


# ─────────────────────────────────────────────────────────────────────────────
# argparse main
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser():
    parser = _GracefulArgumentParser(
        prog="self_pm_tool",
        description="OPAL self-pm-tool — opal-self-pm 경량 실행 기록 CLI (init/update/show)",
    )
    sub = parser.add_subparsers(dest="command", help="서브명령")
    sub.required = True

    # ── init ── (의도적으로 choices=/required= 미사용 — 수동 검증으로 graceful 에러)
    p_init = sub.add_parser("init", help="run 파일 신설 (8필드 스켈레톤)")
    p_init.add_argument("--task-root", dest="task_root", default=None, help="태스크 루트 경로 (필수)")
    p_init.add_argument("--objective", default=None, help="run 목표 (필수 비공백)")
    p_init.add_argument("--run-id", dest="run_id", default=None, help="run 식별자 (미지정 시 생성)")
    p_init.add_argument("--run-dir", dest="run_dir", default=None, help="run 파일 저장 디렉토리 override")
    p_init.set_defaults(func=cmd_init)

    # ── update ──
    p_update = sub.add_parser("update", help="run 파일 status 전이 및/또는 리스트 필드 갱신")
    p_update.add_argument("--task-root", dest="task_root", default=None, help="태스크 루트 경로 (필수)")
    p_update.add_argument("--run-id", dest="run_id", default=None, help="run 식별자 (필수)")
    p_update.add_argument(
        "--status", default=None,
        help="폐쇄 집합 status 값 (선택 — --set-field/--append-field 중 하나 이상과 병행 가능)",
    )
    p_update.add_argument(
        "--set-field", dest="set_fields", nargs=2, action="append", default=None,
        metavar=("FIELD", "JSON_LIST"),
        help="리스트 필드 전체 교체 — FIELD는 6개 리스트 필드 중 하나, 값은 JSON 배열 (반복 가능)",
    )
    p_update.add_argument(
        "--append-field", dest="append_fields", nargs=2, action="append", default=None,
        metavar=("FIELD", "VALUE"),
        help="리스트 필드에 항목 하나 추가 — VALUE는 JSON 파싱 시도 후 실패 시 원문 문자열 (반복 가능)",
    )
    p_update.add_argument("--run-dir", dest="run_dir", default=None, help="run 파일 저장 디렉토리 override")
    p_update.set_defaults(func=cmd_update)

    # ── show ──
    p_show = sub.add_parser("show", help="run 파일 조회 (read-only)")
    p_show.add_argument("--task-root", dest="task_root", default=None, help="태스크 루트 경로 (필수)")
    p_show.add_argument("--run-id", dest="run_id", default=None, help="run 식별자 (필수)")
    p_show.add_argument("--run-dir", dest="run_dir", default=None, help="run 파일 저장 디렉토리 override")
    p_show.set_defaults(func=cmd_show)

    return parser


def main():
    parser = _build_parser()
    try:
        args = parser.parse_args()
    except _ArgumentError as e:
        err(f"argument error: {e}")
        return

    try:
        args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        err(f"unexpected error: {e}")


if __name__ == "__main__":
    main()
