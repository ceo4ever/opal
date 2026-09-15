"""
@header {
  "module": "event_loader",
  "layer": "util",
  "domain": "opal-tools",
  "description": "이벤트 manifest 문서·receipt와 복수 진행 태스크·경로 이상·메모리를 포함한 bounded session.project 브리핑을 결정론적으로 생성·검증하는 플랫폼 독립 CLI",
  "exports": ["main", "load_event", "verify_receipt", "static_check", "measure_event", "compose_project_brief", "project_brief"]
}
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Iterable


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
REQUIRED_EVENT_FIELDS = (
    "id",
    "required_docs",
    "optional_docs",
    "predecessors",
    "receipt_required",
    "consumer",
)
TEXT_SUFFIXES = {".md", ".mdc", ".py", ".sh", ".json"}
ROOT_KEYS = ("source", "deployed", "project")
TOKEN_PATTERN = re.compile(r"^\{(source_root|deployed_root|project_root)\}(?:/|$)")
LEGACY_HARNESS_PATTERN = re.compile(
    r"(?:부트스트랩.{0,80}(?:로드되지|미로드)|fallback|폴백).{0,120}opal-harness\.md",
    re.IGNORECASE,
)


class EventLoaderError(Exception):
    def __init__(self, code: str, detail: str, **fields: Any) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.fields = fields


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _running_from_source() -> bool:
    path = Path(__file__).resolve()
    return path.parents[2].name == "opal" and (path.parents[3] / "opal" / "core" / "references").is_dir()


def _script_source_root() -> Path:
    if _running_from_source():
        return Path(__file__).resolve().parents[3]
    configured = os.environ.get("OPAL_SOURCE_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.cwd().resolve()


def _project_root(path: Path) -> Path:
    """cwd에서 `.git`과 `.opal/AGENT.md`를 함께 가진 첫 조상을 task root로 반환한다.

    루트 소유권 계약의 원문은 `harness/worktree.md` §task root와 allocator root
    계약이며 여기서 복제하지 않는다. 임의 조상의 ~/.opal 설치본을 프로젝트로
    오인하지 않도록 탐색 상한은 가장 가까운 Git 경계이고, 비-Git 프로젝트는
    호출자가 --project-root를 명시해야 한다.
    """
    resolved = path.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / ".git").exists():
            if (candidate / ".opal" / "AGENT.md").is_file():
                return candidate
            break
    return resolved


def _default_manifest(source_root: Path, deployed_root: Path) -> Path:
    if _running_from_source():
        return source_root / "opal" / "core" / "references" / "events.json"
    return deployed_root / "references" / "events.json"


def _roots(args: argparse.Namespace) -> dict[str, Path]:
    source = Path(args.source_root).expanduser().resolve() if args.source_root else _script_source_root()
    deployed = (
        Path(args.deployed_root).expanduser().resolve()
        if args.deployed_root
        else Path(os.environ.get("OPAL_DEPLOYED_ROOT", "~/.opal")).expanduser().resolve()
    )
    project = (
        Path(args.project_root).expanduser().resolve()
        if args.project_root
        else _project_root(Path.cwd())
    )
    return {"source_root": source, "deployed_root": deployed, "project_root": project}


def _read_manifest(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise EventLoaderError("manifest_not_found", f"manifest를 찾을 수 없습니다: {path}", path=str(path)) from exc
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EventLoaderError("manifest_invalid", f"manifest JSON이 유효하지 않습니다: {exc}", path=str(path)) from exc
    violations = _validate_manifest(manifest)
    if violations:
        raise EventLoaderError("manifest_invalid", "manifest schema 검증에 실패했습니다.", violations=violations)
    return manifest, raw


def _validate_manifest(manifest: Any) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    if not isinstance(manifest, dict) or not isinstance(manifest.get("events"), list):
        return [{"code": "events_missing", "detail": "events는 배열이어야 합니다."}]
    events = manifest["events"]
    ids: list[str] = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            violations.append({"code": "event_invalid", "index": index})
            continue
        missing = [field for field in REQUIRED_EVENT_FIELDS if field not in event]
        if missing:
            violations.append({"code": "event_fields_missing", "index": index, "fields": missing})
            continue
        event_id = event["id"]
        ids.append(event_id)
        for field in ("required_docs", "optional_docs", "predecessors"):
            if not isinstance(event[field], list):
                violations.append({"code": "event_field_type", "event": event_id, "field": field, "expected": "array"})
        if not isinstance(event["receipt_required"], bool):
            violations.append({"code": "event_field_type", "event": event_id, "field": "receipt_required", "expected": "boolean"})
        consumer = event["consumer"]
        if not isinstance(consumer, dict) or not isinstance(consumer.get("type"), str) or not isinstance(consumer.get("paths"), list):
            violations.append({"code": "consumer_invalid", "event": event_id})
        for kind in ("required_docs", "optional_docs"):
            seen_docs: set[str] = set()
            for doc in event.get(kind, []):
                if not isinstance(doc, dict) or not isinstance(doc.get("id"), str):
                    violations.append({"code": "document_invalid", "event": event_id, "field": kind})
                    continue
                if doc["id"] in seen_docs:
                    violations.append({"code": "document_duplicate", "event": event_id, "document": doc["id"]})
                seen_docs.add(doc["id"])
                variants = [key for key in ROOT_KEYS if key in doc]
                if not variants:
                    violations.append({"code": "document_path_missing", "event": event_id, "document": doc["id"]})
                for key in variants:
                    value = doc[key]
                    expected = f"{{{key}_root}}"
                    if not isinstance(value, str) or not value.startswith(expected):
                        violations.append({"code": "document_token_invalid", "event": event_id, "document": doc["id"], "path": value})
    duplicates = sorted({event_id for event_id in ids if ids.count(event_id) > 1})
    if duplicates:
        violations.append({"code": "event_duplicate", "events": duplicates})
    missing_events = [event_id for event_id in STANDARD_EVENTS if event_id not in ids]
    extra_events = [event_id for event_id in ids if event_id not in STANDARD_EVENTS]
    if missing_events:
        violations.append({"code": "standard_events_missing", "events": missing_events})
    if extra_events:
        violations.append({"code": "unknown_events", "events": extra_events})
    disabled = next((event for event in events if isinstance(event, dict) and event.get("id") == "session.disabled"), None)
    if disabled and (disabled.get("required_docs") or disabled.get("optional_docs")):
        violations.append({"code": "disabled_event_has_documents", "event": "session.disabled"})
    return violations


def _event_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {event["id"]: event for event in manifest["events"]}


def _event(manifest: dict[str, Any], event_id: str) -> dict[str, Any]:
    try:
        return _event_map(manifest)[event_id]
    except KeyError as exc:
        raise EventLoaderError("event_not_found", f"선언되지 않은 이벤트입니다: {event_id}", event=event_id) from exc


def _resolve_token(token: str, roots: dict[str, Path]) -> Path:
    match = TOKEN_PATTERN.match(token)
    if not match:
        raise EventLoaderError("path_token_invalid", f"root token이 없는 경로입니다: {token}", token=token)
    root_name = match.group(1)
    relative = token[match.end():]
    candidate = roots[root_name].joinpath(*Path(relative).parts).resolve()
    root = roots[root_name].resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise EventLoaderError("path_outside_root", f"root 밖의 문서 경로입니다: {token}", token=token) from exc
    return candidate


def _select_document_path(doc: dict[str, Any], roots: dict[str, Path]) -> tuple[str, Path]:
    # A source checkout consumes source variants; an installed copy consumes deployed variants.
    order = ("project", "source", "deployed") if _running_from_source() else ("project", "deployed", "source")
    variants: list[tuple[str, str, Path]] = []
    for key in order:
        if key in doc:
            token = doc[key]
            variants.append((key, token, _resolve_token(token, roots)))
    if not variants:
        raise EventLoaderError("document_path_missing", f"문서 경로가 없습니다: {doc.get('id')}", document=doc.get("id"))
    selected = variants[0]
    return selected[1], selected[2]


def _load_document(doc: dict[str, Any], roots: dict[str, Path], required: bool, include_content: bool = True) -> dict[str, Any] | None:
    token, path = _select_document_path(doc, roots)
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        if not required:
            return None
        raise EventLoaderError(
            "document_not_found",
            f"필수 문서를 찾을 수 없습니다: {token}",
            document=doc["id"],
            token=token,
            path=str(path),
        ) from exc
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EventLoaderError("document_not_utf8", f"문서가 UTF-8이 아닙니다: {token}", document=doc["id"], path=str(path)) from exc
    result = {
        "id": doc["id"],
        "token": token,
        "path": str(path),
        "sha256": _sha256(raw),
        "bytes": len(raw),
    }
    if include_content:
        result["content"] = content
    return result


def _context(args: argparse.Namespace) -> tuple[dict[str, Path], Path, dict[str, Any], bytes]:
    roots = _roots(args)
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else _default_manifest(roots["source_root"], roots["deployed_root"])
    manifest, raw = _read_manifest(manifest_path)
    return roots, manifest_path, manifest, raw


def load_event(args: argparse.Namespace) -> dict[str, Any]:
    roots, manifest_path, manifest, manifest_raw = _context(args)
    declaration = _event(manifest, args.event)
    required = [_load_document(doc, roots, True) for doc in declaration["required_docs"]]
    optional: list[dict[str, Any]] = []
    missing_optional: list[str] = []
    for doc in declaration["optional_docs"]:
        loaded = _load_document(doc, roots, False)
        if loaded is None:
            missing_optional.append(doc["id"])
        else:
            optional.append(loaded)
    documents = required + optional
    metadata = [{key: value for key, value in document.items() if key != "content"} for document in documents]
    manifest_sha = _sha256(manifest_raw)
    receipt = {
        "schema_version": 1,
        "event": args.event,
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_sha,
        "documents": metadata,
        "required_document_ids": [doc["id"] for doc in declaration["required_docs"]],
        "payload_bytes": sum(document["bytes"] for document in documents),
    }
    return {
        "ok": True,
        "command": "load",
        "event": args.event,
        "receipt_required": declaration["receipt_required"],
        "predecessors": declaration["predecessors"],
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_sha,
        "manifest_hash": manifest_sha,
        "documents": documents,
        "required_documents": required,
        "optional_documents": optional,
        "missing_optional_documents": missing_optional,
        "document_count": len(documents),
        "required_document_count": len(required),
        "payload_bytes": receipt["payload_bytes"],
        "receipt": receipt,
    }


def _read_receipt(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise EventLoaderError("receipt_not_found", f"receipt를 찾을 수 없습니다: {path}", path=str(path)) from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EventLoaderError("receipt_invalid", f"receipt JSON이 유효하지 않습니다: {exc}", path=str(path)) from exc
    if isinstance(value, dict) and isinstance(value.get("receipt"), dict):
        value = value["receipt"]
    if not isinstance(value, dict):
        raise EventLoaderError("receipt_invalid", "receipt는 JSON object여야 합니다.", path=str(path))
    return value


def verify_receipt(args: argparse.Namespace) -> dict[str, Any]:
    receipt_path = Path(args.receipt).expanduser().resolve()
    receipt = _read_receipt(receipt_path)
    receipt_event = receipt.get("event")
    if not isinstance(receipt_event, str):
        raise EventLoaderError("receipt_invalid", "receipt.event가 없습니다.", path=str(receipt_path))
    if args.event and args.event != receipt_event:
        raise EventLoaderError("event_mismatch", f"요청 event와 receipt event가 다릅니다: {args.event} != {receipt_event}", expected_event=args.event, receipt_event=receipt_event)
    if not args.manifest and isinstance(receipt.get("manifest_path"), str):
        args.manifest = receipt["manifest_path"]
    roots, manifest_path, manifest, manifest_raw = _context(args)
    declaration = _event(manifest, receipt_event)
    current_manifest_sha = _sha256(manifest_raw)
    if receipt.get("manifest_sha256") != current_manifest_sha:
        raise EventLoaderError("stale_receipt", "manifest hash가 현재 값과 다릅니다.", expected_sha256=current_manifest_sha, receipt_sha256=receipt.get("manifest_sha256"))
    receipt_docs = receipt.get("documents")
    if not isinstance(receipt_docs, list):
        raise EventLoaderError("receipt_invalid", "receipt.documents가 배열이 아닙니다.")
    by_id = {doc.get("id"): doc for doc in receipt_docs if isinstance(doc, dict) and isinstance(doc.get("id"), str)}
    if len(by_id) != len(receipt_docs):
        raise EventLoaderError("receipt_invalid", "receipt.documents에 id 누락 또는 중복이 있습니다.")
    current_documents: list[dict[str, Any]] = []
    required_ids = [doc["id"] for doc in declaration["required_docs"]]
    if receipt.get("required_document_ids") != required_ids:
        raise EventLoaderError("missing_document", "receipt의 필수 문서 목록이 현재 선언과 다릅니다.", expected_document_ids=required_ids, receipt_document_ids=receipt.get("required_document_ids"))
    for declaration_doc in declaration["required_docs"]:
        current = _load_document(declaration_doc, roots, True, include_content=False)
        assert current is not None
        current_documents.append(current)
    for declaration_doc in declaration["optional_docs"]:
        current = _load_document(declaration_doc, roots, False, include_content=False)
        if current is not None:
            current_documents.append(current)
    current_by_id = {doc["id"]: doc for doc in current_documents}
    if set(by_id) != set(current_by_id):
        raise EventLoaderError("stale_receipt", "receipt 문서 집합이 현재 이벤트 선언과 다릅니다.", expected_document_ids=sorted(current_by_id), receipt_document_ids=sorted(by_id))
    verified: list[dict[str, Any]] = []
    for doc_id, current in current_by_id.items():
        recorded = by_id.get(doc_id)
        if recorded is None:
            raise EventLoaderError("missing_document", f"receipt에 필수 문서가 없습니다: {doc_id}", document=doc_id)
        if recorded.get("token") != current["token"] or recorded.get("path") != current["path"]:
            raise EventLoaderError("stale_receipt", f"문서 경로가 현재 선언과 다릅니다: {doc_id}", document=doc_id, expected_path=current["path"], receipt_path=recorded.get("path"))
        if recorded.get("sha256") != current["sha256"] or recorded.get("bytes") != current["bytes"]:
            raise EventLoaderError("document_hash_mismatch", f"문서 hash 또는 bytes가 현재 값과 다릅니다: {doc_id}", document=doc_id, expected_sha256=current["sha256"], receipt_sha256=recorded.get("sha256"))
        verified.append(current)
    current_payload_bytes = sum(doc["bytes"] for doc in verified)
    if receipt.get("payload_bytes") != current_payload_bytes:
        raise EventLoaderError("stale_receipt", "receipt payload bytes가 현재 문서 합계와 다릅니다.", expected_payload_bytes=current_payload_bytes, receipt_payload_bytes=receipt.get("payload_bytes"))
    return {
        "ok": True,
        "command": "verify",
        "event": receipt_event,
        "receipt_path": str(receipt_path),
        "manifest_path": str(manifest_path),
        "manifest_sha256": current_manifest_sha,
        "verified_documents": verified,
        "verified_document_count": len(verified),
        "payload_bytes": current_payload_bytes,
    }


def _expand_consumer_paths(source_root: Path, patterns: Iterable[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        candidate = Path(pattern).expanduser()
        if candidate.is_absolute():
            matches = glob.glob(str(candidate), recursive=True)
        else:
            matches = glob.glob(str(source_root / pattern), recursive=True)
        for match in matches:
            path = Path(match)
            if path.is_file() and path.suffix in TEXT_SUFFIXES:
                paths.add(path.resolve())
            elif path.is_dir():
                paths.update(child.resolve() for child in path.rglob("*") if child.is_file() and child.suffix in TEXT_SUFFIXES)
    return sorted(paths)


def _event_token_present(text: str, event_id: str) -> bool:
    if event_id in text:
        return True
    if event_id.startswith("stage.") and "stage.*" in text:
        return True
    if event_id.startswith("session.") and "session.*" in text:
        return True
    return False


def static_check(args: argparse.Namespace) -> dict[str, Any]:
    roots, manifest_path, manifest, manifest_raw = _context(args)
    selected = [_event(manifest, args.event)] if args.event else list(manifest["events"])
    violations = _validate_manifest(manifest)
    checked_files: set[str] = set()
    explicit_patterns = list(args.path or [])
    if not args.manifest_only:
        for declaration in selected:
            patterns = explicit_patterns or declaration["consumer"]["paths"]
            paths = _expand_consumer_paths(roots["source_root"], patterns)
            if explicit_patterns and not paths:
                violations.append({"code": "consumer_not_found", "event": declaration["id"], "paths": patterns})
                continue
            for path in paths:
                checked_files.add(str(path))
                text = path.read_text(encoding="utf-8")
                if not _event_token_present(text, declaration["id"]):
                    violations.append({"code": "event_contract_missing", "event": declaration["id"], "path": str(path)})
                elif "event-loader" not in text or not re.search(r"\b(?:load|verify|receipt)\b", text, re.IGNORECASE):
                    violations.append({"code": "loader_contract_missing", "event": declaration["id"], "path": str(path)})
                for line_number, line in enumerate(text.splitlines(), 1):
                    if LEGACY_HARNESS_PATTERN.search(line):
                        violations.append({"code": "legacy_harness_fallback", "event": declaration["id"], "path": str(path), "line": line_number})
    return {
        "ok": not violations,
        "command": "static-check",
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256(manifest_raw),
        "checked_events": [declaration["id"] for declaration in selected],
        "checked_files": sorted(checked_files),
        "violation_count": len(violations),
        "violations": violations,
    }


def measure_event(args: argparse.Namespace) -> dict[str, Any]:
    roots, manifest_path, manifest, manifest_raw = _context(args)
    declaration = _event(manifest, args.event)
    iterations = args.iterations
    samples_ns: list[int] = []
    final_documents: list[dict[str, Any]] = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        documents: list[dict[str, Any]] = []
        for doc in declaration["required_docs"]:
            loaded = _load_document(doc, roots, True, include_content=False)
            assert loaded is not None
            documents.append(loaded)
        for doc in declaration["optional_docs"]:
            loaded = _load_document(doc, roots, False, include_content=False)
            if loaded is not None:
                documents.append(loaded)
        samples_ns.append(time.perf_counter_ns() - started)
        final_documents = documents
    payload_bytes = sum(doc["bytes"] for doc in final_documents)
    return {
        "ok": True,
        "command": "measure",
        "event": args.event,
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256(manifest_raw),
        "iterations": iterations,
        "document_count": len(final_documents),
        "required_document_count": len(declaration["required_docs"]),
        "payload_bytes": payload_bytes,
        "declared_payload_bytes": payload_bytes,
        "documents": final_documents,
        "elapsed_ns": sum(samples_ns),
        "time_ns": {
            "samples": samples_ns,
            "average": sum(samples_ns) // len(samples_ns),
            "maximum": max(samples_ns),
            "minimum": min(samples_ns),
        },
    }


def _run_tool_json(command: list[str]) -> dict[str, Any] | None:
    """Run a read-only sibling tool and discard failed or malformed results."""
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return None
    return payload


def _brief_value(value: Any) -> str:
    """Normalize tool-owned values to one user-visible Markdown line."""
    return " ".join(str(value or "").split())


def compose_project_brief(
    state_payload: dict[str, Any] | None,
    memory_payload: dict[str, Any] | None,
    *,
    max_bytes: int = 1024,
) -> str:
    """Compose the exact bounded prefix for a session.project first response."""
    states: list[dict[str, str]] = []
    other_count = 0
    anomaly_count = 0
    if isinstance(state_payload, dict) and state_payload.get("ok") is True:
        items = state_payload.get("items")
        if isinstance(items, list):
            for item in items[:3]:
                if not isinstance(item, dict):
                    continue
                candidate = {
                    "title": _brief_value(item.get("title")),
                    "stage": _brief_value(item.get("stage")),
                    "next_action": _brief_value(item.get("next_action")),
                }
                if all(candidate.values()):
                    states.append(candidate)
        raw_other_count = state_payload.get("other_count", 0)
        if isinstance(raw_other_count, int) and not isinstance(raw_other_count, bool):
            other_count = max(0, raw_other_count)
        anomalies = state_payload.get("anomalies")
        if isinstance(anomalies, list):
            anomaly_count = len(anomalies)

    reviews: list[dict[str, str]] = []
    if isinstance(memory_payload, dict) and memory_payload.get("ok") is True:
        rows = memory_payload.get("review_rows")
        if isinstance(rows, list):
            for row in rows[:2]:
                if not isinstance(row, dict):
                    continue
                candidate = {
                    "title": _brief_value(row.get("title")),
                    "summary": _brief_value(row.get("summary")),
                }
                if all(candidate.values()):
                    reviews.append(candidate)

    def render() -> str:
        lines = ["[부트스트랩] ✅ session.project ⏳ PM"]
        if states or other_count or anomaly_count:
            lines.extend(["", "📌 이어보기"])
            lines.extend(
                f"- {state['title']} — {state['stage']} · 다음: {state['next_action']}"
                for state in states
            )
            if other_count:
                lines.append(f"- 그 외 {other_count}건")
            if anomaly_count:
                lines.append(f"- 경로 이상 {anomaly_count}건")
        if reviews:
            lines.extend(["", "📌 우선 검토"])
            lines.extend(f"- {row['title']} — {row['summary']}" for row in reviews)
        return "\n".join(lines)

    markdown = render()
    mutable = states + reviews
    while len(markdown.encode("utf-8")) > max_bytes:
        candidates = [
            (len(value.encode("utf-8")), row, key)
            for row in mutable
            for key, value in row.items()
            if value
        ]
        if not candidates:
            break
        _, row, key = max(candidates, key=lambda item: item[0])
        row[key] = row[key][:-1]
        markdown = render()
    return markdown


def project_brief(args: argparse.Namespace) -> dict[str, Any]:
    """Build a ready-to-emit session.project briefing from the two SSOT tools."""
    roots = _roots(args)
    project_root = roots["project_root"]
    tools_root = Path(__file__).resolve().parents[1]
    state_payload = _run_tool_json([
        sys.executable,
        str(tools_root / "state-tool" / "state_tool.py"),
        "boot-summary",
        str(project_root),
    ])
    memory_file = project_root / ".opal" / "MEMORY.json"
    memory_payload = None
    if memory_file.is_file():
        memory_payload = _run_tool_json([
            sys.executable,
            str(tools_root / "memory-tool" / "memory_tool.py"),
            "show",
            "--file",
            str(memory_file),
            "--boot-brief",
            "--max-bytes",
            "1024",
            "--memories",
            "3",
            "--history",
            "0",
        ])
    markdown = compose_project_brief(state_payload, memory_payload)
    return {
        "ok": True,
        "command": "project-brief",
        "markdown": markdown,
        "bytes": len(markdown.encode("utf-8")),
    }


def _add_context_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", help="events.json 경로")
    parser.add_argument("--source-root", help="framework source checkout root")
    parser.add_argument("--deployed-root", help="installed OPAL root")
    parser.add_argument("--project-root", help="current project root")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="event-loader", description="OPAL event document loader and receipt gate")
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser("load", help="필수 문서 전문과 receipt 반환")
    load_parser.add_argument("--event", required=True)
    _add_context_options(load_parser)
    load_parser.set_defaults(handler=load_event)

    verify_parser = subparsers.add_parser("verify", help="receipt의 event/manifest/document 최신성 검증")
    verify_parser.add_argument("--receipt", required=True)
    verify_parser.add_argument("--event")
    _add_context_options(verify_parser)
    verify_parser.set_defaults(handler=verify_receipt)

    static_parser = subparsers.add_parser("static-check", help="manifest 및 이벤트 소비자 로딩 계약 검사")
    static_parser.add_argument("--event")
    static_parser.add_argument("--path", action="append", help="검사할 파일/디렉터리/glob (반복 가능)")
    static_parser.add_argument("--manifest-only", action="store_true", help="manifest schema만 검사")
    _add_context_options(static_parser)
    static_parser.set_defaults(handler=static_check)

    measure_parser = subparsers.add_parser("measure", help="이벤트 선언 payload bytes와 읽기 시간 측정")
    measure_parser.add_argument("--event", required=True)
    measure_parser.add_argument("--iterations", type=int, default=3)
    _add_context_options(measure_parser)
    measure_parser.set_defaults(handler=measure_event)

    brief_parser = subparsers.add_parser(
        "project-brief",
        help="session.project 첫 응답용 상태·검토 브리핑 렌더",
    )
    brief_parser.add_argument("--json", action="store_true", help="Markdown 대신 JSON envelope 출력")
    _add_context_options(brief_parser)
    brief_parser.set_defaults(handler=project_brief)
    return parser


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if getattr(args, "iterations", 1) < 1:
        _emit({"ok": False, "command": args.command, "error": "invalid_iterations", "detail": "iterations는 1 이상이어야 합니다."})
        return 2
    try:
        payload = args.handler(args)
    except EventLoaderError as exc:
        _emit({"ok": False, "command": args.command, "error": exc.code, "detail": exc.detail, **exc.fields})
        return 1
    except OSError as exc:
        _emit({"ok": False, "command": args.command, "error": "io_error", "detail": str(exc)})
        return 1
    if args.command == "project-brief" and not args.json:
        print(payload["markdown"])
    else:
        _emit(payload)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
