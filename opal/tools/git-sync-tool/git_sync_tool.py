"""
@header {
  "module": "git_sync_tool",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "워크스페이스 아래 여러 독립 git 저장소를 순회하며 안전하게 일괄 최신화(clean+ff-only pull)하는 CLI. 대상 결정(단일 git 루트 또는 직속 자식 1단계, 재귀 금지) → 선언 대조(선언 파일이 있을 때만) → 저장소별 판정(detached→no-upstream→dirty→fetch→diverged/ff) → JSON 결과 출력. git 2.22+ 필요 (rev-list --left-right --count). detached HEAD에서는 @{u} 조회 자체가 fatal로 실패해 no-upstream과 구분되지 않으므로 detached 판정을 no-upstream보다 먼저 수행한다. dirty/diverged/detached/no-upstream 저장소에는 stash/rebase/force/commit/push 등 자율 조치를 일절 수행하지 않는다(skip 후 보고만) — 헌법 user sovereignty 원칙. `--root <경로>`는 순회 대상 밖에 있는 상위 root 저장소(예: `<프로젝트>/workspace`를 순회할 때의 `<프로젝트>` 자체)를 대상 선두에 추가한다 — 미전달 시 동작은 현행과 동일하고, `.git` 없는 root는 조용히 제외하며(상위 저장소 오조작 방지) 이미 발견된 대상과 중복되면 계상하지 않는다. 선언 파일(`<순회경로>/.opal/workspace.json` — 없으면 `<순회경로>/../.opal/workspace.json`)이 있으면 선언×디스크 6상태를 대조해 mismatch/unknown/not-cloned/undeclared를 보고하고 pull을 보류한다 — 선언 파일이 없으면 대조 자체를 수행하지 않아 응답 키 집합이 도입 전과 동일하다. 정체성 비교 키는 org/repo이며 host·프로토콜·대소문자·후행 .git은 판정에서 배제한다. 로컬 파일시스템 경로는 환원 대상이 아니며 unknown으로 보류한다. 도구 응답에 원격 URL 원문을 싣지 않는다.",
  "exports": ["cmd_sync", "cmd_init", "cmd_clone", "process_repo", "discover_targets", "resolve_root_target", "resolve_project_root", "normalize_repo_coord", "compare_repo_coord", "load_workspace_config", "validate_workspace_config"],
  "depends": ["git CLI 2.22+"]
}
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys
import subprocess

# ─────────────────────────────────────────────────────────────────────────────
# 에러 코드 카탈로그 (state_tool.py:66-100 패턴)
# ─────────────────────────────────────────────────────────────────────────────
ERROR_CODES = {
    "PATH_NOT_FOUND": "지정한 경로가 존재하지 않습니다: {path}",
    "NOT_A_DIRECTORY": "지정한 경로가 디렉토리가 아닙니다: {path}",
    "WORKSPACE_CONFIG_INVALID": "workspace 선언 파일이 스키마를 위반했습니다: {path}",
    "WORKSPACE_CONFIG_MALFORMED": "workspace 선언 파일이 유효한 JSON이 아닙니다: {path}",
    "CONFIG_EXISTS": "workspace 선언 파일이 이미 존재합니다(--force 필요): {path}",
    "DIR_EXISTS": "대상 디렉토리가 이미 존재합니다: {path}",
    "INVALID_DIR": "디렉토리 이름이 basename이 아닙니다: {path}",
    "CLONE_FAILED": "clone에 실패했습니다: {path}",
    "NOT_A_WORKSPACE_CONTAINER": "경로가 저장소 자체입니다 — 자식 저장소를 담은 컨테이너 경로를 주십시오: {path}",
}


def ok_response(**kwargs):
    payload = {"ok": True, "error": None, **kwargs}
    print(json.dumps(payload, ensure_ascii=False, default=str))


def err_response(code, path=None, exit_code=1, details=None):
    message = ERROR_CODES.get(code, code)
    try:
        message = message.format(path=path)
    except (KeyError, IndexError):
        pass
    payload = {"ok": False, "error": code, "message": message}
    if details:
        payload["details"] = list(details)
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
# org/repo 정규화와 3진 대조 — 정체성 축 (C-2, C-4)
#
# 접속 방식(host·SSH 별칭·프로토콜·후행 .git·대소문자)은 사용자마다 다르므로 판정에서
# 배제하고 host를 뺀 경로 전체(`org/repo`, 계층이 깊으면 `org/subgroup/repo`)를 정체성
# 키로 쓴다. 환원 대상은 원격 좌표 3형식뿐이다 — 로컬 파일시스템 경로를 org/repo로
# 읽으면 서로 무관한 경로가 같은 키로 충돌해 미탐(다른 레포를 같다고 판정)을 새로 만든다.
# ─────────────────────────────────────────────────────────────────────────────

_SCHEME_RE = re.compile(r"^(?P<scheme>[a-zA-Z][a-zA-Z0-9+.-]*)://(?P<rest>.*)$")
_SCP_RE = re.compile(r"^(?:[^/@:]+@)?(?P<host>[^/@:]+):(?P<path>[^/].*)$")
_REMOTE_SCHEMES = {"ssh", "git", "http", "https"}


def _coord_from_path(path: str):
    """
    URL 경로 부분에서 좌표를 뽑는다. 뽑을 수 없으면 None.

    **경로 전체를 쓴다 — 마지막 2세그먼트만 취하지 않는다.** GitLab subgroup처럼
    `orgA/team/repo`·`orgB/team/repo`가 되는 계층에서 뒤 2개만 보면 상위 조직이
    소실돼 서로 다른 조직의 저장소가 같은 좌표로 충돌한다(H-1 미탐). 잘라내면
    조용히 엉뚱한 저장소를 pull하고, 안 자르면 시끄러운 mismatch가 날 뿐이다.
    """
    path = path.strip().strip("/")
    if path.endswith(".git"):
        path = path[: -len(".git")]
    segments = [seg for seg in path.split("/") if seg]
    if len(segments) < 2:
        return None
    if any(seg in (".", "..") for seg in segments):
        return None
    return "/".join(segments)


def normalize_repo_coord(url):
    """
    원격 URL을 `org/repo` 좌표로 환원한다. 환원 불가면 None.

    좌표는 host를 뺀 **경로 전체**다. 계층이 깊으면 `org/subgroup/repo`처럼 그대로
    유지한다 — 상위 조직을 버리면 서로 다른 레포가 같은 키가 된다(H-1).

    환원 대상은 3형식뿐이다.
      - `git@host:org/repo`(scp 축약, SSH 별칭 포함)
      - `ssh://[user@]host/org/repo` · `git://host/org/repo`
      - `https://host/org/repo[.git]` · `http://...`

    로컬 절대·상대 경로와 `file://`은 원격 좌표가 아니므로 환원하지 않는다.
    """
    if not isinstance(url, str):
        return None
    url = url.strip()
    if not url:
        return None

    scheme_match = _SCHEME_RE.match(url)
    if scheme_match:
        scheme = scheme_match.group("scheme").lower()
        if scheme not in _REMOTE_SCHEMES:
            return None  # file:// 등 — 원격 좌표가 아니다
        rest = scheme_match.group("rest")
        if "/" not in rest:
            return None
        _, _, path = rest.partition("/")
        return _coord_from_path(path)

    scp_match = _SCP_RE.match(url)
    if scp_match:
        return _coord_from_path(scp_match.group("path"))

    return None


def compare_repo_coord(declared, actual):
    """
    선언 좌표와 실제 좌표를 3진으로 대조한다 — `match` / `mismatch` / `unknown`.
    한쪽이라도 환원 불가면 `unknown`이며 `unknown`은 pull하지 않는다(fail-closed).
    대소문자는 비교에서 무시한다 — GitHub·GitLab이 org/repo를 대소문자 구분 없이 같은
    레포로 해석하므로 구분하면 오탐(막지 말아야 할 것을 막음)이 된다.
    """
    if not declared or not actual:
        return "unknown"
    return "match" if declared.casefold() == actual.casefold() else "mismatch"


def get_origin_coord(repo_path: pathlib.Path):
    """
    저장소의 origin URL을 org/repo 좌표로 환원한다. 원격 부재·환원 불가면 None.

    `git remote get-url`이 아니라 `git config --get`으로 **설정 원문**을 읽는다.
    전자는 `url.<base>.insteadOf` 재작성을 적용해 로컬 접속 경로를 돌려주는데,
    그 재작성은 사용자별 접속 방식이지 레포 정체성이 아니다 — 판정에 새면 같은
    레포가 사용자마다 다른 좌표로 읽힌다 (C-2).
    """
    res = _run_git(["config", "--get", "remote.origin.url"], repo_path)
    if res.returncode != 0:
        return None
    return normalize_repo_coord(res.stdout.strip())


# ─────────────────────────────────────────────────────────────────────────────
# workspace.json 선언 — 로더와 검증 (C-1, C-6, AC-10)
# ─────────────────────────────────────────────────────────────────────────────

WORKSPACE_CONFIG_RELPATH = pathlib.Path(".opal") / "workspace.json"
VALID_REPO_STATES = {"active", "deferred"}
_REPO_REQUIRED_KEYS = {"dir", "repo", "state"}
# 판정에 쓰지 않는 사람용·부가 필드. 알려진 키만 허용해 오타(`stat` 등)를 계속 잡는다.
_REPO_OPTIONAL_KEYS = {"note", "_help", "clone_branch"}
_CONFIG_REQUIRED_KEYS = {"schema_version", "host", "org", "repos"}
_CONFIG_OPTIONAL_KEYS = {"_help"}
# 선언 파일은 사람이 손으로 쓰므로 "1"·"1.0"·1이 섞인다. 판정에 영향이 없는 표기 차이로
# 전체를 거부하지 않는다 — 거부는 판정을 바꾸는 위반(state·dir·중복)에만 쓴다.
_ACCEPTED_SCHEMA_VERSIONS = {1, "1", "1.0"}


def resolve_project_root(path: pathlib.Path) -> pathlib.Path:
    """
    선언 파일이 속한 프로젝트 루트를 판정한다.

    `path/.opal`이 디렉토리면 **path 자체가 프로젝트 루트**다 — 사람이 워크스페이스
    컨테이너가 아니라 프로젝트 경로를 직접 준 경우다. 아니면 path를 컨테이너로 보고
    부모를 프로젝트 루트로 쓴다(`<프로젝트>/workspace`를 순회하는 기본 형태).

    부모 고정 규칙만 두면 프로젝트 경로를 직접 준 순간 선언 파일이 **레포 밖 한 단계
    위**로 잡힌다. 실제로 `init .`이 그렇게 어긋났다.
    """
    if (path / ".opal").is_dir():
        return path
    return path.parent


def workspace_config_path(project_root: pathlib.Path) -> pathlib.Path:
    """선언 파일 경로. `resolve_project_root`가 판정한 프로젝트 루트 기준이다."""
    return project_root / WORKSPACE_CONFIG_RELPATH


def declared_coord(config: dict, entry: dict):
    """
    선언 항목의 `repo`를 좌표로 해석한다.

    **`repo`는 항상 최상위 `org` 아래의 경로다.** 짧은 이름이면 `org/repo`가 되고,
    subgroup처럼 `/`를 포함하면 `org/team/repo`가 된다. `/` 포함을 "전체 좌표"로
    달리 해석하지 않는다 — 같은 문자열이 선언 위치에 따라 다른 조직을 가리키면
    사람이 읽는 의미와 도구 판정이 갈린다. 다른 조직을 쓰려고 `repo`에 org를 적으면
    좌표가 어긋나 `mismatch`로 드러난다(조용한 오탐이 아니라 시끄러운 거부).
    """
    repo = entry.get("repo")
    if not isinstance(repo, str) or not repo.strip():
        return None
    org = config.get("org")
    if not isinstance(org, str) or not org.strip():
        return None
    return _coord_from_path(f"{org.strip()}/{repo.strip()}")


def validate_workspace_config(config) -> list:
    """
    hand-rolled 스키마 검증 (worktree_tool.validate_worktree_config 선례).
    위반 사유 목록을 반환하며 빈 목록이면 통과다.
    """
    errors = []
    if not isinstance(config, dict):
        return ["최상위가 객체가 아닙니다"]

    missing = _CONFIG_REQUIRED_KEYS - config.keys()
    if missing:
        errors.append(f"필수 키 누락: {sorted(missing)}")
    extra = config.keys() - _CONFIG_REQUIRED_KEYS - _CONFIG_OPTIONAL_KEYS
    if extra:
        errors.append(f"허용되지 않은 키: {sorted(extra)}")

    if config.get("schema_version") not in _ACCEPTED_SCHEMA_VERSIONS:
        errors.append(
            f"schema_version이 지원 범위({sorted(_ACCEPTED_SCHEMA_VERSIONS, key=str)}) 밖입니다: "
            f"{config.get('schema_version')!r}"
        )
    for key in ("host", "org"):
        value = config.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key}가 비어 있거나 문자열이 아닙니다: {value!r}")

    repos = config.get("repos")
    if not isinstance(repos, list):
        errors.append(f"repos가 배열이 아닙니다: {type(repos).__name__}")
        return errors

    seen_dirs, seen_coords = set(), set()
    for index, entry in enumerate(repos):
        label = f"repos[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label}가 객체가 아닙니다")
            continue

        entry_missing = _REPO_REQUIRED_KEYS - entry.keys()
        if entry_missing:
            errors.append(f"{label} 필수 키 누락: {sorted(entry_missing)}")
        entry_extra = entry.keys() - _REPO_REQUIRED_KEYS - _REPO_OPTIONAL_KEYS
        if entry_extra:
            errors.append(f"{label} 허용되지 않은 키: {sorted(entry_extra)}")

        dir_name = entry.get("dir")
        if not isinstance(dir_name, str) or not dir_name.strip():
            errors.append(f"{label}.dir가 비어 있거나 문자열이 아닙니다: {dir_name!r}")
        elif (
            "/" in dir_name
            or "\\" in dir_name
            or dir_name in (".", "..")
            or dir_name != dir_name.strip()
        ):
            errors.append(f"{label}.dir가 basename이 아닙니다: {dir_name!r}")
        elif dir_name in seen_dirs:
            errors.append(f"{label}.dir가 중복입니다: {dir_name!r}")
        else:
            seen_dirs.add(dir_name)

        state = entry.get("state")
        if state not in VALID_REPO_STATES:
            errors.append(f"{label}.state가 허용값({sorted(VALID_REPO_STATES)}) 밖입니다: {state!r}")

        coord = declared_coord(config, entry)
        if coord is None:
            errors.append(f"{label}.repo를 org/repo 좌표로 해석할 수 없습니다: {entry.get('repo')!r}")
        elif coord.casefold() in seen_coords:
            errors.append(f"{label}.repo가 중복입니다: {coord!r}")
        else:
            seen_coords.add(coord.casefold())

    return errors


def load_workspace_config(project_root: pathlib.Path):
    """
    선언 파일을 읽어 반환한다. **파일 부재는 오류가 아니라 None이다** — 선언이 없는
    프로젝트는 대조 분기 자체를 타지 않고 도입 전 동작을 그대로 유지한다(C-1).
    JSON 파싱 실패는 WORKSPACE_CONFIG_MALFORMED, 스키마 위반은 WORKSPACE_CONFIG_INVALID로
    순회 시작 전에 거부한다.
    """
    config_path = workspace_config_path(project_root)
    if not config_path.exists():
        return None

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        err_response("WORKSPACE_CONFIG_MALFORMED", path=str(config_path), details=[str(exc)])

    errors = validate_workspace_config(config)
    if errors:
        err_response("WORKSPACE_CONFIG_INVALID", path=str(config_path), details=errors)

    return config


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


def resolve_root_target(root_arg: str):
    """
    --root 인자를 순회 대상에 추가할 root 저장소 경로로 해석한다.
    경로 부재/비디렉토리는 에러로 거부하고, `.git`이 없으면 None을 반환해 제외한다
    (`.git` 없는 경로에서 git을 실행하면 상위 저장소로 올라가 엉뚱한 저장소를 조작한다).
    """
    root_path = pathlib.Path(root_arg)
    if not root_path.exists():
        err_response("PATH_NOT_FOUND", path=str(root_path))
    if not root_path.is_dir():
        err_response("NOT_A_DIRECTORY", path=str(root_path))

    root_path = root_path.resolve()
    if not (root_path / ".git").exists():
        return None
    return root_path


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

def _blocked_entry(name: str, reason: str, declaration: str, repo_coord=None) -> dict:
    """선언 대조에서 pull 전에 확정된 항목 — 순회 판정에 진입시키지 않는다."""
    return {
        "name": name,
        "branch": None,
        "upstream": None,
        "status": "skipped",
        "reason": reason,
        "ahead": None,
        "behind": None,
        "prev_head": None,
        "new_head": None,
        "pulled_commits": 0,
        "repo": repo_coord,
        "declaration": declaration,
    }


def process_declared_repo(repo_path: pathlib.Path, entry, config: dict) -> dict:
    """
    선언×디스크 대조 후 저장소를 처리한다. 판정은 pull보다 먼저 확정되며,
    `mismatch`·`unknown`은 fetch/pull 경로에 진입하지 않는다(C-4 fail-closed).

    | 선언 | 디스크 | 결과 |
    |---|---|---|
    | active | 있음·좌표 일치 | 정상 순회(sync) |
    | active | 있음·좌표 불일치 | `mismatch` — pull 보류 |
    | active/deferred | 있음·환원 불가 | `unknown` — pull 보류 |
    | deferred | 있음 | 정상 순회 + `deferred-present` 선언 어긋남 보고 |
    | 미선언 | 있음 | `undeclared` — 선언 드리프트 보고, pull 보류 |

    `reason`과 `declaration`은 축이 다르다. `reason`은 **status의 사유**이고
    `declaration`은 **선언 대조 결과**다. 선언이 곧 status의 사유인 판정
    (`mismatch`·`unknown`·`not-cloned`·`deferred`·`undeclared`)만 양쪽에 함께 실린다.
    `deferred-present`는 저장소가 정상 순회되므로 status의 사유가 따로 있고,
    `declaration`에만 실린다 — **소비자는 `reason`과 별개로 `declaration`을 읽어야 한다.**
    """
    name = repo_path.name
    actual = get_origin_coord(repo_path)

    if entry is None:
        return _blocked_entry(name, "undeclared", "undeclared", actual)

    verdict = compare_repo_coord(declared_coord(config, entry), actual)
    if verdict in ("mismatch", "unknown"):
        return _blocked_entry(name, verdict, verdict, actual)

    result = process_repo(repo_path)
    result["repo"] = actual
    result["declaration"] = (
        "deferred-present" if entry.get("state") == "deferred" else "match"
    )
    return result


def cmd_sync(args):
    path = pathlib.Path(args.path)

    if not path.exists():
        err_response("PATH_NOT_FOUND", path=str(path))
    if not path.is_dir():
        err_response("NOT_A_DIRECTORY", path=str(path))

    path = path.resolve()

    # 선언 파일은 순회 시작 전에 읽는다 — 스키마 위반이면 한 저장소도 건드리지 않는다.
    project_root = resolve_project_root(path)
    config = load_workspace_config(project_root)

    root = resolve_root_target(args.root) if args.root else None

    targets = discover_targets(path)
    if root is not None and root not in targets:
        targets = [root, *targets]

    repositories = []

    if config is None:
        # 선언 부재 — 도입 전 경로를 그대로 탄다. 응답 키 집합이 동일하다 (C-1).
        for target in targets:
            repositories.append(process_repo(target))
    else:
        declared = {entry["dir"]: entry for entry in config["repos"]}
        for target in targets:
            # `--root`로 추가된 순회 대상 밖 저장소는 워크스페이스 멤버십 선언의
            # 대상이 아니므로 대조하지 않는다.
            if root is not None and target == root:
                result = process_repo(target)
                result["repo"] = get_origin_coord(target)
                result["declaration"] = None
                repositories.append(result)
                continue
            repositories.append(
                process_declared_repo(target, declared.get(target.name), config)
            )

        # 선언됐는데 디스크에 없는 레포 — 조용히 사라지지 않도록 전부 보고한다.
        # `active`는 조치가 필요한 누락(`not-cloned`)이고 `deferred`는 의도된 상태
        # (`deferred`)다. **의도된 상태도 출력에는 남긴다** — 경고를 내지 않는 것과
        # 보고에서 지우는 것은 다르다. 지우면 "선언은 했는데 아무도 안 본다"가 되어
        # 드리프트 탐지가 절반만 작동한다.
        present = {target.name for target in targets}
        for entry in config["repos"]:
            if entry["dir"] in present:
                continue
            reason = "not-cloned" if entry.get("state") == "active" else "deferred"
            repositories.append(
                _blocked_entry(
                    entry["dir"], reason, reason, declared_coord(config, entry)
                )
            )

    summary = {
        "total": len(repositories),
        "updated": sum(1 for r in repositories if r["status"] == "updated"),
        "skipped": sum(1 for r in repositories if r["status"] == "skipped"),
        "failed": sum(1 for r in repositories if r["status"] == "failed"),
    }

    payload = {
        "command": "sync",
        "workspace": str(path),
        "root": str(root) if root is not None else None,
        "repositories": repositories,
        "summary": summary,
    }
    if config is not None:
        payload["workspace_config"] = str(workspace_config_path(project_root))

    ok_response(**payload)


# ─────────────────────────────────────────────────────────────────────────────
# init 서브커맨드 — 탐지 기반 선언 초안 (AC-6, C-6)
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_HOST = "github.com"


def cmd_init(args):
    path = pathlib.Path(args.path)

    if not path.exists():
        err_response("PATH_NOT_FOUND", path=str(path))
    if not path.is_dir():
        err_response("NOT_A_DIRECTORY", path=str(path))

    path = path.resolve()

    if (path / ".git").exists():
        # 단일 저장소를 훑으면 그 저장소 자신이 유일한 "자식"이 되어 의미 없는 초안이
        # 나온다. 컨테이너 경로를 추측해 내려가지 않고 사람에게 돌려준다.
        err_response("NOT_A_WORKSPACE_CONTAINER", path=str(path))

    config_path = workspace_config_path(resolve_project_root(path))

    # --dry-run은 아무것도 쓰지 않으므로 기존 파일과 충돌하지 않는다. 오히려 선언이
    # 이미 있을 때 현재 디스크와 어떻게 다른지 보려면 이 경로가 열려 있어야 한다.
    if config_path.exists() and not args.force and not args.dry_run:
        err_response("CONFIG_EXISTS", path=str(config_path))

    found, unresolved = [], []
    orgs = []
    for target in discover_targets(path):
        coord = get_origin_coord(target)
        if coord is None:
            # 추측하지 않는다 — 환원 불가한 자식은 초안에서 빼고 사람에게 넘긴다.
            unresolved.append(target.name)
            continue
        top, _, rest = coord.partition("/")
        orgs.append(top)
        found.append({"dir": target.name, "coord": coord, "org": top, "repo": rest})

    org = collections.Counter(orgs).most_common(1)[0][0] if orgs else ""

    # 선언의 `repo`는 항상 최상위 `org` 아래 경로다. 다수 org와 다른 자식은 이 선언
    # 형식으로 표현할 수 없으므로 초안에 넣지 않고 따로 보고한다 — 억지로 넣으면
    # `org/다른org/repo`가 되어 사람이 읽는 의미와 판정이 어긋난다.
    in_org = [item for item in found if item["org"] == org]
    other_org = [
        {"dir": item["dir"], "repo": item["coord"]}
        for item in found
        if item["org"] != org
    ]

    draft = {
        "schema_version": 1,
        "host": DEFAULT_HOST,
        "org": org,
        # state는 전건 active다 — deferred는 사람의 결정이므로 추측하지 않는다 (C-6).
        "repos": [
            {"dir": item["dir"], "repo": item["repo"], "state": "active"}
            for item in in_org
        ],
    }

    if args.dry_run:
        ok_response(
            command="init",
            workspace=str(path),
            config_path=str(config_path),
            written=False,
            unresolved=unresolved,
            other_org=other_org,
            draft=draft,
        )
        return

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    ok_response(
        command="init",
        workspace=str(path),
        config_path=str(config_path),
        written=True,
        unresolved=unresolved,
        other_org=other_org,
        repos=len(draft["repos"]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# clone 서브커맨드 — 승인 게이트 통과 후에만 호출된다 (AC-8, C-3, C-5)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_clone(args):
    path = pathlib.Path(args.path)

    if not path.exists():
        err_response("PATH_NOT_FOUND", path=str(path))
    if not path.is_dir():
        err_response("NOT_A_DIRECTORY", path=str(path))

    path = path.resolve()

    dir_name = args.dir
    if "/" in dir_name or "\\" in dir_name or dir_name in (".", ".."):
        err_response("INVALID_DIR", path=dir_name)

    dest = path / dir_name
    if dest.exists():
        # 파괴적 덮어쓰기를 만들지 않는다 — 점유된 디렉토리는 사람이 정리한다.
        err_response("DIR_EXISTS", path=str(dest))

    # 인자 리스트 방식(shell=False) — 스킬이 raw git을 셸로 부르지 않게 하려고 도구가 집행한다.
    result = subprocess.run(
        ["git", "clone", args.url, str(dest)],
        cwd=str(path),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # stderr에 원격 URL 원문이 섞이므로 응답에 싣지 않는다 (C-3).
        err_response("CLONE_FAILED", path=str(dest))

    coord = get_origin_coord(dest)
    ok_response(
        command="clone",
        workspace=str(path),
        dir=dir_name,
        repo=coord,
        created=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="git_sync_tool")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("path")
    sync_parser.add_argument(
        "--root",
        default=None,
        help="순회 대상 밖의 상위 root 저장소 경로. 대상 선두에 추가한다 (.git 없으면 제외)",
    )
    sync_parser.set_defaults(func=cmd_sync)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("path")
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="기존 선언 파일을 덮어쓴다. 없으면 CONFIG_EXISTS로 거부한다",
    )
    init_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="파일을 쓰지 않고 draft 키로 초안만 반환한다",
    )
    init_parser.set_defaults(func=cmd_init)

    clone_parser = subparsers.add_parser("clone")
    clone_parser.add_argument("path")
    clone_parser.add_argument("--dir", required=True, help="생성할 자식 디렉토리 basename")
    clone_parser.add_argument("--url", required=True, help="clone 원본 URL (응답에 싣지 않는다)")
    clone_parser.set_defaults(func=cmd_clone)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
