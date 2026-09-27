"""
@header {
  "module": "runner",
  "layer": "util",
  "domain": "opal-tools",
  "description": "unit 계층 stop-on-fail 실행기(lint→typecheck→unit→a11y 순서, 단발 실행) + check(설치 확인) / run(실제 검사) 분리 실행 계약(task 161 D-1~D-7) + check 도구 설치 게이트. 러너 재구현 금지 — subprocess 위임만.",
  "exports": [
    "run_unit_layers",
    "run_check",
    "LAYER_STATUSES",
    "OVERALL_STATUSES",
    "LAYER_REASONS",
    "OVERALL_REASONS"
  ]
}

test-tool runner — unit stop-on-fail 실행기 + check 게이트.

[MUST] 헌법 §2 단순성: pytest/vitest/eslint/ruff 등 러너를 재구현하지 않는다.
  yaml에 선언된 run(실제 검사)/check(설치 확인) 명령을 그대로 subprocess 실행하고 JSON 증거 반환.
[MUST] 단발 실행: watch 플래그 미사용 — verification-loop §2 [MUST] :60.
[MUST] stop-on-fail: 필수 계층 실패 시 이후 계층 미실행 + not_run/stopped_after_failure 기록.
[MUST] task 161 C-2: run 없는 계층에서 check를 검사 명령으로 대체 실행하지 않는다.
[MUST] task 161 C-5: run_files를 지원하지 않는 도구에 파일 인자를 붙이지 않는다.

계약 원문(상태값·사유 코드·exit 대응)은 opal/tools/test-tool/README.md `unit` 절이 소유한다(D-8).
이 모듈은 그 원문과 대조하는 선언 목록만 상수로 둔다.
"""

import fnmatch
import os
import pathlib
import shlex
import shutil
import subprocess
from typing import Any, Dict, List, Optional

# 계층 실행 순서 (a11y는 optional 기본값이므로 마지막)
LAYER_ORDER = ["lint", "typecheck", "unit", "a11y"]

# 폐쇄 목록 — README `unit` 절(D-8 원문)과 대조. 방출 전 아래 목록 밖 값을 쓰지 않는다.
LAYER_STATUSES = {"pass", "fail", "tool_unavailable", "not_configured", "not_applicable", "not_run"}
OVERALL_STATUSES = {"pass", "fail", "incomplete"}
LAYER_REASONS = {
    "run_missing",
    "install_check_failed",
    "stopped_after_failure",
    "no_matching_files",
}
SCOPE_REASONS = {"file_scope_unsupported"}
SCOPE_EXCLUDE_REASONS = {"missing", "outside_project", "pattern_mismatch"}
OVERALL_REASONS = {
    "required_layer_unverified",
    "no_check_executed",
    "no_layers_declared",
}

_LEGACY_HINT = (
    "구형 설정: check에 실제 검사 명령이 들어 있으면 run으로 옮기고 check는 설치 확인 명령(예: "
    "`<tool> --version`)으로 바꾼다. 절차는 opal/tools/test-tool/README.md `unit` 절 "
    "'구형 설정 이관' 참고."
)


def _run_command(cmd: str, cwd: Optional[pathlib.Path] = None, env=None) -> Dict[str, Any]:
    """
    shell 명령을 subprocess로 실행하고 {cmd, exit, stdout, status} 반환.
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
    도구 설치 상태 게이트 검사. (변경 없음 — PATH 조회 기반, task 161 범위 밖)

    반환 dict:
        ok: bool
        command: str
        results: List[{name, installed, required}]
        blocked: bool
        error: str (blocked 시)
    """
    results: List[Dict[str, Any]] = []
    blocked = False

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


def _resolve_file_scope(
    changed_files: List[str],
    file_globs: Optional[List[str]],
    project_root: Optional[pathlib.Path],
) -> Dict[str, Any]:
    """
    D-3: 요청 파일을 프로젝트 안 존재·glob 일치 여부로 판정한다.
    반환: {kind:"files", requested, checked, excluded:[{path, reason}]}
    """
    root = (project_root or pathlib.Path.cwd()).resolve()
    checked: List[str] = []
    excluded: List[Dict[str, str]] = []

    for raw in changed_files:
        candidate = pathlib.Path(raw)
        abs_path = candidate if candidate.is_absolute() else (root / candidate)
        try:
            resolved = abs_path.resolve()
        except OSError:
            resolved = abs_path

        try:
            resolved.relative_to(root)
            inside = True
        except ValueError:
            inside = False

        if not inside:
            excluded.append({"path": raw, "reason": "outside_project"})
            continue
        if not resolved.exists():
            excluded.append({"path": raw, "reason": "missing"})
            continue
        if file_globs:
            basename = resolved.name
            matched = any(fnmatch.fnmatch(basename, pattern) for pattern in file_globs)
            if not matched:
                excluded.append({"path": raw, "reason": "pattern_mismatch"})
                continue
        checked.append(raw)

    return {
        "kind": "files",
        "requested": list(changed_files),
        "checked": checked,
        "excluded": excluded,
        "reason": None,
    }


def _not_run_layer(layer_name: str, tool: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": layer_name,
        "tool": tool.get("name"),
        "required": bool(tool.get("required", True)),
        "status": "not_run",
        "reason": "stopped_after_failure",
        "check": None,
        "cmd": None,
        "exit": None,
        "stdout": None,
        "scope": None,
    }


def _not_configured_layer(layer_name: str, tool: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": layer_name,
        "tool": tool.get("name"),
        "required": bool(tool.get("required", True)),
        "status": "not_configured",
        "reason": "run_missing",
        "check": None,
        "cmd": None,
        "exit": None,
        "stdout": None,
        "scope": None,
        "hint": _LEGACY_HINT,
    }


def run_unit_layers(
    tiers_data: Dict[str, Any],
    scope: str = "be",
    project_root: Optional[pathlib.Path] = None,
    env=None,
    changed_files: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    unit 계층 stop-on-fail 실행 (task 161 D-1~D-7 계약).
    순서: lint → typecheck → unit → a11y.
    [MUST] 단발 실행 — watch 플래그 사용 금지.
    [MUST] stop-on-fail — 필수 계층 fail 시 이후 계층 not_run/stopped_after_failure로 남긴다.
    [MUST] check(설치 확인)와 run(실제 검사)를 분리 실행한다 — run 없으면 check도 실행하지 않는다.

    반환 dict: status, reason(비통과 시), scope, cwd, config는 CLI(cmd_unit)가 채운다.
        layers: List[layer dict], stopped_at, requested_files, error(비통과 시)
    """
    unit_data = tiers_data.get("unit", {})
    scope_data = unit_data.get(scope, {})
    changed_files = list(changed_files) if changed_files else []

    layers: List[Dict[str, Any]] = []
    stopped_at: Optional[str] = None
    stopped = False

    for layer_name in LAYER_ORDER:
        tool_list = scope_data.get(layer_name)
        if not tool_list:
            continue

        tool = tool_list[0] if isinstance(tool_list, list) else None
        if not isinstance(tool, dict):
            continue

        required = bool(tool.get("required", True))
        name = tool.get("name")

        if stopped:
            layers.append(_not_run_layer(layer_name, tool))
            continue

        run_cmd = tool.get("run")
        run_files_cmd = tool.get("run_files")
        file_globs = tool.get("file_globs")
        check_cmd = tool.get("check")

        if not run_cmd and not run_files_cmd:
            layers.append(_not_configured_layer(layer_name, tool))
            continue

        # D-3: 검사 범위 결정
        layer_scope: Dict[str, Any]
        exec_cmd: Optional[str] = None

        if changed_files:
            if run_files_cmd:
                layer_scope = _resolve_file_scope(changed_files, file_globs, project_root)
                if not layer_scope["checked"]:
                    layer_entry = {
                        "name": layer_name,
                        "tool": name,
                        "required": required,
                        "status": "not_applicable",
                        "reason": "no_matching_files",
                        "check": None,
                        "cmd": None,
                        "exit": None,
                        "stdout": None,
                        "scope": layer_scope,
                    }
                    layers.append(layer_entry)
                    continue
                quoted = " ".join(shlex.quote(f) for f in layer_scope["checked"])
                exec_cmd = run_files_cmd.replace("{files}", quoted)
            else:
                layer_scope = {
                    "kind": "project",
                    "requested": list(changed_files),
                    "checked": [],
                    "excluded": [],
                    "reason": "file_scope_unsupported",
                }
                exec_cmd = run_cmd
        else:
            layer_scope = {
                "kind": "project",
                "requested": [],
                "checked": [],
                "excluded": [],
                "reason": None,
            }
            exec_cmd = run_cmd

        if exec_cmd is None:
            layers.append(_not_configured_layer(layer_name, tool))
            continue

        check_field: Optional[Dict[str, Any]] = None
        if check_cmd:
            check_result = _run_command(check_cmd, cwd=project_root, env=env)
            check_field = {
                "cmd": check_result["cmd"],
                "exit": check_result["exit"],
                "status": check_result["status"],
            }
            if check_result["status"] == "fail":
                layer_entry = {
                    "name": layer_name,
                    "tool": name,
                    "required": required,
                    "status": "tool_unavailable",
                    "reason": "install_check_failed",
                    "check": check_field,
                    "cmd": None,
                    "exit": None,
                    "stdout": None,
                    "scope": layer_scope,
                }
                layers.append(layer_entry)
                continue

        result = _run_command(exec_cmd, cwd=project_root, env=env)
        layer_entry = {
            "name": layer_name,
            "tool": name,
            "required": required,
            "status": result["status"],
            "check": check_field,
            "cmd": result["cmd"],
            "exit": result["exit"],
            "stdout": result["stdout"],
            "scope": layer_scope,
        }
        layers.append(layer_entry)

        if result["status"] == "fail":
            stopped = True
            stopped_at = layer_name

    # D-4: 전체 상태 결정
    required_layers = [l for l in layers if l.get("required")]
    overall_status: str
    overall_reason: Optional[str] = None
    overall_error: Optional[str] = None

    if any(l.get("status") == "fail" for l in required_layers):
        overall_status = "fail"
        overall_error = "layer_failed"
    elif any(l.get("status") in ("tool_unavailable", "not_configured") for l in required_layers):
        overall_status = "incomplete"
        overall_reason = "required_layer_unverified"
        overall_error = "unit_incomplete"
    elif not any(l.get("status") == "pass" for l in layers):
        overall_status = "incomplete"
        overall_reason = "no_layers_declared" if not layers else "no_check_executed"
        overall_error = "unit_incomplete"
    else:
        overall_status = "pass"

    response: Dict[str, Any] = {
        "ok": overall_status == "pass",
        "status": overall_status,
        "layers": layers,
        "stopped_at": stopped_at,
        "requested_files": changed_files,
    }
    if overall_reason:
        response["reason"] = overall_reason
    if overall_error:
        response["error"] = overall_error

    return response
