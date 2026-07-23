"""
@header {
  "module": "scenario",
  "layer": "util",
  "domain": "opal-tools",
  "description": "test-tool scenario-* 서브명령(scenario-init/scenario-lock/scenario-mark/scenario-status/scenario-red/scenario-fidelity-check/scenario-conformance/scenario-coverage-check) 핸들러. test-scenario.json SSOT(spec존/result존) 관리 — RED-first 동결 게이트(scenario-lock은 전 시나리오 red_confirmed==true일 때만 통과, self-confirming 방지) + scenario-mark는 locked==true 이후에만 허용. 069: 증거 충실도 사다리(mock<real-http<real-usage) 필드(required_fidelity/fidelity)와 시나리오별 부분 게이트(scenario-fidelity-check) + 표면(surface) 전수 conformance 판정(scenario-conformance, surfaces.json 분모)을 추가한다. 073: scenario-coverage-check — scenario-gate.md §3 정규화 페이로드(pilot-중립, test-scenario.json SSOT 미접촉)의 R/F/H↔시나리오 매핑 커버리지(루브릭 ②③④)를 결정론 판정한다(070 거짓 초록불 재발 방지). resolver/runner/e2e_adapter와 완전 격리되어 기존 4서브명령(resolve/check/unit/integration) 로직에 간섭하지 않는다(056/F-002). 타 도구의 SSOT는 일절 미접촉(축 분리, 069/H-7).",
  "exports": [
    "SCENARIO_ERROR_CODES",
    "FIDELITY_ORDER",
    "add_scenario_subparsers",
    "SCENARIO_DISPATCH",
    "cmd_scenario_init",
    "cmd_scenario_lock",
    "cmd_scenario_mark",
    "cmd_scenario_status",
    "cmd_scenario_red",
    "cmd_scenario_fidelity_check",
    "cmd_scenario_conformance",
    "cmd_scenario_coverage_check"
  ],
  "depends": []
}

test-tool scenario-* 핸들러 — test-scenario.json SSOT (spec존/result존 분리).

[MUST] PLAN.md §3.2.2 RED-first 동결 게이트(H-2): scenario-lock은 전 시나리오
  red_confirmed==true일 때만 locked=true. 미확인 시 red_not_confirmed exit 8
  (self-confirming 테스트로 T2→G 게이트 무력화 방지).
[MUST] scenario-mark --result는 locked==true 이후에만 허용.
  미충족 시 scenario_not_locked exit 9.
[MUST] 기존 test_tool.py의 resolve/check/unit/integration(dispatch/lib.resolver/
  lib.runner/lib.e2e_adapter) 로직 미간섭 — 본 모듈로 완전 격리.
[MUST] 신규 에러코드 8~11은 기존 4서브명령 exit code(0~7 계열)와 충돌 없이 배정됨
  (→ test_tool.py D-12:196-249 회귀 보호). 본 모듈 전용 SCENARIO_ERROR_CODES로 분리
  관리한다(test_tool.py의 ERROR_CODES 카탈로그는 미변경).
[MUST] (056/ADD-1) scenario-red — red_confirmed를 RED 증거와 함께 tool-gated로
  갱신하는 전용 경로. --evidence 필수(argparse required), locked==true 이후에는
  거부(scenario_already_locked exit 12, 8~11과 충돌 없는 신규 배정) — enforce-don't-advise
  보강(oppl-scenario-red-confirmed-gap.md). scenario-init의 red_confirmed 시드 입력은
  항상 무시(false 강제)한다 — RED 미관찰 상태를 시드로 우회 선언하는 경로 봉쇄.
[MUST] (069/F-005) required_fidelity(spec존, `.get(...,"mock")` 방어)/fidelity(result존,
  scenario-mark --fidelity로 기록, 미지정 mock) 사다리 필드. scenario-fidelity-check는
  전부-게이트가 아닌 **시나리오별 부분 게이트** — result==pass AND
  FIDELITY_ORDER[fidelity] >= FIDELITY_ORDER[required_fidelity] 미충족 시나리오만
  거부(fidelity_unmet exit 13, task:061 전부-게이트 붕괴 재발 방지).
[MUST] (069/F-006) surface_ref(spec존, nullable)로 시나리오-표면 연결. scenario-conformance는
  surfaces.json(표면 분모, 읽기 전용)을 소비하되 타 도구의 SSOT는 일절 미접촉(축 분리, H-7).
  surfaces.json 부재 시 applicable:false exit 0으로 스킵(M-5, 기존 프로젝트 무영향).
  auth:required 표면은 fidelity>=real-http 강제, 그 외는 시나리오 자신의
  required_fidelity(기본 mock)를 문턱으로 사용. 미충족 표면 존재 시 surface_unverified
  exit 14.
[MUST] (073/F-002) scenario-coverage-check — scenario-gate.md §3 정규화 페이로드
  (`{goal, requirements[], features[], hypotheses[], scenarios[]}`)를 --coverage-input
  <path>로 받아 R/F/H↔시나리오 매핑 커버리지(루브릭 ②③④, 결정론)를 판정한다.
  test-scenario.json SSOT는 미접촉(축 분리) — pilot-중립 transient 페이로드만 소비한다.
  missing.requirements/features/hypotheses 중 하나라도 non-empty면 coverage_unmet
  exit 16(070 거짓 초록불 재발 방지 — 미커버가 있는데 ok 반환 금지). 모두 empty면
  exit 0 + all_covered:true. 파일 부재/JSON 파손/필수 키 누락은 coverage_input_invalid
  exit 17. ①⑤⑥ 판단축(목표달성/채택잔존/경계부정)은 판정하지 않는다
  (opal-evaluator-agent scenario-rubric phase 소관). 기존 7서브명령·exit 8~14는 무변경
  (additive, H-2 회귀 보호).
"""

import argparse
import json
import pathlib
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

_KST = timezone(timedelta(hours=9))

# ─────────────────────────────────────────────────────────────────────────────
# 에러 코드 카탈로그 (scenario-* 전용, SSOT) — 기존 test_tool.py ERROR_CODES와 분리.
# exit 8~11 신규 배정 (기존 0~7과 충돌 없음).
# ─────────────────────────────────────────────────────────────────────────────

SCENARIO_ERROR_CODES: Dict[str, str] = {
    "red_not_confirmed":        "전 시나리오 red_confirmed==true 미충족 — scenario-lock 거부(H-2)",
    "scenario_not_locked":      "test-scenario.json locked==false — scenario-mark 거부",
    "scenario_not_initialized": "test-scenario.json 부재 — scenario-init 선행 필요",
    "scenario_spec_invalid_json": "--scenarios 인자 JSON 파싱 실패",
    "scenario_already_locked":  "test-scenario.json locked==true — scenario-red 거부(locked 후 spec존 변경 금지, 056/ADD-1)",
    "fidelity_unmet":           "요구 충실도 미달 시나리오 존재 — scenario-fidelity-check 거부(069/H-3)",
    "surface_unverified":       "conformance 미검증 표면 존재 — scenario-conformance 거부(069/H-4)",
    "surfaces_file_not_found":  "surfaces.json 부재(명시적 --surfaces 경로 포함) — applicable:false로 스킵(069/M-5, 정보용 배정)",
    "coverage_unmet":           "요구/기능/가설 미커버 존재 — scenario-coverage-check 거부(073/R-2)",
    "coverage_input_invalid":   "--coverage-input JSON 파싱/스키마 실패 — scenario-coverage-check 거부(073)",
}

# ─────────────────────────────────────────────────────────────────────────────
# 증거 충실도 사다리 (069/F-005·M-3) — mock < real-http < real-usage.
# verification.md §1 "증거 충실도" 규범(F-001)의 게이트 구현.
# ─────────────────────────────────────────────────────────────────────────────

FIDELITY_ORDER: Dict[str, int] = {"mock": 0, "real-http": 1, "real-usage": 2}


# ─────────────────────────────────────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _now_kst() -> str:
    """KST(UTC+9) ISO 8601 타임스탬프. test-tool은 date.js 미사용(D-11 §2.2.2)
    — 표준 라이브러리 datetime으로 자체 산출한다."""
    return datetime.now(_KST).strftime("%Y-%m-%dT%H:%M:%S+09:00")


def _respond(data: Dict[str, Any], exit_code: int = 0) -> None:
    """JSON 출력 후 지정 exit code로 종료 — test_tool.py `_respond`와 동일 계약."""
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(exit_code)


def _error(error_key: str, command: str, exit_code: int, detail: Optional[str] = None) -> None:
    """에러 응답 출력 후 지정 exit code로 종료 — test_tool.py `_error`와 동일 계약."""
    resp: Dict[str, Any] = {
        "ok": False,
        "command": command,
        "error": error_key,
    }
    if detail:
        resp["detail"] = detail
    print(json.dumps(resp, ensure_ascii=False))
    sys.exit(exit_code)


def _spec_path(task_path: pathlib.Path) -> pathlib.Path:
    return task_path / "test-scenario.json"


def _load_spec(task_path: pathlib.Path) -> Optional[Dict[str, Any]]:
    path = _spec_path(task_path)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_spec(task_path: pathlib.Path, spec: Dict[str, Any]) -> None:
    path = _spec_path(task_path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)


def _normalize_scenario(raw: Dict[str, Any]) -> Dict[str, Any]:
    """입력 시나리오 항목을 spec존/result존 완전한 형태로 정규화한다.

    [MUST] (056/ADD-1) red_confirmed는 입력값과 무관하게 항상 false로 생성한다 —
    scenario-init 시드로 "RED 미관찰 상태를 우회 선언"하는 경로를 봉쇄한다.
    red_confirmed는 오직 scenario-red(RED 증거 tool-gated 갱신)로만 true가 될 수
    있다. 시드 입력에 true가 있었는지 여부는 cmd_scenario_init이 별도로 감지해
    응답 warning으로 알린다(무시하되 침묵하지 않음).

    [MUST] (069/M-5) required_fidelity(spec존): `raw.get("required_fidelity","mock")`
    방어 접근 — 미지원 값(FIDELITY_ORDER 밖)은 "mock"으로 강등한다(관대한 기본값,
    R-E/H-6 회귀 0). fidelity(result존)는 scenario-mark --fidelity로만 갱신되며
    미지정 시 "mock" 기본값(M-5)."""
    required_fidelity = raw.get("required_fidelity", "mock")
    if required_fidelity not in FIDELITY_ORDER:
        required_fidelity = "mock"

    return {
        "id": raw.get("id"),
        "acceptance_ref": raw.get("acceptance_ref"),
        "type": raw.get("type"),
        "expected": raw.get("expected"),
        # spec존 — red_confirmed/red_evidence/red_at은 scenario-init에서 항상 초기값으로
        # 생성되며, red_confirmed는 scenario-red를 통해서만 true로 갱신될 수 있다.
        "red_confirmed": False,
        "red_evidence": None,
        "red_at": None,
        # spec존 — 증거 충실도 사다리 (069/F-005)
        "required_fidelity": required_fidelity,
        # spec존 — 검증 대상 표면 id (069/F-006, nullable)
        "surface_ref": raw.get("surface_ref"),
        # result존
        "result": raw.get("result"),
        "evidence": raw.get("evidence"),
        "marked_at": raw.get("marked_at"),
        # result존 — 실제 관찰된 충실도 (069/F-005, scenario-mark --fidelity로 기록)
        "fidelity": raw.get("fidelity", "mock"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 서브명령 핸들러
# ─────────────────────────────────────────────────────────────────────────────

def cmd_scenario_init(args: argparse.Namespace) -> None:
    """scenario-init — test-scenario.json 생성 (spec존, locked=false)."""
    task_path = pathlib.Path(args.task_path)
    raw_arg = getattr(args, "scenarios", None)

    try:
        scenarios_input: List[Dict[str, Any]] = json.loads(raw_arg) if raw_arg else []
        if not isinstance(scenarios_input, list):
            raise ValueError("scenarios must be a JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        _error("scenario_spec_invalid_json", "scenario-init", 11, detail=str(e))
        return

    # (056/ADD-1) red_confirmed 시드 입력 무력화: _normalize_scenario가 항상 false로
    # 강제하므로 여기서는 "무시된 시도"만 감지해 응답 warning으로 알린다(무시하되 침묵하지 않음).
    seeded_ids = [
        s.get("id") for s in scenarios_input
        if isinstance(s, dict) and bool(s.get("red_confirmed"))
    ]

    scenarios = [_normalize_scenario(s) for s in scenarios_input]

    task_path.mkdir(parents=True, exist_ok=True)

    now = _now_kst()
    spec = {
        "schema_version": "1.0",
        "task_id": task_path.name,
        "locked": False,
        "created_at": now,
        "locked_at": None,
        "scenarios": scenarios,
    }
    _save_spec(task_path, spec)

    resp: Dict[str, Any] = {
        "ok": True,
        "command": "scenario-init",
        "task_id": spec["task_id"],
        "scenarios_count": len(scenarios),
    }
    if seeded_ids:
        resp["warning"] = (
            f"red_confirmed seed ignored (forced false): {seeded_ids} — "
            "RED 증거는 scenario-red로만 기록할 수 있다(056/ADD-1)"
        )
    _respond(resp, 0)


def cmd_scenario_lock(args: argparse.Namespace) -> None:
    """scenario-lock — 전 시나리오 red_confirmed==true일 때만 locked=true (RED-first 게이트, H-2)."""
    task_path = pathlib.Path(args.task_path)
    spec = _load_spec(task_path)
    if spec is None:
        _error("scenario_not_initialized", "scenario-lock", 10)
        return

    scenarios = spec.get("scenarios", [])
    unconfirmed = [s.get("id") for s in scenarios if not s.get("red_confirmed")]
    if unconfirmed:
        _error(
            "red_not_confirmed", "scenario-lock", 8,
            detail=f"red_confirmed==false: {unconfirmed}",
        )
        return

    now = _now_kst()
    spec["locked"] = True
    spec["locked_at"] = now
    _save_spec(task_path, spec)

    _respond({
        "ok": True,
        "command": "scenario-lock",
        "locked": True,
        "locked_at": now,
    }, 0)


def cmd_scenario_mark(args: argparse.Namespace) -> None:
    """scenario-mark — result존 기록 (locked 후에만 허용)."""
    task_path = pathlib.Path(args.task_path)
    spec = _load_spec(task_path)
    if spec is None:
        _error("scenario_not_initialized", "scenario-mark", 10)
        return

    if not spec.get("locked"):
        _error("scenario_not_locked", "scenario-mark", 9)
        return

    scenario_id = args.id
    target = next((s for s in spec.get("scenarios", []) if s.get("id") == scenario_id), None)
    if target is None:
        _error("scenario_not_initialized", "scenario-mark", 10, detail=f"unknown scenario id: {scenario_id}")
        return

    now = _now_kst()
    target["result"] = args.result
    target["evidence"] = getattr(args, "evidence", None)
    target["marked_at"] = now
    # (069/M-5) --fidelity 미지정 시 "mock" 기본값(관대한 기본값, 실제 충실도 미기록 결과는
    # 목 수준으로 간주).
    target["fidelity"] = getattr(args, "fidelity", None) or "mock"
    _save_spec(task_path, spec)

    _respond({
        "ok": True,
        "command": "scenario-mark",
        "scenario_id": scenario_id,
        "result": args.result,
    }, 0)


def cmd_scenario_red(args: argparse.Namespace) -> None:
    """scenario-red — RED 증거와 함께 red_confirmed를 tool-gated로 갱신한다(056/ADD-1).

    locked==true 이후에는 spec존 변경을 거부한다(scenario_already_locked exit 12) —
    RED 확인은 항상 동결 이전에 이루어져야 한다는 계약을 tool 레벨에서 강제한다."""
    task_path = pathlib.Path(args.task_path)
    spec = _load_spec(task_path)
    if spec is None:
        _error("scenario_not_initialized", "scenario-red", 10)
        return

    if spec.get("locked"):
        _error("scenario_already_locked", "scenario-red", 12)
        return

    scenario_id = args.id
    target = next((s for s in spec.get("scenarios", []) if s.get("id") == scenario_id), None)
    if target is None:
        _error("scenario_not_initialized", "scenario-red", 10, detail=f"unknown scenario id: {scenario_id}")
        return

    now = _now_kst()
    target["red_confirmed"] = True
    target["red_evidence"] = args.evidence
    target["red_at"] = now
    _save_spec(task_path, spec)

    _respond({
        "ok": True,
        "command": "scenario-red",
        "scenario_id": scenario_id,
        "red_confirmed": True,
        "red_at": now,
    }, 0)


def cmd_scenario_status(args: argparse.Namespace) -> None:
    """scenario-status — spec/result 요약 (RED 확인 수·통과율)."""
    task_path = pathlib.Path(args.task_path)
    spec = _load_spec(task_path)
    if spec is None:
        _error("scenario_not_initialized", "scenario-status", 10)
        return

    scenarios = spec.get("scenarios", [])
    total = len(scenarios)
    red_confirmed = sum(1 for s in scenarios if s.get("red_confirmed") is True)
    passed = sum(1 for s in scenarios if s.get("result") == "pass")
    failed = sum(1 for s in scenarios if s.get("result") == "fail")

    _respond({
        "ok": True,
        "command": "scenario-status",
        "locked": bool(spec.get("locked", False)),
        "total": total,
        "red_confirmed": red_confirmed,
        "passed": passed,
        "failed": failed,
    }, 0)


def cmd_scenario_fidelity_check(args: argparse.Namespace) -> None:
    """scenario-fidelity-check — 시나리오별 부분 게이트(069/F-005).

    [MUST] 전부-게이트가 아니다(task:061 재발 방지, M-3) — 각 시나리오를 독립 판정하여
    `result==pass AND FIDELITY_ORDER[fidelity] >= FIDELITY_ORDER[required_fidelity]`를
    만족하지 못하는 시나리오만 `unmet`에 모은다."""
    task_path = pathlib.Path(args.task_path)
    spec = _load_spec(task_path)
    if spec is None:
        _error("scenario_not_initialized", "scenario-fidelity-check", 10)
        return

    scenarios = spec.get("scenarios", [])
    unmet: List[str] = []
    for s in scenarios:
        required = s.get("required_fidelity", "mock")
        actual = s.get("fidelity", "mock")
        result = s.get("result")
        met = (
            result == "pass"
            and FIDELITY_ORDER.get(actual, 0) >= FIDELITY_ORDER.get(required, 0)
        )
        if not met:
            unmet.append(s.get("id"))

    if unmet:
        _error("fidelity_unmet", "scenario-fidelity-check", 13, detail=unmet)
        return

    _respond({
        "ok": True,
        "command": "scenario-fidelity-check",
        "all_met": True,
        "total": len(scenarios),
        "met": len(scenarios),
    }, 0)


def cmd_scenario_conformance(args: argparse.Namespace) -> None:
    """scenario-conformance — 표면(surface) 전수 conformance 판정(069/F-006).

    [MUST] surfaces.json(표면 분모, 읽기 전용)만 소비하며 타 도구의 SSOT는 일절
    미접촉한다(축 분리, H-7). surfaces.json 부재 시 `applicable:false`로 스킵한다
    (M-5 — 기존 프로젝트·비-API 프로젝트 무영향). auth:required 표면은
    fidelity>=real-http를 강제하고, 그 외 표면은 매칭 시나리오 자신의
    required_fidelity(기본 mock)를 문턱으로 사용한다."""
    task_path = pathlib.Path(args.task_path)
    surfaces_arg = getattr(args, "surfaces", None)
    surfaces_path = pathlib.Path(surfaces_arg) if surfaces_arg else (task_path / "surfaces.json")

    if not surfaces_path.exists():
        _respond({
            "ok": True,
            "command": "scenario-conformance",
            "applicable": False,
        }, 0)
        return

    with open(surfaces_path, encoding="utf-8") as f:
        surfaces_doc = json.load(f)

    spec = _load_spec(task_path)
    if spec is None:
        _error("scenario_not_initialized", "scenario-conformance", 10)
        return

    scenarios = spec.get("scenarios", [])
    surfaces = surfaces_doc.get("surfaces", [])

    unverified: List[str] = []
    for surface in surfaces:
        surface_id = surface.get("id")
        auth = surface.get("auth", "none")
        verified = False
        for s in scenarios:
            if s.get("surface_ref") != surface_id or s.get("result") != "pass":
                continue
            actual = FIDELITY_ORDER.get(s.get("fidelity", "mock"), 0)
            if auth == "required":
                threshold = FIDELITY_ORDER["real-http"]
            else:
                threshold = FIDELITY_ORDER.get(s.get("required_fidelity", "mock"), 0)
            if actual >= threshold:
                verified = True
                break
        if not verified:
            unverified.append(surface_id)

    if unverified:
        _respond({
            "ok": False,
            "command": "scenario-conformance",
            "error": "surface_unverified",
            "detail": unverified,
            "all_surfaces_green": False,
        }, 14)
        return

    _respond({
        "ok": True,
        "command": "scenario-conformance",
        "all_surfaces_green": True,
        "surface_count": len(surfaces),
    }, 0)


_COVERAGE_REQUIRED_KEYS = ("goal", "requirements", "features", "hypotheses", "scenarios")


def cmd_scenario_coverage_check(args: argparse.Namespace) -> None:
    """scenario-coverage-check — 정규화 페이로드(scenario-gate.md §3)의 R/F/H ↔ 시나리오
    매핑 커버리지를 결정론 판정한다(루브릭 ②③④, 073/F-002). test-scenario.json SSOT
    미접촉 — pilot-중립 transient 페이로드(--coverage-input <path>)만 소비한다(축 분리,
    ANALYSIS.md 073 §4 발견①). ①⑤⑥ 판단축(목표달성/채택잔존/경계부정)은 판정하지
    않는다(opal-evaluator-agent scenario-rubric phase 소관)."""
    coverage_input_path = pathlib.Path(args.coverage_input)

    if not coverage_input_path.exists():
        _error(
            "coverage_input_invalid", "scenario-coverage-check", 17,
            detail=f"--coverage-input 파일 부재: {coverage_input_path}",
        )
        return

    try:
        with open(coverage_input_path, encoding="utf-8") as f:
            payload = json.load(f)
    except json.JSONDecodeError as e:
        _error(
            "coverage_input_invalid", "scenario-coverage-check", 17,
            detail=f"--coverage-input JSON 파싱 실패: {e}",
        )
        return

    if not isinstance(payload, dict):
        _error(
            "coverage_input_invalid", "scenario-coverage-check", 17,
            detail="--coverage-input 페이로드는 JSON object여야 한다",
        )
        return

    missing_keys = [k for k in _COVERAGE_REQUIRED_KEYS if k not in payload]
    if missing_keys:
        _error(
            "coverage_input_invalid", "scenario-coverage-check", 17,
            detail=f"필수 키 누락: {missing_keys}",
        )
        return

    requirements = payload.get("requirements") or []
    features = payload.get("features") or []
    hypotheses = payload.get("hypotheses") or []
    scenarios = payload.get("scenarios") or []

    covered_requirements: set = set()
    covered_features: set = set()
    covered_hypotheses: set = set()
    for s in scenarios:
        covered_requirements.update(s.get("covers_requirements") or [])
        covered_features.update(s.get("covers_features") or [])
        covered_hypotheses.update(s.get("covers_hypotheses") or [])

    missing = {
        "requirements": [r for r in requirements if r not in covered_requirements],
        "features": [f for f in features if f not in covered_features],
        "hypotheses": [h for h in hypotheses if h not in covered_hypotheses],
    }

    if missing["requirements"] or missing["features"] or missing["hypotheses"]:
        _error(
            "coverage_unmet", "scenario-coverage-check", 16,
            detail={"missing": missing},
        )
        return

    _respond({
        "ok": True,
        "command": "scenario-coverage-check",
        "goal": payload.get("goal"),
        "all_covered": True,
        "counts": {
            "requirements": len(requirements),
            "features": len(features),
            "hypotheses": len(hypotheses),
            "scenarios": len(scenarios),
        },
    }, 0)


# ─────────────────────────────────────────────────────────────────────────────
# argparse 서브파서 등록 + dispatch 테이블
# ─────────────────────────────────────────────────────────────────────────────

def add_scenario_subparsers(subparsers: "argparse._SubParsersAction") -> None:
    """test_tool.py `_build_parser`의 top-level subparsers 객체에
    scenario-init/scenario-lock/scenario-mark/scenario-status/scenario-red/
    scenario-fidelity-check/scenario-conformance/scenario-coverage-check 8종을 추가한다."""

    p_init = subparsers.add_parser("scenario-init", help="test-scenario.json 생성 (spec존, locked=false)")
    p_init.add_argument("--task-path", required=True, metavar="PATH", help="태스크 폴더 경로")
    p_init.add_argument("--scenarios", metavar="JSON", help="시나리오 배열 JSON (선택, 기본 [])")

    p_lock = subparsers.add_parser("scenario-lock", help="전 시나리오 red_confirmed==true일 때만 동결(locked=true)")
    p_lock.add_argument("--task-path", required=True, metavar="PATH", help="태스크 폴더 경로")

    p_mark = subparsers.add_parser("scenario-mark", help="locked 후 result존 기록")
    p_mark.add_argument("--task-path", required=True, metavar="PATH", help="태스크 폴더 경로")
    p_mark.add_argument("--id", required=True, metavar="S", help="시나리오 id")
    p_mark.add_argument("--result", required=True, choices=["pass", "fail"], help="판정 결과")
    p_mark.add_argument("--evidence", metavar="E", help="증거 문자열 (선택)")
    p_mark.add_argument(
        "--fidelity", choices=["mock", "real-http", "real-usage"],
        help="실제 관찰된 증거 충실도 (선택, 미지정 시 mock — 069/M-5)",
    )

    p_status = subparsers.add_parser("scenario-status", help="spec/result 요약 (RED 확인·통과율)")
    p_status.add_argument("--task-path", required=True, metavar="PATH", help="태스크 폴더 경로")

    p_red = subparsers.add_parser(
        "scenario-red",
        help="RED 증거와 함께 red_confirmed를 tool-gated로 갱신 (locked 전에만 허용, 056/ADD-1)",
    )
    p_red.add_argument("--task-path", required=True, metavar="PATH", help="태스크 폴더 경로")
    p_red.add_argument("--id", required=True, metavar="S", help="시나리오 id")
    p_red.add_argument("--evidence", required=True, metavar="E", help="RED 실패 출력 요약 (필수)")

    p_fidelity = subparsers.add_parser(
        "scenario-fidelity-check",
        help="시나리오별 요구 충실도 부분 게이트(069/F-005 — 전부-게이트 아님, task:061 재발 방지)",
    )
    p_fidelity.add_argument("--task-path", required=True, metavar="PATH", help="태스크 폴더 경로")

    p_conformance = subparsers.add_parser(
        "scenario-conformance",
        help="표면(surface) 전수 conformance 판정(069/F-006 — surfaces.json 분모, 부재 시 스킵)",
    )
    p_conformance.add_argument("--task-path", required=True, metavar="PATH", help="태스크 폴더 경로")
    p_conformance.add_argument(
        "--surfaces", metavar="PATH",
        help="surfaces.json 경로 (선택, 기본 <task-path>/surfaces.json — 부재 시 applicable:false)",
    )

    p_coverage = subparsers.add_parser(
        "scenario-coverage-check",
        help="정규화 페이로드(scenario-gate.md §3)의 R/F/H↔시나리오 매핑 커버리지 결정론 판정(073/F-002)",
    )
    p_coverage.add_argument(
        "--coverage-input", required=True, metavar="PATH",
        help="정규화 페이로드 JSON 경로 (goal/requirements/features/hypotheses/scenarios, test-scenario.json과 무관)",
    )


SCENARIO_DISPATCH: Dict[str, Any] = {
    "scenario-init": cmd_scenario_init,
    "scenario-lock": cmd_scenario_lock,
    "scenario-mark": cmd_scenario_mark,
    "scenario-status": cmd_scenario_status,
    "scenario-red": cmd_scenario_red,
    "scenario-fidelity-check": cmd_scenario_fidelity_check,
    "scenario-conformance": cmd_scenario_conformance,
    "scenario-coverage-check": cmd_scenario_coverage_check,
}
