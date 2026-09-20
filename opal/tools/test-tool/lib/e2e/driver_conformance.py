"""
@header {
  "module": "driver_conformance",
  "layer": "util",
  "domain": "opal-tools",
  "description": "등록된 browser driver가 CONTRACT §B.2의 8연산을 실제 dispatch하고 최소 출력 형태를 충족하는지 검사한다. provider 부재와 부분 구현은 pass로 승격하지 않는다.",
  "exports": ["verify_driver_factory", "verify_registered_driver"]
}

lib.e2e.driver_conformance — 후보 선택과 독립된 등록 전 적합성 검사다. 정적 구현 여부만으로
통과시키지 않고 각 연산을 dispatch한다. probe가 provider_unavailable이면 부수효과 연산을
시도하지 않으며, 결과는 비통과로 유지한다.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from lib.e2e import drivers as e2e_drivers


_MINIMUM_OUTPUT_KEYS: Dict[str, Tuple[str, ...]] = {
    "probe": ("available", "capabilities"),
    "open": ("handle", "owned", "current_url"),
    "snapshot": ("snapshot", "current_url", "artifact_path"),
    "act": ("ok", "action_result", "current_url"),
    "wait": ("satisfied", "wait_kind", "elapsed_ms"),
    "assert": ("id", "expected", "actual", "passed"),
    "capture": ("artifacts", "redacted", "redaction_failed"),
    "close": ("closed", "released", "leaked"),
}


def _payload(operation: str, handle: Optional[str]) -> Dict[str, Any]:
    common = {"handle": handle, "page_id": handle}
    payloads: Dict[str, Dict[str, Any]] = {
        "probe": {"runtime_context": {}, "required_capabilities": []},
        "open": {"url": "about:blank", "isolation_key": "driver-conformance"},
        "snapshot": dict(common, label="conformance"),
        "act": dict(common, action={"kind": "reload", "target": "about:blank"}),
        "wait": dict(
            common,
            condition={"ms": 1},
            wait_kind="assertion_condition",
            timeout_ms=1000,
        ),
        "assert": dict(
            common,
            # agent-browser와 cmux가 함께 제공하는 최소 semantic verifier를 쓴다.
            # cmux는 URL verifier를 제공하지 않으므로 URL 단언을 쓰면 8연산을 구현한
            # driver도 synthetic payload 때문에 거짓 실패한다. about:blank의 빈 body는
            # 외부 서비스나 제품 상태에도 의존하지 않는다.
            assertion={
                "id": "driver-conformance",
                "verifier": "dom_text",
                "target": "body",
                "expected": "",
            },
        ),
        "capture": dict(common, evidence_spec=[]),
        "close": common,
    }
    return payloads[operation]


def _missing_output(operation: str, output: Any) -> Sequence[str]:
    if not isinstance(output, Mapping):
        return _MINIMUM_OUTPUT_KEYS[operation]
    # 일부 기존 driver는 open 시 contract handle과 함께 page_id를 쓰고, ego-lite의 과거
    # 응답은 url만 돌려준다. 적합성 스위트는 frozen B.2의 handle을 요구한다.
    return [key for key in _MINIMUM_OUTPUT_KEYS[operation] if key not in output]


def _unsuccessful_output(operation: str, output: Mapping[str, Any]) -> Optional[str]:
    """형태는 맞지만 synthetic conformance 동작을 완료하지 못한 응답을 구분한다."""
    if operation == "open" and not output.get("handle"):
        return "driver_output_invalid:handle"
    if operation == "act" and output.get("ok") is not True:
        return "driver_operation_unsuccessful:act"
    if operation == "wait" and output.get("satisfied") is not True:
        return "driver_operation_unsuccessful:wait"
    if operation == "assert" and output.get("passed") is not True:
        return "driver_operation_unsuccessful:assert"
    if operation == "capture" and output.get("redaction_failed") is True:
        return "driver_operation_unsuccessful:capture"
    if operation == "close" and (output.get("closed") is not True or output.get("leaked")):
        return "driver_operation_unsuccessful:close"
    return None


def verify_driver_factory(
    driver: str,
    session_mode: Optional[str],
    factory: Callable[..., e2e_drivers.BrowserDriver],
    *,
    runtime_context: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """factory 하나를 생성해 8연산을 순서대로 실제 실행한다."""
    result: Dict[str, Any] = {
        "driver": driver,
        "session_mode": session_mode,
        "outcome": "failed",
        "operations": [],
        "missing_operations": [],
    }
    try:
        instance = factory(runtime_context=dict(runtime_context or {}))
    except (e2e_drivers.DriverError, OSError) as exc:
        result.update(outcome="infra_error", detail_code=getattr(exc, "detail_code", type(exc).__name__))
        return result

    result["missing_operations"] = e2e_drivers.missing_operations(
        instance, e2e_drivers.DRIVER_OPERATIONS
    )
    handle: Optional[str] = None
    for operation in e2e_drivers.DRIVER_OPERATIONS:
        record: Dict[str, Any] = {"operation": operation, "executed": False, "ok": False}
        if operation in result["missing_operations"]:
            record["detail_code"] = "driver_operation_unimplemented"
            result["operations"].append(record)
            continue
        try:
            output = instance.dispatch(operation, _payload(operation, handle))
            record["executed"] = True
            if operation == "probe" and not bool(output.get("available")):
                record["detail_code"] = str(
                    output.get("unavailable_reason") or output.get("reason") or "provider_unavailable"
                )
                result["operations"].append(record)
                result.update(outcome="provider_unavailable", detail_code=record["detail_code"])
                return result
            missing_keys = list(_missing_output(operation, output))
            if missing_keys:
                record["detail_code"] = f"driver_output_missing:{','.join(missing_keys)}"
            else:
                unsuccessful = _unsuccessful_output(operation, output)
                if unsuccessful:
                    record["detail_code"] = unsuccessful
                else:
                    record["ok"] = True
                    if operation == "open":
                        handle = str(output.get("handle"))
        except e2e_drivers.DriverError as exc:
            record["executed"] = True
            record["detail_code"] = exc.detail_code
        except (OSError, ValueError, TypeError) as exc:
            record["executed"] = True
            record["detail_code"] = type(exc).__name__
        result["operations"].append(record)

    failures = [item for item in result["operations"] if not item["ok"]]
    if failures:
        result["detail_code"] = failures[0].get("detail_code") or "driver_conformance_failed"
        return result
    result["outcome"] = "pass"
    return result


def verify_registered_driver(
    driver: str,
    *,
    registry: Optional[Mapping[Tuple[str, Optional[str]], Callable[..., e2e_drivers.BrowserDriver]]] = None,
    runtime_context: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """이름이 같은 등록 variant를 모두 검사하고 하나라도 실패하면 전체를 거부한다."""
    available = dict(registry) if registry is not None else e2e_drivers.registered_drivers()
    matching = sorted(
        ((mode, factory) for (name, mode), factory in available.items() if name == driver),
        key=lambda item: str(item[0]),
    )
    if not matching:
        return {
            "ok": False,
            "command": "e2e driver-verify",
            "driver": driver,
            "required_operations": list(e2e_drivers.DRIVER_OPERATIONS),
            "outcome": "provider_unavailable",
            "detail_code": "driver_not_registered",
            "results": [],
        }
    results = [
        verify_driver_factory(driver, mode, factory, runtime_context=runtime_context)
        for mode, factory in matching
    ]
    ok = all(item["outcome"] == "pass" for item in results)
    if ok:
        outcome = "pass"
    elif any(item["outcome"] == "infra_error" for item in results):
        outcome = "infra_error"
    elif any(item["outcome"] == "failed" for item in results):
        # 이름이 같은 variant 하나가 실제 8연산 검사에서 실패했다면, 다른 variant의
        # provider 부재가 그 실행 실패를 가리면 안 된다.
        outcome = "failed"
    elif any(item["outcome"] == "provider_unavailable" for item in results):
        # 바이너리 부재를 conformance 실패나 pass로 뭉개지 않는다. 호출자가 실제
        # 연산 검사가 수행되지 못했다는 사실을 구조적으로 구분할 수 있어야 한다.
        outcome = "provider_unavailable"
    else:
        outcome = "failed"
    return {
        "ok": ok,
        "command": "e2e driver-verify",
        "driver": driver,
        "required_operations": list(e2e_drivers.DRIVER_OPERATIONS),
        "outcome": outcome,
        "results": results,
    }
