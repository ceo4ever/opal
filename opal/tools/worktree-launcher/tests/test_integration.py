# @header
# module: worktree_launcher.tests.test_integration
# layer: test
# domain: worktree-launcher
# description: W-20 통합 회귀 — 모듈 경계를 가로지르는 실행 경로만 검증한다(PRINCIPLES §2). 기존
#   test_launcher_core.py는 `_FakeAdapter`로 receipt를 직접 주입해 launcher_core.run()의
#   전이 로직만 단위 검증하지만, 여기서는 실제 adapter 모듈(worktree_launcher.adapters.generic/
#   orca)의 launch()·parse_response()가 만든 보고 dict를 launcher_core.run()이 그대로 소비해
#   실 `worktree-tool ownership-set` subprocess를 거쳐 registry 파일을 바꾸는 전체 사슬을
#   재현한다(adapter → launcher_core → ownership-set → registry). 유일하게 대체하는 지점은
#   각 adapter의 최하위 프로세스 실행 seam(`_run_subprocess`)뿐이다 — 실제 터미널을 띄우지
#   않는다는 뜻이지 adapter의 응답 파싱·receipt 조립 로직을 건너뛴다는 뜻이 아니다. 아울러
#   launcher_core.run()을 같은 hub에 두 번 호출하는 재진입 경로(이미 worktree_session_owned인
#   태스크를 다시 launch)도 검증한다 — 기존 단위 테스트는 hub마다 1회만 run()을 호출한다.
#   T1은 실제 ownership-tool lease handoff 뒤 자식 claim을 만들어 registry owner가 같은
#   자식 ID인지, receipt가 registry에서 객체로 보존되는지 함께 집행한다.
# exports: (none — pytest module)
# depends: worktree_launcher.launcher_core, worktree_launcher.adapters.generic,
#   worktree_launcher.adapters.orca, conftest.build_launcher_hub/read_meta,
#   opal/tools/worktree-tool/worktree_tool.py(ownership-set, subprocess 경유·미수정)
"""통합 회귀 — 실 adapter 모듈 + 실 `ownership-set` subprocess + registry 파일을 잇는
경로만 검증한다. 각 테스트가 대체하는 것은 adapter의 최하위 프로세스 실행 seam뿐이다.
T1은 실제 lease handoff·child claim·ownership-set 전이를 함께 통과시킨다."""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

from conftest import build_launcher_hub, read_meta

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ownership-tool"))
from ownership_tool import lease


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class _AdapterModuleWrapper:
    """`worktree_launcher.adapters.<name>` 모듈을 launcher_core.run()이 기대하는
    `adapter.launch(worktree_root, command)` 시그니처로 감싼다. 모듈 함수 자체
    (render_template·parse_response·build_argv 전부)는 그대로 실행되며, 이 래퍼는
    추가 키워드 인자(`template=`)만 주입할 뿐 판정·파싱 로직을 대신하지 않는다."""

    def __init__(self, module, **extra_kwargs):
        self._module = module
        self._extra_kwargs = extra_kwargs
        self.calls: list[tuple] = []

    def launch(self, worktree_root, command):
        self.calls.append((worktree_root, command))
        return self._module.launch(worktree_root, command, **self._extra_kwargs)


class _FakeAdapter:
    """launcher_core.run() 자신의 재진입 가드(같은 hub에 두 번째 run())만을 보려는
    테스트용 대역 — receipt 조립 자체는 T1·T2가 이미 실 adapter로 검증했으므로 여기서는
    adapter 내부를 다시 통과시킬 필요가 없다."""

    def __init__(self, fixture: dict):
        self._fixture = fixture
        self.calls: list[tuple] = []

    def launch(self, worktree_root, command):
        self.calls.append((worktree_root, command))
        return self._fixture


def _canonical_task(hub, *, owner="hub-session"):
    """Give the registry a canonical task and a live hub lease.

    The launcher must consume this issued path for both the public handoff and
    the later `ownership-set --owner-from-lease` subprocess.  Keeping this as
    a real ownership-tool lease makes these source integration tests cover the
    cross-tool transition rather than injecting a launcher-only status dict.
    """
    task_path = hub.worktree_root / "tasks" / "220-integration"
    task_path.mkdir(parents=True)
    meta = read_meta(hub.meta_path)
    meta.update(task_folder=task_path.name, task_path=str(task_path))
    hub.meta_path.write_text(json.dumps(meta), encoding="utf-8")
    assert lease.claim(task_path, session_id=owner, claim_source="state_transition")["ok"]
    return task_path


# ─────────────────────────────────────────────────────────────────────────────
# T1 — generic adapter 실물 launch() → launcher_core.run() → 실 ownership-set
# subprocess → registry 파일. generic.launch()의 template 렌더링·subprocess 실행·
# JSON 응답 파싱(parse_response) 전부가 실행되고, 그 결과 receipt만 launcher_core로
# 넘어간다. 대체 지점은 generic._run_subprocess 하나뿐이다.
# ─────────────────────────────────────────────────────────────────────────────

def test_generic_adapter_real_launch_through_launcher_core_updates_registry(tmp_path, monkeypatch):
    from worktree_launcher import launcher_core
    from worktree_launcher.adapters import generic

    hub = build_launcher_hub(tmp_path, adapter="generic", prior_state="hub_owned", prior_generation=0)
    task_path = _canonical_task(hub)

    recorded = {}

    def fake_run_subprocess(args, **kwargs):
        recorded["args"] = args
        recorded["cwd"] = kwargs.get("cwd")
        # This is the child-side codex-start equivalent: a child may claim only
        # after the real launcher handoff put the lease into handoff_pending.
        claimed = lease.claim(
            task_path,
            session_id="codex-child-001",
            claimant_root=hub.worktree_root,
            claim_source="session_start",
        )
        assert claimed["ok"], claimed
        response = {
            "terminal": {
                "handle": "generic-term-0001",
                "cwd": str(hub.worktree_root),
                "launched_at": _now_iso(),
                "prompt_id": "prompt-0001",
                "submitted_at": _now_iso(),
            }
        }

        class _Completed:
            returncode = 0
            stdout = json.dumps(response)
            stderr = ""

        return _Completed()

    monkeypatch.setattr(generic, "_run_subprocess", fake_run_subprocess)
    adapter = _AdapterModuleWrapper(generic, template="some-term --cwd {cwd} --run {command}")

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="codex",
        owner_session_id="hub-session",
    )

    # adapter seam이 실제로 1회 호출됐고, launcher_core가 넘긴 worktree_root가 그대로
    # generic._run_subprocess의 cwd로 전달됐다(render_template → shlex.split → subprocess 경계).
    assert len(adapter.calls) == 1
    assert adapter.calls[0][0] == hub.worktree_root
    import shlex
    assert shlex.split(adapter.calls[0][1])[-3:] == ["session-launch", "--command", "codex"]
    assert recorded["cwd"] == str(hub.worktree_root)
    assert "--cwd" in recorded["args"] or any(str(hub.worktree_root) in a for a in recorded["args"])

    assert result["ok"] is True
    assert result["status"] == "worktree_session_owned"
    assert result["adapter_handle"] == "generic-term-0001"

    # registry 파일은 launcher_core가 아니라 실 `worktree-tool ownership-set` subprocess가
    # 썼다 — 여기서는 그 결과만 읽는다(사설 writer 금지 계약이 실제로 지켜졌는지 관측).
    data = read_meta(hub.meta_path)
    eo = data["execution_ownership"]
    assert eo["state"] == "worktree_session_owned"
    assert eo["owner_session_id"] == "codex-child-001"
    assert eo["adapter"] == "generic"
    assert eo["adapter_handle"] == "generic-term-0001"
    # registry SSOT 충실도(PLAN W-11) — receipt는 객체여야 한다. 필드는 하드코딩하지 않고
    # launcher_core의 SSOT 상수(LAUNCH_RECEIPT_FIELDS/PROMPT_RECEIPT_FIELDS)로 대조한다.
    # Receipts cross the public ownership-set CLI and remain JSON objects in
    # the registry, so consumers do not need to decode a second time.
    stored_launch_receipt = eo["launch_receipt"]
    stored_prompt_receipt = eo["prompt_receipt"]
    assert isinstance(stored_launch_receipt, dict), (
        f"launch_receipt must be a dict (registry SSOT, PLAN W-11) — "
        f"got {type(stored_launch_receipt).__name__}: {stored_launch_receipt!r}"
    )
    assert isinstance(stored_prompt_receipt, dict), (
        f"prompt_receipt must be a dict (registry SSOT, PLAN W-11) — "
        f"got {type(stored_prompt_receipt).__name__}: {stored_prompt_receipt!r}"
    )
    for field in launcher_core.LAUNCH_RECEIPT_FIELDS:
        assert field in stored_launch_receipt, f"launch_receipt missing field {field!r}"
    for field in launcher_core.PROMPT_RECEIPT_FIELDS:
        assert field in stored_prompt_receipt, f"prompt_receipt missing field {field!r}"
    assert stored_launch_receipt["reported_cwd"] == str(hub.worktree_root)
    assert stored_prompt_receipt["prompt_id"] == "prompt-0001"
    assert "attribution_state" not in data


# ─────────────────────────────────────────────────────────────────────────────
# T2 — orca adapter 실물 launch()가 실패(orca 비-0 종료)를 보고하면 launcher_core가
# 실 ownership-set subprocess로 recovery_required를 기록하는지 확인한다. handle이 없어서
# terminal absence를 입증할 수 없으므로 hub_owned로 추정 복귀하지 않는다.
# ─────────────────────────────────────────────────────────────────────────────

def test_orca_adapter_real_launch_failure_preserves_recovery_state(tmp_path, monkeypatch):
    from worktree_launcher import launcher_core
    from worktree_launcher.adapters import orca

    hub = build_launcher_hub(tmp_path, adapter="orca", prior_state="hub_owned", prior_generation=0)
    task_path = _canonical_task(hub)

    def fake_run_subprocess(argv, **kwargs):
        class _Completed:
            returncode = 1
            stdout = ""
            stderr = "orca: worktree busy"

        return _Completed()

    monkeypatch.setattr(orca, "_run_subprocess", fake_run_subprocess)
    adapter = _AdapterModuleWrapper(orca)

    result = launcher_core.run(
        adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="codex",
        owner_session_id="hub-session",
    )

    assert len(adapter.calls) == 1
    assert adapter.calls[0][0] == hub.worktree_root
    import shlex
    assert shlex.split(adapter.calls[0][1])[-3:] == ["session-launch", "--command", "codex"]
    assert result["ok"] is False
    assert result["failure_reason"] == "launch_failed"

    data = read_meta(hub.meta_path)
    eo = data["execution_ownership"]
    # A launch command can fail before it yields a terminal handle.  The
    # launcher cannot prove absence, so it must retain recovery_required
    # instead of guessing that hub ownership is safe.
    assert eo["state"] == "recovery_required"
    assert eo["failure_reason"] == "launch_failed"
    assert eo["owner_session_id"] is None
    assert eo["terminal_creation"] == "unknown"
    assert eo["launch_receipt"] is None
    assert eo["prompt_receipt"] is None
    # generation은 ownership-set 호출마다 단조 증가한다(worktree_tool.py:1820-1828) —
    # hub_owned(0) → session_launching preflight(1회, generation=1) → launch 실패 →
    # hub_owned 원자 복귀(2회째, generation=2)로 정확히 2회 전이한 결과다.
    assert eo["generation"] == 2
    assert "attribution_state" not in data


# ─────────────────────────────────────────────────────────────────────────────
# T3 — 같은 hub에 launcher_core.run()을 두 번 호출하는 재진입 경로. 첫 호출이
# worktree_session_owned로 성공한 뒤, 두 번째 호출은 어떤 adapter도 launch()를 호출하지
# 않고 ownership_not_launchable로 거부되며 registry는 첫 호출의 최종 상태에서 바뀌지
# 않는다(dual owner 금지 가드가 registry 재조회만으로 판정됨을 확인 — 기존 단위 테스트는
# hub마다 run()을 1회만 호출해 이 재진입 자체를 검증하지 않는다).
# ─────────────────────────────────────────────────────────────────────────────

def test_second_run_on_child_owned_hub_is_rejected_without_touching_adapter(tmp_path):
    from conftest import load_launcher_fixture
    from worktree_launcher import launcher_core

    hub = build_launcher_hub(tmp_path, adapter="generic", prior_state="hub_owned", prior_generation=0)
    task_path = _canonical_task(hub)
    fixture = load_launcher_fixture("fake_process-success.json", hub.hub, hub.wt_parent)

    class _ClaimingAdapter(_FakeAdapter):
        def launch(self, worktree_root, command):
            claimed = lease.claim(
                task_path,
                session_id="codex-child-002",
                claimant_root=hub.worktree_root,
                claim_source="session_start",
            )
            assert claimed["ok"], claimed
            return super().launch(worktree_root, command)

    first_adapter = _ClaimingAdapter(fixture)

    first_result = launcher_core.run(
        first_adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="codex",
        owner_session_id="hub-session",
    )
    assert first_result["ok"] is True
    assert first_result["status"] == "worktree_session_owned"
    data_after_first = read_meta(hub.meta_path)

    second_adapter = _FakeAdapter(fixture)
    second_result = launcher_core.run(
        second_adapter,
        hub_root=hub.hub,
        task=hub.task,
        worktree_root=hub.worktree_root,
        command="codex",
        owner_session_id="hub-session",
    )

    # 두 번째 호출은 adapter.launch()를 아예 부르지 않는다 — hub_owned/session_launching
    # 둘 다 아니므로 launch 이전 가드에서 거부된다.
    assert second_adapter.calls == []
    assert second_result["ok"] is False
    assert second_result["error"] == "foreign_session_owned"

    data_after_second = read_meta(hub.meta_path)
    assert data_after_second == data_after_first
