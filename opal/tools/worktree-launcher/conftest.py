# @header
# module: worktree_launcher.conftest
# layer: test
# domain: opal-workspace
# description: tool-dir(`opal/tools/worktree-launcher/`)을 sys.path에 넣어 `from worktree_launcher import ...`를 해석 가능하게 하는 패키지 배선. ownership-tool의 tests/conftest.py(D-19)와 같은 역할이며, 이 도구는 tests/conftest.py를 테스트 소유물로 두므로 배선만 tool-dir 레벨에 분리한다. 픽스처·수집 규칙·assertion에는 관여하지 않는다.
# exports: TOOL_DIR
# depends: (none)
"""pytest conftest — tool-dir을 sys.path에 삽입한다. 그 외 어떤 것도 두지 않는다."""
from __future__ import annotations

import sys
from pathlib import Path

TOOL_DIR = str(Path(__file__).resolve().parent)
if TOOL_DIR not in sys.path:
    sys.path.insert(0, TOOL_DIR)
