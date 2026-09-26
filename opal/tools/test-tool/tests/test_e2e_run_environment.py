"""
@header {
  "module": "test_e2e_run_environment",
  "task": "159-260926-opds-E2E-테스트환경-설정체계",
  "layer": "test",
  "domain": "opal-tools",
  "description": "e2e run의 설정 기반 SUT 기동(PLAN D-9·D-10)을 공개 진입점 orchestrator.run_e2e로 검증한다. 설정 부재·무효는 호환 역할 2건 임대 후 서비스 미기동 blocked(e2e_env_config_missing/invalid, env-inspect·//e2e setup 안내), 표면 없음·모호는 서비스 기동 전 blocked(e2e_env_surface_missing/ambiguous), 임시 프로젝트의 표준 라이브러리 HTTP 서비스는 설정 서비스 id로 임대·1회 기동·회수되고 api 표면의 health_path가 api probe에 전달된다. 두 번째 서비스 cwd가 프로젝트 밖을 가리키는 symlink(render path_escape)면 첫 기동 전에 걸려 어떤 서비스도 띄우지 않고 blocked(e2e_env_config_invalid, detail에 경로 원문 없음)·임대 해제로 끝난다.",
  "scenarios": ["S-6", "S-7"],
  "exports": ["TestRunConfigAbsentOrInvalid", "TestRunSurfaceSelectionFailure", "TestRunStartsConfiguredServices", "TestRunRenderViolationStartsNothing"]
}
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

from lib import e2e_contract  # noqa: E402
from lib.e2e import orchestrator as e2e_orchestrator  # noqa: E402
from lib.e2e import process as e2e_process  # noqa: E402
from lib.e2e import target as e2e_target  # noqa: E402

_SERVER_SOURCE = """\
import http.server, json, sys

port = int(sys.argv[sys.argv.index("--port") + 1])


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/ready":
            body = json.dumps({"status": "ok"}).encode()
            self.send_response(200)
        else:
            body = b"{}"
            self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
"""


def _write_config(root: pathlib.Path, config: dict) -> None:
    path = root / ".opal" / "e2e" / "environment.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding="utf-8")


def _write_scenario(task_dir: pathlib.Path, profile: str, surface_ref=None) -> None:
    scenario = {
        "id": "S-1",
        "acceptance_ref": ["AC-5"],
        "type": "integration",
        "expected": "설정 기반 SUT 기동 검증용 최소 시나리오",
        "red_required": False,
        "required_fidelity": "mock",
        "surface_ref": surface_ref,
        "surface_kind": "cli",
        "profile": profile,
        "actors": ["service"],
        "steps": [{"id": "noop", "executor": profile}],
        "assertions": [{"id": "S-1-a1", "expected": "시나리오 도달"}],
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
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "test-scenario.json").write_text(
        json.dumps(
            {
                "schema_version": "2.0",
                "task_id": task_dir.name,
                "locked": True,
                "created_at": "2026-09-26T00:00:00+09:00",
                "locked_at": "2026-09-26T00:00:00+09:00",
                "scenarios": [scenario],
            }
        ),
        encoding="utf-8",
    )


class _RunMixin:
    def _run(self, project_root: str, profile: str, surface_ref=None):
        with tempfile.TemporaryDirectory() as taskdir, tempfile.TemporaryDirectory() as artifact_root:
            task_dir = pathlib.Path(taskdir) / "task"
            _write_scenario(task_dir, profile, surface_ref)
            payload = e2e_orchestrator.run_e2e(
                target=e2e_target.TARGET_SOURCE_WORKTREE,
                scenario_id="S-1",
                task_path=str(task_dir),
                worktree_root=project_root,
                artifact_root=artifact_root,
            )
            run_dir = pathlib.Path(payload["run_json_path"]).parent
            run_json = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            owned = json.loads((run_dir / "owned.json").read_text(encoding="utf-8"))
            journal = json.loads((run_dir / "journal.json").read_text(encoding="utf-8"))
            server_logs = sorted(
                path.name for path in (run_dir / "server").glob("*.log")
            ) if (run_dir / "server").is_dir() else []
        return payload, run_json, owned, journal, server_logs

    def _assert_blocked_before_sut(self, payload, run_json, owned, journal, detail_code):
        self.assertEqual(payload["status"], "blocked", payload)
        self.assertEqual(payload["exit_code"], e2e_contract.status_to_exit("blocked"))
        self.assertEqual(payload["error"], e2e_contract.status_to_error("blocked"))
        self.assertEqual(run_json["detail_code"], detail_code, run_json)
        self.assertEqual(owned["process_groups"], [])
        states = [item["to"] for item in journal["transitions"]]
        self.assertNotIn(e2e_orchestrator.STATE_SUT_STARTING, states)


class TestRunConfigAbsentOrInvalid(_RunMixin, unittest.TestCase):
    """D-10 — 설정 부재·무효: 호환 역할 2건 임대, 기동 없이 blocked."""

    def test_missing_config_leases_compat_roles_and_blocks(self):
        with tempfile.TemporaryDirectory() as root:
            payload, run_json, owned, journal, _ = self._run(root, "api")
        self._assert_blocked_before_sut(payload, run_json, owned, journal, "e2e_env_config_missing")
        self.assertEqual(sorted(run_json["urls"]), ["backend", "frontend"])
        self.assertEqual(len(run_json["lease_released"]), 2)
        self.assertIn("env-inspect", run_json["detail"])
        self.assertIn("//e2e setup", run_json["detail"])

    def test_invalid_config_blocks_without_echoing_values(self):
        with tempfile.TemporaryDirectory() as root:
            _write_config(pathlib.Path(root), {"schema_version": "1.0", "surfaces": []})
            payload, run_json, owned, journal, _ = self._run(root, "api")
        self._assert_blocked_before_sut(payload, run_json, owned, journal, "e2e_env_config_invalid")
        self.assertEqual(len(run_json["lease_released"]), 2)
        self.assertIn("required_field_missing", run_json["detail"])
        self.assertIn("env-inspect", run_json["detail"])


class TestRunSurfaceSelectionFailure(_RunMixin, unittest.TestCase):
    """D-9 — 필요한 종류의 표면이 없거나 고를 수 없으면 서비스 기동 전에 blocked."""

    def _config_with_service(self, surfaces):
        return {
            "schema_version": "1.0",
            "services": [
                {"id": "api", "command": ["{python}", "server.py", "--port", "{port}"]},
            ],
            "surfaces": surfaces,
        }

    def test_missing_api_surface_blocks_and_starts_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            _write_config(
                pathlib.Path(root),
                self._config_with_service([{"id": "console", "kind": "web", "service": "api"}]),
            )
            payload, run_json, owned, journal, logs = self._run(root, "api")
        self._assert_blocked_before_sut(payload, run_json, owned, journal, "e2e_env_surface_missing")
        # 임대 역할은 설정 서비스 id다.
        self.assertEqual(sorted(run_json["urls"]), ["api"])
        # 서비스 로그(server/<id>.log)가 없다 = 서비스를 띄우지 않았다.
        self.assertNotIn("api.log", logs)

    def test_ambiguous_api_surface_blocks_unless_surface_ref_names_one(self):
        surfaces = [
            {"id": "alpha", "kind": "api", "service": "api"},
            {"id": "beta", "kind": "api", "url": "http://127.0.0.1:9"},
        ]
        with tempfile.TemporaryDirectory() as root:
            _write_config(pathlib.Path(root), self._config_with_service(surfaces))
            payload, run_json, owned, journal, logs = self._run(root, "api", surface_ref="gamma.health")
        self._assert_blocked_before_sut(payload, run_json, owned, journal, "e2e_env_surface_ambiguous")
        self.assertIn("alpha", run_json["detail"])
        # 서비스 로그(server/<id>.log)가 없다 = 서비스를 띄우지 않았다.
        self.assertNotIn("api.log", logs)


class TestRunStartsConfiguredServices(_RunMixin, unittest.TestCase):
    """D-9 — 임시 프로젝트의 설정 서비스를 임대 포트로 1회 기동하고 api 표면 값을 probe에 넘긴다."""

    def test_temp_project_service_is_leased_started_once_and_reclaimed(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = pathlib.Path(root)
            (root_path / "server.py").write_text(_SERVER_SOURCE, encoding="utf-8")
            _write_config(
                root_path,
                {
                    "schema_version": "1.0",
                    "services": [
                        {
                            "id": "api",
                            "command": ["{python}", "server.py", "--port", "{port}"],
                            "health": {"type": "http", "path": "/ready", "json_field": "status"},
                            "startup_timeout_s": 20,
                        }
                    ],
                    # 두 표면이 같은 서비스를 공유해도 서비스는 1회만 기동한다.
                    "surfaces": [
                        {"id": "svc-api", "kind": "api", "service": "api", "health_path": "/ready"},
                        {"id": "svc-web", "kind": "web", "service": "api", "path": "/"},
                    ],
                },
            )
            payload, run_json, owned, journal, logs = self._run(root, "api")

        self.assertNotEqual(run_json["detail_code"], "e2e_sut_startup_failed", run_json)
        self.assertNotIn(
            run_json["detail_code"],
            ("e2e_env_config_missing", "e2e_env_config_invalid",
             "e2e_env_surface_missing", "e2e_env_surface_ambiguous"),
        )
        states = [item["to"] for item in journal["transitions"]]
        self.assertIn(e2e_orchestrator.STATE_SUT_READY, states)
        # urls 키 = 설정 서비스 id, 임대 1건, 종료 시 해제.
        self.assertEqual(list(run_json["urls"]), ["api"])
        self.assertTrue(run_json["urls"]["api"].startswith("http://127.0.0.1:"))
        self.assertEqual(payload["urls"], run_json["urls"])
        self.assertEqual(len(run_json["lease_released"]), 1)
        # 서비스 1회 기동(프로세스 그룹 1건, 로그는 server/<id>.log) 후 누수 없이 회수.
        self.assertEqual([item["role"] for item in owned["process_groups"]], ["api"])
        self.assertEqual(logs, ["api.err.log", "api.log"])
        self.assertEqual(owned["leaked"], [])
        self.assertEqual(run_json["cleanup"], "complete")
        # api probe가 api 표면의 base URL + health_path(/ready)로 가용성을 확인했다.
        api_candidates = [c for c in run_json["candidates"] if c.get("type") == "api"]
        self.assertTrue(api_candidates, run_json["candidates"])
        self.assertEqual(api_candidates[0]["outcome"], "selected", api_candidates)
        for pgid in (item["pgid"] for item in owned["process_groups"]):
            self.assertEqual(e2e_process.process_group_members(pgid), [])


class TestRunRenderViolationStartsNothing(_RunMixin, unittest.TestCase):
    """GC-003 — 서비스 render 위반(path_escape)은 첫 기동 전에 걸려 아무 서비스도 띄우지 않는다."""

    def test_second_service_cwd_symlink_escape_blocks_before_any_start(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            root_path = pathlib.Path(root)
            (root_path / "server.py").write_text(_SERVER_SOURCE, encoding="utf-8")
            # 프로젝트 안 경로처럼 보이지만 실제로는 프로젝트 밖을 가리키는 symlink.
            (root_path / "escape").symlink_to(outside, target_is_directory=True)
            _write_config(
                root_path,
                {
                    "schema_version": "1.0",
                    "services": [
                        {
                            "id": "api",
                            "command": ["{python}", "server.py", "--port", "{port}"],
                            "health": {"type": "http", "path": "/ready", "json_field": "status"},
                            "startup_timeout_s": 20,
                        },
                        {
                            "id": "web",
                            "command": ["{python}", "server.py", "--port", "{port}"],
                            "cwd": "escape",
                            "depends_on": ["api"],
                            "health": {"type": "http", "path": "/ready", "json_field": "status"},
                            "startup_timeout_s": 20,
                        },
                    ],
                    "surfaces": [
                        {"id": "svc-api", "kind": "api", "service": "api", "health_path": "/ready"},
                        {"id": "svc-web", "kind": "web", "service": "web", "path": "/"},
                    ],
                },
            )
            payload, run_json, owned, journal, logs = self._run(root, "api")

        self.assertEqual(payload["status"], "blocked", payload)
        self.assertEqual(payload["exit_code"], e2e_contract.status_to_exit("blocked"))
        self.assertEqual(run_json["detail_code"], "e2e_env_config_invalid", run_json)
        # detail에는 위반 코드 이름만 있고 경로 원문은 없다.
        self.assertIn("path_escape", run_json["detail"])
        self.assertNotIn(outside, run_json["detail"])
        self.assertNotIn(root, run_json["detail"])
        # 첫 번째 서비스(api)도 기동하지 않았다.
        self.assertEqual(owned["process_groups"], [])
        self.assertNotIn("api.log", logs)
        states = [item["to"] for item in journal["transitions"]]
        self.assertNotIn(e2e_orchestrator.STATE_SUT_READY, states)
        # 서비스 2건의 임대가 모두 해제됐다.
        self.assertEqual(sorted(run_json["urls"]), ["api", "web"])
        self.assertEqual(len(run_json["lease_released"]), 2)


if __name__ == "__main__":
    unittest.main()
