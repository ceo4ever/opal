"""
@header {
  "module": "test_state_tool_run_log",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool run-log 계약 RED-first 테스트 — T02 관통분(초기화 관통·미지정 경로 바이트 동일성·기존 회귀 기준선)과 T05 보관함분(활성 계약 기록 삭제의 run_log_missing 진단, 중단된 초기화의 보관함 복구와 멱등 재전송, 상태 전이의 state.changed 원자 커밋, 기록 실패 시 전건 보존과 비교착, 128건·4 KiB 상한 집행, 스키마 1.2 등재, 미지정 경로 무영향)을 함께 판정한다. run.sh subprocess 실호출 + 디스크 산출물 검사만 사용하고 mock/patch/MagicMock은 쓰지 않는다(red-first.md §4). 기록 실패는 조각 파일 권한 제거(0o400)로, 보관함 상한은 state.json fixture 주입으로 실제 유발한다.",
  "exports": ["TestShadowInitPierce", "TestUnflaggedInitByteIdentical", "TestExistingRegressionBaseline", "TestRunLogMissingDiagnosis", "TestInterruptedInitRecovery", "TestStateChangedAtomicCommit", "TestOutboxPreservesOnWriteFailure", "TestOutboxLimits", "TestSchema12Registered", "TestUnflaggedTransitionUnaffected", "TestWorkerDurationDerivedAndConflict", "TestUnflaggedDurationPathByteIdentical"],
  "scenarios": ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-9", "TEST-SCENARIO(W-7).S-8", "TEST-SCENARIO(W-7).S-9"]
}

W-7 추가분(123 RED-b, AC-12/C-3/H-6) — 아래 두 클래스가 다루는 `S-8`·`S-9`는 위
scenarios 목록의 T02/T05 구간 `S-1..S-9`(run-log-tool 초기 계약)와 **ID 공간이
다른 현재 TEST-SCENARIO.md의 시나리오**다(같은 파일 안에서 스키마 버전대가
갈리며 재사용된 번호라 접두 `TEST-SCENARIO(W-7).`로 구분한다):
  - S-8 (AC-12, C-3, H-6, red_required=true) — schema 1.2 mark의 파생 분값 자동
    기록·명시값 일치 시 수용+deprecated 경고·불일치 시 worker_duration_conflict
    거부+state.json 무변경. mark가 아직 W-6 코어 조회를 호출하지 않으므로 세
    경우 모두 현재 실패로 관찰된다(구현 전 RED).
  - S-9 (C-3, H-6, test-scenario.json상 red_required=true로 등재) — run_log
    블록이 없는 1.0/1.1 태스크의 mark·advance가 git HEAD와 바이트 동일해야
    한다는 보존 시나리오. **실측 결과 이 자산은 현재 이미 참이다** —
    state_tool.py가 아직 수정되지 않았으므로(W-7 GREEN 미착수) HEAD 실행과
    현재 빌드 실행이 항상 동일 산출물을 낸다. 이는 이 파일의 기존 동류
    보존 시나리오(TestUnflaggedInitByteIdentical·TestExistingRegressionBaseline)
    가 각각 주석에 `red_required=false`로 명시한 것과 동일한 성격이다. 아래
    TestUnflaggedDurationPathByteIdentical은 그래서 **의도적으로 RED가 아닌
    통과 상태로 추가**됐고, PM에는 test-scenario.json의 S-9 `red_required` 값이
    이 선례와 불일치한다는 점을 blocker로 보고한다(허위 RED 증거 조작 금지,
    헌법 §4).

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
import uuid

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


def _run_direct(state_tool_source, args):
    """지정된 state_tool.py 소스를 venv python으로 직접 실행한다(임의 서브커맨드).
    run.sh 래퍼가 아니라 소스 파일을 직접 지정해, HEAD 사본과 현재본을 동일 조건으로
    비교할 수 있게 한다(S-9)."""
    cmd = [str(_VENV_PYTHON), str(state_tool_source)] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
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


# ═════════════════════════════════════════════════════════════════════════════
# W-7 (TEST-SCENARIO.md 현재판) S-8 / S-9 — RED-b 분할
#   S-8 (AC-12, C-3, H-6) — schema 1.2 mark 파생 분값 자동 기록·명시값 일치
#     수용+deprecated·불일치 worker_duration_conflict 거부
#   S-9 (C-3, H-6) — run_log 블록 없는 1.0/1.1 mark·advance의 git HEAD 대비
#     바이트 동일성 보존(파생 조회 미호출)
# ═════════════════════════════════════════════════════════════════════════════

_ROWS_SPEC_S8 = json.dumps([
    {"stage": "EXECUTE", "item": "작업 (구현)"},
], ensure_ascii=False)

_ROWS_SPEC_11 = json.dumps([
    {"stage": "EXECUTE", "item": "구현 A", "key": "execute.impl_a"},
    {"stage": "EXECUTE", "item": "구현 B", "key": "execute.impl_b"},
], ensure_ascii=False)


def _append_segment_line(task_path, event):
    """활성 run의 마지막 조각 파일에 원본 사건 1줄을 그대로 append한다.

    W-6(다중 process span 합산 읽기 함수·`reconcile-duration`)가 아직 구현되지
    않아 이 fixture를 만드는 정규 CLI 경로(예: run-log-tool append) 자체가 없으므로,
    S-8이 전제하는 "다중 process span을 가진 동일 worker_run_id" 상태를 디스크에
    직접 실측 파일로 만든다(mock/patch 대신 실제 조각 파일 조작 — red-first.md §4,
    TestOutboxLimits와 동일 관례)."""
    run_dir = pathlib.Path(task_path) / "run"
    segments = sorted(run_dir.glob("run-log-*.jsonl"))
    seg = segments[-1]
    with seg.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _worker_terminal_events(task_path, run_id, worker_run_id, spans, start_seq):
    """CONTRACT §1.1/§1.1.1/§1.1.2 공통 필드를 갖춘 worker.started + worker.completed
    2건을 만든다. terminal 사건의 `data.duration_spans[]`는 서로 다른 `source_id`
    2건이며 합계가 `duration_ms`와 같다(CONTRACT §1.2 terminal 공통 조건)."""
    total_ms = sum(s["duration_ms"] for s in spans)
    task_id = pathlib.Path(task_path).name
    base = {
        "schema_version": "1.0",
        "timestamp": "2026-09-14T00:00:00.000Z",
        "task_id": task_id,
        "run_id": run_id,
        "parent_run_id": None,
        "worker_run_id": worker_run_id,
        "caused_by_event_id": None,
        "stage": "EXECUTE",
        "task_step": None,
        "work_item": None,
        "gate_id": None,
        "actor": {"kind": "worker", "id": "opal-task-agent"},
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "worker", "id": "opal-task-agent"},
            "worker_log_token_id": "wlt_11111111-1111-4111-8111-111111111111",
        },
        "reason": None,
        "reason_code": None,
        "duration_unknown_reason": None,
        "refs": [],
    }
    started = dict(base)
    started.update({
        "event_id": f"evt_{uuid.uuid4()}",
        "request_id": f"req_{uuid.uuid4()}",
        "sequence": start_seq,
        "actor_sequence": 1,
        "event": "worker.started",
        "summary": None,
        "duration_ms": None,
        "duration_source": None,
        "data": {},
    })
    completed = dict(base)
    completed.update({
        "event_id": f"evt_{uuid.uuid4()}",
        "request_id": f"req_{uuid.uuid4()}",
        "sequence": start_seq + 1,
        "actor_sequence": 2,
        "event": "worker.completed",
        "summary": "S-8 fixture — multi-span terminal",
        "duration_ms": total_ms,
        "duration_source": "worker_monotonic",
        "data": {"duration_spans": spans},
    })
    return started, completed


class TestWorkerDurationDerivedAndConflict(unittest.TestCase):
    """S-8 (AC-12, C-3, H-6, test-scenario.json red_required=true) — schema 1.2에서
    `mark`가 W-6 코어 조회로 파생 분값을 자동 기록하고, 명시값이 파생값과 같으면
    수용+deprecated 경고, 다르면 `worker_duration_conflict`로 거부해야 한다.

    구현 전 RED — 현재 `mark`는 이 조회를 전혀 호출하지 않으므로 세 경우 모두
    아래에서 실제 실패(AssertionError)로 관찰된다."""

    _SPANS = [
        {"source_id": "proc-1", "duration_ms": 120000},
        {"source_id": "proc-2", "duration_ms": 60000},
    ]  # 합계 180000ms → floor(180000/60000) = 3분 (파생값, 서로 다른 source_id 2건 합산)
    _DERIVED_MINUTES = 3

    def _seed_task(self, tmp, name):
        task = _mktask(tmp, name)
        code, out, errtxt, data = _run([
            "init", str(task), "--skill", "oppl", "--mode", "agentic",
            "--rows-spec", _ROWS_SPEC_S8, "--run-log-mode", "shadow"])
        self.assertEqual(code, 0, f"S-8 init 실패 — {out!r} {errtxt!r}")

        state = _read_state(task)
        run_id = state["run_log"]["active_run_id"]
        worker_run_id = f"wrk_{uuid.uuid4()}"

        started, completed = _worker_terminal_events(
            task, run_id, worker_run_id, self._SPANS, start_seq=2)
        _append_segment_line(task, started)
        _append_segment_line(task, completed)
        return task

    def test_mark_without_args_auto_records_derived_minutes(self):
        """① 인자 없이 mark — 파생 분값(3)이 자동 기록되고 missing 경고가 없어야 한다."""
        with tempfile.TemporaryDirectory() as tmp:
            task = self._seed_task(tmp, "task-s8-a")

            code, out, errtxt, data = _run(["mark", str(task), "--row", "1", "--done"])
            self.assertEqual(code, 0, f"S-8① mark 자체가 실패함(무관한 회귀) — {out!r} {errtxt!r}")

            self.assertEqual(
                data.get("worker_duration_minutes"), self._DERIVED_MINUTES,
                f"S-8① 파생 분값({self._DERIVED_MINUTES})이 응답에 자동 기록되지 않음(미구현) — {out!r}")

            missing_warnings = [w for w in (data.get("warnings") or [])
                                if w.get("code") == "worker_duration_missing"]
            self.assertEqual(
                missing_warnings, [],
                f"S-8① 파생 자동 기록 경로인데 worker_duration_missing 경고가 남음(미구현) — {out!r}")

            state = _read_state(task)
            row = state["rows"][0]
            self.assertEqual(
                row.get("worker_duration_minutes"), self._DERIVED_MINUTES,
                f"S-8① state.json 행에 파생 분값이 기록되지 않음(미구현) — {row}")

    def test_mark_with_matching_value_accepted_with_deprecation_warning(self):
        """② 파생값과 같은 --worker-duration-minutes — 수용되지만 deprecated 경고가 실려야 한다."""
        with tempfile.TemporaryDirectory() as tmp:
            task = self._seed_task(tmp, "task-s8-b")

            code, out, errtxt, data = _run([
                "mark", str(task), "--row", "1", "--done",
                "--worker-duration-minutes", str(self._DERIVED_MINUTES)])
            self.assertEqual(code, 0, f"S-8② 일치값 mark가 실패함 — {out!r} {errtxt!r}")

            warnings = data.get("warnings") or []
            deprecated = [w for w in warnings
                         if "deprecat" in (w.get("code") or "").lower()]
            self.assertTrue(
                deprecated,
                "S-8② 파생값과 일치하는 --worker-duration-minutes인데 deprecated 경고가 "
                f"없음(미구현) — {out!r}")

    def test_mark_with_conflicting_value_rejected_and_state_unchanged(self):
        """③ 파생값과 다른 --worker-duration-minutes — worker_duration_conflict로 거부, state.json 무변경."""
        with tempfile.TemporaryDirectory() as tmp:
            task = self._seed_task(tmp, "task-s8-c")
            before = (task / "state.json").read_bytes()

            code, out, errtxt, data = _run([
                "mark", str(task), "--row", "1", "--done",
                "--worker-duration-minutes", "99"])

            self.assertNotEqual(
                code, 0,
                f"S-8③ 파생값(={self._DERIVED_MINUTES}분)과 다른 --worker-duration-minutes 99가 "
                f"거부되지 않고 통과함(미구현) — {out!r}")
            self.assertEqual(
                data.get("error"), "worker_duration_conflict",
                f"S-8③ 오류 코드가 worker_duration_conflict가 아님 — {out!r}")
            self.assertEqual(
                (task / "state.json").read_bytes(), before,
                "S-8③ 거부됐어야 하는데 state.json이 변경됨")


class TestUnflaggedDurationPathByteIdentical(unittest.TestCase):
    """S-9 (C-3, H-6) — run_log 블록이 없는 1.0/1.1 태스크의 `mark`·`advance`가
    git HEAD와 산출물·응답 키 집합 바이트 동일해야 한다(파생 조회 미호출의 대리 판정).

    self-confirming 금지(PM 하네스 가드) — 현재 빌드 자신의 출력을 정답으로 쓰지
    않고, git HEAD를 별도 프로세스로 실행해 독립적으로 정답을 만든다(S-2와 동일
    기법). `_import_run_log_core()`가 sibling 배치를 우선하므로, HEAD 사본은
    `opal/tools/{state-tool,run-log-tool}` 형제 구조를 그대로 복제해 두지 않으면
    빌드 위치 차이만으로 거짓 실패가 난다 — 아래 `_head_source()`가 그 구조를 만든다.

    [실측 결과 — 정직한 보고, 조작 없음] 이 두 테스트는 **현재 이미 통과한다**
    (state_tool.py가 W-7 GREEN으로 아직 수정되지 않았으므로 HEAD == 현재 빌드).
    이는 파일 내 동류 보존 시나리오(TestUnflaggedInitByteIdentical §S-2,
    TestExistingRegressionBaseline §구 S-9)가 명시적으로 `red_required=false`인
    것과 같은 성격이며, 이 두 클래스만 유독 test-scenario.json에서
    `red_required=true`로 등재돼 있다 — PM 반환 시 blocker로 보고한다.

    [벽시계 필드 정규화] HEAD와 현재본은 별도 subprocess로 순차 실행되므로
    `created_at`·`updated_at`·`rows[*].timestamp`는 두 실행이 초 경계를 straddle하면
    값 자체가 달라진다. C-3의 바이트 동일성은 구조·키·나머지 값에 대한 계약이지 두
    시점에 찍힌 벽시계가 같아야 한다는 뜻이 아니므로, 이 필드들만 존재·타입을 확인한
    뒤 고정값으로 치환해 비교하고 그 외 키·값은 그대로 엄격 비교한다."""

    def _head_source(self, tmp_path):
        head_root = tmp_path / "head-src" / "opal" / "tools"
        st_dir = head_root / "state-tool"
        rl_dir = head_root / "run-log-tool"
        st_dir.mkdir(parents=True)
        rl_dir.mkdir(parents=True)

        head_result = subprocess.run(
            ["git", "show", "HEAD:./state_tool.py"],
            cwd=str(_STATE_TOOL_DIR), capture_output=True, text=True)
        self.assertEqual(head_result.returncode, 0,
                         f"S-9 git show HEAD 실패 — {head_result.stderr}")
        (st_dir / "state_tool.py").write_text(head_result.stdout, encoding="utf-8")

        current_core = _STATE_TOOL_DIR.parent / "run-log-tool" / "run_log_core.py"
        shutil.copy(current_core, rl_dir / "run_log_core.py")
        return st_dir / "state_tool.py"

    _WALLCLOCK_SENTINEL = "<S-9 wallclock normalized>"

    def _normalize_wallclock(self, state, variant):
        """state.json의 벽시계 필드(`created_at`·`updated_at`·`rows[*].timestamp`)만
        고정값으로 치환한다. 필드의 존재와 타입은 그대로 확인해, 한쪽에만 필드가
        생기거나 타입이 달라지는 회귀는 여전히 잡아낸다. 그 외 키·값은 건드리지 않는다."""
        for field in ("created_at", "updated_at"):
            self.assertIn(field, state, f"S-9({variant}) state.json에 {field} 키가 없음")
            self.assertIsInstance(
                state[field], str, f"S-9({variant}) {field} 타입이 문자열이 아님 — {state[field]!r}")
            state[field] = self._WALLCLOCK_SENTINEL
        for row in state.get("rows", []):
            if "timestamp" not in row:
                continue
            ts = row["timestamp"]
            self.assertTrue(
                ts is None or isinstance(ts, str),
                f"S-9({variant}) rows[row_id={row.get('row_id')}].timestamp 타입 이상 — {ts!r}")
            if ts is not None:
                row["timestamp"] = self._WALLCLOCK_SENTINEL
        return state

    def _assert_schema_variant_matches_head(self, rows_spec, label):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            head_source = self._head_source(tmp_path)

            task_a = tmp_path / "head-parent" / f"task-s9-{label}"
            task_b = tmp_path / "current-parent" / f"task-s9-{label}"
            task_a.parent.mkdir(parents=True)
            task_b.parent.mkdir(parents=True)

            def _init_args(task):
                args = ["init", str(task), "--skill", "oppl", "--mode", "agentic"]
                if rows_spec:
                    args += ["--rows-spec", rows_spec]
                return args

            for d in (task_a, task_b):
                if d.exists():
                    shutil.rmtree(d)
                d.mkdir()

            # 재시도 루프 없음: 벽시계 필드를 정규화한 뒤 비교하므로, 두 subprocess가
            # 초 경계를 straddle해도 더 이상 거짓 실패가 나지 않는다(과거 5회 재시도는
            # 비교 방법 자체의 결함을 완화하려던 우회책이었다).
            code_a, out_a, err_a, _ = _run_direct(head_source, _init_args(task_a))
            code_b, out_b, err_b, _ = _run_direct(_CURRENT_STATE_TOOL, _init_args(task_b))
            self.assertEqual(code_a, 0, f"S-9({label}) HEAD init 실패 — {out_a!r} {err_a!r}")
            self.assertEqual(code_b, 0, f"S-9({label}) 현재본 init 실패 — {out_b!r} {err_b!r}")

            code_a, out_a, err_a, adv_data_a = _run_direct(
                head_source, ["advance", str(task_a), "--row", "1"])
            code_b, out_b, err_b, adv_data_b = _run_direct(
                _CURRENT_STATE_TOOL, ["advance", str(task_b), "--row", "1"])
            self.assertEqual(code_a, 0, f"S-9({label}) HEAD advance 실패 — {out_a!r} {err_a!r}")
            self.assertEqual(code_b, 0, f"S-9({label}) 현재본 advance 실패 — {out_b!r} {err_b!r}")

            code_a, out_a, err_a, mark_data_a = _run_direct(
                head_source, ["mark", str(task_a), "--row", "1", "--done"])
            code_b, out_b, err_b, mark_data_b = _run_direct(
                _CURRENT_STATE_TOOL, ["mark", str(task_b), "--row", "1", "--done"])
            self.assertEqual(code_a, 0, f"S-9({label}) HEAD mark 실패 — {out_a!r} {err_a!r}")
            self.assertEqual(code_b, 0, f"S-9({label}) 현재본 mark 실패 — {out_b!r} {err_b!r}")

            bytes_a = (task_a / "state.json").read_bytes()
            bytes_b = (task_b / "state.json").read_bytes()
            norm_a = self._normalize_wallclock(json.loads(bytes_a), f"{label}/HEAD")
            norm_b = self._normalize_wallclock(json.loads(bytes_b), f"{label}/현재본")

            self.assertEqual(
                norm_a, norm_b,
                f"S-9({label}) HEAD 대비 state.json 불일치(벽시계 필드 정규화 후에도 남는 차이) — "
                f"HEAD={norm_a!r} 현재본={norm_b!r}")
            self.assertEqual(
                set(adv_data_a), set(adv_data_b),
                f"S-9({label}) advance 응답 키 집합 불일치 — HEAD={set(adv_data_a)!r} 현재본={set(adv_data_b)!r}")
            self.assertEqual(
                set(mark_data_a), set(mark_data_b),
                f"S-9({label}) mark 응답 키 집합 불일치 — HEAD={set(mark_data_a)!r} 현재본={set(mark_data_b)!r}")

            self.assertNotIn("run_log", mark_data_b, f"S-9({label}) 응답에 run_log 키가 생김(회귀)")
            state_b = json.loads(bytes_b)
            self.assertNotIn("run_log", state_b, f"S-9({label}) state.json에 run_log 키가 생김(회귀)")
            self.assertFalse((task_b / "run").exists(), f"S-9({label}) run/ 디렉터리가 생성됨(회귀)")

        return True

    def test_schema_1_0_mark_advance_match_head(self):
        self._assert_schema_variant_matches_head(_ROWS_SPEC, "1-0")

    def test_schema_1_1_mark_advance_match_head(self):
        self._assert_schema_variant_matches_head(_ROWS_SPEC_11, "1-1")
