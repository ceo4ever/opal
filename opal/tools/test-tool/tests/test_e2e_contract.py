"""
@header {
  "module": "test_e2e_contract",
  "task": "125",
  "layer": "test",
  "domain": "opal-tools",
  "description": "E2E profile/verdict contract and PM correction boundary regression tests for TEST-SCENARIO S-1~S-8.",
  "scenarios": ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-8"],
  "exports": [
    "TestS1ProfileMatrix",
    "TestS2StatusExitMapping",
    "TestS3LegacyMigration",
    "TestS4ProviderSwitch",
    "TestS5PassEvidenceGate",
    "TestS6SurfaceAndHybrid",
    "TestS7HumanContract",
    "TestS8ScenarioVersionBoundary",
    "TestCorrectionHandoffContract"
  ]
}

Public regression tests for the E2E contract owner introduced by PLAN W-1. Each
scenario imports the public owner lazily and protects the S-1~S-8 contract plus
PM correction boundaries without coupling to implementation-private helpers.
"""

import importlib
import json
import pathlib
import sys
import unittest


_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

_RESULT_KEYS = {"ok", "status", "error", "detail", "normalized"}
_LEGACY_OUTPUT_KEYS = {"fallback", "fallback_reason", "escalated", "escalate", "escalation"}


def _contract():
    """Load the public contract owner at test execution time."""
    return importlib.import_module("lib.e2e_contract")


def _assert_result_shape(testcase, result):
    testcase.assertIsInstance(result, dict)
    testcase.assertTrue(set(result).issubset(_RESULT_KEYS), result)
    testcase.assertIn("ok", result)
    testcase.assertIn("status", result)
    testcase.assertIn("error", result)
    testcase.assertIn("detail", result)
    testcase.assertIn("normalized", result)


def _assert_no_legacy_output(testcase, value):
    if isinstance(value, dict):
        testcase.assertFalse(_LEGACY_OUTPUT_KEYS.intersection(value), value)
        for item in value.values():
            _assert_no_legacy_output(testcase, item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_legacy_output(testcase, item)
    elif isinstance(value, str):
        testcase.assertNotIn(value, {"fallback", "escalated", "escalate", "escalation"})


class TestS1ProfileMatrix(unittest.TestCase):
    """S-1: five profiles, executor matrix, and surface/profile mismatch."""

    def test_five_profiles_and_executor_matrix(self):
        c = _contract()
        self.assertEqual(
            c.PROFILES,
            ("browser", "api", "hybrid", "collaborative", "manual"),
        )
        self.assertEqual(c.EXECUTOR_TYPES, ("browser", "api", "human"))
        expected = {
            "browser": {"required": ("browser",), "allowed": ("browser",)},
            "api": {"required": ("api",), "allowed": ("api",)},
            "hybrid": {
                "required": ("api", "browser"),
                "allowed": ("api", "browser"),
            },
            "collaborative": {
                "required": ("human",),
                "allowed": ("browser", "api", "human"),
            },
            "manual": {"required": ("human",), "allowed": ("human",)},
        }
        self.assertEqual(c.EXECUTOR_MATRIX, expected)
        for profile, matrix in expected.items():
            with self.subTest(profile=profile):
                self.assertEqual(c.executor_contract(profile), matrix)

    def test_profile_is_resolved_from_public_surface_not_tool_availability(self):
        c = _contract()
        cases = (
            ({"kind": "web_ui"}, ("user",), "browser"),
            ({"kind": "api"}, ("service",), "api"),
            ({"kind": "hybrid"}, ("user", "service"), "hybrid"),
            ({"kind": "collaborative"}, ("human", "agent"), "collaborative"),
            ({"kind": "manual"}, ("human",), "manual"),
        )
        for surface, actors, expected in cases:
            with self.subTest(surface=surface):
                result = c.resolve_profile(surface, actors=actors)
                _assert_result_shape(self, result)
                self.assertTrue(result["ok"], result)
                self.assertEqual(result["normalized"]["profile"], expected)

    def test_surface_profile_mismatches_are_rejected(self):
        c = _contract()
        for profile, surface_kind, actors in (
            ("api", "web_ui", ("user",)),
            ("browser", "api", ("service",)),
            ("hybrid", "web_ui", ("user",)),
        ):
            with self.subTest(profile=profile, surface_kind=surface_kind):
                result = c.validate_surface_match(profile, surface_kind, actors)
                _assert_result_shape(self, result)
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["status"], "fail")
                self.assertEqual(result["error"], "surface_profile_mismatch")


class TestS2StatusExitMapping(unittest.TestCase):
    """S-2: final/operational state split and process exit mapping."""

    def test_status_sets_and_exit_error_mapping(self):
        c = _contract()
        self.assertEqual(
            c.FINAL_STATUSES,
            ("pass", "fail", "executor_unavailable", "infra_error", "blocked"),
        )
        self.assertEqual(c.OPERATIONAL_STATUSES, ("awaiting_human",))
        self.assertNotIn("awaiting_human", c.FINAL_STATUSES)
        exits = {
            "pass": 0,
            "fail": 6,
            "infra_error": 7,
            "executor_unavailable": 18,
            "blocked": 19,
            "awaiting_human": 20,
        }
        errors = {
            "pass": None,
            "fail": "e2e_failed",
            "infra_error": "e2e_infra_error",
            "executor_unavailable": "executor_unavailable",
            "blocked": "e2e_blocked",
            "awaiting_human": "e2e_awaiting_human",
        }
        self.assertEqual(c.STATUS_EXIT_CODES, exits)
        self.assertEqual(c.STATUS_ERROR_CODES, {k: v for k, v in errors.items() if v is not None})
        for status, exit_code in exits.items():
            with self.subTest(status=status):
                self.assertEqual(c.status_to_exit(status), exit_code)
                self.assertEqual(c.status_to_error(status), errors[status])


class TestS3LegacyMigration(unittest.TestCase):
    """S-3: reason/wait-kind migration and removal of legacy output vocabulary."""

    def test_legacy_reason_matrix(self):
        c = _contract()
        cases = (
            ({"status": "fallback", "fallback_reason": "not_in_cmux"}, "provider_unavailable"),
            ({"status": "fallback", "fallback_reason": "cmux_not_installed"}, "provider_unavailable"),
            ({"status": "fallback", "fallback_reason": "open_failed"}, "infra_error"),
            ({"status": "fallback", "fallback_reason": "surface_parse_failed"}, "infra_error"),
            ({"status": "fallback", "fallback_reason": "cmux not configured", "has_cmux": False}, "infra_error"),
            ({"status": "escalated", "error": "usage", "escalate": True}, "infra_error"),
            ({"status": "escalated", "error": "invalid_surface", "escalate": True}, "infra_error"),
            ({"status": "escalated", "error": "goto_failed", "escalate": True}, "infra_error"),
            ({"status": "escalated", "error": "eval_failed", "escalate": True}, "infra_error"),
            ({"status": "fallback"}, "infra_error"),
            ({"status": "escalated", "error": "unknown_driver_error"}, "infra_error"),
        )
        for payload, status in cases:
            with self.subTest(payload=payload):
                result = c.normalize_legacy_verdict(payload)
                _assert_result_shape(self, result)
                self.assertEqual(result["status"], status, result)
                _assert_no_legacy_output(self, result)

    def test_wait_failed_requires_explicit_assertion_kind_to_be_product_fail(self):
        c = _contract()
        expected = {
            "assertion_condition": "fail",
            "navigation_ready": "infra_error",
            "transport": "infra_error",
            None: "infra_error",
        }
        for wait_kind, status in expected.items():
            with self.subTest(wait_kind=wait_kind):
                payload = {"status": "escalated", "error": "wait_failed"}
                if wait_kind is not None:
                    payload["wait_kind"] = wait_kind
                result = c.normalize_legacy_verdict(payload)
                self.assertEqual(result["status"], status, result)
                _assert_no_legacy_output(self, result)


class TestS4ProviderSwitch(unittest.TestCase):
    """S-4: only provider_unavailable permits the next Browser candidate."""

    def test_only_provider_unavailable_can_try_next_provider(self):
        c = _contract()
        self.assertTrue(c.can_try_next_provider({"status": "provider_unavailable"}))
        self.assertTrue(
            c.can_try_next_provider({"status": "fallback", "fallback_reason": "not_in_cmux"})
        )
        self.assertTrue(
            c.can_try_next_provider({"status": "fallback", "fallback_reason": "cmux_not_installed"})
        )
        for candidate in (
            {"status": "fail", "error": "assertion_failed"},
            {"status": "fail", "error": "product_failure"},
            {"status": "fail", "error": "authentication_failed"},
            {"status": "fail", "error": "data_mismatch"},
            {"status": "fail", "error": "evidence_missing"},
            {"status": "infra_error", "error": "goto_failed"},
        ):
            with self.subTest(candidate=candidate):
                self.assertFalse(c.can_try_next_provider(candidate))


class TestS5PassEvidenceGate(unittest.TestCase):
    """S-5: semantic assertions and required evidence gate pass/real-usage."""

    def setUp(self):
        self.c = _contract()
        self.scenario = {
            "profile": "browser",
            "required_evidence": ["screenshot", "trace"],
            "assertions": [{"id": "heading", "expected": "Dashboard"}],
        }
        self.complete = {
            "status": "pass",
            "fidelity": "real-usage",
            "observed_executors": ["browser"],
            "assertion_results": [
                {"id": "heading", "expected": "Dashboard", "actual": "Dashboard"}
            ],
            "observed_evidence": ["screenshot", "trace"],
        }

    def test_missing_expected_actual_or_required_evidence_is_rejected(self):
        missing_actual = dict(self.complete)
        missing_actual["assertion_results"] = [{"id": "heading", "expected": "Dashboard"}]
        missing_evidence = dict(self.complete)
        missing_evidence["observed_evidence"] = ["screenshot"]
        for result in (missing_actual, missing_evidence):
            with self.subTest(result=result):
                verdict = self.c.validate_pass_requirements(self.scenario, result)
                _assert_result_shape(self, verdict)
                self.assertFalse(verdict["ok"], verdict)
                self.assertNotEqual(verdict["status"], "pass")
                self.assertTrue(verdict["error"])

    def test_only_complete_semantic_assertions_and_evidence_pass(self):
        verdict = self.c.validate_pass_requirements(self.scenario, self.complete)
        _assert_result_shape(self, verdict)
        self.assertTrue(verdict["ok"], verdict)
        self.assertEqual(verdict["status"], "pass")
        self.assertEqual(verdict["normalized"]["fidelity"], "real-usage")

    def test_open_navigate_close_alone_cannot_build_pass_verdict(self):
        verdict = self.c.build_verdict({
            "status": "pass",
            "profile": "browser",
            "observed_executors": ["browser"],
            "events": ["open", "navigate", "close"],
            "assertion_results": [],
            "required_evidence": ["screenshot"],
            "observed_evidence": [],
        })
        _assert_result_shape(self, verdict)
        self.assertFalse(verdict["ok"], verdict)
        self.assertNotEqual(verdict["status"], "pass")


class TestS6SurfaceAndHybrid(unittest.TestCase):
    """S-6: API-only UI is rejected and Hybrid requires both verification axes."""

    def test_api_only_executor_cannot_satisfy_web_ui(self):
        c = _contract()
        verdict = c.validate_pass_requirements(
            {
                "surface_kind": "web_ui",
                "profile": "browser",
                "required_evidence": ["ui_screenshot"],
                "assertions": [{"id": "ui", "expected": "visible"}],
            },
            {
                "status": "pass",
                "observed_executors": ["api"],
                "assertion_results": [{"id": "ui", "expected": "visible", "actual": "visible"}],
                "observed_evidence": ["api_response"],
            },
        )
        self.assertFalse(verdict["ok"], verdict)
        self.assertEqual(verdict["error"], "surface_profile_mismatch")

    def test_hybrid_requires_browser_and_api_assertion_evidence(self):
        c = _contract()
        scenario = {
            "surface_kind": "hybrid",
            "profile": "hybrid",
            "required_evidence": ["ui_screenshot", "api_response", "state_snapshot"],
            "assertions": [
                {"id": "ui_action", "executor": "browser", "expected": "submitted"},
                {"id": "api_state", "executor": "api", "expected": "persisted"},
            ],
        }
        complete = {
            "status": "pass",
            "fidelity": "real-usage",
            "observed_executors": ["browser", "api"],
            "assertion_results": [
                {"id": "ui_action", "executor": "browser", "expected": "submitted", "actual": "submitted"},
                {"id": "api_state", "executor": "api", "expected": "persisted", "actual": "persisted"},
            ],
            "observed_evidence": ["ui_screenshot", "api_response", "state_snapshot"],
        }
        self.assertTrue(c.validate_pass_requirements(scenario, complete)["ok"])
        for missing_executor in ("browser", "api"):
            with self.subTest(missing_executor=missing_executor):
                result = dict(complete)
                result["observed_executors"] = [
                    item for item in complete["observed_executors"] if item != missing_executor
                ]
                verdict = c.validate_pass_requirements(scenario, result)
                self.assertFalse(verdict["ok"], verdict)


class TestS7HumanContract(unittest.TestCase):
    """S-7 unit boundary: handoff is operational and free-form completion is not pass."""

    def test_structured_handoff_contract_is_valid_but_free_form_pass_is_not(self):
        c = _contract()
        scenario = {
            "id": "S-7",
            "profile": "collaborative",
            "surface_kind": "collaborative",
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
        valid = c.validate_scenario_contract({"schema_version": "2.0", "scenarios": [scenario]})
        _assert_result_shape(self, valid)
        self.assertTrue(valid["ok"], valid)
        free_form = c.build_verdict({
            "status": "pass",
            "profile": "collaborative",
            "human_message": "done",
            "assertion_results": [],
            "observed_evidence": [],
        })
        self.assertFalse(free_form["ok"], free_form)
        self.assertNotEqual(free_form["status"], "pass")


class TestS8ScenarioVersionBoundary(unittest.TestCase):
    """S-8 unit boundary: v1 defaults are explicit; invalid v2 is strict."""

    def test_v1_is_accepted_only_through_legacy_defaults(self):
        c = _contract()
        legacy = {
            "schema_version": "1.0",
            "scenarios": [{"id": "S1", "type": "unit", "expected": "legacy"}],
        }
        accepted = c.validate_scenario_contract(legacy, legacy_defaults=True)
        self.assertTrue(accepted["ok"], accepted)
        normalized_scenario = accepted["normalized"]["scenarios"][0]
        self.assertEqual(normalized_scenario["required_fidelity"], "mock")
        self.assertIsNone(normalized_scenario["profile"])
        self.assertEqual(normalized_scenario["required_evidence"], [])
        rejected = c.validate_scenario_contract(legacy, legacy_defaults=False)
        self.assertFalse(rejected["ok"], rejected)

    def test_v2_rejects_invalid_enum_and_surface_executor_contract(self):
        c = _contract()
        invalid_specs = (
            {
                "schema_version": "2.0",
                "scenarios": [{"id": "S1", "profile": "desktop", "surface_kind": "web_ui"}],
            },
            {
                "schema_version": "2.0",
                "scenarios": [{
                    "id": "S1",
                    "profile": "browser",
                    "surface_kind": "web_ui",
                    "actors": ["user"],
                    "steps": [{"id": "call", "executor": "api"}],
                    "assertions": [],
                    "required_evidence": [],
                }],
            },
        )
        for spec in invalid_specs:
            with self.subTest(spec=spec):
                result = c.validate_scenario_contract(spec, legacy_defaults=False)
                self.assertFalse(result["ok"], result)


class TestCorrectionHandoffContract(unittest.TestCase):
    """PM correction: the public handoff contract owns all eight resume fields."""

    def test_handoff_required_fields_include_server_policy(self):
        c = _contract()
        self.assertEqual(
            c.HANDOFF_REQUIRED_FIELDS,
            (
                "handoff_id",
                "instruction",
                "expected_observation",
                "required_evidence",
                "timeout_seconds",
                "resume_token",
                "server_policy",
                "submission_path",
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
