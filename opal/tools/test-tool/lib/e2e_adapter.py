"""
@header {
  "module": "e2e_adapter",
  "layer": "util",
  "domain": "opal-tools",
  "description": "Priority-ordered Ego Lite, cmux, and Playwright adapters with provider-unavailable-only traversal.",
  "exports": ["run_integration"],
  "depends": ["lib.e2e_contract", "ego-browser-tool", "cmux-tool", "playwright-tool"]
}

Configured providers are candidates, not success evidence. Only
provider_unavailable permits traversal to the next candidate.
"""

import json
import os
import pathlib
import shlex
import subprocess
from typing import Any, Dict, List, Optional

from lib.e2e_contract import build_verdict, normalize_legacy_verdict, status_to_error

FALLBACK_CODES = {"not_in_cmux", "cmux_not_installed"}
_EGO_DEFAULT = os.path.expanduser("~/.opal/tools/ego-browser-tool/run.sh")
_CMUX_DEFAULT = os.path.expanduser("~/.opal/tools/cmux-tool/run.sh")
_PLAYWRIGHT_DEFAULT = os.path.expanduser("~/.opal/tools/playwright-tool/run.sh")


def _tool_cmd(env, name: str, default: str) -> List[str]:
    return shlex.split((env or os.environ).get(name) or default)


def _call_json(command: List[str], args: List[str], env=None) -> Dict[str, Any]:
    try:
        process = subprocess.run([*command, *args], capture_output=True, text=True, env=env, check=False)
    except (FileNotFoundError, PermissionError) as exc:
        return {"ok": False, "status": "provider_unavailable", "detail": str(exc)}
    stdout = process.stdout.strip()
    if not stdout:
        return {
            "ok": False,
            "status": "provider_unavailable" if process.returncode in {18, 126, 127} else "infra_error",
            "detail": process.stderr.strip() or "provider returned empty output",
        }
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return {"ok": False, "status": "infra_error", "detail": "provider returned invalid JSON"}
    if not isinstance(data, dict):
        return {"ok": False, "status": "infra_error", "detail": "provider JSON root is not an object"}
    data.setdefault("_exit_code", process.returncode)
    return data


def _resolve_cmux_tool_cmd(env=None) -> str:
    """Compatibility seam retained for existing callers and tests."""
    return _tool_cmd(env, "OPAL_CMUX_TOOL_CMD", _CMUX_DEFAULT)[0]


def _call_cmux_tool(args: List[str], env=None) -> Dict[str, Any]:
    command = _tool_cmd(env, "OPAL_CMUX_TOOL_CMD", _CMUX_DEFAULT)
    if len(command) == 1:
        command = ["bash", command[0]]
    data = _call_json(command, args, env=env)
    if data.get("status") == "provider_unavailable" and not data.get("error"):
        data["error"] = "cmux_not_installed"
    return data


def _response(status: str, *, e2e=None, detail=None, handoff=None) -> Dict[str, Any]:
    output = {
        "ok": status == "pass",
        "command": "integration",
        "status": status,
        "error": status_to_error(status),
        "detail": detail,
        "e2e": e2e or {"status": status},
        "api_db": {"status": "skip"},
        "contract_version": "2.0",
    }
    if handoff is not None:
        output["handoff"] = handoff
    return output


def _asserted(name: str, raw: Dict[str, Any], url: Optional[str], expected: Optional[str]) -> Dict[str, Any]:
    status = raw.get("status")
    if status == "provider_unavailable":
        return {"status": status, "raw": raw}
    if status not in {"pass", "fail", "infra_error", "blocked", "awaiting_human"}:
        status = "pass" if raw.get("ok") else "infra_error"
    actual = raw.get("actual")
    if status == "pass" and (not expected or actual is None or expected not in str(actual)):
        status = "fail"
    return {
        "status": status,
        "raw": raw,
        "e2e": {"driver": name, "status": status, "url": url, "expected": expected, "actual": actual},
    }


def _run_ego(url, expected, install_choice, env=None) -> Dict[str, Any]:
    if not url:
        return {"status": "fail", "detail": "URL is required"}
    args = ["smoke", url]
    if expected:
        args += ["--expect-text", expected]
    if install_choice:
        args += ["--install-choice", install_choice]
    raw = _call_json(_tool_cmd(env, "OPAL_EGO_BROWSER_TOOL_CMD", _EGO_DEFAULT), args, env=env)
    result = _asserted("ego-lite", raw, url, expected)
    if raw.get("space_id") is not None and result.get("e2e"):
        result["e2e"]["space_id"] = raw["space_id"]
    return result


def _cmux_error(raw: Dict[str, Any]) -> Dict[str, Any]:
    error = raw.get("error")
    payload = {"status": "fallback" if error in FALLBACK_CODES else "escalated", "fallback_reason": error, "error": error}
    if "wait_kind" in raw:
        payload["wait_kind"] = raw["wait_kind"]
    return normalize_legacy_verdict(payload)


def _run_cmux(url, expected, env=None) -> Dict[str, Any]:
    opened = _call_cmux_tool(["open"] + ([url] if url else []), env=env)
    if not opened.get("ok"):
        normalized = _cmux_error(opened)
        return {"status": normalized["status"], "detail": normalized.get("detail"), "raw": opened}
    surface = opened.get("surface")
    try:
        if url and surface:
            navigated = _call_cmux_tool(["navigate", url], env=env)
            if not navigated.get("ok"):
                normalized = _cmux_error(navigated)
                return {"status": normalized["status"], "detail": normalized.get("detail"), "raw": navigated}
        actual = None
        if expected:
            observed = _call_cmux_tool(["eval", "--surface", str(surface), "--script", "document.body.innerText"], env=env)
            if not observed.get("ok"):
                normalized = _cmux_error(observed)
                return {"status": normalized["status"], "detail": normalized.get("detail"), "raw": observed}
            actual = observed.get("result")
        verdict = build_verdict({
            "status": "pass", "profile": "browser", "observed_executors": ["browser"],
            "assertion_results": ([{"id": "expect-text", "expected": expected, "actual": expected if expected and expected in str(actual or "") else actual}] if expected else []),
            "required_evidence": ["semantic_assertion"], "observed_evidence": (["semantic_assertion"] if expected else []),
        })
        status = verdict["status"]
        return {"status": status, "detail": verdict.get("detail"), "e2e": {"driver": "cmux", "status": status, "url": url, "surface": surface, "expected": expected, "actual": actual}}
    finally:
        _call_cmux_tool(["close"], env=env)


def _run_playwright(candidate, url, expected, env=None) -> Dict[str, Any]:
    override = (env or os.environ).get("OPAL_PLAYWRIGHT_TOOL_CMD")
    if not override and candidate.get("via") != "playwright-tool":
        return {"status": "provider_unavailable", "detail": "playwright adapter is not configured"}
    if not url:
        return {"status": "fail", "detail": "URL is required"}
    raw = _call_json(_tool_cmd(env, "OPAL_PLAYWRIGHT_TOOL_CMD", _PLAYWRIGHT_DEFAULT), [url, "--mode", "clean"], env=env)
    if raw.get("status") == "provider_unavailable":
        return {"status": "provider_unavailable", "raw": raw}
    if not raw.get("ok"):
        return {"status": raw.get("status") or "infra_error", "raw": raw, "detail": raw.get("detail") or raw.get("error")}
    raw["actual"] = raw.get("actual") if raw.get("actual") is not None else raw.get("content")
    raw["status"] = "pass"
    return _asserted("playwright", raw, url, expected)


def run_integration(
    tiers_data: Dict[str, Any], scope: str = "be", url: Optional[str] = None,
    project_root: Optional[pathlib.Path] = None, env=None,
    expect_text: Optional[str] = None, ego_install_choice: Optional[str] = None,
) -> Dict[str, Any]:
    del scope, project_root
    candidates = [item for item in tiers_data.get("integration", {}).get("e2e", []) if isinstance(item, dict)]
    candidates.sort(key=lambda item: (item.get("priority", 999), str(item.get("name", ""))))
    attempted: List[str] = []
    for candidate in candidates:
        name = str(candidate.get("name") or "")
        if name in {"ego", "ego-lite", "ego-browser"}:
            result, driver = _run_ego(url, expect_text, ego_install_choice, env), "ego-lite"
        elif name == "cmux":
            result, driver = _run_cmux(url, expect_text, env), "cmux"
        elif name == "playwright":
            result, driver = _run_playwright(candidate, url, expect_text, env), "playwright"
        else:
            result, driver = {"status": "provider_unavailable", "detail": f"unknown provider: {name}"}, name
        attempted.append(name)
        status = result.get("status")
        if status == "provider_unavailable":
            continue
        raw = result.get("raw") or {}
        e2e = result.get("e2e") or {"driver": driver, "status": status, "url": url, "expected": expect_text, "actual": raw.get("actual")}
        e2e["attempted"] = attempted
        return _response(str(status), e2e=e2e, detail=result.get("detail") or raw.get("detail"), handoff=raw.get("handoff"))
    return _response("executor_unavailable", e2e={"driver": None, "status": "executor_unavailable", "url": url, "attempted": attempted}, detail="configured E2E provider candidates are unavailable")
