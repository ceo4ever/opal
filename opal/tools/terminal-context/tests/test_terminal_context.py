# @header
# module: terminal_context.tests.test_terminal_context
# layer: test
# domain: terminal-context
# description: RED-first S-1 — current-process evidence only, closed four-key output, host precedence, tmux nesting, and secret-value redaction.
# exports: (none — pytest module)
# depends: terminal_context.py
"""Terminal context detector public contract tests (RED-first, S-1)."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


TOOL_DIR = Path(__file__).resolve().parent.parent
MODULE_PATH = TOOL_DIR / "terminal_context.py"
RUN_SH = TOOL_DIR / "run.sh"
OUTPUT_KEYS = {"host", "multiplexers", "confidence", "evidence"}


@pytest.fixture
def detector():
    """Load the source module by path because the deployed tool directory is hyphenated."""
    spec = importlib.util.spec_from_file_location("terminal_context_under_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _detect(detector, *, env=None, direct=(), tmux_client=()):
    """The fixture seams are explicit inputs; tests never inspect global processes."""
    return detector.detect_context(
        env=dict(env or {}),
        direct_ancestors=list(direct),
        tmux_client_ancestors=list(tmux_client),
    )


def _assert_closed_schema(result):
    assert set(result) == OUTPUT_KEYS
    assert isinstance(result["host"], str)
    assert isinstance(result["multiplexers"], list)
    assert result["confidence"] in {"high", "medium", "low"}
    assert isinstance(result["evidence"], list)


@pytest.mark.parametrize(
    ("env", "direct", "tmux_client", "expected_host", "expected_confidence"),
    [
        ({"OPAL_TERMINAL_HOST": "cmux", "TERM_PROGRAM": "Apple_Terminal"}, (), (), "cmux", "high"),
        ({"CMUX_SURFACE_ID": "surface:secret"}, ("/Applications/Orca.app/Contents/MacOS/Orca",), (), "cmux", "high"),
        ({"TERM_PROGRAM": "Apple_Terminal"}, ("/Applications/Orca.app/Contents/MacOS/Orca",), (), "orca", "high"),
        ({"TMUX": "/private/tmp/tmux-secret"}, ("tmux: server",), ("/Applications/cmux.app/Contents/MacOS/cmux",), "cmux", "high"),
        ({"TERM_PROGRAM": "iTerm.app"}, (), (), "iterm2", "medium"),
        ({}, (), (), "unknown", "low"),
    ],
)
def test_host_precedence_and_closed_schema(
    detector, env, direct, tmux_client, expected_host, expected_confidence
):
    result = _detect(detector, env=env, direct=direct, tmux_client=tmux_client)

    _assert_closed_schema(result)
    assert result["host"] == expected_host
    assert result["confidence"] == expected_confidence


def test_tmux_is_reported_as_a_layer_and_never_replaces_host(detector):
    result = _detect(
        detector,
        env={"TMUX": "/private/tmp/tmux-501/default,1,0"},
        direct=("tmux: server",),
        tmux_client=("/Applications/Orca.app/Contents/MacOS/Orca",),
    )

    assert result["host"] == "orca"
    assert result["multiplexers"] == ["tmux"]


def test_evidence_contains_signal_names_but_no_raw_secret_values(detector):
    secrets = {
        "CMUX_SURFACE_ID": "surface-super-secret",
        "TMUX": "/private/tmp/private-socket-token",
    }
    result = _detect(detector, env=secrets)
    serialized = json.dumps(result, ensure_ascii=False)

    _assert_closed_schema(result)
    assert "CMUX_SURFACE_ID" in serialized
    for secret in secrets.values():
        assert secret not in serialized


def test_unrelated_installed_or_running_apps_are_not_detector_inputs(detector):
    """No installed/running-app inventory seam exists; identical process evidence is stable."""
    first = _detect(detector, env={"TERM_PROGRAM": "Apple_Terminal"})
    second = _detect(detector, env={"TERM_PROGRAM": "Apple_Terminal"})

    assert first == second
    assert first["host"] == "apple-terminal"


def test_public_cli_emits_one_line_exact_four_key_json():
    completed = subprocess.run(
        [str(RUN_SH)],
        env={"PATH": "/usr/bin:/bin", "OPAL_TERMINAL_HOST": "cmux"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    assert len(lines) == 1
    _assert_closed_schema(json.loads(lines[0]))


def test_ancestor_arguments_never_decide_host(detector, monkeypatch):
    """A parent's argv (e.g. a user prompt mentioning cmux) must not override the real host executable."""
    tree = {
        200: (100, "claude", "claude --permission-mode auto cmux 어댑터 봐줘"),
        100: (50, "-/bin/zsh", "-/bin/zsh -l"),
        50: (1, "/Applications/Orca.app/Contents/Frameworks/Orca Helper.app/Contents/MacOS/Orca Helper",
             "/Applications/Orca.app/Contents/Frameworks/Orca Helper.app/Contents/MacOS/Orca Helper --type=pty"),
    }

    def fake_ps(argv):
        pid = int(argv[argv.index("-p") + 1])
        if pid not in tree:
            return subprocess.CompletedProcess(argv, 1, "", "")
        ppid, comm, command = tree[pid]
        column = command if "command=" in argv else comm
        return subprocess.CompletedProcess(argv, 0, f"{ppid} {column}\n", "")

    monkeypatch.setattr(detector, "_run_process", fake_ps)
    monkeypatch.setattr(detector.os, "getppid", lambda: 200)

    result = detector.detect_context(env={})

    assert result["host"] == "orca"
    assert result["evidence"] == ["ancestor:orca"]
    assert result["multiplexers"] == []
