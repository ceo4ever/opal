"""
@header {
  "module": "tests.test_routers",
  "layer": "test",
  "domain": "console",
  "description": "S-6: 5개 엔드포인트 200 + Pydantic 응답 스키마 계약 검증. httpx TestClient. RED-first. [T021/L2-R4api] query param 방식 엔드포인트 검증 (path segment 절대경로 버그 근본 수정). [T021-fix] dashboard project 쿼리 파라미터 케이스 추가. [T021-fix2] state.json 없는 태스크 산출물 추론 케이스 추가.",
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
    "test_no_brain_endpoints",
    "test_api_projects_detail_query_param",
    "test_api_tasks_detail_query_param",
    "test_infer_column_done",
    "test_infer_column_in_progress",
    "test_infer_column_pending",
    "test_infer_column_qa_artifact",
    "test_state_to_task_card_no_state_done",
    "test_state_to_task_card_no_state_in_progress",
    "test_state_to_task_card_no_state_pending"
  ],
  "depends": ["main", "models", "routers"]
}
"""
from __future__ import annotations

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


# ── brain 엔드포인트 부재 (C-11) ──────────────────────────────────────────────

def test_no_brain_endpoints(client):
    """/api/brain* 엔드포인트가 존재하지 않아야 한다 (C-11)."""
    resp = client.get("/api/brain")
    assert resp.status_code == 404

    resp2 = client.get("/api/brain/search")
    assert resp2.status_code == 404


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
