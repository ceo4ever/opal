"""
@header {
  "module": "tests.test_cache",
  "layer": "test",
  "domain": "console",
  "description": "[T103/R1 RED] cache.py mtime 무효화 실동작 계약 (TS-016). P-8 시계 혼용 결함 회귀 방지 — set()은 time.monotonic() 기반 expires_at을 저장하는데 get()은 이를 epoch os.path.getmtime()과 직접 비교해 source_path 지정 항목이 상시 무효화된다. 파일 미변경 시 TTL 내 히트 / touch 후 즉시 미스 / source_path=None은 TTL 축만 / 공개 시그니처·TTL_SECONDS 불변 4계약을 단정한다. mtime은 os.utime()으로 고정 주입해 벽시계 해상도 의존을 제거했다. RED-first — 작성자(opal-test-agent, mode: red) != 구현자(opal-be-agent).",
  "exports": [
    "test_cache_hit_when_source_file_unchanged",
    "test_cache_miss_after_source_file_touched",
    "test_cache_hit_without_source_path",
    "test_cache_public_signature_unchanged",
    "test_cache_missing_source_file_does_not_raise"
  ],
  "depends": ["cache"],
  "task": "103",
  "scenarios": ["TS-016"],
  "changelog": [
    "2026-08-25 T103 R1 RED: TS-016 cache.py mtime 무효화 실동작 실패 테스트 신규 — 구현(Step 2) 전 RED 트랙(red-first.md §1), 작성자!=구현자(동 §2)"
  ]
}
"""
from __future__ import annotations

import os
import time

import pytest


@pytest.fixture
def store():
    """매 테스트마다 격리된 CacheStore 인스턴스 (전역 cache 오염 금지)."""
    from dashboard.backend.cache import CacheStore
    return CacheStore()


@pytest.fixture
def source_file(tmp_path):
    """FX-TOUCH — 임시 state.json. mtime을 과거로 고정 주입해 결정론을 확보한다."""
    path = tmp_path / "state.json"
    path.write_text('{"rows": []}', encoding="utf-8")
    past = time.time() - 600
    os.utime(path, (past, past))
    return str(path)


# ── TS-016 (a) 파일 미변경 → TTL 내 캐시 히트 ────────────────────────────────

def test_cache_hit_when_source_file_unchanged(store, source_file):
    """[T103/L1-R12] source_path 지정 항목은 파일이 변하지 않으면 TTL 내 히트한다.

    RED 기대 실패: 교정 전 get()이 monotonic 기반 cached_since(약 6.1e5)를
    epoch mtime(약 1.78e9)과 비교해 current_mtime > cached_since가 항상 참이 되고,
    저장 직후 조회조차 None을 반환한다 (cache.py:45-51·:58-60).
    """
    store.set("k-unchanged", {"total_minutes": 425}, source_path=source_file)

    assert store.get("k-unchanged") == {"total_minutes": 425}

    # 연속 조회에서도 히트가 유지된다 (상시 무효화 아님)
    assert store.get("k-unchanged") == {"total_minutes": 425}


# ── TS-016 (b) 파일 touch → 즉시 미스 ────────────────────────────────────────

def test_cache_miss_after_source_file_touched(store, source_file):
    """[T103/L1-R12] source_path 파일의 mtime이 갱신되면 TTL 내라도 즉시 미스한다."""
    store.set("k-touched", {"total_minutes": 425}, source_path=source_file)
    assert store.get("k-touched") == {"total_minutes": 425}, "선행 조건: touch 전에는 히트"

    # 캐시 저장 이후 시각으로 mtime을 명시 주입 (touch와 동일 의미, 해상도 비의존)
    future = time.time() + 60
    os.utime(source_file, (future, future))

    assert store.get("k-touched") is None


# ── TS-016 (c) source_path 미지정 → TTL 축만 ─────────────────────────────────

def test_cache_hit_without_source_path(store):
    """[T103/L1-R12] source_path 없는 항목은 mtime 축과 무관하게 TTL 내 히트한다."""
    store.set("k-nosource", ["a", "b"])
    assert store.get("k-nosource") == ["a", "b"]


# ── TS-016 (d) 공개 시그니처·TTL 불변 ────────────────────────────────────────

def test_cache_public_signature_unchanged(store, source_file):
    """[T103/L1-R12] get/set/invalidate/clear 4종 공개 시그니처와 TTL_SECONDS는 불변이다."""
    import inspect

    from dashboard.backend import cache as cache_mod

    assert cache_mod.TTL_SECONDS == 30.0

    assert list(inspect.signature(cache_mod.CacheStore.get).parameters) == ["self", "key"]
    assert list(inspect.signature(cache_mod.CacheStore.set).parameters) == [
        "self", "key", "data", "source_path",
    ]
    assert list(inspect.signature(cache_mod.CacheStore.invalidate).parameters) == ["self", "key"]
    assert list(inspect.signature(cache_mod.CacheStore.clear).parameters) == ["self"]

    # invalidate / clear 동작 불변
    store.set("k-inv", 1, source_path=source_file)
    store.invalidate("k-inv")
    assert store.get("k-inv") is None

    store.set("k-clr", 2, source_path=source_file)
    store.clear()
    assert store.get("k-clr") is None


def test_cache_missing_source_file_does_not_raise(store, tmp_path):
    """[T103/L1-R12] source_path가 존재하지 않는 경로여도 예외 없이 히트한다."""
    store.set("k-missing", "v", source_path=str(tmp_path / "does-not-exist.json"))
    assert store.get("k-missing") == "v"
