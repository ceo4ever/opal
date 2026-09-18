"""
@header {
  "module": "test_e2e_api_executor",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "T09 — API executor 6연산 계약(CONTRACT.md §B.3), 실 HTTP 호출과 §A.11 요청/응답 증적, §A.4 actions.jsonl step_role 구분, C-API-2 retry 화이트리스트(제품 4xx/5xx 미은폐), C-API-3 run_id namespace fixture 한정 정리, §A.12 redaction 관문 통과를 검증한다.",
  "scenarios": ["S-10", "S-40"],
  "exports": [
    "TestExecutorOperationContract", "TestProbeIsEvidenceBased", "TestRealHttpAct",
    "TestRetryWhitelist", "TestEvidenceGate", "TestFixtureOwnership",
    "TestCandidateResolution", "TestScenarioAdapter"
  ]
}

이 스위트는 W-7 산출물(`lib/e2e/executors/`·`lib/e2e/scenario_adapter.py`)의 **공개
인터페이스**만 검사한다 — §B.3 연산의 JSON 입출력, 증적 관문이 디스크에 남긴 파일,
그리고 `e2e_contract`가 그 결과를 먹었을 때의 판정이다. 내부 헬퍼의 형태는 고정하지
않는다.

실 SUT(uvicorn/vite) 기동은 orchestrator 소유이고 이 스위트의 대상이 아니다. 여기서
포트를 여는 `http.server`는 **executor가 실제로 소켓을 여는지**를 관측하기 위한
계측기이며, executor 안에 응답을 합성하는 경로가 없다는 사실(C-API-1)은 별도 테스트가
직접 확인한다.
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

from lib import e2e_contract  # noqa: E402
from lib.e2e import evidence as e2e_evidence  # noqa: E402
from lib.e2e import executors as e2e_executors  # noqa: E402
from lib.e2e import scenario_adapter  # noqa: E402
from lib.e2e.executors import api as e2e_api  # noqa: E402


# ─── 계측용 실 HTTP 서버 ─────────────────────────────────────────────────────
class _Recorder(BaseHTTPRequestHandler):
    """라우팅 표대로 응답하고 받은 요청을 전부 기록한다."""

    routes: dict = {}
    received: list = []

    def _handle(self):
        type(self).received.append((self.command, self.path))
        status, payload = type(self).routes.get(self.path, (404, {"error": "not_found"}))
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Set-Cookie", "session=super-secret-value; Path=/")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = _handle
    do_POST = _handle
    do_DELETE = _handle

    def log_message(self, *_args):  # 테스트 출력 오염 방지
        return


class _Server:
    def __init__(self, routes):
        _Recorder.routes = dict(routes)
        _Recorder.received = []
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Recorder)
        self.port = self.httpd.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def received(self):
        return list(_Recorder.received)

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)


def _closed_port() -> int:
    """아무도 듣지 않는 포트 — transport 오류(ECONNREFUSED)를 실제로 일으킨다."""
    import socket

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _executor(server_url, **kwargs):
    return e2e_api.ApiExecutor(runtime_context={"backend_url": server_url}, **kwargs)


def _prepared(executor, server_url, run_id="e2e-20260914-001", **extra):
    return executor.dispatch(
        "prepare", dict({"run_id": run_id, "base_url": server_url, "target": "source-worktree"}, **extra)
    )["handle"]


# ─── §B.3 연산 계약 ──────────────────────────────────────────────────────────
class TestExecutorOperationContract(unittest.TestCase):
    """§B.3 표 — 연산 이름 집합과 필수 입력 집행."""

    def test_api_executor_exposes_exactly_the_six_contract_operations(self):
        self.assertEqual(
            e2e_api.ApiExecutor.operations,
            ("probe", "prepare", "act", "assert", "capture", "cleanup"),
        )

    def test_unknown_operation_is_rejected_without_touching_the_sut(self):
        executor = _executor("http://127.0.0.1:1")
        with self.assertRaises(e2e_executors.ExecutorError) as ctx:
            executor.dispatch("navigate", {})
        self.assertEqual(ctx.exception.detail_code, "executor_unknown_operation")

    def test_act_without_step_role_is_refused_before_any_request(self):
        """C-EXE-2 — §C.4 fidelity 집행의 입력이므로 기본값으로 얼버무리지 않는다."""
        server = _Server({"/x": (200, {"ok": True})})
        self.addCleanup(server.close)
        executor = _executor(server.url)
        handle = _prepared(executor, server.url)
        with self.assertRaises(e2e_executors.ExecutorError) as ctx:
            executor.dispatch("act", {"handle": handle, "action": {"method": "GET", "url": "/x"}})
        self.assertEqual(ctx.exception.detail_code, "executor_step_role_required")
        self.assertEqual(server.received, [], "요청이 나가서는 안 된다")

    def test_operations_require_the_handle_returned_by_prepare(self):
        executor = _executor("http://127.0.0.1:1")
        for operation, payload in (
            ("act", {"action": {"method": "GET", "url": "/", "step_role": "verify"}}),
            ("assert", {"assertion": {"id": "a1", "expected": 200}}),
            ("cleanup", {}),
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(e2e_executors.ExecutorError) as ctx:
                    executor.dispatch(operation, payload)
                self.assertEqual(ctx.exception.detail_code, "api_handle_required")

    def test_prepare_returns_the_three_contract_keys(self):
        server = _Server({})
        self.addCleanup(server.close)
        result = _executor(server.url).dispatch(
            "prepare", {"run_id": "e2e-20260914-002", "base_url": server.url}
        )
        self.assertEqual(sorted(result), ["handle", "owned", "setup_evidence"])


class TestProbeIsEvidenceBased(unittest.TestCase):
    """C-EXE-1 / §A.8 [MUST] — 가용성 근거는 probe 결과뿐이다."""

    def test_probe_without_a_base_url_is_unavailable_and_unprobed(self):
        probe = e2e_api.ApiExecutor(runtime_context={}).dispatch("probe", {})
        self.assertFalse(probe["available"])
        self.assertEqual(probe["unavailable_reason"], "api_base_url_absent")
        for key, item in probe["capabilities"].items():
            with self.subTest(capability=key):
                self.assertFalse(item["probed"])
                self.assertFalse(item["available"])

    def test_probe_against_a_live_health_surface_is_available(self):
        server = _Server({"/health": (200, {"status": "ok"})})
        self.addCleanup(server.close)
        probe = _executor(server.url).dispatch("probe", {})
        self.assertTrue(probe["available"])
        self.assertIsNone(probe["unavailable_reason"])
        self.assertEqual(("GET", "/health"), server.received[0])

    def test_probe_against_a_dead_port_is_unavailable(self):
        probe = _executor(f"http://127.0.0.1:{_closed_port()}").dispatch("probe", {})
        self.assertFalse(probe["available"])
        self.assertIn(probe["unavailable_reason"], e2e_api.TRANSPORT_ERROR_CODES)

    def test_normalization_never_promotes_an_unprobed_capability(self):
        normalized = e2e_executors.normalize_probe_result(
            {"available": True, "capabilities": {"request": {"available": True, "probed": False}}},
            executor="api",
            capability_keys=e2e_executors.API_CAPABILITY_KEYS,
        )
        self.assertFalse(normalized["capabilities"]["request"]["available"])


# ─── 실 호출 ─────────────────────────────────────────────────────────────────
class TestRealHttpAct(unittest.TestCase):
    """C-API-1 — `act`는 실제 소켓을 연다. 응답을 합성하는 경로가 없다."""

    def test_act_opens_a_real_socket_and_reports_the_product_status(self):
        server = _Server({"/api/projects": (201, {"id": "p-1", "state": "created"})})
        self.addCleanup(server.close)
        executor = _executor(server.url)
        handle = _prepared(executor, server.url, body_allowlist=["/api/projects"])
        result = executor.dispatch(
            "act",
            {
                "handle": handle,
                "step_id": "create-project",
                "action": {
                    "method": "POST",
                    "url": "/api/projects",
                    "body": {"name": "x"},
                    "timeout_ms": 5000,
                    "step_role": "verify",
                },
            },
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], 201)
        self.assertIn(("POST", "/api/projects"), server.received)
        self.assertEqual(result["response_ref"], f"{e2e_api.API_RESPONSES_PATH}#1")

    def test_the_only_transport_is_the_injected_opener(self):
        """모의 응답 경로 부재의 관측 지점 — 전송이 막히면 성공이 불가능하다.

        transport를 막았을 때 executor가 `ok=true`와 status를 만들어낸다면 어딘가에
        응답을 합성하는 분기가 있다는 뜻이다(C-API-1 위반).
        """
        calls = []

        def _refuse(**kwargs):
            calls.append(kwargs["url"])
            raise RuntimeError("transport is unavailable")

        executor = e2e_api.ApiExecutor(
            runtime_context={"backend_url": "http://127.0.0.1:1"}, opener=_refuse
        )
        handle = _prepared(executor, "http://127.0.0.1:1")
        result = executor.dispatch(
            "act",
            {"handle": handle, "action": {"method": "GET", "url": "/x", "step_role": "verify"}},
        )
        self.assertFalse(result["ok"])
        self.assertIsNone(result["status"])
        self.assertEqual(result["error_code"], "api_request_failed")
        self.assertEqual(len(calls), 1, "transport 아닌 오류는 재시도 대상이 아니다")

    def test_the_default_transport_is_the_real_socket_opener(self):
        self.assertIs(e2e_api.ApiExecutor(runtime_context={})._opener, e2e_api._urlopen)

    def test_observe_url_records_the_follow_up_state_as_its_own_action(self):
        server = _Server({
            "/api/tasks": (202, {"accepted": True}),
            "/api/tasks/1": (200, {"state": "done"}),
        })
        self.addCleanup(server.close)
        executor = _executor(server.url)
        handle = _prepared(executor, server.url, body_allowlist=["/api/tasks"])
        result = executor.dispatch(
            "act",
            {
                "handle": handle,
                "step_id": "run-task",
                "action": {
                    "method": "POST", "url": "/api/tasks", "step_role": "verify",
                    "observe_url": "/api/tasks/1",
                },
            },
        )
        self.assertEqual(result["observed_state"], {"state": "done"})
        self.assertEqual(len(executor.action_log), 2, "후속 상태 확인도 하나의 행동이다")

    def test_state_verifier_asserts_against_a_follow_up_call(self):
        server = _Server({"/api/state": (200, {"phase": "ready"})})
        self.addCleanup(server.close)
        executor = _executor(server.url)
        handle = _prepared(executor, server.url)
        outcome = executor.dispatch(
            "assert",
            {
                "handle": handle,
                "assertion": {"id": "S-10-a1", "verifier": "state", "url": "/api/state",
                              "field": "phase", "expected": "ready"},
            },
        )
        self.assertEqual(outcome["actual"], "ready")
        self.assertTrue(outcome["passed"])

    def test_assertion_result_always_carries_expected_and_actual_keys(self):
        """§A.5 [MUST] — 값이 null이어도 키는 존재해야 한다."""
        server = _Server({})
        self.addCleanup(server.close)
        executor = _executor(server.url)
        handle = _prepared(executor, server.url)
        outcome = executor.dispatch(
            "assert", {"handle": handle, "assertion": {"id": "a1", "expected": "x"}}
        )
        self.assertIn("expected", outcome)
        self.assertIn("actual", outcome)
        self.assertFalse(outcome["passed"])
        self.assertEqual(outcome["executor"], "api")


class TestRetryWhitelist(unittest.TestCase):
    """C-API-2 [MUST] — retry는 transport 오류 한정. 제품 4xx/5xx는 숨기지 않는다."""

    def test_the_whitelist_holds_only_the_four_contract_codes(self):
        self.assertEqual(
            set(e2e_api.TRANSPORT_ERROR_CODES),
            {"ECONNREFUSED", "ECONNRESET", "EDNS", "ETIMEDOUT"},
        )

    def test_http_error_is_never_classified_as_a_transport_error(self):
        import urllib.error

        for code in (400, 401, 404, 409, 500, 503):
            with self.subTest(status=code):
                exc = urllib.error.HTTPError("http://x", code, "boom", None, None)
                self.assertIsNone(e2e_api.classify_transport_error(exc))

    def test_product_4xx_and_5xx_are_returned_once_and_never_retried(self):
        for status in (404, 409, 500):
            with self.subTest(status=status):
                server = _Server({"/fail": (status, {"detail": "product failure"})})
                self.addCleanup(server.close)
                executor = _executor(server.url)
                handle = _prepared(executor, server.url)
                result = executor.dispatch(
                    "act",
                    {"handle": handle, "step_id": "s",
                     "action": {"method": "GET", "url": "/fail", "step_role": "verify"}},
                )
                self.assertTrue(result["ok"], "응답을 받았으므로 전송은 성공이다")
                self.assertEqual(result["status"], status)
                self.assertEqual(executor.transport_attempts(), [])
                self.assertEqual(
                    len([item for item in server.received if item[1] == "/fail"]), 1,
                    "제품 실패를 재시도로 덮지 않는다",
                )

    def test_transport_failure_retries_up_to_the_contract_ceiling_then_errors(self):
        dead = f"http://127.0.0.1:{_closed_port()}"
        executor = e2e_api.ApiExecutor(
            runtime_context={"backend_url": dead}, max_attempts=e2e_api.DEFAULT_MAX_ATTEMPTS
        )
        handle = _prepared(executor, dead)
        result = executor.dispatch(
            "act",
            {"handle": handle, "step_id": "s",
             "action": {"method": "GET", "url": "/x", "step_role": "verify"}},
        )
        self.assertFalse(result["ok"])
        self.assertIn(result["error_code"], e2e_api.TRANSPORT_ERROR_CODES)
        self.assertEqual(len(executor.transport_attempts()), e2e_api.DEFAULT_MAX_ATTEMPTS)
        self.assertEqual(e2e_api.DEFAULT_MAX_ATTEMPTS, 3)

    def test_failed_action_is_recorded_as_error_not_omitted(self):
        dead = f"http://127.0.0.1:{_closed_port()}"
        executor = e2e_api.ApiExecutor(runtime_context={"backend_url": dead}, max_attempts=1)
        handle = _prepared(executor, dead)
        executor.dispatch(
            "act",
            {"handle": handle, "step_id": "s",
             "action": {"method": "GET", "url": "/x", "step_role": "verify"}},
        )
        row = executor.action_log.rows()[0]
        self.assertEqual(row["result"], "error")
        self.assertIsNone(row["response"]["status"])


# ─── 증적 ────────────────────────────────────────────────────────────────────
class TestEvidenceGate(unittest.TestCase):
    """§A.11·§A.12 — 요청/응답 증적은 evidence.py 관문을 통과해서만 디스크에 남는다."""

    def _capture(self, routes, **act):
        server = _Server(routes)
        self.addCleanup(server.close)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        writer = e2e_evidence.EvidenceWriter(tmp.name, "e2e-20260914-010")
        executor = e2e_api.ApiExecutor(runtime_context={"backend_url": server.url}, writer=writer)
        handle = _prepared(executor, server.url, body_allowlist=act.pop("allowlist", []))
        executor.dispatch("act", {"handle": handle, "step_id": "s", "action": act})
        artifacts = executor.dispatch("capture", {"handle": handle, "evidence_spec": []})
        return pathlib.Path(tmp.name), executor, artifacts

    def test_capture_writes_the_two_contract_a11_files_plus_the_action_log(self):
        root, _, artifacts = self._capture(
            {"/api/ping": (200, {"pong": True})},
            method="GET", url="/api/ping", step_role="verify",
        )
        self.assertEqual(sorted(artifacts["artifacts"]), ["action_log", "api_requests", "api_responses"])
        for rel in (e2e_api.API_REQUESTS_PATH, e2e_api.API_RESPONSES_PATH, "actions.jsonl"):
            with self.subTest(artifact=rel):
                self.assertTrue((root / rel).is_file(), rel)

    def test_secret_headers_never_reach_the_artifact_in_clear_text(self):
        """TASK.md C-6 / §A.12 — Authorization·Cookie·Set-Cookie는 마스킹본만 남는다."""
        root, _, _ = self._capture(
            {"/api/secure": (200, {"ok": True})},
            method="GET", url="/api/secure?token=raw-query-secret", step_role="verify",
            headers={"Authorization": "Bearer raw-header-secret", "Cookie": "sid=raw-cookie"},
        )
        blob = "\n".join(
            (root / rel).read_text(encoding="utf-8")
            for rel in (e2e_api.API_REQUESTS_PATH, e2e_api.API_RESPONSES_PATH, "actions.jsonl")
        )
        for secret in ("raw-header-secret", "raw-cookie", "raw-query-secret", "super-secret-value"):
            with self.subTest(secret=secret):
                self.assertNotIn(secret, blob)
        self.assertIn("Authorization", blob, "키 이름은 남고 값만 마스킹된다")

    def test_action_rows_carry_the_contract_a4_keys_and_the_step_role(self):
        _, executor, _ = self._capture(
            {"/api/ping": (200, {"pong": True})},
            method="GET", url="/api/ping", step_role="setup",
        )
        row = executor.action_log.rows()[0]
        for key in ("seq", "at", "step_id", "executor", "step_role", "action", "wait_kind",
                    "request", "response", "result", "error_code", "current_url", "elapsed_ms"):
            self.assertIn(key, row, key)
        self.assertEqual(row["step_role"], "setup")
        self.assertEqual(row["executor"], "api")
        self.assertIsNotNone(row["request"])
        self.assertIsNotNone(row["response"])

    def test_api_rows_cross_reference_the_action_log_by_seq(self):
        """§A.11 — requests/responses 1행은 actions.jsonl의 같은 seq를 가리킨다."""
        _, executor, _ = self._capture(
            {"/api/ping": (200, {"pong": True})},
            method="GET", url="/api/ping", step_role="verify",
        )
        action_seqs = [row["seq"] for row in executor.action_log.rows()]
        self.assertEqual([item["seq"] for item in executor.request_records()], action_seqs)
        self.assertEqual([item["seq"] for item in executor.response_records()], action_seqs)

    def test_body_is_not_collected_unless_the_endpoint_is_allowlisted(self):
        """§A.11 — body 기본 미수집. allowlist endpoint만 수집한다."""
        _, executor, _ = self._capture(
            {"/api/private": (200, {"payload": "not-collected"})},
            method="GET", url="/api/private", step_role="verify",
        )
        self.assertIsNone(executor.response_records()[0]["body"])

    def test_capture_without_an_evidence_writer_is_a_contract_error(self):
        """§C.2 [MUST] — executor는 파일을 직접 쓰지 않는다."""
        server = _Server({})
        self.addCleanup(server.close)
        executor = _executor(server.url)
        handle = _prepared(executor, server.url)
        with self.assertRaises(e2e_executors.ExecutorError) as ctx:
            executor.dispatch("capture", {"handle": handle, "evidence_spec": []})
        self.assertEqual(ctx.exception.detail_code, "api_evidence_writer_absent")

    def test_api_executor_module_has_no_direct_file_write_path(self):
        """§C.2 [MUST] — redaction 우회 경로를 구조적으로 남기지 않는다."""
        source = (_TOOL_DIR / "lib" / "e2e" / "executors" / "api.py").read_text(encoding="utf-8")
        for forbidden in ("write_text", "write_bytes", "os.replace", "mkdir(", "NamedTemporary"):
            with self.subTest(call=forbidden):
                self.assertNotIn(forbidden, source)

    def test_api_executor_module_has_no_os_branch(self):
        """§C.2 [MUST] / TD-16 — OS 분기는 lib/e2e/process.py 한 곳뿐이다."""
        source = (_TOOL_DIR / "lib" / "e2e" / "executors" / "api.py").read_text(encoding="utf-8")
        for forbidden in ("sys.platform", "os.name", "platform.system"):
            with self.subTest(branch=forbidden):
                self.assertNotIn(forbidden, source)


# ─── 소유 자원 ───────────────────────────────────────────────────────────────
class TestFixtureOwnership(unittest.TestCase):
    """C-API-3 / §C.3 [MUST] — run_id namespace의 자기 fixture만 정리한다."""

    def _handle_with_fixtures(self, server):
        executor = _executor(server.url)
        handle = executor.dispatch(
            "prepare",
            {
                "run_id": "e2e-20260914-020",
                "base_url": server.url,
                "fixtures": [
                    {"fixture_id": "mine", "endpoint": "/api/fixtures/mine"},
                    {"fixture_id": "theirs", "namespace": "e2e-19990101-999",
                     "endpoint": "/api/fixtures/theirs"},
                    {"fixture_id": "user", "endpoint": "/api/fixtures/user", "user_owned": True},
                ],
            },
        )["handle"]
        return executor, handle

    def test_owned_ledger_lists_only_this_runs_namespace(self):
        server = _Server({})
        self.addCleanup(server.close)
        executor = _executor(server.url)
        owned = executor.dispatch(
            "prepare",
            {
                "run_id": "e2e-20260914-021", "base_url": server.url,
                "fixtures": [
                    {"fixture_id": "mine", "endpoint": "/a"},
                    {"fixture_id": "user", "endpoint": "/b", "user_owned": True},
                ],
            },
        )["owned"]
        self.assertEqual([item["fixture_id"] for item in owned], ["mine"])
        self.assertEqual(owned[0]["namespace"], "e2e-20260914-021")

    def test_cleanup_calls_only_the_owned_fixture_endpoint(self):
        server = _Server({"/api/fixtures/mine": (204, {})})
        self.addCleanup(server.close)
        executor, handle = self._handle_with_fixtures(server)
        report = executor.dispatch("cleanup", {"handle": handle})
        self.assertEqual([item["id"] for item in report["released"]], ["mine"])
        self.assertEqual(
            sorted(item["id"] for item in report["skipped_user_owned"]), ["theirs", "user"]
        )
        touched = {path for _method, path in server.received}
        self.assertEqual(touched, {"/api/fixtures/mine"})
        self.assertNotIn("/api/fixtures/theirs", touched)
        self.assertNotIn("/api/fixtures/user", touched)

    def test_cleanup_reports_a_leak_instead_of_claiming_success(self):
        server = _Server({})  # mine → 404
        self.addCleanup(server.close)
        executor, handle = self._handle_with_fixtures(server)
        report = executor.dispatch("cleanup", {"handle": handle})
        self.assertEqual(report["released"], [])
        self.assertEqual([item["id"] for item in report["leaked"]], ["mine"])

    def test_cleanup_actions_are_recorded_with_the_cleanup_step_role(self):
        """§C.4 / TD-17 — setup·cleanup API와 검증 대상 API가 구분 기록된다."""
        server = _Server({"/api/fixtures/mine": (204, {})})
        self.addCleanup(server.close)
        executor, handle = self._handle_with_fixtures(server)
        executor.dispatch("cleanup", {"handle": handle})
        self.assertEqual(len(executor.action_log.rows_with_role("cleanup")), 1)
        self.assertEqual(executor.action_log.rows_with_role("verify"), [])


# ─── 후보 해석 ───────────────────────────────────────────────────────────────
class TestCandidateResolution(unittest.TestCase):
    """§A.1.2 — api·human 후보가 candidates[]에 전건 기록된다."""

    def tearDown(self):
        for name in ("api", "human"):
            e2e_executors.unregister_executor(name)

    def test_unregistered_executor_is_provider_unavailable_not_excluded(self):
        candidates, probes = e2e_executors.resolve_executor_candidates(["api"], registry={})
        self.assertEqual(candidates[0]["outcome"], "provider_unavailable")
        self.assertEqual(candidates[0]["reason"], "no_registered_executor")
        self.assertIsNone(candidates[0]["excluded_by"])
        self.assertEqual(probes, [], "실행하지 않은 후보의 probe는 없다")

    def test_registered_and_available_executor_is_selected(self):
        server = _Server({"/health": (200, {"status": "ok"})})
        self.addCleanup(server.close)
        e2e_api.register()
        candidates, probes = e2e_executors.resolve_executor_candidates(
            ["api"], runtime_context={"backend_url": server.url}
        )
        self.assertEqual(candidates[0]["outcome"], "selected")
        self.assertEqual(candidates[0]["type"], "api")
        self.assertEqual(len(probes), 1)
        self.assertTrue(probes[0]["available"])

    def test_unavailable_executor_is_not_selected(self):
        e2e_api.register()
        candidates, _ = e2e_executors.resolve_executor_candidates(
            ["api"], runtime_context={"backend_url": f"http://127.0.0.1:{_closed_port()}"}
        )
        self.assertEqual(candidates[0]["outcome"], "provider_unavailable")

    def test_order_continues_after_browser_candidates(self):
        candidates, _ = e2e_executors.resolve_executor_candidates(
            ["api", "human"], registry={}, start_order=4
        )
        self.assertEqual([item["order"] for item in candidates], [5, 6])

    def test_candidate_elements_carry_every_contract_a12_field(self):
        candidates, _ = e2e_executors.resolve_executor_candidates(["api"], registry={})
        for key in ("order", "type", "driver", "session_mode", "binary_path",
                    "resolution_source", "version", "outcome", "excluded_by", "reason"):
            self.assertIn(key, candidates[0], key)

    def test_registry_rejects_a_type_outside_the_contract_enum(self):
        with self.assertRaises(e2e_executors.ExecutorError) as ctx:
            e2e_executors.register_executor("database", lambda **_: None)
        self.assertEqual(ctx.exception.detail_code, "executor_type_unknown")
        self.assertEqual(e2e_contract.EXECUTOR_TYPES, ("browser", "api", "human"))


# ─── 시나리오 어댑터 ─────────────────────────────────────────────────────────
class TestScenarioAdapter(unittest.TestCase):
    """시나리오 spec → executor 계획 → e2e_contract 판정 입력의 형태 계약."""

    SCENARIO = {
        "id": "S-10",
        "profile": "api",
        "surface_kind": "api",
        "actors": ["service"],
        "required_fidelity": "real-http",
        "steps": [
            {"id": "seed", "executor": "api", "step_role": "setup", "method": "POST", "url": "/seed"},
            {"id": "check", "executor": "api", "method": "GET", "url": "/api/state"},
            {"id": "drop", "executor": "api", "step_role": "cleanup", "method": "DELETE", "url": "/seed"},
        ],
        "assertions": [{"id": "S-10-a1", "expected": 200}],
        "required_evidence": ["metadata", "action_log"],
    }

    def test_step_role_defaults_to_verify_and_keeps_declared_roles(self):
        plan = scenario_adapter.build_execution_plan(self.SCENARIO)
        self.assertEqual([step.step_role for step in plan], ["setup", "verify", "cleanup"])
        self.assertEqual(plan[1].as_action()["step_role"], "verify")

    def test_verify_steps_are_separable_from_setup_and_cleanup(self):
        plan = scenario_adapter.build_execution_plan(self.SCENARIO)
        self.assertEqual(scenario_adapter.verify_step_ids_by_executor(plan), {"api": ["check"]})

    def test_a_step_executor_outside_the_enum_is_refused(self):
        with self.assertRaises(e2e_executors.ExecutorError) as ctx:
            scenario_adapter.build_execution_plan(
                {"steps": [{"id": "x", "executor": "database"}]}
            )
        self.assertEqual(ctx.exception.detail_code, "scenario_step_executor_invalid")

    def test_observed_executors_reflect_execution_not_declaration(self):
        plan = scenario_adapter.build_execution_plan(self.SCENARIO)
        self.assertEqual(scenario_adapter.observed_executors(plan, []), [])
        self.assertEqual(scenario_adapter.observed_executors(plan, ["check"]), ["api"])

    def test_required_executor_types_come_from_the_contract_matrix(self):
        self.assertEqual(scenario_adapter.required_executor_types(self.SCENARIO), ("api",))
        self.assertEqual(
            scenario_adapter.required_executor_types({"profile": "collaborative"}), ("human",)
        )

    def test_verdict_input_passes_the_contract_gate_when_assertions_match(self):
        results = [{"id": "S-10-a1", "verifier": "response", "executor": "api",
                    "expected": 200, "actual": 200, "passed": True}]
        verdict_input = scenario_adapter.build_verdict_input(
            self.SCENARIO, status="pass", run_id="e2e-20260914-030",
            assertion_results=results, observed_executor_types=["api"],
            observed_evidence=["metadata", "action_log"],
        )
        verdict = e2e_contract.build_verdict(verdict_input)
        self.assertTrue(verdict["ok"])
        self.assertEqual(verdict["status"], "pass")

    def test_verdict_input_is_rejected_when_the_actual_diverges(self):
        results = [{"id": "S-10-a1", "verifier": "response", "executor": "api",
                    "expected": 200, "actual": 500, "passed": False}]
        verdict = e2e_contract.build_verdict(
            scenario_adapter.build_verdict_input(
                self.SCENARIO, status="pass", run_id="e2e-20260914-031",
                assertion_results=results, observed_executor_types=["api"],
                observed_evidence=["metadata", "action_log"],
            )
        )
        self.assertFalse(verdict["ok"])
        self.assertEqual(verdict["error"], "assertion_failed")

    def test_missing_evidence_blocks_pass(self):
        results = [{"id": "S-10-a1", "expected": 200, "actual": 200, "passed": True}]
        verdict = e2e_contract.build_verdict(
            scenario_adapter.build_verdict_input(
                self.SCENARIO, status="pass", run_id="e2e-20260914-032",
                assertion_results=results, observed_executor_types=["api"],
                observed_evidence=["metadata"],
            )
        )
        self.assertEqual(verdict["error"], "evidence_missing")

    def test_assertion_summary_counts_missing_results(self):
        self.assertEqual(
            scenario_adapter.assertion_summary(self.SCENARIO, []),
            {"passed": 0, "failed": 0, "missing": 1},
        )


if __name__ == "__main__":
    unittest.main()
