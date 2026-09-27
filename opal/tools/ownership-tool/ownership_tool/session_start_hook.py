"""
@header {
  "module": "ownership_tool.session_start_hook",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "SessionStart hook 어댑터(W-7). 봉투의 session_id·cwd를 session_registry에 등록하고, 어댑터가 알려준 env 파일에 `export <SESSION_ID_ENV_LINE_KEY>=<quoted id>` 1줄을 append한다 — 이 파일은 dotenv가 아니라 부모 쉘이 source하는 쉘 프리앰블이라 export 접두가 있어야 자식 프로세스가 값을 상속한다. 루트 판정은 ownership_core.resolve_roots가 소유하고(D-20), 해석된 canonical task에만 lease.claim(claim_source=session_start — D-21 수동 소유권)을 시도하며, claim 주체 루트를 봉투의 cwd로 명시 전달한다(claimant_root) — 허브가 터미널 기동 직전에 남긴 이관 대기 lease는 이관 대상 루트와 realpath 동치이거나 그 하위에서 온 claim만 수용하므로(harness/worktree.md §이관), 이 전달이 워크트리 세션이 이관을 소비하는 유일한 연결점이다. claim 실패는 classification과 함께 `registry_owner_not_registered:<diagnostic>` 진단을 남기고 registry 등록을 시도하지 않는다(D-7) — 소유하지 않은 세션이 registry owner가 되지 않게 한다. lease를 잡은 워크트리 세션은 이어서 허브 registry의 부트 owner 등록을 worktree-tool `ownership-set` CLI 경유로 1회 위임한다(999 D-H) — registry `execution_ownership` 쓰기는 이 CLI만 허용되므로 meta 파일을 직접 편집하지 않는다(C-9). 세션 ID는 ownership_core.hook_session_id로 봉투 session_id만 읽는다 — 부모 세션 env를 상속한 자식 프로세스가 부모 신원으로 등록·claim하지 않도록 세션 환경변수·플랫폼 env로 대체하지 않으며, 봉투 신원이 없으면 no_session_id 진단만 남긴다(task 153). 플랫폼 고유 변수명은 claude_adapter에만 둔다(C-15). 실행 루트는 봉투 cwd를 그대로 쓰지 않고 ownership_core.resolve_project_root(① 명시 오버라이드 OPAL_PROJECT_ROOT → ② 봉투 cwd부터 조상으로 올라가며 .opal/MEMORY.json 또는 .opal/AGENT.md를 파일로 가진 첫 디렉토리 → ③ None)가 해석하며, 미해석이면 파일 I/O 이전에 종료한다(D-30b·D-25). 해석된 루트는 handle() 내부의 루트 파생 호출에도 그대로 전파한다(D-27). 전 경로 fail-safe exit 0.",
  "exports": ["SESSION_ID_ENV_LINE_KEY", "handle", "main"],
  "depends": ["ownership_tool.ownership_core", "ownership_tool.lease", "ownership_tool.session_registry", "ownership_tool.claude_adapter", "worktree-tool ownership-set CLI"]
}
"""
from __future__ import annotations

import json
import os
import pathlib
import shlex
import subprocess
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

# registry `execution_ownership` 전이는 worktree-tool CLI 경유만 허용된다(TASK 999 C-9).
# 배포본 아래 고정 경로이며 허브 위치 해석은 worktree_tool.py:2254-2257의 기존 선례를 쓴다.
_WORKTREE_TOOL_RUN_REL = "tools/worktree-tool/run.sh"
# 부트 등록이 진입할 수 있는 유일한 registry 상태.
_EXEC_STATE_WORKTREE_SESSION_OWNED = "worktree_session_owned"
# CLI가 "attribution 키 부재"를 지칭하는 토큰(worktree_tool.py:142).
_ATTRIBUTION_TOKEN_ACTIVE = "active"
# ownership-set 호출 상한(초). CLI는 registry lock 대기를 자신이 REGISTRY_LOCK_TIMEOUT_MS=30000
# (worktree_tool.py:165)으로 이미 상한하고 초과 시 registry_lock_timeout을 반환하므로, 그보다
# 넉넉한 값을 둬 정상 경합을 잘라내지 않으면서도 hook이 무한 대기하지 않게 한다.
_OWNERSHIP_SET_TIMEOUT_SEC = 45


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


def _registry_entry_for_task(allocator_root, task_path):
    """allocator_root registry에서 canonical task_path와 동치인 행 하나를 돌려준다.

    발급값끼리의 경로 대조만 한다 — 문자열 접두·이름 추론을 쓰지 않는다(C-6).
    """
    target = str(pathlib.Path(str(task_path)))
    for entry in _load_registry(allocator_root):
        value = entry.get("task_path")
        if value and str(pathlib.Path(str(value))) == target:
            return entry
    return None


def _ownership_set_error_code(completed):
    """Return the exact structured error emitted by ownership-set, if present."""
    for output in (completed.stdout, completed.stderr):
        if not isinstance(output, str) or not output.strip():
            continue
        try:
            response = json.loads(output)
        except ValueError:
            continue
        if isinstance(response, dict) and isinstance(response.get("error"), str):
            return response["error"]
    return None


def _register_registry_owner(cwd, task_path, session_id, env):
    """워크트리 세션의 부트 owner 등록을 1회 시도한다. (등록 여부, 진단 목록).

    D-H: registry `execution_ownership`의 쓰기는 `worktree-tool ownership-set` 경유만
    허용되므로(TASK 999 C-9) 이 모듈은 meta 파일을 **읽기만** 하고 전이는 CLI에 맡긴다 —
    파일 쓰기·lock·원자 교체는 여전히 worktree-tool 소유라 dual writer가 생기지 않는다.
    허브 위치는 `ownership_core.resolve_roots`가 준 `allocator_root`만 쓰고 추론하지 않는다.

    분기는 5개다. `state == worktree_session_owned` ∧ `owner_session_id`가 비었을 때만
    호출하고, 이미 자기 세션이면 멱등 게이트로 호출을 생략하며(D-J — generation 낭비 방지),
    타 세션 owner·다른 state·registry 행 부재·CLI 실패는 호출 없이 진단만 남긴다.
    `--generation`은 지정하지 않아 항상 `prior+1` 단조 증가에 맡긴다(D-J).
    """
    roots = ownership_core.resolve_roots(cwd)
    if not roots.get("ok") or roots.get("kind") != "worktree":
        return False, []
    allocator_root = roots.get("allocator_root")

    entry = _registry_entry_for_task(allocator_root, task_path)
    if entry is None:
        return False, ["registry_row_absent"]

    block = entry.get("execution_ownership")
    if not isinstance(block, dict) or block.get("state") != _EXEC_STATE_WORKTREE_SESSION_OWNED:
        return False, ["registry_not_worktree_owned"]

    owner = block.get("owner_session_id")
    if owner:
        if str(owner) == str(session_id):
            return False, []  # 이미 자기 세션 — 멱등 게이트(호출 0회, 진단 없음).
        return False, ["foreign_registry_owner"]

    task = entry.get("task")
    if not task:
        return False, ["registry_row_absent"]

    runner = pathlib.Path(
        (env or {}).get("OPAL_HOME") or os.path.expanduser("~/.opal")
    ) / _WORKTREE_TOOL_RUN_REL
    argv = [
        str(runner), "ownership-set",
        "--project-root", str(allocator_root),
        "--task", str(task),
        "--execution-ownership", _EXEC_STATE_WORKTREE_SESSION_OWNED,
        "--attribution-state", str(entry.get("attribution_state") or _ATTRIBUTION_TOKEN_ACTIVE),
        "--owner-session-id", str(session_id),
    ]
    try:
        completed = subprocess.run(
            argv, capture_output=True, text=True, timeout=_OWNERSHIP_SET_TIMEOUT_SEC)
    except (OSError, subprocess.TimeoutExpired) as exc:
        # 실행 불가도 멈춘 CLI도 세션을 막지 않는다 — 예외로 새지 않고 구조화 반환한다(fail-safe).
        return False, ["ownership_set_failed", "ownership_set_detail:{}".format(exc)]
    if completed.returncode != 0:
        detail = "\n".join(value.strip() for value in (completed.stderr, completed.stdout) if value).strip()
        # The worktree sandbox may prohibit this child from writing the hub
        # registry.  The lease remains authoritative and the hub will make the
        # final registry transition.  Only its exact structured error code is
        # deferrable; wording in an unrelated error must stay a failure.
        if _ownership_set_error_code(completed) == "registry_write_denied":
            return False, ["registry_write_denied", "ownership_set_detail:{}".format(detail)]
        return False, ["ownership_set_failed", "ownership_set_detail:{}".format(detail)]
    return True, []


def _append_session_id(env_file_path, session_id):
    """env 파일에 `export <SESSION_ID_ENV_LINE_KEY>=<quoted id>` 1줄을 append한다. (성공 여부, 진단).

    플랫폼은 이 파일을 dotenv로 파싱하지 않고 Bash 도구의 **부모 쉘에서 실행되는 쉘
    스크립트 프리앰블**로 `source`한다(D-A). 따라서 `KEY=value` 대입만으로는 자식
    프로세스에 전파되지 않아 `export` 접두가 필요하고, 값은 쉘 메타문자에 안전하도록
    `shlex.quote`로 quoting한다(D-B). 이 모듈은 자신의 `os.environ`을 수정하지 않는다.
    """
    if not env_file_path:
        return False, "env_file_not_provided"
    try:
        with open(str(env_file_path), "a", encoding="utf-8") as handle:
            handle.write("export {}={}\n".format(
                SESSION_ID_ENV_LINE_KEY, shlex.quote(str(session_id))))
        return True, None
    except OSError as exc:  # 쓰기 실패는 진단만 남기고 등록은 유지한다.
        return False, "env_file_write_failed:{}".format(exc)


def handle(payload, project_root=None, env_file_path=None, env=None, now=None):
    """SessionStart 봉투를 처리해 구조화 결과를 돌려준다. 예외를 던지지 않는다.

    반환 키: exit_code(항상 0) · session_id · registered · env_file_written ·
    lease_claimed · classification · task_path · registry_owner_registered · diagnostics.
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
        "registry_owner_registered": False,
        "diagnostics": [],
    }

    session_id = ownership_core.hook_session_id(payload)
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

    task_path, roots_diagnostic = _canonical_task_path(root)
    if roots_diagnostic:
        result["diagnostics"].append(roots_diagnostic)
    if task_path is None:
        result["diagnostics"].append("no_owned_task")
        return result

    result["task_path"] = task_path
    claimed = lease.claim(task_path, session_id=session_id,
                          claim_source="session_start", now=now, project_root=root,
                          claimant_root=root)
    if claimed.get("ok"):
        result["lease_claimed"] = True
        result["classification"] = "current_session_owned"
        registered_owner, owner_diagnostics = _register_registry_owner(
            root, task_path, session_id, env)
        result["registry_owner_registered"] = registered_owner
        result["diagnostics"].extend(owner_diagnostics)
        return result

    diagnostic = claimed.get("diagnostic")
    result["classification"] = diagnostic
    result["diagnostics"].append(diagnostic)
    # claim 실패는 registry 등록을 시도하지 않는다 — 소유하지 않은 세션이 registry
    # `owner_session_id`가 되면 두 축이 어긋나므로(harness/worktree.md §저장 위치와 축 분리),
    # 등록 대신 미등록 사유만 남기고 `registry_owner_registered`는 False로 유지한다(D-7).
    result["diagnostics"].append("registry_owner_not_registered:{}".format(diagnostic))
    return result


def main():
    """stdin SessionStart 봉투 → handle. hook 출력은 없다(등록·claim만 수행)."""
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — 봉투 파싱 실패는 무출력 통과(fail-safe)
        return
    if not isinstance(payload, dict):
        return
    project_root = ownership_core.resolve_project_root(payload, os.environ)
    if not project_root:
        return
    handle(payload, project_root=project_root)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 — 전 경로 fail-safe: 어떤 예외에서도 세션을 막지 않는다.
        pass
    sys.exit(0)
