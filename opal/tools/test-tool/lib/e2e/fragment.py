"""
@header {
  "module": "fragment",
  "layer": "util",
  "domain": "opal-tools",
  "description": "E2E 조각 문서 등록·검증 — Markdown의 YAML 계약을 읽고 params·steps·필수 postconditions를 검증한다.",
  "exports": [
    "FragmentError", "parse_fragment_document", "load_fragment",
    "load_fragment_registry", "expand_fragment"
  ]
}

조각은 실행 매크로가 아니라 사후 조건을 가진 검증 블록이다. 이 모듈은 문서를
읽고 전개할 뿐 판정·상태·exit을 만들지 않는다.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, Mapping, MutableMapping

import yaml


_YAML_FENCE = re.compile(r"```(?:yaml|yml)\s*\n(?P<body>.*?)```", re.IGNORECASE | re.DOTALL)
_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_-]*)\}")


class FragmentError(ValueError):
    """등록·전개할 수 없는 조각 계약."""

    def __init__(self, detail_code: str, detail: str):
        super().__init__(detail)
        self.detail_code = detail_code
        self.detail = detail


def _document_payload(text: str, *, source: str) -> Dict[str, Any]:
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
        raise FragmentError(
            "fragment_document_contract_missing",
            f"{source}: YAML frontmatter or fenced YAML contract is required",
        )
    try:
        payload = yaml.safe_load(body)
    except yaml.YAMLError as exc:
        raise FragmentError("fragment_yaml_invalid", f"{source}: {exc}") from exc
    if not isinstance(payload, dict):
        raise FragmentError("fragment_document_invalid", f"{source}: fragment contract must be an object")
    return dict(payload)


def _validate_fragment(payload: Mapping[str, Any], *, source: str) -> Dict[str, Any]:
    fragment_id = payload.get("id")
    if not isinstance(fragment_id, str) or not fragment_id.strip():
        raise FragmentError("fragment_id_required", f"{source}: non-empty id is required")

    params = payload.get("params", [])
    if not isinstance(params, list) or any(not isinstance(item, str) or not item for item in params):
        raise FragmentError("fragment_params_invalid", f"{source}: params must be a list of names")
    if len(params) != len(set(params)):
        raise FragmentError("fragment_params_duplicate", f"{source}: params must be unique")

    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps or any(not isinstance(item, dict) for item in steps):
        raise FragmentError("fragment_steps_required", f"{source}: one or more object steps are required")
    for index, step in enumerate(steps, start=1):
        if "fragment" in step:
            raise FragmentError(
                "fragment_nested_reference_forbidden",
                f"{source}: steps[{index}] cannot reference another fragment",
            )
        if step.get("kind") in ("fill", "type") and "value" in step:
            raise FragmentError(
                "fragment_secret_value_forbidden",
                f"{source}: steps[{index}] must use value_ref instead of an inline value",
            )

    postconditions = payload.get("postconditions")
    if not isinstance(postconditions, list) or not postconditions:
        raise FragmentError(
            "fragment_postcondition_required",
            f"{source}: one or more postconditions are required",
        )
    for index, condition in enumerate(postconditions, start=1):
        if not isinstance(condition, dict) or not condition.get("verifier") or "expected" not in condition:
            raise FragmentError(
                "fragment_postcondition_invalid",
                f"{source}: postconditions[{index}] requires verifier and expected",
            )

    normalized = dict(payload)
    normalized["id"] = fragment_id.strip()
    normalized["params"] = list(params)
    normalized["steps"] = [dict(item) for item in steps]
    normalized["postconditions"] = [dict(item) for item in postconditions]
    normalized["source_path"] = source
    return normalized


def parse_fragment_document(text: str, *, source: str = "<fragment>") -> Dict[str, Any]:
    """Markdown 문서 한 건을 검증된 조각 dict로 바꾼다."""
    return _validate_fragment(_document_payload(text, source=source), source=source)


def load_fragment(path: str | Path) -> Dict[str, Any]:
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise FragmentError("fragment_read_failed", f"{source}: {exc}") from exc
    fragment = parse_fragment_document(text, source=str(source))
    if fragment["id"] != source.stem:
        raise FragmentError(
            "fragment_id_path_mismatch",
            f"{source}: id {fragment['id']!r} must match filename {source.stem!r}",
        )
    return fragment


def load_fragment_registry(root: str | Path) -> Dict[str, Dict[str, Any]]:
    """`fragments/*.md`를 결정론적 이름 순서로 등록한다."""
    directory = Path(root)
    registry: Dict[str, Dict[str, Any]] = {}
    if not directory.is_dir():
        raise FragmentError("fragment_registry_not_found", f"fragment directory not found: {directory}")
    for path in sorted(directory.glob("*.md")):
        fragment = load_fragment(path)
        fragment_id = fragment["id"]
        if fragment_id in registry:
            raise FragmentError("fragment_id_duplicate", f"duplicate fragment id: {fragment_id}")
        registry[fragment_id] = fragment
    return registry


def _substitute(value: Any, bindings: Mapping[str, Any], *, source: str) -> Any:
    if isinstance(value, dict):
        return {key: _substitute(item, bindings, source=source) for key, item in value.items()}
    if isinstance(value, list):
        return [_substitute(item, bindings, source=source) for item in value]
    if not isinstance(value, str):
        return value

    whole = _PLACEHOLDER.fullmatch(value)
    if whole:
        name = whole.group(1)
        if name not in bindings:
            raise FragmentError("fragment_binding_missing", f"{source}: missing binding for {name!r}")
        return bindings[name]

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in bindings:
            raise FragmentError("fragment_binding_missing", f"{source}: missing binding for {name!r}")
        return str(bindings[name])

    return _PLACEHOLDER.sub(replace, value)


def expand_fragment(
    fragment: Mapping[str, Any],
    bindings: Mapping[str, Any],
    *,
    occurrence: int = 1,
) -> Dict[str, Any]:
    """조각 1회를 실제 steps/assertions로 전개한다.

    전개 step id에 fragment scope를 넣는다. 같은 연산 signature가 여정 본문에도 있어도
    서로 다른 authoring scope이며, 둘 중 하나를 제거하거나 retry로 합치지 않는다.
    """
    fragment_id = str(fragment.get("id") or "")
    source = str(fragment.get("source_path") or fragment_id or "<fragment>")
    required = list(fragment.get("params") or [])
    missing = [name for name in required if name not in bindings]
    unknown = sorted(set(bindings) - set(required))
    if missing:
        raise FragmentError("fragment_binding_missing", f"{source}: missing bindings {missing}")
    if unknown:
        raise FragmentError("fragment_binding_unknown", f"{source}: unknown bindings {unknown}")

    steps = []
    for index, raw in enumerate(fragment.get("steps") or [], start=1):
        step = _substitute(dict(raw), bindings, source=source)
        original_id = str(step.get("id") or f"step-{index}")
        step["id"] = f"fragment:{fragment_id}:{occurrence}:{original_id}"
        step.setdefault("executor", "browser")
        step.setdefault("step_role", "verify")
        step["origin_scope"] = "fragment"
        step["origin_id"] = fragment_id
        step["origin_step_id"] = original_id
        steps.append(step)

    assertions = []
    for index, raw in enumerate(fragment.get("postconditions") or [], start=1):
        assertion = _substitute(dict(raw), bindings, source=source)
        original_id = str(assertion.get("id") or f"postcondition-{index}")
        assertion["id"] = f"fragment:{fragment_id}:{occurrence}:{original_id}"
        assertion.setdefault("executor", "browser")
        assertion.setdefault("match", "equals")
        assertion["origin_scope"] = "fragment"
        assertion["origin_id"] = fragment_id
        assertions.append(assertion)
    return {"steps": steps, "assertions": assertions, "fragment_ids": [fragment_id]}
