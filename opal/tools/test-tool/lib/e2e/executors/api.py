"""
@header {
  "module": "api",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T09 API executor — CONTRACT.md §B.3 probe·prepare·act·assert·capture·cleanup 6연산을 실제 임대 SUT의 공개 HTTP endpoint에 대해 수행한다(C-API-1, mock server 대체 금지). 요청·응답 증적은 §A.11 api/requests.jsonl·api/responses.jsonl과 §A.4 actions.jsonl로 남기고 전부 evidence.py redaction 관문을 통과한다(§A.12). retry는 C-API-2의 transport 오류 화이트리스트에만 적용하고 제품 4xx/5xx를 숨기지 않는다. fixture는 run_id namespace 소유분만 정리한다(C-API-3·§C.3).",
  "exports": [
    "ApiExecutor", "ApiHandle", "TRANSPORT_ERROR_CODES", "DEFAULT_MAX_ATTEMPTS",
    "API_REQUESTS_PATH", "API_RESPONSES_PATH", "classify_transport_error", "register"
  ]
}

lib.e2e.executors.api — 이 모듈은 파일을 직접 쓰지 않는다. 모든 증적은 생성자로 받은
`EvidenceWriter`를 통해서만 발행한다(§C.2 [MUST], TRD.md TD-14). OS 조건문을 갖지
않는다(§C.2 [MUST], TD-16).

집행 규칙:
- C-API-1 [MUST]: 실제 SUT의 공개 HTTP endpoint를 호출한다. 응답을 합성하는 경로가
  없다 — `act`는 항상 소켓을 열며, 열지 못하면 성공으로 기록하지 않는다.
- C-API-2 [MUST]: retry는 `TRANSPORT_ERROR_CODES` 한정이다. HTTP 응답을 받아낸 순간
  (4xx·5xx 포함) 재시도는 끝난다 — 제품 실패를 다음 시도의 성공으로 덮지 않는다
  (TASK.md C-3, TRD.md TD-13).
- C-API-3 [MUST]: 정리 대상은 `namespace == run_id`이고 `user_owned == false`인 fixture
  뿐이다. 그 밖의 자원은 `skipped_user_owned[]`로 남기고 건드리지 않는다(§C.3).
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from lib.e2e import executors as e2e_executors

SCHEMA_VERSION = e2e_executors.SCHEMA_VERSION

EXECUTOR_TYPE = "api"
CLIENT_ID = "urllib"

# §A.11 경로. 공통 필수 증적 5종이 아니므로 EVIDENCE_PATHS에 얹지 않고 여기서 소유한다.
API_REQUESTS_PATH = "api/requests.jsonl"
API_RESPONSES_PATH = "api/responses.jsonl"

# C-API-2 확정 목록 — 연결 거부·연결 초기화·DNS 일시 실패·TCP 연결 타임아웃.
# **제품의 4xx/5xx는 여기에 없다.** 목록을 넓히면 제품 실패가 재시도에 묻힌다.
TRANSPORT_ERROR_CODES: Tuple[str, ...] = (
    "ECONNREFUSED",
    "ECONNRESET",
    "EDNS",
    "ETIMEDOUT",
)
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_TIMEOUT_MS = 10_000
_RETRY_BACKOFF_S = 0.2

# §A.8 route — in-process HTTP 클라이언트이므로 외부 실행기를 거치지 않는다.
_ROUTE_NATIVE = "native"


def classify_transport_error(exc: BaseException) -> Optional[str]:
    """예외를 C-API-2 화이트리스트 코드로 분류한다. 해당 없으면 None.

    [MUST] `HTTPError`는 **응답을 받은 것**이므로 여기서 절대 분류되지 않는다 — 4xx/5xx가
    transport 오류로 새어 들어가면 retry가 제품 실패를 숨긴다.
    """
    if isinstance(exc, urllib.error.HTTPError):
        return None
    reason: Any = getattr(exc, "reason", exc)
    if isinstance(reason, socket.gaierror):
        return "EDNS"
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return "ETIMEDOUT"
    if isinstance(reason, ConnectionRefusedError):
        return "ECONNREFUSED"
    if isinstance(reason, ConnectionResetError):
        return "ECONNRESET"
    if isinstance(reason, OSError):
        errno = getattr(reason, "errno", None)
        return {61: "ECONNREFUSED", 111: "ECONNREFUSED", 54: "ECONNRESET", 104: "ECONNRESET",
                60: "ETIMEDOUT", 110: "ETIMEDOUT"}.get(errno)
    return None


@dataclass
class ApiFixture:
    """§A.3 `owned.json.api_fixtures` 원소 + 정리에 필요한 최소 정보."""

    fixture_id: str
    namespace: str
    endpoint: str
    method: str = "DELETE"
    user_owned: bool = False

    def as_owned_record(self) -> Dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "namespace": self.namespace,
            "endpoint": self.endpoint,
        }


@dataclass
class ApiHandle:
    """§B.3 `prepare`가 돌려주는 handle. run 하나의 API 실행 문맥이다."""

    run_id: str
    base_url: str
    namespace: str
    target: Optional[str] = None
    body_allowlist: Tuple[str, ...] = ()
    fixtures: List[ApiFixture] = field(default_factory=list)
    responses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    last_seq: Optional[int] = None

    def owned_fixtures(self) -> List[ApiFixture]:
        """C-API-3 — 정리 대상은 자기 namespace의 비-사용자 소유 fixture뿐이다."""
        return [
            item
            for item in self.fixtures
            if item.namespace == self.namespace and not item.user_owned
        ]

    def foreign_fixtures(self) -> List[ApiFixture]:
        return [
            item
            for item in self.fixtures
            if item.namespace != self.namespace or item.user_owned
        ]


class ApiExecutor(e2e_executors.Executor):
    """§B.3 API executor 구현. 증적 쓰기는 생성자로 받은 관문에만 위임한다."""

    executor_type = EXECUTOR_TYPE
    operations = e2e_executors.API_OPERATIONS
    capability_keys = e2e_executors.API_CAPABILITY_KEYS
    client = CLIENT_ID

    def __init__(
        self,
        *,
        runtime_context: Optional[Mapping[str, Any]] = None,
        writer: Any = None,
        action_log: Optional[e2e_executors.ActionLog] = None,
        opener: Optional[Any] = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ):
        context = dict(runtime_context or {})
        self.runtime_context = context
        self.binary_path = None
        self.resolution_source = e2e_executors.RESOLUTION_SOURCE_INPROCESS
        self.declared_version = None
        self.base_url = _strip_slash(context.get("backend_url") or context.get("base_url") or "")
        self.health_path = str(context.get("health_path") or "/health")
        self._writer = writer if writer is not None else context.get("writer")
        self._log = action_log or context.get("action_log") or e2e_executors.ActionLog()
        # 주입 가능한 전송 경로. 기본값은 실제 소켓을 여는 urllib이며, 모의 응답을
        # 만들어내는 기본 구현은 존재하지 않는다(C-API-1).
        self._opener = opener or context.get("opener") or _urlopen
        self._max_attempts = max(1, int(max_attempts))
        self._requests: List[Dict[str, Any]] = []
        self._responses: List[Dict[str, Any]] = []
        self._transport_attempts: List[Dict[str, Any]] = []

    # ── 조회 ─────────────────────────────────────────────────────────────────
    @property
    def action_log(self) -> e2e_executors.ActionLog:
        return self._log

    def request_records(self) -> List[Dict[str, Any]]:
        return [dict(item) for item in self._requests]

    def response_records(self) -> List[Dict[str, Any]]:
        return [dict(item) for item in self._responses]

    def transport_attempts(self) -> List[Dict[str, Any]]:
        """C-API-2 관측 지점 — 어떤 호출이 몇 번, 어떤 코드로 재시도됐는지."""
        return [dict(item) for item in self._transport_attempts]

    def executor_record(self) -> Dict[str, Any]:
        """§A.1.1 `executors[]` 원소."""
        return {
            "type": EXECUTOR_TYPE,
            "driver": None,
            "session_mode": None,
            "driver_version": None,
            "client": CLIENT_ID,
        }

    # ── §B.3 probe ───────────────────────────────────────────────────────────
    def op_probe(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """실제 SUT health 표면을 한 번 호출해 가용성을 확정한다(C-EXE-1·§B.5).

        base_url이 없거나 응답을 받지 못하면 `available=false`다. 설정값 존재만으로
        가용을 주장하지 않는다 — probe 아닌 근거로 가용성을 추정하지 않는다(NR-7).
        """
        if not self.base_url:
            return {
                "executor": EXECUTOR_TYPE,
                "available": False,
                "unavailable_reason": "api_base_url_absent",
                "capabilities": e2e_executors.default_capabilities(self.capability_keys),
            }
        probed_ok = False
        reason: Optional[str] = None
        try:
            response = self._send(
                method="GET",
                url=self.base_url + self.health_path,
                headers={},
                body=None,
                timeout_ms=int(request.get("timeout_ms") or 2_000),
                allow_retry=False,
            )
            probed_ok = 200 <= int(response["status"]) < 500
            if not probed_ok:
                reason = f"health_status_{response['status']}"
        except e2e_executors.ExecutorError as exc:
            reason = exc.detail_code

        capabilities = {
            key: {"available": probed_ok, "route": _ROUTE_NATIVE, "probed": True}
            for key in self.capability_keys
        }
        return {
            "executor": EXECUTOR_TYPE,
            "available": probed_ok,
            "version": None,
            "unavailable_reason": None if probed_ok else (reason or "probe_reported_unavailable"),
            "capabilities": capabilities,
        }

    # ── §B.3 prepare ─────────────────────────────────────────────────────────
    def op_prepare(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{run_id, target, isolation_key}` → `{handle, owned[], setup_evidence[]}`.

        fixture namespace는 `isolation_key`가 없으면 `run_id`다(C-API-3). 사용자 소유로
        표시된 fixture는 소유 대장에 올리되 정리 대상에서는 제외된다(§A.3 [MUST]).
        """
        run_id = str(request.get("run_id") or "")
        if not run_id:
            raise e2e_executors.ExecutorError("api_run_id_required", "prepare requires run_id")
        base_url = _strip_slash(str(request.get("base_url") or self.base_url))
        if not base_url:
            raise e2e_executors.ExecutorError(
                "api_base_url_absent", "prepare requires a leased SUT base_url"
            )
        namespace = str(request.get("isolation_key") or run_id)
        handle = ApiHandle(
            run_id=run_id,
            base_url=base_url,
            namespace=namespace,
            target=request.get("target"),
            body_allowlist=tuple(str(item) for item in (request.get("body_allowlist") or ())),
        )
        for spec in request.get("fixtures") or []:
            if not isinstance(spec, Mapping):
                continue
            handle.fixtures.append(
                ApiFixture(
                    fixture_id=str(spec.get("fixture_id") or f"{namespace}-fixture"),
                    namespace=str(spec.get("namespace") or namespace),
                    endpoint=str(spec.get("endpoint") or ""),
                    method=str(spec.get("method") or "DELETE").upper(),
                    user_owned=bool(spec.get("user_owned", False)),
                )
            )
        return {
            "handle": handle,
            "owned": [item.as_owned_record() for item in handle.owned_fixtures()],
            "setup_evidence": [],
        }

    # ── §B.3 act ─────────────────────────────────────────────────────────────
    def op_act(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle, action}` → `{ok, status, response_ref, observed_state}`.

        `ok`는 **전송이 끝났는가**이고 `status`는 **제품이 무엇을 답했는가**다. 둘을
        섞지 않는 것이 C-API-2의 관측 지점이다 — 4xx/5xx는 `ok=true`와 함께 그대로
        올라가고 재시도 대상이 아니다.
        """
        handle = _require_handle(request.get("handle"))
        action: Mapping[str, Any] = request.get("action") or {}
        step_id = str(request.get("step_id") or action.get("step_id") or "api-step")
        step_role = str(action.get("step_role"))
        method = str(action.get("method") or "GET").upper()
        url = _absolute_url(handle.base_url, str(action.get("url") or ""))
        headers = dict(action.get("headers") or {})
        body = action.get("body")
        timeout_ms = int(action.get("timeout_ms") or DEFAULT_TIMEOUT_MS)
        seq = self._log.next_seq

        started = time.monotonic()
        error_code: Optional[str] = None
        response: Optional[Dict[str, Any]] = None
        try:
            response = self._send(
                method=method,
                url=url,
                headers=headers,
                body=body,
                timeout_ms=timeout_ms,
                allow_retry=True,
                seq=seq,
            )
        except e2e_executors.ExecutorError as exc:
            error_code = exc.detail_code
        elapsed_ms = int((time.monotonic() - started) * 1000)

        collect_body = _body_allowed(url, handle.body_allowlist)
        request_record = {
            "seq": seq,
            "method": method,
            "url": url,
            "headers": headers,
            "body": body if collect_body else None,
            "timeout_ms": timeout_ms,
            "step_role": step_role,
        }
        response_record = {
            "seq": seq,
            "status": response["status"] if response else None,
            "headers": dict(response["headers"]) if response else {},
            "body": (response.get("json") if collect_body else None) if response else None,
            "elapsed_ms": elapsed_ms,
            "redacted": True,
        }
        self._requests.append(request_record)
        self._responses.append(response_record)

        self._log.record(
            step_id=step_id,
            executor=EXECUTOR_TYPE,
            action="act",
            step_role=step_role,
            result="ok" if response else "error",
            elapsed_ms=elapsed_ms,
            error_code=error_code,
            request={
                "method": method,
                "url": url,
                "headers": headers,
                "body_ref": f"{API_REQUESTS_PATH}#{seq}" if collect_body else None,
                "timeout_ms": timeout_ms,
            },
            response={
                "status": response["status"] if response else None,
                "body_ref": f"{API_RESPONSES_PATH}#{seq}" if collect_body else None,
                "elapsed_ms": elapsed_ms,
            },
        )

        if response is not None:
            handle.responses[seq] = response
            handle.last_seq = seq

        observed_state = None
        observe_url = action.get("observe_url")
        if response is not None and observe_url:
            observed_state = self._observe(handle, str(observe_url), step_id, step_role, timeout_ms)

        return {
            "ok": response is not None,
            "status": response["status"] if response else None,
            "response_ref": f"{API_RESPONSES_PATH}#{seq}",
            "observed_state": observed_state,
            "error_code": error_code,
            "seq": seq,
        }

    def _observe(
        self,
        handle: ApiHandle,
        observe_url: str,
        step_id: str,
        step_role: str,
        timeout_ms: int,
    ) -> Optional[Any]:
        """후속 observable state를 같은 SUT에 대한 실 호출로 확인한다(§A.11 상호참조 유지)."""
        follow = self.op_act(
            {
                "handle": handle,
                "step_id": f"{step_id}:observe",
                "action": {
                    "method": "GET",
                    "url": observe_url,
                    "timeout_ms": timeout_ms,
                    "step_role": step_role,
                },
            }
        )
        seq = follow.get("seq")
        captured = handle.responses.get(seq) if seq else None
        return captured.get("json") if captured else None

    # ── §B.3 assert ──────────────────────────────────────────────────────────
    def op_assert(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle, assertion}` → `{id, expected, actual, passed}`.

        [MUST] `expected`/`actual`은 `null`일 수 있으나 **키는 반드시 존재**한다(§A.5).
        실제값을 얻지 못한 경우에도 키를 지우지 않고 `null`로 남긴다 —
        `e2e_contract.py`가 키 존재로 `assertion_expected_actual_missing`을 판정한다.
        """
        handle = _require_handle(request.get("handle"))
        assertion: Mapping[str, Any] = request.get("assertion") or {}
        assertion_id = str(assertion.get("id") or "")
        if not assertion_id:
            raise e2e_executors.ExecutorError(
                "api_assertion_id_required", "assert requires assertion.id (§A.5.1)"
            )
        verifier = str(assertion.get("verifier") or "response")
        expected = assertion.get("expected")
        field_path = assertion.get("field")

        if verifier == "state":
            url = _absolute_url(handle.base_url, str(assertion.get("url") or ""))
            outcome = self.op_act(
                {
                    "handle": handle,
                    "step_id": f"{assertion_id}:state",
                    "action": {
                        "method": str(assertion.get("method") or "GET").upper(),
                        "url": url,
                        "timeout_ms": int(assertion.get("timeout_ms") or DEFAULT_TIMEOUT_MS),
                        "step_role": e2e_executors.STEP_ROLE_VERIFY,
                    },
                }
            )
            source = handle.responses.get(outcome.get("seq"))
        else:
            seq = assertion.get("source_seq") or handle.last_seq
            source = handle.responses.get(seq) if seq is not None else None

        actual = _extract(source, field_path) if source is not None else None
        return {
            "id": assertion_id,
            "verifier": verifier,
            "executor": EXECUTOR_TYPE,
            "expected": expected,
            "actual": actual,
            "passed": expected == actual,
            "at": e2e_executors.now_iso(),
            "evidence_refs": [API_RESPONSES_PATH],
        }

    # ── §B.3 capture ─────────────────────────────────────────────────────────
    def op_capture(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle, evidence_spec[]}` → `{artifacts, redacted, redaction_failed}`.

        §A.11 두 파일과 §A.4 actions.jsonl을 증적 관문으로 발행한다. 관문이 redaction에
        실패하면 `EvidenceError`가 올라가고 호출자가 원문 미잔존 상태로 `infra_error`를
        낸다(§A.12 [MUST], TASK.md C-6) — 여기서 삼키지 않는다.
        """
        _require_handle(request.get("handle"))
        writer = self._require_writer()

        artifacts: Dict[str, str] = {}
        artifacts["api_requests"] = writer.write_jsonl(
            API_REQUESTS_PATH, self._requests, kind=None, observed=False
        )
        artifacts["api_responses"] = writer.write_jsonl(
            API_RESPONSES_PATH, self._responses, kind=None, observed=False
        )
        artifacts["action_log"] = self._log.flush(writer)
        return {"artifacts": artifacts, "redacted": True, "redaction_failed": False}

    def write_assertions(self, run_id: str, results: Sequence[Mapping[str, Any]]) -> str:
        """§A.5 `assertions.json`을 증적 관문으로 발행한다."""
        from lib.e2e import evidence as e2e_evidence

        writer = self._require_writer()
        return writer.write_json(
            e2e_evidence.EVIDENCE_PATHS["assertion_evidence"],
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "results": [dict(item) for item in results],
            },
            kind="assertion_evidence",
            observed=bool(results),
        )

    # ── §B.3 cleanup ─────────────────────────────────────────────────────────
    def op_cleanup(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle}` → `{released[], leaked[], skipped_user_owned[]}`.

        [MUST] `namespace == run_id`이고 `user_owned == false`인 fixture만 호출한다.
        기존 제품 데이터·사용자 설정은 대상이 아니며 패턴으로 범위를 넓히지 않는다
        (§C.3, TRD.md TD-15).
        """
        handle = _require_handle(request.get("handle"))
        released: List[Dict[str, Any]] = []
        leaked: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = [
            {"kind": "api_fixture", "id": item.fixture_id, "reason": "not_owned_by_this_run"}
            for item in handle.foreign_fixtures()
        ]

        for fixture in handle.owned_fixtures():
            seq = self._log.next_seq
            started = time.monotonic()
            error_code: Optional[str] = None
            response: Optional[Dict[str, Any]] = None
            try:
                response = self._send(
                    method=fixture.method,
                    url=_absolute_url(handle.base_url, fixture.endpoint),
                    headers={},
                    body=None,
                    timeout_ms=DEFAULT_TIMEOUT_MS,
                    allow_retry=True,
                    seq=seq,
                )
            except e2e_executors.ExecutorError as exc:
                error_code = exc.detail_code
            elapsed_ms = int((time.monotonic() - started) * 1000)
            self._log.record(
                step_id=f"cleanup:{fixture.fixture_id}",
                executor=EXECUTOR_TYPE,
                action="act",
                step_role=e2e_executors.STEP_ROLE_CLEANUP,
                result="ok" if response else "error",
                elapsed_ms=elapsed_ms,
                error_code=error_code,
                request={
                    "method": fixture.method,
                    "url": _absolute_url(handle.base_url, fixture.endpoint),
                    "headers": {},
                    "body_ref": None,
                    "timeout_ms": DEFAULT_TIMEOUT_MS,
                },
                response={
                    "status": response["status"] if response else None,
                    "body_ref": None,
                    "elapsed_ms": elapsed_ms,
                },
            )
            record = {"kind": "api_fixture", "id": fixture.fixture_id}
            if response is not None and int(response["status"]) < 400:
                released.append(record)
            else:
                # §A.6.1 — api_fixture 누출은 infra_error 승격 대상이 아니라 warning이다.
                leaked.append(dict(record, reason=error_code or f"status_{response['status']}"))
        return {"released": released, "leaked": leaked, "skipped_user_owned": skipped}

    # ── 전송 ─────────────────────────────────────────────────────────────────
    def _send(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, Any],
        body: Any,
        timeout_ms: int,
        allow_retry: bool,
        seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """실 SUT 호출 1건. C-API-2 화이트리스트 오류에만 재시도한다.

        HTTP 응답을 **한 번이라도 받으면** 그 응답이 결과다. 4xx/5xx에서 재시도하지
        않으며 다음 시도의 성공으로 덮지 않는다(TASK.md C-3).
        """
        attempts = self._max_attempts if allow_retry else 1
        last_code = "api_transport_error"
        last_detail = ""
        for attempt in range(1, attempts + 1):
            try:
                return self._opener(
                    method=method,
                    url=url,
                    headers=dict(headers),
                    body=body,
                    timeout_s=max(timeout_ms, 1) / 1000.0,
                )
            except Exception as exc:  # noqa: BLE001 — 분류 후 계약 오류로 다시 올린다.
                code = classify_transport_error(exc)
                if code is None:
                    # transport 오류가 아니면 재시도 대상이 아니다. 계약 오류로 올린다.
                    raise e2e_executors.ExecutorError("api_request_failed", str(exc)) from exc
                last_code, last_detail = code, str(exc)
                self._transport_attempts.append(
                    {"seq": seq, "url": url, "attempt": attempt, "error_code": code}
                )
                if attempt >= attempts:
                    break
                time.sleep(_RETRY_BACKOFF_S)
        raise e2e_executors.ExecutorError(last_code, last_detail)

    def _require_writer(self) -> Any:
        if self._writer is None:
            raise e2e_executors.ExecutorError(
                "api_evidence_writer_absent",
                "capture requires an EvidenceWriter — executors never write files directly (§C.2)",
            )
        return self._writer


# ─── 전송 기본 구현 ──────────────────────────────────────────────────────────
def _urlopen(*, method: str, url: str, headers: Mapping[str, Any], body: Any, timeout_s: float) -> Dict[str, Any]:
    """실제 소켓을 여는 유일한 경로. 모의 응답을 만들지 않는다(C-API-1)."""
    data: Optional[bytes] = None
    send_headers = {str(key): str(value) for key, value in headers.items()}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        send_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(url, data=data, method=method, headers=send_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            return _to_response(response.status, response.headers.items(), response.read())
    except urllib.error.HTTPError as exc:
        # 제품의 4xx/5xx다. 예외가 아니라 **응답**으로 되돌린다 — 호출자가 이것을 숨기지
        # 못하게 하는 것이 C-API-2의 요점이다.
        return _to_response(exc.code, exc.headers.items() if exc.headers else [], exc.read())


def _to_response(status: int, header_items: Any, raw: bytes) -> Dict[str, Any]:
    text = raw.decode("utf-8", errors="replace") if raw else ""
    parsed: Any = None
    if text:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
    return {
        "status": int(status),
        "headers": {str(key): str(value) for key, value in (header_items or [])},
        "text": text,
        "json": parsed,
    }


# ─── 헬퍼 ────────────────────────────────────────────────────────────────────
def _strip_slash(url: str) -> str:
    return str(url or "").rstrip("/")


def _absolute_url(base_url: str, url: str) -> str:
    if not url:
        return base_url
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return urllib.parse.urljoin(base_url + "/", url.lstrip("/"))


def _body_allowed(url: str, allowlist: Sequence[str]) -> bool:
    """§A.11 — body는 기본 미수집이며 시나리오 allowlist endpoint만 수집한다."""
    path = urllib.parse.urlparse(url).path or url
    return any(str(item) and str(item) in path for item in allowlist)


def _require_handle(handle: Any) -> ApiHandle:
    if not isinstance(handle, ApiHandle):
        raise e2e_executors.ExecutorError(
            "api_handle_required", "operation requires the handle returned by prepare (§B.3)"
        )
    return handle


def _extract(source: Optional[Mapping[str, Any]], field_path: Any) -> Any:
    """응답에서 `field` 경로의 값을 뽑는다. 경로가 없으면 `None`(키는 호출자가 유지)."""
    if source is None:
        return None
    if field_path in (None, "", "status"):
        return source.get("status")
    cursor: Any = source.get("json")
    for part in str(field_path).split("."):
        if isinstance(cursor, Mapping) and part in cursor:
            cursor = cursor[part]
            continue
        if isinstance(cursor, (list, tuple)):
            try:
                cursor = cursor[int(part)]
                continue
            except (ValueError, IndexError):
                return None
        return None
    return cursor


def register() -> None:
    """레지스트리에 `api` executor를 등록한다.

    import 부작용으로 자동 등록하지 않는다 — 후보 목록이 언제 열리는지를 호출자가
    통제해야 §A.2.1 상태 순서(기동 → 후보 해석)를 지킬 수 있기 때문이다.
    """
    e2e_executors.register_executor(
        EXECUTOR_TYPE, lambda **kwargs: ApiExecutor(**kwargs)
    )
