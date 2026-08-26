"""
@header {
  "module": "routers.tasks",
  "layer": "router",
  "domain": "console",
  "description": "GET /api/tasks, /api/tasks/detail?project=&task_id=, /api/tasks/artifact?project=&task_id=&name= — 칸반 5컬럼 정규화(pending/in_progress/blocked/done/archive) + 산출물 뷰어. tasks/backup/ 하위 폴더 → archive 컬럼. state.json 없는 옛 형식 태스크는 산출물(DONE.md/PLAN.md 등)로 컬럼 추론. 완료·아카이브 최근순(task_id desc). 절대경로 식별자는 query param으로 전달(path segment 금지). 읽기 전용. _derive_current_stage: rows에서 도달 단계 파생(①in_progress→②마지막도달단계(done/na/skipped)→③전부pending이면첫행; pending 미시작 단계 제외). _group_pipeline_stages: rows를 stage 단위 PipelineStageGroup으로 그룹핑(total/done_count는 na/skipped 제외 active 기준) + stats.py 파생(행 소요·단계 2계열 + 3계열 pm/worker/captain) 결합. _aggregate_status: 단계 내 행 status 집계(na/skipped 제외→blocked우선→all_done→in_progress/혼재→pending; active없으면done). [T103] 상세 응답에 진행 통계 결합 — 행 매핑을 원천 키(row_id·timestamp)로 교정하고 사표 필드(row·updated_at)에 같은 값을 채운다(집계기준 15). 캐시(task_detail:{project}:{task_id})에는 **정적 파생만** 담고 실시간 파생(is_running·current_elapsed_*)은 캐시 밖에서 task_live_stats(now 주입)로 합성한다 — 캐시 저장 시 state.json을 source_path로 넘겨 mtime 무효화를 켠다. [T103 R-21] 야간 제외 구간(집계 기준 17)은 **라우터가** config.load_quiet_hours(project_path)로 읽어 task_static_stats·row_durations·task_live_stats에 인자로 주입한다 — stats.py는 설정을 읽지 않는다. 캐시 키는 `task_detail:{project}:{task_id}:{구간서명}`으로 설정 변경 시 자연히 갈린다(mtime 축은 state.json만 본다). 행 시각 표시 문자열(`time_label`)은 자체 슬라이싱이 아니라 stats.format_timestamp를 호출해 얻는다 — 표시 규칙은 stats.py 단일 소유다(P-7). _get_artifact_files는 6종 화이트리스트를 폐기하고 .md 전수를 유형 순(pipeline→verification→log→other)으로 열거하며, classify_artifact가 파일명 기반 4유형을 판정한다(P-3). artifact_count·artifacts[] **값** 증가는 P-4가 선언한 회귀 예외다. [호칭 하드코딩 제거] 행 라벨의 사용자 호칭은 config.load_owner_name()이 원천이다 — _OWNER_ROLE_LABELS는 역할명(PM·자동)만 갖고, _owner_label()이 owner == \"user\"일 때만 호칭을 붙인다. 라우터가 요청당 1회 읽어 _build_static_detail → _group_pipeline_stages → _to_pipeline_row로 주입하며 상세 응답 최상위 owner_term에도 같은 값을 싣는다(FE가 문구를 조립한다). owner_term은 캐시 키에 넣지 않는다 — 행 라벨은 캐시 TTL(30초)만큼 지연될 수 있고 TTL이 스스로 회복한다.",
  "exports": [
    "GET /api/tasks",
    "GET /api/tasks/detail?project=&task_id=",
    "GET /api/tasks/artifact?project=&task_id=&name=",
    "COLUMN_MAP",
    "_derive_current_stage",
    "_aggregate_status",
    "_group_pipeline_stages",
    "classify_artifact",
    "_get_artifact_files"
  ],
  "depends": ["models", "scanner", "config", "cache", "stats", "adapters.state_adapter", "parsers.markdown_reader"],
  "changelog": [
    "2026-08-26 호칭 하드코딩 제거: _OWNER_LABELS의 특정 호칭 리터럴 제거 → _OWNER_ROLE_LABELS(PM·자동) + _owner_label(owner, owner_term). owner_term을 라우터에서 1회 로드해 행에 주입 + 상세 응답에 additive 표면화",
    "2026-08-26 T103 R-21: 야간 제외 구간을 config.load_quiet_hours로 읽어 stats.py 4함수에 주입 + 캐시 키에 quiet_hours_token 서명 부착. stats.py는 설정을 읽지 않는다(TS-008 유지)",
    "2026-08-25 T103 R-19: 행 시각 표시 문자열 소유권을 stats.py로 이관 — `time_label`을 `timestamp[11:16]` 슬라이싱에서 `stats.format_timestamp`(`YY-MM-DD HH:mm:ss`) 호출로 교체. 날짜가 라벨에 실려 날짜 경계를 넘는 행이 역행처럼 읽히던 결함이 해소된다(P-7 단일 소유)",
    "2026-08-25 T103 R-20: _group_pipeline_stages가 단계 3계열 표시 문자열(pm_label·worker_label·captain_label)을 PipelineStageGroup에 결합 — 값은 stats.py 소유, 라우터는 전달만 한다",
    "2026-08-25 T103 R-16: _group_pipeline_stages가 stats.py 단계 3계열(pm/worker/captain + worker_measured)을 PipelineStageGroup에 결합 — 태스크 단위 3계열은 TaskStats(**merged) 경로로 자동 승계. TS-101~TS-105",
    "2026-08-25 T103 Step5: 상세 응답에 stats.py 정적·실시간 파생 결합 + _group_pipeline_stages 행 매핑 교정(row_id·timestamp) + 캐시 source_path 전달·정적 파생만 캐시 — F-002, TS-010~013·015·018",
    "2026-08-25 T103 Step6: _get_artifact_files 화이트리스트 폐기(.md 전수) + classify_artifact 4유형 분류 + artifact_items 응답 추가 — F-002, TS-014"
  ]
}
"""
from __future__ import annotations

import datetime
import os
import re
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from dashboard.backend.cache import cache
from dashboard.backend.config import load_config, load_owner_name, load_quiet_hours, quiet_hours_token
from dashboard.backend.models import (
    ArtifactItem,
    PipelineGate,
    PipelineRow,
    PipelineStageGroup,
    TaskCardResponse,
    TaskDetailResponse,
    TaskStats,
)
from dashboard.backend.parsers.markdown_reader import read_markdown
from dashboard.backend.scanner import scan_projects
from dashboard.backend.stats import (
    format_timestamp,
    row_durations,
    task_live_stats,
    task_static_stats,
)

router = APIRouter()

# 칸반 5컬럼 정규화 (PLAN §3.4.2 COLUMN_MAP — 단일 계약)
# archive 컬럼은 tasks/backup/ 스캔 전용 — COLUMN_MAP 직접 매핑 없음(별도 경로)
COLUMN_MAP: dict[str, Literal["pending", "in_progress", "blocked", "done", "archive"]] = {
    "in_progress": "in_progress",
    "blocked": "blocked",
    "additional_work": "in_progress",   # 추가작업 → 진행중에 합류
    "additional_work_done": "done",
    "done": "done",
    # 미착수(state 없음) → "pending" (default)
}

# task_id 앞 숫자 접두사 추출 (정렬 키 — NNN 또는 YYMMDD-NNN 형식 대응)
_TASK_ID_NUM_RE = re.compile(r"^(\d+)")


def _task_id_sort_key(task_id: str) -> int:
    """task_id 앞 숫자 추출 → 정수 정렬 키. 숫자 없으면 0."""
    m = _TASK_ID_NUM_RE.match(task_id)
    return int(m.group(1)) if m else 0


def _read_state(task_dir: str) -> dict | None:
    """task_dir/state.json 직접 읽기 (읽기 전용)."""
    state_path = os.path.join(task_dir, "state.json")
    if not os.path.isfile(state_path):
        return None
    try:
        import json
        with open(state_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _find_project_path(project_path: str) -> str | None:
    """절대경로로 프로젝트 존재 여부 확인 후 경로 반환 (query param 방식).

    path segment에 절대경로 사용 시 FastAPI 매칭 실패 → 이 함수는 절대경로를
    직접 검증하여 반환한다.
    """
    cfg = load_config()
    projects = scan_projects(cfg.scan_roots, cfg.scan_depth, cfg.exclude)
    for p in projects:
        if p.path == project_path:
            return p.path
    return None


# 산출물 4유형 분류 (T103 P-3) — 화이트리스트 폐기, .md 전수 노출 + 유형 부여
_ARTIFACT_PIPELINE = [
    "TASK.md", "ANALYSIS.md", "PLAN.md", "TEST-SCENARIO.md",
    "TEST.md", "DONE.md", "WIREFRAME.md",
]
_ARTIFACT_VERIFICATION_PREFIXES = [
    "SCENARIO-GATE-", "GC-", "L3-JUDGMENT", "RED-EVIDENCE", "CONTRACT-CROSSCHECK",
]
_ARTIFACT_LOG = ["STATE.md", "AGENTIC-LOG.md"]
_ARTIFACT_TYPE_ORDER = {"pipeline": 0, "verification": 1, "log": 2, "other": 3}
_ARTIFACT_TYPE_LABELS = {
    "pipeline": "파이프라인", "verification": "검증", "log": "로그", "other": "기타",
}


def classify_artifact(name: str) -> tuple[str, str]:
    """산출물 파일명 → (유형, 표시 라벨). 미해당은 전부 `other` 버킷이 흡수한다."""
    if name in _ARTIFACT_PIPELINE:
        artifact_type = "pipeline"
    elif any(name.startswith(p) for p in _ARTIFACT_VERIFICATION_PREFIXES):
        artifact_type = "verification"
    elif name in _ARTIFACT_LOG:
        artifact_type = "log"
    else:
        artifact_type = "other"
    return artifact_type, _ARTIFACT_TYPE_LABELS[artifact_type]


def _artifact_sort_key(name: str) -> tuple[int, int, str]:
    """정렬: 유형 순 → 유형 내 나열 순 → 파일명 오름차순."""
    artifact_type, _ = classify_artifact(name)
    if artifact_type == "pipeline":
        inner = _ARTIFACT_PIPELINE.index(name)
    elif artifact_type == "verification":
        inner = next(
            i for i, p in enumerate(_ARTIFACT_VERIFICATION_PREFIXES) if name.startswith(p)
        )
    elif artifact_type == "log":
        inner = _ARTIFACT_LOG.index(name)
    else:
        inner = 0
    return (_ARTIFACT_TYPE_ORDER[artifact_type], inner, name)


def _get_artifact_files(task_dir: str) -> list[str]:
    """task_dir 하위 `.md` 산출물 **전수** 목록 (유형 순 정렬). 시그니처 불변."""
    try:
        names = [
            e.name for e in os.scandir(task_dir)
            if e.is_file() and e.name.endswith(".md")
        ]
    except OSError:
        return []
    return sorted(names, key=_artifact_sort_key)


# state.json 없는 태스크의 컬럼 추론에 사용할 진행 산출물 파일 목록
_PROGRESS_ARTIFACTS = [
    "PLAN.md", "EXECUTE.md", "TEST-SCENARIO.md", "ANALYSIS.md",
    "WIREFRAME.md", "TODO.md",
]
# QA-*.md 패턴도 진행 산출물로 간주


def _infer_column_from_artifacts(task_dir: str) -> tuple[str, str, int, str]:
    """state.json 없는 태스크 폴더에서 산출물로 (column, current_stage, progress, updated_at) 추론.

    - DONE.md 존재 → ("done", "DONE", 100, mtime)
    - 진행 산출물(PLAN.md/EXECUTE.md/...) 존재 → ("in_progress", "진행", 50, mtime)
    - 그 외 → ("pending", "", 0, "")

    updated_at: 가장 최근 산출물 mtime을 KST(UTC+9) ISO 문자열로 반환. 없으면 "".
    """
    # DONE.md 확인
    done_path = os.path.join(task_dir, "DONE.md")
    if os.path.isfile(done_path):
        mtime = _file_mtime_kst(done_path)
        return ("done", "DONE", 100, mtime)

    # 진행 산출물 확인
    progress_mtime: float = 0.0
    found_progress = False
    for name in _PROGRESS_ARTIFACTS:
        fpath = os.path.join(task_dir, name)
        if os.path.isfile(fpath):
            found_progress = True
            try:
                mt = os.stat(fpath).st_mtime
                if mt > progress_mtime:
                    progress_mtime = mt
            except OSError:
                pass

    # QA-*.md 패턴 탐색
    try:
        for fname in os.listdir(task_dir):
            if fname.startswith("QA-") and fname.endswith(".md"):
                fpath = os.path.join(task_dir, fname)
                found_progress = True
                try:
                    mt = os.stat(fpath).st_mtime
                    if mt > progress_mtime:
                        progress_mtime = mt
                except OSError:
                    pass
    except OSError:
        pass

    if found_progress:
        updated_at = _mtime_to_kst_str(progress_mtime) if progress_mtime > 0 else ""
        return ("in_progress", "진행", 50, updated_at)

    return ("pending", "", 0, "")


def _file_mtime_kst(file_path: str) -> str:
    """파일 mtime을 KST(UTC+9) ISO 문자열로 반환. 실패 시 ""."""
    try:
        mt = os.stat(file_path).st_mtime
        return _mtime_to_kst_str(mt)
    except OSError:
        return ""


def _mtime_to_kst_str(mtime: float) -> str:
    """Unix timestamp를 KST(UTC+9) ISO 8601 문자열로 반환."""
    kst = datetime.timezone(datetime.timedelta(hours=9))
    dt = datetime.datetime.fromtimestamp(mtime, tz=kst)
    return dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")


def _derive_current_stage(rows: list[dict]) -> str:
    """rows에서 현재 진행 단계명 파생 (BE 단일 소스).

    규칙 (PM 확정, R2 파생 — 도달 단계 반환, pending 미시작 단계 제외):
      ① in_progress 행이 있으면 그 행의 stage
      ② 없으면 실제 도달한 마지막 단계
         (status가 done/na/skipped/in_progress 중 하나인 마지막 행의 stage)
      ③ 전부 pending이면 첫 행 stage
      - pending(미시작) 단계는 절대 current_stage로 반환하지 않는다.
      - rows 비어있으면 "" 반환
    """
    if not rows:
        return ""
    # ① 활성 진행
    for r in rows:
        if r.get("status") == "in_progress":
            return r.get("stage", "")
    # ② 실제 도달한 마지막 단계 (done/na/skipped/in_progress 중 마지막 행의 stage)
    reached = ""
    for r in rows:
        if r.get("status") in ("done", "na", "skipped", "in_progress"):
            reached = r.get("stage", "")
    if reached:
        return reached
    # ③ 전부 pending → 첫 행 stage
    return rows[0].get("stage", "")


def _aggregate_status(grp_rows: list[dict]) -> str:
    """단계 내 행들의 status를 집계하여 대표 status 반환 (D-2 집계 규칙).

    na/skipped는 "해당없음"으로 집계에서 제외 (active = status not in (na, skipped)).
    ① active 없으면(전부 해당없음) → "done"
    ② active 중 하나라도 blocked  → "blocked"   (blocked 우선)
    ③ active 중 하나라도 in_progress → "in_progress"
    ④ active 전부 done             → "done"
    ⑤ active 중 done+pending 혼재  → "in_progress"
    ⑥ active 전부 pending          → "pending"
    """
    active = [r for r in grp_rows if r.get("status") not in ("na", "skipped")]
    if not active:
        return "done"                          # ① 전부 해당없음 → 완료로 간주
    statuses = [r.get("status", "") for r in active]
    if any(s == "blocked" for s in statuses):
        return "blocked"                       # ②
    if any(s == "in_progress" for s in statuses):
        return "in_progress"                   # ③
    if all(s == "done" for s in statuses):
        return "done"                          # ④
    if any(s == "done" for s in statuses):
        return "in_progress"                   # ⑤ done+pending 혼재
    return "pending"                           # ⑥ 전부 pending


# `owner` 원천값 → 화면 라벨. `PM`·`auto`는 **역할명**이라 고정이고, `user`만
# 사용자 호칭이라 identity.md에서 읽어 붙인다 (특정 호칭 하드코딩 금지).
_OWNER_ROLE_LABELS = {"PM": "PM", "auto": "자동"}

_OWNER_USER = "user"


def _owner_label(owner: str, owner_term: str) -> str:
    """`owner` 원천값을 화면 라벨로. 미지의 값은 원천값 그대로 노출한다."""
    if owner == _OWNER_USER:
        return owner_term or load_owner_name()
    return _OWNER_ROLE_LABELS.get(owner, owner)


def _to_pipeline_row(row: dict, index: int, derived: dict | None, owner_term: str = "") -> PipelineRow:
    """원천 행 dict → PipelineRow. 사표 필드(`row`·`updated_at`)에 원천 값을 채운다.

    [MUST] 집계기준 15 — 원천 키는 `row_id`·`timestamp`이며, `row`·`updated_at`은
    deprecated 별칭으로 존치하되 같은 값을 담는다 (T103).
    """
    row_id = row.get("row_id", index + 1)
    timestamp = row.get("timestamp") or ""
    owner = row.get("owner") or ""
    gate = row.get("gate")
    derived = derived or {}
    return PipelineRow(
        row=row_id,
        stage=row.get("stage", ""),
        status=row.get("status", ""),
        updated_at=timestamp,
        row_id=row_id,
        key=row.get("key") or "",
        item=row.get("item") or "",
        timestamp=timestamp,
        time_label=format_timestamp(timestamp),
        owner=owner,
        owner_label=_owner_label(owner, owner_term),
        note=row.get("note"),
        gate=PipelineGate(**gate) if isinstance(gate, dict) else None,
        duration_minutes=derived.get("duration_minutes") or 0,
        duration_label=derived.get("duration_label", ""),
        series=derived.get("series", ""),
        is_max_gap=derived.get("is_max_gap", False),
    )


def _group_pipeline_stages(
    rows: list[dict],
    derived: list[dict] | None = None,
    stage_minutes: dict[str, dict] | None = None,
    owner_term: str = "",
) -> list[PipelineStageGroup]:
    """rows를 stage 단위로 그룹핑하여 PipelineStageGroup 배열 반환 (BE 단일 소스).

    - stage 등장 순서 보존 (원본 rows 순서 = 파이프라인 진행 순서)
    - 동일 stage의 연속/분산 행을 하나의 그룹으로 합침
    - done_count/total/status 집계 (D-2 규칙)
    - 빈 rows → [] 반환 (IndexError 없음)
    - derived/stage_minutes(stats.py 파생, T103)는 있으면 행·그룹에 결합한다
    - owner_term은 `owner == "user"` 행의 라벨로 쓸 사용자 호칭이다. 호출자가 주지
      않으면 여기서 1회 읽어 행마다 파일을 다시 열지 않는다.
    """
    if not rows:
        return []

    owner_term = owner_term or load_owner_name()
    derived = derived or []
    stage_minutes = stage_minutes or {}

    groups: list[tuple[str, list[PipelineRow]]] = []  # [(stage, [row, ...]), ...] 등장 순서
    raw: dict[str, list[dict]] = {}                    # stage -> 원천 행 (집계용)
    index: dict[str, int] = {}                         # stage -> groups 내 위치

    for i, r in enumerate(rows):
        st = r.get("stage", "")
        if st not in index:
            index[st] = len(groups)
            groups.append((st, []))
            raw[st] = []
        groups[index[st]][1].append(
            _to_pipeline_row(r, i, derived[i] if i < len(derived) else None, owner_term)
        )
        raw[st].append(r)

    result: list[PipelineStageGroup] = []
    for stage, grp_rows in groups:
        # na/skipped 제외한 active 행 기준 카운트 (표시 정합)
        active_rows = [r for r in raw[stage] if r.get("status") not in ("na", "skipped")]
        done_count = sum(1 for r in active_rows if r.get("status") == "done")
        minutes = stage_minutes.get(stage, {})
        result.append(PipelineStageGroup(
            stage=stage,
            done_count=done_count,
            total=len(active_rows),
            status=_aggregate_status(raw[stage]),
            rows=grp_rows,
            work_minutes=minutes.get("work_minutes", 0),
            wait_minutes=minutes.get("wait_minutes", 0),
            total_minutes=minutes.get("total_minutes", 0),
            total_label=minutes.get("total_label", ""),
            is_peak=minutes.get("is_peak", False),
            pm_minutes=minutes.get("pm_minutes", 0),
            worker_minutes=minutes.get("worker_minutes", 0),
            captain_minutes=minutes.get("captain_minutes", 0),
            # 3계열 표시 문자열 (R-20) — 단계 구획 호버 지표. stats.py가 소유한다 (P-7)
            pm_label=minutes.get("pm_label", "—"),
            worker_label=minutes.get("worker_label", "—"),
            captain_label=minutes.get("captain_label", "—"),
            worker_measured=minutes.get("worker_measured", False),
        ))
    return result


def _state_to_task_card(task_id: str, task_dir: str, state: dict | None) -> TaskCardResponse:
    """state dict → TaskCardResponse."""
    if state is None:
        column, current_stage, progress, updated_at = _infer_column_from_artifacts(task_dir)
        return TaskCardResponse(
            task_id=task_id,
            title=task_id,
            column=column,
            current_stage=current_stage,
            progress=progress,
            updated_at=updated_at,
            artifact_count=len(_get_artifact_files(task_dir)),
        )

    current_status = state.get("current_status", "")
    column = COLUMN_MAP.get(current_status, "pending")

    # 진행률 계산 (완료 rows / 전체 rows)
    rows = state.get("rows", [])
    done_count = sum(1 for r in rows if r.get("status") == "done")
    total = len(rows) if rows else 1
    progress = int((done_count / total) * 100) if total > 0 else 0

    return TaskCardResponse(
        task_id=task_id,
        title=state.get("title", task_id),
        skill=state.get("skill", ""),
        mode=state.get("mode", ""),
        column=column,
        current_stage=state.get("current_stage") or _derive_current_stage(rows),
        progress=progress,
        updated_at=state.get("updated_at", ""),
        artifact_count=len(_get_artifact_files(task_dir)),
    )


@router.get("/api/tasks", response_model=list[TaskCardResponse])
def list_tasks(project: str = Query(default="", description="프로젝트 절대경로 필터")) -> list[TaskCardResponse]:
    """태스크 목록 (칸반 카드). project 지정 시 해당 프로젝트만.

    project 파라미터는 절대경로 문자열 (query param 방식 — path segment 금지).
    """
    if project:
        project_path = _find_project_path(project)
        if project_path is None:
            return []
        project_paths = [project_path]
    else:
        cfg = load_config()
        all_projs = scan_projects(cfg.scan_roots, cfg.scan_depth, cfg.exclude)
        project_paths = [p.path for p in all_projs if p.is_opal]

    cache_key = f"tasks_list:{project}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    cards: list[TaskCardResponse] = []
    for proj_path in project_paths:
        tasks_dir = os.path.join(proj_path, "tasks")
        if not os.path.isdir(tasks_dir):
            continue
        try:
            for entry in os.scandir(tasks_dir):
                if not entry.is_dir():
                    continue
                # backup 디렉토리는 일반 태스크에서 제외 — 아카이브 컬럼으로 별도 처리
                if entry.name == "backup":
                    continue
                state = _read_state(entry.path)
                card = _state_to_task_card(entry.name, entry.path, state)
                cards.append(card)
        except OSError:
            pass

        # tasks/backup/ 하위 폴더 → archive 컬럼 카드
        backup_dir = os.path.join(tasks_dir, "backup")
        if os.path.isdir(backup_dir):
            try:
                for entry in os.scandir(backup_dir):
                    if not entry.is_dir():
                        continue
                    archive_card = TaskCardResponse(
                        task_id=entry.name,
                        title=entry.name,
                        column="archive",
                        current_stage="",
                        progress=0,
                        updated_at="",
                        artifact_count=len(_get_artifact_files(entry.path)),
                    )
                    cards.append(archive_card)
            except OSError:
                pass

    # 완료·아카이브 컬럼: task_id 내림차순(최신이 맨 위)
    # 대기·진행중·블로킹: task_id 오름차순(일관 정렬)
    def _sort_key(card: TaskCardResponse):
        num = _task_id_sort_key(card.task_id)
        if card.column in ("done", "archive"):
            return (0, -num)   # 오름차순 정렬 시 내림차순 효과
        return (1, num)

    cards.sort(key=_sort_key)

    cache.set(cache_key, cards)
    return cards


@router.get("/api/tasks/detail", response_model=TaskDetailResponse)
def get_task_detail(
    project: str = Query(..., description="프로젝트 절대경로 (URL-encoded)"),
    task_id: str = Query(..., description="태스크 ID"),
) -> TaskDetailResponse:
    """태스크 상세 — 파이프라인 단계 현황 + 산출물 목록.

    절대경로는 query param으로 전달한다 — path segment 방식 금지.
    """
    project_path = _find_project_path(project)
    if project_path is None:
        raise HTTPException(status_code=404, detail=f"Project not found: {project}")

    task_dir = os.path.join(project_path, "tasks", task_id)
    if not os.path.isdir(task_dir):
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    # 캐시 조회보다 state 읽기가 앞선다 — 실시간 파생은 캐시 밖에서 조립하므로
    # 캐시 히트 시에도 state가 필요하다 (T103 PLAN §3.2.2)
    state = _read_state(task_dir)

    # 야간 제외 구간(집계 기준 17)은 **라우터가 읽어 stats.py에 주입**한다 —
    # stats.py는 파일 I/O를 하지 않는다(TS-008). 프로젝트 로컬 설정이 전역을 덮는다.
    quiet_hours = load_quiet_hours(project_path)

    # 사용자 호칭도 **라우터가 읽는다** — 요청당 1회 읽어 행마다 파일을 다시 열지
    # 않는다. identity.md는 전역 1개라 프로젝트별로 갈리지 않는다.
    owner_term = load_owner_name()

    # 캐시 키에 구간 서명을 실어 설정 변경이 곧바로 갈리게 한다 — mtime 축은
    # state.json만 보므로 설정 변경을 감지하지 못한다.
    cache_key = f"task_detail:{project}:{task_id}:{quiet_hours_token(quiet_hours)}"
    static_payload = cache.get(cache_key)
    if static_payload is None:
        static_payload = _build_static_detail(
            task_id, task_dir, state, quiet_hours, owner_term
        )
        cache.set(
            cache_key,
            static_payload,
            source_path=os.path.join(task_dir, "state.json") if state is not None else None,
        )

    return _compose_task_detail(static_payload, state, quiet_hours, owner_term)


def _build_static_detail(
    task_id: str,
    task_dir: str,
    state: dict | None,
    quiet_hours: tuple[int, int] | None = None,
    owner_term: str = "",
) -> dict:
    """상세 응답의 **정적 파생만** 담은 캐시 payload.

    [MUST] 실시간 파생(`is_running`·`current_elapsed_*`)은 여기 담지 않는다 —
    캐시에 고착되면 진행 중 태스크의 경과가 최대 TTL만큼 정지한다 (H-6).
    """
    artifacts = _get_artifact_files(task_dir)
    artifact_items = [
        {"name": name, "type": t, "type_label": label}
        for name, (t, label) in ((n, classify_artifact(n)) for n in artifacts)
    ]

    if state is None:
        return {
            "task_id": task_id,
            "title": task_id,
            "skill": "",
            "mode": "",
            "current_status": "pending",
            "current_stage": "",
            "progress": 0,
            "pipeline": [],
            "artifacts": artifacts,
            "artifact_items": artifact_items,
            "updated_at": "",
            "static_stats": None,
        }

    rows = state.get("rows", [])
    static_stats = task_static_stats(state, quiet_hours)
    stage_minutes = {g["stage"]: g for g in static_stats["stages"]}
    pipeline = _group_pipeline_stages(
        rows, row_durations(state, quiet_hours), stage_minutes, owner_term
    )

    done_count = sum(1 for r in rows if r.get("status") == "done")
    total = len(rows) if rows else 1
    progress = int((done_count / total) * 100) if total > 0 else 0

    return {
        "task_id": task_id,
        "title": state.get("title", task_id),
        "skill": state.get("skill", ""),
        "mode": state.get("mode", ""),
        "current_status": state.get("current_status", ""),
        "current_stage": state.get("current_stage") or _derive_current_stage(rows),
        "progress": progress,
        "pipeline": pipeline,
        "artifacts": artifacts,
        "artifact_items": artifact_items,
        "updated_at": state.get("updated_at", ""),
        "static_stats": static_stats,
    }


def _compose_task_detail(
    static_payload: dict,
    state: dict | None,
    quiet_hours: tuple[int, int] | None = None,
    owner_term: str = "",
) -> TaskDetailResponse:
    """정적 payload(캐시 대상) + 실시간 파생(캐시 밖)을 합성한 응답.

    `owner_term`은 화면 문구·범례가 쓸 사용자 호칭이며 **캐시 밖에서** 매 응답에
    붙는다. 행 라벨(`owner_label`)은 정적 payload 안이라 호칭 변경이 캐시 TTL(30초)
    만큼 늦게 반영될 수 있다 — 캐시 키를 늘리지 않는 대신 TTL이 스스로 회복한다.
    """
    payload = {k: v for k, v in static_payload.items() if k != "static_stats"}
    payload["artifact_items"] = [ArtifactItem(**item) for item in payload["artifact_items"]]
    static_stats = static_payload["static_stats"]

    if static_stats is None or state is None:
        stats = TaskStats()   # available=False — 결측 태스크도 200으로 응답한다
    else:
        merged = {k: v for k, v in static_stats.items() if k not in ("stages", "rows")}
        merged.update(task_live_stats(state, now=datetime.datetime.now(), quiet_hours=quiet_hours))
        stats = TaskStats(**merged)

    return TaskDetailResponse(**payload, stats=stats, owner_term=owner_term or load_owner_name())


@router.get("/api/tasks/artifact")
def get_task_artifact(
    project: str = Query(..., description="프로젝트 절대경로 (URL-encoded)"),
    task_id: str = Query(..., description="태스크 ID"),
    name: str = Query(default="TASK.md", description="산출물 파일명"),
) -> dict:
    """산출물 마크다운 원문 반환.

    절대경로는 query param으로 전달한다 — path segment 방식 금지.
    """
    project_path = _find_project_path(project)
    if project_path is None:
        raise HTTPException(status_code=404, detail=f"Project not found: {project}")

    task_dir = os.path.join(project_path, "tasks", task_id)
    if not os.path.isdir(task_dir):
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    # 보안: path traversal 방지
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(status_code=400, detail="Invalid artifact name")

    artifact_path = os.path.join(task_dir, name)
    content = read_markdown(artifact_path)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Artifact not found: {name}")

    return {"name": name, "content": content, "task_id": task_id}
