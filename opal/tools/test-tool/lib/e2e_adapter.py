"""
@header {
  "module": "e2e_adapter",
  "layer": "util",
  "domain": "opal-tools",
  "description": "cmux-tool raw 결과를 provider 후보 결과로 번역하고 공통 E2E contract verdict를 소비하는 integration adapter.",
  "exports": [
    "run_integration"
  ],
  "depends": [
    "lib.e2e_contract",
    "cmux-tool (OPAL_CMUX_TOOL_CMD env → ~/.opal/tools/cmux-tool/run.sh 기본 경로)"
  ]
}

e2e_adapter — cmux-tool raw provider adapter.

[MUST] cmux 분기는 cmux-tool 에러코드 소비로만 — uname/cmux --version 하드코딩 분기 금지 (헌법 플랫폼 독립).
[MUST] provider_unavailable일 때만 다음 Browser 후보 전환을 허용한다.
[MUST] final status/exit/error/pass gate는 lib.e2e_contract 공통 계약을 소비한다.
[MUST] mode A — --surface 미전달(신규 surface 강제), B/C 재사용 금지

Legacy cmux-tool error vocabulary is accepted only as adapter input and normalized
through lib.e2e_contract.  New public JSON does not emit generic fallback,
escalated, escalate, or escalation keys.
"""

import json
import os
import pathlib
import subprocess
from typing import Any, Dict, List, Optional

from lib.e2e_contract import build_verdict, normalize_legacy_verdict, status_to_error


# ─── legacy cmux-tool raw error buckets (input normalization only) ───────────
FALLBACK_CODES = {
    "not_in_cmux",          # provider_unavailable candidate result
    "cmux_not_installed",   # provider_unavailable candidate result
    "surface_parse_failed", # infra_error via common contract
    "open_failed",          # infra_error via common contract
}

ESCALATE_CODES = {
    "usage",            # infra_error via common contract
    "invalid_surface",  # infra_error via common contract
    "goto_failed",      # infra_error via common contract
    "wait_failed",      # infra_error or fail with wait_kind=assertion_condition
    "eval_failed",      # infra_error via common contract
}

# cmux-tool 기본 실행 경로 — OPAL 설치 기준 절대 경로
# OPAL_CMUX_TOOL_CMD 환경변수가 있으면 그 값을 우선 사용 (테스트 스텁 주입 + 오버라이드용)
_CMUX_TOOL_DEFAULT_PATH = os.path.expanduser("~/.opal/tools/cmux-tool/run.sh")


def _resolve_cmux_tool_cmd(env=None) -> str:
    """
    cmux-tool 실행 경로 결정.
    1. OPAL_CMUX_TOOL_CMD 환경변수 (env dict 또는 현재 프로세스 환경)
    2. 없으면 ~/.opal/tools/cmux-tool/run.sh 기본 경로
    """
    # env dict가 전달된 경우 우선 참조, 없으면 현재 프로세스 환경 확인
    if env is not None:
        cmd = env.get("OPAL_CMUX_TOOL_CMD")
    else:
        cmd = os.environ.get("OPAL_CMUX_TOOL_CMD")
    return cmd if cmd else _CMUX_TOOL_DEFAULT_PATH


def _call_cmux_tool(args: List[str], env=None) -> Dict[str, Any]:
    """
    cmux-tool을 subprocess로 호출하고 stdout JSON 파싱하여 반환.
    호출 실패(파일 없음 등) 시 {"ok": False, "error": "cmux_not_installed"} 반환.

    cmux-tool 경로 해석 순서:
    1. env["OPAL_CMUX_TOOL_CMD"] (테스트 스텁 주입 / 오버라이드)
    2. os.environ["OPAL_CMUX_TOOL_CMD"]
    3. ~/.opal/tools/cmux-tool/run.sh (기본 경로)
    """
    cmux_tool_cmd = _resolve_cmux_tool_cmd(env)
    try:
        result = subprocess.run(
            ["bash", cmux_tool_cmd] + args,
            capture_output=True,
            text=True,
            env=env,
        )
        stdout = result.stdout.strip()
        if not stdout:
            # cmux-tool이 설치되지 않았거나 실패한 경우 stderr 확인
            stderr = result.stderr.strip()
            return {
                "ok": False,
                "error": "cmux_not_installed",
                "detail": stderr or "cmux-tool returned empty output",
            }
        try:
            data = json.loads(stdout)
            return data
        except json.JSONDecodeError:
            return {
                "ok": False,
                "error": "surface_parse_failed",
                "detail": f"Failed to parse cmux-tool JSON output: {stdout}",
            }
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "cmux_not_installed",
            "detail": f"{cmux_tool_cmd} not found",
        }


def _integration_response(status: str, *, e2e: Optional[Dict[str, Any]] = None, detail: Any = None) -> Dict[str, Any]:
    return {
        "ok": status == "pass",
        "command": "integration",
        "status": status,
        "error": status_to_error(status),
        "detail": detail,
        "e2e": e2e or {"status": status},
        "api_db": {"status": "skip"},
        "contract_version": "2.0",
    }


def run_integration(
    tiers_data: Dict[str, Any],
    scope: str = "be",
    url: Optional[str] = None,
    project_root: Optional[pathlib.Path] = None,
    env=None,
) -> Dict[str, Any]:
    """
    integration 서브명령 실행 — cmux-tool raw result를 공통 E2E verdict로 정규화한다.

    mode A (격리 신규 surface):
      cmux-tool open <url> → surface 획득 (신규, --surface 미전달)
      → navigate
      → cmux-tool close

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

    # mode A: cmux-tool open (--surface 미전달 — 신규 surface 강제)
    open_args = ["open"]
    if url:
        open_args.append(url)

    open_result = _call_cmux_tool(open_args, env=env)
    error_code = open_result.get("error")

    if not open_result.get("ok") and error_code:
        payload = {
            "status": "fallback" if error_code in FALLBACK_CODES else "escalated",
            "fallback_reason": error_code,
            "error": error_code,
        }
        if "wait_kind" in open_result:
            payload["wait_kind"] = open_result.get("wait_kind")
        normalized = normalize_legacy_verdict(payload)
        status = normalized["status"]
        if status == "provider_unavailable":
            status = "executor_unavailable"
        return _integration_response(
            status,
            e2e={"driver": "cmux", "status": status, "url": url},
            detail=normalized.get("detail"),
        )

    # cmux open 성공 — surface 획득
    surface_id = open_result.get("surface")

    # navigate (mode A)
    if url and surface_id:
        nav_result = _call_cmux_tool(["navigate", url], env=env)
        nav_error = nav_result.get("error")
        if nav_error and nav_error in ESCALATE_CODES:
            _call_cmux_tool(["close"], env=env)
            payload = {"status": "escalated", "error": nav_error}
            if "wait_kind" in nav_result:
                payload["wait_kind"] = nav_result.get("wait_kind")
            normalized = normalize_legacy_verdict(payload)
            return _integration_response(
                normalized["status"],
                e2e={"driver": "cmux", "status": normalized["status"], "url": url},
                detail=normalized.get("detail"),
            )

    # mode A close (신규 surface 정리 — 사용자 surface 미훼손)
    _call_cmux_tool(["close"], env=env)

    verdict = build_verdict({
        "status": "pass",
        "profile": "browser",
        "observed_executors": ["browser"],
        "events": ["open", "navigate", "close"],
        "assertion_results": [],
        "required_evidence": ["semantic_assertion"],
        "observed_evidence": [],
    })
    status = verdict["status"] if not verdict["ok"] else "pass"
    return _integration_response(
        status,
        e2e={"driver": "cmux", "status": status, "url": url, "surface": surface_id},
        detail=verdict.get("detail"),
    )
