"""
@header {
  "module": "test_opal_agent_events",
  "layer": "test",
  "domain": "opal-tools",
  "description": "bootstrap 설정과 첫 줄 marker를 session event로 해석하는 우선순위 계약 RED-first 테스트",
  "task": "113",
  "scenarios": ["S-3"],
  "exports": ["TestSessionEventResolution"]
}

TASK 113 RED-first 테스트.
opal-agent의 공개 session-event resolver 반환값과 adapter 출력만 검증한다.
"""

import pathlib
import sys
import unittest


_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
import opal_agent as OA  # noqa: E402


class TestSessionEventResolution(unittest.TestCase):
    """S-3: disabled > worker > assistant > project 순서로 event가 결정된다."""

    def setUp(self):
        self.resolve = getattr(OA, "resolve_session_event", None)
        self.assertTrue(
            callable(self.resolve),
            "공개 resolve_session_event(prompt, bootstrap_enabled, project_detected)가 필요하다",
        )

    def test_bootstrap_disabled_has_highest_precedence(self):
        event = self.resolve(
            "[WORKER]\nrun task",
            bootstrap_enabled=False,
            project_detected=True,
        )
        self.assertEqual(event, "session.disabled")

    def test_worker_first_line_precedes_assistant_and_project(self):
        event = self.resolve(
            "[WORKER]\n[ASSISTANT]\nrun task",
            bootstrap_enabled=True,
            project_detected=True,
        )
        self.assertEqual(event, "session.worker")

    def test_assistant_first_line_precedes_project(self):
        event = self.resolve(
            "[ASSISTANT]\nhelp me",
            bootstrap_enabled=True,
            project_detected=True,
        )
        self.assertEqual(event, "session.assistant")

    def test_unmarked_project_is_project_aware_not_pm(self):
        event = self.resolve(
            "inspect this project",
            bootstrap_enabled=True,
            project_detected=True,
        )
        self.assertEqual(event, "session.project")

    def test_unmarked_non_project_is_general_assistant(self):
        event = self.resolve(
            "hello",
            bootstrap_enabled=True,
            project_detected=False,
        )
        self.assertEqual(event, "session.assistant")

    def test_opal_bootstrap_cli_mapping_uses_same_events(self):
        worker_prompt = OA.ClaudeAdapter().build_invocation(
            OA.AgentConfig(prompt="task", opal_bootstrap="off"),
            "claude",
        ).cmd[2]
        assistant_prompt = OA.ClaudeAdapter().build_invocation(
            OA.AgentConfig(prompt="help", opal_bootstrap="assistant"),
            "claude",
        ).cmd[2]
        self.assertEqual(
            self.resolve(worker_prompt, bootstrap_enabled=True, project_detected=True),
            "session.worker",
        )
        self.assertEqual(
            self.resolve(assistant_prompt, bootstrap_enabled=True, project_detected=True),
            "session.assistant",
        )


if __name__ == "__main__":
    unittest.main()
