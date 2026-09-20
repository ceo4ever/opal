"""T03 — 시나리오 요구 연산을 추출하고 부분 driver를 실행 전에 제외하는 gate 검증."""
from __future__ import annotations

import pathlib
import sys
import unittest
from unittest import mock

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

from lib.e2e import drivers as e2e_drivers  # noqa: E402
from lib.e2e import orchestrator  # noqa: E402
from lib.e2e import scenario_adapter  # noqa: E402


def _manifest():
    return {
        "schema_version": "1.0",
        "drivers": {"stub": {"minimum_version": "0.0.0", "tested_range": "*", "ci_pin": "0.0.0"}},
    }


class _GateDriver(e2e_drivers.BrowserDriver):
    name = "stub"
    session_mode = "standalone"

    def __init__(self, operations, **_kwargs):
        self.operations = tuple(operations)
        self.dispatched = []

    def op_probe(self, _request):
        self.dispatched.append("probe")
        return {"available": True, "version": "0.0.0", "capabilities": e2e_drivers.default_capabilities()}


class TestRequiredOperationExtraction(unittest.TestCase):
    def test_browser_action_requires_lifecycle_act_and_assert(self):
        scenario = {
            "steps": [{"id": "click", "executor": "browser", "kind": "click"}],
            "assertions": [{"id": "visible", "executor": "browser"}],
        }
        self.assertEqual(
            scenario_adapter.required_driver_operations(scenario),
            ("probe", "open", "act", "assert", "capture", "close"),
        )

    def test_explicit_wait_snapshot_and_capture_steps_are_preserved(self):
        scenario = {
            "steps": [
                {"executor": "browser", "operation": "wait"},
                {"executor": "browser", "driver_operation": "snapshot"},
                {"executor": "browser", "operation": "capture"},
            ]
        }
        self.assertEqual(
            scenario_adapter.required_driver_operations(scenario),
            ("probe", "open", "snapshot", "wait", "capture", "close"),
        )


class TestPreExecutionOperationGate(unittest.TestCase):
    def _resolve(self, operations, required):
        instances = []

        def factory(**kwargs):
            instance = _GateDriver(operations, **kwargs)
            instances.append(instance)
            return instance

        candidates, _ = e2e_drivers.resolve_candidates(
            required_operations=required,
            manifest=_manifest(),
            registry={("stub", "standalone"): factory},
            candidate_order=({"driver": "stub", "session_mode": "standalone", "opt_in": False},),
        )
        return candidates[0], instances[0]

    def test_partial_driver_is_excluded_before_any_scenario_operation_dispatch(self):
        record, instance = self._resolve(("probe", "open", "close"), ("probe", "open", "act", "close"))
        self.assertEqual(record["outcome"], e2e_drivers.OUTCOME_EXCLUDED)
        self.assertEqual(record["excluded_by"], e2e_drivers.EXCLUDED_BY_CAPABILITY_MISSING)
        self.assertEqual(record["reason"], "missing_operations:act")
        self.assertEqual(instance.dispatched, ["probe"])

    def test_python_override_driver_is_gated_without_an_operations_declaration(self):
        class _OverrideOnlyDriver(e2e_drivers.BrowserDriver):
            name = "stub"
            session_mode = "standalone"

            def __init__(self, **_kwargs):
                self.dispatched = []

            def op_probe(self, _request):
                self.dispatched.append("probe")
                return {
                    "available": True,
                    "version": "0.0.0",
                    "capabilities": e2e_drivers.default_capabilities(),
                }

            def op_open(self, _request):
                return {"handle": "page-1", "owned": True, "current_url": "about:blank"}

            def op_close(self, _request):
                return {"closed": True, "released": ["page-1"], "leaked": []}

        instances = []

        def factory(**kwargs):
            instance = _OverrideOnlyDriver(**kwargs)
            instances.append(instance)
            return instance

        candidates, _ = e2e_drivers.resolve_candidates(
            required_operations=("probe", "open", "act", "close"),
            manifest=_manifest(),
            registry={("stub", "standalone"): factory},
            candidate_order=({"driver": "stub", "session_mode": "standalone", "opt_in": False},),
        )

        self.assertEqual(candidates[0]["outcome"], e2e_drivers.OUTCOME_EXCLUDED)
        self.assertEqual(candidates[0]["reason"], "missing_operations:act")
        self.assertEqual(instances[0].dispatched, ["probe"])

    def test_complete_driver_is_selected(self):
        record, instance = self._resolve(e2e_drivers.DRIVER_OPERATIONS, e2e_drivers.DRIVER_OPERATIONS)
        self.assertEqual(record["outcome"], e2e_drivers.OUTCOME_SELECTED)
        self.assertEqual(instance.dispatched, ["probe"])

    def test_orchestrator_passes_extracted_operations_to_candidate_resolution(self):
        scenario = {
            "profile": "browser",
            "steps": [{"id": "s1", "executor": "browser", "kind": "click"}],
            "assertions": [{"id": "a1", "executor": "browser"}],
        }
        with mock.patch.object(orchestrator.e2e_drivers, "resolve_candidates", return_value=([], [])) as resolve:
            orchestrator._resolve_executor_candidates(scenario)
        self.assertEqual(
            resolve.call_args.kwargs["required_operations"],
            scenario_adapter.required_driver_operations(scenario),
        )


if __name__ == "__main__":
    unittest.main()
