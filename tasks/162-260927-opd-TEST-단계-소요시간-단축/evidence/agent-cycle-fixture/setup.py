"""Build an isolated, reproducible task-162 TEST procedure fixture."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys


HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STATE = ROOT / "opal/tools/state-tool/run.sh"
TEST = ROOT / "opal/tools/test-tool/run.sh"
TASK = HERE / "fixture-task"
REPO = HERE / "fixture-repo"
TRACE = HERE / "trace"
RUN_ID = "task162-agent-cycle-handoff-001"


def call(label: str, command: list[str], cwd: pathlib.Path = HERE) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    payload = {
        "command": command,
        "cwd": str(cwd),
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    (TRACE / f"{label}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    if result.returncode:
        raise RuntimeError(f"{label} exit={result.returncode}: {result.stdout} {result.stderr}")


def main() -> None:
    if TASK.exists() or REPO.exists():
        raise RuntimeError("fixture already exists; refusing to reset it")
    TRACE.mkdir(parents=True, exist_ok=True)
    TASK.mkdir()
    REPO.mkdir()
    call("state-init", ["bash", str(STATE), "init", str(TASK), "--skill", "opd", "--mode", "agentic", "--rows-spec", '[{"stage":"TEST","item":"fixture TEST"}]', "--run-log-mode", "off"])
    scenarios = []
    for ident, action in (("H1", "fixture login approval"), ("H2", "fixture DDL approval")):
        scenarios.append({
            "id": ident, "acceptance_ref": "T162/S-1", "type": "e2e", "expected": action,
            "red_required": False, "profile": "manual", "surface_ref": f"fixture-{ident}", "surface_kind": "manual",
            "actors": ["human"], "steps": [{"id": "approve", "executor": "human"}],
            "assertions": [{"id": f"{ident}-approved", "expected": True}],
            "required_evidence": [f"{ident}-submission"],
            "handoff": {
                "handoff_id": ident, "instruction": action,
                "expected_observation": "approved", "required_evidence": [f"{ident}-submission"],
                "timeout_seconds": 900, "resume_token": f"task162-{ident}-token-001",
                "server_policy": "keep", "submission_path": str(TASK / f"{ident}-submission.json"),
            },
        })
    for ident in ("A1", "A2"):
        scenarios.append({"id": ident, "acceptance_ref": "T162/S-1", "expected": f"pytest {ident} passes", "red_required": False})
    call("scenario-init", ["bash", str(TEST), "scenario-init", "--task-path", str(TASK), "--scenarios", json.dumps(scenarios, ensure_ascii=False)])
    call("scenario-lock", ["bash", str(TEST), "scenario-lock", "--task-path", str(TASK)])
    (REPO / "app.py").write_text("def value():\n    return 0\n\ndef stable():\n    return 1\n")
    (REPO / "test_fixture.py").write_text(
        "from app import value, stable\n\n"
        "def test_auto_a1():\n    assert stable() == 1\n\n"
        "def test_auto_a2():\n    assert stable() + 1 == 2\n\n"
        "def test_failed_scenario():\n    assert value() == 2\n\n"
        "def test_impact_scenario():\n    assert value() >= 0\n\n"
        "def test_unknown_scenario():\n    assert stable() == 1\n"
    )
    call("git-init", ["git", "init", "-q", "-b", "main"], REPO)
    call("git-add", ["git", "add", "app.py", "test_fixture.py"], REPO)
    call("git-commit", ["git", "-c", "user.name=Task162 Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture base"], REPO)
    print(json.dumps({"ok": True, "task": str(TASK), "repo": str(REPO), "trace": str(TRACE), "run_id": RUN_ID,
                      "human_ids": ["H1", "H2"], "human_tokens": ["task162-H1-token-001", "task162-H2-token-001"],
                      "auto_command": [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_fixture.py::test_auto_a1", "test_fixture.py::test_auto_a2"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
