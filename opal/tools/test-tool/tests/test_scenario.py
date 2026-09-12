"""
@header {
  "module": "test_scenario",
  "task": "056,069,073,111,125",
  "layer": "test",
  "domain": "opal-tools",
  "description": "test-tool scenario-* public CLI regression tests for RED locking, coverage, fidelity, conformance, E2E v2 schema/runtime validation, status preservation, and human handoff/resume.",
  "scenarios": ["S-011", "S-012", "S-007", "S-014", "T069/S-5", "T069/S-6", "T069/S-7", "T073/S-1", "T073/S-2", "T111/S-6", "T111/S-7", "T111/S-8", "T111/S-9", "T111/S-10", "T111/S-11", "T111/S-18", "T125/S-2", "T125/S-5", "T125/S-7", "T125/S-8"],
  "exports": [
    "TestScenarioLockRedGate",
    "TestScenarioMarkLockGate",
    "TestScenarioResultContract",
    "TestExistingSuiteRegressionPresence",
    "TestScenarioRedToolGated",
    "TestScenarioSelectiveRedGate",
    "TestScenarioInitSeedNeutralized",
    "TestScenarioFidelityCheckUnmet",
    "TestScenarioFidelityCheckMixedAndLegacy",
    "TestScenarioConformance",
    "TestScenarioCoverageCheckUnmet",
    "TestScenarioCoverageCheckComplete",
    "TestScenarioCoverageInputInvalid",
    "TestScenarioCoverageCheckRegression",
    "TestScenarioCoverageBuildSdlcV2",
    "TestScenarioCoverageBuildInvalidSdlcV2",
    "TestScenarioV2PassGate",
    "TestScenarioV2StatusExitMapping",
    "TestScenarioHumanHandoffResume",
    "TestScenarioV1V2Boundary",
    "TestScenarioHandoffSchemaCorrection",
    "TestScenarioRuntimeValidationCorrection",
    "TestScenarioStatusCountsCorrection"
  ]
}

[T073] scenario-coverage-check 신규 서브명령 RED-first 테스트 (opd 시나리오 목표-커버리지 루브릭
게이트 루프, F-007). test-tool `scenario-coverage-check --coverage-input <path>`는 scenario-gate.md
§3 정규화 페이로드({goal, requirements[], features[], hypotheses[], scenarios[]})의 R/F/H↔시나리오
매핑 누락을 결정론 판정한다(루브릭 ②③④, ①⑤⑥은 opal-evaluator-agent 소관 — 본 서브명령 미판정).
현재 구현된 `scenario-coverage-check`와 `scenario-coverage-build`의 공개 CLI 계약을 회귀 보호한다.
exit 16(coverage_unmet)/17(coverage_input_invalid)은 기존 8~14와 충돌 없이 배정된다
(PLAN.md §3.2.2, 15는 정보용 예약이라 회피).

[T069] 069 태스크 추가분: scenario-fidelity-check(fidelity_unmet exit 13) + scenario-conformance
(surface_unverified exit 14 / surfaces_file_not_found exit 15) 신규 서브명령 RED-first 테스트.
두 서브명령의 구현 완료 계약과 기존 시나리오 호환성을 공개 CLI에서 회귀 보호한다.

[T056/ADD1] scenario-red 서브명령과 시드 무력화 계약을 회귀 보호한다. 기존 케이스(S-011/S-012/
  S-007/S-014)와 TestScenarioRedToolGated·TestScenarioInitSeedNeutralized가 함께 검증한다. 배경:
  `.opal/brain/pages/concept/oppl-scenario-red-confirmed-gap.md`
  (red_confirmed를 증거 없이 scenario-init 시드로 선언하는 우회 경로 봉쇄 — enforce-don't-advise 보강).

[T056] test-tool scenario-* 4서브명령 행위 계약 — RED-first TDD
검증 대상: opal/tools/test-tool/run.sh 의 공개 인터페이스(exit code + stdout JSON)만 단언.
내부 함수(lib/scenario.py)/private 결합 금지(red-first.md §4) — subprocess 실호출만 사용,
mock/patch/MagicMock 금지.

PLAN.md §3.2.2 근거:
  - test-scenario.json: schema_version/task_id/locked/created_at/locked_at/scenarios[]
    scenarios[]: id/acceptance_ref/type/expected/red_confirmed(spec존)/result·evidence·marked_at(result존)
  - scenario-lock: 전 시나리오 red_confirmed==true 일 때만 locked=true, 아니면 red_not_confirmed exit 8
  - scenario-mark: locked==true 이후에만 허용, 아니면 scenario_not_locked exit 9
  - scenario-status: 파일 부재 시 scenario_not_initialized exit 10
  - --scenarios 인자 JSON 파싱 실패 시 scenario_spec_invalid_json exit 11
  - 신규 에러코드 8~11은 기존 4서브명령 exit code(0~7 계열)와 충돌 없이 배정됨(→ D-12:196-249 회귀 보호)
"""

import json
import pathlib
import re
import subprocess
import tempfile
import shutil
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"
_EXISTING_SUITE = pathlib.Path(__file__).parent / "test_test_tool.py"


# ─────────────────────────────────────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _run(args, cwd=None):
    """run.sh를 subprocess로 실행하여 (returncode, stdout_text, parsed_json) 반환."""
    cmd = ["bash", str(_RUN_SH)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, data


def _scenario_init(task_path, scenarios):
    return _run([
        "scenario-init", "--task-path", str(task_path),
        "--scenarios", json.dumps(scenarios, ensure_ascii=False),
    ])


def _scenario_lock(task_path):
    return _run(["scenario-lock", "--task-path", str(task_path)])


def _scenario_mark(task_path, scenario_id, result, evidence=None):
    args = ["scenario-mark", "--task-path", str(task_path), "--id", scenario_id, "--result", result]
    if evidence:
        args += ["--evidence", evidence]
    return _run(args)


def _scenario_status(task_path):
    return _run(["scenario-status", "--task-path", str(task_path)])


def _set_red_confirmed(task_path, scenario_id, value):
    """test-scenario.json을 직접 read→patch→write — 외부 RED 증거 기록 프로세스(opal-test-agent)를
    모사하는 fixture 조작이며, scenario-lock/scenario-mark 공개 인터페이스 결합과는 무관하다."""
    spec_path = task_path / "test-scenario.json"
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    for sc in spec["scenarios"]:
        if sc["id"] == scenario_id:
            sc["red_confirmed"] = value
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)


SAMPLE_SCENARIOS = [
    {"id": "S1", "acceptance_ref": "AC1", "type": "unit", "expected": "S1 기대결과", "red_confirmed": False},
    {"id": "S2", "acceptance_ref": "AC2", "type": "unit", "expected": "S2 기대결과", "red_confirmed": False},
]


class BaseScenarioTestCase(unittest.TestCase):
    """임시 태스크 폴더 공통 베이스. 실 파일 생성·재읽기 — mock 금지(red-first.md §4)."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.task_path = self.tmpdir / "056-dryrun"
        self.task_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# S-011: scenario-lock RED-first 동결 게이트 [T056/L1-F002]
# ─────────────────────────────────────────────────────────────────────────────

class TestScenarioLockRedGate(BaseScenarioTestCase):
    """[T056/L1-F002] scenario-lock RED-first 동결 게이트 — S-011 (H-2)"""

    def test_lock_rejected_when_any_scenario_red_unconfirmed(self):
        """Given: S1(red=true)·S2(red=false). When: scenario-lock.
        Then: red_not_confirmed exit 8 (self-confirming 방지, H-2)."""
        code, stdout, data = _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        self.assertEqual(code, 0)
        self.assertFalse((self.task_path / "test-scenario.json").read_text(encoding="utf-8") == "")

        _set_red_confirmed(self.task_path, "S1", True)
        _set_red_confirmed(self.task_path, "S2", False)

        code, stdout, data = _scenario_lock(self.task_path)
        self.assertEqual(code, 8)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "red_not_confirmed")

    def test_lock_succeeds_when_all_scenarios_red_confirmed(self):
        """When: S2도 red=true로 갱신 후 재호출. Then: locked=true."""
        _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        _set_red_confirmed(self.task_path, "S1", True)
        _set_red_confirmed(self.task_path, "S2", True)

        code, stdout, data = _scenario_lock(self.task_path)
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertTrue(data.get("locked"))

        with open(self.task_path / "test-scenario.json", encoding="utf-8") as f:
            spec = json.load(f)
        self.assertTrue(spec.get("locked"))
        self.assertIsNotNone(spec.get("locked_at"))


# ─────────────────────────────────────────────────────────────────────────────
# S-012: scenario-mark 잠금 전 기록 차단 [T056/L1-F002]
# ─────────────────────────────────────────────────────────────────────────────

class TestScenarioMarkLockGate(BaseScenarioTestCase):
    """[T056/L1-F002] scenario-mark 잠금 전 기록 차단 — S-012 (H-2)"""

    def setUp(self):
        super().setUp()
        _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        _set_red_confirmed(self.task_path, "S1", True)
        _set_red_confirmed(self.task_path, "S2", True)

    def test_mark_rejected_before_lock(self):
        """Given: locked=false. When: scenario-mark --result pass.
        Then: scenario_not_locked exit 9."""
        code, stdout, data = _scenario_mark(self.task_path, "S1", "pass", evidence="pytest exit 0")
        self.assertEqual(code, 9)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "scenario_not_locked")

    def test_mark_succeeds_after_lock(self):
        """When: lock 후 재호출. Then: result·evidence 기록 성공."""
        lock_code, _, _ = _scenario_lock(self.task_path)
        self.assertEqual(lock_code, 0)

        code, stdout, data = _scenario_mark(self.task_path, "S1", "pass", evidence="pytest exit 0")
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("scenario_id"), "S1")
        self.assertEqual(data.get("result"), "pass")

        with open(self.task_path / "test-scenario.json", encoding="utf-8") as f:
            spec = json.load(f)
        s1 = next(s for s in spec["scenarios"] if s["id"] == "S1")
        self.assertEqual(s1.get("result"), "pass")
        self.assertEqual(s1.get("evidence"), "pytest exit 0")
        self.assertIsNotNone(s1.get("marked_at"))

    def test_mark_records_blocked_result_and_status_count(self):
        """실행 환경이 없을 때 BLOCKED를 증거와 함께 결과 SSOT에 기록한다."""
        lock_code, _, _ = _scenario_lock(self.task_path)
        self.assertEqual(lock_code, 0)

        code, _, data = _scenario_mark(
            self.task_path,
            "S1",
            "blocked",
            evidence="required API endpoint unavailable",
        )
        self.assertEqual(code, 0)
        self.assertEqual(data.get("result"), "blocked")

        status_code, _, status = _scenario_status(self.task_path)
        self.assertEqual(status_code, 0)
        self.assertEqual(status.get("blocked"), 1)


# ─────────────────────────────────────────────────────────────────────────────
# S-007 (scenario 몫): 도구 결과 계약 — 단일라인 JSON + exit code [T056/L1-F002]
# ─────────────────────────────────────────────────────────────────────────────

class TestScenarioResultContract(BaseScenarioTestCase):
    """[T056/L1-F002] scenario-* 4서브명령 결과 계약 — S-007 (H-5)"""

    def _assert_single_line_json(self, stdout, data):
        self.assertEqual(len(stdout.splitlines()), 1, "stdout은 단일라인이어야 한다")
        self.assertNotIn("_raw", data, "stdout이 유효 JSON으로 파싱되지 않음")

    def test_scenario_init_success_contract(self):
        code, stdout, data = _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 0)
        self.assertIs(data.get("ok"), True)
        self.assertEqual(data.get("scenarios_count"), 2)

    def test_scenario_init_invalid_json_contract(self):
        """--scenarios에 파싱 불가능한 값 전달 시 scenario_spec_invalid_json exit 11."""
        code, stdout, data = _run([
            "scenario-init", "--task-path", str(self.task_path),
            "--scenarios", "{not-valid-json",
        ])
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 11)
        self.assertEqual(data.get("error"), "scenario_spec_invalid_json")

    def test_scenario_status_not_initialized_contract(self):
        """test-scenario.json 부재 상태에서 scenario-status 호출 시 scenario_not_initialized exit 10."""
        code, stdout, data = _scenario_status(self.task_path)
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 10)
        self.assertEqual(data.get("error"), "scenario_not_initialized")

    def test_scenario_status_success_contract(self):
        _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        code, stdout, data = _scenario_status(self.task_path)
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 0)
        self.assertIn("locked", data)
        self.assertIn("total", data)
        self.assertIn("red_confirmed", data)
        self.assertIn("passed", data)
        self.assertIn("failed", data)

    def test_scenario_lock_error_contract(self):
        _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        code, stdout, data = _scenario_lock(self.task_path)
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 8)

    def test_scenario_mark_error_contract(self):
        _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        code, stdout, data = _scenario_mark(self.task_path, "S1", "pass")
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 9)


# ─────────────────────────────────────────────────────────────────────────────
# S-014: 기존 test-tool 4서브명령 회귀 스위트 — 존재 확인만 (기존 파일 미수정)
# ─────────────────────────────────────────────────────────────────────────────

class TestExistingSuiteRegressionPresence(unittest.TestCase):
    """[T056/L2-F002] 기존 test_test_tool.py 회귀 스위트 존재 확인 — S-014.
    기존 4서브명령(resolve/check/unit/integration) 로직 회귀 검증은 기존 스위트가 전담한다.
    본 케이스는 그 스위트가 온전히 존재하는지만 확인하며, 기존 파일은 수정하지 않는다."""

    def test_existing_suite_file_exists(self):
        self.assertTrue(_EXISTING_SUITE.exists(), "기존 test_test_tool.py가 존재해야 한다")

    def test_existing_suite_covers_four_subcommands(self):
        content = _EXISTING_SUITE.read_text(encoding="utf-8")
        for cls_name in ("TestResolve", "TestUnit", "TestCheck", "TestIntegration"):
            self.assertTrue(
                re.search(rf"class\s+{cls_name}\w*", content),
                f"기존 스위트에 {cls_name}* 클래스가 존재해야 한다(회귀 커버리지 확인)",
            )

    def test_test_tool_dispatch_unchanged_keys_present(self):
        """test_tool.py의 dispatch dict에 기존 4서브명령 키가 여전히 존재해야 한다(회귀 불변).
        scenario-* 4종은 추가되어야 하지만 기존 키 삭제는 금지."""
        tool_py = _TOOL_DIR / "test_tool.py"
        content = tool_py.read_text(encoding="utf-8")
        for key in ("resolve", "check", "unit", "integration"):
            self.assertIn(f'"{key}"', content, f"dispatch dict에 기존 키 '{key}'가 유지되어야 한다")


# ─────────────────────────────────────────────────────────────────────────────
# ADD-1: scenario-red — RED 증거 tool-gated 갱신 [T056/ADD1]
# ─────────────────────────────────────────────────────────────────────────────

def _scenario_red(task_path, scenario_id, evidence=None):
    args = ["scenario-red", "--task-path", str(task_path), "--id", scenario_id]
    if evidence is not None:
        args += ["--evidence", evidence]
    return _run(args)


class TestScenarioRedToolGated(BaseScenarioTestCase):
    """[T056/ADD1] scenario-red — RED 증거 tool-gated red_confirmed 갱신 (enforce-don't-advise 보강)"""

    def setUp(self):
        super().setUp()
        _scenario_init(self.task_path, SAMPLE_SCENARIOS)

    def test_scenario_red_updates_red_confirmed_with_evidence(self):
        """Given: red_confirmed=false(init 시드, 증거 없음). When: scenario-red --evidence <RED 출력 요약>.
        Then: red_confirmed=true + red_evidence·red_at 기록, exit 0."""
        code, stdout, data = _scenario_red(
            self.task_path, "S1", evidence="pytest FAILED test_x — AssertionError: expected 1 got 0",
        )
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("scenario_id"), "S1")
        self.assertTrue(data.get("red_confirmed"))

        with open(self.task_path / "test-scenario.json", encoding="utf-8") as f:
            spec = json.load(f)
        s1 = next(s for s in spec["scenarios"] if s["id"] == "S1")
        self.assertTrue(s1.get("red_confirmed"))
        self.assertEqual(s1.get("red_evidence"), "pytest FAILED test_x — AssertionError: expected 1 got 0")
        self.assertIsNotNone(s1.get("red_at"))
        # S2는 변경되지 않아야 한다 (대상 시나리오만 갱신).
        s2 = next(s for s in spec["scenarios"] if s["id"] == "S2")
        self.assertFalse(s2.get("red_confirmed"))

    def test_scenario_red_rejected_without_evidence(self):
        """Given: --evidence 미전달. When: scenario-red. Then: argparse required 위반으로 거부(exit != 0,
        성공 응답 아님) — evidence 없는 red_confirmed 갱신 자체가 불가능해야 한다."""
        code, stdout, data = _scenario_red(self.task_path, "S1", evidence=None)
        self.assertNotEqual(code, 0)
        self.assertFalse(data.get("ok"))

        with open(self.task_path / "test-scenario.json", encoding="utf-8") as f:
            spec = json.load(f)
        s1 = next(s for s in spec["scenarios"] if s["id"] == "S1")
        self.assertFalse(s1.get("red_confirmed"), "evidence 없이는 red_confirmed가 갱신되면 안 된다")

    def test_scenario_red_rejected_when_locked(self):
        """Given: 전 시나리오 red_confirmed=true 후 scenario-lock 통과(locked=true). When: scenario-red 재호출.
        Then: 신규 에러코드 scenario_already_locked로 거부 — locked 이후 spec존 변경 금지."""
        _set_red_confirmed(self.task_path, "S1", True)
        _set_red_confirmed(self.task_path, "S2", True)
        lock_code, _, _ = _scenario_lock(self.task_path)
        self.assertEqual(lock_code, 0)

        code, stdout, data = _scenario_red(self.task_path, "S1", evidence="locked 이후 재시도 증거")
        self.assertNotEqual(code, 0)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "scenario_already_locked")


class TestScenarioSelectiveRedGate(BaseScenarioTestCase):
    """[T111/S-18] red_required=true인 시나리오만 RED 잠금 게이트에 포함한다."""

    MIXED_SCENARIOS = [
        {
            "id": "S1",
            "acceptance_ref": "AC1",
            "type": "unit",
            "expected": "구현 전에 실패해야 함",
            "red_required": True,
        },
        {
            "id": "S2",
            "acceptance_ref": "AC2",
            "type": "regression",
            "expected": "기존 동작 회귀 확인",
            "red_required": False,
        },
    ]

    def test_init_preserves_red_required_and_lock_checks_only_required_scenarios(self):
        code, _, data = _scenario_init(self.task_path, self.MIXED_SCENARIOS)
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))

        spec = json.loads((self.task_path / "test-scenario.json").read_text(encoding="utf-8"))
        scenarios = {s["id"]: s for s in spec["scenarios"]}
        self.assertTrue(scenarios["S1"]["red_required"])
        self.assertFalse(scenarios["S2"]["red_required"])
        self.assertFalse(scenarios["S1"]["red_confirmed"])
        self.assertFalse(scenarios["S2"]["red_confirmed"])

        lock_code, _, lock_data = _scenario_lock(self.task_path)
        self.assertEqual(lock_code, 8)
        self.assertIn("S1", lock_data.get("detail", ""))
        self.assertNotIn("S2", lock_data.get("detail", ""))

        red_code, _, _ = _scenario_red(self.task_path, "S1", evidence="pytest failed before implementation")
        self.assertEqual(red_code, 0)
        lock_code, _, lock_data = _scenario_lock(self.task_path)
        self.assertEqual(lock_code, 0)
        self.assertTrue(lock_data.get("locked"))

    def test_status_reports_required_red_progress_separately(self):
        _scenario_init(self.task_path, self.MIXED_SCENARIOS)
        _scenario_red(self.task_path, "S1", evidence="pytest failed before implementation")

        code, _, data = _scenario_status(self.task_path)
        self.assertEqual(code, 0)
        self.assertEqual(data.get("red_required"), 1)
        self.assertEqual(data.get("red_confirmed_required"), 1)


class TestScenarioInitSeedNeutralized(BaseScenarioTestCase):
    """[T056/ADD1] scenario-init red_confirmed 시드 입력 무력화 — RED 미관찰 우회 선언 봉쇄"""

    def test_scenario_init_forces_red_confirmed_false_regardless_of_seed(self):
        """Given: --scenarios에 red_confirmed=true로 시드 입력(관찰 없이 선언 시도).
        When: scenario-init.
        Then: 생성된 spec존 red_confirmed는 시드값과 무관하게 항상 false + 응답에 warning 포함
        (init 시드로 red_confirmed를 우회 선언하는 경로 봉쇄)."""
        seeded = [
            {"id": "S1", "acceptance_ref": "AC1", "type": "unit", "expected": "e1", "red_confirmed": True},
            {"id": "S2", "acceptance_ref": "AC2", "type": "unit", "expected": "e2", "red_confirmed": False},
        ]
        code, stdout, data = _scenario_init(self.task_path, seeded)
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertIn("warning", data, "red_confirmed 시드 시도 시 응답에 warning 필드가 있어야 한다")

        with open(self.task_path / "test-scenario.json", encoding="utf-8") as f:
            spec = json.load(f)
        s1 = next(s for s in spec["scenarios"] if s["id"] == "S1")
        s2 = next(s for s in spec["scenarios"] if s["id"] == "S2")
        self.assertFalse(s1.get("red_confirmed"), "true 시드도 무시되어 false로 생성되어야 한다")
        self.assertFalse(s2.get("red_confirmed"))



# ─────────────────────────────────────────────────────────────────────────────
# [T069] scenario-fidelity-check / scenario-conformance 공개 CLI 회귀 테스트
# 검증 대상: opal/tools/test-tool/run.sh 공개 인터페이스(exit code + stdout JSON)만
# 단언 — 내부 함수 직접 import 금지(red-first.md §4). PLAN.md §3.5.2/§3.6.2 근거.
# 구현된 두 서브명령의 fidelity/conformance 경계와 기존 호환성을 보호한다.
# ─────────────────────────────────────────────────────────────────────────────

def _scenario_fidelity_check(task_path):
    """scenario-fidelity-check 신규 서브명령 호출 헬퍼 [T069] (PLAN §3.5.2)."""
    return _run(["scenario-fidelity-check", "--task-path", str(task_path)])


def _scenario_conformance(task_path, surfaces_path=None):
    """scenario-conformance 신규 서브명령 호출 헬퍼 [T069] (PLAN §3.6.2)."""
    args = ["scenario-conformance", "--task-path", str(task_path)]
    if surfaces_path is not None:
        args += ["--surfaces", str(surfaces_path)]
    return _run(args)


def _patch_scenario_fields(task_path, scenario_id, **fields):
    """test-scenario.json을 직접 read→patch→write [T069] — `_set_red_confirmed`와 동일한
    fixture 조작 패턴(외부 기록 프로세스 모사). scenario-fidelity-check/scenario-conformance
    공개 인터페이스 결합과는 무관하다(red-first.md §4)."""
    spec_path = task_path / "test-scenario.json"
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    for sc in spec["scenarios"]:
        if sc["id"] == scenario_id:
            sc.update(fields)
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)


def _write_surfaces_fixture_for_scenario(dest_dir):
    """fixture-A(test-tool 몫): 표면 3종(auth-login:auth none, agents/budgets:auth required) +
    origins.dev 선언 — TEST-SCENARIO.md §2.1 fixture-A 재현 (backlog-tool 몫과 동일 데이터,
    축 분리 원칙상 파일은 별도로 이 테스트 모듈 안에서 자체 생성한다)."""
    surfaces = {
        "origins": ["https://app.dev"],
        "surfaces": [
            {"id": "auth-login", "auth": "none"},
            {"id": "agents", "auth": "required"},
            {"id": "budgets", "auth": "required"},
        ],
    }
    path = pathlib.Path(dest_dir) / "surfaces.json"
    path.write_text(json.dumps(surfaces, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


class TestScenarioFidelityCheckUnmet(BaseScenarioTestCase):
    """[T069/S-5] scenario-fidelity-check 요구 충실도 미달 거부 (H-3).
    fixture-C1: S1(required_fidelity=real-usage, fidelity=mock, result=pass)."""

    def test_fidelity_check_rejects_unmet_scenario(self):
        code, _, _ = _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        self.assertEqual(code, 0)
        _patch_scenario_fields(
            self.task_path, "S1",
            required_fidelity="real-usage", fidelity="mock", result="pass",
        )

        code, stdout, data = _scenario_fidelity_check(self.task_path)
        self.assertEqual(code, 13)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "fidelity_unmet")
        self.assertIn("S1", data.get("detail", []))


class TestScenarioFidelityCheckMixedAndLegacy(BaseScenarioTestCase):
    """[T069/S-6] fidelity 혼합 트랙 부분 게이트 + 구형식 하위 호환 (H-6, task:061 재발 방지)."""

    def test_mixed_track_all_met_passes(self):
        """fixture-C2: S1(req=mock 충족)+S2(req=real-usage, fid=real-usage 충족) 혼합.
        Then: 전체-게이트가 아니라 각자 충족 시 all_met exit 0(부분 게이트, R-B)."""
        code, _, _ = _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        self.assertEqual(code, 0)
        _patch_scenario_fields(
            self.task_path, "S1",
            required_fidelity="mock", fidelity="mock", result="pass",
        )
        _patch_scenario_fields(
            self.task_path, "S2",
            required_fidelity="real-usage", fidelity="real-usage", result="pass",
        )

        code, stdout, data = _scenario_fidelity_check(self.task_path)
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertTrue(data.get("all_met"))

    def test_legacy_format_without_fidelity_fields_passes(self):
        """fixture-C3: required_fidelity/fidelity 필드 자체 부재(구버전 형식).
        Then: 기본값 mock>=mock으로 통과 exit 0(회귀 0, H-6)."""
        code, _, _ = _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        self.assertEqual(code, 0)
        # 구형식 재현: required_fidelity/fidelity 키 자체를 제거(수기 JSON)
        spec_path = self.task_path / "test-scenario.json"
        with open(spec_path, encoding="utf-8") as f:
            spec = json.load(f)
        for sc in spec["scenarios"]:
            sc.pop("required_fidelity", None)
            sc.pop("fidelity", None)
            sc["result"] = "pass"
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)

        code, stdout, data = _scenario_fidelity_check(self.task_path)
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertTrue(data.get("all_met"))


class TestScenarioConformance(BaseScenarioTestCase):
    """[T069/S-7] scenario-conformance 전수 판정 + surfaces 부재 스킵 (H-4)."""

    def test_conformance_rejects_unverified_surfaces(self):
        """fixture-A + fixture-C4: surface_ref로 auth-login만 pass — agents·budgets 미검증.
        Then: surface_unverified + detail=[agents,budgets] exit 14."""
        surfaces_path = _write_surfaces_fixture_for_scenario(self.tmpdir)
        code, _, _ = _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        self.assertEqual(code, 0)
        _patch_scenario_fields(
            self.task_path, "S1",
            surface_ref="auth-login", result="pass", fidelity="real-http",
        )
        # S2는 surface_ref 미지정 상태로 남겨 agents/budgets 미검증 상태 유지

        code, stdout, data = _scenario_conformance(self.task_path, surfaces_path)
        self.assertEqual(code, 14)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "surface_unverified")
        self.assertEqual(sorted(data.get("detail", [])), ["agents", "budgets"])
        self.assertFalse(data.get("all_surfaces_green", True))

    def test_conformance_all_surfaces_green(self):
        """전 표면 pass 상태(auth 표면은 fidelity>=real-http) → all_surfaces_green:true exit 0."""
        surfaces_path = _write_surfaces_fixture_for_scenario(self.tmpdir)
        scenarios = [
            {"id": "S1", "acceptance_ref": "AC1", "type": "unit", "expected": "e1", "red_confirmed": False},
            {"id": "S2", "acceptance_ref": "AC2", "type": "unit", "expected": "e2", "red_confirmed": False},
            {"id": "S3", "acceptance_ref": "AC3", "type": "unit", "expected": "e3", "red_confirmed": False},
        ]
        code, _, _ = _scenario_init(self.task_path, scenarios)
        self.assertEqual(code, 0)
        _patch_scenario_fields(self.task_path, "S1", surface_ref="auth-login", result="pass", fidelity="mock")
        _patch_scenario_fields(self.task_path, "S2", surface_ref="agents", result="pass", fidelity="real-http")
        _patch_scenario_fields(self.task_path, "S3", surface_ref="budgets", result="pass", fidelity="real-http")

        code, stdout, data = _scenario_conformance(self.task_path, surfaces_path)
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertTrue(data.get("all_surfaces_green"))
        self.assertEqual(data.get("surface_count"), 3)

    def test_conformance_skips_when_surfaces_absent(self):
        """surfaces.json 부재 → applicable:false 스킵(기존 프로젝트·비-API 무영향, M-5) exit 0."""
        code, _, _ = _scenario_init(self.task_path, SAMPLE_SCENARIOS)
        self.assertEqual(code, 0)
        missing_surfaces_path = self.tmpdir / "surfaces.json"  # 의도적으로 생성하지 않음

        code, stdout, data = _scenario_conformance(self.task_path, missing_surfaces_path)
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertFalse(data.get("applicable"))


# ─────────────────────────────────────────────────────────────────────────────
# [T073] scenario-coverage-check 공개 CLI 회귀 테스트
# 검증 대상: run.sh 공개 인터페이스(exit code + stdout JSON)만 단언 — 내부 함수 직접
# import 금지(red-first.md §4). PLAN.md §3.2.2 / scenario-gate.md §3 정규화 계약 근거.
# 구현된 커버리지 판정과 기존 scenario-* dispatch/exit 계약을 보호한다.
# ─────────────────────────────────────────────────────────────────────────────

def _write_coverage_fixture(dest_dir, payload):
    """scenario-gate.md §3 정규화 페이로드를 임시 JSON 파일로 기록 — coverage-input fixture."""
    path = pathlib.Path(dest_dir) / "coverage-input.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _scenario_coverage_check(coverage_input_path):
    """scenario-coverage-check 신규 서브명령 호출 헬퍼 [T073] (PLAN §3.2.2)."""
    return _run(["scenario-coverage-check", "--coverage-input", str(coverage_input_path)])


def _scenario_coverage_build(task_path, template="sdlc-v2"):
    """scenario-coverage-build 서브명령 호출 헬퍼 [T111/W-5].

    2026-09-09 14:18 KST task 111: sdlc-v2 TASK/PLAN/TEST-SCENARIO를 결정론적으로
    .scenario-coverage-input.json으로 변환하는 공개 CLI 계약을 검증한다.
    """
    return _run([
        "scenario-coverage-build",
        "--task-folder", str(task_path),
        "--template", template,
    ])


# fixture-cov-missing: requirements=[R-1,R-2], hypotheses=[H-1] 중 R-2·H-1이 어떤 시나리오에도
# 매핑되지 않은 페이로드 (S-1 조건, TEST-SCENARIO.md §3 S-1).
FX_COV_MISSING = {
    "goal": "T073 시나리오 목표-커버리지 게이트가 R/F/H 매핑 누락을 결정론 판정한다",
    "requirements": ["R-1", "R-2"],
    "features": ["F-001"],
    "hypotheses": ["H-1"],
    "scenarios": [
        {
            "id": "S-1",
            "covers_requirements": ["R-1"],
            "covers_features": ["F-001"],
            "covers_hypotheses": [],
            "is_goal_scenario": True,
            "is_adoption_scenario": False,
            "is_boundary_scenario": False,
        }
    ],
}

# fixture-cov-complete: 전 R/F/H가 시나리오에 매핑된 페이로드 (S-1 보완 케이스, exit0 기대).
FX_COV_COMPLETE = {
    "goal": "T073 시나리오 목표-커버리지 게이트가 R/F/H 매핑 누락을 결정론 판정한다",
    "requirements": ["R-1", "R-2"],
    "features": ["F-001"],
    "hypotheses": ["H-1"],
    "scenarios": [
        {
            "id": "S-1",
            "covers_requirements": ["R-1", "R-2"],
            "covers_features": ["F-001"],
            "covers_hypotheses": ["H-1"],
            "is_goal_scenario": True,
            "is_adoption_scenario": False,
            "is_boundary_scenario": False,
        }
    ],
}


class TestScenarioCoverageCheckUnmet(BaseScenarioTestCase):
    """[T073/L1-R2a] scenario-coverage-check 미커버 R/H 결정론 거부 — S-1 (H-1).
    거짓 초록불 차단: 미커버가 있는데 ok 반환하면 안 된다(070 재발 방지)."""

    def test_missing_requirement_and_hypothesis_rejected(self):
        """Given: fx-cov-missing.json(R-2·H-1 미매핑). When: scenario-coverage-check.
        Then: exit 16(coverage_unmet) + detail.missing.requirements=["R-2"],
        detail.missing.hypotheses=["H-1"], detail.missing.features=[]."""
        fx_path = _write_coverage_fixture(self.tmpdir, FX_COV_MISSING)
        code, stdout, data = _scenario_coverage_check(fx_path)

        self.assertEqual(code, 16, f"기대 exit 16(coverage_unmet), 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_unmet")
        missing = data.get("detail", {}).get("missing", {})
        self.assertEqual(missing.get("requirements"), ["R-2"])
        self.assertEqual(missing.get("hypotheses"), ["H-1"])
        self.assertEqual(missing.get("features"), [])
        self.assertFalse(data.get("all_covered"), "미커버 존재 시 all_covered는 참이면 안 된다")


class TestScenarioCoverageCheckComplete(BaseScenarioTestCase):
    """[T073/L1-R2b] scenario-coverage-check 전 R/F/H 커버 시 exit 0 통과 — S-1 보완 (H-1)."""

    def test_all_requirements_features_hypotheses_covered(self):
        """Given: fx-cov-complete.json(전 R/F/H 매핑). When: scenario-coverage-check.
        Then: exit 0 + all_covered:true."""
        fx_path = _write_coverage_fixture(self.tmpdir, FX_COV_COMPLETE)
        code, stdout, data = _scenario_coverage_check(fx_path)

        self.assertEqual(code, 0, f"기대 exit 0, 실제 stdout={stdout!r}")
        self.assertTrue(data.get("ok"))
        self.assertTrue(data.get("all_covered"))


class TestScenarioCoverageInputInvalid(BaseScenarioTestCase):
    """[T073/L1-R2c] scenario-coverage-check --coverage-input 부재/파손/필수키누락 시 exit 17 거부."""

    def test_rejects_when_file_absent(self):
        """Given: --coverage-input 경로가 존재하지 않음. Then: coverage_input_invalid exit 17."""
        missing_path = pathlib.Path(self.tmpdir) / "does-not-exist.json"
        code, stdout, data = _scenario_coverage_check(missing_path)

        self.assertEqual(code, 17, f"기대 exit 17(coverage_input_invalid), 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_input_invalid")

    def test_rejects_when_json_malformed(self):
        """Given: fx-cov-broken.json(JSON 파손). Then: coverage_input_invalid exit 17."""
        broken_path = pathlib.Path(self.tmpdir) / "fx-cov-broken.json"
        broken_path.write_text("{not-valid-json", encoding="utf-8")
        code, stdout, data = _scenario_coverage_check(broken_path)

        self.assertEqual(code, 17, f"기대 exit 17(coverage_input_invalid), 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_input_invalid")

    def test_rejects_when_required_keys_missing(self):
        """Given: 정규화 페이로드 필수 키(features/hypotheses/scenarios) 누락.
        Then: coverage_input_invalid exit 17."""
        incomplete = {"goal": "T073 필수키 누락 케이스", "requirements": ["R-1"]}
        incomplete_path = _write_coverage_fixture(self.tmpdir, incomplete)
        code, stdout, data = _scenario_coverage_check(incomplete_path)

        self.assertEqual(code, 17, f"기대 exit 17(coverage_input_invalid), 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_input_invalid")


class TestScenarioCoverageCheckRegression(unittest.TestCase):
    """[T073/L1-REG] 기존 scenario-* 7서브명령 dispatch 키·exit 8~14 불변 확인 — S-2 (H-2,
    additive 보장). scenario-coverage-check 신규 배정이 기존 계약을 깨지 않는지 회귀 확인."""

    _SCENARIO_PY = _TOOL_DIR / "lib" / "scenario.py"

    def test_existing_seven_dispatch_keys_present(self):
        content = self._SCENARIO_PY.read_text(encoding="utf-8")
        for key in (
            "scenario-init", "scenario-lock", "scenario-mark", "scenario-status",
            "scenario-red", "scenario-fidelity-check", "scenario-conformance",
        ):
            self.assertIn(
                f'"{key}"', content,
                f"SCENARIO_DISPATCH에 기존 키 '{key}'가 유지되어야 한다(회귀 0)",
            )

    def test_dispatch_dict_grows_additively(self):
        """SCENARIO_DISPATCH 정의 블록에 기존 7개 이상(신규 추가 후 8개)의 cmd_scenario_* 매핑이
        존재해야 한다 — 삭제 없는 additive 확장만 허용."""
        content = self._SCENARIO_PY.read_text(encoding="utf-8")
        parts = content.split("SCENARIO_DISPATCH: Dict[str, Any] = {", 1)
        self.assertEqual(len(parts), 2, "SCENARIO_DISPATCH 정의를 찾을 수 없다")
        body = parts[1].split("}", 1)[0]
        key_count = body.count(": cmd_scenario")
        self.assertGreaterEqual(key_count, 7, "기존 7개 dispatch 키가 유지되어야 한다")

    def test_existing_error_codes_still_functional(self):
        """exit 8~10을 유발하는 기존 계약이 실 CLI 호출로도 여전히 성립하는지 회귀 확인
        (subprocess 실호출, mock 금지)."""
        tmpdir = pathlib.Path(tempfile.mkdtemp())
        try:
            task_path = tmpdir / "073-regression-check"
            task_path.mkdir()

            code, stdout, data = _scenario_status(task_path)
            self.assertEqual(code, 10, f"scenario_not_initialized 회귀, stdout={stdout!r}")
            self.assertEqual(data.get("error"), "scenario_not_initialized")

            init_code, _, _ = _scenario_init(task_path, SAMPLE_SCENARIOS)
            self.assertEqual(init_code, 0)

            code, stdout, data = _scenario_lock(task_path)
            self.assertEqual(code, 8, f"red_not_confirmed 회귀, stdout={stdout!r}")
            self.assertEqual(data.get("error"), "red_not_confirmed")

            code, stdout, data = _scenario_mark(task_path, "S1", "pass")
            self.assertEqual(code, 9, f"scenario_not_locked 회귀, stdout={stdout!r}")
            self.assertEqual(data.get("error"), "scenario_not_locked")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# [T111] scenario-coverage-build — sdlc-v2 문서 → coverage input 결정론 변환
# 검증 대상: run.sh 공개 인터페이스(exit code + stdout JSON)만 단언한다.
# ─────────────────────────────────────────────────────────────────────────────

def _write_sdlc_v2_docs(task_path, *, task_body=None, plan_body=None, scenario_body=None):
    task_path.mkdir(parents=True, exist_ok=True)
    (task_path / "TASK.md").write_text(task_body or """---
template: sdlc-v2
---
# TASK: Builder fixture

## Problem

Builder가 새 문서의 검증 토큰을 읽어야 한다.

## Proposed outcome

Coverage input이 결정론적으로 생성된다.

## Affected users and systems

- 사용자: PM
- 시스템: test-tool

## Constraints

- C-1: W 토큰을 기능 분모로 취급하지 않는다.
- C-2: 알 수 없는 검증 참조는 실패한다.

## Acceptance criteria

- AC-1: AC와 C가 requirements에 포함된다.
- AC-2: TEST-SCENARIO의 S 행이 AC/C/H 커버로 변환된다.
""", encoding="utf-8")
    (task_path / "PLAN.md").write_text(plan_body or """---
template: sdlc-v2
---
# PLAN: Builder fixture

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. Builder 구현 | opal-be-agent | `opal/tools/test-tool/lib/scenario.py` | build 추가 | 없음 | P1 | AC-1, C-1 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 빈 분모 통과 | coverage build | false green | AC/C/S 추출 실패를 거부 |
| H-2. W를 F로 오해 | coverage check | 과잉 시나리오 | W는 features에 넣지 않음 |
""", encoding="utf-8")
    (task_path / "TEST-SCENARIO.md").write_text(scenario_body or """---
template: sdlc-v2
---
# TEST-SCENARIO: Builder fixture

## Setup

- 환경: 임시 태스크 폴더

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1, H-1 | 정상 문서 | build 실행 | requirements와 hypotheses가 채워짐 | CLI | 구현 전 RED, 구현 후 |
| S-2 | AC-2, C-2, H-2 | 정상 문서 | build 실행 | W는 features에 들어가지 않음 | CLI | 구현 전 RED, 구현 후 |
""", encoding="utf-8")


class TestScenarioCoverageBuildSdlcV2(BaseScenarioTestCase):
    """[T111/S-6] sdlc-v2 scenario-coverage-build 정상 변환 계약."""

    def test_builds_coverage_input_from_sdlc_v2_docs(self):
        _write_sdlc_v2_docs(self.task_path)

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 0, f"기대 exit 0, 실제 stdout={stdout!r}")
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("command"), "scenario-coverage-build")
        output_path = pathlib.Path(data.get("coverage_input"))
        self.assertEqual(output_path, self.task_path / ".scenario-coverage-input.json")
        self.assertTrue(output_path.exists())

        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload.get("requirements"), ["AC-1", "AC-2", "C-1", "C-2"])
        self.assertEqual(payload.get("features"), [])
        self.assertEqual(payload.get("hypotheses"), ["H-1", "H-2"])
        self.assertEqual([s.get("id") for s in payload.get("scenarios", [])], ["S-1", "S-2"])
        self.assertEqual(payload["scenarios"][0]["covers_requirements"], ["AC-1", "C-1"])
        self.assertEqual(payload["scenarios"][0]["covers_hypotheses"], ["H-1"])
        self.assertEqual(payload["scenarios"][0]["covers_features"], [])

        check_code, check_stdout, check_data = _scenario_coverage_check(output_path)
        self.assertEqual(check_code, 0, f"coverage-check 회귀 실패 stdout={check_stdout!r}")
        self.assertTrue(check_data.get("all_covered"))

    def test_allows_zero_hypotheses_when_risks_declares_none(self):
        _write_sdlc_v2_docs(
            self.task_path,
            plan_body="""---
template: sdlc-v2
---
# PLAN: Builder fixture

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. Builder 구현 | opal-be-agent | `opal/tools/test-tool/lib/scenario.py` | build 추가 | 없음 | P1 | AC-1, C-1 |

## Risks

추가 검증이 필요한 위험 없음.
""",
            scenario_body="""---
template: sdlc-v2
---
# TEST-SCENARIO: No hypotheses

## Setup
- 환경: 임시 태스크 폴더

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1 | 정상 문서 | build 실행 | requirements가 채워짐 | CLI | 구현 전 RED, 구현 후 |
| S-2 | AC-2, C-2 | 정상 문서 | coverage check 실행 | H가 없어도 통과 | CLI | 구현 전 RED, 구현 후 |
""",
        )

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 0, f"기대 exit 0, 실제 stdout={stdout!r}")
        output_path = pathlib.Path(data.get("coverage_input"))
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload.get("hypotheses"), [])

        check_code, check_stdout, check_data = _scenario_coverage_check(output_path)
        self.assertEqual(check_code, 0, f"H=0 coverage-check 회귀 실패 stdout={check_stdout!r}")
        self.assertTrue(check_data.get("all_covered"))

    def test_existing_hypothesis_must_still_be_covered(self):
        _write_sdlc_v2_docs(
            self.task_path,
            scenario_body="""---
template: sdlc-v2
---
# TEST-SCENARIO: Missing existing hypothesis coverage

## Setup
- 환경: 임시 태스크 폴더

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1, H-1 | 정상 문서 | build 실행 | 일부 H만 커버 | CLI | 구현 전 RED, 구현 후 |
| S-2 | AC-2, C-2 | 정상 문서 | coverage check 실행 | H-2 미커버 실패 | CLI | 구현 전 RED, 구현 후 |
""",
        )

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 0, f"기대 exit 0, 실제 stdout={stdout!r}")
        output_path = pathlib.Path(data.get("coverage_input"))

        check_code, check_stdout, check_data = _scenario_coverage_check(output_path)
        self.assertEqual(check_code, 16, f"기대 exit 16, 실제 stdout={check_stdout!r}")
        self.assertFalse(check_data.get("all_covered"))
        self.assertIn("H-2", str(check_data.get("detail")))


class TestScenarioCoverageBuildInvalidSdlcV2(BaseScenarioTestCase):
    """[T111/S-7] sdlc-v2 scenario-coverage-build 부정·경계 계약."""

    def test_rejects_missing_acceptance_criteria(self):
        _write_sdlc_v2_docs(
            self.task_path,
            task_body="""---
template: sdlc-v2
---
# TASK: Missing AC

## Problem
문제
## Proposed outcome
목표
## Affected users and systems
대상
## Constraints
- C-1: 제약
## Acceptance criteria
""",
        )

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 17, f"기대 exit 17, 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_input_invalid")
        self.assertIn("Acceptance criteria", str(data.get("detail")))

    def test_rejects_missing_risks_section(self):
        _write_sdlc_v2_docs(
            self.task_path,
            plan_body="""---
template: sdlc-v2
---
# PLAN: Missing Risks

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. Builder 구현 | opal-be-agent | `opal/tools/test-tool/lib/scenario.py` | build 추가 | 없음 | P1 | AC-1, C-1 |
""",
        )

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 17, f"기대 exit 17, 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_input_invalid")
        self.assertIn("PLAN Risks", str(data.get("detail")))

    def test_rejects_unknown_scenario_reference(self):
        _write_sdlc_v2_docs(
            self.task_path,
            scenario_body="""---
template: sdlc-v2
---
# TEST-SCENARIO: Unknown ref

## Setup
- 환경: 임시 태스크 폴더

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-999, C-1, H-1 | 정상 문서 | build 실행 | 실패 | CLI | 구현 전 RED |
""",
        )

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 17, f"기대 exit 17, 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_input_invalid")
        self.assertIn("unknown reference", str(data.get("detail")))
        self.assertIn("AC-999", str(data.get("detail")))

    def test_rejects_duplicate_scenario_id(self):
        _write_sdlc_v2_docs(
            self.task_path,
            scenario_body="""---
template: sdlc-v2
---
# TEST-SCENARIO: Duplicate scenario id

## Setup
- 환경: 임시 태스크 폴더

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-13 | AC-1, C-1, H-1 | 정상 문서 | build 실행 | 첫 번째 행 | CLI | 구현 전 RED |
| S-13 | AC-2, C-2, H-2 | 정상 문서 | build 실행 | 중복 행은 거부 | CLI | 구현 전 RED |
""",
        )

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 17, f"기대 exit 17, 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_input_invalid")
        self.assertIn("duplicate scenario id", str(data.get("detail")))
        self.assertIn("S-13", str(data.get("detail")))

    def test_rejects_zero_scenarios(self):
        _write_sdlc_v2_docs(
            self.task_path,
            scenario_body="""---
template: sdlc-v2
---
# TEST-SCENARIO: Zero scenarios

## Setup
- 환경: 임시 태스크 폴더

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
""",
        )

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 17, f"기대 exit 17, 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_input_invalid")
        self.assertIn("scenario", str(data.get("detail")).lower())


# ─────────────────────────────────────────────────────────────────────────────
# [T125] E2E verdict/scenario v2 public CLI contract — S-5, S-7, S-8
# ─────────────────────────────────────────────────────────────────────────────

def _write_json_fixture(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _scenario_mark_verdict(task_path, scenario_id, verdict_path):
    return _run([
        "scenario-mark", "--task-path", str(task_path), "--id", scenario_id,
        "--verdict-json", str(verdict_path),
    ])


def _scenario_resume(task_path, scenario_id, run_id, token, submission_path):
    return _run([
        "scenario-mark", "--task-path", str(task_path), "--id", scenario_id,
        "--resume-run-id", run_id, "--resume-token", token,
        "--submission", str(submission_path),
    ])


def _v2_browser_scenario(red_required=False):
    return {
        "id": "S1",
        "acceptance_ref": "AC-5",
        "type": "e2e",
        "expected": "Dashboard heading is visible",
        "red_required": red_required,
        "required_fidelity": "real-usage",
        "surface_ref": "dashboard",
        "surface_kind": "web_ui",
        "profile": "browser",
        "actors": ["user"],
        "steps": [{"id": "open-dashboard", "executor": "browser"}],
        "assertions": [{"id": "heading", "expected": "Dashboard"}],
        "required_evidence": ["screenshot", "trace"],
        "handoff": None,
    }


def _v2_human_scenario(red_required=False):
    return {
        "id": "S1",
        "acceptance_ref": "AC-7",
        "type": "e2e",
        "expected": "Human approval is deterministically verified",
        "red_required": red_required,
        "required_fidelity": "real-usage",
        "surface_ref": "approval",
        "surface_kind": "collaborative",
        "profile": "collaborative",
        "actors": ["human", "agent"],
        "steps": [{"id": "approve", "executor": "human"}],
        "assertions": [{"id": "approved", "expected": True}],
        "required_evidence": ["approval_record"],
        "handoff": {
            "handoff_id": "handoff-7",
            "instruction": "Approve the observed result",
            "expected_observation": "approval is recorded",
            "required_evidence": ["approval_record"],
            "timeout_seconds": 300,
            "resume_token": "resume-7",
            "server_policy": "keep",
            "submission_path": "submission.json",
        },
    }


def _v2_manual_scenario(red_required=False):
    scenario = json.loads(json.dumps(_v2_human_scenario(red_required)))
    scenario.update({
        "surface_ref": "manual-approval",
        "surface_kind": "manual",
        "profile": "manual",
        "actors": ["human"],
    })
    scenario["handoff"]["handoff_id"] = "handoff-manual"
    scenario["handoff"]["resume_token"] = "resume-manual"
    return scenario


class TestScenarioV2PassGate(BaseScenarioTestCase):
    """[T125/S-5] scenario-mark cannot persist pass/real-usage without verdict evidence."""

    def setUp(self):
        super().setUp()
        code, stdout, data = _scenario_init(self.task_path, [_v2_browser_scenario()])
        self.assertEqual(code, 0, stdout)
        lock_code, lock_stdout, _ = _scenario_lock(self.task_path)
        self.assertEqual(lock_code, 0, lock_stdout)

    def test_legacy_pass_real_usage_without_structured_verdict_is_rejected(self):
        code, stdout, data = _run([
            "scenario-mark", "--task-path", str(self.task_path), "--id", "S1",
            "--result", "pass", "--fidelity", "real-usage", "--evidence", "done",
        ])
        self.assertNotEqual(code, 0, stdout)
        self.assertFalse(data.get("ok"), data)
        spec = json.loads((self.task_path / "test-scenario.json").read_text(encoding="utf-8"))
        self.assertNotEqual(spec["scenarios"][0].get("result"), "pass", spec)

    def test_structured_assertion_and_evidence_verdict_is_the_only_pass_path(self):
        verdict_path = _write_json_fixture(self.tmpdir / "verdict.json", {
            "status": "pass",
            "profile": "browser",
            "fidelity": "real-usage",
            "observed_executors": ["browser"],
            "assertion_results": [
                {"id": "heading", "expected": "Dashboard", "actual": "Dashboard"}
            ],
            "observed_evidence": ["screenshot", "trace"],
        })
        code, stdout, data = _scenario_mark_verdict(self.task_path, "S1", verdict_path)
        self.assertEqual(code, 0, stdout)
        self.assertTrue(data.get("ok"), data)
        self.assertEqual(data.get("status"), "pass", data)
        spec = json.loads((self.task_path / "test-scenario.json").read_text(encoding="utf-8"))
        scenario = spec["scenarios"][0]
        self.assertEqual(scenario.get("result"), "pass")
        self.assertEqual(scenario.get("fidelity"), "real-usage")
        self.assertEqual(scenario.get("observed_executors"), ["browser"])
        self.assertEqual(scenario.get("observed_evidence"), ["screenshot", "trace"])


class TestScenarioV2StatusExitMapping(BaseScenarioTestCase):
    """[T125/S-2] public scenario verdict path preserves all status exit mappings."""

    def test_public_cli_status_to_exit_mapping(self):
        exits = {
            "pass": 0,
            "fail": 6,
            "infra_error": 7,
            "executor_unavailable": 18,
            "blocked": 19,
            "awaiting_human": 20,
        }
        for index, (status, expected_exit) in enumerate(exits.items()):
            with self.subTest(status=status):
                task_path = self.tmpdir / f"status-{index}"
                task_path.mkdir()
                init_code, init_stdout, _ = _scenario_init(task_path, [_v2_human_scenario()])
                self.assertEqual(init_code, 0, init_stdout)
                lock_code, lock_stdout, _ = _scenario_lock(task_path)
                self.assertEqual(lock_code, 0, lock_stdout)
                verdict = {
                    "status": status,
                    "profile": "collaborative",
                    "observed_executors": ["human"],
                    "assertion_results": [
                        {"id": "approved", "expected": True, "actual": True}
                    ],
                    "observed_evidence": ["approval_record"],
                }
                if status == "awaiting_human":
                    verdict.update({
                        "operational_status": "awaiting_human",
                        "run_id": f"run-{index}",
                        "handoff_state": {
                            "handoff_id": "handoff-7",
                            "resume_token": "resume-7",
                            "expected_observation": "approval is recorded",
                            "required_evidence": ["approval_record"],
                        },
                    })
                verdict_path = _write_json_fixture(
                    self.tmpdir / f"status-{index}.json", verdict,
                )
                code, stdout, data = _scenario_mark_verdict(task_path, "S1", verdict_path)
                self.assertEqual(code, expected_exit, stdout)
                self.assertEqual(data.get("status"), status, data)
                self.assertNotIn("awaiting_human", data.get("final_statuses", []), data)


class TestScenarioHumanHandoffResume(BaseScenarioTestCase):
    """[T125/S-7] awaiting_human is resumable; only verified structured submission finalizes."""

    def setUp(self):
        super().setUp()
        code, stdout, _ = _scenario_init(self.task_path, [_v2_human_scenario()])
        self.assertEqual(code, 0, stdout)
        lock_code, lock_stdout, _ = _scenario_lock(self.task_path)
        self.assertEqual(lock_code, 0, lock_stdout)
        self.awaiting_path = _write_json_fixture(self.tmpdir / "awaiting.json", {
            "status": "awaiting_human",
            "operational_status": "awaiting_human",
            "run_id": "run-7",
            "profile": "collaborative",
            "handoff_state": {
                "handoff_id": "handoff-7",
                "resume_token": "resume-7",
                "expected_observation": "approval is recorded",
                "required_evidence": ["approval_record"],
            },
        })

    def _mark_awaiting(self):
        code, stdout, data = _scenario_mark_verdict(self.task_path, "S1", self.awaiting_path)
        self.assertEqual(code, 20, stdout)
        self.assertEqual(data.get("status"), "awaiting_human", data)

    def test_initial_handoff_exits_20_and_free_form_done_is_not_pass(self):
        self._mark_awaiting()
        code, stdout, data = _run([
            "scenario-mark", "--task-path", str(self.task_path), "--id", "S1",
            "--result", "pass", "--evidence", "done",
        ])
        self.assertNotEqual(code, 0, stdout)
        self.assertFalse(data.get("ok"), data)
        spec = json.loads((self.task_path / "test-scenario.json").read_text(encoding="utf-8"))
        scenario = spec["scenarios"][0]
        self.assertEqual(scenario.get("operational_status"), "awaiting_human")
        self.assertNotEqual(scenario.get("result"), "pass")

    def test_matching_run_token_and_structured_evidence_resume_to_final_pass(self):
        self._mark_awaiting()
        submission = _write_json_fixture(self.tmpdir / "submission.json", {
            "run_id": "run-7",
            "resume_token": "resume-7",
            "assertion_results": [
                {"id": "approved", "expected": True, "actual": True}
            ],
            "observed_executors": ["human"],
            "observed_evidence": ["approval_record"],
        })
        code, stdout, data = _scenario_resume(
            self.task_path, "S1", "run-7", "resume-7", submission,
        )
        self.assertEqual(code, 0, stdout)
        self.assertEqual(data.get("status"), "pass", data)
        spec = json.loads((self.task_path / "test-scenario.json").read_text(encoding="utf-8"))
        scenario = spec["scenarios"][0]
        self.assertEqual(scenario.get("result"), "pass")
        self.assertIsNone(scenario.get("operational_status"))

    def test_mismatched_resume_token_is_rejected(self):
        self._mark_awaiting()
        submission = _write_json_fixture(self.tmpdir / "bad-submission.json", {
            "run_id": "run-7",
            "resume_token": "wrong-token",
            "assertion_results": [{"id": "approved", "expected": True, "actual": True}],
            "observed_executors": ["human"],
            "observed_evidence": ["approval_record"],
        })
        code, stdout, data = _scenario_resume(
            self.task_path, "S1", "run-7", "wrong-token", submission,
        )
        self.assertNotEqual(code, 0, stdout)
        self.assertFalse(data.get("ok"), data)
        self.assertNotEqual(data.get("status"), "pass", data)


class TestScenarioV1V2Boundary(BaseScenarioTestCase):
    """[T125/S-8] legacy v1 read compatibility and strict v2 schema/runtime validation."""

    def test_new_init_writes_v2_structured_spec_while_v1_status_still_reads(self):
        code, stdout, _ = _scenario_init(self.task_path, [_v2_browser_scenario()])
        self.assertEqual(code, 0, stdout)
        v2 = json.loads((self.task_path / "test-scenario.json").read_text(encoding="utf-8"))
        self.assertEqual(v2.get("schema_version"), "2.0", v2)
        scenario = v2["scenarios"][0]
        for key in (
            "surface_kind", "profile", "actors", "steps", "assertions", "required_evidence",
            "operational_status", "observed_executors", "assertion_results",
            "observed_evidence", "handoff_state",
        ):
            self.assertIn(key, scenario, v2)

        legacy_path = self.tmpdir / "legacy-task"
        legacy_path.mkdir()
        legacy = {
            "schema_version": "1.0",
            "task_id": "legacy-task",
            "locked": True,
            "created_at": "2026-09-12T00:00:00+09:00",
            "locked_at": "2026-09-12T00:01:00+09:00",
            "scenarios": [{
                "id": "S1", "acceptance_ref": "AC1", "type": "unit",
                "expected": "legacy", "red_confirmed": True,
                "red_evidence": "old red", "red_at": "2026-09-12T00:00:30+09:00",
                "result": "pass", "evidence": "old pass",
                "marked_at": "2026-09-12T00:02:00+09:00",
            }],
        }
        _write_json_fixture(legacy_path / "test-scenario.json", legacy)
        status_code, status_stdout, status = _scenario_status(legacy_path)
        self.assertEqual(status_code, 0, status_stdout)
        self.assertEqual(status.get("passed"), 1)

    def test_schema_accepts_valid_v2_and_schema_and_runtime_reject_invalid_v2(self):
        from jsonschema import Draft7Validator

        schema_path = _TOOL_DIR / "schema" / "test-scenario.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        code, stdout, _ = _scenario_init(self.task_path, [_v2_browser_scenario()])
        self.assertEqual(code, 0, stdout)
        valid_v2 = json.loads((self.task_path / "test-scenario.json").read_text(encoding="utf-8"))
        Draft7Validator(schema).validate(valid_v2)

        invalid_v2 = json.loads(json.dumps(valid_v2))
        invalid_v2["scenarios"][0]["profile"] = "desktop"
        self.assertTrue(list(Draft7Validator(schema).iter_errors(invalid_v2)))
        _write_json_fixture(self.task_path / "test-scenario.json", invalid_v2)
        status_code, status_stdout, status = _scenario_status(self.task_path)
        self.assertNotEqual(status_code, 0, status_stdout)
        self.assertFalse(status.get("ok"), status)
        self.assertEqual(status.get("error"), "scenario_contract_invalid", status)


class TestScenarioHandoffSchemaCorrection(BaseScenarioTestCase):
    """[T125/S-7] Draft7 requires the complete eight-field human handoff shape."""

    REQUIRED_HANDOFF_FIELDS = (
        "handoff_id",
        "instruction",
        "expected_observation",
        "required_evidence",
        "timeout_seconds",
        "resume_token",
        "server_policy",
        "submission_path",
    )

    def test_collaborative_and_manual_handoff_and_state_require_all_fields(self):
        from jsonschema import Draft7Validator

        schema_path = _TOOL_DIR / "schema" / "test-scenario.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = Draft7Validator(schema)

        for profile, scenario_factory in (
            ("collaborative", _v2_human_scenario),
            ("manual", _v2_manual_scenario),
        ):
            with self.subTest(profile=profile, phase="valid"):
                task_path = self.tmpdir / f"schema-{profile}"
                task_path.mkdir()
                code, stdout, _ = _scenario_init(task_path, [scenario_factory()])
                self.assertEqual(code, 0, stdout)
                valid = json.loads((task_path / "test-scenario.json").read_text(encoding="utf-8"))
                item = valid["scenarios"][0]
                item["handoff_state"] = dict(item["handoff"])
                item["operational_status"] = "awaiting_human"
                validator.validate(valid)

            for container in ("handoff", "handoff_state"):
                for field in self.REQUIRED_HANDOFF_FIELDS:
                    with self.subTest(profile=profile, container=container, missing=field):
                        invalid = json.loads(json.dumps(valid))
                        invalid["scenarios"][0][container].pop(field)
                        errors = list(validator.iter_errors(invalid))
                        self.assertTrue(
                            errors,
                            f"Draft7 must reject {profile} {container} without {field}",
                        )


class TestScenarioRuntimeValidationCorrection(BaseScenarioTestCase):
    """[T125/S-8] scenario-status rejects malformed v2 root/result state via exit 17."""

    def _new_v2_task(self, name, scenario=None):
        task_path = self.tmpdir / name
        task_path.mkdir()
        code, stdout, _ = _scenario_init(task_path, [scenario or _v2_browser_scenario()])
        self.assertEqual(code, 0, stdout)
        return task_path

    def _load_spec(self, task_path):
        return json.loads((task_path / "test-scenario.json").read_text(encoding="utf-8"))

    def _save_spec(self, task_path, spec):
        _write_json_fixture(task_path / "test-scenario.json", spec)

    def _assert_status_contract_invalid(self, task_path, label):
        code, stdout, data = _scenario_status(task_path)
        self.assertEqual(
            code,
            17,
            f"{label}: expected exit 17 scenario_contract_invalid, stdout={stdout!r}",
        )
        self.assertFalse(data.get("ok"), data)
        self.assertEqual(data.get("error"), "scenario_contract_invalid", data)

    def test_status_rejects_invalid_v2_enums_and_executor_values(self):
        invalid_values = (
            ("type", "static"),
            ("required_fidelity", "synthetic"),
            ("result", "success"),
            ("operational_status", "paused"),
            ("observed_executors", ["shell"]),
        )
        for index, (field, value) in enumerate(invalid_values):
            with self.subTest(field=field, value=value):
                task_path = self._new_v2_task(f"invalid-{index}")
                spec = self._load_spec(task_path)
                spec["scenarios"][0][field] = value
                self._save_spec(task_path, spec)
                self._assert_status_contract_invalid(task_path, field)

    def test_status_rejects_result_and_awaiting_human_collision(self):
        task_path = self._new_v2_task("state-collision", _v2_human_scenario())
        spec = self._load_spec(task_path)
        item = spec["scenarios"][0]
        item["result"] = "pass"
        item["operational_status"] = "awaiting_human"
        item["handoff_state"] = dict(item["handoff"])
        item["run_id"] = "run-collision"
        self._save_spec(task_path, spec)
        self._assert_status_contract_invalid(task_path, "result+awaiting_human")

    def test_status_rejects_missing_v2_root_required_key(self):
        task_path = self._new_v2_task("missing-root-key")
        spec = self._load_spec(task_path)
        spec.pop("task_id")
        self._save_spec(task_path, spec)
        self._assert_status_contract_invalid(task_path, "missing root task_id")


class TestScenarioStatusCountsCorrection(BaseScenarioTestCase):
    """[T125/S-2] scenario-status preserves every final and operational state."""

    def test_status_counts_preserve_final_five_and_awaiting_human(self):
        final_statuses = ("pass", "fail", "executor_unavailable", "infra_error", "blocked")
        scenarios = []
        for index, status in enumerate(final_statuses, start=1):
            scenario = json.loads(json.dumps(_v2_browser_scenario()))
            scenario["id"] = f"S{index}"
            scenarios.append(scenario)
        awaiting = _v2_human_scenario()
        awaiting["id"] = "S6"
        scenarios.append(awaiting)

        code, stdout, _ = _scenario_init(self.task_path, scenarios)
        self.assertEqual(code, 0, stdout)
        spec = self._load_status_spec()
        for item, status in zip(spec["scenarios"][:5], final_statuses):
            item["result"] = status
            item["operational_status"] = None
            item["observed_executors"] = ["browser"]
            item["assertion_results"] = [
                {"id": "heading", "expected": "Dashboard", "actual": "Dashboard"}
            ]
            item["observed_evidence"] = ["screenshot", "trace"]
        waiting_item = spec["scenarios"][5]
        waiting_item["result"] = None
        waiting_item["operational_status"] = "awaiting_human"
        waiting_item["observed_executors"] = ["human"]
        waiting_item["handoff_state"] = dict(waiting_item["handoff"])
        waiting_item["run_id"] = "run-status-counts"
        _write_json_fixture(self.task_path / "test-scenario.json", spec)

        code, stdout, data = _scenario_status(self.task_path)
        self.assertEqual(code, 0, stdout)
        self.assertEqual(data.get("passed"), 1, data)
        self.assertEqual(data.get("failed"), 1, data)
        self.assertEqual(data.get("blocked"), 1, data)
        self.assertEqual(data.get("awaiting_human"), 1, data)
        self.assertEqual(
            data.get("status_counts"),
            {
                "pass": 1,
                "fail": 1,
                "executor_unavailable": 1,
                "infra_error": 1,
                "blocked": 1,
                "awaiting_human": 1,
            },
            data,
        )

    def _load_status_spec(self):
        return json.loads((self.task_path / "test-scenario.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
