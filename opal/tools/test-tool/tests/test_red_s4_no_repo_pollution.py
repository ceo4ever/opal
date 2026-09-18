"""
@header {
  "module": "test_red_s4_no_repo_pollution",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "RED — S-4: 깨끗한 저장소에서 `e2e run` 1회 완주 전후 `git status --porcelain`이 동일하고 dist/가 생기지 않으며, 격리된 OPAL_HOME override를 써서 사용자의 실제 ~/.opal을 건드리지 않는지 검증한다.",
  "scenarios": ["S-4"],
  "exports": ["TestNoRepoPollution"]
}

RED 근거: `e2e run` CLI 서브명령이 없다. 이 테스트는 실행 전/후 git status 비교와
dist/ 생성 여부를 검증하려 시도하지만, 서브명령 부재로 즉시 RED다. 사용자의 실제
~/.opal은 절대 건드리지 않는다 — OPAL_HOME을 tmp 디렉터리로 override한다.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_SOURCE_ROOT = _TOOL_DIR.parent.parent.parent  # opal/tools/test-tool -> repo root
_TASK_PATH = _SOURCE_ROOT / "tasks" / "127-260912-oppl-E2E-하네스-구현"
_SCENARIO_ID = "S-4"
_PYTHON = sys.executable


def _git_status_porcelain():
    return subprocess.run(
        ["git", "status", "--porcelain"], cwd=_SOURCE_ROOT, capture_output=True, text=True
    ).stdout


class TestNoRepoPollution(unittest.TestCase):
    """S-4: 깨끗한 저장소에서 e2e run 1회 완주해도 저장소가 오염되지 않아야 한다."""

    def test_repo_git_status_unchanged_and_no_dist_created(self):
        # 이 worktree는 작업 중 다른 태스크 산출물로 이미 dirty할 수 있다 — S-4의 요구는
        # "실행 전/후 git status --porcelain이 동일함"(dirty 여부 자체가 아니라 델타 0)이므로
        # 클린 전제조건이 없어도 이 델타 비교는 그대로 유효하다. 그리고 실제 RED 지점은
        # 그 이전 단계(`e2e run` 서브명령 부재)에서 먼저 발생한다.
        before = _git_status_porcelain()

        dist_path = _SOURCE_ROOT / "dist"
        dist_existed_before = dist_path.exists()

        with tempfile.TemporaryDirectory() as fake_opal_home, \
             tempfile.TemporaryDirectory() as artifact_dir:
            env = os.environ.copy()
            env["OPAL_HOME"] = fake_opal_home  # 사용자 실제 ~/.opal 격리
            env["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir

            proc = subprocess.run(
                [
                    _PYTHON, str(_TEST_TOOL_PY), "e2e", "run",
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
            try:
                json.loads(proc.stdout)
            except json.JSONDecodeError:
                self.fail(f"e2e run did not emit JSON stdout: {proc.stdout!r} / {proc.stderr!r}")

        after = _git_status_porcelain()
        self.assertEqual(before, after, "git status --porcelain must be identical before/after e2e run")

        dist_existed_after = dist_path.exists()
        self.assertEqual(
            dist_existed_before, dist_existed_after,
            "e2e run must not create dist/ in the repository",
        )


if __name__ == "__main__":
    unittest.main()
