#!/usr/bin/env python3
"""
@header {
  "module": "improve_tool",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "PM 개선 루프 결정론 집행 CLI — record/list/show 3서브명령. scope local(<project-root>/.opal/MEMORY.json 또는 과도기 MEMORY.md 존재 시 memory-tool append 위임 — md만 있어도 json 경로로 위임해 lazy 변환을 유도, 둘 다 부재 시 graceful no-op) / scope fw(~/.opal/fw-inbox 자기완결 항목 write) 2원 분기. 판단(로컬/FW 분류)은 호출자(opal-improve 스킬·CLOSE 회고 하드스텝)가 수행하고, 이 도구는 확정된 scope를 결정론적으로 집행만 한다. 모든 경로 JSON \"ok\" 계약 보장 — argparse choices/required 미사용, 수동 검증으로 graceful 에러 반환(크래시·traceback 금지).",
  "exports": ["cmd_record", "cmd_list", "cmd_show"],
  "depends": ["memory_tool"]
}

opal/tools/improve-tool/improve_tool.py — PM 개선 루프 도구 (task 058)

PLAN.md §3.1.2 (F-001) 서브명령 스펙 근거로 구현:
  record --scope {local|fw}(req) --title(req) --body --situation --source-task --project-root
  list   --scope {local|fw} --project-root
  show   --scope {local|fw} --id/--path

scope 분기 (H-2 — 분기 격리):
  - local: <project-root>/.opal/MEMORY.json 존재 시(과도기: MEMORY.md만 있어도 json 경로로
           위임 — memory-tool의 lazy 변환이 발동) memory-tool(sibling 소스 경로) append 위임
           (--type improvement --status candidate). 둘 다 부재 시 예외 없이
           {"ok":true,"scope":"local","skipped":true,"reason":"no MEMORY.json"} no-op.
           존재 판정은 `_resolve_memory_target()`(PLAN.md 078 F-008 §3.8.2)로 통합.
  - fw:    ~/.opal/fw-inbox/{YYYYMMDD-HHmmss}-{host}-{slug}.md 결정론적 write.
           환경변수 IMPROVE_FW_INBOX가 설정되어 있으면 그 경로를 최우선 사용(테스트 격리).
           frontmatter 필수키(H-8): host/project/situation/created — 전부 비어있지 않게 보장.

memory-tool 위임 경로는 배포 경로(~/.opal/tools/memory-tool)를 하드코딩하지 않고,
improve_tool.py 자신의 위치 기준 형제 디렉토리(opal/tools/memory-tool)를 가리킨다 —
소스 트리(개발)와 배포 트리(설치 후) 양쪽에서 항상 같은 트리 내 형제 경로로 resolve된다.

JSON 계약 (H-4): 모든 경로 stdout에 "ok" 키 보장. 실패는 크래시/스택트레이스 없이
{"ok":false,"error":"..."}. 잘못된 --scope 값·필수 인자 누락은 argparse의
choices=/required= 기본 크래시 대신, 커스텀 파서(_GracefulArgumentParser)가
error()를 가로채고 각 커맨드 핸들러가 수동 검증하여 graceful JSON 에러로 응답한다.

변경이력:
  v1.0 2026-07-17 초기 구현 — record/list/show 3서브명령, local(memory-tool 위임)/fw
                  (fw-inbox write) scope 분기, IMPROVE_FW_INBOX 테스트 격리 훅 (058)
  v1.1 2026-07-28 scope local 위임 경로를 MEMORY.json 단독 SSOT로 전환 — 존재 판정 3곳
                  (_record_local/cmd_list/cmd_show)을 `_resolve_memory_target()` 헬퍼로
                  통합, md만 있어도 json 경로로 위임해 memory-tool lazy 변환 유도(과도기),
                  no-op 사유 문자열 "no MEMORY.md" → "no MEMORY.json" (078)
"""

import argparse
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────────────────────

VALID_SCOPES = ("local", "fw")

TOOL_DIR = pathlib.Path(__file__).resolve().parent
# memory-tool은 improve-tool의 형제 도구 — 소스/배포 트리 어느 쪽이든 동일 구조
MEMORY_TOOL_RUN = TOOL_DIR.parent / "memory-tool" / "run.sh"

SUMMARY_LIMIT = 80

KST = timezone(timedelta(hours=9))


# ─────────────────────────────────────────────────────────────────────────────
# 응답 헬퍼 (state-tool/memory-tool ok/err 동형 — 단, error는 단순 문자열)
# ─────────────────────────────────────────────────────────────────────────────

def ok(**kwargs):
    """성공(또는 no-op) 응답 — 단일 라인 JSON, exit 0(자연 종료)."""
    print(json.dumps({"ok": True, **kwargs}, ensure_ascii=False, default=str))


def err(message, **kwargs):
    """실패 응답 — 단일 라인 JSON, exit 1. 크래시·traceback 없이 항상 graceful."""
    payload = {"ok": False, "error": message}
    payload.update(kwargs)
    print(json.dumps(payload, ensure_ascii=False, default=str))
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# argparse 크래시 방지 (S-5 — 잘못된 인자/필수 누락 시 graceful JSON, traceback 금지)
# ─────────────────────────────────────────────────────────────────────────────

class _ArgumentError(Exception):
    """_GracefulArgumentParser.error()가 raise — main()에서 잡아 JSON 에러로 변환."""


class _GracefulArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise _ArgumentError(message)


# ─────────────────────────────────────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _now_kst():
    return datetime.now(KST)


def _slugify(text, limit=40):
    """제목 → 파일명 slug. 특수문자 제거, 공백/연속기호를 '-'로."""
    text = (text or "").strip()
    slug = re.sub(r"[^\w가-힣]+", "-", text)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        slug = "improvement"
    return slug[:limit]


def _truncate_summary(text, limit=SUMMARY_LIMIT):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _resolve_fw_inbox_dir():
    """IMPROVE_FW_INBOX 환경변수 최우선(테스트 격리 훅) — 미설정 시 기본 ~/.opal/fw-inbox."""
    env_dir = os.environ.get("IMPROVE_FW_INBOX")
    if env_dir:
        return pathlib.Path(env_dir)
    return pathlib.Path(os.path.expanduser("~/.opal/fw-inbox"))


def _resolve_project_root(project_root):
    if project_root:
        return pathlib.Path(project_root)
    return pathlib.Path.cwd()


def _resolve_memory_target(proj_root_path):
    """scope local 위임 대상 결정 (PLAN.md F-008 §3.8.2 과도기 폴백).

    반환 (memory-tool --file 인자, reason):
      1) .opal/MEMORY.json 존재       → (json_path, "")
      2) .opal/MEMORY.md 존재(미변환)  → (json_path, "")  # memory-tool의 lazy 변환 유도
      3) 둘 다 부재                   → (None, "no MEMORY.json")
    """
    memory_json = proj_root_path / ".opal" / "MEMORY.json"
    memory_md = proj_root_path / ".opal" / "MEMORY.md"
    if memory_json.exists() or memory_md.exists():
        return memory_json, ""
    return None, "no MEMORY.json"


def _call_memory_tool(*args):
    """memory-tool run.sh를 subprocess로 호출 후 (ok:bool, data:dict, raw_stderr:str) 반환."""
    cmd = ["bash", str(MEMORY_TOOL_RUN)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    stdout = (result.stdout or "").strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {}
    success = (result.returncode == 0) and bool(data.get("ok"))
    return success, data, (result.stderr or "").strip()


# ─────────────────────────────────────────────────────────────────────────────
# record — scope fw
# ─────────────────────────────────────────────────────────────────────────────

def _record_fw(title, body, situation, source_task, project_root):
    fw_inbox_dir = _resolve_fw_inbox_dir()
    try:
        fw_inbox_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        err(f"failed to prepare fw-inbox directory: {e}")
        return

    host = socket.gethostname()
    proj_root_path = _resolve_project_root(project_root)
    project_name = proj_root_path.name or "unknown"
    situation_value = (situation or "").strip() or "unspecified"

    now = _now_kst()
    created = now.strftime("%Y-%m-%d %H:%M") + " KST"
    ts_compact = now.strftime("%Y%m%d-%H%M%S")
    slug = _slugify(title)
    filename = f"{ts_compact}-{host}-{slug}.md"
    file_path = fw_inbox_dir / filename

    summary_line = (body or title).strip()
    body_text = (body or "").strip() or "(본문 미기재)"

    content = (
        "---\n"
        "type: fw-improvement\n"
        f"title: {title}\n"
        f"created: {created}\n"
        f"host: {host}\n"
        f"project: {project_name}\n"
        f"project_root: {proj_root_path}\n"
        f"source_task: {source_task or ''}\n"
        f"situation: {situation_value}\n"
        "status: inbox\n"
        "---\n"
        "\n"
        "## 제안 요약\n"
        f"{summary_line}\n"
        "\n"
        "## 상황 (Context)\n"
        f"{situation_value}\n"
        "\n"
        "## 제안 내용\n"
        f"{body_text}\n"
    )

    try:
        file_path.write_text(content, encoding="utf-8")
    except OSError as e:
        err(f"failed to write fw-inbox entry: {e}")
        return

    ok(scope="fw", path=str(file_path), id=filename)


# ─────────────────────────────────────────────────────────────────────────────
# record — scope local
# ─────────────────────────────────────────────────────────────────────────────

def _record_local(title, body, situation, source_task, project_root):
    proj_root_path = _resolve_project_root(project_root)
    memory_target, reason = _resolve_memory_target(proj_root_path)

    if memory_target is None:
        # H-6 — 예외 전파 없는 graceful no-op. write 0건.
        ok(scope="local", skipped=True, reason=reason)
        return

    summary = _truncate_summary(body or title)

    try:
        success, data, raw_stderr = _call_memory_tool(
            "append",
            "--file", str(memory_target),
            "--kind", "memory",
            "--title", title,
            "--type", "improvement",
            "--status", "candidate",
            "--summary", summary,
        )
    except Exception as e:
        err(f"memory-tool delegation failed: {e}")
        return

    if not success:
        message = data.get("error") or data.get("message") or raw_stderr or "memory-tool append failed"
        err(f"memory-tool delegation failed: {message}")
        return

    ok(scope="local", delegated="memory-tool", file=str(memory_target), title=title)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_record
# ─────────────────────────────────────────────────────────────────────────────

def cmd_record(args):
    scope = args.scope
    if scope not in VALID_SCOPES:
        err(f"--scope must be one of {VALID_SCOPES!r}, got {scope!r}")
        return

    title = (args.title or "").strip()
    if not title:
        err("--title is required (non-empty)")
        return

    body = args.body or ""
    situation = args.situation or ""
    source_task = args.source_task or ""
    project_root = args.project_root

    if scope == "fw":
        _record_fw(title, body, situation, source_task, project_root)
    else:
        _record_local(title, body, situation, source_task, project_root)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_list (read-only)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_list(args):
    scope = args.scope
    if scope not in VALID_SCOPES:
        err(f"--scope must be one of {VALID_SCOPES!r}, got {scope!r}")
        return

    if scope == "fw":
        fw_inbox_dir = _resolve_fw_inbox_dir()
        items = []
        if fw_inbox_dir.exists():
            for p in sorted(fw_inbox_dir.glob("*.md")):
                items.append({"id": p.name, "path": str(p)})
        ok(scope="fw", items=items)
        return

    # scope == local
    proj_root_path = _resolve_project_root(args.project_root)
    memory_target, reason = _resolve_memory_target(proj_root_path)
    if memory_target is None:
        ok(scope="local", items=[], skipped=True, reason=reason)
        return

    try:
        success, data, raw_stderr = _call_memory_tool("show", "--file", str(memory_target))
    except Exception as e:
        err(f"memory-tool show failed: {e}")
        return

    if not success:
        message = data.get("error") or data.get("message") or raw_stderr or "memory-tool show failed"
        err(f"memory-tool show failed: {message}")
        return

    rows = [r for r in data.get("index_rows", []) if r.get("type") == "improvement"]
    ok(scope="local", items=rows)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_show (read-only)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_show(args):
    scope = args.scope
    if scope not in VALID_SCOPES:
        err(f"--scope must be one of {VALID_SCOPES!r}, got {scope!r}")
        return

    if scope == "fw":
        path_arg = args.path
        if not path_arg and args.id:
            path_arg = str(_resolve_fw_inbox_dir() / args.id)
        if not path_arg:
            err("--id or --path is required for show --scope fw")
            return
        p = pathlib.Path(path_arg)
        if not p.exists():
            err(f"fw-inbox entry not found: {p}")
            return
        ok(scope="fw", item={"path": str(p), "content": p.read_text(encoding="utf-8")})
        return

    # scope == local
    proj_root_path = _resolve_project_root(args.project_root)
    memory_target, reason = _resolve_memory_target(proj_root_path)
    if memory_target is None:
        ok(scope="local", skipped=True, reason=reason)
        return

    if not args.id:
        err("--id (title) is required for show --scope local")
        return

    try:
        success, data, raw_stderr = _call_memory_tool("show", "--file", str(memory_target))
    except Exception as e:
        err(f"memory-tool show failed: {e}")
        return

    if not success:
        message = data.get("error") or data.get("message") or raw_stderr or "memory-tool show failed"
        err(f"memory-tool show failed: {message}")
        return

    rows = [r for r in data.get("index_rows", []) if r.get("title") == args.id]
    if not rows:
        err(f"item not found: {args.id}")
        return

    ok(scope="local", item=rows[0])


# ─────────────────────────────────────────────────────────────────────────────
# argparse main
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser():
    parser = _GracefulArgumentParser(
        prog="improve_tool",
        description="OPAL improve-tool — PM 개선 루프 결정론 집행 CLI (record/list/show)",
    )
    sub = parser.add_subparsers(dest="command", help="서브명령")
    sub.required = True

    # ── record ── (의도적으로 choices=/required= 미사용 — 수동 검증으로 graceful 에러, S-5)
    p_record = sub.add_parser("record", help="개선 후보 기록 (scope local|fw 결정론 분기 집행)")
    p_record.add_argument("--scope", default=None, help="local 또는 fw")
    p_record.add_argument("--title", default=None, help="제안 제목 (필수 비공백)")
    p_record.add_argument("--body", default="", help="제안 본문")
    p_record.add_argument("--situation", default="", help="발생 맥락 유형 (예: retrospective)")
    p_record.add_argument("--source-task", dest="source_task", default="", help="태스크 번호/경로")
    p_record.add_argument("--project-root", dest="project_root", default=None, help="프로젝트 루트 경로")
    p_record.set_defaults(func=cmd_record)

    # ── list ──
    p_list = sub.add_parser("list", help="개선 후보 목록 조회 (read-only)")
    p_list.add_argument("--scope", default=None, help="local 또는 fw")
    p_list.add_argument("--project-root", dest="project_root", default=None, help="프로젝트 루트 경로 (local 시)")
    p_list.set_defaults(func=cmd_list)

    # ── show ──
    p_show = sub.add_parser("show", help="단일 개선 후보 조회 (read-only)")
    p_show.add_argument("--scope", default=None, help="local 또는 fw")
    p_show.add_argument("--id", default=None, help="식별자 (fw: 파일명 / local: title)")
    p_show.add_argument("--path", default=None, help="fw-inbox 항목 절대경로 (--id 대체)")
    p_show.add_argument("--project-root", dest="project_root", default=None, help="프로젝트 루트 경로 (local 시)")
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
