"""
@header {
  "module": "routers.memory",
  "layer": "router",
  "domain": "console",
  "description": "GET /api/memory — MEMORY.md 메모리+히스토리 구조화 반환. project 파라미터 지원. 읽기 전용",
  "exports": ["GET /api/memory"],
  "depends": ["models", "scanner", "config", "cache", "parsers.memory_parser", "parsers.memory_file_parser"]
}
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query

from dashboard.backend.cache import cache
from dashboard.backend.config import load_config
from dashboard.backend.models import (
    HistoryRowResponse,
    MemoryIndexResponse,
    MemoryRowResponse,
)
from dashboard.backend.parsers.memory_parser import parse_memory_index
from dashboard.backend.scanner import scan_projects

router = APIRouter()


def _find_project_path(project_path_arg: str) -> str | None:
    # 절대경로(path)로 매칭 — 다른 화면(projects/tasks)과 식별자 통일. name 매칭 시 mams 중복 오선택·경로 불일치 발생
    cfg = load_config()
    projects = scan_projects(cfg.scan_roots, cfg.scan_depth, cfg.exclude)
    for p in projects:
        if p.path == project_path_arg:
            return p.path
    return None


def _parse_memory_for_project(project_path: str) -> MemoryIndexResponse:
    """프로젝트의 MEMORY.md 파싱 → MemoryIndexResponse."""
    memory_path = os.path.join(project_path, ".opal", "MEMORY.md")
    if not os.path.isfile(memory_path):
        return MemoryIndexResponse()

    try:
        with open(memory_path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return MemoryIndexResponse()

    raw = parse_memory_index(content)
    rows = [
        MemoryRowResponse(
            date=r.get("date", ""),
            category=r.get("category", ""),
            status=r.get("status", ""),
            file=r.get("file", ""),
            description=r.get("description", ""),
        )
        for r in raw.get("rows", [])
    ]
    history = [
        HistoryRowResponse(
            date=h.get("date", ""),
            task=h.get("task", ""),
            stage=h.get("stage", ""),
            path=h.get("path", ""),
            start=h.get("start"),
            end=h.get("end"),
        )
        for h in raw.get("history", [])
    ]
    return MemoryIndexResponse(
        rows=rows,
        history=history,
        warning=raw.get("warning"),
    )


@router.get("/api/memory", response_model=MemoryIndexResponse)
def get_memory(
    project: str = Query(default="", description="프로젝트명"),
) -> MemoryIndexResponse:
    """메모리 인덱스 반환 (메모리 표 + 히스토리 표)."""
    if not project:
        # project 미지정 → 첫 번째 OPAL 프로젝트 사용
        cfg = load_config()
        projects = scan_projects(cfg.scan_roots, cfg.scan_depth, cfg.exclude)
        opal_projects = [p for p in projects if p.is_opal]
        if not opal_projects:
            return MemoryIndexResponse()
        project_path = opal_projects[0].path
        project = opal_projects[0].name
    else:
        project_path = _find_project_path(project)
        if project_path is None:
            raise HTTPException(status_code=404, detail=f"Project not found: {project}")

    cache_key = f"memory:{project}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = _parse_memory_for_project(project_path)
    cache.set(cache_key, result)
    return result
