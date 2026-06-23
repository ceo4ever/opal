"""
@header {
  "module": "test_tool",
  "layer": "util",
  "domain": "opal-tools",
  "description": "test-tool CLI — 4서브명령(resolve/check/unit/integration) argparse 라우터 + ERROR_CODES 카탈로그 + JSON 출력 헬퍼. 얇은 래퍼: yaml 해석→명령 실행(subprocess 위임)→JSON 증거 반환. 루프 한도 비보유(opal-harness.md §1 포인터).",
  "exports": [
    "main",
    "ERROR_CODES"
  ],
  "depends": [
    "lib.resolver",
    "lib.runner",
    "lib.e2e_adapter"
  ]
}

test-tool — 4서브명령 CLI 라우터.

[MUST] 헌법 §2 단순성: 러너(pytest/vitest/cmux/eslint) 재구현 금지.
  yaml 해석 → 명령 실행(subprocess) → JSON 증거 반환하는 얇은 래퍼.
[MUST] 헌법 플랫폼 독립: cmux 분기는 cmux-tool 에러코드 소비(어댑터)로만.
[MUST] 루프 한도 비보유: test-tool은 1회 실행·판정만.
  재시도 루프는 오케스트레이터 책임(opal-harness.md §1 포인터).
"""

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, Optional

# lib 모듈 경로 추가
_TOOL_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(_TOOL_DIR))

from lib.resolver import resolve_test_tools
from lib.runner import run_check, run_unit_layers
from lib.e2e_adapter import run_integration as _run_integration

# ─────────────────────────────────────────────────────────────────────────────
# ERROR_CODES 카탈로그 (SSOT) — 모든 error 응답 값은 이 키를 사용한다.
# 추가/임의 변형 금지. state-tool.py:68-103 패턴 답습.
# ─────────────────────────────────────────────────────────────────────────────

ERROR_CODES: Dict[str, str] = {
    "venv_missing":       "OPAL .venv not found — Run install-mac.sh first",
    "yaml_parse_failed":  "test-tools.yaml 파싱 실패 — YAML 문법 오류",
    "no_runner":          "test-tools.yaml 없음 + package.json/pyproject.toml 추론 불가",
    "required_missing":   "required 도구 미설치 — check 게이트 차단",
    "layer_failed":       "unit 계층 실패 (stop-on-fail) — lint/typecheck/unit 중 한 계층 실패",
    "e2e_failed":         "E2E 테스트 실패 — cmux/playwright 모두 실패",
    "escalation":         "cmux-tool 에스컬레이션 에러코드 — 폴백 금지, 호출자 수정 필요",
}

# ─────────────────────────────────────────────────────────────────────────────
# 응답 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _respond(data: Dict[str, Any], exit_code: int = 0) -> None:
    """JSON 출력 후 지정 exit code로 종료."""
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(exit_code)


def _error(error_key: str, detail: Optional[str] = None, command: str = "") -> None:
    """에러 응답 출력 후 exit 1."""
    resp: Dict[str, Any] = {
        "ok": False,
        "command": command,
        "error": error_key,
    }
    if detail:
        resp["detail"] = detail
    print(json.dumps(resp, ensure_ascii=False))
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 서브명령 핸들러
# ─────────────────────────────────────────────────────────────────────────────

def cmd_resolve(args: argparse.Namespace) -> None:
    """resolve 서브명령 — test-tools.yaml resolution_order 해석."""
    project_root = pathlib.Path(args.project_root) if args.project_root else None
    result = resolve_test_tools(
        project_root=project_root,
        stack=getattr(args, "stack", None),
    )
    if not result.get("ok"):
        error_key = result.get("error", "yaml_parse_failed")
        # exit code 매핑
        if error_key == "yaml_parse_failed":
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(2)
        elif error_key == "no_runner":
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(3)
        else:
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(1)
    _respond(result, 0)


def cmd_check(args: argparse.Namespace) -> None:
    """check 서브명령 — required/optional 도구 설치 게이트."""
    project_root = pathlib.Path(args.project_root) if args.project_root else None
    resolved = resolve_test_tools(project_root=project_root)
    if not resolved.get("ok"):
        error_key = resolved.get("error", "yaml_parse_failed")
        print(json.dumps(resolved, ensure_ascii=False))
        sys.exit(1)

    tiers_data = resolved.get("tiers", {})
    tier = getattr(args, "tier", None)
    category = getattr(args, "category", None)

    result = run_check(tiers_data, tier=tier, category=category)
    result["command"] = "check"

    if result.get("blocked"):
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(4)
    _respond(result, 0)


def cmd_unit(args: argparse.Namespace) -> None:
    """unit 서브명령 — lint→typecheck→unit stop-on-fail 단발 실행."""
    project_root = pathlib.Path(args.project_root) if args.project_root else None
    resolved = resolve_test_tools(project_root=project_root)
    if not resolved.get("ok"):
        print(json.dumps(resolved, ensure_ascii=False))
        sys.exit(1)

    tiers_data = resolved.get("tiers", {})
    scope = getattr(args, "scope", "be") or "be"

    import os
    env = os.environ.copy()

    result = run_unit_layers(
        tiers_data=tiers_data,
        scope=scope,
        project_root=project_root,
        env=env,
    )
    result["command"] = "unit"

    if not result.get("ok"):
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(5)
    _respond(result, 0)


def cmd_integration(args: argparse.Namespace) -> None:
    """integration 서브명령 — cmux-tool 에러코드 소비 → 폴백/에스컬레이션."""
    project_root = pathlib.Path(args.project_root) if args.project_root else None
    resolved = resolve_test_tools(project_root=project_root)
    if not resolved.get("ok"):
        print(json.dumps(resolved, ensure_ascii=False))
        sys.exit(1)

    tiers_data = resolved.get("tiers", {})
    scope = getattr(args, "scope", "be") or "be"
    url = getattr(args, "url", None)

    import os
    env = os.environ.copy()

    result = _run_integration(
        tiers_data=tiers_data,
        scope=scope,
        url=url,
        project_root=project_root,
        env=env,
    )
    result["command"] = "integration"

    if result.get("escalate"):
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(7)

    if not result.get("ok"):
        # e2e 실패(폴백도 실패한 경우)
        result.setdefault("error", "e2e_failed")
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(6)

    _respond(result, 0)


# ─────────────────────────────────────────────────────────────────────────────
# argparse 설정
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="test-tool",
        description="OPAL 테스트 단계별 도구 결정론적 집행기 — 4서브명령(resolve/check/unit/integration)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # resolve
    p_resolve = subparsers.add_parser("resolve", help="test-tools.yaml resolution_order 해석")
    p_resolve.add_argument("--stack", choices=["py", "ts"], help="스택 힌트 (py|ts)")
    p_resolve.add_argument("--project-root", metavar="PATH", help="프로젝트 루트 경로")

    # check
    p_check = subparsers.add_parser("check", help="도구 설치 상태 게이트 검사")
    p_check.add_argument("--category", metavar="C", help="카테고리 필터")
    p_check.add_argument("--tier", choices=["unit", "integration"], help="tier 필터")
    p_check.add_argument("--project-root", metavar="PATH", help="프로젝트 루트 경로")

    # unit
    p_unit = subparsers.add_parser("unit", help="lint→typecheck→unit stop-on-fail 단발 실행")
    p_unit.add_argument("--scope", choices=["fe", "be"], default="be", help="실행 범위 (fe|be)")
    p_unit.add_argument("--changed-files", nargs="*", metavar="FILE", help="변경 파일 목록 (선택)")
    p_unit.add_argument("--project-root", metavar="PATH", help="프로젝트 루트 경로")

    # integration
    p_integration = subparsers.add_parser("integration", help="cmux-tool → playwright 폴백 E2E + api_db")
    p_integration.add_argument("--scope", choices=["fe", "be"], default="be", help="실행 범위 (fe|be)")
    p_integration.add_argument("--url", metavar="URL", help="SUT URL (dev서버/localhost)")
    p_integration.add_argument("--project-root", metavar="PATH", help="프로젝트 루트 경로")

    return parser


# ─────────────────────────────────────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    dispatch = {
        "resolve": cmd_resolve,
        "check": cmd_check,
        "unit": cmd_unit,
        "integration": cmd_integration,
    }

    handler = dispatch.get(args.subcommand)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
