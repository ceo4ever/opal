"""
@header {
  "module": "adapters.scan_adapter",
  "layer": "service",
  "domain": "console",
  "description": "code-scan scan --json read-only 호출 래퍼. 프로젝트 @header 구조 정보 제공",
  "exports": ["get_scan"],
  "depends": ["adapters.base"]
}
"""
from __future__ import annotations

import os
from pathlib import Path

from dashboard.backend.adapters.base import run_tool, ToolError


# code-scan 경로 (배포 환경: ~/.opal/tools/code-scan/code-scan.js)
CODE_SCAN = str(Path.home() / ".opal" / "tools" / "code-scan" / "code-scan.js")


def get_scan(project_path: str) -> dict | list:
    """code-scan scan <project-path> --json 호출.

    Args:
        project_path: 스캔할 프로젝트 경로

    Returns:
        code-scan 결과 (dict 또는 list)

    Raises:
        ToolError: 도구 실패(3종)
    """
    if not os.path.exists(CODE_SCAN):
        raise ToolError(
            f"code-scan not found: {CODE_SCAN}",
            kind="exit_error",
            details={"path": CODE_SCAN},
        )

    result = run_tool(
        ["node", CODE_SCAN, "scan", project_path, "--json"],
        timeout=30.0,
    )
    return result
