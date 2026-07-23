"""
@header {
  "module": "test_scenario",
  "task": "056",
  "layer": "test",
  "domain": "opal-tools",
  "description": "test-tool scenario-* 4서브명령(scenario-init/scenario-lock/scenario-mark/scenario-status) 행위 계약 RED-first 테스트. RED 상태(미구현 — lib/scenario.py 부재, test_tool.py에 서브명령 미등록) — 전부 FAIL 예상. GREEN 전환은 EXECUTE 구현 워커 담당(작성자≠구현자, red-first.md §2). S-014는 기존 4서브명령 스위트 존재 확인만 수행(기존 test_test_tool.py 미수정).",
  "scenarios": ["S-011", "S-012", "S-007", "S-014", "T069/S-5", "T069/S-6", "T069/S-7", "T073/S-1", "T073/S-2"],
  "exports": [
    "TestScenarioLockRedGate",
    "TestScenarioMarkLockGate",
    "TestScenarioResultContract",
    "TestExistingSuiteRegressionPresence",
    "TestScenarioRedToolGated",
    "TestScenarioInitSeedNeutralized",
    "TestScenarioFidelityCheckUnmet",
    "TestScenarioFidelityCheckMixedAndLegacy",
    "TestScenarioConformance",
    "TestScenarioCoverageCheckUnmet",
    "TestScenarioCoverageCheckComplete",
    "TestScenarioCoverageInputInvalid",
    "TestScenarioCoverageCheckRegression"
  ]
}

[T073] scenario-coverage-check 신규 서브명령 RED-first 테스트 (opd 시나리오 목표-커버리지 루브릭
게이트 루프, F-007). test-tool `scenario-coverage-check --coverage-input <path>`는 scenario-gate.md
§3 정규화 페이로드({goal, requirements[], features[], hypotheses[], scenarios[]})의 R/F/H↔시나리오
매핑 누락을 결정론 판정한다(루브릭 ②③④, ①⑤⑥은 opal-evaluator-agent 소관 — 본 서브명령 미판정).
현재 lib/scenario.py에 미구현(SCENARIO_DISPATCH에 키 부재) — 신규 케이스 전부 자연 RED 예상.
GREEN 전환은 EXECUTE 구현 워커(opal-be-agent, F-002)가 담당한다(작성자≠구현자, red-first.md §2).
기존 클래스(TestScenarioLockRedGate ~ TestScenarioConformance)는 수정하지 않았다 — 아래 4개 클래스만
신규 추가. exit 16(coverage_unmet)/17(coverage_input_invalid)은 기존 8~14와 충돌 없이 배정
(PLAN.md §3.2.2, 15는 정보용 예약이라 회피).

[T069] 069 태스크 추가분: scenario-fidelity-check(fidelity_unmet exit 13) + scenario-conformance
(surface_unverified exit 14 / surfaces_file_not_found exit 15) 신규 서브명령 RED-first 테스트.
두 서브명령은 lib/scenario.py에 미구현 — 자연 RED 예상. GREEN 전환은 EXECUTE 구현 워커 담당
(작성자≠구현자, red-first.md §2). 기존 클래스는 불변.

[T056/ADD1] scenario-red 서브명령 신설 RED-first 추가 테스트 — RED 상태(미구현, lib/scenario.py에
  scenario-red 부재) 전부 FAIL 예상. GREEN 전환은 EXECUTE 구현 워커 담당. 기존 케이스(S-011/S-012/
  S-007/S-014)는 수정하지 않았다 — 아래 TestScenarioRedToolGated·TestScenarioInitSeedNeutralized만
  신규 추가. 배경: `.opal/brain/pages/concept/oppl-scenario-red-confirmed-gap.md`
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
# [T069] scenario-fidelity-check / scenario-conformance 신규 서브명령 RED-first 테스트
# 검증 대상: opal/tools/test-tool/run.sh 공개 인터페이스(exit code + stdout JSON)만
# 단언 — 내부 함수 직접 import 금지(red-first.md §4). PLAN.md §3.5.2/§3.6.2 근거.
# 두 서브명령은 현재 lib/scenario.py에 미구현 — 자연 RED 예상.
# 기존 클래스(TestScenarioLockRedGate ~ TestScenarioInitSeedNeutralized)는 수정하지 않았다.
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
# [T073] scenario-coverage-check 신규 서브명령 RED-first 테스트
# 검증 대상: run.sh 공개 인터페이스(exit code + stdout JSON)만 단언 — 내부 함수 직접
# import 금지(red-first.md §4). PLAN.md §3.2.2 / scenario-gate.md §3 정규화 계약 근거.
# 현재 lib/scenario.py에 미구현 — 신규 케이스 전부 자연 RED 예상.
# 기존 클래스(TestScenarioLockRedGate ~ TestScenarioConformance)는 수정하지 않았다.
# ─────────────────────────────────────────────────────────────────────────────

def _write_coverage_fixture(dest_dir, payload):
    """scenario-gate.md §3 정규화 페이로드를 임시 JSON 파일로 기록 — coverage-input fixture."""
    path = pathlib.Path(dest_dir) / "coverage-input.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _scenario_coverage_check(coverage_input_path):
    """scenario-coverage-check 신규 서브명령 호출 헬퍼 [T073] (PLAN §3.2.2)."""
    return _run(["scenario-coverage-check", "--coverage-input", str(coverage_input_path)])


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
