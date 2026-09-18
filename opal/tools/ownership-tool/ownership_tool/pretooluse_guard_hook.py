"""
@header {
  "module": "ownership_tool.pretooluse_guard_hook",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "PreToolUse hook 어댑터(W-19, D-6). 첫 분기에서 ownership_core.resolve_roots가 cwd 루트를 해석하지 못하면 후보 수집·lease 조회 없이 즉시 no-op exit 0으로 끝난다(등록 worktree 밖 latency 방어 — 이 경로는 어떤 파일도 쓰지 않는다). 루트가 해석되면 session_start_hook이 소유한 exact 발급값 대조로 canonical task를 얻고 lease.classify가 foreign_session_owned로 판정할 때만 차단을 검토한다. 차단 대상은 D-6의 폐쇄 목록뿐이다 — Edit·Write·NotebookEdit 전건과 Bash 중 git·state-tool·worktree-tool의 쓰기 서브명령이며, 그 밖의 Bash와 읽기 전용 도구(Read·Grep·Glob)는 허용하고 Bash에는 foreign_owner_bash_unclassified 진단만 남긴다(전면 Bash 차단은 D-6이 기각한 대안이다). 진단 어휘는 decisions.DIAGNOSTICS 폐쇄 enum을 재사용하며 새 값을 만들지 않는다. 세션 ID 해석은 ownership_core.resolve_session_id(D-18)에 위임하고 플랫폼 고유 변수명은 갖지 않는다(C-15). 전 경로 fail-safe exit 0.",
  "exports": ["BLOCKED_TOOLS", "BLOCKED_SUBCOMMANDS", "classify_bash", "handle", "to_hook_output", "main"],
  "depends": ["ownership_tool.ownership_core", "ownership_tool.lease", "ownership_tool.session_start_hook"]
}
"""
from __future__ import annotations

import json
import os
import pathlib
import shlex
import sys

if __package__:
    from . import lease, ownership_core, session_start_hook
else:
    # hook은 이 파일을 경로로 직접 실행한다(패키지 컨텍스트 없음) — tool-dir을 path에 올린다.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from ownership_tool import lease, ownership_core, session_start_hook

# D-6 — 전건 차단 도구.
BLOCKED_TOOLS = ("Edit", "Write", "NotebookEdit")

# D-6 — Bash 쓰기 서브명령 폐쇄 목록. 여기 없는 Bash는 차단하지 않는다(기각된 대안 (a)).
BLOCKED_SUBCOMMANDS = {
    "git": (
        "commit", "add", "merge", "push", "rebase", "reset", "checkout", "switch",
        "restore", "stash", "clean", "am", "cherry-pick", "revert", "worktree",
    ),
    "state-tool": (
        "init", "advance", "mark", "block", "add-row", "status", "run-start",
        "finalize-attribution", "log-event", "gate-request", "gate-resolve",
    ),
    "worktree-tool": ("create", "remove", "finalize"),
}

# lease.classify가 "다른 live 세션이 소유한다"고 판정하는 단일 값.
_FOREIGN = "foreign_session_owned"

# D-3 폐쇄 enum 재사용 — 새 diagnostic을 만들지 않는다.
_DIAGNOSTIC_FOREIGN = "foreign_owner"
_DIAGNOSTIC_BASH_UNCLASSIFIED = "foreign_owner_bash_unclassified"

# 한 Bash 명령 안에서 서브명령 스코프를 끊는 셸 구분자(shlex punctuation_chars 토큰).
_SEPARATORS = (";", "&&", "||", "|", "&", "(", ")", "\n")


def _tool_key(token):
    """토큰이 D-6의 감시 대상 실행 파일이면 그 키를, 아니면 None을 돌려준다."""
    if not token:
        return None
    if token.rsplit("/", 1)[-1] == "git":
        return "git"
    for key in ("state-tool", "worktree-tool"):
        if key in token:
            return key
    return None


def classify_bash(command):
    """Bash 명령을 D-6 폐쇄 목록으로 판정한다. (tool_key, subcommand) 또는 None.

    셸 구분자로 끊은 각 세그먼트에서 감시 대상 실행 파일을 찾고, 그 뒤 비-플래그 토큰이
    폐쇄 목록에 있으면 차단 대상이다. 목록 밖 명령은 판정하지 않는다 — Bash의 mutation
    여부는 정적으로 결정 불가하므로 전면 차단하지 않는다(D-6 기각 대안 (a)).
    """
    if not isinstance(command, str) or not command.strip():
        return None
    try:
        # punctuation_chars=True는 shlex.split이 아니라 렉서 생성자만 받는다 —
        # `;`·`&&`·`|`를 별도 토큰으로 떼어내 세그먼트 경계를 얻는다.
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:  # 닫히지 않은 따옴표 등 — 판정하지 않는다(fail-open, 진단만).
        return None

    segment = []
    for token in tokens + [";"]:
        if token in _SEPARATORS:
            hit = _classify_segment(segment)
            if hit:
                return hit
            segment = []
            continue
        segment.append(token)
    return None


def _classify_segment(segment):
    """구분자로 끊긴 단일 세그먼트를 판정한다. (tool_key, subcommand) 또는 None."""
    for index, token in enumerate(segment):
        key = _tool_key(token)
        if key is None:
            continue
        blocked = BLOCKED_SUBCOMMANDS[key]
        for candidate in segment[index + 1:]:
            if candidate.startswith("-"):
                continue
            if candidate in blocked:
                return key, candidate
        return None
    return None


def handle(payload, project_root=None, session_id=None, env=None, now=None):
    """PreToolUse 봉투를 처리해 구조화 결과를 돌려준다. 예외를 던지지 않는다.

    반환 키: exit_code(항상 0) · decision("block" | None) · reason · diagnostics ·
    classification · task_path · session_id.

    첫 분기는 루트 해석이다 — resolve_roots가 cwd를 해석하지 못하면 registry glob도
    lease 조회도 하지 않고 즉시 돌아온다(W-19 latency 방어).
    """
    payload = payload if isinstance(payload, dict) else {}
    result = {
        "exit_code": 0,
        "decision": None,
        "reason": None,
        "diagnostics": [],
        "classification": None,
        "task_path": None,
        "session_id": None,
    }

    cwd = payload.get("cwd") or project_root
    if not cwd:
        return result

    # ── 첫 분기: 등록 worktree/허브가 아니면 여기서 끝난다(파일 I/O 없음) ──────────
    roots = ownership_core.resolve_roots(cwd)
    if not roots.get("ok"):
        result["diagnostics"].append(roots.get("diagnostic"))
        return result

    env = os.environ if env is None else env
    if not session_id:
        session_id = ownership_core.resolve_session_id(env, payload)
    result["session_id"] = session_id
    if not session_id:
        return result

    # canonical task 해석은 session_start_hook이 소유한 exact 발급값 대조를 재사용한다
    # (PRINCIPLES §2 — 같은 패턴을 복제하지 않는다). 이 태스크에서 그 모듈은 동결이라
    # 공개 이름으로 승격하지 않고 그대로 호출한다.
    task_path, _roots_diagnostic = session_start_hook._canonical_task_path(cwd)
    if not task_path:
        return result
    result["task_path"] = task_path

    classification = lease.classify(task_path, session_id, now=now)
    result["classification"] = classification
    if classification != _FOREIGN:
        return result

    tool_name = payload.get("tool_name")
    if tool_name in BLOCKED_TOOLS:
        result["decision"] = "block"
        result["diagnostics"].append(_DIAGNOSTIC_FOREIGN)
        result["reason"] = (
            "foreign_owner: {} is owned by another session's lease ({}). "
            "{} is blocked in this worktree.".format(task_path, classification, tool_name)
        )
        return result

    if tool_name != "Bash":
        return result

    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    hit = classify_bash(command)
    if hit is None:
        result["diagnostics"].append(_DIAGNOSTIC_BASH_UNCLASSIFIED)
        return result

    result["decision"] = "block"
    result["diagnostics"].append(_DIAGNOSTIC_FOREIGN)
    result["reason"] = (
        "foreign_owner: {} is owned by another session's lease. "
        "Bash write subcommand `{} {}` is blocked in this worktree.".format(
            task_path, hit[0], hit[1]
        )
    )
    return result


def to_hook_output(result):
    """판정 결과를 PreToolUse hook 출력 dict로 바꾼다. 통과 판정이면 None."""
    if not isinstance(result, dict) or result.get("decision") != "block":
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": result.get("reason") or _DIAGNOSTIC_FOREIGN,
        }
    }


def main():
    """stdin PreToolUse 봉투 → handle → 차단 시에만 1줄 출력."""
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — 봉투 파싱 실패는 무출력 통과(fail-safe)
        return
    if not isinstance(payload, dict):
        return
    project_root = payload.get("cwd")
    if not project_root:
        return
    output = to_hook_output(handle(payload, project_root=project_root))
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 — 전 경로 fail-safe: 어떤 예외에서도 세션을 막지 않는다.
        pass
    sys.exit(0)
