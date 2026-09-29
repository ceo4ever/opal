"""
@header {
  "module": "test_scenario",
  "task": "056,069,073,111,125,151",
  "layer": "test",
  "domain": "opal-tools",
  "description": "test-tool scenario-* public CLI regression tests for RED locking, coverage, escape-aware Markdown table parsing, malformed-row rejection, fidelity, conformance, E2E v2 schema/runtime validation, status preservation, and human handoff/resume.",
  "scenarios": ["S-011", "S-012", "S-007", "S-014", "T069/S-5", "T069/S-6", "T069/S-7", "T073/S-1", "T073/S-2", "T111/S-6", "T111/S-7", "T111/S-8", "T111/S-9", "T111/S-10", "T111/S-11", "T111/S-18", "T125/S-2", "T125/S-5", "T125/S-7", "T125/S-8", "T151/S-1", "T151/S-2"],
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

    def test_preserves_scenario_row_with_escaped_pipe(self):
        """[T151/S-1] 셀 안의 Markdown escape 파이프는 행 구분자가 아니다."""
        _write_sdlc_v2_docs(
            self.task_path,
            scenario_body="""---
template: sdlc-v2
---
# TEST-SCENARIO: Escaped pipe

## Setup
- 환경: 임시 태스크 폴더

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1, H-1 | grep 체인 | `grep a \\| grep b` 실행 | 행 보존 | CLI | 구현 전 RED, 구현 후 |
| S-2 | AC-2, C-2, H-2 | 정상 문서 | build 실행 | 커버 유지 | CLI | 구현 전 RED, 구현 후 |
""",
        )

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 0, f"기대 exit 0, 실제 stdout={stdout!r}")
        output_path = pathlib.Path(data.get("coverage_input"))
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(
            [scenario.get("id") for scenario in payload.get("scenarios", [])],
            ["S-1", "S-2"],
        )
        self.assertEqual(payload["scenarios"][0]["covers_requirements"], ["AC-1", "C-1"])
        self.assertEqual(payload["scenarios"][0]["covers_hypotheses"], ["H-1"])

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

    def test_rejects_malformed_scenario_table_row_instead_of_dropping_it(self):
        """[T151/S-2] 열 수가 다른 S 행은 조용히 유실되지 않고 입력 오류가 된다."""
        _write_sdlc_v2_docs(
            self.task_path,
            scenario_body="""---
template: sdlc-v2
---
# TEST-SCENARIO: Malformed row

## Setup
- 환경: 임시 태스크 폴더

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1 | 열 수 부족 |
| S-2 | AC-1, AC-2, C-1, C-2, H-1, H-2 | 정상 문서 | build 실행 | 커버 유지 | CLI | 구현 전 RED, 구현 후 |
""",
        )

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 17, f"기대 exit 17, 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_input_invalid")
        self.assertIn("S-1", str(data.get("detail")))

    def test_rejects_malformed_row_without_trailing_pipe(self):
        """[T151/S-2] 후미 테두리 파이프가 없는 불완전 S 행도 입력 오류가 된다."""
        _write_sdlc_v2_docs(
            self.task_path,
            scenario_body="""---
template: sdlc-v2
---
# TEST-SCENARIO: Missing trailing border

## Setup
- 환경: 임시 태스크 폴더

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1 | 열 수 부족
| S-2 | AC-1, AC-2, C-1, C-2, H-1, H-2 | 정상 문서 | build 실행 | 커버 유지 | CLI | 구현 전 RED, 구현 후 |
""",
        )

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 17, f"기대 exit 17, 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_input_invalid")
        self.assertIn("S-1", str(data.get("detail")))

    def test_rejects_malformed_row_without_leading_pipe(self):
        """[T151/S-2] 선두 테두리 파이프가 없는 불완전 S 행도 입력 오류가 된다."""
        _write_sdlc_v2_docs(
            self.task_path,
            scenario_body="""---
template: sdlc-v2
---
# TEST-SCENARIO: Missing leading border

## Setup
- 환경: 임시 태스크 폴더

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
S-1 | AC-1 | 열 수 부족 |
| S-2 | AC-1, AC-2, C-1, C-2, H-1, H-2 | 정상 문서 | build 실행 | 커버 유지 | CLI | 구현 전 RED, 구현 후 |
""",
        )

        code, stdout, data = _scenario_coverage_build(self.task_path)

        self.assertEqual(code, 17, f"기대 exit 17, 실제 stdout={stdout!r}")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "coverage_input_invalid")
        self.assertIn("S-1", str(data.get("detail")))

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


# ─────────────────────────────────────────────────────────────────────────────
# [T167] S-2/S-4/S-6: 유형 열 전환·check+RED 모순·정확 중복·목표-커버 advisory 기록
# RED-first — 태스크 167 PLAN.md Decisions and contracts SSOT
# ─────────────────────────────────────────────────────────────────────────────

_T167_TYPE_VALUES = ("unit", "integration", "contract", "regression", "e2e", "check")


def _t167_type_table(rows):
    """rows: [(id, 유형, 검증대상, 조건, 행동, 기대결과, 방법환경, 시점), ...]"""
    header = "| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |"
    sep = "|---|---|---|---|---|---|---|---|"
    lines = [header, sep]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _t167_scenario_body(rows):
    return f"""---
template: sdlc-v2
---
# TEST-SCENARIO: T167 유형 열 fixture

## Setup

- 환경: 임시 태스크 폴더

## Scenarios

{_t167_type_table(rows)}
"""


class TestS167_S2TypeColumn(BaseScenarioTestCase):
    """[T167/S-2] 유형 열 선언값이 builder payload·test-scenario.json에 그대로 전달된다 (AC-2).
    현재 builder는 `유형` 헤더를 해석하지 않고 scenario-init의 `type` 검증에는 `check`가
    허용값에 없다 — 두 계약 모두 미구현이라 RED다."""

    def test_normal_six_types_propagate_to_payload_and_spec(self):
        """① payload scenarios[].type이 행별 선언값과 같다. ② 생성된 test-scenario.json의
        type도 같다(check 포함)."""
        rows = [
            (f"S-{i}", t, "AC-1, C-1, H-1", f"조건{i}", f"행동{i}", f"기대{i}", "CLI", "구현 후")
            for i, t in enumerate(_T167_TYPE_VALUES, start=1)
        ]
        _write_sdlc_v2_docs(self.task_path, scenario_body=_t167_scenario_body(rows))

        code, stdout, data = _scenario_coverage_build(self.task_path)
        self.assertEqual(code, 0, f"기대 exit 0, 실제 stdout={stdout!r}")
        output_path = pathlib.Path(data.get("coverage_input"))
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        got_types = [s.get("type") for s in payload.get("scenarios", [])]
        self.assertEqual(
            got_types, list(_T167_TYPE_VALUES),
            "① payload scenarios[].type이 유형 열 선언값과 같아야 한다",
        )

        init_scenarios = [
            {
                "id": f"S-{i}", "acceptance_ref": "AC-1", "type": t,
                "expected": f"기대{i}", "red_required": False,
            }
            for i, t in enumerate(_T167_TYPE_VALUES, start=1)
        ]
        code2, stdout2, _data2 = _scenario_init(self.task_path, init_scenarios)
        self.assertEqual(code2, 0, f"scenario-init 기대 exit 0, 실제 stdout={stdout2!r}")
        spec = json.loads((self.task_path / "test-scenario.json").read_text(encoding="utf-8"))
        spec_types = [s.get("type") for s in spec.get("scenarios", [])]
        self.assertEqual(
            spec_types, list(_T167_TYPE_VALUES),
            "② test-scenario.json의 type도 선언값과 같아야 한다(check 포함)",
        )

    def test_blank_type_rejected_with_sid_in_detail(self):
        """③ 빈 유형은 exit 17 coverage_input_invalid이고 detail에 해당 S-ID가 있다."""
        rows = [
            ("S-1", "", "AC-1, C-1, H-1", "조건", "행동", "기대", "CLI", "구현 후"),
        ]
        _write_sdlc_v2_docs(self.task_path, scenario_body=_t167_scenario_body(rows))
        code, stdout, data = _scenario_coverage_build(self.task_path)
        self.assertEqual(code, 17, f"빈 유형은 exit 17이어야 한다, 실제 stdout={stdout!r}")
        self.assertEqual(data.get("error"), "coverage_input_invalid")
        self.assertIn("S-1", str(data.get("detail")), "detail에 S-1이 있어야 한다")

    def test_unknown_type_value_rejected_with_sid_in_detail(self):
        """③ 허용 6값 밖(smoke)은 exit 17 coverage_input_invalid이고 detail에 해당 S-ID가 있다."""
        rows = [
            ("S-1", "smoke", "AC-1, C-1, H-1", "조건", "행동", "기대", "CLI", "구현 후"),
        ]
        _write_sdlc_v2_docs(self.task_path, scenario_body=_t167_scenario_body(rows))
        code, stdout, data = _scenario_coverage_build(self.task_path)
        self.assertEqual(code, 17, f"smoke는 exit 17이어야 한다, 실제 stdout={stdout!r}")
        self.assertEqual(data.get("error"), "coverage_input_invalid")
        self.assertIn("S-1", str(data.get("detail")), "detail에 S-1이 있어야 한다")


class TestS167_S4CheckRedContradiction(BaseScenarioTestCase):
    """[T167/S-4] check 유형과 구현 전 RED 모순, 정확 중복(6셀 동일) 거부 (AC-3).
    현재 builder는 유형 열 검증도 6셀 중복 검증도 하지 않고, scenario-init은 `check`를
    허용값 밖으로 취급한다 — 둘 다 미구현이라 RED다."""

    def _fresh_task(self, suffix):
        path = self.tmpdir / f"056-dryrun-{suffix}"
        path.mkdir()
        return path

    def test_check_type_with_pre_red_timing_rejected_by_builder(self):
        """(a) check 행의 시점이 `구현 전 RED`이면 builder가 exit 17이고 detail에 S-ID가 있다."""
        rows = [
            ("S-1", "check", "AC-1, C-1, H-1", "조건", "행동", "기대", "CLI", "구현 전 RED"),
        ]
        _write_sdlc_v2_docs(self.task_path, scenario_body=_t167_scenario_body(rows))
        code, stdout, data = _scenario_coverage_build(self.task_path)
        self.assertEqual(code, 17, f"check+구현 전 RED는 exit 17이어야 한다, 실제 stdout={stdout!r}")
        self.assertIn("S-1", str(data.get("detail")), "detail에 S-1이 있어야 한다")

    def test_identical_six_cells_duplicate_rejected_by_builder(self):
        """(b) 여섯 셀이 모두 같은 두 행은 exit 17(duplicate scenario content)이고
        detail에 두 S-ID가 있다."""
        rows = [
            ("S-1", "unit", "AC-1, C-1, H-1", "같은 조건", "같은 행동", "같은 기대", "CLI", "구현 후"),
            ("S-2", "unit", "AC-1, C-1, H-1", "같은 조건", "같은 행동", "같은 기대", "CLI", "구현 후"),
        ]
        _write_sdlc_v2_docs(self.task_path, scenario_body=_t167_scenario_body(rows))
        code, stdout, data = _scenario_coverage_build(self.task_path)
        self.assertEqual(code, 17, f"6셀 동일 중복은 exit 17이어야 한다, 실제 stdout={stdout!r}")
        detail = str(data.get("detail"))
        self.assertIn("S-1", detail)
        self.assertIn("S-2", detail)

    def test_expected_only_difference_passes(self):
        """(c) 기대 결과만 다른 두 행은 exit 0이다(정확 중복 아님)."""
        rows = [
            ("S-1", "unit", "AC-1, C-1, H-1", "같은 조건", "같은 행동", "기대A", "CLI", "구현 후"),
            ("S-2", "unit", "AC-1, C-1, H-1", "같은 조건", "같은 행동", "기대B", "CLI", "구현 후"),
        ]
        _write_sdlc_v2_docs(self.task_path, scenario_body=_t167_scenario_body(rows))
        code, stdout, _data = _scenario_coverage_build(self.task_path)
        self.assertEqual(code, 0, f"기대 결과만 다르면 exit 0이어야 한다, 실제 stdout={stdout!r}")

    def test_scenario_init_check_red_required_contradiction(self):
        """init `type=check`+`red_required=true`, `type=check`+`red_required` 없음은
        scenario_contract_invalid exit 17이고 test-scenario.json이 생기지 않는다.
        `type=check`+`red_required=false`는 성공한다."""
        task_a = self._fresh_task("a")
        code_a, stdout_a, data_a = _scenario_init(task_a, [
            {"id": "S-1", "acceptance_ref": "AC-1", "type": "check", "expected": "x", "red_required": True},
        ])
        self.assertEqual(code_a, 17, f"check+red_required=true는 exit 17이어야 한다, 실제={stdout_a!r}")
        self.assertEqual(data_a.get("error"), "scenario_contract_invalid")
        self.assertIn(
            "red_required", str(data_a.get("detail")).lower() + str(data_a.get("error")),
            "detail 또는 error가 check+red_required 모순을 가리켜야 한다",
        )
        self.assertFalse((task_a / "test-scenario.json").exists())

        task_b = self._fresh_task("b")
        code_b, stdout_b, data_b = _scenario_init(task_b, [
            {"id": "S-1", "acceptance_ref": "AC-1", "type": "check", "expected": "x"},
        ])
        self.assertEqual(code_b, 17, f"check+red_required 미지정(기본 true)은 exit 17이어야 한다, 실제={stdout_b!r}")
        self.assertEqual(data_b.get("error"), "scenario_contract_invalid")
        self.assertFalse((task_b / "test-scenario.json").exists())

        task_c = self._fresh_task("c")
        code_c, stdout_c, _data_c = _scenario_init(task_c, [
            {"id": "S-1", "acceptance_ref": "AC-1", "type": "check", "expected": "x", "red_required": False},
        ])
        self.assertEqual(code_c, 0, f"check+red_required=false는 성공해야 한다, 실제={stdout_c!r}")
        self.assertTrue((task_c / "test-scenario.json").exists())


def _t167_scenario_gate_record(task_path, iteration, **kwargs):
    args = ["scenario-gate-record", "--task-folder", str(task_path), "--iteration", str(iteration)]
    for flag, value in kwargs.items():
        if value is None:
            continue
        args += [f"--{flag.replace('_', '-')}", str(value)]
    return _run(args)


def _t167_scenario_gate_verify(task_path, **kwargs):
    args = ["scenario-gate-verify", "--task-folder", str(task_path)]
    for flag, value in kwargs.items():
        if value is None:
            continue
        args += [f"--{flag.replace('_', '-')}", str(value)]
    return _run(args)


def _t167_write_evaluator_result(task_path, name, *, verdict="pass", advisories=None):
    payload = {
        "scores": {"goal": 2, "adoption": 2, "boundary": 2},
        "average": 2.0,
        "gaps": [],
        "verdict": verdict,
        "advisories": advisories if advisories is not None else [],
    }
    path = task_path / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


_T167_ADVISORY_OK = {
    "id": "A-1", "kind": "mergeable", "targets": ["S-1"],
    "basis": "두 시나리오가 같은 축을 다룬다", "recommendation": "S-2를 S-1에 통합",
}


class TestS167_S6ScenarioGateRecord(BaseScenarioTestCase):
    """[T167/S-6] test-tool scenario-gate-record/scenario-gate-verify — advisory 형식 검사,
    응답 완전성 검사, apply→refinement 전이, --input-error/--evidence-error 모드 (AC-4, AC-5,
    AC-6, C-4, H-2). 두 서브명령이 아직 없어 RED다."""

    def setUp(self):
        super().setUp()
        _write_sdlc_v2_docs(self.task_path)

    def _history(self):
        history_path = self.task_path / ".scenario-gate-history.json"
        if not history_path.exists():
            return None
        return json.loads(history_path.read_text(encoding="utf-8"))

    def test_malformed_advisories_rejected_exit18(self):
        """① advisory 형식 오류는 exit 18(scenario_gate_record_invalid)이다."""
        _t167_write_evaluator_result(
            self.task_path, "eval-i1.json",
            advisories=[{"id": "A-1"}],  # kind/targets/basis/recommendation 누락
        )
        code, stdout, data = _t167_scenario_gate_record(
            self.task_path, 1, evaluator_result=str(self.task_path / "eval-i1.json"),
        )
        self.assertEqual(code, 18, f"advisory 형식 오류는 exit 18이어야 한다, 실제 stdout={stdout!r}")
        self.assertEqual(data.get("error"), "scenario_gate_record_invalid")

    def test_pass_with_incomplete_response_rejected_exit19_history_unchanged(self):
        """② pass에 응답이 불완전하면 exit 19(advisory_response_invalid)이고 이력 파일이
        바이트 단위로 불변이다."""
        _t167_write_evaluator_result(
            self.task_path, "eval-i1.json", verdict="pass", advisories=[_T167_ADVISORY_OK],
        )
        history_path = self.task_path / ".scenario-gate-history.json"
        before = history_path.read_bytes() if history_path.exists() else None

        code, stdout, data = _t167_scenario_gate_record(
            self.task_path, 1,
            evaluator_result=str(self.task_path / "eval-i1.json"),
            advisory_responses=None,  # 응답 없이 호출
        )
        self.assertEqual(code, 19, f"불완전 응답은 exit 19여야 한다, 실제 stdout={stdout!r}")
        self.assertEqual(data.get("error"), "advisory_response_invalid")
        after = history_path.read_bytes() if history_path.exists() else None
        self.assertEqual(before, after, "이력 파일이 바이트 단위로 불변이어야 한다")

    def test_apply_response_records_rewrite_advisory_apply_counted_false(self):
        """③ apply는 verdict: rewrite·reason: advisory_apply·counted: false다. 그 직후
        scenario-gate-verify는 exit 20(not_passed)이다."""
        _t167_write_evaluator_result(
            self.task_path, "eval-i1.json", verdict="pass", advisories=[_T167_ADVISORY_OK],
        )
        responses_path = self.task_path / "i1-responses.json"
        responses_path.write_text(
            json.dumps([{"id": "A-1", "response": "apply", "reason": "통합 채택"}], ensure_ascii=False),
            encoding="utf-8",
        )
        code, stdout, data = _t167_scenario_gate_record(
            self.task_path, 1,
            evaluator_result=str(self.task_path / "eval-i1.json"),
            advisory_responses=str(responses_path),
        )
        self.assertEqual(code, 0, f"완전한 apply 응답은 exit 0이어야 한다, 실제 stdout={stdout!r}")
        self.assertEqual(data.get("verdict"), "rewrite")
        self.assertEqual(data.get("reason"), "advisory_apply")

        history = self._history()
        self.assertIsNotNone(history, "이력 파일이 생성되어야 한다")
        last = history[-1]
        self.assertEqual(last.get("verdict"), "rewrite")
        self.assertEqual(last.get("reason"), "advisory_apply")
        self.assertIs(last.get("counted"), False, "apply 원소는 counted: false여야 한다")

        verify_code, verify_stdout, verify_data = _t167_scenario_gate_verify(self.task_path)
        self.assertEqual(verify_code, 20, f"apply 직후 verify는 exit 20이어야 한다, 실제={verify_stdout!r}")
        self.assertEqual(verify_data.get("error"), "scenario_gate_not_passed")

    def test_refinement_round_pass_converges(self):
        """④ apply 다음 회차(refinement)가 evaluator pass·누락 0이면 verdict: pass·
        reason: converged다. verify는 exit 0이 된다."""
        _t167_write_evaluator_result(
            self.task_path, "eval-i1.json", verdict="pass", advisories=[_T167_ADVISORY_OK],
        )
        responses_path = self.task_path / "i1-responses.json"
        responses_path.write_text(
            json.dumps([{"id": "A-1", "response": "apply", "reason": "통합 채택"}], ensure_ascii=False),
            encoding="utf-8",
        )
        self.assertEqual(
            _t167_scenario_gate_record(
                self.task_path, 1,
                evaluator_result=str(self.task_path / "eval-i1.json"),
                advisory_responses=str(responses_path),
            )[0], 0,
        )

        _t167_write_evaluator_result(self.task_path, "eval-i2.json", verdict="pass", advisories=[])
        code, stdout, data = _t167_scenario_gate_record(
            self.task_path, 2, evaluator_result=str(self.task_path / "eval-i2.json"),
        )
        self.assertEqual(code, 0, f"refinement pass는 exit 0이어야 한다, 실제 stdout={stdout!r}")
        self.assertEqual(data.get("verdict"), "pass")
        self.assertEqual(data.get("reason"), "converged")

        history = self._history()
        self.assertEqual(history[-1].get("verdict"), "pass")
        self.assertEqual(history[-1].get("reason"), "converged")

        verify_code, verify_stdout, _verify_data = _t167_scenario_gate_verify(self.task_path)
        self.assertEqual(verify_code, 0, f"refinement pass 뒤 verify는 exit 0이어야 한다, 실제={verify_stdout!r}")

    def test_refinement_round_fail_escalates_and_ignores_advisories(self):
        """⑤ apply 다음 회차(refinement)가 evaluator rewrite면 verdict: escalate·
        reason: advisory_refinement_failed다. 그 결과의 비어 있지 않은 advisories는
        응답 없이 무시되고 이력에는 advisories: []로 남는다."""
        _t167_write_evaluator_result(
            self.task_path, "eval-i1.json", verdict="pass", advisories=[_T167_ADVISORY_OK],
        )
        responses_path = self.task_path / "i1-responses.json"
        responses_path.write_text(
            json.dumps([{"id": "A-1", "response": "apply", "reason": "통합 채택"}], ensure_ascii=False),
            encoding="utf-8",
        )
        self.assertEqual(
            _t167_scenario_gate_record(
                self.task_path, 1,
                evaluator_result=str(self.task_path / "eval-i1.json"),
                advisory_responses=str(responses_path),
            )[0], 0,
        )

        _t167_write_evaluator_result(
            self.task_path, "eval-i2.json", verdict="rewrite",
            advisories=[_T167_ADVISORY_OK],  # refinement에서는 응답 없이 무시되어야 함
        )
        code, stdout, data = _t167_scenario_gate_record(
            self.task_path, 2, evaluator_result=str(self.task_path / "eval-i2.json"),
        )
        self.assertEqual(code, 0, f"refinement 실패 기록 자체는 exit 0이어야 한다, 실제 stdout={stdout!r}")
        self.assertEqual(data.get("verdict"), "escalate")
        self.assertEqual(data.get("reason"), "advisory_refinement_failed")

        last = self._history()[-1]
        self.assertEqual(last.get("advisories"), [], "refinement 회차의 advisories는 무시되고 []로 기록된다")

    def test_input_error_mode_records_escalate_counted_true(self):
        """⑦(일부) builder exit 17 뒤 --input-error는 evaluator·응답 검사 없이
        verdict: escalate·reason: input_error·counted: true 원소를 남긴다."""
        code, stdout, data = _t167_scenario_gate_record(
            self.task_path, 1, input_error="유형 오값: S-1",
        )
        self.assertEqual(code, 0, f"--input-error 모드는 exit 0이어야 한다, 실제 stdout={stdout!r}")
        self.assertEqual(data.get("verdict"), "escalate")
        self.assertEqual(data.get("reason"), "input_error")

        last = self._history()[-1]
        self.assertEqual(last.get("verdict"), "escalate")
        self.assertEqual(last.get("reason"), "input_error")
        self.assertIs(last.get("counted"), True, "input-error 원소는 counted: true여야 한다")

    def test_evidence_error_mode_appends_field_and_switches_to_escalate(self):
        """⑪ `--evidence-error <code>`는 마지막 원소에 evidence_error를 붙이고
        escalate·input_error로 바꾼다. 회차가 다르면 exit 18이다."""
        _t167_write_evaluator_result(self.task_path, "eval-i1.json", verdict="pass", advisories=[])
        self.assertEqual(
            _t167_scenario_gate_record(
                self.task_path, 1, evaluator_result=str(self.task_path / "eval-i1.json"),
            )[0], 0,
        )
        code, stdout, data = _t167_scenario_gate_record(
            self.task_path, 1, evidence_error="EXECUTE_EVIDENCE_MISSING",
        )
        self.assertEqual(code, 0, f"--evidence-error 모드는 exit 0이어야 한다, 실제 stdout={stdout!r}")
        last = self._history()[-1]
        self.assertEqual(last.get("evidence_error"), "EXECUTE_EVIDENCE_MISSING")
        self.assertEqual(last.get("verdict"), "escalate")
        self.assertEqual(last.get("reason"), "input_error")

        # 회차 불일치는 exit 18
        code2, stdout2, data2 = _t167_scenario_gate_record(
            self.task_path, 99, evidence_error="EXECUTE_EVIDENCE_MISSING",
        )
        self.assertEqual(code2, 18, f"회차 불일치는 exit 18이어야 한다, 실제 stdout={stdout2!r}")

    def test_input_error_and_evidence_error_mutually_exclusive_exit18(self):
        """`--input-error`와 `--evidence-error`를 함께 주면 exit 18이다."""
        code, stdout, data = _t167_scenario_gate_record(
            self.task_path, 1, input_error="x", evidence_error="y",
        )
        self.assertEqual(code, 18, f"두 옵션 동시 지정은 exit 18이어야 한다, 실제 stdout={stdout!r}")

    def test_pass_with_empty_advisories_records_pass_without_response(self):
        """⑩(끝) advisories가 빈 pass 회차는 응답 없이 pass다."""
        _t167_write_evaluator_result(self.task_path, "eval-i1.json", verdict="pass", advisories=[])
        code, stdout, data = _t167_scenario_gate_record(
            self.task_path, 1, evaluator_result=str(self.task_path / "eval-i1.json"),
        )
        self.assertEqual(code, 0, f"advisories가 빈 pass는 exit 0이어야 한다, 실제 stdout={stdout!r}")
        self.assertEqual(data.get("verdict"), "pass")
        self.assertEqual(data.get("reason"), "converged")


def _t167_write_coverage_input(task_path, *, complete):
    """coverage-check 재판정용 `.scenario-coverage-input.json` fixture. complete=False는
    requirements 중 하나가 어떤 scenario에도 커버되지 않아 missing이 발생한다."""
    requirements = ["AC-1"] if complete else ["AC-1", "AC-2"]
    payload = {
        "goal": "T167 목표-커버 기록 명령 회귀",
        "requirements": requirements,
        "features": [],
        "hypotheses": [],
        "scenarios": [
            {
                "id": "S-1",
                "covers_requirements": ["AC-1"],
                "covers_features": [],
                "covers_hypotheses": [],
            },
        ],
    }
    (task_path / ".scenario-coverage-input.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8",
    )


class TestS167_S6ExtraGateRecordCoverage(BaseScenarioTestCase):
    """[T167/S-6 보강] RED 테스트가 다루지 않은 판정 갈래 — 누락 있는 coverage 입력의
    evaluator-없는 rewrite/recoverable, 누락 없는데 evaluator 없으면 exit 18, coverage
    입력 파손 시 escalate/input_error(⑦). retry_limit 3회째·no_progress 연속 무개선(⑧).
    회차 건너뛰기 exit 18(⑨)."""

    def setUp(self):
        super().setUp()
        _write_sdlc_v2_docs(self.task_path)

    def _history(self):
        history_path = self.task_path / ".scenario-gate-history.json"
        if not history_path.exists():
            return None
        return json.loads(history_path.read_text(encoding="utf-8"))

    def test_legacy_history_elements_without_counted_key_are_treated_as_counted_true(self):
        """(STATE.md 결정 로그) `counted` 키가 없는 구형 이력 원소는 counted:true로
        간주한다. 구형 원소 2개가 이미 있는 상태에서 새 회차가 counted 3회째가 되어
        상한(3)에 도달, escalate/retry_limit이어야 한다."""
        legacy_history = [
            {
                "iteration": 1, "missing": {"requirements": ["AC-2"], "features": [], "hypotheses": []},
                "scores": None, "gaps": [], "verdict": "rewrite", "reason": "recoverable",
                "advisories": [], "advisory_responses": [], "refinement": False,
                "bundle_hash": "legacy", "files": [], "at": "2026-01-01T00:00:00+09:00",
                # counted 키 없음 — 구형 원소
            },
            {
                "iteration": 2, "missing": {"requirements": ["AC-2"], "features": [], "hypotheses": []},
                "scores": None, "gaps": [], "verdict": "rewrite", "reason": "recoverable",
                "advisories": [], "advisory_responses": [], "refinement": False,
                "bundle_hash": "legacy", "files": [], "at": "2026-01-01T00:01:00+09:00",
                # counted 키 없음 — 구형 원소
            },
        ]
        (self.task_path / ".scenario-gate-history.json").write_text(
            json.dumps(legacy_history, ensure_ascii=False), encoding="utf-8",
        )
        _t167_write_coverage_input(self.task_path, complete=False)
        code, stdout, data = _t167_scenario_gate_record(self.task_path, 3)
        self.assertEqual(code, 0, f"실제={stdout!r}")
        self.assertEqual(
            data.get("verdict"), "escalate",
            "구형 원소 2개 + 이번 회차 = counted 3회째이므로 escalate여야 한다",
        )
        self.assertEqual(
            data.get("reason"), "retry_limit",
            f"구형 counted 키 부재 원소를 counted:true로 간주해야 retry_limit이 된다: {data!r}",
        )
        last = self._history()[-1]
        self.assertIs(last.get("counted"), True)

    def test_missing_present_without_evaluator_records_rewrite_recoverable(self):
        """⑦ 누락이 있는 coverage 입력에서는 evaluator 결과 없이 rewrite/recoverable이
        기록된다."""
        _t167_write_coverage_input(self.task_path, complete=False)
        code, stdout, data = _t167_scenario_gate_record(self.task_path, 1)
        self.assertEqual(code, 0, f"누락 있는 입력에서 evaluator 없이도 exit 0이어야 한다, 실제={stdout!r}")
        self.assertEqual(data.get("verdict"), "rewrite")
        self.assertEqual(data.get("reason"), "recoverable")
        last = self._history()[-1]
        self.assertIs(last.get("counted"), True)

    def test_missing_absent_without_evaluator_rejected_exit18(self):
        """⑦ 누락이 없는데 evaluator 결과가 없으면 exit 18이다."""
        _t167_write_coverage_input(self.task_path, complete=True)
        code, stdout, data = _t167_scenario_gate_record(self.task_path, 1)
        self.assertEqual(code, 18, f"누락 없고 evaluator 없으면 exit 18이어야 한다, 실제={stdout!r}")
        self.assertEqual(data.get("error"), "scenario_gate_record_invalid")

    def test_broken_coverage_input_without_evaluator_records_escalate_input_error(self):
        """⑦ coverage 입력이 파손되면 evaluator 없이도 escalate/input_error가 기록된다."""
        (self.task_path / ".scenario-coverage-input.json").write_text("{not-valid-json", encoding="utf-8")
        code, stdout, data = _t167_scenario_gate_record(self.task_path, 1)
        self.assertEqual(code, 0, f"파손 입력의 자동 escalate 기록은 exit 0이어야 한다, 실제={stdout!r}")
        self.assertEqual(data.get("verdict"), "escalate")
        self.assertEqual(data.get("reason"), "input_error")
        last = self._history()[-1]
        self.assertIs(last.get("counted"), True)

    def test_no_progress_after_two_unimproved_counted_rounds(self):
        """⑧ 연속 2회 개선 없음(누락 수 그대로·점수 없음=0)은 no_progress다(retry_limit
        상한 3에 도달하기 전, 2번째 counted 원소에서 판정)."""
        _t167_write_coverage_input(self.task_path, complete=False)
        code1, stdout1, data1 = _t167_scenario_gate_record(self.task_path, 1)
        self.assertEqual(code1, 0)
        self.assertEqual(data1.get("reason"), "recoverable")

        code2, stdout2, data2 = _t167_scenario_gate_record(self.task_path, 2)
        self.assertEqual(code2, 0, f"실제={stdout2!r}")
        self.assertEqual(data2.get("verdict"), "escalate")
        self.assertEqual(data2.get("reason"), "no_progress")

    def test_retry_limit_at_third_counted_round_with_progress(self):
        """⑧ `retry_limit`은 counted:true 3회째에만 나온다(개선이 있어도 상한 도달 시
        escalate/retry_limit)."""
        _t167_write_coverage_input(self.task_path, complete=False)
        code1, _stdout1, data1 = _t167_scenario_gate_record(self.task_path, 1)
        self.assertEqual(code1, 0)
        self.assertEqual(data1.get("reason"), "recoverable")

        # 2회차: missing이 1건으로 줄어 개선 있음 → no_progress 아님, recoverable 유지
        payload = json.loads((self.task_path / ".scenario-coverage-input.json").read_text(encoding="utf-8"))
        payload["scenarios"][0]["covers_requirements"] = ["AC-1", "AC-2"]
        (self.task_path / ".scenario-coverage-input.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8",
        )
        # 완전 커버가 되면 missing이 사라져 pass 갈래로 빠지므로, 다시 미커버 유지하되
        # 점수만 붙는 evaluator 결과로 "개선"을 표시한다.
        _t167_write_coverage_input(self.task_path, complete=False)
        _t167_write_evaluator_result(self.task_path, "eval-i2.json", verdict="rewrite", advisories=[])
        code2, stdout2, data2 = _t167_scenario_gate_record(
            self.task_path, 2, evaluator_result=str(self.task_path / "eval-i2.json"),
        )
        self.assertEqual(code2, 0, f"실제={stdout2!r}")
        self.assertEqual(data2.get("reason"), "recoverable", f"점수 개선이 있으면 no_progress가 아니어야 한다: {data2!r}")

        code3, stdout3, data3 = _t167_scenario_gate_record(self.task_path, 3)
        self.assertEqual(code3, 0, f"실제={stdout3!r}")
        self.assertEqual(data3.get("verdict"), "escalate")
        self.assertEqual(data3.get("reason"), "retry_limit")
        last = self._history()[-1]
        self.assertIs(last.get("counted"), True)

    def test_skipping_iteration_rejected_exit18(self):
        """⑨ 회차를 건너뛰면(마지막 iteration+1이 아니면) exit 18이다."""
        _t167_write_coverage_input(self.task_path, complete=False)
        code1, _stdout1, _data1 = _t167_scenario_gate_record(self.task_path, 1)
        self.assertEqual(code1, 0)

        code2, stdout2, data2 = _t167_scenario_gate_record(self.task_path, 3)
        self.assertEqual(code2, 18, f"회차 건너뛰기는 exit 18이어야 한다, 실제={stdout2!r}")
        self.assertEqual(data2.get("error"), "scenario_gate_record_invalid")


class TestS167_S6ExtraBuilderCleanupAndHistoryShape(BaseScenarioTestCase):
    """[T167/S-6 보강] ⑩ builder exit 17 시 이전 `.scenario-coverage-input.json` 삭제.
    ⑫ 이력은 JSON 배열을 유지한다. ⑬ 저장 뒤 임시 파일이 남지 않는다."""

    def test_builder_failure_deletes_stale_coverage_input_then_input_error_records_counted_true(self):
        rows = [("S-1", "unit", "AC-1, C-1, H-1", "조건", "행동", "기대", "CLI", "구현 후")]
        _write_sdlc_v2_docs(self.task_path, scenario_body=_t167_scenario_body(rows))
        build_code, build_stdout, _build_data = _scenario_coverage_build(self.task_path)
        self.assertEqual(build_code, 0, f"정상 문서 build는 exit 0이어야 한다, 실제={build_stdout!r}")
        coverage_input = self.task_path / ".scenario-coverage-input.json"
        self.assertTrue(coverage_input.exists())

        bad_rows = [("S-1", "smoke", "AC-1, C-1, H-1", "조건", "행동", "기대", "CLI", "구현 후")]
        _write_sdlc_v2_docs(self.task_path, scenario_body=_t167_scenario_body(bad_rows))
        fail_code, fail_stdout, _fail_data = _scenario_coverage_build(self.task_path)
        self.assertEqual(fail_code, 17, f"허용 밖 유형은 exit 17이어야 한다, 실제={fail_stdout!r}")
        self.assertFalse(
            coverage_input.exists(),
            "builder exit 17 뒤에는 이전 회차의 .scenario-coverage-input.json이 지워져야 한다",
        )

        code, stdout, data = _t167_scenario_gate_record(
            self.task_path, 1, input_error="유형 오값: S-1",
        )
        self.assertEqual(code, 0, f"--input-error 모드는 exit 0이어야 한다, 실제={stdout!r}")
        self.assertEqual(data.get("verdict"), "escalate")
        self.assertEqual(data.get("reason"), "input_error")
        history_path = self.task_path / ".scenario-gate-history.json"
        history = json.loads(history_path.read_text(encoding="utf-8"))
        self.assertIsInstance(history, list, "⑫ 이력은 JSON 배열을 유지해야 한다")
        self.assertIs(history[-1].get("counted"), True)

    def test_history_stays_array_and_no_tmp_file_left_after_multiple_records(self):
        _write_sdlc_v2_docs(self.task_path)
        _t167_write_coverage_input(self.task_path, complete=False)
        self.assertEqual(_t167_scenario_gate_record(self.task_path, 1)[0], 0)
        _t167_write_coverage_input(self.task_path, complete=False)
        self.assertEqual(_t167_scenario_gate_record(self.task_path, 2)[0], 0)

        history_path = self.task_path / ".scenario-gate-history.json"
        history = json.loads(history_path.read_text(encoding="utf-8"))
        self.assertIsInstance(history, list, "⑫ 이력은 JSON 배열을 유지해야 한다")
        self.assertEqual(len(history), 2)

        tmp_path = history_path.with_name(history_path.name + ".tmp")
        self.assertFalse(tmp_path.exists(), "⑬ 저장 뒤 임시 파일이 남지 않아야 한다")


if __name__ == "__main__":
    unittest.main(verbosity=2)
