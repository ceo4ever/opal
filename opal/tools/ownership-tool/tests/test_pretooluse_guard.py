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
from datetime import datetime, timedelta, timezone
from pathlib import Path

FIXTURES_ROOT = Path(__file__).parent / "fixtures"
# A: fixtures/runtime/owner-current-session.json의 lease_expires_at은 고정 시각이 아니라
# "{NOW+1H}" 템플릿이다(값 자체는 파싱 불가 — lease._parse_dt가 None으로 접어 안전하게
# 무시됨). 이 fixture로 foreign_session_owned를 재현해야 하는 소비 지점(여기)에서만
# 실행 시점 기준 미래 값으로 명시 계산해 덮어쓴다 — wall-clock에 무관하게 결정적이다.
_KST = timezone(timedelta(hours=9))


def _future_lease_expiry() -> str:
    return (datetime.now(_KST) + timedelta(hours=1)).isoformat()


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
    # B: lease.py의 실제 status 어휘는 active/released 2종뿐이다(hub_owned는
    # worktree_tool의 execution_ownership FSM 토큰이며 다른 도메인). live lease를
    # 표현하려면 lease.claim()이 실제로 쓰는 "active"를 주입해야 한다.
    owner_record["status"] = "active"
    # A: 템플릿 lease_expires_at을 실행 시점 기준 미래로 계산해 덮어쓴다.
    owner_record["lease_expires_at"] = _future_lease_expiry()
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
    # B: lease.py의 실제 status 어휘는 active/released 2종뿐이다(hub_owned는
    # worktree_tool의 execution_ownership FSM 토큰이며 다른 도메인). live lease를
    # 표현하려면 lease.claim()이 실제로 쓰는 "active"를 주입해야 한다.
    owner_record["status"] = "active"
    # A: 템플릿 lease_expires_at을 실행 시점 기준 미래로 계산해 덮어쓴다.
    owner_record["lease_expires_at"] = _future_lease_expiry()
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


# ─────────────────────────────────────────────────────────────────────────────
# TASK 150 — S-2(AC-2, C-2, H-1) 가드 절반: 이관은 가드 판정을 차단으로 만들지 않는다
#
# @header 보강: layer=test / domain=opal-pipeline. D-8은 차단 로직을 **건드리지 않고**
# 이관만으로 AC-2가 성립해야 한다고 정한다 — `handoff_pending` 레코드는 owner_session_id가
# 비어 `classify`가 `unowned`을 돌려주고, 대상 루트에서 claim한 뒤에는
# `current_session_owned`가 된다. 두 국면 모두 `foreign_session_owned`가 아니므로
# 차단 분기에 닿지 않는다. 판정은 공개 진입점 `pretooluse_guard_hook.handle`로만 관측한다.
# 시간 의존은 고정 now 인자로 주입한다.
# ─────────────────────────────────────────────────────────────────────────────

import os

S2_NOW = "2026-09-22T10:00:00+09:00"
S2_HUB_SESSION = "sess-hub-150"
S2_WT_SESSION = "sess-worktree-150"

# D-6 폐쇄 목록에서 실제 차단 대상이 되는 쓰기 봉투들 — 여기서 하나라도 block이 나오면
# 이관된 태스크의 워크트리 세션이 첫 쓰기부터 막힌다(AC-2 위반).
_S2_WRITE_ENVELOPES = (
    ("Edit", {"file_path": "TASK.md", "old_string": "a", "new_string": "b"}),
    ("Write", {"file_path": "TASK.md", "content": "x"}),
    ("NotebookEdit", {"notebook_path": "nb.ipynb", "new_source": "x"}),
    ("Bash", {"command": "git commit -m handoff"}),
    ("Bash", {"command": "state-tool advance --task 308"}),
)


def _build_handoff_worktree(tmp_path, task_number="308", task_folder="308-handoff-guard"):
    """이관 대상 워크트리를 실물 동형으로 조립한다.

    워크트리 세션의 루트 해석은 `ownership_core.resolve_roots` ② 분기 —
    `<worktree_root>/.opal/task-ownership.json` 발급값 사본 — 를 탄다. 워크트리 안쪽에는
    `.opal-worktrees`를 만들지 않는다(실물 허브 대조 형상).
    """
    hub_root = tmp_path / "hub"
    wt_parent = hub_root / ".opal-worktrees"
    meta_dir = wt_parent / ".meta"
    worktree_root = wt_parent / ("task_" + task_number)
    task_dir = worktree_root / "tasks" / task_folder
    meta_dir.mkdir(parents=True, exist_ok=True)
    task_dir.mkdir(parents=True, exist_ok=True)

    entry = {
        "task": task_number,
        "worktree_root": str(worktree_root),
        "allocator_root": str(hub_root),
        "task_home": str(worktree_root),
        "task_folder": task_folder,
        "task_path": str(task_dir),
        "artifact_repo": ".",
        "task_ownership_version": 2,
    }
    (meta_dir / ("task_" + task_number + ".json")).write_text(
        json.dumps(entry, ensure_ascii=False), encoding="utf-8"
    )
    copy_path = worktree_root / ".opal" / "task-ownership.json"
    copy_path.parent.mkdir(parents=True, exist_ok=True)
    copy_path.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")

    assert not (worktree_root / ".opal-worktrees").exists()
    return hub_root, entry, worktree_root, task_dir


def _guard(pretooluse_guard_hook, worktree_root, session_id, tool_name, tool_input):
    payload = {
        "cwd": str(worktree_root),
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input,
    }
    return pretooluse_guard_hook.handle(
        payload, project_root=worktree_root, session_id=session_id, env={}, now=S2_NOW
    )


def test_s2_handoff_pending_and_claimed_worktree_session_are_not_blocked(tmp_path, monkeypatch):
    """S-2(AC-2, C-2, H-1): 이관 대기 중에도, 대상 루트에서 claim한 뒤에도 워크트리 세션의
    쓰기 도구·쓰기 Bash 봉투가 가드에 차단되지 않는다."""
    from ownership_tool import lease, pretooluse_guard_hook  # RED: lease.handoff 미구현

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    hub_root, entry, worktree_root, task_dir = _build_handoff_worktree(tmp_path)

    assert lease.claim(
        task_dir, session_id=S2_HUB_SESSION, claim_source="state_transition", now=S2_NOW
    )["ok"] is True
    assert lease.handoff(
        task_dir,
        session_id=S2_HUB_SESSION,
        to_worktree_root=entry["worktree_root"],
        now=S2_NOW,
    )["ok"] is True

    # ① 이관 대기 국면 — 소유자 필드가 비어 classify가 unowned이므로 차단 분기에 닿지 않는다.
    for tool_name, tool_input in _S2_WRITE_ENVELOPES:
        result = _guard(pretooluse_guard_hook, worktree_root, S2_WT_SESSION, tool_name, tool_input)
        assert result.get("task_path") == str(task_dir)
        assert result.get("classification") == "unowned", (tool_name, result)
        assert result.get("decision") != "block", (tool_name, result)

    # ② 대상 루트에서 claim 성공 후 — current_session_owned이므로 역시 차단되지 않는다.
    claimed = lease.claim(
        task_dir,
        session_id=S2_WT_SESSION,
        claim_source="session_start",
        now=S2_NOW,
        claimant_root=str(worktree_root),
    )
    assert claimed["ok"] is True, claimed

    for tool_name, tool_input in _S2_WRITE_ENVELOPES:
        result = _guard(pretooluse_guard_hook, worktree_root, S2_WT_SESSION, tool_name, tool_input)
        assert result.get("classification") == "current_session_owned", (tool_name, result)
        assert result.get("decision") != "block", (tool_name, result)


def test_s2_hub_session_is_blocked_after_the_worktree_session_claims(tmp_path, monkeypatch):
    """S-2 대칭 확인: 이관이 소비된 뒤에는 **허브 세션**이 그 태스크의 쓰기에서 차단된다 —
    이관이 소유권을 실제로 옮겼음을 차단 판정의 반대편에서 관측한다(AC-1)."""
    from ownership_tool import lease, pretooluse_guard_hook

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    hub_root, entry, worktree_root, task_dir = _build_handoff_worktree(
        tmp_path, task_number="309", task_folder="309-handoff-guard-symmetry"
    )
    assert lease.claim(
        task_dir, session_id=S2_HUB_SESSION, claim_source="state_transition", now=S2_NOW
    )["ok"] is True
    assert lease.handoff(
        task_dir,
        session_id=S2_HUB_SESSION,
        to_worktree_root=entry["worktree_root"],
        now=S2_NOW,
    )["ok"] is True
    assert lease.claim(
        task_dir,
        session_id=S2_WT_SESSION,
        claim_source="session_start",
        now=S2_NOW,
        claimant_root=str(worktree_root),
    )["ok"] is True

    result = _guard(
        pretooluse_guard_hook, worktree_root, S2_HUB_SESSION, "Edit",
        {"file_path": "TASK.md", "old_string": "a", "new_string": "b"},
    )
    assert result.get("classification") == "foreign_session_owned", result
    assert result.get("decision") == "block", result
    assert "foreign_owner" in result.get("diagnostics", [])
