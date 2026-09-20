"""T05 — 조각 등록 계약과 프로젝트 시드를 검증한다."""

from __future__ import annotations

import pathlib
import tempfile
import unittest

from lib.e2e.fragment import FragmentError, load_fragment_registry, parse_fragment_document
from lib.e2e import orchestrator


class TestFragmentRegistry(unittest.TestCase):
    def test_postcondition_is_required(self):
        with self.assertRaises(FragmentError) as raised:
            parse_fragment_document(
                """```yaml
id: no-proof
params: []
steps:
  - {id: open, kind: navigate, target: /}
```"""
            )
        self.assertEqual(raised.exception.detail_code, "fragment_postcondition_required")

    def test_inline_fill_secret_is_rejected(self):
        with self.assertRaises(FragmentError) as raised:
            parse_fragment_document(
                """```yaml
id: unsafe
params: []
steps:
  - {id: password, kind: fill, target: '#pw', value: secret}
postconditions:
  - {verifier: url, expected: /dashboard}
```"""
            )
        self.assertEqual(raised.exception.detail_code, "fragment_secret_value_forbidden")

    def test_registry_loads_valid_document(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / "login.md").write_text(
                """```yaml
id: login
params: [user_ref]
steps:
  - {id: user, kind: fill, target: '#id', value_ref: '{user_ref}'}
postconditions:
  - {id: url, verifier: url, expected: /dashboard}
```""",
                encoding="utf-8",
            )
            registry = load_fragment_registry(root)
        self.assertEqual(list(registry), ["login"])
        self.assertEqual(registry["login"]["postconditions"][0]["verifier"], "url")

    def test_project_login_seed_is_registered(self):
        source = pathlib.Path(__file__).resolve()
        project_root = next(
            (
                root
                for root in (source.parents[4], source.parents[3])
                if (root / "docs" / "e2e" / "fragments").is_dir()
            ),
            None,
        )
        if project_root is None:
            self.skipTest("project E2E seeds are not part of the installed test-tool layout")
        registry = load_fragment_registry(project_root / "docs" / "e2e" / "fragments")
        self.assertIn("login", registry)
        self.assertTrue(registry["login"]["postconditions"])

    def test_library_journey_id_cannot_escape_the_journeys_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            task = root / "task"
            task.mkdir()
            outside = root / "docs" / "outside.md"
            outside.parent.mkdir(parents=True)
            outside.write_text(
                """```yaml
id: outside
steps:
  - {id: open, executor: browser, step_role: verify, action: open}
assertions: []
```""",
                encoding="utf-8",
            )
            scenario, detail_code, detail, _check = orchestrator._load_scenario(
                str(task), "../../outside", project_root=str(root)
            )
        self.assertIsNone(scenario)
        self.assertEqual(detail_code, "e2e_scenario_contract_invalid")
        self.assertIn("single filename", detail)


if __name__ == "__main__":
    unittest.main()
