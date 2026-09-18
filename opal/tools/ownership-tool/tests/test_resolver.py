# @header
# module: ownership_tool.tests.test_resolver
# layer: test
# domain: ownership
# description: RED-first — ownership_tool.resolver.resolve_worktree/resolve_hub 공개 계약 검증 (S-3, S-4) + resolve_hub의 worktree_owned_shadow/hub_canonical 분류 술어를 resolver 단위에서 직접 집행(AC-10, AC-11, C-7, D-14)
# exports: (none — pytest module)
# depends: ownership_tool.resolver (미구현), fixtures/worktrees, fixtures/registry, fixtures/hub
"""RED 테스트 — 구현 전. ownership_tool.resolver 미구현이므로 ImportError로 실패해야 한다."""
from __future__ import annotations

import ast
import json
import shutil
import tempfile
from pathlib import Path

import pytest

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


def _load(tmp: Path, rel: str) -> dict:
    return json.loads((tmp / rel).read_text(encoding="utf-8"))


def test_s3_worktree_resolver_returns_single_canonical_candidate():
    """S-3: WT-132 worktree(fossil 4건 + canonical 132). cwd=worktree root.
    후보가 registry exact canonical task_path 정확히 1건."""
    from ownership_tool import resolver  # RED

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    registry = _load(tmp, "registry/active/WT-132/.meta/task_132.json")
    worktree_root = wt_tmp / "task_132"

    candidates = resolver.resolve_worktree(worktree_root, registry)
    assert len(candidates) == 1
    assert candidates[0]["task_path"] == registry["task_path"]


def test_s3_invalid_registry_json_classified_invalid_registry():
    """S-3: registry task_path와 디스크가 불일치(또는 파싱 실패)하면 invalid_registry."""
    from ownership_tool import resolver  # RED

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    invalid_path = tmp / "registry/invalid/invalid_registry.json"
    raw = invalid_path.read_text(encoding="utf-8")
    try:
        registry = json.loads(raw)
    except json.JSONDecodeError:
        registry = raw  # 손상된 원문 그대로 전달 — resolver가 invalid_registry로 분류해야 함

    result = resolver.resolve_worktree(wt_tmp / "task_666", registry)
    assert result == "invalid_registry" or any(
        c.get("classification") == "invalid_registry" for c in result
    )


def test_s3_no_filesystem_scan_in_resolver_source():
    """S-3: resolver 소스가 os.walk/iterdir/.parents 순회나 updated_at/mtime 정렬을 쓰지 않는다."""
    from ownership_tool import resolver  # RED

    src = Path(resolver.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    forbidden_calls = {"walk", "iterdir"}
    forbidden_attrs = {"parents"}
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if node.attr in forbidden_calls or node.attr in forbidden_attrs:
                found.append(node.attr)
    assert not found, f"forbidden filesystem-scan usage found: {found}"
    assert "updated_at" not in src or "sort" not in src


def test_s4_resolve_hub_excludes_foreign_session_owned_from_forced_candidates():
    """S-4: HUB-TWO-SESSIONS. 세션 A가 태스크 X를 lease. 세션 B로 resolve_hub 호출 시
    X는 foreign_session_owned로 강제 후보 제외(진단에는 남음)."""
    from ownership_tool import resolver  # RED

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    registry = _load(tmp, "registry/active/WT-132/.meta/task_132.json")

    # setup: resolve_hub는 <hub_root>/tasks/ 직계 자식만 스캔한다. _clone_fixtures는
    # hub_root를 빈 디렉터리로만 만들므로, HUB-TWO-SESSIONS 픽스처의 태스크를
    # hub_tmp/tasks/ 아래로 이 테스트 안에서 명시적으로 복제한다.
    fixture_hub = FIXTURES_ROOT / "hub" / "HUB-TWO-SESSIONS"
    shutil.copytree(fixture_hub / "tasks", hub_tmp / "tasks", dirs_exist_ok=True)

    # 세션 A(fixture owner-foreign-session.json의 owner_session_id)가 태스크를
    # lease 중인 상태를 배치한다. 만료 시각을 호출 시점(now=15:20)보다 뒤로
    # 조정해 W-3 lease.classify 계약상 foreign_session_owned(만료 아님)가 되도록 한다.
    foreign_lease = json.loads(
        (FIXTURES_ROOT / "runtime" / "owner-foreign-session.json").read_text(encoding="utf-8")
    )
    task_dir = hub_tmp / "tasks" / "210-two-session-x"
    foreign_lease["task_path"] = str(task_dir)
    foreign_lease["lease_expires_at"] = "2026-09-17 19:20:00+09:00"
    owner_path = task_dir / "run" / ".runtime" / "owner.json"
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(json.dumps(foreign_lease), encoding="utf-8")

    classified = resolver.resolve_hub(hub_tmp, registry, "sess-live-0099-B", now="2026-09-17T15:20:00+09:00")
    kinds = {c["classification"] for c in classified}
    assert "foreign_session_owned" in kinds
    forced = [c for c in classified if c.get("forced")]
    assert not any(c["classification"] == "foreign_session_owned" for c in forced)


def test_s4_classify_allows_two_leases_for_same_session():
    """S-4: 세션 A가 X·Y 2건을 lease한 경우 classify가 둘 다 '현재 세션 소유'로 판정."""
    from ownership_tool import resolver  # RED

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    leases = [
        {"task_path": str(hub_tmp / "tasks/200-multi-task-x"), "owner_session_id": "sess-a", "status": "hub_owned"},
        {"task_path": str(hub_tmp / "tasks/201-multi-task-y"), "owner_session_id": "sess-a", "status": "hub_owned"},
    ]
    classified = [resolver.classify(lease, "sess-a") for lease in leases]
    assert all(c == "current_session_owned" for c in classified)


def _write_state(task_dir, task_id, current_status="in_progress"):
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "state.json").write_text(
        json.dumps({"task_id": task_id, "current_status": current_status, "next_action": "EXECUTE"}),
        encoding="utf-8",
    )


def test_w5_resolve_hub_classifies_worktree_canonical_copy_as_shadow_not_outside_hub_root(tmp_path):
    """AC-10, C-7, D-14 — resolver 단위 집행.

    shadow 조건은 canonical task_path가 허브 사본 경로(`<hub_root>/tasks/<task_folder>`)와
    다른지로 판정해야 한다(worktree.md canonical path 발급 계약). 실물 워크트리 canonical은
    `<hub_root>/.opal-worktrees/task_NNN/tasks/<task_folder>`로 hub_root **안**에 있으므로,
    "canonical이 hub_root 밖"을 조건으로 쓰는 술어는 이 실물 배치에서 결코 발화하지 않고
    허브 사본을 `hub_canonical`로 오분류한다(#42/#33 근본원인). registry가 active(키 부재)이고
    허브에 동명 사본이 있으면 이 사본은 `worktree_owned_shadow`로 강제 후보에서 제외되어야
    하며(forced False), `task_path_ambiguous` 동시 발화가 evidence에 남고, 반환 task_path는
    canonical이 아니다(D-14 — canonical path를 shadow 경로에서 반환하지 않는다)."""
    from ownership_tool import resolver  # RED

    hub_root = tmp_path / "hub_root"
    wt_root = hub_root / ".opal-worktrees"
    task_folder = "138-shadow-case"
    canonical_dir = wt_root / "task_138" / "tasks" / task_folder
    hub_copy_dir = hub_root / "tasks" / task_folder

    _write_state(canonical_dir, task_folder)
    _write_state(hub_copy_dir, task_folder)

    registry = {
        "allocator_root": str(hub_root),
        "task_home": str(wt_root / "task_138"),
        "task_folder": task_folder,
        "task_path": str(canonical_dir),
        "artifact_repo": str(hub_root),
        "task_ownership_version": 1,
        # attribution_state 키 부재 = active 3상태 중 하나
    }

    classified = resolver.resolve_hub(hub_root, [registry], "sess-live", now="2026-09-17T15:20:00+09:00")
    matches = [c for c in classified if c["task_id"] == task_folder]
    assert len(matches) == 1
    candidate = matches[0]
    assert candidate["classification"] == "worktree_owned_shadow"
    assert candidate["forced"] is False
    assert candidate["evidence"].get("task_path_ambiguous") is True
    assert candidate["task_path"] != registry["task_path"]


def test_w5_resolve_hub_closed_attribution_hub_copy_is_hub_canonical_not_shadow(tmp_path):
    """AC-11 — resolver 단위 집행. 같은 배치에서 `attribution_state: closed`만 다르면
    허브 사본은 shadow로 제외되지 않고 `hub_canonical`로 판정된다."""
    from ownership_tool import resolver  # RED

    hub_root = tmp_path / "hub_root"
    wt_root = hub_root / ".opal-worktrees"
    task_folder = "138-shadow-case"
    canonical_dir = wt_root / "task_138" / "tasks" / task_folder
    hub_copy_dir = hub_root / "tasks" / task_folder

    _write_state(canonical_dir, task_folder)
    _write_state(hub_copy_dir, task_folder)

    registry = {
        "allocator_root": str(hub_root),
        "task_home": str(wt_root / "task_138"),
        "task_folder": task_folder,
        "task_path": str(canonical_dir),
        "artifact_repo": str(hub_root),
        "task_ownership_version": 1,
        "attribution_state": "closed",
    }

    classified = resolver.resolve_hub(hub_root, [registry], "sess-live", now="2026-09-17T15:20:00+09:00")
    matches = [c for c in classified if c["task_id"] == task_folder]
    assert len(matches) == 1
    candidate = matches[0]
    assert candidate["classification"] == "hub_canonical"
    assert candidate["classification"] != "worktree_owned_shadow"
