"""
@header {
  "module": "models",
  "layer": "schema",
  "domain": "console",
  "description": "Pydantic 응답 스키마. ProjectInfo·ProjectDetail·TaskCard·MemoryIndex·DoctorReport 등 5개 화면 계약 정의",
  "exports": [
    "HealthResponse",
    "ProjectInfoResponse",
    "ProjectDetailResponse",
    "TaskCardResponse",
    "TaskDetailResponse",
    "MemoryIndexResponse",
    "DoctorReportResponse",
    "DashboardSummaryResponse"
  ],
  "depends": []
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


class TaskDetailResponse(BaseModel):
    task_id: str
    title: str
    skill: str = ""
    mode: str = ""
    current_status: str = ""
    current_stage: str = ""
    progress: int = 0
    pipeline: list[PipelineRow] = []
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
