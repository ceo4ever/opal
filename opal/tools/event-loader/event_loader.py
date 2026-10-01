"""
@header {
  "module": "event_loader",
  "layer": "util",
  "domain": "opal-tools",
  "description": "이벤트 manifest 문서·receipt(worker.dispatch 계약 2: 대상·역할·식별자 묶음, 에이전트 항목 선별, 구형 호환·호출 원장)와 bounded session.project 브리핑을 결정론적으로 생성·검증하는 플랫폼 독립 CLI",
  "exports": ["main", "load_event", "verify_receipt", "static_check", "measure_event", "load_report", "legacy_report", "agent_index", "compose_project_brief", "project_brief"],
  "depends": ["agent_sections"]
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
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_sections import parse_sections, select_agent_entries  # noqa: E402


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
    "stage.design",
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
CONTRACT_FLAGS = (
    ("contract_version", "--contract-version"),
    ("agent", "--agent"),
    ("role", "--role"),
    ("dispatch_id", "--dispatch-id"),
)
VERSION_PATTERN = re.compile(r"^[0-9]{1,6}$")
ROLE_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
DISPATCH_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,63}$")
AGENT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
DISPATCH_EVENT = "worker.dispatch"
INDEX_SECTIONS = ("전문 에이전트 매핑 테이블", "폴백 규칙", "탐색 경로")
LEGACY_WARNING = {
    "code": "legacy_dispatch_contract",
    "detail": "구형 호출(계약 인자 없음)입니다. 전체 문서를 전달하며 호환 종료 후 거부됩니다. --contract-version 2 --agent --role --dispatch-id 를 넘기십시오.",
}
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


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _contract_violations(event_id: str, contract: Any) -> list[dict[str, Any]]:
    problems: list[str] = []
    if not isinstance(contract, dict):
        problems.append("contract는 객체여야 합니다.")
    else:
        supported = contract.get("supported")
        if not _is_int(contract.get("current")):
            problems.append("current는 정수여야 합니다.")
        if not isinstance(supported, list) or not supported or not all(_is_int(v) for v in supported):
            problems.append("supported는 정수의 비어 있지 않은 배열이어야 합니다.")
        elif _is_int(contract.get("current")) and contract["current"] not in supported:
            problems.append("current는 supported에 포함되어야 합니다.")
        if not isinstance(contract.get("legacy_accepted"), bool):
            problems.append("legacy_accepted는 boolean이어야 합니다.")
    return [{"code": "contract_invalid", "event": event_id, "detail": text} for text in problems]


def _selection_violations(event_id: str, event: dict[str, Any]) -> list[dict[str, Any]]:
    selection = event["selection"]
    problems: list[str] = []
    if not isinstance(selection, dict):
        problems.append("selection은 객체여야 합니다.")
    else:
        doc_ids = [doc.get("id") for doc in event.get("required_docs", []) if isinstance(doc, dict)]
        if not isinstance(selection.get("document"), str) or selection["document"] not in doc_ids:
            problems.append("document는 required_docs에 있는 문서 id여야 합니다.")
        if selection.get("mode") != "agent_entries":
            problems.append("mode는 agent_entries여야 합니다.")
        for key in ("exclude_sections", "full_for_agents"):
            value = selection.get(key)
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                problems.append(f"{key}는 문자열 배열이어야 합니다.")
    return [{"code": "selection_invalid", "event": event_id, "detail": text} for text in problems]


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
        if "contract" in event:
            violations.extend(_contract_violations(event_id, event["contract"]))
        if "selection" in event:
            violations.extend(_selection_violations(event_id, event))
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


def _now_iso() -> str:
    configured = os.environ.get("OPAL_EVENT_LOADER_NOW")
    if configured:
        return configured
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ledger_path(roots: dict[str, Path]) -> Path:
    configured = os.environ.get("OPAL_EVENT_LOADER_LEDGER")
    if configured:
        return Path(configured).expanduser()
    return roots["deployed_root"] / "state" / "event-loader" / "legacy-dispatch.jsonl"


def _record_legacy(op: str, event_id: str, roots: dict[str, Path], warnings: list[dict[str, Any]]) -> None:
    """구형 호출 한 줄을 원장에 남긴다. 실패는 호출을 막지 않고 경고로만 남긴다."""
    line = json.dumps(
        {"ts": _now_iso(), "op": op, "event": event_id, "project_root": str(roots["project_root"])},
        ensure_ascii=False,
        sort_keys=True,
    )
    try:
        path = _ledger_path(roots)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as exc:
        warnings.append({"code": "ledger_write_failed", "detail": f"구형 호출 원장 기록 실패: {exc}"})


def _contract_args_error(code: str, detail: str, **fields: Any) -> EventLoaderError:
    return EventLoaderError(code, detail, **fields)


def _call_mode(args: argparse.Namespace, declaration: dict[str, Any]) -> dict[str, Any]:
    """호출 인자 묶음을 판정한다: plain(계약 선언 없음) | legacy | v2."""
    contract = declaration.get("contract")
    given = {name: getattr(args, name, None) for name, _ in CONTRACT_FLAGS}
    role_doc_arg = getattr(args, "role_doc", None)
    if not isinstance(contract, dict):
        if any(value is not None for value in given.values()) or role_doc_arg is not None:
            raise _contract_args_error(
                "contract_not_declared",
                f"이벤트 {declaration.get('id')}는 계약을 선언하지 않았으므로 계약 인자를 받을 수 없습니다.",
                event=declaration.get("id"),
            )
        return {"mode": "plain"}
    if all(value is None for value in given.values()) and role_doc_arg is None:
        if not contract.get("legacy_accepted"):
            return {"mode": "legacy", "rejected": True}
        return {"mode": "legacy", "rejected": False}
    missing = [flag for name, flag in CONTRACT_FLAGS if given[name] is None]
    if missing:
        raise _contract_args_error(
            "contract_args_missing",
            f"계약 인자가 모두 필요합니다. 누락: {', '.join(missing)}",
            missing=missing,
        )
    version, agent, role, dispatch_id = (given[name] for name, _ in CONTRACT_FLAGS)
    for value, pattern, flag in (
        (version, VERSION_PATTERN, "--contract-version"),
        (agent, AGENT_NAME_PATTERN, "--agent"),
        (role, ROLE_PATTERN, "--role"),
        (dispatch_id, DISPATCH_ID_PATTERN, "--dispatch-id"),
    ):
        if not pattern.fullmatch(value):
            raise _contract_args_error("contract_arg_invalid", f"{flag} 값의 형식이 올바르지 않습니다: {value}", argument=flag)
    version_number = int(version)
    if version_number not in contract["supported"]:
        raise _contract_args_error(
            "unsupported_contract_version",
            f"지원하지 않는 계약 버전입니다: {version_number}. 설치본을 갱신한 뒤 문서를 재로드하십시오.",
            requested=version_number,
            supported=contract["supported"],
        )
    role_doc: dict[str, Any] | None = None
    if role_doc_arg is not None:
        doc_path = Path(role_doc_arg).expanduser().resolve()
        try:
            raw = doc_path.read_bytes()
        except OSError as exc:
            raise _contract_args_error("contract_arg_invalid", f"--role-doc 파일을 읽을 수 없습니다: {doc_path}", argument="--role-doc") from exc
        role_doc = {"path": str(doc_path), "sha256": _sha256(raw)}
    return {
        "mode": "v2",
        "contract_version": version_number,
        "agent": agent,
        "role": role,
        "dispatch_id": dispatch_id,
        "role_doc": role_doc,
    }


def _resolve_agent(name: str, roots: dict[str, Path]) -> dict[str, str]:
    project_file = roots["project_root"] / ".opal" / "agents" / name / "AGENT.md"
    if project_file.is_file():
        origin, path = "project", project_file
    else:
        base = roots["source_root"] / "opal" / "agents" if _running_from_source() else roots["deployed_root"] / "agents"
        path = base / name / "AGENT.md"
        if not path.is_file():
            raise EventLoaderError("agent_not_found", f"에이전트 문서를 찾을 수 없습니다: {name}", agent=name)
        origin = "framework"
    return {"name": name, "path": str(path.resolve()), "sha256": _sha256(path.read_bytes()), "origin": origin}


def _metadata(document: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in document.items() if key != "content"}


def _body_sha256(documents: list[dict[str, Any]]) -> str:
    joined = "".join(f"{doc['id']}\0{doc['content']}\0" for doc in documents)
    return _sha256(joined.encode("utf-8"))


def _select_document(document: dict[str, Any], selection: dict[str, Any], agent: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """대상 에이전트 항목만 남긴 전달 문서와 selection 요약을 만든다. 원본 값은 source_* 로 보존한다."""
    result = select_agent_entries(document["content"], selection, agent)
    content = result["content"]
    delivered = dict(document)
    delivered.update(
        {
            "content": content,
            "sha256": _sha256(content.encode("utf-8")),
            "bytes": len(content.encode("utf-8")),
        }
    )
    summary = {
        "document": document["id"],
        "mode": selection["mode"],
        "agent": agent,
        "target_entry": result["target"],
        "kept_entries": result["kept_entries"],
        "dropped_entries": result["dropped_entries"],
        "excluded_sections": result["excluded_sections"],
        "original_bytes": result["original_bytes"],
        "content_bytes": result["content_bytes"],
    }
    return delivered, summary


def _collect_documents(declaration: dict[str, Any], roots: dict[str, Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    required = [_load_document(doc, roots, True) for doc in declaration["required_docs"]]
    optional: list[dict[str, Any]] = []
    missing_optional: list[str] = []
    for doc in declaration["optional_docs"]:
        loaded = _load_document(doc, roots, False)
        if loaded is None:
            missing_optional.append(doc["id"])
        else:
            optional.append(loaded)
    return required, optional, missing_optional


def _with_source_fields(document: dict[str, Any]) -> dict[str, Any]:
    entry = dict(document)
    entry.setdefault("source_sha256", document["sha256"])
    entry.setdefault("source_bytes", document["bytes"])
    return entry


def _build_response(
    args: argparse.Namespace,
    context: tuple[dict[str, Path], Path, dict[str, Any], bytes],
    *,
    record_ledger: bool,
) -> dict[str, Any]:
    roots, manifest_path, manifest, manifest_raw = context
    declaration = _event(manifest, args.event)
    call = _call_mode(args, declaration)
    if call["mode"] == "legacy" and call["rejected"]:
        raise EventLoaderError("legacy_dispatch_rejected", "구형 호출은 더 이상 허용되지 않습니다. 계약 인자를 넘겨 새 계약으로 호출하십시오.")
    required, optional, missing_optional = _collect_documents(declaration, roots)
    warnings: list[dict[str, Any]] = []
    selection_summary: dict[str, Any] | None = None
    agent_info: dict[str, str] | None = None
    source_payload_bytes = sum(doc["bytes"] for doc in required + optional)
    if call["mode"] == "v2":
        agent_info = _resolve_agent(call["agent"], roots)
        selection = declaration.get("selection")
        delivered_required: list[dict[str, Any]] = []
        for doc in required + optional:
            doc = _with_source_fields(doc)
            if isinstance(selection, dict) and doc["id"] == selection["document"]:
                doc, selection_summary = _select_document(doc, selection, call["agent"])
            delivered_required.append(doc)
        required = delivered_required[: len(required)]
        optional = delivered_required[len(required):]
    documents = required + optional
    manifest_sha = _sha256(manifest_raw)
    load_id = uuid.uuid4().hex
    payload_bytes = sum(document["bytes"] for document in documents)
    receipt: dict[str, Any] = {
        "schema_version": 2 if call["mode"] == "v2" else 1,
        "event": args.event,
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_sha,
        "documents": [_metadata(document) for document in documents],
        "required_document_ids": [doc["id"] for doc in declaration["required_docs"]],
        "payload_bytes": payload_bytes,
    }
    response: dict[str, Any] = {
        "ok": True,
        "command": "load",
        "event": args.event,
        "response_version": 2,
        "load_id": load_id,
        "receipt_required": declaration["receipt_required"],
        "predecessors": declaration["predecessors"],
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_sha,
        "manifest_hash": manifest_sha,
        "documents": documents,
        "required_documents": [{k: doc[k] for k in ("id", "token", "path", "sha256", "bytes")} for doc in required],
        "optional_documents": [{k: doc[k] for k in ("id", "token", "path", "sha256", "bytes")} for doc in optional],
        "missing_optional_documents": missing_optional,
        "document_count": len(documents),
        "required_document_count": len(required),
        "payload_bytes": payload_bytes,
        "receipt": receipt,
    }
    if call["mode"] == "v2":
        receipt.update(
            {
                "contract_version": call["contract_version"],
                "load_id": load_id,
                "dispatch_id": call["dispatch_id"],
                "agent": agent_info,
                "role": call["role"],
                "role_doc": call["role_doc"],
                "selection": selection_summary,
                "body_sha256": _body_sha256(documents),
                "source_payload_bytes": source_payload_bytes,
            }
        )
        response["contract"] = call["contract_version"]
        response["source_payload_bytes"] = source_payload_bytes
        response["selection"] = selection_summary
    elif call["mode"] == "legacy":
        response["contract"] = "legacy"
        warnings.append(dict(LEGACY_WARNING))
        if record_ledger:
            _record_legacy("load", args.event, roots, warnings)
        response["warnings"] = warnings
    # response_bytes: 자기 필드를 0으로 둔 응답 JSON의 UTF-8 길이
    response["response_bytes"] = 0
    if call["mode"] == "v2":
        receipt["response_bytes"] = 0
    size = len(json.dumps(response, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    response["response_bytes"] = size
    if call["mode"] == "v2":
        receipt["response_bytes"] = size
    return response


def load_event(args: argparse.Namespace) -> dict[str, Any]:
    return _build_response(args, _context(args), record_ledger=True)


def _read_response_file(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise EventLoaderError("receipt_not_found", f"receipt를 찾을 수 없습니다: {path}", path=str(path)) from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EventLoaderError("receipt_invalid", f"receipt JSON이 유효하지 않습니다: {exc}", path=str(path)) from exc
    if not isinstance(value, dict):
        raise EventLoaderError("receipt_invalid", "receipt는 JSON object여야 합니다.", path=str(path))
    receipt = value["receipt"] if isinstance(value.get("receipt"), dict) else value
    return value, receipt


def _check_contract_receipt(receipt: dict[str, Any], response: dict[str, Any], call: dict[str, Any]) -> None:
    """D-9 (b)(c): 인자와 receipt의 일치, 응답 본문과 receipt 해시의 일치."""
    if receipt.get("contract_version") != call["contract_version"]:
        raise EventLoaderError("contract_mismatch", "receipt의 계약 버전이 요청 값과 다릅니다.", receipt_contract_version=receipt.get("contract_version"), requested=call["contract_version"])
    recorded_agent = receipt.get("agent") if isinstance(receipt.get("agent"), dict) else {}
    if recorded_agent.get("name") != call["agent"]:
        raise EventLoaderError("dispatch_target_mismatch", "receipt의 대상 에이전트가 요청 값과 다릅니다.", receipt_agent=recorded_agent.get("name"), requested=call["agent"])
    role_doc = call["role_doc"]
    recorded_doc = receipt.get("role_doc")
    same_doc = (recorded_doc is None and role_doc is None) or (
        isinstance(recorded_doc, dict)
        and role_doc is not None
        and recorded_doc.get("path") == role_doc["path"]
        and recorded_doc.get("sha256") == role_doc["sha256"]
    )
    if receipt.get("role") != call["role"] or not same_doc:
        raise EventLoaderError("dispatch_role_mismatch", "receipt의 역할 또는 역할 문서가 요청 값과 다릅니다.", receipt_role=receipt.get("role"), requested=call["role"])
    if receipt.get("dispatch_id") != call["dispatch_id"]:
        raise EventLoaderError("dispatch_id_mismatch", "receipt의 디스패치 식별자가 요청 값과 다릅니다.", receipt_dispatch_id=receipt.get("dispatch_id"), requested=call["dispatch_id"])
    documents = response.get("documents")
    if response is receipt or not isinstance(documents, list) or not all(isinstance(d, dict) and isinstance(d.get("content"), str) for d in documents):
        raise EventLoaderError("response_body_missing", "receipt에 해당하는 응답 본문(documents[].content)이 없습니다. load 응답 전체 파일을 --receipt로 넘기십시오.")
    recorded_docs = receipt.get("documents")
    if not isinstance(recorded_docs, list) or [d.get("id") for d in documents] != [d.get("id") for d in recorded_docs if isinstance(d, dict)]:
        raise EventLoaderError("body_hash_mismatch", "응답 본문 문서 목록이 receipt와 다릅니다.")
    for body, recorded in zip(documents, recorded_docs):
        if _sha256(body["content"].encode("utf-8")) != recorded.get("sha256"):
            raise EventLoaderError("body_hash_mismatch", f"응답 본문이 receipt 해시와 다릅니다: {body.get('id')}", document=body.get("id"))
    if _body_sha256(documents) != receipt.get("body_sha256"):
        raise EventLoaderError("body_hash_mismatch", "응답 본문 전체 해시가 receipt와 다릅니다.")


def _check_selection_and_agent(
    receipt: dict[str, Any],
    declaration: dict[str, Any],
    roots: dict[str, Path],
    call: dict[str, Any],
) -> None:
    """D-9 (d)(e): 같은 규칙으로 선별을 다시 수행한 해시와 에이전트 문서 재해석."""
    required, optional, _ = _collect_documents(declaration, roots)
    selection = declaration.get("selection")
    recorded_by_id = {d.get("id"): d for d in receipt.get("documents", []) if isinstance(d, dict)}
    for doc in required + optional:
        if isinstance(selection, dict) and doc["id"] == selection["document"]:
            doc, _summary = _select_document(doc, selection, call["agent"])
        recorded = recorded_by_id.get(doc["id"])
        if recorded is None or recorded.get("sha256") != doc["sha256"]:
            raise EventLoaderError(
                "document_hash_mismatch",
                f"선별을 다시 수행한 전달 내용이 receipt와 다릅니다: {doc['id']}",
                document=doc["id"],
                expected_sha256=doc["sha256"],
                receipt_sha256=(recorded or {}).get("sha256"),
            )
    recorded_agent = receipt.get("agent") if isinstance(receipt.get("agent"), dict) else {}
    current = _resolve_agent(call["agent"], roots)
    if any(recorded_agent.get(key) != current[key] for key in ("path", "sha256", "origin")):
        raise EventLoaderError(
            "agent_changed",
            "에이전트 문서의 경로·해시·출처가 load 시점과 다릅니다. 다시 load하십시오.",
            receipt_origin=recorded_agent.get("origin"),
            current_origin=current["origin"],
            receipt_sha256=recorded_agent.get("sha256"),
            current_sha256=current["sha256"],
        )


def verify_receipt(args: argparse.Namespace) -> dict[str, Any]:
    receipt_path = Path(args.receipt).expanduser().resolve()
    response, receipt = _read_response_file(receipt_path)
    receipt_event = receipt.get("event")
    if not isinstance(receipt_event, str):
        raise EventLoaderError("receipt_invalid", "receipt.event가 없습니다.", path=str(receipt_path))
    if args.event and args.event != receipt_event:
        raise EventLoaderError("event_mismatch", f"요청 event와 receipt event가 다릅니다: {args.event} != {receipt_event}", expected_event=args.event, receipt_event=receipt_event)
    roots, manifest_path, manifest, manifest_raw = _context(args)
    receipt_manifest = receipt.get("manifest_path")
    if not isinstance(receipt_manifest, str) or Path(receipt_manifest).expanduser().resolve() != manifest_path:
        raise EventLoaderError(
            "stale_receipt",
            f"receipt 매니페스트 경로가 실행 경계 매니페스트와 다릅니다: {receipt_manifest} != {manifest_path}",
            expected_manifest_path=str(manifest_path),
            receipt_manifest_path=receipt_manifest,
        )
    declaration = _event(manifest, receipt_event)
    args.event = receipt_event
    call = _call_mode(args, declaration)
    receipt_schema = receipt.get("schema_version")
    warnings: list[dict[str, Any]] = []
    contract_fields: dict[str, Any] = {}
    if call["mode"] == "legacy":
        if receipt_schema == 2:
            raise EventLoaderError("contract_args_missing", "새 계약 receipt는 계약 인자가 필요합니다.", missing=[flag for _, flag in CONTRACT_FLAGS])
        if call["rejected"]:
            raise EventLoaderError("legacy_receipt_rejected", "구형 receipt는 더 이상 허용되지 않습니다. 새 계약으로 다시 load하십시오.")
        warnings.append(dict(LEGACY_WARNING))
        _record_legacy("verify", receipt_event, roots, warnings)
        contract_fields = {"contract": "legacy", "legacy_verified": True}
    elif call["mode"] == "v2":
        if receipt_schema != 2:
            raise EventLoaderError("contract_mismatch", "구형 receipt에 계약 인자를 함께 쓸 수 없습니다. 새 계약으로 다시 load하십시오.", receipt_schema_version=receipt_schema)
        _check_contract_receipt(receipt, response, call)
        _check_selection_and_agent(receipt, declaration, roots, call)
        contract_fields = {
            "contract": call["contract_version"],
            "dispatch_id": call["dispatch_id"],
            "agent": receipt.get("agent"),
            "role": call["role"],
            "load_id": receipt.get("load_id"),
        }
    v2 = call["mode"] == "v2"
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
        recorded_sha = recorded.get("source_sha256") if v2 else recorded.get("sha256")
        recorded_bytes = recorded.get("source_bytes") if v2 else recorded.get("bytes")
        if recorded_sha != current["sha256"] or recorded_bytes != current["bytes"]:
            raise EventLoaderError("document_hash_mismatch", f"문서 hash 또는 bytes가 현재 값과 다릅니다: {doc_id}", document=doc_id, expected_sha256=current["sha256"], receipt_sha256=recorded_sha)
        verified.append(current)
    current_payload_bytes = sum(doc["bytes"] for doc in verified)
    recorded_total = receipt.get("source_payload_bytes") if v2 else receipt.get("payload_bytes")
    if recorded_total != current_payload_bytes:
        raise EventLoaderError("stale_receipt", "receipt payload bytes가 현재 문서 합계와 다릅니다.", expected_payload_bytes=current_payload_bytes, receipt_payload_bytes=recorded_total)
    result: dict[str, Any] = {
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
    result.update(contract_fields)
    if warnings:
        result["warnings"] = warnings
    return result


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


def _dispatch_line_violations(path: Path, text: str) -> list[dict[str, Any]]:
    """D-14: worker.dispatch load/verify 줄의 계약 인자 누락과 게이트 줄의 자기 폴더 이름 불일치."""
    violations: list[dict[str, Any]] = []
    folder = path.parent.name if path.name == "AGENT.md" and path.parent.parent.name == "agents" else None
    for line_number, line in enumerate(text.splitlines(), 1):
        if "--event worker.dispatch" not in line or not re.search(r"\b(?:load|verify)\b", line):
            continue
        missing = [flag for _, flag in CONTRACT_FLAGS if flag not in line]
        if missing:
            violations.append({"code": "dispatch_contract_args_missing", "event": DISPATCH_EVENT, "path": str(path), "line": line_number, "missing": missing})
        if folder and re.search(r"\bverify\b", line):
            match = re.search(r"--agent\s+[`'\"]?([^\s`'\"]+)", line)
            if match and not match.group(1).startswith("<") and match.group(1) != folder:
                violations.append({"code": "dispatch_gate_agent_mismatch", "event": DISPATCH_EVENT, "path": str(path), "line": line_number, "agent": match.group(1), "folder": folder})
    return violations


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
                if declaration["id"] == DISPATCH_EVENT and isinstance(declaration.get("contract"), dict):
                    violations.extend(_dispatch_line_violations(path, text))
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
    context = _context(args)
    roots, manifest_path, manifest, manifest_raw = context
    declaration = _event(manifest, args.event)
    iterations = args.iterations
    samples_ns: list[int] = []
    response: dict[str, Any] = {}
    for _ in range(iterations):
        started = time.perf_counter_ns()
        response = _build_response(args, context, record_ledger=False)
        samples_ns.append(time.perf_counter_ns() - started)
    final_documents = [_metadata(doc) for doc in response["documents"]]
    payload_bytes = response["payload_bytes"]
    source_payload_bytes = response.get("source_payload_bytes", payload_bytes)
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
        "source_payload_bytes": source_payload_bytes,
        "response_bytes": response["response_bytes"],
        "declared_payload_bytes": source_payload_bytes,
        "documents": final_documents,
        "elapsed_ns": sum(samples_ns),
        "time_ns": {
            "samples": samples_ns,
            "average": sum(samples_ns) // len(samples_ns),
            "maximum": max(samples_ns),
            "minimum": min(samples_ns),
        },
    }


def load_report(args: argparse.Namespace) -> dict[str, Any]:
    """load 응답 파일들의 본문·응답 바이트 합계. load_id 기준 중복 제거, verify 결과 파일은 건너뛴다."""
    seen: dict[str, tuple[int, int]] = {}
    skipped_verify = 0
    for raw_path in args.receipt:
        path = Path(raw_path).expanduser().resolve()
        value, receipt = _read_response_file(path)
        if value.get("command") == "verify":
            skipped_verify += 1
            continue
        load_id = value.get("load_id") or receipt.get("load_id") or f"path:{path}"
        payload = receipt.get("payload_bytes", value.get("payload_bytes", 0))
        response_bytes = value.get("response_bytes", receipt.get("response_bytes", 0))
        seen.setdefault(str(load_id), (int(payload), int(response_bytes)))
    return {
        "ok": True,
        "command": "load-report",
        "load_count": len(seen),
        "skipped_verify_results": skipped_verify,
        "payload_bytes": sum(item[0] for item in seen.values()),
        "response_bytes": sum(item[1] for item in seen.values()),
    }


def _parse_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def legacy_report(args: argparse.Namespace) -> dict[str, Any]:
    roots = _roots(args)
    path = _ledger_path(roots)
    try:
        since = _parse_ts(args.since) if args.since else None
        until = _parse_ts(args.until) if args.until else None
    except ValueError as exc:
        raise EventLoaderError("contract_arg_invalid", f"시각 형식이 올바르지 않습니다: {exc}") from exc
    rows: list[tuple[datetime, dict[str, Any]]] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                stamp = _parse_ts(row["ts"])
            except (json.JSONDecodeError, KeyError, ValueError, TypeError, AttributeError):
                continue
            if (since and stamp < since) or (until and stamp > until):
                continue
            rows.append((stamp, row))
    rows.sort(key=lambda item: item[0])
    by_op: dict[str, int] = {}
    for _, row in rows:
        by_op[str(row.get("op"))] = by_op.get(str(row.get("op")), 0) + 1
    return {
        "ok": True,
        "command": "legacy-report",
        "ledger_path": str(path),
        "since": args.since,
        "until": args.until,
        "count": len(rows),
        "first_ts": rows[0][1]["ts"] if rows else None,
        "last_ts": rows[-1][1]["ts"] if rows else None,
        "by_op": by_op,
    }


def agent_index(args: argparse.Namespace) -> dict[str, Any]:
    """대상 선택용 가벼운 목록: 매핑 테이블·폴백 규칙·탐색 경로 절과 에이전트 이름만 출력한다."""
    roots, manifest_path, manifest, _ = _context(args)
    declaration = _event(manifest, DISPATCH_EVENT)
    selection = declaration.get("selection")
    if not isinstance(selection, dict):
        raise EventLoaderError("manifest_invalid", "worker.dispatch에 selection 선언이 없습니다.")
    doc = next(d for d in declaration["required_docs"] if d["id"] == selection["document"])
    loaded = _load_document(doc, roots, True)
    assert loaded is not None
    sections = parse_sections(loaded["content"])
    picked: list[dict[str, str]] = []
    index = 0
    while index < len(sections):
        section = sections[index]
        if section.level == 2 and section.title in INDEX_SECTIONS:
            end = index + 1
            while end < len(sections) and sections[end].level > 2:
                end += 1
            picked.append({"title": section.title, "content": "".join(s.text for s in sections[index:end])})
            index = end
            continue
        index += 1
    names = select_agent_entries(loaded["content"], selection, "")["dropped_entries"]
    return {
        "ok": True,
        "command": "agent-index",
        "manifest_path": str(manifest_path),
        "document": {k: loaded[k] for k in ("id", "token", "path", "sha256", "bytes")},
        "agents": names,
        "sections": picked,
        "content": "".join(item["content"] for item in picked),
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


def _brief_mode_value(value: Any) -> str:
    """Normalize a resolver-owned mode field without reinterpreting it."""
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def compose_project_brief(
    state_payload: dict[str, Any] | None,
    memory_payload: dict[str, Any] | None,
    *,
    max_bytes: int = 1024,
) -> str:
    """Compose the exact bounded prefix for a session.project first response.

    Mode resolution remains state-tool's responsibility. This display-only
    adapter accepts its structured payload and performs only safe line
    normalization; it does not infer or repair a mode or source.
    """
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
                    mode = _brief_mode_value(item.get("mode"))
                    mode_source = _brief_mode_value(item.get("mode_source"))
                    if mode and mode_source:
                        candidate.update({"mode": mode, "mode_source": mode_source})
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
            for state in states:
                line = (
                    f"- {state['title']} — {state['stage']}"
                    f" · 다음: {state['next_action']}"
                )
                if "mode" in state:
                    line += f" · 모드: {state['mode']} ({state['mode_source']})"
                lines.append(line)
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


def _add_contract_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--contract-version", dest="contract_version", help="worker.dispatch 계약 버전")
    parser.add_argument("--agent", help="디스패치 대상 에이전트 이름")
    parser.add_argument("--role", help="디스패치 역할 (예: builder, verifier)")
    parser.add_argument("--role-doc", dest="role_doc", help="역할 문서 경로(선택)")
    parser.add_argument("--dispatch-id", dest="dispatch_id", help="호출자가 발급한 디스패치 식별자")


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
    _add_contract_options(load_parser)
    _add_context_options(load_parser)
    load_parser.set_defaults(handler=load_event)

    verify_parser = subparsers.add_parser("verify", help="receipt의 event/manifest/document 최신성 검증")
    verify_parser.add_argument("--receipt", required=True)
    verify_parser.add_argument("--event")
    _add_contract_options(verify_parser)
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
    _add_contract_options(measure_parser)
    _add_context_options(measure_parser)
    measure_parser.set_defaults(handler=measure_event)

    report_parser = subparsers.add_parser("load-report", help="load 응답 파일들의 본문·응답 바이트 합계(load_id 중복 제거)")
    report_parser.add_argument("--receipt", nargs="+", required=True)
    _add_context_options(report_parser)
    report_parser.set_defaults(handler=load_report)

    legacy_parser = subparsers.add_parser("legacy-report", help="구형 worker.dispatch 호출 원장 집계")
    legacy_parser.add_argument("--since", help="ISO8601 시작 시각(포함)")
    legacy_parser.add_argument("--until", help="ISO8601 종료 시각(포함)")
    _add_context_options(legacy_parser)
    legacy_parser.set_defaults(handler=legacy_report)

    index_parser = subparsers.add_parser("agent-index", help="대상 선택용 매핑 테이블·폴백 규칙·탐색 경로·에이전트 이름 목록")
    _add_context_options(index_parser)
    index_parser.set_defaults(handler=agent_index)

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
