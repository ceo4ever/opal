"""
@header {
  "module": "test_e2e_human_executor",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "T10 — Human handoff executor 계약. §A.9 handoff 8필드 전건 발행과 server_policy 발행 시점 enum 정규화(MV-17, 선언 원문·정규화 사실 병기), awaiting_human(exit 20)과 §A.2.3 journal resume 보존, §B.1.2 `test-tool e2e resume` 시그니처와 동일 run-id·resume token 재개, 사람 제출만으로 pass 불가(R-13), timeout은 fail이 아니라 blocked(C-HUM-2), 재개 판정이 scenario.py:482-528 기존 경로로만 내려가는지(TD-18)를 검증한다.",
  "scenarios": ["S-11", "S-28"],
  "exports": [
    "TestHandoffContract", "TestResumeState", "TestServerPolicyNormalization",
    "TestAwaitingHumanPause", "TestResumeUsesTheExistingScenarioPath", "TestResumeCli",
    "TestTimeoutIsBlocked", "TestScenarioModuleUnchanged"
  ]
}

이 스위트는 W-8 산출물(`lib/e2e/executors/human.py` + `test_tool.py`의 `e2e resume`
라우팅)의 **공개 인터페이스**만 검사한다 — CLI exit, stdout JSON, 그리고 증적 관문이
디스크에 남긴 파일이다.

동결 자산 보호: 실제 태스크의 `test-scenario.json`은 읽기만 하고, 재개가 result존을
기록하는 대상은 임시 디렉터리로 복사한 사본이다. 원본은 어떤 테스트도 쓰지 않는다.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

from lib import e2e_contract  # noqa: E402
from lib import scenario as scenario_module  # noqa: E402
from lib.e2e import evidence as e2e_evidence  # noqa: E402
from lib.e2e import executors as e2e_executors  # noqa: E402
from lib.e2e.executors import human as e2e_human  # noqa: E402

_PYTHON = sys.executable
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_TASK_PATH = (
    _TOOL_DIR.parent.parent.parent / "tasks" / "127-260912-oppl-E2E-하네스-구현"
)
_RUN_ID = "e2e-20260914-100"


def _frozen_scenario(scenario_id):
    """동결 시나리오 1건을 **읽기만** 해서 돌려준다."""
    spec = json.loads((_TASK_PATH / "test-scenario.json").read_text(encoding="utf-8"))
    for item in spec["scenarios"]:
        if item["id"] == scenario_id:
            return spec, item
    raise AssertionError(f"{scenario_id} not in the frozen spec")


def _temp_task(scenario_id):
    """동결 spec에서 시나리오 1건만 뽑아 임시 태스크 폴더를 만든다(원본은 쓰지 않는다)."""
    spec, scenario = _frozen_scenario(scenario_id)
    tmp = tempfile.mkdtemp()
    copy = dict(spec, scenarios=[dict(scenario)])
    (pathlib.Path(tmp) / "test-scenario.json").write_text(
        json.dumps(copy, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return tmp, dict(scenario)


class _HandoffFixture:
    """artifact 디렉터리 + 증적 관문 + handoff를 발행한 human executor 한 벌."""

    def __init__(self, scenario_id="S-11", run_id=_RUN_ID, timeout_seconds=None):
        self.task_path, self.scenario = _temp_task(scenario_id)
        self.artifact_dir = tempfile.mkdtemp()
        self.writer = e2e_evidence.EvidenceWriter(self.artifact_dir, run_id)
        self.run_id = run_id
        spec = dict(self.scenario.get("handoff") or {})
        if timeout_seconds is not None:
            spec["timeout_seconds"] = timeout_seconds
        self.executor = e2e_human.HumanExecutor(
            runtime_context={"artifact_dir": self.artifact_dir, "task_path": self.task_path},
            writer=self.writer,
        )
        self.handoff = self.executor.dispatch(
            "handoff",
            {
                "run_id": run_id,
                "scenario_id": self.scenario["id"],
                "step_id": "handoff",
                "handoff_spec": spec,
            },
        )

    def mark_awaiting(self):
        return e2e_human.mark_awaiting_human(
            task_path=self.task_path,
            scenario_id=self.scenario["id"],
            run_id=self.run_id,
            handoff=self.handoff,
            verdict_path=str(pathlib.Path(self.artifact_dir) / "verdict.json"),
        )

    def submission(self, **overrides):
        """§A.10 제출물. 기본값은 검증을 통과할 수 있는 완전한 형태다."""
        payload = {
            "run_id": self.run_id,
            "resume_token": self.handoff["resume_token"],
            "handoff_id": self.handoff["handoff_id"],
            "completed": True,
            "observations": {"final_url": "http://127.0.0.1:0/"},
            "evidence_paths": {"final_url": f"{self.artifact_dir}/run.json"},
            "submitted_at": "2026-09-14T12:00:00Z",
            "observed_executors": ["human"],
            "assertion_results": [
                {
                    "id": f"{self.scenario['id']}-a1",
                    "verifier": "human",
                    "executor": "human",
                    "expected": self.scenario["assertions"][0]["expected"],
                    "actual": self.scenario["assertions"][0]["expected"],
                    "passed": True,
                }
            ],
            "observed_evidence": list(self.scenario["required_evidence"]),
            "fidelity": "real-usage",
        }
        payload.update(overrides)
        path = pathlib.Path(self.artifact_dir) / "human" / "submission.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return str(path)


# ─── §A.9 handoff ────────────────────────────────────────────────────────────
class TestHandoffContract(unittest.TestCase):
    """§A.9 / C-HUM-1 [MUST] — 8필드 전건이 아니면 handoff를 발행하지 않는다."""

    def test_required_field_list_is_owned_by_the_contract_module(self):
        self.assertEqual(len(e2e_contract.HANDOFF_REQUIRED_FIELDS), 8)
        source = (_TOOL_DIR / "lib" / "e2e" / "executors" / "human.py").read_text(encoding="utf-8")
        for field in e2e_contract.HANDOFF_REQUIRED_FIELDS:
            with self.subTest(field=field):
                self.assertNotIn(f'"{field}",', source, "필수 필드 목록을 복제하지 않는다")

    def test_handoff_carries_all_eight_required_fields_plus_the_identity_fields(self):
        fixture = _HandoffFixture()
        for field in e2e_contract.HANDOFF_REQUIRED_FIELDS:
            with self.subTest(field=field):
                self.assertNotIn(fixture.handoff.get(field), (None, "", [], {}))
        for field in ("actor", "run_id", "step_id", "issued_at"):
            self.assertIn(field, fixture.handoff)
        self.assertEqual(fixture.handoff["actor"], "human")
        self.assertEqual(fixture.handoff["run_id"], _RUN_ID)

    def test_an_incomplete_handoff_spec_is_refused(self):
        for missing in e2e_contract.HANDOFF_REQUIRED_FIELDS:
            spec = {
                "handoff_id": "HO-1", "instruction": "do", "expected_observation": "seen",
                "required_evidence": ["metadata"], "timeout_seconds": 60,
                "resume_token": "RT-1", "server_policy": "keep",
                "submission_path": "/tmp/s.json",
            }
            spec.pop(missing)
            with self.subTest(missing=missing):
                with self.assertRaises(e2e_executors.ExecutorError) as ctx:
                    e2e_human.build_handoff(
                        run_id=_RUN_ID, scenario_id="S-11", step_id="h", handoff_spec=spec
                    )
                self.assertEqual(ctx.exception.detail_code, "handoff_contract_incomplete")

    def test_a_non_positive_timeout_is_refused(self):
        spec = {
            "handoff_id": "HO-1", "instruction": "do", "expected_observation": "seen",
            "required_evidence": ["metadata"], "timeout_seconds": -1,
            "resume_token": "RT-1", "server_policy": "keep", "submission_path": "/tmp/s.json",
        }
        with self.assertRaises(e2e_executors.ExecutorError) as ctx:
            e2e_human.build_handoff(run_id=_RUN_ID, scenario_id="S", step_id="h", handoff_spec=spec)
        self.assertEqual(ctx.exception.detail_code, "handoff_timeout_invalid")

    def test_handoff_json_is_written_through_the_evidence_gate(self):
        fixture = _HandoffFixture()
        path = pathlib.Path(fixture.artifact_dir) / e2e_human.HANDOFF_PATH
        self.assertTrue(path.is_file())
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["handoff_id"],
                         fixture.handoff["handoff_id"])

    def test_handoff_without_an_evidence_writer_is_a_contract_error(self):
        """§C.2 [MUST] — executor는 파일을 직접 쓰지 않는다."""
        executor = e2e_human.HumanExecutor(runtime_context={"artifact_dir": "/tmp"})
        with self.assertRaises(e2e_executors.ExecutorError) as ctx:
            executor.dispatch(
                "handoff",
                {"run_id": _RUN_ID, "scenario_id": "S-11", "step_id": "h",
                 "handoff_spec": _frozen_scenario("S-11")[1]["handoff"]},
            )
        self.assertEqual(ctx.exception.detail_code, "human_evidence_writer_absent")

    def test_handoff_is_recorded_as_an_action(self):
        fixture = _HandoffFixture()
        row = fixture.executor.action_log.rows()[0]
        self.assertEqual(row["executor"], "human")
        self.assertEqual(row["action"], "handoff")
        self.assertEqual(row["step_role"], "verify")


class TestResumeState(unittest.TestCase):
    """§A.2.3 — journal resume 객체와 server_policy 해석."""

    def test_resume_state_has_every_contract_field(self):
        fixture = _HandoffFixture()
        state = e2e_human.build_resume_state(fixture.handoff)
        for field in ("resume_token", "issued_at", "expires_at", "expired",
                      "server_policy", "resumed_at"):
            self.assertIn(field, state, field)
        self.assertFalse(state["expired"])
        self.assertIsNone(state["resumed_at"])

    def test_expires_at_is_issued_at_plus_timeout_seconds(self):
        handoff = e2e_human.build_handoff(
            run_id=_RUN_ID, scenario_id="S-11", step_id="h",
            issued_at="2026-09-14T00:00:00Z",
            handoff_spec={
                "handoff_id": "HO-1", "instruction": "do", "expected_observation": "seen",
                "required_evidence": ["metadata"], "timeout_seconds": 900,
                "resume_token": "RT-1", "server_policy": "keep", "submission_path": "/tmp/s.json",
            },
        )
        state = e2e_human.build_resume_state(handoff)
        self.assertEqual(state["expires_at"], "2026-09-14T00:15:00Z")

    def test_server_policy_enum_is_the_contract_pair_and_unknown_values_keep(self):
        """§A.9 — `terminate`만 정리한다. 판단 불가는 사용자 자원을 건드리지 않는 쪽이다."""
        self.assertEqual(e2e_human.SERVER_POLICIES, ("keep", "terminate"))
        self.assertEqual(e2e_human.server_action("terminate"), "terminate")
        for value in ("keep", "local-only", None, "", "TERMINATE"):
            with self.subTest(policy=value):
                self.assertEqual(e2e_human.server_action(value), "keep")

    def test_declared_policy_text_is_preserved_verbatim(self):
        """추적 가능성 — 선언 원문은 `server_policy_declared`에 그대로 남는다."""
        fixture = _HandoffFixture()
        state = e2e_human.build_resume_state(fixture.handoff)
        self.assertEqual(
            state["server_policy_declared"], fixture.scenario["handoff"]["server_policy"]
        )

    def test_expiry_is_computed_from_expires_at(self):
        state = {"expires_at": "2026-09-14T00:15:00Z"}
        self.assertFalse(e2e_human.is_expired(state, at=datetime(2026, 9, 14, 0, 14, tzinfo=timezone.utc)))
        self.assertTrue(e2e_human.is_expired(state, at=datetime(2026, 9, 14, 0, 16, tzinfo=timezone.utc)))
        self.assertFalse(e2e_human.is_expired({"expires_at": "not-a-time"}))


class TestServerPolicyNormalization(unittest.TestCase):
    """§A.9(:346) enum 확정 + MV-17(:837) — 발행값은 반드시 `keep`|`terminate`다.

    동결 `test-scenario.json`의 S-11·S-28은 계약 밖 값 `"local-only"`를 들고 있고 spec은
    재시드할 수 없다. 따라서 집행 지점은 **발행 시점**이며, 대체는 조용히 일어나지 않는다.
    """

    def test_emitted_policy_is_always_inside_the_contract_enum(self):
        """MV-17 — 산출물 `handoff.json`의 값만이 검사 대상이다."""
        for scenario_id in ("S-11", "S-28"):
            with self.subTest(scenario=scenario_id):
                fixture = _HandoffFixture(scenario_id=scenario_id)
                emitted = fixture.handoff["server_policy"]
                self.assertIn(emitted, e2e_human.SERVER_POLICIES)
                written = json.loads(
                    (pathlib.Path(fixture.artifact_dir) / e2e_human.HANDOFF_PATH)
                    .read_text(encoding="utf-8")
                )
                self.assertIn(written["server_policy"], e2e_human.SERVER_POLICIES)

    def test_an_out_of_enum_declaration_normalizes_to_keep_not_terminate(self):
        """TASK.md C-2 — 판단 불가에서 종료 쪽으로 기울지 않는다."""
        emitted, normalized = e2e_human.normalize_server_policy("local-only")
        self.assertEqual(emitted, "keep")
        self.assertTrue(normalized)
        for value in (None, "", "LOCAL-ONLY", "terminate-now", 0, []):
            with self.subTest(declared=value):
                emitted, normalized = e2e_human.normalize_server_policy(value)
                self.assertEqual(emitted, "keep")
                self.assertTrue(normalized)

    def test_contract_enum_values_pass_through_untouched(self):
        for value in ("keep", "terminate"):
            with self.subTest(declared=value):
                emitted, normalized = e2e_human.normalize_server_policy(value)
                self.assertEqual(emitted, value)
                self.assertFalse(normalized, "정규화가 아닌데 정규화로 표시하지 않는다")

    def test_the_declared_original_survives_on_the_handoff(self):
        fixture = _HandoffFixture()
        declared = fixture.scenario["handoff"]["server_policy"]
        self.assertEqual(declared, "local-only", "동결 spec의 전제가 바뀌었다")
        self.assertEqual(fixture.handoff["server_policy_declared"], declared)
        self.assertTrue(fixture.handoff["server_policy_normalized"])
        self.assertNotEqual(fixture.handoff["server_policy"], declared)

    def test_the_journal_resume_records_both_sides_of_the_normalization(self):
        """PM 확정 — 정규화 전/후를 함께 남겨 조용한 대체를 만들지 않는다."""
        fixture = _HandoffFixture()
        state = e2e_human.build_resume_state(fixture.handoff)
        self.assertEqual(state["server_policy"], "keep")
        self.assertEqual(state["server_policy_declared"], "local-only")
        self.assertTrue(state["server_policy_normalized"])

    def test_the_resume_server_policy_is_inside_the_contract_a23_enum(self):
        """§A.2.3 (`CONTRACT.md:187`) — resume.server_policy는 `keep`|`terminate`다.

        MV-17은 `handoff.server_policy`만 보지만 §A.2.3도 같은 enum을 규정한다. 나중에
        journal 쪽 검사가 추가돼도 걸리지 않도록 지금 고정한다.
        """
        for scenario_id in ("S-11", "S-28"):
            with self.subTest(scenario=scenario_id):
                fixture = _HandoffFixture(scenario_id=scenario_id)
                state = e2e_human.build_resume_state(fixture.handoff)
                self.assertIn(state["server_policy"], e2e_human.SERVER_POLICIES)
                index = json.loads(
                    (pathlib.Path(fixture.artifact_dir) / e2e_human.RESUME_INDEX_PATH)
                    .read_text(encoding="utf-8")
                )
                self.assertIn(index["resume"]["server_policy"], e2e_human.SERVER_POLICIES)

    def test_the_key_means_the_same_thing_in_every_artifact(self):
        """같은 키 이름이 산출물마다 다른 것을 가리키지 않는다(PM 확정)."""
        fixture = _HandoffFixture()
        written_handoff = json.loads(
            (pathlib.Path(fixture.artifact_dir) / e2e_human.HANDOFF_PATH).read_text(encoding="utf-8")
        )
        resume = json.loads(
            (pathlib.Path(fixture.artifact_dir) / e2e_human.RESUME_INDEX_PATH)
            .read_text(encoding="utf-8")
        )["resume"]
        for key in ("server_policy", "server_policy_declared", "server_policy_normalized"):
            with self.subTest(key=key):
                self.assertEqual(written_handoff[key], resume[key])

    def test_the_persisted_resume_index_carries_the_normalization_record(self):
        fixture = _HandoffFixture()
        index = json.loads(
            (pathlib.Path(fixture.artifact_dir) / e2e_human.RESUME_INDEX_PATH)
            .read_text(encoding="utf-8")
        )
        resume = index["resume"]
        self.assertEqual(resume["server_policy"], "keep")
        self.assertEqual(resume["server_policy_declared"], "local-only")
        self.assertTrue(resume["server_policy_normalized"])

    def test_a_conforming_scenario_is_not_flagged_as_normalized(self):
        handoff = e2e_human.build_handoff(
            run_id=_RUN_ID, scenario_id="S-11", step_id="h",
            handoff_spec={
                "handoff_id": "HO-1", "instruction": "do", "expected_observation": "seen",
                "required_evidence": ["metadata"], "timeout_seconds": 60,
                "resume_token": "RT-1", "server_policy": "terminate",
                "submission_path": "/tmp/s.json",
            },
        )
        self.assertEqual(handoff["server_policy"], "terminate")
        self.assertEqual(handoff["server_policy_declared"], "terminate")
        self.assertFalse(handoff["server_policy_normalized"])
        state = e2e_human.build_resume_state(handoff)
        self.assertFalse(state["server_policy_normalized"])
        self.assertEqual(state["server_policy"], "terminate")
        self.assertEqual(state["server_policy"], state["server_policy_declared"])

    def test_normalizing_terminates_nothing(self):
        """C-2 — 이 executor에는 프로세스를 종료할 수단 자체가 없다."""
        fixture = _HandoffFixture()
        self.assertEqual(e2e_human.server_action(fixture.handoff["server_policy"]), "keep")
        source = (_TOOL_DIR / "lib" / "e2e" / "executors" / "human.py").read_text(encoding="utf-8")
        for forbidden in ("os.kill", "killpg", "signal.", "subprocess", ".terminate()",
                          "stop_all", "e2e_process", "e2e_runtime", "release_lease"):
            with self.subTest(call=forbidden):
                self.assertNotIn(forbidden, source)


# ─── 일시 정지 ───────────────────────────────────────────────────────────────
class TestAwaitingHumanPause(unittest.TestCase):
    """AC-9 — collaborative 시나리오가 awaiting_human(exit 20)으로 정지한다."""

    def test_awaiting_human_is_an_operational_status_with_exit_20(self):
        self.assertIn("awaiting_human", e2e_contract.OPERATIONAL_STATUSES)
        self.assertNotIn("awaiting_human", e2e_contract.FINAL_STATUSES)
        self.assertEqual(e2e_contract.status_to_exit("awaiting_human"), 20)

    def test_marking_awaiting_human_preserves_run_id_and_the_handoff_state(self):
        fixture = _HandoffFixture()
        exit_code, payload = fixture.mark_awaiting()
        self.assertEqual(exit_code, 20, payload)
        self.assertEqual(payload["status"], "awaiting_human")
        spec = json.loads(
            (pathlib.Path(fixture.task_path) / "test-scenario.json").read_text(encoding="utf-8")
        )
        target = spec["scenarios"][0]
        self.assertEqual(target["operational_status"], "awaiting_human")
        self.assertIsNone(target["result"], "정지는 최종 판정이 아니다")
        self.assertEqual(target["run_id"], _RUN_ID)
        self.assertEqual(target["handoff_state"]["resume_token"], fixture.handoff["resume_token"])

    def test_the_resume_index_keeps_what_resume_needs(self):
        fixture = _HandoffFixture()
        index = json.loads(
            (pathlib.Path(fixture.artifact_dir) / e2e_human.RESUME_INDEX_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual(index["run_id"], _RUN_ID)
        self.assertEqual(index["scenario_id"], "S-11")
        self.assertEqual(index["task_path"], fixture.task_path)
        self.assertEqual(index["resume"]["resume_token"], fixture.handoff["resume_token"])


# ─── 재개 판정 경로 ──────────────────────────────────────────────────────────
class TestResumeUsesTheExistingScenarioPath(unittest.TestCase):
    """TD-18 / §C.2 [MUST] — 새 resume 판정 경로를 만들지 않는다."""

    def test_resume_delegates_to_cmd_scenario_mark(self):
        fixture = _HandoffFixture()
        fixture.mark_awaiting()
        submission = fixture.submission()
        seen = []
        original = scenario_module.cmd_scenario_mark

        def _spy(namespace):
            seen.append(namespace)
            return original(namespace)

        scenario_module.cmd_scenario_mark = _spy
        try:
            e2e_human.run_resume(
                run_id=_RUN_ID, token=fixture.handoff["resume_token"],
                submission=submission, artifact_dir=fixture.artifact_dir,
            )
        finally:
            scenario_module.cmd_scenario_mark = original

        self.assertEqual(len(seen), 1, "재개 판정은 기존 핸들러 1회 호출로만 내려간다")
        namespace = seen[0]
        self.assertEqual(namespace.resume_run_id, _RUN_ID)
        self.assertEqual(namespace.resume_token, fixture.handoff["resume_token"])
        self.assertEqual(namespace.submission, submission)
        self.assertIsNone(namespace.result)
        self.assertIsNone(namespace.verdict_json)

    def test_a_complete_submission_passes_only_after_the_contract_gate(self):
        fixture = _HandoffFixture()
        fixture.mark_awaiting()
        payload = e2e_human.run_resume(
            run_id=_RUN_ID, token=fixture.handoff["resume_token"],
            submission=fixture.submission(), artifact_dir=fixture.artifact_dir,
        )
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual([item["id"] for item in payload["verifier_results"]], ["S-11-a1"])

    def test_completed_true_alone_does_not_make_a_pass(self):
        """R-13 [MUST] / §A.10 — 사람의 완료 선언은 pass 선언이 아니다."""
        for label, overrides in (
            ("no_assertions", {"assertion_results": []}),
            ("no_evidence", {"observed_evidence": []}),
            ("no_human_executor", {"observed_executors": []}),
            ("assertion_mismatch", {"assertion_results": [
                {"id": "S-11-a1", "expected": "x", "actual": "y", "passed": True}
            ]}),
        ):
            with self.subTest(case=label):
                fixture = _HandoffFixture()
                fixture.mark_awaiting()
                payload = e2e_human.run_resume(
                    run_id=_RUN_ID, token=fixture.handoff["resume_token"],
                    submission=fixture.submission(completed=True, **overrides),
                    artifact_dir=fixture.artifact_dir,
                )
                self.assertNotEqual(payload["status"], "pass")
                self.assertNotEqual(payload["exit_code"], 0)

    def test_a_mismatched_token_or_run_id_is_refused(self):
        for label, kwargs in (
            ("wrong_token", {"token": "RT-WRONG"}),
            ("wrong_run_id", {"run_id": "e2e-20260914-999"}),
        ):
            with self.subTest(case=label):
                fixture = _HandoffFixture()
                fixture.mark_awaiting()
                call = {
                    "run_id": _RUN_ID, "token": fixture.handoff["resume_token"],
                    "submission": fixture.submission(), "artifact_dir": fixture.artifact_dir,
                    "task_path": fixture.task_path, "scenario_id": "S-11",
                }
                call.update(kwargs)
                payload = e2e_human.run_resume(**call)
                self.assertNotEqual(payload["status"], "pass")

    def test_resume_without_a_prior_handoff_is_blocked_not_failed(self):
        with tempfile.TemporaryDirectory() as empty:
            payload = e2e_human.run_resume(
                run_id=_RUN_ID, token="RT", submission="/nonexistent.json", artifact_dir=empty
            )
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["exit_code"], e2e_contract.status_to_exit("blocked"))
        self.assertEqual(payload["detail_code"], "e2e_resume_state_not_found")


# ─── C-HUM-2 timeout ─────────────────────────────────────────────────────────
class TestTimeoutIsBlocked(unittest.TestCase):
    """C-HUM-2 [MUST] — timeout은 자동 fail이 아니라 blocked이며 만료를 기록한다."""

    def _expired_fixture(self):
        fixture = _HandoffFixture(scenario_id="S-28", timeout_seconds=1)
        fixture.mark_awaiting()
        index_path = pathlib.Path(fixture.artifact_dir) / e2e_human.RESUME_INDEX_PATH
        index = json.loads(index_path.read_text(encoding="utf-8"))
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        index["resume"]["expires_at"] = past.isoformat().replace("+00:00", "Z")
        index_path.write_text(json.dumps(index), encoding="utf-8")
        return fixture

    def test_an_expired_token_ends_blocked_with_exit_19(self):
        fixture = self._expired_fixture()
        payload = e2e_human.run_resume(
            run_id=_RUN_ID, token=fixture.handoff["resume_token"],
            submission=fixture.submission(), artifact_dir=fixture.artifact_dir,
        )
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["exit_code"], 19)
        self.assertEqual(payload["exit_code"], e2e_contract.status_to_exit("blocked"))
        self.assertNotEqual(payload["exit_code"], e2e_contract.status_to_exit("fail"))
        self.assertEqual(payload["detail_code"], "e2e_resume_token_expired")

    def test_expiry_is_recorded_in_the_journal_resume_object(self):
        fixture = self._expired_fixture()
        e2e_human.run_resume(
            run_id=_RUN_ID, token=fixture.handoff["resume_token"],
            submission=fixture.submission(), artifact_dir=fixture.artifact_dir,
        )
        journal = json.loads(
            (pathlib.Path(fixture.artifact_dir) / "journal.json").read_text(encoding="utf-8")
        )
        self.assertTrue(journal["resume"]["expired"])
        self.assertEqual(journal["resume"]["resume_token"], fixture.handoff["resume_token"])

    def test_an_expired_run_never_reaches_the_scenario_judgement(self):
        fixture = self._expired_fixture()
        called = []
        original = scenario_module.cmd_scenario_mark
        scenario_module.cmd_scenario_mark = lambda ns: called.append(ns)
        try:
            e2e_human.run_resume(
                run_id=_RUN_ID, token=fixture.handoff["resume_token"],
                submission=fixture.submission(), artifact_dir=fixture.artifact_dir,
            )
        finally:
            scenario_module.cmd_scenario_mark = original
        self.assertEqual(called, [])


# ─── §B.1.2 CLI ──────────────────────────────────────────────────────────────
class TestResumeCli(unittest.TestCase):
    """§B.1.2 — `test-tool e2e resume --run-id --token --submission [--artifact-root]`."""

    def _resume(self, args):
        return subprocess.run(
            [_PYTHON, str(_TEST_TOOL_PY), "e2e", "resume"] + args,
            capture_output=True, text=True, timeout=60,
        )

    def test_the_three_contract_arguments_are_required(self):
        for args in (
            [],
            ["--run-id", _RUN_ID],
            ["--run-id", _RUN_ID, "--token", "RT"],
            ["--token", "RT", "--submission", "/tmp/s.json"],
        ):
            with self.subTest(args=args):
                proc = self._resume(args)
                self.assertEqual(proc.returncode, 2, proc.stderr)
                self.assertIn("the following arguments are required", proc.stderr)

    def test_the_subcommand_accepts_exactly_the_contract_option_set(self):
        proc = self._resume(["--help"])
        self.assertEqual(proc.returncode, 0)
        for option in ("--run-id", "--token", "--submission", "--artifact-root"):
            self.assertIn(option, proc.stdout, option)
        for absent in ("--scenario", "--task-path", "--target"):
            self.assertNotIn(absent, proc.stdout, f"§B.1.2 밖의 인자: {absent}")

    def test_a_complete_resume_exits_with_a_contract_exit_code_and_payload(self):
        fixture = _HandoffFixture()
        fixture.mark_awaiting()
        proc = self._resume([
            "--run-id", _RUN_ID,
            "--token", fixture.handoff["resume_token"],
            "--submission", fixture.submission(),
            "--artifact-root", fixture.artifact_dir,
        ])
        payload = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, payload["exit_code"])
        self.assertIn(proc.returncode, set(e2e_contract.STATUS_EXIT_CODES.values()))
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(proc.returncode, 0)

    def test_the_stdout_payload_is_the_run_shape_plus_verifier_results(self):
        fixture = _HandoffFixture()
        fixture.mark_awaiting()
        proc = self._resume([
            "--run-id", _RUN_ID,
            "--token", fixture.handoff["resume_token"],
            "--submission", fixture.submission(),
            "--artifact-root", fixture.artifact_dir,
        ])
        payload = json.loads(proc.stdout)
        for key in ("run_id", "scenario_id", "profile", "status", "operational_status",
                    "error", "exit_code", "run_json_path", "artifact_dir", "verifier_results"):
            self.assertIn(key, payload, key)
        self.assertIsInstance(payload["verifier_results"], list)

    def test_an_unknown_run_id_is_blocked_not_a_crash(self):
        proc = self._resume([
            "--run-id", "e2e-19990101-001", "--token", "RT",
            "--submission", "/nonexistent.json",
        ])
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(proc.returncode, e2e_contract.status_to_exit("blocked"))

    def test_the_existing_e2e_run_subcommand_is_untouched(self):
        """PLAN.md H-3 — `e2e` 서브파서 확장이 기존 시그니처를 회귀시키지 않는다."""
        proc = subprocess.run(
            [_PYTHON, str(_TEST_TOOL_PY), "e2e", "run", "--help"],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.returncode, 0)
        for option in ("--scenario", "--task-path", "--target", "--worktree-root",
                       "--opal-home", "--artifact-root", "--run-id"):
            self.assertIn(option, proc.stdout, option)


# ─── C-1 동결 모듈 ───────────────────────────────────────────────────────────
class TestScenarioModuleUnchanged(unittest.TestCase):
    """TASK.md C-1 — `scenario.py`·`e2e_contract.py`는 변경 0이다."""

    def test_the_frozen_modules_have_no_working_tree_diff(self):
        root = _TOOL_DIR.parent.parent.parent
        proc = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--",
             "opal/tools/test-tool/lib/scenario.py",
             "opal/tools/test-tool/lib/e2e_contract.py"],
            cwd=root, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.stdout.strip(), "", f"frozen module changed: {proc.stdout}")

    def test_the_human_executor_declares_no_pattern_based_process_kill(self):
        """TASK.md C-9 — pkill·pgrep·killall 0건."""
        for name in ("human.py", "api.py", "__init__.py"):
            source = (_TOOL_DIR / "lib" / "e2e" / "executors" / name).read_text(encoding="utf-8")
            for forbidden in ("pkill", "pgrep", "killall"):
                with self.subTest(module=name, call=forbidden):
                    self.assertNotIn(forbidden, source)

    def test_the_human_executor_builds_no_status_or_exit_of_its_own(self):
        """C-125-1 — 상태·exit은 e2e_contract 함수 반환값으로만 만든다."""
        source = (_TOOL_DIR / "lib" / "e2e" / "executors" / "human.py").read_text(encoding="utf-8")
        for literal in ("exit_code = 19", "exit_code = 20", "exit_code = 6", '"exit_code": 19'):
            with self.subTest(literal=literal):
                self.assertNotIn(literal, source)
        self.assertIn("e2e_contract.status_to_exit", source)
        self.assertIn("e2e_contract.status_to_error", source)


if __name__ == "__main__":
    unittest.main()
