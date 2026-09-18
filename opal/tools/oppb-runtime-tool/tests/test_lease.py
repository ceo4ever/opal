"""
@header {
  "module": "test_lease",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "oppb-runtime-tool lease 공개 CLI 계약 RED 테스트. 132 TEST-SCENARIO.md S-10(AC-5, C-7)을 검증한다 — 동일 tracked write·ephemeral write·contract·runtime resource를 요구하는 두 미니 태스크는 dispatch 전에 거부되어 동시 lease 0이고, 완전히 분리된 두 미니 태스크는 실제 동시 실행되며, Verifier에는 실행 중 Runner와 겹치지 않는 전용 runtime resource lease가 발급된다. 제안서 §P2.1 소유권 6축과 §4.5 Verifier resource lease가 SSOT다. PLAN H-6에 따라 내부 함수·클래스를 import하지 않고 공개 CLI(run.sh)와 run root 파일 계약으로만 검증한다. mock/patch 금지 — 실제 git 저장소·실제 프로세스만 사용한다(PLAN W-17).",
  "exports": [],
  "depends": ["opal/tools/oppb-runtime-tool/run.sh", "git CLI 2.x", "opal/tools/worktree-tool/tests/conftest.py(패턴 원천)"]
}
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

import pytest

# opal/tools/oppb-runtime-tool/tests -> opal/tools/oppb-runtime-tool
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


# ─────────────────────────────────────────────────────────────────────────────
# 공개 인터페이스 헬퍼 — run.sh subprocess 호출만 사용한다 (red-first.md §2, PLAN H-6)
# conftest.py는 W-17의 변경 대상이 아니므로(W-10과 소유권 충돌) 헬퍼를 파일 내부에 둔다.
# ─────────────────────────────────────────────────────────────────────────────


def run_git(args: list[str], cwd: pathlib.Path, check: bool = True) -> subprocess.CompletedProcess:
    """fixture 구성·불변식 관측 전용 git 실행 헬퍼. 전역 git config에 의존하지 않도록
    author/gpgsign/defaultBranch를 항상 주입한다."""
    cmd = ["git", *GIT_AUTHOR_ARGS, *args]
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git fixture 구성 실패: {' '.join(cmd)}\n"
            f"cwd={cwd}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def run_oppb(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    """공개 인터페이스(run.sh 서브프로세스)로만 oppb-runtime-tool을 호출한다.
    run.sh·lease 하위명령이 아직 없으면(W-6·W-12 구현 전) 이 실패가 RED 증거다."""
    if not RUN_SH.exists():
        pytest.fail(
            "RED: opal/tools/oppb-runtime-tool/run.sh 미존재 — W-6·W-12 구현 전 정상 실패. "
            f"요청 명령: run.sh {' '.join(args)}"
        )
    return subprocess.run(
        ["bash", str(RUN_SH), *args], capture_output=True, text=True, timeout=timeout
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


def make_hub_repo(base: pathlib.Path, name: str = "hub") -> pathlib.Path:
    """깨끗한 허브 저장소 fixture — 커밋 1개가 있는 실 git 작업 저장소."""
    repo = base / name
    repo.mkdir(parents=True)
    run_git(["init", "-b", "main", "."], cwd=repo)
    (repo / "README.md").write_text("# hub\n", encoding="utf-8")
    run_git(["add", "README.md"], cwd=repo)
    run_git(["commit", "-m", "init"], cwd=repo)
    return repo


def init_run(repo: pathlib.Path) -> dict:
    """`init --allocator-root <abs> --project-root <abs>` 1회.
    test_oppb_init.py(W-10)가 고정한 응답 계약을 재사용한다."""
    result = run_oppb(
        ["init", "--allocator-root", str(repo), "--project-root", str(repo)]
    )
    assert result.returncode == 0, (
        f"init 실패: exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    payload = parse_json_stdout(result, "init")
    for key in ("run_id", "run_root", "cache_root"):
        assert key in payload, f"init 응답에 {key} 없음: {payload}"
    return payload


# ─────────────────────────────────────────────────────────────────────────────
# 미니 태스크 소유권 spec — 제안서 §P2.1 "소유권 축" 6종을 그대로 표현한다.
# 이 스키마 자체가 GREEN 구현이 지켜야 할 입력 계약이다.
# ─────────────────────────────────────────────────────────────────────────────

OWNERSHIP_AXES = (
    "tracked_write",
    "ephemeral_write",
    "contract",
    "business_rule",
    "acceptance",
    "runtime_resource",
    "global_output",
)


def task_spec(
    task_id: str,
    *,
    tracked_write_set=None,
    ephemeral_write_set=None,
    contracts=None,
    business_rules=None,
    acceptance_ids=None,
    runtime_resources=None,
    global_outputs=None,
) -> dict:
    return {
        "task_id": task_id,
        "capability_id": f"cap-{task_id}",
        "tracked_write_set": list(tracked_write_set or []),
        "ephemeral_write_set": list(ephemeral_write_set or []),
        "contracts": list(contracts or []),
        "business_rules": list(business_rules or []),
        "acceptance_ids": list(acceptance_ids or []),
        "runtime_resources": list(runtime_resources or []),
        "global_outputs": list(global_outputs or []),
    }


def spec_a(tmp_path: pathlib.Path, **overrides) -> pathlib.Path:
    base = task_spec(
        "T01",
        tracked_write_set=["src/users/service.py"],
        ephemeral_write_set=[{"path": ".cache/users", "policy": "attempt_namespaced"}],
        contracts=["contract:user-api@3"],
        business_rules=["BR-USER-1"],
        acceptance_ids=["ACC-USER-1"],
        runtime_resources=["port:5001", "db:schema_users"],
    )
    base.update(overrides)
    base["task_id"] = "T01"
    return write_json(tmp_path / "spec_a.json", base)


def spec_b(tmp_path: pathlib.Path, **overrides) -> pathlib.Path:
    """기본값은 T01과 **완전 분리**된 태스크다. overrides로 축 하나씩 충돌시킨다."""
    base = task_spec(
        "T02",
        tracked_write_set=["src/orders/service.py"],
        ephemeral_write_set=[{"path": ".cache/orders", "policy": "attempt_namespaced"}],
        contracts=["contract:order-api@1"],
        business_rules=["BR-ORDER-1"],
        acceptance_ids=["ACC-ORDER-1"],
        runtime_resources=["port:5002", "db:schema_orders"],
    )
    base.update(overrides)
    base["task_id"] = "T02"
    return write_json(tmp_path / "spec_b.json", base)


def check_parallel(run_root: str, a: pathlib.Path, b: pathlib.Path) -> dict:
    """dispatch admission 검사 — Controller pairwise 교집합 검사의 공개 진입점."""
    result = run_oppb(
        ["lease", "check-parallel", "--run-root", run_root, "--spec", str(a), "--spec", str(b)]
    )
    return parse_json_stdout(result, "lease check-parallel")


def acquire(run_root: str, spec: pathlib.Path, attempt: str = "a1") -> dict:
    result = run_oppb(
        ["lease", "acquire", "--run-root", run_root, "--spec", str(spec), "--attempt", attempt]
    )
    return parse_json_stdout(result, "lease acquire")


def lease_list(run_root: str) -> dict:
    result = run_oppb(["lease", "list", "--run-root", run_root])
    return parse_json_stdout(result, "lease list")


def active_leases(run_root: str) -> list:
    payload = lease_list(run_root)
    assert payload.get("ok") is True, f"lease list 실패: {payload}"
    return [lease for lease in payload.get("leases", []) if lease.get("state") == "active"]


@pytest.fixture
def run_env(tmp_path: pathlib.Path):
    """실 git 허브 저장소 + init된 run root."""
    repo = make_hub_repo(tmp_path)
    payload = init_run(repo)
    return repo, payload["run_root"]


# ═════════════════════════════════════════════════════════════════════════════
# S-10 ①: 소유권 축이 겹치는 두 미니 태스크는 dispatch **전에** 거부된다 (수용기준 15)
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "axis,override",
    [
        ("tracked_write", {"tracked_write_set": ["src/users/service.py"]}),
        (
            "ephemeral_write",
            {"ephemeral_write_set": [{"path": ".cache/users", "policy": "attempt_namespaced"}]},
        ),
        ("contract", {"contracts": ["contract:user-api@3"]}),
        ("runtime_resource", {"runtime_resources": ["port:5001"]}),
    ],
)
def test_s10_1_conflicting_axis_is_rejected_before_dispatch(run_env, tmp_path, axis, override):
    """[T132/S-10] Controller가 기계적으로 lease를 발급하는 3축(tracked write·ephemeral
    write·contract)과 runtime resource 중 하나라도 교집합이 있으면 dispatch admission에서
    거부된다. 제안서 §P2.1 "schema 누락·교집합·표현 불가능은 dispatch 거부다"."""
    _repo, run_root = run_env
    a = spec_a(tmp_path)
    b = spec_b(tmp_path, **override)

    payload = check_parallel(run_root, a, b)

    assert payload.get("ok") is False, f"{axis} 교집합인데 admission이 통과했다: {payload}"
    assert payload.get("parallel_eligible") is False, payload
    assert payload.get("error") == "LEASE_CONFLICT", payload
    assert axis in payload.get("conflict_axes", []), (
        f"conflict_axes에 {axis}가 없다: {payload.get('conflict_axes')}"
    )


def test_s10_2_logical_ownership_intersection_is_also_rejected(run_env, tmp_path):
    """[T132/S-10] business rule·acceptance는 파일이 아니라 workgraph 논리 소유권 ID
    교집합으로 검사한다(제안서 §P2.1). global output은 write set 또는 runtime resource로
    반드시 다시 표현되어야 하며, 표현되지 않으면 dispatch 거부다."""
    _repo, run_root = run_env
    a = spec_a(tmp_path)

    shared_rule = check_parallel(
        run_root,
        a,
        spec_b(tmp_path, business_rules=["BR-USER-1"], acceptance_ids=["ACC-USER-1"]),
    )
    assert shared_rule.get("ok") is False, shared_rule
    assert "business_rule" in shared_rule.get("conflict_axes", []), shared_rule
    assert "acceptance" in shared_rule.get("conflict_axes", []), shared_rule

    # global output이 write set·runtime resource 어디에도 재표현되지 않은 spec은 거부된다.
    unrepresented = check_parallel(
        run_root, a, spec_b(tmp_path, global_outputs=["package-lock.json"])
    )
    assert unrepresented.get("ok") is False, unrepresented
    assert unrepresented.get("error") in ("LEASE_CONFLICT", "OWNERSHIP_NOT_REPRESENTABLE"), (
        unrepresented
    )


def test_s10_3_conflicting_pair_yields_zero_concurrent_leases(run_env, tmp_path):
    """[T132/S-10] 충돌 쌍은 **동시 lease 0** — 먼저 잡은 쪽만 active로 남고 두 번째
    acquire는 거부된다. 수용기준 5의 "동일 tracked/ephemeral write·contract·runtime
    resource의 동시 lease 0"을 lease list 관측으로 기계 판정한다."""
    _repo, run_root = run_env
    a = spec_a(tmp_path)
    b = spec_b(tmp_path, tracked_write_set=["src/users/service.py"])

    first = acquire(run_root, a)
    assert first.get("ok") is True, f"단독 acquire가 실패했다: {first}"

    second = acquire(run_root, b)
    assert second.get("ok") is False, f"충돌 lease가 동시에 발급됐다: {second}"
    assert second.get("error") == "LEASE_CONFLICT", second

    held = active_leases(run_root)
    assert len(held) == 1, f"동시 active lease가 1개가 아니다: {held}"
    assert held[0].get("task_id") == "T01", held


# ═════════════════════════════════════════════════════════════════════════════
# S-10 ②: 완전 분리된 두 미니 태스크는 **실제로** 동시 실행된다 (수용기준 5)
# ═════════════════════════════════════════════════════════════════════════════


def test_s10_4_disjoint_pair_is_parallel_eligible(run_env, tmp_path):
    """[T132/S-10] 6축 전부 분리된 쌍은 admission을 통과하고 근거가 기록된다."""
    _repo, run_root = run_env
    payload = check_parallel(run_root, spec_a(tmp_path), spec_b(tmp_path))

    assert payload.get("ok") is True, f"분리 쌍이 거부됐다: {payload}"
    assert payload.get("parallel_eligible") is True, payload
    assert payload.get("conflict_axes") == [], payload
    # workgraph에는 pair별 교집합 검사 결과와 근거를 저장한다(제안서 §P2.1).
    checked = payload.get("checked_axes", [])
    for axis in OWNERSHIP_AXES:
        assert axis in checked, f"소유권 축 {axis}의 검사 근거가 없다: {checked}"


def test_s10_5_disjoint_pair_actually_runs_concurrently(run_env, tmp_path):
    """[T132/S-10] 선언만이 아니라 **실제 동시 실행**을 관찰한다. 두 lease를 각각 잡고
    실제 자식 프로세스 2개를 띄운 뒤, 둘이 살아 있는 동안 lease list가 active 2개를
    동시에 보고하는 순간을 포착한다. mock 금지 — 실제 프로세스만 사용한다."""
    _repo, run_root = run_env
    a = spec_a(tmp_path)
    b = spec_b(tmp_path)

    granted_a = acquire(run_root, a, attempt="a1")
    granted_b = acquire(run_root, b, attempt="b1")
    assert granted_a.get("ok") is True, granted_a
    assert granted_b.get("ok") is True, f"분리 태스크의 두 번째 lease가 거부됐다: {granted_b}"

    marker_a = tmp_path / "worked_a.txt"
    marker_b = tmp_path / "worked_b.txt"
    script = (
        "import pathlib, sys, time\n"
        "p = pathlib.Path(sys.argv[1]); p.write_text('start', encoding='utf-8')\n"
        "time.sleep(3)\n"
        "p.write_text('done', encoding='utf-8')\n"
    )
    proc_a = subprocess.Popen([sys.executable, "-c", script, str(marker_a)])
    proc_b = subprocess.Popen([sys.executable, "-c", script, str(marker_b)])
    try:
        observed_both_running = False
        observed_two_active = False
        deadline = time.time() + 10
        while time.time() < deadline:
            both_alive = proc_a.poll() is None and proc_b.poll() is None
            if both_alive:
                observed_both_running = True
                if len(active_leases(run_root)) == 2:
                    observed_two_active = True
                    break
            time.sleep(0.1)
    finally:
        for proc in (proc_a, proc_b):
            if proc.poll() is None:
                proc.terminate()
            proc.wait(timeout=10)

    assert observed_both_running, "두 attempt 프로세스가 동시에 살아 있는 구간이 관측되지 않았다."
    assert observed_two_active, (
        "분리된 두 미니 태스크의 active lease 2개가 동시에 관측되지 않았다 — 실제 동시 실행 실패."
    )
    assert marker_a.exists() and marker_b.exists(), "두 attempt가 각자 경로에 실제로 쓰지 못했다."


# ═════════════════════════════════════════════════════════════════════════════
# S-10 ③: Verifier 전용 runtime resource lease (수용기준 32, 제안서 §4.5)
# ═════════════════════════════════════════════════════════════════════════════


def test_s10_6_verifier_gets_dedicated_runtime_resource_lease(run_env, tmp_path):
    """[T132/S-10] Verifier 실행 전 Scope Lease Tool이 candidate ID에 귀속된 검증용
    runtime resource lease를 발급한다. 포트·DB schema·service·queue·browser profile이
    실행 중 Runner와 겹치면 검증을 시작하지 않는다(제안서 §4.5)."""
    _repo, run_root = run_env
    a = spec_a(tmp_path)
    runner = acquire(run_root, a, attempt="a1")
    assert runner.get("ok") is True, runner

    result = run_oppb(
        [
            "lease",
            "verifier-acquire",
            "--run-root",
            run_root,
            "--candidate",
            "cand-0001",
            "--spec",
            str(a),
        ]
    )
    payload = parse_json_stdout(result, "lease verifier-acquire")

    assert payload.get("ok") is True, f"Verifier lease 발급 실패: {payload}"
    assert payload.get("role") == "verifier", payload
    assert payload.get("candidate_id") == "cand-0001", payload

    verifier_resources = set(payload.get("runtime_resources", []))
    assert verifier_resources, f"Verifier 전용 runtime resource가 비어 있다: {payload}"

    runner_resources = set()
    for lease in active_leases(run_root):
        if lease.get("role") == "runner":
            runner_resources.update(lease.get("runtime_resources", []))
    assert runner_resources, "Runner lease의 runtime resource가 관측되지 않았다."
    assert verifier_resources & runner_resources == set(), (
        "Verifier runtime resource가 실행 중 Runner와 겹친다: "
        f"{verifier_resources & runner_resources}"
    )


def test_s10_7_verifier_lease_pends_when_resources_collide(run_env, tmp_path):
    """[T132/S-10] 분리 가능한 자원이 없으면 Verifier는 검증을 시작하지 않고 pending으로
    둔다 — 겹친 채 시작하는 경로가 없어야 한다(제안서 §4.5)."""
    _repo, run_root = run_env
    spec = task_spec(
        "T09",
        tracked_write_set=["src/legacy/mod.py"],
        runtime_resources=["port:5001", "service:only-one"],
    )
    # 배타 자원이라 namespace 격리로 분리할 수 없다고 선언한다.
    spec["runtime_resource_isolation"] = "exclusive"
    exclusive = write_json(tmp_path / "spec_excl.json", spec)
    runner = acquire(run_root, exclusive, attempt="a1")
    assert runner.get("ok") is True, runner

    result = run_oppb(
        [
            "lease",
            "verifier-acquire",
            "--run-root",
            run_root,
            "--candidate",
            "cand-0002",
            "--spec",
            str(exclusive),
        ]
    )
    payload = parse_json_stdout(result, "lease verifier-acquire(collide)")

    assert payload.get("ok") is False, f"자원 충돌인데 Verifier lease가 발급됐다: {payload}"
    assert payload.get("state") == "pending", payload
    assert payload.get("error") in ("RESOURCE_BUSY", "LEASE_CONFLICT"), payload
