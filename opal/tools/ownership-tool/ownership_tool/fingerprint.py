"""
@header {
  "module": "ownership_tool.fingerprint",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "state-tool show --format json 응답에서 파이프라인 전이에 영향을 주는 의미 필드만 추출해 정규화하고 안정적인 SHA-256 fingerprint를 계산한다(S-6/TASK C-10). created_at/updated_at/timestamp/note 자유문(Step N/M 추출값 제외)/run_log/활동 로그/worker_duration_*/owner는 정규화 dict에서 제외한다. stop-guard receipt(StopReceipt)는 ownership_core의 경로·락·원자쓰기 헬퍼로 저장/조회한다.",
  "exports": ["normalize", "compute", "save_receipt", "load_receipt"],
  "depends": ["ownership_core"]
}
"""
from __future__ import annotations

import hashlib
import json
import re

from . import ownership_core

_STEP_RE = re.compile(r"Step\s+(\d+)\s*/\s*(\d+)")


def _extract_step(note):
    """note 자유문에서 'Step N/M' 패턴만 추출한다. 없으면 None."""
    if not isinstance(note, str):
        return None
    match = _STEP_RE.search(note)
    if not match:
        return None
    return f"{match.group(1)}/{match.group(2)}"


def _unwrap(show_json):
    """show_json은 전체 응답(data+최상위 transition_action/next_action)일 수도, data만일 수도 있다."""
    if not isinstance(show_json, dict):
        return {}, None, None
    if isinstance(show_json.get("data"), dict):
        data = show_json["data"]
        transition_action = show_json.get("transition_action", data.get("transition_action"))
        next_action = show_json.get("next_action", data.get("next_action"))
        return data, transition_action, next_action
    return show_json, show_json.get("transition_action"), show_json.get("next_action")


def normalize(show_json, registry_meta=None, lease=None, decision_kind=None):
    """의미 필드만 남긴 정규화 dict를 반환한다.

    제외: state.json 원문/해시/revision, created_at, updated_at, 행 timestamp, note 자유문
    (Step N/M 추출값 제외), run_log 블록, 활동 로그, worker_duration_*, owner.
    """
    data, transition_action, next_action = _unwrap(show_json)

    rows_out = []
    for row in data.get("rows") or []:
        if not isinstance(row, dict):
            continue
        rows_out.append(
            {
                "key": row.get("key"),
                "status": row.get("status"),
                "step": _extract_step(row.get("note")),
            }
        )
    rows_out.sort(key=lambda r: (r.get("key") or ""))

    canonical_candidates = data.get("canonical_candidates")
    candidates_out = None
    if isinstance(canonical_candidates, list) and canonical_candidates:
        entries = []
        for c in canonical_candidates:
            if isinstance(c, dict):
                entries.append({"path": c.get("path"), "current_status": c.get("current_status")})
            else:
                entries.append({"path": c, "current_status": None})
        candidates_out = sorted(entries, key=lambda e: (e.get("path") or ""))

    normalized = {
        "current_status": data.get("current_status"),
        "rows": rows_out,
        "next_action": next_action,
        "transition_action": transition_action,
        "decision_kind": decision_kind,
    }
    if candidates_out is not None:
        normalized["canonical_candidates"] = candidates_out

    if isinstance(registry_meta, dict) and registry_meta:
        execution_ownership = registry_meta.get("execution_ownership")
        registry_out = {}
        if isinstance(execution_ownership, dict):
            if "generation" in execution_ownership:
                registry_out["generation"] = execution_ownership.get("generation")
        if "attribution_state" in registry_meta:
            registry_out["attribution_state"] = registry_meta.get("attribution_state")
        if registry_out:
            normalized["registry"] = registry_out

    if isinstance(lease, dict) and lease and "generation" in lease:
        normalized["lease_generation"] = lease.get("generation")

    return normalized


def compute(show_json, registry_meta=None, lease=None, decision_kind=None):
    """normalize()의 결과를 canonical JSON으로 직렬화해 SHA-256 hex를 반환한다."""
    normalized = normalize(show_json, registry_meta=registry_meta, lease=lease, decision_kind=decision_kind)
    canonical = json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def save_receipt(project_root, receipt):
    """receipt(dict 또는 StopReceipt)를 stop_receipt_path(project_root, session_id)에 원자 저장한다."""
    if hasattr(receipt, "to_dict"):
        receipt_dict = receipt.to_dict()
    else:
        receipt_dict = dict(receipt)
    session_id = receipt_dict.get("session_id")
    path = ownership_core.stop_receipt_path(project_root, session_id)
    return ownership_core.write_json_atomic(path, receipt_dict)


def load_receipt(project_root, session_id):
    """stop_receipt_path(project_root, session_id)에서 receipt dict를 읽는다. 부재 시 None."""
    path = ownership_core.stop_receipt_path(project_root, session_id)
    result = ownership_core.read_json(path)
    if not result.get("ok"):
        return None
    return result.get("data")
