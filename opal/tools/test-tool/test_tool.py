"""
@header {
  "module": "test_tool",
  "layer": "util",
  "domain": "opal-tools",
  "description": "test-tool CLI — resolve/check/unit/integration · e2e · scenario-* argparse 라우터 + ERROR_CODES 카탈로그 + JSON 출력 헬퍼. integration은 Ego Lite → cmux → Playwright 우선순위 후보 체인을 돈다.",
  "exports": [
    "main",
    "ERROR_CODES"
  ],
  "depends": [
    "lib.resolver",
    "lib.runner",
    "lib.e2e_adapter",
    "lib.e2e_contract",
    "lib.scenario"
  ]
}

test-tool — test-tool public CLI router.

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
from lib.e2e_contract import status_to_exit
from lib.scenario import add_scenario_subparsers, SCENARIO_DISPATCH
from lib.e2e.target import TARGET_KINDS

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
    "e2e_failed":         "E2E 테스트 실패 — browser executor 후보 전건 실패",
    "escalation":         "cmux-tool 에스컬레이션 에러코드 — 폴백 금지, 호출자 수정 필요",
    "e2e_infra_error":    "E2E 실행 인프라 오류 — provider 오류 또는 환경 오류",
    "executor_unavailable": "E2E executor 후보 소진 — 실행 수단 없음",
    "e2e_blocked":        "E2E 외부 조건 차단",
    "e2e_awaiting_human": "E2E 사람 입력 대기 — 재개 가능한 중간 상태",
    # e2e run 진입 오류 — 최종 status·error·exit는 e2e_contract가 소유하므로, 아래 키는
    # run.json/stdout의 `detail_code`에만 실린다(CONTRACT.md 계약 규칙 C-125-1).
    "e2e_target_invalid":            "--target이 3종 enum도 실재 디렉터리도 아님",
    "e2e_opal_home_required":        "--target=installed인데 --opal-home 미지정",
    "e2e_opal_home_unprepared":      "--opal-home 트리 미준비 — 하네스는 install을 호출하지 않음",
    "e2e_opal_home_is_user_owned":   "--opal-home이 사용자 실제 ~/.opal과 동일 — 거부",
    "e2e_port_lease_failed":         "포트 임대 실패 — allocator lock 또는 가용 포트 소진",
    "e2e_run_id_exhausted":          "당일 run_id 순번 소진",
    "e2e_scenario_not_found":        "test-scenario.json 또는 해당 시나리오 id 없음",
    "e2e_scenario_contract_invalid": "시나리오가 schema_version 2.0 계약을 만족하지 않음",
    "e2e_sut_startup_failed":        "임대 포트 위 SUT 기동·health 실패",
    "e2e_no_executor_registered":    "등록된 executor 후보 0 — 후보 소진",
    "e2e_scenario_runner_absent":    "시나리오 step 실행기 미등록",
    "e2e_executor_contract_mismatch": "profile이 요구하는 executor를 시나리오 step이 갖지 않음 — 실행 전 정적 거부(CONTRACT.md §C.4)",
    "e2e_step_executor_not_selected": "시나리오 step이 요구한 executor가 선택된 후보에 없음",
    "e2e_core_ui_behavior_substituted_by_api": "핵심 UI 행동의 검증을 step_role=verify API step이 대체 — real-usage 미승격(§C.4)",
    # §B.1.3 조회 명령의 대상 부재. 새 exit 값을 배정하지 않고 기존 usage 오류 코드를 쓴다.
    "run_not_found":                 "지정한 run_id·artifact-dir에 해당하는 run 산출물 없음",
    "e2e_resume_state_not_found":    "재개 대상 run의 handoff 색인 없음 — awaiting_human 정지 이력 부재",
    "e2e_resume_token_expired":      "resume token 만료 — timeout은 fail이 아니라 blocked (C-HUM-2)",
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
    """integration 서브명령 — Ego Lite→cmux→Playwright 후보 계약 실행."""
    project_root = pathlib.Path(args.project_root) if args.project_root else None
    resolved = resolve_test_tools(project_root=project_root)
    if not resolved.get("ok"):
        print(json.dumps(resolved, ensure_ascii=False))
        sys.exit(1)

    tiers_data = resolved.get("tiers", {})
    scope = getattr(args, "scope", "be") or "be"
    url = getattr(args, "url", None)
    expect_text = getattr(args, "expect_text", None)
    ego_install_choice = getattr(args, "ego_install_choice", None)

    import os
    env = os.environ.copy()

    result = _run_integration(
        tiers_data=tiers_data,
        scope=scope,
        url=url,
        project_root=project_root,
        env=env,
        expect_text=expect_text,
        ego_install_choice=ego_install_choice,
    )
    result["command"] = "integration"

    status = result.get("status") or result.get("e2e", {}).get("status")
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(status_to_exit(status or ("pass" if result.get("ok") else "fail")))


def cmd_e2e(args: argparse.Namespace) -> None:
    """e2e 서브명령군 라우터 — `run`·`resume`·`status`·`clean`(§B.1.1~§B.1.4).

    `run`·`resume`의 exit은 `status_to_exit()` 결과로만 결정한다. 재시도 루프를 내장하지
    않는다. `status`·`clean`은 조회·정리 명령이므로 exit `0`이며(§B.1.3·§B.1.4) 새 exit
    값을 배정하지 않는다 — `clean`의 `infra_error` 승격도 payload로만 알린다.
    """
    from lib.e2e.orchestrator import run_e2e

    if args.e2e_command == "status":
        from lib.e2e.orchestrator import run_status

        found = run_status(
            run_id=getattr(args, "run_id", None),
            artifact_dir=getattr(args, "artifact_dir", None),
            artifact_root=getattr(args, "artifact_root", None),
        )
        if found.get("error"):
            # §B.1.3 — 대상 부재는 기존 도구의 usage 오류 코드를 쓴다.
            _error(found["error"], detail=f"run_id={found.get('run_id')!r}", command="e2e status")
            return
        _respond(found, 0)
        return

    if args.e2e_command == "clean":
        from lib.e2e.orchestrator import run_clean

        cleaned = run_clean(
            run_id=getattr(args, "run_id", None),
            stale=bool(getattr(args, "stale", False)),
            artifact_root=getattr(args, "artifact_root", None),
            dry_run=bool(getattr(args, "dry_run", False)),
        )
        if cleaned.get("error") == "run_not_found":
            _error(cleaned["error"], detail=f"run_id={cleaned.get('run_id')!r}", command="e2e clean")
            return
        _respond(cleaned, 0)
        return

    if args.e2e_command == "resume":
        # §B.1.2 — 판정은 여기서 만들지 않는다. human executor가 scenario.py의 기존
        # resume 검증(:482-528)을 호출하고 그 결과를 payload로 옮긴다(TRD.md TD-18).
        from lib.e2e.executors.human import run_resume

        resumed = run_resume(
            run_id=args.run_id,
            token=args.token,
            submission=args.submission,
            artifact_root=getattr(args, "artifact_root", None),
        )
        _respond(resumed, resumed["exit_code"])
        return

    if args.e2e_command != "run":
        _error("no_runner", detail=f"unknown e2e subcommand: {args.e2e_command}", command="e2e")
        return

    payload = run_e2e(
        target=args.target,
        scenario_id=args.scenario,
        task_path=args.task_path,
        worktree_root=getattr(args, "worktree_root", None),
        opal_home=getattr(args, "opal_home", None),
        artifact_root=getattr(args, "artifact_root", None),
        run_id=getattr(args, "run_id", None),
    )
    _respond(payload, payload["exit_code"])


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
    p_integration = subparsers.add_parser("integration", help="Ego Lite → cmux → Playwright 후보 전환 E2E + api_db")
    p_integration.add_argument("--scope", choices=["fe", "be"], default="be", help="실행 범위 (fe|be)")
    p_integration.add_argument("--url", metavar="URL", help="SUT URL (dev서버/localhost)")
    p_integration.add_argument("--expect-text", metavar="TEXT", help="브라우저에서 확인할 의미 문자열")
    p_integration.add_argument(
        "--ego-install-choice",
        choices=["manual", "r2", "cancel"],
        help="Ego Lite 미설치 handoff에 대한 사용자 선택",
    )
    p_integration.add_argument("--project-root", metavar="PATH", help="프로젝트 루트 경로")

    # e2e — 임대 SUT 위 1회 실행·판정 (CONTRACT.md §B.1)
    p_e2e = subparsers.add_parser("e2e", help="E2E 하네스 — 임대 포트 SUT 위 1회 실행·판정")
    e2e_sub = p_e2e.add_subparsers(dest="e2e_command", required=True)
    p_e2e_run = e2e_sub.add_parser("run", help="대상 소스를 해석하고 포트를 임대해 1회 실행한다")
    # §B.1.1 표 — --scenario·--task-path·--target 필수, 나머지 조건부/선택.
    p_e2e_run.add_argument("--scenario", required=True, metavar="ID",
                           help="test-scenario.json의 시나리오 id (schema_version 2.0)")
    p_e2e_run.add_argument("--task-path", required=True, metavar="PATH", help="태스크 폴더 절대경로")
    p_e2e_run.add_argument("--target", required=True, choices=list(TARGET_KINDS),
                           help="대상 소스 3종")
    p_e2e_run.add_argument("--worktree-root", metavar="PATH",
                           help="--target=source-worktree일 때 (미지정 시 git rev-parse --show-toplevel)")
    p_e2e_run.add_argument("--opal-home", metavar="PATH", help="--target=installed일 때 준비된 격리 OPAL_HOME")
    p_e2e_run.add_argument("--artifact-root", metavar="PATH", help="산출물·lease 루트 (기본 ${TMPDIR}/opal-e2e-runs)")
    p_e2e_run.add_argument("--run-id", metavar="ID", help="run_id 지정 (미지정 시 생성)")

    # §B.1.2 표 — --run-id·--token·--submission 필수, --artifact-root만 선택.
    p_e2e_resume = e2e_sub.add_parser(
        "resume", help="awaiting_human으로 정지한 run을 동일 run-id·resume token으로 재개한다"
    )
    p_e2e_resume.add_argument("--run-id", required=True, metavar="ID", help="정지한 run의 run_id")
    p_e2e_resume.add_argument("--token", required=True, metavar="TOKEN", help="handoff가 발행한 resume token")
    p_e2e_resume.add_argument("--submission", required=True, metavar="PATH",
                              help="CONTRACT.md §A.10 스키마 제출물 JSON 경로")
    p_e2e_resume.add_argument("--artifact-root", metavar="PATH", help="산출물·lease 루트 (기본 ${TMPDIR}/opal-e2e-runs)")

    # §B.1.3 표 — (--run-id | --artifact-dir) 택일 + --artifact-root 선택. 조회 명령이므로
    # 아무것도 변경하지 않으며 exit은 0이다.
    p_e2e_status = e2e_sub.add_parser(
        "status", help="지정 run의 상태·증적 경로·소유 자원을 조회한다 (변경 없음)"
    )
    status_target = p_e2e_status.add_mutually_exclusive_group(required=True)
    status_target.add_argument("--run-id", metavar="ID", help="조회할 run의 run_id")
    status_target.add_argument("--artifact-dir", metavar="PATH", help="run 산출물 디렉터리 직접 지정")
    p_e2e_status.add_argument("--artifact-root", metavar="PATH", help="산출물·lease 루트 (기본 ${TMPDIR}/opal-e2e-runs)")

    # §B.1.4 표 — (--run-id | --stale) 택일 + --artifact-root·--dry-run 선택.
    # [MUST] 회수 대상은 owned.json 대장에 오른 자원뿐이며(TD-15) 프로세스 이름 패턴
    # 매칭을 쓰지 않고 opal-cli의 console PID 파일을 보지 않는다(§C.1).
    p_e2e_clean = e2e_sub.add_parser(
        "clean", help="owned.json 대장에 오른 자원만 회수한다 (user_owned=true는 제외)"
    )
    clean_target = p_e2e_clean.add_mutually_exclusive_group(required=True)
    clean_target.add_argument("--run-id", metavar="ID", help="정리할 run의 run_id")
    clean_target.add_argument(
        "--stale", action="store_true", help="owner_pid가 죽은 lease record와 그에 딸린 프로세스 그룹 회수"
    )
    p_e2e_clean.add_argument("--artifact-root", metavar="PATH", help="산출물·lease 루트 (기본 ${TMPDIR}/opal-e2e-runs)")
    p_e2e_clean.add_argument("--dry-run", action="store_true", help="회수 대상만 계산하고 실제로 회수하지 않는다")

    # scenario-init / scenario-lock / scenario-mark / scenario-status (lib/scenario.py로 격리)
    add_scenario_subparsers(subparsers)

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
        "e2e": cmd_e2e,
        **SCENARIO_DISPATCH,
    }

    handler = dispatch.get(args.subcommand)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
