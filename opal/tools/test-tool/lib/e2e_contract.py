"""
@header {
  "module": "e2e_contract",
  "layer": "util",
  "domain": "opal-tools",
  "description": "E2E profile, executor, status, legacy migration, and pass evidence contract owner.",
  "exports": [
    "E2E_CONTRACT_SCHEMA_VERSION",
    "PROFILES",
    "FINAL_STATUSES",
    "OPERATIONAL_STATUSES",
    "EXECUTOR_TYPES",
    "STATUS_EXIT_CODES",
    "STATUS_ERROR_CODES",
    "EXECUTOR_MATRIX",
    "HANDOFF_REQUIRED_FIELDS",
    "resolve_profile",
    "executor_contract",
    "validate_surface_match",
    "normalize_legacy_verdict",
    "can_try_next_provider",
    "build_verdict",
    "validate_pass_requirements",
    "validate_scenario_contract",
    "status_to_exit",
    "status_to_error"
  ],
  "depends": []
}

Platform-neutral E2E verdict contract.
"""

from typing import Any, Dict, Mapping, Optional, Sequence


E2E_CONTRACT_SCHEMA_VERSION = "2.0"
PROFILES = ("browser", "api", "hybrid", "collaborative", "manual")
FINAL_STATUSES = ("pass", "fail", "executor_unavailable", "infra_error", "blocked")
OPERATIONAL_STATUSES = ("awaiting_human",)
EXECUTOR_TYPES = ("browser", "api", "human")
STATUS_EXIT_CODES = {
    "pass": 0,
    "fail": 6,
    "infra_error": 7,
    "executor_unavailable": 18,
    "blocked": 19,
    "awaiting_human": 20,
}
STATUS_ERROR_CODES = {
    "fail": "e2e_failed",
    "infra_error": "e2e_infra_error",
    "executor_unavailable": "executor_unavailable",
    "blocked": "e2e_blocked",
    "awaiting_human": "e2e_awaiting_human",
}
EXECUTOR_MATRIX = {
    "browser": {"required": ("browser",), "allowed": ("browser",)},
    "api": {"required": ("api",), "allowed": ("api",)},
    "hybrid": {"required": ("api", "browser"), "allowed": ("api", "browser")},
    "collaborative": {
        "required": ("human",),
        "allowed": ("browser", "api", "human"),
    },
    "manual": {"required": ("human",), "allowed": ("human",)},
}
HANDOFF_REQUIRED_FIELDS = (
    "handoff_id",
    "instruction",
    "expected_observation",
    "required_evidence",
    "timeout_seconds",
    "resume_token",
    "server_policy",
    "submission_path",
)

_SURFACE_TO_PROFILE = {
    "web_ui": "browser",
    "browser": "browser",
    "ui": "browser",
    "api": "api",
    "hybrid": "hybrid",
    "collaborative": "collaborative",
    "manual": "manual",
}
_PROVIDER_UNAVAILABLE_REASONS = {"not_in_cmux", "cmux_not_installed"}
_INFRA_FALLBACK_REASONS = {"open_failed", "surface_parse_failed"}
_INFRA_ESCALATED_ERRORS = {
    "usage",
    "invalid_surface",
    "goto_failed",
    "eval_failed",
}
_LEGACY_KEYS = {"fallback", "fallback_reason", "escalated", "escalate", "escalation"}


def _result(
    *,
    ok: bool,
    status: Optional[str],
    error: Optional[str],
    detail: Any = None,
    normalized: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "ok": ok,
        "status": status,
        "error": error,
        "detail": detail,
        "normalized": normalized or {},
    }


def _scrub_legacy(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _scrub_legacy(v) for k, v in value.items() if k not in _LEGACY_KEYS}
    if isinstance(value, list):
        return [_scrub_legacy(v) for v in value]
    if value in {"fallback", "escalated", "escalate", "escalation"}:
        return None
    return value


def status_to_exit(status: str) -> int:
    return STATUS_EXIT_CODES.get(status, 6)


def status_to_error(status: str) -> Optional[str]:
    return STATUS_ERROR_CODES.get(status)


def executor_contract(profile: str) -> Dict[str, tuple[str, ...]]:
    return EXECUTOR_MATRIX[profile]


def resolve_profile(
    surface: Mapping[str, Any] | None,
    requirement_text: str = "",
    actors: Sequence[str] = (),
) -> Dict[str, Any]:
    surface_kind = (surface or {}).get("kind") or (surface or {}).get("surface_kind")
    profile = _SURFACE_TO_PROFILE.get(str(surface_kind or "").lower())
    text = requirement_text.lower()
    actor_set = {str(actor).lower() for actor in actors}
    if profile is None:
        if "manual" in text or actor_set == {"human"}:
            profile = "manual"
        elif "human" in actor_set:
            profile = "collaborative"
        elif "api" in text and ("ui" in text or "browser" in text):
            profile = "hybrid"
        elif "api" in text:
            profile = "api"
        elif "ui" in text or "browser" in text or "web" in text:
            profile = "browser"
    if profile not in PROFILES:
        return _result(
            ok=False,
            status="fail",
            error="surface_profile_mismatch",
            detail=f"cannot resolve profile from surface_kind={surface_kind!r}",
            normalized={"profile": None, "surface_kind": surface_kind, "actors": list(actors)},
        )
    return _result(
        ok=True,
        status="pass",
        error=None,
        normalized={"profile": profile, "surface_kind": surface_kind, "actors": list(actors)},
    )


def validate_surface_match(
    profile: str,
    surface_kind: str | None,
    actors: Sequence[str],
) -> Dict[str, Any]:
    if profile not in PROFILES:
        return _result(
            ok=False,
            status="fail",
            error="surface_profile_mismatch",
            detail=f"unknown profile: {profile}",
            normalized={"profile": profile, "surface_kind": surface_kind, "actors": list(actors)},
        )
    expected = _SURFACE_TO_PROFILE.get(str(surface_kind or "").lower())
    if expected and expected != profile:
        return _result(
            ok=False,
            status="fail",
            error="surface_profile_mismatch",
            detail=f"surface {surface_kind!r} requires profile {expected!r}",
            normalized={"profile": profile, "surface_kind": surface_kind, "actors": list(actors)},
        )
    return _result(
        ok=True,
        status="pass",
        error=None,
        normalized={"profile": profile, "surface_kind": surface_kind, "actors": list(actors)},
    )


def normalize_legacy_verdict(payload: Mapping[str, Any]) -> Dict[str, Any]:
    status = payload.get("status")
    error = payload.get("error")
    reason = payload.get("fallback_reason") or error
    normalized = _scrub_legacy(dict(payload))

    if status == "provider_unavailable":
        return _result(ok=False, status="provider_unavailable", error=None, normalized=normalized)
    if status == "fallback":
        if reason in _PROVIDER_UNAVAILABLE_REASONS:
            return _result(ok=False, status="provider_unavailable", error=None, normalized=normalized)
        return _result(
            ok=False,
            status="infra_error",
            error=status_to_error("infra_error"),
            detail=f"legacy fallback reason is not provider-only: {reason!r}",
            normalized=normalized,
        )
    if payload.get("has_cmux") is False:
        return _result(
            ok=False,
            status="infra_error",
            error=status_to_error("infra_error"),
            detail="legacy has_cmux=false is not execution evidence",
            normalized=normalized,
        )
    if status == "escalated" or payload.get("escalate") is True:
        if error == "wait_failed" and payload.get("wait_kind") == "assertion_condition":
            return _result(
                ok=False,
                status="fail",
                error=status_to_error("fail"),
                detail="assertion wait condition failed",
                normalized=normalized,
            )
        return _result(
            ok=False,
            status="infra_error",
            error=status_to_error("infra_error"),
            detail=f"legacy escalated error: {error!r}",
            normalized=normalized,
        )
    if status in STATUS_EXIT_CODES or status == "provider_unavailable":
        return _result(
            ok=status == "pass",
            status=status,
            error=status_to_error(status),
            normalized=normalized,
        )
    if error in _INFRA_ESCALATED_ERRORS or reason in _INFRA_FALLBACK_REASONS:
        return _result(
            ok=False,
            status="infra_error",
            error=status_to_error("infra_error"),
            detail=f"legacy driver error: {error or reason!r}",
            normalized=normalized,
        )
    return _result(
        ok=False,
        status="infra_error",
        error=status_to_error("infra_error"),
        detail="unknown legacy verdict",
        normalized=normalized,
    )


def can_try_next_provider(candidate_result: Mapping[str, Any]) -> bool:
    if candidate_result.get("status") == "provider_unavailable":
        return True
    legacy = normalize_legacy_verdict(candidate_result)
    return legacy.get("status") == "provider_unavailable"


def _required_assertion_ids(scenario: Mapping[str, Any]) -> set[str]:
    return {
        str(item.get("id"))
        for item in scenario.get("assertions") or []
        if isinstance(item, Mapping) and item.get("id") is not None
    }


def _observed_assertions(result: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    observed: Dict[str, Mapping[str, Any]] = {}
    for item in result.get("assertion_results") or []:
        if isinstance(item, Mapping) and item.get("id") is not None:
            observed[str(item.get("id"))] = item
    return observed


def validate_pass_requirements(
    scenario: Mapping[str, Any],
    result: Mapping[str, Any],
) -> Dict[str, Any]:
    profile = result.get("profile") or scenario.get("profile")
    surface_kind = scenario.get("surface_kind") or result.get("surface_kind")
    surface_match = validate_surface_match(str(profile), surface_kind, scenario.get("actors") or [])
    if not surface_match["ok"]:
        return surface_match

    contract = EXECUTOR_MATRIX.get(str(profile))
    if contract is None:
        return _result(
            ok=False,
            status="fail",
            error="surface_profile_mismatch",
            detail=f"unknown profile: {profile}",
            normalized={"profile": profile},
        )
    observed_executors = tuple(result.get("observed_executors") or [])
    missing_executors = [item for item in contract["required"] if item not in observed_executors]
    disallowed = [item for item in observed_executors if item not in contract["allowed"]]
    if missing_executors or disallowed:
        return _result(
            ok=False,
            status="fail",
            error="surface_profile_mismatch",
            detail={"missing_executors": missing_executors, "disallowed_executors": disallowed},
            normalized={"profile": profile, "observed_executors": list(observed_executors)},
        )

    required_assertions = _required_assertion_ids(scenario)
    observed_assertions = _observed_assertions(result)
    if not required_assertions:
        # Legacy v1 scenarios have no structured assertion spec. Keep pass gated by
        # structured verdict JSON by using observed assertion ids as the temporary
        # assertion contract only when the result supplies explicit expected/actual.
        required_assertions = set(observed_assertions)
        if not required_assertions:
            return _result(
                ok=False,
                status="fail",
                error="assertion_required",
                detail="pass requires at least one semantic assertion",
                normalized={"profile": profile},
            )
    for assertion_id in required_assertions:
        observed = observed_assertions.get(assertion_id)
        if not observed or "expected" not in observed or "actual" not in observed:
            return _result(
                ok=False,
                status="fail",
                error="assertion_expected_actual_missing",
                detail=f"missing expected/actual for assertion {assertion_id}",
                normalized={"profile": profile},
            )
        if observed.get("expected") != observed.get("actual"):
            return _result(
                ok=False,
                status="fail",
                error="assertion_failed",
                detail=f"assertion {assertion_id} expected/actual mismatch",
                normalized={"profile": profile},
            )

    required_evidence = set(scenario.get("required_evidence") or result.get("required_evidence") or [])
    observed_evidence = set(result.get("observed_evidence") or [])
    missing_evidence = sorted(required_evidence - observed_evidence)
    if missing_evidence:
        return _result(
            ok=False,
            status="fail",
            error="evidence_missing",
            detail={"missing_evidence": missing_evidence},
            normalized={"profile": profile, "observed_evidence": sorted(observed_evidence)},
        )

    normalized = dict(_scrub_legacy(dict(result)))
    normalized["profile"] = profile
    normalized["fidelity"] = result.get("fidelity") or scenario.get("required_fidelity") or "mock"
    return _result(ok=True, status="pass", error=None, normalized=normalized)


def build_verdict(run_result: Mapping[str, Any]) -> Dict[str, Any]:
    legacy = normalize_legacy_verdict(run_result)
    status = legacy.get("status")
    if status == "provider_unavailable":
        return legacy
    if status == "pass":
        assertion_specs = run_result.get("assertions")
        if not assertion_specs and run_result.get("assertion_results"):
            assertion_specs = [
                {"id": item.get("id"), "expected": item.get("expected")}
                for item in run_result.get("assertion_results") or []
                if isinstance(item, Mapping)
            ]
        required_evidence = run_result.get("required_evidence")
        if not required_evidence and run_result.get("observed_evidence"):
            required_evidence = list(run_result.get("observed_evidence") or [])
        scenario = {
            "profile": run_result.get("profile"),
            "surface_kind": run_result.get("surface_kind"),
            "actors": run_result.get("actors") or [],
            "assertions": assertion_specs or [],
            "required_evidence": required_evidence or [],
        }
        return validate_pass_requirements(scenario, run_result)
    if status == "awaiting_human":
        normalized = dict(_scrub_legacy(dict(run_result)))
        return _result(
            ok=True,
            status="awaiting_human",
            error=status_to_error("awaiting_human"),
            normalized=normalized,
        )
    if status in STATUS_EXIT_CODES:
        normalized = dict(_scrub_legacy(dict(run_result)))
        return _result(
            ok=status == "pass",
            status=status,
            error=status_to_error(status),
            normalized=normalized,
        )
    return legacy


def _validate_v2_scenario(scenario: Mapping[str, Any]) -> Optional[str]:
    scenario_id = scenario.get("id")
    required_keys = (
        "id",
        "surface_kind",
        "profile",
        "actors",
        "steps",
        "assertions",
        "required_evidence",
    )
    missing_keys = [key for key in required_keys if key not in scenario]
    if missing_keys:
        return f"{scenario_id}: missing required scenario keys {missing_keys}"
    if scenario.get("type") is not None and scenario.get("type") not in ("unit", "integration", "contract", "regression", "e2e"):
        return f"{scenario_id}: invalid type {scenario.get('type')!r}"
    if scenario.get("required_fidelity") is not None and scenario.get("required_fidelity") not in ("mock", "real-http", "real-usage"):
        return f"{scenario_id}: invalid required_fidelity {scenario.get('required_fidelity')!r}"
    if scenario.get("result") not in (None, "pass", "fail", "blocked", "infra_error", "executor_unavailable"):
        return f"{scenario_id}: invalid result {scenario.get('result')!r}"
    if scenario.get("operational_status") not in (None, "awaiting_human"):
        return f"{scenario_id}: invalid operational_status {scenario.get('operational_status')!r}"
    if scenario.get("result") is not None and scenario.get("operational_status") == "awaiting_human":
        return f"{scenario_id}: result and awaiting_human cannot both be set"
    for list_key in (
        "actors",
        "steps",
        "assertions",
        "required_evidence",
        "observed_executors",
        "assertion_results",
        "observed_evidence",
    ):
        if list_key in scenario and not isinstance(scenario.get(list_key), list):
            return f"{scenario_id}: {list_key} must be a list"
    for executor in scenario.get("observed_executors") or []:
        if executor not in EXECUTOR_TYPES:
            return f"{scenario_id}: invalid observed executor {executor!r}"
    if scenario.get("operational_status") == "awaiting_human":
        handoff_state = scenario.get("handoff_state")
        if not isinstance(handoff_state, Mapping):
            return f"{scenario_id}: complete handoff_state required"
        missing_state = [
            field for field in HANDOFF_REQUIRED_FIELDS
            if handoff_state.get(field) in (None, "", [])
        ]
        if missing_state:
            return f"{scenario_id}: handoff_state missing {missing_state}"
        if not scenario.get("run_id"):
            return f"{scenario_id}: run_id required for awaiting_human"
    profile = scenario.get("profile")
    if profile is None:
        return None
    if profile not in PROFILES:
        return f"{scenario_id}: invalid profile {profile!r}"
    surface = validate_surface_match(str(profile), scenario.get("surface_kind"), scenario.get("actors") or [])
    if not surface["ok"]:
        return f"{scenario_id}: {surface['error']}"
    contract = EXECUTOR_MATRIX[str(profile)]
    steps = scenario.get("steps") or []
    executors = [step.get("executor") for step in steps if isinstance(step, Mapping)]
    missing = [item for item in contract["required"] if item not in executors]
    disallowed = [item for item in executors if item not in contract["allowed"]]
    if missing or disallowed:
        return f"{scenario_id}: executor contract mismatch"
    assertions = scenario.get("assertions") or []
    if not assertions:
        return f"{scenario_id}: semantic assertion required"
    for assertion in assertions:
        if not isinstance(assertion, Mapping) or not assertion.get("id") or "expected" not in assertion:
            return f"{scenario_id}: assertion id and expected are required"
    if not scenario.get("required_evidence"):
        return f"{scenario_id}: required_evidence required"
    if profile in ("collaborative", "manual"):
        handoff = scenario.get("handoff")
        if not isinstance(handoff, Mapping):
            return f"{scenario_id}: complete handoff spec required"
        missing_handoff = [
            field for field in HANDOFF_REQUIRED_FIELDS
            if handoff.get(field) in (None, "", [])
        ]
        if missing_handoff:
            return f"{scenario_id}: handoff missing {missing_handoff}"
    return None


def validate_scenario_contract(
    spec: Mapping[str, Any],
    *,
    legacy_defaults: bool = True,
) -> Dict[str, Any]:
    if not isinstance(spec.get("scenarios"), list):
        return _result(
            ok=False,
            status="fail",
            error="scenario_contract_invalid",
            detail="scenarios must be a list",
            normalized={},
        )
    version = spec.get("schema_version")
    scenarios = list(spec.get("scenarios") or [])
    if version != E2E_CONTRACT_SCHEMA_VERSION:
        if not legacy_defaults:
            return _result(
                ok=False,
                status="fail",
                error="scenario_contract_invalid",
                detail=f"unsupported schema_version: {version!r}",
                normalized={},
            )
        normalized = dict(spec)
        normalized["scenarios"] = []
        for scenario in scenarios:
            item = dict(scenario)
            item.setdefault("required_fidelity", "mock")
            item.setdefault("profile", None)
            item.setdefault("required_evidence", [])
            normalized["scenarios"].append(item)
        return _result(ok=True, status="pass", error=None, normalized=normalized)

    for scenario in scenarios:
        detail = _validate_v2_scenario(scenario)
        if detail:
            return _result(
                ok=False,
                status="fail",
                error="scenario_contract_invalid",
                detail=detail,
                normalized={},
            )
    return _result(ok=True, status="pass", error=None, normalized=dict(spec))
