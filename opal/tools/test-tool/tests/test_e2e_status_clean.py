"""
@header {
  "module": "test_e2e_status_clean",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "W-9 `test-tool e2e status`(§B.1.3)·`e2e clean`(§B.1.4) 검증 — 조회 명령의 stdout 필드와 exit 0, owned.json 대장에 오른 자원만 회수하고 user_owned=true를 skipped[]로 제외하는 경계(TD-15·C-2), 누출 잔존 시 cleanup 결과의 infra_error 승격(§A.6.1), 그리고 두 명령이 프로세스 이름 패턴 매칭·console PID 파일을 쓰지 않는다는 구조 제약(§C.1·C-9)을 고정한다.",
  "scenarios": ["S-2", "S-4"],
  "exports": ["TestE2eStatus", "TestE2eClean", "TestCleanBoundaryConstraints"]
}

lib/e2e_contract.py·lib/scenario.py는 소비만 한다(TASK.md C-1). 이 테스트는 SUT를
기동하지 않으며 저장소에 아무것도 쓰지 않는다(C-5) — 산출물은 전부 임시 디렉터리다.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_PYTHON = sys.executable

from lib import e2e_contract  # noqa: E402
from lib.e2e import orchestrator as e2e_orchestrator  # noqa: E402
from lib.e2e import ports as e2e_ports  # noqa: E402


def _write_run_dir(
    root: pathlib.Path,
    run_id: str,
    *,
    project_id: str = "proj",
    owned: dict | None = None,
    run_json: dict | None = None,
    transitions: list | None = None,
) -> pathlib.Path:
    """§A.1/§A.2/§A.3 산출물 3종을 갖춘 run 디렉터리를 만든다."""
    run_dir = root / project_id / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "schema_version": e2e_contract.E2E_CONTRACT_SCHEMA_VERSION,
                "run_id": run_id,
                "scenario_id": "S-2",
                "profile": "api",
                "target": "source-worktree",
                "state": "cleanup_complete",
                "status": "pass",
                "operational_status": None,
                "urls": {"frontend": "http://127.0.0.1:1", "backend": "http://127.0.0.1:2"},
                **(run_json or {}),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (run_dir / "journal.json").write_text(
        json.dumps(
            {
                "schema_version": e2e_contract.E2E_CONTRACT_SCHEMA_VERSION,
                "run_id": run_id,
                "transitions": transitions
                if transitions is not None
                else [{"from": None, "to": "created", "at": "2026-09-15T00:00:00Z"}],
                "resume": None,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (run_dir / "owned.json").write_text(
        json.dumps(
            {
                "schema_version": e2e_contract.E2E_CONTRACT_SCHEMA_VERSION,
                "run_id": run_id,
                "process_groups": [],
                "leases": [],
                "browser_pages": [],
                "browser_profiles": [],
                "cmux_surfaces": [],
                "api_fixtures": [],
                **(owned or {}),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return run_dir


class TestE2eStatus(unittest.TestCase):
    """§B.1.3 — 조회 명령. 아무것도 변경하지 않고 exit은 0이다."""

    def _status(self, args):
        env = os.environ.copy()
        env.pop("OPAL_E2E_ARTIFACT_DIR", None)
        return subprocess.run(
            [_PYTHON, str(_TEST_TOOL_PY), "e2e", "status"] + args,
            capture_output=True, text=True, env=env, timeout=60,
        )

    def test_status_returns_the_contract_b13_field_set_with_exit_zero(self):
        with tempfile.TemporaryDirectory() as root:
            run_dir = _write_run_dir(pathlib.Path(root), "e2e-20260915-101")
            proc = self._status(["--run-id", "e2e-20260915-101", "--artifact-root", root])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            for key in (
                "run_id", "scenario_id", "profile", "target", "state", "status",
                "operational_status", "urls", "artifact_dir", "journal_tail",
            ):
                self.assertIn(key, payload, f"§B.1.3 stdout missing {key}")
            self.assertEqual(payload["run_id"], "e2e-20260915-101")
            self.assertEqual(payload["artifact_dir"], str(run_dir))
            # 조회는 대상을 바꾸지 않는다.
            self.assertTrue((run_dir / "run.json").is_file())
            self.assertTrue((run_dir / "owned.json").is_file())

    def test_artifact_dir_addresses_a_run_without_a_run_id(self):
        with tempfile.TemporaryDirectory() as root:
            run_dir = _write_run_dir(pathlib.Path(root), "e2e-20260915-102")
            proc = self._status(["--artifact-dir", str(run_dir)])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)["run_id"], "e2e-20260915-102")

    def test_journal_tail_is_the_most_recent_transitions_only(self):
        with tempfile.TemporaryDirectory() as root:
            transitions = [
                {"from": None if i == 0 else str(i - 1), "to": str(i), "at": "2026-09-15T00:00:00Z"}
                for i in range(40)
            ]
            _write_run_dir(pathlib.Path(root), "e2e-20260915-103", transitions=transitions)
            proc = self._status(["--run-id", "e2e-20260915-103", "--artifact-root", root])
            tail = json.loads(proc.stdout)["journal_tail"]
            self.assertLessEqual(len(tail), len(transitions))
            self.assertEqual(tail[-1], transitions[-1], "tail must end at the latest transition")

    def test_unknown_run_is_run_not_found_without_a_new_exit_value(self):
        """§B.1.3 — 대상 부재는 기존 usage 오류 코드를 쓰고 새 exit 값을 만들지 않는다."""
        with tempfile.TemporaryDirectory() as root:
            proc = self._status(["--run-id", "e2e-20260915-999", "--artifact-root", root])
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["error"], e2e_orchestrator.ERROR_RUN_NOT_FOUND)
            self.assertNotIn(proc.returncode, set(e2e_contract.STATUS_EXIT_CODES.values()) - {6})
            self.assertNotEqual(proc.returncode, 0)

    def test_run_id_and_artifact_dir_are_mutually_exclusive_and_one_is_required(self):
        self.assertEqual(self._status([]).returncode, 2)
        proc = self._status(["--run-id", "x", "--artifact-dir", "/tmp"])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not allowed with argument", proc.stderr)


class TestE2eClean(unittest.TestCase):
    """§B.1.4 — owned.json 대장에 오른 자원만 회수하고 exit은 0이다."""

    def _clean(self, args):
        env = os.environ.copy()
        env.pop("OPAL_E2E_ARTIFACT_DIR", None)
        return subprocess.run(
            [_PYTHON, str(_TEST_TOOL_PY), "e2e", "clean"] + args,
            capture_output=True, text=True, env=env, timeout=60,
        )

    def test_clean_returns_the_contract_b14_field_set_with_exit_zero(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = pathlib.Path(root)
            lease_dir = e2e_ports.lease_dir_for(root)
            (lease_dir / "e2e-20260915-201-backend.json").write_text(
                json.dumps({"lease_id": "e2e-20260915-201-backend", "run_id": "e2e-20260915-201",
                            "owner_pid": os.getpid(), "port": 51000, "role": "backend",
                            "state": "confirmed"}),
                encoding="utf-8",
            )
            _write_run_dir(
                root_path, "e2e-20260915-201",
                owned={"leases": [{"lease_id": "e2e-20260915-201-backend", "port": 51000,
                                   "role": "backend"}]},
            )
            proc = self._clean(["--run-id", "e2e-20260915-201", "--artifact-root", root])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            for key in ("reclaimed_leases", "terminated_process_groups",
                        "removed_artifact_dirs", "skipped"):
                self.assertIn(key, payload, f"§B.1.4 stdout missing {key}")
            self.assertIn("e2e-20260915-201-backend", payload["reclaimed_leases"])
            self.assertFalse((lease_dir / "e2e-20260915-201-backend.json").exists())
            self.assertFalse((root_path / "proj" / "e2e-20260915-201").exists())

    def test_user_owned_resources_are_skipped_and_never_touched(self):
        """[MUST] TASK.md C-2·§A.3 — user_owned=true는 정리 대상에서 제외된다(R-8)."""
        with tempfile.TemporaryDirectory() as root:
            root_path = pathlib.Path(root)
            _write_run_dir(
                root_path, "e2e-20260915-202",
                owned={
                    "browser_pages": [
                        {"page_id": "user-tab", "driver": "cmux", "session_mode": "owned-surface",
                         "user_owned": True},
                        {"page_id": "run-page", "driver": "cmux", "session_mode": "owned-surface",
                         "user_owned": False},
                    ],
                    "cmux_surfaces": [{"surface_handle": "user-surface", "user_owned": True}],
                    "api_fixtures": [{"fixture_id": "user-data", "namespace": "n",
                                      "endpoint": "/x", "user_owned": True}],
                    # 사용자 Console daemon 포트는 애초에 임대되지 않지만(EXCLUDED_PORTS),
                    # 대장에 표시가 들어와도 회수하지 않는다.
                    "leases": [{"lease_id": "user-console", "port": 7823, "role": "backend",
                                "user_owned": True}],
                },
            )
            proc = self._clean(["--run-id", "e2e-20260915-202", "--artifact-root", root])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            skipped_ids = {item["id"] for item in payload["skipped"]}
            self.assertEqual(
                skipped_ids, {"user-tab", "user-surface", "user-data", "user-console"},
                f"user_owned 자원 전건이 skipped[]에 있어야 한다: {payload['skipped']}",
            )
            for item in payload["skipped"]:
                self.assertEqual(item["reason"], "user_owned")
            # 사용자 소유 lease는 회수 목록에 오르지 않는다.
            self.assertNotIn("user-console", payload["reclaimed_leases"])

    def test_clean_only_touches_what_the_owned_ledger_lists(self):
        """TD-15 — 대장에 없는 run은 같은 root 아래 있어도 건드리지 않는다."""
        with tempfile.TemporaryDirectory() as root:
            root_path = pathlib.Path(root)
            _write_run_dir(root_path, "e2e-20260915-203")
            bystander = _write_run_dir(root_path, "e2e-20260915-204")
            proc = self._clean(["--run-id", "e2e-20260915-203", "--artifact-root", root])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["removed_artifact_dirs"],
                             [str(root_path / "proj" / "e2e-20260915-203")])
            self.assertTrue(bystander.is_dir(), "대장에 없는 run을 지우면 안 된다")

    def test_dry_run_changes_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = pathlib.Path(root)
            run_dir = _write_run_dir(root_path, "e2e-20260915-205")
            proc = self._clean(["--run-id", "e2e-20260915-205", "--artifact-root", root,
                                "--dry-run"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(json.loads(proc.stdout)["dry_run"])
            self.assertTrue(run_dir.is_dir())

    def test_stale_reclaims_dead_owner_lease_records(self):
        """C-LEASE-2 — owner_pid가 살아 있지 않은 record가 대상이다."""
        with tempfile.TemporaryDirectory() as root:
            lease_dir = e2e_ports.lease_dir_for(root)
            dead_pid = 2 ** 22 + 7  # 실존하지 않는 pid
            (lease_dir / "dead.json").write_text(
                json.dumps({"lease_id": "dead", "run_id": "e2e-20260915-206",
                            "owner_pid": dead_pid, "port": 51001, "role": "backend",
                            "state": "reserved"}),
                encoding="utf-8",
            )
            (lease_dir / "alive.json").write_text(
                json.dumps({"lease_id": "alive", "run_id": "e2e-20260915-207",
                            "owner_pid": os.getpid(), "port": 51002, "role": "backend",
                            "state": "confirmed"}),
                encoding="utf-8",
            )
            proc = self._clean(["--stale", "--artifact-root", root])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertIn("dead", payload["reclaimed_leases"])
            self.assertNotIn("alive", payload["reclaimed_leases"])
            self.assertTrue((lease_dir / "alive.json").exists(),
                            "살아 있는 소유자의 lease는 회수 대상이 아니다")

    def test_leaked_process_group_escalates_the_cleanup_result_to_infra_error(self):
        """§A.6.1 — 회수 후에도 남은 프로세스 그룹은 정리 성공으로 기록할 수 없다."""
        original = e2e_orchestrator.e2e_process.terminate_process_group
        original_alive = e2e_orchestrator.e2e_process.pid_alive
        e2e_orchestrator.e2e_process.pid_alive = lambda pid: True
        e2e_orchestrator.e2e_process.terminate_process_group = (
            lambda pgid, **kwargs: e2e_orchestrator.e2e_process.TerminationResult(
                released=False, method="sigkill", leaked=[pgid, pgid + 1]
            )
        )
        try:
            with tempfile.TemporaryDirectory() as root:
                root_path = pathlib.Path(root)
                run_dir = _write_run_dir(
                    root_path, "e2e-20260915-208",
                    owned={"process_groups": [{"pgid": 987654, "role": "backend",
                                               "started_at": "2026-09-15T00:00:00Z"}]},
                )
                payload = e2e_orchestrator.run_clean(
                    run_id="e2e-20260915-208", artifact_root=root
                )
                self.assertTrue(payload["escalated_to_infra_error"])
                self.assertEqual(payload["status"], "infra_error")
                self.assertEqual(
                    payload["error"], e2e_contract.status_to_error("infra_error")
                )
                self.assertTrue(payload["leaked"])
                # 누출이 남은 run의 증적은 지우지 않는다 — 원인을 남긴다.
                self.assertTrue(run_dir.is_dir())
                self.assertEqual(payload["removed_artifact_dirs"], [])
        finally:
            e2e_orchestrator.e2e_process.terminate_process_group = original
            e2e_orchestrator.e2e_process.pid_alive = original_alive

    def test_run_id_and_stale_are_mutually_exclusive_and_one_is_required(self):
        self.assertEqual(self._clean([]).returncode, 2)
        proc = self._clean(["--run-id", "x", "--stale"])
        self.assertEqual(proc.returncode, 2)


class TestCleanBoundaryConstraints(unittest.TestCase):
    """§C.1·TASK.md C-9 — 패턴 매칭 금지와 opal-cli 무의존의 구조 제약."""

    def test_no_process_name_pattern_matching_anywhere_in_the_harness(self):
        forbidden = re.compile(r"\b(?:" + "|".join(["p" + "kill", "p" + "grep", "kill" + "all"]) + r")\b")
        sources = list((_TOOL_DIR / "lib" / "e2e").rglob("*.py")) + [_TEST_TOOL_PY]
        for path in sources:
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(
                forbidden.search(text),
                f"{path.name} must not match processes by name (CONTRACT.md §C.1)",
            )

    def test_clean_never_reads_the_opal_cli_console_pid_file(self):
        """[MUST] §B.1.4 — clean은 $OPAL_HOME/run/console.pid를 보지 않는다."""
        sources = list((_TOOL_DIR / "lib" / "e2e").rglob("*.py")) + [_TEST_TOOL_PY]
        for path in sources:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("console.pid", text, f"{path.name} must not read the console PID file")

    def test_console_daemon_port_stays_out_of_the_lease_pool(self):
        """TASK.md C-2 — 사용자 Console daemon 포트는 임대 후보에서 제외된다."""
        self.assertEqual(e2e_ports.EXCLUDED_PORTS, (7823,))


if __name__ == "__main__":
    unittest.main()
