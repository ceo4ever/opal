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

    첫 기동 시 기본값 파일을 생성하지 않음 — PLAN §3.1.3: "런타임 생성/읽기"
    (설정 파일 생성은 install 단계에서 수행)
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
