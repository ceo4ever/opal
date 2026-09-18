"""
@header {
  "module": "ownership_tool.session_start_hook",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "SessionStart hook 어댑터(W-7). 봉투의 session_id·cwd를 session_registry에 등록하고, 어댑터가 알려준 env 파일에 OPAL_SESSION_ID=<id> 1줄을 append해 이후 Bash 호출이 같은 ID를 받게 한다(파일 미제공·쓰기 실패는 진단만 남기고 등록은 유지). 루트 판정은 ownership_core.resolve_roots가 소유한다(D-20) — 워크트리 세션은 발급값 사본 <cwd>/.opal/task-ownership.json이 준 task_path를 canonical로 삼고, 허브 세션은 <allocator_root>/.opal-worktrees/.meta/task_*.json 발급값과 cwd가 정확히 일치할 때만 태스크를 얻으며, 루트가 해석되지 않으면 추측하지 않고 진단만 남기고 통과한다(등록·env append는 이 분기에서도 수행). 해석된 canonical task에만 lease.claim(claim_source=session_start — D-21 수동 소유권)을 시도하고 기존 live owner가 있으면 이전하지 않고 foreign_owner로 거부한다. TTL은 lease.resolve_ttl_sec 재사용이고 플랫폼 고유 변수명은 claude_adapter에만 둔다(C-15). 전 경로 fail-safe exit 0.",
  "exports": ["SESSION_ID_ENV_LINE_KEY", "handle", "main"],
  "depends": ["ownership_tool.ownership_core", "ownership_tool.lease", "ownership_tool.session_registry", "ownership_tool.claude_adapter"]
}
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

if __package__:
    from . import claude_adapter, lease, ownership_core, session_registry
else:
    # hook은 이 파일을 경로로 직접 실행한다(패키지 컨텍스트 없음) — tool-dir을 path에 올린다.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from ownership_tool import claude_adapter, lease, ownership_core, session_registry

# env 파일에 남기는 OPAL 중립 키. 플랫폼 변수명이 아니므로 이 모듈이 소유한다.
SESSION_ID_ENV_LINE_KEY = "OPAL_SESSION_ID"

# registry meta 파일명 패턴 — 발급 계약이 정한 위치만 읽는다(추론하지 않는다).
_REGISTRY_META_GLOB = "task_*.json"


def _load_registry(allocator_root):
    """<allocator_root>/.opal-worktrees/.meta/task_*.json 전건을 이름순으로 읽는다.

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
    entries = []
    for name in names:
        read = ownership_core.read_json(meta_dir / name)
        if read.get("ok") and isinstance(read.get("data"), dict):
            entries.append(read["data"])
    return entries


def _canonical_task_path(cwd):
    """cwd의 canonical task_path와 루트 진단을 (task_path, diagnostic)으로 돌려준다.

    루트 판정은 전부 ownership_core.resolve_roots가 소유한다(D-20) — 이 모듈은 cwd 문자열
    자르기·부모 디렉터리 순회·`.opal-worktrees` 문자열 탐색을 하지 않는다
    (harness/worktree.md §task root와 allocator root 계약). 분기는 3개다.

    ① kind="worktree" — 허브가 내려보낸 발급값 사본이 준 `task_path`를 그대로 canonical로
       삼는다. 사본은 발급값이므로 이를 근거로 추가 탐색·검증 스캔을 하지 않는다.
    ② kind="hub" — `allocator_root`의 registry 발급값과 cwd가 정확히 일치할 때만
       (`task_home` 일치 시 같은 entry의 `task_path`, 또는 `task_path` 자체 일치) 그 값이다.
       허브 루트 cwd는 어떤 발급값과도 일치하지 않으므로 세션 시작만으로 태스크를 얻지 못한다.
    ③ ok=False — 추측하지 않고 resolve_roots의 진단을 그대로 돌려준다.
    """
    if not cwd:
        return None, "no_cwd"
    roots = ownership_core.resolve_roots(cwd)
    if not roots.get("ok"):
        return None, roots.get("diagnostic")
    if roots.get("kind") == "worktree":
        return roots.get("task_path"), None

    target = str(pathlib.Path(str(cwd)))
    for entry in _load_registry(roots.get("allocator_root")):
        task_path = entry.get("task_path")
        if not task_path:
            continue
        home = entry.get("task_home")
        if home and str(pathlib.Path(str(home))) == target:
            return task_path, None
        if str(pathlib.Path(str(task_path))) == target:
            return task_path, None
    return None, None


def _append_session_id(env_file_path, session_id):
    """env 파일에 `OPAL_SESSION_ID=<id>` 1줄을 append한다. (성공 여부, 진단)."""
    if not env_file_path:
        return False, "env_file_not_provided"
    try:
        with open(str(env_file_path), "a", encoding="utf-8") as handle:
            handle.write("{}={}\n".format(SESSION_ID_ENV_LINE_KEY, session_id))
        return True, None
    except OSError as exc:  # 쓰기 실패는 진단만 남기고 등록은 유지한다.
        return False, "env_file_write_failed:{}".format(exc)


def handle(payload, project_root=None, env_file_path=None, env=None, now=None):
    """SessionStart 봉투를 처리해 구조화 결과를 돌려준다. 예외를 던지지 않는다.

    반환 키: exit_code(항상 0) · session_id · registered · env_file_written ·
    lease_claimed · classification · task_path · diagnostics.
    """
    payload = payload if isinstance(payload, dict) else {}
    env = os.environ if env is None else env
    result = {
        "exit_code": 0,
        "session_id": None,
        "registered": False,
        "env_file_written": False,
        "lease_claimed": False,
        "classification": None,
        "task_path": None,
        "diagnostics": [],
    }

    session_id = ownership_core.resolve_session_id(env, payload)
    result["session_id"] = session_id
    if not session_id:
        result["diagnostics"].append("no_session_id")
        return result

    cwd = payload.get("cwd") or project_root
    root = project_root if project_root is not None else cwd

    registered = session_registry.register(root, session_id, cwd, now=now)
    result["registered"] = bool(registered.get("ok"))
    if not registered.get("ok"):
        result["diagnostics"].append("session_register_failed:{}".format(registered.get("error")))

    if env_file_path is None:
        env_file_path = (env or {}).get(claude_adapter.ENV_FILE_ENV)
    written, env_diagnostic = _append_session_id(env_file_path, session_id)
    result["env_file_written"] = written
    if env_diagnostic:
        result["diagnostics"].append(env_diagnostic)

    task_path, roots_diagnostic = _canonical_task_path(cwd)
    if roots_diagnostic:
        result["diagnostics"].append(roots_diagnostic)
    if task_path is None:
        result["diagnostics"].append("no_owned_task")
        return result

    result["task_path"] = task_path
    claimed = lease.claim(task_path, session_id=session_id,
                          claim_source="session_start", now=now, project_root=root)
    if claimed.get("ok"):
        result["lease_claimed"] = True
        result["classification"] = "current_session_owned"
        return result

    diagnostic = claimed.get("diagnostic")
    result["classification"] = diagnostic
    result["diagnostics"].append(diagnostic)
    return result


def main():
    """stdin SessionStart 봉투 → handle. hook 출력은 없다(등록·claim만 수행)."""
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
