"""
@header {
  "module": "test_state_tool_test_cycle",
  "layer": "test",
  "domain": "opal-tools",
  "description": "Task 162 S-2/S-7: TEST 추가 행 유형과 실행 사건 기반 시간을 공개 CLI로 검증",
  "exports": [],
  "depends": ["state_tool"]
}
"""

import json
import importlib.util
import pathlib
import subprocess
import sys
import time


TOOL = pathlib.Path(__file__).parents[1] / "state_tool.py"


def test_error_catalog_keeps_legacy_keys_frozen():
    spec = importlib.util.spec_from_file_location("state_tool_test_cycle", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert len(module.ERROR_CODES) == 59
    assert set(module.TEST_CYCLE_ERROR_CODES) == {
        "test_change_kind_requires_test",
        "test_clock_already_open", "test_clock_not_open",
    }
    for code, message in module.TEST_CYCLE_ERROR_CODES.items():
        assert module._error_template(code) == message


def cli(*args):
    result = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"stdout": result.stdout, "stderr": result.stderr}
    return result, payload


def task(tmp_path):
    path = tmp_path / "tasks" / "162-test-cycle"
    path.mkdir(parents=True)
    result, payload = cli("init", path, "--skill", "opd", "--mode", "agentic",
                          "--rows-spec", json.dumps([{"stage": "TEST", "item": "verify"}]),
                          "--run-log-mode", "off")
    assert result.returncode == 0, payload
    return path


def test_s2_distinct_fix_and_requirement_counts_do_not_block_feedback(tmp_path):
    path = task(tmp_path)
    for kind, count in (("fix", 2), ("requirement_change", 4)):
        for index in range(count):
            result, payload = cli("add-row", path, "--after-task-step-id", "1",
                                  "--stage", "TEST", "--item", f"{kind}-{index}",
                                  "--test-change-kind", kind)
            assert result.returncode == 0, payload
    result, metrics = cli("test-metrics", path)
    assert result.returncode == 0, metrics
    assert (metrics["fix_count"], metrics["requirement_change_count"]) == (2, 4)
    assert json.loads((path / "state.json").read_text())["current_status"] != "blocked"


def test_s2_kind_only_on_test_rows_and_legacy_rows_unclassified(tmp_path):
    path = task(tmp_path)
    before = (path / "state.json").read_bytes()
    result, denied = cli("add-row", path, "--after-task-step-id", "1", "--stage", "PLAN",
                         "--item", "wrong-stage", "--test-change-kind", "fix")
    assert result.returncode != 0, denied
    assert (path / "state.json").read_bytes() == before
    result, added = cli("add-row", path, "--after-task-step-id", "1", "--stage", "TEST",
                        "--item", "unclassified")
    assert result.returncode == 0, added
    before = (path / "state.json").read_bytes()
    result, metrics = cli("test-metrics", path)
    assert result.returncode == 0, metrics
    assert metrics["legacy_unclassified_rows"] == 2
    assert metrics["fix_count"] == metrics["requirement_change_count"] == 0
    assert (path / "state.json").read_bytes() == before


def test_s7_clock_intervals_overlap_duplicate_guards_and_legacy_unknown(tmp_path):
    path = task(tmp_path)
    legacy_result, legacy = cli("test-metrics", path)
    assert legacy_result.returncode == 0, legacy
    assert legacy["auto_seconds"] is None
    assert legacy["human_wait_seconds"] is None

    for kind, ident in (("human", "login"), ("human", "ddl"), ("auto", "unit")):
        result, payload = cli("test-clock", "start", path, "--kind", kind, "--id", ident)
        assert result.returncode == 0, payload
    duplicate, duplicate_payload = cli("test-clock", "start", path, "--kind", "human", "--id", "login")
    assert duplicate.returncode != 0, duplicate_payload
    open_result, open_metrics = cli("test-metrics", path)
    assert open_result.returncode == 0, open_metrics
    assert len(open_metrics["open_intervals"]) == 3
    assert open_metrics["human_wait_seconds"] is None
    time.sleep(0.05)
    for kind, ident in (("auto", "unit"), ("human", "login"), ("human", "ddl")):
        result, payload = cli("test-clock", "stop", path, "--kind", kind, "--id", ident)
        assert result.returncode == 0, payload
    unmatched, unmatched_payload = cli("test-clock", "stop", path, "--kind", "auto", "--id", "missing")
    assert unmatched.returncode != 0, unmatched_payload
    result, metrics = cli("test-metrics", path)
    assert result.returncode == 0, metrics
    assert metrics["auto_seconds"] > 0
    assert metrics["human_wait_seconds"] > 0
    assert metrics["open_intervals"] == []
    state = json.loads((path / "state.json").read_text())
    intervals = state["test_timing"]["intervals"]
    assert len(intervals) == 3
    assert all(item["started_at"] and item["ended_at"] for item in intervals)
    human_sum = sum((__import__("datetime").datetime.fromisoformat(i["ended_at"]) -
                     __import__("datetime").datetime.fromisoformat(i["started_at"])).total_seconds()
                    for i in intervals if i["kind"] == "human")
    assert metrics["human_wait_seconds"] < human_sum
