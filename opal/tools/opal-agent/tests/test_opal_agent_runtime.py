"""
@header {
  "module": "test_opal_agent_runtime",
  "layer": "test",
  "domain": "opal-tools",
  "description": "opal_agent.py 실행 원시 기능(D1/D5/D9/D10·terminal framing) RED-first 테스트. 프로세스 수명주기·PGID 회수·파일 소유·실행 중 증분 관측은 실제 subprocess로만 검증하고(mock 금지), terminal 판정은 tests/fixtures/ stream fixture 6종으로 검증한다.",
  "exports": [
    "TestPhaseDeadlineProcessGroupReclaim", "TestTimeoutLimitRejection",
    "TestTerminalFramingMultiResultEpilogue", "TestTerminalFramingUnknownEvent",
    "TestTerminalFramingChildUnterminated", "TestExitClassApiError",
    "TestCostUsedIsTerminalCandidate", "TestHeartbeatIsStreamOnly",
    "TestRunDirOutputOwnership", "TestStreamLiveWindow",
    "TestOriginIsNotUsedForDecision"
  ],
  "task": "131",
  "scenarios": ["S-5", "S-6", "S-7", "S-8", "S-9", "S-10", "S-11", "S-12", "S-13", "S-23", "S-28"]
}

# 인용 규칙
# - TEST-SCENARIO.md(131) Scenarios S-5·S-6·S-7·S-8·S-9·S-10·S-11·S-12·S-13·S-23·S-28 ↔
#   PLAN.md(131) Decisions D1(출력 소유)·D5(origin 비의존)·D9(exit_class)·D10(heartbeat stream 전용)
#   및 W-5 ①~⑥ 기준.
# - [MUST] red-first.md §2 작성자≠구현자: 이 파일은 opal-test-agent(RED)가 작성하며
#   GREEN(W-5) 전까지 opal_agent.py를 수정하지 않는다. 기존 test_opal_agent.py·
#   test_opal_agent_events.py도 수정하지 않는다.
# - [MUST] PRINCIPLES.md §4 "Don't fake it": S-5·S-6·S-12·S-13·S-23의 프로세스 수명주기·
#   PGID 소멸·파일 소유·증분 관측은 mock/patch를 쓰지 않는다. 실제 subprocess로 무출력
#   프로세스와 손자 프로세스를 띄우고, 소멸은 os.kill(pgid, 0)의 ProcessLookupError로 확인한다.
# - provider CLI(`claude`)는 호출하지 않는다 — config.bin에 더미 셸 스크립트를 주입한다
#   (TEST-SCENARIO.md Setup "대역 사용과 한계").
#
# 이 파일이 고정하는 공개 계약(RED 시점에는 전부 미구현):
#   OA.analyze_stream(stdout) -> StreamVerdict
#       .status                 "done" | "running" | "error"
#       .exit_class             OA.EXIT_CLASSES 중 하나
#       .terminal               terminal candidate result 이벤트 dict (없으면 None)
#       .cost_used              terminal candidate의 total_cost_usd (합산 금지, C-10)
#       .origin                 진단 전용(판정 분기에 사용 금지, D5)
#       .unterminated_children  stream 종료 시점 미종료 자식 task_id 목록
#   OA.EXIT_CLASSES = ok / impl_failure / api_error / timed_out /
#                     output_format_invalid / framing_error   (D9)
#   OA.EPILOGUE_ALLOWLIST = background_tasks_changed / task_updated / task_notification
#   AgentConfig·call_agent 신규 인자: run_dir, phase, attempt,
#                                     heartbeat_timeout_sec, terminate_grace_sec,
#                                     max_timeout_sec                    (D1/D10/W-5②)
#   CLI 신규 인자: --run-dir / --phase / --attempt                        (D1)
#   산출물: <run-dir>/<phase>[.aN].events.jsonl | .result.json | .err.log |
#           .exitcode | .attempt.json                                    (D1/D4)
"""

import ast
import json
import os
import pathlib
import shutil
import stat
import sys
import tempfile
import threading
import time
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
import opal_agent as OA  # noqa: E402

FIXTURES = pathlib.Path(__file__).parent / "fixtures"

# W-1 fixture별 기대 판정 — expected.json이 아니라 테스트 코드 상수로 둔다(PLAN W-1).
EXPECTED = {
    "stream_single_result.jsonl":        {"status": "done",  "exit_class": "ok",
                                          "cost_used": 1.1229666},
    "stream_multi_result_epilogue.jsonl": {"status": "done", "exit_class": "ok",
                                          "cost_used": 3.4706659999999996},
    "stream_api_error.jsonl":            {"status": "error", "exit_class": "api_error",
                                          "cost_used": 3.466276400000001},
    "stream_unknown_after_result.jsonl": {"status": "error", "exit_class": "framing_error",
                                          "cost_used": 1.1229666},
    "stream_child_unterminated.jsonl":   {"status": ("running", "error"),
                                          "exit_class": ("framing_error", "ok"),
                                          "cost_used": 2.5},
    "stream_multiline_object.jsonl":     {"status": "error",
                                          "exit_class": "output_format_invalid",
                                          "cost_used": None},
}


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def assert_code(testcase, exc: BaseException, code: str) -> None:
    """오류 코드는 예외 속성 `code` 또는 메시지 토큰으로 관측한다."""
    observed = getattr(exc, "code", None)
    testcase.assertTrue(
        observed == code or code in str(exc),
        f"오류 코드 {code!r}를 관측하지 못했습니다: code={observed!r} msg={str(exc)[:300]!r}",
    )


def pgid_alive(pgid: int) -> bool:
    """PGID 생존 여부 — 소멸은 ProcessLookupError로만 확정한다."""
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class ScriptSandbox(unittest.TestCase):
    """더미 셸 스크립트와 run-dir을 실제 파일로 만드는 공통 베이스."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="opal-agent-runtime-"))
        self.run_dir = self.tmp / ".oppl-run"
        self.run_dir.mkdir()
        self.spawn_marker = self.tmp / "spawned.marker"
        self._pgids: list[int] = []

    def tearDown(self):
        for pgid in self._pgids:
            try:
                os.killpg(pgid, 9)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def script(self, name: str, body: str) -> str:
        path = self.tmp / name
        path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return str(path)

    def silent_grandchild_script(self, name="silent_grandchild.sh", sleep_sec=120) -> str:
        """stdout을 전혀 내지 않으면서 손자 프로세스를 fork한 뒤 대기한다."""
        return self.script(name, (
            f': > "{self.spawn_marker}"\n'
            f"sh -c 'sleep {sleep_sec}' &\n"
            f"sleep {sleep_sec}\n"
        ))

    def record_pgid(self, pgid: int) -> None:
        if isinstance(pgid, int) and pgid > 0:
            self._pgids.append(pgid)

    def attempt_record(self, phase: str, attempt: str | None = None) -> dict:
        suffix = f".{attempt}" if attempt else ""
        path = self.run_dir / f"{phase}{suffix}.attempt.json"
        self.assertTrue(path.exists(), f"attempt record가 없습니다: {path}")
        return json.loads(path.read_text(encoding="utf-8"))


# ─── S-5 / AC-1 ────────────────────────────────────────────────

class TestPhaseDeadlineProcessGroupReclaim(ScriptSandbox):
    """S-5: phase별 고유 deadline에 TERM→grace→KILL, PGID 전체(손자 포함) 소멸."""

    def _run_phase(self, phase: str, timeout: int):
        started = time.monotonic()
        with self.assertRaises(OA.OpalAgentTimeout):
            OA.call_agent(
                "fixture prompt",
                bin=self.silent_grandchild_script(f"{phase}_silent.sh"),
                timeout=timeout,
                terminate_grace_sec=1,
                run_dir=str(self.run_dir),
                phase=phase,
            )
        return time.monotonic() - started

    def _assert_phase_reclaimed(self, phase: str, timeout: int):
        elapsed = self._run_phase(phase, timeout)
        self.assertGreaterEqual(elapsed, timeout)
        self.assertLess(elapsed, timeout + 5)

        record = self.attempt_record(phase)
        self.assertEqual(record.get("status"), "timed_out")
        self.assertEqual(record.get("exit_class"), "timed_out")

        pgid = record.get("pgid")
        self.assertIsInstance(pgid, int)
        self.record_pgid(pgid)
        self.assertFalse(
            pgid_alive(pgid),
            f"phase {phase}의 PGID {pgid}가 손자 프로세스와 함께 소멸하지 않았습니다.",
        )

    def test_s5_phase_t1_deadline_reclaims_whole_process_group(self):
        self._assert_phase_reclaimed("t1", 2)

    def test_s5_phase_g_deadline_reclaims_whole_process_group(self):
        self._assert_phase_reclaimed("g", 3)

    def test_s5_grandchild_is_not_left_behind(self):
        self._run_phase("t1", 2)
        pgid = self.attempt_record("t1")["pgid"]
        self.record_pgid(pgid)
        self.assertRaises(ProcessLookupError, os.killpg, pgid, 0)


# ─── S-6 / AC-1 ────────────────────────────────────────────────

class TestTimeoutLimitRejection(ScriptSandbox):
    """S-6: phase 상한·max_hard_timeout_sec 초과 요청은 프로세스 생성 0건으로 거부."""

    def _expect_rejected(self, **kwargs):
        with self.assertRaises(OA.OpalAgentError) as ctx:
            OA.call_agent(
                "fixture prompt",
                bin=self.silent_grandchild_script(),
                run_dir=str(self.run_dir),
                phase="t1",
                **kwargs,
            )
        assert_code(self, ctx.exception, "timeout_limit_exceeded")
        self.assertFalse(
            self.spawn_marker.exists(),
            "거부되어야 할 요청에서 자식 프로세스가 생성됐습니다(spawn marker 존재).",
        )
        self.assertEqual(list(self.run_dir.iterdir()), [],
                         "거부 경로에서 산출물 파일이 생성됐습니다.")

    def test_s6_request_over_phase_limit_spawns_nothing(self):
        self._expect_rejected(timeout=120, phase_timeout_limit_sec=5)

    def test_s6_request_over_max_hard_timeout_spawns_nothing(self):
        self._expect_rejected(timeout=120, max_timeout_sec=5)


# ─── S-7 / AC-2, C-9 ───────────────────────────────────────────

class TestTerminalFramingMultiResultEpilogue(unittest.TestCase):
    """S-7: 선행 turn + terminal candidate + 허용 epilogue → done, 마지막 물리 줄 비의존."""

    NAME = "stream_multi_result_epilogue.jsonl"

    def test_s7_only_terminal_candidate_is_consumed(self):
        # 마지막 물리 줄은 result가 아니다 — 마지막 줄 의존 구현이면 여기서 갈린다.
        lines = [l for l in read_fixture(self.NAME).splitlines() if l.strip()]
        self.assertNotEqual(json.loads(lines[-1]).get("type"), "result")

        verdict = OA.analyze_stream(read_fixture(self.NAME))
        self.assertEqual(verdict.status, EXPECTED[self.NAME]["status"])
        self.assertEqual(verdict.exit_class, EXPECTED[self.NAME]["exit_class"])
        self.assertEqual(verdict.terminal.get("result_index"), 1)
        self.assertEqual(verdict.unterminated_children, [])

    def test_s7_preceding_turn_requires_same_session_and_monotonic_index(self):
        """C-9/D5: session_id가 다르거나 result_index가 단조 증가하지 않으면 error."""
        events = [json.loads(l) for l in read_fixture(self.NAME).splitlines() if l.strip()]

        broken_session = [dict(e) for e in events]
        for e in broken_session:
            if e.get("type") == "result" and e.get("result_index") == 0:
                e["session_id"] = "00000000-0000-4000-8000-0000000000ff"
        verdict = OA.analyze_stream(
            "".join(json.dumps(e) + "\n" for e in broken_session))
        self.assertEqual(verdict.status, "error")

        broken_index = [dict(e) for e in events]
        for e in broken_index:
            if e.get("type") == "result" and e.get("result_index") == 0:
                e["result_index"] = 3
        verdict = OA.analyze_stream(
            "".join(json.dumps(e) + "\n" for e in broken_index))
        self.assertEqual(verdict.status, "error")

    def test_s7_origin_is_diagnostic_only(self):
        """D5: origin을 제거해도 판정이 바뀌지 않는다."""
        events = [json.loads(l) for l in read_fixture(self.NAME).splitlines() if l.strip()]
        stripped = []
        for e in events:
            e = dict(e)
            e.pop("origin", None)
            stripped.append(e)
        with_origin = OA.analyze_stream(read_fixture(self.NAME))
        without_origin = OA.analyze_stream(
            "".join(json.dumps(e) + "\n" for e in stripped))
        self.assertEqual(with_origin.status, without_origin.status)
        self.assertEqual(with_origin.exit_class, without_origin.exit_class)


# ─── S-8 / AC-3 ────────────────────────────────────────────────

class TestTerminalFramingUnknownEvent(unittest.TestCase):
    """S-8: terminal candidate 뒤 allowlist 밖 이벤트 → done 아님, framing_error."""

    NAME = "stream_unknown_after_result.jsonl"

    def test_s8_epilogue_allowlist_is_exactly_three_subtypes(self):
        self.assertEqual(
            set(OA.EPILOGUE_ALLOWLIST),
            {"background_tasks_changed", "task_updated", "task_notification"},
        )

    def test_s8_unknown_trailing_event_is_framing_error(self):
        verdict = OA.analyze_stream(read_fixture(self.NAME))
        self.assertNotEqual(verdict.status, "done")
        self.assertEqual(verdict.status, "error")
        self.assertEqual(verdict.exit_class, "framing_error")


# ─── S-9 / AC-3 ────────────────────────────────────────────────

class TestTerminalFramingChildUnterminated(unittest.TestCase):
    """S-9: 종료 시점 미종료 자식 잔존 → done 아님. fixture ②와 판정이 갈린다."""

    NAME = "stream_child_unterminated.jsonl"

    def test_s9_unterminated_child_blocks_done(self):
        verdict = OA.analyze_stream(read_fixture(self.NAME))
        self.assertNotEqual(verdict.status, "done")
        self.assertIn(verdict.status, ("running", "error"))
        self.assertIn("bfixture02", verdict.unterminated_children)

    def test_s9_diverges_from_transiently_running_child_fixture(self):
        """중간에 실행 중 task가 있다가 뒤에서 닫히는 fixture ②는 done이어야 한다."""
        closed = OA.analyze_stream(read_fixture("stream_multi_result_epilogue.jsonl"))
        open_child = OA.analyze_stream(read_fixture(self.NAME))
        self.assertEqual(closed.status, "done")
        self.assertNotEqual(open_child.status, closed.status)


# ─── S-10 / AC-14, C-12 ────────────────────────────────────────

class TestExitClassApiError(unittest.TestCase):
    """S-10: terminal_reason=api_error·429 → exit_class=api_error (impl_failure와 분리)."""

    NAME = "stream_api_error.jsonl"

    def test_s10_exit_class_enum_is_fixed(self):
        self.assertEqual(
            set(OA.EXIT_CLASSES),
            {"ok", "impl_failure", "api_error", "timed_out",
             "output_format_invalid", "framing_error"},
        )

    def test_s10_api_error_is_classified_apart_from_impl_failure(self):
        verdict = OA.analyze_stream(read_fixture(self.NAME))
        self.assertEqual(verdict.exit_class, "api_error")
        self.assertNotEqual(verdict.exit_class, "impl_failure")
        self.assertEqual(verdict.terminal.get("api_error_status"), 429)
        self.assertTrue(verdict.terminal.get("is_error"))

    def test_s10_impl_failure_uses_a_different_exit_class(self):
        """같은 is_error라도 api_error가 아니면 impl_failure로 갈린다."""
        events = [json.loads(l) for l in read_fixture(self.NAME).splitlines() if l.strip()]
        for e in events:
            if e.get("type") == "result":
                e["terminal_reason"] = "error_during_execution"
                e["api_error_status"] = None
        verdict = OA.analyze_stream("".join(json.dumps(e) + "\n" for e in events))
        self.assertEqual(verdict.exit_class, "impl_failure")


# ─── S-11 / AC-15, C-10 ────────────────────────────────────────

class TestCostUsedIsTerminalCandidate(unittest.TestCase):
    """S-11: adapter가 노출하는 비용은 terminal candidate 단일 값이며 합산이 아니다."""

    NAME = "stream_multi_result_epilogue.jsonl"

    def test_s11_cost_equals_terminal_candidate(self):
        verdict = OA.analyze_stream(read_fixture(self.NAME))
        self.assertEqual(verdict.cost_used, EXPECTED[self.NAME]["cost_used"])
        self.assertEqual(verdict.cost_used, verdict.terminal.get("total_cost_usd"))

    def test_s11_cost_is_not_the_sum_of_results(self):
        """fixture ②는 선행 비용이 0이라 합/단일값이 같다 — 두 값이 갈리는 stream으로 고정한다."""
        events = [json.loads(l) for l in read_fixture(self.NAME).splitlines() if l.strip()]
        for e in events:
            if e.get("type") == "result" and e.get("result_index") == 0:
                e["total_cost_usd"] = 1.25
            if e.get("type") == "result" and e.get("result_index") == 1:
                e["total_cost_usd"] = 2.5
        verdict = OA.analyze_stream("".join(json.dumps(e) + "\n" for e in events))
        self.assertEqual(verdict.cost_used, 2.5)
        self.assertNotEqual(verdict.cost_used, 3.75)


# ─── S-12 / AC-16, C-11, D10 ───────────────────────────────────

class TestHeartbeatIsStreamOnly(ScriptSandbox):
    """S-12: heartbeat_timeout_sec는 stream 전용. sync는 hard timeout만 적용한다."""

    RESULT_JSON = json.dumps({
        "type": "result", "subtype": "success", "is_error": False,
        "result": "fixture", "result_index": 0, "num_turns": 1,
        "terminal_reason": "completed", "api_error_status": None,
        "total_cost_usd": 0.5, "duration_ms": 3000,
        "session_id": "00000000-0000-4000-8000-0000000000d1",
        "uuid": "00000000-0000-4000-8000-000000000071",
    })

    def silent_then_done(self, name):
        return self.script(name, (
            f': > "{self.spawn_marker}"\n'
            "sleep 3\n"
            f"printf '%s\\n' '{self.RESULT_JSON}'\n"
        ))

    def test_s12_sync_ignores_heartbeat_and_completes(self):
        result = OA.call_agent(
            "fixture prompt",
            bin=self.silent_then_done("sync_silent.sh"),
            output_format="json",
            timeout=20,
            heartbeat_timeout_sec=1,
            terminate_grace_sec=1,
            run_dir=str(self.run_dir),
            phase="sync",
        )
        self.assertFalse(result.is_error)
        record = self.attempt_record("sync")
        self.assertEqual(record.get("status"), "done")
        self.assertNotEqual(record.get("exit_class"), "timed_out")

    def test_s12_stream_applies_heartbeat_timeout(self):
        with self.assertRaises(OA.OpalAgentTimeout) as ctx:
            OA.call_agent(
                "fixture prompt",
                bin=self.silent_then_done("stream_silent.sh"),
                output_format="stream-json",
                timeout=20,
                heartbeat_timeout_sec=1,
                terminate_grace_sec=1,
                run_dir=str(self.run_dir),
                phase="stream",
            )
        assert_code(self, ctx.exception, "heartbeat")
        record = self.attempt_record("stream")
        self.assertEqual(record.get("status"), "timed_out")
        self.record_pgid(record.get("pgid"))
        self.assertFalse(pgid_alive(record["pgid"]))

    def _assert_hard_timeout_reclaim(self, phase: str, fmt: str):
        with self.assertRaises(OA.OpalAgentTimeout):
            OA.call_agent(
                "fixture prompt",
                bin=self.silent_grandchild_script(f"{phase}.sh"),
                output_format=fmt,
                timeout=2,
                terminate_grace_sec=1,
                run_dir=str(self.run_dir),
                phase=phase,
            )
        record = self.attempt_record(phase)
        self.assertEqual(record.get("status"), "timed_out")
        self.record_pgid(record.get("pgid"))
        self.assertFalse(pgid_alive(record["pgid"]))

    def test_s12_hard_timeout_and_pgid_reclaim_in_sync_mode(self):
        self._assert_hard_timeout_reclaim("hard_sync", "json")

    def test_s12_hard_timeout_and_pgid_reclaim_in_stream_mode(self):
        self._assert_hard_timeout_reclaim("hard_stream", "stream-json")


# ─── S-13 / AC-13, D1 ──────────────────────────────────────────

class TestRunDirOutputOwnership(ScriptSandbox):
    """S-13: opal-agent가 mode별 산출물을 소유하고 직렬화 불일치를 output_format_invalid로 거부."""

    RESULT_JSON = TestHeartbeatIsStreamOnly.RESULT_JSON

    def test_s13_sync_writes_single_json_object(self):
        OA.call_agent(
            "fixture prompt",
            bin=self.script("sync_ok.sh", f"printf '%s\\n' '{self.RESULT_JSON}'\n"),
            output_format="json",
            timeout=20,
            run_dir=str(self.run_dir),
            phase="t3",
            attempt="a1",
        )
        result_path = self.run_dir / "t3.a1.result.json"
        self.assertTrue(result_path.exists())
        self.assertIsInstance(
            json.loads(result_path.read_text(encoding="utf-8")), dict)
        self.assertFalse((self.run_dir / "t3.a1.events.jsonl").exists())
        self.assertTrue((self.run_dir / "t3.a1.err.log").exists())
        self.assertEqual(
            (self.run_dir / "t3.a1.exitcode").read_text(encoding="utf-8").strip(), "0")

    def test_s13_stream_writes_one_object_per_line(self):
        body = "".join(
            f"printf '%s\\n' '{line}'\n"
            for line in read_fixture("stream_single_result.jsonl").splitlines()
        )
        OA.call_agent(
            "fixture prompt",
            bin=self.script("stream_ok.sh", body),
            output_format="stream-json",
            timeout=20,
            run_dir=str(self.run_dir),
            phase="t3",
            attempt="a2",
        )
        events_path = self.run_dir / "t3.a2.events.jsonl"
        self.assertTrue(events_path.exists())
        lines = [l for l in events_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(lines), 3)
        for line in lines:
            self.assertIsInstance(json.loads(line), dict)
        self.assertFalse((self.run_dir / "t3.a2.result.json").exists())
        self.assertTrue((self.run_dir / "t3.a2.err.log").exists())
        self.assertEqual(
            (self.run_dir / "t3.a2.exitcode").read_text(encoding="utf-8").strip(), "0")

    def test_s13_multiline_jsonl_is_output_format_invalid(self):
        raw = read_fixture("stream_multiline_object.jsonl")
        payload = self.tmp / "multiline.jsonl"
        payload.write_text(raw, encoding="utf-8")
        with self.assertRaises(OA.OpalAgentError) as ctx:
            OA.call_agent(
                "fixture prompt",
                bin=self.script("stream_broken.sh", f'cat "{payload}"\n'),
                output_format="stream-json",
                timeout=20,
                run_dir=str(self.run_dir),
                phase="broken",
            )
        assert_code(self, ctx.exception, "output_format_invalid")
        record = self.attempt_record("broken")
        self.assertNotEqual(record.get("status"), "done")
        self.assertEqual(record.get("exit_class"), "output_format_invalid")

    def test_s13_analyze_stream_rejects_multiline_object(self):
        verdict = OA.analyze_stream(read_fixture("stream_multiline_object.jsonl"))
        self.assertEqual(verdict.exit_class, "output_format_invalid")
        self.assertNotEqual(verdict.status, "done")

    def test_s13_cli_accepts_run_dir_phase_attempt(self):
        argv = [
            "fixture prompt", "--json",
            "--bin", self.script("cli_ok.sh", f"printf '%s\\n' '{self.RESULT_JSON}'\n"),
            "--run-dir", str(self.run_dir), "--phase", "cli", "--attempt", "a1",
        ]
        self.assertEqual(OA.main(argv), 0)
        self.assertTrue((self.run_dir / "cli.a1.result.json").exists())


# ─── S-23 / H-4 ────────────────────────────────────────────────

class TestStreamLiveWindow(ScriptSandbox):
    """S-23: stream 산출물은 실행 중 줄 단위 append+flush로 증분 관측된다."""

    def test_s23_events_file_grows_while_process_is_alive(self):
        lines = read_fixture("stream_single_result.jsonl").splitlines()
        body = "".join(f"printf '%s\\n' '{l}'\nsleep 1\n" for l in lines)
        errors: list[BaseException] = []

        def run():
            try:
                OA.call_agent(
                    "fixture prompt",
                    bin=self.script("stream_live.sh", body),
                    output_format="stream-json",
                    timeout=30,
                    run_dir=str(self.run_dir),
                    phase="live",
                )
            except BaseException as exc:  # noqa: BLE001 — RED 관측용
                errors.append(exc)

        worker = threading.Thread(target=run, daemon=True)
        worker.start()

        events_path = self.run_dir / "live.events.jsonl"
        exitcode_path = self.run_dir / "live.exitcode"
        counts: list[int] = []
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and worker.is_alive():
            if events_path.exists():
                n = len([l for l in events_path.read_text(encoding="utf-8").splitlines()
                         if l.strip()])
                if not counts or n != counts[-1]:
                    counts.append(n)
                    self.assertFalse(
                        exitcode_path.exists(),
                        "프로세스 생존 중인데 .exitcode가 이미 생성됐습니다 "
                        "(atomic rename으로 종료 시점에만 나타나는 동작).",
                    )
                if len(counts) >= 2:
                    break
            time.sleep(0.2)
        worker.join(timeout=30)

        self.assertEqual(errors, [], f"stream 실행이 예외로 끝났습니다: {errors}")
        self.assertGreaterEqual(
            len(counts), 2,
            f"실행 중 증분 관측에 실패했습니다(관측된 줄 수 추이: {counts}).",
        )
        self.assertGreater(counts[-1], counts[0])
        self.assertTrue(exitcode_path.exists())


# ─── S-28 / H-1, C-9, D5 ───────────────────────────────────────

class TestOriginIsNotUsedForDecision(unittest.TestCase):
    """S-28: origin 부재는 오류가 아니며, origin은 판정 분기에 등장하지 않는다(D5).

    ②③(소스 검사)은 현재 소스에 `origin`·"replay"가 0건이라 단독으로는 지금도 통과한다 —
    RED 증거가 되지 않으므로 `analyze_stream` 구현 존재를 전제 조건으로 묶어 지금 실패시킨다.
    """

    NAME = "stream_single_result.jsonl"
    SOURCE = _TOOL_DIR / "opal_agent.py"
    README = _TOOL_DIR / "README.md"

    def require_adapter(self):
        """판정 adapter가 구현되기 전에는 소스 검사 자체가 성립하지 않는다."""
        self.assertTrue(
            hasattr(OA, "analyze_stream"),
            "analyze_stream 미구현 — origin 비의존(D5) 소스 검사의 전제가 성립하지 않습니다.",
        )

    @staticmethod
    def decision_conditions(source_text: str) -> list[str]:
        """판정 분기 조건식만 추출한다 — 진단 목적의 대입·기록은 대상이 아니다."""
        tree = ast.parse(source_text)
        conditions: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.IfExp, ast.Assert)):
                conditions.append(ast.unparse(node.test))
            elif isinstance(node, ast.comprehension):
                conditions.extend(ast.unparse(t) for t in node.ifs)
            elif isinstance(node, ast.Match):
                conditions.append(ast.unparse(node.subject))
        return conditions

    def test_s28_missing_origin_is_not_an_error(self):
        raw = read_fixture(self.NAME)
        events = [json.loads(l) for l in raw.splitlines() if l.strip()]
        results = [e for e in events if e.get("type") == "result"]
        self.assertEqual(len(results), 1)
        self.assertNotIn("origin", results[0])

        verdict = OA.analyze_stream(raw)
        self.assertEqual(verdict.status, EXPECTED[self.NAME]["status"])
        self.assertEqual(verdict.exit_class, EXPECTED[self.NAME]["exit_class"])
        self.assertEqual(verdict.cost_used, EXPECTED[self.NAME]["cost_used"])

    def test_s28_origin_absent_from_decision_branches(self):
        self.require_adapter()
        offenders = [
            cond for cond in self.decision_conditions(
                self.SOURCE.read_text(encoding="utf-8"))
            if "origin" in cond
        ]
        self.assertEqual(
            offenders, [],
            f"판정 분기 조건에 origin이 등장합니다(D5 위반): {offenders}",
        )

    def test_s28_origin_is_recorded_as_diagnostic_only(self):
        self.require_adapter()
        verdict = OA.analyze_stream(read_fixture("stream_multi_result_epilogue.jsonl"))
        self.assertEqual(verdict.origin, {"kind": "task-notification"})
        stripped = OA.analyze_stream(read_fixture(self.NAME))
        self.assertIsNone(stripped.origin)
        self.assertEqual(stripped.status, "done")

    def test_s28_no_replay_wording_in_source_or_readme(self):
        self.require_adapter()
        for path in (self.SOURCE, self.README):
            hits = [
                f"{path.name}:{n}"
                for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
                if "replay" in line.lower()
            ]
            self.assertEqual(
                hits, [], f'"replay" 표현이 남아 있습니다(D5): {hits}')


if __name__ == "__main__":
    unittest.main()
