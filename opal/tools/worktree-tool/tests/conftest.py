"""
@header {
  "module": "conftest",
  "layer": "test",
  "domain": "opal-workspace",
  "description": "worktree-tool pytest fixture — tmp_path에 실 git 저장소(유형 A multi-repo: bare remote 2 + clone 2, 유형 B monorepo: bare remote 1 + workspace/tasks/.opal 4디렉토리 clone)를 subprocess로 구성한다. RED-first 트랙(092) — 실 git 저장소만 사용, mock/patch 금지. 공개 인터페이스(CLI subprocess)로만 검증하기 위한 run_worktree_cli/run_state_cli 헬퍼와, worktree_tool.py 미구현 상태에서 remove/status/list의 선행 상태(가드 4종·메타 파일)를 재현하기 위한 raw git 헬퍼(add_worktree/write_meta 등)를 제공한다. 모든 git 호출에 -c user.email=test@opal.local -c user.name='OPAL Test' -c commit.gpgsign=false -c init.defaultBranch=main 주입(TEST-SCENARIO.md §2.1 [MUST]).",
  "exports": [
    "run_git", "make_bare_remote", "make_monorepo_bare_remote", "clone_repo",
    "write_json", "add_worktree", "write_meta", "ProjectA", "ProjectB", "GuardRepo",
    "project_a", "project_b", "build_guard_repo",
    "run_worktree_cli", "run_state_cli", "WORKTREE_TOOL_PATH", "STATE_TOOL_PATH", "OPAL_DIR"
  ],
  "depends": ["git CLI 2.50+", "opal/tools/git-sync-tool/tests/conftest.py(패턴 원천)"]
}
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass, field

import pytest

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
    """
    저장소 fixture 구성 + 가드 상태 조작 전용 git 실행 헬퍼.
    전역 git config에 의존하지 않도록 -c user.email/-c user.name/-c commit.gpgsign/
    -c init.defaultBranch을 항상 주입한다 (TEST-SCENARIO.md §2.1 [MUST]).
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
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: pathlib.Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def make_bare_remote(base: pathlib.Path, name: str) -> pathlib.Path:
    """base 아래 bare 저장소를 생성하고 초기 커밋 1개(main)가 있는 상태로 준비한다."""
    bare_path = base / f"{name}.git"
    bare_path.mkdir(parents=True)
    run_git(["init", "--bare", "-b", "main", str(bare_path)], cwd=base)

    seed_path = base / f"{name}-seed"
    run_git(["clone", str(bare_path), str(seed_path)], cwd=base)
    _write_file(seed_path, "README.md", f"# {name}\ninitial\n")
    run_git(["add", "README.md"], cwd=seed_path)
    run_git(["commit", "-m", "initial commit"], cwd=seed_path)
    run_git(["push", "origin", "main"], cwd=seed_path)
    return bare_path


def make_monorepo_bare_remote(base: pathlib.Path, name: str) -> pathlib.Path:
    """유형 B(monorepo) bare remote — workspace/backend, workspace/frontend, tasks/, .opal/
    4디렉토리에 각각 파일 1개를 커밋한 main 브랜치를 준비한다."""
    bare_path = base / f"{name}.git"
    bare_path.mkdir(parents=True)
    run_git(["init", "--bare", "-b", "main", str(bare_path)], cwd=base)

    seed_path = base / f"{name}-seed"
    run_git(["clone", str(bare_path), str(seed_path)], cwd=base)
    _write_file(seed_path, "workspace/backend/app.py", "# backend\n")
    _write_file(seed_path, "workspace/frontend/app.js", "// frontend\n")
    _write_file(seed_path, "tasks/README.md", "# tasks\n")
    _write_file(seed_path, ".opal/README.md", "# opal\n")
    run_git(["add", "-A"], cwd=seed_path)
    run_git(["commit", "-m", "initial monorepo commit"], cwd=seed_path)
    run_git(["push", "origin", "main"], cwd=seed_path)
    return bare_path


def clone_repo(bare_path: pathlib.Path, dest_parent: pathlib.Path, name: str) -> pathlib.Path:
    """bare_path를 dest_parent/name으로 clone한다."""
    dest_parent.mkdir(parents=True, exist_ok=True)
    dest = dest_parent / name
    run_git(["clone", str(bare_path), str(dest)], cwd=dest_parent)
    return dest


def add_worktree(
    repo_root: pathlib.Path, branch: str, dest: pathlib.Path, base: str = "main"
) -> None:
    """`git worktree add -b <branch> <dest> <base>` — worktree_tool.py의 create가 아직 없으므로
    remove/status의 선행 상태를 raw git으로 재현하기 위한 헬퍼."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    run_git(["worktree", "add", "-b", branch, str(dest), base], cwd=repo_root)


def write_meta(
    project_root: pathlib.Path,
    task: str,
    layout: str,
    branch: str,
    entries: list[dict],
    pending_setup: list | None = None,
    worktree_root: pathlib.Path | None = None,
) -> pathlib.Path:
    """PLAN §3.2.3 메타 파일 스키마대로 `.opal-worktrees/.meta/task_{NNN}.json`을 직접 기록한다.
    worktree_tool.py의 create가 아직 없으므로(RED), remove/status를 단독으로 검증하기 위해
    선행 상태를 이 헬퍼로 조립한다 — 이 스키마 자체가 GREEN 구현이 지켜야 할 계약이다."""
    wt_root = worktree_root or (project_root / ".opal-worktrees" / f"task_{task}")
    meta = {
        "task": task,
        "layout": layout,
        "branch": branch,
        "created_at": "2026-08-15 00:00",
        "worktree_root": str(wt_root),
        "entries": entries,
        "pending_setup": pending_setup or [],
    }
    meta_path = project_root / ".opal-worktrees" / ".meta" / f"task_{task}.json"
    write_json(meta_path, meta)
    return meta_path


# ─────────────────────────────────────────────────────────────────────────────
# 유형 A (multi-repo) — bare remote 2 + clone 2 + 프로젝트 루트
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ProjectA:
    root: pathlib.Path
    remotes_dir: pathlib.Path
    origin_be: pathlib.Path
    origin_fe: pathlib.Path
    backend: pathlib.Path
    frontend: pathlib.Path
    config_path: pathlib.Path


def _write_multi_repo_config(project_root: pathlib.Path, repos: list[str]) -> pathlib.Path:
    config_path = project_root / ".opal" / "worktree.json"
    write_json(
        config_path,
        {
            "layout": "multi-repo",
            "repos": repos,
            "branchTemplate": "feat/OP-TASK-{NNN}",
            "copy": [],
            "setup": [],
            "portOffset": 0,
        },
    )
    return config_path


@pytest.fixture
def project_a(tmp_path: pathlib.Path) -> ProjectA:
    """유형 A — origin_be.git/origin_fe.git bare remote + workspace/{backend,frontend} clone +
    `.opal/worktree.json`(multi-repo)."""
    remotes_dir = tmp_path / "_remotes"
    remotes_dir.mkdir()
    project_root = tmp_path / "proj_a"
    project_root.mkdir()

    origin_be = make_bare_remote(remotes_dir, "origin_be")
    origin_fe = make_bare_remote(remotes_dir, "origin_fe")
    backend = clone_repo(origin_be, project_root / "workspace", "backend")
    frontend = clone_repo(origin_fe, project_root / "workspace", "frontend")

    config_path = _write_multi_repo_config(
        project_root, ["workspace/backend", "workspace/frontend"]
    )
    (project_root / ".gitignore").write_text("*.pyc\n", encoding="utf-8")

    return ProjectA(
        root=project_root,
        remotes_dir=remotes_dir,
        origin_be=origin_be,
        origin_fe=origin_fe,
        backend=backend,
        frontend=frontend,
        config_path=config_path,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 유형 B (monorepo) — bare remote 1(4디렉토리) + clone 1 + 프로젝트 루트(=clone)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ProjectB:
    root: pathlib.Path
    remotes_dir: pathlib.Path
    origin_mono: pathlib.Path
    config_path: pathlib.Path


@pytest.fixture
def project_b(tmp_path: pathlib.Path) -> ProjectB:
    """유형 B — workspace/backend·workspace/frontend·tasks/·.opal/ 4디렉토리를 가진 monorepo
    bare remote + clone(=프로젝트 루트) + `.opal/worktree.json`(monorepo, repos=["workspace"])."""
    remotes_dir = tmp_path / "_remotes"
    remotes_dir.mkdir()
    origin_mono = make_monorepo_bare_remote(remotes_dir, "origin_mono")
    project_root = clone_repo(origin_mono, tmp_path, "proj_b")

    config_path = project_root / ".opal" / "worktree.json"
    write_json(
        config_path,
        {
            "layout": "monorepo",
            "repos": ["workspace"],
            "branchTemplate": "feat/OP-TASK-{NNN}",
            "copy": [],
            "setup": [],
            "portOffset": 100,
        },
    )

    return ProjectB(
        root=project_root,
        remotes_dir=remotes_dir,
        origin_mono=origin_mono,
        config_path=config_path,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 가드 상태 저장소 (dirty/unpushed/unmerged/clean) — 단일 repo, multi-repo layout(N=1)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class GuardRepo:
    project_root: pathlib.Path
    origin: pathlib.Path
    repo: pathlib.Path  # git_root == project_root/workspace/app (메인 clone)
    wt_path: pathlib.Path  # worktree 디렉토리
    branch: str
    task: str
    base_ref: str = "main"


def build_guard_repo(tmp_path: pathlib.Path, state: str, name_suffix: str = "") -> GuardRepo:
    """가드 상태 4종(dirty/unpushed/unmerged/clean)을 raw git으로 재현한다.
    base_ref는 항상 "main"(DEC-3 우선순위 3 — 현재 체크아웃 브랜치명 fallback과 동형)으로
    고정해 메타에 동결 기록한다. worktree_tool.py의 create가 없으므로 add_worktree()로
    선행 상태를 직접 구성한다."""
    assert state in ("dirty", "unpushed", "unmerged", "clean")
    task = "092"
    branch = f"feat/OP-TASK-{task}"

    remotes_dir = tmp_path / f"_remotes{name_suffix}"
    remotes_dir.mkdir()
    project_root = tmp_path / f"proj_guard_{state}{name_suffix}"
    project_root.mkdir()

    origin = make_bare_remote(remotes_dir, "origin_app")
    repo = clone_repo(origin, project_root / "workspace", "app")

    _write_multi_repo_config(project_root, ["workspace/app"])

    wt_root = project_root / ".opal-worktrees" / f"task_{task}"
    dest = wt_root / "workspace" / "app"
    add_worktree(repo, branch, dest, base="main")

    if state == "dirty":
        # 추적 파일을 수정만 하고 커밋하지 않는다.
        (dest / "README.md").write_text("# app\nuncommitted change\n", encoding="utf-8")

    elif state == "unpushed":
        _write_file(dest, "local-only.txt", "local change\n")
        run_git(["add", "local-only.txt"], cwd=dest)
        run_git(["commit", "-m", "local commit, not pushed"], cwd=dest)
        # push 안 함 → upstream 없음 → base_ref(main) 대비 ahead 1

    elif state == "unmerged":
        _write_file(dest, "feature.txt", "feature change\n")
        run_git(["add", "feature.txt"], cwd=dest)
        run_git(["commit", "-m", "feature commit"], cwd=dest)
        run_git(["push", "-u", "origin", branch], cwd=dest)
        # push 완료(upstream==HEAD → unpushed 0) 이지만 main엔 미머지

    elif state == "clean":
        _write_file(dest, "feature.txt", "feature change\n")
        run_git(["add", "feature.txt"], cwd=dest)
        run_git(["commit", "-m", "feature commit"], cwd=dest)
        run_git(["push", "-u", "origin", branch], cwd=dest)
        # repo(git_root)는 현재 main 체크아웃 상태 — 그대로 merge 가능
        run_git(["merge", branch], cwd=repo)

    write_meta(
        project_root,
        task,
        layout="multi-repo",
        branch=branch,
        entries=[
            {
                "repo": str(repo),
                "path": str(dest),
                "branch": branch,
                "base_ref": "main",
            }
        ],
        worktree_root=wt_root,
    )

    return GuardRepo(
        project_root=project_root,
        origin=origin,
        repo=repo,
        wt_path=dest,
        branch=branch,
        task=task,
        base_ref="main",
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI 실행 헬퍼 — 공개 인터페이스(subprocess)로만 검증한다 (red-first.md §4)
# ─────────────────────────────────────────────────────────────────────────────

TESTS_DIR = pathlib.Path(__file__).resolve().parent
WORKTREE_TOOL_DIR = TESTS_DIR.parent  # opal/tools/worktree-tool
WORKTREE_TOOL_PATH = WORKTREE_TOOL_DIR / "worktree_tool.py"

# opal/tools/worktree-tool/tests -> .../opal/tools -> .../opal(내부) -> .../opal(저장소 루트)
OPAL_DIR = WORKTREE_TOOL_DIR.parents[1]  # .../opal/opal (내부 패키지 루트: skills/, core/, tools/)
REPO_ROOT = OPAL_DIR.parent  # .../opal (저장소 루트)

STATE_TOOL_PATH = OPAL_DIR / "tools" / "state-tool" / "state_tool.py"


def run_worktree_cli(args: list[str]) -> subprocess.CompletedProcess:
    """공개 인터페이스(CLI 서브프로세스 호출)로만 worktree-tool을 검증한다.
    내부 함수 import 금지(red-first §4). worktree_tool.py가 아직 없으므로(RED)
    exit code != 0 + stdout 파싱 실패가 정상이다."""
    return subprocess.run(
        [sys.executable, str(WORKTREE_TOOL_PATH), *args],
        capture_output=True,
        text=True,
    )


def run_state_cli(args: list[str]) -> subprocess.CompletedProcess:
    """공개 인터페이스(CLI 서브프로세스 호출)로 state-tool을 검증한다(S-24 파이프라인 관통).
    run.sh(venv 위임)를 거치지 않고 스크립트를 직접 호출해 venv 유무에 대한 의존을 없앤다."""
    return subprocess.run(
        [sys.executable, str(STATE_TOOL_PATH), *args],
        capture_output=True,
        text=True,
    )


def parse_json_stdout(result: subprocess.CompletedProcess, label: str = "") -> dict:
    """stdout을 JSON으로 파싱한다. 실패하면 pytest.fail로 명확한 증거를 남긴다
    (worktree_tool.py 미구현 상태에서는 이 실패 자체가 RED 증거)."""
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"{label} stdout이 유효 JSON이 아님 (RED 예상 — worktree_tool.py 미구현). "
            f"exit={result.returncode}\nstdout={result.stdout!r}\nstderr={result.stderr!r}\n"
            f"원인: {exc}"
        )
