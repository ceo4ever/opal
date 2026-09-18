"""
@header {
  "module": "test_cors_env",
  "layer": "test",
  "domain": "console",
  "description": "S-4 — OPAL_CONSOLE_CORS_ORIGINS env 주입 CORS 허용 목록 계약을 검증한다. main.py가 os.getenv(OPAL_CONSOLE_CORS_ORIGINS)를 소비해 미주입 시 기존 고정 2종을, 주입 시 유효 origin만 추가 허용하는지 확인한다.",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "scenarios": ["S-4"],
  "exports": ["test_env_unset_keeps_default_origins", "test_env_single_origin_appended", "test_env_multiple_origins_appended", "test_env_invalid_entries_excluded", "test_cors_middleware_options_unchanged"]
}
"""
from __future__ import annotations

import importlib

import pytest


_DEFAULT_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


@pytest.fixture
def reload_main(monkeypatch):
    """OPAL_CONSOLE_CORS_ORIGINS를 설정/해제한 뒤 main 모듈을 reload하고, 테스트 종료 시 원복한다."""
    import dashboard.backend.main as m

    def _reload(env_value: str | None):
        if env_value is None:
            monkeypatch.delenv("OPAL_CONSOLE_CORS_ORIGINS", raising=False)
        else:
            monkeypatch.setenv("OPAL_CONSOLE_CORS_ORIGINS", env_value)
        importlib.reload(m)
        return m

    yield _reload

    monkeypatch.delenv("OPAL_CONSOLE_CORS_ORIGINS", raising=False)
    importlib.reload(m)


def test_env_unset_keeps_default_origins(reload_main):
    m = reload_main(None)
    assert m.CORS_ORIGINS == _DEFAULT_DEV_ORIGINS


def test_env_single_origin_appended(reload_main):
    m = reload_main("http://127.0.0.1:5555")
    assert m.CORS_ORIGINS == _DEFAULT_DEV_ORIGINS + ["http://127.0.0.1:5555"]


def test_env_multiple_origins_appended(reload_main):
    m = reload_main("http://127.0.0.1:5555,http://127.0.0.1:6666")
    assert m.CORS_ORIGINS == _DEFAULT_DEV_ORIGINS + [
        "http://127.0.0.1:5555",
        "http://127.0.0.1:6666",
    ]


def test_env_invalid_entries_excluded(reload_main):
    m = reload_main("*,${OPAL_E2E_FRONTEND_PORT},   ,http://127.0.0.1:5555")
    assert "*" not in m.CORS_ORIGINS
    assert not any("${" in o for o in m.CORS_ORIGINS)
    assert m.CORS_ORIGINS == _DEFAULT_DEV_ORIGINS + ["http://127.0.0.1:5555"]


def test_cors_middleware_options_unchanged(reload_main):
    m = reload_main("http://127.0.0.1:5555")
    cors_entry = next(
        mw for mw in m.app.user_middleware if "CORSMiddleware" in str(mw.cls)
    )
    kwargs = cors_entry.kwargs
    assert kwargs["allow_credentials"] is False
    assert kwargs["allow_methods"] == ["GET", "POST"]
    assert kwargs.get("allow_origin_regex") is None
    assert "*" not in kwargs["allow_origins"]
