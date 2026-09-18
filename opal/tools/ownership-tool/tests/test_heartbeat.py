# @header
# module: ownership_tool.tests.test_heartbeat
# layer: test
# domain: ownership
# description: RED-first — ownership_tool.heartbeat_hook / session_end_hook 공개 계약 검증 (S-12 hooks)
# exports: (none — pytest module)
# depends: ownership_tool.heartbeat_hook, ownership_tool.session_end_hook (미구현), fixtures/hook-payloads
"""RED 테스트 — 구현 전."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from ownership_tool import session_registry

FIXTURES_ROOT = Path(__file__).parent / "fixtures"


def _clone_fixtures() -> tuple[Path, Path, Path]:
    tmp = Path(tempfile.mkdtemp(prefix="ownership-fixtures-"))
    shutil.copytree(FIXTURES_ROOT, tmp, dirs_exist_ok=True)
    hub_tmp = tmp / "hub_root"
    # 실물 동형화(W-2'): 워크트리 루트는 허브의 형제가 아니라
    # <hub_root>/.opal-worktrees/task_NNN이고 registry meta는
    # <hub_root>/.opal-worktrees/.meta/에 위치한다(worktree.md 발급 계약).
    wt_tmp = hub_tmp / ".opal-worktrees"
    hub_tmp.mkdir(parents=True, exist_ok=True)
    wt_tmp.mkdir(parents=True, exist_ok=True)
    for p in tmp.rglob("*.json"):
        text = p.read_text(encoding="utf-8")
        text = text.replace("{HUB}", str(hub_tmp)).replace("{WT}", str(wt_tmp))
        p.write_text(text, encoding="utf-8")
    return tmp, hub_tmp, wt_tmp


def _seed_owned_task_138(hub_tmp, wt_tmp, owner_session_id):
    """wt_tmp/task_138에 registry meta + <owner_session_id> live lease를 실물 배치하고
    canonical task_dir을 반환한다. session_start_hook 실측대로 registry meta는
    <project_root>/.opal-worktrees/.meta/(project_root=worktree_root)에 둔다.
    """
    worktree_root = wt_tmp / "task_138"
    worktree_root.mkdir(parents=True, exist_ok=True)
    task_folder = "138-260916-opds-스톱-훅-태스크-소유권-결정론화"
    task_dir = worktree_root / "tasks" / task_folder
    registry_entry = {
        "allocator_root": str(hub_tmp),
        "task_home": str(worktree_root),
        "task_folder": task_folder,
        "task_path": str(task_dir),
        "artifact_repo": ".",
        "task_ownership_version": 2,
    }
    meta_dir = worktree_root / ".opal-worktrees" / ".meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "task_138.json").write_text(json.dumps(registry_entry), encoding="utf-8")

    owner_record = json.loads(
        (FIXTURES_ROOT / "runtime" / "owner-current-session.json").read_text(encoding="utf-8")
    )
    owner_record["task_path"] = str(task_dir)
    owner_record["owner_session_id"] = owner_session_id
    owner_record["status"] = "hub_owned"
    owner_path = task_dir / "run" / ".runtime" / "owner.json"
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(json.dumps(owner_record), encoding="utf-8")
    return worktree_root, task_dir


def test_posttooluse_from_owning_session_refreshes_heartbeat(monkeypatch):
    """PostToolUse(A, 소유 세션) → heartbeat_hook이 모든 PostToolUse에서 호출되어 갱신."""
    from ownership_tool import heartbeat_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/posttooluse.json").read_text(encoding="utf-8"))
    payload["cwd"] = str(wt_tmp / "task_138")
    payload["session_id"] = "sess-a"

    # setup(B-1): "소유 세션"이 성립하려면 canonical task에 이 세션("sess-a")이 소유한
    # live lease가 실제로 있어야 한다.
    worktree_root, _task_dir = _seed_owned_task_138(hub_tmp, wt_tmp, owner_session_id="sess-a")

    result = heartbeat_hook.handle(payload, project_root=worktree_root)
    assert result.get("exit_code", 0) == 0


def test_posttooluse_from_foreign_session_is_noop(monkeypatch):
    """타 세션 PostToolUse → no-op."""
    from ownership_tool import heartbeat_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/posttooluse.json").read_text(encoding="utf-8"))
    payload["cwd"] = str(wt_tmp / "task_138")
    payload["session_id"] = "sess-foreign"

    # setup(B-1): "타 세션"이 성립하려면 canonical task의 live lease 소유자가 payload의
    # session_id("sess-foreign")와 달라야 한다(소유자는 "sess-a").
    worktree_root, _task_dir = _seed_owned_task_138(hub_tmp, wt_tmp, owner_session_id="sess-a")

    result = heartbeat_hook.handle(payload, project_root=worktree_root)
    assert result.get("noop") is True or result.get("exit_code", 0) == 0


def test_session_end_releases_and_closes_registry(monkeypatch):
    """SessionEnd → registry closed, lease released."""
    from ownership_tool import session_end_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/sessionend.json").read_text(encoding="utf-8"))
    payload["cwd"] = str(wt_tmp / "task_138")
    payload["session_id"] = "sess-a"

    # setup(B-1): release가 성립하려면 종료하는 세션("sess-a")이 소유한 live lease와,
    # session_start_hook.register가 만드는 세션 registry 엔트리가 실제로 있어야 한다.
    worktree_root, _task_dir = _seed_owned_task_138(hub_tmp, wt_tmp, owner_session_id="sess-a")
    session_registry.register(worktree_root, "sess-a", payload["cwd"])

    result = session_end_hook.handle(payload, project_root=worktree_root)
    assert result.get("released") is True
