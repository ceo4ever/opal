# @header
# module: ownership_tool.tests.test_pretooluse_guard
# layer: test
# domain: ownership
# description: RED-first — ownership_tool.pretooluse_guard_hook 공개 계약 검증 (S-13)
# exports: (none — pytest module)
# depends: ownership_tool.pretooluse_guard_hook (미구현), fixtures/hook-payloads
"""RED 테스트 — 구현 전."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

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


def test_outside_registered_worktree_exits_immediately_no_io(tmp_path, monkeypatch):
    """등록 worktree 밖 cwd → guard가 파일 I/O 없이 즉시 exit 0."""
    from ownership_tool import pretooluse_guard_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 케이스와 동일 사유) — env -u 유무와 무관하게
    # 동일 결과가 나와야 한다.
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/pretooluse.json").read_text(encoding="utf-8"))
    outside_dir = tmp_path / "not-a-registered-worktree"
    outside_dir.mkdir()
    payload["cwd"] = str(outside_dir)

    before = list(outside_dir.rglob("*"))
    result = pretooluse_guard_hook.handle(payload, project_root=outside_dir)
    after = list(outside_dir.rglob("*"))
    assert result.get("exit_code", 0) == 0
    assert before == after


def test_foreign_owner_blocks_edit_and_git_commit(monkeypatch):
    """foreign_owner에서 Edit/Write/NotebookEdit·git commit 차단."""
    from ownership_tool import pretooluse_guard_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root = wt_tmp / "task_220"
    worktree_root.mkdir(parents=True, exist_ok=True)

    # setup(B-1): pretooluse_guard_hook.handle이 foreign_owner를 판정하려면 cwd가 registry
    # 발급 canonical task로 해석되고, 그 task에 "sess-foreign"이 아닌 세션의 live lease가
    # 있어야 한다. session_start_hook의 실측(project_root=cwd이므로 registry meta는
    # <project_root>/.opal-worktrees/.meta/에 있다)과 동형으로 배치한다.
    task_folder = "220-foreign-owner-guard"
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
    (meta_dir / "task_220.json").write_text(json.dumps(registry_entry), encoding="utf-8")

    # setup: canonical task_path에 다른 세션("sess-owner")이 소유한 live lease를 실물
    # 배치한다(fixtures/runtime/owner-current-session.json 스키마 재사용).
    owner_record = json.loads(
        (FIXTURES_ROOT / "runtime" / "owner-current-session.json").read_text(encoding="utf-8")
    )
    owner_record["task_path"] = str(task_dir)
    owner_record["owner_session_id"] = "sess-owner"
    owner_record["status"] = "hub_owned"
    owner_path = task_dir / "run" / ".runtime" / "owner.json"
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(json.dumps(owner_record), encoding="utf-8")

    edit_payload = json.loads((tmp / "hook-payloads/pretooluse.json").read_text(encoding="utf-8"))
    edit_payload["cwd"] = str(worktree_root)
    edit_payload["tool_name"] = "Edit"
    result = pretooluse_guard_hook.handle(edit_payload, project_root=worktree_root, session_id="sess-foreign")
    assert result.get("decision") == "block"

    commit_payload = dict(edit_payload)
    commit_payload["tool_name"] = "Bash"
    commit_payload["tool_input"] = {"command": "git commit -m x"}
    result_commit = pretooluse_guard_hook.handle(commit_payload, project_root=worktree_root, session_id="sess-foreign")
    assert result_commit.get("decision") == "block"


def test_foreign_owner_allows_read_and_ls_with_diagnostic(monkeypatch):
    """Read 허용, ls는 허용 + foreign_owner_bash_unclassified 진단."""
    from ownership_tool import pretooluse_guard_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root = wt_tmp / "task_220"
    worktree_root.mkdir(parents=True, exist_ok=True)

    # setup(B-1): test_foreign_owner_blocks_edit_and_git_commit과 동일한 사유로 foreign
    # owner 시나리오(registry meta + 타 세션 live lease)를 이 테스트 안에서도 독립 조립한다.
    task_folder = "220-foreign-owner-guard"
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
    (meta_dir / "task_220.json").write_text(json.dumps(registry_entry), encoding="utf-8")

    owner_record = json.loads(
        (FIXTURES_ROOT / "runtime" / "owner-current-session.json").read_text(encoding="utf-8")
    )
    owner_record["task_path"] = str(task_dir)
    owner_record["owner_session_id"] = "sess-owner"
    owner_record["status"] = "hub_owned"
    owner_path = task_dir / "run" / ".runtime" / "owner.json"
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(json.dumps(owner_record), encoding="utf-8")

    read_payload = json.loads((tmp / "hook-payloads/pretooluse.json").read_text(encoding="utf-8"))
    read_payload["cwd"] = str(worktree_root)
    read_payload["tool_name"] = "Read"
    result_read = pretooluse_guard_hook.handle(read_payload, project_root=worktree_root, session_id="sess-foreign")
    assert result_read.get("decision") != "block"

    ls_payload = dict(read_payload)
    ls_payload["tool_name"] = "Bash"
    ls_payload["tool_input"] = {"command": "ls"}
    result_ls = pretooluse_guard_hook.handle(ls_payload, project_root=worktree_root, session_id="sess-foreign")
    assert result_ls.get("decision") != "block"
    assert "foreign_owner_bash_unclassified" in result_ls.get("diagnostics", [])
