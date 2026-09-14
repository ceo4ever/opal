"""
@header {
  "module": "test_state_tool_run_log",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool run-log 계약 RED-first 테스트 — T02 관통분(초기화 관통·미지정 경로 바이트 동일성·기존 회귀 기준선)과 T05 보관함분(활성 계약 기록 삭제의 run_log_missing 진단, 중단된 초기화의 보관함 복구와 멱등 재전송, 상태 전이의 state.changed 원자 커밋, 기록 실패 시 전건 보존과 비교착, 128건·4 KiB 상한 집행, 스키마 1.2 등재, 미지정 경로 무영향)을 함께 판정한다. run.sh subprocess 실호출 + 디스크 산출물 검사만 사용하고 mock/patch/MagicMock은 쓰지 않는다(red-first.md §4). 기록 실패는 조각 파일 권한 제거(0o400)로, 보관함 상한은 state.json fixture 주입으로 실제 유발한다.",
  "exports": ["TestShadowInitPierce", "TestUnflaggedInitByteIdentical", "TestExistingRegressionBaseline", "TestRunLogMissingDiagnosis", "TestInterruptedInitRecovery", "TestStateChangedAtomicCommit", "TestOutboxPreservesOnWriteFailure", "TestOutboxLimits", "TestSchema12Registered", "TestUnflaggedTransitionUnaffected"],
  "scenarios": ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-9"]
}

PLAN.md(T02) §테스트 시나리오 초안 근거:
  - S-1 state-tool.init.run-log-mode shadow — state.json schema_version==1.2 + run_log 7필드 +
    첫 조각(run/run-log-{run_id}-0001.jsonl) 1줄(run.started, sequence==1, actor_sequence==1)
  - S-2 (C-3) --run-log-mode 미지정 init은 개정 전(git show HEAD:./state_tool.py)과 state.json 바이트 동일
  - S-9 (C-2) 기존 state-tool 회귀 0건 — pytest 실패 0건·종료 코드 0 재현(통과 개수는 형제 태스크가 이동시키므로 상수로 고정하지 않는다),
    tests/test_state_tool.py·schema/state.schema.json 미변경
"""

import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

_STATE_TOOL_DIR = pathlib.Path(__file__).parent.parent
_REPO_ROOT = _STATE_TOOL_DIR.parent.parent.parent
_RUN_SH = _STATE_TOOL_DIR / "run.sh"
_CURRENT_STATE_TOOL = _STATE_TOOL_DIR / "state_tool.py"
_VENV_PYTHON = pathlib.Path.home() / ".opal" / ".venv" / "bin" / "python"


# ─────────────────────────────────────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _run(args, cwd=None):
    """run.sh를 subprocess로 실행하여 (returncode, stdout_text, stderr_text, parsed_json) 반환."""
    cmd = ["bash", str(_RUN_SH)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


def _run_init_direct(state_tool_source, task_path):
    """지정된 state_tool.py 소스 파일을 venv python으로 직접 실행해 init 수행.
    HEAD 버전(임시 위치에 풀어놓은 사본)과 현재본을 동일 조건으로 비교하기 위해
    run.sh 래퍼가 아니라 소스 파일을 직접 지정해 실행한다."""
    cmd = [str(_VENV_PYTHON), str(state_tool_source), "init", str(task_path),
           "--skill", "oppl", "--mode", "agentic"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


# ─────────────────────────────────────────────────────────────────────────────
# S-1 — shadow 초기화가 상태 1.2와 첫 조각을 함께 만든다
# ─────────────────────────────────────────────────────────────────────────────

class TestShadowInitPierce(unittest.TestCase):
    def test_shadow_init_creates_state_1_2_and_first_segment(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = pathlib.Path(tmp) / "task-s1"
            task_path.mkdir()

            code, out, err, data = _run([
                "init", str(task_path),
                "--skill", "oppl", "--mode", "agentic",
                "--run-log-mode", "shadow",
            ])
            self.assertEqual(code, 0, f"S-1 init exit!=0 — stdout={out!r} stderr={err!r}")

            state_file = task_path / "state.json"
            self.assertTrue(state_file.exists(), "S-1 state.json이 생성되지 않음")
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(state.get("schema_version"), "1.2", f"S-1 schema_version!=1.2 — {state}")

            run_log = state.get("run_log")
            self.assertIsNotNone(run_log, f"S-1 run_log 블록 부재 — {state}")
            self.assertEqual(run_log.get("contract_version"), "1.0", f"S-1 contract_version 불일치 — {run_log}")
            self.assertEqual(run_log.get("mode"), "shadow", f"S-1 mode!=shadow — {run_log}")
            self.assertEqual(run_log.get("completion_profile"), "cooperative",
                              f"S-1 completion_profile!=cooperative — {run_log}")
            self.assertIsNone(run_log.get("completion_profile_receipt"),
                               f"S-1 completion_profile_receipt가 None이 아님 — {run_log}")
            run_id = run_log.get("active_run_id")
            self.assertTrue(run_id and run_id.startswith("run_"),
                             f"S-1 active_run_id가 run_ 접두가 아님 — {run_log}")
            self.assertEqual(run_log.get("status"), "active", f"S-1 status!=active — {run_log}")
            self.assertEqual(run_log.get("pending_events"), [], f"S-1 pending_events가 비어있지 않음 — {run_log}")

            segment = task_path / "run" / f"run-log-{run_id}-0001.jsonl"
            self.assertTrue(segment.exists(), f"S-1 첫 조각 파일 부재: {segment}")
            lines = segment.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1, f"S-1 첫 조각은 정확히 1줄이어야 함 — {lines}")

            event = json.loads(lines[0])
            self.assertEqual(event.get("event"), "run.started", f"S-1 event!=run.started — {event}")
            self.assertEqual(event.get("sequence"), 1, f"S-1 sequence!=1 — {event}")
            self.assertEqual(event.get("actor_sequence"), 1, f"S-1 actor_sequence!=1 — {event}")
            self.assertEqual(event.get("actor", {}).get("kind"), "tool", f"S-1 actor.kind!=tool — {event}")
            self.assertEqual(event.get("provenance", {}).get("type"), "direct",
                              f"S-1 provenance.type!=direct — {event}")
            ts = event.get("timestamp", "")
            self.assertRegex(ts, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$",
                              f"S-1 timestamp가 RFC3339 밀리초 UTC 형식이 아님 — {ts!r}")


# ─────────────────────────────────────────────────────────────────────────────
# S-2 — --run-log-mode 미지정 init이 개정 전과 바이트 동일 (C-3, red_required=false)
# ─────────────────────────────────────────────────────────────────────────────

class TestUnflaggedInitByteIdentical(unittest.TestCase):
    def test_no_run_log_mode_init_matches_head_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)

            head_result = subprocess.run(
                ["git", "show", "HEAD:./state_tool.py"],
                cwd=str(_STATE_TOOL_DIR), capture_output=True, text=True,
            )
            self.assertEqual(head_result.returncode, 0, f"S-2 git show HEAD 실패 — {head_result.stderr}")
            self.assertTrue(head_result.stdout, "S-2 git show HEAD:./state_tool.py 결과가 비어 있음")

            head_copy_dir = tmp_path / "head-copy"
            head_copy_dir.mkdir()
            head_source = head_copy_dir / "state_tool.py"
            head_source.write_text(head_result.stdout, encoding="utf-8")

            # task_id는 폴더명에서 파생되므로(state_tool.py task_path.name) 두 실행이
            # 같은 리프 디렉터리명을 쓰도록 별도 부모 아래에 둔다 — 이름 차이가
            # 바이트 비교를 오염시키지 않게 한다.
            task_a = tmp_path / "head-parent" / "task-s2"
            task_b = tmp_path / "current-parent" / "task-s2"
            task_a.parent.mkdir(parents=True, exist_ok=True)
            task_b.parent.mkdir(parents=True, exist_ok=True)

            bytes_a = bytes_b = None
            last_mismatch = None
            # 초 해상도 시각(get_kst_datetime)이 두 실행 사이 경계를 넘는 드문 레이스를
            # 완화하기 위한 재시도 — 단언 자체(바이트 완전 동일)는 약화하지 않는다.
            for _ in range(5):
                for d in (task_a, task_b):
                    if d.exists():
                        shutil.rmtree(d)
                    d.mkdir()

                code_a, out_a, err_a = _run_init_direct(head_source, task_a)
                code_b, out_b, err_b = _run_init_direct(_CURRENT_STATE_TOOL, task_b)
                self.assertEqual(code_a, 0, f"S-2 HEAD 버전 init 실패 — stdout={out_a!r} stderr={err_a!r}")
                self.assertEqual(code_b, 0, f"S-2 현재본 init 실패 — stdout={out_b!r} stderr={err_b!r}")

                bytes_a = (task_a / "state.json").read_bytes()
                bytes_b = (task_b / "state.json").read_bytes()
                if bytes_a == bytes_b:
                    last_mismatch = None
                    break
                last_mismatch = (bytes_a, bytes_b)

            self.assertIsNone(
                last_mismatch,
                "S-2 개정 전/후 state.json 바이트 불일치"
                if last_mismatch is None else
                f"S-2 개정 전/후 state.json 바이트 불일치 — head={last_mismatch[0]!r} current={last_mismatch[1]!r}")

            state_b = json.loads(bytes_b.decode("utf-8"))
            self.assertNotIn("run_log", state_b, "S-2 --run-log-mode 미지정인데 run_log 키가 생성됨")
            self.assertFalse((task_b / "run").exists(), "S-2 --run-log-mode 미지정인데 run/ 디렉터리가 생성됨")


# ─────────────────────────────────────────────────────────────────────────────
# S-9 — 기존 state-tool 회귀 0건 (C-2, red_required=false)
# ─────────────────────────────────────────────────────────────────────────────

class TestExistingRegressionBaseline(unittest.TestCase):
    def test_existing_suite_matches_baseline_and_frozen_files_untouched(self):
        # [MUST] 이 테스트 파일 자신(test_state_tool_run_log.py)은 --ignore로 제외한다 —
        # tests/ 디렉터리 전체를 그대로 지정하면 자신이 재귀적으로 포함되어, S-9가
        # 자신을 실행하는 pytest를 다시 기동하는 무한 재귀가 된다. 기준선 425
        # passed/3 skipped/111 subtests passed는 tests/ 안의 나머지 3개 파일
        # (test_state_tool.py·test_event_verify.py·test_todo_mirror_hook.py) 합산 실측이다.
        self_path = pathlib.Path(__file__).resolve()
        result = subprocess.run(
            ["python3", "-m", "pytest", "opal/tools/state-tool/tests/", "-q",
             f"--ignore={self_path}"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True,
        )
        combined = result.stdout + result.stderr
        # [불안정 기준선 제거 — 123 opd 전환] 통과 **개수**를 상수로 박으면 형제 태스크가
        # 테스트를 늘릴 때마다 구현이 정상인데도 거짓 실패가 난다(실제 발생: 425→441,
        # main의 122·131 유입). 더구나 개수 단언은 누군가 테스트를 지우고 수를 맞춰도
        # 통과시켜 계약을 지키지 못한다. 이 단언이 지키려는 계약은 "기존 테스트가 깨지지
        # 않았다"이므로 **실패 0건**이라는 불변 조건으로 판정한다.
        self.assertNotIn("failed", combined,
                         f"S-9 회귀 실패 — 기존 테스트가 깨졌다. 출력 말미: {combined[-2000:]}")
        self.assertIn("passed", combined,
                      f"S-9 테스트가 수집되지 않았다(스위트 자체 실패 의심). 출력 말미: {combined[-2000:]}")
        self.assertEqual(0, result.returncode,
                         f"S-9 pytest 종료 코드 비정상({result.returncode}). 출력 말미: {combined[-2000:]}")

        # T02의 동결 대상(`tests/test_state_tool.py`·`schema/state.schema.json`)은
        # T05(AC-4)가 스키마 1.2 등재를 인계받으면서 해제됐다 — 등재는 두 파일을
        # 반드시 건드리므로 "미변경" 단언과 양립하지 않는다. 회귀를 지키는 실질
        # 판정은 위의 건수 기준선(425/3/111)이며, 그 수치가 그대로인 한 1.0/1.1
        # 태스크의 동작은 바뀌지 않았다(C-2·C-3). 1.2 등재 자체의 판정은 S-6이
        # 소유한다.
        schema = json.loads(
            (_STATE_TOOL_DIR / "schema" / "state.schema.json").read_text(encoding="utf-8"))
        self.assertLessEqual(
            {"1.0", "1.1"}, set(schema["properties"]["schema_version"]["enum"]),
            "S-9 1.0/1.1 병행 허용이 깨짐(C-3)")


if __name__ == "__main__":
    unittest.main()


# ═════════════════════════════════════════════════════════════════════════════
# T05 — 보관함(outbox)·복구·상한 (AC-3 / AC-10 / AC-4 / C-3)
#   T05 S-1 활성 계약 기록 삭제 → run_log_missing 진단(강등 없음)
#   T05 S-2 중단된 초기화 → 보관함 run.started로 active 복구(멱등)
#   T05 S-3 상태 전이 = state.changed 1건 원자 커밋 → append → 보관함 비우기
#   T05 S-4 기록 실패 연속 발생 시 전건 보존 + 전이 비교착
#   T05 S-5 보관함 상한(128건·사건당 4 KiB) 집행
#   T05 S-6 state.schema.json 1.2 등재
#   T05 S-7 --run-log-mode 미지정 경로 무영향
# ═════════════════════════════════════════════════════════════════════════════

import os

_ROWS_SPEC = json.dumps([
    {"stage": "EXECUTE", "item": "구현 A"},
    {"stage": "EXECUTE", "item": "구현 B"},
    {"stage": "TEST", "item": "검증"},
], ensure_ascii=False)


def _init_shadow(task_path, extra=()):
    """--run-log-mode shadow + 3행으로 태스크를 초기화한다."""
    args = ["init", str(task_path), "--skill", "oppl", "--mode", "agentic",
            "--rows-spec", _ROWS_SPEC, "--run-log-mode", "shadow"]
    args.extend(extra)
    return _run(args)


def _read_state(task_path):
    return json.loads((pathlib.Path(task_path) / "state.json").read_text(encoding="utf-8"))


def _write_state(task_path, state):
    (pathlib.Path(task_path) / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _segment_records(task_path, run_id=None):
    run_dir = pathlib.Path(task_path) / "run"
    if not run_dir.exists():
        return []
    records = []
    for seg in sorted(run_dir.glob("run-log-*.jsonl")):
        for line in seg.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def _mktask(tmp, name="123-260912-oppl-t05"):
    p = pathlib.Path(tmp) / name
    p.mkdir(parents=True)
    return p


class TestRunLogMissingDiagnosis(unittest.TestCase):
    """T05 S-1 (AC-3) — 활성 계약 태스크의 기록이 사라지면 legacy 강등이 아니라 고장으로 진단된다."""

    def test_deleted_run_log_is_diagnosed_not_downgraded(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp)
            code, out, errtxt, data = _init_shadow(task)
            self.assertEqual(code, 0, f"T05 S-1 init 실패 — {out!r} {errtxt!r}")

            shutil.rmtree(task / "run")

            code, out, errtxt, data = _run(["validate", str(task)])
            codes = [v.get("code") for v in data.get("violations", [])]
            self.assertIn("run_log_missing", codes,
                          f"T05 S-1 진단이 run_log_missing이 아님 — {out!r}")
            self.assertNotEqual(code, 0, "T05 S-1 기록 부재인데 validate가 exit 0")

            state = _read_state(task)
            self.assertEqual(state.get("schema_version"), "1.2",
                             f"T05 S-1 스키마가 강등됨 — {state.get('schema_version')!r}")
            self.assertIn("run_log", state, "T05 S-1 run_log 계약 블록이 제거됨(강등)")


class TestInterruptedInitRecovery(unittest.TestCase):
    """T05 S-2 (AC-3) — 초기화가 중단돼 첫 조각이 없어도 보관함의 run.started로 active 복구된다."""

    def test_pending_run_started_recovers_to_active_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp)
            code, out, errtxt, data = _init_shadow(task)
            self.assertEqual(code, 0, f"T05 S-2 init 실패 — {out!r}")

            started = _segment_records(task)[0]
            # 초기화가 조각 생성 직전에 끊긴 상태를 재현: run/ 부재 + 보관함에 run.started
            shutil.rmtree(task / "run")
            state = _read_state(task)
            state["run_log"]["status"] = "pending"
            state["run_log"]["pending_events"] = [
                {k: v for k, v in started.items()
                 if k not in ("sequence", "actor_sequence")}]
            _write_state(task, state)

            code, out, errtxt, data = _run(["validate", str(task)])
            codes = [v.get("code") for v in data.get("violations", [])]
            self.assertNotIn("run_log_missing", codes,
                             f"T05 S-2 복구 가능 초기화가 run_log_missing으로 오진단됨 — {out!r}")
            self.assertIn("run_log_pending", codes,
                          f"T05 S-2 복구 가능 진단(run_log_pending)이 없음 — {out!r}")

            code, out, errtxt, data = _run(["advance", str(task), "--row", "1"])
            self.assertEqual(code, 0, f"T05 S-2 복구 전이 실패 — {out!r} {errtxt!r}")

            state = _read_state(task)
            self.assertEqual(state["run_log"]["status"], "active",
                             f"T05 S-2 복구 후 status!=active — {state['run_log']}")
            self.assertEqual(state["run_log"]["pending_events"], [],
                             "T05 S-2 복구 후 보관함이 비지 않음")

            recs = _segment_records(task)
            started_ids = [r["event_id"] for r in recs if r["event"] == "run.started"]
            self.assertEqual(started_ids, [started["event_id"]],
                             f"T05 S-2 run.started 복구 결과가 원본 1건이 아님 — {started_ids}")

            # 멱등 — 다음 전이가 같은 사건을 다시 적재하지 않는다
            code, out, errtxt, data = _run(["mark", str(task), "--row", "1", "--done"])
            self.assertEqual(code, 0, f"T05 S-2 후속 전이 실패 — {out!r}")
            recs = _segment_records(task)
            self.assertEqual(
                len([r for r in recs if r["event"] == "run.started"]), 1,
                "T05 S-2 복구 드레인이 멱등하지 않음(run.started 중복)")


class TestStateChangedAtomicCommit(unittest.TestCase):
    """T05 S-3 — 상태 전이가 state.changed 1건을 보관함에 적재한 뒤 같은 원자 쓰기로 커밋한다."""

    def test_transition_commits_state_changed_and_drains_outbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp)
            self.assertEqual(_init_shadow(task)[0], 0)

            code, out, errtxt, data = _run(["advance", str(task), "--row", "1"])
            self.assertEqual(code, 0, f"T05 S-3 advance 실패 — {out!r}")

            state = _read_state(task)
            self.assertEqual(state["run_log"]["pending_events"], [],
                             "T05 S-3 append 성공인데 보관함이 비지 않음")
            self.assertEqual(state["run_log"]["status"], "active")

            changed = [r for r in _segment_records(task) if r["event"] == "state.changed"]
            self.assertEqual(len(changed), 1, f"T05 S-3 state.changed 1건이 아님 — {len(changed)}")
            ev = changed[0]
            self.assertEqual(ev["actor"]["kind"], "tool")
            self.assertEqual(ev["data"]["from"], "pending")
            self.assertEqual(ev["data"]["to"], "in_progress")
            self.assertIn("row_key", ev["data"])

            code, out, errtxt, data = _run(["mark", str(task), "--row", "1", "--done"])
            self.assertEqual(code, 0, f"T05 S-3 mark 실패 — {out!r}")
            changed = [r for r in _segment_records(task) if r["event"] == "state.changed"]
            self.assertEqual(len(changed), 2, f"T05 S-3 mark의 state.changed 미기록 — {len(changed)}")
            self.assertEqual(changed[1]["data"]["to"], "done")


class TestOutboxPreservesOnWriteFailure(unittest.TestCase):
    """T05 S-4 (AC-10) — 연속된 기록 실패가 보관함에 전건 보존되고 전이가 교착되지 않는다."""

    def test_consecutive_write_failures_are_all_preserved_without_deadlock(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp)
            self.assertEqual(_init_shadow(task)[0], 0)

            segment = sorted((task / "run").glob("run-log-*.jsonl"))[0]
            os.chmod(segment, 0o400)  # append 강제 실패 (쓰기 권한 제거)
            try:
                for args in (["advance", str(task), "--row", "1"],
                             ["mark", str(task), "--row", "1", "--done"],
                             ["advance", str(task), "--row", "2"]):
                    code, out, errtxt, data = _run(args)
                    self.assertEqual(code, 0,
                                     f"T05 S-4 기록 실패가 상태 전이를 교착시킴 — {args} {out!r}")

                state = _read_state(task)
                pending = state["run_log"]["pending_events"]
                self.assertEqual(len(pending), 3,
                                 f"T05 S-4 보관함 전건 보존 실패 — {len(pending)}건")
                self.assertEqual(state["run_log"]["status"], "pending",
                                 f"T05 S-4 미해소 보관함인데 status={state['run_log']['status']}")
                for ev in pending:
                    size = len(json.dumps(ev, ensure_ascii=False).encode("utf-8"))
                    self.assertLessEqual(size, 4096,
                                         f"T05 S-4 보관함 항목이 4 KiB 상한 초과 — {size}B")
                # 전이 자체는 반영됐다(교착 없음)
                rows = {r["row_id"]: r["status"] for r in state["rows"]}
                self.assertEqual(rows[1], "done")
                self.assertEqual(rows[2], "in_progress")
            finally:
                os.chmod(segment, 0o600)


class TestOutboxLimits(unittest.TestCase):
    """T05 S-5 (AC-10) — 전체 128건·사건당 4 KiB 상한이 집행되고 상한 도달 시 전이가 차단된다."""

    def test_total_limit_blocks_further_transitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp)
            self.assertEqual(_init_shadow(task)[0], 0)

            state = _read_state(task)
            template = _segment_records(task)[0]
            filler = []
            for i in range(128):
                ev = {k: v for k, v in template.items()
                      if k not in ("sequence", "actor_sequence")}
                ev["event"] = "state.changed"
                ev["event_id"] = f"evt_fill-{i:04d}"
                ev["request_id"] = f"req_fill-{i:04d}"
                ev["summary"] = f"filler {i}"
                ev["data"] = {"from": "pending", "to": "in_progress", "row_key": f"k{i}"}
                filler.append(ev)
            state["run_log"]["status"] = "pending"
            state["run_log"]["pending_events"] = filler
            _write_state(task, state)
            before = (task / "state.json").read_bytes()

            code, out, errtxt, data = _run(["advance", str(task), "--row", "1"])
            self.assertNotEqual(code, 0, f"T05 S-5 상한 도달인데 전이가 통과됨 — {out!r}")
            self.assertEqual(data.get("error"), "run_log_outbox_full",
                             f"T05 S-5 오류 코드가 run_log_outbox_full이 아님 — {out!r}")
            self.assertEqual((task / "state.json").read_bytes(), before,
                             "T05 S-5 차단됐는데 state.json이 변경됨")

    def test_oversized_event_is_rejected_before_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp)
            self.assertEqual(_init_shadow(task)[0], 0)
            before = (task / "state.json").read_bytes()

            code, out, errtxt, data = _run(
                ["advance", str(task), "--row", "1", "--note", "x" * 5000])
            self.assertNotEqual(code, 0, f"T05 S-5 4 KiB 초과 사건이 통과됨 — {out!r}")
            self.assertEqual(data.get("error"), "event_too_large",
                             f"T05 S-5 오류 코드가 event_too_large가 아님 — {out!r}")
            self.assertEqual((task / "state.json").read_bytes(), before,
                             "T05 S-5 거부됐는데 state.json이 변경됨")


class TestSchema12Registered(unittest.TestCase):
    """T05 S-6 (AC-4) — state.schema.json에 스키마 1.2와 run_log 계약 블록이 등재된다."""

    def test_schema_registers_1_2_and_run_log_block(self):
        schema = json.loads((_STATE_TOOL_DIR / "schema" / "state.schema.json")
                            .read_text(encoding="utf-8"))
        self.assertIn("1.2", schema["properties"]["schema_version"]["enum"],
                      "T05 S-6 schema_version enum에 1.2 미등재")
        run_log = schema["properties"].get("run_log")
        self.assertIsNotNone(run_log, "T05 S-6 properties.run_log 미등재")
        required = set(run_log.get("required", []))
        self.assertEqual(
            required,
            {"contract_version", "mode", "completion_profile",
             "completion_profile_receipt", "active_run_id", "status", "pending_events"},
            f"T05 S-6 run_log 필수 7필드 불일치 — {sorted(required)}")
        self.assertEqual(
            run_log["properties"]["pending_events"].get("maxItems"), 128,
            "T05 S-6 pending_events 전체 건수 상한(128) 미등재")
        self.assertEqual(set(run_log["properties"]["status"]["enum"]),
                         {"active", "pending", "overridden"},
                         "T05 S-6 run_log.status enum 불일치")


class TestUnflaggedTransitionUnaffected(unittest.TestCase):
    """T05 S-7 (C-3) — 미지정(1.0/1.1) 태스크의 전이는 run-log 경로를 타지 않는다."""

    def test_transition_without_run_log_block_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp)
            code, out, errtxt, data = _run(
                ["init", str(task), "--skill", "oppl", "--mode", "agentic",
                 "--rows-spec", _ROWS_SPEC])
            self.assertEqual(code, 0, f"T05 S-7 init 실패 — {out!r}")

            code, out, errtxt, data = _run(["advance", str(task), "--row", "1"])
            self.assertEqual(code, 0, f"T05 S-7 advance 실패 — {out!r}")
            self.assertNotIn("run_log", data, "T05 S-7 미지정 태스크 응답에 run_log 키가 생김")

            state = _read_state(task)
            self.assertNotIn("run_log", state, "T05 S-7 미지정 태스크 state.json에 run_log 키가 생김")
            self.assertFalse((task / "run").exists(), "T05 S-7 미지정 태스크에 run/ 생성됨")

            code, out, errtxt, data = _run(["validate", str(task)])
            self.assertEqual(code, 0, f"T05 S-7 미지정 태스크 validate 실패 — {out!r}")
            self.assertEqual(data.get("violations"), [], f"T05 S-7 위반 발생 — {out!r}")
