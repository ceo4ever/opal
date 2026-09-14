"""
@header {
  "module": "test_opal_agent_cli_runtime",
  "layer": "test",
  "domain": "opal-tools",
  "description": "opal-agent watchdog 인자의 CLI 경로 검증. 실제 OPPL 호출 경로가 run.sh 셸 호출(opal-loop-action-agent AGENT.md)이므로, call_agent로만 도달 가능한 상태면 AC-1·AC-16이 실제 경로에서 도달 불가다. run.sh를 subprocess로 직접 실행해 상한 거부와 heartbeat mode 범위를 관측한다.",
  "exports": ["TestCliTimeoutLimitRejection", "TestCliHeartbeatIsStreamOnly"],
  "task": "131",
  "scenarios": ["S-6", "S-12"]
}

# 인용 규칙
# - TEST-SCENARIO.md(131) S-6(상한 초과 요청 거부)·S-12(heartbeat stream 전용, D10)의
#   CLI 경로 몫. 두 시나리오의 라이브러리 경로는 test_opal_agent_runtime.py가 소유하며
#   이 파일은 그 파일을 열지도 수정하지도 않는다.
# - [MUST] coding-principles "검증과 증거": 문구 존재 확인이 아니라 run.sh를 실제로
#   실행해 종료 코드·stderr·산출물로 관측한다. mock/patch를 쓰지 않는다.
# - provider CLI(`claude`)는 호출하지 않는다 — --bin에 더미 셸 스크립트를 주입한다.
"""

import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"

RESULT_JSON = json.dumps({
    "type": "result", "subtype": "success", "is_error": False,
    "result": "fixture", "result_index": 0, "num_turns": 1,
    "terminal_reason": "completed", "api_error_status": None,
    "total_cost_usd": 0.5, "duration_ms": 3000,
    "session_id": "00000000-0000-4000-8000-0000000000d1",
    "uuid": "00000000-0000-4000-8000-000000000071",
})


class CliSandbox(unittest.TestCase):
    """run.sh를 실제로 실행하는 공통 베이스."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="opal-agent-cli-"))
        self.run_dir = self.tmp / ".oppl-run"
        self.run_dir.mkdir()
        self.spawn_marker = self.tmp / "spawned.marker"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def script(self, name: str, body: str) -> str:
        path = self.tmp / name
        path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return str(path)

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        """run.sh를 그대로 실행한다 — 배포 래퍼가 없으면 같은 인터프리터로 대체한다.

        run.sh는 ~/.opal/.venv 파이썬을 쓰므로, 미배포 작업본에서는 동일 argv를
        현재 인터프리터로 실행해 CLI 표면(argparse → call_agent) 자체를 검증한다.
        """
        venv_python = pathlib.Path(os.path.expanduser("~/.opal/.venv/bin/python"))
        if _RUN_SH.exists() and os.access(_RUN_SH, os.X_OK) and venv_python.exists():
            cmd = [str(_RUN_SH), *args]
        else:
            cmd = [sys.executable, str(_TOOL_DIR / "opal_agent.py"), *args]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


# ─── S-6 / AC-1 — CLI 경로 ─────────────────────────────────────

class TestCliTimeoutLimitRejection(CliSandbox):
    """상한 초과 요청은 CLI 경로에서도 프로세스 생성 0건으로 거부돼야 한다."""

    def silent_grandchild(self, name="cli_silent.sh", sleep_sec=120) -> str:
        return self.script(name, (
            f': > "{self.spawn_marker}"\n'
            f"sh -c 'sleep {sleep_sec}' &\n"
            f"sleep {sleep_sec}\n"
        ))

    def _expect_rejected(self, *limit_args: str):
        started = time.monotonic()
        proc = self.cli(
            "fixture prompt", "--json",
            "--bin", self.silent_grandchild(),
            "--timeout", "120",
            "--run-dir", str(self.run_dir), "--phase", "t1",
            *limit_args,
        )
        elapsed = time.monotonic() - started

        self.assertEqual(proc.returncode, 2, f"stderr={proc.stderr[:400]!r}")
        self.assertIn("timeout_limit_exceeded", proc.stderr)
        self.assertLess(elapsed, 30, "거부 경로가 자식 프로세스를 기다렸습니다.")
        self.assertFalse(
            self.spawn_marker.exists(),
            "거부되어야 할 요청에서 자식 프로세스가 생성됐습니다(spawn marker 존재).",
        )
        self.assertEqual(
            list(self.run_dir.iterdir()), [],
            "거부 경로에서 산출물 파일이 생성됐습니다.",
        )

    def test_s6_cli_request_over_phase_limit_spawns_nothing(self):
        self._expect_rejected("--phase-timeout-limit-sec", "5")

    def test_s6_cli_request_over_max_timeout_spawns_nothing(self):
        self._expect_rejected("--max-timeout-sec", "5")

    def test_s6_cli_request_within_limits_is_not_rejected(self):
        """상한 안의 요청은 거부되지 않는다 — 거부가 무조건이 아님을 고정한다."""
        proc = self.cli(
            "fixture prompt", "--json",
            "--bin", self.script("ok.sh", f"printf '%s\\n' '{RESULT_JSON}'\n"),
            "--timeout", "20",
            "--phase-timeout-limit-sec", "60", "--max-timeout-sec", "60",
            "--run-dir", str(self.run_dir), "--phase", "t1",
        )
        self.assertEqual(proc.returncode, 0, f"stderr={proc.stderr[:400]!r}")
        self.assertNotIn("timeout_limit_exceeded", proc.stderr)
        self.assertTrue((self.run_dir / "t1.result.json").exists())


# ─── S-12 / AC-16, D10 — CLI 경로 ──────────────────────────────

class TestCliHeartbeatIsStreamOnly(CliSandbox):
    """--heartbeat-timeout-sec는 CLI 경로에서도 stream mode 전용이다(D10)."""

    def silent_then_done(self, name: str) -> str:
        return self.script(name, (
            f': > "{self.spawn_marker}"\n'
            "sleep 3\n"
            f"printf '%s\\n' '{RESULT_JSON}'\n"
        ))

    def test_s12_cli_sync_ignores_heartbeat_and_completes(self):
        proc = self.cli(
            "fixture prompt", "--json",
            "--bin", self.silent_then_done("cli_sync.sh"),
            "--timeout", "20",
            "--heartbeat-timeout-sec", "1",
            "--terminate-grace-sec", "1",
            "--run-dir", str(self.run_dir), "--phase", "sync",
        )
        self.assertEqual(proc.returncode, 0, f"stderr={proc.stderr[:400]!r}")

        record = json.loads((self.run_dir / "sync.attempt.json").read_text(encoding="utf-8"))
        self.assertEqual(record.get("status"), "done")
        self.assertNotEqual(record.get("exit_class"), "timed_out")
        self.assertIsNone(record.get("timeout_reason"))
        # sync에는 heartbeat 상한 자체가 적용되지 않는다.
        self.assertIsNone(record["heartbeat"]["timeout_sec"])
        self.assertFalse(record["heartbeat"]["expired"])

    def test_s12_cli_stream_applies_heartbeat_timeout(self):
        """같은 인자라도 stream mode에서는 heartbeat이 적용돼 판정이 갈린다."""
        proc = self.cli(
            "fixture prompt", "--stream",
            "--bin", self.silent_then_done("cli_stream.sh"),
            "--timeout", "20",
            "--heartbeat-timeout-sec", "1",
            "--terminate-grace-sec", "1",
            "--run-dir", str(self.run_dir), "--phase", "stream",
        )
        self.assertEqual(proc.returncode, 2, f"stderr={proc.stderr[:400]!r}")
        self.assertIn("heartbeat", proc.stderr)

        record = json.loads((self.run_dir / "stream.attempt.json").read_text(encoding="utf-8"))
        self.assertEqual(record.get("status"), "timed_out")
        self.assertEqual(record.get("exit_class"), "timed_out")
        self.assertEqual(record.get("timeout_reason"), "heartbeat")
        self.assertTrue(record.get("pgid_reclaimed"))


if __name__ == "__main__":
    unittest.main()
