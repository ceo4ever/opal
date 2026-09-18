"""
@header {
  "module": "ownership_tool.session_registry",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "D-5 세션 registry 저장소(<project_root>/.opal/run/.runtime/sessions/<session_id>.json) 기록기. register가 {session_id, cwd, started_at, heartbeat_at, expires_at, status} 레코드를 ownership_core.write_json_atomic으로 원자 기록하며, 같은 세션 재등록은 started_at을 보존하고 heartbeat_at·expires_at만 갱신한다(멱등). TTL은 lease.resolve_ttl_sec를 재사용해 lease와 같은 값으로 만료되게 하고 자체 기본값을 두지 않는다. 실패는 예외가 아니라 ok/error 구조화 dict로 반환한다.",
  "exports": ["STATUS_ACTIVE", "register"],
  "depends": ["ownership_tool.ownership_core", "ownership_tool.lease"]
}
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import lease, ownership_core

STATUS_ACTIVE = "active"

# lease 레코드와 같은 표기(KST aware ISO 8601)로 시각을 남긴다.
_KST = timezone(timedelta(hours=9))


def _now_dt(now):
    if isinstance(now, datetime):
        return now
    if now is not None:
        try:
            return datetime.fromisoformat(str(now))
        except ValueError:
            pass
    return datetime.now(_KST)


def register(project_root, session_id, cwd, *, now=None, ttl_sec=None):
    """세션 레코드를 기록한다. 성공 {"ok": True, "path", "record"} / 실패 구조화 dict.

    TTL은 `lease.resolve_ttl_sec(project_root, ttl_sec)`로 해석해 lease와 동일한
    만료 기준을 쓴다. 기존 레코드가 있으면 `started_at`을 보존한다.
    """
    if not session_id:
        return {"ok": False, "error": "no_session_id"}

    path = ownership_core.session_registry_path(project_root, session_id)
    now_dt = _now_dt(now)
    effective_ttl = lease.resolve_ttl_sec(project_root, ttl_sec)

    existing = ownership_core.read_json(path)
    started_at = None
    if existing.get("ok") and isinstance(existing.get("data"), dict):
        started_at = existing["data"].get("started_at")

    record = ownership_core.SessionRecord(
        session_id=session_id,
        cwd=str(cwd) if cwd is not None else None,
        started_at=started_at or now_dt.isoformat(),
        heartbeat_at=now_dt.isoformat(),
        expires_at=(now_dt + timedelta(seconds=effective_ttl)).isoformat(),
        status=STATUS_ACTIVE,
    ).to_dict()
    write = ownership_core.write_json_atomic(path, record)
    if not write["ok"]:
        return {"ok": False, "error": write["error"], "path": write.get("path")}
    return {"ok": True, "path": write["path"], "record": record}
