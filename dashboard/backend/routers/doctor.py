"""
@header {
  "module": "routers.doctor",
  "layer": "router",
  "domain": "console",
  "description": "GET /api/doctor — doctor 4섹션+MCP+스킬 구조화 반환. project 파라미터 지원(캐시 키 분리 + 프로젝트 OPAL 구조 섹션 추가). 읽기 전용",
  "exports": ["GET /api/doctor"],
  "depends": ["models", "cache", "adapters.doctor_adapter", "adapters.skill_adapter"]
}
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Query

from dashboard.backend.adapters.doctor_adapter import get_doctor
from dashboard.backend.adapters.skill_adapter import list_skills
from dashboard.backend.cache import cache
from dashboard.backend.models import (
    CheckItem,
    DoctorCounts,
    DoctorReportResponse,
    DoctorSection,
)

router = APIRouter()

CACHE_KEY_DOCTOR = "doctor_report"
CACHE_KEY_SKILLS = "skills_list"


def _build_project_section(project_path: str) -> DoctorSection:
    """프로젝트 경로의 OPAL 구조 체크 섹션을 빌드한다."""
    p = Path(project_path)
    project_name = p.name if p.name else project_path

    items: list[CheckItem] = []

    # 프로젝트 경로 존재 여부
    if p.exists():
        items.append(CheckItem(status="ok", message=f"프로젝트 경로 존재: {project_path}"))
    else:
        items.append(CheckItem(status="fail", message=f"프로젝트 경로 없음: {project_path}"))
        return DoctorSection(
            name=f"프로젝트 — {project_name}",
            index=0,
            total_sections=0,
            items=items,
        )

    # .opal/ 디렉토리 존재 여부
    opal_dir = p / ".opal"
    if opal_dir.exists():
        items.append(CheckItem(status="ok", message=".opal/ 디렉토리 존재"))
    else:
        items.append(CheckItem(status="warn", message=".opal/ 디렉토리 없음 (OPAL 미초기화)"))

    # 핵심 파일 체크
    key_files = [
        (".opal/AGENT.md", "AGENT.md (PM 정의)"),
        (".opal/MEMORY.md", "MEMORY.md (메모리 인덱스)"),
        (".opal/code-scan.json", "code-scan.json (코드 스캔)"),
        (".opal/brain", "brain/ (지식 베이스)"),
    ]
    for rel_path, label in key_files:
        full_path = p / rel_path
        if full_path.exists():
            items.append(CheckItem(status="ok", message=f"{label}"))
        else:
            items.append(CheckItem(status="warn", message=f"{label} — 없음"))

    # tasks/ 디렉토리 + 태스크 수
    tasks_dir = p / "tasks"
    if tasks_dir.exists():
        task_count = len([d for d in tasks_dir.iterdir() if d.is_dir()])
        items.append(CheckItem(status="ok", message=f"tasks/ — {task_count}개 태스크 폴더"))
    else:
        items.append(CheckItem(status="warn", message="tasks/ 디렉토리 없음"))

    return DoctorSection(
        name=f"프로젝트 — {project_name}",
        index=0,
        total_sections=0,
        items=items,
    )


@router.get("/api/doctor", response_model=DoctorReportResponse)
def get_doctor_report(
    project: str = Query(default="", description="프로젝트 경로 (선택 시 해당 프로젝트 OPAL 구조 섹션 추가)"),
) -> DoctorReportResponse:
    """doctor 4섹션 + MCP + 스킬 목록 반환. project 지정 시 캐시 키 분리 + 프로젝트 섹션 추가."""
    cache_key = f"doctor:{project}" if project else CACHE_KEY_DOCTOR
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # doctor 실행
    try:
        raw = get_doctor()
    except Exception as exc:
        # doctor 실행 실패 — graceful 폴백
        raw = {
            "sections": [],
            "verdict": "",
            "counts": {"ok": 0, "warn": 0, "fail": 0, "total": 0},
            "warning": str(exc),
        }

    sections = [
        DoctorSection(
            name=s.get("name", ""),
            index=s.get("index", 0),
            total_sections=s.get("total_sections", 0),
            items=[
                CheckItem(status=it.get("status", ""), message=it.get("message", ""))
                for it in s.get("items", [])
            ],
        )
        for s in raw.get("sections", [])
    ]

    # project 파라미터가 있으면 해당 프로젝트 OPAL 구조 섹션을 맨 앞에 추가
    if project:
        project_section = _build_project_section(project)
        sections = [project_section] + sections

    counts_raw = raw.get("counts", {})
    counts = DoctorCounts(
        ok=counts_raw.get("ok", 0),
        warn=counts_raw.get("warn", 0),
        fail=counts_raw.get("fail", 0),
        total=counts_raw.get("total", 0),
    )

    # 스킬 목록
    skills: list[dict] = []
    try:
        skills_cached = cache.get(CACHE_KEY_SKILLS)
        if skills_cached is not None:
            skills = skills_cached
        else:
            skills = list_skills()
            cache.set(CACHE_KEY_SKILLS, skills)
    except Exception:
        skills = []

    result = DoctorReportResponse(
        sections=sections,
        counts=counts,
        verdict=raw.get("verdict", ""),
        skills=skills,
        warning=raw.get("warning"),
    )
    cache.set(cache_key, result)
    return result
