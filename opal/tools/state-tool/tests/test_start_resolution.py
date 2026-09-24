"""
@header {
  "module": "test_start_resolution",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "Task 156 resolve-start 3축(mode·workspace·actor) resolver 공개 CLI RED 계약(S-1~S-5, DEC-1~DEC-5, DEC-8). 아직 미구현이라 모두 실패해야 한다(unknown subcommand/argument, 기대 코드 불일치 등).",
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

ROWS = json.dumps([
    {"stage": "TASK", "item": "work"},
    {"stage": "EXECUTE", "item": "work"},
], ensure_ascii=False)

# DEC-1 신규 기본값 표
AGENTIC_WORKTREE_SKILLS = ("opd", "opds", "oppd", "oppl", "oppb")
SEMI_HUB_SKILLS = ("opp", "opwt", "opsdd", "opdd", "opgc", "opdw")


class StartResolutionCliContractTest(unittest.TestCase):
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
        return payload

    def _assert_err(self, result, code: str) -> dict:
        completed, payload = result
        self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
        self.assertIsInstance(payload, dict, completed.stdout)
        self.assertFalse(payload.get("ok"), payload)
        self.assertEqual(payload.get("error"), code, payload)
        return payload

    def _init_from_resolver(self, task: Path, resolved: dict, extra_init_args: list[str] | None = None) -> dict:
        init_args = list(resolved.get("init_args") or [])
        # 157 DEC-1: opd/opds init_args에는 resolver가 판정한 --rows-from <pipeline>이 실린다.
        # 이 헬퍼는 행 구성을 고정 ROWS(--rows-spec)로 주입하므로 그 쌍만 걷어낸다
        # (--rows-spec/--rows-from 배타 계약 rows_input_conflict는 그대로 유지).
        if "--rows-from" in init_args:
            idx = init_args.index("--rows-from")
            del init_args[idx:idx + 2]
        # worktree 판정 태스크는 worktree-tool create가 발급한 worktree_root를 --worktree로 덧붙인다
        # (DEC-8 절차 — 경로 없는 --workspace worktree는 S-5가 worktree_path_required로 고정한다).
        if resolved.get("workspace") == "worktree":
            init_args.extend(["--worktree", str(self.root / f"wt-{task.name}")])
        init_args.extend(extra_init_args or [])
        completed, payload = self._run(
            "init", str(task), *init_args, "--rows-spec", ROWS,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload and payload.get("ok"), payload)
        return payload

    # ------------------------------------------------------------------
    # S-1 — 신규 태스크 기본값 표 (DEC-1, DEC-2)
    # ------------------------------------------------------------------

    def test_s1_new_task_agentic_worktree_defaults(self):
        for skill in AGENTIC_WORKTREE_SKILLS:
            with self.subTest(skill=skill):
                task = self.root / f"new-{skill}"
                result = self._run(
                    "resolve-start", str(task), "--skill", skill, "--new-task",
                )
                payload = self._assert_ok(result)
                self.assertEqual(payload.get("effective_mode"), "agentic", payload)
                self.assertEqual(payload.get("mode_source"), "default", payload)
                self.assertEqual(payload.get("workspace"), "worktree", payload)
                self.assertEqual(payload.get("workspace_source"), "default", payload)
                self.assertFalse((task / "state.json").exists())

    def test_s1_new_task_semi_agentic_hub_defaults(self):
        for skill in SEMI_HUB_SKILLS:
            with self.subTest(skill=skill):
                task = self.root / f"new-{skill}"
                result = self._run(
                    "resolve-start", str(task), "--skill", skill, "--new-task",
                )
                payload = self._assert_ok(result)
                self.assertEqual(payload.get("effective_mode"), "semi-agentic", payload)
                self.assertEqual(payload.get("mode_source"), "default", payload)
                self.assertEqual(payload.get("workspace"), "hub", payload)
                self.assertEqual(payload.get("workspace_source"), "default", payload)
                self.assertFalse((task / "state.json").exists())

    # ------------------------------------------------------------------
    # S-2 — actor 기본값과 init 연동 (DEC-1, DEC-4, C-2)
    # ------------------------------------------------------------------

    def test_s2_opd_opds_default_actor_coordinator_persisted(self):
        for skill in ("opd", "opds"):
            with self.subTest(skill=skill):
                task = self.root / f"actor-{skill}"
                resolved = self._assert_ok(self._run(
                    "resolve-start", str(task), "--skill", skill, "--new-task",
                ))
                self.assertEqual(resolved.get("actor"), "coordinator", resolved)
                self.assertEqual(resolved.get("actor_source"), "default", resolved)
                self._init_from_resolver(task, resolved)
                state = json.loads((task / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(state.get("actor"), "coordinator", state)

    def test_s2_oppd_oppl_oppb_default_actor_worker_no_key(self):
        for skill in ("oppd", "oppl", "oppb"):
            with self.subTest(skill=skill):
                task = self.root / f"actor-{skill}"
                resolved = self._assert_ok(self._run(
                    "resolve-start", str(task), "--skill", skill, "--new-task",
                ))
                self.assertEqual(resolved.get("actor"), "worker", resolved)
                self.assertEqual(resolved.get("actor_source"), "default", resolved)
                self._init_from_resolver(task, resolved)
                state = json.loads((task / "state.json").read_text(encoding="utf-8"))
                self.assertNotIn("actor", state, state)

    def test_s2_oppd_with_pm_flag_rejected(self):
        task = self.root / "oppd-pm"
        self._assert_err(
            self._run(
                "resolve-start", str(task), "--skill", "oppd", "--new-task", "--pm",
            ),
            "actor_unsupported_for_skill",
        )
        self.assertFalse((task / "state.json").exists())

    # ------------------------------------------------------------------
    # S-3 — 기존 태스크 상속·명시 재개 (DEC-2, DEC-3, H-1)
    # ------------------------------------------------------------------

    def _make_existing_state(self, name: str, *, mode: str, extra: dict | None = None) -> Path:
        task = self.root / name
        task.mkdir(parents=True)
        completed, payload = self._run(
            "init", str(task), "--skill", "opd", "--mode", mode,
            "--rows-spec", ROWS,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        if extra:
            state_path = task / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.update(extra)
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return task

    def test_s3_agentic_worktree_coordinator_resumes_stored_values(self):
        task = self._make_existing_state(
            "resume-a", mode="agentic",
            extra={"worktree": str(self.root / "wt-a"), "actor": "coordinator"},
        )
        resolved = self._assert_ok(self._run("resolve-start", str(task), "--skill", "opd"))
        self.assertEqual(resolved.get("effective_mode"), "agentic", resolved)
        self.assertEqual(resolved.get("mode_source"), "state", resolved)
        self.assertEqual(resolved.get("workspace"), "worktree", resolved)
        self.assertEqual(resolved.get("workspace_source"), "state", resolved)
        self.assertEqual(resolved.get("actor"), "coordinator", resolved)
        self.assertEqual(resolved.get("actor_source"), "state", resolved)

    def test_s3_semi_agentic_hub_no_actor_key_legacy_default_worker(self):
        task = self._make_existing_state("resume-b", mode="semi-agentic")
        resolved = self._assert_ok(self._run("resolve-start", str(task), "--skill", "opp"))
        self.assertEqual(resolved.get("workspace"), "hub", resolved)
        self.assertEqual(resolved.get("workspace_source"), "state", resolved)
        self.assertEqual(resolved.get("actor"), "worker", resolved)
        self.assertEqual(resolved.get("actor_source"), "legacy_default", resolved)

    def test_s3_interactive_worktree_legacy_pm_advance_ok(self):
        task = self._make_existing_state(
            "resume-c", mode="interactive",
            extra={"worktree": str(self.root / "wt-c"), "actor": "pm"},
        )
        resolved = self._assert_ok(self._run("resolve-start", str(task), "--skill", "opd"))
        self.assertEqual(resolved.get("actor"), "pm", resolved)
        self.assertEqual(resolved.get("actor_source"), "state", resolved)
        completed, payload = self._run(
            "advance", str(task), "--task-step-id", "1",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload and payload.get("ok"), payload)
        completed, payload = self._run(
            "mark", str(task), "--task-step-id", "1", "--done",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload and payload.get("ok"), payload)

    def test_s3_agentic_hub_worker_resumes_stored_values(self):
        task = self._make_existing_state("resume-d", mode="agentic")
        resolved = self._assert_ok(self._run("resolve-start", str(task), "--skill", "oppd"))
        self.assertEqual(resolved.get("workspace"), "hub", resolved)
        self.assertEqual(resolved.get("workspace_source"), "state", resolved)
        self.assertEqual(resolved.get("actor"), "worker", resolved)
        self.assertEqual(resolved.get("actor_source"), "legacy_default", resolved)

    def test_s3_invalid_stored_mode_falls_back_interactive_fail_closed(self):
        task = self.root / "resume-e"
        task.mkdir(parents=True)
        completed, payload = self._run(
            "init", str(task), "--skill", "opd", "--mode", "agentic",
            "--rows-spec", ROWS,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        state_path = task / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["mode"] = "bogus-mode"
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        resolved = self._assert_ok(self._run("resolve-start", str(task), "--skill", "opd"))
        self.assertEqual(resolved.get("effective_mode"), "interactive", resolved)
        self.assertEqual(resolved.get("mode_source"), "fail_closed", resolved)

    def test_s3_resume_axis_locked_on_workspace_and_actor_flag_change(self):
        task = self._make_existing_state(
            "resume-lock-ws", mode="agentic",
            extra={"worktree": str(self.root / "wt-lock"), "actor": "coordinator"},
        )
        payload = self._assert_err(
            self._run("resolve-start", str(task), "--skill", "opd", "--no-wt"),
            "resume_axis_locked",
        )
        self.assertEqual(payload.get("axis"), "workspace", payload)

        task2 = self._make_existing_state("resume-lock-actor", mode="semi-agentic")
        payload2 = self._assert_err(
            self._run("resolve-start", str(task2), "--skill", "opp", "--pm"),
            "resume_axis_locked",
        )
        self.assertEqual(payload2.get("axis"), "actor", payload2)

    def test_s3_explicit_mode_flag_updates_mode_only(self):
        task = self._make_existing_state(
            "resume-mode-only", mode="agentic",
            extra={"worktree": str(self.root / "wt-mode-only"), "actor": "coordinator"},
        )
        before = json.loads((task / "state.json").read_text(encoding="utf-8"))
        resolved = self._assert_ok(self._run(
            "resolve-start", str(task), "--skill", "opd", "--interactive",
        ))
        self.assertEqual(resolved.get("effective_mode"), "interactive", resolved)
        self.assertEqual(resolved.get("mode_source"), "explicit", resolved)
        after = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(after.get("mode"), "interactive", after)
        self.assertEqual(after.get("worktree"), before.get("worktree"), after)
        self.assertEqual(after.get("actor"), before.get("actor"), after)

    # ------------------------------------------------------------------
    # S-4 — 충돌·거부 (DEC-3, DEC-4, C-4)
    # ------------------------------------------------------------------

    def test_s4_mode_flag_conflict(self):
        task = self.root / "conflict-mode"
        payload = self._assert_err(
            self._run(
                "resolve-start", str(task), "--skill", "opd", "--new-task",
                "--agentic", "--interactive",
            ),
            "mode_flag_conflict",
        )
        self.assertFalse((task / "state.json").exists())

    def test_s4_workspace_flag_conflict(self):
        task = self.root / "conflict-ws"
        self._assert_err(
            self._run(
                "resolve-start", str(task), "--skill", "opd", "--new-task",
                "--wt", "--no-wt",
            ),
            "workspace_flag_conflict",
        )
        self.assertFalse((task / "state.json").exists())

    def test_s4_actor_flag_conflict(self):
        task = self.root / "conflict-actor"
        self._assert_err(
            self._run(
                "resolve-start", str(task), "--skill", "opd", "--new-task",
                "--pm", "--no-pm",
            ),
            "actor_flag_conflict",
        )
        self.assertFalse((task / "state.json").exists())

    def test_s4_oppb_no_wt_workspace_required_for_skill(self):
        task = self.root / "conflict-oppb"
        self._assert_err(
            self._run(
                "resolve-start", str(task), "--skill", "oppb", "--new-task", "--no-wt",
            ),
            "workspace_required_for_skill",
        )
        self.assertFalse((task / "state.json").exists())

    def test_s4_init_actor_pm_retired(self):
        task = self.root / "init-actor-pm-retired"
        task.mkdir(parents=True)
        self._assert_err(
            self._run(
                "init", str(task), "--skill", "opds", "--mode", "agentic",
                "--rows-spec", ROWS, "--actor", "pm",
            ),
            "actor_pm_retired",
        )
        self.assertFalse((task / "state.json").exists())

    def test_s4_opds_no_pm_resolves_and_persists_worker(self):
        task = self.root / "opds-no-pm"
        resolved = self._assert_ok(self._run(
            "resolve-start", str(task), "--skill", "opds", "--new-task", "--no-pm",
        ))
        self.assertEqual(resolved.get("actor"), "worker", resolved)
        self.assertEqual(resolved.get("actor_source"), "explicit", resolved)
        init_args = resolved.get("init_args") or []
        self.assertIn("--actor", init_args, resolved)
        idx = init_args.index("--actor")
        self.assertEqual(init_args[idx + 1], "worker", resolved)
        self._init_from_resolver(task, resolved)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state.get("actor"), "worker", state)

    # ------------------------------------------------------------------
    # S-5 — worktree 게이트 (DEC-8, H-2)
    # ------------------------------------------------------------------

    def test_s5_init_workspace_worktree_requires_worktree_path(self):
        task = self.root / "ws-worktree-missing"
        task.mkdir(parents=True)
        self._assert_err(
            self._run(
                "init", str(task), "--skill", "opds", "--mode", "agentic",
                "--rows-spec", ROWS, "--workspace", "worktree",
            ),
            "worktree_path_required",
        )
        self.assertFalse((task / "state.json").exists())
        self.assertFalse((task / "STATE.md").exists())

    def test_s5_init_workspace_hub_oppb_rejected(self):
        task = self.root / "ws-hub-oppb"
        task.mkdir(parents=True)
        self._assert_err(
            self._run(
                "init", str(task), "--skill", "oppb", "--mode", "agentic",
                "--rows-spec", ROWS, "--workspace", "hub",
            ),
            "workspace_required_for_skill",
        )
        self.assertFalse((task / "state.json").exists())

    def test_s5_init_workspace_hub_opds_ok_no_worktree_key(self):
        task = self.root / "ws-hub-opds"
        task.mkdir(parents=True)
        completed, payload = self._run(
            "init", str(task), "--skill", "opds", "--mode", "agentic",
            "--rows-spec", ROWS, "--workspace", "hub",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload and payload.get("ok"), payload)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertNotIn("worktree", state, state)

    def test_s5_init_workspace_worktree_with_path_ok_has_worktree_key(self):
        task = self.root / "ws-worktree-ok"
        task.mkdir(parents=True)
        wt_path = self.root / "wt-ok"
        completed, payload = self._run(
            "init", str(task), "--skill", "opds", "--mode", "agentic",
            "--rows-spec", ROWS, "--workspace", "worktree", "--worktree", str(wt_path),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload and payload.get("ok"), payload)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        self.assertIn("worktree", state, state)

    def test_s5_init_without_workspace_flag_stays_compatible(self):
        task = self.root / "ws-unspecified"
        task.mkdir(parents=True)
        completed, payload = self._run(
            "init", str(task), "--skill", "opd", "--mode", "agentic",
            "--rows-spec", ROWS,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload and payload.get("ok"), payload)


if __name__ == "__main__":
    unittest.main()
