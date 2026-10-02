# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool_parts.run_log",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "state-tool run-log 연동 — outbox admission·원자 커밋·drain·사건 조립·완전성 진단",
  "exports": [
    "run_log_commit",
    "run_log_outbox_admit",
    "_run_log_drain",
    "run_log_diagnose"
  ]
}
"""

import json
import pathlib
import re
import uuid
from datetime import datetime, timezone

from . import base
from .codes import (
    RUN_LOG_OUTBOX_EVENT_MAX_BYTES,
    RUN_LOG_OUTBOX_TOTAL_LIMIT,
    RUN_LOG_OUTBOX_TOTAL_MAX_BYTES,
    RUN_LOG_STATE_ERROR_CODES,
    WARNING_CODES,
)
from .base import (
    _atomic_write_state_json,
    _current_session_id,
    _import_ownership_fingerprint,
    _ownership_warn,
    _rl_err,
    err,
    load_state_json,
    ok,
    resolve_task_path,
    save_state_json,
)

# ─────────────────────────────────────────────────────────────────────────────
# 미전송 사건 보관함(outbox)·복구 — CONTRACT §1.4 / TRD D-2 (T05)
#   상태 원천이 기록 실패를 견디게 하는 계층이다. 상태 변경과 사건 적재를 한 번의
#   원자 쓰기로 커밋(①)한 뒤, 기록 코어의 멱등 append(②)와 보관함 비우기(③)로
#   잇는다. ②가 실패해도 ①은 이미 디스크에 있으므로 상태 전이가 기록 장애로
#   교착되지 않는다(제안서 §11 R-6).
# ─────────────────────────────────────────────────────────────────────────────

_RUN_LOG_RUN_ID_PATTERN = re.compile(r"^run_[A-Za-z0-9_-]+$")


def _run_log_block(state):
    """state의 로그 계약 블록(dict) 또는 None. None이면 1.0/1.1 태스크다(C-3)."""
    block = state.get("run_log") if isinstance(state, dict) else None
    return block if isinstance(block, dict) else None


def _run_log_event_bytes(event):
    """보관함 항목의 UTF-8 직렬화 바이트 수 — 상한 판정의 유일한 척도(§1.4)."""
    return len(json.dumps(event, ensure_ascii=False, default=str).encode("utf-8"))


def _run_log_is_override_event(event):
    """override bundle 구성원 여부. 일반 admission 한도 계산에서 제외된다(§1.4).

    `TOTAL_LIMIT − (보관함에 있는 override 사건 수)`가 일반 한도이므로, 별도 예약
    슬롯 자료구조를 두지 않고 이 표시만으로 한도를 계산한다. bundle 적재 자체는
    `--run-log-override`(T10 소유 CLI 표면)의 일이며 여기서는 세기만 한다.
    """
    data = event.get("data") if isinstance(event, dict) else None
    return bool(isinstance(data, dict) and data.get("override_bundle"))


def run_log_outbox_admit(block, event):
    """보관함 admission 판정 → (허용 여부, 오류 코드, detail) (§1.4 상한).

    - 항목당 UTF-8 4 KiB 초과: `event_too_large`. 조용한 절단·자동 외부 저장을 하지
      않는다 — 초과분을 별도 파일로 빼는 것은 호출자의 책임이다(§1.4).
    - 일반 한도(`TOTAL_LIMIT − override 수`) 도달 또는 전체 512 KiB 초과:
      `run_log_outbox_full`. 호출자는 전이를 시작하지 않는다(§2.2).
    """
    size = _run_log_event_bytes(event)
    if size > RUN_LOG_OUTBOX_EVENT_MAX_BYTES:
        return False, "event_too_large", {
            "bytes": size, "limit": RUN_LOG_OUTBOX_EVENT_MAX_BYTES}

    pending = list(block.get("pending_events") or [])
    override_count = sum(1 for e in pending if _run_log_is_override_event(e))
    general_limit = RUN_LOG_OUTBOX_TOTAL_LIMIT - override_count
    general_count = len(pending) - override_count
    if not _run_log_is_override_event(event) and general_count >= general_limit:
        return False, "run_log_outbox_full", {
            "pending": len(pending), "limit": general_limit}

    total_bytes = sum(_run_log_event_bytes(e) for e in pending) + size
    if total_bytes > RUN_LOG_OUTBOX_TOTAL_MAX_BYTES:
        return False, "run_log_outbox_full", {
            "bytes": total_bytes, "limit": RUN_LOG_OUTBOX_TOTAL_MAX_BYTES}

    return True, None, {"bytes": size}


def _run_log_segment_records(task_path, run_id):
    """조각을 **읽기 전용**으로 스캔한다 → 레코드 리스트, 조각 부재면 None.

    §3.1은 상태 도구의 조각 **쓰기**를 금지하며 읽기는 금지하지 않는다. 읽는 이유는
    두 가지다 — (a) 보관함 재전송이 이미 기록된 사건을 다시 쓰지 않게 하는 멱등
    판정, (b) 활성 계약인데 기록이 사라졌는지의 진단(§1.4). 어느 쪽도 사건을
    합성하지 않는다.

    `run_id`는 glob 패턴에 그대로 들어가므로 기록 코어와 같은 화이트리스트
    (`run_<영숫자·밑줄·하이픈>`)로 먼저 거른다 — `*` 같은 메타문자가 다른 run의
    조각까지 끌어오는 것을 막는다(GC-003 동형).
    """
    if not isinstance(run_id, str) or not _RUN_LOG_RUN_ID_PATTERN.match(run_id):
        return None
    run_dir = pathlib.Path(task_path) / "run"
    if run_dir.is_symlink() or not run_dir.is_dir():
        return None
    segments = sorted(run_dir.glob(f"run-log-{run_id}-*.jsonl"))
    if not segments:
        return None
    records = []
    for seg in segments:
        try:
            raw = seg.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in raw.splitlines():
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


# W-7 (PLAN D-P8/H-6) — terminal 사건 3종. CONTRACT §1.2 "terminal 공통 조건"의
# 정의와 동일 문자열이며, run_log_core._TERMINAL_EVENTS(비공개)를 다시 import하지
# 않고 상태 도구 쪽에 독립 상수로 둔다(D-5 단방향 의존 — 상태 도구가 코어의
# 비공개 심볼에 결합하지 않는다).
_RUN_LOG_TERMINAL_EVENTS = ("worker.completed", "worker.failed", "worker.blocked")


def _resolve_sole_terminal_worker_run_id(task_path, run_id):
    """활성 run의 조각에서 terminal 사건(worker.completed/failed/blocked)의
    `worker_run_id`를 조회한다 (W-7, PLAN.md W-6가 남긴 열린 질문에 대한 구현
    측 판정).

    `surfaces.json`의 `state-tool.mark.completion-gate` 표면에는 `--worker-run-id`
    인자가 없어 `mark`가 어느 워커의 파생값을 볼지 표면 계약만으로는 정할 수
    없다. CONTRACT §1.2 "terminal 공통 조건"이 "같은 worker_run_id에 정확히
    1건"을 보장하므로, 이 run의 조각 전체에서 terminal 사건에 실린 서로 다른
    `worker_run_id`가 **정확히 1개**뿐이면 그 값을 "이 run의 유일한 미해소
    terminal"로 간주해 반환한다(RED 테스트를 작성한 형제 워커가 fixture에서
    가정한 것과 같은 관례).

    0건(아직 워커가 종료 사건을 내지 않음)이거나 2건 이상(서로 다른
    `worker_run_id`가 섞여 있어 이 mark 호출이 가리키는 대상을 표면 계약만으로
    특정할 수 없음)이면 `None`을 반환한다 — 추측해 잘못된 워커의 값을 자동
    기록하지 않고, 호출자가 기존 수동 경로로 폴백하게 한다.
    """
    if not run_id:
        return None
    records = _run_log_segment_records(task_path, run_id) or []
    worker_run_ids = {
        rec.get("worker_run_id") for rec in records
        if isinstance(rec, dict)
        and rec.get("event") in _RUN_LOG_TERMINAL_EVENTS
        and rec.get("worker_run_id")
    }
    if len(worker_run_ids) != 1:
        return None
    return next(iter(worker_run_ids))


def _reconcile_worker_duration_minutes(task_path, state, explicit_minutes, command):
    """W-7 (PLAN D-P8, CONTRACT §2.5 시간 절) — 1.2 태스크에서 W-6 코어 조회
    (`run_log_core.reconcile_duration()`, `_import_run_log_core()` 경로)로 파생
    분값을 읽어 `--worker-duration-minutes` 명시값과 대조한다.

    반환은 `(mark가 행에 기록할 분값, deprecated 경고 dict|None)`이다.

    - `run_log` 블록이 없는 1.0/1.1 태스크는 손대지 않고 명시값을 그대로
      돌려준다 — 산출물·응답 키 집합이 종전과 바이트 동일해야 한다(H-6, S-9).
    - 파생값을 아직 얻을 수 없으면(terminal 미기록·조회 실패·`duration_ms`가
      `duration_unknown_reason` 경로로 `null`) 역시 명시값을 그대로 돌려준다 —
      모르는 것을 추측해 차단하지 않는다(CONTRACT §2.6과 같은 태도).
    - 명시값이 없으면 파생값을 그대로 기록값으로 승격한다(자동 기록, 경고 없음).
    - 명시값과 파생값이 같으면 수용하되 폐기 예정 경고를 함께 반환한다.
    - 명시값과 파생값이 다르면 `worker_duration_conflict`로 **즉시 거부**한다.
      이 함수는 `cmd_mark`가 아직 어떤 상태도 변경하지 않은 시점에서 호출돼야
      한다 — 그래야 거부 시 `state.json`이 손대지지 않은 채로 남는다(S-8③).
    """
    block = _run_log_block(state)
    if block is None:
        return explicit_minutes, None

    run_id = block.get("active_run_id")
    worker_run_id = _resolve_sole_terminal_worker_run_id(task_path, run_id)
    if worker_run_id is None:
        return explicit_minutes, None

    core = base._import_run_log_core()
    result = core.reconcile_duration(str(task_path), run_id, worker_run_id)
    if not result.get("ok"):
        return explicit_minutes, None

    derived_minutes = (result.get("data") or {}).get("duration_minutes")
    if derived_minutes is None:
        return explicit_minutes, None

    if explicit_minutes is None:
        return derived_minutes, None

    if explicit_minutes == derived_minutes:
        return explicit_minutes, {
            "code": "worker_duration_minutes_deprecated",
            "message": WARNING_CODES["worker_duration_minutes_deprecated"].format(
                minutes=explicit_minutes),
        }

    err(command, "worker_duration_conflict",
        explicit_minutes=explicit_minutes, derived_minutes=derived_minutes,
        worker_run_id=worker_run_id)


def _run_log_drain(task_path, block, core):
    """보관함을 **순서대로** 재전송한다 → (재전송 건수, 실패 detail 또는 None).

    - 완전한 사건만 그대로 재전송한다. 현재 시각·stdout에서 사건을 합성하지
      않는다(§2.3 `reconcile` 불변식).
    - 첫 실패에서 멈추고 나머지를 보관함에 남긴다 — 건너뛰고 뒤를 먼저 쓰면
      조각의 순서가 보관함 순서와 어긋난다.
    - 이미 조각에 있는 `event_id`는 성공으로 간주하고 건너뛴다(멱등 재전송).
    - 보관함에 `run.started`가 있으면 실행 디렉터리·첫 조각을 다시 만든다 —
      이것이 §1.4의 "복구 가능 초기화"다. 그 근거가 없으면 조각을 만들지 않는다.
      만들면 삭제된 기록이 `run_log_missing` 대신 조용히 재생성된다.
    """
    pending = list(block.get("pending_events") or [])
    if not pending:
        return 0, None

    run_id = block.get("active_run_id")
    drained = 0
    failure = None

    with core.task_lock(str(task_path)) as acquired:
        if not acquired:
            return 0, {"code": "task_lock_timeout", "message": str(task_path)}

        if any(e.get("event") == "run.started" for e in pending):
            init_result = core.init(str(task_path), run_id, lock_held=True)
            if not init_result.get("ok"):
                return 0, init_result.get("error") or {"code": "run_log_write_failed"}

        records = _run_log_segment_records(task_path, run_id) or []
        recorded_ids = {r.get("event_id") for r in records}

        for event in pending:
            if event.get("event_id") in recorded_ids:
                drained += 1
                continue
            result = core.append(str(task_path), run_id, event, lock_held=True)
            if not result.get("ok"):
                failure = result.get("error") or {"code": "run_log_write_failed"}
                break
            drained += 1

    block["pending_events"] = pending[drained:]
    return drained, failure


def build_state_changed_event(state, *, task_id, command, from_status, to_status,
                              row=None, row_key=None, note=None):
    """`state.changed` 1건을 §1.1 필수 필드 전건으로 만든다 (§1.2 추가 조건 포함).

    조합 A7(`actor.kind=tool` + `provenance.type=direct` + `recorded_by.kind=tool`)
    이며 `event_id`를 여기서 사전 확정한다 — 보관함에 적재된 payload와 조각에
    기록되는 payload가 같은 식별자를 갖게 해 재전송이 멱등이 된다(§1.3 A7).
    """
    core = base._import_run_log_core()
    block = _run_log_block(state) or {}
    event = {
        "schema_version": "1.0",
        "event_id": core.new_event_id(),
        "request_id": f"req_{uuid.uuid4()}",
        "task_id": task_id,
        "run_id": block.get("active_run_id"),
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": None,
        "stage": (row or {}).get("stage"),
        "task_step": (row or {}).get("key"),
        "work_item": (row or {}).get("item"),
        "gate_id": None,
        "event": "state.changed",
        "actor": {"kind": "tool", "id": "state-tool", "provider": None,
                  "session_id": _current_session_id()},  # 138 W-9
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "tool", "id": "state-tool"},
            "worker_log_token_id": None,
            "source": None,
        },
        "summary": f"{command}: {from_status} → {to_status}",
        "reason": None,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": None,
        "timestamp": core.utc_now_ms(),
        "data": {
            "from": from_status,
            "to": to_status,
            # §1.2는 state.changed에 data.row_key를 요구한다. key 없는 레거시 구조의
            # 행은 row_id로 폴백해 필수 필드가 null이 되지 않게 한다.
            "row_key": row_key if row_key is not None else (
                (row or {}).get("key")
                or (f"row:{row['row_id']}" if row and row.get("row_id") else None)),
        },
    }
    if note:
        event["data"]["note"] = note
    return event


def run_log_commit(task_path, state, command, event=None):
    """상태 변경 + 보관함 적재를 **한 번의 원자 쓰기**로 커밋한다 (D-2, D-3, §2.5).

    `run_log` 블록이 없는 태스크(1.0/1.1)는 기존 `save_state_json()`을 그대로 타고
    반환도 없다 — 미지정 경로의 산출물·응답 키 집합이 종전과 동일해야 한다(C-3).

    `event`는 단일 이벤트 dict(하위호환) 또는 이벤트 dict의 list를 받는다(D-3).
    list인 경우 `advance`/`mark`가 자동 승인한 각 사용자 확인 행의 `state.changed`와
    대상 행 전이의 `state.changed`를 함께 실어, 여러 상태 변경을 **한 번의
    admission·원자 쓰기**로 커밋한다(H-1) — admission 판정은 순서대로 전부
    통과해야만 `block["pending_events"]`에 반영되며, 도중 하나라도 거부되면
    `err()`가 즉시 종료시켜 그 어떤 이벤트도 보관함에 들어가지 않는다(부분
    admission 불가, S-4).

    순서:
      ① admission 판정(리스트 전원) → 위반이면 `err()`로 전이를 **시작하지 않는다**(state.json 미기록)
      ② `status=pending` + 보관함 일괄 적재 + 상태 변경을 1회 원자 쓰기로 커밋
      ③ 기록 코어 멱등 append(락 보유) — 실패해도 ②는 유지된다(교착 금지)
      ④ 성공분을 보관함에서 비우고 `status`를 확정하는 2차 원자 쓰기

    반환은 `ok()`에 병합할 응답 필드 dict다. append가 실패하면 `warnings`에
    `run_log_pending`을 실어 보내되 exit code는 바꾸지 않는다(§2.2 "한도 내 일반
    진행 허용").
    """
    block = _run_log_block(state)
    if block is None:
        save_state_json(task_path, state)
        return {}

    core = base._import_run_log_core()

    # W-7 — Stop hook은 run-log에 직접 쓰지 않고 ownership receipt에 판정만
    # 적재한다. 다음 state-tool 커밋이 그 receipt를 A7 사건으로 중개한다. receipt
    # 항목은 **state outbox 원자 커밋 뒤에만** 제거한다. 따라서 admission 거부나
    # 상태 저장 실패가 나면 다음 전이에서 다시 시도할 증거가 사라지지 않는다.
    stop_decision_events, stop_receipt_token = _load_pending_stop_decisions(task_path, state)
    events = list(stop_decision_events)
    if event is not None:
        events.extend(event if isinstance(event, list) else [event])

    if events:
        # H-1: admission 판정을 working copy(pending 스냅샷 누적)로 전부 통과시킨
        # 뒤에만 block["pending_events"]를 갱신한다 — 전부-아니면-전무.
        _working_pending = list(block.get("pending_events") or [])
        for _ev in events:
            admitted, code, detail = run_log_outbox_admit(
                {**block, "pending_events": _working_pending}, _ev)
            if not admitted:
                err(command, code, **(detail or {}))
            _working_pending = _working_pending + [_ev]
        block["pending_events"] = _working_pending

        # TASK-147 D-7/H-2 — `pm.report` 커밋은 `run_log.last_report` 파생 포인터를
        # **같은 원자 쓰기 안에서** 갱신한다. 위 admission 루프가 하나라도 거부하면
        # `err()`가 이미 프로세스를 끝냈으므로 여기에 닿지 않는다 — 즉 거부된
        # 보고는 사건도 포인터도 남기지 않는다(사건이 SSOT, 포인터는 파생).
        # 포인터에는 §1.4 폐쇄 5키만 싣는다. `summary`·`reason` 같은 자유 서술은
        # 절대 복제하지 않는다 — 그것이 §1.3 "원본 프롬프트·chain-of-thought·
        # 비밀값을 어떤 필드에도 저장하지 않는다"를 포인터에서 지키는 방법이다.
        for _ev in events:
            if _ev.get("event") != "pm.report":
                continue
            _report_data = _ev.get("data") or {}
            block["last_report"] = {
                "event_id": _ev.get("event_id"),
                "report_type": _report_data.get("report_type"),
                "transition_action": _report_data.get("transition_action"),
                "user_input_required": _report_data.get("user_input_required"),
                "at": _ev.get("timestamp"),
            }

    if block.get("pending_events") and block.get("status") != "overridden":
        block["status"] = "pending"
    _atomic_write_state_json(task_path, state)

    # receipt는 outbox에 먼저 영속된 사건의 보조 증거일 뿐이다. 이 제거가 실패해도
    # 상태 전이와 이미 커밋된 보관함을 되돌리지 않는다. 다음 호출에서 receipt가
    # 남아 있음을 stderr 경고로만 드러낸다(fail-safe).
    receipt_failure = _drain_pending_stop_decisions(stop_receipt_token)
    if receipt_failure is not None:
        _ownership_warn(receipt_failure["code"],
                        "stop receipt pending_decisions 제거 실패: "
                        f"{receipt_failure.get('message')}")

    drained, failure = _run_log_drain(task_path, block, core)

    if not block.get("pending_events") and block.get("status") == "pending":
        block["status"] = "active"
    if drained or failure is not None or events:
        _atomic_write_state_json(task_path, state)

    pending_count = len(block.get("pending_events") or [])
    summary = {
        "status": block.get("status"),
        "pending": pending_count,
        "active_run_id": block.get("active_run_id"),
    }
    fields = {"run_log": summary}
    if failure is not None:
        summary["last_error"] = failure.get("code")
        fields["warnings"] = [{
            "code": "run_log_pending",
            "message": RUN_LOG_STATE_ERROR_CODES["run_log_pending"].format(
                count=pending_count),
        }]
    return fields


def run_log_diagnose(task_path, state):
    """로그 계약 블록의 진단 → violations 리스트 (§1.4 계약 무결성 / AC-3).

    **legacy 강등을 하지 않는다.** 활성 계약(블록 보유) 태스크에서 기록이 사라지면
    스키마를 1.1로 되돌리거나 블록을 지우는 대신 `run_log_missing` 위반을 낸다.
    보관함에 `run.started`가 남아 있으면 고장이 아니라 **복구 가능 초기화**이므로
    `run_log_pending`으로만 보고한다.

    읽기 전용이다 — 진단이 상태를 고치지 않는다(복구는 다음 전이의 재전송이 수행).
    """
    block = _run_log_block(state)
    if block is None:
        return []

    violations = []
    pending = list(block.get("pending_events") or [])
    run_id = block.get("active_run_id")

    if pending:
        recoverable_init = any(e.get("event") == "run.started" for e in pending)
        violations.append({
            "code": "run_log_pending",
            "row_id": None,
            "detail": (f"pending_events={len(pending)}, "
                       f"recoverable_init={str(recoverable_init).lower()}"),
        })
        override_count = sum(1 for e in pending if _run_log_is_override_event(e))
        if len(pending) - override_count >= RUN_LOG_OUTBOX_TOTAL_LIMIT - override_count:
            violations.append({
                "code": "run_log_outbox_full",
                "row_id": None,
                "detail": f"pending_events={len(pending)} (limit={RUN_LOG_OUTBOX_TOTAL_LIMIT})",
            })
        return violations

    records = _run_log_segment_records(task_path, run_id)
    if records is None:
        violations.append({
            "code": "run_log_missing",
            "row_id": None,
            "detail": f"run log segments not found for {run_id} (계약 유지, 강등하지 않음)",
        })
    elif not any(r.get("event") == "run.started" for r in records):
        violations.append({
            "code": "run_log_missing",
            "row_id": None,
            "detail": f"run.started not found in segments for {run_id}",
        })
    return violations


# ─────────────────────────────────────────────────────────────────────────────
# W-3 (135, CONTRACT §2.4) — log-event / gate-request / gate-resolve
#   surfaces.json이 선언한 3개 신규 표면. run_log_commit()의 outbox/admission/
#   drain 경로를 그대로 재사용한다 — 별도 기록 경로를 만들지 않는다.
# ─────────────────────────────────────────────────────────────────────────────

_PM_ACTIVITY_KIND_ENUM = {"decision", "validation", "retry", "progress"}

# ── TASK-147 D-2 — `pm.report` data 폐쇄 3키와 값 enum ──
# [MUST] 이 상수들은 기록 코어 `run_log_core._PM_REPORT_DATA_KEYS`·
# `_PM_REPORT_TYPES`·`_PM_TRANSITION_ACTIONS`의 **물리 분리 사본**이다(D-5·§3.1
# 단방향 의존 — 상태 도구는 기록 코어를 `_import_run_log_core()` 경로로만 만지고
# 검증 상수를 import해 결합을 만들지 않는다). 앞단 검증은 같은 규칙의 **중복
# 방어**이며 두 지점의 판정 결과는 항상 일치해야 한다(§1.3, TASK-147.S-6).
_PM_REPORT_DATA_KEYS = {"report_type", "transition_action", "user_input_required"}
_PM_REPORT_TYPE_ENUM = ("progress_report", "decision_request")
_PM_TRANSITION_ACTION_ENUM = ("continue", "await_user", "blocked", "complete")

# CONTRACT §1.4 — `run_log.last_report` 포인터의 폐쇄 5키(D-7).
_RUN_LOG_LAST_REPORT_KEYS = (
    "event_id", "report_type", "transition_action", "user_input_required", "at")


def _require_absolute_task_path(task_path_str, command):
    """CONTRACT §3.2 (M-2) — task path는 절대 경로여야 한다.

    기존 서브커맨드(advance/mark/...)는 `resolve_task_path()`로 상대경로를
    말없이 절대화하는 관례를 그대로 둔다(PRINCIPLES §3 수술적 변경 — 기존 경로
    불변). log-event/gate-request/gate-resolve 3개 신규 표면만 이 계약을
    새로 집행한다.
    """
    p = pathlib.Path(task_path_str)
    if not p.is_absolute():
        _rl_err(command, "task_path_not_absolute", path=task_path_str)
    return resolve_task_path(task_path_str, command)


def _run_log_all_records(task_path, block):
    """이미 조각에 기록된 사건 + 아직 드레인되지 않은 보관함 사건을 합쳐 반환한다.

    gate_id 유일성·선행관계 판정은 조각(진실의 원천)뿐 아니라 아직 드레인되지
    않은 보관함 항목까지 봐야 한다 — 그렇지 않으면 직전 호출이 기록 실패로
    보관함에만 남아 있는 상태에서 같은 gate_id가 중복 승인될 수 있다.
    """
    run_id = block.get("active_run_id")
    committed = _run_log_segment_records(task_path, run_id) or []
    pending = list(block.get("pending_events") or [])
    return committed + pending


def _stop_decision_project_root(task_path):
    """표준 ``<project>/tasks/<task>`` 배치에서 receipt 프로젝트 루트를 얻는다.

    이 함수는 receipt 경로를 만들지 않는다. 경로 계산·읽기·쓰기 모두
    ownership-tool의 fingerprint API가 소유하고, 여기서는 대상 task가 표준
    ``tasks/`` 아래인지 확인하는 데만 쓴다.
    """
    task_dir = pathlib.Path(task_path).resolve()
    if task_dir.parent.name != "tasks":
        return None
    return task_dir.parent.parent


def _timestamp_sort_key(value):
    """UTC 시각의 결정론적 비교 키. 잘못된 값은 판정 후보에서 제외한다."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc).timestamp()


def _last_activity_before(records, decided_at):
    """판정 시각 *직전* 마지막 activity의 event_id를 시각·ID 순으로 고른다."""
    decision_key = _timestamp_sort_key(decided_at)
    if decision_key is None:
        return None
    candidates = []
    for record in records:
        if not isinstance(record, dict) or record.get("event") != "activity":
            continue
        timestamp_key = _timestamp_sort_key(record.get("timestamp"))
        event_id = record.get("event_id")
        if timestamp_key is None or timestamp_key >= decision_key or not isinstance(event_id, str):
            continue
        candidates.append((timestamp_key, event_id))
    return max(candidates)[1] if candidates else None


def _build_stop_decision_event(state, *, task_id, receipt_decision, last_activity_event_id):
    """ownership-tool receipt의 닫힌 판정 축만 A7 ``stop.decision``으로 조립한다.

    receipt의 task_path/decided_at 외 자유 필드, Stop envelope, last assistant
    message는 사건에 옮기지 않는다. ``data`` 6키와 summary는 각각 CONTRACT
    §1.3/§1.3.1의 유일한 저장 후보이며, event/request ID는 같은 사전 확정 값이다.
    """
    core = base._import_run_log_core()
    block = _run_log_block(state) or {}
    event_id = core.new_event_id()
    report_event_id = receipt_decision.get("report_event_id")
    data = {
        "decision_kind": receipt_decision.get("decision_kind"),
        "diagnostics": list(receipt_decision.get("diagnostics") or []),
        "block_count": receipt_decision.get("block_count"),
        "claim_source": receipt_decision.get("claim_source"),
        "report_event_id": report_event_id,
        "last_activity_event_id": last_activity_event_id,
    }
    return {
        "schema_version": "1.0",
        "event_id": event_id,
        "request_id": event_id,
        "task_id": task_id,
        "run_id": block.get("active_run_id"),
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": report_event_id,
        "stage": None,
        "task_step": None,
        "work_item": None,
        "gate_id": None,
        "event": "stop.decision",
        "actor": {"kind": "tool", "id": "ownership-tool", "provider": None,
                  "session_id": _current_session_id()},
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "tool", "id": "state-tool"},
            "worker_log_token_id": None,
            "source": None,
        },
        "summary": core.render_event_summary("stop.decision", data),
        "reason": None,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": None,
        "timestamp": receipt_decision.get("decided_at"),
        "data": data,
    }


def _load_pending_stop_decisions(task_path, state):
    """현재 세션·대상 태스크의 receipt를 API로 읽어 drain 후보를 만든다.

    반환한 receipt token은 state의 첫 원자 커밋 뒤에만 비운다. 따라서 admission이
    거부되거나 state 저장이 실패한 경우 receipt는 증거로 남는다.
    """
    session_id = _current_session_id()
    project_root = _stop_decision_project_root(task_path)
    if session_id is None or project_root is None:
        return [], None
    try:
        fingerprint = _import_ownership_fingerprint()
        receipt = fingerprint.load_receipt(str(project_root), session_id)
    except Exception as exc:  # noqa: BLE001 — receipt 경계는 상태 전이를 막지 않는다.
        _ownership_warn("ownership_stop_receipt_load_failed",
                        f"stop receipt 조회 실패({exc.__class__.__name__}: {exc}).")
        return [], None
    if not isinstance(receipt, dict):
        return [], None

    pending = receipt.get("pending_decisions")
    if not isinstance(pending, list):
        return [], None
    canonical_task_path = pathlib.Path(task_path).resolve()
    selected_indexes = []
    for index, decision in enumerate(pending):
        if not isinstance(decision, dict) or not isinstance(decision.get("task_path"), str):
            continue
        # `/var` → `/private/var`처럼 동등한 task 경로가 표기만 다른 macOS
        # 배치를 수용하되, receipt의 경로는 비교 외 어떤 파일 연산에도 쓰지 않는다.
        try:
            is_target = pathlib.Path(decision["task_path"]).resolve() == canonical_task_path
        except (OSError, RuntimeError):
            is_target = False
        if is_target:
            selected_indexes.append(index)
    if not selected_indexes:
        return [], None

    records = _run_log_all_records(task_path, _run_log_block(state) or {})
    events = []
    admitted_indexes = []
    core = base._import_run_log_core()
    for index in selected_indexes:
        decision = pending[index]
        try:
            event = _build_stop_decision_event(
                state, task_id=pathlib.Path(task_path).name,
                receipt_decision=decision,
                last_activity_event_id=_last_activity_before(records, decision.get("decided_at")))
        except (KeyError, TypeError, ValueError):
            # 비정상 receipt를 보관함에 복사하면 원문이 pending_events라는 우회
            # 저장소에 남을 수 있다. receipt는 남기고, 값 자체는 경고에도 싣지 않는다.
            _ownership_warn("ownership_stop_receipt_schema_invalid",
                            "stop receipt 판정이 폐쇄 event 형태로 조립되지 않아 보류했습니다.")
            continue
        if core.validate_event(event) or core.validate_provenance(event):
            _ownership_warn("ownership_stop_receipt_schema_invalid",
                            "stop receipt 판정이 run-log 폐쇄 스키마를 통과하지 않아 보류했습니다.")
            continue
        events.append(event)
        admitted_indexes.append(index)
    if not events:
        return [], None
    return events, {
        "fingerprint": fingerprint,
        "project_root": str(project_root),
        "receipt": receipt,
        "selected_indexes": frozenset(admitted_indexes),
    }


def _drain_pending_stop_decisions(token):
    """state outbox 커밋 뒤 선택한 receipt 항목만 ownership API로 제거한다."""
    if token is None:
        return None
    receipt = dict(token["receipt"])
    pending = receipt.get("pending_decisions") or []
    receipt["pending_decisions"] = [
        decision for index, decision in enumerate(pending)
        if index not in token["selected_indexes"]
    ]
    try:
        result = token["fingerprint"].save_receipt(token["project_root"], receipt)
    except Exception as exc:  # noqa: BLE001 — receipt 경계는 상태 전이를 막지 않는다.
        return {"code": "ownership_stop_receipt_drain_failed",
                "message": f"{exc.__class__.__name__}: {exc}"}
    if not isinstance(result, dict) or not result.get("ok"):
        return {"code": "ownership_stop_receipt_drain_failed",
                "message": (result or {}).get("error") if isinstance(result, dict) else None}
    return None


def _pending_stop_receipt_count(task_path):
    """현재 세션 receipt에서 대상 task의 미커밋 Stop 판정 수를 읽기 전용 조회한다.

    D-14의 ``missing_stop_decision``은 hook 미실행과 receipt에는 있으나 아직
    outbox로 drain되지 않은 경우를 구별해야 한다. receipt 경로를 직접 열지 않고
    W-7과 같은 ownership-tool API만 사용하며, 완전성 진단 자체는 어떤 실패도
    경고·쓰기 없이 빈 값으로 폴백한다.
    """
    session_id = _current_session_id()
    project_root = _stop_decision_project_root(task_path)
    if session_id is None or project_root is None:
        return 0
    try:
        receipt = _import_ownership_fingerprint().load_receipt(
            str(project_root), session_id)
    except Exception:  # noqa: BLE001 — read-only 진단은 항상 비차단이다.
        return 0
    pending = receipt.get("pending_decisions") if isinstance(receipt, dict) else None
    if not isinstance(pending, list):
        return 0
    canonical_task_path = pathlib.Path(task_path).resolve()
    count = 0
    for decision in pending:
        if not isinstance(decision, dict) or not isinstance(decision.get("task_path"), str):
            continue
        try:
            if pathlib.Path(decision["task_path"]).resolve() == canonical_task_path:
                count += 1
        except (OSError, RuntimeError):
            continue
    return count


_RUN_LOG_TERMINAL_EVENTS = ("worker.completed", "worker.failed", "worker.blocked")


def _check_active_completion_evidence(task_path, block, command):
    """135 W-4 (AC-6, C-2, H-4) — active 완료 게이트.

    `completion_profile`이 `cooperative`가 아닌 active run의 완료 전이는
    trusted terminal 사건 정확히 1건을 요구하고, `observed_trajectory`는
    추가로 trusted `activity` 1건 이상을 요구한다(CONTRACT §1.5). 증거가
    부족하면 `completion_evidence_missing`으로 거부해 state.json을 손대지
    않는다(호출 시점이 아직 원자 쓰기 이전이어야 한다).
    """
    if block.get("mode") != "active":
        return
    profile = block.get("completion_profile")
    if profile == "cooperative":
        return

    records = _run_log_all_records(task_path, block)
    terminal_events = [r for r in records if r.get("event") in _RUN_LOG_TERMINAL_EVENTS]
    if len(terminal_events) != 1:
        err(command, "completion_evidence_missing",
            reason="terminal_missing_or_multiple", terminal_count=len(terminal_events))

    if profile == "observed_trajectory":
        activity_events = [
            r for r in records
            if r.get("event") == "activity" and (r.get("actor") or {}).get("kind") != "PM"
        ]
        if not activity_events:
            err(command, "completion_evidence_missing", reason="activity_missing")


_RUN_LOG_BOUNDARY_EVENTS = (
    "run.started", "run.completed",
    "worker.started", "worker.completed", "worker.failed", "worker.blocked",
)


def _run_log_completeness_check(task_path):
    """135 W-4 (AC-5~AC-8, D-6) — state.json run_log 계약과 JSONL 사건을 대조해
    완전성 갭을 진단한다(읽기 전용, 비차단, exit 0).

    구조 검증(run-log-tool validate-run)과는 별개 축이다 — 순번·스키마가
    유효해도 기대되는 상태 전이·PM 활동·gate 쌍·worker 경계가 실제로 관측됐는지는
    이 함수만이 판정한다(AC-8, C-4/C-5, TASK-135.S-9).

    반환 필드:
      - `missing_state_changed` / `missing_pm_activity` / `missing_gate_event` /
        `unobserved_worker_boundary`: 누락 목록 4종. `missing_pm_activity`는
        CONTRACT §2.5 트리거 조문의 상태 앵커 2종(자동 승인 행 / override)을
        committed+pending 합집합 사건과 대조해 채운다(137 W-5, D-1~D-6).
      - `last_observed_decision` / `last_observed_state_change` / `last_observed_boundary`:
        관측 지점 3필드(`{event_id, ts, ref}` 또는 없으면 None) — 누락 목록과
        무관하게 항상 반환한다(AC-7, 사람 판독이 아닌 결정론 조회).

    run_log 블록이 없는 태스크(1.0/1.1)는 모든 목록이 비고 3필드가 전부 None이다
    (C-3, 완전성 검사 대상이 아님).
    """
    result = {
        "missing_state_changed": [],
        "missing_pm_activity": [],
        "missing_gate_event": [],
        "unobserved_worker_boundary": [],
        # TASK-147 D-14/D-10(b) — 정지 원인 4분류와 오인 방지 activity 축.
        # 모든 항목은 아래 구현부의 고정 키만 쓰며, 자유 summary·reason을 읽거나
        # 응답으로 복사하지 않는다. 기존 4축/관측 3필드는 순서·의미 모두 불변이다.
        "report_intent_inconsistent": [],
        "missing_stop_decision": [],
        "stop_decision_allowed": [],
        "stop_block_without_followup": [],
        "unanchored_activity": [],
        "last_observed_decision": None,
        "last_observed_state_change": None,
        "last_observed_boundary": None,
    }

    state_file = pathlib.Path(task_path) / "state.json"
    if not state_file.is_file():
        return result
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return result

    block = _run_log_block(state)
    if block is None:
        return result

    run_id = block.get("active_run_id")
    committed = _run_log_segment_records(task_path, run_id) or []
    # 관측 지점 3필드는 아직 조각에 드레인되지 않은 보관함 사건까지 포함해 "마지막으로
    # 관측된 지점"을 결정론적으로 조회한다(AC-7) — _run_log_all_records() 재사용.
    all_records = _run_log_all_records(task_path, block)

    # ── 누락 ① missing_state_changed — committed(진짜 persist된) 로그만 근거로 삼는다.
    #   보관함에만 있는 사건은 run_log_pending이 별도로 진단하므로(§1.4), 여기서
    #   "누락"으로 다시 잡으면 두 진단이 뒤섞인다.
    committed_transitions = {}
    for rec in committed:
        if rec.get("event") == "state.changed" and isinstance(rec.get("data"), dict):
            row_key = rec["data"].get("row_key")
            to_status = rec["data"].get("to")
            committed_transitions.setdefault(row_key, set()).add(to_status)

    rows = state.get("rows") or []
    missing_state_changed = []
    for row in rows:
        row_key = row.get("key") or (f"row:{row['row_id']}" if row.get("row_id") else None)
        status = row.get("status")
        observed = committed_transitions.get(row_key, set())
        if status in ("in_progress", "done") and status not in observed:
            missing_state_changed.append({
                "row_id": row.get("row_id"), "row_key": row_key,
                "stage": row.get("stage"), "expected": status,
            })
        elif status == "done" and "in_progress" not in observed:
            # 자동 승인 등으로 in_progress 체크포인트 없이 곧바로 done에 도달한 경우
            # (S-9) — 구조적으로는 유효하지만 완전성 관점에서는 관측 중간 지점 갭이다.
            missing_state_changed.append({
                "row_id": row.get("row_id"), "row_key": row_key,
                "stage": row.get("stage"), "expected": "in_progress",
            })

    # 마지막 done 행 바로 다음 행이 여전히 pending이면(TASK 보고 후 중단 재현,
    # TASK-135.S-8) 다음 stage 진입 자체가 관측되지 않은 것이다.
    done_indices = [i for i, r in enumerate(rows) if r.get("status") == "done"]
    if done_indices:
        _next_idx = max(done_indices) + 1
        if _next_idx < len(rows) and rows[_next_idx].get("status") == "pending":
            _next_row = rows[_next_idx]
            _next_key = _next_row.get("key") or (
                f"row:{_next_row['row_id']}" if _next_row.get("row_id") else None)
            missing_state_changed.append({
                "row_id": _next_row.get("row_id"), "row_key": _next_key,
                "stage": _next_row.get("stage"), "expected": "in_progress",
                "detail": "다음 stage 진입 관측 없음(TASK 보고 후 중단 후보)",
            })
    result["missing_state_changed"] = missing_state_changed

    # ── 누락 ② missing_gate_event — gate.requested만 있고 gate.resolved가 없는 경우.
    requested_ids = {rec.get("gate_id") for rec in all_records if rec.get("event") == "gate.requested"}
    resolved_ids = {rec.get("gate_id") for rec in all_records if rec.get("event") == "gate.resolved"}
    result["missing_gate_event"] = [
        {"gate_id": gid, "expected": "gate.resolved"}
        for gid in sorted(requested_ids - resolved_ids) if gid
    ]

    # ── 누락 ③ unobserved_worker_boundary — worker.started만 있고 terminal이 없는 경우.
    started_ids = {rec.get("worker_run_id") for rec in all_records if rec.get("event") == "worker.started"}
    terminal_ids = {rec.get("worker_run_id") for rec in all_records
                    if rec.get("event") in _RUN_LOG_TERMINAL_EVENTS}
    result["unobserved_worker_boundary"] = [
        {"worker_run_id": wid} for wid in sorted(started_ids - terminal_ids) if wid
    ]

    # ── 누락 ④ missing_pm_activity — CONTRACT §2.5 트리거 조문(앵커 2종, 137 D-1~D-6).
    #   대조 집합은 committed 조각 + 보관함(pending)의 합집합(all_records)이다 — 보관함에
    #   적재된 PM activity도 이미 생산된 사건으로 본다(§1.4, D-3). 상태 앵커는 state.json의
    #   현재 사실이므로 이 판정은 state-tool 전담이다(§3.1 단방향 의존, C-4).
    pm_decisions = [
        rec for rec in all_records
        if rec.get("event") == "activity"
        and (rec.get("actor") or {}).get("kind") == "PM"
        and isinstance(rec.get("data"), dict)
        and rec["data"].get("kind") == "decision"
    ]
    decision_steps = {rec.get("task_step") for rec in pm_decisions}

    missing_pm_activity = []
    # 앵커 ① 자동 승인 행 — status=="done" ∧ owner=="auto" ∧ key 보유. key가 없는 행은
    #   대조 주소가 없어 판정 대상이 아니다(§2.5 범위 한정 (a)). row_id 오름차순(§2.5 정렬).
    auto_rows = [
        row for row in rows
        if row.get("status") == "done" and row.get("owner") == "auto" and row.get("key")
    ]
    for row in sorted(auto_rows, key=lambda r: r["row_id"]):
        if row["key"] not in decision_steps:
            missing_pm_activity.append({
                "row_id": row.get("row_id"), "row_key": row.get("key"),
                "stage": row.get("stage"), "expected": "activity(decision)",
                "anchor": "auto_approved_row",
            })

    # 앵커 ② override — run_log.status=="overridden"인데 run 전역에 PM activity(decision)가
    #   하나도 없으면 1건. 주소 대조를 하지 않으며 배열 마지막에 붙는다(§2.5 정렬).
    if block.get("status") == "overridden" and not pm_decisions:
        missing_pm_activity.append({
            "row_id": None, "row_key": None, "stage": None,
            "expected": "activity(decision)", "anchor": "override_bundle",
        })
    result["missing_pm_activity"] = missing_pm_activity

    # ── TASK-147 D-14 — Stop 판정 4분류 + D-10(b) activity 오인 방지.
    #
    # `all_records`는 조각의 append 순서 뒤에 outbox 순서를 붙인 결정론적 사건열이다.
    # 이 축은 timestamp나 summary 같은 자유 서술을 재해석하지 않는다. 특히 fixture의
    # 수동 시각이 실제 append 시각과 달라도 사건 *순서*라는 계약을 보존한다.
    # 각 배열은 이 사건열 순서(동일 입력이면 동일 순서)로 생성한다.
    report_intent_inconsistent = []
    missing_stop_decision = []
    stop_decision_allowed = []
    stop_block_without_followup = []
    unanchored_activity = []
    # missing_stop_decision의 뒤 앵커가 된 사건은 해당 "다음 턴"을 증명하는
    # 용도다. 같은 사건을 unanchored_activity에도 중복 계상하면 D-14의 4분류가
    # 서로 배타라는 S-9 계약을 깨므로 구조적 앵커로 소비한다.
    missing_stop_anchor_event_ids = set()
    receipt_pending_count = _pending_stop_receipt_count(task_path)

    # activity 앵커는 마지막 state.changed 이후 아직 소비하지 않은 1건이다. 따라서
    # 같은 상태 변화에 기대어 activity를 반복해 "진전"으로 세는 길이 생기지 않는다.
    # data.kind/사건 존재만 보며 summary는 어떤 비교에도 쓰지 않는다.
    available_state_anchor_id = None
    for index, rec in enumerate(all_records):
        if not isinstance(rec, dict):
            continue
        event_type = rec.get("event")
        if event_type == "state.changed":
            available_state_anchor_id = rec.get("event_id")
            continue

        if event_type == "pm.report":
            data = rec.get("data") if isinstance(rec.get("data"), dict) else {}
            report_type = data.get("report_type")
            transition_action = data.get("transition_action")
            user_input_required = data.get("user_input_required")
            if ((report_type == "decision_request" and transition_action == "continue")
                    or (report_type == "progress_report" and user_input_required is True)):
                report_intent_inconsistent.append({
                    "event_id": rec.get("event_id"),
                    "report_type": report_type,
                    "transition_action": transition_action,
                    "user_input_required": user_input_required,
                })

            # "부재"는 바로 다음 사건이라는 뒤 앵커가 있을 때만 확정한다. 다음
            # stop.decision이면 hook이 실행된 것이고, 어떤 다른 사건이면 그 사이에
            # Stop 판정이 없었던 것이다. 마지막 보고는 뒤 앵커가 없어 제외한다.
            if index + 1 < len(all_records):
                next_rec = all_records[index + 1]
                if isinstance(next_rec, dict) and next_rec.get("event") != "stop.decision":
                    missing_stop_anchor_event_ids.add(next_rec.get("event_id"))
                    missing_stop_decision.append({
                        "report_event_id": rec.get("event_id"),
                        "next_event_id": next_rec.get("event_id"),
                        "receipt_pending": receipt_pending_count > 0,
                    })
            continue

        if event_type == "stop.decision":
            data = rec.get("data") if isinstance(rec.get("data"), dict) else {}
            decision_kind = data.get("decision_kind")
            if isinstance(decision_kind, str) and decision_kind.startswith("allow_"):
                stop_decision_allowed.append({
                    "event_id": rec.get("event_id"),
                    "decision_kind": decision_kind,
                })
            if decision_kind == "block_continue":
                boundary_event_id = None
                has_followup = False
                for later_rec in all_records[index + 1:]:
                    if not isinstance(later_rec, dict):
                        continue
                    later_event = later_rec.get("event")
                    if later_event in ("stop.decision", "run.completed"):
                        boundary_event_id = later_rec.get("event_id")
                        break
                    if later_event in ("activity", "state.changed"):
                        has_followup = True
                        break
                if not has_followup:
                    stop_block_without_followup.append({
                        "event_id": rec.get("event_id"),
                        "boundary_event_id": boundary_event_id,
                    })
            continue

        if event_type != "activity":
            continue
        if rec.get("event_id") in missing_stop_anchor_event_ids:
            continue
        if available_state_anchor_id is None:
            unanchored_activity.append({
                "event_id": rec.get("event_id"),
                "anchor_event_id": None,
                "reason": "no_state_change_anchor",
            })
        else:
            # 한 state.changed는 activity 한 건의 구조 앵커일 뿐이다. 이 소비 규칙은
            # 동일 결과의 반복을 summary 파싱 없이 결정론적으로 드러낸다.
            available_state_anchor_id = None

    result["report_intent_inconsistent"] = report_intent_inconsistent
    result["missing_stop_decision"] = missing_stop_decision
    result["stop_decision_allowed"] = stop_decision_allowed
    result["stop_block_without_followup"] = stop_block_without_followup
    result["unanchored_activity"] = unanchored_activity

    # ── 관측 지점 3필드 (AC-7) — committed+pending 전 구간에서 마지막 레코드를 찾는다.
    def _observation(rec):
        if not rec:
            return None
        return {"event_id": rec.get("event_id"), "ts": rec.get("timestamp"), "ref": rec.get("event")}

    decisions = [
        rec for rec in all_records
        if rec.get("event") == "activity" and isinstance(rec.get("data"), dict)
        and rec["data"].get("kind") == "decision"
    ]
    state_changes = [rec for rec in all_records if rec.get("event") == "state.changed"]
    boundaries = [rec for rec in all_records if rec.get("event") in _RUN_LOG_BOUNDARY_EVENTS]

    result["last_observed_decision"] = _observation(decisions[-1] if decisions else None)
    result["last_observed_state_change"] = _observation(state_changes[-1] if state_changes else None)
    result["last_observed_boundary"] = _observation(boundaries[-1] if boundaries else None)

    return result


def _validate_run_log_refs(refs, command):
    """CONTRACT §1.1 refs 제약 — 프로젝트 상대 경로만 허용, 절대 경로는 거부한다
    (원문 그대로 저장하지 않는다는 선택 대신, 명시적 거부를 택한다 — 회신에 명시).
    """
    if not refs:
        return None
    normalized = list(refs)
    for ref in normalized:
        if pathlib.Path(ref).is_absolute():
            _rl_err(command, "refs_invalid", ref=ref)
    return normalized


def _build_pm_activity_data(args, command):
    """CONTRACT §1.3 PM activity 폐쇄 목록 — `data`는 `kind` 1개 키만 허용하고
    값은 `{decision, validation, retry, progress}` 4종 enum이다. 위반은
    `schema_invalid`로 거부한다(§1.1 폐쇄형 스키마 위반 범위).

    이 검증은 **기록 코어 집행의 앞단 중복 방어**다(137 D-9) — 같은 폐쇄 판정을
    기록 코어의 `validate_event()`도 수행하며 두 지점의 판정 결과는 항상 일치한다.
    CLI 인자 단계에서 더 구체적인 detail을 내기 위해 유지한다.
    """
    raw_data = getattr(args, "data", None)
    if raw_data:
        try:
            parsed = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            _rl_err(command, "schema_invalid", detail=f"--data가 유효한 JSON이 아님: {exc}")
        if not isinstance(parsed, dict) or set(parsed.keys()) != {"kind"}:
            _rl_err(command, "schema_invalid",
                detail="activity data는 kind 1개 키만 허용합니다(CONTRACT §1.3 폐쇄 목록)")
        kind = parsed.get("kind")
    else:
        kind = args.kind
    if kind not in _PM_ACTIVITY_KIND_ENUM:
        _rl_err(command, "schema_invalid",
            detail=f"data.kind={kind!r}는 4종 enum 밖입니다(CONTRACT §1.3)")
    return {"kind": kind}


def _build_pm_report_data(args, command):
    """CONTRACT §1.3 `pm.report` 폐쇄 목록 — `data`는 `report_type`·
    `transition_action`·`user_input_required` **정확히 3키**이고 값은 각각
    2종·4종 enum과 boolean이다. 위반은 `schema_invalid`로 거부한다(D-2).

    `_build_pm_activity_data()`의 **형제**이며 같은 앞단 중복 방어 형태를 그대로
    복제한다 — 집행 지점은 기록 코어 `validate_event()` 한 곳이고(§1.3), 여기서는
    CLI 인자 단계에서 더 구체적인 detail을 내기 위해 같은 판정을 한 번 더 한다.
    [MUST] 두 지점의 판정 결과는 항상 일치한다(TASK-147.S-6이 이를 단언한다) —
    그래서 `--report-type`·`--transition-action` 값 검증을 argparse `choices`로
    하지 않는다. argparse가 거르면 앞단 오류 코드가 usage 오류(exit 2)가 되어
    기록 코어의 `schema_invalid`와 갈린다.
    """
    raw_data = getattr(args, "data", None)
    if raw_data:
        try:
            parsed = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            _rl_err(command, "schema_invalid", detail=f"--data가 유효한 JSON이 아님: {exc}")
        if not isinstance(parsed, dict) or set(parsed.keys()) != _PM_REPORT_DATA_KEYS:
            keys = sorted(parsed.keys()) if isinstance(parsed, dict) else None
            _rl_err(command, "schema_invalid",
                detail=f"pm.report data는 {sorted(_PM_REPORT_DATA_KEYS)} 3키 폐쇄입니다"
                       f"(CONTRACT §1.3) — 받은 키: {keys}")
        report_type = parsed.get("report_type")
        transition_action = parsed.get("transition_action")
        user_input_required = parsed.get("user_input_required")
    else:
        report_type = getattr(args, "report_type", None)
        transition_action = getattr(args, "transition_action", None)
        raw_flag = getattr(args, "user_input_required", None)
        if raw_flag is None:
            user_input_required = None
        elif isinstance(raw_flag, bool):
            user_input_required = raw_flag
        elif raw_flag in ("true", "false"):
            user_input_required = (raw_flag == "true")
        else:
            user_input_required = raw_flag

    if report_type not in _PM_REPORT_TYPE_ENUM:
        _rl_err(command, "schema_invalid",
            detail=f"data.report_type={report_type!r}는 2종 enum 밖입니다(CONTRACT §1.3)")
    if transition_action not in _PM_TRANSITION_ACTION_ENUM:
        _rl_err(command, "schema_invalid",
            detail=f"data.transition_action={transition_action!r}는 4종 enum 밖입니다"
                   "(CONTRACT §1.3)")
    if not isinstance(user_input_required, bool):
        _rl_err(command, "schema_invalid",
            detail=f"data.user_input_required={user_input_required!r}는 boolean이어야 "
                   "합니다(CONTRACT §1.3)")
    return {
        "report_type": report_type,
        "transition_action": transition_action,
        "user_input_required": user_input_required,
    }


def _build_pm_activity_event(state, *, task_id, command, kind, summary, reason, refs,
                             stage, task_step, work_item):
    """PM `activity` 사건(조합 A4: actor.kind=PM, provenance.type=direct,
    recorded_by.kind=PM) — §1.1 공통 필드 전건 + §1.3 폐쇄 목록 준수 payload.
    """
    core = base._import_run_log_core()
    block = _run_log_block(state) or {}
    return {
        "schema_version": "1.0",
        "event_id": core.new_event_id(),
        "request_id": f"req_{uuid.uuid4()}",
        "task_id": task_id,
        "run_id": block.get("active_run_id"),
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": None,
        "stage": stage,
        "task_step": task_step,
        "work_item": work_item,
        "gate_id": None,
        "event": "activity",
        "actor": {"kind": "PM", "id": "PM", "provider": None,
                  "session_id": _current_session_id()},  # 138 W-9
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "PM", "id": "PM"},
            "worker_log_token_id": None,
            "source": None,
        },
        "summary": summary,
        "reason": reason,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": refs,
        "timestamp": core.utc_now_ms(),
        "data": kind,
    }


def _build_pm_report_event(state, *, task_id, command, data, stage, task_step,
                           work_item):
    """PM `pm.report` 사건(조합 A4: actor.kind=PM, provenance.type=direct,
    recorded_by.kind=PM) — §1.1 공통 필드 전건 + §1.3 `data` 폐쇄 3키 준수 payload.

    `_build_pm_activity_event()`의 **형제**다 — 공통 필드 골격은 동일하고 `event`와
    `data`만 다르다. `activity`의 하위 축이 아니라 별도 사건이므로 완료 게이트에
    기여하지 않는다(D-1·D-2). D-16은 호출자 자유 서술을 저장 후보로 만들지 않는다:
    기록 코어의 결정론 renderer가 구조화 3축만 받아 summary를 만들고, 나머지 서술
    축은 null로 닫는다.
    """
    core = base._import_run_log_core()
    block = _run_log_block(state) or {}
    return {
        "schema_version": "1.0",
        "event_id": core.new_event_id(),
        "request_id": f"req_{uuid.uuid4()}",
        "task_id": task_id,
        "run_id": block.get("active_run_id"),
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": None,
        "stage": stage,
        "task_step": task_step,
        "work_item": work_item,
        "gate_id": None,
        "event": "pm.report",
        "actor": {"kind": "PM", "id": "PM", "provider": None,
                  "session_id": _current_session_id()},
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "PM", "id": "PM"},
            "worker_log_token_id": None,
            "source": None,
        },
        "summary": core.render_event_summary("pm.report", data),
        "reason": None,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": None,
        "timestamp": core.utc_now_ms(),
        "data": data,
    }


def cmd_log_event(args):
    """state-tool log-event — PM direct 사건 기록 (CONTRACT §2.4 state-tool.log-event).

    `--event`는 `activity`·`pm.report` 2종을 수용한다(TASK-147 D-2, §2.4).
    `stop.decision`은 이 표면이 수용하지 않는다 — 그 사건은 Stop hook receipt의
    drain 경로가 조립한다(D-6).

    `actor.kind=worker` 지정은 `actor_not_allowed`로 거부한다(§9) — 이 표면은
    PM actor 사건만 수용한다. run_log_commit()의 공통 outbox/admission/drain
    경로를 그대로 재사용한다.
    """
    command = "log-event"
    actor_kind = getattr(args, "actor", None) or "PM"
    if actor_kind != "PM":
        _rl_err(command, "actor_not_allowed", actor_kind=actor_kind)

    task_path = _require_absolute_task_path(args.task_path, command)
    state = load_state_json(task_path, command)

    event_name = getattr(args, "event", None)

    if event_name == "pm.report":
        # D-16 / CONTRACT §1.3.1 — legacy `--summary`는 CLI 호환을 위해 수용하되
        # 저장하지 않는다. 반대로 reason/refs는 사건의 닫힌 서술 축을 열므로 어떤
        # 값도 검증·정규화하지 않고 쓰기 전에 schema_invalid로 거부한다.
        if getattr(args, "reason", None) is not None or getattr(args, "refs", None) is not None:
            _rl_err(command, "schema_invalid",
                    detail="pm.report는 --reason 또는 --refs를 허용하지 않습니다(CONTRACT §1.3.1)")
        report_data = _build_pm_report_data(args, command)
        event = _build_pm_report_event(
            state, task_id=task_path.name, command=command,
            data=report_data, stage=getattr(args, "stage", None),
            task_step=getattr(args, "task_step", None),
            work_item=getattr(args, "work_item", None))
    else:
        refs = _validate_run_log_refs(getattr(args, "refs", None), command)
        data_kind = _build_pm_activity_data(args, command)
        event = _build_pm_activity_event(
            state, task_id=task_path.name, command=command,
            kind=data_kind, summary=args.summary, reason=getattr(args, "reason", None),
            refs=refs, stage=getattr(args, "stage", None),
            task_step=getattr(args, "task_step", None),
            work_item=getattr(args, "work_item", None))

    fields = run_log_commit(task_path, state, command, event=event)
    warnings = fields.get("warnings") or []
    if any(w.get("code") == "run_log_pending" for w in warnings):
        pending_count = ((fields.get("run_log") or {}).get("pending") or 0)
        _rl_err(command, "run_log_pending", count=pending_count)

    status = (fields.get("run_log") or {}).get("status")
    ok(command, event_id=event["event_id"], status=status)


def _build_gate_event(state, *, task_id, command, event_name, gate_id, actor_kind,
                      summary, reason, data):
    """`gate.requested`/`gate.resolved` 공통 골격 — §1.1 공통 필드 전건.

    `actor.kind=PM`이면 조합 A4, `user`면 A5, `auto`면 A6이다. 세 조합 모두
    `recorded_by.kind ∈ {PM, tool}`(A4)·`{PM, tool}`(A5)·`{tool}`(A6)을 허용하므로
    `recorded_by.kind="tool"`(state-tool 자신)로 통일해도 세 조합 모두에 유효하다.
    """
    core = base._import_run_log_core()
    block = _run_log_block(state) or {}
    return {
        "schema_version": "1.0",
        "event_id": core.new_event_id(),
        "request_id": f"req_{uuid.uuid4()}",
        "task_id": task_id,
        "run_id": block.get("active_run_id"),
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": None,
        "stage": None,
        "task_step": None,
        "work_item": None,
        "gate_id": gate_id,
        "event": event_name,
        "actor": {"kind": actor_kind, "id": actor_kind, "provider": None,
                  "session_id": _current_session_id()},  # 138 W-9
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "tool", "id": "state-tool"},
            "worker_log_token_id": None,
            "source": None,
        },
        "summary": summary,
        "reason": reason,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": None,
        "timestamp": core.utc_now_ms(),
        "data": data,
    }


def cmd_gate_request(args):
    """state-tool gate-request — `gate.requested` 기록 (CONTRACT §2.4 state-tool.gate-request).

    같은 `gate_id`의 중복 requested는 `gate_duplicate`로 거부한다(§4.4). 조각 +
    아직 드레인되지 않은 보관함 양쪽에서 유일성을 판정한다.
    """
    command = "gate-request"
    task_path = _require_absolute_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    block = _run_log_block(state)

    if block is not None:
        existing = _run_log_all_records(task_path, block)
        if any(r.get("event") == "gate.requested" and r.get("gate_id") == args.gate_id
               for r in existing):
            _rl_err(command, "gate_duplicate", gate_id=args.gate_id, event="gate.requested")

    event = _build_gate_event(
        state, task_id=task_path.name, command=command,
        event_name="gate.requested", gate_id=args.gate_id, actor_kind="PM",
        summary=args.summary, reason=None, data=None)

    fields = run_log_commit(task_path, state, command, event=event)
    warnings = fields.get("warnings") or []
    if any(w.get("code") == "run_log_pending" for w in warnings):
        pending_count = ((fields.get("run_log") or {}).get("pending") or 0)
        _rl_err(command, "run_log_pending", count=pending_count)

    status = (fields.get("run_log") or {}).get("status")
    ok(command, event_id=event["event_id"], gate_id=args.gate_id, status=status)


def cmd_gate_resolve(args):
    """state-tool gate-resolve — `gate.resolved` 기록 (CONTRACT §2.4 state-tool.gate-resolve).

    선행 `gate.requested` 없는 resolve는 `gate_not_requested`, 같은 `gate_id`의
    중복 resolved는 `gate_duplicate`로 거부한다. 대기 시간(`waited_ms`)은 두
    사건의 UTC timestamp 차분으로만 계산한다(§2.4 계약 불변식) — 벽시계를
    별도로 다시 재지 않는다.
    """
    command = "gate-resolve"
    task_path = _require_absolute_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    block = _run_log_block(state)

    existing = _run_log_all_records(task_path, block) if block is not None else []
    requested = [r for r in existing
                 if r.get("event") == "gate.requested" and r.get("gate_id") == args.gate_id]
    if not requested:
        _rl_err(command, "gate_not_requested", gate_id=args.gate_id)
    if any(r.get("event") == "gate.resolved" and r.get("gate_id") == args.gate_id
           for r in existing):
        _rl_err(command, "gate_duplicate", gate_id=args.gate_id, event="gate.resolved")

    actor_kind_map = {"PM": "PM", "user": "user", "auto": "auto"}
    actor_kind = actor_kind_map.get(args.owner, "PM")

    event = _build_gate_event(
        state, task_id=task_path.name, command=command,
        event_name="gate.resolved", gate_id=args.gate_id, actor_kind=actor_kind,
        summary=getattr(args, "note", None) or f"gate {args.gate_id} resolved: {args.verdict}",
        reason=getattr(args, "note", None),
        data={"verdict": args.verdict})

    core = base._import_run_log_core()
    requested_ts = requested[0].get("timestamp")
    waited_ms = None
    if requested_ts:
        try:
            fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
            t0 = datetime.strptime(requested_ts, fmt).replace(tzinfo=timezone.utc)
            t1 = datetime.strptime(event["timestamp"], fmt).replace(tzinfo=timezone.utc)
            waited_ms = int((t1 - t0).total_seconds() * 1000)
        except ValueError:
            waited_ms = None

    fields = run_log_commit(task_path, state, command, event=event)
    warnings = fields.get("warnings") or []
    if any(w.get("code") == "run_log_pending" for w in warnings):
        pending_count = ((fields.get("run_log") or {}).get("pending") or 0)
        _rl_err(command, "run_log_pending", count=pending_count)

    status = (fields.get("run_log") or {}).get("status")
    ok(command, event_id=event["event_id"], gate_id=args.gate_id,
       waited_ms=waited_ms, status=status)
