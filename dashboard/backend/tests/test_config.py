"""
@header {
  "module": "tests.test_config",
  "layer": "test",
  "domain": "console",
  "description": "config.load_config()의 prewarm_projects 파싱·타입 가드 테스트(T060 F-1, RED). 5variant: 키 부재/빈 배열/문자열(비-list)/dict(비-list)/정상 배열(경로 2개+비str 원소 혼합) → 부재·빈·비-list는 예외 없이 []로 폴백, 정상 배열은 str 원소만 로드된다(H-4). CONFIG_PATH를 tmp_path로 monkeypatch하여 실제 ~/.opal/console.config.json과 격리. [T061] config.save_config(머지 보존, H-3)·config._atomic_write_json(temp+os.replace 원자 쓰기·동시 쓰기 직렬화, H-2) 검증. save_project_local 계약(TestSaveProjectLocal)은 T061 범위 축소로 프로젝트 로컬 설정 편집이 제외되어 삭제됨.",
  "exports": ["TestConfigPrewarmProjects", "TestSaveConfigMergePreservation", "TestAtomicWriteJson"],
  "depends": ["config"],
  "task": "061",
  "scenarios": ["S-2", "S-3"],
  "changelog": [
    "2026-07-14 T061 RED: config.save_config 머지 보존(S-3)·config._atomic_write_json 원자 쓰기+동시성(S-2)·config.save_project_local 원자 쓰기 실패 테스트 추가 — 구현 전 RED 트랙(red-first.md), 작성자(opal-test-agent)≠구현자(opal-be-agent)",
    "2026-07-14 T061 범위 축소: TestSaveProjectLocal 클래스 삭제(save_project_local 제거에 따른 계약 삭제) — TestSaveConfigMergePreservation·TestAtomicWriteJson은 유지"
  ]
}
"""
from __future__ import annotations

import json
import threading
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


# ── [T061] config.save_config / _atomic_write_json ───────────────────────────
# PLAN.md §3.1.2 설계 시그니처 대상.


def _isolate_config_path(monkeypatch: pytest.MonkeyPatch, config_path: Path):
    """config.CONFIG_PATH를 tmp 경로로 격리(로드 없이 몽키패치만 수행)하고 config 모듈을 반환."""
    import dashboard.backend.config as config_module

    monkeypatch.setattr(config_module, "CONFIG_PATH", config_path)
    return config_module


class TestSaveConfigMergePreservation:
    """[T061/L1-R3] config.save_config 머지 보존 — 부분 갱신 시 기존/미지 키 유실 금지 (H-3, RED, S-3).

    대상: config.save_config(updates: dict) -> dict (미구현 — PLAN §3.1.2 대상).
    현재는 함수 자체가 없으므로 AttributeError가 정상(RED)이다.
    """

    def test_partial_update_preserves_existing_keys(self, tmp_path, monkeypatch):
        """[T061/L1-R3] (a) prewarm_projects만 갱신 → scan_roots/scan_depth/exclude 등 기존 키 보존."""
        config_path = _write_config(
            tmp_path,
            {
                "scan_roots": ["/tmp/ws"],
                "scan_depth": 2,
                "exclude": ["backup"],
                "prewarm_projects": [],
                "future_key": "keep-me",
            },
        )
        config_module = _isolate_config_path(monkeypatch, config_path)
        snapshot = config_module.save_config({"prewarm_projects": ["/tmp/ws/proj-a"]})

        assert snapshot["prewarm_projects"] == ["/tmp/ws/proj-a"]
        assert snapshot["scan_roots"] == ["/tmp/ws"]
        assert snapshot["scan_depth"] == 2
        assert snapshot["exclude"] == ["backup"]
        assert snapshot["future_key"] == "keep-me", "미지 future 키가 갱신 후 유실됨(H-3)"

    def test_existing_key_change_reflected(self, tmp_path, monkeypatch):
        """[T061/L1-R3] (b) scan_depth 기존 키 변경 → 반영."""
        config_path = _write_config(
            tmp_path,
            {"scan_roots": ["/tmp/ws"], "scan_depth": 2, "future_key": "keep-me"},
        )
        config_module = _isolate_config_path(monkeypatch, config_path)
        snapshot = config_module.save_config({"scan_depth": 5})

        assert snapshot["scan_depth"] == 5
        assert snapshot["future_key"] == "keep-me"

    def test_partial_update_reload_from_disk_matches(self, tmp_path, monkeypatch):
        """[T061/L1-R3] (c) 부분 갱신 후 재로드(파일 재읽기) 시 갱신값+future_key 일치."""
        config_path = _write_config(
            tmp_path,
            {
                "scan_roots": ["/tmp/ws"],
                "prewarm_projects": [],
                "future_key": "keep-me",
            },
        )
        config_module = _isolate_config_path(monkeypatch, config_path)
        config_module.save_config({"prewarm_projects": ["/tmp/ws/proj-a"]})

        reloaded = json.loads(config_path.read_text(encoding="utf-8"))
        assert reloaded["prewarm_projects"] == ["/tmp/ws/proj-a"]
        assert reloaded["scan_roots"] == ["/tmp/ws"]
        assert reloaded["future_key"] == "keep-me"


class TestAtomicWriteJson:
    """[T061/L2-R1] config._atomic_write_json — temp 파일 + os.replace 원자적 쓰기 (H-2, RED, S-2).

    대상: config._atomic_write_json(path, data) -> None + config.save_config의
    동시 쓰기 직렬화(_WRITE_LOCK) (미구현 — PLAN §3.1.2 대상).
    """

    def test_writes_valid_json_and_no_temp_leftover(self, tmp_path):
        """[T061/L2-R1] 쓰기 후 대상 파일 파스 성공 + temp 잔존 파일 0."""
        import dashboard.backend.config as config_module

        target = tmp_path / "atomic-target.json"
        config_module._atomic_write_json(target, {"a": 1, "b": [1, 2]})

        assert target.exists()
        loaded = json.loads(target.read_text(encoding="utf-8"))
        assert loaded == {"a": 1, "b": [1, 2]}

        leftovers = [p for p in tmp_path.iterdir() if ".tmp." in p.name]
        assert leftovers == [], f"temp 파일 잔존: {leftovers}"

    def test_concurrent_save_config_no_key_loss(self, tmp_path, monkeypatch):
        """[T061/L2-R1] 스레드 2개 동시 save_config(서로 다른 키) → 두 갱신 모두 반영,
        future_key 보존, JSON 파스 성공(파손 0), temp 잔존 0."""
        config_path = _write_config(
            tmp_path,
            {"scan_roots": ["/tmp/ws"], "future_key": "keep-me"},
        )
        config_module = _isolate_config_path(monkeypatch, config_path)

        barrier = threading.Barrier(2)
        errors: list[Exception] = []

        def _writer(update: dict) -> None:
            try:
                barrier.wait(timeout=5)
                config_module.save_config(update)
            except Exception as exc:  # pragma: no cover - 진단용
                errors.append(exc)

        t1 = threading.Thread(target=_writer, args=({"scan_depth": 9},))
        t2 = threading.Thread(target=_writer, args=({"exclude": ["node_modules"]},))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        assert not errors, f"동시 쓰기 중 예외 발생: {errors}"

        # 파손 없이 파스 가능해야 함 — 두 갱신 모두 반영(키 유실 0)
        reloaded = json.loads(config_path.read_text(encoding="utf-8"))
        assert reloaded["scan_depth"] == 9, "동시 쓰기 중 한쪽 키가 유실됨(H-2)"
        assert reloaded["exclude"] == ["node_modules"], "동시 쓰기 중 한쪽 키가 유실됨(H-2)"
        assert reloaded["future_key"] == "keep-me"

        leftovers = [p for p in tmp_path.iterdir() if ".tmp." in p.name]
        assert leftovers == [], f"temp 파일 잔존: {leftovers}"
