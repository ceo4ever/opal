"""
@header {
  "module": "executors",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T09·T10 API·Human executor 계약 — CONTRACT.md §B.3의 executor-op JSON 입출력 계약, executor 레지스트리와 §A.1.2 후보 해석, §A.4 actions.jsonl 행 조립(step_role 구분 포함), §A.8 형태 probe 정규화. 구체 executor 구현(api·human)은 여기 등록만 되고 별도 모듈이 소유한다.",
  "exports": [
    "API_OPERATIONS", "HUMAN_OPERATIONS", "STEP_ROLES", "ACTION_RESULTS",
    "API_CAPABILITY_KEYS", "HUMAN_CAPABILITY_KEYS",
    "ExecutorError", "Executor", "ActionLog",
    "default_capabilities", "normalize_probe_result",
    "register_executor", "registered_executors", "unregister_executor",
    "resolve_executor_candidates"
  ]
}

lib.e2e.executors — CONTRACT.md §B.3의 JSON 입출력이 계약 표면이며 클래스는 그 계약을
파이썬에서 호출하기 위한 얇은 배선이다(§B.2 driver 패키지와 같은 구조). 다음 규칙을
이 모듈이 집행한다.

- C-EXE-1 [MUST]: 가용성은 `probe` 반환값만으로 판정한다. binary 존재·설정 파일·help
  문자열로 추정하지 않으며 `probed == false`인 capability는 보수적으로
  `available=false`다(§A.8 [MUST], NR-7).
- C-EXE-2 [MUST]: `act`는 `step_role`(§A.4 `verify`|`setup`|`cleanup`)을 필수 입력으로
  받는다. 누락하면 executor를 실행하지 않고 오류를 반환한다 — §C.4 surface fidelity
  집행이 이 필드를 입력으로 쓰므로 기본값으로 얼버무리면 집행 근거가 사라진다.
- C-EXE-3 [MUST]: 증적은 executor가 직접 파일로 쓰지 않고 `lib/e2e/evidence.py` 관문을
  통해서만 발행한다(§A.12·§C.2, TRD.md TD-14).
- C-EXE-4: 미가용 후보는 `provider_unavailable`로만 기록하고 실행 오류는 `infra_error`로
  기록한다. 전환 허용 판정은 호출자가 `can_try_next_provider()`로 한다(TASK.md C-3, §C.7).

이 패키지는 OS 조건문을 갖지 않는다(§C.2 [MUST], TRD.md TD-16 — 분기는 process.py 한 곳).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from lib import e2e_contract

SCHEMA_VERSION = e2e_contract.E2E_CONTRACT_SCHEMA_VERSION

# CONTRACT.md §B.3 표 — API executor 6연산. 이름은 계약 표면이므로 여기서만 정의한다.
API_OPERATIONS: Tuple[str, ...] = ("probe", "prepare", "act", "assert", "capture", "cleanup")

# CONTRACT.md §B.3 표 — Human handoff 2연산 + 공통 probe.
HUMAN_OPERATIONS: Tuple[str, ...] = ("probe", "handoff", "resume")

# CONTRACT.md §A.4 `step_role` enum. 기본값은 `verify`이지만 `act` 입력에서는 명시를
# 요구한다(C-EXE-2) — 기록 시의 기본값과 입력 시의 필수는 별개다.
STEP_ROLE_VERIFY = "verify"
STEP_ROLE_SETUP = "setup"
STEP_ROLE_CLEANUP = "cleanup"
STEP_ROLES: Tuple[str, ...] = (STEP_ROLE_VERIFY, STEP_ROLE_SETUP, STEP_ROLE_CLEANUP)

# CONTRACT.md §A.4 `result` enum.
ACTION_RESULTS: Tuple[str, ...] = ("ok", "error")

# §A.8 형태를 따르는 executor별 capability 키. browser용 6키(§A.8.1)는 driver가 소유하며
# executor는 자기 표면의 키를 소유한다 — 남의 키 집합을 빌려 쓰면 probe 결과가 거짓말을 한다.
API_CAPABILITY_KEYS: Tuple[str, ...] = (
    "request",
    "response_capture",
    "state_verify",
    "fixture_namespace",
)
HUMAN_CAPABILITY_KEYS: Tuple[str, ...] = ("handoff", "resume", "submission_capture")

# §A.1.2 outcome enum — driver 패키지와 같은 값 집합을 쓴다.
OUTCOME_SELECTED = "selected"
OUTCOME_EXCLUDED = "excluded"
OUTCOME_PROVIDER_UNAVAILABLE = "provider_unavailable"
OUTCOME_INFRA_ERROR = "infra_error"

EXCLUDED_BY_CAPABILITY_MISSING = "capability_missing"

# §A.1.2 `resolution_source` enum 중 executor가 쓰는 값.
RESOLUTION_SOURCE_INPROCESS = "installed"


def now_iso() -> str:
    """§A.4·§A.5·§A.9가 요구하는 ISO-8601(UTC) 타임스탬프."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ExecutorError(Exception):
    """executor 계약 위반·실행 오류. `detail_code`는 후보가 반환한 원문을 그대로 싣는다."""

    def __init__(self, detail_code: str, detail: str = ""):
        super().__init__(detail or detail_code)
        self.detail_code = detail_code
        self.detail = detail or detail_code


# ─── §A.8 probe 결과 ─────────────────────────────────────────────────────────
def default_capabilities(keys: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """미확인 상태의 §A.8 capability 표. 선언한 키가 항상 전부 존재한다."""
    return {str(key): {"available": False, "route": "exec", "probed": False} for key in keys}


def normalize_probe_result(
    raw: Any,
    *,
    executor: str,
    capability_keys: Sequence[str],
) -> Dict[str, Any]:
    """executor의 `probe` 반환값을 §A.8 객체로 정규화한다(§B.3 `probe` 최소 출력).

    [MUST] `probed == false`인 capability는 보수적으로 `available=false`다(C-EXE-1).
    """
    payload: Mapping[str, Any] = raw if isinstance(raw, Mapping) else {}
    capabilities = default_capabilities(capability_keys)
    raw_caps = payload.get("capabilities")
    if isinstance(raw_caps, Mapping):
        for key in capability_keys:
            item = raw_caps.get(key)
            if not isinstance(item, Mapping):
                continue
            probed = bool(item.get("probed", False))
            route = item.get("route")
            capabilities[key] = {
                # 보수 처리: probe하지 않았으면 available은 무조건 false다.
                "available": bool(item.get("available", False)) and probed,
                "route": route if route in {"native", "exec"} else "exec",
                "probed": probed,
            }
    available = bool(payload.get("available", False))
    reason = payload.get("unavailable_reason")
    return {
        "executor": executor,
        "available": available,
        "version": payload.get("version"),
        # 후보가 반환한 error code 원문을 그대로 싣는다. 하네스가 재작문하지 않는다(NR-7).
        "unavailable_reason": None if available else (reason or "probe_reported_unavailable"),
        "capabilities": capabilities,
    }


def missing_capabilities(probe: Mapping[str, Any], required: Sequence[str]) -> List[str]:
    capabilities = probe.get("capabilities") or {}
    return [
        name
        for name in required
        if name in capabilities and not (capabilities.get(name) or {}).get("available", False)
    ]


# ─── §B.3 연산 배선 ──────────────────────────────────────────────────────────
class Executor:
    """§B.3 executor-op의 파이썬 배선. 구체 executor가 각 연산을 구현한다.

    `dispatch()`는 연산 이름과 §B.3 필수 입력만 검증하고 결과를 그대로 통과시킨다 —
    executor가 반환한 값을 하네스가 재해석하지 않는다(NR-7).
    """

    executor_type: str = "abstract"
    operations: Tuple[str, ...] = ()
    capability_keys: Tuple[str, ...] = ()
    declared_version: Optional[str] = None
    binary_path: Optional[str] = None
    resolution_source: Optional[str] = RESOLUTION_SOURCE_INPROCESS

    def dispatch(self, operation: str, payload: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        if operation not in self.operations:
            raise ExecutorError(
                "executor_unknown_operation",
                f"{operation!r} is not one of {self.operations}",
            )
        request: Mapping[str, Any] = payload or {}
        if operation == "act":
            # C-EXE-2 [MUST]: step_role 없이는 실행하지 않는다. §C.4 집행의 입력이다.
            action = request.get("action")
            step_role = (action or {}).get("step_role") if isinstance(action, Mapping) else None
            if step_role not in STEP_ROLES:
                raise ExecutorError(
                    "executor_step_role_required",
                    f"act requires action.step_role in {STEP_ROLES}, got {step_role!r}",
                )
        handler = getattr(self, f"op_{operation}" if operation != "assert" else "op_assert", None)
        if handler is None:
            raise ExecutorError(
                "executor_operation_unimplemented", f"{self.executor_type}: {operation}"
            )
        return handler(dict(request))


# ─── §A.4 actions.jsonl ──────────────────────────────────────────────────────
class ActionLog:
    """§A.4 `actions.jsonl` 행 누적기. 파일 쓰기는 하지 않는다(C-EXE-3).

    `seq`는 1부터 증가하며 §A.11 `api/requests.jsonl`·`api/responses.jsonl`이 이 값으로
    상호 참조한다. 행을 모아 두었다가 호출자가 `flush(writer)`로 증적 관문에 넘긴다.
    """

    def __init__(self) -> None:
        self._rows: List[Dict[str, Any]] = []

    def __len__(self) -> int:
        return len(self._rows)

    @property
    def next_seq(self) -> int:
        return len(self._rows) + 1

    def record(
        self,
        *,
        step_id: str,
        executor: str,
        action: str,
        result: str,
        elapsed_ms: int,
        step_role: str = STEP_ROLE_VERIFY,
        wait_kind: Optional[str] = None,
        request: Optional[Mapping[str, Any]] = None,
        response: Optional[Mapping[str, Any]] = None,
        error_code: Optional[str] = None,
        current_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """§A.4 1행을 만들어 누적하고 그 행을 돌려준다.

        `executor == "api"`이면 `request`·`response`가 조건부 필수다(§A.4 표). 누락은
        계약 위반이므로 조용히 `null`로 채우지 않고 오류로 드러낸다.
        """
        if result not in ACTION_RESULTS:
            raise ExecutorError("action_result_invalid", f"result must be one of {ACTION_RESULTS}")
        if step_role not in STEP_ROLES:
            raise ExecutorError("action_step_role_invalid", f"step_role must be one of {STEP_ROLES}")
        if executor == "api" and action not in {"prepare", "cleanup", "capture"}:
            if request is None or response is None:
                raise ExecutorError(
                    "action_api_request_response_required",
                    f"api action {action!r} requires both request and response (§A.4)",
                )
        row: Dict[str, Any] = {
            "seq": self.next_seq,
            "at": now_iso(),
            "step_id": str(step_id),
            "executor": str(executor),
            "step_role": step_role,
            "action": str(action),
            "wait_kind": wait_kind,
            "request": dict(request) if request is not None else None,
            "response": dict(response) if response is not None else None,
            "result": result,
            "error_code": error_code,
            "current_url": current_url,
            "elapsed_ms": int(elapsed_ms),
        }
        self._rows.append(row)
        return row

    def rows(self) -> List[Dict[str, Any]]:
        return [dict(row) for row in self._rows]

    def rows_with_role(self, step_role: str) -> List[Dict[str, Any]]:
        """§C.4 집행 입력 — setup·cleanup과 검증 대상(`verify`)을 구분해 돌려준다."""
        return [dict(row) for row in self._rows if row.get("step_role") == step_role]

    def flush(self, writer: Any) -> str:
        """증적 단일 관문으로 `actions.jsonl`을 발행한다(§A.12).

        행이 0개면 관측 증적으로 올리지 않는다 — 빈 파일로 pass 게이트를 통과시키지
        않기 위한 evidence.py의 규약을 그대로 따른다.
        """
        from lib.e2e import evidence as e2e_evidence

        return writer.write_jsonl(
            e2e_evidence.EVIDENCE_PATHS["action_log"],
            self.rows(),
            kind="action_log",
            observed=bool(self._rows),
        )


# ─── executor 레지스트리 ─────────────────────────────────────────────────────
_REGISTRY: Dict[str, Callable[..., Executor]] = {}


def register_executor(executor_type: str, factory: Callable[..., Executor]) -> None:
    """구체 executor 구현을 `EXECUTOR_TYPES` 키로 등록한다(api·human).

    driver 레지스트리(`lib/e2e/drivers`)와 별개다 — browser 후보의 순서·manifest 게이트는
    driver 쪽이 소유하고, 여기에는 `api`·`human`만 등록된다.
    """
    if executor_type not in e2e_contract.EXECUTOR_TYPES:
        raise ExecutorError(
            "executor_type_unknown",
            f"{executor_type!r} is not one of {e2e_contract.EXECUTOR_TYPES}",
        )
    _REGISTRY[executor_type] = factory


def unregister_executor(executor_type: str) -> None:
    _REGISTRY.pop(executor_type, None)


def registered_executors() -> Dict[str, Callable[..., Executor]]:
    return dict(_REGISTRY)


def resolve_executor_candidates(
    executor_types: Sequence[str],
    *,
    runtime_context: Optional[Mapping[str, Any]] = None,
    required_capabilities: Optional[Mapping[str, Sequence[str]]] = None,
    registry: Optional[Mapping[str, Callable[..., Executor]]] = None,
    start_order: int = 0,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """`api`·`human` 후보를 §A.1.2 `candidates[]` 원소로 열거한다.

    반환: `(candidates, probes)`. `outcome=selected`는 executor 종류마다 최대 1개이며,
    미등록·미가용은 `provider_unavailable`, 후보 실행 오류는 `infra_error`로 기록한다.
    전환 허용 판정은 여기서 만들지 않는다(C-EXE-4, TASK.md C-3).

    `start_order`는 browser 후보 뒤에 순번을 잇기 위한 오프셋이다 — 후보 배열 전체의
    `order`는 1부터 연속이어야 한다(§A.1.2).
    """
    available = dict(registry) if registry is not None else registered_executors()
    caps_by_type = dict(required_capabilities or {})
    candidates: List[Dict[str, Any]] = []
    probes: List[Dict[str, Any]] = []
    order = start_order

    for executor_type in executor_types:
        order += 1
        record = blank_candidate(order, executor_type)
        factory = available.get(executor_type)
        if factory is None:
            record["reason"] = "no_registered_executor"
            candidates.append(record)
            continue

        try:
            executor = factory(runtime_context=dict(runtime_context or {}))
        except ExecutorError as exc:
            record["outcome"] = OUTCOME_INFRA_ERROR
            record["reason"] = exc.detail_code
            candidates.append(record)
            # §C.7 — infra_error 이후 다음 후보를 시도하지 않는다.
            break

        record["binary_path"] = getattr(executor, "binary_path", None)
        record["resolution_source"] = getattr(executor, "resolution_source", None)
        required = list(caps_by_type.get(executor_type) or ())

        try:
            raw_probe = executor.dispatch(
                "probe",
                {
                    "runtime_context": dict(runtime_context or {}),
                    "required_capabilities": required,
                },
            )
        except ExecutorError as exc:
            probes.append(
                normalize_probe_result(
                    {"available": False, "unavailable_reason": exc.detail_code},
                    executor=executor_type,
                    capability_keys=getattr(executor, "capability_keys", ()),
                )
            )
            record["reason"] = exc.detail_code
            candidates.append(record)
            continue

        probe = normalize_probe_result(
            raw_probe,
            executor=executor_type,
            capability_keys=getattr(executor, "capability_keys", ()),
        )
        probes.append(probe)
        record["version"] = probe.get("version")

        if not probe["available"]:
            record["reason"] = probe.get("unavailable_reason")
            candidates.append(record)
            continue

        lacking = missing_capabilities(probe, required)
        if lacking:
            record["outcome"] = OUTCOME_EXCLUDED
            record["excluded_by"] = EXCLUDED_BY_CAPABILITY_MISSING
            record["reason"] = f"missing_capabilities:{','.join(sorted(lacking))}"
            candidates.append(record)
            continue

        record["outcome"] = OUTCOME_SELECTED
        candidates.append(record)

    return candidates, probes


def blank_candidate(order: int, executor_type: str) -> Dict[str, Any]:
    """§A.1.2 원소의 미시도 기본값. 필드는 전건 존재하며 값만 nullable이다."""
    return {
        "order": order,
        "type": executor_type,
        "driver": None,
        "session_mode": None,
        "binary_path": None,
        "resolution_source": None,
        "version": None,
        "outcome": OUTCOME_PROVIDER_UNAVAILABLE,
        "excluded_by": None,
        "reason": None,
    }
