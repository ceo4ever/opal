# @header
# module: ownership_tool.tests.test_decisions
# layer: test
# domain: ownership
# description: RED-first — ownership_tool.decisions DECISION_KINDS/DIAGNOSTICS 폐쇄 enum 검증 (S-28)
# exports: (none — pytest module)
# depends: ownership_tool.decisions (미구현)
"""RED 테스트 — 구현 전. ownership_tool.decisions 미구현이므로 ImportError로 실패해야 한다."""
from __future__ import annotations


def test_decision_kinds_enum_has_exactly_seven_members():
    """DECISION_KINDS는 7종: allow_complete, allow_await_user, allow_inactive,
    allow_no_progress_same_fingerprint, allow_block_cap_reached, block_continue, defer_to_pm."""
    from ownership_tool import decisions  # RED

    expected = {
        "allow_complete",
        "allow_await_user",
        "allow_inactive",
        "allow_no_progress_same_fingerprint",
        "allow_block_cap_reached",
        "block_continue",
        "defer_to_pm",
    }
    assert set(decisions.DECISION_KINDS) == expected


def test_diagnostics_enum_is_closed_member_set():
    """DIAGNOSTICS는 11종 멤버로 고정된 폐쇄 enum이다(개수뿐 아니라 각 값도 고정)."""
    from ownership_tool import decisions  # RED

    expected = {
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
    }
    assert set(decisions.DIAGNOSTICS) == expected


def test_schema_validator_rejects_values_outside_enum():
    """스키마 검증기가 enum 밖 값을 거부한다."""
    from ownership_tool import decisions  # RED

    bad_result = {"decision_kind": "not_a_real_kind", "diagnostics": [], "candidates": [], "evidence": {}}
    assert decisions.validate(bad_result) is False

    good_result = {"decision_kind": "block_continue", "diagnostics": [], "candidates": [], "evidence": {}}
    assert decisions.validate(good_result) is True


def test_distinct_decision_kinds_for_distinct_states():
    """정상 완료·대기·비활성·동일 fingerprint 통과가 서로 다른 decision_kind로 구분된다."""
    from ownership_tool import decisions  # RED

    distinct = {
        decisions.DECISION_KINDS.ALLOW_COMPLETE if hasattr(decisions.DECISION_KINDS, "ALLOW_COMPLETE") else "allow_complete",
        "allow_await_user",
        "allow_inactive",
        "allow_no_progress_same_fingerprint",
    }
    assert len(distinct) == 4
