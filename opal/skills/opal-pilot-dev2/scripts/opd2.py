#!/usr/bin/env python3
"""OPD2 public entry point; existing OPAL tools remain the state owners."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def fail(code, message):
    print(json.dumps({"ok": False, "error": code, "message": message}, ensure_ascii=False))
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opal-root", type=Path, default=Path.home() / ".opal")
    commands = parser.add_subparsers(dest="command", required=True)
    resolve = commands.add_parser("resolve-start")
    resolve.add_argument("task_path", type=Path)
    resolve.add_argument("--new-task", action="store_true")
    modes = resolve.add_mutually_exclusive_group()
    modes.add_argument("--semi-agentic", action="store_true")
    modes.add_argument("--agentic", action="store_true")
    spaces = resolve.add_mutually_exclusive_group()
    spaces.add_argument("--wt", "--worktree", action="store_true")
    spaces.add_argument("--no-wt", action="store_true")
    status = commands.add_parser("status")
    status.add_argument("task_path", type=Path)
    args = parser.parse_args(argv)
    tool = args.opal_root.expanduser().resolve() / "tools/state-tool/run.sh"
    if not tool.is_file():
        return fail("engine_missing", str(tool))
    task = args.task_path.expanduser().resolve()
    if args.command == "status":
        if (task / '.sdlc/events.jsonl').exists():
            return subprocess.run([sys.executable, str(Path(__file__).with_name('lifecycle.py')),
                                   'status', str(task)], check=False).returncode
        return subprocess.run([str(tool), "show", str(task)], check=False).returncode
    state = task / "state.json"
    if args.new_task and state.exists():
        return fail("task_already_exists", "Use resume without --new-task")
    if not args.new_task and not state.is_file():
        return fail("resume_state_missing", str(state))
    mode = "semi-agentic" if args.semi_agentic else "agentic" if args.agentic else None
    if state.is_file():
        try:
            saved = json.loads(state.read_text())
        except (OSError, ValueError) as exc:
            return fail("state_json_malformed", str(exc))
        if not isinstance(saved, dict):
            return fail("state_json_malformed", "Expected an object")
        if saved.get("skill") != "opd":
            return fail("incompatible_engine_skill", "Only opd engine tasks can resume through opd2")
        if mode is None and saved.get("mode") not in ("semi-agentic", "agentic"):
            return fail("unsupported_stored_mode", "Explicit --semi-agentic or --agentic required")
    command = [str(tool), "resolve-start", str(task), "--skill", "opd"]
    if args.new_task:
        command.append("--new-task")
        mode = mode or "agentic"
        if not args.no_wt:
            command.append("--wt")
    if mode:
        command.append("--" + mode)
    if args.wt and not args.new_task:
        command.append("--wt")
    if args.no_wt:
        command.append("--no-wt")
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode:
        print(result.stdout, end="")
        return result.returncode
    try:
        payload = json.loads(result.stdout)
    except ValueError:
        return fail("invalid_engine_response", "Expected JSON from resolve-start")
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return fail("invalid_engine_response", "Missing successful resolver receipt")
    payload["entrypoint"] = "opd2"
    payload["engine_skill"] = "opd"
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
