"""
@header {
  "module": "test_mode_resolution",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "Task 134 effective mode resolver public CLI RED contract",
  "exports": [],
  "depends": ["state_tool"]
}
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[4]
STATE_TOOL = REPO_ROOT / "opal" / "tools" / "state-tool" / "state_tool.py"
MODES = ("interactive", "semi-agentic", "agentic")
ROWS = json.dumps([
    {"stage": "TASK", "item": "work"},
    {"stage": "TASK", "item": "사용자 확인"},
    {"stage": "EXECUTE", "item": "work"},
], ensure_ascii=False)


class ModeResolutionCliContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _run(self, *args: str) -> tuple[subprocess.CompletedProcess[str], dict | None]:
        completed = subprocess.run(
            [sys.executable, str(STATE_TOOL), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            payload = json.loads(completed.stdout)
        except (json.JSONDecodeError, TypeError):
            payload = None
        return completed, payload

    def _assert_ok(self, result: tuple[subprocess.CompletedProcess[str], dict | None]) -> dict:
        completed, payload = result
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIsInstance(payload, dict, completed.stdout)
        self.assertTrue(payload.get("ok"), payload)
        self.assertEqual(payload.get("command"), "resolve-mode", payload)
        return payload

    def _init(self, name: str, mode: str) -> Path:
        task = self.root / name
        task.mkdir()
        completed, payload = self._run(
            "init", str(task), "--skill", "opd", "--mode", mode,
            "--rows-spec", ROWS,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload and payload.get("ok"), payload)
        return task

    def _mark(self, task: Path, row_id: int, *extra: str) -> dict:
        completed, payload = self._run(
            "mark", str(task), "--task-step-id", str(row_id), "--done", *extra,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload and payload.get("ok"), payload)
        return payload

    def test_s1_new_task_default_and_explicit_precedence(self):
        new_default = self.root / "new-default"
        default = self._assert_ok(self._run("resolve-mode", str(new_default), "--new-task"))
        self.assertEqual(
            (default.get("effective_mode"), default.get("source"), default.get("persisted")),
            ("semi-agentic", "default", False),
        )
        self.assertFalse((new_default / "state.json").exists())

        new_explicit = self.root / "new-explicit"
        explicit = self._assert_ok(self._run(
            "resolve-mode", str(new_explicit), "--new-task", "--mode", "agentic",
        ))
        self.assertEqual(
            (explicit.get("effective_mode"), explicit.get("source"), explicit.get("persisted")),
            ("agentic", "explicit", False),
        )
        self.assertFalse((new_explicit / "state.json").exists())

    def test_s1_stored_resume_atomic_override_idempotency_and_audit(self):
        task = self._init("existing", "agentic")
        state_file = task / "state.json"
        journal_file = task / "STATE.md"

        before = json.loads(state_file.read_text(encoding="utf-8"))
        resumed = self._assert_ok(self._run("resolve-mode", str(task)))
        self.assertEqual(
            (resumed.get("effective_mode"), resumed.get("source"), resumed.get("persisted")),
            ("agentic", "state", False),
        )
        self.assertEqual(json.loads(state_file.read_text(encoding="utf-8")), before)

        changed = self._assert_ok(self._run(
            "resolve-mode", str(task), "--mode", "interactive",
        ))
        self.assertEqual(changed.get("previous_mode"), "agentic")
        self.assertEqual(changed.get("effective_mode"), "interactive")
        self.assertEqual(changed.get("source"), "explicit")
        self.assertIs(changed.get("persisted"), True)
        after = json.loads(state_file.read_text(encoding="utf-8"))
        expected = dict(before)
        expected["mode"] = "interactive"
        self.assertEqual(after, expected, "override may mutate only state.json.mode")
        audit = journal_file.read_text(encoding="utf-8")
        for token in ("agentic", "interactive", "explicit"):
            self.assertIn(token, audit)
        self.assertFalse(any(p.name.startswith(".state.json") for p in task.iterdir()))

        state_bytes = state_file.read_bytes()
        audit_bytes = journal_file.read_bytes()
        same = self._assert_ok(self._run(
            "resolve-mode", str(task), "--mode", "interactive",
        ))
        self.assertIs(same.get("persisted"), False)
        self.assertEqual(state_file.read_bytes(), state_bytes)
        self.assertEqual(journal_file.read_bytes(), audit_bytes)

    def test_s2_stored_agentic_survives_new_process_and_auto_approves(self):
        task = self._init("resume", "agentic")
        self._mark(task, 1)

        resolved = self._assert_ok(self._run("resolve-mode", str(task)))
        self.assertEqual((resolved.get("effective_mode"), resolved.get("source")),
                         ("agentic", "state"))
        completed, advanced = self._run(
            "advance", str(task), "--task-step-id", "3",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(advanced and advanced.get("ok"), advanced)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        by_id = {row["row_id"]: row for row in state["rows"]}
        self.assertEqual(by_id[2]["status"], "done")
        self.assertEqual(by_id[2]["owner"], "auto")
        self.assertIn(2, advanced.get("auto_approved", []))

    def test_s3_mode_boundaries_and_close_sovereignty_survive_resolution(self):
        for mode, expected_code in (
            ("agentic", 0),
            ("interactive", 1),
            ("semi-agentic", 1),
        ):
            with self.subTest(mode=mode):
                task = self._init(f"boundary-{mode}", mode)
                self._mark(task, 1)
                resolved = self._assert_ok(self._run("resolve-mode", str(task)))
                self.assertEqual(resolved.get("effective_mode"), mode)
                completed, payload = self._run(
                    "advance", str(task), "--task-step-id", "3",
                )
                self.assertEqual(completed.returncode, expected_code, payload)
                if expected_code:
                    self.assertEqual(payload and payload.get("error"),
                                     "user_confirmation_required")
                else:
                    self.assertEqual(payload and payload.get("auto_approved"), [2])

        for mode in ("agentic", "semi-agentic"):
            with self.subTest(close_mode=mode):
                task = self._init(f"close-{mode}", mode)
                state = json.loads((task / "state.json").read_text(encoding="utf-8"))
                state["rows"][2]["stage"] = "CLOSE"
                (task / "state.json").write_text(
                    json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                )
                self._mark(task, 1)
                self._assert_ok(self._run("resolve-mode", str(task)))
                completed, payload = self._run(
                    "advance", str(task), "--task-step-id", "3",
                )
                self.assertEqual(completed.returncode, 1, payload)
                self.assertEqual(payload and payload.get("error"), "close_gate_violation")

    def test_s4_invalid_legacy_modes_resolve_fail_closed_without_mutation(self):
        invalid_values = ("missing", None, 7, "", "future-mode")
        for value in invalid_values:
            with self.subTest(value=value):
                task = self._init(f"invalid-{value!s}", "agentic")
                state_file = task / "state.json"
                state = json.loads(state_file.read_text(encoding="utf-8"))
                if value == "missing":
                    state.pop("mode")
                else:
                    state["mode"] = value
                state_file.write_text(
                    json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                )
                before = state_file.read_bytes()
                payload = self._assert_ok(self._run("resolve-mode", str(task)))
                self.assertEqual(
                    (payload.get("effective_mode"), payload.get("source"), payload.get("persisted")),
                    ("interactive", "fail_closed", False),
                )
                self.assertTrue(payload.get("warnings"), payload)
                self.assertEqual(state_file.read_bytes(), before)

    def test_s4_validate_and_advance_share_invalid_mode_fail_closed_policy(self):
        task = self._init("invalid-consumers", "agentic")
        self._mark(task, 1)
        state_file = task / "state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state["mode"] = "future-mode"
        state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        before = state_file.read_bytes()

        validated, validation = self._run("validate", str(task))
        self.assertEqual(validated.returncode, 1, validation)
        violations = validation.get("violations", []) if validation else []
        self.assertTrue(any("mode" in str(row.get("code", "")) for row in violations), validation)
        advanced, denial = self._run(
            "advance", str(task), "--task-step-id", "3",
        )
        self.assertEqual(advanced.returncode, 1, denial)
        self.assertEqual(denial and denial.get("error"), "user_confirmation_required")
        self.assertEqual(denial and denial.get("reason"), "invalid_mode_requires_user")
        self.assertEqual(state_file.read_bytes(), before)

    def test_s4_explicit_mode_is_the_only_invalid_legacy_recovery(self):
        task = self._init("invalid-recovery", "agentic")
        state_file = task / "state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state.pop("mode")
        state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        payload = self._assert_ok(self._run(
            "resolve-mode", str(task), "--mode", "semi-agentic",
        ))
        self.assertEqual(payload.get("source"), "explicit")
        self.assertIs(payload.get("persisted"), True)
        self.assertEqual(json.loads(state_file.read_text())["mode"], "semi-agentic")

    def test_s5_malformed_state_hard_blocks_even_explicit_and_preserves_files(self):
        fixtures = ("{not-json", "[]")
        for index, malformed in enumerate(fixtures):
            for explicit in (False, True):
                with self.subTest(index=index, explicit=explicit):
                    task = self.root / f"malformed-{index}-{explicit}"
                    task.mkdir()
                    state_file = task / "state.json"
                    journal_file = task / "STATE.md"
                    state_file.write_text(malformed, encoding="utf-8")
                    journal_file.write_text("audit sentinel\n", encoding="utf-8")
                    before = (state_file.read_bytes(), journal_file.read_bytes())
                    args = ["resolve-mode", str(task)]
                    if explicit:
                        args.extend(("--mode", "agentic"))
                    completed, payload = self._run(*args)
                    self.assertNotEqual(completed.returncode, 0, completed.stdout)
                    self.assertEqual(payload and payload.get("ok"), False)
                    self.assertEqual(payload and payload.get("command"), "resolve-mode")
                    self.assertEqual(payload and payload.get("error"), "state_json_malformed")
                    self.assertEqual((state_file.read_bytes(), journal_file.read_bytes()), before)


if __name__ == "__main__":
    unittest.main()
