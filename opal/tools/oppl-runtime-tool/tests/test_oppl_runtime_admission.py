"""
@header {
  "module": "test_oppl_runtime_admission",
  "task": "131",
  "layer": "test",
  "domain": "opal-tools",
  "description": "oppl-runtime-tool ledger·lock·admission 행위 계약 RED-first 테스트. S-15(resume 상한), S-16(5개 상한 도달), S-17(실패 지문 무진전), S-18(실제 다중 프로세스 동시 admit 직렬화), S-19(receipt 없는 done 기록 금지), S-26(ledger 축 분리 — 3-SSOT 비복제·원문 비저장), S-34(T4b 3분기 동시 차감), S-11(ledger cost_used 비합산)을 담당한다. 검증 대상은 run.sh 공개 인터페이스(stdout 단일 라인 JSON + exit code)와 runtime.json 저장값뿐이며 내부 함수 결합·mock/patch를 쓰지 않는다(red-first.md §4). RED 상태 — oppl-runtime-tool 미구현이므로 전부 FAIL 예상. GREEN 전환은 EXECUTE 구현 워커 담당(작성자≠구현자, red-first.md §2).",
  "scenarios": ["S-15", "S-16", "S-17", "S-18", "S-19", "S-26", "S-34", "S-11"],
  "exports": ["TestResumeLimit", "TestLimitExhaustion", "TestFailureFingerprint", "TestConcurrentAdmit", "TestReceiptGate", "TestLedgerAxisSeparation", "TestT4bTransitionDeduction", "TestLedgerCostUsed"]
}

고정하는 공개 인터페이스 (PLAN.md D2 / W-6)
--------------------------------------------
  run.sh init           --task-path <t> --run-id <id>
  run.sh admit          --task-path <t> --scope round|dispatch|task-phase|resume
                        [--task-id <id> --phase <p>]
  run.sh attempt-start  --task-path <t> --task-id <id> --phase <p>
                        --attempt-id <aid> --record-path <path>
  run.sh attempt-finish --task-path <t> --task-id <id> --phase <p> --attempt-id <aid>
                        --status <pending|running|done|failed|error|blocked|timed_out>
                        [--cost-usd <float>] [--exit-class <c>] [--verifier-id <v>]
                        [--command-id <c>] [--failing-scenarios <json array>]
                        [--error-code <c>] [--contract-revision <r>]
                        [--t4b-branch impl_defect|contract_defect|policy_conflict]
  run.sh show           --task-path <t>   → {"ok":true,"command":"show","runtime":{...}}

  성공 {"ok":true,...} exit 0 / 실패 {"ok":false,"error":"<코드>",...} exit != 0
  (opal/core/references/harness/tool-output-contract.md — 단일 라인 JSON + exit code만)

  admit이 카운터를 증가시키고 active attempt를 예약한다(제안서 §6.2 "허가된 경우에만
  카운터를 증가"). attempt-start는 attempt-id·attempt record 경로를 ledger에 외래 참조로
  바인딩하고, attempt-finish만이 phase 상태를 확정하는 receipt 경로다(AC-12).

근거
  제안서 §5(상태 7종) §6.2(admission 6검사·거부 코드 8종) §6.3(실패 지문) §6.4(T4b 전이)
  PLAN.md D4(ledger 집계값만) D9(exit_class 1급 필드) W-6
  TASK C-4(축 분리) C-10(cost_used 비합산)
  guards.md §자동 루핑 제약(재개 상한 — 수치를 테스트에 복제하지 않고 도구 노출값으로 검증)
"""

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
import unittest

_RUN_SH = pathlib.Path(__file__).resolve().parent.parent / "run.sh"

REGISTERED_PHASES = ["t1", "t2", "g", "t3", "t4a", "t4b"]

REJECTION_CODES = {
    "active_attempt",
    "round_limit_exceeded",
    "attempt_limit_exceeded",
    "resume_limit_exceeded",
    "budget_exceeded",
    "timeout_limit_exceeded",
    "no_progress",
    "decision_required",
}

TASK_ID = "T-001"
PHASE = "t3"
RUN_ID = "run-20260914000000-deadbeef"


def valid_runtime(**overrides):
    base = {
        "max_design_rounds": 5,
        "max_project_dispatches": 20,
        "max_task_attempts": 4,
        "max_identical_failures": 3,
        "max_wall_time_sec": 3600,
        "heartbeat_timeout_sec": 120,
        "hard_timeout_sec_by_phase": {p: 600 for p in REGISTERED_PHASES},
        "max_hard_timeout_sec": 1800,
        "terminate_grace_sec": 5,
    }
    base.update(overrides)
    return base


class Workspace:
    def __init__(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="oppl-rt-adm-"))
        self.opal_home = self.tmp / "opal-home"
        self.opal_home.mkdir(parents=True)
        self.project_root = self.tmp / "project"
        (self.project_root / ".opal").mkdir(parents=True)
        self.task_path = self.project_root / "tasks" / "T-001-fixture"
        self.task_path.mkdir(parents=True)

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_global(self, runtime):
        (self.opal_home / "setting.json").write_text(
            json.dumps({"oppl": {"runtime": runtime}}, ensure_ascii=False), encoding="utf-8"
        )

    def write_state(self, run_id=RUN_ID):
        doc = {
            "task_id": "131",
            "skill": "opal-pilot-project-loop",
            "mode": "agentic",
            "schema_version": "2.0",
            "created_at": "2026-09-14 00:00",
            "updated_at": "2026-09-14 00:00",
            "current_status": "in_progress",
            "rows": [],
            "run_id": run_id,
        }
        (self.task_path / "state.json").write_text(
            json.dumps(doc, ensure_ascii=False), encoding="utf-8"
        )

    @property
    def runtime_json(self):
        return self.task_path / ".oppl-run" / "runtime.json"

    def env(self):
        e = dict(os.environ)
        e["OPAL_HOME"] = str(self.opal_home)
        return e


def run_tool(ws, args, timeout=60):
    proc = subprocess.run(
        ["bash", str(_RUN_SH), *args],
        capture_output=True, text=True, env=ws.env(),
        cwd=str(ws.project_root), timeout=timeout,
    )
    stdout = proc.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return proc.returncode, stdout, data


def collect_keys(node, out=None):
    if out is None:
        out = set()
    if isinstance(node, dict):
        for k, v in node.items():
            out.add(k)
            collect_keys(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_keys(v, out)
    return out


class _Base(unittest.TestCase):
    """실제 파일·실제 프로세스만 사용한다. 대역·mock 없음."""

    RUNTIME_OVERRIDES = {}

    def setUp(self):
        self.ws = Workspace()
        self.addCleanup(self.ws.cleanup)
        self.ws.write_global(valid_runtime(**self.RUNTIME_OVERRIDES))
        self.ws.write_state()
        self.init_ledger()

    # ── 호출 헬퍼 ────────────────────────────────────────────────────────
    def tool(self, *args, **kw):
        return run_tool(self.ws, ["--task-path", str(self.ws.task_path), *args], **kw)

    def init_ledger(self):
        rc, stdout, data = run_tool(
            self.ws, ["init", "--task-path", str(self.ws.task_path), "--run-id", RUN_ID]
        )
        self.assert_ok(rc, stdout, data, "init")
        return data

    def assert_ok(self, rc, stdout, data, label):
        self.assertTrue(stdout, f"[{label}] stdout이 비어 있다 — 단일 라인 JSON 계약 위반")
        self.assertNotIn("\n", stdout, f"[{label}] 다중 라인 출력 — 계약 위반: {stdout!r}")
        self.assertTrue(data.get("ok"), f"[{label}] 실패 응답: {data!r}")
        self.assertEqual(rc, 0, f"[{label}] exit code가 0이 아니다: {rc}")
        return data

    def assert_rejected(self, rc, stdout, data, code, label):
        self.assertTrue(stdout, f"[{label}] stdout이 비어 있다")
        self.assertNotIn("\n", stdout, f"[{label}] 다중 라인 출력 — 계약 위반: {stdout!r}")
        self.assertFalse(data.get("ok"), f"[{label}] 거부되지 않았다: {data!r}")
        self.assertEqual(data.get("error"), code, f"[{label}] 오류 코드 불일치: {data!r}")
        self.assertIn(data.get("error"), REJECTION_CODES, f"[{label}] 거부 코드 8종 밖")
        self.assertNotEqual(rc, 0, f"[{label}] exit code가 0이다")
        return data

    # ── ledger 조회 ──────────────────────────────────────────────────────
    def read_ledger_file(self):
        """runtime.json을 직접 읽는다 — show 출력이 아니라 저장된 원본을 본다."""
        self.assertTrue(
            self.ws.runtime_json.exists(),
            f"runtime.json이 생성되지 않았다: {self.ws.runtime_json}",
        )
        return json.loads(self.ws.runtime_json.read_text(encoding="utf-8"))

    def ledger(self):
        rc, stdout, data = self.tool("show")
        self.assert_ok(rc, stdout, data, "show")
        self.assertIn("runtime", data, f"show 응답에 runtime 블록이 없다: {data!r}")
        return data["runtime"]

    def counters(self, task_id=TASK_ID, phase=PHASE, ledger=None):
        """(task_id, phase)의 attempt 카운터 레코드를 찾는다.

        중첩 구조는 구현 선택이므로 고정하지 않는다. 고정하는 계약은 task·phase 단위로
        attempt_count / resume_count / active_attempt_id가 조회 가능하다는 점뿐이다(D4).
        """
        node = self.ledger() if ledger is None else ledger
        found = []

        def walk(n, trail):
            if isinstance(n, dict):
                if "attempt_count" in n:
                    key = "/".join(str(t) for t in trail)
                    if task_id in key and phase in [str(t) for t in trail]:
                        found.append(n)
                for k, v in n.items():
                    walk(v, trail + [k])
            elif isinstance(n, list):
                for i, v in enumerate(n):
                    walk(v, trail + [str(i)])

        walk(node, [])
        self.assertEqual(
            len(found), 1,
            f"(task_id={task_id}, phase={phase}) attempt 카운터 레코드를 1건 찾지 못했다: "
            f"{len(found)}건 / ledger={json.dumps(node, ensure_ascii=False)[:400]}",
        )
        for field in ("attempt_count", "resume_count", "active_attempt_id"):
            self.assertIn(field, found[0], f"카운터 레코드에 {field}가 없다: {found[0]!r}")
        return found[0]

    # ── attempt 수명주기 ──────────────────────────────────────────────────
    def admit(self, scope, task_id=TASK_ID, phase=PHASE):
        args = ["admit", "--scope", scope]
        if scope in ("task-phase", "resume"):
            args += ["--task-id", task_id, "--phase", phase]
        return self.tool(*args)

    def start(self, attempt_id, task_id=TASK_ID, phase=PHASE):
        record = self.ws.task_path / ".oppl-run" / f"{phase}.{attempt_id}.attempt.json"
        return self.tool(
            "attempt-start", "--task-id", task_id, "--phase", phase,
            "--attempt-id", attempt_id, "--record-path", str(record),
        )

    def finish(self, attempt_id, status="failed", task_id=TASK_ID, phase=PHASE, **extra):
        args = ["attempt-finish", "--task-id", task_id, "--phase", phase,
                "--attempt-id", attempt_id, "--status", status]
        for key, value in extra.items():
            args += [f"--{key.replace('_', '-')}", str(value)]
        return self.tool(*args)

    def cycle(self, attempt_id, status="failed", **extra):
        """admit → attempt-start → attempt-finish 1회전. 전부 성공해야 한다."""
        rc, stdout, data = self.admit("task-phase")
        self.assert_ok(rc, stdout, data, f"admit({attempt_id})")
        rc, stdout, data = self.start(attempt_id)
        self.assert_ok(rc, stdout, data, f"attempt-start({attempt_id})")
        rc, stdout, data = self.finish(attempt_id, status=status, **extra)
        self.assert_ok(rc, stdout, data, f"attempt-finish({attempt_id})")
        return data


# ─────────────────────────────────────────────────────────────────────────────
# S-15 — 동일 컨텍스트 resume 상한 (AC-4)
# ─────────────────────────────────────────────────────────────────────────────
class TestResumeLimit(_Base):

    def test_s15_second_resume_rejected_and_limit_is_tool_exposed(self):
        """resume 허가 횟수는 도구가 노출한 상한값과 일치해야 한다.

        guards.md §자동 루핑 제약의 수치를 테스트에 복제하지 않는다 — 허가가 끊긴 지점의
        허가 횟수와 거부 응답이 노출하는 `limit`이 같은지만 본다.
        """
        granted = 0
        rejection = None
        for i in range(1, 11):
            rc, stdout, data = self.admit("resume")
            if data.get("ok"):
                granted += 1
                # resume 허가 뒤 active attempt를 닫아 다음 resume이 active_attempt로
                # 막히지 않게 한다
                a = f"a{i}"
                rc2, so2, d2 = self.start(a)
                self.assert_ok(rc2, so2, d2, f"attempt-start({a})")
                rc3, so3, d3 = self.finish(a, status="failed")
                self.assert_ok(rc3, so3, d3, f"attempt-finish({a})")
                continue
            rejection = self.assert_rejected(
                rc, stdout, data, "resume_limit_exceeded", f"resume #{i}"
            )
            break

        self.assertIsNotNone(rejection, "resume이 상한 없이 계속 허가됐다")
        self.assertIn("limit", rejection, f"거부 응답이 상한값을 노출하지 않는다: {rejection!r}")
        self.assertEqual(
            granted, rejection["limit"],
            f"허가 횟수({granted})가 도구가 노출한 상한({rejection['limit']})과 다르다",
        )
        self.assertEqual(
            self.counters()["resume_count"], granted,
            "ledger resume_count가 실제 허가 횟수와 다르다",
        )

    def test_s15_resume_limit_absent_from_config_output(self):
        """재개 상한은 설정 키가 아니다 — config 출력에 부재해야 한다."""
        rc, stdout, data = self.tool("config")
        self.assert_ok(rc, stdout, data, "config")
        eff = data.get("config", {})
        leaked = [k for k in eff if "resume" in k.lower()]
        self.assertEqual(leaked, [], f"재개 상한이 설정 키로 노출됐다: {leaked}")


# ─────────────────────────────────────────────────────────────────────────────
# S-16 — 5개 상한 도달 후 거부 + blocked 전이 (AC-6)
# ─────────────────────────────────────────────────────────────────────────────
class TestLimitExhaustion(_Base):

    def _fresh(self, **overrides):
        self.ws.cleanup()
        self.ws = Workspace()
        self.addCleanup(self.ws.cleanup)
        self.ws.write_global(valid_runtime(**overrides))
        self.ws.write_state()
        self.init_ledger()

    def _assert_blocked_status(self, label):
        self.assertEqual(
            self.ledger().get("status"), "blocked",
            f"[{label}] 상한 도달 후 ledger status가 blocked로 전이하지 않았다",
        )

    def test_s16_design_round_limit(self):
        self._fresh(max_design_rounds=1)
        rc, stdout, data = self.admit("round")
        self.assert_ok(rc, stdout, data, "round #1")
        rc, stdout, data = self.admit("round")
        self.assert_rejected(rc, stdout, data, "round_limit_exceeded", "round #2")
        self._assert_blocked_status("round")

    def test_s16_project_dispatch_limit(self):
        self._fresh(max_project_dispatches=1)
        rc, stdout, data = self.admit("dispatch")
        self.assert_ok(rc, stdout, data, "dispatch #1")
        rc, stdout, data = self.admit("dispatch")
        self.assert_rejected(rc, stdout, data, "attempt_limit_exceeded", "dispatch #2")
        self._assert_blocked_status("dispatch")

    def test_s16_task_attempt_limit(self):
        self._fresh(max_task_attempts=1)
        self.cycle("a1", status="failed")
        rc, stdout, data = self.admit("task-phase")
        self.assert_rejected(rc, stdout, data, "attempt_limit_exceeded", "task-phase #2")
        self.assertEqual(self.counters()["attempt_count"], 1, "거부된 admit이 카운터를 올렸다")
        self._assert_blocked_status("task-attempt")

    def test_s16_wall_time_limit(self):
        self._fresh(max_wall_time_sec=1)
        time.sleep(1.5)
        rc, stdout, data = self.admit("task-phase")
        self.assert_rejected(rc, stdout, data, "budget_exceeded", "wall-time")
        self._assert_blocked_status("wall-time")
        # 신규 프로세스 0건 — 거부 경로는 attempt record를 만들지 않는다
        self.assertEqual(
            list((self.ws.task_path / ".oppl-run").glob("*.attempt.json")), [],
            "거부 경로에서 attempt record가 생성됐다 (신규 프로세스 0건 위반)",
        )
        self.assertEqual(
            self.counters()["attempt_count"] if _has_counter(self.ledger(), TASK_ID, PHASE) else 0,
            0, "거부된 admit이 attempt 카운터를 올렸다",
        )

    def test_s16_cost_limit(self):
        self._fresh(max_cost_usd=1)
        self.cycle("a1", status="failed", cost_usd=1.0)
        rc, stdout, data = self.admit("task-phase")
        self.assert_rejected(rc, stdout, data, "budget_exceeded", "cost")
        self._assert_blocked_status("cost")


# ─────────────────────────────────────────────────────────────────────────────
# S-17 — 실패 지문 무진전 판정 (AC-7)
# ─────────────────────────────────────────────────────────────────────────────
class TestFailureFingerprint(_Base):

    RUNTIME_OVERRIDES = {"max_identical_failures": 3, "max_task_attempts": 50}

    FAILURE = {
        "exit_class": "impl_failure",
        "verifier_id": "pytest",
        "command_id": "cmd-unit",
        "error_code": "assertion_failed",
        "contract_revision": "r7",
    }

    def _fingerprints(self):
        text = json.dumps(self.ledger(), ensure_ascii=False)
        import re
        return set(re.findall(r"\b[0-9a-f]{64}\b", text))

    def test_s17_identical_failures_trigger_no_progress(self):
        """동일 정규화 payload가 max_identical_failures에 도달하면 no_progress."""
        limit = 3  # RUNTIME_OVERRIDES가 주입한 설정값 — 테스트가 소유한 fixture 값이다
        for i in range(1, limit + 1):
            self.cycle(f"a{i}", status="failed",
                       failing_scenarios=json.dumps(["S-2", "S-1"]), **self.FAILURE)
        rc, stdout, data = self.admit("task-phase")
        self.assert_rejected(rc, stdout, data, "no_progress", "identical failures")

        fps = self._fingerprints()
        self.assertEqual(len(fps), 1, f"동일 실패인데 지문이 여러 개다: {fps}")

    def test_s17_scenario_id_order_does_not_create_new_fingerprint(self):
        """대조군 — failing_scenario_ids 순서만 뒤바꿔도 정렬 후 같은 지문이다."""
        orders = [["S-2", "S-1"], ["S-1", "S-2"], ["S-2", "S-1"]]
        for i, order in enumerate(orders, start=1):
            self.cycle(f"a{i}", status="failed",
                       failing_scenarios=json.dumps(order), **self.FAILURE)
        fps = self._fingerprints()
        self.assertEqual(len(fps), 1, f"순서 차이가 새 지문을 만들었다: {fps}")
        rc, stdout, data = self.admit("task-phase")
        self.assert_rejected(rc, stdout, data, "no_progress", "reordered scenario ids")

    def test_s17_volatile_inputs_excluded_from_fingerprint(self):
        """attempt-id·attempt record 임시 경로·시각이 매회 달라도 같은 지문에 누적된다.

        자유 텍스트·timestamp·임시 경로·PID는 지문에서 제외된다(제안서 §6.3).
        """
        for i in range(1, 4):
            time.sleep(0.05)  # 도구가 스스로 찍는 timestamp를 매회 달라지게 한다
            self.cycle(f"attempt-{i}-{os.getpid()}", status="failed",
                       failing_scenarios=json.dumps(["S-1", "S-2"]), **self.FAILURE)
        self.assertEqual(len(self._fingerprints()), 1,
                         "휘발성 입력이 새 지문을 만들었다")
        rc, stdout, data = self.admit("task-phase")
        self.assert_rejected(rc, stdout, data, "no_progress", "volatile inputs")

    def test_s17_exit_class_is_first_class_field(self):
        """D9 — exit_class가 다르면 다른 지문이다(api_error는 no_progress를 트리거하지 않는다)."""
        self.cycle("a1", status="failed",
                   failing_scenarios=json.dumps(["S-1"]), **self.FAILURE)
        api = dict(self.FAILURE, exit_class="api_error")
        for i in range(2, 6):
            self.cycle(f"a{i}", status="error",
                       failing_scenarios=json.dumps(["S-1"]), **api)
        rc, stdout, data = self.admit("task-phase")
        self.assert_ok(rc, stdout, data, "api_error repetition must stay admissible")


# ─────────────────────────────────────────────────────────────────────────────
# S-18 — 실제 다중 프로세스 동시 admit (AC-11)
# ─────────────────────────────────────────────────────────────────────────────
class TestConcurrentAdmit(_Base):

    CONCURRENCY = 6

    def test_s18_exactly_one_admit_granted_under_real_concurrency(self):
        """동일 task·phase에 6개 실제 프로세스가 동시에 admit → 정확히 1건만 허가."""
        args = [
            "bash", str(_RUN_SH), "admit",
            "--task-path", str(self.ws.task_path),
            "--scope", "task-phase",
            "--task-id", TASK_ID, "--phase", PHASE,
        ]
        procs = [
            subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, env=self.ws.env(), cwd=str(self.ws.project_root))
            for _ in range(self.CONCURRENCY)
        ]
        results = []
        for p in procs:
            out, _err = p.communicate(timeout=60)
            stdout = out.strip()
            try:
                data = json.loads(stdout) if stdout else {}
            except json.JSONDecodeError:
                data = {"_raw": stdout}
            results.append((p.returncode, stdout, data))

        granted = [r for r in results if r[2].get("ok") is True]
        rejected = [r for r in results if r[2].get("ok") is False]

        for rc, stdout, data in results:
            self.assertTrue(stdout, "동시 호출 중 stdout이 비어 있다 — 계약 위반")
            self.assertNotIn("\n", stdout, f"다중 라인 출력 — 계약 위반: {stdout!r}")

        self.assertEqual(len(granted), 1,
                         f"정확히 1건만 허가되어야 한다 — 허가 {len(granted)}건")
        self.assertEqual(len(rejected), self.CONCURRENCY - 1,
                         "허가되지 않은 호출이 모두 거부 응답을 내지 않았다")
        self.assertEqual(granted[0][0], 0, "허가 응답의 exit code가 0이 아니다")
        for rc, _stdout, data in rejected:
            self.assertEqual(data.get("error"), "active_attempt",
                             f"동시 거부 코드가 active_attempt가 아니다: {data!r}")
            self.assertNotEqual(rc, 0, "거부 응답의 exit code가 0이다")

        # ledger 무손상 + 카운터 1회만 증가
        self.assertTrue(self.ws.runtime_json.exists(), "runtime.json이 사라졌다")
        ledger = self.read_ledger_file()
        self.assertIsInstance(ledger.get("revision"), int,
                              f"revision이 손상됐다: {ledger.get('revision')!r}")
        c = self.counters(ledger=ledger)
        self.assertEqual(c["attempt_count"], 1,
                         f"카운터가 1회만 증가해야 한다: {c['attempt_count']}")
        self.assertIsNotNone(c["active_attempt_id"], "허가됐는데 active attempt가 없다")


# ─────────────────────────────────────────────────────────────────────────────
# S-19 — receipt 없는 done 기록 금지 (AC-12, C-2)
# ─────────────────────────────────────────────────────────────────────────────
class TestReceiptGate(_Base):

    def _assert_no_done_recorded(self, label):
        text = json.dumps(self.ledger(), ensure_ascii=False)
        self.assertNotIn('"done"', text, f"[{label}] receipt 없이 done이 기록됐다")

    def test_s19_finish_without_start_is_rejected(self):
        """attempt-start 없이 attempt-finish → 전이 거부, done 기록 0건."""
        rc, stdout, data = self.admit("task-phase")
        self.assert_ok(rc, stdout, data, "admit")
        rc, stdout, data = self.finish("a1", status="done")
        self.assertTrue(stdout, "stdout이 비어 있다")
        self.assertNotIn("\n", stdout, f"다중 라인 출력 — 계약 위반: {stdout!r}")
        self.assertFalse(data.get("ok"), f"attempt-start 없는 finish가 허용됐다: {data!r}")
        self.assertTrue(data.get("error"), "오류 코드가 비어 있다")
        self.assertNotEqual(rc, 0, "exit code가 0이다")
        self._assert_no_done_recorded("finish-without-start")

    def test_s19_finish_with_unknown_attempt_id_is_rejected(self):
        """active attempt와 다른 attempt-id로 finish → 전이 거부, done 기록 0건."""
        rc, stdout, data = self.admit("task-phase")
        self.assert_ok(rc, stdout, data, "admit")
        rc, stdout, data = self.start("a1")
        self.assert_ok(rc, stdout, data, "attempt-start")
        rc, stdout, data = self.finish("a-bogus", status="done")
        self.assertFalse(data.get("ok"), f"미등록 attempt-id의 finish가 허용됐다: {data!r}")
        self.assertNotEqual(rc, 0, "exit code가 0이다")
        self._assert_no_done_recorded("unknown-attempt-id")

    def test_s19_only_attempt_finish_can_record_done(self):
        """대조군 — 정상 receipt 경로에서만 done이 기록된다."""
        self.cycle("a1", status="done")
        text = json.dumps(self.ledger(), ensure_ascii=False)
        self.assertIn('"done"', text, "정상 receipt 경로에서도 done이 기록되지 않았다")


# ─────────────────────────────────────────────────────────────────────────────
# S-26 — ledger 축 분리 (C-4, D4)
# ─────────────────────────────────────────────────────────────────────────────
class TestLedgerAxisSeparation(_Base):

    # D4 — ledger가 보유하는 집계 필드 전체
    ALLOWED_TOP_LEVEL = {
        "run_id", "revision", "status", "started_at", "deadline_at",
        "design_round", "project_dispatch_count",
        "cost_used", "wall_time_used", "budget_snapshot",
        "schema_version",
    }

    # 저장 금지 — attempt 원문과 3-SSOT 복제
    FORBIDDEN_KEY_SUBSTRINGS = [
        "pid", "pgid", "heartbeat", "fingerprint_source",
        "stdout", "stderr", "terminal_result", "result_json", "exitcode",
        "tasks", "rows", "scenarios", "acceptance_criteria",
        "current_status", "backlog", "test_scenario",
    ]

    def _seed_sibling_ssots(self):
        """같은 태스크 폴더에 3-SSOT를 심어 복제 여부를 문자열로 검출한다."""
        (self.ws.task_path / "backlog.json").write_text(json.dumps({
            "tasks": [{"id": TASK_ID, "title": "SENTINEL-BACKLOG-TITLE",
                       "status": "in_progress"}]
        }, ensure_ascii=False), encoding="utf-8")
        (self.ws.task_path / "test-scenario.json").write_text(json.dumps({
            "scenarios": [{"id": "S-1", "result": "SENTINEL-SCENARIO-RESULT"}]
        }, ensure_ascii=False), encoding="utf-8")
        state = json.loads((self.ws.task_path / "state.json").read_text(encoding="utf-8"))
        state["rows"] = [{"step": "T3", "status": "SENTINEL-STATE-ROW"}]
        (self.ws.task_path / "state.json").write_text(
            json.dumps(state, ensure_ascii=False), encoding="utf-8")

    def test_s26_ledger_holds_aggregates_only(self):
        self._seed_sibling_ssots()
        self.cycle("a1", status="failed", cost_usd=0.25,
                   exit_class="impl_failure", verifier_id="pytest",
                   command_id="cmd-unit", error_code="assertion_failed",
                   contract_revision="r7", failing_scenarios=json.dumps(["S-1"]))

        ledger = self.read_ledger_file()
        text = json.dumps(ledger, ensure_ascii=False)

        # ① 3-SSOT 값 복제 0건
        for sentinel in ("SENTINEL-BACKLOG-TITLE", "SENTINEL-SCENARIO-RESULT",
                         "SENTINEL-STATE-ROW"):
            self.assertNotIn(sentinel, text, f"3-SSOT 값 {sentinel}이 ledger에 복제됐다")

        # ② 금지 키 0건
        keys = {k.lower() for k in collect_keys(ledger)}
        for bad in self.FORBIDDEN_KEY_SUBSTRINGS:
            hits = [k for k in keys if bad in k]
            self.assertEqual(hits, [], f"ledger에 저장 금지 필드가 있다: {hits}")

        # ③ attempt record는 경로 외래 참조로만 존재
        c = self.counters(ledger=ledger)
        self.assertIn("active_attempt_id", c)
        paths = [v for v in _flat_strings(ledger) if v.endswith(".attempt.json")]
        self.assertTrue(paths, "attempt record 경로 외래 참조가 없다")

        # ④ ledger는 집계 ledger이므로 attempt 원문을 인라인할 만큼 커지지 않는다
        self.assertLess(
            len(text), 8192,
            "ledger가 집계값 범위를 넘어섰다 — attempt 원문 인라인 의심",
        )

    def test_s26_top_level_keys_are_bounded(self):
        self.cycle("a1", status="failed")
        ledger = self.read_ledger_file()
        extra = set(ledger) - self.ALLOWED_TOP_LEVEL
        # 카운터 컨테이너 1개(task·phase별 집계)와 실패 지문 컨테이너 1개만 추가 허용
        self.assertLessEqual(
            len(extra), 2,
            f"D4가 정의하지 않은 최상위 필드가 있다: {sorted(extra)}",
        )


def _flat_strings(node, out=None):
    if out is None:
        out = []
    if isinstance(node, dict):
        for v in node.values():
            _flat_strings(v, out)
    elif isinstance(node, list):
        for v in node:
            _flat_strings(v, out)
    elif isinstance(node, str):
        out.append(node)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# S-34 — T4b 3분기 전이 차감 (AC-8, AC-6)
# ─────────────────────────────────────────────────────────────────────────────
class TestT4bTransitionDeduction(_Base):

    RUNTIME_OVERRIDES = {"max_task_attempts": 20, "max_project_dispatches": 20}

    BRANCHES = ["impl_defect", "contract_defect", "policy_conflict"]

    def test_s34_every_branch_deducts_both_counters(self):
        """3분기 어느 경로든 task attempt와 project dispatch가 함께 1씩 증가한다."""
        for i, branch in enumerate(self.BRANCHES, start=1):
            before_ledger = self.ledger()
            before_dispatch = before_ledger.get("project_dispatch_count")
            self.assertIsInstance(
                before_dispatch, int,
                f"project_dispatch_count가 정수가 아니다: {before_dispatch!r}")
            before_attempt = self.counters(phase="t4b", ledger=before_ledger)["attempt_count"] \
                if _has_counter(before_ledger, TASK_ID, "t4b") else 0

            rc, stdout, data = self.admit("task-phase", phase="t4b")
            self.assert_ok(rc, stdout, data, f"admit t4b ({branch})")
            rc, stdout, data = self.start(f"b{i}", phase="t4b")
            self.assert_ok(rc, stdout, data, f"attempt-start t4b ({branch})")
            rc, stdout, data = self.finish(
                f"b{i}", status="failed", phase="t4b", t4b_branch=branch,
                exit_class="impl_failure", verifier_id="gate", command_id="cmd-t4b",
                error_code=f"code-{branch}", contract_revision="r7",
                failing_scenarios=json.dumps(["S-1"]),
            )
            self.assert_ok(rc, stdout, data, f"attempt-finish t4b ({branch})")

            after_ledger = self.ledger()
            after_dispatch = after_ledger.get("project_dispatch_count")
            after_attempt = self.counters(phase="t4b", ledger=after_ledger)["attempt_count"]

            # subTest를 쓰지 않는다 — pytest가 subTest 실패를 내면서도 테스트를
            # PASSED로 집계해 거짓 GREEN이 만들어진다.
            self.assertEqual(
                after_attempt - before_attempt, 1,
                f"[{branch}] task attempt 카운터가 1 증가하지 않았다")
            self.assertEqual(
                after_dispatch - before_dispatch, 1,
                f"[{branch}] project dispatch 카운터가 1 증가하지 않았다 "
                f"(어느 한쪽만 차감되는 경로 0건이어야 한다)")

    def test_s34_dispatch_limit_reached_via_t4b_rejects_next_admit(self):
        """T4b 차감으로 project dispatch 상한에 도달하면 다음 admit이 거부된다."""
        self.ws.cleanup()
        self.ws = Workspace()
        self.addCleanup(self.ws.cleanup)
        self.ws.write_global(valid_runtime(max_project_dispatches=1, max_task_attempts=20))
        self.ws.write_state()
        self.init_ledger()

        rc, stdout, data = self.admit("task-phase", phase="t4b")
        self.assert_ok(rc, stdout, data, "admit t4b")
        rc, stdout, data = self.start("b1", phase="t4b")
        self.assert_ok(rc, stdout, data, "attempt-start t4b")
        rc, stdout, data = self.finish("b1", status="failed", phase="t4b",
                                       t4b_branch="policy_conflict")
        self.assert_ok(rc, stdout, data, "attempt-finish t4b")

        rc, stdout, data = self.admit("dispatch")
        self.assert_rejected(rc, stdout, data, "attempt_limit_exceeded",
                             "dispatch after t4b deduction")


def _has_counter(ledger, task_id, phase):
    found = []

    def walk(n, trail):
        if isinstance(n, dict):
            if "attempt_count" in n:
                key = "/".join(str(t) for t in trail)
                if task_id in key and phase in [str(t) for t in trail]:
                    found.append(n)
            for k, v in n.items():
                walk(v, trail + [k])
        elif isinstance(n, list):
            for i, v in enumerate(n):
                walk(v, trail + [str(i)])

    walk(ledger, [])
    return bool(found)


# ─────────────────────────────────────────────────────────────────────────────
# S-11 (ledger 측면) — cost_used는 terminal candidate 값이며 합산이 아니다 (AC-15, C-10)
# ─────────────────────────────────────────────────────────────────────────────
class TestLedgerCostUsed(_Base):
    """fixture ②의 adapter 측 판정은 다른 워커가 담당한다. 여기서는 ledger 저장값만 본다.

    fixture ②는 같은 session_id에 result_index 0(선행 turn, total_cost_usd 0)과
    1(terminal candidate, 양수)을 갖는다. adapter가 terminal candidate 값만 넘기므로
    ledger는 넘겨받은 값을 그대로 저장해야 하며, 자체적으로 배수·합산을 하지 않는다.
    """

    NON_TERMINAL_COST = 0.0
    TERMINAL_COST = 0.0731

    def test_s11_cost_used_equals_terminal_candidate_value(self):
        self.cycle("a1", status="done", cost_usd=self.TERMINAL_COST)
        cost = self.ledger().get("cost_used")
        self.assertIsInstance(cost, (int, float), f"cost_used가 수치가 아니다: {cost!r}")
        self.assertAlmostEqual(
            cost, self.TERMINAL_COST, places=6,
            msg=f"cost_used가 terminal candidate 값과 다르다: {cost!r}")
        self.assertNotAlmostEqual(
            cost, self.TERMINAL_COST + self.NON_TERMINAL_COST + self.TERMINAL_COST, places=6,
            msg="cost_used가 중복 합산됐다")

    def test_s11_cost_used_is_not_multiplied_by_stream_result_count(self):
        """attempt 1건은 cost를 정확히 1회만 반영한다(stream 안의 result 개수와 무관)."""
        self.cycle("a1", status="failed", cost_usd=self.TERMINAL_COST)
        first = self.ledger().get("cost_used")
        self.assertAlmostEqual(first, self.TERMINAL_COST, places=6)

        self.cycle("a2", status="done", cost_usd=self.TERMINAL_COST)
        second = self.ledger().get("cost_used")
        self.assertAlmostEqual(
            second, self.TERMINAL_COST * 2, places=6,
            msg="run 누적 cost_used가 attempt별 terminal candidate 값의 합이 아니다")


if __name__ == "__main__":
    unittest.main()
