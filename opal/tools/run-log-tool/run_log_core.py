"""
@header {
  "module": "run_log_core",
  "layer": "util",
  "domain": "opal-tools",
  "description": "태스크 실행 로그 기록 코어 — append 전용 줄 단위 기록 조각(run/run-log-{run_id}-{segment}.jsonl) 관리. init/append/validate_run/import_agentic/import_oppl/reconcile_duration/reconcile_duration_check 7개 공개 함수가 CONTRACT.md §2.6 인프로세스 호출 형태(task_path, run_id, ..., *, lock_held=False, lock_timeout_ms=30000)를 따른다. reconcile_duration(task_path, run_id, worker_run_id)은 같은 worker_run_id의 terminal 사건에서 duration_ms·floor(duration_ms/60000)(duration_minutes)을 조회하는 단일 대상 점조회이며, reconcile_duration_check(task_path, run_id=None, worker_run_id=None)은 run-log-tool reconcile-duration CLI 표면이 쓰는 범위 감사 조회다(worker_run_id 지정 시 불일치를 worker_duration_conflict로 즉시 거부, 미지정 시 {checked, mismatches}로 보고) — 둘 다 상태 원천 파일을 읽지 않는다(W-6, TASK C-4). 상태 원천 파일을 읽지도 쓰지도 않으며 상태 도구 모듈을 import하지 않는다(TRD D-5 단방향 의존, AC-19/MV-24). append()는 §1.1/§1.2 폐쇄형 스키마(validate_event)와 §1.3 4축 허용 조합·필수 증거(validate_provenance)를 조각 스캔 전에 순수 인메모리로 판정하고, 표 밖 조합·명시적 거부·사건별 actor 제약 위반을 provenance_invalid로, 폐쇄형 스키마·조건부 필수 필드 위반을 schema_invalid로 나눈다. COMBINATION_TABLE(A1~A8)과 iter_all_combinations()가 §1.3 조합 판정의 단일 원천이며 전수 열거가 그 표에서만 파생된다. 요청 식별자 멱등(AC-7)은 canonical_digest()가 발급 필드(event_id/sequence/actor_sequence/timestamp)를 제외한 정규 직렬화 SHA-256으로 판정하며, scan_run() 1회 조각 스캔에서 순번 발급과 함께 수행한다. actor_sequence 범위는 actor.kind=worker면 worker_run_id, 그 외에는 (actor.kind, actor.id)다. append()의 명시적 키워드 전용 mode 인자(None|shadow|active)는 active 전용 source.kind 제약(§1.3 말미)을 게이트하며, 코어는 이 값을 인자로만 받고 상태 원천에서 읽지 않는다. 직렬화 상한 16 KiB는 redact() 통과 후 최종 줄의 UTF-8 바이트로 잰다. import_agentic()/import_oppl()은 legacy AGENTIC-LOG.md·Project Loop .oppl-run/ 원본을 각각 형식별 규칙으로 표준 activity 사건(조합 A8)으로 정규화해 append()로 위임하며, 멱등 키는 원본 식별자·위치자·정규화 해시로 파생한 request_id로 환원해 append()의 멱등 판정을 그대로 탄다(역변환 금지, 완료 게이트 불기여). 가져오기 원본 읽기는 조각 경로와 동일한 심볼릭 링크·경계 이탈 방어(_reject_symlink_or_escape·_safe_read_bytes, O_NOFOLLOW)를 거치고, 신뢰 불가 원본의 디코딩 실패·타입 불일치·중첩 초과·달력 오류는 예외를 던지지 않고 해당 행·파일만 건너뛴다. 배타 락은 <task-path>/.opal-task.lock 1개이고 fcntl.flock(LOCK_EX+LOCK_NB) 재시도 루프로 30,000ms 기본 상한을 집행하며 초과 시 task_lock_timeout을 반환한다(§2.7). task_lock()은 이 락을 상태 도구와 공유하는 공개 컨텍스트매니저다. 락 파일·조각 파일은 0600, run/ 디렉터리는 0700으로 생성한다. run_id는 화이트리스트 정규식(RUN_ID_PATTERN)으로 검증한 뒤에만 파일명 보간·glob 패턴에 사용하고 glob.escape()·resolve() 포함 관계 확인을 덧댄다. 조각 생성은 O_CREAT|O_EXCL|O_NOFOLLOW, append는 O_WRONLY|O_APPEND|O_NOFOLLOW 단일 open()으로 TOCTOU·심볼릭 링크 추종 간극을 없앤다. 조각 상한(SEGMENT_MAX_BYTES, 4 MiB)에 다음 단일 사건의 최대 크기(MAX_EVENT_BYTES, 16 KiB) 여유가 남지 않으면 append()가 상한 검사·다음 번호 선택·새 조각 생성을 같은 `_with_lock()` 구간 안에서 연속 수행해 다음 번호 조각으로 전환한다(D-P5, W-5) — 새 조각 자리도 조각 경로와 같은 심볼릭 링크·경계 이탈 방어(`_reject_symlink_or_escape`)를 거치고, 이미 닫힌(이전 번호) 조각은 다시 열지 않는다. `scan_run()`은 번호 순 전 조각을 열거하므로 전환 이후에도 run 전역 순번·요청 식별자 멱등 판정 범위가 유지된다(D-P6). 순번은 색인 없이 조각 전량 스캔으로 발급하며, 디코딩·파싱 실패 줄은 예외를 던지지 않고 위반/손상 신호로 집계한다. 사건 시각은 Python 표준 라이브러리 UTC로 발급하고 날짜 도구를 타지 않는다(§1.1) — legacy 가져오기만 예외로 KST(+09:00) 고정 오프셋을 UTC로 옮긴다. redact()는 디스크 직렬화 직전 공통 마스킹 초크포인트이며 멱등 계약을 갖는다 — 환경변수형 비밀값·Bearer/token·API key·private key 블록 4종을 문자열 값 안에서만 규칙 기반 치환하고 키 집합·타입·중첩 구조는 보존한다(D-9, writer별 개별 마스킹 금지). 마스킹을 안전하게 판정할 수 없는 입력(적대적으로 깊은 중첩)은 저장을 거부하고 redaction_failed 오류 봉투만 반환한다. RUN_LOG_ERROR_CODES는 run-log 계열 오류 코드의 자기 SSOT다(상태 도구의 오류 코드 테이블과 물리 분리) — profile_not_found는 §3.1 소유 경계에 따라 이 테이블에 없다(상태 도구 쪽 소유). err()는 미등록 코드에 대해 .format() 호출을 건너뛴다. 런타임 색인·락 정책, 상태 보관함·복구, 원본 상한·마스킹 규칙 본문, 채널 변환기, 가져온 사건의 완료 게이트 불기여 집행은 이 모듈이 다루지 않는다 — 소유 배정은 `tasks/{NNN}-*/PLAN.md` 범위 경계표를 참조한다.",
  "exports": [
    "ok", "err", "redact", "require_absolute", "task_lock",
    "new_event_id", "new_run_id", "utc_now_ms", "segment_path",
    "ACTOR_KINDS", "PROVENANCE_TYPES", "RECORDED_BY_KINDS", "SOURCE_KINDS",
    "ALLOWED_EVENTS", "ALLOWED_TOP_LEVEL_KEYS", "EVENT_ACTOR_CONSTRAINTS",
    "COMBINATION_TABLE", "combination_of", "iter_all_combinations",
    "canonical_digest", "scan_run", "validate_event", "validate_provenance",
    "init", "append", "validate_run", "import_agentic", "import_oppl",
    "reconcile_duration", "reconcile_duration_check"
  ]
}
"""

# TASK C-4 / T-11 관례: 표준 라이브러리만 import. 상태 도구 모듈을 import하지 않는다(D-5).
import contextlib
import fcntl
import glob as glob_module
import hashlib
import json
import os
import pathlib
import re
import stat
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────────────────────────────────────────
# 오류 코드 SSOT (run-log 계열 전용, 상태 도구의 오류 코드 테이블과 물리 분리 — D-A)
# ─────────────────────────────────────────────────────────────────────────────

RUN_LOG_ERROR_CODES = {
    "task_path_not_absolute": "task path가 절대 경로가 아닙니다: {path}",
    "task_lock_timeout":      "배타 락 대기가 상한({timeout_ms}ms)을 초과했습니다: {path}",
    "run_log_write_failed":   "기록 조각 쓰기 실패: {detail}",
    "run_log_missing":        "기록 조각·실행 디렉터리가 없습니다: {detail}",
    "schema_invalid":         "폐쇄형 사건 스키마 위반: {detail}",
    "run_id_invalid":         "run_id 형식이 올바르지 않습니다(영숫자·밑줄·하이픈만 허용): {run_id}",
    "provenance_invalid":     "§1.3 허용 조합·출처 증거 위반: {detail}",
    "request_id_conflict":    "request_id가 재사용됐으나 payload가 다릅니다: {detail}",
    "event_too_large":        "직렬화 크기가 16 KiB 상한을 초과했습니다: {detail}",
    "redaction_failed":       "마스킹할 수 없는 원본으로 판정되어 저장을 거부합니다: {detail}",
    "worker_duration_conflict": "저장된 duration_ms가 파생값과 일치하지 않습니다: {detail}",
}

# run_id 형식 화이트리스트 (GC-003) — 파일명 보간·glob 패턴에 넣기 전 검증한다.
RUN_ID_PATTERN = re.compile(r"^run_[A-Za-z0-9_-]+$")

# CONTRACT §1.1 최상위 필드 전체 (폐쇄형 스키마 — 이 밖의 키는 거부)
ALLOWED_TOP_LEVEL_KEYS = {
    "schema_version", "event_id", "request_id", "sequence", "actor_sequence",
    "timestamp", "task_id", "run_id", "parent_run_id", "worker_run_id",
    "caused_by_event_id", "stage", "task_step", "work_item", "gate_id",
    "event", "actor", "provenance", "summary", "reason", "reason_code",
    "duration_ms", "duration_source", "duration_unknown_reason", "refs", "data",
}

# CONTRACT §1.2 사건 종류 12종
ALLOWED_EVENTS = {
    "run.started", "state.changed", "worker.started",
    "worker.capability.issued", "worker.capability.revoked", "activity",
    "worker.completed", "worker.failed", "worker.blocked",
    "gate.requested", "gate.resolved", "run.completed",
}

# ─────────────────────────────────────────────────────────────────────────────
# §1.3 조합 4축 enum (COMBINATION_TABLE·iter_all_combinations()의 원천)
# ─────────────────────────────────────────────────────────────────────────────

ACTOR_KINDS = ("worker", "PM", "user", "auto", "tool")
PROVENANCE_TYPES = ("direct", "adapter", "import")
RECORDED_BY_KINDS = ("worker", "PM", "adapter", "tool")
SOURCE_KINDS = (
    "worker_event", "process_start", "agent_handshake", "agent_message",
    "stream_event", "tool_result", "process_exit", "agent_error",
    "legacy_line", "oppl_event",
)
_SOURCE_KIND_OPTIONS = SOURCE_KINDS + (None,)

# CONTRACT §1.2 "주체" 열 — 사건 종류별 허용 actor.kind 집합. §1.3 조합 전수(AC-6/MV-2)의
# 일부이므로 provenance_invalid 판정에서 소비한다(D-T03-3 — event 이름 기준이 아니라
# actor.kind가 표 밖이면 provenance 위반). `activity`는 direct(A4~A7)·adapter(A1)·
# import(A3/A8) 조합 전부가 실제로 사용하는 범용 사건이라 5종 전부를 허용한다 —
# 조합 자체의 적법성은 COMBINATION_TABLE이 이미 좁혀 놓았으므로 이중 제약을 두지 않는다.
EVENT_ACTOR_CONSTRAINTS = {
    "run.started": ("tool",),
    "state.changed": ("tool",),
    "worker.started": ("worker",),
    "worker.capability.issued": ("tool",),
    "worker.capability.revoked": ("tool",),
    "activity": ACTOR_KINDS,
    "worker.completed": ("worker",),
    "worker.failed": ("worker",),
    "worker.blocked": ("worker",),
    "gate.requested": ("PM",),
    "gate.resolved": ("PM", "user", "auto"),
    "run.completed": ("tool",),
}

_TERMINAL_EVENTS = ("worker.completed", "worker.failed", "worker.blocked")
_REASON_REQUIRED_EVENTS = ("worker.failed", "worker.blocked", "run.completed")
# summary는 activity·gate 사건에만 조건부 필수다 — terminal 사건은 구조화된
# duration_*/reason 필드로 결과를 담고 summary를 요구하지 않는다(실사용 증거 — 워커
# terminal 사건 payload에 summary가 실리지 않는다).
_SUMMARY_REQUIRED_EVENTS = ("activity", "gate.requested", "gate.resolved")
_GATE_EVENTS = ("gate.requested", "gate.resolved")
_ACTIVITY_DATA_KINDS = ("progress", "decision", "validation", "retry")

# §1.1의 폐쇄형 스키마는 최상위 키만이 아니라 중첩 객체(actor/provenance와 그
# 하위 recorded_by/source)에도 적용된다(GC-208, §1.1.1·§1.1.2). 여기서 닫지
# 않으면 마스킹(redact(), 알려진 필드만 가릴 수 있다)으로도 막을 수 없는 구멍이
# 생긴다 — 예: worker_log_token_id 대신 worker_log_token을 실어 원문을 그대로
# 적재.
_ACTOR_ALLOWED_KEYS = frozenset({"kind", "id", "provider", "session_id"})
_PROVENANCE_ALLOWED_KEYS = frozenset({"type", "recorded_by", "worker_log_token_id", "source"})
_RECORDED_BY_ALLOWED_KEYS = frozenset({"kind", "id"})
_SOURCE_ALLOWED_KEYS = frozenset({
    "kind", "id", "sha256", "observed_at", "locator", "upstream_event_id",
})

# CONTRACT §1.3 허용 조합표 A1~A8. 이 테이블이 §1.3 조합 판정의 유일 원천이다 —
# combination_of()·iter_all_combinations() 모두 여기서만 파생한다(D-T03-1).
COMBINATION_TABLE = (
    {
        "id": "A1",
        "actor_kinds": frozenset({"worker"}),
        "provenance_type": "adapter",
        "recorded_by_kinds": frozenset({"adapter"}),
        "source_kinds": frozenset({
            "process_start", "agent_handshake", "agent_message",
            "stream_event", "tool_result", "process_exit", "agent_error",
        }),
    },
    {
        "id": "A2",
        "actor_kinds": frozenset({"worker"}),
        "provenance_type": "direct",
        "recorded_by_kinds": frozenset({"worker"}),
        "source_kinds": frozenset({"worker_event"}),
    },
    {
        "id": "A3",
        "actor_kinds": frozenset({"worker"}),
        "provenance_type": "import",
        "recorded_by_kinds": frozenset({"tool"}),
        "source_kinds": frozenset({"legacy_line", "oppl_event"}),
    },
    {
        "id": "A4",
        "actor_kinds": frozenset({"PM"}),
        "provenance_type": "direct",
        "recorded_by_kinds": frozenset({"PM", "tool"}),
        "source_kinds": frozenset({None}),
    },
    {
        "id": "A5",
        "actor_kinds": frozenset({"user"}),
        "provenance_type": "direct",
        "recorded_by_kinds": frozenset({"PM", "tool"}),
        "source_kinds": frozenset({None}),
    },
    {
        "id": "A6",
        "actor_kinds": frozenset({"auto"}),
        "provenance_type": "direct",
        "recorded_by_kinds": frozenset({"tool"}),
        "source_kinds": frozenset({None}),
    },
    {
        "id": "A7",
        "actor_kinds": frozenset({"tool"}),
        "provenance_type": "direct",
        "recorded_by_kinds": frozenset({"tool"}),
        "source_kinds": frozenset({None}),
    },
    {
        "id": "A8",
        "actor_kinds": frozenset({"PM", "user", "auto", "tool"}),
        "provenance_type": "import",
        "recorded_by_kinds": frozenset({"tool"}),
        "source_kinds": frozenset({"legacy_line", "oppl_event"}),
    },
)

# active 모드(§1.3 말미)에서만 집행되는 사건별 source.kind 제약. mode=None|"shadow"에서는
# 적용하지 않는다(D-T03-9의 원 설계는 "기록 코어가 아예 집행하지 않음"이었으나, PM
# 판정②가 "명시적 mode 인자로 게이트"로 갱신했다 — 코어는 이 값을 어디서도 읽지 않고
# 호출자가 전달한 인자로만 소비한다).
_ACTIVE_MODE_SOURCE_CONSTRAINTS = {
    "worker.started": frozenset({"process_start", "agent_handshake"}),
    "activity": frozenset({"agent_message", "stream_event", "tool_result"}),
    "worker.completed": frozenset({"process_exit", "agent_error"}),
    "worker.failed": frozenset({"process_exit", "agent_error"}),
    "worker.blocked": frozenset({"process_exit", "agent_error"}),
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RFC3339_MS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
_LEGACY_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")

DEFAULT_LOCK_TIMEOUT_MS = 30000
_LOCK_POLL_INTERVAL_SEC = 0.02

# 요청 식별자 멱등 정규 직렬화(canonical_digest)에서 제외하는 발급 필드 — 매 호출마다
# 달라지므로 동일성 비교 대상이 아니다(D-T03-6, AC-7).
_DIGEST_EXCLUDED_KEYS = frozenset({"event_id", "sequence", "actor_sequence", "timestamp"})


# ─────────────────────────────────────────────────────────────────────────────
# 응답 봉투 (CONTRACT §2.1 — 중첩형. 상태 도구 err()의 평면 봉투와 다르다.
# run-log-tool/state-tool 두 봉투 병존 경계는 README.md가 문서화한다 — F-1)
# ─────────────────────────────────────────────────────────────────────────────

def ok(**data):
    return {"ok": True, "data": data}


def err(code, message=None, **detail):
    if message is None:
        template = RUN_LOG_ERROR_CODES.get(code)
        if template is None:
            # 미등록 코드 — code 문자열 자체를 메시지로 쓰고 .format()은 건너뛴다
            # (GC-008: 미등록 코드가 우연히 "{...}"를 포함하면 포맷 문자열로
            # 오인되어 KeyError/부분 치환을 일으킬 수 있다).
            message = code
        else:
            try:
                message = template.format(**detail)
            except (KeyError, IndexError):
                message = template
    return {"ok": False, "error": {"code": code, "message": message, "detail": detail}}


# ─────────────────────────────────────────────────────────────────────────────
# 마스킹 초크포인트 (D-9 / TASK C-8 / W-2) — 값 문자열 안에서만 규칙 기반 치환.
# docs/SECURITY.md 점검 결과(2026-09-15) 마스킹 패턴 추가 등재 없음 — 환경변수형·
# Bearer/token·API key·private key 블록 4종 기본 패턴만 적용한다.
# ─────────────────────────────────────────────────────────────────────────────

_PRIVATE_KEY_BLOCK_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]+-----.*?-----END [A-Z0-9 ]+-----", re.DOTALL)
_BEARER_TOKEN_RE = re.compile(r"\bBearer\s+\S+", re.IGNORECASE)
_API_KEY_RE = re.compile(r"\bapi[_-]?key\s*[=:]\s*\S+", re.IGNORECASE)
# env var형 비밀값 — 이름에 아래 지표 단어가 들어간 KEY=value만 대상으로 한다
# (범용 KEY=value 전수 치환은 event_id·sha256 같은 보존 대상까지 건드릴 위험이
# 있어 H-5 위반이다 — 지표 단어 매치로 범위를 좁힌다). API key는 위 전용 패턴이
# 이미 담당하므로 여기서는 제외한다.
_ENV_SECRET_INDICATOR = r"(?:PASSWORD|PASSWD|SECRET|TOKEN|ACCESS_?KEY|PRIVATE_?KEY|CREDENTIAL)"
_ENV_SECRET_RE = re.compile(
    rf"\b(?P<key>[A-Za-z][A-Za-z0-9_]*{_ENV_SECRET_INDICATOR}[A-Za-z0-9_]*)=\S+",
    re.IGNORECASE,
)

_MASK_PLACEHOLDER = "[REDACTED]"
_MAX_REDACT_DEPTH = 200  # GC-205와 같은 이유의 방어 — 적대적으로 깊은 중첩은 redaction_failed


def _mask_private_key(_match):
    return "[REDACTED_PRIVATE_KEY_BLOCK]"


def _mask_bearer(_match):
    return f"Bearer {_MASK_PLACEHOLDER}"


def _mask_api_key(_match):
    return f"api_key={_MASK_PLACEHOLDER}"


def _mask_env_secret(match):
    return f"{match.group('key')}={_MASK_PLACEHOLDER}"


def _mask_secret_string(text):
    """문자열 값 하나에 4종 패턴을 순서대로 적용한다. 치환 결과 자리표시자는
    어떤 패턴과도 다시 일치하지 않으므로 재적용해도 동일 결과다(멱등, S-2)."""
    text = _PRIVATE_KEY_BLOCK_RE.sub(_mask_private_key, text)
    text = _BEARER_TOKEN_RE.sub(_mask_bearer, text)
    text = _API_KEY_RE.sub(_mask_api_key, text)
    text = _ENV_SECRET_RE.sub(_mask_env_secret, text)
    return text


class _RedactionFailure(Exception):
    """redact()가 안전하게 마스킹할 수 없다고 판정했을 때만 발생한다(내부 전용).
    append()가 이를 받아 redaction_failed 오류 봉투로 옮긴다."""


def _redact_value(value, _depth=0):
    if _depth > _MAX_REDACT_DEPTH:
        raise _RedactionFailure("payload 중첩 깊이가 마스킹 처리 한도를 초과했습니다")
    if isinstance(value, str):
        return _mask_secret_string(value)
    if isinstance(value, dict):
        return {k: _redact_value(v, _depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(v, _depth + 1) for v in value]
    return value


def redact(payload):
    """디스크 직렬화 **직전** 모든 writer가 통과하는 공통 마스킹 경로 (D-9).

    환경변수형 비밀값·Bearer/token·API key·private key 블록을 규칙 기반으로
    찾아 **문자열 값 안에서만** 치환한다. 문자열이 아닌 값과 dict/list의 키
    집합·타입·중첩 구조는 그대로 보존한다(W-2) — `event_id`·`sha256`·
    `worker_log_token_id`처럼 비밀값과 형태가 비슷한 식별자도 위 4종 패턴에
    걸리지 않으므로 값 그대로 남는다(H-5).

    [MUST] **멱등 계약**: 이미 이 함수를 통과한 payload를 다시 통과시켜도 결과가
    같아야 한다(같은 payload에 두 번 적용 == 한 번 적용) — 치환 자리표시자
    (`[REDACTED]` 계열)는 위 4종 패턴 중 어느 것과도 다시 일치하지 않는다.

    마스킹을 안전하게 판정할 수 없을 만큼(예: 적대적으로 깊은 중첩) 입력이
    구성돼 있으면 원본을 그대로 반환하지 않고 `_RedactionFailure`를 발생시킨다
    — 호출자(`append()`)가 이를 `redaction_failed` 오류 봉투로 옮긴다.
    """
    try:
        return _redact_value(payload)
    except RecursionError:
        raise _RedactionFailure("payload 중첩 깊이가 마스킹 처리 한도를 초과했습니다")


# ─────────────────────────────────────────────────────────────────────────────
# 경로 계약 (§3.2 / MV-27) — 추론 금지, 전달받은 절대경로로만 해석
# ─────────────────────────────────────────────────────────────────────────────

def require_absolute(task_path):
    """task_path가 절대경로가 아니면 err 봉투, 절대경로면 None."""
    if not os.path.isabs(str(task_path)):
        return err("task_path_not_absolute", path=str(task_path))
    return None


def _validate_run_id(run_id):
    """run_id가 화이트리스트 형식이 아니면 err 봉투, 형식이면 None (GC-003)."""
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.match(run_id):
        return err("run_id_invalid", run_id=run_id)
    return None


def _segment_glob_pattern(run_id):
    """조각 glob 패턴 — `run_id`가 이미 `_validate_run_id()`를 통과했어도
    `glob.escape()`를 한 번 더 적용한다(화이트리스트+이스케이프 이중 방어)."""
    return f"run-log-{glob_module.escape(run_id)}-*.jsonl"


def _ensure_run_dir(task_dir):
    """`run/` 디렉터리를 안전하게 보장한다(GC-103) — 심볼릭 링크 선점을 거부하고
    0700을 강제한다. 성공 시 `(run_dir, None)`, 실패 시 `(None, err 봉투)`."""
    run_dir = task_dir / "run"
    if run_dir.is_symlink():
        return None, err("run_log_write_failed",
                          detail=f"run/이 심볼릭 링크입니다(거부): {run_dir}")
    if not run_dir.exists():
        try:
            run_dir.mkdir(parents=True, mode=0o700)
        except FileExistsError:
            pass
        except OSError as e:
            return None, err("run_log_write_failed", detail=str(e))
    if run_dir.is_symlink():
        return None, err("run_log_write_failed",
                          detail=f"run/이 심볼릭 링크입니다(거부): {run_dir}")
    try:
        fd = os.open(str(run_dir), os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as e:
        return None, err("run_log_write_failed", detail=str(e))
    try:
        try:
            os.fchmod(fd, 0o700)
        except OSError:
            pass
    finally:
        os.close(fd)
    return run_dir, None


def _resolved_segments(task_dir, run_id):
    """`task_dir/run` 아래 조각을 glob으로 찾되, `run/` 자체가 심볼릭 링크이거나
    찾은 조각이 `task_dir` 경계 밖으로 해석되면 제외한다(GC-103)."""
    task_dir = pathlib.Path(task_dir)
    run_dir = task_dir / "run"
    if run_dir.is_symlink() or not run_dir.exists():
        return []
    resolved_task_dir = task_dir.resolve()
    segments = []
    for seg in sorted(run_dir.glob(_segment_glob_pattern(run_id))):
        try:
            resolved_seg = seg.resolve()
            resolved_seg.relative_to(resolved_task_dir)
        except (OSError, ValueError):
            continue
        segments.append(seg)
    return segments


_SEGMENT_NUMBER_SUFFIX_RE = re.compile(r"-(\d+)\.jsonl$")


def _active_segment_number(task_dir, run_id):
    """run의 현재 활성(가장 큰 번호) 조각 번호. 조각이 아직 하나도 없으면 첫 조각
    관례(D-H)에 따라 1을 반환한다. `init()`·`append()` 양쪽이 이 함수로 활성 조각을
    찾아 하드코딩된 `segment_path(..., 1)`을 대체한다(W-5)."""
    numbers = []
    for seg in _resolved_segments(task_dir, run_id):
        m = _SEGMENT_NUMBER_SUFFIX_RE.search(seg.name)
        if m:
            numbers.append(int(m.group(1)))
    return max(numbers) if numbers else 1


def _iter_records_from_bytes(raw_bytes):
    """조각 원문 바이트를 줄 단위로 안전하게 파싱한다 (GC-006). 실패한 줄은
    `None`으로 yield하고 호출자가 위반으로 집계한다. 빈 줄은 건너뛴다."""
    for raw_line in raw_bytes.split(b"\n"):
        if not raw_line.strip():
            continue
        try:
            text = raw_line.decode("utf-8")
        except UnicodeDecodeError:
            yield None
            continue
        try:
            yield json.loads(text)
        except (json.JSONDecodeError, RecursionError):
            # GC-205: 손상되거나 적대적으로 깊게 중첩된 줄도 예외를 밖으로
            # 던지지 않고 손상 신호(None)로 집계한다 — 조각은 신뢰 불가 원본을
            # 가져온 결과일 수 있다(legacy·oppl import).
            yield None


def _reject_symlink_or_escape(task_dir, path):
    """`path`가 심볼릭 링크이거나 해석 결과가 `task_dir` 경계 밖이면 err 봉투,
    안전하면 `None` (GC-201/202 — `_resolved_segments()`가 조각 경로에 이미 쓰는
    GC-103 방어를 가져오기 읽기 경로에도 이식한다). 신뢰 기준은 호출자가 전달한
    `task_dir`이지 `path.resolve()`가 아니다 — `path` 자신이나 그 부모 구성요소가
    링크면 `resolve()` 결과부터 이미 오염돼 있어 그것을 기준으로 삼으면 경계 검사가
    항상 통과해버린다(실측 재현: import-agentic/import-oppl → 태스크 밖 파일 적재).
    `path`가 아직 존재하지 않는 정상 경로(예: 선택적 원본 파일 부재)에는 개입하지
    않는다 — 존재 여부는 호출자가 판단한다."""
    path = pathlib.Path(path)
    if path.is_symlink():
        return err("run_log_write_failed",
                    detail=f"{path}이 심볼릭 링크입니다(거부)")
    try:
        resolved_task_dir = pathlib.Path(task_dir).resolve()
        path.resolve().relative_to(resolved_task_dir)
    except (OSError, ValueError):
        return err("run_log_write_failed",
                    detail=f"{path}이 태스크 경계 밖으로 해석됩니다(거부)")
    return None


def _safe_read_bytes(path):
    """`O_NOFOLLOW` 단일 `open()`으로 존재 확인과 오픈 사이 TOCTOU·심볼릭 링크
    추종 간극을 없앤다(GC-005와 동일 패턴, GC-201/202 가져오기 경로 이식).
    반환: `(bytes, None)` 성공, `(None, None)` 파일 부재, `(None, err봉투)` 그 외 실패.
    호출 전 `_reject_symlink_or_escape()`로 경계를 먼저 확인해야 한다 — 이 함수는
    marker 심볼릭 링크만 막고 부모 디렉터리 링크는 막지 않는다.

    [MUST] 열린 fd에 `os.fstat()` 게이트를 건다(GC-212) — 하드 링크는 경로
    비교(`_reject_symlink_or_escape`)로 잡을 수 없다. 링크와 원본이 같은
    inode이고 링크 경로 자체는 태스크 안에 있어 경계 검사를 그대로 통과한다.
    이미 연 fd의 메타데이터를 보므로 이 판정 자체에는 TOCTOU가 없다(T02가
    경로 기반 `chmod()` 대신 fd 기반 `os.fchmod()`를 쓴 것과 같은 원리) —
    (a) 정규 파일이 아니면(`stat.S_ISREG` 아님, 예: FIFO) 거부해 GC-213(무한
    정지)도 함께 닫고, (b) `st_nlink != 1`이면 하드 링크로 간주해 거부한다.

    [MUST] `open()` 자체에 `O_NONBLOCK`을 준다(GC-213) — FIFO는 `O_RDONLY`
    단독으로 열면 반대편 writer가 열릴 때까지 `open()` 호출 자체가 블로킹돼
    fstat 게이트에 도달하기 전에 멈춘다(실측: FIFO 배치 10초 타임아웃 재현).
    `O_NONBLOCK`은 정규 파일 읽기에는 아무 영향이 없다(POSIX상 정규 파일의
    읽기/쓰기는 항상 즉시 처리된다) — FIFO만 논블로킹으로 열려 즉시 fstat
    검사로 넘어가 거부된다.
    """
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None, None
    except OSError as e:
        return None, err("run_log_write_failed", detail=str(e))
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            os.close(fd)
            return None, err("run_log_write_failed",
                              detail=f"{path}이 정규 파일이 아닙니다(거부)")
        if st.st_nlink != 1:
            os.close(fd)
            return None, err("run_log_write_failed",
                              detail=f"{path}이 하드 링크입니다(거부): nlink={st.st_nlink}")
    except OSError as e:
        os.close(fd)
        return None, err("run_log_write_failed", detail=str(e))
    try:
        with os.fdopen(fd, "rb") as f:
            return f.read(), None
    except OSError as e:
        return None, err("run_log_write_failed", detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 식별자·시각 발급 (D-G — Python 표준 라이브러리 UTC, date.js를 타지 않는다)
# ─────────────────────────────────────────────────────────────────────────────

def new_event_id():
    return f"evt_{uuid.uuid4()}"


def new_run_id():
    return f"run_{uuid.uuid4()}"


def utc_now_ms():
    """RFC 3339 밀리초 UTC, 'Z' 접미(§1.1 timestamp 필수 형식)."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _legacy_kst_to_utc_ms(value):
    """`YYYY-MM-DD HH:mm`(시간대 없는 KST)을 RFC 3339 밀리초 UTC로 옮긴다
    (가져오기 전용, TRD §시간 모델 — Asia/Seoul 고정 오프셋 +09:00). 외부 날짜
    도구를 호출하지 않는다(D-5와 같은 이유, D-G)."""
    dt = datetime.strptime(value, "%Y-%m-%d %H:%M")
    dt_utc = dt - timedelta(hours=9)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def segment_path(task_path, run_id, n):
    """조각 경로 — D-1 패턴, 첫 조각은 0001(D-H). 4 MiB 경계 전환은 SEGMENT_MAX_BYTES와
    `_select_write_segment()`가 이 모듈 안에서 담당한다(W-5)."""
    return pathlib.Path(task_path) / "run" / f"run-log-{run_id}-{n:04d}.jsonl"


# 조각 상한(D-P5/AC-8/H-2) — 4 MiB. 여유는 사건 직렬화 상한(MAX_EVENT_BYTES)만큼
# 남겨 두고 전환해, 상한 검사 시점에 이번 사건의 최종 직렬화 크기를 아직 몰라도
# (redact()·sequence 발급 전) 다음 단일 append가 항상 새 조각 없이 상한 안에
# 들어가도록 보장한다.
SEGMENT_MAX_BYTES = 4 * 1024 * 1024
MAX_EVENT_BYTES = 16384


# ─────────────────────────────────────────────────────────────────────────────
# 배타 락 (D-4 — <task-path>/.opal-task.lock 1개, §2.7 기본 30,000ms 상한)
# ─────────────────────────────────────────────────────────────────────────────

def _acquire_lock(task_path, timeout_ms):
    """LOCK_EX|LOCK_NB 재시도 루프. 성공 시 열린 파일 디스크립터(fd), 상한 초과 시 None."""
    lock_path = pathlib.Path(task_path) / ".opal-task.lock"
    # GC-211: mode 없이 mkdir하면 umask 기본값(대개 0755)이 적용돼 읽기 전용
    # 명령(validate_run 등)도 태스크 디렉터리 트리를 세계 읽기 가능하게 만든다.
    # run/(0700)·조각·락 파일(0600)과 같은 최소 권한 원칙을 여기에도 맞춘다.
    lock_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        except OSError:
            if time.monotonic() >= deadline:
                return None
            time.sleep(_LOCK_POLL_INTERVAL_SEC)
            continue

        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except OSError:
            os.close(fd)
            if time.monotonic() >= deadline:
                return None
            time.sleep(_LOCK_POLL_INTERVAL_SEC)


@contextlib.contextmanager
def task_lock(task_path, *, lock_held=False, lock_timeout_ms=DEFAULT_LOCK_TIMEOUT_MS):
    """공개 락 컨텍스트매니저 — D-4 단일 배타 락을 외부 호출자(상태 도구)와 공유한다."""
    if lock_held:
        yield True
        return
    fd = _acquire_lock(task_path, lock_timeout_ms)
    if fd is None:
        yield False
        return
    try:
        yield True
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(fd)


def _with_lock(task_path, lock_held, lock_timeout_ms, fn):
    """fn()을 락 보유 구간 안에서 호출한다. 락 타임아웃이면 err 봉투를 그대로 반환한다."""
    with task_lock(task_path, lock_held=lock_held, lock_timeout_ms=lock_timeout_ms) as acquired:
        if not acquired:
            return err("task_lock_timeout", path=str(task_path), timeout_ms=lock_timeout_ms)
        return fn()


# ─────────────────────────────────────────────────────────────────────────────
# §1.3 조합 판정 (D-T03-1/2 — 전수 열거·판정의 단일 원천)
# ─────────────────────────────────────────────────────────────────────────────

def iter_all_combinations():
    """§1.3 조합 판정 4축의 곱집합 전체(660건)를 생성한다. actor_kind, provenance_type,
    recorded_by_kind, source_kind 튜플 순서로 yield한다."""
    for actor_kind in ACTOR_KINDS:
        for provenance_type in PROVENANCE_TYPES:
            for recorded_by_kind in RECORDED_BY_KINDS:
                for source_kind in _SOURCE_KIND_OPTIONS:
                    yield (actor_kind, provenance_type, recorded_by_kind, source_kind)


def combination_of(actor_kind, provenance_type, recorded_by_kind, source_kind):
    """4축 조합이 COMBINATION_TABLE의 어느 행과 일치하면 그 id, 아니면 None."""
    for row in COMBINATION_TABLE:
        if (actor_kind in row["actor_kinds"]
                and provenance_type == row["provenance_type"]
                and recorded_by_kind in row["recorded_by_kinds"]
                and source_kind in row["source_kinds"]):
            return row["id"]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 요청 식별자 멱등 정규화 (D-T03-6 / AC-7 / MV-5)
# ─────────────────────────────────────────────────────────────────────────────

def canonical_digest(event):
    """발급 필드(event_id/sequence/actor_sequence/timestamp)를 제외한 나머지 필드를
    키 정렬 정규 직렬화한 UTF-8 바이트의 SHA-256 hex. 저장된 사건과 재호출 payload
    양쪽에 같은 함수를 적용해 재계산으로 비교한다(색인 불요)."""
    normalized = {k: v for k, v in event.items() if k not in _DIGEST_EXCLUDED_KEYS}
    serialized = json.dumps(normalized, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# 순번 발급 + 멱등 조회 (D-3/D-I/D-T03-5/D-T03-7 — 색인 없이 조각 1회 스캔)
# ─────────────────────────────────────────────────────────────────────────────

def _actor_scope_key(actor, worker_run_id):
    """actor_sequence 범위 키 — actor.kind=worker면 worker_run_id, 그 외에는
    (actor.kind, actor.id)다(PM 판정①, CONTRACT §1.1 actor_sequence 정의)."""
    actor = actor or {}
    if actor.get("kind") == "worker":
        return ("worker_run_id", worker_run_id)
    return ("actor", actor.get("kind"), actor.get("id"))


def scan_run(task_path, run_id, event):
    """1회 조각 스캔으로 (다음 run 전역 sequence, 다음 actor_sequence, 손상된 줄 수,
    같은 request_id를 가진 저장 사건 또는 None)을 함께 계산한다(D-T03-7 — 순번
    스캔과 멱등 조회를 같은 순회에서 수행). 조각 glob이 이미 run_id로 좁혀져 있으므로
    (run_id, request_id) 범위가 자동으로 성립한다."""
    task_dir = pathlib.Path(task_path)
    max_seq = 0
    max_actor_seq = 0
    malformed = 0
    idempotent_match = None

    actor = event.get("actor") or {}
    scope_key = _actor_scope_key(actor, event.get("worker_run_id"))
    request_id = event.get("request_id")

    for seg in _resolved_segments(task_dir, run_id):
        for rec in _iter_records_from_bytes(seg.read_bytes()):
            if rec is None:
                malformed += 1
                continue
            seq = rec.get("sequence")
            if isinstance(seq, int) and seq > max_seq:
                max_seq = seq
            rec_actor = rec.get("actor") or {}
            rec_scope_key = _actor_scope_key(rec_actor, rec.get("worker_run_id"))
            if rec_scope_key == scope_key:
                a_seq = rec.get("actor_sequence")
                if isinstance(a_seq, int) and a_seq > max_actor_seq:
                    max_actor_seq = a_seq
            if request_id is not None and rec.get("request_id") == request_id:
                idempotent_match = rec

    return max_seq + 1, max_actor_seq + 1, malformed, idempotent_match


def _existing_request_ids(task_dir, run_id):
    """run의 전 조각에 이미 기록된 request_id 집합 — 가져오기 배치의 사전 스캔용
    (D-T03-11, 가져오기 멱등은 append()의 (run_id, request_id) 판정을 그대로 탄다)."""
    ids = set()
    for seg in _resolved_segments(task_dir, run_id):
        for rec in _iter_records_from_bytes(seg.read_bytes()):
            if rec is not None and rec.get("request_id") is not None:
                ids.add(rec.get("request_id"))
    return ids


# ─────────────────────────────────────────────────────────────────────────────
# 스키마 검증 (§1.1 폐쇄형 최상위 키 + §1.2 사건별 조건부 필수 필드 → schema_invalid)
# ─────────────────────────────────────────────────────────────────────────────

def _valid_sha256(value):
    return isinstance(value, str) and bool(_SHA256_RE.match(value))


def _valid_rfc3339_ms(value):
    return isinstance(value, str) and bool(_RFC3339_MS_RE.match(value))


def validate_event(event):
    """§1.1 폐쇄형 최상위 키·타입과 §1.2 사건별 조건부 필수 필드만 판정한다.
    §1.3 조합 전수·필수 증거는 validate_provenance()가 판정한다(D-T03-3 경계)."""
    if not isinstance(event, dict):
        return err("schema_invalid", detail="event는 object여야 합니다")

    unknown = set(event.keys()) - ALLOWED_TOP_LEVEL_KEYS
    if unknown:
        return err("schema_invalid", detail=f"정의되지 않은 최상위 키: {sorted(unknown)}")

    event_type = event.get("event")
    if event_type not in ALLOWED_EVENTS:
        return err("schema_invalid", detail=f"§1.2 밖의 event 값: {event_type!r}")

    data = event.get("data")
    if data is not None and not isinstance(data, dict):
        return err("schema_invalid", detail="data 필드는 object여야 합니다")

    actor = event.get("actor")
    if not isinstance(actor, dict) or actor.get("kind") not in ACTOR_KINDS:
        return err("schema_invalid", detail="actor.kind가 유효하지 않습니다")
    unknown_actor_keys = set(actor.keys()) - _ACTOR_ALLOWED_KEYS
    if unknown_actor_keys:
        # GC-208: §1.1은 최상위 키만이 아니라 §1.1.1(actor) 구조도 폐쇄형으로
        # 정의한다 — 정의되지 않은 중첩 키를 허용하면 스키마가 "완전한 문지기"가
        # 아니게 된다(AC-6).
        return err("schema_invalid",
                   detail=f"actor에 정의되지 않은 키: {sorted(unknown_actor_keys)}")

    provenance = event.get("provenance")
    if not isinstance(provenance, dict):
        return err("schema_invalid", detail="provenance가 object여야 합니다")
    unknown_prov_keys = set(provenance.keys()) - _PROVENANCE_ALLOWED_KEYS
    if unknown_prov_keys:
        # GC-208: 마스킹(redact())은 *알려진* 필드만 가릴 수 있어 정의되지 않은
        # 키(예: 호출자가 worker_log_token_id 대신 worker_log_token을 실어
        # 원문을 그대로 적재하는 경우)를 막지 못한다 — 이 구멍은 폐쇄형 스키마
        # 집행으로만 닫을 수 있다(§1.1.2, CONTRACT §1.1.3 "절대 남지 않는다").
        return err("schema_invalid",
                   detail=f"provenance에 정의되지 않은 키: {sorted(unknown_prov_keys)}")

    recorded_by = provenance.get("recorded_by")
    if not isinstance(recorded_by, dict):
        return err("schema_invalid", detail="provenance.recorded_by가 object여야 합니다")
    unknown_rb_keys = set(recorded_by.keys()) - _RECORDED_BY_ALLOWED_KEYS
    if unknown_rb_keys:
        return err("schema_invalid",
                   detail=f"provenance.recorded_by에 정의되지 않은 키: {sorted(unknown_rb_keys)}")

    source = provenance.get("source")
    if source is not None:
        if not isinstance(source, dict):
            return err("schema_invalid", detail="provenance.source가 object 또는 null이어야 합니다")
        unknown_src_keys = set(source.keys()) - _SOURCE_ALLOWED_KEYS
        if unknown_src_keys:
            return err("schema_invalid",
                       detail=f"provenance.source에 정의되지 않은 키: {sorted(unknown_src_keys)}")

    # worker_run_id의 "actor.kind=worker면 필수, 그 외 null" 판정(PM 판정①)은
    # validate_provenance()가 §1.3 조합 판정 직후에 수행한다(D-T03-3 재조정) — 조합
    # 자체가 표 밖인 사건(예: PM 대필 시도)은 그 사유만으로 이미 provenance_invalid이며,
    # 이 필드 하나가 §검증 순서상 더 앞선 스키마 단계에서 다른 사유의 거부를 가로채지
    # 않아야 각 시나리오가 판정하려는 단일 사유가 유지된다.

    # gate_id 조건부 필수 — gate.requested/gate.resolved만 필수, 그 외는 null.
    gate_id = event.get("gate_id")
    if event_type in _GATE_EVENTS:
        if not gate_id:
            return err("schema_invalid", detail=f"{event_type}는 gate_id가 필수입니다")
    elif gate_id is not None:
        return err("schema_invalid", detail=f"{event_type}는 gate_id를 가질 수 없습니다")

    # summary 조건부 필수 — activity·terminal·gate 사건.
    if event_type in _SUMMARY_REQUIRED_EVENTS and not event.get("summary"):
        return err("schema_invalid", detail=f"{event_type}는 summary가 필수입니다")

    # activity의 data.kind 4종 enum — data가 있을 때만 판정한다(data 자체는 선택).
    if event_type == "activity" and data is not None:
        kind = data.get("kind")
        if kind not in _ACTIVITY_DATA_KINDS:
            return err("schema_invalid", detail=f"activity data.kind가 4종 밖입니다: {kind!r}")

    # terminal(worker.completed/failed/blocked) duration 필드 — 정확히 하나만 허용.
    if event_type in _TERMINAL_EVENTS:
        has_ms = event.get("duration_ms") is not None
        has_unknown = event.get("duration_unknown_reason") is not None
        if has_ms == has_unknown:
            return err("schema_invalid",
                       detail=f"{event_type}는 duration_ms+duration_source 또는 "
                              "duration_unknown_reason 중 정확히 하나가 필요합니다")
        if has_ms and not event.get("duration_source"):
            return err("schema_invalid",
                       detail=f"{event_type}는 duration_ms와 함께 duration_source가 필요합니다")

        # W-6 — data.duration_spans[]는 {source_id, duration_ms} 배열이며 duration_ms는
        # span 합과 같아야 하고 같은 source_id 중복은 거부한다(§1.2 terminal 공통 조건,
        # PLAN.md D-P7·TRD.md §시간 모델 — 시각 차분으로 시간을 만들지 않는다). span
        # 필드는 선택이므로 event.data에 실려 있을 때만 판정한다.
        spans = (data or {}).get("duration_spans") if data is not None else None
        if spans is not None:
            if not isinstance(spans, list):
                return err("schema_invalid",
                           detail=f"{event_type}의 data.duration_spans는 array여야 합니다")
            seen_source_ids = set()
            span_sum = 0
            for span in spans:
                if not isinstance(span, dict):
                    return err("schema_invalid",
                               detail="duration_spans 원소는 object여야 합니다")
                source_id = span.get("source_id")
                span_ms = span.get("duration_ms")
                if not isinstance(source_id, str) or not source_id:
                    return err("schema_invalid",
                               detail="duration_spans[].source_id가 유효하지 않습니다")
                if not isinstance(span_ms, int) or isinstance(span_ms, bool) or span_ms < 0:
                    return err("schema_invalid",
                               detail="duration_spans[].duration_ms가 유효하지 않습니다")
                if source_id in seen_source_ids:
                    return err("schema_invalid",
                               detail=f"duration_spans에 같은 source_id가 중복됩니다: {source_id!r}")
                seen_source_ids.add(source_id)
                span_sum += span_ms
            if has_ms and span_sum != event.get("duration_ms"):
                return err("schema_invalid",
                           detail=f"duration_ms({event.get('duration_ms')})가 "
                                  f"duration_spans 합({span_sum})과 다릅니다")

    # reason 조건부 필수 — worker.failed/worker.blocked/run.completed.
    if event_type in _REASON_REQUIRED_EVENTS and not event.get("reason"):
        return err("schema_invalid", detail=f"{event_type}는 reason이 필수입니다")

    # state.changed data 구조 — from/to/row_key 3키 전부 필수.
    if event_type == "state.changed":
        d = data or {}
        if not all(k in d for k in ("from", "to", "row_key")):
            return err("schema_invalid", detail="state.changed는 data.from/to/row_key가 필수입니다")

    # worker.capability.issued/revoked data 구조 (§1.2 추가 필수 조건).
    if event_type == "worker.capability.issued":
        d = data or {}
        if not all(k in d for k in ("token_id", "token_sha256", "scope", "expires_at")):
            return err("schema_invalid",
                       detail="worker.capability.issued는 data.token_id/token_sha256/"
                              "scope/expires_at이 필수입니다")
    if event_type == "worker.capability.revoked":
        d = data or {}
        if not all(k in d for k in ("token_id", "reason")):
            return err("schema_invalid",
                       detail="worker.capability.revoked는 data.token_id/reason이 필수입니다")

    # refs — 프로젝트 상대 경로만 허용.
    refs = event.get("refs")
    if refs is not None:
        if not isinstance(refs, list):
            return err("schema_invalid", detail="refs는 array여야 합니다")
        for r in refs:
            if not isinstance(r, str) or os.path.isabs(r):
                return err("schema_invalid", detail=f"refs는 상대경로만 허용합니다: {r!r}")

    # timestamp 형식 — RFC 3339 밀리초.
    ts = event.get("timestamp")
    if ts is not None and not _valid_rfc3339_ms(ts):
        return err("schema_invalid", detail=f"timestamp 형식이 RFC 3339 ms가 아닙니다: {ts!r}")

    return None


# ─────────────────────────────────────────────────────────────────────────────
# §1.3 조합·출처 증거 검증 (→ provenance_invalid, D-T03-3 경계)
# ─────────────────────────────────────────────────────────────────────────────

def validate_provenance(event, *, mode=None):
    """§1.3 4축 허용 조합(전수), 사건별 actor 제약, adapter/import 필수 증거,
    active 모드 게이트 source 제약(PM 판정②)을 판정한다. 조합표 밖이거나 이
    함수가 거부하면 provenance_invalid — schema_invalid는 validate_event()
    소관이다(D-T03-3)."""
    event_type = event.get("event")
    actor = event.get("actor") or {}
    actor_kind = actor.get("kind")
    provenance = event.get("provenance") or {}
    prov_type = provenance.get("type")
    recorded_by = provenance.get("recorded_by") or {}
    recorded_by_kind = recorded_by.get("kind")
    source = provenance.get("source") or None
    source_kind = source.get("kind") if source else None

    combo_id = combination_of(actor_kind, prov_type, recorded_by_kind, source_kind)
    if combo_id is None:
        return err("provenance_invalid",
                   detail=f"§1.3 표 밖 조합: actor={actor_kind} type={prov_type} "
                          f"recorded_by={recorded_by_kind} source={source_kind}")

    # PM 판정① — CONTRACT §1.1 actor_sequence 정의("actor.kind=worker면 worker_run_id
    # 범위, 그 외 (actor.kind, actor.id) 범위")의 집행. 오류 코드는 schema_invalid다
    # (필드 필수 여부 위반 — D-T03-3 경계, PM 지시 "기존 worker.* 계열 집행과 같은 코드").
    # 위치는 여기(조합 매치 확인 후)다 — 조합 자체가 표 밖인 사건은 이미 그 사유로
    # provenance_invalid 반환을 마쳤으므로, 여기 도달했다는 것은 조합은 유효하다는
    # 뜻이다. 조합 불일치를 이 필드 검사가 가로채지 않아야 각 시나리오가 판정하려는
    # 단일 사유(조합 vs 필드)가 유지된다.
    worker_run_id = event.get("worker_run_id")
    if actor_kind == "worker" and not worker_run_id:
        return err("schema_invalid",
                   detail=f"actor.kind=worker 사건({event_type})은 worker_run_id가 필수입니다")
    if actor_kind != "worker" and worker_run_id is not None:
        return err("schema_invalid",
                   detail="actor.kind가 worker가 아니면 worker_run_id는 null이어야 합니다")

    allowed_actors = EVENT_ACTOR_CONSTRAINTS.get(event_type, ())
    if actor_kind not in allowed_actors:
        return err("provenance_invalid",
                   detail=f"{event_type} 사건은 actor.kind={actor_kind!r}를 허용하지 않습니다")

    if combo_id == "A1":
        for field in ("id", "sha256", "observed_at"):
            if not source or not source.get(field):
                return err("provenance_invalid", detail=f"adapter 사건에 source.{field} 결측")
        if not _valid_sha256(source.get("sha256")):
            return err("provenance_invalid", detail="source.sha256 형식이 유효하지 않습니다")
        if not _valid_rfc3339_ms(source.get("observed_at")):
            return err("provenance_invalid", detail="source.observed_at 형식이 유효하지 않습니다")
    elif combo_id in ("A3", "A8"):
        for field in ("id", "sha256", "locator"):
            if not source or not source.get(field):
                return err("provenance_invalid", detail=f"import 사건에 source.{field} 결측")
        if not _valid_sha256(source.get("sha256")):
            return err("provenance_invalid", detail="source.sha256 형식이 유효하지 않습니다")
    elif combo_id == "A2":
        if not provenance.get("worker_log_token_id"):
            return err("provenance_invalid",
                       detail="worker direct 사건에 worker_log_token_id 결측")

    if mode == "active":
        allowed_sources = _ACTIVE_MODE_SOURCE_CONSTRAINTS.get(event_type)
        if allowed_sources is not None and source_kind not in allowed_sources:
            return err("provenance_invalid",
                       detail=f"active 모드에서 {event_type}는 "
                              f"source.kind={source_kind!r}를 허용하지 않습니다")

    return None


# ─────────────────────────────────────────────────────────────────────────────
# 공개 명령 (CONTRACT §2.6 인프로세스 호출 형태)
# ─────────────────────────────────────────────────────────────────────────────

def init(task_path, run_id, *, lock_held=False, lock_timeout_ms=DEFAULT_LOCK_TIMEOUT_MS):
    """실행 디렉터리와 첫 조각 생성 — 멱등(이미 있으면 created:false)."""
    path_err = require_absolute(task_path)
    if path_err:
        return path_err
    run_id_err = _validate_run_id(run_id)
    if run_id_err:
        return run_id_err
    task_dir = pathlib.Path(task_path)

    def _do():
        run_dir, dir_err = _ensure_run_dir(task_dir)
        if dir_err:
            return dir_err
        # 현재 활성 조각 번호를 쓴다(하드코딩된 1번 제거, W-5) — 정상 경로에서는
        # run/이 방금 만들어졌거나 비어 있으므로 1을 반환해 기존 동작과 같다.
        segment = segment_path(task_dir, run_id, _active_segment_number(task_dir, run_id))
        created = False
        try:
            fd = os.open(str(segment),
                         os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            created = False
        except OSError as e:
            return err("run_log_write_failed", detail=str(e))
        else:
            os.close(fd)
            created = True
        return ok(run_id=run_id, segment=str(segment), created=created)

    return _with_lock(task_dir, lock_held, lock_timeout_ms, _do)


def _select_write_segment(task_dir, run_id):
    """append()가 이번 사건을 쓸 활성 조각을 고른다(D-P5, W-5). 현재 활성 조각의
    상한(SEGMENT_MAX_BYTES) 여유가 다음 단일 사건의 최대 크기(MAX_EVENT_BYTES)보다
    작으면 — 이 시점에는 아직 redact()·sequence 발급 전이라 이번 사건의 정확한
    직렬화 크기를 모르므로 최댓값(16 KiB)을 보수적으로 예약한다 — 다음 번호 조각을
    새로 만들어 그쪽으로 전환한다. 새 조각 자리는 기존 조각 경로와 같은 심볼릭
    링크·경계 이탈 방어(`_reject_symlink_or_escape`, GC-201/202)를 거치고
    O_CREAT|O_EXCL|O_NOFOLLOW 0600으로만 생성한다(C-8 — 기존 방어 재사용, 새로
    만들지 않는다). 이미 닫힌(이전 번호) 조각은 이 함수가 절대 다시 열지 않는다 —
    반환하는 조각은 이번 호출이 그대로 쓸 활성 조각 1개뿐이다.

    호출자는 이 함수를 `_with_lock()`이 이미 잡은 락 구간 **안에서** 호출해야
    한다 — 상한 검사·다음 번호 선택·새 조각 생성 사이에 락을 놓지 않는다(D-4 단일성).

    반환: `(segment_path, None)` 성공, `(None, err봉투)` 실패."""
    n = _active_segment_number(task_dir, run_id)
    segment = segment_path(task_dir, run_id, n)
    try:
        current_size = segment.stat().st_size
    except FileNotFoundError:
        return None, err("run_log_missing", detail=f"segment not found: {segment}")
    except OSError as e:
        return None, err("run_log_write_failed", detail=str(e))

    if current_size + MAX_EVENT_BYTES <= SEGMENT_MAX_BYTES:
        return segment, None

    # 상한 여유 부족 — 다음 번호로 전환한다.
    next_segment = segment_path(task_dir, run_id, n + 1)
    boundary_err = _reject_symlink_or_escape(task_dir, next_segment)
    if boundary_err:
        return None, boundary_err
    try:
        fd = os.open(str(next_segment),
                     os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        return None, err("run_log_write_failed",
                          detail=f"다음 조각 자리가 이미 점유돼 있습니다(거부): {next_segment}")
    except OSError as e:
        return None, err("run_log_write_failed", detail=str(e))
    os.close(fd)
    return next_segment, None


def append(task_path, run_id, event, *, lock_held=False, lock_timeout_ms=DEFAULT_LOCK_TIMEOUT_MS,
           mode=None):
    """표준 사건 1건 append. event_id/timestamp/schema_version은 미채움 시 여기서 발급한다
    (호출자가 이미 채워 넘기면 그 값을 그대로 보존 — 상태 도구의 사전 확정 경로, D-E).

    `mode`(키워드 전용, 기본 None)는 §1.3 말미 active 전용 source 제약을 게이트하는
    PM 판정② 인자다 — 코어는 이 값을 어디서도 읽지 않고 호출자가 전달한 값만 소비한다
    (D-5 단방향 의존 유지). 기존 위치·키워드 인자는 그대로이며 이 인자만 추가된다.
    """
    path_err = require_absolute(task_path)
    if path_err:
        return path_err
    run_id_err = _validate_run_id(run_id)
    if run_id_err:
        return run_id_err
    task_dir = pathlib.Path(task_path)

    def _do():
        full_event = dict(event)
        full_event.setdefault("schema_version", "1.0")
        full_event.setdefault("event_id", new_event_id())
        full_event.setdefault("run_id", run_id)
        full_event.setdefault("timestamp", utc_now_ms())
        full_event.setdefault("task_id", task_dir.name)
        for nullable in ("parent_run_id", "worker_run_id", "caused_by_event_id",
                          "stage", "task_step", "work_item", "gate_id",
                          "reason", "reason_code", "duration_ms",
                          "duration_source", "duration_unknown_reason", "refs"):
            full_event.setdefault(nullable, None)
        full_event.setdefault("summary", None)

        validation_err = validate_event(full_event)
        if validation_err:
            return validation_err

        provenance_err = validate_provenance(full_event, mode=mode)
        if provenance_err:
            return provenance_err

        # GC-103: run/ 자체가 (init 이후 별도 시점에) 심볼릭 링크로 치환됐으면
        # 그 아래 세그먼트를 열지 않는다.
        run_dir = task_dir / "run"
        if run_dir.is_symlink():
            return err("run_log_write_failed",
                       detail=f"run/이 심볼릭 링크입니다(거부): {run_dir}")

        # D-P5/W-5 — 상한 검사·다음 번호 선택·새 조각 생성을 이 락 구간 안에서
        # 연속 수행한다(중간에 락을 놓지 않는다). 하드코딩된 segment_path(...,1) 대신
        # 현재 활성 조각 번호를 쓰고, 상한 여유가 부족하면 다음 번호로 전환한다.
        segment, segment_err = _select_write_segment(task_dir, run_id)
        if segment_err:
            return segment_err

        next_seq, next_actor_seq, malformed, idempotent_match = scan_run(task_dir, run_id, full_event)
        if malformed:
            # GC-006: 순번을 신뢰할 수 없는 상태에서 append를 진행하면 중복·역행
            # sequence를 만들 수 있다 — append는 진단이 아니라 집행이므로 봉투
            # 오류로 거부한다.
            return err("run_log_write_failed",
                       detail=f"조각에 손상된 줄이 있어 append를 거부합니다: {malformed}건")

        # AC-7/MV-5 — (run_id, request_id) 멱등 판정. 발급 필드를 뺀 정규 직렬화가
        # 같으면 기존 사건을 그대로 반환(조각 미변경), 다르면 request_id_conflict.
        if idempotent_match is not None:
            if canonical_digest(idempotent_match) == canonical_digest(full_event):
                return ok(event_id=idempotent_match.get("event_id"),
                          sequence=idempotent_match.get("sequence"),
                          actor_sequence=idempotent_match.get("actor_sequence"),
                          segment=str(segment), idempotent_hit=True)
            return err("request_id_conflict",
                       detail=f"request_id={full_event.get('request_id')!r} 재사용, "
                              "payload가 이전 호출과 다릅니다")

        full_event["sequence"] = next_seq
        full_event["actor_sequence"] = next_actor_seq

        try:
            safe_event = redact(full_event)
        except _RedactionFailure as e:
            # 마스킹 불가 판정 원본은 저장하지 않는다 — 메타데이터(사유)만 담은
            # 오류 봉투를 반환하고 조각에는 아무 줄도 추가하지 않는다(§2.2 redaction_failed).
            return err("redaction_failed", detail=str(e))
        line = json.dumps(safe_event, ensure_ascii=False, default=str)
        line_bytes = line.encode("utf-8")
        if len(line_bytes) > MAX_EVENT_BYTES:
            # §1.1 — 직렬화 상한 16 KiB(MAX_EVENT_BYTES). redact() 통과 후 최종 줄로
            # 재므로 디스크 크기와 판정이 정확히 일치한다. 순번은 디스크에 아직
            # 확정되지 않았으므로 거부해도 다음 append가 같은 번호를 재계산한다(빈 번호 없음).
            return err("event_too_large",
                       detail=f"직렬화 크기 {len(line_bytes)} bytes > {MAX_EVENT_BYTES}")

        try:
            fd = os.open(str(segment), os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        except FileNotFoundError:
            return err("run_log_missing", detail=f"segment not found: {segment}")
        except OSError as e:
            return err("run_log_write_failed", detail=str(e))

        try:
            with os.fdopen(fd, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())
        except OSError as e:
            return err("run_log_write_failed", detail=str(e))

        return ok(event_id=full_event["event_id"], sequence=next_seq, actor_sequence=next_actor_seq,
                   segment=str(segment), idempotent_hit=False)

    return _with_lock(task_dir, lock_held, lock_timeout_ms, _do)


def validate_run(task_path, run_id, *, lock_held=False, lock_timeout_ms=DEFAULT_LOCK_TIMEOUT_MS):
    """run 단위 무결성 검증 — 조각 정렬·순번 중복/누락·총 바이트."""
    path_err = require_absolute(task_path)
    if path_err:
        return path_err
    run_id_err = _validate_run_id(run_id)
    if run_id_err:
        return run_id_err
    task_dir = pathlib.Path(task_path)

    def _do():
        segments = _resolved_segments(task_dir, run_id)
        if not segments:
            return err("run_log_missing", detail=f"run_id={run_id}의 조각이 없습니다")

        violations = []
        event_count = 0
        total_bytes = 0
        seen_sequences = []

        for seg in segments:
            raw = seg.read_bytes()
            total_bytes += len(raw)
            for rec in _iter_records_from_bytes(raw):
                event_count += 1
                if rec is None:
                    violations.append({"code": "malformed_line", "segment": str(seg)})
                    continue
                seq = rec.get("sequence")
                if isinstance(seq, int):
                    seen_sequences.append(seq)
                else:
                    violations.append({"code": "sequence_missing", "segment": str(seg)})

        seen_set = set()
        for seq in seen_sequences:
            if seq in seen_set:
                violations.append({"code": "sequence_duplicate", "sequence": seq})
            seen_set.add(seq)

        sequence_gaps = []
        top = max(seen_sequences) if seen_sequences else 0
        for n in range(1, top + 1):
            if n not in seen_set:
                sequence_gaps.append(n)

        verdict = "pass" if not violations and not sequence_gaps else "fail"
        return ok(run_id=run_id, verdict=verdict, segment_count=len(segments),
                   event_count=event_count, total_bytes=total_bytes,
                   sequence_gaps=sequence_gaps, violations=violations)

    return _with_lock(task_dir, lock_held, lock_timeout_ms, _do)


# ─────────────────────────────────────────────────────────────────────────────
# run_id 해석 (D-T03-18 — 가져오기 명령의 --run-id 생략 시 조각에서 발견)
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_import_run_id(task_dir, explicit_run_id):
    """(run_id, err봉투). explicit_run_id가 있으면 그대로(형식 검증만), 없으면
    run/ 조각 파일명에서 발견한다 — 정확히 1개면 그 값, 0개면 run_log_missing,
    2개 이상이면 schema_invalid(--run-id 명시 요구)."""
    if explicit_run_id is not None:
        rid_err = _validate_run_id(explicit_run_id)
        if rid_err:
            return None, rid_err
        return explicit_run_id, None

    run_dir = task_dir / "run"
    if run_dir.is_symlink() or not run_dir.exists():
        return None, err("run_log_missing", detail=f"{run_dir} 부재")

    found = set()
    for seg in run_dir.glob("run-log-*-*.jsonl"):
        m = re.match(r"^run-log-(?P<run_id>.+)-\d{4}\.jsonl$", seg.name)
        if m:
            found.add(m.group("run_id"))

    if not found:
        return None, err("run_log_missing", detail=f"{run_dir}에 조각이 없습니다")
    if len(found) > 1:
        return None, err("schema_invalid",
                         detail=f"run_id가 여럿입니다({sorted(found)}) — --run-id를 명시하세요")
    return next(iter(found)), None


# ─────────────────────────────────────────────────────────────────────────────
# 시간 파생 일치 조회·감사 (W-6, CONTRACT.md §1.2/§2.3 run-log-tool.reconcile-duration,
# TRD.md §시간 모델 — 단조 시계 구간 합만 쓰고 시각 차분으로 시간을 만들지 않는다)
# ─────────────────────────────────────────────────────────────────────────────

def _duration_span_sum(spans):
    """duration_spans[] 중 정수 duration_ms를 가진 항목만 합산한다. validate_event()가
    이미 폐쇄형으로 판정한 정상 payload뿐 아니라, 그 검증을 거치지 않고 조각에 실렸을
    수 있는 원본(legacy·수동 편집)도 방어적으로 다룬다."""
    total = 0
    for span in spans or ():
        if isinstance(span, dict):
            span_ms = span.get("duration_ms")
            if isinstance(span_ms, int) and not isinstance(span_ms, bool):
                total += span_ms
    return total


def reconcile_duration(task_path, run_id, worker_run_id, *, lock_held=False,
                        lock_timeout_ms=DEFAULT_LOCK_TIMEOUT_MS):
    """같은 worker_run_id의 terminal(worker.completed/failed/blocked) 사건에서
    duration_ms와 그 파생값 floor(duration_ms / 60000)(duration_minutes)을 조회한다
    (PLAN.md W-6 §2). task_path·run_id·worker_run_id만 인자로 받으며 상태 원천
    파일을 읽지 않는다(TASK C-4, TRD.md D-5 단방향 의존) — 다른
    도구(state-tool)가 이 함수를 인프로세스로 호출해 자신이 보유한 값과 비교한다.
    저장된 duration_ms가 자기 자신의 data.duration_spans[] 합과 다르면(append()
    이후 조각이 변조됐거나 검증 이전 시점의 legacy 사건이면) worker_duration_conflict로
    거부한다 — append()가 이미 이 조건을 막으므로 정상 경로에서는 발생하지 않는다."""
    path_err = require_absolute(task_path)
    if path_err:
        return path_err
    run_id_err = _validate_run_id(run_id)
    if run_id_err:
        return run_id_err
    task_dir = pathlib.Path(task_path)

    def _do():
        record = None
        for seg in _resolved_segments(task_dir, run_id):
            for rec in _iter_records_from_bytes(seg.read_bytes()):
                if rec is None:
                    continue
                if rec.get("event") in _TERMINAL_EVENTS and rec.get("worker_run_id") == worker_run_id:
                    record = rec
                    break
            if record is not None:
                break

        if record is None:
            return err("run_log_missing",
                       detail=f"worker_run_id={worker_run_id!r}의 terminal 사건이 없습니다")

        duration_ms = record.get("duration_ms")
        if duration_ms is None:
            # duration_unknown_reason 경로 — 파생할 값이 없다(schema_invalid 대상이 아님).
            return ok(duration_ms=None, duration_minutes=None)

        spans = (record.get("data") or {}).get("duration_spans")
        if isinstance(spans, list):
            span_sum = _duration_span_sum(spans)
            if span_sum != duration_ms:
                return err("worker_duration_conflict",
                           detail=f"worker_run_id={worker_run_id!r}의 저장된 "
                                  f"duration_ms({duration_ms})가 duration_spans 합"
                                  f"({span_sum})과 다릅니다")

        return ok(duration_ms=duration_ms, duration_minutes=duration_ms // 60000)

    return _with_lock(task_dir, lock_held, lock_timeout_ms, _do)


def reconcile_duration_check(task_path, run_id=None, worker_run_id=None, *, lock_held=False,
                              lock_timeout_ms=DEFAULT_LOCK_TIMEOUT_MS):
    """`run-log-tool reconcile-duration` CLI 표면의 조회 로직 — 지정 범위(run_id로
    좁히고, worker_run_id를 더 주면 단일 대상)의 terminal 사건을 훑어 저장된
    duration_ms가 자기 자신의 data.duration_spans[] 합과 일치하는지 감사한다.
    worker_run_id까지 지정하면 단일 대상 판정이 되어 불일치를 즉시
    worker_duration_conflict로 거부하고(자동화 소비자용 엄격 모드), 지정하지 않으면
    범위 내 전건을 훑어 {checked, mismatches}로 보고한다(감사 모드 — 개별 불일치
    하나로 전체 호출을 실패시키지 않는다). duration_spans가 없는 terminal 사건은
    감사할 근거가 없으므로 checked에 넣지 않는다. run_id 생략 시
    `_resolve_import_run_id()`와 같은 규칙으로 조각에서 유일 run_id를 찾는다."""
    path_err = require_absolute(task_path)
    if path_err:
        return path_err
    task_dir = pathlib.Path(task_path)

    def _do():
        resolved_run_id, resolve_err = _resolve_import_run_id(task_dir, run_id)
        if resolve_err:
            return resolve_err

        checked = 0
        mismatches = []
        for seg in _resolved_segments(task_dir, resolved_run_id):
            for rec in _iter_records_from_bytes(seg.read_bytes()):
                if rec is None:
                    continue
                if rec.get("event") not in _TERMINAL_EVENTS:
                    continue
                rec_worker_run_id = rec.get("worker_run_id")
                if worker_run_id is not None and rec_worker_run_id != worker_run_id:
                    continue
                duration_ms = rec.get("duration_ms")
                spans = (rec.get("data") or {}).get("duration_spans")
                if duration_ms is None or not isinstance(spans, list):
                    continue
                checked += 1
                span_sum = _duration_span_sum(spans)
                if span_sum != duration_ms:
                    if worker_run_id is not None:
                        return err("worker_duration_conflict",
                                   detail=f"worker_run_id={worker_run_id!r}의 "
                                          f"duration_ms({duration_ms})가 duration_spans 합"
                                          f"({span_sum})과 다릅니다")
                    mismatches.append({
                        "worker_run_id": rec_worker_run_id,
                        "duration_ms": duration_ms,
                        "span_sum": span_sum,
                    })

        return ok(checked=checked, mismatches=mismatches)

    return _with_lock(task_dir, lock_held, lock_timeout_ms, _do)


# ─────────────────────────────────────────────────────────────────────────────
# legacy AGENTIC-LOG.md 단방향 가져오기 (D-T03-11/12/13, AC-15)
# ─────────────────────────────────────────────────────────────────────────────

_LEGACY_TABLE_HEADER = ["#", "시점", "단계", "카테고리", "내용", "결과"]
_LEGACY_CATEGORY_KIND = {"DECISION": "decision", "GATE": "validation"}


def _split_table_row(line):
    if not line.lstrip().startswith("|"):
        return None
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_separator_row(cells):
    return all(set(c) <= set("-: ") for c in cells)


def _parse_legacy_agentic_log(text):
    """`## 대행 일지` 6열 표(D-T03-12 V1 변종)의 헤더 행을 정확히 식별하고,
    그 아래 데이터 행 중 `시점`이 `YYYY-MM-DD HH:mm`을 만족하는 행만 후보로
    반환한다. `## 요약` 2열 표, V2 4열 표, V3 자유 서술, V4 불릿은 인식하지
    않는다 — 위치 기반 파싱은 다른 표의 열을 잘못 흡수해 정규화를 오염시킨다."""
    rows = []
    inside = False
    for idx, line in enumerate(text.splitlines(), start=1):
        cells = _split_table_row(line)
        if cells == _LEGACY_TABLE_HEADER:
            inside = True
            continue
        if cells is None:
            inside = False
            continue
        if not inside:
            continue
        if _is_separator_row(cells):
            continue
        if len(cells) != 6:
            inside = False
            continue
        ts = cells[1]
        if not _LEGACY_TIMESTAMP_RE.match(ts):
            continue
        rows.append((idx, {
            "num": cells[0], "timestamp": ts, "stage": cells[2],
            "category": cells[3], "content": cells[4], "result": cells[5],
        }))
    return rows


def _build_legacy_event(row, line_no, rel_path):
    normalized = "|".join([row["num"], row["timestamp"], row["stage"],
                            row["category"], row["content"], row["result"]])
    sha = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    locator = f"{rel_path}#L{line_no}"
    timestamp = _legacy_kst_to_utc_ms(row["timestamp"])
    kind = _LEGACY_CATEGORY_KIND.get(row["category"], "progress")
    event = {
        "event": "activity",
        "actor": {"kind": "PM", "id": "legacy-import", "provider": None, "session_id": None},
        "provenance": {
            "type": "import",
            "recorded_by": {"kind": "tool", "id": "run-log-tool"},
            "worker_log_token_id": None,
            "source": {
                "kind": "legacy_line", "id": rel_path, "sha256": sha,
                "observed_at": None, "locator": locator, "upstream_event_id": None,
            },
        },
        "stage": row["stage"] or None,
        "summary": row["content"] or f"{row['stage']} {row['category']}",
        "timestamp": timestamp,
        "data": {"kind": kind, "category": row["category"], "result": row["result"]},
    }
    key = f"{rel_path}|{locator}|{sha}"
    request_id = "imp_" + hashlib.sha256(key.encode("utf-8")).hexdigest()
    return event, request_id


def _run_import_batch(task_dir, run_id, candidates, dry_run, lock_held, lock_timeout_ms, sources=None):
    """candidates(list of (event, request_id))를 append()로 위임해 실행한다.
    dry_run이면 append를 호출하지 않고 기존 request_id 집합과의 대조만으로
    scanned/imported/skipped_idempotent를 계산한다(D-T03-12 정의: scanned ==
    imported + skipped_idempotent)."""
    scanned = len(candidates)

    def _do():
        nonlocal scanned
        existing_ids = _existing_request_ids(task_dir, run_id)
        imported = 0
        skipped = 0
        seen = set()
        for event, request_id in candidates:
            if request_id in existing_ids or request_id in seen:
                skipped += 1
                seen.add(request_id)
                continue
            if dry_run:
                imported += 1
                seen.add(request_id)
                continue
            evt = dict(event)
            evt["request_id"] = request_id
            result = append(str(task_dir), run_id, evt, lock_held=True, lock_timeout_ms=lock_timeout_ms)
            if not result.get("ok"):
                if result.get("error", {}).get("code") == "event_too_large":
                    # GC-209: 원본 행 1개가 16 KiB를 넘는다고 배치 전체를 영구
                    # 차단하지 않는다 — 그 행만 건너뛰고 나머지를 계속 가져온다.
                    # 새 집계 필드(예: skipped_invalid)를 만들면 surfaces.json의
                    # ok 응답 필드가 늘어나 MV-30 3자산 개정이 발생하므로,
                    # D-T03-12의 기존 정의("scanned == 원본에서 인식한 사건
                    # 후보 수")를 그대로 써서 이 행을 후보에서 제외한다 — 시각
                    # 형식이 맞지 않는 legacy 행을 scanned에서 빼는 것과 같은
                    # 처리다. 조용히 삼키지 않도록 stderr에 위치자를 남긴다.
                    scanned -= 1
                    source = (evt.get("provenance") or {}).get("source") or {}
                    locator = source.get("locator")
                    print(f"run-log-tool: 원본 행을 건너뜁니다(event_too_large): "
                          f"{locator or request_id}", file=sys.stderr)
                    seen.add(request_id)
                    continue
                return result
            data = result["data"]
            if data.get("idempotent_hit"):
                skipped += 1
            else:
                imported += 1
            seen.add(request_id)
        if sources is None:
            return ok(scanned=scanned, imported=imported, skipped_idempotent=skipped)
        return ok(scanned=scanned, imported=imported, skipped_idempotent=skipped, sources=sources)

    return _with_lock(task_dir, lock_held, lock_timeout_ms, _do)


def import_agentic(task_path, run_id=None, *, dry_run=False, lock_held=False,
                    lock_timeout_ms=DEFAULT_LOCK_TIMEOUT_MS):
    """legacy `<task-path>/AGENTIC-LOG.md`를 단방향·멱등으로 표준 사건(조합 A8)으로
    가져온다. 완료 게이트 불기여(집행은 T11 소관). 역변환하지 않는다."""
    path_err = require_absolute(task_path)
    if path_err:
        return path_err
    task_dir = pathlib.Path(task_path)

    resolved_run_id, run_id_err = _resolve_import_run_id(task_dir, run_id)
    if run_id_err:
        return run_id_err

    source_path = task_dir / "AGENTIC-LOG.md"
    escape_err = _reject_symlink_or_escape(task_dir, source_path)
    if escape_err:
        return escape_err
    if not source_path.exists():
        return err("run_log_missing", detail=f"{source_path} 부재")

    raw, read_err = _safe_read_bytes(source_path)
    if read_err:
        return read_err
    if raw is None:
        return err("run_log_missing", detail=f"{source_path} 부재")
    # GC-206: legacy 원본은 인코딩이 제각각일 수 있다 — 가져오기는 최선 노력이므로
    # 디코딩 실패로 죽지 않고 손실 허용 치환으로 흡수한다.
    text = raw.decode("utf-8", errors="replace")
    rel_path = source_path.name

    candidates = []
    for line_no, row in _parse_legacy_agentic_log(text):
        try:
            candidates.append(_build_legacy_event(row, line_no, rel_path))
        except (ValueError, OverflowError):
            # GC-203: 정규식은 자릿수만 보므로 달력상 불가능한 시각(예:
            # "2026-13-45 99:99")이 통과할 수 있다 — 그런 행은 변환 시점에
            # 건너뛰고 배치 전체를 죽이지 않는다.
            continue

    return _run_import_batch(task_dir, resolved_run_id, candidates, dry_run,
                              lock_held, lock_timeout_ms)


# ─────────────────────────────────────────────────────────────────────────────
# Project Loop `.oppl-run/` 단방향 가져오기 (D-T03-14/15, AC-15)
# ─────────────────────────────────────────────────────────────────────────────

_OPPL_JOURNAL_HEADER = ["시각", "단계", "이벤트", "근거"]
_OPPL_JOURNAL_KIND = {"start": "progress", "end": "progress",
                      "gate-verdict": "validation", "retry": "retry"}


def _parse_oppl_journal(text):
    rows = []
    inside = False
    for idx, line in enumerate(text.splitlines(), start=1):
        cells = _split_table_row(line)
        if cells == _OPPL_JOURNAL_HEADER:
            inside = True
            continue
        if cells is None:
            inside = False
            continue
        if not inside:
            continue
        if _is_separator_row(cells):
            continue
        if len(cells) != 4:
            inside = False
            continue
        rows.append((idx, {"timestamp": cells[0], "stage": cells[1],
                            "event": cells[2], "reason": cells[3]}))
    return rows


def _build_oppl_journal_event(row, line_no, rel_path):
    normalized = "|".join([row["timestamp"], row["stage"], row["event"], row["reason"]])
    sha = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    locator = f"{rel_path}#L{line_no}"
    kind = _OPPL_JOURNAL_KIND.get(row["event"], "progress")
    event = {
        "event": "activity",
        "actor": {"kind": "PM", "id": "oppl-import", "provider": None, "session_id": None},
        "provenance": {
            "type": "import",
            "recorded_by": {"kind": "tool", "id": "run-log-tool"},
            "worker_log_token_id": None,
            "source": {
                "kind": "oppl_event", "id": rel_path, "sha256": sha,
                "observed_at": None, "locator": locator, "upstream_event_id": None,
            },
        },
        "stage": row["stage"] or None,
        "summary": row["reason"] or f"{row['stage']} {row['event']}",
        "timestamp": row["timestamp"] if _valid_rfc3339_ms(row["timestamp"]) else None,
        "data": {"kind": kind, "journal_event": row["event"]},
    }
    if event["timestamp"] is None:
        event.pop("timestamp")
    key = f"{rel_path}|{locator}|{sha}"
    request_id = "imp_" + hashlib.sha256(key.encode("utf-8")).hexdigest()
    return event, request_id


def _build_oppl_result_event(obj, phase, rel_path, sha, locator):
    upstream = obj.get("uuid")
    data = {
        "kind": "progress", "phase": phase,
        "subtype": obj.get("subtype"), "is_error": obj.get("is_error"),
        "duration_ms": obj.get("duration_ms"), "num_turns": obj.get("num_turns"),
        "session_id": obj.get("session_id"),
    }
    if "exitcode" in obj:
        data["exitcode"] = obj.get("exitcode")
    event = {
        "event": "activity",
        "actor": {"kind": "PM", "id": "oppl-import", "provider": None, "session_id": None},
        "provenance": {
            "type": "import",
            "recorded_by": {"kind": "tool", "id": "run-log-tool"},
            "worker_log_token_id": None,
            "source": {
                "kind": "oppl_event", "id": rel_path, "sha256": sha,
                "observed_at": None, "locator": locator, "upstream_event_id": upstream,
            },
        },
        "stage": phase,
        "summary": f"{phase} 결과: {obj.get('subtype')}",
        "data": data,
    }
    key = f"{rel_path}|{upstream if upstream is not None else locator}|{sha}"
    request_id = "imp_" + hashlib.sha256(key.encode("utf-8")).hexdigest()
    return event, request_id


def _build_oppl_exitcode_event(phase, exitcode, rel_path, sha, locator):
    event = {
        "event": "activity",
        "actor": {"kind": "PM", "id": "oppl-import", "provider": None, "session_id": None},
        "provenance": {
            "type": "import",
            "recorded_by": {"kind": "tool", "id": "run-log-tool"},
            "worker_log_token_id": None,
            "source": {
                "kind": "oppl_event", "id": rel_path, "sha256": sha,
                "observed_at": None, "locator": locator, "upstream_event_id": None,
            },
        },
        "stage": phase,
        "summary": f"{phase} exitcode={exitcode}",
        "data": {"kind": "progress", "phase": phase, "exitcode": exitcode},
    }
    key = f"{rel_path}|{locator}|{sha}"
    request_id = "imp_" + hashlib.sha256(key.encode("utf-8")).hexdigest()
    return event, request_id


def _all_oppl_candidates(oppl_dir, task_dir):
    """`.oppl-run/`의 이원 구조를 D-T03-14 3규칙으로 정규화한다. 반환값은
    (candidates, source_paths_in_order) — candidates는 (event, request_id, rel_path).

    각 원본 파일은 읽기 전 `_reject_symlink_or_escape()`로 경계를 확인하고
    `_safe_read_bytes()`(O_NOFOLLOW)로 읽는다(GC-201/202 — GC-103 방어 이식).
    거부된 파일은 `sources[]`에도 오르지 않는다 — 실제로 소비하지 않았기 때문이다."""
    candidates = []
    source_order = []

    journal_path = oppl_dir / "journal.md"
    if _reject_symlink_or_escape(task_dir, journal_path) is None and journal_path.exists():
        raw, read_err = _safe_read_bytes(journal_path)
        if read_err is None and raw is not None:
            rel_path = str(journal_path.relative_to(task_dir))
            # GC-206: journal.md도 legacy와 같은 이유로 최선 노력 디코딩을 쓴다.
            text = raw.decode("utf-8", errors="replace")
            rows = _parse_oppl_journal(text)
            if rows:
                source_order.append(rel_path)
            for line_no, row in rows:
                event, request_id = _build_oppl_journal_event(row, line_no, rel_path)
                candidates.append((event, request_id, rel_path))

    phases_with_result = set()

    for result_path in sorted(oppl_dir.glob("*.result.json")):
        if _reject_symlink_or_escape(task_dir, result_path) is not None:
            continue
        phase = result_path.name[: -len(".result.json")]
        rel_path = str(result_path.relative_to(task_dir))
        raw, read_err = _safe_read_bytes(result_path)
        if read_err is not None or raw is None:
            continue
        try:
            obj = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
            # GC-204/205/206: 원본이 object가 아니거나(뒤 isinstance 검사),
            # UTF-8이 아니거나, 적대적으로 깊게 중첩됐을 수 있다 — 해당 파일만
            # 건너뛰고 배치 전체를 죽이지 않는다.
            continue
        if not isinstance(obj, dict):
            continue
        sha = hashlib.sha256(raw).hexdigest()
        event, request_id = _build_oppl_result_event(obj, phase, rel_path, sha, f"{rel_path}#L1")
        candidates.append((event, request_id, rel_path))
        source_order.append(rel_path)
        phases_with_result.add(phase)

    for events_path in sorted(oppl_dir.glob("*.events.jsonl")):
        if _reject_symlink_or_escape(task_dir, events_path) is not None:
            continue
        phase = events_path.name[: -len(".events.jsonl")]
        rel_path = str(events_path.relative_to(task_dir))
        raw, read_err = _safe_read_bytes(events_path)
        if read_err is not None or raw is None:
            continue
        text = raw.decode("utf-8", errors="replace")
        found_result = False
        for line_no, raw_line in enumerate(text.splitlines(), start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                rec = json.loads(stripped)
            except (json.JSONDecodeError, RecursionError):
                continue
            if not isinstance(rec, dict) or rec.get("type") != "result":
                continue
            found_result = True
            sha = hashlib.sha256(stripped.encode("utf-8")).hexdigest()
            event, request_id = _build_oppl_result_event(
                rec, phase, rel_path, sha, f"{rel_path}#L{line_no}")
            candidates.append((event, request_id, rel_path))
        if found_result:
            source_order.append(rel_path)
            phases_with_result.add(phase)

    for exitcode_path in sorted(oppl_dir.glob("*.exitcode")):
        if _reject_symlink_or_escape(task_dir, exitcode_path) is not None:
            continue
        phase = exitcode_path.name[: -len(".exitcode")]
        if phase in phases_with_result:
            # 짝이 있는 종료 마커는 수집하지 않는다(D-T03-14 ③은 짝 결과 파일
            # 부재 시에만 적용) — 이미 rule②가 이 단계의 종료를 표준화했다.
            continue
        rel_path = str(exitcode_path.relative_to(task_dir))
        raw, read_err = _safe_read_bytes(exitcode_path)
        if read_err is not None or raw is None:
            continue
        try:
            exitcode = int(raw.decode("utf-8", errors="replace").strip())
        except ValueError:
            continue
        sha = hashlib.sha256(raw).hexdigest()
        event, request_id = _build_oppl_exitcode_event(phase, exitcode, rel_path, sha, f"{rel_path}#L1")
        candidates.append((event, request_id, rel_path))
        source_order.append(rel_path)

    seen_paths = set()
    ordered_unique = []
    for p in source_order:
        if p not in seen_paths:
            seen_paths.add(p)
            ordered_unique.append(p)

    return candidates, ordered_unique


def import_oppl(task_path, run_id=None, *, dry_run=False, lock_held=False,
                 lock_timeout_ms=DEFAULT_LOCK_TIMEOUT_MS):
    """`<task-path>/.oppl-run/`(비동기 축 `<phase>.events.jsonl`+`journal.md`,
    동기 축 `<phase>.result.json`, 종료 마커 `<phase>.exitcode`)를 단방향·멱등으로
    표준 사건(조합 A8)으로 가져온다. `*.prompt.txt`·`*.probe.*`·`*.err.log`·
    `session.json`은 수집하지 않는다(AC-14, D-T03-15). 완료 게이트 불기여."""
    path_err = require_absolute(task_path)
    if path_err:
        return path_err
    task_dir = pathlib.Path(task_path)

    resolved_run_id, run_id_err = _resolve_import_run_id(task_dir, run_id)
    if run_id_err:
        return run_id_err

    oppl_dir = task_dir / ".oppl-run"
    escape_err = _reject_symlink_or_escape(task_dir, oppl_dir)
    if escape_err:
        return escape_err
    if not oppl_dir.exists() or not oppl_dir.is_dir():
        return err("run_log_missing", detail=f"{oppl_dir} 부재")

    candidates_with_path, ordered_paths = _all_oppl_candidates(oppl_dir, task_dir)
    candidates = [(event, request_id) for event, request_id, _rel in candidates_with_path]

    counts = {}
    for _event, _request_id, rel in candidates_with_path:
        counts[rel] = counts.get(rel, 0) + 1
    # sources[]는 실제로 소비한 파일만 싣는다 — _all_oppl_candidates()가 이미
    # 경계·링크를 확인한 경로만 ordered_paths에 넣으므로 여기서 다시 거부할
    # 파일은 없지만, 안전 읽기(O_NOFOLLOW)는 재확인 차원에서 그대로 유지한다.
    sources = []
    for p in ordered_paths:
        raw, read_err = _safe_read_bytes(task_dir / p)
        if read_err is not None or raw is None:
            continue
        sources.append({"path": p, "sha256": hashlib.sha256(raw).hexdigest(),
                         "scanned": counts.get(p, 0)})

    return _run_import_batch(task_dir, resolved_run_id, candidates, dry_run,
                              lock_held, lock_timeout_ms, sources=sources)
