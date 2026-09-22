"""
@header {
  "module": "test_state_tool_run_log",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool run-log 공개 계약을 실제 CLI와 디스크 산출물로 검증한다. shadow 초기화·비활성 경로 호환성·보관함 복구와 상한·상태 사건 원자 커밋·완전성 진단·PM 보고 및 stop 판정·schema 1.0/1.1/1.2 등록을 다루며, mock 없이 실패 조건을 실제 파일 I/O로 유발한다.",
  "exports": ["TestShadowInitPierce", "TestOffModeInitByteIdentical", "TestLegacySchemaVersionsRegistered", "TestRunLogMissingDiagnosis", "TestInterruptedInitRecovery", "TestStateChangedAtomicCommit", "TestOutboxPreservesOnWriteFailure", "TestOutboxLimits", "TestSchema12Registered", "TestOffModeTransitionUnaffected", "TestWorkerDurationDerivedAndConflict", "TestOffModeDurationPathByteIdentical", "TestAutoApprovedRowsEachGetIndependentStateChanged", "TestLogEventSurfaceForPmActivity", "TestPmActivityWhitelistRejection", "TestGateRequestResolvePairing", "TestShadowMissingIsNonBlockingDiagnosis", "TestActiveCompletionEvidenceGate", "TestVerifyCompletenessCheckThreeObservationFields", "TestCompletenessMissingPmActivityAutoApprovedRows", "TestCompletenessMissingPmActivityClearedByLoggedDecision", "TestCompletenessMissingPmActivityOverrideAnchor", "TestSchema10And11WithoutRunLogBlockUnchanged", "TestCompletenessCheckIndependentFromStructuralValidation", "TestModeInventoryEquality", "TestT147S5PmReportSurfaceAndLastReportPointer", "TestT147S6PmReportAxisEnumsAndDualValidation", "TestT147S7StopDecisionReceiptDrain", "TestT147S9StopVerdictAxesClassifyFourCases", "TestT147S10UnanchoredActivityAndProgressExclusion"],
  "scenarios": ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-9", "TEST-SCENARIO(W-7).S-8", "TEST-SCENARIO(W-7).S-9", "TASK-135.S-1", "TASK-135.S-2", "TASK-135.S-3", "TASK-135.S-4", "TASK-135.S-5", "TASK-135.S-6", "TASK-135.S-7", "TASK-135.S-8", "TASK-135.S-9", "TASK-137.S-6", "TASK-137.S-7", "TASK-137.S-8", "TASK-137.S-9", "TASK-147.S-5", "TASK-147.S-6", "TASK-147.S-7", "TASK-147.S-9", "TASK-147.S-10"]
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
    블록이 없는 1.0/1.1 태스크의 mark·advance가 **개정 전 빌드**와 바이트
    동일해야 한다는 보존 시나리오. 개정 전 빌드는 고정 커밋
    `_PRE_RUN_LOG_DEFAULT_SHA`에서 꺼낸다 — 움직이는 `HEAD` 참조를 기준으로
    쓰던 원래 방식은 기본값 전환 커밋 `f8aba0a` 머지와 동시에 자기무효화됐다
    (TASK-137 W-7에서 고정 SHA 핀으로 정정). 이 시나리오는 보존·회귀 가드이며
    구현 전 RED가 아니다 — 이 파일의 기존 동류 보존 시나리오
    (TestOffModeInitByteIdentical·TestLegacySchemaVersionsRegistered)가 각각 주석에
    `red_required=false`로 명시한 것과 같은 성격이다.

PLAN.md(T02) §테스트 시나리오 초안 근거:
  - S-1 state-tool.init.run-log-mode shadow — state.json schema_version==1.2 + run_log 7필드 +
    첫 조각(run/run-log-{run_id}-0001.jsonl) 1줄(run.started, sequence==1, actor_sequence==1)
  - S-2 (C-3) --run-log-mode off init은 개정 전 빌드(고정 커밋
    _PRE_RUN_LOG_DEFAULT_SHA에서 꺼낸 state_tool.py, 미지정 호출)와 state.json 바이트 동일
  - S-9 (C-3) legacy schema 1.0·1.1이 state.schema.json 허용 enum에 계속 등록됨
"""

import importlib.util
import json
import os
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
# [TASK-137 W-7] "개정 전 동작"의 고정 비교 기준 (택 A — 고정 커밋 SHA 핀)
#
# 이 파일의 보존 가드 3건(TestOffModeInitByteIdentical,
# TestOffModeDurationPathByteIdentical 2건)은 C-6이 요구하는 "run_log 블록이 없는
# 1.0/1.1 경로의 산출물 불변"을 판정하기 위해, 현재 빌드 자신의 출력을 정답으로
# 쓰지 않고 **개정 전 빌드를 별도 프로세스로 실행해 독립적으로 정답을 만든다**
# (self-confirming 금지).
#
# 그 기준을 원래 `git show` + 움직이는 `HEAD` 참조로 잡았던 것이 결함이었다. HEAD는
# 움직이는 참조라서, 개정이 머지되는 순간 기준 자신이 개정본이 되어 가드가
# **자기무효화**된다. 실제로 그렇게 됐다 — `f8aba0a`("chore(135): 추가작업 2건 —
# 훅 세션 소유권과 run-log 기본 활성화")가 `state-tool init`의 `--run-log-mode`
# 기본값을 미지정에서 `shadow`로 전환하고 `off`를 명시적 비활성화로 추가하면서,
# HEAD 쪽 무플래그 init이 `schema_version 1.2` + `run_log` 블록을 내기 시작했다.
# 그 뒤로 이 3건은 "개정 후 vs 개정 후"를 비교하며 영구 실패했다.
#
# 그래서 기준을 **움직이지 않는 커밋**으로 고정한다. `e842f3d`는 `f8aba0a`의
# 직전 `state_tool.py` 변경 커밋, 즉 기본값 전환이 들어오기 **직전** 빌드다.
#
# [H-4 대응 — 고정 전 실측 관측] 이 SHA를 적기 전에 실제로 꺼내 돌려서 확인했다:
#   $ git show e842f3d:./state_tool.py > <tmp>/state_tool.py
#   $ python <tmp>/state_tool.py init <task> --skill oppl --mode agentic
#   → state.json = {"schema_version": "1.0", ...}, `run_log` 키 없음, `run/` 미생성
# advance·mark 경로도 같은 빌드로 실행해 `run_log` 미생성과 1.0 유지를 확인했다.
# 관측 없이 SHA만 적으면 가드가 통과해도 아무것도 지키지 않으므로(H-4), 이 SHA를
# 바꿀 때는 위 관측을 **먼저** 재수행한다.
_PRE_RUN_LOG_DEFAULT_SHA = "e842f3dc470b3c5ad4cc953ab2fdf8d0d35bb3aa"


def _pre_revision_state_tool_source(test_case, dest_dir, scenario):
    """개정 전(`_PRE_RUN_LOG_DEFAULT_SHA`) state_tool.py를 dest_dir에 풀어 경로를 반환한다.

    HEAD가 아니라 고정 SHA를 쓰는 이유는 위 상수 주석 참조 — 움직이는 참조를 기준으로
    삼으면 개정이 머지되는 순간 가드가 자기무효화된다."""
    result = subprocess.run(
        ["git", "show", f"{_PRE_RUN_LOG_DEFAULT_SHA}:./state_tool.py"],
        cwd=str(_STATE_TOOL_DIR), capture_output=True, text=True,
    )
    test_case.assertEqual(
        result.returncode, 0,
        f"{scenario} 개정 전 기준 커밋 {_PRE_RUN_LOG_DEFAULT_SHA[:7]} 추출 실패 — {result.stderr}")
    test_case.assertTrue(
        result.stdout,
        f"{scenario} git show {_PRE_RUN_LOG_DEFAULT_SHA[:7]}:./state_tool.py 결과가 비어 있음")
    dest = pathlib.Path(dest_dir) / "state_tool.py"
    dest.write_text(result.stdout, encoding="utf-8")
    return dest


# ─────────────────────────────────────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

_CLAUDE_ADAPTER_PATH = (
    _STATE_TOOL_DIR.parent / "ownership-tool" / "ownership_tool" / "claude_adapter.py")


def _load_claude_adapter_session_id_env():
    """`claude_adapter`가 소유한 플랫폼 고유 세션 변수명 상수를 얻는다.

    [MUST] 변수명을 이 테스트에 하드코딩하지 않는다(`~/.opal/PRINCIPLES.md`
    §Core Stance 플랫폼 격리 / TASK-138 D-18·C-15 — 플랫폼 고유 이름은 어댑터
    한 곳에만 둔다). 하드코딩하면 플랫폼이 변수명을 바꾸거나 변수가 늘어났을 때
    아래 가드가 조용히 무력해진다. `test_state_tool_ownership.py`(TASK-147 W-12)가
    같은 방식을 쓴다."""
    spec = importlib.util.spec_from_file_location(
        "ownership_tool.claude_adapter", _CLAUDE_ADAPTER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SESSION_ID_ENV


_CLAUDE_SESSION_ID_ENV = _load_claude_adapter_session_id_env()


def _env_without_session_ids():
    """세션 식별자 계열 변수를 **전부 제거한** 서브프로세스 env를 만든다(H-6).

    왜 필요한가 — 앰비언트 세션 식별자가 있으면 `cmd_advance`/`cmd_mark`의
    `_claim_task_lease_if_needed()`가 lease를 claim해 `<task>/run/.runtime/`을
    만든다(TASK-138 W-9). 그러면 "run_log 비활성 태스크의 산출물은 종전과 바이트
    동일하다"(C-3·C-6)를 판정하는 보존 가드가 **실행 위치에 따라** 뒤집힌다 —
    Claude 세션 셸에서는 실패하고 변수 없는 CI에서는 통과한다. 검증 대상은
    run-log 경로의 불변성이지 lease 소유권 배선이 아니므로, 전제를 명시적으로
    고정한다(프로덕션 코드는 바꾸지 않는다).

    [MUST] `dict(os.environ)` + `update` 병합으로는 이 일을 할 수 없다 — 병합은
    **키 삭제를 전달하지 못해** 앰비언트 값이 그대로 되살아난다. 그래서 완성된
    env dict를 그대로 넘긴다(W-12가 밝힌 함정).
    """
    env = dict(os.environ)
    env.pop("OPAL_SESSION_ID", None)
    env.pop(_CLAUDE_SESSION_ID_ENV, None)
    return env


def _run(args, cwd=None, env=None):
    """run.sh를 subprocess로 실행하여 (returncode, stdout_text, stderr_text, parsed_json) 반환.

    `env`를 주면 **병합하지 않고 그대로** 서브프로세스 환경으로 쓴다 — 키 삭제를
    전달해야 하는 호출부(`_env_without_session_ids()`)가 있기 때문이다."""
    cmd = ["bash", str(_RUN_SH)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


def _run_direct(state_tool_source, args, env=None):
    """지정된 state_tool.py 소스를 venv python으로 직접 실행한다(임의 서브커맨드).
    run.sh 래퍼가 아니라 소스 파일을 직접 지정해, HEAD 사본과 현재본을 동일 조건으로
    비교할 수 있게 한다(S-9).

    `env`는 `_run()`과 같은 계약이다 — 주면 병합 없이 그대로 쓴다."""
    cmd = [str(_VENV_PYTHON), str(state_tool_source)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


def _run_init_direct(state_tool_source, task_path, run_log_mode=None):
    """지정된 state_tool.py 소스 파일을 venv python으로 직접 실행해 init 수행.
    HEAD 버전(임시 위치에 풀어놓은 사본)과 현재본을 동일 조건으로 비교하기 위해
    run.sh 래퍼가 아니라 소스 파일을 직접 지정해 실행한다.
    run_log_mode가 주어지면 --run-log-mode <값>을 덧붙인다 — HEAD 버전은 이 플래그
    자체가 choices=["shadow","active"]라 "off"를 모르므로 None으로 호출하고,
    현재본은 기본값이 shadow로 바뀌었으므로 비활성화 경로를 재현하려면 "off"를
    명시로 호출한다(재타겟: 원래 "미지정"이 하던 역할을 현재본에서는 "off"가 한다)."""
    cmd = [str(_VENV_PYTHON), str(state_tool_source), "init", str(task_path),
           "--skill", "oppl", "--mode", "agentic"]
    if run_log_mode is not None:
        cmd.extend(["--run-log-mode", run_log_mode])
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
# S-2 — --run-log-mode off 명시 init이 개정 전(미지정)과 바이트 동일 (C-3, red_required=false)
# [재타겟] 기본값이 shadow로 바뀌면서 "미지정"은 더 이상 비활성화를 뜻하지 않는다.
# 비활성화 경로의 바이트 동일성이라는 계약의 실질은 그대로이므로, 트리거를
# 현재본의 "--run-log-mode off" 명시로 옮긴다. HEAD 버전은 이 플래그를 모르므로
# (choices=["shadow","active"]) 여전히 미지정으로 호출한다.
# ─────────────────────────────────────────────────────────────────────────────

class TestOffModeInitByteIdentical(unittest.TestCase):
    def test_run_log_mode_off_init_matches_head_unflagged_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)

            # [TASK-137 W-7 — 택 A] 기준을 HEAD가 아니라 고정 SHA로 핀한다.
            # HEAD 기준은 개정(`f8aba0a`) 머지와 동시에 자기무효화됐다(상수 주석 참조).
            head_copy_dir = tmp_path / "head-copy"
            head_copy_dir.mkdir()
            head_source = _pre_revision_state_tool_source(self, head_copy_dir, "S-2")

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
                code_b, out_b, err_b = _run_init_direct(_CURRENT_STATE_TOOL, task_b, run_log_mode="off")
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
            self.assertNotIn("run_log", state_b, "S-2 --run-log-mode off인데 run_log 키가 생성됨")
            self.assertFalse((task_b / "run").exists(), "S-2 --run-log-mode off인데 run/ 디렉터리가 생성됨")


# ─────────────────────────────────────────────────────────────────────────────
# S-9 — legacy schema 1.0·1.1 병행 허용 (C-3, red_required=false)
# ─────────────────────────────────────────────────────────────────────────────

class TestLegacySchemaVersionsRegistered(unittest.TestCase):
    def test_schema_1_0_and_1_1_remain_registered(self):
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


class TestOffModeTransitionUnaffected(unittest.TestCase):
    """T05 S-7 (C-3) — --run-log-mode off로 비활성화한(1.0/1.1 상당) 태스크의 전이는
    run-log 경로를 타지 않는다. [재타겟] 기본값이 shadow가 되면서 "미지정"은 더 이상
    비활성화를 뜻하지 않으므로, 계약의 실질(비활성화 경로 무영향)은 그대로 두고
    트리거만 --run-log-mode off 명시로 옮긴다."""

    def test_transition_without_run_log_block_is_unchanged(self):
        # [H-6] 앰비언트 세션 식별자를 제거한 env로 호출한다 — 변수가 있으면 전이가
        # lease를 claim해 `run/.runtime/`이 생기고 아래 "run/ 미생성" 단언이 실행
        # 위치에 따라 뒤집힌다. 검증 축(비활성화 경로 무영향)은 그대로다.
        clean_env = _env_without_session_ids()
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp)
            code, out, errtxt, data = _run(
                ["init", str(task), "--skill", "oppl", "--mode", "agentic",
                 "--rows-spec", _ROWS_SPEC, "--run-log-mode", "off"], env=clean_env)
            self.assertEqual(code, 0, f"T05 S-7 init 실패 — {out!r}")

            code, out, errtxt, data = _run(["advance", str(task), "--row", "1"],
                                           env=clean_env)
            self.assertEqual(code, 0, f"T05 S-7 advance 실패 — {out!r}")
            self.assertNotIn("run_log", data, "T05 S-7 off 태스크 응답에 run_log 키가 생김")

            state = _read_state(task)
            self.assertNotIn("run_log", state, "T05 S-7 off 태스크 state.json에 run_log 키가 생김")
            self.assertFalse((task / "run").exists(), "T05 S-7 off 태스크에 run/ 생성됨")

            code, out, errtxt, data = _run(["validate", str(task)], env=clean_env)
            self.assertEqual(code, 0, f"T05 S-7 off 태스크 validate 실패 — {out!r}")
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


class TestOffModeDurationPathByteIdentical(unittest.TestCase):
    """S-9 (C-3, H-6) — --run-log-mode off로 비활성화한(run_log 블록 없는 1.0/1.1
    상당) 태스크의 `mark`·`advance`가 개정 전 빌드(미지정 호출)와 산출물·응답 키
    집합 바이트 동일해야 한다(파생 조회 미호출의 대리 판정). [재타겟] 기본값이
    shadow가 되면서 "미지정"은 더 이상 비활성화를 뜻하지 않으므로, 현재본만
    --run-log-mode off를 명시해 호출한다 — 개정 전 빌드는 이 플래그를 모르므로
    (choices=["shadow","active"]) 미지정 그대로 둔다. 계약의 실질(비활성화 경로의
    산출물·응답 키 바이트 동일성)은 바뀌지 않는다.

    self-confirming 금지(PM 하네스 가드) — 현재 빌드 자신의 출력을 정답으로 쓰지
    않고, 개정 전 빌드를 별도 프로세스로 실행해 독립적으로 정답을 만든다(S-2와
    동일 기법). `_import_run_log_core()`가 sibling 배치를 우선하므로, 개정 전 사본은
    `opal/tools/{state-tool,run-log-tool}` 형제 구조를 그대로 복제해 두지 않으면
    빌드 위치 차이만으로 거짓 실패가 난다 — 아래 `_head_source()`가 그 구조를 만든다.

    [TASK-137 W-7 — 택 A로 정정] 비교 기준은 고정 커밋
    `_PRE_RUN_LOG_DEFAULT_SHA`다. 원래는 움직이는 `HEAD`를 기준으로 삼았는데,
    기본값 전환 커밋 `f8aba0a`가 머지되며 기준 자신이 개정본이 되어 이 두
    테스트가 영구 실패했다(개정 후 vs 개정 후를 비교). 고정 SHA 핀으로 원래의
    검증 축(비활성화 경로 산출물·응답 키 불변)을 그대로 유지한 채 자기무효화만
    제거한다. SHA 선정 근거와 H-4 실측 관측은 상수 주석 참조.

    [벽시계 필드 정규화] 두 빌드는 별도 subprocess로 순차 실행되므로
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

        # [TASK-137 W-7 — 택 A] 기준을 HEAD가 아니라 고정 SHA로 핀한다(상수 주석 참조).
        _pre_revision_state_tool_source(self, st_dir, "S-9")

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
        # [H-6] 두 빌드 모두 앰비언트 세션 식별자를 제거한 env로 실행한다. 변수가
        # 있으면 현재본의 `advance`/`mark`만 lease를 claim해(개정 전 빌드에는 그
        # 코드가 없다) `run/.runtime/`이 생기고, 아래 "run/ 미생성" 단언이 실행
        # 위치에 따라 뒤집힌다. 비교 대칭성을 위해 양쪽에 같은 env를 준다.
        clean_env = _env_without_session_ids()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            head_source = self._head_source(tmp_path)

            task_a = tmp_path / "head-parent" / f"task-s9-{label}"
            task_b = tmp_path / "current-parent" / f"task-s9-{label}"
            task_a.parent.mkdir(parents=True)
            task_b.parent.mkdir(parents=True)

            def _init_args(task, off=False):
                args = ["init", str(task), "--skill", "oppl", "--mode", "agentic"]
                if rows_spec:
                    args += ["--rows-spec", rows_spec]
                if off:
                    args += ["--run-log-mode", "off"]
                return args

            for d in (task_a, task_b):
                if d.exists():
                    shutil.rmtree(d)
                d.mkdir()

            # 재시도 루프 없음: 벽시계 필드를 정규화한 뒤 비교하므로, 두 subprocess가
            # 초 경계를 straddle해도 더 이상 거짓 실패가 나지 않는다(과거 5회 재시도는
            # 비교 방법 자체의 결함을 완화하려던 우회책이었다). 현재본만 --run-log-mode
            # off를 명시한다 — HEAD는 이 값을 모르므로 미지정 그대로 호출한다.
            code_a, out_a, err_a, _ = _run_direct(
                head_source, _init_args(task_a), env=clean_env)
            code_b, out_b, err_b, _ = _run_direct(
                _CURRENT_STATE_TOOL, _init_args(task_b, off=True), env=clean_env)
            self.assertEqual(code_a, 0, f"S-9({label}) HEAD init 실패 — {out_a!r} {err_a!r}")
            self.assertEqual(code_b, 0, f"S-9({label}) 현재본 init 실패 — {out_b!r} {err_b!r}")

            code_a, out_a, err_a, adv_data_a = _run_direct(
                head_source, ["advance", str(task_a), "--row", "1"], env=clean_env)
            code_b, out_b, err_b, adv_data_b = _run_direct(
                _CURRENT_STATE_TOOL, ["advance", str(task_b), "--row", "1"], env=clean_env)
            self.assertEqual(code_a, 0, f"S-9({label}) HEAD advance 실패 — {out_a!r} {err_a!r}")
            self.assertEqual(code_b, 0, f"S-9({label}) 현재본 advance 실패 — {out_b!r} {err_b!r}")

            code_a, out_a, err_a, mark_data_a = _run_direct(
                head_source, ["mark", str(task_a), "--row", "1", "--done"], env=clean_env)
            code_b, out_b, err_b, mark_data_b = _run_direct(
                _CURRENT_STATE_TOOL, ["mark", str(task_b), "--row", "1", "--done"],
                env=clean_env)
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


# ═════════════════════════════════════════════════════════════════════════════
# TASK-135 (opds-run-log-기록완전성) W-1 RED — opal-test-agent red mode
#
# 아래 시나리오 ID(`TASK-135.S-1`..`S-9`)는 태스크 135의
# tasks/135-260915-opds-run-log-기록완전성/TEST-SCENARIO.md 표를 가리키며,
# 위 T02/T05 구간·W-7 구간의 재사용된 `S-1`..`S-9` 번호와는 별개의 ID 공간이다
# (파일 내 세 번째로 재사용되는 번호대이므로 접두 `TASK-135.`로 구분한다).
#
# 각 클래스는 PLAN.md W-1이 지정한 GREEN 담당 Work item을 주석으로 태깅한다:
#   ① TASK-135.S-4 자동승인 독립 state.changed  → GREEN: W-2
#   ② TASK-135.S-2 state-tool log-event 표면    → GREEN: W-3
#   ③ TASK-135.S-5 gate-request/gate-resolve    → GREEN: W-3
#   ④ TASK-135.S-6 shadow 누락 비차단 진단       → GREEN: W-4
#   ⑤ TASK-135.S-7 active completion 증거 게이트 → GREEN: W-4
#   ⑥ TASK-135.S-8 verify --run-log-completeness-check 3필드 → GREEN: W-4
#   + TASK-135.S-1 mode별 인벤토리 동일성        → GREEN: W-2/W-3/W-4 종합
#   + TASK-135.S-3 PM activity 화이트리스트 거부  → GREEN: W-3
#   + TASK-135.S-9 구조검증/상태대조 분리 + 의존방향 → GREEN: W-4
#
# mock/patch/MagicMock 미사용. 공개 CLI(run.sh subprocess)와 실제 파일 I/O만
# 사용한다(harness/red-first.md §2, TEST-SCENARIO.md Setup).
# ═════════════════════════════════════════════════════════════════════════════

_ROWS_SPEC_USER_CONFIRM_X2 = json.dumps([
    {"stage": "EXECUTE", "item": "사용자 확인"},
    {"stage": "EXECUTE", "item": "사용자 확인"},
    {"stage": "TEST", "item": "검증"},
], ensure_ascii=False)


class TestAutoApprovedRowsEachGetIndependentStateChanged(unittest.TestCase):
    """TASK-135.S-4 (AC-3, AC-8, C-1, C-4, C-5, C-6, H-1) — GREEN: W-2.

    자동 승인 2건 + 대상 전이 1건이 각각 독립 `state.changed`로 남고
    순서·from/to·row_key가 state.json과 일치해야 한다(부분 admission 없음).

    현재 관찰: auto_approve_prior_user_confirmations()는 앞 두 '사용자 확인' 행을
    in-place로 done 처리하지만, advance 호출부(state_tool.py:2348 부근)는
    대상 행 전이의 state.changed 1건만 build_state_changed_event()로 만든다.
    따라서 실제로는 상태 변경 3건이 일어나지만 JSONL에는 1건만 남는다 — 이것이
    RED로 고정하려는 불일치다.
    """

    def test_two_auto_approvals_and_target_transition_each_log_state_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="135-auto-approve")
            code, out, err, data = _run([
                "init", str(task), "--skill", "oppl", "--mode", "agentic",
                "--rows-spec", _ROWS_SPEC_USER_CONFIRM_X2,
                "--run-log-mode", "shadow",
            ])
            self.assertEqual(code, 0, f"TASK-135.S-4 init 실패 — {out!r} {err!r}")

            # 대상 행(row_id=3, TEST/검증)으로 advance — 앞의 두 '사용자 확인' 행이
            # 자동 승인되면서 함께 전이되어야 한다.
            code, out, err, data = _run(["advance", str(task), "--row", "3"])
            self.assertEqual(code, 0, f"TASK-135.S-4 advance 실패 — {out!r} {err!r}")
            self.assertEqual(data.get("auto_approved"), [1, 2],
                             f"TASK-135.S-4 자동승인 대상이 예상과 다름 — {data!r}")

            state = _read_state(task)
            rows = state["rows"]
            self.assertEqual(rows[0]["status"], "done")
            self.assertEqual(rows[1]["status"], "done")
            self.assertEqual(rows[2]["status"], "in_progress")

            changed = [r for r in _segment_records(task) if r["event"] == "state.changed"]
            self.assertEqual(
                len(changed), 3,
                f"TASK-135.S-4 state.changed가 3건이 아님(부분 admission) — {len(changed)}건: {changed!r}")

            by_row_key = {c["data"].get("row_key"): c for c in changed}
            self.assertEqual(len(by_row_key), 3,
                             f"TASK-135.S-4 row_key 3종이 아님 — {by_row_key.keys()!r}")

            for c in changed:
                self.assertIn("row_key", c["data"], f"TASK-135.S-4 row_key 누락 — {c!r}")
                self.assertIn("from", c["data"])
                self.assertIn("to", c["data"])

            seqs = [c["sequence"] for c in changed]
            self.assertEqual(seqs, sorted(seqs),
                             f"TASK-135.S-4 state.changed 순서가 단조 증가가 아님 — {seqs!r}")


class TestLogEventSurfaceForPmActivity(unittest.TestCase):
    """TASK-135.S-2 (AC-2, C-3, C-5, H-2) — GREEN: W-3.

    surfaces.json이 선언한 `state-tool.log-event`로 PM decision/validation/retry를
    summary·reason·refs와 함께 기록하고 조회할 수 있어야 한다.

    현재 관찰: state_tool.py에 `log-event` 서브파서가 존재하지 않는다
    (add_parser("log-event") 0건 실측). argparse가 미지정 서브커맨드로 거부한다.
    """

    def test_log_event_records_pm_decision_activity(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="135-log-event")
            code, out, err, data = _init_shadow(task)
            self.assertEqual(code, 0, f"TASK-135.S-2 init 실패 — {out!r} {err!r}")

            code, out, err, data = _run([
                "log-event", str(task),
                "--event", "activity", "--kind", "decision",
                "--summary", "PM이 W-1 RED 작성을 승인함",
                "--reason", "TEST-SCENARIO S-2 판정 근거",
                "--refs", "tasks/135-260915-opds-run-log-기록완전성/PLAN.md",
            ])
            self.assertEqual(
                code, 0,
                f"TASK-135.S-2 log-event 서브커맨드 부재로 실패(미구현 RED) — "
                f"exit={code} stdout={out!r} stderr={err!r}")

            activities = [r for r in _segment_records(task)
                          if r["event"] == "activity" and r["actor"]["kind"] == "PM"]
            self.assertEqual(len(activities), 1, f"TASK-135.S-2 PM activity 1건이 아님 — {activities!r}")
            act = activities[0]
            self.assertEqual(act["data"]["kind"], "decision")
            self.assertEqual(act["summary"], "PM이 W-1 RED 작성을 승인함")
            self.assertEqual(act["reason"], "TEST-SCENARIO S-2 판정 근거")
            self.assertIn("tasks/135-260915-opds-run-log-기록완전성/PLAN.md", act.get("refs") or [])


class TestPmActivityWhitelistRejection(unittest.TestCase):
    """TASK-135.S-3 (C-3, C-5, H-2) — GREEN: W-3.

    CONTRACT §1.3 PM activity 폐쇄 목록 밖의 `data` 키, 절대경로 refs, 비밀값
    포함 입력을 `log-event`/append 경로가 거부하거나 정규화·redact해야 한다.
    CONTRACT §1.1 공통 필드는 거부 대상이 아니다(§1.3이 명시).

    현재 관찰: `log-event` 서브커맨드 자체가 없어 화이트리스트 판정 이전
    단계에서 실패한다(미구현 RED, 위 S-2와 같은 근본 원인이지만 독립 판정 대상).
    """

    def test_disallowed_data_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="135-whitelist-key")
            self.assertEqual(_init_shadow(task)[0], 0)

            code, out, err, data = _run([
                "log-event", str(task),
                "--event", "activity", "--kind", "decision",
                "--summary", "s",
                "--data", json.dumps({"kind": "decision", "raw_prompt": "내부 사고 과정 원문"}),
            ])
            self.assertNotEqual(
                code, 0,
                "TASK-135.S-3 화이트리스트 밖 data 키(raw_prompt)가 거부되지 않음(미구현 RED 기대와 불일치)")
            self.assertIn(
                "schema_invalid", (out + err),
                f"TASK-135.S-3 거부 사유가 schema_invalid로 식별되지 않음 — out={out!r} err={err!r}")

    def test_absolute_path_refs_rejected_or_normalized(self):
        """PM Gate 보강(루핑 1) — exit code만이 아니라 CONTRACT §2.1 오류 봉투
        (`{"ok": false, "error": {"code": ...}}`)까지 요구하도록 조인다.

        [BLOCKER] 절대경로 refs 거부 전용 오류 코드는 CONTRACT §2.2 오류 코드 표,
        surfaces.json의 `state-tool.log-event` err 집합([actor_not_allowed,
        run_log_pending, run_log_outbox_full, run_log_write_failed,
        task_path_not_absolute, task_lock_timeout]), RUN_LOG_STATE_ERROR_CODES
        어디에도 선언되어 있지 않다(2026-09-16 3원천 실측). `schema_invalid`는
        같은 CONTRACT가 "§1.1 폐쇄형 최상위 키와 개별 필드 enum 위반에만 쓴다"고
        명시적으로 범위를 좁혀 두어 refs(array<string> 경로 제약)에 임의로
        전용하면 안 된다. 따라서 여기서는 특정 코드값을 발명하지 않고 **구조화
        오류 봉투(ok:false + error.code 존재)까지만** 조인다 — 코드값 확정은
        W-5가 CONTRACT/surfaces.json에서 이 계약 공백을 메운 뒤의 몫이다.
        """
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="135-whitelist-refs")
            self.assertEqual(_init_shadow(task)[0], 0)

            code, out, err, data = _run([
                "log-event", str(task),
                "--event", "activity", "--kind", "progress",
                "--summary", "s",
                "--refs", "/etc/passwd",
            ])
            if code == 0:
                activities = [r for r in _segment_records(task) if r["event"] == "activity"]
                self.assertTrue(activities, "TASK-135.S-3 activity가 기록되지 않음")
                refs = activities[-1].get("refs") or []
                self.assertNotIn("/etc/passwd", refs,
                                 f"TASK-135.S-3 절대경로 refs가 원문 그대로 저장됨 — {refs!r}")
            else:
                self.assertNotEqual(code, 0,
                    "TASK-135.S-3 절대경로 refs 거부 확인(미구현 RED — log-event 부재로 실패)")
                self.assertIsInstance(
                    data, dict,
                    f"TASK-135.S-3 stdout이 CONTRACT §2.1 JSON 오류 봉투가 아님 — {out!r}")
                self.assertEqual(
                    data.get("ok"), False,
                    f"TASK-135.S-3 오류 봉투의 ok가 false가 아님 — {data!r}")
                self.assertIn(
                    "code", data.get("error", {}) if isinstance(data.get("error"), dict) else {},
                    f"TASK-135.S-3 오류 봉투에 error.code가 없음(CONTRACT §2.1) — {data!r}")


class TestGateRequestResolvePairing(unittest.TestCase):
    """TASK-135.S-5 (AC-4, C-4, C-5) — GREEN: W-3.

    `gate-request` → `gate-resolve` 정상 쌍은 기록되고, 요청 없는 resolve와
    중복 resolve는 무변경 구조화 오류(gate_not_requested/gate_duplicate)로
    거부되어야 한다.

    현재 관찰: `gate-request`/`gate-resolve` 서브파서가 state_tool.py에 없다
    (add_parser 0건 실측).
    """

    def test_gate_request_then_resolve_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="135-gate-pair")
            self.assertEqual(_init_shadow(task)[0], 0)

            gate_id = f"gate_{uuid.uuid4()}"
            code, out, err, data = _run([
                "gate-request", str(task), "--gate-id", gate_id, "--summary", "PM Gate 요청",
            ])
            self.assertEqual(code, 0, f"TASK-135.S-5 gate-request 미구현으로 실패(RED) — {out!r} {err!r}")

            code, out, err, data = _run([
                "gate-resolve", str(task), "--gate-id", gate_id,
                "--verdict", "approved", "--owner", "PM",
            ])
            self.assertEqual(code, 0, f"TASK-135.S-5 gate-resolve 실패 — {out!r} {err!r}")

            requested = [r for r in _segment_records(task) if r["event"] == "gate.requested"]
            resolved = [r for r in _segment_records(task) if r["event"] == "gate.resolved"]
            self.assertEqual(len(requested), 1, f"TASK-135.S-5 gate.requested 1건이 아님 — {requested!r}")
            self.assertEqual(len(resolved), 1, f"TASK-135.S-5 gate.resolved 1건이 아님 — {resolved!r}")
            self.assertEqual(requested[0]["gate_id"], gate_id)
            self.assertEqual(resolved[0]["gate_id"], gate_id)

    def test_resolve_without_request_rejected(self):
        """PM Gate 보강(루핑 1) — exit code뿐 아니라 `error.code == "gate_not_requested"`
        까지 단언한다. 코드 확정 근거: CONTRACT §2.2 오류 코드 표
        ("gate_not_requested | 선행 gate.requested 없는 gate.resolved | 거부 | §4.4",
        docs/run-log/CONTRACT.md:381) + §2.2.1 오류 코드↔표면 대응
        ("gate_not_requested | state-tool.gate-resolve", CONTRACT.md:429) +
        surfaces.json의 `state-tool.gate-resolve` err 배열에 `gate_not_requested`
        선언(둘 다 계약 확정, RUN_LOG_STATE_ERROR_CODES 구현 테이블은 아직
        미등재 — 이는 W-3 GREEN의 몫이라 여기서 발명하지 않는다)."""
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="135-gate-orphan")
            self.assertEqual(_init_shadow(task)[0], 0)

            gate_id = f"gate_{uuid.uuid4()}"
            code, out, err, data = _run([
                "gate-resolve", str(task), "--gate-id", gate_id,
                "--verdict", "approved", "--owner", "PM",
            ])
            self.assertNotEqual(code, 0, "TASK-135.S-5 선행 요청 없는 resolve가 거부되지 않음")
            gate_events = [r for r in _segment_records(task) if r["event"].startswith("gate.")]
            self.assertEqual(gate_events, [],
                             "TASK-135.S-5 거부된 resolve가 무변경이 아니라 gate 사건을 남김")
            self.assertIsInstance(
                data, dict,
                f"TASK-135.S-5 stdout이 CONTRACT §2.1 JSON 오류 봉투가 아님 — {out!r}")
            self.assertEqual(
                (data.get("error") or {}).get("code"), "gate_not_requested",
                f"TASK-135.S-5 오류 코드가 gate_not_requested가 아님(CONTRACT §2.2/§2.2.1, "
                f"surfaces.json state-tool.gate-resolve) — {data!r} stderr={err!r}")

    def test_duplicate_resolve_rejected(self):
        """PM Gate 보강(루핑 1) — `error.code == "gate_duplicate"`까지 단언한다.
        코드 확정 근거: CONTRACT §2.2 오류 코드 표
        ("gate_duplicate | 같은 gate_id의 중복 requested 또는 중복 resolved | 거부 | §4.4",
        docs/run-log/CONTRACT.md:382) + §2.2.1
        ("gate_duplicate | state-tool.gate-request, .gate-resolve", CONTRACT.md:430) +
        surfaces.json의 `state-tool.gate-request`/`.gate-resolve` err 배열에
        `gate_duplicate` 선언(계약 확정, 구현 테이블 미등재는 W-3 GREEN의 몫)."""
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="135-gate-dup")
            self.assertEqual(_init_shadow(task)[0], 0)

            gate_id = f"gate_{uuid.uuid4()}"
            _run(["gate-request", str(task), "--gate-id", gate_id, "--summary", "PM Gate"])
            code1, out1, err1, _ = _run([
                "gate-resolve", str(task), "--gate-id", gate_id,
                "--verdict", "approved", "--owner", "PM",
            ])
            before = _segment_records(task)
            code2, out2, err2, data2 = _run([
                "gate-resolve", str(task), "--gate-id", gate_id,
                "--verdict", "approved", "--owner", "PM",
            ])
            self.assertNotEqual(code2, 0, "TASK-135.S-5 중복 resolve가 거부되지 않음(미구현 RED)")
            after = _segment_records(task)
            self.assertEqual(before, after, "TASK-135.S-5 거부된 중복 resolve가 조각을 변경함")
            self.assertIsInstance(
                data2, dict,
                f"TASK-135.S-5 stdout이 CONTRACT §2.1 JSON 오류 봉투가 아님 — {out2!r}")
            self.assertEqual(
                (data2.get("error") or {}).get("code"), "gate_duplicate",
                f"TASK-135.S-5 오류 코드가 gate_duplicate가 아님(CONTRACT §2.2/§2.2.1, "
                f"surfaces.json state-tool.gate-request/.gate-resolve) — {data2!r} stderr={err2!r}")


class TestShadowMissingIsNonBlockingDiagnosis(unittest.TestCase):
    """TASK-135.S-6 (AC-5, C-1, C-5, H-1) — GREEN: W-4.

    쓰기 불가 조각(권한 제거로 기록 실패 유발)이 있는 shadow run에서 상태 전이는
    exit 0으로 완료되고, 누락 범위·원인이 `run_log_pending`/완전성 진단으로
    식별되어야 한다.

    현재 관찰: `verify --run-log-completeness-check` 플래그가 없어 완전성
    진단 자체를 조회할 수 없다(미구현 RED). 상태 전이의 exit 0 유지는
    이미 통과하는 기존 성질이므로 이 테스트는 완전성 진단 조회 실패로 RED다.
    """

    def test_transition_stays_exit0_and_completeness_diagnoses_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp)
            self.assertEqual(_init_shadow(task)[0], 0)

            run_dir = task / "run"
            for seg in run_dir.glob("run-log-*.jsonl"):
                seg.chmod(0o400)
            try:
                code, out, err, data = _run(["advance", str(task), "--row", "1"])
                self.assertEqual(code, 0, f"TASK-135.S-6 기록 실패에도 exit 0이어야 함 — {out!r} {err!r}")
            finally:
                for seg in run_dir.glob("run-log-*.jsonl"):
                    seg.chmod(0o600)

            code, out, err, data = _run([
                "verify", str(task), "--run-log-completeness-check",
            ])
            self.assertEqual(
                code, 0,
                f"TASK-135.S-6 --run-log-completeness-check 미구현으로 실패(RED) — "
                f"exit={code} stdout={out!r} stderr={err!r}")
            missing = data.get("missing_state_changed", []) + data.get("missing", {}).get(
                "missing_state_changed", []) if isinstance(data.get("missing"), dict) else data.get(
                "missing_state_changed", [])
            self.assertTrue(missing, f"TASK-135.S-6 누락 진단이 비어 있음 — {data!r}")


class TestActiveCompletionEvidenceGate(unittest.TestCase):
    """TASK-135.S-7 (AC-6, C-2, H-4) — GREEN: W-4.

    completion profile이 요구하는 trusted 증거가 부족·모순인 active fixture는
    완료 전이를 거부해야 하고, profiles.json에 없는 channel의 active init은
    `profile_not_found`로 거부되어야 한다(임의 profile 승격 없음).

    현재 관찰: `state-tool init --run-log-mode active`는 채널·profiles.json
    유효성과 무관하게 무조건 profile_not_found로 거부한다(active 3종 분기
    미구현, state_tool.py:1990 부근). 따라서 "정당한 채널의 active init 성공"
    자체가 지금은 항상 실패하며, 이것이 이 테스트가 고정하는 RED다. 반대로
    "미승인 channel의 profile_not_found 거부"는 이 무조건 거부 때문에 이미
    참으로 관측되므로(우연히 통과) 별도 메서드로 분리해 회귀 없이 문서화한다.
    """

    def test_unassigned_channel_active_init_rejected_profile_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="135-active-unassigned")
            task.mkdir(exist_ok=True)
            code, out, err, data = _run([
                "init", str(task), "--skill", "oppl", "--mode", "agentic",
                "--run-log-mode", "active", "--channel-id", "no-such-channel",
            ])
            self.assertNotEqual(code, 0, "TASK-135.S-7 미승인 channel의 active init이 거부되지 않음")
            self.assertIn("profile_not_found", out + err,
                         f"TASK-135.S-7 거부 사유가 profile_not_found가 아님 — {out!r} {err!r}")

    def test_assigned_channel_active_init_succeeds_then_completion_requires_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="135-active-assigned")
            task.mkdir(exist_ok=True)
            profiles_path = pathlib.Path(tmp) / "profiles.json"
            profiles_path.write_text(json.dumps({
                "schema_version": "1.0",
                "produced_by": "135-fixture",
                "channels": [{
                    "channel_id": "pm-agent-tool",
                    "completion_profile": "observed_trajectory",
                    "adapter_id": "agent-tool-adapter",
                    "adapter_sha256": "0" * 64,
                    "receipt_sha256": "0" * 64,
                    "evidence_paths": ["evidence/pm-agent-tool/start.json"],
                }],
            }, ensure_ascii=False), encoding="utf-8")

            code, out, err, data = _run([
                "init", str(task), "--skill", "oppl", "--mode", "agentic",
                "--run-log-mode", "active", "--channel-id", "pm-agent-tool",
                "--profiles", str(profiles_path),
            ])
            self.assertEqual(
                code, 0,
                f"TASK-135.S-7 배정된 channel의 active init이 실패함(active 3종 미구현 RED) — "
                f"exit={code} stdout={out!r} stderr={err!r}")

            # trusted activity/terminal 증거 없이 완료를 시도하면 completion_evidence_missing이어야 한다.
            code, out, err, data = _run(["mark", str(task), "--row", "1", "--done"])
            self.assertNotEqual(
                code, 0,
                "TASK-135.S-7 증거 부족한데 active 완료가 통과함(completion gate 약화)")
            self.assertIn("completion_evidence_missing", out + err,
                         f"TASK-135.S-7 거부 사유가 completion_evidence_missing이 아님 — {out!r} {err!r}")


class TestVerifyCompletenessCheckThreeObservationFields(unittest.TestCase):
    """TASK-135.S-8 (AC-7, AC-8, C-3) — GREEN: W-4.

    `state-tool verify --run-log-completeness-check`는
    `last_observed_decision`·`last_observed_state_change`·`last_observed_boundary`
    3필드를 반환해야 하며, "TASK 보고 후 중단" 재현 fixture에서 서로 다른
    event_id/ts로 채워지고 다음 stage 진입 행이 missing_state_changed에
    실려야 한다.

    현재 관찰: `--run-log-completeness-check` 플래그가 verify 서브파서에
    없다(argparse가 미지정 인자로 거부, 미구현 RED).
    """

    def test_three_observation_fields_returned_and_missing_next_stage_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="135-completeness-fields")
            code, out, err, data = _run([
                "init", str(task), "--skill", "oppl", "--mode", "agentic",
                "--rows-spec", _ROWS_SPEC, "--run-log-mode", "shadow",
            ])
            self.assertEqual(code, 0, f"TASK-135.S-8 init 실패 — {out!r} {err!r}")

            # 첫 행 advance+mark로 "의사결정/상태전이"까지는 관측되게 하고,
            # 다음 stage(행 2) 진입 state.changed는 의도적으로 만들지 않는다
            # (TASK 보고 후 중단 재현 — advance만 걸고 mark하지 않음).
            self.assertEqual(_run(["advance", str(task), "--row", "1"])[0], 0)
            self.assertEqual(_run(["mark", str(task), "--row", "1", "--done"])[0], 0)

            code, out, err, data = _run([
                "verify", str(task), "--run-log-completeness-check",
            ])
            self.assertEqual(
                code, 0,
                f"TASK-135.S-8 --run-log-completeness-check 미구현으로 실패(RED) — "
                f"exit={code} stdout={out!r} stderr={err!r}")

            for field in ("last_observed_decision", "last_observed_state_change", "last_observed_boundary"):
                self.assertIn(field, data, f"TASK-135.S-8 {field} 필드 부재 — {data!r}")

            decision = data.get("last_observed_decision") or {}
            state_change = data.get("last_observed_state_change") or {}
            if decision.get("event_id") and state_change.get("event_id"):
                self.assertNotEqual(
                    decision.get("event_id"), state_change.get("event_id"),
                    "TASK-135.S-8 last_observed_decision/state_change가 같은 event_id를 가리킴")

            missing = data.get("missing_state_changed", [])
            self.assertTrue(missing, f"TASK-135.S-8 다음 stage 진입 누락이 missing_state_changed에 없음 — {data!r}")


# ═════════════════════════════════════════════════════════════════════════════
# TASK-137 W-3 — 완전성 진단 `missing_pm_activity` 트리거 양방향
#
#   TASK-137.S-6 (AC-3, C-2, C-3) 앵커 ① 충족 방향      → GREEN: W-5 [구현 전 RED]
#   TASK-137.S-7 (AC-3, C-2, H-2) 앵커 ① 미충족 방향    → GREEN: W-5 [구현 전 RED]
#   TASK-137.S-8 (AC-3, C-2)      앵커 ② override       → GREEN: W-5 [구현 전 RED]
#   TASK-137.S-9 (C-6)            1.0/1.1 보존·회귀 가드 → 현 구현에서도 통과
#
# 기대값의 유일한 원천은 `docs/run-log/CONTRACT.md` §2.5
# 『`missing_pm_activity`의 트리거 조건』 조문이다(앵커 2종·대조 술어·대조 집합·
# 범위 한정 3항·정렬·항목 형태). PLAN D-1~D-6, D-13.
#
# 판정은 `run.sh` subprocess 실호출 반환값·exit code와 `state.json` 실제 바이트로만
# 한다 — `_run_log_completeness_check()`를 직접 import하지 않는다
# (harness/red-first.md §2). mock/patch/MagicMock 미사용.
# ═════════════════════════════════════════════════════════════════════════════

_PIPELINE_SPEC_KEYED = {
    "spec_version": "1.0",
    "skill": "oppl",
    "meta": {"name": "137-w3-fixture"},
    "task_steps": [
        {"id": 1, "stage": "EXECUTE", "item": "구현 A", "key": "execute.impl_a"},
        {"id": 2, "stage": "EXECUTE", "item": "구현 B", "key": "execute.impl_b"},
        {"id": 3, "stage": "TEST", "item": "검증", "key": "test.verify"},
    ],
}

_ROWS_SPEC_KEYLESS = json.dumps([
    {"stage": "EXECUTE", "item": "구현 A"},
    {"stage": "TEST", "item": "검증"},
], ensure_ascii=False)

_ANCHOR_ITEM_KEYS = {"row_id", "row_key", "stage", "expected", "anchor"}


def _write_keyed_pipeline(tmp):
    """`key`를 가진 rows[]를 만들기 위한 pipeline.json fixture를 tmp에 쓴다.

    `--rows-spec` 경로는 `key`를 만들지 않아(state_tool.build_rows_from_spec) 앵커 ①의
    대조 주소가 생기지 않는다(CONTRACT §2.5 범위 한정 (a)). `--rows-from <pipeline.json>`
    경로만 `key` 보유 행 + schema 1.1/1.2를 만든다.
    """
    spec_path = pathlib.Path(tmp) / "pipeline.json"
    spec_path.write_text(json.dumps(_PIPELINE_SPEC_KEYED, ensure_ascii=False), encoding="utf-8")
    return spec_path


def _init_keyed(task_path, spec_path, run_log_mode="shadow"):
    args = ["init", str(task_path), "--skill", "oppl", "--mode", "agentic",
            "--rows-from", str(spec_path)]
    if run_log_mode is not None:
        args.extend(["--run-log-mode", run_log_mode])
    return _run(args)


def _state_bytes(task_path):
    return (pathlib.Path(task_path) / "state.json").read_bytes()


def _completeness(task_path):
    """`verify --run-log-completeness-check`를 실호출하고
    (exit, data, state.json 바이트 불변 여부)를 함께 돌려준다(C-3 read-only 판정용)."""
    before = _state_bytes(task_path)
    code, out, err, data = _run(["verify", str(task_path), "--run-log-completeness-check"])
    after = _state_bytes(task_path)
    return code, out, err, data, (before == after)


def _make_auto_approved_fixture(tmp, name):
    """앵커 ① fixture — `status="done"` ∧ `owner="auto"` ∧ `key` 보유 행 2건
    (row_id 1, 2)을 만들고 3행은 pending으로 남긴다. PM `activity(decision)`은
    아직 하나도 기록하지 않는다."""
    spec_path = _write_keyed_pipeline(tmp)
    task = _mktask(tmp, name=name)
    code, out, err, _ = _init_keyed(task, spec_path)
    assert code == 0, f"init 실패 — {out!r} {err!r}"
    for key in ("execute.impl_a", "execute.impl_b"):
        code, out, err, _ = _run(["mark", str(task), "--task-step", key, "--done", "--owner", "auto"])
        assert code == 0, f"mark --owner auto 실패({key}) — {out!r} {err!r}"
    return task


class TestCompletenessMissingPmActivityAutoApprovedRows(unittest.TestCase):
    """TASK-137.S-6 (AC-3, C-2, C-3) — GREEN: W-5. **구현 전 RED**.

    CONTRACT §2.5 앵커 ①: `rows[]` 중 `status == "done"` ∧ `owner == "auto"` ∧ `key`
    보유 행에 대해 `event=="activity"` ∧ `actor.kind=="PM"` ∧ `data.kind=="decision"`
    ∧ `task_step == row.key`인 사건이 하나도 없으면 그 행마다 1건을 싣는다.
    정렬은 `row_id` 오름차순(§2.5 정렬), 항목은 5키 고정(§2.5 항목 형태).

    현재 관찰: `_run_log_completeness_check()`의 누락 ④ 자리(state_tool.py:1371)가
    "최소 구현" 주석만 있고 `missing_pm_activity`를 초기화값 `[]`에서 갱신하지
    않는다. 따라서 이 시나리오는 빈 배열로 실패한다(미구현 RED).
    """

    def test_auto_approved_rows_without_pm_decision_are_listed_in_row_id_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _make_auto_approved_fixture(tmp, "137-s6-auto-approved")

            code, out, err, data, unchanged = _completeness(task)

            self.assertEqual(code, 0, f"TASK-137.S-6 진단이 exit 0이 아님(C-3 비차단 위반) — "
                                      f"exit={code} stdout={out!r} stderr={err!r}")
            self.assertTrue(unchanged, "TASK-137.S-6 read-only 진단이 state.json 바이트를 변경함(C-3)")

            missing = data.get("missing_pm_activity")
            self.assertTrue(
                missing,
                f"TASK-137.S-6 자동 승인 행 2건에 대응 PM activity(decision)가 없는데 "
                f"missing_pm_activity가 비어 있음(미구현 RED) — {data!r}")

            for item in missing:
                self.assertEqual(
                    set(item.keys()), _ANCHOR_ITEM_KEYS,
                    f"TASK-137.S-6 항목 키 집합이 §2.5 항목 형태 5키와 다름 — {item!r}")
                self.assertEqual(item["expected"], "activity(decision)",
                                 f"TASK-137.S-6 expected 값 불일치 — {item!r}")
                self.assertEqual(item["anchor"], "auto_approved_row",
                                 f"TASK-137.S-6 anchor 값 불일치 — {item!r}")

            self.assertEqual(
                [item["row_id"] for item in missing], [1, 2],
                f"TASK-137.S-6 앵커 ① 항목이 row_id 오름차순 2건이 아님(§2.5 정렬) — {missing!r}")
            self.assertEqual(
                [item["row_key"] for item in missing], ["execute.impl_a", "execute.impl_b"],
                f"TASK-137.S-6 row_key가 행 주소와 불일치 — {missing!r}")
            self.assertEqual(
                [item["stage"] for item in missing], ["EXECUTE", "EXECUTE"],
                f"TASK-137.S-6 stage가 행 stage와 불일치 — {missing!r}")


class TestCompletenessMissingPmActivityClearedByLoggedDecision(unittest.TestCase):
    """TASK-137.S-7 (AC-3, C-2, H-2) — GREEN: W-5. **구현 전 RED**.

    "기록하면 신호가 해소된다"는 미충족 방향이다. 현 구현은 `missing_pm_activity`를
    항상 비워 두므로 아래 `test_all_rows_logged_clears_missing_pm_activity`는
    **우연히 통과한다** — 그래서 같은 fixture에서 한 행만 기록한 대조군을 함께 두어
    "기록한 경우에만 빈다"를 실제로 구분한다. 대조군은 현재 실패한다(미구현 RED).
    """

    @staticmethod
    def _log_decision(task, row_key):
        return _run([
            "log-event", str(task),
            "--event", "activity", "--kind", "decision",
            "--summary", f"PM이 {row_key} 자동 승인을 판단함",
            "--task-step", row_key,
        ])

    def test_partial_logging_leaves_only_the_unlogged_row(self):
        """대조군 — 두 자동 승인 행 중 1행만 기록하면 나머지 1행만 남아야 한다.
        빈 배열이면 "기록 때문에 빈 것"과 "원래 항상 비는 것"을 구분할 수 없다."""
        with tempfile.TemporaryDirectory() as tmp:
            task = _make_auto_approved_fixture(tmp, "137-s7-partial")

            code, out, err, _ = self._log_decision(task, "execute.impl_a")
            self.assertEqual(code, 0, f"TASK-137.S-7 log-event 실패 — {out!r} {err!r}")

            code, out, err, data, unchanged = _completeness(task)
            self.assertEqual(code, 0, f"TASK-137.S-7 진단이 exit 0이 아님 — {out!r} {err!r}")
            self.assertTrue(unchanged, "TASK-137.S-7 read-only 진단이 state.json 바이트를 변경함(C-3)")

            missing = data.get("missing_pm_activity")
            self.assertEqual(
                [item.get("row_key") for item in (missing or [])], ["execute.impl_b"],
                f"TASK-137.S-7 기록하지 않은 행 1건만 남아야 하는데 다름(미구현 RED) — {data!r}")

    def test_all_rows_logged_clears_missing_pm_activity(self):
        """S-7 본 시나리오 — 모든 자동 승인 행에 대응 PM activity(decision)를 기록하면
        빈 배열이어야 한다. (현 구현에서는 항상 빈 배열이라 우연히 통과한다.)"""
        with tempfile.TemporaryDirectory() as tmp:
            task = _make_auto_approved_fixture(tmp, "137-s7-full")

            for row_key in ("execute.impl_a", "execute.impl_b"):
                code, out, err, _ = self._log_decision(task, row_key)
                self.assertEqual(code, 0, f"TASK-137.S-7 log-event 실패({row_key}) — {out!r} {err!r}")

            code, out, err, data, unchanged = _completeness(task)
            self.assertEqual(code, 0, f"TASK-137.S-7 진단이 exit 0이 아님 — {out!r} {err!r}")
            self.assertTrue(unchanged, "TASK-137.S-7 read-only 진단이 state.json 바이트를 변경함(C-3)")
            self.assertEqual(
                data.get("missing_pm_activity"), [],
                f"TASK-137.S-7 대응 사건을 모두 기록했는데 신호가 해소되지 않음 — {data!r}")


class TestCompletenessMissingPmActivityOverrideAnchor(unittest.TestCase):
    """TASK-137.S-8 (AC-3, C-2) — GREEN: W-5. **구현 전 RED**.

    CONTRACT §2.5 앵커 ②: `run_log.status == "overridden"`인데 run 전역에
    `event=="activity"` ∧ `actor.kind=="PM"` ∧ `data.kind=="decision"` 사건이
    하나도 없으면 1건을 싣는다(주소 대조 없음). 항목은 같은 5키이되
    `row_id`·`row_key`·`stage`가 `null`이고 `anchor == "override_bundle"`이며,
    §2.5 정렬에 따라 **배열 마지막**에 붙는다.

    `--run-log-override` CLI 표면은 이 범위(T10)가 아니므로 `run_log.status`는
    state.json fixture 주입으로 만든다(기존 TestOutboxLimits의 주입 관례 재사용).

    현재 관찰: S-6과 같은 원인(누락 ④ 미집행)으로 빈 배열이 반환된다(미구현 RED).
    """

    @staticmethod
    def _mark_overridden(task):
        state = _read_state(task)
        state["run_log"]["status"] = "overridden"
        _write_state(task, state)

    def test_overridden_run_without_pm_decision_yields_single_override_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = _write_keyed_pipeline(tmp)
            task = _mktask(tmp, name="137-s8-override-only")
            code, out, err, _ = _init_keyed(task, spec_path)
            self.assertEqual(code, 0, f"TASK-137.S-8 init 실패 — {out!r} {err!r}")
            self._mark_overridden(task)

            code, out, err, data, unchanged = _completeness(task)
            self.assertEqual(code, 0, f"TASK-137.S-8 진단이 exit 0이 아님 — {out!r} {err!r}")
            self.assertTrue(unchanged, "TASK-137.S-8 read-only 진단이 state.json 바이트를 변경함(C-3)")

            missing = data.get("missing_pm_activity") or []
            override_items = [i for i in missing if i.get("anchor") == "override_bundle"]
            self.assertEqual(
                len(override_items), 1,
                f"TASK-137.S-8 override 앵커 항목이 정확히 1건이 아님(미구현 RED) — {data!r}")

            item = override_items[0]
            self.assertEqual(set(item.keys()), _ANCHOR_ITEM_KEYS,
                             f"TASK-137.S-8 항목 키 집합이 §2.5 5키와 다름 — {item!r}")
            self.assertIsNone(item["row_id"], f"TASK-137.S-8 row_id가 null이 아님 — {item!r}")
            self.assertIsNone(item["row_key"], f"TASK-137.S-8 row_key가 null이 아님 — {item!r}")
            self.assertIsNone(item["stage"], f"TASK-137.S-8 stage가 null이 아님 — {item!r}")
            self.assertEqual(item["expected"], "activity(decision)",
                             f"TASK-137.S-8 expected 값 불일치 — {item!r}")

    def test_override_item_is_last_when_anchor_one_items_exist(self):
        """§2.5 정렬 — 앵커 ① 항목을 row_id 오름차순으로 먼저 싣고 앵커 ②는 마지막 1건."""
        with tempfile.TemporaryDirectory() as tmp:
            task = _make_auto_approved_fixture(tmp, "137-s8-override-with-rows")
            self._mark_overridden(task)

            code, out, err, data, unchanged = _completeness(task)
            self.assertEqual(code, 0, f"TASK-137.S-8 진단이 exit 0이 아님 — {out!r} {err!r}")
            self.assertTrue(unchanged, "TASK-137.S-8 read-only 진단이 state.json 바이트를 변경함(C-3)")

            missing = data.get("missing_pm_activity") or []
            self.assertEqual(
                [i.get("anchor") for i in missing],
                ["auto_approved_row", "auto_approved_row", "override_bundle"],
                f"TASK-137.S-8 앵커 ① 2건 뒤 앵커 ② 1건 순서가 아님(§2.5 정렬, 미구현 RED) — {data!r}")
            self.assertEqual(
                [i.get("row_id") for i in missing[:-1]], [1, 2],
                f"TASK-137.S-8 앵커 ① 항목이 row_id 오름차순이 아님 — {missing!r}")


# `--run-log-mode off` 경로(= run_log 블록 없음)의 advance/mark 응답 키 집합 기준선.
# C-6이 "종전과 동일"을 요구하는 대상이며, 개정 전 동작을 `git show HEAD:`로 대리하면
# 기준 커밋이 개정본이 되는 순간 가드가 자기무효화되므로(이 파일의 기존 실패 4건)
# 기준선을 **명시 리터럴로 고정**한다. W-5가 이 키 집합을 바꾸면 여기서 잡힌다.
_OFF_MODE_ADVANCE_KEYS_KEYLESS = {
    "ok", "command", "row_id", "stage", "item", "status", "timestamp",
    "auto_approved", "todo_mirror",
}
_OFF_MODE_MARK_KEYS_KEYLESS = _OFF_MODE_ADVANCE_KEYS_KEYLESS | {"owner"}
_OFF_MODE_ADVANCE_KEYS_KEYED = _OFF_MODE_ADVANCE_KEYS_KEYLESS | {
    "next_action", "report_type", "transition_action",
}
_OFF_MODE_MARK_KEYS_KEYED = _OFF_MODE_ADVANCE_KEYS_KEYED | {"owner"}


class TestSchema10And11WithoutRunLogBlockUnchanged(unittest.TestCase):
    """TASK-137.S-9 (C-6) — 보존·회귀 가드. 현 구현에서도 통과해야 한다.

    (a) `run_log` 블록이 없는 태스크는 완전성 검사 전체의 대상이 아니다
        (CONTRACT §2.5 범위 한정 (b)) — 누락 목록 4종이 모두 비고 관측 3필드가
        전부 `null`이며 exit 0이다.
    (b) `advance`·`mark` 각 1회의 응답 키 집합과 `state.json` 산출물이 종전과
        동일하다 — 응답 키는 명시 기준선 리터럴과, state.json은 호출 전 자기
        자신의 최상위 키 집합·schema_version과 대조하고 run 디렉터리·run_log
        키가 생기지 않음을 확인한다.
    """

    def _assert_completeness_is_empty(self, task, label):
        code, out, err, data, unchanged = _completeness(task)
        self.assertEqual(code, 0, f"TASK-137.S-9 {label} 진단이 exit 0이 아님 — {out!r} {err!r}")
        self.assertTrue(unchanged, f"TASK-137.S-9 {label} 진단이 state.json 바이트를 변경함(C-3)")
        for field in ("missing_state_changed", "missing_pm_activity",
                      "missing_gate_event", "unobserved_worker_boundary"):
            self.assertEqual(data.get(field), [],
                             f"TASK-137.S-9 {label} {field}가 비어 있지 않음(§2.5 범위 한정 (b)) — {data!r}")
        for field in ("last_observed_decision", "last_observed_state_change",
                      "last_observed_boundary"):
            self.assertIn(field, data, f"TASK-137.S-9 {label} {field} 필드 부재 — {data!r}")
            self.assertIsNone(data.get(field),
                              f"TASK-137.S-9 {label} {field}가 null이 아님 — {data!r}")

    def _assert_transition_path_unchanged(self, task, label, row_args,
                                          advance_keys, mark_keys, schema_version):
        # [H-6] 앰비언트 세션 식별자를 제거한 env로 전이를 호출한다 — 변수가 있으면
        # `advance`/`mark`가 lease를 claim해 `run/.runtime/`이 생기고 아래
        # "run 디렉터리 미생성" 단언이 실행 위치에 따라 뒤집힌다(프로덕션 코드는
        # 바꾸지 않는다 — 이 가드의 검증 축은 run-log 경로의 산출물 불변이다).
        clean_env = _env_without_session_ids()
        state_before = _read_state(task)
        self.assertNotIn("run_log", state_before,
                         f"TASK-137.S-9 {label} off 경로인데 run_log 블록이 생성됨 — {state_before.keys()!r}")
        top_keys_before = set(state_before.keys())

        code, out, err, data = _run(["advance", str(task)] + row_args, env=clean_env)
        self.assertEqual(code, 0, f"TASK-137.S-9 {label} advance 실패 — {out!r} {err!r}")
        self.assertEqual(set(data.keys()), advance_keys,
                         f"TASK-137.S-9 {label} advance 응답 키 집합이 기준선과 다름(C-6) — {sorted(data.keys())!r}")

        code, out, err, data = _run(["mark", str(task)] + row_args + ["--done"],
                                    env=clean_env)
        self.assertEqual(code, 0, f"TASK-137.S-9 {label} mark 실패 — {out!r} {err!r}")
        self.assertEqual(set(data.keys()), mark_keys,
                         f"TASK-137.S-9 {label} mark 응답 키 집합이 기준선과 다름(C-6) — {sorted(data.keys())!r}")

        state_after = _read_state(task)
        self.assertEqual(set(state_after.keys()), top_keys_before,
                         f"TASK-137.S-9 {label} state.json 최상위 키 집합이 달라짐(C-6) — "
                         f"{sorted(set(state_after.keys()) ^ top_keys_before)!r}")
        self.assertNotIn("run_log", state_after,
                         f"TASK-137.S-9 {label} 전이 후 run_log 블록이 생김(C-6)")
        self.assertEqual(state_after.get("schema_version"), schema_version,
                         f"TASK-137.S-9 {label} schema_version이 승격·강등됨 — {state_after.get('schema_version')!r}")
        self.assertFalse((pathlib.Path(task) / "run").exists(),
                         f"TASK-137.S-9 {label} run_log 없는 태스크에 run 디렉터리가 생성됨")
        self.assertEqual(_segment_records(task), [],
                         f"TASK-137.S-9 {label} run_log 없는 태스크에 조각 사건이 기록됨")

    def test_schema_1_0_task_without_run_log_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="137-s9-schema-1-0")
            code, out, err, _ = _run([
                "init", str(task), "--skill", "oppl", "--mode", "agentic",
                "--rows-spec", _ROWS_SPEC_KEYLESS, "--run-log-mode", "off",
            ])
            self.assertEqual(code, 0, f"TASK-137.S-9 1.0 init 실패 — {out!r} {err!r}")
            self.assertEqual(_read_state(task).get("schema_version"), "1.0")

            self._assert_completeness_is_empty(task, "1.0")
            self._assert_transition_path_unchanged(
                task, "1.0", ["--row", "1"],
                _OFF_MODE_ADVANCE_KEYS_KEYLESS, _OFF_MODE_MARK_KEYS_KEYLESS, "1.0")

    def test_schema_1_1_task_without_run_log_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = _write_keyed_pipeline(tmp)
            task = _mktask(tmp, name="137-s9-schema-1-1")
            code, out, err, _ = _init_keyed(task, spec_path, run_log_mode="off")
            self.assertEqual(code, 0, f"TASK-137.S-9 1.1 init 실패 — {out!r} {err!r}")
            self.assertEqual(_read_state(task).get("schema_version"), "1.1")

            self._assert_completeness_is_empty(task, "1.1")
            self._assert_transition_path_unchanged(
                task, "1.1", ["--task-step", "execute.impl_a"],
                _OFF_MODE_ADVANCE_KEYS_KEYED, _OFF_MODE_MARK_KEYS_KEYED, "1.1")


class TestCompletenessCheckIndependentFromStructuralValidation(unittest.TestCase):
    """TASK-135.S-9 (AC-8, C-4, C-5, H-3) — GREEN: W-4.

    순번·스키마·provenance는 유효하지만 자동 승인 `state.changed` 1건을 뺀
    JSONL에 대해 `run-log-tool validate-run`은 구조만 보므로 통과하고,
    `state-tool verify --run-log-completeness-check`는 빠진 row/event를
    정확히 누락으로 보고해야 한다. run-log-core는 state.json을 읽지 않는
    의존 방향을 유지해야 한다(TRD D-5).

    현재 관찰: --run-log-completeness-check 플래그 부재로 후자 조회가
    불가능하다(미구현 RED). validate-run 구조 통과와 run_log_core의 state.json
    비의존은 기존 자산으로 이미 성립하므로 회귀 가드로 함께 판정한다.
    """

    def test_validate_run_passes_but_completeness_check_flags_missing_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="135-completeness-vs-structural")
            self.assertEqual(_run([
                "init", str(task), "--skill", "oppl", "--mode", "agentic",
                "--rows-spec", _ROWS_SPEC_USER_CONFIRM_X2, "--run-log-mode", "shadow",
            ])[0], 0)

            code, out, err, data = _run(["advance", str(task), "--row", "3"])
            self.assertEqual(code, 0, f"TASK-135.S-9 advance 실패 — {out!r} {err!r}")

            state = _read_state(task)
            run_id = state["run_log"]["active_run_id"]

            # run-log-tool.validate-run은 구조(순번·스키마·provenance)만 보므로
            # 통과해야 한다(자동승인 state.changed 누락 여부와 무관).
            rl_run_sh = _STATE_TOOL_DIR.parent / "run-log-tool" / "run.sh"
            if rl_run_sh.exists():
                result = subprocess.run(
                    ["bash", str(rl_run_sh), "validate-run",
                     "--task", str(task), "--run-id", run_id, "--format", "json"],
                    capture_output=True, text=True)
                self.assertEqual(
                    result.returncode, 0,
                    f"TASK-135.S-9 validate-run이 구조 유효 로그를 거부함 — "
                    f"stdout={result.stdout!r} stderr={result.stderr!r}")

            # run-log-core는 state.json을 읽지 않는다(정적 의존 방향 검사).
            core_src = _STATE_TOOL_DIR.parent / "run-log-tool" / "run_log_core.py"
            if core_src.exists():
                core_text = core_src.read_text(encoding="utf-8")
                self.assertNotIn("state.json", core_text,
                                 "TASK-135.S-9 run_log_core.py가 state.json을 직접 참조함(TRD D-5 위반)")

            code, out, err, data = _run([
                "verify", str(task), "--run-log-completeness-check",
            ])
            self.assertEqual(
                code, 0,
                f"TASK-135.S-9 --run-log-completeness-check 미구현으로 실패(RED) — "
                f"exit={code} stdout={out!r} stderr={err!r}")
            self.assertTrue(
                data.get("missing_state_changed"),
                f"TASK-135.S-9 자동승인 state.changed 누락이 보고되지 않음 — {data!r}")


class TestModeInventoryEquality(unittest.TestCase):
    """TASK-135.S-1 (AC-1, C-1, C-2, C-4) — GREEN: W-2/W-3/W-4 종합.

    동일한 실행·상태·PM·worker·gate 입력을 갖는 shadow와 검증용 active run이
    관측 가능한 event 종류·payload 의미에서 동일해야 하며 차이는 provenance
    신뢰도와 completion enforcement에만 있어야 한다(CONTRACT §1.2).

    현재 관찰: active 3종 분기가 구현되지 않아(state_tool.py:1990 부근 무조건
    profile_not_found) active run 자체를 만들 수 없다 — mode 동등성 비교 이전
    단계에서 막힌다(미구현 RED).
    """

    def test_shadow_and_active_produce_same_event_kind_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            shadow_task = _mktask(tmp, name="135-mode-shadow")
            self.assertEqual(_init_shadow(shadow_task)[0], 0)
            self.assertEqual(_run(["advance", str(shadow_task), "--row", "1"])[0], 0)
            self.assertEqual(_run(["mark", str(shadow_task), "--row", "1", "--done"])[0], 0)
            shadow_kinds = {r["event"] for r in _segment_records(shadow_task)}

            active_task = _mktask(tmp, name="135-mode-active")
            active_task.mkdir(exist_ok=True)
            profiles_path = pathlib.Path(tmp) / "profiles-s1.json"
            profiles_path.write_text(json.dumps({
                "schema_version": "1.0",
                "produced_by": "135-fixture",
                "channels": [{
                    "channel_id": "pm-agent-tool",
                    "completion_profile": "observed_trajectory",
                    "adapter_id": "agent-tool-adapter",
                    "adapter_sha256": "0" * 64,
                    "receipt_sha256": "0" * 64,
                    "evidence_paths": ["evidence/pm-agent-tool/start.json"],
                }],
            }, ensure_ascii=False), encoding="utf-8")

            code, out, err, data = _run([
                "init", str(active_task), "--skill", "oppl", "--mode", "agentic",
                "--rows-spec", _ROWS_SPEC,
                "--run-log-mode", "active", "--channel-id", "pm-agent-tool",
                "--profiles", str(profiles_path),
            ])
            self.assertEqual(
                code, 0,
                f"TASK-135.S-1 active init이 실패해 동등성 비교 자체가 불가함(RED) — "
                f"exit={code} stdout={out!r} stderr={err!r}")

            self.assertEqual(_run(["advance", str(active_task), "--row", "1"])[0], 0)
            active_kinds = {r["event"] for r in _segment_records(active_task)}

            self.assertEqual(
                shadow_kinds, active_kinds,
                f"TASK-135.S-1 shadow/active 관측 가능 event 종류 불일치 — "
                f"shadow={shadow_kinds!r} active={active_kinds!r}")


# ═════════════════════════════════════════════════════════════════════════════
# TASK-147 — PM 보고 표면·`last_report` 포인터·`stop.decision` drain·정지 판정 축
#
#   TASK-147.S-5  (AC-2, AC-7, C-2, C-5, H-2) → GREEN: W-5  [구현 전 RED]
#   TASK-147.S-6  (AC-2, C-2)                 → GREEN: W-5  [구현 전 RED]
#   TASK-147.S-7  (AC-3, AC-7, C-3, H-4)      → GREEN: W-7  [구현 전 RED]
#   TASK-147.S-9  (AC-5, C-1)                 → GREEN: W-9  [구현 전 RED]
#   TASK-147.S-10 (AC-1, C-1)                 → GREEN: W-9  [구현 전 RED]
#
# 기대값의 유일한 원천은 개정된 `docs/run-log/CONTRACT.md`다 —
#   §1.2 사건 14종(`pm.report` A4·3키 / `stop.decision` A7·6키)
#   §1.4 『`last_report` 포인터 계약』(5키 폐쇄·같은 원자 쓰기·admission 거부 시 미갱신)
#   §2.4 `state-tool.log-event` 불변식(수용 `--event`는 `activity`·`pm.report` 2종)
#   §2.5 『정지 판정 목록 5종』과 MV-34
# 그리고 PLAN.md D-2·D-3·D-7·D-14, W-5·W-7·W-9.
#
# 판정 경계(harness/red-first.md §2): `run.sh` subprocess 실호출의 exit code·
# §2.1 응답 봉투와 디스크 산출물(`state.json` 바이트, 조각 JSONL, stop-guard
# receipt 파일)만 본다. `state_tool.py`의 내부 함수를 직접 import하지 않으며
# mock/patch/MagicMock을 쓰지 않는다.
# ═════════════════════════════════════════════════════════════════════════════

_T147_RUN_LOG_RUN_SH = _STATE_TOOL_DIR.parent / "run-log-tool" / "run.sh"


def _run_run_log_tool(args, cwd=None):
    """`run-log-tool run.sh`를 subprocess로 실호출한다(기록 코어 집행 지점 대조용).

    `run_log_core`를 import하지 않고 CLI 표면만 쓴다 — state-tool 테스트가 기록
    도구 내부에 결합되지 않게 한다(§3.1 단방향 의존)."""
    cmd = ["bash", str(_T147_RUN_LOG_RUN_SH)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


# CONTRACT §1.4 — `last_report` 포인터의 폐쇄 5키.
_T147_LAST_REPORT_KEYS = {
    "event_id", "report_type", "transition_action", "user_input_required", "at"}

# CONTRACT §1.3 — `stop.decision` data의 폐쇄 6키.
_T147_STOP_DECISION_DATA_KEYS = {
    "decision_kind", "diagnostics", "block_count", "claim_source",
    "report_event_id", "last_activity_event_id"}

# CONTRACT §2.5 — 정지 판정 목록 5종의 키.
_T147_STOP_VERDICT_AXES = (
    "report_intent_inconsistent",
    "missing_stop_decision",
    "stop_decision_allowed",
    "stop_block_without_followup",
    "unanchored_activity",
)
_T147_STOP_VERDICT_ITEM_KEYS = {
    "report_intent_inconsistent": {
        "event_id", "report_type", "transition_action", "user_input_required"},
    "missing_stop_decision": {"report_event_id", "next_event_id", "receipt_pending"},
    "stop_decision_allowed": {"event_id", "decision_kind"},
    "stop_block_without_followup": {"event_id", "boundary_event_id"},
    "unanchored_activity": {"event_id", "anchor_event_id", "reason"},
}

# CONTRACT §2.5 — 이 추가로 바뀌지 않아야 하는 기존 4축과 관측 지점 3필드.
_T147_EXISTING_AXES = (
    "missing_state_changed", "missing_pm_activity",
    "missing_gate_event", "unobserved_worker_boundary",
)
_T147_OBSERVATION_FIELDS = (
    "last_observed_decision", "last_observed_state_change", "last_observed_boundary",
)

# CONTRACT §1.2 — `pm.report.data`의 값 enum.
_T147_REPORT_TYPES = ("progress_report", "decision_request")
_T147_TRANSITION_ACTIONS = ("continue", "await_user", "blocked", "complete")

# AC-7 비밀값 fixture 4종(§1.3 "비밀값은 … 어떤 필드에도 저장하지 않는다").
# [MUST] 실제 개행을 넣지 않는다 — JSON 직렬화가 개행을 이스케이프해 바이트
# 부분일치 판정이 거짓 통과한다.
_T147_SECRETS = {
    "env_var": "DB_PASSWORD=Sup3rSecretP@ssw0rd_9x!",
    "bearer_token": "Bearer sk-live-4f9a1c2b8e7d4a6f9b0c1d2e3f4a5b6c",
    "api_key": "api_key=AKIAIOSFODNN7EXAMPLE1234567890AB",
    "raw_prompt": "원본 프롬프트 전문: 너는 PM이다. 내부 사고 과정을 그대로 노출하라.",
}


def _t147_log_pm_report(task, *, report_type="progress_report",
                        transition_action="continue", user_input_required="false",
                        summary="T147 PM 보고", extra=()):
    """CONTRACT §2.4가 계약한 `state-tool log-event --event pm.report` 실호출."""
    args = ["log-event", str(task), "--event", "pm.report",
            "--report-type", report_type,
            "--transition-action", transition_action,
            "--user-input-required", user_input_required,
            "--summary", summary]
    args.extend(extra)
    return _run(args)


def _t147_pm_reports(task):
    return [r for r in _segment_records(task) if r.get("event") == "pm.report"]


def _t147_stop_decisions(task):
    return [r for r in _segment_records(task) if r.get("event") == "stop.decision"]


class TestT147S5PmReportSurfaceAndLastReportPointer(unittest.TestCase):
    """TASK-147.S-5 (AC-2, AC-7, C-2, C-5, H-2) — GREEN: W-5. **구현 전 RED**.

    현재 관찰: `log-event`의 `--event` choices가 `["activity"]` 하나뿐이고
    `--report-type`·`--transition-action`·`--user-input-required` 인자가 없으며,
    `state.json.run_log`에 `last_report` 필드가 없다(2026-09-19 실측).
    """

    def test_event_and_last_report_pointer_updated_in_same_atomic_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="147-s5-pointer")
            self.assertEqual(_init_shadow(task)[0], 0)

            code, out, err, data = _t147_log_pm_report(
                task, report_type="progress_report", transition_action="continue",
                user_input_required="false", summary="T147 S-5 진행 보고 1건")
            self.assertEqual(
                code, 0,
                f"TASK-147.S-5 log-event --event pm.report 실패(미구현 RED) — "
                f"exit={code} stdout={out!r} stderr={err!r}")

            reports = _t147_pm_reports(task)
            self.assertEqual(len(reports), 1,
                             f"TASK-147.S-5 조각의 pm.report가 1건이 아님 — {reports!r}")
            event = reports[0]
            self.assertEqual(
                event.get("data"),
                {"report_type": "progress_report", "transition_action": "continue",
                 "user_input_required": False},
                f"TASK-147.S-5 기록된 data가 §1.2 폐쇄 3키와 다름 — {event.get('data')!r}")
            self.assertEqual(
                event.get("summary"),
                "pm.report: report_type=progress_report; transition_action=continue; "
                "user_input_required=false",
                "TASK-147.S-5 pm.report summary가 D-16 renderer 템플릿과 다름")
            for field in ("reason", "reason_code", "duration_unknown_reason", "refs"):
                self.assertIsNone(
                    event.get(field),
                    f"TASK-147.S-5 pm.report {field}가 D-16 null 폐쇄를 어김")

            block = _read_state(task).get("run_log") or {}
            pointer = block.get("last_report")
            self.assertIsInstance(
                pointer, dict,
                f"TASK-147.S-5 state.json run_log.last_report가 없음(§1.4) — {block!r}")
            self.assertEqual(
                set(pointer.keys()), _T147_LAST_REPORT_KEYS,
                f"TASK-147.S-5 last_report 키가 5키 폐쇄와 다름(§1.4) — {sorted(pointer)}")
            self.assertEqual(pointer["event_id"], event["event_id"],
                             "TASK-147.S-5 포인터가 방금 기록한 사건을 가리키지 않음")
            self.assertEqual(pointer["report_type"], "progress_report")
            self.assertEqual(pointer["transition_action"], "continue")
            self.assertIs(pointer["user_input_required"], False)

    def test_rejected_admission_updates_neither_event_nor_pointer(self):
        """H-2 — admission이 거부되면 사건도 포인터도 갱신되지 않는다(§1.4 (b))."""
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="147-s5-rejected")
            self.assertEqual(_init_shadow(task)[0], 0)
            before_state = (task / "state.json").read_bytes()
            before_events = len(_segment_records(task))

            code, out, err, data = _t147_log_pm_report(
                task, extra=("--stage", "x" * 5000))  # 항목당 UTF-8 4 KiB 상한 초과(§1.4)
            self.assertNotEqual(
                code, 0,
                f"TASK-147.S-5 4 KiB 초과 보고가 수용됨 — stdout={out!r}")
            # [MUST] 거부 사유를 admission 한도로 좁힌다. `--report-type` 인자
            # 자체가 없어 argparse가 내는 사용법 오류로 통과하면 이 가드는
            # 아무것도 지키지 않는다(거짓 통과).
            error_code = (data.get("error", {}).get("code")
                          if isinstance(data.get("error"), dict) else data.get("error"))
            self.assertEqual(
                error_code, "event_too_large",
                f"TASK-147.S-5 거부 사유가 §1.4 항목 4 KiB 상한(event_too_large)이 "
                f"아님 — exit={code} stdout={out!r} stderr={err!r}")
            self.assertEqual(
                (task / "state.json").read_bytes(), before_state,
                "TASK-147.S-5 거부됐는데 state.json이 변경됨(포인터 누수)")
            self.assertEqual(
                len(_segment_records(task)), before_events,
                "TASK-147.S-5 거부됐는데 조각에 사건이 추가됨")
            self.assertIsNone(
                (_read_state(task).get("run_log") or {}).get("last_report"),
                "TASK-147.S-5 거부됐는데 last_report 포인터가 갱신됨")

    def test_secret_in_summary_absent_from_segment_pending_and_pointer(self):
        """AC-7 — 조각·`pending_events`·`last_report` 어디에도 평문 0건."""
        for kind, secret in _T147_SECRETS.items():
            with self.subTest(kind=kind):
                with tempfile.TemporaryDirectory() as tmp:
                    task = _mktask(tmp, name=f"147-s5-secret-{kind}")
                    self.assertEqual(_init_shadow(task)[0], 0)

                    code, out, err, data = _t147_log_pm_report(
                        task, summary=f"T147 S-5 {kind} 투입: {secret}")
                    self.assertEqual(
                        code, 0,
                        f"TASK-147.S-5 {kind} log-event 실패(미구현 RED) — {out!r} {err!r}")

                    state = _read_state(task)
                    block = state.get("run_log") or {}
                    pending_text = json.dumps(block.get("pending_events") or [],
                                              ensure_ascii=False)
                    pointer_text = json.dumps(block.get("last_report"), ensure_ascii=False)
                    segment_text = "".join(
                        seg.read_text(encoding="utf-8")
                        for seg in sorted((task / "run").glob("run-log-*.jsonl")))

                    self.assertNotIn(secret, segment_text,
                                     f"TASK-147.S-5 {kind}: 조각 파일에 평문이 남음")
                    self.assertNotIn(secret, pending_text,
                                     f"TASK-147.S-5 {kind}: pending_events에 평문이 남음")
                    self.assertNotIn(secret, pointer_text,
                                     f"TASK-147.S-5 {kind}: last_report 포인터에 평문이 남음")

    def test_reason_and_refs_are_rejected_before_any_write(self):
        """D-16 — pm.report의 닫힌 서술 축을 여는 CLI 인자는 schema_invalid다."""
        for option, value in (
            ("--reason", _T147_SECRETS["raw_prompt"]),
            ("--refs", "evidence/raw-prompt.txt"),
        ):
            with self.subTest(option=option):
                with tempfile.TemporaryDirectory() as tmp:
                    task = _mktask(tmp, name=f"147-s5-reject-{option[2:]}")
                    self.assertEqual(_init_shadow(task)[0], 0)
                    before_state = (task / "state.json").read_bytes()
                    before_segments = [p.read_bytes() for p in sorted(
                        (task / "run").glob("run-log-*.jsonl"))]

                    code, out, err, data = _t147_log_pm_report(
                        task, extra=(option, value))
                    self.assertNotEqual(code, 0,
                                        f"TASK-147.S-5 {option}가 수용됨 — {out!r}")
                    error_code = (data.get("error", {}).get("code")
                                  if isinstance(data.get("error"), dict)
                                  else data.get("error"))
                    self.assertEqual(error_code, "schema_invalid",
                                     f"TASK-147.S-5 {option} 거부 코드가 schema_invalid가 아님 — {out!r} {err!r}")
                    self.assertEqual((task / "state.json").read_bytes(), before_state,
                                     f"TASK-147.S-5 {option} 거부가 state.json을 변경함")
                    self.assertEqual(
                        [p.read_bytes() for p in sorted((task / "run").glob("run-log-*.jsonl"))],
                        before_segments,
                        f"TASK-147.S-5 {option} 거부가 조각 바이트를 변경함")


class TestT147S6PmReportAxisEnumsAndDualValidation(unittest.TestCase):
    """TASK-147.S-6 (AC-2, C-2) — GREEN: W-5. **구현 전 RED**.

    3축의 유효 조합 전수(2 × 4 × 2 = 16)가 각각 식별 가능한 값으로 기록·조회되고,
    enum 밖 값은 앞단 `_build_pm_report_data()`(= `state-tool log-event`)와 기록
    코어(= `run-log-tool append`)가 **같은** `schema_invalid`를 낸다(§1.3 중복 방어
    "두 지점의 판정 결과는 항상 일치한다").
    """

    def test_all_valid_axis_combinations_recorded_distinctly(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="147-s6-enums")
            self.assertEqual(_init_shadow(task)[0], 0)

            expected = []
            for report_type in _T147_REPORT_TYPES:
                for transition_action in _T147_TRANSITION_ACTIONS:
                    for flag, value in (("true", True), ("false", False)):
                        code, out, err, _ = _t147_log_pm_report(
                            task, report_type=report_type,
                            transition_action=transition_action,
                            user_input_required=flag,
                            summary=f"T147 S-6 {report_type}/{transition_action}/{flag}")
                        self.assertEqual(
                            code, 0,
                            f"TASK-147.S-6 유효 조합 {report_type}/{transition_action}/"
                            f"{flag} 거부됨(미구현 RED) — {out!r} {err!r}")
                        expected.append({
                            "report_type": report_type,
                            "transition_action": transition_action,
                            "user_input_required": value,
                        })

            recorded = [r.get("data") for r in _t147_pm_reports(task)]
            self.assertEqual(
                recorded, expected,
                f"TASK-147.S-6 기록된 3축 값이 입력과 다름 — {recorded!r}")

    def test_enum_violation_gets_same_schema_invalid_at_both_enforcement_points(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="147-s6-enum-violation")
            self.assertEqual(_init_shadow(task)[0], 0)
            run_id = ((_read_state(task).get("run_log") or {}).get("active_run_id"))
            self.assertTrue(run_id, "TASK-147.S-6 active_run_id 부재")

            bad_payloads = [
                {"report_type": "final_report", "transition_action": "continue",
                 "user_input_required": False},
                {"report_type": "progress_report", "transition_action": "retry",
                 "user_input_required": False},
                {"report_type": "progress_report", "transition_action": "continue",
                 "user_input_required": "false"},
                {"report_type": "progress_report", "transition_action": "continue",
                 "user_input_required": False, "raw_prompt": "내부 사고 과정 원문"},
            ]

            for i, payload in enumerate(bad_payloads):
                with self.subTest(payload=payload):
                    before_state = (task / "state.json").read_bytes()
                    before_events = len(_segment_records(task))

                    # ① 앞단 중복 방어 — state-tool log-event
                    code_f, out_f, err_f, data_f = _run([
                        "log-event", str(task), "--event", "pm.report",
                        "--summary", f"T147 S-6 위반 {i}",
                        "--data", json.dumps(payload, ensure_ascii=False)])
                    self.assertNotEqual(
                        code_f, 0,
                        f"TASK-147.S-6 앞단이 enum 밖 payload를 수용함 — {out_f!r}")
                    front_code = (data_f.get("error", {}).get("code")
                                  if isinstance(data_f.get("error"), dict)
                                  else data_f.get("error"))
                    self.assertEqual(
                        front_code, "schema_invalid",
                        f"TASK-147.S-6 앞단 오류 코드가 schema_invalid가 아님 — {out_f!r} {err_f!r}")

                    # ② 집행 지점 — 기록 코어(run-log-tool append)
                    code_c, out_c, err_c, data_c = _run_run_log_tool([
                        "append", "--task", str(task), "--run-id", run_id,
                        "--request-id", f"req_t147_s6_{i}", "--event", "pm.report",
                        "--actor-kind", "PM", "--actor-id", "PM",
                        "--provenance-type", "direct", "--recorded-by-kind", "PM",
                        "--summary", f"T147 S-6 위반 {i}",
                        "--data", json.dumps(payload, ensure_ascii=False),
                        "--format", "json"])
                    self.assertNotEqual(
                        code_c, 0,
                        f"TASK-147.S-6 기록 코어가 enum 밖 payload를 수용함 — {out_c!r}")
                    self.assertEqual(
                        data_c.get("error", {}).get("code"), "schema_invalid",
                        f"TASK-147.S-6 코어 오류 코드가 schema_invalid가 아님 — {out_c!r}")

                    self.assertEqual(
                        (task / "state.json").read_bytes(), before_state,
                        "TASK-147.S-6 거부됐는데 state.json이 변경됨")
                    self.assertEqual(
                        len(_segment_records(task)), before_events,
                        "TASK-147.S-6 거부됐는데 조각에 사건이 추가됨")


# ─────────────────────────────────────────────────────────────────────────────
# TASK-147.S-7 / S-9 / S-10 공통 — 프로젝트 루트 캡슐과 조각 사건 fixture
# ─────────────────────────────────────────────────────────────────────────────

def _t147_project_capsule(tmp, name):
    """`<tmp>/proj/tasks/<name>` 캡슐을 `state-tool init --run-log-mode shadow`로
    실제로 만들고 (project_root, task_path)를 돌려준다.

    stop-guard receipt는 `<project_root>/.opal/run/.runtime/stop-guard/`에 있으므로
    (ownership_core.stop_receipt_path) 캡슐을 프로젝트 루트 아래 `tasks/`에 둔다 —
    실물 배치와 같은 형태여야 drain 경로가 receipt를 찾을 수 있다."""
    project_root = pathlib.Path(tmp) / "proj"
    task = project_root / "tasks" / name
    task.mkdir(parents=True)
    code, out, err, _ = _init_shadow(task)
    assert code == 0, f"init 실패 — {out!r} {err!r}"
    return project_root, task


def _t147_next_sequence(task):
    records = _segment_records(task)
    return max([r.get("sequence") or 0 for r in records] + [0]) + 1


def _t147_seg_event(task, event_name, *, sequence, actor, recorded_by, data,
                    summary, timestamp, caused_by_event_id=None, event_id=None,
                    actor_sequence=1):
    """CONTRACT §1.1 공통 필드를 갖춘 사건 1건을 활성 조각에 직접 append한다.

    `pm.report`·`stop.decision`을 방출하는 정규 CLI 경로가 아직 없으므로(W-4·W-5·W-7
    미구현) §2.5 읽기 판정이 전제하는 사건 조각을 실제 디스크 파일로 만든다 —
    mock/patch가 아니라 실제 조각 조작이며, 기존 `_append_segment_line` 관례와 같다."""
    block = _read_state(task).get("run_log") or {}
    event = {
        "schema_version": "1.0",
        "event_id": event_id or f"evt_{uuid.uuid4()}",
        "request_id": f"req_{uuid.uuid4()}",
        "sequence": sequence,
        "actor_sequence": actor_sequence,
        "timestamp": timestamp,
        "task_id": pathlib.Path(task).name,
        "run_id": block.get("active_run_id"),
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": caused_by_event_id,
        "stage": "EXECUTE",
        "task_step": None,
        "work_item": None,
        "gate_id": None,
        "event": event_name,
        "actor": actor,
        "provenance": {"type": "direct", "recorded_by": recorded_by,
                       "worker_log_token_id": None, "source": None},
        "summary": summary,
        "reason": None,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": [],
        "data": data,
    }
    _append_segment_line(task, event)
    return event


_T147_PM_ACTOR = {"kind": "PM", "id": "PM", "provider": None, "session_id": None}
_T147_PM_RECORDED_BY = {"kind": "PM", "id": "PM"}
_T147_TOOL_ACTOR = {"kind": "tool", "id": "ownership-tool",
                    "provider": None, "session_id": None}
_T147_TOOL_RECORDED_BY = {"kind": "tool", "id": "state-tool"}


def _t147_report_event(task, *, sequence, report_type, transition_action,
                       user_input_required, timestamp, summary="T147 보고"):
    return _t147_seg_event(
        task, "pm.report", sequence=sequence, actor=_T147_PM_ACTOR,
        recorded_by=_T147_PM_RECORDED_BY, summary=summary, timestamp=timestamp,
        data={"report_type": report_type, "transition_action": transition_action,
              "user_input_required": user_input_required})


def _t147_decision_event(task, *, sequence, decision_kind, timestamp,
                         report_event_id=None, last_activity_event_id=None,
                         summary="T147 정지 판정"):
    event_id = f"evt_{uuid.uuid4()}"
    return _t147_seg_event(
        task, "stop.decision", sequence=sequence, actor=_T147_TOOL_ACTOR,
        recorded_by=_T147_TOOL_RECORDED_BY, summary=summary, timestamp=timestamp,
        event_id=event_id, caused_by_event_id=report_event_id,
        data={"decision_kind": decision_kind, "diagnostics": [], "block_count": 1,
              "claim_source": "state_transition",
              "report_event_id": report_event_id,
              "last_activity_event_id": last_activity_event_id})


def _t147_activity_event(task, *, sequence, timestamp, summary, kind="progress"):
    return _t147_seg_event(
        task, "activity", sequence=sequence, actor=_T147_PM_ACTOR,
        recorded_by=_T147_PM_RECORDED_BY, summary=summary, timestamp=timestamp,
        data={"kind": kind})


def _t147_axes(data):
    """응답에서 정지 판정 5축만 뽑는다. 축이 없으면 KeyError 대신 sentinel."""
    return {axis: data.get(axis, "<missing>") for axis in _T147_STOP_VERDICT_AXES}


def _assert_t147_stop_verdict_item_shapes(test_case, data, scenario):
    """D-14 5축 항목은 축별 고정 키만 반환한다(자유문 복사 방지 포함)."""
    for axis, expected_keys in _T147_STOP_VERDICT_ITEM_KEYS.items():
        for item in data.get(axis) or []:
            test_case.assertEqual(
                set(item), expected_keys,
                f"{scenario} {axis} 항목 키가 고정 계약과 다름 — {item!r}")


class TestT147S7StopDecisionReceiptDrain(unittest.TestCase):
    """TASK-147.S-7 (AC-3, AC-7, C-3, H-4) — GREEN: W-7. **구현 전 RED**.

    훅 receipt의 `pending_decisions[]` 1건이 `state-tool` 상태 전이 1회에서
    `stop.decision`(조합 A7)으로 조각에 커밋되고 receipt에서 제거된다.
    `caused_by_event_id`는 대응 `pm.report`의 `event_id`이고,
    `data.last_activity_event_id`는 판정 시각 직전 마지막 `activity`를 가리킨다.
    `data`는 폐쇄 6키만 가지며 receipt에 섞인 자유 서술·비밀값은 조각에 평문 0건이다.

    현재 관찰: `StopReceipt`에 `pending_decisions` 필드 자체가 없고
    `run_log_commit()`에 drain 경로가 없다(2026-09-19 실측).
    """

    def test_pending_decision_is_committed_and_removed_on_state_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root, task = _t147_project_capsule(tmp, "147-s7-drain")

            # ① 판정 입력이 된 pm.report와 그 뒤의 activity를 실제 조각에 둔다.
            report = _t147_report_event(
                task, sequence=_t147_next_sequence(task),
                report_type="progress_report", transition_action="continue",
                user_input_required=False, timestamp="2026-09-19T01:00:00.000Z")
            activity = _t147_activity_event(
                task, sequence=_t147_next_sequence(task),
                timestamp="2026-09-19T01:01:00.000Z", summary="T147 S-7 직전 활동")

            # ② 훅 receipt에 판정 1건을 적재한다. 자유 서술·비밀값을 일부러 섞는다.
            session_id = "sess-t147-s7"
            receipt_path = (project_root / ".opal" / "run" / ".runtime" /
                            "stop-guard" / f"{session_id}.json")
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(json.dumps({
                "session_id": session_id,
                "fingerprint": "f" * 64,
                "decision_kind": "block_continue",
                "decided_at": "2026-09-19T01:02:00.000Z",
                "block_count": 1,
                # Stop 봉투의 원문도 receipt에 남을 수 있지만 W-7 drain은 이를
                # 사건으로 복사하지 않는다(AC-7).
                "last_assistant_message": (
                    f"T147 S-7 fixture assistant message: {_T147_SECRETS['raw_prompt']}"),
                "pending_decisions": [{
                    "decision_kind": "block_continue",
                    "diagnostics": ["no_progress_same_fingerprint"],
                    "block_count": 1,
                    "claim_source": "state_transition",
                    "report_event_id": report["event_id"],
                    "task_path": str(task),
                    "decided_at": "2026-09-19T01:02:00.000Z",
                    # 폐쇄 6키 밖 — 커밋된 사건에 실려서는 안 되는 자유 서술·비밀값
                    "note": f"T147 S-7 자유 서술 {_T147_SECRETS['raw_prompt']}",
                    "secret": _T147_SECRETS["bearer_token"],
                }],
            }, ensure_ascii=False), encoding="utf-8")

            # ③ 상태 전이 1회 — drain 경로 진입
            env = dict(os.environ, OPAL_SESSION_ID=session_id)
            cmd = ["bash", str(_RUN_SH), "mark", str(task), "--row", "1", "--done"]
            proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
            self.assertEqual(
                proc.returncode, 0,
                f"TASK-147.S-7 상태 전이 실패 — stdout={proc.stdout!r} stderr={proc.stderr!r}")

            decisions_recorded = _t147_stop_decisions(task)
            self.assertEqual(
                len(decisions_recorded), 1,
                f"TASK-147.S-7 drain된 stop.decision이 1건이 아님(미구현 RED) — "
                f"{[r.get('event') for r in _segment_records(task)]}")
            decision = decisions_recorded[0]

            self.assertEqual(
                decision.get("caused_by_event_id"), report["event_id"],
                "TASK-147.S-7 caused_by_event_id가 대응 pm.report를 가리키지 않음")
            self.assertEqual(
                decision.get("actor", {}).get("id"), "ownership-tool",
                f"TASK-147.S-7 actor.id가 ownership-tool이 아님(§1.1.1) — {decision.get('actor')}")
            self.assertEqual(
                decision.get("provenance", {}).get("recorded_by"),
                {"kind": "tool", "id": "state-tool"},
                f"TASK-147.S-7 recorded_by가 state-tool이 아님 — {decision.get('provenance')}")
            self.assertEqual(
                set((decision.get("data") or {}).keys()), _T147_STOP_DECISION_DATA_KEYS,
                f"TASK-147.S-7 data가 폐쇄 6키와 다름(§1.3) — {decision.get('data')!r}")
            self.assertEqual(
                decision["data"].get("last_activity_event_id"), activity["event_id"],
                "TASK-147.S-7 last_activity_event_id가 판정 직전 activity를 가리키지 않음")
            self.assertEqual(
                decision["data"].get("report_event_id"), report["event_id"],
                "TASK-147.S-7 report_event_id가 대응 pm.report와 다름")
            self.assertEqual(
                decision.get("summary"),
                ("stop.decision: decision_kind=block_continue; "
                 "diagnostics=no_progress_same_fingerprint; block_count=1; "
                 "claim_source=state_transition; report_event_id="
                 f"{report['event_id']}; last_activity_event_id={activity['event_id']}"),
                "TASK-147.S-7 summary가 D-16 renderer 템플릿과 다름")
            self.assertEqual(
                decision.get("event_id"), decision.get("request_id"),
                "TASK-147.S-7 stop.decision event_id/request_id가 사전 확정 동일값이 아님")
            for field in ("reason", "reason_code", "duration_unknown_reason", "refs"):
                self.assertIsNone(
                    decision.get(field),
                    f"TASK-147.S-7 {field}가 D-16의 null 폐쇄를 어김 — {decision.get(field)!r}")

            remaining = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(
                remaining.get("pending_decisions") or [], [],
                f"TASK-147.S-7 커밋 후 receipt에 판정이 남아 있음 — {remaining!r}")

            segment_text = "".join(
                seg.read_text(encoding="utf-8")
                for seg in sorted((task / "run").glob("run-log-*.jsonl")))
            pending_text = json.dumps((_read_state(task).get("run_log") or {}).get("pending_events") or [],
                                      ensure_ascii=False)
            for kind in ("raw_prompt", "bearer_token"):
                self.assertNotIn(
                    _T147_SECRETS[kind], segment_text,
                    f"TASK-147.S-7 receipt의 {kind} 평문이 조각에 실림(AC-7 위반)")
                self.assertNotIn(
                    _T147_SECRETS[kind], pending_text,
                    f"TASK-147.S-7 receipt의 {kind} 평문이 pending_events에 실림(AC-7 위반)")


class TestT147S9StopVerdictAxesClassifyFourCases(unittest.TestCase):
    """TASK-147.S-9 (AC-5, C-1) — GREEN: W-9. **구현 전 RED**.

    MV-34 — 4분류 재현 조각 4벌이 각각 `report_intent_inconsistent` /
    `missing_stop_decision` / `stop_decision_allowed` / `stop_block_without_followup`
    **하나에만** 잡히고, 정상 흐름 조각에서는 5축 전부 빈 배열이다. 기존 4축과
    관측 지점 3필드는 불변이며 read-only·비차단(exit 0)이다.

    현재 관찰: `verify --run-log-completeness-check` 응답에 5축이 하나도 없다
    (2026-09-19 실측 — 응답 키는 기존 4축 + 관측 3필드뿐).
    """

    def _assert_exactly_one_axis(self, task, expected_axis, scenario):
        code, out, err, data, unchanged = _completeness(task)
        self.assertEqual(code, 0,
                         f"{scenario} 비차단(exit 0) 위반 — exit={code} {out!r} {err!r}")
        self.assertTrue(unchanged, f"{scenario} read-only 위반 — state.json이 변경됨")
        _assert_t147_stop_verdict_item_shapes(self, data, scenario)
        for axis in _T147_STOP_VERDICT_AXES:
            self.assertIn(axis, data, f"{scenario} 판정 축 {axis} 부재(§2.5) — {sorted(data)}")
        for field in _T147_EXISTING_AXES + _T147_OBSERVATION_FIELDS:
            self.assertIn(field, data,
                          f"{scenario} 기존 축·관측 필드 {field}가 사라짐(§2.5 불변) — {sorted(data)}")
        axes = _t147_axes(data)
        self.assertTrue(axes[expected_axis],
                        f"{scenario} {expected_axis}에 잡히지 않음 — {axes!r}")
        for axis, items in axes.items():
            if axis == expected_axis:
                continue
            self.assertEqual(items, [],
                             f"{scenario} {axis}에도 잡힘(하나에만 잡혀야 함) — {axes!r}")

    def test_report_intent_inconsistent_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="147-s9-intent")
            self.assertEqual(_init_shadow(task)[0], 0)
            # decision_request ∧ transition_action=continue — 뒤 앵커를 두지 않아
            # missing_stop_decision의 앵커 쌍이 성립하지 않는다(§2.5).
            _t147_report_event(
                task, sequence=_t147_next_sequence(task),
                report_type="decision_request", transition_action="continue",
                user_input_required=True, timestamp="2026-09-19T02:00:00.000Z")
            self._assert_exactly_one_axis(task, "report_intent_inconsistent",
                                          "TASK-147.S-9(a)")

    def test_missing_stop_decision_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="147-s9-missing")
            self.assertEqual(_init_shadow(task)[0], 0)
            _t147_report_event(
                task, sequence=_t147_next_sequence(task),
                report_type="progress_report", transition_action="await_user",
                user_input_required=False, timestamp="2026-09-19T02:00:00.000Z")
            # 보고보다 늦은 사건(뒤 앵커)은 있는데 그 사이에 stop.decision이 없다.
            _t147_activity_event(
                task, sequence=_t147_next_sequence(task),
                timestamp="2026-09-19T02:05:00.000Z", summary="T147 S-9 다음 턴 활동")
            self._assert_exactly_one_axis(task, "missing_stop_decision",
                                          "TASK-147.S-9(b)")

    def test_stop_decision_allowed_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="147-s9-allowed")
            self.assertEqual(_init_shadow(task)[0], 0)
            report = _t147_report_event(
                task, sequence=_t147_next_sequence(task),
                report_type="decision_request", transition_action="await_user",
                user_input_required=True, timestamp="2026-09-19T02:00:00.000Z")
            _t147_decision_event(
                task, sequence=_t147_next_sequence(task),
                decision_kind="allow_await_user",
                timestamp="2026-09-19T02:01:00.000Z",
                report_event_id=report["event_id"])
            self._assert_exactly_one_axis(task, "stop_decision_allowed",
                                          "TASK-147.S-9(c)")

    def test_stop_block_without_followup_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="147-s9-block")
            self.assertEqual(_init_shadow(task)[0], 0)
            report = _t147_report_event(
                task, sequence=_t147_next_sequence(task),
                report_type="progress_report", transition_action="continue",
                user_input_required=False, timestamp="2026-09-19T02:00:00.000Z")
            _t147_decision_event(
                task, sequence=_t147_next_sequence(task),
                decision_kind="block_continue",
                timestamp="2026-09-19T02:01:00.000Z",
                report_event_id=report["event_id"])
            # 차단 뒤 run 종료까지 activity·state.changed 0건.
            self._assert_exactly_one_axis(task, "stop_block_without_followup",
                                          "TASK-147.S-9(d)")

    def test_normal_flow_leaves_all_five_axes_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="147-s9-normal")
            self.assertEqual(_init_shadow(task)[0], 0)
            # 상태 전이(state.changed)에 앵커된 활동 + 의도가 일관된 마지막 보고.
            self.assertEqual(_run(["advance", str(task), "--row", "1"])[0], 0)
            _t147_activity_event(
                task, sequence=_t147_next_sequence(task),
                timestamp="2026-09-19T03:00:00.000Z", summary="T147 S-9 앵커된 활동")
            _t147_report_event(
                task, sequence=_t147_next_sequence(task),
                report_type="decision_request", transition_action="await_user",
                user_input_required=True, timestamp="2026-09-19T03:01:00.000Z")

            code, out, err, data, unchanged = _completeness(task)
            self.assertEqual(code, 0, f"TASK-147.S-9(e) exit 0 위반 — {out!r} {err!r}")
            self.assertTrue(unchanged, "TASK-147.S-9(e) read-only 위반")
            for axis in _T147_STOP_VERDICT_AXES:
                self.assertIn(axis, data,
                              f"TASK-147.S-9(e) 판정 축 {axis} 부재(§2.5) — {sorted(data)}")
                self.assertEqual(data[axis], [],
                                 f"TASK-147.S-9(e) 정상 흐름인데 {axis}가 비어 있지 않음 — {data[axis]!r}")


class TestT147S10UnanchoredActivityAndProgressExclusion(unittest.TestCase):
    """TASK-147.S-10 (AC-1, C-1) — GREEN: W-9. **구현 전 RED**.

    D-10(b) 오인 방지 — 동일 결과가 반복되는 `activity`와 어떤 상태 전이에도
    앵커되지 않는 `activity`는 `unanchored_activity`에 잡히고 진행으로 계산되지
    않는다. `pm.report`·`stop.decision`은 `activity`가 아니므로(§1.2) 이 판정의
    대상이 아니고 어떤 진행 집계에도 포함되지 않는다.
    """

    def test_repeated_and_unanchored_activities_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="147-s10-unanchored")
            self.assertEqual(_init_shadow(task)[0], 0)

            repeated = []
            for i in range(3):
                repeated.append(_t147_activity_event(
                    task, sequence=_t147_next_sequence(task),
                    timestamp=f"2026-09-19T04:0{i}:00.000Z",
                    summary="T147 S-10 동일 결과 반복"))
            drifting = _t147_activity_event(
                task, sequence=_t147_next_sequence(task),
                timestamp="2026-09-19T04:10:00.000Z",
                summary="T147 S-10 어떤 상태 전이에도 앵커되지 않는 활동")

            code, out, err, data, unchanged = _completeness(task)
            self.assertEqual(code, 0, f"TASK-147.S-10 exit 0 위반 — {out!r} {err!r}")
            self.assertTrue(unchanged, "TASK-147.S-10 read-only 위반")
            _assert_t147_stop_verdict_item_shapes(self, data, "TASK-147.S-10(a)")
            self.assertIn("unanchored_activity", data,
                          f"TASK-147.S-10 unanchored_activity 축 부재(§2.5) — {sorted(data)}")
            _assert_t147_stop_verdict_item_shapes(self, data, "TASK-147.S-10(b)")
            items_text = json.dumps(data["unanchored_activity"], ensure_ascii=False)
            self.assertTrue(
                data["unanchored_activity"],
                f"TASK-147.S-10 반복·무앵커 activity가 잡히지 않음 — {data!r}")
            for event in repeated[1:] + [drifting]:
                self.assertIn(
                    event["event_id"], items_text,
                    f"TASK-147.S-10 {event['summary']!r}가 unanchored_activity에 없음 — {items_text}")

    def test_pm_report_and_stop_decision_are_not_counted_as_activity(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = _mktask(tmp, name="147-s10-exclusion")
            self.assertEqual(_init_shadow(task)[0], 0)

            report = _t147_report_event(
                task, sequence=_t147_next_sequence(task),
                report_type="progress_report", transition_action="continue",
                user_input_required=False, timestamp="2026-09-19T05:00:00.000Z")
            decision = _t147_decision_event(
                task, sequence=_t147_next_sequence(task),
                decision_kind="block_continue",
                timestamp="2026-09-19T05:01:00.000Z",
                report_event_id=report["event_id"])

            code, out, err, data, unchanged = _completeness(task)
            self.assertEqual(code, 0, f"TASK-147.S-10 exit 0 위반 — {out!r} {err!r}")
            self.assertIn("unanchored_activity", data,
                          f"TASK-147.S-10 unanchored_activity 축 부재(§2.5) — {sorted(data)}")
            items_text = json.dumps(data["unanchored_activity"], ensure_ascii=False)
            self.assertEqual(
                data["unanchored_activity"], [],
                f"TASK-147.S-10 pm.report·stop.decision이 activity 판정에 포함됨 — {items_text}")
            for event_id in (report["event_id"], decision["event_id"]):
                self.assertNotIn(
                    event_id, items_text,
                    f"TASK-147.S-10 {event_id}가 activity 진행 집계에 들어감(§1.2 위반)")
