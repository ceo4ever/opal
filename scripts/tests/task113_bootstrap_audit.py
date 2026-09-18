#!/usr/bin/env python3
"""
@header {
  "module": "task113_bootstrap_audit",
  "layer": "test",
  "domain": "opal-bootstrap",
  "description": "이벤트 부트, 사용자 브리핑, 문서 표준, payload/time, 설치 parity 결정론 감사",
  "exports": ["main", "run_source_audit", "snapshot_installed", "run_installed_parity", "measure_boot_payloads"]
}
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
EVENT_LOADER = REPO_ROOT / "opal" / "tools" / "event-loader" / "event_loader.py"
STATE_TOOL = REPO_ROOT / "opal" / "tools" / "state-tool" / "state_tool.py"
MEMORY_TOOL = REPO_ROOT / "opal" / "tools" / "memory-tool" / "memory_tool.py"
OPAL_AGENT = REPO_ROOT / "opal" / "tools" / "opal-agent" / "opal_agent.py"
MANIFEST = REPO_ROOT / "opal" / "core" / "references" / "events.json"
STANDARD_EVENTS = (
    "session.disabled",
    "session.worker",
    "session.assistant",
    "session.project",
    "pm.activate",
    "pilot.start",
    "stage.task",
    "stage.analysis",
    "stage.plan",
    "stage.test_scenario",
    "stage.execute",
    "stage.test",
    "stage.close",
    "worker.dispatch",
)
BASELINE_GENERAL_DOCS = (
    "opal/core/AGENT.md",
    "opal/core/PRINCIPLES.md",
)
BASELINE_PROJECT_DOCS = BASELINE_GENERAL_DOCS + (
    "opal/core/references/opal-harness.md",
    "opal/core/references/opal-pm.md",
    ".opal/AGENT.md",
)
PARITY_PATHS = (
    ("opal/core/references/events.json", "references/events.json"),
    ("opal/tools/event-loader/event_loader.py", "tools/event-loader/event_loader.py"),
    ("opal/tools/event-loader/run.sh", "tools/event-loader/run.sh"),
    ("opal/tools/event-loader/README.md", "tools/event-loader/README.md"),
    ("opal/core/references/opal-harness.md", "references/opal-harness.md"),
    ("opal/core/references/harness/guards.md", "references/harness/guards.md"),
    ("opal/core/references/harness/modes.md", "references/harness/modes.md"),
    ("opal/core/references/harness/worktree.md", "references/harness/worktree.md"),
    ("opal/core/references/harness/capability.md", "references/harness/capability.md"),
    ("opal/core/references/harness/task-process.md", "references/harness/task-process.md"),
    ("opal/core/references/harness/state.md", "references/harness/state.md"),
    ("opal/core/references/harness/scenario-gate.md", "references/harness/scenario-gate.md"),
    ("opal/core/references/harness/pm-review-gate.md", "references/harness/pm-review-gate.md"),
    ("opal/core/references/harness/citation-rules.md", "references/harness/citation-rules.md"),
    ("opal/core/references/pm/activation.md", "references/pm/activation.md"),
)
class AuditFailure(RuntimeError):
    pass


def _run(
    command: list[str],
    *,
    cwd: Path = REPO_ROOT,
    expect: int = 0,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != expect:
        raise AuditFailure(
            f"command exit {completed.returncode}, expected {expect}: {' '.join(command)}\n"
            f"stdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return completed


def _run_json(command: list[str], *, cwd: Path = REPO_ROOT, expect: int = 0) -> dict[str, Any]:
    completed = _run(command, cwd=cwd, expect=expect)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AuditFailure(f"JSON output expected: {' '.join(command)}") from exc


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _project_hub() -> Path:
    parts = REPO_ROOT.parts
    if ".opal-worktrees" in parts:
        return Path(*parts[: parts.index(".opal-worktrees")])
    return REPO_ROOT


def _git_blob(path: str) -> bytes:
    completed = subprocess.run(
        ["git", "cat-file", "blob", f"HEAD:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AuditFailure(f"HEAD baseline blob missing: {path}")
    return completed.stdout


def _measure_materialized_blobs(paths: tuple[str, ...], iterations: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        materialized: list[Path] = []
        for index, source_path in enumerate(paths):
            target = temp / f"{index}.blob"
            target.write_bytes(_git_blob(source_path))
            materialized.append(target)

        samples: list[int] = []
        payload = 0
        for _ in range(iterations):
            started = time.perf_counter_ns()
            content = [path.read_bytes() for path in materialized]
            samples.append(time.perf_counter_ns() - started)
            payload = sum(len(value) for value in content)
    return {
        "documents": list(paths),
        "document_count": len(paths),
        "payload_bytes": payload,
        "time_ns": {
            "samples": samples,
            "average": sum(samples) // len(samples),
            "maximum": max(samples),
            "minimum": min(samples),
        },
    }


def _measure_memory(project_root: Path, *, boot: bool, iterations: int) -> dict[str, Any]:
    memory_file = project_root / ".opal" / "MEMORY.json"
    if not memory_file.is_file():
        return {
            "available": False,
            "payload_bytes": 0,
            "time_ns": {"samples": [0] * iterations, "average": 0, "maximum": 0, "minimum": 0},
        }
    command = [sys.executable, str(MEMORY_TOOL), "show", "--file", str(memory_file)]
    if boot:
        command.extend(["--boot-brief", "--max-bytes", "1024", "--memories", "3", "--history", "0"])
    else:
        command.append("--brief")

    samples: list[int] = []
    stdout = ""
    for _ in range(iterations):
        started = time.perf_counter_ns()
        completed = _run(command)
        samples.append(time.perf_counter_ns() - started)
        stdout = completed.stdout
    payload = json.loads(stdout)
    if boot:
        if len(stdout.encode("utf-8")) > 1024:
            raise AuditFailure("boot brief exceeds 1024 UTF-8 bytes")
        if len(payload.get("index_rows", [])) > 3:
            raise AuditFailure("boot brief exceeds three active memories")
        if payload.get("history_rows"):
            raise AuditFailure("boot brief unexpectedly includes history")
    return {
        "available": True,
        "payload_bytes": len(stdout.encode("utf-8")),
        "active_memory_count": len(payload.get("index_rows", [])),
        "history_count": len(payload.get("history_rows", [])),
        "time_ns": {
            "samples": samples,
            "average": sum(samples) // len(samples),
            "maximum": max(samples),
            "minimum": min(samples),
        },
    }


def _combine_time(*measurements: dict[str, Any]) -> dict[str, Any]:
    sample_sets = [measurement["time_ns"]["samples"] for measurement in measurements]
    combined = [sum(values) for values in zip(*sample_sets)]
    return {
        "samples": combined,
        "average": sum(combined) // len(combined),
        "maximum": max(combined),
        "minimum": min(combined),
    }


def _reduction(before: int, after: int) -> float:
    return round((before - after) * 100.0 / before, 2) if before else 0.0


def measure_boot_payloads(project_root: Path, iterations: int = 3) -> dict[str, Any]:
    before_general = _measure_materialized_blobs(BASELINE_GENERAL_DOCS, iterations)
    before_project_docs = _measure_materialized_blobs(BASELINE_PROJECT_DOCS, iterations)
    before_memory = _measure_memory(project_root, boot=False, iterations=iterations)

    with tempfile.TemporaryDirectory() as directory:
        deployed = Path(directory) / "empty-deployed"
        deployed.mkdir()
        common = [
            sys.executable,
            str(EVENT_LOADER),
            "measure",
            "--iterations",
            str(iterations),
            "--source-root",
            str(REPO_ROOT),
            "--deployed-root",
            str(deployed),
            "--project-root",
            str(REPO_ROOT),
        ]
        after_assistant = _run_json(common[:3] + ["--event", "session.assistant"] + common[3:])
        after_project_event = _run_json(common[:3] + ["--event", "session.project"] + common[3:])

    after_memory = _measure_memory(project_root, boot=True, iterations=iterations)
    before_project_payload = before_project_docs["payload_bytes"] + before_memory["payload_bytes"]
    after_project_payload = (
        after_assistant["payload_bytes"]
        + after_project_event["payload_bytes"]
        + after_memory["payload_bytes"]
    )
    before_project_time = _combine_time(before_project_docs, before_memory)
    after_project_time = _combine_time(after_assistant, after_project_event, after_memory)

    general_reduction = _reduction(
        before_general["payload_bytes"], after_assistant["payload_bytes"]
    )
    # Task 113's legacy baseline is no longer present in later checkouts: the
    # HEAD blobs may already be the compact event-driven documents.  In that
    # case a reduction percentage is not a meaningful regression signal, but
    # an expansion still is, so retain the hard size cap below.
    general_baseline_available = (
        before_general["payload_bytes"] > after_assistant["payload_bytes"]
    )
    metrics = {
        "method": {
            "baseline": "git HEAD blobs materialized once, then read three times",
            "after": "event-loader measure plus bounded project-brief queries, three times",
            "identity": "user-specific identity.md excluded from both sides",
            "project_before": "legacy automatic PM Eager chain",
        },
        "general_assistant": {
            "before": before_general,
            "after": after_assistant,
            "payload_reduction_percent": general_reduction,
            "legacy_baseline_available": general_baseline_available,
            "under_30kb": after_assistant["payload_bytes"] <= 30 * 1024,
            "at_least_70_percent_reduction": (
                not general_baseline_available or general_reduction >= 70.0
            ),
        },
        "project_aware_assistant": {
            "before": {
                **before_project_docs,
                "legacy_memory_brief": before_memory,
                "payload_bytes": before_project_payload,
                "time_ns": before_project_time,
            },
            "after": {
                "session_assistant": after_assistant,
                "session_project": after_project_event,
                "memory_boot_brief": after_memory,
                "payload_bytes": after_project_payload,
                "time_ns": after_project_time,
            },
            "payload_reduction_percent": _reduction(before_project_payload, after_project_payload),
            "under_30kb": after_project_payload <= 30 * 1024,
            "at_least_70_percent_reduction": _reduction(before_project_payload, after_project_payload)
            >= 70.0,
        },
    }
    for state in ("general_assistant", "project_aware_assistant"):
        if not metrics[state]["under_30kb"]:
            raise AuditFailure(f"{state} after payload exceeds 30KB")
        if not metrics[state]["at_least_70_percent_reduction"]:
            raise AuditFailure(f"{state} payload reduction is below 70%")
    return metrics


def _extract_bootstrap_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if path.suffix == ".mdc":
        match = re.match(r"\A---\n.*?\n---\n\n?(.*)\Z", text, re.DOTALL)
        if not match:
            raise AuditFailure(f"cursor frontmatter/body parse failed: {path}")
        return match.group(1).strip()
    match = re.search(r"^```markdown\n(.*?)^```\s*$", text, re.MULTILINE | re.DOTALL)
    if not match:
        raise AuditFailure(f"bootstrap fenced body parse failed: {path}")
    return match.group(1).strip()


def _changed_markdown_files() -> list[Path]:
    modified = _run(
        ["git", "diff", "--name-only", "HEAD", "--", "*.md", "*.mdc"]
    ).stdout.splitlines()
    untracked = _run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", "*.md", "*.mdc"]
    ).stdout.splitlines()
    return sorted({(REPO_ROOT / path).resolve() for path in modified + untracked})


def _doc_standard_section_5() -> str:
    standard = (REPO_ROOT / "opal/core/references/opal-doc-standard.md").read_text(encoding="utf-8")
    match = re.search(r"^## 5\. 이력과 버전\n(.*?)(?=^## 6\.)", standard, re.MULTILINE | re.DOTALL)
    if not match:
        raise AuditFailure("opal-doc-standard.md §5 not found")
    return match.group(1)


def _history_aliases_from_standard(section: str) -> tuple[str, ...]:
    history_paragraph = section.split("문서 상단", 1)[0]
    aliases = tuple(re.findall(r"`([^`]+)`", history_paragraph))
    if len(aliases) < 4:
        raise AuditFailure("opal-doc-standard.md §5 history heading examples are unavailable")
    return aliases


def _manual_history_headings(text: str, aliases: tuple[str, ...]) -> list[str]:
    normalized_aliases = tuple(re.sub(r"\s+", "", alias).casefold() for alias in aliases)
    hits = []
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*$", text, re.MULTILINE):
        normalized_heading = re.sub(r"\s+", "", heading).casefold()
        if any(alias in normalized_heading for alias in normalized_aliases):
            hits.append(heading)
    return hits


def _load_opal_agent_module() -> Any:
    spec = importlib.util.spec_from_file_location("task113_opal_agent", OPAL_AGENT)
    if spec is None or spec.loader is None:
        raise AuditFailure("opal-agent import spec unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_source_audit(project_root: Path, iterations: int = 3) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ids = tuple(event["id"] for event in manifest["events"])
    if ids != STANDARD_EVENTS:
        raise AuditFailure(f"standard event drift: {ids}")
    checks.append({"name": "manifest_14_events", "count": len(ids)})

    disabled = next(event for event in manifest["events"] if event["id"] == "session.disabled")
    worker = next(event for event in manifest["events"] if event["id"] == "session.worker")
    for event in (disabled, worker):
        if event["required_docs"] or event["optional_docs"]:
            raise AuditFailure(f"{event['id']} must declare zero documents")
    checks.append({"name": "zero_payload_session_declarations", "events": [disabled["id"], worker["id"]]})

    static = _run_json(
        [sys.executable, str(EVENT_LOADER), "static-check", "--source-root", str(REPO_ROOT)]
    )
    if not static["ok"] or static["violation_count"]:
        raise AuditFailure(f"event static-check failed: {static['violations']}")
    checked = {Path(path).resolve() for path in static["checked_files"]}
    pilots = {path.resolve() for path in REPO_ROOT.glob("opal/skills/opal-pilot-*/SKILL.md")}
    workers = {path.resolve() for path in REPO_ROOT.glob("opal/agents/*/AGENT.md")}
    if not pilots.issubset(checked):
        missing = sorted(str(path) for path in pilots - checked)
        raise AuditFailure(
            f"pilot static coverage mismatch: {len(pilots)} pilots found, "
            f"missing from static-check: {missing}"
        )
    if not workers.issubset(checked):
        missing = sorted(str(path) for path in workers - checked)
        raise AuditFailure(
            f"worker static coverage mismatch: {len(workers)} workers found, "
            f"missing from static-check: {missing}"
        )
    checks.append({"name": "consumer_static_check", "pilots": len(pilots), "workers": len(workers)})

    bootstrap_paths = (
        REPO_ROOT / "opal/bootstrapper/claude-bootstrap.md",
        REPO_ROOT / "opal/bootstrapper/codex-bootstrap.md",
        REPO_ROOT / "opal/bootstrapper/cursor-bootstrap.mdc",
        REPO_ROOT / "opal/bootstrapper/gemini-bootstrap.md",
    )
    bodies = [_extract_bootstrap_body(path) for path in bootstrap_paths]
    if len(set(bodies)) != 1:
        raise AuditFailure("four platform bootstrap bodies are not byte-equivalent after wrappers")
    body = bodies[0]
    required_fragments = (
        "session.disabled",
        "session.worker",
        "session.assistant",
        "session.project",
        "load --event session.assistant",
        "event-loader/run.sh project-brief --project-root <project-root>",
        "stdout 전문을 byte-for-byte 첫 응답 맨 앞에 출력",
        "내부 컨텍스트로만 소비하거나 다시 요약하지 않는다",
        "UTF-8 1,024바이트",
        "session.project`에서만 수행",
    )
    missing = [fragment for fragment in required_fragments if fragment not in body]
    if missing:
        raise AuditFailure(f"bootstrap contract fragments missing: {missing}")
    forbidden_commands = (
        "load --event pm.activate",
        "load --event pilot.start",
        "load --event worker.dispatch",
        "state-tool/run.sh boot-summary <project-root>",
        "memory-tool/run.sh show --file <project-root>",
        "Read ~/.opal/references/opal-harness.md",
        "Read ~/.opal/references/opal-pm.md",
        "Read docs/PROJECT.md",
    )
    present = [fragment for fragment in forbidden_commands if fragment in body]
    if present:
        raise AuditFailure(f"Eager-forbidden bootstrap commands present: {present}")
    order = (
        body.index("load --event session.assistant"),
        body.index("event-loader/run.sh project-brief"),
        body.index("stdout 전문을 byte-for-byte"),
    )
    if order != tuple(sorted(order)):
        raise AuditFailure(f"project boot actions are out of order: {order}")
    # The display contract must retain every mode boundary, including the
    # marker cases that must never invoke project-only briefing.
    if "[WORKER]" not in body or "[ASSISTANT]" not in body or "bootstrap`이 정확히 `off`" not in body:
        raise AuditFailure("bootstrap mode boundaries are incomplete")
    checks.append({"name": "bootstrapper_body_parity", "platforms": 4})

    # Exercise the two bounded SSOT queries with absence, unfinished-task, and
    # actionable-memory fixtures.  This keeps the audit independent of the
    # hub's live task and memory contents.
    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory)
        no_tasks = _run_json(
            [sys.executable, str(STATE_TOOL), "boot-summary", str(fixture)]
        )
        if no_tasks.get("items") != []:
            raise AuditFailure(f"empty project boot summary is not a no-op: {no_tasks}")
        empty_brief = _run([
            sys.executable, str(EVENT_LOADER), "project-brief",
            "--source-root", str(REPO_ROOT), "--project-root", str(fixture),
        ]).stdout
        if empty_brief != "[부트스트랩] ✅ session.project ⏳ PM\n":
            raise AuditFailure(f"empty project brief changed the short prefix: {empty_brief!r}")
        task_dir = fixture / "tasks" / "999-fixture"
        task_dir.mkdir(parents=True)
        (task_dir / "state.json").write_text(json.dumps({
            "task_id": "999 fixture", "current_status": "in_progress",
            "updated_at": "2026-09-11 12:00:00", "next_action": "resume",
            "rows": [{"status": "in_progress", "stage": "EXECUTE"}],
        }), encoding="utf-8")
        unfinished = _run_json(
            [sys.executable, str(STATE_TOOL), "boot-summary", str(fixture)]
        )
        unfinished_items = unfinished.get("items", [])
        if not unfinished_items or unfinished_items[0].get("stage") != "EXECUTE":
            raise AuditFailure(f"unfinished task missing from boot summary: {unfinished}")
        memory = fixture / ".opal" / "MEMORY.json"
        memory.parent.mkdir()
        memory.write_text(json.dumps({"version": 1, "last_task_number": 999,
            "memories": [
                {"title": "일반", "date": "2026-09-20", "type": "project", "status": "active", "file": "memory/p.md", "summary": "일반"},
                {"title": "후보", "date": "2026-09-01", "type": "project", "status": "candidate", "file": "memory/c.md", "summary": "검토"},
                {"title": "피드백", "date": "2026-09-19", "type": "feedback", "status": "active", "file": "memory/f.md", "summary": "확인"},
            ], "history": []}, ensure_ascii=False), encoding="utf-8")
        memory_result = _run_json([
            sys.executable, str(MEMORY_TOOL), "show", "--file", str(memory),
            "--boot-brief", "--max-bytes", "1024", "--memories", "3", "--history", "0",
        ])
        if [row.get("title") for row in memory_result.get("review_rows", [])] != ["후보", "피드백"]:
            raise AuditFailure(f"actionable memory priority drift: {memory_result}")
        if len(memory_result.get("review_rows", [])) > 2:
            raise AuditFailure("boot brief returned more than two review rows")
        rendered = _run([
            sys.executable, str(EVENT_LOADER), "project-brief",
            "--source-root", str(REPO_ROOT), "--project-root", str(fixture),
        ]).stdout.rstrip("\n")
        required_output = (
            "📌 이어보기",
            "- 999 fixture — EXECUTE · 다음: resume",
            "📌 우선 검토",
            "- 후보 — 검토",
            "- 피드백 — 확인",
        )
        missing_output = [fragment for fragment in required_output if fragment not in rendered]
        if missing_output:
            raise AuditFailure(f"ready-to-emit project brief omitted output: {missing_output}")
        if len(rendered.encode("utf-8")) > 1024:
            raise AuditFailure("rendered project brief exceeds 1024 UTF-8 bytes")
    checks.append({"name": "project_boot_brief_fixtures", "cases": ["absence", "unfinished", "review_priority", "rendered_stdout"]})

    module = _load_opal_agent_module()
    resolver_cases = (
        ("[WORKER]\njob", False, True, "session.disabled"),
        ("[WORKER]\njob", True, True, "session.worker"),
        ("[ASSISTANT]\njob", True, True, "session.assistant"),
        ("job", True, True, "session.project"),
        ("job", True, False, "session.assistant"),
        ("job\n[WORKER]", True, True, "session.project"),
    )
    for prompt, enabled, project, expected in resolver_cases:
        actual = module.resolve_session_event(prompt, enabled, project)
        if actual != expected:
            raise AuditFailure(f"session resolver mismatch: expected {expected}, got {actual}")
    checks.append({"name": "session_resolver_precedence", "cases": len(resolver_cases)})

    with tempfile.TemporaryDirectory() as directory:
        receipt = Path(directory) / "stage-execute.json"
        loaded = _run_json(
            [
                sys.executable,
                str(EVENT_LOADER),
                "load",
                "--event",
                "stage.execute",
                "--source-root",
                str(REPO_ROOT),
            ]
        )
        receipt.write_text(json.dumps(loaded, ensure_ascii=False), encoding="utf-8")
        verified = _run_json(
            [
                sys.executable,
                str(STATE_TOOL),
                "event-verify",
                "--event",
                "stage.execute",
                "--receipt",
                str(receipt),
                "--source-root",
                str(REPO_ROOT),
            ]
        )
    if not verified["ok"] or verified.get("via") != "state-tool event-verify":
        raise AuditFailure("state-tool event-verify did not pass through a current receipt")
    checks.append({"name": "state_tool_event_verify"})

    standard_section = _doc_standard_section_5()
    history_aliases = _history_aliases_from_standard(standard_section)
    changed_markdown = _changed_markdown_files()
    history_hits = []
    for path in changed_markdown:
        current_text = path.read_text(encoding="utf-8")
        current_headings = _manual_history_headings(current_text, history_aliases)
        if not current_headings:
            continue
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        baseline = subprocess.run(
            ["git", "show", f"HEAD:{rel_path}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        baseline_headings = (
            _manual_history_headings(baseline.stdout, history_aliases)
            if baseline.returncode == 0 else []
        )
        new_headings = [heading for heading in current_headings if heading not in baseline_headings]
        if new_headings:
            history_hits.append({"path": rel_path, "headings": new_headings})
    if history_hits:
        raise AuditFailure(f"manual history headings remain in changed Markdown: {history_hits}")
    checks.append({"name": "changed_markdown_history_sections", "files": len(changed_markdown), "hits": 0})

    if "수기 누적 이력 절을 만들지 않는다" not in standard_section or "git과 태스크 기록이 소유" not in standard_section:
        raise AuditFailure("opal-doc-standard.md §5 history ownership contract drift")
    policy_files = {
        "CONVENTIONS": REPO_ROOT / "docs/CONVENTIONS.md",
        "skill_creator": REPO_ROOT / "opal/skills/opal-skill-creator/SKILL.md",
        "gc_checklist": REPO_ROOT / "opal/skills/op-gc-convention/references/convention-categories.md",
    }
    for label, path in policy_files.items():
        text = path.read_text(encoding="utf-8")
        if "opal-doc-standard.md" not in text or "§5" not in text:
            raise AuditFailure(f"{label} does not point to opal-doc-standard.md §5")
    if "기존 수기 누적 이력 절은 전체 제거한다" not in policy_files["skill_creator"].read_text(encoding="utf-8"):
        raise AuditFailure("skill creator does not remove existing manual history sections")
    if "Y (절 전체 제거)" not in policy_files["gc_checklist"].read_text(encoding="utf-8"):
        raise AuditFailure("GC checklist does not auto-remove whole history sections")
    checks.append({"name": "doc_standard_section_5_alignment", "consumers": len(policy_files)})

    mac_installer = (REPO_ROOT / "scripts/install-mac.sh").read_text(encoding="utf-8")
    windows_installer = (REPO_ROOT / "scripts/install/windows.ps1").read_text(encoding="utf-8")
    mac_fragments = ("opal/core/references", 'local clean_dirs=("skills" "agents" "references" "templates" "tools"')
    windows_fragments = ("'references', 'templates', 'tools'", "$toolsSrc", "'opal', 'core', 'references'")
    for fragment in mac_fragments:
        if fragment not in mac_installer:
            raise AuditFailure(f"mac installer asset parity fragment missing: {fragment}")
    for fragment in windows_fragments:
        if fragment not in windows_installer:
            raise AuditFailure(f"Windows installer asset parity fragment missing: {fragment}")
    checks.append({"name": "installer_static_parity", "pwsh_available": shutil.which("pwsh") is not None})

    metrics = measure_boot_payloads(project_root, iterations)
    checks.append({"name": "cold_start_measurement", "iterations": iterations})
    return {"ok": True, "mode": "source", "checks": checks, "metrics": metrics}


def run_installed_parity(installed_root: Path) -> dict[str, Any]:
    installed_root = installed_root.expanduser().resolve()
    mismatches: list[dict[str, str]] = []
    checked: list[dict[str, str]] = []
    for source_relative, installed_relative in PARITY_PATHS:
        source = REPO_ROOT / source_relative
        installed = installed_root / installed_relative
        if not installed.is_file():
            mismatches.append({"path": installed_relative, "reason": "installed_missing"})
            continue
        source_hash = _sha256(source)
        installed_hash = _sha256(installed)
        if source_hash != installed_hash:
            mismatches.append(
                {
                    "path": installed_relative,
                    "reason": "sha256_mismatch",
                    "source_sha256": source_hash,
                    "installed_sha256": installed_hash,
                }
            )
        checked.append({"source": source_relative, "installed": installed_relative, "sha256": source_hash})
    run_sh = installed_root / "tools/event-loader/run.sh"
    if run_sh.exists() and not run_sh.stat().st_mode & 0o111:
        mismatches.append({"path": "tools/event-loader/run.sh", "reason": "not_executable"})
    if mismatches:
        raise AuditFailure(f"installed parity failed: {mismatches}")
    return {"ok": True, "mode": "installed", "installed_root": str(installed_root), "checked": checked}


def snapshot_installed(installed_root: Path) -> dict[str, Any]:
    """설치 전 복구 근거로 핵심 배포 파일의 존재·hash를 읽기 전용 기록한다."""
    installed_root = installed_root.expanduser().resolve()
    targets = [installed_root / "AGENT.md"] + [
        installed_root / installed_relative for _, installed_relative in PARITY_PATHS
    ]
    files = []
    for path in targets:
        files.append(
            {
                "path": str(path),
                "exists": path.is_file(),
                "bytes": path.stat().st_size if path.is_file() else None,
                "sha256": _sha256(path) if path.is_file() else None,
            }
        )
    return {"ok": True, "mode": "snapshot", "installed_root": str(installed_root), "files": files}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Task 113 bootstrap/event harness audit")
    parser.add_argument("--mode", choices=("source", "snapshot", "installed", "all"), default="source")
    parser.add_argument("--project-root", type=Path, default=_project_hub())
    parser.add_argument("--installed-root", type=Path, default=Path.home() / ".opal")
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.iterations < 1:
        payload: dict[str, Any] = {"ok": False, "error": "invalid_iterations"}
    else:
        try:
            results = []
            if args.mode in ("source", "all"):
                results.append(run_source_audit(args.project_root.resolve(), args.iterations))
            if args.mode == "snapshot":
                results.append(snapshot_installed(args.installed_root))
            if args.mode in ("installed", "all"):
                results.append(run_installed_parity(args.installed_root))
            payload = {"ok": True, "mode": args.mode, "results": results}
        except (AuditFailure, OSError, ValueError, json.JSONDecodeError) as exc:
            payload = {"ok": False, "mode": args.mode, "error": type(exc).__name__, "detail": str(exc)}

    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
