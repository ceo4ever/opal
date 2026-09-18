"""
@header {
  "module": "test_red_s3_run_json_shape",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "RED — S-3: `e2e run --target source-worktree` 실행 후 run.json이 CONTRACT.md §A.1 필수 키 전건(profile·actors·target·project_root·worktree_root·commit(40자)·dirty:true·dirty_files·urls.frontend·urls.backend·executors[]·candidates[]·driver_version)을 갖추고 commit이 git rev-parse HEAD와 일치하는지 검증한다.",
  "scenarios": ["S-3"],
  "exports": ["TestRunJsonShape"]
}

RED 근거: `e2e run` CLI 서브명령이 test_tool.py에 존재하지 않는다 (_build_parser에
resolve/check/unit/integration/scenario-*만 등록). run.json을 산출하는 어떤 경로도
없으므로 이 테스트는 실행 즉시 RED로 실패한다.
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
_SOURCE_ROOT = _TOOL_DIR.parent.parent.parent  # opal/tools/test-tool -> repo root
_TASK_PATH = _SOURCE_ROOT / "tasks" / "127-260912-oppl-E2E-하네스-구현"
_SCENARIO_ID = "S-3"
_PYTHON = sys.executable

_REQUIRED_RUN_JSON_KEYS = (
    "profile",
    "actors",
    "target",
    "project_root",
    "worktree_root",
    "commit",
    "dirty",
    "dirty_files",
    "urls",
    "executors",
    "candidates",
    "driver_version",
)


class TestRunJsonShape(unittest.TestCase):
    """S-3: run.json 필수 키 shape + commit 일치 검증."""

    @classmethod
    def setUpClass(cls):
        cls._real_head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=_SOURCE_ROOT, capture_output=True, text=True
        ).stdout.strip()

    def test_run_json_has_required_shape_and_matching_commit(self):
        with tempfile.TemporaryDirectory() as artifact_dir:
            import os
            env = os.environ.copy()
            env["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir

            proc = subprocess.run(
                [
                    _PYTHON, str(_TEST_TOOL_PY),
                    "e2e", "run",
                    "--scenario", _SCENARIO_ID,
                    "--task-path", str(_TASK_PATH),
                    "--target", "source-worktree",
                    "--worktree-root", str(_SOURCE_ROOT),
                ],
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )

            self.assertNotEqual(
                proc.returncode, 2,
                f"'e2e run' subcommand missing (RED target): {proc.stderr!r}",
            )

            run_json_path = pathlib.Path(artifact_dir) / "run.json"
            self.assertTrue(run_json_path.is_file(), f"run.json not produced at {run_json_path}")
            data = json.loads(run_json_path.read_text(encoding="utf-8"))

            missing = [key for key in _REQUIRED_RUN_JSON_KEYS if key not in data]
            self.assertEqual(missing, [], f"run.json missing required keys: {missing}")

            self.assertEqual(len(data.get("commit", "")), 40, "commit must be 40-char sha")
            self.assertEqual(data.get("commit"), self._real_head, "commit must equal git rev-parse HEAD")

            urls = data.get("urls") or {}
            self.assertIn("frontend", urls)
            self.assertIn("backend", urls)


if __name__ == "__main__":
    unittest.main()
