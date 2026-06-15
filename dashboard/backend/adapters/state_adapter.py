"""
@header {
  "module": "adapters.state_adapter",
  "layer": "service",
  "domain": "console",
  "description": "state-tool show --format json read-only 호출 래퍼. 쓰기 커맨드(init/advance/mark 등) 금지",
  "exports": ["get_state"],
  "depends": ["adapters.base"]
}
"""
from __future__ import annotations

import os
from pathlib import Path

from dashboard.backend.adapters.base import run_tool, ToolError


# state-tool 래퍼 경로 (배포 환경: ~/.opal/tools/state-tool/run.sh)
STATE_TOOL = str(Path.home() / ".opal" / "tools" / "state-tool" / "run.sh")


def get_state(task_dir: str) -> dict:
    """state-tool show <task-dir> --format json 호출.

    Args:
        task_dir: 태스크 디렉토리 경로 (tasks/{NNN}-.../)

    Returns:
        state-tool show --format json 결과 dict

    Raises:
        ToolError: 도구 실패(3종)
    """
    if not os.path.exists(STATE_TOOL):
        raise ToolError(
            f"state-tool not found: {STATE_TOOL}",
            kind="exit_error",
            details={"path": STATE_TOOL},
        )

    result = run_tool(
        ["bash", STATE_TOOL, "show", task_dir, "--format", "json"],
        timeout=10.0,
    )

    if isinstance(result, dict):
        return result
    # 비정상 응답 — tool_error로 변환
    raise ToolError(
        f"Unexpected state-tool response type: {type(result)}",
        kind="tool_error",
        details={"response": str(result)[:200]},
    )
