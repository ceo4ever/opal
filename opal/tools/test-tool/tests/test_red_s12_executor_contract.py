"""
@header {
  "module": "test_red_s12_executor_contract",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "S-12: (a) 핵심 UI 행동을 API 호출로 대체한 hybrid 시나리오는 real-usage로 승격되면 안 된다 — 관측 지점은 하네스 층(`lib/e2e/scenario_adapter.py`)의 `api_substituted_core_ui_assertions`이다(CONTRACT.md §C.4, §C.2). (b) browser profile인데 browser step이 없는 시나리오는 실행 전 executor contract mismatch로 정적 거부돼야 한다.",
  "scenarios": ["S-12"],
  "exports": ["TestHybridApiSubstitutionNotPromoted", "TestBrowserProfileStaticRejectionViaCli"]
}

교정 배경(PM 지시 (A)): 이전 버전은 `lib.e2e_contract.build_verdict`를 직접 호출해
`fidelity != "real-usage"`를 요구했다. 이를 만족시키려면 `e2e_contract.py`가
`step_role`을 소비해야 하는데, `TASK.md` C-1이 그 파일을 변경 0으로 동결하고
`CONTRACT.md` §C.2는 verdict 조립을 `e2e_contract` 소유로 규정한다. 결정적으로
`TEST-SCENARIO.md` S-12 행의 방법·환경은 "integration — 실행 전 정적 거부 + 실행 후
충실도 판정"이고, `CONTRACT.md:229`는 `step_role`이 §C.4 집행의 **입력**이라고
규정한다 — §C.4 집행은 `e2e_contract` 층이 아니라 하네스 층의 책임이다(실측:
`orchestrator.py:757`가 `e2e_scenario_adapter.api_substituted_core_ui_assertions(
scenario, plan, assertion_results)`를 호출해 `fidelity_ceiling`을 정한다).

이 테스트는 이제 `e2e_contract.build_verdict`를 우회하지 않고, W-10이 구현한 그
공개 함수(`scenario_adapter.api_substituted_core_ui_assertions`, 모듈 header의
`exports`에 선언됨)를 직접 관측한다. 이 함수가 비어 있지 않은 목록을 돌려주면, 그
결과가 `orchestrator.py:769`에서 그대로 `fidelity_ceiling = FIDELITY_REAL_HTTP`
("real-http")로 이어진다는 사실은 소스 열람이 아니라 `lib.scenario.FIDELITY_ORDER`
(공개 상수 — `scenario.py`도 C-1이 동결하지만 **소비**는 허용된다)로 검증한다 —
`FIDELITY_ORDER["real-http"] < FIDELITY_ORDER["real-usage"]`이므로 이 상한 아래에서는
`real-usage` 승격이 구조적으로 불가능하다.

실행을 통한 최종 `run.json.fidelity` 왕복 관측은 별개 이유로 아직 CLI에서 재현할 수
없다 — `orchestrator.py`가 browser 후보가 선택된 run을 `e2e_scenario_runner_absent`로
봉쇄해 두었기 때문이다(동결 RED S-27 `(d-1)`의 과다 구속이 원인이었고, PM 지시 (B)에서
별도로 좁혔다). 그 봉쇄가 W-10에 의해 풀리기 전까지는 `scenario_adapter` 층의 직접
관측이 이 시나리오가 가리키는 정확한 하네스 계층이다.

(b) `_validate_v2_scenario`가 static executor contract mismatch를 이미 판정하지만,
    이를 `e2e run` CLI로 재현하려면 `test-scenario.json`(태스크 루트, locked)을
    건드릴 수 없으므로 이 테스트 전용 fixture를 임시 폴더에 써서 --task-path로
    넘긴다(§B.1.1 필수 인자 교정 포함).
"""
from __future__ import annotations

import importlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_SOURCE_ROOT = _TOOL_DIR.parent.parent.parent
_PYTHON = sys.executable
sys.path.insert(0, str(_TOOL_DIR))


def _contract():
    return importlib.import_module("lib.e2e_contract")


def _scenario_adapter():
    return importlib.import_module("lib.e2e.scenario_adapter")


def _scenario_module():
    return importlib.import_module("lib.scenario")


class TestHybridApiSubstitutionNotPromoted(unittest.TestCase):
    """S-12(a): 핵심 UI 행동을 API로 대체한 hybrid 시나리오는 real-usage가 되면 안 된다.

    관측 지점: `scenario_adapter.api_substituted_core_ui_assertions()`(하네스 §C.4
    집행 2의 공개 입력 함수) + `scenario.FIDELITY_ORDER`(공개 상수)로, orchestrator가
    이 판정을 그대로 소비하면 `real-usage` 승격이 구조적으로 불가능함을 증명한다.
    """

    def test_core_ui_assertion_satisfied_only_by_verify_api_step_is_rejected(self):
        adapter = _scenario_adapter()
        scenario_module = _scenario_module()

        # hybrid profile: 계약상 api+browser 둘 다 필요하다. browser executor는
        # "로그인"같은 부수 단계(step_role=setup)에만 쓰이고, 핵심 UI 행동(예: '저장 버튼
        # 클릭 후 목록에 반영')의 검증 assertion은 step_role=verify인 API 호출 하나로만
        # 충족된다 — 이는 §C.4가 금지하는 대체다.
        steps = [
            {"id": "st-1", "executor": "browser", "step_role": "setup", "action": "login"},
            {
                "id": "st-2",
                "executor": "api",
                "step_role": "verify",
                "action": "GET /api/items — 핵심 UI 저장 동작의 검증을 API로 대체",
            },
        ]
        scenario = {
            "id": "hybrid-ui-bypass",
            "profile": "hybrid",
            "surface_kind": "hybrid",
            "actors": ["api", "browser"],
            "steps": steps,
            "assertions": [{"id": "core-ui-save", "expected": "saved", "core_ui_behavior": True}],
            "required_evidence": ["semantic_assertion"],
        }
        assertion_results = [
            {"id": "core-ui-save", "expected": "saved", "actual": "saved", "observed_via_step": "st-2"},
        ]

        plan = adapter.build_execution_plan(scenario)
        substituted = adapter.api_substituted_core_ui_assertions(scenario, plan, assertion_results)

        self.assertEqual(
            substituted, ["core-ui-save"],
            f"the core UI assertion satisfied only by a step_role=verify api step must be "
            f"detected as substituted (§C.4): substituted={substituted}",
        )

        # orchestrator.py:769 — substituted가 비어 있지 않으면 fidelity_ceiling은
        # 반드시 "real-http"다. real-http < real-usage이므로 이 상한 아래에서는 어떤
        # 경로로도 real-usage 승격이 불가능하다.
        ceiling = "real-http" if substituted else None
        self.assertEqual(ceiling, "real-http")
        self.assertLess(
            scenario_module.FIDELITY_ORDER[ceiling],
            scenario_module.FIDELITY_ORDER["real-usage"],
            "a run whose core UI assertion is substituted by a verify-role api step must be "
            "capped below real-usage — it can never be promoted to real-usage",
        )

    def test_setup_role_api_step_is_not_treated_as_bypass(self):
        """TD-17: setup·cleanup 용도 API 호출은 우회로 판정되지 않는다."""
        adapter = _scenario_adapter()

        # 핵심 UI assertion은 browser verify step으로 충족되고, api는 setup(로그인)에만
        # 쓰인다 — 대체가 아니다.
        steps = [
            {"id": "st-1", "executor": "api", "step_role": "setup", "action": "login via api"},
            {"id": "st-2", "executor": "browser", "step_role": "verify", "action": "click save"},
        ]
        scenario = {
            "id": "hybrid-ui-legit",
            "profile": "hybrid",
            "surface_kind": "hybrid",
            "actors": ["api", "browser"],
            "steps": steps,
            "assertions": [{"id": "core-ui-save", "expected": "saved", "core_ui_behavior": True}],
            "required_evidence": ["semantic_assertion"],
        }
        assertion_results = [
            {"id": "core-ui-save", "expected": "saved", "actual": "saved", "observed_via_step": "st-2"},
        ]

        plan = adapter.build_execution_plan(scenario)
        substituted = adapter.api_substituted_core_ui_assertions(scenario, plan, assertion_results)
        self.assertEqual(
            substituted, [],
            f"a setup-role api step must not be treated as a UI bypass when the core "
            f"assertion is actually satisfied by a browser verify step: substituted={substituted}",
        )


class TestBrowserProfileStaticRejectionViaCli(unittest.TestCase):
    """S-12(b): browser profile + browser step 없음 → 실행 전 정적 거부(CLI 경로).

    교정(PM 지시): §B.1.1 필수 인자(--scenario·--task-path·--target enum)를 채우고,
    `test-scenario.json`(태스크 루트, locked)을 건드리는 대신 이 테스트 전용 fixture를
    임시 폴더에 써서 --task-path로 넘긴다. fixture는 TEST-SCENARIO.md S-12 행이 요구하는
    "browser profile인데 browser step이 없는 시나리오"를 그대로 구성한다(step executor는
    전부 api).
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.task_path = self.tmpdir / "fixture"
        self.task_path.mkdir()
        (self.task_path / "test-scenario.json").write_text(
            json.dumps(
                {
                    "schema_version": "2.0",
                    "task_id": "s12-fixture-task",
                    "locked": False,
                    "scenarios": [
                        {
                            "id": "s12-browser-no-browser-step",
                            "surface_kind": "browser",
                            "profile": "browser",
                            "actors": ["browser"],
                            # browser profile은 executor="browser" step을 요구하지만
                            # (EXECUTOR_MATRIX["browser"]["required"] == ("browser",)),
                            # 이 fixture는 의도적으로 api step만 둔다 — executor contract
                            # mismatch를 재현한다.
                            "steps": [
                                {"id": "st-1", "executor": "api", "step_role": "verify", "action": "GET /api/x"},
                            ],
                            "assertions": [{"id": "a1", "expected": "ok"}],
                            "required_evidence": ["metadata"],
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_browser_profile_without_browser_step_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as artifact_dir:
            import os
            env = os.environ.copy()
            env["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir
            proc = subprocess.run(
                [
                    _PYTHON, str(_TEST_TOOL_PY),
                    "e2e", "run",
                    "--scenario", "s12-browser-no-browser-step",
                    "--task-path", str(self.task_path),
                    "--target", "source-worktree",
                    "--worktree-root", str(_SOURCE_ROOT),
                ],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )
            self.assertNotEqual(
                proc.returncode, 2,
                f"'e2e run' subcommand missing (RED target): {proc.stderr!r}",
            )
            data = json.loads(proc.stdout)
            self.assertEqual(
                data.get("error"), "surface_profile_mismatch",
                f"missing browser step must be a static pre-execution rejection: {data}",
            )
            self.assertEqual(
                data.get("executed"), False,
                f"rejection must happen before execution, not as a runtime failure: {data}",
            )


if __name__ == "__main__":
    unittest.main()
