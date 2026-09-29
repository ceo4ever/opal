"""
@header {
  "module": "test_mode_transition_contract",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "Task 136 mode-aware transition and CLOSE tail public CLI contract",
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
STATE_TOOL_RUN = REPO_ROOT / "opal" / "tools" / "state-tool" / "run.sh"


# [T167] 목표-커버 게이트 mark 가드(state-tool apply_scenario_gate_mark_guard) fixture 준비 —
#   게이트 행 mark 전에 형제 test-tool scenario-gate-record로 현재 문서 묶음의 pass 이력을 만든다.
_T167_TEST_TOOL_PY = Path(__file__).resolve().parents[2] / "test-tool" / "test_tool.py"


def _t167_record_scenario_gate_pass(task_dir):
    task_dir = Path(task_dir)
    history_path = task_dir / ".scenario-gate-history.json"
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else []
    eval_path = task_dir / ".t167-scenario-gate-eval.json"
    eval_path.write_text(json.dumps({
        "scores": {"goal": 2, "adoption": 2, "boundary": 2}, "average": 2.0,
        "gaps": [], "verdict": "pass", "advisories": [],
    }), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(_T167_TEST_TOOL_PY), "scenario-gate-record",
         "--task-folder", str(task_dir), "--iteration", str(len(history) + 1),
         "--evaluator-result", str(eval_path)],
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout).get("verdict") == "pass", completed.stdout
MODES = ("interactive", "semi-agentic", "agentic")
TRANSITION_ACTIONS = {"continue", "await_user", "blocked", "complete"}
PRE_EXECUTE_STAGES = {
    "TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO", "SPEC", "REVIEW",
    "DESIGN", "WBS", "WIREFRAME", "DICT", "MODEL", "DDL/MIGRATION",
}
NON_CLOSE_STAGES = (
    "TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO", "SPEC", "REVIEW",
    "DESIGN", "WBS", "WIREFRAME", "DICT", "MODEL", "DDL/MIGRATION",
    "EXECUTE", "TEST", "QA", "VERIFY", "SCAN", "CHECK", "REPORT",
)


class ModeTransitionCliContractTest(unittest.TestCase):
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

    def _run_public(self, *args: str) -> tuple[subprocess.CompletedProcess[str], dict | None]:
        """Exercise the source state-tool only through its supported shell CLI."""
        completed = subprocess.run(
            ["bash", str(STATE_TOOL_RUN), *args],
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

    def _assert_ok(
        self, result: tuple[subprocess.CompletedProcess[str], dict | None]
    ) -> dict:
        completed, payload = result
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIsInstance(payload, dict, completed.stdout)
        self.assertTrue(payload.get("ok"), payload)
        return payload

    def _init(self, name: str, mode: str, rows: list[dict]) -> Path:
        task = self.root / name
        task.mkdir()
        self._assert_ok(self._run(
            "init", str(task), "--skill", "opds", "--mode", mode,
            "--rows-spec", json.dumps(rows, ensure_ascii=False),
        ))
        return task

    def _mark(self, task: Path, row_id: int, *extra: str) -> dict:
        return self._assert_ok(self._run(
            "mark", str(task), "--task-step-id", str(row_id), "--done", *extra,
        ))

    def _assert_transition(
        self, payload: dict, action: str, report_type: str
    ) -> None:
        self.assertIn(payload.get("transition_action"), TRANSITION_ACTIONS, payload)
        self.assertEqual(payload.get("transition_action"), action, payload)
        self.assertEqual(payload.get("report_type"), report_type, payload)
        self.assertIsInstance(payload.get("next_action"), str, payload)
        self.assertTrue(payload.get("next_action"), payload)

    @staticmethod
    def _stage_slug(stage: str) -> str:
        return stage.lower().replace("-", "_").replace("/", "_")

    def test_s1_three_modes_cover_every_non_close_stage_boundary(self):
        for mode in MODES:
            for stage in NON_CLOSE_STAGES:
                with self.subTest(mode=mode, stage=stage):
                    slug = self._stage_slug(stage)
                    rows = [
                        {"key": f"{slug}.work", "stage": stage, "item": "작업"},
                        {"key": f"{slug}.user_confirm", "stage": stage,
                         "item": "사용자 확인"},
                        {"key": "execute.next_work", "stage": "EXECUTE",
                         "item": "다음 작업"},
                    ]
                    task = self._init(f"s1-{mode}-{slug}", mode, rows)
                    payload = self._mark(task, 1)
                    expected = (
                        "await_user"
                        if mode == "interactive"
                        or (mode == "semi-agentic" and stage in PRE_EXECUTE_STAGES)
                        else "continue"
                    )
                    expected_report = (
                        "decision_request" if expected == "await_user"
                        else "progress_report"
                    )
                    self._assert_transition(payload, expected, expected_report)

    def test_s1_blocked_is_a_structured_transition(self):
        rows = [
            {"key": "execute.work", "stage": "EXECUTE", "item": "작업"},
            {"key": "test.work", "stage": "TEST", "item": "검증"},
        ]
        task = self._init("s1-blocked", "agentic", rows)
        payload = self._assert_ok(self._run(
            "block", str(task), "--task-step-id", "1",
            "--reason", "retry exhaustion",
        ))
        self._assert_transition(payload, "blocked", "decision_request")

    def test_s3_task_interruption_resume_preserves_mode_frontier_and_action(self):
        rows = [
            {"key": "task.task_md", "stage": "TASK", "item": "TASK.md 작성"},
            {"key": "task.user_confirm", "stage": "TASK", "item": "사용자 확인"},
            {"key": "execute.work", "stage": "EXECUTE", "item": "구현"},
        ]
        task = self._init("s3-task-resume", "agentic", rows)
        first = self._mark(task, 1)
        self._assert_transition(first, "continue", "progress_report")

        resolved = self._assert_ok(self._run("resolve-mode", str(task)))
        self.assertEqual(resolved.get("effective_mode"), "agentic", resolved)
        shown = self._assert_ok(self._run("show", str(task), "--format", "json"))
        self.assertEqual(shown.get("mode"), "agentic", shown)
        self._assert_transition(shown, "continue", "progress_report")

        advanced = self._assert_ok(self._run(
            "advance", str(task), "--task-step-id", "3",
        ))
        self.assertEqual(advanced.get("auto_approved"), [2], advanced)
        self._assert_transition(advanced, "continue", "progress_report")

    def test_s3_legacy_single_close_row_remains_resumable(self):
        rows = [
            {"key": "test.work", "stage": "TEST", "item": "검증"},
            {"key": "test.user_confirm", "stage": "TEST", "item": "사용자 확인"},
            {"key": "close.done_md", "stage": "CLOSE", "item": "DONE.md 생성"},
        ]
        task = self._init("s3-legacy-close", "agentic", rows)
        self._mark(task, 1)
        self._mark(task, 2, "--owner", "user")
        completed = self._mark(task, 3, "--owner", "user")
        self._assert_transition(completed, "complete", "progress_report")
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state.get("current_status"), "completed_unmerged")

        resumed = self._assert_ok(self._run("show", str(task), "--format", "json"))
        self._assert_transition(resumed, "complete", "progress_report")

    def test_s4_interactive_close_requires_user_then_continues_until_explicit_final(self):
        close_rows = [
            ("close.done_md", "DONE.md 생성"),
            ("close.docs_sync", "관련 문서 동기화"),
            ("close.brain_ingest", "brain ingest"),
            ("close.retrospective", "회고와 개선 후보"),
            ("close.worktree_finalize", "worktree finalize/attribution"),
            ("close.final", "CLOSE 최종 상태 확정"),
        ]
        rows = [
            {"key": "test.work", "stage": "TEST", "item": "검증"},
            {"key": "test.user_confirm", "stage": "TEST", "item": "사용자 확인"},
            *[
                {"key": key, "stage": "CLOSE", "item": item}
                for key, item in close_rows
            ],
        ]
        task = self._init("s4-close-tail", "interactive", rows)
        self._mark(task, 1)

        denied_process, denied = self._run(
            "advance", str(task), "--task-step-id", "3",
        )
        self.assertEqual(denied_process.returncode, 1, denied)
        self.assertEqual(denied and denied.get("error"), "user_confirmation_required")
        self._assert_transition(denied, "await_user", "decision_request")

        self._mark(task, 2, "--owner", "user")
        for index, (key, _item) in enumerate(close_rows):
            payload = self._mark(task, index + 3)
            state = json.loads((task / "state.json").read_text(encoding="utf-8"))
            if key == "close.final":
                self.assertEqual(state.get("current_status"), "completed_unmerged")
                self._assert_transition(payload, "complete", "progress_report")
            else:
                self.assertNotEqual(state.get("current_status"), "completed_unmerged")
                self._assert_transition(payload, "continue", "progress_report")

    def test_s1_close_entry_is_mode_aware_for_real_opds_and_opgc_pipelines(self):
        """S-1 RED: source run.sh must own every mode/confirmation/CLOSE entry path.

        The two checked-in pipeline fixtures deliberately preserve their existing row
        keys, schema, and ordering.  All setup and every transition use the public
        CLI; the only test-created files are gate artifacts required to reach CLOSE.
        """
        fixtures = (
            # opds intentionally consumes the shared opd pipeline specification.
            ("opds", REPO_ROOT / "opal" / "skills" / "opal-pilot-dev" / "references" / "pipeline.json", True),
            ("opgc", REPO_ROOT / "opal" / "skills" / "opal-pilot-gc" / "references" / "pipeline.json", False),
        )
        gate_artifacts = ("ANALYSIS.md", "TASK.md", "PLAN.md", "TEST-SCENARIO.md", "test-scenario.json")

        for mode in MODES:
            for fixture_name, pipeline, has_confirmation in fixtures:
                for entry in ("advance", "mark"):
                    with self.subTest(mode=mode, fixture=fixture_name, entry=entry):
                        task = self.root / f"s1-{mode}-{fixture_name}-{entry}"
                        initialized = self._assert_ok(self._run_public(
                            "init", str(task), "--skill", fixture_name, "--mode", mode,
                            "--rows-from", str(pipeline),
                        ))
                        self.assertEqual(initialized.get("command"), "init")
                        for artifact in gate_artifacts:
                            (task / artifact).write_text("fixture artifact\n", encoding="utf-8")

                        initial = json.loads((task / "state.json").read_text(encoding="utf-8"))
                        initial_schema = initial["schema_version"]
                        initial_keys = [row["key"] for row in initial["rows"]]
                        first_close_index = next(
                            index for index, row in enumerate(initial["rows"])
                            if row["stage"] == "CLOSE"
                        )
                        confirmation = (
                            initial["rows"][first_close_index - 1]
                            if has_confirmation else None
                        )
                        if confirmation is not None:
                            self.assertEqual(confirmation["item"], "사용자 확인")

                        # Reach the CLOSE frontier without hand-editing pipeline state.
                        for row in initial["rows"][:first_close_index]:
                            if confirmation is not None and row["row_id"] == confirmation["row_id"]:
                                continue
                            if row["key"] in ("test_scenario.scenario_gate", "plan.scenario_gate"):
                                _t167_record_scenario_gate_pass(task)
                            args = ["mark", str(task), "--task-step", row["key"], "--done"]
                            if row["item"] == "사용자 확인":
                                args.extend(("--owner", "user"))
                            else:
                                # These real pipeline work rows are worker-owned;
                                # declare the unavailable fixture duration so the
                                # independent worker-duration guard is not the
                                # reason a CLOSE contract test fails.
                                args.append("--worker-duration-unknown")
                            self._assert_ok(self._run_public(*args))

                        first_close = initial["rows"][first_close_index]
                        entry_args = [entry, str(task), "--task-step", first_close["key"]]
                        if entry == "mark":
                            entry_args.append("--done")
                        before_attempt = (task / "state.json").read_bytes()
                        process, payload = self._run_public(*entry_args)
                        first_close_done = entry == "mark"

                        if mode == "interactive":
                            self.assertEqual(process.returncode, 1, payload)
                            self.assertEqual(payload and payload.get("transition_action"), "await_user")
                            self.assertEqual(payload and payload.get("report_type"), "decision_request")
                            self.assertEqual((task / "state.json").read_bytes(), before_attempt)
                            if confirmation is not None:
                                self._assert_ok(self._run_public(
                                    "mark", str(task), "--task-step", confirmation["key"],
                                    "--done", "--owner", "user",
                                ))
                                process, payload = self._run_public(*entry_args)
                            else:
                                process, payload = self._run_public(
                                    "mark", str(task), "--task-step", first_close["key"],
                                    "--done", "--owner", "user",
                                )
                                first_close_done = True
                        self.assertEqual(process.returncode, 0, payload)
                        self.assertTrue(payload and payload.get("ok"), payload)
                        if mode in ("semi-agentic", "agentic"):
                            self._assert_transition(payload, "continue", "progress_report")

                        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
                        self.assertEqual(state["schema_version"], initial_schema)
                        self.assertEqual([row["key"] for row in state["rows"]], initial_keys)
                        if mode in ("semi-agentic", "agentic") and confirmation is not None:
                            approved = next(row for row in state["rows"] if row["row_id"] == confirmation["row_id"])
                            self.assertEqual(approved["status"], "done")
                            self.assertEqual(approved["owner"], "auto")
                            self.assertIn(confirmation["row_id"], payload.get("auto_approved", []))

                        # advance enters the row; mark it before proving the unchanged CLOSE tail.
                        if not first_close_done:
                            self._assert_ok(self._run_public(
                                "mark", str(task), "--task-step", first_close["key"], "--done",
                            ))
                        for row in initial["rows"][first_close_index + 1:]:
                            tail = self._assert_ok(self._run_public(
                                "mark", str(task), "--task-step", row["key"], "--done",
                            ))
                            if row["key"] == "close.final":
                                self._assert_transition(tail, "complete", "progress_report")
                            else:
                                self._assert_transition(tail, "continue", "progress_report")

    def test_s4_close_auto_approval_is_atomic_when_a_following_gate_fails(self):
        """S-4 RED: a failed CLOSE guard may not persist a partial auto-approval."""
        rows = [
            {"key": "test.work", "stage": "TEST", "item": "검증"},
            {"key": "test.user_confirm", "stage": "TEST", "item": "사용자 확인"},
            {
                "key": "close.done_md", "stage": "CLOSE", "item": "DONE.md 생성",
                "gate": {"artifacts": ["DONE.md"], "checklist": ["DONE.md exists"]},
            },
            {"key": "close.final", "stage": "CLOSE", "item": "CLOSE 최종 상태 확정"},
        ]
        for entry in ("advance", "mark"):
            with self.subTest(entry=entry):
                task = self.root / f"s4-atomic-{entry}"
                self._assert_ok(self._run_public(
                    "init", str(task), "--skill", "opds", "--mode", "semi-agentic",
                    "--rows-spec", json.dumps(rows, ensure_ascii=False),
                ))
                self._assert_ok(self._run_public(
                    "mark", str(task), "--task-step-id", "1", "--done",
                ))
                before = (task / "state.json").read_bytes()
                args = [entry, str(task), "--task-step-id", "3"]
                if entry == "mark":
                    args.append("--done")
                failed, failure = self._run_public(*args)
                self.assertEqual(failed.returncode, 1, failure)
                self.assertEqual(failure and failure.get("error"), "gate_artifact_missing")
                self.assertEqual(failure and failure.get("auto_approved", []), [])
                self.assertEqual((task / "state.json").read_bytes(), before)

                (task / "DONE.md").write_text("done\n", encoding="utf-8")
                succeeded, success = self._run_public(*args)
                self.assertEqual(succeeded.returncode, 0, success)
                self.assertTrue(success and success.get("ok"), success)
                self.assertEqual(success.get("auto_approved"), [2])
                self._assert_transition(success, "continue", "progress_report")
                state = json.loads((task / "state.json").read_text(encoding="utf-8"))
                approved = state["rows"][1]
                self.assertEqual((approved["status"], approved["owner"]), ("done", "auto"))
                self.assertEqual(approved["note"], "auto-approved on CLOSE entry")


if __name__ == "__main__":
    unittest.main()
