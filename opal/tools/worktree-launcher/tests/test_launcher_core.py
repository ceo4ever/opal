# @header
# module: worktree_launcher.tests.test_launcher_core
# layer: test
# domain: worktree-launcher
# description: RED-first — worktree_launcher.launcher_core.run() 공개 계약 검증 (S-15)
# exports: (none — pytest module)
# depends: worktree_launcher.launcher_core (미구현), ownership-tool fixtures/launcher
"""RED 테스트 — 구현 전. worktree_launcher 패키지 자체가 없으므로 ImportError로 실패해야 한다."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES_ROOT = (
    Path(__file__).parent.parent.parent / "ownership-tool" / "tests" / "fixtures" / "launcher"
)


def _load(name: str) -> dict:
    return json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))


class _FakeAdapter:
    def __init__(self, fixture: dict):
        self._fixture = fixture

    def launch(self, worktree_root, command):
        return self._fixture


def test_success_path_sets_worktree_session_owned_only_after_both_receipts(tmp_path):
    """성공: launch·prompt receipt 둘 다 기록된 뒤에만 worktree_session_owned."""
    from worktree_launcher import launcher_core  # RED

    fixture = _load("fake_process-success.json")
    adapter = _FakeAdapter(fixture)
    registry_path = tmp_path / "owner.json"

    result = launcher_core.run(adapter, fixture, registry_path=registry_path, worktree_root=tmp_path)
    assert result["status"] == "worktree_session_owned"
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    assert data["status"] == "worktree_session_owned"


def test_launch_failed_path_reverts_atomically(tmp_path):
    """launch 실패: failure_reason=launch_failed, generation+1, hub_owned + attribution_state 부재로 원자 복귀."""
    from worktree_launcher import launcher_core  # RED

    fixture = _load("fake_process-launch-failed.json")
    adapter = _FakeAdapter(fixture)
    registry_path = tmp_path / "owner.json"
    registry_path.write_text(json.dumps({"status": "session_launching", "generation": 1}), encoding="utf-8")

    result = launcher_core.run(adapter, fixture, registry_path=registry_path, worktree_root=tmp_path)
    assert result["failure_reason"] == "launch_failed"
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    assert data["status"] == "hub_owned"
    assert "attribution_state" not in data
    assert data["generation"] == 2


def test_prompt_failed_path_reverts_atomically(tmp_path):
    """prompt 실패도 launch_failed 경로와 동일하게 원자 복귀한다."""
    from worktree_launcher import launcher_core  # RED

    fixture = _load("fake_process-prompt-failed.json")
    adapter = _FakeAdapter(fixture)
    registry_path = tmp_path / "owner.json"
    registry_path.write_text(json.dumps({"status": "session_launching", "generation": 1}), encoding="utf-8")

    result = launcher_core.run(adapter, fixture, registry_path=registry_path, worktree_root=tmp_path)
    assert result["failure_reason"] == "launch_failed"
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    assert data["status"] == "hub_owned"


def test_cwd_mismatch_path_reverts_atomically(tmp_path):
    """reported_cwd 불일치도 launch_failed 경로로 원자 복귀한다."""
    from worktree_launcher import launcher_core  # RED

    fixture = _load("fake_process-cwd-mismatch.json")
    adapter = _FakeAdapter(fixture)
    registry_path = tmp_path / "owner.json"
    registry_path.write_text(json.dumps({"status": "session_launching", "generation": 1}), encoding="utf-8")

    result = launcher_core.run(adapter, fixture, registry_path=registry_path, worktree_root=fixture["expected_worktree_root"])
    assert result["failure_reason"] == "launch_failed"
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    assert data["status"] == "hub_owned"


def test_no_dual_owner_or_orphan_session_launching_across_all_paths(tmp_path):
    """어느 경로도 owner 2건 또는 owner 없는 session_launching 잔존을 남기지 않는다."""
    from worktree_launcher import launcher_core  # RED

    for name in (
        "fake_process-success.json",
        "fake_process-launch-failed.json",
        "fake_process-prompt-failed.json",
        "fake_process-cwd-mismatch.json",
    ):
        fixture = _load(name)
        adapter = _FakeAdapter(fixture)
        registry_path = tmp_path / f"owner-{name}.json"
        registry_path.write_text(json.dumps({"status": "session_launching", "generation": 1}), encoding="utf-8")
        launcher_core.run(adapter, fixture, registry_path=registry_path, worktree_root=tmp_path)
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        assert data["status"] != "session_launching"
