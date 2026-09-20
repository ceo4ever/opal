"""T03 — driver-verify가 §B.2 8연산을 실제 실행하고 부분 driver를 거부하는지 검증한다."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

from lib.e2e import driver_conformance  # noqa: E402
from lib.e2e import drivers as e2e_drivers  # noqa: E402


class _CompleteDriver(e2e_drivers.BrowserDriver):
    name = "complete"
    session_mode = "standalone"

    def __init__(self, **_kwargs):
        self.calls = []

    def _record(self, operation, output):
        self.calls.append(operation)
        return output

    def op_probe(self, _request):
        return self._record("probe", {"available": True, "capabilities": {}})

    def op_open(self, _request):
        return self._record("open", {"handle": "page-1", "owned": True, "current_url": "about:blank"})

    def op_snapshot(self, _request):
        return self._record("snapshot", {"snapshot": {}, "current_url": "about:blank", "artifact_path": None})

    def op_act(self, _request):
        return self._record("act", {"ok": True, "action_result": {}, "current_url": "about:blank"})

    def op_wait(self, request):
        return self._record("wait", {"satisfied": True, "wait_kind": request["wait_kind"], "elapsed_ms": 1})

    def op_assert(self, request):
        assertion = request["assertion"]
        return self._record("assert", {"id": assertion["id"], "expected": "about:blank", "actual": "about:blank", "passed": True})

    def op_capture(self, _request):
        return self._record("capture", {"artifacts": [], "redacted": True, "redaction_failed": False})

    def op_close(self, _request):
        return self._record("close", {"closed": True, "released": ["page-1"], "leaked": []})


class _PartialDriver(e2e_drivers.BrowserDriver):
    name = "partial"
    session_mode = "standalone"

    def __init__(self, **_kwargs):
        self.calls = []

    def op_probe(self, _request):
        self.calls.append("probe")
        return {"available": True, "capabilities": {}}

    def op_open(self, _request):
        self.calls.append("open")
        return {"handle": "page-1", "owned": True, "current_url": "about:blank"}

    def op_close(self, _request):
        self.calls.append("close")
        return {"closed": True, "released": ["page-1"], "leaked": []}


class _UnavailableDriver(_CompleteDriver):
    def op_probe(self, _request):
        self.calls.append("probe")
        return {"available": False, "unavailable_reason": "binary_absent", "capabilities": {}}


class _DomTextOnlyDriver(_CompleteDriver):
    def op_assert(self, request):
        assertion = request["assertion"]
        if assertion.get("verifier") != "dom_text":
            raise e2e_drivers.DriverError("unsupported_verifier")
        return self._record(
            "assert",
            {
                "id": assertion["id"],
                "expected": assertion["expected"],
                "actual": "",
                "passed": assertion["expected"] == "",
            },
        )


class TestDriverVerify(unittest.TestCase):
    def test_complete_driver_dispatches_all_eight_operations(self):
        instances = []

        def factory(**kwargs):
            instance = _CompleteDriver(**kwargs)
            instances.append(instance)
            return instance

        result = driver_conformance.verify_driver_factory("complete", "standalone", factory)
        self.assertEqual(result["outcome"], "pass")
        self.assertEqual(instances[0].calls, list(e2e_drivers.DRIVER_OPERATIONS))
        self.assertTrue(all(item["executed"] and item["ok"] for item in result["operations"]))

    def test_partial_driver_cannot_pass_and_reports_every_missing_operation(self):
        result = driver_conformance.verify_driver_factory(
            "partial", "standalone", lambda **kwargs: _PartialDriver(**kwargs)
        )
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["missing_operations"], ["snapshot", "act", "wait", "assert", "capture"])
        missing = [item for item in result["operations"] if not item["executed"]]
        self.assertEqual([item["operation"] for item in missing], result["missing_operations"])
        self.assertTrue(all(item["detail_code"] == "driver_operation_unimplemented" for item in missing))

    def test_shape_only_response_cannot_hide_an_unsuccessful_operation(self):
        class _FailedActDriver(_CompleteDriver):
            def op_act(self, _request):
                return self._record("act", {"ok": False, "action_result": {}, "current_url": "about:blank"})

        result = driver_conformance.verify_driver_factory(
            "failed-act", "standalone", lambda **kwargs: _FailedActDriver(**kwargs)
        )
        self.assertEqual(result["outcome"], "failed")
        act = next(item for item in result["operations"] if item["operation"] == "act")
        self.assertEqual(act["detail_code"], "driver_operation_unsuccessful:act")

    def test_provider_unavailable_is_distinct_and_never_promoted_to_pass(self):
        registry = {("offline", "standalone"): lambda **kwargs: _UnavailableDriver(**kwargs)}
        result = driver_conformance.verify_registered_driver("offline", registry=registry)
        self.assertFalse(result["ok"])
        self.assertEqual(result["outcome"], "provider_unavailable")
        self.assertEqual(result["results"][0]["operations"][0]["detail_code"], "binary_absent")

    def test_conformance_assertion_uses_the_cross_driver_dom_text_surface(self):
        result = driver_conformance.verify_driver_factory(
            "dom-text-only", "standalone", lambda **kwargs: _DomTextOnlyDriver(**kwargs)
        )
        self.assertEqual(result["outcome"], "pass")

    def test_executed_variant_failure_is_not_hidden_by_an_unavailable_variant(self):
        class _FailedActDriver(_CompleteDriver):
            def op_act(self, _request):
                return self._record("act", {"ok": False, "action_result": {}, "current_url": "about:blank"})

        registry = {
            ("mixed", "managed"): lambda **kwargs: _FailedActDriver(**kwargs),
            ("mixed", "standalone"): lambda **kwargs: _UnavailableDriver(**kwargs),
        }
        result = driver_conformance.verify_registered_driver("mixed", registry=registry)
        self.assertFalse(result["ok"])
        self.assertEqual(result["outcome"], "failed")

    def test_cli_surface_rejects_an_unregistered_driver_with_structured_json(self):
        completed = subprocess.run(
            [sys.executable, str(_TOOL_DIR / "test_tool.py"), "e2e", "driver-verify", "--driver", "absent-driver"],
            cwd=str(_TOOL_DIR), capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(completed.returncode, 1, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["command"], "e2e driver-verify")
        self.assertEqual(payload["detail_code"], "driver_not_registered")
        self.assertEqual(payload["required_operations"], list(e2e_drivers.DRIVER_OPERATIONS))


if __name__ == "__main__":
    unittest.main()
