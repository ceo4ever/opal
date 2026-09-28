"""Exercise focused fix retests and SHA/environment evidence reuse decisions."""

from __future__ import annotations

import hashlib
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
ALL = ["test_auto_a1", "test_auto_a2", "test_failed_scenario", "test_impact_scenario", "test_unknown_scenario"]
UNIT = ["test_auto_a1", "test_auto_a2"]


def call(label: str, command: list[str], *, profile: str = "v1", cwd: pathlib.Path = REPO) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TASK162_FIXTURE_PROFILE=profile)
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    output = {"command": command, "cwd": str(cwd), "profile": profile,
              "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    (TRACE / f"{label}.json").write_text(json.dumps(output, ensure_ascii=False, indent=2))
    return output


def require(output: dict, expected: int = 0) -> None:
    if output["exit_code"] != expected:
        raise RuntimeError(f"expected exit {expected}: {output}")


def sha() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def signature(profile: str) -> str:
    material = {"python": sys.version.split()[0], "pytest": "-q -p no:cacheprovider",
                "config_sha256": hashlib.sha256((REPO / "test_fixture.py").read_bytes()).hexdigest(),
                "profile": profile}
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


def pytest(label: str, selected: list[str], profile: str = "v1", expect: int = 0) -> dict:
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    command.extend(f"test_fixture.py::{name}" for name in selected)
    result = call(label, command, profile=profile)
    require(result, expect)
    return result


def fix_row(label: str) -> None:
    output = call(label, ["bash", str(STATE), "add-row", str(TASK), "--after-task-step-id", "1",
                          "--stage", "TEST", "--item", label, "--test-change-kind", "fix"], cwd=HERE)
    require(output)


def commit(label: str) -> str:
    require(call(f"{label}-git-add", ["git", "add", "app.py"]))
    require(call(f"{label}-git-commit", ["git", "-c", "user.name=Task162 Fixture", "-c", "user.email=fixture@example.invalid",
                                        "commit", "-qm", label]))
    return sha()


def main() -> None:
    if (TRACE / "s34-complete.json").exists():
        raise RuntimeError("fixture already completed; refusing duplicate run")
    base = sha()
    original = (REPO / "app.py").read_text()
    if "def value():\n    return 0" not in original:
        raise RuntimeError("fixture base differs; refusing to rewrite")

    # Observe the initial failure, and capture EXECUTE unit evidence at base SHA.
    pytest("s3-initial-full", ALL, expect=1)
    base_unit = pytest("s4-base-unit-pass", UNIT)
    base_signature = signature("v1")
    reuse_same = {"sha": base, "command": base_unit["command"], "environment_signature": base_signature,
                  "pass_output": str(TRACE / "s4-base-unit-pass.json"), "decision": "reuse", "rerun": False}
    (TRACE / "s4-same-signature-decision.json").write_text(json.dumps(reuse_same, indent=2))

    # Fix 1 changes app.py; impact map is known for failed and impact scenarios.
    fix_row("s3-fix-1-row")
    (REPO / "app.py").write_text(original.replace("def value():\n    return 0", "def value():\n    return 1"))
    first = commit("fixture fix 1")
    if first == base:
        raise RuntimeError("commit SHA failed to change")
    first_selected = ["test_failed_scenario", "test_impact_scenario"]
    (TRACE / "s3-fix-1-selection.json").write_text(json.dumps({"failed": ["test_failed_scenario"],
        "changed_files": ["app.py"], "impacted": ["test_impact_scenario"], "unknown": [],
        "selected": first_selected, "excluded_pass": ["test_auto_a1", "test_auto_a2", "test_unknown_scenario"],
        "reason": "explicit app.value dependency only; stable() tests unchanged"}, indent=2))
    pytest("s3-fix-1-focused", first_selected, expect=1)
    first_unit = pytest("s4-sha-changed-rerun", UNIT)
    (TRACE / "s4-sha-changed-decision.json").write_text(json.dumps({"source_sha": base, "target_sha": first,
        "same_command": base_unit["command"] == first_unit["command"], "same_environment_signature": base_signature == signature("v1"),
        "decision": "rerun", "result_path": str(TRACE / "s4-sha-changed-rerun.json")}, indent=2))

    # Fix 2 has an intentionally unresolved dependency relation; expand to the entire bundle.
    fix_row("s3-fix-2-row")
    (REPO / "app.py").write_text((REPO / "app.py").read_text().replace("def value():\n    return 1", "def value():\n    return 2"))
    second = commit("fixture fix 2")
    (TRACE / "s3-fix-2-selection.json").write_text(json.dumps({"failed": ["test_failed_scenario"],
        "changed_files": ["app.py"], "impacted": ["test_impact_scenario"],
        "unknown": ["test_unknown_scenario"], "selected": ALL,
        "reason": "unknown relation forces full scenario bundle; preserved PASS not assumed"}, indent=2))
    pytest("s3-fix-2-expanded", ALL)
    # Final full regression is a separate single run after the last fix.
    pytest("s3-final-full-regression", ALL)

    # A changed environment signature, even on the same SHA, invalidates reuse.
    changed_env = pytest("s4-env-changed-rerun", UNIT, profile="v2")
    (TRACE / "s4-env-changed-decision.json").write_text(json.dumps({"sha": second,
        "prior_profile": "v1", "target_profile": "v2", "prior_signature": signature("v1"),
        "target_signature": signature("v2"), "decision": "rerun", "result_path": str(TRACE / "s4-env-changed-rerun.json"),
        "exit_code": changed_env["exit_code"]}, indent=2))
    (TRACE / "s34-complete.json").write_text(json.dumps({"base_sha": base, "fix1_sha": first, "fix2_sha": second,
        "fix_count": 2, "focused_retests": ["s3-fix-1-focused.json", "s3-fix-2-expanded.json"],
        "final_full_regression": "s3-final-full-regression.json", "same_signature_reused": True,
        "sha_change_reran": True, "environment_change_reran": True}, indent=2))
    print((TRACE / "s34-complete.json").read_text())


if __name__ == "__main__":
    main()
