"""
@header {
  "module": "ownership_tool.tests.test_stop_hook_process",
  "layer": "test",
  "domain": "ownership",
  "description": "TASK-147 S-11/S-12 — stop_hook.py를 실제 subprocess로 띄워 Stop 판정 경로를 디스크 산출물로만 판정한다. state-tool init --run-log-mode shadow로 만든 실제 태스크 캡슐과 W-2가 캡처한 실제 Stop 봉투 fixture를 쓰며, 판정 경로에 monkeypatch·mock을 일절 쓰지 않는다(PLAN D-12, TEST-SCENARIO Setup). 기존 test_integration.py는 손대지 않는다.",
  "exports": [],
  "depends": [
    "ownership_tool.stop_hook(프로세스 실행)",
    "state-tool run.sh",
    "fixtures/hook-payloads/stop.json"
  ]
}

TASK-147 S-11·S-12 실제 훅 프로세스 E2E 테스트.

기대값의 원천:
  - `docs/run-log/CONTRACT.md` §1.2 `stop.decision`, §1.4 `last_report`, §2.5 정지 판정 5종
  - PLAN.md D-6(훅은 receipt에 적재만), D-7(`last_report` 포인터), D-8(판정 입력 교체),
    D-9(죽어 있던 `show_json`·`now` 경로 복구), D-12(훅 프로세스 실행 계층)
  - TASK.md AC-3·AC-4·AC-5·AC-6

판정 경계(harness/red-first.md §2): `stop_hook.py`의 **프로세스 stdout·exit code**와
디스크 산출물(stop-guard receipt, run-log 조각, `state.json`)만 본다. 인프로세스
`evaluate()` 직접 호출은 이 파일에서 하지 않는다 — 그 축은 단위 계약 전용이며
AC-4·AC-6의 근거가 아니다(TEST-SCENARIO Setup).

W-10의 다섯 시나리오를 각각 독립 테스트로 고정한다. 판정 경로에는
mock·patch를 쓰지 않고 state-tool·stop_hook.py를 모두 subprocess로 실호출한다.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

_TESTS_DIR = pathlib.Path(__file__).resolve().parent
_TOOL_DIR = _TESTS_DIR.parent
_REPO_ROOT = _TOOL_DIR.parent.parent.parent
_STOP_HOOK = _TOOL_DIR / "ownership_tool" / "stop_hook.py"
_STATE_RUN_SH = _REPO_ROOT / "opal" / "tools" / "state-tool" / "run.sh"

# 훅이 실제로 쓰는 인터프리터(TEST-SCENARIO Setup).
_VENV_PYTHON = pathlib.Path.home() / ".opal" / ".venv" / "bin" / "python"

# W-2가 실제 Stop에서 캡처한 봉투. **이 파일을 이 테스트가 수정·생성하지 않는다** —
# 경로로 참조만 하고 내용은 W-2가 소유한다(TASK C-4: 합성 fixture로 프로덕션 동작을
# 확정하지 않는다).
_STOP_ENVELOPE_FIXTURE = _TESTS_DIR / "fixtures" / "hook-payloads" / "stop.json"

_SESSION_ID = "sess-t147-stop-hook"
_ROWS_SPEC = json.dumps(
    [{"stage": "EXECUTE", "item": "구현"}, {"stage": "TEST", "item": "검증"}],
    ensure_ascii=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# 공통 헬퍼 — 전부 실호출이다. mock/patch/MagicMock을 쓰지 않는다.
# ─────────────────────────────────────────────────────────────────────────────

def _state_tool(args, env=None):
    """state-tool run.sh subprocess 실호출 → (exit, stdout, stderr, parsed)."""
    result = subprocess.run(
        ["bash", str(_STATE_RUN_SH)] + args,
        capture_output=True, text=True,
        env=dict(os.environ, OPAL_SESSION_ID=_SESSION_ID) if env is None else env,
    )
    stdout = result.stdout.strip()
    try:
        parsed = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        parsed = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, parsed


def _run_stop_hook(payload, project_root):
    """`stop_hook.py`를 subprocess로 실행하고 (exit, stdout, stderr)를 돌려준다.

    훅은 stdin으로 Stop 봉투를 받고, 차단일 때만 stdout 1줄을 낸다."""
    result = subprocess.run(
        [str(_VENV_PYTHON), str(_STOP_HOOK)],
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True, text=True,
        cwd=str(project_root),
        env=dict(os.environ, OPAL_SESSION_ID=_SESSION_ID),
    )
    return result.returncode, result.stdout, result.stderr


def _stop_envelope(project_root, *, stop_hook_active):
    """W-2의 실제 캡처 봉투를 읽어 이 시나리오의 cwd·session_id만 바꾼 사본을 만든다."""
    raw = json.loads(_STOP_ENVELOPE_FIXTURE.read_text(encoding="utf-8"))
    payload = dict(raw)
    payload.pop("_fixture", None)
    payload["cwd"] = str(project_root)
    payload["session_id"] = _SESSION_ID
    payload["stop_hook_active"] = stop_hook_active
    return payload


def _receipt_path(project_root):
    return (pathlib.Path(project_root) / ".opal" / "run" / ".runtime"
            / "stop-guard" / f"{_SESSION_ID}.json")


def _read_receipt(project_root):
    path = _receipt_path(project_root)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _segment_records(task):
    run_dir = pathlib.Path(task) / "run"
    records = []
    if not run_dir.exists():
        return records
    for seg in sorted(run_dir.glob("run-log-*.jsonl")):
        for line in seg.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def _events_of(task, name):
    return [r for r in _segment_records(task) if r.get("event") == name]


class _StopHookHarness(unittest.TestCase):
    """실제 캡슐·실제 lease·실제 봉투를 디스크에 배치하는 공통 setUp."""

    def setUp(self):
        self.assertTrue(
            _VENV_PYTHON.exists(),
            f"TASK-147 S-11/S-12 훅 인터프리터 부재 — {_VENV_PYTHON} "
            "(테스트 실행 환경이 없으면 자동 우회하지 않고 실패로 드러낸다, red-first.md §2)")
        self.assertTrue(_STOP_HOOK.exists(), f"stop_hook.py 부재 — {_STOP_HOOK}")

        # [MUST] W-2의 실제 캡처본을 전제한다(TASK C-4, PLAN D-13). fixture가 아직
        # 합성 상태면 AC-6의 근거로 삼을 수 없으므로 우회하지 않고 실패로 드러낸다.
        fixture = json.loads(_STOP_ENVELOPE_FIXTURE.read_text(encoding="utf-8"))
        self.assertIs(
            (fixture.get("_fixture") or {}).get("captured"), True,
            f"TASK-147 S-11/S-12 Stop 봉투 fixture가 아직 실제 캡처본이 아님 "
            f"(_fixture.captured != true) — {_STOP_ENVELOPE_FIXTURE}")

        self._tmp = tempfile.mkdtemp(prefix="t147-stop-hook-")
        self.addCleanup(shutil.rmtree, self._tmp, True)
        self.project_root, self.task = self._create_capsule("base")

    def _create_capsule(self, name):
        """shadow state·조각·lease가 있는 독립 실제 태스크 캡슐을 만든다."""
        project_root = pathlib.Path(self._tmp) / f"proj-{name}"
        task = project_root / "tasks" / f"147-stop-hook-e2e-{name}"
        task.mkdir(parents=True)

        code, out, err, _ = _state_tool([
            "init", str(task), "--skill", "oppl", "--mode", "agentic",
            "--rows-spec", _ROWS_SPEC, "--run-log-mode", "shadow"])
        self.assertEqual(code, 0, f"TASK-147 검증용 캡슐 init 실패 — {out!r} {err!r}")

        # 이 세션이 태스크를 소유(claim_source=state_transition)하는 실제 lease 레코드.
        owner = task / "run" / ".runtime" / "owner.json"
        owner.parent.mkdir(parents=True, exist_ok=True)
        owner.write_text(json.dumps({
            "task_path": str(task),
            "owner_session_id": _SESSION_ID,
            "generation": 1,
            "claimed_at": "2026-09-19 09:00:00+09:00",
            "heartbeat_at": "2026-09-19 09:30:00+09:00",
            "lease_expires_at": "2099-01-01 00:00:00+09:00",
            "status": "active",
            "ttl_sec": 14400,
            "claim_source": "state_transition",
        }, ensure_ascii=False), encoding="utf-8")
        return project_root, task

    def _log_pm_report(self, *, report_type, transition_action, user_input_required,
                       summary, task=None):
        task = self.task if task is None else task
        code, out, err, _ = _state_tool([
            "log-event", str(task), "--event", "pm.report",
            "--report-type", report_type,
            "--transition-action", transition_action,
            "--user-input-required", user_input_required,
            "--summary", summary])
        self.assertEqual(
            code, 0,
            f"TASK-147 선행 pm.report 기록 실패(CONTRACT §2.4가 계약한 "
            f"`log-event --event pm.report` 표면이 없다) — exit={code} "
            f"stdout={out!r} stderr={err!r}")
        reports = _events_of(task, "pm.report")
        self.assertTrue(reports, "TASK-147 pm.report가 조각에 기록되지 않음")
        return reports[-1]

    def _block_continue(self):
        """비차단 보고 후 실제 Stop을 1회 차단하고 보고 사건을 돌려준다."""
        report = self._log_pm_report(
            report_type="progress_report", transition_action="continue",
            user_input_required="false", summary="TASK-147 W-10 비차단 진행 통지")
        payload = _stop_envelope(self.project_root, stop_hook_active=False)
        code, stdout, stderr = _run_stop_hook(payload, self.project_root)
        self.assertEqual(code, 0, f"TASK-147 W-10 Stop fail-safe 위반 — {stderr!r}")
        self.assertTrue(stdout.strip(), "TASK-147 W-10 선행 Stop이 차단되지 않음")
        return report

    def _assert_exact_stop_axis(self, task, expected_axis, scenario):
        code, out, err, data = _state_tool(
            ["verify", str(task), "--run-log-completeness-check"])
        self.assertEqual(code, 0, f"{scenario} verify exit 0 위반 — {out!r} {err!r}")
        axes = ("report_intent_inconsistent", "missing_stop_decision",
                "stop_decision_allowed", "stop_block_without_followup")
        for axis in axes:
            self.assertIn(axis, data, f"{scenario} 판정 축 {axis} 부재 — {sorted(data)}")
            if axis == expected_axis:
                self.assertTrue(data[axis], f"{scenario} {axis}에 판정이 없음 — {data!r}")
            else:
                self.assertEqual(
                    data[axis], [], f"{scenario} {axis}에도 중복 분류됨 — {data!r}")


class TestT147S11StopHookHonoursLastReport(_StopHookHarness):
    """TASK-147.S-11 (AC-4, AC-6, C-4) — 보고 의도별 Stop 실행.

    D-8 — Stop 판정 입력이 `current_status` 추정에서 `run_log.last_report`로 바뀐다.
    (1) `decision_request` ∧ `user_input_required=true` → 정상 정지(무출력·exit 0).
    (2) `progress_report` ∧ `false` ∧ `continue` → 차단 1줄·exit 0이고 receipt
        `pending_decisions`가 1건 늘어난다(D-6 — 훅은 적재만 하고 run-log에 쓰지 않는다).
    """

    def test_decision_request_report_lets_stop_pass_silently(self):
        self._log_pm_report(
            report_type="decision_request", transition_action="await_user",
            user_input_required="true",
            summary="TASK-147 S-11(1) 사용자 응답을 기다리는 보고")

        payload = _stop_envelope(self.project_root, stop_hook_active=False)
        code, stdout, stderr = _run_stop_hook(payload, self.project_root)

        self.assertEqual(code, 0, f"TASK-147.S-11(1) fail-safe exit 0 위반 — {stderr!r}")
        self.assertEqual(
            stdout, "",
            f"TASK-147.S-11(1) decision_request 보고인데 Stop이 차단됨 — "
            f"판정 입력이 아직 last_report가 아니라 current_status 추정이다(D-8) — "
            f"stdout={stdout!r}")

    def test_progress_report_continue_blocks_and_stages_pending_decision(self):
        report = self._log_pm_report(
            report_type="progress_report", transition_action="continue",
            user_input_required="false", summary="TASK-147 S-11(2) 비차단 진행 통지")
        payload = _stop_envelope(self.project_root, stop_hook_active=False)
        code, stdout, stderr = _run_stop_hook(payload, self.project_root)

        self.assertEqual(code, 0, f"TASK-147.S-11(2) fail-safe exit 0 위반 — {stderr!r}")
        lines = [l for l in stdout.splitlines() if l.strip()]
        self.assertEqual(
            len(lines), 1,
            f"TASK-147.S-11(2) stdout이 1줄이 아님(훅의 유일한 채널) — {stdout!r}")
        decision = json.loads(lines[0])
        self.assertEqual(decision.get("decision"), "block",
                         f"TASK-147.S-11(2) 차단 판정이 아님 — {decision!r}")
        self.assertTrue(decision.get("reason"),
                        f"TASK-147.S-11(2) reason이 비어 있음 — {decision!r}")

        receipt = _read_receipt(self.project_root)
        self.assertIsInstance(
            receipt, dict, "TASK-147.S-11(2) stop-guard receipt가 생성되지 않음")
        pending = receipt.get("pending_decisions")
        self.assertIsInstance(
            pending, list,
            f"TASK-147.S-11(2) receipt에 pending_decisions[]가 없음(D-6 미구현 RED) — "
            f"{sorted(receipt)}")
        self.assertEqual(
            len(pending), 1,
            f"TASK-147.S-11(2) pending_decisions가 1건 늘지 않음 — {pending!r}")
        entry = pending[0]
        self.assertEqual(entry.get("decision_kind"), "block_continue",
                         f"TASK-147.S-11(2) 적재된 판정 종류가 다름 — {entry!r}")
        self.assertEqual(
            entry.get("report_event_id"), report["event_id"],
            f"TASK-147.S-11(2) 적재된 report_event_id가 판정에 쓰인 pm.report와 다름 — {entry!r}")
        self.assertEqual(
            entry.get("task_path"), str(self.task),
            f"TASK-147.S-11(2) 적재된 task_path가 다름 — {entry!r}")

        # D-6 — 훅은 run-log에 직접 쓰지 않는다. 이 시점에 조각은 비어 있어야 한다.
        self.assertEqual(
            _events_of(self.task, "stop.decision"), [],
            "TASK-147.S-11(2) 훅이 run-log에 stop.decision을 직접 append함(D-6 위반)")


class TestT147S12DrainAndRepeatStopPath(_StopHookHarness):
    """TASK-147.S-12 (AC-3, AC-4, AC-5, AC-6) — drain·재Stop·분류 E2E.

    S-11(2) 직후 상태에서:
      ① `state-tool` 호출 1회로 drain → `stop.decision`이 조각에 커밋되고
         `caused_by_event_id`가 그 `pm.report`를 가리킨다(D-6·W-7).
      ② 상태 진전 없이 재차 Stop → `allow_no_progress_same_fingerprint`로 통과하고
         receipt의 `fingerprint`·`decided_at`이 채워진다(D-9가 살린 경로의 실증).
      ③ `verify --run-log-completeness-check`의 판정 축에서 분류가 서로 다른 축에 잡힌다.

    drain은 `log-event --event activity`로 건다 — `run_log_commit()` 진입 1회면
    충분하고(W-7), 행 상태를 바꾸지 않아 "상태 진전 없이"라는 ② 전제를 지킨다
    (`advance`/`mark`는 fingerprint를 바꿔 ②를 관측 불가로 만든다).
    """

    def test_next_state_tool_call_commits_decision_caused_by_report(self):
        report = self._block_continue()

        # state-tool 호출 1회로 drain
        code, out, err, _ = _state_tool([
            "log-event", str(self.task), "--event", "activity", "--kind", "progress",
            "--summary", "TASK-147 S-12 drain 유발 활동"])
        self.assertEqual(code, 0, f"TASK-147.S-12 drain 호출 실패 — {out!r} {err!r}")

        committed = _events_of(self.task, "stop.decision")
        self.assertEqual(
            len(committed), 1,
            f"TASK-147.S-12 drain 후 stop.decision이 조각에 1건이 아님(W-7) — "
            f"{[r.get('event') for r in _segment_records(self.task)]}")
        self.assertEqual(
            committed[0].get("caused_by_event_id"), report["event_id"],
            f"TASK-147.S-12 caused_by_event_id가 (2)의 pm.report를 가리키지 않음 — "
            f"{committed[0].get('caused_by_event_id')!r}")

        receipt_after_drain = _read_receipt(self.project_root) or {}
        self.assertEqual(
            receipt_after_drain.get("pending_decisions") or [], [],
            f"TASK-147.S-12 drain 후 receipt에 판정이 남음 — {receipt_after_drain!r}")

    def test_repeat_stop_without_state_progress_allows_same_fingerprint(self):
        self._block_continue()
        code, out, err, _ = _state_tool([
            "log-event", str(self.task), "--event", "activity", "--kind", "progress",
            "--summary", "TASK-147 S-12 drain 유발 활동"])
        self.assertEqual(code, 0, f"TASK-147.S-12 drain 호출 실패 — {out!r} {err!r}")

        # 상태 진전 없이 재차 Stop
        repeat_payload = _stop_envelope(self.project_root, stop_hook_active=True)
        code, stdout, stderr = _run_stop_hook(repeat_payload, self.project_root)
        self.assertEqual(code, 0, f"TASK-147.S-12 재차 Stop fail-safe 위반 — {stderr!r}")
        self.assertEqual(
            stdout, "",
            f"TASK-147.S-12 상태 진전이 없는데 재차 차단됨 — "
            f"allow_no_progress_same_fingerprint 경로가 아직 도달 불가하다(D-9) — "
            f"stdout={stdout!r}")

        receipt = _read_receipt(self.project_root) or {}
        self.assertEqual(
            receipt.get("decision_kind"), "allow_no_progress_same_fingerprint",
            f"TASK-147.S-12 재차 Stop 판정 종류가 다름 — {receipt!r}")
        self.assertTrue(
            receipt.get("fingerprint"),
            f"TASK-147.S-12 receipt fingerprint가 비어 있음 — stop_hook이 show_json을 "
            f"넘기지 않는다(D-9) — {receipt!r}")
        self.assertTrue(
            receipt.get("decided_at"),
            f"TASK-147.S-12 receipt decided_at이 비어 있음 — stop_hook이 now를 "
            f"넘기지 않는다(D-9) — {receipt!r}")

    def test_completeness_four_classifications_are_mutually_exclusive(self):
        # (a) PM의 잘못된 정지 의도 — 뒤 앵커가 없어 missing은 성립하지 않는다.
        _root, task = self._create_capsule("intent")
        self._log_pm_report(
            task=task, report_type="decision_request", transition_action="continue",
            user_input_required="true", summary="TASK-147 W-10 intent")
        self._assert_exact_stop_axis(task, "report_intent_inconsistent", "TASK-147.W-10(5a)")

        # (b) hook 미실행 — 두 번째 보고가 뒤 앵커이지만 stop.decision은 없다.
        _root, task = self._create_capsule("missing")
        self._log_pm_report(
            task=task, report_type="progress_report", transition_action="await_user",
            user_input_required="false", summary="TASK-147 W-10 missing anchor front")
        self._log_pm_report(
            task=task, report_type="decision_request", transition_action="await_user",
            user_input_required="true", summary="TASK-147 W-10 missing anchor back")
        self._assert_exact_stop_axis(task, "missing_stop_decision", "TASK-147.W-10(5b)")

        # (c) hook 허용 — 실제 Stop receipt를 다음 보고 호출이 drain한다.
        root, task = self._create_capsule("allowed")
        self._log_pm_report(
            task=task, report_type="decision_request", transition_action="await_user",
            user_input_required="true", summary="TASK-147 W-10 allowed")
        code, stdout, stderr = _run_stop_hook(
            _stop_envelope(root, stop_hook_active=False), root)
        self.assertEqual(code, 0, f"TASK-147.W-10(5c) Stop 실패 — {stderr!r}")
        self.assertEqual(stdout, "", f"TASK-147.W-10(5c) 허용 Stop이 차단됨 — {stdout!r}")
        self._log_pm_report(
            task=task, report_type="decision_request", transition_action="await_user",
            user_input_required="true", summary="TASK-147 W-10 allowed drain")
        self._assert_exact_stop_axis(task, "stop_decision_allowed", "TASK-147.W-10(5c)")

        # (d) 차단 후 후속 활동 부재 — pm.report로 drain해 activity/state.changed를
        # 만들지 않고, 실제 hook의 block_continue만 독립 분류한다.
        root, task = self._create_capsule("block-no-followup")
        report = self._log_pm_report(
            task=task, report_type="progress_report", transition_action="continue",
            user_input_required="false", summary="TASK-147 W-10 block")
        code, stdout, stderr = _run_stop_hook(
            _stop_envelope(root, stop_hook_active=False), root)
        self.assertEqual(code, 0, f"TASK-147.W-10(5d) Stop 실패 — {stderr!r}")
        self.assertTrue(stdout.strip(), "TASK-147.W-10(5d) Stop이 차단되지 않음")
        self._log_pm_report(
            task=task, report_type="decision_request", transition_action="await_user",
            user_input_required="true", summary="TASK-147 W-10 block drain")
        decisions = _events_of(task, "stop.decision")
        self.assertEqual(len(decisions), 1, f"TASK-147.W-10(5d) decision drain 실패 — {decisions!r}")
        self.assertEqual(decisions[0].get("caused_by_event_id"), report["event_id"])
        self._assert_exact_stop_axis(
            task, "stop_block_without_followup", "TASK-147.W-10(5d)")


if __name__ == "__main__":
    unittest.main()
