"""
@header {
  "module": "config",
  "layer": "config",
  "domain": "console",
  "description": "~/.opal/console.config.json 로드 및 기본값 추론. scan_roots/scan_depth/exclude/prewarm_projects 관리. prewarm_projects는 기동 선프라임 대상 프로젝트 절대경로 목록(T060 F-1) — _coerce_str_list()로 비-list 값을 안전하게 []로 폴백한다. [T061 F-1] save_config — 원자적 쓰기(_atomic_write_json: temp write + os.replace) + _WRITE_LOCK(threading.Lock)으로 read-modify-write 사이클 직렬화. 쓰기 대상은 routers/config.py의 POST /api/config/prewarm이 검증한 prewarm_projects 갱신뿐이다(T061 범위 축소로 save_project_local 제거).",
  "exports": ["load_config", "ConsoleConfig", "save_config"],
  "depends": [],
  "task": "061",
  "changelog": [
    "2026-07-14 T060 Step1: prewarm_projects 필드 + _coerce_str_list 타입 가드 추가 (F-1, H-4)",
    "2026-07-14 T061 Step2: _WRITE_LOCK + _atomic_write_json + save_config + save_project_local 추가 — 원자 쓰기·머지 보존 (F-001, H-2/H-3)",
    "2026-07-14 T061 범위 축소: save_project_local 제거(프로젝트 로컬 설정 편집 미반영, 수동 JSON 편집 대체)"
  ]
}
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from dataclasses import dataclass, field


CONFIG_PATH = Path.home() / ".opal" / "console.config.json"

DEFAULT_SCAN_ROOTS = [str(Path.home() / "workspace")]
DEFAULT_SCAN_DEPTH = 2
DEFAULT_EXCLUDE = ["node_modules", ".git", ".venv", "__pycache__", ".DS_Store"]


@dataclass
class ConsoleConfig:
    scan_roots: list[str] = field(default_factory=lambda: list(DEFAULT_SCAN_ROOTS))
    scan_depth: int = DEFAULT_SCAN_DEPTH
    exclude: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDE))
    prewarm_projects: list[str] = field(default_factory=list)


def _coerce_str_list(value: object) -> list[str]:
    """list[str]이 아니면 빈 리스트로 폴백. 원소 중 str만 취해 안전 순회 보장(H-4)."""
    if not isinstance(value, list):
        return []
    return [v for v in value if isinstance(v, str)]


def load_config() -> ConsoleConfig:
    """~/.opal/console.config.json 로드. 없으면 기본값 반환.

    설정 파일 생성/갱신은 `opal-cli console scan [기준경로...]`가 수행하며,
    install(install_dashboard)이 신규 머신에서 1회 자동 실행한다.
    백엔드는 이 파일을 읽기 전용으로 소비한다(쓰기 없음, 태스크 021 C-2).
    """
    if not CONFIG_PATH.exists():
        return ConsoleConfig()

    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data: dict = json.load(f)
    except (json.JSONDecodeError, OSError):
        return ConsoleConfig()

    return ConsoleConfig(
        scan_roots=data.get("scan_roots", DEFAULT_SCAN_ROOTS),
        scan_depth=int(data.get("scan_depth", DEFAULT_SCAN_DEPTH)),
        exclude=data.get("exclude", DEFAULT_EXCLUDE),
        prewarm_projects=_coerce_str_list(data.get("prewarm_projects", [])),
    )


# ── 쓰기 인프라 (T061 F-001) ──────────────────────────────────────────────────
# 쓰기 대상은 routers/config.py가 검증한 console.config.json(prewarm_projects)
# 갱신으로 한정된다. 이 모듈은 경로 검증을 수행하지 않고 전달받은 경로에
# 원자적으로 쓴다.

_WRITE_LOCK = threading.Lock()   # read-modify-write 사이클 직렬화(H-2)


def _atomic_write_json(path: Path, data: dict) -> None:
    """temp 파일 쓰기 후 os.replace로 atomic rename (부분 쓰기·파손 방지)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)        # 동일 파일시스템 내 atomic rename (POSIX 보장)


def save_config(updates: dict) -> dict:
    """console.config.json 머지 보존 쓰기. 기존 키 유실 금지(H-3)."""
    with _WRITE_LOCK:
        existing = {}
        if CONFIG_PATH.exists():
            try:
                existing = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = {}
        existing.update(updates)          # 부분 갱신 — 미전달 키 보존
        _atomic_write_json(CONFIG_PATH, existing)
        return existing
