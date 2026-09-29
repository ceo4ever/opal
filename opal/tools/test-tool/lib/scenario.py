"""
@header {
  "module": "scenario",
  "task": "056,069,073,111,167",
  "layer": "util",
  "domain": "opal-tools",
  "description": "test-tool scenario-* 서브명령 핸들러. test-scenario.json spec/result SSOT와 RED 동결, v2 E2E verdict-json/handoff runtime validation, fidelity/conformance/coverage gate, 유형 열 검증·정확 중복 거부, 목표-커버 게이트 기록·검증을 관리한다.",
  "exports": [
    "SCENARIO_ERROR_CODES",
    "FIDELITY_ORDER",
    "SCENARIO_TYPE_VALUES",
    "SCENARIO_GATE_RETRY_LIMIT",
    "add_scenario_subparsers",
    "SCENARIO_DISPATCH",
    "cmd_scenario_init",
    "cmd_scenario_lock",
    "cmd_scenario_mark",
    "cmd_scenario_status",
    "cmd_scenario_red",
    "cmd_scenario_fidelity_check",
    "cmd_scenario_conformance",
    "cmd_scenario_coverage_check",
    "cmd_scenario_coverage_build",
    "cmd_scenario_gate_record",
    "cmd_scenario_gate_verify"
  ],
  "depends": ["lib.e2e_contract"]
}

test-tool scenario-* 핸들러 — test-scenario.json SSOT (spec존/result존 분리).

[MUST] RED-first 동결 게이트: scenario-lock은 red_required==true인 시나리오가 모두
  red_confirmed==true일 때만 locked=true. red_required가 없는 기존 JSON은 true로 간주한다.
  미확인 시 red_not_confirmed exit 8
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
[MUST] (111/W-5) scenario-coverage-build — sdlc-v2 TASK/PLAN/TEST-SCENARIO를
  `{task_folder}/.scenario-coverage-input.json`으로 변환한다. TASK AC/C, TEST S 및
  검증 대상 토큰을 고정 파싱하고, PLAN H는 optional로 파싱한다. W는 features로 넣지
  않는다. Markdown escape 파이프(`\\|`)는 셀 내용으로 보존하고, 열 수가 다른 표 행,
  unknown ref, 필수 AC/C 추출 실패, S 0건, 중복 S-ID는 coverage_input_invalid exit 17로
  거부한다.
[MUST] (167/AC-2,AC-3) scenario-coverage-build — Scenarios 표 헤더에 `유형`이 있으면
  모든 행이 SCENARIO_TYPE_VALUES(unit·integration·contract·regression·e2e·check) 중
  하나여야 하고, 각 scenario payload에 `type`(열 없으면 null)과 `red_required`(`시점`에
  `구현 전 RED` 포함 여부)를 싣는다. `check`+구현 전 RED 모순, 유형 열이 있는 문서에서
  6셀(유형·조건·행동·기대 결과·방법·환경·시점, 공백 정규화) 완전 동일 중복은
  coverage_input_invalid exit 17로 거부한다. build가 exit 17이면 남아 있던
  `.scenario-coverage-input.json`을 먼저 지운다(재판정 오염 방지).
[MUST] (167/AC-2,AC-3) scenario-init(e2e_contract.validate_scenario_contract 경유) —
  `type` 허용값에 `check`를 추가하고, `type=check`이면서 `red_required`가 참(미지정
  기본 true 포함)이면 scenario_contract_invalid exit 17로 거부한다.
[MUST] (167/AC-4~AC-7) scenario-gate-record/scenario-gate-verify — 목표-커버 게이트
  이력(`.scenario-gate-history.json`, 배열 additive)에 회차별 판정을 기록·검증한다.
  advisory 형식·응답 완전성 위반은 각각 scenario_gate_record_invalid exit 18,
  advisory_response_invalid exit 19다. apply 응답은 verdict:rewrite·reason:advisory_apply·
  counted:false로 기록되고 다음 회차(refinement)에서 pass/converged 또는
  escalate/advisory_refinement_failed로 닫힌다. `--input-error`/`--evidence-error`는
  evaluator·응답 검사를 건너뛰는 별도 모드이며 서로 배타적이다. counted:true 원소가
  SCENARIO_GATE_RETRY_LIMIT(3)에 도달하면 escalate/retry_limit, 직전 counted 원소 대비
  개선이 없으면 escalate/no_progress다. scenario-gate-verify는 이력 마지막 원소가
  verdict:pass이고 그 bundle_hash가 현재 TASK.md/PLAN.md/producer 산출물 sha256 묶음과
  같을 때만 exit 0이고, 아니면 scenario_gate_not_passed exit 20이다.
"""

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Set

from lib.e2e_contract import (
    E2E_CONTRACT_SCHEMA_VERSION,
    FINAL_STATUSES,
    HANDOFF_REQUIRED_FIELDS,
    OPERATIONAL_STATUSES,
    build_verdict,
    status_to_error,
    status_to_exit,
    validate_pass_requirements,
    validate_scenario_contract,
)

_KST = timezone(timedelta(hours=9))

# ─────────────────────────────────────────────────────────────────────────────
# 에러 코드 카탈로그 (scenario-* 전용, SSOT) — 기존 test_tool.py ERROR_CODES와 분리.
# exit 8~11 신규 배정 (기존 0~7과 충돌 없음).
# ─────────────────────────────────────────────────────────────────────────────

SCENARIO_ERROR_CODES: Dict[str, str] = {
    "red_not_confirmed":        "RED 대상 시나리오의 red_confirmed==true 미충족 — scenario-lock 거부",
    "scenario_not_locked":      "test-scenario.json locked==false — scenario-mark 거부",
    "scenario_not_initialized": "test-scenario.json 부재 — scenario-init 선행 필요",
    "scenario_spec_invalid_json": "--scenarios 인자 JSON 파싱 실패",
    "scenario_already_locked":  "test-scenario.json locked==true — scenario-red 거부(locked 후 spec존 변경 금지, 056/ADD-1)",
    "fidelity_unmet":           "요구 충실도 미달 시나리오 존재 — scenario-fidelity-check 거부(069/H-3)",
    "surface_unverified":       "conformance 미검증 표면 존재 — scenario-conformance 거부(069/H-4)",
    "surfaces_file_not_found":  "surfaces.json 부재(명시적 --surfaces 경로 포함) — applicable:false로 스킵(069/M-5, 정보용 배정)",
    "coverage_unmet":           "요구/기능/가설 미커버 존재 — scenario-coverage-check 거부(073/R-2)",
    "coverage_input_invalid":   "--coverage-input JSON 파싱/스키마 실패 — scenario-coverage-check 거부(073)",
    "scenario_contract_invalid": "test-scenario.json v2 계약 위반 — profile/executor/status/schema 검증 실패",
    "resume_verification_failed": "human handoff resume token/run/evidence 검증 실패",
    "scenario_gate_record_invalid": "scenario-gate-record 입력·advisory·이력 계약 위반(167)",
    "advisory_response_invalid": "advisory 응답 ID 집합·중복·retain 사유 계약 위반(167)",
    "scenario_gate_not_passed": "scenario-gate-verify 이력 마지막 원소가 pass가 아니거나 묶음 hash 불일치(167)",
}

# ─────────────────────────────────────────────────────────────────────────────
# 증거 충실도 사다리 (069/F-005·M-3) — mock < real-http < real-usage.
# verification.md §1 "증거 충실도" 규범(F-001)의 게이트 구현.
# ─────────────────────────────────────────────────────────────────────────────

FIDELITY_ORDER: Dict[str, int] = {"mock": 0, "real-http": 1, "real-usage": 2}

# ─────────────────────────────────────────────────────────────────────────────
# (167/AC-2) `유형` 열 허용값 — Scenarios 표 헤더에 `유형`이 있으면 모든 행이
# 이 6값 중 하나여야 한다.
# ─────────────────────────────────────────────────────────────────────────────

SCENARIO_TYPE_VALUES = ("unit", "integration", "contract", "regression", "e2e", "check")

# (167/AC-6) 목표-커버 게이트 반복 상한 — guards.md 목표-커버 행과 동일한 값.
SCENARIO_GATE_RETRY_LIMIT = 3

_ADVISORY_KINDS = ("subsumed", "mergeable", "cheaper_layer", "misclassified")


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

    [MUST] (111/S-18) red_required(spec존): 명시값을 bool로 보존한다. 필드가 없는 기존
    입력은 true가 기본값이다. 기존 전 시나리오 RED 계약을 유지하면서 sdlc-v2가
    구현 전 실패 확인 대상으로 선택한 시나리오만 잠금 게이트에 포함할 수 있게 한다.

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
        # spec존 — 선택적 RED 대상. 기존 입력은 전부 RED 대상으로 호환한다.
        "red_required": bool(raw.get("red_required", True)),
        # spec존 — red_confirmed/red_evidence/red_at은 scenario-init에서 항상 초기값으로
        # 생성되며, red_confirmed는 scenario-red를 통해서만 true로 갱신될 수 있다.
        "red_confirmed": False,
        "red_evidence": None,
        "red_at": None,
        # spec존 — 증거 충실도 사다리 (069/F-005)
        "required_fidelity": required_fidelity,
        # spec존 — 검증 대상 표면 id (069/F-006, nullable)
        "surface_ref": raw.get("surface_ref"),
        "surface_kind": raw.get("surface_kind"),
        "profile": raw.get("profile"),
        "actors": raw.get("actors", []),
        "steps": raw.get("steps", []),
        "assertions": raw.get("assertions", []),
        "required_evidence": raw.get("required_evidence", []),
        "handoff": raw.get("handoff"),
        # result존
        "result": raw.get("result"),
        "operational_status": raw.get("operational_status"),
        "observed_executors": raw.get("observed_executors", []),
        "assertion_results": raw.get("assertion_results", []),
        "observed_evidence": raw.get("observed_evidence", []),
        "handoff_state": raw.get("handoff_state"),
        "run_id": raw.get("run_id"),
        "evidence": raw.get("evidence"),
        "marked_at": raw.get("marked_at"),
        # result존 — 실제 관찰된 충실도 (069/F-005, scenario-mark --fidelity로 기록)
        "fidelity": raw.get("fidelity", "mock"),
    }


def _complete_handoff_state(target: Dict[str, Any], state: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Merge scenario handoff defaults into runtime handoff_state and require all fields."""
    if state is not None and not isinstance(state, dict):
        return None
    merged: Dict[str, Any] = {}
    scenario_handoff = target.get("handoff")
    if isinstance(scenario_handoff, dict):
        merged.update(scenario_handoff)
    if state:
        merged.update(state)
    missing = [field for field in HANDOFF_REQUIRED_FIELDS if merged.get(field) in (None, "", [])]
    if missing:
        return None
    return merged


def _scenario_mark_mode(args: argparse.Namespace) -> Dict[str, Any]:
    result_present = getattr(args, "result", None) is not None
    verdict_present = getattr(args, "verdict_json", None) is not None
    resume_values = {
        "resume_run_id": getattr(args, "resume_run_id", None),
        "resume_token": getattr(args, "resume_token", None),
        "submission": getattr(args, "submission", None),
    }
    resume_present = any(value is not None for value in resume_values.values())
    resume_complete = all(value is not None for value in resume_values.values())
    if resume_present and not resume_complete:
        return {"ok": False, "error": "resume_verification_failed", "exit": 6}
    selected = sum(1 for value in (result_present, verdict_present, resume_present) if value)
    if selected != 1:
        return {"ok": False, "error": "scenario_contract_invalid", "exit": 17}
    if result_present:
        return {"ok": True, "mode": "result"}
    if verdict_present:
        return {"ok": True, "mode": "verdict"}
    return {"ok": True, "mode": "resume"}


def _ensure_scenario_contract(spec: Dict[str, Any], command: str, *, legacy_defaults: bool = True) -> None:
    if spec.get("schema_version") == E2E_CONTRACT_SCHEMA_VERSION:
        root_keys = ("schema_version", "task_id", "locked", "created_at", "locked_at", "scenarios")
        missing_root = [key for key in root_keys if key not in spec]
        if missing_root:
            _error("scenario_contract_invalid", command, 17, detail=f"missing required root keys {missing_root}")
        if not isinstance(spec.get("scenarios"), list):
            _error("scenario_contract_invalid", command, 17, detail="scenarios must be a list")
        scenario_keys = (
            "id",
            "acceptance_ref",
            "type",
            "expected",
            "red_required",
            "red_confirmed",
            "red_evidence",
            "red_at",
            "surface_ref",
            "surface_kind",
            "profile",
            "actors",
            "steps",
            "assertions",
            "required_evidence",
            "handoff",
            "result",
            "operational_status",
            "observed_executors",
            "assertion_results",
            "observed_evidence",
            "handoff_state",
            "evidence",
            "marked_at",
        )
        for scenario in spec.get("scenarios") or []:
            missing = [key for key in scenario_keys if key not in scenario]
            if missing:
                _error(
                    "scenario_contract_invalid",
                    command,
                    17,
                    detail=f"{scenario.get('id')}: missing required scenario keys {missing}",
                )
    contract = validate_scenario_contract(spec, legacy_defaults=legacy_defaults)
    if not contract["ok"]:
        _error("scenario_contract_invalid", command, 17, detail=str(contract.get("detail")))


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
        "schema_version": E2E_CONTRACT_SCHEMA_VERSION,
        "task_id": task_path.name,
        "locked": False,
        "created_at": now,
        "locked_at": None,
        "scenarios": scenarios,
    }
    _ensure_scenario_contract(spec, "scenario-init", legacy_defaults=False)
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
    """scenario-lock — RED 대상 시나리오가 확인된 뒤 spec을 동결한다."""
    task_path = pathlib.Path(args.task_path)
    spec = _load_spec(task_path)
    if spec is None:
        _error("scenario_not_initialized", "scenario-lock", 10)
        return
    _ensure_scenario_contract(spec, "scenario-lock", legacy_defaults=True)

    scenarios = spec.get("scenarios", [])
    unconfirmed = [
        s.get("id") for s in scenarios
        if s.get("red_required", True) and not s.get("red_confirmed")
    ]
    if unconfirmed:
        _error(
            "red_not_confirmed", "scenario-lock", 8,
            detail=f"red_required==true and red_confirmed==false: {unconfirmed}",
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
    _ensure_scenario_contract(spec, "scenario-mark", legacy_defaults=True)

    if not spec.get("locked"):
        _error("scenario_not_locked", "scenario-mark", 9)
        return

    scenario_id = args.id
    target = next((s for s in spec.get("scenarios", []) if s.get("id") == scenario_id), None)
    if target is None:
        _error("scenario_not_initialized", "scenario-mark", 10, detail=f"unknown scenario id: {scenario_id}")
        return

    now = _now_kst()
    mode_result = _scenario_mark_mode(args)
    if not mode_result["ok"]:
        _error(mode_result["error"], "scenario-mark", mode_result["exit"])
        return
    mode = mode_result["mode"]
    verdict_path_arg = getattr(args, "verdict_json", None)
    if mode == "verdict":
        try:
            with open(pathlib.Path(verdict_path_arg), encoding="utf-8") as f:
                verdict_input = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            _error("scenario_contract_invalid", "scenario-mark", 17, detail=str(e))
            return
        verdict = build_verdict(verdict_input)
        status = verdict["status"]
        if status == "pass":
            pass_gate = validate_pass_requirements(target, verdict_input)
            if not pass_gate["ok"]:
                _respond({
                    "ok": False,
                    "command": "scenario-mark",
                    "error": pass_gate["error"],
                    "status": pass_gate["status"],
                    "detail": pass_gate["detail"],
                }, status_to_exit(pass_gate["status"] or "fail"))
                return
            target["result"] = "pass"
            target["operational_status"] = None
            target["fidelity"] = verdict_input.get("fidelity", target.get("required_fidelity", "mock"))
        elif status == "awaiting_human":
            handoff_state = _complete_handoff_state(target, verdict_input.get("handoff_state"))
            if handoff_state is None or not verdict_input.get("run_id"):
                _error("scenario_contract_invalid", "scenario-mark", 17, detail="complete handoff_state and run_id required")
                return
            target["result"] = None
            target["operational_status"] = "awaiting_human"
            target["handoff_state"] = handoff_state
            target["run_id"] = verdict_input.get("run_id")
        else:
            if status in FINAL_STATUSES:
                target["result"] = status
            target["operational_status"] = None
        target["observed_executors"] = verdict_input.get("observed_executors", [])
        target["assertion_results"] = verdict_input.get("assertion_results", [])
        target["observed_evidence"] = verdict_input.get("observed_evidence", [])
        target["evidence"] = verdict_input.get("evidence")
        target["marked_at"] = now
        _save_spec(task_path, spec)
        _respond({
            "ok": status == "pass" or status == "awaiting_human",
            "command": "scenario-mark",
            "scenario_id": scenario_id,
            "status": status,
            "error": status_to_error(status),
            "final_statuses": list(FINAL_STATUSES),
            "operational_statuses": list(OPERATIONAL_STATUSES),
        }, status_to_exit(status))
        return

    resume_token = getattr(args, "resume_token", None)
    if mode == "resume":
        try:
            with open(pathlib.Path(args.submission), encoding="utf-8") as f:
                submission = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            _error("resume_verification_failed", "scenario-mark", 6, detail=str(e))
            return
        expected_run = target.get("run_id")
        expected_handoff = target.get("handoff_state") or {}
        expected_token = expected_handoff.get("resume_token")
        if (
            target.get("operational_status") != "awaiting_human"
            or args.resume_run_id != expected_run
            or resume_token != expected_token
            or submission.get("run_id") != expected_run
            or submission.get("resume_token") != expected_token
        ):
            _error("resume_verification_failed", "scenario-mark", 6)
            return
        result_payload = dict(submission)
        result_payload["status"] = "pass"
        result_payload["profile"] = target.get("profile")
        pass_gate = validate_pass_requirements(target, result_payload)
        if not pass_gate["ok"]:
            _respond({
                "ok": False,
                "command": "scenario-mark",
                "error": pass_gate["error"],
                "status": pass_gate["status"],
                "detail": pass_gate["detail"],
            }, status_to_exit(pass_gate["status"] or "fail"))
            return
        target["result"] = "pass"
        target["operational_status"] = None
        target["observed_executors"] = submission.get("observed_executors", [])
        target["assertion_results"] = submission.get("assertion_results", [])
        target["observed_evidence"] = submission.get("observed_evidence", [])
        target["fidelity"] = submission.get("fidelity", target.get("required_fidelity", "mock"))
        target["marked_at"] = now
        _save_spec(task_path, spec)
        _respond({
            "ok": True,
            "command": "scenario-mark",
            "scenario_id": scenario_id,
            "status": "pass",
        }, 0)
        return

    result_arg = getattr(args, "result", None)
    if (
        result_arg == "pass"
        and (target.get("profile") is not None or target.get("required_fidelity") == "real-usage")
    ):
        _respond({
            "ok": False,
            "command": "scenario-mark",
            "error": "assertion_required",
            "status": "fail",
            "detail": "pass/real-usage requires --verdict-json structured assertions and evidence",
        }, 6)
        return

    target["result"] = result_arg
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
        "result": result_arg,
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
    """scenario-status — spec/result 요약 (전체·필수 RED 확인 수와 통과율)."""
    task_path = pathlib.Path(args.task_path)
    spec = _load_spec(task_path)
    if spec is None:
        _error("scenario_not_initialized", "scenario-status", 10)
        return

    _ensure_scenario_contract(spec, "scenario-status", legacy_defaults=True)

    scenarios = spec.get("scenarios", [])
    total = len(scenarios)
    red_confirmed = sum(1 for s in scenarios if s.get("red_confirmed") is True)
    red_required = sum(1 for s in scenarios if s.get("red_required", True) is True)
    red_confirmed_required = sum(
        1 for s in scenarios
        if s.get("red_required", True) is True and s.get("red_confirmed") is True
    )
    passed = sum(1 for s in scenarios if s.get("result") == "pass")
    failed = sum(1 for s in scenarios if s.get("result") == "fail")
    blocked = sum(1 for s in scenarios if s.get("result") == "blocked")
    status_counts = {
        "pass": passed,
        "fail": failed,
        "executor_unavailable": sum(1 for s in scenarios if s.get("result") == "executor_unavailable"),
        "infra_error": sum(1 for s in scenarios if s.get("result") == "infra_error"),
        "blocked": blocked,
        "awaiting_human": sum(1 for s in scenarios if s.get("operational_status") == "awaiting_human"),
    }

    _respond({
        "ok": True,
        "command": "scenario-status",
        "locked": bool(spec.get("locked", False)),
        "total": total,
        "red_confirmed": red_confirmed,
        "red_required": red_required,
        "red_confirmed_required": red_confirmed_required,
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "awaiting_human": status_counts["awaiting_human"],
        "status_counts": status_counts,
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
    _ensure_scenario_contract(spec, "scenario-fidelity-check", legacy_defaults=True)

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

    spec = _load_spec(task_path)
    if spec is None:
        _error("scenario_not_initialized", "scenario-conformance", 10)
        return
    _ensure_scenario_contract(spec, "scenario-conformance", legacy_defaults=True)

    if not surfaces_path.exists():
        _respond({
            "ok": True,
            "command": "scenario-conformance",
            "applicable": False,
        }, 0)
        return

    with open(surfaces_path, encoding="utf-8") as f:
        surfaces_doc = json.load(f)

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
_TOKEN_RE = re.compile(r"\b(AC|C|H|F|S|W)-\d+\b")
_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*", re.DOTALL)


def _read_text(path: pathlib.Path, command: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        _error("coverage_input_invalid", command, 17, detail=f"파일 읽기 실패: {path}: {e}")
        raise


def _frontmatter_template(text: str) -> Optional[str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None
    for line in match.group(1).splitlines():
        if line.strip().startswith("template:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return None


def _section_body(text: str, heading: str) -> str:
    matches = list(_SECTION_RE.finditer(text))
    for index, match in enumerate(matches):
        current = match.group(1).strip()
        if current == heading:
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            return text[start:end]
    return ""


def _has_section(text: str, heading: str) -> bool:
    return any(match.group(1).strip() == heading for match in _SECTION_RE.finditer(text))


def _unique_in_order(values: Sequence[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _ids_from_section(text: str, heading: str, prefixes: Sequence[str]) -> List[str]:
    body = _section_body(text, heading)
    prefix_alt = "|".join(re.escape(prefix) for prefix in prefixes)
    pattern = re.compile(rf"(?m)^\s*(?:[-*]\s+)?(({prefix_alt})-\d+)\b")
    return _unique_in_order(match.group(1) for match in pattern.finditer(body))


def _tokens_by_prefix(text: str, prefixes: Sequence[str]) -> Dict[str, List[str]]:
    result = {prefix: [] for prefix in prefixes}
    for match in _TOKEN_RE.finditer(text):
        token = match.group(0)
        prefix = match.group(1)
        if prefix in result and token not in result[prefix]:
            result[prefix].append(token)
    return result


def _split_markdown_table_row(line: str) -> List[str]:
    """Markdown 표 한 행을 escape되지 않은 `|`에서만 분리한다.

    Markdown의 선두·후미 테두리 파이프는 선택 사항이므로 있으면 제거하되,
    셀 안의 ``\\|``는 텍스트로 보존한다.
    """
    content = line.strip()
    if content.startswith("|"):
        content = content[1:]

    trailing_backslashes = 0
    for char in reversed(content[:-1]) if content.endswith("|") else ():
        if char != "\\":
            break
        trailing_backslashes += 1
    if content.endswith("|") and trailing_backslashes % 2 == 0:
        content = content[:-1]

    cells: List[str] = []
    current: List[str] = []
    escaped = False
    for char in content:
        if escaped:
            if char == "|":
                current.append("|")
            else:
                current.extend(("\\", char))
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if escaped:
        current.append("\\")
    cells.append("".join(current).strip())
    return cells


def _parse_markdown_table_rows(section: str) -> List[Dict[str, str]]:
    rows: List[List[str]] = []
    row_lines: List[tuple[int, str]] = []
    header_found = False
    for line_number, raw_line in enumerate(section.splitlines(), start=1):
        line = raw_line.strip()
        if "|" not in line:
            continue
        cells = _split_markdown_table_row(line)
        if not header_found:
            if cells and cells[0].strip().lower() == "id":
                header_found = True
                rows.append(cells)
                row_lines.append((line_number, line))
            continue
        if cells and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        if not cells or not re.fullmatch(r"S-\d+", cells[0].strip()):
            continue
        rows.append(cells)
        row_lines.append((line_number, line))

    if not rows:
        return []

    header = rows[0]
    parsed: List[Dict[str, str]] = []
    for index, cells in enumerate(rows[1:], start=1):
        if len(cells) != len(header):
            line_number, line = row_lines[index]
            raise ValueError(
                f"Scenarios 표 {line_number}행 열 수 불일치: "
                f"expected={len(header)}, actual={len(cells)}, row={line}"
            )
        parsed.append({header[i]: cells[i] for i in range(len(header))})
    return parsed


def _goal_from_task(task_text: str) -> str:
    proposed = _section_body(task_text, "Proposed outcome").strip()
    return " ".join(line.strip() for line in proposed.splitlines() if line.strip())


def _build_sdlc_v2_coverage_payload(task_folder: pathlib.Path) -> Dict[str, Any]:
    command = "scenario-coverage-build"
    task_text = _read_text(task_folder / "TASK.md", command)
    plan_text = _read_text(task_folder / "PLAN.md", command)
    scenario_text = _read_text(task_folder / "TEST-SCENARIO.md", command)

    for label, text in (("TASK.md", task_text), ("PLAN.md", plan_text), ("TEST-SCENARIO.md", scenario_text)):
        if _frontmatter_template(text) != "sdlc-v2":
            _error(
                "coverage_input_invalid", command, 17,
                detail=f"{label} 첫 YAML frontmatter template 값이 sdlc-v2가 아니다",
            )

    acceptance_ids = _ids_from_section(task_text, "Acceptance criteria", ("AC",))
    constraint_ids = _ids_from_section(task_text, "Constraints", ("C",))
    if not acceptance_ids:
        _error("coverage_input_invalid", command, 17, detail="Acceptance criteria AC 추출 실패")
    if not constraint_ids:
        _error("coverage_input_invalid", command, 17, detail="Constraints C 추출 실패")

    if not _has_section(plan_text, "Risks"):
        _error("coverage_input_invalid", command, 17, detail="PLAN Risks 절 누락")
    risk_section = _section_body(plan_text, "Risks")
    hypothesis_ids = _tokens_by_prefix(risk_section, ("H",))["H"]

    legacy_feature_ids = _ids_from_section(plan_text, "기능 목록", ("F",))
    scenario_section = _section_body(scenario_text, "Scenarios")
    try:
        rows = _parse_markdown_table_rows(scenario_section)
    except ValueError as exc:
        _error("coverage_input_invalid", command, 17, detail=str(exc))
        return {}
    scenarios: List[Dict[str, Any]] = []
    known_requirements = set(acceptance_ids + constraint_ids)
    known_hypotheses = set(hypothesis_ids)
    known_features = set(legacy_feature_ids)
    unknown_refs: List[str] = []
    seen_scenario_ids: Set[str] = set()
    duplicate_scenario_ids: List[str] = []

    # (167/AC-2, AC-3) `유형` 열 전환 규칙: 헤더에 있으면 6값 강제 검사·check+RED
    # 모순 거부·정확 중복(6셀) 거부. 헤더에 없으면 기존 변환을 유지한다(type=None).
    type_header_present = bool(rows) and "유형" in rows[0]
    invalid_type_ids: List[str] = []
    check_red_contradiction_ids: List[str] = []
    exact_duplicate_groups: Dict[tuple, List[str]] = {}

    def _norm_cell(value: Optional[str]) -> str:
        return re.sub(r"\s+", " ", (value or "").strip())

    for row in rows:
        scenario_id = (row.get("ID") or row.get("Id") or row.get("id") or "").strip()
        if not re.fullmatch(r"S-\d+", scenario_id):
            continue
        if scenario_id in seen_scenario_ids:
            duplicate_scenario_ids.append(scenario_id)
        else:
            seen_scenario_ids.add(scenario_id)
        target_text = row.get("검증 대상") or row.get("Target") or row.get("대상") or ""
        tokens = _tokens_by_prefix(target_text, ("AC", "C", "H", "F", "W"))
        refs = tokens["AC"] + tokens["C"] + tokens["H"] + tokens["F"] + tokens["W"]
        for ref in refs:
            if ref.startswith(("AC-", "C-")) and ref not in known_requirements:
                unknown_refs.append(ref)
            elif ref.startswith("H-") and ref not in known_hypotheses:
                unknown_refs.append(ref)
            elif ref.startswith("F-") and ref not in known_features:
                unknown_refs.append(ref)
            elif ref.startswith("W-"):
                unknown_refs.append(ref)

        timing_text = row.get("시점") or ""
        red_required = "구현 전 RED" in timing_text
        type_value: Optional[str] = None
        if type_header_present:
            raw_type = (row.get("유형") or "").strip()
            type_value = raw_type
            if raw_type not in SCENARIO_TYPE_VALUES:
                invalid_type_ids.append(scenario_id)
            elif raw_type == "check" and red_required:
                check_red_contradiction_ids.append(scenario_id)
            six_key = (
                _norm_cell(row.get("유형")),
                _norm_cell(row.get("조건")),
                _norm_cell(row.get("행동")),
                _norm_cell(row.get("기대 결과")),
                _norm_cell(row.get("방법·환경")),
                _norm_cell(row.get("시점")),
            )
            exact_duplicate_groups.setdefault(six_key, []).append(scenario_id)

        scenarios.append({
            "id": scenario_id,
            "type": type_value,
            "red_required": red_required,
            "covers_requirements": _unique_in_order(tokens["AC"] + tokens["C"]),
            "covers_features": _unique_in_order(tokens["F"]),
            "covers_hypotheses": _unique_in_order(tokens["H"]),
            "is_goal_scenario": False,
            "is_adoption_scenario": False,
            "is_boundary_scenario": False,
        })

    if invalid_type_ids:
        _error(
            "coverage_input_invalid", command, 17,
            detail=f"invalid 유형 값(허용: {list(SCENARIO_TYPE_VALUES)}): {_unique_in_order(invalid_type_ids)}",
        )
    if check_red_contradiction_ids:
        _error(
            "coverage_input_invalid", command, 17,
            detail=f"check 유형과 구현 전 RED 모순: {_unique_in_order(check_red_contradiction_ids)}",
        )
    duplicate_content_ids = [
        ids for ids in exact_duplicate_groups.values() if len(ids) > 1
    ]
    if duplicate_content_ids:
        first_group = duplicate_content_ids[0]
        _error(
            "coverage_input_invalid", command, 17,
            detail=f"duplicate scenario content: {first_group}",
        )

    if not scenarios:
        _error("coverage_input_invalid", command, 17, detail="TEST-SCENARIO Scenarios S 0건")
    if duplicate_scenario_ids:
        _error(
            "coverage_input_invalid", command, 17,
            detail=f"duplicate scenario id: {_unique_in_order(duplicate_scenario_ids)}",
        )
    if unknown_refs:
        _error(
            "coverage_input_invalid", command, 17,
            detail=f"unknown reference: {_unique_in_order(unknown_refs)}",
        )

    return {
        "goal": _goal_from_task(task_text),
        "requirements": acceptance_ids + constraint_ids,
        "features": legacy_feature_ids,
        "hypotheses": hypothesis_ids,
        "scenarios": scenarios,
    }


def cmd_scenario_coverage_build(args: argparse.Namespace) -> None:
    """scenario-coverage-build — sdlc-v2 문서를 coverage-check 입력 JSON으로 결정론 변환한다.

    2026-09-09 14:18 KST task 111: 신규 TEST-SCENARIO는 Setup/Scenarios만 소유하고,
    단계·승인은 state.json, 결과·증거는 test-scenario.json이 소유한다. 이 builder는
    문서의 필수 AC/C/S와 optional H 추적 토큰만 transient coverage payload로 변환한다.
    """
    command = "scenario-coverage-build"
    template = getattr(args, "template", None) or "sdlc-v2"
    if template != "sdlc-v2":
        _error("coverage_input_invalid", command, 17, detail=f"지원하지 않는 template: {template}")
        return

    task_folder = pathlib.Path(args.task_folder)
    output_path = task_folder / ".scenario-coverage-input.json"
    # (167/목표-커버 기록 명령) 이번 회차 build가 실패하면 이전 회차의 입력이 재판정에
    # 재사용되지 않도록, build 시도 전에 기존 파일을 먼저 지운다. 성공 시 아래에서 새로
    # 다시 쓴다.
    if output_path.exists():
        try:
            output_path.unlink()
        except OSError:
            pass
    payload = _build_sdlc_v2_coverage_payload(task_folder)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError as e:
        _error("coverage_input_invalid", command, 17, detail=f"coverage input 저장 실패: {e}")
        return

    _respond({
        "ok": True,
        "command": command,
        "template": template,
        "coverage_input": str(output_path),
        "counts": {
            "requirements": len(payload["requirements"]),
            "features": len(payload["features"]),
            "hypotheses": len(payload["hypotheses"]),
            "scenarios": len(payload["scenarios"]),
        },
    }, 0)


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
# (167) 목표-커버 게이트 기록·검증 — scenario-gate-record / scenario-gate-verify
# ─────────────────────────────────────────────────────────────────────────────

_GATE_HISTORY_NAME = ".scenario-coverage-input.json"


def _gate_history_path(task_folder: pathlib.Path) -> pathlib.Path:
    return task_folder / ".scenario-gate-history.json"


def _atomic_write_json(path: pathlib.Path, data: Any) -> None:
    """tmp→os.replace 원자 쓰기 (167/목표-커버 기록 명령)."""
    tmp_path = path.with_name(path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def _read_gate_history(history_path: pathlib.Path):
    """반환: [] (파일 부재), list (정상), None (배열 아님/파손 — 호출측이 오류 처리)."""
    if not history_path.exists():
        return []
    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    return data


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compute_bundle_hash(task_folder: pathlib.Path, producer_artifact: str):
    """TASK.md·PLAN.md(존재하는 파일만) + producer 파일 순서로 sha256을 이어 묶음 hash를
    계산한다(167/목표-커버 기록·검증 명령 공통). producer 파일이 없으면 (None, files)를
    반환한다."""
    parts: List[str] = []
    files: List[str] = []
    for name in ("TASK.md", "PLAN.md"):
        candidate = task_folder / name
        if candidate.exists():
            parts.append(f"{name}\n{_sha256_file(candidate)}")
            files.append(name)
    producer_path = pathlib.Path(producer_artifact)
    if not producer_path.is_absolute():
        producer_path = task_folder / producer_artifact
    if not producer_path.exists():
        return None, files
    parts.append(f"{producer_artifact}\n{_sha256_file(producer_path)}")
    files.append(producer_artifact)
    combined = "\n".join(parts)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest(), files


def _judge_coverage_input(task_folder: pathlib.Path, *, evaluator_provided: bool) -> Dict[str, Any]:
    """`.scenario-coverage-input.json`을 scenario-coverage-check와 같은 로직으로
    재판정한다. 부재·파손·필수 키 누락은 evaluator_result가 주어졌으면(호출측이 이미
    커버리지를 확인했다고 신뢰) missing 없음으로 간주하고, 주어지지 않았으면 판정
    불가(ok:False)로 반환한다(167/목표-커버 기록 명령 ②)."""
    empty_missing = {"requirements": [], "features": [], "hypotheses": []}
    path = task_folder / ".scenario-coverage-input.json"
    if not path.exists():
        return {"ok": True, "missing": empty_missing} if evaluator_provided else {"ok": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"ok": True, "missing": empty_missing} if evaluator_provided else {"ok": False}
    if not isinstance(payload, dict) or any(k not in payload for k in _COVERAGE_REQUIRED_KEYS):
        return {"ok": True, "missing": empty_missing} if evaluator_provided else {"ok": False}

    requirements = payload.get("requirements") or []
    features = payload.get("features") or []
    hypotheses = payload.get("hypotheses") or []
    scenarios = payload.get("scenarios") or []
    covered_requirements: Set[str] = set()
    covered_features: Set[str] = set()
    covered_hypotheses: Set[str] = set()
    for s in scenarios:
        covered_requirements.update(s.get("covers_requirements") or [])
        covered_features.update(s.get("covers_features") or [])
        covered_hypotheses.update(s.get("covers_hypotheses") or [])
    missing = {
        "requirements": [r for r in requirements if r not in covered_requirements],
        "features": [f for f in features if f not in covered_features],
        "hypotheses": [h for h in hypotheses if h not in covered_hypotheses],
    }
    return {"ok": True, "missing": missing}


def _missing_count(missing: Optional[Dict[str, Any]]) -> int:
    if not isinstance(missing, dict):
        return 0
    return sum(len(missing.get(k) or []) for k in ("requirements", "features", "hypotheses"))


def _score_sum(scores: Optional[Dict[str, Any]]) -> float:
    if not isinstance(scores, dict):
        return 0.0
    total = 0.0
    for key in ("goal", "adoption", "boundary"):
        value = scores.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += value
    return total


def _validate_advisories(advisories: Any) -> Optional[str]:
    if not isinstance(advisories, list):
        return "advisories must be a list"
    seen_ids: List[str] = []
    for advisory in advisories:
        if not isinstance(advisory, dict):
            return "advisory item must be an object"
        advisory_id = advisory.get("id")
        if not advisory_id or not isinstance(advisory_id, str):
            return "advisory.id is required"
        if advisory.get("kind") not in _ADVISORY_KINDS:
            return f"advisory.kind invalid: {advisory.get('kind')!r}"
        targets = advisory.get("targets")
        if not isinstance(targets, list) or not targets:
            return "advisory.targets must be a non-empty list"
        if not advisory.get("basis"):
            return "advisory.basis is required"
        if not advisory.get("recommendation"):
            return "advisory.recommendation is required"
        seen_ids.append(advisory_id)
    if len(seen_ids) != len(set(seen_ids)):
        return "advisory.id duplicated"
    return None


def _validate_advisory_responses(advisories: List[Dict[str, Any]], responses: Any):
    """반환: (에러 메시지 또는 None, 정규화된 responses 리스트)."""
    advisory_ids = {a.get("id") for a in advisories}
    if not advisory_ids:
        if responses in (None, []):
            return None, []
        return "advisories가 없으면 advisory_responses는 생략하거나 빈 배열이어야 한다", []
    if responses is None:
        return "advisories가 있는 pass 회차는 advisory_responses가 필요하다", []
    if not isinstance(responses, list):
        return "advisory_responses must be a list", []
    seen_ids: Set[str] = set()
    for response in responses:
        if not isinstance(response, dict):
            return "advisory response item must be an object", []
        response_id = response.get("id")
        if response_id in seen_ids:
            return f"duplicate advisory response id: {response_id}", []
        seen_ids.add(response_id)
        kind = response.get("response")
        if kind not in ("apply", "retain"):
            return f"invalid advisory response: {kind!r}", []
        if kind == "retain" and not str(response.get("reason") or "").strip():
            return "retain response requires a non-blank reason", []
    if seen_ids != advisory_ids:
        return (
            f"advisory response id set mismatch: expected {sorted(advisory_ids)}, got {sorted(seen_ids)}",
            [],
        )
    return None, responses


def cmd_scenario_gate_record(args: argparse.Namespace) -> None:
    """scenario-gate-record — 목표-커버 게이트 이력에 회차별 판정 1건을 추가한다
    (167/목표-커버 기록 명령). --input-error/--evidence-error는 서로 배타적인 별도 모드다."""
    command = "scenario-gate-record"
    task_folder = pathlib.Path(args.task_folder)
    iteration = args.iteration
    evidence_error = getattr(args, "evidence_error", None)
    input_error = getattr(args, "input_error", None)
    evaluator_result_path = getattr(args, "evaluator_result", None)
    advisory_responses_path = getattr(args, "advisory_responses", None)
    producer_artifact = getattr(args, "producer_artifact", None) or "TEST-SCENARIO.md"

    history_path = _gate_history_path(task_folder)
    history = _read_gate_history(history_path)
    if history is None:
        _error("scenario_gate_record_invalid", command, 18, detail="이력 파일이 배열이 아니거나 파손되었다")
        return

    if evidence_error is not None:
        if input_error is not None or evaluator_result_path or advisory_responses_path:
            _error(
                "scenario_gate_record_invalid", command, 18,
                detail="--evidence-error는 --input-error·--evaluator-result·--advisory-responses와 함께 쓸 수 없다",
            )
            return
        if not history:
            _error("scenario_gate_record_invalid", command, 18, detail="이력이 없어 --evidence-error를 적용할 수 없다")
            return
        last = history[-1]
        if last.get("iteration") != iteration:
            _error(
                "scenario_gate_record_invalid", command, 18,
                detail=f"회차 불일치: 이력 마지막={last.get('iteration')}, 지정={iteration}",
            )
            return
        last["evidence_error"] = evidence_error
        last["verdict"] = "escalate"
        last["reason"] = "input_error"
        _atomic_write_json(history_path, history)
        _respond({
            "ok": True, "command": command, "verdict": "escalate", "reason": "input_error",
            "iteration": iteration,
        }, 0)
        return

    if input_error is not None:
        element = {
            "iteration": iteration,
            "missing": None,
            "scores": None,
            "gaps": [],
            "verdict": "escalate",
            "reason": "input_error",
            "advisories": [],
            "advisory_responses": [],
            "refinement": bool(history and history[-1].get("reason") == "advisory_apply"),
            "counted": True,
            "bundle_hash": None,
            "files": [],
            "at": _now_kst(),
            "input_error": input_error,
        }
        history.append(element)
        _atomic_write_json(history_path, history)
        _respond({
            "ok": True, "command": command, "verdict": "escalate", "reason": "input_error",
            "iteration": iteration,
        }, 0)
        return

    # ① 이력 마지막 iteration+1 == N
    expected_iteration = (history[-1].get("iteration") + 1) if history else 1
    if iteration != expected_iteration:
        _error(
            "scenario_gate_record_invalid", command, 18,
            detail=f"iteration은 {expected_iteration}이어야 한다(지정={iteration})",
        )
        return

    # ② coverage-input 재판정 (evaluator_result가 주어지면 부재·파손 시에도 진행한다)
    coverage_judgement = _judge_coverage_input(task_folder, evaluator_provided=bool(evaluator_result_path))
    if not coverage_judgement.get("ok"):
        element = {
            "iteration": iteration,
            "missing": None,
            "scores": None,
            "gaps": [],
            "verdict": "escalate",
            "reason": "input_error",
            "advisories": [],
            "advisory_responses": [],
            "refinement": bool(history and history[-1].get("reason") == "advisory_apply"),
            "counted": True,
            "bundle_hash": None,
            "files": [],
            "at": _now_kst(),
        }
        history.append(element)
        _atomic_write_json(history_path, history)
        _respond({
            "ok": True, "command": command, "verdict": "escalate", "reason": "input_error",
            "iteration": iteration,
        }, 0)
        return
    missing = coverage_judgement["missing"]
    missing_present = bool(missing["requirements"] or missing["features"] or missing["hypotheses"])

    # ③④ evaluator 결과 로드·필수 여부·3축 재계산 대조
    evaluator_result: Optional[Dict[str, Any]] = None
    if evaluator_result_path:
        try:
            evaluator_result = json.loads(pathlib.Path(evaluator_result_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            _error("scenario_gate_record_invalid", command, 18, detail=f"--evaluator-result 로드 실패: {e}")
            return
        if not isinstance(evaluator_result, dict):
            _error("scenario_gate_record_invalid", command, 18, detail="--evaluator-result는 JSON object여야 한다")
            return

    if not missing_present and evaluator_result is None:
        _error("scenario_gate_record_invalid", command, 18, detail="누락이 없으면 --evaluator-result가 필요하다")
        return

    scores: Optional[Dict[str, Any]] = None
    gaps: List[Any] = []
    evaluator_pass = False
    if evaluator_result is not None:
        scores = evaluator_result.get("scores")
        gaps = evaluator_result.get("gaps") or []
        if not isinstance(scores, dict) or any(k not in scores for k in ("goal", "adoption", "boundary")):
            _error(
                "scenario_gate_record_invalid", command, 18,
                detail="evaluator_result.scores는 goal/adoption/boundary 3키가 필요하다",
            )
            return
        try:
            values = [float(scores[k]) for k in ("goal", "adoption", "boundary")]
        except (TypeError, ValueError):
            _error("scenario_gate_record_invalid", command, 18, detail="evaluator_result.scores 값은 숫자여야 한다")
            return
        average = sum(values) / len(values)
        computed_pass = all(v >= 1 for v in values) and average >= 1.5
        verdict_field = evaluator_result.get("verdict")
        if verdict_field == "pass":
            if not computed_pass:
                _error(
                    "scenario_gate_record_invalid", command, 18,
                    detail=(
                        f"evaluator verdict=pass인데 점수 재계산 결과 불일치"
                        f"(scores={scores}, average={round(average, 3)})"
                    ),
                )
                return
            evaluator_pass = True
        else:
            evaluator_pass = False

    is_refinement = bool(history and history[-1].get("reason") == "advisory_apply")

    raw_advisories = (evaluator_result.get("advisories") if evaluator_result else None) or []
    advisory_responses_input: Optional[Any] = None
    if advisory_responses_path:
        try:
            advisory_responses_input = json.loads(pathlib.Path(advisory_responses_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            _error("advisory_response_invalid", command, 19, detail=f"--advisory-responses 로드 실패: {e}")
            return

    if is_refinement:
        # refinement 회차의 advisories는 응답 없이 무시하고 이력에는 빈 배열로 남긴다.
        advisories_to_record: List[Dict[str, Any]] = []
        advisory_responses_to_record: List[Dict[str, Any]] = []
    else:
        advisory_error = _validate_advisories(raw_advisories)
        if advisory_error:
            _error("scenario_gate_record_invalid", command, 18, detail=advisory_error)
            return
        response_required = bool(raw_advisories) and evaluator_pass
        if response_required:
            if advisory_responses_input is None:
                _error(
                    "advisory_response_invalid", command, 19,
                    detail="advisories가 있는 pass 회차는 --advisory-responses가 필요하다",
                )
                return
            response_error, validated_responses = _validate_advisory_responses(raw_advisories, advisory_responses_input)
            if response_error:
                _error("advisory_response_invalid", command, 19, detail=response_error)
                return
            advisory_responses_to_record = validated_responses
        else:
            if advisory_responses_input not in (None, []):
                _error(
                    "advisory_response_invalid", command, 19,
                    detail="advisories가 없으면 --advisory-responses는 생략하거나 빈 배열이어야 한다",
                )
                return
            advisory_responses_to_record = []
        advisories_to_record = raw_advisories

    # ⑥ 묶음 hash
    bundle_hash, files = _compute_bundle_hash(task_folder, producer_artifact)
    if bundle_hash is None:
        _error("scenario_gate_record_invalid", command, 18, detail=f"producer artifact 부재: {producer_artifact}")
        return

    apply_count = sum(1 for r in advisory_responses_to_record if r.get("response") == "apply")
    now = _now_kst()
    next_refinement = False

    if is_refinement:
        if not missing_present and evaluator_pass:
            verdict, reason, counted = "pass", "converged", False
        else:
            verdict, reason, counted = "escalate", "advisory_refinement_failed", False
    elif not missing_present and evaluator_pass and apply_count >= 1:
        verdict, reason, counted = "rewrite", "advisory_apply", False
        next_refinement = True
    elif not missing_present and evaluator_pass:
        verdict, reason, counted = "pass", "converged", True
    else:
        counted = True
        # (167/STATE.md 결정 로그) 구형 이력 원소(`counted` 키 없음)는 counted:true로
        # 간주한다 — 신규 도구가 생성하지 않은 이관 이력과의 호환.
        prior_counted = [e for e in history if e.get("counted", True)]
        if len(prior_counted) + 1 >= SCENARIO_GATE_RETRY_LIMIT:
            verdict, reason = "escalate", "retry_limit"
        elif prior_counted and (
            _missing_count(missing) >= _missing_count(prior_counted[-1].get("missing"))
            and _score_sum(scores) <= _score_sum(prior_counted[-1].get("scores"))
        ):
            verdict, reason = "escalate", "no_progress"
        else:
            verdict, reason = "rewrite", "recoverable"

    element = {
        "iteration": iteration,
        "missing": missing,
        "scores": scores,
        "gaps": gaps,
        "verdict": verdict,
        "reason": reason,
        "advisories": advisories_to_record,
        "advisory_responses": advisory_responses_to_record,
        "refinement": is_refinement,
        "counted": counted,
        "bundle_hash": bundle_hash,
        "files": files,
        "at": now,
    }
    history.append(element)
    _atomic_write_json(history_path, history)
    _respond({
        "ok": True,
        "command": command,
        "verdict": verdict,
        "reason": reason,
        "iteration": iteration,
        "next_refinement": next_refinement,
    }, 0)


def cmd_scenario_gate_verify(args: argparse.Namespace) -> None:
    """scenario-gate-verify — 이력 마지막 원소가 pass이고 묶음 hash가 현재와 같을 때만
    exit 0이다(167/목표-커버 검증 명령)."""
    command = "scenario-gate-verify"
    task_folder = pathlib.Path(args.task_folder)
    producer_artifact = getattr(args, "producer_artifact", None) or "TEST-SCENARIO.md"
    history_path = _gate_history_path(task_folder)

    if not history_path.exists():
        _error("scenario_gate_not_passed", command, 20, detail={"reason": "history_missing"})
        return
    try:
        history = json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        _error("scenario_gate_not_passed", command, 20, detail={"reason": "history_invalid"})
        return
    if not isinstance(history, list) or not history:
        _error("scenario_gate_not_passed", command, 20, detail={"reason": "history_invalid"})
        return
    last = history[-1]
    if not isinstance(last, dict) or "bundle_hash" not in last:
        _error("scenario_gate_not_passed", command, 20, detail={"reason": "history_invalid"})
        return
    if last.get("verdict") != "pass":
        _error("scenario_gate_not_passed", command, 20, detail={"reason": "not_passed"})
        return
    bundle_hash, _files = _compute_bundle_hash(task_folder, producer_artifact)
    if bundle_hash is None or bundle_hash != last.get("bundle_hash"):
        _error("scenario_gate_not_passed", command, 20, detail={"reason": "bundle_changed"})
        return

    _respond({
        "ok": True,
        "command": command,
        "verdict": "pass",
        "iteration": last.get("iteration"),
    }, 0)


# ─────────────────────────────────────────────────────────────────────────────
# argparse 서브파서 등록 + dispatch 테이블
# ─────────────────────────────────────────────────────────────────────────────

def add_scenario_subparsers(subparsers: "argparse._SubParsersAction") -> None:
    """test_tool.py `_build_parser`의 top-level subparsers 객체에
    scenario-init/scenario-lock/scenario-mark/scenario-status/scenario-red/
    scenario-fidelity-check/scenario-conformance/scenario-coverage-check/
    scenario-coverage-build 9종을 추가한다."""

    p_init = subparsers.add_parser("scenario-init", help="test-scenario.json 생성 (spec존, locked=false)")
    p_init.add_argument("--task-path", required=True, metavar="PATH", help="태스크 폴더 경로")
    p_init.add_argument("--scenarios", metavar="JSON", help="시나리오 배열 JSON (선택, 기본 [])")

    p_lock = subparsers.add_parser("scenario-lock", help="RED 대상 시나리오 확인 후 동결(locked=true)")
    p_lock.add_argument("--task-path", required=True, metavar="PATH", help="태스크 폴더 경로")

    p_mark = subparsers.add_parser("scenario-mark", help="locked 후 result존 기록")
    p_mark.add_argument("--task-path", required=True, metavar="PATH", help="태스크 폴더 경로")
    p_mark.add_argument("--id", required=True, metavar="S", help="시나리오 id")
    p_mark.add_argument("--result", choices=["pass", "fail", "blocked"], help="판정 결과")
    p_mark.add_argument("--evidence", metavar="E", help="증거 문자열 (선택)")
    p_mark.add_argument(
        "--fidelity", choices=["mock", "real-http", "real-usage"],
        help="실제 관찰된 증거 충실도 (선택, 미지정 시 mock — 069/M-5)",
    )
    p_mark.add_argument("--verdict-json", metavar="PATH", help="구조화 E2E verdict JSON 경로")
    p_mark.add_argument("--resume-run-id", metavar="RUN", help="awaiting_human 재개 run id")
    p_mark.add_argument("--resume-token", metavar="TOKEN", help="awaiting_human 재개 token")
    p_mark.add_argument("--submission", metavar="PATH", help="human submission JSON 경로")

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

    p_coverage_build = subparsers.add_parser(
        "scenario-coverage-build",
        help="sdlc-v2 TASK/PLAN/TEST-SCENARIO를 .scenario-coverage-input.json으로 결정론 변환(111/W-5)",
    )
    p_coverage_build.add_argument(
        "--task-folder", required=True, metavar="PATH",
        help="TASK.md/PLAN.md/TEST-SCENARIO.md가 있는 태스크 폴더",
    )
    p_coverage_build.add_argument(
        "--template", default="sdlc-v2", choices=["sdlc-v2"],
        help="입력 템플릿 계약 (기본: sdlc-v2)",
    )

    p_gate_record = subparsers.add_parser(
        "scenario-gate-record",
        help="목표-커버 게이트 이력에 회차 판정 1건을 기록(167/목표-커버 기록 명령)",
    )
    p_gate_record.add_argument("--task-folder", required=True, metavar="PATH", help="태스크 폴더 경로")
    p_gate_record.add_argument("--iteration", required=True, type=int, metavar="N", help="회차 번호")
    p_gate_record.add_argument("--evaluator-result", metavar="PATH", help="evaluator scenario-rubric 결과 JSON 경로")
    p_gate_record.add_argument("--advisory-responses", metavar="PATH", help="advisory 응답 JSON 경로")
    p_gate_record.add_argument(
        "--producer-artifact", default="TEST-SCENARIO.md", metavar="PATH",
        help="묶음 hash에 포함할 producer 산출물 (기본: TEST-SCENARIO.md)",
    )
    p_gate_record.add_argument(
        "--input-error", metavar="DETAIL",
        help="builder(scenario-coverage-build) 실패 시 evaluator·응답 검사 없이 escalate/input_error를 기록",
    )
    p_gate_record.add_argument(
        "--evidence-error", metavar="CODE",
        help="oppb evidence 실패 코드를 이력 마지막 원소에 붙이고 escalate/input_error로 바꾼다(--input-error와 배타적)",
    )

    p_gate_verify = subparsers.add_parser(
        "scenario-gate-verify",
        help="이력 마지막 원소가 pass이고 묶음 hash가 현재와 같은지 검증(167/목표-커버 검증 명령)",
    )
    p_gate_verify.add_argument("--task-folder", required=True, metavar="PATH", help="태스크 폴더 경로")
    p_gate_verify.add_argument(
        "--producer-artifact", default="TEST-SCENARIO.md", metavar="PATH",
        help="묶음 hash에 포함할 producer 산출물 (기본: TEST-SCENARIO.md)",
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
    "scenario-coverage-build": cmd_scenario_coverage_build,
    "scenario-gate-record": cmd_scenario_gate_record,
    "scenario-gate-verify": cmd_scenario_gate_verify,
}
