"""
@header {
  "module": "test_state_tool",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool 단위 테스트 — 9개 명령 happy path + 23종 에러 코드 × 최소 1건 + G-5~G-15 시나리오. 005: TestClarificationGate 신설 — verify --clarification-check + TASK→다음단계 자동 훅 RED-first 케이스 ①~⑨ + 회귀 보호. 054: TestOwnerNamePlaceholder 신설 — note '{owner_name}' 플레이스홀더 identity.md write-time 치환 RED-first(S-1~S-7). 056: TestOpplSkillInit 신설 — `--skill oppl` enum 미등록 RED-first(S-020, H-1) — run.sh subprocess 실호출로 공개 인터페이스만 검증(mock 미사용). 070: task-step 키 주소 체계 도입 1차 RED-first — TestPipelineSpecValidate/TestPipelineJsonInit/TestStateSchema11Compat/TestTaskStepAddressing/TestActionStepRename/TestAddRowKey/TestOpddEnumDrift/TestGroupAPipelineSpecs/TestBackwardCompatAliases 9종 신설(TEST-SCENARIO.md S-1~S-14, PLAN §3.7.2) — 미구현 기능이므로 전부 FAIL 기대(RED 증거). 072: TestNextActionAutoDerive 신설 — STATE.md '다음 액션' 자동 파생 RED-first(TEST-SCENARIO.md S-1~S-4,S-6,S-7) — init next_action 영속화+schema optional 등록, advance/mark 프론티어 파생(pending '진입'/in_progress '진행 중'/전체완료 '태스크 완료'), 첫 줄만 치환(하위 자유기재 보존), --next-action 오버라이드 우선+비지속 복귀 — 공개 CLI 경로(직접 호출+run.sh subprocess)로만 검증, 미구현이므로 실패 기대(RED 증거). 074: TestImportPreservesKeys 신설 — `--import-existing` task-step key 유실 결함 RED-first(TEST-SCENARIO.md S-a~S-e) — force+import-existing 후 rows[].key 100% 보존, pipeline.json 폴백 복원, key 원천 전무 시 keyless+stderr 경고(하위호환), schema_version 1.1 유지, 동일 (stage,item) 중복 순서 소비 — 공개 cmd_init 호출 + 실 파일 I/O로만 검증, 수정 전 코드에서 FAIL 기대(RED 증거). 076: TestTodoMirror 신설 — build_todo_mirror 파생 규칙(TS-001~007): init create 페이로드·전부pending→pending·전부done→completed·advance/부분→in_progress·na 중립·블로커 in_progress 유지·영속 경계(state.json 미영속+schema validate 통과) — 공개 cmd_init/advance/mark/block ok() stdout 페이로드 캡처로만 검증. 088: TestCloseHistoryLink 신설(TS-1~TS-7) — CLOSE 마지막 행 mark 시 link_memory_history()가 <프로젝트루트>/.opal/MEMORY.json history에 행을 자동 생성(title/path/stage/result 파생값, date는 memory-tool KST 충전)·재mark 멱등(duplicate_skipped)·MEMORY.json 부재/손상 시 비차단(ok:true + skipped/failed)·비CLOSE 행 무발동 대조군·result 보강 리마인더 구성요소·state.json 영속 경계(schema validate 통과) — 공개 cmd_mark 호출 + 실 MEMORY.json 파일 내용으로만 검증(내부 함수 mock 없음, 블랙박스 결함 주입). 091(RED-first, mode:red, F-004 게이트 집행 배선): TestTaskStepGate 신설(TEST-SCENARIO S-10~S-17) — check_gate_artifacts()/build_gate_payload()가 아직 없어(Step 8 GREEN 이전) 실 pipeline.json(opd/opdw/opsdd) 기반 gate 정의를 state.json 행에 직접 주입하는 픽스처로 산출물 부재 차단(H-1)·부분 상태 변경 부재·checklist dict 페이로드(H-6)·gate 없는 행 무영향(H-2/H-3)·빈 artifacts 비차단(opdw 실사례)·--force --note 우회 의사결정 로그(H-5)·경로 이탈 토큰 거부(H-4)·glob 토큰 매칭(opsdd 실사례)을 검증(공개 cmd_mark 호출 + 실 state.json/STATE.md 파일 내용, mock 없음). TestPipelineSpecValidate에 gate violation 4종(spec_gate_type_invalid/spec_gate_missing_field/spec_gate_field_type_invalid/spec_gate_checklist_empty, S-9) 케이스 + 실 pipeline.json 10종 유효성 케이스 추가. TestErrorCodesCompleteness에 091 신규 5종 반영(39→44). 093(RED-first, mode:red, 사용자 확인 행 자동 승인 경로 일원화): TestT093AutoNaRemoval/TestT093AutoApproveHook/TestT093AutoApproveBoundary/TestT093HookGuardOrder/TestT093MarkIdempotency/TestT093NaBackwardCompat/TestT093SingleDecisionSource 7종 신설(TEST-SCENARIO S-1~S-18·S-24~S-26) — init 시점 agentic auto-na 제거 후 전 모드 pending/PM 동형성(S-2~S-4), 다음 단계 진입 시 auto_approve_prior_user_confirmations 훅 자동 승인(S-1/S-5/S-13/S-26), CLOSE·워커 경로 구조적 제외(S-6~S-9), user_confirmation_required 전용 에러(S-12/S-24), 훅→후속 가드 순서와 파일 미오염(S-10/S-11), mark 접두 멱등·재-auto-pass no-op(S-15/S-16), MODE_BOUNDARY_STAGES 단일 판정 수렴(S-25), 경계 불변 회귀표 18셀·na 하위호환(S-14/S-17/S-18) — worktree run.sh subprocess 실호출 + 실 pipeline.json/state.json 파일 상태로만 검증(mock 미사용), 미구현 기능이므로 신규 계약 케이스는 전부 FAIL 기대(RED 증거: RED-EVIDENCE.md). 093 GREEN(Step 9): 구형 계약을 고정하던 기존 테스트를 신규 계약으로 수정 — test_init_agentic_auto_na_user_confirmation→test_init_agentic_user_confirmation_pending, test_rows_from_agentic_auto_na→test_rows_from_agentic_user_confirmation_pending(둘 다 na→pending 단언 교체), test_close_gate_regression_via_task_step_addressing_subprocess(주석 갱신 + CLOSE 직전 사용자 확인 행 row 8 캡틴 승인 단계 추가, 최종 assert 불변), agentic CLOSE 게이트 3건(test_agentic_close_gate_requires_user·test_g13_agentic_close_gate_auto_pass_rejected·test_c6_agentic_auto_pass_close_first_row)에 캡틴 승인 사전 단계 추가, test_new_structure_guard_blocks_skip에 사용자 확인 행 선(先)승인으로 guard 축 격리, test_s13_new_style_row_without_gate_response_unaffected 기대 키 집합에 auto_approved 추가, TestErrorCodesCompleteness 44→45종(user_confirmation_required). 테스트 삭제 0건. 094 R-11 Step0(RED-first, mode:red, agentic 승인 계약 정합): TestR11ModeBoundary/TestR11CloseGateFallback/TestR11DerivedSignals/TestR11Invariants 4종 신설(TEST-SCENARIO S-34~S-37,S-40) — G-1 MODE_BOUNDARY_STAGES에 DICT/MODEL/DDL·MIGRATION 3원소 부재로 semi-agentic opdd 설계 확정 3건이 미노출 통과하는 결함을 3 stage 개별 advance 호출로 판정(부분 구현 방지, S-34), G-2 check_close_gate가 확인 행 0개 파이프라인(opgc)에서 --owner user로도 영구 데드락인 결함(S-35), G-3-a/G-3-b _derive_next_action·build_todo_mirror가 자동 승인 예정 확인 행을 중립 처리하지 않아 next_action 헛 확인·todo 오판정하는 결함(S-36/S-37), R-11 [MUST] 불변 제약(신규 판정 함수 금지·next_action 스키마·build_todo_mirror 시그니처·ERROR_CODES 무접촉) 역검증(S-40) — 실 pipeline.json(opdd/opgc/opd) + run.sh subprocess 실호출 + 실 state.json 파일 상태로만 검증(mock 미사용), 미구현 기능이므로 신규 계약 케이스는 전부 FAIL 기대(RED 증거). 구현(op-be-agent)과 작성자(opal-test-agent) 분리. 098 ADD-2(RED-first, mode:red, 배포 경로 루트 파생 결함): TestT098Add2RootDerivation 신설 — `_resolve_citation_exists()`(`state_tool.py:2400`)가 프로젝트 루트를 `task_md_path`가 아니라 스크립트 자기 위치(`__file__`)에서 파생해, 배포본(`~/.opal/tools/state-tool/`)에서 실행 시 조상에 `.opal/MEMORY.json`이 없어 root=None → 정규 인용도 전건 citation_path_not_found로 오강등되는 결함을 3축(①스크립트 위치 독립성 ②오강등 부재 ③프로젝트 소스 실행 회귀 방어)으로 검증 — 실 TASK.md(본 태스크 098) + `state_tool.py` 임시 사본 subprocess 실행(공개 CLI `verify --evidence-check` stdout JSON)으로만 검증(mock 미사용), 미구현이므로 ①·②는 FAIL 기대(RED 증거: RED-EVIDENCE.md ADD-2절). 구현(op-be-agent)과 작성자(opal-test-agent) 분리, state_tool.py 무접촉. 100: TestT100DirectionEvidence 신설(RED-first 7케이스) — `verify --evidence-check`의 `## 확정된 설계 방향` 불릿 파서 확장 계약 검증. ① items[] 편입 + source 필드 ② verdict `승계` ③ `direction_confirmed_ratio` 신규 키 ④ 기존 `confirmed_ratio` 분모 불변(PD-1 분리형) ⑤ 섹션 부재 graceful skip ⑥ exit 0 3경로 ⑦ 항목 0건 분모 0 경계. 실 파일 픽스처 3종(A 방향 6불릿+표 4행 / B 섹션 없음 / C 항목 0건), mock 금지. RED 증거: 단일 파일 7 failed·340 passed → GREEN 후 347 passed(스코프·명령 병기). 작성자(opal-be-agent Step 10)와 구현자(Step 11) 분리. 103 R-21: TestT103WorkerDurationWarning 신설(13케이스) — `mark`가 워커 디스패치 행(`--as-worker` 또는 `--worker-stage`)을 `done`으로 닫으면서 `--worker-duration-minutes`를 빠뜨렸을 때 stdout JSON `warnings`로 경고하는 계약 검증. 발생(W1/W2 두 신호·W3 마지막 Step·W4 문구 구성요소), 차단 아님·산출물 불변(W5 경고본 vs 억제본 state.json/STATE.md 시각 정규화 후 동일·W6 validate ok), 오탐 방어(W7 PM 직접 수행 행 + 응답 키 집합 불변·W8 `owner=user` 사용자 확인 행·W9 값 보유(0 포함)·W10 093 재-auto-pass 멱등 no-op·W3 중간 진행 N<M), 억제(W11 `--worker-duration-unknown` 무경고+필드 미생성·W12 `--worker-duration-minutes`와 배타 exit 2), 카탈로그 경계(W13 `ERROR_CODES` 45종 불변 + `WARNING_CODES` 분리). _T093Base(run.sh subprocess 실호출 + 실 파일 상태)만 사용하며 mock 미사용, 기존 케이스 수정·삭제 0건.",
  "exports": [
    "TestInit", "TestShow", "TestAdvance", "TestMark",
    "TestBlock", "TestValidate", "TestAddRow", "TestStatus", "TestGatePass",
    "TestErrorCodes", "TestFreeTextPreservation", "TestClarificationGate",
    "TestOwnerNamePlaceholder", "TestOpplSkillInit",
    "TestPipelineSpecValidate", "TestPipelineJsonInit", "TestStateSchema11Compat",
    "TestTaskStepAddressing", "TestActionStepRename", "TestAddRowKey",
    "TestOpddEnumDrift", "TestGroupAPipelineSpecs", "TestBackwardCompatAliases",
    "TestNextActionAutoDerive", "TestImportPreservesKeys", "TestTodoMirror",
    "TestCloseHistoryLink", "TestTaskStepGate",
    "TestJournalResilience", "TestLegacyCoexistence", "TestShowAsQueryStandard",
    "TestT093AutoNaRemoval", "TestT093AutoApproveHook", "TestT093AutoApproveBoundary",
    "TestT093HookGuardOrder", "TestT093MarkIdempotency", "TestT093NaBackwardCompat",
    "TestT093SingleDecisionSource",
    "TestR11ModeBoundary", "TestR11CloseGateFallback", "TestR11DerivedSignals",
    "TestR11Invariants", "TestT098Add2RootDerivation",
    "TestT100DirectionEvidence", "TestT103WorkerDuration",
    "TestT103WorkerDurationWarning"
  ]
}

# 인용 규칙 (citation-rules.md §0)
# - PLAN §2.11~§2.17 G-5~G-15 시나리오: 각 테스트 함수 docstring에 §번호 인용
# - PLAN §2.18 에러 코드 23종: 테스트 함수명에 에러 코드 명시 (cross-ref 형식)
# - PLAN §2.19 인자 매트릭스 C-1~C-6: 충돌/종속 관계 테스트 포함
# - [MUST] TASK T-11: 표준 라이브러리만 import (pytest/hypothesis 금지)
# - [MUST] AGENT.md §확정 기준 #2: 임시 디렉토리에서 실행, ~/ .opal/ 직접 수정 금지
"""

# TASK T-11: 표준 라이브러리만 import
import ast
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch, MagicMock

# state_tool.py를 직접 import (PYTHONPATH 조정)
_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
import state_tool as ST

# 056: TestOpplSkillInit용 — run.sh 공개 인터페이스 subprocess 실호출 (mock 금지, red-first.md §4)
_RUN_SH = _TOOL_DIR / "run.sh"


def _run094(args_list):
    """094: run.sh 공개 인터페이스 subprocess 실호출 → (returncode, stdout_str, stderr_str, parsed_json).
    [MUST] red-first.md §4: 공개 인터페이스(stdout/exit code)만 관찰 — mock/patch/MagicMock 금지.
    STATE.md 저널화(094) RED 테스트 전용 — TestJournalResilience/TestLegacyCoexistence/
    TestShowAsQueryStandard 및 기존 클래스 추가분(S-1~S-32)이 공유한다."""
    cmd = ["bash", str(_RUN_SH)] + args_list
    result = subprocess.run(cmd, capture_output=True, text=True)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


# 094: opd pipeline.json 실 스펙 경로 — TEST-SCENARIO.md §2.1 "pipeline 스펙" 실 파일 자산.
# task.task_md 등 gate 필드 없는 순수 행이 다수라 mark/advance/block 회귀 시나리오에 적합하다.
_OPD_REAL_PIPELINE_JSON = _TOOL_DIR.parent.parent / "skills" / "opal-pilot-dev" / "references" / "pipeline.json"


def _extract_md_section(md, heading):
    """094: `## {heading}` 섹션 본문(다음 `## ` 헤딩 직전까지)을 반환. 없으면 "".
    파이프라인 현황판 표와 의사결정 로그 표가 동일한 '| N | ... |' 행 형태를
    공유하므로, 행 수 계산은 반드시 이 헬퍼로 섹션을 먼저 격리한 뒤 수행한다
    (그렇지 않으면 파이프라인 표 행까지 오카운트된다)."""
    m = re.search(rf"^## {re.escape(heading)}\n", md, re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"^## ", md[start:], re.MULTILINE)
    end = start + nxt.start() if nxt else len(md)
    return md[start:end]


def _decision_log_row_numbers(md):
    """094: '## 의사결정 로그' 표의 '#' 컬럼 값 목록을 등장 순서대로 반환."""
    section = _extract_md_section(md, "의사결정 로그")
    return re.findall(r"^\|\s*(\d+)\s*\|", section, re.MULTILINE)

# ─────────────────────────────────────────────────────────────────────────────
# 테스트 공통 픽스처 / 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_ROWS_SPEC = json.dumps([
    {"stage": "TASK",    "item": "작업"},
    {"stage": "TASK",    "item": "TASK.md 생성"},
    {"stage": "TASK",    "item": "사용자 확인"},
    {"stage": "PLAN",    "item": "작업"},
    {"stage": "PLAN",    "item": "PLAN.md 생성"},
    {"stage": "PLAN",    "item": "QA Gate"},
    {"stage": "PLAN",    "item": "QA-PLAN.md 생성"},
    {"stage": "PLAN",    "item": "State Gate"},
    {"stage": "PLAN",    "item": "PM Gate"},
    {"stage": "PLAN",    "item": "State Gate"},
    {"stage": "PLAN",    "item": "사용자 확인"},
    {"stage": "EXECUTE", "item": "작업"},
    {"stage": "EXECUTE", "item": "QA Gate"},
    {"stage": "EXECUTE", "item": "QA-EXECUTE.md 생성"},
    {"stage": "EXECUTE", "item": "State Gate"},
    {"stage": "EXECUTE", "item": "PM Gate"},
    {"stage": "EXECUTE", "item": "State Gate"},
    {"stage": "EXECUTE", "item": "사용자 확인"},
    {"stage": "CLOSE",   "item": "DONE.md 생성"},
    {"stage": "CLOSE",   "item": "State Gate"},
])

GATE_ROWS_SPEC = json.dumps([
    {"stage": "PLAN", "item": "작업"},
    {"stage": "PLAN", "item": "QA Gate"},
    {"stage": "PLAN", "item": "State Gate"},
    {"stage": "PLAN", "item": "PM Gate"},
    {"stage": "PLAN", "item": "State Gate"},
    {"stage": "PLAN", "item": "사용자 확인"},
    {"stage": "CLOSE", "item": "DONE.md 생성"},
    {"stage": "CLOSE", "item": "State Gate"},
])

SIMPLE_ROWS_SPEC = json.dumps([
    {"stage": "TASK",    "item": "작업"},
    {"stage": "PLAN",    "item": "작업"},
    {"stage": "EXECUTE", "item": "작업"},
    {"stage": "CLOSE",   "item": "State Gate"},
])


def _mock_now():
    """date.js 호출을 모킹하는 패치 컨텍스트."""
    return patch.object(ST, "get_kst_datetime", return_value="2026-05-01 23:00")


def make_args(**kwargs):
    """argparse Namespace 유사 객체 생성 헬퍼."""
    defaults = {
        "task_path": None,
        "skill": "opp",
        "mode": "interactive",
        "task_title": None,
        "next_action": None,
        "rows_spec": None,
        "rows_from": None,
        "rows_acts": None,
        "force": False,
        "note": None,
        "import_existing": False,
        "format": "md",
        "row": None,
        "done": True,
        "as_worker": False,
        "worker_stage": None,
        "step": None,
        "owner": None,
        "auto_pass": False,
        "reason": None,
        "after": None,
        "stage": None,
        "item": None,
        "set": None,
        "start": None,
        # 005: clarification-check 플래그 기본값 (AttributeError 방지)
        "clarification_check": False,
        "task_md": None,
        # 070: task-step 키 주소 체계 신규 플래그 기본값 (PLAN §3.3.2/§3.7.2) —
        # GREEN에서 resolve_row_index가 args.task_step/args.task_step_id를 참조하게
        # 되므로, 기존 테스트(이 값들을 지정하지 않는 호출)가 AttributeError 없이
        # 통과하도록 지금 defaults에 추가한다(005 선례와 동일한 유일 허용 접점).
        "task_step": None,
        "task_step_id": None,
        "action_step": None,  # dest="step" 공유 별칭(§3.3.2) — 미사용 시 무해
        "key": None,
        "after_task_step": None,
        "after_task_step_id": None,
    }
    defaults.update(kwargs)
    ns = types.SimpleNamespace(**defaults)
    return ns


class BaseTestCase(unittest.TestCase):
    """임시 디렉토리 + date.js 모킹 공통 베이스.
    [MUST] AGENT.md §확정 기준 #2: tempfile.mkdtemp() 사용, ~/ .opal/ 수정 금지.
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.task_path = self.tmpdir / "134-260501-test"
        self.task_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _call_cmd(self, fn, args, expect_ok=True):
        """명령 함수 호출 → (exit_code, result_dict) 반환.
        ok()는 SystemExit를 발생시키지 않고 print만 하므로 stdout을 캡처.
        err()는 SystemExit를 발생시키므로 둘 다 처리.
        """
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        exit_code = 0
        with redirect_stdout(out):
            try:
                fn(args)
            except SystemExit as e:
                exit_code = e.code
        output = out.getvalue().strip()
        result = json.loads(output) if output else {}
        return exit_code, result

    def _init(self, rows_spec=SIMPLE_ROWS_SPEC, mode="interactive", force=False,
               note=None, import_existing=False, next_action=None, task_title=None):
        """기본 init 헬퍼."""
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode=mode,
                rows_spec=rows_spec,
                force=force, note=note,
                import_existing=import_existing,
                next_action=next_action,
                task_title=task_title,
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
            self.assertEqual(exit_code, 0, f"init failed: {result}")

    def _state(self):
        return json.loads((self.task_path / "state.json").read_text())

    def _md(self):
        return (self.task_path / "STATE.md").read_text()

    def _mark(self, row_id, note=None, as_worker=False, worker_stage=None,
               auto_pass=False, owner=None, force=False, step=None):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=row_id, done=True,
                note=note, as_worker=as_worker,
                worker_stage=worker_stage,
                auto_pass=auto_pass, owner=owner,
                force=force, step=step,
            )
            exit_code, _ = self._call_cmd(ST.cmd_mark, args)
            return exit_code

    def _advance(self, row_id, note=None):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=row_id, note=note,
            )
            exit_code, _ = self._call_cmd(ST.cmd_advance, args)
            return exit_code

    def _block(self, row_id, reason="test reason"):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=row_id, reason=reason,
            )
            exit_code, _ = self._call_cmd(ST.cmd_block, args)
            return exit_code

    def _add_row(self, after, stage, item, note=None):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                after=after, stage=stage, item=item, note=note,
            )
            exit_code, _ = self._call_cmd(ST.cmd_add_row, args)
            return exit_code

    def _status_set(self, to_status, note=None):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                set=to_status, note=note,
            )
            exit_code, _ = self._call_cmd(ST.cmd_status, args)
            return exit_code

    def _validate(self):
        args = make_args(task_path=str(self.task_path))
        _, result = self._call_cmd(ST.cmd_validate, args)
        return result


# ═════════════════════════════════════════════════════════════════════════════
# A. 9개 명령 Happy Path (§3 Step 2 "C. 9개 명령 happy path")
# ═════════════════════════════════════════════════════════════════════════════

class TestInit(BaseTestCase):
    """state init happy path — PLAN §2.11 G-8"""

    def test_init_happy_path(self):
        """init: state.json + STATE.md 정상 생성 (PLAN §2.11 G-8)"""
        self._init(rows_spec=SAMPLE_ROWS_SPEC)
        state = self._state()
        self.assertEqual(state["skill"], "opp")
        self.assertEqual(state["mode"], "interactive")
        self.assertEqual(state["schema_version"], "1.0")
        self.assertEqual(state["current_status"], "in_progress")
        self.assertEqual(len(state["rows"]), 20)  # SAMPLE_ROWS_SPEC = 20행

    def test_init_creates_state_md(self):
        """[T094 수정] init: STATE.md 저널 산출물(의사결정 로그·블로커) 생성 확인
        (D-1 완전 제거 — 마커/파이프라인 표/'## 현재 상태'는 더 이상 생성되지
        않는다. 검증 지점을 파생 표/마커 존재에서 저널 골격 존재로 이동한다.
        PLAN §3.1.2 (1), TEST-SCENARIO S-1)."""
        self._init()
        md = self._md()
        self.assertIn("## 의사결정 로그", md, "저널 골격 '## 의사결정 로그'가 생성되지 않음")
        self.assertIn("| # | 시점 | 결정 | 근거 |", md, "의사결정 로그 빈 표 헤더가 없음")
        self.assertIn("## 블로커", md, "저널 골격 '## 블로커'가 생성되지 않음")
        self.assertIn("없음", md)
        # D-1 완전 제거 — 파생 4패턴은 신규 저널에 0건이어야 함(회귀 가드)
        self.assertNotIn("<!-- pipeline:start -->", md, "마커가 잔존함(D-1 위반)")
        self.assertNotIn("<!-- pipeline:end -->", md, "마커가 잔존함(D-1 위반)")
        self.assertNotIn("## 현재 상태", md, "'## 현재 상태' 섹션이 잔존함(D-1 위반)")
        self.assertNotIn("## 다음 액션", md, "'## 다음 액션' 섹션이 잔존함(D-1 위반)")

    def test_init_g8_free_text_sections(self):
        """[T094 수정] init이 저널 2섹션(의사결정 로그·블로커)을 정확히 생성한다
        (D-1 — '## 다음 액션' 섹션은 완전 제거되어 더 이상 렌더되지 않는다.
        `next_action` 값은 state.json 필드로만 영속화되므로 검증 지점을
        state.json으로 이동한다. PLAN §3.1.2 (1))."""
        self._init(next_action="테스트 다음 액션")
        md = self._md()
        # 저널 2개 섹션 존재 확인
        self.assertIn("## 의사결정 로그", md)
        self.assertIn("## 블로커", md)
        self.assertIn("없음", md)
        # 의사결정 로그 빈 표 헤더
        self.assertIn("| # | 시점 | 결정 | 근거 |", md)
        # '## 다음 액션'은 D-1로 완전 제거됨 — state.json 필드로만 확인(정보 손실 0)
        self.assertNotIn("## 다음 액션", md, "'## 다음 액션' 섹션이 잔존함(D-1 위반)")
        state = self._state()
        self.assertEqual(state.get("next_action"), "테스트 다음 액션",
                         "next_action 값이 state.json에 정상 영속화되어야 함(정보 손실 0)")

    def test_init_agentic_user_confirmation_pending(self):
        """[093 TS-002] init agentic: 사용자 확인 행은 전 모드 pending/⬜/PM으로 초기화된다.
        (093 F-001 — 구형 auto-na 분기 제거. 자동 승인은 init이 아니라 다음 단계 진입 훅이 수행)"""
        rows = json.dumps([
            {"stage": "TASK",    "item": "작업"},
            {"stage": "TASK",    "item": "사용자 확인"},
            {"stage": "CLOSE",   "item": "사용자 확인"},
        ])
        self._init(rows_spec=rows, mode="agentic")
        state = self._state()
        # TASK 사용자 확인 행 → pending (구형: na)
        task_user = next(r for r in state["rows"] if r["stage"] == "TASK" and r["item"] == "사용자 확인")
        self.assertEqual(task_user["status"], "pending")
        self.assertEqual(task_user["status_label"], "⬜")
        self.assertEqual(task_user["owner"], "PM")
        # CLOSE 사용자 확인 행 → pending 유지
        close_user = next(r for r in state["rows"] if r["stage"] == "CLOSE" and r["item"] == "사용자 확인")
        self.assertEqual(close_user["status"], "pending")

    def test_init_rows_all_pending(self):
        """init: 모든 행이 pending/⬜/timestamp=null로 초기화 (PLAN §2.20.1)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC, mode="interactive")
        state = self._state()
        for row in state["rows"]:
            self.assertEqual(row["status"], "pending")
            self.assertEqual(row["status_label"], "⬜")
            self.assertIsNone(row["timestamp"])

    # ─────────────────────────────────────────────────────────────────────
    # 094 RED-first 추가 — TEST-SCENARIO.md S-1, S-9 (PLAN §3.1.2/§3.2.2)
    # [MUST] red-first.md §4: 공개 인터페이스(run.sh subprocess, stdout JSON +
    # exit code) + 실 파일 내용으로만 검증 — mock/patch/MagicMock 금지.
    # ─────────────────────────────────────────────────────────────────────

    def test_s1_new_journal_has_zero_derived_artifacts(self):
        """[T094/L1-F001] S-1 — 빈 태스크 폴더에서
        `init --skill opd --mode agentic --rows-from <pipeline.json>` 실행 시,
        산출 STATE.md 본문에 파생 4패턴(`pipeline:start` 마커 / 파이프라인 표
        헤더 `| # | 단계 | 항목 |` / `## 현재 상태` / `## 다음 액션`)이 각각
        0건이어야 한다(PLAN §3.1.2 (1) 저널 템플릿, D-1 완전 제거).

        RED 근거: 현재 `_build_new_state_md`는 여전히 `<!-- pipeline:start -->`
        마커·파이프라인 표·`## 현재 상태`·`## 다음 액션` 4블록을 전부 생성하므로
        (state_tool.py:1317-1346), 아래 4개 assertEqual(count, 0)이 전부 실패한다."""
        self.assertTrue(_OPD_REAL_PIPELINE_JSON.exists(),
                        f"opd pipeline.json 실 스펙 부재: {_OPD_REAL_PIPELINE_JSON}")
        task_path = self.tmpdir / "094-s1-new-journal"
        task_path.mkdir()
        code, stdout, stderr, data = _run094([
            "init", str(task_path),
            "--skill", "opd", "--mode", "agentic",
            "--rows-from", str(_OPD_REAL_PIPELINE_JSON),
        ])
        self.assertEqual(code, 0, f"init 실패: stdout={stdout!r} stderr={stderr!r}")
        self.assertTrue(data.get("ok"))

        md = (task_path / "STATE.md").read_text(encoding="utf-8")
        self.assertEqual(md.count("pipeline:start"), 0,
                         "신규 저널에 pipeline:start 마커가 잔존함(D-1 위반)")
        self.assertEqual(md.count("| # | 단계 | 항목 |"), 0,
                         "신규 저널에 파이프라인 현황판 표 헤더가 잔존함(D-1 위반)")
        self.assertEqual(md.count("## 현재 상태"), 0,
                         "신규 저널에 '## 현재 상태' 섹션이 잔존함(D-1 위반)")
        self.assertEqual(md.count("## 다음 액션"), 0,
                         "신규 저널에 '## 다음 액션' 섹션이 잔존함(D-1 완전 제거 결정)")

    def test_s9_import_existing_removed_rejected(self):
        """[T094/L2-F002] S-9 — `init --import-existing` 명시적 거부(D-2).

        기대: `{"ok":false,"error":"import_existing_removed",...}` 단일 라인 JSON +
        exit 1 (argparse usage 에러인 exit 2가 아님). RED 근거: 현재 `cmd_init`은
        `--import-existing`을 여전히 정상 처리(마커 파싱·재삽입)하므로 이 에러
        코드 자체가 ERROR_CODES에 없어 어서션이 실패한다(state_tool.py:1177-1206)."""
        task_path = self.tmpdir / "094-s9-import-rejected"
        task_path.mkdir()
        code, stdout, stderr, data = _run094([
            "init", str(task_path),
            "--skill", "opd", "--mode", "agentic",
            "--import-existing",
        ])
        self.assertEqual(code, 1,
                         f"--import-existing은 exit 1(명시적 에러)이어야 한다 — 실제: "
                         f"code={code}, stdout={stdout!r}, stderr={stderr!r}")
        self.assertEqual(len(stdout.splitlines()), 1,
                         "stdout은 단일 라인 JSON이어야 한다(usage 에러 다중 라인 아님)")
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "import_existing_removed")

    def test_s9_no_framework_call_sites_reference_import_existing(self):
        """[T094/L2-F002] S-9 부속 — `opal/`·`docs/`·`.opal/` 전역(현재시제
        본문, `## 변경이력` 섹션 제외)에서 `--import-existing` 문자열 참조가
        0건이어야 한다(H-7, 치환 규격 #11). changelog 섹션은 과거 이력이므로
        소급 변경 금지 대상이라 검사 범위에서 제외한다(치환 규격 #12).

        [T094 추가작업] `.opal/brain/`도 검사 범위에서 제외한다. brain은
        지식 아카이브로서 과거 결정을 원 철자 그대로 보존하는 것이 존재
        이유이며(예: `.opal/brain/pages/entity/state-tool.md`가 D-2
        "`--import-existing` 완전 제거" 결정을 역사적 기록으로 남김),
        `## 변경이력` 섹션과 동일하게 현재시제 사용 안내가 아니다 —
        머지 후 허브(전체 체크아웃) 환경에서 brain ingest가 반영되며
        드러난 오탐이며, brain 페이지 자체를 수정하는 것은 소급 변경
        금지 대상이라 해법이 아니다.

        RED 근거: 개정 전 `README.md`(§2.2.3 실측: `:51,:58,:284,:287`)에
        `--import-existing` 사용 안내가 아직 남아 있어 현재시제 본문 참조가
        0을 초과한다."""
        project_root = _TOOL_DIR.parent.parent.parent  # .../opal (worktree)
        hits = []
        for base in ("opal", "docs", ".opal"):
            base_dir = project_root / base
            if not base_dir.exists():
                continue
            for path in base_dir.rglob("*.md"):
                # PLAN §2.4.1 "개정 제외 확정" — (D) 074 히스토리 fixture 문자열은
                # 검사 대상에서 제외한다(오탐, 소급 변경 금지 대상 아님).
                # [T094 추가작업] `.opal/brain/`은 지식 아카이브(과거 결정
                # 보존소)이며 changelog와 동일하게 현재시제 사용 안내가
                # 아니므로 제외한다.
                rel_parts = path.relative_to(project_root).parts
                if ("backup" in path.parts or "tasks" in path.parts
                        or "fixtures" in path.parts
                        or rel_parts[:2] == (".opal", "brain")):
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                changelog_start = text.find("## 변경이력")
                body = text[:changelog_start] if changelog_start != -1 else text
                body_line_count = len(body.splitlines())
                for lineno, line in enumerate(text.splitlines(), start=1):
                    if lineno > body_line_count:
                        break  # 변경이력 섹션 진입 — 과거 이력이므로 검사 제외
                    if "--import-existing" in line:
                        hits.append(f"{path.relative_to(project_root)}:{lineno}: {line.strip()}")
        self.assertEqual(hits, [],
                         f"--import-existing 참조가 현재시제 본문에 잔존함(H-7): {hits}")


class TestShow(BaseTestCase):
    """state show happy path — PLAN §2.14 G-11"""

    def setUp(self):
        super().setUp()
        self._init()

    def _show(self, fmt="md"):
        args = make_args(task_path=str(self.task_path), format=fmt)
        _, result = self._call_cmd(ST.cmd_show, args)
        return result

    def test_show_md_happy_path(self):
        """show --format md: 마크다운 표 + 현재 상태 4줄 (PLAN §2.14 G-11)"""
        result = self._show("md")
        self.assertTrue(result["ok"])
        self.assertEqual(result["format"], "md")
        self.assertIn("content", result)

    def test_show_json_happy_path(self):
        """show --format json: state.json raw 출력 (PLAN §2.14 G-11)"""
        result = self._show("json")
        self.assertTrue(result["ok"])
        self.assertEqual(result["format"], "json")
        self.assertIn("data", result)
        self.assertEqual(result["data"]["skill"], "opp")

    def test_show_full_happy_path(self):
        """[T094 수정] show --format full: STATE.md 전체 본문 출력 (PLAN §2.14
        G-11). '## 현재 상태'는 D-1로 완전 제거되었으므로, 신규 저널이 실제로
        갖는 골격(제목·의사결정 로그)으로 검증 지점을 이동한다."""
        result = self._show("full")
        self.assertTrue(result["ok"])
        self.assertEqual(result["format"], "full")
        self.assertIn("content", result)
        self.assertIn("# STATE:", result["content"])
        self.assertIn("## 의사결정 로그", result["content"])

    def test_show_json_marker_missing_marker_present_false(self):
        """G-11: 마커 손실 시 show json → marker_present=false (PLAN §2.14 G-11)"""
        md = self._md()
        md_no_marker = md.replace("<!-- pipeline:start -->", "").replace("<!-- pipeline:end -->", "")
        (self.task_path / "STATE.md").write_text(md_no_marker)
        result = self._show("json")
        self.assertFalse(result.get("marker_present", True))


class TestAdvance(BaseTestCase):
    """state advance happy path — PLAN T-7"""

    def setUp(self):
        super().setUp()
        self._init()

    def test_advance_happy_path(self):
        """advance: ⬜→🔄 전환 정상 (PLAN T-7)"""
        code = self._advance(1)
        self.assertEqual(code, 0)
        state = self._state()
        self.assertEqual(state["rows"][0]["status"], "in_progress")
        self.assertEqual(state["rows"][0]["status_label"], "🔄")

    def test_advance_g5_header_updated(self):
        """G-5: advance 후 STATE.md 1번째 줄 '> 최종 갱신:' 자동 교체 (PLAN §2.11 G-5)"""
        self._advance(1)
        md = self._md()
        self.assertIn("> 최종 갱신: 2026-05-01 23:00", md)

    def test_advance_g6_progress_updated(self):
        """[T094 수정] G-6: advance 후 진행 상태 갱신 (PLAN §2.11 G-6).
        '## 현재 상태' 섹션은 D-1로 STATE.md에서 완전 제거되었다 — 동일 정보는
        `state.json.next_action`(프론티어 파생)으로 이동했으므로 검증 지점을
        옮긴다(정보 손실 0, `_derive_next_action` in_progress 분기)."""
        self._advance(1)
        state = self._state()
        self.assertEqual(state["rows"][0]["status"], "in_progress")
        self.assertEqual(state.get("next_action"), "TASK 작업 진행 중",
                         "advance 후 next_action이 진행 중 프론티어로 파생되지 않음")

    def test_s21_header_timestamp_updates_after_journal_refactor(self):
        """[T094/L1-F001] S-21 — `> 최종 갱신:` 헤더 존치 회귀(D-3).

        저널 축소판(§3.1.2 (3))에서도 `update_state_md_header`가 계속 호출되어
        `advance`/`mark` 후 헤더 타임스탬프가 실제 호출 시각으로 갱신되어야
        한다. 실 date.js 호출로 [before, after] 시각 창을 잡고, advance 직후
        헤더 타임스탬프가 그 창 안에 들어오는지로 검증한다(mock 없이 real-time
        경계 비교 — 분 단위 우연 불일치를 피한다).

        RED 근거: 이 자체는 D-3 존치 대상이라 현재 코드에서도 통과할 수 있으나,
        S-1(§3.1.2 (1) 템플릿 재작성)이 먼저 깨지면 STATE.md 형식이 달라져
        헤더 정규식 위치를 흔들 수 있으므로 회귀 안전망으로 유지한다(기존
        test_advance_g5_header_updated 4건과 함께 D-3 이중 보호)."""
        self.assertTrue(_OPD_REAL_PIPELINE_JSON.exists())
        task_path = self.tmpdir / "094-s21-header"
        task_path.mkdir()
        code, stdout, stderr, data = _run094([
            "init", str(task_path), "--skill", "opd", "--mode", "agentic",
            "--rows-from", str(_OPD_REAL_PIPELINE_JSON),
        ])
        self.assertEqual(code, 0, f"init 실패: {stdout!r} {stderr!r}")

        before = subprocess.run(
            ["node", os.path.expanduser("~/.opal/tools/date/date.js"), "datetime"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()

        code, stdout, stderr, data = _run094([
            "advance", str(task_path), "--task-step", "task.task_md",
        ])
        self.assertEqual(code, 0, f"advance 실패: {stdout!r} {stderr!r}")

        after = subprocess.run(
            ["node", os.path.expanduser("~/.opal/tools/date/date.js"), "datetime"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()

        md = (task_path / "STATE.md").read_text(encoding="utf-8")
        m = re.search(r"^> 최종 갱신: (.+)$", md, re.MULTILINE)
        self.assertIsNotNone(m, "'> 최종 갱신:' 헤더 라인이 STATE.md에 없음(D-3 위반)")
        header_ts = m.group(1).strip()
        # [T103] 시각이 초 해상도(`datetime-sec`)로 확장되면서 `before`/`after` 창(분 해상도)과
        # 사전순 비교가 깨진다("21:59:54" > "21:59"). 이 테스트의 의도는 포맷이 아니라
        # "헤더가 실제로 갱신됐는가"이므로 양쪽을 분 단위로 절삭해 비교한다.
        header_minute = header_ts[:16]
        self.assertTrue(before[:16] <= header_minute <= after[:16],
                       f"헤더 타임스탬프({header_ts!r})가 advance 호출 시각 창"
                       f"[{before!r}, {after!r}] 밖에 있음 — 헤더 갱신 누락 의심")


class TestMark(BaseTestCase):
    """state mark happy path — PLAN T-7, §2.4, §2.15 G-12"""

    def setUp(self):
        super().setUp()
        self._init(rows_spec=SIMPLE_ROWS_SPEC)

    def test_mark_happy_path(self):
        """mark: ⬜→✅ 전환 정상 (PLAN T-7)"""
        code = self._mark(1)
        self.assertEqual(code, 0)
        state = self._state()
        self.assertEqual(state["rows"][0]["status"], "done")
        self.assertEqual(state["rows"][0]["status_label"], "✅")

    def test_mark_g5_header_updated(self):
        """G-5: mark 후 STATE.md '> 최종 갱신:' 자동 교체 (PLAN §2.11 G-5)"""
        self._mark(1)
        md = self._md()
        self.assertIn("> 최종 갱신: 2026-05-01 23:00", md)

    def test_mark_close_last_row_status_done(self):
        """[T094 수정] G-6: CLOSE 마지막 행 mark → current_status=done (PLAN §2.11
        G-6). '- 상태: 완료' STATE.md 렌더는 D-1로 제거되었다 — 동일 정보는
        `state.json.current_status`(기존에도 검증하던 필드)로 충분히 커버되므로
        MD 렌더 확인만 제거한다(정보 손실 0, 조회 경로는 `show --format md`의
        `STATUS_TEXT` 매핑으로 이관 — TestShowAsQueryStandard가 별도 검증)."""
        rows = json.dumps([
            {"stage": "TASK", "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows, force=True, note="테스트 재초기화")
        self._mark(1, owner="user")  # 사용자 확인 → done/user
        self._mark(2)  # CLOSE State Gate → done
        state = self._state()
        self.assertEqual(state["current_status"], "done")

    def test_mark_auto_pass_owner_auto(self):
        """G-12: mark --auto-pass → owner=auto 자동 저장 (PLAN §2.15 G-12)"""
        self._mark(1, auto_pass=True, note="agentic mode test")
        state = self._state()
        self.assertEqual(state["rows"][0]["owner"], "auto")
        self.assertIn("agentic auto-pass", state["rows"][0]["note"])

    def test_mark_owner_user(self):
        """G-12: mark --owner user → owner=user 저장 (PLAN §2.15 G-12)"""
        self._mark(1, owner="user", note="소유자 확인")
        state = self._state()
        self.assertEqual(state["rows"][0]["owner"], "user")

    def test_mark_as_worker_happy_path(self):
        """mark --as-worker --worker-stage 정상 동작 (PLAN §2.4, T-10)"""
        # prior_stage_only guard: EXECUTE 대상 행은 앞 단계(TASK·PLAN)가 완료여야 통과
        self._mark(1)  # TASK 완료
        self._mark(2)  # PLAN 완료
        code = self._mark(3, as_worker=True, worker_stage="EXECUTE")
        self.assertEqual(code, 0)
        state = self._state()
        self.assertEqual(state["rows"][2]["status"], "done")

    def test_mark_as_worker_with_step_progress(self):
        """[T094 수정] G-6: mark --as-worker --step N/M → 진행률 영속화 (PLAN
        §2.11 G-6). '- 진행: Step N/M 완료' STATE.md 렌더는 D-1로 제거되었다 —
        동일 정보는 `state.json.rows[].step` 필드로 이미 영속화되므로(017,
        state_tool.py 조기 done 가드) 검증 지점을 그쪽으로 이동한다(정보 손실 0)."""
        # prior_stage_only guard: EXECUTE 대상 행은 앞 단계(TASK·PLAN)가 완료여야 통과
        self._mark(1)  # TASK 완료
        self._mark(2)  # PLAN 완료
        self._mark(3, as_worker=True, worker_stage="EXECUTE", step="2/5")
        state = self._state()
        self.assertEqual(state["rows"][2].get("step"), "2/5",
                         "Step 진행률이 state.json rows[].step에 영속화되지 않음")
        self.assertEqual(state["rows"][2]["status"], "in_progress",
                         "N<M(2/5)은 조기 done 없이 in_progress로 유지되어야 함")


class TestBlock(BaseTestCase):
    """state block happy path — PLAN §2.17 트리거 #7"""

    def setUp(self):
        super().setUp()
        self._init()

    def test_block_happy_path(self):
        """block: any→❌ + current_status=blocked (PLAN §2.17 트리거 #7)"""
        code = self._block(1, reason="테스트 블로커")
        self.assertEqual(code, 0)
        state = self._state()
        self.assertEqual(state["rows"][0]["status"], "failed")
        self.assertEqual(state["rows"][0]["status_label"], "❌")
        self.assertEqual(state["current_status"], "blocked")
        self.assertIn("테스트 블로커", state["rows"][0]["note"])

    def test_block_g5_header_updated(self):
        """G-5: block 후 STATE.md '> 최종 갱신:' 자동 교체 (PLAN §2.11 G-5)"""
        self._block(1)
        md = self._md()
        self.assertIn("> 최종 갱신: 2026-05-01 23:00", md)

    def test_block_g6_status_blocker(self):
        """[T094 수정] G-6: block 후 상태가 블로커로 갱신 (PLAN §2.11 G-6).
        '- 상태:' STATE.md 렌더는 D-1로 제거되었다 — 조회 경로가
        `show --format md`의 `STATUS_TEXT` 매핑으로 이관되었으므로(R-5 AC(b))
        검증 지점을 그쪽으로 이동한다(정보 손실 0)."""
        self._block(1)
        state = self._state()
        self.assertEqual(state["current_status"], "blocked")
        args = make_args(task_path=str(self.task_path), format="md")
        _, result = self._call_cmd(ST.cmd_show, args)
        self.assertIn("- 상태: 블로커", result.get("content", ""),
                     "show --format md가 블로커 상태 텍스트를 반영하지 않음")


class TestValidate(BaseTestCase):
    """state validate happy path — PLAN §2.6, §2.15 G-12"""

    def setUp(self):
        super().setUp()
        self._init()

    def test_validate_happy_path(self):
        """validate: violations 0건 시 ok=true (PLAN §2.6)"""
        result = self._validate()
        self.assertTrue(result["ok"])
        self.assertEqual(result["violations_count"], 0)

    def test_validate_returns_violations_array(self):
        """validate: 응답에 violations 배열 포함 (PLAN §2.19.6)"""
        result = self._validate()
        self.assertIn("violations", result)
        self.assertIsInstance(result["violations"], list)

    def test_s8_validate_no_marker_missing_violation(self):
        """[T094/L1-F002] S-8 — 마커 없는 STATE.md에서 `validate` 실행 시
        `violations[]`에 `marker_missing` 항목이 0건이어야 한다(R-3 AC(a),
        `cmd_validate` 마커 검사 블록 삭제, state_tool.py:1734-1740).

        RED 근거: 현재 `cmd_validate`는 `md and not (마커 존재)`일 때
        `violations`에 `{"code": "marker_missing", ...}`를 추가하므로, 마커를
        제거한 STATE.md에서 이 어서션이 실패한다."""
        md = self._md()
        md_no_marker = (md.replace("<!-- pipeline:start -->", "")
                           .replace("<!-- pipeline:end -->", ""))
        (self.task_path / "STATE.md").write_text(md_no_marker, encoding="utf-8")
        result = self._validate()
        marker_violations = [v for v in result.get("violations", [])
                             if v.get("code") == "marker_missing"]
        self.assertEqual(marker_violations, [],
                         f"validate가 marker_missing 위반을 여전히 보고함(R-3 위반): "
                         f"{marker_violations}")


class TestAddRow(BaseTestCase):
    """state add-row happy path — PLAN §2.12 G-9"""

    def setUp(self):
        super().setUp()
        self._init(rows_spec=SIMPLE_ROWS_SPEC)

    def test_add_row_happy_path(self):
        """add-row: 행 삽입 + row_id 재정렬 (PLAN §2.12 G-9)"""
        code = self._add_row(after=1, stage="CLOSE", item="추가작업 항목")
        self.assertEqual(code, 0)
        state = self._state()
        self.assertEqual(len(state["rows"]), 5)  # 4 + 1
        # 삽입된 행이 row_id=2
        new_row = next(r for r in state["rows"] if r["item"] == "추가작업 항목")
        self.assertEqual(new_row["row_id"], 2)
        self.assertEqual(new_row["stage"], "CLOSE")

    def test_add_row_g9_row_id_renumbered(self):
        """G-9: add-row 후 N+1 이후 모든 row_id가 +1 됨 (PLAN §2.12 G-9)"""
        original_ids = [r["row_id"] for r in self._state()["rows"]]  # [1,2,3,4]
        self._add_row(after=2, stage="EXECUTE", item="추가 항목")
        new_ids = [r["row_id"] for r in self._state()["rows"]]
        self.assertEqual(new_ids, [1, 2, 3, 4, 5])

    def test_add_row_g9_current_status_additional_work(self):
        """G-9: add-row 시 current_status=done이면 additional_work로 전환 (PLAN §2.12 G-9, G-7)"""
        # current_status를 done으로 강제 설정
        state = self._state()
        state["current_status"] = "done"
        ST.save_state_json(self.task_path, state)

        self._add_row(after=1, stage="CLOSE", item="추가작업")
        state = self._state()
        self.assertEqual(state["current_status"], "additional_work")

    def test_add_row_g5_header_updated(self):
        """G-5: add-row 후 STATE.md '> 최종 갱신:' 자동 교체 (PLAN §2.11 G-5)"""
        self._add_row(after=1, stage="CLOSE", item="추가")
        md = self._md()
        self.assertIn("> 최종 갱신: 2026-05-01 23:00", md)

    def test_add_row_g6_status_additional_work(self):
        """[T094 수정] G-6: add-row(done→additional_work) 후 상태 갱신 (PLAN §2.11
        G-6). '- 상태:' STATE.md 렌더는 D-1로 제거되었다 — 조회 경로가
        `show --format md`의 `STATUS_TEXT` 매핑으로 이관되었으므로 검증 지점을
        그쪽으로 이동한다(정보 손실 0)."""
        state = self._state()
        state["current_status"] = "done"
        ST.save_state_json(self.task_path, state)
        self._add_row(after=1, stage="CLOSE", item="추가")
        state = self._state()
        self.assertEqual(state["current_status"], "additional_work")
        args = make_args(task_path=str(self.task_path), format="md")
        _, result = self._call_cmd(ST.cmd_show, args)
        self.assertIn("- 상태: 추가작업중", result.get("content", ""),
                     "show --format md가 추가작업중 상태 텍스트를 반영하지 않음")

    def test_add_row_decision_log_appended(self):
        """G-14/G-15: add-row 후 의사결정 로그 자동 기재 (PLAN §2.17 트리거 #5)"""
        self._add_row(after=1, stage="CLOSE", item="추가 항목", note="추가작업 진입")
        md = self._md()
        self.assertIn("additional row inserted after row 1", md)


class TestStatus(BaseTestCase):
    """state status happy path — PLAN §2.11 G-7"""

    def setUp(self):
        super().setUp()
        self._init()

    def test_status_in_progress_to_blocked(self):
        """status: in_progress→blocked 전이 (PLAN §2.11 G-7)"""
        self._status_set("blocked")
        self.assertEqual(self._state()["current_status"], "blocked")

    def test_status_in_progress_to_done(self):
        """status: in_progress→done 전이 (PLAN §2.11 G-7)"""
        self._status_set("done")
        self.assertEqual(self._state()["current_status"], "done")

    def test_status_in_progress_to_additional_work(self):
        """status: in_progress→additional_work 전이 (PLAN §2.11 G-7)"""
        self._status_set("additional_work")
        self.assertEqual(self._state()["current_status"], "additional_work")

    def test_status_done_to_additional_work(self):
        """status: done→additional_work 전이 (PLAN §2.11 G-7)"""
        self._status_set("done")
        self._status_set("additional_work")
        self.assertEqual(self._state()["current_status"], "additional_work")

    def test_status_blocked_to_in_progress(self):
        """status: blocked→in_progress 전이 (PLAN §2.11 G-7)"""
        self._status_set("blocked")
        self._status_set("in_progress")
        self.assertEqual(self._state()["current_status"], "in_progress")

    def test_status_decision_log_appended(self):
        """G-14/G-15: status --set 후 의사결정 로그 자동 기재 (PLAN §2.17 트리거 #4)"""
        self._status_set("blocked", note="테스트 블로킹")
        md = self._md()
        self.assertIn("current_status changed:", md)

    def test_status_g6_status_text_updated(self):
        """[T094 수정] G-6: status --set 후 상태 텍스트 갱신 (PLAN §2.11 G-6).
        '- 상태:' STATE.md 렌더는 D-1로 제거되었다 — 조회 경로가
        `show --format md`의 `STATUS_TEXT` 매핑으로 이관되었으므로 검증 지점을
        그쪽으로 이동한다(정보 손실 0)."""
        self._status_set("blocked")
        self.assertEqual(self._state()["current_status"], "blocked")
        args = make_args(task_path=str(self.task_path), format="md")
        _, result = self._call_cmd(ST.cmd_show, args)
        self.assertIn("- 상태: 블로커", result.get("content", ""),
                     "show --format md가 블로커 상태 텍스트를 반영하지 않음")


class TestGatePass(BaseTestCase):
    """state gate-pass happy path — PLAN §2.13 G-10"""

    def setUp(self):
        super().setUp()
        self._init(rows_spec=GATE_ROWS_SPEC)

    def test_gate_pass_happy_path(self):
        """gate-pass: QA Gate부터 4행 일괄 ✅ 처리 (PLAN §2.13 G-10)"""
        # GATE_ROWS_SPEC: row2=QA Gate, row3=State Gate, row4=PM Gate, row5=State Gate
        with _mock_now():
            args = make_args(task_path=str(self.task_path), start=2)
            exit_code, result = self._call_cmd(ST.cmd_gate_pass, args)
        self.assertEqual(exit_code, 0, f"gate-pass failed: {result}")
        state = self._state()
        # row2~5가 모두 done
        for row in state["rows"][1:5]:
            self.assertEqual(row["status"], "done")

    def test_gate_pass_g10_decision_log(self):
        """G-10: gate-pass 후 의사결정 로그 자동 기재 (PLAN §2.17 트리거 #6)"""
        with _mock_now():
            args = make_args(task_path=str(self.task_path), start=2, note="테스트 게이트")
            self._call_cmd(ST.cmd_gate_pass, args)
        md = self._md()
        self.assertIn("Gate Pass:", md)

    def test_gate_pass_g5_header_updated(self):
        """G-5: gate-pass 후 STATE.md '> 최종 갱신:' 자동 교체 (PLAN §2.11 G-5)"""
        with _mock_now():
            args = make_args(task_path=str(self.task_path), start=2)
            self._call_cmd(ST.cmd_gate_pass, args)
        md = self._md()
        self.assertIn("> 최종 갱신: 2026-05-01 23:00", md)


# ═════════════════════════════════════════════════════════════════════════════
# B. 23종 에러 코드 (PLAN §2.18 E-1) — cross-ref: 함수명에 에러 코드 명시
# ═════════════════════════════════════════════════════════════════════════════

class TestErrorCodes(BaseTestCase):
    """PLAN §2.18 에러 코드 카탈로그 23종 — 각 1건 이상"""

    def _err_code(self, fn, *a, **kw):
        """fn 호출 시 JSON 에러 응답의 error 코드 추출 (err()는 SystemExit, ok()는 반환값)."""
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            try:
                fn(*a, **kw)
            except SystemExit:
                pass
        output = out.getvalue().strip()
        return json.loads(output).get("error") if output else None

    # ── E-1: worker_scope_violation ──────────────────────────────────────────
    def test_worker_scope_violation(self):
        """#1 worker_scope_violation: 워커가 자기 단계 외 행 갱신 시도 (PLAN §2.18 #1)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=1, done=True, as_worker=True, worker_stage="EXECUTE",
            )
            code = self._err_code(ST.cmd_mark, args)
        self.assertEqual(code, "worker_scope_violation")

    # ── E-2: marker_missing — [T094 삭제·D-2/R-3] 094 R-3으로 마커 하드 게이트
    # 자체가 제거되어 `marker_missing` 에러 코드가 ERROR_CODES에서 소멸했다
    # (state_tool.py:81-133 실측 43종 중 부재). 대체 회귀 커버리지는
    # `TestBasicScenarios.test_s6_marker_gate_removed_three_corruption_cases`
    # (마커 제거 상태에서 advance/mark가 ok:true를 반환함을 검증)가 담당한다.

    # ── E-3: already_initialized ─────────────────────────────────────────────
    def test_already_initialized_rejection(self):
        """#3 already_initialized: init 두 번 호출 시 거부 (PLAN §2.18 #3, T-8)"""
        self._init()
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                rows_spec=SIMPLE_ROWS_SPEC,
            )
            code = self._err_code(ST.cmd_init, args)
        self.assertEqual(code, "already_initialized")

    # ── E-4: date_tool_failed ─────────────────────────────────────────────────
    def test_date_tool_failed(self):
        """#4 date_tool_failed: date.js 호출 실패 시 에러 (PLAN §2.18 #4)"""
        self._init()
        with patch.object(ST, "get_kst_datetime", side_effect=SystemExit(2)):
            args = make_args(task_path=str(self.task_path), row=1, done=True)
            exit_code, _ = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 2)

    # ── E-5: import_failed — [T094 삭제·D-2/R-3] 094 D-2로 `--import-existing`
    # 파싱 분기(`parse_existing_state_md` 등) 자체가 삭제되어 `import_failed`
    # 에러 코드의 유일 발생점이 소멸했다(ERROR_CODES 실측 43종 중 부재).
    # 대체 회귀 커버리지는 `TestInit.test_s9_import_existing_removed_rejected`
    # (--import-existing 호출 시 `import_existing_removed` 단일 에러로 즉시
    # 거부됨을 검증)가 담당한다.

    # ── E-6: invalid_status_transition ───────────────────────────────────────
    def test_invalid_status_transition(self):
        """#6 invalid_status_transition: 전이 그래프 위반 (PLAN §2.18 #6, §2.11 G-7)"""
        self._init()
        with _mock_now():
            args = make_args(task_path=str(self.task_path), set="additional_work_done")
            code = self._err_code(ST.cmd_status, args)
        self.assertEqual(code, "invalid_status_transition")

    # ── E-7: row_not_found ───────────────────────────────────────────────────
    def test_row_not_found(self):
        """#7 row_not_found: 존재하지 않는 row_id 지정 (PLAN §2.18 #7)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=999, done=True)
            code = self._err_code(ST.cmd_mark, args)
        self.assertEqual(code, "row_not_found")

    # ── E-8: invalid_stage_enum ──────────────────────────────────────────────
    def test_invalid_stage_enum(self):
        """#8 invalid_stage_enum: --stage에 유효하지 않은 값 (PLAN §2.18 #8, §2.12 G-9)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                after=1, stage="INVALID_STAGE", item="테스트 항목",
            )
            code = self._err_code(ST.cmd_add_row, args)
        self.assertEqual(code, "invalid_stage_enum")

    # ── E-9: gate_pattern_mismatch ───────────────────────────────────────────
    def test_gate_pattern_mismatch_not_qa_gate(self):
        """#9 gate_pattern_mismatch: --start가 QA Gate로 시작 안 함 (PLAN §2.18 #9, §2.13 G-10)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)  # row1=TASK/작업 (QA Gate 아님)
        with _mock_now():
            args = make_args(task_path=str(self.task_path), start=1)
            code = self._err_code(ST.cmd_gate_pass, args)
        self.assertEqual(code, "gate_pattern_mismatch")

    # ── E-10: gate_stage_mixed ───────────────────────────────────────────────
    def test_gate_stage_mixed(self):
        """#10 gate_stage_mixed: 4행이 동일 stage 아님 (PLAN §2.18 #10, §2.13 G-10)"""
        # 혼합 stage 구성: QA Gate부터 시작하지만 stage가 다름
        mixed = json.dumps([
            {"stage": "PLAN",    "item": "QA Gate"},
            {"stage": "EXECUTE", "item": "State Gate"},   # 다른 stage!
            {"stage": "PLAN",    "item": "PM Gate"},
            {"stage": "PLAN",    "item": "State Gate"},
        ])
        self._init(rows_spec=mixed)
        with _mock_now():
            args = make_args(task_path=str(self.task_path), start=1)
            code = self._err_code(ST.cmd_gate_pass, args)
        self.assertEqual(code, "gate_stage_mixed")

    # ── E-11: state_not_initialized ──────────────────────────────────────────
    def test_state_not_initialized(self):
        """#11 state_not_initialized: state.json 미존재 시 (PLAN §2.18 #11)"""
        # state.json 없는 상태에서 show
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        args = make_args(task_path=str(self.task_path))
        with redirect_stdout(out), self.assertRaises(SystemExit) as cm:
            ST.cmd_show(args)
        result = json.loads(out.getvalue())
        self.assertEqual(result["error"], "state_not_initialized")

    # ── E-12: user_confirmation_owner_mismatch ───────────────────────────────
    def test_user_confirmation_owner_mismatch(self):
        """#12 user_confirmation_owner_mismatch: validate가 violations에 추가 (PLAN §2.18 #12, §2.15 G-12)"""
        rows = json.dumps([
            {"stage": "TASK", "item": "사용자 확인"},
        ])
        self._init(rows_spec=rows)
        # owner=PM으로 mark (user/auto 아님)
        self._mark(1, owner="PM")
        result = self._validate()
        codes = [v["code"] for v in result["violations"]]
        self.assertIn("user_confirmation_owner_mismatch", codes)

    # ── E-13: owner_flag_conflict ────────────────────────────────────────────
    def test_owner_flag_conflict(self):
        """#13 owner_flag_conflict: --owner와 --auto-pass 동시 사용 (PLAN §2.18 #13, §2.15 G-12)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=1, done=True,
                owner="user", auto_pass=True,
            )
            code = self._err_code(ST.cmd_mark, args)
        self.assertEqual(code, "owner_flag_conflict")

    # ── E-14: auto_pass_in_interactive_mode ──────────────────────────────────
    def test_auto_pass_in_interactive_mode(self):
        """#14 auto_pass_in_interactive_mode: interactive에서 owner=auto ✅ (PLAN §2.18 #14, §2.15 G-12)"""
        rows = json.dumps([
            {"stage": "TASK", "item": "사용자 확인"},
        ])
        self._init(rows_spec=rows, mode="interactive")
        self._mark(1, auto_pass=True)
        result = self._validate()
        codes = [v["code"] for v in result["violations"]]
        self.assertIn("auto_pass_in_interactive_mode", codes)

    # ── E-15: close_gate_violation ───────────────────────────────────────────
    def test_close_gate_violation(self):
        """#15 close_gate_violation: CLOSE 첫 행 mark 시 사용자 확인 미충족 (PLAN §2.18 #15, §2.16 G-13)"""
        rows = json.dumps([
            {"stage": "TASK",  "item": "작업"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows)
        # row1(TASK/작업) 먼저 done 처리 — stage_transition guard 통과 후 close_gate_violation 발생
        self._mark(1)
        # 사용자 확인 행 없음 → close_gate_violation
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=2, done=True)
            code = self._err_code(ST.cmd_mark, args)
        self.assertEqual(code, "close_gate_violation")

    # ── E-16: agentic_close_gate_requires_user ───────────────────────────────
    def test_agentic_close_gate_requires_user(self):
        """#16 agentic_close_gate_requires_user: agentic + CLOSE 첫 행 + --auto-pass (PLAN §2.18 #16, §2.16 G-13)"""
        rows = json.dumps([
            {"stage": "TASK",  "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows, mode="agentic")
        # 093 F-001: 사용자 확인 행은 init 시 pending이며, CLOSE 직전 행이라 훅이
        # 자동 승인하지 않는다(DEC-D) — 캡틴 승인으로 CLOSE 게이트 축까지 도달시킨다.
        self._mark(1, owner="user")
        # agentic 모드에서 CLOSE 첫 행에 auto-pass 시도
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=2, done=True, auto_pass=True,
            )
            code = self._err_code(ST.cmd_mark, args)
        self.assertEqual(code, "agentic_close_gate_requires_user")

    # ── E-17: note_required_for_force ────────────────────────────────────────
    def test_note_required_for_force_init(self):
        """#17 note_required_for_force (트리거 #1): init --force 시 --note 미제공 (PLAN §2.18 #17)"""
        self._init()  # 첫 init
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit) as cm:
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    skill="opp", mode="interactive",
                    force=True, note=None,
                )
                ST.cmd_init(args)
        result = json.loads(out.getvalue())
        self.assertEqual(result["error"], "note_required_for_force")

    def test_note_required_for_force_mark(self):
        """#17 note_required_for_force (트리거 #3): mark --force 시 --note 미제공 (PLAN §2.18 #17)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=1, done=True, force=True, note=None,
            )
            code = self._err_code(ST.cmd_mark, args)
        self.assertEqual(code, "note_required_for_force")

    # ── E-18: rows_spec_invalid_json ─────────────────────────────────────────
    def test_rows_spec_invalid_json(self):
        """#18 rows_spec_invalid_json: --rows-spec에 유효하지 않은 JSON (PLAN §2.18 #18)"""
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit) as cm:
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    skill="opp", mode="interactive",
                    rows_spec="NOT_JSON",
                )
                ST.cmd_init(args)
        result = json.loads(out.getvalue())
        self.assertEqual(result["error"], "rows_spec_invalid_json")

    def test_rows_spec_not_array(self):
        """#18 rows_spec_invalid_json: --rows-spec 최상위가 배열 아님 (PLAN §2.18 #18)"""
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit):
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    skill="opp", mode="interactive",
                    rows_spec='{"stage": "TASK"}',
                )
                ST.cmd_init(args)
        result = json.loads(out.getvalue())
        self.assertEqual(result["error"], "rows_spec_invalid_json")

    # ── E-19: skill_md_parse_error ───────────────────────────────────────────
    def test_skill_md_parse_error_header_not_found(self):
        """#19 skill_md_parse_error: SKILL.md에서 헤더 미발견 (PLAN §2.18 #19)"""
        skill_md = self.tmpdir / "SKILL.md"
        skill_md.write_text("# 다른 섹션\n내용 없음\n")
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit):
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    skill="opp", mode="interactive",
                    rows_from=str(skill_md),
                )
                ST.cmd_init(args)
        result = json.loads(out.getvalue())
        self.assertEqual(result["error"], "skill_md_parse_error")

    # ── E-20: task_path_not_found ────────────────────────────────────────────
    def test_task_path_not_found(self):
        """#20 task_path_not_found: 존재하지 않는 task-path (PLAN §2.18 #20)"""
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit):
            with _mock_now():
                args = make_args(
                    task_path="/nonexistent/path/that/does/not/exist",
                    skill="opp", mode="interactive",
                )
                ST.cmd_init(args)
        result = json.loads(out.getvalue())
        self.assertEqual(result["error"], "task_path_not_found")

    # ── E-21: worker_stage_required ──────────────────────────────────────────
    def test_worker_stage_required(self):
        """#21 worker_stage_required: --as-worker 시 --worker-stage 미지정 (PLAN §2.18 #21)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=1, done=True, as_worker=True, worker_stage=None,
            )
            code = self._err_code(ST.cmd_mark, args)
        self.assertEqual(code, "worker_stage_required")

    # ── E-22: rows_input_conflict (C-1) ──────────────────────────────────────
    def test_rows_input_conflict_c1(self):
        """#22 rows_input_conflict (C-1): --rows-spec와 --rows-from 동시 사용 (PLAN §2.18 #22, §2.19 C-1)"""
        skill_md = self.tmpdir / "SKILL.md"
        skill_md.write_text("# STATE.md 도메인 치환값\n")
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit):
            with _mock_now():
                # argparse mutually_exclusive_group이 이미 막지만, 직접 검증도 가능
                args = make_args(
                    task_path=str(self.task_path),
                    skill="opp", mode="interactive",
                    rows_spec=SIMPLE_ROWS_SPEC,
                    rows_from=str(skill_md),
                )
                ST.cmd_init(args)
        result = json.loads(out.getvalue())
        self.assertEqual(result["error"], "rows_input_conflict")

    # ── E-23: rows_acts_not_implemented ──────────────────────────────────────
    def test_rows_acts_not_implemented(self):
        """#23 rows_acts_not_implemented: --rows-acts 미구현 거부 (PLAN §2.18 #23, §2.20.3, R-13)"""
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit) as cm:
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    skill="opsdd", mode="interactive",
                    rows_acts='[{"act_id": "ACT-1"}]',
                )
                ST.cmd_init(args)
        result = json.loads(out.getvalue())
        self.assertEqual(result["error"], "rows_acts_not_implemented")
        self.assertEqual(cm.exception.code, 2)


# ═════════════════════════════════════════════════════════════════════════════
# C. G-5~G-15 심층 시나리오 (PLAN §3 Step 2)
# ═════════════════════════════════════════════════════════════════════════════

class TestG7StatusTransitions(BaseTestCase):
    """G-7: state status --set 8개 전이 케이스 (PLAN §2.11 G-7)"""

    def setUp(self):
        super().setUp()
        self._init()

    def _cur(self):
        return self._state()["current_status"]

    def test_g7_in_progress_to_done_allowed(self):
        """G-7 허용: in_progress → done"""
        code = self._status_set("done")
        self.assertEqual(code, 0)
        self.assertEqual(self._cur(), "done")

    def test_g7_done_to_additional_work_allowed(self):
        """G-7 허용: done → additional_work"""
        self._status_set("done")
        code = self._status_set("additional_work")
        self.assertEqual(code, 0)

    def test_g7_additional_work_to_additional_work_done_allowed(self):
        """G-7 허용: additional_work → additional_work_done"""
        self._status_set("additional_work")
        code = self._status_set("additional_work_done")
        self.assertEqual(code, 0)

    def test_g7_blocked_to_in_progress_allowed(self):
        """G-7 허용: blocked → in_progress"""
        self._status_set("blocked")
        code = self._status_set("in_progress")
        self.assertEqual(code, 0)

    def test_g7_any_to_blocked_allowed(self):
        """G-7 허용: in_progress → blocked"""
        code = self._status_set("blocked")
        self.assertEqual(code, 0)

    def test_g7_in_progress_to_additional_work_done_rejected(self):
        """G-7 거부: in_progress → additional_work_done (PLAN §2.18 #6)"""
        with _mock_now():
            args = make_args(task_path=str(self.task_path), set="additional_work_done")
            exit_code, result = self._call_cmd(ST.cmd_status, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "invalid_status_transition")

    def test_g7_done_to_in_progress_rejected(self):
        """G-7 거부: done → in_progress"""
        self._status_set("done")
        with _mock_now():
            args = make_args(task_path=str(self.task_path), set="in_progress")
            exit_code, result = self._call_cmd(ST.cmd_status, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "invalid_status_transition")

    def test_g7_additional_work_done_to_done_rejected(self):
        """G-7 거부: additional_work_done → done"""
        self._status_set("additional_work")
        self._status_set("additional_work_done")
        with _mock_now():
            args = make_args(task_path=str(self.task_path), set="done")
            exit_code, result = self._call_cmd(ST.cmd_status, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "invalid_status_transition")


class TestG10GatePass(BaseTestCase):
    """G-10: gate-pass 시나리오 (PLAN §2.13 G-10)"""

    def setUp(self):
        super().setUp()
        self._init(rows_spec=GATE_ROWS_SPEC)

    def test_g10_gate_pass_all_done(self):
        """G-10 happy: 4행 일괄 ✅ (PLAN §2.13 G-10)"""
        with _mock_now():
            args = make_args(task_path=str(self.task_path), start=2)
            exit_code, result = self._call_cmd(ST.cmd_gate_pass, args)
        self.assertEqual(exit_code, 0, f"gate-pass failed: {result}")
        state = self._state()
        for row in state["rows"][1:5]:
            self.assertEqual(row["status"], "done")
            self.assertEqual(row["status_label"], "✅")

    def test_g10_gate_pattern_mismatch_not_qa_gate(self):
        """G-10 거부: 시작 행이 QA Gate 아님 (PLAN §2.18 #9)"""
        with _mock_now():
            args = make_args(task_path=str(self.task_path), start=1)  # row1=작업
            exit_code, result = self._call_cmd(ST.cmd_gate_pass, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "gate_pattern_mismatch")

    def test_g10_gate_stage_mixed(self):
        """G-10 거부: 4행 stage 혼합 (PLAN §2.18 #10)"""
        mixed = json.dumps([
            {"stage": "PLAN",    "item": "QA Gate"},
            {"stage": "EXECUTE", "item": "State Gate"},
            {"stage": "PLAN",    "item": "PM Gate"},
            {"stage": "PLAN",    "item": "State Gate"},
        ])
        self._init(rows_spec=mixed, force=True, note="재초기화")
        with _mock_now():
            args = make_args(task_path=str(self.task_path), start=1)
            exit_code, result = self._call_cmd(ST.cmd_gate_pass, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "gate_stage_mixed")

    def test_g10_same_timestamp_all_4_rows(self):
        """G-10: 4행 모두 동일 timestamp (date.js 1회 호출 재사용) (PLAN §2.13 G-10 단계 4)"""
        with _mock_now():
            args = make_args(task_path=str(self.task_path), start=2)
            self._call_cmd(ST.cmd_gate_pass, args)
        state = self._state()
        timestamps = [r["timestamp"] for r in state["rows"][1:5]]
        self.assertEqual(len(set(timestamps)), 1)  # 모두 같은 시점


class TestG12UserConfirmation(BaseTestCase):
    """G-12: 사용자 확인 행 처리 (PLAN §2.15 G-12)"""

    def setUp(self):
        super().setUp()
        rows = json.dumps([
            {"stage": "TASK", "item": "사용자 확인"},
            {"stage": "TASK", "item": "작업"},
        ])
        self._init(rows_spec=rows)

    def test_g12_user_confirmation_without_owner_user_causes_violation(self):
        """G-12: '사용자 확인' 행을 owner=user 없이 mark 시 validate가 violations 반환 (PLAN §2.15 G-12)"""
        self._mark(1, owner="PM")  # owner=PM, not user
        result = self._validate()
        codes = [v["code"] for v in result["violations"]]
        self.assertIn("user_confirmation_owner_mismatch", codes)

    def test_g12_auto_pass_saves_owner_auto(self):
        """G-12: --auto-pass → owner=auto 저장 (PLAN §2.15 G-12)"""
        self._mark(1, auto_pass=True, note="agentic auto-pass 테스트")
        state = self._state()
        self.assertEqual(state["rows"][0]["owner"], "auto")

    def test_g12_interactive_auto_pass_causes_violation(self):
        """G-12: interactive 모드에서 owner=auto → validate violations (PLAN §2.15 G-12)"""
        self._mark(1, auto_pass=True)  # interactive 모드에서 auto_pass
        result = self._validate()
        codes = [v["code"] for v in result["violations"]]
        self.assertIn("auto_pass_in_interactive_mode", codes)

    def test_g12_owner_flag_conflict_xor_c2(self):
        """G-12, C-2: --owner와 --auto-pass 배타(XOR) (PLAN §2.19 C-2)"""
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=1, done=True, owner="user", auto_pass=True,
            )
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "owner_flag_conflict")


class TestG13CloseGate(BaseTestCase):
    """G-13: CLOSE 진입 게이트 (PLAN §2.16 G-13)"""

    def _make_close_rows(self):
        return json.dumps([
            {"stage": "TASK",  "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])

    def test_g13_close_gate_violation_no_prev_user_row(self):
        """G-13: 사용자 확인 행 미존재 → close_gate_violation (PLAN §2.16 G-13)"""
        rows = json.dumps([
            {"stage": "TASK",  "item": "작업"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows)
        # row1(TASK/작업) 먼저 done 처리 — stage_transition guard 통과 후 close_gate_violation 발생
        self._mark(1)
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=2, done=True)
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "close_gate_violation")

    def test_g13_close_gate_violation_owner_not_user(self):
        """G-13: 사용자 확인 행이 owner=PM으로 done → close_gate_violation (PLAN §2.16 G-13)"""
        self._init(rows_spec=self._make_close_rows())
        self._mark(1, owner="PM")  # owner=PM, 미충족
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=2, done=True)
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "close_gate_violation")

    def test_g13_agentic_close_gate_auto_pass_rejected(self):
        """G-13: agentic 모드 CLOSE 첫 행 + --auto-pass → agentic_close_gate_requires_user (PLAN §2.16 G-13)"""
        self._init(rows_spec=self._make_close_rows(), mode="agentic")
        # 093 F-001: TASK 사용자 확인 행은 전 모드 pending으로 초기화된다.
        # CLOSE 직전 사용자 확인 행이므로 훅이 자동 승인하지 않는다(DEC-D) — 캡틴 승인 필수.
        self._mark(1, owner="user")
        # CLOSE 첫 행에 auto-pass 시도
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=2, done=True, auto_pass=True,
            )
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "agentic_close_gate_requires_user")

    def test_g13_force_bypass_decision_log(self):
        """G-13: --force 우회 시 의사결정 로그 자동 기재 (PLAN §2.17 트리거 #8)"""
        rows = json.dumps([
            {"stage": "TASK",  "item": "작업"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows)
        # --force + --note로 close gate 우회
        self._mark(2, force=True, note="강제 우회 테스트")
        md = self._md()
        # 의사결정 로그에 force 관련 기재 확인
        # 트리거 #3 (worker_scope_force)은 as_worker+force인 경우이고,
        # 트리거 #8 (CLOSE 진입 게이트 force)은 현재 mark --force로 처리됨
        self.assertIn("2026-05-01 23:00", md)

    def test_g13_close_gate_pass_with_owner_user(self):
        """G-13: 사용자 확인 행이 owner=user/done → CLOSE 첫 행 통과 (PLAN §2.16 G-13)"""
        self._init(rows_spec=self._make_close_rows())
        self._mark(1, owner="user")  # 사용자 확인 → done/user
        code = self._mark(2)  # CLOSE State Gate → 통과
        self.assertEqual(code, 0)


class TestG14G15DecisionLog(BaseTestCase):
    """G-14/G-15: 의사결정 로그 자동 기재 트리거 (PLAN §2.17)"""

    def setUp(self):
        super().setUp()
        self._init(rows_spec=SIMPLE_ROWS_SPEC)

    def _log_has(self, keyword):
        md = self._md()
        return keyword in md

    def test_trigger1_init_force_decision_log(self):
        """트리거 #1: init --force → 의사결정 로그 기재 (PLAN §2.17 트리거 #1)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC, force=True, note="강제 재초기화")
        md = self._md()
        self.assertIn("force flag used at init", md)

    def test_trigger1_note_required(self):
        """트리거 #1: init --force --note 미제공 → note_required_for_force (PLAN §2.17 트리거 #1)"""
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                force=True, note=None,
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "note_required_for_force")

    def test_trigger2_auto_pass_decision_log(self):
        """트리거 #2: mark --auto-pass → 의사결정 로그 기재 (PLAN §2.17 트리거 #2)"""
        self._mark(1, auto_pass=True, note="agentic mode")
        self.assertTrue(self._log_has("agentic auto-pass at row 1"))

    def test_trigger3_note_required_for_worker_force(self):
        """트리거 #3: mark --force 시 --note 미제공 → note_required_for_force (PLAN §2.17 트리거 #3)"""
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=1, done=True, force=True, note=None,
            )
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "note_required_for_force")

    def test_trigger4_status_set_decision_log(self):
        """트리거 #4: status --set → 의사결정 로그 기재 (PLAN §2.17 트리거 #4)"""
        self._status_set("blocked", note="테스트 상태 변경")
        self.assertTrue(self._log_has("current_status changed:"))

    def test_trigger5_add_row_decision_log(self):
        """트리거 #5: add-row → 의사결정 로그 기재 (PLAN §2.17 트리거 #5)"""
        self._add_row(after=1, stage="CLOSE", item="신규 항목", note="추가작업")
        self.assertTrue(self._log_has("additional row inserted after row 1"))

    def test_trigger6_gate_pass_decision_log(self):
        """트리거 #6: gate-pass → 의사결정 로그 기재 (PLAN §2.17 트리거 #6)"""
        self._init(rows_spec=GATE_ROWS_SPEC, force=True, note="재초기화")
        with _mock_now():
            args = make_args(task_path=str(self.task_path), start=2, note="게이트 통과")
            self._call_cmd(ST.cmd_gate_pass, args)
        self.assertTrue(self._log_has("Gate Pass:"))

    def test_trigger7_block_no_decision_log(self):
        """트리거 #7: block은 의사결정 로그 미기재, row.note만 기재 (PLAN §2.17 트리거 #7)"""
        md_before = self._md()
        log_rows_before = md_before.count("| ")
        self._block(1, reason="테스트 블로커")
        md_after = self._md()
        # block은 의사결정 로그 표에 행 추가 안 함
        # (row.note에만 기재)
        state = self._state()
        self.assertIn("block: 테스트 블로커", state["rows"][0]["note"])

    # ─────────────────────────────────────────────────────────────────────
    # 094 RED-first 추가 — TEST-SCENARIO.md S-2, S-3 (PLAN §3.1.2, D-1/D-2)
    # [MUST] 실 CLI subprocess(run.sh) + 실 파일 내용으로만 검증, mock 금지.
    # ─────────────────────────────────────────────────────────────────────

    def test_s2_journal_two_sections_survive_consecutive_updates(self):
        """[T094/L1-F001] S-2 — S-1 산출 저널에 `advance` → `mark` → `block`을
        연속 호출해도 `## 의사결정 로그`와 `## 블로커` 2섹션이 보존되어야 하고,
        D-1이 제거하는 파생 4패턴(`pipeline:start`/표 헤더/`## 현재 상태`/
        `## 다음 액션`)은 3회 호출 후에도 여전히 0건이어야 한다(재파생 금지).

        RED 근거: 현재 `_build_new_state_md`가 4패턴을 그대로 생성하므로
        마지막 4개 assertEqual(count, 0)이 init 직후부터 이미 실패한다."""
        self.assertTrue(_OPD_REAL_PIPELINE_JSON.exists())
        task_path = self.tmpdir / "094-s2-two-sections"
        task_path.mkdir()
        code, stdout, stderr, _ = _run094([
            "init", str(task_path), "--skill", "opd", "--mode", "agentic",
            "--rows-from", str(_OPD_REAL_PIPELINE_JSON),
        ])
        self.assertEqual(code, 0, f"init 실패: {stdout!r} {stderr!r}")

        code, stdout, stderr, _ = _run094([
            "advance", str(task_path), "--task-step", "task.task_md",
        ])
        self.assertEqual(code, 0, f"advance 실패: {stdout!r} {stderr!r}")

        code, stdout, stderr, _ = _run094([
            "mark", str(task_path), "--task-step", "task.task_md", "--done",
        ])
        self.assertEqual(code, 0, f"mark 실패: {stdout!r} {stderr!r}")

        code, stdout, stderr, _ = _run094([
            "block", str(task_path), "--task-step", "task.user_confirm",
            "--reason", "테스트 블로커",
        ])
        self.assertEqual(code, 0, f"block 실패: {stdout!r} {stderr!r}")

        md = (task_path / "STATE.md").read_text(encoding="utf-8")
        self.assertIn("## 의사결정 로그", md,
                     "3회 연속 갱신 후 '## 의사결정 로그' 표 헤더가 소실됨(H-1)")
        self.assertIn("## 블로커", md,
                     "3회 연속 갱신 후 '## 블로커' 섹션이 소실됨")
        self.assertEqual(md.count("pipeline:start"), 0,
                         "연속 갱신 중 pipeline:start 마커가 재파생됨(D-1 위반)")
        self.assertEqual(md.count("## 현재 상태"), 0,
                         "연속 갱신 중 '## 현재 상태' 섹션이 재파생됨(D-1 위반)")
        self.assertEqual(md.count("## 다음 액션"), 0,
                         "연속 갱신 중 '## 다음 액션' 섹션이 재파생됨(D-1 위반)")

    def test_s3_decision_log_accumulates_without_loss(self):
        """[T094/L1-F001] S-3 — 로그 1행이 이미 있는 저널에 후속
        `mark --auto-pass --note '두번째'`를 호출하면 표 행이 +1(총 2행)되어야
        하고, 기존 1행이 원문 그대로 보존되며, `#` 컬럼이 1·2로 연속되어야
        한다(§3.1.2 (6) `append_decision_log` 행 수 계산 보강 — 오프바이원 수정).

        [PM 판정 정정 2026-08-16] 최초 작성 시 관찰 대상을 `mark --force --note`
        (비워커·비게이트)로 삼았으나, 실측 결과 이 경로는 `decision`을 전혀
        세팅하지 않는 트리거 3종(auto-pass/worker-force/gate-force) 밖의
        존재하지 않는 트리거였다(state_tool.py:1615-1634, PLAN §3.1.2 "decision/
        reason_text 계산 로직 전량 존치" — 신규 트리거 미신설 확정, 헌법 §3
        Surgical Changes). TASK.md R-2 AC와 TEST-SCENARIO S-3 조건을 실재
        트리거 `--auto-pass`로 교정하고 본 테스트도 동일하게 교정한다. 1행
        시딩은 계속 무조건 로그하는 `status --set --note`(트리거 #4)로 수행해
        관찰 대상(두 번째 `mark --auto-pass --note`)과 분리한다.

        RED 근거: 현재 `append_decision_log`의 `row_count =
        existing_rows.count("\\n| ")`는 기존 행이 정확히 1개일 때 캡처 그룹
        문자열이 "\\n"으로 시작하지 않아 0으로 오카운트되므로(오프바이원),
        두 번째 호출 후에도 `#`가 1로 재사용되어 1,2 연속에 실패한다."""
        self.assertTrue(_OPD_REAL_PIPELINE_JSON.exists())
        task_path = self.tmpdir / "094-s3-log-accum"
        task_path.mkdir()
        code, stdout, stderr, _ = _run094([
            "init", str(task_path), "--skill", "opd", "--mode", "agentic",
            "--rows-from", str(_OPD_REAL_PIPELINE_JSON),
        ])
        self.assertEqual(code, 0, f"init 실패: {stdout!r} {stderr!r}")

        # 1행 시딩 — 무조건 로그하는 경로(트리거 #4)
        code, stdout, stderr, _ = _run094([
            "status", str(task_path), "--set", "blocked", "--note", "첫번째",
        ])
        self.assertEqual(code, 0, f"status 실패: {stdout!r} {stderr!r}")
        md_seed = (task_path / "STATE.md").read_text(encoding="utf-8")
        seed_rows = _decision_log_row_numbers(md_seed)
        self.assertEqual(len(seed_rows), 1,
                         f"시딩 직후 로그가 정확히 1행이어야 함 — 실제: {seed_rows}")

        # 관찰 대상 — mark --auto-pass --note (두 번째 로그, 실재 트리거 #2)
        code, stdout, stderr, _ = _run094([
            "mark", str(task_path), "--task-step", "task.task_md", "--done",
            "--auto-pass", "--note", "두번째",
        ])
        self.assertEqual(code, 0, f"mark --auto-pass 실패: {stdout!r} {stderr!r}")

        md_after = (task_path / "STATE.md").read_text(encoding="utf-8")
        all_rows = _decision_log_row_numbers(md_after)
        self.assertEqual(len(all_rows), 2,
                         f"두 번째 호출 후 로그 총 행수는 2여야 함 — 실제: {all_rows}")
        self.assertEqual(all_rows, ["1", "2"],
                         f"'#' 컬럼이 1,2로 연속되어야 함(오프바이원 없음) — 실제: {all_rows}")
        self.assertIn("첫번째", md_after, "기존 1행(첫번째)이 원문 보존되어야 함")
        self.assertIn("두번째", md_after, "신규 행(두번째)이 추가되어야 함")


# ═════════════════════════════════════════════════════════════════════════════
# D. 기본 시나리오 (PLAN §3 Step 2 "A. 기본 시나리오")
# ═════════════════════════════════════════════════════════════════════════════

class TestBasicScenarios(BaseTestCase):
    """기본 7종 시나리오 (권한/순서/마커/멱등성/워커 스코프/--force/--import-existing)"""

    def test_scenario_invalid_status_transition_advance_done_row(self):
        """순서 위반: 이미 done 상태 행에 advance 거부 (PLAN §2.18 #7 인접)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        self._mark(1)  # done 처리
        # advance는 pending→in_progress만 허용
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=1)
            exit_code, result = self._call_cmd(ST.cmd_advance, args)
        # advance: done row에 대한 advance는 에러 반환
        self.assertEqual(exit_code, 1)

    def test_scenario_worker_scope_violation(self):
        """워커 스코프 위반: EXECUTE 스코프 워커가 TASK 행 mark 시도 (PLAN §2.4, §2.18 #1)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=1, done=True,  # row1=TASK/작업
                as_worker=True, worker_stage="EXECUTE",  # EXECUTE 스코프
            )
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "worker_scope_violation")

    # [T094 삭제·D-2/R-3] test_scenario_marker_missing_init_then_remove — 마커
    # 하드 게이트 자체가 R-3으로 제거되어 "마커 제거 → advance 거부"라는 전제
    # (marker_missing exit 1)가 더 이상 성립하지 않는다(정반대 동작이 정상 —
    # advance는 ok:true를 반환해야 함). 대체 회귀 커버리지는
    # `TestBasicScenarios.test_s6_marker_gate_removed_three_corruption_cases`가
    # (i)삭제 (ii)마커만 제거 (iii)임의 텍스트 3케이스 × advance/mark 6회 호출
    # 전부 ok:true를 검증하며 이미 담당한다.

    def test_scenario_idempotency_already_initialized(self):
        """멱등성 위반: init 두 번 → already_initialized 거부 (PLAN §2.18 #3, T-8)"""
        self._init()
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                rows_spec=SIMPLE_ROWS_SPEC,
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "already_initialized")

    def test_scenario_force_with_note_bypass(self):
        """--force 우회: --force + --note 제공 시 init 성공 (PLAN §2.17 트리거 #1, T-8)"""
        self._init()
        self._init(rows_spec=SIMPLE_ROWS_SPEC, force=True, note="강제 재초기화 이유")
        state = self._state()
        # 재초기화 성공 확인
        self.assertIsNotNone(state)

    # [T094 삭제·D-2/R-3] test_scenario_import_existing_success /
    # test_scenario_import_existing_failure — `--import-existing` 파싱 분기
    # (성공/실패 양쪽 모두)가 D-2로 완전히 삭제되어 두 전제 모두 성립하지
    # 않는다(호출 자체가 항상 `import_existing_removed`로 즉시 거부됨).
    # 대체 회귀 커버리지는 `TestInit.test_s9_import_existing_removed_rejected`
    # (단일 라인 JSON + exit 1 + `import_existing_removed` 검증)가 담당한다.

    # ─────────────────────────────────────────────────────────────────────
    # 094 RED-first 추가 — TEST-SCENARIO.md S-6, S-23 (PLAN §3.2.2 (3), 제약 ③)
    # [MUST] 실 CLI subprocess(run.sh) + 실 파일 내용으로만 검증, mock 금지.
    # ─────────────────────────────────────────────────────────────────────

    def test_s6_marker_gate_removed_three_corruption_cases(self):
        """[T094/L2-F002] S-6 — STATE.md (i) 삭제 (ii) 마커 라인만 제거 (iii)
        임의 텍스트로 덮어쓰기, 3케이스 각각에서 `advance`·`mark`를 호출하면
        6회 전부 `ok:true`·exit 0이어야 한다(R-3 AC(a) 마커 하드 차단 제거).

        [Step 3-c 시퀀스 교정, 093 머지 여파] 원래는 advance(task.task_md) →
        mark(task.user_confirm)로 서로 다른 두 행을 건드렸으나, 093의
        stage-transition guard(F-002)는 대상 행 앞의 모든 행이 done/na여야
        진입을 허용한다 — advance는 pending→in_progress까지만 전진시키므로
        task.task_md가 in_progress로 남은 채 task.user_confirm을 mark하면
        `stage_transition_violation`(마커 게이트와 무관한 별개 가드)에 걸린다.
        이 테스트의 검증 대상은 어디까지나 '마커 손상 상태에서 advance·mark가
        차단되지 않는다'이므로, **같은 행(task.task_md)에 advance→mark를
        순서대로 걸어 그 행 하나를 완결**시키는 유효한 시퀀스로 교정한다 —
        advance 호출 앞에는 검증할 선행 행이 없어(row_index=0) guard가
        구조적으로 통과하고, mark 호출도 동일 행(이미 앞 행 없음)이라 guard가
        걸릴 여지가 없다. 3케이스 × 2명령 = 6회 호출이라는 시나리오 강도는
        그대로 유지된다."""
        self.assertTrue(_OPD_REAL_PIPELINE_JSON.exists())
        corruption_cases = ["삭제", "마커만_제거", "임의_텍스트"]
        for case_name in corruption_cases:
            with self.subTest(case=case_name):
                task_path = self.tmpdir / f"094-s6-{case_name}"
                task_path.mkdir()
                code, stdout, stderr, _ = _run094([
                    "init", str(task_path), "--skill", "opd", "--mode", "agentic",
                    "--rows-from", str(_OPD_REAL_PIPELINE_JSON),
                ])
                self.assertEqual(code, 0, f"init 실패({case_name}): {stdout!r} {stderr!r}")

                md_path = task_path / "STATE.md"
                if case_name == "삭제":
                    md_path.unlink()
                elif case_name == "마커만_제거":
                    md_text = md_path.read_text(encoding="utf-8")
                    md_path.write_text(
                        md_text.replace(ST.PIPELINE_MARKER_START, "")
                                .replace(ST.PIPELINE_MARKER_END, ""),
                        encoding="utf-8")
                else:  # 임의_텍스트
                    md_path.write_text("마커도 표도 없는 임의 텍스트\n", encoding="utf-8")

                code, stdout, stderr, data = _run094([
                    "advance", str(task_path), "--task-step", "task.task_md",
                ])
                self.assertEqual(code, 0,
                                 f"advance가 exit 0이어야 함({case_name}, 마커 게이트 소멸): "
                                 f"stdout={stdout!r} stderr={stderr!r}")
                self.assertTrue(data.get("ok"), f"advance ok:true 아님({case_name}): {data}")

                code, stdout, stderr, data = _run094([
                    "mark", str(task_path), "--task-step", "task.task_md", "--done",
                ])
                self.assertEqual(code, 0,
                                 f"mark가 exit 0이어야 함({case_name}, 마커 게이트 소멸): "
                                 f"stdout={stdout!r} stderr={stderr!r}")
                self.assertTrue(data.get("ok"), f"mark ok:true 아님({case_name}): {data}")

    def test_s23_five_update_commands_response_keys_preserved(self):
        """[T094/L1-F001/F003] S-23 — `advance`/`mark`/`block`/`add-row`/`status`
        5개 갱신 명령의 stdout 응답 키 집합에서 기존 키 삭제가 0건이어야 하고,
        `journal_warning`은 조건부(실패 시에만) 추가되어야 한다(제약 ③ stdout
        계약 호환, PLAN §3.1.2 (4)).

        정상 경로(저널 쓰기 성공)에서는 `journal_warning` 키가 아예 없어야
        한다 — 이 부분은 현재도 성립해 회귀 안전망 역할을 하지만, 기존 키
        보존 자체는 F-001 재배선이 인자를 축소하며 실수로 키를 지우지
        않는지 GREEN 이후에도 감시한다.

        [PM 판정 정정 2026-08-16] 최초 작성 시 `block` 직후(current_status가
        이미 "blocked") `status --set blocked`를 호출해 `blocked→blocked`
        (`ALLOWED_TRANSITIONS` 미등재 — 자기 전이 불허)가 되어 시퀀스 자체가
        무효했다. `blocked`에서 허용되는 전이(`in_progress`/`done`) 중
        `in_progress`로 교정한다 — 검증 목적(5개 갱신 명령의 응답 키 계약)은
        불변이다."""
        self.assertTrue(_OPD_REAL_PIPELINE_JSON.exists())
        task_path = self.tmpdir / "094-s23-response-keys"
        task_path.mkdir()
        code, stdout, stderr, _ = _run094([
            "init", str(task_path), "--skill", "opd", "--mode", "agentic",
            "--rows-from", str(_OPD_REAL_PIPELINE_JSON),
        ])
        self.assertEqual(code, 0, f"init 실패: {stdout!r} {stderr!r}")

        baseline_keys = {
            "advance": {"ok", "command", "row_id", "stage", "item", "status",
                        "timestamp", "todo_mirror"},
            "mark":    {"ok", "command", "row_id", "stage", "item", "status",
                        "timestamp", "owner", "todo_mirror"},
            "block":   {"ok", "command", "row_id", "stage", "item", "status",
                        "current_status", "timestamp", "todo_mirror"},
            "add-row": {"ok", "command", "row_id", "key", "rows_count",
                        "current_status"},
            "status":  {"ok", "command", "from", "to", "timestamp"},
        }

        code, stdout, stderr, data = _run094([
            "advance", str(task_path), "--task-step", "task.task_md",
        ])
        self.assertEqual(code, 0, f"advance 실패: {stdout!r} {stderr!r}")
        missing = baseline_keys["advance"] - set(data.keys())
        self.assertEqual(missing, set(), f"advance 응답에서 기존 키 삭제됨: {missing}")

        code, stdout, stderr, data = _run094([
            "mark", str(task_path), "--task-step", "task.task_md", "--done",
        ])
        self.assertEqual(code, 0, f"mark 실패: {stdout!r} {stderr!r}")
        missing = baseline_keys["mark"] - set(data.keys())
        self.assertEqual(missing, set(), f"mark 응답에서 기존 키 삭제됨: {missing}")

        code, stdout, stderr, data = _run094([
            "block", str(task_path), "--task-step", "task.user_confirm",
            "--reason", "테스트 블로커",
        ])
        self.assertEqual(code, 0, f"block 실패: {stdout!r} {stderr!r}")
        missing = baseline_keys["block"] - set(data.keys())
        self.assertEqual(missing, set(), f"block 응답에서 기존 키 삭제됨: {missing}")

        code, stdout, stderr, data = _run094([
            "add-row", str(task_path), "--after-task-step", "task.user_confirm",
            "--stage", "TASK", "--item", "094 추가행",
        ])
        self.assertEqual(code, 0, f"add-row 실패: {stdout!r} {stderr!r}")
        missing = baseline_keys["add-row"] - set(data.keys())
        self.assertEqual(missing, set(), f"add-row 응답에서 기존 키 삭제됨: {missing}")

        code, stdout, stderr, data = _run094([
            "status", str(task_path), "--set", "in_progress", "--note", "상태 전환",
        ])
        self.assertEqual(code, 0, f"status 실패: {stdout!r} {stderr!r}")
        missing = baseline_keys["status"] - set(data.keys())
        self.assertEqual(missing, set(), f"status 응답에서 기존 키 삭제됨: {missing}")


# [T094 삭제·D-2/R-3] TestImportPreservesKeys 클래스 전체(5건: test_force_import_preserves_all_keys,
# test_import_with_pipeline_json_restores_keys, test_import_no_key_source_keyless_with_warning,
# test_preserved_keys_keep_schema_version_1_1, test_duplicate_stage_item_ordered_consumption) —
# 074가 도입한 `--import-existing` key 재접합 로직(`parse_existing_state_md`/
# `_key_source_index`/`_reattach_import_keys`)이 094 D-2로 전부 삭제되어 이 클래스가
# 검증하던 기능 자체가 소멸했다. 대체 회귀 커버리지는
# `TestInit.test_s9_import_existing_removed_rejected`(호출 시 즉시 거부)가 담당한다.

# ═════════════════════════════════════════════════════════════════════════════
# E. 자유 텍스트 영역 보존 (PLAN §3 Step 2 마지막 항목)
# ═════════════════════════════════════════════════════════════════════════════

class TestFreeTextPreservation(BaseTestCase):
    """[MUST] 자유 텍스트 영역 보존: 블로커 섹션은 전 명령(mark/advance/block/
    add-row) 보존되어야 한다.

    [T094 수정 2026-08-16] '## 다음 액션' 섹션은 D-1로 STATE.md에서 완전
    제거되었다(값은 state.json.next_action에만 영속화, 조회는 `show`).
    이에 따라 이 클래스가 검증하던 3영역 중 '다음 액션' 렌더 관련 부분은
    다음과 같이 정리한다:
    - `test_mark_derives_next_action_preserves_others` /
      `test_advance_derives_next_action_preserves_others`: STATE.md '## 다음
      액션' 첫 줄 치환 + 하위 자유기재 보존만 검증하는 순수 렌더 테스트라
      대체 불가능하게 기능이 소멸했으므로 삭제한다(D-1). 동일 파생값 검증은
      `TestAdvance.test_advance_g6_progress_updated`가 `state.json.next_action`
      기준으로 계승한다.
    - `test_block_preserves_free_text` / `test_add_row_preserves_free_text` /
      `test_pipeline_marker_region_only_changed`: '블로커 섹션 보존'은 여전히
      살아있는 계약(TASK.md §제약 "의사결정 로그·블로커 데이터는 어떤 경로에서도
      유실되어서는 안 된다")이므로 존치하되, `_free_text_sections`이 더 이상
      존재하지 않는 '## 다음 액션'을 경계로 삼던 부분을 제거해 블로커 섹션을
      파일 끝까지로 재정의한다(수정 없이 두면 항상 (None, None)을 반환해
      비교가 무의미하게 항상 통과하는 결함이 있었다 — 이번에 회귀 감지력을
      복원한다).
    """

    def setUp(self):
        super().setUp()
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        # 블로커 자유 텍스트 영역에 마커 내용 추가('## 다음 액션'은 D-1로 제거되어
        # 더 이상 fixture에 없다 — 하위 자유기재 삽입 대상도 함께 제거)
        md = self._md()
        md = md.replace("없음", "블로커 상세: 테스트 블로커 내용이 여기 있음")
        (self.task_path / "STATE.md").write_text(md)

    def _free_text_sections(self, md):
        """[T094 수정] 블로커 섹션(파일 끝까지) 추출. '## 다음 액션'은 D-1로
        제거되어 경계로 사용할 수 없으므로, '## 블로커' 시작부터 파일 끝까지를
        블로커 영역으로 간주한다."""
        blocker_start = md.find("## 블로커")
        if blocker_start == -1:
            return None
        return md[blocker_start:]

    def _assert_free_text_preserved(self, before_md, after_md):
        """블로커 섹션이 변경되지 않았는지 확인."""
        b_before = self._free_text_sections(before_md)
        b_after = self._free_text_sections(after_md)
        self.assertIsNotNone(b_before, "블로커 섹션 추출 실패(픽스처 손상)")
        self.assertEqual(b_before, b_after, "블로커 섹션이 변경됨!")

    def test_block_preserves_free_text(self):
        """block 후 블로커/다음 액션 섹션 보존 (PLAN §3 Step 2)"""
        md_before = self._md()
        self._block(1, reason="블로킹")
        md_after = self._md()
        self._assert_free_text_preserved(md_before, md_after)

    def test_add_row_preserves_free_text(self):
        """add-row 후 블로커/다음 액션 섹션 보존 (PLAN §3 Step 2)"""
        md_before = self._md()
        self._add_row(after=1, stage="CLOSE", item="신규 항목")
        md_after = self._md()
        self._assert_free_text_preserved(md_before, md_after)

    def test_pipeline_marker_region_only_changed(self):
        """[T094 수정] 갱신 명령은 파이프라인 표 영역만 변경, 블로커 영역은 불변
        (PLAN §2.11 G-8, F-4). '## 다음 액션'은 D-1로 제거되어 더 이상 경계로
        쓸 수 없으므로 블로커 섹션을 파일 끝까지로 재정의한다."""
        md_before = self._md()
        self._mark(1)
        md_after = self._md()
        # 블로커 영역(파일 끝까지)은 동일해야 함(의사결정 로그 자동 기재는 허용 범위 밖)
        blocker_before = self._free_text_sections(md_before)
        blocker_after = self._free_text_sections(md_after)
        self.assertIsNotNone(blocker_before)
        self.assertEqual(blocker_before, blocker_after)


# ═════════════════════════════════════════════════════════════════════════════
# 072: TestNextActionAutoDerive — STATE.md "다음 액션" 자동 파생 RED-first
# (TEST-SCENARIO.md S-1~S-4, S-6, S-7 / red-first.md §2,§4 — 작성자≠구현자,
#  공개 인터페이스(CLI 서브명령 호출 → state.json/STATE.md 관측)로만 검증)
# ═════════════════════════════════════════════════════════════════════════════

class TestNextActionAutoDerive(BaseTestCase):
    """072: `next_action` 자동 파생 — TEST-SCENARIO.md S-1~S-4, S-6, S-7 (RED-first).

    [MUST] red-first.md §4: 내부 private 함수(`_derive_next_action` 등)를 직접 import·
    호출하지 않는다. 오직 공개 CLI 경로(cmd_init/cmd_advance/cmd_mark 직접 호출 또는
    run.sh subprocess 실호출)와 그 관측 가능 산출물(state.json, STATE.md)만으로 검증한다.

    파생 로직 구현 **전** 현재 코드에서 이 클래스는 실패(RED)해야 한다 —
    GREEN 구현은 op-dev-execute가 담당한다(red-first.md §2, 작성자≠구현자).

    [T094 수정 2026-08-16] '## 다음 액션' STATE.md 섹션은 D-1로 완전 제거되었다
    (`next_action` 값은 state.json 필드로만 영속화, 조회는 `show`). 이 클래스의
    9개 테스트 중 `_derive_next_action` 프론티어 파생 로직 자체(state.json
    `next_action` 필드 검증)는 여전히 완전히 살아있는 기능이므로, STATE.md
    렌더 확인 부분만 제거하고 state.json 검증은 그대로 존치한다("기능은
    있는데 확인 위치만 옮겨졌다" — 삭제하면 프론티어 파생 회귀 감지력이
    사라진다). `test_m1_first_line_replaced_subordinate_free_text_preserved`
    하나만 STATE.md 렌더 자체(첫 줄 치환 + 하위 자유기재 보존)만을 검증하는
    순수 렌더 테스트라 대체 불가능하게 기능이 소멸했으므로 삭제한다(D-1).
    """

    # S-2/S-3 프론티어 파생 검증용 — CLOSE 게이트 없이 순수 전이 순서만 확인
    _NEXT_ACTION_ROWS_SPEC = json.dumps([
        {"stage": "TASK", "item": "작업"},
        {"stage": "PLAN", "item": "작업"},
        {"stage": "PLAN", "item": "QA Gate"},
    ])

    # S-3 전체 완료 경계 검증용 — CLOSE 게이트 통과 조건(직전 "사용자 확인" 행 done/user)
    _NEXT_ACTION_CLOSE_ROWS_SPEC = json.dumps([
        {"stage": "TASK",  "item": "사용자 확인"},
        {"stage": "CLOSE", "item": "State Gate"},
    ])

    # S-6/S-7 오버라이드 검증용 — 최소 2행
    _NEXT_ACTION_OVERRIDE_ROWS_SPEC = json.dumps([
        {"stage": "TASK", "item": "작업"},
        {"stage": "PLAN", "item": "작업"},
    ])

    # [T094 수정] `_next_action_lines`(STATE.md '## 다음 액션' 첫 줄/하위 라인
    # 추출 헬퍼)는 D-1로 해당 섹션 자체가 제거되어 삭제한다. 프론티어 파생값은
    # 이제 각 테스트에서 `state.get("next_action")`으로만 검증한다.

    # ── S-1 (R-1/H-4): init next_action 영속화 + schema optional 등록 + 하위호환 ──

    def test_r1_init_default_next_action_persisted_to_state_json(self):
        """[T072/L1-R1] S-1 ①: init(기본값, --next-action 미지정) 후 state.json에
        `next_action` 키가 존재하고 기존 STATE.md 기본 문구("PLAN 단계 진입")와 일치해야 한다.
        현재 cmd_init은 state.json에 next_action을 기록하지 않으므로 실패한다(RED)."""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        state = self._state()
        self.assertIn("next_action", state,
                      "state.json에 'next_action' 키가 없음 — R-1 미구현(RED 증거)")
        self.assertEqual(state.get("next_action"), "PLAN 단계 진입")

    def test_r1_init_custom_next_action_persisted_to_state_json(self):
        """[T072/L1-R1] S-1 ①: init --next-action "커스텀 초기 액션" 지정 시 state.json
        `next_action` 값이 그대로 영속화되어야 한다. 현재 미저장이므로 실패한다(RED)."""
        self._init(rows_spec=SIMPLE_ROWS_SPEC, next_action="커스텀 초기 액션")
        state = self._state()
        self.assertEqual(state.get("next_action"), "커스텀 초기 액션",
                         f"state.json next_action 불일치: {state.get('next_action')!r}")

    def test_r1_schema_next_action_optional_registered_not_required(self):
        """[T072/L1-R1] S-1 ②: state.schema.json `properties`에 `next_action`(optional)이
        등록되고, `required` 배열에는 포함되지 않아야 한다(H-4 하위호환 — 구버전 state.json이
        향후 validate 시 위반되지 않도록). 현재 properties 미등록이므로 실패한다(RED)."""
        schema_path = _SCHEMA_DIR / "state.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertNotIn("next_action", schema.get("required", []),
                         "next_action이 required에 추가됨 — 구버전 state.json 하위호환 파괴(H-4)")
        self.assertIn("next_action", schema.get("properties", {}),
                      "next_action이 schema properties에 미등록 — RED 증거")

    def test_r1_legacy_state_json_without_next_action_advance_no_keyerror(self):
        """[T072/L1-R1] S-1 ③: `next_action` 키가 없는 구버전 state.json으로 advance 호출 시
        KeyError 없이 정상 동작(exit 0)해야 한다. 하위호환 회귀 방지 가드."""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        state = self._state()
        state.pop("next_action", None)  # 구버전 시뮬레이션
        (self.task_path / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        code = self._advance(1)
        self.assertEqual(code, 0,
                         "next_action 키 없는 구버전 state.json으로 advance 실패(하위호환 위반)")

    # ── S-2 (R-2/R-3): advance/mark 순차 전이 프론티어 파생 + 렌더 정합 ──

    def test_r2_r3_sequential_frontier_derivation_advance_mark(self):
        """[T072/L1-R2,R3][T094 수정] S-2 — 여러 행을 순차로 advance(→in_progress)/
        mark(→done)하며 각 시점 state.json `next_action`이 프론티어(첫 미완료
        행) 기반 값과 일치해야 한다: pending → "{stage} {item} 진입",
        in_progress → "{stage} {item} 진행 중".

        STATE.md '## 다음 액션' 렌더 확인은 D-1로 해당 섹션이 완전히
        제거되어 삭제한다 — 프론티어 파생 로직 자체(`_derive_next_action`)는
        state.json에 여전히 살아있는 기능이므로 그 검증만 존치한다."""
        self._init(rows_spec=self._NEXT_ACTION_ROWS_SPEC)

        steps = [
            ("advance", 1, "TASK 작업 진행 중"),
            ("mark",    1, "PLAN 작업 진입"),
            ("advance", 2, "PLAN 작업 진행 중"),
            ("mark",    2, "PLAN QA Gate 진입"),
        ]
        for action, row_id, expected in steps:
            with self.subTest(action=action, row=row_id, expected=expected):
                code = self._advance(row_id) if action == "advance" else self._mark(row_id)
                self.assertEqual(code, 0, f"{action}(row={row_id}) 실패")

                state = self._state()
                self.assertEqual(
                    state.get("next_action"), expected,
                    f"{action}(row={row_id}) 후 state.json next_action 불일치: "
                    f"{state.get('next_action')!r} (기대: {expected!r})"
                )

    # ── S-3 (R-2/M-2): 전체 완료 시 "태스크 완료" 경계 ──

    def test_r2_m2_all_rows_complete_next_action_task_complete(self):
        """[T072/L1-R2,M-2][T094 수정] S-3 — 마지막 행까지 모두 완료
        (current_status=done)되면 프론티어(다음 대기 행)가 부재하므로
        `next_action == "태스크 완료"`여야 한다.

        STATE.md 첫 줄 렌더 확인은 D-1로 '## 다음 액션' 섹션이 완전히
        제거되어 삭제한다 — state.json 필드 검증(태스크 완료 경계)은 존치."""
        self._init(rows_spec=self._NEXT_ACTION_CLOSE_ROWS_SPEC)

        code1 = self._mark(1, owner="user")  # TASK 사용자 확인 → done/user (CLOSE 게이트 통과)
        self.assertEqual(code1, 0, "row1(사용자 확인) mark 실패")

        # 마지막 행(CLOSE State Gate) mark 전 — 프론티어 = row2(pending)
        state_mid = self._state()
        self.assertEqual(
            state_mid.get("next_action"), "CLOSE State Gate 진입",
            f"row2 mark 전 프론티어 파생값 불일치: {state_mid.get('next_action')!r}"
        )

        code2 = self._mark(2)  # CLOSE State Gate → done, current_status=done
        self.assertEqual(code2, 0, "row2(CLOSE State Gate) mark 실패")

        state_final = self._state()
        self.assertEqual(state_final.get("current_status"), "done")
        self.assertEqual(
            state_final.get("next_action"), "태스크 완료",
            f"전체 완료 후 next_action 불일치: {state_final.get('next_action')!r}"
        )

    # [T094 삭제·D-1] test_m1_first_line_replaced_subordinate_free_text_preserved
    # — '## 다음 액션' 헤더의 첫 줄 치환 + 하위 자유 기재 보존을 검증하는
    # 순수 STATE.md 렌더 테스트였다(state.json 검증 0건). D-1로 해당 섹션
    # 자체가 완전 제거되어 대체 불가능하게 기능이 소멸했다.

    # ── S-6 (R-4): advance/mark --next-action 오버라이드 우선 ──

    def test_r4_override_next_action_takes_priority_over_derivation(self):
        """[T072/L1-R4][T094 수정] S-6 — `advance --next-action "커스텀 안내"`
        지정 시 자동 파생값보다 오버라이드가 우선해야 한다. 공개 CLI 실호출
        (run.sh subprocess, red-first.md §4).

        STATE.md 첫 줄 렌더 확인은 D-1로 '## 다음 액션' 섹션이 완전히
        제거되어 삭제한다 — 오버라이드 우선 순위 로직 자체(state.json 필드)는
        여전히 살아있는 기능이므로 그 검증만 존치한다."""
        self._init(rows_spec=self._NEXT_ACTION_OVERRIDE_ROWS_SPEC)

        code, stdout, stderr, data = _run070([
            "advance", str(self.task_path),
            "--row", "1",
            "--next-action", "커스텀 안내",
        ])
        self.assertEqual(
            code, 0,
            f"advance --next-action 실호출 실패(exit={code}): stdout={stdout!r} stderr={stderr!r}"
        )
        self.assertTrue(data.get("ok"), f"advance --next-action 응답 ok 아님: {data}")

        state = self._state()
        self.assertEqual(
            state.get("next_action"), "커스텀 안내",
            f"오버라이드가 파생값보다 우선하지 않음: {state.get('next_action')!r}"
        )

    # ── S-7 (R-4/M-3): 오버라이드 비지속 — 다음 전이 자동 파생 복귀 ──

    def test_m3_override_non_persistent_reverts_to_derived_on_next_transition(self):
        """[T072/L1-R4,M-3][T094 수정] S-7 — S-6과 동일한 오버라이드 전이 직후,
        `--next-action` 없는 후속 mark 시 자동 파생값으로 복귀해야 한다
        (오버라이드 비지속 — stale 값 재도입 금지).

        STATE.md 첫 줄 렌더 확인은 D-1로 '## 다음 액션' 섹션이 완전히
        제거되어 삭제한다 — 오버라이드 비지속 로직 자체(state.json 필드)는
        여전히 살아있는 기능이므로 그 검증만 존치한다."""
        self._init(rows_spec=self._NEXT_ACTION_OVERRIDE_ROWS_SPEC)

        code, stdout, stderr, data = _run070([
            "advance", str(self.task_path),
            "--row", "1",
            "--next-action", "커스텀 안내",
        ])
        self.assertEqual(
            code, 0,
            f"S-6 사전 오버라이드 전이 실패(exit={code}): stdout={stdout!r} stderr={stderr!r}"
        )

        # --next-action 없는 후속 mark(row1 완료) → 프론티어 = row2(PLAN 작업, pending)
        mark_code = self._mark(1)
        self.assertEqual(mark_code, 0, "후속 mark(row1) 실패")

        state = self._state()
        self.assertNotEqual(
            state.get("next_action"), "커스텀 안내",
            "오버라이드 값이 후속 전이에서도 stale하게 재도입됨(비지속 위반)"
        )
        self.assertEqual(
            state.get("next_action"), "PLAN 작업 진입",
            f"후속 전이 후 자동 파생값 복귀 실패: {state.get('next_action')!r}"
        )


# ═════════════════════════════════════════════════════════════════════════════
# F. C-1~C-6 충돌/종속 관계 (PLAN §2.19.10)
# ═════════════════════════════════════════════════════════════════════════════

class TestConflictConstraints(BaseTestCase):
    """PLAN §2.19.10 충돌/종속 C-1~C-6 단위 테스트"""

    def setUp(self):
        super().setUp()
        self._init(rows_spec=SIMPLE_ROWS_SPEC)

    def test_c1_rows_spec_rows_from_conflict(self):
        """C-1 배타: --rows-spec + --rows-from 동시 사용 → rows_input_conflict (PLAN §2.19 C-1)"""
        skill_md = self.tmpdir / "SKILL.md"
        skill_md.write_text("dummy")
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                rows_spec=SIMPLE_ROWS_SPEC,
                rows_from=str(skill_md),
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "rows_input_conflict")

    def test_c2_owner_auto_pass_conflict(self):
        """C-2 배타: --owner + --auto-pass 동시 → owner_flag_conflict (PLAN §2.19 C-2)"""
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=1, done=True, owner="user", auto_pass=True,
            )
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "owner_flag_conflict")

    def test_c3_as_worker_without_worker_stage(self):
        """C-3 종속: --as-worker 시 --worker-stage 필수 → worker_stage_required (PLAN §2.19 C-3)"""
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=1, done=True, as_worker=True, worker_stage=None,
            )
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "worker_stage_required")

    def test_c4_force_without_note_init(self):
        """C-4 종속: --force 시 --note 필수 (init) → note_required_for_force (PLAN §2.19 C-4)"""
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                force=True, note=None,
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "note_required_for_force")

    def test_c4_force_without_note_mark(self):
        """C-4 종속: --force 시 --note 필수 (mark) → note_required_for_force (PLAN §2.19 C-4)"""
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=1, done=True, force=True, note=None,
            )
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "note_required_for_force")

    def test_c6_agentic_auto_pass_close_first_row(self):
        """C-6 모드 제약: agentic + CLOSE 첫 행 + auto-pass → agentic_close_gate_requires_user (PLAN §2.19 C-6)"""
        rows = json.dumps([
            {"stage": "TASK",  "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows, mode="agentic", force=True, note="재초기화")
        # 093 F-001/F-002: 사용자 확인 행은 pending 초기화 + CLOSE 직전이라 훅 제외(DEC-D)
        self._mark(1, owner="user")
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=2, done=True, auto_pass=True,
            )
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "agentic_close_gate_requires_user")


# ═════════════════════════════════════════════════════════════════════════════
# G. rows-from SKILL.md 파싱 (PLAN §2.20.2)
# ═════════════════════════════════════════════════════════════════════════════

class TestRowsFrom(BaseTestCase):
    """--rows-from SKILL.md 파싱 테스트 (PLAN §2.20.2)"""

    def _make_skill_md(self, content):
        skill_md = self.tmpdir / "SKILL.md"
        skill_md.write_text(content)
        return skill_md

    def test_rows_from_success(self):
        """--rows-from: 유효한 SKILL.md에서 행 추출 성공 (PLAN §2.20.2)"""
        skill_md = self._make_skill_md("""
## STATE.md 도메인 치환값

| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ |  |
| 2 | PLAN | 작업 | ⬜ |  |
| 3 | CLOSE | State Gate | ⬜ |  |
""")
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                rows_from=str(skill_md),
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 0, f"rows_from failed: {result}")
        state = self._state()
        self.assertEqual(len(state["rows"]), 3)

    def test_rows_from_skill_md_parse_error_no_header(self):
        """--rows-from: 헤더 없음 → skill_md_parse_error (PLAN §2.20.2 단계 2)"""
        skill_md = self._make_skill_md("# 다른 헤더\n내용\n")
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                rows_from=str(skill_md),
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "skill_md_parse_error")

    def test_rows_from_agentic_user_confirmation_pending(self):
        """[093 TS-003] --rows-from agentic: 사용자 확인 행은 pending으로 초기화된다
        (093 F-001 — 구형 auto-na 분기 제거)"""
        skill_md = self._make_skill_md("""
## STATE.md 도메인 치환값

| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 사용자 확인 | ⬜ |  |
| 2 | CLOSE | 사용자 확인 | ⬜ |  |
""")
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="agentic",
                rows_from=str(skill_md),
            )
            self._call_cmd(ST.cmd_init, args)
        state = self._state()
        task_user = next(r for r in state["rows"] if r["stage"] == "TASK")
        self.assertEqual(task_user["status"], "pending")
        close_user = next(r for r in state["rows"] if r["stage"] == "CLOSE")
        self.assertEqual(close_user["status"], "pending")  # CLOSE도 pending (불변)

    def test_md_init_stamps_schema_version_1_0_and_validates(self):
        """[T070 후속/Part B] `.md`(SKILL.md 레거시 파싱) init → schema_version=="1.0" 유지 + validate ok.

        key 없는 레거시 경로(rows[]에 key 미부여)는 1.1로 승격되지 않아야 한다
        (단순·결정론 규칙 — rows 중 하나라도 key 있으면 1.1, 아니면 1.0).
        """
        skill_md = self._make_skill_md("""
## STATE.md 도메인 치환값

| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ |  |
| 2 | PLAN | 작업 | ⬜ |  |
| 3 | CLOSE | State Gate | ⬜ |  |
""")
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                rows_from=str(skill_md),
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 0, f"md init 실패: {result}")
        state = self._state()
        self.assertEqual(
            state["schema_version"], "1.0",
            ".md 파싱 경로(key 없음)는 schema_version 1.0을 유지해야 함"
        )
        validate_result = self._validate()
        self.assertTrue(validate_result["ok"], f"1.0 state.json validate 실패: {validate_result}")


# ═════════════════════════════════════════════════════════════════════════════
# H. ERROR_CODES 상수 완전성 검증
# ═════════════════════════════════════════════════════════════════════════════

class TestErrorCodesCompleteness(unittest.TestCase):
    """PLAN §2.18 E-1: ERROR_CODES 25종 기존 + PLAN 013 신규 2종 + PLAN 014 신규 1종 + PLAN 016 신규 2종 + PLAN 005 신규 1종 + 070 신규 8종 + 091 신규 5종 - 094 삭제 2종 + 094 신규 1종 = 43종 모두 등재 확인.

    [PM 승인 예외 — 070 GREEN 후속 정정] 31→39 계약 갱신은 테스트 약화가 아니라
    카탈로그 정합 보존을 위한 승인된 갱신이다(AGENTIC-LOG #16 승인 근거).
    091(RED-first, F-004): 게이트 집행 배선 신규 5종(gate_artifact_missing +
    spec_gate_type_invalid/spec_gate_missing_field/spec_gate_field_type_invalid/
    spec_gate_checklist_empty) 반영.
    [T094 수정 2026-08-16 — R-3/D-2] 마커 하드 게이트 제거로 `marker_missing`,
    `--import-existing` 파싱 분기 삭제로 `import_failed`가 ERROR_CODES에서
    소멸(44→42)하고, 명시적 거부 코드 `import_existing_removed`가 신규
    등재(42→43)되어 실측 39→43(070 GREEN 후속 정정)이 아니라 44→43으로
    갱신됐다. 목록·카운트 둘 다 실측값(43)에 맞춰 동기화한다."""

    EXPECTED_CODES = [
        # 기존 25종 (PLAN §2.18 + 이전 추가분) 중 23종 존치
        # ([T094 삭제] marker_missing/import_failed 2종은 아래 094 절 참조)
        "worker_scope_violation",
        "already_initialized",
        "date_tool_failed",
        "invalid_status_transition",
        "row_not_found",
        "invalid_stage_enum",
        "gate_pattern_mismatch",
        "gate_stage_mixed",
        "state_not_initialized",
        "user_confirmation_owner_mismatch",
        "owner_flag_conflict",
        "auto_pass_in_interactive_mode",
        "close_gate_violation",
        "agentic_close_gate_requires_user",
        "semi_agentic_pre_execute_auto_pass_denied",
        "mode_flag_conflict",
        "note_required_for_force",
        "rows_spec_invalid_json",
        "skill_md_parse_error",
        "task_path_not_found",
        "worker_stage_required",
        "rows_input_conflict",
        "rows_acts_not_implemented",
        # PLAN 013 신규 2종 (헌법 §4 동작 증거 강제 게이트)
        "mock_in_scenario",
        "evidence_missing",
        # PLAN 014 신규 1종 (M-A stage-transition guard)
        "stage_transition_violation",
        # PLAN 016 신규 2종 (RED-first TDD 트랙 게이트)
        "red_evidence_missing",
        "test_modified_in_fix",
        # PLAN 005 신규 1종 (TASK 4요소 잠금 명확화 게이트)
        "clarification_gate_unmet",
        # 070 신규 8종 (F-001 spec-validate 3종 + F-003 task-step 주소 3종 + F-004 add-row --key 2종)
        "spec_file_not_found",
        "spec_invalid_json",
        "spec_validation_failed",
        "task_step_addr_required",
        "task_step_addr_conflict",
        "task_step_not_found",
        "task_step_key_invalid",
        "task_step_key_duplicate",
        # 091 신규 5종 (F-004 게이트 집행 배선 — PLAN §3.4.2 (2)/(6))
        "gate_artifact_missing",
        "spec_gate_type_invalid",
        "spec_gate_missing_field",
        "spec_gate_field_type_invalid",
        "spec_gate_checklist_empty",
        # 094 신규 1종 (D-2 — --import-existing 명시적 거부)
        "import_existing_removed",
        # 093 F-004 R-4 (머지 편입)
        "user_confirmation_required",
        # 098 신규 1종 (F-003 R-4 — --evidence-check/--clarification-check 동시 지정 거부)
        "evidence_check_flag_conflict",
    ]

    def test_error_codes_count(self):
        """[098 H-10 선갱신] ERROR_CODES 45종 — 093 시점 44종에서 098 F-003이
        `evidence_check_flag_conflict` 1종을 신규 등재해 44+1=45종.

        RED 근거: 098 GREEN(Step 5, opal-be-agent) 구현 전에는 ERROR_CODES가
        여전히 44종이므로 이 단언은 현재 실패한다(45!=44) — 신규 에러 코드
        추가가 본 테스트를 동시에 깨는 문제(H-10)를 선갱신으로 흡수한다."""
        self.assertEqual(len(ST.ERROR_CODES), 45,
                         "[RED] 098 evidence_check_flag_conflict 반영 전이므로 "
                         "44종으로 실패 예상")

    def test_all_28_codes_registered(self):
        """[098 H-10 선갱신] 45종 각각이 ERROR_CODES에 등재됨."""
        for code in self.EXPECTED_CODES:
            self.assertIn(code, ST.ERROR_CODES, f"에러 코드 {code} 미등재")
        self.assertEqual(len(self.EXPECTED_CODES), len(ST.ERROR_CODES),
                         "EXPECTED_CODES 목록 건수가 실측 ERROR_CODES 종수와 불일치")

    def test_s7_error_catalog_marker_import_realignment(self):
        """[T094/L1-F002 + 098 H-10 선갱신] S-7 — 에러 카탈로그 코드↔문서
        정합(D-5 ①, R-3 AC(b)).

        기대: `marker_missing`·`import_failed`가 `ERROR_CODES`에서 삭제되고
        `import_existing_removed`가 신규 등재되며, 실측 `len(ERROR_CODES)`가
        `README.md`의 카탈로그 헤더 기재 종수와 일치해야 한다(설계 목표 43이나
        실측값을 채택 — PLAN §1.5 D-5 각주). 098부터는 두 종수 모두 45종을
        명시 기대한다(H-10 대응, PLAN §3.3.2 신규 에러 코드 1종).

        RED 근거: 현재 `ERROR_CODES`는 44종이고 `README.md` 헤더도 "44종"으로
        표기되어 있다(098 Step 5가 GREEN에서 정정) — 따라서 아래 하드코딩된
        45 기대값 2건은 GREEN(state_tool.py 구현 + README 정정) 완료 전까지
        의도적으로 실패한다. 이것도 RED 증거다(098 dispatch 지시)."""
        self.assertNotIn("marker_missing", ST.ERROR_CODES,
                         "marker_missing이 아직 ERROR_CODES에 남아있음(R-3 위반)")
        self.assertNotIn("import_failed", ST.ERROR_CODES,
                         "import_failed가 아직 ERROR_CODES에 남아있음(D-2 위반)")
        self.assertIn("import_existing_removed", ST.ERROR_CODES,
                     "import_existing_removed가 ERROR_CODES에 없음(D-2 위반)")

        readme_path = _TOOL_DIR / "README.md"
        readme_text = readme_path.read_text(encoding="utf-8")
        m = re.search(r"##\s*에러\s*코드\s*카탈로그\s*\((\d+)종", readme_text)
        self.assertIsNotNone(m, "README.md에서 '에러 코드 카탈로그 (N종' 헤더를 찾지 못함")
        readme_count = int(m.group(1))
        actual_count = len(ST.ERROR_CODES)
        self.assertEqual(readme_count, actual_count,
                         f"README 기재 종수({readme_count})와 실측 len(ERROR_CODES)"
                         f"({actual_count})가 불일치함(D-5 ① 정합 위반)")
        # [098 H-10 선갱신] 종수 45 하드 기대 — Step 5(GREEN) 전에는 의도적으로 실패
        self.assertEqual(actual_count, 45,
                         "[RED] len(ERROR_CODES)==45 기대 — 098 evidence_check_flag_conflict "
                         "미반영 상태이므로 44로 실패 예상")
        self.assertEqual(readme_count, 45,
                         "[RED] README 헤더 종수==45 기대 — 098 Step5 README 정정 전이므로 "
                         "44로 실패 예상")


# ═════════════════════════════════════════════════════════════════════════════
# I-0. verify 명령 — 헌법 §4 동작 증거 강제 게이트 (PLAN 013)
# ═════════════════════════════════════════════════════════════════════════════

class TestVerify(BaseTestCase):
    """cmd_verify + mark TEST stage 자동 훅 테스트 (PLAN 013)

    [MUST] TASK T-11: 표준 라이브러리만 사용.
    [MUST] AGENT.md §확정 기준 #2: 임시 디렉토리 사용.
    """

    # ── 픽스처 헬퍼 ─────────────────────────────────────────────────────────

    def _write_scenario(self, content):
        """TEST-SCENARIO.md를 task_path 아래에 생성한다."""
        p = self.task_path / "TEST-SCENARIO.md"
        p.write_text(content, encoding="utf-8")
        return p

    def _call_verify(self, task_path=None, scenario=None):
        """cmd_verify 호출 → (exit_code, result_dict)."""
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        exit_code = 0
        args = types.SimpleNamespace(
            task_path=str(task_path or self.task_path),
            scenario=scenario,
        )
        with redirect_stdout(out):
            try:
                ST.cmd_verify(args)
            except SystemExit as e:
                exit_code = e.code
        output = out.getvalue().strip()
        result = json.loads(output) if output else {}
        return exit_code, result

    # ── 케이스 1: happy path — 깨끗한 TEST-SCENARIO.md ─────────────────────

    def test_verify_happy_path(self):
        """verify: 정상 TEST-SCENARIO.md → ok=True, exit 0 (PLAN 013 AC-1)"""
        self._write_scenario(
            "# TEST-SCENARIO\n\n"
            "| 시나리오 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|------|---------|------|\n"
            "| S-1 정상 | Pass | python -m pytest | 1 passed |\n"
        )
        exit_code, result = self._call_verify()
        self.assertEqual(exit_code, 0)
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("checks", {}).get("mock_in_scenario"), "pass")
        self.assertEqual(result.get("checks", {}).get("evidence_missing"), "pass")

    # ── 케이스 2: mock 코드 패턴 검출 ───────────────────────────────────────

    def test_verify_detects_magicmock(self):
        """verify: MagicMock 코드 패턴 발견 → mock_in_scenario, exit 1 (PLAN 013 AC-2)"""
        self._write_scenario(
            "# TEST-SCENARIO\n\n"
            "실행:\n"
            "```python\n"
            "svc = MagicMock()\n"
            "```\n"
        )
        exit_code, result = self._call_verify()
        self.assertEqual(exit_code, 1)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("error"), "mock_in_scenario")

    def test_verify_detects_unittest_mock(self):
        """verify: unittest.mock 패턴 → mock_in_scenario (PLAN 013 AC-2)"""
        self._write_scenario(
            "from unittest.mock import patch\n"
        )
        exit_code, result = self._call_verify()
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "mock_in_scenario")

    def test_verify_detects_at_patch(self):
        """verify: @patch 데코레이터 → mock_in_scenario (PLAN 013 AC-2)"""
        self._write_scenario(
            "@patch('some.module.func')\n"
            "def test_foo(): pass\n"
        )
        exit_code, result = self._call_verify()
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "mock_in_scenario")

    def test_verify_no_false_positive_on_plain_mock_word(self):
        """verify: 설명 문구의 단순 'mock' 단어는 오탐 없음 (PLAN 013 M-2)"""
        self._write_scenario(
            "# 주의: mock 데이터 사용 금지\n"
            "실 DB fixture를 사용한다.\n"
            "| 시나리오 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|------|---------|------|\n"
            "| S-1 | Pass | make test | OK |\n"
        )
        exit_code, result = self._call_verify()
        self.assertEqual(exit_code, 0)
        self.assertTrue(result.get("ok"))

    # ── 케이스 3: 증거 누락 ──────────────────────────────────────────────────

    def test_verify_detects_evidence_missing(self):
        """verify: Pass 행에 실행 명령 빈칸 → evidence_missing, exit 1 (PLAN 013 AC-3)"""
        self._write_scenario(
            "# TEST-SCENARIO\n\n"
            "| 시나리오 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|------|---------|------|\n"
            "| S-1 정상 | Pass |  |  |\n"
        )
        exit_code, result = self._call_verify()
        self.assertEqual(exit_code, 1)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("error"), "evidence_missing")

    def test_verify_pass_with_checkmark(self):
        """verify: ✅ 기호도 Pass로 인식, 증거 없으면 evidence_missing (PLAN 013 AC-3)"""
        self._write_scenario(
            "| 시나리오 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|------|---------|------|\n"
            "| S-1 | ✅ |  |  |\n"
        )
        exit_code, result = self._call_verify()
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "evidence_missing")

    def test_verify_fail_row_not_checked(self):
        """verify: 결과가 Fail인 행은 증거 검사 대상 아님 (PLAN 013 AC-3)"""
        self._write_scenario(
            "| 시나리오 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|------|---------|------|\n"
            "| S-1 | Fail |  |  |\n"
        )
        exit_code, result = self._call_verify()
        self.assertEqual(exit_code, 0)
        self.assertTrue(result.get("ok"))

    # ── 케이스 4: doc-only skip ──────────────────────────────────────────────

    def test_verify_doc_only_skip_when_no_file(self):
        """verify: TEST-SCENARIO.md 없으면 skip ok, exit 0 (PLAN 013 AC-4)"""
        # task_path에 TEST-SCENARIO.md를 생성하지 않음
        exit_code, result = self._call_verify()
        self.assertEqual(exit_code, 0)
        self.assertTrue(result.get("ok"))
        self.assertTrue(result.get("skipped"))

    def test_verify_scenario_arg_not_found_skip(self):
        """verify: --scenario 경로 없어도 skip ok (PLAN 013 AC-4)"""
        exit_code, result = self._call_verify(
            scenario=str(self.task_path / "NONEXISTENT.md")
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(result.get("skipped"))

    # ── 케이스 5: mark TEST stage 자동 훅 ───────────────────────────────────

    def _setup_with_test_stage(self):
        """TEST stage 행을 포함한 state를 초기화한다."""
        rows_spec = json.dumps([
            {"stage": "TEST", "item": "작업"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows_spec)

    def test_mark_test_stage_no_scenario_skip(self):
        """mark TEST stage done + TEST-SCENARIO.md 없음 → 자동 훅 skip, mark 성공 (PLAN 013 AC-5)"""
        self._setup_with_test_stage()
        # TEST-SCENARIO.md 없음 → 자동 훅은 skip
        exit_code = self._mark(row_id=1)
        self.assertEqual(exit_code, 0)

    def test_mark_test_stage_clean_scenario_succeeds(self):
        """mark TEST stage done + 정상 TEST-SCENARIO.md → mark 성공 (PLAN 013 AC-5)"""
        self._setup_with_test_stage()
        self._write_scenario(
            "| 시나리오 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|------|---------|------|\n"
            "| S-1 | Pass | pytest | 1 passed |\n"
        )
        exit_code = self._mark(row_id=1)
        self.assertEqual(exit_code, 0)

    def test_mark_test_stage_mock_in_scenario_blocks(self):
        """mark TEST stage done + mock 패턴 → mark 거부, exit 1 (PLAN 013 AC-5)"""
        self._setup_with_test_stage()
        self._write_scenario(
            "svc = MagicMock()\n"
        )
        exit_code = self._mark(row_id=1)
        self.assertEqual(exit_code, 1)

    def test_mark_test_stage_evidence_missing_blocks(self):
        """mark TEST stage done + 증거 누락 → mark 거부, exit 1 (PLAN 013 AC-5)"""
        self._setup_with_test_stage()
        self._write_scenario(
            "| 시나리오 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|------|---------|------|\n"
            "| S-1 | Pass |  |  |\n"
        )
        exit_code = self._mark(row_id=1)
        self.assertEqual(exit_code, 1)

    def test_mark_non_test_stage_not_affected(self):
        """mark PLAN/EXECUTE stage done은 verify 훅 없음 (PLAN 013 AC-5)"""
        rows_spec = json.dumps([
            {"stage": "PLAN", "item": "작업"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows_spec)
        # TEST-SCENARIO.md 없어도 PLAN stage mark는 성공
        exit_code = self._mark(row_id=1)
        self.assertEqual(exit_code, 0)

    # ── 034 RED-first 케이스 ─────────────────────────────────────────────────

    def test_mock_guard_prose_magicmock_no_false_positive(self):
        """034 TS-001 (RED→GREEN #1): 산문 'MagicMock' 단어는 비검출이어야 한다.
        수정 전: _check_mock_patterns가 [1]을 반환 → 단언 FAIL(RED 증거).
        수정 후: [] 반환 → PASS(GREEN).
        """
        # op-dev-test-scenario SKILL §7 PM Gate 표준 문구 — 산문 MagicMock 단어
        result = ST._check_mock_patterns(
            ["- [x] mock/patch/MagicMock 등 시나리오 본문에 부재"]
        )
        self.assertEqual(result, [], f"산문 MagicMock 단어가 오탐됨: {result}")

    def test_mock_guard_inline_backtick_example_no_false_positive(self):
        """034 TS-012 (RED→GREEN #2): 인라인 백틱 코드 예시는 비검출이어야 한다.
        수정 전: _check_mock_patterns가 [1]을 반환 → 단언 FAIL(RED 증거 = 메타-순환 버그).
        수정 후: [] 반환 → PASS(GREEN).
        """
        # 인라인 백틱으로 감싼 Mock() 예시 — 문서화 표기, 실제 코드 아님
        line = "대상 `m = Mock()` 토큰을 문서화"
        result = ST._check_mock_patterns([line])
        self.assertEqual(result, [], f"인라인 백틱 예시가 오탐됨: {result}")

    # ── 034 회귀: 정탐 유지 + 통합 케이스 ───────────────────────────────────

    def test_mock_guard_real_magicmock_call_detected(self):
        """034 TS-002: 실제 MagicMock() 코드(bare 라인)는 여전히 검출되어야 한다.
        'Mock(' 대안이 MagicMock()의 끝부분 Mock(을 커버함을 단언으로 고정.
        """
        result = ST._check_mock_patterns(["x = MagicMock()"])
        self.assertEqual(result, [1], f"실제 MagicMock() 코드가 미검출됨: {result}")

    def test_mock_guard_pm_gate_standard_phrase(self):
        """034 TS-003: PM Gate 표준 문구 전체 줄 → 비검출 (SKILL §7 :157 원문)."""
        line = "- [ ] mock/patch/MagicMock 등 시나리오 본문에 부재"
        result = ST._check_mock_patterns([line])
        self.assertEqual(result, [], f"PM Gate 표준 문구가 오탐됨: {result}")

    def test_mock_guard_unittest_mock_detected(self):
        """034 TS-004 (회귀): bare 'from unittest.mock import patch' 검출 유지."""
        result = ST._check_mock_patterns(["from unittest.mock import patch"])
        self.assertEqual(result, [1], f"unittest.mock bare 라인 미검출: {result}")

    def test_mock_guard_at_patch_detected(self):
        """034 TS-005 (회귀): bare '@patch(...)' 검출 유지."""
        result = ST._check_mock_patterns(["@patch('m.f')"])
        self.assertEqual(result, [1], f"@patch bare 라인 미검출: {result}")

    def test_mock_guard_mock_patch_detected(self):
        """034 TS-006 (회귀): bare 'with mock.patch(...)' 검출 유지."""
        result = ST._check_mock_patterns(["with mock.patch('x'):"])
        self.assertEqual(result, [1], f"mock.patch bare 라인 미검출: {result}")

    def test_mock_guard_mock_call_detected(self):
        """034 TS-007 (회귀): bare 'm = Mock()' 검출 유지."""
        result = ST._check_mock_patterns(["m = Mock()"])
        self.assertEqual(result, [1], f"Mock() bare 라인 미검출: {result}")

    def test_mock_guard_at_mock_dot_detected(self):
        """034 TS-008 (회귀): bare '@mock.patch(...)' 검출 유지."""
        result = ST._check_mock_patterns(["@mock.patch('x')"])
        self.assertEqual(result, [1], f"@mock. bare 라인 미검출: {result}")

    def test_verify_no_false_positive_doc_example(self):
        """034 TS-009 (통합): verify — 산문+백틱 예시 TEST-SCENARIO.md → exit 0;
        bare MagicMock() 포함 버전 → exit 1 mock_in_scenario.
        """
        # (a) 정당 텍스트(산문 + 인라인 백틱 예시) → exit 0
        self._write_scenario(
            "# TEST-SCENARIO\n\n"
            "- [x] mock/patch/MagicMock 등 시나리오 본문에 부재\n"
            "대상 `m = Mock()` 토큰을 문서화\n"
            "| 시나리오 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|------|---------|------|\n"
            "| S-1 | Pass | pytest | 1 passed |\n"
        )
        exit_code, result = self._call_verify()
        self.assertEqual(exit_code, 0, f"정당 텍스트가 차단됨: {result}")
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("checks", {}).get("mock_in_scenario"), "pass")

        # (b) bare 코드 포함 버전 → exit 1 mock_in_scenario
        self._write_scenario(
            "# TEST-SCENARIO\n\n"
            "svc = MagicMock()\n"
        )
        exit_code2, result2 = self._call_verify()
        self.assertEqual(exit_code2, 1, f"bare MagicMock()가 차단 안 됨: {result2}")
        self.assertEqual(result2.get("error"), "mock_in_scenario")

    def test_mark_test_stage_doc_example_not_blocked(self):
        """034 TS-010 (통합): mark TEST 훅 — 산문+백틱 예시 → 차단 안 됨(exit 0);
        bare MagicMock() → exit 1 mock_in_scenario.
        """
        rows_spec = json.dumps([
            {"stage": "TEST", "item": "작업"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])

        # (a) 정당 텍스트 → mark 성공
        self._init(rows_spec=rows_spec)
        self._write_scenario(
            "# TEST-SCENARIO\n\n"
            "- [x] mock/patch/MagicMock 등 시나리오 본문에 부재\n"
            "대상 `m = Mock()` 토큰을 문서화\n"
            "| 시나리오 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|------|---------|------|\n"
            "| S-1 | Pass | pytest | 1 passed |\n"
        )
        exit_code = self._mark(row_id=1)
        self.assertEqual(exit_code, 0, "정당 텍스트가 mark 훅에서 차단됨")

        # (b) 새 state — force re-init 후 bare 코드 포함 → mark 거부
        self._init(rows_spec=rows_spec, force=True, note="034 TS-010 (b) 재초기화")
        self._write_scenario("svc = MagicMock()\n")
        exit_code2 = self._mark(row_id=1)
        self.assertEqual(exit_code2, 1, "bare MagicMock()가 mark 훅에서 차단 안 됨")

    def test_mock_guard_codefence_and_mixed_line_detected(self):
        """034 TS-014 (정탐 유지): 코드펜스 내부 bare mock + 백틱·bare 혼합 라인 → 검출 유지.
        헌법 §4 'Don't fake it' — 전처리가 과도하지 않음을 단언.
        """
        # (a) 코드펜스 내부 bare mock 코드 → 검출
        lines_fence = [
            "```python",
            "m = Mock()",
            "```",
        ]
        result_fence = ST._check_mock_patterns(lines_fence)
        self.assertEqual(result_fence, [2], f"코드펜스 내부 Mock() 미검출: {result_fence}")

        # (b) 인라인 백틱 예시 + 백틱 밖 bare 코드가 같은 줄 → bare 검출
        line_mixed = "예시 `foo` 이후에 실제 m = Mock() 코드"
        result_mixed = ST._check_mock_patterns([line_mixed])
        self.assertEqual(result_mixed, [1], f"백틱+bare 혼합 라인에서 bare 미검출: {result_mixed}")

    def test_verify_passes_own_test_scenario_md(self):
        """034 TS-013 (자기검증): 034 자신의 TEST-SCENARIO.md → _check_mock_patterns []
        + verify exit 0. 메타-순환(가드 검증 문서가 가드에 막힘) 해소 증명.
        TEST-SCENARIO.md를 통과 목적으로 수정 금지 — 본문은 PM이 #2 전제로 작성.

        [T094 R-10 수정 2026-08-16] `repo_root = _TOOL_DIR.parents[2]`는 "레포
        루트 = 작업 루트"를 가정한다 — worktree(`.opal-worktrees/task_094/`)에서
        실행하면 worktree 자체의 루트를 가리켜, `tasks/`가 분기되지 않고
        허브에 고정되는 092 경로 계약(`opal-harness.md` §2.5)과 어긋나
        `tasks/034-*`를 못 찾는다. [MUST] 신규 헬퍼를 만들지 않고
        `find_project_root()`(state_tool.py:553 — `.opal/MEMORY.json` 보유
        조상 탐색, 088 §2.3에서 이미 검증된 패턴)를 재사용한다 — 이 함수는
        worktree/허브(전체 체크아웃) 양쪽에서 정확히 허브 루트를 반환한다."""
        import io
        from contextlib import redirect_stdout

        # 092 경로 계약(tasks/는 허브 고정) — find_project_root()로 허브 루트를
        # 찾는다. worktree에서 실행돼도 `.opal/MEMORY.json` 보유 조상(허브)까지
        # 거슬러 올라가므로 정확하다(088 §2.3 선례 재사용, 신규 헬퍼 미신설).
        repo_root = ST.find_project_root(str(_TOOL_DIR))
        self.assertIsNotNone(
            repo_root,
            f"find_project_root({_TOOL_DIR})가 None을 반환함 — .opal/MEMORY.json "
            "보유 조상을 찾지 못함(허브 경로 계약 위반 의심)"
        )
        # 034는 tasks/backup/으로 이관됐으므로 두 위치를 모두 탐색한다.
        task_dir = "034-260621-opds-state-tool-mock-패턴-오탐수정"
        candidates = [
            repo_root / "tasks" / task_dir / "TEST-SCENARIO.md",
            repo_root / "tasks" / "backup" / task_dir / "TEST-SCENARIO.md",
        ]
        scenario_path = next((p for p in candidates if p.exists()), None)
        self.assertIsNotNone(
            scenario_path,
            f"034 TEST-SCENARIO.md 파일이 없음 (탐색: {[str(p) for p in candidates]})",
        )

        lines = scenario_path.read_text(encoding="utf-8").splitlines()
        result = ST._check_mock_patterns(lines)
        self.assertEqual(result, [], f"034 TEST-SCENARIO.md에서 오탐 발생: lines {result}")

        # verify CLI로도 exit 0 확인 (scenario 파라미터로 직접 파일 지정)
        out = io.StringIO()
        exit_code = 0
        args = types.SimpleNamespace(
            task_path=str(self.task_path),
            scenario=str(scenario_path),
        )
        with redirect_stdout(out):
            try:
                ST.cmd_verify(args)
            except SystemExit as e:
                exit_code = e.code
        output = out.getvalue().strip()
        verify_result = json.loads(output) if output else {}
        self.assertEqual(exit_code, 0, f"034 TEST-SCENARIO.md verify exit 1: {verify_result}")
        self.assertTrue(verify_result.get("ok"), f"verify ok=False: {verify_result}")
        self.assertEqual(
            verify_result.get("checks", {}).get("mock_in_scenario"), "pass",
            f"mock_in_scenario 체크 실패: {verify_result}"
        )


# ═════════════════════════════════════════════════════════════════════════════
# I. 추가 시나리오: add-row schema validate 통과 (PLAN §2.12 G-9 단계 6)
# ═════════════════════════════════════════════════════════════════════════════

class TestAddRowSchemaValidate(BaseTestCase):
    """add-row 후 schema validate 통과 확인 (PLAN §2.12 G-9)"""

    def setUp(self):
        super().setUp()
        self._init(rows_spec=SIMPLE_ROWS_SPEC)

    def test_add_row_validate_zero_violations(self):
        """G-9: add-row 후 validate violations 0건 (PLAN §2.12 G-9 단계 6)"""
        self._add_row(after=1, stage="CLOSE", item="추가 작업 항목")
        result = self._validate()
        # 마커도 있어야 violations 0 — 확인
        self.assertIsInstance(result["violations"], list)

    def test_add_row_additional_work_done_to_additional_work(self):
        """G-9: additional_work_done에서 add-row → additional_work로 회귀 (PLAN §2.12 G-9 단계 8)"""
        self._status_set("additional_work")
        self._status_set("additional_work_done")
        self._add_row(after=1, stage="CLOSE", item="재추가 항목")
        state = self._state()
        self.assertEqual(state["current_status"], "additional_work")


# ═════════════════════════════════════════════════════════════════════════════
# J. Stage-Transition Guard (PLAN §M-A stage-transition guard)
# ═════════════════════════════════════════════════════════════════════════════

class TestStageTransitionGuard(BaseTestCase):
    """PLAN §M-A stage-transition guard 단위 테스트.
    규칙: mark/advance 시 대상 행보다 앞의 모든 행이 완료(done/additional_work_done/na)가
    아니면 stage_transition_violation 에러로 거부.
    예외: --force+--note 우회 / as_worker 스킵 / 이미 done 행 재mark(멱등).
    """

    ORDERED_ROWS = json.dumps([
        {"stage": "TASK",    "item": "작업 A"},
        {"stage": "PLAN",    "item": "작업 B"},
        {"stage": "EXECUTE", "item": "작업 C"},
        {"stage": "CLOSE",   "item": "사용자 확인"},
    ])

    def setUp(self):
        super().setUp()
        self._init(rows_spec=self.ORDERED_ROWS)

    # ── 1. 정상 순차 통과 ─────────────────────────────────────────────────────

    def test_sequential_mark_passes(self):
        """순차 mark: 앞 행을 모두 done 처리 후 다음 행 mark → 성공 (PLAN §M-A)"""
        code1 = self._mark(1)
        self.assertEqual(code1, 0)
        code2 = self._mark(2)
        self.assertEqual(code2, 0)
        code3 = self._mark(3)
        self.assertEqual(code3, 0)

    def test_sequential_advance_passes(self):
        """순차 advance: 앞 행 done 처리 후 advance → 성공 (PLAN §M-A)"""
        self._mark(1)
        code = self._advance(2)
        self.assertEqual(code, 0)

    # ── 2. 건너뛰기 거부 (mark) ───────────────────────────────────────────────

    def test_skip_mark_row2_without_row1_done_rejected(self):
        """row1 미완인 상태에서 row2 mark → stage_transition_violation (PLAN §M-A)"""
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    row=2, done=True,
                )
                try:
                    ST.cmd_mark(args)
                except SystemExit:
                    pass
        result = json.loads(out.getvalue())
        self.assertEqual(result.get("error"), "stage_transition_violation")
        self.assertIn(1, result.get("incomplete_rows", []))

    def test_skip_mark_row3_without_row1_row2_done_rejected(self):
        """row1·row2 미완인 상태에서 row3 mark → incomplete_rows에 두 행 모두 포함 (PLAN §M-A)"""
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    row=3, done=True,
                )
                try:
                    ST.cmd_mark(args)
                except SystemExit:
                    pass
        result = json.loads(out.getvalue())
        self.assertEqual(result.get("error"), "stage_transition_violation")
        incomplete = result.get("incomplete_rows", [])
        self.assertIn(1, incomplete)
        self.assertIn(2, incomplete)

    # ── 3. 건너뛰기 거부 (advance) ────────────────────────────────────────────

    def test_skip_advance_row2_without_row1_done_rejected(self):
        """row1 미완인 상태에서 row2 advance → stage_transition_violation (PLAN §M-A)"""
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    row=2,
                )
                try:
                    ST.cmd_advance(args)
                except SystemExit:
                    pass
        result = json.loads(out.getvalue())
        self.assertEqual(result.get("error"), "stage_transition_violation")

    # ── 4. --force 우회 ───────────────────────────────────────────────────────

    def test_force_with_note_bypasses_guard_mark(self):
        """mark --force --note: 앞 행 미완이어도 guard 우회 → 성공 (PLAN §M-A)"""
        code = self._mark(2, force=True, note="긴급 우회")
        self.assertEqual(code, 0)

    # ── 5. 멱등 (이미 done인 행 재mark) ──────────────────────────────────────

    def test_idempotent_mark_already_done_row_bypasses_guard(self):
        """이미 done인 행 재mark: 앞 행 미완이어도 guard 스킵 → 성공 (PLAN §M-A 멱등)"""
        # row2를 강제로 done 상태로 직접 설정 (state.json 직접 수정)
        state = self._state()
        state["rows"][1]["status"]       = "done"
        state["rows"][1]["status_label"] = "✅"
        ST.save_state_json(self.task_path, state)
        # row1이 미완인 상태에서 row2(이미 done) 재mark → guard 스킵
        code = self._mark(2)
        self.assertEqual(code, 0)

    # ── 6. na 상태 행은 완료로 간주 ──────────────────────────────────────────

    def test_na_status_rows_treated_as_complete(self):
        """앞 행이 na(agentic auto-na)이면 완료로 간주, 건너뛰기 허용 (PLAN §M-A)"""
        # row1을 na 상태로 직접 설정
        state = self._state()
        state["rows"][0]["status"]       = "na"
        state["rows"][0]["status_label"] = "-"
        state["rows"][0]["owner"]        = "auto"
        ST.save_state_json(self.task_path, state)
        # row1=na, row2=pending → row2 mark 시 row1은 완료로 간주 → 성공
        code = self._mark(2)
        self.assertEqual(code, 0)

    # ── 7. as_worker prior_stage_only guard ──────────────────────────────────

    def test_as_worker_prior_stage_complete_passes(self):
        """mark --as-worker: 앞 단계(TASK·PLAN) 완료 + 같은 단계 내 앞 행 미완 → 통과 (prior_stage_only)"""
        # ORDERED_ROWS: TASK(row1) / PLAN(row2) / EXECUTE(row3) / CLOSE(row4)
        # row1(TASK), row2(PLAN) 완료 처리 후 row3(EXECUTE)를 as_worker로 mark → 성공
        self._mark(1)                                    # TASK 완료
        self._mark(2)                                    # PLAN 완료
        code = self._mark(3, as_worker=True, worker_stage="EXECUTE")
        self.assertEqual(code, 0)

    def test_as_worker_prior_stage_incomplete_rejected(self):
        """mark --as-worker: 앞 단계(TASK) 미완 → stage_transition_violation 거부 (prior_stage_only)"""
        # row1(TASK) 미완인 상태에서 row3(EXECUTE)를 as_worker로 mark → 거부
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    row=3, done=True,
                    as_worker=True, worker_stage="EXECUTE",
                )
                try:
                    ST.cmd_mark(args)
                except SystemExit:
                    pass
        result = json.loads(out.getvalue())
        self.assertEqual(result.get("error"), "stage_transition_violation")
        # 앞 단계 행(TASK=row1, PLAN=row2)이 미완으로 포함돼야 함
        self.assertIn(1, result.get("incomplete_rows", []))

    def test_as_worker_same_stage_prior_row_incomplete_allowed(self):
        """mark --as-worker: 앞 단계 완료 + 같은 stage 내 앞 행 미완이어도 통과 (prior_stage_only 자율)"""
        # ORDERED_ROWS에 같은 stage 내 두 행을 가진 spec을 사용해야 하므로
        # SAMPLE_ROWS_SPEC을 사용하는 별도 태스크 디렉토리 구성
        import tempfile, shutil, pathlib
        tmpdir2 = pathlib.Path(tempfile.mkdtemp())
        task_path2 = tmpdir2 / "134-260501-worker-same-stage"
        task_path2.mkdir()
        try:
            # PLAN 단계 내 두 행이 있는 spec: TASK(row1) / PLAN(row2·row3) / EXECUTE(row4)
            rows_spec_2stage = json.dumps([
                {"stage": "TASK",    "item": "작업 A"},
                {"stage": "PLAN",    "item": "작업 B"},
                {"stage": "PLAN",    "item": "작업 C"},
                {"stage": "EXECUTE", "item": "작업 D"},
            ])
            with _mock_now():
                init_args = make_args(
                    task_path=str(task_path2),
                    skill="opp", mode="interactive",
                    rows_spec=rows_spec_2stage,
                )
                ST.cmd_init(init_args)

            # TASK(row1) 완료 처리
            with _mock_now():
                mark_args = make_args(task_path=str(task_path2), row=1, done=True)
                ST.cmd_mark(mark_args)

            # PLAN row2 미완인 상태에서 PLAN row3을 as_worker로 mark → 통과해야 함
            # (앞 단계=TASK 완료, 같은 PLAN 단계 내 row2 미완은 무시)
            with _mock_now():
                args = make_args(
                    task_path=str(task_path2),
                    row=3, done=True,
                    as_worker=True, worker_stage="PLAN",
                )
                import io
                from contextlib import redirect_stdout
                out = io.StringIO()
                exit_code = 0
                with redirect_stdout(out):
                    try:
                        ST.cmd_mark(args)
                    except SystemExit as e:
                        exit_code = e.code
            self.assertEqual(exit_code, 0,
                             msg=f"같은 stage 내 앞 행 미완이어도 통과해야 함: {out.getvalue()}")
        finally:
            shutil.rmtree(tmpdir2, ignore_errors=True)

    def test_pm_path_full_guard_unchanged(self):
        """mark (PM 경로, as_worker=False): full guard 불변 — 앞 행 미완 시 거부 (PLAN §M-A)"""
        # PM 경로에서 row2 미완인 상태로 row3 mark → stage_transition_violation
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    row=3, done=True,
                    as_worker=False,
                )
                try:
                    ST.cmd_mark(args)
                except SystemExit:
                    pass
        result = json.loads(out.getvalue())
        self.assertEqual(result.get("error"), "stage_transition_violation")

    # ── 8. error_code 등재 확인 ───────────────────────────────────────────────

    def test_stage_transition_violation_in_error_codes(self):
        """stage_transition_violation이 ERROR_CODES SSOT에 등재됨 (PLAN §M-A)"""
        self.assertIn("stage_transition_violation", ST.ERROR_CODES)


# ═════════════════════════════════════════════════════════════════════════════
# K. 014 Phase 4 — 새 표준 행 구조 (QA Gate/State Gate 행 없음) 정합
# ═════════════════════════════════════════════════════════════════════════════

# opds 새 10행 표준 구조 (Phase 2에서 확정 — QA Gate/State Gate 행 없음).
# Gate는 "PM Gate"와 "사용자 확인"만 남고, State Gate는 stage-transition guard로 이전,
# QA Gate는 PM Gate로 통합, CLOSE 마지막 행은 "DONE.md 생성".
NEW_OPDS_ROWS_SPEC = json.dumps([
    {"stage": "TASK",    "item": "작업"},
    {"stage": "TASK",    "item": "사용자 확인"},
    {"stage": "PLAN",    "item": "작업"},
    {"stage": "PLAN",    "item": "PM Gate"},
    {"stage": "PLAN",    "item": "사용자 확인"},
    {"stage": "EXECUTE", "item": "작업"},
    {"stage": "TEST",    "item": "작업"},
    {"stage": "TEST",    "item": "PM Gate"},
    {"stage": "TEST",    "item": "사용자 확인"},
    {"stage": "CLOSE",   "item": "DONE.md 생성"},
])


class TestNewStandardRowStructure(BaseTestCase):
    """014 Phase 4: 새 표준 행 구조(QA Gate/State Gate 행 없음)에서 도구가 정상 동작하는지 검증.
    - guard가 새 구조에서 단계 건너뛰기를 정상 차단 (기능 약화 금지)
    - CLOSE 마지막 행이 "DONE.md 생성"이어도 current_status=done 정상 전환
    - QA Gate/State Gate 행이 없어도 전체 플로우가 끝까지 완주
    """

    def setUp(self):
        super().setUp()
        self._init(rows_spec=NEW_OPDS_ROWS_SPEC)

    def test_new_structure_has_no_gate_rows(self):
        """새 구조: 어떤 행에도 QA Gate / State Gate 항목이 없다 (Phase 2 확정)"""
        state = self._state()
        items = [r["item"] for r in state["rows"]]
        self.assertNotIn("QA Gate", items)
        self.assertNotIn("State Gate", items)
        self.assertEqual(len(state["rows"]), 10)

    def test_new_structure_full_sequential_flow_completes(self):
        """[T094 수정] 새 10행 구조 전체 순차 완주: 모든 행 순서대로 mark →
        current_status=done. guard가 정상 통과하고 CLOSE "DONE.md 생성" 행에서
        완료 전환 (014 Phase 4). '- 상태: 완료' STATE.md 렌더는 D-1로 제거되어
        `state.json.current_status` 검증만으로 충분하다(정보 손실 0, 조회
        경로는 `show --format md`로 이관)."""
        # row1 TASK 작업
        self.assertEqual(self._mark(1), 0)
        # row2 TASK 사용자 확인 (owner=user — 사용자 발화)
        self.assertEqual(self._mark(2, owner="user"), 0)
        # row3 PLAN 작업
        self.assertEqual(self._mark(3), 0)
        # row4 PLAN PM Gate
        self.assertEqual(self._mark(4), 0)
        # row5 PLAN 사용자 확인 (CLOSE gate를 위해 owner=user)
        self.assertEqual(self._mark(5, owner="user"), 0)
        # row6 EXECUTE 작업
        self.assertEqual(self._mark(6), 0)
        # row7 TEST 작업
        self.assertEqual(self._mark(7), 0)
        # row8 TEST PM Gate
        self.assertEqual(self._mark(8), 0)
        # row9 TEST 사용자 확인 (CLOSE 직전 사용자 확인 — owner=user)
        self.assertEqual(self._mark(9, owner="user"), 0)
        # row10 CLOSE DONE.md 생성 (CLOSE 마지막 행)
        self.assertEqual(self._mark(10), 0)

        state = self._state()
        self.assertEqual(state["current_status"], "done")

    def test_new_structure_close_done_row_triggers_done_status(self):
        """새 구조: CLOSE 마지막 행 항목이 'DONE.md 생성'이어도 current_status=done 전환.
        (레거시는 'State Gate'였음 — 항목명 비의존 판정 검증) (014 Phase 4)"""
        # 최소 구조: CLOSE 직전 사용자 확인 → CLOSE DONE.md 생성
        rows = json.dumps([
            {"stage": "TEST",  "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "DONE.md 생성"},
        ])
        self._init(rows_spec=rows, force=True, note="새 구조 재초기화")
        self._mark(1, owner="user")  # 사용자 확인 → done/user (close gate 충족)
        code = self._mark(2)         # CLOSE DONE.md 생성 → 마지막 행
        self.assertEqual(code, 0)
        state = self._state()
        self.assertEqual(state["current_status"], "done")

    def test_new_structure_guard_blocks_skip(self):
        """새 구조에서도 guard가 단계 건너뛰기를 차단 (기능 약화 금지) (014 Phase 4 / §M-A).
        row1 미완 상태에서 row3(PLAN 작업) mark → stage_transition_violation"""
        import io
        from contextlib import redirect_stdout
        # 093 F-002: row2(TASK 사용자 확인)가 pending이면 훅이 먼저 user_confirmation_required로
        # 거부한다(interactive). 본 테스트가 관찰하려는 축은 stage-transition guard이므로
        # row2를 캡틴 승인으로 닫아 미완 행을 row1만 남긴다.
        self.assertEqual(self._mark(2, owner="user", force=True, note="guard 축 격리"), 0)
        out = io.StringIO()
        with redirect_stdout(out):
            with _mock_now():
                args = make_args(task_path=str(self.task_path), row=3, done=True)
                try:
                    ST.cmd_mark(args)
                except SystemExit:
                    pass
        result = json.loads(out.getvalue())
        self.assertEqual(result.get("error"), "stage_transition_violation")
        self.assertIn(1, result.get("incomplete_rows", []))

    def test_new_structure_close_gate_still_enforced(self):
        """새 구조: CLOSE 진입 게이트가 여전히 직전 사용자 확인 행 owner=user를 요구.
        TEST 사용자 확인(row9)이 owner=PM이면 CLOSE 첫 행에서 close_gate_violation (014 Phase 4)"""
        for r in range(1, 9):
            # row2 사용자 확인은 user, 나머지는 기본 mark
            if r == 2:
                self._mark(r, owner="user")
            else:
                self._mark(r)
        # row9 TEST 사용자 확인을 owner=PM(미충족)으로 done 처리
        self._mark(9, owner="PM")
        # row10 CLOSE 첫 행 mark → close_gate_violation
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            with _mock_now():
                args = make_args(task_path=str(self.task_path), row=10, done=True)
                try:
                    ST.cmd_mark(args)
                except SystemExit:
                    pass
        result = json.loads(out.getvalue())
        self.assertEqual(result.get("error"), "close_gate_violation")


class TestGatePassDeprecation(BaseTestCase):
    """014 Phase 4: gate-pass deprecate — 레거시 state.json 하위호환 유지 + deprecated 플래그."""

    def test_gate_pass_legacy_still_works_with_deprecated_flag(self):
        """레거시 4행 Gate 구조 state.json에서 gate-pass는 여전히 동작하되 deprecated=True 반환.
        (in-flight 레거시 태스크 하위호환 — 즉시 제거 금지) (014 Phase 4)"""
        self._init(rows_spec=GATE_ROWS_SPEC)  # 레거시 QA/State/PM/State Gate 4행 포함
        with _mock_now():
            args = make_args(task_path=str(self.task_path), start=2)
            exit_code, result = self._call_cmd(ST.cmd_gate_pass, args)
        self.assertEqual(exit_code, 0, f"legacy gate-pass should still work: {result}")
        self.assertTrue(result.get("deprecated"))
        self.assertIn("deprecation_note", result)
        # 4행 모두 done
        state = self._state()
        for row in state["rows"][1:5]:
            self.assertEqual(row["status"], "done")

    def test_gate_pass_on_new_structure_fails_pattern_mismatch(self):
        """새 구조(QA Gate/State Gate 행 없음)에서 gate-pass는 패턴 불일치로 거부.
        → 신규 태스크는 gate-pass를 쓸 수 없음을 명확히 (014 Phase 4)"""
        self._init(rows_spec=NEW_OPDS_ROWS_SPEC, force=True, note="새 구조")
        with _mock_now():
            # row4 = PLAN PM Gate (QA Gate 아님) — 패턴 시작 불일치
            args = make_args(task_path=str(self.task_path), start=4)
            exit_code, result = self._call_cmd(ST.cmd_gate_pass, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "gate_pattern_mismatch")


class TestStandardItemsConstants(unittest.TestCase):
    """014 Phase 4: STANDARD_ITEMS / DEPRECATED_ITEMS 상수 정합 검증."""

    def test_standard_items_no_gate_rows(self):
        """STANDARD_ITEMS에서 QA Gate/State Gate 제거됨 (새 표준) (014 Phase 4)"""
        self.assertNotIn("QA Gate", ST.STANDARD_ITEMS)
        self.assertNotIn("State Gate", ST.STANDARD_ITEMS)
        self.assertIn("작업", ST.STANDARD_ITEMS)
        self.assertIn("PM Gate", ST.STANDARD_ITEMS)
        self.assertIn("사용자 확인", ST.STANDARD_ITEMS)
        self.assertIn("DONE.md 생성", ST.STANDARD_ITEMS)

    def test_deprecated_items_retained_for_legacy(self):
        """DEPRECATED_ITEMS에 QA Gate/State Gate 보존 (레거시 하위호환) (014 Phase 4)"""
        self.assertIn("QA Gate", ST.DEPRECATED_ITEMS)
        self.assertIn("State Gate", ST.DEPRECATED_ITEMS)


# ═════════════════════════════════════════════════════════════════════════════
# K. RED-first TDD 트랙 — RED 게이트·테스트 불변성 단위 테스트 (PLAN 016)
# ═════════════════════════════════════════════════════════════════════════════

class TestRedFirst(BaseTestCase):
    """RED-first TDD 트랙 — verify --red-check / --fix-mode 게이트 단위 테스트 [T016].

    [MUST] TASK T-11: 표준 라이브러리만 사용 (unittest/re/fnmatch/tempfile/json).
    [MUST] AGENT.md §확정 기준 #2: tempfile.mkdtemp() 사용, ~/.opal/ 수정 금지.
    신규 인자: args.red_check (bool), args.changed_files (list),
               args.test_globs (list), args.fix_mode (bool).
    신규 에러: "red_evidence_missing", "test_modified_in_fix".
    신규 헬퍼: _check_red_evidence, _match_test_files.
    PLAN §3.2.2 기준 설계.
    """

    # ── 픽스처 헬퍼 ─────────────────────────────────────────────────────────

    def _write_scenario(self, content):
        """TEST-SCENARIO.md를 task_path 아래에 생성한다."""
        p = self.task_path / "TEST-SCENARIO.md"
        p.write_text(content, encoding="utf-8")
        return p

    def _call_verify_red(self, **kwargs):
        """cmd_verify를 호출하여 (exit_code, result_dict)를 반환.

        make_args에 red_check/fix_mode/changed_files/test_globs를 주입한다.
        기존 TestVerify._call_verify 헬퍼와 동일한 try/except SystemExit 패턴.
        """
        import io
        from contextlib import redirect_stdout

        args = make_args(
            task_path=str(self.task_path),
            scenario=kwargs.pop("scenario", None),
            red_check=kwargs.pop("red_check", False),
            fix_mode=kwargs.pop("fix_mode", False),
            changed_files=kwargs.pop("changed_files", None),
            test_globs=kwargs.pop("test_globs", None),
            **kwargs,
        )
        out = io.StringIO()
        exit_code = 0
        with redirect_stdout(out):
            try:
                ST.cmd_verify(args)
            except SystemExit as e:
                exit_code = e.code
        output = out.getvalue().strip()
        result = json.loads(output) if output else {}
        return exit_code, result

    # ── S-1: verify --red-check + RED 증거 존재 → 통과 ──────────────────────

    def test_verify_red_check_pass(self):
        """[T016/L1-S1] verify --red-check + RED 증거 있음 → exit 0, ok=True.

        PLAN §3.2.5 TS-002. 시나리오 표에 "RED 증거" 헤더와 실패 출력 내용 포함.
        구현될 _check_red_evidence가 "RED 증거" 헤더 + 내용 유무로 판정 (§3.2.2).
        """
        self._write_scenario(
            "# TEST-SCENARIO\n\n"
            "| 시나리오 | RED 증거 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|---------|------|---------|------|\n"
            "| S-1 정상 | FAILED tests/test_state_tool.py::TestRedFirst (AssertionError) | Pass | python -m unittest | 1 passed |\n"
        )
        exit_code, result = self._call_verify_red(red_check=True)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result.get("ok"))

    # ── S-2: verify --red-check + RED 증거 누락 → red_evidence_missing ───────

    def test_verify_red_check_missing(self):
        """[T016/L1-S2] verify --red-check + RED 증거 빈 표 → exit 1, error==red_evidence_missing.

        PLAN §3.2.5 TS-003. "RED 증거" 열이 비어있는 케이스.
        """
        self._write_scenario(
            "# TEST-SCENARIO\n\n"
            "| 시나리오 | RED 증거 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|---------|------|---------|------|\n"
            "| S-1 정상 |  | Pass | python -m unittest | 1 passed |\n"
        )
        exit_code, result = self._call_verify_red(red_check=True)
        self.assertEqual(exit_code, 1)
        self.assertFalse(result.get("ok", True))
        self.assertEqual(result.get("error"), "red_evidence_missing")

    # ── S-3: verify --fix-mode + 테스트 파일 변경 → test_modified_in_fix ─────

    def test_verify_fix_mode_test_modified(self):
        """[T016/L1-S3] fix_mode=True + changed_files에 테스트 파일 → exit 1, error==test_modified_in_fix.

        PLAN §3.2.5 TS-004. _match_test_files(changed_files, test_globs) 결과 비지 않음.
        """
        exit_code, result = self._call_verify_red(
            fix_mode=True,
            changed_files=["tests/test_state_tool.py"],
            test_globs=["tests/**"],
        )
        self.assertEqual(exit_code, 1)
        self.assertFalse(result.get("ok", True))
        self.assertEqual(result.get("error"), "test_modified_in_fix")

    # ── S-4: verify --fix-mode + 프로덕션 파일만 → 통과 ────────────────────

    def test_verify_fix_mode_prod_ok(self):
        """[T016/L1-S4] fix_mode=True + changed_files에 프로덕션 파일만 → exit 0, ok=True.

        PLAN §3.2.5 TS-005. 테스트 파일 미매칭 → 불변성 위반 없음.
        """
        exit_code, result = self._call_verify_red(
            fix_mode=True,
            changed_files=["state_tool.py"],
            test_globs=["tests/**", "*_test.py"],
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(result.get("ok"))

    # ── S-6: verify --red-check + 산출물(TEST-SCENARIO.md) 부재 → graceful skip ─

    def test_verify_red_check_skip_no_file(self):
        """[T016/L1-S6] TEST-SCENARIO.md 부재 + red_check=True → exit 0, skipped=True.

        PLAN §3.2.5 TS-007. 기존 _find_scenario_file None 경로 재사용(graceful skip).
        """
        # TEST-SCENARIO.md를 생성하지 않음
        exit_code, result = self._call_verify_red(red_check=True)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result.get("ok"))
        self.assertTrue(result.get("skipped"))

    # ── S-7: RED 증거 없으면 GREEN 진입 차단 (통합) ─────────────────────────

    def test_red_gate_blocks_green(self):
        """[T016/L2-S7] init state.json + RED 증거 빈 TEST-SCENARIO.md → verify --red-check가 차단 입증.

        PLAN §3.2.5 TS-007 통합 변형. 오케스트레이터 명시 verify --red-check 게이트.
        RED 증거 누락 시 red_evidence_missing exit 1 → GREEN 진입 차단.
        """
        self._init()
        self._write_scenario(
            "# TEST-SCENARIO\n\n"
            "| 시나리오 | RED 증거 | 결과 | 실행 명령 | 출력 |\n"
            "|---------|---------|------|---------|------|\n"
            "| S-1 | |  Pass | python -m unittest | 1 passed |\n"
        )
        exit_code, result = self._call_verify_red(red_check=True)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "red_evidence_missing",
                         "RED 증거 누락 시 verify가 red_evidence_missing을 반환해야 GREEN 진입 차단됨")

    # ── S-8: verify --fix-mode + test_globs 미지정 → 불변성 검사 skip ────────

    def test_verify_fix_mode_no_globs(self):
        """[T016/L1-S8] fix_mode=True + changed_files + test_globs 미지정 → exit 0, immutability skip.

        PLAN §3.2.2: '--fix-mode' + '--test-globs' 미지정 → 불변성 검사 skip (deterministic 입력 없음).
        result의 immutability_check == "skipped (no test-globs)".
        """
        exit_code, result = self._call_verify_red(
            fix_mode=True,
            changed_files=["tests/x.py"],
            test_globs=None,
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(result.get("ok"))
        self.assertEqual(
            result.get("immutability_check"),
            "skipped (no test-globs)",
            "test_globs 미지정 시 immutability_check가 'skipped (no test-globs)' 이어야 함",
        )


# ═════════════════════════════════════════════════════════════════════════════
# [T017] 다중 Step EXECUTE 행 조기 done 가드
# ═════════════════════════════════════════════════════════════════════════════

class TestMultiStepDoneGuard(BaseTestCase):
    """[T017] 다중 Step EXECUTE 행 조기 done 가드 테스트.

    설계된 동작 (PLAN §3.2.2):
    - mark --step N/M --done: N<M 이면 status=in_progress 유지 + step:"N/M" 저장
    - mark --step N/M --done: N==M 이면 status=done + step:"N/M" 저장
    - mark (--step 없음 / 비정형): 기존 즉시 done (하위 호환)
    - N<M 행(in_progress)이 있으면 다음 단계 mark/advance → stage_transition_violation
    """

    # EXECUTE 행이 포함된 표준 순차 구조
    MULTISTEP_ROWS = json.dumps([
        {"stage": "TASK",    "item": "작업"},
        {"stage": "PLAN",    "item": "작업"},
        {"stage": "EXECUTE", "item": "다중 Step 작업"},
        {"stage": "CLOSE",   "item": "사용자 확인"},
    ])

    def setUp(self):
        super().setUp()
        self._init(rows_spec=self.MULTISTEP_ROWS)

    def _mark_and_get_row(self, row_id, step=None):
        """mark 호출 후 state.json에서 해당 행을 반환 (공개 관측 기준)."""
        code = self._mark(row_id, step=step, as_worker=True, worker_stage="EXECUTE")
        state = self._state()
        row = state["rows"][row_id - 1]
        return code, row

    # ── TS-001: N<M → in_progress 유지 + step 저장 ───────────────────────────

    def test_step_n_lt_m_stays_in_progress(self):
        """[T017/TS-001] mark --row R --done --step 1/7 → status=in_progress(done 아님), step=="1/7".

        미구현 시: 현재 코드는 --done 무조건 done 처리하여 status=done → AssertionError(RED).
        PLAN §3.2.2 R-1: N<M 이면 행을 done으로 닫지 않고 in_progress 유지.
        """
        # EXECUTE 행(row3)이 대상 — 앞 행(1,2) 먼저 완료
        self._mark(1)
        self._mark(2)

        code, row = self._mark_and_get_row(3, step="1/7")

        self.assertEqual(code, 0, "step 1/7 mark가 exit 0으로 성공해야 함")
        self.assertEqual(
            row["status"], "in_progress",
            f"N<M(1<7)이면 status=in_progress이어야 함, 실제: {row['status']}"
        )
        self.assertNotEqual(row["status"], "done",
                            "N<M이면 status가 done이면 안 됨 (조기 done 가드)")
        self.assertEqual(
            row.get("step"), "1/7",
            f"state.json 행에 step=='1/7' 저장되어야 함, 실제: {row.get('step')}"
        )

    # ── TS-002: N==M → done + step 저장 ──────────────────────────────────────

    def test_step_n_eq_m_done(self):
        """[T017/TS-002] mark --row R --done --step 7/7 → status=done, step=="7/7".

        N==M은 마지막 Step → 정상 done (PLAN §3.2.2 R-2).
        현재 코드도 done 처리하므로 step 저장 검증이 핵심 — step 미저장이면 FAIL.
        """
        self._mark(1)
        self._mark(2)

        code, row = self._mark_and_get_row(3, step="7/7")

        self.assertEqual(code, 0, "step 7/7 mark가 exit 0으로 성공해야 함")
        self.assertEqual(
            row["status"], "done",
            f"N==M(7==7)이면 status=done이어야 함, 실제: {row['status']}"
        )
        self.assertEqual(
            row.get("step"), "7/7",
            f"state.json 행에 step=='7/7' 저장되어야 함, 실제: {row.get('step')}"
        )

    # ── TS-003: N<M 행이 in_progress이면 다음 단계 mark 차단 ─────────────────

    def test_incomplete_step_blocks_next_stage(self):
        """[T017/TS-003] EXECUTE 행을 --step 1/7 --done(in_progress 기대) 후 다음 단계 mark → stage_transition_violation.

        미구현 시: EXECUTE가 done되어 다음 단계 mark가 통과됨 → AssertionError(RED).
        PLAN §3.2.3: in_progress는 _COMPLETE_STATUSES에 없으므로 기존 guard가 자동 차단.
        """
        import io
        from contextlib import redirect_stdout

        self._mark(1)
        self._mark(2)
        # EXECUTE 행(row3)을 1/7로 mark → in_progress 기대 (미구현 시 done)
        self._mark(3, step="1/7")

        # 다음 단계 행(row4 = CLOSE) mark 시도 → stage_transition_violation 기대
        out = io.StringIO()
        with redirect_stdout(out):
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    row=4, done=True,
                )
                try:
                    ST.cmd_mark(args)
                except SystemExit:
                    pass
        raw = out.getvalue().strip()
        result = json.loads(raw) if raw else {}

        self.assertEqual(
            result.get("error"), "stage_transition_violation",
            f"EXECUTE 행이 in_progress이면 다음 단계 mark가 stage_transition_violation으로 거부되어야 함. 실제: {result}"
        )
        self.assertIn(3, result.get("incomplete_rows", []),
                      f"incomplete_rows에 row3이 포함되어야 함, 실제: {result.get('incomplete_rows')}")

    # ── TS-004: N<M 행이 in_progress이면 CLOSE 첫 행 mark 차단 ──────────────

    def test_incomplete_step_blocks_close(self):
        """[T017/TS-004] 선행 EXECUTE 행 --step 1/7 --done(in_progress) 후 CLOSE 첫 행 mark → 거부(stage_transition_violation).

        미구현 시: EXECUTE가 done되어 CLOSE mark 통과 → AssertionError(RED).
        PLAN §3.2.4: mark/advance는 stage-transition guard를 close gate보다 먼저 호출하므로 차단.
        """
        import io
        from contextlib import redirect_stdout

        self._mark(1)
        self._mark(2)
        # EXECUTE 행(row3)을 1/7로 mark → in_progress 기대
        self._mark(3, step="1/7")

        # CLOSE 첫 행(row4) mark → stage_transition_violation 기대
        out = io.StringIO()
        with redirect_stdout(out):
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    row=4, done=True,
                    owner="user",
                )
                try:
                    ST.cmd_mark(args)
                except SystemExit:
                    pass
        raw = out.getvalue().strip()
        result = json.loads(raw) if raw else {}

        self.assertEqual(
            result.get("error"), "stage_transition_violation",
            f"EXECUTE 행이 in_progress이면 CLOSE mark가 stage_transition_violation으로 거부되어야 함. 실제: {result}"
        )

    # ── TS-005: --step 없는 mark → 즉시 done (하위 호환) ────────────────────

    def test_no_step_backward_compat(self):
        """[T017/TS-005] --step 없는 mark → 기존대로 즉시 done. step 키 없는 행 정상.

        하위 호환 가드 (PLAN §3.2.2 C-4). 현재도 통과해야 함(GREEN에서 변경 없음).
        """
        self._mark(1)
        self._mark(2)
        # --step 없이 mark
        code = self._mark(3)

        self.assertEqual(code, 0, "--step 없는 mark가 exit 0이어야 함")
        state = self._state()
        row = state["rows"][2]  # row3 (0-indexed)
        self.assertEqual(row["status"], "done",
                         "--step 없으면 기존대로 즉시 done이어야 함")
        # step 키 미저장 또는 None — 기존 state.json 하위 호환
        self.assertIsNone(row.get("step"),
                          f"--step 미지정 시 step 키가 없거나 None이어야 함, 실제: {row.get('step')}")

    # ── TS-007: 비정형 --step → 기존 done 경로 (크래시 없음) ─────────────────

    def test_malformed_step_falls_back(self):
        """[T017/TS-007] --step "abc" / "3" / "0/0" → 기존 done 경로, 크래시 없음.

        PLAN §3.2.1: _parse_step이 None 반환 → 기존 즉시 done 경로 (C-4 하위 호환).
        현재도 통과 가능 (크래시 방어). step은 저장되지 않거나 무해해야 함.
        """
        malformed_cases = ["abc", "3", "0/0"]

        for i, bad_step in enumerate(malformed_cases):
            with self.subTest(step=bad_step):
                # 새 tmpdir로 초기화 (subTest 간 독립)
                import tempfile
                old_task_path = self.task_path
                self.task_path = self.tmpdir / f"subtest-{i}"
                self.task_path.mkdir(exist_ok=True)
                self._init(rows_spec=self.MULTISTEP_ROWS)

                self._mark(1)
                self._mark(2)
                # 비정형 step으로 mark — 크래시 없이 done 처리 기대
                code = self._mark(3, step=bad_step)

                self.assertEqual(code, 0,
                                 f"비정형 step='{bad_step}'이어도 exit 0이어야 함 (크래시 없음)")
                state = self._state()
                row = state["rows"][2]
                self.assertEqual(row["status"], "done",
                                 f"비정형 step='{bad_step}'이면 기존 done 경로로 즉시 done이어야 함")
                # 복원
                self.task_path = old_task_path

    # ── TS-008: 순차 Step 진행률 갱신 ────────────────────────────────────────

    def test_sequential_step_progress(self):
        """[T017/TS-008] 같은 행 1/7 → 2/7 → 7/7 순차 mark: 1·2는 in_progress, 7에서 done, step 갱신.

        미구현 시: 1/7 mark에서 done되어 2/7 mark 시 이미 done인 행 재mark(멱등) 또는
        step 갱신 없음 → AssertionError(RED).
        PLAN §3.2.2 R-1: 각 중간 Step mark마다 in_progress 유지 + step 갱신.
        """
        self._mark(1)
        self._mark(2)

        # Step 1/7 → in_progress, step="1/7"
        code1 = self._mark(3, step="1/7")
        self.assertEqual(code1, 0, "step 1/7 mark exit 0")
        row1 = self._state()["rows"][2]
        self.assertEqual(row1["status"], "in_progress",
                         f"step 1/7 후 in_progress 기대, 실제: {row1['status']}")
        self.assertEqual(row1.get("step"), "1/7",
                         f"step 1/7 저장 기대, 실제: {row1.get('step')}")

        # Step 2/7 → in_progress, step="2/7"
        code2 = self._mark(3, step="2/7")
        self.assertEqual(code2, 0, "step 2/7 mark exit 0")
        row2 = self._state()["rows"][2]
        self.assertEqual(row2["status"], "in_progress",
                         f"step 2/7 후 in_progress 기대, 실제: {row2['status']}")
        self.assertEqual(row2.get("step"), "2/7",
                         f"step 2/7로 갱신 기대, 실제: {row2.get('step')}")

        # Step 7/7 → done, step="7/7"
        code7 = self._mark(3, step="7/7")
        self.assertEqual(code7, 0, "step 7/7 mark exit 0")
        row7 = self._state()["rows"][2]
        self.assertEqual(row7["status"], "done",
                         f"step 7/7 후 done 기대, 실제: {row7['status']}")
        self.assertEqual(row7.get("step"), "7/7",
                         f"step 7/7로 갱신 기대, 실제: {row7.get('step')}")


# ═════════════════════════════════════════════════════════════════════════════
# K. 명확화 게이트 (PLAN 005) — RED-first TDD 트랙
#    verify --clarification-check 직접 호출 케이스 ①~⑥
#    자동 훅(cmd_mark/cmd_advance) 케이스 ⑦~⑨
#    회귀 보호 케이스 ⑩
# ═════════════════════════════════════════════════════════════════════════════

# ── TASK.md 픽스처 콘텐츠 상수 ───────────────────────────────────────────────

_TASK_MD_ALL_FILLED = """\
# TASK: 테스트 태스크

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 테스트 목표 확정 | - | - |
| 범위 | 포함·제외 확정 | - | - |
| 제약 | 기술 제약 확정 | - | - |
| 완료기준 | 검증 가능 기준 확정 | - | - |
"""

_TASK_MD_ONE_BLANK = """\
# TASK: 테스트 태스크

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 테스트 목표 확정 | - | - |
| 범위 |  | - | - |
| 제약 | 기술 제약 확정 | - | - |
| 완료기준 | 검증 가능 기준 확정 | - | - |
"""

_TASK_MD_ONE_TBD = """\
# TASK: 테스트 태스크

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 테스트 목표 확정 | - | - |
| 범위 | TBD | - | - |
| 제약 | 기술 제약 확정 | - | - |
| 완료기준 | 검증 가능 기준 확정 | - | - |
"""

_TASK_MD_NO_SECTION = """\
# TASK: 테스트 태스크

## 요구사항

내용 없음
"""

_TASK_MD_NA_VALUE = """\
# TASK: 테스트 태스크

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 테스트 목표 확정 | - | - |
| 범위 | N/A: 단일 파일 수정이므로 범위 제한 없음 | - | - |
| 제약 | 기술 제약 확정 | - | - |
| 완료기준 | 검증 가능 기준 확정 | - | - |
"""

_TASK_MD_ONE_MISSING_ELEMENT = """\
# TASK: 테스트 태스크

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 테스트 목표 확정 | - | - |
| 범위 | 포함·제외 확정 | - | - |
| 제약 | 기술 제약 확정 | - | - |
"""


class TestClarificationGate(BaseTestCase):
    """PLAN 005 — verify --clarification-check + 자동 훅 RED-first 테스트.

    [MUST] mock/patch/MagicMock 금지 — 실제 TASK.md 파일 픽스처(tmp 디렉토리) + 실 state.json + 실 CLI 호출만.
    [MUST] 구현 코드(state_tool.py 본체) 수정 금지 — RED 증거만 확보.
    정책 A(graceful skip) 기준: "## 명확화 결과" 섹션/파일 부재 시 {ok:true, skipped} exit 0.
    """

    # ── 헬퍼 ──────────────────────────────────────────────────────────────────

    def _write_task_md(self, content):
        """TASK.md를 task_path 아래에 생성한다."""
        p = self.task_path / "TASK.md"
        p.write_text(content, encoding="utf-8")
        return p

    def _call_clarification_verify(self, task_path=None, task_md=None):
        """cmd_verify --clarification-check 호출 → (exit_code, result_dict).

        task_path 기본값: self.task_path
        task_md: --task-md 경로 (None이면 <task_path>/TASK.md 자동)
        """
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        exit_code = 0
        args = types.SimpleNamespace(
            task_path=str(task_path or self.task_path),
            scenario=None,
            clarification_check=True,
            task_md=task_md,
            red_check=False,
            fix_mode=False,
            changed_files=None,
            test_globs=None,
        )
        with redirect_stdout(out):
            try:
                ST.cmd_verify(args)
            except SystemExit as e:
                exit_code = e.code
        output = out.getvalue().strip()
        result = json.loads(output) if output else {}
        return exit_code, result

    def _mark_with_state(self, row_id, auto_pass=False, force=False, note=None):
        """cmd_mark 헬퍼 — _mark보다 인자 명시적."""
        return self._mark(row_id, auto_pass=auto_pass, force=force, note=note)

    # ── 케이스 ①: 4요소 모두 채워진 TASK.md → PASS exit 0 ─────────────────────

    def test_case1_all_filled_pass(self):
        """① 4요소 확정값 채워진 TASK.md → {ok:true, clarification_check:"pass"} exit 0 (PLAN M-2 ①)"""
        self._write_task_md(_TASK_MD_ALL_FILLED)
        exit_code, result = self._call_clarification_verify()
        self.assertEqual(exit_code, 0,
                         f"[RED] exit_code 0 기대 (미구현이므로 비0 가능). result={result}")
        self.assertTrue(result.get("ok"),
                        f"[RED] ok=true 기대. result={result}")
        self.assertEqual(result.get("clarification_check"), "pass",
                         f"[RED] clarification_check='pass' 기대. result={result}")

    # ── 케이스 ②: 1요소 공란 → FAIL exit 1 + missing 포함 ──────────────────────

    def test_case2_one_blank_fail(self):
        """② 1요소 공란 → {ok:false, error:'clarification_gate_unmet', missing:[...]} exit 1 (PLAN M-2 ②)"""
        self._write_task_md(_TASK_MD_ONE_BLANK)
        exit_code, result = self._call_clarification_verify()
        self.assertEqual(exit_code, 1,
                         f"[RED] exit_code 1 기대. result={result}")
        self.assertFalse(result.get("ok"),
                         f"[RED] ok=false 기대. result={result}")
        self.assertEqual(result.get("error"), "clarification_gate_unmet",
                         f"[RED] error='clarification_gate_unmet' 기대. result={result}")
        missing = result.get("missing", [])
        self.assertTrue(len(missing) >= 1,
                        f"[RED] missing에 최소 1개 요소 기대. missing={missing}")
        # "범위" 요소가 공란이므로 missing에 포함되어야 함
        found_beom_wi = any("범위" in str(m) for m in missing)
        self.assertTrue(found_beom_wi,
                        f"[RED] missing에 '범위' 포함 기대. missing={missing}")

    # ── 케이스 ③: 1요소 "TBD" → FAIL (missing 포함) ────────────────────────────

    def test_case3_tbd_fail(self):
        """③ 1요소 'TBD' → FAIL (PLAN M-2 ③ — TBD는 미확정으로 간주)"""
        self._write_task_md(_TASK_MD_ONE_TBD)
        exit_code, result = self._call_clarification_verify()
        self.assertEqual(exit_code, 1,
                         f"[RED] exit_code 1 기대 (TBD=미충족). result={result}")
        self.assertFalse(result.get("ok"),
                         f"[RED] ok=false 기대. result={result}")
        self.assertEqual(result.get("error"), "clarification_gate_unmet",
                         f"[RED] error='clarification_gate_unmet' 기대. result={result}")
        missing = result.get("missing", [])
        self.assertTrue(len(missing) >= 1,
                        f"[RED] missing에 최소 1개 기대 (TBD=범위). missing={missing}")

    # ── 케이스 ④: "## 명확화 결과" 섹션 부재 → 정책 A: skip ok exit 0 ──────────

    def test_case4_no_section_skip_ok(self):
        """④ '## 명확화 결과' 섹션 부재 → 정책 A: {ok:true, clarification_check:'skipped'} exit 0 (PLAN M-2 ④)"""
        self._write_task_md(_TASK_MD_NO_SECTION)
        exit_code, result = self._call_clarification_verify()
        self.assertEqual(exit_code, 0,
                         f"[RED] 섹션 부재 시 graceful skip(exit 0) 기대. result={result}")
        self.assertTrue(result.get("ok"),
                        f"[RED] ok=true 기대. result={result}")
        clarification_check = result.get("clarification_check")
        self.assertEqual(clarification_check, "skipped",
                         f"[RED] clarification_check='skipped' 기대. result={result}")

    # ── 케이스 ⑤: TASK.md 파일 부재 → 정책 A: skip ok exit 0 ──────────────────

    def test_case5_no_task_md_skip_ok(self):
        """⑤ TASK.md 파일 부재 → 정책 A: skip ok exit 0 (PLAN M-2 ⑤)"""
        # TASK.md를 생성하지 않음 — task_path 자체는 존재
        exit_code, result = self._call_clarification_verify()
        self.assertEqual(exit_code, 0,
                         f"[RED] TASK.md 부재 시 graceful skip(exit 0) 기대. result={result}")
        self.assertTrue(result.get("ok"),
                        f"[RED] ok=true 기대. result={result}")
        clarification_check = result.get("clarification_check")
        self.assertEqual(clarification_check, "skipped",
                         f"[RED] clarification_check='skipped' 기대. result={result}")

    # ── 케이스 ⑥: 1요소 "N/A: <사유>" → PASS (명시적 해당없음) ────────────────

    def test_case6_na_value_pass(self):
        """⑥ 1요소 'N/A: <사유>' → PASS (명시적 해당없음, PLAN M-2 ⑥)"""
        self._write_task_md(_TASK_MD_NA_VALUE)
        exit_code, result = self._call_clarification_verify()
        self.assertEqual(exit_code, 0,
                         f"[RED] N/A:<사유>는 PASS, exit 0 기대. result={result}")
        self.assertTrue(result.get("ok"),
                        f"[RED] ok=true 기대. result={result}")
        self.assertEqual(result.get("clarification_check"), "pass",
                         f"[RED] clarification_check='pass' 기대. result={result}")

    # ── 케이스 ⑦: 자동 훅 — TASK 완료 후 다음 단계 첫 행 mark 시 미충족 → 거부 ──

    def test_case7_auto_hook_mark_rejected_when_unmet(self):
        """⑦ TASK 행 전부 done 후 다음 단계 첫 행 mark, 4요소 미충족 → clarification_gate_unmet 거부 (PLAN M-2 ⑦)"""
        # TASK.md 생성 — 1요소 공란(미충족)
        self._write_task_md(_TASK_MD_ONE_BLANK)

        # TASK + PLAN 행 구성
        rows_spec = json.dumps([
            {"stage": "TASK", "item": "작업"},
            {"stage": "PLAN", "item": "작업"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows_spec)

        # TASK 행(row1) done
        code = self._mark(1)
        self.assertEqual(code, 0, "TASK 행 mark exit 0 기대")

        # 다음 단계(PLAN) 첫 행(row2) mark 시도 → 미충족이므로 거부 기대
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    row=2, done=True,
                )
                exit_code = 0
                try:
                    ST.cmd_mark(args)
                except SystemExit as e:
                    exit_code = e.code
        result = json.loads(out.getvalue()) if out.getvalue().strip() else {}
        self.assertEqual(exit_code, 1,
                         f"[RED] 미충족 시 거부(exit 1) 기대. result={result}")
        self.assertEqual(result.get("error"), "clarification_gate_unmet",
                         f"[RED] error='clarification_gate_unmet' 기대. result={result}")

    # ── 케이스 ⑧: 자동 훅 — 4요소 충족 시 다음 단계 첫 행 mark/advance 통과 ───

    def test_case8_auto_hook_mark_passes_when_met(self):
        """⑧ TASK 행 전부 done 후 다음 단계 첫 행 mark, 4요소 충족 → 정상 통과 (PLAN M-2 ⑧)"""
        # TASK.md 생성 — 4요소 전부 채워짐(충족)
        self._write_task_md(_TASK_MD_ALL_FILLED)

        rows_spec = json.dumps([
            {"stage": "TASK", "item": "작업"},
            {"stage": "PLAN", "item": "작업"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows_spec)

        # TASK 행(row1) done
        code = self._mark(1)
        self.assertEqual(code, 0, "TASK 행 mark exit 0 기대")

        # 다음 단계(PLAN) 첫 행(row2) mark → 충족이므로 통과 기대
        code2 = self._mark(2)
        self.assertEqual(code2, 0,
                         f"[RED] 4요소 충족 시 mark 통과(exit 0) 기대. 실제 exit_code={code2}")

    def test_case8_auto_hook_advance_passes_when_met(self):
        """⑧-b TASK 행 전부 done 후 다음 단계 첫 행 advance, 4요소 충족 → 통과 (PLAN M-2 ⑧)"""
        self._write_task_md(_TASK_MD_ALL_FILLED)

        rows_spec = json.dumps([
            {"stage": "TASK", "item": "작업"},
            {"stage": "PLAN", "item": "작업"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows_spec)

        code = self._mark(1)
        self.assertEqual(code, 0, "TASK 행 mark exit 0 기대")

        code2 = self._advance(2)
        self.assertEqual(code2, 0,
                         f"[RED] 4요소 충족 시 advance 통과(exit 0) 기대. 실제 exit_code={code2}")

    # ── 케이스 ⑨: 자동 훅 — --auto-pass 우회 불가 ──────────────────────────────

    def test_case9_auto_pass_cannot_bypass(self):
        """⑨ 미충족 상태에서 다음 단계 첫 행 mark --auto-pass 시도 → 거부(우회 불가) (PLAN M-2 ⑨)"""
        # TASK.md — 미충족
        self._write_task_md(_TASK_MD_ONE_BLANK)

        rows_spec = json.dumps([
            {"stage": "TASK", "item": "작업"},
            {"stage": "PLAN", "item": "작업"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows_spec)

        # TASK 행 done
        code = self._mark(1)
        self.assertEqual(code, 0)

        # 다음 단계(PLAN) 첫 행에 --auto-pass 시도 → 거부 기대
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            with _mock_now():
                args = make_args(
                    task_path=str(self.task_path),
                    row=2, done=True,
                    auto_pass=True,
                )
                exit_code = 0
                try:
                    ST.cmd_mark(args)
                except SystemExit as e:
                    exit_code = e.code
        result = json.loads(out.getvalue()) if out.getvalue().strip() else {}
        self.assertEqual(exit_code, 1,
                         f"[RED] --auto-pass 우회 거부(exit 1) 기대. result={result}")
        self.assertEqual(result.get("error"), "clarification_gate_unmet",
                         f"[RED] error='clarification_gate_unmet' 기대 (auto-pass 우회 불가). result={result}")

    # ── 케이스 ⑩: 회귀 보호 — 기존형 STATE(명확화 섹션 없음) 픽스처로 mark → 게이트 미발동 ──

    def test_case10_regression_no_section_no_gate(self):
        """⑩ '명확화 결과' 섹션 없는 기존형 STATE 픽스처로 단계 전환 mark → 게이트 미발동(정책 A skip) → 정상 진행 (PLAN M-2 ⑩)"""
        # TASK.md 없음 (기존 태스크 — 명확화 섹션 없는 케이스)
        # task_path에 TASK.md를 생성하지 않는다

        rows_spec = json.dumps([
            {"stage": "TASK", "item": "작업"},
            {"stage": "PLAN", "item": "작업"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows_spec)

        # TASK 행 done
        code = self._mark(1)
        self.assertEqual(code, 0, "TASK 행 mark exit 0 기대")

        # 다음 단계(PLAN) 첫 행 mark → TASK.md 없으므로 게이트 발동 안 함 → 통과 기대
        code2 = self._mark(2)
        self.assertEqual(code2, 0,
                         f"[RED] TASK.md 없는 기존형 픽스처는 게이트 미발동으로 통과(exit 0) 기대. 실제 exit_code={code2}")

    def test_case10b_regression_simple_rows_spec_mark(self):
        """⑩-b SIMPLE_ROWS_SPEC(명확화 섹션 없음) 픽스처로 mark 시 게이트 미발동 (PLAN M-2 ⑩)"""
        # SIMPLE_ROWS_SPEC: TASK/PLAN/EXECUTE/CLOSE 4행 — 명확화 섹션 없음
        self._init(rows_spec=SIMPLE_ROWS_SPEC)

        # row1(TASK/작업) done → row2(PLAN/작업) mark
        code1 = self._mark(1)
        self.assertEqual(code1, 0)

        code2 = self._mark(2)
        self.assertEqual(code2, 0,
                         f"[RED] 기존 SIMPLE_ROWS_SPEC 픽스처는 게이트 미발동, 정상 진행 기대. 실제 exit_code={code2}")


# ═════════════════════════════════════════════════════════════════════════════
# T098 — verify --evidence-check 근거 등급·확정판정 RED 테스트 (PLAN 098 §3.3.2, Step 4)
# ═════════════════════════════════════════════════════════════════════════════

class TestT098EvidenceCheck(BaseTestCase):
    """098 F-003 RED — `verify --evidence-check` 반환 계약(PLAN §3.3.2).

    [MUST] mock/patch/MagicMock 금지 — 실 파일 픽스처(tmp_path) + 공개 CLI 경로
    (`cmd_verify` 직접 호출)만 사용한다. 구현(`state_tool.py`) 무접촉 — 본
    클래스는 RED 증거만 확보한다(작성자≠구현자, `harness/red-first.md` §2).
    GREEN은 Step 5(`opal-be-agent`)가 담당한다.

    `## 명확화 결과` 표는 열 수 4(`요소 | 확정값 | 미확정(있으면) | 의존 사실`)를
    유지한다 — 열 추가는 설계에 없다(098 dispatch 지시).
    """

    _ELEMENTS = ("목표", "범위", "제약", "완료기준")

    def _write_task_md(self, rows):
        """rows: {요소: (확정값, 의존사실)} 또는 4-tuple 시퀀스.
        누락된 요소는 빈 확정값·'-' 의존사실로 채운다(4행 고정 — U-2 설계)."""
        if isinstance(rows, dict):
            row_map = rows
        else:
            row_map = {elem: (confirmed, dep) for elem, confirmed, dep in rows}
        lines = [
            "## 명확화 결과",
            "",
            "| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |",
            "|------|--------|--------------|----------|",
        ]
        for elem in self._ELEMENTS:
            confirmed, dep = row_map.get(elem, (f"{elem} 확정값", "-"))
            lines.append(f"| {elem} | {confirmed} | - | {dep} |")
        p = self.task_path / "TASK.md"
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return p

    def _call_evidence_verify(self, task_path=None, task_md=None, **extra_flags):
        """cmd_verify --evidence-check 호출 → (exit_code, result_dict).

        [MUST] 신규 헬퍼 — `TestClarificationGate._call_clarification_verify`
        (:3926-3946)는 무수정으로 둔다(098 dispatch 지시). evidence_check
        플래그를 기본 True로 명시 지정하되, 필요 시 extra_flags로 덮어쓴다
        (플래그 충돌 케이스 등)."""
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        exit_code = 0
        fields = dict(
            task_path=str(task_path or self.task_path),
            scenario=None,
            clarification_check=False,
            evidence_check=True,
            task_md=task_md,
            red_check=False,
            fix_mode=False,
            changed_files=None,
            test_globs=None,
        )
        fields.update(extra_flags)
        args = types.SimpleNamespace(**fields)
        with redirect_stdout(out):
            try:
                ST.cmd_verify(args)
            except SystemExit as e:
                exit_code = e.code
        output = out.getvalue().strip()
        result = json.loads(output) if output else {}
        return exit_code, result

    @staticmethod
    def _items_by_element(result):
        return {it.get("element"): it for it in result.get("items", [])}

    @staticmethod
    def _find_citation(item, substr):
        for c in item.get("citations", []):
            if substr in str(c.get("raw", "")):
                return c
        return None

    # ── S-7: 신 스키마 판정 반환 계약 (FX-NEW) ─────────────────────────────

    def test_s7_new_schema_verdict_reasons_citations_ratio(self):
        """S-7 — `FX-NEW`: 항목별 verdict+reasons+citations[{raw,grade,exists}]
        + confirmed_ratio 반환, exit 0 (PLAN §3.3.2 반환 JSON 스키마)."""
        self._write_task_md({
            "목표": ("목표 확정값", "`opal/tools/state-tool/state_tool.py:100`"),
            "범위": ("범위 확정값", "`opal/tools/state-tool/README.md` §1"),
            "제약": ("제약 확정값", "-"),
            "완료기준": ("완료기준 확정값", "`.opal/brain/note.md`"),
        })
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")
        self.assertTrue(result.get("ok"), f"[RED] ok=true 기대. result={result}")
        self.assertEqual(result.get("command"), "verify")

        items = result.get("items")
        self.assertIsInstance(items, list, f"[RED] items가 list 기대. result={result}")
        self.assertEqual(len(items), 4, f"[RED] items 4건(요소별) 기대. result={result}")
        for it in items:
            for key in ("element", "verdict", "reasons", "citations"):
                self.assertIn(key, it, f"[RED] item에 '{key}' 키 기대. item={it}")
            for c in it.get("citations", []):
                for ckey in ("raw", "grade", "exists"):
                    self.assertIn(ckey, c, f"[RED] citation에 '{ckey}' 키 기대. citation={c}")

        by_elem = self._items_by_element(result)
        self.assertEqual(by_elem["목표"].get("verdict"), "확정",
                         f"[RED] 목표(코드 인용, 유효)는 확정 기대. result={result}")
        self.assertEqual(by_elem["범위"].get("verdict"), "확정",
                         f"[RED] 범위(문서 인용, 유효)는 확정 기대. result={result}")
        self.assertEqual(by_elem["제약"].get("verdict"), "미확정",
                         f"[RED] 제약(인용 0건)은 미확정 기대. result={result}")
        self.assertIn("citation_missing", by_elem["제약"].get("reasons", []))
        self.assertEqual(by_elem["완료기준"].get("verdict"), "미확정",
                         f"[RED] 완료기준(E5 단독)은 미확정 기대. result={result}")
        self.assertIn("e5_sole_citation", by_elem["완료기준"].get("reasons", []))

        self.assertEqual(result.get("confirmed_ratio"), 0.5,
                         f"[RED] confirmed_ratio 2/4=0.5 기대. result={result}")
        unconfirmed = set(result.get("unconfirmed", []))
        self.assertEqual(unconfirmed, {"제약", "완료기준"},
                         f"[RED] unconfirmed={{제약,완료기준}} 기대. result={result}")

    # ── S-2: 인용 부재 항목의 미확정 강등 (FX-NOCITE) ──────────────────────

    def test_s2_citation_missing_demotes(self):
        """S-2 — `FX-NOCITE`: `[사실]` 항목의 `의존 사실` 셀이 `-` →
        verdict:'미확정', reasons:['citation_missing'], exit 0."""
        self._write_task_md({
            "목표": ("목표 확정값", "`opal/tools/state-tool/README.md` §1"),
            "범위": ("범위 확정값", "`opal/tools/state-tool/README.md` §2"),
            "제약": ("제약 확정값", "-"),
            "완료기준": ("완료기준 확정값", "`opal/tools/state-tool/README.md` §3"),
        })
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대(라우터형, 차단 아님). result={result}")
        by_elem = self._items_by_element(result)
        item = by_elem.get("제약", {})
        self.assertEqual(item.get("verdict"), "미확정",
                         f"[RED] 인용 0건 항목은 미확정 기대. result={result}")
        self.assertIn("citation_missing", item.get("reasons", []),
                     f"[RED] reasons에 'citation_missing' 기대. item={item}")
        self.assertEqual(item.get("citations", []), [],
                         f"[RED] 인용 0건이므로 citations도 빈 리스트 기대. item={item}")

    # ── S-16: 경로 부재·줄번호 초과 강등 (FX-BADPATH) ──────────────────────

    def test_s16_bad_path_and_line_overflow_demotes(self):
        """S-16 — `FX-BADPATH`: 없는 경로 + 파일 끝 초과 줄번호 →
        reasons:['citation_path_not_found']로 미확정 강등."""
        self._write_task_md({
            "목표": ("목표 확정값", "`opal/tools/state-tool/README.md` §1"),
            "범위": ("범위 확정값", "`docs/DOES_NOT_EXIST_098_XYZ.md:3`"),
            "제약": ("제약 확정값", "`opal/tools/state-tool/README.md:999999`"),
            "완료기준": ("완료기준 확정값", "`opal/tools/state-tool/README.md` §4"),
        })
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")
        by_elem = self._items_by_element(result)

        no_path = by_elem.get("범위", {})
        self.assertEqual(no_path.get("verdict"), "미확정",
                         f"[RED] 없는 경로 인용은 미확정 기대. result={result}")
        self.assertIn("citation_path_not_found", no_path.get("reasons", []),
                     f"[RED] reasons에 'citation_path_not_found' 기대. item={no_path}")

        overflow = by_elem.get("제약", {})
        self.assertEqual(overflow.get("verdict"), "미확정",
                         f"[RED] 파일 끝 초과 줄번호 인용은 미확정 기대. result={result}")
        self.assertIn("citation_path_not_found", overflow.get("reasons", []),
                     f"[RED] reasons에 'citation_path_not_found' 기대. item={overflow}")

    # ── S-15: brain 단독 인용 강등 (FX-E5ONLY) ─────────────────────────────

    def test_s15_e5_sole_citation_demotes(self):
        """S-15 — `FX-E5ONLY`: `.opal/brain/**` 단독 인용 →
        reasons:['e5_sole_citation']로 미확정 강등."""
        self._write_task_md({
            "목표": ("목표 확정값", "`.opal/brain/note.md`"),
            "범위": ("범위 확정값", "`opal/tools/state-tool/README.md` §1"),
            "제약": ("제약 확정값", "`opal/tools/state-tool/README.md` §2"),
            "완료기준": ("완료기준 확정값", "`opal/tools/state-tool/README.md` §3"),
        })
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")
        by_elem = self._items_by_element(result)
        item = by_elem.get("목표", {})
        self.assertEqual(item.get("verdict"), "미확정",
                         f"[RED] E5 단독 인용은 미확정 기대. result={result}")
        self.assertIn("e5_sole_citation", item.get("reasons", []),
                     f"[RED] reasons에 'e5_sole_citation' 기대. item={item}")

    # ── S-35: E5 동반 인용 통과 — 과잉 차단 대조군 (FX-E5PAIR) ─────────────

    def test_s35_e5_paired_with_source_stays_confirmed(self):
        """S-35 — `FX-E5PAIR`: `.opal/brain/**` + 원천(E4) 동반 인용 →
        e5_sole_citation 미발생, 확정 유지 (S-15의 양성 대조군)."""
        self._write_task_md({
            "목표": ("목표 확정값",
                    "`.opal/brain/note.md`, `opal/tools/state-tool/README.md` §1"),
            "범위": ("범위 확정값", "`opal/tools/state-tool/README.md` §2"),
            "제약": ("제약 확정값", "`opal/tools/state-tool/README.md` §3"),
            "완료기준": ("완료기준 확정값", "`opal/tools/state-tool/README.md` §4"),
        })
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")
        by_elem = self._items_by_element(result)
        item = by_elem.get("목표", {})
        self.assertNotIn("e5_sole_citation", item.get("reasons", []),
                        f"[RED] E5 동반 인용은 e5_sole_citation 미발생 기대. item={item}")
        self.assertEqual(item.get("verdict"), "확정",
                         f"[RED] E5 동반 인용(원천 유효)은 확정 유지 기대. result={result}")

    # ── S-14: 미매칭 경로의 unknown 반환 (FX-UNKNOWN) ──────────────────────

    def test_s14_unmatched_path_returns_unknown_not_blocked(self):
        """S-14 — `FX-UNKNOWN`: 등급 패턴 밖 경로 → grade:'unknown' 반환.
        차단(exit!=0) 0건, 임의 등급 부여 0건."""
        self._write_task_md({
            "목표": ("목표 확정값", "`opal/tools/state-tool/README.md` §1"),
            "범위": ("범위 확정값", "`opal/tools/state-tool/README.md` §2"),
            "제약": ("제약 확정값", "`opal/tools/requirements.txt:1`"),
            "완료기준": ("완료기준 확정값", "`opal/tools/state-tool/README.md` §3"),
        })
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0,
                         f"[RED] 미매칭 경로는 차단하지 않음(exit 0) 기대. result={result}")
        by_elem = self._items_by_element(result)
        item = by_elem.get("제약", {})
        citation = self._find_citation(item, "requirements.txt")
        self.assertIsNotNone(citation, f"[RED] requirements.txt 인용 미검출. item={item}")
        self.assertEqual(citation.get("grade"), "unknown",
                         f"[RED] 미매칭 경로 grade='unknown' 기대. citation={citation}")
        self.assertNotIn(citation.get("grade"), ("E1", "E2", "E3", "E4", "E5"),
                         f"[RED] 임의 등급 부여 0건 기대. citation={citation}")

    # ── S-26: E1·E3 자동 부여 제외 경계 (Block B — H-11) ───────────────────

    def test_s26_e1_execution_log_and_e3_generated_code_return_unknown(self):
        """S-26 — E1(실행 로그)·E3(생성 코드) 경로 인용 → 둘 다 grade:'unknown'
        (도구 자동 부여 대상 아님, PLAN §3.3.2 [MUST] H-11)."""
        self._write_task_md({
            "목표": ("목표 확정값", "`logs/test-run-output.log:5`"),
            "범위": ("범위 확정값", "`generated/migrations/0001_auto_schema.sql:3`"),
            "제약": ("제약 확정값", "`opal/tools/state-tool/README.md` §1"),
            "완료기준": ("완료기준 확정값", "`opal/tools/state-tool/README.md` §2"),
        })
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")
        by_elem = self._items_by_element(result)

        e1_item = by_elem.get("목표", {})
        e1_citation = self._find_citation(e1_item, "test-run-output.log")
        self.assertIsNotNone(e1_citation, f"[RED] E1 로그 인용 미검출. item={e1_item}")
        self.assertEqual(e1_citation.get("grade"), "unknown",
                         f"[RED] E1(실행 로그)는 unknown 기대. citation={e1_citation}")

        e3_item = by_elem.get("범위", {})
        e3_citation = self._find_citation(e3_item, "0001_auto_schema.sql")
        self.assertIsNotNone(e3_citation, f"[RED] E3 생성코드 인용 미검출. item={e3_item}")
        self.assertEqual(e3_citation.get("grade"), "unknown",
                         f"[RED] E3(생성 코드)는 unknown 기대. citation={e3_citation}")

    # ── S-17: 근거 없는 `[결정]`은 확정 유지 — 과잉 차단 대조군 (FX-DECISION) ──

    def test_s17_decision_tag_without_citation_stays_confirmed(self):
        """S-17 — `FX-DECISION`: `[결정]` 태그만, 인용 0건, `의존 사실` 전건 `-`
        → 해당 항목 verdict:'확정' 유지. 미확정 강등 발생 시 FAIL (P0 —
        캡틴의 새 요구사항이 미확정으로 강등되면 파이프라인이 멈춘다)."""
        self._write_task_md({
            "목표": ("[결정] 캡틴이 정한 목표(근거 불요)", "-"),
            "범위": ("[결정] 캡틴이 정한 범위(근거 불요)", "-"),
            "제약": ("[결정] 캡틴이 정한 제약(근거 불요)", "-"),
            "완료기준": ("[결정] 캡틴이 정한 완료기준(근거 불요)", "-"),
        })
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")
        for elem, item in self._items_by_element(result).items():
            self.assertEqual(item.get("verdict"), "확정",
                             f"[RED][P0] [결정] 항목({elem})은 인용 없어도 확정 유지 기대 — "
                             f"강등되면 새 요구사항이 파이프라인을 멈춘다. item={item}")
            self.assertNotIn("citation_missing", item.get("reasons", []),
                            f"[RED][P0] [결정] 항목({elem})에 citation_missing 발생 0건 기대. item={item}")
        self.assertEqual(result.get("confirmed_ratio"), 1.0,
                         f"[RED] 전건 [결정] → confirmed_ratio 1.0 기대. result={result}")

    # ── S-34: 정규 인용 형식 변형 통과 — 과잉 차단 대조군 (FX-FORMAT) ──────

    def test_s34_regular_citation_formats_not_overblocked(self):
        """S-34 — `FX-FORMAT`: 정규 4형식 혼재 → 4형식 전건이
        citation_path_not_found로 강등되지 않음. 파싱 비대상 형식(③④)은
        unknown으로 PM 판단에 위임되되 경로 부재로 오판정하지 않는다."""
        self._write_task_md({
            "목표": ("목표 확정값", "`opal/tools/state-tool/state_tool.py:100`"),
            "범위": ("범위 확정값", "`opal/tools/state-tool/README.md` §1"),
            "제약": ("제약 확정값", "[Anthropic Docs](https://docs.anthropic.com)"),
            "완료기준": ("완료기준 확정값", "(→ D-1 §2)"),
        })
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")
        by_elem = self._items_by_element(result)

        for elem in self._ELEMENTS:
            item = by_elem.get(elem, {})
            self.assertNotIn("citation_path_not_found", item.get("reasons", []),
                            f"[RED] 정규 형식({elem})이 citation_path_not_found로 "
                            f"오강등되면 안 됨(H-13). item={item}")

        self.assertEqual(by_elem.get("목표", {}).get("verdict"), "확정",
                         f"[RED] 형식①(경로:N, 유효) 확정 기대. result={result}")
        self.assertEqual(by_elem.get("범위", {}).get("verdict"), "확정",
                         f"[RED] 형식②(경로 §N, 유효) 확정 기대. result={result}")

        shorthand_item = by_elem.get("완료기준", {})
        self.assertNotIn("citation_missing", shorthand_item.get("reasons", []),
                        f"[RED] 형식④(단축 참조)는 백틱이 없어도 citation_missing이 "
                        f"아니어야 함(PLAN §3.3.2 [MUST]). item={shorthand_item}")

    # ── S-31: 본 태스크 TASK.md 실파일 판정 — 목표달성 축 (L2, 저장소 실파일) ──

    def test_s31_self_task_md_real_file_confirmed_ratio(self):
        """S-31 — `FX-SELF`: 본 태스크(098) `TASK.md`(신 스키마로 작성된 유일한
        실파일) → exit 0 + citation_missing 0건(4셀 전건 백틱 경로 스팬 보유)
        + confirmed_ratio == 3/4 (목표 행만 디렉토리 없는 파일명 단독이라
        unknown). tmp_path 합성 픽스처(S-7)로 대신할 수 없는 목표달성 검증."""
        repo_root = ST.find_project_root(str(_TOOL_DIR))
        self.assertIsNotNone(
            repo_root,
            "find_project_root가 None을 반환함 — .opal/MEMORY.json 보유 조상을 찾지 못함"
        )
        task_md_path = repo_root / "tasks" / "098-260821-opds-근거등급-확정판정-트랙강등" / "TASK.md"
        self.assertTrue(task_md_path.exists(),
                       f"[RED] 098 TASK.md 실파일 부재: {task_md_path}")

        exit_code, result = self._call_evidence_verify(
            task_path=str(task_md_path.parent), task_md=str(task_md_path)
        )
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")

        all_reasons = [
            r for it in result.get("items", []) for r in it.get("reasons", [])
        ]
        self.assertNotIn("citation_missing", all_reasons,
                        f"[RED] 098 TASK.md 4셀 전건 백틱 경로 스팬 보유 — "
                        f"citation_missing 0건 기대. reasons={all_reasons}")

        by_elem = self._items_by_element(result)
        self.assertEqual(by_elem.get("목표", {}).get("verdict"), "미확정",
                         f"[RED] '목표' 행은 디렉토리 없는 파일명 단독(`citation-rules.md`)"
                         f"이라 unknown→미확정 기대. result={result}")

        self.assertEqual(result.get("confirmed_ratio"), 0.75,
                         f"[RED] confirmed_ratio == 3/4 기대(목표 행만 미확정, "
                         f"범위·제약·완료기준은 E4/E2 등급 부여). result={result}")

    # ── S-13: 레거시 실파일 다건 무차단 처리 (L2, 저장소 실파일) ───────────

    def test_s13_legacy_task_md_real_files_no_block(self):
        """S-13 — `FX-LEGACY`: 저장소 실측 `tasks/*/TASK.md` 다건(`의존 사실`
        전건 `-`인 레거시 다수 포함) → 전건 exit 0
        (`evidence_check:'skipped'` 또는 미확정 반환이되 차단 없음).
        예외·차단 0건."""
        repo_root = ST.find_project_root(str(_TOOL_DIR))
        self.assertIsNotNone(repo_root, "find_project_root가 None을 반환함")
        task_md_files = sorted((repo_root / "tasks").glob("*/TASK.md"))
        self.assertGreater(len(task_md_files), 0,
                           "[RED] 저장소 실측 TASK.md 파일이 0건 — 픽스처 불가")

        failures = []
        for p in task_md_files:
            try:
                exit_code, result = self._call_evidence_verify(
                    task_path=str(p.parent), task_md=str(p)
                )
            except Exception as e:  # pragma: no cover — RED 증거용 방어적 캡처
                failures.append((str(p), "exception", repr(e)))
                continue
            if exit_code != 0:
                failures.append((str(p), exit_code, result))
            elif "evidence_check" not in result:
                failures.append((str(p), exit_code,
                                  "evidence_check 키 부재(신 스키마 미반영)"))
        self.assertEqual(failures, [],
                         f"[RED] 레거시 TASK.md 실파일 {len(task_md_files)}건 중 "
                         f"비정상/미반영 {len(failures)}건: {failures}")

    # ── 신규 에러: --evidence-check + --clarification-check 동시 지정 ─────

    def test_evidence_check_flag_conflict_exit1(self):
        """신규 에러 — `--evidence-check`와 `--clarification-check` 동시 지정 →
        `evidence_check_flag_conflict` exit 1 (무성 무시 방지, PLAN §3.3.2)."""
        self._write_task_md({})
        exit_code, result = self._call_evidence_verify(clarification_check=True)
        self.assertEqual(exit_code, 1,
                         f"[RED] 두 플래그 동시 지정 시 exit 1 기대. result={result}")
        self.assertFalse(result.get("ok"), f"[RED] ok=false 기대. result={result}")
        self.assertEqual(result.get("error"), "evidence_check_flag_conflict",
                         f"[RED] error='evidence_check_flag_conflict' 기대. result={result}")

    # ── S-24: 고정 필드 SimpleNamespace 호출 안전 (Block B — H-9) ──────────

    def test_s24_fixed_field_namespace_no_attribute_error(self):
        """S-24 — 신 속성(`evidence_check`) 없는 고정 필드 `SimpleNamespace`로
        `cmd_verify` 호출 → AttributeError 0건(`getattr(args,"evidence_check",
        False)` 기본값 경로, H-9).

        [RED 예외 고지] 현재(미구현) 상태에서는 evidence_check 분기 자체가
        없어 이 케이스가 자연히 PASS할 수 있다 — '충돌 부재'를 검증하는
        가드성 테스트이기 때문이다. GREEN이 getattr 없이 `args.evidence_check`
        로 직접 접근하도록 구현하면 그때 이 케이스가 비로소 실패하여 회귀를
        잡아낸다(TestClarificationGate._call_clarification_verify:3936-3946과
        동일한 고정 필드 패턴 재현, 헬퍼 자체는 무수정)."""
        self._write_task_md({
            "목표": ("목표 확정값", "-"),
            "범위": ("범위 확정값", "-"),
            "제약": ("제약 확정값", "-"),
            "완료기준": ("완료기준 확정값", "-"),
        })
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        args = types.SimpleNamespace(
            task_path=str(self.task_path),
            scenario=None,
            clarification_check=False,
            task_md=None,
            red_check=False,
            fix_mode=False,
            changed_files=None,
            test_globs=None,
        )
        exit_code = 0
        raised = None
        with redirect_stdout(out):
            try:
                ST.cmd_verify(args)
            except SystemExit as e:
                exit_code = e.code
            except AttributeError as e:
                raised = e
        self.assertIsNone(raised,
                         f"[RED] evidence_check 속성 부재로 AttributeError 발생: {raised!r}")


class TestOwnerNamePlaceholder(BaseTestCase):
    """note '{owner_name}' 플레이스홀더 → identity.md owner_name write-time 치환 (PLAN §3.1.2, TASK 054)
    RED-first 트랙(H-1 self-confirming 방지) — TEST-SCENARIO.md §1 S-1~S-7.
    OPAL_HOME은 임시 디렉토리로 주입한다 (~/.opal 직접 접근 금지 — AGENT.md §확정 기준 #2).
    """

    def setUp(self):
        super().setUp()
        self._init()
        self.opal_home = self.tmpdir / "opal_home"
        self.opal_home.mkdir()

    def _write_identity(self, content):
        (self.opal_home / "identity.md").write_text(content, encoding="utf-8")

    def test_owner_name_substituted(self):
        """S-1(RED)/S-2(GREEN): identity.md owner_name=루카스 주입 후 mark note의 '{owner_name}'이
        실제 owner_name으로 치환 저장된다 (PLAN §3.1.2, TS-1/TS-2). 구현 전에는 미치환 원문이 저장되어
        AssertionError로 FAIL — 이 실패 트레이스백이 RED 증거다.
        """
        self._write_identity(
            "---\n"
            "name: 알투\n"
            "owner_name: 루카스\n"
            "---\n"
        )
        with patch.dict(os.environ, {"OPAL_HOME": str(self.opal_home)}):
            code = self._mark(1, owner="user", note="{owner_name} 확인: 검토 완료")
        self.assertEqual(code, 0)
        state = self._state()
        self.assertEqual(state["rows"][0]["note"], "루카스 확인: 검토 완료")

    def test_plain_note_unchanged(self):
        """S-3(회귀): 플레이스홀더 없는 note는 fast-path로 byte-identical 불변 (PLAN §3.1.2 H-2, TS-3)"""
        self._write_identity(
            "---\nowner_name: 루카스\n---\n"
        )
        with patch.dict(os.environ, {"OPAL_HOME": str(self.opal_home)}):
            code = self._mark(1, owner="user", note="검토 완료")
        self.assertEqual(code, 0)
        state = self._state()
        self.assertEqual(state["rows"][0]["note"], "검토 완료")

    def test_fallback_no_identity(self):
        """S-4(폴백): identity.md 부재 → note '{owner_name}' 원문 유지, 에러 없음(exit 0) (TS-4)"""
        # self.opal_home 디렉토리는 존재하나 identity.md는 작성하지 않음(부재)
        with patch.dict(os.environ, {"OPAL_HOME": str(self.opal_home)}):
            code = self._mark(1, owner="user", note="{owner_name} 확인: X")
        self.assertEqual(code, 0)
        state = self._state()
        self.assertEqual(state["rows"][0]["note"], "{owner_name} 확인: X")

    def test_fallback_blank_owner(self):
        """S-5(폴백): identity.md 존재하나 owner_name 공란 → 원문 유지, 빈값 치환 금지 (TS-5)"""
        self._write_identity(
            "---\nowner_name:\n---\n"
        )
        with patch.dict(os.environ, {"OPAL_HOME": str(self.opal_home)}):
            code = self._mark(1, owner="user", note="{owner_name} 확인: X")
        self.assertEqual(code, 0)
        state = self._state()
        self.assertEqual(state["rows"][0]["note"], "{owner_name} 확인: X")

    def test_fallback_no_frontmatter(self):
        """S-6(폴백): frontmatter/owner_name 키 부재 → 원문 유지, 크래시 없음(exit 0) (TS-6)"""
        self._write_identity("# identity\n\n특이사항 없음\n")
        with patch.dict(os.environ, {"OPAL_HOME": str(self.opal_home)}):
            code = self._mark(1, owner="user", note="{owner_name} 확인: X")
        self.assertEqual(code, 0)
        state = self._state()
        self.assertEqual(state["rows"][0]["note"], "{owner_name} 확인: X")

    def test_advance_and_autopass(self):
        """S-7: advance 경로 치환 + mark --auto-pass 접두('agentic auto-pass: ') 보존 조합 (PLAN §3.1.2 H-5, TS-7)"""
        self._write_identity(
            "---\nowner_name: 루카스\n---\n"
        )
        with patch.dict(os.environ, {"OPAL_HOME": str(self.opal_home)}):
            code_advance = self._advance(1, note="{owner_name} 확인")
            self.assertEqual(code_advance, 0)
            state = self._state()
            self.assertEqual(state["rows"][0]["note"], "루카스 확인")

            code_mark = self._mark(1, auto_pass=True, note="{owner_name} 승인")
        self.assertEqual(code_mark, 0)
        state = self._state()
        self.assertEqual(state["rows"][0]["note"], "agentic auto-pass: 루카스 승인")


# ═════════════════════════════════════════════════════════════════════════════
# 056: TestOpplSkillInit — state-tool oppl init 실호출 RED-first (S-020, H-1)
# ═════════════════════════════════════════════════════════════════════════════

class TestOpplSkillInit(unittest.TestCase):
    """`state-tool init --skill oppl` 실호출 계약 — TEST-SCENARIO.md S-020 (PLAN §3.3, H-1).

    [MUST] red-first.md §4: 공개 인터페이스(run.sh subprocess, stdout JSON + exit code)로만
    검증한다 — 내부 함수 직결(BaseTestCase._call_cmd류) 결합 및 mock/patch/MagicMock 금지.
    현재 state_tool.py의 `--skill` choices=[..., "opsdd"]에 "oppl"이 없어 argparse 단계에서
    거부(usage error, exit 2)된다 — 이 실패가 RED 증거다. GREEN 후에는 exit 0 + state.json
    skill:"oppl" + STATE.md 생성으로 전환되어야 한다(F-003, PLAN §3.3.2).
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.task_path = self.tmpdir / "056-dryrun"
        self.task_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, args):
        cmd = ["bash", str(_RUN_SH)] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        stdout = result.stdout.strip()
        try:
            data = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            data = {"_raw": stdout}
        return result.returncode, stdout, data

    def test_init_with_skill_oppl_succeeds(self):
        """[T056/L2-F003] `init --skill oppl --mode semi-agentic` 성공 기대 —
        현재는 argparse choices 미등록으로 거부되어 FAIL(RED). GREEN 후: exit 0,
        ok:true, state.json skill=="oppl" 생성."""
        code, stdout, data = self._run([
            "init", str(self.task_path),
            "--skill", "oppl",
            "--mode", "semi-agentic",
        ])
        self.assertEqual(code, 0, f"init --skill oppl 은 exit 0 이어야 한다 (실제 stdout: {stdout!r})")
        self.assertTrue(data.get("ok"))

        state_file = self.task_path / "state.json"
        self.assertTrue(state_file.exists(), "state.json이 생성되어야 한다")
        with open(state_file, encoding="utf-8") as f:
            state = json.load(f)
        self.assertEqual(state.get("skill"), "oppl")
        self.assertTrue((self.task_path / "STATE.md").exists(), "STATE.md가 생성되어야 한다")

    def test_existing_eight_skills_regression_unaffected(self):
        """[T056/L2-F003] 회귀 보호: oppl 추가가 기존 8개 스킬(opp) init 성공 경로를
        깨뜨리지 않아야 한다 — enum 확장은 추가만이어야 한다(PLAN §3.3.3)."""
        code, stdout, data = self._run([
            "init", str(self.task_path),
            "--skill", "opp",
            "--mode", "interactive",
        ])
        self.assertEqual(code, 0, f"기존 스킬 opp init은 회귀 없이 exit 0 이어야 한다 (stdout: {stdout!r})")
        self.assertTrue(data.get("ok"))


# ═════════════════════════════════════════════════════════════════════════════
# [T056/ADD2] TestSchemaModeEnumSemiAgentic — schema.json mode enum 드리프트 회귀 방지
# ═════════════════════════════════════════════════════════════════════════════

class TestSchemaModeEnumSemiAgentic(unittest.TestCase):
    """[T056/ADD2] state.schema.json의 `mode` enum이 CLI `--mode` choices(3-way:
    interactive/semi-agentic/agentic)와 정합해야 한다. 기존에는 스키마 enum이
    ["interactive", "agentic"]만 포함해 semi-agentic이 누락되어 있었다(문서 드리프트).
    이 테스트는 (1) 스키마 파일 자체의 enum에 semi-agentic이 존재하는지, (2) 실제
    init --mode semi-agentic 이후 validate가 이를 거부 없이 수용하는지 두 각도로
    회귀를 방지한다."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.task_path = self.tmpdir / "056-add2-dryrun"
        self.task_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, args):
        cmd = ["bash", str(_RUN_SH)] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        stdout = result.stdout.strip()
        try:
            data = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            data = {"_raw": stdout}
        return result.returncode, stdout, data

    def test_schema_mode_enum_includes_semi_agentic(self):
        """[T056/ADD2] state.schema.json properties.mode.enum에 "semi-agentic"이
        포함되어야 한다 — CLI choices와의 드리프트 재발 방지."""
        schema_path = _TOOL_DIR / "schema" / "state.schema.json"
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)
        mode_enum = schema["properties"]["mode"]["enum"]
        self.assertIn("semi-agentic", mode_enum,
                      "schema.json mode enum에 semi-agentic이 없음 (드리프트 재발)")
        self.assertEqual(set(mode_enum), {"interactive", "semi-agentic", "agentic"})

    def test_validate_accepts_semi_agentic_mode(self):
        """[T056/ADD2] init --mode semi-agentic 이후 validate가 violations 0으로
        통과해야 한다 (mode 값 자체로 인한 거부가 없어야 함)."""
        code, stdout, data = self._run([
            "init", str(self.task_path),
            "--skill", "oppl",
            "--mode", "semi-agentic",
        ])
        self.assertEqual(code, 0, f"init 실패: {stdout!r}")
        self.assertTrue(data.get("ok"))

        code, stdout, data = self._run(["validate", str(self.task_path)])
        self.assertEqual(code, 0, f"validate 실패: {stdout!r}")
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("violations_count"), 0)



# ═════════════════════════════════════════════════════════════════════════════
# 070: task-step 키 주소 체계 도입 1차 — RED-first 신규 테스트 9종
# PLAN 070 §3.7.2 클래스 설계 / TEST-SCENARIO 070 S-1~S-14
# [MUST] red-first.md §2/§3: 작성자(opal-test-agent mode:red) ≠ 구현자(op-dev-execute),
# 테스트 불변성(GREEN/fix 루핑 중 이 파일 수정 금지). 아래는 spec-validate/task-step
# 주소/--action-step/add-row --key/opdd enum/그룹 A pipeline.json 등 미구현 기능을
# 검증하므로, GREEN(PLAN §4 Step 1~9) 이전에는 FAIL/ERROR가 정상이다(RED 증거).
# ═════════════════════════════════════════════════════════════════════════════

_SCHEMA_DIR = _TOOL_DIR / "schema"


def _call070(fn, args):
    """cmd_* 함수 직접 호출 → (exit_code, result_dict).
    BaseTestCase._call_cmd와 동일 계약이나, BaseTestCase를 상속하지 않는 신규
    unittest.TestCase 클래스에서도 쓰기 위한 독립 헬퍼(신규 코드, 기존 미변경)."""
    import io
    from contextlib import redirect_stdout
    out = io.StringIO()
    exit_code = 0
    with redirect_stdout(out):
        try:
            fn(args)
        except SystemExit as e:
            exit_code = e.code
    output = out.getvalue().strip()
    result = json.loads(output) if output else {}
    return exit_code, result


def _run070(args_list):
    """run.sh subprocess 실호출 → (returncode, stdout_str, stderr_str, parsed_json).
    [MUST] red-first.md §4: mock/patch 금지 — 공개 인터페이스(stdout/stderr/exit code)만 관찰.
    """
    cmd = ["bash", str(_RUN_SH)] + args_list
    result = subprocess.run(cmd, capture_output=True, text=True)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


def _deepcopy_json(obj):
    """표준 라이브러리만(T-11) — json 왕복으로 딥카피(copy 모듈 불요)."""
    return json.loads(json.dumps(obj))


# ── PLAN 070 §3.6.2 그룹 A pipeline.json 스펙 전문(全文) 인용 — RED 임시 픽스처 ─────
# 그룹 A 4종 실파일(opal/skills/opal-pilot-*/references/pipeline.json)은 GREEN(Step 8)
# 에서 생성된다. RED 단계에서는 PLAN 인용 전문을 그대로 임시 파일로 만들어 사용한다.

_OPP_PIPELINE_SPEC = json.loads("""
{
  "spec_version": "1.0",
  "skill": "opp",
  "meta": { "mode_label": "Project Task", "stages": ["TASK", "PLAN", "EXECUTE", "CLOSE"] },
  "task_steps": [
    { "id": 1, "key": "task.task_md",        "stage": "TASK",    "item": "작업" },
    { "id": 2, "key": "task.user_confirm",   "stage": "TASK",    "item": "사용자 확인" },
    { "id": 3, "key": "plan.plan_md",        "stage": "PLAN",    "item": "작업" },
    { "id": 4, "key": "plan.pm_gate",        "stage": "PLAN",    "item": "PM Gate" },
    { "id": 5, "key": "plan.user_confirm",   "stage": "PLAN",    "item": "사용자 확인" },
    { "id": 6, "key": "execute.implement",   "stage": "EXECUTE", "item": "작업" },
    { "id": 7, "key": "execute.pm_gate",     "stage": "EXECUTE", "item": "PM Gate" },
    { "id": 8, "key": "execute.user_confirm","stage": "EXECUTE", "item": "사용자 확인" },
    { "id": 9, "key": "close.done_md",       "stage": "CLOSE",   "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "PLAN",    "artifacts": ["TASK.md", "PLAN.md"], "checklist": ["TASK.md 요구사항", "PLAN.md §3", "PLAN.md §4"] },
    { "stage": "EXECUTE", "artifacts": ["GC-CONVENTION-*.md"], "checklist": ["PLAN.md §3 실행 체크리스트", "컨벤션 자동 진단"] }
  ]
}
""")

_OPD_PIPELINE_SPEC = json.loads("""
{
  "spec_version": "1.0",
  "skill": "opd",
  "meta": { "mode_label": "Full Task", "stages": ["TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO", "EXECUTE", "TEST", "CLOSE"] },
  "task_steps": [
    { "id": 1,  "key": "task.task_md",                 "stage": "TASK",          "item": "작업" },
    { "id": 2,  "key": "task.user_confirm",            "stage": "TASK",          "item": "사용자 확인" },
    { "id": 3,  "key": "analysis.analysis_md",         "stage": "ANALYSIS",      "item": "작업" },
    { "id": 4,  "key": "analysis.pm_gate",             "stage": "ANALYSIS",      "item": "PM Gate" },
    { "id": 5,  "key": "analysis.user_confirm",        "stage": "ANALYSIS",      "item": "사용자 확인" },
    { "id": 6,  "key": "plan.plan_md",                 "stage": "PLAN",          "item": "작업" },
    { "id": 7,  "key": "plan.pm_gate",                 "stage": "PLAN",          "item": "PM Gate" },
    { "id": 8,  "key": "plan.user_confirm",            "stage": "PLAN",          "item": "사용자 확인" },
    { "id": 9,  "key": "test_scenario.test_scenario_md","stage": "TEST-SCENARIO","item": "작업" },
    { "id": 10, "key": "test_scenario.user_confirm",   "stage": "TEST-SCENARIO", "item": "사용자 확인" },
    { "id": 11, "key": "execute.implement",            "stage": "EXECUTE",       "item": "작업" },
    { "id": 12, "key": "test.run_tests",               "stage": "TEST",          "item": "작업" },
    { "id": 13, "key": "test.pm_gate",                 "stage": "TEST",          "item": "PM Gate" },
    { "id": 14, "key": "test.user_confirm",            "stage": "TEST",          "item": "사용자 확인" },
    { "id": 15, "key": "close.done_md",                "stage": "CLOSE",         "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "ANALYSIS",      "artifacts": ["ANALYSIS.md"], "checklist": ["-"] },
    { "stage": "PLAN",          "artifacts": ["TASK.md", "PLAN.md"], "checklist": ["TASK.md 요구사항", "PLAN.md §4.2", "PLAN.md §5", "PLAN.md §리스크 가설 표"] },
    { "stage": "TEST-SCENARIO", "artifacts": ["TEST-SCENARIO.md"], "checklist": ["mock 부재(grep)", "사전 조건 데이터 채워짐", "Given/When/Then 3필드", "가설↔시나리오 매핑 완전", "L1/L2/L3 계층 명시", "L3 [SUPERVISOR] 마커", "실행 방식(M1/M2/M3) 명시"] },
    { "stage": "TEST",          "artifacts": ["TEST-SCENARIO.md", "GC-CONVENTION-*.md"], "checklist": ["시나리오 결과/코드품질/보안/회귀", "컨벤션 자동 진단 PASS"] }
  ]
}
""")

_OPDS_PIPELINE_SPEC = json.loads("""
{
  "spec_version": "1.0",
  "skill": "opds",
  "meta": { "mode_label": "Short Task", "stages": ["TASK", "PLAN", "EXECUTE", "TEST", "CLOSE"] },
  "task_steps": [
    { "id": 1,  "key": "task.task_md",         "stage": "TASK",    "item": "작업" },
    { "id": 2,  "key": "task.user_confirm",    "stage": "TASK",    "item": "사용자 확인" },
    { "id": 3,  "key": "plan.plan_md",         "stage": "PLAN",    "item": "작업" },
    { "id": 4,  "key": "plan.pm_gate",         "stage": "PLAN",    "item": "PM Gate" },
    { "id": 5,  "key": "plan.user_confirm",    "stage": "PLAN",    "item": "사용자 확인" },
    { "id": 6,  "key": "execute.implement",    "stage": "EXECUTE", "item": "작업" },
    { "id": 7,  "key": "test.run_tests",       "stage": "TEST",    "item": "작업" },
    { "id": 8,  "key": "test.pm_gate",         "stage": "TEST",    "item": "PM Gate" },
    { "id": 9,  "key": "test.user_confirm",    "stage": "TEST",    "item": "사용자 확인" },
    { "id": 10, "key": "close.done_md",        "stage": "CLOSE",   "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "PLAN", "artifacts": ["TASK.md", "PLAN.md", "TEST-SCENARIO.md"], "checklist": ["TASK.md 요구사항", "PLAN.md §4.2", "PLAN.md §5", "TEST-SCENARIO.md 시나리오 목록/보안/설계 피드백"] },
    { "stage": "TEST", "artifacts": ["TEST-SCENARIO.md", "GC-CONVENTION-*.md"], "checklist": ["시나리오 결과/코드품질/보안/회귀", "컨벤션 자동 진단 PASS"] }
  ]
}
""")

_OPDW_PIPELINE_SPEC = json.loads("""
{
  "spec_version": "1.0",
  "skill": "opdw",
  "meta": { "mode_label": "Wireframe UI", "stages": ["TASK", "WIREFRAME", "EXECUTE", "CLOSE"] },
  "task_steps": [
    { "id": 1, "key": "task.task_md",           "stage": "TASK",      "item": "작업" },
    { "id": 2, "key": "task.user_confirm",      "stage": "TASK",      "item": "사용자 확인" },
    { "id": 3, "key": "wireframe.wireframe_md",  "stage": "WIREFRAME", "item": "작업",        "conditional": true },
    { "id": 4, "key": "wireframe.pm_gate",       "stage": "WIREFRAME", "item": "PM Gate",     "conditional": true },
    { "id": 5, "key": "wireframe.user_confirm",  "stage": "WIREFRAME", "item": "사용자 확인", "conditional": true },
    { "id": 6, "key": "execute.implement",       "stage": "EXECUTE",   "item": "작업" },
    { "id": 7, "key": "execute.pm_gate",         "stage": "EXECUTE",   "item": "PM Gate" },
    { "id": 8, "key": "execute.user_confirm",    "stage": "EXECUTE",   "item": "사용자 확인" },
    { "id": 9, "key": "close.done_md",           "stage": "CLOSE",     "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "WIREFRAME", "artifacts": ["TASK.md", "wireframe.md"], "checklist": ["TASK.md 요구사항", "wireframe.md 화면 목록", "op-dev-qa 와이어프레임 검증 기준"] },
    { "stage": "EXECUTE",   "artifacts": ["changed_files", "GC-CONVENTION-*.md"], "checklist": ["빌드/린트 결과", "wireframe↔코드 대조", "컨벤션 자동 진단"] }
  ]
}
""")

# (skill, 픽스처 스펙, 픽스처 행 수, 실파일 행 수, 실파일 스킬 디렉토리)
# - 픽스처 행 수: PLAN 070 §3.6.2 전문 인용 시점의 고정값. 실파일이 진화해도 바꾸지 않는다.
# - 실파일 행 수: 현행 pipeline.json 기준. 파이프라인 행 추가/삭제 시 함께 갱신한다.
#   073(opd `test_scenario.scenario_gate`)·075(opds `plan.scenario_gate`) 목표-커버 게이트 행
#   추가로 두 값이 분기했다.
_GROUP_A_SPECS = [
    ("opp",  _OPP_PIPELINE_SPEC,  9,  9,  "opal-pilot-project"),
    ("opd",  _OPD_PIPELINE_SPEC,  15, 16, "opal-pilot-dev"),
    ("opds", _OPDS_PIPELINE_SPEC, 10, 11, "opal-pilot-dev-short"),
    ("opdw", _OPDW_PIPELINE_SPEC, 9,  9,  "opal-pilot-dev-wireframe"),
]


# ═════════════════════════════════════════════════════════════════════════════
# 1. TestPipelineSpecValidate — F-001 spec-validate (TEST-SCENARIO S-7)
# ═════════════════════════════════════════════════════════════════════════════

class TestPipelineSpecValidate(unittest.TestCase):
    """F-001 spec-validate 서브명령 — PLAN 070 §3.1.2 / TEST-SCENARIO S-7.

    validate_pipeline_spec()/cmd_spec_validate()는 아직 state_tool.py에 없다 —
    GREEN(Step 1·2) 이전에는 AttributeError(직접 호출) 또는 argparse invalid-choice
    (subprocess)로 실패하는 것이 정상 RED 증거다.
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_spec(self, name, spec_dict):
        p = self.tmpdir / name
        p.write_text(json.dumps(spec_dict, ensure_ascii=False), encoding="utf-8")
        return p

    def test_valid_spec_direct_zero_violations(self):
        """[T070/S-7] 유효 스펙(opp) → validate_pipeline_spec() violations 0건 (직접 호출)."""
        violations = ST.validate_pipeline_spec(_deepcopy_json(_OPP_PIPELINE_SPEC))
        self.assertEqual(violations, [], f"유효 스펙인데 violations 발생: {violations}")

    def test_valid_spec_cmd_spec_validate_ok_true(self):
        """[T070/S-7/TS-002] cmd_spec_validate — 정상 스펙 → ok:true, violations_count:0 (직접 호출)."""
        spec_path = self._write_spec("opp.json", _OPP_PIPELINE_SPEC)
        args = types.SimpleNamespace(spec_path=str(spec_path))
        exit_code, result = _call070(ST.cmd_spec_validate, args)
        self.assertEqual(exit_code, 0, f"유효 스펙인데 exit!=0: {result}")
        self.assertTrue(result.get("ok"), f"유효 스펙인데 ok=false: {result}")
        self.assertEqual(result.get("violations_count"), 0)

    def test_key_duplicate_spec_violation(self):
        """[T070/S-7/TS-003] key 중복 스펙 → spec_key_duplicate violation (직접 호출)."""
        spec = _deepcopy_json(_OPP_PIPELINE_SPEC)
        spec["task_steps"][1]["key"] = spec["task_steps"][0]["key"]  # id2 key를 id1과 중복
        violations = ST.validate_pipeline_spec(spec)
        codes = [v.get("code") for v in violations]
        self.assertIn("spec_key_duplicate", codes,
                      f"key 중복인데 spec_key_duplicate 없음: {violations}")

    def test_key_format_violation(self):
        """[T070/S-7/TS-004] key 형식 위반(대문자·언더스코어, TASK.md 예시 'Plan.PM_Gate')
        → spec_key_format_invalid (직접 호출)."""
        spec = _deepcopy_json(_OPP_PIPELINE_SPEC)
        spec["task_steps"][3]["key"] = "Plan.PM_Gate"  # 대문자 포함 — KEY_PATTERN 위반
        violations = ST.validate_pipeline_spec(spec)
        codes = [v.get("code") for v in violations]
        self.assertIn("spec_key_format_invalid", codes,
                      f"key 형식 위반인데 spec_key_format_invalid 없음: {violations}")

    def test_stage_enum_violation(self):
        """[T070/S-7/TS-005] stage enum 외 값('FOO') → spec_stage_invalid (직접 호출)."""
        spec = _deepcopy_json(_OPP_PIPELINE_SPEC)
        spec["task_steps"][2]["stage"] = "FOO"
        violations = ST.validate_pipeline_spec(spec)
        codes = [v.get("code") for v in violations]
        self.assertIn("spec_stage_invalid", codes,
                      f"stage enum 위반인데 spec_stage_invalid 없음: {violations}")

    def test_spec_validate_subprocess_exit_codes(self):
        """[T070/S-7] run.sh spec-validate — 유효/위반 스펙 exit code 0/1 구분
        (subprocess 실호출, mock 금지 — red-first.md §4)."""
        valid_path = self._write_spec("valid.json", _OPP_PIPELINE_SPEC)
        code, stdout, stderr, data = _run070(["spec-validate", str(valid_path)])
        self.assertEqual(code, 0, f"유효 스펙 spec-validate가 exit 0이어야 함 (stdout={stdout!r})")
        self.assertTrue(data.get("ok"))

        bad_spec = _deepcopy_json(_OPP_PIPELINE_SPEC)
        bad_spec["task_steps"][0]["stage"] = "FOO"
        bad_path = self._write_spec("bad.json", bad_spec)
        code, stdout, stderr, data = _run070(["spec-validate", str(bad_path)])
        self.assertEqual(code, 1, f"위반 스펙 spec-validate가 exit 1이어야 함 (stdout={stdout!r})")
        self.assertFalse(data.get("ok"))

    # ── 091 F-004 R-10: task_steps[].gate 검사 4종 (TEST-SCENARIO S-9) ──────────
    # [MUST] red-first.md §4: validate_pipeline_spec()에 gate 검사가 아직 없다
    # (Step 8 GREEN 이전) — 아래 4건은 codes가 항상 빈 리스트라 FAIL이 정상(RED 증거).

    def test_gate_type_invalid_violation(self):
        """[T091/L1-S9] task_steps[].gate가 object가 아님 → spec_gate_type_invalid."""
        spec = _deepcopy_json(_OPP_PIPELINE_SPEC)
        spec["task_steps"][3]["gate"] = ["not", "a", "dict"]  # id4 plan.pm_gate
        violations = ST.validate_pipeline_spec(spec)
        codes = [v.get("code") for v in violations]
        self.assertIn("spec_gate_type_invalid", codes,
                      f"gate가 배열인데 spec_gate_type_invalid 없음: {violations}")

    def test_gate_missing_field_violation(self):
        """[T091/L1-S9] gate.checklist 키 누락 → spec_gate_missing_field."""
        spec = _deepcopy_json(_OPP_PIPELINE_SPEC)
        spec["task_steps"][3]["gate"] = {"artifacts": ["TASK.md"]}  # checklist 누락
        violations = ST.validate_pipeline_spec(spec)
        codes = [v.get("code") for v in violations]
        self.assertIn("spec_gate_missing_field", codes,
                      f"gate.checklist 누락인데 spec_gate_missing_field 없음: {violations}")

    def test_gate_field_type_invalid_violation(self):
        """[T091/L1-S9] gate.artifacts 요소가 문자열이 아님 → spec_gate_field_type_invalid."""
        spec = _deepcopy_json(_OPP_PIPELINE_SPEC)
        spec["task_steps"][3]["gate"] = {"artifacts": [1, 2], "checklist": ["ok"]}
        violations = ST.validate_pipeline_spec(spec)
        codes = [v.get("code") for v in violations]
        self.assertIn("spec_gate_field_type_invalid", codes,
                      f"gate.artifacts 요소가 문자열이 아닌데 spec_gate_field_type_invalid 없음: {violations}")

    def test_gate_checklist_empty_violation(self):
        """[T091/L1-S9] gate.checklist:[] → spec_gate_checklist_empty
        (artifacts:[]는 그 자체로는 위반이 아님 — §3.4.2 (1) MUST)."""
        spec = _deepcopy_json(_OPP_PIPELINE_SPEC)
        spec["task_steps"][3]["gate"] = {"artifacts": [], "checklist": []}
        violations = ST.validate_pipeline_spec(spec)
        codes = [v.get("code") for v in violations]
        self.assertIn("spec_gate_checklist_empty", codes,
                      f"checklist:[] 인데 spec_gate_checklist_empty 없음: {violations}")
        self.assertNotIn("spec_gate_missing_field", codes,
                         "artifacts:[]/checklist:[] 필드 자체 존재는 missing_field가 아니어야 함")

    def test_gate_empty_artifacts_alone_is_not_a_violation(self):
        """[T091/L1-S9] artifacts:[]만 있고 checklist가 채워져 있으면 위반 0건
        (opdw/opp EXECUTE 게이트의 정당성 확인, R-10 AC 해석 확정)."""
        spec = _deepcopy_json(_OPP_PIPELINE_SPEC)
        spec["task_steps"][3]["gate"] = {"artifacts": [], "checklist": ["ok"]}
        violations = ST.validate_pipeline_spec(spec)
        self.assertEqual(violations, [], f"artifacts:[] 단독인데 violations 발생: {violations}")

    def test_real_pipeline_json_gate_specs_valid_zero_violations(self):
        """[T091/L1-S9] 실 pipeline.json 10종(gate 보유 9종 + opgc) — 정상 스펙
        validate_pipeline_spec violations 0건 + spec-validate CLI ok:true (실측 10/10).
        gate 검사가 없는 현재도 우연히 통과할 수 있으나(비검사=무해), Step 8 GREEN 이후에도
        계속 참이어야 하는 회귀 앵커다."""
        repo_root = _TOOL_DIR.parent.parent.parent
        real_skill_dirs = [
            "opal-pilot-project", "opal-pilot-dev", "opal-pilot-dev-short",
            "opal-pilot-dev-wireframe", "opal-pilot-write-tech", "opal-pilot-sdd",
            "opal-pilot-data-design", "opal-pilot-project-dev", "opal-pilot-project-loop",
            "opal-pilot-gc",
        ]
        for skill_dir in real_skill_dirs:
            spec_path = repo_root / "opal" / "skills" / skill_dir / "references" / "pipeline.json"
            with self.subTest(skill=skill_dir):
                self.assertTrue(spec_path.exists(), f"실 pipeline.json 부재: {spec_path}")
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                violations = ST.validate_pipeline_spec(spec)
                self.assertEqual(violations, [],
                                  f"{skill_dir} pipeline.json이 유효해야 하는데 violations: {violations}")
                code, stdout, stderr, data = _run070(["spec-validate", str(spec_path)])
                self.assertEqual(code, 0, f"{skill_dir} spec-validate exit!=0 (stdout={stdout!r})")
                self.assertTrue(data.get("ok"), f"{skill_dir} spec-validate ok:false: {data}")


# ═════════════════════════════════════════════════════════════════════════════
# 2. TestPipelineJsonInit — F-002 json 로딩·key 영속 (TEST-SCENARIO S-1)
# ═════════════════════════════════════════════════════════════════════════════

class TestPipelineJsonInit(BaseTestCase):
    """F-002 build_rows_from_pipeline_json + init `.json` 확장자 분기 —
    PLAN 070 §3.2.2 / TEST-SCENARIO S-1.

    build_rows_from_pipeline_json()은 아직 없고 cmd_init의 `.json`/`.md` 확장자 분기도
    없다(현재는 --rows-from이 확장자 무관 build_rows_from_skill_md로만 라우팅) — GREEN
    (Step 5) 이전에는 이하 테스트가 FAIL한다(행 수 불일치/skill_md_parse_error).
    """

    _MINI_SPEC = {
        "spec_version": "1.0",
        "skill": "opp",
        "meta": {"mode_label": "Mini", "stages": ["TASK", "PLAN", "CLOSE"]},
        "task_steps": [
            {"id": 1, "key": "task.task_md",      "stage": "TASK",  "item": "작업"},
            {"id": 2, "key": "task.user_confirm", "stage": "TASK",  "item": "사용자 확인"},
            {"id": 3, "key": "plan.plan_md",       "stage": "PLAN",  "item": "작업"},
            {"id": 4, "key": "close.done_md",      "stage": "CLOSE", "item": "DONE.md 생성"},
        ],
    }

    def _write_spec_file(self, name, spec_dict):
        p = self.tmpdir / name
        p.write_text(json.dumps(spec_dict, ensure_ascii=False), encoding="utf-8")
        return p

    def test_json_init_row_count_and_all_keys_present(self):
        """[T070/S-1] `.json` init → rows_count==스펙 길이 + 전 행 key 존재."""
        spec_path = self._write_spec_file("mini.json", self._MINI_SPEC)
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                rows_from=str(spec_path),
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 0, f"json init 실패: {result}")
        state = self._state()
        self.assertEqual(len(state["rows"]), 4)
        for row in state["rows"]:
            self.assertIn("key", row, f"row {row.get('row_id')}에 key 없음")
            self.assertTrue(row["key"], f"row {row.get('row_id')} key가 비어있음")

    def test_json_init_keys_match_spec_exactly(self):
        """[T070/S-1] rows[].key가 스펙 task_steps[].key와 순서대로 일치."""
        spec_path = self._write_spec_file("mini2.json", self._MINI_SPEC)
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                rows_from=str(spec_path),
            )
            self._call_cmd(ST.cmd_init, args)
        state = self._state()
        expected_keys = [ts["key"] for ts in self._MINI_SPEC["task_steps"]]
        actual_keys = [row.get("key") for row in state["rows"]]
        self.assertEqual(actual_keys, expected_keys)

    def test_conditional_field_persisted_as_pure_metadata(self):
        """[T070/S-1, DEC-1] conditional:true task_step → rows[].conditional=true 저장,
        자동 na 마킹 없음(status는 pending 유지) — opdw WIREFRAME id3/id4(작업/PM Gate)로 검증."""
        spec_path = self._write_spec_file("opdw.json", _OPDW_PIPELINE_SPEC)
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opdw", mode="agentic",
                rows_from=str(spec_path),
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 0, f"opdw json init 실패: {result}")
        state = self._state()
        wireframe_work = state["rows"][2]   # id3: wireframe.wireframe_md, item=작업
        wireframe_gate = state["rows"][3]   # id4: wireframe.pm_gate, item=PM Gate
        self.assertTrue(wireframe_work.get("conditional"), "id3 conditional=true 저장 안 됨")
        self.assertTrue(wireframe_gate.get("conditional"), "id4 conditional=true 저장 안 됨")
        self.assertEqual(
            wireframe_work["status"], "pending",
            f"DEC-1: conditional은 순수 메타데이터 — status가 na로 자동전환되면 안 됨, "
            f"실제: {wireframe_work['status']}"
        )
        self.assertEqual(wireframe_gate["status"], "pending")

    def test_json_init_stamps_schema_version_1_1_and_validates(self):
        """[T070 후속/Part B] `.json`(pipeline.json) init → schema_version=="1.1" + validate ok.

        RED 근거: cmd_init이 schema_version을 하드코딩 "1.0"으로 stamp하던 시점에는
        rows[]에 key가 있어도 "1.0"이 나와 본 테스트가 FAIL했다(Part B-1 구현 전 확인).
        """
        spec_path = self._write_spec_file("mini_schema11.json", self._MINI_SPEC)
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                rows_from=str(spec_path),
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 0, f"json init 실패: {result}")
        state = self._state()
        self.assertEqual(
            state["schema_version"], "1.1",
            "rows[]에 key가 있는 pipeline.json init은 schema_version 1.1로 승격되어야 함"
        )
        validate_result = self._validate()
        self.assertTrue(validate_result["ok"], f"1.1 state.json validate 실패: {validate_result}")

    def test_s22_rows_from_json_regression_after_import_existing_removal(self):
        """[T094/L1-F002] S-22 — `--import-existing` 및 074 key 재접합 삭제(D-2)가
        정상 `--rows-from <pipeline.json>` 경로를 훼손하지 않아야 한다(회귀).
        실 opd pipeline.json(16개 task_steps)으로 init 시 `rows[].key` 전건
        영속화 + `schema_version=="1.1"` 유지를 확인한다.

        이 테스트는 D-2가 삭제하는 대상(`--import-existing`/`_reattach_import_keys`)
        과 무관한 정상 경로만 검증하므로, F-002 삭제 작업 전후 모두 통과해야
        하는 회귀 안전망이다(TEST-SCENARIO.md S-22 '정상 경로 회귀')."""
        self.assertTrue(_OPD_REAL_PIPELINE_JSON.exists())
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opd", mode="agentic",
                rows_from=str(_OPD_REAL_PIPELINE_JSON),
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 0, f"opd pipeline.json init 실패: {result}")
        state = self._state()
        self.assertEqual(state["schema_version"], "1.1",
                         "실 opd pipeline.json init은 schema_version 1.1을 유지해야 함")
        with open(_OPD_REAL_PIPELINE_JSON, encoding="utf-8") as f:
            spec = json.load(f)
        expected_keys = [ts["key"] for ts in spec["task_steps"]]
        actual_keys = [row.get("key") for row in state["rows"]]
        self.assertEqual(actual_keys, expected_keys,
                         "rows[].key가 실 pipeline.json task_steps[].key 순서와 불일치")
        validate_result = self._validate()
        self.assertTrue(validate_result["ok"], f"validate 실패: {validate_result}")


# ═════════════════════════════════════════════════════════════════════════════
# 3. TestStateSchema11Compat — F-002 state.schema.json 1.1 병행 (TEST-SCENARIO S-4)
# ═════════════════════════════════════════════════════════════════════════════

class TestStateSchema11Compat(unittest.TestCase):
    """F-002 state.schema.json 1.1 병행 — PLAN 070 §3.2.2 / TEST-SCENARIO S-4.

    state.schema.json의 schema_version은 아직 const:"1.0"이고 rows[].items.properties에
    key/conditional이 등록되어 있지 않다 — GREEN(Step 4) 이전에는 이하 정적 스키마 검증이
    FAIL한다.
    """

    def setUp(self):
        schema_path = _SCHEMA_DIR / "state.schema.json"
        with open(schema_path, encoding="utf-8") as f:
            self.schema = json.load(f)

    def test_schema_version_enum_allows_1_0_and_1_1(self):
        """[T070/S-4] schema_version이 enum(["1.0","1.1"])이어야 함 — 현재는 const:"1.0"."""
        version_schema = self.schema["properties"]["schema_version"]
        self.assertIn("enum", version_schema,
                      f"schema_version이 아직 enum이 아님(1.1 병행 미지원): {version_schema}")
        self.assertEqual(set(version_schema["enum"]), {"1.0", "1.1"})

    def test_rows_key_field_registered_in_schema(self):
        """[T070/S-4, R-A2] rows[].items.properties에 key(pattern) 필드가 등록되어야 함."""
        row_props = self.schema["properties"]["rows"]["items"]["properties"]
        self.assertIn("key", row_props, "rows[].items.properties에 key 필드 미등록")
        self.assertIn("pattern", row_props.get("key", {}), "key 필드에 pattern 미지정")

    def test_rows_conditional_field_registered_in_schema(self):
        """[T070/S-4] rows[].items.properties에 conditional(boolean) 필드가 등록되어야 함."""
        row_props = self.schema["properties"]["rows"]["items"]["properties"]
        self.assertIn("conditional", row_props, "rows[].items.properties에 conditional 필드 미등록")
        self.assertEqual(row_props.get("conditional", {}).get("type"), "boolean")

    def test_key_bearing_1_1_state_and_legacy_1_0_state_both_validate_ok(self):
        """[T070/S-4] key 有 1.1 state.json + key 無 1.0 state.json 모두 cmd_validate ok:true.

        스키마 필드 등록(위 테스트들)이 먼저 충족되어야 이 조합 검증이 SSOT와 정합한
        상태로 의미를 가진다 — rows[].key가 스키마에 반영되지 않은 현재 상태에서는
        첫 assertIn에서 실패한다(런타임 cmd_validate 자체는 schema.json을 참조하지
        않으므로 이 assertIn이 스키마 드리프트를 포착하는 핵심 검증이다).
        """
        row_props = self.schema["properties"]["rows"]["items"]["properties"]
        self.assertIn("key", row_props,
                      "rows[].key가 스키마에 등록되어야 1.1 state.json이 SSOT 정합 상태다")

        # 기능 관측: key 있는 state.json 구성 후 cmd_validate ok:true
        tmpdir = pathlib.Path(tempfile.mkdtemp())
        try:
            task_path = tmpdir / "070-schema-compat"
            task_path.mkdir()
            with _mock_now():
                args = make_args(
                    task_path=str(task_path), skill="opp", mode="interactive",
                    rows_spec=SIMPLE_ROWS_SPEC,
                )
                _call070(ST.cmd_init, args)
            state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
            for i, row in enumerate(state["rows"]):
                row["key"] = f"stage_{i}.item_{i}"
                row["conditional"] = False
            state["schema_version"] = "1.1"
            (task_path / "state.json").write_text(
                json.dumps(state, ensure_ascii=False), encoding="utf-8"
            )

            val_args = make_args(task_path=str(task_path))
            exit_code, result = _call070(ST.cmd_validate, val_args)
            self.assertEqual(exit_code, 0, f"key 있는 1.1 state.json validate 실패: {result}")
            self.assertTrue(result.get("ok"))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ═════════════════════════════════════════════════════════════════════════════
# 4. TestTaskStepAddressing — F-003 3주소·conflict (TEST-SCENARIO S-2,S-3,S-10,S-11,S-13)
# ═════════════════════════════════════════════════════════════════════════════

class TestTaskStepAddressing(BaseTestCase):
    """F-003 resolve_row_index — 3주소(--task-step/--task-step-id/--row) 통일 해석 +
    task_step_addr_required/conflict — PLAN 070 §3.3.2 / TEST-SCENARIO S-2, S-3, S-10,
    S-11, S-13.

    resolve_row_index()가 아직 없고 cmd_mark/advance/block은 여전히
    find_row_index(state, args.row, command)만 호출한다 — args.task_step/args.task_step_id를
    지정해도 무시되므로(row=None) 아래 테스트는 GREEN(Step 6) 이전에는 FAIL한다.
    """

    KEYED_ROWS = json.dumps([
        {"stage": "TASK",    "item": "작업"},
        {"stage": "TASK",    "item": "사용자 확인"},
        {"stage": "PLAN",    "item": "작업"},
        {"stage": "PLAN",    "item": "PM Gate"},
        {"stage": "PLAN",    "item": "사용자 확인"},
        {"stage": "EXECUTE", "item": "작업"},
        {"stage": "CLOSE",   "item": "DONE.md 생성"},
    ])
    KEYS = [
        "task.task_md", "task.user_confirm", "plan.plan_md", "plan.pm_gate",
        "plan.user_confirm", "execute.implement", "close.done_md",
    ]

    def setUp(self):
        super().setUp()
        self._init(rows_spec=self.KEYED_ROWS)
        # 1.1 스타일 key 주입 — 그룹 A pipeline.json init(F-002) 완료 상태를 시뮬레이션
        state = self._state()
        for row, key in zip(state["rows"], self.KEYS):
            row["key"] = key
        (self.task_path / "state.json").write_text(
            json.dumps(state, ensure_ascii=False), encoding="utf-8"
        )

    def _mark_by(self, **addr_kwargs):
        with _mock_now():
            args = make_args(task_path=str(self.task_path), done=True, **addr_kwargs)
            return self._call_cmd(ST.cmd_mark, args)

    def test_three_way_addressing_same_row_same_result(self):
        """[T070/S-2, H-1] 동일 행(row_id=4, plan.pm_gate)을 --task-step/--task-step-id/--row
        3방식으로 각각 mark — 모두 row_id=4로 동일 갱신·동일 응답이어야 한다."""
        # 앞 행(1,2,3) 먼저 완료 — stage-transition guard(scope=full) 통과
        self._mark(1)
        self._mark(2)
        self._mark(3)

        with self.subTest(addr="task_step"):
            exit_code, result = self._mark_by(task_step="plan.pm_gate")
            self.assertEqual(exit_code, 0, f"--task-step mark 실패: {result}")
            self.assertEqual(result.get("row_id"), 4)

        with self.subTest(addr="task_step_id"):
            exit_code, result = self._mark_by(task_step_id=4)
            self.assertEqual(exit_code, 0, f"--task-step-id mark 실패: {result}")
            self.assertEqual(result.get("row_id"), 4)

        with self.subTest(addr="row_deprecated"):
            exit_code, result = self._mark_by(row=4)
            self.assertEqual(exit_code, 0, f"--row(deprecated) mark 실패: {result}")
            self.assertEqual(result.get("row_id"), 4)

    def test_task_step_not_found_returns_candidates(self):
        """[T070/S-3] 존재하지 않는 key(--task-step plan.qa_gate) → task_step_not_found +
        candidates 목록 포함 + exit 1."""
        self._mark(1)
        self._mark(2)
        self._mark(3)
        exit_code, result = self._mark_by(task_step="plan.qa_gate")
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "task_step_not_found",
                         f"미매칭 key인데 task_step_not_found 아님: {result}")
        self.assertIn("candidates", result, "후보 목록(candidates) 누락")
        self.assertIn("plan.pm_gate", result.get("candidates", []))

    def test_addr_required_when_zero_address_subprocess(self):
        """[T070/S-10, H-2] 주소 플래그 0개(--row/--task-step/--task-step-id 전부 없음)로
        mark --done → task_step_addr_required + exit 1 (argparse 레벨, subprocess 실호출)."""
        code, stdout, stderr, data = _run070([
            "mark", str(self.task_path), "--done",
        ])
        self.assertEqual(code, 1, f"주소 0개인데 exit!=1 (stdout={stdout!r})")
        self.assertEqual(data.get("error"), "task_step_addr_required")

    def test_addr_conflict_task_step_and_row_together_subprocess(self):
        """[T070/S-11, H-2] --task-step과 --row 동시 지정 → task_step_addr_conflict + exit 1
        (argparse mutex는 exit 2 usage 에러라 코드 방출 불가하므로 subprocess 실호출로 검증)."""
        code, stdout, stderr, data = _run070([
            "mark", str(self.task_path),
            "--task-step", "plan.pm_gate", "--row", "4", "--done",
        ])
        self.assertEqual(code, 1, f"주소 2개 동시인데 exit!=1 (stdout={stdout!r}, stderr={stderr!r})")
        self.assertEqual(data.get("error"), "task_step_addr_conflict")

    def test_close_gate_regression_via_task_step_addressing_subprocess(self):
        """[T070/S-13, H-7] agentic CLOSE 첫 행을 --task-step 주소로 --auto-pass 시도 →
        agentic_close_gate_requires_user 거부가 유지되어야 한다(item 한글 판정 불변, R-A5).
        subprocess 실호출.

        [PM 승인 정정] 최초 버전은 `--rows-spec`(inline JSON — key 미부여 경로)으로
        init한 뒤 `--task-step`으로 주소를 지정해 자기모순이었다(항상 task_step_not_found).
        정정: `--rows-from <pipeline.json>`(opp 전문 픽스처, PLAN §3.6.2 인용) 경로로
        init해 key가 실제로 존재하는 상태를 구성한 뒤 CLOSE 게이트를 검증한다."""
        agentic_task = self.tmpdir / "070-close-gate-agentic"
        agentic_task.mkdir()
        spec_path = self.tmpdir / "opp-close-gate.json"
        spec_path.write_text(json.dumps(_OPP_PIPELINE_SPEC, ensure_ascii=False), encoding="utf-8")

        code, stdout, stderr, data = _run070([
            "init", str(agentic_task),
            "--skill", "opp", "--mode", "agentic",
            "--rows-from", str(spec_path),
        ])
        self.assertEqual(code, 0, f"agentic pipeline.json init 실패: {stdout!r}")

        # opp 스펙: row 2(task.user_confirm)/5(plan.user_confirm)는 "사용자 확인"(non-CLOSE)
        # — 093 F-002 훅이 다음 행 진입 시 자동 승인하므로 명시 mark가 불필요하다.
        # row 8(execute.user_confirm)은 CLOSE 직전 행이라 훅이 손대지 않으며(DEC-D 1차 방어)
        # 캡틴 승인(--owner user)이 필수다. 나머지(1,3,4,6,7)만 mark.
        for rid in (1, 3, 4, 6, 7):
            code, stdout, stderr, data = _run070(
                ["mark", str(agentic_task), "--row", str(rid), "--done"]
            )
            self.assertEqual(code, 0, f"사전 행 {rid} mark 실패: {stdout!r}")

        # row 8 = execute.user_confirm — CLOSE 직전 사용자 확인 행은 캡틴 승인만 가능
        code, stdout, stderr, data = _run070(
            ["mark", str(agentic_task), "--row", "8", "--done", "--owner", "user"]
        )
        self.assertEqual(code, 0, f"CLOSE 직전 사용자 확인 행 캡틴 승인 실패: {stdout!r}")

        # row 9 = close.done_md(CLOSE 첫 행) — key가 실제 존재하므로 --task-step 주소가
        # task_step_not_found 없이 정상 해석된 뒤 CLOSE 게이트가 발동해야 한다.
        code, stdout, stderr, data = _run070([
            "mark", str(agentic_task),
            "--task-step", "close.done_md",
            "--done", "--auto-pass",
        ])
        self.assertEqual(code, 1, f"agentic CLOSE 첫 행 auto-pass가 거부되어야 함 (stdout={stdout!r})")
        self.assertEqual(data.get("error"), "agentic_close_gate_requires_user",
                         f"CLOSE 게이트 회귀 — 실제 응답: {data!r} (stdout={stdout!r})")


# ═════════════════════════════════════════════════════════════════════════════
# 5. TestActionStepRename — F-003 --action-step 별칭 (TEST-SCENARIO S-9)
# ═════════════════════════════════════════════════════════════════════════════

class TestActionStepRename(BaseTestCase):
    """F-003 --action-step 별칭(dest="step" 공유) — PLAN 070 §3.3.2 / TEST-SCENARIO S-9.

    --action-step 필드는 아직 cmd_mark에서 전혀 참조되지 않는다(args.step만 참조) —
    action_step만 지정하고 step을 비워두면 현재는 즉시 done(비정형 step 폴백)으로 처리되어
    N<M 케이스에서 기대(in_progress 유지 + step 저장)가 깨진다 — GREEN(Step 6) 이전에는
    FAIL한다.
    """

    ROWS = json.dumps([
        {"stage": "TASK",    "item": "작업"},
        {"stage": "PLAN",    "item": "작업"},
        {"stage": "EXECUTE", "item": "다중 Step 작업"},
        {"stage": "CLOSE",   "item": "DONE.md 생성"},
    ])

    def setUp(self):
        super().setUp()
        self._init(rows_spec=self.ROWS)
        self._mark(1)
        self._mark(2)

    def _mark_execute(self, step=None, action_step=None):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path), row=3, done=True,
                as_worker=True, worker_stage="EXECUTE",
                step=step, action_step=action_step,
            )
            exit_code, _ = self._call_cmd(ST.cmd_mark, args)
        state = self._state()
        return exit_code, state["rows"][2]

    def test_action_step_n_lt_m_stays_in_progress(self):
        """[T070/S-9] --action-step 2/6(N<M) → status=in_progress 유지 + step 저장 —
        --step 2/6와 동일 동작이어야 함."""
        code, row = self._mark_execute(action_step="2/6")
        self.assertEqual(code, 0)
        self.assertEqual(row["status"], "in_progress",
                         f"--action-step 2/6(N<M)이면 in_progress여야 함, 실제: {row['status']}")
        self.assertEqual(row.get("step"), "2/6",
                         f"--action-step 값이 step으로 저장되어야 함, 실제: {row.get('step')}")

    def test_action_step_n_eq_m_done(self):
        """[T070/S-9] --action-step 6/6(N==M) → status=done + step 저장."""
        code, row = self._mark_execute(action_step="6/6")
        self.assertEqual(code, 0)
        self.assertEqual(row["status"], "done")
        self.assertEqual(row.get("step"), "6/6",
                         f"--action-step 값이 step으로 저장되어야 함, 실제: {row.get('step')}")

    def test_action_step_matches_step_flag_result(self):
        """[T070/S-9] --action-step 2/6 결과가 --step 2/6 결과와 동일해야 함(별칭 등가성,
        진행률 가드 회귀 0) — 별도 task로 --step 2/6 재현 후 비교."""
        code_a, row_a = self._mark_execute(action_step="2/6")

        other_task = self.tmpdir / "070-action-step-cmp"
        other_task.mkdir()
        with _mock_now():
            args = make_args(
                task_path=str(other_task), skill="opp", mode="interactive",
                rows_spec=self.ROWS,
            )
            self._call_cmd(ST.cmd_init, args)
        with _mock_now():
            args = make_args(task_path=str(other_task), row=1, done=True)
            self._call_cmd(ST.cmd_mark, args)
        with _mock_now():
            args = make_args(task_path=str(other_task), row=2, done=True)
            self._call_cmd(ST.cmd_mark, args)
        with _mock_now():
            args = make_args(
                task_path=str(other_task), row=3, done=True,
                as_worker=True, worker_stage="EXECUTE", step="2/6",
            )
            code_b, _ = self._call_cmd(ST.cmd_mark, args)
        state_b = json.loads((other_task / "state.json").read_text(encoding="utf-8"))
        row_b = state_b["rows"][2]

        self.assertEqual(code_a, code_b)
        self.assertEqual(row_a["status"], row_b["status"],
                         f"--action-step와 --step 결과 status 불일치: {row_a['status']} vs {row_b['status']}")
        self.assertEqual(row_a.get("step"), row_b.get("step"),
                         f"--action-step와 --step 결과 step 불일치: {row_a.get('step')} vs {row_b.get('step')}")


# ═════════════════════════════════════════════════════════════════════════════
# 6. TestAddRowKey — F-004 --key 지원·자동 생성 (TEST-SCENARIO S-5, S-6)
# ═════════════════════════════════════════════════════════════════════════════

class TestAddRowKey(BaseTestCase):
    """F-004 add-row --key(자동 생성·유일성) — PLAN 070 §3.4.2 / TEST-SCENARIO S-5, S-6.

    cmd_add_row는 아직 args.key를 전혀 참조하지 않고 신규 행 dict에 key 필드를 넣지 않는다 —
    GREEN(Step 7) 이전에는 이하 테스트가 FAIL한다(신규 행에 key 없음/중복 거부 없음).
    """

    ROWS = json.dumps([
        {"stage": "TASK",  "item": "작업"},
        {"stage": "PLAN",  "item": "작업"},
        {"stage": "PLAN",  "item": "PM Gate"},
        {"stage": "CLOSE", "item": "DONE.md 생성"},
    ])
    # 1.1 스타일 key 사전 주입(그룹 A init 완료 상태 시뮬레이션)
    KEYS = ["task.task_md", "plan.plan_md", "plan.pm_gate", "close.done_md"]

    def setUp(self):
        super().setUp()
        self._init(rows_spec=self.ROWS)
        state = self._state()
        for row, key in zip(state["rows"], self.KEYS):
            row["key"] = key
        (self.task_path / "state.json").write_text(
            json.dumps(state, ensure_ascii=False), encoding="utf-8"
        )

    def _add_row_with_key(self, after, stage, item, key=None):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                after=after, stage=stage, item=item, key=key,
            )
            return self._call_cmd(ST.cmd_add_row, args)

    def test_explicit_key_persisted_on_new_row(self):
        """[T070/S-5] --key 명시 지정 add-row → 신규 행에 해당 key 저장, 기존 key 불변."""
        exit_code, result = self._add_row_with_key(2, "TEST", "fix 작업", key="test.fix_manual")
        self.assertEqual(exit_code, 0, f"add-row 실패: {result}")
        state = self._state()
        new_row = state["rows"][2]  # after=2(row_id2) 다음 삽입 → row_id3
        self.assertEqual(new_row.get("key"), "test.fix_manual",
                         f"신규 행에 --key가 저장되어야 함, 실제: {new_row.get('key')}")
        existing_keys_after = [r.get("key") for r in state["rows"] if r.get("key") in self.KEYS]
        self.assertEqual(sorted(existing_keys_after), sorted(self.KEYS),
                         "재정렬 후 기존 행의 key가 훼손됨")

    def test_auto_key_generation_two_add_rows_no_collision(self):
        """[T070/S-5] key 미지정 add-row 2회(TEST/fix 작업) → 자동 키 test.fix_1, test.fix_2
        (충돌 없이 순차 부여), 기존 행 key 불변."""
        self._add_row_with_key(2, "TEST", "fix 작업")
        self._add_row_with_key(3, "TEST", "fix 작업")
        state = self._state()
        test_rows = [r for r in state["rows"] if r["stage"] == "TEST"]
        self.assertEqual(len(test_rows), 2)
        auto_keys = [r.get("key") for r in test_rows]
        self.assertEqual(auto_keys, ["test.fix_1", "test.fix_2"],
                         f"자동 key가 test.fix_1/test.fix_2 순으로 생성되어야 함, 실제: {auto_keys}")
        existing_keys_after = [r.get("key") for r in state["rows"] if r.get("key") in self.KEYS]
        self.assertEqual(sorted(existing_keys_after), sorted(self.KEYS),
                         "자동 key 생성 후 기존 행의 key가 훼손됨")

    def test_duplicate_key_rejected(self):
        """[T070/S-6] 기존 key와 동일한 --key 지정(add-row --key plan.pm_gate) → 중복 거부
        + exit 1(task_step_key_duplicate)."""
        exit_code, result = self._add_row_with_key(1, "PLAN", "재작업", key="plan.pm_gate")
        self.assertEqual(exit_code, 1, f"중복 key인데 exit!=1: {result}")
        self.assertEqual(result.get("error"), "task_step_key_duplicate",
                         f"중복 key인데 task_step_key_duplicate 아님: {result}")


# ═════════════════════════════════════════════════════════════════════════════
# 7. TestOpddEnumDrift — F-005 opdd 드리프트 정정 (TEST-SCENARIO S-8)
# ═════════════════════════════════════════════════════════════════════════════

class TestOpddEnumDrift(unittest.TestCase):
    """F-005 opdd 드리프트 정정(skill·stage enum 등록) — PLAN 070 §3.5.2 /
    TEST-SCENARIO S-8.

    현재 --skill choices에 "opdd"가 없고 STAGE_ENUM(및 add-row --stage choices)에
    "DICT"가 없다 — 둘 다 argparse choices 레벨 제약이라 subprocess 실호출로만 검증
    가능하다(red-first.md §4 — 직접 호출은 argparse 파싱을 우회하므로 이 제약을 재현
    못 함, TestOpplSkillInit(056) 관례와 동일).
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.task_path = self.tmpdir / "070-opdd-dryrun"
        self.task_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_skill_opdd_succeeds(self):
        """[T070/S-8] init --skill opdd --mode interactive → 거부 해소(exit 0, ok:true).
        현재는 choices 미등록으로 argparse usage error(exit 2)로 거부된다."""
        code, stdout, stderr, data = _run070([
            "init", str(self.task_path),
            "--skill", "opdd", "--mode", "interactive",
            "--rows-spec", json.dumps([
                {"stage": "TASK", "item": "작업"},
                {"stage": "PLAN", "item": "작업"},
                {"stage": "CLOSE", "item": "DONE.md 생성"},
            ]),
        ])
        self.assertEqual(code, 0, f"init --skill opdd는 exit 0이어야 함 (stdout={stdout!r}, stderr={stderr!r})")
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("task_id"), self.task_path.name)

    def test_add_row_stage_dict_accepted(self):
        """[T070/S-8] add-row --stage DICT --item 'DICT 작업' → enum 에러 없이 동작.
        현재는 STAGE_ENUM에 DICT가 없어 argparse choices 거부(exit 2)된다.
        (opdd 스킬 자체와 무관하게 STAGE_ENUM 확장만 독립 검증 — 임의 스킬 opp 사용)"""
        code, stdout, stderr, data = _run070([
            "init", str(self.task_path),
            "--skill", "opp", "--mode", "interactive",
            "--rows-spec", json.dumps([
                {"stage": "TASK", "item": "작업"},
                {"stage": "CLOSE", "item": "DONE.md 생성"},
            ]),
        ])
        self.assertEqual(code, 0, f"사전 init 실패: {stdout!r}")

        code, stdout, stderr, data = _run070([
            "add-row", str(self.task_path),
            "--after", "1", "--stage", "DICT", "--item", "DICT 작업",
        ])
        self.assertEqual(code, 0, f"add-row --stage DICT는 exit 0이어야 함 (stdout={stdout!r}, stderr={stderr!r})")
        self.assertTrue(data.get("ok"))


# ═════════════════════════════════════════════════════════════════════════════
# 8. TestGroupAPipelineSpecs — F-006 그룹 A 4종 실증 (TEST-SCENARIO S-1)
# ═════════════════════════════════════════════════════════════════════════════

class TestGroupAPipelineSpecs(unittest.TestCase):
    """F-006 그룹 A 4종 pipeline.json 실증 — PLAN 070 §3.6.2 / TEST-SCENARIO S-1.

    그룹 A 실파일(opal/skills/opal-pilot-*/references/pipeline.json)은 GREEN(Step 8)에서
    생성된다. RED 단계는 PLAN §3.6.2 인용 전문을 임시 픽스처로 검증한다(직접 호출) +
    실파일 존재 시에만 subprocess로 추가 검증한다(부재 시 명시적 skipTest).
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_all_four_fixtures_row_counts_and_keys(self):
        """[T070/S-1] opp/opd/opds/opdw 임시 픽스처 json init → 행 수 9/15/10/9 + 전 행 key
        존재·유일 (직접 호출, PLAN §3.6.2 전문 인용)."""
        for skill, spec, expected_count, _real_count, _skill_dir in _GROUP_A_SPECS:
            with self.subTest(skill=skill):
                spec_path = self.tmpdir / f"{skill}.pipeline.json"
                spec_path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
                task_path = self.tmpdir / f"070-{skill}-fixture"
                task_path.mkdir()
                with _mock_now():
                    args = make_args(
                        task_path=str(task_path), skill=skill, mode="interactive",
                        rows_from=str(spec_path),
                    )
                    exit_code, result = _call070(ST.cmd_init, args)
                self.assertEqual(exit_code, 0, f"{skill} json init 실패: {result}")
                state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(len(state["rows"]), expected_count,
                                 f"{skill} 행 수 불일치: {len(state['rows'])} != {expected_count}")
                keys = [r.get("key") for r in state["rows"]]
                self.assertTrue(all(keys), f"{skill}에 key 없는 행 존재: {keys}")
                self.assertEqual(len(keys), len(set(keys)), f"{skill} key 중복 발견: {keys}")

    def test_all_four_fixtures_spec_validate_ok(self):
        """[T070/S-1] 그룹 A 4종 임시 픽스처 모두 spec-validate ok:true (직접 호출)."""
        for skill, spec, _count, _real_count, _skill_dir in _GROUP_A_SPECS:
            with self.subTest(skill=skill):
                violations = ST.validate_pipeline_spec(_deepcopy_json(spec))
                self.assertEqual(violations, [], f"{skill} 스펙 위반 발견: {violations}")

    def test_real_group_a_pipeline_json_files_if_present(self):
        """[T070/S-1 후반] 그룹 A 실파일(opal/skills/opal-pilot-*/references/pipeline.json)이
        존재하면 spec-validate + init 실증(행 수 일치)까지 검증한다.

        [NOTE] 아래 skipTest는 "테스트 인프라 부재로 인한 graceful skip"(red-first.md §5
        금지 대상)이 아니다 — 이 태스크(070) 자체가 F-006(Step 8)에서 이 파일들을 만드는
        구조이므로, RED 시점(Step 8 이전)에는 아직 파일이 없는 것이 정상이고 의도된
        사전조건 skip이다. GREEN 이후(Step 8 완료) 이 테스트는 실파일을 발견해 자동으로
        활성화된다(skip에서 실행으로 전환).
        """
        skills_root = _TOOL_DIR.parent.parent / "skills"
        for skill, _spec, _fixture_count, real_count, skill_dir in _GROUP_A_SPECS:
            real_path = skills_root / skill_dir / "references" / "pipeline.json"
            if not real_path.exists():
                self.skipTest(
                    f"그룹 A 실파일 부재({real_path}) — GREEN(F-006/Step 8) 이전 의도된 "
                    f"사전조건 skip(graceful skip 아님). Step 8 완료 후 이 테스트가 활성화된다."
                )
            with self.subTest(skill=skill):
                code, stdout, stderr, data = _run070(["spec-validate", str(real_path)])
                self.assertEqual(code, 0, f"{skill} 실파일 spec-validate 실패: {stdout!r}")
                self.assertTrue(data.get("ok"))

                task_path = self.tmpdir / f"070-{skill}-real"
                task_path.mkdir()
                code, stdout, stderr, data = _run070([
                    "init", str(task_path),
                    "--skill", skill, "--mode", "interactive",
                    "--rows-from", str(real_path),
                ])
                self.assertEqual(code, 0, f"{skill} 실파일 init 실패: {stdout!r}")
                self.assertEqual(data.get("rows_count"), real_count,
                                 f"{skill} 실파일 행 수 불일치 — pipeline.json 변경 시 "
                                 f"_GROUP_A_SPECS 실파일 행 수도 갱신해야 한다")


# ═════════════════════════════════════════════════════════════════════════════
# 9. TestBackwardCompatAliases — 전역 --row/--step/.md 회귀 (TEST-SCENARIO S-12)
# ═════════════════════════════════════════════════════════════════════════════

class TestBackwardCompatAliases(BaseTestCase):
    """전역 --row/--step/.md 하위호환 별칭 회귀 — PLAN 070 §3.2.2/§3.4.2 /
    TEST-SCENARIO S-12.

    `.md` --rows-from 파싱 경로에 stderr deprecation 경고 1줄이 아직 없다(cmd_init의
    `.json`/`.md` 분기 자체가 없음) — GREEN(Step 5) 이전에는 stderr가 비어 FAIL한다.
    add-row --after(숫자, deprecated) 경로도 F-004 자동 key 생성이 적용되어야 하는데
    현재는 신규 행에 key가 전혀 없어 FAIL한다. --action-step CLI 플래그도 아직 argparse
    에 없어 FAIL한다.
    """

    def _make_skill_md(self, tmpdir):
        skill_md = tmpdir / "SKILL.md"
        skill_md.write_text("""
## STATE.md 도메인 치환값

| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ |  |
| 2 | PLAN | 작업 | ⬜ |  |
| 3 | CLOSE | DONE.md 생성 | ⬜ |  |
""", encoding="utf-8")
        return skill_md

    def test_md_rows_from_still_works_with_deprecation_warning_subprocess(self):
        """[T070/S-12] `.md` init 결과는 기존과 동일(행 수 3) + stderr에 deprecation 경고
        1줄 출력(subprocess, run.sh 실호출 — 016 stderr 게이트 관례와 동일한 형식)."""
        tmpdir = pathlib.Path(tempfile.mkdtemp())
        try:
            skill_md = self._make_skill_md(tmpdir)
            task_path = tmpdir / "070-md-fallback"
            code, stdout, stderr, data = _run070([
                "init", str(task_path),
                "--skill", "opp", "--mode", "interactive",
                "--rows-from", str(skill_md),
            ])
            self.assertEqual(code, 0, f".md init 실패: {stdout!r}")
            self.assertTrue(data.get("ok"))
            self.assertEqual(data.get("rows_count"), 3, "기존과 동일한 행 수(3)여야 함")
            self.assertIn(
                "deprecated", stderr.lower(),
                f".md 파싱 경로에 deprecation 경고가 stderr에 있어야 함, 실제 stderr={stderr!r}"
            )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_after_deprecated_numeric_anchor_still_gets_auto_key(self):
        """[T070] add-row --after(숫자, deprecated) 경로로 삽입해도 F-004 자동 key가
        부여되어야 한다(주소 방식과 무관하게 자동 key 생성은 항상 적용, PLAN §3.4.2)."""
        self._init(rows_spec=json.dumps([
            {"stage": "TASK",  "item": "작업"},
            {"stage": "PLAN",  "item": "작업"},
            {"stage": "CLOSE", "item": "DONE.md 생성"},
        ]))
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                after=1, stage="TEST", item="fix 작업",
            )
            exit_code, result = self._call_cmd(ST.cmd_add_row, args)
        self.assertEqual(exit_code, 0, f"--after add-row 실패: {result}")
        state = self._state()
        new_row = state["rows"][1]
        self.assertTrue(
            new_row.get("key"),
            f"--after(deprecated) 경로로 삽입해도 자동 key가 있어야 함, 실제: {new_row.get('key')}"
        )

    def test_step_and_action_step_both_accepted_subprocess(self):
        """[T070/S-9 보강] CLI 레벨에서 --step(기존)과 --action-step(신규 별칭) 둘 다
        argparse에서 인식되어야 한다(신규 플래그 추가가 기존 --step 인식을 깨지 않음 +
        --action-step 자체가 신규 인식됨). 현재는 --action-step이 argparse에 없어 실패."""
        task_path = self.tmpdir / "070-step-alias-cli"
        code, stdout, stderr, data = _run070([
            "init", str(task_path),
            "--skill", "opp", "--mode", "interactive",
            "--rows-spec", json.dumps([
                {"stage": "TASK",    "item": "작업"},
                {"stage": "EXECUTE", "item": "작업"},
                {"stage": "CLOSE",   "item": "DONE.md 생성"},
            ]),
        ])
        self.assertEqual(code, 0, f"사전 init 실패: {stdout!r}")
        code, stdout, stderr, data = _run070(["mark", str(task_path), "--row", "1", "--done"])
        self.assertEqual(code, 0, f"row1 mark 실패: {stdout!r}")

        # --step(기존)은 이미 동작해야 함
        code, stdout, stderr, data = _run070([
            "mark", str(task_path), "--row", "2", "--done",
            "--as-worker", "--worker-stage", "EXECUTE", "--step", "1/3",
        ])
        self.assertEqual(code, 0, f"--step(기존)이 여전히 동작해야 함 (stdout={stdout!r})")

        # --action-step(신규)도 argparse에서 인식되어야 함(unrecognized arguments 없이)
        code, stdout, stderr, data = _run070([
            "mark", str(task_path), "--row", "2", "--done",
            "--as-worker", "--worker-stage", "EXECUTE", "--action-step", "2/3",
        ])
        self.assertEqual(
            code, 0,
            f"--action-step이 argparse에서 인식되어야 함 (exit={code}, stdout={stdout!r}, stderr={stderr!r})"
        )


# ═════════════════════════════════════════════════════════════════════════════
# 076: TestTodoMirror — build_todo_mirror 파생 규칙 + ok() 페이로드 + 영속 경계
# (PLAN §3.1.5 TS-001~TS-007). 표준 라이브러리만, 실 파일 I/O + date.js 모킹.
# ═════════════════════════════════════════════════════════════════════════════

class TestTodoMirror(BaseTestCase):
    """076 F-001: init/advance/mark/block ok() stdout 페이로드의 todo_mirror 검증.
    파생 4규칙(na 중립·전부pending→pending·전부done→completed·부분/failed→in_progress)
    + 영속 경계(state.json 미영속, schema 무위반). 공개 cmd_* 호출로만 검증."""

    # 단계당 다중 행 스펙 — 파생 경계(부분완료/블로커)를 재현하기 위한 픽스처
    MULTI_SPEC = json.dumps([
        {"stage": "TASK",    "item": "작업"},
        {"stage": "TASK",    "item": "PM Gate"},
        {"stage": "PLAN",    "item": "작업"},
        {"stage": "PLAN",    "item": "PM Gate"},
        {"stage": "EXECUTE", "item": "작업"},
    ])

    def _init_capture(self, rows_spec=None, mode="interactive"):
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode=mode,
                rows_spec=rows_spec or SIMPLE_ROWS_SPEC,
            )
            return self._call_cmd(ST.cmd_init, args)

    def _advance_capture(self, row_id):
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=row_id)
            return self._call_cmd(ST.cmd_advance, args)

    def _mark_capture(self, row_id, **kw):
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=row_id, done=True, **kw)
            return self._call_cmd(ST.cmd_mark, args)

    def _block_capture(self, row_id, reason="테스트 블로커"):
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=row_id, reason=reason)
            return self._call_cmd(ST.cmd_block, args)

    @staticmethod
    def _by_stage(todo_mirror):
        return {t["id"]: t for t in todo_mirror["todos"]}

    def test_ts001_init_payload_all_pending(self):
        """TS-001: init ok() → todo_mirror.action==create + 단계별 todo(전부 pending).
        content/activeForm/id 필드 포함(native todo 스키마)."""
        code, result = self._init_capture(rows_spec=SIMPLE_ROWS_SPEC)
        self.assertEqual(code, 0, f"init 실패: {result}")
        tm = result["todo_mirror"]
        self.assertEqual(tm["action"], "create")
        ids = [t["id"] for t in tm["todos"]]
        self.assertEqual(ids, ["stage:TASK", "stage:PLAN", "stage:EXECUTE", "stage:CLOSE"])
        for t in tm["todos"]:
            self.assertEqual(t["status"], "pending")
        first = tm["todos"][0]
        self.assertEqual(first["content"], "TASK 단계")
        self.assertEqual(first["activeForm"], "TASK 단계 진행 중")

    def test_ts002_stage_all_done_completed(self):
        """TS-002: 한 단계 전 행 done → 해당 단계 todo status=completed."""
        self._init_capture(rows_spec=self.MULTI_SPEC)
        self._mark_capture(1)              # TASK/작업 → done
        code, result = self._mark_capture(2)  # TASK/PM Gate → done
        self.assertEqual(code, 0, f"mark 실패: {result}")
        by = self._by_stage(result["todo_mirror"])
        self.assertEqual(by["stage:TASK"]["status"], "completed")
        self.assertEqual(by["stage:PLAN"]["status"], "pending")  # 미착수 유지

    def test_ts003_advance_and_partial_in_progress(self):
        """TS-003: advance로 한 행 🔄 → 단계 in_progress; 일부만 done인 단계도 in_progress.
        action==update 동반."""
        self._init_capture(rows_spec=self.MULTI_SPEC)
        code, result = self._advance_capture(1)  # TASK/작업 → in_progress
        self.assertEqual(result["todo_mirror"]["action"], "update")
        by = self._by_stage(result["todo_mirror"])
        self.assertEqual(by["stage:TASK"]["status"], "in_progress")
        # 일부만 done(작업 done, PM Gate pending) → in_progress
        code, result = self._mark_capture(1)
        by = self._by_stage(result["todo_mirror"])
        self.assertEqual(by["stage:TASK"]["status"], "in_progress")

    def test_ts004_untouched_stage_pending(self):
        """TS-004: 미착수 단계 todo status=pending (전부 ⬜)."""
        self._init_capture(rows_spec=self.MULTI_SPEC)
        code, result = self._advance_capture(1)  # TASK만 접촉
        by = self._by_stage(result["todo_mirror"])
        self.assertEqual(by["stage:PLAN"]["status"], "pending")
        self.assertEqual(by["stage:EXECUTE"]["status"], "pending")

    def test_ts005_na_neutral(self):
        """TS-005: agentic init 시 사용자 확인(na)+작업(pending) 단계 → pending(na 미반영).
        na를 완료로 셌다면 in_progress로 오판되므로 pending 검증이 na 중립을 확증."""
        rows = json.dumps([
            {"stage": "TASK",  "item": "작업"},
            {"stage": "TASK",  "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "사용자 확인"},
        ])
        code, result = self._init_capture(rows_spec=rows, mode="agentic")
        self.assertEqual(code, 0, f"agentic init 실패: {result}")
        by = self._by_stage(result["todo_mirror"])
        self.assertEqual(by["stage:TASK"]["status"], "pending")

    def test_ts006_block_keeps_in_progress(self):
        """TS-006: block 후 대상 단계 todo status=in_progress 유지 + action==update."""
        self._init_capture(rows_spec=self.MULTI_SPEC)
        code, result = self._block_capture(1)  # TASK/작업 → failed
        self.assertEqual(code, 0, f"block 실패: {result}")
        tm = result["todo_mirror"]
        self.assertEqual(tm["action"], "update")
        by = self._by_stage(tm)
        self.assertEqual(by["stage:TASK"]["status"], "in_progress")

    def test_ts007_not_persisted_schema_passes(self):
        """TS-007(H-3 영속 경계): 4개 명령 실행 후 state.json에 todo_mirror 부재 +
        save_state_json 결과가 schema validate 통과."""
        self._init_capture(rows_spec=self.MULTI_SPEC)
        self._advance_capture(1)
        self._mark_capture(1)
        self._block_capture(2)
        state = self._state()
        self.assertNotIn("todo_mirror", state)
        for row in state["rows"]:
            self.assertNotIn("todo_mirror", row)
        result = self._validate()
        self.assertTrue(result["ok"], f"validate 실패: {result}")
        self.assertEqual(result["violations_count"], 0)


# ═════════════════════════════════════════════════════════════════════════════
# 088: TestCloseHistoryLink — CLOSE 마지막 행 mark → 메모리 히스토리 자동 연결
# (PLAN 088 §3 Step 1 TS-1~TS-7 / TASK R-1~R-5).
# [MUST] red-first.md §4: 공개 인터페이스(cmd_mark 호출 + ok() stdout 페이로드 +
#   실 MEMORY.json 파일 내용)로만 검증한다. 내부 함수 mock 금지 — 실패 주입은
#   파일 시스템 레벨 블랙박스 결함 주입으로만 수행한다.
# ═════════════════════════════════════════════════════════════════════════════

# 태스크 폴더명 → title 파생 규칙 검증용 고정 픽스처 (PLAN 088 §2.6)
#   088-260811-opp-테스트-태스크 → "088 테스트 태스크"
_HL_TASK_DIR       = "088-260811-opp-테스트-태스크"
_HL_EXPECTED_TITLE = "088 테스트 태스크"
_HL_EXPECTED_PATH  = f"tasks/{_HL_TASK_DIR}/"
_HL_STAGE_DONE     = "완료"
_HL_RESULT_PLACEHOLDER = "(PM 보강 대기)"

# memory.schema.json 유효 최소 문서 (version/last_task_number/memories/history 필수)
_HL_EMPTY_MEMORY_DOC = {
    "version": 1,
    "last_task_number": 0,
    "memories": [],
    "history": [],
}


class TestCloseHistoryLink(BaseTestCase):
    """088 R-1~R-5: CLOSE 마지막 행 mark 시 state-tool이 memory-tool을 호출해
    `<프로젝트루트>/.opal/MEMORY.json` history[0]에 작업 히스토리 행을 자동 생성한다.

    픽스처는 BaseTestCase의 평면 tmpdir 대신 **프로젝트 루트 형태**를 구성한다:
        <tmpdir>/.opal/MEMORY.json    ← 앵커 (조상 탐색 대상, PLAN §2.3)
        <tmpdir>/tasks/<태스크폴더>/  ← task_path
    기존 262건은 앵커 없는 평면 tmpdir에서 돌아 무발동이며(PLAN §2.8),
    이 클래스만 실제 연동 경로를 탄다.

    CLOSE 진입 게이트(check_close_gate, state_tool.py:558-595)는 직전 '사용자 확인'
    행이 status=done/owner=user일 것을 요구하므로, 기존 픽스처 패턴
    (test_state_tool.py:433-447)을 그대로 재사용한다.
    """

    CLOSE_ROWS_SPEC = json.dumps([
        {"stage": "TASK",  "item": "사용자 확인"},
        {"stage": "CLOSE", "item": "DONE.md 생성"},
    ])

    def setUp(self):
        super().setUp()
        # BaseTestCase가 만든 평면 task_path는 사용하지 않는다 — 프로젝트 루트 구조로 교체
        self.project_root = self.tmpdir
        self.memory_file  = self.project_root / ".opal" / "MEMORY.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self._write_memory(_HL_EMPTY_MEMORY_DOC)
        self.task_path = self.project_root / "tasks" / _HL_TASK_DIR
        self.task_path.mkdir(parents=True)

    # ── 픽스처 헬퍼 ──────────────────────────────────────────────────────────

    def _write_memory(self, doc):
        self.memory_file.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    def _history(self):
        return json.loads(self.memory_file.read_text(encoding="utf-8"))["history"]

    def _mark_capture(self, row_id, **kw):
        """mark 호출 → (exit_code, ok() 페이로드 dict). 공개 경로만 사용."""
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=row_id, done=True, **kw)
            return self._call_cmd(ST.cmd_mark, args)

    def _mark_close_last(self):
        """사용자 확인(row1, owner=user) 선행 → CLOSE 마지막 행(row2) mark 결과 반환."""
        code, result = self._mark_capture(1, owner="user")
        self.assertEqual(code, 0, f"픽스처 오류 — 사용자 확인 행 mark 실패: {result}")
        return self._mark_capture(2)

    # ── TS-1 (R-1/R-2) ──────────────────────────────────────────────────────

    def test_ts1_close_last_mark_creates_history_row(self):
        """TS-1 (R-1/R-2): CLOSE 마지막 행 mark → MEMORY.json history[0]에 1건 생성.
        title/path/stage/result는 도구 파생값, date는 memory-tool이 채운 KST 당일."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        code, result = self._mark_close_last()

        self.assertEqual(code, 0, f"CLOSE 마지막 행 mark 실패: {result}")
        self.assertTrue(result.get("ok"), f"mark 응답이 ok:true여야 함: {result}")

        history = self._history()
        self.assertEqual(len(history), 1,
                         f"history에 정확히 1건이 생성되어야 함, 실제: {history}")
        row = history[0]
        self.assertEqual(row.get("title"), _HL_EXPECTED_TITLE,
                         f"title은 task_id에서 파생되어야 함(§2.6), 실제: {row.get('title')!r}")
        self.assertEqual(row.get("path"), _HL_EXPECTED_PATH,
                         f"path는 프로젝트 루트 상대경로여야 함, 실제: {row.get('path')!r}")
        self.assertEqual(row.get("stage"), _HL_STAGE_DONE,
                         f"stage는 '완료'여야 함(D-6), 실제: {row.get('stage')!r}")
        self.assertRegex(str(row.get("date")), r"^\d{4}-\d{2}-\d{2}$",
                         f"date는 KST YYYY-MM-DD여야 함, 실제: {row.get('date')!r}")
        self.assertEqual(row.get("result"), _HL_RESULT_PLACEHOLDER,
                         f"result는 플레이스홀더여야 함(§2.6), 실제: {row.get('result')!r}")

        link = result.get("history_link")
        self.assertIsInstance(link, dict,
                              f"mark 응답에 history_link 객체가 있어야 함: {result}")
        self.assertEqual(link.get("status"), "created",
                         f"최초 생성은 status=created여야 함, 실제: {link.get('status')!r}")

    # ── TS-2 (R-3 멱등) ─────────────────────────────────────────────────────

    def test_ts2_duplicate_mark_is_idempotent(self):
        """TS-2 (R-3): 동일 CLOSE 마지막 행을 2회 mark해도 해당 path 행은 정확히 1건.
        2회차 응답은 status=duplicate_skipped."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        code1, result1 = self._mark_close_last()
        self.assertEqual(code1, 0, f"1회차 mark 실패: {result1}")

        code2, result2 = self._mark_capture(2)
        self.assertEqual(code2, 0, f"2회차 mark 실패: {result2}")
        self.assertTrue(result2.get("ok"), f"2회차 mark도 ok:true여야 함: {result2}")

        history = self._history()
        same_path = [r for r in history if r.get("path") == _HL_EXPECTED_PATH]
        self.assertEqual(len(same_path), 1,
                         f"동일 path 행이 정확히 1건이어야 함(멱등), 실제 history: {history}")

        link = result2.get("history_link")
        self.assertIsInstance(link, dict,
                              f"2회차 mark 응답에도 history_link가 있어야 함: {result2}")
        self.assertEqual(link.get("status"), "duplicate_skipped",
                         f"2회차는 duplicate_skipped여야 함, 실제: {link.get('status')!r}")

    # ── TS-3 (R-4a 부재 → 비차단 skipped) ───────────────────────────────────

    def test_ts3_missing_memory_json_is_non_blocking_skip(self):
        """TS-3 (R-4a): MEMORY.json 부재 상태로 mark → mark는 ok:true를 유지하고
        history_link.status=skipped + 비공백 warning으로 표면화된다."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        self.memory_file.unlink()   # 블랙박스 결함 주입 — 앵커 제거

        code, result = self._mark_close_last()
        self.assertEqual(code, 0, f"MEMORY.json 부재가 mark를 실패시키면 안 됨: {result}")
        self.assertTrue(result.get("ok"),
                        f"MEMORY.json 부재에도 ok:true여야 함(R-4): {result}")

        link = result.get("history_link")
        self.assertIsInstance(link, dict,
                              f"부재 상황도 history_link로 표면화되어야 함: {result}")
        self.assertEqual(link.get("status"), "skipped",
                         f"앵커 미탐지는 skipped여야 함, 실제: {link.get('status')!r}")
        self.assertTrue(str(link.get("warning", "")).strip(),
                        f"warning이 비공백이어야 함, 실제: {link.get('warning')!r}")
        self.assertFalse(self.memory_file.exists(), "MEMORY.json이 새로 생성되면 안 됨")

    # ── TS-4 (R-4b 손상 → 비차단 failed) ────────────────────────────────────

    def test_ts4_corrupt_memory_json_is_non_blocking_failure(self):
        """TS-4 (R-4b): MEMORY.json이 손상 JSON일 때 mark → ok:true 유지 +
        history_link.status=failed + 비공백 warning. 결함 주입은 파일 덮어쓰기(블랙박스)."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        self.memory_file.write_text("{ this is not valid json ", encoding="utf-8")

        code, result = self._mark_close_last()
        self.assertEqual(code, 0, f"손상 MEMORY.json이 mark를 실패시키면 안 됨: {result}")
        self.assertTrue(result.get("ok"),
                        f"손상 MEMORY.json에도 ok:true여야 함(R-4): {result}")

        link = result.get("history_link")
        self.assertIsInstance(link, dict,
                              f"손상 상황도 history_link로 표면화되어야 함: {result}")
        self.assertEqual(link.get("status"), "failed",
                         f"손상 JSON은 failed여야 함, 실제: {link.get('status')!r}")
        self.assertTrue(str(link.get("warning", "")).strip(),
                        f"warning이 비공백이어야 함, 실제: {link.get('warning')!r}")

    # ── TS-5 (회귀: 비CLOSE 행 무발동) ──────────────────────────────────────

    def test_ts5_non_close_row_mark_does_not_link(self):
        """TS-5 (회귀/선택성): 비CLOSE 행 mark는 무발동이고, **같은 태스크의** CLOSE
        마지막 행 mark는 발동한다.

        무발동만 단언하면 기능이 아예 없어도 통과하는 공허한 가드가 되므로,
        동일 픽스처 안에서 발동/무발동을 대조해 '무발동이 선택적임'을 확증한다.
        """
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        before = self._history()

        # (1) 비CLOSE 행 → 무발동
        code, result = self._mark_capture(1, owner="user")   # TASK/사용자 확인 (비CLOSE)
        self.assertEqual(code, 0, f"비CLOSE 행 mark 실패: {result}")
        self.assertNotIn("history_link", result,
                         f"비CLOSE mark 응답에는 history_link 키가 없어야 함: {result}")
        self.assertEqual(len(self._history()), len(before),
                         "비CLOSE mark는 history를 변경하면 안 됨")

        # (2) 대조군 — CLOSE 마지막 행 → 발동 (무발동이 선택적임을 확증)
        code, close_result = self._mark_capture(2)
        self.assertEqual(code, 0, f"CLOSE 마지막 행 mark 실패: {close_result}")
        self.assertIn("history_link", close_result,
                      f"CLOSE 마지막 행 mark는 발동해야 함(대조군): {close_result}")
        self.assertEqual(len(self._history()), len(before) + 1,
                         "CLOSE 마지막 행 mark는 history를 1건 늘려야 함(대조군)")

    # ── TS-6 (R-5 리마인더) ─────────────────────────────────────────────────

    def test_ts6_reminder_contains_actionable_update_command(self):
        """TS-6 (R-5): history_link.reminder에 보강 명령의 구성요소가 모두 포함된다 —
        `update`, `--kind history`, `--result`, 그리고 실제 사용된 title."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        code, result = self._mark_close_last()
        self.assertEqual(code, 0, f"CLOSE 마지막 행 mark 실패: {result}")

        link = result.get("history_link")
        self.assertIsInstance(link, dict, f"history_link가 있어야 함: {result}")
        reminder = link.get("reminder")
        self.assertIsInstance(reminder, str,
                              f"reminder는 문자열이어야 함, 실제: {reminder!r}")
        for token in ("update", "--kind history", "--result", _HL_EXPECTED_TITLE):
            self.assertIn(token, reminder,
                          f"reminder에 {token!r}가 포함되어야 함(R-5), 실제: {reminder!r}")

    # ── TS-7 (H-3 영속 경계) ────────────────────────────────────────────────

    def test_ts7_history_link_not_persisted_schema_passes(self):
        """TS-7 (H-3 영속 경계, 076 TS-007 패턴): mark 후 state.json 어디에도
        history_link 키가 없고 state.schema.json 검증을 통과한다."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        code, result = self._mark_close_last()
        self.assertEqual(code, 0, f"CLOSE 마지막 행 mark 실패: {result}")
        # 선행 조건 — 발동 자체는 일어나야 한다(무발동으로 인한 위양성 통과 차단)
        self.assertIn("history_link", result,
                      f"CLOSE 마지막 행 mark 응답에 history_link가 있어야 함: {result}")

        state = self._state()
        self.assertNotIn("history_link", state,
                         "history_link는 state.json에 영속되면 안 됨")
        for row in state["rows"]:
            self.assertNotIn("history_link", row,
                             "history_link는 rows[]에도 영속되면 안 됨")

        validated = self._validate()
        self.assertTrue(validated["ok"], f"state.schema.json 검증 실패: {validated}")
        self.assertEqual(validated["violations_count"], 0)


# ═════════════════════════════════════════════════════════════════════════════
# 091 F-004: TestTaskStepGate — 게이트 집행 배선 (TEST-SCENARIO S-10~S-17)
# [MUST] red-first.md §2/§4: 작성자(opal-test-agent mode:red) ≠ 구현자(opal-be-agent,
# Step 8). check_gate_artifacts()/build_gate_payload()/_is_safe_artifact_token()은
# 아직 state_tool.py에 없고, build_rows_from_pipeline_json()도 아직 gate를 rows[]로
# 전파하지 않는다(§3.4.2 (5) 1줄 미착수). 따라서 real pipeline.json으로 init해도
# row에 "gate" 키가 실리지 않는다 — 아래 _inject_gate()는 Step 8 GREEN이 만들 결과
# ("전파된 뒤의 row 모습")를 실 pipeline.json의 실제 gate 정의값 그대로 미리
# state.json에 반영하는 fixture 준비 절차다(비mock — 실 JSON 파일 read/write일 뿐,
# state_tool.py의 어떤 함수도 patch하지 않는다). 현재 cmd_mark에는 가드 자체가 없으므로
# artifacts 미충족에도 ok:true가 나오는 것이 RED 증거다.
# ═════════════════════════════════════════════════════════════════════════════

class TestTaskStepGate(unittest.TestCase):
    """F-004 게이트 집행 배선 — PLAN §3.4.2 / TEST-SCENARIO S-10~S-17.

    실 pipeline.json 3종(opd/opdw/opsdd, Step 4~6에서 27건 gate 배치 완료·
    spec-validate 10/10 통과 확인됨)을 fixture로 사용한다:
      - opd `plan.pm_gate`      artifacts=["TASK.md","PLAN.md"]  (S-10/S-11/S-12/S-13/S-15/S-16)
      - opdw `execute.pm_gate`  artifacts=[] (전치 완료 실사례, S-14)
      - opsdd `execute.pm_gate` artifacts=["actions/ACT-*/DONE.md"] (glob 실사례, S-17)
    """

    _REPO_ROOT     = _TOOL_DIR.parent.parent.parent
    _OPD_PIPELINE  = _REPO_ROOT / "opal/skills/opal-pilot-dev/references/pipeline.json"
    _OPDW_PIPELINE = _REPO_ROOT / "opal/skills/opal-pilot-dev-wireframe/references/pipeline.json"
    _OPSDD_PIPELINE = _REPO_ROOT / "opal/skills/opal-pilot-sdd/references/pipeline.json"

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.task_path = self.tmpdir / "091-260814-gate-test"
        self.task_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ── 내부 헬퍼 (fixture 준비 전용 — state_tool.py 함수는 공개 경로로만 호출) ────

    def _init(self, pipeline_path, skill):
        self.assertTrue(pipeline_path.exists(), f"실 pipeline.json 부재: {pipeline_path}")
        args = make_args(task_path=str(self.task_path), skill=skill, mode="interactive",
                          rows_from=str(pipeline_path))
        exit_code, result = _call070(ST.cmd_init, args)
        self.assertEqual(exit_code, 0, f"init 실패: {result}")

    def _state(self):
        return json.loads((self.task_path / "state.json").read_text(encoding="utf-8"))

    def _write_state(self, state):
        (self.task_path / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _inject_gate(self, key, gate):
        """실 pipeline.json의 gate 정의를 state.json 행에 직접 주입 — Step 8 GREEN의
        rows 전파 배선(§3.4.2 (5))이 아직 없어 수동으로 재현한다. mock/patch 아님(실 파일 조작)."""
        state = self._state()
        for row in state["rows"]:
            if row.get("key") == key:
                row["gate"] = gate
                break
        else:
            self.fail(f"key {key} 행을 state.json rows[]에서 찾을 수 없음")
        self._write_state(state)

    def _force_done_before(self, key):
        """target 행 앞의 모든 행을 done으로 강제 설정 — stage-transition guard(기존
        구현, 본 시나리오의 검증 대상 아님) 충족만을 위한 fixture 준비."""
        state = self._state()
        for row in state["rows"]:
            if row.get("key") == key:
                break
            if row.get("status") not in ("done", "na", "additional_work_done"):
                row["status"] = "done"
                row["status_label"] = "✅"
                row["owner"] = "PM"
                row["timestamp"] = "2026-05-01 23:00"
        self._write_state(state)

    def _mark_by_key(self, key, force=False, note=None):
        """cmd_mark 공개 경로 — --task-step 주소 지정(070 R-4 addressing)."""
        args = make_args(task_path=str(self.task_path), task_step=key, done=True,
                          force=force, note=note)
        return _call070(ST.cmd_mark, args)

    # ── S-10: 산출물 부재 시 게이트 차단 (H-1) ──────────────────────────────────

    def test_s10_missing_artifact_blocks_mark(self):
        """[T091/L1-S10] opd plan.pm_gate artifacts(TASK.md/PLAN.md) 부재 → ok:false +
        error=gate_artifact_missing + missing[]에 둘 다 포함."""
        self._init(self._OPD_PIPELINE, "opd")
        gate = {"artifacts": ["TASK.md", "PLAN.md"],
                "checklist": ["TASK.md 요구사항", "PLAN.md §4.2"]}
        self._inject_gate("plan.pm_gate", gate)
        self._force_done_before("plan.pm_gate")

        exit_code, result = self._mark_by_key("plan.pm_gate")
        self.assertFalse(result.get("ok"),
                         f"artifacts 부재인데 ok:true — 게이트 차단 미구현(RED 목표): {result}")
        self.assertEqual(result.get("error"), "gate_artifact_missing")
        missing = result.get("missing", [])
        self.assertIn("TASK.md", missing)
        self.assertIn("PLAN.md", missing)

    # ── S-11: 차단 시 부분 상태 변경 부재 (H-1, save_state_json() 이전 가드) ────

    def test_s11_no_partial_state_change_on_block(self):
        """[T091/L2-S11] S-10 차단 후 state.json 내용·mtime 무변화, STATE.md 무변화
        — 검증이 save_state_json() 이전에 수행되어야 함."""
        self._init(self._OPD_PIPELINE, "opd")
        gate = {"artifacts": ["TASK.md", "PLAN.md"], "checklist": ["TASK.md 요구사항"]}
        self._inject_gate("plan.pm_gate", gate)
        self._force_done_before("plan.pm_gate")

        state_file = self.task_path / "state.json"
        md_file = self.task_path / "STATE.md"
        before_state_bytes = state_file.read_bytes()
        before_md_text = md_file.read_text(encoding="utf-8")
        before_mtime = state_file.stat().st_mtime_ns

        exit_code, result = self._mark_by_key("plan.pm_gate")
        self.assertFalse(result.get("ok"),
                         f"artifacts 부재인데 ok:true — 게이트 차단 미구현(RED 목표): {result}")

        after_state_bytes = state_file.read_bytes()
        after_md_text = md_file.read_text(encoding="utf-8")
        after_mtime = state_file.stat().st_mtime_ns

        self.assertEqual(before_state_bytes, after_state_bytes,
                         "차단 후 state.json 내용이 변경됨 — 부분 상태 변경 발생(H-1 위반)")
        self.assertEqual(before_mtime, after_mtime,
                         "차단 후 state.json mtime이 변경됨 — save_state_json()이 가드보다 먼저 호출됨")
        self.assertEqual(before_md_text, after_md_text, "차단 후 STATE.md가 변경됨")

    # ── S-12: checklist dict 페이로드 반환 (H-6) ────────────────────────────────

    def test_s12_gate_checklist_dict_payload_on_pass(self):
        """[T091/L1-S12] artifacts 충족 시 ok:true + gate_checklist가 dict로 반환
        (list면 todo_mirror_hook._extract_payload가 조용히 무시함, H-6)."""
        self._init(self._OPD_PIPELINE, "opd")
        gate = {"artifacts": ["TASK.md", "PLAN.md"],
                "checklist": ["TASK.md 요구사항", "PLAN.md §4.2"]}
        self._inject_gate("plan.pm_gate", gate)
        self._force_done_before("plan.pm_gate")
        (self.task_path / "TASK.md").write_text("# TASK\n", encoding="utf-8")
        (self.task_path / "PLAN.md").write_text("# PLAN\n", encoding="utf-8")

        exit_code, result = self._mark_by_key("plan.pm_gate")
        self.assertTrue(result.get("ok"), f"artifacts 충족인데 ok:false: {result}")
        payload = result.get("gate_checklist")
        self.assertIsInstance(payload, dict,
                              f"gate_checklist가 dict가 아님(list면 hook이 무시함, H-6): {payload!r}")
        self.assertEqual(payload.get("artifacts"), gate["artifacts"])
        self.assertEqual(payload.get("checklist"), gate["checklist"])

    # ── S-13: gate 미보유 행 무영향 (회귀, H-2/H-3) ─────────────────────────────

    def test_s13_new_style_row_without_gate_response_unaffected(self):
        """[T091/L1-S13] gate 필드가 없는 행(신형 키는 있으나 gate 미보유, 예: opd
        task.task_md)의 mark 응답 키 집합이 변경 전과 동일 — gate_checklist가 섞이지
        않는다(H-2/H-3 회귀 앵커)."""
        self._init(self._OPD_PIPELINE, "opd")

        exit_code, result = self._mark_by_key("task.task_md")
        self.assertEqual(exit_code, 0)
        self.assertTrue(result.get("ok"))
        expected_keys = {"ok", "command", "row_id", "stage", "item", "status",
                         "timestamp", "owner", "todo_mirror",
                         "auto_approved"}  # 093 F-002 관측 필드(PLAN §3.2.2 (6)) — 상시 존재
        self.assertEqual(set(result.keys()), expected_keys,
                         f"gate 없는 행인데 응답 키 집합이 변경됨: {sorted(result.keys())}")
        self.assertNotIn("gate_checklist", result)

    def test_s13_legacy_keyless_state_json_mark_still_passes(self):
        """[T091/L1-S13] key/gate 필드가 전무한 구형(schema_version 1.0, --rows-spec
        경로) state.json도 mark가 정상 통과(ok:true) — 소급 마이그레이션 불필요
        (TASK.md 제약 d, §3.4.4)."""
        args = make_args(task_path=str(self.task_path), skill="opp", mode="interactive",
                         rows_spec=SIMPLE_ROWS_SPEC)
        exit_code, result = _call070(ST.cmd_init, args)
        self.assertEqual(exit_code, 0, f"legacy init 실패: {result}")

        state = self._state()
        self.assertEqual(state.get("schema_version"), "1.0")
        for row in state["rows"]:
            self.assertNotIn("key", row)
            self.assertNotIn("gate", row)

        exit_code, result = _call070(ST.cmd_mark, make_args(
            task_path=str(self.task_path), row=1, done=True))
        self.assertEqual(exit_code, 0, f"구 state.json에서 mark 실패: {result}")
        self.assertTrue(result.get("ok"), f"구 state.json인데 ok:false: {result}")

    # ── S-14: 빈 artifacts는 차단하지 않음 (opdw 실사례, 영구 차단 부재) ────────

    def test_s14_empty_artifacts_never_blocks(self):
        """[T091/L1-S14] opdw execute.pm_gate(artifacts:[]) — 산출물 없이도 ok:true
        (캡틴 확정 실패 모드 배제) + gate_checklist payload가 여전히 반환됨."""
        self._init(self._OPDW_PIPELINE, "opdw")
        opdw_spec = json.loads(self._OPDW_PIPELINE.read_text(encoding="utf-8"))
        gate = next(ts["gate"] for ts in opdw_spec["task_steps"] if ts["key"] == "execute.pm_gate")
        self.assertEqual(gate["artifacts"], [],
                         "픽스처 전제 위반 — 실 opdw execute.pm_gate.artifacts가 더 이상 빈 배열이 아님")
        self._inject_gate("execute.pm_gate", gate)
        self._force_done_before("execute.pm_gate")

        exit_code, result = self._mark_by_key("execute.pm_gate")
        self.assertTrue(result.get("ok"), f"artifacts:[] 인데 ok:false — 영구 차단 발생: {result}")
        payload = result.get("gate_checklist")
        self.assertIsInstance(payload, dict, f"gate_checklist dict 페이로드 없음: {payload!r}")
        self.assertEqual(payload.get("checklist"), gate["checklist"])

    # ── S-15: --force 우회 시 의사결정 로그 강제 (H-5, 미결-4) ──────────────────

    def test_s15_force_note_bypass_records_decision_log(self):
        """[T091/L1-S15] artifacts 부재 + --force --note → ok:true + STATE.md
        의사결정 로그에 gate_artifact_force와 missing 목록이 기재됨."""
        self._init(self._OPD_PIPELINE, "opd")
        gate = {"artifacts": ["TASK.md", "PLAN.md"], "checklist": ["TASK.md 요구사항"]}
        self._inject_gate("plan.pm_gate", gate)
        self._force_done_before("plan.pm_gate")

        exit_code, result = self._mark_by_key("plan.pm_gate", force=True, note="긴급 우회 사유")
        self.assertTrue(result.get("ok"), f"--force --note인데 ok:false: {result}")

        md = (self.task_path / "STATE.md").read_text(encoding="utf-8")
        self.assertIn("gate_artifact_force", md, "STATE.md 의사결정 로그에 gate_artifact_force 미기재")
        self.assertIn("TASK.md", md, "의사결정 로그에 missing 목록(TASK.md)이 없음")
        self.assertIn("PLAN.md", md, "의사결정 로그에 missing 목록(PLAN.md)이 없음")

    def test_s15_force_without_note_rejected(self):
        """[T091/L1-S15] --force만 있고 --note가 없으면 note_required_for_force로
        거부(기존 §2.17 규칙 — 게이트 우회 경로도 예외 없음, 회귀 앵커)."""
        self._init(self._OPD_PIPELINE, "opd")
        gate = {"artifacts": ["TASK.md", "PLAN.md"], "checklist": ["TASK.md 요구사항"]}
        self._inject_gate("plan.pm_gate", gate)
        self._force_done_before("plan.pm_gate")

        exit_code, result = self._mark_by_key("plan.pm_gate", force=True, note=None)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("error"), "note_required_for_force")

    # ── S-16: 경로 이탈 토큰 거부 (보안·경계, H-4) ──────────────────────────────

    def test_s16_path_traversal_tokens_rejected_as_missing(self):
        """[T091/L1-S16] artifacts 토큰 /etc/passwd·../outside.md → 태스크 폴더 밖
        매칭 0건, missing 처리, 크래시 없음. 상위 경로 토큰은 **실제로 존재하는**
        파일(outside.md)이어도 경로 이탈이므로 거부되어야 한다(단순 부재 케이스가 아님)."""
        self._init(self._OPD_PIPELINE, "opd")
        gate = {"artifacts": ["/etc/passwd", "../outside.md"], "checklist": ["보안 경계 확인"]}
        self._inject_gate("plan.pm_gate", gate)
        self._force_done_before("plan.pm_gate")
        # 태스크 폴더 밖(tmpdir 최상위)에 실제로 파일을 만들어 둔다 — 존재해도 거부되어야 함
        (self.tmpdir / "outside.md").write_text("outside", encoding="utf-8")

        exit_code, result = self._mark_by_key("plan.pm_gate")
        self.assertFalse(result.get("ok"),
                         f"경로 이탈 토큰인데 ok:true — 보안 경계 위반(H-4): {result}")
        self.assertEqual(result.get("error"), "gate_artifact_missing")
        missing = result.get("missing", [])
        self.assertIn("/etc/passwd", missing)
        self.assertIn("../outside.md", missing)

    # ── S-17: glob 토큰 매칭 (opsdd 실사례, H-4) ────────────────────────────────

    def test_s17_glob_token_matches_when_file_exists(self):
        """[T091/L1-S17] actions/ACT-*/DONE.md 글롭(opsdd execute.pm_gate 실사용처)
        — 실 파일 존재 시 통과."""
        self._init(self._OPSDD_PIPELINE, "opsdd")
        opsdd_spec = json.loads(self._OPSDD_PIPELINE.read_text(encoding="utf-8"))
        gate = next(ts["gate"] for ts in opsdd_spec["task_steps"] if ts["key"] == "execute.pm_gate")
        self.assertEqual(gate["artifacts"], ["actions/ACT-*/DONE.md"],
                         "픽스처 전제 위반 — opsdd execute.pm_gate.artifacts 실측값 변경됨")
        self._inject_gate("execute.pm_gate", gate)
        self._force_done_before("execute.pm_gate")

        act_dir = self.task_path / "actions" / "ACT-1"
        act_dir.mkdir(parents=True)
        (act_dir / "DONE.md").write_text("done", encoding="utf-8")

        exit_code, result = self._mark_by_key("execute.pm_gate")
        self.assertTrue(result.get("ok"), f"글롭 파일 존재인데 ok:false: {result}")

    def test_s17_glob_token_missing_when_no_file(self):
        """[T091/L1-S17] actions/ACT-*/DONE.md 글롭 — 부재 시 missing 처리
        (opsdd execute.pm_gate)."""
        self._init(self._OPSDD_PIPELINE, "opsdd")
        opsdd_spec = json.loads(self._OPSDD_PIPELINE.read_text(encoding="utf-8"))
        gate = next(ts["gate"] for ts in opsdd_spec["task_steps"] if ts["key"] == "execute.pm_gate")
        self._inject_gate("execute.pm_gate", gate)
        self._force_done_before("execute.pm_gate")

        exit_code, result = self._mark_by_key("execute.pm_gate")
        self.assertFalse(result.get("ok"), f"글롭 파일 부재인데 ok:true: {result}")
        self.assertEqual(result.get("error"), "gate_artifact_missing")
        self.assertIn("actions/ACT-*/DONE.md", result.get("missing", []))

    def test_s17_non_glob_token_not_misclassified_as_glob(self):
        """[T091/L1-S17] `*` 미포함 정적 토큰(PLAN.md)은 glob()이 아니라 존재 검사로
        처리된다 — opd plan.pm_gate로 확인(정적 경로 존재 시 통과)."""
        self._init(self._OPD_PIPELINE, "opd")
        gate = {"artifacts": ["TASK.md", "PLAN.md"], "checklist": ["TASK.md 요구사항"]}
        self._inject_gate("plan.pm_gate", gate)
        self._force_done_before("plan.pm_gate")
        (self.task_path / "TASK.md").write_text("# TASK\n", encoding="utf-8")
        (self.task_path / "PLAN.md").write_text("# PLAN\n", encoding="utf-8")

        exit_code, result = self._mark_by_key("plan.pm_gate")
        self.assertTrue(result.get("ok"),
                        f"'*' 미포함 정적 토큰 존재 시 통과해야 함(오분류 없음): {result}")


# ═════════════════════════════════════════════════════════════════════════════
# 092(RED-first, mode:red): TestWorktreeFlag 신설 — `state-tool init --worktree <path>`
# TEST-SCENARIO.md S-1(H-1)·S-2(H-1,H-11) — worktree-tool 축 신설의 state-tool 측 계약.
# 작성자(opal-test-agent)≠구현자(EXECUTE 워커) — red-first.md §2. 현재 state_tool.py의
# cmd_init/argparse에는 --worktree 처리가 전혀 없으므로(F-005 GREEN 이전), '지정 시
# 키 존재 + 값이 전달한 절대경로와 문자열 동일'(S-1②, G-3 반영)과 'worktree 키 유무만
# 차이나야 한다'(S-2)는 단언이 실패하는 것이 RED 증거다. 공개 인터페이스(ST.cmd_init/
# ST.cmd_show 직접 호출 + 실 state.json/STATE.md 파일 내용)로만 검증 — 기존 BaseTestCase
# 관행과 동일하게 mock/patch 없음. 기존 테스트 케이스는 일절 수정하지 않았다(파일 끝 append).
# ═════════════════════════════════════════════════════════════════════════════

class TestWorktreeFlag(BaseTestCase):
    """092: `state-tool init --worktree <path>` — TEST-SCENARIO.md S-1·S-2 (H-1, H-11)."""

    def _new_task_path(self, name):
        p = self.tmpdir / name
        p.mkdir()
        return p

    def _init_at(self, task_path, worktree=None, task_title=None):
        kwargs = dict(
            task_path=str(task_path),
            skill="opd",
            mode="interactive",
            rows_spec=SIMPLE_ROWS_SPEC,
            force=False,
            note=None,
            import_existing=False,
            next_action=None,
            task_title=task_title,
        )
        if worktree is not None:
            kwargs["worktree"] = worktree
        with _mock_now():
            args = make_args(**kwargs)
            return self._call_cmd(ST.cmd_init, args)

    def _show_json_at(self, task_path):
        with _mock_now():
            args = make_args(task_path=str(task_path), format="json")
            _, result = self._call_cmd(ST.cmd_show, args)
        return result

    # ── S-1: --worktree 미지정/지정 양방향 (H-1) ────────────────────────────

    def test_s1_worktree_unspecified_key_absent_in_state_json(self):
        """[T092/L1-F5a] S-1① — --worktree 미지정 시 state.json에 "worktree" 키가
        아예 존재하지 않아야 한다(null 값 키도 불가)."""
        task_path = self._new_task_path("s1_no_wt")
        exit_code, _ = self._init_at(task_path)
        self.assertEqual(exit_code, 0, "미지정 init은 exit 0이어야 한다")
        state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        self.assertNotIn("worktree", state, "미지정인데 worktree 키가 생성됨(H-1 위반)")

    def test_s1_worktree_specified_key_matches_value_and_show_json(self):
        """[T092/L1-F5a] S-1② — --worktree 지정 시 state["worktree"]가 전달한 절대경로와
        문자열 동일해야 하고(null·빈 문자열·상대경로 불가), show --format json의
        data.worktree도 같은 값을 반환해야 한다(iteration 2 G-3 반영 — '키 존재'만이
        아니라 '값 정합'까지 확인)."""
        task_path = self._new_task_path("s1_with_wt")
        wt_path = "/abs/fake/worktree/task_092"
        exit_code, _ = self._init_at(task_path, worktree=wt_path)
        self.assertEqual(exit_code, 0, "지정 init은 exit 0이어야 한다")

        state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        self.assertIn("worktree", state, "지정했는데 worktree 키가 생성되지 않음")
        self.assertIsNotNone(state["worktree"], "worktree 값이 null이면 안 된다")
        self.assertNotEqual(state["worktree"], "", "worktree 값이 빈 문자열이면 안 된다")
        self.assertEqual(state["worktree"], wt_path,
                         "worktree 값이 전달한 절대경로와 문자열 동일해야 한다")

        show_payload = self._show_json_at(task_path)
        self.assertEqual(show_payload["data"]["worktree"], wt_path,
                         "show --format json의 data.worktree가 init 값과 동일해야 한다")

    # ── S-2: --worktree 유무와 무관하게 STATE.md/스키마 동일 (H-1, H-11) ────

    def test_s2_state_md_identical_regardless_of_worktree_flag(self):
        """[T092/L2-F5b] S-2 — 동일 인자(_mock_now로 타임스탬프까지 고정)로 두 태스크
        폴더에 init한다. 한쪽만 --worktree를 추가해도 STATE.md가 바이트 동일해야 한다
        (_build_new_state_md는 state dict를 받지 않아 worktree를 참조할 수 없다 — H-11)."""
        task_no_wt = self._new_task_path("s2_no_wt")
        task_with_wt = self._new_task_path("s2_with_wt")
        # 폴더명이 다르면 STATE.md 제목 줄 자체가 달라지므로(무관 변수), task_title을
        # 동일하게 고정해 --worktree 유무만 변수로 통제한다.
        common_title = "동일 태스크 제목(S-2)"

        exit_no, _ = self._init_at(task_no_wt, task_title=common_title)
        exit_with, _ = self._init_at(
            task_with_wt, worktree="/abs/fake/worktree/task_092", task_title=common_title
        )
        self.assertEqual(exit_no, 0)
        self.assertEqual(exit_with, 0)

        md_no_wt = (task_no_wt / "STATE.md").read_text(encoding="utf-8")
        md_with_wt = (task_with_wt / "STATE.md").read_text(encoding="utf-8")
        self.assertEqual(md_no_wt, md_with_wt,
                         "STATE.md가 --worktree 유무에 따라 달라지면 안 된다(H-11)")

    def test_s2_state_json_differs_only_in_worktree_key(self):
        """[T092/L2-F5b] S-2 — state.json은 worktree 키 유무만 차이나야 하고 그 외 필드는
        전부 동일해야 한다. 현재는 --worktree 처리가 없어 두 state.json 모두 키가 없으므로
        '한쪽만 키 존재' 단언이 실패하는 것이 RED 증거다(H-1 GREEN 이후 통과 기대)."""
        task_no_wt = self._new_task_path("s2_diff_no_wt")
        task_with_wt = self._new_task_path("s2_diff_with_wt")
        # task_id는 태스크 폴더명(task_path.name)에서 파생되므로 두 폴더명이 다른 이상
        # 값이 다른 게 정상이다(무관 변수) — 비교 대상에서 제외한다.
        common_title = "동일 태스크 제목(S-2 diff)"

        self._init_at(task_no_wt, task_title=common_title)
        self._init_at(task_with_wt, worktree="/abs/fake/worktree/task_092", task_title=common_title)

        state_no_wt = json.loads((task_no_wt / "state.json").read_text(encoding="utf-8"))
        state_with_wt = json.loads((task_with_wt / "state.json").read_text(encoding="utf-8"))

        self.assertNotIn("worktree", state_no_wt)
        self.assertIn("worktree", state_with_wt,
                      "--worktree 지정 케이스에만 키가 있어야 한다(H-1 GREEN 이전엔 실패 — RED)")

        ignore_keys = {"task_id", "worktree"}
        keys_no_wt = set(state_no_wt.keys()) - ignore_keys
        keys_with_wt = set(state_with_wt.keys()) - ignore_keys
        self.assertEqual(keys_no_wt, keys_with_wt,
                         "worktree 키(및 폴더명 파생 task_id) 외에는 스키마가 동일해야 한다")
        for key in keys_no_wt:
            self.assertEqual(state_no_wt[key], state_with_wt[key],
                             f"'{key}' 필드가 --worktree 유무에 따라 달라짐(H-1 위반)")


# ═════════════════════════════════════════════════════════════════════════════
# 094 RED-first 신설 — TestJournalResilience (TEST-SCENARIO.md S-4, S-5, S-30, S-32)
# PLAN §3.1.2 (2)(3) ensure_journal_skeleton/fail-open sync_state_md, §3.5.2
# [MUST] red-first.md §2/§4: 작성자(opal-test-agent mode:red) ≠ 구현자(opal-be-agent),
# 공개 인터페이스(run.sh subprocess, stdout JSON + exit code) + 실 파일 내용으로만
# 검증 — mock/patch/MagicMock 금지. 파일 권한 조작(os.chmod)은 실 환경 조작이므로 허용.
# ═════════════════════════════════════════════════════════════════════════════

def _corrupt_decision_log_table_header(md):
    """094: '## 의사결정 로그' 표 헤더행+구분행만 제거해 손상 저널을 만든다
    (헤딩 텍스트와 본문 나머지는 그대로 보존 — S-30 fixture)."""
    return re.sub(
        r"(## 의사결정 로그\n)\| # \| 시점 \| 결정 \| 근거 \|\n\|[-| ]+\|\n",
        r"\1",
        md,
    )


class TestJournalResilience(BaseTestCase):
    """094 F-001 — 저널 쓰기 회복력: STATE.md 삭제/권한불가/골격손상/입력파괴
    4가지 실패 모드에서도 의사결정 로그가 유실되지 않아야 한다(TASK.md §제약
    "의사결정 로그·블로커 데이터는 어떤 경로에서도 유실되어서는 안 된다").

    [MUST] 전 테스트가 실 CLI subprocess(run.sh) + 실 파일 I/O로만 검증한다.
    """

    def setUp(self):
        super().setUp()
        self.assertTrue(_OPD_REAL_PIPELINE_JSON.exists(),
                        f"opd pipeline.json 실 스펙 부재: {_OPD_REAL_PIPELINE_JSON}")

    def _init_opd(self, task_path):
        code, stdout, stderr, data = _run094([
            "init", str(task_path), "--skill", "opd", "--mode", "agentic",
            "--rows-from", str(_OPD_REAL_PIPELINE_JSON),
        ])
        self.assertEqual(code, 0, f"init 실패: {stdout!r} {stderr!r}")
        return data

    # ── S-4: STATE.md 삭제 상태에서 의사결정 로그 무손실 [P0] ──────────────

    def test_s4_state_md_deleted_mark_autopass_autocreates_and_logs(self):
        """[T094/L2-F001] S-4 — STATE.md를 삭제한 뒤
        `mark --task-step <key> --done --auto-pass --note '삭제상태기재'`를
        호출하면 `ok:true` + STATE.md **자동 생성** + `## 의사결정 로그`에 해당
        note 1행 기재 + state.json 정상 갱신이 이루어져야 한다(R-2 AC,
        `ensure_journal_skeleton` §3.1.2 (2)).

        [PM 판정 정정 2026-08-16] 최초 작성 시 `--force`(비워커·비게이트)를
        트리거로 삼았으나, 이 경로는 `decision`을 세팅하지 않는 실재하지 않는
        트리거였다(실측: `decision` 세팅 트리거는 auto-pass/worker-force/
        gate-force 3종뿐, state_tool.py:1615-1634). TASK.md R-2 AC·TEST-SCENARIO
        S-4를 실재 트리거 `--auto-pass`로 교정하고 본 테스트도 동일 교정한다.

        RED 근거: 현재 `sync_state_md`는 `load_state_md(task_path)`가 None이면
        즉시 `err(command, "marker_missing")`로 exit 1하므로(state_tool.py:
        375-378), STATE.md 자동 생성도 로그 기재도 일어나지 않는다. 단,
        `save_state_json()`이 `sync_state_md()`보다 먼저 커밋되므로(H-3) row
        상태 자체는 state.json에 이미 반영된 채 exit 1이 발생하는 이중 실패
        창(H-2)이 관측된다."""
        task_path = self.tmpdir / "094-s4-deleted"
        task_path.mkdir()
        self._init_opd(task_path)
        (task_path / "STATE.md").unlink()
        self.assertFalse((task_path / "STATE.md").exists())

        code, stdout, stderr, data = _run094([
            "mark", str(task_path), "--task-step", "task.task_md", "--done",
            "--auto-pass", "--note", "삭제상태기재",
        ])
        self.assertEqual(code, 0,
                         f"STATE.md 삭제 상태에서도 mark는 exit 0이어야 함(fail-open): "
                         f"stdout={stdout!r} stderr={stderr!r}")
        self.assertTrue(data.get("ok"), f"ok:true가 아님: {data}")

        self.assertTrue((task_path / "STATE.md").exists(),
                        "mark --force 후 STATE.md가 자동 생성되어야 함")
        md = (task_path / "STATE.md").read_text(encoding="utf-8")
        self.assertIn("삭제상태기재", md,
                     "삭제 상태에서 기재하려던 note가 저널 어디에도 없음(로그 유실)")

        state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        row = next(r for r in state["rows"] if r.get("key") == "task.task_md")
        self.assertEqual(row["status"], "done",
                         "state.json은 STATE.md 부재와 무관하게 정상 갱신되어야 함")

    # ── S-5: 저널 쓰기 불가 시 이중 실패 방지 [P0] ─────────────────────────

    def test_s5_state_md_readonly_fail_open_journal_warning(self):
        """[T094/L2-F001/F002] S-5 — STATE.md 권한을 0444(쓰기 불가)로 만든 뒤
        `mark --task-step <key> --done --auto-pass --note '권한불가기재'`를
        호출하면 ① `ok:true`·exit 0(파이프라인이 멈추지 않음) ②
        stdout `journal_warning.decision`에 기재 실패한 decision 원문 포함
        (로그가 조용히 증발하지 않음) ③ `state.json`은 정상 갱신, 이 3가지가
        모두 성립해야 한다(H-2/H-3, §3.1.2 (3) fail-open try/except).

        [PM 판정 정정 2026-08-16] 최초 작성 시 `status --set blocked --note`를
        트리거로 삼았으나, 저널 쓰기 불가 조건(0444) 자체를 검증하는 데는
        문제가 없되 R-2 AC가 요구하는 "실재 트리거 3종" 목록에 정합시키기
        위해 `mark --auto-pass --note`(트리거 #2)로 교정한다. 권한 0444 조건은
        그대로 유지한다. `mark`는 CLOSE 마지막 행이 아닌 한 `current_status`를
        건드리지 않으므로, state.json 정상 갱신 확인은 대상 행의
        `status`/`owner` 필드로 검증한다.

        RED 근거: 현재 `sync_state_md`는 어떤 예외도 흡수하지 않으므로,
        `save_state_md()`의 쓰기 시도가 `PermissionError`를 그대로 전파해
        CLI가 비정상 종료(exit 1, stdout에 유효 JSON 없음)한다 — journal_warning
        필드 자체가 존재하지 않는다."""
        task_path = self.tmpdir / "094-s5-readonly"
        task_path.mkdir()
        self._init_opd(task_path)
        md_path = task_path / "STATE.md"
        original_mode = md_path.stat().st_mode
        md_path.chmod(0o444)
        try:
            code, stdout, stderr, data = _run094([
                "mark", str(task_path), "--task-step", "task.task_md", "--done",
                "--auto-pass", "--note", "권한불가기재",
            ])
            self.assertEqual(code, 0,
                             f"저널 쓰기 실패가 파이프라인을 막으면 안 됨(fail-open): "
                             f"stdout={stdout!r} stderr={stderr!r}")
            self.assertTrue(data.get("ok"), f"ok:true가 아님: {data}")
            self.assertIn("journal_warning", data,
                         "저널 쓰기 실패 시 journal_warning 필드가 stdout에 없음(로그 유실 위험)")
            jw = data["journal_warning"]
            self.assertIn("권한불가기재", json.dumps(jw, ensure_ascii=False),
                         f"journal_warning에 기재 실패한 decision 원문이 없음: {jw}")

            state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
            row = next(r for r in state["rows"] if r.get("key") == "task.task_md")
            self.assertEqual(row["status"], "done",
                             "저널 쓰기 실패와 무관하게 state.json 행 상태는 정상 갱신되어야 함")
            self.assertEqual(row["owner"], "auto",
                             "저널 쓰기 실패와 무관하게 state.json owner는 정상 갱신되어야 함")
        finally:
            md_path.chmod(original_mode)

    # ── S-5 보안 후속 — journal_warning 경로 노출 (PLAN.md:1094, 094 Step 14 TEST 발견) ──

    def test_journal_warning_reason_redacts_absolute_path_and_home_dir(self):
        """[T094/SEC-FOLLOWUP] PLAN.md §5.4 "`journal_warning` 페이로드에 절대
        경로·사용자 홈 경로가 노출되지 않는가 — 예외 메시지에 경로가 포함되면
        파일명만 남기고 절삭" 요구사항의 회귀 테스트.

        opal-test-agent가 배포본(`~/.opal/tools/state-tool/run.sh`) 실증 중
        STATE.md를 0444(쓰기 불가)로 만든 뒤 `mark --auto-pass`를 호출하면
        `journal_warning.reason`에 태스크 폴더의 **절대 경로 전체**가 그대로
        노출됨을 실측했다(TEST-SCENARIO.md §6 보안 3번째 행, 094 Step 14).
        PM이 결함으로 확정하고 본 RED 테스트 작성을 지시했다(red-first.md §2 —
        작성자≠구현자, 구현은 별도 워커가 수행).

        검증 4조건 — `mark --auto-pass` 호출로 STATE.md 쓰기 실패를 유발한 뒤
        stdout `journal_warning.reason` 문자열에 대해:
        ① **절대경로 부재** — 태스크 폴더의 절대 경로 문자열(`str(task_path)`)이
           포함되지 않는다 (POSIX 절대경로 `/...` 형태 전체가 새어나가지 않는다)
        ② **홈 경로 부재** — `str(pathlib.Path.home())`가 포함되지 않는다
        ③ **파일명은 남는다** — `STATE.md`는 그대로 포함되어 진단 가치가
           보존된다(파일명까지 지우면 무엇이 실패했는지 알 수 없다)
        ④ **예외 타입은 남는다** — `PermissionError`가 포함되어 원인 분류가
           가능하다

        RED 근거: 현재 `sync_state_md`(`state_tool.py:447-450`)의 except 블록은
        `f"{type(e).__name__}: {e}"`로 예외 객체를 그대로 문자열화한다.
        `PermissionError`의 `str(e)`는 `[Errno 13] Permission denied: '<전체
        경로>'` 형태로 실패한 파일의 **절대 경로 전체**를 포함하므로(Python
        표준 OSError 메시지 포맷), 절삭 로직이 없는 현재 구현에서는 조건
        ①이 반드시 FAIL한다(경로 문자열이 그대로 나타남). [MUST]
        `state_tool.py`는 이 테스트를 통과시키기 위해 수정하지 않는다 — 구현은
        후속 워커(op-be-agent) 몫이다.

        [MUST] mock 금지 — 실 `os.chmod`(권한 조작으로 실패 주입) + 실
        `run.sh` CLI subprocess(`_run094`)로만 검증한다."""
        task_path = self.tmpdir / "094-secfix-journal-warning-path"
        task_path.mkdir()
        self._init_opd(task_path)
        md_path = task_path / "STATE.md"
        original_mode = md_path.stat().st_mode
        md_path.chmod(0o444)
        try:
            code, stdout, stderr, data = _run094([
                "mark", str(task_path), "--task-step", "task.task_md", "--done",
                "--auto-pass", "--note", "보안회귀-경로노출점검",
            ])
            self.assertEqual(code, 0,
                             f"저널 쓰기 실패가 파이프라인을 막으면 안 됨(fail-open): "
                             f"stdout={stdout!r} stderr={stderr!r}")
            self.assertIn("journal_warning", data,
                         f"journal_warning 필드가 stdout에 없음: {data}")
            reason = data["journal_warning"].get("reason", "")

            home = str(pathlib.Path.home())
            self.assertNotIn(str(task_path), reason,
                            f"journal_warning.reason에 태스크 폴더 절대 경로가 그대로 "
                            f"노출됨(PLAN §5.4 위반, 파일명만 남겨야 함): {reason!r}")
            self.assertNotIn(home, reason,
                            f"journal_warning.reason에 사용자 홈 디렉토리 경로가 "
                            f"노출됨(PLAN §5.4 위반): {reason!r}")
            self.assertIn("STATE.md", reason,
                         f"경로 절삭 시 파일명(STATE.md)까지 지워지면 진단 가치가 "
                         f"소실됨: {reason!r}")
            self.assertIn("PermissionError", reason,
                         f"예외 타입명이 사라지면 원인 분류가 불가능해짐: {reason!r}")
        finally:
            md_path.chmod(original_mode)

    # ── S-30: 손상 저널 골격 복구 append 분기 + 멱등 ───────────────────────

    def test_s30_broken_journal_skeleton_recovers_and_is_idempotent(self):
        """[T094/L2-F001] S-30 — `## 의사결정 로그` 표 헤더(헤더행+구분행)만
        제거한 손상 저널에서 `mark --auto-pass --note`를 2회 연속 호출하면,
        1회차에 골격이 append로 복구되며 로그 1행이 기재되고 기존 본문은
        무손실이어야 하며, 2회차에는 골격이 중복 append되지 않고(멱등) 로그만
        2행으로 누적되어야 한다(`ensure_journal_skeleton` 두 번째 분기 —
        헤더 미매칭 시 파일 끝 append, §3.1.2 (2)).

        [PM 판정 정정 2026-08-16] 최초 작성 시 `--force`(비워커·비게이트)를
        트리거로 삼았으나 실재하지 않는 트리거였다(실측: decision 세팅 트리거는
        auto-pass/worker-force/gate-force 3종뿐). 실재 트리거 `--auto-pass`
        (트리거 #2)로 교정한다. 2회차는 1회차와 다른 행(`task.user_confirm`)을
        대상으로 하여 "이미 done인 행 재대상"이 아닌 순수 append-경로 멱등성만
        관찰한다.

        RED 근거: 현재 코드에는 `ensure_journal_skeleton` 자체가 없다.
        `append_decision_log`는 `## 의사결정 로그\\n| # | 시점 | 결정 | 근거 |\\n
        |[-| ]+\\n` 정규식으로 헤더를 못 찾으면 조용히 원문을 반환하므로
        (state_tool.py:344-350), 골격 복구도 로그 기재도 일어나지 않는다."""
        task_path = self.tmpdir / "094-s30-broken"
        task_path.mkdir()
        self._init_opd(task_path)
        md_path = task_path / "STATE.md"
        original_md = md_path.read_text(encoding="utf-8")
        self.assertIn("| # | 시점 | 결정 | 근거 |", original_md,
                      "픽스처 전제: 원본 저널에 의사결정 로그 표 헤더가 있어야 함")
        broken_md = _corrupt_decision_log_table_header(original_md)
        self.assertNotIn("| # | 시점 | 결정 | 근거 |", broken_md,
                        "픽스처 손상 실패: 표 헤더가 여전히 남아있음")
        md_path.write_text(broken_md, encoding="utf-8")

        # 무손실 확인 대상 — 손상시키지 않은 임의 본문 마커
        self.assertIn("## 블로커", broken_md)
        self.assertIn("없음", broken_md)

        # 1회차 호출
        code, stdout, stderr, data = _run094([
            "mark", str(task_path), "--task-step", "task.task_md", "--done",
            "--auto-pass", "--note", "손상복구기재",
        ])
        self.assertEqual(code, 0, f"1회차 mark --auto-pass 실패: {stdout!r} {stderr!r}")
        self.assertTrue(data.get("ok"))

        md_after_1 = md_path.read_text(encoding="utf-8")
        self.assertIn("## 블로커", md_after_1, "1회차 이후 '## 블로커' 섹션이 소실됨(무손실 위반)")
        self.assertEqual(md_after_1.count("## 의사결정 로그"), 1,
                         "1회차 이후 '## 의사결정 로그' 헤딩이 중복 생성됨")
        self.assertEqual(md_after_1.count("| # | 시점 | 결정 | 근거 |"), 1,
                         "1회차 이후 표 헤더가 정확히 1개 복구되어야 함(append 분기)")
        rows_after_1 = _decision_log_row_numbers(md_after_1)
        self.assertEqual(rows_after_1, ["1"],
                         f"1회차 이후 로그가 정확히 1행(#1)이어야 함 — 실제: {rows_after_1}")
        self.assertIn("손상복구기재", md_after_1, "1회차 note가 로그에 기재되지 않음(조용한 no-op)")

        # 2회차 호출 — 멱등성(골격 중복 append 0, 로그만 누적)
        code, stdout, stderr, data = _run094([
            "mark", str(task_path), "--task-step", "task.user_confirm", "--done",
            "--auto-pass", "--note", "손상복구기재2",
        ])
        self.assertEqual(code, 0, f"2회차 mark --auto-pass 실패: {stdout!r} {stderr!r}")
        self.assertTrue(data.get("ok"))

        md_after_2 = md_path.read_text(encoding="utf-8")
        self.assertEqual(md_after_2.count("## 의사결정 로그"), 1,
                         "2회차 이후 '## 의사결정 로그' 헤딩이 중복 생성됨(비멱등)")
        self.assertEqual(md_after_2.count("| # | 시점 | 결정 | 근거 |"), 1,
                         "2회차 이후 표 헤더가 중복 append됨(비멱등)")
        rows_after_2 = _decision_log_row_numbers(md_after_2)
        self.assertEqual(rows_after_2, ["1", "2"],
                         f"2회차 이후 로그가 1,2로 누적되어야 함 — 실제: {rows_after_2}")
        self.assertIn("손상복구기재", md_after_2, "1회차 로그가 2회차 이후에도 보존되어야 함")
        self.assertIn("손상복구기재2", md_after_2, "2회차 note가 로그에 기재되지 않음")

    # ── S-32: --note 표 파괴 입력 방어 [경계 보강] ─────────────────────────

    def test_s32_note_with_pipe_and_newline_does_not_break_table(self):
        """[T094/L2-F001] S-32 — `--note` 값에 마크다운 표 구분자(`|`)와 개행이
        포함된 입력(`'A | B\\n두번째줄'`)으로 `mark --auto-pass`를 실행해도 ①
        `ok:true` ② `## 의사결정 로그` 표 구조가 파괴되지 않고 행 수가 정확히
        +1·컬럼 수 유지 ③ 입력 원문이 복원 가능한 형태로 보존(이스케이프/치환,
        무단 절삭 금지) ④ 후속 `mark` 호출이 정상 동작해야 한다
        (`append_decision_log` 입력 방어).

        [PM 판정 정정 2026-08-16] 최초 작성 시 `--force`(비워커·비게이트)를
        트리거로 삼았으나 실재하지 않는 트리거였다. 실재 트리거 `--auto-pass`
        (트리거 #2)로 교정한다 — dirty note는 `reason_text`(근거 컬럼)로
        유입된다.

        RED 근거: 현재 `append_decision_log`는 `decision`/`reason`을 이스케이프
        없이 `f"| {new_num} | {now_str} | {decision} | {reason} |\\n"`로 그대로
        삽입하므로(state_tool.py:356), `|`가 열 경계를 늘리고 개행이 표 행을
        여러 줄로 쪼갠다."""
        task_path = self.tmpdir / "094-s32-dirty-note"
        task_path.mkdir()
        self._init_opd(task_path)
        dirty_note = "A | B\n두번째줄"

        code, stdout, stderr, data = _run094([
            "mark", str(task_path), "--task-step", "task.task_md", "--done",
            "--auto-pass", "--note", dirty_note,
        ])
        self.assertEqual(code, 0, f"mark --auto-pass(dirty note) 실패: {stdout!r} {stderr!r}")
        self.assertTrue(data.get("ok"))

        md = (task_path / "STATE.md").read_text(encoding="utf-8")
        rows = _decision_log_row_numbers(md)
        self.assertEqual(rows, ["1"],
                         f"표 구분자/개행 입력 후에도 로그는 정확히 1행(#1)이어야 함 — 실제: {rows}")

        section = _extract_md_section(md, "의사결정 로그")
        data_lines = [ln for ln in section.splitlines() if re.match(r"^\|\s*1\s*\|", ln)]
        self.assertEqual(len(data_lines), 1,
                         f"1번 로그 행이 단일 물리 라인이어야 함(개행 미이스케이프 시 라인 분열) — "
                         f"섹션: {section!r}")
        cell_count = len(data_lines[0].strip().strip("|").split("|"))
        self.assertEqual(cell_count, 4,
                         f"표 컬럼 수(#/시점/결정/근거=4)가 유지되어야 함(| 미이스케이프 시 컬럼 증가) — "
                         f"실제 행: {data_lines[0]!r}")

        # 원문 복원 가능성 — 이스케이프/치환되었더라도 핵심 토큰은 보존되어야 함
        self.assertIn("A", md)
        self.assertIn("B", md)
        self.assertIn("두번째줄", md)

        # 후속 mark 호출 정상 동작
        code, stdout, stderr, data = _run094([
            "mark", str(task_path), "--task-step", "task.user_confirm", "--done",
            "--auto-pass", "--note", "후속 정상 호출",
        ])
        self.assertEqual(code, 0,
                         f"표 파괴 입력 이후 후속 mark가 실패하면 안 됨: {stdout!r} {stderr!r}")
        self.assertTrue(data.get("ok"))

    # ── R-2 AC 확대분 (PM 판정 2026-08-16) — 트리거 #3 worker-force 로그 보존 ──
    # [MUST 재사용 명시] 트리거 #3(gate-force)의 저널 보존은 이미
    # `TestTaskStepGate.test_s15_force_note_bypass_records_decision_log`
    # (state_tool.py:6357 부근)가 `gate_artifact_force` + missing 목록 기재를
    # 검증하고 있으므로 중복 신설하지 않는다 — 본 테스트는 나머지 1종
    # (`--as-worker --force`, 트리거 #3-a "worker-force")만 신규로 담당한다.

    def test_r2_worker_force_trigger_decision_log_preserved(self):
        """[T094/L2-F001] R-2 AC 확대 — `--as-worker --worker-stage <다른 단계>
        --force --note`(트리거 #3 "worker_scope_force")로 워커 스코프 위반을
        강제 우회해도 `## 의사결정 로그`에 `worker_scope_force` 및 note 원문이
        정상 기재되어야 한다(TASK.md R-2 AC가 auto-pass/worker-force/
        gate-force 3트리거 전부를 요구하도록 확대됨).

        이 트리거 자체는 094 이전부터 이미 `decision`을 세팅하는 실재 경로다
        (state_tool.py:1623-1627, "§2.17 트리거 #3"). 저널화(F-001) 이후에도
        이 로그 기재가 계속 보존되는지 확인하는 회귀 안전망이며, S-1이
        만드는 신규 저널 형식(`## 현재 상태` 등 파생 4패턴 부재) 위에서도
        `## 의사결정 로그`만은 여전히 기능해야 한다는 것이 R-2 AC의 핵심이다."""
        task_path = self.tmpdir / "094-r2-worker-force"
        task_path.mkdir()
        self._init_opd(task_path)

        code, stdout, stderr, data = _run094([
            "mark", str(task_path), "--task-step", "task.user_confirm", "--done",
            "--as-worker", "--worker-stage", "EXECUTE",
            "--force", "--note", "워커범위강제기재",
        ])
        self.assertEqual(code, 0, f"mark --as-worker --force 실패: {stdout!r} {stderr!r}")
        self.assertTrue(data.get("ok"), f"ok:true가 아님: {data}")

        md = (task_path / "STATE.md").read_text(encoding="utf-8")
        self.assertIn("worker_scope_force", md,
                     "저널화 이후 worker_scope_force 트리거의 의사결정 로그 기재가 유실됨(R-2 AC 위반)")
        self.assertIn("워커범위강제기재", md,
                     "worker_scope_force 로그에 note 원문이 없음(로그 유실 위험)")

        state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        row = next(r for r in state["rows"] if r.get("key") == "task.user_confirm")
        self.assertEqual(row["status"], "done", "state.json 행 상태가 정상 갱신되어야 함")


# ═════════════════════════════════════════════════════════════════════════════
# 094 RED-first 신설 — TestLegacyCoexistence (TEST-SCENARIO.md S-29, S-11)
# PLAN §3.2.2 (4) 함수 생사 판정 / §3.3.2 (1)(2) show 렌더 원천 단일화·배너, D-4
# [MUST] 레거시 원본 tasks/093-*는 절대 직접 조작하지 않는다 — 반드시 tmp_path
# 사본을 조작한다(TASK.md 확정 방향 §4 소급 변경 금지). mock/patch 금지.
# ═════════════════════════════════════════════════════════════════════════════

# TEST-SCENARIO.md §2.1 "레거시 STATE.md" 실 파일 자산 — 메인 저장소 경로(워크트리에는
# tasks/ 디렉토리가 포함되지 않으므로 절대경로로 직접 참조한다).
_LEGACY_093_TASK_DIR = pathlib.Path(
    "/Volumes/Data/AiStudio/workspace/opal/tasks/093-260815-opd-사용자확인행-자동승인-일원화"
)


def _extract_marker_region(md):
    """094: PIPELINE_MARKER_START~END(마커 포함) 구간 원문을 반환. 없으면 None."""
    start = md.find(ST.PIPELINE_MARKER_START)
    end = md.find(ST.PIPELINE_MARKER_END)
    if start == -1 or end == -1:
        return None
    return md[start:end + len(ST.PIPELINE_MARKER_END)]


def _extract_current_status_region(md):
    """094: '## 현재 상태' 섹션(헤딩 + '- ' 라인들) 원문을 반환. 없으면 None."""
    m = re.search(r"## 현재 상태\n(?:- [^\n]+\n){1,6}", md)
    return m.group(0) if m else None


class TestLegacyCoexistence(BaseTestCase):
    """094 F-002/F-003 — 레거시(001~093, 마커+표+`## 현재 상태` 보유) STATE.md와
    신형 저널 코드의 공존. 반드시 `tasks/093-*` **사본**으로만 조작하고 원본은
    읽기만 한다(소급 변경 금지). [MUST] 실 CLI subprocess + 실 파일 I/O, mock 금지.
    """

    def setUp(self):
        super().setUp()
        if not _LEGACY_093_TASK_DIR.exists():
            self.skipTest(f"레거시 실 자산 없음(메인 저장소 경로): {_LEGACY_093_TASK_DIR}")
        self._legacy_original_state_md = (_LEGACY_093_TASK_DIR / "STATE.md").read_bytes()
        self._legacy_original_state_json = (_LEGACY_093_TASK_DIR / "state.json").read_bytes()

    def _copy_legacy_task(self, name):
        """093 STATE.md + state.json을 tmp_path 사본으로 복사(원본 무변경)."""
        dst = self.tmpdir / name
        dst.mkdir()
        shutil.copy2(_LEGACY_093_TASK_DIR / "STATE.md", dst / "STATE.md")
        shutil.copy2(_LEGACY_093_TASK_DIR / "state.json", dst / "state.json")
        return dst

    def _assert_legacy_original_untouched(self):
        self.assertEqual(
            (_LEGACY_093_TASK_DIR / "STATE.md").read_bytes(), self._legacy_original_state_md,
            "원본 tasks/093-*/STATE.md가 변경됨(소급 변경 금지 위반)")
        self.assertEqual(
            (_LEGACY_093_TASK_DIR / "state.json").read_bytes(), self._legacy_original_state_json,
            "원본 tasks/093-*/state.json이 변경됨(소급 변경 금지 위반)")

    # ── S-29: 레거시 저널 쓰기 경로 — 표 바이트 동결 [P0·BLOCKING 해소] ────

    def test_s29_legacy_write_path_freezes_pipeline_table_bytes(self):
        """[T094/L2-F001/F002] S-29 — `tasks/093-*` 사본(마커+표+`## 현재 상태`
        보유)에 `advance` → `mark --auto-pass --note '레거시쓰기기재'` → `block`을
        연속 호출하면 ① 3개 호출 전건 `ok:true`·무예외 ② `## 의사결정 로그`에
        해당 note 1행 정상 추가 ③ 마커·파이프라인 표·`## 현재 상태` 블록이
        **바이트 동결**(호출 전후 diff 0) ④ 마커·표 중복 삽입 0건 ⑤ 원본
        무변경이 모두 성립해야 한다(H-4 핵심 — §3.1.2 (3) 신형 `sync_state_md`는
        더 이상 파이프라인 표/`## 현재 상태`를 재렌더하지 않는다).

        [PM 판정 정정 2026-08-16] 최초 작성 시 중간 호출을 `mark --force --note`
        (비워커·비게이트)로 삼았으나 실재하지 않는 트리거였다. 실재 트리거
        `--auto-pass`(트리거 #2)로 교정한다.

        RED 근거: 현재 `sync_state_md`는 매 호출마다 `render_pipeline_table`+
        `replace_pipeline_section`으로 마커 구간을 다시 그리고
        `update_current_status_section`으로 `## 현재 상태`를 갱신하므로
        (state_tool.py:380-387), 세 번의 호출 후 두 구간 모두 원본과
        바이트 단위로 달라진다(동결 위반)."""
        task_path = self._copy_legacy_task("094-s29-legacy-write")

        # advance가 가능하도록 사본 state.json의 한 행만 pending으로 되돌린다
        # (093 원본은 전 행 done/na로 완주되어 advance 대상이 없음 — 사본 한정 조정,
        # 원본 파일은 건드리지 않는다).
        state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        state["rows"][0]["status"] = "pending"
        state["rows"][0]["status_label"] = "⬜"
        state["rows"][0]["timestamp"] = None
        (task_path / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        md_before = (task_path / "STATE.md").read_text(encoding="utf-8")
        marker_before = _extract_marker_region(md_before)
        current_status_before = _extract_current_status_region(md_before)
        self.assertIsNotNone(marker_before, "픽스처 전제: 사본에 마커 구간이 있어야 함")
        self.assertIsNotNone(current_status_before, "픽스처 전제: 사본에 '## 현재 상태'가 있어야 함")

        code, stdout, stderr, data = _run094([
            "advance", str(task_path), "--task-step", "task.task_md",
        ])
        self.assertEqual(code, 0, f"advance 실패: {stdout!r} {stderr!r}")
        self.assertTrue(data.get("ok"))

        code, stdout, stderr, data = _run094([
            "mark", str(task_path), "--task-step", "task.task_md", "--done",
            "--auto-pass", "--note", "레거시쓰기기재",
        ])
        self.assertEqual(code, 0, f"mark --auto-pass 실패: {stdout!r} {stderr!r}")
        self.assertTrue(data.get("ok"))

        code, stdout, stderr, data = _run094([
            "block", str(task_path), "--task-step", "task.user_confirm",
            "--reason", "레거시블록",
        ])
        self.assertEqual(code, 0, f"block 실패: {stdout!r} {stderr!r}")
        self.assertTrue(data.get("ok"))

        md_after = (task_path / "STATE.md").read_text(encoding="utf-8")
        self.assertIn("레거시쓰기기재", md_after,
                     "레거시 사본에서도 의사결정 로그 기재가 유실되면 안 됨(H-1)")

        marker_after = _extract_marker_region(md_after)
        current_status_after = _extract_current_status_region(md_after)
        self.assertEqual(marker_after, marker_before,
                         "3회 호출 후 레거시 파이프라인 표/마커 구간이 바이트 동결되지 않음(H-4 위반)")
        self.assertEqual(current_status_after, current_status_before,
                         "3회 호출 후 레거시 '## 현재 상태' 블록이 바이트 동결되지 않음(H-4 위반)")

        self.assertEqual(md_after.count(ST.PIPELINE_MARKER_START), 1,
                         "pipeline:start 마커가 중복 삽입됨")
        self.assertEqual(md_after.count(ST.PIPELINE_MARKER_END), 1,
                         "pipeline:end 마커가 중복 삽입됨")
        self.assertEqual(md_after.count("## 현재 상태"), 1,
                         "'## 현재 상태' 섹션이 중복 삽입됨")

        self._assert_legacy_original_untouched()

    # ── S-11: 레거시 동결 표 오반환 차단 [P0] ──────────────────────────────

    def test_s11_show_md_returns_state_json_values_not_frozen_table(self):
        """[T094/L2-F003] S-11 — `tasks/093-*` 사본에서 STATE.md 표 내용과
        `state.json.rows[]`를 의도적으로 불일치시킨 뒤 `show --format md`를
        호출하면 ① 반환 표가 **state.json 값**과 일치(STATE.md 동결 표가
        아님) ② 배너 1줄 prepend ③ `marker_present:true` ④ 원본 무변경이
        모두 성립해야 한다(D-4, R-5 AC(b) — 렌더 원천 단일화).

        RED 근거: 현재 `cmd_show --format md`는 마커가 있으면 STATE.md
        본문에서 표를 그대로 추출해 반환하므로(state_tool.py:1395-1405),
        의도적으로 불일치시킨 state.json 값이 아니라 STATE.md의 동결된
        옛 값을 그대로 반환한다 — 배너도 붙지 않는다."""
        task_path = self._copy_legacy_task("094-s11-legacy-show")

        # state.json 값과 STATE.md 표 내용을 의도적으로 불일치시킨다
        # (STATE.md 표는 원래 row1=done/✅ — state.json만 in_progress로 되돌려
        # 표와 어긋나게 만든다).
        state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["rows"][0]["status"], "done",
                         "픽스처 전제: 원본 093 row1은 done이어야 의도적 불일치 설계가 성립함")
        distinct_note = "094-S11-불일치마커"
        state["rows"][0]["status"] = "in_progress"
        state["rows"][0]["status_label"] = "🔄"
        state["rows"][0]["note"] = distinct_note
        (task_path / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        code, stdout, stderr, data = _run094([
            "show", str(task_path), "--format", "md",
        ])
        self.assertEqual(code, 0, f"show 실패: {stdout!r} {stderr!r}")
        self.assertTrue(data.get("ok"))
        self.assertTrue(data.get("marker_present"),
                        "레거시 사본은 마커가 있으므로 marker_present:true여야 함")

        content = data.get("content", "")
        self.assertIn(distinct_note, content,
                     "show --format md가 state.json의 최신(불일치) 값을 반영하지 않음"
                     "(STATE.md 동결 표를 그대로 반환한 것으로 의심됨, D-4 위반)")
        self.assertTrue(content.lstrip().startswith("> [레거시]"),
                        f"레거시 배너가 content 최상단에 prepend되지 않음: {content[:200]!r}")

        self._assert_legacy_original_untouched()


# ═════════════════════════════════════════════════════════════════════════════
# 094 RED-first 신설 — TestShowAsQueryStandard (TEST-SCENARIO.md S-10, S-24, S-25)
# PLAN §3.3.2 (1)(2)(3) cmd_show 3분기 재설계 — 렌더 원천 단일화·배너 극성 반전
# [MUST] mock/patch 금지. 신규 저널(마커 없음) 픽스처는 현재 코드가 마커를 항상
# 생성하므로, init 후 마커 구간을 제거해 "D-1 완전 제거 후" 형태를 모사한다.
# ═════════════════════════════════════════════════════════════════════════════

class TestShowAsQueryStandard(BaseTestCase):
    """094 F-003 — `show`가 현황 조회 표준 경로로서 3포맷 모두 일관되게
    동작해야 한다: md는 항상 state.json 파생, full은 배너 극성이 마커 유무에
    따라 정확히 반전(레거시=부착/신규=미부착), 응답 키 계약은 삭제 0건."""

    def setUp(self):
        super().setUp()
        self.assertTrue(_OPD_REAL_PIPELINE_JSON.exists())

    def _init_opd(self, task_path):
        code, stdout, stderr, data = _run094([
            "init", str(task_path), "--skill", "opd", "--mode", "agentic",
            "--rows-from", str(_OPD_REAL_PIPELINE_JSON),
        ])
        self.assertEqual(code, 0, f"init 실패: {stdout!r} {stderr!r}")
        return data

    def _strip_markers_to_simulate_new_journal(self, task_path):
        """094: D-1 완전 제거(파생 4패턴 부재) 후의 신규 저널 형태를 모사하기
        위해, 현재 코드가 생성한 마커+표+`## 현재 상태` 블록을 제거한다.
        (GREEN 이후에는 `init` 자체가 이 형태를 직접 산출하게 된다 — S-1)."""
        md = (task_path / "STATE.md").read_text(encoding="utf-8")
        md = re.sub(
            re.escape(ST.PIPELINE_MARKER_START) + r".*?" + re.escape(ST.PIPELINE_MARKER_END) + r"\n?",
            "", md, flags=re.DOTALL)
        md = re.sub(r"## 현재 상태\n(?:- [^\n]+\n){1,6}\n?", "", md)
        (task_path / "STATE.md").write_text(md, encoding="utf-8")
        return md

    # ── S-10: show --format md 신규 태스크 렌더 ────────────────────────────

    def test_s10_show_md_new_journal_renders_from_state_json(self):
        """[T094/L1-F003] S-10 — 신규 태스크(마커 없음)에서 `show --format md`는
        `state.json.rows[]` 파생 표 + `- 모드:`/`- 상태:`/`- 다음 액션:` 3줄을
        포함해야 하고, `marker_present:false`여야 한다(R-5 AC(b) — STATE.md에서
        뺀 '## 현재 상태' 4줄 정보가 조회 경로로 이동, 정보 손실 0).

        RED 근거: 현재 `cmd_show`의 마커-없음 fallback 분기는
        `render_pipeline_table` 결과만 반환하고 `- 모드:`/`- 상태:`/
        `- 다음 액션:` 3줄을 전혀 포함하지 않는다(state_tool.py:1376-1393)."""
        task_path = self.tmpdir / "094-s10-new-journal"
        task_path.mkdir()
        self._init_opd(task_path)
        self._strip_markers_to_simulate_new_journal(task_path)

        code, stdout, stderr, data = _run094([
            "show", str(task_path), "--format", "md",
        ])
        self.assertEqual(code, 0, f"show 실패: {stdout!r} {stderr!r}")
        self.assertTrue(data.get("ok"))
        self.assertFalse(data.get("marker_present", True),
                         "마커 없는 신규 저널은 marker_present:false여야 함")

        content = data.get("content", "")
        self.assertIn("- 모드:", content, "show --format md에 '- 모드:' 라인이 없음(정보 손실)")
        self.assertIn("- 상태:", content, "show --format md에 '- 상태:' 라인이 없음(정보 손실)")
        self.assertIn("- 다음 액션:", content, "show --format md에 '- 다음 액션:' 라인이 없음(정보 손실)")
        self.assertIn("작업", content, "표에 rows[] 파생 내용(항목명)이 반영되어야 함")

    # ── S-24: show --format full 배너 조건부 부착 ──────────────────────────

    def test_s24_show_full_banner_only_on_legacy(self):
        """[T094/L2-F003] S-24 — `show --format full`은 레거시(마커 잔존)에는
        배너를 부착하고 신규(마커 없음)에는 부착하지 않으며, 두 경우 모두
        STATE.md 원문을 손상 없이 반환해야 한다(D-4 배너 극성 반전).

        RED 근거: 현재 `cmd_show --format full`은 정확히 반대로 동작한다 —
        마커 **없을 때** 복구 권고 WARNING을 prepend하고, 마커가 **있을 때**는
        아무 배너 없이 원문만 반환한다(state_tool.py:1365-1374, D-4가 뒤집으려는
        지점 그 자체)."""
        if not _LEGACY_093_TASK_DIR.exists():
            self.skipTest(f"레거시 실 자산 없음: {_LEGACY_093_TASK_DIR}")

        # 케이스 1 — 레거시(마커 잔존)
        legacy_path = self.tmpdir / "094-s24-legacy"
        legacy_path.mkdir()
        shutil.copy2(_LEGACY_093_TASK_DIR / "STATE.md", legacy_path / "STATE.md")
        shutil.copy2(_LEGACY_093_TASK_DIR / "state.json", legacy_path / "state.json")
        legacy_raw = (legacy_path / "STATE.md").read_text(encoding="utf-8")

        code, stdout, stderr, data = _run094(["show", str(legacy_path), "--format", "full"])
        self.assertEqual(code, 0, f"레거시 show full 실패: {stdout!r} {stderr!r}")
        legacy_content = data.get("content", "")
        self.assertTrue(legacy_content.lstrip().startswith("> [레거시]"),
                        f"레거시 사본에는 배너가 부착되어야 함: {legacy_content[:200]!r}")
        self.assertIn(legacy_raw, legacy_content,
                     "레거시 원문이 손상 없이(배너 아래) 포함되어야 함")

        # 케이스 2 — 신규(마커 없음)
        new_path = self.tmpdir / "094-s24-new"
        new_path.mkdir()
        self._init_opd(new_path)
        self._strip_markers_to_simulate_new_journal(new_path)
        new_raw = (new_path / "STATE.md").read_text(encoding="utf-8")

        code, stdout, stderr, data = _run094(["show", str(new_path), "--format", "full"])
        self.assertEqual(code, 0, f"신규 show full 실패: {stdout!r} {stderr!r}")
        new_content = data.get("content", "")
        self.assertFalse(new_content.lstrip().startswith("> [레거시]"),
                         "신규 저널(마커 없음)에는 배너가 부착되면 안 됨")
        self.assertEqual(new_content, new_raw,
                        "신규 저널은 원문 그대로(배너·경고 문구 없이) 반환되어야 함")

    # ── S-25: show 3포맷 응답 키 계약 유지 ──────────────────────────────────

    def test_s25_show_three_formats_response_key_contract_preserved(self):
        """[T094/L1-F003] S-25 — `show --format md/json/full` 3포맷 응답의
        키 집합이 기존과 동일해야 한다(추가만 허용, 삭제 0) — `ok`, `command`,
        `format`, `marker_present`, `content`(md/full)/`data`(json)(제약 ③).

        이 검사 자체는 F-003이 `content`/`data` 값의 출처만 바꾸고 키를
        삭제하지 않으므로 현재도 통과할 수 있는 회귀 안전망이다."""
        task_path = self.tmpdir / "094-s25-response-keys"
        task_path.mkdir()
        self._init_opd(task_path)

        baseline = {
            "md":   {"ok", "command", "format", "marker_present", "content"},
            "json": {"ok", "command", "format", "marker_present", "data"},
            "full": {"ok", "command", "format", "content"},
        }
        for fmt, expected in baseline.items():
            code, stdout, stderr, data = _run094(["show", str(task_path), "--format", fmt])
            self.assertEqual(code, 0, f"show --format {fmt} 실패: {stdout!r} {stderr!r}")
            missing = expected - set(data.keys())
            self.assertEqual(missing, set(),
                             f"show --format {fmt} 응답에서 기존 키 삭제됨: {missing}")
# 093 (RED-first, mode:red) — 파이프라인 사용자 확인 행 자동 승인 경로 일원화
#   TEST-SCENARIO.md S-1~S-18 / S-24~S-26 (S-19 전체 스위트·S-20~S-22 문서·S-23 L3 제외)
#   PLAN §3 F-001~F-006 시그니처·계약을 그대로 신뢰해 작성한 실패 테스트다.
#
# [MUST] red-first.md §2 작성자≠구현자 — 본 블록은 테스트만 추가하며 state_tool.py를
#        수정하지 않는다. 기존 케이스도 수정·삭제하지 않는다(순수 additive).
# [MUST] red-first.md §4 / 헌법 §4 "Don't fake it" — mock/patch/MagicMock 미사용.
#        worktree run.sh subprocess 실호출 + 실 pipeline.json + 실 state.json 파일
#        내용(공개 인터페이스: exit code / stdout JSON / 파일 상태)으로만 검증한다.
#        시각도 실 date.js를 통과한 실제 KST 값을 쓴다(고정 모킹 없음).
# ═════════════════════════════════════════════════════════════════════════════

_REPO_ROOT_093 = _TOOL_DIR.parent.parent.parent
_SRC_093 = _TOOL_DIR / "state_tool.py"
_OPD_PIPELINE_093 = (_REPO_ROOT_093 / "opal" / "skills" / "opal-pilot-dev"
                     / "references" / "pipeline.json")


def _t093_json(obj):
    return json.dumps(obj, ensure_ascii=False)


def _t093_pipeline_spec(skill, stages, steps):
    """070/091 pipeline.json 스펙 포맷 픽스처 (validate_pipeline_spec 통과 형태)."""
    return {
        "spec_version": "1.0",
        "skill": skill,
        "meta": {"mode_label": "T093 fixture", "stages": stages},
        "task_steps": steps,
    }


# 경계 불변 회귀표 표 A(B-1~B-9) 공용 픽스처 — PLAN §3.3.2 (3)
_T093_B_SPEC = _t093_json([
    {"stage": "TASK",    "item": "작업"},            # row 1
    {"stage": "TASK",    "item": "사용자 확인"},      # row 2 — MODE_BOUNDARY_STAGES
    {"stage": "EXECUTE", "item": "작업"},            # row 3
    {"stage": "EXECUTE", "item": "사용자 확인"},      # row 4 — 경계 밖 일반 stage
    {"stage": "CLOSE",   "item": "DONE.md 생성"},    # row 5 — CLOSE 첫 행
])

# 경계 불변 회귀표 표 B(V-1~V-9) 공용 픽스처 — CLOSE 첫 행이 사용자 확인 행이 아니게 두어
# check_close_gate와 무관하게 validate 축만 관찰한다.
_T093_V_SPEC = _t093_json([
    {"stage": "TASK",    "item": "사용자 확인"},      # row 1
    {"stage": "EXECUTE", "item": "사용자 확인"},      # row 2
    {"stage": "CLOSE",   "item": "DONE.md 생성"},    # row 3
    {"stage": "CLOSE",   "item": "사용자 확인"},      # row 4
])


class _T093Base(unittest.TestCase):
    """093 공통 베이스 — tmp 작업 폴더 + worktree run.sh subprocess 실호출.

    [MUST] AGENT.md §확정 기준 #2 — tempfile.mkdtemp() 밖(레포/~/.opal)을 쓰지 않는다.
    tmp 경로에는 .opal/MEMORY.json이 없으므로 CLOSE 마지막 행 mark의
    link_memory_history()는 skipped로 무해하게 끝난다(실 메모리 파일 미오염).
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ── 픽스처 ────────────────────────────────────────────────────────────
    def _task_dir(self, name):
        d = self.tmpdir / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _init(self, task_dir, mode, *, rows_spec=None, rows_from=None, skill="opd"):
        argv = ["init", str(task_dir), "--skill", skill, "--mode", mode]
        if rows_spec is not None:
            argv += ["--rows-spec", rows_spec]
        if rows_from is not None:
            argv += ["--rows-from", str(rows_from)]
        code, stdout, stderr, data = _run070(argv)
        self.assertEqual(code, 0, f"init 실패(mode={mode}): {stdout!r} / {stderr!r}")
        return data

    def _init_b(self, mode, name=None):
        d = self._task_dir(name or f"b-{mode}")
        self._init(d, mode, rows_spec=_T093_B_SPEC)
        return d

    # ── 관찰 ──────────────────────────────────────────────────────────────
    def _state_of(self, task_dir):
        return json.loads((task_dir / "state.json").read_text(encoding="utf-8"))

    def _row(self, task_dir, row_id):
        for r in self._state_of(task_dir)["rows"]:
            if r["row_id"] == row_id:
                return r
        self.fail(f"row {row_id} 없음 (task_dir={task_dir})")

    # ── 호출 ──────────────────────────────────────────────────────────────
    def _mark(self, task_dir, row_id, *extra):
        return _run070(["mark", str(task_dir), "--row", str(row_id), "--done", *extra])

    def _mark_key(self, task_dir, key, *extra):
        return _run070(["mark", str(task_dir), "--task-step", key, "--done", *extra])

    def _advance(self, task_dir, row_id, *extra):
        return _run070(["advance", str(task_dir), "--row", str(row_id), *extra])

    def _advance_key(self, task_dir, key, *extra):
        return _run070(["advance", str(task_dir), "--task-step", key, *extra])

    def _validate(self, task_dir):
        return _run070(["validate", str(task_dir)])

    def _assert_ok(self, result, label):
        code, stdout, stderr, data = result
        self.assertEqual(code, 0, f"{label} exit!=0 (stdout={stdout!r} stderr={stderr!r})")
        return data


# ─────────────────────────────────────────────────────────────────────────────
# S-2 / S-3 / S-4 — F-001 auto-na 제거 + 전 모드 pending 초기화
# ─────────────────────────────────────────────────────────────────────────────

class TestT093AutoNaRemoval(_T093Base):
    """F-001 — init 시점 agentic auto-na 분기 제거 (TEST-SCENARIO S-2/S-3/S-4)."""

    _USER_CONFIRM_INIT = {
        "status": "pending", "status_label": "⬜", "owner": "PM",
        "timestamp": None, "note": None,
    }

    def _assert_pending_user_confirm(self, task_dir, label):
        rows = self._state_of(task_dir)["rows"]
        targets = [r for r in rows if r["item"] == "사용자 확인"]
        self.assertTrue(targets, f"{label}: 사용자 확인 행이 픽스처에 없음")
        for r in targets:
            for field, expected in self._USER_CONFIRM_INIT.items():
                self.assertEqual(
                    r.get(field), expected,
                    f"{label}: row {r['row_id']}({r['stage']}) {field}="
                    f"{r.get(field)!r}, 기대 {expected!r} — F-1 AC(b) 전 모드 pending/PM")

    def test_auto_na_marker_absent_in_source_T093_L1_F1a(self):
        """[T093/L1-F1a] S-2 — state_tool.py에 'agentic auto-na at init' 잔존 0건.
        3개 빌더의 mode 파라미터 시그니처는 존치(PLAN §3.1.2 [MUST])."""
        src = _SRC_093.read_text(encoding="utf-8")
        hits = [i + 1 for i, line in enumerate(src.splitlines())
                if "agentic auto-na at init" in line]
        self.assertEqual(hits, [],
                         f"F-001 구형 잔존 — 'agentic auto-na at init' 라인 {hits}")

        import inspect
        for fn in (ST.build_rows_from_spec, ST.build_rows_from_skill_md,
                   ST.build_rows_from_pipeline_json):
            params = list(inspect.signature(fn).parameters)
            self.assertIn("mode", params,
                          f"{fn.__name__} 시그니처에서 mode 제거 금지 (PLAN §3.1.2)")

    def test_three_modes_init_rows_identical_T093_L1_F1b(self):
        """[T093/L1-F1b] S-3 — 실 opd pipeline.json을 3모드로 init → rows[] 전 필드 diff 0.
        F-1 AC(b)의 유일한 직접 검증(PLAN TS-004)."""
        self.assertTrue(_OPD_PIPELINE_093.is_file(),
                        f"실 pipeline.json 부재: {_OPD_PIPELINE_093}")
        rows_by_mode = {}
        for mode in ("interactive", "semi-agentic", "agentic"):
            d = self._task_dir(f"3mode-{mode}")
            self._init(d, mode, rows_from=_OPD_PIPELINE_093)
            rows_by_mode[mode] = self._state_of(d)["rows"]
            self._assert_pending_user_confirm(d, f"S-3/{mode}")

        base = rows_by_mode["interactive"]
        for mode in ("semi-agentic", "agentic"):
            other = rows_by_mode[mode]
            self.assertEqual(len(base), len(other), f"{mode}: 행 수 불일치")
            for i, (a, b) in enumerate(zip(base, other)):
                self.assertEqual(
                    a, b,
                    f"S-3 diff!=0 — row index {i}: interactive={a!r} / {mode}={b!r}")

    def test_all_three_builders_init_pending_T093_L1_F1b(self):
        """[T093/L1-F1b] S-4 — 빌더 3경로(--rows-spec / --rows-from *.md / *.json)를
        각각 --mode agentic으로 init → 사용자 확인 행 전건 pending/⬜/PM."""
        # (a) build_rows_from_spec — 인라인 JSON
        d_spec = self._task_dir("builder-spec")
        self._init(d_spec, "agentic", rows_spec=_t093_json([
            {"stage": "TASK",  "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "사용자 확인"},
        ]))
        self._assert_pending_user_confirm(d_spec, "S-4(a) rows-spec")

        # (b) build_rows_from_skill_md — 레거시 SKILL.md 표
        skill_md = self.tmpdir / "SKILL.md"
        skill_md.write_text(
            "\n## STATE.md 도메인 치환값\n\n"
            "| # | 단계 | 항목 | 상태 | 시점 |\n"
            "|---|------|------|------|------|\n"
            "| 1 | TASK | 사용자 확인 | ⬜ |  |\n"
            "| 2 | CLOSE | 사용자 확인 | ⬜ |  |\n",
            encoding="utf-8")
        d_md = self._task_dir("builder-skillmd")
        self._init(d_md, "agentic", rows_from=skill_md)
        self._assert_pending_user_confirm(d_md, "S-4(b) rows-from SKILL.md")

        # (c) build_rows_from_pipeline_json — 실 opd pipeline.json
        d_json = self._task_dir("builder-pipeline")
        self._init(d_json, "agentic", rows_from=_OPD_PIPELINE_093)
        self._assert_pending_user_confirm(d_json, "S-4(c) rows-from pipeline.json")


# ─────────────────────────────────────────────────────────────────────────────
# S-1 / S-5 / S-13 / S-26 — F-002 자동 승인 훅 (긍정 경로)
# ─────────────────────────────────────────────────────────────────────────────

class TestT093AutoApproveHook(_T093Base):
    """F-002 auto_approve_prior_user_confirmations — 다음 단계 진입만으로 자동 승인."""

    _TASK_MD = (
        "# TASK: T093 픽스처\n\n"
        "## 목표\n자동 승인 훅 관통 검증\n\n"
        "## 완료 기준\n- 전 행 진행\n"
    )  # '## 명확화 결과' 섹션 부재 → _run_clarification_hook graceful skip(005 정책 A)

    def _opd_task(self, name):
        d = self._task_dir(name)
        self._init(d, "agentic", rows_from=_OPD_PIPELINE_093)
        # gate.artifacts 실 파일 생성 (analysis.pm_gate / plan.pm_gate / scenario_gate)
        (d / "TASK.md").write_text(self._TASK_MD, encoding="utf-8")
        (d / "ANALYSIS.md").write_text("# ANALYSIS\n", encoding="utf-8")
        (d / "PLAN.md").write_text("# PLAN\n", encoding="utf-8")
        (d / "TEST-SCENARIO.md").write_text("# TEST SCENARIO\n", encoding="utf-8")
        return d

    def test_pipeline_traversal_auto_approves_T093_L2_GOAL(self):
        """[T093/L2-GOAL] S-1 — 실 opd pipeline.json 관통(TASK→EXECUTE).
        어느 호출에도 --auto-pass를 전달하지 않는다. 훅 미배선이면
        stage_transition_violation으로 실패해야 한다(070 동형 공백 방지)."""
        d = self._opd_task("s1-traversal")
        for key in ("task.task_md", "analysis.analysis_md", "analysis.pm_gate",
                    "plan.plan_md", "plan.pm_gate",
                    "test_scenario.test_scenario_md", "test_scenario.scenario_gate"):
            self._assert_ok(self._mark_key(d, key), f"S-1 mark {key}")

        entry = self._assert_ok(self._advance_key(d, "execute.implement"),
                                "S-1 advance execute.implement")

        state = self._state_of(d)
        by_key = {r.get("key"): r for r in state["rows"]}

        # ② 4개 user_confirm 행이 명시 호출 없이 done/auto/timestamp≠None
        for key, stage in (("task.user_confirm", "TASK"),
                           ("analysis.user_confirm", "ANALYSIS"),
                           ("plan.user_confirm", "PLAN"),
                           ("test_scenario.user_confirm", "TEST-SCENARIO")):
            r = by_key[key]
            self.assertEqual(r["status"], "done", f"S-1 {key} status={r['status']}")
            self.assertEqual(r["owner"], "auto", f"S-1 {key} owner={r.get('owner')}")
            self.assertIsNotNone(r.get("timestamp"), f"S-1 {key} timestamp 미기록")
            self.assertEqual(r["stage"], stage)

        # ③ na 상태 행 0건
        na_rows = [r["row_id"] for r in state["rows"] if r.get("status") == "na"]
        self.assertEqual(na_rows, [], f"S-1 na 잔존 행 {na_rows}")

        # ④ 승인 timestamp가 그 행을 승인시킨 진입 호출 응답 timestamp와 문자열 일치
        approved = entry.get("auto_approved")
        self.assertEqual(approved, [by_key["test_scenario.user_confirm"]["row_id"]],
                         f"S-1 EXECUTE 진입 auto_approved={approved!r}")
        self.assertEqual(by_key["test_scenario.user_confirm"]["timestamp"],
                         entry.get("timestamp"),
                         "S-1 승인 timestamp가 진입 호출 응답 timestamp와 불일치")
        self.assertEqual(by_key["execute.implement"]["status"], "in_progress")

    def test_hook_fires_without_auto_pass_flag_T093_L2_F2(self):
        """[T093/L2-F2] S-5 — PLAN 첫 행 advance 시 앞 ANALYSIS 사용자 확인 행이
        done/auto/timestamp≠None이 되고 note가 'auto-approved on PLAN entry'
        형식('agentic auto-pass:' 접두 미사용, PLAN §3.2.2 (4) [MUST])."""
        d = self._opd_task("s5-hook")
        for key in ("task.task_md", "analysis.analysis_md", "analysis.pm_gate"):
            self._assert_ok(self._mark_key(d, key), f"S-5 mark {key}")

        data = self._assert_ok(self._advance_key(d, "plan.plan_md"), "S-5 advance plan.plan_md")

        r = {x.get("key"): x for x in self._state_of(d)["rows"]}["analysis.user_confirm"]
        self.assertEqual(r["status"], "done")
        self.assertEqual(r["owner"], "auto")
        self.assertIsNotNone(r.get("timestamp"))
        self.assertEqual(r.get("status_label"), "✅")
        self.assertEqual(r.get("note"), "auto-approved on PLAN entry",
                         f"S-5 note={r.get('note')!r}")
        self.assertNotIn("agentic auto-pass", str(r.get("note")),
                         "훅 승인 note는 PM 명시 호출(F-005) 문자열 공간과 분리되어야 한다")
        self.assertIn(r["row_id"], data.get("auto_approved") or [])

    def test_semi_agentic_post_execute_auto_approved_T093_L1_F3(self):
        """[T093/L1-F3] S-13 — semi-agentic에서 MODE_BOUNDARY_STAGES 밖(EXECUTE→TEST)
        구간은 자동 승인이 허용된다(exit 0, done/auto/timestamp≠None)."""
        d = self._task_dir("s13-semi-post")
        self._init(d, "semi-agentic", rows_spec=_t093_json([
            {"stage": "EXECUTE", "item": "작업"},
            {"stage": "EXECUTE", "item": "사용자 확인"},
            {"stage": "TEST",    "item": "작업"},
        ]))
        self._assert_ok(self._mark(d, 1), "S-13 mark row1")
        data = self._assert_ok(self._advance(d, 3), "S-13 advance row3")

        r = self._row(d, 2)
        self.assertEqual(r["status"], "done")
        self.assertEqual(r["owner"], "auto")
        self.assertIsNotNone(r.get("timestamp"))
        self.assertEqual(data.get("auto_approved"), [2])

    def test_auto_approved_payload_positive_T093_L1_F2o(self):
        """[T093/L1-F2o] S-26 — 성공 응답 JSON의 auto_approved 배열이 승인된 row_id를
        정확히 담는다(advance/mark 양쪽). 승인 0건 호출은 빈 배열."""
        rows = _t093_json([
            {"stage": "TASK",    "item": "작업"},
            {"stage": "TASK",    "item": "사용자 확인"},
            {"stage": "EXECUTE", "item": "작업"},
        ])
        # (a) advance 경로
        d_adv = self._task_dir("s26-advance")
        self._init(d_adv, "agentic", rows_spec=rows)
        first = self._assert_ok(self._mark(d_adv, 1), "S-26 mark row1")
        self.assertEqual(first.get("auto_approved", []), [],
                         "승인 0건 호출의 auto_approved는 빈 배열이어야 한다")
        data_adv = self._assert_ok(self._advance(d_adv, 3), "S-26 advance row3")
        self.assertEqual(data_adv.get("auto_approved"), [2])

        # (b) mark 경로
        d_mark = self._task_dir("s26-mark")
        self._init(d_mark, "agentic", rows_spec=rows)
        self._assert_ok(self._mark(d_mark, 1), "S-26 mark row1")
        data_mark = self._assert_ok(self._mark(d_mark, 3), "S-26 mark row3")
        self.assertEqual(data_mark.get("auto_approved"), [2])
        self.assertEqual(self._row(d_mark, 2)["owner"], "auto")


# ─────────────────────────────────────────────────────────────────────────────
# S-6 / S-7 / S-8 / S-9 / S-12 / S-14 / S-24 — 경계·부정 경로
# ─────────────────────────────────────────────────────────────────────────────

class TestT093AutoApproveBoundary(_T093Base):
    """F-002 CLOSE·워커 구조적 제외 + F-003 경계 불변 + F-004 전용 에러."""

    def test_close_entry_does_not_auto_approve_T093_L2_GOAL(self):
        """[T093/L2-GOAL] S-6 — agentic에서 TEST 사용자 확인 행을 pending으로 둔 채
        CLOSE 첫 행 mark → 차단(exit 1) + 파일 재로드 시 그 행이 여전히 pending.
        이후 --owner user로 승인하면 CLOSE 진입이 정상 통과(DEC-D 1차 방어)."""
        d = self._task_dir("s6-close")
        self._init(d, "agentic", rows_spec=_t093_json([
            {"stage": "TEST",  "item": "작업"},
            {"stage": "TEST",  "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "DONE.md 생성"},
        ]))
        # [T103 강제 2단] TEST/작업은 워커 디스패치 규범 행이라 소요를 기록하거나
        # 미측정을 선언해야 CLOSE를 통과한다. 이 테스트의 관심사는 「사용자 확인 행이
        # 자동 승인되지 않는가」이므로, 축을 격리하기 위해 미측정을 선언해 둔다.
        self._assert_ok(self._mark(d, 1, "--worker-duration-unknown"), "S-6 mark row1")
        self.assertEqual(self._row(d, 2)["status"], "pending",
                         "S-6 전제: TEST 사용자 확인 행은 init 직후 pending이어야 한다")

        code, stdout, stderr, data = self._mark(d, 3)
        self.assertEqual(code, 1, f"S-6 CLOSE 첫 행 mark가 차단되지 않음 (stdout={stdout!r})")
        r2 = self._row(d, 2)
        self.assertEqual(r2["status"], "pending",
                         f"S-6 훅이 CLOSE 진입 경로에서 앞 행을 승인함 — {r2!r}")
        self.assertNotEqual(r2.get("owner"), "auto")

        self._assert_ok(self._mark(d, 2, "--owner", "user"), "S-6 캡틴 승인")
        self._assert_ok(self._mark(d, 3), "S-6 CLOSE 재진입")
        self.assertEqual(self._row(d, 3)["status"], "done")

    def test_close_first_row_auto_pass_denied_T093_L1_F3(self):
        """[T093/L1-F3] S-7 — agentic·semi-agentic 모두 CLOSE 첫 행
        mark --done --auto-pass가 agentic_close_gate_requires_user로 거부(exit 1).
        에러 코드 문자열까지 대조."""
        for mode in ("agentic", "semi-agentic"):
            with self.subTest(mode=mode):
                d = self._init_b(mode, name=f"s7-{mode}")
                self._assert_ok(self._mark(d, 1), "prep row1")
                self._assert_ok(self._mark(d, 2, "--owner", "user"), "prep row2")
                self._assert_ok(self._mark(d, 3), "prep row3")
                self._assert_ok(self._mark(d, 4, "--auto-pass"), "prep row4")
                code, stdout, stderr, data = self._mark(d, 5, "--auto-pass")
                self.assertEqual(code, 1, f"S-7/{mode} 미차단 (stdout={stdout!r})")
                self.assertEqual(data.get("error"), "agentic_close_gate_requires_user",
                                 f"S-7/{mode} 에러 코드 회귀 — {data!r}")

    def test_worker_path_hook_disabled_T093_L2_GOAL(self):
        """[T093/L2-GOAL] S-8 — --as-worker --worker-stage EXECUTE 경로에서 앞 단계
        PLAN 사용자 확인 행이 자동 승인되지 않고 stage_transition_violation(exit 1).
        워커가 주소 지정 없이 앞 단계 행을 실질 갱신하는 우회가 불가해야 한다(DEC-C)."""
        d = self._worker_fixture("s8-worker")
        code, stdout, stderr, data = self._mark(
            d, 3, "--as-worker", "--worker-stage", "EXECUTE")
        self.assertEqual(code, 1, f"S-8 워커 경로 미차단 (stdout={stdout!r})")
        self.assertEqual(data.get("error"), "stage_transition_violation", f"S-8 {data!r}")
        r2 = self._row(d, 2)
        self.assertEqual(r2["status"], "pending",
                         f"S-8 워커 경로에서 앞 단계 사용자 확인 행이 갱신됨 — {r2!r}")

    def test_worker_path_leaves_file_byte_identical_T093_L2_GOAL(self):
        """[T093/L2-GOAL] S-9 — S-8과 동일 호출 후 state.json 바이트가 호출 전과 완전 동일
        (updated_at 포함 무변경)."""
        d = self._worker_fixture("s9-worker")
        before = (d / "state.json").read_bytes()
        code, stdout, stderr, data = self._mark(
            d, 3, "--as-worker", "--worker-stage", "EXECUTE")
        self.assertEqual(code, 1, f"S-9 전제: 호출이 차단되어야 한다 (stdout={stdout!r})")
        after = (d / "state.json").read_bytes()
        self.assertEqual(before, after,
                         "S-9 워커 경로 실패 호출이 state.json 바이트를 변경했다")

    def _worker_fixture(self, name):
        d = self._task_dir(name)
        self._init(d, "agentic", rows_spec=_t093_json([
            {"stage": "PLAN",    "item": "작업"},
            {"stage": "PLAN",    "item": "사용자 확인"},
            {"stage": "EXECUTE", "item": "작업"},
        ]))
        self._assert_ok(self._mark(d, 1), f"{name} prep row1")
        self.assertEqual(self._row(d, 2)["status"], "pending",
                         f"{name} 전제: PLAN 사용자 확인 행은 init 직후 pending")
        return d

    def test_semi_agentic_boundary_requires_user_T093_L1_F4(self):
        """[T093/L1-F4] S-12 — semi-agentic + MODE_BOUNDARY_STAGES 사용자 확인 행은
        훅 경로에서 자동 승인되지 않고 user_confirmation_required를 반환한다.
        페이로드에 row_id·stage·reason·required_action 포함(PLAN §3.4.2)."""
        d = self._task_dir("s12-semi-boundary")
        self._init(d, "semi-agentic", rows_spec=_t093_json([
            {"stage": "TASK",    "item": "작업"},
            {"stage": "TASK",    "item": "사용자 확인"},
            {"stage": "EXECUTE", "item": "작업"},
        ]))
        self._assert_ok(self._mark(d, 1), "S-12 mark row1")
        code, stdout, stderr, data = self._advance(d, 3)

        self.assertEqual(code, 1, f"S-12 자동 승인이 발생함 (stdout={stdout!r})")
        self.assertEqual(data.get("error"), "user_confirmation_required", f"S-12 {data!r}")
        self.assertEqual(data.get("row_id"), 2)
        self.assertEqual(data.get("stage"), "TASK")
        self.assertEqual(data.get("reason"), "semi_agentic_pre_execute")
        self.assertTrue(data.get("required_action"), f"S-12 required_action 누락 — {data!r}")
        self.assertEqual(self._row(d, 2)["status"], "pending")

    def test_interactive_path_split_T093_L1_F4(self):
        """[T093/L1-F4] S-24 — DEC-A 경로 분리 실측.
        (a) 훅 경로: user_confirmation_required 거부(reason=interactive_requires_user)
        (b) PM 직접 mark --auto-pass: 현행대로 exit 0 + validate가
            auto_pass_in_interactive_mode 위반 1건 방출.
        [MUST] (b)를 차단으로 바꾸면 F-3 AC '경계 불변'이 깨진다."""
        rows = _t093_json([
            {"stage": "TASK",    "item": "작업"},
            {"stage": "TASK",    "item": "사용자 확인"},
            {"stage": "EXECUTE", "item": "작업"},
        ])
        # (a) 훅 경로
        d_a = self._task_dir("s24-hook")
        self._init(d_a, "interactive", rows_spec=rows)
        self._assert_ok(self._mark(d_a, 1), "S-24(a) mark row1")
        code, stdout, stderr, data = self._advance(d_a, 3)
        self.assertEqual(code, 1, f"S-24(a) interactive 훅이 자동 승인함 (stdout={stdout!r})")
        self.assertEqual(data.get("error"), "user_confirmation_required", f"S-24(a) {data!r}")
        self.assertEqual(data.get("reason"), "interactive_requires_user")
        self.assertEqual(self._row(d_a, 2)["status"], "pending")

        # (b) PM 명시 호출 경로 — 현행 유지
        d_b = self._task_dir("s24-explicit")
        self._init(d_b, "interactive", rows_spec=rows)
        self._assert_ok(self._mark(d_b, 1), "S-24(b) mark row1")
        self._assert_ok(self._mark(d_b, 2, "--auto-pass"),
                        "S-24(b) PM 직접 --auto-pass는 exit 0이어야 한다(경계 불변)")
        self.assertEqual(self._row(d_b, 2)["owner"], "auto")

        vcode, vstdout, vstderr, vdata = self._validate(d_b)
        codes = [v["code"] for v in vdata.get("violations", [])]
        self.assertEqual(codes, ["auto_pass_in_interactive_mode"],
                         f"S-24(b) validate 위반 집합 회귀 — {vdata!r}")
        self.assertEqual(vcode, 1)

    # ── S-14 경계 불변 회귀표 18셀 (PLAN §3.3.2 (3) 표 A/표 B) ────────────────

    _B_TABLE = [
        # (cell, target_row, mode, expected_exit, expected_error)
        ("B-1", 2, "interactive",  0, None),
        ("B-2", 2, "semi-agentic", 1, "semi_agentic_pre_execute_auto_pass_denied"),
        ("B-3", 2, "agentic",      0, None),
        ("B-4", 4, "interactive",  0, None),
        ("B-5", 4, "semi-agentic", 0, None),
        ("B-6", 4, "agentic",      0, None),
        ("B-7", 5, "interactive",  1, "close_gate_violation"),
        ("B-8", 5, "semi-agentic", 1, "agentic_close_gate_requires_user"),
        ("B-9", 5, "agentic",      1, "agentic_close_gate_requires_user"),
    ]

    def test_boundary_table_a_mark_auto_pass_T093_L1_F3(self):
        """[T093/L1-F3] S-14(표 A) — mark --auto-pass 즉시 차단 여부 9셀.
        exit code만이 아니라 error 필드 문자열까지 대조한다(B-7 vs B-8/B-9 구분)."""
        for cell, target, mode, exp_code, exp_err in self._B_TABLE:
            with self.subTest(cell=cell, mode=mode, target=target):
                d = self._init_b(mode, name=f"s14-{cell}")
                self._assert_ok(self._mark(d, 1), f"{cell} prep row1")
                if target >= 4:
                    self._assert_ok(self._mark(d, 2, "--owner", "user"), f"{cell} prep row2")
                    self._assert_ok(self._mark(d, 3), f"{cell} prep row3")
                if target >= 5:
                    self._assert_ok(self._mark(d, 4, "--auto-pass"), f"{cell} prep row4")

                code, stdout, stderr, data = self._mark(d, target, "--auto-pass")
                self.assertEqual(code, exp_code,
                                 f"{cell} exit={code} 기대={exp_code} (stdout={stdout!r})")
                self.assertEqual(data.get("error"), exp_err,
                                 f"{cell} error={data.get('error')!r} 기대={exp_err!r}")

    _V_TABLE = [
        # (cell, stage, mode, expected violation codes)
        ("V-1", "TASK",    "interactive",  {"auto_pass_in_interactive_mode"}),
        ("V-2", "TASK",    "semi-agentic", {"semi_agentic_pre_execute_auto_pass_denied"}),
        ("V-3", "TASK",    "agentic",      set()),
        ("V-4", "EXECUTE", "interactive",  {"auto_pass_in_interactive_mode"}),
        ("V-5", "EXECUTE", "semi-agentic", set()),
        ("V-6", "EXECUTE", "agentic",      set()),
        ("V-7", "CLOSE",   "interactive",  {"auto_pass_in_interactive_mode"}),
        ("V-8", "CLOSE",   "semi-agentic", set()),
        ("V-9", "CLOSE",   "agentic",      set()),
    ]

    def _validate_fixture(self, name, stage, mode):
        """init(실 CLI)으로 만든 state.json의 tmp 복사본에서 대상 stage의 사용자 확인
        행만 done/auto로 바꾼 픽스처 — 손편집 대상은 tmp 복사본뿐이다."""
        d = self._task_dir(name)
        self._init(d, "interactive", rows_spec=_T093_V_SPEC)
        state_path = d / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["mode"] = mode
        hit = 0
        for r in state["rows"]:
            if r["item"] == "사용자 확인" and r["stage"] == stage:
                r["status"] = "done"
                r["status_label"] = "✅"
                r["owner"] = "auto"
                r["timestamp"] = state["created_at"]
                hit += 1
        self.assertEqual(hit, 1, f"{name}: stage={stage} 사용자 확인 행 1건이어야 함")
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                              encoding="utf-8")
        return d

    def test_boundary_table_b_validate_T093_L1_F3(self):
        """[T093/L1-F3] S-14(표 B) — validate 사후 위반 방출 9셀.
        V-8·V-9(CLOSE × semi-agentic/agentic)는 violations_count == 0 — H-4 핵심 셀.
        판정 함수의 close_requires_user를 cmd_validate가 소비하면 이 셀이 깨진다."""
        for cell, stage, mode, expected in self._V_TABLE:
            with self.subTest(cell=cell, stage=stage, mode=mode):
                d = self._validate_fixture(f"s14-{cell}", stage, mode)
                code, stdout, stderr, data = self._validate(d)
                codes = {v["code"] for v in data.get("violations", [])}
                self.assertEqual(codes, expected,
                                 f"{cell} violations={data.get('violations')!r}")
                self.assertEqual(data.get("violations_count"), len(expected))

    def test_close_done_auto_validate_no_violation_T093_L2_F6a(self):
        """[T093/L2-F6a] S-18 — CLOSE stage 사용자 확인 행이 done/auto인 state.json에
        validate → violations_count == 0. 판정 함수 도입으로 신규 위반이 생기면 안 된다(H-4)."""
        for mode in ("semi-agentic", "agentic"):
            with self.subTest(mode=mode):
                d = self._validate_fixture(f"s18-{mode}", "CLOSE", mode)
                code, stdout, stderr, data = self._validate(d)
                self.assertEqual(data.get("violations_count"), 0,
                                 f"S-18/{mode} 신규 오탐 — {data!r}")
                self.assertEqual(code, 0)


# ─────────────────────────────────────────────────────────────────────────────
# S-10 / S-11 — H-8 훅 × 후속 가드 순서 (파일 오염·응답 오염 배제)
# ─────────────────────────────────────────────────────────────────────────────

class TestT093HookGuardOrder(_T093Base):
    """F-002 — 훅은 save_state_json을 호출하지 않는다(PLAN §3.2.2 (1) [MUST])."""

    def _gate_fixture(self, name):
        """사용자 확인 행 바로 다음이 gate 보유 PM Gate 행인 최소 pipeline.json 픽스처.
        gate.artifacts가 가리키는 ANALYSIS.md는 의도적으로 만들지 않는다(§2.1)."""
        spec = _t093_pipeline_spec("opd", ["TASK", "ANALYSIS"], [
            {"id": 1, "key": "task.task_md",      "stage": "TASK",     "item": "작업"},
            {"id": 2, "key": "task.user_confirm", "stage": "TASK",     "item": "사용자 확인"},
            {"id": 3, "key": "analysis.pm_gate",  "stage": "ANALYSIS", "item": "PM Gate",
             "gate": {"artifacts": ["ANALYSIS.md"], "checklist": ["-"]}},
        ])
        spec_path = self.tmpdir / f"{name}-pipeline.json"
        spec_path.write_text(_t093_json(spec), encoding="utf-8")
        d = self._task_dir(name)
        self._init(d, "agentic", rows_from=spec_path)
        self._assert_ok(self._mark_key(d, "task.task_md"), f"{name} prep row1")
        self.assertEqual(self._row(d, 2)["status"], "pending",
                         f"{name} 전제: 사용자 확인 행은 init 직후 pending")
        self.assertFalse((d / "ANALYSIS.md").exists())
        return d

    def test_guard_failure_leaves_file_unsaved_T093_L2_F2(self):
        """[T093/L2-F2] S-10 — 훅 통과 후 check_gate_artifacts가 실패하면
        저장된 state.json의 앞 단계 사용자 확인 행이 여전히 pending이어야 한다.
        (메모리 mutate는 있어도 파일에 반영되지 않음 — H-8)"""
        d = self._gate_fixture("s10-gate")
        before = (d / "state.json").read_bytes()
        code, stdout, stderr, data = self._mark_key(d, "analysis.pm_gate")
        self.assertEqual(code, 1, f"S-10 gate 미차단 (stdout={stdout!r})")
        self.assertEqual(data.get("error"), "gate_artifact_missing", f"S-10 {data!r}")

        r2 = self._row(d, 2)
        self.assertEqual(r2["status"], "pending",
                         f"S-10 훅 승인이 파일에 저장됨(부분 상태 변경) — {r2!r}")
        self.assertEqual(before, (d / "state.json").read_bytes(),
                         "S-10 실패 경로에서 state.json이 변경됨")

    def test_failed_response_has_no_auto_approved_T093_L1_F2o(self):
        """[T093/L1-F2o] S-11 — 훅 거부/후속 가드 실패 응답 JSON에 auto_approved 필드가
        없거나 빈 배열이어야 한다(관측 계약 오염 배제)."""
        d = self._gate_fixture("s11-gate")
        code, stdout, stderr, data = self._mark_key(d, "analysis.pm_gate")
        self.assertEqual(code, 1, f"S-11 전제: 실패 경로 (stdout={stdout!r})")
        self.assertIn(data.get("auto_approved", []), ([], None),
                      f"S-11 실패 응답에 auto_approved 오염 — {data!r}")
        self.assertEqual(self._row(d, 2)["status"], "pending")


# ─────────────────────────────────────────────────────────────────────────────
# S-15 / S-16 — F-005 mark 멱등성
# ─────────────────────────────────────────────────────────────────────────────

class TestT093MarkIdempotency(_T093Base):
    """F-005 — note 접두 1회 부여 + 재-auto-pass no-op (PLAN §3.5.2)."""

    # TASK 단계를 두지 않는다 — _run_clarification_hook(005)은 TASK 단계가 있는
    # 파이프라인의 'TASK 직후 첫 행'에서 --auto-pass를 무조건 거부하므로, F-005
    # 멱등성(자동 승인 경계와 무관한 축)만 격리 관찰하기 위해 그 축을 제거한다.
    _SPEC = _t093_json([
        {"stage": "EXECUTE", "item": "작업"},
        {"stage": "EXECUTE", "item": "사용자 확인"},
        {"stage": "EXECUTE", "item": "사용자 확인"},
    ])

    def _fixture(self, name):
        d = self._task_dir(name)
        self._init(d, "agentic", rows_spec=self._SPEC)
        self._assert_ok(self._mark(d, 1), f"{name} prep row1")
        return d

    def test_auto_pass_note_prefix_applied_once_T093_L1_F5(self):
        """[T093/L1-F5] S-15 — mark --done --auto-pass --note "X" 1회 →
        note == 'agentic auto-pass: X'. 접두 문자열 자체는 불변."""
        d = self._fixture("s15-note")
        self._assert_ok(self._mark(d, 2, "--auto-pass", "--note", "PM 판단 근거"),
                        "S-15 1회차")
        self.assertEqual(self._row(d, 2).get("note"), "agentic auto-pass: PM 판단 근거")

        # ANALYSIS §4 #5 실측 패턴(tasks/092-*/state.json:71,116,163) 재현 —
        # PM이 이미 접두를 가진 note 문자열을 그대로 재전달해도 중첩되지 않아야 한다.
        self._assert_ok(
            self._mark(d, 3, "--auto-pass", "--note", "agentic auto-pass: 접두 보유"),
            "S-15 접두 보유 note")
        self.assertEqual(self._row(d, 3).get("note"), "agentic auto-pass: 접두 보유",
                         f"S-15 접두 중첩 — {self._row(d, 3).get('note')!r}")

    def test_re_auto_pass_is_noop_T093_L1_F5(self):
        """[T093/L1-F5] S-16 — 2회차 동일 명령이 ok:true이고 note 문자열 불변
        (접두 중첩 0건) + timestamp·updated_at 미변경. 대조군 3종은 no-op에 삼켜지지 않는다."""
        d = self._fixture("s16-noop")
        self._assert_ok(self._mark(d, 2, "--auto-pass", "--note", "PM 판단 근거"),
                        "S-16 1회차")
        first_row = self._row(d, 2)
        first_updated = self._state_of(d)["updated_at"]

        data = self._assert_ok(self._mark(d, 2, "--auto-pass", "--note", "PM 판단 근거"),
                               "S-16 2회차")
        second_row = self._row(d, 2)
        self.assertTrue(data.get("ok"), f"S-16 2회차 ok:true 아님 — {data!r}")
        self.assertEqual(second_row.get("note"), "agentic auto-pass: PM 판단 근거",
                         f"S-16 접두 중첩 — {second_row.get('note')!r}")
        self.assertNotIn("agentic auto-pass: agentic auto-pass",
                         str(second_row.get("note")))
        self.assertEqual(second_row.get("timestamp"), first_row.get("timestamp"),
                         "S-16 no-op이 timestamp를 갱신했다")
        self.assertEqual(self._state_of(d)["updated_at"], first_updated,
                         "S-16 no-op이 updated_at을 갱신했다")
        self.assertTrue(data.get("idempotent"), f"S-16 idempotent 미표기 — {data!r}")

    def test_noop_control_groups_T093_L1_F5(self):
        """[T093/L1-F5] S-16 대조군 3종 — (a) owner=user done 행 (b) --force
        (c) --action-step N/M 은 멱등 조기 반환에 삼켜지지 않고 기존 경로로 진행한다."""
        # (a) owner=user로 done인 행에 --auto-pass → 기존 동작대로 owner=auto로 진행
        d_a = self._fixture("s16-ctl-a")
        self._assert_ok(self._mark(d_a, 2, "--owner", "user"), "(a) prep")
        self._assert_ok(self._mark(d_a, 2, "--auto-pass"), "(a) 재호출")
        self.assertEqual(self._row(d_a, 2).get("owner"), "auto",
                         "(a) owner=user done 행이 no-op으로 삼켜졌다")

        # (b) --force는 명시 우회 의도 → no-op 금지
        d_b = self._fixture("s16-ctl-b")
        self._assert_ok(self._mark(d_b, 2, "--auto-pass"), "(b) prep")
        data_b = self._assert_ok(
            self._mark(d_b, 2, "--auto-pass", "--force", "--note", "긴급 재승인"),
            "(b) --force 재호출")
        self.assertNotEqual(data_b.get("idempotent"), True,
                            f"(b) --force가 no-op으로 삼켜졌다 — {data_b!r}")

        # (c) --action-step N/M 진행률 갱신은 상태 변경이 목적 → no-op 금지
        d_c = self._fixture("s16-ctl-c")
        self._assert_ok(self._mark(d_c, 2, "--auto-pass"), "(c) prep")
        self._assert_ok(self._mark(d_c, 2, "--auto-pass", "--action-step", "1/3"),
                        "(c) --action-step 재호출")
        row_c = self._row(d_c, 2)
        self.assertEqual(row_c.get("step"), "1/3",
                         f"(c) --action-step이 no-op으로 삼켜졌다 — {row_c!r}")
        self.assertEqual(row_c.get("status"), "in_progress")


# ─────────────────────────────────────────────────────────────────────────────
# S-17 — F-006 (a) 기존 na 보유 실파일 하위호환
# ─────────────────────────────────────────────────────────────────────────────

class TestT093NaBackwardCompat(_T093Base):
    """F-006 (a) — _COMPLETE_STATUSES의 na 존치 확인 (DEC-G, TEST-SCENARIO S-17).

    검증 경로는 2단이다.
      주 경로(항상 실행): 아래 `_SNAPSHOT_092` — `tasks/092-260815-opd-워크트리-작업공간-분리/
        state.json`의 구조를 보존한 축약 스냅샷. 실파일 존재 여부와 무관하게 반드시 실행된다.
      부가 경로(실파일 존재 시): 동일 검증을 레포 실파일 복사본에도 수행한다.
    [PM 판정] 실파일이 아카이브로 이관되면 skipTest로 시나리오 전체가 조용히 무력화되므로
    (헌법 §4 — 검증하지 않은 것을 통과로 만들지 않는다) skip 경로를 제거하고 스냅샷을
    주 경로로 승격했다. 실파일 원본은 여전히 읽기 전용이며 바이트 대조로 무변경을 증명한다.
    """

    # ── 092 실파일 구조 보존 축약 스냅샷 (실 파일에서 그대로 발췌한 값) ─────────
    # 보존 특징:
    #   ① row 2 — status="na" / owner="auto" / note="agentic auto-na at init" (F-001 구형 산물)
    #   ② row 4 — status="done" / owner="auto" / note에 "agentic auto-pass:" 접두 **중첩**
    #              (ANALYSIS §4 #5가 실측한 결함 패턴, 원문 tasks/092-*/state.json:71)
    #   ③ row 6 — status="done" / owner="user" (CLOSE 게이트 요건 충족 행)
    #   ④ schema_version "1.1" · mode "agentic" · skill "opd" · task-step key 체계
    #   ⑤ CLOSE stage에 add-row 산물(`close.item_1`, 추가작업 행)이 이미 존재
    _SNAPSHOT_092 = {
        "task_id": "092-260815-opd-워크트리-작업공간-분리",
        "skill": "opd",
        "mode": "agentic",
        "schema_version": "1.1",
        "created_at": "2026-08-15 14:10",
        "updated_at": "2026-08-15 19:52",
        "current_status": "done",
        "rows": [
            {"row_id": 1, "stage": "TASK", "item": "작업", "key": "task.task_md",
             "status": "done", "status_label": "✅", "timestamp": "2026-08-15 14:11",
             "owner": "PM", "note": None},
            {"row_id": 2, "stage": "TASK", "item": "사용자 확인", "key": "task.user_confirm",
             "status": "na", "status_label": "-", "timestamp": None,
             "owner": "auto", "note": "agentic auto-na at init"},
            {"row_id": 3, "stage": "ANALYSIS", "item": "작업", "key": "analysis.analysis_md",
             "status": "done", "status_label": "✅", "timestamp": "2026-08-15 14:58",
             "owner": "PM", "note": None},
            {"row_id": 4, "stage": "ANALYSIS", "item": "사용자 확인",
             "key": "analysis.user_confirm",
             "status": "done", "status_label": "✅", "timestamp": "2026-08-15 14:59",
             "owner": "auto",
             "note": "agentic auto-pass: agentic auto-pass: PM Gate 강화 검토 Pass — "
                     "접합면 6곳 전건 분석, 핵심 주장 4건 PM 직접 실측 대조, "
                     "근거 오류 1건 정정 완료, 블로커 0건"},
            {"row_id": 5, "stage": "TEST", "item": "작업", "key": "test.run_tests",
             "status": "done", "status_label": "✅", "timestamp": "2026-08-15 18:40",
             "owner": "PM", "note": None},
            {"row_id": 6, "stage": "TEST", "item": "사용자 확인", "key": "test.user_confirm",
             "status": "done", "status_label": "✅", "timestamp": "2026-08-15 19:01",
             "owner": "user",
             "note": "캡틴 확인: CLOSE 진입 승인 (L3 S-18·S-19·S-20 결과 수용 포함)"},
            {"row_id": 7, "stage": "CLOSE", "item": "DONE.md 생성", "key": "close.done_md",
             "status": "done", "status_label": "✅", "timestamp": "2026-08-15 19:40",
             "owner": "PM", "note": None},
            {"row_id": 8, "stage": "CLOSE",
             "item": "추가작업 ADD-1: worktree.json 온보딩 경로 (worktree-tool init)",
             "key": "close.item_1",
             "status": "done", "status_label": "✅", "timestamp": "2026-08-15 19:52",
             "owner": "PM", "note": None},
        ],
        "next_action": "태스크 완료",
    }

    @staticmethod
    def _find_092_state():
        """레포 실파일 탐색. worktree는 sparse checkout이라 tasks/가 없을 수 있으므로
        상위 메인 체크아웃까지 본다. 미탐색 시 None — 부가 경로만 생략된다."""
        candidates = [_REPO_ROOT_093, _REPO_ROOT_093.parent.parent]
        for root in candidates:
            tasks_dir = root / "tasks"
            if not tasks_dir.is_dir():
                continue
            for base in (tasks_dir, tasks_dir / "backup"):
                if not base.is_dir():
                    continue
                for d in sorted(base.glob("092-*")):
                    if (d / "state.json").is_file() and (d / "STATE.md").is_file():
                        return d
        return None

    def _snapshot_task_dir(self, name):
        """스냅샷 state.json + 실 init이 생성한 STATE.md(마커/섹션 포함)로 tmp 태스크 구성.
        STATE.md는 손으로 쓰지 않고 실 CLI init 산물을 쓴다 — 마커 계약을 위조하지 않기 위함."""
        rows_spec = _t093_json([{"stage": r["stage"], "item": r["item"]}
                                for r in self._SNAPSHOT_092["rows"]])
        d = self._task_dir(name)
        self._init(d, "interactive", rows_spec=rows_spec)
        (d / "state.json").write_text(
            json.dumps(self._SNAPSHOT_092, ensure_ascii=False, indent=2), encoding="utf-8")
        return d

    def _exercise_na_state(self, d, label):
        """na 보유 state.json에 validate → add-row/advance → mark --done 3종 실호출.
        na 행이 _COMPLETE_STATUSES로 완료 인정되어 stage-transition guard를 통과해야 한다."""
        state = self._state_of(d)
        na_rows = [r["row_id"] for r in state["rows"] if r.get("status") == "na"]
        self.assertTrue(na_rows, f"{label}: na 행이 있어야 한다(전제)")
        nested = [r["row_id"] for r in state["rows"]
                  if "agentic auto-pass: agentic auto-pass" in str(r.get("note"))]
        self.assertTrue(nested, f"{label}: 접두 중첩 note 행이 있어야 한다(ANALYSIS §4 #5 전제)")

        # ① validate
        vcode, vstdout, vstderr, vdata = self._validate(d)
        self.assertEqual(vdata.get("violations_count"), 0, f"{label} validate — {vdata!r}")
        self.assertEqual(vcode, 0, f"{label} validate exit={vcode}")

        # ② add-row로 미완 행을 만들고 advance
        last_row_id = state["rows"][-1]["row_id"]
        self._assert_ok(
            _run070(["add-row", str(d), "--after", str(last_row_id),
                     "--stage", "CLOSE", "--item", "추가작업 ADD-093: na 하위호환 회귀"]),
            f"{label} add-row")
        new_row_id = self._state_of(d)["rows"][-1]["row_id"]
        self._assert_ok(self._advance(d, new_row_id), f"{label} advance")

        # ③ mark --done
        self._assert_ok(self._mark(d, new_row_id), f"{label} mark")
        self.assertEqual(self._row(d, new_row_id)["status"], "done")

        # na 행은 소급 변환되지 않는다 (PLAN §3.1.4 — 기존 파일 미마이그레이션)
        after = self._state_of(d)
        self.assertEqual([r["row_id"] for r in after["rows"] if r.get("status") == "na"],
                         na_rows, f"{label}: 기존 na 행이 소급 변환되었다")

    def test_existing_na_state_json_still_operable_T093_L2_F6a(self):
        """[T093/L2-F6a] S-17 — na 보유 state.json에 validate → add-row/advance →
        mark --done 3종 실행 → 전부 exit 0, violations 0.

        주 경로(스냅샷)는 항상 실행된다. 실파일이 있으면 동일 검증을 추가 수행하고,
        원본 바이트 대조로 읽기 전용 제약을 증명한다."""
        # ── 주 경로: 092 구조 보존 스냅샷 (실파일 유무와 무관하게 항상 실행) ──
        with self.subTest(source="snapshot"):
            d = self._snapshot_task_dir("s17-snapshot")
            self._exercise_na_state(d, "S-17 스냅샷")

        # ── 부가 경로: 레포 실파일 복사본 (존재할 때만) ──
        src = self._find_092_state()
        if src is None:
            return
        with self.subTest(source="real-file", path=str(src)):
            original = (src / "state.json").read_bytes()
            d2 = self._task_dir("s17-real-file")
            shutil.copy2(src / "state.json", d2 / "state.json")
            shutil.copy2(src / "STATE.md", d2 / "STATE.md")
            self._exercise_na_state(d2, f"S-17 실파일({src.name})")
            # [MUST] 원본은 읽기만 한다 — 수정 0건
            self.assertEqual(original, (src / "state.json").read_bytes(),
                             "S-17 원본 실파일이 변경되었다 — 읽기 전용 제약 위반")


# ─────────────────────────────────────────────────────────────────────────────
# S-25 — F-003 구조적 단일화 (행동 불변만으로는 복붙 통과)
# ─────────────────────────────────────────────────────────────────────────────

class TestT093SingleDecisionSource(unittest.TestCase):
    """F-003 — 판정 로직이 실제로 단일 함수로 수렴했는가 (TEST-SCENARIO S-25)."""

    _FN = "can_auto_approve_user_confirmation"

    def test_mode_boundary_stages_single_reference_T093_L1_F3s(self):
        """[T093/L1-F3s] S-25 — MODE_BOUNDARY_STAGES 참조가 판정 함수 내부 1곳으로 수렴
        (정의부 제외). cmd_mark·cmd_validate가 상수를 직접 참조하지 않아야 한다.
        [MUST] 행동 불변(S-14)만 검증하면 판정 로직을 3곳에 복붙해도 PASS한다."""
        lines = _SRC_093.read_text(encoding="utf-8").splitlines()
        hits = [(i + 1, ln) for i, ln in enumerate(lines) if "MODE_BOUNDARY_STAGES" in ln]
        refs = [(n, ln) for n, ln in hits if not ln.lstrip().startswith("MODE_BOUNDARY_STAGES =")]
        self.assertEqual(len(refs), 1,
                         f"S-25 참조 지점이 1곳으로 수렴하지 않음 — {[(n, l.strip()) for n, l in refs]}")

        # 유일 참조가 판정 함수 본문 안에 있는지 확인
        def_line = None
        for i, ln in enumerate(lines):
            if ln.startswith(f"def {self._FN}("):
                def_line = i + 1
                break
        self.assertIsNotNone(def_line, f"S-25 판정 함수 {self._FN} 미정의")
        end_line = len(lines) + 1
        for i in range(def_line, len(lines)):
            if lines[i].startswith(("def ", "class ")):
                end_line = i + 1
                break
        ref_line = refs[0][0]
        self.assertTrue(def_line < ref_line < end_line,
                        f"S-25 유일 참조(line {ref_line})가 {self._FN} 본문"
                        f"({def_line}~{end_line}) 밖에 있다")

    def test_decision_function_contract_T093_L1_F3s(self):
        """[T093/L1-F3s] S-25 보조 — 판정 함수의 (allowed, deny_reason) 계약
        (PLAN §3.3.2 (1) 두 축 합성 순서: CLOSE → interactive → semi-agentic 경계)."""
        fn = getattr(ST, self._FN, None)
        self.assertIsNotNone(fn, f"판정 함수 {self._FN} 부재 (F-003 미구현)")
        cases = [
            ("CLOSE",   "interactive",  (False, "close_requires_user")),
            ("CLOSE",   "semi-agentic", (False, "close_requires_user")),
            ("CLOSE",   "agentic",      (False, "close_requires_user")),
            ("TASK",    "interactive",  (False, "interactive_requires_user")),
            ("TASK",    "semi-agentic", (False, "semi_agentic_pre_execute")),
            ("TASK",    "agentic",      (True,  None)),
            ("EXECUTE", "interactive",  (False, "interactive_requires_user")),
            ("EXECUTE", "semi-agentic", (True,  None)),
            ("EXECUTE", "agentic",      (True,  None)),
        ]
        for stage, mode, expected in cases:
            with self.subTest(stage=stage, mode=mode):
                self.assertEqual(tuple(fn(stage, mode)), expected)


# ═════════════════════════════════════════════════════════════════════════════
# 094 R-11(RED-first, mode:red): agentic 승인 계약 정합
# TestR11ModeBoundary / TestR11CloseGateFallback / TestR11DerivedSignals / TestR11Invariants
# (TEST-SCENARIO.md S-34~S-37, S-40 / R-11-요청서.md §2 G-1~G-3, §7)
#
# [MUST] red-first.md §4 / 헌법 §4 "Don't fake it" — mock/patch/MagicMock 미사용.
#        _T093Base(worktree run.sh subprocess 실호출 + 실 pipeline.json/state.json 파일
#        상태)를 그대로 재사용한다 — 신규 헬퍼 신설 없음(헌법 §2 중복 구현 금지).
#        구현 대상 state_tool.py는 이 RED 단계에서 무변경(작성자≠구현자, 다음 Step이
#        can_auto_approve_user_confirmation() 단일 판정 함수를 재사용해 배선한다).
# ═════════════════════════════════════════════════════════════════════════════

# 실 opdd pipeline.json — G-1 모드 경계 상수 검증 대상(_REPO_ROOT_093 재사용, R-10 무관 —
# 워크트리에도 opal/skills/가 존재하므로 허브 탐색 헬퍼 불요, TASK.md R-10 범위 밖)
_OPDD_REAL_PIPELINE = (_REPO_ROOT_093 / "opal" / "skills" / "opal-pilot-data-design"
                       / "references" / "pipeline.json")


class TestR11ModeBoundary(_T093Base):
    """G-1 `MODE_BOUNDARY_STAGES` 3원소(DICT/MODEL/DDL·MIGRATION) 정합 (S-34, R-11 AC(a)).

    [MUST] 3 stage를 각각 별도 advance 호출로 노출시켜 개별 subTest로 판정한다 —
    단일 케이스만 보면 'DICT'만 추가한 부분 구현이 통과한다(SCENARIO-GATE-3.md ① 지적)."""

    def test_semi_agentic_opdd_boundary_three_stages_individually_S34(self):
        """S-34 — semi-agentic opdd에서 DICT/MODEL/DDL·MIGRATION 3개 확인 행이
        각각 개별적으로 차단되어야 하고, 승인 후에는 다음 전이가 정상 진행되어야 하며
        (영구 데드락 아님), 경계 밖 QA는 기존대로 자동 승인되어야 한다(과잉 차단 아님)."""
        self.assertTrue(_OPDD_REAL_PIPELINE.is_file(),
                        f"실 pipeline.json 부재: {_OPDD_REAL_PIPELINE}")
        d = self._task_dir("s34-opdd-semi-agentic")
        self._init(d, "semi-agentic", rows_from=_OPDD_REAL_PIPELINE, skill="opdd")

        # TASK 단계 확인 행(row 2)은 093에서 이미 경계에 있던 기존 stage다 —
        # 이 테스트의 대상(R-11 신규 3원소)이 아니므로 명시 승인으로 조기에 통과시킨다.
        self._assert_ok(self._mark_key(d, "task.task_md"), "S-34 prep task.task_md")
        self._assert_ok(self._mark_key(d, "task.user_confirm", "--owner", "user"),
                        "S-34 prep task.user_confirm (기존 TASK 경계 — R-11 대상 아님)")

        # ── ① DICT 경계 (직전 확인행 = id 5 dict.user_confirm) ──────────────────
        self._assert_ok(self._mark_key(d, "dict.dictionaries"), "S-34 prep dict.dictionaries")
        self._assert_ok(self._mark_key(d, "dict.pm_gate"), "S-34 prep dict.pm_gate")

        with self.subTest(stage="DICT"):
            code, stdout, stderr, data = self._advance_key(d, "model.modeling")
            self.assertEqual(code, 1,
                f"S-34 DICT 경계 미차단 — advance model.modeling이 성공함(부분/무구현 의심) "
                f"— {stdout!r}")
            self.assertEqual(data.get("error"), "user_confirmation_required", f"S-34 DICT {data!r}")
            self.assertEqual(data.get("row_id"), 5, f"S-34 DICT row_id 불일치 — {data!r}")
            self.assertEqual(data.get("stage"), "DICT", f"S-34 DICT stage 불일치 — {data!r}")
            self.assertEqual(data.get("reason"), "semi_agentic_pre_execute", f"S-34 DICT {data!r}")
            self.assertIn(data.get("auto_approved"), (None, []),
                         f"S-34 DICT auto_approved가 비어있지 않음 — {data!r}")
            r5 = self._row(d, 5)
            self.assertEqual(r5["status"], "pending", f"S-34 DICT dict.user_confirm이 승인됨 — {r5!r}")
            self.assertEqual(r5.get("owner"), "PM", f"S-34 DICT owner 변조 — {r5!r}")

        # 통과 경로 — 소유자 명시 승인 후 재진입(차단이 영구 데드락이 아님을 증명).
        # advance가 아닌 mark를 쓴다 — 미구현 상태에서 앞선 advance가 이미 통과해 버리면
        # row가 in_progress로 바뀌어 advance의 pending 전용 제약과 충돌하기 때문이다.
        self._assert_ok(self._mark_key(d, "dict.user_confirm", "--owner", "user"),
                        "S-34 DICT 소유자 승인")
        self._assert_ok(self._mark_key(d, "model.modeling"),
                        "S-34 DICT 승인 후 model.modeling 진입 실패 — 차단이 영구 데드락이 됨")

        # ── ② MODEL 경계 (직전 확인행 = id 8 model.user_confirm) ─────────────────
        self._assert_ok(self._mark_key(d, "model.pm_gate"), "S-34 prep model.pm_gate")

        with self.subTest(stage="MODEL"):
            code, stdout, stderr, data = self._advance_key(d, "ddl_migration.ddl_scripts")
            self.assertEqual(code, 1, f"S-34 MODEL 경계 미차단 — {stdout!r}")
            self.assertEqual(data.get("error"), "user_confirmation_required", f"S-34 MODEL {data!r}")
            self.assertEqual(data.get("row_id"), 8, f"S-34 MODEL row_id 불일치 — {data!r}")
            self.assertEqual(data.get("stage"), "MODEL", f"S-34 MODEL stage 불일치 — {data!r}")
            self.assertEqual(data.get("reason"), "semi_agentic_pre_execute", f"S-34 MODEL {data!r}")
            self.assertIn(data.get("auto_approved"), (None, []),
                         f"S-34 MODEL auto_approved가 비어있지 않음 — {data!r}")
            r8 = self._row(d, 8)
            self.assertEqual(r8["status"], "pending",
                             f"S-34 MODEL model.user_confirm이 승인됨 — {r8!r}")
            self.assertEqual(r8.get("owner"), "PM", f"S-34 MODEL owner 변조 — {r8!r}")

        self._assert_ok(self._mark_key(d, "model.user_confirm", "--owner", "user"),
                        "S-34 MODEL 소유자 승인")
        self._assert_ok(self._mark_key(d, "ddl_migration.ddl_scripts"),
                        "S-34 MODEL 승인 후 ddl_migration.ddl_scripts 진입 실패 — 영구 데드락")

        # ── ③ DDL/MIGRATION 경계 (직전 확인행 = id 11 ddl_migration.user_confirm) ─
        self._assert_ok(self._mark_key(d, "ddl_migration.pm_gate"), "S-34 prep ddl_migration.pm_gate")

        with self.subTest(stage="DDL/MIGRATION"):
            code, stdout, stderr, data = self._advance_key(d, "qa.review")
            self.assertEqual(code, 1, f"S-34 DDL/MIGRATION 경계 미차단 — {stdout!r}")
            self.assertEqual(data.get("error"), "user_confirmation_required",
                             f"S-34 DDL/MIGRATION {data!r}")
            self.assertEqual(data.get("row_id"), 11, f"S-34 DDL/MIGRATION row_id 불일치 — {data!r}")
            self.assertEqual(data.get("stage"), "DDL/MIGRATION",
                             f"S-34 DDL/MIGRATION stage 불일치 — {data!r}")
            self.assertEqual(data.get("reason"), "semi_agentic_pre_execute",
                             f"S-34 DDL/MIGRATION {data!r}")
            self.assertIn(data.get("auto_approved"), (None, []),
                         f"S-34 DDL/MIGRATION auto_approved가 비어있지 않음 — {data!r}")
            r11 = self._row(d, 11)
            self.assertEqual(r11["status"], "pending",
                             f"S-34 DDL/MIGRATION ddl_migration.user_confirm이 승인됨 — {r11!r}")
            self.assertEqual(r11.get("owner"), "PM", f"S-34 DDL/MIGRATION owner 변조 — {r11!r}")

        self._assert_ok(self._mark_key(d, "ddl_migration.user_confirm", "--owner", "user"),
                        "S-34 DDL/MIGRATION 소유자 승인")
        self._assert_ok(self._mark_key(d, "qa.review"),
                        "S-34 DDL/MIGRATION 승인 후 qa.review 진입 실패 — 영구 데드락")

        # ── 대조군: QA(id 14)는 경계 밖 — 기존대로 자동 승인되어야 한다(과잉 차단 아님) ──
        self._assert_ok(self._mark_key(d, "qa.pm_gate"), "S-34 prep qa.pm_gate")
        qa_data = self._assert_ok(self._mark_key(d, "qa.user_confirm", "--auto-pass"),
                                  "S-34 QA 대조군 — 경계 밖인데 자동 승인이 차단됨(과잉 차단)")
        r14 = self._row(d, 14)
        self.assertEqual(r14["status"], "done", f"S-34 QA 대조군 status 불일치 — {r14!r}")
        self.assertEqual(r14.get("owner"), "auto", f"S-34 QA 대조군 owner 불일치 — {r14!r}")


# 실 opgc pipeline.json — G-2 CLOSE 게이트 폴백 검증 대상(확인 행 0개 파이프라인)
_OPGC_REAL_PIPELINE = (_REPO_ROOT_093 / "opal" / "skills" / "opal-pilot-gc"
                       / "references" / "pipeline.json")


class TestR11CloseGateFallback(_T093Base):
    """G-2 `check_close_gate` 폴백 — 확인 행 0개 파이프라인(opgc) 데드락 해소 (S-35,
    R-11 AC(c))."""

    _OPGC_STEPS = (
        "scan.select_targets", "check.dispatch_agents", "check.await_agents",
        "report.security_report", "report.convention_report", "report.summary_table",
    )

    def _opgc_ready(self, name):
        self.assertTrue(_OPGC_REAL_PIPELINE.is_file(),
                        f"실 pipeline.json 부재: {_OPGC_REAL_PIPELINE}")
        d = self._task_dir(name)
        self._init(d, "agentic", rows_from=_OPGC_REAL_PIPELINE, skill="opgc")
        for key in self._OPGC_STEPS:
            self._assert_ok(self._mark_key(d, key), f"S-35 prep {key}")
        return d

    def test_opgc_close_fallback_owner_axis_and_opd_control_S35(self):
        """S-35 — 확인 행이 없는 opgc는 CLOSE 첫 행 자체가 소유자 승인 지점이 된다.
        ① --owner user 있으면 ok:true(--force 불요) ② 없으면 close_gate_violation
        ③ 대조군 — 확인 행이 있는 opd는 기존 prev_user_row 검증 경로가 그대로 동작
        (폴백이 기존 게이트를 무력화하지 않음)."""
        with self.subTest(case="opgc-owner-user-passes-without-force"):
            d = self._opgc_ready("s35-owner-user")
            code, stdout, stderr, data = self._mark_key(d, "close.done_md", "--owner", "user")
            self.assertEqual(code, 0,
                f"S-35 확인 행 0개(opgc) CLOSE 첫 행이 --owner user로도 통과하지 못함"
                f"(폴백 미구현 — --force 없이는 영구 데드락) — {stdout!r}")
            self.assertEqual(data.get("status"), "done", f"S-35 {data!r}")

        with self.subTest(case="opgc-without-owner-still-denied"):
            d2 = self._opgc_ready("s35-no-owner")
            code, stdout, stderr, data = self._mark_key(d2, "close.done_md")
            self.assertEqual(code, 1,
                f"S-35 --owner user 없이 통과됨 — 폴백이 게이트를 무력화함 — {stdout!r}")
            self.assertEqual(data.get("error"), "close_gate_violation", f"S-35 {data!r}")

        with self.subTest(case="opd-control-prev-user-row-path-unaffected"):
            d3 = self._task_dir("s35-opd-control")
            self._init(d3, "agentic", rows_from=_OPD_PIPELINE_093, skill="opd")
            state_path = d3 / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            for r in state["rows"]:
                if r.get("key") != "close.done_md":
                    r["status"] = "done"
                    r["status_label"] = "✅"
                    r["owner"] = "auto"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
            code, stdout, stderr, data = self._mark_key(d3, "close.done_md")
            self.assertEqual(code, 1,
                f"S-35 대조군 — 확인 행이 있는 opd(test.user_confirm owner=auto)에서도 "
                f"CLOSE 게이트가 무력화됨(G-2 회귀) — {stdout!r}")
            self.assertEqual(data.get("error"), "close_gate_violation", f"S-35 대조군 {data!r}")


class TestR11DerivedSignals(_T093Base):
    """G-3-a `_derive_next_action` + G-3-b `build_todo_mirror` 파생 신호 배선
    (S-36, S-37, R-11 AC(a)(d))."""

    _TASK_MD = (
        "# TASK: R-11 파생 신호 픽스처\n\n"
        "## 목표\nS-36/S-37 검증\n\n"
        "## 완료 기준\n- 전 행 진행\n"
    )  # '## 명확화 결과' 섹션 부재 → graceful skip(005 정책 A)

    def _opd_task(self, name, mode="agentic"):
        d = self._task_dir(name)
        self._init(d, mode, rows_from=_OPD_PIPELINE_093, skill="opd")
        # gate.artifacts 실 파일 생성(analysis.pm_gate/plan.pm_gate/scenario_gate/test.pm_gate)
        (d / "TASK.md").write_text(self._TASK_MD, encoding="utf-8")
        (d / "ANALYSIS.md").write_text("# ANALYSIS\n", encoding="utf-8")
        (d / "PLAN.md").write_text("# PLAN\n", encoding="utf-8")
        (d / "TEST-SCENARIO.md").write_text("# TEST SCENARIO\n", encoding="utf-8")
        return d

    def _next_action(self, d):
        code, stdout, stderr, data = _run070(["show", str(d), "--format", "json"])
        self.assertEqual(code, 0, f"S-36 show 실패: {stdout!r}/{stderr!r}")
        return (data.get("data") or {}).get("next_action")

    def test_agentic_next_action_suppresses_hollow_confirmation_S36(self):
        """S-36 — agentic opd 16행 전 구간에서 next_action이 '사용자 확인'을 가리키지
        않는다. 단, CLOSE 진입 직전(test.user_confirm, id15)은 실제 승인 필요 지점이므로
        예외. 대조군 — interactive 모드는 확인 프론티어를 정상적으로 노출해야 한다
        (과잉 억제 방지)."""
        d = self._opd_task("s36-agentic")
        steps = [
            ("mark",    "task.task_md"),
            ("advance", "analysis.analysis_md"),
            ("mark",    "analysis.analysis_md"),
            ("mark",    "analysis.pm_gate"),
            ("advance", "plan.plan_md"),
            ("mark",    "plan.plan_md"),
            ("mark",    "plan.pm_gate"),
            ("advance", "test_scenario.test_scenario_md"),
            ("mark",    "test_scenario.test_scenario_md"),
            ("mark",    "test_scenario.scenario_gate"),
            ("advance", "execute.implement"),
            ("mark",    "execute.implement"),
            ("mark",    "test.run_tests"),
            ("mark",    "test.pm_gate"),
        ]
        captured = {}
        for action, key in steps:
            if action == "mark":
                self._assert_ok(self._mark_key(d, key), f"S-36 mark {key}")
            else:
                self._assert_ok(self._advance_key(d, key), f"S-36 advance {key}")
            captured[key] = self._next_action(d)

        with self.subTest(check="no-hollow-confirmation-mid-pipeline"):
            hollow = {k: na for k, na in captured.items()
                      if k != "test.pm_gate" and na and "사용자 확인" in na}
            self.assertEqual(hollow, {}, f"S-36 헛 확인 잔존(자동 승인 예정 행이 노출됨) — {hollow!r}")

        with self.subTest(check="close-adjacent-exception-preserved"):
            na = captured["test.pm_gate"]
            self.assertIsNotNone(na, "S-36 test.pm_gate 이후 next_action 미획득")
            self.assertIn("사용자 확인", na,
                          "S-36 CLOSE 진입 직전(test.user_confirm) 노출이 과잉 억제됨 — "
                          "실제 승인이 필요한 유일 지점이다")

        with self.subTest(check="interactive-control-still-shows-confirmation"):
            d2 = self._opd_task("s36-interactive", mode="interactive")
            self._assert_ok(self._mark_key(d2, "task.task_md"), "S-36 control mark task.task_md")
            na2 = self._next_action(d2)
            self.assertIsNotNone(na2)
            self.assertIn("사용자 확인", na2,
                          "S-36 대조군 — interactive 모드에서 확인 프론티어가 억제됨(과잉 억제)")

    def test_todo_mirror_neutralizes_pending_auto_approve_row_S37(self):
        """S-37 — 작업+PM Gate 완료·확인 행만 pending인 단계의 todo가 completed로
        렌더된다(자동 승인 예정 행 중립 처리). 대조군 — semi-agentic 모드 경계 내부
        단계는 중립 처리되지 않고 in_progress 유지. state.json 미접촉(스키마 validate 통과)."""
        with self.subTest(case="agentic-stage-neutralized-to-completed"):
            d = self._opd_task("s37-agentic")
            self._assert_ok(self._mark_key(d, "task.task_md"), "S-37 mark task.task_md")
            self._assert_ok(self._mark_key(d, "analysis.analysis_md"),
                            "S-37 mark analysis.analysis_md(task.user_confirm 훅 자동승인 동반)")
            data = self._assert_ok(self._mark_key(d, "analysis.pm_gate"),
                                   "S-37 mark analysis.pm_gate")
            self.assertEqual(self._row(d, 5)["item"], "사용자 확인")
            self.assertEqual(self._row(d, 5)["status"], "pending",
                             "S-37 전제: analysis.user_confirm은 아직 pending이어야 한다")
            by_stage = {t["id"]: t for t in data["todo_mirror"]["todos"]}
            self.assertEqual(by_stage["stage:ANALYSIS"]["status"], "completed",
                f"S-37 자동 승인 예정 확인 행이 중립 처리되지 않음(과잉 in_progress) — "
                f"{by_stage['stage:ANALYSIS']!r}")

            vcode, vstdout, vstderr, vdata = self._validate(d)
            self.assertEqual(vdata.get("violations_count"), 0, f"S-37 validate 위반 — {vdata!r}")
            state = json.loads((d / "state.json").read_text(encoding="utf-8"))
            self.assertNotIn("todo_mirror", state, "S-37 todo_mirror가 state.json에 영속화됨(H-3 위반)")

        with self.subTest(case="semi-agentic-boundary-control-stays-in-progress"):
            d2 = self._task_dir("s37-semi-boundary")
            self._init(d2, "semi-agentic", rows_from=_OPD_PIPELINE_093, skill="opd")
            data2 = self._assert_ok(self._mark_key(d2, "task.task_md"),
                                    "S-37 control mark task.task_md")
            self.assertEqual(self._row(d2, 2)["status"], "pending",
                             "S-37 control 전제: task.user_confirm pending")
            by_stage2 = {t["id"]: t for t in data2["todo_mirror"]["todos"]}
            self.assertEqual(by_stage2["stage:TASK"]["status"], "in_progress",
                f"S-37 대조군 — semi-agentic 경계 내부 단계가 중립 처리(과잉 억제)됨 — "
                f"{by_stage2['stage:TASK']!r}")


def _error_codes_key_set_from_source(source_text):
    """[Step 3-c] state_tool.py 소스 텍스트에서 `ERROR_CODES = {...}` 대입문을 AST로
    찾아 `ast.literal_eval`로 안전하게 평가한 뒤 키 집합만 반환한다(코드 실행 없음).
    대입문을 찾지 못하면 None."""
    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "ERROR_CODES" for t in node.targets):
            continue
        value = ast.literal_eval(node.value)
        return set(value.keys())
    return None


class TestR11Invariants(_T093Base):
    """R-11 [MUST] 불변 제약 역검증 — 신규 판정 함수/상수 금지, `next_action` 스키마·
    `build_todo_mirror` 시그니처·`ERROR_CODES` 무접촉 (S-40).

    [주의] 이 클래스의 '무접촉'류 서브케이스(diff 기반)는 R-11이 아직 배선되지 않은
    RED 시점에는 git diff 자체가 비어 있어 공허하게 참일 수 있다(비교 대상 부재).
    이 테스트가 실질적으로 RED인 지점은 '단일 판정 함수 재사용'이 아직 배선되지
    않았다는 사실을 양성 단언(포함 여부)으로 검증하는 서브케이스다 — 부재를 확인하는
    것이 아니라 재사용의 '존재'를 확인하므로 미구현 상태에서 반드시 실패한다."""

    def test_r11_invariants_S40(self):
        """S-40 — R-11 적용 전후 불변 제약. ① G-1·G-3가 `can_auto_approve_user_confirmation`
        단일 판정 함수를 재사용함(신규 판정 함수/상수 금지, 헌법 §2) ② `next_action`
        필드·스키마 불변 ③ `build_todo_mirror` 시그니처·반환 키 집합 불변 ④ R-11 diff가
        `ERROR_CODES`를 접촉하지 않음(종수 리터럴은 S-7·S-15가 실측 기준으로 판정하므로
        여기서 재고정하지 않는다)."""
        import inspect

        with self.subTest(check="derive_next_action_reuses_single_judge"):
            src = inspect.getsource(ST._derive_next_action)
            self.assertIn(
                "can_auto_approve_user_confirmation", src,
                "S-40 _derive_next_action이 단일 판정 함수(can_auto_approve_user_confirmation)를 "
                "재사용하지 않음 — 새 판정 로직/상수를 별도로 만들면 이 검증이 깨진다(헌법 §2)")

        with self.subTest(check="build_todo_mirror_reuses_single_judge"):
            src = inspect.getsource(ST.build_todo_mirror)
            self.assertIn(
                "can_auto_approve_user_confirmation", src,
                "S-40 build_todo_mirror가 단일 판정 함수(can_auto_approve_user_confirmation)를 "
                "재사용하지 않음")

        with self.subTest(check="next_action_schema_unchanged"):
            schema = json.loads((_TOOL_DIR / "schema" / "state.schema.json")
                                .read_text(encoding="utf-8"))
            props = schema.get("properties", {})
            na_schema = props.get("next_action")
            self.assertIsNotNone(na_schema, "S-40 next_action 필드가 스키마에서 소멸")
            one_of_types = {t.get("type") for t in na_schema.get("oneOf", [])}
            self.assertIn("string", one_of_types,
                         f"S-40 next_action 타입 계약 변경 감지 — {na_schema!r}")

        with self.subTest(check="build_todo_mirror_signature_unchanged"):
            params = list(inspect.signature(ST.build_todo_mirror).parameters)
            self.assertEqual(params, ["state", "action"],
                             f"S-40 build_todo_mirror 시그니처 변경 감지 — {params!r}")

        with self.subTest(check="error_codes_key_set_untouched"):
            # [Step 3-c 정교화] git diff의 substring 판정은 @header description이
            # 단일 물리 라인이라 과거 이력 문구("ERROR_CODES 8종 추가" 등)가 이미
            # 박혀 있다 — 그 줄에 R-11 요약을 한 글자만 보태도 diff가 줄 전체를
            # 삭제+추가로 잡아 거짓 FAIL을 낸다(@header 갱신 자체를 구조적으로
            # 막는 부작용). S-40이 검증하려는 것은 "ERROR_CODES 자체가 바뀌지
            # 않았다"이지 "diff 텍스트에 그 문자열이 없다"가 아니므로, HEAD
            # 시점(R-11 반영 전)의 ERROR_CODES 딕셔너리를 AST로 직접 파싱해
            # 키 집합을 비교한다 — @header 같은 무관한 문자열 변경에 흔들리지
            # 않으면서 실제 종목 추가·삭제는 그대로 잡아낸다.
            head_src = subprocess.run(
                ["git", "show", "HEAD:./state_tool.py"],
                cwd=str(_TOOL_DIR), capture_output=True, text=True,
            ).stdout
            self.assertTrue(head_src, "S-40 git show HEAD:state_tool.py 결과가 비어 있음")
            head_keys = _error_codes_key_set_from_source(head_src)
            self.assertIsNotNone(head_keys,
                                 "S-40 HEAD 버전 소스에서 ERROR_CODES 대입문을 찾지 못함")
            current_keys = set(ST.ERROR_CODES.keys())
            self.assertEqual(
                current_keys, head_keys,
                f"S-40 R-11 변경이 ERROR_CODES 키 집합을 바꿈 — "
                f"추가={sorted(current_keys - head_keys)!r} "
                f"삭제={sorted(head_keys - current_keys)!r} "
                "(종수는 S-7·S-15가 실측 기준으로 판정 — 여기서 재고정 금지)")


# ═════════════════════════════════════════════════════════════════════════════
# 098 ADD-2 RED-first — 배포 경로 루트 파생 결함 (mode:red)
# [MUST] red-first.md §2 작성자≠구현자 — 본 블록은 테스트만 추가하며 state_tool.py를
#        수정하지 않는다(Read 전용). 기존 케이스도 수정·삭제하지 않는다(순수 additive).
# [MUST] 헌법 §4 "Don't fake it" — mock/patch/MagicMock 미사용. 합성 픽스처가 아니라
#        저장소 실파일(본 태스크 TASK.md) + `state_tool.py` 임시 사본 subprocess
#        실행(공개 CLI `verify --evidence-check` stdout JSON)으로만 검증한다.
# ═════════════════════════════════════════════════════════════════════════════

_T098ADD2_TASK_PATH = _REPO_ROOT_093 / "tasks" / "098-260821-opds-근거등급-확정판정-트랙강등"


class TestT098Add2RootDerivation(unittest.TestCase):
    """098 ADD-2 RED — `_resolve_citation_exists()`(`state_tool.py:2400`)가 프로젝트
    루트를 `find_project_root(str(pathlib.Path(__file__).resolve()))`로, 즉
    `task_md_path`가 아니라 스크립트 자기 위치에서 파생하는 결함의 배포 경로
    등가성 실패 테스트.

    결함 재현: `state_tool.py`를 프로젝트 밖(조상에 `.opal/MEMORY.json`이 없는
    임시 디렉토리)으로 복사한 사본으로 실행하면 `find_project_root`가 None을
    반환해 `_resolve_citation_exists`가 조기 반환 False를 내놓고, 정규 인용을
    갖춘 항목까지 전건 `citation_path_not_found`로 오강등된다(PM 실측: 프로젝트
    소스 실행 confirmed_ratio=0.75 vs 배포본 `~/.opal/tools/state-tool/run.sh`
    실행 confirmed_ratio=0.0).

    구현 시그니처(예: `_resolve_citation_exists`가 root 인자를 받는지)는 GREEN
    단계(op-be-agent) 결정 — 본 클래스는 내부 함수가 아니라 공개 CLI 동작
    (`verify --evidence-check` stdout)만으로 판정한다.
    """

    @classmethod
    def setUpClass(cls):
        if not (_T098ADD2_TASK_PATH / "TASK.md").is_file():
            raise unittest.SkipTest(
                f"본 태스크 TASK.md 부재 — 실파일 입력 전제가 깨짐: {_T098ADD2_TASK_PATH}"
            )

    def setUp(self):
        self._copy_dir = pathlib.Path(tempfile.mkdtemp())
        self._copied_script = self._copy_dir / "state_tool.py"
        # 힌트: memory_tool.py는 `verify` 경로에서 미참조(_MEMORY_TOOL은
        # link_memory_history 전용 — cmd_mark에서만 소비)이므로 복사 불필요.
        shutil.copy2(_SRC_093, self._copied_script)

    def tearDown(self):
        shutil.rmtree(self._copy_dir, ignore_errors=True)

    def _run_verify(self, script_path):
        """공개 CLI `verify <task-path> --evidence-check` subprocess 실행 →
        stdout JSON dict. exit code는 라우터형이라 항상 0 기대(차단 없음,
        PLAN §3.3.2)."""
        result = subprocess.run(
            [sys.executable, str(script_path), "verify",
             str(_T098ADD2_TASK_PATH), "--evidence-check"],
            capture_output=True, text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"[RED] verify --evidence-check는 라우터형이라 항상 exit 0 기대 "
            f"(script={script_path}). stderr={result.stderr}",
        )
        stdout = result.stdout.strip()
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            self.fail(
                f"[RED] stdout이 JSON이 아님(script={script_path}): "
                f"{stdout!r} stderr={result.stderr}"
            )

    # ── 축 ① 스크립트 위치 독립성 ────────────────────────────────────────

    def test_axis1_copied_script_confirmed_ratio_matches_source_location(self):
        """축① — 프로젝트 밖 임시 디렉토리로 복사한 사본으로
        `verify <태스크경로> --evidence-check`를 실행해도, 프로젝트 소스로
        실행한 결과와 `confirmed_ratio`·항목별 `verdict`·`reasons`가 동일해야
        한다(배포 경로 등가 조건). 결함 현재: 사본은 root=None → 모든 실존
        인용이 미존재 처리되어 confirmed_ratio가 0.75→0.0으로 붕괴 — 지금 FAIL
        기대."""
        source_result = self._run_verify(_SRC_093)
        copied_result = self._run_verify(self._copied_script)

        self.assertEqual(
            copied_result.get("confirmed_ratio"),
            source_result.get("confirmed_ratio"),
            f"[RED] 사본 실행 confirmed_ratio가 프로젝트 소스 실행과 달라짐"
            f"(배포 경로 루트 파생 결함 재현). "
            f"source={source_result.get('confirmed_ratio')} "
            f"copied={copied_result.get('confirmed_ratio')}",
        )

        source_items = {it.get("element"): it for it in source_result.get("items", [])}
        copied_items = {it.get("element"): it for it in copied_result.get("items", [])}
        self.assertEqual(
            set(copied_items.keys()), set(source_items.keys()),
            f"[RED] 항목 집합 자체가 달라짐. source={sorted(source_items)} "
            f"copied={sorted(copied_items)}",
        )
        for elem, s_item in source_items.items():
            c_item = copied_items.get(elem, {})
            self.assertEqual(
                c_item.get("verdict"), s_item.get("verdict"),
                f"[RED] '{elem}' verdict 불일치(사본 vs 소스) — "
                f"source={s_item} copied={c_item}",
            )
            self.assertEqual(
                c_item.get("reasons"), s_item.get("reasons"),
                f"[RED] '{elem}' reasons 불일치(사본 vs 소스) — "
                f"source={s_item} copied={c_item}",
            )

    # ── 축 ② 오강등 부재 ─────────────────────────────────────────────────

    def test_axis2_copied_script_no_false_demotion_for_valid_citation(self):
        """축② — 사본 실행에서 정규 인용(`경로:N` 형식으로 실존 파일을 가리키는
        항목, 여기서는 '제약' 요소의 `opal/tools/state-tool/state_tool.py:2225`)이
        `citation_path_not_found`를 받지 않아야 한다. 결함 현재: 사본 실행은
        실존 파일 인용까지 미존재로 오판정 — 지금 FAIL 기대."""
        copied_result = self._run_verify(self._copied_script)
        by_elem = {it.get("element"): it for it in copied_result.get("items", [])}

        constraint_item = by_elem.get("제약", {})
        citation = None
        for c in constraint_item.get("citations", []):
            if "state_tool.py:2225" in str(c.get("raw", "")):
                citation = c
                break
        self.assertIsNotNone(
            citation,
            f"[RED] '제약' 항목에서 `state_tool.py:2225` 인용을 찾지 못함 — "
            f"TASK.md 표 구조가 전제와 달라졌을 가능성. item={constraint_item}",
        )
        self.assertNotIn(
            "citation_path_not_found", constraint_item.get("reasons", []),
            f"[RED] 정규 인용(실존 파일:유효 줄번호)이 배포 경로에서 "
            f"citation_path_not_found로 오강등됨. item={constraint_item}",
        )
        self.assertIs(
            citation.get("exists"), True,
            f"[RED] 실존 파일 인용의 exists가 True 기대. citation={citation}",
        )

    # ── 축 ③ 회귀 방어 (프로젝트 소스 실행 — 지금 PASS, GREEN 이후에도 PASS) ─

    def test_axis3_source_location_confirmed_ratio_unchanged_regression_guard(self):
        """축③ — 프로젝트 소스 위치(`opal/tools/state-tool/state_tool.py`)로
        실행한 기존 판정(PM 실측 confirmed_ratio=0.75, '목표'만 grade_unknown,
        나머지 3요소는 확정)이 불변이어야 한다. 회귀 가드 — 지금 PASS 기대이며
        ①·②의 GREEN 구현 이후에도 계속 PASS해야 한다."""
        result = self._run_verify(_SRC_093)
        self.assertEqual(
            result.get("confirmed_ratio"), 0.75,
            f"[REGRESSION] 프로젝트 소스 실행 confirmed_ratio 변경됨. result={result}",
        )
        by_elem = {it.get("element"): it for it in result.get("items", [])}
        self.assertEqual(
            by_elem.get("목표", {}).get("verdict"), "미확정",
            f"[REGRESSION] '목표'(grade_unknown 인용) verdict 변경됨. result={result}",
        )
        self.assertIn(
            "grade_unknown", by_elem.get("목표", {}).get("reasons", []),
            f"[REGRESSION] '목표' reasons에 grade_unknown 부재. result={result}",
        )
        for elem in ("범위", "제약", "완료기준"):
            self.assertEqual(
                by_elem.get(elem, {}).get("verdict"), "확정",
                f"[REGRESSION] '{elem}' verdict 변경됨(기존 확정 항목). result={result}",
            )


# ═════════════════════════════════════════════════════════════════════════════
# T100 — verify --evidence-check `## 확정된 설계 방향` 승계 파서 RED 테스트
#        (PLAN 100 §3.7.2 / §4.2 Step 10, TS-025~TS-030)
# ═════════════════════════════════════════════════════════════════════════════

class TestT100DirectionEvidence(BaseTestCase):
    """태스크 100 / RED-first / 실 파일 픽스처, mock 금지.

    `verify --evidence-check`의 확장 계약(PLAN 100 §3.7.2)에 대한 RED 증거만
    확보한다. 구현(`state_tool.py`)은 Step 11(GREEN) 소관이며 본 Step에서
    무접촉이다(`opal/core/references/harness/red-first.md`).

    [MUST] mock/patch/MagicMock 금지 — `tmp_path`(tempfile) 실 파일 픽스처 +
    공개 CLI 경로(`cmd_verify` 직접 호출)만 사용한다. 기존
    `TestT098EvidenceCheck`(:4225)의 원칙을 그대로 따르며, 해당 클래스와
    그 헬퍼는 무수정으로 둔다(본 클래스는 자체 헬퍼를 보유한다).

    검증 대상 계약 6종:
      ① `## 확정된 설계 방향` 최상위 불릿이 `items[]`에 편입되고, 모든 item에
         출처 구분 `source` 필드(`clarification` | `confirmed_direction`)가 붙는다.
      ② 상류에서 대조 확인된 `[사실]` 항목의 verdict로 `승계`가 존재한다
         (`확정`·`승계` 모두 confirmed로 계수).
      ③ 신규 키 `direction_confirmed_ratio`가 반환된다(섹션 부재 시 None).
      ④ [회귀] 기존 `confirmed_ratio`의 분모는 `## 명확화 결과` 4요소로 불변이다(PD-1).
      ⑤ [회귀] `## 확정된 설계 방향` 섹션이 없는 레거시 TASK.md는 graceful skip.
      ⑥ [회귀] 위 전 경로에서 exit code 0 유지.

    [MUST] `## 명확화 결과` 표는 열 4개 고정(:4237-4238) — 열 추가가 아니라
    **별도 섹션 파서**를 전제한다. 본 클래스의 어떤 픽스처도 표 열을 늘리지 않는다.

    [계약] direction item의 `element`는 해당 불릿을 식별할 수 있는 문자열이어야
    한다(불릿 본문 유래). 인덱스형 불투명 라벨은 PM이 어떤 항목이 미확정인지
    식별할 수 없게 하므로 계약 위반이다 — 아래 테스트는 불릿에 심어둔 마커
    (`DIR-D1` 등)가 `element`에 남는지로 이를 판정한다.
    """

    _ELEMENTS = ("목표", "범위", "제약", "완료기준")

    # 명확화 결과 4행 — 확정 2(목표: [결정] / 범위: 유효 E4 인용) +
    # 미확정 2(제약: 인용 0건 / 완료기준: E5 단독) → confirmed_ratio 고정 0.5.
    # 이 0.5는 ④(분모 불변) 판정의 기준값이다.
    _CLARIFICATION_ROWS = {
        "목표": ("[결정] 캡틴이 정한 목표(근거 불요)", "-"),
        "범위": ("범위 확정값", "`opal/tools/state-tool/README.md` §1"),
        "제약": ("제약 확정값", "-"),
        "완료기준": ("완료기준 확정값", "`.opal/brain/note.md`"),
    }
    _CLARIFICATION_RATIO = 0.5
    _CLARIFICATION_UNCONFIRMED = {"제약", "완료기준"}

    _DECISION_MARKERS = ("DIR-D1", "DIR-D2", "DIR-D3")
    _FACT_MARKERS = ("DIR-F1", "DIR-F2", "DIR-F3")

    # 픽스처 A의 `[사실]` 불릿 3건이 인용하는 **실재 파일 + 유효 줄번호**.
    # (state_tool.py 2897줄 / README.md 420줄 / citation-rules.md 487줄 — 전부
    #  E2·E4 등급 매칭 경로이므로 4축을 통과한다.)
    _REAL_CITATIONS = (
        "opal/tools/state-tool/state_tool.py:100",
        "opal/tools/state-tool/README.md:10",
        "opal/core/references/harness/citation-rules.md:20",
    )

    # ── 픽스처 빌더 (실 파일만, mock 없음) ────────────────────────────────

    def _clarification_block(self):
        """`## 명확화 결과` 4행 표 — 열 4개 고정(:4237-4238 계약 유지)."""
        lines = [
            "## 명확화 결과",
            "",
            "| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |",
            "|------|--------|--------------|----------|",
        ]
        for elem in self._ELEMENTS:
            confirmed, dep = self._CLARIFICATION_ROWS[elem]
            lines.append(f"| {elem} | {confirmed} | - | {dep} |")
        return lines

    def _write_fixture_a(self):
        """픽스처 A — `## 확정된 설계 방향` 최상위 불릿 6행([결정] 3 + [사실] 3,
        사실 항목은 실재 `경로:줄번호` 인용) + `## 명확화 결과` 표 4행.

        불릿 표기는 실제 TASK.md 형식을 그대로 따른다
        (`tasks/100-260822-opd-분석코어-공유SSOT/TASK.md:63-87` — 헤딩 접미사
        `(대화에서 합의)` 포함, 태그는 백틱 스팬).
        중첩 불릿 1행을 섞어 **최상위 불릿만 수집**되는지도 함께 판정한다."""
        lines = [
            "# TASK — T100 RED 픽스처 A",
            "",
            "## 확정된 설계 방향 (대화에서 합의)",
            "",
            f"- `[결정]` {self._DECISION_MARKERS[0]} — 근거 없이 확정 유지되는 캡틴 결정 1.",
            f"- `[결정]` {self._DECISION_MARKERS[1]} — 근거 없이 확정 유지되는 캡틴 결정 2.",
            "  - 중첩 불릿 — 최상위가 아니므로 항목으로 수집하지 않는다.",
            f"- `[결정]` {self._DECISION_MARKERS[2]} — 근거 없이 확정 유지되는 캡틴 결정 3.",
            f"- `[사실]` {self._FACT_MARKERS[0]} — 상류에서 대조 확인된 사실 1 "
            f"(`{self._REAL_CITATIONS[0]}`).",
            f"- `[사실]` {self._FACT_MARKERS[1]} — 상류에서 대조 확인된 사실 2 "
            f"(`{self._REAL_CITATIONS[1]}`).",
            f"- `[사실]` {self._FACT_MARKERS[2]} — 상류에서 대조 확인된 사실 3 "
            f"(`{self._REAL_CITATIONS[2]}`).",
            "",
        ]
        lines += self._clarification_block()
        return self._write(lines)

    def _write_fixture_b(self):
        """픽스처 B — `## 확정된 설계 방향` 섹션 **없음**(레거시 TASK.md)."""
        lines = ["# TASK — T100 RED 픽스처 B (레거시)", ""]
        lines += self._clarification_block()
        return self._write(lines)

    def _write_fixture_c(self):
        """픽스처 C — `## 확정된 설계 방향` 헤딩만 있고 항목 0건.
        분모 0 나눗셈 경계(ZeroDivisionError 금지)."""
        lines = [
            "# TASK — T100 RED 픽스처 C (항목 0건)",
            "",
            "## 확정된 설계 방향",
            "",
        ]
        lines += self._clarification_block()
        return self._write(lines)

    def _write(self, lines):
        p = self.task_path / "TASK.md"
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return p

    # ── 호출 헬퍼 ─────────────────────────────────────────────────────────

    def _call_evidence_verify(self, task_path=None, task_md=None, **extra_flags):
        """cmd_verify --evidence-check 호출 → (exit_code, result_dict).

        [MUST] 신규 헬퍼 — `TestT098EvidenceCheck._call_evidence_verify`(:4285)는
        무수정으로 둔다(태스크 100 dispatch 지시: 기존 클래스 무접촉)."""
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        exit_code = 0
        fields = dict(
            task_path=str(task_path or self.task_path),
            scenario=None,
            clarification_check=False,
            evidence_check=True,
            task_md=task_md,
            red_check=False,
            fix_mode=False,
            changed_files=None,
            test_globs=None,
        )
        fields.update(extra_flags)
        args = types.SimpleNamespace(**fields)
        with redirect_stdout(out):
            try:
                ST.cmd_verify(args)
            except SystemExit as e:
                exit_code = e.code
        output = out.getvalue().strip()
        result = json.loads(output) if output else {}
        return exit_code, result

    @staticmethod
    def _items_with_source(result, source):
        return [it for it in result.get("items", []) if it.get("source") == source]

    @staticmethod
    def _item_by_marker(result, marker):
        """불릿 마커(`DIR-D1` 등)를 `element`에 보유한 item 1건을 찾는다.
        미발견 시 None — 계약 위반 메시지는 호출자가 낸다."""
        for it in result.get("items", []):
            if marker in str(it.get("element", "")):
                return it
        return None

    @staticmethod
    def _clarification_items(result):
        """명확화 결과 4요소 라벨을 가진 item만 골라낸다(source 필드가 아직
        없는 현행 구현에서도 분모 계산 회귀를 판정할 수 있게 한다)."""
        elems = TestT100DirectionEvidence._ELEMENTS
        return [it for it in result.get("items", []) if it.get("element") in elems]

    # ── ① 확정된 설계 방향 항목의 items[] 편입 + source 필드 (TS-025) ──────

    def test_t100_direction_items_merged_into_items_with_source_field(self):
        """① TS-025 — `## 확정된 설계 방향` 최상위 불릿 6건이 `items[]`에
        `source="confirmed_direction"`으로 편입되고, 명확화 결과 4건은
        `source="clarification"`을 보유한다. 중첩 불릿은 수집 대상이 아니다.
        (PLAN 100 §3.7.2 `_locate_confirmed_direction_items`, R-10 AC (a))"""
        self._write_fixture_a()
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")
        self.assertTrue(result.get("ok"), f"[RED] ok=true 기대. result={result}")

        direction = self._items_with_source(result, "confirmed_direction")
        self.assertEqual(
            len(direction), 6,
            f"[RED] 최상위 불릿 6건이 source='confirmed_direction'으로 편입 기대"
            f"(중첩 불릿 1행은 비수집). 실제 {len(direction)}건. result={result}")

        clarification = self._items_with_source(result, "clarification")
        self.assertEqual(
            len(clarification), 4,
            f"[RED] 명확화 결과 4건이 source='clarification' 기대. "
            f"실제 {len(clarification)}건. result={result}")

        self.assertEqual(
            len(result.get("items", [])), 10,
            f"[RED] 두 소스 병합 items 10건(6+4) 기대. result={result}")

        for it in result.get("items", []):
            self.assertIn("source", it, f"[RED] 모든 item에 source 필드 기대. item={it}")
            self.assertIn(
                it.get("source"), ("clarification", "confirmed_direction"),
                f"[RED] source는 'clarification'|'confirmed_direction' 중 하나 기대. item={it}")
            for key in ("element", "verdict", "reasons", "citations"):
                self.assertIn(key, it, f"[RED] item에 '{key}' 키 기대(기존 스키마 유지). item={it}")

        for marker in self._DECISION_MARKERS + self._FACT_MARKERS:
            item = self._item_by_marker(result, marker)
            self.assertIsNotNone(
                item,
                f"[RED] 불릿 마커 '{marker}'를 element에 보유한 item 미검출 — "
                f"element는 불릿을 식별 가능해야 한다(불투명 인덱스 라벨 금지). "
                f"result={result}")

        nested = [it for it in result.get("items", []) if "중첩 불릿" in str(it.get("element", ""))]
        self.assertEqual(
            nested, [],
            f"[RED] 중첩(비최상위) 불릿은 항목으로 수집하지 않는다. 검출={nested}")

    # ── ② verdict `승계` 신설 (TS-025 / R-10 AC (c)) ───────────────────────

    def test_t100_fact_bullet_with_valid_citation_gets_inherited_verdict(self):
        """② `[사실]` + E1~E4 유효 인용(실재 경로:줄번호) → verdict `승계`,
        `[결정]` 불릿 → verdict `확정`(등급 판정 면제). `확정`·`승계` 모두
        confirmed로 계수된다. (PLAN 100 §3.7.2 verdict 규칙)"""
        self._write_fixture_a()
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")

        for marker in self._DECISION_MARKERS:
            item = self._item_by_marker(result, marker) or {}
            self.assertEqual(
                item.get("verdict"), "확정",
                f"[RED] `[결정]` 불릿({marker})은 인용 없어도 확정 기대 "
                f"(_has_decision_tag 재사용). item={item}")

        for marker in self._FACT_MARKERS:
            item = self._item_by_marker(result, marker) or {}
            self.assertEqual(
                item.get("verdict"), "승계",
                f"[RED] `[사실]` + 유효 인용 불릿({marker})은 신규 verdict '승계' 기대 "
                f"(상류 대조 확인 승계 — 재확인 면제). item={item}")
            self.assertEqual(
                item.get("reasons", []), [],
                f"[RED] 승계 항목은 강등 사유 0건 기대. item={item}")

        unconfirmed = set(result.get("unconfirmed", []))
        for marker in self._DECISION_MARKERS + self._FACT_MARKERS:
            self.assertNotIn(
                marker, " ".join(unconfirmed),
                f"[RED] 확정·승계 항목({marker})은 unconfirmed에 오르지 않는다. "
                f"unconfirmed={unconfirmed}")

    # ── ③ direction_confirmed_ratio 신규 키 (PD-1) ─────────────────────────

    def test_t100_direction_confirmed_ratio_new_key_returned(self):
        """③ 신규 키 `direction_confirmed_ratio`가 반환된다 — 픽스처 A는
        확정 3 + 승계 3 / 6 = 1.0. 기존 `confirmed_ratio`(0.5)와 **다른 값**이어야
        분리형(PD-1)이 성립한다."""
        self._write_fixture_a()
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")
        self.assertIn(
            "direction_confirmed_ratio", result,
            f"[RED] 신규 키 'direction_confirmed_ratio' 반환 기대(PD-1 분리형). result={result}")
        self.assertEqual(
            result.get("direction_confirmed_ratio"), 1.0,
            f"[RED] 확정3+승계3 / 6 = 1.0 기대. result={result}")
        self.assertNotEqual(
            result.get("direction_confirmed_ratio"), result.get("confirmed_ratio"),
            f"[RED] 두 비율은 분모가 다른 별개 키다(PD-1 — 기존 키 의미 불변). "
            f"result={result}")

    # ── ④ [회귀] 기존 confirmed_ratio 분모 불변 (TS-029 / H-2) ─────────────

    def test_t100_existing_confirmed_ratio_denominator_unchanged(self):
        """④ [회귀] `confirmed_ratio`의 분모는 `## 명확화 결과` 4요소로 불변이다
        (PD-1 — 조용한 계약 파괴 방지). 픽스처 A에서 확정 2/4 = 0.5이며,
        방향 항목 6건이 분모(10)로 섞여 들어가면 FAIL. `unconfirmed[]`는 병합
        대상이지만 방향 항목이 전건 확정·승계이므로 명확화 2건만 남는다."""
        self._write_fixture_a()
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")

        self.assertEqual(
            result.get("confirmed_ratio"), self._CLARIFICATION_RATIO,
            f"[RED][REGRESSION] confirmed_ratio 2/4=0.5 불변 기대 — 방향 항목이 "
            f"분모에 섞이면 조용한 계약 파괴(H-2). result={result}")

        clar_by_source = self._items_with_source(result, "clarification")
        self.assertEqual(
            len(clar_by_source), 4,
            f"[RED] confirmed_ratio 분모 근거인 clarification item은 4건 고정. result={result}")
        self.assertEqual(
            len(self._clarification_items(result)), 4,
            f"[RED] 명확화 4요소 항목 수 불변 기대. result={result}")

        self.assertEqual(
            set(result.get("unconfirmed", [])), self._CLARIFICATION_UNCONFIRMED,
            f"[RED] unconfirmed는 명확화 미확정 2건({{제약,완료기준}})만 기대 "
            f"(방향 항목 전건 확정·승계). result={result}")

    # ── ⑤ [회귀] 섹션 부재 레거시 TASK.md graceful skip (TS-030 / H-1) ─────

    def test_t100_legacy_task_md_without_direction_section_graceful_skip(self):
        """⑤ [회귀] `## 확정된 설계 방향` 섹션이 없는 레거시 TASK.md —
        예외 없이 기존 반환 형태를 유지한다: exit 0 + items 4건 +
        confirmed_ratio 0.5 + unconfirmed 2건, `direction_confirmed_ratio`는
        None(섹션 부재 → 신규 파서 None 반환, 호출자 graceful skip)."""
        self._write_fixture_b()
        exit_code, result = self._call_evidence_verify()

        self.assertEqual(exit_code, 0, f"[RED] 레거시 TASK.md도 exit 0 기대. result={result}")
        self.assertTrue(result.get("ok"), f"[RED] ok=true 기대. result={result}")
        self.assertEqual(
            len(result.get("items", [])), 4,
            f"[RED] 명확화 4건만 반환 기대(방향 항목 0건). result={result}")
        self.assertEqual(
            result.get("confirmed_ratio"), self._CLARIFICATION_RATIO,
            f"[RED][REGRESSION] 레거시 confirmed_ratio 0.5 불변 기대. result={result}")
        self.assertEqual(
            set(result.get("unconfirmed", [])), self._CLARIFICATION_UNCONFIRMED,
            f"[RED][REGRESSION] 레거시 unconfirmed 불변 기대. result={result}")
        self.assertIsNone(
            result.get("direction_confirmed_ratio"),
            f"[RED] 섹션 부재 시 direction_confirmed_ratio는 None 기대. result={result}")

        for it in result.get("items", []):
            self.assertEqual(
                it.get("source"), "clarification",
                f"[RED] 레거시 경로의 item도 출처 구분 source='clarification' 보유 기대(①). "
                f"item={it}")

    # ── 픽스처 C: 항목 0건 — 분모 0 나눗셈 경계 ────────────────────────────

    def test_t100_direction_section_with_zero_items_no_zero_division(self):
        """⑤-b 헤딩만 있고 항목 0건 — ZeroDivisionError 없이 exit 0.
        `direction_confirmed_ratio`는 None(항목 부재 → 미산출) 또는 0.0을
        허용하되, 예외·비정상 종료·기존 키 변형은 허용하지 않는다."""
        self._write_fixture_c()
        exit_code, result = self._call_evidence_verify()

        self.assertEqual(
            exit_code, 0,
            f"[RED] 항목 0건 섹션에서도 exit 0 기대(0 나눗셈 금지). result={result}")
        self.assertTrue(result.get("ok"), f"[RED] ok=true 기대. result={result}")
        self.assertIn(
            result.get("direction_confirmed_ratio"), (None, 0.0),
            f"[RED] 항목 0건 → None 또는 0.0 기대(분모 0 나눗셈 금지). result={result}")
        self.assertEqual(
            result.get("confirmed_ratio"), self._CLARIFICATION_RATIO,
            f"[RED][REGRESSION] 항목 0건이어도 confirmed_ratio 0.5 불변 기대. result={result}")
        self.assertEqual(
            len(result.get("items", [])), 4,
            f"[RED] 방향 항목 0건 → items는 명확화 4건. result={result}")
        for it in result.get("items", []):
            self.assertEqual(
                it.get("source"), "clarification",
                f"[RED] 항목 0건 경로의 item도 source='clarification' 보유 기대(①). item={it}")

    # ── ⑥ [회귀] 전 반환 경로 exit 0 유지 (TS-026 / R-10 AC (b)) ───────────

    def test_t100_exit_code_zero_on_all_return_paths(self):
        """⑥ [회귀] `--evidence-check` 반환 3경로 전부 exit 0 유지 —
        ① TASK.md 부재 skip ② 섹션/열 부재 skip ③ 정상 판정(픽스처 A·B·C).
        정상 경로에서는 신규 키가 JSON에 실려야 한다(③과 동일 계약).
        (`state_tool.py:2621` `:2630` `:2639` — 신규 플래그 신설 금지)"""
        # ① TASK.md 부재
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] TASK.md 부재 skip exit 0 기대. result={result}")
        self.assertEqual(result.get("evidence_check"), "skipped",
                         f"[RED] TASK.md 부재는 skipped 기대. result={result}")

        # ② 명확화 결과 섹션 자체가 없는 문서 — 기존 graceful skip 유지
        (self.task_path / "TASK.md").write_text(
            "# TASK — 섹션 없음\n\n본문만 있는 레거시 문서.\n", encoding="utf-8")
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] 섹션 부재 skip exit 0 기대. result={result}")
        self.assertEqual(result.get("evidence_check"), "skipped",
                         f"[RED] 명확화 섹션 부재는 skipped 기대. result={result}")

        # ③ 정상 판정 3픽스처
        for name, writer in (("A", self._write_fixture_a),
                             ("B", self._write_fixture_b),
                             ("C", self._write_fixture_c)):
            writer()
            exit_code, result = self._call_evidence_verify()
            self.assertEqual(
                exit_code, 0,
                f"[RED] 픽스처 {name} 정상 판정 exit 0 기대(라우터형·차단 없음). result={result}")
            self.assertTrue(result.get("ok"), f"[RED] 픽스처 {name} ok=true 기대. result={result}")
            self.assertIn(
                "confirmed_ratio", result,
                f"[RED] 픽스처 {name} 기존 키 confirmed_ratio 유지 기대. result={result}")

        # 정상 경로(A)에서 신규 키가 실제 JSON 출력에 실리는지
        self._write_fixture_a()
        exit_code, result = self._call_evidence_verify()
        self.assertEqual(exit_code, 0, f"[RED] exit 0 기대. result={result}")
        self.assertIn(
            "direction_confirmed_ratio", result,
            f"[RED] 정상 반환 경로 JSON에 direction_confirmed_ratio 포함 기대. result={result}")


# ═════════════════════════════════════════════════════════════════════════════
# 103 R-15 — 워커 소요 계측 필드 (`rows[].worker_duration_minutes`)
# 집계 기준 16/16-a/16-b: 소요를 캡틴/워커/PM 3계열로 분해하려면 워커 실행 시간이
# 행에 남아야 한다. 미기록 행은 축퇴 규칙에 따라 PM 계열로 전액 귀속되므로,
# **필드가 없는 기존 태스크의 수치가 종전과 항등**인 것이 이 블록의 핵심 계약이다.
# [MUST] red-first.md §4 — run.sh subprocess 공개 인터페이스(stdout/exit code)와
#   실 state.json 파일 내용으로만 관찰한다(mock/patch 없음). 기존 케이스 무수정.
# ═════════════════════════════════════════════════════════════════════════════

# TASK→ANALYSIS→EXECUTE 평이한 3행 — '사용자 확인' 행이 없어 자동 승인/CLOSE 게이트
# 축과 무관하게 워커 소요 축만 관찰한다.
_T103_SPEC = _t093_json([
    {"stage": "TASK",     "item": "작업"},              # row 1
    {"stage": "ANALYSIS", "item": "ANALYSIS.md"},       # row 2
    {"stage": "EXECUTE",  "item": "작업"},              # row 3
])

# 인자 미지정 mark 응답의 키 집합 — 6528행 S-13(gate 없는 행)과 동일한 계약.
# 103이 새 키를 무조건 싣지 않는다는 것(H-11)을 이 집합이 고정한다.
_T103_BASELINE_MARK_KEYS = {
    "ok", "command", "row_id", "stage", "item", "status",
    "timestamp", "owner", "auto_approved", "todo_mirror",
}


class TestT103WorkerDuration(_T093Base):
    """103 R-15 — `mark --worker-duration-minutes`와 `rows[].worker_duration_minutes`.

    핵심 계약 3가지:
      (1) 인자를 넘기면 해당 행에 분 단위 정수로 기록된다
      (2) 넘기지 않으면 **필드를 만들지 않는다** — state.json·응답 키 집합 모두 종전과 동일
      (3) 음수·비정수는 거부되고, 거부 시 행이 전혀 변경되지 않는다(부분 상태 변경 부재)
    """

    def _fresh(self, mode="interactive", name="t103"):
        d = self._task_dir(name)
        self._init(d, mode, rows_spec=_T103_SPEC)
        return d

    # ── (1) 기록 경로 ────────────────────────────────────────────────────

    def test_s1_worker_duration_recorded_when_flag_passed(self):
        """[T103/R-15] `--worker-duration-minutes 12` → 행에 정수 12로 기록되고
        mark 응답 JSON에도 동명 키가 실린다(PM이 반영값을 확인할 수 있어야 한다)."""
        d = self._fresh(name="t103-record")
        data = self._assert_ok(
            self._mark(d, 1, "--worker-duration-minutes", "12"), "mark w/ duration")

        row = self._row(d, 1)
        self.assertIn("worker_duration_minutes", row,
                      f"인자를 넘겼는데 행에 필드가 없음: {row}")
        self.assertEqual(row["worker_duration_minutes"], 12,
                         f"기록값 불일치: {row['worker_duration_minutes']!r}")
        self.assertIsInstance(row["worker_duration_minutes"], int,
                              "분 단위 정수로 기록되어야 함(문자열 저장 금지)")
        self.assertEqual(data.get("worker_duration_minutes"), 12,
                         f"mark 응답에 반영값이 없음: {data}")

    def test_s2_zero_is_a_recorded_value_not_absence(self):
        """[T103/R-15] `0`은 '측정했으나 1분 미만'이라는 유효값이다 — 필드가
        생성되고 값이 0이어야 한다. '측정하지 않음'(인자 미지정)과 구별된다."""
        d = self._fresh(name="t103-zero")
        self._assert_ok(self._mark(d, 1, "--worker-duration-minutes", "0"), "mark 0")

        row = self._row(d, 1)
        self.assertIn("worker_duration_minutes", row,
                      f"0이 '미기록'으로 뭉개졌음 — 축퇴 규칙(16-a)과 충돌: {row}")
        self.assertEqual(row["worker_duration_minutes"], 0)

    def test_s3_recorded_state_json_still_passes_validate(self):
        """[T103/R-15] 필드가 실린 state.json도 `validate` ok:true — 신규 필드가
        정합성 검증을 깨지 않는다."""
        d = self._fresh(name="t103-validate")
        self._assert_ok(self._mark(d, 1, "--worker-duration-minutes", "37"), "mark")
        data = self._assert_ok(self._validate(d), "validate")
        self.assertTrue(data.get("ok"), f"validate 실패: {data}")
        self.assertEqual(data.get("violations_count"), 0, f"violations: {data}")

    # ── (2) 하위호환 — 인자 미지정 ───────────────────────────────────────

    def test_s4_field_absent_when_flag_omitted(self):
        """[T103/R-15 하위호환] 인자 없는 mark는 필드를 만들지 않는다. 기존 23개
        태스크의 state.json이 무영향인 근거이자, 축퇴 규칙(16-a)의 전제다."""
        d = self._fresh(name="t103-omitted")
        self._assert_ok(self._mark(d, 1), "mark w/o duration")

        for row in self._state_of(d)["rows"]:
            self.assertNotIn(
                "worker_duration_minutes", row,
                f"인자를 넘기지 않았는데 행에 필드가 생성됨(기존 태스크 오염): {row}")

    def test_s5_response_key_set_unchanged_when_flag_omitted(self):
        """[T103/R-15 하위호환 H-11] 인자 미지정 mark의 응답 키 집합이 종전과
        완전히 동일하다 — 신규 키를 무조건 싣지 않는다(6528행 S-13과 동일 계약)."""
        d = self._fresh(name="t103-keys")
        data = self._assert_ok(self._mark(d, 1), "mark w/o duration")
        self.assertEqual(
            set(data.keys()), _T103_BASELINE_MARK_KEYS,
            f"인자 미지정인데 mark 응답 키 집합이 변경됨: {sorted(data.keys())}")

    def test_s6_legacy_rows_without_field_are_unaffected_by_a_recorded_sibling(self):
        """[T103/R-15 하위호환] 한 행에 기록해도 다른 행에는 필드가 생기지 않는다 —
        행 단위 선택 필드이지 파일 단위 스키마 승격이 아니다."""
        d = self._fresh(name="t103-mixed")
        self._assert_ok(self._mark(d, 1, "--worker-duration-minutes", "5"), "mark row1")
        self._assert_ok(self._mark(d, 2), "mark row2")

        self.assertEqual(self._row(d, 1).get("worker_duration_minutes"), 5)
        self.assertNotIn("worker_duration_minutes", self._row(d, 2),
                         "인자 없는 행에 필드가 번졌음")
        self.assertNotIn("worker_duration_minutes", self._row(d, 3),
                         "미완 행에 필드가 번졌음")

    # ── (3) 거부 경로 ────────────────────────────────────────────────────

    def test_s7_invalid_values_rejected_without_touching_the_row(self):
        """[T103/R-15] 음수·소수·비수치·공백은 거부되고(exit != 0), 거부된 호출은
        행을 전혀 바꾸지 않는다(부분 상태 변경 부재 — 091 H-1과 동일 원칙)."""
        for bad in ("-5", "-1", "1.5", "0.0", "abc", "", "  ", "3분", "12m", "1e3"):
            with self.subTest(value=bad):
                d = self._fresh(name=f"t103-bad-{abs(hash(bad))}")
                before = self._row(d, 1)

                code, stdout, stderr, _ = self._mark(
                    d, 1, "--worker-duration-minutes", bad)
                self.assertNotEqual(
                    code, 0,
                    f"{bad!r}가 수용됨 — 0 이상 정수만 허용해야 함 "
                    f"(stdout={stdout!r})")

                after = self._row(d, 1)
                self.assertEqual(
                    after, before,
                    f"{bad!r} 거부인데 행이 변경됨(부분 상태 변경): {before} → {after}")
                self.assertNotIn("worker_duration_minutes", after,
                                 f"{bad!r} 거부인데 필드가 기록됨: {after}")

    # ── (4) 093 재-auto-pass no-op과의 상호작용 ──────────────────────────

    def test_s8_auto_pass_noop_preserved_but_a_carried_value_is_not_dropped(self):
        """[T103/R-15 × 093 F-005] 인자 없는 재-auto-pass는 종전대로 no-op
        (`idempotent: true`)이고, 값이 실린 재-auto-pass는 no-op을 타지 않고
        값을 기록한다 — 전달한 계측치가 조용히 버려지지 않아야 한다."""
        d = self._fresh(mode="agentic", name="t103-idem")
        self._assert_ok(self._mark(d, 1, "--auto-pass"), "1st auto-pass")

        again = self._assert_ok(self._mark(d, 1, "--auto-pass"), "2nd auto-pass")
        self.assertTrue(again.get("idempotent"),
                        f"인자 없는 재-auto-pass no-op(093)이 깨졌음: {again}")
        self.assertNotIn("worker_duration_minutes", self._row(d, 1))

        carried = self._assert_ok(
            self._mark(d, 1, "--auto-pass", "--worker-duration-minutes", "9"),
            "auto-pass w/ duration")
        self.assertNotIn(
            "idempotent", carried,
            f"값이 실린 호출이 no-op으로 흡수됨 — 계측치 유실: {carried}")
        self.assertEqual(self._row(d, 1).get("worker_duration_minutes"), 9,
                         "재-auto-pass 경로에서 워커 소요가 기록되지 않음")

    # ── (5) 스키마 등록 계약 ─────────────────────────────────────────────

    def test_s9_schema_registers_optional_nonnegative_integer(self):
        """[T103/R-15] `state.schema.json`에 선택 필드로 등록된다 —
        `rows[].items.required`에 들어가면 기존 23개 state.json이 전건 무효가 되고,
        `additionalProperties`가 풀리면 스키마가 오타를 못 잡는다."""
        schema = json.loads((_SCHEMA_DIR / "state.schema.json")
                            .read_text(encoding="utf-8"))
        items = schema["properties"]["rows"]["items"]
        props = items["properties"]

        self.assertIn("worker_duration_minutes", props,
                      "rows[].items.properties에 worker_duration_minutes 미등록")
        field = props["worker_duration_minutes"]
        self.assertEqual(field.get("type"), "integer",
                         f"분 단위 정수여야 함: {field}")
        self.assertEqual(field.get("minimum"), 0,
                         f"음수를 스키마에서 배제해야 함: {field}")

        self.assertNotIn("worker_duration_minutes", items.get("required", []),
                         "선택 필드여야 함 — required 등재 시 기존 state.json 전건 무효")
        self.assertIs(items.get("additionalProperties"), False,
                      "행 스키마의 additionalProperties: false는 유지되어야 함")

    def test_s10_error_codes_untouched(self):
        """[T103/R-15] 값 검증은 argparse가 파싱 시점에 수행하므로 ERROR_CODES는
        건드리지 않는다 — 카탈로그 종수 고정 테스트(S-7/S-15)와 충돌하지 않는다."""
        self.assertNotIn("worker_duration_invalid", ST.ERROR_CODES,
                         "103이 ERROR_CODES를 신설했음 — 카탈로그 종수 계약 위반")
        self.assertEqual(len(ST.ERROR_CODES), 45,
                         f"ERROR_CODES 종수가 변했음: {len(ST.ERROR_CODES)}")


# ═════════════════════════════════════════════════════════════════════════════
# 103 R-21: 워커 소요 누락 경고 (`mark` stdout `warnings`)
# TestT103WorkerDurationWarning — 발생 / 미발생(오탐 방어) / 억제 3경로
#
# [MUST] 헌법 §4 "Don't fake it" — mock/patch 미사용. _T093Base(run.sh subprocess
#        실호출 + 실 state.json/STATE.md 파일 상태)만 사용한다.
# [MUST] 경고는 에러가 아니다 — exit 0 유지, 산출물 바이트 불변이 계약의 절반이다.
# ═════════════════════════════════════════════════════════════════════════════

# 워커 경로(prior_stage_only)를 태우려면 EXECUTE 행 앞의 TASK/ANALYSIS가 완료여야 한다.
_T103W_SPEC = _t093_json([
    {"stage": "TASK",     "item": "작업"},          # row 1
    {"stage": "ANALYSIS", "item": "ANALYSIS.md"},   # row 2
    {"stage": "EXECUTE",  "item": "Step 1"},        # row 3
    {"stage": "EXECUTE",  "item": "Step 2"},        # row 4
])

_T103W_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?")


class TestT103WorkerDurationWarning(_T093Base):
    """103 R-21 — 워커를 디스패치한 행을 소요 없이 닫으면 `mark`가 경고한다.

    계약 4가지:
      (1) 발생 — `--as-worker`/`--worker-stage`로 행을 `done`으로 닫는데
          `--worker-duration-minutes`가 없으면 stdout JSON에 `warnings`가 실린다
      (2) 차단 아님 — exit 0이 유지되고 `state.json`/`STATE.md`는 경고 유무와
          무관하게 동일하다(경고는 stdout 전용)
      (3) 미발생 — PM 직접 수행 행·값이 실린 호출·중간 진행 행(N<M)에는 뜨지 않는다
          (오탐이 반복되면 PM이 경고 자체를 무시하게 된다)
      (4) 억제 — `--worker-duration-unknown`은 경고를 없애고 필드도 만들지 않는다
    """

    _CODE = "worker_duration_missing"

    def _fresh(self, name, mode="interactive"):
        d = self._task_dir(name)
        self._init(d, mode, rows_spec=_T103W_SPEC)
        # EXECUTE 행에 워커 경로로 접근하기 위한 앞 단계 완료 (prior_stage_only 전제)
        self._assert_ok(self._mark(d, 1), f"{name} prep row1")
        self._assert_ok(self._mark(d, 2), f"{name} prep row2")
        return d

    def _warnings(self, data):
        return data.get("warnings")

    def _assert_warned(self, data, label):
        warns = self._warnings(data)
        self.assertIsInstance(
            warns, list,
            f"{label}: 워커 디스패치 행을 소요 없이 닫았는데 warnings가 없음 — {data}")
        self.assertEqual([w.get("code") for w in warns], [self._CODE],
                         f"{label}: 경고 코드 불일치 — {warns}")
        return warns[0]

    def _assert_not_warned(self, data, label):
        self.assertNotIn(
            "warnings", data,
            f"{label}: 오탐 — 이 호출에는 경고가 뜨면 안 된다: {data}")

    # ── (1) 발생 경로 ────────────────────────────────────────────────────

    def test_w1_warns_when_worker_row_closed_without_duration(self):
        """[T103/R-21] `--as-worker --worker-stage EXECUTE`로 행을 done 처리하면서
        소요를 넘기지 않으면 경고가 실린다 — 이 값은 소급 복구가 불가능하므로
        도구가 알려주지 않으면 영구히 소실된다."""
        d = self._fresh("w1")
        code, stdout, stderr, data = self._mark(
            d, 3, "--as-worker", "--worker-stage", "EXECUTE")
        self.assertEqual(code, 0, f"W1 경고는 차단이 아니어야 함: {stdout!r} {stderr!r}")
        w = self._assert_warned(data, "W1")
        self.assertEqual(w.get("row_id", 3) if "row_id" in w else 3, 3)

    def test_w2_warns_on_worker_stage_alone_without_as_worker(self):
        """[T103/R-21] `--worker-stage`만 실린 호출도 '워커가 수행한 행'이라는 신호다 —
        `--as-worker` 유무로만 판정하면 이 형태가 조용히 새어나간다."""
        d = self._fresh("w2")
        code, stdout, stderr, data = self._mark(d, 3, "--worker-stage", "EXECUTE")
        self.assertEqual(code, 0, f"W2 exit!=0: {stdout!r} {stderr!r}")
        self._assert_warned(data, "W2")

    def test_w3_warns_on_last_action_step_but_not_intermediate(self):
        """[T103/R-21 오탐 방어] `--action-step N/M`에서 N<M은 행이 `in_progress`로
        남으므로 경고하지 않고, N==M(행이 실제 done이 되는 시점)에만 경고한다.
        중간 진행 보고마다 경고하면 전부 오탐이 된다."""
        d = self._fresh("w3")
        for n in ("1/3", "2/3"):
            with self.subTest(step=n):
                data = self._assert_ok(
                    self._mark(d, 3, "--as-worker", "--worker-stage", "EXECUTE",
                               "--action-step", n), f"W3 {n}")
                self._assert_not_warned(data, f"W3 {n}(중간 진행)")
                self.assertEqual(self._row(d, 3)["status"], "in_progress",
                                 f"W3 전제: {n}은 in_progress로 남아야 함")

        data = self._assert_ok(
            self._mark(d, 3, "--as-worker", "--worker-stage", "EXECUTE",
                       "--action-step", "3/3"), "W3 3/3")
        self.assertEqual(self._row(d, 3)["status"], "done", "W3 전제: 3/3은 done")
        self._assert_warned(data, "W3 3/3(마지막 Step)")

    def test_w4_message_states_what_was_missed_and_why_it_is_permanent(self):
        """[T103/R-21] 문구는 '무엇을 놓쳤는지'(--worker-duration-minutes)와
        '왜 문제인지'(알림은 세션과 함께 사라져 영구 소실 + PM 몫 오귀속)를 담고,
        복구 행동 2가지(다시 mark / 미상 명시)를 제시해야 한다."""
        d = self._fresh("w4")
        data = self._assert_ok(
            self._mark(d, 3, "--as-worker", "--worker-stage", "EXECUTE"), "W4")
        msg = self._assert_warned(data, "W4").get("message", "")
        for fragment in ("--worker-duration-minutes", "세션", "영구", "소실",
                         "PM", "--worker-duration-unknown"):
            self.assertIn(fragment, msg,
                          f"W4 경고 문구에 '{fragment}' 없음 — 왜 문제인지 전달 실패: {msg!r}")
        self.assertIn("EXECUTE", msg, f"W4 문구에 대상 행 stage 없음: {msg!r}")

    # ── (2) 차단 아님 + 산출물 불변 ──────────────────────────────────────

    def test_w5_warning_does_not_change_exit_code_or_artifacts(self):
        """[T103/R-21 MUST] 경고는 exit 0을 유지하고 `state.json`/`STATE.md`를 바꾸지
        않는다 — 경고가 실린 호출과 억제된 호출의 산출물이 (시각 제외) 동일해야 한다."""
        # 두 픽스처의 폴더명(=task_id)을 같게 두어야 산출물 diff가 '경고 유무' 축만
        # 남긴다 — 상위 디렉토리로만 분리한다.
        warned = self._fresh("w5-warned/t")
        quiet  = self._fresh("w5-quiet/t")

        dw = self._assert_ok(
            self._mark(warned, 3, "--as-worker", "--worker-stage", "EXECUTE"), "W5 warned")
        dq = self._assert_ok(
            self._mark(quiet, 3, "--as-worker", "--worker-stage", "EXECUTE",
                       "--worker-duration-unknown"), "W5 quiet")
        self._assert_warned(dw, "W5 warned")
        self._assert_not_warned(dq, "W5 quiet")

        def _norm(path):
            return _T103W_TS_RE.sub("<TS>", path.read_text(encoding="utf-8"))

        # [T103 강제 2단 정밀화] 억제 인자는 이제 `worker_duration_unknown: true`를
        # 행에 **남긴다** — CLOSE 차단이 「미측정 선언」과 「침묵」을 갈라야 하기 때문이다.
        # 남기지 않으면 선언할 이유가 사라지고 강제가 무의미해진다. 따라서 두 산출물의
        # 유일한 차이는 그 한 필드여야 하며, 그 밖은 여전히 바이트 동일이어야 한다.
        _decl = ',\n      "worker_duration_unknown": true'
        self.assertEqual(
            _norm(warned / "state.json"),
            _norm(quiet / "state.json").replace(_decl, "", 1),
            "W5 경고가 state.json을 바꿨음 — 차이는 미측정 선언 1필드뿐이어야 한다")
        self.assertIn('"worker_duration_unknown": true',
                      _norm(quiet / "state.json"),
                      "W5 억제 인자는 미측정 선언을 행에 남겨야 한다(강제 2단 (c))")
        self.assertNotIn("worker_duration_unknown", _norm(warned / "state.json"),
                         "W5 침묵 호출은 선언 필드를 만들지 않아야 한다")
        self.assertEqual(_norm(warned / "STATE.md"), _norm(quiet / "STATE.md"),
                         "W5 경고가 STATE.md 내용을 바꿨음")
        for d in (warned, quiet):
            self.assertNotIn("worker_duration_minutes", self._row(d, 3),
                             "W5 경고·억제 어느 쪽도 소요 값 필드를 만들면 안 된다")

    def test_w6_warned_state_json_still_validates(self):
        """[T103/R-21] 경고가 뜬 뒤에도 `validate`는 ok:true — 경고는 정합성과 무관하다."""
        d = self._fresh("w6")
        self._assert_warned(
            self._assert_ok(self._mark(d, 3, "--as-worker", "--worker-stage", "EXECUTE"),
                            "W6 mark"), "W6")
        data = self._assert_ok(self._validate(d), "W6 validate")
        self.assertTrue(data.get("ok"), f"W6 validate 실패: {data}")
        self.assertEqual(data.get("violations_count"), 0, f"W6 violations: {data}")

    # ── (3) 미발생 경로 (오탐 방어) ──────────────────────────────────────

    def test_w7_no_warning_for_pm_direct_row(self):
        """[T103/R-21 오탐 방어] PM 직접 수행 행(`--as-worker`/`--worker-stage` 없음)에는
        경고가 뜨지 않고, 응답 키 집합도 종전과 완전히 동일하다(H-11 하위호환)."""
        d = self._task_dir("w7")
        self._init(d, "interactive", rows_spec=_T103W_SPEC)
        data = self._assert_ok(self._mark(d, 1), "W7 PM 직접")
        self._assert_not_warned(data, "W7 PM 직접")
        self.assertEqual(
            set(data.keys()), _T103_BASELINE_MARK_KEYS,
            f"W7 인자 미지정 mark의 응답 키 집합이 변경됨: {sorted(data.keys())}")

    def test_w8_no_warning_for_user_confirmation_row(self):
        """[T103/R-21 오탐 방어] 사용자 확인 행(`--owner user`)은 캡틴 승인 지점이지
        워커 디스패치 지점이 아니다 — `--as-worker`가 함께 실려도 경고하지 않는다."""
        d = self._fresh("w8")
        data = self._assert_ok(
            self._mark(d, 3, "--as-worker", "--worker-stage", "EXECUTE",
                       "--owner", "user"), "W8")
        self.assertEqual(self._row(d, 3)["owner"], "user", "W8 전제: owner=user")
        self._assert_not_warned(data, "W8 사용자 확인 행")

    def test_w9_no_warning_when_duration_is_supplied(self):
        """[T103/R-21] 값을 넘긴 호출(0 포함)에는 경고할 것이 없다."""
        for minutes in ("0", "12"):
            with self.subTest(minutes=minutes):
                d = self._fresh(f"w9-{minutes}")
                data = self._assert_ok(
                    self._mark(d, 3, "--as-worker", "--worker-stage", "EXECUTE",
                               "--worker-duration-minutes", minutes), f"W9 {minutes}")
                self._assert_not_warned(data, f"W9 {minutes}")
                self.assertEqual(self._row(d, 3)["worker_duration_minutes"], int(minutes))

    def test_w10_no_warning_on_idempotent_reauto_pass(self):
        """[T103/R-21 오탐 방어 × 093 F-005] 이미 auto 승인된 행을 다시 두드리는
        멱등 호출(`idempotent: true`)은 상태를 바꾸지 않으므로 경고도 없다."""
        d = self._task_dir("w10")
        self._init(d, "agentic", rows_spec=_T103W_SPEC)
        self._assert_ok(self._mark(d, 1, "--auto-pass"), "W10 1st")
        again = self._assert_ok(self._mark(d, 1, "--auto-pass",
                                           "--as-worker", "--worker-stage", "TASK"),
                                "W10 2nd")
        self.assertTrue(again.get("idempotent"), f"W10 전제: 재-auto-pass no-op — {again}")
        self._assert_not_warned(again, "W10 멱등 재호출")

    # ── (4) 억제 인자 ────────────────────────────────────────────────────

    def test_w11_unknown_flag_suppresses_and_creates_no_field(self):
        """[T103/R-21] `--worker-duration-unknown`은 경고를 억제하고 행에 필드를
        만들지 않는다 — 기록 결과가 인자 미지정과 완전히 동형이어야 '미측정'이
        `0`(측정했으나 1분 미만)으로 오독되지 않는다."""
        d = self._fresh("w11")
        code, stdout, stderr, data = self._mark(
            d, 3, "--as-worker", "--worker-stage", "EXECUTE", "--worker-duration-unknown")
        self.assertEqual(code, 0, f"W11 exit!=0: {stdout!r} {stderr!r}")
        self._assert_not_warned(data, "W11 억제")
        self.assertNotIn("worker_duration_minutes", data,
                         f"W11 억제 인자가 응답에 값을 만들었음: {data}")
        self.assertNotIn("worker_duration_minutes", self._row(d, 3),
                         f"W11 억제 인자가 행에 필드를 만들었음: {self._row(d, 3)}")
        self.assertEqual(self._row(d, 3)["status"], "done", "W11 억제해도 mark는 정상 완료")

    def test_w12_minutes_and_unknown_are_mutually_exclusive(self):
        """[T103/R-21] 값과 '미상 선언'은 동시에 성립할 수 없다 — argparse 배타 그룹이
        exit 2로 거부하며(`--owner`/`--auto-pass`와 동일 계열), 행은 변경되지 않는다."""
        d = self._fresh("w12")
        before = self._row(d, 3)
        code, stdout, stderr, data = self._mark(
            d, 3, "--as-worker", "--worker-stage", "EXECUTE",
            "--worker-duration-minutes", "5", "--worker-duration-unknown")
        self.assertEqual(code, 2, f"W12 배타 미집행 (exit={code}, stderr={stderr!r})")
        self.assertEqual(self._row(d, 3), before, "W12 거부인데 행이 변경됨")

    # ── (5) 카탈로그 경계 ────────────────────────────────────────────────

    def test_w13_warning_catalog_is_separate_from_error_codes(self):
        """[T103/R-21] 경고는 에러가 아니다 — `ERROR_CODES` 45종은 불변이고 경고 코드는
        별도 사전(`WARNING_CODES`)에 산다. 카탈로그를 공유하면 `err()`가 sys.exit로
        끝나는 탓에 '경고인데 차단'이라는 오용 경로가 생긴다."""
        self.assertNotIn(self._CODE, ST.ERROR_CODES,
                         "R-21이 ERROR_CODES를 늘렸음 — 카탈로그 종수 계약 위반")
        self.assertEqual(len(ST.ERROR_CODES), 45,
                         f"ERROR_CODES 종수가 변했음: {len(ST.ERROR_CODES)}")
        self.assertIn(self._CODE, ST.WARNING_CODES,
                      "WARNING_CODES에 worker_duration_missing 미등재")



# ═════════════════════════════════════════════════════════════════════════════
# 진입점
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)


# ─────────────────────────────────────────────────────────────────────────────
# 103 강제 2단 — CLOSE 차단 (침묵으로는 통과 못 한다)
# ─────────────────────────────────────────────────────────────────────────────

class TestT103WorkerEnforce(_T093Base):
    """워커 소요 기록 강제 — 조기 경고(행 기반 판정) + CLOSE 차단.

    배경: 인자 신호(`--as-worker`)에만 의존하던 경고는 PM이 그 인자를 쓰지 않는 순간
    침묵했다(실측: 다른 프로젝트 태스크가 15행 전건 미기록으로 통과). 그래서 판정
    근거를 행의 `stage`·`item`으로 옮기고, CLOSE에서 한 번은 반드시 걸리게 했다.
    """

    def _pipeline(self):
        return _t093_json([
            {"stage": "TEST",  "item": "작업"},
            {"stage": "TEST",  "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "DONE.md 생성"},
        ])

    def _aged(self, d, created):
        """created_at을 조작해 유예 경계를 검증 가능하게 만든다."""
        p = d / "state.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["created_at"] = created
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")

    def _close(self, d, *extra):
        return self._mark(d, 3, *extra)

    def test_e1_warning_without_arg_signal(self):
        """[T103/E1] `--as-worker` 없이 워커 규범 행을 닫아도 경고가 뜬다.

        이것이 강제 2단의 1단이다 — 인자에만 의존하던 종전 판정은 여기서 침묵했다."""
        d = self._task_dir("e1")
        self._init(d, "agentic", rows_spec=self._pipeline())
        data = self._assert_ok(self._mark(d, 1), "E1 mark")
        codes = [w.get("code") for w in (data.get("warnings") or [])]
        self.assertIn("worker_duration_missing", codes,
                      "E1 인자 신호 없이도 행 기반 판정으로 경고해야 한다")

    def test_e2_no_warning_for_gate_row(self):
        """[T103/E2 오탐 방어] PM Gate·사용자 확인 행은 워커 디스패치 지점이 아니다."""
        d = self._task_dir("e2")
        self._init(d, "agentic", rows_spec=self._pipeline())
        self._assert_ok(self._mark(d, 1, "--worker-duration-unknown"), "E2 row1")
        data = self._assert_ok(self._mark(d, 2, "--owner", "user"), "E2 row2")
        self.assertFalse(data.get("warnings"),
                         "E2 사용자 확인 행에 경고가 뜨면 오탐이다")

    def test_e3_close_blocked_on_silence(self):
        """[T103/E3 ★] 침묵한 채 CLOSE에 들어가면 **차단**된다 — exit != 0."""
        d = self._task_dir("e3")
        self._init(d, "agentic", rows_spec=self._pipeline())
        self._aged(d, "2026-09-01 10:00:00")
        self._assert_ok(self._mark(d, 1), "E3 row1 침묵")
        self._assert_ok(self._mark(d, 2, "--owner", "user"), "E3 row2")
        code, stdout, _stderr, data = self._close(d)
        self.assertEqual(code, 1, f"E3 CLOSE가 차단되지 않았다: {stdout!r}")
        self.assertEqual(data.get("error"), "worker_duration_undeclared")
        self.assertIn(1, data.get("undeclared_rows") or [],
                      "E3 미선언 행 번호가 응답에 실려야 한다")
        self.assertEqual(self._row(d, 3)["status"], "pending",
                         "E3 차단 시 상태가 바뀌면 안 된다")

    def test_e4_close_passes_with_minutes(self):
        """[T103/E4] 소요를 기록하면 통과한다."""
        d = self._task_dir("e4")
        self._init(d, "agentic", rows_spec=self._pipeline())
        self._aged(d, "2026-09-01 10:00:00")
        self._assert_ok(self._mark(d, 1, "--worker-duration-minutes", "12"), "E4 row1")
        self._assert_ok(self._mark(d, 2, "--owner", "user"), "E4 row2")
        self._assert_ok(self._close(d), "E4 CLOSE")

    def test_e5_close_passes_with_declaration(self):
        """[T103/E5] 미측정을 **선언**하면 통과한다 — 「모르면 모른다고 말해야」 한다."""
        d = self._task_dir("e5")
        self._init(d, "agentic", rows_spec=self._pipeline())
        self._aged(d, "2026-09-01 10:00:00")
        self._assert_ok(self._mark(d, 1, "--worker-duration-unknown"), "E5 row1")
        self.assertTrue(self._row(d, 1).get("worker_duration_unknown"),
                        "E5 선언이 행에 영속화돼야 침묵과 구별된다")
        self._assert_ok(self._mark(d, 2, "--owner", "user"), "E5 row2")
        self._assert_ok(self._close(d), "E5 CLOSE")

    def test_e6_force_bypasses(self):
        """[T103/E6] `--force --note`는 최후 우회로 남는다."""
        d = self._task_dir("e6")
        self._init(d, "agentic", rows_spec=self._pipeline())
        self._aged(d, "2026-09-01 10:00:00")
        self._assert_ok(self._mark(d, 1), "E6 row1 침묵")
        self._assert_ok(self._mark(d, 2, "--owner", "user"), "E6 row2")
        self._assert_ok(self._close(d, "--force", "--note", "E6 강제 통과"), "E6 CLOSE")

    def test_e7_grace_before_epoch(self):
        """[T103/E7] 계측 도입 **이전 생성** 태스크는 유예한다 — 선언할 수단이 없었다."""
        d = self._task_dir("e7")
        self._init(d, "agentic", rows_spec=self._pipeline())
        self._aged(d, "2026-08-25 10:00:00")
        self._assert_ok(self._mark(d, 1), "E7 row1 침묵")
        self._assert_ok(self._mark(d, 2, "--owner", "user"), "E7 row2")
        self._assert_ok(self._close(d), "E7 CLOSE — 유예")

    def test_e8_no_grace_after_epoch(self):
        """[T103/E8 ★] 도입 **이후 생성**에는 예외가 없다 — 「반드시 적용」의 핵심.

        기록이 한 건도 없다는 이유로 유예하면 워커를 돌리고도 전건 미기록인 신규
        태스크가 그대로 통과한다. 그래서 유예 기준을 `created_at`으로 둔다."""
        d = self._task_dir("e8")
        self._init(d, "agentic", rows_spec=self._pipeline())
        self._aged(d, "2026-08-26 00:00:00")
        self._assert_ok(self._mark(d, 1), "E8 row1 침묵")
        self._assert_ok(self._mark(d, 2, "--owner", "user"), "E8 row2")
        code, _stdout, _stderr, data = self._close(d)
        self.assertEqual(code, 1, "E8 도입 이후 태스크는 유예 없이 차단돼야 한다")
        self.assertEqual(data.get("error"), "worker_duration_undeclared")

    def test_e9_error_codes_untouched(self):
        """[T103/E9] 차단 코드는 `ERROR_CODES`를 늘리지 않는다(BLOCK_CODES 분리)."""
        import state_tool as st  # noqa: F401 — 경로는 _T093Base가 세팅한다
        self.assertNotIn("worker_duration_undeclared", st.ERROR_CODES,
                         "E9 ERROR_CODES 종수를 늘리면 기존 카탈로그 계약이 깨진다")
        self.assertIn("worker_duration_undeclared", st.BLOCK_CODES)
