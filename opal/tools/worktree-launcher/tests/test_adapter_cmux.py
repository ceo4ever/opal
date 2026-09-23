# @header
# module: worktree_launcher.tests.test_adapter_cmux
# layer: test
# domain: worktree-launcher
# description: RED-first S-3 — cmux launch/read/close argv, receipt schema, strict workspace-handle parsing, structured failures, and zero fallback. S-4는 이 모듈에서 유일하게 실제 cmux를 호출하는 live 대조 1건이다 — `OPAL_LIVE_CMUX=1`이고 cmux가 PATH에 있을 때만 돌고(그 외 skip), launch 전 workspace 목록 스냅샷과 비교해 새로 생긴 ref만 회수한다.
# exports: (none — pytest module)
# depends: worktree_launcher.adapters.cmux, worktree_launcher.launcher_core, cmux CLI(live 대조 S-4 한정)
"""cmux adapter public contract tests (RED-first, S-3; opt-in live S-4)."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest


class _Completed:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _stub_run(recorded, *, returncode=0, stdout="", stderr=""):
    def fake_run(argv, **kwargs):
        recorded.append([str(token) for token in argv])
        return _Completed(returncode, stdout, stderr)

    return fake_run


def test_launch_builds_one_workspace_and_complete_receipts(monkeypatch, tmp_path):
    from worktree_launcher import launcher_core
    from worktree_launcher.adapters import cmux

    worktree = tmp_path / "task_152"
    worktree.mkdir()
    command = 'codex "태스크 이어서 수행"'
    calls = []
    monkeypatch.setattr(
        cmux,
        "_run_subprocess",
        _stub_run(calls, stdout="OK workspace:42\n"),
    )

    report = cmux.launch(worktree, command)

    assert calls == [[
        "cmux", "new-workspace", "--name", "task_152",
        "--cwd", str(worktree), "--command", command, "--focus", "true",
    ]]
    assert report["adapter"] == "cmux"
    assert report["adapter_handle"] == "workspace:42"
    assert report["reported_cwd"] == str(worktree)
    assert report["prompt_id"] == hashlib.sha256(command.encode()).hexdigest()[:16]
    assert report["prompt_receipt_source"] == "launch_argv"
    assert report["fallback_attempted"] is False
    assert launcher_core.build_launch_receipt(report) is not None
    assert launcher_core.build_prompt_receipt(report) is not None


def test_read_uses_workspace_handle_and_bounded_lines(monkeypatch):
    from worktree_launcher.adapters import cmux

    calls = []
    monkeypatch.setattr(
        cmux,
        "_run_subprocess",
        _stub_run(calls, stdout="line one\nline two\n"),
    )

    report = cmux.read("workspace:42", limit=20)

    assert calls == [["cmux", "read-screen", "--workspace", "workspace:42", "--lines", "20"]]
    assert report == {
        "adapter": "cmux",
        "exit_code": 0,
        "fallback_attempted": False,
        "handle": "workspace:42",
        "content": "line one\nline two",
        "next_cursor": None,
        "source": "screen",
    }


def test_close_only_the_explicit_workspace_handle(monkeypatch):
    from worktree_launcher.adapters import cmux

    calls = []
    monkeypatch.setattr(cmux, "_run_subprocess", _stub_run(calls, stdout="OK workspace:42\n"))

    report = cmux.close(handle="workspace:42")

    assert calls == [["cmux", "close-workspace", "--workspace", "workspace:42"]]
    assert report["exit_code"] == 0
    assert report["scope"] == "terminal"
    assert report["closed"] == ["workspace:42"]
    assert report["fallback_attempted"] is False


def test_worktree_wide_close_is_rejected_without_guessing(monkeypatch, tmp_path):
    from worktree_launcher.adapters import cmux

    calls = []
    monkeypatch.setattr(cmux, "_run_subprocess", _stub_run(calls, stdout="OK workspace:42\n"))

    report = cmux.close(worktree_root=tmp_path, all=True)

    assert calls == []
    assert report["exit_code"] != 0
    assert report["failure_reason"] == "close_scope_unsupported"
    assert report["fallback_attempted"] is False


def test_launch_rejects_empty_or_ambiguous_workspace_refs(monkeypatch, tmp_path):
    from worktree_launcher.adapters import cmux

    for stdout in ("", "workspace:1\n", "OK workspace:1\nOK workspace:2\n"):
        calls = []
        monkeypatch.setattr(cmux, "_run_subprocess", _stub_run(calls, stdout=stdout))

        report = cmux.launch(tmp_path, "codex")

        assert report["exit_code"] != 0
        assert report["failure_reason"] == "launch_failed"
        assert "response_unparsable" in report["detail"]
        assert report["fallback_attempted"] is False


def test_nonzero_cmux_exit_is_structured_and_never_falls_back(monkeypatch, tmp_path):
    from worktree_launcher.adapters import cmux

    calls = []
    monkeypatch.setattr(
        cmux,
        "_run_subprocess",
        _stub_run(calls, returncode=7, stderr="cmux rejected request"),
    )

    report = cmux.launch(tmp_path, "codex")

    assert report["adapter"] == "cmux"
    assert report["exit_code"] == 7
    assert report["failure_reason"] == "launch_failed"
    assert report["detail"] == "cmux rejected request"
    assert report["fallback_attempted"] is False


# ─────────────────────────────────────────────────────────────────────────────
# S-4 — live 대조 (opt-in). 실제 cmux를 호출하는 이 모듈의 유일한 테스트다.
#   fixture는 캡처 시점(`OK workspace:<n>`) 응답만 고정하므로 이후 CLI 드리프트(H-2)는 여기서만 관측된다.
# ─────────────────────────────────────────────────────────────────────────────

LIVE_ENV = "OPAL_LIVE_CMUX"
LIVE_MARKER_OK = "OPAL-LIVE-CMUX-S4-CWD-OK"
LIVE_MARKER_BAD = "OPAL-LIVE-CMUX-S4-CWD-MISMATCH"
LIVE_READ_LINES = 20
LIVE_POLL_SEC = 15
LIVE_TIMEOUT_SEC = 30
WORKSPACE_TOKEN = re.compile(r"\bworkspace:[1-9][0-9]*\b")

live_cmux = pytest.mark.skipif(
    os.environ.get(LIVE_ENV) != "1" or shutil.which("cmux") is None,
    reason=f"live 대조는 {LIVE_ENV}=1이고 cmux가 PATH에 있을 때만 실행한다(S-4 실행 조건)",
)


def _live_command(worktree: Path) -> str:
    """cwd 일치를 셸 안에서 판정하고 결과 마커만 찍은 뒤 close까지 살아 있는 무해한 명령.

    cmux는 `--command`를 프롬프트에 타이핑해 에코하므로, 마커는 `printf` 인자 둘로 쪼개
    명령 에코 줄에는 나타나지 않고 실제 출력 줄에만 이어진 형태로 나타나게 한다.
    """
    expected = os.path.realpath(worktree)
    return (
        f"if [ \"$(pwd -P)\" = '{expected}' ]; "
        "then printf '%s-%s\\n' OPAL-LIVE-CMUX-S4 CWD-OK; "
        "else printf '%s-%s\\n' OPAL-LIVE-CMUX-S4 CWD-MISMATCH; fi; sleep 120"
    )


def _live_refs_named(name: str) -> set[str]:
    """`cmux workspace list`에서 제목이 정확히 `name`인 workspace ref만 고른다.

    ref 집합 diff는 생성 직후 목록 반영 지연 때문에 누수를 놓치므로(S-4 실측), 실행마다
    고유한 이름으로 이 테스트가 만든 workspace만 식별한다.
    """
    completed = subprocess.run(
        ["cmux", "workspace", "list"],
        capture_output=True,
        text=True,
        timeout=LIVE_TIMEOUT_SEC,
        env={**os.environ, "CMUX_QUIET": "1"},
    )
    assert completed.returncode == 0, f"cmux workspace list 실패: {completed.stderr.strip()}"
    refs = set()
    for line in completed.stdout.splitlines():
        tokens = line.replace("*", " ").split()
        if len(tokens) >= 2 and WORKSPACE_TOKEN.fullmatch(tokens[0]) and name in tokens[1:]:
            refs.add(tokens[0])
    return refs


def _poll_refs_named(name: str, until) -> set[str]:
    deadline = time.monotonic() + LIVE_POLL_SEC
    refs = _live_refs_named(name)
    while not until(refs) and time.monotonic() < deadline:
        time.sleep(0.5)
        refs = _live_refs_named(name)
    return refs


@live_cmux
def test_live_cmux_launch_read_close_leaves_no_workspace(tmp_path):
    """실 `cmux new-workspace` stdout이 handle로 파싱되고, 그 workspace가 요청한 cwd에서
    command를 실행하며, read가 유계 출력을 돌려주고, 같은 handle close 뒤 잔존 0개다(S-4).

    teardown은 단언 실패·파싱 실패에서도 돌아야 하므로 `finally`에서 이 실행의 고유 이름을
    가진 workspace만 닫는다 — 사용자의 기존 workspace는 건드리지 않는다.
    """
    from worktree_launcher.adapters import cmux

    name = f"opal-live-cmux-s4-{os.getpid()}-{time.monotonic_ns()}"
    worktree = tmp_path / name
    worktree.mkdir()
    handle = None
    close_report = None
    leaked = set()
    try:
        report = cmux.launch(worktree, _live_command(worktree))
        assert report["exit_code"] == 0, f"cmux launch 실패(H-2 드리프트 의심): {report}"
        handle = report["adapter_handle"]
        created = _poll_refs_named(name, lambda refs: bool(refs))
        assert created == {handle}, f"새 workspace가 handle 하나가 아니다: {created} vs {handle}"
        assert report["reported_cwd"] == str(worktree)

        content = ""
        deadline = time.monotonic() + LIVE_POLL_SEC
        while time.monotonic() < deadline:
            read_report = cmux.read(handle, limit=LIVE_READ_LINES)
            assert read_report["exit_code"] == 0, f"cmux read 실패: {read_report}"
            content = read_report["content"]
            if LIVE_MARKER_OK in content or LIVE_MARKER_BAD in content:
                break
            time.sleep(0.5)
        assert LIVE_MARKER_BAD not in content, f"workspace cwd가 요청 경로와 다르다: {content!r}"
        assert LIVE_MARKER_OK in content, f"command 출력이 화면에 없다: {content!r}"
        assert len(content.splitlines()) <= LIVE_READ_LINES
    finally:
        if handle is not None:
            close_report = cmux.close(handle=handle)
        # close도 비동기로 반영되므로 사라질 때까지 기다린 뒤 남은 것만 회수한다.
        leaked = _poll_refs_named(name, lambda refs: not refs)
        for ref in leaked:
            cmux.close(handle=ref)

    assert close_report is not None, "handle을 얻지 못해 회수 대상이 없다"
    assert close_report["exit_code"] == 0, f"workspace 회수 실패: {close_report}"
    assert close_report["closed"] == [handle]
    assert leaked == set(), f"close 뒤 남은 workspace: {leaked}"
