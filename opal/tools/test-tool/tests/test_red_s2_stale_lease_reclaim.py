"""
@header {
  "module": "test_red_s2_stale_lease_reclaim",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "RED — S-2: owner_pid가 죽은 stale lease record가 있을 때 새 run이 EADDRINUSE 없이 포트를 회수/재할당하고 회수 사실을 산출물에 기록하는지 검증한다. lib/e2e/ports.py는 아직 lease 개념 자체가 없다(문서화된 D-7 정지선).",
  "scenarios": ["S-2"],
  "exports": ["TestStaleLeaseReclaim"]
}

RED 근거: lib/e2e/ports.py의 모듈 docstring은 "allocator lock·lease record·stale
회수·worktree 동시성(§A.7, C-LEASE-1/2, MV-36)은 T03 소유이며 이 모듈에 stub조차
두지 않는다(D-7)"라고 명시한다. CONTRACT.md §A.7 lease record 경로
`{artifact_root}/.leases/{lease_id}.json`도 아직 어떤 모듈도 쓰지 않는다. 이 테스트는
공개 CLI(`e2e run`)로 stale lease를 만든 뒤 재실행해 회수를 증명하려 시도하지만,
`e2e run` 서브명령 자체가 없으므로 RED다.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_PYTHON = sys.executable
_TASK_PATH = _TOOL_DIR.parent.parent.parent / "tasks" / "127-260912-oppl-E2E-하네스-구현"
_SCENARIO_ID = "S-2"


class TestStaleLeaseReclaim(unittest.TestCase):
    """S-2: owner_pid가 죽은 stale lease를 새 run이 회수해야 한다."""

    def test_stale_lease_is_reclaimed_without_eaddrinuse(self):
        with tempfile.TemporaryDirectory() as artifact_root:
            leases_dir = pathlib.Path(artifact_root) / ".leases"
            leases_dir.mkdir(parents=True, exist_ok=True)

            # 이미 죽은 PID를 owner_pid로 하는 stale lease record를 CONTRACT.md §A.7
            # 형식으로 직접 배치한다 (죽은 PID 확보: 자식 프로세스를 즉시 종료해 얻는다).
            dead = subprocess.Popen([sys.executable, "-c", "pass"])
            dead.wait()
            dead_pid = dead.pid

            stale_lease = {
                "schema_version": "2.0",
                "lease_id": "stale-run-backend",
                "run_id": "stale-run",
                "owner_pid": dead_pid,
                "port": 18765,
                "role": "backend",
                "state": "reserved",
                "created_at": "2020-01-01T00:00:00+09:00",
                "confirmed_at": None,
                "attempt": 1,
            }
            (leases_dir / "stale-run-backend.json").write_text(
                json.dumps(stale_lease, ensure_ascii=False), encoding="utf-8"
            )

            env = {"OPAL_E2E_ARTIFACT_DIR": artifact_root}
            import os
            full_env = os.environ.copy()
            full_env.update(env)

            proc = subprocess.run(
                [
                    _PYTHON, str(_TEST_TOOL_PY), "e2e", "run",
                    "--scenario", _SCENARIO_ID,
                    "--task-path", str(_TASK_PATH),
                    "--target", "source-worktree",
                    "--worktree-root", str(_TOOL_DIR.parent.parent),
                ],
                capture_output=True,
                text=True,
                env=full_env,
                timeout=60,
            )

            # RED target: 'e2e run' 서브명령이 없으므로 argparse가 invalid choice로
            # exit code 2를 반환한다. 실기능이 있다면 EADDRINUSE 없이 성공(0) 혹은
            # 정상적인 최종 상태 exit code여야 한다.
            self.assertNotEqual(
                proc.returncode, 2,
                f"'e2e run' subcommand missing — cannot exercise stale lease reclaim (RED target): {proc.stderr!r}",
            )
            data = json.loads(proc.stdout)
            self.assertNotIn(
                "EADDRINUSE", json.dumps(data),
                "stale lease reclaim must avoid EADDRINUSE on reuse/reallocation",
            )
            self.assertTrue(
                data.get("lease_reclaimed") or data.get("candidates"),
                "reclamation fact must be recorded in run artifacts",
            )


if __name__ == "__main__":
    unittest.main()
