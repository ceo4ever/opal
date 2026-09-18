# @header
# module: ownership_tool.tests.conftest
# layer: test
# domain: opal-pipeline
# description: tests/ 부모(tool-dir)를 sys.path에 넣어 `from ownership_tool import ...`를 해석 가능하게 한다(D-19)
# exports: (none — pytest conftest)
# depends: (none)
"""pytest conftest — tool-dir을 sys.path에 삽입한다. 그 외 픽스처는 두지 않는다."""
from __future__ import annotations

import sys
from pathlib import Path

TOOL_DIR = str(Path(__file__).resolve().parent.parent)
if TOOL_DIR not in sys.path:
    sys.path.insert(0, TOOL_DIR)
