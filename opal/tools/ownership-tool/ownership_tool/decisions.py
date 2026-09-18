"""
@header {
  "module": "decisions",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "D-3 폐쇄 enum과 구조화 판정 결과 계약. DECISION_KINDS 7종·DIAGNOSTICS 11종(D-21 passive_ownership 포함)을 고정하고 Decision dataclass와 validate()로 enum 밖 값·필수 키 누락을 거부한다. 어떤 시스템 상태도 읽지 않는 순수 모듈이다.",
  "exports": ["DECISION_KINDS", "DIAGNOSTICS", "RESULT_KEYS", "Decision", "validate"],
  "depends": []
}
"""
from __future__ import annotations

from dataclasses import dataclass, field

# D-3 — decision_kind 폐쇄 enum (7종)
DECISION_KINDS = (
    "allow_complete",
    "allow_await_user",
    "allow_inactive",
    "allow_no_progress_same_fingerprint",
    "allow_block_cap_reached",
    "block_continue",
    "defer_to_pm",
)

# D-3 — diagnostic 폐쇄 enum (11종)
DIAGNOSTICS = (
    "no_owned_task",
    "multiple_hub_tasks",
    "worktree_owned_shadow",
    "foreign_owner",
    "invalid_registry",
    "invalid_state",
    "launch_failed",
    "no_progress_same_fingerprint",
    "lease_expired",
    "foreign_owner_bash_unclassified",
    "passive_ownership",
)

# 구조화 판정 결과의 필수 키
RESULT_KEYS = ("decision_kind", "diagnostics", "candidates", "evidence")


@dataclass
class Decision:
    """구조화 판정 결과 — {decision_kind, diagnostics[], candidates[], evidence{}}."""

    decision_kind: str
    diagnostics: list = field(default_factory=list)
    candidates: list = field(default_factory=list)
    evidence: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "decision_kind": self.decision_kind,
            "diagnostics": list(self.diagnostics),
            "candidates": list(self.candidates),
            "evidence": dict(self.evidence),
        }


def validate(obj):
    """구조화 판정 결과가 D-3 계약을 만족하면 True, 아니면 False.

    거부 사유: dict 아님 · 필수 키 누락 · 미등록 키 · decision_kind가 DECISION_KINDS 밖 ·
    diagnostics 원소가 DIAGNOSTICS 밖 · candidates/evidence 타입 불일치.
    예외를 던지지 않고 bool만 반환한다.
    """
    if isinstance(obj, Decision):
        obj = obj.to_dict()
    if not isinstance(obj, dict):
        return False
    if set(obj.keys()) != set(RESULT_KEYS):
        return False
    if obj["decision_kind"] not in DECISION_KINDS:
        return False
    diagnostics = obj["diagnostics"]
    if not isinstance(diagnostics, (list, tuple)):
        return False
    for item in diagnostics:
        if item not in DIAGNOSTICS:
            return False
    if not isinstance(obj["candidates"], (list, tuple)):
        return False
    if not isinstance(obj["evidence"], dict):
        return False
    return True
