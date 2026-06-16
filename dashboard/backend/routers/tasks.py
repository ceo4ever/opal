"""
@header {
  "module": "routers.tasks",
  "layer": "router",
  "domain": "console",
  "description": "GET /api/tasks, /api/tasks/detail?project=&task_id=, /api/tasks/artifact?project=&task_id=&name= — 칸반 5컬럼 정규화(pending/in_progress/blocked/done/archive) + 산출물 뷰어. tasks/backup/ 하위 폴더 → archive 컬럼. state.json 없는 옛 형식 태스크는 산출물(DONE.md/PLAN.md 등)로 컬럼 추론. 완료·아카이브 최근순(task_id desc). 절대경로 식별자는 query param으로 전달(path segment 금지). 읽기 전용. _derive_current_stage: rows에서 도달 단계 파생(①in_progress→②마지막도달단계(done/na/skipped)→③전부pending이면첫행; pending 미시작 단계 제외). _group_pipeline_stages: rows를 stage 단위 PipelineStageGroup으로 그룹핑(total/done_count는 na/skipped 제외 active 기준). _aggregate_status: 단계 내 행 status 집계(na/skipped 제외→blocked우선→all_done→in_progress/혼재→pending; active없으면done).",
  "exports": [
    "GET /api/tasks",
    "GET /api/tasks/detail?project=&task_id=",
    "GET /api/tasks/artifact?project=&task_id=&name=",
    "COLUMN_MAP",
    "_derive_current_stage",
    "_aggregate_status",
    "_group_pipeline_stages"
  ],
  "depends": ["models", "scanner", "config", "cache", "adapters.state_adapter", "parsers.markdown_reader"]
}
"""
from __future__ import annotations

import datetime
import os
import re
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from dashboard.backend.cache import cache
from dashboard.backend.config import load_config
from dashboard.backend.models import (
    PipelineRow,
    PipelineStageGroup,
    TaskCardResponse,
    TaskDetailResponse,
)
from dashboard.backend.parsers.markdown_reader import read_markdown
from dashboard.backend.scanner import scan_projects

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


def _get_artifact_files(task_dir: str) -> list[str]:
    """task_dir 하위 .md 산출물 파일 목록 반환."""
    artifacts = []
    known = ["TASK.md", "PLAN.md", "DONE.md", "TEST-SCENARIO.md", "ANALYSIS.md", "WIREFRAME.md"]
    for name in known:
        if os.path.isfile(os.path.join(task_dir, name)):
            artifacts.append(name)
    return artifacts


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


def _group_pipeline_stages(rows: list[dict]) -> list[PipelineStageGroup]:
    """rows를 stage 단위로 그룹핑하여 PipelineStageGroup 배열 반환 (BE 단일 소스).

    - stage 등장 순서 보존 (원본 rows 순서 = 파이프라인 진행 순서)
    - 동일 stage의 연속/분산 행을 하나의 그룹으로 합침
    - done_count/total/status 집계 (D-2 규칙)
    - 빈 rows → [] 반환 (IndexError 없음)
    """
    if not rows:
        return []

    groups: list[tuple[str, list[dict]]] = []  # [(stage, [row, ...]), ...] 등장 순서
    index: dict[str, int] = {}                  # stage -> groups 내 위치

    for r in rows:
        st = r.get("stage", "")
        if st not in index:
            index[st] = len(groups)
            groups.append((st, []))
        groups[index[st]][1].append(r)

    result: list[PipelineStageGroup] = []
    for stage, grp_rows in groups:
        # na/skipped 제외한 active 행 기준 카운트 (표시 정합)
        active_rows = [r for r in grp_rows if r.get("status") not in ("na", "skipped")]
        done_count = sum(1 for r in active_rows if r.get("status") == "done")
        result.append(PipelineStageGroup(
            stage=stage,
            done_count=done_count,
            total=len(active_rows),
            status=_aggregate_status(grp_rows),
            rows=[
                PipelineRow(
                    row=r.get("row", i),
                    stage=r.get("stage", ""),
                    status=r.get("status", ""),
                    updated_at=r.get("updated_at", ""),
                )
                for i, r in enumerate(grp_rows)
            ],
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

    cache_key = f"task_detail:{project}:{task_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    state = _read_state(task_dir)
    if state is None:
        result = TaskDetailResponse(
            task_id=task_id,
            title=task_id,
            current_status="pending",
            artifacts=_get_artifact_files(task_dir),
        )
        cache.set(cache_key, result)
        return result

    rows = state.get("rows", [])
    pipeline = _group_pipeline_stages(rows)

    done_count = sum(1 for r in rows if r.get("status") == "done")
    total = len(rows) if rows else 1
    progress = int((done_count / total) * 100) if total > 0 else 0

    result = TaskDetailResponse(
        task_id=task_id,
        title=state.get("title", task_id),
        skill=state.get("skill", ""),
        mode=state.get("mode", ""),
        current_status=state.get("current_status", ""),
        current_stage=state.get("current_stage") or _derive_current_stage(rows),
        progress=progress,
        pipeline=pipeline,
        artifacts=_get_artifact_files(task_dir),
        updated_at=state.get("updated_at", ""),
    )
    cache.set(cache_key, result)
    return result


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
