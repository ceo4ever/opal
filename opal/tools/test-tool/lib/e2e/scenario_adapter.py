"""
@header {
  "module": "scenario_adapter",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T09 시나리오 ↔ executor 어댑터 — schema_version 2.0 시나리오의 steps[]/assertions[]를 executor 실행 계획으로 옮기고(§A.4 step_role 구분 포함), 실행 결과를 e2e_contract.build_verdict/validate_pass_requirements가 먹는 verdict 입력으로 조립한다. 판정·상태·exit은 만들지 않고 e2e_contract 함수에 넘긴다(C-125-1).",
  "exports": [
    "ExecutionStep", "build_execution_plan", "step_role_of", "required_executor_types",
    "observed_executors", "assertion_summary", "build_verdict_input",
    "verify_step_ids_by_executor", "missing_assertion_results",
    "core_ui_assertion_ids", "api_substituted_core_ui_assertions", "ACTION_KEYS", "ASSERTION_KEYS",
    "static_executor_contract_error"
  ]
}

lib.e2e.scenario_adapter — 시나리오 파일은 동결돼 있다(`test-scenario.json` locked).
따라서 이 모듈은 **읽기 전용 어댑터**이며 spec존 필드를 보태거나 고쳐 쓰지 않는다.
`scenario.py`의 `_normalize_scenario`에 필드를 추가하지도 않는다(§C.2 [MUST]).

판정 경계: 이 모듈은 `passed`·`status`·`exit`을 결정하지 않는다. assertion의
`expected == actual` 비교는 executor가 수행하고 최종 게이트는
`e2e_contract.validate_pass_requirements`가 수행한다 — 어댑터는 둘 사이의 형태만 맞춘다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from lib import e2e_contract
from lib.e2e import executors as e2e_executors


@dataclass
class ExecutionStep:
    """시나리오 `steps[]` 1건을 executor 호출로 옮긴 형태."""

    id: str
    executor: str
    step_role: str = e2e_executors.STEP_ROLE_VERIFY
    action: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    def as_action(self) -> Dict[str, Any]:
        """§B.3 `act` 입력의 `action` 객체. `step_role`은 항상 실린다(C-EXE-2)."""
        return dict(self.action, step_role=self.step_role)


def step_role_of(step: Mapping[str, Any]) -> str:
    """§A.4 `step_role` — 기본값은 `verify`다.

    setup·cleanup을 기본값으로 흘려보내면 §C.4의 "핵심 UI 행동을 verify API로 대체"
    판정이 무너지므로, 알 수 없는 값은 조용히 넘기지 않고 `verify`로 떨어뜨린 뒤
    호출자가 구분할 수 있게 원문을 `raw`에 남긴다.
    """
    role = step.get("step_role")
    return role if role in e2e_executors.STEP_ROLES else e2e_executors.STEP_ROLE_VERIFY


# §B.2 `act`·§B.3 `act`가 각각 요구하는 **행동 어휘**. executor 종류마다 다르므로 한
# 목록으로 합치지 않는다 — 합치면 api step에 browser 키가, browser step에 api 키가 섞여
# 들어가고, driver·executor는 자기 계약에 없는 필드를 받게 된다.
#
# 이 표가 비어 있던 것이 W-5가 올린 blocker의 원인이다. browser step의 `kind`가 전달되지
# 않으면 driver는 8연산을 다 갖추고도 **수행할 행동이 없어** `agent_browser_action_kind_absent`
# 로 끝난다(`drivers/agent_browser.py` `op_act`). 어휘는 driver 쪽 계약이 소유하며 여기서는
# 시나리오 원소에서 그 이름들을 그대로 옮기기만 한다.
ACTION_KEYS: Dict[str, Tuple[str, ...]] = {
    # §B.3 `act` — `{method, url, headers, body, timeout_ms}` + 후속 관측 대상.
    "api": ("method", "url", "headers", "body", "timeout_ms", "observe_url"),
    # §B.2 `act` — `{kind, target, value?}`. `kind`는 `_ACT_SUBCOMMANDS`의 키이고
    # `target`은 셀렉터·URL, `value`는 fill·type·select의 입력값이다.
    "browser": ("kind", "target", "value"),
    # human executor는 `act`를 갖지 않는다(§B.3 — probe·handoff·resume 3연산).
    "human": (),
}

# §B.2 `assert` 입력이 assertion 원소에서 읽는 키. assertion은 step과 달리 dict 전체가
# 그대로 넘어가지만, 어느 키가 계약 표면인지 한 곳에 적어 둔다(§A.5·C-DRV-4).
ASSERTION_KEYS: Tuple[str, ...] = (
    "id", "verifier", "expected", "target", "match", "attribute", "script",
    "field", "url", "method", "source_seq", "timeout_ms", "executor",
)


def build_execution_plan(scenario: Mapping[str, Any]) -> List[ExecutionStep]:
    """시나리오 `steps[]`를 실행 계획으로 옮긴다. 순서는 시나리오 순서 그대로다.

    `action`에 담기는 키는 `ACTION_KEYS`가 executor 종류별로 정한다 — 시나리오가 쓴
    어휘를 그대로 옮기며 번역하거나 추측해 채우지 않는다.
    """
    plan: List[ExecutionStep] = []
    for index, raw in enumerate(scenario.get("steps") or [], start=1):
        if not isinstance(raw, Mapping):
            continue
        executor = str(raw.get("executor") or "")
        if executor not in e2e_contract.EXECUTOR_TYPES:
            raise e2e_executors.ExecutorError(
                "scenario_step_executor_invalid",
                f"steps[{index}].executor={executor!r} is not one of {e2e_contract.EXECUTOR_TYPES}",
            )
        action = {key: raw[key] for key in ACTION_KEYS.get(executor, ()) if key in raw}
        plan.append(
            ExecutionStep(
                id=str(raw.get("id") or f"step-{index}"),
                executor=executor,
                step_role=step_role_of(raw),
                action=action,
                raw=dict(raw),
            )
        )
    return plan


def required_executor_types(scenario: Mapping[str, Any]) -> Tuple[str, ...]:
    """profile이 요구하는 executor 종류. 행렬은 `e2e_contract`가 소유한다(§C.2)."""
    profile = str(scenario.get("profile") or "")
    try:
        return tuple(e2e_contract.executor_contract(profile)["required"])
    except KeyError:
        return ()


def allowed_executor_types(scenario: Mapping[str, Any]) -> Tuple[str, ...]:
    profile = str(scenario.get("profile") or "")
    try:
        return tuple(e2e_contract.executor_contract(profile)["allowed"])
    except KeyError:
        return ()


def verify_step_ids_by_executor(plan: Sequence[ExecutionStep]) -> Dict[str, List[str]]:
    """§C.4 집행 입력 — `step_role="verify"`인 step을 executor별로 모은다.

    setup·cleanup은 여기에 들어오지 않는다. "핵심 UI 행동이 verify API step만으로
    충족되는가"를 판정하려면 검증 대상 step만 봐야 하기 때문이다(TD-17, R-12).
    """
    grouped: Dict[str, List[str]] = {}
    for step in plan:
        if step.step_role != e2e_executors.STEP_ROLE_VERIFY:
            continue
        grouped.setdefault(step.executor, []).append(step.id)
    return grouped


def observed_executors(plan: Sequence[ExecutionStep], executed_step_ids: Sequence[str]) -> List[str]:
    """실제로 **동작한** executor 종류. 시나리오 선언을 베껴 쓰지 않는다.

    `validate_pass_requirements`가 이 목록을 `EXECUTOR_MATRIX`와 대조하므로, 실행되지
    않은 executor를 여기에 넣으면 §C.4의 실행 후 집행이 무력해진다.
    """
    executed = set(str(item) for item in executed_step_ids)
    seen: List[str] = []
    for step in plan:
        if step.id in executed and step.executor not in seen:
            seen.append(step.executor)
    return seen


def missing_assertion_results(
    scenario: Mapping[str, Any], results: Sequence[Mapping[str, Any]]
) -> List[str]:
    """시나리오가 선언했지만 결과가 없는 assertion id."""
    declared = [
        str(item.get("id"))
        for item in (scenario.get("assertions") or [])
        if isinstance(item, Mapping) and item.get("id") is not None
    ]
    observed = {str(item.get("id")) for item in results if isinstance(item, Mapping)}
    return [item for item in declared if item not in observed]


def assertion_summary(
    scenario: Mapping[str, Any], results: Sequence[Mapping[str, Any]]
) -> Dict[str, int]:
    """§A.1 `assertion_summary` — `{passed, failed, missing}`."""
    missing = missing_assertion_results(scenario, results)
    passed = sum(1 for item in results if isinstance(item, Mapping) and item.get("passed") is True)
    failed = sum(1 for item in results if isinstance(item, Mapping) and item.get("passed") is not True)
    return {"passed": passed, "failed": failed, "missing": len(missing)}


def build_verdict_input(
    scenario: Mapping[str, Any],
    *,
    status: str,
    run_id: str,
    assertion_results: Sequence[Mapping[str, Any]],
    observed_executor_types: Sequence[str],
    observed_evidence: Sequence[str],
    fidelity: Optional[str] = None,
) -> Dict[str, Any]:
    """`e2e_contract.build_verdict()`가 먹는 입력을 조립한다.

    [MUST] 여기서 `status`를 만들지 않는다 — 호출자가 실행 결과로 이미 정한 값을 싣고,
    `pass` 승격 여부는 `build_verdict` → `validate_pass_requirements`가 결정한다
    (C-125-1, §C.2 "자체 pass 판정" 금지).
    """
    return {
        "status": status,
        "run_id": run_id,
        "profile": scenario.get("profile"),
        "surface_kind": scenario.get("surface_kind"),
        "actors": list(scenario.get("actors") or []),
        "assertions": [dict(item) for item in (scenario.get("assertions") or []) if isinstance(item, Mapping)],
        "assertion_results": [dict(item) for item in assertion_results],
        "required_evidence": [str(item) for item in (scenario.get("required_evidence") or [])],
        "observed_evidence": [str(item) for item in observed_evidence],
        "observed_executors": list(observed_executor_types),
        "fidelity": fidelity or scenario.get("required_fidelity") or "mock",
    }


# ─── §C.4 surface fidelity 집행 입력 (TD-17·R-12·AC-8) ───────────────────────
#
# 집행은 두 지점이다. 아래 두 함수가 각 지점의 **입력**을 만든다 — 판정 문자열
# (`surface_profile_mismatch`·status·exit)은 전부 `e2e_contract`가 돌려준 값을 그대로
# 통과시키고 이 모듈이 리터럴로 짓지 않는다(C-125-1, C-8).

# 핵심 UI 행동 표시. 시나리오 파일은 동결돼 있으므로(test-scenario.json locked) 신규
# 최상위 필드를 만들지 않고 기존 원소의 표시 필드를 읽기만 한다(TD-12).
CORE_UI_MARKERS: Tuple[str, ...] = ("core_ui_behavior", "core_ui")


def _is_core_ui(item: Mapping[str, Any]) -> bool:
    return any(bool(item.get(marker)) for marker in CORE_UI_MARKERS)


def core_ui_assertion_ids(scenario: Mapping[str, Any]) -> List[str]:
    """`assertions[]` 중 핵심 UI 행동을 검증하는 원소의 id.

    표시가 하나도 없으면 빈 목록이다 — 표시 없는 시나리오를 "전부 핵심 UI"로 확대하면
    setup·cleanup API까지 우회로 몰리게 되고, 그것은 §C.4가 명시적으로 금지한 판정이다
    ("setup·cleanup 용도 API 호출은 우회로 판정되지 않는다").
    """
    return [
        str(item.get("id"))
        for item in (scenario.get("assertions") or [])
        if isinstance(item, Mapping) and item.get("id") is not None and _is_core_ui(item)
    ]


def api_substituted_core_ui_assertions(
    scenario: Mapping[str, Any],
    plan: Sequence[ExecutionStep],
    assertion_results: Sequence[Mapping[str, Any]],
) -> List[str]:
    """핵심 UI assertion이 `step_role="verify"`인 **api** step만으로 충족된 id 목록.

    §C.4가 요구하는 판정의 입력이다. 세 가지를 구분한다.

    - `step_role`이 `setup`·`cleanup`인 api step은 후보에서 빠진다
      (`verify_step_ids_by_executor`가 `verify`만 모은다) — setup·cleanup API를 우회로
      판정하지 않기 위해서다.
    - 같은 assertion을 browser verify step이 함께 충족했다면 대체가 아니다.
    - 어떤 step이 충족했는지 결과가 말하지 않으면(`observed_via_step`·`executor` 모두
      부재) 대체로 단정하지 않는다 — 근거 없이 충실도를 깎지 않는다.
    """
    core = set(core_ui_assertion_ids(scenario))
    if not core:
        return []
    grouped = verify_step_ids_by_executor(plan)
    api_verify = set(grouped.get("api", ()))
    browser_verify = set(grouped.get("browser", ()))
    substituted: List[str] = []
    for item in assertion_results:
        if not isinstance(item, Mapping):
            continue
        assertion_id = str(item.get("id"))
        if assertion_id not in core:
            continue
        via = item.get("observed_via_step")
        if via is not None:
            if str(via) in api_verify and str(via) not in browser_verify:
                substituted.append(assertion_id)
            continue
        # step 참조가 없으면 결과가 밝힌 executor로 판정한다. browser verify step이
        # 하나도 없는 run에서 api가 충족했다면 그것은 대체다.
        if str(item.get("executor") or "") == "api" and not browser_verify:
            substituted.append(assertion_id)
    return substituted


def static_executor_contract_error(scenario: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    """§C.4 집행 1 — 실행 **전** executor contract 대조 결과. 위반이 없으면 `None`.

    실행 전에 확정할 수 있는 축은 둘뿐이다. 각 축의 판정은 이미 `e2e_contract`가
    소유하므로(§C.2 "pass 게이트") 그 함수를 그대로 호출하고 결과를 통과시킨다 —
    `status`·`error` 문자열을 이 모듈이 리터럴로 짓지 않는다(C-125-1).

    1. profile ↔ surface_kind 축: `validate_surface_match`.
    2. profile ↔ 선언된 `steps[].executor` 축: `validate_pass_requirements`에
       선언 executor를 `observed_executors`로 넘겨 `EXECUTOR_MATRIX`와 대조시킨다.
       `browser` profile에 browser step이 없으면 여기서 걸린다.

    assertion·증적 축은 실행 전에 성립할 수 없으므로 쓰지 않는다. 그래서 2번은
    `detail`이 executor 키를 담은 경우에만 통과시킨다 — 같은 함수가 뒤이어 내는
    assertion·증적 판정을 실행 전 거부로 둔갑시키지 않기 위해서다.
    """
    profile = scenario.get("profile")
    if profile not in e2e_contract.PROFILES:
        # 미지의 profile은 이 게이트의 대상이 아니다. 계약에 없는 판정을 지어내지
        # 않고 상위의 시나리오 계약 검증(`validate_scenario_contract`)에 맡긴다(C-8).
        return None

    surface = e2e_contract.validate_surface_match(
        str(profile), scenario.get("surface_kind"), list(scenario.get("actors") or [])
    )
    if not surface.get("ok"):
        return dict(surface)

    declared = [
        step.get("executor")
        for step in (scenario.get("steps") or [])
        if isinstance(step, Mapping)
    ]
    check = e2e_contract.validate_pass_requirements(
        {
            "profile": profile,
            "surface_kind": scenario.get("surface_kind"),
            "actors": list(scenario.get("actors") or []),
        },
        {"profile": profile, "observed_executors": declared},
    )
    detail = check.get("detail")
    if not check.get("ok") and isinstance(detail, Mapping) and (
        detail.get("missing_executors") or detail.get("disallowed_executors")
    ):
        return dict(check)
    return None
