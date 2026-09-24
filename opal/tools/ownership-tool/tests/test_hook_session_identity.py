"""
@header {
  "module": "ownership_tool.tests.test_hook_session_identity",
  "layer": "test",
  "domain": "ownership",
  "description": "TASK 153 훅 세션 식별 분리 RED-first 시나리오(S-1~S-7 대응, W-1). 훅 소비자 5종(session_start_hook·session_end_hook·heartbeat_hook·pretooluse_guard_hook·stop_evaluator)이 env(OPAL_SESSION_ID/CLAUDE_CODE_SESSION_ID)로 부모 신원을 상속한 자식 이벤트를 부모 신원으로 오판하는 결함(PLAN D-1~D-6)을 공개 인터페이스(handle()/evaluate() 반환값, subprocess 종료코드·파일 상태, 모듈 소스 AST)로만 고정한다. mock/patch는 쓰지 않는다. 구현 전 실행 시 S-2·S-4·S-5·S-6은 실패해야 한다(RED). SessionEnd subprocess 시나리오(S-2·S-3)는 env로 명시 PATH·HOME·가짜 부모 id 2종·OPAL_PROJECT_ROOT를 주입한다 — resolve_project_root의 조상 탐색이 임시 루트를 채택하도록 .opal/AGENT.md 마커도 픽스처가 함께 둔다(TEST-SCENARIO Setup 고정, PM 재지시로 보정). S-7은 CLI run.sh status/release가 --session-id 없이 env OPAL_SESSION_ID만으로 판정하는 회귀와 lease.claim의 타 세션 live lease 거부를 고정한다.",
  "exports": [],
  "depends": ["ownership_tool.ownership_core", "ownership_tool.lease", "ownership_tool.session_registry", "ownership_tool.session_start_hook", "ownership_tool.session_end_hook", "ownership_tool.heartbeat_hook", "ownership_tool.pretooluse_guard_hook", "ownership_tool.stop_evaluator", "ownership_tool.decisions", "ownership-tool run.sh CLI"]
}
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from ownership_tool import (
    decisions,
    heartbeat_hook,
    lease,
    ownership_core,
    pretooluse_guard_hook,
    session_end_hook,
    session_registry,
    session_start_hook,
    stop_evaluator,
)

TOOL_DIR = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

HOOK_MODULE_NAMES = (
    "session_start_hook",
    "session_end_hook",
    "heartbeat_hook",
    "pretooluse_guard_hook",
    "stop_evaluator",
)


def _uid(prefix: str) -> str:
    return "{}-{}".format(prefix, uuid.uuid4().hex[:8])


def _make_worktree_project(tmp_path: Path, name: str, task_folder: str):
    """resolve_roots가 kind='worktree'로 해석하는 <root>/.opal/task-ownership.json 발급 사본을
    만든다(Setup 문단의 "발급 사본" 계약). task_path는 <root>/tasks/<task_folder>다.

    <root>/.opal/AGENT.md 마커도 함께 둔다 — subprocess로 훅 main()을 돌릴 때
    ownership_core.resolve_project_root의 ② 조상 탐색(파일 마커) 분기가 이 루트를
    채택하도록 하기 위해서다(Setup 문단 "`.opal/AGENT.md` 마커" 계약).
    """
    root = tmp_path / name
    task_dir = root / "tasks" / task_folder
    task_dir.mkdir(parents=True, exist_ok=True)
    opal_dir = root / ".opal"
    opal_dir.mkdir(parents=True, exist_ok=True)
    (opal_dir / "AGENT.md").write_text("# temp project marker (test_hook_session_identity)\n",
                                        encoding="utf-8")
    copy_path = ownership_core.task_ownership_copy_path(root)
    copy_path.write_text(
        json.dumps(
            {
                "allocator_root": str(root),
                "task_home": str(root),
                "task_folder": task_folder,
                "task_path": str(task_dir),
                "artifact_repo": ".",
                "task_ownership_version": 2,
            }
        ),
        encoding="utf-8",
    )
    return root, task_dir


def _subprocess_env(project_root: Path, parent_id: str) -> dict:
    """훅 subprocess에 넘기는 명시 env — os.environ을 통째로 상속하지 않는다.

    PATH·HOME + 가짜 부모 id 2종(OPAL_SESSION_ID·CLAUDE_CODE_SESSION_ID) +
    OPAL_PROJECT_ROOT=<임시 루트>(TEST-SCENARIO Setup 고정)만 넣는다.
    """
    import os as _os

    env = {}
    for key in ("PATH", "HOME"):
        if key in _os.environ:
            env[key] = _os.environ[key]
    env["OPAL_SESSION_ID"] = parent_id
    env["CLAUDE_CODE_SESSION_ID"] = parent_id
    env["OPAL_PROJECT_ROOT"] = str(project_root)
    return env


def _runtime_snapshot(root: Path):
    """<root>/.opal/run/.runtime 이하 전 파일의 (상대경로, 바이트) 스냅샷."""
    runtime_dir = root / ".opal" / "run" / ".runtime"
    if not runtime_dir.is_dir():
        return {}
    return {
        str(p.relative_to(runtime_dir)): p.read_bytes()
        for p in sorted(runtime_dir.rglob("*"))
        if p.is_file()
    }


def _owner_snapshot(task_dir: Path):
    owner_path = task_dir / "run" / ".runtime" / "owner.json"
    if not owner_path.is_file():
        return None
    return owner_path.read_bytes()


# ─────────────────────────────────────────────────────────────────────────────
# D-1 — ownership_core.hook_session_id(payload) 단위 표
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"session_id": "sess-abc"}, "sess-abc"),
        ({"session_id": "  sess-padded  "}, "sess-padded"),
        ({}, None),
        ({"session_id": None}, None),
        ({"session_id": "   "}, None),
        ({"session_id": 123}, None),
        ({"session_id": ""}, None),
        (None, None),
        ("not-a-dict", None),
        ([], None),
    ],
)
def test_hook_session_id_table(payload, expected):
    """D-1 계약 — payload dict의 공백 아닌 str session_id만 strip 반환, 그 외 None."""
    assert ownership_core.hook_session_id(payload) == expected


def test_hook_session_id_has_no_env_parameter():
    """D-1 — hook_session_id는 env를 인자로 받지 않는다(시그니처가 payload 하나뿐)."""
    import inspect

    sig = inspect.signature(ownership_core.hook_session_id)
    assert list(sig.parameters) == ["payload"]


def test_resolve_session_id_env_still_first_priority(monkeypatch):
    """D-2 — 공용 resolve_session_id는 무변경, env OPAL_SESSION_ID가 여전히 1순위."""
    env = {"OPAL_SESSION_ID": "env-parent"}
    assert ownership_core.resolve_session_id(env, {"session_id": "payload-child"}) == "env-parent"


# ─────────────────────────────────────────────────────────────────────────────
# S-6 — 훅 모듈 정적 검사(AST/문자열): env 우선 신원 판별 잔존 0건
# ─────────────────────────────────────────────────────────────────────────────

def _module_source(name: str) -> str:
    return (TOOL_DIR / "ownership_tool" / "{}.py".format(name)).read_text(encoding="utf-8")


def _resolve_session_id_call_sites(tree: ast.AST):
    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name == "resolve_session_id":
                sites.append(node.lineno)
    return sites


def test_hook_modules_do_not_call_resolve_session_id():
    """D-3 — 훅 소비자 5종 어디에도 resolve_session_id 호출이 없다(RED — 현재는 6곳 남음)."""
    offenders = {}
    for name in HOOK_MODULE_NAMES:
        source = _module_source(name)
        tree = ast.parse(source, filename=name)
        sites = _resolve_session_id_call_sites(tree)
        if sites:
            offenders[name] = sites
    assert offenders == {}, "resolve_session_id 호출이 남은 훅 모듈: {}".format(offenders)


def test_hook_modules_do_not_reference_env_var_literals():
    """D-3 — 훅 모듈 소스에 OPAL_SESSION_ID·CLAUDE_CODE_SESSION_ID 문자열 리터럴이 없다.

    session_start_hook의 env 파일 **기록** 키 SESSION_ID_ENV_LINE_KEY 정의 줄은 출력
    계약이므로 예외로 둔다(PLAN D-3 괄호 조건).
    """
    offenders = {}
    for name in HOOK_MODULE_NAMES:
        source = _module_source(name)
        hits = []
        for lineno, line in enumerate(source.splitlines(), start=1):
            if name == "session_start_hook" and "SESSION_ID_ENV_LINE_KEY = " in line:
                continue
            if "OPAL_SESSION_ID" in line or "CLAUDE_CODE_SESSION_ID" in line:
                hits.append(lineno)
        if hits:
            offenders[name] = hits
    assert offenders == {}, "env 변수 리터럴이 남은 훅 모듈: {}".format(offenders)


def test_decisions_diagnostics_will_include_no_session_id():
    """D-5 — decisions.DIAGNOSTICS(11→12종)에 no_session_id가 추가되어야 한다(RED — W-2 전 부재)."""
    assert "no_session_id" in decisions.DIAGNOSTICS


# ─────────────────────────────────────────────────────────────────────────────
# S-2 — SessionEnd subprocess: 자식이 소유한 태스크 B만 release, 태스크 A/부모는 불변
# ─────────────────────────────────────────────────────────────────────────────

def test_session_end_subprocess_releases_only_child_owned_task():
    """S-2 — env=부모 id, 봉투 session_id=자식. 자식 소유 태스크 B만 release/close되고
    부모 소유 태스크 A의 owner.json·부모 registry 파일은 바이트 단위로 불변이어야 한다."""
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="hook-session-identity-"))
    parent_id = _uid("parent")
    child_id = _uid("child")

    root_a, task_a = _make_worktree_project(tmp, "proj-a", "A-task")
    root_b, task_b = _make_worktree_project(tmp, "proj-b", "B-task")

    claimed_a = lease.claim(task_a, session_id=parent_id, claim_source="state_transition",
                            project_root=root_a)
    assert claimed_a["ok"]
    registered_a = session_registry.register(root_a, parent_id, str(root_a))
    assert registered_a["ok"]

    claimed_b = lease.claim(task_b, session_id=child_id, claim_source="state_transition",
                            project_root=root_b)
    assert claimed_b["ok"]
    registered_b = session_registry.register(root_b, child_id, str(root_b))
    assert registered_b["ok"]

    owner_a_before = _owner_snapshot(task_a)
    registry_a_before = _runtime_snapshot(root_a)

    payload = {
        "session_id": child_id,
        "cwd": str(root_b),
        "hook_event_name": "SessionEnd",
        "reason": "exit",
    }
    env = _subprocess_env(root_b, parent_id)
    completed = subprocess.run(
        [PYTHON, str(TOOL_DIR / "ownership_tool" / "session_end_hook.py")],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=str(root_b), env=env, timeout=30,
    )
    assert completed.returncode == 0

    # 태스크 B(자식 소유)는 released, 자식 registry closed여야 한다.
    owner_b = json.loads((task_b / "run" / ".runtime" / "owner.json").read_text(encoding="utf-8"))
    assert owner_b.get("status") == "released"
    registry_b_path = ownership_core.session_registry_path(root_b, child_id)
    registry_b = json.loads(registry_b_path.read_text(encoding="utf-8"))
    assert registry_b.get("status") == "closed"

    # 태스크 A(부모 소유)와 부모 registry는 실행 전과 바이트 동일해야 한다.
    assert _owner_snapshot(task_a) == owner_a_before
    assert _runtime_snapshot(root_a) == registry_a_before


# ─────────────────────────────────────────────────────────────────────────────
# S-3 — SessionEnd subprocess: 부모 자신의 종료 → 부모 소유 태스크 A released·registry closed
# ─────────────────────────────────────────────────────────────────────────────

def test_session_end_subprocess_releases_own_owned_task():
    """S-3 — env=부모 id, 봉투 session_id=부모 자신. 태스크 A released, 부모 registry closed."""
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="hook-session-identity-s3-"))
    parent_id = _uid("parent")

    root_a, task_a = _make_worktree_project(tmp, "proj-a", "A-task")
    claimed_a = lease.claim(task_a, session_id=parent_id, claim_source="state_transition",
                            project_root=root_a)
    assert claimed_a["ok"]
    registered_a = session_registry.register(root_a, parent_id, str(root_a))
    assert registered_a["ok"]

    payload = {
        "session_id": parent_id,
        "cwd": str(root_a),
        "hook_event_name": "SessionEnd",
        "reason": "exit",
    }
    env = _subprocess_env(root_a, parent_id)
    completed = subprocess.run(
        [PYTHON, str(TOOL_DIR / "ownership_tool" / "session_end_hook.py")],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=str(root_a), env=env, timeout=30,
    )
    assert completed.returncode == 0

    owner_a = json.loads((task_a / "run" / ".runtime" / "owner.json").read_text(encoding="utf-8"))
    assert owner_a.get("status") == "released"
    registry_a_path = ownership_core.session_registry_path(root_a, parent_id)
    registry_a = json.loads(registry_a_path.read_text(encoding="utf-8"))
    assert registry_a.get("status") == "closed"


# ─────────────────────────────────────────────────────────────────────────────
# S-7 — CLI 회귀: env 신원 유지(status/release는 --session-id 없이 env로 판정),
# 타 세션 live lease claim 거부
# ─────────────────────────────────────────────────────────────────────────────

RUN_SH = TOOL_DIR / "run.sh"


def _cli_env(session_id):
    import os as _os

    env = {}
    for key in ("PATH", "HOME"):
        if key in _os.environ:
            env[key] = _os.environ[key]
    if session_id is not None:
        env["OPAL_SESSION_ID"] = session_id
    return env


def test_cli_status_and_release_use_env_identity_without_session_id_flag(tmp_path):
    """S-7 — CLI status/release는 --session-id 없이 env OPAL_SESSION_ID로 판정한다.
    소유자는 release 성공, 비소유자는 not_owner + 비0 종료코드이고 레코드를 바꾸지 않는다."""
    owner_id = _uid("owner")
    other_id = _uid("other")
    root, task_dir = _make_worktree_project(tmp_path, "proj", "T-task")
    claimed = lease.claim(task_dir, session_id=owner_id, claim_source="state_transition",
                          project_root=root)
    assert claimed["ok"]

    # 소유자 status: env만으로 소유자 판정.
    status_owner = subprocess.run(
        [str(RUN_SH), "status", "--task-path", str(task_dir)],
        capture_output=True, text=True, env=_cli_env(owner_id), timeout=30,
    )
    assert status_owner.returncode == 0
    status_payload = json.loads(status_owner.stdout.strip().splitlines()[-1])
    assert status_payload.get("classification") == "current_session_owned"

    # 비소유자 release: not_owner + 비0 종료, 레코드 불변.
    owner_before = _owner_snapshot(task_dir)
    release_other = subprocess.run(
        [str(RUN_SH), "release", "--task-path", str(task_dir)],
        capture_output=True, text=True, env=_cli_env(other_id), timeout=30,
    )
    assert release_other.returncode != 0
    release_payload = json.loads(release_other.stdout.strip().splitlines()[-1])
    assert release_payload.get("diagnostic") == "not_owner" or release_payload.get("error") == "not_owner"
    assert _owner_snapshot(task_dir) == owner_before

    # 소유자 release: env만으로 성공.
    release_owner = subprocess.run(
        [str(RUN_SH), "release", "--task-path", str(task_dir)],
        capture_output=True, text=True, env=_cli_env(owner_id), timeout=30,
    )
    assert release_owner.returncode == 0
    owner_after = json.loads((task_dir / "run" / ".runtime" / "owner.json").read_text(encoding="utf-8"))
    assert owner_after.get("status") == "released"


def test_lease_claim_rejects_foreign_live_lease_and_leaves_record_unchanged(tmp_path):
    """S-7 — 타 세션이 소유한 live lease에 lease.claim 시도 시 거부되고 레코드가 불변이다."""
    owner_id = _uid("owner")
    intruder_id = _uid("intruder")
    root, task_dir = _make_worktree_project(tmp_path, "proj", "T-task")
    claimed = lease.claim(task_dir, session_id=owner_id, claim_source="state_transition",
                          project_root=root)
    assert claimed["ok"]
    before = _owner_snapshot(task_dir)

    result = lease.claim(task_dir, session_id=intruder_id, claim_source="state_transition",
                         project_root=root)
    assert result["ok"] is False
    assert result.get("diagnostic") == "foreign_owner"
    assert _owner_snapshot(task_dir) == before


# ─────────────────────────────────────────────────────────────────────────────
# S-4 — 신원 없는 이벤트(누락·공백·비문자·null) → no_session_id 진단 + 무변경
# ─────────────────────────────────────────────────────────────────────────────

_MALFORMED_SESSION_IDS = pytest.mark.parametrize(
    "malformed_payload",
    [
        {},  # 누락
        {"session_id": "  "},  # 공백
        {"session_id": 123},  # 비문자
        {"session_id": None},  # null
    ],
    ids=["missing", "blank", "non_string", "null"],
)


@_MALFORMED_SESSION_IDS
def test_session_start_no_session_id_is_diagnosed_and_noop(malformed_payload, tmp_path):
    """S-4 SessionStart — no_session_id 진단 + session_id None + 파일 무변경(RED).

    현재는 env의 부모 id로 폴백되어 session_id가 parent_id로 채워지고 세션 registry
    파일까지 새로 생성된다 — D-1 계약(훅은 봉투 session_id만 본다) 위반의 직접 증거다.
    """
    parent_id = _uid("parent")
    root, _task_dir = _make_worktree_project(tmp_path, "proj", "T-task")
    before = _runtime_snapshot(root)

    payload = dict(malformed_payload)
    payload["cwd"] = str(root)
    payload["hook_event_name"] = "SessionStart"
    env = {"OPAL_SESSION_ID": parent_id, "CLAUDE_CODE_SESSION_ID": parent_id}

    result = session_start_hook.handle(payload, project_root=root, env=env)

    assert result["session_id"] is None
    assert "no_session_id" in result["diagnostics"]
    assert _runtime_snapshot(root) == before


@_MALFORMED_SESSION_IDS
def test_session_end_no_session_id_is_diagnosed_and_noop(malformed_payload, tmp_path):
    """S-4 SessionEnd — no_session_id 진단 + session_id None + 파일 무변경(RED)."""
    parent_id = _uid("parent")
    root, task_dir = _make_worktree_project(tmp_path, "proj", "T-task")
    claimed = lease.claim(task_dir, session_id=parent_id, claim_source="state_transition",
                          project_root=root)
    assert claimed["ok"]
    owner_before = _owner_snapshot(task_dir)
    runtime_before = _runtime_snapshot(root)

    payload = dict(malformed_payload)
    payload["cwd"] = str(root)
    payload["hook_event_name"] = "SessionEnd"
    env = {"OPAL_SESSION_ID": parent_id, "CLAUDE_CODE_SESSION_ID": parent_id}

    result = session_end_hook.handle(payload, project_root=root, env=env)

    assert result["session_id"] is None
    assert "no_session_id" in result["diagnostics"]
    assert _owner_snapshot(task_dir) == owner_before
    assert _runtime_snapshot(root) == runtime_before


@_MALFORMED_SESSION_IDS
def test_heartbeat_no_session_id_is_diagnosed_and_noop(malformed_payload, tmp_path):
    """S-4 PostToolUse heartbeat — no_session_id 진단 + session_id None + 파일 무변경(RED)."""
    parent_id = _uid("parent")
    root, task_dir = _make_worktree_project(tmp_path, "proj", "T-task")
    claimed = lease.claim(task_dir, session_id=parent_id, claim_source="state_transition",
                          project_root=root)
    assert claimed["ok"]
    owner_before = _owner_snapshot(task_dir)
    runtime_before = _runtime_snapshot(root)

    payload = dict(malformed_payload)
    payload["cwd"] = str(root)
    payload["hook_event_name"] = "PostToolUse"
    payload["tool_name"] = "Bash"
    env = {"OPAL_SESSION_ID": parent_id, "CLAUDE_CODE_SESSION_ID": parent_id}

    result = heartbeat_hook.handle(payload, project_root=root, env=env)

    assert result["session_id"] is None
    assert "no_session_id" in result["diagnostics"]
    assert _owner_snapshot(task_dir) == owner_before
    assert _runtime_snapshot(root) == runtime_before


@_MALFORMED_SESSION_IDS
def test_pretooluse_no_session_id_is_diagnosed_and_noop(malformed_payload, tmp_path):
    """S-4 PreToolUse — no_session_id 진단 + session_id None + 차단 없음 + 파일 무변경(RED).

    D-4 — PreToolUse는 fail-open을 유지하되(차단 없음) diagnostics에 no_session_id를
    남겨야 한다. 현재는 env의 부모 id로 판정이 진행되어 진단이 비어 있다.
    """
    parent_id = _uid("parent")
    root, task_dir = _make_worktree_project(tmp_path, "proj", "T-task")
    claimed = lease.claim(task_dir, session_id=parent_id, claim_source="state_transition",
                          project_root=root)
    assert claimed["ok"]
    owner_before = _owner_snapshot(task_dir)
    runtime_before = _runtime_snapshot(root)

    payload = dict(malformed_payload)
    payload["cwd"] = str(root)
    payload["hook_event_name"] = "PreToolUse"
    payload["tool_name"] = "Edit"
    payload["tool_input"] = {"file_path": str(task_dir / "x.py")}
    env = {"OPAL_SESSION_ID": parent_id, "CLAUDE_CODE_SESSION_ID": parent_id}

    result = pretooluse_guard_hook.handle(payload, project_root=root, env=env)

    assert result["session_id"] is None
    assert "no_session_id" in result["diagnostics"]
    assert result["decision"] is None
    assert _owner_snapshot(task_dir) == owner_before
    assert _runtime_snapshot(root) == runtime_before


@_MALFORMED_SESSION_IDS
def test_stop_no_session_id_is_diagnosed_and_validates(malformed_payload, tmp_path):
    """S-4 Stop — evidence.session_id None + diagnostics에 no_session_id + decisions.validate()
    통과(RED — 현재 evidence.session_id는 env의 부모 id로 채워진다)."""
    parent_id = _uid("parent")
    root = tmp_path / "proj"
    root.mkdir(parents=True, exist_ok=True)

    payload = dict(malformed_payload)
    payload["cwd"] = str(root)
    payload["hook_event_name"] = "Stop"
    payload["stop_hook_active"] = False
    env = {"OPAL_SESSION_ID": parent_id, "CLAUDE_CODE_SESSION_ID": parent_id}

    result = stop_evaluator.evaluate(payload, project_root=root, env=env)

    assert result["evidence"].get("session_id") is None
    assert "no_session_id" in result["diagnostics"]
    assert decisions.validate(result) is True


# ─────────────────────────────────────────────────────────────────────────────
# S-5 — 자식이 봉투 session_id=child로 부모 소유 태스크를 건드리지 않는지
# ─────────────────────────────────────────────────────────────────────────────

def test_heartbeat_from_child_session_id_does_not_touch_parent(tmp_path):
    """S-5 heartbeat — 봉투 session_id=child(부모 소유 태스크 A에 대해 타 세션) → no-op,
    부모 heartbeat_at·registry 불변(RED — 현재는 env의 부모 id로 갱신된다)."""
    parent_id = _uid("parent")
    child_id = _uid("child")
    root, task_dir = _make_worktree_project(tmp_path, "proj", "T-task")
    claimed = lease.claim(task_dir, session_id=parent_id, claim_source="state_transition",
                          project_root=root)
    assert claimed["ok"]
    registered = session_registry.register(root, parent_id, str(root))
    assert registered["ok"]
    owner_before = _owner_snapshot(task_dir)
    runtime_before = _runtime_snapshot(root)

    payload = {
        "session_id": child_id,
        "cwd": str(root),
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
    }
    env = {"OPAL_SESSION_ID": parent_id, "CLAUDE_CODE_SESSION_ID": parent_id}

    result = heartbeat_hook.handle(payload, project_root=root, env=env)

    assert result["noop"] is True
    assert result["session_id"] == child_id
    assert _owner_snapshot(task_dir) == owner_before
    assert _runtime_snapshot(root) == runtime_before


def test_pretooluse_from_child_session_id_blocks_as_foreign(tmp_path):
    """S-5 PreToolUse — 봉투 session_id=child(부모 소유 태스크 A) →
    classification=foreign_session_owned, decision=block(RED — 현재 classify는 부모
    자신의 env id로 이뤄져 current_session_owned로 오판된다)."""
    parent_id = _uid("parent")
    child_id = _uid("child")
    root, task_dir = _make_worktree_project(tmp_path, "proj", "T-task")
    claimed = lease.claim(task_dir, session_id=parent_id, claim_source="state_transition",
                          project_root=root)
    assert claimed["ok"]

    payload = {
        "session_id": child_id,
        "cwd": str(root),
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(task_dir / "x.py")},
    }
    env = {"OPAL_SESSION_ID": parent_id, "CLAUDE_CODE_SESSION_ID": parent_id}

    result = pretooluse_guard_hook.handle(payload, project_root=root, env=env)

    assert result["classification"] == "foreign_session_owned"
    assert result["decision"] == "block"


def test_stop_evidence_session_id_is_envelope_child_not_env_parent(tmp_path):
    """S-5 Stop — 봉투 session_id=child가 evidence.session_id에 실려야 한다. 부모 id 명의
    receipt는 생성되지 않는다(RED — 현재 evidence.session_id는 env의 부모 id다)."""
    parent_id = _uid("parent")
    child_id = _uid("child")
    root = tmp_path / "proj"
    root.mkdir(parents=True, exist_ok=True)

    payload = {
        "session_id": child_id,
        "cwd": str(root),
        "hook_event_name": "Stop",
        "stop_hook_active": False,
    }
    env = {"OPAL_SESSION_ID": parent_id, "CLAUDE_CODE_SESSION_ID": parent_id}

    result = stop_evaluator.evaluate(payload, project_root=root, env=env)

    assert result["evidence"].get("session_id") == child_id
    parent_receipt_dir = root / ".opal" / "run" / ".runtime" / "stop-guard"
    if parent_receipt_dir.is_dir():
        assert not any(parent_id in p.name for p in parent_receipt_dir.iterdir())


# ─────────────────────────────────────────────────────────────────────────────
# 회귀 가드 — 일반 CLI 경로(resolve_session_id)의 env 우선순위는 계속 성립해야 한다
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_status_still_uses_env_identity(monkeypatch, tmp_path):
    """S-7 회귀 가드 — cli.py는 hook_session_id가 아니라 resolve_session_id(env 우선)를
    계속 쓴다(D-2 무변경 확인). ownership_core 자체의 우선순위만 재확인한다."""
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    env = {"OPAL_SESSION_ID": "owner-session"}
    assert ownership_core.resolve_session_id(env, {}) == "owner-session"
