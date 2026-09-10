"""
@header {
  "module": "test_event_loader",
  "layer": "test",
  "domain": "opal-tools",
  "description": "event-loader 공개 CLI의 receipt 누락·event 불일치·문서 hash stale 거부 계약을 고정하는 RED-first 테스트",
  "task": "113",
  "scenarios": ["S-1"],
  "exports": ["TestReceiptVerification"]
}

TASK 113 RED-first 테스트.
프로덕션 내부 함수 대신 run.sh의 exit code와 stdout JSON만 검증한다.
"""

import json
import pathlib
import subprocess
import tempfile
import unittest


_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"
_SOURCE_ROOT = _TOOL_DIR.parents[2]


def _run(args):
    result = subprocess.run(
        ["bash", str(_RUN_SH), *args],
        capture_output=True,
        text=True,
        cwd=_SOURCE_ROOT,
    )
    stdout = result.stdout.strip()
    try:
        payload = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        payload = {"_raw": stdout}
    return result, payload


def _write_receipt(path, receipt):
    if isinstance(receipt, str):
        path.write_text(receipt, encoding="utf-8")
    else:
        path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")


def _mutate_first_sha256(value):
    """Public load output의 receipt를 불투명하게 다루되 첫 hash만 stale로 만든다."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"sha256", "hash"} and isinstance(child, str):
                value[key] = "0" * 64
                return True
            if _mutate_first_sha256(child):
                return True
    elif isinstance(value, list):
        for child in value:
            if _mutate_first_sha256(child):
                return True
    return False


class TestReceiptVerification(unittest.TestCase):
    """S-1: verify는 invalid receipt 3종을 non-zero 구조화 오류로 거부한다."""

    def _load_assistant_receipt(self):
        result, payload = _run(["load", "--event", "session.assistant"])
        self.assertEqual(
            result.returncode,
            0,
            "valid session.assistant load가 먼저 성공해야 한다. "
            f"exit={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertTrue(payload.get("ok"), payload)
        self.assertIn("receipt", payload, payload)
        return payload["receipt"]

    def test_missing_receipt_is_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = pathlib.Path(tmp) / "missing-receipt.json"
            result, payload = _run(["verify", "--receipt", str(missing)])

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload.get("ok", True), payload)
        self.assertEqual(payload.get("command"), "verify", payload)
        self.assertIn(
            payload.get("error"),
            {"receipt_not_found", "missing_receipt"},
            payload,
        )

    def test_wrong_event_receipt_is_rejected(self):
        receipt = self._load_assistant_receipt()
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = pathlib.Path(tmp) / "receipt.json"
            _write_receipt(receipt_path, receipt)
            result, payload = _run(
                [
                    "verify",
                    "--receipt",
                    str(receipt_path),
                    "--event",
                    "session.worker",
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload.get("ok", True), payload)
        self.assertIn(
            payload.get("error"),
            {"event_mismatch", "receipt_event_mismatch", "wrong_event"},
            payload,
        )

    def test_stale_document_hash_is_rejected(self):
        receipt = self._load_assistant_receipt()
        self.assertIsInstance(receipt, dict, "stale hash 검증용 receipt는 JSON object여야 한다")
        self.assertTrue(
            _mutate_first_sha256(receipt),
            f"receipt에 문서 sha256이 없다: {receipt}",
        )
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = pathlib.Path(tmp) / "stale-receipt.json"
            _write_receipt(receipt_path, receipt)
            result, payload = _run(
                [
                    "verify",
                    "--receipt",
                    str(receipt_path),
                    "--event",
                    "session.assistant",
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload.get("ok", True), payload)
        self.assertIn(
            payload.get("error"),
            {"stale_receipt", "document_hash_mismatch", "receipt_stale"},
            payload,
        )


if __name__ == "__main__":
    unittest.main()
