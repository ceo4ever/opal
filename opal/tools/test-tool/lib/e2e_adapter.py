"""
@header {
  "module": "e2e_adapter",
  "layer": "util",
  "domain": "opal-tools",
  "description": "cmux 후보 결과를 공통 E2E contract verdict로 번역하는 integration adapter. cmux-tool 호출과 8연산 계약은 lib.e2e.drivers.cmux가 소유하고, 이 모듈은 tier 설정 판독·후보 결과 정규화·공통 판정 관문 소비만 한다.",
  "exports": [
    "run_integration"
  ],
  "depends": [
    "lib.e2e_contract",
    "lib.e2e.drivers.cmux (cmux-tool 호출·8연산 계약 소유)"
  ]
}

e2e_adapter — cmux 후보 결과 adapter.

[MUST] cmux 분기는 cmux-tool 에러코드 소비로만 — uname/cmux --version 하드코딩 분기 금지 (헌법 플랫폼 독립).
[MUST] provider_unavailable일 때만 다음 Browser 후보 전환을 허용한다.
[MUST] final status/exit/error/pass gate는 lib.e2e_contract 공통 계약을 소비한다.
[MUST] mode A — --surface 미전달(신규 surface 강제), B/C 재사용 금지

Legacy cmux-tool error vocabulary is accepted only as adapter input and normalized
through lib.e2e_contract.  New public JSON does not emit generic fallback,
escalated, escalate, or escalation keys.

W-6 이관 경계: cmux-tool 실행(경로 해석·subprocess·JSON 파싱)과 mode A 소유권 규칙,
`open`/`act`/`assert`/`close` 연산은 `lib.e2e.drivers.cmux`로 옮겼다. 여기 남은 것은
(1) tier 설정에서 cmux 후보 존재 판독, (2) cmux-tool error code → 공통 verdict 정규화,
(3) `build_verdict` 단일 관문 소비와 integration 응답 봉투다 — 즉 **판정**만 남았다.
"""

import pathlib
from typing import Any, Dict, List, Optional

from lib.e2e.drivers import cmux as cmux_driver
from lib.e2e.evidence import COMMON_REQUIRED_EVIDENCE
from lib.e2e_contract import build_verdict, normalize_legacy_verdict, status_to_error

# CONTRACT.md §A.1 `fidelity` enum 중 이 adapter가 발행할 수 있는 값. 증적이 불완전한
# run은 절대 real-usage로 기록하지 않는다(AC-6, S-6).
FIDELITY_MOCK = "mock"


# ─── legacy cmux-tool raw error buckets (input normalization only) ───────────
# 어휘의 SSOT는 후보를 실제로 실행하는 `lib.e2e.drivers.cmux`다. 이름과 값은 그대로
# 보존하되 복제하지 않는다 — 두 벌로 갈라지면 `~/.opal/tools/cmux-tool/lib/dispatch.sh`가
# 발행하는 code와 한쪽만 어긋나도 알아채지 못한다(cmux-tool 변경 0이 전제다).
FALLBACK_CODES = cmux_driver.FALLBACK_CODES
ESCALATE_CODES = cmux_driver.ESCALATE_CODES


def _evidence_block(observed: Optional[List[str]] = None, fidelity: str = FIDELITY_MOCK) -> Dict[str, Any]:
    """CONTRACT.md §A.1 공통 필수 증적 5종 요구와 실제 관측분을 함께 싣는다.

    required_evidence를 `semantic_assertion` 한 항목으로 고정하면 계약이 요구하는 5종이
    판정 관문에 전달되지 않는다(S-5). 관측분은 실제 수집된 것만 올린다 — 요구치를
    관측치로 베끼면 결손 자체가 보이지 않게 된다.
    """
    observed_list = list(observed or [])
    missing = [item for item in COMMON_REQUIRED_EVIDENCE if item not in observed_list]
    return {
        "required_evidence": list(COMMON_REQUIRED_EVIDENCE),
        "observed_evidence": observed_list,
        "missing_evidence": missing,
        "evidence_complete": not missing,
        # [MUST] 증적이 불완전하면 real-usage가 아니다(S-6).
        "fidelity": FIDELITY_MOCK if missing else fidelity,
    }


def _integration_response(status: str, *, e2e: Optional[Dict[str, Any]] = None, detail: Any = None) -> Dict[str, Any]:
    e2e_block = dict(e2e or {"status": status})
    for key, value in _evidence_block().items():
        e2e_block.setdefault(key, value)
    return {
        "ok": status == "pass",
        "command": "integration",
        "status": status,
        "error": status_to_error(status),
        "detail": detail,
        "e2e": e2e_block,
        "api_db": {"status": "skip"},
        "contract_version": "2.0",
    }


def _legacy_payload(error_code: str, raw: Dict[str, Any], *, bucket_by_fallback: bool) -> Dict[str, Any]:
    """cmux-tool error code를 공통 계약 입력으로 감싼다.

    사유를 재작문하지 않는다 — code 원문을 그대로 실어 `normalize_legacy_verdict`가
    최종 status를 결정하게 한다(NR-7, TASK.md C-3).
    """
    payload: Dict[str, Any] = {
        "status": "fallback" if (bucket_by_fallback and error_code in FALLBACK_CODES) else "escalated",
        "error": error_code,
    }
    if bucket_by_fallback:
        payload["fallback_reason"] = error_code
    if "wait_kind" in raw:
        payload["wait_kind"] = raw.get("wait_kind")
    return payload


def run_integration(
    tiers_data: Dict[str, Any],
    scope: str = "be",
    url: Optional[str] = None,
    project_root: Optional[pathlib.Path] = None,
    env=None,
) -> Dict[str, Any]:
    """
    integration 서브명령 실행 — cmux 후보 결과를 공통 E2E verdict로 정규화한다.

    mode A (격리 신규 surface) — 연산은 `lib.e2e.drivers.cmux`가 수행한다:
      driver.open <url> → surface 획득 (신규, --surface 미전달)
      → act(navigate)
      → close (우리가 연 surface만, user_owned surface는 건드리지 않는다)

    반환 dict:
        ok: bool
        status: pass|fail|infra_error|executor_unavailable|blocked|awaiting_human
        command: str
        e2e: {driver, status}
        api_db: {status}
        error: status_to_error(status)
        contract_version: str
    """
    integration_data = tiers_data.get("integration", {})
    e2e_config = integration_data.get("e2e", [])

    # cmux가 e2e config에 있는지 확인
    has_cmux = any(
        isinstance(t, dict) and t.get("name") == "cmux"
        for t in e2e_config
    )

    if not has_cmux:
        return _integration_response(
            "executor_unavailable",
            e2e={"driver": None, "status": "executor_unavailable", "url": url},
            detail="no configured E2E executor is available",
        )

    driver = cmux_driver.CmuxDriver(runtime_context={"url": url, "scope": scope}, env=env)

    # mode A: open (--surface 미전달 — 신규 surface 강제). driver가 그 규칙을 소유한다.
    try:
        open_result = driver.dispatch("open", {"url": url})
    except cmux_driver.CmuxToolError as exc:
        normalized = normalize_legacy_verdict(
            _legacy_payload(exc.detail_code, exc.raw, bucket_by_fallback=True)
        )
        status = normalized["status"]
        if status == "provider_unavailable":
            status = "executor_unavailable"
        return _integration_response(
            status,
            e2e={"driver": "cmux", "status": status, "url": url},
            detail=normalized.get("detail"),
        )

    surface_id = open_result.get("handle")

    # navigate (mode A)
    if url and surface_id:
        try:
            driver.dispatch("act", {"handle": surface_id, "action": {"kind": "navigate", "target": url}})
        except cmux_driver.CmuxToolError as exc:
            if exc.detail_code in ESCALATE_CODES:
                _safe_close(driver)
                normalized = normalize_legacy_verdict(
                    _legacy_payload(exc.detail_code, exc.raw, bucket_by_fallback=False)
                )
                return _integration_response(
                    normalized["status"],
                    e2e={"driver": "cmux", "status": normalized["status"], "url": url},
                    detail=normalized.get("detail"),
                )

    # mode A close (신규 surface 정리 — 사용자 surface 미훼손)
    _safe_close(driver)

    # open·navigate·close만으로는 semantic assertion도 필수 증적도 없다(C-DRV-4). 판정은
    # 단일 관문 `build_verdict`에 넘기고, 계약이 요구하는 5종 증적을 요구치로 그대로
    # 전달한다 — 여기서 `semantic_assertion` 한 항목으로 축소하면 §A.1 결손이 판정에
    # 도달하지 못한다(S-5). assertion 결과는 driver가 실제로 수행한 `assert` 연산분만
    # 싣는다 — 이 경로에는 assertion이 선언되지 않으므로 비어 있고, 그 비어 있음이 곧
    # `assertion_required` fail의 근거다. 빈 리터럴을 고정으로 넘기지 않는다.
    assertion_results = driver.assertion_results()
    observed_evidence = driver.observed_evidence()
    verdict = build_verdict({
        "status": "pass",
        "profile": "browser",
        "observed_executors": ["browser"],
        "events": ["open", "navigate", "close"],
        "assertion_results": assertion_results,
        "required_evidence": list(COMMON_REQUIRED_EVIDENCE),
        "observed_evidence": list(observed_evidence),
    })
    status = verdict["status"] if not verdict["ok"] else "pass"
    e2e_block: Dict[str, Any] = {"driver": "cmux", "status": status, "url": url, "surface": surface_id}
    e2e_block.update(_evidence_block(observed_evidence))
    return _integration_response(status, e2e=e2e_block, detail=verdict.get("detail"))


def _safe_close(driver: "cmux_driver.CmuxDriver") -> None:
    """정리 실패가 판정을 바꾸지 않게 한다 — 정리 대상은 driver 대장(우리 surface)뿐이다."""
    try:
        driver.dispatch("close", {})
    except cmux_driver.CmuxToolError:
        return
