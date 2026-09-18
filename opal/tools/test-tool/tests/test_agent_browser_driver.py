"""
@header {
  "module": "test_agent_browser_driver",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "T07 agent-browser 공용 driver — §B.2 8연산 전수 존재·디스패치, 바이너리 해석(env override·Orca 번들 glob·PATH)과 resolution_source 기록, §A.8 probe의 실행-근거-only 판정과 미확인 capability 보수 처리, wait_kind별 fail/infra_error 분기(RK-6), semantic assertion의 expected/actual 기록(C-DRV-4), 증적 관문 경유 capture, §A.14 ambient env 차단, C-2 소유 page/profile 한정 정리(close --all 미사용), 연산별 1회 호출을 검증한다.",
  "scenarios": ["S-8", "S-9"],
  "exports": [
    "TestBinaryResolution", "TestVersionDetection", "TestProbeContract",
    "TestAmbientEnvIsolation", "TestStandaloneConfig", "TestOwnershipScopedCleanup",
    "TestEightOperationCompleteness", "TestActContract", "TestWaitKindSemantics",
    "TestAssertContract", "TestCaptureContract", "TestFullPathSingleInvocation",
    "TestActionResultEnum", "TestRegistryRegistration"
  ]
}

[MUST] 이 스위트의 `subprocess` 대역(스텁 바이너리)은 **계약 형태 검증 전용**이며
AC-4·AC-5의 실행 증거로 인정하지 않는다(PM 확정 H-2). 실제 브라우저를 기동해 얻는
증거는 `probe.json`·`run.json`의 실행 산출물이 소유한다. 여기서 고정하는 것은 "driver가
계약대로 판정·기록·정리하는가"뿐이다.

스텁은 실제 `agent-browser`의 관측된 표면만 흉내낸다 — `--version`은 `agent-browser
<semver>`를 내고, `session list`는 활성 세션이 없을 때 `No active sessions`를 낸다.
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

from lib.e2e import drivers as e2e_drivers  # noqa: E402
from lib.e2e import evidence as e2e_evidence  # noqa: E402
from lib.e2e import executors as e2e_executors  # noqa: E402
from lib.e2e.drivers import agent_browser as ab  # noqa: E402


def _write_stub(path: pathlib.Path, body: str) -> pathlib.Path:
    path.write_text("#!/bin/bash\n" + body)
    path.chmod(0o755)
    return path


# 활성 세션 0건 — 이 머신의 실측 응답과 같은 모양이다.
_STUB_NO_SESSION = """
case "$*" in
  *--version*) echo "agent-browser 0.27.0"; exit 0;;
  *"session list"*) echo "No active sessions"; exit 0;;
  *) exit 0;;
esac
"""

# 활성 세션이 있는 managed runtime.
_STUB_ACTIVE_SESSION = """
case "$*" in
  *--version*) echo "agent-browser 0.27.0"; exit 0;;
  *"session list"*) echo "opal-e2e-run  (active)"; exit 0;;
  *) exit 0;;
esac
"""

# `--config` 경로를 거부하는 바이너리 — 실측상 없거나 잘못된 config는 오류 종료한다.
_STUB_CONFIG_REJECTED = """
case "$*" in
  *--version*) echo "agent-browser 0.27.0"; exit 0;;
  *) echo "invalid config" >&2; exit 1;;
esac
"""


class _StubEnvCase(unittest.TestCase):
    """스텁 바이너리 1개를 env override로 꽂아 쓰는 공통 케이스."""

    stub_body = _STUB_NO_SESSION

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.bin = _write_stub(self.tmp / "agent-browser", self.stub_body)
        self.env = {ab.ENV_BINARY_OVERRIDE: str(self.bin), "PATH": os.environ.get("PATH", "")}

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def driver(self, session_mode, **context):
        return ab.AgentBrowserDriver(
            session_mode=session_mode, runtime_context=context, environ=self.env
        )


class TestBinaryResolution(_StubEnvCase):
    """T07 — 바이너리 경로를 하드코딩하지 않고 해석하며 출처를 기록한다."""

    def test_env_override_wins_and_is_labelled(self):
        for mode in (ab.SESSION_MODE_ORCA_MANAGED, ab.SESSION_MODE_STANDALONE):
            with self.subTest(mode=mode):
                path, source = ab.resolve_binary(mode, environ=self.env)
                self.assertEqual(path, str(self.bin))
                self.assertEqual(source, ab.RESOLUTION_ENV_OVERRIDE)

    def test_unusable_override_does_not_silently_fall_back(self):
        """지정한 바이너리를 못 쓰면 다른 바이너리로 조용히 대체하지 않는다."""
        env = {ab.ENV_BINARY_OVERRIDE: str(self.tmp / "absent"), "PATH": os.environ.get("PATH", "")}
        self.assertEqual(ab.resolve_binary(ab.SESSION_MODE_ORCA_MANAGED, environ=env), (None, None))

    def test_orca_bundle_is_found_by_glob_not_by_a_fixed_filename(self):
        """번들 바이너리는 플랫폼 접미사를 갖는다 — 이름을 고정하지 않고 glob으로 찾는다."""
        resources = self.tmp / "Resources"
        resources.mkdir()
        _write_stub(resources / "agent-browser-darwin-arm64", self.stub_body)
        env = {ab.ENV_ORCA_RESOURCES: str(resources), "PATH": ""}
        path, source = ab.resolve_binary(ab.SESSION_MODE_ORCA_MANAGED, environ=env)
        self.assertEqual(path, str(resources / "agent-browser-darwin-arm64"))
        self.assertEqual(source, ab.RESOLUTION_ORCA_BUNDLE)

    def test_bundle_glob_ignores_non_binary_siblings(self):
        resources = self.tmp / "Resources"
        resources.mkdir()
        (resources / "agent-browser.json").write_text("{}")
        _write_stub(resources / "agent-browser-linux-x64", self.stub_body)
        env = {ab.ENV_ORCA_RESOURCES: str(resources), "PATH": ""}
        path, _ = ab.resolve_binary(ab.SESSION_MODE_ORCA_MANAGED, environ=env)
        self.assertEqual(path, str(resources / "agent-browser-linux-x64"))

    def test_standalone_resolves_from_path_only(self):
        """standalone은 Orca 번들로 되돌아가지 않는다 — 되돌아가면 '전환됐다'는 관측이 거짓이 된다."""
        resources = self.tmp / "Resources"
        resources.mkdir()
        _write_stub(resources / "agent-browser-darwin-arm64", self.stub_body)
        env = {ab.ENV_ORCA_RESOURCES: str(resources), "PATH": ""}
        self.assertEqual(ab.resolve_binary(ab.SESSION_MODE_STANDALONE, environ=env), (None, None))

        bindir = self.tmp / "bin"
        bindir.mkdir()
        _write_stub(bindir / "agent-browser", self.stub_body)
        path, source = ab.resolve_binary(ab.SESSION_MODE_STANDALONE, environ={"PATH": str(bindir)})
        self.assertEqual(path, str(bindir / "agent-browser"))
        self.assertEqual(source, ab.RESOLUTION_PATH)

    def test_invalid_session_mode_is_rejected(self):
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            ab.AgentBrowserDriver(session_mode="owned-surface", environ=self.env)
        self.assertEqual(ctx.exception.detail_code, "driver_session_mode_invalid")


class TestVersionDetection(_StubEnvCase):
    """§A.15 — 버전은 manifest 게이트용 metadata일 뿐 가용성 근거가 아니다."""

    def test_semver_is_extracted_from_version_output(self):
        self.assertEqual(ab.detect_version(str(self.bin)), "0.27.0")

    def test_version_alone_never_makes_a_driver_available(self):
        """C-DRV-2 — 버전이 읽혀도 probe가 unavailable이면 unavailable이다."""
        driver = self.driver(ab.SESSION_MODE_ORCA_MANAGED, run_id="r1")
        self.assertEqual(driver.declared_version, "0.27.0")
        probe = driver.dispatch("probe", {})
        self.assertFalse(probe["available"])

    def test_unreadable_version_is_none_not_an_error(self):
        broken = _write_stub(self.tmp / "broken", "exit 3\n")
        self.assertIsNone(ab.detect_version(str(broken)))


class TestProbeContract(_StubEnvCase):
    """§A.8 — 가용성은 실행 결과로만 판정하고, 미확인 capability는 보수적으로 false다."""

    def test_orca_managed_without_active_session_is_provider_unavailable(self):
        driver = self.driver(ab.SESSION_MODE_ORCA_MANAGED, run_id="r1")
        probe = driver.dispatch("probe", {})
        self.assertFalse(probe["available"])
        self.assertEqual(probe["unavailable_reason"], "orca_runtime_no_active_session")

    def test_missing_binary_is_provider_unavailable_not_an_exception(self):
        """'실행 수단이 없음'은 provider_unavailable이며 infra_error가 아니다(C-3·TD-13)."""
        env = {ab.ENV_BINARY_OVERRIDE: str(self.tmp / "absent"), "PATH": ""}
        driver = ab.AgentBrowserDriver(session_mode=ab.SESSION_MODE_STANDALONE, environ=env)
        self.assertIsNone(driver.binary_path)
        probe = driver.dispatch("probe", {})
        self.assertFalse(probe["available"])
        self.assertEqual(probe["unavailable_reason"], "agent_browser_binary_not_found")

    def test_every_capability_stays_unprobed_and_unavailable(self):
        """[MUST] help 문자열·번들 파일 존재로 capability를 승격하지 않는다(§A.8)."""
        driver = self.driver(ab.SESSION_MODE_ORCA_MANAGED, run_id="r1")
        raw = driver.dispatch("probe", {})
        normalized = e2e_drivers.normalize_probe_result(
            raw, driver=ab.DRIVER_NAME, session_mode=ab.SESSION_MODE_ORCA_MANAGED
        )
        self.assertEqual(sorted(normalized["capabilities"]), sorted(e2e_drivers.CAPABILITY_KEYS))
        for key, item in normalized["capabilities"].items():
            with self.subTest(capability=key):
                self.assertFalse(item["probed"])
                self.assertFalse(item["available"])

    def test_active_managed_session_probes_available(self):
        stub = _write_stub(self.tmp / "active", _STUB_ACTIVE_SESSION)
        env = {ab.ENV_BINARY_OVERRIDE: str(stub), "PATH": ""}
        driver = ab.AgentBrowserDriver(
            session_mode=ab.SESSION_MODE_ORCA_MANAGED, runtime_context={"run_id": "r1"}, environ=env
        )
        self.assertTrue(driver.dispatch("probe", {})["available"])

    def test_standalone_config_rejection_is_provider_unavailable(self):
        stub = _write_stub(self.tmp / "reject", _STUB_CONFIG_REJECTED)
        env = {ab.ENV_BINARY_OVERRIDE: str(stub), "PATH": ""}
        driver = ab.AgentBrowserDriver(
            session_mode=ab.SESSION_MODE_STANDALONE, runtime_context={"run_id": "r1"}, environ=env
        )
        probe = driver.dispatch("probe", {})
        self.assertFalse(probe["available"])
        self.assertEqual(probe["unavailable_reason"], "agent_browser_config_rejected")

    def test_wait_without_wait_kind_is_refused_before_execution(self):
        """C-DRV-1 [MUST] — wait_kind 없이는 driver를 실행하지 않는다."""
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            driver.dispatch("wait", {"handle": "h", "condition": "x", "timeout_ms": 10})
        self.assertEqual(ctx.exception.detail_code, "driver_wait_kind_required")


class TestAmbientEnvIsolation(_StubEnvCase):
    """§A.14 [MUST] — standalone child env에서 AGENT_BROWSER_* 를 제거한 뒤 주입한다."""

    def test_standalone_strips_every_ambient_agent_browser_variable(self):
        env = {
            "AGENT_BROWSER_CONFIG": "/Users/someone/.agent-browser/config.json",
            "AGENT_BROWSER_ALLOWED_DOMAINS": "*",
            "PATH": "/usr/bin",
        }
        child = ab.child_env(ab.SESSION_MODE_STANDALONE, environ=env)
        self.assertEqual([key for key in child if key.startswith(ab.AMBIENT_ENV_PREFIX)], [])
        self.assertEqual(child["PATH"], "/usr/bin")

    def test_harness_owned_values_are_injected_after_the_strip(self):
        env = {"AGENT_BROWSER_ALLOWED_DOMAINS": "*"}
        child = ab.child_env(
            ab.SESSION_MODE_STANDALONE,
            environ=env,
            injected={"AGENT_BROWSER_ALLOWED_DOMAINS": "127.0.0.1:5173"},
        )
        self.assertEqual(child["AGENT_BROWSER_ALLOWED_DOMAINS"], "127.0.0.1:5173")

    def test_orca_managed_does_not_rewrite_the_runtime_environment(self):
        """C-2 — Orca가 소유한 runtime의 환경을 하네스가 재작성하지 않는다."""
        env = {"AGENT_BROWSER_CONFIG": "/user/owned.json"}
        child = ab.child_env(ab.SESSION_MODE_ORCA_MANAGED, environ=env)
        self.assertEqual(child["AGENT_BROWSER_CONFIG"], "/user/owned.json")


class TestStandaloneConfig(_StubEnvCase):
    """standalone explicit config — 절대경로 지정과 allowed domains 제한."""

    def test_allowed_domains_are_leased_localhost_plus_declared_origins_only(self):
        driver = self.driver(
            ab.SESSION_MODE_STANDALONE,
            run_id="r1",
            leased_urls=["http://127.0.0.1:5173", "http://127.0.0.1:8000"],
            allowed_origins=["https://auth.example.com"],
        )
        config = driver.build_config()
        self.assertEqual(
            config["allowedDomains"],
            ["http://127.0.0.1:5173", "http://127.0.0.1:8000", "https://auth.example.com"],
        )
        self.assertNotIn("*", config["allowedDomains"])

    def test_config_is_written_through_the_evidence_gate_at_an_absolute_path(self):
        """§C.2 — driver가 파일을 직접 쓰지 않고 관문을 통과시킨다. --config는 절대경로다."""
        with tempfile.TemporaryDirectory() as artifact_dir:
            writer = e2e_evidence.EvidenceWriter(artifact_dir, "e2e-20260914-001")
            driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1", leased_urls=["http://127.0.0.1:5173"])
            path = driver.write_config(writer)
            self.assertTrue(os.path.isabs(path))
            self.assertTrue(pathlib.Path(path).is_file())
            self.assertIn(pathlib.Path(artifact_dir), pathlib.Path(path).parents)
            # config는 증적이 아니므로 관측 증적 목록을 오염시키지 않는다.
            self.assertEqual(writer.observed(), [])
            self.assertIn("--config", driver._base_argv())
            self.assertIn(path, driver._base_argv())

    def test_orca_managed_does_not_pass_a_harness_config(self):
        driver = self.driver(ab.SESSION_MODE_ORCA_MANAGED, run_id="r1")
        self.assertNotIn("--config", driver._base_argv())

    def test_session_name_is_scoped_per_run(self):
        self.assertEqual(self.driver(ab.SESSION_MODE_STANDALONE, run_id="r9").session_name, "opal-e2e-r9")


class TestOwnershipScopedCleanup(_StubEnvCase):
    """TASK.md C-2 [MUST] — 소유한 page/profile만 정리하고 다른 탭은 보존한다."""

    def test_close_all_is_never_emitted_as_an_argument(self):
        """`close --all`은 모든 세션을 닫으므로 어떤 경로에서도 발행하지 않는다.

        산문이 아니라 **실제 인자 리터럴**이 없는지를 본다 — 모듈 docstring은 이 금지
        사항을 설명하느라 같은 문자열을 언급하므로, 원문 전체 검색은 근거가 되지 못한다.
        """
        source = pathlib.Path(ab.__file__).read_text(encoding="utf-8")
        for literal in ('"--all"', "'--all'"):
            with self.subTest(literal=literal):
                self.assertNotIn(literal, source)

    def test_only_opened_pages_enter_the_ownership_ledger(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        self.assertEqual(driver.owned_resources()["browser_pages"], [])
        driver.dispatch("open", {"url": "http://127.0.0.1:5173", "isolation_key": "page-a"})
        self.assertEqual(driver.owned_resources()["browser_pages"], ["page-a"])

    def test_closing_a_handle_we_did_not_open_is_refused(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        driver.dispatch("open", {"url": "http://127.0.0.1:5173", "isolation_key": "ours"})
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            driver.dispatch("close", {"handle": "someone-elses-tab"})
        self.assertEqual(ctx.exception.detail_code, "driver_close_unowned_handle")
        # 거부됐으므로 우리 대장은 그대로다.
        self.assertEqual(driver.owned_resources()["browser_pages"], ["ours"])

    def test_close_releases_the_owned_page_and_empties_the_ledger(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        driver.dispatch("open", {"url": "http://127.0.0.1:5173", "isolation_key": "ours"})
        result = driver.dispatch("close", {"handle": "ours"})
        self.assertTrue(result["closed"])
        self.assertIn("ours", result["released"])
        self.assertEqual(result["leaked"], [])
        self.assertEqual(driver.owned_resources()["browser_pages"], [])

    def test_standalone_releases_its_own_profile_but_orca_managed_does_not(self):
        """소유권 모드가 정리 범위를 가른다 — orca-managed는 세션·profile에 손대지 않는다."""
        standalone = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        standalone.dispatch("open", {"url": "http://127.0.0.1:5173", "isolation_key": "p"})
        self.assertEqual(standalone.owned_resources()["profiles"], ["opal-e2e-r1"])
        self.assertIn("opal-e2e-r1", standalone.dispatch("close", {"handle": "p"})["released"])

        managed = self.driver(ab.SESSION_MODE_ORCA_MANAGED, run_id="r1")
        managed.dispatch("open", {"url": "http://127.0.0.1:5173", "isolation_key": "p"})
        self.assertEqual(managed.owned_resources()["profiles"], [])
        self.assertEqual(managed.dispatch("close", {"handle": "p"})["released"], ["p"])

    def test_open_failure_does_not_put_anything_in_the_ledger(self):
        stub = _write_stub(self.tmp / "failopen", "exit 1\n")
        env = {ab.ENV_BINARY_OVERRIDE: str(stub), "PATH": ""}
        driver = ab.AgentBrowserDriver(
            session_mode=ab.SESSION_MODE_STANDALONE, runtime_context={"run_id": "r1"}, environ=env
        )
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            driver.dispatch("open", {"url": "http://127.0.0.1:5173", "isolation_key": "p"})
        self.assertEqual(ctx.exception.detail_code, "agent_browser_open_failed")
        self.assertEqual(driver.owned_resources()["browser_pages"], [])


class TestEightOperationCompleteness(_StubEnvCase):
    """§B.2 [MUST] — 8연산이 **전수** 존재하고 디스패치 가능해야 한다.

    이 테스트가 존재하는 이유: 앞선 판본은 `probe`·`open`·`close` 3개만 구현했고, 나머지
    5개는 기반 클래스의 `driver_operation_unimplemented`로 떨어졌다. 구현한 범위만 덮는
    테스트는 그 공백을 드러내지 못했다 — 그래서 여기서는 **계약이 정한 연산 목록**을
    출발점으로 삼고, driver가 그 전부를 실제로 소유하는지 되묻는다.
    """

    def test_every_contract_operation_has_an_implementation(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        missing = []
        for operation in e2e_drivers.DRIVER_OPERATIONS:
            attribute = "op_assert" if operation == "assert" else f"op_{operation}"
            implementation = getattr(type(driver), attribute, None)
            base = getattr(e2e_drivers.BrowserDriver, attribute, None)
            if implementation is None or implementation is base:
                missing.append(operation)
        self.assertEqual(
            missing, [],
            f"§B.2 requires all 8 operations; {missing} fall through to the unimplemented base",
        )

    def test_no_operation_reports_itself_unimplemented_when_dispatched(self):
        """디스패치했을 때 `driver_operation_unimplemented`가 나오는 연산이 없어야 한다.

        각 연산은 자기 필수 인자를 요구하거나 실제로 실행한다 — 어느 쪽이든 '연산 자체가
        없다'와는 다른 결과다. 그 구분이 무너지면 orchestrator가 `blocked`로 떨어뜨린다.
        """
        payloads = {
            "probe": {},
            "open": {"url": "http://127.0.0.1:5173"},
            "snapshot": {"label": "after"},
            "act": {"action": {"kind": "reload"}},
            "wait": {"wait_kind": "assertion_condition", "condition": {"ms": 1}},
            "assert": {"assertion": {"id": "a1", "verifier": "url", "expected": ""}},
            "capture": {"evidence_spec": []},
            "close": {},
        }
        for operation in e2e_drivers.DRIVER_OPERATIONS:
            with self.subTest(operation=operation):
                driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
                try:
                    driver.dispatch(operation, payloads[operation])
                except e2e_drivers.DriverError as exc:
                    self.assertNotIn(
                        exc.detail_code,
                        ("driver_operation_unimplemented", "driver_unknown_operation"),
                        f"{operation} is not implemented by this driver",
                    )


class TestActContract(_StubEnvCase):
    """§B.2 `act` — 알려진 행동만 실행하고 모르는 것은 대체하지 않는다."""

    def test_known_action_kinds_map_to_subcommands(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        result = driver.dispatch("act", {"step_id": "s1", "action": {"kind": "click", "target": "#go"}})
        self.assertTrue(result["ok"])

    def test_unknown_action_kind_is_refused_rather_than_substituted(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            driver.dispatch("act", {"action": {"kind": "teleport", "target": "#x"}})
        self.assertEqual(ctx.exception.detail_code, "agent_browser_unsupported_action")

    def test_act_without_an_action_object_is_refused(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            driver.dispatch("act", {"action": "click"})
        self.assertEqual(ctx.exception.detail_code, "driver_act_action_required")

    def test_action_without_a_kind_is_recorded_not_escalated(self):
        """번역되지 않은 step은 `infra_error`가 아니라 **수행 안 함**으로 남는다.

        `scenario_adapter.build_execution_plan`은 아직 API 형태 키만 action으로 옮기므로
        browser step의 action에는 `kind`가 없다. 이를 예외로 올리면 어댑터의 번역 공백이
        "driver가 깨졌다"로 기록돼 원인이 사라진다. 실행하지 않았다는 사실을 남기고
        `ok=false`로 돌려주는 것이 그 공백을 증적에 보이게 하는 형태다.
        """
        log = e2e_executors.ActionLog()
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1", action_log=log)
        result = driver.dispatch("act", {"step_id": "st-1", "action": {"step_role": "verify"}})
        self.assertFalse(result["ok"])
        self.assertEqual(result["action_result"]["error_code"], "agent_browser_action_kind_absent")
        self.assertEqual(log.rows()[-1]["result"], "error")

    def test_act_failure_raises_rather_than_reporting_ok(self):
        stub = _write_stub(self.tmp / "failact", "exit 1\n")
        env = {ab.ENV_BINARY_OVERRIDE: str(stub), "PATH": ""}
        driver = ab.AgentBrowserDriver(
            session_mode=ab.SESSION_MODE_STANDALONE, runtime_context={"run_id": "r1"}, environ=env
        )
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            driver.dispatch("act", {"action": {"kind": "click", "target": "#go"}})
        self.assertEqual(ctx.exception.detail_code, "agent_browser_act_failed")


class TestWaitKindSemantics(_StubEnvCase):
    """RK-6 / CONTRACT.md:231 — timeout의 의미는 wait_kind가 가른다."""

    def setUp(self):
        super().setUp()
        self.timeout_bin = _write_stub(self.tmp / "timeout", "exit 1\n")
        self.timeout_env = {ab.ENV_BINARY_OVERRIDE: str(self.timeout_bin), "PATH": ""}

    def _timeout_driver(self):
        return ab.AgentBrowserDriver(
            session_mode=ab.SESSION_MODE_STANDALONE,
            runtime_context={"run_id": "r1"},
            environ=self.timeout_env,
        )

    def test_assertion_condition_timeout_is_a_product_failure_not_an_error(self):
        """제품 조건 미충족은 `satisfied=false`로 정상 반환된다 — 호출자가 fail로 판정한다."""
        result = self._timeout_driver().dispatch(
            "wait", {"wait_kind": "assertion_condition", "condition": {"selector": "#done"}}
        )
        self.assertFalse(result["satisfied"])
        self.assertEqual(result["wait_kind"], "assertion_condition")

    def test_infrastructure_waits_escalate_to_driver_error(self):
        """`navigation_ready`·`transport` timeout을 fail로 내리면 인프라 문제가 제품 실패로 위장된다."""
        for wait_kind in ("navigation_ready", "transport"):
            with self.subTest(wait_kind=wait_kind):
                with self.assertRaises(e2e_drivers.DriverError) as ctx:
                    self._timeout_driver().dispatch(
                        "wait", {"wait_kind": wait_kind, "condition": {"selector": "#x"}}
                    )
                self.assertEqual(ctx.exception.detail_code, "agent_browser_wait_failed")

    def test_satisfied_wait_returns_its_wait_kind(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        result = driver.dispatch(
            "wait", {"wait_kind": "navigation_ready", "condition": {"selector": "#ok"}}
        )
        self.assertTrue(result["satisfied"])


class TestAssertContract(_StubEnvCase):
    """§B.2 `assert` + C-DRV-4 — 실제로 읽어 온 값으로만 판정한다."""

    stub_body = """
case "$*" in
  *--version*) echo "agent-browser 0.27.0"; exit 0;;
  *"session list"*) echo "No active sessions"; exit 0;;
  *"get text"*) echo "Welcome back"; exit 0;;
  *"get url"*) echo "http://127.0.0.1:5173/home"; exit 0;;
  *) exit 0;;
esac
"""

    def test_matching_value_passes_and_is_recorded(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        record = driver.dispatch(
            "assert",
            {"assertion": {"id": "a1", "verifier": "dom_text", "target": "#hi", "expected": "Welcome back"}},
        )
        self.assertTrue(record["passed"])
        self.assertEqual(record["actual"], "Welcome back")
        self.assertEqual(driver.assertion_results(), [record])

    def test_mismatching_value_fails_with_both_expected_and_actual(self):
        """§A.5 — expected와 actual이 함께 남아야 무엇이 어긋났는지가 기록에서 읽힌다."""
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        record = driver.dispatch(
            "assert",
            {"assertion": {"id": "a1", "verifier": "dom_text", "target": "#hi", "expected": "Goodbye"}},
        )
        self.assertFalse(record["passed"])
        self.assertEqual(record["expected"], "Goodbye")
        self.assertEqual(record["actual"], "Welcome back")

    def test_contains_matcher_is_honoured(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        record = driver.dispatch(
            "assert",
            {"assertion": {"id": "a1", "verifier": "url", "expected": "/home", "match": "contains"}},
        )
        self.assertTrue(record["passed"])

    def test_assertion_without_an_id_is_refused(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            driver.dispatch("assert", {"assertion": {"verifier": "url", "expected": "x"}})
        self.assertEqual(ctx.exception.detail_code, "driver_assert_id_required")

    def test_assertion_without_a_verifier_cannot_pass(self):
        """검증 수단이 명시되지 않은 단언은 통과할 수 없다(§9.2 · C-DRV-4).

        예외로 올려 `infra_error`를 만들면 제품 판정이 인프라 오류로 위장된다. 관측
        근거가 없다는 사실을 실패한 단언으로 남겨 run이 `fail`로 끝나게 한다.
        """
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        record = driver.dispatch("assert", {"assertion": {"id": "a1", "expected": "ok"}})
        self.assertFalse(record["passed"])
        self.assertIsNone(record["actual"])
        self.assertEqual(record["reason"], "assertion_verifier_unspecified")
        self.assertEqual(driver.assertion_results(), [record])

    def test_unknown_verifier_and_matcher_are_refused(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            driver.dispatch("assert", {"assertion": {"id": "a", "verifier": "vibes", "expected": "x"}})
        self.assertEqual(ctx.exception.detail_code, "agent_browser_unsupported_verifier")
        with self.assertRaises(e2e_drivers.DriverError) as ctx:
            driver.dispatch(
                "assert",
                {"assertion": {"id": "a", "verifier": "url", "expected": "x", "match": "roughly"}},
            )
        self.assertEqual(ctx.exception.detail_code, "agent_browser_unsupported_matcher")

    def test_open_and_act_alone_leave_assertion_results_empty(self):
        """C-DRV-4 — 화면을 열고 조작한 사실만으로는 pass 근거가 생기지 않는다."""
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        driver.dispatch("open", {"url": "http://127.0.0.1:5173"})
        driver.dispatch("act", {"action": {"kind": "click", "target": "#go"}})
        self.assertEqual(driver.assertion_results(), [])


class TestCaptureContract(_StubEnvCase):
    """§B.2 `capture` + §C.2 — 증적은 관문을 통과하고, 없는 수단은 보고하지 않는다."""

    stub_body = """
case "$*" in
  *--version*) echo "agent-browser 0.27.0"; exit 0;;
  *"session list"*) echo "No active sessions"; exit 0;;
  *snapshot*) echo "- button \\"Save\\" [ref=e1]"; exit 0;;
  *console*) echo '{"level":"log","text":"hello"}'; exit 0;;
  *errors*) echo '{"message":"boom"}'; exit 0;;
  *) exit 0;;
esac
"""

    def _writer(self, artifact_dir):
        return e2e_evidence.EvidenceWriter(artifact_dir, "e2e-20260915-001")

    def test_capture_without_a_writer_writes_nothing_and_says_so(self):
        """쓰지 않은 것을 썼다고 보고하지 않는다."""
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        result = driver.dispatch("capture", {"evidence_spec": ["snapshot"]})
        self.assertEqual(result["artifacts"], {})
        self.assertEqual(result["unsupported"], ["snapshot"])

    def test_snapshot_is_written_through_the_gate_at_the_mapped_path(self):
        with tempfile.TemporaryDirectory() as artifact_dir:
            writer = self._writer(artifact_dir)
            driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1", writer=writer)
            result = driver.dispatch("snapshot", {"label": "before"})
            self.assertTrue(result["artifact_path"].endswith(ab.SNAPSHOT_ARTIFACTS["before"]))
            self.assertTrue(pathlib.Path(result["artifact_path"]).is_file())
            self.assertIn("snapshot", driver.observed_evidence())

    def test_unavailable_capability_is_reported_not_written_as_an_empty_file(self):
        """[MUST] 없는 수단으로 만든 빈 증적을 남기지 않는다 — 결손이 판정에 도달해야 한다(S-5)."""
        stub = _write_stub(self.tmp / "nocaps", "exit 1\n")
        env = {ab.ENV_BINARY_OVERRIDE: str(stub), "PATH": ""}
        with tempfile.TemporaryDirectory() as artifact_dir:
            writer = self._writer(artifact_dir)
            driver = ab.AgentBrowserDriver(
                session_mode=ab.SESSION_MODE_STANDALONE,
                runtime_context={"run_id": "r1", "writer": writer},
                environ=env,
            )
            result = driver.dispatch("capture", {"evidence_spec": ["console", "errors"]})
            self.assertEqual(result["artifacts"], {})
            self.assertCountEqual(result["unsupported"], ["console", "errors"])
            self.assertFalse((pathlib.Path(artifact_dir) / ab.CONSOLE_ARTIFACT).exists())

    def test_capture_executes_each_capability_once_and_records_what_it_measured(self):
        """capability의 **유일한** 실행 지점이 capture다 — 판정과 수집을 한 번에 한다.

        probe에서 한 번 더 부르면 동결 RED S-27 (d-1)이 같은 연산 2회를 retry로 잡는다.
        """
        with tempfile.TemporaryDirectory() as artifact_dir:
            writer = self._writer(artifact_dir)
            driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1", writer=writer)
            driver.dispatch("probe", {})
            result = driver.dispatch("capture", {"evidence_spec": ["console", "errors"]})
            self.assertTrue(result["artifacts"]["console"].endswith(ab.CONSOLE_ARTIFACT))
            self.assertTrue(result["artifacts"]["errors"].endswith(ab.ERRORS_ARTIFACT))
            # 실행했으므로 probed=true로 확정된다 — "미확인"이 아니다.
            self.assertTrue(driver._capabilities["console"]["probed"])
            self.assertTrue(driver._capabilities["console"]["available"])

    def test_probe_does_not_invoke_capability_subcommands(self):
        """S-27 (d-1) — probe가 capability를 실행하면 capture와 중복돼 retry로 관측된다."""
        calls = self.tmp / "calls.log"
        stub = _write_stub(
            self.tmp / "logged",
            f'echo "$@" >> "{calls}"\n'
            'if [[ "$1" == "--version" ]]; then echo "agent-browser 0.27.0"; exit 0; fi\n'
            'if [[ "$1" == "session" ]]; then echo "No active sessions"; exit 0; fi\nexit 0\n',
        )
        env = {ab.ENV_BINARY_OVERRIDE: str(stub), "PATH": ""}
        driver = ab.AgentBrowserDriver(
            session_mode=ab.SESSION_MODE_STANDALONE, runtime_context={"run_id": "r1"}, environ=env
        )
        driver.dispatch("probe", {})
        invoked = [line.split()[0] for line in calls.read_text().splitlines() if line.strip()]
        for capability in ("console", "errors", "snapshot"):
            with self.subTest(capability=capability):
                self.assertNotIn(capability, invoked)

    def test_network_har_is_never_promoted_without_a_non_destructive_probe(self):
        """`har start`는 기록을 시작한다 — 확인하려고 부작용을 만들지 않는다."""
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        raw = driver.dispatch("probe", {})
        self.assertFalse(raw["capabilities"]["network_har"]["probed"])
        self.assertFalse(raw["capabilities"]["network_har"]["available"])

    def test_orca_managed_isolated_profile_stays_unprobed_pending_q2(self):
        """Q-2 미해소 — managed 세션에 config가 적용되는지 실행으로 확인하지 못했다."""
        stub = _write_stub(self.tmp / "active", _STUB_ACTIVE_SESSION)
        env = {ab.ENV_BINARY_OVERRIDE: str(stub), "PATH": ""}
        driver = ab.AgentBrowserDriver(
            session_mode=ab.SESSION_MODE_ORCA_MANAGED, runtime_context={"run_id": "r1"}, environ=env
        )
        caps = driver.dispatch("probe", {})["capabilities"]
        self.assertFalse(caps["isolated_profile"]["probed"])
        self.assertFalse(caps["isolated_profile"]["available"])

    def test_standalone_isolated_profile_is_confirmed_by_the_accepted_config(self):
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        caps = driver.dispatch("probe", {})["capabilities"]
        self.assertTrue(caps["isolated_profile"]["probed"])
        self.assertTrue(caps["isolated_profile"]["available"])


class TestFullPathSingleInvocation(_StubEnvCase):
    """스텁 후보로 open → act → assert → capture → close 전 경로를 돌리고 중복 호출을 본다."""

    stub_body = TestAssertContract.stub_body

    def test_full_path_runs_and_each_operation_is_invoked_exactly_once(self):
        """[MUST] 같은 연산의 2회차 호출은 재시도로 관측된다(동결 RED S-27 (d-1))."""
        with tempfile.TemporaryDirectory() as artifact_dir:
            writer = e2e_evidence.EvidenceWriter(artifact_dir, "e2e-20260915-002")
            log = e2e_executors.ActionLog()
            driver = self.driver(
                ab.SESSION_MODE_STANDALONE, run_id="r1", writer=writer, action_log=log
            )

            session = driver.dispatch("open", {"url": "http://127.0.0.1:5173"})
            page_id = session["page_id"]
            driver.dispatch("act", {"page_id": page_id, "step_id": "s1", "action": {"kind": "click", "target": "#go"}})
            record = driver.dispatch(
                "assert",
                {"page_id": page_id,
                 "assertion": {"id": "a1", "verifier": "dom_text", "target": "#hi", "expected": "Welcome back"}},
            )
            capture = driver.dispatch("capture", {"page_id": page_id, "evidence_spec": []})
            closed = driver.dispatch("close", {"page_id": page_id})

            self.assertTrue(record["passed"])
            self.assertTrue(closed["closed"])
            self.assertEqual(driver.owned_resources()["browser_pages"], [])

            # §A.4 actions.jsonl이 실제로 관문을 통과했다 — browser 전용 run에서는 이
            # driver가 유일한 발행자다.
            self.assertIn("action_log", capture["artifacts"])
            self.assertIn("action_log", driver.observed_evidence())
            self.assertTrue(pathlib.Path(capture["artifacts"]["action_log"]).is_file())

            for operation, count in driver.operation_calls().items():
                with self.subTest(operation=operation):
                    self.assertEqual(count, 1, f"{operation} was invoked {count} times (retry observed)")

    def test_open_returns_both_contract_and_orchestrator_identifiers(self):
        """§B.2는 `handle`, orchestrator browser 경로는 `page_id`로 부른다 — 둘 다 싣는다."""
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1")
        session = driver.dispatch("open", {"url": "http://127.0.0.1:5173"})
        self.assertEqual(session["handle"], session["page_id"])
        # orchestrator가 page_id로 닫아도 소유 대장이 비워져야 한다.
        driver.dispatch("close", {"page_id": session["page_id"]})
        self.assertEqual(driver.owned_resources()["browser_pages"], [])


class TestActionResultEnum(_StubEnvCase):
    """§A.4 [MUST] — `actions.jsonl`의 `result`는 `ok`|`error` 둘뿐이다.

    이 스위트가 존재하는 이유: 앞선 판본이 `"timeout"`·`"fail"`을 실어 `ActionLog.record`가
    `action_result_invalid`로 거부했고, **실패한 assertion 하나가 run 전체를
    `infra_error`로 만들며 `assertions.json`까지 빈 채로 끝냈다.** 제품 실패가 인프라
    오류로 위장되는 경로였다.

    되묻는 출발점은 이 driver의 코드가 아니라 **계약이 소유한 `ACTION_RESULTS`**다 —
    enum이 바뀌면 이 테스트가 같이 움직이고, driver가 벗어나면 즉시 잡힌다.
    """

    stub_body = TestAssertContract.stub_body

    def _rows_for(self, run):
        log = e2e_executors.ActionLog()
        driver = self.driver(ab.SESSION_MODE_STANDALONE, run_id="r1", action_log=log)
        run(driver)
        return log.rows()

    def _assert_enum(self, rows):
        self.assertTrue(rows, "no action row was recorded")
        for row in rows:
            with self.subTest(action=row.get("action")):
                self.assertIn(
                    row["result"], e2e_executors.ACTION_RESULTS,
                    f"result={row['result']!r} is outside §A.4 {e2e_executors.ACTION_RESULTS}",
                )

    def test_every_operation_records_a_result_inside_the_contract_enum(self):
        """8연산을 실제로 돌려 모든 행이 enum 안인지 본다 — 세 위반 지점을 모두 지난다."""
        def exercise(driver):
            driver.dispatch("probe", {})
            session = driver.dispatch("open", {"url": "http://127.0.0.1:5173"})
            page = session["page_id"]
            driver.dispatch("snapshot", {"page_id": page, "label": "before"})
            driver.dispatch("act", {"page_id": page, "step_id": "s1", "action": {"kind": "click", "target": "#go"}})
            driver.dispatch("wait", {"page_id": page, "wait_kind": "assertion_condition", "condition": {"ms": 1}})
            # 통과하는 단언과 실패하는 단언을 모두 지난다.
            driver.dispatch("assert", {"page_id": page, "assertion": {
                "id": "pass", "verifier": "dom_text", "target": "#hi", "expected": "Welcome back"}})
            driver.dispatch("assert", {"page_id": page, "assertion": {
                "id": "fail", "verifier": "dom_text", "target": "#hi", "expected": "Goodbye"}})
            driver.dispatch("close", {"page_id": page})

        self._assert_enum(self._rows_for(exercise))

    def test_a_failing_assertion_is_a_successful_operation(self):
        """판정 결과를 `result`에 겹쳐 쓰지 않는다 — 그러면 제품 실패가 연산 실패로 읽힌다."""
        rows = self._rows_for(lambda d: d.dispatch("assert", {"assertion": {
            "id": "a1", "verifier": "dom_text", "target": "#hi", "expected": "Goodbye"}}))
        row = rows[-1]
        self.assertEqual(row["action"], "assert")
        self.assertEqual(row["result"], "ok", "the get/compare operation completed normally")
        self.assertIsNone(row["error_code"])

    def test_an_unevaluatable_assertion_is_an_operation_error(self):
        """verifier가 없으면 읽을 대상을 모른다 — 관측 자체가 없었으므로 `error`다."""
        rows = self._rows_for(lambda d: d.dispatch("assert", {"assertion": {"id": "a1", "expected": "ok"}}))
        row = rows[-1]
        self.assertEqual(row["result"], "error")
        self.assertEqual(row["error_code"], "assertion_verifier_unspecified")

    def test_wait_timeout_is_an_error_row_classified_by_wait_kind(self):
        """RK-6 — fail/infra_error를 가르는 것은 `result`가 아니라 `wait_kind`다.

        `e2e_contract.py:229-231`이 error=`wait_failed`인 행을 받아 `wait_kind`로 가르므로,
        timeout은 error 행으로 남고 분류 정보는 `wait_kind`가 싣는다.
        """
        timeout_bin = _write_stub(self.tmp / "timeout", "exit 1\n")
        env = {ab.ENV_BINARY_OVERRIDE: str(timeout_bin), "PATH": ""}
        log = e2e_executors.ActionLog()
        driver = ab.AgentBrowserDriver(
            session_mode=ab.SESSION_MODE_STANDALONE,
            runtime_context={"run_id": "r1", "action_log": log},
            environ=env,
        )
        driver.dispatch("wait", {"wait_kind": "assertion_condition", "condition": {"selector": "#x"}})
        row = log.rows()[-1]
        self.assertEqual(row["result"], "error")
        self.assertEqual(row["error_code"], "wait_failed")
        self.assertEqual(row["wait_kind"], "assertion_condition")

    def test_satisfied_wait_records_ok_with_no_error_code(self):
        rows = self._rows_for(
            lambda d: d.dispatch("wait", {"wait_kind": "navigation_ready", "condition": {"ms": 1}})
        )
        row = rows[-1]
        self.assertEqual(row["result"], "ok")
        self.assertIsNone(row["error_code"])

    def test_action_log_accepts_every_row_this_driver_produces(self):
        """`ActionLog.record`가 거부하면 run이 `infra_error`가 된다 — 거부가 없어야 한다.

        위 테스트들이 이미 `record()`를 통과시켜 행을 쌓았다는 사실 자체가 검증이지만,
        여기서는 그 계약을 명시적으로 되묻는다.
        """
        def exercise(driver):
            driver.dispatch("act", {"step_id": "s1", "action": {"kind": "reload"}})
            driver.dispatch("assert", {"assertion": {
                "id": "a1", "verifier": "url", "expected": "nope"}})

        rows = self._rows_for(exercise)  # record()가 거부하면 ExecutorError로 여기서 터진다
        self.assertEqual(len(rows), 2)
        self._assert_enum(rows)


class TestRegistryRegistration(unittest.TestCase):
    """TD-11 — 두 모드가 **같은 adapter 클래스**로 등록된다(별도 driver가 아니다)."""

    def test_both_session_modes_register_the_same_adapter(self):
        registry = e2e_drivers.registered_drivers()
        for mode in (ab.SESSION_MODE_ORCA_MANAGED, ab.SESSION_MODE_STANDALONE):
            with self.subTest(mode=mode):
                factory = registry.get((ab.DRIVER_NAME, mode))
                self.assertIsNotNone(factory, f"{mode} must be registered")
                built = factory(runtime_context={"run_id": "r1"})
                self.assertIsInstance(built, ab.AgentBrowserDriver)
                self.assertEqual(built.session_mode, mode)

    def test_manifest_minimum_version_matches_the_measured_bundle_version(self):
        """§A.15 — 버전 SSOT는 manifest 한 곳이며 값은 실측치다(실측: agent-browser 0.27.0)."""
        policy = e2e_drivers.load_manifest()["drivers"][ab.DRIVER_NAME]
        self.assertTrue(e2e_drivers.meets_minimum_version("0.27.0", policy["minimum_version"]))
        self.assertTrue(e2e_drivers.in_tested_range("0.27.0", policy["tested_range"]))


if __name__ == "__main__":
    unittest.main()
