# @header
# module: ownership_tool.tests.test_fingerprint
# layer: test
# domain: ownership
# description: RED-first — ownership_tool.fingerprint.compute() 공개 계약 검증 (S-6)
# exports: (none — pytest module)
# depends: ownership_tool.fingerprint (미구현), fixtures/fingerprint, fixtures/runtime
"""RED 테스트 — 구현 전. ownership_tool.fingerprint 미구현이므로 ImportError로 실패해야 한다."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES_ROOT = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES_ROOT / "fingerprint" / name).read_text(encoding="utf-8"))


def test_fingerprint_stable_across_note_and_runlog_only_changes():
    """(a)와 (c)는 updated_at/created_at/timestamp/note 자유문/run_log만 다르므로
    fingerprint가 동일해야 한다."""
    from ownership_tool import fingerprint  # RED

    show_a = _load("show-a-baseline.json")
    show_c = _load("show-c-note-runlog-only.json")

    fp_a = fingerprint.compute(show_a, registry_meta={}, lease={}, decision_kind="allow_no_progress_same_fingerprint")
    fp_c = fingerprint.compute(show_c, registry_meta={}, lease={}, decision_kind="allow_no_progress_same_fingerprint")
    assert fp_a == fp_c


def test_fingerprint_changes_on_status_change():
    """(b)는 execute.implement 행 status가 의미 변경되었으므로 fingerprint가 달라야 한다."""
    from ownership_tool import fingerprint  # RED

    show_a = _load("show-a-baseline.json")
    show_b = _load("show-b-status-changed.json")

    fp_a = fingerprint.compute(show_a, registry_meta={}, lease={}, decision_kind="block_continue")
    fp_b = fingerprint.compute(show_b, registry_meta={}, lease={}, decision_kind="block_continue")
    assert fp_a != fp_b


def test_fingerprint_normalized_dict_excludes_volatile_keys():
    """정규화 dict에 updated_at/created_at/timestamp/note 자유문/run_log 키가 없어야 한다."""
    from ownership_tool import fingerprint  # RED

    show_a = _load("show-a-baseline.json")
    normalized = fingerprint.normalize(show_a)
    forbidden = {"updated_at", "created_at", "timestamp", "note", "run_log"}
    assert not (forbidden & set(normalized.keys()))
    for row in normalized.get("rows", []):
        assert not (forbidden & set(row.keys()))


def test_receipt_storage_path_contract(tmp_path):
    """receipt 저장/조회 경로: <project_root>/.opal/run/.runtime/stop-guard/<session_id>.json"""
    from ownership_tool import fingerprint  # RED

    project_root = tmp_path / "task_138"
    project_root.mkdir()
    receipt = {
        "session_id": "sess-live-0001",
        "fingerprint": "abc123",
        "decision_kind": "allow_no_progress_same_fingerprint",
        "decided_at": "2026-09-17T15:40:00+09:00",
        "block_count": 1,
    }
    fingerprint.save_receipt(project_root, receipt)
    expected_path = project_root / ".opal/run/.runtime/stop-guard/sess-live-0001.json"
    assert expected_path.exists()

    loaded = fingerprint.load_receipt(project_root, "sess-live-0001")
    assert loaded["fingerprint"] == "abc123"
