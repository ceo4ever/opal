#!/usr/bin/env python3
"""
@header {
  "module": "verify_real_cli",
  "layer": "task-artifact",
  "domain": "opal-pipeline",
  "description": "TASK 153 W-6 — 실 claude CLI(2.1.280)로 훅 세션 식별 결함(D-7)을 재현·검증한다.
    임시 프로젝트(.opal/AGENT.md 마커, 임시 태스크, .opal/task-ownership.json 발급 사본)에
    가짜 부모 세션의 active lease·active registry를 실물 배치하고, `claude --setting-sources
    project mcp get context7`·`mcp list`를 자식 프로세스로 실행한다. 자식 env는 명시 dict로
    구성하며(PATH·HOME·USER·LANG·TERM + OPAL_SESSION_ID/CLAUDE_CODE_SESSION_ID=가짜 부모 id +
    OPAL_PROJECT_ROOT=임시 루트) 실제 세션의 OPAL_SESSION_ID·CLAUDE_CODE_SESSION_ID·
    CLAUDE_ENV_FILE·CLAUDE_CODE_MESSAGING_*·CLAUDECODE는 절대 전달하지 않는다.
    mode=control은 훅 미배선(사용자 전역 훅이 --setting-sources project로 배제됨을 확인하는
    대조군), mode=before는 `git archive HEAD`로 복원한 ownership-tool 임시 배포본, mode=after는
    작업본 ownership-tool 사본(지금은 구현하되 실행하지 않는다 — TEST 단계 담당)으로 SessionStart·
    SessionEnd·PostToolUse(heartbeat) 훅을 임시 프로젝트 .claude/settings.json에 배선한다.
    각 훅 명령은 stdin 봉투를 evidence/payloads/<mode>-<event>-<n>.json에 저장한 뒤 배포본
    훅 스크립트로 넘기는 래퍼 쉘 스크립트를 경유한다. 실행 전후 실제 태스크 153
    run/.runtime/owner.json의 owner_session_id·status·generation이 불변인지 매 실행마다
    확인하고, 변화가 감지되면 즉시 중단한다(TASK C-3 안전장치).",
  "exports": ["main"],
  "depends": ["claude CLI 2.1.280", "git archive"]
}
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone

_KST = timezone(timedelta(hours=9))

# 이 스크립트가 사는 곳 = <task_path>/run/real-cli
THIS_DIR = pathlib.Path(__file__).resolve().parent
EVIDENCE_DIR = THIS_DIR
TASK_PATH = THIS_DIR.parent.parent  # <task_path>
CODE_ROOT = pathlib.Path(
    "/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_153"
).resolve()
REAL_OWNER_JSON = TASK_PATH / "run" / ".runtime" / "owner.json"

CLAUDE_BIN = shutil.which("claude") or "/Users/iskang/.local/bin/claude"
PYTHON_BIN = os.path.expanduser("~/.opal/.venv/bin/python")


def _now_str() -> str:
    return datetime.now(_KST).isoformat()


def _read_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _snapshot_real_owner():
    """실제 태스크 153 owner.json의 불변 감시 대상 3필드 + 원문 스냅샷."""
    data = _read_json(REAL_OWNER_JSON)
    if data is None:
        return {"exists": False}
    return {
        "exists": True,
        "owner_session_id": data.get("owner_session_id"),
        "status": data.get("status"),
        "generation": data.get("generation"),
    }


def _assert_real_owner_unchanged(before: dict, where: str):
    after = _snapshot_real_owner()
    if before != after:
        raise SystemExit(
            "[C-3 위반 감지] 실제 태스크 153 owner.json이 {} 시점에 변했다: before={} after={} "
            "— 즉시 중단한다. 실 CLI 검증을 재실행하지 말 것.".format(where, before, after)
        )


# ─────────────────────────────────────────────────────────────────────────────
# 임시 프로젝트·배포본 준비
# ─────────────────────────────────────────────────────────────────────────────

def _make_temp_project(tmp_root: pathlib.Path, mode: str):
    """.opal/AGENT.md 마커 + 임시 태스크 + .opal/task-ownership.json 발급 사본."""
    project = tmp_root / "project"
    opal_dir = project / ".opal"
    opal_dir.mkdir(parents=True, exist_ok=True)
    (opal_dir / "AGENT.md").write_text("# temp project marker (verify_real_cli)\n", encoding="utf-8")

    task_folder = "000-real-cli-verify-{}".format(mode)
    task_dir = project / "tasks" / task_folder
    task_dir.mkdir(parents=True, exist_ok=True)

    copy_path = opal_dir / "task-ownership.json"
    copy_path.write_text(
        json.dumps(
            {
                "allocator_root": str(project),
                "task_home": str(project),
                "task_folder": task_folder,
                "task_path": str(task_dir),
                "artifact_repo": ".",
                "task_ownership_version": 2,
            }
        ),
        encoding="utf-8",
    )
    return project, task_dir


def _make_deployment(tmp_root: pathlib.Path, mode: str) -> pathlib.Path:
    """ownership-tool 임시 배포본을 만든다. before=git archive HEAD, after=작업본 사본."""
    dest = tmp_root / "deployment-{}".format(mode)
    dest.mkdir(parents=True, exist_ok=True)
    if mode == "before":
        archive_path = tmp_root / "before.tar"
        subprocess.run(
            ["git", "-C", str(CODE_ROOT), "archive", "ace8368", "opal/tools/ownership-tool",
             "-o", str(archive_path)],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(["tar", "-xf", str(archive_path), "-C", str(dest)], check=True)
        return dest / "opal" / "tools" / "ownership-tool" / "ownership_tool"
    if mode == "after":
        src = CODE_ROOT / "opal" / "tools" / "ownership-tool" / "ownership_tool"
        target = dest / "ownership_tool"
        shutil.copytree(src, target)
        return target
    raise ValueError("unknown deployment mode: {}".format(mode))


def _write_wrapper(evidence_payload_dir: pathlib.Path, hook_module_path: pathlib.Path,
                    mode: str, event: str) -> pathlib.Path:
    """stdin 봉투를 evidence/payloads/<mode>-<event>-<n>.json으로 저장한 뒤 배포본 훅으로
    넘기는 래퍼 쉘 스크립트를 만들고 경로를 돌려준다."""
    evidence_payload_dir.mkdir(parents=True, exist_ok=True)
    wrapper_path = evidence_payload_dir.parent / "wrappers" / "{}-{}.sh".format(mode, event)
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    capture_glob_prefix = str(evidence_payload_dir / "{}-{}-".format(mode, event))
    script = """#!/bin/sh
set -eu
STDIN_DATA=$(cat)
N=0
while [ -f "{prefix}${{N}}.json" ]; do N=$((N+1)); done
printf '%s' "$STDIN_DATA" > "{prefix}${{N}}.json"
printf '%s' "$STDIN_DATA" | exec "{python}" "{hook}"
""".format(prefix=capture_glob_prefix, python=PYTHON_BIN, hook=str(hook_module_path))
    wrapper_path.write_text(script, encoding="utf-8")
    wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return wrapper_path


def _write_mcp_fixture(project: pathlib.Path):
    """`--setting-sources project`는 사용자 스코프 MCP를 읽지 않으므로, `mcp get/list`가
    exit 0으로 끝나도록 임시 프로젝트에 프로젝트 스코프 context7 MCP 서버를 등록한다
    (PM 탐침 결과 반영 — 판정 기준 변경 아님, fixture 보강)."""
    (project / ".mcp.json").write_text(
        json.dumps({
            "mcpServers": {
                "context7": {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@upstash/context7-mcp@latest"],
                }
            }
        }, indent=2),
        encoding="utf-8",
    )


def _write_settings(project: pathlib.Path, deployment_hooks_dir: pathlib.Path | None, mode: str,
                     evidence_payload_dir: pathlib.Path):
    """임시 프로젝트 .claude/settings.json에 SessionStart·SessionEnd·PostToolUse(heartbeat)
    훅(배선 대상 모드에서만)과 enableAllProjectMcpServers를 배선한다."""
    claude_dir = project / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    settings = {"enableAllProjectMcpServers": True}

    if deployment_hooks_dir is not None:
        session_start_wrapper = _write_wrapper(
            evidence_payload_dir, deployment_hooks_dir / "session_start_hook.py", mode, "SessionStart")
        session_end_wrapper = _write_wrapper(
            evidence_payload_dir, deployment_hooks_dir / "session_end_hook.py", mode, "SessionEnd")
        heartbeat_wrapper = _write_wrapper(
            evidence_payload_dir, deployment_hooks_dir / "heartbeat_hook.py", mode, "PostToolUse")

        settings["hooks"] = {
            "SessionStart": [{"hooks": [{"type": "command", "command": str(session_start_wrapper)}]}],
            "SessionEnd": [{"hooks": [{"type": "command", "command": str(session_end_wrapper)}]}],
            "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": str(heartbeat_wrapper)}]}],
        }

    (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# lease/registry 실물 배치 — 작업본 ownership_tool.lease/session_registry로 만든다
# ─────────────────────────────────────────────────────────────────────────────

def _seed_parent_state(project: pathlib.Path, task_dir: pathlib.Path, parent_id: str):
    sys.path.insert(0, str(CODE_ROOT / "opal" / "tools" / "ownership-tool"))
    from ownership_tool import lease, session_registry  # noqa: E402  (동적 경로 삽입 후 import)

    claimed = lease.claim(task_dir, session_id=parent_id, claim_source="state_transition",
                          project_root=project)
    if not claimed.get("ok"):
        raise SystemExit("parent lease.claim 실패: {}".format(claimed))
    registered = session_registry.register(project, parent_id, str(project))
    if not registered.get("ok"):
        raise SystemExit("parent session_registry.register 실패: {}".format(registered))
    return claimed, registered


def _lease_status(task_dir: pathlib.Path):
    owner_path = task_dir / "run" / ".runtime" / "owner.json"
    data = _read_json(owner_path)
    return data.get("status") if data else None


def _registry_status(project: pathlib.Path, session_id: str):
    path = project / ".opal" / "run" / ".runtime" / "sessions" / "{}.json".format(session_id)
    data = _read_json(path)
    return data.get("status") if data else None


def _captured_session_ids(evidence_payload_dir: pathlib.Path, mode: str):
    ids = {}
    if not evidence_payload_dir.is_dir():
        return ids
    for path in sorted(evidence_payload_dir.glob("{}-*.json".format(mode))):
        data = _read_json(path)
        ids[path.name] = data.get("session_id") if isinstance(data, dict) else None
    return ids


# ─────────────────────────────────────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────────────────────────────────────

def _run_cli(cwd: pathlib.Path, env: dict, argv_variant: str):
    """claude --setting-sources project mcp get/list를 실행한다. 플래그 위치가 거부되면
    대안 위치를 시도한다."""
    attempts = []
    if argv_variant == "get":
        attempts = [
            [CLAUDE_BIN, "--setting-sources", "project", "mcp", "get", "context7"],
            [CLAUDE_BIN, "mcp", "get", "context7", "--setting-sources", "project"],
        ]
    else:
        attempts = [
            [CLAUDE_BIN, "--setting-sources", "project", "mcp", "list"],
            [CLAUDE_BIN, "mcp", "list", "--setting-sources", "project"],
        ]
    last = None
    for argv in attempts:
        completed = subprocess.run(argv, cwd=str(cwd), env=env, capture_output=True, text=True,
                                    timeout=60)
        last = (argv, completed)
        if completed.returncode == 0 or "unknown option" not in (completed.stderr or "").lower():
            return argv, completed
    return last


def _build_child_env(project_root: pathlib.Path, parent_id: str) -> dict:
    keep = {}
    for key in ("PATH", "HOME", "USER", "LANG", "TERM"):
        if key in os.environ:
            keep[key] = os.environ[key]
    keep["OPAL_SESSION_ID"] = parent_id
    keep["CLAUDE_CODE_SESSION_ID"] = parent_id
    keep["OPAL_PROJECT_ROOT"] = str(project_root)
    return keep


def run_mode(mode: str) -> dict:
    real_owner_before = _snapshot_real_owner()

    tmp_root = pathlib.Path(tempfile.mkdtemp(prefix="verify-real-cli-{}-".format(mode)))
    project, task_dir = _make_temp_project(tmp_root, mode)
    parent_id = "real-cli-parent-{}-{}".format(mode, uuid.uuid4().hex[:8])

    evidence_payload_dir = EVIDENCE_DIR / "payloads"

    _write_mcp_fixture(project)

    hooks_wired = mode in ("before", "after")
    deployment_hooks_dir = _make_deployment(tmp_root, mode) if hooks_wired else None
    _write_settings(project, deployment_hooks_dir, mode, evidence_payload_dir)

    commands = []
    for variant in ("get", "list"):
        claimed, registered = _seed_parent_state(project, task_dir, parent_id)
        env = _build_child_env(project, parent_id)

        _assert_real_owner_unchanged(real_owner_before, "run_mode({})/{} 실행 전".format(mode, variant))
        argv, completed = _run_cli(project, env, variant)
        _assert_real_owner_unchanged(real_owner_before, "run_mode({})/{} 실행 후".format(mode, variant))

        commands.append({
            "variant": variant,
            "argv": argv,
            "exit_code": completed.returncode,
            "stdout_tail": (completed.stdout or "")[-2000:],
            "stderr_tail": (completed.stderr or "")[-2000:],
            "parent_id": parent_id,
            "lease_status_after": _lease_status(task_dir),
            "registry_status_after": _registry_status(project, parent_id),
        })

    captured = _captured_session_ids(evidence_payload_dir, mode) if hooks_wired else {}

    result = {
        "mode": mode,
        "hooks_wired": hooks_wired,
        "project_root": str(project),
        "task_dir": str(task_dir),
        "parent_id_last": parent_id,
        "commands": commands,
        "captured_envelope_session_ids": captured,
        "real_owner_before": real_owner_before,
        "real_owner_after": _snapshot_real_owner(),
        "recorded_at": _now_str(),
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["control", "before", "after"])
    args = parser.parse_args()

    result = run_mode(args.mode)
    out_path = EVIDENCE_DIR / "evidence-{}.json".format(args.mode)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": True, "mode": args.mode, "evidence_path": str(out_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
