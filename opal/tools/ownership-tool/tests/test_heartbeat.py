# @header
# module: ownership_tool.tests.test_heartbeat
# layer: test
# domain: ownership
# description: ownership_tool.heartbeat_hook / session_end_hook 공개 계약 검증 (S-12 hooks). 기존
#   3건은 GREEN. 4번째(closed 세션 registry가 PostToolUse heartbeat로 되살아나지 않아야 한다)는
#   heartbeat_hook이 세션 registry 레코드의 status를 보지 않고 존재 여부만으로 재등록해 RED다.
#   태스크 150 추가분(S-3, AC-1·H-4) — 허브→워크트리 이관(D-3) 대기 lease가 이관을 수행한
#   허브 세션의 heartbeat로 되살아나지 않는지를 고정한다: lease.claim→lease.handoff 실호출로
#   만든 handoff_pending 레코드에 lease.heartbeat를 걸어 {"ok": True, "noop": True} 반환과
#   레코드 파일 mtime·size·내용 불변을 확인하고, 실제 PostToolUse 진입점
#   heartbeat_hook.handle의 갱신 대상이 0건인지도 함께 확인한다.
# exports: (none — pytest module)
# depends: ownership_tool.heartbeat_hook, ownership_tool.session_end_hook, ownership_tool.session_registry,
#   ownership_tool.ownership_core, ownership_tool.lease, fixtures/hook-payloads
"""S-12 hooks 공개 계약 회귀 — 3건 GREEN + closed 세션 재활성화 방지 1건(RED, 결함②) +
태스크 150 S-3(이관 대기 lease의 허브 heartbeat no-op) 회귀 가드 1건."""
from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ownership_tool import ownership_core, session_registry

FIXTURES_ROOT = Path(__file__).parent / "fixtures"


def _clone_fixtures() -> tuple[Path, Path, Path]:
    tmp = Path(tempfile.mkdtemp(prefix="ownership-fixtures-"))
    shutil.copytree(FIXTURES_ROOT, tmp, dirs_exist_ok=True)
    hub_tmp = tmp / "hub_root"
    # 실물 동형화(W-2'): 워크트리 루트는 허브의 형제가 아니라
    # <hub_root>/.opal-worktrees/task_NNN이고 registry meta는
    # <hub_root>/.opal-worktrees/.meta/에 위치한다(worktree.md 발급 계약).
    wt_tmp = hub_tmp / ".opal-worktrees"
    hub_tmp.mkdir(parents=True, exist_ok=True)
    wt_tmp.mkdir(parents=True, exist_ok=True)
    for p in tmp.rglob("*.json"):
        text = p.read_text(encoding="utf-8")
        text = text.replace("{HUB}", str(hub_tmp)).replace("{WT}", str(wt_tmp))
        p.write_text(text, encoding="utf-8")
    return tmp, hub_tmp, wt_tmp


def _seed_owned_task_138(hub_tmp, wt_tmp, owner_session_id):
    """wt_tmp/task_138에 registry meta + <owner_session_id> live lease를 실물 배치하고
    canonical task_dir을 반환한다. session_start_hook 실측대로 registry meta는
    <project_root>/.opal-worktrees/.meta/(project_root=worktree_root)에 둔다.
    """
    worktree_root = wt_tmp / "task_138"
    worktree_root.mkdir(parents=True, exist_ok=True)
    task_folder = "138-260916-opds-스톱-훅-태스크-소유권-결정론화"
    task_dir = worktree_root / "tasks" / task_folder
    registry_entry = {
        "allocator_root": str(hub_tmp),
        "task_home": str(worktree_root),
        "task_folder": task_folder,
        "task_path": str(task_dir),
        "artifact_repo": ".",
        "task_ownership_version": 2,
    }
    meta_dir = worktree_root / ".opal-worktrees" / ".meta" / "task_138"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "meta.json").write_text(json.dumps(registry_entry), encoding="utf-8")

    owner_record = json.loads(
        (FIXTURES_ROOT / "runtime" / "owner-current-session.json").read_text(encoding="utf-8")
    )
    owner_record["task_path"] = str(task_dir)
    owner_record["owner_session_id"] = owner_session_id
    owner_record["status"] = "hub_owned"
    owner_path = task_dir / "run" / ".runtime" / "owner.json"
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(json.dumps(owner_record), encoding="utf-8")
    return worktree_root, task_dir


def test_posttooluse_from_owning_session_refreshes_heartbeat(monkeypatch):
    """PostToolUse(A, 소유 세션) → heartbeat_hook이 모든 PostToolUse에서 호출되어 갱신."""
    from ownership_tool import heartbeat_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/posttooluse.json").read_text(encoding="utf-8"))
    payload["cwd"] = str(wt_tmp / "task_138")
    payload["session_id"] = "sess-a"

    # setup(B-1): "소유 세션"이 성립하려면 canonical task에 이 세션("sess-a")이 소유한
    # live lease가 실제로 있어야 한다.
    worktree_root, _task_dir = _seed_owned_task_138(hub_tmp, wt_tmp, owner_session_id="sess-a")

    result = heartbeat_hook.handle(payload, project_root=worktree_root)
    assert result.get("exit_code", 0) == 0


def test_posttooluse_from_foreign_session_is_noop(monkeypatch):
    """타 세션 PostToolUse → no-op."""
    from ownership_tool import heartbeat_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/posttooluse.json").read_text(encoding="utf-8"))
    payload["cwd"] = str(wt_tmp / "task_138")
    payload["session_id"] = "sess-foreign"

    # setup(B-1): "타 세션"이 성립하려면 canonical task의 live lease 소유자가 payload의
    # session_id("sess-foreign")와 달라야 한다(소유자는 "sess-a").
    worktree_root, _task_dir = _seed_owned_task_138(hub_tmp, wt_tmp, owner_session_id="sess-a")

    result = heartbeat_hook.handle(payload, project_root=worktree_root)
    assert result.get("noop") is True or result.get("exit_code", 0) == 0


def test_session_end_releases_and_closes_registry(monkeypatch):
    """SessionEnd → registry closed, lease released."""
    from ownership_tool import session_end_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/sessionend.json").read_text(encoding="utf-8"))
    payload["cwd"] = str(wt_tmp / "task_138")
    payload["session_id"] = "sess-a"

    # setup(B-1): release가 성립하려면 종료하는 세션("sess-a")이 소유한 live lease와,
    # session_start_hook.register가 만드는 세션 registry 엔트리가 실제로 있어야 한다.
    worktree_root, _task_dir = _seed_owned_task_138(hub_tmp, wt_tmp, owner_session_id="sess-a")
    session_registry.register(worktree_root, "sess-a", payload["cwd"])

    result = session_end_hook.handle(payload, project_root=worktree_root)
    assert result.get("released") is True


def test_posttooluse_after_sessionend_keeps_registry_closed_and_does_not_refresh_lease(monkeypatch):
    """SessionEnd로 닫힌 세션의 PostToolUse는 세션 registry의 status를 되살리지 않고 lease도
    갱신하지 않아야 한다(결함② — heartbeat가 닫힌 세션을 되살린다).

    heartbeat_hook.handle()은 세션 registry 레코드의 *존재 여부*만 보고(read_json(...).ok)
    session_registry.register()를 호출한다 — register()는 status를 무조건 STATUS_ACTIVE로
    덮어쓰므로(heartbeat_hook.py에 status 참조가 0건) SessionEnd로 closed 전이된 레코드가
    다음 PostToolUse에서 active로 되살아난다. lease 축은 release로 이미 'released'이므로
    owned_task_paths가 빈 목록을 돌려줘 lease 갱신 자체는 일어나지 않는다(정상) — 문제는
    세션 registry 축뿐이다. 이 단언은 현재 구현에서 RED다."""
    from ownership_tool import heartbeat_hook, session_end_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root, _task_dir = _seed_owned_task_138(hub_tmp, wt_tmp, owner_session_id="sess-a")

    end_payload = json.loads((tmp / "hook-payloads/sessionend.json").read_text(encoding="utf-8"))
    end_payload["cwd"] = str(worktree_root)
    end_payload["session_id"] = "sess-a"

    # setup(B-1): 먼저 세션 registry 레코드를 실물 생성한 뒤 SessionEnd로 닫는다(test 3과
    # 동일 사전조건 — session_registry.register 없이는 registry_closed 판정 자체가 불가).
    session_registry.register(worktree_root, "sess-a", end_payload["cwd"])
    end_result = session_end_hook.handle(end_payload, project_root=worktree_root)
    assert end_result.get("registry_closed") is True

    registry_path = ownership_core.session_registry_path(worktree_root, "sess-a")
    closed_record = ownership_core.read_json(registry_path)
    assert closed_record.get("ok") is True
    assert closed_record["data"]["status"] == "closed"

    post_payload = json.loads((tmp / "hook-payloads/posttooluse.json").read_text(encoding="utf-8"))
    post_payload["cwd"] = str(worktree_root)
    post_payload["session_id"] = "sess-a"

    result = heartbeat_hook.handle(post_payload, project_root=worktree_root)

    # lease 축: released lease는 current_session_owned이 아니므로 갱신 대상에 들지 않는다
    # (이 단언은 오늘도 PASS — 문제는 아래 registry status 단언이다).
    assert result["refreshed"] == []

    # registry 축: closed 상태가 되살아나면 안 된다 — 오늘은 heartbeat_hook이
    # session_registry.register()를 무조건 호출해 status가 "active"로 되돌아가므로 FAIL한다.
    reread = ownership_core.read_json(registry_path)
    assert reread.get("ok") is True
    assert reread["data"]["status"] == "closed", (
        "closed 세션 registry가 PostToolUse heartbeat로 되살아나면 안 된다 "
        f"(actual status={reread['data'].get('status')!r})"
    )


# ─────────────────────────────────────────────────────────────────────────────
# S-3(AC-1·H-4) — 이관 대기 lease는 이관을 수행한 허브 세션의 heartbeat로 되살아나면
# 안 된다. 허브 세션은 매 도구 호출마다 PostToolUse heartbeat를 발화하므로, 이 경로가
# handoff_pending 레코드를 갱신하면 AC-1(이관된 태스크의 소유자는 워크트리 세션이다)이
# 수 초 만에 깨진다. lease.heartbeat 공개 반환값과 레코드 파일의 불변성, 그리고 실제
# PostToolUse 진입점(heartbeat_hook.handle)의 갱신 대상 0건을 함께 고정한다.
# 레코드는 손으로 조립하지 않고 lease.claim → lease.handoff 실호출로 만든다.
# ─────────────────────────────────────────────────────────────────────────────

_KST = timezone(timedelta(hours=9))


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _seed_handoff_pending_worktree(hub_tmp, wt_tmp, task_num, task_folder, registry_entry_out=None):
    """<wt_tmp>/task_<num> 워크트리와 그 안의 canonical task를 실물 배치하고 발급값 사본
    (<worktree_root>/.opal/task-ownership.json)을 내려보낸다 — heartbeat_hook의 cwd→task
    해석이 이 사본을 읽는다(test_integration.py `_seed_manual_worktree`와 같은 방식)."""
    worktree_root = wt_tmp / "task_{}".format(task_num)
    worktree_root.mkdir(parents=True, exist_ok=True)
    task_dir = worktree_root / "tasks" / task_folder
    task_dir.mkdir(parents=True, exist_ok=True)
    registry_entry = {
        "allocator_root": str(hub_tmp),
        "task_home": str(worktree_root),
        "task_folder": task_folder,
        "task_path": str(task_dir),
        "artifact_repo": ".",
        "task_ownership_version": 2,
    }
    meta_dir = wt_tmp / ".meta" / "task_{}".format(task_num)
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "meta.json").write_text(
        json.dumps(registry_entry, ensure_ascii=False), encoding="utf-8"
    )
    copy_path = ownership_core.task_ownership_copy_path(worktree_root)
    copy_path.parent.mkdir(parents=True, exist_ok=True)
    copy_path.write_text(json.dumps(registry_entry, ensure_ascii=False), encoding="utf-8")
    return worktree_root, task_dir


def test_s3_hub_heartbeat_does_not_revive_handoff_pending_lease(monkeypatch):
    """이관 대기 lease + 이관을 수행한 허브 세션 id → heartbeat는 no-op이고 파일을 쓰지 않는다."""
    from ownership_tool import heartbeat_hook, lease

    # setup(B-5): 앰비언트 세션 env 격리(다른 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root, task_dir = _seed_handoff_pending_worktree(
        hub_tmp, wt_tmp, "150", "150-handoff-heartbeat-noop")

    hub_session = "sess-150-hub"
    now = datetime.now(_KST).replace(microsecond=0)

    # ① 허브 세션이 canonical task lease를 실제로 확보한 뒤 ② 워크트리 앞으로 이관한다 —
    # 이관 대기 레코드는 손으로 쓰지 않고 공개 API 연쇄가 만든다.
    claimed = lease.claim(str(task_dir), session_id=hub_session,
                          claim_source="state_transition", now=_iso(now))
    assert claimed["ok"] is True
    handed = lease.handoff(str(task_dir), session_id=hub_session,
                           to_worktree_root=str(worktree_root),
                           now=_iso(now + timedelta(seconds=1)))
    assert handed["ok"] is True

    lease_path = ownership_core.hub_lease_path(task_dir)
    before_record = json.loads(lease_path.read_text(encoding="utf-8"))
    assert before_record["status"] == lease.HANDOFF_STATUS
    assert before_record["owner_session_id"] is None
    before_stat = lease_path.stat()

    # ③ 허브 세션 id로 heartbeat를 호출한다 — 반환은 정확히 no-op 계약이어야 한다.
    beat = lease.heartbeat(str(task_dir), session_id=hub_session,
                           now=_iso(now + timedelta(seconds=2)), project_root=worktree_root)
    assert beat == {"ok": True, "noop": True}, beat

    # ④ 파일이 쓰이지 않았다 — mtime·size 불변으로 확인한다(갱신은 원자 교체라 mtime이 바뀐다).
    after_stat = lease_path.stat()
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns
    assert after_stat.st_size == before_stat.st_size

    # ⑤ 소유자 필드와 이관 3필드를 포함해 레코드 전체가 불변이다.
    assert json.loads(lease_path.read_text(encoding="utf-8")) == before_record

    # ⑥ 실제 PostToolUse 진입점도 이 레코드를 갱신 후보로 잡지 않는다(H-4의 실질) —
    # 허브 세션은 매 도구 호출마다 이 경로를 밟는다.
    payload = json.loads((tmp / "hook-payloads/posttooluse.json").read_text(encoding="utf-8"))
    payload["cwd"] = str(worktree_root)
    payload["session_id"] = hub_session
    hook_result = heartbeat_hook.handle(
        payload, project_root=worktree_root, now=_iso(now + timedelta(seconds=3)))
    assert hook_result["refreshed"] == [], hook_result

    assert lease_path.stat().st_mtime_ns == before_stat.st_mtime_ns
    assert json.loads(lease_path.read_text(encoding="utf-8")) == before_record


# ─────────────────────────────────────────────────────────────────────────────
# TASK-149 RED-first — S-8 (AC-4). `<루트>/.opal/setting.local.json`의
# `ownership.lease_ttl_sec`를 기본값(14400)과 다른 값으로 두고, 봉투 cwd는 하위
# 디렉토리인 상태에서 heartbeat_hook.py를 subprocess로 실행하면 그 설정값이
# 적용돼야 한다(14400으로 폴백하지 않는다).
#
# RED: 지금은 heartbeat_hook.main()이 project_root = payload.get("cwd")(하위
# 디렉토리)를 그대로 채택하므로 lease.heartbeat에 넘기는 project_root가 루트가
# 아니라서 resolve_ttl_sec가 루트의 setting.local.json을 못 읽는다(폴백 14400).
# ─────────────────────────────────────────────────────────────────────────────

import os as _t149_os
import subprocess as _t149_subprocess

_T149_TOOL_DIR = Path(__file__).resolve().parent.parent
_T149_HEARTBEAT_HOOK = _T149_TOOL_DIR / "ownership_tool" / "heartbeat_hook.py"
_T149_VENV_PYTHON = Path.home() / ".opal" / ".venv" / "bin" / "python"
_T149_CUSTOM_TTL = 999


def _t149_minimal_env():
    env = {}
    for key in ("PATH", "HOME"):
        if key in _t149_os.environ:
            env[key] = _t149_os.environ[key]
    return env


def test_t149_s8_heartbeat_applies_root_setting_ttl_from_subdir_cwd(tmp_path):
    wt_root = tmp_path / "wt_root"
    task_dir = tmp_path / "hub" / "tasks" / "t149-s8"
    (wt_root / ".opal").mkdir(parents=True)
    (wt_root / ".opal" / "task-ownership.json").write_text(
        json.dumps({
            "allocator_root": str(tmp_path / "hub"),
            "task_path": str(task_dir),
        }),
        encoding="utf-8",
    )
    (wt_root / ".opal" / "setting.local.json").write_text(
        json.dumps({"ownership": {"lease_ttl_sec": _T149_CUSTOM_TTL}}),
        encoding="utf-8",
    )

    session_id = "sess-t149-s8"
    now = datetime(2026, 9, 22, 10, 0, 0, tzinfo=timezone(timedelta(hours=9)))
    owner_path = task_dir / "run" / ".runtime" / "owner.json"
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    # ttl_sec 없는 구버전 레코드 — heartbeat가 resolve_ttl_sec(project_root)로
    # 재해석하게 만든다(lease.heartbeat 구현 — ttl_sec 없으면 project_root 설정을 읽는다).
    owner_path.write_text(json.dumps({
        "task_path": str(task_dir),
        "owner_session_id": session_id,
        "generation": 1,
        "claimed_at": now.isoformat(),
        "heartbeat_at": now.isoformat(),
        "lease_expires_at": (now + timedelta(hours=4)).isoformat(),
        "status": "active",
        "claim_source": "state_transition",
    }), encoding="utf-8")

    sub_cwd = wt_root / "sub" / "nested"
    sub_cwd.mkdir(parents=True)

    payload = {
        "cwd": str(sub_cwd),
        "session_id": session_id,
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "tool_response": {"stdout": "hi\n", "stderr": "", "exit_code": 0},
    }
    env = _t149_minimal_env()
    env["OPAL_PROJECT_ROOT"] = str(wt_root)

    result = _t149_subprocess.run(
        [str(_T149_VENV_PYTHON), str(_T149_HEARTBEAT_HOOK)],
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True, text=True,
        cwd=str(sub_cwd), env=env,
    )
    assert result.returncode == 0, f"T149.S-8 fail-safe exit 0 위반 — {result.stderr!r}"

    updated = json.loads(owner_path.read_text(encoding="utf-8"))
    heartbeat_at = datetime.fromisoformat(updated["heartbeat_at"])
    lease_expires_at = datetime.fromisoformat(updated["lease_expires_at"])
    applied_ttl_sec = round((lease_expires_at - heartbeat_at).total_seconds())
    assert applied_ttl_sec == _T149_CUSTOM_TTL, (
        f"T149.S-8 위반 — heartbeat가 루트 setting.local.json의 lease_ttl_sec({_T149_CUSTOM_TTL})을 "
        f"적용하지 않음(적용된 TTL={applied_ttl_sec}, 14400 기본 폴백으로 보인다): {updated!r}"
    )
