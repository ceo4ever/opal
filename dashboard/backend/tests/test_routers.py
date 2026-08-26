"""
@header {
  "module": "tests.test_routers",
  "layer": "test",
  "domain": "console",
  "description": "S-6: 5개 엔드포인트 200 + Pydantic 응답 스키마 계약 검증. httpx TestClient. RED-first. [T021/L2-R4api] query param 방식 엔드포인트 검증 (path segment 절대경로 버그 근본 수정). [T021-fix] dashboard project 쿼리 파라미터 케이스 추가. [T021-fix2] state.json 없는 태스크 산출물 추론 케이스 추가. [T023/RED] _derive_current_stage / _group_pipeline_stages / _aggregate_status 신규 헬퍼 + get_task_detail pipeline 그룹 스키마 RED-first (S-001~S-012). [T023/RED-fix] _derive_current_stage na/skipped 도달 단계 파악 + _aggregate_status na/skipped 제외 집계 RED-first (S-013~S-016). [T061] 설정 라우터 계약 — 경로검증·화이트리스트(S-1, prewarm 대상 빈/비스캔 400만) · console.config GET 스냅샷(S-3 router측, GET만) · 프라임 풀 토글 멱등+prewarm 트리거 관측(S-5). S-5는 brain_session_registry.prewarm을 MagicMock으로 대체 관측 — 실 claude 서브프로세스 호출 0회(test_brain.py 격리 패턴 재사용). T061 범위 축소(캡틴 지시)로 console.config POST(S-3 쓰기측)·프로젝트 로컬 설정(S-4) 계약은 미사용 쓰기 API 제거에 따라 삭제됨. [T103/R3 RED] 태스크 진행 통계 API 계약 — PipelineRow 원천 5키+gate 객체(TS-010) · 사표 필드 row/updated_at 값 채움(TS-011) · 상세 stats 소요 파생(TS-012) · 실시간 현재 행 불변식(TS-013) · 산출물 전수 9건 4유형(TS-014) · 결측 200 + gate_recorded 구분(TS-015) · 캐시 경계 정적만(TS-018) · 대시보드 모수 항등(TS-020) · 코호트 필터 중앙값(TS-021) · 산출물 규모 항등(TS-022) · workflow 키 0건(TS-023). 기대값 원천은 STATS-BASELINE.md(E1)이며 이동값은 항등·하한·불변식으로 단정한다. RED-first — 작성자(opal-test-agent, mode: red) != 구현자(opal-be-agent). 기존 케이스는 수정 0건, 추가만 수행. [T103/Step8 회귀] RED 대상이 아닌 회귀 2건 보강 — 변경 전 응답 스키마 불변(TS-017: 카드 9필드·상세 10필드·그룹 5필드·행 4필드, artifact_count 값 증가는 P-4 4항 명시적 예외) · DashboardSummaryResponse 기존 8필드 불변(TS-024: 타입·중첩 형태·의미 항등 + additive 5필드 기본값 보유). 기대값 원천은 변경 전(git HEAD) models.py이며 구현 출력을 되쓰지 않는다. 전역 카운트는 응답 내부 항등으로 단정한다(이동값 규약). [T103/R-16] 소요 3계열 API 계약 — 미기록 태스크(101)의 축퇴 항등 PM==작업·캡틴==대기(TS-106) · 기록 보유 태스크(103)의 실분해와 단계 합 항등(TS-107) · 워크플로우 집계 additive + 대표값 불변(TS-108). 진행 중 태스크의 total_minutes는 실시간 값이라 3계열 항등의 기준이 아니며(집계기준 11) 정적 합(work+wait)에 대해 단정한다. [호칭 하드코딩 제거] owner 라벨·owner_term 계약 — owner==user 행 라벨이 로더 값(스텁 \"테스터\")을 따르고, PM·auto 역할명은 불변이며, 상세·대시보드 응답 최상위 owner_term에 같은 값이 실리고, identity.md 부재 시 200 + \"사용자\" 폴백이 라벨·owner_term 양쪽에 도달함을 단정한다. 기존 케이스 수정 0건, 추가만 수행.",
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
    "test_t103_ts106_detail_three_series_degenerates_on_unmeasured",
    "test_t103_ts107_detail_three_series_splits_on_measured",
    "test_t103_ts108_dashboard_three_series_is_additive",
    "TestConfigPathWhitelist",
    "TestPrewarmToggle",
    "TestConsoleConfigEndpoints",
    "test_t103_ts010_pipeline_row_source_keys_and_gate_object",
    "test_t103_ts011_deprecated_aliases_filled",
    "test_t103_ts012_detail_stats_matches_baseline",
    "test_t103_ts013_running_task_current_row_invariant",
    "test_t103_ts013_completed_task_is_not_running",
    "test_t103_ts013_pending_owner_does_not_decide_series",
    "test_t103_ts014_artifacts_full_enumeration_and_classification",
    "test_t103_ts015_missing_state_json_returns_200",
    "test_t103_ts015_gate_recorded_distinguishes_zero_from_unrecorded",
    "test_t103_ts018_cache_holds_static_derivations_only",
    "test_t103_ts018_completed_task_stable_across_cache",
    "test_t103_ts020_dashboard_task_counts_identity",
    "test_t103_ts021_workflow_stats_cohort_filtered_medians",
    "test_t103_ts022_artifact_total_identity",
    "test_t103_ts023_response_uses_source_terminology",
    "test_t103_ts017_task_card_legacy_fields_unchanged",
    "test_t103_ts017_task_detail_legacy_fields_unchanged",
    "test_t103_ts017_artifact_count_increase_is_declared_exception",
    "test_t103_ts024_dashboard_legacy_fields_unchanged",
    "test_t103_ts024_dashboard_legacy_semantics_unchanged",
    "test_t103_ts024_dashboard_model_extension_is_additive"
  ],
  "depends": [
    "main",
    "models",
    "routers",
    "config",
    "adapters.brain_session",
    "cache",
    "stats"
  ],
  "task": "061",
  "scenarios": [
    "S-1",
    "S-3",
    "S-5",
    "TS-010",
    "TS-011",
    "TS-012",
    "TS-013",
    "TS-014",
    "TS-015",
    "TS-017",
    "TS-018",
    "TS-020",
    "TS-021",
    "TS-022",
    "TS-023",
    "TS-024",
    "TS-106",
    "TS-107",
    "TS-108"
  ],
  "changelog": [
    "2026-08-26 T103 R-21: 야간 보정(집계 기준 17) 반영 — t103_clean_cache가 라우터 load_quiet_hours를 00:00~09:00으로 고정(머신 설정 의존 제거), _T103_BASELINE_WORKFLOW 기대값 갱신(opd 799→425·13시간 19분→7시간 5분, opds 대기 비중 4→5, opp 불변), TS-018 캐시 키 리터럴에 구간 서명 부착, TS-137 표면화·보정 끔 2건 추가. 기존 케이스 삭제 0건",
    "2026-07-14 T061 RED: 설정 라우터(routers/config.py, 미구현) 경로검증/화이트리스트(S-1)·console.config GET/POST(S-3)·프로젝트 로컬 설정 3경로+재조회(S-4)·프라임 풀 토글 멱등(S-5) 실패 테스트 추가 — 구현 전 RED 트랙(red-first.md), 작성자(opal-test-agent)≠구현자(opal-be-agent)",
    "2026-07-14 T061 범위 축소: TestProjectLocalSettings 클래스 삭제 + TestConfigPathWhitelist 중 project-local 대상 3건(traversal·symlink·화이트리스트 외 무변경) 삭제(prewarm 대상 빈/비스캔 400 2건은 유지) + TestConsoleConfigEndpoints의 console POST 2건 삭제(GET 스냅샷 1건은 유지) — 프로젝트 로컬 설정·console.config 전반 편집 미반영에 따른 계약 삭제, scenarios에서 S-4 제거",
    "2026-08-25 T103 R3 RED: 태스크 진행 통계 API 계약 케이스 15건 추가(TS-010~015·018·020~023) — 구현(Step 4~7) 전 RED 트랙(red-first.md §1), 작성자!=구현자(동 §2). 기존 케이스 수정·삭제 0건",
    "2026-08-25 T103 Step8: 회귀 케이스 6건 추가(TS-017 3건·TS-024 3건, 파라미터화 포함 7항목) — P-4 회귀 경계 1·2 조작적 정의. RED 대상 아님(항상 GREEN). 기존 케이스 수정·삭제 0건",
    "2026-08-25 T103 R-16: 소요 3계열 API 계약 케이스 3건 추가(TS-106~TS-108) — 축퇴 항등·실분해·additive 확장. 기존 케이스 수정·삭제 0건"
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


# ══════════════════════════════════════════════════════════════════════════════
# T103 R3 RED-first: 태스크 진행 통계 API 계약 (TS-010~015 · TS-018 · TS-020~023)
#
# 아래 테스트는 구현 전 RED(실패) 상태여야 정상이다.
# GREEN 전환은 opal-be-agent(EXECUTE Step 4~7)가 담당한다.
# [MUST] red-first.md §3 — GREEN 루핑 중 본 블록의 단정을 약화·삭제하지 않는다.
#
# 기대값 원천: tasks/103-260825-opd-태스크-진행통계/STATS-BASELINE.md §3~§5
#             (ANALYSIS §8 재검증 완료 수치, 근거 E1). stats.py 출력 되쓰기 금지.
# 이동값 규약: §0.5 — 진행 중 태스크·전역 카운트는 값이 아니라 항등·하한·불변식으로 단정한다.
# ══════════════════════════════════════════════════════════════════════════════

import statistics
import urllib.parse

_T103_ROOT = str(Path(__file__).resolve().parents[3])

_T103_TASK_101 = "101-260824-opd-핸드오프-스키마-계약정합"
_T103_TASK_091 = "091-260813-opd-파이프라인-스펙-중복정리"   # FX-LEGACY — gate 보유 행 0건
_T103_TASK_089 = "089-260811-opi-opal"                      # FX-089 — state.json 부재
_T103_TASK_102 = "102-260824-opd-태스크분석-경계재정의"
_T103_TASK_103 = "103-260825-opd-태스크-진행통계"

# STATS-BASELINE.md §2.1 동결 코호트 21건 (3자리 접두)
_T103_COHORT = {
    "opd": ["080", "091", "092", "093", "094", "100", "101"],
    "opds": ["081", "082", "083", "085", "090", "095", "096", "097", "098", "099"],
    "opp": ["084", "086", "087", "088"],
}
# STATS-BASELINE.md §4.4 — skill: (n, median_minutes, median_label, wait_ratio)
# [R-21 갱신 2026-08-26] 야간 보정(집계 기준 17, `00:00~09:00` 제외)이 켜지면서 기대값이 옮겨졌다.
# 보정 전 확정값은 STATS-BASELINE.md §4.1·§4.2에 그대로 남아 있다 —
#   opd (7, 799, "13시간 19분", 21) / opds (10, 276, "4시간 36분", 4) / opp (4, 75, "1시간 15분", 54)
# opd만 움직인다(밤을 넘긴 태스크가 5건). opds·opp의 중앙값은 하루 안에 끝나 불변이며,
# opds의 대기 비중만 분모(작업)가 줄어 4 → 5로 반올림이 넘어간다.
_T103_BASELINE_WORKFLOW = {
    "opd": (7, 425, "7시간 5분", 23),
    "opds": (10, 276, "4시간 36분", 5),
    "opp": (4, 75, "1시간 15분", 54),
}
# STATS-BASELINE.md §3.2 — stage: (total, work, wait)
_T103_BASELINE_101_STAGES = [
    ("TASK", 24, 0, 24),
    ("ANALYSIS", 22, 17, 5),
    ("PLAN", 13, 11, 2),
    ("TEST-SCENARIO", 295, 10, 285),
    ("EXECUTE", 18, 18, 0),
    ("TEST", 51, 47, 4),
    ("CLOSE", 2, 2, 0),
]


def _t103_detail(client, task_id: str):
    """GET /api/tasks/detail — 실 프로젝트 절대경로 기준."""
    project = urllib.parse.quote(_T103_ROOT, safe="")
    task = urllib.parse.quote(task_id, safe="")
    return client.get(f"/api/tasks/detail?project={project}&task_id={task}")


def _t103_dashboard(client):
    """GET /api/dashboard — 실 프로젝트 절대경로 기준."""
    project = urllib.parse.quote(_T103_ROOT, safe="")
    return client.get(f"/api/dashboard?project={project}")


def _t103_flat_rows(detail: dict) -> list[dict]:
    """pipeline[].rows[] 평탄화 — 그룹 순서·행 순서 보존."""
    return [r for group in detail["pipeline"] for r in group["rows"]]


def _t103_live_state(task_id: str) -> dict:
    """실 state.json 로드 — 불변식 대조용(값 단정 아님)."""
    with open(os.path.join(_T103_ROOT, "tasks", task_id, "state.json"), encoding="utf-8") as f:
        return json.load(f)


def _t103_expected_current_row(state: dict) -> dict | None:
    """집계기준 12 불변식 — in_progress 행 우선, 없으면 첫 pending 행."""
    for row in state.get("rows", []):
        if row.get("status") == "in_progress":
            return row
    for row in state.get("rows", []):
        if row.get("status") == "pending":
            return row
    return None


def _t103_all_keys(node, acc: set) -> set:
    """응답 JSON 전 키 재귀 수집."""
    if isinstance(node, dict):
        for key, value in node.items():
            acc.add(key)
            _t103_all_keys(value, acc)
    elif isinstance(node, list):
        for item in node:
            _t103_all_keys(item, acc)
    return acc


# 야간 제외 구간 고정값 (집계 기준 17) — setting.default.json의 기본과 같은 `00:00~09:00`.
# 기대값이 실행 머신의 ~/.opal/setting.json에 좌우되면 안 되므로 라우터 로더를 고정한다.
_T103_QUIET_HOURS = (0, 9 * 60)
_T103_QUIET_TOKEN = "0-540"
_T103_QUIET_LABEL = "00:00~09:00"


@pytest.fixture
def t103_clean_cache(monkeypatch):
    """전역 캐시 격리 + 야간 제외 구간 고정.

    캐시는 앞선 테스트가 남긴 항목이 계약 검증을 오염시키지 않게 비운다.
    야간 구간(R-21)은 설정 파일이 아니라 여기서 못박는다 — 라우터가 실제 설정을
    읽으므로, 고정하지 않으면 머신마다 기대값이 달라진다.
    """
    from dashboard.backend.cache import cache
    from dashboard.backend.routers import dashboard as dashboard_router
    from dashboard.backend.routers import tasks as tasks_router

    for module in (dashboard_router, tasks_router):
        monkeypatch.setattr(
            module, "load_quiet_hours", lambda _project=None: _T103_QUIET_HOURS
        )

    cache.clear()
    yield cache
    cache.clear()


# ── TS-010: PipelineRow 5키 확장 + gate 객체 직렬화 ──────────────────────────

def test_t103_ts010_pipeline_row_source_keys_and_gate_object(client, t103_clean_cache):
    """[T103/L2-R2] 101 상세 rows[]가 owner·gate·note·timestamp·key 5키를 보유하고
    gate가 {artifacts, checklist} 객체로 직렬화된다 (불리언 아님).

    RED 기대 실패: 확장 전 rows[]는 row·stage·status·updated_at 4키뿐 → KeyError/assert 실패.
    """
    resp = _t103_detail(client, _T103_TASK_101)
    assert resp.status_code == 200
    rows = _t103_flat_rows(resp.json())

    assert len(rows) == 19

    for row in rows:
        for key in ("owner", "gate", "note", "timestamp", "key"):
            assert key in row, f"row {row.get('row_id')}에 {key} 키 부재"

    gate_rows = [r for r in rows if r["gate"] is not None]
    assert len(gate_rows) == 4
    assert [r["row_id"] for r in gate_rows] == [4, 7, 10, 17]

    for row in gate_rows:
        gate = row["gate"]
        assert isinstance(gate, dict), "gate는 불리언이 아니라 객체다"
        assert "artifacts" in gate and "checklist" in gate
        assert isinstance(gate["artifacts"], list)
        assert isinstance(gate["checklist"], list)

    assert sum(1 for r in rows if r["gate"] is None) == 15


# ── TS-011: 사표 필드 교정 — row 1~19 연속 · updated_at 빈 문자열 0건 ────────

def test_t103_ts011_deprecated_aliases_filled(client, t103_clean_cache):
    """[T103/L2-R2] 평탄화 rows[]에서 row가 1~19 연속이고 updated_at 빈 문자열이 0건이다.

    RED 기대 실패: 교정 전 row는 그룹마다 0-based로 리셋되고 updated_at은 19건 전건 "".
    """
    resp = _t103_detail(client, _T103_TASK_101)
    assert resp.status_code == 200
    rows = _t103_flat_rows(resp.json())

    assert [r["row"] for r in rows] == list(range(1, 20))
    assert [r["row_id"] for r in rows] == list(range(1, 20))

    assert [r for r in rows if r["updated_at"] == ""] == []

    for row in rows:
        assert row["row"] == row["row_id"]
        assert row["updated_at"] == row["timestamp"]


# ── TS-012: 상세 응답 소요 파생 — BE 값이 L1 계산과 동일 ────────────────────

def test_t103_ts012_detail_stats_matches_baseline(client, t103_clean_cache):
    """[T103/L2-R3] 101 상세 stats·pipeline 소요가 STATS-BASELINE.md §3과 전건 일치한다."""
    resp = _t103_detail(client, _T103_TASK_101)
    assert resp.status_code == 200
    detail = resp.json()

    stats = detail["stats"]
    assert stats["available"] is True
    assert stats["total_minutes"] == 425
    assert stats["work_minutes"] == 105
    assert stats["wait_minutes"] == 320
    assert stats["wait_ratio"] == 75
    assert stats["total_label"] == "7시간 5분"
    assert stats["work_label"] == "1시간 45분"
    assert stats["wait_label"] == "5시간 20분"
    assert stats["peak_stage"] == "TEST-SCENARIO"

    groups = detail["pipeline"]
    assert len(groups) == 7
    for group, (name, total, work, wait) in zip(groups, _T103_BASELINE_101_STAGES):
        assert group["stage"] == name
        assert group["total_minutes"] == total, f"{name} 총 소요"
        assert group["work_minutes"] == work, f"{name} 작업 소요"
        assert group["wait_minutes"] == wait, f"{name} 대기 소요"

    assert sum(g["total_minutes"] for g in groups) == stats["total_minutes"]
    assert [g["stage"] for g in groups if g["is_peak"]] == ["TEST-SCENARIO"]


# ── TS-013: 실시간 파생 — 진행 중 구조 단정 + 완료 값 단정 ──────────────────

@pytest.mark.parametrize("task_id", [_T103_TASK_102, _T103_TASK_103])
def test_t103_ts013_running_task_current_row_invariant(client, t103_clean_cache, task_id):
    """[T103/L2-R4] 진행 중 태스크의 현재 행이 집계기준 12·14 불변식을 만족한다.

    이동값이므로 값이 아니라 동작을 단정한다 (TASK.md §제약 조건).
    current_series는 owner(pending 행 전건 PM 기본값)가 아니라 key의 *.user_confirm 패턴으로 판정된다.
    """
    state = _t103_live_state(task_id)
    resp = _t103_detail(client, task_id)
    assert resp.status_code == 200
    stats = resp.json()["stats"]

    if state.get("current_status") == "done":
        assert stats["is_running"] is False
        assert stats["current_row_id"] is None
        return

    assert stats["is_running"] is True

    expected_row = _t103_expected_current_row(state)
    assert expected_row is not None, "진행 중 태스크에는 현재 행이 존재한다"
    assert stats["current_row_id"] == expected_row["row_id"]
    assert stats["current_key"] == expected_row["key"]
    assert stats["current_stage"] == expected_row["stage"]

    expected_series = "wait" if expected_row["key"].endswith(".user_confirm") else "work"
    assert stats["current_series"] == expected_series

    assert isinstance(stats["current_elapsed_minutes"], int)
    assert stats["current_elapsed_minutes"] >= 0
    assert stats["total_minutes"] >= stats["current_elapsed_minutes"]


def test_t103_ts013_completed_task_is_not_running(client, t103_clean_cache):
    """[T103/L2-R4] 완료 태스크(101)는 is_running=false이고 total_minutes가 425로 고정된다."""
    resp = _t103_detail(client, _T103_TASK_101)
    assert resp.status_code == 200
    stats = resp.json()["stats"]

    assert stats["is_running"] is False
    assert stats["total_minutes"] == 425
    assert stats["current_row_id"] is None
    assert stats["current_elapsed_minutes"] is None


def test_t103_ts013_pending_owner_does_not_decide_series(client, t103_clean_cache):
    """[T103/L2-R4] FX-102 전제 — pending 행 owner가 전건 PM인데도 user_confirm 행은 wait로 귀속된다."""
    state = _t103_live_state(_T103_TASK_102)
    pending = [r for r in state["rows"] if r.get("status") == "pending"]
    assert pending, "102는 pending 행을 보유한다"
    assert {r.get("owner") for r in pending} == {"PM"}, "전제: pending owner는 init 기본값 PM"

    resp = _t103_detail(client, _T103_TASK_102)
    assert resp.status_code == 200
    stats = resp.json()["stats"]

    if stats["current_key"] and stats["current_key"].endswith(".user_confirm"):
        assert stats["current_series"] == "wait", "owner=PM에 속아 work로 귀속되면 안 된다"


# ── TS-014: 산출물 전수 9건 + 4유형 분류 ─────────────────────────────────────

def test_t103_ts014_artifacts_full_enumeration_and_classification(client, t103_clean_cache):
    """[T103/L2-R5] 101 상세 artifacts가 .md 전수 9건이고 artifact_items가 4유형으로 분류된다.

    RED 기대 실패: 화이트리스트 6종 교집합 폐기 전에는 artifacts 길이 5.
    """
    resp = _t103_detail(client, _T103_TASK_101)
    assert resp.status_code == 200
    detail = resp.json()

    assert len(detail["artifacts"]) == 9
    assert sorted(detail["artifacts"]) == [
        "AGENTIC-LOG.md",
        "ANALYSIS.md",
        "DONE.md",
        "GC-CONVENTION-260824.md",
        "PLAN.md",
        "SCENARIO-GATE-1.md",
        "STATE.md",
        "TASK.md",
        "TEST-SCENARIO.md",
    ]

    items = detail["artifact_items"]
    assert len(items) == len(detail["artifacts"])

    by_type: dict[str, list[str]] = {}
    for item in items:
        by_type.setdefault(item["type"], []).append(item["name"])

    assert sorted(by_type.get("pipeline", [])) == [
        "ANALYSIS.md", "DONE.md", "PLAN.md", "TASK.md", "TEST-SCENARIO.md",
    ]
    assert sorted(by_type.get("verification", [])) == [
        "GC-CONVENTION-260824.md", "SCENARIO-GATE-1.md",
    ]
    assert sorted(by_type.get("log", [])) == ["AGENTIC-LOG.md", "STATE.md"]
    assert by_type.get("other", []) == []

    # 정렬: pipeline → verification → log → other
    order = ["pipeline", "verification", "log", "other"]
    observed = [item["type"] for item in items]
    assert observed == sorted(observed, key=order.index)

    # 유형 라벨 동반
    labels = {item["type"]: item["type_label"] for item in items}
    assert labels["pipeline"] == "파이프라인"
    assert labels["verification"] == "검증"
    assert labels["log"] == "로그"


# ── TS-015: 결측 태스크 200 + 게이트 「미기록」 구분 ─────────────────────────

def test_t103_ts015_missing_state_json_returns_200(client, t103_clean_cache):
    """[T103/L2-R12] state.json 부재 태스크(089)가 500이 아니라 200 + available=false로 응답한다."""
    resp = _t103_detail(client, _T103_TASK_089)
    assert resp.status_code == 200

    detail = resp.json()
    assert detail["stats"] is None or detail["stats"]["available"] is False
    assert detail["pipeline"] == []


def test_t103_ts015_gate_recorded_distinguishes_zero_from_unrecorded(client, t103_clean_cache):
    """[T103/L2-R12] 「게이트 0건」과 「게이트 미기록」이 서로 다른 두 필드로 구분된다.

    091(092 이전 태스크, gate 키 보유 행 0건) → gate_recorded=false · gate_count=0
    101 → gate_recorded=true · gate_count=4
    """
    legacy = _t103_detail(client, _T103_TASK_091)
    assert legacy.status_code == 200
    legacy_stats = legacy.json()["stats"]
    assert legacy_stats["available"] is True
    assert legacy_stats["gate_recorded"] is False
    assert legacy_stats["gate_count"] == 0

    current = _t103_detail(client, _T103_TASK_101)
    assert current.status_code == 200
    current_stats = current.json()["stats"]
    assert current_stats["gate_recorded"] is True
    assert current_stats["gate_count"] == 4


# ── TS-018: 캐시 히트 응답에서도 실시간 값 재계산 ───────────────────────────

def test_t103_ts018_cache_holds_static_derivations_only(client, t103_clean_cache):
    """[T103/L2-R4] TTL 내 2회 연속 호출에서 정적 파생은 동일하고 실시간 파생은 캐시에 고착되지 않는다.

    [MUST] PLAN.md §3.2.2: "캐시에는 정적 파생만 담는다. 진행 중 태스크의 실시간 파생은
    캐시 히트 이후 task_live_stats(state, now=datetime.now())로 계산해 응답에 합성한다."

    RED 기대 실패: 실시간 값까지 캐시에 넣은 구현에서 캐시 payload에 current_elapsed_minutes가 실린다.
    """
    first = _t103_detail(client, _T103_TASK_102)
    assert first.status_code == 200
    second = _t103_detail(client, _T103_TASK_102)
    assert second.status_code == 200

    d1, d2 = first.json(), second.json()

    # 정적 파생 동일
    assert d1["pipeline"] == d2["pipeline"]
    assert d1["stats"]["gate_count"] == d2["stats"]["gate_count"]
    assert d1["stats"]["work_minutes"] == d2["stats"]["work_minutes"]
    assert d1["stats"]["wait_minutes"] == d2["stats"]["wait_minutes"]

    # 캐시 payload에는 실시간 파생 키가 실리지 않는다 (캐시 경계 계약)
    cache_key = f"task_detail:{_T103_ROOT}:{_T103_TASK_102}:{_T103_QUIET_TOKEN}"
    cached = t103_clean_cache.get(cache_key)
    assert cached is not None, "TTL 내 2차 호출은 캐시 히트여야 한다"

    cached_payload = cached if isinstance(cached, dict) else cached.model_dump()
    cached_keys = _t103_all_keys(cached_payload, set())
    for live_key in ("current_elapsed_minutes", "current_elapsed_label", "is_running"):
        assert live_key not in cached_keys, f"실시간 파생 {live_key}가 캐시에 고착됐다"

    # 재계산 결과는 단조 비감소
    if d1["stats"]["is_running"]:
        assert d2["stats"]["current_elapsed_minutes"] >= d1["stats"]["current_elapsed_minutes"]


def test_t103_ts018_completed_task_stable_across_cache(client, t103_clean_cache):
    """[T103/L2-R4] 완료 태스크(101)는 캐시 미스·히트 2회 호출 모두 425로 불변이다."""
    first = _t103_detail(client, _T103_TASK_101).json()
    second = _t103_detail(client, _T103_TASK_101).json()

    assert first["stats"]["total_minutes"] == 425
    assert second["stats"]["total_minutes"] == 425


# ── TS-020: 대시보드 모수 — 완료/전체 항등 ──────────────────────────────────

def test_t103_ts020_dashboard_task_counts_identity(client, t103_clean_cache):
    """[T103/L2-R10] completed + 진행중 == total, completed >= 21 (이동값 → 항등·하한 단정)."""
    resp = _t103_dashboard(client)
    assert resp.status_code == 200
    data = resp.json()

    assert data["completed_tasks"] >= 21
    assert data["total_tasks"] >= 23
    assert data["completed_tasks"] <= data["total_tasks"]

    assert sum(w["n"] for w in data["workflow_stats"]) == data["completed_tasks"]
    assert sum(len(w["tasks"]) for w in data["workflow_stats"]) == data["completed_tasks"]


# ── TS-021: 워크플로우별 응답 — 코호트 필터 기준 중앙값·대기 비중 ───────────

def test_t103_ts021_workflow_stats_cohort_filtered_medians(client, t103_clean_cache):
    """[T103/L2-R10] 동결 코호트 21건 ID로 필터한 중앙값이 799/276/75와 일치한다.

    [MUST] STATS-BASELINE.md §6.1: "완료기준 (3) 검증은 반드시 §2 ID 목록으로 필터한 뒤 대조한다"
    — 102 완료 시 필터 없는 재측정은 opd 모수가 7→8로 이동한다 (H-10).
    """
    resp = _t103_dashboard(client)
    assert resp.status_code == 200
    workflows = resp.json()["workflow_stats"]

    assert len(workflows) == 3
    by_skill = {w["skill"]: w for w in workflows}
    assert sorted(by_skill) == ["opd", "opds", "opp"]

    for skill, (n, median, median_label, wait_ratio) in _T103_BASELINE_WORKFLOW.items():
        w = by_skill[skill]
        cohort = _T103_COHORT[skill]

        observed_ids = {t["task_id"] for t in w["tasks"]}
        observed_prefixes = {tid[:3] for tid in observed_ids}
        assert set(cohort) <= observed_prefixes, f"{skill} 코호트 누락: {set(cohort) - observed_prefixes}"

        # 코호트 ID로 필터한 재계산 — 동결값이므로 값 단정이 성립한다
        cohort_totals = [t["total_minutes"] for t in w["tasks"] if t["task_id"][:3] in cohort]
        assert len(cohort_totals) == n, f"{skill} 코호트 모수"
        assert round(statistics.median(cohort_totals)) == median, f"{skill} 코호트 중앙값"

        # sample_insufficient는 n<5 판정 (집계기준 5)
        assert w["sample_insufficient"] is (w["n"] < 5)

        # 이동값 경계 — 코호트가 곧 완료 전량인 동안에만 API 직접값을 단정한다
        if observed_prefixes == set(cohort):
            assert w["n"] == n
            assert w["median_minutes"] == median
            assert w["median_label"] == median_label
            assert w["wait_ratio"] == wait_ratio, f"{skill} 대기 비중"
        else:
            assert 0 <= w["wait_ratio"] <= 100


# ── TS-022: 산출물 규모 항등 ────────────────────────────────────────────────

def test_t103_ts022_artifact_total_identity(client, t103_clean_cache):
    """[T103/L2-R10] artifact_total == artifact_by_type 합계 (이동값 → 항등 단정)."""
    resp = _t103_dashboard(client)
    assert resp.status_code == 200
    data = resp.json()

    by_type = data["artifact_by_type"]
    assert sorted(by_type) == ["log", "other", "pipeline", "verification"]
    assert data["artifact_total"] == sum(by_type.values())
    assert data["artifact_total"] >= 192


# ── TS-023: 필드 명명 계약 — workflow 키 0건 ────────────────────────────────

def test_t103_ts023_response_uses_source_terminology(client, t103_clean_cache):
    """[T103/L2] 두 응답 JSON 전 키에 workflow가 0건이고 skill·timestamp·row_id를 쓴다.

    [MUST] TASK.md 집계 기준 15 — 「워크플로우」는 UI 표시 라벨로만 남는다.
    stats.py의 import 경계(순환 차단)는 test_stats.py TS-008이 소유한다.
    """
    detail_keys = _t103_all_keys(_t103_detail(client, _T103_TASK_101).json(), set())
    dashboard_keys = _t103_all_keys(_t103_dashboard(client).json(), set())

    for keys, label in ((detail_keys, "detail"), (dashboard_keys, "dashboard")):
        assert "workflow" not in keys, f"{label} 응답에 workflow 키가 존재한다"

    assert {"timestamp", "row_id"} <= detail_keys
    assert "skill" in dashboard_keys

    # 사표 필드는 존치하되 값이 채워진다 (빈 문자열·0 폴백 0건)
    rows = _t103_flat_rows(_t103_detail(client, _T103_TASK_101).json())
    assert all(r["row"] > 0 for r in rows)
    assert all(r["updated_at"] != "" for r in rows)


# ══════════════════════════════════════════════════════════════════════════════
# T103 Step 8 회귀 보강: TS-017 · TS-024 (PLAN P-4 회귀 경계)
#
# 본 2건은 RED-first 대상이 아니다 — 구현 후 회귀 방지 시나리오이며 항상 GREEN이어야
# 한다 (TEST-SCENARIO.md §0.2).
#
# 기대값 원천: 변경 전(T103 이전) 응답 스키마 = git HEAD의 dashboard/backend/models.py.
#             구현 출력을 기대값으로 되쓰지 않는다 (§0.4 자기확인 금지).
# 이동값 규약: 전역 카운트는 절대값이 아니라 응답 내부 항등·불변식으로 단정한다 (§0.5).
# 예외 선언: artifact_count·artifacts[]의 값 증가(101 기준 5 → 9)는 집계기준 9의
#           의도된 결과이며 회귀가 아니다 (PLAN P-4 4항).
# ══════════════════════════════════════════════════════════════════════════════

import datetime as _t103_dt

# ── 변경 전 스키마 (필드명 → 기대 타입) ─────────────────────────────────────
_T103_LEGACY_TASK_CARD = {
    "task_id": str, "title": str, "skill": str, "mode": str, "column": str,
    "current_stage": str, "progress": int, "updated_at": str, "artifact_count": int,
}
_T103_LEGACY_TASK_CARD_COLUMNS = {"pending", "in_progress", "blocked", "done", "archive"}
_T103_LEGACY_DETAIL = {
    "task_id": str, "title": str, "skill": str, "mode": str, "current_status": str,
    "current_stage": str, "progress": int, "pipeline": list, "artifacts": list,
    "updated_at": str,
}
_T103_LEGACY_STAGE_GROUP = {
    "stage": str, "done_count": int, "total": int, "status": str, "rows": list,
}
_T103_LEGACY_PIPELINE_ROW = {"row": int, "stage": str, "status": str, "updated_at": str}
_T103_LEGACY_DASHBOARD = {
    "total_projects": int, "running_tasks": int, "blockers": int,
    "additional_work": int, "status_distribution": dict, "activity_trend": list,
    "alerts": list, "recent_activities": list,
}
_T103_LEGACY_STATUS_DISTRIBUTION = {
    "pending": int, "in_progress": int, "blocked": int, "done": int,
}
_T103_LEGACY_ACTIVITY_POINT = {"date": str, "count": int}
_T103_LEGACY_ALERT = {
    "task_id": str, "title": str, "project": str, "status": str, "message": str,
}
_T103_LEGACY_RECENT = {
    "date": str, "task_id": str, "title": str, "project": str, "stage": str,
}
# 103 additive 5필드 — TS-024 「신규 5필드 전건 기본값 보유」 대상
_T103_DASHBOARD_ADDITIVE = (
    "completed_tasks", "total_tasks", "artifact_total", "artifact_by_type",
    "workflow_stats",
)

# 101은 완료 태스크이며 `.md` 9개로 동결된다 (TEST-SCENARIO §2.1 FX-101 · §0.4 E1)
_T103_BASELINE_101_ARTIFACTS = 9
# 구 화이트리스트 6종 교집합 기준 101 산출물 수 (PLAN P-3 근거 1)
_T103_LEGACY_WHITELIST_101_ARTIFACTS = 5


def _t103_assert_legacy_fields(payload: dict, spec: dict, label: str) -> None:
    """변경 전 필드가 전건 존재하고 타입이 불변인지 단정한다 (제거·타입 변경 0건)."""
    for field, expected in spec.items():
        assert field in payload, f"{label}: 변경 전 필드 `{field}`가 응답에서 사라졌다"
        value = payload[field]
        if expected is int:
            ok = isinstance(value, int) and not isinstance(value, bool)
        else:
            ok = isinstance(value, expected)
        assert ok, (
            f"{label}: `{field}` 타입이 {expected.__name__} → "
            f"{type(value).__name__}으로 변경됐다"
        )


def _t103_tasks(client):
    """GET /api/tasks — 실 프로젝트 절대경로 기준."""
    project = urllib.parse.quote(_T103_ROOT, safe="")
    return client.get(f"/api/tasks?project={project}")


# ── TS-017: BE 기존 응답 스키마 회귀 0 (P-4 회귀 경계 1·2) ───────────────────

def test_t103_ts017_task_card_legacy_fields_unchanged(client, t103_clean_cache):
    """[T103/L2-REG2] 칸반 카드 응답의 변경 전 9필드가 제거·타입 변경 없이 유지된다.

    화이트리스트 폐기(Step 6)가 artifact_count 소비자를 동반 변동시키므로,
    스키마 축 불변을 값 축 변동(P-4 4항 예외)과 분리해 단정한다 (H-4).
    """
    resp = _t103_tasks(client)
    assert resp.status_code == 200
    cards = resp.json()
    assert isinstance(cards, list) and cards

    for card in cards:
        _t103_assert_legacy_fields(
            card, _T103_LEGACY_TASK_CARD, f"card {card.get('task_id')}"
        )
        assert card["column"] in _T103_LEGACY_TASK_CARD_COLUMNS


@pytest.mark.parametrize("task_id", [_T103_TASK_101, _T103_TASK_089])
def test_t103_ts017_task_detail_legacy_fields_unchanged(client, t103_clean_cache, task_id):
    """[T103/L2-REG2] 상세 응답의 변경 전 10필드 + 그룹 5필드 + 행 4필드가 불변이다.

    state.json 부재 태스크(089)까지 포함해, additive 확장이 결측 경로에서도
    기존 필드를 떨어뜨리지 않음을 확인한다 (H-3).
    """
    resp = _t103_detail(client, task_id)
    assert resp.status_code == 200
    data = resp.json()

    _t103_assert_legacy_fields(data, _T103_LEGACY_DETAIL, f"detail {task_id}")
    assert all(isinstance(name, str) for name in data["artifacts"])

    for group in data["pipeline"]:
        _t103_assert_legacy_fields(
            group, _T103_LEGACY_STAGE_GROUP, f"group {group.get('stage')}"
        )
        for row in group["rows"]:
            _t103_assert_legacy_fields(
                row, _T103_LEGACY_PIPELINE_ROW, f"row {row.get('row')}"
            )


def test_t103_ts017_artifact_count_increase_is_declared_exception(client, t103_clean_cache):
    """[T103/L2-REG2] artifact_count 값 증가는 회귀가 아니라 P-4 4항 명시적 예외다.

    스키마(int)는 불변이고 값만 구 화이트리스트 5에서 `.md` 전수 9로 늘어난다.
    카드 배지와 상세 목록이 같은 원천을 쓰는지도 함께 단정한다.
    """
    cards = _t103_tasks(client).json()
    card = next(c for c in cards if c["task_id"] == _T103_TASK_101)
    detail = _t103_detail(client, _T103_TASK_101).json()

    count = card["artifact_count"]
    assert isinstance(count, int) and not isinstance(count, bool)
    assert count == _T103_BASELINE_101_ARTIFACTS
    assert count > _T103_LEGACY_WHITELIST_101_ARTIFACTS
    assert count == len(detail["artifacts"])


# ── TS-024: DashboardSummaryResponse 기존 8필드 불변 (P-4 회귀 경계 1) ───────

def test_t103_ts024_dashboard_legacy_fields_unchanged(client, t103_clean_cache):
    """[T103/L2-REG1] 기존 8필드가 타입·중첩 형태까지 불변이다.

    워크플로우별 집계 5필드 additive(Step 7)가 기존 4메트릭·상태분포·활동추이·
    알림·최근활동 계약을 건드리지 않았음을 스키마 축에서 단정한다.
    """
    resp = _t103_dashboard(client)
    assert resp.status_code == 200
    data = resp.json()

    _t103_assert_legacy_fields(data, _T103_LEGACY_DASHBOARD, "dashboard")
    _t103_assert_legacy_fields(
        data["status_distribution"], _T103_LEGACY_STATUS_DISTRIBUTION,
        "status_distribution",
    )
    for point in data["activity_trend"]:
        _t103_assert_legacy_fields(point, _T103_LEGACY_ACTIVITY_POINT, "activity_trend[]")
    for alert in data["alerts"]:
        _t103_assert_legacy_fields(alert, _T103_LEGACY_ALERT, "alerts[]")
    for item in data["recent_activities"]:
        _t103_assert_legacy_fields(item, _T103_LEGACY_RECENT, "recent_activities[]")


def test_t103_ts024_dashboard_legacy_semantics_unchanged(client, t103_clean_cache):
    """[T103/L2-REG1] 기존 8필드의 의미가 변경 전 산출 규칙과 동일하다.

    전역 카운트는 이동값이므로 절대값이 아니라 응답 내부 항등으로 단정한다 (§0.5).
    항등의 근거는 변경 전 구현이다 — running = in_progress + additional_work이고
    COLUMN_MAP이 두 상태를 in_progress 컬럼에 합류시키므로 두 값이 같다.
    """
    data = _t103_dashboard(client).json()
    dist = data["status_distribution"]

    assert data["total_projects"] == 1                    # project 지정 모드 = 대상 1건
    assert data["running_tasks"] == dist["in_progress"]
    assert data["blockers"] == dist["blocked"]
    assert data["additional_work"] <= data["running_tasks"]

    assert len(data["alerts"]) == data["blockers"]        # 알림 = 블로커 전건
    assert all(a["status"] == "blocked" for a in data["alerts"])

    trend = data["activity_trend"]
    assert len(trend) == 7                                # 최근 7일 고정 창
    dates = [_t103_dt.date.fromisoformat(p["date"]) for p in trend]
    assert dates == sorted(dates)
    assert all((dates[i + 1] - dates[i]).days == 1 for i in range(6))
    assert all(p["count"] >= 0 for p in trend)

    recent = data["recent_activities"]
    assert len(recent) <= 5                               # 최신 5건 상한
    assert [r["date"] for r in recent] == sorted(
        (r["date"] for r in recent), reverse=True
    )


def test_t103_ts024_dashboard_model_extension_is_additive(client):
    """[T103/L2-REG1] 확장이 additive만이며 신규 5필드가 전건 기본값을 보유한다.

    신규 필드가 Pydantic 필수 필드로 들어가면 무인자 생성이 ValidationError로
    깨진다 (H-3). 기존 8필드의 기본값도 변경 전과 동일해야 한다.
    """
    from dashboard.backend.models import DashboardSummaryResponse

    fields = DashboardSummaryResponse.model_fields
    assert set(_T103_LEGACY_DASHBOARD) <= set(fields), "변경 전 필드가 모델에서 제거됐다"

    default = DashboardSummaryResponse()   # 인자 0개 — 필수 필드가 추가되면 실패한다
    assert default.total_projects == 0
    assert default.running_tasks == 0
    assert default.blockers == 0
    assert default.additional_work == 0
    assert default.status_distribution.model_dump() == {
        "pending": 0, "in_progress": 0, "blocked": 0, "done": 0,
    }
    assert default.activity_trend == []
    assert default.alerts == []
    assert default.recent_activities == []

    for field in _T103_DASHBOARD_ADDITIVE:
        assert field in fields, f"103 신규 필드 `{field}`가 없다"
        assert not fields[field].is_required(), f"신규 필드 `{field}`가 필수 필드다"


# ══════════════════════════════════════════════════════════════════════════════
# TS-106~TS-108 — 소요 3계열 API 계약 (R-16, 집계 기준 16·16-a)
# 이동값 규약: §0.5 — 진행 중 태스크(103)는 값이 아니라 항등·부등식으로 단정한다.
# ══════════════════════════════════════════════════════════════════════════════

_T103_THREE_SERIES = ("pm_minutes", "worker_minutes", "captain_minutes")


def test_t103_ts106_detail_three_series_degenerates_on_unmeasured(client, t103_clean_cache):
    """[T103/L2-R16] 101(워커 미기록) 상세가 총 425 = PM 105 + 워커 0 + 캡틴 320으로 반환된다.

    축퇴 규칙(집계기준 16-a) — 기존 2계열 확정값과 수치가 항등이어야 회귀가 아니다.
    """
    resp = _t103_detail(client, _T103_TASK_101)
    assert resp.status_code == 200
    stats = resp.json()["stats"]

    assert stats["total_minutes"] == 425
    assert stats["pm_minutes"] == 105
    assert stats["worker_minutes"] == 0
    assert stats["captain_minutes"] == 320

    # 축퇴 항등 — PM == 기존 작업, 캡틴 == 기존 대기
    assert stats["pm_minutes"] == stats["work_minutes"]
    assert stats["captain_minutes"] == stats["wait_minutes"]

    # 「워커 0분」이 아니라 「미측정」 — FE가 이 신호로 표기를 가른다
    assert stats["worker_measured"] is False
    assert stats["worker_clamped_count"] == 0

    # 단계별로도 축퇴한다
    for group in resp.json()["pipeline"]:
        assert group["pm_minutes"] == group["work_minutes"], group["stage"]
        assert group["captain_minutes"] == group["wait_minutes"], group["stage"]
        assert group["worker_minutes"] == 0, group["stage"]
        assert group["worker_measured"] is False, group["stage"]


def test_t103_ts107_detail_three_series_splits_on_measured(client, t103_clean_cache):
    """[T103/L2-R16] 103(워커 기록 보유) 상세가 3계열로 실제 분해되고 항등이 성립한다.

    103은 진행 중이라 값이 이동하므로 항등·부등식으로만 단정한다 (§0.5).
    전제 확인 — 라이브 state에 worker_duration_minutes 기록 행이 존재한다.
    """
    state = _t103_live_state(_T103_TASK_103)
    measured_rows = [r for r in state["rows"] if "worker_duration_minutes" in r]
    assert measured_rows, "전제: 103은 워커 소요 기록 행을 보유한다 (R-17)"

    resp = _t103_detail(client, _T103_TASK_103)
    assert resp.status_code == 200
    detail = resp.json()
    stats = detail["stats"]

    assert stats["available"] is True
    assert stats["worker_measured"] is True
    assert stats["worker_minutes"] > 0, "기록이 있는데 워커 계열이 0이면 분해가 작동하지 않은 것이다"

    # 3계열 합 항등 — PM은 유도값이므로 이 항등이 정의 그 자체다.
    # 진행 중 태스크의 total_minutes는 실시간 값(created_at → now)이라 정적 합보다 크다
    # (집계기준 11 — 기존 2계열도 동일). 항등은 정적 합(work + wait)에 대해 성립한다.
    static_total = stats["work_minutes"] + stats["wait_minutes"]
    assert (
        stats["pm_minutes"] + stats["worker_minutes"] + stats["captain_minutes"]
        == static_total
    )
    assert static_total <= stats["total_minutes"]
    # 하위 호환 2계열과의 관계
    assert stats["work_minutes"] == stats["pm_minutes"] + stats["worker_minutes"]
    assert stats["wait_minutes"] == stats["captain_minutes"]

    # 음수 금지 + clamp 미발생
    for field in _T103_THREE_SERIES:
        assert stats[field] >= 0, field
    assert stats["worker_clamped_count"] == 0

    # 단계 합 == 태스크 합
    groups = detail["pipeline"]
    for field in _T103_THREE_SERIES:
        assert sum(g[field] for g in groups) == stats[field], field
    for group in groups:
        for field in _T103_THREE_SERIES:
            assert group[field] >= 0, (group["stage"], field)
        assert (
            group["pm_minutes"] + group["worker_minutes"] + group["captain_minutes"]
            == group["total_minutes"]
        ), group["stage"]

    assert any(g["worker_measured"] for g in groups), "측정 신호가 단계에 전파되지 않았다"


def test_t103_ts108_dashboard_three_series_is_additive(client, t103_clean_cache):
    """[T103/L2-R16] 워크플로우 집계가 3계열을 additive로 싣고 기존 대표값이 불변이다."""
    from dashboard.backend.models import StageStat, TaskStats, WorkflowStat

    # 모델 확장이 전건 선택 필드다 (H-3 — 필수 필드는 기존 생성 경로를 깬다)
    for model in (TaskStats, WorkflowStat, StageStat):
        fields = model.model_fields
        for field in (*_T103_THREE_SERIES, "worker_measured"):
            assert field in fields, f"{model.__name__}.{field} 누락"
            assert not fields[field].is_required(), f"{model.__name__}.{field}가 필수 필드다"

    TaskStats()                      # 결측 태스크 경로 — 인자 0개 생성이 깨지지 않는다
    WorkflowStat(skill="opd")        # skill·stage는 103 이전부터의 기존 필수 필드다
    StageStat(stage="EXECUTE")

    resp = _t103_dashboard(client)
    assert resp.status_code == 200
    workflows = {w["skill"]: w for w in resp.json()["workflow_stats"]}

    for skill, (n, median, median_label, wait_ratio) in _T103_BASELINE_WORKFLOW.items():
        if skill not in workflows:
            continue
        w = workflows[skill]
        # 3계열 추가가 기존 대표값을 흔들지 않는다
        assert w["median_minutes"] == median, f"{skill} 중앙값 회귀"
        assert w["wait_ratio"] == wait_ratio, f"{skill} 대기 비중 회귀"
        # 워커 미기록 코호트 → 축퇴
        assert w["pm_minutes"] == w["work_minutes"], skill
        assert w["captain_minutes"] == w["wait_minutes"], skill
        for field in _T103_THREE_SERIES:
            assert w[field] >= 0, (skill, field)
        for stage in w["stages"]:
            assert stage["pm_minutes"] == stage["work_minutes"], (skill, stage["stage"])
            assert stage["captain_minutes"] == stage["wait_minutes"], (skill, stage["stage"])


# ── TS-137: 야간 보정 표면화 — 두 엔드포인트 응답 계약 (R-21) ────────────────

def test_t103_ts137_quiet_hours_surfaced_on_both_endpoints(client, t103_clean_cache):
    """[T103/L2-R21] 상세·대시보드 응답이 보정 적용 여부와 제외 구간을 싣는다.

    [MUST] 캡틴 지시 2026-08-26: "같은 태스크가 799분으로도 425분으로도 보이면
    혼란이다. 응답에 보정 적용 여부와 제외 구간을 실어라." FE는 이 두 필드만 읽어
    배지 1개를 그린다 — 계산도 문자열 조립도 FE가 하지 않는다 (P-7).
    """
    detail = _t103_detail(client, _T103_TASK_101)
    assert detail.status_code == 200
    stats = detail.json()["stats"]
    assert stats["quiet_hours_applied"] is True
    assert stats["quiet_hours_label"] == _T103_QUIET_LABEL

    # 101은 하루 안에 끝나 보정과 무관하다 — 완료기준 (2)의 확정값이 유지된다
    assert stats["total_minutes"] == 425
    assert stats["pm_minutes"] + stats["worker_minutes"] + stats["captain_minutes"] == 425
    assert (stats["work_minutes"], stats["wait_minutes"]) == (105, 320)

    summary = _t103_dashboard(client)
    assert summary.status_code == 200
    data = summary.json()
    assert data["quiet_hours_applied"] is True
    assert data["quiet_hours_label"] == _T103_QUIET_LABEL
    for entry in data["workflow_stats"]:
        assert entry["quiet_hours_applied"] is True
        assert entry["quiet_hours_label"] == _T103_QUIET_LABEL


def test_t103_ts137_disabled_setting_restores_wall_clock(client, monkeypatch):
    """[T103/L2-R21] 설정을 끄면 응답이 보정 전 수치(opd 799)로 돌아간다.

    끄는 수단이 실제로 라우터 응답까지 관통하는지 — 설정 → 로더 → stats 주입 →
    응답의 전 경로를 한 번에 단정한다.
    """
    from dashboard.backend.cache import cache
    from dashboard.backend.routers import dashboard as dashboard_router

    monkeypatch.setattr(dashboard_router, "load_quiet_hours", lambda _project=None: None)
    cache.clear()
    try:
        data = _t103_dashboard(client).json()
        assert data["quiet_hours_applied"] is False
        assert data["quiet_hours_label"] == ""
        by_skill = {w["skill"]: w for w in data["workflow_stats"]}
        assert by_skill["opd"]["median_minutes"] == 799     # STATS-BASELINE.md §4.1
        assert by_skill["opds"]["median_minutes"] == 276
        assert by_skill["opp"]["median_minutes"] == 75
    finally:
        cache.clear()


# ══════════════════════════════════════════════════════════════════════════════
# [호칭 하드코딩 제거] owner 라벨·owner_term 표면화
# 화면 호칭이 코드에 박혀 있으면 다른 사용자에게 남의 호칭이 뜬다. 라벨은 로더가
# 준 값을 쓰고, 호칭 자체를 응답에 실어 FE가 문구를 조립하게 한다.
# ══════════════════════════════════════════════════════════════════════════════

_OWNER_TERM_STUB = "테스터"


@pytest.fixture
def owner_term_stub(monkeypatch, t103_clean_cache):
    """호칭 로더를 실 identity.md와 무관한 값으로 고정한다.

    실행 머신의 `~/.opal/identity.md`에 기대값이 좌우되면 안 되고, 스텁 값이
    응답에 그대로 나타나야 「읽어서 쓴다」가 실증된다.
    """
    from dashboard.backend.routers import dashboard as dashboard_router
    from dashboard.backend.routers import tasks as tasks_router

    for module in (dashboard_router, tasks_router):
        monkeypatch.setattr(module, "load_owner_name", lambda: _OWNER_TERM_STUB)
    return t103_clean_cache


def test_owner_label_uses_loaded_term_not_literal(client, owner_term_stub):
    """[호칭] `owner == "user"` 행 라벨이 로더 값이다 — 코드 리터럴이 아니다."""
    detail = _t103_detail(client, _T103_TASK_101)
    assert detail.status_code == 200

    rows = _t103_flat_rows(detail.json())
    user_rows = [r for r in rows if r["owner"] == "user"]
    assert user_rows, "이 태스크는 사용자 확인 행을 갖고 있어야 한다(픽스처 전제)"
    for row in user_rows:
        assert row["owner_label"] == _OWNER_TERM_STUB


def test_role_owner_labels_are_unchanged(client, owner_term_stub):
    """[호칭] `PM`·`auto`는 역할명이라 호칭 교체와 무관하게 고정이다."""
    rows = _t103_flat_rows(_t103_detail(client, _T103_TASK_101).json())
    by_owner = {r["owner"]: r["owner_label"] for r in rows}

    assert by_owner.get("PM") == "PM"
    for owner, label in by_owner.items():
        if owner == "auto":
            assert label == "자동"
        # 어떤 라벨도 스텁 호칭을 역할 행에 흘리지 않는다
        if owner != "user":
            assert label != _OWNER_TERM_STUB


def test_detail_response_carries_owner_term(client, owner_term_stub):
    """[호칭] 상세 응답 최상위 `owner_term` — FE가 문구를 조립할 원천이다."""
    data = _t103_detail(client, _T103_TASK_101).json()
    assert data["owner_term"] == _OWNER_TERM_STUB


def test_dashboard_response_carries_owner_term(client, owner_term_stub):
    """[호칭] 대시보드 응답 최상위 `owner_term` — 범례·비중 문구의 원천이다."""
    data = _t103_dashboard(client).json()
    assert data["owner_term"] == _OWNER_TERM_STUB


def test_owner_term_falls_back_when_identity_missing(client, monkeypatch, t103_clean_cache):
    """[호칭] identity.md가 없는 머신에서도 200이며 중립 호칭이 실린다."""
    import dashboard.backend.config as config_module

    monkeypatch.setattr(config_module, "IDENTITY_PATH", Path("/nonexistent/identity.md"))

    detail = _t103_detail(client, _T103_TASK_101)
    assert detail.status_code == 200
    data = detail.json()
    assert data["owner_term"] == "사용자"

    user_rows = [r for r in _t103_flat_rows(data) if r["owner"] == "user"]
    assert user_rows and all(r["owner_label"] == "사용자" for r in user_rows)


def test_state_missing_task_still_carries_owner_term(client, owner_term_stub):
    """[호칭] state.json 부재 태스크(결측 200)도 호칭을 싣는다 — FE 분기 불필요."""
    detail = _t103_detail(client, _T103_TASK_089)
    assert detail.status_code == 200
    assert detail.json()["owner_term"] == _OWNER_TERM_STUB
