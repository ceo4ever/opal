"""
@header {
  "module": "test_opd2_gate_mark_guard",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "168 W-1 apply_opd2_gate_mark_guard()의 공개 CLI 계약 — opd2 태스크의 opd2 게이트 행(task.intent_md 등)을 완료로 바꿀 때 형제 스킬 opal-pilot-dev2/scripts/lifecycle.py verify-mark가 통과해야 하고, 통과하지 못하면 opd2_gate_record_required로 거부되며 --force/--auto-pass/--as-worker로도 우회할 수 없음을 검증한다.",
  "exports": ["OPD2GateMarkGuardTest"],
  "depends": ["state_tool", "opal-pilot-dev2/scripts/lifecycle"]
}
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
STATE_TOOL_PATH = REPO_ROOT / "opal" / "tools" / "state-tool" / "state_tool.py"
LIFECYCLE_PY = REPO_ROOT / "opal" / "skills" / "opal-pilot-dev2" / "scripts" / "lifecycle.py"
PIPELINE_JSON = REPO_ROOT / "opal" / "skills" / "opal-pilot-dev2" / "references" / "pipeline.json"


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_state_tool(*args):
    completed = subprocess.run(
        [sys.executable, str(STATE_TOOL_PATH), *args],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        payload = None
    return completed, payload


def _run_lifecycle(*args):
    completed = subprocess.run(
        [sys.executable, str(LIFECYCLE_PY), *args],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        payload = None
    return completed, payload


def _assert_ok(result):
    completed, payload = result
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert isinstance(payload, dict), completed.stdout
    assert payload.get("ok"), payload
    return payload


def _make_opd2_task(root: Path, name: str):
    """resolve-start(--skill opd2 --no-wt)로 workspace=hub를 명시 판정한 뒤,
    opd2 pipeline.json으로 state-tool init까지 마친 태스크를 만든다(opd2는
    ACTOR_SKILLS가 아니라 resolve-start init_args에 --rows-from이 없으므로 이
    헬퍼가 references/pipeline.json 경로를 직접 넘긴다)."""
    repo = root / name / "repo"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    (repo / "app.py").write_text("value = 1\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=OPD2 gate test", "-c",
         "user.email=opd2-gate@example.invalid", "-c", "commit.gpgsign=false",
         "commit", "-qm", "seed"], check=True)
    task = repo / "tasks" / "change"

    resolved = _assert_ok(_run_state_tool(
        "resolve-start", str(task), "--skill", "opd2", "--new-task", "--no-wt"))
    assert resolved["workspace"] == "hub", resolved

    _assert_ok(_run_state_tool(
        "init", str(task), "--skill", "opd2", "--mode", "agentic",
        "--workspace", "hub", "--rows-from", str(PIPELINE_JSON)))

    _assert_ok(_run_lifecycle(
        "init", str(task), "--repo", str(repo), "--change-id", "C1",
        "--workspace", "hub", "--mode", "agentic", "--delivery", "build"))

    return task, repo


def _write_intent_artifact(task: Path, *, change_id="C1"):
    intent = {
        "change_id": change_id, "risk": "normal", "open_questions": [],
        "problem": "Bug adds one", "outcome": "Correct sum",
        "acceptance": ["1+1 is 2"], "non_goals": [],
        "constraints": ["No new dependencies"],
    }
    (task / "intent.md").write_text(
        "# intent\n\nConcrete user contract for arithmetic behavior.\n")
    (task / "intent.json").write_text(json.dumps(intent, ensure_ascii=False))


class OPD2GateMarkGuardTest(unittest.TestCase):
    """[T168/W-9] apply_opd2_gate_mark_guard() 계약 — (a) verify-mark 통과 시 정상
    완료, (b) verify-mark 실패 시 opd2_gate_record_required로 거부되고 state.json
    불변, (c) --force/--auto-pass/--as-worker로도 (b)를 우회할 수 없다."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory(prefix="opd2-gate-guard-")
        self.root = Path(self.tempdir.name)
        self.addCleanup(self.tempdir.cleanup)

    def _mark_intent(self, task, *extra_args):
        return _run_state_tool(
            "mark", str(task), "--task-step", "task.intent_md", "--done", *extra_args)

    def test_verify_mark_success_completes_row(self):
        """(a) lifecycle.py verify-mark가 통과(exit 0)하면 mark가 정상 완료되고
        해당 행이 done이 된다."""
        task, _repo = _make_opd2_task(self.root, "a-success")
        _write_intent_artifact(task)

        # 사전 확인 — lifecycle.py verify-mark 자체가 exit 0을 반환한다.
        verify_completed, verify_payload = _run_lifecycle(
            "verify-mark", "--task", str(task), "--key", "task.intent_md")
        self.assertEqual(verify_completed.returncode, 0,
                         verify_completed.stderr or verify_completed.stdout)
        self.assertTrue(verify_payload.get("ok"), verify_payload)

        completed, payload = self._mark_intent(task)
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload.get("ok"), payload)
        state = json.loads((task / "state.json").read_text(encoding="utf-8"))
        rows = {row.get("key"): row for row in state.get("rows", [])}
        self.assertEqual(rows.get("task.intent_md", {}).get("status"), "done", state)

    def test_verify_mark_failure_rejects_and_state_unchanged(self):
        """(b) intent.md/intent.json이 없어 lifecycle.py verify-mark가 실패하면
        opd2_gate_record_required로 거부되고 state.json이 바이트 단위로 불변이다."""
        task, _repo = _make_opd2_task(self.root, "b-fail")
        # intent 아티팩트를 의도적으로 만들지 않는다 — verify-mark가 실패해야 한다.
        verify_completed, _verify_payload = _run_lifecycle(
            "verify-mark", "--task", str(task), "--key", "task.intent_md")
        self.assertNotEqual(verify_completed.returncode, 0, verify_completed.stdout)

        before = _sha256(task / "state.json")
        completed, payload = self._mark_intent(task)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertFalse(payload.get("ok"), payload)
        self.assertEqual(payload.get("error"), "opd2_gate_record_required", payload)
        after = _sha256(task / "state.json")
        self.assertEqual(before, after, "state.json이 바이트 단위로 불변이어야 한다")
        required_action = str(payload.get("required_action") or "")
        self.assertIn("verify-mark", required_action, payload)

    def test_bypass_flags_do_not_skip_guard(self):
        """(c) 이력 없는 상태에서 --force --note·--auto-pass·
        --as-worker --worker-stage TASK로도 (b)의 거부를 우회할 수 없다."""
        task, _repo = _make_opd2_task(self.root, "c-bypass")
        before = _sha256(task / "state.json")
        for extra in (
            ["--force", "--note", "우회 시도"],
            ["--auto-pass"],
            ["--as-worker", "--worker-stage", "TASK"],
        ):
            with self.subTest(extra=extra):
                completed, payload = self._mark_intent(task, *extra)
                self.assertEqual(completed.returncode, 1, completed.stdout)
                self.assertFalse(payload.get("ok"), payload)
                self.assertEqual(payload.get("error"), "opd2_gate_record_required", payload)
                after = _sha256(task / "state.json")
                self.assertEqual(before, after, "state.json이 바이트 단위로 불변이어야 한다")


if __name__ == "__main__":
    unittest.main()
