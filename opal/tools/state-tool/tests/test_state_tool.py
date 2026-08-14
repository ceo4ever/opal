"""
@header {
  "module": "test_state_tool",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool 단위 테스트 — 9개 명령 happy path + 23종 에러 코드 × 최소 1건 + G-5~G-15 시나리오. 005: TestClarificationGate 신설 — verify --clarification-check + TASK→다음단계 자동 훅 RED-first 케이스 ①~⑨ + 회귀 보호. 054: TestOwnerNamePlaceholder 신설 — note '{owner_name}' 플레이스홀더 identity.md write-time 치환 RED-first(S-1~S-7). 056: TestOpplSkillInit 신설 — `--skill oppl` enum 미등록 RED-first(S-020, H-1) — run.sh subprocess 실호출로 공개 인터페이스만 검증(mock 미사용). 070: task-step 키 주소 체계 도입 1차 RED-first — TestPipelineSpecValidate/TestPipelineJsonInit/TestStateSchema11Compat/TestTaskStepAddressing/TestActionStepRename/TestAddRowKey/TestOpddEnumDrift/TestGroupAPipelineSpecs/TestBackwardCompatAliases 9종 신설(TEST-SCENARIO.md S-1~S-14, PLAN §3.7.2) — 미구현 기능이므로 전부 FAIL 기대(RED 증거). 072: TestNextActionAutoDerive 신설 — STATE.md '다음 액션' 자동 파생 RED-first(TEST-SCENARIO.md S-1~S-4,S-6,S-7) — init next_action 영속화+schema optional 등록, advance/mark 프론티어 파생(pending '진입'/in_progress '진행 중'/전체완료 '태스크 완료'), 첫 줄만 치환(하위 자유기재 보존), --next-action 오버라이드 우선+비지속 복귀 — 공개 CLI 경로(직접 호출+run.sh subprocess)로만 검증, 미구현이므로 실패 기대(RED 증거). 074: TestImportPreservesKeys 신설 — `--import-existing` task-step key 유실 결함 RED-first(TEST-SCENARIO.md S-a~S-e) — force+import-existing 후 rows[].key 100% 보존, pipeline.json 폴백 복원, key 원천 전무 시 keyless+stderr 경고(하위호환), schema_version 1.1 유지, 동일 (stage,item) 중복 순서 소비 — 공개 cmd_init 호출 + 실 파일 I/O로만 검증, 수정 전 코드에서 FAIL 기대(RED 증거). 076: TestTodoMirror 신설 — build_todo_mirror 파생 규칙(TS-001~007): init create 페이로드·전부pending→pending·전부done→completed·advance/부분→in_progress·na 중립·블로커 in_progress 유지·영속 경계(state.json 미영속+schema validate 통과) — 공개 cmd_init/advance/mark/block ok() stdout 페이로드 캡처로만 검증. 088: TestCloseHistoryLink 신설(TS-1~TS-7) — CLOSE 마지막 행 mark 시 link_memory_history()가 <프로젝트루트>/.opal/MEMORY.json history에 행을 자동 생성(title/path/stage/result 파생값, date는 memory-tool KST 충전)·재mark 멱등(duplicate_skipped)·MEMORY.json 부재/손상 시 비차단(ok:true + skipped/failed)·비CLOSE 행 무발동 대조군·result 보강 리마인더 구성요소·state.json 영속 경계(schema validate 통과) — 공개 cmd_mark 호출 + 실 MEMORY.json 파일 내용으로만 검증(내부 함수 mock 없음, 블랙박스 결함 주입). 091(RED-first, mode:red, F-004 게이트 집행 배선): TestTaskStepGate 신설(TEST-SCENARIO S-10~S-17) — check_gate_artifacts()/build_gate_payload()가 아직 없어(Step 8 GREEN 이전) 실 pipeline.json(opd/opdw/opsdd) 기반 gate 정의를 state.json 행에 직접 주입하는 픽스처로 산출물 부재 차단(H-1)·부분 상태 변경 부재·checklist dict 페이로드(H-6)·gate 없는 행 무영향(H-2/H-3)·빈 artifacts 비차단(opdw 실사례)·--force --note 우회 의사결정 로그(H-5)·경로 이탈 토큰 거부(H-4)·glob 토큰 매칭(opsdd 실사례)을 검증(공개 cmd_mark 호출 + 실 state.json/STATE.md 파일 내용, mock 없음). TestPipelineSpecValidate에 gate violation 4종(spec_gate_type_invalid/spec_gate_missing_field/spec_gate_field_type_invalid/spec_gate_checklist_empty, S-9) 케이스 + 실 pipeline.json 10종 유효성 케이스 추가. TestErrorCodesCompleteness에 091 신규 5종 반영(39→44).",
  "exports": [
    "TestInit", "TestShow", "TestAdvance", "TestMark",
    "TestBlock", "TestValidate", "TestAddRow", "TestStatus", "TestGatePass",
    "TestErrorCodes", "TestFreeTextPreservation", "TestClarificationGate",
    "TestOwnerNamePlaceholder", "TestOpplSkillInit",
    "TestPipelineSpecValidate", "TestPipelineJsonInit", "TestStateSchema11Compat",
    "TestTaskStepAddressing", "TestActionStepRename", "TestAddRowKey",
    "TestOpddEnumDrift", "TestGroupAPipelineSpecs", "TestBackwardCompatAliases",
    "TestNextActionAutoDerive", "TestImportPreservesKeys", "TestTodoMirror",
    "TestCloseHistoryLink", "TestTaskStepGate"
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
import json
import os
import pathlib
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
        """init: STATE.md 파일 생성 및 마커 포함 확인 (PLAN §2.11 G-8, T-6)"""
        self._init()
        md = self._md()
        self.assertIn("<!-- pipeline:start -->", md)
        self.assertIn("<!-- pipeline:end -->", md)
        self.assertIn("## 현재 상태", md)

    def test_init_g8_free_text_sections(self):
        """G-8: init이 자유 텍스트 3개 섹션을 정확히 생성 (PLAN §2.11 G-8)"""
        self._init(next_action="테스트 다음 액션")
        md = self._md()
        # 3개 자유 텍스트 섹션 존재 확인
        self.assertIn("## 의사결정 로그", md)
        self.assertIn("## 블로커", md)
        self.assertIn("없음", md)
        self.assertIn("## 다음 액션", md)
        self.assertIn("테스트 다음 액션", md)
        # 의사결정 로그 빈 표 헤더
        self.assertIn("| # | 시점 | 결정 | 근거 |", md)

    def test_init_agentic_auto_na_user_confirmation(self):
        """init agentic: 사용자 확인 행(CLOSE 제외) auto-na 처리 (PLAN §2.20.1)"""
        rows = json.dumps([
            {"stage": "TASK",    "item": "작업"},
            {"stage": "TASK",    "item": "사용자 확인"},
            {"stage": "CLOSE",   "item": "사용자 확인"},
        ])
        self._init(rows_spec=rows, mode="agentic")
        state = self._state()
        # TASK 사용자 확인 행 → na
        task_user = next(r for r in state["rows"] if r["stage"] == "TASK" and r["item"] == "사용자 확인")
        self.assertEqual(task_user["status"], "na")
        self.assertEqual(task_user["status_label"], "-")
        self.assertEqual(task_user["owner"], "auto")
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
        """show --format full: STATE.md 전체 본문 출력 (PLAN §2.14 G-11)"""
        result = self._show("full")
        self.assertTrue(result["ok"])
        self.assertEqual(result["format"], "full")
        self.assertIn("content", result)
        self.assertIn("## 현재 상태", result["content"])

    def test_show_md_marker_missing_fallback(self):
        """G-11: 마커 손실 시 show md fallback — 헤더 명시 + json rows 재구성 (PLAN §2.14 G-11)"""
        # 마커 제거
        md = self._md()
        md_no_marker = md.replace("<!-- pipeline:start -->", "").replace("<!-- pipeline:end -->", "")
        (self.task_path / "STATE.md").write_text(md_no_marker)

        result = self._show("md")
        self.assertTrue(result["ok"])
        self.assertFalse(result.get("marker_present", True))
        self.assertIn("fallback", result.get("content", ""))

    def test_show_json_marker_missing_marker_present_false(self):
        """G-11: 마커 손실 시 show json → marker_present=false (PLAN §2.14 G-11)"""
        md = self._md()
        md_no_marker = md.replace("<!-- pipeline:start -->", "").replace("<!-- pipeline:end -->", "")
        (self.task_path / "STATE.md").write_text(md_no_marker)
        result = self._show("json")
        self.assertFalse(result.get("marker_present", True))

    def test_show_full_marker_missing_warning_prepend(self):
        """G-11: 마커 손실 시 show full → WARNING 주석 prepend (PLAN §2.14 G-11)"""
        md = self._md()
        md_no_marker = md.replace("<!-- pipeline:start -->", "").replace("<!-- pipeline:end -->", "")
        (self.task_path / "STATE.md").write_text(md_no_marker)
        result = self._show("full")
        self.assertIn("WARNING", result.get("content", ""))


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
        """G-6: advance 후 '## 현재 상태' - 진행: 라인 갱신 (PLAN §2.11 G-6)"""
        self._advance(1)
        md = self._md()
        self.assertIn("- 진행: TASK 단계", md)


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
        """G-6: CLOSE 마지막 State Gate mark → current_status=done, '- 상태: 완료' (PLAN §2.11 G-6)"""
        # SIMPLE_ROWS_SPEC: row4 = CLOSE/State Gate
        # 먼저 사용자 확인 행(row3)을 user로 mark해야 close gate 통과
        self._mark(3, owner="user")  # EXECUTE/작업 → user mark (close gate 위해)
        # 실제로 CLOSE 첫 행 전에 사용자 확인 행을 owner=user로 처리
        # SIMPLE_ROWS_SPEC에서 row3=EXECUTE/작업은 사용자 확인이 아님
        # 최소 사양의 rows로 재init
        rows = json.dumps([
            {"stage": "TASK", "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows, force=True, note="테스트 재초기화")
        self._mark(1, owner="user")  # 사용자 확인 → done/user
        self._mark(2)  # CLOSE State Gate → done
        state = self._state()
        self.assertEqual(state["current_status"], "done")
        md = self._md()
        self.assertIn("- 상태: 완료", md)

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
        """G-6: mark --as-worker --step N/M → '- 진행: Step N/M 완료' (PLAN §2.11 G-6)"""
        # prior_stage_only guard: EXECUTE 대상 행은 앞 단계(TASK·PLAN)가 완료여야 통과
        self._mark(1)  # TASK 완료
        self._mark(2)  # PLAN 완료
        self._mark(3, as_worker=True, worker_stage="EXECUTE", step="2/5")
        md = self._md()
        self.assertIn("- 진행: Step 2/5 완료", md)


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
        """G-6: block 후 '- 상태: 블로커' (PLAN §2.11 G-6)"""
        self._block(1)
        md = self._md()
        self.assertIn("- 상태: 블로커", md)


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
        """G-6: add-row(done→additional_work) 후 '- 상태: 추가작업중' (PLAN §2.11 G-6)"""
        state = self._state()
        state["current_status"] = "done"
        ST.save_state_json(self.task_path, state)
        self._add_row(after=1, stage="CLOSE", item="추가")
        md = self._md()
        self.assertIn("- 상태: 추가작업중", md)

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
        """G-6: status --set 후 '- 상태:' 라인 갱신 (PLAN §2.11 G-6)"""
        self._status_set("blocked")
        md = self._md()
        self.assertIn("- 상태: 블로커", md)


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

    # ── E-2: marker_missing ───────────────────────────────────────────────────
    def test_marker_missing(self):
        """#2 marker_missing: STATE.md 마커 누락 시 갱신 명령 거부 (PLAN §2.18 #2, T-6)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        # 마커 제거
        md = self._md()
        (self.task_path / "STATE.md").write_text(
            md.replace("<!-- pipeline:start -->", "REMOVED").replace("<!-- pipeline:end -->", "REMOVED")
        )
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=1, done=True)
            code = self._err_code(ST.cmd_mark, args)
        self.assertEqual(code, "marker_missing")

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

    # ── E-5: import_failed ───────────────────────────────────────────────────
    def test_import_failed(self):
        """#5 import_failed: --import-existing 파싱 실패 (PLAN §2.18 #5, §2.5)"""
        # 파싱 불가한 STATE.md 작성 (표 행 없음)
        (self.task_path / "STATE.md").write_text("# STATE: 테스트\n빈 파일\n")
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                import_existing=True,
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "import_failed")

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
        # agentic 모드에서 TASK 사용자 확인 행은 auto-na로 초기화됨
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

    def test_scenario_marker_missing_init_then_remove(self):
        """마커 손실: init 후 마커 제거 → advance 거부 (PLAN §2.18 #2, T-6)"""
        self._init(rows_spec=SIMPLE_ROWS_SPEC)
        md = self._md()
        (self.task_path / "STATE.md").write_text(
            md.replace("<!-- pipeline:start -->", "").replace("<!-- pipeline:end -->", "")
        )
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=1)
            exit_code, result = self._call_cmd(ST.cmd_advance, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "marker_missing")

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

    def test_scenario_import_existing_success(self):
        """--import-existing 성공: 파싱 가능한 STATE.md (PLAN §2.5, T-13)"""
        # 마크다운 표가 있는 STATE.md 직접 작성
        md_content = """# STATE: 테스트

> 최종 갱신: 2026-05-01 22:00

## 현재 상태
- 모드: interactive
- 단계: TASK
- 진행: TASK 단계
- 상태: 진행 중

## 파이프라인 현황판

| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ |  |
| 2 | TASK | TASK.md 생성 | ⬜ |  |
| 3 | CLOSE | State Gate | ⬜ |  |

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음

## 다음 액션
PLAN 단계 진입
"""
        (self.task_path / "STATE.md").write_text(md_content)
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                import_existing=True,
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 0, f"import_existing failed: {result}")
        state = self._state()
        self.assertEqual(len(state["rows"]), 3)

    def test_scenario_import_existing_failure(self):
        """--import-existing 실패: 파싱 불가 STATE.md → import_failed (PLAN §2.18 #5)"""
        (self.task_path / "STATE.md").write_text("# 파싱 불가능한 내용\n")
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                skill="opp", mode="interactive",
                import_existing=True,
            )
            exit_code, result = self._call_cmd(ST.cmd_init, args)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result.get("error"), "import_failed")


# ═════════════════════════════════════════════════════════════════════════════
# D-2. TestImportPreservesKeys — 074 `--import-existing` task-step key 유실 결함
#      (TEST-SCENARIO.md S-a~S-e, RED-first — 작성자≠구현자, mock/patch 금지)
# ═════════════════════════════════════════════════════════════════════════════

class TestImportPreservesKeys(BaseTestCase):
    """`cmd_init` import 분기가 기존 state.json/pipeline.json의 rows[].key를
    (stage,item) 순서 매칭으로 재접합하는지 검증 — PLAN 074 §3.2 DEC-1~DEC-5.

    RED 근거: 현재 `cmd_init` import 분기(state_tool.py:900-908)는
    `parse_existing_state_md`가 만든 keyless rows를 그대로 사용하고, line 932
    schema_version 계산도 그 결과에 의존한다 — key 재접합 로직이 없으므로
    S-a/S-b/S-d/S-e는 GREEN(구현) 이전에는 FAIL한다(key 부재/None,
    schema_version "1.0" 강등). S-c는 keyless 자체는 이미 성립하나 stderr 경고
    단언이 없어 FAIL한다.

    검증 방식: mock/patch/MagicMock 금지 — 실 `cmd_init` 호출(직접 함수 호출,
    `BaseTestCase._call_cmd` 패턴) + 실 파일 I/O(state.json/STATE.md)만 사용한다
    (red-first.md §4).
    """

    # S-a/S-d/S-e 공용 — key 보유 상태 fixture 생성용 pipeline.json 스펙
    # (TestPipelineJsonInit._MINI_SPEC과 동형 구조, task_steps 4행)
    _KEY_SPEC = {
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

    # S-e 전용 — 동일 (stage,item)("EXECUTE","작업")이 2회 중복 등장하는 스펙
    _DUP_SPEC = {
        "spec_version": "1.0",
        "skill": "opp",
        "meta": {"mode_label": "Dup", "stages": ["TASK", "EXECUTE", "CLOSE"]},
        "task_steps": [
            {"id": 1, "key": "task.task_md",   "stage": "TASK",    "item": "작업"},
            {"id": 2, "key": "execute.step_a", "stage": "EXECUTE", "item": "작업"},
            {"id": 3, "key": "execute.step_b", "stage": "EXECUTE", "item": "작업"},
            {"id": 4, "key": "close.done_md",  "stage": "CLOSE",   "item": "DONE.md 생성"},
        ],
    }

    def _write_spec_file(self, name, spec_dict):
        p = self.tmpdir / name
        p.write_text(json.dumps(spec_dict, ensure_ascii=False), encoding="utf-8")
        return p

    def _write_state_md_table(self, stage_item_pairs):
        """key 컬럼이 없는 실제 렌더 형식 STATE.md를 직접 작성한다
        (`render_pipeline_table` state_tool.py:271 산출 형식과 동일한
        `| # | 단계 | 항목 | 상태 | 시점 |` 5컬럼 표 — key 원천이 STATE.md뿐인
        결함 재현 조건)."""
        header = (
            "# STATE: 테스트\n\n"
            "> 최종 갱신: 2026-05-01 22:00\n\n"
            "## 현재 상태\n- 모드: interactive\n- 단계: TASK\n"
            "- 진행: TASK 단계\n- 상태: 진행 중\n\n"
            "## 파이프라인 현황판\n\n"
            "| # | 단계 | 항목 | 상태 | 시점 |\n"
            "|---|------|------|------|------|\n"
        )
        body = "".join(
            f"| {i + 1} | {stage} | {item} | ⬜ |  |\n"
            for i, (stage, item) in enumerate(stage_item_pairs)
        )
        footer = (
            "\n## 의사결정 로그\n| # | 시점 | 결정 | 근거 |\n|---|------|------|------|\n\n"
            "## 블로커\n없음\n\n## 다음 액션\nPLAN 단계 진입\n"
        )
        (self.task_path / "STATE.md").write_text(header + body + footer, encoding="utf-8")

    def _run_init(self, **kwargs):
        """cmd_init 직접 호출 — stdout+stderr 동시 캡처.
        반환: (exit_code, result_dict, stderr_text)."""
        import io
        from contextlib import redirect_stdout, redirect_stderr
        kwargs.setdefault("skill", "opp")
        kwargs.setdefault("mode", "interactive")
        args = make_args(task_path=str(self.task_path), **kwargs)
        out, err_buf = io.StringIO(), io.StringIO()
        exit_code = 0
        with redirect_stdout(out), redirect_stderr(err_buf):
            with _mock_now():
                try:
                    ST.cmd_init(args)
                except SystemExit as e:
                    exit_code = e.code
        output = out.getvalue().strip()
        result = json.loads(output) if output else {}
        return exit_code, result, err_buf.getvalue()

    def _make_key_bearing_fixture(self, spec_dict, name="key_spec.json"):
        """spec_dict로 실제 init을 1회 실행해 key 보유 state.json + 렌더된
        STATE.md(key 컬럼 없음) fixture를 생성한다. 반환: 원본 state dict."""
        spec_path = self._write_spec_file(name, spec_dict)
        exit_code, result, _ = self._run_init(rows_from=str(spec_path))
        self.assertEqual(exit_code, 0, f"fixture 생성용 init 실패: {result}")
        return self._state()

    # ── S-a ──────────────────────────────────────────────────────────────
    def test_force_import_preserves_all_keys(self):
        """S-a (H-1): key 보유 state.json + STATE.md 존재 상태에서
        `init --force --import-existing` 후 rows[].key가 원본과 순서·값
        100% 일치해야 한다 (070 --task-step 주소 계약)."""
        original = self._make_key_bearing_fixture(self._KEY_SPEC)
        original_keys = [r.get("key") for r in original["rows"]]
        original_stage_item = [(r["stage"], r["item"]) for r in original["rows"]]
        self.assertTrue(all(original_keys), "fixture 자체에 key 없음 — 사전조건 오류")

        exit_code, result, _ = self._run_init(
            force=True, import_existing=True, note="recovery"
        )
        self.assertEqual(exit_code, 0, f"force+import_existing 실패: {result}")

        restored = self._state()
        restored_keys = [r.get("key") for r in restored["rows"]]
        restored_stage_item = [(r["stage"], r["item"]) for r in restored["rows"]]
        self.assertEqual(
            restored_keys, original_keys,
            f"key 유실 — 원본 {original_keys} vs 복구 후 {restored_keys}"
        )
        self.assertEqual(restored_stage_item, original_stage_item)

    # ── S-b ──────────────────────────────────────────────────────────────
    def test_import_with_pipeline_json_restores_keys(self):
        """S-b (H-2): state.json 없음 + STATE.md + pipeline.json 스펙 상태에서
        `--import-existing --rows-from mini.json` 후 rows[].key가 스펙 기준
        (stage,item) 매칭으로 복원되어야 한다."""
        pairs = [(ts["stage"], ts["item"]) for ts in self._KEY_SPEC["task_steps"]]
        self._write_state_md_table(pairs)
        spec_path = self._write_spec_file("mini.json", self._KEY_SPEC)
        self.assertFalse((self.task_path / "state.json").exists())

        exit_code, result, _ = self._run_init(
            import_existing=True, rows_from=str(spec_path)
        )
        self.assertEqual(exit_code, 0, f"pipeline.json 폴백 import 실패: {result}")

        state = self._state()
        expected_keys = [ts["key"] for ts in self._KEY_SPEC["task_steps"]]
        actual_keys = [r.get("key") for r in state["rows"]]
        self.assertEqual(actual_keys, expected_keys)

    # ── S-c ──────────────────────────────────────────────────────────────
    def test_import_no_key_source_keyless_with_warning(self):
        """S-c (H-3): key 원천(기존 state.json/pipeline.json)이 전무한 상태에서
        `--import-existing`만 호출 시 ①rows keyless 유지 ②stderr 경고 JSON
        1줄 ③stdout ok 페이로드·rows_count 불변(하위호환) ④schema_version
        "1.0" 유지를 만족해야 한다."""
        self._write_state_md_table([
            ("TASK", "작업"), ("TASK", "TASK.md 생성"), ("CLOSE", "State Gate"),
        ])
        self.assertFalse((self.task_path / "state.json").exists())

        exit_code, result, stderr_text = self._run_init(import_existing=True)

        self.assertEqual(exit_code, 0, f"key 원천 전무 import 실패: {result}")
        self.assertTrue(result.get("ok"), f"ok 페이로드 불변 위반: {result}")
        self.assertEqual(result.get("rows_count"), 3, "rows_count 불변(하위호환) 위반")

        state = self._state()
        self.assertEqual(len(state["rows"]), 3)
        for row in state["rows"]:
            self.assertFalse(row.get("key"), f"key 원천 전무인데 key 부여됨: {row}")
        self.assertEqual(state["schema_version"], "1.0")

        self.assertIn(
            "warning", stderr_text,
            f"key 원천 전무 시 stderr 경고 1줄이 있어야 함 — 실제 stderr: {stderr_text!r}"
        )

    # ── S-d ──────────────────────────────────────────────────────────────
    def test_preserved_keys_keep_schema_version_1_1(self):
        """S-d (H-4): key 보유 state.json + STATE.md 상태에서
        `init --force --import-existing` 후 결과 state.json의 schema_version이
        "1.1"로 유지되어야 한다 (재접합이 schema_version 계산 이전에 배치되어
        any(key) 조건이 True가 되는 정합, state_tool.py:932 무변경 전제)."""
        self._make_key_bearing_fixture(self._KEY_SPEC)

        exit_code, result, _ = self._run_init(
            force=True, import_existing=True, note="recovery"
        )
        self.assertEqual(exit_code, 0, f"force+import_existing 실패: {result}")

        restored = self._state()
        self.assertEqual(
            restored["schema_version"], "1.1",
            f"key 보존 import인데 schema_version 강등: {restored['schema_version']}"
        )

    # ── S-e ──────────────────────────────────────────────────────────────
    def test_duplicate_stage_item_ordered_consumption(self):
        """S-e (H-2, H-5): 동일 (stage,item)("EXECUTE","작업")이 복수 행으로
        존재하는 key 보유 state.json + STATE.md 상태에서
        `init --force --import-existing` 후 각 중복 행이 원본 순서대로
        대응 key를 부여받아 key 오배정 0건, 원본과 100% 일치해야 한다."""
        original = self._make_key_bearing_fixture(self._DUP_SPEC, name="dup_spec.json")
        original_keys = [r.get("key") for r in original["rows"]]
        # 사전조건: 실제로 중복 (stage,item) 쌍이 존재하는지 확인
        stage_items = [(r["stage"], r["item"]) for r in original["rows"]]
        self.assertEqual(
            stage_items.count(("EXECUTE", "작업")), 2,
            "fixture에 중복 (stage,item) 쌍이 없음 — 사전조건 오류"
        )

        exit_code, result, _ = self._run_init(
            force=True, import_existing=True, note="recovery duplicate order"
        )
        self.assertEqual(exit_code, 0, f"force+import_existing 실패: {result}")

        restored = self._state()
        restored_keys = [r.get("key") for r in restored["rows"]]
        self.assertEqual(
            restored_keys, original_keys,
            f"중복 (stage,item) 순서 소비 오배정 — 원본 {original_keys} vs 복구 후 {restored_keys}"
        )


# ═════════════════════════════════════════════════════════════════════════════
# E. 자유 텍스트 영역 보존 (PLAN §3 Step 2 마지막 항목)
# ═════════════════════════════════════════════════════════════════════════════

class TestFreeTextPreservation(BaseTestCase):
    """[MUST] 자유 텍스트 영역 보존: 블로커는 전 명령(mark/advance/block/add-row) 보존.
    '다음 액션'은 mark/advance 시 파생 갱신(첫 줄), block/add-row 시 보존.
    하위 자유 기재 라인(- 세부 액션 N)은 전 명령 보존.
    (PLAN 072 F-002/F-004)
    """

    def setUp(self):
        super().setUp()
        self._init(rows_spec=SIMPLE_ROWS_SPEC, next_action="초기 다음 액션")
        # 자유 텍스트 영역에 마커 내용 추가
        md = self._md()
        md = md.replace("없음", "블로커 상세: 테스트 블로커 내용이 여기 있음")
        md = md.replace("초기 다음 액션", "초기 다음 액션\n- 세부 액션 1\n- 세부 액션 2")
        (self.task_path / "STATE.md").write_text(md)

    def _free_text_sections(self, md):
        """자유 텍스트 영역 3개 섹션 추출."""
        blocker_start = md.find("## 블로커")
        next_start = md.find("## 다음 액션")
        if blocker_start == -1 or next_start == -1:
            return None, None
        blocker = md[blocker_start:next_start]
        next_action = md[next_start:]
        return blocker, next_action

    def _assert_free_text_preserved(self, before_md, after_md):
        """블로커 / 다음 액션 섹션이 변경되지 않았는지 확인."""
        b_before, n_before = self._free_text_sections(before_md)
        b_after, n_after = self._free_text_sections(after_md)
        self.assertEqual(b_before, b_after, "블로커 섹션이 변경됨!")
        self.assertEqual(n_before, n_after, "다음 액션 섹션이 변경됨!")

    def test_mark_derives_next_action_preserves_others(self):
        """mark 후: 블로커 섹션 보존 + '다음 액션' 첫 줄 파생 갱신 + 하위 자유기재 보존
        (PLAN 072 F-002/F-004 — 의도된 설계 반전, 회귀 아님)"""
        md_before = self._md()
        blocker_before, _ = self._free_text_sections(md_before)

        self._mark(1)  # SIMPLE_ROWS_SPEC row1 = TASK/작업 → done, 프론티어 = row2(PLAN/작업)

        md_after = self._md()
        blocker_after, _ = self._free_text_sections(md_after)
        self.assertEqual(blocker_before, blocker_after, "블로커 섹션이 변경됨!")

        next_start = md_after.find("## 다음 액션")
        lines = md_after[next_start:].splitlines()
        self.assertEqual(lines[1], "PLAN 작업 진입",
                         f"'다음 액션' 첫 줄이 파생값으로 갱신되지 않음: {lines[1]!r}")
        self.assertEqual(lines[2:], ["- 세부 액션 1", "- 세부 액션 2"],
                         "하위 자유 기재 라인이 보존되지 않음")

    def test_advance_derives_next_action_preserves_others(self):
        """advance 후: 블로커 섹션 보존 + '다음 액션' 첫 줄 파생 갱신 + 하위 자유기재 보존
        (PLAN 072 F-002/F-004 — 의도된 설계 반전, 회귀 아님)"""
        md_before = self._md()
        blocker_before, _ = self._free_text_sections(md_before)

        self._advance(1)  # SIMPLE_ROWS_SPEC row1 = TASK/작업 → in_progress, 프론티어 = row1 자신

        md_after = self._md()
        blocker_after, _ = self._free_text_sections(md_after)
        self.assertEqual(blocker_before, blocker_after, "블로커 섹션이 변경됨!")

        next_start = md_after.find("## 다음 액션")
        lines = md_after[next_start:].splitlines()
        self.assertEqual(lines[1], "TASK 작업 진행 중",
                         f"'다음 액션' 첫 줄이 파생값으로 갱신되지 않음: {lines[1]!r}")
        self.assertEqual(lines[2:], ["- 세부 액션 1", "- 세부 액션 2"],
                         "하위 자유 기재 라인이 보존되지 않음")

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
        """갱신 명령은 마커 영역만 변경, 자유 텍스트 영역은 불변 (PLAN §2.11 G-8, F-4)"""
        md_before = self._md()
        self._mark(1)
        md_after = self._md()
        # 마커 영역 밖 자유 텍스트는 동일해야 함
        # (의사결정 로그 자동 기재는 허용)
        blocker_before = md_before[md_before.find("## 블로커"):md_before.find("## 다음 액션")]
        blocker_after = md_after[md_after.find("## 블로커"):md_after.find("## 다음 액션")]
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

    def _next_action_lines(self, md):
        """STATE.md '## 다음 액션' 섹션에서 (첫 줄, 하위 잔여 라인 리스트) 반환."""
        idx = md.find("## 다음 액션")
        self.assertNotEqual(idx, -1, "STATE.md에 '## 다음 액션' 섹션이 없음")
        section_lines = md[idx:].splitlines()
        first_line = section_lines[1] if len(section_lines) > 1 else ""
        rest_lines = section_lines[2:]
        return first_line, rest_lines

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
        """[T072/L1-R2,R3] S-2 — 여러 행을 순차로 advance(→in_progress)/mark(→done)하며
        각 시점 state.json `next_action`과 STATE.md '## 다음 액션' 첫 줄이 프론티어
        (첫 미완료 행) 기반 값과 일치해야 한다: pending → "{stage} {item} 진입",
        in_progress → "{stage} {item} 진행 중". 현재 미구현이므로 매 단계 실패한다(RED)."""
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
                first_line, _ = self._next_action_lines(self._md())
                self.assertEqual(
                    first_line, expected,
                    f"{action}(row={row_id}) 후 STATE.md '## 다음 액션' 첫 줄 불일치: "
                    f"{first_line!r} (기대: {expected!r})"
                )

    # ── S-3 (R-2/M-2): 전체 완료 시 "태스크 완료" 경계 ──

    def test_r2_m2_all_rows_complete_next_action_task_complete(self):
        """[T072/L1-R2,M-2] S-3 — 마지막 행까지 모두 완료(current_status=done)되면
        프론티어(다음 대기 행)가 부재하므로 `next_action == "태스크 완료"`여야 한다.
        현재 미구현이므로 실패한다(RED)."""
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
        first_line, _ = self._next_action_lines(self._md())
        self.assertEqual(
            first_line, "태스크 완료",
            f"전체 완료 후 STATE.md 첫 줄 불일치: {first_line!r}"
        )

    # ── S-4 (R-2/M-1): 첫 줄만 치환 — 하위 자유 기재 보존 ──

    def test_m1_first_line_replaced_subordinate_free_text_preserved(self):
        """[T072/L1-M1] S-4 — '## 다음 액션' 헤더 + 첫 줄 + 하위 자유 기재
        ("- 세부 액션 1"/"- 세부 액션 2") 상태에서 mark/advance 시 첫 줄만 파생값으로
        치환되고 하위 2줄은 잔존해야 하며, 다른 섹션(블로커 등)은 오염되지 않아야 한다.
        현재 첫 줄이 갱신되지 않으므로 실패한다(RED)."""
        self._init(rows_spec=SIMPLE_ROWS_SPEC, next_action="초기 다음 액션")
        md = self._md()
        md = md.replace(
            "## 다음 액션\n초기 다음 액션",
            "## 다음 액션\n초기 다음 액션\n- 세부 액션 1\n- 세부 액션 2",
        )
        self.assertIn("- 세부 액션 2", md, "픽스처 조립 실패 — 하위 자유 기재 삽입 확인 필요")
        blocker_before = md[md.find("## 블로커"):md.find("## 다음 액션")]
        (self.task_path / "STATE.md").write_text(md, encoding="utf-8")

        code = self._advance(1)  # SIMPLE_ROWS_SPEC row1 = TASK/작업 → in_progress
        self.assertEqual(code, 0, "advance(1) 실패")

        new_md = self._md()
        first_line, rest_lines = self._next_action_lines(new_md)
        self.assertEqual(
            first_line, "TASK 작업 진행 중",
            f"'## 다음 액션' 첫 줄이 파생값으로 치환되지 않음: {first_line!r}"
        )
        self.assertEqual(
            rest_lines, ["- 세부 액션 1", "- 세부 액션 2"],
            f"하위 자유 기재가 보존되지 않음: {rest_lines!r}"
        )
        blocker_after = new_md[new_md.find("## 블로커"):new_md.find("## 다음 액션")]
        self.assertEqual(blocker_before, blocker_after, "블로커 섹션이 오염됨")

    # ── S-6 (R-4): advance/mark --next-action 오버라이드 우선 ──

    def test_r4_override_next_action_takes_priority_over_derivation(self):
        """[T072/L1-R4] S-6 — `advance --next-action "커스텀 안내"` 지정 시 자동 파생값보다
        오버라이드가 우선해야 한다. 공개 CLI 실호출(run.sh subprocess, red-first.md §4) —
        현재 advance 파서에 `--next-action`이 없어 argparse 단계에서 거부(usage error,
        exit 2)되므로 실패한다(RED)."""
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
        first_line, _ = self._next_action_lines(self._md())
        self.assertEqual(
            first_line, "커스텀 안내",
            f"STATE.md 오버라이드 반영 불일치: {first_line!r}"
        )

    # ── S-7 (R-4/M-3): 오버라이드 비지속 — 다음 전이 자동 파생 복귀 ──

    def test_m3_override_non_persistent_reverts_to_derived_on_next_transition(self):
        """[T072/L1-R4,M-3] S-7 — S-6과 동일한 오버라이드 전이 직후, `--next-action` 없는
        후속 mark 시 자동 파생값으로 복귀해야 한다(오버라이드 비지속 — stale 값 재도입 금지).
        현재 오버라이드 자체가 미구현이라 사전 단계(advance --next-action)에서부터
        실패한다(RED)."""
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
        first_line, _ = self._next_action_lines(self._md())
        self.assertEqual(
            first_line, "PLAN 작업 진입",
            f"STATE.md 첫 줄 복귀 실패: {first_line!r}"
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

    def test_rows_from_agentic_auto_na(self):
        """--rows-from agentic: 사용자 확인 행 auto-na (PLAN §2.20.2 단계 10)"""
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
        self.assertEqual(task_user["status"], "na")
        close_user = next(r for r in state["rows"] if r["stage"] == "CLOSE")
        self.assertEqual(close_user["status"], "pending")  # CLOSE는 na 불가

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
    """PLAN §2.18 E-1: ERROR_CODES 25종 기존 + PLAN 013 신규 2종 + PLAN 014 신규 1종 + PLAN 016 신규 2종 + PLAN 005 신규 1종 + 070 신규 8종 + 091 신규 5종 = 44종 모두 등재 확인.

    [PM 승인 예외 — 070 GREEN 후속 정정] 31→39 계약 갱신은 테스트 약화가 아니라
    카탈로그 정합 보존을 위한 승인된 갱신이다(AGENTIC-LOG #16 승인 근거).
    091(RED-first, F-004): 게이트 집행 배선 신규 5종(gate_artifact_missing +
    spec_gate_type_invalid/spec_gate_missing_field/spec_gate_field_type_invalid/
    spec_gate_checklist_empty) 반영 — Step 8 GREEN 이전에는 ST.ERROR_CODES에
    미등재이므로 FAIL이 정상(RED 증거).
    """

    EXPECTED_CODES = [
        # 기존 25종 (PLAN §2.18 + 이전 추가분)
        "worker_scope_violation",
        "marker_missing",
        "already_initialized",
        "date_tool_failed",
        "import_failed",
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
    ]

    def test_error_codes_count(self):
        """ERROR_CODES 상수가 44종 모두 포함 (PLAN §2.18 + PLAN 013 + PLAN 014 + PLAN 016 + PLAN 005 + 070 F-001/F-003/F-004 8종 + 091 F-004 5종)"""
        self.assertEqual(len(ST.ERROR_CODES), 44)

    def test_all_28_codes_registered(self):
        """44종 코드 각각이 ERROR_CODES에 등재됨(070 신규 8종 + 091 신규 5종 포함)"""
        for code in self.EXPECTED_CODES:
            self.assertIn(code, ST.ERROR_CODES, f"에러 코드 {code} 미등재")


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
        """
        import io
        from contextlib import redirect_stdout

        # 레포 루트 기준 상대 해석 — 절대경로 하드코딩은 레포 개명(opal→ai-framework)으로
        # 이미 한 차례 끊겼다. 034는 tasks/backup/으로 이관됐으므로 두 위치를 모두 탐색한다.
        repo_root = _TOOL_DIR.parents[2]
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
        """새 10행 구조 전체 순차 완주: 모든 행 순서대로 mark → current_status=done.
        guard가 정상 통과하고 CLOSE "DONE.md 생성" 행에서 완료 전환 (014 Phase 4)"""
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
        md = self._md()
        self.assertIn("- 상태: 완료", md)

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

        # opp 스펙: row 2(task.user_confirm)/5(plan.user_confirm)/8(execute.user_confirm)는
        # "사용자 확인"(non-CLOSE) — agentic 자동 na로 이미 완료. 나머지(1,3,4,6,7)만 mark.
        for rid in (1, 3, 4, 6, 7):
            code, stdout, stderr, data = _run070(
                ["mark", str(agentic_task), "--row", str(rid), "--done"]
            )
            self.assertEqual(code, 0, f"사전 행 {rid} mark 실패: {stdout!r}")

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
                         "timestamp", "owner", "todo_mirror"}
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
# 진입점
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
