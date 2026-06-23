"""
@header {
  "module": "adapters.brain_session",
  "layer": "service",
  "domain": "console",
  "description": "대화별 BrainSession 상태기계 (B2). ConversationBrainSession: 단일 대화(conversation_id)의 인메모리 세션 핸들 + threading.Lock 직렬화. BrainSessionRegistry: dict[conversation_id → ConversationBrainSession] 전역 레지스트리 — 대화별 독립 세션 격리. 한 프로젝트에 복수 대화 공존 가능. state 필드: idle|priming|ready|error. prime(session_id, project_path)·ask(session_id, question, project_path)·status(session_id)·reset(session_id) — 모두 해당 session_id 세션에만 작용. project_path는 cwd 격리에만 사용(brain 검색 격리 유지). 5트리거 리셋은 대화(session_id)별 적용: ⓐ서버재실행(인메모리 소멸) ⓑturn_count≥임계(20) ⓒ유휴(30분) ⓓ크래시(resume 실패→새 uuid 콜드 재시도, 투명) ⓔ수동(reset(session_id)). [KEY] conversation_id(FE uuid)와 claude 세션 핸들(_claude_session_id)을 분리 — 콜드마다 새 uuid4 발급 → 'already in use' 충돌 근본 차단. conversation_id는 레지스트리 키·FE 계약 전용(opbr_adapter에 절대 전달 안 함). [MUST] backend 무상태 원칙 — Q&A 내용 저장 안 함. 세션 핸들만(휘발성 프로세스 상태) 보유, DB·파일 영속 금지. 동시성: dict 접근은 전역 _registry_lock으로 보호, 개별 세션 내부는 ConversationBrainSession._lock으로 보호. 비동기 잡 폴링(PLAN §3.1.2): submit_job(question)→job_id 즉시 반환·백그라운드 ask 실행, get_job(job_id)→스냅샷(done/error 수신 시 _current_job 제거=TTL). BrainSessionRegistry 위임: submit_job(session_id,question,project_path)·get_job(session_id,job_id).",
  "exports": ["BrainSessionRegistry", "brain_session_registry"],
  "depends": ["adapters.opbr_adapter"],
  "changelog": [
    "2026-06-23 Step2: submit_job/_run_job_background/get_job/_current_job 추가 — 비동기 잡 폴링 지원(PLAN §3.1.2)"
  ]
}
"""
from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime
from typing import Any, Literal

from dashboard.backend.adapters import opbr_adapter

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
            return self._cold_and_ask(question)
        else:
            # 웜 resume 시도 → 실패 시 ⓓ 투명 재프라임
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
        try:
            result = self.ask(question)
            with self._lock:
                if self._current_job is not None and self._current_job["job_id"] == job_id:
                    self._current_job["status"] = "done"
                    self._current_job["answer"] = result.get("answer", "")
                    self._current_job["citations"] = result.get("citations", [])
        except Exception as exc:
            with self._lock:
                if self._current_job is not None and self._current_job["job_id"] == job_id:
                    self._current_job["status"] = "error"
                    self._current_job["error_msg"] = str(exc)

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
    ) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, ConversationBrainSession] = {}
        self.max_turns = max_turns
        self.idle_timeout_s = idle_timeout_s

    def _get_or_create(self, session_id: str, project_path: str) -> ConversationBrainSession:
        """session_id에 해당하는 세션을 조회하거나 신규 생성 (lock 포함).

        Args:
            session_id: FE가 생성·전달하는 대화 식별자
            project_path: cwd 격리용 OPAL 프로젝트 절대경로
        """
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = ConversationBrainSession(
                    conversation_id=session_id,
                    project_path=project_path,
                    max_turns=self.max_turns,
                    idle_timeout_s=self.idle_timeout_s,
                )
            return self._sessions[session_id]

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
