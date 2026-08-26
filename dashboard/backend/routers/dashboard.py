"""
@header {
  "module": "routers.dashboard",
  "layer": "router",
  "domain": "console",
  "description": "GET /api/dashboard — 전 프로젝트 집계 또는 개별 프로젝트 집계(4메트릭·상태분포·활동추이·주의알림·최근활동). project 쿼리 파라미터로 개별/전체 구분. 읽기 전용. 최근활동·주의알림 title은 TASK.md H1에서 파생(_resolve_task_title: 'TASK NNN —'/'TASK:' 접두사 제거, 부재 시 폴더명 슬러그 폴백) — state.json에 title 필드가 없어 폴더명 중복 방지. [T103] 워크플로우별 횡단 집계 additive — 모수는 current_status == done인 완료 태스크만이며(집계기준 3) 진행 중은 total_tasks 차이로만 드러난다. stats.workflow_stats(skill 단위 중앙값·2계열·3계열(pm/worker/captain)·단계별)를 호출하기 전 각 state에 _title을 주입한다(stats.py는 파일 I/O를 하지 않는다). 산출물 규모(artifact_total·artifact_by_type 4유형)는 routers.tasks의 _get_artifact_files·classify_artifact를 함수 내부 지연 import로 호출한다(COLUMN_MAP 선례). 캐시는 현행 유지 — 모수에 실시간 성분이 없고 다중 파일 소스라 단일 source_path mtime 무효화가 적용 불가하다. [T103 R-21] 야간 제외 구간(집계 기준 17)은 라우터가 config.load_quiet_hours로 읽어 workflow_stats에 주입한다 — 개별 프로젝트 모드는 그 프로젝트의 로컬 설정이 전역을 덮고, 전체 모드는 어느 프로젝트도 편들 수 없어 전역 설정만 쓴다. 캐시 키 `dashboard:{project|ALL}:{구간서명}`에 서명을 실어 설정 변경 시 보정 전후 값이 같은 키를 공유하지 않게 했다.",
  "exports": ["GET /api/dashboard"],
  "depends": ["models", "scanner", "config", "cache", "stats", "adapters.state_adapter"],
  "changelog": [
    "2026-08-26 호칭 하드코딩 제거: 응답에 owner_term 표면화 — config.load_owner_name() 1회 호출. 집계·필터 경로 무변경",
    "2026-08-26 T103 R-21: 야간 제외 구간을 config.load_quiet_hours로 읽어 workflow_stats에 주입 + 캐시 키에 구간 서명 부착 + 응답에 quiet_hours_applied·quiet_hours_label 표면화",
    "2026-08-25 T103 R-16: workflow_stats 3계열 필드가 WorkflowStat(**w) 경로로 자동 승계 — 라우터 로직 무변경, @header 기술만 갱신",
    "2026-08-25 T103 Step7: 워크플로우별 집계 5필드 additive(completed_tasks·total_tasks·artifact_total·artifact_by_type·workflow_stats) — F-003, TS-020~024. 기존 8필드 무변경"
  ]
}
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from dashboard.backend.cache import cache
from dashboard.backend.config import load_config, load_owner_name, load_quiet_hours, quiet_hours_token
from dashboard.backend.models import (
    ActivityPoint,
    AlertItem,
    DashboardSummaryResponse,
    RecentActivity,
    StatusDistribution,
    WorkflowStat,
)
from dashboard.backend.scanner import scan_projects
from dashboard.backend.stats import format_quiet_hours, workflow_stats

router = APIRouter()


def _get_state_for_task(task_dir: str) -> dict | None:
    """task 디렉토리의 state.json을 직접 읽어 반환 (실패 시 None)."""
    state_path = os.path.join(task_dir, "state.json")
    if not os.path.isfile(state_path):
        return None
    try:
        import json
        with open(state_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _collect_all_tasks(project_path: str) -> list[dict]:
    """프로젝트의 모든 태스크 state 수집."""
    tasks_dir = os.path.join(project_path, "tasks")
    if not os.path.isdir(tasks_dir):
        return []
    tasks = []
    try:
        for entry in os.scandir(tasks_dir):
            if not entry.is_dir():
                continue
            state = _get_state_for_task(entry.path)
            if state:
                state["_task_id"] = entry.name
                state["_project"] = os.path.basename(project_path)
                state["_task_dir"] = entry.path
                tasks.append(state)
    except OSError:
        pass
    return tasks


# task_id에서 설명 슬러그 추출 (NNN-YYMMDD-skill- 접두사 제거) — 폴백용
_TASK_ID_SLUG_RE = re.compile(r"^\d+-\d+-[a-z0-9]+-(.+)$")
# H1 선행 'TASK' 키워드 + 구분자(: — -)/공백 제거
_TASK_KW_RE = re.compile(r"^TASK\b[\s:—\-]*(.*)$")
# 남은 앞부분이 '숫자id 구분자 제목'이면 id+구분자 추가 제거 (콜론형 'TASK: 제목'은 미해당)
_TASK_ID_HEAD_RE = re.compile(r"^\d\S*\s*[—:\-]\s*(.+)$")


def _strip_task_heading(h1: str) -> str:
    """TASK.md H1에서 'TASK NNN —' / 'TASK:' 등 관례 접두사를 제거해 제목부만 남긴다.

    - 'TASK 028 — 데이터 구조 실측 자산화' → '데이터 구조 실측 자산화'
    - 'TASK: 캠페인 리포트 상품 랭킹 API — 모바일 전환' → '캠페인 리포트 상품 랭킹 API — 모바일 전환'
    - 'TASK' 접두사가 없으면 H1 원문 유지
    """
    m = _TASK_KW_RE.match(h1)
    rest = m.group(1).strip() if m else h1
    m2 = _TASK_ID_HEAD_RE.match(rest)
    if m2:
        rest = m2.group(1).strip()
    return rest or h1


def _resolve_task_title(task_dir: str, task_id: str) -> str:
    """TASK.md H1에서 사람이 쓴 제목을 추출. 실패 시 폴더명 슬러그로 폴백.

    - TASK.md 부재/파싱 실패 → task_id 슬러그(접두사 제거), 그것도 실패면 task_id 원본
    """
    task_md = os.path.join(task_dir, "TASK.md") if task_dir else ""
    if task_md and os.path.isfile(task_md):
        try:
            with open(task_md, encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s.startswith("# "):
                        return _strip_task_heading(s[2:].strip())
        except OSError:
            pass
    m = _TASK_ID_SLUG_RE.match(task_id)
    return m.group(1) if m else task_id


@router.get("/api/dashboard", response_model=DashboardSummaryResponse)
def get_dashboard(project: str = Query(default="")) -> DashboardSummaryResponse:
    """전 프로젝트 또는 개별 프로젝트 집계 데이터 반환.

    Args:
        project: 절대경로 문자열. 비어있으면 전체 OPAL 프로젝트 집계.
                 지정 시 해당 프로젝트 1개만 집계. 매칭 없으면 404.
    """
    # 야간 제외 구간(집계 기준 17)은 라우터가 읽어 stats.py에 주입한다.
    # 개별 프로젝트 모드면 그 프로젝트의 로컬 설정이 전역을 덮고, 전체 모드는
    # 어느 프로젝트 하나를 편들 수 없으므로 전역 설정만 쓴다.
    quiet_hours = load_quiet_hours(project or None)

    # 캐시 키에 구간 서명을 실어 설정 변경이 곧바로 갈리게 한다.
    cache_key = f"dashboard:{project or 'ALL'}:{quiet_hours_token(quiet_hours)}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    cfg = load_config()
    projects = scan_projects(cfg.scan_roots, cfg.scan_depth, cfg.exclude)
    opal_projects = [p for p in projects if p.is_opal]

    if project:
        # 개별 프로젝트 모드
        matched = [p for p in opal_projects if p.path == project]
        if not matched:
            raise HTTPException(status_code=404, detail=f"Project not found: {project}")
        target_projects = matched
    else:
        # 전체 프로젝트 모드
        target_projects = opal_projects

    all_tasks: list[dict] = []
    for proj in target_projects:
        all_tasks.extend(_collect_all_tasks(proj.path))

    # 태스크 제목 주입 — B-3 리드타임 표의 표시명 (stats.py는 파일 I/O를 하지 않는다)
    for t in all_tasks:
        t["_title"] = _resolve_task_title(t.get("_task_dir", ""), t.get("_task_id", ""))

    # 4메트릭
    running = sum(
        1 for t in all_tasks
        if t.get("current_status") in ("in_progress", "additional_work")
    )
    blockers = sum(1 for t in all_tasks if t.get("current_status") == "blocked")
    additional_work = sum(
        1 for t in all_tasks if t.get("current_status") == "additional_work"
    )

    # 상태 분포 (칸반 4컬럼 기준)
    from dashboard.backend.routers.tasks import COLUMN_MAP
    dist = StatusDistribution()
    col_counts: dict[str, int] = {"pending": 0, "in_progress": 0, "blocked": 0, "done": 0}
    for t in all_tasks:
        status = t.get("current_status", "")
        col = COLUMN_MAP.get(status, "pending")
        col_counts[col] = col_counts.get(col, 0) + 1
    dist.pending = col_counts["pending"]
    dist.in_progress = col_counts["in_progress"]
    dist.blocked = col_counts["blocked"]
    dist.done = col_counts["done"]

    # 활동 추이 (최근 7일, 태스크 updated_at 기준)
    today = datetime.now().date()
    activity_by_date: dict[str, int] = {}
    for i in range(7):
        d = (today - timedelta(days=6 - i)).isoformat()
        activity_by_date[d] = 0
    for t in all_tasks:
        upd = t.get("updated_at", "")
        if upd:
            d = upd[:10]
            if d in activity_by_date:
                activity_by_date[d] += 1
    activity_trend = [ActivityPoint(date=d, count=c) for d, c in sorted(activity_by_date.items())]

    # 주의 알림 (블로커 + 오래된 진행중)
    alerts: list[AlertItem] = []
    for t in all_tasks:
        st = t.get("current_status", "")
        task_id = t.get("_task_id", "")
        proj_name = t.get("_project", "")
        title = _resolve_task_title(t.get("_task_dir", ""), task_id)
        if st == "blocked":
            alerts.append(AlertItem(
                task_id=task_id,
                title=title,
                project=proj_name,
                status=st,
                message="블로킹 상태",
            ))

    # 최근 활동 (업데이트 최신 5건)
    recent_raw = sorted(
        all_tasks,
        key=lambda t: t.get("updated_at", ""),
        reverse=True,
    )[:5]
    recent_activities = [
        RecentActivity(
            date=t.get("updated_at", "")[:10],
            task_id=t.get("_task_id", ""),
            title=_resolve_task_title(t.get("_task_dir", ""), t.get("_task_id", "")),
            project=t.get("_project", ""),
            stage=t.get("current_stage", ""),
        )
        for t in recent_raw
    ]

    # 워크플로우별 집계 (T103 R-10) — 모수는 완료 태스크만 (집계기준 3)
    completed = [t for t in all_tasks if t.get("current_status") == "done"]
    workflows = [WorkflowStat(**w) for w in workflow_stats(completed, quiet_hours)]

    # 산출물 규모 — 파일시스템 접근이므로 tasks.py 헬퍼를 지연 import한다 (COLUMN_MAP 선례)
    from dashboard.backend.routers.tasks import _get_artifact_files, classify_artifact
    artifact_by_type: dict[str, int] = {
        "pipeline": 0, "verification": 0, "log": 0, "other": 0,
    }
    for t in all_tasks:
        for name in _get_artifact_files(t.get("_task_dir", "")):
            artifact_type, _ = classify_artifact(name)
            artifact_by_type[artifact_type] += 1

    result = DashboardSummaryResponse(
        total_projects=len(target_projects),
        running_tasks=running,
        blockers=blockers,
        additional_work=additional_work,
        status_distribution=dist,
        activity_trend=activity_trend,
        alerts=alerts,
        recent_activities=recent_activities,
        completed_tasks=len(completed),
        total_tasks=len(all_tasks),
        artifact_total=sum(artifact_by_type.values()),
        artifact_by_type=artifact_by_type,
        workflow_stats=workflows,
        quiet_hours_applied=quiet_hours is not None,
        quiet_hours_label=format_quiet_hours(quiet_hours),
        # 사용자 호칭 표면화 — 화면 문구·범례가 이 값으로 조립한다 (하드코딩 금지)
        owner_term=load_owner_name(),
    )
    cache.set(cache_key, result)
    return result
