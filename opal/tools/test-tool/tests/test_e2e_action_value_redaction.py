"""
@header {
  "module": "test_e2e_action_value_redaction",
  "layer": "test",
  "domain": "opal-tools",
  "description": "INTENT C-1 — fill/type/select action 입력값이 actions.jsonl에 원문으로 남지 않고 evidence 단일 관문의 fail-closed 저장 계약을 유지하는지 검증한다.",
  "exports": ["TestActionValueRedaction"]
}
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

from lib.e2e import evidence, redaction  # noqa: E402


class TestActionValueRedaction(unittest.TestCase):
    def test_masks_value_for_every_value_action_and_both_log_shapes(self):
        rows = [
            {"kind": "fill", "target": "#password", "value": "fill-secret"},
            {"action": "type", "target": "#token", "value": "type-secret"},
            {"action": "SELECT", "target": "#account", "value": "select-secret"},
            {"operation": "act", "action": {"kind": "fill", "target": "#nested", "value": "nested-secret"}},
        ]

        masked, fields = redaction.redact_value(rows, path="actions.jsonl")

        self.assertEqual(masked[0]["value"], redaction.MASK)
        self.assertEqual(masked[1]["value"], redaction.MASK)
        self.assertEqual(masked[2]["value"], redaction.MASK)
        self.assertEqual(masked[3]["action"]["value"], redaction.MASK)
        self.assertEqual(masked[0]["target"], "#password")
        self.assertEqual(
            fields,
            [
                "actions.jsonl[0].value",
                "actions.jsonl[1].value",
                "actions.jsonl[2].value",
                "actions.jsonl[3].action.value",
            ],
        )

    def test_does_not_mask_unrelated_value_fields(self):
        payload = {
            "kind": "navigate",
            "value": "https://example.test/public",
            "assertion": {"field": "status", "value": "ready"},
        }

        masked, fields = redaction.redact_value(payload)

        self.assertEqual(masked, payload)
        self.assertEqual(fields, [])

    def test_actions_jsonl_single_gateway_never_persists_raw_input(self):
        secrets = ("fill-secret", "type-secret", "select-secret")
        rows = [
            {"action": action, "target": f"#{action}", "value": secret}
            for action, secret in zip(("fill", "type", "select"), secrets)
        ]

        with tempfile.TemporaryDirectory() as artifact_dir:
            writer = evidence.EvidenceWriter(artifact_dir, run_id="action-value-redaction")
            path = pathlib.Path(
                writer.write_jsonl("actions.jsonl", rows, kind="action_log")
            )
            contents = path.read_text(encoding="utf-8")
            persisted = [json.loads(line) for line in contents.splitlines()]

            for secret in secrets:
                self.assertNotIn(secret, contents)
            self.assertEqual([row["value"] for row in persisted], [redaction.MASK] * 3)
            self.assertEqual(writer.observed(), ["action_log"])
            self.assertEqual(
                writer.redaction_records()[0]["redacted_fields"],
                ["actions.jsonl[0].value", "actions.jsonl[1].value", "actions.jsonl[2].value"],
            )

    def test_redaction_failure_leaves_no_original_or_partial_action_log(self):
        with tempfile.TemporaryDirectory() as artifact_dir:
            writer = evidence.EvidenceWriter(artifact_dir, run_id="redaction-failure")
            with mock.patch.object(
                redaction,
                "redact_value",
                side_effect=redaction.RedactionError("redaction_injected_failure"),
            ):
                with self.assertRaisesRegex(evidence.EvidenceError, "redaction_injected_failure") as raised:
                    writer.write_jsonl(
                        "actions.jsonl",
                        [{"action": "fill", "target": "#pw", "value": "must-not-reach-disk"}],
                        kind="action_log",
                    )

            self.assertEqual(raised.exception.detail_code, "evidence_redaction_failed")
            self.assertFalse(pathlib.Path(artifact_dir, "actions.jsonl").exists())
            self.assertFalse(pathlib.Path(artifact_dir, "actions.jsonl.partial").exists())


if __name__ == "__main__":
    unittest.main()
