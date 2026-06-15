"""
@header {
  "module": "scanner",
  "layer": "service",
  "domain": "console",
  "description": "scan_roots 하위를 os.walk + maxdepth 가드로 탐색. .opal/AGENT.md 마커로 OPAL 프로젝트 발견. exclude 목록 진입 금지(H-4). 읽기 전용 — mtime 불변",
  "exports": ["scan_projects", "ProjectInfo"],
  "depends": ["config"]
}
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ProjectInfo:
    """단일 프로젝트 발견 결과"""
    name: str
    path: str
    is_opal: bool
    task_count: int
    last_updated: str | None


def _count_tasks(project_path: str) -> int:
    """tasks/ 하위 1-depth 디렉토리 개수 반환 (OPAL 프로젝트 전용)"""
    tasks_dir = os.path.join(project_path, "tasks")
    if not os.path.isdir(tasks_dir):
        return 0
    try:
        return sum(
            1 for entry in os.scandir(tasks_dir)
            if entry.is_dir()
        )
    except OSError:
        return 0


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
