"""
@header {
  "module": "adapters.brain_policy",
  "layer": "service",
  "domain": "console",
  "description": "구형 Brain(claude -p 서브프로세스 경로) 사용 정책의 프로세스 단일 소유자. 저장 위치는 console.config.json의 legacy_brain_enabled이며 JSON true일 때만 켜짐으로 해석한다(키 없음·비불리언·파손은 꺼짐, prewarm_projects·업그레이드는 무관). 값은 첫 사용(is_enabled·spawn_guard·set_enabled 최초 호출) 또는 reload_from_config() 호출 시 config.load_legacy_brain_enabled()로 읽고, 이후 변경은 set_enabled(bool)만 한다(메모리 반영만 — 설정 파일 저장은 호출자 책임). 하나의 threading.Lock이 set_enabled와 spawn_guard(최종 launch 허가+프로세스 시작)를 직렬화하므로 set_enabled(False)가 반환된 뒤에는 어떤 경로도 새 프로세스를 시작할 수 없고, 이미 시작된 turn은 끝까지 진행한다. spawn_guard()는 컨텍스트 매니저이며 꺼짐이면 LegacyBrainDisabled(RuntimeError 하위)를 던지고, 켜짐이면 본문(Popen 시작)이 예외 없이 끝난 직후 running_turns를 1 올리고 turn 핸들을 돌려준다. 호출자는 turn이 끝날 때(finally) 핸들의 finish()를 호출해 running_turns를 내린다(중복 호출 안전). 락은 시작 구간에만 잡고 communicate 대기는 락 밖이다. require_enabled()는 꺼짐이면 LegacyBrainDisabled를 던지는 조기 게이트이고, 최종 방어선은 spawn_guard다.",
  "exports": ["LegacyBrainDisabled", "is_enabled", "set_enabled", "spawn_guard", "running_turns", "reload_from_config", "require_enabled"],
  "depends": ["config"],
  "task": "179-261001-opd-콘솔-POST-인증-게이트"
}
"""
from __future__ import annotations

import contextlib
import logging
import threading
from typing import Iterator

from dashboard.backend import config

logger = logging.getLogger(__name__)


class LegacyBrainDisabled(RuntimeError):
    """구형 Brain이 꺼져 있어 spawn·질의가 거절됨."""


class _Turn:
    """시작된 turn 1건의 핸들. finish()는 running_turns를 정확히 1회만 내린다."""

    def __init__(self) -> None:
        self._done = False

    def finish(self) -> None:
        with _state_lock:
            if self._done:
                return
            self._done = True
            _state["running_turns"] -= 1


# 정책 상태: 하나의 락이 enabled 변경과 spawn 허가+시작을 직렬화한다(D-16).
_lock = threading.RLock()       # spawn_guard 본문 안에서 is_enabled 등 재진입 허용
_state_lock = threading.Lock()  # running_turns 카운터 전용(락 순서: _lock → _state_lock)
_state: dict = {"enabled": False, "loaded": False, "running_turns": 0}


def _ensure_loaded() -> None:
    """첫 사용 시 설정에서 한 번 읽는다(이후 변경은 set_enabled만)."""
    if _state["loaded"]:
        return
    with _lock:
        if not _state["loaded"]:
            _state["enabled"] = config.load_legacy_brain_enabled() is True
            _state["loaded"] = True


def reload_from_config() -> bool:
    """호출 시점의 config.CONFIG_PATH를 다시 읽어 정책을 갱신한다. 새 값을 돌려준다."""
    with _lock:
        _state["enabled"] = config.load_legacy_brain_enabled() is True
        _state["loaded"] = True
        return _state["enabled"]


def is_enabled() -> bool:
    _ensure_loaded()
    return bool(_state["enabled"])


def set_enabled(enabled: bool) -> None:
    """메모리 정책을 바꾼다. 끄기는 반환 시점부터 새 spawn을 막는다(진행 중 turn은 유지)."""
    with _lock:
        _state["enabled"] = bool(enabled)
        _state["loaded"] = True
    logger.info("[brain] legacy_brain enabled=%s", bool(enabled))


def running_turns() -> int:
    with _state_lock:
        return int(_state["running_turns"])


def require_enabled() -> None:
    """꺼짐이면 LegacyBrainDisabled. 조기 게이트(최종 방어선은 spawn_guard)."""
    if not is_enabled():
        raise LegacyBrainDisabled("legacy brain is disabled")


@contextlib.contextmanager
def spawn_guard() -> Iterator[_Turn]:
    """프로세스 시작 구간 직렬화. 꺼짐이면 LegacyBrainDisabled.

    본문(Popen)이 예외 없이 끝나면 running_turns를 올리고 turn 핸들을 yield 시점의
    객체로 돌려준다. 호출자가 finally에서 handle.finish()를 호출한다.
    """
    with _lock:
        _ensure_loaded()
        if not _state["enabled"]:
            raise LegacyBrainDisabled("legacy brain is disabled")
        turn = _Turn()
        yield turn  # 본문 예외는 그대로 전파되어 카운트가 오르지 않는다
        with _state_lock:
            _state["running_turns"] += 1
