"""
@header {
  "module": "claude_adapter",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "Claude Code 플랫폼 고유 환경변수 어댑터(D-18·C-15). CLAUDE_CODE_SESSION_ID·CLAUDE_CODE_STOP_HOOK_BLOCK_CAP 등 플랫폼 변수명을 이 모듈 한 곳에만 두고 OPAL 중립 값으로 매핑한다. 판정 로직은 갖지 않는다.",
  "exports": ["SESSION_ID_ENV", "ENV_FILE_ENV", "STOP_HOOK_BLOCK_CAP_ENV", "session_id_from_env", "stop_hook_block_cap"],
  "depends": []
}
"""
from __future__ import annotations

SESSION_ID_ENV = "CLAUDE_CODE_SESSION_ID"
ENV_FILE_ENV = "CLAUDE_ENV_FILE"
STOP_HOOK_BLOCK_CAP_ENV = "CLAUDE_CODE_STOP_HOOK_BLOCK_CAP"


def session_id_from_env(env):
    """Claude Code env에서 세션 ID를 읽는다. 없으면 None."""
    if not env:
        return None
    value = env.get(SESSION_ID_ENV)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def stop_hook_block_cap(env):
    """Claude Code env에서 Stop hook 재차단 상한을 읽는다. 미설정·비정수면 None.

    None은 "상한 검사를 건너뛴다"는 뜻이다(H-7). 자체 기본 상한을 두지 않는다.
    """
    if not env:
        return None
    value = env.get(STOP_HOOK_BLOCK_CAP_ENV)
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None
