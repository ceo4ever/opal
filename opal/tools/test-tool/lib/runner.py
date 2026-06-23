"""
@header {
  "module": "runner",
  "layer": "util",
  "domain": "opal-tools",
  "description": "unit 계층 stop-on-fail 실행기(lint→typecheck→unit 순서, 단발 실행) + check 도구 설치 게이트. 러너 재구현 금지 — subprocess 위임만.",
  "exports": [
    "run_unit_layers",
    "run_check"
  ]
}

test-tool runner — unit stop-on-fail 실행기 + check 게이트.

[MUST] 헌법 §2 단순성: pytest/vitest/eslint/ruff 등 러너를 재구현하지 않는다.
  yaml에 선언된 check 명령을 그대로 subprocess 실행하고 JSON 증거 반환.
[MUST] 단발 실행: watch 플래그 미사용 — verification-loop §2 [MUST] :60.
[MUST] stop-on-fail: lint 실패 시 typecheck/unit 미실행 + stopped_at 기록.
"""

import os
import pathlib
import shutil
import subprocess
from typing import Any, Dict, List, Optional


def _run_command(cmd: str, cwd: Optional[pathlib.Path] = None, env=None) -> Dict[str, Any]:
    """
    shell 명령을 subprocess로 실행하고 {name, cmd, exit, stdout, status} 반환.
    [MUST] watch 플래그를 명령에 추가하지 않는다.
    """
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        env=env,
    )
    status = "pass" if result.returncode == 0 else "fail"
    return {
        "cmd": cmd,
        "exit": result.returncode,
        "stdout": (result.stdout + result.stderr).strip(),
        "status": status,
    }


def _is_tool_installed(tool_name: str) -> bool:
    """도구가 PATH에 설치되어 있는지 확인."""
    return shutil.which(tool_name) is not None


def run_check(
    tiers_data: Dict[str, Any],
    tier: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    도구 설치 상태 게이트 검사.

    반환 dict:
        ok: bool
        command: str
        results: List[{name, installed, required}]
        blocked: bool
        error: str (blocked 시)
    """
    results: List[Dict[str, Any]] = []
    blocked = False

    # tier 필터링
    tiers_to_check = {}
    if tier:
        if tier in tiers_data:
            tiers_to_check[tier] = tiers_data[tier]
    else:
        tiers_to_check = tiers_data

    for tier_name, tier_val in tiers_to_check.items():
        if not isinstance(tier_val, dict):
            continue
        for scope_name, scope_val in tier_val.items():
            if not isinstance(scope_val, dict):
                # e2e/supervisor는 list 형태일 수 있음
                if isinstance(scope_val, list):
                    _process_tool_list(scope_val, results, category)
                continue
            for cat_name, tool_list in scope_val.items():
                if category and cat_name != category:
                    continue
                if isinstance(tool_list, list):
                    _process_tool_list(tool_list, results, category)

    for r in results:
        if r.get("required") and not r.get("installed"):
            blocked = True
            break

    result: Dict[str, Any] = {
        "ok": not blocked,
        "command": "check",
        "results": results,
        "blocked": blocked,
    }
    if blocked:
        result["error"] = "required_missing"
    return result


def _process_tool_list(
    tool_list: List[Any],
    results: List[Dict[str, Any]],
    category: Optional[str],
) -> None:
    """도구 리스트를 처리하여 results에 추가."""
    for tool in tool_list:
        if not isinstance(tool, dict):
            continue
        name = tool.get("name", "")
        if not name:
            continue
        required = bool(tool.get("required", False))
        installed = _is_tool_installed(name)
        results.append({
            "name": name,
            "installed": installed,
            "required": required,
        })


def run_unit_layers(
    tiers_data: Dict[str, Any],
    scope: str = "be",
    project_root: Optional[pathlib.Path] = None,
    env=None,
) -> Dict[str, Any]:
    """
    unit 계층 stop-on-fail 실행.
    순서: lint → typecheck/build → unit
    [MUST] 단발 실행 — watch 플래그 사용 금지.
    [MUST] stop-on-fail — 한 계층 fail 시 다음 미실행 + stopped_at 기록.

    반환 dict:
        ok: bool
        command: str
        layers: List[{name, cmd, status, stdout, exit}]
        stopped_at: Optional[str]
        error: str (실패 시)
    """
    unit_data = tiers_data.get("unit", {})
    scope_data = unit_data.get(scope, {})

    # 계층 순서: lint → typecheck → unit (a11y는 optional이므로 마지막)
    LAYER_ORDER = ["lint", "typecheck", "unit", "a11y"]

    layers: List[Dict[str, Any]] = []
    stopped_at: Optional[str] = None
    overall_failed = False

    for layer_name in LAYER_ORDER:
        tool_list = scope_data.get(layer_name)
        if not tool_list:
            continue

        # 첫 번째 도구만 실행 (기본값)
        tool = tool_list[0] if isinstance(tool_list, list) else None
        if not isinstance(tool, dict):
            continue

        cmd = tool.get("check", "")
        if not cmd:
            continue

        result = _run_command(cmd, cwd=project_root, env=env)
        layer_entry: Dict[str, Any] = {
            "name": layer_name,
            "cmd": result["cmd"],
            "status": result["status"],
            "stdout": result["stdout"],
            "exit": result["exit"],
        }
        layers.append(layer_entry)

        if result["status"] == "fail":
            overall_failed = True
            stopped_at = layer_name
            break  # stop-on-fail

    response: Dict[str, Any] = {
        "ok": not overall_failed,
        "command": "unit",
        "layers": layers,
        "stopped_at": stopped_at,
    }
    if overall_failed:
        response["error"] = "layer_failed"

    return response
