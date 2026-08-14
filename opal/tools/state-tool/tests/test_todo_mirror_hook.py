"""
@header {
  "module": "test_todo_mirror_hook",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "076 F-002: todo_mirror_hook.py 단위 테스트 (TS-010~013). 합성 stdin JSON으로 (1)state-tool advance+payload→additionalContext 주입 (2)비state-tool/비Bash Bash 명령→무출력 exit0(H-6) (3)stderr 경고 혼입 stdout에서 마지막 JSON 라인 payload 추출(H-5) (4)payload 부재·깨진 JSON(stdin/stdout)→무출력 exit0 fail-safe(DEC-9) 를 검증한다. 스크립트 subprocess 실행(exit0 실증) + 순수 함수 직접 호출 병행. 표준 라이브러리만. 088: TestHistoryLinkRelay 신설(TS-8~TS-10) — stdout의 todo_mirror+history_link 동시 존재 시 reminder 원문이 기존 todo 미러 지시문과 병존 릴레이·history_link 부재 시 기존 동작 불변(대조군으로 미주입의 선택성 확증)·history_link 단독일 때도 exit0+reminder 주입을 스크립트 subprocess 실행으로만 검증(mock 없음). 091(RED-first, mode:red, F-004 §3.4.2 (7)): TestGateChecklistRelay 신설(TEST-SCENARIO S-18~S-19) — extract_gate_checklist()/build_additional_context()의 gate_checklist 인자가 아직 없어(Step 9 GREEN 이전) stdout의 gate_checklist가 릴레이되지 않는 것이 RED 증거. gate_checklist 단독 주입(S-18)과 076 todo_mirror·088 history_link·091 gate_checklist 3종 병존(S-19)을 스크립트 subprocess 실행으로만 검증(mock 없음).",
  "exports": ["TestTodoMirrorHook", "TestHookPureFunctions", "TestHistoryLinkRelay", "TestGateChecklistRelay"]
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


# ═════════════════════════════════════════════════════════════════════════════
# 088: TestHistoryLinkRelay — history_link.reminder 릴레이 확장 (TS-8~TS-10)
# PLAN 088 §2.7 — 기존 todo_mirror 주입을 유지한 채 리마인더를 덧붙이는 **병존**
# 확장(교체 아님). [MUST] red-first.md §4: 훅 스크립트 subprocess 실행(공개 경계)
# 으로만 검증하며 내부 함수를 mock하지 않는다.
# ═════════════════════════════════════════════════════════════════════════════

_HL_REMINDER = (
    "[메모리 히스토리] 작업 히스토리 행이 자동 생성되었다(핵심결과 미기재). 지금 보강하라:\n"
    '"$HOME/.opal/tools/memory-tool/run.sh" update --file /tmp/proj/.opal/MEMORY.json '
    '--kind history --title "088 클로즈 메모리히스토리 자동연결" '
    '--result "<무엇을 바꿨는지 + 결과>"'
)


def _history_link_payload(status="created", reminder=_HL_REMINDER):
    return {
        "status":      status,
        "title":       "088 클로즈 메모리히스토리 자동연결",
        "path":        "tasks/088-260811-opp-클로즈-메모리히스토리-자동연결/",
        "stage":       "완료",
        "memory_file": "/tmp/proj/.opal/MEMORY.json",
        "reminder":    reminder,
    }


class TestHistoryLinkRelay(unittest.TestCase):
    """088 R-5: state-tool mark stdout의 history_link.reminder가 PostToolUse
    additionalContext로 원문 그대로 릴레이되는지 검증한다(스크립트 subprocess)."""

    _MARK_CMD = '"$HOME/.opal/tools/state-tool/run.sh" mark /tmp/proj/tasks/t --row 9 --done'

    def _run_hook(self, stdin_obj):
        raw = stdin_obj if isinstance(stdin_obj, str) else json.dumps(stdin_obj)
        proc = subprocess.run(
            [sys.executable, str(_HOOK)],
            input=raw, capture_output=True, text=True,
        )
        return proc.returncode, proc.stdout.strip()

    def _stdin_for(self, stdout_obj):
        return {
            "tool_name": "Bash",
            "tool_input": {"command": self._MARK_CMD},
            "tool_response": {"stdout": json.dumps(stdout_obj, ensure_ascii=False)},
        }

    def test_ts8_both_payloads_relay_reminder_verbatim(self):
        """TS-8: stdout에 todo_mirror + history_link가 동시 존재 →
        additionalContext에 기존 todo_mirror 주입과 reminder 원문이 **둘 다** 포함."""
        stdin = self._stdin_for({
            "ok": True, "command": "mark",
            "todo_mirror":  _mirror_payload("update", "CLOSE", "completed"),
            "history_link": _history_link_payload(),
        })
        code, out = self._run_hook(stdin)
        self.assertEqual(code, 0)
        self.assertTrue(out, "additionalContext 미출력 — 두 페이로드 병존 시 출력되어야 함")
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        # 기존 todo_mirror 주입 보존(병존, 교체 아님)
        self.assertIn("파이프라인 todo 미러", ctx)
        self.assertIn("stage:CLOSE", ctx)
        # 신규 리마인더 원문 릴레이
        self.assertIn(_HL_REMINDER, ctx,
                      f"reminder 원문이 그대로 포함되어야 함, 실제 ctx={ctx!r}")

    def test_ts9_absent_history_link_preserves_existing_behavior(self):
        """TS-9 (회귀/선택성): history_link 부재(기존 payload) → 기존 todo_mirror 주입이
        불변이고 리마인더가 섞이지 않는다. **동일 stdin에 history_link만 얹은 대조군**과
        비교해 미주입이 선택적임을 확증한다(부재만 단언하면 기능 부재 시에도 통과하는
        공허한 가드가 되므로)."""
        base_stdout = {
            "ok": True, "command": "mark",
            "todo_mirror": _mirror_payload("update", "PLAN", "in_progress"),
        }
        # (1) history_link 부재 → 기존 동작 불변
        code, out = self._run_hook(self._stdin_for(base_stdout))
        self.assertEqual(code, 0)
        self.assertTrue(out, "기존 todo_mirror 단독 주입이 유지되어야 함")
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("파이프라인 todo 미러", ctx)
        self.assertIn("stage:PLAN", ctx)
        self.assertIn("SSOT", ctx)
        self.assertNotIn(_HL_REMINDER, ctx,
                         f"history_link 부재 시 리마인더가 붙으면 안 됨: {ctx!r}")

        # (2) 대조군 — 동일 payload + history_link → 리마인더가 붙고, 기존 주입은 보존
        code2, out2 = self._run_hook(self._stdin_for(
            dict(base_stdout, history_link=_history_link_payload())))
        self.assertEqual(code2, 0)
        self.assertTrue(out2, "대조군은 출력이 있어야 함")
        ctx2 = json.loads(out2)["hookSpecificOutput"]["additionalContext"]
        self.assertIn(_HL_REMINDER, ctx2,
                      f"대조군에는 리마인더가 붙어야 함(미주입의 선택성 확증): {ctx2!r}")
        self.assertIn("stage:PLAN", ctx2, "대조군에서도 기존 todo_mirror 주입은 보존되어야 함")

    def test_ts10_history_link_only_still_injects(self):
        """TS-10: history_link만 있고 todo_mirror가 없어도 exit 0 + reminder 주입.
        (기존 '페이로드 부재 → 무출력' 경로가 history_link 단독을 삼키면 안 된다.)"""
        stdin = self._stdin_for({
            "ok": True, "command": "mark",
            "history_link": _history_link_payload(),
        })
        code, out = self._run_hook(stdin)
        self.assertEqual(code, 0)
        self.assertTrue(out, "history_link 단독일 때도 additionalContext가 출력되어야 함")
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn(_HL_REMINDER, ctx,
                      f"reminder 원문이 포함되어야 함, 실제 ctx={ctx!r}")


# ═════════════════════════════════════════════════════════════════════════════
# 091 F-004 §3.4.2 (7): TestGateChecklistRelay — gate_checklist 릴레이 (S-18~S-19)
# [MUST] red-first.md §4: extract_gate_checklist()/build_additional_context()의
# gate_checklist 인자는 아직 todo_mirror_hook.py에 없다(Step 9 GREEN 이전) — 아래는
# additionalContext에 게이트 리마인더/checklist가 섞이지 않는 것이 RED 증거다.
# 스크립트 subprocess 실행(공개 경계)만 사용 — 내부 함수 mock 없음.
# ═════════════════════════════════════════════════════════════════════════════

_GATE_REMINDER = (
    "[PM Gate 점검] 아래 checklist 전 항목을 확인한 뒤 다음 단계로 진행하라. "
    "SSOT는 해당 pilot references/pipeline.json task_steps[].gate 이다."
)


def _gate_checklist_payload(key="plan.pm_gate", stage="PLAN", item="PM Gate",
                            artifacts=None, checklist=None, reminder=_GATE_REMINDER):
    return {
        "key":       key,
        "stage":     stage,
        "item":      item,
        "artifacts": artifacts if artifacts is not None else ["TASK.md", "PLAN.md"],
        "checklist": checklist if checklist is not None else ["TASK.md 요구사항", "PLAN.md §4.2"],
        "reminder":  reminder,
    }


class TestGateChecklistRelay(unittest.TestCase):
    """091 R-11(b)/R-12: state-tool mark stdout의 gate_checklist가 PostToolUse
    additionalContext로 릴레이되는지 검증한다(스크립트 subprocess, mock 없음).

    R-12가 SKILL.md의 PM Gate 체크리스트 표를 삭제하는 짝으로, mark stdout이
    유일한 checklist 노출 경로가 된다 — 이 릴레이가 없으면 정보 손실이 발생한다
    (§3.4.2 (7) 확대 근거 1).
    """

    _MARK_CMD = '"$HOME/.opal/tools/state-tool/run.sh" mark /tmp/proj/tasks/t --task-step plan.pm_gate --done'

    def _run_hook(self, stdin_obj):
        raw = stdin_obj if isinstance(stdin_obj, str) else json.dumps(stdin_obj)
        proc = subprocess.run(
            [sys.executable, str(_HOOK)],
            input=raw, capture_output=True, text=True,
        )
        return proc.returncode, proc.stdout.strip()

    def _stdin_for(self, stdout_obj):
        return {
            "tool_name": "Bash",
            "tool_input": {"command": self._MARK_CMD},
            "tool_response": {"stdout": json.dumps(stdout_obj, ensure_ascii=False)},
        }

    def test_s18_gate_checklist_alone_injects_additional_context(self):
        """[T091/L2-S18] stdout에 gate_checklist만 존재 → hook exit 0 +
        additionalContext에 게이트 리마인더 + checklist 항목 포함(S-12 실제 stdout을
        stdin으로 주입하는 시나리오의 최소 재현)."""
        payload = _gate_checklist_payload()
        stdin = self._stdin_for({"ok": True, "command": "mark", "gate_checklist": payload})
        code, out = self._run_hook(stdin)
        self.assertEqual(code, 0)
        self.assertTrue(out, "gate_checklist 단독일 때도 additionalContext가 출력되어야 함")
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn(_GATE_REMINDER, ctx, f"게이트 리마인더가 포함되어야 함: {ctx!r}")
        self.assertIn("TASK.md 요구사항", ctx, f"checklist 항목이 포함되어야 함: {ctx!r}")

    def test_s19_three_payloads_coexist(self):
        """[T091/L2-S19] 076 todo_mirror · 088 history_link · 091 gate_checklist
        3종이 동시에 있을 때 additionalContext에 셋 다 병존 출력(교체 아님, 기존
        2-페이로드 병존 계약의 회귀 보호 + 신규 페이로드 추가)."""
        stdin = self._stdin_for({
            "ok": True, "command": "mark",
            "todo_mirror":    _mirror_payload("update", "PLAN", "in_progress"),
            "history_link":   _history_link_payload(),
            "gate_checklist": _gate_checklist_payload(),
        })
        code, out = self._run_hook(stdin)
        self.assertEqual(code, 0)
        self.assertTrue(out, "3종 병존 시 출력이 있어야 함")
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("파이프라인 todo 미러", ctx, "076 todo_mirror 지시문이 보존되어야 함")
        self.assertIn("stage:PLAN", ctx, "076 todo_mirror payload가 보존되어야 함")
        self.assertIn(_HL_REMINDER, ctx, "088 history_link reminder가 보존되어야 함")
        self.assertIn(_GATE_REMINDER, ctx, "091 gate_checklist reminder가 추가되어야 함")


if __name__ == "__main__":
    unittest.main(verbosity=2)
