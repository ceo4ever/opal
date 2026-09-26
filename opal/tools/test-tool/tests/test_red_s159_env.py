"""
@header {
  "module": "test_red_s159_env",
  "task": "159-260926-opds-E2E-테스트환경-설정체계",
  "layer": "test",
  "domain": "opal-tools",
  "description": "S-1~S-7: PLAN.md D-1~D-11의 `.opal/e2e/environment.json` 설정 체계(env-validate/env-inspect/env-check 신규 명령, run의 설정 기반 SUT 기동/blocked 코드)를 공개 인터페이스(CLI subprocess stdout JSON·exit, orchestrator.run_e2e 공개 진입점, 파일 트리 해시, grep)로 검증하는 구현 전 RED 스위트. 구현 워커는 이 파일의 기대 계약을 약화하지 않는다.",
  "scenarios": ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7"],
  "exports": [
    "TestEnvValidate", "TestEnvInspect", "TestEnvCheckReady",
    "TestEnvCheckServiceFailure", "TestNoDashboardStringLeft",
    "TestRunEnvironmentBlocked", "TestRunSurfaceSelection"
  ]
}

작성자: opal-test-agent (red mode). 이 파일은 TEST-SCENARIO.md S-1~S-7("구현 전 RED")의
기대 계약을 실행 가능한 pytest 코드로 옮긴 것이며, 구현(W-1~W-6)이 끝나기 전에는 실패한다.
공개 인터페이스만 쓴다: CLI는 `sys.executable test_tool.py e2e <cmd>`를 subprocess로 호출해
stdout JSON·exit code만 본다. S-7의 browser 후보 게이트만 `lib.e2e.drivers.register_driver`로
최소 stub driver를 등록해 통과시키고(기존 test_e2e_drivers.py 패턴), 판정 경로 자체는
`lib.e2e.orchestrator.run_e2e` 공개 진입점을 그대로 호출한다. private 함수는 import하지 않는다.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_PYTHON = sys.executable

sys.path.insert(0, str(_TOOL_DIR))

from lib.e2e import drivers as e2e_drivers  # noqa: E402
from lib.e2e import orchestrator as e2e_orchestrator  # noqa: E402
from lib.e2e import target as e2e_target  # noqa: E402


def _run_cli(args, cwd=None):
    """`test_tool.py`를 subprocess로 실행하고 (exit_code, stdout_text, parsed_json_or_None)를 낸다."""
    proc = subprocess.run(
        [_PYTHON, str(_TEST_TOOL_PY), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        parsed = None
    return proc.returncode, proc.stdout, proc.stderr, parsed


def _write_config(project_root: pathlib.Path, config: dict) -> pathlib.Path:
    e2e_dir = project_root / ".opal" / "e2e"
    e2e_dir.mkdir(parents=True, exist_ok=True)
    path = e2e_dir / "environment.json"
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _tree_snapshot(root: pathlib.Path):
    """파일 경로·크기·mtime·sha256 목록 — env-inspect가 쓰기 없이 끝나는지 대조."""
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            out.append((str(p.relative_to(root)), p.stat().st_size, p.stat().st_mtime, digest))
    return out


_VALID_ALL_SURFACES_CONFIG = {
    "schema_version": "1.0",
    "services": [
        {
            "id": "backend",
            "command": [_PYTHON, "-c", "import time; time.sleep(60)"],
        }
    ],
    "surfaces": [
        {"id": "web1", "kind": "web", "service": "backend", "path": "/"},
        {"id": "api1", "kind": "api", "service": "backend", "health_path": "/health"},
        {"id": "mac1", "kind": "macos-app", "app": {"path": "/System/Applications/Calculator.app"}},
        {"id": "win1", "kind": "windows-app", "app": {"launch": ["true"]}},
        {"id": "lin1", "kind": "linux-app", "app": {"launch": ["true"]}},
        {"id": "human1", "kind": "human"},
    ],
}


class TestEnvValidate(unittest.TestCase):
    """S-1 — `env-validate` 구조화 오류 계약(PLAN D-6)."""

    def test_a_valid_config_reports_six_surfaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_config(root, _VALID_ALL_SURFACES_CONFIG)
            code, out, err, parsed = _run_cli(["e2e", "env-validate", "--project-root", str(root)])
            self.assertEqual(code, 0, f"stdout={out!r} stderr={err!r}")
            self.assertIsNotNone(parsed, f"stdout이 JSON이 아님: {out!r} stderr={err!r}")
            self.assertTrue(parsed.get("ok"))
            self.assertEqual(parsed.get("summary", {}).get("surfaces"), 6)

    def test_b_missing_service_command_is_required_field_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            config = {
                "schema_version": "1.0",
                "services": [{"id": "backend"}],
                "surfaces": [{"id": "api1", "kind": "api", "service": "backend"}],
            }
            _write_config(root, config)
            code, out, err, parsed = _run_cli(["e2e", "env-validate", "--project-root", str(root)])
            self.assertEqual(code, 1, f"stdout={out!r} stderr={err!r}")
            self.assertIsNotNone(parsed, f"stdout이 JSON이 아님: {out!r} stderr={err!r}")
            self.assertEqual(parsed.get("error"), "e2e_env_config_invalid")
            violations = parsed.get("violations", [])
            self.assertTrue(
                any(
                    v.get("code") == "required_field_missing" and v.get("path") == "services[0].command"
                    for v in violations
                ),
                f"violations={violations!r}",
            )

    def test_c_secret_literal_value_is_rejected_and_not_echoed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            secret_value = "sk-literal-159-should-not-leak"
            config = {
                "schema_version": "1.0",
                "services": [],
                "surfaces": [],
                "secrets": [{"name": "S159_TOKEN", "purpose": "x", "value": secret_value}],
            }
            _write_config(root, config)
            code, out, err, parsed = _run_cli(["e2e", "env-validate", "--project-root", str(root)])
            self.assertEqual(code, 1, f"stdout={out!r} stderr={err!r}")
            self.assertIsNotNone(parsed, f"stdout이 JSON이 아님: {out!r} stderr={err!r}")
            violations = parsed.get("violations", [])
            self.assertTrue(any(v.get("code") == "secret_literal" for v in violations), f"{violations!r}")
            self.assertNotIn(secret_value, out)

    def test_d_password_env_literal_is_rejected_and_not_echoed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            secret_value = "pw-literal-159-should-not-leak"
            config = {
                "schema_version": "1.0",
                "services": [
                    {"id": "backend", "command": ["true"], "env": {"DB_PASSWORD": secret_value}}
                ],
                "surfaces": [],
            }
            _write_config(root, config)
            code, out, err, parsed = _run_cli(["e2e", "env-validate", "--project-root", str(root)])
            self.assertEqual(code, 1, f"stdout={out!r} stderr={err!r}")
            self.assertIsNotNone(parsed, f"stdout이 JSON이 아님: {out!r} stderr={err!r}")
            violations = parsed.get("violations", [])
            self.assertTrue(any(v.get("code") == "secret_literal" for v in violations), f"{violations!r}")
            self.assertNotIn(secret_value, out)

    def test_e_missing_file_is_config_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            code, out, err, parsed = _run_cli(["e2e", "env-validate", "--project-root", str(root)])
            self.assertEqual(code, 1, f"stdout={out!r} stderr={err!r}")
            self.assertIsNotNone(parsed, f"stdout이 JSON이 아님: {out!r} stderr={err!r}")
            self.assertEqual(parsed.get("error"), "e2e_env_config_missing")


class TestEnvInspect(unittest.TestCase):
    """S-2 — `env-inspect` 읽기 전용 검토(PLAN D-7)."""

    def test_inspect_reports_candidates_without_writing_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "name": "sample",
                        "scripts": {"dev": "vite"},
                        "dependencies": {"vite": "^5.0.0"},
                    }
                ),
                encoding="utf-8",
            )
            (root / "server.py").write_text(
                "# GET /health -> {\"status\": \"ok\"}\n"
                "from fastapi import FastAPI\napp = FastAPI()\n",
                encoding="utf-8",
            )
            (root / ".env.example").write_text("E2E_TOKEN=\n", encoding="utf-8")

            before = _tree_snapshot(root)
            code, out, err, parsed = _run_cli(["e2e", "env-inspect", "--project-root", str(root)])
            after = _tree_snapshot(root)

            self.assertEqual(code, 0, f"stdout={out!r} stderr={err!r}")
            self.assertIsNotNone(parsed, f"stdout이 JSON이 아님: {out!r} stderr={err!r}")
            self.assertFalse(parsed.get("config", {}).get("present"))

            kinds = {c.get("kind") for c in parsed.get("surface_candidates", [])}
            self.assertIn("web", kinds)
            self.assertIn("api", kinds)
            for candidate in parsed.get("surface_candidates", []):
                self.assertIn("command", candidate.get("suggested", {}))

            for driver in parsed.get("drivers", []):
                self.assertIn("installed", driver)
                self.assertIsInstance(driver["installed"], bool)

            self.assertIn("E2E_TOKEN", parsed.get("secret_hints", []))
            self.assertNotIn("=", "".join(parsed.get("secret_hints", [])))

            self.assertEqual(before, after, "env-inspect가 프로젝트 트리를 바꿈")
            self.assertFalse((root / ".opal" / "e2e" / "environment.json").exists())


def _register_stub_driver_for_gate():
    """S-7의 browser 후보 게이트만 통과시키는 최소 대역 — 판정 경로는 대역하지 않는다."""

    class _StubDriver(e2e_drivers.BrowserDriver):
        def __init__(self, **_kwargs):
            self.name = "agent-browser"
            self.binary_path = "/nonexistent/agent-browser"
            self.resolution_source = "test-stub"
            self.declared_version = "1.0.0"

        def op_probe(self, request):
            return {
                key: {"available": True, "route": "native", "probed": True}
                for key in e2e_drivers.CAPABILITY_KEYS
            }

    e2e_drivers.register_driver("agent-browser", None, _StubDriver)


class TestEnvCheckReady(unittest.TestCase):
    """S-3 — `env-check` 준비 검증(PLAN D-8): api/데스크톱/human 표면 + secrets 집계."""

    def test_env_check_surfaces_and_secrets(self):
        env_var_name = "E2E_S159_TOKEN"
        os.environ.pop(env_var_name, None)
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as artifact_root:
            root = pathlib.Path(tmp)
            server_script = root / "server.py"
            server_script.write_text(
                "import http.server, json\n"
                "class H(http.server.BaseHTTPRequestHandler):\n"
                "    def do_GET(self):\n"
                "        self.send_response(200)\n"
                "        self.send_header('Content-Type', 'application/json')\n"
                "        self.end_headers()\n"
                "        self.wfile.write(json.dumps({'status': 'ok'}).encode())\n"
                "http.server.HTTPServer(('127.0.0.1', 0), H)\n",
                encoding="utf-8",
            )
            config = {
                "schema_version": "1.0",
                "services": [{"id": "api-svc", "command": [_PYTHON, str(server_script)]}],
                "surfaces": [
                    {"id": "api1", "kind": "api", "service": "api-svc", "health_path": "/health"},
                    {"id": "mac1", "kind": "macos-app", "app": {"path": "/System/Applications/Calculator.app"}},
                    {"id": "lin1", "kind": "linux-app", "app": {"launch": ["true"]}},
                    {"id": "human1", "kind": "human"},
                ],
                "secrets": [{"name": env_var_name, "purpose": "s159 red 계약"}],
            }
            _write_config(root, config)
            code, out, err, parsed = _run_cli(
                ["e2e", "env-check", "--project-root", str(root), "--artifact-root", artifact_root]
            )
            self.assertEqual(code, 1, f"stdout={out!r} stderr={err!r}")
            self.assertIsNotNone(parsed, f"stdout이 JSON이 아님: {out!r} stderr={err!r}")
            self.assertFalse(parsed.get("ready"))

            surfaces = {s["id"]: s for s in parsed.get("surfaces", [])}

            api_surface = surfaces.get("api1", {})
            check_names = [c.get("name") for c in api_surface.get("checks", [])]
            check_oks = {c.get("name"): c.get("ok") for c in api_surface.get("checks", [])}
            self.assertTrue(check_names, "api 표면에 check 항목이 없음")
            self.assertTrue(all(check_oks.values()), f"api1 checks={api_surface.get('checks')!r}")

            mac_surface = surfaces.get("mac1", {})
            self.assertEqual(mac_surface.get("status"), "not_ready")
            self.assertEqual(mac_surface.get("cause"), "desktop_executor_absent")
            mac_checks = {c.get("name"): c.get("ok") for c in mac_surface.get("checks", [])}
            self.assertEqual(len(mac_checks), 3, f"mac1 checks={mac_surface.get('checks')!r}")
            self.assertTrue(
                sum(1 for ok in mac_checks.values() if ok is False) >= 1,
                "실행기 확인 항목이 실패해야 함",
            )

            lin_surface = surfaces.get("lin1", {})
            self.assertEqual(lin_surface.get("cause"), "platform_mismatch")

            human_surface = surfaces.get("human1", {})
            self.assertEqual(human_surface.get("status"), "ready")

            for surface in surfaces.values():
                self.assertNotIn(
                    surface.get("cause"),
                    ("secret_literal", "secret_missing"),
                    "표면 cause에 비밀 누락이 섞임",
                )

            top_secrets = {s["name"]: s for s in parsed.get("secrets", [])}
            self.assertIn(env_var_name, top_secrets)
            self.assertFalse(top_secrets[env_var_name].get("ok"))
            self.assertIn(env_var_name, top_secrets[env_var_name].get("remediation", ""))


class TestEnvCheckServiceFailure(unittest.TestCase):
    """S-4 — 즉시 종료하는 서비스는 `service_start_failed`로 닫힌다(PLAN D-8)."""

    def test_service_exit_immediately_reports_service_start_failed(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as artifact_root:
            root = pathlib.Path(tmp)
            config = {
                "schema_version": "1.0",
                "services": [
                    {"id": "api-svc", "command": [_PYTHON, "-c", "import sys; sys.exit(3)"]}
                ],
                "surfaces": [
                    {"id": "api1", "kind": "api", "service": "api-svc", "health_path": "/health"}
                ],
            }
            _write_config(root, config)
            code, out, err, parsed = _run_cli(
                ["e2e", "env-check", "--project-root", str(root), "--artifact-root", artifact_root]
            )
            self.assertEqual(code, 1, f"stdout={out!r} stderr={err!r}")
            self.assertIsNotNone(parsed, f"stdout이 JSON이 아님: {out!r} stderr={err!r}")
            surfaces = {s["id"]: s for s in parsed.get("surfaces", [])}
            api_surface = surfaces.get("api1", {})
            self.assertEqual(api_surface.get("status"), "not_ready")
            self.assertEqual(api_surface.get("cause"), "service_start_failed")
            self.assertTrue(api_surface.get("remediation"))
            checks = api_surface.get("checks", [])
            detail_blob = json.dumps(checks)
            self.assertIn("readiness", detail_blob, f"로그 경로가 detail에 없음: {checks!r}")

    def test_skill_setup_section_does_not_recompute_result(self):
        skill_path = _TOOL_DIR.parent.parent / "skills" / "opal-e2e" / "SKILL.md"
        self.assertTrue(skill_path.exists(), f"{skill_path} 없음")
        text = skill_path.read_text(encoding="utf-8")
        self.assertIn("## setup", text)
        setup_section = text.split("## setup", 1)[1]
        self.assertIn("env-check", setup_section)
        self.assertNotIn("재계산", setup_section)


class TestNoDashboardStringLeft(unittest.TestCase):
    """S-5 — `dashboard` 고정 경로가 test-tool 코드에 남지 않고 설정으로 옮겨진다(PLAN D-10)."""

    def test_no_dashboard_string_in_lib_e2e_or_router(self):
        proc = subprocess.run(
            [
                "grep", "-rn", "dashboard",
                str(_TOOL_DIR / "lib" / "e2e"),
                str(_TEST_TOOL_PY),
            ],
            capture_output=True,
            text=True,
        )
        hits = [line for line in proc.stdout.splitlines() if line.strip()]
        self.assertEqual(hits, [], f"dashboard 문자열이 남아 있음: {hits!r}")

    def test_repo_environment_json_has_dashboard_service(self):
        env_path = _TOOL_DIR.parent.parent.parent / ".opal" / "e2e" / "environment.json"
        self.assertTrue(env_path.exists(), f"{env_path} 없음")
        config = json.loads(env_path.read_text(encoding="utf-8"))
        commands = [
            " ".join(svc.get("command", [])) for svc in config.get("services", [])
        ]
        self.assertTrue(
            any("dashboard" in cmd or "uvicorn" in cmd for cmd in commands),
            f"dashboard 기동 명령이 설정에 없음: {commands!r}",
        )


def _write_scenario(task_dir: pathlib.Path, scenario_id: str, profile: str, surface_ref=None):
    scenario = {
        "id": scenario_id,
        "acceptance_ref": ["AC-5"],
        "type": "integration",
        "expected": "S-159 RED 계약 검증용 최소 시나리오",
        "red_required": False,
        "required_fidelity": "mock",
        "surface_ref": surface_ref,
        "surface_kind": "cli",
        "profile": profile,
        "actors": ["service"],
        "steps": [{"id": "noop", "executor": profile}],
        "assertions": [{"id": f"{scenario_id}-a1", "expected": "시나리오 도달"}],
        "required_evidence": ["metadata"],
        "handoff": None,
        "result": None,
        "operational_status": None,
        "observed_executors": [],
        "assertion_results": [],
        "observed_evidence": [],
        "handoff_state": None,
        "run_id": None,
        "evidence": None,
        "marked_at": None,
        "fidelity": "mock",
    }
    payload = {
        "schema_version": "2.0",
        "task_id": task_dir.name,
        "locked": True,
        "created_at": "2026-09-26T00:00:00+09:00",
        "locked_at": "2026-09-26T00:00:00+09:00",
        "scenarios": [scenario],
    }
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "test-scenario.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_run_artifacts(parsed_or_payload: dict):
    """CLI stdout이나 `run_e2e()` 반환값의 `run_json_path`를 따라가 run.json·owned.json을 읽는다.

    §B.1.1 계약상 run stdout/payload 필드 집합은 14키로 동결돼 있으므로(D-6·D-9의
    `detail_code`, D-9의 임대 해제·process_groups 잔존 확인은 payload 자체가 아니라
    `run_json_path`가 가리키는 run.json과, 같은 run 디렉터리의 `owned.json` 대장에서
    읽는다(기존 `test_e2e_runtime.py::TestOrchestratorRunJson._run` 패턴).
    """
    run_json_path = pathlib.Path(parsed_or_payload["run_json_path"])
    run_json = json.loads(run_json_path.read_text(encoding="utf-8"))
    owned_path = run_json_path.parent / "owned.json"
    owned = json.loads(owned_path.read_text(encoding="utf-8")) if owned_path.exists() else {}
    return run_json, owned


class TestRunEnvironmentBlocked(unittest.TestCase):
    """S-6 — 설정 부재·무효 프로젝트에서 `e2e run`이 blocked/exit19로 닫힌다(PLAN D-10)."""

    def _run(self, worktree_root, scenario_id, task_dir):
        return _run_cli(
            [
                "e2e", "run",
                "--scenario", scenario_id,
                "--task-path", str(task_dir),
                "--target", e2e_target.TARGET_SOURCE_WORKTREE,
                "--worktree-root", str(worktree_root),
            ]
        )

    def test_missing_config_is_blocked_with_config_missing_detail(self):
        with tempfile.TemporaryDirectory() as worktree, tempfile.TemporaryDirectory() as taskdir:
            task_dir = pathlib.Path(taskdir) / "task"
            _write_scenario(task_dir, "S-1", "api")
            code, out, err, parsed = self._run(worktree, "S-1", task_dir)
            self.assertIsNotNone(parsed, f"stdout이 JSON이 아님: {out!r} stderr={err!r}")
            self.assertEqual(parsed.get("status"), "blocked", f"payload={parsed!r}")
            self.assertEqual(code, 19, f"stdout={out!r} stderr={err!r}")
            self.assertIn("run_json_path", parsed, f"payload={parsed!r}")
            run_json, owned = _load_run_artifacts(parsed)
            self.assertEqual(run_json.get("detail_code"), "e2e_env_config_missing", f"run_json={run_json!r}")
            self.assertIn("env-inspect", json.dumps(run_json.get("detail", run_json)))
            self.assertEqual(len(run_json.get("lease_released", [])), 2, f"run_json={run_json!r}")
            self.assertEqual(owned.get("process_groups", None), [])

    def test_invalid_config_is_blocked_with_config_invalid_detail(self):
        with tempfile.TemporaryDirectory() as worktree, tempfile.TemporaryDirectory() as taskdir:
            root = pathlib.Path(worktree)
            _write_config(root, {"schema_version": "1.0", "surfaces": []})  # services 누락
            task_dir = pathlib.Path(taskdir) / "task"
            _write_scenario(task_dir, "S-1", "api")
            code, out, err, parsed = self._run(worktree, "S-1", task_dir)
            self.assertIsNotNone(parsed, f"stdout이 JSON이 아님: {out!r} stderr={err!r}")
            self.assertEqual(parsed.get("status"), "blocked", f"payload={parsed!r}")
            self.assertEqual(code, 19, f"stdout={out!r} stderr={err!r}")
            self.assertIn("run_json_path", parsed, f"payload={parsed!r}")
            run_json, owned = _load_run_artifacts(parsed)
            self.assertEqual(run_json.get("detail_code"), "e2e_env_config_invalid", f"run_json={run_json!r}")
            self.assertEqual(len(run_json.get("lease_released", [])), 2, f"run_json={run_json!r}")
            self.assertEqual(owned.get("process_groups", None), [])


class TestRunSurfaceSelection(unittest.TestCase):
    """S-7 — 동종 표면 모호/부재는 `blocked` + D-9 코드로 닫힌다(PLAN D-9)."""

    def setUp(self):
        self._original_registry = dict(e2e_drivers.registered_drivers())

    def tearDown(self):
        e2e_drivers.registered_drivers.__globals__  # no-op, keep lints quiet
        # 등록표를 원복 — 다른 테스트에 stub driver가 새어 나가지 않게 한다.
        current = e2e_drivers.registered_drivers()
        for key in list(current.keys()):
            if key not in self._original_registry:
                del current[key]

    def test_ambiguous_web_surface_is_blocked(self):
        _register_stub_driver_for_gate()
        with tempfile.TemporaryDirectory() as worktree, tempfile.TemporaryDirectory() as taskdir, \
                tempfile.TemporaryDirectory() as artifact_root:
            root = pathlib.Path(worktree)
            config = {
                "schema_version": "1.0",
                "services": [],
                "surfaces": [
                    {"id": "alpha", "kind": "web", "url": "http://127.0.0.1:9/", "path": "/"},
                    {"id": "beta", "kind": "web", "url": "http://127.0.0.1:9/", "path": "/"},
                ],
            }
            _write_config(root, config)
            task_dir = pathlib.Path(taskdir) / "task"
            _write_scenario(task_dir, "S-1", "browser", surface_ref="gamma.home")
            payload = e2e_orchestrator.run_e2e(
                target=e2e_target.TARGET_SOURCE_WORKTREE,
                scenario_id="S-1",
                task_path=str(task_dir),
                worktree_root=worktree,
                artifact_root=artifact_root,
            )
            self.assertEqual(payload.get("status"), "blocked", f"payload={payload!r}")
            self.assertIn("run_json_path", payload, f"payload={payload!r}")
            run_json, owned = _load_run_artifacts(payload)
            self.assertEqual(
                run_json.get("detail_code"), "e2e_env_surface_ambiguous", f"run_json={run_json!r}"
            )
            self.assertEqual(owned.get("process_groups", None), [])

    def test_missing_api_surface_is_blocked(self):
        with tempfile.TemporaryDirectory() as worktree, tempfile.TemporaryDirectory() as taskdir, \
                tempfile.TemporaryDirectory() as artifact_root:
            root = pathlib.Path(worktree)
            config = {
                "schema_version": "1.0",
                "services": [],
                "surfaces": [{"id": "human1", "kind": "human"}],
            }
            _write_config(root, config)
            task_dir = pathlib.Path(taskdir) / "task"
            _write_scenario(task_dir, "S-1", "api")
            payload = e2e_orchestrator.run_e2e(
                target=e2e_target.TARGET_SOURCE_WORKTREE,
                scenario_id="S-1",
                task_path=str(task_dir),
                worktree_root=worktree,
                artifact_root=artifact_root,
            )
            self.assertEqual(payload.get("status"), "blocked", f"payload={payload!r}")
            self.assertIn("run_json_path", payload, f"payload={payload!r}")
            run_json, owned = _load_run_artifacts(payload)
            self.assertEqual(
                run_json.get("detail_code"), "e2e_env_surface_missing", f"run_json={run_json!r}"
            )
            self.assertEqual(owned.get("process_groups", None), [])


if __name__ == "__main__":
    unittest.main()
