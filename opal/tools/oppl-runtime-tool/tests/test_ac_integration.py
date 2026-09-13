"""
@header {
  "module": "test_ac_integration",
  "task": "131",
  "layer": "test",
  "domain": "opal-tools",
  "description": "도구 경계를 넘는 결합만 검증하는 통합 테스트(PLAN W-12 / AC-20). 각 도구의 단위 테스트가 이미 덮는 단일 도구 행위는 복제하지 않고([MUST] PRINCIPLES §2), state-tool·opal-agent·oppl-runtime-tool·opal-action-monitor 4개 도구가 실제 프로세스로 주고받는 4개 결합만 관측한다 — ① run identity 외래 참조(state-tool run-start → oppl init --run-id → show), ② attempt record ↔ ledger 소유권 분리(opal-agent --run-dir가 만든 실 attempt.json을 attempt-start --record-path로 참조시키고 ledger에 PID·PGID·heartbeat·terminal 원문 부재와 cost_used 비합산 확인), ③ monitor 위임(픽스처가 아니라 앞 두 결합이 만든 실제 runtime.json·산출물로 7종 enum·읽기 전용 확인), ④ CLI 상한 경계(run.sh 실행으로 프로세스 생성 0건 거부와 실제 timeout 후 PGID 전체 소멸이 ledger timed_out으로 이어짐), ⑤ 다중 프로세스 동시 admit 이후의 attempt-start 바인딩. mock·patch를 쓰지 않고 provider CLI(claude)는 호출하지 않는다 — 더미 셸 스크립트를 --bin으로 주입한다.",
  "scenarios": ["S-24", "S-27", "S-29", "S-30"],
  "exports": [
    "TestRunIdentityBinding", "TestAttemptRecordLedgerBinding",
    "TestMonitorDelegationOnRealArtifacts", "TestCliTimeoutBoundary",
    "TestConcurrentAdmitBinding"
  ]
}

검증 대상과 경계
----------------
- 공개 인터페이스만 단언한다 — 각 도구 `run.sh`의 exit code·stdout과 실 파일 상태.
  내부 함수 import·mock·patch를 쓰지 않는다(red-first.md §4).
- 단일 도구 안에서 닫히는 계약은 이 파일의 몫이 아니다. 상한 거부·지문·설정 로더는
  `test_oppl_runtime_admission.py`·`test_oppl_runtime_config.py`가, watchdog·adapter 판정은
  `opal-agent/tests/`가, 위임 렌더 문법은 `opal-action-monitor/tests/`가 소유한다.
  이 파일은 그 파일들을 열지도 수정하지도 않는다.
- [MUST] PRINCIPLES §4 "Don't fake it" — 프로세스 수명주기·PGID·파일 lock·직렬화에
  대역을 쓰지 않는다. PGID 소멸은 실제 `killpg(pgid, 0)`의 ProcessLookupError로만 확정한다.
- provider CLI 대역 범위는 TEST-SCENARIO.md §Setup "대역 사용과 한계"에 명시된
  provider 프로세스 1건으로 한정한다.
- timeout·grace는 테스트 전용 소값(1~3초)을 주입해 총 실행 시간을 제한한다
  (PLAN §검증 전략 "실측 경계").
- 임시 디렉토리만 쓴다 — 프로젝트 파일과 `~/.opal/`을 건드리지 않는다(C-6).

근거
  PLAN.md W-12(통합 검증), D4(attempt record ↔ ledger 소유권 분리),
  D7(monitor 위임), D8/C-5(run identity 외래 참조), C-10(cost_used 비합산)
  TEST-SCENARIO.md S-29(AC-20 — mock 전용 통과 0건), S-24 §Setup 대역 경계
"""

import hashlib
import json
import os
import pathlib
import shutil
import signal
import stat
import subprocess
import tempfile
import time
import unittest

_TOOLS_DIR = pathlib.Path(__file__).resolve().parents[2]
_OPPL_RUN_SH = _TOOLS_DIR / "oppl-runtime-tool" / "run.sh"
_STATE_RUN_SH = _TOOLS_DIR / "state-tool" / "run.sh"
_AGENT_RUN_SH = _TOOLS_DIR / "opal-agent" / "run.sh"
_MONITOR_RUN_SH = _TOOLS_DIR / "opal-action-monitor" / "run.sh"

REGISTERED_PHASES = ["t1", "t2", "g", "t3", "t4a", "t4b"]

# 제안서 §5 / PLAN D7 — phase status 폐쇄 집합
STATUS_ENUM_7 = {"pending", "running", "done", "failed", "error", "blocked", "timed_out"}

TASK_ID = "T-131"

# stream fixture — terminal candidate는 마지막 유효 result다(제안서 §7.2).
# 선행 result와 비용이 다르므로 합산(1.25)과 candidate 값(0.75)이 구분된다(C-10).
_SESSION = "00000000-0000-4000-8000-0000000000c1"
PRECEDING_COST = 0.5
TERMINAL_COST = 0.75


def _result_event(index, cost):
    return {
        "type": "result", "subtype": "success", "is_error": False,
        "result": "integration fixture", "result_index": index, "num_turns": index + 1,
        "terminal_reason": "completed", "api_error_status": None,
        "total_cost_usd": cost, "duration_ms": 1000,
        "session_id": _SESSION,
        "uuid": "00000000-0000-4000-8000-00000000007%d" % index,
    }


STREAM_LINES = [
    {"type": "system", "subtype": "init", "session_id": _SESSION,
     "uuid": "00000000-0000-4000-8000-000000000011"},
    _result_event(0, PRECEDING_COST),
    _result_event(1, TERMINAL_COST),
    # candidate 뒤 epilogue allowlist — 판정을 뒤집지 않는다.
    {"type": "system", "subtype": "task_notification", "task_id": "bg01",
     "status": "completed", "session_id": _SESSION,
     "uuid": "00000000-0000-4000-8000-000000000015"},
]

SYNC_RESULT_JSON = json.dumps(_result_event(0, TERMINAL_COST))


def valid_runtime(**overrides):
    """등록 phase 전체를 채운 유효 `oppl.runtime` 블록(D6 — 부분 map은 결손이다)."""
    base = {
        "max_design_rounds": 5,
        "max_project_dispatches": 20,
        "max_task_attempts": 4,
        "max_identical_failures": 3,
        "max_wall_time_sec": 3600,
        "heartbeat_timeout_sec": 120,
        "hard_timeout_sec_by_phase": {p: 600 for p in REGISTERED_PHASES},
        "max_hard_timeout_sec": 1800,
        "terminate_grace_sec": 1,
    }
    base.update(overrides)
    return base


def _parse(proc):
    stdout = proc.stdout.strip()
    try:
        return json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        return {"_raw": stdout}


def _sha256_tree(directory):
    """디렉토리 하위 전 파일의 상대경로 → SHA-256 맵."""
    digests = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            digests[str(path.relative_to(directory))] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return digests


def killpg_alive(pgid):
    """PGID 생존 여부 — 소멸은 ProcessLookupError로만 확정한다."""
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class Workspace:
    """실제 프로젝트 레이아웃을 흉내낸 임시 작업공간. 프로젝트 파일을 건드리지 않는다."""

    def __init__(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="oppl-ac-int-"))
        self.opal_home = self.tmp / "opal-home"
        self.opal_home.mkdir(parents=True)
        self.project_root = self.tmp / "project"
        (self.project_root / ".opal").mkdir(parents=True)
        self.task_path = self.project_root / "tasks" / "131-260914-oppl-integration"
        self.task_path.mkdir(parents=True)
        self.bin_dir = self.tmp / "bin"
        self.bin_dir.mkdir()
        self._pgids = []

    # ── 정리 ─────────────────────────────────────────────────────────────
    def cleanup(self):
        for pgid in self._pgids:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def record_pgid(self, pgid):
        if isinstance(pgid, int) and pgid > 0:
            self._pgids.append(pgid)

    # ── 환경 ─────────────────────────────────────────────────────────────
    def env(self, **extra):
        e = dict(os.environ)
        e["OPAL_HOME"] = str(self.opal_home)
        e.update(extra)
        return e

    def write_global_setting(self, runtime=None):
        (self.opal_home / "setting.json").write_text(
            json.dumps({"oppl": {"runtime": runtime or valid_runtime()}}, ensure_ascii=False),
            encoding="utf-8",
        )

    @property
    def run_dir(self):
        return self.task_path / ".oppl-run"

    @property
    def runtime_json(self):
        return self.run_dir / "runtime.json"

    def read_ledger(self):
        return json.loads(self.runtime_json.read_text(encoding="utf-8"))

    # ── 더미 provider 스크립트 ───────────────────────────────────────────
    def script(self, name, body):
        path = self.bin_dir / name
        path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return str(path)

    def stream_script(self, name="stream_ok.sh"):
        payload = self.tmp / "stream.jsonl"
        payload.write_text(
            "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in STREAM_LINES),
            encoding="utf-8",
        )
        return self.script(name, f'cat "{payload}"\n')

    def grandchild_script(self, name="silent_grandchild.sh", sleep_sec=120):
        """손자 프로세스를 fork하고 둘 다 무출력으로 대기하는 스크립트."""
        marker = self.tmp / f"{name}.spawned"
        body = (
            f': > "{marker}"\n'
            f"sh -c 'sleep {sleep_sec}' &\n"
            f"sleep {sleep_sec}\n"
        )
        return self.script(name, body), marker

    # ── 도구 호출 ────────────────────────────────────────────────────────
    def state_tool(self, *args, timeout=120):
        return subprocess.run(
            ["bash", str(_STATE_RUN_SH), *[str(a) for a in args]],
            capture_output=True, text=True, timeout=timeout,
        )

    def oppl(self, *args, timeout=60):
        return subprocess.run(
            ["bash", str(_OPPL_RUN_SH), *[str(a) for a in args]],
            capture_output=True, text=True, timeout=timeout,
            env=self.env(), cwd=str(self.project_root),
        )

    def oppl_task(self, *args, **kw):
        return self.oppl(args[0], "--task-path", str(self.task_path), *args[1:], **kw)

    def agent(self, *args, timeout=180):
        return subprocess.run(
            ["bash", str(_AGENT_RUN_SH), *[str(a) for a in args]],
            capture_output=True, text=True, timeout=timeout, env=self.env(),
        )

    def monitor(self, *args, timeout=60):
        return subprocess.run(
            ["bash", str(_MONITOR_RUN_SH), *[str(a) for a in args]],
            capture_output=True, text=True, timeout=timeout, env=self.env(),
        )

    # ── 조립 ─────────────────────────────────────────────────────────────
    def init_state(self):
        """state.json은 state-tool로만 만든다(CONVENTIONS §State 관리)."""
        proc = self.state_tool(
            "init", self.task_path, "--skill", "oppl", "--mode", "agentic",
            "--rows-spec", json.dumps([{"stage": "PLAN", "item": "통합 검증"}]),
        )
        assert proc.returncode == 0, f"state-tool init 실패: {proc.stdout} {proc.stderr}"
        return proc

    def run_start(self):
        proc = self.state_tool("run-start", self.task_path)
        assert proc.returncode == 0, f"run-start 실패: {proc.stdout} {proc.stderr}"
        return _parse(proc)["run_id"]

    def attempt_record(self, stem):
        return json.loads((self.run_dir / f"{stem}.attempt.json").read_text(encoding="utf-8"))


def collect_keys(node, out=None):
    if out is None:
        out = set()
    if isinstance(node, dict):
        for key, value in node.items():
            out.add(key)
            collect_keys(value, out)
    elif isinstance(node, list):
        for value in node:
            collect_keys(value, out)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# ① run identity 결합 — state-tool → oppl-runtime-tool (C-5 / AC-12)
# ─────────────────────────────────────────────────────────────────────────────
class TestRunIdentityBinding(unittest.TestCase):
    """run_id의 발급자는 state-tool 하나뿐이고 ledger는 외래 참조만 갖는다."""

    def setUp(self):
        self.ws = Workspace()
        self.addCleanup(self.ws.cleanup)
        self.ws.write_global_setting()
        self.ws.init_state()

    def test_run_id_flows_from_state_tool_into_ledger_as_foreign_reference(self):
        run_id = self.ws.run_start()

        proc = self.ws.oppl_task("init", "--run-id", run_id)
        self.assertEqual(proc.returncode, 0, f"init 실패: {proc.stdout} {proc.stderr}")

        shown = _parse(self.ws.oppl_task("show"))
        self.assertTrue(shown.get("ok"), f"show 실패: {shown!r}")
        self.assertEqual(
            shown["runtime"]["run_id"], run_id,
            "ledger의 run_id가 state-tool 발급값과 다르다 — 외래 참조가 아니다(C-5).",
        )

        state = json.loads((self.ws.task_path / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            state["run_id"], shown["runtime"]["run_id"],
            "state.json과 ledger의 run_id가 갈라졌다 — 발급 주체가 둘이 됐다.",
        )

    def test_init_without_state_run_id_is_rejected_and_writes_no_ledger(self):
        """`run-start` 없이 온 init은 run_id를 발급하지 않고 거부한다(D8)."""
        proc = self.ws.oppl_task("init", "--run-id", "run-20260914000000-deadbeef")
        self.assertNotEqual(proc.returncode, 0, "run_id 없는 state.json에서 init이 통과했다.")
        data = _parse(proc)
        self.assertEqual(data.get("error"), "run_identity_missing", f"거부 코드 불일치: {data!r}")
        self.assertFalse(
            self.ws.runtime_json.exists(),
            "거부 경로에서 ledger가 생성됐다 — 실패한 init이 상태를 남겼다.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# ② attempt record ↔ ledger 결합 — opal-agent → oppl-runtime-tool (D4 / AC-15)
# ─────────────────────────────────────────────────────────────────────────────
class TestAttemptRecordLedgerBinding(unittest.TestCase):
    """opal-agent가 만든 실 attempt record를 ledger가 경로로만 참조한다."""

    PHASE = "t3"
    ATTEMPT_ID = "a1"

    @classmethod
    def setUpClass(cls):
        ws = cls.ws = Workspace()
        cls.addClassCleanup(ws.cleanup)
        ws.write_global_setting()
        ws.init_state()
        run_id = ws.run_start()

        proc = ws.oppl_task("init", "--run-id", run_id)
        assert proc.returncode == 0, f"init 실패: {proc.stdout} {proc.stderr}"

        # opal-agent가 `--run-dir`로 attempt 산출물의 단일 writer가 된다(D1).
        cls.agent_proc = ws.agent(
            "integration fixture prompt", "--stream",
            "--bin", ws.stream_script(),
            "--timeout", "20", "--terminate-grace-sec", "1",
            "--run-dir", str(ws.run_dir), "--phase", cls.PHASE,
        )
        assert cls.agent_proc.returncode == 0, (
            f"opal-agent 실행 실패: {cls.agent_proc.stderr[:400]!r}"
        )
        cls.record = ws.attempt_record(cls.PHASE)
        ws.record_pgid(cls.record.get("pgid"))

        assert _parse(ws.oppl_task(
            "admit", "--scope", "task-phase", "--task-id", TASK_ID, "--phase", cls.PHASE,
        )).get("ok"), "admit이 허가되지 않았다"

        assert _parse(ws.oppl_task(
            "attempt-start", "--task-id", TASK_ID, "--phase", cls.PHASE,
            "--attempt-id", cls.ATTEMPT_ID,
            "--record-path", str(ws.run_dir / f"{cls.PHASE}.attempt.json"),
        )).get("ok"), "attempt-start가 실패했다"

        cls.finish = _parse(ws.oppl_task(
            "attempt-finish", "--task-id", TASK_ID, "--phase", cls.PHASE,
            "--attempt-id", cls.ATTEMPT_ID, "--status", "done",
            # opal-agent가 판정한 terminal candidate 비용을 그대로 넘긴다(C-10).
            "--cost-usd", str(cls.record["cost_used"]),
        ))
        assert cls.finish.get("ok"), f"attempt-finish 실패: {cls.finish!r}"
        cls.ledger = ws.read_ledger()
        cls.phase_record = cls.ledger["counters"][TASK_ID]["phases"][cls.PHASE]

    def test_ledger_references_attempt_record_by_path_only(self):
        expected = str(self.ws.run_dir / f"{self.PHASE}.attempt.json")
        self.assertEqual(
            self.phase_record["record_path"], expected,
            "ledger가 attempt record 경로를 외래 참조로 갖지 않는다(D4).",
        )
        self.assertTrue(pathlib.Path(expected).is_file(), "참조된 attempt record가 실재하지 않는다.")

    def test_ledger_stores_no_attempt_runtime_originals(self):
        """PID·PGID·heartbeat·terminal result 원문은 attempt record 쪽에만 있다."""
        record_keys = collect_keys(self.record)
        for key in ("pid", "pgid", "heartbeat", "terminal", "exit_code"):
            self.assertIn(key, record_keys, f"attempt record에 {key}가 없다 — 전제 붕괴")

        ledger_keys = collect_keys(self.ledger)
        for key in ("pid", "pgid", "pgid_reclaimed", "heartbeat", "terminal",
                    "exit_code", "timeout_reason", "fingerprint"):
            self.assertNotIn(
                key, ledger_keys,
                f"ledger가 attempt 원문 필드 {key}를 복제했다 — 소유권 분리 위반(D4/C-4).",
            )

    def test_cost_used_is_terminal_candidate_value_not_a_sum(self):
        self.assertEqual(
            self.record["cost_used"], TERMINAL_COST,
            "opal-agent가 terminal candidate 비용을 잘못 골랐다.",
        )
        self.assertAlmostEqual(
            self.ledger["cost_used"], TERMINAL_COST, places=10,
            msg="ledger cost_used가 terminal candidate 값이 아니다(C-10).",
        )
        self.assertNotAlmostEqual(
            self.ledger["cost_used"], PRECEDING_COST + TERMINAL_COST, places=10,
            msg="ledger cost_used가 stream의 result 개수만큼 합산됐다(C-10 위반).",
        )


# ─────────────────────────────────────────────────────────────────────────────
# ③ monitor 위임 결합 — 실제 도구 산출물 기반 (AC-9 / C-3)
# ─────────────────────────────────────────────────────────────────────────────
class TestMonitorDelegationOnRealArtifacts(unittest.TestCase):
    """픽스처가 아니라 ①②가 만든 실물 `.oppl-run`으로 위임을 관측한다.

    위임 판별은 휴리스틱과 ledger 판정이 갈리는 phase로 한다 — `DIVERGENT_PHASE`는
    산출물이 하나도 없어 6상태 휴리스틱이라면 `pending`이지만, `attempt-start`가
    바인딩한 ledger는 `running`이다. 휴리스틱이 살아 있으면 이 단언이 깨진다.
    """

    PHASE = "t3"
    DIVERGENT_PHASE = "t2"

    @classmethod
    def setUpClass(cls):
        ws = cls.ws = Workspace()
        cls.addClassCleanup(ws.cleanup)
        ws.write_global_setting()
        ws.init_state()
        run_id = ws.run_start()
        assert ws.oppl_task("init", "--run-id", run_id).returncode == 0

        proc = ws.agent(
            "integration fixture prompt", "--stream",
            "--bin", ws.stream_script(),
            "--timeout", "20", "--terminate-grace-sec", "1",
            "--run-dir", str(ws.run_dir), "--phase", cls.PHASE,
        )
        assert proc.returncode == 0, f"opal-agent 실행 실패: {proc.stderr[:400]!r}"
        ws.record_pgid(ws.attempt_record(cls.PHASE).get("pgid"))

        _parse(ws.oppl_task("admit", "--scope", "task-phase",
                            "--task-id", TASK_ID, "--phase", cls.PHASE))
        _parse(ws.oppl_task("attempt-start", "--task-id", TASK_ID, "--phase", cls.PHASE,
                            "--attempt-id", "a1",
                            "--record-path", str(ws.run_dir / f"{cls.PHASE}.attempt.json")))
        finish = _parse(ws.oppl_task("attempt-finish", "--task-id", TASK_ID,
                                     "--phase", cls.PHASE, "--attempt-id", "a1",
                                     "--status", "done"))
        assert finish.get("ok"), f"attempt-finish 실패: {finish!r}"

        # 산출물 없는 phase를 running으로 바인딩한다 — 휴리스틱이라면 pending이다.
        _parse(ws.oppl_task("admit", "--scope", "task-phase",
                            "--task-id", TASK_ID, "--phase", cls.DIVERGENT_PHASE))
        started = _parse(ws.oppl_task(
            "attempt-start", "--task-id", TASK_ID, "--phase", cls.DIVERGENT_PHASE,
            "--attempt-id", "a1",
            "--record-path", str(ws.run_dir / f"{cls.DIVERGENT_PHASE}.attempt.json"),
        ))
        assert started.get("ok"), f"attempt-start 실패: {started!r}"
        cls.ledger = ws.read_ledger()

    def _phase_status(self, payload, phase):
        for entry in payload["phases"]:
            if entry["phase"] == phase:
                return entry["status"]
        self.fail(f"phase {phase}가 출력에 없다")

    def test_monitor_renders_ledger_status_without_rejudging(self):
        proc = self.ws.monitor(str(self.ws.task_path), "--json")
        self.assertEqual(proc.returncode, 0, f"monitor --json 실패: {proc.stderr[:400]!r}")
        payload = json.loads(proc.stdout)

        statuses = {entry["status"] for entry in payload["phases"]}
        self.assertTrue(
            statuses <= STATUS_ENUM_7,
            f"7종 enum 밖의 status가 나왔다: {statuses - STATUS_ENUM_7}",
        )
        phases = self.ledger["counters"][TASK_ID]["phases"]
        self.assertEqual(
            self._phase_status(payload, self.PHASE), phases[self.PHASE]["status"],
            "monitor가 ledger status를 그대로 쓰지 않고 재판정했다(D7).",
        )

        # 산출물 0건 phase — 휴리스틱 pending vs ledger running. 위임이 없으면 갈린다.
        self.assertEqual(phases[self.DIVERGENT_PHASE]["status"], "running")
        self.assertFalse(
            list(self.ws.run_dir.glob(f"{self.DIVERGENT_PHASE}.*")),
            f"{self.DIVERGENT_PHASE}에 산출물이 있어 판별이 항진명제가 된다 — 전제 붕괴",
        )
        self.assertEqual(
            self._phase_status(payload, self.DIVERGENT_PHASE), "running",
            "산출물 없는 phase가 휴리스틱 pending으로 렌더됐다 — 위임 미적용(D7).",
        )
        self.assertEqual(
            payload["runtime"]["run_id"], self.ledger["run_id"],
            "monitor가 렌더한 run_id가 ledger와 다르다.",
        )

    def test_monitor_writes_nothing_in_either_output_mode(self):
        before = _sha256_tree(self.ws.run_dir)
        self.assertTrue(before, ".oppl-run이 비어 있다 — 전제 붕괴")

        text_proc = self.ws.monitor(str(self.ws.task_path))
        self.assertEqual(text_proc.returncode, 0, f"monitor 텍스트 실패: {text_proc.stderr[:400]!r}")
        json_proc = self.ws.monitor(str(self.ws.task_path), "--json")
        self.assertEqual(json_proc.returncode, 0, f"monitor --json 실패: {json_proc.stderr[:400]!r}")

        self.assertEqual(
            before, _sha256_tree(self.ws.run_dir),
            "monitor 실행 전후 .oppl-run 파일 해시가 달라졌다 — 읽기 전용 위반(C-3).",
        )


# ─────────────────────────────────────────────────────────────────────────────
# ④ timeout 상한 경계 결합 — CLI 거부와 실제 PGID 소멸 → ledger (AC-1)
# ─────────────────────────────────────────────────────────────────────────────
class TestCliTimeoutBoundary(unittest.TestCase):
    """run.sh 실행 경로에서 상한 거부는 프로세스 0건, 초과 실행은 PGID 전체 소멸이다."""

    def setUp(self):
        self.ws = Workspace()
        self.addCleanup(self.ws.cleanup)
        self.ws.write_global_setting()
        self.ws.init_state()
        run_id = self.ws.run_start()
        self.assertEqual(self.ws.oppl_task("init", "--run-id", run_id).returncode, 0)

    def test_request_over_max_timeout_spawns_no_process(self):
        script, marker = self.ws.grandchild_script("reject_probe.sh")
        started = time.monotonic()
        proc = self.ws.agent(
            "integration fixture prompt", "--json",
            "--bin", script,
            "--timeout", "120", "--max-timeout-sec", "2",
            "--run-dir", str(self.ws.run_dir), "--phase", "t1",
        )
        elapsed = time.monotonic() - started

        self.assertEqual(proc.returncode, 2, f"stderr={proc.stderr[:400]!r}")
        self.assertIn("timeout_limit_exceeded", proc.stderr)
        self.assertLess(elapsed, 30, "거부 경로가 자식 프로세스를 기다렸다.")
        self.assertFalse(
            marker.exists(),
            "상한 초과 요청에서 provider 프로세스가 생성됐다(spawn marker 존재).",
        )
        self.assertFalse(
            (self.ws.run_dir / "t1.attempt.json").exists(),
            "거부 경로가 attempt 산출물을 남겼다.",
        )

    def test_real_timeout_reclaims_whole_pgid_and_binds_timed_out_to_ledger(self):
        phase = "t4a"
        script, marker = self.ws.grandchild_script("timeout_probe.sh")
        proc = self.ws.agent(
            "integration fixture prompt", "--json",
            "--bin", script,
            "--timeout", "1", "--terminate-grace-sec", "1", "--max-timeout-sec", "30",
            "--run-dir", str(self.ws.run_dir), "--phase", phase,
        )
        self.assertEqual(proc.returncode, 2, f"stderr={proc.stderr[:400]!r}")
        self.assertTrue(marker.exists(), "provider 대역 프로세스가 뜨지 않았다 — 전제 붕괴")

        record = self.ws.attempt_record(phase)
        pgid = record["pgid"]
        self.ws.record_pgid(pgid)
        self.assertEqual(record["status"], "timed_out", f"attempt record: {record!r}")
        self.assertTrue(record["pgid_reclaimed"], "PGID 회수가 확정되지 않았다.")
        # 손자까지 포함한 process group 전체 소멸은 ProcessLookupError로만 확정한다.
        self.assertRaises(ProcessLookupError, os.killpg, pgid, 0)
        self.assertFalse(killpg_alive(pgid))

        _parse(self.ws.oppl_task("admit", "--scope", "task-phase",
                                 "--task-id", TASK_ID, "--phase", phase))
        _parse(self.ws.oppl_task("attempt-start", "--task-id", TASK_ID, "--phase", phase,
                                 "--attempt-id", "a1",
                                 "--record-path", str(self.ws.run_dir / f"{phase}.attempt.json")))
        finish = _parse(self.ws.oppl_task(
            "attempt-finish", "--task-id", TASK_ID, "--phase", phase,
            "--attempt-id", "a1", "--status", "timed_out",
            "--exit-class", record["exit_class"],
        ))
        self.assertTrue(finish.get("ok"), f"attempt-finish 실패: {finish!r}")

        monitor = self.ws.monitor(str(self.ws.task_path), "--json")
        self.assertEqual(monitor.returncode, 0, f"monitor 실패: {monitor.stderr[:400]!r}")
        rendered = {e["phase"]: e["status"] for e in json.loads(monitor.stdout)["phases"]}
        self.assertEqual(
            rendered[phase], "timed_out",
            "실제 timeout이 ledger를 거쳐 monitor의 timed_out으로 이어지지 않았다.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# ⑤ 동시성 결합 — 실 다중 프로세스 admit 이후의 attempt-start 바인딩 (AC-11)
# ─────────────────────────────────────────────────────────────────────────────
class TestConcurrentAdmitBinding(unittest.TestCase):

    CONCURRENCY = 6
    PHASE = "t3"

    def setUp(self):
        self.ws = Workspace()
        self.addCleanup(self.ws.cleanup)
        self.ws.write_global_setting()
        self.ws.init_state()
        run_id = self.ws.run_start()
        self.assertEqual(self.ws.oppl_task("init", "--run-id", run_id).returncode, 0)

    def test_single_admission_survives_concurrency_and_gates_attempt_start(self):
        args = [
            "bash", str(_OPPL_RUN_SH), "admit",
            "--task-path", str(self.ws.task_path),
            "--scope", "task-phase",
            "--task-id", TASK_ID, "--phase", self.PHASE,
        ]
        procs = [
            subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, env=self.ws.env(), cwd=str(self.ws.project_root))
            for _ in range(self.CONCURRENCY)
        ]
        results = []
        for proc in procs:
            out, _err = proc.communicate(timeout=120)
            stdout = out.strip()
            try:
                data = json.loads(stdout) if stdout else {}
            except json.JSONDecodeError:
                data = {"_raw": stdout}
            results.append((proc.returncode, data))

        granted = [r for r in results if r[1].get("ok") is True]
        rejected = [r for r in results if r[1].get("ok") is False]
        self.assertEqual(len(granted), 1, f"정확히 1건만 허가되어야 한다 — {len(granted)}건")
        self.assertEqual(len(rejected), self.CONCURRENCY - 1, "나머지가 모두 거부되지 않았다.")
        for returncode, data in rejected:
            self.assertEqual(data.get("error"), "active_attempt", f"거부 코드 불일치: {data!r}")
            self.assertNotEqual(returncode, 0, "거부 응답의 exit code가 0이다.")

        record = self.ws.read_ledger()["counters"][TASK_ID]["phases"][self.PHASE]
        self.assertEqual(record["attempt_count"], 1, "카운터가 1회만 증가하지 않았다.")
        self.assertIsNotNone(record["active_attempt_id"], "허가됐는데 active attempt가 없다.")

        # 허가 1건이 실제 attempt로 바인딩된 뒤에는 두 번째 바인딩이 막힌다.
        first = _parse(self.ws.oppl_task(
            "attempt-start", "--task-id", TASK_ID, "--phase", self.PHASE,
            "--attempt-id", "a1",
            "--record-path", str(self.ws.run_dir / f"{self.PHASE}.attempt.json"),
        ))
        self.assertTrue(first.get("ok"), f"허가된 attempt-start가 실패했다: {first!r}")

        second = self.ws.oppl_task(
            "attempt-start", "--task-id", TASK_ID, "--phase", self.PHASE,
            "--attempt-id", "a2",
            "--record-path", str(self.ws.run_dir / f"{self.PHASE}.a2.attempt.json"),
        )
        self.assertNotEqual(second.returncode, 0, "예약 없는 attempt-start가 통과했다.")
        self.assertEqual(
            _parse(second).get("error"), "active_attempt",
            "이미 시작된 attempt 위에 두 번째 바인딩이 허용됐다.",
        )


if __name__ == "__main__":
    unittest.main()
