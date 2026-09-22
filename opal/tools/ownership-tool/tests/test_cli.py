# @header
# module: ownership_tool.tests.test_cli
# layer: test
# domain: opal-pipeline
# description: RED-first — ownership_tool.cli(신규, PLAN 150 W-3) 공개 CLI 계약 검증 (S-5, S-6).
#   4서브명령(status·release·handoff·handoff-cancel)의 단일 라인 JSON 출력과 종료코드, 비소유자
#   해제 거부(not_owner), 상대경로 거부(path_not_absolute), 세션 id 해석 순서(--session-id >
#   ownership_core.resolve_session_id), 플랫폼 고유 환경변수명 부재(C-5)를 검증한다. 관측은 전부
#   프로세스 경계(stdout/stderr·exit code)에서 하고 cli 내부 함수를 직접 호출하지 않는다.
# exports: (none — pytest module)
# depends: ownership_tool.cli (미구현), ownership_tool.lease, ownership_tool.claude_adapter
"""RED 테스트 — 구현 전. `ownership_tool/cli.py`는 아직 없다(run.sh는 not_implemented다)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent.parent

CLI_NOW_HUB_SESSION = "sess-hub-150"
CLI_WT_SESSION = "sess-worktree-150"
CLI_OTHER_SESSION = "sess-other-150"


# ─────────────────────────────────────────────────────────────────────────────
# 프로세스 경계 관측 헬퍼 — 내부 구현이 아니라 exit code와 출력만 본다
# ─────────────────────────────────────────────────────────────────────────────


def _run_cli(*args, env_overrides=None, cwd=None):
    """`python -m ownership_tool.cli <args>`를 실행한다(run.sh가 위임하는 그 진입점).

    앰비언트 세션 env를 제거해 `--session-id`/명시 주입만이 세션 id를 정한다 — env -u 유무와
    무관하게 동일 결과가 나와야 한다.
    """
    environ = dict(os.environ)
    environ.pop("OPAL_SESSION_ID", None)
    environ.pop("CLAUDE_CODE_SESSION_ID", None)
    environ["PYTHONPATH"] = str(TOOL_DIR)
    if env_overrides:
        environ.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "ownership_tool.cli", *[str(a) for a in args]],
        capture_output=True,
        text=True,
        cwd=str(cwd or TOOL_DIR),
        env=environ,
    )


def _payload(completed):
    """출력을 **단일 라인 JSON**으로 해석하고 공통 키를 확인한다.

    성공·거부 어느 경로든 정확히 한 줄이어야 한다(스트림 선택은 구현에 맡기되, 두 스트림에
    걸쳐 JSON 줄이 둘 이상 나오면 단일 라인 계약 위반이다).
    """
    lines = [
        line
        for stream in (completed.stdout, completed.stderr)
        for line in stream.splitlines()
        if line.strip()
    ]
    assert len(lines) == 1, "단일 라인 JSON이어야 한다: stdout={!r} stderr={!r}".format(
        completed.stdout, completed.stderr
    )
    data = json.loads(lines[0])
    assert isinstance(data["ok"], bool)
    assert data["command"] == "ownership-tool"
    return data


def _find_value(payload, key):
    """반환 JSON 어디에 놓이든 해당 키의 값을 찾는다.

    PLAN W-3은 `status`가 "lease 레코드 전문 + classify 결과 + handoff_* 필드"를 돌려준다고만
    정하고 중첩 형태를 정하지 않는다 — 내용은 엄격히, 배치는 구현 재량으로 남긴다.
    """
    if isinstance(payload, dict):
        if key in payload:
            return payload[key]
        for value in payload.values():
            found = _find_value(value, key)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_value(item, key)
            if found is not None:
                return found
    return None


def _build_cli_case(tmp_path, *, task_number="320", task_folder="320-cli-lease"):
    """허브 루트 · registry meta 발급값 · canonical task를 tmp_path 안에 조립한다."""
    hub_root = tmp_path / "hub"
    wt_parent = hub_root / ".opal-worktrees"
    meta_dir = wt_parent / ".meta"
    worktree_root = wt_parent / ("task_" + task_number)
    task_dir = worktree_root / "tasks" / task_folder
    meta_dir.mkdir(parents=True, exist_ok=True)
    task_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "task": task_number,
        "worktree_root": str(worktree_root),
        "allocator_root": str(hub_root),
        "task_home": str(worktree_root),
        "task_folder": task_folder,
        "task_path": str(task_dir),
        "artifact_repo": ".",
        "task_ownership_version": 2,
    }
    (meta_dir / ("task_" + task_number + ".json")).write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )
    return hub_root, meta, task_dir


def _claim(task_dir, session_id):
    from ownership_tool import lease

    result = lease.claim(task_dir, session_id=session_id, claim_source="state_transition")
    assert result["ok"] is True, result
    return result


# ─────────────────────────────────────────────────────────────────────────────
# S-5 (AC-5, AC-7, C-5)
# ─────────────────────────────────────────────────────────────────────────────


def test_s5_four_subcommands_return_single_line_json(tmp_path):
    """S-5: 조회·해제·이관·이관취소 4서브명령이 정상 인자에서 전부 단일 라인 JSON을
    `{"ok": true, "command": "ownership-tool", ...}` 형태로 돌려주고 종료코드 0이다."""
    hub_root, meta, task_dir = _build_cli_case(tmp_path)
    _claim(task_dir, CLI_NOW_HUB_SESSION)

    status = _run_cli("status", "--task-path", task_dir, "--session-id", CLI_NOW_HUB_SESSION)
    assert status.returncode == 0, status
    status_payload = _payload(status)
    assert status_payload["ok"] is True
    assert _find_value(status_payload, "owner_session_id") == CLI_NOW_HUB_SESSION
    assert status_payload["classification"] == "current_session_owned"

    handoff = _run_cli(
        "handoff",
        "--task-path", task_dir,
        "--to-worktree-root", meta["worktree_root"],
        "--session-id", CLI_NOW_HUB_SESSION,
    )
    assert handoff.returncode == 0, handoff
    assert _payload(handoff)["ok"] is True

    status_pending = _run_cli("status", "--task-path", task_dir, "--session-id", CLI_NOW_HUB_SESSION)
    assert status_pending.returncode == 0, status_pending
    pending_payload = _payload(status_pending)
    assert pending_payload["classification"] == "unowned"
    assert _find_value(pending_payload, "handoff_to_worktree_root") == meta["worktree_root"]
    assert _find_value(pending_payload, "handoff_from_session_id") == CLI_NOW_HUB_SESSION
    assert _find_value(pending_payload, "handoff_expires_at")

    cancel = _run_cli("handoff-cancel", "--task-path", task_dir, "--session-id", CLI_NOW_HUB_SESSION)
    assert cancel.returncode == 0, cancel
    assert _payload(cancel)["ok"] is True

    release = _run_cli("release", "--task-path", task_dir, "--session-id", CLI_NOW_HUB_SESSION)
    assert release.returncode == 0, release
    assert _payload(release)["ok"] is True


def test_s5_release_from_non_owner_is_rejected_with_nonzero_exit(tmp_path):
    """S-5(D-6): 비소유자 세션의 해제는 `not_owner` 구조화 거부 + 0이 아닌 종료코드이고
    레코드를 건드리지 않는다. 강제 해제 표면(`--force`)은 만들지 않는다(C-3)."""
    hub_root, meta, task_dir = _build_cli_case(
        tmp_path, task_number="321", task_folder="321-cli-not-owner"
    )
    _claim(task_dir, CLI_NOW_HUB_SESSION)
    owner_file = task_dir / "run" / ".runtime" / "owner.json"
    before = json.loads(owner_file.read_text(encoding="utf-8"))

    rejected = _run_cli("release", "--task-path", task_dir, "--session-id", CLI_OTHER_SESSION)
    assert rejected.returncode != 0, rejected
    payload = _payload(rejected)
    assert payload["ok"] is False
    assert payload["error"] == "not_owner"
    assert payload["owner_session_id"] == CLI_NOW_HUB_SESSION
    assert json.loads(owner_file.read_text(encoding="utf-8")) == before


def test_s5_release_is_noop_with_exit_zero_when_no_live_lease(tmp_path):
    """S-5(D-6): lease 부재·이미 released는 `noop: true` + 종료코드 0이다."""
    hub_root, meta, task_dir = _build_cli_case(
        tmp_path, task_number="322", task_folder="322-cli-noop"
    )

    absent = _run_cli("release", "--task-path", task_dir, "--session-id", CLI_NOW_HUB_SESSION)
    assert absent.returncode == 0, absent
    absent_payload = _payload(absent)
    assert absent_payload["ok"] is True
    assert absent_payload["noop"] is True

    _claim(task_dir, CLI_NOW_HUB_SESSION)
    assert _run_cli(
        "release", "--task-path", task_dir, "--session-id", CLI_NOW_HUB_SESSION
    ).returncode == 0
    already = _run_cli("release", "--task-path", task_dir, "--session-id", CLI_NOW_HUB_SESSION)
    assert already.returncode == 0, already
    already_payload = _payload(already)
    assert already_payload["ok"] is True
    assert already_payload["noop"] is True


def test_s5_relative_paths_are_rejected_without_inference(tmp_path):
    """S-5(C-4): 상대경로 `--task-path`·`--to-worktree-root`는 cwd 기준 보정 없이
    `path_not_absolute`로 거부된다."""
    hub_root, meta, task_dir = _build_cli_case(
        tmp_path, task_number="323", task_folder="323-cli-relative"
    )
    _claim(task_dir, CLI_NOW_HUB_SESSION)

    relative_task = _run_cli(
        "status", "--task-path", "./tasks/323-cli-relative", "--session-id", CLI_NOW_HUB_SESSION,
        cwd=hub_root,
    )
    assert relative_task.returncode != 0, relative_task
    relative_task_payload = _payload(relative_task)
    assert relative_task_payload["ok"] is False
    assert relative_task_payload["error"] == "path_not_absolute"

    relative_target = _run_cli(
        "handoff",
        "--task-path", task_dir,
        "--to-worktree-root", "../.opal-worktrees/task_323",
        "--session-id", CLI_NOW_HUB_SESSION,
        cwd=hub_root,
    )
    assert relative_target.returncode != 0, relative_target
    relative_target_payload = _payload(relative_target)
    assert relative_target_payload["ok"] is False
    assert relative_target_payload["error"] == "path_not_absolute"

    # 거부는 레코드를 건드리지 않는다.
    record = json.loads((task_dir / "run" / ".runtime" / "owner.json").read_text(encoding="utf-8"))
    assert record["owner_session_id"] == CLI_NOW_HUB_SESSION
    assert record["status"] == "active"


def test_s5_session_id_resolution_prefers_flag_then_neutral_env(tmp_path):
    """S-5(C-5): 세션 id 해석은 `--session-id` > `ownership_core.resolve_session_id` 순이다.

    플래그 없이 중립 env(`OPAL_SESSION_ID`)만으로 소유자 해제가 성립해야 하고, 플래그가
    있으면 env보다 우선한다(비소유자 플래그 → not_owner).
    """
    hub_root, meta, task_dir = _build_cli_case(
        tmp_path, task_number="324", task_folder="324-cli-session-id"
    )
    _claim(task_dir, CLI_NOW_HUB_SESSION)

    # 플래그가 env를 이긴다 — env는 소유자인데 플래그가 비소유자면 거부된다.
    flag_wins = _run_cli(
        "release", "--task-path", task_dir, "--session-id", CLI_OTHER_SESSION,
        env_overrides={"OPAL_SESSION_ID": CLI_NOW_HUB_SESSION},
    )
    assert flag_wins.returncode != 0, flag_wins
    assert _payload(flag_wins)["error"] == "not_owner"

    # 플래그가 없으면 중립 env가 해석된다.
    env_resolved = _run_cli(
        "release", "--task-path", task_dir,
        env_overrides={"OPAL_SESSION_ID": CLI_NOW_HUB_SESSION},
    )
    assert env_resolved.returncode == 0, env_resolved
    assert _payload(env_resolved)["ok"] is True


def test_s5_cli_module_holds_no_platform_specific_env_var_names():
    """S-5(C-5): 플랫폼 고유 환경변수명은 `claude_adapter.py`에만 둔다 — `cli.py` 본문에
    그 이름이 등장하면 안 된다."""
    from ownership_tool import claude_adapter, cli  # RED: cli 미구현

    source = Path(cli.__file__).read_text(encoding="utf-8")
    for name in (
        claude_adapter.SESSION_ID_ENV,
        claude_adapter.ENV_FILE_ENV,
        claude_adapter.STOP_HOOK_BLOCK_CAP_ENV,
    ):
        assert name not in source, "cli.py에 플랫폼 고유 환경변수명이 있다: {}".format(name)
    assert "CLAUDE" not in source


def test_s5_run_sh_no_longer_returns_not_implemented(tmp_path):
    """S-5(AC-5): `run.sh`가 `not_implemented`를 반환하지 않고 CLI에 위임한다."""
    hub_root, meta, task_dir = _build_cli_case(
        tmp_path, task_number="325", task_folder="325-cli-run-sh"
    )
    _claim(task_dir, CLI_NOW_HUB_SESSION)

    completed = subprocess.run(
        [str(TOOL_DIR / "run.sh"), "status", "--task-path", str(task_dir),
         "--session-id", CLI_NOW_HUB_SESSION],
        capture_output=True,
        text=True,
    )
    payload = _payload(completed)
    assert payload.get("error") != "not_implemented", completed
    assert payload["ok"] is True
    assert completed.returncode == 0


# ─────────────────────────────────────────────────────────────────────────────
# S-6 (AC-6)
# ─────────────────────────────────────────────────────────────────────────────


def test_s6_release_then_unowned_then_other_session_claims(tmp_path):
    """S-6(AC-6): 소유 세션이 해제하면 조회 결과가 무소유가 되고, 다른 세션이 claim에
    성공한다 — 강제 해제 표면 없이 소유자 자신의 명시 해제만으로 이전이 성립한다(C-3)."""
    from ownership_tool import lease

    hub_root, meta, task_dir = _build_cli_case(
        tmp_path, task_number="326", task_folder="326-cli-release-handover"
    )
    _claim(task_dir, CLI_NOW_HUB_SESSION)

    released = _run_cli("release", "--task-path", task_dir, "--session-id", CLI_NOW_HUB_SESSION)
    assert released.returncode == 0, released
    assert _payload(released)["ok"] is True

    status = _run_cli("status", "--task-path", task_dir, "--session-id", CLI_NOW_HUB_SESSION)
    assert status.returncode == 0, status
    status_payload = _payload(status)
    assert status_payload["classification"] == "unowned", status_payload

    other_status = _run_cli("status", "--task-path", task_dir, "--session-id", CLI_OTHER_SESSION)
    assert _payload(other_status)["classification"] == "unowned"

    claimed = lease.claim(task_dir, session_id=CLI_OTHER_SESSION, claim_source="session_start")
    assert claimed["ok"] is True, claimed
    assert claimed["owner_session_id"] == CLI_OTHER_SESSION

    after = _run_cli("status", "--task-path", task_dir, "--session-id", CLI_OTHER_SESSION)
    assert _payload(after)["classification"] == "current_session_owned"
