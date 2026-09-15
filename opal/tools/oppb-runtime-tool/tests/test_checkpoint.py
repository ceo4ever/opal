"""
@header {
  "module": "test_checkpoint",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "oppb-runtime-tool checkpoint 공개 CLI 계약 RED 테스트. 132 TEST-SCENARIO.md S-12 checkpoint 구간(AC-6)과 S-13(AC-7, AC-8)을 검증한다 — Runner가 lease 밖 파일을 수정하거나 commit·checkout·reset을 실행하면 checkpoint가 거부되고, 공유 지식(MEMORY·brain) 쓰기는 lease 쓰기보다 앞서든 뒤서든 쓰기 순서와 무관하게 거부되며, 검증 실패 candidate는 폐기만 되어 project branch·HEAD·공유 index와 다른 Runner lease path hash가 불변이며, 통과 candidate만 expected parent 비교 뒤 fast-forward되고, stale parent candidate는 반영되지 않고 새 parent에서 재생성된다. reset --hard·worktree 전체 restore 호출 0을 PATH 앞단 git audit shim 호출 추적과 reflog 대조라는 두 독립 기제로 기계 단언한다(제안서 §4.5). PLAN H-6에 따라 내부 함수·클래스를 import하지 않고 공개 CLI(run.sh)와 run root 파일 계약으로만 검증한다. mock/patch 금지 — 실제 git 저장소 fixture만 사용한다(PLAN W-17).",
  "exports": [],
  "depends": ["opal/tools/oppb-runtime-tool/run.sh", "git CLI 2.x", "opal/tools/worktree-tool/tests/conftest.py(패턴 원천)"]
}
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess

import pytest

TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
RUN_SH = TOOL_DIR / "run.sh"

GIT_AUTHOR_ARGS = [
    "-c",
    "user.email=test@opal.local",
    "-c",
    "user.name=OPAL Test",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "init.defaultBranch=main",
]

# 제안서 §4.5 [MUST] — "폐기 시에도 path-scoped preimage 복구만 허용하고
# `reset --hard`·worktree 전체 restore를 금지한다."
FORBIDDEN_GIT_CALL_PATTERNS = (
    re.compile(r"\breset\b.*--hard"),
    re.compile(r"\bcheckout\b\s+(-f\s+)?--\s*$"),
    re.compile(r"\bcheckout\b.*--\s+\.\s*$"),
    re.compile(r"\brestore\b(?!.*\s--\s+\S)"),  # pathspec 없는 전체 restore
    re.compile(r"\bclean\b.*-[a-z]*[dfx]"),
    re.compile(r"\bworktree\b\s+(remove|prune)"),
)


def run_git(args: list[str], cwd: pathlib.Path, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["git", *GIT_AUTHOR_ARGS, *args]
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git fixture 구성 실패: {' '.join(cmd)}\n"
            f"cwd={cwd}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def run_oppb(
    args: list[str], env: dict | None = None, timeout: int = 180
) -> subprocess.CompletedProcess:
    """공개 인터페이스(run.sh 서브프로세스)로만 호출한다. run.sh·checkpoint 하위명령이
    아직 없으면(W-6·W-14 구현 전) 이 실패가 RED 증거다."""
    if not RUN_SH.exists():
        pytest.fail(
            "RED: opal/tools/oppb-runtime-tool/run.sh 미존재 — W-6·W-14 구현 전 정상 실패. "
            f"요청 명령: run.sh {' '.join(args)}"
        )
    return subprocess.run(
        ["bash", str(RUN_SH), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def parse_json_stdout(result: subprocess.CompletedProcess, label: str = "") -> dict:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"{label} stdout이 유효 JSON이 아님. exit={result.returncode}\n"
            f"stdout={result.stdout!r}\nstderr={result.stderr!r}\n원인: {exc}"
        )


def write_json(path: pathlib.Path, data) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write(repo: pathlib.Path, relpath: str, content: str) -> pathlib.Path:
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# git audit shim — PATH 앞단에 실행 로그를 남기는 진짜 git wrapper를 둔다.
# 도구를 mock하지 않는다. 실제 git이 그대로 실행되고 인자만 기록된다.
# ─────────────────────────────────────────────────────────────────────────────


def install_git_audit_shim(tmp_path: pathlib.Path) -> tuple[dict, pathlib.Path]:
    real_git = shutil.which("git")
    assert real_git, "git 실행 파일을 찾을 수 없다 — 실 git fixture 전제 위반."
    bindir = tmp_path / "_gitshim"
    bindir.mkdir(parents=True, exist_ok=True)
    log = tmp_path / "_git-calls.log"
    log.write_text("", encoding="utf-8")
    shim = bindir / "git"
    shim.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{log}"\n'
        f'exec "{real_git}" "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
    return env, log


def audit_calls(log: pathlib.Path) -> list[str]:
    return [line for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def assert_no_destructive_git(log: pathlib.Path, label: str) -> None:
    """`reset --hard`·worktree 전체 restore·clean·checkout 전체 복원 호출 0을 단언한다."""
    calls = audit_calls(log)
    assert calls, (
        f"{label}: git audit shim이 호출을 하나도 기록하지 못했다. "
        "Checkpoint Tool은 감사 가능하도록 PATH의 `git`을 호출해야 한다(절대경로 우회 금지)."
    )
    violations = [
        call for call in calls if any(pattern.search(call) for pattern in FORBIDDEN_GIT_CALL_PATTERNS)
    ]
    assert violations == [], f"{label}: 금지된 파괴적 git 호출이 발생했다: {violations}"


# ─────────────────────────────────────────────────────────────────────────────
# git 상태 지문 — ref·HEAD·공유 index·lease path hash 불변을 독립 기제로 관측한다.
# ─────────────────────────────────────────────────────────────────────────────


def git_fingerprint(repo: pathlib.Path) -> dict:
    return {
        "branch_sha": run_git(["rev-parse", "refs/heads/main"], cwd=repo).stdout.strip(),
        "head_sha": run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip(),
        "head_ref": run_git(["symbolic-ref", "-q", "HEAD"], cwd=repo, check=False).stdout.strip(),
        "index": run_git(["ls-files", "-s"], cwd=repo).stdout,
        "reflog": run_git(["reflog", "show", "main"], cwd=repo, check=False).stdout,
    }


def path_hash(repo: pathlib.Path, relpath: str) -> str:
    path = repo / relpath
    if not path.exists():
        return "<absent>"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_hub_repo(base: pathlib.Path, name: str = "hub") -> pathlib.Path:
    repo = base / name
    repo.mkdir(parents=True)
    run_git(["init", "-b", "main", "."], cwd=repo)
    _write(repo, "README.md", "# hub\n")
    run_git(["add", "README.md"], cwd=repo)
    run_git(["commit", "-m", "init"], cwd=repo)
    return repo


def make_project_worktree(base: pathlib.Path, name: str = "project") -> pathlib.Path:
    """프로젝트 worktree fixture — 두 Runner lease 경로와 공유 지식 파일을 가진 실 저장소."""
    repo = base / name
    repo.mkdir(parents=True)
    run_git(["init", "-b", "main", "."], cwd=repo)
    _write(repo, "src/users/service.py", "USERS = 1\n")
    _write(repo, "src/orders/service.py", "ORDERS = 1\n")
    _write(repo, "src/shared/frozen.py", "FROZEN = True\n")
    _write(repo, "MEMORY.md", "# memory\n")
    run_git(["add", "-A"], cwd=repo)
    run_git(["commit", "-m", "project seed"], cwd=repo)
    return repo


def init_run(repo: pathlib.Path, project: pathlib.Path, env: dict | None = None) -> dict:
    result = run_oppb(
        ["init", "--allocator-root", str(repo), "--project-root", str(project)], env=env
    )
    assert result.returncode == 0, (
        f"init 실패: exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    payload = parse_json_stdout(result, "init")
    for key in ("run_id", "run_root", "cache_root"):
        assert key in payload, f"init 응답에 {key} 없음: {payload}"
    return payload


def lease_spec(tmp_path: pathlib.Path, task_id: str, tracked: list[str]) -> pathlib.Path:
    return write_json(
        tmp_path / f"spec_{task_id}.json",
        {
            "task_id": task_id,
            "capability_id": f"cap-{task_id}",
            "tracked_write_set": tracked,
            "ephemeral_write_set": [],
            "contracts": [],
            "business_rules": [],
            "acceptance_ids": [f"ACC-{task_id}"],
            "runtime_resources": [f"port:59{task_id[-2:]}"],
            "global_outputs": [],
        },
    )


def acquire(run_root: str, spec: pathlib.Path, attempt: str, env: dict | None = None) -> dict:
    return parse_json_stdout(
        run_oppb(
            ["lease", "acquire", "--run-root", run_root, "--spec", str(spec), "--attempt", attempt],
            env=env,
        ),
        f"lease acquire({spec.name})",
    )


def make_candidate(
    run_root: str, repo: pathlib.Path, task: str, attempt: str, env: dict, extra: list | None = None
) -> dict:
    args = [
        "checkpoint",
        "candidate",
        "--run-root",
        run_root,
        "--project-root",
        str(repo),
        "--task",
        task,
        "--attempt",
        attempt,
    ]
    args.extend(extra or [])
    return parse_json_stdout(run_oppb(args, env=env), f"checkpoint candidate({task}/{attempt})")


def publish(
    run_root: str, repo: pathlib.Path, candidate_id: str, verification: str, env: dict
) -> dict:
    return parse_json_stdout(
        run_oppb(
            [
                "checkpoint",
                "publish",
                "--run-root",
                run_root,
                "--project-root",
                str(repo),
                "--candidate",
                candidate_id,
                "--verification",
                verification,
            ],
            env=env,
        ),
        f"checkpoint publish({candidate_id},{verification})",
    )


@pytest.fixture
def cp_env(tmp_path: pathlib.Path):
    """허브 + init된 run root + 프로젝트 worktree + git audit shim + 두 Runner lease."""
    env, log = install_git_audit_shim(tmp_path)
    hub = make_hub_repo(tmp_path)
    repo = make_project_worktree(tmp_path)
    run_root = init_run(hub, repo, env=env)["run_root"]

    spec_users = lease_spec(tmp_path, "T01", ["src/users/service.py"])
    spec_orders = lease_spec(tmp_path, "T02", ["src/orders/service.py"])
    assert acquire(run_root, spec_users, "a1", env=env).get("ok") is True
    assert acquire(run_root, spec_orders, "b1", env=env).get("ok") is True

    return {
        "env": env,
        "log": log,
        "run_root": run_root,
        "repo": repo,
        "spec_users": spec_users,
        "spec_orders": spec_orders,
    }


# ═════════════════════════════════════════════════════════════════════════════
# S-12 checkpoint 구간: Runner Git 상태 변경·lease 밖 쓰기 → checkpoint 거부 (수용기준 6·7)
# ═════════════════════════════════════════════════════════════════════════════


def test_s12_1_out_of_lease_write_is_rejected(cp_env):
    """[T132/S-12] Runner가 자기 lease 밖 tracked 파일을 수정하면 checkpoint가 거부된다.
    다른 Runner의 미완료 변경을 candidate commit에 포함한 건수는 0이어야 한다(수용기준 7)."""
    repo, run_root, env, log = cp_env["repo"], cp_env["run_root"], cp_env["env"], cp_env["log"]
    before = git_fingerprint(repo)

    _write(repo, "src/users/service.py", "USERS = 2\n")  # 자기 lease — 허용
    _write(repo, "src/orders/service.py", "ORDERS = 999\n")  # 타 Runner lease — 위반

    payload = make_candidate(run_root, repo, "T01", "a1", env)

    assert payload.get("ok") is False, f"lease 밖 쓰기인데 candidate가 만들어졌다: {payload}"
    assert payload.get("error") == "CHECKPOINT_REJECTED", payload
    assert "out_of_lease_write" in payload.get("reasons", []), payload
    assert "src/orders/service.py" in payload.get("violating_paths", []), payload

    after = git_fingerprint(repo)
    assert after == before, f"거부 경로가 Git 상태를 바꿨다: {before} -> {after}"
    assert_no_destructive_git(log, "S-12 lease 밖 쓰기 거부")


def test_s12_1a_pure_out_of_lease_write_without_own_write_is_rejected(cp_env):
    """[T132/S-12] 호출 attempt가 **자기 lease 경로를 전혀 건드리지 않고** lease 밖만
    수정한 경우 — 가장 전형적인 scope_violation — 도 checkpoint가 거부해야 한다.
    귀속이 자기 lease 쓰기 시점(own_marker)에만 의존하면 own이 공집합일 때 위반이
    하나도 검출되지 않는다(구조적 false negative). 순수 이탈은 lease 계약상 항상
    위반이다(수용기준 6·7, 제안서 §4.5)."""
    repo, run_root, env, log = cp_env["repo"], cp_env["run_root"], cp_env["env"], cp_env["log"]
    before = git_fingerprint(repo)

    # 자기 lease(src/users/service.py)는 손대지 않는다 — lease 밖만 쓴다.
    _write(repo, "src/orders/service.py", "ORDERS = 999\n")

    payload = make_candidate(run_root, repo, "T01", "a1", env)

    assert payload.get("ok") is False, (
        f"자기 lease 쓰기 없이 lease 밖만 썼는데 candidate가 만들어졌다: {payload}"
    )
    assert payload.get("error") == "CHECKPOINT_REJECTED", payload
    assert "out_of_lease_write" in payload.get("reasons", []), payload
    assert "src/orders/service.py" in payload.get("violating_paths", []), payload

    after = git_fingerprint(repo)
    assert after == before, f"거부 경로가 Git 상태를 바꿨다: {before} -> {after}"
    assert_no_destructive_git(log, "S-12 순수 lease 이탈 거부")


def test_s12_1b_out_of_lease_delete_is_rejected(cp_env):
    """[T132/S-12] lease 밖 tracked 파일 **삭제**도 lease 밖 쓰기다. 삭제 경로는 stat이
    불가능해 mtime 관측이 성립하지 않으므로, mtime 대소 비교에만 의존하는 귀속은
    삭제를 구조적으로 절대 귀속하지 못한다. 삭제는 그 자체로 거부 사유여야 한다
    (수용기준 6·7, 제안서 §4.5)."""
    repo, run_root, env, log = cp_env["repo"], cp_env["run_root"], cp_env["env"], cp_env["log"]
    before = git_fingerprint(repo)

    _write(repo, "src/users/service.py", "USERS = 2\n")  # 자기 lease — 허용
    (repo / "src/orders/service.py").unlink()  # 타 Runner lease tracked 파일 삭제 — 위반
    assert not (repo / "src/orders/service.py").exists()

    payload = make_candidate(run_root, repo, "T01", "a1", env)

    assert payload.get("ok") is False, f"lease 밖 삭제인데 candidate가 만들어졌다: {payload}"
    assert payload.get("error") == "CHECKPOINT_REJECTED", payload
    assert "out_of_lease_write" in payload.get("reasons", []), payload
    assert "src/orders/service.py" in payload.get("violating_paths", []), payload

    after = git_fingerprint(repo)
    assert after == before, f"거부 경로가 Git 상태를 바꿨다: {before} -> {after}"
    assert_no_destructive_git(log, "S-12 lease 밖 삭제 거부")


@pytest.mark.parametrize(
    "label,git_args",
    [
        ("commit", ["commit", "-am", "runner commit"]),
        ("checkout", ["checkout", "-b", "runner-branch"]),
        ("reset", ["reset", "--soft", "HEAD~0"]),
    ],
)
def test_s12_2_runner_git_state_change_is_rejected(cp_env, label, git_args):
    """[T132/S-12] 프로젝트 worktree의 Git writer는 Checkpoint Tool 하나다. Runner가
    commit·checkout·reset을 실행하면 HEAD·index tree·reflog fingerprint 비교로 감지되어
    checkpoint가 거부된다(제안서 §4.5, PLAN W-14)."""
    repo, run_root, env, log = cp_env["repo"], cp_env["run_root"], cp_env["env"], cp_env["log"]

    _write(repo, "src/users/service.py", "USERS = 2\n")
    baseline = parse_json_stdout(
        run_oppb(
            [
                "checkpoint",
                "guard",
                "--run-root",
                run_root,
                "--project-root",
                str(repo),
                "--task",
                "T01",
                "--attempt",
                "a1",
                "--record-baseline",
            ],
            env=env,
        ),
        "checkpoint guard --record-baseline",
    )
    assert baseline.get("ok") is True, f"baseline 지문 기록 실패: {baseline}"

    run_git(git_args, cwd=repo)  # Runner가 Git 상태를 직접 바꾼다

    payload = make_candidate(run_root, repo, "T01", "a1", env)
    assert payload.get("ok") is False, f"Runner {label} 후 candidate가 만들어졌다: {payload}"
    assert payload.get("error") == "CHECKPOINT_REJECTED", payload
    assert "git_state_changed" in payload.get("reasons", []), payload
    assert_no_destructive_git(log, f"S-12 Runner {label} 거부")


def test_s12_3_shared_knowledge_write_is_rejected(cp_env):
    """[T132/S-12] 공유 지식(MEMORY·brain) 쓰기는 Runner의 권한이 아니다 — 감지되면
    checkpoint가 거부된다(수용기준 6)."""
    repo, run_root, env, log = cp_env["repo"], cp_env["run_root"], cp_env["env"], cp_env["log"]
    _write(repo, "src/users/service.py", "USERS = 2\n")
    _write(repo, "MEMORY.md", "# memory\nrunner wrote here\n")

    payload = make_candidate(run_root, repo, "T01", "a1", env)
    assert payload.get("ok") is False, payload
    assert payload.get("error") == "CHECKPOINT_REJECTED", payload
    assert "shared_knowledge_write" in payload.get("reasons", []), payload
    assert_no_destructive_git(log, "S-12 공유 지식 쓰기 거부")


def test_s12_3a_shared_knowledge_write_before_lease_write_is_rejected(cp_env):
    """[T132/S-12] 공유 지식 축은 **쓰기 순서와 무관하게** 닫힌다. attempt가 MEMORY·brain을
    **먼저** 쓰고 자기 lease 경로를 나중에 써도 거부된다 — Runner가 공유 지식을 정당하게
    쓰는 경우 자체가 없으므로(제안서 §4.3 capability agent 행동 계약, §5 P5는 지식 반영을
    Project Knowledge Finalizer 1회로 한정) 귀속 판정 이전에 dirty 존재만으로 위반이다.
    lease 밖 **소스** 경로에 남는 mtime 순서 역전 한계와 달리 이 축에는 한계가 없다
    (수용기준 6)."""
    repo, run_root, env, log = cp_env["repo"], cp_env["run_root"], cp_env["env"], cp_env["log"]
    before = git_fingerprint(repo)

    # 순서 역전 — 공유 지식을 **먼저**, 자기 lease 경로를 **나중에** 쓴다.
    _write(repo, "MEMORY.md", "# memory\nrunner wrote here first\n")
    _write(repo, "brain/notes.md", "runner wrote brain first\n")
    _write(repo, "src/users/service.py", "USERS = 2\n")

    payload = make_candidate(run_root, repo, "T01", "a1", env)
    assert payload.get("ok") is False, f"공유 지식 선행 쓰기 후 candidate가 만들어졌다: {payload}"
    assert payload.get("error") == "CHECKPOINT_REJECTED", payload
    assert "shared_knowledge_write" in payload.get("reasons", []), payload
    violating = payload.get("violating_paths", [])
    assert "MEMORY.md" in violating, f"MEMORY.md가 violating_paths에 없다: {payload}"
    assert "brain/notes.md" in violating, f"brain/notes.md가 violating_paths에 없다: {payload}"

    after = git_fingerprint(repo)
    assert after["branch_sha"] == before["branch_sha"], "거부가 project branch를 움직였다."
    assert after["head_sha"] == before["head_sha"], "거부가 HEAD를 움직였다."
    assert after["index"] == before["index"], "거부가 공유 index를 바꿨다."
    assert after["reflog"] == before["reflog"], "거부가 reflog를 남겼다(되돌림 흔적)."
    assert_no_destructive_git(log, "S-12 공유 지식 선행 쓰기 거부")


def test_s12_4_candidate_creation_does_not_move_ref_or_head(cp_env):
    """[T132/S-12] candidate 생성은 임시 index + `commit-tree`로 수행하며 project branch
    ref·HEAD·공유 index를 움직이지 않는다. lease 경로만 후보 tree에 들어간다(제안서 §4.5)."""
    repo, run_root, env, log = cp_env["repo"], cp_env["run_root"], cp_env["env"], cp_env["log"]
    before = git_fingerprint(repo)

    _write(repo, "src/users/service.py", "USERS = 2\n")
    payload = make_candidate(run_root, repo, "T01", "a1", env)
    assert payload.get("ok") is True, f"정상 candidate 생성 실패: {payload}"

    for key in ("candidate_id", "candidate_commit", "parent", "tree", "receipt_path"):
        assert payload.get(key), f"candidate 응답에 {key}가 없다: {payload}"
    assert payload.get("parent") == before["head_sha"], payload
    assert payload.get("lease_path_hashes"), f"receipt용 lease path hash가 없다: {payload}"

    after = git_fingerprint(repo)
    assert after["branch_sha"] == before["branch_sha"], "candidate 생성이 branch ref를 움직였다."
    assert after["head_sha"] == before["head_sha"], "candidate 생성이 HEAD를 움직였다."
    assert after["index"] == before["index"], "candidate 생성이 공유 index를 바꿨다."

    # 후보 tree에는 이 lease 경로만 들어간다 — 타 Runner 경로 포함 0 (수용기준 7).
    listed = run_git(
        ["diff-tree", "--no-commit-id", "--name-only", "-r", payload["candidate_commit"]],
        cwd=repo,
    ).stdout.split()
    assert listed == ["src/users/service.py"], f"후보 tree에 lease 밖 경로가 섞였다: {listed}"
    assert_no_destructive_git(log, "S-12 정상 candidate 생성")


# ═════════════════════════════════════════════════════════════════════════════
# S-13: publication — 실패 폐기·통과 fast-forward·stale 재생성 (수용기준 30·31)
# ═════════════════════════════════════════════════════════════════════════════


def test_s13_1_failed_candidate_is_discarded_without_touching_branch(cp_env):
    """[T132/S-13] 검증 실패 candidate는 **폐기만** 된다. project branch·HEAD·공유 index와
    다른 Runner lease path hash가 전부 불변이고 `reset --hard` 호출 0이다(수용기준 30,
    제안서 §4.5 "실패하면 candidate를 폐기할 뿐 branch·HEAD·공유 index를 되돌리지 않는다")."""
    repo, run_root, env, log = cp_env["repo"], cp_env["run_root"], cp_env["env"], cp_env["log"]

    # 다른 Runner(T02)는 자기 lease 경로에서 작업 중이다 — 이 값이 변하면 안 된다.
    _write(repo, "src/orders/service.py", "ORDERS = 2\n")
    other_hash_before = path_hash(repo, "src/orders/service.py")

    _write(repo, "src/users/service.py", "USERS = 2\n")
    candidate = make_candidate(run_root, repo, "T01", "a1", env)
    assert candidate.get("ok") is True, candidate
    before = git_fingerprint(repo)

    payload = publish(run_root, repo, candidate["candidate_id"], "fail", env)

    assert payload.get("ok") is False, f"실패 candidate가 publish됐다: {payload}"
    assert payload.get("error") == "CANDIDATE_DISCARDED", payload
    assert payload.get("branch_advanced") is False, payload

    after = git_fingerprint(repo)
    assert after["branch_sha"] == before["branch_sha"], "실패 폐기가 project branch를 움직였다."
    assert after["head_sha"] == before["head_sha"], "실패 폐기가 HEAD를 움직였다."
    assert after["index"] == before["index"], "실패 폐기가 공유 index를 바꿨다."
    assert after["reflog"] == before["reflog"], "실패 폐기가 reflog를 남겼다(되돌림 흔적)."
    assert path_hash(repo, "src/orders/service.py") == other_hash_before, (
        "실패 폐기가 다른 Runner lease의 path hash를 바꿨다."
    )
    assert_no_destructive_git(log, "S-13 검증 실패 candidate 폐기")


def test_s13_2_passing_candidate_fast_forwards_after_parent_match(cp_env):
    """[T132/S-13] 모든 검증이 통과한 경우에만 parent가 여전히 branch head인지 확인하고
    candidate commit으로 원자적 fast-forward한다. 승인 lease 경로만 공유 index에 정합된다
    (수용기준 31, 제안서 §4.5 M3 ACCEPT 9)."""
    repo, run_root, env, log = cp_env["repo"], cp_env["run_root"], cp_env["env"], cp_env["log"]
    before = git_fingerprint(repo)

    _write(repo, "src/users/service.py", "USERS = 2\n")
    candidate = make_candidate(run_root, repo, "T01", "a1", env)
    assert candidate.get("ok") is True, candidate

    payload = publish(run_root, repo, candidate["candidate_id"], "pass", env)

    assert payload.get("ok") is True, f"통과 candidate의 publication 실패: {payload}"
    assert payload.get("fast_forward") is True, payload
    assert payload.get("expected_parent") == before["head_sha"], payload
    assert payload.get("new_head") == candidate["candidate_commit"], payload

    after = git_fingerprint(repo)
    assert after["branch_sha"] == candidate["candidate_commit"], (
        f"fast-forward가 반영되지 않았다: {after['branch_sha']}"
    )
    assert (
        run_git(["rev-list", "--count", f"{before['head_sha']}..{after['branch_sha']}"], cwd=repo)
        .stdout.strip()
        == "1"
    ), "fast-forward가 아니라 별도 merge commit이 생겼다."
    assert_no_destructive_git(log, "S-13 통과 candidate fast-forward")


def test_s13_3_stale_parent_candidate_is_not_applied_and_is_regenerated(cp_env):
    """[T132/S-13] parent가 이미 전진했으면 candidate의 publication 자격은 stale로 폐기되고
    새 parent에서 다시 만든다 — stale parent candidate 반영 0(수용기준 31)."""
    repo, run_root, env, log = cp_env["repo"], cp_env["run_root"], cp_env["env"], cp_env["log"]

    _write(repo, "src/users/service.py", "USERS = 2\n")
    stale = make_candidate(run_root, repo, "T01", "a1", env)
    assert stale.get("ok") is True, stale
    old_parent = stale["parent"]

    # 다른 capability가 먼저 publication에 성공해 parent가 전진한다.
    _write(repo, "src/orders/service.py", "ORDERS = 2\n")
    winner = make_candidate(run_root, repo, "T02", "b1", env)
    assert winner.get("ok") is True, winner
    assert publish(run_root, repo, winner["candidate_id"], "pass", env).get("ok") is True
    advanced_head = git_fingerprint(repo)["branch_sha"]
    assert advanced_head != old_parent

    payload = publish(run_root, repo, stale["candidate_id"], "pass", env)
    assert payload.get("ok") is False, f"stale parent candidate가 반영됐다: {payload}"
    assert payload.get("error") == "STALE_PARENT", payload
    assert payload.get("applied") is False, payload
    assert payload.get("expected_parent") == old_parent, payload
    assert payload.get("actual_parent") == advanced_head, payload
    assert git_fingerprint(repo)["branch_sha"] == advanced_head, "stale publish가 branch를 바꿨다."

    regenerated = make_candidate(run_root, repo, "T01", "a1", env, extra=["--regenerate"])
    assert regenerated.get("ok") is True, f"새 parent에서 재생성 실패: {regenerated}"
    assert regenerated.get("parent") == advanced_head, regenerated
    assert regenerated.get("candidate_id") != stale["candidate_id"], regenerated
    assert_no_destructive_git(log, "S-13 stale parent 재생성")
