"""
@header {
  "module": "drivers",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T05 Browser driver 계약 — probe·open·snapshot·act·wait·assert·capture·close 8연산 JSON 입출력 계약(CONTRACT.md §B.2), session 후보 순서 resolver, driver manifest(§A.15) semver 게이트, §A.8 probe 결과 정규화와 probe.json 기록. 구체 driver 구현(agent-browser·cmux)은 여기 등록만 되고 별도 모듈이 소유한다.",
  "exports": [
    "DRIVER_OPERATIONS", "CAPABILITY_KEYS", "CANDIDATE_ORDER", "SESSION_MODES",
    "DriverError", "BrowserDriver", "default_capabilities", "load_manifest",
    "normalize_probe_result", "parse_semver", "compare_versions",
    "meets_minimum_version", "in_tested_range", "register_driver",
    "registered_drivers", "resolve_candidates", "write_probe_json"
  ]
}

lib.e2e.drivers — CONTRACT.md §B.2의 JSON 입출력이 계약 표면이며 클래스는 그 계약을
파이썬에서 호출하기 위한 얇은 배선이다(제안서 §7.6). 다음 규칙은 이 모듈이 집행한다.

- C-DRV-1 [MUST]: `wait`의 `wait_kind`는 필수 인자다. 생략하면 driver를 실행하지 않고
  오류를 반환한다 — `e2e_contract.py`의 `fail`/`infra_error` 분기를 살리는 유일한 경로다.
- C-DRV-2 [MUST]: 가용성은 `probe` 반환값만으로 판정한다. `uname`·`--version` 파싱·번들
  파일 존재로 추정하지 않는다(NR-7). `probed == false`인 capability는 보수적으로
  `available=false`다(§A.8 [MUST]).
- C-DRV-3: 후보 순서는 `agent-browser/orca-managed` → `cmux/owned-surface` →
  `agent-browser/standalone` → `playwright(opt-in)`이다(TRD.md TD-11).
- §A.15 [MUST]: 버전 비교는 문자열 비교가 아니라 semver 비교다. `minimum_version` 미만
  binary는 **probe 없이** 제외하고 `candidates[].excluded_by="minimum_version"`으로 남긴다.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from lib.e2e import evidence as e2e_evidence

SCHEMA_VERSION = "2.0"
MANIFEST_SCHEMA_VERSION = "1.0"

# CONTRACT.md §B.2 8연산. 이름은 계약 표면이므로 여기서만 정의한다.
DRIVER_OPERATIONS: Tuple[str, ...] = (
    "probe",
    "open",
    "snapshot",
    "act",
    "wait",
    "assert",
    "capture",
    "close",
)

# §A.8 capabilities key 집합 — 미확인 상태에서도 6개 키가 모두 존재해야 한다.
CAPABILITY_KEYS: Tuple[str, ...] = (
    "snapshot",
    "screenshot",
    "console",
    "errors",
    "network_har",
    "isolated_profile",
)

# §A.4 wait_kind enum.
WAIT_KINDS: Tuple[str, ...] = ("navigation_ready", "transport", "assertion_condition")

# §A.1.1 session_mode enum.
SESSION_MODES: Tuple[Optional[str], ...] = ("orca-managed", "owned-surface", "standalone", None)

# C-DRV-3 후보 순서. `opt_in=True`인 후보는 시나리오가 명시적으로 요구할 때만 시도한다.
CANDIDATE_ORDER: Tuple[Dict[str, Any], ...] = (
    {"driver": "agent-browser", "session_mode": "orca-managed", "opt_in": False},
    {"driver": "cmux", "session_mode": "owned-surface", "opt_in": False},
    {"driver": "agent-browser", "session_mode": "standalone", "opt_in": False},
    # ADD-1: ego-lite는 **부분 driver**다 — `ego-browser-tool`의 `smoke`가 open과 텍스트
    # assert를 융합해 제공할 뿐 `act`·`wait`·`snapshot`·`capture`가 없다. 이것을 앞에
    # 두면 UI 조작이 필요한 시나리오에서도 먼저 `selected`되고, 실행 도중
    # `driver_operation_unimplemented`로 `blocked`가 된다 — 더 완전한 driver를 가리는
    # 기본값이다. 현재 후보 게이트는 capability(§A.8.1 6키)만 보고 "이 시나리오가 `act`를
    # 쓰는가"를 표현할 수단이 없으므로, 순서로 방어한다.
    #
    # smoke 형태(열고 텍스트 확인)만 도는 프로젝트는 `resolve_candidates(candidate_order=…)`
    # 또는 제안서 §7의 `order.json`으로 1순위에 올릴 수 있다. 태스크 129가 legacy
    # `integration` 경로에 둔 Ego Lite 우선순위는 그 경로에서 그대로 유지된다 — 그쪽은
    # 애초에 smoke 전용 경로다.
    {"driver": "ego-lite", "session_mode": "standalone", "opt_in": False},
    {"driver": "playwright", "session_mode": "standalone", "opt_in": True},
)

_MANIFEST_PATH = Path(__file__).with_name("manifest.json")

# §A.1.2 outcome enum.
OUTCOME_SELECTED = "selected"
OUTCOME_EXCLUDED = "excluded"
OUTCOME_PROVIDER_UNAVAILABLE = "provider_unavailable"
OUTCOME_INFRA_ERROR = "infra_error"

EXCLUDED_BY_MINIMUM_VERSION = "minimum_version"
EXCLUDED_BY_CAPABILITY_MISSING = "capability_missing"

_SEMVER_PATTERN = re.compile(r"^\s*v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-+].*)?\s*$")


class DriverError(Exception):
    """driver 계약 위반·실행 오류. `detail_code`는 후보가 반환한 원문을 그대로 실는다."""

    def __init__(self, detail_code: str, detail: str = ""):
        super().__init__(detail or detail_code)
        self.detail_code = detail_code
        self.detail = detail or detail_code


# ─── manifest (§A.15) ────────────────────────────────────────────────────────
def load_manifest(path: Optional[str] = None) -> Dict[str, Any]:
    """driver manifest를 읽는다. 버전 정책의 단일 SSOT이며 리터럴을 복제하지 않는다."""
    manifest_path = Path(path) if path else _MANIFEST_PATH
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DriverError("driver_manifest_unreadable", f"{manifest_path}: {exc}") from exc
    if data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise DriverError(
            "driver_manifest_schema_mismatch",
            f"expected schema_version {MANIFEST_SCHEMA_VERSION!r}, got {data.get('schema_version')!r}",
        )
    drivers = data.get("drivers")
    if not isinstance(drivers, Mapping) or not drivers:
        raise DriverError("driver_manifest_invalid", "drivers must be a non-empty object")
    for name, policy in drivers.items():
        missing = [key for key in ("minimum_version", "tested_range", "ci_pin") if key not in (policy or {})]
        if missing:
            raise DriverError("driver_manifest_invalid", f"{name}: missing {missing}")
    return data


def parse_semver(version: Any) -> Optional[Tuple[int, int, int]]:
    """`v1.2.3` / `1.2` / `1` 형태를 `(major, minor, patch)`로 만든다. 해석 불가면 None."""
    if version is None:
        return None
    match = _SEMVER_PATTERN.match(str(version))
    if not match:
        return None
    return tuple(int(part) if part else 0 for part in match.groups())  # type: ignore[return-value]


def compare_versions(left: Any, right: Any) -> int:
    """semver 비교. 문자열 비교를 쓰지 않는다(§A.15 [MUST]). 해석 불가는 DriverError."""
    left_parts, right_parts = parse_semver(left), parse_semver(right)
    if left_parts is None or right_parts is None:
        raise DriverError("driver_version_unparsable", f"cannot compare {left!r} and {right!r}")
    return (left_parts > right_parts) - (left_parts < right_parts)


def meets_minimum_version(version: Any, minimum: Any) -> bool:
    return compare_versions(version, minimum) >= 0


def in_tested_range(version: Any, tested_range: Any) -> bool:
    """`0.27.x`·`1.40.x - 1.55.x`·`*` 표기를 판정한다. 판정 불가면 보수적으로 False."""
    spec = str(tested_range or "").strip()
    if spec in {"*", ""}:
        return True
    parsed = parse_semver(version)
    if parsed is None:
        return False
    if " - " in spec:
        low, high = (part.strip() for part in spec.split(" - ", 1))
        return _range_floor(low) <= parsed <= _range_ceiling(high)
    return _range_floor(spec) <= parsed <= _range_ceiling(spec)


def _range_floor(spec: str) -> Tuple[int, int, int]:
    parsed = parse_semver(spec.replace("x", "0").replace("*", "0"))
    return parsed or (0, 0, 0)


def _range_ceiling(spec: str) -> Tuple[int, int, int]:
    cleaned = spec.strip()
    parts = cleaned.split(".")
    ceiling: List[int] = []
    for part in parts:
        if part in {"x", "X", "*"}:
            ceiling.append(1 << 30)
        else:
            try:
                ceiling.append(int(part.lstrip("v")))
            except ValueError:
                return (1 << 30, 1 << 30, 1 << 30)
    while len(ceiling) < 3:
        ceiling.append(1 << 30)
    return (ceiling[0], ceiling[1], ceiling[2])


# ─── §A.8 probe 결과 ─────────────────────────────────────────────────────────
def default_capabilities() -> Dict[str, Dict[str, Any]]:
    """미확인 상태의 §A.8.1 capability 표. 6개 키가 항상 존재한다."""
    return {key: {"available": False, "route": "exec", "probed": False} for key in CAPABILITY_KEYS}


def normalize_probe_result(raw: Any, *, driver: str, session_mode: Optional[str]) -> Dict[str, Any]:
    """후보의 `probe` 반환값을 §A.8 객체로 정규화한다.

    [MUST] `probed == false`인 capability는 보수적으로 `available=false`다. help 문자열·
    번들 파일 존재로 승격하지 않는다(§A.8, 제안서 §7.7).
    """
    payload: Mapping[str, Any] = raw if isinstance(raw, Mapping) else {}
    capabilities = default_capabilities()
    raw_caps = payload.get("capabilities")
    if isinstance(raw_caps, Mapping):
        for key in CAPABILITY_KEYS:
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
        "driver": driver,
        "session_mode": session_mode,
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
        if name in CAPABILITY_KEYS and not (capabilities.get(name) or {}).get("available", False)
    ]


# ─── driver 레지스트리 ───────────────────────────────────────────────────────
_REGISTRY: Dict[Tuple[str, Optional[str]], Callable[..., "BrowserDriver"]] = {}


def register_driver(driver: str, session_mode: Optional[str], factory: Callable[..., "BrowserDriver"]) -> None:
    """구체 driver 구현을 후보 키로 등록한다(W-5 agent-browser·W-6 cmux가 호출)."""
    _REGISTRY[(driver, session_mode)] = factory


def registered_drivers() -> Dict[Tuple[str, Optional[str]], Callable[..., "BrowserDriver"]]:
    return dict(_REGISTRY)


class BrowserDriver:
    """§B.2 8연산의 파이썬 배선. 구체 driver가 각 연산을 구현한다.

    `dispatch()`는 연산 이름과 §B.2 필수 입력만 검증하고 결과를 그대로 통과시킨다 —
    후보가 반환한 값을 하네스가 재해석하지 않는다(NR-7).
    """

    name: str = "abstract"
    session_mode: Optional[str] = None

    def dispatch(self, operation: str, payload: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        if operation not in DRIVER_OPERATIONS:
            raise DriverError("driver_unknown_operation", f"{operation!r} is not one of {DRIVER_OPERATIONS}")
        request: Mapping[str, Any] = payload or {}
        if operation == "wait":
            # C-DRV-1 [MUST]: wait_kind 없이는 실행하지 않는다.
            wait_kind = request.get("wait_kind")
            if wait_kind not in WAIT_KINDS:
                raise DriverError(
                    "driver_wait_kind_required",
                    f"wait requires wait_kind in {WAIT_KINDS}, got {wait_kind!r}",
                )
        handler = getattr(self, f"op_{operation}" if operation != "assert" else "op_assert", None)
        if handler is None:
            raise DriverError("driver_operation_unimplemented", f"{self.name}: {operation}")
        return handler(dict(request))

    # 구체 driver가 덮어쓴다. 기본 구현은 미구현을 명시적으로 알린다.
    def op_probe(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise DriverError("driver_operation_unimplemented", f"{self.name}: probe")

    def op_open(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise DriverError("driver_operation_unimplemented", f"{self.name}: open")

    def op_snapshot(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise DriverError("driver_operation_unimplemented", f"{self.name}: snapshot")

    def op_act(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise DriverError("driver_operation_unimplemented", f"{self.name}: act")

    def op_wait(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise DriverError("driver_operation_unimplemented", f"{self.name}: wait")

    def op_assert(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise DriverError("driver_operation_unimplemented", f"{self.name}: assert")

    def op_capture(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise DriverError("driver_operation_unimplemented", f"{self.name}: capture")

    def op_close(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise DriverError("driver_operation_unimplemented", f"{self.name}: close")


# ─── 후보 해석 (§A.1.2) ──────────────────────────────────────────────────────
def resolve_candidates(
    *,
    required_capabilities: Sequence[str] = (),
    runtime_context: Optional[Mapping[str, Any]] = None,
    manifest: Optional[Mapping[str, Any]] = None,
    registry: Optional[Mapping[Tuple[str, Optional[str]], Callable[..., "BrowserDriver"]]] = None,
    opt_in_drivers: Sequence[str] = (),
    candidate_order: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """후보 순서대로 §A.1.2 `candidates[]`와 §A.8 probe 기록을 만든다.

    반환: `(candidates, probes)`. `outcome=selected`는 최대 1개이며, 하나가 선택되면
    그 뒤 후보는 시도하지 않는다. 전환 허용 판정은 여기서 만들지 않는다 — 미가용 후보는
    `provider_unavailable`로만 기록하고, 실행 오류는 `infra_error`로 기록해 호출자가
    `can_try_next_provider()`로 판단하게 한다(TASK.md C-3, §C.7).
    """
    policies = (manifest or load_manifest()).get("drivers") or {}
    available_drivers = dict(registry) if registry is not None else registered_drivers()
    candidates: List[Dict[str, Any]] = []
    probes: List[Dict[str, Any]] = []
    selected_found = False
    order = 0

    # ADD-1: 순서를 인자로 받는다. 기본값은 `CANDIDATE_ORDER`이고, 호출자가 넘기면 그것을
    # 쓴다. 새 후보를 앞에 넣을 때 순서를 전제한 테스트가 함께 깨지는 것을 막고,
    # 프로젝트별 재정의(제안서 §7 `order.json`)의 접합점을 미리 연다.
    for entry in (candidate_order if candidate_order is not None else CANDIDATE_ORDER):
        driver_name = entry["driver"]
        session_mode = entry["session_mode"]
        if entry["opt_in"] and driver_name not in set(opt_in_drivers):
            continue
        order += 1
        record = _blank_candidate(order, driver_name, session_mode)

        if selected_found:
            record["outcome"] = OUTCOME_PROVIDER_UNAVAILABLE
            record["reason"] = "not_attempted_after_selection"
            candidates.append(record)
            continue

        factory = available_drivers.get((driver_name, session_mode))
        if factory is None:
            record["outcome"] = OUTCOME_PROVIDER_UNAVAILABLE
            record["reason"] = "no_registered_driver"
            candidates.append(record)
            continue

        try:
            driver = factory(runtime_context=dict(runtime_context or {}))
        except DriverError as exc:
            record["outcome"] = OUTCOME_INFRA_ERROR
            record["reason"] = exc.detail_code
            candidates.append(record)
            break

        binary_path = getattr(driver, "binary_path", None)
        resolution_source = getattr(driver, "resolution_source", None)
        declared_version = getattr(driver, "declared_version", None)
        record["binary_path"] = binary_path
        record["resolution_source"] = resolution_source

        policy = policies.get(driver_name) or {}
        minimum = policy.get("minimum_version")
        # §A.15 [MUST]: minimum_version 미만 binary는 probe 없이 제외한다.
        if declared_version is not None and minimum is not None:
            try:
                below_minimum = not meets_minimum_version(declared_version, minimum)
            except DriverError:
                below_minimum = False
            record["version"] = str(declared_version)
            if below_minimum:
                record["outcome"] = OUTCOME_EXCLUDED
                record["excluded_by"] = EXCLUDED_BY_MINIMUM_VERSION
                record["reason"] = f"below_minimum_version:{minimum}"
                candidates.append(record)
                continue

        try:
            raw_probe = driver.dispatch(
                "probe",
                {
                    "runtime_context": dict(runtime_context or {}),
                    "required_capabilities": list(required_capabilities),
                },
            )
        except DriverError as exc:
            probe = normalize_probe_result(
                {"available": False, "unavailable_reason": exc.detail_code},
                driver=driver_name,
                session_mode=session_mode,
            )
            probes.append(probe)
            outside_tested_range = record["version"] is not None and not in_tested_range(
                record["version"], policy.get("tested_range")
            )
            # §A.15·§C.7: tested_range 밖 binary의 probe 실패는 excluded가 아니라
            # infra_error이며, 조용한 fallback 없이 중단한다.
            record["outcome"] = OUTCOME_INFRA_ERROR if outside_tested_range else OUTCOME_PROVIDER_UNAVAILABLE
            record["reason"] = exc.detail_code
            candidates.append(record)
            if record["outcome"] == OUTCOME_INFRA_ERROR:
                break
            continue

        probe = normalize_probe_result(raw_probe, driver=driver_name, session_mode=session_mode)
        probes.append(probe)
        record["version"] = probe.get("version") or record["version"]

        if not probe["available"]:
            record["outcome"] = OUTCOME_PROVIDER_UNAVAILABLE
            record["reason"] = probe.get("unavailable_reason")
            candidates.append(record)
            continue

        lacking = missing_capabilities(probe, required_capabilities)
        if lacking:
            record["outcome"] = OUTCOME_EXCLUDED
            record["excluded_by"] = EXCLUDED_BY_CAPABILITY_MISSING
            record["reason"] = f"missing_capabilities:{','.join(sorted(lacking))}"
            candidates.append(record)
            continue

        record["outcome"] = OUTCOME_SELECTED
        candidates.append(record)
        selected_found = True

    return candidates, probes


def _blank_candidate(order: int, driver: str, session_mode: Optional[str]) -> Dict[str, Any]:
    return {
        "order": order,
        "type": "browser",
        "driver": driver,
        "session_mode": session_mode,
        "binary_path": None,
        "resolution_source": None,
        "version": None,
        "outcome": OUTCOME_PROVIDER_UNAVAILABLE,
        "excluded_by": None,
        "reason": None,
    }


def write_probe_json(writer: "e2e_evidence.EvidenceWriter", probes: Sequence[Mapping[str, Any]]) -> str:
    """§A.8 probe 결과를 후보별 배열로 `probe.json`에 남긴다(MV-14 검사 대상)."""
    return writer.write_json(
        e2e_evidence.EVIDENCE_PATHS["probe"],
        {"schema_version": SCHEMA_VERSION, "probes": [dict(item) for item in probes]},
        kind="probe",
        observed=bool(probes),
    )


# ─── 내장 driver 등록 ────────────────────────────────────────────────────────
# 이 패키지 안의 driver 모듈은 import되는 순간 `register_driver()`로 자기를 등록한다.
# 등록이 일어나려면 누군가 그 모듈을 import해야 하므로, 등록 지점을 여기 한 곳에 둔다.
# 새 driver(W-6 `cmux`)는 아래 목록에 모듈명을 추가하기만 하면 된다.
#
# 이 블록은 **파일 맨 끝**에 있어야 한다. driver 모듈이 `from lib.e2e import drivers`로
# 이 패키지의 심볼(`BrowserDriver`·`register_driver`·enum)을 참조하므로, 그 시점에 위
# 정의가 모두 끝나 있어야 순환 import가 성립한다.
_BUILTIN_DRIVER_MODULES: Tuple[str, ...] = ("ego_lite", "agent_browser", "cmux")


def _load_builtin_drivers() -> None:
    """내장 driver 모듈을 import해 레지스트리에 등록시킨다.

    import 실패를 삼키지 않는다 — driver 모듈이 깨진 것은 후보 미가용(`provider_unavailable`)이
    아니라 결함이며, 조용히 넘기면 모든 후보가 `no_registered_driver`로만 보여 원인이
    가려진다. 실패는 `DriverError`로 이름을 달고 즉시 드러난다.
    """
    import importlib

    for module_name in _BUILTIN_DRIVER_MODULES:
        try:
            importlib.import_module(f"{__name__}.{module_name}")
        except ImportError as exc:
            raise DriverError("driver_module_import_failed", f"{module_name}: {exc}") from exc


_load_builtin_drivers()
