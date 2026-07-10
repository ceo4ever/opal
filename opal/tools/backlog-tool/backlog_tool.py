"""
@header {
  "module": "backlog_tool",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "oppl 2-루프 오케스트레이터의 백로그(backlog.json) SSOT 관리 CLI — 7개 서브 명령(init/add-task/select-next/mark/done-check/show/update-task). state-tool 패턴(ok/err 헬퍼, date.js KST 시점, 마크다운 마커 렌더/치환, ERROR_CODES SSOT)을 복제한다. backlog.json은 state.json/test-scenario.json과 축 분리되어 상호 참조하지 않는다 (PLAN 056 §3.1.2 [MUST] D-2). BACKLOG.md는 도구가 렌더한 미러이며 손편집 금지 구조(마커 <!-- backlog:start/end -->)로 구현한다. mark/add-task/update-task는 fcntl 배타 락으로 read-modify-write를 직렬화해 동시 쓰기 무손상(H-3)을 보장한다. update-task는 056 ADD-3 — Evaluator 지적 반영 시 손편집 없이 tool-gated로 태스크 속성을 수정하는 경로(status는 갱신 불가 — mark 전용, done 태스크는 수정 거부).",
  "exports": [
    "cmd_init", "cmd_add_task", "cmd_select_next",
    "cmd_mark", "cmd_done_check", "cmd_show", "cmd_update_task"
  ]
}
"""

# PLAN 056 §3.1.4 — 표준 라이브러리만 import (신규 패키지 도입 금지, T-11 원칙 준용)
import argparse
import fcntl
import json
import os
import pathlib
import subprocess
import sys

# ─────────────────────────────────────────────────────────────────────────────
# 상수 (PLAN §3.1.2, §3.1.3)
# ─────────────────────────────────────────────────────────────────────────────

MODE_ENUM = ["interactive", "semi-agentic", "agentic"]
AREA_ENUM = ["fe", "be", "db", "공통", "통합"]
PRIORITY_ENUM = ["P0", "P1", "P2"]
STATUS_ENUM = ["pending", "in_progress", "done", "blocked"]

# 태스크 status 전이 그래프 — pending→done 직행 금지(반드시 in_progress 경유),
# done은 종결 상태(H-7 종료 판정 기준과 정합 — done 재개는 add-task로 새 슬라이스 생성)
ALLOWED_TRANSITIONS = {
    "pending":     {"in_progress", "blocked"},
    "in_progress": {"done", "blocked", "pending"},
    "blocked":     {"pending", "in_progress"},
    "done":        set(),
}

# PLAN §3.1.3 에러 코드 SSOT — 임의 변형 금지
ERROR_CODES = {
    "already_initialized":   "backlog.json이 이미 존재합니다. --force로 덮어쓰기 가능",
    "backlog_not_initialized": "backlog.json이 존재하지 않습니다. init을 먼저 실행하세요",
    "task_id_exists":        "이미 존재하는 task id: {task_id}",
    "task_not_found":        "--id {task_id}에 해당하는 태스크가 backlog.json에 없습니다",
    "invalid_status_transition": "status 전이 그래프 위반: {from_status} → {to_status}",
    "dependency_not_found":  "--depends에 지정된 태스크가 존재하지 않음: {dep_id}",
    "acceptance_invalid_json": "--acceptance 인자가 유효한 JSON 배열이 아님",
    "date_tool_failed":      "node ~/.opal/tools/date/date.js datetime 호출 실패 — 파일 변경 없음(원자성)",
    "task_path_not_found":   "<task-path> 디렉토리가 존재하지 않음: {path}",
    "no_fields_to_update":   "update-task: 갱신할 필드가 최소 1개 필요합니다 (--title/--slice/--acceptance/--area/--priority/--depends/--parallel-group 중 하나 이상)",
    "task_already_done":    "--id {task_id}는 이미 done 상태 — 수정 거부(재작업은 add-task로 새 슬라이스 생성)",
}

BACKLOG_MARKER_START = "<!-- backlog:start -->"
BACKLOG_MARKER_END = "<!-- backlog:end -->"

# ─────────────────────────────────────────────────────────────────────────────
# 응답 헬퍼 (state-tool ok()/err() 패턴 복제 → PLAN §3.1.2)
# ─────────────────────────────────────────────────────────────────────────────

def ok(command, **kwargs):
    """성공 응답 — 단일 라인 JSON, exit 0"""
    print(json.dumps({"ok": True, "command": command, **kwargs}, ensure_ascii=False, default=str))


def err(command, code, message=None, exit_code=1, **kwargs):
    """에러 응답 — 단일 라인 JSON, exit {exit_code}
    code는 ERROR_CODES 키 중 하나여야 한다 (§3.1.3 SSOT).
    추가 필드(kwargs)로 에러 컨텍스트(task_id 등)를 포함한다.
    """
    if message is None:
        template = ERROR_CODES.get(code, code)
        try:
            message = template.format(**kwargs)
        except (KeyError, IndexError):
            message = template
    payload = {"ok": False, "command": command, "error": code, "message": message}
    payload.update(kwargs)
    print(json.dumps(payload, ensure_ascii=False, default=str))
    sys.exit(exit_code)


# ─────────────────────────────────────────────────────────────────────────────
# 시점 취득 (state-tool get_kst_datetime 패턴 복제)
# ─────────────────────────────────────────────────────────────────────────────

def get_kst_datetime(command="(unknown)"):
    """node ~/.opal/tools/date/date.js datetime 호출 → KST YYYY-MM-DD HH:mm 반환
    실패 시 date_tool_failed 에러 응답 후 exit 2.
    """
    date_js = os.path.expanduser("~/.opal/tools/date/date.js")
    try:
        result = subprocess.run(
            ["node", date_js, "datetime"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0 or not result.stdout.strip():
            err(command, "date_tool_failed",
                message=f"exit={result.returncode}, stderr={result.stderr.strip()}",
                exit_code=2)
        return result.stdout.strip()
    except Exception as e:
        err(command, "date_tool_failed", message=str(e), exit_code=2)


# ─────────────────────────────────────────────────────────────────────────────
# 파일 I/O 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def resolve_task_path(task_path_str, command):
    """task-path 디렉토리 존재 검증. 미존재 시 task_path_not_found + exit 1."""
    p = pathlib.Path(task_path_str).resolve()
    if not p.is_dir():
        err(command, "task_path_not_found", path=str(p))
    return p


def backlog_json_path(task_path):
    return task_path / "backlog.json"


def backlog_md_path(task_path):
    return task_path / "BACKLOG.md"


def load_backlog_json(task_path, command):
    """backlog.json 로드(읽기 전용). 미존재 시 backlog_not_initialized + exit 1."""
    f = backlog_json_path(task_path)
    if not f.exists():
        err(command, "backlog_not_initialized")
    with open(f, encoding="utf-8") as fh:
        return json.load(fh)


def save_backlog_json(task_path, backlog):
    """backlog.json 저장 (UTF-8, 들여쓰기 2칸)."""
    f = backlog_json_path(task_path)
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(backlog, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def load_backlog_md(task_path):
    """BACKLOG.md 텍스트 반환. 없으면 None."""
    f = backlog_md_path(task_path)
    if not f.exists():
        return None
    with open(f, encoding="utf-8") as fh:
        return fh.read()


def save_backlog_md(task_path, content):
    """BACKLOG.md 저장."""
    f = backlog_md_path(task_path)
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(content)


# ─────────────────────────────────────────────────────────────────────────────
# 동시 쓰기 무손상 — fcntl 배타 락 read-modify-write (PLAN §3.1.6 TS-001b, H-3)
# ─────────────────────────────────────────────────────────────────────────────

def load_backlog_json_locked(task_path, command):
    """backlog.json을 배타적 락(LOCK_EX)으로 열어 (file-handle, backlog) 반환.
    호출자는 반드시 save_and_unlock()으로 마무리한다. 락은 프로세스 종료 시(err()의
    sys.exit 포함) OS가 자동 해제하므로 에러 경로에서 별도 unlock이 필요 없다.
    """
    f = backlog_json_path(task_path)
    if not f.exists():
        err(command, "backlog_not_initialized")
    fh = open(f, "r+", encoding="utf-8")
    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    try:
        backlog = json.load(fh)
    except Exception:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()
        raise
    return fh, backlog


def save_and_unlock(fh, backlog):
    """락을 쥔 파일 핸들에 backlog를 원자적으로 덮어쓰고 락 해제 + close."""
    fh.seek(0)
    fh.truncate()
    json.dump(backlog, fh, ensure_ascii=False, indent=2)
    fh.write("\n")
    fh.flush()
    os.fsync(fh.fileno())
    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    fh.close()


# ─────────────────────────────────────────────────────────────────────────────
# BACKLOG.md 마커 렌더/치환 (state-tool render_pipeline_table 패턴 복제)
# ─────────────────────────────────────────────────────────────────────────────

def render_backlog_table(tasks):
    """backlog.json tasks[]를 마크다운 표로 렌더 (마커 제외)."""
    lines = [
        "## 백로그",
        "",
        "> 상태값: pending / in_progress / done / blocked",
        "",
        "| ID | 제목 | 영역 | 우선순위 | 상태 | 의존 |",
        "|----|------|------|--------|------|------|",
    ]
    for t in tasks:
        depends = ", ".join(t.get("depends") or []) or "-"
        lines.append(
            f"| {t['id']} | {t['title']} | {t['area']} | {t['priority']} | {t['status']} | {depends} |"
        )
    return "\n".join(lines)


def replace_backlog_section(md_content, new_table_content):
    """BACKLOG.md 마커 영역을 new_table_content로 교체 반환.
    마커 없으면 None 반환 (호출자가 fallback 처리).
    """
    start_idx = md_content.find(BACKLOG_MARKER_START)
    end_idx = md_content.find(BACKLOG_MARKER_END)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        return None
    before = md_content[:start_idx]
    after = md_content[end_idx + len(BACKLOG_MARKER_END):]
    return f"{before}{BACKLOG_MARKER_START}\n{new_table_content}\n{BACKLOG_MARKER_END}{after}"


def _build_new_backlog_md(project_title, now_str, mode, goal, table_str):
    """신규 BACKLOG.md 템플릿 생성."""
    return f"""# BACKLOG: {project_title}

> 최종 갱신: {now_str}
> 모드: {mode}
> 목표: {goal or "(미지정)"}

{BACKLOG_MARKER_START}
{table_str}
{BACKLOG_MARKER_END}
"""


def _rerender_backlog_md(task_path, backlog, now_str):
    """add-task/mark 후 BACKLOG.md 마커 영역 재렌더. 마커 없으면 신규 템플릿으로 대체 생성."""
    table_str = render_backlog_table(backlog["tasks"])
    md = load_backlog_md(task_path)
    if md is None:
        new_md = _build_new_backlog_md(
            backlog.get("project_title"), now_str, backlog.get("mode"), backlog.get("goal"), table_str
        )
    else:
        replaced = replace_backlog_section(md, table_str)
        if replaced is None:
            new_md = md.rstrip("\n") + f"\n\n{BACKLOG_MARKER_START}\n{table_str}\n{BACKLOG_MARKER_END}\n"
        else:
            new_md = replaced
    save_backlog_md(task_path, new_md)


# ─────────────────────────────────────────────────────────────────────────────
# 6개 서브 명령 구현 (PLAN §3.1.2)
# ─────────────────────────────────────────────────────────────────────────────

# ── 1. init ──────────────────────────────────────────────────────────────────

def cmd_init(args):
    """backlog.json + BACKLOG.md 생성 (멱등)."""
    command = "init"
    task_path = resolve_task_path(args.task_path, command)

    backlog_file = backlog_json_path(task_path)
    if backlog_file.exists() and not args.force:
        err(command, "already_initialized")

    now_str = get_kst_datetime(command)

    backlog = {
        "schema_version": "1.0",
        "project_title": args.project_title,
        "mode": args.mode,
        "created_at": now_str,
        "updated_at": now_str,
        "goal": args.goal,
        "tasks": [],
    }

    # --force 사용 시 기존 created_at 보존 (state-tool init 패턴 준용)
    if backlog_file.exists() and args.force:
        try:
            old = json.loads(backlog_file.read_text(encoding="utf-8"))
            backlog["created_at"] = old.get("created_at", now_str)
            backlog["tasks"] = old.get("tasks", [])
        except Exception:
            pass

    save_backlog_json(task_path, backlog)

    table_str = render_backlog_table(backlog["tasks"])
    new_md = _build_new_backlog_md(args.project_title, now_str, args.mode, args.goal, table_str)
    save_backlog_md(task_path, new_md)

    ok(command, task_path=str(task_path), created_at=now_str)


# ── 2. add-task ───────────────────────────────────────────────────────────────

def cmd_add_task(args):
    """tasks[] 추가 + BACKLOG.md 재렌더."""
    command = "add-task"

    try:
        acceptance = json.loads(args.acceptance)
    except json.JSONDecodeError:
        err(command, "acceptance_invalid_json")
    if not isinstance(acceptance, list):
        err(command, "acceptance_invalid_json")

    depends = [d.strip() for d in args.depends.split(",") if d.strip()] if args.depends else []

    task_path = resolve_task_path(args.task_path, command)
    fh, backlog = load_backlog_json_locked(task_path, command)

    existing_ids = {t["id"] for t in backlog["tasks"]}
    if args.id in existing_ids:
        err(command, "task_id_exists", task_id=args.id)

    for dep_id in depends:
        if dep_id not in existing_ids:
            err(command, "dependency_not_found", dep_id=dep_id)

    now_str = get_kst_datetime(command)

    new_task = {
        "id": args.id,
        "title": args.title,
        "slice": args.slice,
        "acceptance_criteria": acceptance,
        "area": args.area,
        "priority": args.priority,
        "depends": depends,
        "status": "pending",
        "parallel_group": args.parallel_group,
        "created_at": now_str,
        "done_at": None,
    }

    backlog["tasks"].append(new_task)
    backlog["updated_at"] = now_str

    save_and_unlock(fh, backlog)
    _rerender_backlog_md(task_path, backlog, now_str)

    ok(command, task_id=args.id, tasks_count=len(backlog["tasks"]))


# ── 3. select-next ────────────────────────────────────────────────────────────

_PRIORITY_ORDER = {p: i for i, p in enumerate(PRIORITY_ENUM)}


def cmd_select_next(args):
    """depends 충족 + priority 최상위 pending 태스크 반환 (없으면 null)."""
    command = "select-next"
    task_path = resolve_task_path(args.task_path, command)
    backlog = load_backlog_json(task_path, command)

    done_ids = {t["id"] for t in backlog["tasks"] if t["status"] == "done"}

    candidates = []
    for t in backlog["tasks"]:
        if t["status"] != "pending":
            continue
        depends = t.get("depends") or []
        if all(dep in done_ids for dep in depends):
            candidates.append(t)

    if not candidates:
        ok(command, next_task_id=None, task=None)
        return

    candidates.sort(key=lambda t: _PRIORITY_ORDER.get(t["priority"], len(PRIORITY_ENUM)))
    chosen = candidates[0]
    ok(command, next_task_id=chosen["id"], task=chosen)


# ── 4. mark ───────────────────────────────────────────────────────────────────

def cmd_mark(args):
    """상태 전이 + done 시 done_at 기록."""
    command = "mark"
    task_path = resolve_task_path(args.task_path, command)
    fh, backlog = load_backlog_json_locked(task_path, command)

    task = None
    for t in backlog["tasks"]:
        if t["id"] == args.id:
            task = t
            break
    if task is None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()
        err(command, "task_not_found", task_id=args.id)

    from_status = task["status"]
    to_status = args.status
    if to_status != from_status and to_status not in ALLOWED_TRANSITIONS.get(from_status, set()):
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()
        err(command, "invalid_status_transition", from_status=from_status, to_status=to_status)

    now_str = get_kst_datetime(command)

    task["status"] = to_status
    if to_status == "done":
        task["done_at"] = now_str
    if args.note:
        task["note"] = args.note

    backlog["updated_at"] = now_str

    save_and_unlock(fh, backlog)
    _rerender_backlog_md(task_path, backlog, now_str)

    ok(command, task_id=args.id, status=to_status)


# ── 5b. update-task (056 ADD-3) ───────────────────────────────────────────────

# update-task가 받는 필드 이름 (status는 의도적으로 제외 — 상태 전이는 mark 전용, PLAN 056 ADD-3)
_UPDATE_TASK_FIELDS = ("title", "slice", "acceptance", "area", "priority", "depends", "parallel_group")


def cmd_update_task(args):
    """지정 필드만 tool-gated로 갱신 + BACKLOG.md 재렌더 (056 ADD-3).
    Evaluator 지적 반영 시 손편집 없이 태스크 속성을 수정하는 경로.
    status는 인자 자체가 없다(전이는 mark 전용). done 태스크는 수정 거부.
    """
    command = "update-task"

    provided = {f: getattr(args, f) for f in _UPDATE_TASK_FIELDS if getattr(args, f) is not None}
    if not provided:
        err(command, "no_fields_to_update")

    acceptance = None
    if "acceptance" in provided:
        try:
            acceptance = json.loads(args.acceptance)
        except json.JSONDecodeError:
            err(command, "acceptance_invalid_json")
        if not isinstance(acceptance, list):
            err(command, "acceptance_invalid_json")

    depends = None
    if "depends" in provided:
        depends = [d.strip() for d in args.depends.split(",") if d.strip()]

    task_path = resolve_task_path(args.task_path, command)
    fh, backlog = load_backlog_json_locked(task_path, command)

    task = None
    for t in backlog["tasks"]:
        if t["id"] == args.id:
            task = t
            break
    if task is None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()
        err(command, "task_not_found", task_id=args.id)

    if task["status"] == "done":
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()
        err(command, "task_already_done", task_id=args.id)

    if depends is not None:
        existing_ids = {t["id"] for t in backlog["tasks"]}
        for dep_id in depends:
            if dep_id not in existing_ids:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                fh.close()
                err(command, "dependency_not_found", dep_id=dep_id)

    now_str = get_kst_datetime(command)

    if "title" in provided:
        task["title"] = args.title
    if "slice" in provided:
        task["slice"] = args.slice
    if acceptance is not None:
        task["acceptance_criteria"] = acceptance
    if "area" in provided:
        task["area"] = args.area
    if "priority" in provided:
        task["priority"] = args.priority
    if depends is not None:
        task["depends"] = depends
    if "parallel_group" in provided:
        task["parallel_group"] = args.parallel_group

    backlog["updated_at"] = now_str

    save_and_unlock(fh, backlog)
    _rerender_backlog_md(task_path, backlog, now_str)

    ok(command, task_id=args.id, updated_fields=sorted(provided.keys()))


# ── 5. done-check ─────────────────────────────────────────────────────────────

def cmd_done_check(args):
    """모든 태스크 done 여부 → 종료조건 충족 판정."""
    command = "done-check"
    task_path = resolve_task_path(args.task_path, command)
    backlog = load_backlog_json(task_path, command)

    tasks = backlog["tasks"]
    remaining = [t["id"] for t in tasks if t["status"] != "done"]
    done_count = len(tasks) - len(remaining)

    ok(command,
       all_done=(len(remaining) == 0),
       remaining=remaining,
       done_count=done_count,
       total=len(tasks))


# ── 6. show ───────────────────────────────────────────────────────────────────

def cmd_show(args):
    """BACKLOG.md 렌더 또는 backlog.json raw 출력."""
    command = "show"
    task_path = resolve_task_path(args.task_path, command)
    backlog = load_backlog_json(task_path, command)
    fmt = getattr(args, "format", "md") or "md"

    if fmt == "json":
        ok(command, format="json", data=backlog)
        return

    md = load_backlog_md(task_path)
    if md is None:
        table = render_backlog_table(backlog["tasks"])
        ok(command, format="md", marker_present=False, content=table)
        return

    has_markers = (BACKLOG_MARKER_START in md and BACKLOG_MARKER_END in md)
    if not has_markers:
        table = render_backlog_table(backlog["tasks"])
        ok(command, format="md", marker_present=False, content=table)
        return

    start_idx = md.find(BACKLOG_MARKER_START) + len(BACKLOG_MARKER_START)
    end_idx = md.find(BACKLOG_MARKER_END)
    section = md[start_idx:end_idx].strip()
    ok(command, format="md", marker_present=True, content=section)


# ─────────────────────────────────────────────────────────────────────────────
# argparse 설정
# ─────────────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="backlog-tool",
        description="oppl 백로그(backlog.json) SSOT 관리 CLI (PLAN 056 §3.1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
서브 명령 (7종):
  init          backlog.json + BACKLOG.md 생성 (멱등)
  add-task      tasks[] 추가 + BACKLOG.md 재렌더
  select-next   depends 충족 + priority 최상위 pending 태스크 반환
  mark          상태 전이 (pending/in_progress/done/blocked)
  update-task   지정 필드만 tool-gated 수정 (status 불가 — mark 전용, done 태스크 거부)
  done-check    전 태스크 done 여부 → 종료조건 판정
  show          BACKLOG.md 렌더 또는 backlog.json raw 출력

호출 형식: ~/.opal/tools/backlog-tool/run.sh <command> <task-path> [options]
종료 코드: 0=ok  1=violation/not_found  2=internal_error
"""
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── init ──
    p_init = sub.add_parser("init", help="backlog.json + BACKLOG.md 생성")
    p_init.add_argument("task_path", metavar="<task-path>")
    p_init.add_argument("--project-title", required=True, dest="project_title")
    p_init.add_argument("--mode", required=True, choices=MODE_ENUM)
    p_init.add_argument("--goal")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    # ── add-task ──
    p_add = sub.add_parser("add-task", help="tasks[] 추가 + BACKLOG.md 재렌더")
    p_add.add_argument("task_path", metavar="<task-path>")
    p_add.add_argument("--id", required=True)
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--slice", required=True)
    p_add.add_argument("--acceptance", required=True, metavar="<json-array>")
    p_add.add_argument("--area", required=True, choices=AREA_ENUM)
    p_add.add_argument("--priority", required=True, choices=PRIORITY_ENUM)
    p_add.add_argument("--depends", metavar="<id1,id2,...>")
    p_add.add_argument("--parallel-group", dest="parallel_group")
    p_add.set_defaults(func=cmd_add_task)

    # ── select-next ──
    p_sel = sub.add_parser("select-next", help="depends 충족 + priority 최상위 pending 태스크 반환")
    p_sel.add_argument("task_path", metavar="<task-path>")
    p_sel.set_defaults(func=cmd_select_next)

    # ── mark ──
    p_mark = sub.add_parser("mark", help="상태 전이")
    p_mark.add_argument("task_path", metavar="<task-path>")
    p_mark.add_argument("--id", required=True)
    p_mark.add_argument("--status", required=True, choices=STATUS_ENUM)
    p_mark.add_argument("--note")
    p_mark.set_defaults(func=cmd_mark)

    # ── update-task ──
    p_upd = sub.add_parser("update-task", help="지정 필드만 tool-gated 수정 (status 불가, done 거부)")
    p_upd.add_argument("task_path", metavar="<task-path>")
    p_upd.add_argument("--id", required=True)
    p_upd.add_argument("--title")
    p_upd.add_argument("--slice")
    p_upd.add_argument("--acceptance", metavar="<json-array>")
    p_upd.add_argument("--area", choices=AREA_ENUM)
    p_upd.add_argument("--priority", choices=PRIORITY_ENUM)
    p_upd.add_argument("--depends", metavar="<id1,id2,...>")
    p_upd.add_argument("--parallel-group", dest="parallel_group")
    p_upd.set_defaults(func=cmd_update_task)

    # ── done-check ──
    p_done = sub.add_parser("done-check", help="전 태스크 done 여부 → 종료조건 판정")
    p_done.add_argument("task_path", metavar="<task-path>")
    p_done.set_defaults(func=cmd_done_check)

    # ── show ──
    p_show = sub.add_parser("show", help="BACKLOG.md 렌더 또는 backlog.json raw 출력")
    p_show.add_argument("task_path", metavar="<task-path>")
    p_show.add_argument("--format", dest="format", choices=["md", "json"], default="md")
    p_show.set_defaults(func=cmd_show)

    return parser


# ─────────────────────────────────────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
