"""
@header {
  "module": "ownership_tool.codex_adapter",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "Codex native root-session 신원과 공개 codex-start 부트 어댑터. thread ID를 세션 대체값으로 사용하지 않으며 실제 native ID를 기존 payload-only 등록·claim·heartbeat 경로에 전달한다. 부모 중립 신원 충돌은 쓰기 전에 거부한다.",
  "exports": ["SESSION_ID_ENV", "INHERITED_IDENTITY_KEYS", "session_id_from_env", "start"],
  "depends": ["ownership_tool.session_start_hook", "ownership_tool.heartbeat_hook", "ownership_tool.ownership_core"]
}
"""
from __future__ import annotations

import pathlib

SESSION_ID_ENV = "CODEX_SESSION_ID"
# Orca transport identity is inherited host context, never a Codex session fallback.
INHERITED_IDENTITY_KEYS = (SESSION_ID_ENV, "CODEX_THREAD_ID", "ORCA_SESSION_ID")


def session_id_from_env(env):
    """Read the root-session ID injected by Codex into tool processes."""
    value = (env or {}).get(SESSION_ID_ENV)
    return value.strip() if isinstance(value, str) and value.strip() else None


def start(cwd, env):
    """Normalize a real native identity into the existing SessionStart payload."""
    from . import heartbeat_hook, ownership_core, session_start_hook

    session_id = session_id_from_env(env)
    if not session_id:
        return {"ok": False, "error": "session_id_unresolved"}
    neutral = env.get("OPAL_SESSION_ID")
    if isinstance(neutral, str) and neutral.strip() and neutral.strip() != session_id:
        return {"ok": False, "error": "inherited_identity_conflict"}
    payload = {"session_id": session_id, "cwd": str(cwd)}
    root = ownership_core.resolve_project_root(payload, {})
    if not root:
        return {"ok": True, "noop": True, "diagnostic": "no_project_root"}
    # Use the matching source/installed sibling tool; never append to a parent's env file.
    hook_env = {"OPAL_HOME": str(pathlib.Path(__file__).resolve().parents[3])}
    result = session_start_hook.handle(payload, project_root=root, env=hook_env)
    beat = heartbeat_hook.handle(payload, project_root=root, env={})
    registry_error = next((item for item in result["diagnostics"]
                           if item in ("foreign_registry_owner", "ownership_set_failed")), None)
    ok = result["registered"] and (not result["task_path"] or result["lease_claimed"]) and not registry_error
    return {"ok": bool(ok), "error": None if ok else registry_error or result["classification"] or "session_start_failed",
            "session_start": result, "heartbeat": beat}
