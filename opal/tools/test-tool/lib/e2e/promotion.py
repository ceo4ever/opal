"""
@header {
  "module": "promotion",
  "layer": "util",
  "domain": "opal-tools",
  "description": "docs/e2e 승격 자격을 test-tool run.json의 완전한 pass 증적으로만 판정한다.",
  "exports": ["evaluate_promotion", "check_promotion"]
}

The promotion gate is deliberately read-only.  It does not copy a journey and
does not accept prose or caller supplied verdicts as evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from lib import e2e_contract
from lib.e2e import orchestrator


COMMAND = "e2e promote-check"
ERROR_PROMOTION_NOT_ELIGIBLE = "e2e_promotion_not_eligible"
ERROR_PROMOTION_EVIDENCE_INVALID = "e2e_promotion_evidence_invalid"


def _result(*, eligible: bool, reason: str, evidence: Optional[dict] = None) -> Dict[str, Any]:
    evidence = evidence or {}
    return {
        "ok": eligible,
        "command": COMMAND,
        "eligible": eligible,
        "reason": reason,
        "error": None if eligible else (
            ERROR_PROMOTION_EVIDENCE_INVALID
            if reason in {"run_json_not_found", "run_json_invalid"}
            else ERROR_PROMOTION_NOT_ELIGIBLE
        ),
        "run_id": evidence.get("run_id"),
        "scenario_id": evidence.get("scenario_id"),
        "status": evidence.get("status"),
        "exit_code": evidence.get("exit_code"),
        "run_json_path": evidence.get("run_json_path"),
    }


def evaluate_promotion(
    run_json_path: str | Path, *, journey_id: Optional[str] = None
) -> Dict[str, Any]:
    """Evaluate one immutable run record without changing project files."""
    path = Path(run_json_path).expanduser().resolve()
    if not path.is_file():
        return _result(eligible=False, reason="run_json_not_found")
    try:
        run = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _result(eligible=False, reason="run_json_invalid")
    if not isinstance(run, dict):
        return _result(eligible=False, reason="run_json_invalid")

    evidence = {**run, "run_json_path": str(path)}
    expected_pass_exit = e2e_contract.status_to_exit("pass")
    checks = (
        (run.get("status") == "pass", "status_not_pass"),
        (run.get("exit_code") == expected_pass_exit, "exit_not_pass"),
        (run.get("evidence_complete") is True, "evidence_incomplete"),
        (run.get("missing_evidence") == [], "missing_evidence"),
        (run.get("executed") is True, "run_not_executed"),
    )
    for passed, reason in checks:
        if not passed:
            return _result(eligible=False, reason=reason, evidence=evidence)
    if journey_id is not None and str(run.get("scenario_id")) != str(journey_id):
        return _result(eligible=False, reason="journey_mismatch", evidence=evidence)
    return _result(eligible=True, reason="pass_evidence_verified", evidence=evidence)


def check_promotion(
    *,
    run_id: Optional[str] = None,
    artifact_dir: Optional[str] = None,
    artifact_root: Optional[str] = None,
    run_json: Optional[str] = None,
    journey_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve an E2E run using the normal bounded artifact lookup, then gate it."""
    if run_json:
        return evaluate_promotion(run_json, journey_id=journey_id)
    found = orchestrator.run_status(
        run_id=run_id, artifact_dir=artifact_dir, artifact_root=artifact_root
    )
    if found.get("error"):
        return _result(eligible=False, reason="run_json_not_found")
    return evaluate_promotion(found["run_json_path"], journey_id=journey_id)
