"""
@header {
  "module": "worktree_launcher.adapters.cmux",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "cmux workspace adapter로 기존 OPAL worktree의 launch, bounded screen read, explicit-handle close를 제공한다.",
  "exports": ["ADAPTER_NAME", "build_argv", "build_read_argv", "build_close_argv", "launch", "read", "close"],
  "depends": ["cmux CLI(new-workspace, read-screen, close-workspace)"]
}
"""

from __future__ import annotations

import datetime
import hashlib
import os
import re
import subprocess

ADAPTER_NAME = "cmux"
name = ADAPTER_NAME
CMUX_BIN = "cmux"
CMUX_TIMEOUT_SECONDS = 120
DEFAULT_READ_LINES = 200
LAUNCH_MODE = "cmux_new_workspace"
PROMPT_SOURCE = "launch_argv"
CLOSE_SCOPE_TERMINAL = "terminal"
EXIT_CMUX_UNAVAILABLE = 127
EXIT_RESPONSE_UNPARSABLE = 65
EXIT_INVALID_ARGUMENTS = 64
FAILURE_REASON_LAUNCH = "launch_failed"
FAILURE_REASON_READ = "read_failed"
FAILURE_REASON_CLOSE = "close_failed"
FAILURE_REASON_CLOSE_SCOPE_UNSUPPORTED = "close_scope_unsupported"
# 실측 cmux 응답은 `OK workspace:<n>` 한 줄이다(S-4 live 캡처).
WORKSPACE_REF = re.compile(r"^OK (workspace:[1-9][0-9]*)$")


def _run_subprocess(argv, **kwargs):
    return subprocess.run(
        argv, capture_output=True, text=True, timeout=CMUX_TIMEOUT_SECONDS, **kwargs
    )


def _observed_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _failure(exit_code: int, detail: str, failure_reason: str, **extra) -> dict:
    return {
        "adapter": ADAPTER_NAME,
        "exit_code": exit_code,
        "failure_reason": failure_reason,
        "detail": detail,
        "fallback_attempted": False,
        **extra,
    }


def _invoke(argv, failure_reason: str, **failure_extra):
    try:
        completed = _run_subprocess(argv)
    except OSError as exc:
        return None, _failure(
            EXIT_CMUX_UNAVAILABLE, f"cmux_unavailable: {exc}", failure_reason, **failure_extra
        )
    except subprocess.SubprocessError as exc:
        return None, _failure(
            EXIT_RESPONSE_UNPARSABLE,
            f"cmux_invocation_failed: {exc}",
            failure_reason,
            **failure_extra,
        )
    if completed.returncode != 0:
        return None, _failure(
            completed.returncode,
            (completed.stderr or "").strip() or "cmux_nonzero_exit",
            failure_reason,
            **failure_extra,
        )
    return completed.stdout, None


def build_argv(worktree_root, command):
    return [
        CMUX_BIN,
        "new-workspace",
        "--name",
        os.path.basename(os.path.normpath(str(worktree_root))),
        "--cwd",
        str(worktree_root),
        "--command",
        str(command),
        "--focus",
        "true",
    ]


def build_read_argv(handle, *, limit=None):
    return [
        CMUX_BIN,
        "read-screen",
        "--workspace",
        str(handle),
        "--lines",
        str(DEFAULT_READ_LINES if limit is None else limit),
    ]


def build_close_argv(handle):
    return [CMUX_BIN, "close-workspace", "--workspace", str(handle)]


def _workspace_ref(stdout: str) -> str | None:
    lines = [line.strip() for line in str(stdout).splitlines() if line.strip()]
    match = WORKSPACE_REF.fullmatch(lines[0]) if len(lines) == 1 else None
    return match.group(1) if match else None


def _prompt_id(command) -> str:
    return hashlib.sha256(str(command).encode("utf-8")).hexdigest()[:16]


def launch(worktree_root, command) -> dict:
    stdout, failure = _invoke(
        build_argv(worktree_root, command), FAILURE_REASON_LAUNCH, launch_mode=LAUNCH_MODE
    )
    if failure is not None:
        return failure
    handle = _workspace_ref(stdout)
    if handle is None:
        return _failure(
            EXIT_RESPONSE_UNPARSABLE,
            "response_unparsable: expected one OK workspace:<n> line",
            FAILURE_REASON_LAUNCH,
            launch_mode=LAUNCH_MODE,
        )
    observed_at = _observed_now()
    return {
        "adapter": ADAPTER_NAME,
        "exit_code": 0,
        "fallback_attempted": False,
        "adapter_handle": handle,
        "reported_cwd": os.path.abspath(str(worktree_root)),
        "launched_at": observed_at,
        "launch_mode": LAUNCH_MODE,
        "prompt_id": _prompt_id(command),
        "submitted_at": observed_at,
        "prompt_receipt_source": PROMPT_SOURCE,
    }


def read(handle, *, cursor=None, limit=None, screen=False) -> dict:
    del cursor, screen
    stdout, failure = _invoke(
        build_read_argv(handle, limit=limit), FAILURE_REASON_READ, handle=handle
    )
    if failure is not None:
        return failure
    return {
        "adapter": ADAPTER_NAME,
        "exit_code": 0,
        "fallback_attempted": False,
        "handle": handle,
        "content": str(stdout).rstrip("\n"),
        "next_cursor": None,
        "source": "screen",
    }


def close(*, handle=None, worktree_root=None, all=False) -> dict:
    if handle is None or worktree_root is not None or all:
        return _failure(
            EXIT_INVALID_ARGUMENTS,
            "cmux close requires one explicit workspace handle",
            FAILURE_REASON_CLOSE_SCOPE_UNSUPPORTED,
            scope=None,
            closed=[],
        )
    _stdout, failure = _invoke(
        build_close_argv(handle), FAILURE_REASON_CLOSE, scope=CLOSE_SCOPE_TERMINAL, closed=[]
    )
    if failure is not None:
        return failure
    return {
        "adapter": ADAPTER_NAME,
        "exit_code": 0,
        "fallback_attempted": False,
        "scope": CLOSE_SCOPE_TERMINAL,
        "closed": [handle],
    }
