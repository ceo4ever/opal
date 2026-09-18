# @header
# module: worktree_launcher.tests.test_launcher_core
# layer: test
# domain: worktree-launcher
# description: RED-first — worktree_launcher.launcher_core.run() 공개 계약 검증(S-15). registry는 W-11(worktree_tool.cmd_ownership_set)이 소유하는 v2 스키마(`<hub>/.opal-worktrees/.meta/task_{NNN}.json`, 중첩 `execution_ownership` 블록·최상위 `attribution_state` 키 부재=active)를 대상으로 하고, receipt는 `adapter.launch(worktree_root, command)` 반환으로만 얻는다 — run()이 registry를 직접 재발명하거나 fixture를 인자로 직접 받지 않는다.
# exports: (none — pytest module)
# depends: worktree_launcher.launcher_core(미구현), conftest.build_launcher_hub/load_launcher_fixture/read_meta
"""RED 테스트 — 구현 전. worktree_launcher 패키지 자체가 없으므로 각 테스트가
`from worktree_launcher import launcher_core`에서 ModuleNotFoundError로 실패해야 한다.
그 앞의 registry/fixture 셋업은 GREEN 구현이 지켜야 할 실물 동형 전제(conftest.py 참조)를
미리 고정해 둔다."""
from __future__ import annotations

from conftest import build_launcher_hub, load_launcher_fixture, read_meta


class _FakeAdapter:
    """adapter seam 대역. launcher_core.run()이 `adapter.launch(worktree_root, command)`를
    실제로 호출해 receipt를 얻어야 이 경계가 통과된다 — fixture를 run()에 직접 주입하지
    않는다(PM 감사 3항: adapter seam 미검증 시정)."""

    def __init__(self, fixture: dict):
        self._fixture = fixture
        self.calls: list[tuple] = []

    def launch(self, worktree_root, command):
        self.calls.append((worktree_root, command))
        return self._fixture


def test_success_path_sets_worktree_session_owned_only_after_both_receipts(tmp_path):
    """성공: launch·prompt receipt 둘 다 기록된 뒤에만 worktree_session_owned."""
    from worktree_launcher import launcher_core  # RED

    hub = build_launcher_hub(tmp_path, adapter="generic")
    fixture = load_launcher_fixture("fake_process-success.json", hub.hub, hub.wt_parent)
    adapter = _FakeAdapter(fixture)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )

    assert adapter.calls == [(hub.worktree_root, "claude")]
    assert result["status"] == "worktree_session_owned"

    data = read_meta(hub.meta_path)
    eo = data["execution_ownership"]
    assert eo["state"] == "worktree_session_owned"
    assert eo["launch_receipt"] is not None
    assert eo["prompt_receipt"] is not None
    assert "attribution_state" not in data


def test_launch_failed_path_reverts_atomically(tmp_path):
    """launch 실패: failure_reason=launch_failed, generation+1, hub_owned +
    attribution_state 키 부재로 원자 복귀."""
    from worktree_launcher import launcher_core  # RED

    hub = build_launcher_hub(
        tmp_path, adapter="generic", prior_state="session_launching", prior_generation=1
    )
    fixture = load_launcher_fixture("fake_process-launch-failed.json", hub.hub, hub.wt_parent)
    adapter = _FakeAdapter(fixture)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )
    assert result["failure_reason"] == "launch_failed"

    data = read_meta(hub.meta_path)
    eo = data["execution_ownership"]
    assert eo["state"] == "hub_owned"
    assert eo["failure_reason"] == "launch_failed"
    assert eo["generation"] == 2
    assert eo["owner_session_id"] is None
    assert eo["launch_receipt"] is None
    assert eo["prompt_receipt"] is None
    assert "attribution_state" not in data


def test_prompt_failed_path_reverts_atomically(tmp_path):
    """prompt 실패도 launch_failed 경로와 동일하게 원자 복귀한다."""
    from worktree_launcher import launcher_core  # RED

    hub = build_launcher_hub(
        tmp_path, adapter="generic", prior_state="session_launching", prior_generation=1
    )
    fixture = load_launcher_fixture("fake_process-prompt-failed.json", hub.hub, hub.wt_parent)
    adapter = _FakeAdapter(fixture)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )
    assert result["failure_reason"] == "launch_failed"

    data = read_meta(hub.meta_path)
    eo = data["execution_ownership"]
    assert eo["state"] == "hub_owned"
    assert eo["generation"] == 2
    assert eo["owner_session_id"] is None
    assert eo["launch_receipt"] is None
    assert eo["prompt_receipt"] is None
    assert "attribution_state" not in data


def test_cwd_mismatch_path_reverts_atomically(tmp_path):
    """reported_cwd 불일치도 launch_failed 경로로 원자 복귀한다 — MUST cwd 가드
    (reported_cwd가 registry worktree_root와 불일치하면 launch_failed)."""
    from worktree_launcher import launcher_core  # RED

    hub = build_launcher_hub(
        tmp_path, adapter="orca", prior_state="session_launching", prior_generation=1
    )
    fixture = load_launcher_fixture("fake_process-cwd-mismatch.json", hub.hub, hub.wt_parent)
    # fixture의 reported_cwd는 {HUB}(허브 루트 자체)로 치환돼 worktree_root와 불일치한다.
    assert fixture["reported_cwd"] != str(hub.worktree_root)
    assert fixture["expected_worktree_root"] == str(hub.worktree_root)
    adapter = _FakeAdapter(fixture)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )
    assert result["failure_reason"] == "launch_failed"

    data = read_meta(hub.meta_path)
    eo = data["execution_ownership"]
    assert eo["state"] == "hub_owned"
    assert eo["generation"] == 2
    assert eo["owner_session_id"] is None
    assert "attribution_state" not in data


def test_no_dual_owner_or_orphan_session_launching_across_all_paths(tmp_path):
    """어느 경로도 owner 2건 또는 owner 없는 session_launching 잔존을 남기지 않는다."""
    from worktree_launcher import launcher_core  # RED

    cases = (
        ("fake_process-success.json", "generic"),
        ("fake_process-launch-failed.json", "generic"),
        ("fake_process-prompt-failed.json", "generic"),
        ("fake_process-cwd-mismatch.json", "orca"),
    )
    for idx, (name, adapter_name) in enumerate(cases):
        hub = build_launcher_hub(
            tmp_path / f"case-{idx}",
            adapter=adapter_name,
            prior_state="session_launching",
            prior_generation=1,
        )
        fixture = load_launcher_fixture(name, hub.hub, hub.wt_parent)
        adapter = _FakeAdapter(fixture)
        launcher_core.run(
            adapter,
            hub_root=hub.hub,
            task=hub.task,
            worktree_root=hub.worktree_root,
            command="claude",
        )
        data = read_meta(hub.meta_path)
        eo = data["execution_ownership"]
        assert eo["state"] != "session_launching", f"{name}: session_launching 잔존"
        if eo["state"] == "hub_owned":
            assert eo["owner_session_id"] is None, f"{name}: hub_owned인데 owner 잔존(orphan)"
        if eo["state"] == "worktree_session_owned":
            assert eo["owner_session_id"] is not None
