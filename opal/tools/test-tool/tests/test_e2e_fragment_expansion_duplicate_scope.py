"""T05 — 조각 전개, actions 단위, S-27 중복 signature 범위를 검증한다."""

from __future__ import annotations

import os
import pathlib
import tempfile
import unittest
from unittest import mock

from lib.e2e.fragment import parse_fragment_document
from lib.e2e.journey import expand_journey, parse_journey_document
from lib.e2e.orchestrator import _load_scenario
from lib.e2e.scenario_adapter import build_execution_plan, scoped_operation_signature


def _fragment():
    return parse_fragment_document(
        """```yaml
id: login
params: [user_ref]
steps:
  - {id: open, kind: navigate, target: /login}
  - {id: user, kind: fill, target: '#id', value_ref: '{user_ref}'}
postconditions:
  - {id: landed, verifier: url, expected: /dashboard}
```"""
    )


class TestFragmentExpansionDuplicateScope(unittest.TestCase):
    def test_fragment_and_journey_duplicate_operations_are_both_preserved(self):
        journey = parse_journey_document(
            """```yaml
id: duplicate-scope
profile: browser
surface_kind: browser
actors: [browser]
required_evidence: [metadata, actions]
steps:
  - {fragment: login, with: {user_ref: TEST_LOGIN_ID}}
  - {id: body-open, kind: navigate, target: /login}
assertions: []
```"""
        )
        scenario = expand_journey(journey, {"login": _fragment()})

        navigate = [step for step in scenario["steps"] if step.get("kind") == "navigate"]
        self.assertEqual(len(navigate), 2, "expansion must not deduplicate real operations")
        self.assertEqual(navigate[0]["origin_scope"], "fragment")
        self.assertEqual(navigate[1]["origin_scope"], "journey")

        with mock.patch.dict(os.environ, {"TEST_LOGIN_ID": "captain@example.test"}, clear=False):
            plan = build_execution_plan(scenario)
        signatures = [scoped_operation_signature(step) for step in plan if step.action.get("kind") == "navigate"]
        self.assertNotEqual(signatures[0], signatures[1])
        self.assertEqual([step.action["kind"] for step in plan], ["navigate", "fill", "navigate"])
        self.assertEqual(plan[1].action["value"], "captain@example.test")
        self.assertNotIn("value_ref", plan[1].action)

    def test_fragment_postcondition_becomes_semantic_assertion(self):
        journey = {
            "id": "postcondition",
            "steps": [{"fragment": "login", "with": {"user_ref": "TEST_LOGIN_ID"}}],
            "assertions": [],
        }
        scenario = expand_journey(journey, {"login": _fragment()})
        self.assertEqual(len(scenario["assertions"]), 1)
        self.assertTrue(scenario["assertions"][0]["id"].startswith("fragment:login:1:"))

    def test_orchestrator_reads_project_library_without_copying_scenario(self):
        with tempfile.TemporaryDirectory() as temp:
            project = pathlib.Path(temp)
            task = project / "task"
            fragments = project / "docs" / "e2e" / "fragments"
            journeys = project / "docs" / "e2e" / "journeys"
            task.mkdir(parents=True)
            fragments.mkdir(parents=True)
            journeys.mkdir(parents=True)
            (fragments / "login.md").write_text(
                """```yaml
id: login
params: []
steps:
  - {id: open, kind: navigate, target: /login}
postconditions:
  - {id: landed, verifier: url, expected: /dashboard}
```""",
                encoding="utf-8",
            )
            (journeys / "library-run.md").write_text(
                """```yaml
id: library-run
profile: browser
surface_kind: browser
actors: [browser]
required_evidence: [metadata, actions]
steps:
  - {fragment: login, with: {}}
assertions: []
```""",
                encoding="utf-8",
            )
            scenario, detail_code, detail, contract_check = _load_scenario(
                str(task), "library-run", project_root=str(project)
            )
        self.assertIsNone(detail_code, detail)
        self.assertIsNone(contract_check)
        self.assertEqual(scenario["steps"][0]["kind"], "navigate")
        self.assertEqual(scenario["assertions"][0]["expected"], "/dashboard")


if __name__ == "__main__":
    unittest.main()
