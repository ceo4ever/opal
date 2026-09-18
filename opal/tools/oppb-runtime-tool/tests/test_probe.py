"""
@header {
  "module": "test_probe",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "oppb-runtime-tool probe 공개 CLI 계약 RED 테스트. 132 TEST-SCENARIO.md S-11(AC-4)을 검증한다 — probe 단독 실행이 ignored 출력을 정책(shared_immutable·attempt_namespaced·exclusive)과 한정 입력 hash(command·config·lockfile·toolchain·bootstrap)로 .opal/oppb-environment.json에 원자 봉인하고, profile에 없던 새 command의 첫 미봉인 쓰기는 contract revision당 1 batch delta probe·lease 확장·무과금 재실행으로 회수되며, 같은 revision의 두 번째 미봉인 쓰기·lease 교차·프로젝트 밖 경로는 scope_violation으로 승격되어 그때부터 예산을 차감한다. 제안서 §P2.2(Environment Probe & Seal·Git 미추적 ignore 산출물 계약·Late environment discovery)가 SSOT다. PLAN H-6에 따라 내부 함수·클래스를 import하지 않고 공개 CLI(run.sh)와 run root 파일 계약으로만 검증한다. mock/patch 금지 — 실제 git 저장소·실제 명령 실행만 사용한다(PLAN W-17).",
  "exports": [],
  "depends": ["opal/tools/oppb-runtime-tool/run.sh", "git CLI 2.x", "opal/tools/worktree-tool/tests/conftest.py(패턴 원천)"]
}
"""

from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
RUN_SH = TOOL_DIR / "run.sh"

PROFILE_RELPATH = ".opal/oppb-environment.json"
EPHEMERAL_POLICIES = {"shared_immutable", "attempt_namespaced", "exclusive"}
# 신선도 판정 입력은 repository tree 전체가 아니라 이 5종뿐이다 (제안서 §P2.2).
SEALED_INPUT_HASH_KEYS = {"commands", "config", "lockfile", "toolchain", "bootstrap"}

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


def run_git(args: list[str], cwd: pathlib.Path, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["git", *GIT_AUTHOR_ARGS, *args]
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git fixture 구성 실패: {' '.join(cmd)}\n"
            f"cwd={cwd}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def run_oppb(args: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    """공개 인터페이스(run.sh 서브프로세스)로만 호출한다. run.sh·probe 하위명령이 아직
    없으면(W-6·W-13 구현 전) 이 실패가 RED 증거다."""
    if not RUN_SH.exists():
        pytest.fail(
            "RED: opal/tools/oppb-runtime-tool/run.sh 미존재 — W-6·W-13 구현 전 정상 실패. "
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


def _write(repo: pathlib.Path, relpath: str, content: str) -> pathlib.Path:
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def make_project_repo(base: pathlib.Path, name: str = "proj") -> pathlib.Path:
    """실 git 프로젝트 fixture — lockfile·build config·source·.gitignore를 갖춘 저장소.

    probe가 단독 실행할 명령은 실제로 ignored 경로를 만드는 진짜 명령이다(mock 아님)."""
    repo = base / name
    repo.mkdir(parents=True)
    run_git(["init", "-b", "main", "."], cwd=repo)
    _write(repo, ".gitignore", "build-out/\ndep-cache/\ngen-out/\nlate-out/\n")
    _write(repo, "lockfile.lock", "dep-a==1.0.0\n")
    _write(repo, "build.config.json", '{"out": "build-out"}\n')
    _write(repo, "src/app.py", "VALUE = 1\n")
    run_git(["add", "-A"], cwd=repo)
    run_git(["commit", "-m", "project seed"], cwd=repo)
    return repo


def commands_spec(tmp_path: pathlib.Path, repo: pathlib.Path) -> pathlib.Path:
    """P0에서 수집하고 P2에서 확정한 bootstrap·build·test·검증 명령 정의.

    각 명령은 실제로 미추적·ignored 경로를 만든다 — probe가 관측할 대상이 진짜여야 한다."""
    py = "python3"
    return write_json(
        tmp_path / "commands.json",
        {
            "project_root": str(repo),
            "lockfile": ["lockfile.lock"],
            "config": ["build.config.json"],
            "toolchain": {"python": "3"},
            "commands": [
                {
                    "id": "bootstrap",
                    "kind": "bootstrap",
                    "argv": [
                        py,
                        "-c",
                        "import pathlib;p=pathlib.Path('dep-cache');p.mkdir(exist_ok=True);"
                        "(p/'dep-a').write_text('1.0.0')",
                    ],
                },
                {
                    "id": "build",
                    "kind": "build",
                    "argv": [
                        py,
                        "-c",
                        "import pathlib;p=pathlib.Path('build-out');p.mkdir(exist_ok=True);"
                        "(p/'app.out').write_text('built')",
                    ],
                },
                {
                    "id": "test",
                    "kind": "test",
                    "argv": [
                        py,
                        "-c",
                        "import pathlib;p=pathlib.Path('gen-out');p.mkdir(exist_ok=True);"
                        "(p/'report.txt').write_text('ok')",
                    ],
                },
            ],
        },
    )


def make_hub_repo(base: pathlib.Path, name: str = "hub") -> pathlib.Path:
    repo = base / name
    repo.mkdir(parents=True)
    run_git(["init", "-b", "main", "."], cwd=repo)
    _write(repo, "README.md", "# hub\n")
    run_git(["add", "README.md"], cwd=repo)
    run_git(["commit", "-m", "init"], cwd=repo)
    return repo


def init_run(repo: pathlib.Path, project: pathlib.Path) -> dict:
    result = run_oppb(
        ["init", "--allocator-root", str(repo), "--project-root", str(project)]
    )
    assert result.returncode == 0, (
        f"init 실패: exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    payload = parse_json_stdout(result, "init")
    for key in ("run_id", "run_root", "cache_root"):
        assert key in payload, f"init 응답에 {key} 없음: {payload}"
    return payload


def seal(run_root: str, repo: pathlib.Path, commands: pathlib.Path) -> dict:
    result = run_oppb(
        [
            "probe",
            "seal",
            "--run-root",
            run_root,
            "--project-root",
            str(repo),
            "--commands",
            str(commands),
        ]
    )
    return parse_json_stdout(result, "probe seal")


def probe_status(run_root: str, repo: pathlib.Path) -> dict:
    result = run_oppb(
        ["probe", "status", "--run-root", run_root, "--project-root", str(repo)]
    )
    return parse_json_stdout(result, "probe status")


def observe_write(
    run_root: str,
    repo: pathlib.Path,
    *,
    task: str = "T01",
    attempt: str = "a1",
    revision: int = 1,
    command_id: str = "late-gen",
    argv: list[str] | None = None,
    paths: list[str] | None = None,
) -> dict:
    """미봉인 ignored 쓰기 관측 → late discovery 회수 또는 scope_violation 승격."""
    payload_path = repo.parent / f"observe_{task}_{attempt}_{command_id}.json"
    write_json(
        payload_path,
        {
            "task_id": task,
            "attempt_id": attempt,
            "contract_revision": revision,
            "command": {
                "id": command_id,
                "argv": argv
                or [
                    "python3",
                    "-c",
                    "import pathlib;p=pathlib.Path('late-out');p.mkdir(exist_ok=True);"
                    "(p/'x.txt').write_text('late')",
                ],
            },
            "observed_paths": paths or ["late-out/x.txt", "late-out/y.txt"],
        },
    )
    result = run_oppb(
        [
            "probe",
            "observe-write",
            "--run-root",
            run_root,
            "--project-root",
            str(repo),
            "--observation",
            str(payload_path),
        ]
    )
    return parse_json_stdout(result, f"probe observe-write({command_id})")


@pytest.fixture
def probe_env(tmp_path: pathlib.Path):
    """허브(allocator) + init된 run root + 실 git 프로젝트 저장소 + 명령 정의."""
    hub = make_hub_repo(tmp_path)
    repo = make_project_repo(tmp_path)
    run_root = init_run(hub, repo)["run_root"]
    commands = commands_spec(tmp_path, repo)
    return run_root, repo, commands


# ═════════════════════════════════════════════════════════════════════════════
# S-11 ①: 단독 probe 실행과 원자 봉인 (수용기준 4 전반부)
# ═════════════════════════════════════════════════════════════════════════════


def test_s11_1_probe_seals_ignored_outputs_with_policy_and_input_hash(probe_env):
    """[T132/S-11] probe 단독 실행이 각 명령의 실제 미추적·ignored 출력 경로를 관측해
    3종 정책 중 하나와 한정 입력 hash를 함께 `.opal/oppb-environment.json`에 봉인한다."""
    run_root, repo, commands = probe_env

    payload = seal(run_root, repo, commands)
    assert payload.get("ok") is True, f"probe seal 실패: {payload}"

    profile_path = repo / PROFILE_RELPATH
    assert profile_path.exists(), f"{PROFILE_RELPATH}가 생성되지 않았다: {payload}"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))

    ephemeral = profile.get("ephemeral_write_set")
    assert ephemeral, f"ephemeral_write_set이 비어 있다: {profile}"
    observed = {entry["path"] for entry in ephemeral}
    for expected in ("build-out", "dep-cache", "gen-out"):
        assert any(path.startswith(expected) for path in observed), (
            f"명령이 실제로 만든 ignored 경로 {expected}가 봉인되지 않았다: {sorted(observed)}"
        )
    for entry in ephemeral:
        assert entry.get("policy") in EPHEMERAL_POLICIES, (
            f"정책이 3종 중 하나가 아니다: {entry}"
        )
        assert "adapter" in entry, f"경로별 adapter 배정이 없다: {entry}"

    input_hash = profile.get("input_hash")
    assert isinstance(input_hash, dict), f"input_hash가 객체가 아니다: {profile}"
    assert SEALED_INPUT_HASH_KEYS.issubset(set(input_hash)), (
        f"한정 입력 hash 5종이 모두 없다: {sorted(input_hash)}"
    )

    assert profile.get("runtime_resources") is not None, f"실행 자원 관측이 없다: {profile}"


def test_s11_2_seal_is_atomic_and_leaves_no_partial_file(probe_env):
    """[T132/S-11] 봉인은 원자적이다 — 재봉인 후에도 partial/temp 잔여물이 없고 결과가
    항상 유효 JSON이다(제안서 §P2.2 "원자적으로 봉인한다")."""
    run_root, repo, commands = probe_env
    assert seal(run_root, repo, commands).get("ok") is True
    assert seal(run_root, repo, commands).get("ok") is True

    opal_dir = repo / ".opal"
    leftovers = [
        entry.name
        for entry in opal_dir.iterdir()
        if entry.name != "oppb-environment.json"
        and ("oppb-environment" in entry.name or entry.name.endswith((".tmp", ".partial", ".swp")))
    ]
    assert leftovers == [], f"원자 교체 잔여물이 남았다: {leftovers}"
    json.loads((repo / PROFILE_RELPATH).read_text(encoding="utf-8"))


def test_s11_3_freshness_uses_limited_inputs_not_whole_tree(probe_env):
    """[T132/S-11] 신선도 입력은 repository tree 전체가 아니다 — 일반 source 변경만으로
    profile을 stale 처리하지 않고, lockfile·config가 바뀌어야 stale이다(제안서 §P2.2).
    Controller는 stale profile에서 병렬 dispatch를 거부한다."""
    run_root, repo, commands = probe_env
    assert seal(run_root, repo, commands).get("ok") is True

    _write(repo, "src/app.py", "VALUE = 2\n")
    run_git(["add", "-A"], cwd=repo)
    run_git(["commit", "-m", "ordinary source accept"], cwd=repo)
    after_source = probe_status(run_root, repo)
    assert after_source.get("ok") is True, after_source
    assert after_source.get("fresh") is True, (
        f"일반 source ACCEPT만으로 profile이 stale 처리됐다: {after_source}"
    )
    assert after_source.get("parallel_dispatch_allowed") is True, after_source

    _write(repo, "lockfile.lock", "dep-a==2.0.0\n")
    after_lock = probe_status(run_root, repo)
    assert after_lock.get("fresh") is False, f"lockfile 변경이 stale로 판정되지 않았다: {after_lock}"
    assert after_lock.get("parallel_dispatch_allowed") is False, after_lock


# ═════════════════════════════════════════════════════════════════════════════
# S-11 ②: Late discovery — 1 batch delta probe·lease 확장·무과금 재실행 (수용기준 4)
# ═════════════════════════════════════════════════════════════════════════════


def test_s11_4_first_unsealed_write_is_recovered_by_one_unbilled_batch(probe_env):
    """[T132/S-11] profile에 없던 새 command의 첫 미봉인 ignored 쓰기는 `scope_violation`이
    아니라 1 batch delta probe로 회수된다 — lease를 확장하고 같은 task ID의 새 attempt를
    무과금으로 재실행한다. delta probe가 한 명령에서 관측한 **모든** 경로를 같은 batch로
    봉인한다(제안서 §P2.2 Late environment discovery 1~5)."""
    run_root, repo, commands = probe_env
    assert seal(run_root, repo, commands).get("ok") is True

    payload = observe_write(run_root, repo, revision=1)

    assert payload.get("ok") is True, f"첫 미봉인 쓰기가 회수되지 않았다: {payload}"
    assert payload.get("action") == "delta_probe", payload
    assert payload.get("budget_charged") is False, (
        f"revision당 첫 discovery batch는 무과금이어야 한다: {payload}"
    )
    assert payload.get("rerun_requested") is True, payload
    assert payload.get("lease_extended"), f"임시 ephemeral lease 확장이 없다: {payload}"

    fingerprint = payload.get("fingerprint")
    assert fingerprint, f"discovery fingerprint가 없다: {payload}"
    delta_path = pathlib.Path(run_root) / "environment-deltas" / f"{fingerprint}.json"
    assert delta_path.exists(), (
        f"run-local environment-deltas/<fingerprint>.json이 없다: {delta_path}"
    )
    delta = json.loads(delta_path.read_text(encoding="utf-8"))
    sealed_paths = {entry["path"] for entry in delta.get("ephemeral_write_set", [])}
    assert {"late-out/x.txt", "late-out/y.txt"} <= sealed_paths, (
        f"한 명령의 모든 관측 경로가 같은 batch로 봉인되지 않았다: {sorted(sealed_paths)}"
    )

    # 추적 profile은 이 시점에 바뀌지 않는다 — Runner commit도 후속 임의 commit도 없다.
    assert run_git(["status", "--porcelain"], cwd=repo).stdout.strip() == "", (
        "late discovery가 프로젝트 worktree에 추적 변경을 남겼다."
    )


def test_s11_5_second_unsealed_write_in_same_revision_escalates(probe_env):
    """[T132/S-11] 같은 contract revision의 **두 번째** 미봉인 쓰기는 즉시
    `scope_violation`으로 승격되고 **그때부터** attempt·rework 예산을 차감한다."""
    run_root, repo, commands = probe_env
    assert seal(run_root, repo, commands).get("ok") is True

    first = observe_write(run_root, repo, revision=1, command_id="late-gen")
    assert first.get("action") == "delta_probe", first

    second = observe_write(
        run_root,
        repo,
        revision=1,
        command_id="late-gen-2",
        paths=["late-out/z.txt"],
    )
    assert second.get("ok") is False, f"두 번째 미봉인 쓰기가 승격되지 않았다: {second}"
    assert second.get("error") == "scope_violation", second
    assert second.get("budget_charged") is True, (
        f"승격 시점부터 예산을 차감해야 한다: {second}"
    )
    charged = second.get("charged_budgets", [])
    assert "task_attempt" in charged and "project_rework" in charged, second


def test_s11_6_new_contract_revision_opens_new_discovery_epoch(probe_env):
    """[T132/S-11] task contract revision이 바뀌면 새 discovery epoch를 열 수 있다 —
    새 revision의 첫 batch는 다시 무과금이다(제안서 §P2.2)."""
    run_root, repo, commands = probe_env
    assert seal(run_root, repo, commands).get("ok") is True
    assert observe_write(run_root, repo, revision=1).get("action") == "delta_probe"

    next_epoch = observe_write(
        run_root, repo, revision=2, command_id="late-gen-r2", paths=["late-out/r2.txt"]
    )
    assert next_epoch.get("ok") is True, next_epoch
    assert next_epoch.get("action") == "delta_probe", next_epoch
    assert next_epoch.get("budget_charged") is False, next_epoch


def test_s11_7_lease_crossing_escalates_on_first_occurrence(probe_env):
    """[T132/S-11] 기존 lease와 교차하는 미봉인 쓰기는 첫 관측이라도 자동 확장 조건을
    만족하지 못하므로 즉시 `scope_violation`이다. 이 예외는 tracked write·contract·
    runtime resource 위반에는 적용하지 않는다(제안서 §P2.2)."""
    run_root, repo, commands = probe_env
    assert seal(run_root, repo, commands).get("ok") is True

    other_spec = write_json(
        repo.parent / "spec_other.json",
        {
            "task_id": "T02",
            "capability_id": "cap-T02",
            "tracked_write_set": ["src/other.py"],
            "ephemeral_write_set": [{"path": "late-out", "policy": "exclusive"}],
            "contracts": [],
            "business_rules": [],
            "acceptance_ids": [],
            "runtime_resources": [],
            "global_outputs": [],
        },
    )
    held = parse_json_stdout(
        run_oppb(
            [
                "lease",
                "acquire",
                "--run-root",
                run_root,
                "--spec",
                str(other_spec),
                "--attempt",
                "b1",
            ]
        ),
        "lease acquire(T02)",
    )
    assert held.get("ok") is True, held

    crossing = observe_write(run_root, repo, task="T01", revision=1, paths=["late-out/x.txt"])
    assert crossing.get("ok") is False, f"lease 교차가 승격되지 않았다: {crossing}"
    assert crossing.get("error") == "scope_violation", crossing
    assert crossing.get("reason") == "lease_crossing", crossing
    assert crossing.get("budget_charged") is True, crossing


def test_s11_8_path_outside_project_root_escalates(probe_env, tmp_path):
    """[T132/S-11] 허용된 project/run root 밖 경로와 민감 경로는 자동 확장 대상이 아니다 —
    첫 관측에서 바로 `scope_violation`이다."""
    run_root, repo, commands = probe_env
    assert seal(run_root, repo, commands).get("ok") is True

    outside = str((tmp_path / "outside" / "leak.txt").resolve())
    payload = observe_write(run_root, repo, revision=1, command_id="escape", paths=[outside])

    assert payload.get("ok") is False, f"프로젝트 밖 경로가 허용됐다: {payload}"
    assert payload.get("error") == "scope_violation", payload
    assert payload.get("reason") in ("outside_project_root", "sensitive_path"), payload
    assert payload.get("budget_charged") is True, payload
