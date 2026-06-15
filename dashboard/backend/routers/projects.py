"""
@header {
  "module": "routers.projects",
  "layer": "router",
  "domain": "console",
  "description": "GET /api/projects, /api/projects/detail?path=, /api/projects/doc?path=&name= — 프로젝트 목록·상세·문서 원문. 절대경로 식별자는 query param으로 전달(path segment 금지). 읽기 전용",
  "exports": [
    "GET /api/projects",
    "GET /api/projects/detail?path=",
    "GET /api/projects/doc?path=&name="
  ],
  "depends": ["models", "scanner", "config", "cache", "parsers.project_parser", "parsers.markdown_reader"]
}
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query

from dashboard.backend.cache import cache
from dashboard.backend.config import load_config
from dashboard.backend.models import DocItem, ProjectDetailResponse, ProjectInfoResponse
from dashboard.backend.parsers.markdown_reader import read_markdown
from dashboard.backend.parsers.project_parser import parse_project
from dashboard.backend.scanner import scan_projects

router = APIRouter()


def _get_projects_cached() -> list[ProjectInfoResponse]:
    key = "projects_list"
    cached = cache.get(key)
    if cached is not None:
        return cached
    cfg = load_config()
    raw = scan_projects(cfg.scan_roots, cfg.scan_depth, cfg.exclude)
    result = [
        ProjectInfoResponse(
            name=p.name,
            path=p.path,
            is_opal=p.is_opal,
            task_count=p.task_count,
            last_updated=p.last_updated,
        )
        for p in raw
    ]
    cache.set(key, result)
    return result


def _find_project_by_path(project_path: str) -> ProjectInfoResponse | None:
    """절대경로로 프로젝트를 찾는다 (query param 방식 — path segment 금지)."""
    projects = _get_projects_cached()
    for p in projects:
        if p.path == project_path:
            return p
    return None


@router.get("/api/projects", response_model=list[ProjectInfoResponse])
def list_projects() -> list[ProjectInfoResponse]:
    """프로젝트 목록 반환 (OPAL/비OPAL 포함)."""
    return _get_projects_cached()


@router.get("/api/projects/detail", response_model=ProjectDetailResponse)
def get_project_detail(
    path: str = Query(..., description="프로젝트 절대경로 (URL-encoded)"),
) -> ProjectDetailResponse:
    """프로젝트 상세 — PM프로필·기술스택·문서 목록.

    절대경로는 query param으로 전달한다 — path segment에 슬래시 포함 시
    FastAPI 단일 세그먼트 매칭 실패로 SPA fallback이 호출되는 근본 버그를 방지.
    """
    proj = _find_project_by_path(path)
    if proj is None:
        raise HTTPException(status_code=404, detail=f"Project not found: {path}")

    cache_key = f"project_detail:{path}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    raw = parse_project(proj.path)
    docs = [DocItem(title=d["title"], path=d["path"]) for d in raw.get("docs", [])]
    result = ProjectDetailResponse(
        name=raw["name"],
        path=raw["path"],
        is_opal=proj.is_opal,
        pm_profile=raw.get("pm_profile", {}),
        agent_md=raw.get("agent_md", ""),
        project_md=raw.get("project_md", ""),
        tech_stack=raw.get("tech_stack", []),
        docs=docs,
        warning=raw.get("warning"),
    )
    cache.set(cache_key, result)
    return result


@router.get("/api/projects/doc")
def get_project_doc(
    path: str = Query(..., description="프로젝트 절대경로 (URL-encoded)"),
    name: str = Query(default="PROJECT.md", description="문서 파일명 (docs/ 하위)"),
) -> dict:
    """프로젝트 문서 원문 반환 (markdown_reader).

    절대경로는 query param으로 전달한다 — path segment 방식 금지.
    """
    proj = _find_project_by_path(path)
    if proj is None:
        raise HTTPException(status_code=404, detail=f"Project not found: {path}")

    # 보안: path traversal 방지 — 파일명에 / \ 포함 금지
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(status_code=400, detail="Invalid doc name")

    doc_path = os.path.join(proj.path, "docs", name)
    content = read_markdown(doc_path)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Document not found: {name}")

    return {"name": name, "content": content, "path": doc_path}
