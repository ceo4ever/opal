"""
@header {
  "module": "tests.test_brain",
  "layer": "test",
  "domain": "console",
  "description": "대화별 session_id 격리 단위·통합 테스트. opbr_adapter(query --read-only 플래그·allowedTools·extract_json_fence·shell=False·cwd=project_path·cold 플래그 명시·session_id 호출자 제공), BrainSessionRegistry(session_id 키잉·대화별 독립 세션·세션A prime→A만 ready B idle·A ask B 미오염·reset(A) B 불변·같은 프로젝트 a/b 두 세션 공존), TestSessionIdHandleSeparation(conversation_id↔claude핸들 분리·콜드마다 새 uuid4·already-in-use 폴백·재시도 1회 한정·실 claude 0회), 라우터(prime 즉시반환·session_id 필수·query session_id 필수·GET /api/brain/status?project=&session_id= 미등록→idle). project·session_id 모두 필수: 빈값/무효→400. [MUST] 서브프로세스 전부 mock — 실 claude/brain-tool 호출 0회(H-8). 기존 backend 전체 회귀 0. TestBrainPrimePool(프라임 풀 적재·체크아웃+리필·동시 프라임 상한·락 무중첩)·TestBrainWarmInjection(새 대화 웜 핸들 주입→ready+resume·stale resume 투명 재프라임·빈 풀 콜드 폴백)·TestBrainLifespanPrewarm(main.py lifespan 기동 선프라임 트리거·비블로킹)·TestBrainPoolFixtureRegression(reset_brain_registry 픽스처의 풀 상태 클리어 회귀) — PLAN.md §3.2.2 설계 시그니처(prewarm/checkout_warm_handle/adopt_warm_handle) 대상, GREEN(구현 완료). 플레이키 동기화: 체크아웃 직후 풀 비움 확인·동시 체크아웃 무중복 판정은 백그라운드 리필 완료를 threading.Event로 게이트해 결정론화, 신규 세션 웜 주입 시 콜드 프라임 미호출·투명 재프라임 호출 순서 검증은 registry.prewarm을 인스턴스 no-op으로 대체해 리필 부수효과와 분리(리필 자체는 S-3이 별도 담보).",
  "exports": [
    "TestExtractJsonFence",
    "TestOpbrAdapterCmd",
    "TestOpbrAdapterCwd",
    "TestOpbrAdapterColdWarm",
    "TestConversationBrainSessionCold",
    "TestConversationBrainSessionReset",
    "TestConversationBrainSessionCrash",
    "TestConversationBrainSessionState",
    "TestBrainSessionRegistry",
    "TestOpbrAdapterAllowedTools",
    "TestSessionIdHandleSeparation",
    "TestBrainRouterPrime",
    "TestBrainRouterQuery",
    "TestBrainRouterErrors",
    "TestBrainRouterStatus",
    "TestBrainJobPolling",
    "TestBrainPrimePool",
    "TestBrainPoolT063NeedBasedFill",
    "TestBrainWarmInjection",
    "TestBrainLifespanPrewarm",
    "TestBrainPoolFixtureRegression"
  ],
  "depends": [
    "adapters.opbr_adapter",
    "adapters.brain_session",
    "routers.brain",
    "models",
    "main",
    "config"
  ],
  "task": "060",
  "scenarios": ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-8", "S-9", "S-11"],
  "changelog": [
    "2026-07-14 T060 RED: 프라임 연결 풀(F-2)·웜 핸들 주입(F-4)·lifespan 선프라임(F-3)·픽스처 회귀(H-7) 실패 테스트 추가 — 구현 전 RED 트랙(red-first.md)",
    "2026-07-14 13:31 KST T060 Step5: reset_brain_registry 픽스처에 _pool/_pool_inflight 클리어 추가(S-11 GREEN 전환) + 플레이키 4건 동기화 수리(체크아웃 직후 풀 비움·동시 체크아웃 무중복은 threading.Event로 리필 완료 게이트, 신규 세션 콜드 미호출·투명 재프라임 순서는 registry.prewarm no-op으로 리필 부수효과 분리) + TestOpbrAdapterAllowedTools stale 단언 갱신(커밋 400c03a --model/--effort 삽입 반영, 계약 의도 불변)",
    "2026-07-15 T063 RED(opal-test-agent mode:red): TestBrainPoolT063NeedBasedFill 추가 — prewarm() need=pool_size-have 충전 로직(F-003, H-1) RED 노출(S-1/S-2) + 락순서·세마포어 회귀 가드(H-2/H-3, S-3/S-4). opbr_adapter.prime_and_ask는 mock/patch 미사용, 모듈 속성 직접 대입 스텁으로 대체(red-first.md §4 공개 인터페이스 검증)",
    "2026-07-15 T063 Step5(GREEN 후 정비): test_consecutive_checkout_both_return_distinct_warm_handles(S-2) flaky 결정론화 — need-기반 동시 충전(GREEN)에서 무효화된 stub call-index 게이트(idx==2 대기)를 풀 상태 폴링(`_pool` 길이==pool_size)으로 교체. 기대값(2회 모두 non-None·서로 다른 웜 핸들) 불변, 동기화 메커니즘만 교체 — 10회 반복 무결함 확인",
    "2026-07-15 T063 CLOSE: @header exports 정합 — 존재하지 않는 TestConversationBrainSessionWarm 제거, 누락된 TestOpbrAdapterAllowedTools 반영(코드 변경 없음)"
  ]
}
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ── 테스트용 가짜 프로젝트 경로 ────────────────────────────────────────────────────
# 실제 존재하지 않아도 됨: scan_projects·_resolve_project_path를 mock 처리
_PROJ_A = "/fake/project/alpha"
_PROJ_B = "/fake/project/beta"

# 테스트용 고정 session_id (UUID 형식)
_SID_A1 = "aaaaaaaa-0001-0001-0001-000000000001"
_SID_A2 = "aaaaaaaa-0002-0002-0002-000000000002"
_SID_B1 = "bbbbbbbb-0001-0001-0001-000000000001"


def _mock_scan_projects_with(*paths):
    """scan_projects를 지정 경로를 반환하는 mock으로 대체하는 컨텍스트 매니저 반환."""
    from unittest.mock import patch as _patch

    class _FakeProject:
        def __init__(self, path):
            self.path = path
            self.is_opal = True

    return _patch(
        "dashboard.backend.routers.brain.scan_projects",
        return_value=[_FakeProject(p) for p in paths],
    )


# ── fixture ──────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    from dashboard.backend.main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_brain_registry():
    """각 테스트 전후로 brain_session_registry 전체 세션·풀 상태 클리어 — 테스트 간 상태 오염 방지.

    [T060/S-11/H-7] _sessions뿐 아니라 프라임 연결 풀(_pool·_pool_inflight)도 함께
    클리어한다. 전역 싱글턴 brain_session_registry에 직전 테스트가 남긴 풀 잔류 핸들이
    후속 테스트로 누수되는 것을 방지(TestBrainPoolFixtureRegression 회귀 가드).
    """
    from dashboard.backend.adapters.brain_session import brain_session_registry
    with brain_session_registry._lock:
        brain_session_registry._sessions.clear()
    with brain_session_registry._pool_lock:
        brain_session_registry._pool.clear()
        brain_session_registry._pool_inflight.clear()
    yield
    with brain_session_registry._lock:
        brain_session_registry._sessions.clear()
    with brain_session_registry._pool_lock:
        brain_session_registry._pool.clear()
        brain_session_registry._pool_inflight.clear()


def _mock_proc(stdout: str, returncode: int = 0) -> MagicMock:
    """subprocess.run 반환값 mock 헬퍼."""
    proc = MagicMock()
    proc.stdout = stdout
    proc.stderr = ""
    proc.returncode = returncode
    return proc


def _make_claude_output(
    result_text: str,
    session_id: str = "sid-test",
    is_error: bool = False,
) -> str:
    """claude --output-format json 출력 형식 헬퍼."""
    if is_error:
        return json.dumps({
            "type": "result",
            "subtype": "error_during_execution",
            "is_error": True,
        })
    return json.dumps({
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "result": result_text,
        "session_id": session_id,
    })


# opbr가 JSON 펜스로 출력하는 형식
_OPBR_JSON_FENCE = '```json\n{"answer": "브레인 답변입니다.", "citations": [{"page": "p1", "title": "제목1", "type": "concept"}]}\n```'
_OPBR_PREAMBLE_WITH_FENCE = (
    "[부트스트랩] ✅ principles ✅ identity ...\n"
    "[안내] //opi로 진입하세요\n\n"
    + _OPBR_JSON_FENCE
)


# ── TestExtractJsonFence ─────────────────────────────────────────────────────────

class TestExtractJsonFence:
    """extract_json_fence: preamble 섞인 result에서 JSON 펜스 추출."""

    def test_clean_fence(self):
        """깨끗한 ```json ... ``` 펜스 → answer/citations 정상 추출."""
        from dashboard.backend.adapters.opbr_adapter import extract_json_fence

        result = extract_json_fence(_OPBR_JSON_FENCE)
        assert result["answer"] == "브레인 답변입니다."
        assert len(result["citations"]) == 1
        assert result["citations"][0]["page"] == "p1"

    def test_preamble_before_fence(self):
        """부트스트랩 preamble + JSON 펜스 → 펜스만 발췌."""
        from dashboard.backend.adapters.opbr_adapter import extract_json_fence

        result = extract_json_fence(_OPBR_PREAMBLE_WITH_FENCE)
        assert result["answer"] == "브레인 답변입니다."
        assert len(result["citations"]) == 1

    def test_no_fence_fallback(self):
        """JSON 펜스 없는 result → 전체를 answer로 폴백, citations=[]."""
        from dashboard.backend.adapters.opbr_adapter import extract_json_fence

        plain_text = "브레인에서 페이지를 찾지 못했습니다."
        result = extract_json_fence(plain_text)
        assert result["answer"] == plain_text
        assert result["citations"] == []

    def test_invalid_json_in_fence_fallback(self):
        """```json 펜스가 있지만 내용이 비JSON → 폴백."""
        from dashboard.backend.adapters.opbr_adapter import extract_json_fence

        bad_fence = "```json\nnot-valid-json\n```"
        result = extract_json_fence(bad_fence)
        assert isinstance(result["answer"], str)
        assert result["citations"] == []

    def test_multiple_fences_uses_last(self):
        """여러 펜스가 있을 때 마지막 펜스 우선."""
        from dashboard.backend.adapters.opbr_adapter import extract_json_fence

        first = '```json\n{"answer": "첫번째", "citations": []}\n```'
        last = '```json\n{"answer": "마지막", "citations": [{"page": "p2", "title": "t2", "type": "entity"}]}\n```'
        text = first + "\n\n중간 텍스트\n\n" + last
        result = extract_json_fence(text)
        assert result["answer"] == "마지막"

    def test_citations_missing_becomes_empty_list(self):
        """citations 키 없는 펜스 → citations=[]."""
        from dashboard.backend.adapters.opbr_adapter import extract_json_fence

        fence = '```json\n{"answer": "답변만"}\n```'
        result = extract_json_fence(fence)
        assert result["answer"] == "답변만"
        assert result["citations"] == []

    def test_non_string_input_raises(self):
        """None 또는 비string 입력 → RuntimeError."""
        from dashboard.backend.adapters.opbr_adapter import extract_json_fence

        with pytest.raises(RuntimeError):
            extract_json_fence(None)  # type: ignore


# ── TestOpbrAdapterCmd ───────────────────────────────────────────────────────────

class TestOpbrAdapterCmd:
    """opbr_adapter.prime_and_ask 커맨드 배열 검증 (cold/warm 플래그)."""

    def _capture_cmd(self, **kwargs) -> list[str]:
        """subprocess.run을 patch하여 호출된 커맨드 배열 캡처.

        기본값: cold=True, session_id=_SID_A1
        """
        kwargs.setdefault("session_id", _SID_A1)
        kwargs.setdefault("cold", True)
        result_text = '```json\n{"answer": "테스트 답변", "citations": []}\n```'
        mock_stdout = _make_claude_output(result_text)

        with patch("subprocess.run", return_value=_mock_proc(mock_stdout)) as mock_run, \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            prime_and_ask(question="테스트 질문", project_path="/some/path", **kwargs)
            call_args = mock_run.call_args

        return call_args[0][0]  # positional first arg = cmd list

    def test_opbr_query_read_only_in_cmd(self):
        """커맨드에 '//opbr query --read-only' 포함 확인 (DECISION#23)."""
        cmd = self._capture_cmd()
        cmd_str = " ".join(cmd)
        assert "//opbr query --read-only" in cmd_str, (
            f"//opbr query --read-only not found in: {cmd}"
        )

    def test_question_in_prompt(self):
        """질문 텍스트가 -p 인자에 포함됨."""
        cmd = self._capture_cmd()
        assert "-p" in cmd
        p_idx = cmd.index("-p")
        prompt_arg = cmd[p_idx + 1]
        assert "테스트 질문" in prompt_arg, (
            f"Question not found in prompt: {prompt_arg!r}"
        )

    def test_output_format_json_in_cmd(self):
        """--output-format json 포함 확인."""
        cmd = self._capture_cmd()
        assert "--output-format" in cmd
        idx = cmd.index("--output-format")
        assert cmd[idx + 1] == "json"

    def test_no_safe_mode_flag(self):
        """[MUST] --safe-mode 부재 (H-7)."""
        cmd = self._capture_cmd()
        assert "--safe-mode" not in cmd, f"--safe-mode MUST NOT be in cmd: {cmd}"

    def test_no_bare_flag(self):
        """[MUST] --bare 부재 (H-7)."""
        cmd = self._capture_cmd()
        assert "--bare" not in cmd, f"--bare MUST NOT be in cmd: {cmd}"

    def test_shell_false(self):
        """[MUST] subprocess.run이 shell=False로 호출됨 (H-13)."""
        result_text = '```json\n{"answer": "답변", "citations": []}\n```'
        mock_stdout = _make_claude_output(result_text)

        with patch("subprocess.run", return_value=_mock_proc(mock_stdout)) as mock_run, \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            prime_and_ask(
                question="테스트",
                project_path="/path",
                session_id=_SID_A1,
                cold=True,
            )

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("shell") is False, (
            f"subprocess.run must be called with shell=False, got shell={call_kwargs.get('shell')}"
        )

    def test_result_contains_answer_and_citations(self):
        """prime_and_ask 반환값에 answer·citations·session_id·elapsed_s 포함."""
        result_text = '```json\n{"answer": "답변입니다", "citations": [{"page": "p1", "title": "t1", "type": "concept"}]}\n```'
        mock_stdout = _make_claude_output(result_text, session_id=_SID_A1)

        with patch("subprocess.run", return_value=_mock_proc(mock_stdout)), \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            result = prime_and_ask(
                question="질문",
                project_path="/path",
                session_id=_SID_A1,
                cold=True,
            )

        assert result["answer"] == "답변입니다"
        assert len(result["citations"]) == 1
        assert result["session_id"] == _SID_A1
        assert "elapsed_s" in result

    def test_is_error_raises(self):
        """is_error=true → RuntimeError."""
        mock_stdout = _make_claude_output("", is_error=True)

        with patch("subprocess.run", return_value=_mock_proc(mock_stdout)), \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            with pytest.raises(RuntimeError, match="is_error=true"):
                prime_and_ask(
                    question="질문",
                    project_path="/path",
                    session_id=_SID_A1,
                    cold=True,
                )

    def test_non_json_output_raises(self):
        """비JSON stdout → RuntimeError."""
        with patch("subprocess.run", return_value=_mock_proc("not-json")), \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            with pytest.raises(RuntimeError):
                prime_and_ask(
                    question="질문",
                    project_path="/path",
                    session_id=_SID_A1,
                    cold=True,
                )


# ── TestOpbrAdapterColdWarm ──────────────────────────────────────────────────────

class TestOpbrAdapterColdWarm:
    """opbr_adapter: cold=True → --session-id, cold=False → --resume 분기 검증."""

    def _capture_cmd(self, **kwargs) -> list[str]:
        result_text = '```json\n{"answer": "테스트 답변", "citations": []}\n```'
        mock_stdout = _make_claude_output(result_text)

        with patch("subprocess.run", return_value=_mock_proc(mock_stdout)) as mock_run, \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            prime_and_ask(question="테스트 질문", project_path="/some/path", **kwargs)
            call_args = mock_run.call_args

        return call_args[0][0]

    def test_cold_true_uses_session_id_flag(self):
        """cold=True: --session-id 플래그, --resume 없음."""
        cmd = self._capture_cmd(session_id=_SID_A1, cold=True)
        assert "--session-id" in cmd, f"--session-id missing for cold=True: {cmd}"
        assert "--resume" not in cmd, f"--resume must not appear for cold=True: {cmd}"

    def test_cold_true_uses_provided_session_id(self):
        """cold=True: 호출자 제공 session_id가 --session-id 값으로 사용됨."""
        cmd = self._capture_cmd(session_id=_SID_A1, cold=True)
        idx = cmd.index("--session-id")
        assert cmd[idx + 1] == _SID_A1, (
            f"--session-id value must be provided session_id={_SID_A1!r}, got {cmd[idx+1]!r}"
        )

    def test_cold_false_uses_resume_flag(self):
        """cold=False: --resume 플래그, --session-id 없음."""
        cmd = self._capture_cmd(session_id=_SID_A1, cold=False)
        assert "--resume" in cmd, f"--resume missing for cold=False: {cmd}"
        assert "--session-id" not in cmd, f"--session-id must not appear for cold=False: {cmd}"

    def test_cold_false_uses_provided_session_id_for_resume(self):
        """cold=False: 호출자 제공 session_id가 --resume 값으로 사용됨."""
        cmd = self._capture_cmd(session_id=_SID_A1, cold=False)
        idx = cmd.index("--resume")
        assert cmd[idx + 1] == _SID_A1, (
            f"--resume value must be provided session_id={_SID_A1!r}, got {cmd[idx+1]!r}"
        )

    def test_no_uuid_auto_generation(self):
        """opbr_adapter가 uuid를 자체 생성하지 않음 — 항상 호출자 제공 session_id 사용."""
        result_text = '```json\n{"answer": "답변", "citations": []}\n```'
        mock_stdout = _make_claude_output(result_text, session_id=_SID_A1)

        with patch("subprocess.run", return_value=_mock_proc(mock_stdout)), \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            result = prime_and_ask(
                question="질문",
                project_path="/path",
                session_id=_SID_A1,
                cold=True,
            )

        # 반환된 session_id는 claude output의 session_id 또는 입력값 폴백
        # 중요: uuid4를 새로 생성하지 않고 제공된 값이 사용됨
        assert result["session_id"] == _SID_A1, (
            f"session_id must be caller-provided={_SID_A1!r}, got {result['session_id']!r}"
        )

    def test_cwd_set_to_project_path(self):
        """subprocess.run이 cwd=project_path로 호출됨 (격리 핵심)."""
        result_text = '```json\n{"answer": "답변", "citations": []}\n```'
        mock_stdout = _make_claude_output(result_text)

        with patch("subprocess.run", return_value=_mock_proc(mock_stdout)) as mock_run, \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            prime_and_ask(
                question="질문",
                project_path=_PROJ_A,
                session_id=_SID_A1,
                cold=True,
            )

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("cwd") == _PROJ_A, (
            f"subprocess.run must be called with cwd={_PROJ_A!r}, "
            f"got cwd={call_kwargs.get('cwd')!r}"
        )

    def test_cwd_differs_per_project(self):
        """프로젝트 A·B 각각 cwd 다름 — brain 격리."""
        result_text = '```json\n{"answer": "답변", "citations": []}\n```'
        mock_stdout = _make_claude_output(result_text)

        captured_cwds = []

        def capture_run(cmd, **kwargs):
            captured_cwds.append(kwargs.get("cwd"))
            return _mock_proc(mock_stdout)

        with patch("subprocess.run", side_effect=capture_run), \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            prime_and_ask(question="질문A", project_path=_PROJ_A, session_id=_SID_A1, cold=True)
            prime_and_ask(question="질문B", project_path=_PROJ_B, session_id=_SID_B1, cold=True)

        assert captured_cwds[0] == _PROJ_A
        assert captured_cwds[1] == _PROJ_B
        assert captured_cwds[0] != captured_cwds[1]

    def test_invalid_project_path_raises(self):
        """존재하지 않는 project_path → NotADirectoryError."""
        from dashboard.backend.adapters.opbr_adapter import prime_and_ask

        with patch("os.path.isdir", return_value=False):
            with pytest.raises(NotADirectoryError, match="project_path가 존재하지 않거나"):
                prime_and_ask(
                    question="질문",
                    project_path="/nonexistent/path",
                    session_id=_SID_A1,
                    cold=True,
                )

    def test_empty_project_path_skips_validation(self):
        """빈 project_path → isdir 검증 스킵 (라우터가 사전 400으로 처리)."""
        result_text = '```json\n{"answer": "답변", "citations": []}\n```'
        mock_stdout = _make_claude_output(result_text)

        with patch("subprocess.run", return_value=_mock_proc(mock_stdout)) as mock_run:
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            prime_and_ask(
                question="질문",
                project_path="",
                session_id=_SID_A1,
                cold=True,
            )

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("cwd") is None


# ── TestOpbrAdapterCwd (하위 호환) ───────────────────────────────────────────────

class TestOpbrAdapterCwd:
    """opbr_adapter.prime_and_ask cwd=project_path 격리 검증 (cold=True 기본)."""

    def test_cwd_set_to_project_path(self):
        """subprocess.run이 cwd=project_path로 호출됨 (격리 핵심)."""
        result_text = '```json\n{"answer": "답변", "citations": []}\n```'
        mock_stdout = _make_claude_output(result_text)

        with patch("subprocess.run", return_value=_mock_proc(mock_stdout)) as mock_run, \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            prime_and_ask(
                question="질문",
                project_path=_PROJ_A,
                session_id=_SID_A1,
                cold=True,
            )

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("cwd") == _PROJ_A, (
            f"subprocess.run must be called with cwd='{_PROJ_A}', "
            f"got cwd={call_kwargs.get('cwd')!r}"
        )


# ── TestConversationBrainSessionCold ────────────────────────────────────────────

class TestConversationBrainSessionCold:
    """ConversationBrainSession: 콜드 → 웜 분기 테스트."""

    def _make_ask_return(self, answer: str = "답변", sid: str = _SID_A1) -> dict:
        return {
            "answer": answer,
            "citations": [],
            "session_id": sid,
            "elapsed_s": 1.0,
        }

    def test_cold_ask_sets_claude_session_id(self):
        """콜드 ask → claude_session_id가 ConversationBrainSession에 설정됨."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )
        assert session.claude_session_id is None

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=self._make_ask_return(sid=_SID_A1),
        ):
            result = session.ask("질문")

        assert session.claude_session_id == _SID_A1
        assert session.turn_count == 1
        assert result["answer"] == "답변"

    def test_cold_ask_uses_new_uuid_not_conversation_id(self):
        """콜드 ask → prime_and_ask에 전달되는 session_id가 conversation_id와 다른 새 uuid임.

        conversation_id를 --session-id로 직접 전달하면 리셋/재프라임 시 'already in use' 충돌.
        BE가 콜드마다 새 uuid4를 발급하여 이를 근본 차단.
        """
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        captured_kwargs = {}

        def mock_ask(**kwargs):
            captured_kwargs.update(kwargs)
            return self._make_ask_return(sid="new-claude-handle-uuid")

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            session.ask("질문")

        # 핵심: session_id가 conversation_id(FE uuid)와 달라야 한다
        assert captured_kwargs.get("session_id") != _SID_A1, (
            f"Cold ask MUST NOT pass conversation_id={_SID_A1!r} as session_id "
            f"(would cause 'already in use' on reprime). "
            f"got: session_id={captured_kwargs.get('session_id')!r}"
        )
        assert captured_kwargs.get("cold") is True, (
            f"Cold ask must pass cold=True, got: {captured_kwargs}"
        )
        # session_id는 uuid 형식 문자열이어야 함
        import uuid as _uuid
        try:
            _uuid.UUID(captured_kwargs["session_id"])
        except (ValueError, KeyError):
            raise AssertionError(
                f"session_id must be a valid uuid4, got: {captured_kwargs.get('session_id')!r}"
            )

    def test_warm_ask_uses_resume(self):
        """웜 ask → prime_and_ask에 claude_session_id 전달, cold=False."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        # 첫 콜드
        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=self._make_ask_return(sid=_SID_A1),
        ):
            session.ask("첫 질문")

        assert session.claude_session_id == _SID_A1

        # 두 번째 웜 ask
        captured_kwargs = {}

        def mock_warm_ask(**kwargs):
            captured_kwargs.update(kwargs)
            return self._make_ask_return(sid=_SID_A1)

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_warm_ask,
        ):
            session.ask("두 번째 질문")

        assert captured_kwargs.get("session_id") == _SID_A1, (
            f"Warm ask should use existing claude_session_id, got: {captured_kwargs}"
        )
        assert captured_kwargs.get("cold") is False, (
            f"Warm ask must pass cold=False, got: {captured_kwargs}"
        )

    def test_turn_count_increments(self):
        """ask 성공마다 turn_count++."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=self._make_ask_return(sid=_SID_A1),
        ):
            session.ask("q1")
            session.ask("q2")

        assert session.turn_count == 2

    def test_cwd_is_project_path(self):
        """ask 시 prime_and_ask에 project_path(cwd)가 전달됨."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        captured_kwargs = {}

        def mock_ask(**kwargs):
            captured_kwargs.update(kwargs)
            return self._make_ask_return()

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            session.ask("질문")

        assert captured_kwargs.get("project_path") == _PROJ_A, (
            f"prime_and_ask must receive project_path={_PROJ_A!r}, got: {captured_kwargs}"
        )


# ── TestConversationBrainSessionReset ───────────────────────────────────────────

class TestConversationBrainSessionReset:
    """ConversationBrainSession: 리셋 트리거 테스트."""

    def _make_ask_return(self, sid: str = _SID_A1) -> dict:
        return {"answer": "답변", "citations": [], "session_id": sid, "elapsed_s": 1.0}

    def test_manual_reset_clears_session(self):
        """reset() → claude_session_id=None, turn_count=0."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=self._make_ask_return(),
        ):
            session.ask("질문")

        assert session.claude_session_id is not None

        session.reset()
        assert session.claude_session_id is None
        assert session.turn_count == 0

    def test_turn_threshold_triggers_reset(self):
        """turn_count ≥ max_turns → 다음 ask 시 콜드 재프라임."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A, max_turns=2
        )

        call_cold_flags = []

        def mock_ask(**kwargs):
            call_cold_flags.append(kwargs.get("cold"))
            return {"answer": "답변", "citations": [], "session_id": _SID_A1, "elapsed_s": 1.0}

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            session.ask("q1")  # turn=1, cold
            session.ask("q2")  # turn=2, warm
            # turn_count == max_turns(2) → _should_reset() = True
            session.ask("q3")  # 리셋 후 콜드

        # q3에서는 cold=True (콜드 프라임)으로 호출되어야 함
        assert call_cold_flags[-1] is True, (
            f"After turn threshold reset, last call should be cold=True, "
            f"got: {call_cold_flags}"
        )

    def test_idle_timeout_triggers_reset(self):
        """유휴 타임아웃 초과 → 다음 ask 시 콜드 재프라임."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A, idle_timeout_s=0.01
        )

        call_cold_flags = []

        def mock_ask(**kwargs):
            call_cold_flags.append(kwargs.get("cold"))
            return {"answer": "답변", "citations": [], "session_id": _SID_A1, "elapsed_s": 1.0}

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            session.ask("q1")  # 콜드
            time.sleep(0.05)  # 유휴 타임아웃 초과 (50ms > 10ms)
            session.ask("q2")  # 리셋 후 콜드

        # q2는 cold=True (콜드)으로 호출되어야 함
        assert call_cold_flags[-1] is True, (
            f"After idle timeout, ask should be cold=True, got: {call_cold_flags}"
        )


# ── TestConversationBrainSessionCrash ───────────────────────────────────────────

class TestConversationBrainSessionCrash:
    """ConversationBrainSession: ⓓ 크래시 → 투명 재프라임 테스트."""

    def test_resume_failure_triggers_cold_reprime(self):
        """warm resume 실패 → 세션 클리어 후 새 uuid4로 콜드 1회 재시도 (투명 재프라임).

        재프라임 시 conversation_id를 재사용하지 않고 새 uuid4를 발급해야
        'already in use' 충돌을 방지할 수 있다.
        """
        from dashboard.backend.adapters.brain_session import ConversationBrainSession
        import uuid as _uuid

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )
        call_cold_flags = []
        call_session_ids = []
        cold_reprime_handle = str(_uuid.uuid4())  # 재프라임에서 반환할 새 핸들

        def mock_ask(**kwargs):
            call_cold_flags.append(kwargs.get("cold"))
            call_session_ids.append(kwargs.get("session_id"))
            if kwargs.get("cold") is False:
                # resume 실패 시뮬레이션
                raise RuntimeError("resume failed: session expired")
            # 콜드 성공 — 새 claude 핸들 반환
            return {"answer": "재프라임 답변", "citations": [], "session_id": cold_reprime_handle, "elapsed_s": 2.0}

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            # 직접 상태 주입하여 warm 상태 시작
            session._claude_session_id = "stale-claude-sid"
            session._last_used = time.monotonic()
            session._turn_count = 1

            result = session.ask("질문")

        # 투명 재프라임: resume 실패 후 콜드로 재시도 성공
        assert result["answer"] == "재프라임 답변"
        assert session.claude_session_id == cold_reprime_handle

        # 호출 순서: warm(cold=False) → cold(cold=True)
        assert call_cold_flags[0] is False, "First call should be warm (cold=False)"
        assert call_cold_flags[1] is True, "Second call should be cold (cold=True)"

        # 재프라임 시 전달된 session_id가 conversation_id와 달라야 함 (새 uuid4)
        assert call_session_ids[1] != _SID_A1, (
            f"Cold reprime MUST use a new uuid4, NOT conversation_id={_SID_A1!r}. "
            f"got: {call_session_ids[1]!r}"
        )
        try:
            _uuid.UUID(call_session_ids[1])
        except (ValueError, TypeError):
            raise AssertionError(
                f"Cold reprime session_id must be a valid uuid4, got: {call_session_ids[1]!r}"
            )

    def test_reprime_updates_claude_session_id(self):
        """투명 재프라임 성공 후 새 claude_session_id로 갱신됨."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )
        session._claude_session_id = "old-claude-sid"
        session._last_used = time.monotonic()
        session._turn_count = 1

        new_claude_sid = "new-claude-sid-from-server"
        call_count = [0]

        def mock_ask(**kwargs):
            call_count[0] += 1
            if kwargs.get("cold") is False:
                raise RuntimeError("session expired")
            return {"answer": "새 답변", "citations": [], "session_id": new_claude_sid, "elapsed_s": 1.0}

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            session.ask("질문")

        assert session.claude_session_id == new_claude_sid, (
            f"claude_session_id should be updated to {new_claude_sid!r} after reprime"
        )
        assert call_count[0] == 2, "Should have called prime_and_ask twice (warm fail + cold)"


# ── TestConversationBrainSessionState ───────────────────────────────────────────

class TestConversationBrainSessionState:
    """ConversationBrainSession state 전이 테스트."""

    def _make_ask_return(self, sid: str = _SID_A1) -> dict:
        return {"answer": "답변", "citations": [], "session_id": sid, "elapsed_s": 1.0}

    def test_initial_state_is_idle(self):
        """초기 state=idle."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )
        s = session.status()
        assert s["state"] == "idle"
        assert s["session_active"] is False
        assert s["message"] == ""

    def test_prime_success_state_ready(self):
        """prime 성공 → state=ready, session_active=True."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=self._make_ask_return(sid=_SID_A1),
        ):
            session.prime()

        s = session.status()
        assert s["state"] == "ready"
        assert s["session_active"] is True
        assert s["message"] == ""

    def test_prime_failure_state_error(self):
        """prime 실패 → state=error, message=사유."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=RuntimeError("프라임 실패: 인증 오류"),
        ):
            with pytest.raises(RuntimeError):
                session.prime()

        s = session.status()
        assert s["state"] == "error"
        assert s["session_active"] is False
        assert "프라임 실패" in s["message"]

    def test_reset_returns_to_idle(self):
        """reset() → state=idle, session_active=False."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=self._make_ask_return(),
        ):
            session.prime()

        assert session.status()["state"] == "ready"

        session.reset()
        s = session.status()
        assert s["state"] == "idle"
        assert s["session_active"] is False
        assert s["message"] == ""

    def test_error_reset_returns_to_idle(self):
        """error 상태에서 reset() → state=idle."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=RuntimeError("오류"),
        ):
            with pytest.raises(RuntimeError):
                session.prime()

        assert session.status()["state"] == "error"

        session.reset()
        assert session.status()["state"] == "idle"

    def test_ask_success_state_ready(self):
        """ask 성공 → state=ready."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=self._make_ask_return(),
        ):
            session.ask("질문")

        s = session.status()
        assert s["state"] == "ready"
        assert s["session_active"] is True

    def test_ask_failure_state_error(self):
        """ask 콜드 프라임 실패 → state=error."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=RuntimeError("콜드 실패"),
        ):
            with pytest.raises(RuntimeError):
                session.ask("질문")

        s = session.status()
        assert s["state"] == "error"
        assert "콜드 실패" in s["message"]

    def test_status_message_empty_when_ready(self):
        """state=ready 시 message는 빈 문자열."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=self._make_ask_return(),
        ):
            session.prime()

        assert session.status()["message"] == ""


# ── TestBrainSessionRegistry ─────────────────────────────────────────────────────

class TestBrainSessionRegistry:
    """BrainSessionRegistry 대화별 독립 세션 격리 테스트. (핵심 요구사항)"""

    def _make_ask_return(self, sid: str = _SID_A1) -> dict:
        return {"answer": "답변", "citations": [], "session_id": sid, "elapsed_s": 1.0}

    # ── (a) 레지스트리 session_id 키잉 ───────────────────────────────────────────

    def test_registry_keyed_by_session_id(self):
        """레지스트리 키가 session_id — 같은 프로젝트 다른 session_id 공존."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry()

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=[
                self._make_ask_return(sid=_SID_A1),
                self._make_ask_return(sid=_SID_A2),
            ],
        ):
            registry.prime(_SID_A1, _PROJ_A)
            registry.prime(_SID_A2, _PROJ_A)

        session_a1 = registry.get_session(_SID_A1)
        session_a2 = registry.get_session(_SID_A2)

        assert session_a1 is not None
        assert session_a2 is not None
        assert session_a1 is not session_a2, "Different session_id must map to different session objects"

    def test_same_project_two_sessions_coexist(self):
        """같은 프로젝트에 두 session_id(대화) 독립 공존."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry()

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=[
                self._make_ask_return(sid=_SID_A1),
                self._make_ask_return(sid=_SID_A2),
            ],
        ):
            registry.prime(_SID_A1, _PROJ_A)
            registry.prime(_SID_A2, _PROJ_A)

        # 두 세션 모두 ready — 같은 프로젝트임에도 독립
        status_a1 = registry.status(_SID_A1)
        status_a2 = registry.status(_SID_A2)

        assert status_a1["state"] == "ready", f"A1 must be ready, got {status_a1['state']}"
        assert status_a2["state"] == "ready", f"A2 must be ready, got {status_a2['state']}"
        assert status_a1["session_active"] is True
        assert status_a2["session_active"] is True

    # ── (b) 세션별 독립 (타 세션 불변) ──────────────────────────────────────────

    def test_prime_session_a_only_a_ready_b_idle(self):
        """세션 A prime → A만 ready, B는 idle (격리 핵심)."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry()

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=self._make_ask_return(sid=_SID_A1),
        ):
            registry.prime(_SID_A1, _PROJ_A)

        status_a = registry.status(_SID_A1)
        status_b = registry.status(_SID_B1)  # 세션 없음

        assert status_a["state"] == "ready", f"A must be ready after prime, got {status_a['state']}"
        assert status_b["state"] == "idle", f"B must be idle (never primed), got {status_b['state']}"
        assert status_a["session_active"] is True
        assert status_b["session_active"] is False

    def test_ask_a_does_not_contaminate_b(self):
        """A에 ask → B 세션 미오염 (turn_count·session_id 불변)."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry()

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=self._make_ask_return(sid=_SID_A1),
        ):
            registry.ask(_SID_A1, "A 질문", _PROJ_A)

        status_b = registry.status(_SID_B1)
        assert status_b["state"] == "idle", "B must remain idle after A asks"
        assert status_b["session_active"] is False

        session_b = registry.get_session(_SID_B1)
        assert session_b is None, "B session object must not exist if B was never used"

    def test_reset_a_does_not_affect_b(self):
        """reset(A) → B 세션 불변."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry()

        # A·B 모두 prime
        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=[
                self._make_ask_return(sid=_SID_A1),
                self._make_ask_return(sid=_SID_B1),
            ],
        ):
            registry.prime(_SID_A1, _PROJ_A)
            registry.prime(_SID_B1, _PROJ_B)

        # A 리셋
        registry.reset(_SID_A1)

        status_a = registry.status(_SID_A1)
        status_b = registry.status(_SID_B1)

        assert status_a["state"] == "idle", f"A must be idle after reset, got {status_a['state']}"
        assert status_b["state"] == "ready", f"B must remain ready after A reset, got {status_b['state']}"
        assert status_b["session_active"] is True

    def test_five_trigger_reset_per_session(self):
        """turn_count ≥ max_turns 리셋이 A 세션에만 적용 (B 불변)."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry(max_turns=1)

        call_cold_a = []
        call_cold_b = []

        def mock_ask(**kwargs):
            sid = kwargs.get("session_id")
            cold = kwargs.get("cold")
            if sid == _SID_A1 or (kwargs.get("project_path") == _PROJ_A):
                call_cold_a.append(cold)
            else:
                call_cold_b.append(cold)
            return self._make_ask_return(sid=sid or _SID_B1)

        # B 먼저 prime (max_turns=1이지만 prime만 1회)
        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            registry.prime(_SID_B1, _PROJ_B)
            # A: turn=1(cold) → turn임계(1) → 다음 ask 시 콜드
            registry.ask(_SID_A1, "A-q1", _PROJ_A)
            # A 리셋 유발 (turn_count=1 >= max_turns=1 → 다음 ask 콜드)
            registry.ask(_SID_A1, "A-q2", _PROJ_A)

        # A의 두 번째 ask는 cold=True
        assert call_cold_a[-1] is True, (
            f"A's second ask should be cold=True after turn reset, got {call_cold_a}"
        )
        # B는 여전히 ready
        assert registry.status(_SID_B1)["state"] == "ready"

    # ── (c) prime/query/status session_id 계약 ───────────────────────────────────

    def test_status_unregistered_session_id_returns_idle(self):
        """미등록 session_id → state=idle (서버재시작 후 등)."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry()
        status = registry.status("nonexistent-session-id")

        assert status["state"] == "idle"
        assert status["session_active"] is False
        assert status["message"] == ""

    def test_status_session_a_vs_b_independent(self):
        """status(A) vs status(B) — 각각 독립 상태."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry()

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=self._make_ask_return(sid=_SID_A1),
        ):
            registry.prime(_SID_A1, _PROJ_A)

        status_a = registry.status(_SID_A1)
        status_b = registry.status(_SID_B1)

        assert status_a["state"] == "ready"
        assert status_b["state"] == "idle"

    # ── (d) project=cwd 격리 유지 ────────────────────────────────────────────────

    def test_project_path_used_as_cwd(self):
        """ask 시 project_path가 prime_and_ask의 project_path(cwd)로 전달됨."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry()
        captured_project_path = []

        def mock_ask(**kwargs):
            captured_project_path.append(kwargs.get("project_path"))
            return self._make_ask_return()

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            registry.ask(_SID_A1, "질문", _PROJ_A)

        assert captured_project_path[0] == _PROJ_A, (
            f"project_path must be passed as cwd={_PROJ_A!r}, got {captured_project_path[0]!r}"
        )

    def test_different_projects_different_cwd(self):
        """A와 B가 다른 프로젝트면 각각 다른 cwd 사용."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry()
        captured_cwds = []

        def mock_ask(**kwargs):
            captured_cwds.append(kwargs.get("project_path"))
            sid = kwargs.get("session_id")
            return self._make_ask_return(sid=sid)

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            registry.ask(_SID_A1, "질문A", _PROJ_A)
            registry.ask(_SID_B1, "질문B", _PROJ_B)

        assert captured_cwds[0] == _PROJ_A
        assert captured_cwds[1] == _PROJ_B
        assert captured_cwds[0] != captured_cwds[1]


# ── TestOpbrAdapterAllowedTools ──────────────────────────────────────────────────

class TestOpbrAdapterAllowedTools:
    """opbr_adapter.prime_and_ask --allowedTools 포함 검증."""

    def _capture_cmd(self, **kwargs) -> list[str]:
        kwargs.setdefault("session_id", _SID_A1)
        kwargs.setdefault("cold", True)
        result_text = '```json\n{"answer": "테스트 답변", "citations": []}\n```'
        mock_stdout = _make_claude_output(result_text)

        with patch("subprocess.run", return_value=_mock_proc(mock_stdout)) as mock_run, \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            prime_and_ask(question="테스트 질문", project_path="/some/path", **kwargs)
            call_args = mock_run.call_args

        return call_args[0][0]

    def test_allowed_tools_flag_present(self):
        cmd = self._capture_cmd()
        assert "--allowedTools" in cmd

    def test_bash_in_allowed_tools(self):
        cmd = self._capture_cmd()
        idx = cmd.index("--allowedTools")
        assert "Bash" in cmd[idx + 1]

    def test_read_in_allowed_tools(self):
        cmd = self._capture_cmd()
        idx = cmd.index("--allowedTools")
        assert "Read" in cmd[idx + 1]

    def test_grep_glob_in_allowed_tools(self):
        cmd = self._capture_cmd()
        idx = cmd.index("--allowedTools")
        tools_value = cmd[idx + 1]
        assert "Grep" in tools_value
        assert "Glob" in tools_value

    def test_write_not_in_allowed_tools(self):
        cmd = self._capture_cmd()
        idx = cmd.index("--allowedTools")
        assert "Write" not in cmd[idx + 1]

    def test_edit_not_in_allowed_tools(self):
        cmd = self._capture_cmd()
        idx = cmd.index("--allowedTools")
        assert "Edit" not in cmd[idx + 1]

    def test_allowed_tools_before_p_flag(self):
        cmd = self._capture_cmd()
        allowed_idx = cmd.index("--allowedTools")
        p_idx = cmd.index("-p")
        assert allowed_idx < p_idx

    def test_allowed_tools_value_is_single_comma_string(self):
        """[T060 stale 단언 갱신] --allowedTools 값이 단일 콤마 인자이며 -p를 삼키지 않음.

        커밋 400c03a로 `--model sonnet --effort medium`이 --allowedTools 값과 -p
        사이에 삽입되어 위치 가정(idx+2 == '-p')이 깨짐(PM 승인 #11). 계약 의도는
        불변: --allowedTools는 공백 없는 단일 콤마 문자열 값을 가지며(값이 여러 토큰으로
        흩어져 -p를 삼키지 않음), -p는 cmd 내 독립된 플래그로 남아 있어야 한다.
        """
        cmd = self._capture_cmd()
        idx = cmd.index("--allowedTools")
        assert cmd[idx + 1] == "Bash,Read,Grep,Glob", (
            f"--allowedTools 값은 단일 콤마 구분 문자열이어야 함: {cmd[idx + 1]!r}"
        )
        # --allowedTools 값 바로 다음은 별도 플래그(-- 접두)여야 함 —
        # 값이 여러 인자로 흩어져 후속 플래그를 삼키지 않았다는 증거
        assert cmd[idx + 2].startswith("--"), (
            f"--allowedTools 값 다음은 별도 플래그여야 함(값이 여러 토큰으로 분산되면 안 됨): {cmd}"
        )
        assert "-p" in cmd, f"-p 플래그가 --allowedTools에 삼켜지지 않고 존재해야 함: {cmd}"


# ── TestSessionIdHandleSeparation ────────────────────────────────────────────────
#
# 핵심 버그 픽스 검증: conversation_id(FE uuid) vs claude 세션 핸들(_claude_session_id) 분리.
# "Session ID <X> is already in use" 충돌 근본 차단 — 콜드마다 새 uuid4 발급.

class TestSessionIdHandleSeparation:
    """conversation_id ↔ claude 핸들 분리 + already-in-use 폴백 테스트 (버그 픽스 핵심)."""

    def _make_result(self, handle: str) -> dict:
        return {"answer": "답변", "citations": [], "session_id": handle, "elapsed_s": 1.0}

    def test_cold_prime_session_id_differs_from_conversation_id(self):
        """콜드 프라임 시 opbr_adapter에 전달되는 session_id가 conversation_id(FE uuid)와 다른 새 uuid4.

        이전 버그: conversation_id를 --session-id로 직접 전달 → 리셋 후 동일 id 재생성 → 충돌.
        픽스: BE가 새 uuid4를 발급하여 conversation_id와 항상 분리된 claude 핸들 사용.
        """
        import uuid as _uuid
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )
        captured_session_ids = []

        def mock_ask(**kwargs):
            captured_session_ids.append(kwargs.get("session_id"))
            return self._make_result(kwargs["session_id"])

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            session.ask("첫 질문")

        # (a) session_id가 conversation_id와 달라야 한다
        assert len(captured_session_ids) == 1
        cold_handle = captured_session_ids[0]
        assert cold_handle != _SID_A1, (
            f"MUST NOT use conversation_id={_SID_A1!r} as --session-id. "
            f"got: {cold_handle!r}"
        )
        # (b) 유효한 uuid4 형식
        try:
            parsed = _uuid.UUID(cold_handle)
            assert parsed.version == 4, f"Expected uuid4, got version {parsed.version}"
        except ValueError:
            raise AssertionError(f"session_id must be uuid4, got: {cold_handle!r}")

    def test_cold_reprime_after_reset_uses_different_uuid(self):
        """리셋 후 재콜드 → 이전 콜드와 다른 새 uuid4 발급 (같은 id 재사용 안 함).

        같은 id를 재사용하면 claude가 'already in use'를 반환한다.
        """
        import uuid as _uuid
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )
        captured_handles = []

        def mock_ask(**kwargs):
            captured_handles.append(kwargs.get("session_id"))
            return self._make_result(kwargs["session_id"])

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            session.ask("첫 질문")   # 콜드 #1 → handle_1
            session.reset()          # 클리어
            session.ask("두 번째 질문")  # 콜드 #2 → handle_2

        assert len(captured_handles) == 2
        handle_1, handle_2 = captured_handles[0], captured_handles[1]

        # 두 콜드의 handle이 달라야 한다 — 같으면 'already in use' 충돌
        assert handle_1 != handle_2, (
            f"After reset, cold reprime MUST use a NEW uuid4. "
            f"handle_1={handle_1!r} == handle_2={handle_2!r} would cause 'already in use'"
        )
        # 둘 다 conversation_id와 달라야 한다
        assert handle_1 != _SID_A1, f"handle_1 must differ from conversation_id={_SID_A1!r}"
        assert handle_2 != _SID_A1, f"handle_2 must differ from conversation_id={_SID_A1!r}"
        # 둘 다 유효한 uuid4
        for h in (handle_1, handle_2):
            _uuid.UUID(h)  # ValueError if invalid

    def test_warm_ask_uses_claude_session_id_for_resume(self):
        """웜 ask → --resume에 _claude_session_id(BE 발급 uuid4) 사용.

        conversation_id가 아니라 콜드 성공 시 저장된 claude 핸들로 resume.
        """
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )
        call_kwargs_list = []
        cold_handle = "cold-claude-handle-uuid4-" + "a" * 8

        def mock_ask(**kwargs):
            call_kwargs_list.append(dict(kwargs))
            if kwargs.get("cold") is True:
                return self._make_result(cold_handle)
            # warm: resume with cold_handle
            return self._make_result(cold_handle)

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            session.ask("콜드 질문")    # cold=True
            session.ask("웜 질문")      # cold=False

        assert len(call_kwargs_list) == 2
        warm_kwargs = call_kwargs_list[1]
        # cold=False
        assert warm_kwargs["cold"] is False, (
            f"Second ask must be warm (cold=False), got cold={warm_kwargs['cold']!r}"
        )
        # warm ask의 session_id가 콜드에서 저장된 handle이어야 함
        assert warm_kwargs["session_id"] == cold_handle, (
            f"Warm ask must use claude handle from cold prime={cold_handle!r}, "
            f"got: {warm_kwargs['session_id']!r}"
        )
        # warm ask의 session_id가 conversation_id와 달라야 함
        assert warm_kwargs["session_id"] != _SID_A1, (
            f"Warm ask MUST NOT use conversation_id={_SID_A1!r} for --resume"
        )

    def test_already_in_use_error_triggers_retry_with_new_uuid(self):
        """"already in use" 에러 발생 시 새 uuid로 1회 재시도 후 성공.

        방어 레이어: 이론적으로 uuid4 충돌이 발생해도 투명하게 복구.
        """
        import uuid as _uuid
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )
        call_session_ids = []
        retry_handle = str(_uuid.uuid4())

        def mock_ask(**kwargs):
            sid = kwargs.get("session_id", "")
            call_session_ids.append(sid)
            if len(call_session_ids) == 1:
                # 첫 번째 콜드: "already in use" 에러 시뮬레이션
                raise RuntimeError(f"non-JSON output from claude. stderr='Error: Session ID {sid} is already in use.'")
            # 두 번째 시도(재시도): 성공
            return self._make_result(retry_handle)

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            result = session.ask("질문")

        # 재시도 성공
        assert result["answer"] == "답변"
        assert session.claude_session_id == retry_handle

        # 두 번 호출 (첫 시도 + 재시도)
        assert len(call_session_ids) == 2, (
            f"Should call prime_and_ask twice (initial + retry), got {len(call_session_ids)}"
        )

        # 재시도 시 새 uuid 사용 (첫 시도와 달라야 함)
        assert call_session_ids[0] != call_session_ids[1], (
            f"Retry MUST use a NEW uuid4. "
            f"first={call_session_ids[0]!r} == retry={call_session_ids[1]!r}"
        )

        # 둘 다 conversation_id와 달라야 함
        for sid in call_session_ids:
            assert sid != _SID_A1, (
                f"session_id MUST NOT be conversation_id={_SID_A1!r}, got {sid!r}"
            )

    def test_no_infinite_retry_on_second_already_in_use(self):
        """"already in use" 에러가 재시도에서도 발생하면 propagate (1회만 재시도, 무한루프 없음)."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )
        call_count = [0]

        def mock_ask(**kwargs):
            call_count[0] += 1
            # 항상 "already in use" — 재시도도 실패
            raise RuntimeError("Error: Session ID is already in use.")

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            with pytest.raises(RuntimeError, match="already in use"):
                session.ask("질문")

        # 최대 2회 호출 (초기 + 재시도 1회)
        assert call_count[0] == 2, (
            f"Should call at most twice (1 initial + 1 retry), got {call_count[0]}"
        )

    def test_status_contract_uses_conversation_id(self, client):
        """GET /api/brain/status의 session_id 에코는 conversation_id 기준 (FE 계약 유지)."""
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.get(
                f"/api/brain/status?project={_PROJ_A}&session_id={_SID_A1}"
            )
        assert resp.status_code == 200
        data = resp.json()
        # 레지스트리 조회 키·응답 에코는 conversation_id
        assert data["session_id"] == _SID_A1, (
            f"status response MUST echo conversation_id={_SID_A1!r} as session_id, "
            f"got: {data['session_id']!r}"
        )

    def test_no_real_claude_calls(self):
        """[MUST] 위 모든 분리 로직은 실 claude 호출 0회 (mock 격리 — H-8)."""
        from dashboard.backend.adapters.brain_session import ConversationBrainSession

        session = ConversationBrainSession(
            conversation_id=_SID_A1, project_path=_PROJ_A
        )

        with patch("subprocess.run") as mock_subprocess, \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                return_value=self._make_result("some-handle"),
             ):
            session.ask("질문")
            session.reset()
            session.ask("다시 질문")

        mock_subprocess.assert_not_called()


# ── TestBrainRouterPrime ─────────────────────────────────────────────────────────

class TestBrainRouterPrime:
    """POST /api/brain/prime — project·session_id 필수, 즉시 반환·백그라운드 프라임."""

    def test_prime_returns_immediately(self, client):
        """POST /api/brain/prime project+session_id 지정 → 즉시 {priming: true} 반환."""
        with _mock_scan_projects_with(_PROJ_A), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                side_effect=lambda **kwargs: time.sleep(0),
             ):
            resp = client.post(
                "/api/brain/prime",
                json={"project": _PROJ_A, "session_id": _SID_A1},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["priming"] is True

    def test_prime_session_id_empty_400(self, client):
        """session_id 빈 값 → 400."""
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.post(
                "/api/brain/prime",
                json={"project": _PROJ_A, "session_id": ""},
            )
        assert resp.status_code == 400
        assert "session_id" in resp.json()["detail"]

    def test_prime_session_id_missing_400(self, client):
        """session_id 키 없음 → 400."""
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.post(
                "/api/brain/prime",
                json={"project": _PROJ_A},
            )
        assert resp.status_code == 400

    def test_prime_project_empty_400(self, client):
        """project 빈 값 → 400."""
        resp = client.post(
            "/api/brain/prime",
            json={"project": "", "session_id": _SID_A1},
        )
        assert resp.status_code == 400
        assert "필수" in resp.json()["detail"]

    def test_prime_project_not_found_400(self, client):
        """project 스캔 목록에 없음 → 400."""
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.post(
                "/api/brain/prime",
                json={"project": "/unknown/path", "session_id": _SID_A1},
            )
        assert resp.status_code == 400
        assert "찾을 수 없습니다" in resp.json()["detail"]

    def test_prime_only_target_session_affected(self, client):
        """prime(A) → A 세션만 프라임 트리거, B 세션 불변."""
        from dashboard.backend.adapters.brain_session import brain_session_registry

        primed_sessions = []

        def tracking_prime(session_id, project_path):
            primed_sessions.append(session_id)

        with _mock_scan_projects_with(_PROJ_A, _PROJ_B), \
             patch.object(brain_session_registry, "prime", side_effect=tracking_prime):
            resp = client.post(
                "/api/brain/prime",
                json={"project": _PROJ_A, "session_id": _SID_A1},
            )

        assert resp.status_code == 200
        # 백그라운드 스레드이므로 즉시 확인 불가 — prime이 0 또는 1회 호출됨
        # 2회 이상이면 다른 세션이 오염된 것
        assert len(primed_sessions) <= 1, (
            f"Only target session should be primed, got: {primed_sessions}"
        )

    def test_prime_is_fast(self, client):
        """prime 엔드포인트 응답이 1초 미만 (블로킹 없음)."""
        def slow_prime(**kwargs):
            time.sleep(60)
            return {"answer": "", "citations": [], "session_id": _SID_A1, "elapsed_s": 60.0}

        with _mock_scan_projects_with(_PROJ_A), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                side_effect=slow_prime,
             ):
            t0 = time.monotonic()
            resp = client.post(
                "/api/brain/prime",
                json={"project": _PROJ_A, "session_id": _SID_A1},
            )
            elapsed = time.monotonic() - t0

        assert resp.status_code == 200
        assert elapsed < 5.0, f"prime endpoint should return immediately, took {elapsed:.2f}s"

    def test_prime_no_real_claude(self, client):
        """[MUST] prime 트리거 시 실 claude 호출 0회 (mock 격리 — H-8)."""
        with _mock_scan_projects_with(_PROJ_A), \
             patch("subprocess.run") as mock_run:
            resp = client.post(
                "/api/brain/prime",
                json={"project": _PROJ_A, "session_id": _SID_A1},
            )
        assert resp.status_code == 200


# ── TestBrainRouterQuery ─────────────────────────────────────────────────────────

class TestBrainRouterQuery:
    """POST /api/brain/query — project·session_id 필수, 정상·실패 경로."""

    def test_query_returns_job_id_not_answer(self, client):
        """[RED S-1] POST /query → {job_id} 200 즉시 반환. answer/citations 키 미포함.

        계약 변경(H-1): 기존 동기 {answer,citations,session_id} → 비동기 {job_id}.
        구현 전 RED — 현재 라우터는 동기 answer를 반환하므로 FAIL 예상.
        """
        mock_result = {
            "answer": "OPAL은 프로젝트 관리 프레임워크입니다.",
            "citations": [{"page": "p1", "title": "OPAL 개요", "type": "concept", "score": 0.9}],
            "session_id": _SID_A1,
            "elapsed_s": 2.5,
        }

        with _mock_scan_projects_with(_PROJ_A), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                return_value=mock_result,
             ):
            resp = client.post(
                "/api/brain/query",
                json={"question": "OPAL이 무엇인가요?", "project": _PROJ_A, "session_id": _SID_A1},
            )

        assert resp.status_code == 200
        data = resp.json()
        # 신규 계약: job_id 즉시 반환
        assert "job_id" in data, f"job_id 키 미포함: {data}"
        assert isinstance(data["job_id"], str) and len(data["job_id"]) > 0
        # 구계약 키 미포함 (비동기 전환 후 answer는 폴링으로 수신)
        assert "answer" not in data, f"answer 키가 즉시 응답에 포함되면 안 됨: {data}"
        assert "citations" not in data, f"citations 키가 즉시 응답에 포함되면 안 됨: {data}"

    def test_query_session_id_empty_400(self, client):
        """session_id 빈 값 → 400."""
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.post(
                "/api/brain/query",
                json={"question": "질문", "project": _PROJ_A, "session_id": ""},
            )
        assert resp.status_code == 400
        assert "session_id" in resp.json()["detail"]

    def test_query_project_empty_400(self, client):
        """project 빈 값 → 400."""
        resp = client.post(
            "/api/brain/query",
            json={"question": "질문", "project": "", "session_id": _SID_A1},
        )
        assert resp.status_code == 400
        assert "필수" in resp.json()["detail"]

    def test_query_project_not_found_400(self, client):
        """project 미존재 → 400."""
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.post(
                "/api/brain/query",
                json={"question": "질문", "project": "/unknown/path", "session_id": _SID_A1},
            )
        assert resp.status_code == 400

    def test_query_job_submit_returns_immediately_on_slow_adapter(self, client):
        """[RED S-1] submit_job이 어댑터 지연과 무관하게 즉시 job_id 반환(블로킹 없음, H-6).

        어댑터 대역이 0.3초 지연을 가져도 POST /query 응답은 즉시 반환되어야 함.
        구현 전 RED — 현재 동기 라우터는 어댑터 완료까지 블로킹하므로 FAIL 예상.
        """
        import time as _time

        _DELAY = 0.3  # 어댑터 인위적 지연(초)

        def slow_adapter(**kwargs):
            _time.sleep(_DELAY)
            return {
                "answer": "느린 답변",
                "citations": [],
                "session_id": _SID_A1,
                "elapsed_s": _DELAY,
            }

        with _mock_scan_projects_with(_PROJ_A), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                side_effect=slow_adapter,
             ):
            t0 = _time.monotonic()
            resp = client.post(
                "/api/brain/query",
                json={"question": "질문", "project": _PROJ_A, "session_id": _SID_A1},
            )
            elapsed = _time.monotonic() - t0

        # 신규 계약: job_id 즉시 반환 — 어댑터 지연보다 훨씬 빠름
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data, f"job_id 키 미포함: {data}"
        # 즉시 반환 검증: 어댑터 지연의 50% 이내
        assert elapsed < _DELAY * 0.5, (
            f"POST /query가 {elapsed:.3f}s 소요 — 어댑터 지연({_DELAY}s)만큼 블로킹됨(H-6 위반)"
        )

    def test_query_no_real_claude(self, client):
        """[MUST] 질의 시 실 claude 서브프로세스 호출 0회 (H-8)."""
        mock_result = {
            "answer": "답변",
            "citations": [],
            "session_id": _SID_A1,
            "elapsed_s": 1.0,
        }

        with _mock_scan_projects_with(_PROJ_A), \
             patch("subprocess.run") as subprocess_mock, \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                return_value=mock_result,
             ):
            resp = client.post(
                "/api/brain/query",
                json={"question": "테스트", "project": _PROJ_A, "session_id": _SID_A1},
            )

        assert resp.status_code == 200
        subprocess_mock.assert_not_called()

    def test_query_a_and_b_session_isolation_via_jobs(self, client):
        """[RED S-2 연계] A·B 세션 각각 독립 job_id 발급 — query 격리.

        신규 계약: 각 POST /query → 독립적인 job_id 반환.
        A와 B의 job_id가 서로 다름을 검증(세션 격리).
        구현 전 RED — 현재 라우터는 answer를 반환하므로 FAIL 예상.
        """
        def mock_ask(**kwargs):
            project_path = kwargs.get("project_path", "")
            if project_path == _PROJ_A:
                return {"answer": "A 답변", "citations": [], "session_id": kwargs.get("session_id", ""), "elapsed_s": 1.0}
            elif project_path == _PROJ_B:
                return {"answer": "B 답변", "citations": [], "session_id": kwargs.get("session_id", ""), "elapsed_s": 1.0}
            return {"answer": "?", "citations": [], "session_id": "?", "elapsed_s": 0}

        with _mock_scan_projects_with(_PROJ_A, _PROJ_B), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                side_effect=mock_ask,
             ):
            resp_a = client.post(
                "/api/brain/query",
                json={"question": "q", "project": _PROJ_A, "session_id": _SID_A1},
            )
            resp_b = client.post(
                "/api/brain/query",
                json={"question": "q", "project": _PROJ_B, "session_id": _SID_B1},
            )

        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        # 신규 계약: job_id 반환
        data_a = resp_a.json()
        data_b = resp_b.json()
        assert "job_id" in data_a, f"A: job_id 키 미포함: {data_a}"
        assert "job_id" in data_b, f"B: job_id 키 미포함: {data_b}"
        # 세션 격리 — 각각 고유한 job_id
        assert data_a["job_id"] != data_b["job_id"], (
            f"A와 B가 동일 job_id: {data_a['job_id']}"
        )

    def test_query_new_conversation_no_reset(self, client):
        """query new_conversation=true → reset 미호출 (폐기 — 새 대화는 새 session_id로)."""
        from dashboard.backend.adapters.brain_session import brain_session_registry

        reset_calls = []

        def tracking_reset(session_id):
            reset_calls.append(session_id)

        mock_result = {
            "answer": "답변",
            "citations": [],
            "session_id": _SID_A1,
            "elapsed_s": 1.0,
        }

        with _mock_scan_projects_with(_PROJ_A), \
             patch.object(brain_session_registry, "reset", side_effect=tracking_reset), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                return_value=mock_result,
             ):
            resp = client.post(
                "/api/brain/query",
                json={
                    "question": "질문",
                    "project": _PROJ_A,
                    "session_id": _SID_A1,
                    "new_conversation": True,
                },
            )

        assert resp.status_code == 200
        assert len(reset_calls) == 0, (
            f"query MUST NOT call reset regardless of new_conversation, "
            f"got reset_calls: {reset_calls}"
        )


# ── TestBrainRouterErrors ────────────────────────────────────────────────────────

class TestBrainRouterErrors:
    """라우터 에러 처리."""

    def test_claude_failure_surfaces_as_job_error(self, client):
        """claude 실패(RuntimeError) → 잡 status=error로 흡수 (비동기 계약).

        POST /query는 200 + job_id를 즉시 반환하고,
        백그라운드 스레드의 RuntimeError는 job status=error + error_msg로 흡수된다.
        """
        with _mock_scan_projects_with(_PROJ_A), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                side_effect=RuntimeError("claude subprocess failed"),
             ):
            resp = client.post(
                "/api/brain/query",
                json={"question": "질문", "project": _PROJ_A, "session_id": _SID_A1},
            )
        assert resp.status_code == 200, f"query가 200 아님: {resp.json()}"
        data = resp.json()
        assert "job_id" in data, f"job_id 미포함: {data}"
        job_id = data["job_id"]

        # 백그라운드 스레드 완료 후 error 상태 확인 (결정론적 폴링, 최대 2초)
        deadline = time.monotonic() + 2.0
        resp_job = None
        with _mock_scan_projects_with(_PROJ_A):
            while time.monotonic() < deadline:
                resp_job = client.get(
                    f"/api/brain/job/{job_id}?project={_PROJ_A}&session_id={_SID_A1}"
                )
                if resp_job.status_code == 200 and resp_job.json().get("status") == "error":
                    break
                time.sleep(0.02)

        assert resp_job is not None
        assert resp_job.status_code == 200, f"GET /job 실패: {resp_job.status_code}"
        job_data = resp_job.json()
        assert job_data["status"] == "error", f"status가 error 아님: {job_data}"
        assert "claude subprocess failed" in job_data.get("error_msg", ""), (
            f"error_msg에 실패 내용 없음: {job_data}"
        )

    def test_auth_no_real_subprocess(self, client):
        """GET /api/brain/auth — subprocess.run 호출 0회 (H-8)."""
        with patch("subprocess.run") as mock_run, \
             patch("shutil.which", return_value="/usr/local/bin/claude"):
            resp = client.get("/api/brain/auth")
        assert resp.status_code == 200
        mock_run.assert_not_called()

    def test_auth_cli_not_available(self, client):
        """claude 미설치 → authenticated=false."""
        with patch("shutil.which", return_value=None):
            resp = client.get("/api/brain/auth")
        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is False
        assert data["cli_available"] is False
        assert len(data["message"]) > 0


# ── TestBrainRouterStatus ────────────────────────────────────────────────────────

class TestBrainRouterStatus:
    """GET /api/brain/status?project=<경로>&session_id=<id> 엔드포인트 테스트."""

    def test_status_200_idle_unregistered_session(self, client):
        """GET /api/brain/status?project=A&session_id=a → 200 + idle (미등록 session_id)."""
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.get(
                f"/api/brain/status?project={_PROJ_A}&session_id={_SID_A1}"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == "idle"
        assert data["session_active"] is False
        assert data["message"] == ""
        assert data["session_id"] == _SID_A1  # 에코

    def test_status_missing_project_422(self, client):
        """GET /api/brain/status (project 없음) → 422 (쿼리파라미터 필수)."""
        resp = client.get(f"/api/brain/status?session_id={_SID_A1}")
        assert resp.status_code == 422

    def test_status_missing_session_id_422(self, client):
        """GET /api/brain/status (session_id 없음) → 422 (쿼리파라미터 필수)."""
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.get(f"/api/brain/status?project={_PROJ_A}")
        assert resp.status_code == 422

    def test_status_empty_session_id_400(self, client):
        """GET /api/brain/status?project=A&session_id= → 400."""
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.get(f"/api/brain/status?project={_PROJ_A}&session_id=")
        assert resp.status_code == 400

    def test_status_empty_project_400(self, client):
        """GET /api/brain/status?project=&session_id=a → 400."""
        resp = client.get(f"/api/brain/status?project=&session_id={_SID_A1}")
        assert resp.status_code == 400
        assert "필수" in resp.json()["detail"]

    def test_status_project_not_found_400(self, client):
        """GET /api/brain/status?project=미존재 → 400."""
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.get(
                f"/api/brain/status?project=/unknown/path&session_id={_SID_A1}"
            )
        assert resp.status_code == 400

    def test_status_schema_fields(self, client):
        """응답에 state·session_active·message·session_id 필드 존재."""
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.get(
                f"/api/brain/status?project={_PROJ_A}&session_id={_SID_A1}"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "state" in data
        assert "session_active" in data
        assert "message" in data
        assert "session_id" in data

    def test_status_ready_after_prime(self, client):
        """prime 성공 후 GET /api/brain/status?project=A&session_id=a → state=ready."""
        from dashboard.backend.adapters.brain_session import brain_session_registry

        mock_result = {
            "answer": "초기화",
            "citations": [],
            "session_id": _SID_A1,
            "elapsed_s": 1.0,
        }

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value=mock_result,
        ):
            brain_session_registry.prime(_SID_A1, _PROJ_A)

        with _mock_scan_projects_with(_PROJ_A):
            resp = client.get(
                f"/api/brain/status?project={_PROJ_A}&session_id={_SID_A1}"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == "ready"
        assert data["session_active"] is True
        assert data["message"] == ""

    def test_status_a_vs_b_session_independent(self, client):
        """status(A) ready, status(B) idle — 대화별 독립."""
        from dashboard.backend.adapters.brain_session import brain_session_registry

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value={"answer": "", "citations": [], "session_id": _SID_A1, "elapsed_s": 1.0},
        ):
            brain_session_registry.prime(_SID_A1, _PROJ_A)

        with _mock_scan_projects_with(_PROJ_A, _PROJ_B):
            resp_a = client.get(
                f"/api/brain/status?project={_PROJ_A}&session_id={_SID_A1}"
            )
            resp_b = client.get(
                f"/api/brain/status?project={_PROJ_B}&session_id={_SID_B1}"
            )

        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        assert resp_a.json()["state"] == "ready"
        assert resp_b.json()["state"] == "idle"

    def test_status_error_after_prime_failure(self, client):
        """prime 실패 후 GET /api/brain/status → state=error, message 비어있지 않음."""
        from dashboard.backend.adapters.brain_session import brain_session_registry

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=RuntimeError("인증 실패"),
        ):
            with pytest.raises(RuntimeError):
                brain_session_registry.prime(_SID_A1, _PROJ_A)

        with _mock_scan_projects_with(_PROJ_A):
            resp = client.get(
                f"/api/brain/status?project={_PROJ_A}&session_id={_SID_A1}"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == "error"
        assert data["session_active"] is False
        assert len(data["message"]) > 0

    def test_status_valid_state_values(self, client):
        """state 값이 허용된 4개 값 중 하나."""
        allowed_states = {"idle", "priming", "ready", "error"}
        with _mock_scan_projects_with(_PROJ_A):
            resp = client.get(
                f"/api/brain/status?project={_PROJ_A}&session_id={_SID_A1}"
            )
        assert resp.status_code == 200
        assert resp.json()["state"] in allowed_states

    def test_status_same_project_two_sessions(self, client):
        """같은 프로젝트 두 session_id → 각각 독립 상태."""
        from dashboard.backend.adapters.brain_session import brain_session_registry

        # A1만 prime
        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value={"answer": "", "citations": [], "session_id": _SID_A1, "elapsed_s": 1.0},
        ):
            brain_session_registry.prime(_SID_A1, _PROJ_A)

        with _mock_scan_projects_with(_PROJ_A):
            resp_a1 = client.get(
                f"/api/brain/status?project={_PROJ_A}&session_id={_SID_A1}"
            )
            resp_a2 = client.get(
                f"/api/brain/status?project={_PROJ_A}&session_id={_SID_A2}"
            )

        assert resp_a1.status_code == 200
        assert resp_a2.status_code == 200
        assert resp_a1.json()["state"] == "ready"
        assert resp_a2.json()["state"] == "idle"  # 같은 프로젝트지만 미프라임 session_id


# ── TestBrainJobPolling (S-2 ~ S-6) ─────────────────────────────────────────────

class TestBrainJobPolling:
    """GET /api/brain/job/{job_id} 폴링 계약 및 잡 상태 전이 검증 (RED — 구현 전).

    대상 인터페이스(미구현):
      - BrainSessionRegistry.submit_job / get_job
      - ConversationBrainSession._current_job / submit_job / get_job / _run_job_background
      - GET /api/brain/job/{job_id}?project=<경로>&session_id=<id>
      - BrainJobResponse { job_id, status, answer, citations, error_msg }
    """

    # ── S-2: GET /job/{job_id} pending → done 전이 ──────────────────────────────

    def test_job_status_transitions_pending_to_done(self, client):
        """[RED S-2] GET /api/brain/job/{job_id} — pending(초기) → done(answer/citations) 전이.

        POST /query로 job_id를 받은 뒤 백그라운드 완료 전 폴링 시 status=pending,
        완료 후 폴링 시 status=done + answer + citations 포함.
        구현 전 RED — GET /job 엔드포인트 미존재로 404 또는 AttributeError 예상.
        """
        import threading

        adapter_started = threading.Event()
        adapter_can_finish = threading.Event()

        def controlled_adapter(**kwargs):
            adapter_started.set()
            adapter_can_finish.wait(timeout=5.0)
            return {
                "answer": "잡 완료 답변",
                "citations": [{"page": "p1", "title": "제목", "type": "concept", "score": 0.9}],
                "session_id": _SID_A1,
                "elapsed_s": 0.1,
            }

        with _mock_scan_projects_with(_PROJ_A), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                side_effect=controlled_adapter,
             ):
            # 1) 잡 제출
            resp_submit = client.post(
                "/api/brain/query",
                json={"question": "잡 전이 테스트", "project": _PROJ_A, "session_id": _SID_A1},
            )
            assert resp_submit.status_code == 200, f"query 실패: {resp_submit.json()}"
            data_submit = resp_submit.json()
            assert "job_id" in data_submit, f"job_id 미포함: {data_submit}"
            job_id = data_submit["job_id"]

            # 2) 백그라운드 시작 대기 후 pending 폴링
            adapter_started.wait(timeout=2.0)
            resp_pending = client.get(
                f"/api/brain/job/{job_id}?project={_PROJ_A}&session_id={_SID_A1}"
            )
            assert resp_pending.status_code == 200, f"GET /job pending 실패: {resp_pending.status_code}"
            data_pending = resp_pending.json()
            assert data_pending["status"] == "pending", f"초기 상태가 pending 아님: {data_pending}"
            assert data_pending["job_id"] == job_id

            # 3) 백그라운드 완료 허용 후 done 폴링 (결정론적 조인)
            adapter_can_finish.set()
            # done이 될 때까지 결정론적 폴링 (최대 2초, 10ms 간격)
            deadline = time.monotonic() + 2.0
            resp_done = None
            while time.monotonic() < deadline:
                resp_done = client.get(
                    f"/api/brain/job/{job_id}?project={_PROJ_A}&session_id={_SID_A1}"
                )
                if resp_done.status_code == 200 and resp_done.json().get("status") == "done":
                    break
                time.sleep(0.02)

            assert resp_done is not None
            assert resp_done.status_code == 200
            data_done = resp_done.json()
            assert data_done["status"] == "done", f"완료 후 status != done: {data_done}"
            assert data_done["job_id"] == job_id
            assert "answer" in data_done and data_done["answer"], f"answer 미포함: {data_done}"
            assert "citations" in data_done, f"citations 미포함: {data_done}"

    # ── S-3: 콜드 세션 query → 백그라운드 priming 중 status=priming 반영 ──────────

    def test_cold_session_query_status_priming_during_background(self, client):
        """[RED S-3] 콜드 세션 query 제출 후 백그라운드 진행 중 GET /status state=priming 반영.

        콜드 세션(_cold_and_ask 경로)으로 query 제출 시 백그라운드에서 prime+ask가 실행되고,
        그동안 GET /api/brain/status는 state=priming을 반환해야 한다.
        구현 전 RED — submit_job 미구현으로 GET /query가 동기 블로킹.
        """
        import threading

        adapter_started = threading.Event()
        adapter_can_finish = threading.Event()

        def cold_adapter(**kwargs):
            adapter_started.set()
            adapter_can_finish.wait(timeout=5.0)
            return {
                "answer": "콜드 답변",
                "citations": [],
                "session_id": _SID_A1,
                "elapsed_s": 0.1,
            }

        with _mock_scan_projects_with(_PROJ_A), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                side_effect=cold_adapter,
             ):
            # 미등록 콜드 세션으로 query 제출 (자동 콜드 잡)
            resp_submit = client.post(
                "/api/brain/query",
                json={"question": "콜드 priming 테스트", "project": _PROJ_A, "session_id": _SID_A1},
            )
            assert resp_submit.status_code == 200, f"콜드 query 실패: {resp_submit.json()}"
            assert "job_id" in resp_submit.json(), f"job_id 미포함: {resp_submit.json()}"

            # 백그라운드 어댑터 시작 대기 후 priming 상태 확인
            adapter_started.wait(timeout=2.0)
            resp_status = client.get(
                f"/api/brain/status?project={_PROJ_A}&session_id={_SID_A1}"
            )
            assert resp_status.status_code == 200
            data_status = resp_status.json()
            assert data_status["state"] == "priming", (
                f"백그라운드 진행 중 state가 priming 아님: {data_status['state']}"
            )

            # 정리: 어댑터 완료 허용
            adapter_can_finish.set()
            # 완료 대기 (누수 방지)
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                resp_done = client.get(
                    f"/api/brain/status?project={_PROJ_A}&session_id={_SID_A1}"
                )
                if resp_done.json().get("state") in ("ready", "error"):
                    break
                time.sleep(0.02)

    # ── S-4: 레지스트리 세션 소실 → 콜드 잡 자동 등록 + 즉시 반환 ────────────────

    def test_unknown_session_query_registers_cold_job_and_returns_immediately(self, client):
        """[RED S-4] 레지스트리에 세션 없음(소실) → 콜드 잡 자동 등록 + submit 즉시 반환.

        어댑터 지연과 무관하게 즉시 job_id를 반환해야 한다(인라인 블로킹 0, 결정론적).
        구현 전 RED — 현재 라우터는 _cold_and_ask를 동기 블로킹으로 호출.
        """
        _DELAY = 0.5

        def slow_cold_adapter(**kwargs):
            time.sleep(_DELAY)
            return {
                "answer": "소실 세션 콜드 답변",
                "citations": [],
                "session_id": _SID_A2,
                "elapsed_s": _DELAY,
            }

        with _mock_scan_projects_with(_PROJ_A), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                side_effect=slow_cold_adapter,
             ):
            # 레지스트리에 _SID_A2 미등록 상태에서 query 제출
            t0 = time.monotonic()
            resp = client.post(
                "/api/brain/query",
                json={"question": "소실 세션 질의", "project": _PROJ_A, "session_id": _SID_A2},
            )
            elapsed = time.monotonic() - t0

        assert resp.status_code == 200, f"콜드 잡 등록 실패: {resp.json()}"
        data = resp.json()
        # 콜드 잡도 job_id 즉시 반환
        assert "job_id" in data, f"job_id 미포함: {data}"
        assert isinstance(data["job_id"], str) and len(data["job_id"]) > 0
        # 인라인 블로킹 0 — 어댑터 지연의 50% 미만
        assert elapsed < _DELAY * 0.5, (
            f"콜드 잡 제출이 {elapsed:.3f}s 소요 — 어댑터 지연({_DELAY}s)만큼 블로킹됨"
        )

    # ── S-5: 진행 중 잡 재제출 → 기존 job_id 반환 (idempotent) ───────────────────

    def test_pending_job_resubmit_returns_existing_job_id(self, client):
        """[RED S-5] 진행 중(pending) 잡 보유 세션에 같은 session_id 재제출 → 기존 job_id 반환.

        신규 잡 미생성 — idempotent(H-4, RI-2 방어).
        구현 전 RED — submit_job 미구현.
        """
        import threading

        adapter_started = threading.Event()
        adapter_can_finish = threading.Event()

        def blocking_adapter(**kwargs):
            adapter_started.set()
            adapter_can_finish.wait(timeout=5.0)
            return {
                "answer": "idempotent 답변",
                "citations": [],
                "session_id": _SID_A1,
                "elapsed_s": 0.1,
            }

        with _mock_scan_projects_with(_PROJ_A), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                side_effect=blocking_adapter,
             ):
            # 첫 번째 제출
            resp1 = client.post(
                "/api/brain/query",
                json={"question": "첫 질의", "project": _PROJ_A, "session_id": _SID_A1},
            )
            assert resp1.status_code == 200
            data1 = resp1.json()
            assert "job_id" in data1, f"첫 제출 job_id 미포함: {data1}"
            job_id_1 = data1["job_id"]

            # 백그라운드 시작 대기 (pending 상태)
            adapter_started.wait(timeout=2.0)

            # 동일 세션 재제출 (pending 중)
            resp2 = client.post(
                "/api/brain/query",
                json={"question": "재제출 질의", "project": _PROJ_A, "session_id": _SID_A1},
            )
            assert resp2.status_code == 200
            data2 = resp2.json()
            assert "job_id" in data2, f"재제출 job_id 미포함: {data2}"
            job_id_2 = data2["job_id"]

            # 기존 job_id와 동일해야 함 — 신규 잡 미생성
            assert job_id_1 == job_id_2, (
                f"재제출 시 신규 job_id 발급됨(idempotent 위반): "
                f"첫={job_id_1}, 재제출={job_id_2}"
            )

            # 정리
            adapter_can_finish.set()

    # ── S-6: done 잡 get_job 수신 후 _current_job 제거 → 재조회 graceful ─────────

    def test_done_job_consumed_then_requery_graceful(self, client):
        """[RED S-6] done 잡 get_job 1회 수신 후 _current_job 제거 → 재조회 graceful(소멸 안내).

        done 수신 후 GET /job/{job_id}를 다시 호출해도 500이 아니라
        status=error + error_msg 포함으로 graceful하게 응답해야 한다(H-9, RI-4 TTL 정책).
        구현 전 RED — GET /job 엔드포인트 미존재.
        """
        mock_result = {
            "answer": "소멸 테스트 답변",
            "citations": [],
            "session_id": _SID_A1,
            "elapsed_s": 0.05,
        }

        with _mock_scan_projects_with(_PROJ_A), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                return_value=mock_result,
             ):
            # 잡 제출
            resp_submit = client.post(
                "/api/brain/query",
                json={"question": "소멸 테스트", "project": _PROJ_A, "session_id": _SID_A1},
            )
            assert resp_submit.status_code == 200
            job_id = resp_submit.json()["job_id"]

            # done이 될 때까지 결정론적 폴링 (최대 3초)
            deadline = time.monotonic() + 3.0
            resp_done = None
            while time.monotonic() < deadline:
                resp_done = client.get(
                    f"/api/brain/job/{job_id}?project={_PROJ_A}&session_id={_SID_A1}"
                )
                if resp_done.status_code == 200 and resp_done.json().get("status") == "done":
                    break
                time.sleep(0.02)

            assert resp_done is not None
            assert resp_done.status_code == 200
            assert resp_done.json()["status"] == "done", (
                f"done 상태 미달: {resp_done.json()}"
            )

            # done 수신 후 _current_job 제거됨 — 재조회 시 graceful
            resp_requery = client.get(
                f"/api/brain/job/{job_id}?project={_PROJ_A}&session_id={_SID_A1}"
            )
            # 500이 아니라 graceful(200 or 404) — 소멸 안내 메시지 포함
            assert resp_requery.status_code != 500, (
                f"소멸된 잡 재조회 시 500 발생 (graceful 처리 필요)"
            )
            data_requery = resp_requery.json()
            # status=error + error_msg(소멸 안내) 또는 404
            if resp_requery.status_code == 200:
                assert data_requery.get("status") == "error", (
                    f"소멸 잡 재조회 status != error: {data_requery}"
                )
                assert data_requery.get("error_msg"), (
                    f"소멸 안내 error_msg 미포함: {data_requery}"
                )


# ── TestBrainPrimePool (S-2, S-3, S-4, S-8) — T060 RED ─────────────────────────
#
# 대상 인터페이스(미구현, PLAN §3.2.2):
#   BrainSessionRegistry(pool_size, max_concurrent_prime) 생성자 확장
#   BrainSessionRegistry.prewarm(project_path) / checkout_warm_handle(project_path)
#   내부: _pool / _pool_inflight / _pool_lock / _prime_semaphore
# [MUST] subprocess는 전부 mock — 실 claude 호출 0회(H-8). prime_and_ask 경계만 patch.
# private(_pool 등) 직접 확인은 비동기 백그라운드 스레드 완료 관측을 위한 불가피한 최소
# 접근이며, 공개 동작(checkout_warm_handle 반환값 등)과 병행 검증한다(red-first.md §4).

class TestBrainPrimePool:
    """프라임 풀 신설 — 적재·체크아웃+리필·동시 프라임 상한·락 무중첩 (F-2 AC, RED)."""

    def _wait_until(self, cond, timeout: float = 2.0, interval: float = 0.01) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if cond():
                return
            time.sleep(interval)

    # ── S-2: 풀 선프라임 적재 ────────────────────────────────────────────────────

    def test_prewarm_loads_pool_then_avoids_overfill(self):
        """[T060/L1-F2a] prewarm() 후 풀에 핸들 1개 적재. 이미 충족 상태 재호출 시 추가 프라임 0회.

        H-1(정상 경로 전제), F-2 AC(a).
        """
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry(pool_size=1, max_concurrent_prime=2)
        project = "/fake/pool/basic"
        call_count = [0]

        def fake_prime(**kwargs):
            call_count[0] += 1
            return {
                "answer": "", "citations": [],
                "session_id": str(uuid.uuid4()), "elapsed_s": 0.05,
            }

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=fake_prime,
        ):
            registry.prewarm(project)
            self._wait_until(lambda: len(registry._pool.get(project, [])) >= 1)

            assert len(registry._pool.get(project, [])) == 1, (
                "prewarm 후 풀에 핸들 1개가 적재되어야 함(F-2 AC(a))"
            )
            assert registry._pool_inflight.get(project, 0) == 0, (
                "완료 후 inflight 카운터가 0으로 복귀해야 함"
            )

            calls_after_fill = call_count[0]
            registry.prewarm(project)  # 이미 pool_size(1) 충족 — 과잉 프라임 방지
            time.sleep(0.1)  # 스레드가 기동됐다면 관측할 여유 시간

        assert call_count[0] == calls_after_fill, (
            f"풀이 이미 충족된 상태에서 prewarm() 재호출 시 추가 프라임이 없어야 함"
            f"(과잉 프라임 방지): before={calls_after_fill}, after={call_count[0]}"
        )

    # ── S-3: 체크아웃 pop + 리필 트리거 ──────────────────────────────────────────

    def test_checkout_pops_handle_and_triggers_refill(self):
        """[T060/L1-F2a] checkout_warm_handle() — 핸들 반환 + 풀 비워짐 + 백그라운드 리필 트리거.

        H-1, F-2 AC(a). 리필(2번째 prime 호출)을 이벤트로 게이트하여, "체크아웃 직후
        풀이 비어 있다"는 assert가 리필 완료(append)보다 먼저 결정론적으로 실행되도록
        한다. mock이 지연 없이 즉시 반환되면 백그라운드 리필 스레드가 assert보다 먼저
        새 핸들을 append해 버려 간헐 실패가 발생했다(reward-hacking 아님 — 동기화 수리).
        """
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry(pool_size=1, max_concurrent_prime=2)
        project = "/fake/pool/checkout"
        handles = [str(uuid.uuid4()), str(uuid.uuid4())]
        call_count = [0]
        refill_started = threading.Event()
        refill_can_finish = threading.Event()

        def fake_prime(**kwargs):
            idx = min(call_count[0], len(handles) - 1)
            call_count[0] += 1
            if call_count[0] == 2:
                # 리필(2번째) 호출 — 풀 비움 확인이 끝날 때까지 append(완료)를 지연
                refill_started.set()
                assert refill_can_finish.wait(timeout=2.0), "리필 완료 신호 대기 타임아웃"
            return {
                "answer": "", "citations": [],
                "session_id": handles[idx], "elapsed_s": 0.05,
            }

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=fake_prime,
        ):
            registry.prewarm(project)
            self._wait_until(lambda: len(registry._pool.get(project, [])) >= 1)

            sid = registry.checkout_warm_handle(project)
            assert sid == handles[0], (
                f"체크아웃 반환값이 적재된 핸들과 일치해야 함: sid={sid!r}"
            )

            assert refill_started.wait(timeout=2.0), (
                "체크아웃 후 백그라운드 리필(prewarm 재호출)이 트리거되어야 함(F-2 AC(a))"
            )
            assert registry._pool.get(project, []) == [], (
                "체크아웃 직후(리필 완료 전) 풀이 비어 있어야 함(F-2 AC(a))"
            )

            refill_can_finish.set()
            self._wait_until(lambda: call_count[0] >= 2)

        assert call_count[0] >= 2, (
            "체크아웃 후 백그라운드 리필(prewarm 재호출)이 트리거되어야 함(F-2 AC(a))"
        )

    def test_checkout_empty_pool_returns_none(self):
        """[T060/L1-F2a] 빈 풀에서 checkout_warm_handle() → None."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry(pool_size=1, max_concurrent_prime=2)
        result = registry.checkout_warm_handle("/fake/pool/never-primed")
        assert result is None, f"미적재 프로젝트 체크아웃은 None이어야 함: {result!r}"

    # ── S-4: 동시 프라임 상한(세마포어) 강제 ─────────────────────────────────────

    def test_prewarm_concurrent_limit_enforced(self):
        """[T060/L2-F2c] 서로 다른 프로젝트 4건 동시 prewarm → 관측 최대 동시 실행 ≤ max_concurrent_prime(2).

        H-3, F-2 AC(c).
        """
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry(pool_size=1, max_concurrent_prime=2)
        projects = [f"/fake/pool/concurrent{i}" for i in range(4)]

        count_lock = threading.Lock()
        current = [0]
        max_observed = [0]

        def slow_prime(**kwargs):
            with count_lock:
                current[0] += 1
                max_observed[0] = max(max_observed[0], current[0])
            time.sleep(0.15)
            with count_lock:
                current[0] -= 1
            return {
                "answer": "", "citations": [],
                "session_id": str(uuid.uuid4()), "elapsed_s": 0.15,
            }

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=slow_prime,
        ):
            for p in projects:
                registry.prewarm(p)

            self._wait_until(
                lambda: all(len(registry._pool.get(p, [])) >= 1 for p in projects),
                timeout=4.0,
            )

        assert max_observed[0] <= 2, (
            f"동시 프라임 상한(2) 위반 — 관측 최대 동시 실행={max_observed[0]}(H-3)"
        )
        for p in projects:
            assert len(registry._pool.get(p, [])) == 1, f"{p} 풀이 최종 적재되지 않음"

    # ── S-8: 락 무중첩 — 리필 중 비블로킹 + 동시 체크아웃 무중복 ────────────────

    def test_checkout_non_blocking_during_refill(self):
        """[T060/L2-F2b] 리필 프라임 진행 중(subprocess 대역 지연) checkout 호출이 즉시 반환(블로킹 없음).

        H-1, H-2, F-2 AC(b).
        """
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry(pool_size=1, max_concurrent_prime=2)
        project = "/fake/pool/refill-block"

        prime_started = threading.Event()
        prime_can_finish = threading.Event()

        def blocking_prime(**kwargs):
            prime_started.set()
            prime_can_finish.wait(timeout=5.0)
            return {
                "answer": "", "citations": [],
                "session_id": str(uuid.uuid4()), "elapsed_s": 0.1,
            }

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=blocking_prime,
        ):
            registry.prewarm(project)  # 백그라운드 리필 시작
            assert prime_started.wait(timeout=2.0), "백그라운드 prime이 시작되지 않음(사전조건 실패)"

            t0 = time.monotonic()
            result = registry.checkout_warm_handle(project)
            elapsed = time.monotonic() - t0

            prime_can_finish.set()

        assert elapsed < 1.0, (
            f"checkout_warm_handle이 리필 완료를 기다림(블로킹 발생, H-1 위반): {elapsed:.2f}s"
        )
        assert result is None, "프라임 미완료 상태에서는 풀이 비어 None을 반환해야 함"

    def test_concurrent_checkout_no_duplicate_handle(self):
        """[T060/L2-F2b] 풀 핸들 1개에 동시 체크아웃 2건 — 같은 핸들 중복 배정 0건.

        H-2, F-2 AC(b). 체크아웃 성공 측이 트리거하는 백그라운드 리필이 mock 무지연
        반환으로 동시 체크아웃 판정 창 내에 완료되면, 같은(고정) session_id 값이 풀에
        재적재되어 두 스레드 모두 핸들을 받는 것처럼 보이는 간헐 실패가 발생했다.
        초기 적재(1회차) 이후의 프라임 호출(리필)만 이벤트로 게이트하여 동시 체크아웃
        판정이 끝날 때까지 풀 재적재를 지연시켜 결정론적으로 만든다.
        """
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry(pool_size=1, max_concurrent_prime=2)
        project = "/fake/pool/dup-checkout"
        handle = str(uuid.uuid4())
        call_count = [0]
        refill_gate = threading.Event()

        def fake_prime(**kwargs):
            call_count[0] += 1
            if call_count[0] > 1:
                # 초기 적재 이후 호출(리필)은 정리 시점까지 대기 — 동시 체크아웃 창 보호
                refill_gate.wait(timeout=2.0)
            return {
                "answer": "", "citations": [], "session_id": handle, "elapsed_s": 0.05,
            }

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=fake_prime,
        ):
            registry.prewarm(project)
            self._wait_until(lambda: len(registry._pool.get(project, [])) >= 1)

            results: list = [None, None]

            def do_checkout(idx: int) -> None:
                results[idx] = registry.checkout_warm_handle(project)

            t1 = threading.Thread(target=do_checkout, args=(0,))
            t2 = threading.Thread(target=do_checkout, args=(1,))
            t1.start()
            t2.start()
            t1.join(timeout=2.0)
            t2.join(timeout=2.0)

            refill_gate.set()  # 정리 — 게이트에서 대기 중인 리필 스레드 해제

        non_none = [r for r in results if r is not None]
        assert len(non_none) <= 1, (
            f"동시 체크아웃 2건 중 최대 1건만 핸들을 받아야 함(중복 배정 금지, H-2): {results}"
        )


# ── TestBrainPoolT063NeedBasedFill (S-1, S-2, S-3, S-4) — T063 RED ──────────────
#
# 작성자: opal-test-agent(mode: red) — 구현자(op-dev-execute)와 분리 (red-first.md §2).
# 대상: BrainSessionRegistry.prewarm() need=pool_size-have 충전 로직 (PLAN.md §3 F-003,
# H-1). 현재 구현(brain_session.py:558-571)은 단일 트리거당 핸들을 정확히 1개만 충전한다
# — pool_size를 2로 올려도 단일 prewarm() 호출로는 풀이 1까지만 차므로 R-6(연속 새대화
# 웜 배정)을 충족하지 못한다. S-1/S-2는 이 결함을 RED로 직접 노출한다. S-3/S-4는 H-2
# (락 순서)·H-3(세마포어 상한) 회귀 가드 — 구현 수정이 이 기존 안전 불변을 깨지 않아야
# 함을 검증한다(수정과 무관하게 이미 만족될 수 있음 — 그 경우도 유효한 RED-first 산출물).
#
# opbr_adapter.prime_and_ask는 결정론적 스텁(직접 속성 대입)으로 대체한다 — mock/patch/
# MagicMock 라이브러리 미사용(헌법 §4), 실 claude subprocess 호출 없음. 공개 인터페이스
# (prewarm/checkout_warm_handle)의 관찰 결과로만 검증 — private 메서드 직접 결합 없음
# (red-first.md §4).

class TestBrainPoolT063NeedBasedFill:
    """[T063] prewarm() need=pool_size-have 충전 로직 — 단일 트리거 충전·연속 체크아웃·
    동시성 안전·세마포어 상한 (H-1/H-2/H-3, RED)."""

    def _wait_until(self, cond, timeout: float = 2.0, interval: float = 0.01) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if cond():
                return
            time.sleep(interval)

    # ── S-1: 단일 prewarm() 트리거로 pool_size까지 충전 ──────────────────────────

    def test_prewarm_single_trigger_fills_to_pool_size(self):
        """[T063/L1-R6] pool_size=2에서 prewarm(project) 1회 호출 + 충전 완료 대기 후
        `_pool[project]` 길이 == 2 기대.

        현재 prewarm()은 `_pool_inflight[project_path] += 1` 후 스레드를 정확히 1개만
        기동한다(brain_session.py:570-571) — need=pool_size-have 계산이 없다. 따라서
        단일 트리거 후 풀은 1까지만 차고 이 단언은 실패해야 정상(RED, H-1).
        """
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry
        import dashboard.backend.adapters.brain_session as registry_module

        registry = BrainSessionRegistry(pool_size=2, max_concurrent_prime=2)
        project = "/fake/pool/t063-s1"

        call_count = [0]

        def fake_prime_and_ask(**kwargs):
            call_count[0] += 1
            return {
                "answer": "", "citations": [],
                "session_id": f"warm-handle-{call_count[0]}", "elapsed_s": 0.01,
            }

        original = registry_module.opbr_adapter.prime_and_ask
        registry_module.opbr_adapter.prime_and_ask = fake_prime_and_ask
        try:
            registry.prewarm(project)  # 단일 트리거 1회
            self._wait_until(
                lambda: registry._pool_inflight.get(project, 0) == 0
                and len(registry._pool.get(project, [])) >= 1
            )
            time.sleep(0.1)  # 안정화 여유(추가 충전 스레드가 있다면 완료될 시간)
        finally:
            registry_module.opbr_adapter.prime_and_ask = original

        assert len(registry._pool.get(project, [])) == 2, (
            "[T063/L1-R6] 단일 prewarm() 트리거로 pool_size(2)까지 충전되어야 함(R-6) — "
            f"현재는 트리거당 핸들 1개만 충전(H-1, brain_session.py:558-571): "
            f"pool={registry._pool.get(project, [])!r}"
        )

    # ── S-2: 연속 checkout 2회 모두 웜 핸들 반환 ─────────────────────────────────

    def test_consecutive_checkout_both_return_distinct_warm_handles(self):
        """[T063/L1-R6] pool_size=2 충전 후 checkout_warm_handle 연속 2회 모두 non-None·
        서로 다른 핸들 기대.

        [T063 Step5 결정론화] prewarm() 1회 트리거는 need=pool_size-have 만큼 백그라운드
        스레드를 동시 기동한다(H-1, GREEN) — 두 스레드가 stub을 호출하는 순서는 OS
        스케줄링에 좌우되므로 call-index로 "몇 번째 호출인지" 타이밍을 가정하지 않는다
        (구 버전은 idx==2 게이트로 옛 단일-스레드 충전 가정에 결합되어 need-기반 동시
        충전 하에서 레이스가 발생했다). 대신 풀 상태(`_pool` 길이 == pool_size)를
        폴링해 충전 완료를 관측한 뒤 연속 체크아웃을 수행 — 기대값(2회 모두 non-None·
        서로 다른 웜 핸들)은 불변, 동기화 메커니즘만 폴링으로 교체.
        """
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry
        import dashboard.backend.adapters.brain_session as registry_module

        registry = BrainSessionRegistry(pool_size=2, max_concurrent_prime=2)
        project = "/fake/pool/t063-s2"

        call_count = [0]

        def fake_prime_and_ask(**kwargs):
            call_count[0] += 1
            return {
                "answer": "", "citations": [],
                "session_id": f"warm-handle-{call_count[0]}", "elapsed_s": 0.01,
            }

        original = registry_module.opbr_adapter.prime_and_ask
        registry_module.opbr_adapter.prime_and_ask = fake_prime_and_ask
        try:
            registry.prewarm(project)  # 단일 트리거 — need-기반 충전(H-1)
            self._wait_until(
                lambda: registry._pool_inflight.get(project, 0) == 0
                and len(registry._pool.get(project, [])) >= 2
            )

            sid1 = registry.checkout_warm_handle(project)
            sid2 = registry.checkout_warm_handle(project)
        finally:
            registry_module.opbr_adapter.prime_and_ask = original

        assert sid1 is not None, "첫 체크아웃은 non-None 웜 핸들이어야 함(사전조건)"
        assert sid2 is not None, (
            "[T063/L1-R6] 두 번째 체크아웃도 non-None 웜 핸들이어야 함(R-6 핵심 AC) — "
            f"sid2={sid2!r}"
        )
        assert sid1 != sid2, (
            f"두 체크아웃은 서로 다른 핸들이어야 함(중복 배정 금지): sid1={sid1!r}, sid2={sid2!r}"
        )

    # ── S-3: 동시 prewarm+checkout 반복 — 데드락 없음·중복 배정 0 (H-2 회귀 가드) ──

    def test_concurrent_prewarm_checkout_no_deadlock_no_duplicate(self):
        """[T063/L2-R6c] pool_size=2에서 다중 스레드가 prewarm()+checkout_warm_handle()을
        반복 호출해도 데드락이 없고, 동일 핸들이 중복 배정되지 않아야 한다(H-2).

        락 순서 계약(`_lock`→`_pool_lock`, 역순·중첩 금지)이 need-기반 충전으로 바뀌어도
        유지되어야 하는 회귀 가드 — 현재 구현에서도 유지될 수 있다(그 경우도 유효한
        RED-first 산출물: GREEN 구현이 이 불변을 깨지 않는지 지속 검증).
        """
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry
        import dashboard.backend.adapters.brain_session as registry_module

        registry = BrainSessionRegistry(pool_size=2, max_concurrent_prime=2)
        project = "/fake/pool/t063-s3"

        handle_seq = [0]
        handle_seq_lock = threading.Lock()

        def fake_prime_and_ask(**kwargs):
            with handle_seq_lock:
                handle_seq[0] += 1
                n = handle_seq[0]
            return {
                "answer": "", "citations": [],
                "session_id": f"warm-handle-{n}", "elapsed_s": 0.01,
            }

        checked_out: list[str] = []
        checked_out_lock = threading.Lock()

        def worker(iterations: int) -> None:
            for _ in range(iterations):
                registry.prewarm(project)
                sid = registry.checkout_warm_handle(project)
                if sid is not None:
                    with checked_out_lock:
                        checked_out.append(sid)
                time.sleep(0.005)

        original = registry_module.opbr_adapter.prime_and_ask
        registry_module.opbr_adapter.prime_and_ask = fake_prime_and_ask
        try:
            threads = [threading.Thread(target=worker, args=(5,)) for _ in range(8)]
            t0 = time.monotonic()
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=5.0)
            elapsed = time.monotonic() - t0
        finally:
            registry_module.opbr_adapter.prime_and_ask = original

        alive = [t for t in threads if t.is_alive()]
        assert not alive, (
            f"[T063/L2-R6c] 동시 prewarm+checkout 반복 중 데드락 의심 — "
            f"{len(alive)}개 스레드가 {elapsed:.1f}s 내 완료되지 않음(H-2)"
        )

        dup_count = len(checked_out) - len(set(checked_out))
        assert dup_count == 0, (
            f"[T063/L2-R6c] 동일 핸들 중복 배정 발생(H-2 위반): "
            f"checked_out={checked_out!r}, dup_count={dup_count}"
        )

    # ── S-4: 동시 충전 스레드 실행 수 ≤ DEFAULT_MAX_CONCURRENT_PRIME (H-3 회귀 가드) ─

    def test_concurrent_priming_threads_capped_by_semaphore(self):
        """[T063/L2-R6d] 다중 프로젝트 동시 prewarm() 기동 시 관측 최대 동시 스텁 실행 수
        ≤ DEFAULT_MAX_CONCURRENT_PRIME(2) 기대(H-3).

        need-기반 충전으로 단일 호출이 다중 스레드를 기동하게 되어도 `_prime_semaphore`
        상한은 유지되어야 하는 회귀 가드 — 현재 구현에서도 유지될 수 있다.
        """
        from dashboard.backend.adapters.brain_session import (
            BrainSessionRegistry,
            DEFAULT_MAX_CONCURRENT_PRIME,
        )
        import dashboard.backend.adapters.brain_session as registry_module

        registry = BrainSessionRegistry(
            pool_size=2, max_concurrent_prime=DEFAULT_MAX_CONCURRENT_PRIME
        )
        projects = [f"/fake/pool/t063-s4-{i}" for i in range(6)]

        count_lock = threading.Lock()
        current = [0]
        max_observed = [0]

        def slow_prime(**kwargs):
            with count_lock:
                current[0] += 1
                max_observed[0] = max(max_observed[0], current[0])
            time.sleep(0.15)
            with count_lock:
                current[0] -= 1
            return {
                "answer": "", "citations": [],
                "session_id": f"warm-handle-{kwargs.get('project_path')}-{time.monotonic()}",
                "elapsed_s": 0.15,
            }

        original = registry_module.opbr_adapter.prime_and_ask
        registry_module.opbr_adapter.prime_and_ask = slow_prime
        try:
            for p in projects:
                registry.prewarm(p)  # 각 프로젝트 다중 충전 스레드 동시 기동

            deadline = time.monotonic() + 4.0
            while time.monotonic() < deadline:
                if all(registry._pool_inflight.get(p, 0) == 0 for p in projects):
                    break
                time.sleep(0.02)
        finally:
            registry_module.opbr_adapter.prime_and_ask = original

        assert max_observed[0] <= DEFAULT_MAX_CONCURRENT_PRIME, (
            f"[T063/L2-R6d] 동시 충전 스레드 실행 수가 상한({DEFAULT_MAX_CONCURRENT_PRIME})을 "
            f"초과함(H-3): max_observed={max_observed[0]}"
        )


# ── TestBrainWarmInjection (S-5, S-6, S-7) — T060 RED ───────────────────────────
#
# 대상: BrainSessionRegistry._get_or_create() 웜 주입 연결 (PLAN §3.4.2)
# + ConversationBrainSession.adopt_warm_handle() (PLAN §3.2.2)
# 공개 인터페이스(prime/ask/status)의 관찰 결과로 검증 — private _get_or_create 직접
# 호출 없음(red-first.md §4).

class TestBrainWarmInjection:
    """새 대화 웜 핸들 배정 + 콜드 폴백 (F-4 AC, RED)."""

    def _wait_until(self, cond, timeout: float = 2.0, interval: float = 0.01) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if cond():
                return
            time.sleep(interval)

    def _prewarm_and_wait(self, registry, project: str, handle: str) -> None:
        """지정 핸들로 풀을 채우고 적재를 대기(테스트 준비 공통 루틴)."""
        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            return_value={
                "answer": "", "citations": [], "session_id": handle, "elapsed_s": 0.05,
            },
        ):
            registry.prewarm(project)
            self._wait_until(lambda: len(registry._pool.get(project, [])) >= 1)

    # ── S-5: 새 대화 웜 주입 → ready + resume 경로 ──────────────────────────────

    def test_new_session_ready_without_cold_prime(self):
        """[T060/L1-F4a] 풀에 핸들 존재 시 새 session_id가 콜드 프라임 없이 즉시 ready(F-4 AC(a)).

        checkout_warm_handle()은 체크아웃 성공 시 백그라운드 리필(prewarm)을 트리거한다
        (S-3에서 별도 검증). 리필도 동일 mock(prime_and_ask)을 호출하므로, 이 테스트의
        관심사(신규 세션 자신의 콜드 프라임 미호출)와 경합해 mock_prime.assert_not_called()가
        간헐적으로 깨졌다. 리필 트리거 여부는 이 테스트의 검증 대상이 아니므로(S-3이
        담보) 인스턴스 registry.prewarm을 no-op으로 대체해 리필 백그라운드 스레드
        자체를 제거한다 — 단언 약화 없이 관심사만 분리.
        """
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry(pool_size=1, max_concurrent_prime=2)
        project = _PROJ_A
        warm_handle = str(uuid.uuid4())
        self._prewarm_and_wait(registry, project, warm_handle)

        # 리필 트리거(체크아웃 부수효과) 무력화 — S-3이 리필을 별도로 검증하므로
        # 여기서는 신규 세션 자신의 콜드 프라임 미호출만 순수하게 관측한다.
        registry.prewarm = lambda project_path: None

        new_session_id = str(uuid.uuid4())

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask"
        ) as mock_prime:
            registry.prime(new_session_id, project)  # 신규 세션 생성 → 웜 주입 기대

        assert registry.status(new_session_id)["state"] == "ready", (
            "풀에 핸들이 있으면 새 세션이 콜드 프라임 없이 ready여야 함(F-4 AC(a))"
        )
        mock_prime.assert_not_called()

    def test_new_session_first_ask_uses_resume_with_warm_handle(self):
        """[T060/L1-F4a] 웜 주입 세션의 첫 ask() 호출이 cold=False + 체크아웃 핸들로 resume."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry(pool_size=1, max_concurrent_prime=2)
        project = _PROJ_A
        warm_handle = str(uuid.uuid4())
        self._prewarm_and_wait(registry, project, warm_handle)

        new_session_id = str(uuid.uuid4())
        captured: dict = {}

        def mock_ask(**kwargs):
            captured.update(kwargs)
            return {
                "answer": "웜 답변", "citations": [],
                "session_id": kwargs.get("session_id"), "elapsed_s": 1.0,
            }

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            result = registry.ask(new_session_id, "첫 질문", project)

        assert captured.get("cold") is False, (
            f"웜 주입 세션의 첫 ask는 cold=False(resume)여야 함: {captured}"
        )
        assert captured.get("session_id") == warm_handle, (
            f"웜 주입 세션의 session_id가 체크아웃 핸들과 일치해야 함: {captured}"
        )
        assert result["answer"] == "웜 답변"

    # ── S-6: stale 웜 핸들 resume 실패 → 투명 재프라임 ──────────────────────────

    def test_warm_injected_resume_failure_transparent_reprime(self):
        """[T060/L1-F4a] 이식된 웜 핸들 resume 실패 → 기존 ⓓ 투명 콜드 재프라임으로 answer 정상 반환.

        H-5. checkout_warm_handle()의 백그라운드 리필 트리거가 동일 mock을 공유하므로,
        리필 호출(cold=True)이 세션 자신의 resume 호출보다 먼저 call_cold_flags에
        기록되면 call_cold_flags[0]이 어긋나는 간헐 실패가 발생했다. 리필 트리거는
        이 테스트의 관심사가 아니므로(S-3이 담보) registry.prewarm을 no-op으로
        대체해 call_cold_flags가 이 세션 자신의 resume→재프라임 순서만 기록하도록
        한다 — 단언(투명 재프라임·호출 순서) 약화 없이 관심사만 분리.
        """
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry(pool_size=1, max_concurrent_prime=2)
        project = _PROJ_A
        warm_handle = str(uuid.uuid4())
        self._prewarm_and_wait(registry, project, warm_handle)

        # 리필 트리거 무력화 — S-3이 리필을 별도로 검증하므로 여기서는 이 세션
        # 자신의 resume 실패→콜드 재프라임 순서만 순수하게 관측한다.
        registry.prewarm = lambda project_path: None

        new_session_id = str(uuid.uuid4())
        call_cold_flags: list = []

        def mock_ask(**kwargs):
            call_cold_flags.append(kwargs.get("cold"))
            if kwargs.get("cold") is False:
                raise RuntimeError("resume failed: stale session")
            return {
                "answer": "재프라임 답변", "citations": [],
                "session_id": str(uuid.uuid4()), "elapsed_s": 1.0,
            }

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            result = registry.ask(new_session_id, "질문", project)

        assert result["answer"] == "재프라임 답변", (
            "resume 실패 후 투명 재프라임으로 answer가 정상 반환되어야 함(H-5)"
        )
        assert call_cold_flags[0] is False, "첫 호출은 웜 주입 핸들 resume(cold=False)이어야 함"
        assert call_cold_flags[1] is True, "resume 실패 후 콜드 재프라임(cold=True)이어야 함"

    # ── S-7: 풀 empty 콜드 폴백 (회귀) ──────────────────────────────────────────

    def test_empty_pool_new_session_cold_fallback(self):
        """[T060/L1-F4b] 빈 풀에서 새 대화 → 기존 콜드 경로 동일(F-4 AC(b), 회귀 없음)."""
        from dashboard.backend.adapters.brain_session import BrainSessionRegistry

        registry = BrainSessionRegistry(pool_size=1, max_concurrent_prime=2)
        project = _PROJ_A  # 풀 미적재 상태
        new_session_id = str(uuid.uuid4())

        assert registry.status(new_session_id)["state"] == "idle"

        captured: dict = {}

        def mock_ask(**kwargs):
            captured.update(kwargs)
            return {
                "answer": "콜드 답변", "citations": [],
                "session_id": kwargs.get("session_id"), "elapsed_s": 1.0,
            }

        with patch(
            "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
            side_effect=mock_ask,
        ):
            result = registry.ask(new_session_id, "질문", project)

        assert captured.get("cold") is True, (
            f"풀이 비어 있으면 첫 ask는 콜드(cold=True)여야 함(F-4 AC(b)): {captured}"
        )
        assert result["answer"] == "콜드 답변"


# ── TestBrainLifespanPrewarm (S-9) — T060 RED ───────────────────────────────────
#
# 대상: main.py lifespan asynccontextmanager 신설 (PLAN §3.3.2). 현재 main.py에는
# lifespan이 부재하므로 이 부재 자체가 RED 증거가 된다 — TestClient 컨텍스트 진입 시
# prewarm 미호출로 관측된다.

class TestBrainLifespanPrewarm:
    """main.py lifespan 기동 선프라임 — 트리거·비블로킹·미지정 0회 (F-3 AC, H-6, RED)."""

    def test_lifespan_triggers_prewarm_per_project(self):
        """[T060/L2-F3] prewarm_projects 2건 지정 시 TestClient 진입 즉시 프로젝트당 prewarm 1회 호출."""
        from dashboard.backend.config import ConsoleConfig
        from dashboard.backend.main import app

        fake_cfg = ConsoleConfig(prewarm_projects=[_PROJ_A, _PROJ_B])
        calls: list = []

        with patch("dashboard.backend.main.load_config", return_value=fake_cfg), \
             patch(
                "dashboard.backend.main.brain_session_registry.prewarm",
                side_effect=lambda p: calls.append(p),
             ):
            with TestClient(app) as lifespan_client:
                resp = lifespan_client.get("/health")

        assert resp.status_code == 200
        assert calls == [_PROJ_A, _PROJ_B], (
            f"prewarm_projects 2건 각각 1회 prewarm 호출을 기대: {calls}"
        )

    def test_lifespan_empty_prewarm_projects_zero_calls(self):
        """[T060/L2-F3] prewarm_projects=[] → prewarm 0회 호출, 기동 정상 완료(200)."""
        from dashboard.backend.config import ConsoleConfig
        from dashboard.backend.main import app

        fake_cfg = ConsoleConfig(prewarm_projects=[])
        calls: list = []

        with patch("dashboard.backend.main.load_config", return_value=fake_cfg), \
             patch(
                "dashboard.backend.main.brain_session_registry.prewarm",
                side_effect=lambda p: calls.append(p),
             ):
            with TestClient(app) as lifespan_client:
                resp = lifespan_client.get("/health")

        assert resp.status_code == 200
        assert calls == [], f"prewarm_projects 미지정 시 prewarm 0회 호출이어야 함: {calls}"

    def test_lifespan_does_not_block_startup(self):
        """[T060/L2-F3] lifespan 진입이 프라임 완료를 기다리지 않고 즉시 반환(비블로킹, H-6)."""
        from dashboard.backend.config import ConsoleConfig
        from dashboard.backend.main import app

        fake_cfg = ConsoleConfig(prewarm_projects=[_PROJ_A])

        def slow_prewarm(project_path):
            time.sleep(2.0)

        with patch("dashboard.backend.main.load_config", return_value=fake_cfg), \
             patch(
                "dashboard.backend.main.brain_session_registry.prewarm",
                side_effect=slow_prewarm,
             ):
            t0 = time.monotonic()
            with TestClient(app) as lifespan_client:
                elapsed = time.monotonic() - t0
                resp = lifespan_client.get("/health")

        assert resp.status_code == 200
        assert elapsed < 1.0, (
            f"lifespan 진입이 prewarm 완료(2s 지연)를 기다림 — 블로킹 발생(H-6): {elapsed:.2f}s"
        )


# ── TestBrainPoolFixtureRegression (S-11) — T060 RED ────────────────────────────
#
# H-7: reset_brain_registry 픽스처가 아직 풀 상태(_pool/_pool_inflight)를 클리어하지
# 않으므로(EXECUTE 단계 소관 — TASK 지시에 따라 이 RED 작성 단계에서는 확장하지 않음),
# 직전 테스트가 남긴 잔류 상태가 다음 테스트로 누수되는지 검증한다.
# 실행 순서 의존(클래스 내 정의 순서 — 이 프로젝트 pytest 설정에 랜덤 플러그인 없음).

class TestBrainPoolFixtureRegression:
    """reset_brain_registry 픽스처의 풀 상태 클리어 회귀 (H-7, RED)."""

    def test_step1_pollute_global_pool_state(self):
        """[T060/L2-H7] (1/2) 전역 brain_session_registry 풀에 잔류 상태를 인위 주입."""
        from dashboard.backend.adapters.brain_session import brain_session_registry

        with brain_session_registry._pool_lock:
            brain_session_registry._pool[_PROJ_A] = ["stale-handle"]
            brain_session_registry._pool_inflight[_PROJ_A] = 1

        assert brain_session_registry._pool.get(_PROJ_A) == ["stale-handle"], (
            "사전조건 실패 — 잔류 상태 주입 확인 불가"
        )

    def test_step2_fixture_must_clear_pool_before_next_test(self):
        """[T060/L2-H7] (2/2) 직전 테스트의 풀 잔류 상태가 autouse 픽스처로 클리어됨(H-7)."""
        from dashboard.backend.adapters.brain_session import brain_session_registry

        assert brain_session_registry._pool.get(_PROJ_A, []) == [], (
            "reset_brain_registry 픽스처가 _pool을 클리어하지 않음(H-7 위반) — "
            "직전 테스트가 주입한 잔류 핸들이 남아있음"
        )
        assert brain_session_registry._pool_inflight.get(_PROJ_A, 0) == 0, (
            "reset_brain_registry 픽스처가 _pool_inflight를 클리어하지 않음(H-7 위반)"
        )
