"""
@header {
  "module": "adapters.brain_session",
  "layer": "service",
  "domain": "console",
  "description": "대화별 BrainSession 상태기계 (B2). ConversationBrainSession: 단일 대화(conversation_id)의 인메모리 세션 핸들 + threading.Lock 직렬화. BrainSessionRegistry: dict[conversation_id → ConversationBrainSession] 전역 레지스트리 — 대화별 독립 세션 격리. 한 프로젝트에 복수 대화 공존 가능. state 필드: idle|priming|ready|error. prime(session_id, project_path)·ask(session_id, question, project_path)·status(session_id)·reset(session_id) — 모두 해당 session_id 세션에만 작용. project_path는 cwd 격리에만 사용(brain 검색 격리 유지). 5트리거 리셋은 대화(session_id)별 적용: ⓐ서버재실행(인메모리 소멸) ⓑturn_count≥임계(20) ⓒ유휴(30분) ⓓ크래시(resume 실패→새 uuid 콜드 재시도, 투명) ⓔ수동(reset(session_id)). [KEY] conversation_id(FE uuid)와 claude 세션 핸들(_claude_session_id)을 분리 — 콜드마다 새 uuid4 발급 → 'already in use' 충돌 근본 차단. conversation_id는 레지스트리 키·FE 계약 전용(opbr_adapter에 절대 전달 안 함). [MUST] backend 무상태 원칙 — Q&A 내용 저장 안 함. 세션 핸들만(휘발성 프로세스 상태) 보유, DB·파일 영속 금지. 동시성: dict 접근은 전역 _registry_lock으로 보호, 개별 세션 내부는 ConversationBrainSession._lock으로 보호. 비동기 잡 폴링(PLAN §3.1.2): submit_job(question)→job_id 즉시 반환·백그라운드 ask 실행, get_job(job_id)→스냅샷(done/error 수신 시 _current_job 제거=TTL). BrainSessionRegistry 위임: submit_job(session_id,question,project_path)·get_job(session_id,job_id). [T060 F-2/F-4] 프라임 연결 풀: BrainSessionRegistry._pool(project_path→[claude_session_id])·_pool_inflight·_prime_semaphore(동시 프라임 상한, DEFAULT_MAX_CONCURRENT_PRIME=2)를 `_pool_lock`(레지스트리 `_lock`과 분리)으로 보호. prewarm(project_path)→목표치 미달 시 daemon 스레드로 `_prime_into_pool` 기동(비블로킹, 락 없이 subprocess 실행 후 재획득 append). checkout_warm_handle(project_path)→pop 후 백그라운드 리필 트리거, None이면 풀 empty. `_get_or_create`가 신규 세션 생성 시 레지스트리 락 해제 후 checkout_warm_handle→adopt_warm_handle로 웜 핸들 이식(락 순서 계약: `_lock`→`_pool_lock` 방향만 허용, 역순·세션 `_lock` 중첩 금지). ConversationBrainSession.adopt_warm_handle(claude_session_id)—풀 핸들 이식, 이미 웜/priming 중이면 방어 가드로 no-op(핸들 폐기).",
  "exports": ["BrainSessionRegistry", "brain_session_registry"],
  "depends": ["adapters.opbr_adapter"],
  "task": "060",
  "changelog": [
    "2026-06-23 Step2: submit_job/_run_job_background/get_job/_current_job 추가 — 비동기 잡 폴링 지원(PLAN §3.1.2)",
    "2026-07-14 T060 Step2/3: 프라임 연결 풀(prewarm/_prime_into_pool/checkout_warm_handle) + ConversationBrainSession.adopt_warm_handle(방어 가드 포함) 신설, _get_or_create 신규 세션 웜 핸들 주입 연결 (F-2/F-4)"
  ]
}
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Literal

from dashboard.backend.adapters import opbr_adapter

logger = logging.getLogger(__name__)

# "already in use" 에러 판정 패턴
_ALREADY_IN_USE_PHRASES = (
    "already in use",
    "session id",
    "session_id",
)


# 리셋 임계값 (기본값)
DEFAULT_MAX_TURNS: int = 20          # ⓑ turn_count 임계
DEFAULT_IDLE_TIMEOUT_S: float = 1800.0  # ⓒ 유휴 타임아웃 (30분)

# 타임아웃 (초)
COLD_TIMEOUT_S: float = 180.0
WARM_TIMEOUT_S: float = 60.0

# 프라임 연결 풀 기본값 (T060 F-2)
DEFAULT_POOL_SIZE: int = 1                 # 프로젝트당 웜 핸들 목표 개수
DEFAULT_MAX_CONCURRENT_PRIME: int = 2      # 동시 프라임 상한 (R3/H-3)
PREWARM_QUESTION: str = "프로젝트 브레인 세션을 초기화합니다."  # 기존 prime() 프라임 질의 재사용

# state 타입 리터럴
BrainState = Literal["idle", "priming", "ready", "error"]


def _is_already_in_use_error(exc: Exception) -> bool:
    """claude 'Session ID already in use' 류 에러인지 판정."""
    msg = str(exc).lower()
    return "already in use" in msg


class ConversationBrainSession:
    """단일 대화(conversation_id)의 B2 BrainSession 상태기계.

    thread-safe: 모든 상태 변경은 _lock 보호 하에 수행.
    backend 무상태 원칙: Q&A 내용 저장 없음 — 세션 핸들(conversation_id 등)만 인메모리 보관.
    DB·파일 영속 금지.

    conversation_id vs _claude_session_id:
        - conversation_id: FE가 생성·전달하는 대화 식별자. 레지스트리 키. opbr_adapter에 절대 전달 안 함.
        - _claude_session_id: BE가 콜드 프라임마다 새 uuid4를 발급하는 claude CLI 핸들.
          cold=True → --session-id <새 uuid4> / cold=False → --resume <_claude_session_id>
          conversation_id를 재사용하지 않으므로 'already in use' 충돌 근본 차단.

    state 전이:
        idle → priming  (prime 시작)
        priming → ready (prime 성공)
        priming → error (prime 실패)
        ready → idle    (reset)
        error → idle    (reset)
        * → priming     (ask 콜드 프라임 시)

    Attributes:
        conversation_id: FE가 생성·전달하는 대화 식별자 (UUID). 레지스트리 키.
        project_path: cwd 격리용 OPAL 프로젝트 절대경로.
    """

    def __init__(
        self,
        conversation_id: str,
        project_path: str,
        max_turns: int = DEFAULT_MAX_TURNS,
        idle_timeout_s: float = DEFAULT_IDLE_TIMEOUT_S,
    ) -> None:
        self._lock = threading.Lock()
        self.conversation_id = conversation_id   # 레지스트리 키 — 불변
        self.project_path = project_path         # cwd 격리용 — 불변
        self._claude_session_id: str | None = None  # claude CLI --session-id/--resume 핸들
        self._created_at: float | None = None     # time.monotonic()
        self._last_used: float | None = None      # time.monotonic()
        self._turn_count: int = 0
        self._priming: bool = False               # prime 진행 중 플래그
        self._state: BrainState = "idle"          # 연동 상태
        self._last_error: str = ""                # error 상태 시 사유

        self.max_turns = max_turns
        self.idle_timeout_s = idle_timeout_s

        # 비동기 잡 상태 (단일 잡 슬롯): pending 중인 잡 또는 None
        self._current_job: dict | None = None

    # ── 상태 조회 ─────────────────────────────────────────────────────────────

    @property
    def claude_session_id(self) -> str | None:
        """claude CLI에서 발급된 세션 핸들 (--resume 용)."""
        return self._claude_session_id

    @property
    def turn_count(self) -> int:
        return self._turn_count

    @property
    def is_warm(self) -> bool:
        """세션이 웜(유효한 claude_session_id 보유)인지 여부."""
        return self._claude_session_id is not None

    def get_status(self) -> dict[str, Any]:
        """현재 세션 상태 스냅샷 반환 (진단용)."""
        with self._lock:
            return {
                "conversation_id": self.conversation_id,
                "project_path": self.project_path,
                "claude_session_id": self._claude_session_id,
                "turn_count": self._turn_count,
                "priming": self._priming,
                "created_at": (
                    datetime.fromtimestamp(
                        time.time() - (time.monotonic() - self._created_at)
                    ).isoformat()
                    if self._created_at is not None
                    else None
                ),
                "last_used": (
                    datetime.fromtimestamp(
                        time.time() - (time.monotonic() - self._last_used)
                    ).isoformat()
                    if self._last_used is not None
                    else None
                ),
            }

    def status(self) -> dict[str, Any]:
        """연동 상태 스냅샷 반환 (GET /api/brain/status?session_id=... 용).

        Returns:
            dict:
                state: "idle"|"priming"|"ready"|"error"
                session_active: bool — claude_session_id 보유 여부
                message: str — error 시 사유, 그 외 ""
        """
        with self._lock:
            return {
                "state": self._state,
                "session_active": self._claude_session_id is not None,
                "message": self._last_error if self._state == "error" else "",
            }

    # ── 리셋 트리거 판정 ──────────────────────────────────────────────────────

    def _should_reset(self) -> bool:
        """현재 세션이 리셋 조건에 해당하는지 판정 (lock 내에서 호출).

        ⓑ turn_count ≥ max_turns
        ⓒ 유휴(now - last_used > idle_timeout_s)
        """
        if self._claude_session_id is None:
            return False  # 이미 리셋 상태

        # ⓑ turn 임계
        if self._turn_count >= self.max_turns:
            return True

        # ⓒ 유휴 타임아웃
        if self._last_used is not None:
            idle_s = time.monotonic() - self._last_used
            if idle_s > self.idle_timeout_s:
                return True

        return False

    def _clear_state(self) -> None:
        """세션 상태 클리어 (lock 내에서 호출). state는 idle로 전이."""
        self._claude_session_id = None
        self._created_at = None
        self._last_used = None
        self._turn_count = 0
        self._priming = False
        self._state = "idle"
        self._last_error = ""

    # ── prime ─────────────────────────────────────────────────────────────────

    def prime(self) -> None:
        """콜드 프라임: 새 uuid4를 발급하여 --session-id로 opbr_adapter 호출.

        prime-on-intent용: 라우터가 백그라운드 스레드로 호출.
        이미 웜(state=ready)이거나 priming 중이면 no-op.

        conversation_id는 레지스트리 키 전용 — opbr_adapter에 전달하지 않음.
        claude 핸들은 콜드마다 새 uuid4 발급 → 'already in use' 충돌 근본 차단.

        state 전이: idle|error → priming → ready|error
        """
        with self._lock:
            if self._claude_session_id is not None:
                return  # 이미 웜 — no-op
            if self._priming:
                return  # 프라임 진행 중 — 중복 방지
            self._priming = True
            self._state = "priming"
            self._last_error = ""

        # lock 밖에서 실행 (블로킹 — 다른 요청도 lock 진입 가능)
        try:
            result = self._cold_prime_with_retry(
                question="프로젝트 브레인 세션을 초기화합니다.",
                timeout=COLD_TIMEOUT_S,
            )
            with self._lock:
                self._claude_session_id = result["session_id"]
                self._created_at = time.monotonic()
                self._last_used = time.monotonic()
                self._turn_count = 1  # 프라임 질의 1회
                self._priming = False
                self._state = "ready"
                self._last_error = ""
        except Exception as exc:
            with self._lock:
                self._priming = False
                self._state = "error"
                self._last_error = str(exc)
            raise

    # ── 웜 핸들 이식 (T060 F-4) ───────────────────────────────────────────────

    def adopt_warm_handle(self, claude_session_id: str) -> None:
        """풀에서 체크아웃한 웜 claude 세션 핸들을 이 세션에 이식.

        prime() 성공 커밋과 동형 — 이식 직후 state=ready, 첫 ask()는 --resume 경로.
        방어 가드(PM 지시 AGENTIC-LOG #8): 세션이 이미 웜(_claude_session_id 보유)이거나
        _priming 중이면 no-op — 전달받은 핸들은 폐기하고 기존 상태를 덮어쓰지 않는다.
        (동시에 신규 세션 생성 직후 호출되므로 정상 경로에서는 항상 idle/미웜 상태다.)

        Args:
            claude_session_id: 풀에서 체크아웃한 claude CLI 세션 핸들
        """
        with self._lock:
            if self._claude_session_id is not None or self._priming:
                return  # 이미 웜이거나 프라이밍 중 — 핸들 폐기(덮어쓰기 금지)
            self._claude_session_id = claude_session_id
            self._created_at = time.monotonic()
            self._last_used = time.monotonic()
            self._turn_count = 1              # 프라임 질의 1회 반영(prime()와 동일)
            self._priming = False
            self._state = "ready"
            self._last_error = ""

    # ── ask ──────────────────────────────────────────────────────────────────

    def ask(self, question: str) -> dict:
        """질의 수행. claude_session_id 있으면 --resume(웜), 없거나 리셋조건이면 콜드.

        5트리거 리셋:
          ⓐ 서버재실행 — 인메모리 소멸 = 자연 (claude_session_id=None 상태)
          ⓑ turn_count ≥ max_turns — _should_reset() 판정
          ⓒ 유휴 타임아웃 — _should_reset() 판정
          ⓓ 크래시 — resume 실패 시 같은 conversation_id로 콜드 재시도 (투명)
          ⓔ 수동 — reset() 후 ask 시 콜드 자동 진행

        성공 시: turn_count++, last_used 갱신.

        Returns:
            dict: {answer, citations, session_id, elapsed_s}
        """
        with self._lock:
            # ⓑ/ⓒ 리셋 조건 판정
            if self._should_reset():
                self._clear_state()

            current_claude_sid = self._claude_session_id

        if current_claude_sid is None:
            # 콜드 프라임 후 질의 (conversation_id로 --session-id 생성)
            logger.info(
                "[brain] ask COLD 경로 conv=%s (콜드 프라임 — 부트스트랩 로드, 최대 %.0fs)",
                self.conversation_id[:8], COLD_TIMEOUT_S,
            )
            return self._cold_and_ask(question)
        else:
            # 웜 resume 시도 → 실패 시 ⓓ 투명 재프라임
            logger.info(
                "[brain] ask WARM 경로 conv=%s (resume, 최대 %.0fs)",
                self.conversation_id[:8], WARM_TIMEOUT_S,
            )
            return self._warm_ask(question, current_claude_sid)

    def _cold_prime_with_retry(self, question: str, timeout: float) -> dict:
        """새 uuid4를 발급하여 콜드 프라임. 'already in use' 에러 시 1회 재시도.

        conversation_id는 절대 session_id로 전달하지 않음.
        매 호출마다 새 uuid4 발급 → 같은 id 재사용 없음 → 충돌 근본 차단.
        방어: claude가 'already in use' 에러를 콜드에서 반환해도 새 uuid로 1회 재시도.
        """
        new_handle = str(uuid.uuid4())
        try:
            result = opbr_adapter.prime_and_ask(
                question=question,
                project_path=self.project_path,
                session_id=new_handle,
                cold=True,
                timeout=timeout,
            )
        except Exception as exc:
            if _is_already_in_use_error(exc):
                # 방어: 만약 충돌 발생 시 새 uuid로 1회 재시도 (무한루프 방지 — 1회만)
                retry_handle = str(uuid.uuid4())
                result = opbr_adapter.prime_and_ask(
                    question=question,
                    project_path=self.project_path,
                    session_id=retry_handle,
                    cold=True,
                    timeout=timeout,
                )
            else:
                raise

        # claude 응답의 session_id 있으면 갱신, 없으면 발급한 uuid 유지
        returned_sid = result.get("session_id") or new_handle
        result["session_id"] = returned_sid
        return result

    def _cold_and_ask(self, question: str) -> dict:
        """콜드 프라임: 새 uuid4 발급 후 prime_and_ask 호출.

        conversation_id를 opbr_adapter에 전달하지 않음 — claude 핸들은 BE 발급 uuid4.
        state 전이: → priming → ready (성공) | error (실패).
        """
        with self._lock:
            self._state = "priming"
            self._last_error = ""

        try:
            result = self._cold_prime_with_retry(
                question=question,
                timeout=COLD_TIMEOUT_S,
            )
        except Exception as exc:
            with self._lock:
                self._state = "error"
                self._last_error = str(exc)
                self._priming = False
            raise

        with self._lock:
            self._claude_session_id = result["session_id"]
            self._created_at = time.monotonic()
            self._last_used = time.monotonic()
            self._turn_count = 1
            self._priming = False
            self._state = "ready"
            self._last_error = ""
        return result

    def _warm_ask(self, question: str, claude_session_id: str) -> dict:
        """웜 resume 시도. 실패 시 ⓓ 투명 재프라임 (새 uuid4 콜드 1회 재시도)."""
        try:
            result = opbr_adapter.prime_and_ask(
                question=question,
                project_path=self.project_path,
                session_id=claude_session_id,
                cold=False,
                timeout=WARM_TIMEOUT_S,
            )
            with self._lock:
                self._claude_session_id = result["session_id"]
                self._last_used = time.monotonic()
                self._turn_count += 1
                self._state = "ready"
                self._last_error = ""
            return result
        except RuntimeError:
            # ⓓ 크래시: resume 실패 → 세션 클리어 후 새 uuid4 콜드 1회 재시도 (투명 재프라임)
            with self._lock:
                self._clear_state()
            return self._cold_and_ask(question)

    # ── reset ─────────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """수동 리셋 (ⓔ): 세션 상태 클리어. state=idle. 다음 ask/prime이 콜드 프라임을 수행함."""
        with self._lock:
            self._clear_state()  # _clear_state가 state=idle로 전이시킴

    # ── 비동기 잡 폴링 (PLAN §3.1.2) ──────────────────────────────────────────

    def submit_job(self, question: str) -> str:
        """비동기 잡 제출. 진행 중(pending) 잡이 있으면 idempotent(기존 job_id 반환).

        없으면 새 job_id를 발급하고 백그라운드 스레드에서 ask를 실행한다.
        호출자에게 job_id를 즉시 반환 — 블로킹 없음.

        Args:
            question: 사용자 질문

        Returns:
            str: job_id (UUID 형식)
        """
        with self._lock:
            # 진행 중인 잡이 있으면 idempotent — 기존 job_id 반환
            if self._current_job is not None and self._current_job["status"] == "pending":
                return self._current_job["job_id"]
            # 새 잡 슬롯 할당
            job_id = str(uuid.uuid4())
            self._current_job = {
                "job_id": job_id,
                "status": "pending",
                "answer": "",
                "citations": [],
                "error_msg": "",
            }

        # 백그라운드 스레드로 ask 실행
        t = threading.Thread(
            target=self._run_job_background,
            args=(job_id, question),
            daemon=True,
        )
        t.start()
        return job_id

    def _run_job_background(self, job_id: str, question: str) -> None:
        """백그라운드에서 ask를 실행하고 _current_job을 갱신한다.

        job_id 불일치 시 덮어쓰기 방지(선점 잡 무시).

        Args:
            job_id: 이 잡의 식별자
            question: 사용자 질문
        """
        logger.info("[brain] job 실행 시작 job_id=%s", job_id[:8])
        t0 = time.monotonic()
        try:
            result = self.ask(question)
            elapsed = time.monotonic() - t0
            with self._lock:
                if self._current_job is not None and self._current_job["job_id"] == job_id:
                    self._current_job["status"] = "done"
                    self._current_job["answer"] = result.get("answer", "")
                    self._current_job["citations"] = result.get("citations", [])
            logger.info(
                "[brain] job 완료 job_id=%s status=done elapsed=%.1fs answer_len=%d",
                job_id[:8], elapsed, len(result.get("answer", "")),
            )
        except Exception as exc:
            elapsed = time.monotonic() - t0
            with self._lock:
                if self._current_job is not None and self._current_job["job_id"] == job_id:
                    self._current_job["status"] = "error"
                    self._current_job["error_msg"] = str(exc)
            logger.error(
                "[brain] job 실패 job_id=%s elapsed=%.1fs error=%s",
                job_id[:8], elapsed, exc,
            )

    def get_job(self, job_id: str) -> dict | None:
        """잡 상태 스냅샷 반환. job_id 불일치/미존재 시 None.

        done/error 상태이면 스냅샷 반환 후 _current_job을 제거(TTL — 1회 수신 후 소멸).

        Args:
            job_id: 조회할 잡의 식별자

        Returns:
            dict | None: 잡 스냅샷 또는 None(불일치·미존재)
        """
        with self._lock:
            if self._current_job is None:
                return None
            if self._current_job["job_id"] != job_id:
                return None
            snapshot = dict(self._current_job)
            # done/error — 1회 수신 후 제거(TTL)
            if snapshot["status"] in ("done", "error"):
                self._current_job = None
        return snapshot


# ── 대화별 레지스트리 ──────────────────────────────────────────────────────────

class BrainSessionRegistry:
    """대화(session_id) 단위 독립 BrainSession 레지스트리.

    session_id(conversation_id)를 키로 ConversationBrainSession 인스턴스를 관리한다.
    한 프로젝트에 복수의 대화가 공존할 수 있다 — 세션 간 상태 오염 없음.
    동시성: _registry_lock으로 dict 접근을 직렬화한다.
    """

    def __init__(
        self,
        max_turns: int = DEFAULT_MAX_TURNS,
        idle_timeout_s: float = DEFAULT_IDLE_TIMEOUT_S,
        pool_size: int = DEFAULT_POOL_SIZE,
        max_concurrent_prime: int = DEFAULT_MAX_CONCURRENT_PRIME,
    ) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, ConversationBrainSession] = {}
        self.max_turns = max_turns
        self.idle_timeout_s = idle_timeout_s

        # 프라임 연결 풀 (T060 F-2) — 레지스트리 _lock과 분리된 전용 락
        self.pool_size = pool_size
        self._pool_lock = threading.Lock()                        # 풀 전용 락 (레지스트리 _lock과 분리)
        self._pool: dict[str, list[str]] = {}                      # project_path → [claude_session_id, ...]
        self._pool_inflight: dict[str, int] = {}                   # project_path → 리필 진행 중 카운트
        self._prime_semaphore = threading.Semaphore(max_concurrent_prime)  # 동시 프라임 상한 (R3)

    def _get_or_create(self, session_id: str, project_path: str) -> ConversationBrainSession:
        """session_id에 해당하는 세션을 조회하거나 신규 생성 (lock 포함).

        신규 세션인 경우, 레지스트리 락 해제 후 풀에서 웜 핸들을 체크아웃하여 이식한다
        (T060 F-4). 락 순서 계약: `_lock`(레지스트리) 해제 후 `_pool_lock`(풀) 진입만
        허용 — 역순·중첩 금지(H-2). 풀이 비어 있으면 세션은 idle로 남아 기존 콜드
        경로로 폴백한다(F-4 AC(b), 회귀 없음).

        Args:
            session_id: FE가 생성·전달하는 대화 식별자
            project_path: cwd 격리용 OPAL 프로젝트 절대경로
        """
        with self._lock:
            is_new = session_id not in self._sessions
            if is_new:
                self._sessions[session_id] = ConversationBrainSession(
                    conversation_id=session_id,
                    project_path=project_path,
                    max_turns=self.max_turns,
                    idle_timeout_s=self.idle_timeout_s,
                )
            session = self._sessions[session_id]

        # 락 밖: 신규 세션이면 풀에서 웜 핸들 체크아웃 후 이식 (없으면 콜드 폴백)
        if is_new:
            warm_sid = self.checkout_warm_handle(project_path)   # _pool_lock (레지스트리 락 미보유)
            if warm_sid is not None:
                session.adopt_warm_handle(warm_sid)              # 세션 _lock (레지스트리 락 미보유)
        return session

    # ── 프라임 연결 풀 (T060 F-2) ────────────────────────────────────────────────

    def prewarm(self, project_path: str) -> None:
        """풀 목표치(pool_size) 미달 시 백그라운드 리필 스레드 1개 기동 (비블로킹).

        이미 채워졌거나 채우는 중이면 과잉 프라임 방지를 위해 즉시 반환한다.

        Args:
            project_path: 선프라임할 OPAL 프로젝트 절대경로
        """
        with self._pool_lock:                     # 비블로킹 구간만 락 보유
            have = len(self._pool.get(project_path, [])) + self._pool_inflight.get(project_path, 0)
            if have >= self.pool_size:
                return                            # 이미 채워짐/채우는 중 — 과잉 프라임 방지(size 1)
            self._pool_inflight[project_path] = self._pool_inflight.get(project_path, 0) + 1
        threading.Thread(target=self._prime_into_pool, args=(project_path,), daemon=True).start()

    def _prime_into_pool(self, project_path: str) -> None:
        """풀 리필 워커: 락 없이 subprocess 실행 후 락 재획득하여 append (R1 관용구).

        어떤 락도 subprocess 호출 중 보유하지 않는다(R1/H-1, H-2). 세마포어로 동시
        프라임 수를 max_concurrent_prime 이하로 강제한다(R3/H-3).

        Args:
            project_path: 프라임할 OPAL 프로젝트 절대경로
        """
        with self._prime_semaphore:               # 동시 프라임 상한 강제 (R3/H-3)
            try:
                handle = str(uuid.uuid4())        # opbr_adapter는 uuid 생성 안 함 — BE가 발급
                result = opbr_adapter.prime_and_ask(
                    question=PREWARM_QUESTION, project_path=project_path,
                    session_id=handle, cold=True, timeout=COLD_TIMEOUT_S)   # 락 미보유 구간
                sid = result.get("session_id") or handle
                with self._pool_lock:
                    self._pool.setdefault(project_path, []).append(sid)     # 락 재획득 후 append
                logger.info("[brain] prewarm 완료 project=%s pool=%d", project_path, len(self._pool[project_path]))
            except Exception as exc:
                logger.warning("[brain] prewarm 실패 project=%s error=%s", project_path, exc)  # 실패 시 폴백(콜드)
            finally:
                with self._pool_lock:
                    self._pool_inflight[project_path] = max(0, self._pool_inflight.get(project_path, 0) - 1)

    def checkout_warm_handle(self, project_path: str) -> str | None:
        """풀에서 웜 핸들 1개를 체크아웃(pop)하고 백그라운드 리필을 트리거한다.

        pop은 `_pool_lock` 하에서 수행되어 동시 체크아웃이 직렬화되므로 같은 핸들이
        중복 배정되지 않는다(F-2 AC(b)). 락 해제 후 리필을 트리거하므로 리필의
        subprocess 구간은 이 호출을 블로킹하지 않는다(H-1).

        Args:
            project_path: 체크아웃할 OPAL 프로젝트 절대경로

        Returns:
            str | None: 웜 claude 세션 핸들, 풀이 비어 있으면 None
        """
        with self._pool_lock:
            handles = self._pool.get(project_path)
            sid = handles.pop() if handles else None   # 동시 체크아웃 직렬화 → 중복 배정 차단
        if sid is not None:
            self.prewarm(project_path)                 # 락 해제 후 리필(내부에서 subprocess는 락 밖)
        return sid

    def prime(self, session_id: str, project_path: str) -> None:
        """해당 session_id 세션 콜드 프라임.

        다른 session_id 세션은 완전히 독립 — 영향 없음.

        Args:
            session_id: 프라임할 대화 식별자
            project_path: cwd 격리용 OPAL 프로젝트 절대경로
        """
        session = self._get_or_create(session_id, project_path)
        session.prime()

    def ask(self, session_id: str, question: str, project_path: str) -> dict:
        """해당 session_id 세션에 질의.

        session_id가 레지스트리에 없으면 (서버재시작 후 등) → 콜드 프라임으로 등록.

        Args:
            session_id: 질의할 대화 식별자
            question: 사용자 질문
            project_path: cwd 격리용 OPAL 프로젝트 절대경로 (없는 세션 생성 시 사용)
        """
        session = self._get_or_create(session_id, project_path)
        return session.ask(question)

    def status(self, session_id: str) -> dict[str, Any]:
        """해당 session_id 세션 상태 반환. 미존재 시 idle 반환.

        Args:
            session_id: 상태 조회할 대화 식별자
        """
        with self._lock:
            if session_id not in self._sessions:
                return {
                    "state": "idle",
                    "session_active": False,
                    "message": "",
                }
            session = self._sessions[session_id]
        return session.status()

    def reset(self, session_id: str) -> None:
        """해당 session_id 세션 수동 리셋. 다른 session_id 세션 불변.

        Args:
            session_id: 리셋할 대화 식별자
        """
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
            else:
                return  # 세션 없음 — no-op
        session.reset()

    def get_session(self, session_id: str) -> ConversationBrainSession | None:
        """해당 session_id 세션 직접 반환 (테스트·진단용). 없으면 None.

        Args:
            session_id: 조회할 대화 식별자
        """
        with self._lock:
            return self._sessions.get(session_id)

    def submit_job(self, session_id: str, question: str, project_path: str) -> str:
        """해당 session_id 세션에 비동기 잡 제출 — job_id 즉시 반환.

        세션이 없으면 신규 생성(서버재시작 후 콜드 경로).

        Args:
            session_id: 질의할 대화 식별자
            question: 사용자 질문
            project_path: cwd 격리용 OPAL 프로젝트 절대경로

        Returns:
            str: job_id (UUID 형식)
        """
        session = self._get_or_create(session_id, project_path)
        return session.submit_job(question)

    def get_job(self, session_id: str, job_id: str) -> dict | None:
        """해당 session_id 세션의 잡 상태 스냅샷 반환. 세션 없거나 job_id 불일치 시 None.

        Args:
            session_id: 조회할 대화 식별자
            job_id: 조회할 잡의 식별자

        Returns:
            dict | None: 잡 스냅샷 또는 None
        """
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            return None
        return session.get_job(job_id)


# ── 모듈 레벨 레지스트리 싱글턴 ────────────────────────────────────────────────────
# 데몬 프로세스 내에서 단일 BrainSessionRegistry를 공유 (단일 사용자 로컬 데몬)
brain_session_registry = BrainSessionRegistry()

# 하위 호환 별칭: 기존 코드가 brain_session 이름으로 참조하는 경우를 위해 제공
brain_session = brain_session_registry  # type: ignore[assignment]
