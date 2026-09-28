# @header
# module: worktree_launcher.tests.test_task164_preflight
# layer: test
# domain: worktree-launcher
# description: RED-first(task_164) — S-5(Codex/Claude 기동 명령의 `--add-dir` 쓰기 경로 토큰),
#   S-7(기동 전 점검 실패 4원인), S-8(git 쓰기 경고 비차단)을 공개 CLI(`worktree_launcher.cli.main`)
#   와 공개 함수(`worktree_launcher.settings.resolve_command`)로만 검증한다. launcher_core.run은
#   fake seam으로 가로채 실제 orca/lease를 건드리지 않는다(RED — 미구현 preflight는 이 seam이
#   호출됨 자체로 위반이 드러난다).
# exports: (none — pytest module)
# depends: worktree_launcher.cli, worktree_launcher.settings, worktree_launcher.launcher_core, tests/conftest.py
"""RED 테스트 — task_164 S-5, S-7, S-8 (구현 전)."""
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

import pytest

from conftest import build_launcher_hub, read_meta

TOOL_DIR = Path(__file__).resolve().parent.parent


def _single_line_json(captured: str) -> dict:
    lines = [line for line in captured.splitlines() if line.strip()]
    assert len(lines) == 1, f"stdout이 단일 라인이 아니다: {captured!r}"
    payload = json.loads(lines[0])
    assert isinstance(payload, dict)
    return payload


def _invoke(capsys, argv):
    from worktree_launcher import cli

    code = cli.main(argv)
    return code, _single_line_json(capsys.readouterr().out)


def _hub_with_task_path(tmp_path, task="9051"):
    hub = build_launcher_hub(tmp_path, task=task, prior_state="hub_owned", adapter=None)
    meta = read_meta(hub.meta_path)
    task_path = str(hub.worktree_root / "tasks" / f"{task}-demo")
    meta["task_folder"] = f"{task}-demo"
    meta["task_path"] = task_path
    hub.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return hub, task_path


@pytest.fixture
def captured_run(monkeypatch):
    from worktree_launcher import cli

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


def _write_bin(tmp_path, name, script_body):
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir(exist_ok=True)
    path = bin_dir / name
    path.write_text(script_body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir


# ─────────────────────────────────────────────────────────────────────────────
# S-5 — Codex 기본 명령에 태스크 메타 폴더 쓰기 경로가 정확히 1회 포함된다
# ─────────────────────────────────────────────────────────────────────────────


class TestTask164WriteDirToken:
    def test_codex_default_command_includes_add_dir_for_task_meta_folder(
        self, tmp_path, monkeypatch
    ):
        from worktree_launcher import settings

        # 실제 `~/.opal/setting.json`을 격리한다 — 이 머신의 사용자 설정이 결과를
        # 오염시키면 안 된다(D-F 코드 상수 기본값만 본다).
        monkeypatch.setattr(settings, "GLOBAL_SETTING_PATH", tmp_path / "no-such-setting.json")

        loaded = settings.load_launcher_settings()
        resolved = settings.resolve_command(loaded, agent="codex", task_path="/hub/tasks/x")

        assert resolved.count("--add-dir") == 1, (
            f"Task164 S-5: Codex 기본 명령에 --add-dir이 정확히 1회 있어야 한다 — {resolved!r}"
        )

    def test_claude_default_command_is_byte_identical_to_before(self, tmp_path, monkeypatch):
        """Claude 기본 명령은 D-5 변경 이후에도 코드 상수 기본값(DEFAULT_AGENTS)과
        바이트 동일해야 한다(불변 계약 확인용, 이 머신의 사용자 설정과 무관)."""
        from worktree_launcher import settings

        monkeypatch.setattr(settings, "GLOBAL_SETTING_PATH", tmp_path / "no-such-setting.json")

        loaded = settings.load_launcher_settings()
        resolved = settings.resolve_command(loaded, agent="claude", task_path="/hub/tasks/x")
        assert resolved == 'claude "/hub/tasks/x 이어서 수행"'


# ─────────────────────────────────────────────────────────────────────────────
# S-7 — 기동 전 점검 실패 4원인. 실패 시 어댑터 launch·lease 이관이 0회여야 한다.
# ─────────────────────────────────────────────────────────────────────────────


class TestTask164PreflightFailures:
    def test_meta_dir_missing_blocks_before_adapter_launch(
        self, capsys, tmp_path, captured_run
    ):
        """해당 태스크 전용 메타 폴더(`hub.meta_path.parent`)가 통째로 없으면
        `meta_dir_missing`으로 종료하고 어댑터를 한 번도 부르지 않는다. D-1 설계상
        registry가 곧 태스크 메타 폴더 안의 파일이므로, "registry는 있지만 폴더가
        없다"는 상태는 존재할 수 없다 — 폴더 자체를 제거해 재현한다."""
        hub, _task_path = _hub_with_task_path(tmp_path, task="9071")

        meta_root = hub.wt_parent / ".meta"
        task_meta_dir = hub.meta_path.parent

        def _snapshot_excluding(root: Path, excluded: Path) -> dict[str, bytes]:
            if not root.exists():
                return {}
            out = {}
            for p in sorted(root.rglob("*")):
                if not p.is_file():
                    continue
                if p == excluded or excluded in p.parents:
                    continue
                out[str(p.relative_to(root))] = p.read_bytes()
            return out

        # 삭제 대상(태스크 메타 폴더) 바깥의 `.meta/` 상태는 preflight 실패로 바뀌면
        # 안 된다 — 이 부분만 스냅샷해 불변 검사 기준으로 삼는다.
        snapshot_before = _snapshot_excluding(meta_root, task_meta_dir)

        import shutil

        shutil.rmtree(task_meta_dir)

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

        assert code != 0, f"Task164 S-7: meta_dir_missing인데 성공했다 — {payload}"
        assert payload.get("error") == "launch_preflight_failed", (
            f"Task164 S-7: {payload}"
        )
        assert payload.get("cause") == "meta_dir_missing", f"Task164 S-7: {payload}"
        assert captured_run == [], (
            f"Task164 S-7: preflight 실패에도 어댑터/lease 이관이 호출됐다 — {captured_run}"
        )
        assert not task_meta_dir.exists(), (
            "Task164 S-7: preflight 실패가 삭제된 태스크 메타 폴더를 새로 만들었다"
        )
        assert _snapshot_excluding(meta_root, task_meta_dir) == snapshot_before, (
            "Task164 S-7: preflight 실패가 다른 .meta/ 항목의 바이트를 바꿨다"
        )

    def test_meta_dir_not_writable_blocks_before_adapter_launch(
        self, capsys, tmp_path, captured_run
    ):
        hub, _task_path = _hub_with_task_path(tmp_path, task="9072")
        task_meta_dir = hub.meta_path.parent
        task_meta_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(task_meta_dir, 0o500)
        try:
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
        finally:
            os.chmod(task_meta_dir, 0o700)

        assert code != 0, f"Task164 S-7: meta_dir_not_writable인데 성공했다 — {payload}"
        assert payload.get("error") == "launch_preflight_failed", f"Task164 S-7: {payload}"
        assert payload.get("cause") == "meta_dir_not_writable", f"Task164 S-7: {payload}"
        assert captured_run == []

    def test_grant_option_unsupported_blocks_before_adapter_launch(
        self, capsys, tmp_path, captured_run
    ):
        hub, _task_path = _hub_with_task_path(tmp_path, task="9073")
        task_meta_dir = hub.meta_path.parent
        task_meta_dir.mkdir(parents=True, exist_ok=True)

        bin_dir = _write_bin(
            tmp_path,
            "fake_codex_nogrant",
            "#!/bin/sh\necho 'usage: fake_codex_nogrant [--no-daemon]'\nexit 0\n",
        )
        setting_path = hub.hub / ".opal" / "setting.local.json"
        setting_path.parent.mkdir(parents=True, exist_ok=True)
        setting_path.write_text(
            json.dumps(
                {
                    "launcher": {
                        "agents": {
                            "codex": {
                                "argv_template": (
                                    'fake_codex_nogrant --add-dir "{meta_dir}" "{utterance}"'
                                )
                            }
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        env_path = os.environ.get("PATH", "")
        try:
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{env_path}"
            code, payload = _invoke(
                capsys,
                [
                    "launch",
                    "--adapter", "orca",
                    "--agent", "codex",
                    "--project-root", str(hub.hub),
                    "--task", hub.task,
                    "--worktree-root", str(hub.worktree_root),
                ],
            )
        finally:
            os.environ["PATH"] = env_path

        assert code != 0, f"Task164 S-7: grant_option_unsupported인데 성공했다 — {payload}"
        assert payload.get("error") == "launch_preflight_failed", f"Task164 S-7: {payload}"
        assert payload.get("cause") == "grant_option_unsupported", f"Task164 S-7: {payload}"
        assert captured_run == []

    def test_agent_help_unavailable_blocks_before_adapter_launch(
        self, capsys, tmp_path, captured_run
    ):
        hub, _task_path = _hub_with_task_path(tmp_path, task="9074")
        task_meta_dir = hub.meta_path.parent
        task_meta_dir.mkdir(parents=True, exist_ok=True)

        setting_path = hub.hub / ".opal" / "setting.local.json"
        setting_path.parent.mkdir(parents=True, exist_ok=True)
        setting_path.write_text(
            json.dumps(
                {
                    "launcher": {
                        "agents": {
                            "codex": {
                                "argv_template": (
                                    'nonexistent_agent_binary_task164 --add-dir '
                                    '"{meta_dir}" "{utterance}"'
                                )
                            }
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        code, payload = _invoke(
            capsys,
            [
                "launch",
                "--adapter", "orca",
                "--agent", "codex",
                "--project-root", str(hub.hub),
                "--task", hub.task,
                "--worktree-root", str(hub.worktree_root),
            ],
        )

        assert code != 0, f"Task164 S-7: agent_help_unavailable인데 성공했다 — {payload}"
        assert payload.get("error") == "launch_preflight_failed", f"Task164 S-7: {payload}"
        assert payload.get("cause") == "agent_help_unavailable", f"Task164 S-7: {payload}"
        assert captured_run == []


# ─────────────────────────────────────────────────────────────────────────────
# S-8 — 공유 .git 쓰기 불가는 차단이 아니라 경고다
# ─────────────────────────────────────────────────────────────────────────────


class TestTask164GitWriteWarningIsNonBlocking:
    def test_codex_config_continues_with_git_write_warning(
        self, capsys, tmp_path, captured_run
    ):
        hub, _task_path = _hub_with_task_path(tmp_path, task="9081")
        task_meta_dir = hub.meta_path.parent
        task_meta_dir.mkdir(parents=True, exist_ok=True)

        bin_dir = _write_bin(
            tmp_path,
            "fake_codex_ok",
            "#!/bin/sh\necho 'usage: fake_codex_ok [--add-dir PATH]'\nexit 0\n",
        )
        setting_path = hub.hub / ".opal" / "setting.local.json"
        setting_path.parent.mkdir(parents=True, exist_ok=True)
        setting_path.write_text(
            json.dumps(
                {
                    "launcher": {
                        "agents": {
                            "codex": {
                                "argv_template": (
                                    'fake_codex_ok --add-dir "{meta_dir}" "{utterance}"'
                                )
                            }
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        env_path = os.environ.get("PATH", "")
        try:
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{env_path}"
            code, payload = _invoke(
                capsys,
                [
                    "launch",
                    "--adapter", "orca",
                    "--agent", "codex",
                    "--project-root", str(hub.hub),
                    "--task", hub.task,
                    "--worktree-root", str(hub.worktree_root),
                ],
            )
        finally:
            os.environ["PATH"] = env_path

        assert code == 0, f"Task164 S-8: Codex 점검 통과 조건에서 실패했다 — {payload}"
        assert payload.get("ok") is True
        warnings = payload.get("warnings") or []
        assert "git_write_requires_escalation" in warnings, (
            f"Task164 S-8: Codex 응답에 git_write_requires_escalation 경고가 없다 — {payload}"
        )
        assert len(captured_run) == 1, (
            f"Task164 S-8: 경고가 기동을 차단했다(비차단이어야 함) — {captured_run}"
        )

    def test_claude_config_has_no_git_write_warning(self, capsys, tmp_path, captured_run):
        hub, _task_path = _hub_with_task_path(tmp_path, task="9082")
        task_meta_dir = hub.meta_path.parent
        task_meta_dir.mkdir(parents=True, exist_ok=True)

        code, payload = _invoke(
            capsys,
            [
                "launch",
                "--adapter", "orca",
                "--agent", "claude",
                "--project-root", str(hub.hub),
                "--task", hub.task,
                "--worktree-root", str(hub.worktree_root),
            ],
        )

        assert code == 0, f"Task164 S-8: Claude 경로에서 실패했다 — {payload}"
        warnings = payload.get("warnings") or []
        assert "git_write_requires_escalation" not in warnings, (
            f"Task164 S-8: Claude 설정에 경고가 붙었다 — {payload}"
        )
        assert len(captured_run) == 1
