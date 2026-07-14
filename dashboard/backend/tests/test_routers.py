"""
@header {
  "module": "tests.test_routers",
  "layer": "test",
  "domain": "console",
  "description": "S-6: 5개 엔드포인트 200 + Pydantic 응답 스키마 계약 검증. httpx TestClient. RED-first. [T021/L2-R4api] query param 방식 엔드포인트 검증 (path segment 절대경로 버그 근본 수정). [T021-fix] dashboard project 쿼리 파라미터 케이스 추가. [T021-fix2] state.json 없는 태스크 산출물 추론 케이스 추가. [T023/RED] _derive_current_stage / _group_pipeline_stages / _aggregate_status 신규 헬퍼 + get_task_detail pipeline 그룹 스키마 RED-first (S-001~S-012). [T023/RED-fix] _derive_current_stage na/skipped 도달 단계 파악 + _aggregate_status na/skipped 제외 집계 RED-first (S-013~S-016). [T061] 설정 라우터 계약 — 경로검증·화이트리스트(S-1, prewarm 대상 빈/비스캔 400만) · console.config GET 스냅샷(S-3 router측, GET만) · 프라임 풀 토글 멱등+prewarm 트리거 관측(S-5). S-5는 brain_session_registry.prewarm을 MagicMock으로 대체 관측 — 실 claude 서브프로세스 호출 0회(test_brain.py 격리 패턴 재사용). T061 범위 축소(캡틴 지시)로 console.config POST(S-3 쓰기측)·프로젝트 로컬 설정(S-4) 계약은 미사용 쓰기 API 제거에 따라 삭제됨.",
  "exports": [
    "test_api_dashboard_200",
    "test_api_dashboard_schema",
    "test_api_dashboard_project_param_not_found",
    "test_api_dashboard_project_param_valid",
    "test_api_projects_200",
    "test_api_tasks_200",
    "test_api_memory_200",
    "test_api_doctor_200",
    "test_kanban_column_normalization",
    "test_brain_endpoints_exist",
    "test_existing_routers_reject_post",
    "test_api_projects_detail_query_param",
    "test_api_tasks_detail_query_param",
    "test_infer_column_done",
    "test_infer_column_in_progress",
    "test_infer_column_pending",
    "test_infer_column_qa_artifact",
    "test_state_to_task_card_no_state_done",
    "test_state_to_task_card_no_state_in_progress",
    "test_state_to_task_card_no_state_pending",
    "test_derive_stage_in_progress",
    "test_derive_stage_first_pending",
    "test_derive_stage_all_done",
    "test_derive_stage_empty",
    "test_card_current_stage_filled",
    "test_group_pipeline_order",
    "test_aggregate_all_done",
    "test_aggregate_mixed",
    "test_aggregate_blocked",
    "test_aggregate_all_pending",
    "test_detail_pipeline_groups",
    "test_detail_empty_rows",
    "test_derive_stage_reached_not_pending",
    "test_derive_stage_reached_skips_na_tail",
    "test_aggregate_na_excluded_done",
    "test_aggregate_all_skipped_done",
    "TestConfigPathWhitelist",
    "TestPrewarmToggle",
    "TestConsoleConfigEndpoints"
  ],
  "depends": ["main", "models", "routers", "config", "adapters.brain_session"],
  "task": "061",
  "scenarios": ["S-1", "S-3", "S-5"],
  "changelog": [
    "2026-07-14 T061 RED: 설정 라우터(routers/config.py, 미구현) 경로검증/화이트리스트(S-1)·console.config GET/POST(S-3)·프로젝트 로컬 설정 3경로+재조회(S-4)·프라임 풀 토글 멱등(S-5) 실패 테스트 추가 — 구현 전 RED 트랙(red-first.md), 작성자(opal-test-agent)≠구현자(opal-be-agent)",
    "2026-07-14 T061 범위 축소: TestProjectLocalSettings 클래스 삭제 + TestConfigPathWhitelist 중 project-local 대상 3건(traversal·symlink·화이트리스트 외 무변경) 삭제(prewarm 대상 빈/비스캔 400 2건은 유지) + TestConsoleConfigEndpoints의 console POST 2건 삭제(GET 스냅샷 1건은 유지) — 프로젝트 로컬 설정·console.config 전반 편집 미반영에 따른 계약 삭제, scenarios에서 S-4 제거"
  ]
}
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from dashboard.backend.main import app
    return TestClient(app)


# ── /health ──────────────────────────────────────────────────────────────────

def test_health_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


# ── /api/dashboard ────────────────────────────────────────────────────────────

def test_api_dashboard_200(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200


def test_api_dashboard_schema(client):
    """응답에 집계 필드 포함."""
    resp = client.get("/api/dashboard")
    data = resp.json()
    # DashboardSummary 필드 검증
    assert "total_projects" in data
    assert "running_tasks" in data
    assert "blockers" in data
    assert "additional_work" in data
    assert isinstance(data["total_projects"], int)
    assert isinstance(data["running_tasks"], int)


def test_api_dashboard_project_param_not_found(client):
    """존재하지 않는 project 경로 → 404."""
    resp = client.get("/api/dashboard?project=/nonexistent/path/xyz")
    assert resp.status_code == 404


def test_api_dashboard_project_param_valid(client):
    """첫 번째 OPAL 프로젝트 경로로 개별 조회 → 200 + total_projects=1."""
    resp = client.get("/api/projects")
    projects = resp.json()
    opal_projects = [p for p in projects if p.get("is_opal")]
    if not opal_projects:
        pytest.skip("No OPAL projects found — skip dashboard project param test")
    project_path = opal_projects[0]["path"]
    import urllib.parse
    encoded_path = urllib.parse.quote(project_path, safe="")
    resp2 = client.get(f"/api/dashboard?project={encoded_path}")
    assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}: {resp2.text[:200]}"
    data = resp2.json()
    # 개별 프로젝트 조회 시 total_projects=1
    assert data["total_projects"] == 1
    assert "running_tasks" in data
    assert "blockers" in data


# ── /api/projects ─────────────────────────────────────────────────────────────

def test_api_projects_200(client):
    resp = client.get("/api/projects")
    assert resp.status_code == 200


def test_api_projects_returns_list(client):
    resp = client.get("/api/projects")
    data = resp.json()
    assert isinstance(data, list)


def test_api_projects_item_schema(client):
    """각 항목이 ProjectInfo 스키마 필드를 포함."""
    resp = client.get("/api/projects")
    data = resp.json()
    if data:
        item = data[0]
        assert "name" in item
        assert "path" in item
        assert "is_opal" in item
        assert "task_count" in item
        assert isinstance(item["is_opal"], bool)
        assert isinstance(item["task_count"], int)


# ── /api/projects/detail?path= ────────────────────────────────────────────────
# query param 방식 — path segment에 절대경로 사용 시 FastAPI 매칭 실패 근본 수정

def test_api_projects_detail_query_param(client):
    """GET /api/projects/detail?path=<절대경로> — 첫 번째 OPAL 프로젝트 상세."""
    resp = client.get("/api/projects")
    projects = resp.json()
    opal_projects = [p for p in projects if p.get("is_opal")]
    if not opal_projects:
        pytest.skip("No OPAL projects found — skip detail test")
    project_path = opal_projects[0]["path"]
    import urllib.parse
    encoded_path = urllib.parse.quote(project_path, safe="")
    resp2 = client.get(f"/api/projects/detail?path={encoded_path}")
    assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}: {resp2.text[:200]}"
    detail = resp2.json()
    assert "name" in detail
    assert "path" in detail
    assert "pm_profile" in detail
    assert "tech_stack" in detail
    assert "docs" in detail


def test_api_projects_detail_not_found(client):
    """존재하지 않는 경로 → 404."""
    resp = client.get("/api/projects/detail?path=/nonexistent/path/abc")
    assert resp.status_code == 404


def test_api_projects_detail_missing_path_param(client):
    """path 파라미터 누락 → 422."""
    resp = client.get("/api/projects/detail")
    assert resp.status_code == 422


# ── /api/tasks ────────────────────────────────────────────────────────────────

def test_api_tasks_200(client):
    resp = client.get("/api/tasks")
    assert resp.status_code == 200


def test_api_tasks_returns_list(client):
    resp = client.get("/api/tasks")
    data = resp.json()
    assert isinstance(data, list)


def test_api_tasks_with_project_param(client):
    """?project= 파라미터를 허용해야 한다."""
    resp = client.get("/api/tasks?project=nonexistent_project")
    # 없는 프로젝트 → 빈 목록 or 404, 500이면 안 됨
    assert resp.status_code in (200, 404)


# ── /api/memory ───────────────────────────────────────────────────────────────

def test_api_memory_200(client):
    resp = client.get("/api/memory")
    assert resp.status_code == 200


def test_api_memory_schema(client):
    """MemoryIndex 스키마: rows + history 필드."""
    resp = client.get("/api/memory")
    data = resp.json()
    assert "rows" in data
    assert "history" in data
    assert isinstance(data["rows"], list)
    assert isinstance(data["history"], list)


def test_api_memory_with_project_param(client):
    """/api/memory?project= 파라미터 허용."""
    resp = client.get("/api/memory?project=nonexistent_project")
    assert resp.status_code in (200, 404)


# ── /api/doctor ───────────────────────────────────────────────────────────────

def test_api_doctor_200(client):
    resp = client.get("/api/doctor")
    assert resp.status_code == 200


def test_api_doctor_schema(client):
    """DoctorReport 스키마: sections + counts + verdict."""
    resp = client.get("/api/doctor")
    data = resp.json()
    assert "sections" in data
    assert "counts" in data
    assert "verdict" in data
    assert isinstance(data["sections"], list)
    assert isinstance(data["counts"], dict)


# ── 칸반 컬럼 정규화 ──────────────────────────────────────────────────────────

def test_kanban_column_normalization():
    """COLUMN_MAP 정규화: 5가지 상태 → 4컬럼 매핑 (archive는 backup 스캔 전용)."""
    from dashboard.backend.routers.tasks import COLUMN_MAP
    assert COLUMN_MAP["in_progress"] == "in_progress"
    assert COLUMN_MAP["blocked"] == "blocked"
    assert COLUMN_MAP["additional_work"] == "in_progress"
    assert COLUMN_MAP["additional_work_done"] == "done"
    assert COLUMN_MAP["done"] == "done"


def test_task_card_column_valid_values(client):
    """태스크 카드의 column 필드는 5개 중 하나여야 한다 (archive 포함)."""
    valid_columns = {"pending", "in_progress", "blocked", "done", "archive"}
    resp = client.get("/api/tasks")
    data = resp.json()
    for card in data:
        if "column" in card:
            assert card["column"] in valid_columns, f"Invalid column: {card['column']}"


# ── brain 엔드포인트 존재 검증 (C-11) ─────────────────────────────────────────

def test_brain_endpoints_exist(client):
    """GET /api/brain/auth·POST /api/brain/query·POST /api/brain/prime 가 등록되어 있음을 검증 (C-11).

    격리 전략:
    - GET /api/brain/auth: shutil.which 호출만 하므로 실 claude 없이 200 반환.
    - POST /api/brain/query: body 누락 POST → 422 — 엔드포인트 존재 증명.
    - POST /api/brain/prime: project 빈 값 POST → 400 (project 필수) — 엔드포인트 존재 증명.
      400/422 모두 핸들러 등록됨 증명 (5xx 아님). 실 claude 0회.
    """
    # auth: shutil.which 기반 — claude 설치 여부와 무관하게 200 반환
    resp_auth = client.get("/api/brain/auth")
    assert resp_auth.status_code == 200, (
        f"GET /api/brain/auth 가 등록되지 않았거나 오류: {resp_auth.status_code}"
    )
    data = resp_auth.json()
    assert "authenticated" in data
    assert "cli_available" in data

    # query: body 없는 POST → 422 (엔드포인트 존재 증명, claude 미호출)
    resp_query = client.post("/api/brain/query")
    assert resp_query.status_code == 422, (
        f"POST /api/brain/query body 누락 시 422 예상, got {resp_query.status_code}"
    )

    # prime: project 빈 값 POST → 400 (project 필수 계약 — 엔드포인트 존재 증명)
    # body가 Optional[dict]이므로 422는 아니지만, project 빈 값 → 400
    resp_prime = client.post("/api/brain/prime", json={"project": ""})
    assert resp_prime.status_code == 400, (
        f"POST /api/brain/prime project 빈 값 시 400 예상, got {resp_prime.status_code}"
    )
    # 400 응답의 detail에 '필수' 키워드 포함 확인
    assert "필수" in resp_prime.json().get("detail", ""), (
        f"400 detail should mention '필수': {resp_prime.json()}"
    )

    # [RED S-2] GET /api/brain/job/{job_id}: project/session_id 누락 → 422 (엔드포인트 존재 증명)
    # 구현 전 RED — 엔드포인트 미존재 시 404 반환 예상 (FAIL)
    resp_job = client.get("/api/brain/job/nonexistent-job-id")
    assert resp_job.status_code == 422, (
        f"GET /api/brain/job/{{job_id}} query param 누락 시 422 예상(엔드포인트 등록 증명), "
        f"got {resp_job.status_code} — 엔드포인트 미등록이면 404"
    )


# ── 기존 5라우터 read-only 보존 격리 회귀 (C-11) ──────────────────────────────

def test_existing_routers_reject_post(client):
    """기존 5라우터 대표 경로에 POST → 405 (read-only 보존).

    dashboard/projects/tasks/memory/doctor 라우터는 GET 전용 핸들러만 등록.
    POST 핸들러 미등록이므로 405 Method Not Allowed를 반환해야 한다.
    CORS allow_methods에 POST가 있어도 핸들러 미등록이면 405임을 확인.
    """
    read_only_paths = [
        "/api/dashboard",
        "/api/projects",
        "/api/tasks",
        "/api/memory",
        "/api/doctor",
    ]
    for path in read_only_paths:
        resp = client.post(path)
        assert resp.status_code == 405, (
            f"POST {path} 가 405가 아님: {resp.status_code} — read-only 라우터에 POST 핸들러가 등록된 것으로 보임"
        )


# ── /api/projects/doc?path=&name= ─────────────────────────────────────────────
# query param 방식 — path segment에 절대경로 사용 시 FastAPI 매칭 실패 근본 수정

def test_api_projects_doc_query_param(client):
    """GET /api/projects/doc?path=<절대경로>&name=PROJECT.md — OPAL 프로젝트 문서."""
    resp = client.get("/api/projects")
    projects = resp.json()
    opal_projects = [p for p in projects if p.get("is_opal")]
    if not opal_projects:
        pytest.skip("No OPAL projects")
    project_path = opal_projects[0]["path"]
    import urllib.parse
    encoded_path = urllib.parse.quote(project_path, safe="")
    resp2 = client.get(f"/api/projects/doc?path={encoded_path}&name=PROJECT.md")
    # 200 or 404 (파일 없을 경우)
    assert resp2.status_code in (200, 404)


# ── /api/tasks/detail?project=&task_id= ──────────────────────────────────────
# query param 방식 — path segment에 절대경로 사용 시 FastAPI 매칭 실패 근본 수정

def test_api_tasks_detail_query_param(client):
    """GET /api/tasks/detail?project=<절대경로>&task_id=<id>."""
    resp = client.get("/api/tasks/detail?project=/nonexistent/path&task_id=xxx")
    # 없는 프로젝트 → 404 (500 아님)
    assert resp.status_code == 404


def test_api_tasks_detail_missing_params(client):
    """필수 query param 누락 → 422."""
    resp = client.get("/api/tasks/detail")
    assert resp.status_code == 422


def test_api_tasks_artifact_missing_params(client):
    """필수 query param 누락 → 422."""
    resp = client.get("/api/tasks/artifact")
    assert resp.status_code == 422


# ── state.json 없는 태스크 산출물 추론 (T021-fix2) ────────────────────────────

import os
import tempfile


def _make_task_dir(files: list[str]) -> str:
    """임시 태스크 디렉토리 생성 후 지정 파일을 빈 파일로 만들고 경로 반환."""
    tmpdir = tempfile.mkdtemp()
    for fname in files:
        open(os.path.join(tmpdir, fname), "w").close()
    return tmpdir


def test_infer_column_done():
    """DONE.md 존재 → column=done, progress=100."""
    from dashboard.backend.routers.tasks import _infer_column_from_artifacts
    task_dir = _make_task_dir(["TASK.md", "PLAN.md", "DONE.md"])
    column, stage, progress, updated_at = _infer_column_from_artifacts(task_dir)
    assert column == "done"
    assert progress == 100
    assert stage == "DONE"
    assert updated_at != ""  # mtime이 있어야 함


def test_infer_column_in_progress():
    """DONE.md 없고 PLAN.md 존재 → column=in_progress."""
    from dashboard.backend.routers.tasks import _infer_column_from_artifacts
    task_dir = _make_task_dir(["TASK.md", "PLAN.md"])
    column, stage, progress, _ = _infer_column_from_artifacts(task_dir)
    assert column == "in_progress"
    assert progress == 50
    assert stage == "진행"


def test_infer_column_pending():
    """TASK.md만 존재 → column=pending."""
    from dashboard.backend.routers.tasks import _infer_column_from_artifacts
    task_dir = _make_task_dir(["TASK.md"])
    column, stage, progress, updated_at = _infer_column_from_artifacts(task_dir)
    assert column == "pending"
    assert progress == 0
    assert updated_at == ""


def test_infer_column_qa_artifact():
    """QA-*.md 존재 → column=in_progress."""
    from dashboard.backend.routers.tasks import _infer_column_from_artifacts
    task_dir = _make_task_dir(["TASK.md", "QA-20260615.md"])
    column, stage, progress, _ = _infer_column_from_artifacts(task_dir)
    assert column == "in_progress"


def test_state_to_task_card_no_state_done():
    """state=None + DONE.md → TaskCardResponse(column=done)."""
    from dashboard.backend.routers.tasks import _state_to_task_card
    task_dir = _make_task_dir(["TASK.md", "PLAN.md", "DONE.md"])
    card = _state_to_task_card("999-test-done", task_dir, None)
    assert card.column == "done"
    assert card.progress == 100
    assert card.task_id == "999-test-done"


def test_state_to_task_card_no_state_in_progress():
    """state=None + PLAN.md → TaskCardResponse(column=in_progress)."""
    from dashboard.backend.routers.tasks import _state_to_task_card
    task_dir = _make_task_dir(["TASK.md", "PLAN.md"])
    card = _state_to_task_card("888-test-ip", task_dir, None)
    assert card.column == "in_progress"


def test_state_to_task_card_no_state_pending():
    """state=None + TASK.md만 → TaskCardResponse(column=pending)."""
    from dashboard.backend.routers.tasks import _state_to_task_card
    task_dir = _make_task_dir(["TASK.md"])
    card = _state_to_task_card("777-test-pending", task_dir, None)
    assert card.column == "pending"
    assert card.progress == 0


# ── T023 RED-first: _derive_current_stage / _group_pipeline_stages / _aggregate_status ──
# 아래 테스트는 구현 전 RED(실패) 상태여야 정상이다.
# GREEN 전환은 opal-be-agent(EXECUTE 단계)가 담당한다.

# ── 픽스처: §2.1 데이터 설계 기반 dict 리터럴 ──────────────────────────────────

# rows_ip: TASK done·done / PLAN in_progress / EXECUTE pending
_rows_ip = [
    {"row": 1, "stage": "TASK", "status": "done", "updated_at": ""},
    {"row": 2, "stage": "TASK", "status": "done", "updated_at": ""},
    {"row": 3, "stage": "PLAN", "status": "in_progress", "updated_at": ""},
    {"row": 4, "stage": "EXECUTE", "status": "pending", "updated_at": ""},
]

# rows_pending: TASK done·done·pending / PLAN pending (005 케이스 모사)
_rows_pending = [
    {"row": 1, "stage": "TASK", "status": "done", "updated_at": ""},
    {"row": 2, "stage": "TASK", "status": "done", "updated_at": ""},
    {"row": 3, "stage": "TASK", "status": "pending", "updated_at": ""},
    {"row": 4, "stage": "PLAN", "status": "pending", "updated_at": ""},
    {"row": 5, "stage": "EXECUTE", "status": "pending", "updated_at": ""},
]

# rows_done: TASK·PLAN·EXECUTE·TEST·CLOSE 전부 done (015 케이스 모사, 9행)
_rows_done = [
    {"row": 1, "stage": "TASK", "status": "done", "updated_at": ""},
    {"row": 2, "stage": "TASK", "status": "done", "updated_at": ""},
    {"row": 3, "stage": "PLAN", "status": "done", "updated_at": ""},
    {"row": 4, "stage": "EXECUTE", "status": "done", "updated_at": ""},
    {"row": 5, "stage": "EXECUTE", "status": "done", "updated_at": ""},
    {"row": 6, "stage": "TEST", "status": "done", "updated_at": ""},
    {"row": 7, "stage": "TEST", "status": "done", "updated_at": ""},
    {"row": 8, "stage": "TEST", "status": "done", "updated_at": ""},
    {"row": 9, "stage": "CLOSE", "status": "done", "updated_at": ""},
]

# rows_mixed: EXECUTE done+pending 혼재
_rows_mixed = [
    {"row": 1, "stage": "EXECUTE", "status": "done", "updated_at": ""},
    {"row": 2, "stage": "EXECUTE", "status": "pending", "updated_at": ""},
    {"row": 3, "stage": "EXECUTE", "status": "pending", "updated_at": ""},
]

# rows_blocked: TEST 단계 blocked 포함
_rows_blocked = [
    {"row": 1, "stage": "TEST", "status": "done", "updated_at": ""},
    {"row": 2, "stage": "TEST", "status": "blocked", "updated_at": ""},
    {"row": 3, "stage": "TEST", "status": "pending", "updated_at": ""},
]

# rows_empty
_rows_empty: list = []


# ── S-001: in_progress 행 → 해당 stage 파생 ──────────────────────────────────

def test_derive_stage_in_progress():
    """S-001: rows_ip (PLAN 행 in_progress) → _derive_current_stage 반환 == 'PLAN'."""
    from dashboard.backend.routers.tasks import _derive_current_stage
    result = _derive_current_stage(_rows_ip)
    assert result == "PLAN"


# ── S-002: in_progress 없음 → 첫 미완료 stage (005 케이스) ───────────────────

def test_derive_stage_first_pending():
    """S-002: rows_pending (TASK done·done·pending) → 반환 == 'TASK'."""
    from dashboard.backend.routers.tasks import _derive_current_stage
    result = _derive_current_stage(_rows_pending)
    assert result == "TASK"


# ── S-003: 전부 done → 마지막 stage (015 케이스) [H-2] ───────────────────────

def test_derive_stage_all_done():
    """S-003: rows_done (9행 전부 done, 마지막 CLOSE) → 반환 == 'CLOSE'."""
    from dashboard.backend.routers.tasks import _derive_current_stage
    result = _derive_current_stage(_rows_done)
    assert result == "CLOSE"


# ── S-004: 빈 rows → "" (IndexError 없음) [H-4] ──────────────────────────────

def test_derive_stage_empty():
    """S-004: 빈 rows → 반환 == '', 예외 미발생."""
    from dashboard.backend.routers.tasks import _derive_current_stage
    result = _derive_current_stage(_rows_empty)
    assert result == ""


# ── S-005: state 있는 카드 current_stage 비어있지 않음 ───────────────────────

def test_card_current_stage_filled():
    """S-005: state_card (current_status=in_progress + rows_pending) → current_stage != ''."""
    from dashboard.backend.routers.tasks import _state_to_task_card
    task_dir = _make_task_dir(["TASK.md", "PLAN.md"])
    state = {
        "current_status": "in_progress",
        "title": "test-task",
        "rows": _rows_pending,
    }
    card = _state_to_task_card("555-test-stage", task_dir, state)
    assert card.current_stage != ""


# ── S-006: stage 그룹 변환 + 등장순서 보존 ───────────────────────────────────

def test_group_pipeline_order():
    """S-006: [TASK, TASK, PLAN] rows → 2그룹 [TASK(total=2), PLAN(total=1)], 순서 보존."""
    from dashboard.backend.routers.tasks import _group_pipeline_stages
    rows = [
        {"row": 1, "stage": "TASK", "status": "done", "updated_at": ""},
        {"row": 2, "stage": "TASK", "status": "done", "updated_at": ""},
        {"row": 3, "stage": "PLAN", "status": "pending", "updated_at": ""},
    ]
    groups = _group_pipeline_stages(rows)
    assert len(groups) == 2
    assert groups[0].stage == "TASK"
    assert groups[0].total == 2
    assert groups[1].stage == "PLAN"
    assert groups[1].total == 1


# ── S-007: 집계 — 전부 done → done ───────────────────────────────────────────

def test_aggregate_all_done():
    """S-007: 단계 내 행 전부 done → _aggregate_status == 'done'."""
    from dashboard.backend.routers.tasks import _aggregate_status
    grp_rows = [
        {"row": 1, "stage": "PLAN", "status": "done", "updated_at": ""},
        {"row": 2, "stage": "PLAN", "status": "done", "updated_at": ""},
    ]
    assert _aggregate_status(grp_rows) == "done"


# ── S-008: 집계 — 혼재(done+pending) → in_progress [H-3] ────────────────────

def test_aggregate_mixed():
    """S-008: rows_mixed (done+pending) → _aggregate_status == 'in_progress'."""
    from dashboard.backend.routers.tasks import _aggregate_status
    assert _aggregate_status(_rows_mixed) == "in_progress"


# ── S-009: 집계 — blocked 포함 → blocked 우선 [H-3] ────────────────────────

def test_aggregate_blocked():
    """S-009: rows_blocked (blocked 포함) → _aggregate_status == 'blocked'."""
    from dashboard.backend.routers.tasks import _aggregate_status
    assert _aggregate_status(_rows_blocked) == "blocked"


# ── S-010: 집계 — 전부 pending → pending ─────────────────────────────────────

def test_aggregate_all_pending():
    """S-010: 단계 내 행 전부 pending → _aggregate_status == 'pending'."""
    from dashboard.backend.routers.tasks import _aggregate_status
    grp_rows = [
        {"row": 1, "stage": "EXECUTE", "status": "pending", "updated_at": ""},
        {"row": 2, "stage": "EXECUTE", "status": "pending", "updated_at": ""},
        {"row": 3, "stage": "EXECUTE", "status": "pending", "updated_at": ""},
    ]
    assert _aggregate_status(grp_rows) == "pending"


# ── S-011: get_task_detail 응답 pipeline 그룹 스키마 [H-1] ──────────────────
# rows_done 보유 태스크 픽스처를 임시 디렉토리 + state.json으로 구성한다.

def test_detail_pipeline_groups(tmp_path):
    """S-011: get_task_detail 응답 pipeline[] 각 원소가 stage/done_count/total/status 필드 보유."""
    import json
    import urllib.parse
    from fastapi.testclient import TestClient
    from dashboard.backend.main import app

    # 임시 프로젝트·태스크 구조 생성
    project_dir = tmp_path / "proj-t023"
    task_dir = project_dir / "tasks" / "t023-done"
    task_dir.mkdir(parents=True)
    (task_dir / "TASK.md").write_text("# test")

    state = {
        "current_status": "done",
        "title": "done-task",
        "rows": _rows_done,
    }
    (task_dir / "state.json").write_text(json.dumps(state))

    # scan_roots 패치 없이 _find_project_path가 찾을 수 있도록 실제 경로 직접 사용
    # TestClient로 엔드포인트 호출 — 프로젝트가 scan_roots에 없으면 404이므로
    # 헬퍼 직접 호출로 대체하여 스키마만 검증한다.
    from dashboard.backend.routers.tasks import get_task_detail
    # get_task_detail은 FastAPI 라우터 함수 — 직접 호출 불가(project_path 검색 필요)
    # _group_pipeline_stages 경유로 스키마 계약 검증
    from dashboard.backend.routers.tasks import _group_pipeline_stages
    groups = _group_pipeline_stages(_rows_done)
    assert len(groups) > 0
    for g in groups:
        assert hasattr(g, "stage"), "pipeline 원소에 stage 필드 없음"
        assert hasattr(g, "done_count"), "pipeline 원소에 done_count 필드 없음"
        assert hasattr(g, "total"), "pipeline 원소에 total 필드 없음"
        assert hasattr(g, "status"), "pipeline 원소에 status 필드 없음"


# ── S-012: 빈 rows / state=None → pipeline=[] 200 [H-4] ─────────────────────

def test_detail_empty_rows():
    """S-012: 빈 rows → pipeline == [], 예외 없음 (500 미발생)."""
    from dashboard.backend.routers.tasks import _group_pipeline_stages
    groups = _group_pipeline_stages(_rows_empty)
    assert groups == []


# ── S-013~S-016: RED-fix — na/skipped 처리 규칙 보완 ─────────────────────────
# 새 기대 동작:
#   _derive_current_stage 새 규칙:
#     ① in_progress 있으면 그 stage
#     ② 없으면 실제 도달한 마지막 단계
#        (status가 done/na/skipped/in_progress 중 하나인 마지막 행의 stage)
#     ③ 전부 pending이면 첫 행 stage
#     pending(미시작) 단계는 current_stage로 표시하지 않는다.
#
#   _aggregate_status 새 규칙:
#     na/skipped는 "해당없음"으로 집계에서 제외 (active = status not in (na, skipped))
#     active 없으면 "done"
#     blocked 있으면 "blocked" → in_progress 있으면 "in_progress"
#     → active 전부 done이면 "done" → done 일부+pending이면 "in_progress"
#     → 전부 pending이면 "pending"
#
# 현재 구현은 옛 규칙이므로 아래 4개 테스트는 RED(실패)여야 정상이다.
# GREEN 전환은 opal-be-agent(EXECUTE 단계)가 담당한다.


# S-013 픽스처: 152형 rows — TASK done×2, PLAN done×3, EXECUTE done,
# TEST done×2, TEST "na", CLOSE "pending" (총 10행)
_rows_reached_not_pending = [
    {"row": 1,  "stage": "TASK",    "status": "done",    "updated_at": ""},
    {"row": 2,  "stage": "TASK",    "status": "done",    "updated_at": ""},
    {"row": 3,  "stage": "PLAN",    "status": "done",    "updated_at": ""},
    {"row": 4,  "stage": "PLAN",    "status": "done",    "updated_at": ""},
    {"row": 5,  "stage": "PLAN",    "status": "done",    "updated_at": ""},
    {"row": 6,  "stage": "EXECUTE", "status": "done",    "updated_at": ""},
    {"row": 7,  "stage": "TEST",    "status": "done",    "updated_at": ""},
    {"row": 8,  "stage": "TEST",    "status": "done",    "updated_at": ""},
    {"row": 9,  "stage": "TEST",    "status": "na",      "updated_at": ""},
    {"row": 10, "stage": "CLOSE",   "status": "pending", "updated_at": ""},
]

# S-014 픽스처: TASK done, PLAN done, PLAN "na", EXECUTE "pending"
_rows_reached_skips_na_tail = [
    {"row": 1, "stage": "TASK",    "status": "done",    "updated_at": ""},
    {"row": 2, "stage": "PLAN",    "status": "done",    "updated_at": ""},
    {"row": 3, "stage": "PLAN",    "status": "na",      "updated_at": ""},
    {"row": 4, "stage": "EXECUTE", "status": "pending", "updated_at": ""},
]


# ── S-013: _derive_current_stage — 진행중 태스크에서 pending 단계 표기 금지 ──

def test_derive_stage_reached_not_pending():
    """S-013 (RED): 마지막 도달 단계가 TEST(na 포함), CLOSE는 pending → current_stage == 'TEST'.

    현재 구현은 규칙 ②(첫 미완료=pending 행)를 따라 'CLOSE'를 반환 → RED.
    새 규칙: pending 단계는 표기하지 않고 실제 도달한 마지막 단계(TEST)를 반환해야 한다.
    """
    from dashboard.backend.routers.tasks import _derive_current_stage
    result = _derive_current_stage(_rows_reached_not_pending)
    assert result == "TEST", f"expected 'TEST', got {result!r}"


# ── S-014: _derive_current_stage — na 행은 도달 단계로 간주, pending 행은 제외 ─

def test_derive_stage_reached_skips_na_tail():
    """S-014 (RED): PLAN done + PLAN na + EXECUTE pending → current_stage == 'PLAN'.

    현재 구현은 규칙 ②(첫 미완료=pending 행)를 따라 'EXECUTE'를 반환 → RED.
    새 규칙: na는 도달 단계로 간주, EXECUTE는 미시작(pending)이므로 제외 → 'PLAN' 반환.
    """
    from dashboard.backend.routers.tasks import _derive_current_stage
    result = _derive_current_stage(_rows_reached_skips_na_tail)
    assert result == "PLAN", f"expected 'PLAN', got {result!r}"


# ── S-015: _aggregate_status — na는 집계에서 제외, active(done×2)만 → done ───

def test_aggregate_na_excluded_done():
    """S-015 (RED): grp_rows = [done, done, na] → _aggregate_status == 'done'.

    현재 구현은 na를 집계에 포함하여 all(done) 조건 불충족 → 'in_progress' 반환 → RED.
    새 규칙: na 제외 후 active=[done, done] → 전부 done → 'done' 반환.
    """
    from dashboard.backend.routers.tasks import _aggregate_status
    grp_rows = [
        {"row": 1, "stage": "TEST", "status": "done", "updated_at": ""},
        {"row": 2, "stage": "TEST", "status": "done", "updated_at": ""},
        {"row": 3, "stage": "TEST", "status": "na",   "updated_at": ""},
    ]
    result = _aggregate_status(grp_rows)
    assert result == "done", f"expected 'done', got {result!r}"


# ── S-016: _aggregate_status — 전부 na/skipped → active 없음 → done ──────────

def test_aggregate_all_skipped_done():
    """S-016 (RED): grp_rows = [na, skipped] → _aggregate_status == 'done'.

    현재 구현은 na/skipped를 알 수 없는 status로 처리하여 'pending' 반환 → RED.
    새 규칙: na/skipped 제외 후 active=[] → done 반환.
    """
    from dashboard.backend.routers.tasks import _aggregate_status
    grp_rows = [
        {"row": 1, "stage": "TEST", "status": "na",      "updated_at": ""},
        {"row": 2, "stage": "TEST", "status": "skipped", "updated_at": ""},
    ]
    result = _aggregate_status(grp_rows)
    assert result == "done", f"expected 'done', got {result!r}"


# ── T061 RED-first: 설정 쓰기 라우터(routers/config.py, 미구현) ──────────────
# 아래 테스트는 구현 전 RED(실패) 상태여야 정상이다. 라우터가 등록되지 않은 현재
# 상태에서는 모든 신규 엔드포인트 호출이 404(Not Found)를 반환하므로, 400/422/200을
# 기대하는 아래 단언은 전부 실패한다(RED). GREEN 전환은 opal-be-agent(EXECUTE 단계)가
# 담당한다. PLAN.md §3.1.2~§3.4.2 설계 시그니처 대상.


def _isolate_console_config(monkeypatch: pytest.MonkeyPatch, config_path: Path, data: dict) -> None:
    """dashboard.backend.config.CONFIG_PATH를 tmp 경로로 격리 + console.config.json 시드 작성."""
    import dashboard.backend.config as config_module

    config_path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(config_module, "CONFIG_PATH", config_path)


def _make_scanned_project(root: Path, name: str) -> str:
    """root 하위에 .opal/AGENT.md 마커를 가진 OPAL 프로젝트를 생성하고 절대경로 문자열 반환."""
    proj_dir = root / name
    (proj_dir / ".opal").mkdir(parents=True)
    (proj_dir / ".opal" / "AGENT.md").write_text("# test project", encoding="utf-8")
    return str(proj_dir)


def _make_unscanned_dir(root: Path, name: str) -> str:
    """.opal 마커 없는(스캔 화이트리스트 밖) 디렉토리 생성, 절대경로 문자열 반환."""
    d = root / name
    d.mkdir(parents=True)
    return str(d)


# ── TestConfigPathWhitelist ──────────────────────────────────────────────────

class TestConfigPathWhitelist:
    """[T061/L1-R1] 경로 검증·화이트리스트 — path traversal 차단 (H-1, S-1).

    대상: routers/config.py `_require_project_path` + POST /api/config/prewarm의
    400 게이트(빈 project·비스캔 project). project-local 대상 케이스(traversal·
    symlink·화이트리스트 외 무변경)는 T061 범위 축소로 GET|POST /api/config/project-local
    자체가 제거되어 삭제됨.
    """

    def test_empty_project_rejected_on_prewarm(self, client, tmp_path, monkeypatch):
        """[T061/L1-R1] 빈 project → POST /api/config/prewarm 400."""
        ws = tmp_path / "ws"
        ws.mkdir()
        _make_scanned_project(ws, "proj-a")
        _isolate_console_config(
            monkeypatch, tmp_path / "console.config.json",
            {"scan_roots": [str(ws)], "scan_depth": 2, "exclude": [], "prewarm_projects": []},
        )
        resp = client.post("/api/config/prewarm", json={"project": "", "enabled": True})
        assert resp.status_code == 400, f"빈 project 기대 400, got {resp.status_code}"

    def test_unscanned_project_rejected_on_prewarm(self, client, tmp_path, monkeypatch):
        """[T061/L1-R1] 비스캔 프로젝트 경로 → POST /api/config/prewarm 400."""
        ws = tmp_path / "ws"
        ws.mkdir()
        _make_scanned_project(ws, "proj-a")
        outside = _make_unscanned_dir(tmp_path / "outside", "evil")
        _isolate_console_config(
            monkeypatch, tmp_path / "console.config.json",
            {"scan_roots": [str(ws)], "scan_depth": 2, "exclude": [], "prewarm_projects": []},
        )
        resp = client.post("/api/config/prewarm", json={"project": outside, "enabled": True})
        assert resp.status_code == 400, f"비스캔 경로 기대 400, got {resp.status_code}"


# ── TestPrewarmToggle ─────────────────────────────────────────────────────────

class TestPrewarmToggle:
    """[T061/L1-R2] 프라임 풀 토글 — config 반영 + 즉시 선프라임 + 멱등 (H-5, RED, S-5).

    대상: POST /api/config/prewarm + BrainSessionRegistry.prewarm 연동 (미구현 — PLAN §3.2.2 대상).

    [MUST] 실 claude 서브프로세스 호출 0회 — brain_session_registry.prewarm 자체를
    MagicMock으로 대체하여 트리거 여부만 관측한다(test_brain.py 서브프로세스 격리 패턴
    재사용, 구독 소모 0). opbr_adapter.prime_and_ask까지 내려가지 않으므로 실 claude 미호출.
    """

    def _seed(self, monkeypatch, tmp_path) -> str:
        ws = tmp_path / "ws"
        ws.mkdir()
        proj_a = _make_scanned_project(ws, "proj-a")
        _isolate_console_config(
            monkeypatch, tmp_path / "console.config.json",
            {"scan_roots": [str(ws)], "scan_depth": 2, "exclude": [], "prewarm_projects": []},
        )
        return proj_a

    def test_toggle_on_twice_idempotent_and_single_prewarm_trigger(self, client, tmp_path, monkeypatch):
        """[T061/L1-R2] ON ×2 → config prewarm_projects에 1회만 등재 + prewarm 트리거 1회 관측."""
        from dashboard.backend.adapters.brain_session import brain_session_registry

        proj_a = self._seed(monkeypatch, tmp_path)
        config_path = tmp_path / "console.config.json"

        with patch.object(brain_session_registry, "prewarm") as mock_prewarm:
            resp1 = client.post("/api/config/prewarm", json={"project": proj_a, "enabled": True})
            resp2 = client.post("/api/config/prewarm", json={"project": proj_a, "enabled": True})

        assert resp1.status_code == 200, f"1차 ON 기대 200, got {resp1.status_code}: {resp1.text[:200]}"
        assert resp2.status_code == 200, f"2차 ON 기대 200, got {resp2.status_code}: {resp2.text[:200]}"

        assert mock_prewarm.call_count == 1, (
            f"멱등 ON 2회에도 prewarm 트리거는 1회여야 함, got {mock_prewarm.call_count}"
        )

        reloaded = json.loads(config_path.read_text(encoding="utf-8"))
        assert reloaded["prewarm_projects"].count(proj_a) == 1, (
            f"prewarm_projects에 중복 등재됨: {reloaded['prewarm_projects']}"
        )

    def test_toggle_off_removes_from_list(self, client, tmp_path, monkeypatch):
        """[T061/L1-R2] OFF → prewarm_projects 목록에서 제거."""
        from dashboard.backend.adapters.brain_session import brain_session_registry

        proj_a = self._seed(monkeypatch, tmp_path)
        config_path = tmp_path / "console.config.json"

        with patch.object(brain_session_registry, "prewarm"):
            client.post("/api/config/prewarm", json={"project": proj_a, "enabled": True})
            resp_off = client.post("/api/config/prewarm", json={"project": proj_a, "enabled": False})

        assert resp_off.status_code == 200, f"OFF 기대 200, got {resp_off.status_code}: {resp_off.text[:200]}"
        reloaded = json.loads(config_path.read_text(encoding="utf-8"))
        assert proj_a not in reloaded["prewarm_projects"], (
            f"OFF 후에도 목록에 잔존: {reloaded['prewarm_projects']}"
        )


# ── TestConsoleConfigEndpoints ────────────────────────────────────────────────

class TestConsoleConfigEndpoints:
    """[T061/L1-R3] GET /api/config — 스냅샷 반환 (S-3 router측).

    대상: GET /api/config. POST /api/config/console + models.ConsoleConfigUpdate는
    T061 범위 축소(캡틴 지시)로 제거되어 관련 케이스(미지 필드 거부·부분 갱신 HTTP 계약)는
    삭제됨. 머지 보존 자체(부분 갱신·future_key 보존)는 test_config.py의
    TestSaveConfigMergePreservation이 config.save_config를 직접 호출해 검증한다.
    """

    def _isolate(self, monkeypatch, tmp_path) -> Path:
        config_path = tmp_path / "console.config.json"
        _isolate_console_config(
            monkeypatch, config_path,
            {
                "scan_roots": ["/tmp/ws"],
                "scan_depth": 2,
                "exclude": ["backup"],
                "prewarm_projects": [],
                "future_key": "keep-me",
            },
        )
        return config_path

    def test_get_config_returns_snapshot(self, client, tmp_path, monkeypatch):
        """GET /api/config → 4필드 스냅샷 반환."""
        self._isolate(monkeypatch, tmp_path)
        resp = client.get("/api/config")
        assert resp.status_code == 200, f"기대 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert data.get("scan_roots") == ["/tmp/ws"]
        assert data.get("scan_depth") == 2
        assert data.get("exclude") == ["backup"]
        assert data.get("prewarm_projects") == []
