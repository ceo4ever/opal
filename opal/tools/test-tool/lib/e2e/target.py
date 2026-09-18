"""
@header {
  "module": "target",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T03 대상 소스 해석 — CONTRACT.md §B.1.1의 3종 enum(source-main/source-worktree/installed)만 받아 project_root·worktree_root·opal_home으로 해석하고, 읽기 전용 git 조회로 commit(40자)·dirty·dirty_files를 수집한다(§A.1). source-worktree는 명시된 --worktree-root가 cwd/git 탐색보다 우선하며 그 경로가 곧 project_root다. installed는 --opal-home 입력만 받고 install을 호출하지 않으며, 미준비이거나 사용자 실제 ~/.opal과 같은 경로면 입력 오류로 거부한다(TRD.md TD-9, §C.5).",
  "exports": ["TargetContext", "TargetResolutionError", "TARGET_KINDS", "resolve_target", "project_id_for"]
}

lib.e2e.target — git 호출은 전부 읽기 전용(rev-parse·status --porcelain)이며 저장소를
변경하는 명령을 실행하지 않는다(TRD.md TD-4). OS 분기는 두지 않는다 — lib/e2e의 OS 분기
유일 지점은 lib/e2e/process.py다(D-9, CONTRACT.md §C.2).
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# CONTRACT.md §A.1 `target` enum. 경로가 직접 주어지면 저장소 형태를 보고 앞의 둘 중
# 하나로 해석한다 — 새 enum 값을 만들지 않는다.
TARGET_SOURCE_MAIN = "source-main"
TARGET_SOURCE_WORKTREE = "source-worktree"
TARGET_INSTALLED = "installed"
TARGET_KINDS = (TARGET_SOURCE_MAIN, TARGET_SOURCE_WORKTREE, TARGET_INSTALLED)

# CONTRACT.md §A.0 project_id — 경로 안전 slug(`^[A-Za-z0-9._-]+$`).
_PROJECT_ID_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")

# installed 대상이 "준비됨"으로 인정되는 최소 구성. install을 호출하지 않고 존재만 본다.
_INSTALLED_REQUIRED_ENTRIES = ("tools", "references")

_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


class TargetResolutionError(Exception):
    """대상 소스 해석 단계의 입력 오류. 상태 문자열을 스스로 만들지 않는다.

    detail_code는 test_tool.ERROR_CODES의 키이며, 최종 status·error·exit는 호출자
    (orchestrator)가 e2e_contract 함수로만 산출한다(CONTRACT.md 계약 규칙 C-125-1).
    """

    def __init__(self, detail_code: str, detail: str = ""):
        self.detail_code = detail_code
        self.detail = detail
        super().__init__(f"{detail_code}: {detail}" if detail else detail_code)


@dataclass
class TargetContext:
    target: str
    project_root: str
    worktree_root: Optional[str]
    opal_home: Optional[str]
    commit: str
    dirty: bool
    dirty_files: list = field(default_factory=list)

    def as_run_json_fields(self) -> dict:
        """CONTRACT.md §A.1이 요구하는 대상 소스 증명 필드로 투영한다."""
        return {
            "target": self.target,
            "project_root": self.project_root,
            "worktree_root": self.worktree_root,
            "opal_home": self.opal_home,
            "commit": self.commit,
            "dirty": self.dirty,
            "dirty_files": list(self.dirty_files),
        }


def _git(args: list, cwd: str) -> Optional[str]:
    """읽기 전용 git 조회. 저장소가 아니거나 git이 없으면 None을 반환한다."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _collect_commit(root: str) -> str:
    """`git rev-parse HEAD` 40자. 저장소가 아니거나 커밋이 없으면 빈 문자열."""
    out = _git(["rev-parse", "HEAD"], cwd=root)
    if out is None:
        return ""
    commit = out.strip()
    return commit if _COMMIT_SHA.match(commit) else ""


def _collect_dirty(root: str) -> tuple:
    """`git status --porcelain`으로 미커밋 변경 여부와 경로 목록을 수집한다(PRD R-5)."""
    out = _git(["status", "--porcelain"], cwd=root)
    if out is None:
        return (False, [])
    files = []
    for line in out.splitlines():
        if not line.strip():
            continue
        # porcelain v1: XY<space>path (rename은 `old -> new`)
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        files.append(path.strip('"'))
    return (bool(files), files)


def _git_toplevel(root: str) -> Optional[str]:
    out = _git(["rev-parse", "--show-toplevel"], cwd=root)
    return out.strip() if out else None


def _real_user_opal_home() -> str:
    """사용자 실제 ~/.opal 경로. OPAL_HOME override는 여기에 반영하지 않는다.

    §C.5의 목적은 '사용자 소유 배포 트리를 대상으로 잡지 못하게' 하는 것이므로, 비교
    기준은 프로세스 환경이 아니라 홈 디렉터리 밑의 실제 경로다.
    """
    return os.path.realpath(str(Path.home() / ".opal"))


def project_id_for(project_root: str) -> str:
    """CONTRACT.md §A.0 project_id — 저장소 basename 기반 경로 안전 slug."""
    base = os.path.basename(os.path.normpath(project_root)) or "project"
    slug = _PROJECT_ID_UNSAFE.sub("-", base).strip("-")
    return slug or "project"


def resolve_target(
    target: str,
    *,
    worktree_root: Optional[str] = None,
    opal_home: Optional[str] = None,
) -> TargetContext:
    """`--target`(CONTRACT.md §B.1.1의 3종 enum)을 TargetContext로 해석한다.

    해석 우선순위는 **명시된 인자 > cwd/git 탐색**이다. source-worktree에서 호출자가
    `--worktree-root`를 줬다면 그 경로가 곧 대상 트리이며 project_root도 같다 — 동시에
    도는 여러 worktree run이 각자 자기 트리를 가리켜야 하기 때문이다(AC-1·AC-2).
    `--worktree-root` 미지정일 때만 `git rev-parse --show-toplevel`로 해석한다(§B.1.1).

    경로 문자열은 받지 않는다 — enum 밖 입력은 입력 오류다.
    """
    if target == TARGET_INSTALLED:
        return _resolve_installed(opal_home=opal_home)
    if target == TARGET_SOURCE_MAIN:
        return _resolve_source(_cwd_toplevel(), kind=TARGET_SOURCE_MAIN, worktree_root=None)
    if target == TARGET_SOURCE_WORKTREE:
        resolved = os.path.abspath(worktree_root) if worktree_root else _cwd_toplevel()
        return _resolve_source(resolved, kind=TARGET_SOURCE_WORKTREE, worktree_root=resolved)
    raise TargetResolutionError(
        "e2e_target_invalid",
        f"--target must be one of {list(TARGET_KINDS)}",
    )


def _cwd_toplevel() -> str:
    """명시 인자가 없을 때의 폴백 — 현재 작업 디렉터리의 저장소 루트, 없으면 cwd."""
    cwd = os.getcwd()
    return _git_toplevel(cwd) or os.path.abspath(cwd)


def _resolve_source(root: str, *, kind: str, worktree_root: Optional[str]) -> TargetContext:
    commit = _collect_commit(root)
    dirty, dirty_files = _collect_dirty(root)
    return TargetContext(
        target=kind,
        project_root=root,
        worktree_root=worktree_root,
        opal_home=None,
        commit=commit,
        dirty=dirty,
        dirty_files=dirty_files,
    )


def _resolve_installed(*, opal_home: Optional[str]) -> TargetContext:
    """installed 대상 — install을 호출하지 않는다(TRD.md TD-9).

    미준비 트리와 사용자 실제 ~/.opal은 입력 오류로 거부한다(CONTRACT.md §C.5).
    """
    if not opal_home:
        raise TargetResolutionError(
            "e2e_opal_home_required",
            "--opal-home is required when --target=installed",
        )
    resolved = os.path.realpath(os.path.abspath(opal_home))
    if resolved == _real_user_opal_home():
        raise TargetResolutionError(
            "e2e_opal_home_is_user_owned",
            "--opal-home must not point at the user's own ~/.opal",
        )
    if not os.path.isdir(resolved):
        raise TargetResolutionError(
            "e2e_opal_home_unprepared",
            "--opal-home does not exist; this harness never runs install itself",
        )
    missing = [name for name in _INSTALLED_REQUIRED_ENTRIES if not (Path(resolved) / name).exists()]
    if missing:
        raise TargetResolutionError(
            "e2e_opal_home_unprepared",
            f"--opal-home is missing {missing}; prepare it before running (install is not invoked)",
        )

    root = _cwd_toplevel()
    commit = _collect_commit(root)
    dirty, dirty_files = _collect_dirty(root)
    return TargetContext(
        target=TARGET_INSTALLED,
        project_root=root,
        worktree_root=None,
        opal_home=resolved,
        commit=commit,
        dirty=dirty,
        dirty_files=dirty_files,
    )
