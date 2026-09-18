"""
@header {
  "module": "test_e2e_surface_fidelity",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "W-10 hybrid 연결과 surface fidelity 게이트 검증 — CONTRACT.md §C.4 두 집행 지점(실행 전 정적 거부 / 실행 후 real-usage 미승격)과 setup·cleanup API 비판정, §A.1.2 개정본이 허용하는 hybrid의 executor 타입별 selected 1개씩, §A.2.1 scenario_running→evidence_captured 전이를 고정한다.",
  "scenarios": ["S-12"],
  "exports": [
    "TestStaticExecutorContractGate", "TestApiSubstitutionDetection",
    "TestAchievedFidelityCeiling", "TestHybridWiring"
  ]
}

lib/e2e_contract.py·lib/scenario.py는 소비만 한다(TASK.md C-1) — 이 테스트는 두 파일의
동작을 바꾸지 않고 그 반환값을 소비하는 하네스 쪽 경로만 고정한다. 판정 문자열은 전부
e2e_contract에서 읽어 비교하며 리터럴로 기대값을 짓지 않는다(C-125-1).
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
_SOURCE_ROOT = _TOOL_DIR.parent.parent.parent

from lib import e2e_contract  # noqa: E402
from lib.e2e import drivers as e2e_drivers  # noqa: E402
from lib.e2e import executors as e2e_executors  # noqa: E402
from lib.e2e import orchestrator as e2e_orchestrator  # noqa: E402
from lib.e2e import scenario_adapter as e2e_adapter  # noqa: E402
from lib.e2e import target as e2e_target  # noqa: E402


def _hybrid_scenario(steps, assertions=None):
    return {
        "id": "hybrid-1",
        "surface_kind": "hybrid",
        "profile": "hybrid",
        "actors": ["api", "browser"],
        "steps": steps,
        "assertions": assertions
        or [{"id": "core-ui-save", "expected": "saved", "core_ui_behavior": True}],
        "required_evidence": ["metadata"],
    }


class TestStaticExecutorContractGate(unittest.TestCase):
    """§C.4 집행 1 — 실행 전 정적 거부. 판정은 e2e_contract 함수가 낸다."""

    def test_browser_profile_without_a_browser_step_is_rejected(self):
        check = e2e_adapter.static_executor_contract_error({
            "id": "s", "profile": "browser", "surface_kind": "browser",
            "actors": ["browser"],
            "steps": [{"id": "st-1", "executor": "api", "step_role": "verify"}],
        })
        self.assertIsNotNone(check, "browser profile에 browser step이 없으면 거부돼야 한다")
        self.assertFalse(check["ok"])
        self.assertIn("browser", check["detail"]["missing_executors"])
        # error·status는 계약 함수가 돌려준 값 그대로다.
        self.assertEqual(
            check["error"],
            e2e_contract.validate_pass_requirements(
                {"profile": "browser", "surface_kind": "browser", "actors": ["browser"]},
                {"profile": "browser", "observed_executors": ["api"]},
            )["error"],
        )

    def test_browser_profile_with_a_browser_step_passes_the_gate(self):
        self.assertIsNone(e2e_adapter.static_executor_contract_error({
            "id": "s", "profile": "browser", "surface_kind": "browser",
            "actors": ["browser"],
            "steps": [{"id": "st-1", "executor": "browser", "step_role": "verify"}],
        }))

    def test_hybrid_needs_both_types_and_accepts_exactly_that(self):
        """§A.1.2 개정본 — hybrid는 api+browser 두 타입을 모두 요구한다."""
        self.assertEqual(
            tuple(e2e_contract.executor_contract("hybrid")["required"]), ("api", "browser")
        )
        self.assertIsNotNone(e2e_adapter.static_executor_contract_error(
            _hybrid_scenario([{"id": "st-1", "executor": "api", "step_role": "verify"}])
        ))
        self.assertIsNone(e2e_adapter.static_executor_contract_error(_hybrid_scenario([
            {"id": "st-1", "executor": "api", "step_role": "setup"},
            {"id": "st-2", "executor": "browser", "step_role": "verify"},
        ])))

    def test_assertion_and_evidence_failures_are_not_pre_execution_rejections(self):
        """실행 전에 확정할 수 없는 축까지 정적 거부로 끌어오지 않는다.

        아래 시나리오는 executor 축이 성립하므로(api step 존재) 게이트를 통과해야 한다.
        assertion 결과가 없다는 사실은 실행 **후**에만 판정 대상이다.
        """
        self.assertIsNone(e2e_adapter.static_executor_contract_error({
            "id": "s", "profile": "api", "surface_kind": "api", "actors": ["service"],
            "steps": [{"id": "st-1", "executor": "api", "step_role": "verify"}],
            "assertions": [],
        }))

    def test_unknown_profile_is_left_to_the_scenario_contract_validator(self):
        """C-8 — 계약에 없는 profile에 대한 판정을 지어내지 않는다."""
        self.assertIsNone(e2e_adapter.static_executor_contract_error({
            "id": "s", "profile": None, "surface_kind": None, "actors": [],
            "steps": [{"id": "st-1", "executor": "api"}],
        }))


class TestApiSubstitutionDetection(unittest.TestCase):
    """§C.4 집행 2 입력 — 핵심 UI assertion을 verify API가 대체했는가(R-12·AC-8)."""

    def _plan(self, steps):
        return e2e_adapter.build_execution_plan(_hybrid_scenario(steps))

    def test_core_ui_assertion_met_only_by_a_verify_api_step_is_flagged(self):
        scenario = _hybrid_scenario([
            {"id": "st-1", "executor": "browser", "step_role": "setup"},
            {"id": "st-2", "executor": "api", "step_role": "verify"},
        ])
        plan = e2e_adapter.build_execution_plan(scenario)
        flagged = e2e_adapter.api_substituted_core_ui_assertions(
            scenario, plan,
            [{"id": "core-ui-save", "expected": "saved", "actual": "saved",
              "observed_via_step": "st-2"}],
        )
        self.assertEqual(flagged, ["core-ui-save"])

    def test_setup_and_cleanup_api_calls_are_not_treated_as_a_bypass(self):
        """[MUST] §C.4 — setup·cleanup 용도 API 호출은 우회로 판정되지 않는다."""
        scenario = _hybrid_scenario([
            {"id": "st-setup", "executor": "api", "step_role": "setup"},
            {"id": "st-ui", "executor": "browser", "step_role": "verify"},
            {"id": "st-teardown", "executor": "api", "step_role": "cleanup"},
        ])
        plan = e2e_adapter.build_execution_plan(scenario)
        self.assertEqual(
            e2e_adapter.api_substituted_core_ui_assertions(
                scenario, plan,
                [{"id": "core-ui-save", "expected": "saved", "actual": "saved",
                  "observed_via_step": "st-ui", "executor": "browser"}],
            ),
            [],
        )
        # setup·cleanup API step은 애초에 verify 후보 집합에 들어오지 않는다.
        grouped = e2e_adapter.verify_step_ids_by_executor(plan)
        self.assertNotIn("api", grouped)
        self.assertEqual(grouped["browser"], ["st-ui"])

    def test_assertion_without_a_core_ui_marker_is_not_flagged(self):
        """표시 없는 assertion을 핵심 UI로 확대 해석하지 않는다(TD-12)."""
        scenario = _hybrid_scenario(
            [{"id": "st-1", "executor": "api", "step_role": "verify"},
             {"id": "st-2", "executor": "browser", "step_role": "setup"}],
            assertions=[{"id": "plain", "expected": "ok"}],
        )
        plan = e2e_adapter.build_execution_plan(scenario)
        self.assertEqual(
            e2e_adapter.api_substituted_core_ui_assertions(
                scenario, plan,
                [{"id": "plain", "expected": "ok", "actual": "ok", "observed_via_step": "st-1"}],
            ),
            [],
        )

    def test_a_result_that_names_no_step_or_executor_is_not_assumed_to_be_a_bypass(self):
        scenario = _hybrid_scenario([
            {"id": "st-1", "executor": "api", "step_role": "verify"},
            {"id": "st-2", "executor": "browser", "step_role": "verify"},
        ])
        plan = e2e_adapter.build_execution_plan(scenario)
        self.assertEqual(
            e2e_adapter.api_substituted_core_ui_assertions(
                scenario, plan, [{"id": "core-ui-save", "expected": "x", "actual": "x"}]
            ),
            [],
        )


class TestAchievedFidelityCeiling(unittest.TestCase):
    """§A.1 `fidelity` — 달성 충실도에 §C.4 상한을 적용한다."""

    def _selected_browser(self):
        return [{"type": "browser", "outcome": "selected"}, {"type": "api", "outcome": "selected"}]

    def test_browser_executor_alone_reaches_real_usage(self):
        self.assertEqual(
            e2e_orchestrator._achieved_fidelity(
                evidence_complete=True, candidates=self._selected_browser(), handles=[]
            ),
            e2e_orchestrator.FIDELITY_REAL_USAGE,
        )

    def test_api_substitution_ceiling_blocks_promotion_to_real_usage(self):
        """[MUST] 핵심 UI를 API로 대체한 시나리오는 real-usage로 승격되지 않는다."""
        self.assertEqual(
            e2e_orchestrator._achieved_fidelity(
                evidence_complete=True,
                candidates=self._selected_browser(),
                handles=[],
                ceiling=e2e_orchestrator.FIDELITY_REAL_HTTP,
            ),
            e2e_orchestrator.FIDELITY_REAL_HTTP,
        )

    def test_the_ceiling_never_raises_an_achieved_fidelity(self):
        """상한은 깎기만 한다 — 증적 불완전 run을 상한이 끌어올리지 않는다(AC-6)."""
        self.assertEqual(
            e2e_orchestrator._achieved_fidelity(
                evidence_complete=False,
                candidates=self._selected_browser(),
                handles=[],
                ceiling=e2e_orchestrator.FIDELITY_REAL_USAGE,
            ),
            e2e_orchestrator.FIDELITY_MOCK,
        )


class _FakeBrowserDriver(e2e_drivers.BrowserDriver):
    """probe만 통과시키는 테스트용 driver. 실행 경로는 이 테스트가 쓰지 않는다."""

    name = "agent-browser"
    session_mode = "orca-managed"

    def __init__(self, runtime_context=None):
        self.runtime_context = dict(runtime_context or {})
        self.binary_path = None
        self.resolution_source = "installed"
        self.declared_version = None

    def op_probe(self, request):
        return {
            "driver": self.name,
            "session_mode": self.session_mode,
            "available": True,
            "capabilities": {
                key: {"available": True, "route": "native", "probed": True}
                for key in e2e_drivers.CAPABILITY_KEYS
            },
        }


class TestHybridWiring(unittest.TestCase):
    """hybrid profile의 후보 해석과 §A.2.1 전이.

    이 클래스는 driver 레지스트리에 대역을 꽂는다. 복원하지 않으면 **뒤에 도는 테스트가
    실 driver 대신 대역을 잡는다** — AC-4처럼 실제 브라우저를 요구하는 테스트가 조용히
    대역 위에서 돌면 "실행했다"는 결론이 거짓이 된다. 그래서 매 테스트 전후로 레지스트리
    전체를 스냅샷·복원한다.
    """

    def setUp(self):
        self._registry_snapshot = e2e_drivers.registered_drivers()

    def tearDown(self):
        e2e_drivers._REGISTRY.clear()
        e2e_drivers._REGISTRY.update(self._registry_snapshot)

    def _run(self, scenario, **kwargs):
        with tempfile.TemporaryDirectory() as task_path, \
                tempfile.TemporaryDirectory() as artifact_dir:
            pathlib.Path(task_path, "test-scenario.json").write_text(
                json.dumps(
                    {"schema_version": e2e_contract.E2E_CONTRACT_SCHEMA_VERSION,
                     "task_id": "t", "locked": False, "scenarios": [scenario]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            os.environ["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir
            try:
                payload = e2e_orchestrator.run_e2e(
                    target=e2e_target.TARGET_SOURCE_WORKTREE,
                    scenario_id=scenario["id"],
                    task_path=task_path,
                    worktree_root=str(_SOURCE_ROOT),
                    **kwargs,
                )
                journal = json.loads(
                    pathlib.Path(artifact_dir, "journal.json").read_text(encoding="utf-8")
                )
                run_json = json.loads(
                    pathlib.Path(artifact_dir, "run.json").read_text(encoding="utf-8")
                )
            finally:
                os.environ.pop("OPAL_E2E_ARTIFACT_DIR", None)
        return payload, run_json, journal

    def test_hybrid_resolves_one_selected_candidate_per_required_type(self):
        """§A.1.2 개정본 — hybrid는 타입별 정확히 1개까지 selected를 가질 수 있다.

        browser 후보는 probe만 통과시키는 대역으로 채우고, api 후보는 실제 SUT `/health`를
        물어야 하므로(§A.8, NR-7) 여기서는 probe 단계까지만 확인한다.
        """
        e2e_drivers.register_driver("agent-browser", "orca-managed", _FakeBrowserDriver)
        candidates, probes = e2e_orchestrator._resolve_executor_candidates(
            _hybrid_scenario([
                {"id": "st-1", "executor": "api", "step_role": "setup"},
                {"id": "st-2", "executor": "browser", "step_role": "verify"},
            ]),
            runtime_context={"backend_url": None, "artifact_dir": "", "task_path": ""},
        )
        selected = [item for item in candidates if item["outcome"] == "selected"]
        by_type = {}
        for item in selected:
            by_type.setdefault(item["type"], []).append(item)
        for executor_type, items in by_type.items():
            self.assertEqual(len(items), 1, f"{executor_type}: 타입별 selected는 1개를 넘지 않는다")
        self.assertEqual([item["type"] for item in selected][:1], ["browser"])
        # order는 배열 전체에서 1부터 연속이다(§A.1.2).
        self.assertEqual([item["order"] for item in candidates],
                         list(range(1, len(candidates) + 1)))
        self.assertTrue(probes)

    def test_a_type_with_no_selected_candidate_ends_as_executor_unavailable(self):
        """[MUST] §A.1.2 — 필요 타입 중 하나라도 selected가 0개이면 executor_unavailable.

        이 머신에는 가용 browser 후보가 없다. 그럴 때 api executor를 대역으로 세워
        pass를 만들지 않고 구조화된 미가용 사유로 끝낸다(H-2, §C.4).
        """
        original = e2e_drivers.registered_drivers
        e2e_drivers.registered_drivers = lambda: {}
        try:
            payload, run_json, journal = self._run(_hybrid_scenario([
                {"id": "st-1", "executor": "api", "step_role": "setup"},
                {"id": "st-2", "executor": "browser", "step_role": "verify"},
            ]))
        finally:
            e2e_drivers.registered_drivers = original

        self.assertEqual(payload["status"], "executor_unavailable")
        self.assertEqual(payload["exit_code"], e2e_contract.status_to_exit(payload["status"]))
        self.assertFalse(payload["executed"])
        browser = [item for item in run_json["candidates"] if item["type"] == "browser"]
        self.assertTrue(browser, "후보 기록이 비면 미가용 사유를 감사할 수 없다")
        self.assertEqual({item["outcome"] for item in browser}, {"provider_unavailable"})
        self.assertTrue(all(item["reason"] for item in browser), "사유가 구조화돼 기록된다")
        # 대역으로 real-usage를 만들지 않는다.
        self.assertNotEqual(run_json["fidelity"], e2e_orchestrator.FIDELITY_REAL_USAGE)
        # 실행하지 않았으므로 scenario_running·evidence_captured는 발행되지 않는다.
        states = [item["to"] for item in journal["transitions"]]
        self.assertNotIn(e2e_orchestrator.STATE_SCENARIO_RUNNING, states)
        self.assertNotIn(e2e_orchestrator.STATE_EVIDENCE_CAPTURED, states)

    def test_the_a21_transition_pair_exists_and_precedes_the_final_status(self):
        """§A.2.1 — `scenario_running` → `evidence_captured` → 최종 상태 순서.

        상태 머신이 이 두 상태를 실제로 발행하는지 step runner를 직접 돌려 확인한다.
        SUT·executor는 대역이며, 이 검사의 대상은 전이 순서다.
        """
        journal = e2e_orchestrator._Journal("e2e-20260915-301")
        journal.to(e2e_orchestrator.STATE_EXECUTOR_READY)

        class _Recorder:
            def __init__(self):
                self.steps = []

            def wrap(self):
                return {
                    "run_step": lambda step: self.steps.append(step.id),
                    "assert": lambda assertion: {
                        "id": assertion["id"], "expected": assertion["expected"],
                        "actual": assertion["expected"], "passed": True,
                    },
                    "capture": lambda: None,
                    "close": lambda: None,
                }

        recorder = _Recorder()
        original = e2e_orchestrator._open_executors
        e2e_orchestrator._open_executors = lambda selected, context, **_: {
            "api": recorder.wrap(), "browser": recorder.wrap()
        }
        try:
            outcome = e2e_orchestrator._run_scenario_steps(
                scenario=_hybrid_scenario([
                    {"id": "st-setup", "executor": "api", "step_role": "setup"},
                    {"id": "st-ui", "executor": "browser", "step_role": "verify"},
                ]),
                selected=[{"type": "api", "outcome": "selected"},
                          {"type": "browser", "outcome": "selected"}],
                journal=journal,
                writer=None,
                run_id="e2e-20260915-301",
                runtime_context={},
                urls={"frontend": None, "backend": None},
                target=e2e_target.TARGET_SOURCE_WORKTREE,
            )
        finally:
            e2e_orchestrator._open_executors = original

        states = [item["to"] for item in journal.transitions]
        self.assertIn(e2e_orchestrator.STATE_SCENARIO_RUNNING, states)
        self.assertIn(e2e_orchestrator.STATE_EVIDENCE_CAPTURED, states)
        self.assertLess(
            states.index(e2e_orchestrator.STATE_SCENARIO_RUNNING),
            states.index(e2e_orchestrator.STATE_EVIDENCE_CAPTURED),
        )
        self.assertTrue(outcome["executed"])
        self.assertEqual(outcome["status"], "pass")
        self.assertEqual(outcome["observed_executor_types"], ["api", "browser"])
        # API setup이 핵심 UI 행동보다 먼저 돈다(§A.4 step_role 순서).
        self.assertEqual(recorder.steps, ["st-setup", "st-ui"])
        # browser verify step이 핵심 assertion을 충족했으므로 상한이 걸리지 않는다.
        self.assertIsNone(outcome["fidelity_ceiling"])

    def test_a_verify_api_substitution_sets_the_real_http_ceiling_on_the_run(self):
        """§C.4 집행 2 — 실행 후 판정에서 real-usage 승격이 막힌다."""
        journal = e2e_orchestrator._Journal("e2e-20260915-302")

        def _wrap(executor_type):
            return {
                "run_step": lambda step: None,
                "assert": lambda assertion: {
                    "id": assertion["id"], "expected": assertion["expected"],
                    "actual": assertion["expected"], "passed": True,
                    "executor": executor_type,
                },
                "capture": lambda: None,
                "close": lambda: None,
            }

        original = e2e_orchestrator._open_executors
        e2e_orchestrator._open_executors = lambda selected, context, **_: {
            "api": _wrap("api"), "browser": _wrap("browser")
        }
        try:
            outcome = e2e_orchestrator._run_scenario_steps(
                scenario=_hybrid_scenario([
                    # browser는 로그인 같은 부수 단계에만 쓰이고, 핵심 UI 행동의 검증은
                    # verify API step 하나가 가져간다 — 이것이 §C.4가 막는 대체다.
                    {"id": "st-login", "executor": "browser", "step_role": "setup"},
                    {"id": "st-verify", "executor": "api", "step_role": "verify"},
                ]),
                selected=[{"type": "api", "outcome": "selected"},
                          {"type": "browser", "outcome": "selected"}],
                journal=journal,
                writer=None,
                run_id="e2e-20260915-302",
                runtime_context={},
                urls={"frontend": None, "backend": None},
                target=e2e_target.TARGET_SOURCE_WORKTREE,
            )
        finally:
            e2e_orchestrator._open_executors = original

        self.assertEqual(outcome["fidelity_ceiling"], e2e_orchestrator.FIDELITY_REAL_HTTP)
        self.assertEqual(
            e2e_orchestrator._achieved_fidelity(
                evidence_complete=True,
                candidates=[{"type": "browser", "outcome": "selected"}],
                handles=[],
                ceiling=outcome["fidelity_ceiling"],
            ),
            e2e_orchestrator.FIDELITY_REAL_HTTP,
        )
        self.assertEqual(outcome["detail_code"], "e2e_core_ui_behavior_substituted_by_api")

    def test_browser_step_runs_end_to_end_and_emits_the_a21_transitions(self):
        """browser 후보가 선택된 run은 step을 **실제로 실행**하고 §A.2.1 전이를 발행한다.

        이 테스트는 이전의 `..._withheld_and_says_so`를 대체한다. 그때는 동결 RED S-27의
        "run당 driver 호출 2회" 상한 때문에 browser step 실행을 보류했고, 그 보류 사실을
        관측점으로 고정했다. PM이 (d-1)을 "같은 연산 시그니처 중복 금지"로 정정해 보류가
        풀렸으므로, 같은 자리에서 이제 **실행이 실제로 일어난다**는 것을 고정한다 —
        관측점을 잃지 않는 것이 목적이다.

        §B.2 연산은 각각 **한 번씩만** 호출된다. 후보 해석이 만든 driver 인스턴스를 step
        실행이 그대로 이어받기 때문이며(`_DriverCache`), 재생성하면 생성자의 binary 해석이
        한 번 더 일어나 S-27이 재시도로 잡는다.
        """
        calls = []

        class _RecordingDriver(_FakeBrowserDriver):
            def op_open(self, request):
                calls.append("open")
                return {"page_id": "page-1"}

            def op_act(self, request):
                calls.append(f"act:{request.get('step_id')}")
                return {"ok": True}

            def op_assert(self, request):
                calls.append("assert")
                assertion = request.get("assertion") or {}
                return {"id": assertion["id"], "expected": assertion["expected"],
                        "actual": assertion["expected"], "passed": True}

            def op_capture(self, request):
                calls.append("capture")
                return {"artifacts": {}, "redacted": True, "redaction_failed": False}

            def op_close(self, request):
                calls.append("close")
                return {"closed": True}

        e2e_drivers.register_driver("agent-browser", "orca-managed", _RecordingDriver)
        try:
            payload, run_json, journal = self._run({
                "id": "browser-only", "surface_kind": "browser", "profile": "browser",
                "actors": ["browser"],
                "steps": [{"id": "st-1", "executor": "browser", "step_role": "verify"}],
                "assertions": [{"id": "a1", "expected": "ok"}],
                "required_evidence": ["metadata"],
            })
        finally:
            # 레지스트리 복원은 tearDown이 일괄 수행한다.
            pass

        # 실행이 실제로 일어났다.
        self.assertTrue(payload["executed"], f"browser step must actually run: {payload}")
        self.assertEqual(run_json["observed_executors"], ["browser"])
        self.assertEqual(run_json["assertion_summary"]["passed"], 1)
        self.assertEqual(run_json["assertion_summary"]["missing"], 0)

        # §A.2.1 — scenario_running → evidence_captured → 최종 상태 순서.
        states = [item["to"] for item in journal["transitions"]]
        self.assertIn(e2e_orchestrator.STATE_SCENARIO_RUNNING, states)
        self.assertIn(e2e_orchestrator.STATE_EVIDENCE_CAPTURED, states)
        self.assertLess(
            states.index(e2e_orchestrator.STATE_EXECUTOR_READY),
            states.index(e2e_orchestrator.STATE_SCENARIO_RUNNING),
        )
        self.assertLess(
            states.index(e2e_orchestrator.STATE_SCENARIO_RUNNING),
            states.index(e2e_orchestrator.STATE_EVIDENCE_CAPTURED),
        )
        # §A.2.2 [MUST] — 최종 상태 직전은 evidence_captured다(중간 상태 건너뛴 pass 금지).
        self.assertEqual(
            states[states.index(e2e_orchestrator.STATE_EVIDENCE_CAPTURED) + 1],
            run_json["status"],
        )

        # §B.2 연산은 각각 1회씩만 호출된다 — 중복은 재시도다(S-27 (d-1)).
        self.assertEqual(calls, ["open", "act:st-1", "assert", "capture", "close"])
        self.assertEqual(len(calls), len(set(calls)), f"no operation may repeat: {calls}")

    def test_a_driver_missing_an_operation_blocks_instead_of_switching_candidates(self):
        """연산 부재는 `infra_error`가 아니라 `blocked`이며 후보 전환도 없다.

        `dispatch()`가 연산을 찾지 못해 올리는 오류는 driver가 아무 일도 하기 전에 나온다 —
        §C.7이 `infra_error`로 규정한 "driver 실행 오류"가 아니라 하네스가 그 표면을 실행할
        수단이 없다는 뜻이다. 어느 쪽이든 다음 후보로 넘어가지 않는다(TASK.md C-3).
        """
        e2e_drivers.register_driver("agent-browser", "orca-managed", _FakeBrowserDriver)
        payload, run_json, journal = self._run({
            "id": "browser-only", "surface_kind": "browser", "profile": "browser",
            "actors": ["browser"],
            "steps": [{"id": "st-1", "executor": "browser", "step_role": "verify"}],
            "assertions": [{"id": "a1", "expected": "ok"}],
            "required_evidence": ["metadata"],
        })
        # _FakeBrowserDriver는 probe만 구현한다 — open에서 연산 부재가 드러난다.
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["exit_code"], e2e_contract.status_to_exit("blocked"))
        self.assertIn(run_json["detail_code"], e2e_orchestrator._CAPABILITY_GAP_DETAIL_CODES)
        self.assertFalse(payload["executed"])
        # 후보 2 이후는 시도되지 않는다.
        later = [item for item in run_json["candidates"] if item["order"] > 1]
        for item in later:
            self.assertEqual(item["reason"], "not_attempted_after_selection")
        self.assertIn(e2e_orchestrator.STATE_SCENARIO_RUNNING,
                      [item["to"] for item in journal["transitions"]])

    def test_a_step_needing_an_unselected_executor_is_never_run_by_another_one(self):
        """[MUST] TASK.md C-3·§C.4 — 다른 executor로 대체 실행하지 않는다."""
        journal = e2e_orchestrator._Journal("e2e-20260915-303")
        original = e2e_orchestrator._open_executors
        e2e_orchestrator._open_executors = lambda selected, context, **_: {
            "api": {"run_step": lambda step: None, "assert": lambda a: {},
                    "capture": lambda: None, "close": lambda: None}
        }
        try:
            outcome = e2e_orchestrator._run_scenario_steps(
                scenario=_hybrid_scenario([
                    {"id": "st-1", "executor": "api", "step_role": "setup"},
                    {"id": "st-2", "executor": "browser", "step_role": "verify"},
                ]),
                selected=[{"type": "api", "outcome": "selected"}],
                journal=journal,
                writer=None,
                run_id="e2e-20260915-303",
                runtime_context={},
                urls={"frontend": None, "backend": None},
                target=e2e_target.TARGET_SOURCE_WORKTREE,
            )
        finally:
            e2e_orchestrator._open_executors = original
        self.assertEqual(outcome["status"], "infra_error")
        self.assertEqual(outcome["detail_code"], "e2e_step_executor_not_selected")
        self.assertEqual(outcome["assertion_results"], [])


if __name__ == "__main__":
    unittest.main()


class TestAcceptanceBrowserPathways(unittest.TestCase):
    """AC-4·AC-5 관통 — 동결 `test-scenario.json`의 S-8·S-9에는 실행 스펙이 없으므로
    (`steps:[{id,executor}]`뿐, assertion에 `verifier`·`target` 없음) S-26·S-27과 같은
    방식으로 이 테스트가 자기 fixture를 임시 폴더에 쓴다. spec은 잠겨 있어 고치지 않는다.

    [MUST] 캡틴의 실환경이다(TASK.md C-2). 이 테스트는 사용자 `default` 세션·탭·Chrome
    profile을 **종료·삭제하지 않는다** — driver가 `owned.json`에 올린 run 전용 page만
    닫힌다. AC-5의 미가용 조건도 registry 주입이라는 비파괴 수단으로만 만든다.
    """

    @staticmethod
    def _orca_session_available() -> bool:
        """실 Orca 세션이 있는가. 없으면 AC-4는 skip이다 — H-2에 따라 대역으로
        pass를 만들지 않는다."""
        candidates, _ = e2e_drivers.resolve_candidates()
        return any(
            item.get("outcome") == "selected" and item.get("session_mode") == "orca-managed"
            for item in candidates
        )

    def _run_fixture(self, scenario):
        with tempfile.TemporaryDirectory() as task_path, \
                tempfile.TemporaryDirectory() as artifact_dir:
            pathlib.Path(task_path, "test-scenario.json").write_text(
                json.dumps(
                    {"schema_version": e2e_contract.E2E_CONTRACT_SCHEMA_VERSION,
                     "task_id": "acceptance", "locked": False, "scenarios": [scenario]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            os.environ["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir
            try:
                payload = e2e_orchestrator.run_e2e(
                    target=e2e_target.TARGET_SOURCE_WORKTREE,
                    scenario_id=scenario["id"],
                    task_path=task_path,
                    worktree_root=str(_SOURCE_ROOT),
                )
                artifacts = {
                    name: json.loads(pathlib.Path(artifact_dir, name).read_text(encoding="utf-8"))
                    for name in ("run.json", "journal.json", "owned.json",
                                 "assertions.json", "cleanup.json")
                }
                artifacts["actions.jsonl"] = [
                    json.loads(line)
                    for line in pathlib.Path(artifact_dir, "actions.jsonl")
                    .read_text(encoding="utf-8").splitlines() if line.strip()
                ]
            finally:
                os.environ.pop("OPAL_E2E_ARTIFACT_DIR", None)
        return payload, artifacts

    def test_ac4_real_browser_run_passes_with_a_semantic_assertion(self):
        """AC-4 — 실 Orca 세션에서 실제 UI 행동 + semantic assertion으로 `pass`.

        assertion은 브라우저에서 **실제로 읽어 온 값**과 비교한다. `match`는 `equals`여야
        한다 — `e2e_contract.validate_pass_requirements`가 `expected != actual`을 직접
        비교하므로(§A.5) `contains`로 통과한 driver 판정도 계약 게이트에서 `fail`이 된다.
        """
        if not self._orca_session_available():
            self.skipTest("no selectable orca-managed browser candidate on this machine")

        payload, art = self._run_fixture({
            "id": "ac4-browser", "surface_kind": "browser", "profile": "browser",
            "actors": ["browser"], "required_fidelity": "real-usage",
            "steps": [{"id": "st-reload", "executor": "browser",
                       "step_role": "verify", "kind": "reload"}],
            "assertions": [
                {"id": "ac4-title", "verifier": "title", "match": "equals",
                 "expected": "OPAL Console"},
            ],
            "required_evidence": ["metadata", "action_log", "assertions", "cleanup"],
        })
        run_json = art["run.json"]
        self.assertEqual(payload["status"], "pass", f"AC-4 must pass: {run_json.get('detail')}")
        self.assertEqual(payload["exit_code"], e2e_contract.status_to_exit("pass"))
        self.assertTrue(payload["executed"])
        # 실 UI 행동이 실제로 일어났다 — 행동 기록이 증거다.
        self.assertIn("reload", [row["action"] for row in art["actions.jsonl"]])
        self.assertEqual(run_json["observed_executors"], ["browser"])
        self.assertEqual(run_json["fidelity"], e2e_orchestrator.FIDELITY_REAL_USAGE)
        self.assertTrue(run_json["evidence_complete"])
        self.assertEqual(run_json["missing_evidence"], [])
        # assertion은 브라우저에서 읽어 온 실제 값으로 판정됐다(§A.5).
        for result in art["assertions.json"]["results"]:
            self.assertIn("expected", result)
            self.assertIn("actual", result)
            self.assertEqual(result["expected"], result["actual"])
        # 후보 탐색 기록이 남는다(§A.1.2).
        self.assertTrue(run_json["candidates"])
        self.assertTrue(run_json["executors"], "선택된 실행 수단이 §A.1.1에 기록돼야 한다")

    def test_ac4_cleanup_touches_only_the_page_this_run_opened(self):
        """[MUST] AC-4·C-2 — run이 만든 `browserPageId`만 정리되고 사용자 탭은 남는다."""
        if not self._orca_session_available():
            self.skipTest("no selectable orca-managed browser candidate on this machine")

        payload, art = self._run_fixture({
            "id": "ac4-cleanup", "surface_kind": "browser", "profile": "browser",
            "actors": ["browser"],
            "steps": [{"id": "st-reload", "executor": "browser",
                       "step_role": "verify", "kind": "reload"}],
            "assertions": [{"id": "a1", "verifier": "title", "match": "equals",
                            "expected": "OPAL Console"}],
            "required_evidence": ["metadata"],
        })
        pages = art["owned.json"]["browser_pages"]
        self.assertEqual(len(pages), 1, f"run이 연 page 1건만 대장에 올라야 한다: {pages}")
        # 대장 id는 run 전용이다 — 사용자 세션 이름(`default`)과 구분되지 않으면
        # 정리가 남의 자원을 겨냥할 수 있다.
        self.assertEqual(pages[0]["page_id"], payload["run_id"])
        self.assertFalse(pages[0]["user_owned"])
        self.assertEqual(art["cleanup.json"]["result"], "complete")
        self.assertEqual(art["cleanup.json"]["leaked"], [])
        # 사용자 세션은 여전히 살아 있다 — 후보가 다시 selected되는 것이 그 증거다.
        self.assertTrue(
            self._orca_session_available(),
            "cleanup 이후에도 사용자 Orca 세션은 그대로 있어야 한다(C-2)",
        )

    def test_ac5_provider_unavailable_walks_the_candidate_order_and_records_why(self):
        """AC-5 — Orca runtime 미가용 → 다음 후보 전환. 경위가 `candidates[]`에 남는다.

        미가용 조건은 **registry 주입**으로만 만든다(비파괴) — 사용자 세션을 닫아
        재현하지 않는다. standalone 바이너리는 PATH에 없으므로 전환 후 후보가 소진되고
        `executor_unavailable`로 끝나는 것이 정상이다. pass를 만들려고 바이너리를
        설치하지 않는다(H-2).
        """
        from lib.e2e.drivers import agent_browser as ab

        class _OrcaRuntimeUnavailable(ab.AgentBrowserDriver):
            def op_probe(self, request):
                return {
                    "driver": self.name, "session_mode": self.session_mode,
                    "available": False, "version": self.declared_version,
                    "unavailable_reason": "orca_runtime_no_active_session",
                    "capabilities": e2e_drivers.default_capabilities(),
                }

        registry = dict(e2e_drivers.registered_drivers())
        registry[("agent-browser", "orca-managed")] = (
            lambda **kw: _OrcaRuntimeUnavailable(session_mode="orca-managed", **kw)
        )
        candidates, probes = e2e_drivers.resolve_candidates(registry=registry)

        by_order = {item["order"]: item for item in candidates}
        self.assertEqual(by_order[1]["session_mode"], "orca-managed")
        self.assertEqual(by_order[1]["outcome"], "provider_unavailable")
        self.assertEqual(by_order[1]["reason"], "orca_runtime_no_active_session")
        # 전환이 실제로 일어났다 — 뒤 후보가 "시도되지 않음"이 아니라 자기 사유를 갖는다.
        self.assertNotEqual(by_order[2]["reason"], "not_attempted_after_selection")
        self.assertEqual(by_order[3]["session_mode"], "standalone")
        self.assertEqual(by_order[3]["reason"], "agent_browser_binary_not_found")
        # 후보 소진 → selected 0건. 대역으로 채우지 않는다.
        self.assertEqual([item for item in candidates if item["outcome"] == "selected"], [])
        # [MUST] 전환이 허용되는 분류는 provider_unavailable뿐이다(TASK.md C-3, §C.7).
        self.assertTrue(e2e_contract.can_try_next_provider({"status": "provider_unavailable"}))
        self.assertFalse(e2e_contract.can_try_next_provider({"status": "infra_error"}))
        # §A.8 — 판정 근거인 probe 결과가 후보마다 기록된다.
        self.assertEqual(len(probes), len(candidates))
