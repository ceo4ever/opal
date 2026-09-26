"""
@header {
  "module": "test_e2e_env_commands",
  "layer": "test",
  "domain": "opal-tools",
  "description": "`test-tool e2e env-inspect`·`env-validate`·`env-check`와 drivers.discover_installed 검증. CLI는 subprocess stdout JSON·exit으로, 브라우저 후보가 필요한 web 표면 판정은 readiness.check_readiness에 대역 driver 레지스트리를 넘겨 확인한다. 검토 무변경(트리 해시 동일), 검증 exit·오류 코드, 준비 검증의 ready·not_ready·skipped 순서·데스크톱 desktop_executor_absent·비밀 누락·의존 실패·URL 도달 실패·판정 뒤 프로세스와 임대 회수를 다룬다.",
  "scenarios": ["S-1", "S-2", "S-3", "S-4"],
  "exports": [
    "TestEnvValidateCli", "TestEnvInspectCli", "TestDiscoverInstalled",
    "TestEnvCheckCli", "TestReadinessInProcess"
  ]
}
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import tempfile
import threading
import http.server
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_PYTHON = sys.executable

sys.path.insert(0, str(_TOOL_DIR))

from lib.e2e import drivers as e2e_drivers  # noqa: E402
from lib.e2e import environment as e2e_environment  # noqa: E402
from lib.e2e import readiness as e2e_readiness  # noqa: E402

_SERVER_SCRIPT = (
    "import http.server, json, sys\n"
    "class H(http.server.BaseHTTPRequestHandler):\n"
    "    def log_message(self, *a):\n"
    "        pass\n"
    "    def do_GET(self):\n"
    "        status = 200 if self.path in ('/health', '/') else 404\n"
    "        self.send_response(status)\n"
    "        self.send_header('Content-Type', 'application/json')\n"
    "        self.end_headers()\n"
    "        self.wfile.write(json.dumps({'status': 'ok'}).encode())\n"
    "http.server.HTTPServer((sys.argv[1], int(sys.argv[2])), H).serve_forever()\n"
)


def _run_cli(args, cwd=None, env=None):
    proc = subprocess.run(
        [_PYTHON, str(_TEST_TOOL_PY), *args],
        cwd=cwd, capture_output=True, text=True, timeout=180, env=env,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    parsed = json.loads(proc.stdout) if len(lines) == 1 else None
    return proc.returncode, proc.stdout, proc.stderr, parsed


def _write_config(root: pathlib.Path, config: dict) -> pathlib.Path:
    path = root / ".opal" / "e2e" / "environment.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _tree_hash(root: pathlib.Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        rel = str(path.relative_to(root))
        digest.update(rel.encode())
        if path.is_file():
            stat = path.stat()
            digest.update(f"{stat.st_size}:{stat.st_mtime_ns}".encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _server_service(root: pathlib.Path, service_id: str = "api-svc", **extra) -> dict:
    script = root / "server.py"
    script.write_text(_SERVER_SCRIPT, encoding="utf-8")
    service = {
        "id": service_id,
        "command": ["{python}", str(script), "{host}", "{port}"],
        "health": {"type": "http", "path": "/health", "json_field": "status"},
        "startup_timeout_s": 20,
    }
    service.update(extra)
    return service


def _port_closed(url: str) -> bool:
    match = re.match(r"http://([^:/]+):(\d+)", url)
    host, port = match.group(1), int(match.group(2))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) != 0


def _started_url(checks) -> str:
    for check in checks:
        match = re.search(r"started on (http://\S+?);", check.get("detail") or "")
        if match:
            return match.group(1)
    raise AssertionError(f"no started url in {checks!r}")


class TestEnvValidateCli(unittest.TestCase):
    """S-1 — exit·error 코드·violations 계약(D-6)."""

    def test_valid_config_reports_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_config(root, {"schema_version": "1.0", "services": [], "surfaces": [{"id": "h", "kind": "human"}]})
            code, out, err, parsed = _run_cli(["e2e", "env-validate", "--project-root", str(root)])
            self.assertEqual(code, 0, out + err)
            self.assertEqual(parsed["command"], "e2e env-validate")
            self.assertTrue(parsed["ok"])
            self.assertEqual(parsed["summary"], {"services": 0, "surfaces": 1})

    def test_file_option_and_invalid_violation_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "custom.json"
            path.write_text(json.dumps({"schema_version": "1.0", "surfaces": []}), encoding="utf-8")
            code, out, err, parsed = _run_cli(["e2e", "env-validate", "--project-root", tmp, "--file", str(path)])
            self.assertEqual(code, 1, out + err)
            self.assertFalse(parsed["ok"])
            self.assertEqual(parsed["error"], "e2e_env_config_invalid")
            self.assertEqual(parsed["path"], str(path))
            for violation in parsed["violations"]:
                self.assertEqual(set(violation), {"path", "code", "detail"})
                self.assertIn(violation["code"], e2e_environment.VIOLATION_CODES)
            self.assertTrue(any(v["path"] == "services" for v in parsed["violations"]))

    def test_missing_config_error_code_is_registered(self):
        from test_tool import ERROR_CODES

        with tempfile.TemporaryDirectory() as tmp:
            code, out, err, parsed = _run_cli(["e2e", "env-validate", "--project-root", tmp])
            self.assertEqual(code, 1, out + err)
            self.assertEqual(parsed["error"], "e2e_env_config_missing")
            self.assertIn(parsed["error"], ERROR_CODES)
        for key in ("e2e_env_config_missing", "e2e_env_config_invalid",
                    "e2e_env_surface_missing", "e2e_env_surface_ambiguous"):
            self.assertIn(key, ERROR_CODES)

    def test_project_root_defaults_to_git_toplevel(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp).resolve()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            _write_config(root, {"schema_version": "1.0", "services": [], "surfaces": []})
            nested = root / "a" / "b"
            nested.mkdir(parents=True)
            code, out, err, parsed = _run_cli(["e2e", "env-validate"], cwd=str(nested))
            self.assertEqual(code, 0, out + err)
            self.assertEqual(pathlib.Path(parsed["path"]).resolve(),
                             (root / ".opal" / "e2e" / "environment.json").resolve())


class TestEnvInspectCli(unittest.TestCase):
    """S-2 — 검토는 트리를 바꾸지 않고 후보·driver·비밀 이름만 보고한다(D-7)."""

    def test_inspect_is_read_only_and_reports_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "web").mkdir()
            (root / "web" / "package.json").write_text(json.dumps(
                {"scripts": {"dev": "next dev"}, "dependencies": {"next": "14"}}), encoding="utf-8")
            (root / "app.py").write_text(
                "from flask import Flask\napplication = Flask(__name__)\n", encoding="utf-8")
            (root / "tool.csproj").write_text("<Project/>", encoding="utf-8")
            (root / ".env.example").write_text("export API_TOKEN=secret-value-x\nPLAIN=1\n# c=2\n", encoding="utf-8")
            (root / "node_modules" / "dep").mkdir(parents=True)
            (root / "node_modules" / "dep" / "package.json").write_text(
                json.dumps({"scripts": {"dev": "vite"}, "dependencies": {"vite": "5"}}), encoding="utf-8")

            before = _tree_hash(root)
            code, out, err, parsed = _run_cli(["e2e", "env-inspect", "--project-root", str(root)])
            after = _tree_hash(root)

            self.assertEqual(code, 0, out + err)
            self.assertEqual(before, after)
            self.assertEqual(parsed["command"], "e2e env-inspect")
            self.assertEqual(parsed["config"], {
                "present": False, "path": str(root.resolve() / ".opal" / "e2e" / "environment.json"), "valid": None})
            by_kind = {}
            for candidate in parsed["surface_candidates"]:
                by_kind.setdefault(candidate["kind"], []).append(candidate)
            self.assertEqual([c["evidence"] for c in by_kind["web"]], [["web/package.json"]])
            self.assertEqual(by_kind["web"][0]["suggested"]["cwd"], "web")
            self.assertIn("{port}", by_kind["web"][0]["suggested"]["command"])
            self.assertIn("app:application", " ".join(by_kind["api"][0]["suggested"]["command"]))
            self.assertIn("windows-app", by_kind)
            self.assertEqual(parsed["secret_hints"], ["API_TOKEN", "PLAIN"])
            self.assertNotIn("secret-value-x", out)
            for driver in parsed["drivers"]:
                self.assertEqual(set(driver), {"driver", "session_mode", "installed", "binary"})

    def test_inspect_reports_invalid_existing_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_config(root, {"schema_version": "1.0"})
            before = _tree_hash(root)
            code, out, err, parsed = _run_cli(["e2e", "env-inspect", "--project-root", str(root)])
            self.assertEqual(code, 0, out + err)
            self.assertEqual(before, _tree_hash(root))
            self.assertTrue(parsed["config"]["present"])
            self.assertFalse(parsed["config"]["valid"])


class TestDiscoverInstalled(unittest.TestCase):
    """discover_installed는 생성자(binary 탐색) 외 세션 연산을 부르지 않는다."""

    def setUp(self):
        self._original = e2e_drivers.registered_drivers()

    def tearDown(self):
        e2e_drivers._REGISTRY.clear()
        e2e_drivers._REGISTRY.update(self._original)

    def test_reports_binary_without_probe(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            binary = pathlib.Path(tmp) / "fake-driver"
            binary.write_text("#!/bin/sh\n", encoding="utf-8")
            binary.chmod(0o755)

            class _Stub(e2e_drivers.BrowserDriver):
                def __init__(self, **_kwargs):
                    self.binary_path = str(binary)

                def dispatch(self, operation, payload=None):
                    calls.append(operation)
                    raise AssertionError("session operation must not be called")

            e2e_drivers._REGISTRY.clear()
            e2e_drivers.register_driver("cmux", "owned-surface", _Stub)
            result = e2e_drivers.discover_installed(tmp)

        order = [(entry["driver"], entry["session_mode"]) for entry in e2e_drivers.CANDIDATE_ORDER]
        self.assertEqual([(r["driver"], r["session_mode"]) for r in result], order)
        cmux = next(r for r in result if r["driver"] == "cmux")
        self.assertEqual(cmux, {"driver": "cmux", "session_mode": "owned-surface",
                                "installed": True, "binary": str(binary)})
        others = [r for r in result if r["driver"] != "cmux"]
        self.assertTrue(all(r["installed"] is False and r["binary"] is None for r in others))
        self.assertEqual(calls, [])


class TestEnvCheckCli(unittest.TestCase):
    """S-3·S-4 — CLI 준비 검증(D-8)."""

    def test_ready_api_and_human_exit_zero_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as artifacts:
            root = pathlib.Path(tmp)
            _write_config(root, {
                "schema_version": "1.0",
                "services": [_server_service(root)],
                "surfaces": [
                    {"id": "api1", "kind": "api", "service": "api-svc", "health_path": "/health"},
                    {"id": "api2", "kind": "api", "service": "api-svc"},
                    {"id": "human1", "kind": "human"},
                ],
                "secrets": [{"name": "PATH"}],
            })
            code, out, err, parsed = _run_cli(
                ["e2e", "env-check", "--project-root", str(root), "--artifact-root", artifacts])
            self.assertEqual(code, 0, out + err)
            self.assertTrue(parsed["ok"])
            self.assertTrue(parsed["ready"])
            self.assertEqual(parsed["secrets"], [{"name": "PATH", "ok": True, "remediation": None}])
            surfaces = {s["id"]: s for s in parsed["surfaces"]}
            api1 = surfaces["api1"]
            self.assertEqual([c["name"] for c in api1["checks"]], ["service_start", "health", "executor"])
            self.assertTrue(all(c["ok"] for c in api1["checks"]))
            self.assertIsNone(api1["cause"])
            self.assertIsNone(api1["remediation"])
            self.assertEqual([c["name"] for c in surfaces["human1"]["checks"]], ["executor"])
            # 공유 서비스는 1회만 기동된다 — 두 표면이 같은 URL을 본다.
            url = _started_url(api1["checks"])
            self.assertEqual(url, _started_url(surfaces["api2"]["checks"]))
            self.assertTrue(_port_closed(url), "판정 뒤 서비스가 남아 있음")
            log_dir = pathlib.Path(artifacts) / "readiness"
            logs = list(log_dir.glob("*/api-svc.log"))
            self.assertEqual(len(logs), 1)
            self.assertEqual(list((pathlib.Path(artifacts) / ".leases").glob("*.json")), [])

    def test_desktop_secret_and_service_failure(self):
        name = "E2E_ENV_CMD_TEST_TOKEN"
        env = dict(os.environ)
        env.pop(name, None)
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as artifacts:
            root = pathlib.Path(tmp)
            _write_config(root, {
                "schema_version": "1.0",
                "services": [
                    {"id": "dead", "command": ["{python}", "-c", "import sys; sys.exit(3)"]},
                    {"id": "child", "command": ["{python}", "-c", "import time; time.sleep(30)"],
                     "depends_on": ["dead"]},
                ],
                "surfaces": [
                    {"id": "a-dead", "kind": "api", "service": "dead"},
                    {"id": "a-child", "kind": "api", "service": "child"},
                    {"id": "mac1", "kind": "macos-app", "app": {"path": "/nonexistent/X.app"}},
                    {"id": "win1", "kind": "windows-app", "app": {"launch": ["true"]}},
                ],
                "secrets": [{"name": name}],
            })
            code, out, err, parsed = _run_cli(
                ["e2e", "env-check", "--project-root", str(root), "--artifact-root", artifacts], env=env)
            self.assertEqual(code, 1, out + err)
            self.assertFalse(parsed["ready"])
            surfaces = {s["id"]: s for s in parsed["surfaces"]}

            dead = surfaces["a-dead"]
            self.assertEqual(dead["cause"], "service_start_failed")
            self.assertEqual([c["detail"] for c in dead["checks"][1:]], ["skipped", "skipped"])
            self.assertIn(str(pathlib.Path(artifacts) / "readiness"), dead["checks"][0]["detail"])
            self.assertTrue(dead["remediation"])

            self.assertEqual(surfaces["a-child"]["cause"], "dependency_failed")

            for sid in ("mac1", "win1"):
                surface = surfaces[sid]
                self.assertEqual(surface["status"], "not_ready")
                self.assertEqual([c["name"] for c in surface["checks"]], ["platform", "app_present", "executor"])
                self.assertFalse(surface["checks"][2]["ok"])
            host = e2e_readiness.e2e_process.host_platform()
            if host == "macos":
                self.assertEqual(surfaces["mac1"]["cause"], "app_not_found")
                self.assertEqual(surfaces["win1"]["cause"], "platform_mismatch")
                self.assertEqual(surfaces["win1"]["checks"][1]["detail"], "skipped")

            secret = parsed["secrets"][0]
            self.assertEqual(secret["name"], name)
            self.assertFalse(secret["ok"])
            self.assertIn(f"export {name}=", secret["remediation"])
            causes = {s["cause"] for s in parsed["surfaces"]}
            self.assertTrue(causes <= set(e2e_readiness.CAUSE_CODES))

    def test_invalid_config_uses_validate_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_config(pathlib.Path(tmp), {"schema_version": "1.0", "surfaces": []})
            code, out, err, parsed = _run_cli(["e2e", "env-check", "--project-root", tmp])
            self.assertEqual(code, 1, out + err)
            self.assertEqual(parsed["error"], "e2e_env_config_invalid")
            self.assertFalse((pathlib.Path(tmp) / ".e2e").exists())


class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        status = 200 if self.path == "/health" else (503 if self.path == "/broken" else 200)
        self.send_response(status)
        self.end_headers()
        self.wfile.write(b"{}")


class TestReadinessInProcess(unittest.TestCase):
    """web 표면 판정 — 브라우저 후보 해석에 대역 레지스트리를 넘긴다."""

    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _stub_registry(self):
        class _Stub(e2e_drivers.BrowserDriver):
            name = "agent-browser"

            def __init__(self, **_kwargs):
                self.binary_path = None
                self.declared_version = None

            def op_probe(self, request):
                return {"available": True, "capabilities": {
                    key: {"available": True, "route": "native", "probed": True}
                    for key in e2e_drivers.CAPABILITY_KEYS}}

        return {("agent-browser", "orca-managed"): _Stub}

    def _check(self, surfaces, registry):
        config = e2e_environment.normalize({"schema_version": "1.0", "services": [], "surfaces": surfaces})
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as artifacts:
            return e2e_readiness.check_readiness(
                config, project_root=tmp, artifact_root=artifacts, driver_registry=registry)

    def test_url_surfaces_ready_with_driver(self):
        result = self._check([
            {"id": "w", "kind": "web", "url": self.url, "path": "/"},
            {"id": "a", "kind": "api", "url": self.url, "health_path": "/health"},
        ], self._stub_registry())
        self.assertTrue(result["ready"], result)
        web = result["surfaces"][0]
        self.assertEqual([c["name"] for c in web["checks"]], ["reachable", "response", "executor"])

    def test_web_without_driver_is_driver_unavailable(self):
        result = self._check([{"id": "w", "kind": "web", "url": self.url, "path": "/"}], {})
        self.assertEqual(result["surfaces"][0]["cause"], "driver_unavailable")

    def test_web_5xx_and_api_non_200(self):
        result = self._check([
            {"id": "w", "kind": "web", "url": self.url, "path": "/broken"},
            {"id": "a", "kind": "api", "url": self.url, "health_path": "/broken"},
        ], self._stub_registry())
        causes = [s["cause"] for s in result["surfaces"]]
        self.assertEqual(causes, ["health_bad_response", "health_bad_response"])

    def test_unreachable_url(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        result = self._check([{"id": "a", "kind": "api", "url": f"http://127.0.0.1:{port}"}], {})
        surface = result["surfaces"][0]
        self.assertEqual(surface["cause"], "url_unreachable")
        self.assertEqual([c["detail"] for c in surface["checks"][1:]], ["skipped", "skipped"])


if __name__ == "__main__":
    unittest.main()
