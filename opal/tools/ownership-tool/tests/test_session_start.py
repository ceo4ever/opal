# @header
# module: ownership_tool.tests.test_session_start
# layer: test
# domain: ownership
# description: ownership_tool.session_start_hook 공개 계약 검증 — S-2r(export 접두·실제 셸 상속 관측), S-2n(env 미제공·쓰기 실패 fail-safe 불변), S-10, S-12r(registry 부트 owner 등록 4분기), S-13(claim 경로)
# exports: (none — pytest module)
# depends: ownership_tool.session_start_hook, fixtures/hook-payloads, fixtures/registry
"""ownership_tool.session_start_hook 공개 계약 테스트 — 구현 완료 후 전건 GREEN."""
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

    # S-2r(AC-2, C-3): env 파일은 Bash 도구의 **부모 쉘에서 source되는 프리앰블**이므로
    # `KEY=value` 대입만으로는 자식 프로세스에 전파되지 않는다(PROBE-BASELINE §1 P-3·P-4).
    # 계약은 "export 접두 + 값 일치"다 — 기존의 느슨한 `"OPAL_SESSION_ID=" in env_text`를
    # 좁힌다(약화 아님).
    env_text = env_file.read_text(encoding="utf-8")
    key = session_start_hook.SESSION_ID_ENV_LINE_KEY
    export_lines = [line for line in env_text.splitlines() if line.startswith("export {}=".format(key))]
    assert export_lines, "env 파일 줄은 `export {}=`로 시작해야 한다: {!r}".format(key, env_text)

    # 값 일치는 문자열 파싱이 아니라 **실제 셸 상속 경계**에서 관측한다 — 파일을 source한
    # 쉘의 자식 프로세스가 봉투 session_id와 바이트 일치하는 값을 받아야 한다(P-4의 역).
    session_id = payload["session_id"]
    inherited = subprocess.run(
        ["sh", "-c", '. "$1"; sh -c \'printf %s "$OPAL_SESSION_ID"\'', "sh", str(env_file)],
        capture_output=True,
        text=True,
    )
    assert inherited.returncode == 0, inherited.stderr
    assert inherited.stdout == session_id

    assert result.get("lease_claimed") is True


def test_s2r_env_line_survives_shell_metacharacters(tmp_path, monkeypatch):
    """S-2r(AC-2, C-3): 세션 ID에 셸 메타문자가 있어도 source된 자식이 원값을 그대로 받는다.

    env 파일이 셸 스크립트로 실행되므로 값은 quoting되어야 한다(미quoting이면 `;` 뒤가
    명령으로 실행되거나 값이 잘린다). 내부 구현(shlex.quote 사용 여부)이 아니라 공개
    관측점 — source 후 자식 프로세스가 읽는 값 — 으로만 단언한다.
    """
    from ownership_tool import session_start_hook  # RED

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/session-start.json").read_text(encoding="utf-8"))
    worktree_root = wt_tmp / "task_141"
    worktree_root.mkdir(parents=True, exist_ok=True)
    payload["cwd"] = str(worktree_root)
    hostile_session_id = "sess-a b;touch $(pwd)/pwned&'\"x"
    payload["session_id"] = hostile_session_id

    env_file = tmp_path / "env_file.sh"
    session_start_hook.handle(payload, project_root=worktree_root, env_file_path=env_file)

    env_text = env_file.read_text(encoding="utf-8")
    key = session_start_hook.SESSION_ID_ENV_LINE_KEY
    assert any(line.startswith("export {}=".format(key)) for line in env_text.splitlines()), env_text

    inherited = subprocess.run(
        ["sh", "-c", '. "$1"; sh -c \'printf %s "$OPAL_SESSION_ID"\'', "sh", str(env_file)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert inherited.returncode == 0, inherited.stderr
    assert inherited.stdout == hostile_session_id
    assert not (tmp_path / "pwned").exists(), "미quoting된 값이 셸 명령으로 실행됐다"


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
    # S-2n(AC-2) 불변 계약: 허브 cwd의 lease 0건·exit 0은 W-1/W-6 후에도 동일하다.
    assert result.get("exit_code", 0) == 0


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

    # S-2n(AC-2) 불변 계약: env 파일 미제공 경로의 진단·반환 키는 W-1 수정 후에도 동일하다.
    assert result.get("env_file_written") is False
    assert "env_file_not_provided" in result.get("diagnostics", [])
    assert result.get("registered") is True  # 등록은 유지된다(fail-safe)


def test_s2n_env_file_write_failure_keeps_registration_exit0(tmp_path, monkeypatch):
    """S-2n(AC-2): 쓰기 실패 경로 → `env_file_write_failed:` 진단 + 등록 유지 + exit 0.

    W-1(export 접두 + quoting) 적용 후에도 **불변이어야 하는** 회귀 방어 계약이다.
    """
    from ownership_tool import session_start_hook  # RED

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    tmp, hub_tmp, wt_tmp = _clone_fixtures()
    payload = json.loads((tmp / "hook-payloads/session-start.json").read_text(encoding="utf-8"))
    worktree_root = wt_tmp / "task_132"
    worktree_root.mkdir(parents=True, exist_ok=True)
    payload["cwd"] = str(worktree_root)

    # 존재하지 않는 부모 디렉터리 → open(..., "a")가 OSError로 실패한다(디렉터리를 만들지 않는
    # 것이 현재 계약이며 이 테스트는 그 사실을 고정한다).
    unwritable = tmp_path / "no-such-dir" / "env_file.sh"

    result = session_start_hook.handle(payload, project_root=worktree_root, env_file_path=unwritable)

    assert result.get("exit_code", 0) == 0
    assert result.get("env_file_written") is False
    assert any(
        d.startswith("env_file_write_failed:") for d in result.get("diagnostics", [])
    ), result.get("diagnostics")
    assert result.get("registered") is True
    assert not unwritable.exists()


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


# ─────────────────────────────────────────────────────────────────────────────
# S-12r (AC-12, C-9) — registry 부트 owner 등록 4분기
#
# C-9: registry `execution_ownership`의 쓰기는 `worktree-tool ownership-set` 경유만
# 허용된다(meta 파일 직접 편집 금지). 따라서 이 단위 테스트의 검증 대상은 "meta 파일이
# 바뀌었는가"가 **아니라** "ownership-set이 올바른 인자로 정확히 몇 번 호출되는가"다.
# 호출은 subprocess 경계에서 관측한다(아래 _record_ownership_set) — 이는 실제 registry
# 반영의 **substitute**이며, 실물 반영은 S-12가 통합 경로에서 별도로 검증한다.
# fixture는 전부 tmp_path 안에만 만든다(실물 허브 .opal-worktrees/.meta는 읽지도 쓰지도 않는다).
# ─────────────────────────────────────────────────────────────────────────────

S12R_TASK_NUMBER = "777"
S12R_TASK_FOLDER = "777-registry-boot-registration"
S12R_SESSION_ID = "sess-boot-owner-1"


def _build_registry_boot_case(tmp_path, execution_ownership):
    """tmp_path 안에 허브 registry + 워크트리 발급값 사본 + canonical task를 조립한다."""
    hub_root = tmp_path / "hub"
    meta_dir = hub_root / ".opal-worktrees" / ".meta"
    worktree_root = hub_root / ".opal-worktrees" / ("task_" + S12R_TASK_NUMBER)
    task_dir = worktree_root / "tasks" / S12R_TASK_FOLDER
    meta_dir.mkdir(parents=True, exist_ok=True)
    task_dir.mkdir(parents=True, exist_ok=True)

    registry_entry = {
        "task": S12R_TASK_NUMBER,
        "layout": "monorepo",
        "branch": "feat/OP-TASK-" + S12R_TASK_NUMBER,
        "worktree_root": str(worktree_root),
        "allocator_root": str(hub_root),
        "task_home": str(worktree_root),
        "task_folder": S12R_TASK_FOLDER,
        "task_path": str(task_dir),
        "artifact_repo": ".",
        "task_ownership_version": 2,
        "attribution_state": "active",
        "execution_ownership": execution_ownership,
    }
    (meta_dir / ("task_" + S12R_TASK_NUMBER + ".json")).write_text(
        json.dumps(registry_entry, ensure_ascii=False), encoding="utf-8"
    )
    _write_task_ownership_copy(worktree_root, registry_entry)

    template_state = json.loads(
        (FIXTURES_ROOT / "hub" / "HUB-MULTI" / "tasks" / "200-multi-task-x" / "state.json").read_text(
            encoding="utf-8"
        )
    )
    template_state["task_id"] = S12R_TASK_FOLDER
    (task_dir / "state.json").write_text(json.dumps(template_state), encoding="utf-8")

    assert not (worktree_root / ".opal-worktrees").exists()
    return hub_root, worktree_root, task_dir


def _execution_ownership(owner_session_id=None, state="worktree_session_owned"):
    return {
        "state": state,
        "owner_session_id": owner_session_id,
        "adapter": "claude",
        "adapter_handle": "orca-777",
        "generation": 2,
        "launch_receipt": {"ok": True},
        "prompt_receipt": {"ok": True},
        "failure_reason": None,
        "checkpoint_shas": [],
    }


def _record_ownership_set(monkeypatch):
    """`worktree-tool ownership-set` subprocess 호출을 관측한다(호출 substitute).

    argv에 `ownership-set`이 있는 호출만 가로채 기록하고, 그 밖의 subprocess는 실제로
    실행한다(관측이 다른 경로의 동작을 바꾸지 않게 한다).
    """
    calls = []
    real_run = subprocess.run

    def fake_run(cmd, *args, **kwargs):
        argv = [str(c) for c in cmd] if isinstance(cmd, (list, tuple)) else [str(cmd)]
        if any("ownership-set" == part for part in argv):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, stdout='{"ok": true}', stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


def _flag_value(argv, flag):
    assert flag in argv, "{} 누락: {}".format(flag, argv)
    return argv[argv.index(flag) + 1]


def _run_boot_case(tmp_path, monkeypatch, execution_ownership, session_id=S12R_SESSION_ID):
    from ownership_tool import session_start_hook  # RED

    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("OPAL_SESSION_ID", raising=False)

    hub_root, worktree_root, task_dir = _build_registry_boot_case(tmp_path, execution_ownership)
    calls = _record_ownership_set(monkeypatch)

    payload = json.loads((FIXTURES_ROOT / "hook-payloads" / "session-start.json").read_text(encoding="utf-8"))
    payload["cwd"] = str(worktree_root)
    payload["session_id"] = session_id

    result = session_start_hook.handle(
        payload, project_root=worktree_root, env_file_path=tmp_path / "env_file.sh"
    )
    assert result.get("exit_code", 0) == 0
    return result, calls, hub_root, task_dir


def test_s12r_registers_registry_owner_when_slot_is_unowned(tmp_path, monkeypatch):
    """S-12r ①등록 성공: state=worktree_session_owned ∧ owner_session_id 비어 있음
    → `ownership-set` 1회 호출 + `registry_owner_registered: true` (D-H)."""
    result, calls, hub_root, _ = _run_boot_case(tmp_path, monkeypatch, _execution_ownership(None))

    assert result.get("lease_claimed") is True
    assert len(calls) == 1, "ownership-set은 정확히 1회 호출돼야 한다: {}".format(calls)
    argv = calls[0]
    assert _flag_value(argv, "--owner-session-id") == S12R_SESSION_ID
    assert _flag_value(argv, "--execution-ownership") == "worktree_session_owned"
    assert _flag_value(argv, "--attribution-state") == "active"
    assert _flag_value(argv, "--project-root") == str(hub_root)
    assert _flag_value(argv, "--task") == S12R_TASK_NUMBER
    # D-J: generation은 명시하지 않는다(prior+1 단조 증가에 맡긴다).
    assert "--generation" not in argv
    assert result.get("registry_owner_registered") is True


def test_s12r_skips_when_registry_owner_is_current_session(tmp_path, monkeypatch):
    """S-12r ②이미 자기 세션: 멱등 게이트로 호출 0회 (D-J)."""
    result, calls, _, _ = _run_boot_case(
        tmp_path, monkeypatch, _execution_ownership(S12R_SESSION_ID)
    )

    assert calls == [], "이미 자기 세션이면 ownership-set을 호출하지 않는다"
    assert result.get("registry_owner_registered") is not True


def test_s12r_rejects_foreign_registry_owner(tmp_path, monkeypatch):
    """S-12r ③타 세션 owner: 호출 0회 + `foreign_registry_owner` 진단."""
    result, calls, _, _ = _run_boot_case(
        tmp_path, monkeypatch, _execution_ownership("sess-somebody-else")
    )

    assert calls == [], "타 세션 owner를 덮어쓰지 않는다"
    assert result.get("registry_owner_registered") is not True
    assert "foreign_registry_owner" in result.get("diagnostics", []), result.get("diagnostics")


def test_s12r_skips_when_registry_state_is_not_worktree_owned(tmp_path, monkeypatch):
    """S-12r ④state 불일치: 호출 0회 + `registry_not_worktree_owned` 진단."""
    result, calls, _, _ = _run_boot_case(
        tmp_path, monkeypatch, _execution_ownership(None, state="hub_owned")
    )

    assert calls == [], "worktree_session_owned가 아니면 ownership-set을 호출하지 않는다"
    assert result.get("registry_owner_registered") is not True
    assert "registry_not_worktree_owned" in result.get("diagnostics", []), result.get("diagnostics")
