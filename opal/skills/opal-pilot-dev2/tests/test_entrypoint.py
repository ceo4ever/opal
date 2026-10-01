"""
@header {
  "module": "test_entrypoint",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "opal-pilot-dev2/scripts/opd2.py의 resolve-start 서브커맨드 계약 — mode·workspace 판정 매트릭스, 재개 시 axis 잠금, 충돌 플래그 거부, 다른 Pilot skill 거부를 subprocess CLI 호출로 검증한다.",
  "exports": ["EntrypointTests"],
  "depends": ["opal-pilot-dev2/scripts/opd2"]
}
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/opd2.py"


class EntrypointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="opd2-test-")
        self.addCleanup(self.temp.cleanup)
        self.task = Path(self.temp.name) / "task"
        self.task.mkdir()

    def run_cli(self, *flags):
        return subprocess.run([sys.executable, str(SCRIPT), "resolve-start", str(self.task), *flags],
                              capture_output=True, text=True)

    def saved(self, **changes):
        data = {"skill": "opd2", "mode": "semi-agentic", "actor": "coordinator", "rows": []}
        data.update(changes)
        (self.task / "state.json").write_text(json.dumps(data))

    def test_default(self):
        result = self.run_cli("--new-task")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual((data["effective_mode"], data["workspace"], data["entrypoint"]),
                         ("agentic", "worktree", "opd2"))
        self.assertFalse((self.task / "state.json").exists())

    def test_mode_workspace_matrix(self):
        for mode in ("semi-agentic", "agentic"):
            for flag, expected in (("--wt", "worktree"), ("--no-wt", "hub")):
                with self.subTest(mode=mode, flag=flag):
                    result = self.run_cli("--new-task", "--" + mode, flag)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    data = json.loads(result.stdout)
                    self.assertEqual(data["effective_mode"], mode)
                    self.assertEqual(data["workspace"], expected)

    def test_conflicts_and_unsupported_mode(self):
        for flags in (("--agentic", "--semi-agentic"), ("--wt", "--no-wt"), ("--interactive",)):
            with self.subTest(flags=flags):
                self.assertNotEqual(self.run_cli("--new-task", *flags).returncode, 0)
                self.assertFalse((self.task / "state.json").exists())

    def test_resume_preserves_mode(self):
        self.saved()
        before = (self.task / "state.json").read_bytes()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["effective_mode"], "semi-agentic")
        self.assertEqual((self.task / "state.json").read_bytes(), before)

    def test_resume_workspace_change_rejected(self):
        self.saved()
        result = self.run_cli("--wt")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("resume_axis_locked", result.stdout)

    def test_invalid_saved_mode(self):
        self.saved(mode="invalid")
        self.assertIn("unsupported_stored_mode", self.run_cli().stdout)

    def test_missing_resume_and_existing_new(self):
        self.assertIn("resume_state_missing", self.run_cli().stdout)
        self.saved()
        self.assertIn("task_already_exists", self.run_cli("--new-task").stdout)

    def test_malformed_state(self):
        (self.task / "state.json").write_text("{")
        self.assertIn("state_json_malformed", self.run_cli().stdout)

    def test_other_pilot_rejected(self):
        self.saved(skill="oppb")
        self.assertIn("incompatible_engine_skill", self.run_cli().stdout)


if __name__ == "__main__":
    unittest.main()
