# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "OPAL 파이프라인 현황판(state.json SSOT·STATE.md 저널) 관리 CLI 진입점 — state_tool_parts 하위 모듈을 적재해 재노출하고 main()을 실행한다",
  "exports": ["main", "build_parser"],
  "depends": ["state_tool_parts"]
}
"""

import importlib
import os
import sys

_STATE_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
if not any(os.path.abspath(p or os.curdir) == _STATE_TOOL_DIR for p in sys.path):
    sys.path.insert(0, _STATE_TOOL_DIR)

import state_tool_parts  # noqa: E402


def _reexport_parts():
    """하위 모듈의 모든 최상위 이름(밑줄 시작 포함, dunder 제외)을 이 모듈 전역에 채운다."""
    namespace = globals()
    for part in state_tool_parts.PART_MODULES:
        module = importlib.import_module(f"state_tool_parts.{part}")
        for name, value in vars(module).items():
            if not name.startswith("__"):
                namespace[name] = value


_reexport_parts()

if __name__ == "__main__":
    main()  # noqa: F821 — cli.main을 재노출로 바인딩
