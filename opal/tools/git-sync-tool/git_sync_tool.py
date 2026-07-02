"""
@header {
  "module": "git_sync_tool",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "워크스페이스 아래 여러 독립 git 저장소를 순회하며 안전하게 일괄 최신화(clean+ff-only pull)하는 CLI. 대상 결정(단일 git 루트 또는 직속 자식 1단계, 재귀 금지) → 저장소별 판정(detached→no-upstream→dirty→fetch→diverged/ff) → JSON 결과 출력. git 2.22+ 필요 (rev-list --left-right --count). detached HEAD에서는 @{u} 조회 자체가 fatal로 실패해 no-upstream과 구분되지 않으므로 detached 판정을 no-upstream보다 먼저 수행한다. dirty/diverged/detached/no-upstream 저장소에는 stash/rebase/force/commit/push 등 자율 조치를 일절 수행하지 않는다(skip 후 보고만) — 헌법 user sovereignty 원칙.",
  "exports": ["cmd_sync", "process_repo", "discover_targets"],
  "depends": ["git CLI 2.22+"]
}
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import subprocess

# ─────────────────────────────────────────────────────────────────────────────
# 에러 코드 카탈로그 (state_tool.py:66-100 패턴)
# ─────────────────────────────────────────────────────────────────────────────
ERROR_CODES = {
    "PATH_NOT_FOUND": "지정한 경로가 존재하지 않습니다: {path}",
    "NOT_A_DIRECTORY": "지정한 경로가 디렉토리가 아닙니다: {path}",
}


def ok_response(**kwargs):
    payload = {"ok": True, "error": None, **kwargs}
    print(json.dumps(payload, ensure_ascii=False, default=str))


def err_response(code, path=None, exit_code=1):
    message = ERROR_CODES.get(code, code)
    try:
        message = message.format(path=path)
    except (KeyError, IndexError):
        pass
    payload = {"ok": False, "error": code, "message": message}
    print(json.dumps(payload, ensure_ascii=False, default=str))
    sys.exit(exit_code)


# ─────────────────────────────────────────────────────────────────────────────
# git 호출 헬퍼 — 모두 인자 리스트 방식(shell=True 금지, injection 방지)
# ─────────────────────────────────────────────────────────────────────────────

def _run_git(args, repo_path):
    """subprocess.run 래퍼. cwd=repo_path, capture_output=True, text=True."""
    return subprocess.run(
        ["git", *args],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 대상 순회 로직
# ─────────────────────────────────────────────────────────────────────────────

def discover_targets(path: pathlib.Path):
    """
    path/.git 존재 → 그 1개를 대상 (단일 루트).
    아니면 → path의 직속 자식 1단계만, 이름순 정렬, child/.git 존재하는 것만 대상.
    재귀하지 않는다.
    """
    if (path / ".git").exists():
        return [path]

    targets = []
    for child in sorted(path.iterdir(), key=lambda p: p.name):
        if child.is_dir() and (child / ".git").exists():
            targets.append(child)
    return targets


# ─────────────────────────────────────────────────────────────────────────────
# 저장소별 처리 — 판정 순서 [MUST] 확정 (PLAN §3.1.2(d))
# ─────────────────────────────────────────────────────────────────────────────

def process_repo(repo_path: pathlib.Path) -> dict:
    name = repo_path.name

    result = {
        "name": name,
        "branch": None,
        "upstream": None,
        "status": None,
        "reason": None,
        "ahead": None,
        "behind": None,
        "prev_head": None,
        "new_head": None,
        "pulled_commits": 0,
    }

    # 1. 현재 브랜치 — "HEAD"이면 detached 후보 (@{u} 조회 자체가 fatal로 실패하여
    #    no-upstream과 구분이 안 되므로, detached 여부를 먼저 확정해 순서를 보정한다).
    branch_res = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
    result["branch"] = branch_res.stdout.strip() if branch_res.returncode == 0 else None

    # detached 판정 (symbolic-ref -q HEAD 실패 = HEAD가 브랜치를 가리키지 않음)
    detached_res = _run_git(["symbolic-ref", "-q", "HEAD"], repo_path)
    if detached_res.returncode != 0:
        result["status"] = "skipped"
        result["reason"] = "detached"
        return result

    # 2. no-upstream 판정
    upstream_res = _run_git(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], repo_path
    )
    if upstream_res.returncode != 0:
        result["status"] = "skipped"
        result["reason"] = "no-upstream"
        result["upstream"] = None
        return result
    result["upstream"] = upstream_res.stdout.strip()

    # 4. dirty 판정
    dirty_res = _run_git(["status", "--porcelain"], repo_path)
    if dirty_res.stdout:
        result["status"] = "skipped"
        result["reason"] = "dirty"
        return result

    # 5. fetch
    fetch_res = _run_git(["fetch", "--all", "--prune"], repo_path)
    if fetch_res.returncode != 0:
        result["status"] = "failed"
        result["reason"] = "fetch-failed"
        return result

    # 6. ahead/behind 계산
    rl_res = _run_git(
        ["rev-list", "--left-right", "--count", "@{u}...HEAD"], repo_path
    )
    if rl_res.returncode != 0:
        result["status"] = "failed"
        result["reason"] = "fetch-failed"
        return result

    parts = rl_res.stdout.split()
    if len(parts) != 2:
        result["status"] = "failed"
        result["reason"] = "fetch-failed"
        return result

    behind, ahead = int(parts[0]), int(parts[1])
    result["behind"] = behind
    result["ahead"] = ahead

    if ahead > 0 and behind > 0:
        result["status"] = "skipped"
        result["reason"] = "diverged"
        return result

    if behind == 0:
        result["status"] = "already-current"
        result["reason"] = None
        result["pulled_commits"] = 0
        return result

    # behind > 0 and ahead == 0 → ff 가능
    prev_head_res = _run_git(["rev-parse", "--short", "HEAD"], repo_path)
    prev_head = prev_head_res.stdout.strip() if prev_head_res.returncode == 0 else None
    result["prev_head"] = prev_head

    pull_res = _run_git(["pull", "--ff-only"], repo_path)
    if pull_res.returncode == 0:
        new_head_res = _run_git(["rev-parse", "--short", "HEAD"], repo_path)
        new_head = new_head_res.stdout.strip() if new_head_res.returncode == 0 else None
        result["status"] = "updated"
        result["reason"] = None
        result["new_head"] = new_head
        result["pulled_commits"] = behind
    else:
        result["status"] = "failed"
        result["reason"] = "fetch-failed"

    return result


# ─────────────────────────────────────────────────────────────────────────────
# sync 서브커맨드
# ─────────────────────────────────────────────────────────────────────────────

def cmd_sync(args):
    path = pathlib.Path(args.path)

    if not path.exists():
        err_response("PATH_NOT_FOUND", path=str(path))
    if not path.is_dir():
        err_response("NOT_A_DIRECTORY", path=str(path))

    path = path.resolve()
    targets = discover_targets(path)

    repositories = []
    for target in targets:
        repositories.append(process_repo(target))

    summary = {
        "total": len(repositories),
        "updated": sum(1 for r in repositories if r["status"] == "updated"),
        "skipped": sum(1 for r in repositories if r["status"] == "skipped"),
        "failed": sum(1 for r in repositories if r["status"] == "failed"),
    }

    ok_response(
        command="sync",
        workspace=str(path),
        repositories=repositories,
        summary=summary,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="git_sync_tool")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("path")
    sync_parser.set_defaults(func=cmd_sync)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
