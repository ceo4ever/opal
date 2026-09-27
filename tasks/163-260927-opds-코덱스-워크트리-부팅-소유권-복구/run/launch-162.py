"""Launch Task 162 with the installed tool and an explicit Codex command."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import subprocess


HUB = Path("/Volumes/Data/AIStudio/workspace/ai-framework")
META = HUB / ".opal-worktrees/.meta/task_162.json"
LAUNCHER = Path("/Users/iskang/.opal/tools/worktree-launcher/run.sh")
SETTING = Path("/Users/iskang/.opal/setting.json")
HUB_SESSION = "01a0e27f-0587-7bd2-8ff0-d90accacbb92"


def main() -> None:
    meta = json.loads(META.read_text(encoding="utf-8"))
    before = meta["execution_ownership"]
    if before["state"] != "hub_owned" or before["owner_session_id"] is not None:
        raise RuntimeError(f"task_162_not_ready: {before}")
    task_path = meta["task_path"]
    worktree_root = meta["worktree_root"]
    prompt = (
        f"{task_path} 이어서 수행. //opd agentic으로 CLOSE까지 자율 진행하라. "
        "태스크 161과 163의 파일·상태는 수정하지 말고, merge·push나 외부 시스템 쓰기 전에는 멈춰 보고하라."
    )
    command = shlex.join(["codex", "--no-daemon", prompt])
    setting_before = SETTING.read_bytes()
    argv = [
        str(LAUNCHER), "launch", "--adapter", "orca",
        "--project-root", str(HUB), "--task", "162",
        "--worktree-root", str(worktree_root),
        "--owner-session-id", HUB_SESSION,
        "--command", command,
    ]
    completed = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    response = json.loads(completed.stdout)
    installed_state = json.loads(META.read_text(encoding="utf-8"))["execution_ownership"]
    record = {
        "returncode": completed.returncode,
        "response": response,
        "registry": installed_state,
        "setting_unchanged": SETTING.read_bytes() == setting_before,
    }
    output = Path(__file__).with_name("launch-162.json")
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "returncode": completed.returncode,
        "ok": response.get("ok"),
        "status": response.get("status"),
        "error": response.get("error"),
        "registry_owner": installed_state.get("owner_session_id"),
        "handle": response.get("adapter_handle"),
        "setting_unchanged": record["setting_unchanged"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
