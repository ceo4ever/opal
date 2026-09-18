"""
@header {
  "module": "e2e_adapter",
  "layer": "util",
  "domain": "opal-tools",
  "description": "legacy `integration` 서브명령의 후보 체인 adapter. 우선순위 순회(Ego Lite → cmux → Playwright)와 provider_unavailable 전용 전환은 이 모듈이 소유하고, 각 후보의 실제 연산과 §B.2 8연산 계약은 `lib.e2e.drivers.*`가 소유한다. 여기 남은 것은 후보 순회·결과 정규화·공통 판정 관문 소비다.",
  "exports": ["run_integration"],
  "depends": ["lib.e2e_contract", "lib.e2e.drivers.ego_lite", "lib.e2e.drivers.cmux", "playwright-tool"]
}

Configured providers are candidates, not success evidence. Only
provider_unavailable permits traversal to the next candidate.
"""

import json
import os
import pathlib
import shlex
import subprocess
from typing import Any, Dict, List, Optional

from lib.e2e.drivers import cmux as cmux_driver
from lib.e2e.drivers import ego_lite as ego_driver
from lib.e2e.evidence import COMMON_REQUIRED_EVIDENCE
from lib.e2e_contract import build_verdict, normalize_legacy_verdict, status_to_error

FIDELITY_MOCK = "mock"

# 어휘의 SSOT는 후보를 실제로 실행하는 `lib.e2e.drivers.cmux`다. 같은 객체를 재노출해
# 복제본이 생기지 않게 한다 — 이름이 한 글자라도 갈라지면 cmux-tool을 고쳐야
# 계약이 성립하게 되는데, 제약은 정확히 그 반대다(cmux-tool 변경 0, TRD.md §8).
FALLBACK_CODES = cmux_driver.FALLBACK_CODES
_EGO_DEFAULT = os.path.expanduser("~/.opal/tools/ego-browser-tool/run.sh")
_CMUX_DEFAULT = os.path.expanduser("~/.opal/tools/cmux-tool/run.sh")
_PLAYWRIGHT_DEFAULT = os.path.expanduser("~/.opal/tools/playwright-tool/run.sh")


def _tool_cmd(env, name: str, default: str) -> List[str]:
    return shlex.split((env or os.environ).get(name) or default)


def _call_json(command: List[str], args: List[str], env=None) -> Dict[str, Any]:
    try:
        process = subprocess.run([*command, *args], capture_output=True, text=True, env=env, check=False)
    except (FileNotFoundError, PermissionError) as exc:
        return {"ok": False, "status": "provider_unavailable", "detail": str(exc)}
    stdout = process.stdout.strip()
    if not stdout:
        return {
            "ok": False,
            "status": "provider_unavailable" if process.returncode in {18, 126, 127} else "infra_error",
            "detail": process.stderr.strip() or "provider returned empty output",
        }
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return {"ok": False, "status": "infra_error", "detail": "provider returned invalid JSON"}
    if not isinstance(data, dict):
        return {"ok": False, "status": "infra_error", "detail": "provider JSON root is not an object"}
    data.setdefault("_exit_code", process.returncode)
    return data


def _resolve_cmux_tool_cmd(env=None) -> str:
    """Compatibility seam retained for existing callers and tests."""
    return _tool_cmd(env, "OPAL_CMUX_TOOL_CMD", _CMUX_DEFAULT)[0]


def _call_cmux_tool(args: List[str], env=None) -> Dict[str, Any]:
    command = _tool_cmd(env, "OPAL_CMUX_TOOL_CMD", _CMUX_DEFAULT)
    if len(command) == 1:
        command = ["bash", command[0]]
    data = _call_json(command, args, env=env)
    if data.get("status") == "provider_unavailable" and not data.get("error"):
        data["error"] = "cmux_not_installed"
    return data


def _evidence_block(observed: Optional[List[str]] = None, fidelity: str = FIDELITY_MOCK) -> Dict[str, Any]:
    """`CONTRACT.md` §A.1 공통 필수 증적 5종 요구와 실제 관측분을 함께 싣는다.

    `required_evidence`를 `semantic_assertion` 한 항목으로 고정하면 계약이 요구하는 5종이
    판정 관문에 전달되지 않는다(동결 RED S-5). 관측분은 실제 수집된 것만 올린다 — 요구치를
    관측치로 베끼면 결손 자체가 보이지 않는다.
    """
    observed_list = list(observed or [])
    missing = [item for item in COMMON_REQUIRED_EVIDENCE if item not in observed_list]
    return {
        "required_evidence": list(COMMON_REQUIRED_EVIDENCE),
        "observed_evidence": observed_list,
        "missing_evidence": missing,
        "evidence_complete": not missing,
        # [MUST] 증적이 불완전하면 real-usage가 아니다(동결 RED S-6).
        "fidelity": FIDELITY_MOCK if missing else fidelity,
    }


def _response(status: str, *, e2e=None, detail=None, handoff=None) -> Dict[str, Any]:
    e2e_block = dict(e2e or {"status": status})
    # 후보가 무엇이든 증적 계약은 같다 — 봉투에서 한 번만 채운다.
    for key, value in _evidence_block().items():
        e2e_block.setdefault(key, value)
    output = {
        "ok": status == "pass",
        "command": "integration",
        "status": status,
        "error": status_to_error(status),
        "detail": detail,
        "e2e": e2e_block,
        "api_db": {"status": "skip"},
        "contract_version": "2.0",
    }
    if handoff is not None:
        output["handoff"] = handoff
    return output


def _asserted(name: str, raw: Dict[str, Any], url: Optional[str], expected: Optional[str]) -> Dict[str, Any]:
    status = raw.get("status")
    if status == "provider_unavailable":
        return {"status": status, "raw": raw}
    if status not in {"pass", "fail", "infra_error", "blocked", "awaiting_human"}:
        status = "pass" if raw.get("ok") else "infra_error"
    actual = raw.get("actual")
    if status == "pass" and (not expected or actual is None or expected not in str(actual)):
        status = "fail"
    return {
        "status": status,
        "raw": raw,
        "e2e": {"driver": name, "status": status, "url": url, "expected": expected, "actual": actual},
    }


def _run_ego(url, expected, install_choice, env=None) -> Dict[str, Any]:
    """Ego Lite 후보 — 실행은 `lib.e2e.drivers.ego_lite`가 소유한다.

    [MUST] **도구가 소유한 status를 재해석하지 않는다.** `ego-browser-tool` README 계약:
    미설치는 `awaiting_human`(manual·r2·cancel 선택과 resume 정보)이고, **명시적 `cancel`과
    비지원 플랫폼만** `provider_unavailable`이다. 전자를 후자로 바꾸면 사람의 설치 선택을
    기다려야 할 자리에서 조용히 다음 후보로 넘어간다 — C-3가 금지하는 바로 그 전환이다.

    `smoke`는 open과 텍스트 assert가 융합된 단일 연산이므로 driver도 `open`(URL 기록)
    → `assert`(smoke 1회) 형태로 노출한다. 여기서 `probe`를 먼저 부르지 않는 이유는
    같은 판정을 두 번 하지 않기 위해서다 — `smoke` 자신이 미설치 상태를 돌려준다.
    """
    if not url:
        return {"status": "fail", "detail": "URL is required"}
    driver = ego_driver.EgoLiteDriver(
        runtime_context={"env": env, "ego_install_choice": install_choice}
    )
    try:
        driver.dispatch("open", {"url": url})
        record = driver.dispatch(
            "assert",
            {"assertion": {"id": "expect-text", "verifier": "dom_text",
                           "expected": expected, "match": "equals"}},
        )
    except ego_driver.EgoLiteToolError as exc:
        # 도구 자체가 깨진 경우다. 다음 후보로 넘기지 않는다(C-3).
        return {"status": "infra_error", "detail": exc.detail_code}
    raw = driver.last_raw or {}
    tool_status = raw.get("status")
    # [MUST] 도구가 낸 status는 **전부** 그대로 올린다. 일부만 통과시키면 나머지가
    # `build_verdict` 기본 경로로 떨어져 `fail`로 뭉개진다 — infra_error·blocked가
    # 제품 실패로 위장되는 형태다(C-3·§C.7). 재해석하는 유일한 경우는 도구가 성공을
    # 보고했을 때뿐이고, 그때의 pass 승격은 공통 관문이 판정한다.
    if tool_status and tool_status not in {"pass", "ok"}:
        return {"status": tool_status, "raw": raw, "detail": raw.get("detail")}
    # 판정은 공통 관문이 내린다 — 이 모듈은 status 문자열을 만들지 않는다(§C.2).
    verdict = build_verdict({
        "status": "pass", "profile": "browser", "observed_executors": ["browser"],
        "assertion_results": [record] if expected else [],
        "required_evidence": ["semantic_assertion"],
        "observed_evidence": ["semantic_assertion"] if expected else [],
    })
    status = verdict["status"]
    e2e = {"driver": "ego-lite", "status": status, "url": url,
           "expected": expected, "actual": record.get("actual")}
    if raw.get("space_id") is not None:
        e2e["space_id"] = raw["space_id"]
    return {"status": status, "detail": verdict.get("detail"), "raw": raw, "e2e": e2e}


def _cmux_error(raw: Dict[str, Any]) -> Dict[str, Any]:
    error = raw.get("error")
    payload = {"status": "fallback" if error in FALLBACK_CODES else "escalated", "fallback_reason": error, "error": error}
    if "wait_kind" in raw:
        payload["wait_kind"] = raw["wait_kind"]
    return normalize_legacy_verdict(payload)


def _cmux_failure(exc: "cmux_driver.CmuxToolError") -> Dict[str, Any]:
    """cmux-tool 오류를 공통 verdict로 정규화한다.

    [MUST] `wait_kind`를 실어 보낸다 — `e2e_contract.py:229-231`이 `wait_failed`에서
    `wait_kind == "assertion_condition"`일 때만 `fail`로, 아니면 `infra_error`로 가른다
    (RK-6). 빠뜨리면 제품 실패인 assertion timeout이 인프라 오류로 기록된다.
    """
    raw = dict(getattr(exc, "raw", {}) or {})
    payload = {
        "status": "fallback" if exc.detail_code in FALLBACK_CODES else "escalated",
        "fallback_reason": exc.detail_code,
        "error": exc.detail_code,
    }
    if "wait_kind" in raw:
        payload["wait_kind"] = raw["wait_kind"]
    normalized = normalize_legacy_verdict(payload)
    return {"status": normalized["status"], "detail": normalized.get("detail"), "raw": raw}


def _run_cmux(url, expected, env=None) -> Dict[str, Any]:
    """cmux 후보 — 실행은 `lib.e2e.drivers.cmux`가 소유한다(W-6 이관).

    mode A(`--surface` 미전달, 신규 surface 강제)와 `user_owned=true` surface 미정리는
    driver가 구조로 강제한다. 여기서는 error code 정규화와 결과 봉투만 만든다.
    """
    driver = cmux_driver.CmuxDriver(runtime_context={"url": url}, env=env)
    try:
        opened = driver.dispatch("open", {"url": url})
    except cmux_driver.CmuxToolError as exc:
        return _cmux_failure(exc)
    surface = opened.get("handle")
    try:
        actual = None
        record = None
        if expected:
            record = driver.dispatch(
                "assert",
                {"assertion": {"id": "expect-text", "verifier": "dom_text",
                               "expected": expected, "match": "equals"}},
            )
            actual = record.get("actual")
        verdict = build_verdict({
            "status": "pass", "profile": "browser", "observed_executors": ["browser"],
            "assertion_results": [record] if record else [],
            "required_evidence": ["semantic_assertion"],
            "observed_evidence": ["semantic_assertion"] if record else [],
        })
        status = verdict["status"]
        return {"status": status, "detail": verdict.get("detail"),
                "e2e": {"driver": "cmux", "status": status, "url": url,
                        "surface": surface, "expected": expected, "actual": actual}}
    except cmux_driver.CmuxToolError as exc:
        return _cmux_failure(exc)
    finally:
        try:
            driver.dispatch("close", {"handle": surface})
        except cmux_driver.CmuxToolError:
            # 정리 실패로 이미 정해진 판정을 덮지 않는다.
            pass


def _run_playwright(candidate, url, expected, env=None) -> Dict[str, Any]:
    override = (env or os.environ).get("OPAL_PLAYWRIGHT_TOOL_CMD")
    if not override and candidate.get("via") != "playwright-tool":
        return {"status": "provider_unavailable", "detail": "playwright adapter is not configured"}
    if not url:
        return {"status": "fail", "detail": "URL is required"}
    raw = _call_json(_tool_cmd(env, "OPAL_PLAYWRIGHT_TOOL_CMD", _PLAYWRIGHT_DEFAULT), [url, "--mode", "clean"], env=env)
    if raw.get("status") == "provider_unavailable":
        return {"status": "provider_unavailable", "raw": raw}
    if not raw.get("ok"):
        return {"status": raw.get("status") or "infra_error", "raw": raw, "detail": raw.get("detail") or raw.get("error")}
    raw["actual"] = raw.get("actual") if raw.get("actual") is not None else raw.get("content")
    raw["status"] = "pass"
    return _asserted("playwright", raw, url, expected)


def run_integration(
    tiers_data: Dict[str, Any], scope: str = "be", url: Optional[str] = None,
    project_root: Optional[pathlib.Path] = None, env=None,
    expect_text: Optional[str] = None, ego_install_choice: Optional[str] = None,
) -> Dict[str, Any]:
    del scope, project_root
    candidates = [item for item in tiers_data.get("integration", {}).get("e2e", []) if isinstance(item, dict)]
    candidates.sort(key=lambda item: (item.get("priority", 999), str(item.get("name", ""))))
    attempted: List[str] = []
    for candidate in candidates:
        name = str(candidate.get("name") or "")
        if name in {"ego", "ego-lite", "ego-browser"}:
            result, driver = _run_ego(url, expect_text, ego_install_choice, env), "ego-lite"
        elif name == "cmux":
            result, driver = _run_cmux(url, expect_text, env), "cmux"
        elif name == "playwright":
            result, driver = _run_playwright(candidate, url, expect_text, env), "playwright"
        else:
            result, driver = {"status": "provider_unavailable", "detail": f"unknown provider: {name}"}, name
        attempted.append(name)
        status = result.get("status")
        if status == "provider_unavailable":
            continue
        raw = result.get("raw") or {}
        e2e = result.get("e2e") or {"driver": driver, "status": status, "url": url, "expected": expect_text, "actual": raw.get("actual")}
        e2e["attempted"] = attempted
        return _response(str(status), e2e=e2e, detail=result.get("detail") or raw.get("detail"), handoff=raw.get("handoff"))
    return _response("executor_unavailable", e2e={"driver": None, "status": "executor_unavailable", "url": url, "attempted": attempted}, detail="configured E2E provider candidates are unavailable")
