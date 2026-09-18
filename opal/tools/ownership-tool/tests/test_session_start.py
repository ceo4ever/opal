# @header
# module: ownership_tool.tests.test_session_start
# layer: test
# domain: ownership
# description: RED-first — ownership_tool.session_start_hook 공개 계약 검증 (S-10, S-13 claim 경로)
# exports: (none — pytest module)
# depends: ownership_tool.session_start_hook (미구현), fixtures/hook-payloads, fixtures/registry
"""RED 테스트 — 구현 전. ownership_tool.session_start_hook 미구현이므로 ImportError로 실패해야 한다."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ownership_tool import ownership_core

FIXTURES_ROOT = Path(__file__).parent / "fixtures"


def _clone_fixtures() -> tuple[Path, Path, Path]:
    tmp = Path(tempfile.mkdtemp(prefix="ownership-fixtures-"))
    shutil.copytree(FIXTURES_ROOT, tmp, dirs_exist_ok=True)
    hub_tmp = tmp / "hub_root"
    # 실물 동형화(D-20): 워크트리 루트는 허브의 형제가 아니라
    # <hub_root>/.opal-worktrees/task_NNN이고 registry meta는
    # <hub_root>/.opal-worktrees/.meta/에 위치한다(worktree.md 발급 계약). 워크트리 루트
    # 안쪽에는 .opal-worktrees가 존재하지 않는다 — 실물 허브(/Volumes/Data/AIStudio/workspace/
    # ai-framework/.opal-worktrees/)와 대조 확인된 형상이다(.meta/와 task_NNN/이 형제,
    # task_NNN/ 안에는 .opal-worktrees 없음).
    wt_tmp = hub_tmp / ".opal-worktrees"
    hub_tmp.mkdir(parents=True, exist_ok=True)
    wt_tmp.mkdir(parents=True, exist_ok=True)
    for p in tmp.rglob("*.json"):
        text = p.read_text(encoding="utf-8")
        text = text.replace("{HUB}", str(hub_tmp)).replace("{WT}", str(wt_tmp))
        p.write_text(text, encoding="utf-8")
    return tmp, hub_tmp, wt_tmp


def _write_task_ownership_copy(worktree_root: Path, registry_entry: dict) -> Path:
    """D-20: worktree-tool이 내려보내는 발급값 사본을 만든다(읽기 snapshot).

    경로·키 이름은 ownership_core.task_ownership_copy_path/TASK_OWNERSHIP_COPY_NAME이
    SSOT이며 이 헬퍼에서 하드코딩하지 않는다.
    """
    copy_path = ownership_core.task_ownership_copy_path(worktree_root)
    copy_path.parent.mkdir(parents=True, exist_ok=True)
    copy_body = {
        "allocator_root": registry_entry["allocator_root"],
        "task_home": registry_entry["task_home"],
        "task_folder": registry_entry["task_folder"],
        "task_path": registry_entry["task_path"],
        "artifact_repo": registry_entry["artifact_repo"],
        "task_ownership_version": registry_entry["task_ownership_version"],
    }
    copy_path.write_text(json.dumps(copy_body, ensure_ascii=False), encoding="utf-8")
    return copy_path


def test_s10_worktree_cwd_claims_lease_and_registers_session(tmp_path, monkeypatch):
    """S-10: SessionStart 봉투(cwd=worktree root) → 세션 registry 기록 + env append
    + canonical task lease claim 성공."""
    from ownership_tool import session_start_hook  # RED

    # setup(B-5): 앰비언트 CLAUDE_CODE_SESSION_ID/OPAL_SESSION_ID가 payload의 session_id를
    # 덮어쓰지 않게 격리한다 — env -u 유무와 무관하게 동일 결과가 나와야 한다.
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/session-start.json").read_text(encoding="utf-8"))
    worktree_root = wt_tmp / "task_132"
    worktree_root.mkdir(parents=True, exist_ok=True)
    payload["cwd"] = str(worktree_root)

    # setup(D-20 실물화): registry meta는 허브 발급 위치(<hub_tmp>/.opal-worktrees/.meta/,
    # 즉 wt_tmp/.meta)에만 존재한다 — 워크트리 루트 안쪽에는 .opal-worktrees가 없다
    # (worktree.md 발급 계약, 실물 허브 대조 확인). test_stop_evaluator.py가 쓰는 WT-132
    # registry meta 선례를 같은 위치에 그대로 배치한다.
    meta_dir = wt_tmp / ".meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(tmp / "registry" / "active" / "WT-132" / ".meta" / "task_132.json", meta_dir / "task_132.json")

    # setup(D-20): 워크트리 세션은 허브 registry를 직접 추론하지 않고 worktree-tool이
    # 내려보낸 발급값 사본 <worktree_root>/.opal/task-ownership.json(ownership_core.
    # resolve_roots ② 분기)으로 allocator_root·task_path를 얻는다.
    registry_entry = json.loads((meta_dir / "task_132.json").read_text(encoding="utf-8"))
    _write_task_ownership_copy(worktree_root, registry_entry)

    # setup: canonical task_path(worktree_root/tasks/<task_folder>)에 실제 state.json을
    # 배치한다(test_stop_evaluator.py의 hub 사본 배치 선례와 동일한 방식으로 실물화).
    task_folder = "132-260914-opd-oppb-프로젝트빌드-파일럿-신설"
    task_dir = worktree_root / "tasks" / task_folder
    task_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        FIXTURES_ROOT / "hub" / "HUB-CLOSED-MERGED" / "tasks" / task_folder / "state.json",
        task_dir / "state.json",
    )

    # setup(완료기준 1의 [MUST] 집행): 실물에 없는 .opal-worktrees를 워크트리 안에
    # 만들지 않았음을 setup 자신이 단언한다(계약 강화 — 기존 assertion 수정 아님).
    assert not (worktree_root / ".opal-worktrees").exists()

    env_file = tmp_path / "env_file.sh"
    result = session_start_hook.handle(payload, project_root=worktree_root, env_file_path=env_file)

    session_registry_dir = worktree_root / ".opal/run/.runtime/sessions"
    session_files = list(session_registry_dir.glob("*.json"))
    assert session_files, "session registry file expected"
    data = json.loads(session_files[0].read_text(encoding="utf-8"))
    for key in ("session_id", "cwd", "started_at", "heartbeat_at", "expires_at", "status"):
        assert key in data

    env_text = env_file.read_text(encoding="utf-8")
    assert "OPAL_SESSION_ID=" in env_text
    assert result.get("lease_claimed") is True


def test_s10_hub_cwd_creates_zero_leases(tmp_path, monkeypatch):
    """S-10: 허브 cwd → lease 생성 0건."""
    from ownership_tool import session_start_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 S-10 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/session-start.json").read_text(encoding="utf-8"))
    payload["cwd"] = str(hub_tmp)

    env_file = tmp_path / "env_file.sh"
    result = session_start_hook.handle(payload, project_root=hub_tmp, env_file_path=env_file)
    assert result.get("lease_claimed") is False


def test_s10_missing_env_file_is_fail_safe_exit0(tmp_path, capsys, monkeypatch):
    """S-10: env 파일 미제공/쓰기 실패 시 진단만 남기고 등록 유지, exit 0."""
    from ownership_tool import session_start_hook  # RED

    # setup(B-5): 앰비언트 세션 env 격리(다른 S-10 케이스와 동일 사유).
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/session-start.json").read_text(encoding="utf-8"))
    payload["cwd"] = str(wt_tmp / "task_132")
    (wt_tmp / "task_132").mkdir(parents=True, exist_ok=True)

    result = session_start_hook.handle(payload, project_root=wt_tmp / "task_132", env_file_path=None)
    assert result.get("exit_code", 0) == 0


def test_s13_foreign_session_claim_rejected(tmp_path, monkeypatch):
    """S-13: SAME-WORKTREE-TWO-SESSIONS — 세션 1 claim 성공 후 세션 2 claim → foreign_owner 거부,
    소유자 무변경."""
    from ownership_tool import session_start_hook  # RED

    # setup(B-5): 앰비언트 CLAUDE_CODE_SESSION_ID/OPAL_SESSION_ID를 격리한다. D-18 해석 순서는
    # ① OPAL_SESSION_ID ② CLAUDE_CODE_SESSION_ID ③ 봉투이므로, 격리하지 않으면 payload의
    # session_id("sess-1"/"sess-2")가 앰비언트 env로 덮여 두 호출이 같은 세션이 되어 버려
    # foreign_owner가 끝내 발화하지 않는다 — 두 세션이 실제로 구분되게 만드는 것이 이 테스트의
    # setup 핵심이다.
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    worktree_root = wt_tmp / "task_220"
    worktree_root.mkdir(parents=True, exist_ok=True)
    payload = json.loads((tmp / "hook-payloads/session-start.json").read_text(encoding="utf-8"))
    payload["cwd"] = str(worktree_root)

    # setup(D-20 실물화): session_start_hook.handle은 project_root=worktree_root(=cwd)로
    # 호출되며(main()의 실제 계약), registry meta는 허브 발급 위치
    # (<hub_tmp>/.opal-worktrees/.meta/, 즉 wt_tmp/.meta)에만 있다 — 워크트리 루트 안에는
    # .opal-worktrees가 없다(test_s10과 동일 실측, 실물 허브 대조 확인). 기존 registry
    # fixture 중 task_220용은 없어 최소 조립한다(test_stop_evaluator.py S-5의 무소유 태스크
    # 인라인 조립 선례와 동일한 방식).
    task_folder = "220-two-session-worktree-claim"
    task_dir = worktree_root / "tasks" / task_folder
    registry_entry = {
        "allocator_root": str(hub_tmp),
        "task_home": str(worktree_root),
        "task_folder": task_folder,
        "task_path": str(task_dir),
        "artifact_repo": ".",
        "task_ownership_version": 2,
    }
    meta_dir = wt_tmp / ".meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "task_220.json").write_text(json.dumps(registry_entry), encoding="utf-8")

    # setup(D-20): 워크트리 세션은 허브 registry를 직접 추론하지 않고 worktree-tool이
    # 내려보낸 발급값 사본 <worktree_root>/.opal/task-ownership.json으로
    # allocator_root·task_path를 얻는다(test_s10과 동일 계약).
    _write_task_ownership_copy(worktree_root, registry_entry)

    # setup: canonical task_path에 최소 state.json을 실물 배치한다(HUB-MULTI 템플릿 재사용,
    # task_id만 교체).
    template_state = json.loads(
        (FIXTURES_ROOT / "hub" / "HUB-MULTI" / "tasks" / "200-multi-task-x" / "state.json").read_text(
            encoding="utf-8"
        )
    )
    template_state["task_id"] = task_folder
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "state.json").write_text(json.dumps(template_state), encoding="utf-8")

    # setup(완료기준 1의 [MUST] 집행): 실물에 없는 .opal-worktrees를 워크트리 안에
    # 만들지 않았음을 setup 자신이 단언한다(계약 강화 — 기존 assertion 수정 아님).
    assert not (worktree_root / ".opal-worktrees").exists()

    payload["session_id"] = "sess-1"
    r1 = session_start_hook.handle(payload, project_root=worktree_root, env_file_path=tmp_path / "e1.sh")
    assert r1.get("lease_claimed") is True

    payload["session_id"] = "sess-2"
    r2 = session_start_hook.handle(payload, project_root=worktree_root, env_file_path=tmp_path / "e2.sh")
    assert r2.get("lease_claimed") is False
    assert r2.get("classification") == "foreign_owner"
