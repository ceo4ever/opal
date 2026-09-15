"""
@header {
  "module": "test_e2e_drivers",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "T05 — Browser driver 8연산 계약(CONTRACT.md §B.2), driver manifest semver 게이트(§A.15), §A.8 probe 정규화와 probe.json 기록, 증적 단일 관문(§A.12)의 redaction·실패 시 부분 파일 미잔존을 검증한다.",
  "scenarios": ["S-7"],
  "exports": [
    "TestDriverManifest", "TestSemverGate", "TestProbeNormalization",
    "TestDriverOperationContract", "TestCandidateResolution",
    "TestEvidenceGateRedaction", "TestEvidenceGateFailure"
  ]
}

이 스위트는 W-3 산출물(`lib/e2e/drivers/`·`lib/e2e/evidence.py`·`lib/e2e/redaction.py`)의
계약 표면만 검사한다. 구체 driver 구현(agent-browser·cmux)은 W-5·W-6 소유이므로 여기서는
가짜 후보를 등록해 resolver의 순서·제외 규칙만 고정한다.
"""
from __future__ import annotations

import json
import pathlib
import stat
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

from lib.e2e import drivers as e2e_drivers  # noqa: E402
from lib.e2e import evidence as e2e_evidence  # noqa: E402
from lib.e2e import redaction as e2e_redaction  # noqa: E402


class _StubDriver(e2e_drivers.BrowserDriver):
    """probe 반환값을 주입받는 최소 driver — 계약 표면만 만족한다."""

    def __init__(self, *, probe_payload=None, version=None, raise_on_probe=None, **_kwargs):
        self.name = "agent-browser"
        self.binary_path = "/nonexistent/agent-browser"
        self.resolution_source = "orca-bundle"
        self.declared_version = version
        self._probe_payload = probe_payload or {}
        self._raise_on_probe = raise_on_probe
        self.probe_calls = 0

    def op_probe(self, request):
        self.probe_calls += 1
        if self._raise_on_probe:
            raise e2e_drivers.DriverError(self._raise_on_probe)
        return self._probe_payload


def _all_caps_available():
    return {
        key: {"available": True, "route": "native", "probed": True}
        for key in e2e_drivers.CAPABILITY_KEYS
    }


class TestDriverManifest(unittest.TestCase):
    """§A.15 — 버전 정책의 단일 SSOT는 manifest.json 한 곳이다."""

    def test_manifest_declares_three_policy_fields_per_driver(self):
        manifest = e2e_drivers.load_manifest()
        self.assertEqual(manifest["schema_version"], e2e_drivers.MANIFEST_SCHEMA_VERSION)
        self.assertIn("agent-browser", manifest["drivers"])
        for name, policy in manifest["drivers"].items():
            with self.subTest(driver=name):
                for key in ("minimum_version", "tested_range", "ci_pin"):
                    self.assertIn(key, policy)

    def test_manifest_driver_names_are_within_the_contract_enum(self):
        manifest = e2e_drivers.load_manifest()
        allowed = {"agent-browser", "cmux", "playwright"}
        self.assertTrue(set(manifest["drivers"]) <= allowed, manifest["drivers"])

    def test_version_literals_are_not_duplicated_in_driver_code(self):
        """§A.15 [MUST]: 값 갱신은 manifest에서만 한다 — 코드에 버전 리터럴을 복제하지 않는다."""
        source = (_TOOL_DIR / "lib" / "e2e" / "drivers" / "__init__.py").read_text(encoding="utf-8")
        manifest = e2e_drivers.load_manifest()
        for name, policy in manifest["drivers"].items():
            with self.subTest(driver=name):
                self.assertNotIn(f'"{policy["minimum_version"]}"', source)


class TestSemverGate(unittest.TestCase):
    """§A.15 [MUST] — 버전 비교는 문자열 비교가 아니라 semver 비교다."""

    def test_double_digit_minor_is_ordered_numerically_not_lexically(self):
        # 문자열 비교라면 "0.9.0" > "0.10.0"으로 뒤집힌다.
        self.assertEqual(e2e_drivers.compare_versions("0.9.0", "0.10.0"), -1)
        self.assertEqual(e2e_drivers.compare_versions("0.27.0", "0.27.0"), 0)
        self.assertEqual(e2e_drivers.compare_versions("1.2.10", "1.2.9"), 1)

    def test_minimum_version_boundary_is_inclusive(self):
        self.assertTrue(e2e_drivers.meets_minimum_version("0.27.0", "0.27.0"))
        self.assertFalse(e2e_drivers.meets_minimum_version("0.26.9", "0.27.0"))

    def test_prefix_and_v_forms_parse(self):
        self.assertEqual(e2e_drivers.parse_semver("v0.27.0"), (0, 27, 0))
        self.assertEqual(e2e_drivers.parse_semver("0.27"), (0, 27, 0))
        self.assertIsNone(e2e_drivers.parse_semver("not-a-version"))

    def test_unparsable_version_is_an_explicit_error_not_a_silent_pass(self):
        with self.assertRaises(e2e_drivers.DriverError):
            e2e_drivers.compare_versions("nightly", "0.27.0")

    def test_tested_range_wildcard_and_interval(self):
        self.assertTrue(e2e_drivers.in_tested_range("0.27.5", "0.27.x"))
        self.assertFalse(e2e_drivers.in_tested_range("0.28.0", "0.27.x"))
        self.assertTrue(e2e_drivers.in_tested_range("1.50.0", "1.40.x - 1.55.x"))
        self.assertFalse(e2e_drivers.in_tested_range("1.60.0", "1.40.x - 1.55.x"))


class TestProbeNormalization(unittest.TestCase):
    """§A.8 — capability 6키는 미확인 상태에서도 존재하고, probed=false는 available=false다."""

    def test_default_capabilities_carry_all_six_keys_in_a81_shape(self):
        caps = e2e_drivers.default_capabilities()
        self.assertEqual(sorted(caps), sorted(e2e_drivers.CAPABILITY_KEYS))
        for key, item in caps.items():
            with self.subTest(capability=key):
                self.assertEqual(item, {"available": False, "route": "exec", "probed": False})

    def test_unprobed_capability_is_never_promoted_to_available(self):
        raw = {
            "available": True,
            "version": "0.27.0",
            "capabilities": {
                # 후보가 available=true를 주장하지만 probe하지 않았다 — 보수적으로 false다.
                "network_har": {"available": True, "route": "native", "probed": False},
                "console": {"available": True, "route": "exec", "probed": True},
            },
        }
        probe = e2e_drivers.normalize_probe_result(raw, driver="agent-browser", session_mode="orca-managed")
        self.assertFalse(probe["capabilities"]["network_har"]["available"])
        self.assertFalse(probe["capabilities"]["network_har"]["probed"])
        self.assertTrue(probe["capabilities"]["console"]["available"])

    def test_missing_capability_block_yields_the_conservative_default(self):
        probe = e2e_drivers.normalize_probe_result({"available": False}, driver="cmux", session_mode="owned-surface")
        self.assertEqual(sorted(probe["capabilities"]), sorted(e2e_drivers.CAPABILITY_KEYS))
        self.assertFalse(probe["available"])
        self.assertIsNotNone(probe["unavailable_reason"])

    def test_unavailable_reason_is_the_candidate_original_code(self):
        probe = e2e_drivers.normalize_probe_result(
            {"available": False, "unavailable_reason": "orca_runtime_absent"},
            driver="agent-browser",
            session_mode="orca-managed",
        )
        # NR-7: 하네스가 사유를 재작문하지 않는다.
        self.assertEqual(probe["unavailable_reason"], "orca_runtime_absent")


class TestDriverOperationContract(unittest.TestCase):
    """§B.2 — 8연산 이름과 C-DRV-1 wait_kind 필수."""

    def test_exactly_the_eight_contract_operations_are_declared(self):
        self.assertEqual(
            sorted(e2e_drivers.DRIVER_OPERATIONS),
            sorted(["probe", "open", "snapshot", "act", "wait", "assert", "capture", "close"]),
        )

    def test_unknown_operation_is_rejected(self):
        with self.assertRaises(e2e_drivers.DriverError):
            _StubDriver().dispatch("navigate", {})

    def test_wait_without_wait_kind_never_reaches_the_driver(self):
        """C-DRV-1 [MUST] — wait_kind 생략 시 실행하지 않고 오류를 반환한다."""

        class _WaitDriver(_StubDriver):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.wait_calls = 0

            def op_wait(self, request):
                self.wait_calls += 1
                return {"satisfied": True, "wait_kind": request.get("wait_kind"), "elapsed_ms": 0}

        driver = _WaitDriver()
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            driver.dispatch("wait", {"handle": "h1", "condition": "visible", "timeout_ms": 100})
        self.assertEqual(ctx.exception.detail_code, "driver_wait_kind_required")
        self.assertEqual(driver.wait_calls, 0)

    def test_wait_kind_must_be_one_of_the_contract_enum(self):
        with self.assertRaises(e2e_drivers.DriverError):
            _StubDriver().dispatch("wait", {"handle": "h1", "wait_kind": "whenever"})

    def test_unimplemented_operation_reports_itself_rather_than_returning_a_fake_result(self):
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            _StubDriver().dispatch("open", {"url": "http://127.0.0.1:1", "isolation_key": "k"})
        self.assertEqual(ctx.exception.detail_code, "driver_operation_unimplemented")


class TestCandidateResolution(unittest.TestCase):
    """§A.1.2 · C-DRV-3 — 후보 순서, minimum_version probe-없는 제외, selected ≤ 1."""

    def _manifest(self):
        return {
            "schema_version": "1.0",
            "drivers": {
                "agent-browser": {"minimum_version": "0.27.0", "tested_range": "0.27.x", "ci_pin": "0.27.0"},
                "cmux": {"minimum_version": "0.0.0", "tested_range": "*", "ci_pin": "0.0.0"},
            },
        }

    def test_empty_registry_records_every_candidate_as_provider_unavailable(self):
        candidates, probes = e2e_drivers.resolve_candidates(registry={}, manifest=self._manifest())
        self.assertEqual(probes, [])
        self.assertTrue(candidates)
        self.assertEqual([item["outcome"] for item in candidates], ["provider_unavailable"] * len(candidates))
        self.assertEqual([item["order"] for item in candidates], list(range(1, len(candidates) + 1)))

    def test_candidate_order_follows_cdrv3(self):
        candidates, _ = e2e_drivers.resolve_candidates(registry={}, manifest=self._manifest())
        self.assertEqual(
            [(item["driver"], item["session_mode"]) for item in candidates],
            [("agent-browser", "orca-managed"), ("cmux", "owned-surface"), ("agent-browser", "standalone")],
        )

    def test_playwright_is_opt_in_only(self):
        candidates, _ = e2e_drivers.resolve_candidates(
            registry={}, manifest=self._manifest(), opt_in_drivers=["playwright"]
        )
        self.assertIn("playwright", [item["driver"] for item in candidates])

    def test_below_minimum_version_is_excluded_without_probing(self):
        """§A.15 [MUST] — minimum_version 미만은 probe 없이 제외하고 excluded_by·version을 남긴다."""
        stub = _StubDriver(version="0.26.9", probe_payload={"available": True, "capabilities": _all_caps_available()})
        candidates, probes = e2e_drivers.resolve_candidates(
            registry={("agent-browser", "orca-managed"): lambda **_: stub},
            manifest=self._manifest(),
        )
        record = candidates[0]
        self.assertEqual(record["outcome"], "excluded")
        self.assertEqual(record["excluded_by"], "minimum_version")
        self.assertEqual(record["version"], "0.26.9")
        self.assertEqual(stub.probe_calls, 0, "제외된 후보를 probe해서는 안 된다")
        self.assertEqual(probes, [])

    def test_available_candidate_is_selected_and_later_candidates_are_not_attempted(self):
        stub = _StubDriver(
            version="0.27.0",
            probe_payload={"available": True, "version": "0.27.0", "capabilities": _all_caps_available()},
        )
        later = _StubDriver(version="0.27.0", probe_payload={"available": True, "capabilities": _all_caps_available()})
        candidates, probes = e2e_drivers.resolve_candidates(
            registry={
                ("agent-browser", "orca-managed"): lambda **_: stub,
                ("cmux", "owned-surface"): lambda **_: later,
            },
            manifest=self._manifest(),
        )
        selected = [item for item in candidates if item["outcome"] == "selected"]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["driver"], "agent-browser")
        self.assertEqual(selected[0]["binary_path"], "/nonexistent/agent-browser")
        self.assertEqual(selected[0]["resolution_source"], "orca-bundle")
        self.assertEqual(later.probe_calls, 0)
        self.assertEqual(len(probes), 1)

    def test_missing_required_capability_excludes_by_capability_missing(self):
        caps = _all_caps_available()
        caps["network_har"] = {"available": False, "route": "exec", "probed": True}
        stub = _StubDriver(version="0.27.0", probe_payload={"available": True, "capabilities": caps})
        candidates, _ = e2e_drivers.resolve_candidates(
            registry={("agent-browser", "orca-managed"): lambda **_: stub},
            manifest=self._manifest(),
            required_capabilities=["network_har"],
        )
        self.assertEqual(candidates[0]["outcome"], "excluded")
        self.assertEqual(candidates[0]["excluded_by"], "capability_missing")

    def test_probe_failure_outside_tested_range_is_infra_error_and_stops_candidate_walk(self):
        """§A.15·§C.7 — tested_range 밖 binary의 probe 실패는 excluded가 아니라 infra_error이며,
        조용한 fallback 없이 중단한다."""
        stub = _StubDriver(version="0.99.0", raise_on_probe="probe_exec_failed")
        never = _StubDriver(version="0.27.0", probe_payload={"available": True, "capabilities": _all_caps_available()})
        candidates, _ = e2e_drivers.resolve_candidates(
            registry={
                ("agent-browser", "orca-managed"): lambda **_: stub,
                ("cmux", "owned-surface"): lambda **_: never,
            },
            manifest=self._manifest(),
        )
        self.assertEqual(candidates[0]["outcome"], "infra_error")
        self.assertEqual(candidates[0]["reason"], "probe_exec_failed")
        self.assertEqual(len(candidates), 1, "infra_error 이후 다음 후보를 시도해서는 안 된다")
        self.assertEqual(never.probe_calls, 0)

    def test_every_candidate_record_carries_the_a12_field_set(self):
        candidates, _ = e2e_drivers.resolve_candidates(registry={}, manifest=self._manifest())
        for record in candidates:
            with self.subTest(order=record["order"]):
                self.assertEqual(
                    sorted(record),
                    sorted([
                        "order", "type", "driver", "session_mode", "binary_path",
                        "resolution_source", "version", "outcome", "excluded_by", "reason",
                    ]),
                )


class TestEvidenceGateRedaction(unittest.TestCase):
    """§A.12 · TASK.md C-6 — 저장 전 Authorization·Cookie·Set-Cookie·query secret 마스킹."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.writer = e2e_evidence.EvidenceWriter(self.tmp.name, "e2e-20260914-001")

    def tearDown(self):
        self.tmp.cleanup()

    def _read(self, rel):
        return (pathlib.Path(self.tmp.name) / rel).read_text(encoding="utf-8")

    def test_secret_headers_are_masked_at_any_nesting_depth(self):
        self.writer.write_json(
            "api/requests.jsonl.json",
            {"request": {"headers": {"Authorization": "Bearer sk-secret-1", "Cookie": "session=abc123"}}},
        )
        body = self._read("api/requests.jsonl.json")
        self.assertNotIn("sk-secret-1", body)
        self.assertNotIn("abc123", body)
        self.assertIn(e2e_redaction.MASK, body)

    def test_set_cookie_response_header_is_masked(self):
        self.writer.write_json("api/responses.json", {"headers": {"Set-Cookie": "sid=deadbeef; Path=/"}})
        self.assertNotIn("deadbeef", self._read("api/responses.json"))

    def test_query_secret_in_url_is_masked_but_path_survives(self):
        self.writer.write_json(
            "actions.jsonl.json", {"url": "http://127.0.0.1:9/api/projects?api_key=leak-me&page=2"}
        )
        body = self._read("actions.jsonl.json")
        self.assertNotIn("leak-me", body)
        self.assertIn("/api/projects", body)
        self.assertIn("page=2", body, "비밀이 아닌 query는 보존해야 진단이 가능하다")

    def test_server_log_text_is_masked_line_by_line(self):
        self.writer.write_text(
            "server/backend.log",
            "GET /x?token=leak-me-99 200\nAuthorization: Bearer sk-abc\nplain line\n",
        )
        body = self._read("server/backend.log")
        self.assertNotIn("leak-me-99", body)
        self.assertNotIn("sk-abc", body)
        self.assertIn("plain line", body)

    def test_redaction_records_name_the_artifact_and_the_masked_fields(self):
        self.writer.write_json("actions.jsonl.json", {"headers": {"Authorization": "Bearer x"}})
        record = self.writer.redaction_records()[-1]
        self.assertEqual(sorted(record), ["artifact_path", "redacted_fields", "redaction_failed"])
        self.assertFalse(record["redaction_failed"])
        self.assertTrue(record["redacted_fields"])

    def test_jsonl_rows_are_masked_individually(self):
        self.writer.write_jsonl(
            "actions.jsonl",
            [{"seq": 1, "request": {"headers": {"Cookie": "s=secret-row-1"}}}, {"seq": 2}],
        )
        body = self._read("actions.jsonl")
        self.assertNotIn("secret-row-1", body)
        self.assertEqual(len(body.strip().splitlines()), 2)

    def test_observed_evidence_reports_only_kinds_that_were_actually_filled(self):
        self.writer.write_jsonl("actions.jsonl", [], kind="action_log", observed=False)
        self.writer.write_json("cleanup.json", {"result": "complete"}, kind="cleanup")
        self.assertEqual(self.writer.observed(e2e_evidence.COMMON_REQUIRED_EVIDENCE), ["cleanup"])

    def test_scenario_alias_is_reported_in_the_scenario_own_vocabulary(self):
        self.writer.write_json("assertions.json", {"results": []}, kind="assertion_evidence")
        self.assertIn("assertions", self.writer.observed(["assertions"]))


class TestEvidenceGateFailure(unittest.TestCase):
    """TASK.md C-6 — 마스킹·저장 실패 시 원문도 부분 파일도 남기지 않는다."""

    def test_unserializable_value_is_refused_before_any_file_appears(self):
        with tempfile.TemporaryDirectory() as tmp:
            writer = e2e_evidence.EvidenceWriter(tmp, "e2e-20260914-001")
            with self.assertRaises(e2e_evidence.EvidenceError):
                writer.write_json("actions.jsonl.json", {"handle": object()})
            self.assertEqual([p for p in pathlib.Path(tmp).rglob("*") if p.is_file()], [])

    def test_unwritable_directory_raises_and_leaves_no_partial_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            root.chmod(stat.S_IRUSR | stat.S_IXUSR)
            try:
                writer = e2e_evidence.EvidenceWriter(tmp, "e2e-20260914-001")
                with self.assertRaises(e2e_evidence.EvidenceError) as ctx:
                    writer.write_json("run.json", {"status": "pass"})
                self.assertEqual(ctx.exception.detail_code, "evidence_write_failed")
            finally:
                root.chmod(stat.S_IRWXU)
            self.assertEqual([p for p in root.rglob("*") if p.is_file()], [])

    def test_purge_removes_every_file_the_gate_wrote(self):
        with tempfile.TemporaryDirectory() as tmp:
            writer = e2e_evidence.EvidenceWriter(tmp, "e2e-20260914-001")
            writer.write_json("run.json", {"status": "infra_error"}, kind="metadata")
            writer.write_text("server/backend.log", "line\n", kind="server_log")
            self.assertTrue([p for p in pathlib.Path(tmp).rglob("*") if p.is_file()])
            writer.purge()
            self.assertEqual([p for p in pathlib.Path(tmp).rglob("*") if p.is_file()], [])

    def test_probe_json_is_written_as_a_per_candidate_array(self):
        """§A.8 — probe.json은 단일 객체가 아니라 후보별 결과 배열이다."""
        with tempfile.TemporaryDirectory() as tmp:
            writer = e2e_evidence.EvidenceWriter(tmp, "e2e-20260914-001")
            probes = [
                e2e_drivers.normalize_probe_result({"available": False}, driver="agent-browser", session_mode="orca-managed"),
                e2e_drivers.normalize_probe_result({"available": False}, driver="cmux", session_mode="owned-surface"),
            ]
            path = e2e_drivers.write_probe_json(writer, probes)
            data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "2.0")
            self.assertEqual(len(data["probes"]), 2)
            self.assertEqual([item["driver"] for item in data["probes"]], ["agent-browser", "cmux"])


if __name__ == "__main__":
    unittest.main()


class TestBuiltinDriverRegistration(unittest.TestCase):
    """내장 driver가 실제로 레지스트리에 등록된다 — 등록 누락은 모든 후보를
    `no_registered_driver`로 떨어뜨려 원인을 가린다."""

    def test_agent_browser_is_registered_for_both_session_modes(self):
        registry = e2e_drivers.registered_drivers()
        self.assertIn(("agent-browser", "orca-managed"), registry)
        self.assertIn(("agent-browser", "standalone"), registry)

    def test_registry_is_not_empty_after_importing_the_package(self):
        self.assertTrue(
            e2e_drivers.registered_drivers(),
            "drivers 패키지 import만으로 내장 driver 등록이 끝나야 한다",
        )

    def test_registered_keys_are_within_the_contract_candidate_order(self):
        allowed = {(entry["driver"], entry["session_mode"]) for entry in e2e_drivers.CANDIDATE_ORDER}
        for key in e2e_drivers.registered_drivers():
            with self.subTest(candidate=key):
                self.assertIn(key, allowed, "C-DRV-3 후보 순서에 없는 조합이 등록됐다")

    def test_registered_factories_build_a_driver_honouring_the_operation_contract(self):
        factory = e2e_drivers.registered_drivers()[("agent-browser", "orca-managed")]
        driver = factory(runtime_context={})
        self.assertIsInstance(driver, e2e_drivers.BrowserDriver)
        # C-DRV-1은 구체 driver에도 그대로 적용된다.
        with self.assertRaises(e2e_drivers.DriverError):
            driver.dispatch("wait", {"handle": "h1"})

    def test_a_broken_builtin_module_fails_loudly_instead_of_registering_nothing(self):
        original = e2e_drivers._BUILTIN_DRIVER_MODULES
        e2e_drivers._BUILTIN_DRIVER_MODULES = ("no_such_driver_module",)
        try:
            with self.assertRaises(e2e_drivers.DriverError) as ctx:
                e2e_drivers._load_builtin_drivers()
            self.assertEqual(ctx.exception.detail_code, "driver_module_import_failed")
        finally:
            e2e_drivers._BUILTIN_DRIVER_MODULES = original

    def test_adding_a_driver_needs_only_a_module_name(self):
        """W-6의 `cmux` 추가가 목록 한 줄로 끝나야 한다 — 등록 지점이 하나임을 고정한다."""
        self.assertIsInstance(e2e_drivers._BUILTIN_DRIVER_MODULES, tuple)
        self.assertIn("agent_browser", e2e_drivers._BUILTIN_DRIVER_MODULES)


class TestJournalTransitionOrder(unittest.TestCase):
    """CONTRACT.md §A.2.1 — sut_starting → sut_ready → profile_resolved → executor_ready.

    이 머신에는 가용 후보가 없어 진행 경로가 실행되지 않으므로, 스텁 후보를 주입해
    전이 순서만 관측한다. SUT 기동은 스텁으로 대체한다(실제 프로세스를 띄우지 않는다).
    """

    def setUp(self):
        from lib.e2e import orchestrator as e2e_orchestrator

        self.orchestrator = e2e_orchestrator
        self.source_root = _TOOL_DIR.parent.parent.parent
        self.task_path = self.source_root / "tasks" / "127-260912-oppl-E2E-하네스-구현"
        self._saved = (e2e_orchestrator._resolve_executor_candidates, e2e_orchestrator._start_sut)

    def tearDown(self):
        (
            self.orchestrator._resolve_executor_candidates,
            self.orchestrator._start_sut,
        ) = self._saved

    def _run(self, *, selected: bool):
        import os

        candidate = {
            "order": 1,
            "type": "browser",
            "driver": "agent-browser",
            "session_mode": "orca-managed",
            "binary_path": "/nonexistent/agent-browser",
            "resolution_source": "orca-bundle",
            "version": "0.27.0",
            "outcome": "selected" if selected else "provider_unavailable",
            "excluded_by": None,
            "reason": None if selected else "stubbed_unavailable",
        }
        self.orchestrator._resolve_executor_candidates = lambda scenario, **_kwargs: ([candidate], [])
        # SUT 기동은 이 테스트의 대상이 아니다 — 실제 uvicorn·vite를 띄우지 않는다.
        self.orchestrator._start_sut = lambda **_kwargs: []

        with tempfile.TemporaryDirectory() as artifact_dir:
            previous = os.environ.get("OPAL_E2E_ARTIFACT_DIR")
            os.environ["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir
            try:
                payload = self.orchestrator.run_e2e(
                    target="source-worktree",
                    scenario_id="S-8",
                    task_path=str(self.task_path),
                    worktree_root=str(self.source_root),
                )
            finally:
                if previous is None:
                    os.environ.pop("OPAL_E2E_ARTIFACT_DIR", None)
                else:
                    os.environ["OPAL_E2E_ARTIFACT_DIR"] = previous
            journal = json.loads((pathlib.Path(artifact_dir) / "journal.json").read_text(encoding="utf-8"))
        return payload, [item["to"] for item in journal["transitions"]]

    def test_selected_candidate_emits_the_a21_order(self):
        _payload, states = self._run(selected=True)
        order = [
            self.orchestrator.STATE_SUT_STARTING,
            self.orchestrator.STATE_SUT_READY,
            self.orchestrator.STATE_PROFILE_RESOLVED,
            self.orchestrator.STATE_EXECUTOR_READY,
        ]
        positions = [states.index(state) for state in order]
        self.assertEqual(positions, sorted(positions), f"§A.2.1 순서 위반: {states}")
        self.assertEqual(states[positions[0]: positions[-1] + 1], order)

    def test_profile_resolved_follows_sut_ready_on_the_progress_path(self):
        """진행 경로에서 profile_resolved가 sut_ready보다 앞서면 §A.2.1 위반이다."""
        _payload, states = self._run(selected=True)
        self.assertLess(
            states.index(self.orchestrator.STATE_SUT_READY),
            states.index(self.orchestrator.STATE_PROFILE_RESOLVED),
        )

    def test_executor_ready_is_emitted_exactly_once(self):
        _payload, states = self._run(selected=True)
        self.assertEqual(states.count(self.orchestrator.STATE_EXECUTOR_READY), 1)

    def test_no_selected_candidate_keeps_the_shortcut_and_never_starts_a_sut(self):
        """§A.1.2 [MUST] — selected 0건이면 executor_unavailable이며 SUT를 기동하지 않는다."""
        payload, states = self._run(selected=False)
        self.assertEqual(payload["status"], "executor_unavailable")
        self.assertIn(self.orchestrator.STATE_PROFILE_RESOLVED, states)
        self.assertNotIn(self.orchestrator.STATE_SUT_STARTING, states)
        self.assertNotIn(self.orchestrator.STATE_EXECUTOR_READY, states)

    def test_every_emitted_state_is_within_the_a21_enum(self):
        for selected in (True, False):
            with self.subTest(selected=selected):
                _payload, states = self._run(selected=selected)
                known = {
                    getattr(self.orchestrator, name)
                    for name in dir(self.orchestrator)
                    if name.startswith("STATE_")
                }
                known |= set(e2e_contract_final_statuses())
                for state in states:
                    self.assertIn(state, known, f"§A.2.1 enum 밖의 상태: {state}")


def e2e_contract_final_statuses():
    from lib import e2e_contract

    return tuple(e2e_contract.FINAL_STATUSES)


class TestSutDependentProbeOrdering(unittest.TestCase):
    """§A.8 [MUST] — api executor의 probe는 실제 SUT `/health`를 호출해야 가용성을
    확정하므로, 후보 해석이 `sut_ready` **뒤**에 와야 한다(NR-7: 설정값 존재로 추정 금지).
    """

    def setUp(self):
        from lib.e2e import executors as e2e_executors
        from lib.e2e import orchestrator as e2e_orchestrator

        self.executors = e2e_executors
        self.orchestrator = e2e_orchestrator
        self.source_root = _TOOL_DIR.parent.parent.parent
        self.task_path = self.source_root / "tasks" / "127-260912-oppl-E2E-하네스-구현"
        self._saved_start = e2e_orchestrator._start_sut
        self._saved_registry = e2e_executors.registered_executors
        self.probe_contexts = []
        self.events = []

    def tearDown(self):
        self.orchestrator._start_sut = self._saved_start
        self.executors.registered_executors = self._saved_registry

    def _stub_api_factory(self):
        outer = self

        class _StubApi(self.executors.Executor):
            executor_type = "api"
            operations = self.executors.API_OPERATIONS
            capability_keys = self.executors.API_CAPABILITY_KEYS

            def __init__(self, *, runtime_context=None, **_kwargs):
                self.runtime_context = dict(runtime_context or {})

            def op_probe(self, request):
                outer.events.append("probe")
                outer.probe_contexts.append(dict(self.runtime_context))
                # 실제 api executor와 같은 형태로, probe한 것만 available로 올린다.
                return {
                    "executor": "api",
                    "available": bool(self.runtime_context.get("backend_url")),
                    "version": None,
                    "capabilities": {
                        key: {"available": True, "route": "native", "probed": True}
                        for key in self.capability_keys
                    },
                }

        return lambda **kwargs: _StubApi(**kwargs)

    def _run_api_profile(self):
        import os

        def _recording_start_sut(**_kwargs):
            self.events.append("start_sut")
            return []

        self.orchestrator._start_sut = _recording_start_sut
        self.executors.registered_executors = lambda: {"api": self._stub_api_factory()}

        with tempfile.TemporaryDirectory() as artifact_dir:
            previous = os.environ.get("OPAL_E2E_ARTIFACT_DIR")
            os.environ["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir
            try:
                payload = self.orchestrator.run_e2e(
                    target="source-worktree",
                    scenario_id="S-1",  # profile=api
                    task_path=str(self.task_path),
                    worktree_root=str(self.source_root),
                )
                journal = json.loads(
                    (pathlib.Path(artifact_dir) / "journal.json").read_text(encoding="utf-8")
                )
                run_json = json.loads(
                    (pathlib.Path(artifact_dir) / "run.json").read_text(encoding="utf-8")
                )
            finally:
                if previous is None:
                    os.environ.pop("OPAL_E2E_ARTIFACT_DIR", None)
                else:
                    os.environ["OPAL_E2E_ARTIFACT_DIR"] = previous
        return payload, run_json, [item["to"] for item in journal["transitions"]]

    def test_sut_starts_before_the_api_probe_runs(self):
        _payload, _run_json, _states = self._run_api_profile()
        self.assertEqual(self.events, ["start_sut", "probe"])

    def test_api_probe_receives_a_live_backend_url(self):
        """backend_url이 채워진다는 것은 health를 물어볼 대상이 실제로 있다는 뜻이다."""
        self._run_api_profile()
        self.assertTrue(self.probe_contexts)
        backend_url = self.probe_contexts[0].get("backend_url")
        self.assertIsNotNone(backend_url)
        self.assertTrue(str(backend_url).startswith("http://127.0.0.1:"), backend_url)

    def test_api_profile_emits_the_a21_order(self):
        _payload, _run_json, states = self._run_api_profile()
        order = [
            self.orchestrator.STATE_SUT_STARTING,
            self.orchestrator.STATE_SUT_READY,
            self.orchestrator.STATE_PROFILE_RESOLVED,
            self.orchestrator.STATE_EXECUTOR_READY,
        ]
        positions = [states.index(state) for state in order]
        self.assertEqual(positions, sorted(positions), f"§A.2.1 순서 위반: {states}")

    def test_selected_api_candidate_is_recorded_once(self):
        _payload, run_json, _states = self._run_api_profile()
        selected = [c for c in run_json["candidates"] if c["outcome"] == "selected"]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["type"], "api")

    def test_candidate_orders_are_contiguous_from_one(self):
        """§A.1.2 — browser 후보와 executor 후보가 이어져도 order는 1부터 연속이다."""
        _payload, run_json, _states = self._run_api_profile()
        orders = [c["order"] for c in run_json["candidates"]]
        self.assertEqual(orders, list(range(1, len(orders) + 1)))
