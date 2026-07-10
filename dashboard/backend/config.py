"""
@header {
  "module": "config",
  "layer": "config",
  "domain": "console",
  "description": "~/.opal/console.config.json 로드 및 기본값 추론. scan_roots/scan_depth/exclude 관리",
  "exports": ["load_config", "ConsoleConfig"],
  "depends": []
}
"""
from __future__ import annotations

import json
import os
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
    )
