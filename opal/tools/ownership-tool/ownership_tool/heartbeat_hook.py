"""
@header {
  "module": "ownership_tool.heartbeat_hook",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "PostToolUse hook 어댑터(W-8). matcher 없이 모든 PostToolUse에서 발화해, 해석된 세션이 이미 소유한 lease의 heartbeat_at·lease_expires_at만 lease.heartbeat로 갱신하고 이미 존재하는 세션 registry 엔트리만 session_registry.register로 재등록해 만료를 늦춘다. ownership을 생성·이전하지 않는다 — claim을 호출하지 않으며 봉투가 canonical task를 명시해도 그것을 근거로 소유를 얻지 않고, 소유하지 않은 세션에는 아무 파일도 쓰지 않는다(완전 no-op). 소유 판정은 lease.classify의 current_session_owned 단일 기준이고 후보 task_path는 ownership_core.resolve_roots가 준 발급값(워크트리 사본의 task_path, 허브 registry 발급값)에서만 모은다 — cwd 문자열 자르기·부모 순회·디렉터리 탐색으로 추론하지 않는다. 세션 ID 해석은 ownership_core.resolve_session_id(D-18)에 위임하고 플랫폼 고유 변수명은 갖지 않는다(C-15). 전 경로 fail-safe exit 0.",
  "exports": ["owned_task_paths", "handle", "main"],
  "depends": ["ownership_tool.ownership_core", "ownership_tool.lease", "ownership_tool.session_registry"]
}
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

if __package__:
    from . import lease, ownership_core, session_registry
else:
    # hook은 이 파일을 경로로 직접 실행한다(패키지 컨텍스트 없음) — tool-dir을 path에 올린다.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from ownership_tool import lease, ownership_core, session_registry

# registry meta 파일명 패턴 — 발급 계약이 정한 위치만 읽는다(추론하지 않는다).
_REGISTRY_META_GLOB = "task_*.json"

# lease.classify가 "이 세션이 소유한다"고 판정하는 단일 값.
_OWNED = "current_session_owned"


def _registry_task_paths(allocator_root):
    """<allocator_root>/.opal-worktrees/.meta/task_*.json 발급값의 task_path를 이름순으로 모은다.

    allocator_root는 resolve_roots가 준 발급값만 받는다(이 모듈이 추론하지 않는다).
    디렉터리 부재·손상 JSON은 예외가 아니라 빈 목록/해당 항목 생략으로 처리한다.
    """
    if not allocator_root:
        return []
    meta_dir = pathlib.Path(allocator_root) / ".opal-worktrees" / ".meta"
    try:
        names = sorted(p.name for p in meta_dir.glob(_REGISTRY_META_GLOB))
    except OSError:
        return []
    paths = []
    for name in names:
        read = ownership_core.read_json(meta_dir / name)
        if not (read.get("ok") and isinstance(read.get("data"), dict)):
            continue
        task_path = read["data"].get("task_path")
        if task_path:
            paths.append(str(task_path))
    return paths


def owned_task_paths(cwd, session_id, now=None):
    """session_id가 **이미** 소유한 canonical task_path 목록과 루트 진단을 돌려준다.

    후보는 ownership_core.resolve_roots(D-20)가 준 발급값에서만 모은다 — 워크트리 세션은
    발급값 사본이 적어준 task_path, 허브 registry는 그 발급값들이다. 소유 판정은
    lease.classify 하나뿐이라 만료 lease는 이 목록에 들어오지 않는다(TTL 회수).
    후보를 훑기만 하고 아무것도 쓰지 않으므로 소유하지 않은 세션에는 no-op이다.
    """
    if not cwd or not session_id:
        return [], "no_cwd" if not cwd else "no_session_id"

    roots = ownership_core.resolve_roots(cwd)
    if not roots.get("ok"):
        return [], roots.get("diagnostic")

    candidates = []
    task_path = roots.get("task_path")
    if task_path:
        candidates.append(str(task_path))
    for path in _registry_task_paths(roots.get("allocator_root")):
        if path not in candidates:
            candidates.append(path)

    return [p for p in candidates if lease.classify(p, session_id, now) == _OWNED], None


def handle(payload, project_root=None, env=None, now=None):
    """PostToolUse 봉투를 처리해 구조화 결과를 돌려준다. 예외를 던지지 않는다.

    반환 키: exit_code(항상 0) · session_id · refreshed(갱신된 task_path 목록) ·
    registry_refreshed · noop · diagnostics.

    [MUST] 여기서 lease.claim을 호출하지 않는다 — 봉투가 canonical task를 명시하더라도
    소유를 얻거나 이전하지 않고, 이미 소유한 lease의 갱신까지만 한다.
    """
    payload = payload if isinstance(payload, dict) else {}
    env = os.environ if env is None else env
    result = {
        "exit_code": 0,
        "session_id": None,
        "refreshed": [],
        "registry_refreshed": False,
        "noop": True,
        "diagnostics": [],
    }

    session_id = ownership_core.resolve_session_id(env, payload)
    result["session_id"] = session_id
    if not session_id:
        result["diagnostics"].append("no_session_id")
        return result

    cwd = payload.get("cwd") or project_root
    root = project_root if project_root is not None else cwd

    # 세션 registry는 **이미 있는** 엔트리만 재등록해 만료를 늦춘다. 없는 엔트리를 만들면
    # 소유하지 않은 세션의 PostToolUse가 no-op이 아니게 되므로 만들지 않는다.
    if root and ownership_core.read_json(
        ownership_core.session_registry_path(root, session_id)
    ).get("ok"):
        registered = session_registry.register(root, session_id, cwd, now=now)
        result["registry_refreshed"] = bool(registered.get("ok"))
        if not registered.get("ok"):
            result["diagnostics"].append("session_register_failed:{}".format(registered.get("error")))

    owned, roots_diagnostic = owned_task_paths(cwd, session_id, now=now)
    if roots_diagnostic:
        result["diagnostics"].append(roots_diagnostic)

    for task_path in owned:
        beat = lease.heartbeat(task_path, session_id=session_id, now=now, project_root=root)
        if beat.get("ok") and not beat.get("noop"):
            result["refreshed"].append(task_path)
        elif not beat.get("ok"):
            result["diagnostics"].append("heartbeat_failed:{}".format(beat.get("diagnostic")))

    result["noop"] = not (result["refreshed"] or result["registry_refreshed"])
    return result


def main():
    """stdin PostToolUse 봉투 → handle. hook 출력은 없다(갱신만 수행)."""
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
