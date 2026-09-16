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

    def test_s4_close_requires_user_then_continues_until_explicit_final(self):
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
        task = self._init("s4-close-tail", "agentic", rows)
        self._mark(task, 1)

        denied_process, denied = self._run(
            "advance", str(task), "--task-step-id", "3",
        )
        self.assertEqual(denied_process.returncode, 1, denied)
        self.assertEqual(denied and denied.get("error"), "close_gate_violation")
        self._assert_transition(denied, "await_user", "decision_request")

        self._mark(task, 2, "--owner", "user")
        for index, (key, _item) in enumerate(close_rows):
            extra = ("--owner", "user") if index == 0 else ()
            payload = self._mark(task, index + 3, *extra)
            state = json.loads((task / "state.json").read_text(encoding="utf-8"))
            if key == "close.final":
                self.assertEqual(state.get("current_status"), "completed_unmerged")
                self._assert_transition(payload, "complete", "progress_report")
            else:
                self.assertNotEqual(state.get("current_status"), "completed_unmerged")
                self._assert_transition(payload, "continue", "progress_report")


if __name__ == "__main__":
    unittest.main()
