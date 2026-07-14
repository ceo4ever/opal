"""
@header {
  "module": "tests.test_config",
  "layer": "test",
  "domain": "console",
  "description": "config.load_config()의 prewarm_projects 파싱·타입 가드 테스트(T060 F-1, RED). 5variant: 키 부재/빈 배열/문자열(비-list)/dict(비-list)/정상 배열(경로 2개+비str 원소 혼합) → 부재·빈·비-list는 예외 없이 []로 폴백, 정상 배열은 str 원소만 로드된다(H-4). CONFIG_PATH를 tmp_path로 monkeypatch하여 실제 ~/.opal/console.config.json과 격리.",
  "exports": ["TestConfigPrewarmProjects"],
  "depends": ["config"],
  "task": "060",
  "scenarios": ["S-1"]
}
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_config(tmp_path: Path, data: dict) -> Path:
    """tmp_path에 console.config.json 형식의 JSON 파일을 작성하고 경로를 반환."""
    config_file = tmp_path / "console.config.json"
    config_file.write_text(json.dumps(data), encoding="utf-8")
    return config_file


def _load_with_isolated_config_path(monkeypatch: pytest.MonkeyPatch, config_path: Path):
    """config.CONFIG_PATH를 tmp 경로로 격리한 뒤 load_config()를 호출."""
    import dashboard.backend.config as config_module

    monkeypatch.setattr(config_module, "CONFIG_PATH", config_path)
    return config_module.load_config()


class TestConfigPrewarmProjects:
    """[T060/L1-F1] ConsoleConfig.prewarm_projects 5variant 파싱·타입 가드 (F-1 AC, H-4, RED).

    대상: config.py `ConsoleConfig.prewarm_projects` 필드 + `load_config()` 타입 가드
    (미구현 — PLAN §3.1.2 `_coerce_str_list` 헬퍼 대상). 현재는 필드 자체가 없으므로
    `cfg.prewarm_projects` 접근 시 AttributeError가 정상(RED)이다.
    """

    def test_key_absent_defaults_to_empty_list(self, tmp_path, monkeypatch):
        """[T060/L1-F1] prewarm_projects 키 부재 → []."""
        config_path = _write_config(tmp_path, {"scan_roots": ["/x"]})
        cfg = _load_with_isolated_config_path(monkeypatch, config_path)
        assert cfg.prewarm_projects == []

    def test_empty_list_stays_empty(self, tmp_path, monkeypatch):
        """[T060/L1-F1] prewarm_projects 빈 배열 → []."""
        config_path = _write_config(tmp_path, {"prewarm_projects": []})
        cfg = _load_with_isolated_config_path(monkeypatch, config_path)
        assert cfg.prewarm_projects == []

    def test_string_value_falls_back_to_empty_list(self, tmp_path, monkeypatch):
        """[T060/L1-F1] prewarm_projects가 문자열(비-list) → 예외 없이 []로 폴백(H-4)."""
        config_path = _write_config(tmp_path, {"prewarm_projects": "/not/a/list"})
        cfg = _load_with_isolated_config_path(monkeypatch, config_path)
        assert cfg.prewarm_projects == []

    def test_dict_value_falls_back_to_empty_list(self, tmp_path, monkeypatch):
        """[T060/L1-F1] prewarm_projects가 dict(비-list) → 예외 없이 []로 폴백(H-4)."""
        config_path = _write_config(tmp_path, {"prewarm_projects": {"a": 1}})
        cfg = _load_with_isolated_config_path(monkeypatch, config_path)
        assert cfg.prewarm_projects == []

    def test_valid_list_loads_str_elements_only(self, tmp_path, monkeypatch):
        """[T060/L1-F1] 정상 배열(경로 2개 + 비str 원소 혼합) → str 원소만 로드."""
        config_path = _write_config(
            tmp_path,
            {"prewarm_projects": ["/proj/one", "/proj/two", 123, None]},
        )
        cfg = _load_with_isolated_config_path(monkeypatch, config_path)
        assert cfg.prewarm_projects == ["/proj/one", "/proj/two"]
