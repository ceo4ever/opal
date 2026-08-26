"""
@header {
  "module": "cache",
  "layer": "util",
  "domain": "console",
  "description": "in-memory TTL 캐시(30초) + os.path.getmtime() 무효화. 키→(data, expires_at, source_path, set_wall) 4-tuple 저장. TTL 축은 time.monotonic() 기준 expires_at, mtime 무효화 축은 time.time() 기준 set_wall로 시계를 분리한다 — 두 축을 혼용하면 epoch mtime > monotonic 값이 항상 참이 되어 source_path 지정 항목이 상시 무효화된다(T103 P-8). 읽기 전용 — 소스 파일 불변",
  "exports": ["CacheStore", "cache"],
  "depends": [],
  "changelog": [
    "2026-08-25 T103 Step2: mtime 무효화 비교 기준을 monotonic 파생값(expires_at - TTL)에서 wall-clock set_wall로 교정 — _store 3-tuple → 4-tuple. 공개 시그니처·TTL_SECONDS·키 전략·invalidate 무변경 (P-8, TS-016)"
  ]
}
"""
from __future__ import annotations

import os
import time
from typing import Any

TTL_SECONDS = 30.0


class CacheStore:
    """in-memory TTL 캐시.

    항목: {key: (data, expires_at, source_path | None, set_wall)}
    - TTL 30초 — expires_at은 time.monotonic() 축
    - source_path 지정 시: os.path.getmtime() 변경으로도 무효화 (H-6 준수)
      비교 기준 set_wall은 time.time() 축이다. mtime과 같은 시계여야 한다 (P-8).
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float, str | None, float]] = {}

    def get(self, key: str) -> Any | None:
        """캐시 조회. 없거나 만료됐으면 None."""
        if key not in self._store:
            return None
        data, expires_at, source_path, set_wall = self._store[key]

        # TTL 만료 확인
        if time.monotonic() > expires_at:
            del self._store[key]
            return None

        # mtime 무효화 확인
        if source_path and os.path.isfile(source_path):
            try:
                current_mtime = os.path.getmtime(source_path)
                # mtime이 캐시 저장 시각(wall-clock) 이후 변경됐는지 체크
                if current_mtime > set_wall:
                    del self._store[key]
                    return None
            except OSError:
                pass

        return data

    def set(self, key: str, data: Any, source_path: str | None = None) -> None:
        """캐시 저장. TTL=30초."""
        expires_at = time.monotonic() + TTL_SECONDS
        self._store[key] = (data, expires_at, source_path, time.time())

    def invalidate(self, key: str) -> None:
        """강제 무효화."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """전체 캐시 초기화."""
        self._store.clear()


# 전역 캐시 인스턴스
cache = CacheStore()
