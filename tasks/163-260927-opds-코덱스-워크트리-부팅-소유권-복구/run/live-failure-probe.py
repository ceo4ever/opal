"""Exercise the installed launcher failure path against one Orca terminal.

The registry and lease are temporary. Orca attaches the probe terminal to the
already managed Task 163 worktree; the launcher must close that exact terminal.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile


WORKTREE = Path("/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_163")
LAUNCHER = Path("/Users/iskang/.opal/tools/worktree-launcher/run.sh")


def main() -> None:
    hub = Path(tempfile.mkdtemp(prefix="task163-live-failure-"))
    task = "999"
    task_path = hub / "tasks" / "999-failure-probe"
    task_path.mkdir(parents=True)
    meta_path = hub / ".opal-worktrees" / ".meta" / f"task_{task}.json"
    meta_path.parent.mkdir(parents=True)
    meta = {
        "task": task,
        "layout": "monorepo",
        "branch": "feat/OP-TASK-999-probe",
        "worktree_root": str(WORKTREE),
        "entries": [{"repo": str(hub), "path": str(WORKTREE), "branch": "feat/OP-TASK-999-probe", "base_ref": "main"}],
        "pending_setup": [],
        "allocator_root": str(hub),
        "task_home": str(WORKTREE),
        "task_folder": task_path.name,
        "task_path": str(task_path),
        "artifact_repo": ".",
        "task_ownership_version": 2,
        "memory_index_requests_resolved": [],
        "execution_ownership": {
            "state": "hub_owned", "owner_session_id": None, "adapter": "orca",
            "adapter_handle": None, "generation": 0, "launch_receipt": None,
            "prompt_receipt": None, "failure_reason": None, "checkpoint_shas": [],
        },
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    command = [
        str(LAUNCHER), "launch", "--adapter", "orca",
        "--project-root", str(hub), "--task", task,
        "--worktree-root", str(WORKTREE),
        "--owner-session-id", "task163-probe-hub",
        "--command", "task163-command-that-does-not-exist",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=90)
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError:
        response = {"raw_stdout": completed.stdout, "raw_stderr": completed.stderr}
    observed = json.loads(meta_path.read_text(encoding="utf-8"))["execution_ownership"]
    evidence = {
        "hub": str(hub), "returncode": completed.returncode,
        "response": response, "registry": observed,
    }
    output = Path(__file__).with_name("live-failure-probe.json")
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"returncode": completed.returncode,
                      "error": response.get("error"),
                      "failure_reason": response.get("failure_reason"),
                      "status": response.get("status"),
                      "registry_state": observed.get("state"),
                      "terminal_close": response.get("terminal_close"),
                      "terminal_status": response.get("terminal_status")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
