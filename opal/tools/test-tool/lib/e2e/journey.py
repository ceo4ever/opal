"""
@header {
  "module": "journey",
  "layer": "util",
  "domain": "opal-tools",
  "description": "프로젝트 E2E 여정 Markdown을 읽고 참조 조각을 실행 가능한 scenario v2 step/assertion으로 전개한다.",
  "exports": [
    "JourneyError", "parse_journey_document", "load_journey",
    "expand_journey", "load_and_expand_journey"
  ]
}
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, Mapping

import yaml

from lib.e2e.fragment import FragmentError, expand_fragment, load_fragment_registry


_YAML_FENCE = re.compile(r"```(?:yaml|yml)\s*\n(?P<body>.*?)```", re.IGNORECASE | re.DOTALL)


class JourneyError(ValueError):
    def __init__(self, detail_code: str, detail: str):
        super().__init__(detail)
        self.detail_code = detail_code
        self.detail = detail


def _payload(text: str, *, source: str) -> Dict[str, Any]:
    stripped = text.lstrip()
    body = None
    if stripped.startswith("---"):
        parts = stripped.split("---", 2)
        if len(parts) == 3:
            body = parts[1]
    if body is None:
        match = _YAML_FENCE.search(text)
        if match:
            body = match.group("body")
    if body is None:
        raise JourneyError(
            "journey_document_contract_missing",
            f"{source}: YAML frontmatter or fenced YAML contract is required",
        )
    try:
        value = yaml.safe_load(body)
    except yaml.YAMLError as exc:
        raise JourneyError("journey_yaml_invalid", f"{source}: {exc}") from exc
    if not isinstance(value, dict):
        raise JourneyError("journey_document_invalid", f"{source}: journey contract must be an object")
    return dict(value)


def parse_journey_document(text: str, *, source: str = "<journey>") -> Dict[str, Any]:
    journey = _payload(text, source=source)
    journey_id = journey.get("id")
    if not isinstance(journey_id, str) or not journey_id.strip():
        raise JourneyError("journey_id_required", f"{source}: non-empty id is required")
    steps = journey.get("steps")
    if not isinstance(steps, list) or not steps or any(not isinstance(item, dict) for item in steps):
        raise JourneyError("journey_steps_required", f"{source}: one or more object steps are required")
    assertions = journey.get("assertions", [])
    if not isinstance(assertions, list) or any(not isinstance(item, dict) for item in assertions):
        raise JourneyError("journey_assertions_invalid", f"{source}: assertions must be object rows")
    normalized = dict(journey)
    normalized["id"] = journey_id.strip()
    normalized["steps"] = [dict(item) for item in steps]
    normalized["assertions"] = [dict(item) for item in assertions]
    normalized["source_path"] = source
    return normalized


def load_journey(path: str | Path) -> Dict[str, Any]:
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise JourneyError("journey_read_failed", f"{source}: {exc}") from exc
    journey = parse_journey_document(text, source=str(source))
    if journey["id"] != source.stem:
        raise JourneyError(
            "journey_id_path_mismatch",
            f"{source}: id {journey['id']!r} must match filename {source.stem!r}",
        )
    return journey


def expand_journey(
    journey: Mapping[str, Any],
    fragments: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    """조각 참조를 순서대로 실제 scenario steps와 postcondition assertions로 바꾼다."""
    journey_id = str(journey.get("id") or "")
    steps = []
    assertions = [dict(item) for item in (journey.get("assertions") or [])]
    fragment_ids = []
    occurrences: Dict[str, int] = {}

    for index, raw in enumerate(journey.get("steps") or [], start=1):
        fragment_id = raw.get("fragment")
        if fragment_id is None:
            step = dict(raw)
            step.setdefault("id", f"journey:{journey_id}:step-{index}")
            step.setdefault("executor", "browser")
            step.setdefault("step_role", "verify")
            step["origin_scope"] = "journey"
            step["origin_id"] = journey_id
            steps.append(step)
            continue

        fragment_id = str(fragment_id)
        fragment = fragments.get(fragment_id)
        if fragment is None:
            raise JourneyError(
                "journey_fragment_not_found",
                f"{journey.get('source_path', journey_id)}: unknown fragment {fragment_id!r}",
            )
        bindings = raw.get("with", {})
        if not isinstance(bindings, dict):
            raise JourneyError("journey_fragment_bindings_invalid", f"fragment {fragment_id!r}: with must be an object")
        occurrences[fragment_id] = occurrences.get(fragment_id, 0) + 1
        try:
            expanded = expand_fragment(fragment, bindings, occurrence=occurrences[fragment_id])
        except FragmentError as exc:
            raise JourneyError(exc.detail_code, exc.detail) from exc
        steps.extend(expanded["steps"])
        assertions.extend(expanded["assertions"])
        if fragment_id not in fragment_ids:
            fragment_ids.append(fragment_id)

    scenario = {
        key: value
        for key, value in journey.items()
        if key not in {"source_path", "steps", "assertions"}
    }
    scenario.setdefault("surface_kind", "browser")
    scenario.setdefault("profile", "browser")
    scenario.setdefault("actors", ["browser"])
    scenario.setdefault("required_evidence", ["metadata", "actions"])
    scenario["steps"] = steps
    scenario["assertions"] = assertions
    scenario["journey_source"] = journey.get("source_path")
    scenario["fragment_ids"] = fragment_ids
    return scenario


def load_and_expand_journey(path: str | Path, *, fragments_root: str | Path | None = None) -> Dict[str, Any]:
    journey_path = Path(path)
    root = Path(fragments_root) if fragments_root is not None else journey_path.parent.parent / "fragments"
    try:
        fragments = load_fragment_registry(root)
    except FragmentError as exc:
        raise JourneyError(exc.detail_code, exc.detail) from exc
    return expand_journey(load_journey(journey_path), fragments)
