"""
@header {
  "module": "test_skill_tester_oppb",
  "layer": "test",
  "domain": "opal-skill-tester",
  "description": "opal-skill-tester의 OPPB 판정 프로필, P0~P5 단계 종료, finalize archive 커버리지와 OPPB 기능 시나리오 규격을 고정한다.",
  "exports": []
}
"""
import importlib.util
import json
import pathlib


SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "skill_tester.py"
SPEC = importlib.util.spec_from_file_location("skill_tester", SCRIPT)
skill_tester = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(skill_tester)


def test_oppb_profile_tracks_project_build_milestones():
    profile = skill_tester.PROFILES["oppb"]

    assert profile["exec"] == "p3.continuous_execution"
    assert profile["test_done"] == "p4.pm_gate"
    assert profile["close"] == "p5.worktree_finalize"
    assert profile["scenario_json"] is False
    assert profile["archive_required"] is True
    assert profile["checkpoint_policy"] == "finalized"
    assert "p4.project_checkpoint" in profile["gate_rows"]


def test_oppb_checkpoint_requires_finalized_archive_evidence():
    assert skill_tester.checkpoint_ok({
        "worktree_task": True,
        "checkpoint_policy": "finalized",
        "oppb_archive_ok": True,
        "oppb_worktree_finalized": True,
    })
    assert not skill_tester.checkpoint_ok({
        "worktree_task": True,
        "checkpoint_policy": "finalized",
        "oppb_archive_ok": False,
        "oppb_worktree_finalized": True,
    })
    assert not skill_tester.checkpoint_ok({
        "worktree_task": True,
        "checkpoint_policy": "finalized",
        "oppb_archive_ok": True,
        "oppb_worktree_finalized": False,
    })


def test_checkpoint_ok_keeps_existing_branch_policy():
    assert skill_tester.checkpoint_ok({
        "worktree_task": False,
        "checkpoint_policy": "branch",
        "checkpoint_commits": 0,
        "raw_commits": 99,
    })
    assert skill_tester.checkpoint_ok({
        "worktree_task": True,
        "checkpoint_policy": "branch",
        "checkpoint_commits": 1,
        "raw_commits": 0,
    })
    assert not skill_tester.checkpoint_ok({
        "worktree_task": True,
        "checkpoint_policy": "branch",
        "checkpoint_commits": 1,
        "raw_commits": 1,
    })
    assert not skill_tester.checkpoint_ok({
        "worktree_task": True,
        "checkpoint_policy": "branch",
        "checkpoint_commits": 0,
        "raw_commits": 0,
    })


def test_oppb_archive_status_requires_closed_task_local_run_and_no_legacy(tmp_path):
    task = tmp_path / "tasks" / "001-oppb-sample"
    archive = task / ".oppb-run" / "20260926T102236Z-f5f81223"
    archive.mkdir(parents=True)
    (archive / "run.closed.json").write_text("{}\n", encoding="utf-8")

    status = skill_tester._oppb_archive_status(task, tmp_path)

    assert status == {
        "oppb_archive_count": 1,
        "oppb_archive_ok": True,
        "oppb_legacy_root_absent": True,
    }

    (tmp_path / ".opal-runs").mkdir()
    status = skill_tester._oppb_archive_status(task, tmp_path)
    assert status["oppb_legacy_root_absent"] is False


def test_collect_run_checks_oppb_archive_in_canonical_task_dir(tmp_path, monkeypatch):
    rd = tmp_path / "oppb-r1"
    repo = rd / "repo"
    task_id = "001-260926-oppb-재고부족-조회"
    worktree = repo / ".opal-worktrees" / "task_001"
    worktree_task = worktree / "tasks" / task_id
    canonical_task = repo / "tasks" / task_id
    archive = canonical_task / ".oppb-run" / "20260926T102236Z-f5f81223"
    archive.mkdir(parents=True)
    worktree_task.mkdir(parents=True)
    (archive / "run.closed.json").write_text("{}\n", encoding="utf-8")
    (rd / "run.json").write_text(json.dumps({
        "variant": "//oppb",
        "rep": 1,
        "start": 1000,
        "end": 1120,
    }), encoding="utf-8")
    state = {
        "task_id": task_id,
        "skill": "oppb",
        "current_status": "in_progress",
        "worktree": str(worktree),
        "rows": [
            {"key": "p1.user_gate", "status": "done", "stage": "P1"},
            {"key": "p3.pm_gate", "status": "done", "stage": "P3"},
            {"key": "p4.project_checkpoint", "status": "done", "stage": "P4"},
            {"key": "p4.pm_gate", "status": "done", "stage": "P4"},
            {"key": "p5.user_merge_gate", "status": "done", "stage": "P5"},
            {"key": "p5.done_md", "status": "done", "stage": "P5"},
            {"key": "p5.worktree_finalize", "status": "done", "stage": "P5"},
        ],
        "run_log": {"pending_events": []},
    }
    for task in (worktree_task, canonical_task):
        (task / "state.json").write_text(json.dumps(state), encoding="utf-8")

    monkeypatch.setattr(skill_tester.subprocess, "run", lambda *a, **k: type("R", (), {
        "stdout": "{\"violations_count\": 0}",
        "returncode": 0,
    })())

    metrics = skill_tester.collect_run(rd, {"id": "function-oppb-low-stock"})

    assert metrics["task_found"] is True
    assert metrics["oppb_archive_count"] == 1
    assert metrics["oppb_archive_ok"] is True
    assert metrics["oppb_legacy_root_absent"] is True
    assert metrics["oppb_worktree_finalized"] is False
    assert metrics["gate_evidence"] is False


def test_function_oppb_scenario_is_valid():
    assert skill_tester.validate_scenario("function-oppb-low-stock") == []
