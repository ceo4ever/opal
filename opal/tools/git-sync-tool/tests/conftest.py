"""
@header {
  "module": "conftest",
  "layer": "test",
  "domain": "opal-workspace",
  "description": "git-sync-tool pytest fixture — tmp_path에 로컬 bare remote + 상태별 clone 8종(behind/current/dirty/diverged/detached/noupstream/fetchfail 및 이들을 담는 workspace 컨테이너)을 subprocess로 구성한다. root 저장소 시나리오용으로 자체가 git 저장소인 프로젝트 루트 + 그 아래 workspace/ 컨테이너 구조(project_root_with_workspace)도 제공한다. RED-first 트랙(052) — 실 git 저장소만 사용, mock/patch 금지. 전역 git config 의존 제거를 위해 모든 git 호출에 -c user.email/-c user.name 주입.",
  "exports": ["run_git", "make_bare_remote", "clone_repo", "GitFixtureWorkspace", "git_workspace", "GitProjectRootFixture", "project_root_with_workspace"],
  "depends": ["git CLI 2.22+"]
}
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
from dataclasses import dataclass, field

import pytest

GIT_AUTHOR_ARGS = [
    "-c",
    "user.email=git-sync-tool-test@example.com",
    "-c",
    "user.name=git-sync-tool-test",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "init.defaultBranch=main",
]


def run_git(args: list[str], cwd: pathlib.Path, check: bool = True) -> subprocess.CompletedProcess:
    """
    저장소 fixture 구성 전용 git 실행 헬퍼.
    전역 git config에 의존하지 않도록 -c user.email/-c user.name/-c commit.gpgsign을 항상 주입한다.
    """
    cmd = ["git", *GIT_AUTHOR_ARGS, *args]
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git fixture 구성 실패: {' '.join(cmd)}\n"
            f"cwd={cwd}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def _write_file(repo: pathlib.Path, name: str, content: str) -> None:
    (repo / name).write_text(content, encoding="utf-8")


def make_bare_remote(base: pathlib.Path, name: str) -> pathlib.Path:
    """base 아래 bare 저장소를 생성하고 초기 커밋 1개가 있는 seed 브랜치까지 준비한다."""
    bare_path = base / f"{name}.git"
    bare_path.mkdir(parents=True)
    run_git(["init", "--bare", "-b", "main", str(bare_path)], cwd=base)

    # bare에는 직접 커밋할 수 없으므로 임시 작업 클론을 통해 초기 커밋을 push한다.
    seed_path = base / f"{name}-seed"
    run_git(["clone", str(bare_path), str(seed_path)], cwd=base)
    _write_file(seed_path, "README.md", f"# {name}\ninitial\n")
    run_git(["add", "README.md"], cwd=seed_path)
    run_git(["commit", "-m", "initial commit"], cwd=seed_path)
    run_git(["push", "origin", "main"], cwd=seed_path)
    return bare_path


def clone_repo(bare_path: pathlib.Path, dest_parent: pathlib.Path, name: str) -> pathlib.Path:
    """bare_path를 dest_parent/name으로 clone한다."""
    dest = dest_parent / name
    run_git(["clone", str(bare_path), str(dest)], cwd=dest_parent)
    return dest


def push_extra_commits(bare_path: pathlib.Path, tmp_root: pathlib.Path, count: int, tag: str) -> None:
    """
    bare_path의 main 브랜치에 count개의 추가 커밋을 별도 워킹 클론을 통해 push한다.
    (behind-only 상황 구성용 — 이 push는 target clone의 fetch 전에 이뤄져야 behind로 관측된다)
    """
    pusher = tmp_root / f"pusher-{tag}"
    run_git(["clone", str(bare_path), str(pusher)], cwd=tmp_root)
    for i in range(count):
        _write_file(pusher, f"extra-{tag}-{i}.txt", f"extra commit {i}\n")
        run_git(["add", f"extra-{tag}-{i}.txt"], cwd=pusher)
        run_git(["commit", "-m", f"remote extra commit {i}"], cwd=pusher)
    run_git(["push", "origin", "main"], cwd=pusher)


@dataclass
class GitFixtureWorkspace:
    """구성된 fixture 전체를 표현하는 컨테이너. 각 저장소 경로 + workspace 루트를 보유."""

    root: pathlib.Path  # tmp_path 자체
    workspace: pathlib.Path  # sync 대상 컨테이너 디렉토리
    repo_behind: pathlib.Path
    repo_current: pathlib.Path
    repo_dirty: pathlib.Path
    repo_diverged: pathlib.Path
    repo_detached: pathlib.Path
    repo_noupstream: pathlib.Path
    repo_fetchfail: pathlib.Path
    behind_n: int = field(default=2)


@pytest.fixture
def git_workspace(tmp_path: pathlib.Path) -> GitFixtureWorkspace:
    """
    workspace/ 아래 직속 자식으로 8종 상태의 clone을 배치한 fixture.
    각 저장소는 독립 bare remote를 사용 (repo 간 간섭 방지).
    """
    remotes_dir = tmp_path / "_remotes"
    remotes_dir.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    behind_n = 2

    # ---- repo_behind: clean, 원격이 N커밋 앞섬 (clone 후 remote push, fetch 전) ----
    bare_behind = make_bare_remote(remotes_dir, "behind")
    repo_behind = clone_repo(bare_behind, workspace, "repo_behind")
    push_extra_commits(bare_behind, tmp_path, behind_n, "behind")
    # repo_behind 로컬 clone은 아직 fetch하지 않았으므로 behind 상태 유지됨.

    # ---- repo_current: clean, 원격==로컬 (clone 직후 그대로) ----
    bare_current = make_bare_remote(remotes_dir, "current")
    repo_current = clone_repo(bare_current, workspace, "repo_current")

    # ---- repo_dirty: 작업트리 미커밋 변경 ----
    bare_dirty = make_bare_remote(remotes_dir, "dirty")
    repo_dirty = clone_repo(bare_dirty, workspace, "repo_dirty")
    _write_file(repo_dirty, "README.md", "# dirty\nuncommitted change\n")

    # ---- repo_diverged: ahead>0 AND behind>0 (로컬 커밋1 + 원격 커밋1) ----
    bare_diverged = make_bare_remote(remotes_dir, "diverged")
    repo_diverged = clone_repo(bare_diverged, workspace, "repo_diverged")
    # 로컬에 커밋 1개 (push 안 함 → ahead)
    _write_file(repo_diverged, "local-only.txt", "local change\n")
    run_git(["add", "local-only.txt"], cwd=repo_diverged)
    run_git(["commit", "-m", "local ahead commit"], cwd=repo_diverged)
    # 원격에 별도 커밋 1개 push (behind 유발) — repo_diverged는 fetch 전이므로 아직 모름
    push_extra_commits(bare_diverged, tmp_path, 1, "diverged")

    # ---- repo_detached: detached HEAD ----
    bare_detached = make_bare_remote(remotes_dir, "detached")
    repo_detached = clone_repo(bare_detached, workspace, "repo_detached")
    head_sha = run_git(["rev-parse", "HEAD"], cwd=repo_detached).stdout.strip()
    run_git(["checkout", head_sha], cwd=repo_detached)

    # ---- repo_noupstream: upstream 없는 로컬 브랜치 ----
    bare_noupstream = make_bare_remote(remotes_dir, "noupstream")
    repo_noupstream = clone_repo(bare_noupstream, workspace, "repo_noupstream")
    run_git(["checkout", "-b", "feature/no-upstream"], cwd=repo_noupstream)

    # ---- repo_fetchfail: origin URL을 존재하지 않는 경로로 변경 ----
    bare_fetchfail = make_bare_remote(remotes_dir, "fetchfail")
    repo_fetchfail = clone_repo(bare_fetchfail, workspace, "repo_fetchfail")
    nonexistent = tmp_path / "_does_not_exist" / "nope.git"
    run_git(["remote", "set-url", "origin", str(nonexistent)], cwd=repo_fetchfail)

    return GitFixtureWorkspace(
        root=tmp_path,
        workspace=workspace,
        repo_behind=repo_behind,
        repo_current=repo_current,
        repo_dirty=repo_dirty,
        repo_diverged=repo_diverged,
        repo_detached=repo_detached,
        repo_noupstream=repo_noupstream,
        repo_fetchfail=repo_fetchfail,
        behind_n=behind_n,
    )


@dataclass
class GitProjectRootFixture:
    """자체가 git 저장소인 프로젝트 루트 + 그 아래 workspace/ 컨테이너 구조."""

    root: pathlib.Path  # tmp_path 자체 (git 아님)
    project: pathlib.Path  # 프로젝트 루트 = root 저장소 (clean, behind N)
    workspace: pathlib.Path  # project/workspace — git 아닌 컨테이너
    child: pathlib.Path  # project/workspace/repo_child (clean, behind N)
    behind_n: int = field(default=2)


@pytest.fixture
def project_root_with_workspace(tmp_path: pathlib.Path) -> GitProjectRootFixture:
    """
    opws STEP 1 첫 분기(`<경로>/workspace` 존재)에서 root 저장소가 순회 대상 밖에 놓이는 구조를 재현한다.
    project/ 자체가 git 저장소이고, 그 아래 workspace/ 컨테이너에 자식 저장소가 있다.
    project는 workspace/를 .gitignore로 무시해 clean 상태를 유지한다 (자식 clone이 dirty를 유발하지 않도록).
    """
    remotes_dir = tmp_path / "_remotes"
    remotes_dir.mkdir()

    behind_n = 2

    # ---- project: 프로젝트 루트 = root 저장소 ----
    bare_project = make_bare_remote(remotes_dir, "project")
    project = clone_repo(bare_project, tmp_path, "project")
    _write_file(project, ".gitignore", "workspace/\n")
    run_git(["add", ".gitignore"], cwd=project)
    run_git(["commit", "-m", "ignore workspace container"], cwd=project)
    run_git(["push", "origin", "main"], cwd=project)
    # 원격을 N커밋 앞세워 root 저장소를 behind(=pull 대상)로 만든다.
    push_extra_commits(bare_project, tmp_path, behind_n, "project")

    # ---- project/workspace: git 아닌 컨테이너 + 자식 저장소 ----
    workspace = project / "workspace"
    workspace.mkdir()
    bare_child = make_bare_remote(remotes_dir, "child")
    child = clone_repo(bare_child, workspace, "repo_child")
    push_extra_commits(bare_child, tmp_path, behind_n, "child")

    return GitProjectRootFixture(
        root=tmp_path,
        project=project,
        workspace=workspace,
        child=child,
        behind_n=behind_n,
    )


@pytest.fixture
def single_repo_root(tmp_path: pathlib.Path) -> pathlib.Path:
    """S-10: 경로 자체가 단일 git 루트인 fixture (workspace 컨테이너 없이 clone 1개만)."""
    remotes_dir = tmp_path / "_remotes"
    remotes_dir.mkdir()
    bare = make_bare_remote(remotes_dir, "single")
    repo = clone_repo(bare, tmp_path, "solo_repo")
    return repo


GIT_SYNC_TOOL_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "git_sync_tool.py"
)


def run_sync_cli(
    workspace_path: pathlib.Path, *extra_args: str
) -> subprocess.CompletedProcess:
    """
    공개 인터페이스(CLI 호출)로만 도구를 검증한다. 내부 함수 import 금지 (red-first §4).
    extra_args는 `--root <경로>` 등 옵션을 그대로 전달한다.
    """
    return subprocess.run(
        [
            sys.executable,
            str(GIT_SYNC_TOOL_PATH),
            "sync",
            str(workspace_path),
            *extra_args,
        ],
        capture_output=True,
        text=True,
    )
