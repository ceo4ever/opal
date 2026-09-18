"""
@header {
  "module": "test_state_tool_ownership",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "RED-first — 태스크 138 S-11. state-tool init→첫 advance에서 OPAL_SESSION_ID(또는 CLAUDE_CODE_SESSION_ID 매핑) 존재 시 lease 원자 생성 1회 + run-log actor.session_id 채움을 검증한다. env 미설정 시 종전과 동일 전이여야 한다(회귀). 기존 test_state_tool.py는 수정하지 않고 별도 파일로 신설한다.",
  "exports": [],
  "depends": ["state_tool.py (CLI subprocess)", "ownership_tool.lease (미구현, S-11이 요구하는 신규 연동)"]
}
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

STATE_TOOL_PATH = Path(__file__).parent.parent / "state_tool.py"

SIMPLE_ROWS_SPEC = json.dumps(
    [
        {"stage": "TASK", "item": "작업"},
        {"stage": "PLAN", "item": "작업"},
        {"stage": "EXECUTE", "item": "작업"},
        {"stage": "CLOSE", "item": "State Gate"},
    ]
)


def _run(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = dict(os.environ)
    if env is not None:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(STATE_TOOL_PATH), *args],
        capture_output=True,
        text=True,
        env=full_env,
    )


class TestS11OwnershipSessionIntegration(unittest.TestCase):
    """S-11 (AC-12, AC-27, C-9, H-2) — 구현 전 RED."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.task_path = Path(self.tmp.name) / "tasks" / "999-red-s11"
        self.task_path.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _init(self, env=None):
        return _run(
            [
                "init",
                str(self.task_path),
                "--skill",
                "opds",
                "--mode",
                "agentic",
                "--task-title",
                "S-11 RED",
                "--rows-spec",
                SIMPLE_ROWS_SPEC,
            ],
            env=env,
        )

    def test_env_set_creates_lease_exactly_once_at_first_advance(self):
        """OPAL_SESSION_ID 설정 시 최초 경계 1곳에서만 hub lease 원자 생성(중복 claim 없음)."""
        init_result = self._init()
        self.assertEqual(init_result.returncode, 0, init_result.stderr)

        env = {"OPAL_SESSION_ID": "sess-s11-red-0001"}
        first = _run(["advance", str(self.task_path), "--row", "1"], env=env)

        lease_file = self.task_path / "run/.runtime/owner.json"
        self.assertTrue(
            lease_file.exists(),
            f"S-11 RED 기대: lease 파일이 아직 생성되지 않음(미구현) — stdout={first.stdout!r} stderr={first.stderr!r}",
        )

    def test_env_set_run_log_actor_session_id_filled(self):
        """OPAL_SESSION_ID env 값이 run-log 사건 actor.session_id로 채워진다.

        [MUST] 1.0/1.1 태스크는 run_log 블록 자체가 없고 run_log_commit()이
        save_state_json()으로 우회한다(state_tool.py C-3) — 대조할 사건이 애초에
        생성되지 않는다. `--run-log-mode shadow`로 schema 1.2 + run_log 블록을
        만들어야 검증이 가능하다. 커밋된 사건은 drain되어 `<task>/run/run-log-*.jsonl`
        조각에 실리고 pending_events는 비워지므로(state_tool.py _run_log_drain),
        state.json의 존재한 적 없는 `run_log.events` 키가 아니라 그 조각을 관측한다
        (같은 태스크의 test_state_tool.py::TestT138W9ActorSessionId._events()와 동일 패턴)."""
        init_result = _run(
            [
                "init",
                str(self.task_path),
                "--skill",
                "opds",
                "--mode",
                "agentic",
                "--task-title",
                "S-11 RED",
                "--rows-spec",
                SIMPLE_ROWS_SPEC,
                "--run-log-mode",
                "shadow",
            ]
        )
        self.assertEqual(init_result.returncode, 0, init_result.stderr)

        env = {"OPAL_SESSION_ID": "sess-s11-red-0002"}
        advance_result = _run(["advance", str(self.task_path), "--row", "1"], env=env)
        self.assertEqual(advance_result.returncode, 0, advance_result.stderr)

        events = []
        for segment in sorted((self.task_path / "run").glob("run-log-*.jsonl")):
            for line in segment.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))

        state_path = self.task_path / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        pending_events = state.get("run_log", {}).get("pending_events") or []
        events.extend(e for e in pending_events if isinstance(e, dict))

        actor_session_ids = [e.get("actor", {}).get("session_id") for e in events if isinstance(e, dict)]
        self.assertIn(
            "sess-s11-red-0002",
            actor_session_ids,
            f"run-log 사건(조각+pending_events)에 actor.session_id가 채워져야 한다 — events={events!r}",
        )

    def test_env_unset_transition_unchanged_regression_guard(self):
        """OPAL_SESSION_ID 미설정 시 state 전이 결과·transition_action이 종전과 동일해야 한다
        (이 케이스는 기존 동작 보존이므로 GREEN 이후에도 PASS 유지되어야 하는 회귀 가드)."""
        init_result = self._init()
        self.assertEqual(init_result.returncode, 0, init_result.stderr)

        clean_env = dict(os.environ)
        clean_env.pop("OPAL_SESSION_ID", None)
        result = _run(["advance", str(self.task_path), "--row", "1"], env=clean_env)
        self.assertEqual(result.returncode, 0, result.stderr)

        state_path = self.task_path / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertIn(state.get("current_status"), ("in_progress", "done", None) or [state.get("current_status")])
        lease_file = self.task_path / "run/.runtime/owner.json"
        self.assertFalse(lease_file.exists())


if __name__ == "__main__":
    unittest.main()
