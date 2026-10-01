# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool_parts.base",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "state-tool 공통 기반 — 전이 필드 보조, 출력·오류, 외부 모듈 로더, 상태 파일 I/O",
  "exports": [
    "ok",
    "err",
    "get_kst_datetime",
    "_import_run_log_core",
    "_import_ownership_lease",
    "load_state_json",
    "save_state_json"
  ]
}
"""

import fcntl
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager

from .codes import (
    AWAIT_USER_ERROR_CODES,
    DESIGN_GATE_ERROR_CODES,
    ERROR_CODES,
    OPD2_GATE_ERROR_CODES,
    RUN_LOG_STATE_ERROR_CODES,
    TASK_COMPLETE_STATUSES,
    TEST_CYCLE_ERROR_CODES,
    TRANSITION_ACTIONS,
    can_auto_approve_user_confirmation,
)


def _transition_from_state(state):
    """Return (transition_action, report_type, next_action) for the current frontier."""
    current_status = state.get("current_status")
    next_action = state.get("next_action") or _derive_next_action(state)
    if current_status == "blocked":
        return "blocked", "decision_request", next_action
    if current_status in TASK_COMPLETE_STATUSES:
        return "complete", "progress_report", next_action

    mode = state.get("mode")
    rows = state.get("rows", [])
    for idx, row in enumerate(rows):
        if row.get("status") in _COMPLETE_STATUSES:
            continue
        if row.get("status") == "failed":
            return "blocked", "decision_request", next_action
        if row.get("item") == "사용자 확인":
            allowed, _ = can_auto_approve_user_confirmation(row.get("stage"), mode)
            if allowed:
                continue
            return "await_user", "decision_request", next_action
        if row.get("stage") == "CLOSE":
            first_close = idx == 0 or rows[idx - 1].get("stage") != "CLOSE"
            if first_close:
                allowed, _ = can_auto_approve_user_confirmation("CLOSE", mode)
                if not allowed:
                    return "await_user", "decision_request", next_action
        return "continue", "progress_report", next_action

    return "complete", "progress_report", next_action


def _transition_from_error(payload):
    code = payload.get("error")
    if code in AWAIT_USER_ERROR_CODES:
        return "await_user", "decision_request"
    return "blocked", "decision_request"


def _state_supports_transition_output(state):
    if state.get("current_status") in {"blocked", *TASK_COMPLETE_STATUSES}:
        return True
    return any(
        row.get("key") or row.get("item") == "사용자 확인"
        for row in state.get("rows", [])
    )


def _with_transition_fields(payload):
    """Add Task 136 transition fields without changing the single-line JSON contract."""
    if pathlib.Path(sys.argv[0]).name != "state_tool.py":
        payload.pop("_transition_state", None)
        return payload
    if payload.get("transition_action") not in TRANSITION_ACTIONS:
        state = payload.get("_transition_state")
        if isinstance(state, dict):
            if not _state_supports_transition_output(state):
                payload.pop("_transition_state", None)
                return payload
            action, report_type, next_action = _transition_from_state(state)
            payload.setdefault("transition_action", action)
            payload.setdefault("report_type", report_type)
            payload.setdefault("next_action", next_action)
        elif payload.get("ok") is False:
            action, report_type = _transition_from_error(payload)
            payload.setdefault("transition_action", action)
            payload.setdefault("report_type", report_type)
            payload.setdefault(
                "next_action",
                payload.get("required_action") or payload.get("message") or payload.get("error"),
            )
    if payload.get("transition_action") in TRANSITION_ACTIONS:
        payload.setdefault(
            "report_type",
            "decision_request" if payload["transition_action"] in ("await_user", "blocked")
            else "progress_report",
        )
        payload.setdefault("next_action", payload.get("next_action") or "-")
    payload.pop("_transition_state", None)
    return payload


def ok(command, **kwargs):
    """성공 응답 — 단일 라인 JSON, exit 0"""
    payload = {"ok": True, "command": command, **kwargs}
    print(json.dumps(_with_transition_fields(payload), ensure_ascii=False, default=str))

def _error_template(code):
    """Look up legacy, run-log, design-gate, then TEST-cycle error templates.

    두 테이블에 같은 키가 있으면 `ERROR_CODES`(상태 도구 자기 계약)가 선순위다 —
    이 딕셔너리 리터럴 자체는 어느 경로로도 변경되지 않는다(T02 QA-SPEC F-4).
    두 테이블 모두에 없으면 `None`을 반환한다 — 호출자(`err()`)가 이 미등록
    신호로 `.format()` 호출 자체를 건너뛴다(GC-008: 미등록 코드 문자열이
    포맷 문자열로 오인되는 사고를 막는다).
    """
    if code in ERROR_CODES:
        return ERROR_CODES[code]
    if code in RUN_LOG_STATE_ERROR_CODES:
        return RUN_LOG_STATE_ERROR_CODES[code]
    if code in DESIGN_GATE_ERROR_CODES:
        return DESIGN_GATE_ERROR_CODES[code]
    if code in TEST_CYCLE_ERROR_CODES:
        return TEST_CYCLE_ERROR_CODES[code]
    if code in OPD2_GATE_ERROR_CODES:
        return OPD2_GATE_ERROR_CODES[code]
    return None

def err(command, code, message=None, exit_code=1, **kwargs):
    """에러 응답 — 단일 라인 JSON, exit {exit_code}
    code는 ERROR_CODES 또는 RUN_LOG_STATE_ERROR_CODES 키 중 하나여야 한다 (§2.18 SSOT + D-A).
    추가 필드(kwargs)로 에러 컨텍스트(row_id, stage 등)를 포함한다.
    """
    if message is None:
        template = _error_template(code)
        if template is None:
            # 미등록 코드 — code 문자열 자체를 메시지로 쓰고 .format()은 건너뛴다(GC-008).
            message = code
        else:
            try:
                message = template.format(**kwargs)
            except (KeyError, IndexError):
                message = template
    payload = {"ok": False, "command": command, "error": code, "message": message}
    payload.update(kwargs)
    print(json.dumps(_with_transition_fields(payload), ensure_ascii=False, default=str))
    sys.exit(exit_code)


def _rl_err(command, code, message=None, exit_code=1, **kwargs):
    """CONTRACT §2.1 공통 응답 봉투 — run-log 계열 전용 **중첩** 오류 객체.

    기존 22종 도구의 평면 봉투(`err()`, `{"ok": false, "error": "<code>", ...}`)와
    의도적으로 다르다 — CONTRACT §2.1은 run-log 계열이 `error.code`/`error.message`/
    `error.detail`로 분리된 객체를 반환하도록 확정했고("기존 도구는 이 형태로
    이전하지 않는다"), 그 경계는 "run-log 계열 신규 표면인가"다(§2.1). 이 함수는
    `log-event`/`gate-request`/`gate-resolve` 3개 신규 표면 전용이며, 기존
    서브커맨드는 여전히 `err()`의 평면 봉투를 그대로 쓴다(C-2 기존 동작 보존).
    """
    if message is None:
        template = _error_template(code)
        if template is None:
            message = code
        else:
            try:
                message = template.format(**kwargs)
            except (KeyError, IndexError):
                message = template
    payload = {"ok": False, "command": command,
               "error": {"code": code, "message": message, "detail": kwargs}}
    print(json.dumps(payload, ensure_ascii=False, default=str))
    sys.exit(exit_code)

# ─────────────────────────────────────────────────────────────────────────────
# 시점 취득 (PLAN §2.11 G-5, TASK T-5)
# ─────────────────────────────────────────────────────────────────────────────

# 시각 문자열 형식 — 초 해상도가 1순위, 분 해상도가 하위호환 폴백이다 (103 R-19).
TS_PATTERN_SEC = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
TS_PATTERN_MIN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


def _date_js_path():
    """date.js 실경로 — 형제 배치(`<tools>/date/date.js`) 우선, 없으면 배포본.

    배포 레이아웃(`~/.opal/tools/state-tool/`)에서는 형제 경로가 곧
    `~/.opal/tools/date/date.js`라 종전과 동일하게 해석된다. 레포 소스에서
    직접 실행할 때만 레포의 date.js를 쓰게 되어, 배포 전 검증이 가능하다.
    """
    sibling = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.pardir, "date", "date.js")
    sibling = os.path.normpath(sibling)
    if os.path.exists(sibling):
        return sibling
    return os.path.expanduser("~/.opal/tools/date/date.js")


def _run_log_core_dir():
    """run-log-tool 실경로 — 형제 배치(`<tools>/run-log-tool/`) 우선, 없으면 배포본.

    `_date_js_path()`와 동일한 관례다(D-C) — 배포 레이아웃(`~/.opal/tools/state-tool/`)
    에서는 형제 경로가 곧 `~/.opal/tools/run-log-tool`이라 종전과 동일하게 해석되고,
    레포 소스에서 직접 실행할 때만 레포의 run-log-tool을 쓰게 되어 배포 전 검증이
    가능하다.
    """
    sibling = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.pardir, "run-log-tool")
    sibling = os.path.normpath(sibling)
    if os.path.isdir(sibling):
        return sibling
    return os.path.expanduser("~/.opal/tools/run-log-tool")


_RUN_LOG_CORE_MODULE_CACHE = {}


def _import_run_log_core():
    """기록 코어를 같은 프로세스에서 단일 모듈로 적재한다 (TRD D-5 인프로세스 호출, D-C).

    하위 프로세스로 호출하지 않는다 — 하위 프로세스는 락을 재획득하려 해 D-4와
    충돌한다(TRD §동시성과 실패 모델). `sys.path`는 건드리지 않는다(GC-007) —
    `sys.path.insert(0, ...)`는 이후 프로세스 전체의 모든 import 탐색 순서를
    오염시켜 무관한 모듈이 이 디렉터리를 먼저 보게 만든다. 대신
    `importlib.util.spec_from_file_location`으로 `run_log_core.py` 파일 하나만
    지정 로드한다 — 디렉터리명에 하이픈이 있어 패키지 import가 불가능한 문제도
    이 방식이 같이 해소한다. 모듈 경로별로 캐시해 같은 프로세스 안 반복 호출이
    매번 다시 적재하지 않게 한다.
    """
    core_dir = _run_log_core_dir()
    module_path = os.path.join(core_dir, "run_log_core.py")
    cached = _RUN_LOG_CORE_MODULE_CACHE.get(module_path)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("run_log_core", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _RUN_LOG_CORE_MODULE_CACHE[module_path] = module
    return module


# ─────────────────────────────────────────────────────────────────────────────
# 138 W-9 — 세션 소유권 lease 연동 (C-9, AC-12, AC-13, AC-27)
#
# 기존 전이 계약은 무변경이다 — 아래 어떤 실패도 state 갱신을 막지 않고 stderr
# 경고 1줄만 남긴다(fail-safe). 플랫폼 고유 세션 변수명은 ownership-tool의
# 어댑터가 단독 소유하므로(C-15) 이 모듈은 OPAL 중립 변수 하나만 읽는다.
# ─────────────────────────────────────────────────────────────────────────────

def _ownership_warn(code, message):
    """단일 라인 JSON 경고를 stderr로 낸다 (init --rows-from deprecated 경고 선례)."""
    print(json.dumps({"warning": code, "message": message}, ensure_ascii=False),
          file=sys.stderr)


def _current_session_id():
    """공통 ownership resolver로 중립·플랫폼 세션 신원을 해석한다."""
    try:
        return _import_ownership_lease().ownership_core.resolve_session_id(os.environ)
    except (ImportError, OSError, AttributeError) as exc:
        _ownership_warn("ownership_import_failed", str(exc))
        return None


def _ownership_tool_dir():
    """ownership-tool 실경로 — 형제 배치 우선, 없으면 배포본(`_run_log_core_dir()`와 동일 관례, D-C)."""
    sibling = os.path.normpath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.pardir, "ownership-tool"))
    if os.path.isdir(sibling):
        return sibling
    return os.path.expanduser("~/.opal/tools/ownership-tool")


_OWNERSHIP_LEASE_MODULE_CACHE = {}
_OWNERSHIP_FINGERPRINT_MODULE_CACHE = {}


def _import_ownership_lease():
    """`ownership_tool.lease`를 `sys.path` 오염 없이 적재한다 (GC-007 관례).

    `lease.py`는 `from . import ownership_core` 상대 import를 쓰므로 단일 파일
    적재로는 부족하다 — 패키지 `ownership_tool`을 `submodule_search_locations`와
    함께 먼저 등록한 뒤 하위 모듈을 적재한다. 디렉터리명에 하이픈이 있어 일반
    패키지 import가 불가능한 점도 이 방식이 해소한다. 적재 실패는 호출자가
    예외로 받는다.
    """
    pkg_dir = os.path.join(_ownership_tool_dir(), "ownership_tool")
    cached = _OWNERSHIP_LEASE_MODULE_CACHE.get(pkg_dir)
    if cached is not None:
        return cached
    pkg_spec = importlib.util.spec_from_file_location(
        "ownership_tool", os.path.join(pkg_dir, "__init__.py"),
        submodule_search_locations=[pkg_dir])
    pkg = importlib.util.module_from_spec(pkg_spec)
    sys.modules["ownership_tool"] = pkg
    pkg_spec.loader.exec_module(pkg)
    lease_spec = importlib.util.spec_from_file_location(
        "ownership_tool.lease", os.path.join(pkg_dir, "lease.py"))
    lease = importlib.util.module_from_spec(lease_spec)
    sys.modules["ownership_tool.lease"] = lease
    lease_spec.loader.exec_module(lease)
    _OWNERSHIP_LEASE_MODULE_CACHE[pkg_dir] = lease
    return lease


def _import_ownership_fingerprint():
    """`ownership_tool.fingerprint`를 형제 도구의 모듈 API로 적재한다.

    Stop receipt는 ownership-tool의 런타임 저장소다. state-tool은 그 경로를
    직접 열거나 편집하지 않고, lease 적재와 같은 패키지 적재 경계를 통해 이
    모듈의 ``load_receipt``/``save_receipt`` API만 호출한다(W-7, §3.1).
    """
    pkg_dir = os.path.join(_ownership_tool_dir(), "ownership_tool")
    cached = _OWNERSHIP_FINGERPRINT_MODULE_CACHE.get(pkg_dir)
    if cached is not None:
        return cached

    # 전이 진입 시 lease가 먼저 적재된 경우에는 그 패키지 객체를 재사용한다.
    # 그렇지 않은 경로(log-event/gate 표면)도 독립적으로 동작하도록 패키지를
    # 먼저 등록한다. 이는 _import_ownership_lease()의 hyphen-directory 우회와
    # 같은 관례이며 sys.path를 변경하지 않는다.
    pkg = sys.modules.get("ownership_tool")
    if pkg is None or pkg_dir not in list(getattr(pkg, "__path__", []) or []):
        pkg_spec = importlib.util.spec_from_file_location(
            "ownership_tool", os.path.join(pkg_dir, "__init__.py"),
            submodule_search_locations=[pkg_dir])
        pkg = importlib.util.module_from_spec(pkg_spec)
        sys.modules["ownership_tool"] = pkg
        pkg_spec.loader.exec_module(pkg)

    fingerprint_spec = importlib.util.spec_from_file_location(
        "ownership_tool.fingerprint", os.path.join(pkg_dir, "fingerprint.py"))
    fingerprint = importlib.util.module_from_spec(fingerprint_spec)
    sys.modules["ownership_tool.fingerprint"] = fingerprint
    fingerprint_spec.loader.exec_module(fingerprint)
    _OWNERSHIP_FINGERPRINT_MODULE_CACHE[pkg_dir] = fingerprint
    return fingerprint


def _claim_task_lease_if_needed(task_path):
    """상태 전이 진입 경계에서 이 세션의 task lease를 1회 원자 생성한다 (W-9).

    claim 자체가 멱등이라(같은 세션 재-claim은 heartbeat 갱신) 같은 세션의 반복
    호출은 lease를 새로 만들지 않는다. 다른 세션의 live lease가 있으면 claim은
    `foreign_owner`로 실패하지만 이 역시 전이를 막지 않는다 — 소유권 집행은 stop
    hook 축의 책임이고 state-tool은 기록 축이다.

    claim 주체 루트로 `os.getcwd()`를 넘긴다(150 W-5) — lease가 이관 대기
    (`handoff_pending`)인 태스크는 이 루트가 이관 대상 워크트리 루트와 realpath
    동치이거나 그 하위일 때만 claim이 성립하므로, 허브의 재-claim은 `handoff_pending`
    거부가 되어 이관이 되돌려지지 않고(H-2) 워크트리 cwd의 전이는 SessionStart가
    실패했더라도 이관을 소비해 자가 치유된다. 그 거부는 `foreign_owner`와 **완전히
    동일한** fail-safe 경로로 접혀 stderr 경고 1줄만 남기고 전이를 통과시킨다 —
    응답 JSON 키 집합·종료코드·state.json 산출물은 불변이고(C-6, AC-10) 집행자는
    PreToolUse 쓰기 가드 하나다(state-tool은 판정 지점을 늘리지 않는다).

    반환값은 관측용 dict(`{"claimed": bool, "warning": str|None}`)이며 응답 JSON에
    싣지 않는다 — advance/mark 응답 키 집합을 바꾸지 않기 위해서다(C-3 취지).
    """
    # Distinguish an unavailable ownership module from a genuinely absent
    # session ID.  _current_session_id() is fail-safe and returns None for
    # both, so loading the module first preserves the actionable warning.
    try:
        lease = _import_ownership_lease()
    except Exception as exc:                      # noqa: BLE001 — fail-safe 경계
        warning = "ownership_claim_failed"
        _ownership_warn(warning,
                        f"task lease claim 실패({exc.__class__.__name__}: {exc}). "
                        "상태 전이는 그대로 진행됩니다.")
        return {"claimed": False, "warning": warning}

    session_id = _current_session_id()
    if session_id is None:
        warning = "ownership_session_id_missing"
        _ownership_warn(warning,
                        "해석 가능한 session ID가 없어 task lease를 claim하지 않았습니다. "
                        "상태 전이는 그대로 진행됩니다.")
        return {"claimed": False, "warning": warning}
    try:
        result = lease.claim(str(task_path), session_id=session_id,
                             claim_source="state_transition",
                             claimant_root=os.getcwd())
    except Exception as exc:                      # noqa: BLE001 — fail-safe 경계
        warning = "ownership_claim_failed"
        _ownership_warn(warning,
                        f"task lease claim 실패({exc.__class__.__name__}: {exc}). "
                        "상태 전이는 그대로 진행됩니다.")
        return {"claimed": False, "warning": warning}
    if not isinstance(result, dict) or not result.get("ok"):
        warning = "ownership_claim_skipped"
        diagnostic = result.get("diagnostic") if isinstance(result, dict) else None
        _ownership_warn(warning,
                        f"task lease를 claim하지 않았습니다(diagnostic={diagnostic}). "
                        "상태 전이는 그대로 진행됩니다.")
        return {"claimed": False, "warning": warning, "diagnostic": diagnostic}
    return {"claimed": True, "warning": None}


def _run_date_js(date_js, fmt):
    """date.js 1회 호출 → (returncode, stdout, stderr). 예외는 호출자가 처리한다."""
    result = subprocess.run(
        ["node", date_js, fmt],
        capture_output=True, text=True, timeout=10
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_kst_datetime(command="(unknown)"):
    """date.js 호출 → KST `YYYY-MM-DD HH:mm:ss` 반환 (103 R-19).

    `datetime-sec`(초 해상도)를 먼저 요청하고, 응답이 형식에 맞지 않으면
    `datetime`(분 해상도)으로 폴백한다 — date.js가 아직 `datetime-sec`를
    모르는 배포본이면 사용법 안내를 exit 0으로 출력하므로, 반환값 형식 검사가
    지원 여부 판정을 겸한다. 폴백 값은 종전과 바이트 동일한 분 해상도 문자열이며
    스키마·집계 양쪽이 두 형식을 모두 수용한다.

    두 형식 모두 얻지 못하면 date_tool_failed 에러 응답 후 exit 2.
    """
    date_js = _date_js_path()
    try:
        code, out, stderr = _run_date_js(date_js, "datetime-sec")
        if code == 0 and TS_PATTERN_SEC.match(out):
            return out

        code, out, stderr = _run_date_js(date_js, "datetime")
        if code == 0 and TS_PATTERN_MIN.match(out):
            return out

        err(command, "date_tool_failed",
            message=f"exit={code}, stderr={stderr}",
            exit_code=2)
    except Exception as e:
        err(command, "date_tool_failed", message=str(e), exit_code=2)

# ─────────────────────────────────────────────────────────────────────────────
# 파일 I/O 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def resolve_task_path(task_path_str, command):
    """task-path 디렉토리 존재 검증. 미존재 시 task_path_not_found + exit 1."""
    p = pathlib.Path(task_path_str).resolve()
    if not p.is_dir():
        err(command, "task_path_not_found", path=str(p))
    return p


@contextmanager
def state_writer_lock(task_path):
    """Serialize state-tool writers across processes for one task."""
    lock_path = pathlib.Path(task_path) / ".state-tool.lock"
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(lock_path, flags, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

def load_state_json(task_path, command):
    """state.json 로드. 미존재 시 state_not_initialized + exit 1."""
    state_file = task_path / "state.json"
    if not state_file.exists():
        err(command, "state_not_initialized")
    with open(state_file, encoding="utf-8") as f:
        return json.load(f)

def _atomic_write_state_json(task_path, state):
    """tmp(같은 디렉터리) → fsync → os.replace 원자적 교체 (D-F).

    `opal/tools/memory-tool/memory_tool.py`의 `atomic_write_json()` 선례를 복제한다.
    run-log 초기화 경로(2단 커밋, D-E) 전용이며, 기존 `save_state_json()`은
    그대로 두어 `--run-log-mode` 미지정 경로가 이 함수를 타지 않게 한다(D-L).

    [MUST] `state["run_log"]["pending_events"]`가 있으면 디스크에 쓰기 **직전**
    각 사건을 `run_log_core.redact()`(공통 마스킹 초크포인트, D-9)에 통과시킨다.
    outbox(보관함)도 조각 파일과 동일하게 **원본 writer**이므로 D-9의 "모든 writer가
    공통 경로를 통과한다"가 이 경로에도 적용된다(GC-001) — 이 배치가 호출부에
    있지 않고 함수 안에 있으므로, 앞으로 이 함수를 호출하는 모든 코드가 자동으로
    초크포인트를 탄다(writer별 개별 마스킹 금지, D-9). `redact()`는 멱등이므로
    (이미 통과한 payload를 다시 통과시켜도 결과가 같다) 2단 커밋에서 같은 사건을
    중복 기재해도 안전하다.
    """
    run_log_block = state.get("run_log")
    if run_log_block and run_log_block.get("pending_events"):
        run_log_core = _import_run_log_core()
        run_log_block["pending_events"] = [
            run_log_core.redact(evt) for evt in run_log_block["pending_events"]
        ]

    state_file = pathlib.Path(task_path) / "state.json"
    # GC-101: 예측 가능한 tmp 이름(`state.json.tmp.{pid}`)은 그 이름으로 미리
    # 심볼릭 링크를 심어두는 경합에 노출된다 — 실측 재현: 링크 선점으로 임의
    # 파일을 state JSON으로 덮어쓰는 데 성공했다. `tempfile.mkstemp()`는 같은
    # 디렉터리에 예측 불가능한 이름을 `O_CREAT|O_EXCL`(+플랫폼이 지원하면
    # `O_NOFOLLOW`까지, CPython tempfile이 자동 부여)로 배타 생성해 이름
    # 선점 자체가 통하지 않게 한다. 생성 mode는 0600이며, `os.replace()`가
    # 이 tmp의 inode를 그대로 옮기므로 run-log 경로로 만든 `state.json`은
    # 0600이 된다(GC-004 잔여분) — `save_state_json()`을 쓰는 미지정 경로는
    # 이 함수를 타지 않으므로 그 경로의 기존 권한은 그대로다(D-L/C-3).
    fd, tmp_name = tempfile.mkstemp(
        prefix=f"{state_file.name}.tmp.", dir=str(state_file.parent))
    tmp_path = pathlib.Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp_path), str(state_file))
    except Exception:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def save_state_json(task_path, state):
    """state.json 저장 (UTF-8, 들여쓰기 2칸).

    [MUST] `state["run_log"]["pending_events"]`가 있으면 쓰기 직전 각 사건을
    `redact()`에 통과시킨다(GC-001 잔여분) — 이 함수는 `_atomic_write_state_json`
    바깥의 여러 호출부(advance/mark/block/add-row/status 등)에서도 쓰이므로,
    shadow init 뒤 이 경로로 state.json이 다시 기록되는 모든 경우에 초크포인트를
    태워야 outbox 사건이 마스킹 없이 남는 경로가 없어진다. `run_log` 블록
    자체가 없으면(= `--run-log-mode` 미지정 태스크) 기록 코어를 **import조차
    하지 않고** 기존 경로와 완전히 동일하게 동작한다 — S-2 바이트 동일성(C-3)을
    지키기 위한 조건부 격리이며, 이 조건이 없으면 미지정 경로도 이 함수를
    타는 이상 매 호출마다 불필요한 import·분기가 끼어든다.
    """
    run_log_block = state.get("run_log")
    if run_log_block and run_log_block.get("pending_events"):
        run_log_core = _import_run_log_core()
        run_log_block["pending_events"] = [
            run_log_core.redact(evt) for evt in run_log_block["pending_events"]
        ]
    state_file = task_path / "state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


def save_state_json_atomic(task_path, state):
    """Atomically replace state.json after flushing the complete new payload."""
    state_file = task_path / "state.json"
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(task_path),
            prefix=".state.json.", suffix=".tmp", delete=False,
        ) as temp_file:
            temp_name = temp_file.name
            json.dump(state, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_name, state_file)
        temp_name = None
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

# ─────────────────────────────────────────────────────────────────────────────
# 단계 건너뛰기 차단 (PLAN §M-A stage-transition guard)
# ─────────────────────────────────────────────────────────────────────────────

# 완료로 간주하는 상태값 — 이 상태의 앞 행은 건너뛰기 검증에서 제외
_COMPLETE_STATUSES = {"done", "additional_work_done", "na"}


def _derive_next_action(state):
    """072 G-16: 파이프라인 프론티어(첫 미완료 행)에서 '다음 액션' 문자열 파생.
    전체 완료 시 '태스크 완료'(M-2). 070 정합: row 순서 스캔 + _COMPLETE_STATUSES 재사용
    (resolve_row_index/task-step key 체계 무접촉)."""
    mode = state.get("mode")
    rows = state.get("rows", [])
    for idx, row in enumerate(rows):
        st = row.get("status")
        if st in _COMPLETE_STATUSES:
            continue
        # R-11 G-3-a: 다음 진입 시 도구가 자동 승인할 사용자 확인 행은 프론티어가 아니다.
        # CLOSE 직전 행도 can_auto_approve_user_confirmation()의 같은 mode 판정을 따른다.
        if row.get("item") == "사용자 확인":
            allowed, _ = can_auto_approve_user_confirmation(row.get("stage"), mode)
            if allowed:
                continue
        stage, item = row.get("stage", ""), row.get("item", "")
        if st == "in_progress":
            return f"{stage} {item} 진행 중"
        if st == "failed":
            return f"{stage} {item} 블로커 해소"
        return f"{stage} {item} 진입"   # pending
    return "태스크 완료"
