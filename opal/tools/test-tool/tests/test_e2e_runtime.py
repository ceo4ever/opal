"""
@header {
  "module": "test_e2e_runtime",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "W-1 Runtime Manager 단위 검증 — target.py의 3종 target 해석·commit/dirty 수집·installed 거부 규칙(TD-9·§C.5), ports.py allocator의 lease record·O_EXCL lock·stale 회수(§A.7·C-LEASE-1/2)·사용자 포트 제외(C-2), orchestrator의 run.json 필수 키·상태 머신·exit=status_to_exit 및 `e2e run` 서브파서가 기존 4개 서브파서를 건드리지 않았음을 고정한다.",
  "scenarios": ["S-1", "S-2", "S-3", "S-4"],
  "exports": ["TestTargetResolution", "TestPortAllocator", "TestOrchestratorRunJson", "TestCliSubparserBoundary"]
}

lib/e2e 골격(process.py·runtime.py)과 lib/e2e_contract.py는 소비만 한다(PLAN.md D-11,
TASK.md C-1). 이 테스트는 SUT를 기동하지 않으며 저장소에 아무것도 쓰지 않는다(C-5).
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_SOURCE_ROOT = _TOOL_DIR.parent.parent.parent
_TASK_PATH = _SOURCE_ROOT / "tasks" / "127-260912-oppl-E2E-하네스-구현"
_PYTHON = sys.executable

from lib import e2e_contract  # noqa: E402
from lib.e2e import drivers as e2e_drivers  # noqa: E402
from lib.e2e import orchestrator as e2e_orchestrator  # noqa: E402
from lib.e2e import ports as e2e_ports  # noqa: E402
from lib.e2e import target as e2e_target  # noqa: E402


class TestTargetResolution(unittest.TestCase):
    """target.py — 3종 enum + 경로 직접 지정, commit·dirty 수집, installed 거부 규칙."""

    def test_source_worktree_collects_head_commit_and_dirty_state(self):
        context = e2e_target.resolve_target(
            e2e_target.TARGET_SOURCE_WORKTREE, worktree_root=str(_SOURCE_ROOT)
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=_SOURCE_ROOT, capture_output=True, text=True
        ).stdout.strip()
        self.assertEqual(context.target, e2e_target.TARGET_SOURCE_WORKTREE)
        self.assertEqual(context.commit, head)
        self.assertEqual(len(context.commit), 40)
        self.assertIsNotNone(context.worktree_root)
        self.assertIsInstance(context.dirty, bool)
        self.assertIsInstance(context.dirty_files, list)
        self.assertEqual(context.dirty, bool(context.dirty_files))

    def test_explicit_worktree_root_wins_over_cwd_discovery(self):
        """S-1의 핵심 — 동시에 도는 run이 각자 자기 트리를 가리켜야 한다(AC-1·AC-2).

        cwd는 실제 저장소 안이지만, 명시된 --worktree-root가 우선해야 한다.
        """
        with tempfile.TemporaryDirectory() as other_tree:
            context = e2e_target.resolve_target(
                e2e_target.TARGET_SOURCE_WORKTREE, worktree_root=other_tree
            )
            self.assertEqual(context.project_root, os.path.abspath(other_tree))
            self.assertEqual(context.worktree_root, os.path.abspath(other_tree))
            # 저장소가 아닌 트리도 입력 오류가 아니라 빈 commit으로 해석된다.
            self.assertEqual(context.commit, "")
            self.assertEqual(context.dirty_files, [])

    def test_target_outside_the_three_enum_values_is_rejected(self):
        """CONTRACT.md §B.1.1 — --target은 3종 enum이다. 경로 문자열은 받지 않는다."""
        with tempfile.TemporaryDirectory() as plain_dir:
            for bad in ("source-somewhere-else", plain_dir):
                with self.assertRaises(e2e_target.TargetResolutionError) as caught:
                    e2e_target.resolve_target(bad)
                self.assertEqual(caught.exception.detail_code, "e2e_target_invalid")

    def test_installed_requires_opal_home_and_never_runs_install(self):
        """TD-9 — installed는 --opal-home 입력만 받고 install을 호출하지 않는다."""
        with self.assertRaises(e2e_target.TargetResolutionError) as caught:
            e2e_target.resolve_target(e2e_target.TARGET_INSTALLED)
        self.assertEqual(caught.exception.detail_code, "e2e_opal_home_required")

    def test_installed_rejects_unprepared_opal_home(self):
        with tempfile.TemporaryDirectory() as fake_home:
            with self.assertRaises(e2e_target.TargetResolutionError) as caught:
                e2e_target.resolve_target(
                    e2e_target.TARGET_INSTALLED, opal_home=fake_home
                )
            self.assertEqual(caught.exception.detail_code, "e2e_opal_home_unprepared")

    def test_installed_rejects_the_users_own_opal_home(self):
        """CONTRACT.md §C.5 — 사용자 실제 ~/.opal은 대상이 될 수 없다(TASK.md C-2)."""
        with self.assertRaises(e2e_target.TargetResolutionError) as caught:
            e2e_target.resolve_target(
                e2e_target.TARGET_INSTALLED, opal_home=str(pathlib.Path.home() / ".opal")
            )
        self.assertEqual(caught.exception.detail_code, "e2e_opal_home_is_user_owned")

    def test_prepared_isolated_opal_home_is_accepted(self):
        with tempfile.TemporaryDirectory() as fake_home:
            for name in ("tools", "references"):
                (pathlib.Path(fake_home) / name).mkdir()
            context = e2e_target.resolve_target(
                e2e_target.TARGET_INSTALLED, opal_home=fake_home
            )
            self.assertEqual(context.target, e2e_target.TARGET_INSTALLED)
            self.assertEqual(context.opal_home, os.path.realpath(fake_home))


class TestPortAllocator(unittest.TestCase):
    """ports.py — find_free_port를 치환하지 않고 그 곁에 붙은 allocator 계약(§A.7)."""

    def test_find_free_port_is_still_the_t01_entry_point(self):
        """PLAN.md W-1 — 기존 find_free_port를 치환하지 않는다."""
        port = e2e_ports.find_free_port()
        self.assertTrue(1024 <= port <= 65535)
        self.assertEqual(e2e_ports.MAX_PORT_ATTEMPTS, 5)

    def test_lease_writes_contract_shaped_records(self):
        with tempfile.TemporaryDirectory() as root:
            leases, reclaimed = e2e_ports.lease_ports(
                artifact_root=root, run_id="e2e-20260914-001", roles=("backend", "frontend")
            )
            self.assertEqual(reclaimed, [])
            self.assertEqual([rec.role for rec in leases], ["backend", "frontend"])
            self.assertNotEqual(leases[0].port, leases[1].port)
            for record in leases:
                path = pathlib.Path(root) / ".leases" / f"{record.lease_id}.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    sorted(data),
                    sorted(
                        [
                            "schema_version",
                            "lease_id",
                            "run_id",
                            "owner_pid",
                            "port",
                            "role",
                            "state",
                            "created_at",
                            "confirmed_at",
                            "attempt",
                        ]
                    ),
                )
                self.assertEqual(data["schema_version"], e2e_contract.E2E_CONTRACT_SCHEMA_VERSION)
                self.assertEqual(data["owner_pid"], os.getpid())
                self.assertEqual(data["state"], "reserved")
                self.assertEqual(data["attempt"], 1)
                self.assertEqual(data["lease_id"], f"e2e-20260914-001-{data['role']}")

    def test_live_lease_ports_are_not_handed_out_twice(self):
        """S-1의 핵심 — 살아 있는 lease가 점유한 포트는 다음 임대 후보에서 제외된다."""
        with tempfile.TemporaryDirectory() as root:
            first, _ = e2e_ports.lease_ports(
                artifact_root=root, run_id="e2e-20260914-001", roles=("backend",)
            )
            second, _ = e2e_ports.lease_ports(
                artifact_root=root, run_id="e2e-20260914-002", roles=("backend",)
            )
            self.assertNotEqual(first[0].port, second[0].port)

    def test_stale_lease_with_dead_owner_pid_is_reclaimed(self):
        """계약 규칙 C-LEASE-2 — owner_pid가 죽은 reserved record는 다음 실행이 회수한다."""
        with tempfile.TemporaryDirectory() as root:
            lease_dir = e2e_ports.lease_dir_for(root)
            dead = subprocess.Popen([sys.executable, "-c", "pass"])
            dead.wait()
            (lease_dir / "stale-run-backend.json").write_text(
                json.dumps(
                    {
                        "schema_version": e2e_contract.E2E_CONTRACT_SCHEMA_VERSION,
                        "lease_id": "stale-run-backend",
                        "run_id": "stale-run",
                        "owner_pid": dead.pid,
                        "port": 18765,
                        "role": "backend",
                        "state": "reserved",
                        "created_at": "2020-01-01T00:00:00Z",
                        "confirmed_at": None,
                        "attempt": 1,
                    }
                ),
                encoding="utf-8",
            )
            _, reclaimed = e2e_ports.lease_ports(
                artifact_root=root, run_id="e2e-20260914-003", roles=("backend",)
            )
            self.assertEqual(reclaimed, ["stale-run-backend"])
            self.assertFalse((lease_dir / "stale-run-backend.json").exists())

    def test_live_lease_of_another_process_is_not_reclaimed(self):
        """회수는 죽은 owner에 한정된다 — 살아 있는 run의 lease를 빼앗지 않는다."""
        with tempfile.TemporaryDirectory() as root:
            lease_dir = e2e_ports.lease_dir_for(root)
            (lease_dir / "live-run-backend.json").write_text(
                json.dumps(
                    {
                        "schema_version": e2e_contract.E2E_CONTRACT_SCHEMA_VERSION,
                        "lease_id": "live-run-backend",
                        "run_id": "live-run",
                        "owner_pid": os.getpid(),
                        "port": 18766,
                        "role": "backend",
                        "state": "reserved",
                        "created_at": "2020-01-01T00:00:00Z",
                        "confirmed_at": None,
                        "attempt": 1,
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(e2e_ports.reclaim_stale_leases(lease_dir), [])
            self.assertTrue((lease_dir / "live-run-backend.json").exists())

    def test_allocator_lock_is_exclusive_and_released(self):
        """계약 규칙 C-LEASE-1 — O_CREAT|O_EXCL 취득, 블록 종료 시 해제."""
        with tempfile.TemporaryDirectory() as root:
            lease_dir = e2e_ports.lease_dir_for(root)
            with e2e_ports.allocator_lock(lease_dir):
                self.assertTrue((lease_dir / ".lock").exists())
                with self.assertRaises(e2e_ports.PortLeaseError):
                    with e2e_ports.allocator_lock(lease_dir, timeout_s=0.1):
                        pass
            self.assertFalse((lease_dir / ".lock").exists())

    def test_allocator_lock_does_not_use_fcntl_flock(self):
        """계약 규칙 C-LEASE-1 — fcntl.flock은 금지된다(플랫폼 분기를 낳음)."""
        source = (_TOOL_DIR / "lib" / "e2e" / "ports.py").read_text(encoding="utf-8")
        # 산문에서 금지 사실을 언급하는 것과 실제로 쓰는 것을 구분한다 — 실행 코드에
        # fcntl이 들어오지 않았는지를 본다.
        self.assertNotIn("import fcntl", source)
        self.assertNotIn("fcntl.flock(", source)
        self.assertIn("O_EXCL", source)

    def test_user_owned_console_port_is_excluded(self):
        """TASK.md C-2 — 127.0.0.1:7823 Console daemon 포트는 임대 후보가 아니다."""
        self.assertIn(7823, e2e_ports.EXCLUDED_PORTS)

    def test_release_removes_only_own_records(self):
        with tempfile.TemporaryDirectory() as root:
            leases, _ = e2e_ports.lease_ports(
                artifact_root=root, run_id="e2e-20260914-004", roles=("backend", "frontend")
            )
            other = e2e_ports.lease_dir_for(root) / "someone-else.json"
            other.write_text(json.dumps({"lease_id": "someone-else"}), encoding="utf-8")
            released = e2e_ports.release_leases(root, leases)
            self.assertEqual(
                released, ["e2e-20260914-004-backend", "e2e-20260914-004-frontend"]
            )
            self.assertTrue(other.exists())


class TestOrchestratorRunJson(unittest.TestCase):
    """orchestrator.py — 상태 머신·산출물·exit 결정 경로."""

    def _run(self, **kwargs):
        kwargs.setdefault("scenario_id", "S-1")
        kwargs.setdefault("task_path", str(_TASK_PATH))
        with tempfile.TemporaryDirectory() as artifact_dir:
            os.environ["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir
            try:
                payload = e2e_orchestrator.run_e2e(**kwargs)
                run_json = json.loads(
                    (pathlib.Path(artifact_dir) / "run.json").read_text(encoding="utf-8")
                )
                journal = json.loads(
                    (pathlib.Path(artifact_dir) / "journal.json").read_text(encoding="utf-8")
                )
                owned = json.loads(
                    (pathlib.Path(artifact_dir) / "owned.json").read_text(encoding="utf-8")
                )
            finally:
                os.environ.pop("OPAL_E2E_ARTIFACT_DIR", None)
        return payload, run_json, journal, owned

    def test_zero_executor_candidates_ends_before_the_sut_is_started(self):
        """§A.1.2 [MUST] — selected가 0개이면 status는 executor_unavailable이다.

        판정이 기동 전에 확정되므로 아무도 구동하지 않을 uvicorn·vite를 띄우지 않는다
        (TASK.md C-4·C-5).

        재현 대상은 **SUT probe가 필요 없는 profile**이다. `api` executor의 probe는 실제
        SUT `/health`를 호출해야 가용성을 확정하므로(§A.8 [MUST], NR-7) `api` profile은
        원리상 기동 전에 판정할 수 없다 — 그 경로까지 이 단축으로 묶으면 probe 없이
        가용성을 추정하게 된다. `browser` profile은 driver binary 해석만으로 판정되므로
        단축이 성립하며, 여기서는 driver 레지스트리를 비워 후보 전건을 미가용으로 만든다.
        """
        original_registry = e2e_drivers.registered_drivers
        e2e_drivers.registered_drivers = lambda: {}
        try:
            with tempfile.TemporaryDirectory() as other_tree:
                payload, run_json, journal, owned = self._run(
                    target=e2e_target.TARGET_SOURCE_WORKTREE,
                    worktree_root=other_tree,
                    scenario_id="S-8",  # profile=browser — SUT probe가 필요 없다.
                )
        finally:
            e2e_drivers.registered_drivers = original_registry
        self.assertEqual(payload["status"], "executor_unavailable")
        # 상태·exit·error는 e2e_contract가 소유한 값 그대로여야 한다(C-125-1).
        self.assertIn(payload["status"], e2e_contract.FINAL_STATUSES)
        self.assertEqual(payload["exit_code"], e2e_contract.status_to_exit(payload["status"]))
        self.assertEqual(payload["error"], e2e_contract.status_to_error(payload["status"]))
        self.assertEqual(owned["process_groups"], [])
        # 후보 전건이 미가용이고 selected는 0개다 — 이것이 단축의 전제다.
        self.assertTrue(run_json["candidates"], "후보 기록 자체가 비면 판정 근거가 없다")
        self.assertEqual(
            {c["outcome"] for c in run_json["candidates"]}, {"provider_unavailable"}
        )
        self.assertEqual(
            [c for c in run_json["candidates"] if c["outcome"] == "selected"], []
        )
        # 포트는 임대됐고 종료 시 해제됐다.
        self.assertTrue(run_json["urls"]["backend"].startswith("http://127.0.0.1:"))
        self.assertTrue(run_json["urls"]["frontend"].startswith("http://127.0.0.1:"))
        self.assertEqual(len(run_json["lease_released"]), 2)
        states = [item["to"] for item in journal["transitions"]]
        self.assertEqual(states[0], e2e_orchestrator.STATE_CREATED)
        self.assertIsNone(journal["transitions"][0]["from"])
        self.assertIn(e2e_orchestrator.STATE_CONTEXT_RESOLVED, states)
        self.assertIn(e2e_orchestrator.STATE_PORTS_LEASED, states)
        self.assertIn(e2e_orchestrator.STATE_PROFILE_RESOLVED, states)
        self.assertNotIn(e2e_orchestrator.STATE_SUT_STARTING, states)
        self.assertEqual(states[-1], e2e_orchestrator.STATE_CLEANUP_COMPLETE)

    def test_each_concurrent_worktree_run_points_at_its_own_tree(self):
        """AC-1·AC-2 — 명시된 --worktree-root가 cwd/git 탐색을 이긴다(S-1의 실패 사유)."""
        with tempfile.TemporaryDirectory() as tree_a, tempfile.TemporaryDirectory() as tree_b:
            payload_a, run_a, _, _ = self._run(
                target=e2e_target.TARGET_SOURCE_WORKTREE, worktree_root=tree_a
            )
            payload_b, run_b, _, _ = self._run(
                target=e2e_target.TARGET_SOURCE_WORKTREE, worktree_root=tree_b
            )
            self.assertEqual(payload_a["project_root"], os.path.abspath(tree_a))
            self.assertEqual(payload_b["project_root"], os.path.abspath(tree_b))
            self.assertEqual(run_a["worktree_root"], os.path.abspath(tree_a))
            self.assertEqual(run_b["worktree_root"], os.path.abspath(tree_b))

    def test_run_json_carries_every_contract_a1_required_key(self):
        _, run_json, _, _ = self._run(
            target=e2e_target.TARGET_SOURCE_WORKTREE, worktree_root=str(_SOURCE_ROOT)
        )
        for key in (
            "schema_version", "run_id", "scenario_id", "profile", "actors", "surface_kind",
            "target", "project_root", "worktree_root", "opal_home", "commit", "dirty",
            "dirty_files", "urls", "executors", "candidates", "state", "status",
            "operational_status", "error", "exit_code", "assertion_summary",
            "required_evidence", "observed_evidence", "missing_evidence",
            "evidence_complete", "fidelity", "cleanup", "artifact_dir", "started_at",
            "ended_at", "driver_version",
        ):
            self.assertIn(key, run_json, f"run.json missing CONTRACT §A.1 key: {key}")
        self.assertEqual(run_json["schema_version"], e2e_contract.E2E_CONTRACT_SCHEMA_VERSION)
        self.assertEqual(run_json["target"], e2e_target.TARGET_SOURCE_WORKTREE)
        self.assertIsNone(run_json["opal_home"])
        self.assertEqual(run_json["scenario_id"], "S-1")
        self.assertEqual(run_json["profile"], "api")
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=_SOURCE_ROOT, capture_output=True, text=True
        ).stdout.strip()
        self.assertEqual(run_json["commit"], head)

    def test_stdout_payload_is_the_contract_b11_set_plus_only_what_red_consumes(self):
        """§B.1.1 stdout 필드 + 동결 RED가 stdout에서 읽는 5개. 그 밖의 superset은 없다.

        `executed`는 S-12(b)가 stdout에서 직접 읽는다 — "실행 전 정적 거부"와 "실행 중
        실패"를 구분하는 값이므로 경로마다 모양이 달라지지 않게 모든 run이 싣는다.
        """
        payload, _, _, _ = self._run(
            target=e2e_target.TARGET_SOURCE_WORKTREE, worktree_root=str(_SOURCE_ROOT)
        )
        self.assertEqual(
            sorted(payload),
            sorted([
                "run_id", "scenario_id", "profile", "status", "operational_status",
                "error", "exit_code", "run_json_path", "artifact_dir",
                "urls", "project_root", "lease_reclaimed", "candidates", "executed",
            ]),
        )

    def test_unreadable_scenario_blocks_without_leasing_a_sut(self):
        with tempfile.TemporaryDirectory() as empty_task:
            payload, _, _, owned = self._run(
                target=e2e_target.TARGET_SOURCE_WORKTREE,
                worktree_root=str(_SOURCE_ROOT),
                scenario_id="S-1",
                task_path=empty_task,
            )
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["exit_code"], e2e_contract.status_to_exit("blocked"))
        self.assertEqual(owned["process_groups"], [])

    def test_target_resolution_failure_blocks_before_any_port_is_leased(self):
        payload, run_json, _, owned = self._run(target=e2e_target.TARGET_INSTALLED)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(owned["leases"], [])
        self.assertEqual(run_json["urls"], {"frontend": None, "backend": None})
        self.assertEqual(run_json["detail_code"], "e2e_opal_home_required")

    def test_run_id_matches_contract_a0_format(self):
        payload, _, _, _ = self._run(
            target=e2e_target.TARGET_SOURCE_WORKTREE, worktree_root=str(_SOURCE_ROOT)
        )
        self.assertRegex(payload["run_id"], e2e_orchestrator.RUN_ID_PATTERN)

    def test_orchestrator_declares_no_pattern_based_process_kill(self):
        """TASK.md C-9 / CONTRACT.md §C.1 — pkill·pgrep·killall 0건."""
        for name in ("orchestrator.py", "ports.py", "target.py"):
            source = (_TOOL_DIR / "lib" / "e2e" / name).read_text(encoding="utf-8")
            for forbidden in ("pkill", "pgrep", "killall"):
                self.assertNotIn(forbidden, source, f"{name} must not use {forbidden}")


class TestCliSubparserBoundary(unittest.TestCase):
    """test_tool.py — §B.1.1 시그니처 집행 + 기존 4개 서브파서 무변경(PLAN.md H-3)."""

    def _e2e_run(self, args, env_extra=None):
        env = os.environ.copy()
        env.update(env_extra or {})
        return subprocess.run(
            [_PYTHON, str(_TEST_TOOL_PY), "e2e", "run"] + args,
            capture_output=True, text=True, env=env, timeout=60,
        )

    def test_missing_required_arguments_are_rejected_by_argparse(self):
        """§B.1.1 — --scenario·--task-path·--target은 필수다. 우회 경로를 두지 않는다."""
        for args in (
            [],
            ["--target", "source-worktree"],
            ["--scenario", "S-1", "--target", "source-worktree"],
            ["--scenario", "S-1", "--task-path", str(_TASK_PATH)],
        ):
            proc = self._e2e_run(args)
            self.assertEqual(proc.returncode, 2, f"must be a usage error: {args}")
            self.assertIn("the following arguments are required", proc.stderr)

    def test_target_outside_the_enum_is_a_usage_error(self):
        proc = self._e2e_run(
            ["--scenario", "S-1", "--task-path", str(_TASK_PATH), "--target", "/tmp"]
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("invalid choice", proc.stderr)

    def test_complete_invocation_exits_with_a_contract_exit_code(self):
        with tempfile.TemporaryDirectory() as artifact_dir:
            proc = self._e2e_run(
                ["--scenario", "S-1", "--task-path", str(_TASK_PATH),
                 "--target", "source-worktree", "--worktree-root", str(_SOURCE_ROOT)],
                {"OPAL_E2E_ARTIFACT_DIR": artifact_dir},
            )
            self.assertNotEqual(proc.returncode, 2, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertIn(proc.returncode, set(e2e_contract.STATUS_EXIT_CODES.values()))
            self.assertEqual(proc.returncode, payload["exit_code"])
            self.assertEqual(
                proc.returncode, e2e_contract.status_to_exit(payload["status"])
            )

    def test_existing_four_subcommands_keep_their_argument_contract(self):
        proc = subprocess.run(
            [_PYTHON, str(_TEST_TOOL_PY), "--help"], capture_output=True, text=True, timeout=60
        )
        self.assertEqual(proc.returncode, 0)
        for name in ("resolve", "check", "unit", "integration", "e2e"):
            self.assertIn(name, proc.stdout)

    def test_e2e_requires_a_nested_subcommand(self):
        proc = subprocess.run(
            [_PYTHON, str(_TEST_TOOL_PY), "e2e"], capture_output=True, text=True, timeout=60
        )
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
