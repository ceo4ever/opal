"""
@header {
  "module": "test_skill_tester_todo_crud",
  "layer": "test",
  "domain": "opal-skill-tester",
  "description": "Fixes the reusable function-todo-crud scenario metadata, base regression behavior, and RED-first hidden test expectation.",
  "exports": []
}
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys


SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "skill_tester.py"
SCENARIO = SKILL_DIR / "scenarios" / "function-todo-crud"
BASE = SKILL_DIR / "scenarios" / "_bases" / "todo-web"
SPEC = importlib.util.spec_from_file_location("skill_tester", SCRIPT)
skill_tester = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(skill_tester)


def test_function_todo_crud_scenario_is_valid_and_reusable():
    assert skill_tester.validate_scenario("function-todo-crud") == []
    scenario = json.loads((SCENARIO / "scenario.json").read_text(encoding="utf-8"))
    assert scenario["id"] == "function-todo-crud"
    assert scenario["base"] == "_bases/todo-web"
    assert scenario["default_variant"] == "//opd"
    assert scenario["target_pilots"] == ["opd", "opds", "opsdd", "oppb"]
    assert "oppb" not in (SCENARIO / "request.md").read_text(encoding="utf-8").lower()


def test_todo_web_base_contains_required_opal_assets():
    for rel in (
        "_opal/AGENT.md",
        "_opal/code-scan.json",
        "_opal/MEMORY.json",
        "_opal/worktree.json",
        "docs/PROJECT.md",
        "_gitignore",
        "tasks/.gitkeep",
    ):
        assert (BASE / rel).exists(), rel
    assert not (BASE / ".opal").exists()


def test_todo_web_base_existing_tests_are_green():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests", "-p", "no:cacheprovider"],
        cwd=BASE,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_todo_web_base_is_red_for_crud_hidden_tests():
    env = os.environ.copy()
    env["SUT_REPO"] = str(BASE)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            str(SCENARIO / "hidden" / "test_hidden.py"),
            "-p",
            "no:cacheprovider",
        ],
        cwd=BASE,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "/api/todos" in result.stdout + result.stderr
