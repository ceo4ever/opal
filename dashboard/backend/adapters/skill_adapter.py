"""
@header {
  "module": "adapters.skill_adapter",
  "layer": "service",
  "domain": "console",
  "description": "skill-registry list read-only 호출 래퍼. 등록된 스킬 목록 제공",
  "exports": ["list_skills"],
  "depends": ["adapters.base"]
}
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from dashboard.backend.adapters.base import run_tool, ToolError


# skill-registry 경로
SKILL_REGISTRY = str(Path.home() / ".opal" / "tools" / "skill-registry" / "skill-registry.js")


def list_skills() -> list[dict]:
    """skill-registry list 호출 → 스킬 목록 반환.

    Returns:
        스킬 목록 (list[dict]). 각 항목: {name, description, version, ...}

    Raises:
        ToolError: 도구 실패(3종)

    Note:
        skill-registry list는 STDOUT에 JSON 배열 또는 텍스트 목록을 출력한다.
        텍스트 형식의 경우 각 줄을 {name: str} dict로 변환한다.
    """
    if not os.path.exists(SKILL_REGISTRY):
        raise ToolError(
            f"skill-registry not found: {SKILL_REGISTRY}",
            kind="exit_error",
            details={"path": SKILL_REGISTRY},
        )

    try:
        result = run_tool(
            ["node", SKILL_REGISTRY, "list"],
            timeout=15.0,
        )
    except ToolError:
        raise

    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        # {skills: [...]} 형태
        if "skills" in result:
            return result["skills"]
        return [result]

    # 텍스트 출력 → 줄별 파싱
    if isinstance(result, str):
        lines = [line.strip() for line in result.splitlines() if line.strip()]
        # JSON 배열 시도
        try:
            parsed = json.loads(result)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        # 텍스트 목록 → 간단한 dict 변환
        return [{"name": line} for line in lines if line]

    return []
