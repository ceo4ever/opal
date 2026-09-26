"""
@header {
  "module": "test_e2e_environment",
  "task": "159-260926-opds-E2E-테스트환경-설정체계",
  "layer": "test",
  "domain": "opal-tools",
  "description": "lib/e2e/environment 모듈 단위 검증(유효 7종 표면 구성, D-6 위반 코드 11종별 거부와 비밀 원문 비노출, 치환 토큰·from_env 해석, 의존 순서, 표면 선택, load 상태 3종)과 runtime.start_service의 실제 프로세스 기동(http health·port health·조기 종료·상태 불일치·json_field 부재·실패 시 그룹 회수), process.host_platform 값 집합을 검증한다.",
  "scenarios": ["S-1", "S-5", "S-8"],
  "exports": ["TestValidateValid", "TestValidateViolations", "TestLoad", "TestServiceOrder", "TestRenderService", "TestSelectSurface", "TestStartService", "TestHostPlatform", "TestRepoEnvironment"]
}
"""
from __future__ import annotations

import copy
import json
import os
import pathlib
import shutil
import socket
import sys
import tempfile
import time
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
_SOURCE_ROOT = _TOOL_DIR.parent.parent.parent

from lib.e2e import environment as env  # noqa: E402
from lib.e2e import ports as e2e_ports  # noqa: E402
from lib.e2e import process as e2e_process  # noqa: E402
from lib.e2e import runtime as e2e_runtime  # noqa: E402


def _base():
    return {
        "schema_version": "1.0",
        "services": [
            {"id": "api", "command": ["{python}", "server.py", "--port", "{port}"]},
            {
                "id": "web",
                "command": ["npm", "run", "dev", "--", "--port", "{port}"],
                "cwd": "web",
                "env": {"API_URL": "{service.api.url}", "APP_TOKEN": {"from_env": "APP_TOKEN"}},
                "depends_on": ["api"],
                "health": {"type": "port"},
                "startup_timeout_s": 90,
            },
        ],
        "surfaces": [
            {"id": "site", "kind": "web", "service": "web", "path": "/"},
            {"id": "public-api", "kind": "api", "url": "https://api.example.com"},
            {"id": "mac", "kind": "macos-app", "app": {"path": "/Applications/X.app"}},
            {"id": "win", "kind": "windows-app", "app": {"launch": ["x.exe"]}},
            {"id": "lin", "kind": "linux-app", "app": {"path": "/usr/bin/x", "launch": ["x"]}},
            {"id": "ops", "kind": "human"},
            {"id": "site-remote", "kind": "web", "url": "https://staging.example.com", "path": "/app"},
        ],
        "secrets": [{"name": "APP_TOKEN", "purpose": "로그인"}],
        "data": {"prepare": ["{python}", "seed.py"], "restore": ["{python}", "reset.py"], "notes": "샘플"},
        "external_integrations": [{"name": "payments", "policy": "sandbox"}],
    }


def _codes(violations):
    return {(v["path"], v["code"]) for v in violations}


class TestValidateValid(unittest.TestCase):
    def test_all_surface_kinds_and_mixed_config_are_valid(self):
        self.assertEqual(env.validate(_base()), [])

    def test_empty_services_and_surfaces_are_valid(self):
        self.assertEqual(env.validate({"schema_version": "1.0", "services": [], "surfaces": []}), [])

    def test_violation_shape(self):
        violations = env.validate({"schema_version": "1.0", "surfaces": []})
        self.assertTrue(violations)
        for item in violations:
            self.assertEqual(set(item), {"path", "code", "detail"})
            self.assertIn(item["code"], env.VIOLATION_CODES)


class TestValidateViolations(unittest.TestCase):
    def _mutate(self, fn):
        config = _base()
        fn(config)
        return env.validate(config)

    def test_required_field_missing(self):
        v = self._mutate(lambda c: c["services"][0].pop("command"))
        self.assertIn(("services[0].command", "required_field_missing"), _codes(v))
        v = env.validate({"schema_version": "1.0", "surfaces": []})
        self.assertIn(("services", "required_field_missing"), _codes(v))
        v = self._mutate(lambda c: c["surfaces"][0].pop("service"))
        self.assertIn(("surfaces[0].service", "required_field_missing"), _codes(v))
        v = self._mutate(lambda c: c["surfaces"][2].update(app={}))
        self.assertIn(("surfaces[2].app.path", "required_field_missing"), _codes(v))

    def test_unknown_field(self):
        v = self._mutate(lambda c: c.update(extra=1))
        self.assertIn(("extra", "unknown_field"), _codes(v))
        v = self._mutate(lambda c: c["services"][0].update(restart=True))
        self.assertIn(("services[0].restart", "unknown_field"), _codes(v))
        v = self._mutate(lambda c: c["surfaces"][5].update(url="http://x"))
        self.assertIn(("surfaces[5].url", "unknown_field"), _codes(v))
        v = self._mutate(lambda c: c["services"][1].update(health={"type": "port", "path": "/x"}))
        self.assertIn(("services[1].health.path", "unknown_field"), _codes(v))

    def test_invalid_type(self):
        v = self._mutate(lambda c: c["services"][0].update(command="python server.py"))
        self.assertIn(("services[0].command", "invalid_type"), _codes(v))
        v = self._mutate(lambda c: c["services"][0].update(id="Bad_Id"))
        self.assertIn(("services[0].id", "invalid_type"), _codes(v))
        v = self._mutate(lambda c: c["services"][0].update(startup_timeout_s=0))
        self.assertIn(("services[0].startup_timeout_s", "invalid_type"), _codes(v))
        self.assertIn(("$", "invalid_type"), _codes(env.validate([])))

    def test_invalid_kind(self):
        v = self._mutate(lambda c: c["surfaces"][0].update(kind="mobile"))
        self.assertIn(("surfaces[0].kind", "invalid_kind"), _codes(v))
        v = self._mutate(lambda c: c["services"][1].update(health={"type": "tcp"}))
        self.assertIn(("services[1].health.type", "invalid_kind"), _codes(v))

    def test_duplicate_id(self):
        v = self._mutate(lambda c: c["services"].append(copy.deepcopy(c["services"][0])))
        self.assertIn(("services[2].id", "duplicate_id"), _codes(v))
        v = self._mutate(lambda c: c["surfaces"].append({"id": "ops", "kind": "human"}))
        self.assertIn(("surfaces[7].id", "duplicate_id"), _codes(v))

    def test_unknown_service_ref(self):
        v = self._mutate(lambda c: c["surfaces"][0].update(service="nope"))
        self.assertIn(("surfaces[0].service", "unknown_service_ref"), _codes(v))
        v = self._mutate(lambda c: c["services"][1].update(depends_on=["nope"]))
        self.assertIn(("services[1].depends_on[0]", "unknown_service_ref"), _codes(v))
        v = self._mutate(lambda c: c["services"][1]["env"].update(X="{service.nope.url}"))
        self.assertIn(("services[1].env.X", "unknown_service_ref"), _codes(v))

    def test_surface_target_conflict(self):
        v = self._mutate(lambda c: c["surfaces"][0].update(url="http://127.0.0.1:1"))
        self.assertIn(("surfaces[0]", "surface_target_conflict"), _codes(v))

    def test_dependency_cycle(self):
        v = self._mutate(lambda c: c["services"][0].update(depends_on=["web"]))
        self.assertIn("dependency_cycle", {x["code"] for x in v})
        v = self._mutate(lambda c: c["services"][0].update(depends_on=["api"]))
        self.assertIn("dependency_cycle", {x["code"] for x in v})

    def test_invalid_placeholder(self):
        v = self._mutate(lambda c: c["services"][0]["command"].append("{home}"))
        self.assertIn(("services[0].command[4]", "invalid_placeholder"), _codes(v))
        v = self._mutate(lambda c: c["services"][0]["command"].append("{service.api.host}"))
        self.assertIn(("services[0].command[4]", "invalid_placeholder"), _codes(v))
        # `{{ }}`는 리터럴 중괄호라 허용된다.
        v = self._mutate(lambda c: c["services"][0]["command"].append("print({{}})"))
        self.assertEqual(v, [])

    def test_path_escape(self):
        for cwd in ("..", "../other", "/tmp", "a/../../b", "{project_root}/.."):
            v = self._mutate(lambda c, cwd=cwd: c["services"][0].update(cwd=cwd))
            self.assertIn(("services[0].cwd", "path_escape"), _codes(v), cwd)
        v = self._mutate(lambda c: c["services"][0].update(cwd="{project_root}/sub"))
        self.assertEqual(v, [])

    def test_cwd_non_root_token_is_path_escape(self):
        # GC-004: cwd에서는 `{project_root}` 외 토큰을 path_escape로 거부한다(치환 값이 루트 밖일 수 있다).
        for cwd in ("{python}/..", "{python}", "logs-{port}", "{service.api.url}"):
            v = self._mutate(lambda c, cwd=cwd: c["services"][0].update(cwd=cwd))
            self.assertIn(("services[0].cwd", "path_escape"), _codes(v), cwd)
            self.assertNotIn(("services[0].cwd", "invalid_placeholder"), _codes(v), cwd)

    def test_secret_literal_rules_do_not_echo_values(self):
        leak = "sk-literal-should-not-leak"
        v = self._mutate(lambda c: c["secrets"][0].update(value=leak))
        self.assertIn(("secrets[0].value", "secret_literal"), _codes(v))
        self.assertNotIn(leak, json.dumps(v))

        v = self._mutate(lambda c: c["services"][1]["env"].update(DB_PASSWORD=leak))
        self.assertIn(("services[1].env.DB_PASSWORD", "secret_literal"), _codes(v))
        self.assertNotIn(leak, json.dumps(v))

        for key in ("my_secret", "GITHUB_TOKEN", "OPENAI_API_KEY", "GCP_CREDENTIALS", "SSH_PRIVATE_KEY"):
            v = self._mutate(lambda c, key=key: c["services"][1]["env"].update({key: "x"}))
            self.assertIn("secret_literal", {x["code"] for x in v}, key)

        # redact_text가 마스킹하는 원문(Bearer·query 비밀값)은 어느 필드에 있어도 거부한다.
        v = self._mutate(lambda c: c["services"][0]["command"].append("Bearer abcdef123456"))
        self.assertIn(("services[0].command[4]", "secret_literal"), _codes(v))
        v = self._mutate(lambda c: c["surfaces"][1].update(url="https://api.example.com/?token=abc123"))
        self.assertIn(("surfaces[1].url", "secret_literal"), _codes(v))
        self.assertNotIn("abc123", json.dumps(v))


class TestLoad(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="opal-e2e-env-"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, text, rel=".opal/e2e/environment.json"):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_missing(self):
        result = env.load(str(self.root))
        self.assertEqual(result["status"], "missing")
        self.assertIsNone(result["config"])
        self.assertTrue(result["path"].endswith(os.path.join(".opal", "e2e", "environment.json")))

    def test_invalid_json_does_not_echo_content(self):
        self._write('{"secrets": [ "pw-leak-value" ')
        result = env.load(str(self.root))
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["violations"][0]["code"], "invalid_type")
        self.assertNotIn("pw-leak-value", json.dumps(result))

    def test_ok_normalizes_defaults(self):
        config = _base()
        config["surfaces"].append({"id": "api-local", "kind": "api", "service": "api"})
        self._write(json.dumps(config))
        result = env.load(str(self.root))
        self.assertEqual(result["status"], "ok", result["violations"])
        api = result["config"]["services"][0]
        self.assertEqual(api["cwd"], ".")
        self.assertEqual(api["health"], {"type": "port"})
        self.assertEqual(api["startup_timeout_s"], 60)
        self.assertEqual(result["config"]["surfaces"][-1]["health_path"], "/health")

    def test_explicit_file(self):
        path = self._write(json.dumps(_base()), rel="draft/env.json")
        result = env.load(str(self.root / "elsewhere"), file=str(path))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["path"], str(path))


class TestServiceOrder(unittest.TestCase):
    def test_dependency_order_is_stable(self):
        config = {
            "services": [
                {"id": "web", "command": ["x"], "depends_on": ["api", "db"]},
                {"id": "api", "command": ["x"], "depends_on": ["db"]},
                {"id": "db", "command": ["x"]},
                {"id": "worker", "command": ["x"]},
            ]
        }
        self.assertEqual(env.service_order(config), ["db", "api", "web", "worker"])

    def test_cycle_raises(self):
        config = {"services": [{"id": "a", "command": ["x"], "depends_on": ["b"]},
                               {"id": "b", "command": ["x"], "depends_on": ["a"]}]}
        with self.assertRaises(ValueError):
            env.service_order(config)


class TestRenderService(unittest.TestCase):
    def test_tokens_and_from_env(self):
        root = tempfile.mkdtemp(prefix="opal-e2e-render-")
        self.addCleanup(shutil.rmtree, root, True)
        service = {
            "id": "web",
            "command": ["{python}", "-m", "x", "--host", "{host}", "--port", "{port}", "{project_root}", "{{lit}}"],
            "cwd": "sub",
            "env": {
                "API_URL": "{service.api.url}",
                "API_PORT": "{service.api.port}",
                "APP_TOKEN": {"from_env": "S159_RENDER_TOKEN"},
                "MISSING": {"from_env": "S159_RENDER_ABSENT"},
            },
            "health": {"type": "http", "path": "/health"},
        }
        os.environ["S159_RENDER_TOKEN"] = "t0ken"
        os.environ.pop("S159_RENDER_ABSENT", None)
        self.addCleanup(os.environ.pop, "S159_RENDER_TOKEN", None)
        rendered = env.render_service(service, port=4100, ports_by_id={"api": 4200, "web": 4100}, project_root=root)
        resolved_root = str(pathlib.Path(root).resolve())
        self.assertEqual(
            rendered["argv"],
            [sys.executable, "-m", "x", "--host", "127.0.0.1", "--port", "4100", resolved_root, "{lit}"],
        )
        self.assertEqual(rendered["cwd"], os.path.join(resolved_root, "sub"))
        self.assertEqual(rendered["env"]["API_URL"], "http://127.0.0.1:4200")
        self.assertEqual(rendered["env"]["API_PORT"], "4200")
        self.assertEqual(rendered["env"]["APP_TOKEN"], "t0ken")
        self.assertNotIn("MISSING", rendered["env"])
        self.assertEqual(rendered["missing_env"], ["S159_RENDER_ABSENT"])
        self.assertEqual(rendered["health"], {"type": "http", "path": "/health", "expect_status": 200, "json_field": None})
        self.assertEqual(rendered["url"], "http://127.0.0.1:4100")
        self.assertEqual(rendered["startup_timeout_s"], 60.0)

    def test_cwd_placeholder_outside_root_is_rejected(self):
        root = tempfile.mkdtemp(prefix="opal-e2e-render-")
        self.addCleanup(shutil.rmtree, root, True)
        with self.assertRaises(ValueError) as ctx:
            env.render_service({"id": "a", "command": ["x"], "cwd": "{python}/.."}, port=1, ports_by_id={},
                               project_root=root)
        self.assertTrue(str(ctx.exception).startswith("path_escape"), str(ctx.exception))

    def test_cwd_symlink_outside_root_is_rejected(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="opal-e2e-render-"))
        outside = pathlib.Path(tempfile.mkdtemp(prefix="opal-e2e-outside-"))
        self.addCleanup(shutil.rmtree, root, True)
        self.addCleanup(shutil.rmtree, outside, True)
        (root / "inside").mkdir()
        (root / "link-in").symlink_to(root / "inside", target_is_directory=True)
        (root / "link-out").symlink_to(outside, target_is_directory=True)
        service = {"id": "a", "command": ["x"], "cwd": "link-out"}
        # 어휘 검증은 통과하지만(파일 시스템을 보지 않는다) 기동 값 확정에서 거부된다.
        self.assertNotIn("path_escape", [item["code"] for item in env.validate({"schema_version": "1.0", "services": [service]})])
        with self.assertRaises(ValueError) as ctx:
            env.render_service(service, port=1, ports_by_id={}, project_root=str(root))
        self.assertTrue(str(ctx.exception).startswith("path_escape"), str(ctx.exception))
        self.assertNotIn(str(outside), str(ctx.exception))
        # 루트 안을 가리키는 symlink는 허용된다.
        rendered = env.render_service(dict(service, cwd="link-in"), port=1, ports_by_id={}, project_root=str(root))
        self.assertEqual(rendered["cwd"], os.path.join(str(root.resolve()), "link-in"))

    def test_bare_command_is_resolved_on_path(self):
        rendered = env.render_service({"id": "a", "command": ["sh", "-c", "true"]}, port=1, ports_by_id={},
                                      project_root=str(_SOURCE_ROOT))
        self.assertTrue(os.path.isabs(rendered["argv"][0]))
        self.assertEqual(rendered["health"], {"type": "port"})


class TestSelectSurface(unittest.TestCase):
    def setUp(self):
        self.config = env.normalize(_base())

    def test_single(self):
        result = env.select_surface(self.config, "api", None)
        self.assertEqual((result["status"], result["surface"]["id"]), ("ok", "public-api"))

    def test_missing(self):
        config = {"surfaces": [{"id": "ops", "kind": "human"}]}
        result = env.select_surface(config, "api", "x.y")
        self.assertEqual(result["status"], "missing")
        self.assertEqual(result["detail_code"], "e2e_env_surface_missing")

    def test_multiple_resolved_by_surface_ref_head(self):
        result = env.select_surface(self.config, "web", "site-remote.home")
        self.assertEqual((result["status"], result["surface"]["id"]), ("ok", "site-remote"))

    def test_multiple_ambiguous(self):
        for ref in ("gamma.home", None, ""):
            result = env.select_surface(self.config, "web", ref)
            self.assertEqual(result["status"], "ambiguous", ref)
            self.assertEqual(result["detail_code"], "e2e_env_surface_ambiguous")
            self.assertEqual(result["candidates"], ["site", "site-remote"])


_SERVER = """
import http.server, json, sys
port = int(sys.argv[1]); status = int(sys.argv[2]); body = sys.argv[3]
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body.encode())
    def log_message(self, *a):
        pass
http.server.HTTPServer(('127.0.0.1', port), H).serve_forever()
"""

# http health를 선언했지만 HTTP가 아닌 바이트를 돌려주는 raw TCP 서비스. 같은 그룹에 자식 1건을 둔다.
_RAW_TCP_SERVER = """
import os, socket, subprocess, sys
port = int(sys.argv[1]); pid_file = sys.argv[2]
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
with open(pid_file, 'w') as fh:
    fh.write(str(os.getpid()))
srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(('127.0.0.1', port)); srv.listen(8)
while True:
    conn, _ = srv.accept()
    try:
        conn.recv(4096)
        conn.sendall(b'NOT-HTTP garbage bytes\\r\\n\\r\\n')
    finally:
        conn.close()
"""


class TestStartService(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="opal-e2e-start-"))
        (self.root / "server.py").write_text(_SERVER, encoding="utf-8")
        self.artifact_dir = tempfile.mkdtemp(prefix="opal-e2e-start-art-")
        self.handles = []

    def tearDown(self):
        report = e2e_runtime.stop_all(self.handles)
        self.assertEqual(report.leaked, [])
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.artifact_dir, ignore_errors=True)

    def _render(self, *, status=200, body='{"status": "ok"}', health=None, timeout=10, command=None):
        port = e2e_ports.find_free_port()
        service = {
            "id": "svc",
            # 본문의 JSON 중괄호는 치환 토큰 문법과 겹치므로 `{{`·`}}`로 적는다.
            "command": command or ["{python}", "server.py", "{port}", str(status),
                                   body.replace("{", "{{").replace("}", "}}")],
            "startup_timeout_s": timeout,
        }
        if health is not None:
            service["health"] = health
        return port, env.render_service(service, port=port, ports_by_id={}, project_root=str(self.root))

    def test_http_health_with_json_field(self):
        port, rendered = self._render(health={"type": "http", "path": "/health", "json_field": "status"})
        handle = e2e_runtime.start_service(rendered, role="svc", port=port, artifact_dir=self.artifact_dir)
        self.handles.append(handle)
        self.assertEqual(handle.url, f"http://127.0.0.1:{port}")
        self.assertEqual(handle.role, "svc")
        self.assertTrue(pathlib.Path(handle.log_paths["stdout"]).exists())

    def test_default_port_health(self):
        port, rendered = self._render()
        handle = e2e_runtime.start_service(rendered, role="svc", port=port, artifact_dir=self.artifact_dir)
        self.handles.append(handle)
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass

    def _assert_fails(self, rendered, port, reason):
        with self.assertRaises(e2e_runtime.SutStartupError) as ctx:
            e2e_runtime.start_service(rendered, role="svc", port=port, artifact_dir=self.artifact_dir)
        self.assertEqual(ctx.exception.reason, reason, ctx.exception.detail)
        self.assertIn("log=", ctx.exception.detail)
        return ctx.exception

    def test_early_exit(self):
        port, rendered = self._render(command=["{python}", "-c", "import sys; sys.exit(3)"])
        self._assert_fails(rendered, port, "process_exited_early")

    def test_spawn_failure_is_process_exited_early(self):
        port, rendered = self._render(command=["/nonexistent/opal-e2e-binary"])
        self._assert_fails(rendered, port, "process_exited_early")

    def test_status_mismatch_is_bad_response_and_group_reclaimed(self):
        port, rendered = self._render(status=503, health={"type": "http", "path": "/health"}, timeout=2)
        self._assert_fails(rendered, port, "health_bad_response")
        # 실패 시 start_service가 그룹을 회수했으므로 포트가 다시 비어 있어야 한다.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            self.assertNotEqual(sock.connect_ex(("127.0.0.1", port)), 0)

    def test_missing_json_field_is_bad_response(self):
        port, rendered = self._render(body='{"ok": true}', health={"type": "http", "path": "/", "json_field": "status"})
        self._assert_fails(rendered, port, "health_bad_response")

    def _assert_group_gone(self, pid_file):
        pgid = int(pid_file.read_text(encoding="utf-8"))
        self.assertEqual(e2e_process.process_group_members(pgid), [])
        self.assertFalse(e2e_process.pid_alive(pgid))

    def test_non_http_bytes_is_bad_response_and_group_reclaimed(self):
        # GC-001: http.client.HTTPException(BadStatusLine 등)은 health_bad_response로 바뀌고 그룹이 남지 않는다.
        (self.root / "raw.py").write_text(_RAW_TCP_SERVER, encoding="utf-8")
        pid_file = self.root / "raw.pid"
        port, rendered = self._render(command=["{python}", "raw.py", "{port}", str(pid_file)],
                                      health={"type": "http", "path": "/health"}, timeout=5)
        self._assert_fails(rendered, port, "health_bad_response")
        self._assert_group_gone(pid_file)

    def test_unexpected_exception_reclaims_group_and_propagates(self):
        # GC-001: SutStartupError가 아닌 예외도 그룹을 회수한 뒤 그대로 올린다.
        pid_file = self.root / "sleep.pid"
        script = f"import os, time; open({str(pid_file)!r}, 'w').write(str(os.getpid())); time.sleep(60)"
        port, rendered = self._render(command=["{python}", "-c", script.replace("{", "{{").replace("}", "}}")],
                                      health={"type": "http", "path": "/"}, timeout=5)

        def _boom(*_args, **_kwargs):
            deadline = time.monotonic() + 5
            while not pid_file.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            raise RuntimeError("unexpected")

        original = e2e_runtime.wait_http_health
        e2e_runtime.wait_http_health = _boom
        self.addCleanup(setattr, e2e_runtime, "wait_http_health", original)
        with self.assertRaises(RuntimeError):
            e2e_runtime.start_service(rendered, role="svc", port=port, artifact_dir=self.artifact_dir)
        self._assert_group_gone(pid_file)

    def test_port_never_opens_is_timeout(self):
        port, rendered = self._render(command=["{python}", "-c", "import time; time.sleep(30)"], timeout=1)
        self._assert_fails(rendered, port, "health_timeout")


class TestHostPlatform(unittest.TestCase):
    def test_value_set(self):
        self.assertIn(e2e_process.host_platform(), ("macos", "windows", "linux"))


class TestRepoEnvironment(unittest.TestCase):
    """이 저장소 설정이 현재 기동 계약을 그대로 옮겼는지 확인한다(D-10·H-1·H-2)."""

    def test_repo_config_is_valid_and_matches_current_startup(self):
        result = env.load(str(_SOURCE_ROOT))
        self.assertEqual(result["status"], "ok", result["violations"])
        config = result["config"]
        self.assertEqual(env.service_order(config), ["backend", "frontend"])
        ports = {"backend": 41001, "frontend": 41002}
        backend = env.render_service(config["services"][0], port=41001, ports_by_id=ports,
                                     project_root=str(_SOURCE_ROOT))
        frontend = env.render_service(config["services"][1], port=41002, ports_by_id=ports,
                                      project_root=str(_SOURCE_ROOT))
        self.assertEqual(backend["argv"][0], sys.executable)
        self.assertEqual(backend["argv"][-4:], ["--host", "127.0.0.1", "--port", "41001"])
        self.assertEqual(backend["health"]["json_field"], "status")
        self.assertEqual(backend["startup_timeout_s"], 60.0)
        self.assertEqual(frontend["argv"][-1], "--strictPort")
        self.assertEqual(frontend["env"]["VITE_API_BASE_URL"], "http://127.0.0.1:41001")
        self.assertEqual(frontend["health"], {"type": "port"})
        self.assertEqual(frontend["startup_timeout_s"], 90.0)
        self.assertEqual(env.select_surface(config, "web", None)["surface"]["service"], "frontend")
        api = env.select_surface(config, "api", None)["surface"]
        self.assertEqual((api["id"], api["service"], api["health_path"]), ("console-api", "backend", "/health"))


if __name__ == "__main__":
    unittest.main()
