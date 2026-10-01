# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool_parts",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "state-tool 책임별 하위 모듈 패키지 — state_tool.py가 PART_MODULES 순서로 적재해 재노출한다",
  "exports": ["PART_MODULES"]
}
"""

# 적재 순서 = 허용 import 방향(하위 → 상위). state_tool.py가 이 순서로 재노출한다.
PART_MODULES = (
    "codes",
    "base",
    "run_log",
    "journal",
    "guards",
    "gates",
    "commands_core",
    "commands_run",
    "cli",
)
