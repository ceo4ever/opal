"""
@header {
  "module": "models",
  "layer": "schema",
  "domain": "console",
  "description": "Pydantic 응답 스키마. ProjectInfo·ProjectDetail·TaskCard·MemoryIndex·DoctorReport 등 5개 화면 계약 정의. PipelineStageGroup: stage 단위 그룹 스키마(done_count/total/status/rows) — TaskDetailResponse.pipeline 타입. Brain: BrainQueryRequest(project·session_id 필수·빈값→400)·BrainQueryResponse·BrainPrimeResponse·BrainStatusResponse·CitationItem (Phase 2 하드닝 + 대화별 session_id 격리). 비동기 잡 폴링: BrainJobSubmitResponse(job_id 즉시 반환)·BrainJobResponse(job_id·status·answer·citations·error_msg) — PLAN §3.1.2. [T061] 설정 쓰기 스키마(범위 축소, 프라임 풀 스위칭 한정): ConsoleConfigResponse(GET /api/config 스냅샷)·ConfigWriteResponse(쓰기 응답 공통)·PrewarmToggleRequest. console.config 전반 편집(ConsoleConfigUpdate)·프로젝트 로컬 설정 편집(SettingLocalUpdate) 스키마는 캡틴 지시로 제거(T061 범위 축소). [T103] 태스크 진행 통계 스키마: PipelineGate(artifacts·checklist 객체, 불리언 아님)·TaskStats(정적+실시간 파생 병합)·ArtifactItem(4유형 분류)·WorkflowStat/StageStat/TaskLeadtime(skill 단위 횡단 집계) 6종 신설 + PipelineRow·PipelineStageGroup·TaskDetailResponse·DashboardSummaryResponse 전건 기본값 additive 확장. [MUST] 집계기준 15 — 응답 키는 원천 용어(skill·timestamp·row_id)를 쓰고 workflow 키를 만들지 않으며, 사표 필드 row·updated_at은 deprecated 별칭으로 존치하되 값을 채운다. [T103/R-16] 소요 3계열 분해 additive — TaskStats·PipelineStageGroup·StageStat·WorkflowStat 4종에 pm_minutes·worker_minutes·captain_minutes·worker_measured를 추가한다(집계기준 16). work·wait는 하위 호환으로 존치하며 work == pm + worker · wait == captain 항등이 성립한다. worker_measured는 「워커 0분」과 「미측정」(필드 부재)을 FE가 구분하기 위한 신호다. [T103/R-20] 3계열 표시 문자열 additive — 단계 층(PipelineStageGroup·StageStat)·워크플로우 층(WorkflowStat)·태스크 막대(TaskLeadtime)에 pm_label·worker_label·captain_label을 추가하고, StageStat에는 막대 폭의 분모이자 「단계 총」인 누적 total_minutes·total_label(= work + wait)을 함께 둔다. 화면의 구획 호버가 읽을 지표이며 표시 문자열 소유권은 여전히 BE 단일 지점이다(P-7). [호칭 하드코딩 제거] owner_term — 사용자 호칭을 응답에 실어 FE가 문구를 조립하게 한다. TaskDetailResponse(상세)·DashboardSummaryResponse(대시보드) 최상위 1필드씩이며 원천은 config.load_owner_name(identity.md, 폴백 \"사용자\")다. PipelineRow.owner_label의 owner==user 라벨도 같은 값을 쓴다 — PM·auto는 역할명이라 불변이다.",
  "exports": [
    "HealthResponse",
    "ProjectInfoResponse",
    "ProjectDetailResponse",
    "TaskCardResponse",
    "PipelineGate",
    "PipelineRow",
    "PipelineStageGroup",
    "TaskStats",
    "ArtifactItem",
    "TaskDetailResponse",
    "MemoryIndexResponse",
    "DoctorReportResponse",
    "StageStat",
    "TaskLeadtime",
    "WorkflowStat",
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
    "2026-08-25 T103 R-16: 소요 3계열 필드 additive — TaskStats(pm/worker/captain 분·라벨 + worker_measured + worker_clamped_count)·PipelineStageGroup·StageStat·WorkflowStat 4종 확장. 기존 work·wait 필드 무변경 존치",
    "2026-07-14 T061 범위 축소: ConsoleConfigUpdate·SettingLocalUpdate 제거(console.config 전반·프로젝트 로컬 설정 편집 미반영) — ConfigDict import도 함께 제거",
    "2026-07-15 T063 Step5(F-004): BrainQueryRequest.new_conversation 폐기 필드 제거 — FE가 더 이상 전송하지 않음(휘발성 단일 세션 전환, 새 대화는 새 session_id로 처리). pydantic extra 필드 무시 규칙상 하위호환 영향 없음",
    "2026-07-28 T078 F-009: MemoryRowResponse.title / HistoryRowResponse.result additive 추가 — MEMORY.json 전환 신필드, 기존 필드 무변경(H-6)",
    "2026-08-26 호칭 하드코딩 제거: TaskDetailResponse·DashboardSummaryResponse에 owner_term 1필드 additive — 사용자 호칭의 응답 표면화(원천 identity.md, 폴백 \"사용자\"). 기존 필드 제거·타입 변경 0건",
    "2026-08-26 T103 R-21: 야간 보정 표면화 additive — TaskStats·WorkflowStat·DashboardSummaryResponse에 quiet_hours_applied·quiet_hours_label 2필드 추가. 기존 필드 제거·타입 변경 0건",
    "2026-08-25 T103 Step4: 진행 통계 응답 스키마 6종 신설 + 4모델 additive 확장 — PipelineRow 원천 7필드·파생 4필드, PipelineStageGroup 5필드, TaskDetailResponse stats·artifact_items, DashboardSummaryResponse 5필드. 기존 필드 제거·타입 변경 0건(PipelineRow.row는 필수 → 기본값 0으로 완화)"
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


class StageStat(BaseModel):
    """워크플로우 내 단계 1개의 횡단 집계 (103)."""
    stage: str
    n: int = 0                       # 해당 단계를 보유한 완료 태스크 수
    median_minutes: int = 0
    median_label: str = "—"
    work_minutes: int = 0
    wait_minutes: int = 0
    # 누적 총 = work + wait (막대 폭의 분모 · 구획 호버의 「단계 총」, R-20)
    total_minutes: int = 0
    total_label: str = "—"
    # 3계열 분해 (집계기준 16, R-16) — work = pm + worker, wait = captain
    pm_minutes: int = 0
    worker_minutes: int = 0
    captain_minutes: int = 0
    # 3계열 표시 문자열 (R-20) — 구획 호버 지표. FE는 조립하지 않는다 (P-7)
    pm_label: str = "—"
    worker_label: str = "—"
    captain_label: str = "—"
    worker_measured: bool = False    # 단계 내 워커 소요 기록 행 존재 여부
    is_peak: bool = False


class TaskLeadtime(BaseModel):
    """워크플로우 내 완료 태스크 1건의 총 리드타임 (103)."""
    task_id: str
    title: str = ""
    total_minutes: int = 0
    total_label: str = "—"
    # 3계열 분해·표시 문자열 (R-20) — 태스크 막대 호버 지표. 태스크 층 값을 그대로 승계한다
    pm_minutes: int = 0
    pm_label: str = "—"
    worker_minutes: int = 0
    worker_label: str = "—"
    captain_minutes: int = 0
    captain_label: str = "—"
    worker_measured: bool = False
    is_peak: bool = False


class WorkflowStat(BaseModel):
    """skill 단위 횡단 집계 (103). 모수는 완료 태스크만 (집계기준 3).

    [MUST] 집계기준 15 — 키는 원천 용어 `skill`이며 `workflow` 키를 만들지 않는다.
    「워크플로우」는 UI 표시 라벨로만 남는다.
    """
    skill: str
    n: int = 0
    sample_insufficient: bool = False  # n < 5 → FE 「표본 부족」 배지
    median_minutes: int = 0            # 주 지표
    median_label: str = "—"
    mean_minutes: int = 0              # 보조 지표
    mean_label: str = "—"
    work_minutes: int = 0
    wait_minutes: int = 0
    wait_ratio: int = 0
    # 3계열 분해 (집계기준 16, R-16)
    pm_minutes: int = 0
    worker_minutes: int = 0
    captain_minutes: int = 0
    # 3계열 표시 문자열 (R-20) — FE는 조립하지 않는다 (P-7)
    pm_label: str = "—"
    worker_label: str = "—"
    captain_label: str = "—"
    worker_measured: bool = False    # 코호트 내 워커 소요 기록 태스크 존재 여부
    gate_count: int = 0
    blocker_count: int = 0
    # 야간 보정 표면화 (집계기준 17, R-21)
    quiet_hours_applied: bool = False
    quiet_hours_label: str = ""
    stages: list[StageStat] = []
    tasks: list[TaskLeadtime] = []


class DashboardSummaryResponse(BaseModel):
    total_projects: int = 0
    running_tasks: int = 0
    blockers: int = 0
    additional_work: int = 0
    status_distribution: StatusDistribution = StatusDistribution()
    activity_trend: list[ActivityPoint] = []
    alerts: list[AlertItem] = []
    recent_activities: list[RecentActivity] = []
    # 103 additive
    completed_tasks: int = 0
    total_tasks: int = 0
    artifact_total: int = 0
    artifact_by_type: dict[str, int] = {}
    workflow_stats: list[WorkflowStat] = []
    # 야간 보정 표면화 (집계기준 17, R-21) — 대시보드 배지 1개의 원천
    quiet_hours_applied: bool = False
    quiet_hours_label: str = ""
    # 사용자 호칭 표면화 — FE가 「{owner_term} 확인 대기」 류 문구를 조립한다
    owner_term: str = ""


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


class PipelineGate(BaseModel):
    """state.json rows[].gate — 게이트 행의 산출물·체크리스트 (불리언 아닌 객체)."""
    artifacts: list[str] = []
    checklist: list[str] = []


class PipelineRow(BaseModel):
    # 기존 필드 — row·updated_at은 deprecated 별칭으로 존치하되 값을 채운다 (집계기준 15)
    row: int = 0                     # deprecated 별칭 — row_id 값으로 채운다
    stage: str
    status: str
    updated_at: str = ""             # deprecated 별칭 — timestamp 값으로 채운다
    # 원천 필드 (103 additive) — state.json 스키마 용어를 그대로 쓴다
    row_id: int = 0                  # 원천 정렬 키
    key: str = ""                    # `*.user_confirm` 판정 원천
    item: str = ""                   # A-4 「항목」 열
    timestamp: str = ""              # 원천 시각
    time_label: str = ""             # `YY-MM-DD HH:mm:ss` 표시 문자열 (stats.format_timestamp 소유)
    owner: str = ""                  # 2계열 귀속 원천
    owner_label: str = ""            # PM | {사용자 호칭} | 자동 (호칭은 identity.md 원천)
    note: str | None = None
    gate: PipelineGate | None = None  # None = 게이트 행 아님
    # 파생 필드 (103 additive) — stats.py row_durations 결과
    duration_minutes: int = 0
    duration_label: str = ""
    series: str = ""                 # work | wait | ""(비 done)
    is_max_gap: bool = False


class PipelineStageGroup(BaseModel):
    stage: str                       # "TASK" | "PLAN" | "EXECUTE" | "TEST" | "CLOSE" 등
    done_count: int                  # 단계 내 done 행 수
    total: int                       # 단계 내 전체 행 수
    status: str                      # 집계 status: done|in_progress|pending|blocked
    rows: list[PipelineRow] = []     # 단계 내부 행 보존 (디버그/툴팁 확장 여지)
    # 단계 소요 파생 (103 additive)
    work_minutes: int = 0
    wait_minutes: int = 0
    total_minutes: int = 0
    total_label: str = ""
    is_peak: bool = False            # 최장 단계 강조
    # 3계열 분해 (집계기준 16, R-16) — A-2 3색 스택 막대의 원천
    pm_minutes: int = 0
    worker_minutes: int = 0
    captain_minutes: int = 0
    # 3계열 표시 문자열 (R-20) — 구획 호버 지표. FE는 조립하지 않는다 (P-7)
    pm_label: str = "—"
    worker_label: str = "—"
    captain_label: str = "—"
    worker_measured: bool = False


class TaskStats(BaseModel):
    """태스크 진행 통계 — stats.py 정적 파생 + 실시간 파생 병합 결과.

    단계별·행별 파생은 PipelineStageGroup·PipelineRow가 담으므로 중복 게재하지 않는다.
    """
    available: bool = False          # rows 부재·created_at 파싱 실패 시 False
    # 정적 파생 (캐시 대상)
    total_minutes: int = 0
    total_label: str = "—"
    work_minutes: int = 0
    work_label: str = "—"
    wait_minutes: int = 0
    wait_label: str = "—"
    wait_ratio: int = 0
    # 3계열 분해 (집계기준 16, R-16) — pm + worker + captain == total_minutes
    pm_minutes: int = 0
    pm_label: str = "—"
    worker_minutes: int = 0
    worker_label: str = "—"
    captain_minutes: int = 0
    captain_label: str = "—"
    worker_measured: bool = False    # 「워커 0분」과 「미측정」 구분 (필드 부재 = 미측정)
    worker_clamped_count: int = 0    # 기록 워커가 남은 몫을 초과해 상한 clamp된 행 수
    peak_stage: str = ""
    peak_stage_label: str = "—"
    gate_count: int = 0
    gate_recorded: bool = False      # 「게이트 0건」과 「미기록」 구분
    blocker_count: int = 0
    # 야간 보정 표면화 (집계기준 17, R-21) — FE 배지의 원천.
    # 같은 태스크가 799분으로도 425분으로도 보이면 혼란이므로 수치와 구간을 함께 싣는다.
    quiet_hours_applied: bool = False
    quiet_hours_label: str = ""      # `00:00~09:00` — 미적용이면 빈 문자열
    # 실시간 파생 (캐시 밖, now 주입)
    is_running: bool = False
    current_row_id: int | None = None
    current_stage: str | None = None
    current_item: str | None = None
    current_key: str | None = None
    current_series: str = ""
    current_elapsed_minutes: int | None = None
    current_elapsed_label: str = "—"


class ArtifactItem(BaseModel):
    """산출물 1건 — 파일명 기반 4유형 분류 (P-3)."""
    name: str
    type: str                        # pipeline | verification | log | other
    type_label: str                  # 파이프라인 | 검증 | 로그 | 기타


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
    # 103 additive
    stats: TaskStats | None = None
    artifact_items: list[ArtifactItem] = []
    # 사용자 호칭 표면화 — 화면 문구·범례의 호칭 원천 (하드코딩 금지)
    owner_term: str = ""


# ── Memory ────────────────────────────────────────────────────────────────────

class MemoryRowResponse(BaseModel):
    date: str = ""
    category: str = ""
    status: str = ""
    file: str = ""
    description: str = ""
    title: str = ""  # additive (078 F-009) — MEMORY.json memories[].title, FE 미사용


class HistoryRowResponse(BaseModel):
    date: str = ""
    task: str = ""
    stage: str = ""
    path: str = ""
    start: str | None = None
    end: str | None = None
    result: str = ""  # additive (078 F-009) — MEMORY.json history[].result, FE 미사용


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
