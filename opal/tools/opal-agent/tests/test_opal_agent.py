"""
@header {
  "module": "test_opal_agent",
  "layer": "test",
  "domain": "opal-tools",
  "description": "opal_agent.py 단위 테스트 — 059(부트스트랩 마커 3-way 확장 + caller-supplied cold session id) RED-first TS-001~TS-009 + 067(stream-json 실행 경로) RED-first S-1/S-2/S-3(`[T067/L1-R1]`). subprocess 미사용 — ClaudeAdapter/GeminiAdapter/CursorAdapter/AntigravityAdapter.build_invocation()의 공개 조립 출력(cmd 배열)과 _mark()/_run()/_build_parser()의 관찰 가능한 예외·경고·SystemExit만 검증한다. TS-002(on/off 하위호환)·TS-006(warm resume 유지)은 RED 시점에도 PASS해야 하는 회귀 baseline(§4 표)이다.",
  "exports": [
    "TestBootstrapMarkerAssembly", "TestBootstrapBackCompatBaseline",
    "TestBootstrapCliChoices", "TestColdSessionIdAssembly",
    "TestWarmResumeBaseline", "TestSessionIdMutualExclusion",
    "TestUnsupportedProviderWarning", "TestCliSessionIdMutualExclusion",
    "TestStreamBuildInvocation", "TestStreamParseResult",
    "TestStreamUnsupportedProviderError"
  ],
  "task": "059, 067",
  "scenarios": ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-8", "S-9"]
}

# 인용 규칙
# - TEST-SCENARIO.md §3 S-1~S-9 ↔ PLAN.md §3.1.2(F-001 마커 3-way)/§3.2.2(F-002 cold session id) 설계 확정안 기준.
# - [MUST] red-first.md §2 작성자≠구현자: 이 파일은 opal-test-agent(RED)가 작성 — opal_agent.py는 절대 수정하지 않는다.
# - [MUST] red-first.md §4: 공개 인터페이스(build_invocation().cmd)·모듈 수준 관찰 지점(_mark, _run, _build_parser)만 사용. 내부 private 결합 금지.
# - [MUST] 무의존성: 이 파일은 표준 라이브러리만 import (pytest는 러너로만 사용).
# - subprocess 미사용: TS-007(상호배타)은 config.bin에 존재하지 않는 바이너리명을 강제로 지정해
#   shutil.which를 항상 실패시킴으로써, 상호배타 검증이 실제로 _run() 진입부(디스패치 이전)에 있는지
#   결정론적으로 관측한다 (ClaudeNotFoundError가 아니라 순수 OpalAgentError여야 순서가 맞음).
#
# 067(RED-first, S-1/S-2/S-3, prefix [T067/L1-R1]):
# - TEST-SCENARIO.md(067) §3 S-1~S-3 ↔ PLAN.md(067) §3.1.2 함수 시그니처 설계
#   (AgentConfig.output_format="stream-json" / ClaudeAdapter.supports_stream /
#   build_invocation stream 분기+--verbose / parse_result 마지막 result 줄 5필드 /
#   비-claude stream → OpalAgentError) 기준.
# - fixture는 ANALYSIS.md(067) §2.2/§2.4 실측 stream-json 스키마(system/init →
#   assistant → 마지막 줄 type:result, 5필드 result/session_id/is_error/
#   total_cost_usd/duration_ms)를 준거로 작성 — mock/patch 없이 실 JSONL 문자열만 사용.
# - [MUST] red-first.md §2/§3: 이 3건은 opal-test-agent(RED)가 작성하며 GREEN(Step 1)
#   구현 전까지 opal_agent.py를 수정하지 않는다. fix 루핑 중 이 3건 수정 금지(테스트 불변성).
"""

import contextlib
import io
import json
import pathlib
import sys
import unittest

# opal_agent.py를 소스에서 직접 import (재배포 산출물이 아니라 프로젝트 소스 검증)
_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
import opal_agent as OA  # noqa: E402


def _first_line(text: str) -> str:
    return text.split("\n", 1)[0]


class TestBootstrapMarkerAssembly(unittest.TestCase):
    """S-1/TS-001: claude assistant 마커 조립 — 최외곽 첫 줄 == '[ASSISTANT]'."""

    def test_ts001_claude_assistant_marker_first_line(self):
        config = OA.AgentConfig(prompt="hello world", opal_bootstrap="assistant")
        inv = OA.ClaudeAdapter().build_invocation(config, "claude")
        self.assertEqual(inv.cmd[1], "-p")
        self.assertEqual(_first_line(inv.cmd[2]), "[ASSISTANT]")
        self.assertEqual(inv.cmd[2], "[ASSISTANT]\nhello world")


class TestBootstrapBackCompatBaseline(unittest.TestCase):
    """S-2/TS-002: on/off 하위호환 — RED 시점에도 PASS해야 하는 회귀 baseline."""

    def test_ts002_default_is_on(self):
        config = OA.AgentConfig(prompt="p")
        self.assertEqual(config.opal_bootstrap, "on")

    def test_ts002_on_leaves_prompt_unchanged(self):
        config = OA.AgentConfig(prompt="hello world", opal_bootstrap="on")
        inv = OA.ClaudeAdapter().build_invocation(config, "claude")
        self.assertEqual(inv.cmd[2], "hello world")

    def test_ts002_off_prefixes_worker_marker(self):
        config = OA.AgentConfig(prompt="hello world", opal_bootstrap="off")
        inv = OA.ClaudeAdapter().build_invocation(config, "claude")
        self.assertEqual(inv.cmd[2], "[WORKER]\nhello world")


class TestBootstrapCliChoices(unittest.TestCase):
    """S-4/TS-004: CLI choices 확장 — assistant 파싱 통과 / bad 값 거부 / 기본 on."""

    def test_ts004_assistant_choice_parses(self):
        parser = OA._build_parser()
        args = parser.parse_args(["hi", "--opal-bootstrap", "assistant"])
        self.assertEqual(args.opal_bootstrap, "assistant")

    def test_ts004_default_choice_is_on(self):
        parser = OA._build_parser()
        args = parser.parse_args(["hi"])
        self.assertEqual(args.opal_bootstrap, "on")

    def test_ts004_bad_choice_rejected_by_argparse(self):
        parser = OA._build_parser()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["hi", "--opal-bootstrap", "bad"])


class TestBootstrapOutermostInvariant(unittest.TestCase):
    """S-3/TS-003: cursor·antigravity 최외곽 불변식 — system_prompt 접붙임 후에도 첫 줄 == '[ASSISTANT]'."""

    def test_ts003_cursor_outermost_marker(self):
        config = OA.AgentConfig(
            prompt="do the task", system_prompt="you are a role",
            opal_bootstrap="assistant",
        )
        inv = OA.CursorAdapter().build_invocation(config, "cursor-agent")
        self.assertEqual(_first_line(inv.cmd[2]), "[ASSISTANT]")

    def test_ts003_antigravity_outermost_marker(self):
        config = OA.AgentConfig(
            prompt="do the task", system_prompt="you are a role",
            opal_bootstrap="assistant",
        )
        inv = OA.AntigravityAdapter().build_invocation(config, "agy")
        self.assertEqual(_first_line(inv.cmd[2]), "[ASSISTANT]")


class TestColdSessionIdAssembly(unittest.TestCase):
    """S-5/TS-005: cold `--session-id` 조립 — new_session_id → cmd에 --session-id 포함, --resume 부재."""

    def test_ts005_claude_cold_session_id(self):
        config = OA.AgentConfig(prompt="p", new_session_id="sid-x")
        inv = OA.ClaudeAdapter().build_invocation(config, "claude")
        self.assertIn("--session-id", inv.cmd)
        self.assertEqual(inv.cmd[inv.cmd.index("--session-id") + 1], "sid-x")
        self.assertNotIn("--resume", inv.cmd)


class TestWarmResumeBaseline(unittest.TestCase):
    """S-6/TS-006: warm `--resume` 유지 — RED 시점에도 PASS해야 하는 회귀 baseline."""

    def test_ts006_claude_warm_resume(self):
        config = OA.AgentConfig(prompt="p", session_id="sid-y")
        inv = OA.ClaudeAdapter().build_invocation(config, "claude")
        self.assertIn("--resume", inv.cmd)
        self.assertEqual(inv.cmd[inv.cmd.index("--resume") + 1], "sid-y")
        self.assertNotIn("--session-id", inv.cmd)


class TestSessionIdMutualExclusion(unittest.TestCase):
    """S-7/TS-007: cold/warm 상호배타 — new_session_id + session_id 동시 지정 시 OpalAgentError.

    bin에 존재하지 않는 바이너리명을 강제 지정해 shutil.which를 항상 실패시킨다.
    이렇게 하면 상호배타 검증이 `_run()` 진입부(디스패치 이전)에 있을 때만
    (ClaudeNotFoundError가 아닌) 순수 OpalAgentError가 관측된다 — 검증 순서 보증.
    """

    def test_ts007_cold_warm_both_set_raises_before_dispatch(self):
        config = OA.AgentConfig(
            prompt="p",
            session_id="sid-warm",
            new_session_id="sid-cold",
            bin="___opal_agent_test_nonexistent_binary___",
        )
        with self.assertRaises(OA.OpalAgentError) as ctx:
            OA._run(config)
        self.assertNotIsInstance(ctx.exception, OA.ClaudeNotFoundError)


class TestUnsupportedProviderWarning(unittest.TestCase):
    """S-8/TS-008: 미지원 provider 경고 — capability 플래그 + build_invocation cmd 부재로 검증(subprocess 미사용)."""

    def test_ts008_claude_supports_session_assign_true(self):
        self.assertTrue(OA.ClaudeAdapter.supports_session_assign)

    def test_ts008_gemini_supports_session_assign_false(self):
        self.assertFalse(OA.GeminiAdapter.supports_session_assign)

    def test_ts008_gemini_build_invocation_ignores_new_session_id(self):
        config = OA.AgentConfig(prompt="p", new_session_id="sid-z")
        inv = OA.GeminiAdapter().build_invocation(config, "gemini")
        self.assertNotIn("--session-id", inv.cmd)


class TestCliSessionIdMutualExclusion(unittest.TestCase):
    """S-9/TS-009: CLI 상호배타 방어 — --resume/--session-id 동시 전달 시 argparse가 거부."""

    def test_ts009_session_id_flag_parses_alone(self):
        parser = OA._build_parser()
        args = parser.parse_args(["hi", "--session-id", "sid-b"])
        self.assertEqual(getattr(args, "new_session_id", None), "sid-b")

    def test_ts009_resume_and_session_id_together_rejected(self):
        parser = OA._build_parser()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["hi", "--resume", "sid-a", "--session-id", "sid-b"])


# ─── 067 RED-first: stream-json 실행 경로 (S-1/S-2/S-3, prefix [T067/L1-R1]) ───
#
# ANALYSIS.md(067) §2.2/§2.4 실측 준거 fixture — claude -p --output-format
# stream-json --verbose 실측 33줄 중 범용 최소 보장 집합(system/init(1회) →
# 0회 이상 assistant/user → result(정확히 1회, 마지막 줄))으로 좁힌 것.

_STREAM_FIXTURE_OK = "\n".join([
    json.dumps({
        "type": "system", "subtype": "init",
        "session_id": "2005e50d-abcd-4c11-9a11-000000000000",
        "tools": ["Bash", "Read"], "model": "claude-haiku",
        "cwd": "/tmp",
    }),
    json.dumps({
        "type": "assistant",
        "message": {"role": "assistant", "content": [
            {"type": "text", "text": "2"},
        ]},
    }),
    json.dumps({
        "type": "result", "subtype": "success",
        "result": "2",
        "session_id": "2005e50d-abcd-4c11-9a11-000000000000",
        "is_error": False,
        "total_cost_usd": 0.0252952,
        "duration_ms": 7947,
    }),
])

# 마지막 줄이 result가 아닌 fixture(assistant 이벤트로 종료) — 명시 에러 기대.
_STREAM_FIXTURE_NO_RESULT_TAIL = "\n".join([
    json.dumps({
        "type": "system", "subtype": "init",
        "session_id": "2005e50d-abcd-4c11-9a11-000000000000",
        "tools": [], "model": "claude-haiku", "cwd": "/tmp",
    }),
    json.dumps({
        "type": "assistant",
        "message": {"role": "assistant", "content": [
            {"type": "text", "text": "still thinking"},
        ]},
    }),
])


class TestStreamBuildInvocation(unittest.TestCase):
    """[T067/L1-R1] 스트림 조립 — S-1/TS-001(H-2): output_format="stream-json"이면
    cmd에 `--output-format stream-json`과 `--verbose`가 동시 포함되어야 한다
    (ANALYSIS.md(067) §2.5 실측 — `--verbose` 누락 시 claude CLI exit 1)."""

    def test_t067_l1_r1_stream_build_invocation_includes_output_format_and_verbose(self):
        config = OA.AgentConfig(prompt="1+1 결과만 답해", output_format="stream-json")
        inv = OA.ClaudeAdapter().build_invocation(config, "claude")
        self.assertIn("--output-format", inv.cmd)
        self.assertEqual(
            inv.cmd[inv.cmd.index("--output-format") + 1], "stream-json"
        )
        self.assertIn(
            "--verbose", inv.cmd,
            "stream-json 분기는 --verbose를 항상 자동 부착해야 한다(H-2, 미구현 상태에서 RED)",
        )


class TestStreamParseResult(unittest.TestCase):
    """[T067/L1-R1] 스트림 파싱 — S-2/TS-002(H-1): stream JSONL의 마지막
    비어있지 않은 줄(type:result)에서 5필드(result/session_id/is_error/
    total_cost_usd/duration_ms)를 정확 추출해야 한다. 마지막 줄이 result가
    아니면 명시 에러(OpalAgentError)여야 한다."""

    def test_t067_l1_r1_stream_parse_result_extracts_five_fields(self):
        config = OA.AgentConfig(prompt="p", output_format="stream-json")
        result = OA.ClaudeAdapter().parse_result(config, _STREAM_FIXTURE_OK)
        self.assertEqual(result.text, "2")
        self.assertEqual(
            result.session_id, "2005e50d-abcd-4c11-9a11-000000000000"
        )
        self.assertFalse(result.is_error)
        self.assertAlmostEqual(result.cost_usd, 0.0252952)
        self.assertEqual(result.duration_ms, 7947)

    def test_t067_l1_r1_stream_parse_result_non_result_tail_raises(self):
        config = OA.AgentConfig(prompt="p", output_format="stream-json")
        with self.assertRaises(OA.OpalAgentError):
            OA.ClaudeAdapter().parse_result(config, _STREAM_FIXTURE_NO_RESULT_TAIL)


class TestStreamUnsupportedProviderError(unittest.TestCase):
    """[T067/L1-R1] 비지원 provider — S-3/TS-004(H-3): provider=codex +
    output_format="stream-json" 조합은 (ClaudeNotFoundError가 아니라) 명시적
    OpalAgentError를 던져야 한다(침묵 폴백 금지). bin에 존재하지 않는 바이너리명을
    지정해 shutil.which를 항상 실패시킴으로써, supports_stream 검증이 디스패치
    이전 chokepoint에 있는지 결정론적으로 관측한다(TestSessionIdMutualExclusion과
    동일 관측 기법)."""

    def test_t067_l1_r1_codex_stream_json_raises_explicit_opal_agent_error(self):
        config = OA.AgentConfig(
            prompt="p",
            provider="codex",
            output_format="stream-json",
            bin="___opal_agent_test_nonexistent_binary___",
        )
        with self.assertRaises(OA.OpalAgentError) as ctx:
            OA._run(config)
        self.assertNotIsInstance(
            ctx.exception, OA.ClaudeNotFoundError,
            "supports_stream 미보유 provider 에러는 shutil.which 실패보다 "
            "먼저 검증되어야 한다(명시 에러, 미구현 상태에서 RED)",
        )


if __name__ == "__main__":
    unittest.main()
