"""
@header {
  "module": "ownership_tool.session_end_hook",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "SessionEnd hook 어댑터(W-8). 종료하는 세션이 소유한 lease 전건을 lease.release로 released 전이시키고, <project_root>/.opal/run/.runtime/sessions/<session_id>.json 레코드의 status를 closed로 바꿔 세션 registry를 닫는다. 소유 task_path 수집은 heartbeat_hook.owned_task_paths(발급값만 읽는 resolve_roots 경유)를 재사용해 판정 규칙을 한 곳에 둔다 — 소유하지 않은 lease는 건드리지 않고 ownership을 생성·이전하지 않는다. SessionEnd가 발화하지 않는 crash·강제 종료는 이 훅이 아니라 TTL 만료가 회수하며 만료 lease는 lease.classify가 unowned로 판정한다(새 분류 로직을 두지 않는다). 세션 ID 해석은 ownership_core.resolve_session_id(D-18)에 위임하고 플랫폼 고유 변수명은 갖지 않는다(C-15). 전 경로 fail-safe exit 0.",
  "exports": ["SESSION_STATUS_CLOSED", "handle", "main"],
  "depends": ["ownership_tool.ownership_core", "ownership_tool.lease", "ownership_tool.heartbeat_hook"]
}
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

if __package__:
    from . import heartbeat_hook, lease, ownership_core
else:
    # hook은 이 파일을 경로로 직접 실행한다(패키지 컨텍스트 없음) — tool-dir을 path에 올린다.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from ownership_tool import heartbeat_hook, lease, ownership_core

# 세션 registry 레코드의 종료 상태. active(session_registry.STATUS_ACTIVE)의 짝이다.
SESSION_STATUS_CLOSED = "closed"


def _close_registry(project_root, session_id):
    """세션 registry 레코드의 status를 closed로 바꾼다. 레코드가 없으면 만들지 않는다."""
    if not project_root:
        return False
    path = ownership_core.session_registry_path(project_root, session_id)
    read = ownership_core.read_json(path)
    if not (read.get("ok") and isinstance(read.get("data"), dict)):
        return False
    record = dict(read["data"])
    record["status"] = SESSION_STATUS_CLOSED
    return bool(ownership_core.write_json_atomic(path, record).get("ok"))


def handle(payload, project_root=None, env=None, now=None):
    """SessionEnd 봉투를 처리해 구조화 결과를 돌려준다. 예외를 던지지 않는다.

    반환 키: exit_code(항상 0) · session_id · released(1건 이상 released 전이 여부) ·
    released_tasks · registry_closed · diagnostics.
    """
    payload = payload if isinstance(payload, dict) else {}
    env = os.environ if env is None else env
    result = {
        "exit_code": 0,
        "session_id": None,
        "released": False,
        "released_tasks": [],
        "registry_closed": False,
        "diagnostics": [],
    }

    session_id = ownership_core.resolve_session_id(env, payload)
    result["session_id"] = session_id
    if not session_id:
        result["diagnostics"].append("no_session_id")
        return result

    cwd = payload.get("cwd") or project_root
    root = project_root if project_root is not None else cwd

    owned, roots_diagnostic = heartbeat_hook.owned_task_paths(cwd, session_id, now=now)
    if roots_diagnostic:
        result["diagnostics"].append(roots_diagnostic)

    for task_path in owned:
        released = lease.release(task_path, session_id=session_id, now=now)
        if released.get("ok") and not released.get("noop"):
            result["released_tasks"].append(task_path)
        elif not released.get("ok"):
            result["diagnostics"].append("release_failed:{}".format(released.get("diagnostic")))

    result["released"] = bool(result["released_tasks"])
    result["registry_closed"] = _close_registry(root, session_id)
    return result


def main():
    """stdin SessionEnd 봉투 → handle. hook 출력은 없다(release·close만 수행)."""
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — 봉투 파싱 실패는 무출력 통과(fail-safe)
        return
    if not isinstance(payload, dict):
        return
    project_root = payload.get("cwd")
    if not project_root:
        return
    handle(payload, project_root=project_root)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 — 전 경로 fail-safe: 어떤 예외에서도 세션을 막지 않는다.
        pass
    sys.exit(0)
