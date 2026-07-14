"""
@header {
  "module": "routers.config",
  "layer": "router",
  "domain": "console",
  "description": "설정 쓰기 라우터(T061 신설, T061 추가작업 범위 축소) — 콘솔 '읽기 전용' 원칙의 유일한 예외. 이번 범위는 프라임 풀 스위칭 한정: 쓰기 대상은 ~/.opal/console.config.json의 prewarm_projects 필드뿐이다. _require_project_path(brain.py 선례 재사용)로 project 빈값/비스캔 400. GET /api/config(스냅샷) + POST /api/config/prewarm(토글, 신규 등재 시에만 prewarm() 1회 호출). [MUST] LLM/claude 서브프로세스 호출은 이 라우터에서 0회 — 파일 쓰기 + prewarm() 호출만 수행한다(brain.py 라우터 격리 원칙 준수). 거부된 쓰기 요청은 logger.warning으로 기록한다. console.config 전반 편집·프로젝트 로컬 설정 편집은 이번 범위에서 제외(수동 JSON 편집 대체) — 캡틴 지시로 미사용 쓰기 API(POST /api/config/console, GET|POST /api/config/project-local) 제거(T061 범위 축소).",
  "exports": [
    "GET /api/config",
    "POST /api/config/prewarm"
  ],
  "depends": ["config", "scanner", "models", "adapters.brain_session"],
  "task": "061",
  "changelog": [
    "2026-07-14 T061 Step3~7: 설정 쓰기 라우터 신설 — 경로검증/화이트리스트 헬퍼 + GET/config·POST/console·POST/prewarm·GET|POST/project-local (F-001~F-004)",
    "2026-07-14 T061 범위 축소: 캡틴 지시로 프라임 풀 스위칭만 반영 — POST /api/config/console, GET|POST /api/config/project-local, _resolve_setting_local_path 제거(미사용 쓰기 표면 최소화)"
  ]
}
"""
from __future__ import annotations

import logging
from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from dashboard.backend.adapters.brain_session import brain_session_registry
from dashboard.backend.config import load_config, save_config
from dashboard.backend.models import (
    ConfigWriteResponse,
    ConsoleConfigResponse,
    PrewarmToggleRequest,
)
from dashboard.backend.scanner import scan_projects

router = APIRouter()

logger = logging.getLogger(__name__)


# ── 경로 검증 · 화이트리스트 헬퍼 (brain.py 선례 재사용) ──────────────────────

def _resolve_project_path(project: str) -> str:
    """project 절대경로 검증 및 반환. 빈값/비스캔 시 빈 문자열 반환(brain.py와 동일 계약)."""
    if not project:
        return ""

    cfg = load_config()
    projects = scan_projects(cfg.scan_roots, cfg.scan_depth, cfg.exclude)

    for p in projects:
        if p.path == project:
            return p.path

    return ""


def _require_project_path(project: str) -> str:
    """project 검증 후 절대경로 반환. 실패 시 HTTPException(400) raise + 거부 로깅."""
    if not project:
        logger.warning("[config] 거부: project 빈 값")
        raise HTTPException(
            status_code=400,
            detail="project가 필수입니다. OPAL 프로젝트 절대경로를 지정하세요.",
        )

    resolved = _resolve_project_path(project)
    if not resolved:
        logger.warning("[config] 거부: 비스캔 프로젝트 경로 %r", project)
        raise HTTPException(
            status_code=400,
            detail=f"프로젝트를 찾을 수 없습니다: {project!r}",
        )

    return resolved


# ── GET /api/config ───────────────────────────────────────────────────────────

@router.get("/api/config", response_model=ConsoleConfigResponse)
def get_config() -> ConsoleConfigResponse:
    """console.config.json 4필드 스냅샷 반환."""
    cfg = load_config()
    return ConsoleConfigResponse(**asdict(cfg))


# ── POST /api/config/prewarm ──────────────────────────────────────────────────

@router.post("/api/config/prewarm", response_model=ConfigWriteResponse)
def post_prewarm(body: PrewarmToggleRequest) -> ConfigWriteResponse:
    """프라임 풀 토글 — ON 시 prewarm_projects 신규 등재하고 즉시 선프라임(비블로킹, 멱등)."""
    project_path = _require_project_path(body.project)      # 400 게이트
    cfg = load_config()
    projects = list(cfg.prewarm_projects)
    newly_added = False
    if body.enabled and project_path not in projects:
        projects.append(project_path)
        newly_added = True
    elif not body.enabled and project_path in projects:
        projects.remove(project_path)
    snapshot = save_config({"prewarm_projects": projects})  # 머지 보존
    if newly_added:
        brain_session_registry.prewarm(project_path)        # 즉시 선프라임(비블로킹, 재기동 불요)
    return ConfigWriteResponse(config=snapshot)
