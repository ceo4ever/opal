"""
@header {
  "module": "terminal_context",
  "layer": "util",
  "domain": "terminal-context",
  "description": "현재 프로세스에 연결된 터미널 host와 multiplexer를 환경·프로세스 계보로 판별해 닫힌 JSON 스키마로 출력한다.",
  "exports": ["detect_context", "main"],
  "depends": []
}
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence

OUTPUT_KEYS = ("host", "multiplexers", "confidence", "evidence")
EXPLICIT_HOSTS = {"cmux", "orca"}
MAX_ANCESTORS = 64
COMMAND_TIMEOUT_SECONDS = 2

TERM_PROGRAM_HOSTS = {
    "apple_terminal": "apple-terminal",
    "iterm.app": "iterm2",
    "iterm2": "iterm2",
    "wezterm": "wezterm",
    "warpterminal": "warp",
    "warp": "warp",
    "vscode": "vscode",
    "ghostty": "ghostty",
    "alacritty": "alacritty",
    "kitty": "kitty",
}


def _run_process(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Subprocess seam used by ancestry and tmux-client inspection."""
    return subprocess.run(
        list(argv),
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
        check=False,
    )


def _process_record(pid: int) -> tuple[int, str] | None:
    if pid <= 0:
        return None
    try:
        # comm= is the executable only; command= would include argv such as a user prompt.
        completed = _run_process(
            ["ps", "-p", str(pid), "-o", "ppid=", "-o", "comm="]
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if completed.returncode != 0:
        return None
    line = completed.stdout.strip().splitlines()
    if not line:
        return None
    parts = line[0].strip().split(None, 1)
    if not parts or not parts[0].isdigit():
        return None
    return int(parts[0]), parts[1] if len(parts) == 2 else ""


def _ancestor_commands(start_pid: int) -> list[str]:
    commands: list[str] = []
    seen: set[int] = set()
    pid = start_pid
    while pid > 0 and pid not in seen and len(commands) < MAX_ANCESTORS:
        seen.add(pid)
        record = _process_record(pid)
        if record is None:
            break
        parent_pid, command = record
        commands.append(command)
        pid = parent_pid
    return commands


def _tmux_client_pid() -> int | None:
    try:
        completed = _run_process(
            ["tmux", "display-message", "-p", "#{client_pid}"]
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = completed.stdout.strip()
    if completed.returncode != 0 or not value.isdigit():
        return None
    return int(value)


def _host_from_ancestors(executables: Sequence[str]) -> str | None:
    for executable in executables:
        lowered = str(executable).strip().lower()
        basename = lowered.rsplit("/", 1)[-1]
        for host in sorted(EXPLICIT_HOSTS):
            if f"/{host}.app/" in lowered or basename == host:
                return host
    return None


def _has_tmux(commands: Sequence[str]) -> bool:
    return any(re.search(r"(^|[/\s])tmux(?:[:\s]|$)", str(item).lower()) for item in commands)


def _term_program_host(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower()
    for raw, normalized in TERM_PROGRAM_HOSTS.items():
        if lowered == raw.lower():
            return normalized
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return normalized or None


def _result(host: str, multiplexers: list[str], confidence: str, evidence: list[str]) -> dict:
    return {
        "host": host,
        "multiplexers": multiplexers,
        "confidence": confidence,
        "evidence": evidence,
    }


def detect_context(
    *,
    env: Mapping[str, str] | None = None,
    direct_ancestors: Sequence[str] | None = None,
    tmux_client_ancestors: Sequence[str] | None = None,
) -> dict:
    """Return host/layers using only evidence attached to the current process.

    Optional ancestor inputs are deterministic test seams. When omitted, the detector
    walks the caller's parents and, inside tmux, the active client's parents.
    """
    environment = dict(os.environ if env is None else env)
    direct = list(
        _ancestor_commands(os.getppid())
        if direct_ancestors is None
        else direct_ancestors
    )

    tmux_present = bool(environment.get("TMUX")) or _has_tmux(direct)
    multiplexers = ["tmux"] if tmux_present else []
    layer_evidence = ["env:TMUX"] if environment.get("TMUX") else []
    if tmux_present and not layer_evidence:
        layer_evidence.append("ancestor:tmux")

    explicit = environment.get("OPAL_TERMINAL_HOST", "").strip().lower()
    if explicit in EXPLICIT_HOSTS:
        return _result(
            explicit,
            multiplexers,
            "high",
            ["env:OPAL_TERMINAL_HOST", *layer_evidence],
        )

    cmux_signal = next(
        (
            name
            for name in ("CMUX_SURFACE_ID", "CMUX_WORKSPACE_ID", "CMUX_BUNDLE_ID")
            if environment.get(name)
        ),
        None,
    )
    if cmux_signal:
        return _result(
            "cmux",
            multiplexers,
            "high",
            [f"env:{cmux_signal}", *layer_evidence],
        )

    direct_host = _host_from_ancestors(direct)
    if direct_host:
        return _result(
            direct_host,
            multiplexers,
            "high",
            [f"ancestor:{direct_host}", *layer_evidence],
        )

    if tmux_present:
        if tmux_client_ancestors is None:
            client_pid = _tmux_client_pid()
            client_ancestors = _ancestor_commands(client_pid) if client_pid else []
        else:
            client_ancestors = list(tmux_client_ancestors)
        client_host = _host_from_ancestors(client_ancestors)
        if client_host:
            return _result(
                client_host,
                multiplexers,
                "high",
                [f"tmux:client_ancestor:{client_host}", *layer_evidence],
            )

    term_host = _term_program_host(environment.get("TERM_PROGRAM"))
    if term_host:
        return _result(
            term_host,
            multiplexers,
            "medium",
            ["env:TERM_PROGRAM", *layer_evidence],
        )

    return _result("unknown", multiplexers, "low", layer_evidence)


def main() -> int:
    payload = detect_context()
    # Keep key order stable while enforcing the closed public schema.
    sys.stdout.write(
        json.dumps({key: payload[key] for key in OUTPUT_KEYS}, ensure_ascii=False, separators=(",", ":"))
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
