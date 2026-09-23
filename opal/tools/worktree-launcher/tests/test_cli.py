# @header
# module: worktree_launcher.tests.test_cli
# layer: test
# domain: worktree-launcher
# description: RED-first — CLI 표면(`worktree_launcher.cli`)과 `run.sh` 위임의 공개 계약 검증 (S-5). 인자 조합 4종(`--adapter` 누락 / `--adapter cmux` 미구현 / `--adapter orca` 정상 / `--command` 미지정)에 대해 폐쇄 목록 밖 어댑터 거부·자동 폴백 0건, 단일 라인 JSON + exit 0/1, `--command` 미지정 시 `resolve_command()` 결정, `close` 인자 배타성, `run.sh`의 `not_implemented` 제거와 venv·import 가드 2종 유지를 고정한다. 실제 orca는 호출하지 않는다 — `launcher_core.run`과 adapter 3동사를 monkeypatch로 대체하고 registry는 tests/conftest의 tmp 허브를 쓴다.
# exports: (none — pytest module)
# depends: worktree_launcher.cli, worktree_launcher.launcher_core, worktree_launcher.settings, worktree_launcher.adapters.orca, tests/conftest.py
"""RED 테스트 — 구현 전(S-5)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from conftest import build_launcher_hub, read_meta

TOOL_DIR = Path(__file__).resolve().parent.parent
RUN_SH = TOOL_DIR / "run.sh"

# 서브명령별 유효 인자 집합 — `--adapter` 판정에 다른 인자의 유효성이 섞이지 않게 한다.
SUBCOMMAND_ARGS = {
    "launch": ["--project-root", "/tmp/hub", "--task", "220", "--worktree-root", "/tmp/wt"],
    "read": ["--terminal", "t-1"],
    "close": ["--terminal", "t-1"],
}
SUBCOMMANDS = tuple(SUBCOMMAND_ARGS)


def _single_line_json(captured: str) -> dict:
    """stdout은 **단일 라인 JSON 객체 하나**여야 한다(tool-output-contract)."""
    lines = [line for line in captured.splitlines() if line.strip()]
    assert len(lines) == 1, f"stdout이 단일 라인이 아니다: {captured!r}"
    payload = json.loads(lines[0])
    assert isinstance(payload, dict)
    return payload


def _invoke(capsys, argv):
    from worktree_launcher import cli  # RED

    code = cli.main(argv)
    return code, _single_line_json(capsys.readouterr().out)


def _hub_with_task_path(tmp_path, task="220", prior_state="hub_owned"):
    """conftest 허브의 canonical `task_path`를 채워 돌려준다(create 발급값 자리)."""
    hub = build_launcher_hub(tmp_path, task=task, prior_state=prior_state, adapter=None)
    meta = read_meta(hub.meta_path)
    task_path = str(hub.worktree_root / "tasks" / f"{task}-demo")
    meta["task_folder"] = f"{task}-demo"
    meta["task_path"] = task_path
    hub.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return hub, task_path


# ─────────────────────────────────────────────────────────────────────────────
# 어댑터 명시 주입 (AC-1) — 누락·폐쇄 목록 밖 값은 거부하고 자동 폴백을 하지 않는다
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("sub", SUBCOMMANDS)
def test_adapter_missing_is_rejected(capsys, sub):
    """`--adapter` 누락은 전 서브명령에서 구조화 오류 + exit 1이다."""
    code, payload = _invoke(capsys, [sub, *SUBCOMMAND_ARGS[sub]])

    assert code == 1
    assert payload["ok"] is False
    assert payload["error"] == "adapter_required"


@pytest.mark.parametrize("sub", SUBCOMMANDS)
def test_adapter_outside_closed_list_is_rejected(capsys, sub):
    """미구현 어댑터는 폐쇄 목록 밖이므로 거부하고 자동 폴백하지 않는다."""
    code, payload = _invoke(capsys, [sub, "--adapter", "unsupported", *SUBCOMMAND_ARGS[sub]])

    assert code == 1
    assert payload["ok"] is False
    assert payload["error"] == "adapter_unsupported"
    assert payload["adapter"] == "unsupported"
    # 폐쇄 목록은 응답이 스스로 밝힌다. 자동 탐지·자동 폴백 0건.
    assert payload["supported"] == ["orca", "cmux"]
    assert payload.get("fallback_attempted") is False


def test_closed_adapter_list_contains_orca_and_cmux():
    from worktree_launcher import cli  # RED

    assert list(cli.SUPPORTED_ADAPTERS) == ["orca", "cmux"]


# ─────────────────────────────────────────────────────────────────────────────
# launch — 정상 경로와 `--command` 결정
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def captured_run(monkeypatch):
    """`launcher_core.run` 호출 인자를 가로채는 seam — 실제 orca·registry 전이는 없다."""
    from worktree_launcher import cli  # RED

    calls = []

    def fake_run(adapter, **kwargs):
        calls.append({"adapter": adapter, **kwargs})
        return {
            "ok": True,
            "status": "worktree_session_owned",
            "failure_reason": None,
            "task": kwargs.get("task"),
            "adapter": "orca",
            "adapter_handle": "term-1",
        }

    monkeypatch.setattr(cli.launcher_core, "run", fake_run)
    return calls


def test_launch_orca_success_emits_single_line_json(capsys, tmp_path, captured_run):
    from worktree_launcher.adapters import orca  # RED

    hub, _ = _hub_with_task_path(tmp_path)

    code, payload = _invoke(
        capsys,
        [
            "launch",
            "--adapter", "orca",
            "--project-root", str(hub.hub),
            "--task", hub.task,
            "--worktree-root", str(hub.worktree_root),
            "--owner-session-id", "session-cli",
        ],
    )

    assert code == 0
    assert payload["ok"] is True
    assert payload["command"] == "launch"
    assert payload["status"] == "worktree_session_owned"

    assert len(captured_run) == 1
    call = captured_run[0]
    # 명시 주입된 어댑터 모듈 그 자체가 코어에 전달된다(추측·탐지 없음).
    assert call["adapter"] is orca
    assert call["owner_session_id"] == "session-cli"
    assert str(call["worktree_root"]) == str(hub.worktree_root)


def test_launch_without_command_resolves_from_settings(capsys, tmp_path, captured_run):
    """`--command` 미지정이면 W-2의 `resolve_command()`가 registry canonical
    `task_path`로 명령을 결정한다."""
    from worktree_launcher import settings  # RED

    hub, task_path = _hub_with_task_path(tmp_path)

    code, _ = _invoke(
        capsys,
        [
            "launch",
            "--adapter", "orca",
            "--project-root", str(hub.hub),
            "--task", hub.task,
            "--worktree-root", str(hub.worktree_root),
        ],
    )

    assert code == 0
    expected = settings.resolve_command(
        settings.load_launcher_settings(project_root=str(hub.hub)),
        agent=None,
        task_path=task_path,
    )
    assert captured_run[0]["command"] == expected
    assert task_path in captured_run[0]["command"]


def test_launch_agent_selects_argv_template(capsys, tmp_path, captured_run):
    """`--agent`가 설정의 `default`를 이긴다."""
    from worktree_launcher import settings  # RED

    hub, task_path = _hub_with_task_path(tmp_path)

    code, _ = _invoke(
        capsys,
        [
            "launch",
            "--adapter", "orca",
            "--project-root", str(hub.hub),
            "--task", hub.task,
            "--worktree-root", str(hub.worktree_root),
            "--agent", "codex",
        ],
    )

    assert code == 0
    assert captured_run[0]["command"] == settings.resolve_command(
        settings.load_launcher_settings(project_root=str(hub.hub)),
        agent="codex",
        task_path=task_path,
    )


def test_launch_explicit_command_is_passed_verbatim(capsys, tmp_path, captured_run):
    hub, _ = _hub_with_task_path(tmp_path)

    code, _ = _invoke(
        capsys,
        [
            "launch",
            "--adapter", "orca",
            "--project-root", str(hub.hub),
            "--task", hub.task,
            "--worktree-root", str(hub.worktree_root),
            "--command", "claude \"이어서\"",
        ],
    )

    assert code == 0
    assert captured_run[0]["command"] == 'claude "이어서"'


def test_launch_without_task_path_refuses_instead_of_guessing(capsys, tmp_path, captured_run):
    """registry에서 canonical `task_path`를 얻지 못하면 `--worktree-root`로 대신하지 않고
    구조화 오류로 거부한다(harness/worktree.md §canonical path 발급 계약)."""
    hub = build_launcher_hub(tmp_path, task="221", prior_state="hub_owned", adapter=None)
    # conftest 기본 메타는 `task_path: None`이다 — 추측 금지 경로.

    code, payload = _invoke(
        capsys,
        [
            "launch",
            "--adapter", "orca",
            "--project-root", str(hub.hub),
            "--task", hub.task,
            "--worktree-root", str(hub.worktree_root),
        ],
    )

    assert code == 1
    assert payload["ok"] is False
    assert payload["error"] == "task_path_unresolved"
    assert captured_run == []


def test_launch_failure_report_exits_one(capsys, tmp_path, monkeypatch):
    from worktree_launcher import cli  # RED

    hub, _ = _hub_with_task_path(tmp_path)
    monkeypatch.setattr(
        cli.launcher_core,
        "run",
        lambda adapter, **kw: {
            "ok": False,
            "status": "hub_owned",
            "failure_reason": "launch_failed",
            "detail": "launch_receipt_missing",
        },
    )

    code, payload = _invoke(
        capsys,
        [
            "launch",
            "--adapter", "orca",
            "--project-root", str(hub.hub),
            "--task", hub.task,
            "--worktree-root", str(hub.worktree_root),
            "--command", "true",
        ],
    )

    assert code == 1
    assert payload["ok"] is False
    assert payload["error"]  # 실패 응답은 안정적인 코드 식별자를 갖는다
    assert payload["failure_reason"] == "launch_failed"


def test_launch_registry_unreadable_is_structured_error(capsys, tmp_path):
    code, payload = _invoke(
        capsys,
        [
            "launch",
            "--adapter", "orca",
            "--project-root", str(tmp_path / "no-hub"),
            "--task", "999",
            "--worktree-root", str(tmp_path / "no-hub" / "wt"),
        ],
    )

    assert code == 1
    assert payload["ok"] is False
    assert payload["error"] == "registry_unreadable"


# ─────────────────────────────────────────────────────────────────────────────
# read
# ─────────────────────────────────────────────────────────────────────────────


def test_read_passes_options_and_exits_zero(capsys, monkeypatch):
    from worktree_launcher.adapters import orca  # RED

    calls = []

    def fake_read(handle, *, cursor=None, limit=None, screen=False):
        calls.append((handle, cursor, limit, screen))
        return {
            "adapter": "orca",
            "exit_code": 0,
            "fallback_attempted": False,
            "handle": handle,
            "content": "hello",
            "next_cursor": 42,
            "source": "tail",
        }

    monkeypatch.setattr(orca, "read", fake_read)

    code, payload = _invoke(
        capsys,
        ["read", "--adapter", "orca", "--terminal", "t-9", "--cursor", "7", "--limit", "20", "--screen"],
    )

    assert code == 0
    assert payload["ok"] is True
    assert payload["command"] == "read"
    assert payload["content"] == "hello"
    assert calls == [("t-9", 7, 20, True)]


def test_read_failure_exits_one(capsys, monkeypatch):
    from worktree_launcher.adapters import orca  # RED

    monkeypatch.setattr(
        orca,
        "read",
        lambda handle, **kw: {
            "adapter": "orca",
            "exit_code": 127,
            "failure_reason": "read_failed",
            "detail": "orca_unavailable",
            "fallback_attempted": False,
        },
    )

    code, payload = _invoke(capsys, ["read", "--adapter", "orca", "--terminal", "t-9"])

    assert code == 1
    assert payload["ok"] is False
    assert payload["error"] == "read_failed"
    assert payload["fallback_attempted"] is False


def test_read_requires_terminal(capsys):
    code, payload = _invoke(capsys, ["read", "--adapter", "orca"])

    assert code == 1
    assert payload["ok"] is False
    assert payload["error"] == "terminal_required"


# ─────────────────────────────────────────────────────────────────────────────
# close — 스코프 배타성
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def captured_close(monkeypatch):
    from worktree_launcher.adapters import orca  # RED

    calls = []

    def fake_close(*, handle=None, worktree_root=None, all=False):
        calls.append({"handle": handle, "worktree_root": worktree_root, "all": all})
        return {
            "adapter": "orca",
            "exit_code": 0,
            "fallback_attempted": False,
            "scope": "terminal" if handle else "worktree_all",
            "closed": [handle] if handle else ["t-1", "t-2"],
        }

    monkeypatch.setattr(orca, "close", fake_close)
    return calls


def test_close_terminal_scope(capsys, captured_close):
    code, payload = _invoke(capsys, ["close", "--adapter", "orca", "--terminal", "t-1"])

    assert code == 0
    assert payload["ok"] is True
    assert payload["command"] == "close"
    assert captured_close == [{"handle": "t-1", "worktree_root": None, "all": False}]


def test_close_worktree_all_scope_accepts_json_flag(capsys, tmp_path, captured_close):
    """worktree-tool의 회수 스윕이 그대로 쓰는 호출 형태다(`--json` 포함)."""
    root = tmp_path / "wt"

    code, payload = _invoke(
        capsys,
        ["close", "--adapter", "orca", "--worktree-root", str(root), "--all", "--json"],
    )

    assert code == 0
    assert payload["ok"] is True
    assert captured_close == [{"handle": None, "worktree_root": str(root), "all": True}]


@pytest.mark.parametrize(
    "extra",
    [
        [],  # 둘 다 없음
        ["--terminal", "t-1", "--worktree-root", "/tmp/wt", "--all"],  # 둘 다
        ["--worktree-root", "/tmp/wt"],  # --all 없음
        ["--terminal", "t-1", "--all"],  # handle + --all
    ],
)
def test_close_scope_must_be_exactly_one(capsys, captured_close, extra):
    code, payload = _invoke(capsys, ["close", "--adapter", "orca", *extra])

    assert code == 1
    assert payload["ok"] is False
    assert payload["error"] == "close_scope_invalid"
    assert captured_close == []  # adapter를 호출하지도 않는다


# ─────────────────────────────────────────────────────────────────────────────
# run.sh 위임 (AC-3) — not_implemented 0건, 가드 2종 유지
# ─────────────────────────────────────────────────────────────────────────────


def test_run_sh_has_no_not_implemented_and_keeps_guards():
    text = RUN_SH.read_text(encoding="utf-8")

    assert "not_implemented" not in text
    assert "venv_missing" in text
    assert "package_import_failed" in text
    assert '-m worktree_launcher.cli "$@"' in text


def test_run_sh_delegates_to_cli():
    """실제 run.sh 실행이 CLI 구조화 오류를 단일 라인 JSON으로 돌려준다."""
    result = subprocess.run(
        [str(RUN_SH), "close", "--adapter", "unsupported", "--terminal", "t-1"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout.strip())
    assert payload["error"] == "adapter_unsupported"
