"""
@header {
  "module": "tests.test_main",
  "layer": "test",
  "domain": "console",
  "description": "S-5: FastAPI main.py 보안 바인딩(127.0.0.1) + /health 엔드포인트 계약 검증. RED-first. [T021/L2-R4sec]",
  "exports": ["test_health_endpoint", "test_host_binding_is_localhost", "test_no_0000_in_code"],
  "depends": ["main"]
}
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient


# ── S-5: 보안 바인딩 정적 검사 ──────────────────────────────────────────────

def test_host_binding_is_localhost():
    """uvicorn.run 호출의 host 인자가 127.0.0.1이어야 한다 (0.0.0.0 금지, H-7)."""
    import pathlib
    main_path = pathlib.Path(__file__).parent.parent / "main.py"
    content = main_path.read_text(encoding="utf-8")
    # 127.0.0.1 명시 존재 (uvicorn.run 호출부에)
    assert 'host="127.0.0.1"' in content or "host='127.0.0.1'" in content, \
        "uvicorn host must be 127.0.0.1"


def test_no_0000_in_uvicorn_call():
    """uvicorn.run 호출 인자에 0.0.0.0 이 없어야 한다 (H-7).

    host= 할당 라인에서 # 이후 인라인 주석을 제거한 코드 부분만 검사한다.
    """
    import pathlib
    main_path = pathlib.Path(__file__).parent.parent / "main.py"
    lines = main_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        stripped = line.strip()
        # 독스트링·주석 전용 라인 제외
        if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        # 인라인 주석 제거 (# 이후 삭제)
        code_part = stripped.split("#")[0]
        assert "0.0.0.0" not in code_part, \
            f"Forbidden 0.0.0.0 in code: {line!r} (H-7)"


# ── /health 엔드포인트 계약 ──────────────────────────────────────────────────

@pytest.fixture
def client():
    from dashboard.backend.main import app
    return TestClient(app)


def test_health_endpoint_returns_200(client):
    """/health 는 HTTP 200 반환."""
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_endpoint_schema(client):
    """/health 응답은 {status: str, version: str} 포함."""
    resp = client.get("/health")
    data = resp.json()
    assert "status" in data, "/health must have 'status' field"
    assert "version" in data, "/health must have 'version' field"
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)


def test_health_status_value(client):
    """/health status 는 'ok' 값."""
    resp = client.get("/health")
    data = resp.json()
    assert data["status"] == "ok"


def test_cors_allow_origins_includes_localhost(client):
    """CORS 설정에 localhost:5173 이 허용 오리진으로 등록돼야 한다 (dev 모드)."""
    import dashboard.backend.main as m
    # CORS_ORIGINS 변수 또는 소스에서 확인
    origins = getattr(m, "CORS_ORIGINS", None)
    if origins is not None:
        assert any("localhost:5173" in o for o in origins), \
            "CORS_ORIGINS must include localhost:5173"
    else:
        import inspect
        source = inspect.getsource(m)
        assert "localhost:5173" in source, "CORS must allow localhost:5173 for dev mode"
