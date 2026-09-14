"""
@header {
  "module": "test_monitor_delegation",
  "task": "131",
  "layer": "test",
  "domain": "opal-tools",
  "description": "opal-action-monitor 7상태 위임·읽기 전용 계약 RED-first 테스트 — PLAN D7 / W-8 / TEST-SCENARIO S-21. 픽스처는 실제 oppl-runtime-tool ledger 스키마(counters.<task_id>.phases.<phase> 중첩)를 그대로 쓴다. `.oppl-run/runtime.json`이 있으면 monitor가 자체 재판정 없이 ledger의 phase별 status(7종 enum)와 잔여 상한만 렌더하는지, 없으면 기존 6상태 휴리스틱을 유지하고 timed_out을 출력하지 않는지, 그리고 두 경로 모두 실행 전후 .oppl-run 전 파일 SHA-256이 동일한지(텍스트·--json 양쪽) 검증한다. RED 상태(위임 경로 미구현, TERMINAL_STATUSES에 timed_out 없음) — 위임 테스트는 FAIL 예상. GREEN 전환은 EXECUTE 구현 워커 담당(작성자!=구현자, red-first.md §2).",
  "scenarios": ["S-21"],
  "exports": ["TestT131RuntimeDelegation", "TestT131LegacyHeuristicFallback", "TestT131ReadOnlyInvariant", "TestT131TerminalStatuses"]
}

검증 대상: opal/tools/opal-action-monitor/run.sh 의 공개 인터페이스(exit code + stdout)와
실 파일 상태(.oppl-run 하위 전 파일의 SHA-256)만 단언한다.
내부 함수 mock/patch 금지(red-first.md §4) — subprocess 실호출과 실제 해시 계산만 사용한다.

ledger 스키마: 픽스처는 실제 `oppl-runtime-tool`(W-3+W-6)이 쓰는 `.oppl-run/runtime.json`과
동일한 키 구조를 쓴다 — phase 레코드 경로는 **`counters.<task_id>.phases.<phase>`** 중첩이고
(제안서 §4.1 "task·phase별"), 최상위 평면 `phases`나 `tasks` 키는 존재하지 않는다.
실제 도구가 생성한 ledger와 키 구조를 대조해 확정했다.

위임 판별 설계: 픽스처는 휴리스틱 판정과 ledger 판정이 **서로 다르도록** 구성한다.
  - t1: `.exitcode`=0 → 휴리스틱 done / ledger `timed_out`  → 출력이 timed_out이어야 위임이 증명된다
  - t3: 산출물 없음 → 휴리스틱 pending / ledger `running`
  - t4a: `.exitcode`=1 → 휴리스틱 failed / ledger `blocked`
휴리스틱이 그대로 살아있으면 위 셋 중 어느 것도 ledger 값과 일치하지 않는다.

[MUST] C-3 읽기 전용: monitor는 `.oppl-run/`에 아무 것도 쓰지 않는다.
[MUST] 표준 라이브러리만 import.
"""

import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"

# 제안서 §5 / PLAN D7 — 상태 7종 고정
STATUS_ENUM_7 = {"pending", "running", "done", "failed", "error", "blocked", "timed_out"}
# 기존 휴리스틱이 낼 수 있는 6종 (timed_out 없음)
STATUS_ENUM_6 = {"pending", "running", "done", "failed", "error", "blocked"}

PHASES = ["t1", "t2", "g", "t3", "t4a", "t4b"]

RUN_ID = "run-20260914010203-0a1b2c3d"

# ledger `counters`의 task 축 — 이 픽스처는 단일 task만 담는다(다중 task 선택 규칙은 S-21 범위 밖).
LEDGER_TASK_ID = "T-1"

# PLAN D4 / 제안서 §4.1 — ledger는 집계값과 예산 상한만 보유한다(원문 복제 금지).
# 실제 `oppl-runtime-tool`(W-3+W-6) `ledger.BUDGET_SNAPSHOT_KEYS`와 동일 키 집합.
# heartbeat·timeout 계열은 의도적으로 없다 — attempt wrapper 소유 축이다.
BUDGET_SNAPSHOT = {
    "max_design_rounds": 5,
    "max_project_dispatches": 20,
    "max_task_attempts": 3,
    "max_identical_failures": 2,
    "max_wall_time_sec": 3600,
    "max_cost_usd": 10.0,
}

# 휴리스틱과 의도적으로 어긋나게 설계한 위임 판정 (파일 상단 주석 참조)
LEDGER_PHASE_STATUS = {
    "t1": "timed_out",
    "t2": "done",
    "g": "error",
    "t3": "running",
    "t4a": "blocked",
    "t4b": "pending",
}


def _run(args):
    """run.sh subprocess 실호출 → CompletedProcess."""
    return subprocess.run(
        ["bash", str(_RUN_SH)] + [str(a) for a in args],
        capture_output=True, text=True,
    )


def _hash_tree(root: pathlib.Path) -> dict:
    """디렉토리 하위 전 파일의 상대경로 → SHA-256 맵."""
    digests = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digests[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


class _RunDirCase(unittest.TestCase):
    """`.oppl-run/` 실행 증거 픽스처 — runtime.json 유무만 다르다."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="t131-monitor-")
        self.task_folder = pathlib.Path(self.tmp) / "003-260914-oppl-monitor"
        self.run_dir = self.task_folder / ".oppl-run"
        self.run_dir.mkdir(parents=True)
        self._seed_evidence()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _seed_evidence(self):
        """휴리스틱이 done/…/failed/pending을 내도록 실행 증거를 깐다."""
        # t1: stream 축 + exitcode 0 → 휴리스틱 done
        (self.run_dir / "t1.prompt.txt").write_text("t1 프롬프트\n", encoding="utf-8")
        (self.run_dir / "t1.events.jsonl").write_text(
            json.dumps({"type": "assistant", "message": {"content": []}}, ensure_ascii=False) + "\n"
            + json.dumps({
                "type": "result", "subtype": "success", "is_error": False,
                "total_cost_usd": 0.12, "session_id": "sess-t1-0001",
            }, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (self.run_dir / "t1.exitcode").write_text("0\n", encoding="utf-8")

        # t2: sync 축 + exitcode 0 → 휴리스틱 done
        (self.run_dir / "t2.prompt.txt").write_text("t2 프롬프트\n", encoding="utf-8")
        (self.run_dir / "t2.result.json").write_text(
            json.dumps({
                "type": "result", "subtype": "success", "is_error": False,
                "result": "t2 완료", "total_cost_usd": 0.03, "session_id": "sess-t2-0001",
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        (self.run_dir / "t2.exitcode").write_text("0\n", encoding="utf-8")

        # g: 산출물만 있고 exitcode 없음 → 휴리스틱 running
        (self.run_dir / "g.prompt.txt").write_text("g 프롬프트\n", encoding="utf-8")

        # t3: 아무 산출물 없음 → 휴리스틱 pending
        # t4a: exitcode 1 → 휴리스틱 failed
        (self.run_dir / "t4a.prompt.txt").write_text("t4a 프롬프트\n", encoding="utf-8")
        (self.run_dir / "t4a.exitcode").write_text("1\n", encoding="utf-8")
        (self.run_dir / "t4a.err.log").write_text("stderr sample\n", encoding="utf-8")

        # t4b: 산출물 없음 → 휴리스틱 pending
        (self.run_dir / "journal.md").write_text(
            "| 시각 | 단계 | 이벤트 | 근거 |\n"
            "|---|---|---|---|\n"
            "| 2026-09-14 01:00 | t1 | started | dispatch |\n",
            encoding="utf-8",
        )

    def _phase_record(self, status):
        """`oppl-runtime-tool` `ledger.phase_record()`가 만드는 레코드와 동일 필드 집합."""
        return {
            "attempt_count": 1,
            "resume_count": 0,
            "active_attempt_id": None,
            "status": status,
            "record_path": None,
            "last_failure_fingerprint": None,
            "identical_failure_count": 0,
        }

    def _build_ledger(self, phase_statuses=None):
        """실제 `oppl-runtime-tool`(W-3+W-6)이 쓰는 ledger 스키마 그대로 구성한다.

        phase 레코드 경로는 `counters.<task_id>.phases.<phase>` 중첩이다
        (제안서 §4.1 "task·phase별" — 최상위 평면 `phases`가 아니다).
        최상위 `tasks` 키는 쓰지 않는다 — 컨테이너 이름은 `counters`다(S-26 금지 키).
        """
        statuses = LEDGER_PHASE_STATUS if phase_statuses is None else phase_statuses
        return {
            "schema_version": "1.0",
            "run_id": RUN_ID,
            "revision": 7,
            "status": "running",
            "started_at": "2026-09-14T01:00:00+00:00",
            "deadline_at": "2026-09-14T02:00:00+00:00",
            "design_round": 1,
            "project_dispatch_count": 3,
            "cost_used": 0.15,
            "wall_time_used": 300.0,
            "budget_snapshot": dict(BUDGET_SNAPSHOT),
            "counters": {
                LEDGER_TASK_ID: {
                    "phases": {
                        phase: self._phase_record(status)
                        for phase, status in statuses.items()
                    }
                }
            },
        }

    def _write_runtime_json(self, phase_statuses=None):
        """ledger와 lock 파일을 깐다 — 실제 `.oppl-run/` 구성(runtime.json + runtime.lock)."""
        (self.run_dir / "runtime.json").write_text(
            json.dumps(self._build_ledger(phase_statuses), ensure_ascii=False), encoding="utf-8"
        )
        (self.run_dir / "runtime.lock").write_text("", encoding="utf-8")

    def _json_payload(self):
        proc = _run([self.task_folder, "--json"])
        self.assertEqual(proc.returncode, 0, f"--json 실행 실패: {proc.stdout}{proc.stderr}")
        return json.loads(proc.stdout)

    def _statuses(self, payload):
        return {p["phase"]: p["status"] for p in payload["phases"]}


class TestT131RuntimeDelegation(_RunDirCase):
    """S-21 / PLAN D7 — runtime.json이 있으면 재판정 없이 위임한다."""

    def setUp(self):
        super().setUp()
        self._write_runtime_json()

    def test_json_phase_statuses_come_from_ledger(self):
        """phase별 status가 ledger 값과 전건 일치한다 — 자체 휴리스틱 재판정 0건."""
        statuses = self._statuses(self._json_payload())
        self.assertEqual(
            statuses, LEDGER_PHASE_STATUS,
            "monitor가 runtime.json 위임 판정 대신 자체 휴리스틱 결과를 냈다",
        )

    def test_heuristic_is_actually_bypassed(self):
        """휴리스틱과 어긋나게 설계한 3개 phase가 ledger 값으로 나온다(위임 증명)."""
        statuses = self._statuses(self._json_payload())
        self.assertEqual(statuses.get("t1"), "timed_out", "exitcode 0을 done으로 재판정했다")
        self.assertEqual(statuses.get("t3"), "running", "산출물 부재를 pending으로 재판정했다")
        self.assertEqual(statuses.get("t4a"), "blocked", "exitcode 1을 failed로 재판정했다")

    def test_json_statuses_within_seven_enum(self):
        """출력 status는 7종 enum 안에만 있다."""
        for phase, status in self._statuses(self._json_payload()).items():
            self.assertIn(status, STATUS_ENUM_7, f"{phase} status가 7종 enum 밖이다: {status}")

    def test_json_exposes_run_id_and_remaining_limits(self):
        """잔여 상한과 run_id를 ledger에서 읽어 그대로 노출한다 (D7 '잔여 상한만 읽어 렌더')."""
        payload = self._json_payload()
        runtime = payload.get("runtime")
        self.assertIsInstance(
            runtime, dict, f"--json 출력에 runtime 위임 블록이 없다: {sorted(payload)}",
        )
        self.assertEqual(runtime.get("run_id"), RUN_ID)
        self.assertEqual(runtime.get("budget_snapshot"), BUDGET_SNAPSHOT)

    def test_text_mode_renders_delegated_timed_out(self):
        """텍스트 모드에도 위임된 timed_out이 렌더된다."""
        proc = _run([self.task_folder])
        self.assertEqual(proc.returncode, 0, f"텍스트 실행 실패: {proc.stdout}{proc.stderr}")
        self.assertIn("timed_out", proc.stdout, "텍스트 현황판에 위임된 timed_out이 없다")

    def test_missing_phase_record_reads_as_pending(self):
        """phase 레코드는 `admit` 시점에 생성된다 — 부재 레코드를 pending/0으로 읽고 오류를 내지 않는다.

        거부된 admit은 레코드를 만들지 않으므로 `counters`는 있는데 특정 phase가 없는
        상태가 실제로 발생한다. `g`를 빼도 나머지 위임 판정은 그대로여야 한다.
        휴리스틱이라면 `g`는 산출물(prompt.txt) 때문에 running이 되므로 항진명제가 아니다.
        """
        partial = {p: s for p, s in LEDGER_PHASE_STATUS.items() if p != "g"}
        self._write_runtime_json(partial)

        proc = _run([self.task_folder, "--json"])
        self.assertEqual(
            proc.returncode, 0,
            f"phase 레코드 부재로 monitor가 실패했다: {proc.stdout}{proc.stderr}",
        )
        payload = json.loads(proc.stdout)
        statuses = self._statuses(payload)
        self.assertEqual(statuses.get("g"), "pending", "부재 레코드를 pending으로 읽지 않았다")
        self.assertEqual(statuses.get("t1"), "timed_out", "부재 레코드가 나머지 위임을 깨뜨렸다")

        phase_g = next(p for p in payload["phases"] if p["phase"] == "g")
        for counter in ("attempt_count", "resume_count"):
            if counter in phase_g:
                self.assertEqual(phase_g[counter], 0, f"부재 레코드의 {counter}가 0이 아니다")

    def test_text_mode_survives_missing_phase_record(self):
        """텍스트 모드도 phase 레코드 부재에서 6행을 정상 렌더한다."""
        self._write_runtime_json({p: s for p, s in LEDGER_PHASE_STATUS.items() if p != "g"})
        proc = _run([self.task_folder])
        self.assertEqual(proc.returncode, 0, f"텍스트 실행 실패: {proc.stdout}{proc.stderr}")
        for phase in PHASES:
            self.assertRegex(proc.stdout, rf"(?m)^{phase}\s", f"{phase} 행이 렌더되지 않았다")


class TestT131LegacyHeuristicFallback(_RunDirCase):
    """S-21 하위호환 축 — runtime.json이 없으면 기존 6상태 휴리스틱을 그대로 쓴다."""

    def test_legacy_statuses_match_existing_heuristic(self):
        """runtime.json 부재 시 기존 판정(:180-192)이 그대로 유지된다."""
        statuses = self._statuses(self._json_payload())
        self.assertEqual(statuses, {
            "t1": "done", "t2": "done", "g": "running",
            "t3": "pending", "t4a": "failed", "t4b": "pending",
        })

    def test_legacy_never_emits_timed_out(self):
        """legacy 경로는 timed_out을 절대 출력하지 않는다 (텍스트·--json 양쪽)."""
        payload = self._json_payload()
        for phase, status in self._statuses(payload).items():
            self.assertIn(status, STATUS_ENUM_6, f"{phase}가 6상태 밖이다: {status}")
        self.assertNotIn("timed_out", json.dumps(payload, ensure_ascii=False))

        proc = _run([self.task_folder])
        self.assertEqual(proc.returncode, 0, f"텍스트 실행 실패: {proc.stdout}{proc.stderr}")
        self.assertNotIn("timed_out", proc.stdout)

    def test_legacy_has_no_runtime_block(self):
        """runtime.json이 없으면 위임 블록도 만들지 않는다 — 없는 상한을 지어내지 않는다."""
        payload = self._json_payload()
        self.assertIsNone(payload.get("runtime"), f"위임 블록이 있다: {payload.get('runtime')}")


class TestT131ReadOnlyInvariant(_RunDirCase):
    """S-21 / C-3 — 실행 전후 `.oppl-run` 전 파일 SHA-256 동일 (쓰기 0건)."""

    def _assert_no_writes(self, argv):
        before = _hash_tree(self.run_dir)
        self.assertTrue(before, "픽스처 전제 위반: .oppl-run이 비어있다")
        proc = _run(argv)
        self.assertEqual(proc.returncode, 0, f"실행 실패: {proc.stdout}{proc.stderr}")
        after = _hash_tree(self.run_dir)
        self.assertEqual(sorted(after), sorted(before), "`.oppl-run` 파일 목록이 변했다")
        self.assertEqual(after, before, "`.oppl-run` 파일 내용이 변했다 — monitor가 쓰기를 했다")

    def test_legacy_text_mode_writes_nothing(self):
        """runtime.json 부재 + 텍스트 모드 — 쓰기 0건."""
        self._assert_no_writes([self.task_folder])

    def test_legacy_json_mode_writes_nothing(self):
        """runtime.json 부재 + --json 모드 — 쓰기 0건."""
        self._assert_no_writes([self.task_folder, "--json"])

    def test_runtime_text_mode_writes_nothing(self):
        """runtime.json 존재 + 텍스트 모드 — 쓰기 0건 (runtime.json 자체도 불변)."""
        self._write_runtime_json()
        self._assert_no_writes([self.task_folder])

    def test_runtime_json_mode_writes_nothing(self):
        """runtime.json 존재 + --json 모드 — 쓰기 0건 (runtime.json 자체도 불변)."""
        self._write_runtime_json()
        self._assert_no_writes([self.task_folder, "--json"])


class TestT131TerminalStatuses(unittest.TestCase):
    """S-21 / PLAN D7 — TERMINAL_STATUSES에 timed_out이 추가된다 (`--watch` 종료 판정)."""

    def setUp(self):
        sys.path.insert(0, str(_TOOL_DIR))
        import opal_action_monitor  # noqa: PLC0415 — 도구 디렉토리 경로 주입 후 import
        self.module = opal_action_monitor

    def tearDown(self):
        if str(_TOOL_DIR) in sys.path:
            sys.path.remove(str(_TOOL_DIR))

    def test_timed_out_is_terminal(self):
        """timed_out은 종료 상태다 — --watch가 무한 대기하지 않는다."""
        self.assertIn("timed_out", self.module.TERMINAL_STATUSES)

    def test_terminal_statuses_exact_set(self):
        """종료 상태는 done/failed/error/blocked/timed_out 5종이다 (running·pending 배제)."""
        self.assertEqual(
            set(self.module.TERMINAL_STATUSES),
            {"done", "failed", "error", "blocked", "timed_out"},
        )


if __name__ == "__main__":
    unittest.main()
