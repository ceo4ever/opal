#!/usr/bin/env python3
"""
@header {
  "module": "opal_action_monitor",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "루프 액션 에이전트(opal-agent 채널) `.oppl-run/` 산출물을 파싱해 단계×축 현황판을 렌더하는 CLI — 텍스트/--json/--watch 3모드, 표준 라이브러리 전용",
  "exports": ["scan_task_folder", "render_text", "render_json", "main"],
  "depends": ["opal-loop-action-agent/AGENT.md#결과-파일-규약"]
}

opal/tools/opal-action-monitor/opal_action_monitor.py — 루프 액션 에이전트 진행 현황 모니터

`<task_folder>/.oppl-run/`을 스캔해 phase(t1/t2/g/t3/t4a/t4b) × 축(stream/sync)
현황판을 렌더한다. opal-agent·루프 액션 에이전트가 남기는 파일 계약
(events.jsonl / result.json / err.log / exitcode / prompt.txt / journal.md)만
소비하는 읽기 전용 리더다 — `.oppl-run/`에 아무 것도 쓰지 않는다.

무의존성(Python 3.10+ 표준 라이브러리만: json/argparse/pathlib/os/time/datetime/sys).

완료 마커(★): `.exitcode` 파일의 존재. `.events.jsonl`/`.result.json`의
존재/비존재로 완료를 판정하지 않는다
(opal/agents/opal-loop-action-agent/AGENT.md §결과 파일 규약 v2, [066계승][MUST]).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PHASES = ["t1", "t2", "g", "t3", "t4a", "t4b"]
SUFFIXES = ("events.jsonl", "result.json", "err.log", "exitcode", "prompt.txt")
TERMINAL_STATUSES = {"done", "failed", "error", "blocked"}
JOURNAL_TAIL_DEFAULT = 8
WATCH_INTERVAL_DEFAULT = 2
WATCH_TIMEOUT_DEFAULT = 1800


# ─── 에러 계약 ─────────────────────────────────────────────────

def _error_exit(message: str) -> None:
    print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
    sys.exit(1)


# ─── .oppl-run/ 파서 ───────────────────────────────────────────

def _latest_attempt_prefix(run_dir: Path, phase: str) -> str:
    """재시도 접미사(`.a<N>.`) 중 최대 N을 채택한 파일 접두어를 반환한다.
    접미사 파일이 없으면 base(N=1 취급) 그대로 phase를 반환한다."""
    pattern = re.compile(
        rf"^{re.escape(phase)}\.a(\d+)\.(?:{'|'.join(re.escape(s) for s in SUFFIXES)})$"
    )
    max_n = 1
    try:
        entries = list(run_dir.iterdir())
    except OSError:
        entries = []
    for p in entries:
        m = pattern.match(p.name)
        if m:
            n = int(m.group(1))
            if n > max_n:
                max_n = n
    return phase if max_n == 1 else f"{phase}.a{max_n}"


def _read_exitcode(path: Path) -> int | None:
    try:
        text = path.read_text(encoding="utf-8").strip()
        return int(text)
    except (OSError, ValueError):
        return None


def _read_json_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _summarize_event(obj: dict[str, Any]) -> dict[str, Any] | None:
    """단일 stream 이벤트에서 '최근 이벤트 요약'을 도출한다(R-NEST, H-5/H-6).
    미보장 필드는 .get()으로 방어적으로 접근하고, 알 수 없는 형태는
    generic degrade한다."""
    top_type = obj.get("type")
    if top_type == "assistant":
        message = obj.get("message") or {}
        content = message.get("content") or []
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    return {"kind": "tool_use", "name": item.get("name")}
        return {"kind": "generic", "type": "assistant"}
    if top_type == "user":
        message = obj.get("message") or {}
        content = message.get("content") or []
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    return {"kind": "tool_result"}
        return {"kind": "generic", "type": "user"}
    if top_type == "result":
        return {"kind": "result", "subtype": obj.get("subtype")}
    if top_type:
        return {"kind": "generic", "type": top_type}
    return None


def _last_result_event(lines: list[str]) -> dict[str, Any] | None:
    """비어있지 않은 마지막 `type:result` 줄을 역순 탐색해 반환한다."""
    for line in reversed(lines):
        obj = _read_json_line(line)
        if obj is not None and obj.get("type") == "result":
            return obj
    return None


def _scan_phase(run_dir: Path, journal_blocked_phases: set[str], phase: str) -> dict[str, Any]:
    prefix = _latest_attempt_prefix(run_dir, phase)
    events_path = run_dir / f"{prefix}.events.jsonl"
    result_path = run_dir / f"{prefix}.result.json"
    err_path = run_dir / f"{prefix}.err.log"
    exit_path = run_dir / f"{prefix}.exitcode"
    prompt_path = run_dir / f"{prefix}.prompt.txt"

    axis = "stream" if events_path.exists() else ("sync" if result_path.exists() else None)
    has_artifact = events_path.exists() or result_path.exists() or prompt_path.exists()
    exitcode = _read_exitcode(exit_path) if exit_path.exists() else None

    last_event: dict[str, Any] | None = None
    cost_usd: float | None = None
    session_id: str | None = None
    is_error: bool | None = None

    if axis == "stream" and events_path.exists():
        try:
            lines = events_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
        for line in reversed(lines):
            obj = _read_json_line(line)
            if obj is None:
                continue
            last_event = _summarize_event(obj)
            break
        result_obj = _last_result_event(lines)
        if result_obj is not None:
            cost_usd = result_obj.get("total_cost_usd")
            session_id = result_obj.get("session_id")
            is_error = result_obj.get("is_error")
    elif axis == "sync" and result_path.exists():
        try:
            result_obj = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            result_obj = None
        if isinstance(result_obj, dict):
            text = result_obj.get("result")
            if isinstance(text, str):
                snippet = text.strip().replace("\n", " ")
                if len(snippet) > 80:
                    snippet = snippet[:80] + "…"
                last_event = {"kind": "result_text", "text": snippet}
            cost_usd = result_obj.get("total_cost_usd")
            session_id = result_obj.get("session_id")
            is_error = result_obj.get("is_error")

    # 상태 판정(6상태, H-7) — journal blocked가 exitcode 체계 밖 신호이므로 최우선.
    if phase in journal_blocked_phases:
        status = "blocked"
    elif exitcode == 0:
        status = "done"
    elif exitcode == 1:
        status = "failed"
    elif exitcode is not None:
        status = "error"
    elif has_artifact:
        status = "running"
    else:
        status = "pending"

    # 경과: min(prompt.txt mtime, events/result 최초 mtime) → exitcode mtime(있으면) 또는 now.
    start_candidates = []
    if prompt_path.exists():
        start_candidates.append(prompt_path.stat().st_mtime)
    axis_path = events_path if axis == "stream" else result_path if axis == "sync" else None
    if axis_path is not None and axis_path.exists():
        start_candidates.append(axis_path.stat().st_mtime)
    elapsed_sec: int | None = None
    if start_candidates:
        start = min(start_candidates)
        end = exit_path.stat().st_mtime if exit_path.exists() else time.time()
        elapsed_sec = max(0, int(end - start))

    return {
        "phase": phase,
        "axis": axis,
        "status": status,
        "exitcode": exitcode,
        "elapsed_sec": elapsed_sec,
        "last_event": last_event,
        "cost_usd": cost_usd,
        "session_id": session_id,
        "is_error": is_error,
        "_has_err_log": err_path.exists(),
    }


def _parse_journal(run_dir: Path) -> list[dict[str, str]]:
    """`journal.md`의 `시각|단계|이벤트|근거` append-only 표를 파싱한다.
    형식이 어긋난 행은 건너뛴다(R-H 방어)."""
    journal_path = run_dir / "journal.md"
    if not journal_path.exists():
        return []
    try:
        text = journal_path.read_text(encoding="utf-8")
    except OSError:
        return []

    rows: list[dict[str, str]] = []
    header_seen = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not header_seen:
            if cells and cells[0] in ("시각", "시간"):
                header_seen = True
            continue
        # 구분선(---|---|...) 스킵
        if all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            continue
        if len(cells) < 4:
            continue
        rows.append({
            "time": cells[0],
            "phase": cells[1],
            "event": cells[2],
            "detail": cells[3],
        })
    return rows


def scan_task_folder(task_folder: Path) -> dict[str, Any]:
    run_dir = task_folder / ".oppl-run"
    journal_rows = _parse_journal(run_dir)
    blocked_phases = {r["phase"] for r in journal_rows if r["event"] == "blocked"}
    blocked = len(blocked_phases) > 0 or any(r["event"] == "blocked" for r in journal_rows)

    phases = [_scan_phase(run_dir, blocked_phases, phase) for phase in PHASES]

    return {
        "ok": True,
        "task_folder": str(task_folder.resolve()),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "blocked": blocked,
        "phases": phases,
        "journal_tail": journal_rows[-JOURNAL_TAIL_DEFAULT:],
    }


# ─── 렌더 ─────────────────────────────────────────────────────

def _format_elapsed(seconds: int | None) -> str:
    if seconds is None:
        return "-"
    m, s = divmod(seconds, 60)
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def _format_last_event(last_event: dict[str, Any] | None) -> str:
    if last_event is None:
        return "-"
    kind = last_event.get("kind")
    if kind == "tool_use":
        return f"tool_use: {last_event.get('name')}"
    if kind == "tool_result":
        return "tool_result"
    if kind == "result":
        return f"result({last_event.get('subtype')})"
    if kind == "result_text":
        return last_event.get("text", "-")
    if kind == "generic":
        return str(last_event.get("type"))
    return "-"


def _format_cost_session(phase_data: dict[str, Any]) -> str:
    cost = phase_data.get("cost_usd")
    session_id = phase_data.get("session_id")
    parts = []
    if cost is not None:
        parts.append(f"${cost:.4f}")
    if session_id:
        parts.append(str(session_id)[:8])
    return " / ".join(parts) if parts else "-"


def render_text(data: dict[str, Any]) -> str:
    lines = []
    lines.append(f"opal-action-monitor — {data['task_folder']}")
    lines.append(f"generated_at: {data['generated_at']}" + ("  [BLOCKED]" if data["blocked"] else ""))
    lines.append("")

    header = f"{'축':<6} {'상태':<8} {'경과':<8} {'최근 이벤트 요약':<32} {'비용/세션'}"
    lines.append(header)
    lines.append("-" * len(header))
    for p in data["phases"]:
        row = (
            f"{p['phase']:<6} {p['status']:<8} {_format_elapsed(p['elapsed_sec']):<8} "
            f"{_format_last_event(p['last_event']):<32} {_format_cost_session(p)}"
        )
        lines.append(row)

    lines.append("")
    lines.append(f"journal tail (last {JOURNAL_TAIL_DEFAULT}):")
    if not data["journal_tail"]:
        lines.append("  (없음)")
    else:
        for row in data["journal_tail"]:
            lines.append(f"  {row['time']} | {row['phase']} | {row['event']} | {row['detail']}")

    if data["blocked"]:
        lines.append("")
        lines.append("*** BLOCKED — journal.md에 blocked 이벤트 존재 ***")

    return "\n".join(lines)


def render_json(data: dict[str, Any]) -> str:
    public_phases = []
    for p in data["phases"]:
        public_phases.append({k: v for k, v in p.items() if not k.startswith("_")})
    payload = {**data, "phases": public_phases}
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ─── --watch ───────────────────────────────────────────────────

def _all_terminal(data: dict[str, Any]) -> bool:
    return all(p["status"] in TERMINAL_STATUSES for p in data["phases"])


def run_watch(task_folder: Path, interval: int, watch_timeout: int) -> None:
    start = time.monotonic()
    grace_used = False
    try:
        while True:
            data = scan_task_folder(task_folder)
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.write(render_text(data))
            sys.stdout.write("\n")
            sys.stdout.flush()

            if _all_terminal(data):
                if grace_used:
                    break
                grace_used = True
            else:
                grace_used = False

            if time.monotonic() - start >= watch_timeout:
                break

            time.sleep(interval)
    except KeyboardInterrupt:
        pass


# ─── CLI ──────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opal-action-monitor",
        description="루프 액션 에이전트(.oppl-run/) 단계×축 진행 현황판",
    )
    parser.add_argument("task_folder", help="태스크 폴더 경로 (하위 .oppl-run/ 스캔)")
    parser.add_argument("--json", action="store_true", help="JSON 스키마로 출력(1회성)")
    parser.add_argument(
        "--watch", nargs="?", const=WATCH_INTERVAL_DEFAULT, type=int, default=None,
        metavar="간격초",
        help=f"주기적으로 재렌더(기본 {WATCH_INTERVAL_DEFAULT}초 폴링). --json과 병행 불가(무시됨)",
    )
    parser.add_argument(
        "--watch-timeout", type=int, default=WATCH_TIMEOUT_DEFAULT,
        metavar="초",
        help=f"--watch 상주 상한(초), 기본 {WATCH_TIMEOUT_DEFAULT}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    task_folder = Path(args.task_folder)
    if not task_folder.is_dir():
        _error_exit(f"태스크 폴더를 찾을 수 없습니다: {task_folder}")
        return 1
    run_dir = task_folder / ".oppl-run"
    if not run_dir.is_dir():
        _error_exit(f".oppl-run/ 디렉토리가 없습니다: {run_dir}")
        return 1

    if args.json:
        data = scan_task_folder(task_folder)
        print(render_json(data))
        return 0

    if args.watch is not None:
        run_watch(task_folder, args.watch, args.watch_timeout)
        return 0

    data = scan_task_folder(task_folder)
    print(render_text(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
