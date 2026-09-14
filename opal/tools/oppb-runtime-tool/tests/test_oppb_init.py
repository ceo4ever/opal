"""
@header {
  "module": "test_oppb_init",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "oppb-runtime-tool init 공개 CLI 계약 RED 테스트. 132 TEST-SCENARIO.md S-7(AC-1, C-4, C-5, H-2)을 검증한다 — 깨끗한 허브 저장소에서 init이 run root(.opal-runs/<run_id>/)와 cache root(.opal-cache/oppb/)를 생성하고, allocator Git repository의 .git/info/exclude에 두 경로를 멱등 등록한 뒤 실제 ignore 판정(git check-ignore)을 확인하며, 판정 확인에 실패하면 run 시작을 거부하고, --allocator-root 미지정·상대경로를 cwd 추론 없이 거부하며, 소스에 플랫폼 분기 문자열이 없는지 확인한다. PLAN H-6에 따라 내부 함수·클래스를 import하지 않고 공개 CLI(run.sh)와 run root 파일 계약으로만 검증한다. mock/patch 금지 — 실제 git 저장소와 실제 파일만 사용한다(PLAN W-10).",
  "exports": [],
  "depends": ["opal/tools/oppb-runtime-tool/run.sh", "git CLI 2.x", "opal/tools/worktree-tool/tests/conftest.py(패턴 원천)"]
}
"""

from __future__ import annotations

import json
import os
import pathlib
import stat
import subprocess

import pytest

# opal/tools/oppb-runtime-tool/tests -> opal/tools/oppb-runtime-tool
TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
RUN_SH = TOOL_DIR / "run.sh"

RUN_ROOT_ENTRY = ".opal-runs/"
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


def init_hub(repo: pathlib.Path, cwd: pathlib.Path | None = None) -> dict:
    """정상 init 1회. run_id·run_root·cache_root를 담은 JSON 응답을 돌려준다."""
    result = run_oppb(
        ["init", "--allocator-root", str(repo), "--project-root", str(repo)], cwd=cwd
    )
    assert result.returncode == 0, (
        f"init 실패: exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    payload = parse_json_stdout(result, "init")
    for key in ("run_id", "run_root", "cache_root"):
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
    """S-7 ① 정상 호출에서 `.opal-runs/<run_id>/`와 `.opal-cache/oppb/`가 생성된다."""
    repo = make_hub_repo(tmp_path)
    payload = init_hub(repo)

    run_root = pathlib.Path(payload["run_root"])
    cache_root = pathlib.Path(payload["cache_root"])

    assert run_root.is_absolute(), f"run_root가 절대경로가 아님: {run_root}"
    assert cache_root.is_absolute(), f"cache_root가 절대경로가 아님: {cache_root}"
    assert run_root == repo / ".opal-runs" / payload["run_id"], (
        f"run root 위치 계약 위반(§4.5): {run_root}"
    )
    assert cache_root == repo / ".opal-cache" / "oppb", (
        f"cache root 위치 계약 위반(§4.5): {cache_root}"
    )
    assert run_root.is_dir(), f"run root 디렉토리 미생성: {run_root}"
    assert cache_root.is_dir(), f"cache root 디렉토리 미생성: {cache_root}"


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
    assert ".opal-runs" not in status, f"run root가 Git 추적 대상으로 노출됨:\n{status}"
    assert ".opal-cache" not in status, f"cache root가 Git 추적 대상으로 노출됨:\n{status}"


# ------------------------------------------------- S-7 allocator_root 인자 계약


def test_init_rejects_missing_allocator_root(tmp_path):
    """S-7 ④ `--allocator-root` 미지정은 cwd 추론 없이 거부된다
    (harness/worktree.md §task root와 allocator root 계약 [MUST])."""
    repo = make_hub_repo(tmp_path)

    result = run_oppb(["init", "--project-root", str(repo)], cwd=repo)

    assert result.returncode != 0, (
        f"allocator_root 미지정이 수용됨 — cwd 추론 금지 위반. stdout={result.stdout}"
    )
    combined = f"{result.stdout}\n{result.stderr}"
    assert "allocator" in combined.lower(), f"거부 사유에 allocator_root 언급 없음:\n{combined}"
    assert not (repo / ".opal-runs").exists(), "거부됐는데 run root가 생성됨(cwd 추론 부작용)"
    assert not (repo / ".opal-cache").exists(), "거부됐는데 cache root가 생성됨(cwd 추론 부작용)"


@pytest.mark.parametrize("relative", [".", "./", "..", "hub", "./hub"])
def test_init_rejects_relative_allocator_root(tmp_path, relative):
    """S-7 ⑤ 상대경로 allocator_root는 거부된다 — cwd 기준 해석을 하지 않는다."""
    repo = make_hub_repo(tmp_path)

    result = run_oppb(
        ["init", "--allocator-root", relative, "--project-root", str(repo)], cwd=repo
    )

    assert result.returncode != 0, (
        f"상대경로 allocator_root({relative!r})가 수용됨. stdout={result.stdout}"
    )
    assert not (repo / ".opal-runs").exists(), (
        f"상대경로({relative!r}) 거부 후에도 run root가 생성됨"
    )


def test_init_rejects_allocator_root_that_is_not_a_git_repository(tmp_path):
    """S-7 ⑥ Git 저장소가 아닌 allocator_root는 거부된다 — `.git/info/exclude` 등록과
    ignore 판정 확인이 성립하지 않기 때문이다."""
    plain = tmp_path / "not-a-repo"
    plain.mkdir()

    result = run_oppb(["init", "--allocator-root", str(plain), "--project-root", str(plain)])

    assert result.returncode != 0, (
        f"비-git allocator_root가 수용됨. stdout={result.stdout}"
    )
    assert not (plain / ".opal-runs").exists(), "거부됐는데 run root가 생성됨"


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
        assert not is_ignored(repo, ".opal-runs/probe"), "fixture 전제 위반 — 여전히 ignore 상태"

        reinit = run_oppb(
            ["init", "--allocator-root", str(repo), "--project-root", str(repo)]
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
    (repo / ".gitignore").write_text("!.opal-runs/\n!.opal-cache/\n", encoding="utf-8")
    run_git(["add", ".gitignore"], cwd=repo)
    run_git(["commit", "-m", "negate oppb excludes"], cwd=repo)

    assert RUN_ROOT_ENTRY in exclude_lines(repo), "fixture 전제 위반 — exclude 등록이 사라짐"
    assert not is_ignored(repo, ".opal-runs/probe"), (
        "fixture 전제 위반 — 부정 패턴이 우선하지 않음"
    )

    start = run_oppb(["start", "--run-root", str(run_root)])
    assert start.returncode != 0, (
        f"실제 ignore 판정 실패 상태에서 run이 시작됨 — 등록 문자열만 확인한 것으로 보인다. "
        f"stdout={start.stdout}"
    )


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
