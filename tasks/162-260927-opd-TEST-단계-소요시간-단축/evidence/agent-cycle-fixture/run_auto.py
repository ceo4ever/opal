"""Execute A1/A2 while the PM's H1/H2 human clocks are open."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys


HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = HERE / "fixture-task"
REPO = HERE / "fixture-repo"
TRACE = HERE / "trace"
STATE = ROOT / "opal/tools/state-tool/run.sh"
TEST = ROOT / "opal/tools/test-tool/run.sh"


def call(label: str, command: list[str], cwd: pathlib.Path = HERE) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    output = {"command": command, "cwd": str(cwd), "exit_code": result.returncode,
              "stdout": result.stdout, "stderr": result.stderr}
    (TRACE / f"{label}.json").write_text(json.dumps(output, ensure_ascii=False, indent=2))
    return output


def metrics(label: str) -> dict:
    output = call(label, ["bash", str(STATE), "test-metrics", str(TASK)])
    if output["exit_code"]:
        raise RuntimeError(output)
    return json.loads(output["stdout"])


def main() -> None:
    before = metrics("pre-auto-metrics")
    opened = {(x["kind"], x["id"]) for x in before["open_intervals"]}
    if not {("human", "H1"), ("human", "H2")} <= opened:
        raise RuntimeError(f"both human intervals must already be open: {opened}")
    for ident, test_name in (("A1", "test_auto_a1"), ("A2", "test_auto_a2")):
        started = call(f"auto-{ident}-start", ["bash", str(STATE), "test-clock", "start", str(TASK), "--kind", "auto", "--id", ident])
        if started["exit_code"]:
            raise RuntimeError(started)
        try:
            result = call(f"auto-{ident}-pytest", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"test_fixture.py::{test_name}"], REPO)
        finally:
            stopped = call(f"auto-{ident}-stop", ["bash", str(STATE), "test-clock", "stop", str(TASK), "--kind", "auto", "--id", ident])
            if stopped["exit_code"]:
                raise RuntimeError(stopped)
        if result["exit_code"]:
            raise RuntimeError(result)
        marked = call(f"auto-{ident}-mark", ["bash", str(TEST), "scenario-mark", "--task-path", str(TASK), "--id", ident,
                                             "--result", "pass", "--evidence", f"trace/auto-{ident}-pytest.json exit=0; {result['stdout'].strip()}"])
        if marked["exit_code"]:
            raise RuntimeError(marked)
    after = metrics("post-auto-metrics")
    opened = {(x["kind"], x["id"]) for x in after["open_intervals"]}
    if opened != {("human", "H1"), ("human", "H2")}:
        raise RuntimeError(f"human intervals should remain open; auto closed: {opened}")
    print(json.dumps({"ok": True, "auto_seconds": after["auto_seconds"], "open_intervals": sorted(opened)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
