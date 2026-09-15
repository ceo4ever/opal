"""
@header {
  "module": "test_red_s1_concurrent_port_isolation",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "RED — S-1: main 작업본 1개와 서로 다른 worktree 2개에서 `test-tool e2e run`을 동시 실행해도 포트가 겹치지 않고 독립 종료·포트 해제가 되는지 검증한다. 현재 CLI에 e2e run 서브명령 자체가 없어 RED다.",
  "scenarios": ["S-1"],
  "exports": ["TestConcurrentPortIsolation"]
}

RED 근거: opal/tools/test-tool/test_tool.py의 _build_parser()는 resolve/check/unit/
integration/scenario-* 서브명령만 등록한다. `e2e run`은 존재하지 않으므로 argparse가
반드시 실패(exit code 2, invalid choice)한다. 이 테스트는 그 부재를 공개 CLI 표면
(subprocess 호출)으로 증명한다 — 아직 구현되지 않은 기능을 사설 내부 함수로 우회
호출하지 않는다.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_PYTHON = sys.executable
_TASK_PATH = _TOOL_DIR.parent.parent.parent / "tasks" / "127-260912-oppl-E2E-하네스-구현"
_SCENARIO_ID = "S-1"


def _run_e2e(target_root: str, extra_args=None):
    # CONTRACT.md §B.1.1: --scenario·--task-path·--target은 필수다.
    args = [
        _PYTHON, str(_TEST_TOOL_PY), "e2e", "run",
        "--scenario", _SCENARIO_ID,
        "--task-path", str(_TASK_PATH),
        "--target", "source-worktree",
        "--worktree-root", target_root,
    ]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(args, capture_output=True, text=True, timeout=30)


class TestConcurrentPortIsolation(unittest.TestCase):
    """S-1: 3개의 동시 e2e run이 서로 다른 포트를 임대하고 독립 종료해야 한다."""

    def test_three_concurrent_runs_do_not_collide_and_release_ports(self):
        with tempfile.TemporaryDirectory() as t1, \
             tempfile.TemporaryDirectory() as t2, \
             tempfile.TemporaryDirectory() as t3:
            roots = [t1, t2, t3]
            procs = []
            for root in roots:
                # --target=source-worktree일 때 --worktree-root로 서로 다른 worktree를
                # 구분한다(§B.1.1 표). --scenario·--task-path는 필수 인자다.
                args = [
                    _PYTHON, str(_TEST_TOOL_PY), "e2e", "run",
                    "--scenario", _SCENARIO_ID,
                    "--task-path", str(_TASK_PATH),
                    "--target", "source-worktree",
                    "--worktree-root", root,
                ]
                procs.append(subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))

            results = []
            for proc in procs:
                stdout, stderr = proc.communicate(timeout=60)
                results.append((proc.returncode, stdout, stderr))

            # 서브명령이 실제로 존재해야 아래 검증이 의미가 있다. 지금은 존재하지
            # 않으므로 이 assert에서 RED로 실패한다 (argparse invalid choice, exit 2).
            for returncode, stdout, stderr in results:
                self.assertNotEqual(
                    returncode, 2,
                    f"'e2e run' subcommand missing — argparse rejected it (RED target): {stderr!r}",
                )

            run_jsons = []
            for _, stdout, _ in results:
                data = json.loads(stdout)
                run_jsons.append(data)

            backend_ports = {d["urls"]["backend"] for d in run_jsons}
            frontend_ports = {d["urls"]["frontend"] for d in run_jsons}
            self.assertEqual(len(backend_ports), 3, "backend ports must not collide across concurrent runs")
            self.assertEqual(len(frontend_ports), 3, "frontend ports must not collide across concurrent runs")

            for root, data in zip(roots, run_jsons):
                self.assertEqual(data.get("project_root"), root, "each run's urls/project_root must point at its own target")


if __name__ == "__main__":
    unittest.main()
