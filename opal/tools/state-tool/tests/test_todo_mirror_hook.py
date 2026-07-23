"""
@header {
  "module": "test_todo_mirror_hook",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "076 F-002: todo_mirror_hook.py 단위 테스트 (TS-010~013). 합성 stdin JSON으로 (1)state-tool advance+payload→additionalContext 주입 (2)비state-tool/비Bash Bash 명령→무출력 exit0(H-6) (3)stderr 경고 혼입 stdout에서 마지막 JSON 라인 payload 추출(H-5) (4)payload 부재·깨진 JSON(stdin/stdout)→무출력 exit0 fail-safe(DEC-9) 를 검증한다. 스크립트 subprocess 실행(exit0 실증) + 순수 함수 직접 호출 병행. 표준 라이브러리만.",
  "exports": ["TestTodoMirrorHook", "TestHookPureFunctions"]
}
"""

# 076 T-2: 표준 라이브러리만 import
import json
import pathlib
import subprocess
import sys
import unittest

_TEST_DIR = pathlib.Path(__file__).parent
_TOOL_DIR = _TEST_DIR.parent
_HOOK = _TOOL_DIR / "todo_mirror_hook.py"

# 순수 함수 직접 호출용 import (import 부작용 없음 — 함수 정의 + __main__ 가드만)
sys.path.insert(0, str(_TOOL_DIR))
import todo_mirror_hook as HOOK


def _mirror_payload(action="update", stage="TASK", status="in_progress"):
    return {
        "action": action,
        "todos": [{
            "id":         f"stage:{stage}",
            "content":    f"{stage} 단계",
            "activeForm": f"{stage} 단계 진행 중",
            "status":     status,
        }],
    }


class TestTodoMirrorHook(unittest.TestCase):
    """스크립트 end-to-end(subprocess) — 실 exit0 fail-safe 실증 포함."""

    def _run_hook(self, stdin_obj):
        """스크립트를 subprocess로 실행 → (returncode, stdout_str)."""
        raw = stdin_obj if isinstance(stdin_obj, str) else json.dumps(stdin_obj)
        proc = subprocess.run(
            [sys.executable, str(_HOOK)],
            input=raw, capture_output=True, text=True,
        )
        return proc.returncode, proc.stdout.strip()

    def test_ts010_state_tool_advance_injects_context(self):
        """TS-010: state-tool advance stdin(todo_mirror 포함) →
        hookSpecificOutput.additionalContext에 지시문+payload 출력."""
        stdin = {
            "tool_name": "Bash",
            "tool_input": {
                "command": '"$HOME/.opal/tools/state-tool/run.sh" advance /tmp/task --row 1'
            },
            "tool_response": {
                "stdout": json.dumps({"ok": True, "command": "advance",
                                      "todo_mirror": _mirror_payload("update", "TASK", "in_progress")})
            },
        }
        code, out = self._run_hook(stdin)
        self.assertEqual(code, 0)
        self.assertTrue(out, "additionalContext 미출력")
        obj = json.loads(out)
        hso = obj["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PostToolUse")
        ctx = hso["additionalContext"]
        self.assertIn("파이프라인 todo 미러", ctx)   # 지시문
        self.assertIn("advance", ctx)                # 서브명령
        self.assertIn("stage:TASK", ctx)             # payload 포함
        self.assertIn("SSOT", ctx)                   # SSOT 불변 문구

    def test_ts011_non_state_tool_no_output(self):
        """TS-011: 비state-tool Bash 명령 stdin → 무출력·exit0 (H-6)."""
        stdin = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la /tmp"},
            "tool_response": {"stdout": "file1\nfile2"},
        }
        code, out = self._run_hook(stdin)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_ts011_non_bash_tool_no_output(self):
        """TS-011(보강): 비Bash 도구 이벤트 → 무출력·exit0 (DEC-9)."""
        stdin = {"tool_name": "Read", "tool_input": {}, "tool_response": {}}
        code, out = self._run_hook(stdin)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_ts012_stdout_with_warning_lines(self):
        """TS-012(H-5): stdout에 stderr 경고 라인 혼입 + 마지막 JSON 라인 → payload 추출 성공."""
        payload_line = json.dumps({"ok": True, "command": "mark",
                                   "todo_mirror": _mirror_payload("update", "PLAN", "completed")})
        stdout = "WARNING: --rows-from .md is deprecated\nsome noise line\n" + payload_line
        stdin = {
            "tool_name": "Bash",
            "tool_input": {"command": "~/.opal/tools/state-tool/run.sh mark /tmp/task --row 2 --done"},
            "tool_response": {"stdout": stdout},
        }
        code, out = self._run_hook(stdin)
        self.assertEqual(code, 0)
        self.assertTrue(out)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("stage:PLAN", ctx)
        self.assertIn("mark", ctx)

    def test_ts013_mirrored_cmd_without_payload_no_output(self):
        """TS-013(DEC-9): 미러 대상 명령이나 stdout에 todo_mirror 부재 → 무출력·exit0."""
        stdin = {
            "tool_name": "Bash",
            "tool_input": {"command": "~/.opal/tools/state-tool/run.sh init /tmp/task"},
            "tool_response": {"stdout": json.dumps({"ok": True, "command": "init"})},
        }
        code, out = self._run_hook(stdin)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_ts013_broken_json_stdin_no_output(self):
        """TS-013(DEC-9): 깨진 JSON stdin → 무출력·exit0 (예외 격리)."""
        code, out = self._run_hook("{ this is not valid json ")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_ts013_broken_json_stdout_no_output(self):
        """TS-013(DEC-9): state-tool 명령이나 stdout이 깨진 JSON → 무출력·exit0."""
        stdin = {
            "tool_name": "Bash",
            "tool_input": {"command": "~/.opal/tools/state-tool/run.sh advance /tmp/task --row 1"},
            "tool_response": {"stdout": "{ broken json not parseable"},
        }
        code, out = self._run_hook(stdin)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")


class TestHookPureFunctions(unittest.TestCase):
    """순수 함수 경계 — 필터·추출 로직 직접 검증."""

    def test_is_state_tool_event_true_for_mirrored(self):
        for cmd in ("init", "advance", "mark", "block"):
            self.assertTrue(
                HOOK.is_state_tool_event(f"~/.opal/tools/state-tool/run.sh {cmd} /tmp/t"),
                f"{cmd} 미러 대상 오탐",
            )

    def test_is_state_tool_event_false_for_non_mirrored(self):
        # show/validate 등은 미러 대상 아님
        self.assertFalse(HOOK.is_state_tool_event("~/.opal/tools/state-tool/run.sh show /tmp/t"))
        # state-tool 아님
        self.assertFalse(HOOK.is_state_tool_event("ls -la"))
        self.assertFalse(HOOK.is_state_tool_event("python3 other.py advance"))

    def test_extract_todo_mirror_returns_last(self):
        stdout = (
            json.dumps({"todo_mirror": {"action": "create", "todos": []}}) + "\n"
            + json.dumps({"todo_mirror": {"action": "update", "todos": [{"id": "stage:X"}]}})
        )
        payload = HOOK.extract_todo_mirror(stdout)
        self.assertEqual(payload["action"], "update")

    def test_extract_todo_mirror_none_when_absent(self):
        self.assertIsNone(HOOK.extract_todo_mirror('{"ok": true, "command": "init"}'))
        self.assertIsNone(HOOK.extract_todo_mirror("plain text no json"))
        self.assertIsNone(HOOK.extract_todo_mirror(""))

    def test_extract_command_fail_safe(self):
        self.assertEqual(HOOK.extract_command({"command": "ls"}), "ls")
        self.assertEqual(HOOK.extract_command({}), "")
        self.assertEqual(HOOK.extract_command(None), "")
        self.assertEqual(HOOK.extract_command({"command": 123}), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
