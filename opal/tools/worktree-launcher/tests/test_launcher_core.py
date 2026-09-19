# @header
# module: worktree_launcher.tests.test_launcher_core
# layer: test
# domain: worktree-launcher
# description: worktree_launcher.launcher_core.run() 공개 계약 검증. registry는 worktree_tool.cmd_ownership_set이 소유하는 v2 스키마(`<hub>/.opal-worktrees/.meta/task_{NNN}.json`, 중첩 `execution_ownership` 블록·최상위 `attribution_state` 키 부재=active)를 대상으로 하고, receipt는 `adapter.launch(worktree_root, command)` 반환으로만 얻는다 — run()이 registry를 직접 재발명하거나 fixture를 인자로 직접 받지 않는다. 후반부는 S-4(원자 복귀 시 터미널 정리)를 소유한다 — 복귀 5경로에서 `adapter.close(handle=…)`가 정확히 1회 호출되는지, handle 부재 시 close를 시도하지 않는지, close의 예외·미구현·비-0 exit에도 복귀가 수행되고 실패가 `terminal_close`로만 남는지 검증한다. adapter는 전부 fake이며 실제 orca·실제 터미널을 호출하지 않는다.
# exports: (none — pytest module)
# depends: worktree_launcher.launcher_core, conftest.build_launcher_hub/load_launcher_fixture/read_meta
"""launcher_core.run() 단위 테스트. registry/fixture 셋업의 실물 동형 전제는 conftest.py가
소유하고, 구현 모듈 import는 각 테스트 함수 첫 줄에서 수행한다."""
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
    from worktree_launcher import launcher_core

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
    from worktree_launcher import launcher_core

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
    from worktree_launcher import launcher_core

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
    from worktree_launcher import launcher_core

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
    from worktree_launcher import launcher_core

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


# ─────────────────────────────────────────────────────────────────────────────
# S-4 — 원자 복귀 시 터미널 정리(W-5). 실제 orca·실제 터미널은 호출하지 않는다.
# ─────────────────────────────────────────────────────────────────────────────


class _ClosingAdapter:
    """close seam을 가진 adapter 대역. `close(handle=…)` 호출을 기록만 하고 실제
    터미널을 닫지 않는다 — D-J의 close 보고 스키마(`scope`·`closed`·`exit_code`)만 흉내낸다."""

    def __init__(self, report, *, close_raises=None, close_exit_code=0):
        self._report = report
        self._close_raises = close_raises
        self._close_exit_code = close_exit_code
        self.launch_calls: list[tuple] = []
        self.close_calls: list[dict] = []

    def launch(self, worktree_root, command):
        self.launch_calls.append((worktree_root, command))
        return self._report

    def close(self, *, handle=None, worktree_root=None, all=False):
        self.close_calls.append({"handle": handle, "worktree_root": worktree_root, "all": all})
        if self._close_raises is not None:
            raise self._close_raises
        return {
            "adapter": "fake",
            "exit_code": self._close_exit_code,
            "fallback_attempted": False,
            "scope": "terminal",
            "closed": [handle] if self._close_exit_code == 0 else [],
        }


def _revert_hub(tmp_path, adapter_name="generic"):
    return build_launcher_hub(
        tmp_path, adapter=adapter_name, prior_state="session_launching", prior_generation=1
    )


def _assert_reverted(hub, result):
    """복귀 불변식 — close 결과와 무관하게 항상 성립해야 한다."""
    assert result["failure_reason"] == "launch_failed"
    data = read_meta(hub.meta_path)
    eo = data["execution_ownership"]
    assert eo["state"] == "hub_owned"
    assert eo["generation"] == 2
    assert eo["owner_session_id"] is None
    assert "attribution_state" not in data


def _report_with_handle(hub, name, **overrides):
    report = load_launcher_fixture(name, hub.hub, hub.wt_parent)
    report.update(overrides)
    return report


def test_revert_closes_reported_terminal_exactly_once_on_every_handle_path(tmp_path):
    """복귀 경로에서 launch 보고의 `adapter_handle`로 close가 **정확히 1회** 호출된다.

    `launch_receipt_missing`(handle은 왔으나 receipt 불완전)·`reported_cwd_mismatch`·
    `prompt_receipt_missing` 3경로가 같은 정리 경로를 탄다. `adapter_report_invalid`는
    보고가 dict가 아니라 handle 원천 자체가 없으므로 별도 테스트가 소유한다."""
    from worktree_launcher import launcher_core

    cases = (
        ("launch_receipt_missing", "fake_process-success.json", "orca", {"launched_at": None}),
        ("reported_cwd_mismatch", "fake_process-cwd-mismatch.json", "orca", {}),
        ("prompt_receipt_missing", "fake_process-prompt-failed.json", "generic", {}),
    )
    for idx, (detail, fixture_name, adapter_name, overrides) in enumerate(cases):
        hub = _revert_hub(tmp_path / f"close-{idx}", adapter_name)
        report = _report_with_handle(hub, fixture_name, **overrides)
        adapter = _ClosingAdapter(report)

        result = launcher_core.run(
            adapter,
            hub_root=hub.hub,
            task=hub.task,
            worktree_root=hub.worktree_root,
            command="claude",
        )

        assert result["detail"] == detail
        assert len(adapter.close_calls) == 1, f"{detail}: close 호출 {len(adapter.close_calls)}회"
        assert adapter.close_calls[0]["handle"] == report["adapter_handle"]
        # 정밀 스코프다 — 워크스페이스 스윕(`worktree_root`+`all`)을 쓰지 않는다(D-C).
        assert adapter.close_calls[0]["worktree_root"] is None
        assert adapter.close_calls[0]["all"] is False
        assert result["terminal_close"]["attempted"] is True
        assert result["terminal_close"]["ok"] is True
        assert result["terminal_close"]["handle"] == report["adapter_handle"]
        _assert_reverted(hub, result)


def test_revert_without_reported_handle_does_not_attempt_close(tmp_path):
    """`adapter_handle`이 없으면 close를 **시도하지 않는다**(대상 추측 금지).

    (a) `adapter_report_invalid` — 보고가 dict가 아니어서 handle 원천이 없다.
    (b) `launch_receipt_missing` — 보고는 dict지만 `adapter_handle`이 null이다."""
    from worktree_launcher import launcher_core

    hub_a = _revert_hub(tmp_path / "no-handle-a")
    adapter_a = _ClosingAdapter("not-a-dict")
    result_a = launcher_core.run(
        adapter_a,
        hub_root=hub_a.hub,
        task=hub_a.task,
        worktree_root=hub_a.worktree_root,
        command="claude",
    )
    assert result_a["detail"] == "adapter_report_invalid"
    assert adapter_a.close_calls == []
    assert result_a["terminal_close"] == {"attempted": False, "reason": "handle_missing"}
    _assert_reverted(hub_a, result_a)

    hub_b = _revert_hub(tmp_path / "no-handle-b")
    report_b = load_launcher_fixture("fake_process-launch-failed.json", hub_b.hub, hub_b.wt_parent)
    assert report_b["adapter_handle"] is None
    adapter_b = _ClosingAdapter(report_b)
    result_b = launcher_core.run(
        adapter_b,
        hub_root=hub_b.hub,
        task=hub_b.task,
        worktree_root=hub_b.worktree_root,
        command="claude",
    )
    assert result_b["detail"] == "launch_receipt_missing"
    assert adapter_b.close_calls == []
    assert result_b["terminal_close"] == {"attempted": False, "reason": "handle_missing"}
    _assert_reverted(hub_b, result_b)


def test_revert_is_performed_even_when_close_raises(tmp_path):
    """close가 예외를 던져도 복귀는 **반드시 수행**되고, 실패는 `terminal_close`로만 남는다
    — 복귀가 정리 성공에 종속되면 dual owner가 남는다."""
    from worktree_launcher import launcher_core

    hub = _revert_hub(tmp_path, "orca")
    report = load_launcher_fixture("fake_process-cwd-mismatch.json", hub.hub, hub.wt_parent)
    adapter = _ClosingAdapter(report, close_raises=RuntimeError("orca unreachable"))

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )

    assert len(adapter.close_calls) == 1
    close_log = result["terminal_close"]
    assert close_log["attempted"] is True
    assert close_log["ok"] is False
    assert close_log["reason"] == "close_failed"
    assert "orca unreachable" in close_log["detail"]
    _assert_reverted(hub, result)


def test_revert_is_performed_even_when_close_reports_non_zero_exit(tmp_path):
    """close가 예외 대신 `exit_code != 0` 실패 dict를 돌려주는 경우(D-J)도 같다."""
    from worktree_launcher import launcher_core

    hub = _revert_hub(tmp_path, "orca")
    report = load_launcher_fixture("fake_process-cwd-mismatch.json", hub.hub, hub.wt_parent)
    adapter = _ClosingAdapter(report, close_exit_code=3)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )

    assert len(adapter.close_calls) == 1
    assert result["terminal_close"]["ok"] is False
    assert result["terminal_close"]["reason"] == "close_rejected"
    _assert_reverted(hub, result)


def test_revert_is_performed_when_adapter_has_no_close(tmp_path):
    """close 미구현(`AttributeError`) adapter도 복귀를 막지 않는다 — `_FakeAdapter`는
    close seam이 없는 구형 대역이다."""
    from worktree_launcher import launcher_core

    hub = _revert_hub(tmp_path, "orca")
    fixture = load_launcher_fixture("fake_process-cwd-mismatch.json", hub.hub, hub.wt_parent)
    adapter = _FakeAdapter(fixture)
    assert not hasattr(adapter, "close")

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )

    close_log = result["terminal_close"]
    assert close_log["attempted"] is False
    assert close_log["reason"] == "close_unsupported"
    assert close_log["handle"] == fixture["adapter_handle"]
    _assert_reverted(hub, result)


def test_success_path_never_closes_the_terminal(tmp_path):
    """성공 경로는 살아 있는 세션 터미널을 닫지 않는다 — close는 복귀 전용이다."""
    from worktree_launcher import launcher_core

    hub = _revert_hub(tmp_path)
    report = load_launcher_fixture("fake_process-success.json", hub.hub, hub.wt_parent)
    adapter = _ClosingAdapter(report)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )

    assert result["status"] == "worktree_session_owned"
    assert adapter.close_calls == []
    assert "terminal_close" not in result


def test_revert_closes_terminal_when_ownership_set_rejects_the_owned_transition(
    tmp_path, monkeypatch
):
    """5번째 복귀 경로(`ownership_set_rejected`)도 같은 정리 경로를 탄다.

    이 시점의 터미널은 launch receipt가 성립한 뒤라 **확실히 살아 있다** — 여기를 비워두면
    복귀는 되는데 고아 터미널이 남는다(AC-4 미달). `ownership-set`의 거부 응답은 실제
    `worktree-tool` 판정 규칙에 결합하지 않도록 seam에서 주입하고, 복귀 전이 자체는 실제
    `ownership-set`에 그대로 위임한다."""
    from worktree_launcher import launcher_core

    hub = _revert_hub(tmp_path)
    report = load_launcher_fixture("fake_process-success.json", hub.hub, hub.wt_parent)
    adapter = _ClosingAdapter(report)

    real_ownership_set = launcher_core.ownership_set

    def _reject_owned_transition(hub_root, task, state, **options):
        if state == "worktree_session_owned":
            return {"ok": False, "error": "execution_ownership_transition_rejected"}
        return real_ownership_set(hub_root, task, state, **options)

    monkeypatch.setattr(launcher_core, "ownership_set", _reject_owned_transition)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )

    assert result["detail"].startswith("ownership_set_rejected: ")
    assert len(adapter.close_calls) == 1
    assert adapter.close_calls[0]["handle"] == report["adapter_handle"]
    assert adapter.close_calls[0]["worktree_root"] is None
    assert adapter.close_calls[0]["all"] is False
    assert result["terminal_close"] == {
        "attempted": True,
        "ok": True,
        "handle": report["adapter_handle"],
    }
    _assert_reverted(hub, result)
