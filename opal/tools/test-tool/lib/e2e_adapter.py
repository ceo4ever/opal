"""
@header {
  "module": "e2e_adapter",
  "layer": "util",
  "domain": "opal-tools",
  "description": "cmux-tool subprocess 호출 → JSON error 소비 → 폴백/에스컬레이션 결정 + mode A 시퀀스(open→navigate→close). uname/cmux --version 하드코딩 분기 금지 — cmux-tool 에러코드 소비(어댑터)로만 플랫폼 가드 흡수.",
  "exports": [
    "run_integration"
  ],
  "depends": ["cmux-tool (OPAL_CMUX_TOOL_CMD env → ~/.opal/tools/cmux-tool/run.sh 기본 경로)"]
}

e2e_adapter — cmux-tool 에러코드 소비 어댑터.

[MUST] cmux 분기는 cmux-tool 에러코드 소비로만 — uname/cmux --version 하드코딩 분기 금지 (헌법 플랫폼 독립).
[MUST] FALLBACK_CODES → playwright (phase2)
[MUST] ESCALATE_CODES → escalate=true, 폴백 금지
[MUST] mode A — --surface 미전달(신규 surface 강제), B/C 재사용 금지

cmux-tool README §에러코드 테이블 (README.md:148-161) SSOT:
  usage          → 에스컬레이션 (인자 오류)
  not_in_cmux    → 폴백 (CMUX_SURFACE_ID 미설정)
  cmux_not_installed → 폴백 (cmux 명령 없음)
  invalid_surface → 에스컬레이션 (surface 핸들 형식 오류)
  open_failed    → 폴백 (cmux browser open 실패)
  surface_parse_failed → 폴백 (open 출력 파싱 실패)
  goto_failed    → 에스컬레이션 (URL 오류 — 폴백 금지)
  wait_failed    → 에스컬레이션 (네트워크 문제 — 폴백 금지)
  eval_failed    → 에스컬레이션 (명령 오류 — 폴백 금지)
"""

import json
import os
import pathlib
import subprocess
from typing import Any, Dict, List, Optional


# ─── cmux-tool 에러코드 분류 (PLAN §3.3.3 [MUST]) ────────────────────────────
# cmux-tool/README.md:148-161 SSOT
FALLBACK_CODES = {
    "not_in_cmux",          # CMUX_SURFACE_ID 미설정 → playwright
    "cmux_not_installed",   # cmux 명령 없음 → playwright
    "surface_parse_failed", # open 출력 파싱 실패 → playwright
    "open_failed",          # cmux browser open 실패 → playwright
}

ESCALATE_CODES = {
    "usage",            # 인자 오류 → 에스컬레이션 (호출자 수정 필요)
    "invalid_surface",  # surface 핸들 형식 오류 → 에스컬레이션
    "goto_failed",      # URL/navigate 오류 → 에스컬레이션 (폴백 금지)
    "wait_failed",      # 페이지 로드 타임아웃 → 에스컬레이션 (폴백 금지)
    "eval_failed",      # 명령 실행 실패 → 에스컬레이션 (폴백 금지)
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


def _run_playwright_fallback(
    url: Optional[str],
    fallback_reason: str,
) -> Dict[str, Any]:
    """
    폴백 결정 + opal-test-agent가 소비할 playwright MCP 액션(`mcp_action`/`mcp_url`)을 반환.
    실제 MCP 실행은 opal-test-agent 책임(AGENT.md M2 절차).
    """
    return {
        "driver": "playwright",
        "fallback_reason": fallback_reason,
        "status": "fallback",
        "url": url,
        "mcp_action": "browser_navigate",
        "mcp_url": url,
    }


def run_integration(
    tiers_data: Dict[str, Any],
    scope: str = "be",
    url: Optional[str] = None,
    project_root: Optional[pathlib.Path] = None,
    env=None,
) -> Dict[str, Any]:
    """
    integration 서브명령 실행 — cmux-tool 에러코드 소비 → 폴백/에스컬레이션 결정.

    mode A (격리 신규 surface):
      cmux-tool open <url> → surface 획득 (신규, --surface 미전달)
      → navigate → 증거 캡처
      → cmux-tool close

    반환 dict:
        ok: bool
        command: str
        e2e: {driver, fallback_reason, status}
        api_db: {status}
        escalate: bool
        error: str (에스컬레이션 시)
    """
    integration_data = tiers_data.get("integration", {})
    e2e_config = integration_data.get("e2e", [])

    # cmux가 e2e config에 있는지 확인
    has_cmux = any(
        isinstance(t, dict) and t.get("name") == "cmux"
        for t in e2e_config
    )

    # api_db 검사 (기본 skip)
    api_db_result = {"status": "skip"}

    if not has_cmux:
        # cmux 없으면 playwright 직접
        e2e_result = _run_playwright_fallback(url, "cmux not configured")
        return {
            "ok": e2e_result.get("status") in ("pass", "fallback"),
            "command": "integration",
            "e2e": e2e_result,
            "api_db": api_db_result,
            "escalate": False,
        }

    # mode A: cmux-tool open (--surface 미전달 — 신규 surface 강제)
    open_args = ["open"]
    if url:
        open_args.append(url)

    open_result = _call_cmux_tool(open_args, env=env)
    error_code = open_result.get("error")

    if not open_result.get("ok") and error_code:
        if error_code in FALLBACK_CODES:
            # 폴백 트리거 → playwright
            e2e_result = _run_playwright_fallback(url, error_code)
            return {
                "ok": True,
                "command": "integration",
                "e2e": e2e_result,
                "api_db": api_db_result,
                "escalate": False,
            }
        elif error_code in ESCALATE_CODES:
            # 에스컬레이션 → 폴백 금지
            return {
                "ok": False,
                "command": "integration",
                "e2e": {"driver": None, "status": "escalated", "error": error_code},
                "api_db": api_db_result,
                "escalate": True,
                "error": "escalation",
                "detail": f"cmux-tool returned escalation error: {error_code}",
            }
        else:
            # 알 수 없는 에러 → 에스컬레이션
            return {
                "ok": False,
                "command": "integration",
                "e2e": {"driver": None, "status": "escalated", "error": error_code},
                "api_db": api_db_result,
                "escalate": True,
                "error": "escalation",
                "detail": f"cmux-tool returned unknown error: {error_code}",
            }

    # cmux open 성공 — surface 획득
    surface_id = open_result.get("surface")

    # navigate (mode A)
    if url and surface_id:
        nav_result = _call_cmux_tool(["navigate", url], env=env)
        nav_error = nav_result.get("error")
        if nav_error and nav_error in ESCALATE_CODES:
            # navigate 에스컬레이션 → close 후 에스컬레이션
            _call_cmux_tool(["close"], env=env)
            return {
                "ok": False,
                "command": "integration",
                "e2e": {"driver": "cmux", "status": "escalated", "error": nav_error},
                "api_db": api_db_result,
                "escalate": True,
                "error": "escalation",
                "detail": f"cmux navigate failed: {nav_error}",
            }

    # mode A close (신규 surface 정리 — 사용자 surface 미훼손)
    _call_cmux_tool(["close"], env=env)

    e2e_result = {
        "driver": "cmux",
        "status": "pass",
        "url": url,
        "surface": surface_id,
    }

    return {
        "ok": True,
        "command": "integration",
        "e2e": e2e_result,
        "api_db": api_db_result,
        "escalate": False,
    }
