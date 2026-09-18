"""
@header {
  "module": "ownership_tool.lease",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "hub task lease 저장소(<canonical_task>/run/.runtime/owner.json) claim·heartbeat·release·classify. D-5 스키마(task_path·owner_session_id·generation·claimed_at·heartbeat_at·lease_expires_at·status)로 ownership_core.write_json_atomic을 통해 원자 기록한다. TTL 우선순위는 resolve_ttl_sec — ① claim(ttl_sec=) 명시 인자 ② <project_root>/.opal/setting.local.json의 ownership.lease_ttl_sec ③ 기본 14400(fail-safe, 설정 파일 부재·파싱 실패·비정수는 예외 없이 ③으로 폴백). project_root는 추론하지 않고 호출자가 명시적으로 전달할 때만 ②를 적용한다. 레코드는 claim 출처를 claim_source(폐쇄 enum session_start·state_transition)로 함께 기록한다 — resolve_claim_source가 키 없는 구버전 레코드를 state_transition으로 접어 하위호환을 지키고, enum 밖 값은 예외 대신 claim_source_invalid 거부이며 파일을 쓰지 않는다. 같은 세션 재-claim은 session_start→state_transition 승격만 하고 강등하지 않으며 승격 시 generation·claimed_at·owner_session_id는 불변이다. classify는 lease_expires_at과 요청 session_id만으로 current_session_owned·foreign_session_owned·unowned·lease_expired 중 하나를 판정하며 예외 대신 구조화 값을 반환한다.",
  "exports": ["claim", "heartbeat", "release", "classify", "resolve_ttl_sec", "resolve_claim_source", "CLAIM_SOURCES"],
  "depends": ["ownership_tool.ownership_core"]
}
"""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timedelta, timezone

from . import ownership_core

DEFAULT_TTL_SEC = 14400
# D-21 — claim 출처 폐쇄 enum. session_start는 SessionStart 자동 claim(수동 소유권),
# state_transition은 state-tool 상태 전이 claim(능동 소유권)이다.
CLAIM_SOURCES = ("session_start", "state_transition")
DEFAULT_CLAIM_SOURCE = "state_transition"
_KST = timezone(timedelta(hours=9))
_SETTING_REL_PATH = pathlib.Path(".opal") / "setting.local.json"


def resolve_ttl_sec(project_root=None, ttl_sec=None):
    """lease TTL(초)을 우선순위대로 해석한다.

    ① 명시 `ttl_sec` 인자 ② `<project_root>/.opal/setting.local.json`의
    `ownership.lease_ttl_sec` ③ 기본 `DEFAULT_TTL_SEC`(14400). project_root는
    호출자가 명시적으로 준 경우에만 사용하며 canonical task_path로부터
    추론하지 않는다. 설정 파일 부재·손상 JSON·비정수 값은 예외 없이 조용히
    ③으로 폴백한다(fail-safe).
    """
    if ttl_sec is not None:
        return ttl_sec

    if project_root is not None:
        setting_path = pathlib.Path(project_root) / _SETTING_REL_PATH
        try:
            raw = setting_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            value = data.get("ownership", {}).get("lease_ttl_sec")
            if isinstance(value, bool):
                value = None
            if isinstance(value, int):
                return value
        except (OSError, ValueError, AttributeError, TypeError):
            pass

    return DEFAULT_TTL_SEC


def resolve_claim_source(record):
    """lease 레코드의 claim_source를 해석한다.

    `claim_source` 키가 없는 구버전 레코드는 `state_transition`으로 간주한다 —
    배포 시점에 이미 떠 있던 lease의 판정을 바꾸지 않기 위한 하위호환 기본값이다.
    폐쇄 enum 밖 값도 같은 기본값으로 접는다(예외를 던지지 않는다).
    """
    value = record.get("claim_source") if isinstance(record, dict) else None
    if value in CLAIM_SOURCES:
        return value
    return DEFAULT_CLAIM_SOURCE


def _parse_dt(value):
    """ISO 8601(공백 구분 허용) 문자열을 aware datetime으로 변환한다. 실패 시 None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _now_dt(now):
    parsed = _parse_dt(now)
    if parsed is not None:
        return parsed
    return datetime.now(_KST)


def _fmt(dt):
    return dt.isoformat()


def _owner_path(task_path):
    return ownership_core.hub_lease_path(task_path)


def _load_owner(task_path):
    read = ownership_core.read_json(_owner_path(task_path))
    if not read["ok"]:
        return None
    data = read["data"]
    return data if isinstance(data, dict) else None


def _is_live(record, now_dt):
    if not record:
        return False
    if record.get("status") == "released":
        return False
    expires = _parse_dt(record.get("lease_expires_at"))
    if expires is None:
        return False
    return now_dt < expires


def claim(task_path, *, session_id, claim_source=None, now=None, ttl_sec=None, project_root=None):
    """<task_path>/run/.runtime/owner.json에 lease를 기록한다.

    기존 lease가 live(만료 전 + released 아님)이고 다른 세션이면 이전하지 않고
    {"ok": False, "diagnostic": "foreign_owner", ...}를 반환한다. 없음/만료/released면
    새 lease를 생성한다(generation은 기존+1, 없으면 1). 같은 세션 재-claim은 멱등(heartbeat 갱신).
    TTL은 resolve_ttl_sec(project_root, ttl_sec)로 해석한다 — project_root는 호출자가
    명시할 때만 설정 오버라이드에 쓰이며 task_path로부터 추론하지 않는다.

    claim_source는 CLAIM_SOURCES 폐쇄 enum이며 미지정이면 DEFAULT_CLAIM_SOURCE다.
    enum 밖 값은 예외가 아니라 claim_source_invalid 구조화 거부이고 파일을 쓰지 않는다.
    같은 세션 재-claim에서는 session_start → state_transition 승격만 일어나고 강등은
    없다(승격 시 generation·claimed_at·owner_session_id는 불변).
    """
    if claim_source is not None and claim_source not in CLAIM_SOURCES:
        return {
            "ok": False,
            "diagnostic": "claim_source_invalid",
            "task_path": str(task_path),
            "claim_source": claim_source,
        }

    now_dt = _now_dt(now)
    effective_ttl = resolve_ttl_sec(project_root, ttl_sec)
    existing = _load_owner(task_path)

    if existing and _is_live(existing, now_dt) and existing.get("owner_session_id") != session_id:
        return {
            "ok": False,
            "diagnostic": "foreign_owner",
            "task_path": str(task_path),
            "owner_session_id": existing.get("owner_session_id"),
        }

    requested_source = claim_source or DEFAULT_CLAIM_SOURCE
    if existing and existing.get("owner_session_id") == session_id:
        generation = existing.get("generation") or 1
        claimed_at = existing.get("claimed_at") or _fmt(now_dt)
        prior_source = resolve_claim_source(existing)
        # 승격만 허용 — state_transition은 session_start로 되돌아가지 않는다.
        effective_source = (
            "state_transition"
            if "state_transition" in (prior_source, requested_source)
            else prior_source
        )
    else:
        generation = (existing.get("generation") + 1) if existing and existing.get("generation") else 1
        claimed_at = _fmt(now_dt)
        effective_source = requested_source

    record = {
        "task_path": str(task_path),
        "owner_session_id": session_id,
        "generation": generation,
        "claimed_at": claimed_at,
        "heartbeat_at": _fmt(now_dt),
        "lease_expires_at": _fmt(now_dt + timedelta(seconds=effective_ttl)),
        "status": "active",
        "ttl_sec": effective_ttl,
        "claim_source": effective_source,
    }
    write = ownership_core.write_json_atomic(_owner_path(task_path), record)
    if not write["ok"]:
        return {"ok": False, "diagnostic": write["error"], "path": write.get("path")}
    result = dict(record)
    result["ok"] = True
    return result


def heartbeat(task_path, *, session_id, now=None, project_root=None):
    """owner_session_id 일치 시 heartbeat_at·lease_expires_at을 갱신한다. 불일치·부재는 no-op.

    갱신 시 TTL은 기존 레코드의 ttl_sec을 유지한다(claim 시 확정된 값). 레코드에
    ttl_sec이 없는 구버전 데이터만 resolve_ttl_sec(project_root)로 재해석한다.
    """
    existing = _load_owner(task_path)
    if not existing or existing.get("owner_session_id") != session_id:
        return {"ok": True, "noop": True}

    now_dt = _now_dt(now)
    ttl_sec = existing.get("ttl_sec") or resolve_ttl_sec(project_root)
    record = dict(existing)
    record["heartbeat_at"] = _fmt(now_dt)
    record["lease_expires_at"] = _fmt(now_dt + timedelta(seconds=ttl_sec))
    write = ownership_core.write_json_atomic(_owner_path(task_path), record)
    if not write["ok"]:
        return {"ok": False, "diagnostic": write["error"], "path": write.get("path")}
    result = dict(record)
    result["ok"] = True
    return result


def release(task_path, *, session_id, now=None):
    """owner_session_id 일치 시 status를 released로 표시한다. 불일치·부재는 no-op."""
    existing = _load_owner(task_path)
    if not existing or existing.get("owner_session_id") != session_id:
        return {"ok": True, "noop": True}

    now_dt = _now_dt(now)
    record = dict(existing)
    record["status"] = "released"
    record["heartbeat_at"] = _fmt(now_dt)
    write = ownership_core.write_json_atomic(_owner_path(task_path), record)
    if not write["ok"]:
        return {"ok": False, "diagnostic": write["error"], "path": write.get("path")}
    result = dict(record)
    result["ok"] = True
    return result


def classify(record_or_path, session_id, now=None):
    """lease 레코드(dict) 또는 owner.json 경로를 요청 session_id 기준으로 판정한다.

    반환값: "current_session_owned" | "foreign_session_owned" | "unowned" | "lease_expired".
    같은 세션 소유는 만료 여부와 무관하게 current_session_owned로 판정한다 — 자기 lease
    재-claim/heartbeat의 멱등을 보장하기 위함이며, C-8의 "만료→무소유(lease_expired)"
    판정은 타 세션이 소유한 lease에만 적용된다.
    """
    record = record_or_path
    if isinstance(record_or_path, (str, pathlib.Path)):
        record = _load_owner(record_or_path)

    if not record or not record.get("owner_session_id") or record.get("status") == "released":
        return "unowned"

    if record.get("owner_session_id") == session_id:
        return "current_session_owned"

    now_dt = _now_dt(now)
    expires = _parse_dt(record.get("lease_expires_at"))
    if expires is None or now_dt >= expires:
        return "lease_expired"

    return "foreign_session_owned"
