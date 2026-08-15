"""
@header {
  "module": "worktree_tool",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "태스크별 코드 작업본을 git worktree로 격리하는 CLI. `.opal/worktree.json`(multi-repo/monorepo 2유형)을 선언 기반으로 읽어 create/list/status/remove 4서브명령을 제공한다. create의 슬롯·브랜치 판정은 '존재'가 아니라 '점유'다(DEC-7) — 대상 경로가 `git worktree list --porcelain`에 실제 등록돼 있으면 WORKTREE_EXISTS, 브랜치가 다른 worktree에 체크아웃 중이면 BRANCH_EXISTS로 거부하고, 브랜치가 존재하지만 미점유면 `worktree add <path> <branch>` 단일 명령으로 재사용한다(빈 디렉토리 잔존은 차단 사유가 아니다). pre-flight(대상 미점유·repos 경로 실재·git 레포 여부) 전부 통과 후에만 worktree를 생성하고(all-or-nothing), 중간 실패 시 자기 생성물만 롤백한다(DEC-2, 신규 브랜치 경로에만 적용). base-ref는 create 시점에 1회 해석해 `.opal-worktrees/.meta/task_{NNN}.json`(worktree 밖)에 동결 기록하고 remove/status는 그 값만 읽는다(DEC-3, 재해석 없음). remove는 dirty→unpushed→unmerged 순서로 3중 가드를 적용하고 worktree 디렉토리 + 슬롯 루트(`task_{NNN}/`)를 회수한다(브랜치 보존, user sovereignty. `.opal-worktrees/`·`.meta/`는 남긴다). `.gitignore`·캐시 볼륨·code-scan exclude·동시 슬롯 수는 전부 비차단 진단이다.",
  "exports": [
    "load_config", "validate_worktree_config", "resolve_base_ref", "check_guards",
    "ensure_gitignore_entry", "diagnose_cache_volume", "diagnose_code_scan_exclude",
    "diagnose_concurrent_slots", "cmd_create", "cmd_list", "cmd_status", "cmd_remove"
  ],
  "depends": ["git CLI 2.25+"]
}
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
from datetime import datetime
from typing import NoReturn

# ─────────────────────────────────────────────────────────────────────────────
# 에러 코드 카탈로그 (git_sync_tool.py:23-26 패턴, PLAN §3.2.2)
# ─────────────────────────────────────────────────────────────────────────────
ERROR_CODES = {
    "CONFIG_NOT_FOUND": "'.opal/worktree.json' 설정 파일을 찾을 수 없습니다.",
    "CONFIG_INVALID_JSON": "'.opal/worktree.json' 파일이 유효한 JSON이 아닙니다.",
    "CONFIG_MISSING_KEY": "필수 키가 누락되었습니다.",
    "CONFIG_INVALID_LAYOUT": "'layout' 값이 유효하지 않습니다. 'multi-repo' 또는 'monorepo'만 허용됩니다.",
    "CONFIG_INVALID_TYPE": "설정 값의 타입이 유효하지 않습니다.",
    "CONFIG_PATH_ESCAPE": "경로가 프로젝트 루트를 벗어납니다.",
    "PROJECT_ROOT_NOT_FOUND": "지정한 프로젝트 루트가 존재하지 않습니다.",
    "WORKTREE_EXISTS": "대상 worktree 경로가 이미 존재합니다.",
    "BRANCH_EXISTS": "브랜치가 이미 존재합니다.",
    "REPO_NOT_FOUND": "지정된 repos 경로가 존재하지 않습니다.",
    "NOT_A_GIT_REPO": "지정된 경로가 git 저장소가 아닙니다.",
    "GIT_COMMAND_FAILED": "git 명령이 실패했습니다.",
    "META_NOT_FOUND": "메타 파일을 찾을 수 없습니다. --force로만 우회할 수 있습니다.",
    "WORKTREE_NOT_FOUND": "메타는 있으나 실제 worktree 경로가 존재하지 않습니다.",
    "GUARD_DIRTY": "작업본에 미커밋 변경 사항이 있습니다.",
    "GUARD_UNPUSHED": "원격에 반영되지 않은 커밋이 있습니다.",
    "GUARD_UNMERGED": "base 브랜치에 아직 병합되지 않았습니다.",
    "INTERNAL_ERROR": "예상하지 못한 오류가 발생했습니다.",
}

GITIGNORE_ENTRY = ".opal-worktrees/"


# ─────────────────────────────────────────────────────────────────────────────
# 응답 계약 — git_sync_tool.py:29-42 완전 동형
# ─────────────────────────────────────────────────────────────────────────────


def ok_response(**kwargs):
    payload = {"ok": True, "error": None, **kwargs}
    print(json.dumps(payload, ensure_ascii=False, default=str))


def err_response(code, exit_code=1, **kwargs) -> NoReturn:
    message = ERROR_CODES.get(code, code)
    payload = {"ok": False, "error": code, "message": message, **kwargs}
    print(json.dumps(payload, ensure_ascii=False, default=str))
    sys.exit(exit_code)


# ─────────────────────────────────────────────────────────────────────────────
# git 호출 헬퍼 — 리스트 인자, shell=True 금지(injection 방지)
# ─────────────────────────────────────────────────────────────────────────────


def _run_git(args: list, cwd: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


class GitFailure(Exception):
    """_git_or_raise가 git 명령 실패 시 발생시키는 예외. stderr 원문을 보존한다."""

    def __init__(self, stderr: str):
        self.stderr = stderr
        super().__init__(stderr)


def _git_or_raise(cwd: pathlib.Path, args: list) -> subprocess.CompletedProcess:
    result = _run_git(args, cwd)
    if result.returncode != 0:
        raise GitFailure(result.stderr)
    return result


def _branch_exists(git_root: pathlib.Path, branch: str) -> bool:
    result = _run_git(["branch", "--list", branch], git_root)
    return bool(result.stdout.strip())


def _worktree_entries(git_root: pathlib.Path) -> list:
    """`git worktree list --porcelain` 파싱 (DEC-7 ④). 각 항목:
    {"worktree": <절대경로 str>, "branch": <브랜치명 또는 None(detached)>}."""
    result = _run_git(["worktree", "list", "--porcelain"], git_root)
    entries = []
    current = None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            if current is not None:
                entries.append(current)
            current = {"worktree": line[len("worktree ") :], "branch": None}
        elif line.startswith("branch ") and current is not None:
            current["branch"] = line[len("branch ") :].removeprefix("refs/heads/")
    if current is not None:
        entries.append(current)
    return entries


def _dest_registered(git_root: pathlib.Path, dest: pathlib.Path) -> bool:
    """dest가 git_root에 실제 worktree로 등록돼 있는지 판정 — 디렉토리 존재가 아니라
    git이 알고 있는 worktree인지가 기준이다(DEC-7 슬롯 존재 판정 변경: '존재' → '점유')."""
    dest_norm = os.path.normpath(str(dest))
    return any(
        os.path.normpath(e["worktree"]) == dest_norm
        for e in _worktree_entries(git_root)
    )


def _branch_occupied(git_root: pathlib.Path, branch: str) -> bool:
    """branch가 git_root의 어느 worktree에서든 체크아웃(점유) 중인지 판정(DEC-7 브랜치 판정
    변경: '존재' → '점유'). git이 이미 점유 중인 브랜치의 재`add`를 자체 거부하므로(PLAN §1.4
    DEC-7 실측 ③), 이 판정은 그 신호를 사전에 BRANCH_EXISTS로 옮기는 역할을 한다."""
    return any(e["branch"] == branch for e in _worktree_entries(git_root))


# ─────────────────────────────────────────────────────────────────────────────
# config 로더 + 검증 (F-001, PLAN §3.1.3)
# ─────────────────────────────────────────────────────────────────────────────


def _resolve_project_root(raw: str) -> pathlib.Path:
    path = pathlib.Path(raw)
    if not path.is_dir():
        err_response("PROJECT_ROOT_NOT_FOUND", path=str(path))
    return path


def load_config(project_root: pathlib.Path) -> dict:
    """{project_root}/.opal/worktree.json 로드. 부재→CONFIG_NOT_FOUND, 파싱실패→CONFIG_INVALID_JSON."""
    config_path = project_root / ".opal" / "worktree.json"
    if not config_path.is_file():
        err_response("CONFIG_NOT_FOUND", path=str(config_path))
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        err_response("CONFIG_INVALID_JSON", path=str(config_path))


def _is_inside(project_root: pathlib.Path, rel: str) -> bool:
    """os.path.normpath 후 project_root 하위인지 판정. 심볼릭 링크는 해석하지 않는다
    (경로 문자열 기준 — Path.resolve()/os.path.realpath()를 쓰지 않는다, PLAN §3.1.3)."""
    if os.path.isabs(rel):
        return False
    root_norm = os.path.normpath(str(project_root))
    combined = os.path.normpath(os.path.join(root_norm, rel))
    return combined == root_norm or combined.startswith(root_norm + os.sep)


def validate_worktree_config(cfg: dict, project_root: pathlib.Path) -> dict:
    """검증 통과 시 기본값이 채워진 정규화 dict 반환. 위반 시 err_response로 즉시 종료(exit).

    검증 순서(첫 위반에서 즉시 반환 — 결정론): dict 타입 → 필수 키(layout/repos) →
    layout 유효값 → repos 타입/공백 → repos 경로 이탈 → copy 타입/경로 이탈 →
    branchTemplate/baseBranch 타입 → setup 타입 → portOffset 타입.
    """
    if not isinstance(cfg, dict):
        err_response("CONFIG_INVALID_TYPE", key="root")

    if "layout" not in cfg:
        err_response("CONFIG_MISSING_KEY", key="layout")
    if "repos" not in cfg:
        err_response("CONFIG_MISSING_KEY", key="repos")

    layout = cfg["layout"]
    if layout not in ("multi-repo", "monorepo"):
        err_response("CONFIG_INVALID_LAYOUT", value=layout)

    repos = cfg["repos"]
    if (
        not isinstance(repos, list)
        or not repos
        or not all(isinstance(r, str) for r in repos)
    ):
        err_response("CONFIG_INVALID_TYPE", key="repos")
    for rel in repos:
        if not _is_inside(project_root, rel):
            err_response("CONFIG_PATH_ESCAPE", value=rel)

    copy = cfg.get("copy", [])
    if not isinstance(copy, list) or not all(isinstance(c, str) for c in copy):
        err_response("CONFIG_INVALID_TYPE", key="copy")
    for rel in copy:
        if not _is_inside(project_root, rel):
            err_response("CONFIG_PATH_ESCAPE", value=rel)

    branch_template = cfg.get("branchTemplate", "feat/OP-TASK-{NNN}")
    if not isinstance(branch_template, str):
        err_response("CONFIG_INVALID_TYPE", key="branchTemplate")

    base_branch = cfg.get("baseBranch")
    if base_branch is not None and not isinstance(base_branch, str):
        err_response("CONFIG_INVALID_TYPE", key="baseBranch")

    setup = cfg.get("setup", [])
    if not isinstance(setup, list):
        err_response("CONFIG_INVALID_TYPE", key="setup")
    for item in setup:
        if not isinstance(item, dict) or "cwd" not in item or "run" not in item:
            err_response("CONFIG_INVALID_TYPE", key="setup")

    port_offset = cfg.get("portOffset", 0)
    if (
        not isinstance(port_offset, int)
        or isinstance(port_offset, bool)
        or port_offset < 0
    ):
        err_response("CONFIG_INVALID_TYPE", key="portOffset")

    return {
        "layout": layout,
        "repos": repos,
        "branchTemplate": branch_template,
        "baseBranch": base_branch,
        "copy": copy,
        "setup": setup,
        "portOffset": port_offset,
    }


def _render_branch(
    template: str, task: str, slug: str | None, skill: str | None
) -> str:
    result = template.replace("{NNN}", task)
    if slug:
        result = result.replace("{slug}", slug)
    if skill:
        result = result.replace("{skill}", skill)
    return result


def resolve_base_ref(git_root: pathlib.Path, declared: str | None) -> str:
    """DEC-3 3단 우선순위, 1곳에 봉인 — create 시점에만 호출한다(remove/status는 메타 값만 사용)."""
    if declared:
        return declared
    result = _run_git(["symbolic-ref", "refs/remotes/origin/HEAD"], git_root)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip().removeprefix("refs/remotes/")
    result2 = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], git_root)
    return result2.stdout.strip()


# ─────────────────────────────────────────────────────────────────────────────
# create 부수 효과 — .gitignore 멱등 / 캐시 볼륨 / code-scan exclude / 동시 슬롯 (F-007, F-009, DEC-5, DEC-6)
# ─────────────────────────────────────────────────────────────────────────────


def ensure_gitignore_entry(
    project_root: pathlib.Path, entry: str = GITIGNORE_ENTRY
) -> str:
    """루트 .gitignore에 entry를 멱등 보장. 반환: "created" | "added" | "present".

    이미 있으면 파일에 write를 하지 않는다 — 바이트 단위 무변경(TASK F-7 AC).
    """
    gitignore_path = project_root / ".gitignore"
    stripped = entry.rstrip("/")
    if not gitignore_path.exists():
        gitignore_path.write_text(entry + "\n", encoding="utf-8")
        return "created"

    content = gitignore_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        if line.strip() in (entry, stripped):
            return "present"

    if content and not content.endswith("\n"):
        content += "\n"
    content += entry + "\n"
    gitignore_path.write_text(content, encoding="utf-8")
    return "added"


def diagnose_cache_volume(project_root: pathlib.Path) -> list:
    """캐시·프로젝트 볼륨(st_dev) 불일치를 경고 문자열 리스트로 반환. 절대 차단하지 않는다.

    예외(경로 부재·권한 오류·st_dev 미지원)는 모두 삼켜 빈 리스트를 반환한다.
    """
    try:
        cache_dir = os.environ.get("UV_CACHE_DIR")
        cache_path = (
            pathlib.Path(cache_dir)
            if cache_dir
            else (pathlib.Path.home() / ".cache" / "uv")
        )
        if not cache_path.exists() or not project_root.exists():
            return []
        cache_dev = os.stat(cache_path).st_dev
        project_dev = os.stat(project_root).st_dev
        if cache_dev != project_dev:
            return [
                f"uv 캐시({cache_path}, dev={cache_dev})가 프로젝트({project_root}, dev={project_dev})와 "
                "다른 볼륨입니다 — 슬롯당 .venv가 실복사됩니다. UV_CACHE_DIR을 프로젝트와 같은 볼륨으로 "
                "옮기면 제거됩니다."
            ]
        return []
    except OSError:
        return []


def diagnose_code_scan_exclude(project_root: pathlib.Path) -> list:
    """DEC-5(b). {project_root}/.opal/code-scan.json이 있고 exclude에 '.opal-worktrees'가 없으면
    경고 1건. 파일을 수정하지 않는다(DEC-5 (c) 제외 결정). 파일 부재·파싱 실패는 빈 리스트."""
    try:
        code_scan_path = project_root / ".opal" / "code-scan.json"
        if not code_scan_path.is_file():
            return []
        cfg = json.loads(code_scan_path.read_text(encoding="utf-8"))
        exclude = cfg.get("exclude", [])
        if ".opal-worktrees" not in exclude:
            return [
                ".opal/code-scan.json의 exclude에 '.opal-worktrees'가 없습니다 — worktree 사본이 "
                "code-scan 대상에 포함되어 커버리지 지표가 왜곡될 수 있습니다."
            ]
        return []
    except (OSError, json.JSONDecodeError):
        return []


def diagnose_concurrent_slots(project_root: pathlib.Path) -> list:
    """DEC-6. 이번 슬롯 포함 동시 활성 슬롯이 2개 이상이면 공유 자원 충돌 주의 경고.
    비차단(ok:true 유지)이며 파일을 수정하지 않는다. list 로직(메타 디렉토리 열거)을 재사용한다."""
    try:
        meta_dir = project_root / ".opal-worktrees" / ".meta"
        existing = len(list(meta_dir.glob("task_*.json"))) if meta_dir.is_dir() else 0
        total = existing + 1  # 이번에 생성될 슬롯 포함
        if total >= 2:
            return [
                f"동시 슬롯 {total}개 — 공유 자원(개발 DB·포트·compose 프로젝트명) 충돌 주의"
            ]
        return []
    except OSError:
        return []


def _copy_local_files(
    project_root: pathlib.Path, wt_root: pathlib.Path, copy_list: list, warnings: list
):
    """copy[] 값을 worktree로 복사한다. 원본 부재는 비차단 경고."""
    copied = []
    warnings = list(warnings)
    for rel in copy_list:
        src = project_root / rel
        if not src.is_file():
            warnings.append(f"copy 원본 파일 없음(비차단): {rel}")
            continue
        dest = wt_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(rel)
    return copied, warnings


# ─────────────────────────────────────────────────────────────────────────────
# 메타 파일 — {project_root}/.opal-worktrees/.meta/task_{NNN}.json (DEC-3, worktree 밖)
# ─────────────────────────────────────────────────────────────────────────────


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _meta_path(project_root: pathlib.Path, task: str) -> pathlib.Path:
    return project_root / ".opal-worktrees" / ".meta" / f"task_{task}.json"


def _write_meta(
    project_root, task, cfg, branch, created, base_refs, pending_setup
) -> None:
    wt_root = project_root / ".opal-worktrees" / f"task_{task}"
    meta = {
        "task": task,
        "layout": cfg["layout"],
        "branch": branch,
        "created_at": _now_str(),
        "worktree_root": str(wt_root),
        "entries": [
            {
                "repo": str(gr),
                "path": str(path),
                "branch": b,
                "base_ref": base_refs[str(gr)],
            }
            for gr, path, b in created
        ],
        "pending_setup": pending_setup,
    }
    meta_path = _meta_path(project_root, task)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_meta(project_root: pathlib.Path, task: str) -> dict:
    meta_path = _meta_path(project_root, task)
    if not meta_path.is_file():
        err_response("META_NOT_FOUND", path=str(meta_path))
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        err_response("META_NOT_FOUND", path=str(meta_path))


def _delete_meta(project_root: pathlib.Path, task: str) -> None:
    meta_path = _meta_path(project_root, task)
    if meta_path.exists():
        meta_path.unlink()


# ─────────────────────────────────────────────────────────────────────────────
# 가드 판정 — dirty→unpushed→unmerged 고정 순서, 첫 위반 즉시 반환 (F-008, PLAN §3.8.2)
# ─────────────────────────────────────────────────────────────────────────────

GUARD_ORDER = ("dirty", "unpushed", "unmerged")


def _inspect(
    wt_path: pathlib.Path, git_root: pathlib.Path, branch: str, base_ref: str
) -> dict:
    """dirty(bool)/unpushed(int)/merged(bool) 원값을 계산한다. 거부하지 않는다 — status가 그대로 노출한다."""
    dirty = bool(_run_git(["status", "--porcelain"], wt_path).stdout.strip())

    upstream = _run_git(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], wt_path
    )
    ref = upstream.stdout.strip() if upstream.returncode == 0 else base_ref
    count_res = _run_git(["rev-list", f"{ref}..HEAD", "--count"], wt_path)
    try:
        unpushed = int(count_res.stdout.strip() or 0)
    except ValueError:
        unpushed = 0

    merged_res = _run_git(
        ["branch", "--merged", base_ref, "--format=%(refname:short)"], git_root
    )
    merged_branches = merged_res.stdout.split()
    merged = branch in merged_branches

    return {"dirty": dirty, "unpushed": unpushed, "merged": merged}


def check_guards(
    wt_path: pathlib.Path, git_root: pathlib.Path, branch: str, base_ref: str
):
    """(위반 코드 | None, 상세 dict) 반환. 판정 순서는 dirty→unpushed→unmerged 고정(첫 위반 즉시 반환)."""
    info = _inspect(wt_path, git_root, branch, base_ref)
    if info["dirty"]:
        return "GUARD_DIRTY", info
    if info["unpushed"] > 0:
        return "GUARD_UNPUSHED", info
    if not info["merged"]:
        return "GUARD_UNMERGED", info
    return None, info


# ─────────────────────────────────────────────────────────────────────────────
# create 서브명령 (F-002, DEC-2·DEC-3 집행)
# ─────────────────────────────────────────────────────────────────────────────


def _rollback(created: list, wt_root: pathlib.Path) -> None:
    """자기 생성물만 회수한다(DEC-2 all-or-nothing) — worktree remove --force + branch -D."""
    for git_root, path, branch in created:
        _run_git(["worktree", "remove", "--force", str(path)], git_root)
        _run_git(["branch", "-D", branch], git_root)
    if wt_root.exists():
        shutil.rmtree(wt_root, ignore_errors=True)


def cmd_create(args) -> None:
    project_root = _resolve_project_root(args.project_root)
    cfg = validate_worktree_config(load_config(project_root), project_root)
    branch = _render_branch(cfg["branchTemplate"], args.task, args.slug, args.skill)
    wt_root = project_root / ".opal-worktrees" / f"task_{args.task}"

    # ── (1) pre-flight — 여기서 실패하면 아무것도 만들지 않는다 (DEC-2)
    # 슬롯·브랜치 판정 기준은 '존재'가 아니라 '점유'다(DEC-7) — 빈 디렉토리 잔존은
    # 차단 사유가 아니며, 재생성이 영구 차단되는 결함(H-22)을 이 판정 전환으로 없앤다. ──
    for rel in cfg["repos"]:
        src = project_root / rel
        if not src.is_dir():
            err_response("REPO_NOT_FOUND", path=rel)
    plan_entries = (
        [(project_root / rel, wt_root / rel) for rel in cfg["repos"]]
        if cfg["layout"] == "multi-repo"
        else [(project_root, wt_root)]
    )
    git_roots = [git_root for git_root, _dest in plan_entries]
    for git_root, dest in plan_entries:
        if not (git_root / ".git").exists():
            err_response("NOT_A_GIT_REPO", path=str(git_root))
        if _dest_registered(git_root, dest):
            err_response("WORKTREE_EXISTS", path=str(dest))
        if _branch_occupied(git_root, branch):
            err_response("BRANCH_EXISTS", branch=branch, repo=str(git_root))

    # ── (2) 부수 효과(비파괴) ──
    gitignore_state = ensure_gitignore_entry(project_root)
    warnings = diagnose_cache_volume(project_root)
    warnings += diagnose_code_scan_exclude(project_root)
    warnings += diagnose_concurrent_slots(project_root)

    # ── (3) base-ref 해석 + 동결 (DEC-3) ──
    base_refs = {
        str(git_root): resolve_base_ref(git_root, cfg.get("baseBranch"))
        for git_root in git_roots
    }

    # ── (4) worktree 생성 — 실패 시 자기 생성물만 롤백 (DEC-2)
    # 각 레포에 브랜치가 이미 존재하는지(미점유 — (1)에서 점유는 이미 거부됨)로 경로가
    # 갈린다(DEC-7):
    #   - 브랜치 미존재 → 신규 브랜치 경로. [MUST] `git worktree add -b <branch> ...`를 단일
    #     명령으로 실행하면, git이 브랜치 ref를 먼저 만든 뒤 .git/worktrees/ 메타 등록 단계에서
    #     실패하는 경우(예: 이 단계만 권한 문제로 막힘) 브랜치가 고아 상태로 남는다 — 실패 시
    #     rollback은 "성공한 worktree add"만 대상으로 하므로 이 고아 브랜치는 회수되지 않고,
    #     재실행이 BRANCH_EXISTS로 영구 차단된다(H-7 위반). 그래서 worktree 등록(--detach)과
    #     브랜치 생성(checkout -b)을 분리한다 — worktree add가 실패하면 애초에 브랜치가 생성되지
    #     않으므로 롤백 대상 자체가 사라진다.
    #   - 브랜치 존재(미점유) → 재사용 경로. 브랜치를 만들지 않으므로 고아 브랜치 리스크가
    #     없다 — `worktree add <path> <branch>` 단일 명령으로 충분하다(DEC-7 근거).
    created = []
    try:
        if cfg["layout"] == "multi-repo":
            for rel in cfg["repos"]:
                git_root = project_root / rel
                dest = wt_root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                created.append((git_root, dest, branch))
                if _branch_exists(git_root, branch):
                    _git_or_raise(git_root, ["worktree", "add", str(dest), branch])
                else:
                    _git_or_raise(
                        git_root,
                        [
                            "worktree",
                            "add",
                            "--detach",
                            str(dest),
                            base_refs[str(git_root)],
                        ],
                    )
                    _git_or_raise(dest, ["checkout", "-b", branch])
        else:  # monorepo — 순서 [MUST]: --no-checkout → init --cone → set → checkout(-b)/materialize
            git_root = project_root
            created.append((git_root, wt_root, branch))
            reuse = _branch_exists(git_root, branch)
            if reuse:
                _git_or_raise(
                    git_root, ["worktree", "add", "--no-checkout", str(wt_root), branch]
                )
            else:
                _git_or_raise(
                    git_root,
                    [
                        "worktree",
                        "add",
                        "--no-checkout",
                        "--detach",
                        str(wt_root),
                        base_refs[str(git_root)],
                    ],
                )
            _git_or_raise(wt_root, ["sparse-checkout", "init", "--cone"])
            _git_or_raise(wt_root, ["sparse-checkout", "set", *cfg["repos"]])
            if not reuse:
                _git_or_raise(wt_root, ["checkout", "-b", branch])
            # `--no-checkout`로 만든 worktree는 인덱스가 비어 있어 detached HEAD(신규)나 이미
            # 선택된 브랜치(재사용)와 동일 커밋을 가리키는 것만으로는 sparse 패턴이 실제 파일로
            # 물질화되지 않는다(git이 "트리 변경 없음"으로 판단해 작업 디렉토리 갱신을 건너뜀).
            # reset --hard로 강제 반영한다.
            _git_or_raise(wt_root, ["reset", "--hard", "HEAD"])
    except GitFailure as exc:
        _rollback(created, wt_root)
        err_response("GIT_COMMAND_FAILED", detail=exc.stderr, rolled_back=len(created))

    # ── (5) copy[] — 원본 부재는 비차단 경고 ──
    copied, warnings = _copy_local_files(project_root, wt_root, cfg["copy"], warnings)

    # ── (6) setup[]은 실행하지 않는다 (C-7 lazy) — 열거만 ──
    pending_setup = cfg["setup"]

    _write_meta(project_root, args.task, cfg, branch, created, base_refs, pending_setup)
    ok_response(
        command="create",
        task=args.task,
        layout=cfg["layout"],
        worktree_root=str(wt_root),
        branch=branch,
        entries=[
            {"repo": str(g), "path": str(p), "branch": b, "base_ref": base_refs[str(g)]}
            for g, p, b in created
        ],
        gitignore=gitignore_state,
        copied=copied,
        pending_setup=pending_setup,
        port_offset=cfg["portOffset"],
        warnings=warnings,
    )


# ─────────────────────────────────────────────────────────────────────────────
# list / status / remove (F-002, F-008)
# ─────────────────────────────────────────────────────────────────────────────


def cmd_list(args) -> None:
    project_root = _resolve_project_root(args.project_root)
    cfg = validate_worktree_config(load_config(project_root), project_root)

    entries = []
    meta_dir = project_root / ".opal-worktrees" / ".meta"
    if meta_dir.is_dir():
        for meta_file in sorted(meta_dir.glob("task_*.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            wt_root = pathlib.Path(meta.get("worktree_root", ""))
            entries.append(
                {
                    "task": meta.get("task"),
                    "branch": meta.get("branch"),
                    "worktree_root": meta.get("worktree_root"),
                    "exists": wt_root.exists(),
                }
            )

    ok_response(
        command="list",
        project_root=str(project_root),
        layout=cfg["layout"],
        entries=entries,
    )


def cmd_status(args) -> None:
    project_root = _resolve_project_root(args.project_root)
    meta = _load_meta(project_root, args.task)

    entries_out = []
    for entry in meta.get("entries", []):
        git_root = pathlib.Path(entry["repo"])
        wt_path = pathlib.Path(entry["path"])
        branch = entry["branch"]
        base_ref = entry["base_ref"]

        if not wt_path.exists():
            entries_out.append(
                {
                    "repo": entry["repo"],
                    "path": entry["path"],
                    "branch": branch,
                    "base_ref": base_ref,
                    "dirty": None,
                    "unpushed": None,
                    "merged": None,
                    "worktree_missing": True,
                }
            )
            continue

        info = _inspect(wt_path, git_root, branch, base_ref)
        entries_out.append(
            {
                "repo": entry["repo"],
                "path": entry["path"],
                "branch": branch,
                "base_ref": base_ref,
                "dirty": info["dirty"],
                "unpushed": info["unpushed"],
                "merged": info["merged"],
            }
        )

    ok_response(
        command="status",
        task=args.task,
        branch=meta.get("branch"),
        worktree_root=meta.get("worktree_root"),
        entries=entries_out,
        pending_setup=meta.get("pending_setup", []),
    )


def cmd_remove(args) -> None:
    project_root = _resolve_project_root(args.project_root)
    meta = _load_meta(project_root, args.task)
    entries = meta.get("entries", [])

    # ── (1) 가드 판정 — 첫 위반에서 즉시 반환. --force면 우회하고 계속 ──
    bypassed_guards = []
    for entry in entries:
        git_root = pathlib.Path(entry["repo"])
        wt_path = pathlib.Path(entry["path"])
        branch = entry["branch"]
        base_ref = entry["base_ref"]

        if not wt_path.exists():
            if args.force:
                continue
            err_response("WORKTREE_NOT_FOUND", path=str(wt_path))

        code, info = check_guards(wt_path, git_root, branch, base_ref)
        if code:
            if args.force:
                if code not in bypassed_guards:
                    bypassed_guards.append(code)
            else:
                err_response(code, **info)

    # ── (2) 실제 제거 — worktree 디렉토리만 회수, 브랜치는 삭제하지 않는다 ──
    removed = []
    for entry in entries:
        git_root = pathlib.Path(entry["repo"])
        wt_path = pathlib.Path(entry["path"])
        if not wt_path.exists():
            continue
        remove_args = ["worktree", "remove", str(wt_path)]
        if args.force:
            remove_args.append("--force")
        _run_git(remove_args, git_root)
        removed.append(entry["path"])

    _delete_meta(project_root, args.task)

    # ── (3) 슬롯 루트 회수 (DEC-7 정리 범위 확장) ──
    # 레포별 worktree 경로(entry["path"])만 회수하면 그 상위 디렉토리(예: multi-repo의
    # `task_{NNN}/workspace/`)와 슬롯 루트 자체(`task_{NNN}/`)가 빈 껍데기로 남아 같은 번호
    # 재생성이 WORKTREE_EXISTS로 영구 차단된다(H-22, revup 실측). `.opal-worktrees/` 자체와
    # `.meta/`는 다른 슬롯이 쓰므로 남긴다 — 회수 대상은 `task_{NNN}/` 이하뿐이다.
    wt_root = pathlib.Path(
        meta.get("worktree_root")
        or str(project_root / ".opal-worktrees" / f"task_{args.task}")
    )
    if wt_root.exists():
        shutil.rmtree(wt_root, ignore_errors=True)

    ok_response(
        command="remove",
        task=args.task,
        removed=removed,
        forced=bool(args.force),
        bypassed_guards=bypassed_guards,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="worktree_tool")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_create = subparsers.add_parser("create")
    p_create.add_argument("--project-root", required=True)
    p_create.add_argument("--task", required=True)
    p_create.add_argument("--slug", default=None)
    p_create.add_argument("--skill", default=None)
    p_create.set_defaults(func=cmd_create)

    p_list = subparsers.add_parser("list")
    p_list.add_argument("--project-root", required=True)
    p_list.set_defaults(func=cmd_list)

    p_status = subparsers.add_parser("status")
    p_status.add_argument("--project-root", required=True)
    p_status.add_argument("--task", required=True)
    p_status.set_defaults(func=cmd_status)

    p_remove = subparsers.add_parser("remove")
    p_remove.add_argument("--project-root", required=True)
    p_remove.add_argument("--task", required=True)
    p_remove.add_argument("--force", action="store_true")
    p_remove.set_defaults(func=cmd_remove)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — 트레이스백 유출 방지, 통제된 JSON으로 대체 (S-28)
        err_response("INTERNAL_ERROR", detail=str(exc))
