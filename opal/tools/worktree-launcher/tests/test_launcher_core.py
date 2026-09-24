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

    assert len(adapter.calls) == 1
    assert adapter.calls[0][0] == hub.worktree_root
    import shlex
    assert shlex.split(adapter.calls[0][1])[-3:] == ["session-launch", "--command", "claude"]
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
            assert eo["owner_session_id"] is None  # no child claim in this fixture


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


# ─────────────────────────────────────────────────────────────────────────────
# TASK 150 — S-8(AC-1, C-4) · S-9(AC-1) launcher의 lease 이관 호출과 복귀
#
# @header 보강: layer=test / domain=opal-workspace. W-6은 `ownership_set()`과 동형의
# 얇은 호출자 `lease_handoff(task_path, worktree_root)` · `lease_handoff_cancel(task_path)`를
# 추가하고, `run()`이 preflight `session_launching` 전이 직후 · `adapter.launch` **직전**에
# `lease_handoff`를 1회 호출한다. `_revert()`는 `ownership_set` 복귀 호출 전에
# `lease_handoff_cancel`을 1회 호출하고 결과를 `lease_handoff_cancel` 로그 필드로만 싣는다
# (취소 실패가 복귀를 막지 않는다 — 기존 `terminal_close` 취급과 동형).
#
# 이름 주의: 이 파일의 기존 `prompt_receipt`/handoff prompt는 **새 터미널에 보내는 첫 발화**를
# 뜻하고 lease 이관과 다른 개념이다. lease 축은 전부 `lease_` 접두 이름으로만 지칭한다.
#
# lease 판정·쓰기는 ownership_tool이 소유하므로(D-2), 호출 계약 검증은 `launcher_core`의
# 모듈 속성 seam(기존 `ownership_set` monkeypatch 선례와 동형)에서 관측한다.
# ─────────────────────────────────────────────────────────────────────────────

import json
import sys
from pathlib import Path

OWNERSHIP_TOOL_DIR = Path(__file__).resolve().parents[2] / "ownership-tool"
LEASE_HUB_SESSION = "sess-hub-150"


def _hub_with_canonical_task(tmp_path, **kwargs):
    """`build_launcher_hub`가 만든 registry meta에 canonical `task_path` 발급값을 채운다.

    lease 대상 task 경로는 registry meta 발급값에서만 취해야 하므로(C-4, D-4) 그 값이
    meta에 실재하는 상태를 만든다 — 기본 헬퍼는 `task_path: None`으로 둔다.
    """
    hub = build_launcher_hub(tmp_path, **kwargs)
    task_folder = "{}-lease-handoff".format(hub.task)
    task_dir = hub.worktree_root / "tasks" / task_folder
    task_dir.mkdir(parents=True, exist_ok=True)
    meta = read_meta(hub.meta_path)
    meta["task_folder"] = task_folder
    meta["task_path"] = str(task_dir)
    hub.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return hub, task_dir


class _OrderRecordingAdapter(_ClosingAdapter):
    """launch 호출 시점을 공유 순서 로그에 남기는 adapter 대역."""

    def __init__(self, report, order, **kwargs):
        super().__init__(report, **kwargs)
        self._order = order

    def launch(self, worktree_root, command):
        self._order.append("adapter.launch")
        return super().launch(worktree_root, command)


def _patch_lease_seams(monkeypatch, launcher_core, order, *, handoff_result=None,
                       cancel_result=None, cancel_raises=None):
    """`lease_handoff`/`lease_handoff_cancel` 호출을 관측한다(호출 substitute).

    monkeypatch.setattr는 속성이 없으면 AttributeError로 실패한다 — 구현 전에는 이 지점이
    RED가 된다(seam 자체가 계약이다).
    """
    handoff_calls = []
    cancel_calls = []

    def _fake_handoff(task_path, worktree_root, session_id=None):
        order.append("lease_handoff")
        handoff_calls.append((str(task_path), str(worktree_root)))
        return dict(handoff_result if handoff_result is not None else {"ok": True})

    def _fake_cancel(task_path, session_id=None):
        order.append("lease_handoff_cancel")
        cancel_calls.append(str(task_path))
        if cancel_raises is not None:
            raise cancel_raises
        return dict(cancel_result if cancel_result is not None else {"ok": True})

    monkeypatch.setattr(launcher_core, "lease_handoff", _fake_handoff)
    monkeypatch.setattr(launcher_core, "lease_handoff_cancel", _fake_cancel)
    return handoff_calls, cancel_calls


def test_s8_lease_handoff_runs_exactly_once_before_adapter_launch(tmp_path, monkeypatch):
    """S-8(AC-1, C-4): 이관 호출이 `adapter.launch`보다 **먼저 정확히 1회** 발생하고,
    전달된 task 경로·대상 루트가 registry 발급값과 일치한다. 성공 반환 dict에
    `lease_handoff` 필드가 additive로 실린다."""
    from worktree_launcher import launcher_core  # RED: lease_handoff 미구현

    hub, task_dir = _hub_with_canonical_task(tmp_path)
    meta = read_meta(hub.meta_path)
    order = []
    handoff_calls, cancel_calls = _patch_lease_seams(monkeypatch, launcher_core, order)

    report = load_launcher_fixture("fake_process-success.json", hub.hub, hub.wt_parent)
    adapter = _OrderRecordingAdapter(report, order)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )

    assert result["ok"] is True, result
    assert result["status"] == "worktree_session_owned"
    # [MUST] 순서 — 이관이 기동보다 늦으면 워크트리 세션이 부팅하는 동안 허브가 소유자다.
    assert order == ["lease_handoff", "adapter.launch"], order
    assert handoff_calls == [(meta["task_path"], meta["worktree_root"])], handoff_calls
    assert cancel_calls == [], "성공 경로는 이관을 취소하지 않는다"
    assert result["lease_handoff"] == {"ok": True}


def test_s8_noop_handoff_still_proceeds_to_launch(tmp_path, monkeypatch):
    """S-8(AC-1): 이관이 `noop`(live lease 부재)이면 그것도 정상 경로다 — 기동을 막지 않는다."""
    from worktree_launcher import launcher_core

    hub, task_dir = _hub_with_canonical_task(tmp_path)
    order = []
    handoff_calls, cancel_calls = _patch_lease_seams(
        monkeypatch, launcher_core, order,
        handoff_result={"ok": True, "noop": True, "diagnostic": "no_live_lease"},
    )
    report = load_launcher_fixture("fake_process-success.json", hub.hub, hub.wt_parent)
    adapter = _OrderRecordingAdapter(report, order)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )

    assert result["ok"] is True, result
    assert order == ["lease_handoff", "adapter.launch"], order
    assert len(handoff_calls) == 1


def test_s8_failed_handoff_reverts_without_launching(tmp_path, monkeypatch):
    """S-8(AC-1): 이관이 `ok`도 `noop`도 아니면 기동하지 않고 `hub_owned`로 복귀한다."""
    from worktree_launcher import launcher_core

    hub, task_dir = _hub_with_canonical_task(tmp_path)
    order = []
    handoff_calls, cancel_calls = _patch_lease_seams(
        monkeypatch, launcher_core, order,
        handoff_result={"ok": False, "error": "not_owner"},
    )
    report = load_launcher_fixture("fake_process-success.json", hub.hub, hub.wt_parent)
    adapter = _OrderRecordingAdapter(report, order)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )

    assert adapter.launch_calls == [], "이관 실패 시 터미널을 띄우지 않는다"
    assert "adapter.launch" not in order, order
    assert result["detail"] == "lease_handoff_failed", result
    _assert_reverted(hub, result)


def test_s8_launcher_core_source_holds_no_lease_write_or_lock_code(tmp_path):
    """S-8: launcher 모듈 본문에 lease 파일 쓰기·락 코드가 없다(D-2 — 사설 lease writer 금지)."""
    from worktree_launcher import launcher_core

    source = Path(launcher_core.__file__).read_text(encoding="utf-8")
    for token in (
        "owner.json",
        "write_json_atomic",
        "fcntl",
        "LOCK_EX",
        "os.replace",
        "handoff_expires_at",
        "handoff_from_session_id",
        "handoff_pending",
    ):
        assert token not in source, "launcher가 lease 저장을 복제한다: {}".format(token)
    assert "lease_handoff" in source


# ─────────────────────────────────────────────────────────────────────────────
# S-9 (AC-1) — launch 실패 5경로 전건에서 이관취소 + 허브 복귀
# ─────────────────────────────────────────────────────────────────────────────


def _s9_case_runner(tmp_path, monkeypatch, launcher_core, detail, order, **seam_kwargs):
    """5개 복귀 경로 각각을 같은 방식으로 실행해 (hub, result, cancel_calls)를 돌려준다."""
    hub, task_dir = _hub_with_canonical_task(tmp_path)
    handoff_calls, cancel_calls = _patch_lease_seams(
        monkeypatch, launcher_core, order, **seam_kwargs
    )

    if detail == "adapter_report_invalid":
        adapter = _OrderRecordingAdapter("not-a-dict", order)
    elif detail == "launch_receipt_missing":
        report = load_launcher_fixture("fake_process-success.json", hub.hub, hub.wt_parent)
        report["launched_at"] = None
        adapter = _OrderRecordingAdapter(report, order)
    elif detail == "reported_cwd_mismatch":
        report = load_launcher_fixture("fake_process-cwd-mismatch.json", hub.hub, hub.wt_parent)
        adapter = _OrderRecordingAdapter(report, order)
    elif detail == "prompt_receipt_missing":
        report = load_launcher_fixture("fake_process-prompt-failed.json", hub.hub, hub.wt_parent)
        adapter = _OrderRecordingAdapter(report, order)
    else:  # ownership_set_rejected
        report = load_launcher_fixture("fake_process-success.json", hub.hub, hub.wt_parent)
        adapter = _OrderRecordingAdapter(report, order)
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
    return hub, task_dir, result, cancel_calls


S9_REVERT_DETAILS = (
    "adapter_report_invalid",
    "launch_receipt_missing",
    "reported_cwd_mismatch",
    "prompt_receipt_missing",
    "ownership_set_rejected",
)


def test_s9_all_five_launch_failure_paths_cancel_the_handoff_and_return_to_hub(
    tmp_path, monkeypatch
):
    """S-9(AC-1): launch 실패 5경로 전건에서 이관취소가 **정확히 1회** 호출되고 registry가
    `hub_owned`로 복귀한다. 취소는 `ownership_set` 복귀 호출보다 **먼저** 일어난다."""
    from worktree_launcher import launcher_core  # RED: lease_handoff_cancel 미구현

    for index, detail in enumerate(S9_REVERT_DETAILS):
        order = []
        hub, task_dir, result, cancel_calls = _s9_case_runner(
            tmp_path / "s9-{}".format(index), monkeypatch, launcher_core, detail, order
        )
        meta = read_meta(hub.meta_path)

        assert str(result["detail"]).startswith(detail), (detail, result)
        assert len(cancel_calls) == 1, "{}: 이관취소 {}회".format(detail, len(cancel_calls))
        assert cancel_calls[0] == meta["task_path"], (detail, cancel_calls)
        assert order.index("lease_handoff_cancel") > order.index("lease_handoff"), order
        assert result["lease_handoff_cancel"] == {"ok": True}, (detail, result)
        _assert_reverted(hub, result)


def test_s9_failed_handoff_cancel_does_not_block_the_revert(tmp_path, monkeypatch):
    """S-9(AC-1): 이관취소 자체가 실패해도 registry 복귀는 수행되고, 실패 사실은 반환
    로그 필드(`lease_handoff_cancel`)로만 남는다 — 복귀가 취소 성공에 종속되면 dual owner가
    남는다(기존 `terminal_close` 취급과 동일한 결)."""
    from worktree_launcher import launcher_core

    # ① 취소가 구조화 실패를 돌려주는 경우.
    order_a = []
    hub_a, _task_a, result_a, cancel_a = _s9_case_runner(
        tmp_path / "cancel-not-ok", monkeypatch, launcher_core, "reported_cwd_mismatch", order_a,
        cancel_result={"ok": False, "error": "not_handoff_owner"},
    )
    assert len(cancel_a) == 1
    assert result_a["lease_handoff_cancel"]["ok"] is False, result_a
    _assert_reverted(hub_a, result_a)

    # ② 취소 호출 자체가 예외를 던지는 경우도 복귀를 막지 않는다.
    order_b = []
    hub_b, _task_b, result_b, cancel_b = _s9_case_runner(
        tmp_path / "cancel-raises", monkeypatch, launcher_core, "prompt_receipt_missing", order_b,
        cancel_raises=RuntimeError("ownership-tool unreachable"),
    )
    assert len(cancel_b) == 1
    assert result_b["lease_handoff_cancel"]["ok"] is False, result_b
    assert "ownership-tool unreachable" in json.dumps(
        result_b["lease_handoff_cancel"], ensure_ascii=False
    )
    _assert_reverted(hub_b, result_b)


def test_s9_lease_owner_returns_to_the_hub_session_on_launch_failure(tmp_path, monkeypatch):
    """S-9(AC-1) 실연동: seam 대역 없이 실제 `lease_handoff`/`lease_handoff_cancel`을 태워
    **lease 레코드의 소유자가 이관 전 허브 세션으로 되돌아오는지**를 저장 결과로 관측한다.

    호출 substitute가 아니라 owner.json 실물을 보는 유일한 경로다 — 여기가 비면 "취소를
    호출했다"만 증명되고 "소유권이 실제로 돌아왔다"는 미검증으로 남는다.
    """
    sys.path.insert(0, str(OWNERSHIP_TOOL_DIR))
    from ownership_tool import lease  # RED: lease.handoff 미구현
    from worktree_launcher import launcher_core  # RED: lease_handoff 미구현

    monkeypatch.setenv("OPAL_SESSION_ID", LEASE_HUB_SESSION)
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)

    hub, task_dir = _hub_with_canonical_task(tmp_path)
    claimed = lease.claim(task_dir, session_id=LEASE_HUB_SESSION, claim_source="state_transition")
    assert claimed["ok"] is True, claimed

    report = load_launcher_fixture("fake_process-cwd-mismatch.json", hub.hub, hub.wt_parent)
    adapter = _ClosingAdapter(report)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="claude",
    )

    assert result["detail"] == "reported_cwd_mismatch", result
    _assert_reverted(hub, result)

    # 이관취소가 실제로 성립했음을 반환 로그로 먼저 고정한다 — 이관이 일어나지 않았다면
    # 취소는 `not_handoff_owner`로 거부되므로 `ok: True`가 될 수 없다. 이 단언이 없으면
    # "이관을 아예 하지 않았다"는 구현도 아래 소유자 검사를 통과해 버린다.
    assert result["lease_handoff_cancel"]["ok"] is True, result

    record = json.loads(
        (task_dir / "run" / ".runtime" / "owner.json").read_text(encoding="utf-8")
    )
    assert record["owner_session_id"] == LEASE_HUB_SESSION, record
    # 이관·취소 왕복은 generation을 소비하지 않는다(D-3).
    assert record["generation"] == claimed["generation"], record
    assert record["status"] == "active", record
    assert record.get("handoff_to_worktree_root") is None, record
    assert lease.classify(record, LEASE_HUB_SESSION) == "current_session_owned"


def test_codex_preflight_missing_identity_is_read_only(tmp_path, monkeypatch):
    from worktree_launcher import launcher_core
    monkeypatch.setattr(launcher_core.ownership_core, 'resolve_session_id', lambda env: None)
    hub = build_launcher_hub(tmp_path, prior_state='hub_owned')
    before = hub.meta_path.read_bytes()
    adapter = _FakeAdapter({})
    result = launcher_core.run(adapter, hub_root=hub.hub, task=hub.task,
                               worktree_root=hub.worktree_root, command='codex')
    assert result['error'] == 'session_id_unresolved'
    assert result['cause'] == 'identity_preflight'
    assert adapter.calls == []
    assert hub.meta_path.read_bytes() == before


def test_codex_child_claim_before_launcher_final_uses_child_owner(tmp_path):
    from worktree_launcher import launcher_core
    from ownership_tool import lease
    hub = build_launcher_hub(tmp_path, prior_state='hub_owned')
    task_path = hub.worktree_root / 'tasks' / '220-test'
    task_path.mkdir(parents=True)
    meta = read_meta(hub.meta_path)
    meta['task_path'] = str(task_path)
    hub.meta_path.write_text(json.dumps(meta))
    assert lease.claim(task_path, session_id='hub', claim_source='state_transition')['ok']

    class EarlyChild(_FakeAdapter):
        def launch(self, root, command):
            assert lease.claim(task_path, session_id='child', claim_source='session_start', claimant_root=root)['ok']
            return super().launch(root, command)

    adapter = EarlyChild(load_launcher_fixture('fake_process-success.json', hub.hub, hub.wt_parent))
    result = launcher_core.run(adapter, hub_root=hub.hub, task=hub.task,
                               worktree_root=hub.worktree_root, command='codex', owner_session_id='hub')
    assert result['ok'], result
    assert read_meta(hub.meta_path)['execution_ownership']['owner_session_id'] == 'child'


def test_codex_foreign_live_owner_stops_before_registry_mutation(tmp_path):
    from worktree_launcher import launcher_core
    from ownership_tool import lease
    hub = build_launcher_hub(tmp_path, prior_state='hub_owned')
    task_path = hub.worktree_root / 'tasks/220-foreign'
    task_path.mkdir(parents=True)
    meta = read_meta(hub.meta_path)
    meta['task_path'] = str(task_path)
    hub.meta_path.write_text(json.dumps(meta))
    assert lease.claim(task_path, session_id='other-live-owner', claim_source='state_transition')['ok']
    before = hub.meta_path.read_bytes()
    owner = task_path / 'run/.runtime/owner.json'
    before_owner = owner.read_bytes()
    adapter = _FakeAdapter({})
    result = launcher_core.run(adapter, hub_root=hub.hub, task=hub.task,
                               worktree_root=hub.worktree_root, command='codex', owner_session_id='hub')
    assert result['error'] == 'foreign_session_owned'
    assert adapter.calls == []
    assert hub.meta_path.read_bytes() == before
    assert owner.read_bytes() == before_owner
