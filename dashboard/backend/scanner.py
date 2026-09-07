"""
@header {
  "module": "scanner",
  "layer": "service",
  "domain": "console",
  "description": "scan_roots 하위를 os.walk + maxdepth 가드로 탐색. .opal/AGENT.md 마커로 OPAL 프로젝트 발견. exclude 목록 진입 금지(H-4). 태스크 열거는 iter_task_dirs 단일 함수가 담당 — tasks/ + tasks/backup/ 2단 고정 깊이, 이름 정렬로 결정론적. resolve_task_dir는 realpath 접두 검사로 tasks/ 트리 이탈을 차단하고, 경로로 쓸 수 없는 입력(널 바이트)은 realpath 앞단에서 거른다. 읽기 전용 — mtime 불변",
  "exports": ["scan_projects", "ProjectInfo", "iter_task_dirs", "resolve_task_dir"],
  "depends": ["config"]
}
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass

#: `tasks/` 아래 아카이브 태스크를 담는 디렉토리 이름. 이 폴더 자체는 태스크가 아니다.
BACKUP_DIR_NAME = "backup"


@dataclass
class ProjectInfo:
    """단일 프로젝트 발견 결과"""
    name: str
    path: str
    is_opal: bool
    task_count: int
    last_updated: str | None


def _sorted_subdirs(directory: str) -> list[os.DirEntry[str]]:
    """directory 1-depth 하위 디렉토리를 이름 오름차순으로 반환.

    os.scandir의 반환 순서는 파일시스템 의존이라 호출마다 흔들릴 수 있다.
    이름으로 정렬해 같은 입력에 같은 순서를 보장한다 — 하류 집계 출력이
    바이트 단위로 재현되어야 하기 때문이다.
    존재하지 않는 경로·접근 불가 경로는 예외 없이 빈 목록이 된다.
    """
    try:
        entries = [
            entry for entry in os.scandir(directory)
            if entry.is_dir(follow_symlinks=False)
        ]
    except OSError:
        return []
    entries.sort(key=lambda entry: entry.name)
    return entries


def iter_task_dirs(tasks_dir: str) -> Iterator[tuple[os.DirEntry[str], bool]]:
    """tasks/ 태스크 디렉토리를 2단 고정 깊이로 열거하는 단일 진입점.

    Args:
        tasks_dir: 프로젝트의 `tasks` 디렉토리 절대경로

    Yields:
        (DirEntry, is_archived) 튜플. is_archived는 `tasks/backup/` 소재 여부.

    열거 규칙:
        - 1단: `tasks/` 1-depth 하위 디렉토리 (is_archived=False)
        - 2단: `tasks/backup/` 1-depth 하위 디렉토리 (is_archived=True)
        - `backup` 폴더 자체는 태스크로 세지 않고, 그 하위를 센다
        - 깊이는 2단으로 고정 — os.walk로 무한 하강하지 않는다
        - 이름 오름차순 정렬 → 같은 입력에 결정론적 순서
        - `tasks/`나 `tasks/backup/`이 없어도 예외 없이 빈 결과
    """
    for entry in _sorted_subdirs(tasks_dir):
        if entry.name == BACKUP_DIR_NAME:
            continue
        yield entry, False

    for entry in _sorted_subdirs(os.path.join(tasks_dir, BACKUP_DIR_NAME)):
        yield entry, True


def resolve_task_dir(project_path: str, task_id: str) -> str | None:
    """task_id를 실제 태스크 디렉토리 경로로 해석한다.

    Args:
        project_path: 프로젝트 루트 절대경로
        task_id: 태스크 디렉토리 이름 (단일 경로 세그먼트)

    Returns:
        해석된 디렉토리의 realpath. `tasks/` 직속 → `tasks/backup/` 순으로
        찾고, 없거나 경로 이탈 입력이면 None.

    보안:
        해석 결과가 `tasks/` 트리 **내부**임을 realpath 접두 검사로 확인한다.
        문자열 조립만으로는 `..` 세그먼트가 조립 단계에서 흡수되어
        트리 밖 디렉토리가 200으로 응답된다. 트리 내부 확인이 경계이며,
        단일 세그먼트 요구는 그 앞단의 정규화 조건이다.
    """
    if not task_id or task_id in (os.curdir, os.pardir):
        return None
    # 단일 세그먼트만 허용 — 구분자가 섞이면 정규화 전에 거른다
    if task_id != os.path.basename(task_id.rstrip("/\\")):
        return None
    if os.path.isabs(task_id) or "/" in task_id or "\\" in task_id:
        return None
    # 널 바이트는 경로로 쓸 수 없는 입력 — realpath가 ValueError를 던지므로 그 앞에서 거른다.
    # 보안 판정은 여전히 아래 realpath 트리 내부 확인이 담당한다.
    if "\x00" in task_id:
        return None

    tasks_root = os.path.join(project_path, "tasks")
    tasks_root_real = os.path.realpath(tasks_root)

    candidates = []
    if task_id != BACKUP_DIR_NAME:
        candidates.append(os.path.join(tasks_root, task_id))
    candidates.append(os.path.join(tasks_root, BACKUP_DIR_NAME, task_id))

    for candidate in candidates:
        resolved = os.path.realpath(candidate)
        # 경계: 해석 결과가 tasks/ 트리 안에 있어야 한다 (트리 루트 자체는 태스크가 아님)
        if not resolved.startswith(tasks_root_real + os.sep):
            continue
        if os.path.isdir(resolved):
            return resolved

    return None


def _count_tasks(project_path: str) -> int:
    """태스크 개수 반환 (OPAL 프로젝트 전용).

    열거는 iter_task_dirs에 위임한다 — 같은 일을 하는 열거 코드가 둘이면
    오늘은 답이 같아도 내일 갈라진다.
    """
    return sum(1 for _ in iter_task_dirs(os.path.join(project_path, "tasks")))


def scan_projects(
    roots: list[str],
    depth: int,
    exclude: list[str],
) -> list[ProjectInfo]:
    """roots 하위를 os.walk + maxdepth 가드로 탐색.

    Args:
        roots: 탐색 시작 경로 목록
        depth: 최대 탐색 깊이 (루트 기준. depth=2 → root/L1/L2 까지)
        exclude: 진입 금지 디렉토리 이름 목록 (예: node_modules)

    Returns:
        발견된 ProjectInfo 목록. OPAL 마커 여부 포함.

    참고:
        - .opal/AGENT.md 존재 시 OPAL 프로젝트로 등록 후 해당 경로 하위 재귀 탐색 중단(prune)
        - 비OPAL 디렉토리도 depth 내에서 발견된 1-depth 폴더는 is_opal=false로 포함
        - 읽기 전용 — 대상 파일 mtime 불변(H-6)
    """
    exclude_set = set(exclude)
    results: list[ProjectInfo] = []

    for root in roots:
        if not os.path.isdir(root):
            continue
        _walk_dir(root, root, 0, depth, exclude_set, results)

    return results


def _walk_dir(
    base_root: str,
    current_dir: str,
    current_depth: int,
    max_depth: int,
    exclude_set: set[str],
    results: list[ProjectInfo],
) -> None:
    """재귀 탐색 헬퍼.

    current_depth는 base_root 기준 깊이.
    depth=2 → base_root/L1(depth=1)/L2(depth=2) 까지 탐색.
    .opal/AGENT.md 발견 시 results에 추가 후 하위 탐색 중단(prune).
    """
    if current_depth > max_depth:
        return

    try:
        entries = list(os.scandir(current_dir))
    except (PermissionError, OSError):
        return

    # 현재 디렉토리가 OPAL 프로젝트인지 확인 (depth>0 일 때만 — root 자체는 제외)
    if current_depth > 0:
        agent_md = os.path.join(current_dir, ".opal", "AGENT.md")
        if os.path.isfile(agent_md):
            # OPAL 프로젝트 발견 — 하위 탐색 중단(prune)
            results.append(
                ProjectInfo(
                    name=os.path.basename(current_dir),
                    path=current_dir,
                    is_opal=True,
                    task_count=_count_tasks(current_dir),
                    last_updated=None,  # F-004 데몬에서 state.json mtime으로 채움
                )
            )
            return

        # 비OPAL 디렉토리도 depth=1 레벨에서만 포함 (최상위 하위 폴더)
        if current_depth == 1:
            results.append(
                ProjectInfo(
                    name=os.path.basename(current_dir),
                    path=current_dir,
                    is_opal=False,
                    task_count=0,
                    last_updated=None,
                )
            )

    # 하위 디렉토리 재귀 탐색
    if current_depth < max_depth:
        for entry in entries:
            if not entry.is_dir(follow_symlinks=False):
                continue
            # exclude 목록 진입 금지
            if entry.name in exclude_set:
                continue
            # 숨김 디렉토리 중 .opal 제외 나머지 스킵
            if entry.name.startswith(".") and entry.name != ".opal":
                continue
            _walk_dir(
                base_root,
                entry.path,
                current_depth + 1,
                max_depth,
                exclude_set,
                results,
            )
