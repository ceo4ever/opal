"""
@header {
  "module": "test_recovery",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "oppb-runtime-tool recover 공개 CLI 계약 RED 테스트. 132 TEST-SCENARIO.md S-12 복구 구간(AC-7)과 S-16 PROVE 실패 귀속 구간(AC-7)을 검증한다 — 단독 범위 이탈은 declared+actual path 합집합을 해당 attempt preimage로만 복구하고, 두 attempt가 같은 경로를 덮어 귀속 불가이면 연결 성분 process를 모두 종료한 뒤 path-scoped 복구하며, worktree 전체 reset·clean을 쓰지 않고 복구 전후 path hash와 종료 process 목록을 receipt로 남기고, 무관한 accepted 결과와 lease는 불변이다. 또 다른 active lease가 dirty인 상태의 PROVE 실패는 자기 candidate snapshot에서 즉시 재검증되어 대기 굶주림·오귀속 0이고 Repair 예산을 차감하지 않는다. S-16의 needs_revalidation 전파 구간은 W-28의 test_revalidation.py가 소유하므로 여기서 다루지 않는다. reset --hard·전체 restore 금지는 PATH 앞단 git audit shim 호출 추적과 reflog 대조라는 두 독립 기제로 기계 단언한다(제안서 §4.5·§P2.2 scope_violation 회수). PLAN H-6에 따라 내부 함수·클래스를 import하지 않고 공개 CLI(run.sh)와 run root 파일 계약으로만 검증한다. mock/patch 금지 — 실제 git 저장소·실제 프로세스만 사용한다(PLAN W-17).",
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
import sys
import time

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

# 제안서 §P2.2 "복구 과정은 worktree 전체 reset·clean을 사용하지 않는다."
FORBIDDEN_GIT_CALL_PATTERNS = (
    re.compile(r"\breset\b.*--hard"),
    re.compile(r"\bcheckout\b\s+(-f\s+)?--\s*$"),
    re.compile(r"\bcheckout\b.*--\s+\.\s*$"),
    re.compile(r"\brestore\b(?!.*\s--\s+\S)"),
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
    """공개 인터페이스(run.sh 서브프로세스)로만 호출한다. run.sh·recover 하위명령이 아직
    없으면(W-6·W-16 구현 전) 이 실패가 RED 증거다."""
    if not RUN_SH.exists():
        pytest.fail(
            "RED: opal/tools/oppb-runtime-tool/run.sh 미존재 — W-6·W-16 구현 전 정상 실패. "
            f"요청 명령: run.sh {' '.join(args)}"
        )
    return subprocess.run(
        ["bash", str(RUN_SH), *args], capture_output=True, text=True, timeout=timeout, env=env
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


def path_hash(repo: pathlib.Path, relpath: str) -> str:
    path = repo / relpath
    if not path.exists():
        return "<absent>"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_git_audit_shim(tmp_path: pathlib.Path) -> tuple[dict, pathlib.Path]:
    """PATH 앞단에 실행 로그를 남기는 진짜 git wrapper를 둔다 — 도구를 mock하지 않는다."""
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
    calls = audit_calls(log)
    assert calls, (
        f"{label}: git audit shim이 호출을 하나도 기록하지 못했다. "
        "복구 도구는 감사 가능하도록 PATH의 `git`을 호출해야 한다(절대경로 우회 금지)."
    )
    violations = [
        call
        for call in calls
        if any(pattern.search(call) for pattern in FORBIDDEN_GIT_CALL_PATTERNS)
    ]
    assert violations == [], f"{label}: 금지된 전체 reset·clean·restore 호출이 발생했다: {violations}"


def git_fingerprint(repo: pathlib.Path) -> dict:
    return {
        "branch_sha": run_git(["rev-parse", "refs/heads/main"], cwd=repo).stdout.strip(),
        "head_sha": run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip(),
        "reflog": run_git(["reflog", "show", "main"], cwd=repo, check=False).stdout,
    }


def make_hub_repo(base: pathlib.Path, name: str = "hub") -> pathlib.Path:
    repo = base / name
    repo.mkdir(parents=True)
    run_git(["init", "-b", "main", "."], cwd=repo)
    _write(repo, "README.md", "# hub\n")
    run_git(["add", "README.md"], cwd=repo)
    run_git(["commit", "-m", "init"], cwd=repo)
    return repo


def make_project_worktree(base: pathlib.Path, name: str = "project") -> pathlib.Path:
    """세 capability lease 경로와 공유 경로를 가진 실 git 프로젝트 worktree."""
    repo = base / name
    repo.mkdir(parents=True)
    run_git(["init", "-b", "main", "."], cwd=repo)
    _write(repo, "src/users/service.py", "USERS = 1\n")
    _write(repo, "src/orders/service.py", "ORDERS = 1\n")
    _write(repo, "src/reports/service.py", "REPORTS = 1\n")
    _write(repo, "src/shared/contested.py", "CONTESTED = 0\n")
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


def lease_spec(base: pathlib.Path, task_id: str, tracked: list[str]) -> pathlib.Path:
    return write_json(
        base / f"spec_{task_id}.json",
        {
            "task_id": task_id,
            "capability_id": f"cap-{task_id}",
            "tracked_write_set": tracked,
            "ephemeral_write_set": [],
            "contracts": [],
            "business_rules": [],
            "acceptance_ids": [f"ACC-{task_id}"],
            "runtime_resources": [f"port:60{task_id[-2:]}"],
            "global_outputs": [],
        },
    )


def acquire(run_root: str, spec: pathlib.Path, attempt: str, env: dict) -> dict:
    return parse_json_stdout(
        run_oppb(
            ["lease", "acquire", "--run-root", run_root, "--spec", str(spec), "--attempt", attempt],
            env=env,
        ),
        f"lease acquire({spec.name})",
    )


def lease_snapshot(run_root: str, env: dict) -> list:
    payload = parse_json_stdout(
        run_oppb(["lease", "list", "--run-root", run_root], env=env), "lease list"
    )
    assert payload.get("ok") is True, payload
    return sorted(
        (lease.get("task_id"), lease.get("state"), tuple(sorted(lease.get("paths", []))))
        for lease in payload.get("leases", [])
    )


def register_attempt(run_root: str, task: str, attempt: str, pid: int, env: dict) -> dict:
    """실행 중 attempt를 run root에 등록한다 — 연결 성분 종료 대상 판정 입력."""
    return parse_json_stdout(
        run_oppb(
            [
                "recover",
                "register-attempt",
                "--run-root",
                run_root,
                "--task",
                task,
                "--attempt",
                attempt,
                "--pid",
                str(pid),
            ],
            env=env,
        ),
        f"recover register-attempt({task}/{attempt})",
    )


def spawn_attempt_process(marker: pathlib.Path) -> subprocess.Popen:
    """실제 장수명 자식 프로세스 — 연결 성분 종료가 진짜로 일어나는지 관측하기 위한 것."""
    script = (
        "import pathlib, sys, time\n"
        "pathlib.Path(sys.argv[1]).write_text('alive', encoding='utf-8')\n"
        "time.sleep(120)\n"
    )
    proc = subprocess.Popen([sys.executable, "-c", script, str(marker)])
    deadline = time.time() + 10
    while time.time() < deadline and not marker.exists():
        time.sleep(0.05)
    assert marker.exists(), "attempt 프로세스가 기동하지 못했다."
    return proc


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@pytest.fixture
def rec_env(tmp_path: pathlib.Path):
    env, log = install_git_audit_shim(tmp_path)
    hub = make_hub_repo(tmp_path)
    repo = make_project_worktree(tmp_path)
    run_root = init_run(hub, repo, env=env)["run_root"]

    specs = {
        "T01": lease_spec(tmp_path, "T01", ["src/users/service.py", "src/shared/contested.py"]),
        "T02": lease_spec(tmp_path, "T02", ["src/orders/service.py"]),
        "T03": lease_spec(tmp_path, "T03", ["src/reports/service.py"]),
    }
    return {
        "tmp": tmp_path,
        "env": env,
        "log": log,
        "run_root": run_root,
        "repo": repo,
        "specs": specs,
    }


def violation_input(
    base: pathlib.Path,
    name: str,
    *,
    task: str,
    attempt: str,
    declared_paths: list[str],
    actual_paths: list[str],
    attributable: bool,
) -> pathlib.Path:
    return write_json(
        base / f"violation_{name}.json",
        {
            "violating_task": task,
            "violating_attempt": attempt,
            "declared_paths": declared_paths,
            "actual_paths": actual_paths,
            "attributable": attributable,
            "violated_contracts": [],
            "violated_resources": [],
        },
    )


def recover_scope_violation(
    run_root: str, repo: pathlib.Path, violation: pathlib.Path, env: dict
) -> dict:
    return parse_json_stdout(
        run_oppb(
            [
                "recover",
                "scope-violation",
                "--run-root",
                run_root,
                "--project-root",
                str(repo),
                "--violation",
                str(violation),
            ],
            env=env,
        ),
        "recover scope-violation",
    )


# ═════════════════════════════════════════════════════════════════════════════
# S-12 복구 구간: 단독 이탈 → attempt preimage 복구 (수용기준 19, 제안서 §P2.2 2)
# ═════════════════════════════════════════════════════════════════════════════


def test_s12_5_solo_deviation_restores_only_that_attempt_preimage(rec_env):
    """[T132/S-12] 단독 범위 이탈이면 위반 attempt만 종료하고 declared+actual path의
    **합집합**을 그 attempt preimage로 복구한다. 무관한 accepted 결과와 lease는 유지된다."""
    repo, run_root, env, log = rec_env["repo"], rec_env["run_root"], rec_env["env"], rec_env["log"]
    tmp = rec_env["tmp"]
    for task, attempt in (("T01", "a1"), ("T02", "b1"), ("T03", "c1")):
        assert acquire(run_root, rec_env["specs"][task], attempt, env).get("ok") is True

    sealed = parse_json_stdout(
        run_oppb(
            [
                "recover",
                "seal-preimage",
                "--run-root",
                run_root,
                "--project-root",
                str(repo),
                "--task",
                "T01",
                "--attempt",
                "a1",
            ],
            env=env,
        ),
        "recover seal-preimage(T01/a1)",
    )
    assert sealed.get("ok") is True, sealed

    # T01이 선언 밖 경로(src/reports/service.py)까지 건드린다 — 단독 이탈.
    _write(repo, "src/users/service.py", "USERS = 2\n")
    _write(repo, "src/reports/service.py", "REPORTS = 999\n")
    # T02는 자기 lease 안에서 정상 작업 중이다 — 복구가 건드리면 안 된다.
    _write(repo, "src/orders/service.py", "ORDERS = 2\n")
    orders_hash = path_hash(repo, "src/orders/service.py")
    before_git = git_fingerprint(repo)
    before_leases = lease_snapshot(run_root, env)

    payload = recover_scope_violation(
        run_root,
        repo,
        violation_input(
            tmp,
            "solo",
            task="T01",
            attempt="a1",
            declared_paths=["src/users/service.py", "src/shared/contested.py"],
            actual_paths=["src/users/service.py", "src/reports/service.py"],
            attributable=True,
        ),
        env,
    )

    assert payload.get("ok") is True, f"단독 이탈 복구 실패: {payload}"
    assert payload.get("attribution") == "solo", payload
    restored = set(payload.get("restored_paths", []))
    assert restored == {
        "src/users/service.py",
        "src/shared/contested.py",
        "src/reports/service.py",
    }, f"declared+actual 합집합이 복구되지 않았다: {sorted(restored)}"
    assert payload.get("halted_attempts") == ["T01/a1"], payload

    assert path_hash(repo, "src/users/service.py") == hashlib.sha256(b"USERS = 1\n").hexdigest(), (
        "위반 attempt 경로가 preimage로 복구되지 않았다."
    )
    assert (
        path_hash(repo, "src/reports/service.py") == hashlib.sha256(b"REPORTS = 1\n").hexdigest()
    ), "실제 이탈 경로가 preimage로 복구되지 않았다."
    assert path_hash(repo, "src/orders/service.py") == orders_hash, (
        "무관한 attempt(T02)의 작업이 복구에 휩쓸렸다."
    )
    assert git_fingerprint(repo) == before_git, "복구가 branch·HEAD·reflog를 바꿨다."
    assert lease_snapshot(run_root, env) == before_leases, "무관한 lease가 변경됐다."
    assert_no_destructive_git(log, "S-12 단독 이탈 복구")


def test_s12_6_recovery_receipt_records_path_hashes_and_terminated_processes(rec_env):
    """[T132/S-12] 복구 전후 path hash와 종료한 process 목록을 receipt로 남긴다
    (제안서 §P2.2 "복구 과정은 ... receipt로 남긴다")."""
    repo, run_root, env = rec_env["repo"], rec_env["run_root"], rec_env["env"]
    tmp = rec_env["tmp"]
    assert acquire(run_root, rec_env["specs"]["T01"], "a1", env).get("ok") is True
    run_oppb(
        [
            "recover",
            "seal-preimage",
            "--run-root",
            run_root,
            "--project-root",
            str(repo),
            "--task",
            "T01",
            "--attempt",
            "a1",
        ],
        env=env,
    )
    proc = spawn_attempt_process(tmp / "marker_a1.txt")
    try:
        register_attempt(run_root, "T01", "a1", proc.pid, env)
        _write(repo, "src/users/service.py", "USERS = 2\n")

        payload = recover_scope_violation(
            run_root,
            repo,
            violation_input(
                tmp,
                "receipt",
                task="T01",
                attempt="a1",
                declared_paths=["src/users/service.py"],
                actual_paths=["src/users/service.py"],
                attributable=True,
            ),
            env,
        )
    finally:
        if proc.poll() is None:
            proc.terminate()
        proc.wait(timeout=10)

    assert payload.get("ok") is True, payload
    receipt_path = pathlib.Path(payload.get("receipt_path", ""))
    assert receipt_path.is_file(), f"복구 receipt 파일이 없다: {payload}"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt.get("path_hashes_before"), f"복구 전 path hash가 없다: {receipt}"
    assert receipt.get("path_hashes_after"), f"복구 후 path hash가 없다: {receipt}"
    assert "src/users/service.py" in receipt["path_hashes_before"], receipt
    assert proc.pid in receipt.get("terminated_pids", []), (
        f"종료한 process 목록에 실제 PID가 없다: {receipt.get('terminated_pids')}"
    )
    assert receipt.get("reset_hard_calls") == 0, receipt
    assert receipt.get("worktree_restore_calls") == 0, receipt


# ═════════════════════════════════════════════════════════════════════════════
# S-12 복구 구간: 귀속 불가 → 연결 성분만 중단·path-scoped 복구 (제안서 §P2.2 3)
# ═════════════════════════════════════════════════════════════════════════════


def test_s12_7_unattributable_overlap_halts_only_connected_component(rec_env):
    """[T132/S-12] 두 attempt가 같은 경로를 덮어 귀속할 수 없으면 **연결 성분의 process를
    모두 종료**하고 영향 경로만 마지막 accepted head 또는 봉인 preimage로 path-scoped
    복구한다. 연결 성분 밖의 무관한 attempt·lease·결과는 불변이다(수용기준 19)."""
    repo, run_root, env, log = rec_env["repo"], rec_env["run_root"], rec_env["env"], rec_env["log"]
    tmp = rec_env["tmp"]
    for task, attempt in (("T01", "a1"), ("T02", "b1"), ("T03", "c1")):
        assert acquire(run_root, rec_env["specs"][task], attempt, env).get("ok") is True

    procs = {}
    for task, attempt in (("T01", "a1"), ("T02", "b1"), ("T03", "c1")):
        proc = spawn_attempt_process(tmp / f"marker_{task}_{attempt}.txt")
        procs[f"{task}/{attempt}"] = proc
        register_attempt(run_root, task, attempt, proc.pid, env)

    try:
        # T01과 T02가 같은 경로를 덮었다 — 어느 쪽 변경인지 귀속 불가.
        _write(repo, "src/shared/contested.py", "CONTESTED = 2\n")
        # T03은 완전히 무관한 경로에서 작업 중이다.
        _write(repo, "src/reports/service.py", "REPORTS = 7\n")
        reports_hash = path_hash(repo, "src/reports/service.py")
        before_git = git_fingerprint(repo)

        payload = recover_scope_violation(
            run_root,
            repo,
            violation_input(
                tmp,
                "overlap",
                task="T01",
                attempt="a1",
                declared_paths=["src/shared/contested.py"],
                actual_paths=["src/shared/contested.py"],
                attributable=False,
            ),
            env,
        )

        assert payload.get("ok") is True, f"귀속 불가 복구 실패: {payload}"
        assert payload.get("attribution") == "unattributable", payload
        halted = set(payload.get("halted_attempts", []))
        assert halted == {"T01/a1", "T02/b1"}, (
            f"연결 성분이 정확히 계산되지 않았다(T03 포함 금지): {sorted(halted)}"
        )
        assert payload.get("recovery_mode") == "path_scoped", payload
        assert set(payload.get("restored_paths", [])) == {"src/shared/contested.py"}, payload

        # 연결 성분 process는 실제로 죽어야 한다 — 선언만으로는 부족하다.
        # 자식 프로세스이므로 종료 판정은 poll()을 쓴다: os.kill(pid, 0)은 부모(pytest)가
        # 아직 수확하지 않은 좀비에도 성공을 반환해 오탐한다(POSIX 표준 동작).
        deadline = time.time() + 15
        while time.time() < deadline and any(
            procs[key].poll() is None for key in ("T01/a1", "T02/b1")
        ):
            time.sleep(0.1)
        for key in ("T01/a1", "T02/b1"):
            assert procs[key].poll() is not None, f"연결 성분 process가 종료되지 않았다: {key}"
        assert procs["T03/c1"].poll() is None, "무관한 attempt process까지 종료됐다."

        assert (
            path_hash(repo, "src/shared/contested.py")
            == hashlib.sha256(b"CONTESTED = 0\n").hexdigest()
        ), "충돌 경로가 봉인 preimage로 복구되지 않았다."
        assert path_hash(repo, "src/reports/service.py") == reports_hash, (
            "무관한 attempt(T03)의 변경이 복구에 휩쓸렸다."
        )
        assert path_hash(repo, "src/users/service.py") == hashlib.sha256(b"USERS = 1\n").hexdigest()
        assert git_fingerprint(repo) == before_git, "복구가 branch·HEAD·reflog를 바꿨다."
        assert_no_destructive_git(log, "S-12 귀속 불가 path-scoped 복구")
    finally:
        for proc in procs.values():
            if proc.poll() is None:
                proc.terminate()
            proc.wait(timeout=10)


# ═════════════════════════════════════════════════════════════════════════════
# S-16 PROVE 실패 귀속: 타 lease dirty → 자기 snapshot 즉시 재검증 (수용기준 27)
# needs_revalidation 전파 구간은 W-28의 test_revalidation.py가 소유한다.
# ═════════════════════════════════════════════════════════════════════════════


def test_s16_1_prove_failure_revalidates_on_own_snapshot_without_waiting(rec_env):
    """[T132/S-16] 다른 active lease가 dirty인 상태에서 PROVE가 실패해도, 재검증은 자기
    candidate snapshot에서 **즉시** 수행된다 — 다른 lease가 깨끗해질 때까지 기다리는
    대기 굶주림 0, 타 lease 변경으로 인한 오귀속 0(수용기준 27)."""
    repo, run_root, env, log = rec_env["repo"], rec_env["run_root"], rec_env["env"], rec_env["log"]
    for task, attempt in (("T01", "a1"), ("T02", "b1")):
        assert acquire(run_root, rec_env["specs"][task], attempt, env).get("ok") is True

    # T02가 자기 lease를 dirty 상태로 점유한 채 계속 작업 중이다.
    _write(repo, "src/orders/service.py", "ORDERS = 2\n")
    dirty_hash = path_hash(repo, "src/orders/service.py")

    _write(repo, "src/users/service.py", "USERS = 2\n")
    candidate = parse_json_stdout(
        run_oppb(
            [
                "checkpoint",
                "candidate",
                "--run-root",
                run_root,
                "--project-root",
                str(repo),
                "--task",
                "T01",
                "--attempt",
                "a1",
            ],
            env=env,
        ),
        "checkpoint candidate(T01/a1)",
    )
    assert candidate.get("ok") is True, candidate

    started = time.time()
    payload = parse_json_stdout(
        run_oppb(
            [
                "recover",
                "prove-failure",
                "--run-root",
                run_root,
                "--project-root",
                str(repo),
                "--task",
                "T01",
                "--attempt",
                "a1",
                "--candidate",
                candidate["candidate_id"],
            ],
            env=env,
        ),
        "recover prove-failure",
    )
    elapsed = time.time() - started

    assert payload.get("ok") is True, f"PROVE 실패 재검증 진입 실패: {payload}"
    assert payload.get("revalidation") == "immediate", (
        f"타 lease dirty를 이유로 재검증이 지연됐다: {payload}"
    )
    assert payload.get("snapshot_source") == "own_candidate", payload
    assert payload.get("snapshot_commit") == candidate["candidate_commit"], payload
    assert payload.get("waited_for_other_lease") is False, payload
    assert payload.get("starvation_wait_ms") == 0, payload
    assert payload.get("misattributed_failures") == 0, payload
    assert payload.get("repair_budget_charged") is False, (
        f"타 lease dirty로 인한 재검증은 Repair 예산을 차감하지 않는다: {payload}"
    )
    assert elapsed < 60, f"즉시 재검증이 아니라 대기했다: {elapsed:.1f}s"

    assert path_hash(repo, "src/orders/service.py") == dirty_hash, (
        "재검증이 다른 active lease의 dirty 작업을 건드렸다."
    )
    assert_no_destructive_git(log, "S-16 PROVE 실패 즉시 재검증")


def test_s16_2_revalidation_snapshot_excludes_other_lease_changes(rec_env):
    """[T132/S-16] 재검증 snapshot은 자기 candidate commit에서 만들어지므로 다른 lease의
    dirty 변경이 섞이지 않는다 — 실패 오귀속이 구조적으로 불가능하다(제안서 §4.5
    `git archive <candidate_commit>` 검증 snapshot)."""
    repo, run_root, env = rec_env["repo"], rec_env["run_root"], rec_env["env"]
    for task, attempt in (("T01", "a1"), ("T02", "b1")):
        assert acquire(run_root, rec_env["specs"][task], attempt, env).get("ok") is True

    _write(repo, "src/users/service.py", "USERS = 2\n")
    candidate = parse_json_stdout(
        run_oppb(
            [
                "checkpoint",
                "candidate",
                "--run-root",
                run_root,
                "--project-root",
                str(repo),
                "--task",
                "T01",
                "--attempt",
                "a1",
            ],
            env=env,
        ),
        "checkpoint candidate(T01/a1)",
    )
    assert candidate.get("ok") is True, candidate

    # candidate 생성 **후** 다른 lease가 dirty해진다.
    _write(repo, "src/orders/service.py", "ORDERS = 999\n")

    payload = parse_json_stdout(
        run_oppb(
            [
                "recover",
                "prove-failure",
                "--run-root",
                run_root,
                "--project-root",
                str(repo),
                "--task",
                "T01",
                "--attempt",
                "a1",
                "--candidate",
                candidate["candidate_id"],
            ],
            env=env,
        ),
        "recover prove-failure(snapshot 격리)",
    )
    assert payload.get("ok") is True, payload

    snapshot_root = pathlib.Path(payload.get("snapshot_path", ""))
    assert snapshot_root.is_dir(), f"검증 snapshot 디렉토리가 없다: {payload}"
    assert not (snapshot_root / ".git").exists(), (
        "snapshot에 .git이 포함됐다 — source 복사본이어야 한다(제안서 §4.5)."
    )
    assert (snapshot_root / "src" / "users" / "service.py").read_text(
        encoding="utf-8"
    ) == "USERS = 2\n", "자기 lease 변경이 snapshot에 반영되지 않았다."
    assert (snapshot_root / "src" / "orders" / "service.py").read_text(
        encoding="utf-8"
    ) == "ORDERS = 1\n", "다른 lease의 dirty 변경이 재검증 snapshot에 섞였다 — 오귀속 위험."
