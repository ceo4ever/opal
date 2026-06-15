"""
@header {
  "module": "adapters.base",
  "layer": "service",
  "domain": "console",
  "description": "subprocess 공통 실행·타임아웃·에러 정규화. ok:false/exit≠0/timeout 3종을 ToolError로 구분(H-3). 읽기 전용 커맨드만 허용",
  "exports": ["run_tool", "ToolError"],
  "depends": []
}
"""
from __future__ import annotations

import json
import subprocess


class ToolError(Exception):
    """OPAL 도구 호출 실패 — 3종 구분:

    - kind='exit_error': 프로세스 exit code ≠ 0
    - kind='timeout': subprocess.TimeoutExpired
    - kind='tool_error': JSON 응답의 ok:false
    """

    def __init__(self, message: str, kind: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.kind = kind  # 'exit_error' | 'timeout' | 'tool_error'
        self.details = details or {}


def run_tool(cmd: list[str], timeout: float = 10.0) -> dict | list | str:
    """subprocess.run으로 OPAL 도구 실행.

    Args:
        cmd: 실행할 커맨드 리스트
        timeout: 타임아웃 (초). 기본 10초

    Returns:
        JSON 파싱 결과 (dict/list) 또는 stdout 문자열

    Raises:
        ToolError(kind='timeout'): 타임아웃 초과
        ToolError(kind='exit_error'): exit code ≠ 0
        ToolError(kind='tool_error'): JSON ok:false

    Note:
        쓰기 커맨드(init/advance/mark/add-page 등) 금지 — 읽기 전용(TASK §결정적 제약).
        이 함수는 커맨드 자체를 검증하지 않으므로 호출자가 read-only 커맨드만 전달해야 함.
    """
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ToolError(
            f"Tool timeout after {timeout}s: {' '.join(cmd)}",
            kind="timeout",
            details={"cmd": cmd, "timeout": timeout},
        ) from exc

    if proc.returncode != 0:
        raise ToolError(
            f"Tool exit code {proc.returncode}: {' '.join(cmd)}\nstderr: {proc.stderr[:500]}",
            kind="exit_error",
            details={"cmd": cmd, "returncode": proc.returncode, "stderr": proc.stderr},
        )

    stdout = proc.stdout.strip()

    # JSON 파싱 시도
    if stdout.startswith("{") or stdout.startswith("["):
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            # JSON 파싱 실패 → 원문 문자열 반환
            return stdout

        # ok:false 체크 (dict이고 ok 필드가 있을 때)
        if isinstance(parsed, dict) and parsed.get("ok") is False:
            raise ToolError(
                f"Tool returned ok:false: {parsed.get('error', 'unknown error')}",
                kind="tool_error",
                details=parsed,
            )

        return parsed

    # JSON이 아닌 출력 → 원문 문자열 반환
    return stdout
