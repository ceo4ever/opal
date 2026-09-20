"""
@header {
  "module": "freshness",
  "layer": "util",
  "domain": "opal-tools",
  "description": "프로젝트 E2E 여정의 6요소 신선도 키, pass 증적 원장, 이전 증적 재인용 사건을 관리한다.",
  "exports": [
    "compose_key", "source_identity", "selected_driver_identity",
    "ledger_path", "load_ledger", "save_ledger", "find_reusable",
    "record_pass", "record_reuse"
  ],
  "depends": ["lib.scenario.FIDELITY_ORDER"]
}

Deterministic freshness keys and the project-local E2E evidence ledger.

The ledger never treats a skipped execution as a new pass.  A reusable entry
always points at an existing pass ``run.json`` and every reuse is appended as
an explicit ``evidence_reuse`` event.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from lib.scenario import FIDELITY_ORDER


SCHEMA_VERSION = "1.0"
REUSE_KIND = "evidence_reuse"
REUSE_DESCRIPTION = "이전 증적 재인용"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def hash_file(path: str | Path) -> str:
    """Return the SHA-256 of the exact tracked source bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compose_key(
    *,
    journey_hash: str,
    fragment_hashes: Mapping[str, str] | Iterable[str],
    surface_id: str,
    target_commit: str,
    driver: str,
    session_mode: Optional[str],
    achieved_fidelity: str,
) -> Dict[str, Any]:
    """Build the frozen six-part freshness key and its digest.

    Fragment hashes are a set semantically.  Mapping input retains fragment
    ids for auditability while sorting makes source traversal order irrelevant.
    """
    if isinstance(fragment_hashes, Mapping):
        fragments: Any = {
            str(key): str(value) for key, value in sorted(fragment_hashes.items())
        }
    else:
        fragments = sorted({str(value) for value in fragment_hashes})
    components = {
        "journey_hash": str(journey_hash),
        "fragment_hashes": fragments,
        "surface_id": str(surface_id),
        "target_commit": str(target_commit),
        "driver_identity": {
            "driver": str(driver),
            "session_mode": session_mode,
        },
        "achieved_fidelity": str(achieved_fidelity),
    }
    return {
        "key": hashlib.sha256(_canonical(components)).hexdigest(),
        "components": components,
    }


def source_identity(
    scenario: Mapping[str, Any], *, project_root: str | Path
) -> Optional[Dict[str, Any]]:
    """Hash a library journey and exactly the fragments it references."""
    journey_source = scenario.get("journey_source")
    if not journey_source:
        return None
    root = Path(project_root)
    journey_path = Path(str(journey_source))
    if not journey_path.is_absolute():
        journey_path = root / journey_path
    fragment_root = root / "docs" / "e2e" / "fragments"
    fragment_hashes = {
        str(fragment_id): hash_file(fragment_root / f"{fragment_id}.md")
        for fragment_id in sorted({str(item) for item in scenario.get("fragment_ids") or []})
    }
    return {
        "journey_hash": hash_file(journey_path),
        "fragment_hashes": fragment_hashes,
        "surface_id": str(scenario.get("surface_ref") or scenario.get("id") or ""),
    }


def selected_driver_identity(candidates: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Return the selected browser identity, or the selected executor identity."""
    selected = [item for item in candidates if item.get("outcome") == "selected"]
    chosen = next((item for item in selected if item.get("type") == "browser"), None)
    if chosen is None:
        chosen = selected[0] if selected else {}
    return {
        "driver": str(chosen.get("driver") or chosen.get("type") or "none"),
        "session_mode": chosen.get("session_mode"),
    }


def ledger_path(project_root: str | Path) -> Path:
    return Path(project_root) / ".e2e" / "freshness.json"


def _empty_ledger() -> Dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "entries": {}, "events": []}


def load_ledger(path: str | Path) -> Dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        return _empty_ledger()
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_ledger()
    if not isinstance(value, dict):
        return _empty_ledger()
    entries = value.get("entries")
    events = value.get("events")
    if not isinstance(entries, dict) or not isinstance(events, list):
        return _empty_ledger()
    return {
        "schema_version": SCHEMA_VERSION,
        "entries": dict(entries),
        "events": list(events),
    }


def save_ledger(path: str | Path, ledger: Mapping[str, Any]) -> None:
    """Atomically replace the ledger so interruption cannot leave partial JSON."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(dict(ledger), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, destination)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _evidence_is_reusable(entry: Mapping[str, Any]) -> bool:
    if entry.get("status") != "pass":
        return False
    run_json_path = entry.get("run_json_path")
    if not run_json_path or not Path(str(run_json_path)).is_file():
        return False
    try:
        run_json = json.loads(Path(str(run_json_path)).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        isinstance(run_json, dict)
        and run_json.get("status") == "pass"
        and bool(run_json.get("evidence_complete"))
    )


def find_reusable(
    path: str | Path,
    *,
    source: Mapping[str, Any],
    target_commit: str,
    driver_identity: Mapping[str, Any],
    required_fidelity: str,
) -> Optional[Dict[str, Any]]:
    """Find a matching pass whose achieved fidelity meets the current request."""
    required_rank = FIDELITY_ORDER.get(str(required_fidelity))
    if required_rank is None:
        return None
    for entry in load_ledger(path)["entries"].values():
        if not isinstance(entry, dict):
            continue
        components = entry.get("components") or {}
        achieved = str(components.get("achieved_fidelity") or "")
        if FIDELITY_ORDER.get(achieved, -1) < required_rank:
            continue
        if components.get("journey_hash") != source.get("journey_hash"):
            continue
        if components.get("fragment_hashes") != source.get("fragment_hashes"):
            continue
        if components.get("surface_id") != source.get("surface_id"):
            continue
        if components.get("target_commit") != target_commit:
            continue
        if components.get("driver_identity") != dict(driver_identity):
            continue
        if _evidence_is_reusable(entry):
            return dict(entry)
    return None


def record_pass(
    path: str | Path,
    *,
    source: Mapping[str, Any],
    target_commit: str,
    driver_identity: Mapping[str, Any],
    achieved_fidelity: str,
    run_id: str,
    run_json_path: str,
) -> Dict[str, Any]:
    evidence_path = Path(run_json_path).resolve()
    run_json = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(run_json, dict) or run_json.get("status") != "pass":
        raise ValueError("freshness ledger accepts only an existing pass run.json")
    composed = compose_key(
        journey_hash=str(source["journey_hash"]),
        fragment_hashes=source["fragment_hashes"],
        surface_id=str(source["surface_id"]),
        target_commit=target_commit,
        driver=str(driver_identity["driver"]),
        session_mode=driver_identity.get("session_mode"),
        achieved_fidelity=achieved_fidelity,
    )
    entry = {
        **composed,
        # Preserve the verdict already emitted through build_verdict; this
        # ledger is an index and never constructs a verdict of its own.
        "status": run_json.get("status"),
        "run_id": run_id,
        "run_json_path": str(evidence_path),
        "recorded_at": _now_iso(),
    }
    ledger = load_ledger(path)
    ledger["entries"][composed["key"]] = entry
    save_ledger(path, ledger)
    return entry


def record_reuse(
    path: str | Path,
    *,
    entry: Mapping[str, Any],
    requested_fidelity: str,
) -> Dict[str, Any]:
    event = {
        "kind": REUSE_KIND,
        "description": REUSE_DESCRIPTION,
        "freshness_key": entry.get("key"),
        "reused_run_id": entry.get("run_id"),
        "run_json_path": entry.get("run_json_path"),
        "requested_fidelity": requested_fidelity,
        "recorded_at": _now_iso(),
    }
    ledger = load_ledger(path)
    ledger["events"].append(event)
    save_ledger(path, ledger)
    return event
