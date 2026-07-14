"""
@header {
  "module": "models",
  "layer": "schema",
  "domain": "console",
  "description": "Pydantic 응답 스키마. ProjectInfo·ProjectDetail·TaskCard·MemoryIndex·DoctorReport 등 5개 화면 계약 정의. PipelineStageGroup: stage 단위 그룹 스키마(done_count/total/status/rows) — TaskDetailResponse.pipeline 타입. Brain: BrainQueryRequest(project·session_id 필수·빈값→400)·BrainQueryResponse·BrainPrimeResponse·BrainStatusResponse·CitationItem (Phase 2 하드닝 + 대화별 session_id 격리). 비동기 잡 폴링: BrainJobSubmitResponse(job_id 즉시 반환)·BrainJobResponse(job_id·status·answer·citations·error_msg) — PLAN §3.1.2. [T061] 설정 쓰기 스키마(범위 축소, 프라임 풀 스위칭 한정): ConsoleConfigResponse(GET /api/config 스냅샷)·ConfigWriteResponse(쓰기 응답 공통)·PrewarmToggleRequest. console.config 전반 편집(ConsoleConfigUpdate)·프로젝트 로컬 설정 편집(SettingLocalUpdate) 스키마는 캡틴 지시로 제거(T061 범위 축소).",
  "exports": [
    "HealthResponse",
    "ProjectInfoResponse",
    "ProjectDetailResponse",
    "TaskCardResponse",
    "PipelineRow",
    "PipelineStageGroup",
    "TaskDetailResponse",
    "MemoryIndexResponse",
    "DoctorReportResponse",
    "DashboardSummaryResponse",
    "BrainQueryRequest",
    "BrainQueryResponse",
    "BrainJobSubmitResponse",
    "BrainJobResponse",
    "BrainPrimeResponse",
    "BrainStatusResponse",
    "CitationItem",
    "BrainAuthResponse",
    "ConsoleConfigResponse",
    "ConfigWriteResponse",
    "PrewarmToggleRequest"
  ],
  "depends": [],
  "task": "061",
  "changelog": [
    "2026-07-14 T061 Step3: 설정 쓰기 스키마 5종 추가 (ConsoleConfigResponse/ConfigWriteResponse/PrewarmToggleRequest/ConsoleConfigUpdate/SettingLocalUpdate) — F-001~F-004",
    "2026-07-14 T061 범위 축소: ConsoleConfigUpdate·SettingLocalUpdate 제거(console.config 전반·프로젝트 로컬 설정 편집 미반영) — ConfigDict import도 함께 제거"
  ]
}
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


# ── Dashboard ─────────────────────────────────────────────────────────────────

class StatusDistribution(BaseModel):
    pending: int = 0
    in_progress: int = 0
    blocked: int = 0
    done: int = 0


class ActivityPoint(BaseModel):
    date: str
    count: int


class AlertItem(BaseModel):
    task_id: str
    title: str
    project: str
    status: str
    message: str


class RecentActivity(BaseModel):
    date: str
    task_id: str
    title: str
    project: str
    stage: str


class DashboardSummaryResponse(BaseModel):
    total_projects: int = 0
    running_tasks: int = 0
    blockers: int = 0
    additional_work: int = 0
    status_distribution: StatusDistribution = StatusDistribution()
    activity_trend: list[ActivityPoint] = []
    alerts: list[AlertItem] = []
    recent_activities: list[RecentActivity] = []


# ── Projects ──────────────────────────────────────────────────────────────────

class ProjectInfoResponse(BaseModel):
    name: str
    path: str
    is_opal: bool
    task_count: int
    last_updated: str | None = None


class DocItem(BaseModel):
    title: str
    path: str


class ProjectDetailResponse(BaseModel):
    name: str
    path: str
    is_opal: bool = True
    pm_profile: dict[str, Any] = {}
    agent_md: str = ""
    project_md: str = ""
    tech_stack: list[str] = []
    docs: list[DocItem] = []
    warning: str | None = None


# ── Tasks ─────────────────────────────────────────────────────────────────────

class TaskCardResponse(BaseModel):
    task_id: str
    title: str
    skill: str = ""
    mode: str = ""
    column: Literal["pending", "in_progress", "blocked", "done", "archive"] = "pending"
    current_stage: str = ""
    progress: int = 0
    updated_at: str = ""
    artifact_count: int = 0


class PipelineRow(BaseModel):
    row: int
    stage: str
    status: str
    updated_at: str = ""


class PipelineStageGroup(BaseModel):
    stage: str                       # "TASK" | "PLAN" | "EXECUTE" | "TEST" | "CLOSE" 등
    done_count: int                  # 단계 내 done 행 수
    total: int                       # 단계 내 전체 행 수
    status: str                      # 집계 status: done|in_progress|pending|blocked
    rows: list[PipelineRow] = []     # 단계 내부 행 보존 (디버그/툴팁 확장 여지)


class TaskDetailResponse(BaseModel):
    task_id: str
    title: str
    skill: str = ""
    mode: str = ""
    current_status: str = ""
    current_stage: str = ""
    progress: int = 0
    pipeline: list[PipelineStageGroup] = []
    artifacts: list[str] = []
    updated_at: str = ""


# ── Memory ────────────────────────────────────────────────────────────────────

class MemoryRowResponse(BaseModel):
    date: str = ""
    category: str = ""
    status: str = ""
    file: str = ""
    description: str = ""


class HistoryRowResponse(BaseModel):
    date: str = ""
    task: str = ""
    stage: str = ""
    path: str = ""
    start: str | None = None
    end: str | None = None


class MemoryIndexResponse(BaseModel):
    rows: list[MemoryRowResponse] = []
    history: list[HistoryRowResponse] = []
    warning: str | None = None


# ── Brain ─────────────────────────────────────────────────────────────────────

class CitationItem(BaseModel):
    """brain 인용 항목."""
    page: str = ""
    title: str = ""
    type: str = ""
    score: float | None = None


class BrainQueryRequest(BaseModel):
    """POST /api/brain/query 요청 스키마."""
    question: str
    project: str               # 절대경로. 필수 — 빈 값이면 400 반환
    session_id: str            # FE가 생성·전달하는 대화 식별자(UUID). 필수 — 빈 값이면 400 반환
    new_conversation: bool = False  # 호환 목적으로 수신하되 reset 트리거 안 함


class BrainQueryResponse(BaseModel):
    """POST /api/brain/query 응답 스키마 (하위 호환 보존)."""
    answer: str
    citations: list[CitationItem] = []
    session_id: str = ""


class BrainJobSubmitResponse(BaseModel):
    """POST /api/brain/query 비동기 잡 제출 응답 — job_id 즉시 반환 (PLAN §3.1.2)."""
    job_id: str


class BrainJobResponse(BaseModel):
    """GET /api/brain/job/{job_id} 폴링 응답 — 잡 상태 + 결과 (PLAN §3.1.2)."""
    job_id: str
    status: str = "pending"   # "pending" | "done" | "error"
    answer: str = ""
    citations: list[CitationItem] = []
    error_msg: str = ""


class BrainPrimeResponse(BaseModel):
    """POST /api/brain/prime 응답 스키마."""
    priming: bool = True


class BrainAuthResponse(BaseModel):
    """GET /api/brain/auth 응답 스키마."""
    authenticated: bool
    cli_available: bool
    message: str = ""


class BrainStatusResponse(BaseModel):
    """GET /api/brain/status 응답 스키마."""
    state: str           # "idle" | "priming" | "ready" | "error"
    session_active: bool
    message: str = ""    # error 시 사유, 그 외 ""
    session_id: str = "" # 조회된 session_id (에코)


# ── Doctor ────────────────────────────────────────────────────────────────────

class CheckItem(BaseModel):
    status: str  # "ok" | "warn" | "fail"
    message: str


class DoctorSection(BaseModel):
    name: str
    index: int = 0
    total_sections: int = 0
    items: list[CheckItem] = []


class DoctorCounts(BaseModel):
    ok: int = 0
    warn: int = 0
    fail: int = 0
    total: int = 0


class DoctorReportResponse(BaseModel):
    sections: list[DoctorSection] = []
    counts: DoctorCounts = DoctorCounts()
    verdict: str = ""
    skills: list[dict[str, Any]] = []
    warning: str | None = None


# ── Config (설정 쓰기, T061) ──────────────────────────────────────────────────

class ConsoleConfigResponse(BaseModel):
    """GET /api/config 응답 — console.config.json 4필드 스냅샷."""
    scan_roots: list[str]
    scan_depth: int
    exclude: list[str]
    prewarm_projects: list[str]


class ConfigWriteResponse(BaseModel):
    """설정 쓰기 엔드포인트 공통 응답 — 갱신 후 스냅샷."""
    ok: bool = True
    config: dict = {}


class PrewarmToggleRequest(BaseModel):
    """POST /api/config/prewarm 요청 스키마."""
    project: str          # 절대경로. 필수 — 빈값/비스캔 400
    enabled: bool
