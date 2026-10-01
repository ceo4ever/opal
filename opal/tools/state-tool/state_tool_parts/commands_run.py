# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool_parts.commands_run",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "state-tool 실행 서브커맨드 — test-clock·run-start·attribution·부트 브리핑·gate-pass",
  "exports": [
    "cmd_run_start",
    "cmd_finalize_attribution",
    "collect_boot_summary"
  ]
}
"""

import json
import os
import pathlib
import re
from datetime import datetime, timezone

from . import base
from .codes import (
    GATE_PATTERN,
    normalize_stored_mode,
)
from .base import (
    TS_PATTERN_MIN,
    TS_PATTERN_SEC,
    _atomic_write_state_json,
    err,
    load_state_json,
    ok,
    resolve_task_path,
    save_state_json,
)
from .journal import (
    link_memory_history,
    sync_state_md,
)


def cmd_test_clock(args):
    """Record the UTC event time of a TEST execution or human wait boundary."""
    command = "test-clock"
    task_path = resolve_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    intervals = state.get("test_timing", {}).get("intervals", [])
    active = next((item for item in intervals
                   if item["kind"] == args.kind and item["id"] == args.id
                   and item["ended_at"] is None), None)
    if args.action == "start" and active is not None:
        err(command, "test_clock_already_open", kind=args.kind, id=args.id)
    if args.action == "stop" and active is None:
        err(command, "test_clock_not_open", kind=args.kind, id=args.id)
    at = datetime.now(timezone.utc).isoformat()
    if args.action == "start":
        intervals.append({"kind": args.kind, "id": args.id,
                          "started_at": at, "ended_at": None})
    else:
        active["ended_at"] = at
    state["test_timing"] = {"intervals": intervals}
    state["updated_at"] = base.get_kst_datetime(command)
    _atomic_write_state_json(task_path, state)
    ok(command, action=args.action, kind=args.kind, id=args.id, at=at)


def _interval_union_seconds(intervals):
    """Return elapsed seconds across completed intervals, merging overlaps."""
    spans = sorted((datetime.fromisoformat(item["started_at"]),
                    datetime.fromisoformat(item["ended_at"]))
                   for item in intervals if item["ended_at"] is not None)
    if not spans:
        return None
    total = 0.0
    start, end = spans[0]
    for next_start, next_end in spans[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += (end - start).total_seconds()
            start, end = next_start, next_end
    return total + (end - start).total_seconds()


def _interval_sum_seconds(intervals):
    durations = [(datetime.fromisoformat(item["ended_at"]) -
                  datetime.fromisoformat(item["started_at"])).total_seconds()
                 for item in intervals if item["ended_at"] is not None]
    return sum(durations) if durations else None


def cmd_test_metrics(args):
    """Read only TEST timing and typed iteration counts."""
    command = "test-metrics"
    task_path = resolve_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    intervals = state.get("test_timing", {}).get("intervals", [])
    test_rows = [row for row in state["rows"] if row["stage"] == "TEST"]
    ok(command,
       auto_seconds=_interval_sum_seconds([i for i in intervals if i["kind"] == "auto"]),
       human_wait_seconds=_interval_union_seconds([i for i in intervals if i["kind"] == "human"]),
       fix_count=sum(row.get("test_change_kind") == "fix" for row in test_rows),
       requirement_change_count=sum(row.get("test_change_kind") == "requirement_change"
                                    for row in test_rows),
       legacy_unclassified_rows=sum("test_change_kind" not in row for row in test_rows),
       open_intervals=[i for i in intervals if i["ended_at"] is None])


# ── 8a. run-start (131 D8) ───────────────────────────────────────────────────

# 131 D8: run_id 형식 계약 — `run-<UTC YYYYMMDDHHMMSS>-<8자리 소문자 hex>`.
# state.schema.json properties.run_id의 pattern과 동일 문자열이어야 한다.
RUN_ID_PATTERN = re.compile(r"^run-[0-9]{14}-[0-9a-f]{8}$")


def new_run_id():
    """새 run_id 발급 — UTC 초 해상도 타임스탬프 + 8자리 hex 무작위 접미사.

    타임스탬프는 태스크 시각 표기(KST)와 달리 UTC로 고정한다(131 D8). 같은 초에
    재발급해도 hex 접미사가 id를 구분한다.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"run-{stamp}-{os.urandom(4).hex()}"


def cmd_run_start(args):
    """131 D8 — `run-start <task-path>`: 새 run_id 발급 + state.json 기록.

    현재 run은 항상 1개다. 재호출하면 기존 run_id를 새 id로 교체하며 이력을
    누적하지 않는다(run_ids/runs 같은 목록을 만들지 않는다). run_id는 optional
    필드이므로 init이 만들지 않고 이 커맨드만 생성한다.
    """
    command = "run-start"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    previous = state.get("run_id")
    run_id   = new_run_id()
    state["run_id"] = run_id
    save_state_json(task_path, state)

    ok(command, run_id=run_id, previous_run_id=previous)


# ── 8b. finalize-attribution (118 D-4b / AC-4) ───────────────────────────────

def cmd_finalize_attribution(args):
    """`finalize-attribution <task-path> --allocator-root <abs>` — 귀속 전담 커맨드.

    118 D-4b: CLOSE 마지막 행 mark에서 분리된 허브 `.opal/MEMORY.json` history
    append를 이 커맨드 하나가 전담한다. merge 확인 뒤 허브 PM이 worktree registry
    발급값(`allocator_root`)을 **명시 인자**로 넘겨 호출한다.

    [MUST] allocator_root는 추론하지 않는다 — cwd, task path의 조상,
    `.opal-worktrees` 문자열 어느 것도 근거로 쓰지 않는다. 미지정·상대경로는
    이 도구의 기존 에러 관례(err(), 단일 라인 JSON `ok:false`+`error`, exit 1)로
    거부한다(worktree.md §task root와 allocator root 계약).

    멱등: 동일 path 행이 이미 있으면 append를 건너뛰고 `duplicate_skipped`로
    응답한다(exit 0, ok:true).
    """
    command = "finalize-attribution"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    raw_root = getattr(args, "allocator_root", None)
    if raw_root is None or not str(raw_root).strip():
        err(command, "allocator_root_required")
    raw_root = str(raw_root).strip()
    if not os.path.isabs(raw_root):
        err(command, "allocator_root_not_absolute", path=raw_root)
    allocator_root = pathlib.Path(raw_root).resolve()
    if not (allocator_root / ".opal" / "MEMORY.json").is_file():
        err(command, "allocator_root_invalid", path=str(allocator_root))

    result = link_memory_history(task_path, state, allocator_root)
    status = result.get("status")
    if status not in ("created", "duplicate_skipped"):
        err(command, "finalize_attribution_failed",
            detail=str(result.get("warning") or status),
            attribution=result, allocator_root=str(allocator_root))

    ok(command, attribution=result, allocator_root=str(allocator_root),
       task_id=state.get("task_id", ""))


# ── boot summary (read-only) ─────────────────────────────────────────────────

def _boot_current_stage(state):
    """Return the stage at the current pipeline frontier.

    ``current_status`` is the task-level authority for selecting a task; rows
    provide the most useful stage signal.  Malformed rows are deliberately
    ignored so a single damaged state file cannot affect the project summary.
    """
    rows = state.get("rows")
    if not isinstance(rows, list):
        return ""
    for status in ("in_progress", "failed", "pending"):
        for row in rows:
            if isinstance(row, dict) and row.get("status") == status:
                stage = row.get("stage")
                if isinstance(stage, str) and stage:
                    return stage
    return ""


BOOT_SUMMARY_ITEM_LIMIT = 3
BOOT_SUMMARY_ANOMALY_LIMIT = 8
ACTIVE_ATTRIBUTION_STATES = {"attribution_pending", "completed_unmerged"}


def _boot_candidate(task_dir, include_mode=False):
    """Return one validated state candidate without changing its source file."""
    state_file = task_dir / "state.json"
    if not state_file.is_file() or state_file.is_symlink():
        return None
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            return None
        status = state.get("current_status")
        updated = state.get("updated_at")
        if status not in {"in_progress", "blocked"} or not isinstance(updated, str):
            return None
        if not (TS_PATTERN_MIN.match(updated) or TS_PATTERN_SEC.match(updated)):
            return None
        task_id = state.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            task_id = task_dir.name
        next_action = state.get("next_action", "")
        if not isinstance(next_action, str):
            next_action = ""
        item = {
            "title": task_id,
            "stage": _boot_current_stage(state),
            "next_action": next_action,
        }
        if include_mode:
            mode, mode_source, _mode_warnings = normalize_stored_mode(state.get("mode"))
            item.update({"mode": mode, "mode_source": mode_source})
        return updated, item
    except (OSError, UnicodeError, json.JSONDecodeError, AttributeError, TypeError):
        return None


def _boot_anomaly(code, detail=""):
    anomaly = {"code": code}
    if detail:
        anomaly["detail"] = detail
    return anomaly


def _registry_meta_files(meta_root):
    """`.meta/task_*/meta.json`만 이름순으로 반환한다.

    구 구조 파일(`.meta/task_{NNN}.json`)은 읽지도 옮기지도 않는다. 이 함수가
    이 파일 안의 유일한 경로 계산 지점이며, 모든 소비 지점은 이 함수를 거친다.
    """
    if not meta_root.is_dir():
        return []
    try:
        entries = sorted(meta_root.iterdir(), key=lambda p: p.name)
    except OSError:
        return []
    result = []
    for entry in entries:
        if not entry.is_dir() or not entry.name.startswith("task_"):
            continue
        meta_file = entry / "meta.json"
        if meta_file.is_file() and not meta_file.is_symlink():
            result.append(meta_file)
    return result


def _collect_boot_summary_details(project_root, include_mode=False):
    """Collect direct and registry-issued canonical candidates read-only."""
    root = pathlib.Path(project_root).resolve()
    direct = {}
    tasks_root = root / "tasks"
    if tasks_root.is_dir():
        try:
            entries = sorted(tasks_root.iterdir())
        except OSError:
            entries = []
        for task_dir in entries:
            if not task_dir.is_dir() or task_dir.is_symlink():
                continue
            candidate = _boot_candidate(task_dir, include_mode=include_mode)
            if candidate is not None:
                direct[task_dir.name] = candidate

    anomalies = []
    registry_rows = []
    meta_root = root / ".opal-worktrees" / ".meta"
    meta_files = _registry_meta_files(meta_root)
    required = {"task_path", "task_folder", "allocator_root"}
    for meta_file in meta_files:
        meta_label = meta_file.parent.name
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            anomalies.append(_boot_anomaly("registry_meta_corrupt", meta_label))
            continue
        if not isinstance(meta, dict) or any(
                key not in meta or not isinstance(meta[key], str) or not meta[key]
                for key in required):
            anomalies.append(_boot_anomaly("registry_meta_missing_fields", meta_label))
            continue
        attribution_state = meta.get("attribution_state")
        if "attribution_state" in meta and (
                not isinstance(attribution_state, str) or not attribution_state):
            anomalies.append(_boot_anomaly("registry_attribution_state_invalid", meta_label))
            continue
        if attribution_state == "closed":
            continue
        if (attribution_state is not None
                and attribution_state not in ACTIVE_ATTRIBUTION_STATES):
            anomalies.append(_boot_anomaly("registry_attribution_state_invalid", meta_label))
            continue
        task_folder = meta["task_folder"]
        if pathlib.PurePath(task_folder).name != task_folder or task_folder in {".", ".."}:
            anomalies.append(_boot_anomaly("registry_task_folder_invalid", meta_label))
            continue
        try:
            task_path = pathlib.Path(meta["task_path"])
            allocator_root = pathlib.Path(meta["allocator_root"])
            if not task_path.is_absolute() or not allocator_root.is_absolute():
                anomalies.append(_boot_anomaly("registry_meta_path_not_absolute", meta_label))
                continue
            if allocator_root.resolve() != root:
                anomalies.append(_boot_anomaly("registry_allocator_root_mismatch", meta_label))
                continue
            if not task_path.is_dir() or task_path.is_symlink():
                anomalies.append(_boot_anomaly("registry_task_path_missing", task_folder))
                continue
            canonical_path = task_path.resolve()
        except (OSError, RuntimeError, ValueError):
            anomalies.append(_boot_anomaly("registry_task_path_missing", task_folder))
            continue
        if canonical_path.name != task_folder:
            anomalies.append(_boot_anomaly("registry_task_path_mismatch", task_folder))
            continue
        registry_rows.append({
            "task_folder": task_folder,
            "task_path": canonical_path,
            "meta_name": meta_label,
        })

    folder_counts = {}
    path_counts = {}
    for row in registry_rows:
        folder_counts[row["task_folder"]] = folder_counts.get(row["task_folder"], 0) + 1
        path_key = str(row["task_path"])
        path_counts[path_key] = path_counts.get(path_key, 0) + 1

    candidates = []
    active_registry_folders = {row["task_folder"] for row in registry_rows}
    duplicate_folders = set()
    for row in registry_rows:
        path_key = str(row["task_path"])
        if folder_counts[row["task_folder"]] > 1 or path_counts[path_key] > 1:
            duplicate_folders.add(row["task_folder"])
            continue
        candidate = _boot_candidate(row["task_path"], include_mode=include_mode)
        if candidate is not None:
            candidates.append(candidate)

    for task_folder in sorted(duplicate_folders):
        anomalies.append(_boot_anomaly("registry_active_duplicate", task_folder))
    for task_folder in sorted(active_registry_folders.intersection(direct)):
        anomalies.append(_boot_anomaly("task_path_ambiguous", task_folder))
    for task_folder, candidate in direct.items():
        if task_folder not in active_registry_folders:
            candidates.append(candidate)

    candidates.sort(key=lambda entry: (entry[0], entry[1]["title"]), reverse=True)
    items = [entry[1] for entry in candidates[:BOOT_SUMMARY_ITEM_LIMIT]]
    return {
        "items": items,
        "other_count": max(0, len(candidates) - len(items)),
        "anomalies": anomalies[:BOOT_SUMMARY_ANOMALY_LIMIT],
    }


def collect_boot_summary(project_root):
    """Return the newest direct/canonical item using the legacy list shape."""
    return _collect_boot_summary_details(project_root, include_mode=False)["items"][:1]


def cmd_boot_summary(args):
    """Emit a bounded, read-only summary for session.project bootstrap."""
    command = "boot-summary"
    details = _collect_boot_summary_details(args.project_root, include_mode=True)
    items = details["items"]
    payload = {"ok": True, "command": command, **details}
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Keep the public result bounded even for adversarially long state fields.
    mutable = [
        (row, key)
        for row in items
        for key in ("title", "stage", "next_action", "mode", "mode_source")
        if key in row
    ] + [
        (row, "detail")
        for row in payload["anomalies"]
        if "detail" in row
    ]
    for row, key in mutable:
        limit = 120 if key != "stage" else 40
        row[key] = row[key][:limit]
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Counts, item structure, and anomaly codes are immutable while values trim.
    while len(encoded.encode("utf-8")) > 1024:
        populated = [(row, key) for row, key in mutable if row.get(key)]
        if not populated:
            break
        row, key = max(
            populated,
            key=lambda pair: len(pair[0][pair[1]].encode("utf-8")),
        )
        row[key] = row[key][:-1]
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    print(encoded)

# ── 9. gate-pass ──────────────────────────────────────────────────────────────

def cmd_gate_pass(args):
    """PLAN §2.13 G-10 — 4행 Gate 일괄 처리.

    [DEPRECATED — 014 Phase 4] 새 표준 행 구조(opds 10행)에는 "QA Gate"/"State Gate"
    행이 존재하지 않으므로 [QA Gate, State Gate, PM Gate, State Gate] 4행 패턴이 성립할 수
    없다. 신규 태스크는 gate-pass를 사용하지 않으며, PM Gate는 단일 mark로 통과한다.
    이 명령은 아직 옛 행 구조를 보유한 in-flight 레거시 state.json 하위호환을 위해서만
    유지되며, 성공 응답에 deprecated=True를 포함한다. 후속 버전에서 제거 예정.
    """
    command = "gate-pass"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    start_id = args.start
    rows     = state["rows"]

    # start_id 위치 찾기
    start_index = None
    for i, row in enumerate(rows):
        if row["row_id"] == start_id:
            start_index = i
            break
    if start_index is None:
        err(command, "row_not_found", row_id=start_id)

    # 4행 범위 확인
    if start_index + 3 >= len(rows):
        err(command, "gate_pattern_mismatch",
            message=f"rows {start_id}~{start_id+3} out of range (total rows: {len(rows)})",
            expected="QA Gate at row N")

    gate_rows = rows[start_index:start_index + 4]

    # 시작 행 검증 (§2.13 G-10 단계 1)
    if gate_rows[0]["item"] != "QA Gate":
        err(command, "gate_pattern_mismatch",
            expected=f"QA Gate at row {start_id}",
            found=gate_rows[0]["item"])

    # 연속 4행 패턴 검증 (§2.13 G-10 단계 2)
    found_pattern = [r["item"] for r in gate_rows]
    if found_pattern != GATE_PATTERN:
        err(command, "gate_pattern_mismatch",
            expected=GATE_PATTERN,
            found=found_pattern)

    # stage 일관성 검증 (§2.13 G-10 단계 3)
    stages = {r["stage"] for r in gate_rows}
    if len(stages) > 1:
        err(command, "gate_stage_mixed",
            message=f"4행 stage가 혼합됨: {list(stages)}")

    now_str = base.get_kst_datetime(command)
    stage   = gate_rows[0]["stage"]

    # 순차 ✅ 처리 (§2.13 G-10 단계 4)
    passed_ids = []
    for row in gate_rows:
        row["status"]       = "done"
        row["status_label"] = "✅"
        row["timestamp"]    = now_str
        if not row.get("owner"):
            row["owner"] = "PM"
        passed_ids.append(row["row_id"])

    state["updated_at"] = now_str
    save_state_json(task_path, state)

    # §2.17 트리거 #6
    decision = f"Gate Pass: rows {passed_ids[0]}~{passed_ids[-1]}, stage={stage}"
    reason   = args.note or "(none)"

    _jw = sync_state_md(task_path, state, now_str, command,
                        decision=decision, reason=reason)

    ok(command, rows_passed=passed_ids, stage=stage, timestamp=now_str,
       deprecated=True,
       deprecation_note="gate-pass is deprecated (014 Phase 4): new standard rows have no QA/State Gate rows; use single mark for PM Gate.",
       **(_jw or {}))
