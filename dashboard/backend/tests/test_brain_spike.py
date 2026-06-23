"""
@header {
  "module": "tests.test_brain_spike",
  "layer": "test",
  "domain": "console",
  "description": "Phase 1 스파이크 L1 단위 테스트 (Phase 2 + B2 대화별 session_id 계약 반영). S-1(출력 파싱 정상), S-2(is_error/비JSON → RuntimeError → 잡 status=error 흡수, 비동기 계약), S-3(커맨드 배열 금지 플래그 부재 + shell=False). Phase 2: //opbr query --read-only(DECISION#23), B2: prime_and_ask 시그니처 session_id+cold 필수. [MUST] 실 claude 서브프로세스 호출 0회 — subprocess.run 전부 unittest.mock.patch 격리(H-8). 구독 토큰 소모 없음.",
  "exports": [
    "test_parse_success",
    "test_parse_error_is_error",
    "test_parse_error_non_json",
    "test_parse_error_surfaces_as_job_error",
    "test_cmd_flags"
  ],
  "depends": ["adapters.opbr_adapter", "routers.brain", "main"]
}
"""
from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ── fixture ──────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    from dashboard.backend.main import app
    return TestClient(app)


def _mock_proc(stdout: str, returncode: int = 0) -> MagicMock:
    """subprocess.run 반환값 mock 헬퍼."""
    proc = MagicMock()
    proc.stdout = stdout
    proc.stderr = ""
    proc.returncode = returncode
    return proc


# 성공형 고정 출력 (§2.1 TEST-SCENARIO)
_SUCCESS_OUTPUT = json.dumps({
    "type": "result",
    "subtype": "success",
    "is_error": False,
    "result": "답변텍스트",
    "session_id": "sid-1",
})

# is_error=true 고정 출력
_ERROR_OUTPUT = json.dumps({
    "type": "result",
    "subtype": "error_during_execution",
    "is_error": True,
})

# 비JSON 고정 출력
_NON_JSON_OUTPUT = "not-json-at-all"


# ── S-1: 출력 파싱 정상 ───────────────────────────────────────────────────────────

class TestParseSuccess:
    """S-1: opbr_adapter 출력 파싱 — 정상 경로 (H-6, H-8)."""

    def test_parse_success(self):
        """성공형 고정 출력 → answer='답변텍스트', session_id='sid-1'. 실 claude 0회."""
        with patch("subprocess.run", return_value=_mock_proc(_SUCCESS_OUTPUT)) as mock_run, \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask

            result = prime_and_ask(
                question="테스트 질문",
                project_path="/some/path",
                session_id="sid-1",
                cold=True,
            )

        assert result["answer"] == "답변텍스트"
        assert result["session_id"] == "sid-1"
        assert "elapsed_s" in result
        assert isinstance(result["elapsed_s"], float)
        # 실 claude 서브프로세스 호출 0회 보증 (mock이 대체함)
        mock_run.assert_called_once()

    def test_parse_success_citations_empty_in_spike(self):
        """스파이크 최소본 — citations는 빈 리스트."""
        with patch("subprocess.run", return_value=_mock_proc(_SUCCESS_OUTPUT)), \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask

            result = prime_and_ask(
                question="테스트",
                project_path="/path",
                session_id="spike-sid",
                cold=True,
            )

        assert result["citations"] == []


# ── S-2: 출력 파싱 실패 처리 → 예외 → 잡 status=error 흡수 ──────────────────────────

class TestParseError:
    """S-2: prime_and_ask 실패 경로 — is_error/비JSON → RuntimeError → 잡 status=error 흡수 (비동기, H-6/H-8)."""

    def test_parse_error_is_error_raises(self):
        """is_error=true 고정 출력 → RuntimeError 발생."""
        with patch("subprocess.run", return_value=_mock_proc(_ERROR_OUTPUT)), \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask

            with pytest.raises(RuntimeError, match="is_error=true"):
                prime_and_ask(
                    question="질문",
                    project_path="/path",
                    session_id="spike-sid",
                    cold=True,
                )

    def test_parse_error_non_json_raises(self):
        """비JSON 출력 → RuntimeError 발생."""
        with patch("subprocess.run", return_value=_mock_proc(_NON_JSON_OUTPUT)), \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask

            with pytest.raises(RuntimeError):
                prime_and_ask(
                    question="질문",
                    project_path="/path",
                    session_id="spike-sid",
                    cold=True,
                )

    def test_parse_error_surfaces_as_job_error(self, client):
        """is_error=true mock → POST /api/brain/query 200+job_id, 잡 status=error로 흡수 (비동기 계약)."""
        from unittest.mock import patch as _patch
        _FAKE_PATH = "/fake/spike/project"
        _FAKE_SID = "ffffffff-0001-0001-0001-000000000001"

        class _FakeProj:
            path = _FAKE_PATH
            is_opal = True

        with _patch("dashboard.backend.routers.brain.scan_projects", return_value=[_FakeProj()]), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                side_effect=RuntimeError("is_error=true from claude"),
             ):
            resp = client.post(
                "/api/brain/query",
                json={"question": "테스트", "project": _FAKE_PATH, "session_id": _FAKE_SID},
            )
            assert resp.status_code == 200, f"query가 200 아님: {resp.json()}"
            job_id = resp.json()["job_id"]

            # 백그라운드 RuntimeError가 잡 status=error로 흡수됨을 결정론적 폴링으로 확인
            deadline = time.monotonic() + 2.0
            job_data = None
            while time.monotonic() < deadline:
                rj = client.get(
                    f"/api/brain/job/{job_id}?project={_FAKE_PATH}&session_id={_FAKE_SID}"
                )
                if rj.status_code == 200 and rj.json().get("status") == "error":
                    job_data = rj.json()
                    break
                time.sleep(0.02)

        assert job_data is not None, "잡이 error로 전이되지 않음"
        assert job_data["status"] == "error"
        assert "is_error=true" in job_data.get("error_msg", "")

    def test_parse_non_json_surfaces_as_job_error(self, client):
        """비JSON mock → POST /api/brain/query 200+job_id, 잡 status=error로 흡수 (비동기 계약)."""
        from unittest.mock import patch as _patch
        _FAKE_PATH = "/fake/spike/project"
        _FAKE_SID = "ffffffff-0002-0002-0002-000000000002"

        class _FakeProj:
            path = _FAKE_PATH
            is_opal = True

        with _patch("dashboard.backend.routers.brain.scan_projects", return_value=[_FakeProj()]), \
             patch(
                "dashboard.backend.adapters.brain_session.opbr_adapter.prime_and_ask",
                side_effect=RuntimeError("non-JSON output from claude"),
             ):
            resp = client.post(
                "/api/brain/query",
                json={"question": "테스트", "project": _FAKE_PATH, "session_id": _FAKE_SID},
            )
            assert resp.status_code == 200, f"query가 200 아님: {resp.json()}"
            job_id = resp.json()["job_id"]

            deadline = time.monotonic() + 2.0
            job_data = None
            while time.monotonic() < deadline:
                rj = client.get(
                    f"/api/brain/job/{job_id}?project={_FAKE_PATH}&session_id={_FAKE_SID}"
                )
                if rj.status_code == 200 and rj.json().get("status") == "error":
                    job_data = rj.json()
                    break
                time.sleep(0.02)

        assert job_data is not None, "잡이 error로 전이되지 않음"
        assert job_data["status"] == "error"
        assert "non-JSON output from claude" in job_data.get("error_msg", "")


# ── S-3: 커맨드 배열 — 구독 구동·금지 플래그 부재 ─────────────────────────────────

class TestCmdFlags:
    """S-3: prime_and_ask 커맨드 배열 캡처 — 금지 플래그 부재·필수 플래그 존재 (H-7, H-8)."""

    def _capture_cmd(self, session_id: str = "spike-sid-cold", cold: bool = True) -> list[str]:
        """subprocess.run을 patch하여 호출된 커맨드 배열 캡처.

        B2 시그니처: session_id + cold 모두 필수.
        """
        with patch("subprocess.run", return_value=_mock_proc(_SUCCESS_OUTPUT)) as mock_run:
            from dashboard.backend.adapters import opbr_adapter

            import importlib
            importlib.reload(opbr_adapter)

            with patch("subprocess.run", return_value=_mock_proc(_SUCCESS_OUTPUT)) as mock_run2, \
                 patch("os.path.isdir", return_value=True):
                opbr_adapter.prime_and_ask(
                    question="테스트 질문",
                    project_path="/path",
                    session_id=session_id,
                    cold=cold,
                )

            call_args = mock_run2.call_args
        return call_args[0][0]  # positional first arg = cmd list

    def test_opbr_query_read_only_in_cmd(self):
        """커맨드에 '//opbr query --read-only' 포함 확인 (Phase 2 DECISION#23 — ask→query 변경)."""
        cmd = self._capture_cmd()
        cmd_str = " ".join(cmd)
        assert "//opbr query --read-only" in cmd_str, (
            f"//opbr query --read-only not found in: {cmd}. "
            f"Note: Phase 2 hardening replaced //opbr ask with //opbr query --read-only (DECISION#23)"
        )

    def test_output_format_json_in_cmd(self):
        """커맨드에 --output-format json 포함 확인."""
        cmd = self._capture_cmd()
        assert "--output-format" in cmd, f"--output-format missing in: {cmd}"
        idx = cmd.index("--output-format")
        assert cmd[idx + 1] == "json", f"Expected 'json' after --output-format, got: {cmd[idx + 1]}"

    def test_no_safe_mode_flag(self):
        """[MUST] 커맨드에 --safe-mode 부재 (H-7 — opbr 미로드 방지)."""
        cmd = self._capture_cmd()
        assert "--safe-mode" not in cmd, f"--safe-mode MUST NOT be in cmd: {cmd}"

    def test_no_bare_flag(self):
        """[MUST] 커맨드에 --bare 부재 (H-7 — keychain 우회 방지)."""
        cmd = self._capture_cmd()
        assert "--bare" not in cmd, f"--bare MUST NOT be in cmd: {cmd}"

    def test_shell_false(self):
        """[MUST] subprocess.run이 shell=False로 호출됨 (H-13 — 셸 인젝션 방지)."""
        with patch("subprocess.run", return_value=_mock_proc(_SUCCESS_OUTPUT)) as mock_run, \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            prime_and_ask(
                question="테스트",
                project_path="/path",
                session_id="spike-sid",
                cold=True,
            )

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("shell") is False, (
            f"subprocess.run must be called with shell=False, got shell={call_kwargs.get('shell')}"
        )

    def test_cold_session_uses_session_id_flag(self):
        """콜드(cold=True): --session-id 플래그 사용, --resume 미사용."""
        cmd = self._capture_cmd(session_id="cold-sid", cold=True)
        assert "--session-id" in cmd, f"--session-id missing for cold=True: {cmd}"
        assert "--resume" not in cmd, f"--resume must not appear for cold=True: {cmd}"

    def test_warm_session_uses_resume_flag(self):
        """웜(cold=False): --resume 플래그 사용, --session-id 미사용."""
        cmd = self._capture_cmd(session_id="warm-sid", cold=False)
        assert "--resume" in cmd, f"--resume missing for cold=False: {cmd}"
        assert "--session-id" not in cmd, f"--session-id must not appear for cold=False: {cmd}"

    def test_question_in_prompt(self):
        """커맨드 배열에 질문 텍스트가 포함됨 (//opbr ask 인자로 전달)."""
        expected_question = "테스트 질문"
        cmd = self._capture_cmd(session_id="spike-sid", cold=True)
        assert "-p" in cmd, f"-p flag missing in cmd: {cmd}"
        p_idx = cmd.index("-p")
        prompt_arg = cmd[p_idx + 1]
        assert expected_question in prompt_arg, (
            f"Question '{expected_question}' not found in prompt arg: {prompt_arg!r}"
        )

    def test_readonly_guard_in_prompt(self):
        """[MUST] 읽기전용 가드가 커맨드에 포함됨 (H-1).
        Phase 2: --read-only 플래그가 opbr 계약으로 가드(접미사 제거, DECISION#23).
        """
        with patch("subprocess.run", return_value=_mock_proc(_SUCCESS_OUTPUT)) as mock_run, \
             patch("os.path.isdir", return_value=True):
            from dashboard.backend.adapters.opbr_adapter import prime_and_ask
            prime_and_ask(
                question="테스트",
                project_path="/path",
                session_id="spike-sid",
                cold=True,
            )

        cmd = mock_run.call_args[0][0]
        assert "-p" in cmd
        p_idx = cmd.index("-p")
        prompt_arg = cmd[p_idx + 1]
        assert "--read-only" in prompt_arg, (
            f"--read-only contract not found in prompt: {prompt_arg!r}. "
            f"Phase 2 uses opbr --read-only contract instead of prompt suffix."
        )


# ── GET /api/brain/auth 경량 체크 ────────────────────────────────────────────────

class TestBrainAuth:
    """GET /api/brain/auth — shutil.which mock으로 설치/미설치 분기 (스파이크 보조)."""

    def test_auth_cli_available(self, client):
        """claude CLI 설치됨 → authenticated=true, cli_available=true."""
        with patch("shutil.which", return_value="/usr/local/bin/claude"):
            resp = client.get("/api/brain/auth")
        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is True
        assert data["cli_available"] is True

    def test_auth_cli_not_available(self, client):
        """claude CLI 미설치 → authenticated=false, cli_available=false, message 비어있지 않음."""
        with patch("shutil.which", return_value=None):
            resp = client.get("/api/brain/auth")
        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is False
        assert data["cli_available"] is False
        assert len(data["message"]) > 0, "message must not be empty when cli not available"

    def test_auth_no_real_claude_call(self, client):
        """[MUST] auth 엔드포인트가 실 claude -p 서브프로세스 호출 0회 (H-8)."""
        with patch("subprocess.run") as mock_run, \
             patch("shutil.which", return_value="/usr/local/bin/claude"):
            resp = client.get("/api/brain/auth")
        assert resp.status_code == 200
        mock_run.assert_not_called(), "auth endpoint must NOT call subprocess.run (real claude)"
