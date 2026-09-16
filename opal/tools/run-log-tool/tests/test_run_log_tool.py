"""
@header {
  "module": "test_run_log_tool",
  "layer": "test",
  "domain": "opal-tools",
  "description": "run-log-tool 서브명령(init/append/validate-run/import-agentic/import-oppl) 계약 테스트. §1.1/§1.2 폐쇄형 스키마, §1.3 4축 조합 전수·명시적 거부·사건별 actor 제약, 요청 식별자 멱등, 16 KiB 직렬화 상한, actor_sequence 범위, legacy·oppl 가져오기 멱등·구조 정규화, active 모드 source 제약, 기존 회귀 무손상을 S-3~S-29 시나리오로 판정한다. 이와 별개로 가져오기 읽기 경로의 심볼릭 링크·하드 링크·비정규 파일(FIFO) 거부와 정상 입력 비차단을 잠긴 시나리오 목록 밖에서 회귀 고정한다(보안 검사가 실측한 방어 대상). run.sh subprocess 실호출 + 디스크 조각 파일 검사만으로 판정하며, mock/patch/MagicMock/스텁/가짜 파일시스템은 사용하지 않는다(opal/tools/backlog-tool/tests/test_backlog_tool.py 관례 복제, red-first.md §4). state.json·state_tool 결합 0건을 정적+동적으로 함께 판정한다(AC-19/MV-24, TRD D-5). 시크릿 마스킹 3경로·redact 멱등과 크기 순서·마스킹과 보존 식별자 공존·세그먼트 경계 동시성 배리어·심볼릭 링크 방어 재사용·닫힌 세그먼트 불변성과 세그먼트 간 시퀀스·duration span 산출과 reconcile을 S1~S7 클래스로 회귀 고정한다. 태스크 137: CONTRACT §1.3 PM activity payload 축 폐쇄(A4 한정)를 인프로세스 append()와 run-log-tool append CLI 두 생산 경로에서 schema_invalid 거부·조각 바이트 불변으로 판정하고, A8 import·A2 worker direct 조합의 다중 키 data 수용으로 적용 조건 경계가 새지 않음을 함께 고정한다.",
  "exports": [
    "TestInitIdempotent", "TestAppendEvent", "TestValidateRunPass",
    "TestPathContractRejection", "TestSchemaRejection", "TestStateAssetIndependence",
    "TestCombinationExhaustiveRejection", "TestExplicitRejectionCombinations",
    "TestEventActorConstraintExhaustive", "TestProvenanceEvidenceViolations",
    "TestConditionalRequiredFieldViolations", "TestIdempotentSamePayloadReplay",
    "TestIdempotentConflictOnDifferentPayload", "TestIdempotentNormalizationInvariance",
    "TestSerializationSizeCap", "TestActorSequenceWorkerRunIdScope",
    "TestSequenceGlobalMonotonic", "TestLegacyImportIdempotent",
    "TestLegacyStructuralVariantNormalization", "TestOpplDualStructureNormalization",
    "TestOpplImportIdempotent", "TestDryRunNoWrite", "TestRunIdResolutionAmbiguity",
    "TestStateAssetIndependenceExtended", "TestExistingRegressionSuiteUnaffected",
    "TestActiveModeSourceConstraint", "TestImportReadPathDefenses",
    "TestS1SecretMaskingAcrossThreePaths", "TestS2RedactIdempotentAndSizeOrder",
    "TestS3PreservedIdentifiersSurviveMaskingAlongsideSecrets", "TestS4SegmentBoundaryConcurrentBarrier",
    "TestS5SegmentBoundarySymlinkDefenseReuse", "TestS6ClosedSegmentImmutabilityCrossSegmentSequence",
    "TestS7DurationSpansAndReconcile",
    "TestPmActivityDataClosureInProcess", "TestPmActivityDataClosureCli",
    "TestPmActivityDataClosureScopeBoundary"
  ],
  "scenarios": [
    "S-3", "S-4", "S-5", "S-6", "S-7", "S-8",
    "S-10", "S-11", "S-12", "S-13", "S-14", "S-15", "S-16", "S-17", "S-18", "S-19",
    "S-20", "S-21", "S-22", "S-23", "S-24", "S-25", "S-26", "S-27", "S-28", "S-29"
  ]
}

PLAN.md(T02) §테스트 시나리오 초안 근거:
  - S-3 run-log-tool.init 멱등 (created:true → created:false, 조각 바이트 불변)
  - S-4 run-log-tool.append 표준 사건 1건 (event_id evt_ 접두, sequence/actor_sequence/segment/idempotent_hit, 선행 줄 불변)
  - S-5 run-log-tool.validate-run 관통 판정 (verdict==pass, segment_count/event_count/sequence_gaps/violations/total_bytes)
  - S-6 §3.2/MV-27 상대경로 task path 거부 (task_path_not_absolute, cwd 불문)
  - S-7 §1.1 폐쇄형 스키마 거부 + 부분 쓰기 없음 — (a) event enum 밖 값, (b) append 대상 payload가 §1.1 스키마를 위반하는 --data
  - S-8 AC-19/MV-24/D-5 — 기록 도구가 state.json 자산 없이 성립 (정적 판정 포함)

PLAN.md(T03) §테스트 시나리오 초안 근거 (opal-test-agent mode=red 축, GREEN 미착수):
  - S-10 §1.3 표 밖 4축 조합 전수 거부 — run_log_core.iter_all_combinations()/combination_of() 파생
  - S-11 명시적 거부 조합 4종 (PM 대필·worker direct token 부재·adapter recorded_by 불일치·import recorded_by 불일치)
  - S-12 사건 종류별 actor 제약 전수 60쌍 — run_log_core.ALLOWED_EVENTS × 5개 actor_kind, 기대값은 EVENT_ACTOR_CONSTRAINTS에서 파생
  - S-13 adapter·import 필수 증거 결측·형식 위반 11건 + 대조군 2건
  - S-14 §1.2 조건부 필수 필드 위반 10건(원안 11건 중 (k) timestamp 위반은 현재 append CLI가 --timestamp를 노출하지 않아 재현 불가 — 범위에서 제외, 아래 클래스 docstring 참조)
  - S-15/S-16/S-17 멱등 판정 — 동일 payload 재호출·다른 payload 충돌·키 순서와 발급 필드 불변
  - S-18 16 KiB 직렬화 상한(UTF-8 바이트 기준, 거부가 순번을 소모하지 않음)
  - S-19 actor_sequence 범위 교정 — actor.kind=worker는 worker_run_id 범위
  - S-20 sequence run 전역 단조(red_required=false)
  - S-21/S-22 legacy(AGENTIC-LOG.md) 가져오기 멱등과 구조 변종 식별(헤더 행 기준, 시각 없는 행 제외)
  - S-23/S-24/S-25 oppl(.oppl-run/) 이원 구조 정규화·비수집 경계·가져오기 멱등·--dry-run 무쓰기
  - S-26 --run-id 해석과 모호성 거부
  - S-27 기록 도구 state 자산 독립 유지 확장(red_required=false)
  - S-28 기존 회귀 무손상(red_required=false) — run-log-tool 기존 8건 + state-tool 428건
  - S-29 PM 판정② — 명시적 --mode 인자로만 active 전용 source 제약을 게이트, 코어는 모드를 어디서도 읽지 않는다

surfaces.json 근거: run-log-tool.init/.append/.validate-run/.import-agentic/.import-oppl 5표면의 request_shape/response_shape.
CONTRACT §2.1 응답 봉투: {"ok":true,"data":{...}} / {"ok":false,"error":{"code","message","detail"}}.
"""

import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

# run-log-tool run.sh 위치 — RED 단계에서는 파일 자체가 부재(디렉터리도 신설 전)
_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"
_CORE_SRC = _TOOL_DIR / "run_log_core.py"
_CLI_SRC = _TOOL_DIR / "run_log_tool.py"


# ─────────────────────────────────────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _run(args, cwd=None):
    """run.sh를 subprocess로 실행하여 (returncode, stdout_text, stderr_text, parsed_json) 반환.
    run.sh 부재 시 bash가 자체 오류(exit 127 등)를 내며 비정상 종료한다 — 이 역시 RED 증거다.
    """
    cmd = ["bash", str(_RUN_SH)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


def _abs_task_dir(tmp_root, name):
    p = pathlib.Path(tmp_root) / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def _append_activity_args(task_path, run_id, request_id, summary):
    return [
        "append", "--task", str(task_path), "--run-id", run_id,
        "--request-id", request_id, "--event", "activity",
        "--actor-kind", "PM", "--actor-id", "pm",
        "--provenance-type", "direct", "--recorded-by-kind", "PM",
        "--summary", summary, "--format", "json",
    ]


# ─────────────────────────────────────────────────────────────────────────────
# T03 공통 헬퍼 — combination_of()/iter_all_combinations()/EVENT_ACTOR_CONSTRAINTS
# 등 신규 공개 함수·상수를 파생시키기 위해 run_log_core를 파이썬 모듈로 직접
# import한다(subprocess 호출과 별개 — S-10/S-12/S-19·S-20에서 조합·기대값 생성에 필요).
# 이 함수들은 GREEN 전환 전까지 존재하지 않으므로 호출 시 AttributeError가 나며,
# 이는 그 자체로 유효한 RED 증거다.
# ─────────────────────────────────────────────────────────────────────────────

def _import_core():
    if str(_TOOL_DIR) not in sys.path:
        sys.path.insert(0, str(_TOOL_DIR))
    import run_log_core
    return run_log_core


_PROJECT_ROOT = _TOOL_DIR.parent.parent.parent
_SAMPLE_AGENTIC_LOG = (
    _PROJECT_ROOT / "tasks" / "104-260830-opp-역공학-개념모델링-스킵" / "AGENTIC-LOG.md"
)

# S-22 — M-4 실측의 5가지 변종(요약 표·V1 6열 표·V2 4열 표·V3 자유 서술·V4 불릿)을
# 한 파일에 재현한다. V1의 6행 중 2행은 시각이 `YYYY-MM-DD HH:mm`을 만족하지 않아
# 후보에서 제외되어야 하므로(D-T03-12), 정상 4행만 인식·가져오기 대상이다.
_S22_MIXED_LOG = """# AGENTIC-LOG: S-22 혼합 변종 샘플

## 요약

| 항목 | 건수 |
|------|------|
| 게이트 판단 | 1회 |

## 대행 일지

| # | 시점 | 단계 | 카테고리 | 내용 | 결과 |
|---|------|------|----------|------|------|
| 1 | 2026-09-12 14:49 | TASK | DECISION | S-22 정상 행 1 | 반영 |
| 2 | 2026-09-12 14:50 | PLAN | GATE | S-22 정상 행 2 | Pass |
| 3 | 2026-09-03 | EXECUTE | FIX | S-22 날짜만(시각 없음) — 제외 대상 | 반영 |
| 4 | 2026-09-12 20:0x | EXECUTE | ERROR | S-22 자리표시자(시각 없음) — 제외 대상 | 보정 |
| 5 | 2026-09-12 15:01 | CLOSE | IMPROVE | S-22 정상 행 3 | 완료 |
| 6 | 2026-09-12 15:02 | CLOSE | ESCALATION | S-22 정상 행 4 | 완료 |

## PM 자율 판단 로그

| # | 시점 | 판단 | 근거 |
|---|------|------|------|
| 1 | TEST-SCENARIO 게이트 후 | S-22 V2 표 — 인식하지 않음 | 근거 텍스트 |

## [DECISION] S-22 V3 자유 서술

이 절은 표가 아니라 자유 서술이므로 인식하지 않는다.

## [GATE] S-22 V3 자유 서술 2

Pass — 자유 서술 2.

## 불릿 목록

- S-22 V4 불릿 1
- S-22 V4 불릿 2
"""

_APPEND_FLAG_MAP = {
    "request_id": "--request-id",
    "event": "--event",
    "actor_kind": "--actor-kind",
    "actor_id": "--actor-id",
    "provenance_type": "--provenance-type",
    "recorded_by_kind": "--recorded-by-kind",
    "worker_run_id": "--worker-run-id",
    "source_kind": "--source-kind",
    "source_id": "--source-id",
    "source_sha256": "--source-sha256",
    "source_observed_at": "--source-observed-at",
    "source_locator": "--source-locator",
    "upstream_event_id": "--upstream-event-id",
    "stage": "--stage",
    "task_step": "--task-step",
    "work_item": "--work-item",
    "gate_id": "--gate-id",
    "caused_by_event_id": "--caused-by-event-id",
    "summary": "--summary",
    "reason": "--reason",
    "reason_code": "--reason-code",
    "duration_ms": "--duration-ms",
    "duration_source": "--duration-source",
    "duration_unknown_reason": "--duration-unknown-reason",
    "mode": "--mode",
}


def _append_raw(task_path, run_id, **kwargs):
    """append 인자를 CLI 플래그로 조립한다 (S-10 이후 조합·멱등·상한·모드 시나리오 공용).

    `--mode`(D-T03 신규)는 GREEN 전환 전까지 argparse 미인식 인자로 자체 오류를
    내며, 그 자체가 S-29의 RED 증거다."""
    kwargs = dict(kwargs)
    args = ["append", "--task", str(task_path), "--run-id", run_id]
    data_value = kwargs.pop("data", None)
    refs_value = kwargs.pop("refs", None)
    for key, flag in _APPEND_FLAG_MAP.items():
        if kwargs.get(key) is not None:
            args += [flag, str(kwargs[key])]
    if data_value is not None:
        if isinstance(data_value, (dict, list)):
            data_value = json.dumps(data_value, ensure_ascii=False)
        args += ["--data", data_value]
    if refs_value is not None:
        args += ["--refs"] + list(refs_value)
    args += ["--format", "json"]
    return args


def _segment_of(task_path, run_id):
    return task_path / "run" / f"run-log-{run_id}-0001.jsonl"


# ─────────────────────────────────────────────────────────────────────────────
# S-3 — run-log-tool.init 멱등
# ─────────────────────────────────────────────────────────────────────────────

class TestInitIdempotent(unittest.TestCase):
    def test_init_twice_is_idempotent_and_segment_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s3-task")
            run_id = "run_s3"

            code1, out1, err1, data1 = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code1, 0, f"S-3 1회차 init 실패 — exit={code1} stdout={out1!r} stderr={err1!r}")
            self.assertTrue(data1.get("ok"), f"S-3 1회차 ok:false — {data1}")
            self.assertTrue(data1.get("data", {}).get("created"),
                             f"S-3 1회차 created!=true — {data1}")

            segment = task_path / "run" / f"run-log-{run_id}-0001.jsonl"
            self.assertTrue(segment.exists(), f"S-3 조각 파일 부재: {segment}")
            before = segment.read_bytes()

            code2, out2, err2, data2 = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code2, 0, f"S-3 2회차 init 실패 — exit={code2} stdout={out2!r} stderr={err2!r}")
            self.assertTrue(data2.get("ok"), f"S-3 2회차 ok:false — {data2}")
            self.assertFalse(data2.get("data", {}).get("created", True),
                              f"S-3 2회차 created!=false — {data2}")

            after = segment.read_bytes()
            self.assertEqual(before, after, "S-3 2회차 init이 조각 내용을 변경함")

            fragments = sorted((task_path / "run").glob(f"run-log-{run_id}-*.jsonl"))
            self.assertEqual(len(fragments), 1, f"S-3 조각 파일이 1개가 아님: {fragments}")


# ─────────────────────────────────────────────────────────────────────────────
# S-4 — run-log-tool.append 표준 사건 1건
# ─────────────────────────────────────────────────────────────────────────────

class TestAppendEvent(unittest.TestCase):
    def test_append_adds_one_standard_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s4-task")
            run_id = "run_s4"

            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-4 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            segment = task_path / "run" / f"run-log-{run_id}-0001.jsonl"
            before_lines = segment.read_text(encoding="utf-8").splitlines() if segment.exists() else []

            code, out, err, data = _run(_append_activity_args(task_path, run_id, "req_s4_1", "S-4 표준 사건 append 검증"))
            self.assertEqual(code, 0, f"S-4 append 실패 — exit={code} stdout={out!r} stderr={err!r}")
            self.assertTrue(data.get("ok"), f"S-4 ok:false — {data}")

            body = data.get("data", {})
            self.assertTrue(str(body.get("event_id", "")).startswith("evt_"),
                             f"S-4 event_id가 evt_ 접두가 아님 — {body}")
            self.assertIn("sequence", body, f"S-4 응답에 sequence 없음 — {body}")
            self.assertIn("actor_sequence", body, f"S-4 응답에 actor_sequence 없음 — {body}")
            self.assertIn("segment", body, f"S-4 응답에 segment 없음 — {body}")
            self.assertFalse(body.get("idempotent_hit", True), f"S-4 idempotent_hit!=false — {body}")

            after_lines = segment.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(after_lines), len(before_lines) + 1,
                              "S-4 append 후 조각 줄 수가 정확히 1 증가하지 않음")
            for i, line in enumerate(before_lines):
                self.assertEqual(line, after_lines[i], f"S-4 선행 줄이 append 후 변경됨 (line {i})")

            new_event = json.loads(after_lines[-1])
            self.assertEqual(new_event.get("event"), "activity", f"S-4 새 줄의 event 필드 불일치 — {new_event}")


# ─────────────────────────────────────────────────────────────────────────────
# S-5 — run-log-tool.validate-run 관통 판정 (AC-2 종결 지점)
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateRunPass(unittest.TestCase):
    def test_validate_run_passes_after_two_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s5-task")
            run_id = "run_s5"

            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-5 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            for i in range(2):
                code, out, err, data = _run(
                    _append_activity_args(task_path, run_id, f"req_s5_{i}", f"S-5 사건 {i}"))
                self.assertEqual(code, 0, f"S-5 선행 append #{i} 실패 — stdout={out!r} stderr={err!r}")

            code, out, err, data = _run(
                ["validate-run", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code, 0, f"S-5 validate-run 실패 — exit={code} stdout={out!r} stderr={err!r}")
            self.assertTrue(data.get("ok"), f"S-5 ok:false — {data}")

            body = data.get("data", {})
            self.assertEqual(body.get("verdict"), "pass", f"S-5 verdict!=pass — {body}")
            self.assertEqual(body.get("segment_count"), 1, f"S-5 segment_count!=1 — {body}")
            self.assertEqual(body.get("event_count"), 2, f"S-5 event_count!=2 — {body}")
            self.assertEqual(body.get("sequence_gaps"), [], f"S-5 sequence_gaps 비어있지 않음 — {body}")
            self.assertEqual(body.get("violations"), [], f"S-5 violations 비어있지 않음 — {body}")
            self.assertGreater(body.get("total_bytes", 0), 0, f"S-5 total_bytes<=0 — {body}")


# ─────────────────────────────────────────────────────────────────────────────
# S-6 — §3.2 / MV-27: 상대 경로 task path를 추론 없이 거부
# ─────────────────────────────────────────────────────────────────────────────

class TestPathContractRejection(unittest.TestCase):
    def test_relative_task_path_rejected_without_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            rel_name = "s6-relative-task"
            (tmp_path / rel_name).mkdir()
            run_id = "run_s6"

            cases = {
                "init": ["init", "--task", f"./{rel_name}", "--run-id", run_id, "--format", "json"],
                "append": _append_activity_args(f"./{rel_name}", run_id, "req_s6", "S-6"),
                "validate-run": ["validate-run", "--task", f"./{rel_name}", "--run-id", run_id, "--format", "json"],
            }
            for label, args in cases.items():
                code, out, err, data = _run(args, cwd=str(tmp_path))
                self.assertNotEqual(code, 0, f"S-6 {label} 상대경로가 exit 0으로 통과함 — stdout={out!r}")
                self.assertFalse(data.get("ok", True), f"S-6 {label} ok:true — {data}")
                self.assertEqual(data.get("error", {}).get("code"), "task_path_not_absolute",
                                 f"S-6 {label} 오류 코드 불일치 — {data}")


# ─────────────────────────────────────────────────────────────────────────────
# S-7 — §1.1 폐쇄형 스키마: 정의되지 않은 값을 거부하고 부분 쓰기를 남기지 않는다
# ─────────────────────────────────────────────────────────────────────────────

class TestSchemaRejection(unittest.TestCase):
    def test_unknown_event_enum_value_rejected(self):
        """(a) §1.2 밖 event 값 — schema_invalid, 조각 부분 쓰기 없음"""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s7a-task")
            run_id = "run_s7a"

            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-7a 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            segment = task_path / "run" / f"run-log-{run_id}-0001.jsonl"
            before = segment.read_bytes() if segment.exists() else b""

            args = [
                "append", "--task", str(task_path), "--run-id", run_id,
                "--request-id", "req_s7a", "--event", "not_a_real_event",
                "--actor-kind", "PM", "--actor-id", "pm",
                "--provenance-type", "direct", "--recorded-by-kind", "PM",
                "--summary", "S-7a", "--format", "json",
            ]
            code, out, err, data = _run(args)
            self.assertNotEqual(code, 0, f"S-7a not_a_real_event가 exit 0으로 통과함 — stdout={out!r}")
            self.assertFalse(data.get("ok", True), f"S-7a ok:true — {data}")
            self.assertEqual(data.get("error", {}).get("code"), "schema_invalid", f"S-7a 오류 코드 불일치 — {data}")

            after = segment.read_bytes()
            self.assertEqual(before, after, "S-7a 거부됐는데도 조각 파일이 변경됨(부분 쓰기)")

    def test_schema_violating_data_payload_rejected(self):
        """(b) §1.1 스키마를 위반하는 --data(비-JSON) — schema_invalid, 조각 부분 쓰기 없음.
        surfaces.json의 append 표면은 정의된 필드에만 1:1 매핑되는 폐쇄 인자 집합이라
        CLI 정상 경로로는 미정의 최상위 키를 만들 수 없다 — 폐쇄형 스키마 검사가 실제로
        방어하는 CLI 도달 가능 표면은 §1.1 `data`(object) 필드의 타입 위반이다."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s7b-task")
            run_id = "run_s7b"

            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-7b 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            segment = task_path / "run" / f"run-log-{run_id}-0001.jsonl"
            before = segment.read_bytes() if segment.exists() else b""

            args = [
                "append", "--task", str(task_path), "--run-id", run_id,
                "--request-id", "req_s7b", "--event", "activity",
                "--actor-kind", "PM", "--actor-id", "pm",
                "--provenance-type", "direct", "--recorded-by-kind", "PM",
                "--summary", "S-7b", "--data", "{not-valid-json",
                "--format", "json",
            ]
            code, out, err, data = _run(args)
            self.assertNotEqual(code, 0, f"S-7b 손상된 --data가 exit 0으로 통과함 — stdout={out!r}")
            self.assertFalse(data.get("ok", True), f"S-7b ok:true — {data}")
            self.assertEqual(data.get("error", {}).get("code"), "schema_invalid", f"S-7b 오류 코드 불일치 — {data}")

            after = segment.read_bytes()
            self.assertEqual(before, after, "S-7b 거부됐는데도 조각 파일이 변경됨(부분 쓰기)")


# ─────────────────────────────────────────────────────────────────────────────
# S-8 — AC-19 / MV-24 / TRD D-5: 기록 도구가 state 자산 없이 성립
# ─────────────────────────────────────────────────────────────────────────────

class TestStateAssetIndependence(unittest.TestCase):
    def test_lifecycle_creates_no_state_json(self):
        """(a)+(c) state.json 없는 빈 절대경로 폴더에서 init→append→validate-run
        3연속이 전건 exit 0이며, 그 과정에서 tmpdir 어디에도 state.json이 생성되지 않는다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            task_path = _abs_task_dir(tmp, "s8-task")
            run_id = "run_s8"

            code1, out1, err1, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code1, 0, f"S-8 init 실패 — stdout={out1!r} stderr={err1!r}")

            code2, out2, err2, _ = _run(_append_activity_args(task_path, run_id, "req_s8", "S-8"))
            self.assertEqual(code2, 0, f"S-8 append 실패 — stdout={out2!r} stderr={err2!r}")

            code3, out3, err3, _ = _run(
                ["validate-run", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code3, 0, f"S-8 validate-run 실패 — stdout={out3!r} stderr={err3!r}")

            state_files = list(tmp_path.rglob("state.json"))
            self.assertEqual(state_files, [], f"S-8 state.json이 생성됨 — {state_files}")

    def test_source_has_no_state_tool_coupling(self):
        """(b) run_log_core.py·run_log_tool.py 소스에 state_tool import·state.json 문자열 0건 (정적 판정)"""
        for src_path in (_CORE_SRC, _CLI_SRC):
            self.assertTrue(src_path.exists(), f"S-8 소스 파일 부재: {src_path}")
            text = src_path.read_text(encoding="utf-8")
            self.assertNotIn("state_tool", text, f"S-8 {src_path.name}에 state_tool 결합 문자열 발견")
            self.assertNotIn("state.json", text, f"S-8 {src_path.name}에 state.json 문자열 발견")


# ─────────────────────────────────────────────────────────────────────────────
# S-10 — §1.3 표 밖 4축 조합 전수 거부 (AC-6/MV-2)
# ─────────────────────────────────────────────────────────────────────────────

class TestCombinationExhaustiveRejection(unittest.TestCase):
    def test_all_combinations_outside_table_are_rejected(self):
        core = _import_core()
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s10-task")
            run_id = "run_s10"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-10 선행 init 실패 — stdout={out0!r} stderr={err0!r}")
            segment = _segment_of(task_path, run_id)
            before = segment.read_bytes()

            combos = list(core.iter_all_combinations())
            self.assertGreater(len(combos), 0, "S-10 iter_all_combinations()가 조합을 생성하지 않음")
            rejected = [c for c in combos if core.combination_of(*c) is None]
            self.assertGreater(len(rejected), 0, "S-10 거부 대상 조합이 0건 — combination_of 판정 오류")

            for i, (actor_kind, prov_type, recorded_by_kind, source_kind) in enumerate(rejected):
                kwargs = dict(
                    request_id=f"req_s10_{i}", event="activity",
                    actor_kind=actor_kind, actor_id="x",
                    provenance_type=prov_type, recorded_by_kind=recorded_by_kind,
                    # activity의 §1.2 필수 필드(summary/data.kind)를 채워 스키마 단계를
                    # 통과시킨다 — 거부 사유가 조합 하나로만 좁혀지도록 한다(S-10 문언
                    # "증거 결측이 아니라 조합 때문에 거부됨을 분리한다").
                    summary="s10-reject", data={"kind": "progress"},
                )
                if actor_kind == "worker":
                    # actor.kind=worker는 PM 판정①에 따라 worker_run_id가 별도로 필수다 —
                    # 이 값이 없으면 조합과 무관하게 schema_invalid가 먼저 발생해 이 시나리오가
                    # 판정하려는 "조합만이 유일한 거부 사유"가 깨진다.
                    kwargs["worker_run_id"] = f"wrk_s10_{i}"
                if source_kind is not None:
                    kwargs.update(
                        source_kind=source_kind, source_id="sid",
                        source_sha256="a" * 64,
                        source_observed_at="2026-09-13T00:00:00.000Z",
                        source_locator="loc",
                    )
                code, out, errtext, data = _run(_append_raw(task_path, run_id, **kwargs))
                combo = (actor_kind, prov_type, recorded_by_kind, source_kind)
                self.assertNotEqual(code, 0, f"S-10 조합 {i} {combo}가 exit 0으로 통과함 — stdout={out!r}")
                self.assertFalse(data.get("ok", True), f"S-10 조합 {i} {combo} ok:true — {data}")
                self.assertEqual(data.get("error", {}).get("code"), "provenance_invalid",
                                  f"S-10 조합 {i} {combo} 오류 코드 불일치 — {data}")

            after = segment.read_bytes()
            self.assertEqual(before, after, "S-10 거부된 조합들이 조각 파일을 변경함(부분 쓰기)")

            # 허용 조합 중 activity가 성립하는 것만 골라 대조군으로 append하면 전건 ok:true.
            # A2(worker/direct/worker)는 D-T03-19에 따라 CLI가 worker_log_token_id를 항상
            # None으로 고정해 append 표면으로는 성립할 수 없으므로 제외한다.
            allowed = [c for c in combos if core.combination_of(*c) is not None]
            activity_actors = set(core.EVENT_ACTOR_CONSTRAINTS.get("activity", ()))
            success_combos = [
                c for c in allowed
                if c[0] in activity_actors and not (c[0] == "worker" and c[1] == "direct")
            ]
            for i, (actor_kind, prov_type, recorded_by_kind, source_kind) in enumerate(success_combos):
                kwargs = dict(
                    request_id=f"req_s10_ok_{i}", event="activity",
                    actor_kind=actor_kind, actor_id="x",
                    provenance_type=prov_type, recorded_by_kind=recorded_by_kind,
                    summary="s10-ok", data={"kind": "progress"},
                )
                if actor_kind == "worker":
                    kwargs["worker_run_id"] = f"wrk_s10_{i}"
                if source_kind is not None:
                    kwargs.update(
                        source_kind=source_kind, source_id="sid",
                        source_sha256="a" * 64,
                        source_observed_at="2026-09-13T00:00:00.000Z",
                        source_locator="loc",
                    )
                code, out, errtext, data = _run(_append_raw(task_path, run_id, **kwargs))
                combo = (actor_kind, prov_type, recorded_by_kind, source_kind)
                self.assertEqual(code, 0, f"S-10 허용 조합 {combo}가 실패함 — stdout={out!r} stderr={errtext!r}")
                self.assertTrue(data.get("ok"), f"S-10 허용 조합 {combo} ok:false — {data}")


# ─────────────────────────────────────────────────────────────────────────────
# S-11 — 명시적 거부 조합 4종 (AC-6/MV-3)
# ─────────────────────────────────────────────────────────────────────────────

class TestExplicitRejectionCombinations(unittest.TestCase):
    def test_four_explicit_rejections(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s11-task")
            run_id = "run_s11"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-11 선행 init 실패 — stdout={out0!r} stderr={err0!r}")
            segment = _segment_of(task_path, run_id)
            before = segment.read_bytes()

            cases = {
                "a_pm_ghostwrite": dict(
                    request_id="req_s11_a", event="activity",
                    actor_kind="worker", actor_id="w1",
                    provenance_type="direct", recorded_by_kind="PM",
                    summary="s11a", data={"kind": "progress"},
                ),
                "b_worker_direct_no_token": dict(
                    request_id="req_s11_b", event="activity",
                    actor_kind="worker", actor_id="w1",
                    provenance_type="direct", recorded_by_kind="worker",
                    summary="s11b", data={"kind": "progress"},
                ),
                "c_adapter_recorded_by_tool": dict(
                    request_id="req_s11_c", event="activity",
                    actor_kind="worker", actor_id="w1",
                    provenance_type="adapter", recorded_by_kind="tool",
                    source_kind="agent_message", source_id="sid",
                    source_sha256="a" * 64, source_observed_at="2026-09-13T00:00:00.000Z",
                    summary="s11c", data={"kind": "progress"},
                ),
                "d_import_recorded_by_adapter": dict(
                    request_id="req_s11_d", event="activity",
                    actor_kind="PM", actor_id="pm",
                    provenance_type="import", recorded_by_kind="adapter",
                    source_kind="legacy_line", source_id="sid",
                    source_sha256="a" * 64, source_locator="loc#L1",
                    summary="s11d", data={"kind": "progress"},
                ),
            }
            for label, kwargs in cases.items():
                code, out, errtext, data = _run(_append_raw(task_path, run_id, **kwargs))
                self.assertNotEqual(code, 0, f"S-11 {label}가 exit 0으로 통과함 — stdout={out!r}")
                self.assertFalse(data.get("ok", True), f"S-11 {label} ok:true — {data}")
                self.assertEqual(data.get("error", {}).get("code"), "provenance_invalid",
                                  f"S-11 {label} 오류 코드 불일치 — {data}")

            after = segment.read_bytes()
            self.assertEqual(before, after, "S-11 거부된 조합들이 조각 파일을 변경함(부분 쓰기)")


# ─────────────────────────────────────────────────────────────────────────────
# S-12 — 사건 종류별 actor 제약 전수 (AC-6/MV-2)
# ─────────────────────────────────────────────────────────────────────────────

class TestEventActorConstraintExhaustive(unittest.TestCase):
    _ACTOR_MIN_KWARGS = {
        "tool": dict(provenance_type="direct", recorded_by_kind="tool"),
        "PM": dict(provenance_type="direct", recorded_by_kind="PM"),
        "user": dict(provenance_type="direct", recorded_by_kind="PM"),
        "auto": dict(provenance_type="direct", recorded_by_kind="tool"),
        "worker": dict(
            provenance_type="adapter", recorded_by_kind="adapter",
            source_kind="agent_message", source_id="sid",
            source_sha256="a" * 64, source_observed_at="2026-09-13T00:00:00.000Z",
        ),
    }

    @staticmethod
    def _event_extra_kwargs(event, req_id, run_id):
        if event in ("worker.completed", "worker.failed", "worker.blocked", "run.completed"):
            extra = dict(duration_ms=100, duration_source="adapter_monotonic")
            if event in ("worker.failed", "worker.blocked", "run.completed"):
                extra["reason"] = f"s12-reason-{req_id}"
            return extra
        if event == "activity":
            return dict(summary=f"s12-{req_id}", data={"kind": "progress"})
        if event == "state.changed":
            return dict(data={"from": "a", "to": "b", "row_key": "k"})
        if event in ("gate.requested", "gate.resolved"):
            return dict(gate_id=f"gate_{req_id}", summary=f"s12-{req_id}")
        if event == "worker.capability.issued":
            return dict(data={
                "token_id": f"wlt_{req_id}", "token_sha256": "a" * 64,
                "scope": {"run_id": run_id, "worker_run_id": f"wrk_{req_id}",
                          "events": ["activity"], "provenance_types": ["direct"]},
                "expires_at": "2026-09-13T00:00:00.000Z",
            })
        if event == "worker.capability.revoked":
            return dict(data={"token_id": f"wlt_{req_id}", "reason": f"s12-revoke-{req_id}"})
        return {}

    def test_actor_constraint_matrix(self):
        core = _import_core()
        actor_kinds = ["worker", "PM", "user", "auto", "tool"]
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s12-task")
            run_id = "run_s12"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-12 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            pair_count = 0
            for event in sorted(core.ALLOWED_EVENTS):
                allowed_actors = set(core.EVENT_ACTOR_CONSTRAINTS.get(event, ()))
                for actor_kind in actor_kinds:
                    pair_count += 1
                    req_id = f"req_s12_{pair_count}"
                    kwargs = dict(request_id=req_id, event=event,
                                  actor_kind=actor_kind, actor_id="x")
                    kwargs.update(self._ACTOR_MIN_KWARGS[actor_kind])
                    if actor_kind == "worker":
                        kwargs["worker_run_id"] = f"wrk_{req_id}"
                    kwargs.update(self._event_extra_kwargs(event, req_id, run_id))

                    code, out, errtext, data = _run(_append_raw(task_path, run_id, **kwargs))
                    label = f"{event}/{actor_kind}"
                    if actor_kind in allowed_actors:
                        self.assertTrue(data.get("ok"), f"S-12 {label} 기대 ok:true — {data}")
                    else:
                        self.assertFalse(data.get("ok", True), f"S-12 {label} 기대 ok:false — {data}")
                        self.assertEqual(data.get("error", {}).get("code"), "provenance_invalid",
                                          f"S-12 {label} 오류 코드 불일치 — {data}")
            self.assertEqual(pair_count, 60, "S-12 전수 쌍 수가 60건이 아님(12사건×5actor)")


# ─────────────────────────────────────────────────────────────────────────────
# S-13 — adapter·import 필수 증거 결측·형식 위반 (MV-6)
# ─────────────────────────────────────────────────────────────────────────────

class TestProvenanceEvidenceViolations(unittest.TestCase):
    def test_missing_and_malformed_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s13-task")
            run_id = "run_s13"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-13 선행 init 실패 — stdout={out0!r} stderr={err0!r}")
            segment = _segment_of(task_path, run_id)
            before = segment.read_bytes()

            base_adapter = dict(
                event="activity", actor_kind="worker", actor_id="w1",
                provenance_type="adapter", recorded_by_kind="adapter",
                source_kind="agent_message", source_id="sid",
                source_sha256="a" * 64, source_observed_at="2026-09-13T00:00:00.000Z",
                summary="s13", data={"kind": "progress"},
                # actor.kind=worker이므로 worker_run_id가 별도로 필수다(PM 판정①) — 이
                # 픽스처는 출처 증거(MV-6)만 격리해 판정해야 하므로, 판정 대상이 아닌
                # 이 필드를 채워 결과가 오직 증거 결측/형식에서만 갈리게 한다.
                worker_run_id="wrk_s13_base",
            )
            base_import = dict(
                event="activity", actor_kind="PM", actor_id="pm",
                provenance_type="import", recorded_by_kind="tool",
                source_kind="legacy_line", source_id="sid",
                source_sha256="a" * 64, source_locator="loc#L1",
                summary="s13", data={"kind": "progress"},
            )

            rejects = []
            for i, missing in enumerate(["source_id", "source_sha256", "source_observed_at"]):
                kwargs = dict(base_adapter)
                kwargs.pop(missing)
                kwargs["request_id"] = f"req_s13_a{i}"
                rejects.append((f"adapter-missing-{missing}", kwargs))
            for i, missing in enumerate(["source_id", "source_sha256", "source_locator"]):
                kwargs = dict(base_import)
                kwargs.pop(missing)
                kwargs["request_id"] = f"req_s13_i{i}"
                rejects.append((f"import-missing-{missing}", kwargs))
            for i, bad_sha in enumerate(["x", "A" * 64, "b" * 63]):
                kwargs = dict(base_adapter)
                kwargs["source_sha256"] = bad_sha
                kwargs["request_id"] = f"req_s13_sha{i}"
                rejects.append((f"bad-sha256-{bad_sha!r}", kwargs))
            for i, bad_obs in enumerate(["2026-09-12", "2026-09-12T05:49:00Z"]):
                kwargs = dict(base_adapter)
                kwargs["source_observed_at"] = bad_obs
                kwargs["request_id"] = f"req_s13_obs{i}"
                rejects.append((f"bad-observed_at-{bad_obs!r}", kwargs))

            self.assertEqual(len(rejects), 11, "S-13 거부 케이스 수가 11건이 아님")
            for label, kwargs in rejects:
                code, out, errtext, data = _run(_append_raw(task_path, run_id, **kwargs))
                self.assertNotEqual(code, 0, f"S-13 {label}가 exit 0으로 통과함 — stdout={out!r}")
                self.assertFalse(data.get("ok", True), f"S-13 {label} ok:true — {data}")
                self.assertEqual(data.get("error", {}).get("code"), "provenance_invalid",
                                  f"S-13 {label} 오류 코드 불일치 — {data}")

            after = segment.read_bytes()
            self.assertEqual(before, after, "S-13 거부된 케이스들이 조각 파일을 변경함(부분 쓰기)")

            code_a, out_a, err_a, data_a = _run(
                _append_raw(task_path, run_id, request_id="req_s13_ctrl_a", **base_adapter))
            self.assertTrue(data_a.get("ok"), f"S-13 adapter 대조군 실패 — {data_a}")
            code_i, out_i, err_i, data_i = _run(
                _append_raw(task_path, run_id, request_id="req_s13_ctrl_i", **base_import))
            self.assertTrue(data_i.get("ok"), f"S-13 import 대조군 실패 — {data_i}")


# ─────────────────────────────────────────────────────────────────────────────
# S-14 — §1.2 조건부 필수 필드 위반 (AC-6/MV-1)
# ─────────────────────────────────────────────────────────────────────────────

class TestConditionalRequiredFieldViolations(unittest.TestCase):
    """원안 11건 중 (k) `timestamp`가 RFC 3339 ms가 아닌 케이스는 제외한다 —
    현재 append CLI 표면(surfaces.json)이 `--timestamp` 오버라이드를 노출하지
    않아(코어가 미채움 시 자체 발급) real-usage 원칙 하에서 재현 불가능하다.
    나머지 10건만 이 클래스가 판정한다."""

    def test_conditional_required_field_violations(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s14-task")
            run_id = "run_s14"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-14 선행 init 실패 — stdout={out0!r} stderr={err0!r}")
            segment = _segment_of(task_path, run_id)
            before = segment.read_bytes()

            base_pm = dict(actor_kind="PM", actor_id="pm",
                            provenance_type="direct", recorded_by_kind="PM")
            base_tool = dict(actor_kind="tool", actor_id="tool",
                              provenance_type="direct", recorded_by_kind="tool")
            base_worker_terminal = dict(
                actor_kind="worker", actor_id="w1",
                provenance_type="adapter", recorded_by_kind="adapter",
                source_kind="process_exit", source_id="sid",
                source_sha256="a" * 64, source_observed_at="2026-09-13T00:00:00.000Z",
                worker_run_id="wrk_s14",
            )

            cases = {
                "a_gate_requested_no_gate_id": dict(
                    base_pm, request_id="req_s14_a", event="gate.requested", summary="g"),
                "b_activity_with_gate_id": dict(
                    base_pm, request_id="req_s14_b", event="activity", summary="a",
                    data={"kind": "progress"}, gate_id="gate_x"),
                "c_activity_no_summary": dict(
                    base_pm, request_id="req_s14_c", event="activity", data={"kind": "progress"}),
                "d_activity_bad_data_kind": dict(
                    base_pm, request_id="req_s14_d", event="activity", summary="a",
                    data={"kind": "not_a_real_kind"}),
                "e_worker_failed_no_reason": dict(
                    base_worker_terminal, request_id="req_s14_e", event="worker.failed",
                    duration_ms=100, duration_source="adapter_monotonic"),
                "f_terminal_both_duration_fields": dict(
                    base_worker_terminal, request_id="req_s14_f", event="worker.completed",
                    duration_ms=100, duration_source="adapter_monotonic",
                    duration_unknown_reason="x"),
                "g_terminal_neither_duration_field": dict(
                    base_worker_terminal, request_id="req_s14_g", event="worker.completed"),
                "h_state_changed_no_row_key": dict(
                    base_tool, request_id="req_s14_h", event="state.changed",
                    data={"from": "a", "to": "b"}),
                "i_worker_no_worker_run_id": dict(
                    actor_kind="worker", actor_id="w1",
                    provenance_type="adapter", recorded_by_kind="adapter",
                    source_kind="agent_message", source_id="sid",
                    source_sha256="a" * 64, source_observed_at="2026-09-13T00:00:00.000Z",
                    request_id="req_s14_i", event="activity", summary="a",
                    data={"kind": "progress"}),
                "j_refs_absolute_path": dict(
                    base_pm, request_id="req_s14_j", event="activity", summary="a",
                    data={"kind": "progress"}, refs=["/abs/path"]),
            }

            self.assertEqual(len(cases), 10, "S-14 케이스 수가 10건이 아님")
            for label, kwargs in cases.items():
                code, out, errtext, data = _run(_append_raw(task_path, run_id, **kwargs))
                self.assertNotEqual(code, 0, f"S-14 {label}가 exit 0으로 통과함 — stdout={out!r}")
                self.assertFalse(data.get("ok", True), f"S-14 {label} ok:true — {data}")
                self.assertEqual(data.get("error", {}).get("code"), "schema_invalid",
                                  f"S-14 {label} 오류 코드 불일치(provenance_invalid 아님, D-T03-3 경계) — {data}")

            after = segment.read_bytes()
            self.assertEqual(before, after, "S-14 거부된 케이스들이 조각 파일을 변경함(부분 쓰기)")


# ─────────────────────────────────────────────────────────────────────────────
# S-15 — 동일 request_id + 동일 payload → 기존 사건 반환 (AC-7/MV-5)
# ─────────────────────────────────────────────────────────────────────────────

class TestIdempotentSamePayloadReplay(unittest.TestCase):
    def test_same_request_id_same_payload_returns_existing_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s15-task")
            run_id = "run_s15"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-15 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            args = _append_activity_args(task_path, run_id, "req_s15", "S-15 동일 payload")
            code1, out1, err1, data1 = _run(args)
            self.assertEqual(code1, 0, f"S-15 1회차 append 실패 — stdout={out1!r} stderr={err1!r}")
            self.assertTrue(data1.get("ok"), f"S-15 1회차 ok:false — {data1}")
            body1 = data1.get("data", {})

            segment = _segment_of(task_path, run_id)
            lines_after_1 = segment.read_text(encoding="utf-8").splitlines()
            bytes_after_1 = segment.read_bytes()

            code2, out2, err2, data2 = _run(args)
            self.assertEqual(code2, 0, f"S-15 2회차 append 실패 — stdout={out2!r} stderr={err2!r}")
            self.assertTrue(data2.get("ok"), f"S-15 2회차 ok:false — {data2}")
            body2 = data2.get("data", {})

            self.assertTrue(body2.get("idempotent_hit"), f"S-15 2회차 idempotent_hit!=true — {body2}")
            self.assertEqual(body2.get("event_id"), body1.get("event_id"), "S-15 event_id 불일치")
            self.assertEqual(body2.get("sequence"), body1.get("sequence"), "S-15 sequence 불일치")
            self.assertEqual(body2.get("actor_sequence"), body1.get("actor_sequence"),
                              "S-15 actor_sequence 불일치")

            lines_after_2 = segment.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines_after_2), len(lines_after_1), "S-15 2회차가 조각 줄 수를 늘림")
            self.assertEqual(segment.read_bytes(), bytes_after_1, "S-15 2회차가 조각 바이트를 변경함")

            code3, out3, err3, data3 = _run(
                ["validate-run", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code3, 0, f"S-15 validate-run 실패 — stdout={out3!r} stderr={err3!r}")
            body3 = data3.get("data", {})
            self.assertEqual(body3.get("event_count"), 1, f"S-15 event_count!=1 — {body3}")
            self.assertEqual(body3.get("verdict"), "pass", f"S-15 verdict!=pass — {body3}")


# ─────────────────────────────────────────────────────────────────────────────
# S-16 — 동일 request_id + 다른 payload → 거부 (AC-7/MV-5)
# ─────────────────────────────────────────────────────────────────────────────

class TestIdempotentConflictOnDifferentPayload(unittest.TestCase):
    def test_same_request_id_different_payload_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s16-task")
            run_id = "run_s16"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-16 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            base_args = _append_activity_args(task_path, run_id, "req_s16", "S-16 원본")
            code1, out1, err1, data1 = _run(base_args)
            self.assertEqual(code1, 0, f"S-16 1회차 append 실패 — stdout={out1!r} stderr={err1!r}")
            self.assertTrue(data1.get("ok"), f"S-16 1회차 ok:false — {data1}")

            segment = _segment_of(task_path, run_id)
            before = segment.read_bytes()

            variants = {
                "diff_summary": _append_activity_args(task_path, run_id, "req_s16", "S-16 변경된 요약"),
                "diff_data": [
                    "append", "--task", str(task_path), "--run-id", run_id,
                    "--request-id", "req_s16", "--event", "activity",
                    "--actor-kind", "PM", "--actor-id", "pm",
                    "--provenance-type", "direct", "--recorded-by-kind", "PM",
                    # D-11 — 기준 이벤트 _append_activity_args()는 --data를 넘기지 않아
                    # data=None이므로 {"kind":"progress"} 하나만으로도 digest가 달라진다.
                    # 즉 이 variant가 "data 축의 차이"로 충돌을 유발하는 lever는 그대로
                    # 보존되며, PM activity payload 폐쇄(CONTRACT §1.3)도 준수한다.
                    "--summary", "S-16 원본", "--data", '{"kind":"progress"}',
                    "--format", "json",
                ],
                "diff_stage": [
                    "append", "--task", str(task_path), "--run-id", run_id,
                    "--request-id", "req_s16", "--event", "activity",
                    "--actor-kind", "PM", "--actor-id", "pm",
                    "--provenance-type", "direct", "--recorded-by-kind", "PM",
                    "--summary", "S-16 원본", "--stage", "s16-stage",
                    "--format", "json",
                ],
            }
            for label, args in variants.items():
                code, out, errtext, data = _run(args)
                self.assertNotEqual(code, 0, f"S-16 {label}가 exit 0으로 통과함 — stdout={out!r}")
                self.assertFalse(data.get("ok", True), f"S-16 {label} ok:true — {data}")
                self.assertEqual(data.get("error", {}).get("code"), "request_id_conflict",
                                  f"S-16 {label} 오류 코드 불일치 — {data}")

            self.assertEqual(segment.read_bytes(), before, "S-16 거부된 재사용이 조각 파일을 변경함")


# ─────────────────────────────────────────────────────────────────────────────
# S-17 — 정규화가 키 순서·발급 필드에 불변 (AC-7/MV-5)
# ─────────────────────────────────────────────────────────────────────────────

class TestIdempotentNormalizationInvariance(unittest.TestCase):
    def test_digest_ignores_key_order_and_issued_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s17-task")
            run_id = "run_s17"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-17 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            # D-12 — 이 시나리오의 축("정규화가 키 순서·발급 필드에 불변")은 다중 키
            # data가 있어야 성립한다. PM activity의 data는 CONTRACT §1.3 폐쇄로
            # {"kind"} 단일 키라 키 순서 축 자체가 소멸하므로, 같은 축을 실제 생산
            # payload로 유지할 수 있는 조합 A7(tool/direct/tool/null)의 state.changed로
            # 옮긴다 — from/to/row_key 3키가 §1.2 필수이고, 폐쇄 조문의 적용 조건(A4)
            # 밖이다. 발급 필드(event_id/sequence/timestamp) 불변 축은 actor와 무관해
            # 그대로 보존된다.
            def _args(data_json):
                return [
                    "append", "--task", str(task_path), "--run-id", run_id,
                    "--request-id", "req_s17", "--event", "state.changed",
                    "--actor-kind", "tool", "--actor-id", "state-tool",
                    "--provenance-type", "direct", "--recorded-by-kind", "tool",
                    "--summary", "S-17", "--data", data_json,
                    "--format", "json",
                ]

            code1, out1, err1, data1 = _run(
                _args('{"from":"pending","to":"in_progress","row_key":"plan.plan"}'))
            self.assertEqual(code1, 0, f"S-17 1회차 실패 — stdout={out1!r} stderr={err1!r}")
            self.assertTrue(data1.get("ok"), f"S-17 1회차 ok:false — {data1}")
            event_id_1 = data1.get("data", {}).get("event_id")

            # 같은 3키를 다른 순서로 직렬화 — 키 순서 불변 축.
            code2, out2, err2, data2 = _run(
                _args('{"row_key":"plan.plan","to":"in_progress","from":"pending"}'))
            self.assertEqual(code2, 0, f"S-17 키순서변경 재호출 실패 — stdout={out2!r} stderr={err2!r}")
            body2 = data2.get("data", {})
            self.assertTrue(body2.get("idempotent_hit"), f"S-17 키순서변경 idempotent_hit!=true — {body2}")
            self.assertEqual(body2.get("event_id"), event_id_1, "S-17 키순서변경 후 event_id 불일치")

            time.sleep(1.1)
            code3, out3, err3, data3 = _run(
                _args('{"from":"pending","to":"in_progress","row_key":"plan.plan"}'))
            self.assertEqual(code3, 0, f"S-17 시간간격 재호출 실패 — stdout={out3!r} stderr={err3!r}")
            body3 = data3.get("data", {})
            self.assertTrue(body3.get("idempotent_hit"), f"S-17 시간간격 재호출 idempotent_hit!=true — {body3}")
            self.assertEqual(body3.get("event_id"), event_id_1, "S-17 시간간격 재호출 후 event_id 불일치")


# ─────────────────────────────────────────────────────────────────────────────
# S-18 — 16 KiB 직렬화 상한 (§1.1/AC-6)
# ─────────────────────────────────────────────────────────────────────────────

class TestSerializationSizeCap(unittest.TestCase):
    def test_16kib_cap_enforced_without_consuming_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s18-task")
            run_id = "run_s18"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-18 선행 init 실패 — stdout={out0!r} stderr={err0!r}")
            segment = _segment_of(task_path, run_id)
            before = segment.read_bytes()

            def _args(request_id, summary):
                return [
                    "append", "--task", str(task_path), "--run-id", run_id,
                    "--request-id", request_id, "--event", "activity",
                    "--actor-kind", "PM", "--actor-id", "pm",
                    "--provenance-type", "direct", "--recorded-by-kind", "PM",
                    "--summary", summary, "--data", '{"kind":"progress"}',
                    "--format", "json",
                ]

            code_a, out_a, err_a, data_a = _run(_args("req_s18_a", "x" * 20000))
            self.assertNotEqual(code_a, 0, f"S-18(a) 상한 초과가 exit 0으로 통과함 — stdout={out_a!r}")
            self.assertFalse(data_a.get("ok", True), f"S-18(a) ok:true — {data_a}")
            self.assertEqual(data_a.get("error", {}).get("code"), "event_too_large",
                              f"S-18(a) 오류 코드 불일치 — {data_a}")
            self.assertEqual(segment.read_bytes(), before, "S-18(a) 거부됐는데 조각 파일이 변경됨")

            code_b, out_b, err_b, data_b = _run(_args("req_s18_b", "x" * 100))
            self.assertEqual(code_b, 0, f"S-18(b) 실패 — stdout={out_b!r} stderr={err_b!r}")
            self.assertTrue(data_b.get("ok"), f"S-18(b) ok:false — {data_b}")
            self.assertEqual(data_b.get("data", {}).get("sequence"), 1,
                              f"S-18(b) 거부 직후 sequence가 건너뜀 — {data_b}")
            lines_after_b = segment.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines_after_b), 1, "S-18(b) 조각 줄 수가 정확히 1이 아님")

            before_c = segment.read_bytes()
            code_c, out_c, err_c, data_c = _run(_args("req_s18_c", "가" * 6000))
            self.assertNotEqual(code_c, 0, f"S-18(c) 상한 초과(한글)가 exit 0으로 통과함 — stdout={out_c!r}")
            self.assertFalse(data_c.get("ok", True), f"S-18(c) ok:true — {data_c}")
            self.assertEqual(data_c.get("error", {}).get("code"), "event_too_large",
                              f"S-18(c) 오류 코드 불일치 — {data_c}")
            self.assertEqual(segment.read_bytes(), before_c, "S-18(c) 거부됐는데 조각 파일이 변경됨")


# ─────────────────────────────────────────────────────────────────────────────
# S-19 — actor_sequence 범위 — worker는 worker_run_id (MV-10)
# ─────────────────────────────────────────────────────────────────────────────

class TestActorSequenceWorkerRunIdScope(unittest.TestCase):
    def test_actor_sequence_scoped_by_worker_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s19-task")
            run_id = "run_s19"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-19 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            def _worker_args(req_id, worker_run_id):
                return _append_raw(
                    task_path, run_id, request_id=req_id, event="activity",
                    actor_kind="worker", actor_id="w1",
                    provenance_type="adapter", recorded_by_kind="adapter",
                    source_kind="agent_message", source_id="sid",
                    source_sha256="a" * 64, source_observed_at="2026-09-13T00:00:00.000Z",
                    worker_run_id=worker_run_id, summary="s19", data={"kind": "progress"})

            responses = {}
            order = [("wrk_a", 2), ("wrk_b", 2), ("wrk_a", 1)]
            i = 0
            for worker_run_id, count in order:
                for _ in range(count):
                    i += 1
                    req_id = f"req_s19_{i}"
                    code, out, errtext, data = _run(_worker_args(req_id, worker_run_id))
                    self.assertEqual(code, 0, f"S-19 worker append #{i} 실패 — stdout={out!r} stderr={errtext!r}")
                    self.assertTrue(data.get("ok"), f"S-19 worker append #{i} ok:false — {data}")
                    responses.setdefault(worker_run_id, []).append(data.get("data", {}))

            for _ in range(2):
                i += 1
                req_id = f"req_s19_{i}"
                code, out, errtext, data = _run(_append_activity_args(task_path, run_id, req_id, "s19-pm"))
                self.assertEqual(code, 0, f"S-19 PM append #{i} 실패 — stdout={out!r} stderr={errtext!r}")
                responses.setdefault("PM", []).append(data.get("data", {}))

            self.assertEqual([r.get("actor_sequence") for r in responses["wrk_a"]], [1, 2, 3],
                              f"S-19 wrk_a actor_sequence 불일치 — {responses['wrk_a']}")
            self.assertEqual([r.get("actor_sequence") for r in responses["wrk_b"]], [1, 2],
                              f"S-19 wrk_b actor_sequence 불일치 — {responses['wrk_b']}")
            self.assertEqual([r.get("actor_sequence") for r in responses["PM"]], [1, 2],
                              f"S-19 PM actor_sequence 불일치 — {responses['PM']}")

            all_sequences = sorted(r.get("sequence") for rs in responses.values() for r in rs)
            self.assertEqual(all_sequences, list(range(1, 8)),
                              f"S-19 전역 sequence가 1..7 단조가 아님 — {all_sequences}")

            segment = _segment_of(task_path, run_id)
            records = [json.loads(l) for l in segment.read_text(encoding="utf-8").splitlines()]
            wrk_a_actor_seqs = [r["actor_sequence"] for r in records if r.get("worker_run_id") == "wrk_a"]
            self.assertEqual(wrk_a_actor_seqs, [1, 2, 3], f"S-19 조각 재확인 wrk_a 불일치 — {wrk_a_actor_seqs}")


# ─────────────────────────────────────────────────────────────────────────────
# S-20 — sequence run 전역 단조·무중복·무누락 (MV-10, red_required=false)
# ─────────────────────────────────────────────────────────────────────────────

class TestSequenceGlobalMonotonic(unittest.TestCase):
    def test_sequence_monotonic_across_actors(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s20-task")
            run_id = "run_s20"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-20 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            actors = [
                dict(actor_kind="PM", actor_id="pm", provenance_type="direct", recorded_by_kind="PM"),
                dict(actor_kind="auto", actor_id="scheduler", provenance_type="direct", recorded_by_kind="tool"),
                dict(actor_kind="tool", actor_id="run-log-tool", provenance_type="direct", recorded_by_kind="tool"),
            ]
            for i in range(12):
                actor = actors[i % 3]
                req_id = f"req_s20_{i}"
                code, out, errtext, data = _run(_append_raw(
                    task_path, run_id, request_id=req_id, event="activity",
                    summary=f"s20-{i}", data={"kind": "progress"}, **actor))
                self.assertEqual(code, 0, f"S-20 append #{i} 실패 — stdout={out!r} stderr={errtext!r}")
                self.assertTrue(data.get("ok"), f"S-20 append #{i} ok:false — {data}")
                self.assertEqual(data.get("data", {}).get("sequence"), i + 1,
                                  f"S-20 sequence가 1..12 단조가 아님 — {data}")

            code, out, errtext, data = _run(
                ["validate-run", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code, 0, f"S-20 validate-run 실패 — stdout={out!r} stderr={errtext!r}")
            body = data.get("data", {})
            self.assertEqual(body.get("verdict"), "pass", f"S-20 verdict!=pass — {body}")
            self.assertEqual(body.get("event_count"), 12, f"S-20 event_count!=12 — {body}")
            self.assertEqual(body.get("sequence_gaps"), [], f"S-20 sequence_gaps 비어있지 않음 — {body}")
            self.assertEqual(body.get("violations"), [], f"S-20 violations 비어있지 않음 — {body}")

            segment = _segment_of(task_path, run_id)
            records = [json.loads(l) for l in segment.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(sorted(r["sequence"] for r in records), list(range(1, 13)),
                              "S-20 조각 파싱 sequence 집합이 {1..12}와 불일치")


# ─────────────────────────────────────────────────────────────────────────────
# S-21 — legacy 가져오기 멱등 (AC-15/MV-19)
# ─────────────────────────────────────────────────────────────────────────────

class TestLegacyImportIdempotent(unittest.TestCase):
    def test_import_agentic_idempotent(self):
        self.assertTrue(_SAMPLE_AGENTIC_LOG.exists(), f"S-21 샘플 AGENTIC-LOG.md 부재: {_SAMPLE_AGENTIC_LOG}")
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s21-task")
            run_id = "run_s21"
            (task_path / "AGENTIC-LOG.md").write_text(
                _SAMPLE_AGENTIC_LOG.read_text(encoding="utf-8"), encoding="utf-8")

            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-21 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            args = ["import-agentic", "--task", str(task_path), "--run-id", run_id, "--format", "json"]
            code1, out1, err1, data1 = _run(args)
            self.assertEqual(code1, 0, f"S-21 1회차 import-agentic 실패 — stdout={out1!r} stderr={err1!r}")
            self.assertTrue(data1.get("ok"), f"S-21 1회차 ok:false — {data1}")
            body1 = data1.get("data", {})
            self.assertEqual(body1.get("scanned"), body1.get("imported"),
                              f"S-21 1회차 scanned!=imported — {body1}")
            self.assertEqual(body1.get("skipped_idempotent"), 0, f"S-21 1회차 skipped_idempotent!=0 — {body1}")
            self.assertGreater(body1.get("imported", 0), 0, f"S-21 1회차 imported<=0 — {body1}")

            segment = _segment_of(task_path, run_id)
            lines_after_1 = len(segment.read_text(encoding="utf-8").splitlines())

            code2, out2, err2, data2 = _run(args)
            self.assertEqual(code2, 0, f"S-21 2회차 import-agentic 실패 — stdout={out2!r} stderr={err2!r}")
            body2 = data2.get("data", {})
            self.assertEqual(body2.get("imported"), 0, f"S-21 2회차 imported!=0 — {body2}")
            self.assertEqual(body2.get("skipped_idempotent"), body1.get("imported"),
                              f"S-21 2회차 skipped_idempotent!=1회차 imported — {body2}")
            self.assertEqual(body2.get("scanned"), body1.get("scanned"), "S-21 2회차 scanned 불일치")

            lines_after_2 = len(segment.read_text(encoding="utf-8").splitlines())
            self.assertEqual(lines_after_2, lines_after_1, "S-21 2회차가 조각 줄 수를 늘림")

            code3, out3, err3, data3 = _run(
                ["validate-run", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code3, 0, f"S-21 validate-run 실패 — stdout={out3!r} stderr={err3!r}")
            self.assertEqual(data3.get("data", {}).get("verdict"), "pass", f"S-21 verdict!=pass — {data3}")


# ─────────────────────────────────────────────────────────────────────────────
# S-22 — legacy 구조 변종 식별과 정규화 (AC-15)
# ─────────────────────────────────────────────────────────────────────────────

class TestLegacyStructuralVariantNormalization(unittest.TestCase):
    def test_only_header_matched_v1_rows_with_valid_timestamps_are_imported(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s22-task")
            run_id = "run_s22"
            (task_path / "AGENTIC-LOG.md").write_text(_S22_MIXED_LOG, encoding="utf-8")

            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-22 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            code, out, errtext, data = _run(
                ["import-agentic", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code, 0, f"S-22 import-agentic 실패 — stdout={out!r} stderr={errtext!r}")
            body = data.get("data", {})
            self.assertEqual(body.get("scanned"), 4, f"S-22 scanned!=4 — {body}")
            self.assertEqual(body.get("imported"), 4, f"S-22 imported!=4 — {body}")

            segment = _segment_of(task_path, run_id)
            records = [json.loads(l) for l in segment.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 4, f"S-22 조각에 4건이 기록되지 않음 — {len(records)}건")

            for rec in records:
                self.assertEqual(rec.get("event"), "activity", f"S-22 event!=activity — {rec}")
                self.assertEqual(rec.get("actor", {}).get("kind"), "PM", f"S-22 actor.kind!=PM — {rec}")
                self.assertEqual(rec.get("provenance", {}).get("type"), "import",
                                  f"S-22 provenance.type!=import — {rec}")
                self.assertEqual(rec.get("provenance", {}).get("recorded_by", {}).get("kind"), "tool",
                                  f"S-22 recorded_by.kind!=tool — {rec}")
                self.assertEqual(rec.get("provenance", {}).get("source", {}).get("kind"), "legacy_line",
                                  f"S-22 source.kind!=legacy_line — {rec}")
                self.assertIn(rec.get("data", {}).get("kind"), ["progress", "decision", "validation", "retry"],
                              f"S-22 data.kind가 4종 밖 — {rec}")
                self.assertRegex(rec.get("provenance", {}).get("source", {}).get("locator", ""),
                                  r"^AGENTIC-LOG\.md#L\d+$", f"S-22 locator 형식 불일치 — {rec}")

            locators = {r["provenance"]["source"]["locator"] for r in records}
            self.assertEqual(len(locators), 4, "S-22 locator가 4건 서로 다르지 않음")

            first = next(r for r in records if r.get("data", {}).get("kind") == "decision")
            self.assertEqual(first.get("timestamp"), "2026-09-12T05:49:00.000Z",
                              f"S-22 KST→UTC 변환 불일치 — {first}")

            forbidden_events = {"worker.started", "worker.completed", "worker.failed", "worker.blocked",
                                 "gate.requested", "gate.resolved", "run.started", "run.completed",
                                 "state.changed"}
            for rec in records:
                self.assertNotIn(rec.get("event"), forbidden_events,
                                  f"S-22 worker/gate/run/state.changed 사건이 생성됨 — {rec}")


# ─────────────────────────────────────────────────────────────────────────────
# S-23 — oppl 이원 구조 정규화와 비수집 경계 (AC-15/AC-14)
# ─────────────────────────────────────────────────────────────────────────────

class TestOpplDualStructureNormalization(unittest.TestCase):
    def test_oppl_import_normalizes_and_excludes_raw_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s23-task")
            run_id = "run_s23"
            oppl_dir = task_path / ".oppl-run"
            oppl_dir.mkdir()

            journal = (
                "# journal\n\n"
                "| 시각 | 단계 | 이벤트 | 근거 |\n"
                "|---|---|---|---|\n"
                "| 2026-09-13T00:00:00.000Z | T1 | start | s23 시작 |\n"
                "| 2026-09-13T00:05:00.000Z | T1 | gate-verdict | s23 게이트 |\n"
                "| 2026-09-13T00:06:00.000Z | T1 | retry | s23 재시도 |\n"
                "| 2026-09-13T00:10:00.000Z | T1 | end | s23 종료 |\n"
            )
            (oppl_dir / "journal.md").write_text(journal, encoding="utf-8")

            result_uuid = "s23-result-uuid-0001"
            events_lines = [
                json.dumps({"type": "system", "uuid": "s23-sys-1"}),
                json.dumps({"type": "assistant", "uuid": "s23-asst-1",
                            "timestamp": "2026-09-13T00:01:00.000Z"}),
                json.dumps({"type": "user", "uuid": "s23-user-1",
                            "timestamp": "2026-09-13T00:02:00.000Z"}),
                json.dumps({"type": "tool_progress", "uuid": "s23-tp-1"}),
                json.dumps({"type": "rate_limit_event", "uuid": "s23-rl-1"}),
                json.dumps({"type": "result", "uuid": result_uuid, "subtype": "success",
                            "is_error": False, "duration_ms": 4200, "num_turns": 3,
                            "session_id": "s23-session"}),
            ]
            (oppl_dir / "t1.events.jsonl").write_text("\n".join(events_lines) + "\n", encoding="utf-8")
            (oppl_dir / "t1.exitcode").write_text("0\n", encoding="utf-8")
            (oppl_dir / "t1.prompt.txt").write_text("S23-SECRET-PROMPT-비수집대상", encoding="utf-8")
            (oppl_dir / "t1.err.log").write_text("s23 stderr 비수집대상", encoding="utf-8")

            (oppl_dir / "t4a.result.json").write_text(json.dumps({
                "type": "result", "subtype": "success", "is_error": False,
                "duration_ms": 9900, "num_turns": 5, "session_id": "s23-sync-session",
                "uuid": "s23-sync-uuid", "exitcode": 0,
            }), encoding="utf-8")

            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-23 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            code, out, errtext, data = _run(
                ["import-oppl", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code, 0, f"S-23 import-oppl 실패 — stdout={out!r} stderr={errtext!r}")
            body = data.get("data", {})
            self.assertEqual(body.get("imported"), 6, f"S-23 imported!=6 — {body}")

            sources = body.get("sources", [])
            source_paths = {s.get("path") for s in sources}
            self.assertIn(".oppl-run/journal.md", source_paths, f"S-23 sources에 journal.md 없음 — {sources}")
            self.assertIn(".oppl-run/t1.events.jsonl", source_paths,
                          f"S-23 sources에 t1.events.jsonl 없음 — {sources}")
            self.assertIn(".oppl-run/t4a.result.json", source_paths,
                          f"S-23 sources에 t4a.result.json 없음 — {sources}")
            self.assertNotIn(".oppl-run/t1.prompt.txt", source_paths, "S-23 t1.prompt.txt가 sources에 포함됨")
            self.assertNotIn(".oppl-run/t1.err.log", source_paths, "S-23 t1.err.log가 sources에 포함됨")
            for s in sources:
                self.assertIn("sha256", s, f"S-23 sources 항목에 sha256 없음 — {s}")
                self.assertIn("scanned", s, f"S-23 sources 항목에 scanned 없음 — {s}")

            segment = _segment_of(task_path, run_id)
            raw_text = segment.read_text(encoding="utf-8")
            self.assertNotIn("S23-SECRET-PROMPT", raw_text, "S-23 프롬프트 원문 문자열이 조각에 유출됨")

            records = [json.loads(l) for l in raw_text.splitlines()]
            self.assertEqual(len(records), 6, f"S-23 조각에 6건이 기록되지 않음 — {len(records)}건")
            for rec in records:
                self.assertEqual(rec.get("event"), "activity", f"S-23 event!=activity — {rec}")
                self.assertEqual(rec.get("actor", {}).get("kind"), "PM", f"S-23 actor.kind!=PM — {rec}")
                self.assertEqual(rec.get("provenance", {}).get("type"), "import",
                                  f"S-23 provenance.type!=import — {rec}")
                self.assertEqual(rec.get("provenance", {}).get("recorded_by", {}).get("kind"), "tool",
                                  f"S-23 recorded_by.kind!=tool — {rec}")
                self.assertEqual(rec.get("provenance", {}).get("source", {}).get("kind"), "oppl_event",
                                  f"S-23 source.kind!=oppl_event — {rec}")

            result_rec = next(
                (r for r in records
                 if r.get("provenance", {}).get("source", {}).get("upstream_event_id") == result_uuid), None)
            self.assertIsNotNone(result_rec, f"S-23 stream result 레코드 기반 사건 없음 — {records}")
            self.assertEqual(result_rec.get("data", {}).get("duration_ms"), 4200,
                              f"S-23 result duration_ms 불일치 — {result_rec}")
            self.assertEqual(result_rec.get("data", {}).get("is_error"), False,
                              f"S-23 result is_error 불일치 — {result_rec}")
            self.assertEqual(result_rec.get("data", {}).get("subtype"), "success",
                              f"S-23 result subtype 불일치 — {result_rec}")

            journal_recs = [r for r in records
                            if r.get("provenance", {}).get("source", {}).get("upstream_event_id") is None]
            self.assertEqual(len(journal_recs), 4, f"S-23 journal 유래 사건이 4건이 아님 — {len(journal_recs)}건")
            for rec in journal_recs:
                self.assertRegex(rec.get("provenance", {}).get("source", {}).get("locator", ""),
                                  r"journal\.md#L\d+$", f"S-23 journal locator 형식 불일치 — {rec}")


# ─────────────────────────────────────────────────────────────────────────────
# S-24 — oppl 가져오기 멱등 (AC-15/MV-19)
# ─────────────────────────────────────────────────────────────────────────────

class TestOpplImportIdempotent(unittest.TestCase):
    def test_oppl_import_idempotent_and_incremental(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s24-task")
            run_id = "run_s24"
            oppl_dir = task_path / ".oppl-run"
            oppl_dir.mkdir()
            journal = (
                "# journal\n\n"
                "| 시각 | 단계 | 이벤트 | 근거 |\n"
                "|---|---|---|---|\n"
                "| 2026-09-13T00:00:00.000Z | T1 | start | s24 시작 |\n"
                "| 2026-09-13T00:10:00.000Z | T1 | end | s24 종료 |\n"
            )
            (oppl_dir / "journal.md").write_text(journal, encoding="utf-8")

            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-24 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            args = ["import-oppl", "--task", str(task_path), "--run-id", run_id, "--format", "json"]
            code1, out1, err1, data1 = _run(args)
            self.assertEqual(code1, 0, f"S-24 1회차 import-oppl 실패 — stdout={out1!r} stderr={err1!r}")
            body1 = data1.get("data", {})
            self.assertEqual(body1.get("imported"), 2, f"S-24 1회차 imported!=2 — {body1}")

            segment = _segment_of(task_path, run_id)
            lines_after_1 = len(segment.read_text(encoding="utf-8").splitlines())

            code2, out2, err2, data2 = _run(args)
            self.assertEqual(code2, 0, f"S-24 2회차 import-oppl 실패 — stdout={out2!r} stderr={err2!r}")
            body2 = data2.get("data", {})
            self.assertEqual(body2.get("imported"), 0, f"S-24 2회차 imported!=0 — {body2}")
            self.assertEqual(body2.get("skipped_idempotent"), 2, f"S-24 2회차 skipped_idempotent!=2 — {body2}")
            self.assertEqual(body2.get("scanned"), 2, f"S-24 2회차 scanned!=2 — {body2}")
            self.assertEqual(len(segment.read_text(encoding="utf-8").splitlines()), lines_after_1,
                              "S-24 2회차가 조각 줄 수를 늘림")

            with (oppl_dir / "journal.md").open("a", encoding="utf-8") as f:
                f.write("| 2026-09-13T00:20:00.000Z | T1 | retry | s24 추가 행 |\n")

            code3, out3, err3, data3 = _run(args)
            self.assertEqual(code3, 0, f"S-24 3회차 import-oppl 실패 — stdout={out3!r} stderr={err3!r}")
            body3 = data3.get("data", {})
            self.assertEqual(body3.get("imported"), 1, f"S-24 3회차 imported!=1 — {body3}")
            self.assertEqual(body3.get("skipped_idempotent"), 2, f"S-24 3회차 skipped_idempotent!=2 — {body3}")


# ─────────────────────────────────────────────────────────────────────────────
# S-25 — --dry-run 무쓰기 (AC-15)
# ─────────────────────────────────────────────────────────────────────────────

class TestDryRunNoWrite(unittest.TestCase):
    def test_dry_run_makes_no_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s25-task")
            run_id = "run_s25"
            oppl_dir = task_path / ".oppl-run"
            oppl_dir.mkdir()
            journal = (
                "# journal\n\n"
                "| 시각 | 단계 | 이벤트 | 근거 |\n"
                "|---|---|---|---|\n"
                "| 2026-09-13T00:00:00.000Z | T1 | start | s25 |\n"
                "| 2026-09-13T00:10:00.000Z | T1 | end | s25 |\n"
            )
            (oppl_dir / "journal.md").write_text(journal, encoding="utf-8")
            (task_path / "AGENTIC-LOG.md").write_text(
                _SAMPLE_AGENTIC_LOG.read_text(encoding="utf-8"), encoding="utf-8")

            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-25 선행 init 실패 — stdout={out0!r} stderr={err0!r}")
            segment = _segment_of(task_path, run_id)
            before = segment.read_bytes()

            code1, out1, err1, data1 = _run(
                ["import-oppl", "--task", str(task_path), "--run-id", run_id, "--dry-run", "--format", "json"])
            self.assertEqual(code1, 0, f"S-25 import-oppl --dry-run 실패 — stdout={out1!r} stderr={err1!r}")
            self.assertTrue(data1.get("ok"), f"S-25 import-oppl --dry-run ok:false — {data1}")
            self.assertEqual(data1.get("data", {}).get("imported"), 2, f"S-25 oppl imported 불일치 — {data1}")

            code2, out2, err2, data2 = _run(
                ["import-agentic", "--task", str(task_path), "--run-id", run_id, "--dry-run", "--format", "json"])
            self.assertEqual(code2, 0, f"S-25 import-agentic --dry-run 실패 — stdout={out2!r} stderr={err2!r}")
            self.assertTrue(data2.get("ok"), f"S-25 import-agentic --dry-run ok:false — {data2}")
            self.assertGreater(data2.get("data", {}).get("imported", 0), 0, f"S-25 agentic imported<=0 — {data2}")

            self.assertEqual(segment.read_bytes(), before, "S-25 --dry-run이 조각 파일을 변경함")

            code3, out3, err3, data3 = _run(
                ["validate-run", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code3, 0, f"S-25 validate-run 실패 — stdout={out3!r} stderr={err3!r}")
            self.assertEqual(data3.get("data", {}).get("event_count"), 0, f"S-25 event_count!=0 — {data3}")


# ─────────────────────────────────────────────────────────────────────────────
# S-26 — --run-id 해석과 모호성 거부 (AC-15/§3.2)
# ─────────────────────────────────────────────────────────────────────────────

class TestRunIdResolutionAmbiguity(unittest.TestCase):
    def test_run_id_omitted_resolution_and_ambiguity(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)

            task_a = _abs_task_dir(tmp, "s26a-task")
            (task_a / "AGENTIC-LOG.md").write_text(
                _SAMPLE_AGENTIC_LOG.read_text(encoding="utf-8"), encoding="utf-8")
            code_a, out_a, err_a, data_a = _run(
                ["import-agentic", "--task", str(task_a), "--format", "json"])
            self.assertNotEqual(code_a, 0, f"S-26(a) 조각 0개인데 exit 0 — stdout={out_a!r}")
            self.assertEqual(data_a.get("error", {}).get("code"), "run_log_missing",
                              f"S-26(a) 오류 코드 불일치 — {data_a}")

            task_b = _abs_task_dir(tmp, "s26b-task")
            (task_b / "AGENTIC-LOG.md").write_text(
                _SAMPLE_AGENTIC_LOG.read_text(encoding="utf-8"), encoding="utf-8")
            code_b0, out_b0, err_b0, _ = _run(
                ["init", "--task", str(task_b), "--run-id", "run_x", "--format", "json"])
            self.assertEqual(code_b0, 0, f"S-26(b) 선행 init 실패 — stdout={out_b0!r}")
            code_b, out_b, err_b, data_b = _run(
                ["import-agentic", "--task", str(task_b), "--format", "json"])
            self.assertEqual(code_b, 0, f"S-26(b) 실패 — stdout={out_b!r} stderr={err_b!r}")
            self.assertTrue(data_b.get("ok"), f"S-26(b) ok:false — {data_b}")
            segment_x = _segment_of(task_b, "run_x")
            self.assertGreater(len(segment_x.read_text(encoding="utf-8").splitlines()), 0,
                                "S-26(b) run_x 조각에 사건이 붙지 않음")

            task_c = _abs_task_dir(tmp, "s26c-task")
            (task_c / "AGENTIC-LOG.md").write_text(
                _SAMPLE_AGENTIC_LOG.read_text(encoding="utf-8"), encoding="utf-8")
            code_c0a, _, _, _ = _run(["init", "--task", str(task_c), "--run-id", "run_x", "--format", "json"])
            code_c0b, _, _, _ = _run(["init", "--task", str(task_c), "--run-id", "run_y", "--format", "json"])
            self.assertEqual((code_c0a, code_c0b), (0, 0), "S-26(c) 선행 init 2회 실패")

            code_c, out_c, err_c, data_c = _run(
                ["import-agentic", "--task", str(task_c), "--format", "json"])
            self.assertNotEqual(code_c, 0, f"S-26(c) 모호한데 exit 0 — stdout={out_c!r}")
            self.assertEqual(data_c.get("error", {}).get("code"), "schema_invalid",
                              f"S-26(c) 오류 코드 불일치 — {data_c}")
            combined_msg = str(data_c.get("error", {}).get("message", "")) + str(
                data_c.get("error", {}).get("detail", ""))
            self.assertIn("--run-id", combined_msg, f"S-26(c) 오류 메시지에 --run-id 안내 없음 — {data_c}")

            code_c2, out_c2, err_c2, data_c2 = _run(
                ["import-agentic", "--task", str(task_c), "--run-id", "run_y", "--format", "json"])
            self.assertEqual(code_c2, 0, f"S-26(c) --run-id 명시 후 실패 — stdout={out_c2!r} stderr={err_c2!r}")
            segment_y = _segment_of(task_c, "run_y")
            segment_x2 = _segment_of(task_c, "run_x")
            self.assertGreater(len(segment_y.read_text(encoding="utf-8").splitlines()), 0,
                                "S-26(c) run_y 조각에 사건이 붙지 않음")
            self.assertEqual(len(segment_x2.read_text(encoding="utf-8").splitlines()), 0,
                              "S-26(c) run_x 조각에 잘못 붙음")

            rel_dir = tmp_path / "s26-rel"
            rel_dir.mkdir()
            for cmd in ("import-agentic", "import-oppl"):
                code_r, out_r, err_r, data_r = _run(
                    [cmd, "--task", "./s26-rel", "--format", "json"], cwd=str(tmp_path))
                self.assertNotEqual(code_r, 0, f"S-26 {cmd} 상대경로가 통과함 — stdout={out_r!r}")
                self.assertEqual(data_r.get("error", {}).get("code"), "task_path_not_absolute",
                                  f"S-26 {cmd} 오류 코드 불일치 — {data_r}")


# ─────────────────────────────────────────────────────────────────────────────
# S-27 — 기록 도구 state 자산 독립 유지 확장 (AC-19/MV-24, red_required=false)
# ─────────────────────────────────────────────────────────────────────────────

class TestStateAssetIndependenceExtended(unittest.TestCase):
    def test_five_command_lifecycle_creates_no_state_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            task_path = _abs_task_dir(tmp, "s27-task")
            run_id = "run_s27"

            code1, out1, err1, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code1, 0, f"S-27 init 실패 — stdout={out1!r} stderr={err1!r}")

            code2, out2, err2, _ = _run(_append_activity_args(task_path, run_id, "req_s27", "S-27"))
            self.assertEqual(code2, 0, f"S-27 append 실패 — stdout={out2!r} stderr={err2!r}")

            for cmd in ("import-agentic", "import-oppl"):
                code, out, errtext, data = _run(
                    [cmd, "--task", str(task_path), "--run-id", run_id, "--format", "json"])
                if code != 0:
                    self.assertEqual(data.get("error", {}).get("code"), "run_log_missing",
                                      f"S-27 {cmd} 원본 부재 외 오류 — {data}")

            code5, out5, err5, _ = _run(
                ["validate-run", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code5, 0, f"S-27 validate-run 실패 — stdout={out5!r} stderr={err5!r}")

            state_files = list(tmp_path.rglob("state.json"))
            self.assertEqual(state_files, [], f"S-27 state.json이 생성됨 — {state_files}")

    def test_source_has_no_state_tool_coupling_extended(self):
        """T03 신규 코드 범위까지 정적 판정 확장 (기존 S-8b와 동일 검사)"""
        for src_path in (_CORE_SRC, _CLI_SRC):
            text = src_path.read_text(encoding="utf-8")
            self.assertNotIn("state_tool", text, f"S-27 {src_path.name}에 state_tool 결합 문자열 발견")
            self.assertNotIn("state.json", text, f"S-27 {src_path.name}에 state.json 문자열 발견")


# ─────────────────────────────────────────────────────────────────────────────
# S-28 — 기존 회귀 무손상 (C-2/AC-20, red_required=false)
# ─────────────────────────────────────────────────────────────────────────────

class TestExistingRegressionSuiteUnaffected(unittest.TestCase):
    def test_run_log_tool_original_eight_pass(self):
        """기존 S-3~S-8 6클래스 8메서드만 in-process 서브스위트로 재실행한다.
        subprocess로 파일 전체를 재-discover하면 이 클래스 자신을 다시 실행해
        무한 재귀에 빠지므로 의도적으로 원본 클래스만 직접 선택한다."""
        original_classes = [
            TestInitIdempotent, TestAppendEvent, TestValidateRunPass,
            TestPathContractRejection, TestSchemaRejection, TestStateAssetIndependence,
        ]
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        for cls in original_classes:
            suite.addTests(loader.loadTestsFromTestCase(cls))
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
        self.assertTrue(result.wasSuccessful(),
                          f"S-28 기존 8건 회귀 실패 — failures={result.failures} errors={result.errors}")

    def test_state_tool_regression_baseline(self):
        """PLAN.md 원안은 이 수치를 "428 passed"로 적었으나, T05가 state-tool 테스트를
        확장한 이후의 판정은 실패 0건·종료 코드 0이다(통과 개수는 형제 태스크가 이동시키므로 고정하지 않는다)
        (opal/tools/state-tool/tests/test_state_tool_run_log.py S-9와 동일 기준선·동일
        --ignore 관례 — 자기 자신을 포함해 discover하면 S-9가 이 스위트를 재귀 기동한다)."""
        self_referential = (_PROJECT_ROOT / "opal" / "tools" / "state-tool" / "tests"
                             / "test_state_tool_run_log.py")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "opal/tools/state-tool/tests/", "-q",
             f"--ignore={self_referential}"],
            cwd=str(_PROJECT_ROOT), capture_output=True, text=True)
        combined = result.stdout + result.stderr
        # [불안정 기준선 제거 — 123 opd 전환] 통과 **개수**를 상수로 박으면 형제 태스크가
        # 테스트를 늘릴 때마다 구현이 정상인데도 거짓 실패가 난다(실제 발생: 425→441,
        # main의 122·131 유입). 더구나 개수 단언은 누군가 테스트를 지우고 수를 맞춰도
        # 통과시켜 계약을 지키지 못한다. 이 단언이 지키려는 계약은 "기존 테스트가 깨지지
        # 않았다"이므로 **실패 0건**이라는 불변 조건으로 판정한다.
        self.assertNotIn("failed", combined,
                         f"S-28 회귀 실패 — 기존 테스트가 깨졌다. 출력 말미: {combined[-2000:]}")
        self.assertIn("passed", combined,
                      f"S-28 테스트가 수집되지 않았다(스위트 자체 실패 의심). 출력 말미: {combined[-2000:]}")
        self.assertEqual(0, result.returncode,
                         f"S-28 pytest 종료 코드 비정상({result.returncode}). 출력 말미: {combined[-2000:]}")
        self.assertIn("3 skipped", combined, f"S-28 회귀 기준선(3 skipped) 불일치 — {combined[-2000:]}")
        self.assertNotIn(" failed", combined, f"S-28 state-tool 회귀에 실패가 있음 — {combined[-2000:]}")


# ─────────────────────────────────────────────────────────────────────────────
# S-29 — PM 판정② — 명시적 --mode 인자로만 active 전용 source 제약 집행
# ─────────────────────────────────────────────────────────────────────────────

class TestActiveModeSourceConstraint(unittest.TestCase):
    def _activity_adapter_kwargs(self, request_id, source_kind, mode=None):
        kwargs = dict(
            request_id=request_id, event="activity",
            actor_kind="worker", actor_id="w1",
            provenance_type="adapter", recorded_by_kind="adapter",
            source_kind=source_kind, source_id="sid",
            source_sha256="a" * 64, source_observed_at="2026-09-13T00:00:00.000Z",
            worker_run_id="wrk_s29", summary="s29", data={"kind": "progress"},
        )
        if mode is not None:
            kwargs["mode"] = mode
        return kwargs

    def test_mode_argument_gates_active_source_constraint(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s29-task")
            run_id = "run_s29"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-29 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            code_a, out_a, err_a, data_a = _run(_append_raw(
                task_path, run_id, **self._activity_adapter_kwargs("req_s29_a", "process_start")))
            self.assertEqual(code_a, 0, f"S-29(a) 실패 — stdout={out_a!r} stderr={err_a!r}")
            self.assertTrue(data_a.get("ok"), f"S-29(a) ok:false — {data_a}")

            code_b, out_b, err_b, data_b = _run(_append_raw(
                task_path, run_id, **self._activity_adapter_kwargs("req_s29_b", "process_start", mode="active")))
            self.assertNotEqual(code_b, 0, f"S-29(b)가 exit 0으로 통과함 — stdout={out_b!r}")
            self.assertFalse(data_b.get("ok", True), f"S-29(b) ok:true — {data_b}")
            self.assertEqual(data_b.get("error", {}).get("code"), "provenance_invalid",
                              f"S-29(b) 오류 코드 불일치 — {data_b}")

            code_c, out_c, err_c, data_c = _run(_append_raw(
                task_path, run_id, **self._activity_adapter_kwargs("req_s29_c", "agent_message", mode="active")))
            self.assertEqual(code_c, 0, f"S-29(c) 실패 — stdout={out_c!r} stderr={err_c!r}")
            self.assertTrue(data_c.get("ok"), f"S-29(c) ok:false — {data_c}")

            code_d, out_d, err_d, data_d = _run(_append_raw(
                task_path, run_id, **self._activity_adapter_kwargs("req_s29_d", "process_start", mode="shadow")))
            self.assertEqual(code_d, 0, f"S-29(d) 실패 — stdout={out_d!r} stderr={err_d!r}")
            self.assertTrue(data_d.get("ok"), f"S-29(d) ok:false — {data_d}")

    def test_mode_not_read_from_disk(self):
        """전 케이스에서 코어 소스에 state_tool·state.json 문자열 0건 유지 — 모드는 인자로만 소비"""
        for src_path in (_CORE_SRC, _CLI_SRC):
            text = src_path.read_text(encoding="utf-8")
            self.assertNotIn("state_tool", text, f"S-29 {src_path.name}에 state_tool 결합 문자열 발견")
            self.assertNotIn("state.json", text, f"S-29 {src_path.name}에 state.json 문자열 발견")


# ─────────────────────────────────────────────────────────────────────────────
# 가져오기 읽기 경로 방어 회귀 고정 (locked 시나리오 목록 밖 — 보안 검사 GC-201/
# 202/212/213이 실측한 방어를 테스트로 고정한다. 이 방어가 없으면 S-3~S-29
# 어느 것도 떨어뜨리지 않고 통과하므로, 별도로 고정하지 않으면 후속 변경이
# 무심코 제거해도 아무 시나리오도 감지하지 못한다.)
# ─────────────────────────────────────────────────────────────────────────────

class TestImportReadPathDefenses(unittest.TestCase):
    """import-agentic/import-oppl 읽기 경로의 심볼릭 링크·하드 링크·비정규
    파일(FIFO) 거부를 실제 subprocess 실행 + 디스크 검사로 고정한다. mock 없음."""

    def test_symlinked_agentic_log_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            outside = pathlib.Path(tmp) / "outside"
            outside.mkdir()
            secret = outside / "secret.md"
            secret.write_text(
                "## 대행 일지\n\n| # | 시점 | 단계 | 카테고리 | 내용 | 결과 |\n"
                "|---|---|---|---|---|---|\n"
                "| 1 | 2026-09-13 01:00 | PLAN | DECISION | SYMLINK-LEAK | ok |\n",
                encoding="utf-8",
            )
            task_path = _abs_task_dir(tmp, "defense-symlink-task")
            run_id = "run_defsym"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            try:
                os.symlink(str(secret), str(task_path / "AGENTIC-LOG.md"))
            except OSError:
                self.skipTest("이 환경은 os.symlink()를 지원하지 않음")

            code, out, errtext, data = _run(
                ["import-agentic", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertNotEqual(code, 0, f"심볼릭 링크 AGENTIC-LOG.md가 exit 0으로 통과함 — stdout={out!r}")
            self.assertFalse(data.get("ok", True), f"심볼릭 링크 AGENTIC-LOG.md ok:true — {data}")

            segment = _segment_of(task_path, run_id)
            raw = segment.read_text(encoding="utf-8") if segment.exists() else ""
            self.assertNotIn("SYMLINK-LEAK", raw, "심볼릭 링크로 가져온 외부 내용이 조각에 유출됨")
            self.assertEqual(len(raw.splitlines()), 0, "거부됐는데도 조각에 줄이 추가됨")

    def test_oppl_dir_symlink_and_file_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            outside_dir = pathlib.Path(tmp) / "outside_dir"
            outside_dir.mkdir()
            (outside_dir / "PLAN.result.json").write_text(
                json.dumps({"uuid": "u1", "subtype": "DIR-SYMLINK-LEAK"}), encoding="utf-8")

            task_a = _abs_task_dir(tmp, "defense-opplsym-a")
            run_a = "run_defoppla"
            code_a0, out_a0, err_a0, _ = _run(
                ["init", "--task", str(task_a), "--run-id", run_a, "--format", "json"])
            self.assertEqual(code_a0, 0, f"선행 init(A) 실패 — stdout={out_a0!r} stderr={err_a0!r}")
            try:
                os.symlink(str(outside_dir), str(task_a / ".oppl-run"))
            except OSError:
                self.skipTest("이 환경은 os.symlink()를 지원하지 않음")

            code_a, out_a, err_a, data_a = _run(
                ["import-oppl", "--task", str(task_a), "--run-id", run_a, "--format", "json"])
            self.assertNotEqual(code_a, 0, f".oppl-run/ 심볼릭 링크가 exit 0으로 통과함 — stdout={out_a!r}")
            self.assertFalse(data_a.get("ok", True), f".oppl-run/ 심볼릭 링크 ok:true — {data_a}")
            segment_a = _segment_of(task_a, run_a)
            raw_a = segment_a.read_text(encoding="utf-8") if segment_a.exists() else ""
            self.assertNotIn("DIR-SYMLINK-LEAK", raw_a, ".oppl-run/ 링크로 가져온 외부 내용이 유출됨")

            # 하위 파일 개별 링크 — .oppl-run/ 자체는 정상이되 그 안의 journal.md만 링크.
            outside_file = pathlib.Path(tmp) / "outside_journal.md"
            outside_file.write_text(
                "# journal\n\n| 시각 | 단계 | 이벤트 | 근거 |\n|---|---|---|---|\n"
                "| 2026-09-13T00:00:00.000Z | T1 | start | FILE-SYMLINK-LEAK |\n",
                encoding="utf-8",
            )
            task_b = _abs_task_dir(tmp, "defense-opplsym-b")
            run_b = "run_defopplb"
            code_b0, out_b0, err_b0, _ = _run(
                ["init", "--task", str(task_b), "--run-id", run_b, "--format", "json"])
            self.assertEqual(code_b0, 0, f"선행 init(B) 실패 — stdout={out_b0!r} stderr={err_b0!r}")
            (task_b / ".oppl-run").mkdir()
            os.symlink(str(outside_file), str(task_b / ".oppl-run" / "journal.md"))

            code_b, out_b, err_b, data_b = _run(
                ["import-oppl", "--task", str(task_b), "--run-id", run_b, "--format", "json"])
            segment_b = _segment_of(task_b, run_b)
            raw_b = segment_b.read_text(encoding="utf-8") if segment_b.exists() else ""
            self.assertNotIn("FILE-SYMLINK-LEAK", raw_b,
                              "journal.md 개별 심볼릭 링크로 가져온 외부 내용이 유출됨")
            # 개별 파일 링크는 그 파일만 배제하고 다른 원본이 없으므로 imported 0건.
            if data_b.get("ok"):
                self.assertEqual(data_b.get("data", {}).get("imported"), 0,
                                  f"journal.md 링크가 배제되지 않고 가져와짐 — {data_b}")

    def test_hard_linked_agentic_log_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            outside = pathlib.Path(tmp) / "outside_hl"
            outside.mkdir()
            secret = outside / "secret.md"
            secret.write_text(
                "## 대행 일지\n\n| # | 시점 | 단계 | 카테고리 | 내용 | 결과 |\n"
                "|---|---|---|---|---|---|\n"
                "| 1 | 2026-09-13 01:00 | PLAN | DECISION | HARDLINK-LEAK | ok |\n",
                encoding="utf-8",
            )
            task_path = _abs_task_dir(tmp, "defense-hardlink-task")
            run_id = "run_defhard"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            try:
                os.link(str(secret), str(task_path / "AGENTIC-LOG.md"))
            except OSError:
                self.skipTest("이 환경은 os.link()를 지원하지 않음(다른 파일시스템 등)")

            code, out, errtext, data = _run(
                ["import-agentic", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertNotEqual(code, 0, f"하드 링크 AGENTIC-LOG.md가 exit 0으로 통과함 — stdout={out!r}")
            self.assertFalse(data.get("ok", True), f"하드 링크 AGENTIC-LOG.md ok:true — {data}")

            segment = _segment_of(task_path, run_id)
            raw = segment.read_text(encoding="utf-8") if segment.exists() else ""
            self.assertNotIn("HARDLINK-LEAK", raw,
                              "하드 링크로 가져온 외부 내용이 조각에 유출됨 — 출처 위장 방지 실패(GC-212)")
            self.assertEqual(len(raw.splitlines()), 0, "거부됐는데도 조각에 줄이 추가됨")

    def test_fifo_agentic_log_does_not_hang(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "defense-fifo-task")
            run_id = "run_deffifo"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            fifo_path = task_path / "AGENTIC-LOG.md"
            try:
                os.mkfifo(str(fifo_path))
            except (OSError, AttributeError):
                self.skipTest("이 환경은 os.mkfifo()를 지원하지 않음")

            cmd = ["bash", str(_RUN_SH), "import-agentic", "--task", str(task_path),
                   "--run-id", run_id, "--format", "json"]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            except subprocess.TimeoutExpired:
                self.fail("import-agentic이 FIFO 앞에서 30초 넘게 정지함(GC-213 회귀)")

            self.assertNotEqual(result.returncode, 0,
                                 f"FIFO AGENTIC-LOG.md가 exit 0으로 통과함 — stdout={result.stdout!r}")
            try:
                data = json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                self.fail(f"FIFO 거부 시 §2.1 봉투를 반환하지 않음 — stdout={result.stdout!r}")
            self.assertFalse(data.get("ok", True), f"FIFO AGENTIC-LOG.md ok:true — {data}")

    def test_normal_agentic_log_still_imports(self):
        """대조군 — 방어가 정상 입력을 막지 않는다."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "defense-normal-task")
            run_id = "run_defnormal"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"선행 init 실패 — stdout={out0!r} stderr={err0!r}")
            (task_path / "AGENTIC-LOG.md").write_text(
                _SAMPLE_AGENTIC_LOG.read_text(encoding="utf-8"), encoding="utf-8")

            code, out, errtext, data = _run(
                ["import-agentic", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code, 0, f"정상 AGENTIC-LOG.md 가져오기 실패 — stdout={out!r} stderr={errtext!r}")
            self.assertTrue(data.get("ok"), f"정상 AGENTIC-LOG.md ok:false — {data}")
            self.assertGreater(data.get("data", {}).get("imported", 0), 0,
                                "정상 AGENTIC-LOG.md인데 imported<=0 — 방어가 정상 입력까지 막음")




# ═════════════════════════════════════════════════════════════════════════════
# 태스크 123 신규 시나리오 — TEST-SCENARIO.md
#   (tasks/123-260912-oppl-태스크-실행로그-표준화/TEST-SCENARIO.md) S-1~S-7, RED-a 분할
#   (opal-test-agent, test_mode=red). 위쪽 S-3~S-29는 이전 하위 태스크(T02/T03) PLAN
#   기준 시나리오 번호이며 이번 태스크의 S-1~S-7과 ID가 겹치지만 서로 다른 시나리오다 —
#   클래스명을 `TestS{n}...` 접두로 구분해 혼동을 막는다. GREEN(redact() 본문 — W-2,
#   조각 경계 전환 — W-5, terminal duration_spans 검증·reconcile-duration — W-6)은 이
#   배치가 구현하지 않는다(작성자≠구현자, red-first.md §1.5). 아래 각 테스트는 공개
#   인터페이스(run-log-tool CLI·run_log_core 공개 함수·실제 state-tool CLI)만으로
#   판정하며 mock/patch/MagicMock/가짜 파일시스템을 쓰지 않는다.
# ═════════════════════════════════════════════════════════════════════════════

import hashlib
import multiprocessing
import stat as _stat_module
import uuid

_STATE_TOOL_DIR = _TOOL_DIR.parent / "state-tool"
_STATE_RUN_SH = _STATE_TOOL_DIR / "run.sh"


def _run_state_tool(args, cwd=None):
    """state-tool run.sh를 subprocess로 실행한다(외부 실호출 — state_tool.py는 읽기만
    하고 수정하지 않는다. 본 RED 배치의 변경 범위는 test_run_log_tool.py 1개 파일뿐)."""
    cmd = ["bash", str(_STATE_RUN_SH)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


# secret fixture 4종 (Setup 공통 데이터) — 환경변수형·Bearer 토큰·API key·private key 블록.
_SECRET_ENV_VAR = "DB_PASSWORD=Sup3rSecretP@ssw0rd_9x!"
_SECRET_BEARER = "Bearer sk-live-4f9a1c2b8e7d4a6f9b0c1d2e3f4a5b6c"
_SECRET_API_KEY = "api_key=AKIAIOSFODNN7EXAMPLE1234567890AB"
# [MUST] 줄바꿈 문자를 넣지 않는다 — JSON 직렬화는 개행을 `\n` 2문자로 이스케이프하므로,
# 원본 문자열에 실제 개행이 섞이면 디스크에 쓰인 텍스트와 파이썬 문자열 리터럴이
# 바이트 단위로 달라져 `in` 부분일치 판정이 거짓 통과(false negative)를 낸다.
_SECRET_PRIVATE_KEY_BLOCK = (
    "-----BEGIN PRIVATE KEY-----"
    + ("MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7" * 40)
    + "-----END PRIVATE KEY-----"
)
_SECRET_FIXTURES = {
    "env_var": _SECRET_ENV_VAR,
    "bearer_token": _SECRET_BEARER,
    "api_key": _SECRET_API_KEY,
    "private_key_block": _SECRET_PRIVATE_KEY_BLOCK,
}


# ─────────────────────────────────────────────────────────────────────────────
# S-1 (AC-13) — secret fixture 4종 → 표준 append·상태 보관함 커밋·legacy 가져오기
# 3경로 산출물에 평문 0건. redact()가 pass-through라 현재는 3경로 모두 평문이 남는다.
# ─────────────────────────────────────────────────────────────────────────────

class TestS1SecretMaskingAcrossThreePaths(unittest.TestCase):
    """redact()가 아직 본문 미구현(pass-through, D-9)이므로 아래 3경로 전부 평문이
    디스크에 남아 이 클래스의 테스트가 실패한다 — W-2 GREEN 대상의 RED 증거."""

    def test_standard_append_path_leaves_no_plaintext(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s1-append-task")
            run_id = "run_s1append"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-1 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            for idx, (kind, secret) in enumerate(_SECRET_FIXTURES.items()):
                args = _append_activity_args(
                    task_path, run_id, f"req_s1_append_{idx}",
                    f"S-1 {kind} 표준 append 투입: {secret}")
                code, out, err, data = _run(args)
                self.assertEqual(code, 0, f"S-1 {kind} append 실패 — stdout={out!r} stderr={err!r}")

            segment_text = _segment_of(task_path, run_id).read_text(encoding="utf-8")
            for kind, secret in _SECRET_FIXTURES.items():
                self.assertNotIn(
                    secret, segment_text,
                    f"S-1 표준 append: 조각 파일에 {kind} 평문이 남아있음(redact() 미구현)")

    def test_legacy_import_path_leaves_no_plaintext(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s1-import-task")
            run_id = "run_s1import"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-1 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            rows = []
            for i, (kind, secret) in enumerate(_SECRET_FIXTURES.items(), start=1):
                rows.append(
                    f"| {i} | 2026-09-12 10:{i:02d} | EXECUTE | DECISION | "
                    f"S-1 {kind}: {secret} | 반영 |")
            log_text = (
                "# AGENTIC-LOG: S-1 secret fixture\n\n"
                "## 대행 일지\n\n"
                "| # | 시점 | 단계 | 카테고리 | 내용 | 결과 |\n"
                "|---|------|------|----------|------|------|\n"
                + "\n".join(rows) + "\n"
            )
            (task_path / "AGENTIC-LOG.md").write_text(log_text, encoding="utf-8")

            code, out, err, data = _run(
                ["import-agentic", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code, 0, f"S-1 legacy 가져오기 실패 — stdout={out!r} stderr={err!r}")
            self.assertTrue(data.get("ok"), f"S-1 legacy 가져오기 ok:false — {data}")
            self.assertEqual(
                data.get("data", {}).get("imported"), len(_SECRET_FIXTURES),
                f"S-1 legacy 가져오기 imported 수 불일치 — {data}")

            segment_text = _segment_of(task_path, run_id).read_text(encoding="utf-8")
            for kind, secret in _SECRET_FIXTURES.items():
                self.assertNotIn(
                    secret, segment_text,
                    f"S-1 legacy 가져오기: 조각 파일에 {kind} 평문이 남아있음(redact() 미구현)")

    def test_state_outbox_commit_path_leaves_no_plaintext(self):
        for kind, secret in _SECRET_FIXTURES.items():
            with self.subTest(kind=kind):
                with tempfile.TemporaryDirectory() as tmp:
                    task_path = _abs_task_dir(tmp, f"s1-outbox-{kind}")
                    rows_spec = json.dumps(
                        [{"stage": "EXECUTE", "item": "S-1 outbox 대상"}], ensure_ascii=False)
                    code0, out0, err0, _ = _run_state_tool([
                        "init", str(task_path), "--skill", "oppl", "--mode", "agentic",
                        "--rows-spec", rows_spec, "--run-log-mode", "shadow",
                    ])
                    self.assertEqual(
                        code0, 0,
                        f"S-1 {kind} 상태 도구 init 실패 — stdout={out0!r} stderr={err0!r}")

                    code, out, err, data = _run_state_tool(
                        ["advance", str(task_path), "--row", "1", "--note", secret])
                    self.assertEqual(
                        code, 0, f"S-1 {kind} advance 실패 — stdout={out!r} stderr={err!r}")

                    # [MUST] 판정 범위는 run_log 계열 writer 산출물(보관함 pending_events +
                    # 드레인된 조각 파일)만이다 — state.json의 row["note"]는 D-9 마스킹
                    # 초크포인트(_atomic_write_state_json이 redact()를 거는 대상은
                    # run_log.pending_events뿐)와 무관한, 원래부터 평문인 별개의 저널
                    # 기능이라 여기에 포함하면 GREEN 이후에도 영원히 실패하는 거짓 RED가
                    # 된다(row.note는 STATE.md 의사결정 로그의 원본이며 마스킹 대상이
                    # 아니다).
                    state_json = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
                    pending_text = json.dumps(
                        (state_json.get("run_log") or {}).get("pending_events") or [],
                        ensure_ascii=False)
                    run_dir = task_path / "run"
                    segment_text = ""
                    if run_dir.exists():
                        for seg in sorted(run_dir.glob("run-log-*-*.jsonl")):
                            segment_text += seg.read_text(encoding="utf-8")

                    self.assertNotIn(
                        secret, pending_text,
                        f"S-1 {kind}: state.json run_log.pending_events(상태 보관함)에 "
                        "평문이 남아있음(redact() 미구현)")
                    self.assertNotIn(
                        secret, segment_text,
                        f"S-1 {kind}: 드레인된 조각 파일에 평문이 남아있음(redact() 미구현)")


# ─────────────────────────────────────────────────────────────────────────────
# S-2 (AC-13, C-5, H-1) — redact() 멱등성·구조 불변, 16 KiB 상한이 redact() 통과
# 후 최종 줄에서 측정되는 순서 불변.
# ─────────────────────────────────────────────────────────────────────────────

class TestS2RedactIdempotentAndSizeOrder(unittest.TestCase):
    def test_redact_masks_all_secret_fixtures(self):
        core = _import_core()
        payload = {
            "event": "activity",
            "summary": "S-2 redact 대상",
            "data": {
                "kind": "progress",
                "env": _SECRET_ENV_VAR,
                "bearer": _SECRET_BEARER,
                "api_key": _SECRET_API_KEY,
                "private_key": _SECRET_PRIVATE_KEY_BLOCK,
            },
        }
        redacted = core.redact(payload)
        serialized = json.dumps(redacted, ensure_ascii=False)
        for kind, secret in _SECRET_FIXTURES.items():
            self.assertNotIn(
                secret, serialized,
                f"S-2 redact() 통과 후에도 {kind} 평문이 남아있음(pass-through 미구현)")

    def test_redact_is_idempotent_and_preserves_structure(self):
        core = _import_core()
        payload = {
            "event": "activity",
            "summary": "S-2 멱등성",
            "data": {"kind": "progress", "env": _SECRET_ENV_VAR,
                     "nested": {"api_key": _SECRET_API_KEY}},
        }
        once = core.redact(payload)
        twice = core.redact(once)
        self.assertEqual(once, twice, "S-2 redact() 1회/2회 결과가 다름(멱등 계약 위반)")

        def _shape(v):
            if isinstance(v, dict):
                return {k: _shape(v2) for k, v2 in v.items()}
            if isinstance(v, list):
                return [_shape(v2) for v2 in v]
            return type(v).__name__

        self.assertEqual(_shape(payload), _shape(once),
                          "S-2 redact()가 키 집합·타입·중첩 깊이를 바꿈")

    def test_16kib_cap_measured_after_redact_not_before(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s2-cap-task")
            run_id = "run_s2cap"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-2 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            # private key 블록 + 패딩으로 pre-redaction 직렬화를 16 KiB 위로 부풀린다.
            # redact()가 실동작하면 블록 전체가 짧은 placeholder로 치환돼 post-redaction
            # 크기는 상한 아래로 줄어야 한다(D-P3 "순서 불변" 계약 — redact() 통과 후
            # 최종 줄에서 측정).
            oversized_secret = _SECRET_PRIVATE_KEY_BLOCK + ("A" * 15000)
            args = _append_activity_args(
                task_path, run_id, "req_s2_cap", f"S-2 상한 순서: {oversized_secret}")
            code, out, err, data = _run(args)
            self.assertEqual(
                code, 0,
                "S-2 redact() 통과 후 크기가 상한 아래로 줄어야 하는데 현재 pass-through라 "
                f"거부됨(W-2 GREEN 대상) — stdout={out!r} stderr={err!r}")
            self.assertTrue(data.get("ok"), f"S-2 상한 순서 판정 ok:false — {data}")


# ─────────────────────────────────────────────────────────────────────────────
# S-3 (AC-13, H-5) — event_id·sha256·worker_log_token_id는 비밀값과 형태가 비슷한
# 16진 문자열이지만 마스킹되면 안 된다. 같은 사건에 진짜 비밀값을 함께 실어, 비밀은
# 마스킹되고 보존 대상은 그대로인지 함께 판정한다.
# ─────────────────────────────────────────────────────────────────────────────

class TestS3PreservedIdentifiersSurviveMaskingAlongsideSecrets(unittest.TestCase):
    def test_worker_log_token_id_preserved_while_secret_masked(self):
        core = _import_core()
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s3-a2-task")
            task_path_str = str(task_path)
            run_id = "run_s3a2"
            init_result = core.init(task_path_str, run_id)
            self.assertTrue(init_result.get("ok"), f"S-3 init 실패 — {init_result}")

            token_id = "wlt_" + uuid.uuid4().hex
            event = {
                "request_id": "req_s3_a2",
                "event": "activity",
                "actor": {"kind": "worker", "id": "w1", "provider": None, "session_id": None},
                "provenance": {
                    "type": "direct",
                    "recorded_by": {"kind": "worker", "id": "w1"},
                    "worker_log_token_id": token_id,
                    "source": {"kind": "worker_event", "id": None, "sha256": None,
                               "observed_at": None, "locator": None, "upstream_event_id": None},
                },
                "worker_run_id": "wr_s3a2",
                "summary": "S-3 A2 combo",
                "data": {"kind": "progress", "leak": _SECRET_API_KEY},
            }
            result = core.append(task_path_str, run_id, event)
            self.assertTrue(result.get("ok"), f"S-3 append 실패 — {result}")

            segment_text = _segment_of(task_path, run_id).read_text(encoding="utf-8")
            record = json.loads(segment_text.strip().splitlines()[-1])
            self.assertEqual(
                record.get("provenance", {}).get("worker_log_token_id"), token_id,
                f"S-3 worker_log_token_id가 통과 전후 다름 — {record}")
            self.assertNotIn(
                _SECRET_API_KEY, segment_text,
                "S-3 보존 대상과 함께 실린 진짜 비밀값이 마스킹되지 않음(redact() 미구현)")

    def test_source_sha256_preserved_while_secret_masked(self):
        core = _import_core()
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s3-a1-task")
            task_path_str = str(task_path)
            run_id = "run_s3a1"
            init_result = core.init(task_path_str, run_id)
            self.assertTrue(init_result.get("ok"), f"S-3 init 실패 — {init_result}")

            source_sha = hashlib.sha256(b"s3-adapter-source-fixture").hexdigest()
            event = {
                "request_id": "req_s3_a1",
                "event": "worker.started",
                "actor": {"kind": "worker", "id": "w1", "provider": None, "session_id": None},
                "provenance": {
                    "type": "adapter",
                    "recorded_by": {"kind": "adapter", "id": "adapter-x"},
                    "worker_log_token_id": None,
                    "source": {"kind": "process_start", "id": "proc-1", "sha256": source_sha,
                               "observed_at": core.utc_now_ms(), "locator": None,
                               "upstream_event_id": None},
                },
                "worker_run_id": "wr_s3a1",
                "data": {"note": _SECRET_ENV_VAR},
            }
            result = core.append(task_path_str, run_id, event)
            self.assertTrue(result.get("ok"), f"S-3 append 실패 — {result}")

            segment_text = _segment_of(task_path, run_id).read_text(encoding="utf-8")
            record = json.loads(segment_text.strip().splitlines()[-1])
            self.assertEqual(
                record.get("provenance", {}).get("source", {}).get("sha256"), source_sha,
                f"S-3 source.sha256가 통과 전후 다름 — {record}")
            self.assertNotIn(
                _SECRET_ENV_VAR, segment_text,
                "S-3 source.sha256와 함께 실린 진짜 비밀값이 마스킹되지 않음(redact() 미구현)")


# ─────────────────────────────────────────────────────────────────────────────
# S-4 (AC-8, H-2) — 조각 상한 직전에서 multiprocessing barrier 동시 해제 → 새 조각
# 정확히 1개, 순번 중복 0·누락 0, task_lock_timeout 미발생.
# ─────────────────────────────────────────────────────────────────────────────

def _s4_barrier_worker(task_path_str, run_id, idx, barrier, queue):
    """barrier 해제 직후 append() 1건을 실행하는 별도 프로세스 대상 함수(모듈
    최상위 — fork/spawn 양쪽 호환)."""
    barrier.wait()
    core = _import_core()
    event = {
        "request_id": f"req_s4_barrier_{idx}",
        "event": "activity",
        "actor": {"kind": "PM", "id": "pm", "provider": None, "session_id": None},
        "provenance": {"type": "direct", "recorded_by": {"kind": "PM", "id": "pm"},
                       "worker_log_token_id": None, "source": None},
        "summary": f"S-4 barrier append {idx}",
        "data": {"kind": "progress"},
    }
    result = core.append(task_path_str, run_id, event)
    queue.put((idx, result))


class TestS4SegmentBoundaryConcurrentBarrier(unittest.TestCase):
    """현재 append()는 항상 segment_path(...,1) 고정 대상에 쓰고 조각 전환 자체가
    없다(W-5 미구현) — barrier 해제 후에도 새 조각이 0개 생겨 RED가 성립한다."""

    def test_barrier_release_creates_exactly_one_new_segment(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s4-barrier-task")
            task_path_str = str(task_path)
            run_id = "run_s4barrier"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-4 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            segment1 = _segment_of(task_path, run_id)
            core = _import_core()

            # 조각 상한(4 MiB) 직전까지 유효한 JSON 줄로 채운다 — 실제 append()를
            # 수천 번 호출하면 barrier 시나리오 준비에만 과도한 시간이 걸리므로,
            # "이미 거의 찬 조각" 상태를 파일에 직접 만든다(코어 구현 대체가 아니라
            # barrier 실험을 위한 사전 상태 준비).
            def _filler(seq):
                return json.dumps({
                    "schema_version": "1.0", "event_id": f"evt_filler_{seq}", "request_id": None,
                    "sequence": seq, "actor_sequence": seq, "timestamp": core.utc_now_ms(),
                    "task_id": task_path.name, "run_id": run_id, "event": "activity",
                    "actor": {"kind": "PM", "id": "pm", "provider": None, "session_id": None},
                    "provenance": {"type": "direct", "recorded_by": {"kind": "PM", "id": "pm"},
                                   "worker_log_token_id": None, "source": None},
                    "summary": "S-4 filler", "data": {"kind": "progress", "pad": "x" * 500},
                }, ensure_ascii=False) + "\n"

            target_bytes = 4 * 1024 * 1024 - 4096  # 4 MiB 상한 직전
            with open(segment1, "a", encoding="utf-8") as f:
                seq = 1
                written = 0
                while written < target_bytes:
                    line = _filler(seq)
                    f.write(line)
                    written += len(line.encode("utf-8"))
                    seq += 1
            filler_count = seq - 1

            n_procs = 3
            ctx = multiprocessing.get_context("fork")
            barrier = ctx.Barrier(n_procs)
            queue = ctx.Queue()
            procs = [
                ctx.Process(target=_s4_barrier_worker,
                            args=(task_path_str, run_id, i, barrier, queue))
                for i in range(n_procs)
            ]
            for p in procs:
                p.start()
            for p in procs:
                # §2.7 락 상한(기본 30,000ms)보다 충분히 짧게 잡는다(과제 지시) —
                # 그러지 않으면 판정이 task_lock_timeout과 뒤섞인다.
                p.join(timeout=20)
            for p in procs:
                if p.is_alive():
                    p.terminate()
                    p.join()

            results = []
            while not queue.empty():
                results.append(queue.get())
            self.assertEqual(
                len(results), n_procs,
                f"S-4 프로세스 {n_procs}개 중 일부가 결과를 내지 못함 — {results}")
            for idx, result in results:
                self.assertNotEqual(
                    (result.get("error") or {}).get("code"), "task_lock_timeout",
                    f"S-4 프로세스 {idx}가 task_lock_timeout — {result}")
                self.assertTrue(result.get("ok"), f"S-4 프로세스 {idx} append 실패 — {result}")

            run_dir = task_path / "run"
            segments = sorted(run_dir.glob(f"run-log-{run_id}-*.jsonl"))
            self.assertEqual(
                len(segments), 2,
                f"S-4 barrier 해제 후 새 조각이 정확히 1개 생겨야 하는데 실제 조각 수="
                f"{len(segments)}(조각 경계 전환 미구현, W-5 GREEN 대상) — {segments}")

            all_sequences = []
            for seg in segments:
                for line in seg.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    all_sequences.append(json.loads(line).get("sequence"))
            self.assertEqual(
                len(all_sequences), len(set(all_sequences)),
                f"S-4 순번 중복 발생 — {sorted(all_sequences)}")
            expected_total = filler_count + n_procs
            self.assertEqual(
                sorted(all_sequences), list(range(1, expected_total + 1)),
                f"S-4 순번 누락/불연속 — {sorted(all_sequences)}")


# ─────────────────────────────────────────────────────────────────────────────
# S-5 (AC-8, C-8) — 새 조각 자리의 심볼릭 링크·경계 이탈은 기존 방어 함수를 재사용해
# 거부해야 한다(D-P12). 조각 0600·run/ 0700 유지.
# ─────────────────────────────────────────────────────────────────────────────

class TestS5SegmentBoundarySymlinkDefenseReuse(unittest.TestCase):
    """조각 전환 자체가 없어(W-5 미구현) 상한을 넘겨도 새 조각 생성을 시도하지 않고
    기존 조각에 조용히 계속 쓴다 — 심볼릭 링크가 있어도 거부되지 않고 ok:true가
    나와 RED가 성립한다."""

    def test_next_segment_symlink_is_rejected_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            outside_dir = pathlib.Path(tmp) / "outside"
            outside_dir.mkdir()
            outside_target = outside_dir / "escape-target.jsonl"
            outside_target.write_text("", encoding="utf-8")

            task_path = _abs_task_dir(tmp, "s5-symlink-task")
            task_path_str = str(task_path)
            run_id = "run_s5symlink"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-5 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            core = _import_core()
            segment1 = _segment_of(task_path, run_id)

            def _filler(seq):
                return json.dumps({
                    "schema_version": "1.0", "event_id": f"evt_filler_{seq}", "request_id": None,
                    "sequence": seq, "actor_sequence": seq, "timestamp": core.utc_now_ms(),
                    "task_id": task_path.name, "run_id": run_id, "event": "activity",
                    "actor": {"kind": "PM", "id": "pm", "provider": None, "session_id": None},
                    "provenance": {"type": "direct", "recorded_by": {"kind": "PM", "id": "pm"},
                                   "worker_log_token_id": None, "source": None},
                    "summary": "S-5 filler", "data": {"kind": "progress", "pad": "x" * 500},
                }, ensure_ascii=False) + "\n"

            target_bytes = 4 * 1024 * 1024 - 4096
            with open(segment1, "a", encoding="utf-8") as f:
                seq = 1
                written = 0
                while written < target_bytes:
                    line = _filler(seq)
                    f.write(line)
                    written += len(line.encode("utf-8"))
                    seq += 1

            # 다음 조각 자리(0002)에 경계 밖 심볼릭 링크를 미리 심어 둔다.
            next_segment = task_path / "run" / f"run-log-{run_id}-0002.jsonl"
            next_segment.symlink_to(outside_target)

            event = {
                "request_id": "req_s5_symlink",
                "event": "activity",
                "actor": {"kind": "PM", "id": "pm", "provider": None, "session_id": None},
                "provenance": {"type": "direct", "recorded_by": {"kind": "PM", "id": "pm"},
                               "worker_log_token_id": None, "source": None},
                "summary": "S-5 링크 위 새 조각 시도",
                "data": {"kind": "progress"},
            }
            result = core.append(task_path_str, run_id, event)

            self.assertFalse(
                result.get("ok", True),
                "S-5 상한 초과 + 다음 조각 위치의 심볼릭 링크가 있는데 append()가 ok:true를 "
                f"반환함(조각 전환·방어 재사용 미구현, W-5 GREEN 대상) — {result}")
            self.assertEqual(
                outside_target.read_text(encoding="utf-8"), "",
                "S-5 경계 밖 링크 대상에 내용이 쓰였음(심볼릭 링크 추종)")
            self.assertTrue(
                next_segment.is_symlink(),
                "S-5 링크가 다른 무언가로 치환됨(원본 상태와 달라짐)")

            run_dir_mode = _stat_module.S_IMODE(os.stat(task_path / "run").st_mode)
            self.assertEqual(run_dir_mode, 0o700, f"S-5 run/ 권한이 0700이 아님 — {oct(run_dir_mode)}")
            segment1_mode = _stat_module.S_IMODE(os.stat(segment1).st_mode)
            self.assertEqual(segment1_mode, 0o600, f"S-5 조각 권한이 0600이 아님 — {oct(segment1_mode)}")


# ─────────────────────────────────────────────────────────────────────────────
# S-6 (AC-8, H-2) — 조각 2개 이상으로 전환이 끝난 뒤 append를 이어가면 새 사건은
# 열린 조각에만 붙고, 이미 닫힌 조각의 mtime·바이트는 변하지 않는다.
# ─────────────────────────────────────────────────────────────────────────────

class TestS6ClosedSegmentImmutabilityCrossSegmentSequence(unittest.TestCase):
    """현재 append()는 항상 segment_path(...,1)에 고정해서 쓰므로(조각 경계 전환
    미구현), 이미 "닫힌" 것으로 취급돼야 할 조각 1이 다시 열려 변경된다 — RED."""

    def test_append_after_rotation_does_not_touch_closed_segment(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s6-closed-task")
            task_path_str = str(task_path)
            run_id = "run_s6closed"
            core = _import_core()

            init_result = core.init(task_path_str, run_id)
            self.assertTrue(init_result.get("ok"), f"S-6 init 실패 — {init_result}")

            segment1 = _segment_of(task_path, run_id)
            segment2 = task_path / "run" / f"run-log-{run_id}-0002.jsonl"

            def _rec(seq, event_id):
                return json.dumps({
                    "schema_version": "1.0", "event_id": event_id, "request_id": None,
                    "sequence": seq, "actor_sequence": seq, "timestamp": core.utc_now_ms(),
                    "task_id": task_path.name, "run_id": run_id, "event": "activity",
                    "actor": {"kind": "PM", "id": "pm", "provider": None, "session_id": None},
                    "provenance": {"type": "direct", "recorded_by": {"kind": "PM", "id": "pm"},
                                   "worker_log_token_id": None, "source": None},
                    "summary": f"S-6 seed {seq}", "data": {"kind": "progress"},
                }, ensure_ascii=False) + "\n"

            k = 5  # 조각 1(닫힘)에 들어간 사건 수
            m = 3  # 조각 2(열림)에 들어간 사건 수
            with open(segment1, "w", encoding="utf-8") as f:
                for s in range(1, k + 1):
                    f.write(_rec(s, f"evt_seed1_{s}"))
            os.chmod(segment1, 0o600)
            fd = os.open(str(segment2), os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for s in range(k + 1, k + m + 1):
                    f.write(_rec(s, f"evt_seed2_{s}"))

            before_stat = os.stat(segment1)
            before_mtime_ns = before_stat.st_mtime_ns
            before_size = before_stat.st_size

            time.sleep(0.05)  # mtime 해상도 여유

            new_event = {
                "request_id": "req_s6_after_rotation",
                "event": "activity",
                "actor": {"kind": "PM", "id": "pm", "provider": None, "session_id": None},
                "provenance": {"type": "direct", "recorded_by": {"kind": "PM", "id": "pm"},
                               "worker_log_token_id": None, "source": None},
                "summary": "S-6 rotation 이후 append",
                "data": {"kind": "progress"},
            }
            result = core.append(task_path_str, run_id, new_event)
            self.assertTrue(result.get("ok"), f"S-6 append 실패 — {result}")

            after_stat = os.stat(segment1)
            self.assertEqual(
                (before_mtime_ns, before_size), (after_stat.st_mtime_ns, after_stat.st_size),
                "S-6 이미 닫힌 조각 1의 mtime·바이트가 바뀜(append()가 segment_path(...,1)에 "
                "고정 기록 — 조각 경계 전환 미구현, W-5 GREEN 대상)")
            self.assertEqual(
                result.get("data", {}).get("sequence"), k + m + 1,
                f"S-6 순번이 조각을 넘어 단조 증가하지 않음 — {result}")


# ─────────────────────────────────────────────────────────────────────────────
# S-7 (AC-12, C-4) — terminal 사건의 data.duration_spans[] 합 검증·source_id 중복
# 거부, duration_ms·floor(duration_ms/60000) 파생 조회, 코어의 state.json 읽기 0건.
# ─────────────────────────────────────────────────────────────────────────────

class TestS7DurationSpansAndReconcile(unittest.TestCase):
    """§1.2 terminal 공통 조건의 duration_spans 검증과 reconcile-duration 조회
    표면이 아직 없다(W-6 미구현) — 합 불일치·중복 source_id가 그대로 수용되고,
    조회 함수·CLI 서브명령 호출은 AttributeError·argparse 오류로 RED가 성립한다."""

    def _terminal_event(self, request_id, spans, duration_ms):
        return {
            "request_id": request_id,
            "event": "worker.completed",
            "actor": {"kind": "worker", "id": "w1", "provider": None, "session_id": None},
            "provenance": {"type": "direct", "recorded_by": {"kind": "worker", "id": "w1"},
                           "worker_log_token_id": "wlt_" + uuid.uuid4().hex,
                           "source": {"kind": "worker_event", "id": None, "sha256": None,
                                      "observed_at": None, "locator": None,
                                      "upstream_event_id": None}},
            "worker_run_id": "wr_s7",
            "duration_ms": duration_ms,
            "duration_source": "adapter_monotonic",
            "data": {"duration_spans": spans},
        }

    def test_mismatched_span_sum_is_rejected(self):
        core = _import_core()
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s7-mismatch-task")
            run_id = "run_s7mismatch"
            init_result = core.init(str(task_path), run_id)
            self.assertTrue(init_result.get("ok"), f"S-7 init 실패 — {init_result}")

            spans = [{"source_id": "proc-1", "duration_ms": 1000},
                     {"source_id": "proc-2", "duration_ms": 2000}]
            event = self._terminal_event("req_s7_mismatch", spans, duration_ms=9999)  # 합(3000)과 불일치
            result = core.append(str(task_path), run_id, event)
            self.assertFalse(
                result.get("ok", True),
                "S-7 duration_ms가 span 합과 다른데 append()가 ok:true를 반환함"
                f"(§1.2 terminal 공통 조건 미구현, W-6 GREEN 대상) — {result}")

    def test_duplicate_source_id_span_is_rejected(self):
        core = _import_core()
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s7-dup-task")
            run_id = "run_s7dup"
            init_result = core.init(str(task_path), run_id)
            self.assertTrue(init_result.get("ok"), f"S-7 init 실패 — {init_result}")

            spans = [{"source_id": "proc-1", "duration_ms": 1000},
                     {"source_id": "proc-1", "duration_ms": 1500}]
            event = self._terminal_event("req_s7_dup", spans, duration_ms=2500)
            result = core.append(str(task_path), run_id, event)
            self.assertFalse(
                result.get("ok", True),
                "S-7 같은 source_id가 중복된 duration_spans인데 append()가 ok:true를 반환함"
                f"(§1.2 terminal 공통 조건 미구현, W-6 GREEN 대상) — {result}")

    def test_matching_span_sum_is_accepted_baseline(self):
        core = _import_core()
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s7-match-task")
            run_id = "run_s7match"
            init_result = core.init(str(task_path), run_id)
            self.assertTrue(init_result.get("ok"), f"S-7 init 실패 — {init_result}")

            spans = [{"source_id": "proc-1", "duration_ms": 1000},
                     {"source_id": "proc-2", "duration_ms": 2000}]
            event = self._terminal_event("req_s7_match", spans, duration_ms=3000)
            result = core.append(str(task_path), run_id, event)
            self.assertTrue(result.get("ok"), f"S-7 합이 일치하는 정상 span인데 거부됨 — {result}")

    def test_core_derived_duration_lookup_function_missing(self):
        """run_log_core에 reconcile_duration 계열 공개 함수가 아직 없다 — 호출 시
        AttributeError가 그대로 전파되며, 이는 그 자체로 유효한 RED 증거다(파일 상단
        기존 관례와 동일, red-first.md §4)."""
        core = _import_core()
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s7-lookup-task")
            run_id = "run_s7lookup"
            init_result = core.init(str(task_path), run_id)
            self.assertTrue(init_result.get("ok"), f"S-7 init 실패 — {init_result}")
            spans = [{"source_id": "proc-1", "duration_ms": 1500}]
            event = self._terminal_event("req_s7_lookup", spans, duration_ms=1500)
            append_result = core.append(str(task_path), run_id, event)
            self.assertTrue(append_result.get("ok"), f"S-7 선행 append 실패 — {append_result}")

            lookup = core.reconcile_duration(str(task_path), run_id, "wr_s7")
            self.assertEqual(lookup.get("data", {}).get("duration_ms"), 1500)
            self.assertEqual(lookup.get("data", {}).get("duration_minutes"), 0)

    def test_cli_reconcile_duration_subcommand_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s7-cli-task")
            run_id = "run_s7cli"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"S-7 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            code, out, err, data = _run([
                "reconcile-duration", "--task", str(task_path), "--run-id", run_id,
                "--worker-run-id", "wr_s7cli", "--format", "json",
            ])
            self.assertEqual(
                code, 0,
                "S-7 run-log-tool reconcile-duration 서브명령이 아직 없어 argparse가 "
                f"거부함(W-6 GREEN 대상) — stdout={out!r} stderr={err!r}")

    def test_core_does_not_read_state_json_during_reconcile(self):
        """코어는 task_path·run_id·worker_run_id만으로 조회해야 하며 state.json을
        읽지 않는다(D-5). state.json이 없는 태스크에서도 조회가 성립해야 한다는
        점으로 이를 실측한다 — 현재는 함수 자체가 없어 AttributeError로 RED다."""
        core = _import_core()
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "s7-nostate-task")
            run_id = "run_s7nostate"
            init_result = core.init(str(task_path), run_id)
            self.assertTrue(init_result.get("ok"), f"S-7 init 실패 — {init_result}")
            self.assertFalse((task_path / "state.json").exists(),
                              "S-7 준비 단계에서 state.json이 생겨서는 안 됨")
            spans = [{"source_id": "proc-1", "duration_ms": 750}]
            event = self._terminal_event("req_s7_nostate", spans, duration_ms=750)
            append_result = core.append(str(task_path), run_id, event)
            self.assertTrue(append_result.get("ok"), f"S-7 선행 append 실패 — {append_result}")

            lookup = core.reconcile_duration(str(task_path), run_id, "wr_s7")
            self.assertTrue(lookup.get("ok"), f"S-7 조회 실패 — {lookup}")
            self.assertFalse(
                (task_path / "state.json").exists(),
                "S-7 조회 중 state.json이 생성됨(코어가 상태 파일을 건드림, D-5 위반)")


# ─────────────────────────────────────────────────────────────────────────────
# T137 S-3 — PM activity payload 폐쇄: 인프로세스 경로 거부 (AC-4, C-4)
#
# CONTRACT §1.3 "PM activity의 사건 고유 payload 축 폐쇄 목록"의 집행 지점은
# run_log_core.validate_event()다. 따라서 append()를 통과하는 모든 A4 생산 경로가
# 같은 판정을 받아야 한다. 이 클래스는 CLI를 거치지 않는 인프로세스 호출 경로를
# 판정한다(= state-tool.log-event의 앞단 검증으로 우회되지 않음).
# ─────────────────────────────────────────────────────────────────────────────

class TestPmActivityDataClosureInProcess(unittest.TestCase):
    def test_a4_activity_extra_data_key_rejected_without_partial_write(self):
        core = _import_core()
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "t137-s3-task")
            task_path_str = str(task_path)
            run_id = "run_t137s3"
            init_result = core.init(task_path_str, run_id)
            self.assertTrue(init_result.get("ok"), f"T137 S-3 선행 init 실패 — {init_result}")

            segment = _segment_of(task_path, run_id)
            before = segment.read_bytes()

            event = {
                "request_id": "req_t137_s3",
                "event": "activity",
                "actor": {"kind": "PM", "id": "pm", "provider": None, "session_id": None},
                "provenance": {"type": "direct", "recorded_by": {"kind": "PM", "id": "pm"},
                               "worker_log_token_id": None, "source": None},
                "summary": "T137 S-3 폐쇄 위반 payload",
                "data": {"kind": "progress", "x": 1},
            }
            result = core.append(task_path_str, run_id, event)

            self.assertFalse(
                result.get("ok", True),
                f"T137 S-3 A4 activity의 data에 kind 외 키가 있는데 수용됨 — {result}")
            self.assertEqual(
                result.get("error", {}).get("code"), "schema_invalid",
                f"T137 S-3 오류 코드가 schema_invalid가 아님(CONTRACT §1.3/§2.2) — {result}")
            self.assertEqual(
                segment.read_bytes(), before,
                "T137 S-3 거부된 사건이 조각 파일을 변경함(부분 쓰기)")
            self.assertFalse(
                (task_path / "state.json").exists(),
                "T137 S-3 코어가 state.json을 생성함(D-5 단방향 의존 위반)")


# ─────────────────────────────────────────────────────────────────────────────
# T137 S-4 — PM activity payload 폐쇄: run-log-tool append CLI 경로 거부 (AC-4)
# ─────────────────────────────────────────────────────────────────────────────

class TestPmActivityDataClosureCli(unittest.TestCase):
    def test_a4_activity_extra_data_key_rejected_via_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "t137-s4-task")
            run_id = "run_t137s4"
            code0, out0, err0, _ = _run(
                ["init", "--task", str(task_path), "--run-id", run_id, "--format", "json"])
            self.assertEqual(code0, 0, f"T137 S-4 선행 init 실패 — stdout={out0!r} stderr={err0!r}")

            segment = _segment_of(task_path, run_id)
            before = segment.read_bytes()

            code, out, errtext, data = _run([
                "append", "--task", str(task_path), "--run-id", run_id,
                "--request-id", "req_t137_s4", "--event", "activity",
                "--actor-kind", "PM", "--actor-id", "pm",
                "--provenance-type", "direct", "--recorded-by-kind", "PM",
                "--summary", "T137 S-4 폐쇄 위반 payload",
                "--data", '{"kind":"progress","x":1}',
                "--format", "json",
            ])

            self.assertNotEqual(
                code, 0,
                f"T137 S-4 폐쇄 위반 payload가 exit 0으로 통과함 — stdout={out!r}")
            self.assertFalse(
                data.get("ok", True),
                f"T137 S-4 ok:true — {data} stderr={errtext!r}")
            self.assertEqual(
                data.get("error", {}).get("code"), "schema_invalid",
                f"T137 S-4 오류 코드가 schema_invalid가 아님(CONTRACT §2.1 중첩 봉투) — {data}")
            self.assertEqual(
                segment.read_bytes(), before,
                "T137 S-4 거부된 사건이 조각 파일을 변경함(부분 쓰기)")


# ─────────────────────────────────────────────────────────────────────────────
# T137 S-5 — 폐쇄의 적용 조건 경계 (AC-4, C-7 / D-10)
#
# 폐쇄는 조합 A4(actor.kind=PM ∧ provenance.type=direct)에만 적용된다. A8(import
# 경로)·A2(worker direct)는 조합 자체가 이 조건을 만족하지 않으므로 다중 키 data가
# 그대로 수용되어야 한다. 폐쇄가 경계 밖으로 새지 않음을 고정한다.
# ─────────────────────────────────────────────────────────────────────────────

class TestPmActivityDataClosureScopeBoundary(unittest.TestCase):
    def test_a8_import_activity_multikey_data_accepted(self):
        core = _import_core()
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "t137-s5a-task")
            task_path_str = str(task_path)
            run_id = "run_t137s5a"
            init_result = core.init(task_path_str, run_id)
            self.assertTrue(init_result.get("ok"), f"T137 S-5(a) 선행 init 실패 — {init_result}")

            source_sha = hashlib.sha256(b"t137-s5a-import-source").hexdigest()
            event = {
                "request_id": "req_t137_s5a",
                "event": "activity",
                "actor": {"kind": "PM", "id": "pm", "provider": None, "session_id": None},
                "provenance": {
                    "type": "import",
                    "recorded_by": {"kind": "tool", "id": "run-log-tool"},
                    "worker_log_token_id": None,
                    "source": {"kind": "legacy_line", "id": "line-7", "sha256": source_sha,
                               "observed_at": None,
                               "locator": "tasks/x/AGENTIC-LOG.md#L7",
                               "upstream_event_id": None},
                },
                "summary": "T137 S-5(a) import 경로",
                "data": {"kind": "progress", "x": 1},
            }
            result = core.append(task_path_str, run_id, event)
            self.assertTrue(
                result.get("ok"),
                f"T137 S-5(a) A8 import 조합의 다중 키 data가 거부됨 — 폐쇄가 적용 조건(A4) "
                f"밖으로 샜다(D-10) — {result}")

    def test_a2_worker_direct_activity_multikey_data_accepted(self):
        core = _import_core()
        with tempfile.TemporaryDirectory() as tmp:
            task_path = _abs_task_dir(tmp, "t137-s5b-task")
            task_path_str = str(task_path)
            run_id = "run_t137s5b"
            init_result = core.init(task_path_str, run_id)
            self.assertTrue(init_result.get("ok"), f"T137 S-5(b) 선행 init 실패 — {init_result}")

            event = {
                "request_id": "req_t137_s5b",
                "event": "activity",
                "actor": {"kind": "worker", "id": "w1", "provider": None, "session_id": None},
                "provenance": {
                    "type": "direct",
                    "recorded_by": {"kind": "worker", "id": "w1"},
                    "worker_log_token_id": "wlt_" + uuid.uuid4().hex,
                    "source": {"kind": "worker_event", "id": None, "sha256": None,
                               "observed_at": None, "locator": None,
                               "upstream_event_id": None},
                },
                "worker_run_id": "wr_t137s5b",
                "summary": "T137 S-5(b) worker direct 경로",
                "data": {"kind": "progress", "x": 1, "y": 2},
            }
            result = core.append(task_path_str, run_id, event)
            self.assertTrue(
                result.get("ok"),
                f"T137 S-5(b) A2 worker 조합의 다중 키 data가 거부됨 — 폐쇄가 적용 조건(A4) "
                f"밖으로 샜다(D-10) — {result}")


if __name__ == "__main__":
    unittest.main()
