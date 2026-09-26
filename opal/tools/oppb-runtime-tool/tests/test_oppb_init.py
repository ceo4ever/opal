"""
@header {
  "module": "test_oppb_init",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "oppb-runtime-tool init/finalize-run 공개 CLI 계약 테스트. 신규 run root를 OPPB 태스크의 .oppb-run/<run_id>에 만들고 공유 cache만 allocator에 유지하며, 기존 .opal-runs는 조회·재개 호환으로만 수용하고, 성공 종료 보존 묶음에서 로그·결과·증거는 유지하되 lock·sandbox·임시 index를 제거하는 계약을 실제 Git 저장소와 파일로 검증한다. 내부 함수 import와 mock/patch는 사용하지 않는다.",
  "exports": [],
  "depends": ["opal/tools/oppb-runtime-tool/run.sh", "git CLI 2.x", "opal/tools/worktree-tool/tests/conftest.py(패턴 원천)"]
}
"""

from __future__ import annotations

import fcntl
import json
import os
import pathlib
import shutil
import stat
import subprocess

import pytest

# opal/tools/oppb-runtime-tool/tests -> opal/tools/oppb-runtime-tool
TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
RUN_SH = TOOL_DIR / "run.sh"

RUN_ROOT_ENTRY = ".oppb-run/"
LEGACY_RUN_ROOT_ENTRY = ".opal-runs/"
CACHE_ROOT_ENTRY = ".opal-cache/oppb/"

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
    """fixture 구성·ignore 판정 확인 전용 git 실행 헬퍼. 전역 git config에 의존하지
    않도록 author/gpgsign/defaultBranch를 항상 주입한다."""
    cmd = ["git", *GIT_AUTHOR_ARGS, *args]
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git fixture 구성 실패: {' '.join(cmd)}\n"
            f"cwd={cwd}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def make_hub_repo(base: pathlib.Path, name: str = "hub") -> pathlib.Path:
    """깨끗한 허브 저장소 fixture — 커밋 1개가 있는 실 git 작업 저장소를 만든다."""
    repo = base / name
    repo.mkdir(parents=True)
    run_git(["init", "-b", "main", "."], cwd=repo)
    (repo / "README.md").write_text("# hub\n", encoding="utf-8")
    run_git(["add", "README.md"], cwd=repo)
    run_git(["commit", "-m", "init"], cwd=repo)
    return repo


def run_oppb(args: list[str], cwd: pathlib.Path | None = None, timeout: int = 120):
    """공개 인터페이스(run.sh 서브프로세스)로만 oppb-runtime-tool을 호출한다.
    내부 함수 import 금지(harness/red-first.md §4, PLAN H-6).
    run.sh가 아직 없으면(W-6~W-9 구현 전) 이 실패가 RED 증거다."""
    if not RUN_SH.exists():
        pytest.fail(
            "RED: opal/tools/oppb-runtime-tool/run.sh 미존재 — W-6~W-9 구현 전 정상 실패. "
            f"요청 명령: run.sh {' '.join(args)}"
        )
    return subprocess.run(
        ["bash", str(RUN_SH), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def parse_json_stdout(result: subprocess.CompletedProcess, label: str = "") -> dict:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"{label} stdout이 유효 JSON이 아님. exit={result.returncode}\n"
            f"stdout={result.stdout!r}\nstderr={result.stderr!r}\n원인: {exc}"
        )


def make_task_root(repo: pathlib.Path, parent: str = "tasks") -> pathlib.Path:
    task_root = repo / parent / "200-260926-oppb-sample"
    task_root.mkdir(parents=True, exist_ok=True)
    (task_root / "TASK.md").write_text("# TASK\n", encoding="utf-8")
    return task_root


def init_hub(
    repo: pathlib.Path,
    cwd: pathlib.Path | None = None,
    task_root: pathlib.Path | None = None,
) -> dict:
    """정상 init 1회. run_id·run_root·cache_root를 담은 JSON 응답을 돌려준다."""
    task_root = task_root or make_task_root(repo)
    result = run_oppb(
        [
            "init",
            "--allocator-root", str(repo),
            "--project-root", str(repo),
            "--task-root", str(task_root),
        ],
        cwd=cwd,
    )
    assert result.returncode == 0, (
        f"init 실패: exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    payload = parse_json_stdout(result, "init")
    for key in ("run_id", "run_root", "cache_root", "task_root"):
        assert key in payload, f"init 응답에 {key} 없음: {payload}"
    return payload


def exclude_path(repo: pathlib.Path) -> pathlib.Path:
    return repo / ".git" / "info" / "exclude"


def exclude_lines(repo: pathlib.Path) -> list[str]:
    path = exclude_path(repo)
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]


def is_ignored(repo: pathlib.Path, relpath: str) -> bool:
    """git이 실제로 무시하는지 판정한다 — 등록 문자열 존재가 아니라 판정 결과를 본다."""
    result = run_git(["check-ignore", "-q", "--", relpath], cwd=repo, check=False)
    return result.returncode == 0


# ---------------------------------------------------------------- S-7 정상 경로


def test_init_creates_run_root_and_cache_root(tmp_path):
    """신규 실행은 OPPB 태스크 안에, 공유 cache만 allocator에 생성된다."""
    repo = make_hub_repo(tmp_path)
    task_root = make_task_root(repo)
    payload = init_hub(repo, task_root=task_root)

    run_root = pathlib.Path(payload["run_root"])
    cache_root = pathlib.Path(payload["cache_root"])

    assert run_root.is_absolute(), f"run_root가 절대경로가 아님: {run_root}"
    assert cache_root.is_absolute(), f"cache_root가 절대경로가 아님: {cache_root}"
    assert run_root == task_root / ".oppb-run" / payload["run_id"], (
        f"run root 태스크 귀속 계약 위반: {run_root}"
    )
    assert cache_root == repo / ".opal-cache" / "oppb", (
        f"cache root 위치 계약 위반(§4.5): {cache_root}"
    )
    assert run_root.is_dir(), f"run root 디렉토리 미생성: {run_root}"
    assert cache_root.is_dir(), f"cache root 디렉토리 미생성: {cache_root}"
    assert not (repo / ".opal-runs").exists(), "신규 init이 legacy 허브 run root를 생성함"


def test_init_registers_git_info_exclude_idempotently(tmp_path):
    """S-7 ② `.git/info/exclude`에 두 경로가 멱등 등록된다 — 재호출해도 중복 줄이 늘지 않는다."""
    repo = make_hub_repo(tmp_path)
    init_hub(repo)

    first = exclude_lines(repo)
    assert first.count(RUN_ROOT_ENTRY) == 1, f"run root 등록 1회가 아님: {first}"
    assert first.count(CACHE_ROOT_ENTRY) == 1, f"cache root 등록 1회가 아님: {first}"

    init_hub(repo)
    init_hub(repo)

    third = exclude_lines(repo)
    assert third.count(RUN_ROOT_ENTRY) == 1, f"재호출 후 run root 등록이 중복됨: {third}"
    assert third.count(CACHE_ROOT_ENTRY) == 1, f"재호출 후 cache root 등록이 중복됨: {third}"


def test_init_verifies_actual_ignore_decision(tmp_path):
    """S-7 ③ 등록 문자열이 아니라 실제 ignore 판정이 확인된다 — run root·cache root 산출물이
    `git status`에 전혀 나타나지 않는다."""
    repo = make_hub_repo(tmp_path)
    payload = init_hub(repo)
    run_root = pathlib.Path(payload["run_root"])
    cache_root = pathlib.Path(payload["cache_root"])

    (run_root / "workgraph.json").write_text("{}\n", encoding="utf-8")
    (cache_root / "probe.bin").write_text("x", encoding="utf-8")

    assert is_ignored(repo, str((run_root / "workgraph.json").relative_to(repo))), (
        "run root 산출물이 실제로 ignore되지 않음"
    )
    assert is_ignored(repo, str((cache_root / "probe.bin").relative_to(repo))), (
        "cache root 산출물이 실제로 ignore되지 않음"
    )

    status = run_git(["status", "--porcelain"], cwd=repo).stdout
    assert ".oppb-run" not in status, f"run root가 Git 추적 대상으로 노출됨:\n{status}"
    assert ".opal-cache" not in status, f"cache root가 Git 추적 대상으로 노출됨:\n{status}"


# ------------------------------------------------- S-7 allocator_root 인자 계약


def test_init_rejects_missing_allocator_root(tmp_path):
    """S-7 ④ `--allocator-root` 미지정은 cwd 추론 없이 거부된다
    (harness/worktree.md §task root와 allocator root 계약 [MUST])."""
    repo = make_hub_repo(tmp_path)

    task_root = make_task_root(repo)
    result = run_oppb(
        ["init", "--project-root", str(repo), "--task-root", str(task_root)], cwd=repo
    )

    assert result.returncode != 0, (
        f"allocator_root 미지정이 수용됨 — cwd 추론 금지 위반. stdout={result.stdout}"
    )
    combined = f"{result.stdout}\n{result.stderr}"
    assert "allocator" in combined.lower(), f"거부 사유에 allocator_root 언급 없음:\n{combined}"
    assert not (task_root / ".oppb-run").exists(), "거부됐는데 run root가 생성됨"
    assert not (repo / ".opal-cache").exists(), "거부됐는데 cache root가 생성됨(cwd 추론 부작용)"


@pytest.mark.parametrize("relative", [".", "./", "..", "hub", "./hub"])
def test_init_rejects_relative_allocator_root(tmp_path, relative):
    """S-7 ⑤ 상대경로 allocator_root는 거부된다 — cwd 기준 해석을 하지 않는다."""
    repo = make_hub_repo(tmp_path)

    task_root = make_task_root(repo)
    result = run_oppb([
        "init", "--allocator-root", relative, "--project-root", str(repo),
        "--task-root", str(task_root),
    ], cwd=repo)

    assert result.returncode != 0, (
        f"상대경로 allocator_root({relative!r})가 수용됨. stdout={result.stdout}"
    )
    assert not (task_root / ".oppb-run").exists(), (
        f"상대경로({relative!r}) 거부 후에도 run root가 생성됨"
    )


def test_init_rejects_allocator_root_that_is_not_a_git_repository(tmp_path):
    """S-7 ⑥ Git 저장소가 아닌 allocator_root는 거부된다 — `.git/info/exclude` 등록과
    ignore 판정 확인이 성립하지 않기 때문이다."""
    plain = tmp_path / "not-a-repo"
    plain.mkdir()

    task_root = make_task_root(plain)
    result = run_oppb([
        "init", "--allocator-root", str(plain), "--project-root", str(plain),
        "--task-root", str(task_root),
    ])

    assert result.returncode != 0, (
        f"비-git allocator_root가 수용됨. stdout={result.stdout}"
    )
    assert not (task_root / ".oppb-run").exists(), "거부됐는데 run root가 생성됨"


def test_init_rejects_missing_or_relative_task_root(tmp_path):
    """task_root는 명시 절대경로만 허용하고 project_root에서 추론하지 않는다."""
    repo = make_hub_repo(tmp_path)

    missing = run_oppb([
        "init", "--allocator-root", str(repo), "--project-root", str(repo),
    ], cwd=repo)
    relative = run_oppb([
        "init", "--allocator-root", str(repo), "--project-root", str(repo),
        "--task-root", "tasks/200-260926-oppb-sample",
    ], cwd=repo)

    for result in (missing, relative):
        assert result.returncode != 0, result.stdout
        assert "task_root" in f"{result.stdout}\n{result.stderr}", result.stdout
    assert not (repo / ".oppb-run").exists()


# ------------------------------------------- S-7 ignore 판정 확인 실패 시 run 거부


def test_start_refused_when_exclude_entry_removed_and_not_restorable(tmp_path):
    """S-7 ⑦ `.git/info/exclude` 등록을 인위적으로 제거하고 재등록이 불가능한 상태에서
    재호출하면, ignore 판정 확인 실패로 run 시작을 거부한다."""
    repo = make_hub_repo(tmp_path)
    payload = init_hub(repo)
    run_root = payload["run_root"]

    # 등록을 인위적으로 제거하고 재등록을 불가능하게 만든다(실제 파일 권한, mock 아님).
    path = exclude_path(repo)
    path.write_text("# stripped by test\n", encoding="utf-8")
    os.chmod(path, stat.S_IRUSR)
    try:
        assert not is_ignored(repo, ".oppb-run/probe"), "fixture 전제 위반 — 여전히 ignore 상태"

        task_root = make_task_root(repo, parent="tasks-second")
        reinit = run_oppb(
            [
                "init", "--allocator-root", str(repo), "--project-root", str(repo),
                "--task-root", str(task_root),
            ]
        )
        assert reinit.returncode != 0, (
            f"ignore 재등록 불가 상태에서 init이 성공함. stdout={reinit.stdout}"
        )

        start = run_oppb(["start", "--run-root", str(run_root)])
        assert start.returncode != 0, (
            f"ignore 판정 확인 실패 상태에서 run이 시작됨. stdout={start.stdout}"
        )
        combined = f"{start.stdout}\n{start.stderr}"
        assert "ignore" in combined.lower(), f"거부 사유에 ignore 판정 언급 없음:\n{combined}"
    finally:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def test_start_refused_when_gitignore_negation_overrides_exclude(tmp_path):
    """S-7 ⑧ 등록 문자열은 존재하지만 추적 `.gitignore`의 부정 패턴이 우선해 실제로는
    ignore되지 않는 상태 — 문자열 확인만으로는 통과하고 실제 판정으로만 잡힌다.
    이 경우에도 run 시작을 거부해야 한다."""
    repo = make_hub_repo(tmp_path)
    payload = init_hub(repo)
    run_root = payload["run_root"]

    # .gitignore(작업 디렉토리)는 .git/info/exclude보다 우선순위가 높다.
    (repo / ".gitignore").write_text("!.oppb-run/\n!.opal-cache/\n", encoding="utf-8")
    run_git(["add", ".gitignore"], cwd=repo)
    run_git(["commit", "-m", "negate oppb excludes"], cwd=repo)

    assert RUN_ROOT_ENTRY in exclude_lines(repo), "fixture 전제 위반 — exclude 등록이 사라짐"
    assert not is_ignored(repo, ".oppb-run/probe"), (
        "fixture 전제 위반 — 부정 패턴이 우선하지 않음"
    )

    start = run_oppb(["start", "--run-root", str(run_root)])
    assert start.returncode != 0, (
        f"실제 ignore 판정 실패 상태에서 run이 시작됨 — 등록 문자열만 확인한 것으로 보인다. "
        f"stdout={start.stdout}"
    )


def _write_minimal_workgraph(run_root: pathlib.Path, run_id: str) -> None:
    (run_root / "workgraph.json").write_text(
        json.dumps({
            "schema_version": "1.0",
            "revision": 1,
            "run_id": run_id,
            "budget": {"limits": {}, "debited": {}},
            "mini_tasks": [],
        }) + "\n",
        encoding="utf-8",
    )


def test_legacy_hub_run_root_remains_readable_and_resumable(tmp_path):
    """신규 생성은 금지해도 기존 `.opal-runs/<run_id>` status·resume 호환은 유지한다."""
    repo = make_hub_repo(tmp_path)
    path = exclude_path(repo)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{LEGACY_RUN_ROOT_ENTRY}\n")
        handle.write(f"{CACHE_ROOT_ENTRY}\n")
    run_id = "20260920T000000Z-legacy01"
    run_root = repo / ".opal-runs" / run_id
    run_root.mkdir(parents=True)
    (run_root / "run.json").write_text(json.dumps({
        "schema_version": "1.0",
        "run_id": run_id,
        "allocator_root": str(repo),
        "project_root": str(repo),
        "cache_root": str(repo / ".opal-cache" / "oppb"),
        "created_at": "2026-09-20T00:00:00Z",
    }) + "\n", encoding="utf-8")
    _write_minimal_workgraph(run_root, run_id)

    result = run_oppb(["status", "--run-root", str(run_root)])
    payload = parse_json_stdout(result, "legacy status")

    assert result.returncode == 0, payload
    assert payload["run_root"] == str(run_root)

    resumed = run_oppb(["resume", "--run-root", str(run_root)])
    resumed_payload = parse_json_stdout(resumed, "legacy resume")
    assert resumed.returncode == 0, resumed_payload
    assert resumed_payload["run_root"] == str(run_root)


def test_finalize_run_preserves_records_and_removes_transient_files(tmp_path):
    """P5 보존 묶음은 기록·증거를 유지하고 runtime-only 파일만 제거한다."""
    repo = make_hub_repo(tmp_path)
    source_task = make_task_root(repo, parent="workspace/tasks")
    payload = init_hub(repo, task_root=source_task)
    run_root = pathlib.Path(payload["run_root"])
    _write_minimal_workgraph(run_root, payload["run_id"])
    (run_root / "acceptance.json").write_text("{}\n", encoding="utf-8")
    (run_root / "events.jsonl").write_text('{"event":"run_completed"}\n', encoding="utf-8")
    (run_root / "supervisor.log").write_text("finished\n", encoding="utf-8")
    (run_root / "supervisor.lock").write_text("", encoding="utf-8")
    (run_root / "workgraph.lock").write_text("", encoding="utf-8")
    (run_root / "supervisor.json").write_text(
        '{"schema_version":"1.0","supervisor_pid":123,"started_at":1}\n',
        encoding="utf-8",
    )
    (run_root / "checkpoint" / "tmp-index").mkdir(parents=True)
    (run_root / "checkpoint" / "tmp-index" / "index").write_text("tmp", encoding="utf-8")
    (run_root / "verify-sandboxes" / "candidate").mkdir(parents=True)
    (run_root / "verify-sandboxes" / "candidate" / "tmp").write_text("tmp", encoding="utf-8")
    (run_root / "attempts" / "T01" / "a1").mkdir(parents=True)
    (run_root / "attempts" / "T01" / "a1" / "result.json").write_text(
        '{"status":"succeeded"}\n', encoding="utf-8"
    )
    (run_root / "evidence").mkdir()
    (run_root / "evidence" / "accepted.json").write_text("{}\n", encoding="utf-8")

    destination_task = repo / "tasks" / source_task.name
    destination_task.mkdir(parents=True)
    result = run_oppb([
        "finalize-run", "--run-root", str(run_root), "--allocator-root", str(repo),
        "--task-path", str(destination_task),
    ])
    archived = destination_task / ".oppb-run" / payload["run_id"]
    response = parse_json_stdout(result, "finalize-run")

    assert result.returncode == 0, response
    for relpath in (
        "workgraph.json", "acceptance.json", "events.jsonl", "supervisor.log",
        "attempts/T01/a1/result.json", "evidence/accepted.json", "run.closed.json",
    ):
        assert (archived / relpath).is_file(), relpath
    for relpath in (
        "supervisor.lock", "workgraph.lock", "supervisor.json",
        "checkpoint/tmp-index", "verify-sandboxes",
    ):
        assert not (archived / relpath).exists(), relpath
    assert response["archived_run_root"] == str(archived)
    assert response["content_sha256"]

    repeated = run_oppb([
        "finalize-run", "--run-root", str(run_root), "--allocator-root", str(repo),
        "--task-path", str(destination_task),
    ])
    repeated_payload = parse_json_stdout(repeated, "idempotent finalize-run")
    assert repeated.returncode == 0, repeated_payload
    assert repeated_payload["idempotent"] is True
    assert repeated_payload["content_sha256"] == response["content_sha256"]

    status = run_oppb(["status", "--run-root", str(archived)])
    status_payload = parse_json_stdout(status, "archived status")
    assert status.returncode == 0, status_payload
    assert status_payload["archived"] is True
    assert status_payload["supervisor_pid"] is None

    resume = run_oppb(["resume", "--run-root", str(archived)])
    resume_payload = parse_json_stdout(resume, "archived resume")
    assert resume.returncode != 0
    assert resume_payload["error"] == "run_closed"


def test_finalize_run_rejects_incomplete_run_without_archive(tmp_path):
    """실패·중단 run은 종료 보존으로 닫지 않고 원본 전체를 재개 가능하게 둔다."""
    repo = make_hub_repo(tmp_path)
    source_task = make_task_root(repo, parent="workspace/tasks")
    payload = init_hub(repo, task_root=source_task)
    run_root = pathlib.Path(payload["run_root"])
    _write_minimal_workgraph(run_root, payload["run_id"])
    (run_root / "supervisor.lock").write_text("runtime\n", encoding="utf-8")
    destination_task = repo / "tasks" / source_task.name
    destination_task.mkdir(parents=True)

    result = run_oppb([
        "finalize-run", "--run-root", str(run_root), "--allocator-root", str(repo),
        "--task-path", str(destination_task),
    ])
    response = parse_json_stdout(result, "incomplete finalize-run")

    assert result.returncode != 0
    assert response["error"] == "run_not_finalizable"
    assert (run_root / "supervisor.lock").is_file(), "중단 run의 runtime 상태가 제거됨"
    assert not (destination_task / ".oppb-run" / payload["run_id"]).exists()


def test_finalize_run_rejects_symlink_without_reading_external_target(tmp_path):
    """보존 복사가 run root 밖 symlink target을 따라가 기록 묶음에 유입시키지 않는다."""
    repo = make_hub_repo(tmp_path)
    source_task = make_task_root(repo, parent="workspace/tasks")
    payload = init_hub(repo, task_root=source_task)
    run_root = pathlib.Path(payload["run_root"])
    _write_minimal_workgraph(run_root, payload["run_id"])
    (run_root / "events.jsonl").write_text('{"event":"run_completed"}\n', encoding="utf-8")
    external = tmp_path / "external-secret.txt"
    external.write_text("must-not-copy\n", encoding="utf-8")
    (run_root / "evidence-link").symlink_to(external)
    destination_task = repo / "tasks" / source_task.name
    destination_task.mkdir(parents=True)

    result = run_oppb([
        "finalize-run", "--run-root", str(run_root), "--allocator-root", str(repo),
        "--task-path", str(destination_task),
    ])
    response = parse_json_stdout(result, "symlink finalize-run")

    assert result.returncode != 0
    assert response["error"] == "archive_symlink_forbidden"
    assert not (destination_task / ".oppb-run" / payload["run_id"]).exists()


def test_finalize_run_rejects_symlinked_archive_parent(tmp_path):
    """canonical 태스크 안의 `.oppb-run` symlink로 보존 위치를 밖으로 우회할 수 없다."""
    repo = make_hub_repo(tmp_path)
    source_task = make_task_root(repo, parent="workspace/tasks")
    payload = init_hub(repo, task_root=source_task)
    run_root = pathlib.Path(payload["run_root"])
    _write_minimal_workgraph(run_root, payload["run_id"])
    (run_root / "events.jsonl").write_text('{"event":"run_completed"}\n', encoding="utf-8")
    destination_task = repo / "tasks" / source_task.name
    destination_task.mkdir(parents=True)
    external = tmp_path / "outside-archive"
    external.mkdir()
    (destination_task / ".oppb-run").symlink_to(external, target_is_directory=True)

    result = run_oppb([
        "finalize-run", "--run-root", str(run_root), "--allocator-root", str(repo),
        "--task-path", str(destination_task),
    ])
    response = parse_json_stdout(result, "archive parent symlink")

    assert result.returncode != 0
    assert response["error"] == "archive_symlink_forbidden"
    assert list(external.iterdir()) == []


def test_run_root_symlink_is_rejected_before_manifest_read(tmp_path):
    """run root alias로 외부 또는 다른 실행 tree를 읽는 경로 우회를 허용하지 않는다."""
    repo = make_hub_repo(tmp_path)
    payload = init_hub(repo)
    run_root = pathlib.Path(payload["run_root"])
    alias = run_root.parent / "alias-run"
    alias.symlink_to(run_root, target_is_directory=True)

    result = run_oppb(["status", "--run-root", str(alias)])
    response = parse_json_stdout(result, "symlink run root")

    assert result.returncode != 0
    assert response["error"] == "run_root_invalid"


def test_finalize_run_refuses_when_workgraph_lock_is_held(tmp_path):
    """완료 판정과 copy 사이 snapshot을 workgraph lock 없이 만들지 않는다."""
    repo = make_hub_repo(tmp_path)
    source_task = make_task_root(repo, parent="workspace/tasks")
    payload = init_hub(repo, task_root=source_task)
    run_root = pathlib.Path(payload["run_root"])
    _write_minimal_workgraph(run_root, payload["run_id"])
    (run_root / "events.jsonl").write_text('{"event":"run_completed"}\n', encoding="utf-8")
    destination_task = repo / "tasks" / source_task.name
    destination_task.mkdir(parents=True)

    with (run_root / "workgraph.lock").open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = run_oppb([
            "finalize-run", "--run-root", str(run_root), "--allocator-root", str(repo),
            "--task-path", str(destination_task),
        ])
    response = parse_json_stdout(result, "locked finalize-run")

    assert result.returncode != 0
    assert response["error"] == "run_not_finalizable"
    assert not (destination_task / ".oppb-run" / payload["run_id"]).exists()


def test_finalize_run_revalidates_existing_archive_hash(tmp_path):
    """idempotent 재호출은 marker를 맹신하지 않고 보존본의 현재 hash를 다시 계산한다."""
    repo = make_hub_repo(tmp_path)
    source_task = make_task_root(repo, parent="workspace/tasks")
    payload = init_hub(repo, task_root=source_task)
    run_root = pathlib.Path(payload["run_root"])
    _write_minimal_workgraph(run_root, payload["run_id"])
    (run_root / "events.jsonl").write_text('{"event":"run_completed"}\n', encoding="utf-8")
    destination_task = repo / "tasks" / source_task.name
    destination_task.mkdir(parents=True)
    command = [
        "finalize-run", "--run-root", str(run_root), "--allocator-root", str(repo),
        "--task-path", str(destination_task),
    ]
    first = run_oppb(command)
    assert first.returncode == 0, first.stdout
    archived = destination_task / ".oppb-run" / payload["run_id"]
    (archived / "events.jsonl").write_text('{"event":"tampered"}\n', encoding="utf-8")

    repeated = run_oppb(command)
    response = parse_json_stdout(repeated, "tampered archive")

    assert repeated.returncode != 0
    assert response["error"] == "archive_integrity_failed"
    status = run_oppb(["status", "--run-root", str(archived)])
    status_response = parse_json_stdout(status, "tampered archive status")
    assert status.returncode != 0
    assert status_response["error"] == "archive_integrity_failed"


def test_finalize_run_rejects_lock_symlink_without_external_side_effect(tmp_path):
    """lock 획득 전에 symlink를 거부해 외부 target을 생성하거나 열지 않는다."""
    repo = make_hub_repo(tmp_path)
    source_task = make_task_root(repo, parent="workspace/tasks")
    payload = init_hub(repo, task_root=source_task)
    run_root = pathlib.Path(payload["run_root"])
    _write_minimal_workgraph(run_root, payload["run_id"])
    (run_root / "events.jsonl").write_text('{"event":"run_completed"}\n', encoding="utf-8")
    external = tmp_path / "must-not-create.lock"
    (run_root / "supervisor.lock").symlink_to(external)
    destination_task = repo / "tasks" / source_task.name
    destination_task.mkdir(parents=True)

    result = run_oppb([
        "finalize-run", "--run-root", str(run_root), "--allocator-root", str(repo),
        "--task-path", str(destination_task),
    ])
    response = parse_json_stdout(result, "lock symlink")

    assert result.returncode != 0
    assert response["error"] == "archive_symlink_forbidden"
    assert not external.exists()


def test_finalize_run_rejects_symlinked_tasks_ancestor(tmp_path):
    """allocator `tasks` 조상이 symlink면 openat/no-follow 게시가 외부 쓰기 없이 거부한다."""
    repo = make_hub_repo(tmp_path)
    source_task = make_task_root(repo, parent="workspace/tasks")
    payload = init_hub(repo, task_root=source_task)
    run_root = pathlib.Path(payload["run_root"])
    _write_minimal_workgraph(run_root, payload["run_id"])
    (run_root / "events.jsonl").write_text('{"event":"run_completed"}\n', encoding="utf-8")
    external = tmp_path / "outside-tasks"
    destination_task = external / source_task.name
    destination_task.mkdir(parents=True)
    (repo / "tasks").symlink_to(external, target_is_directory=True)

    result = run_oppb([
        "finalize-run", "--run-root", str(run_root), "--allocator-root", str(repo),
        "--task-path", str(repo / "tasks" / source_task.name),
    ])
    response = parse_json_stdout(result, "tasks ancestor symlink")

    assert result.returncode != 0
    assert response["error"] == "archive_task_path_invalid"
    assert not (destination_task / ".oppb-run").exists()


def test_finalize_run_hash_frames_file_boundaries(tmp_path):
    """파일 경계가 다른 tree가 SHA 충돌 없이 같은 보존 hash를 만들 수 없다."""
    repo = make_hub_repo(tmp_path)
    source_task = make_task_root(repo, parent="workspace/tasks")
    payload = init_hub(repo, task_root=source_task)
    run_root = pathlib.Path(payload["run_root"])
    _write_minimal_workgraph(run_root, payload["run_id"])
    (run_root / "events.jsonl").write_text('{"event":"run_completed"}\n', encoding="utf-8")
    destination_task = repo / "tasks" / source_task.name
    destination_task.mkdir(parents=True)
    command = [
        "finalize-run", "--run-root", str(run_root), "--allocator-root", str(repo),
        "--task-path", str(destination_task),
    ]
    (run_root / "a").write_bytes(b"xb\0")
    (run_root / "c").write_bytes(b"Y")
    first = parse_json_stdout(run_oppb(command), "framed hash A")

    shutil.rmtree(destination_task / ".oppb-run" / payload["run_id"])
    (run_root / "a").write_bytes(b"x")
    (run_root / "c").unlink()
    (run_root / "b").write_bytes(b"c\0Y")
    second = parse_json_stdout(run_oppb(command), "framed hash B")

    assert first["content_sha256"] != second["content_sha256"]


# --------------------------------------------------------- S-7 C-5 플랫폼 분기 금지


@pytest.mark.parametrize(
    "pattern",
    ["sys.platform", "platform.system", "platform.mac_ver", "uname", "darwin", "Darwin"],
)
def test_no_platform_branching_in_tool_source(pattern):
    """S-7 ⑨ C-5 — 플랫폼 분기는 `scripts/install-mac.sh` 어댑터 계층에만 존재하고
    `oppb-runtime-tool` 소스에는 0건이어야 한다."""
    sources = sorted(
        p
        for p in TOOL_DIR.rglob("*")
        if p.is_file()
        and p.suffix in {".py", ".sh"}
        and "tests" not in p.relative_to(TOOL_DIR).parts
    )
    assert sources, (
        "RED: oppb-runtime-tool 소스 파일 0건 — W-6~W-9 구현 전 정상 실패. "
        f"탐색 루트={TOOL_DIR}"
    )

    hits = [
        f"{p.relative_to(TOOL_DIR)}:{i}"
        for p in sources
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        if pattern in line
    ]
    assert not hits, f"플랫폼 분기 문자열 {pattern!r} 발견(C-5 위반): {hits}"
