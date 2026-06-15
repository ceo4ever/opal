"""
@header {
  "module": "cache",
  "layer": "util",
  "domain": "console",
  "description": "in-memory TTL 캐시(30초) + os.path.getmtime() 무효화. 키→(data, expires_at, mtime) 저장. 읽기 전용 — 소스 파일 불변",
  "exports": ["CacheStore", "cache"],
  "depends": []
}
"""
from __future__ import annotations

import os
import time
from typing import Any

TTL_SECONDS = 30.0


class CacheStore:
    """in-memory TTL 캐시.

    항목: {key: (data, expires_at, source_path | None)}
    - TTL 30초
    - source_path 지정 시: os.path.getmtime() 변경으로도 무효화 (H-6 준수)
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float, str | None]] = {}

    def get(self, key: str) -> Any | None:
        """캐시 조회. 없거나 만료됐으면 None."""
        if key not in self._store:
            return None
        data, expires_at, source_path = self._store[key]

        # TTL 만료 확인
        if time.monotonic() > expires_at:
            del self._store[key]
            return None

        # mtime 무효화 확인
        if source_path and os.path.isfile(source_path):
            try:
                current_mtime = os.path.getmtime(source_path)
                # mtime이 캐시 생성 이후 변경됐는지 체크
                cached_since = expires_at - TTL_SECONDS
                if current_mtime > cached_since:
                    del self._store[key]
                    return None
            except OSError:
                pass

        return data

    def set(self, key: str, data: Any, source_path: str | None = None) -> None:
        """캐시 저장. TTL=30초."""
        expires_at = time.monotonic() + TTL_SECONDS
        self._store[key] = (data, expires_at, source_path)

    def invalidate(self, key: str) -> None:
        """강제 무효화."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """전체 캐시 초기화."""
        self._store.clear()


# 전역 캐시 인스턴스
cache = CacheStore()
