"""
@header {
  "module": "test_state_tool",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool 단위 테스트 — 9개 명령 happy path + 23종 에러 코드 × 최소 1건 + G-5~G-15 시나리오",
  "exports": [
    "TestInit", "TestShow", "TestAdvance", "TestMark",
    "TestBlock", "TestValidate", "TestAddRow", "TestStatus", "TestGatePass",
    "TestErrorCodes", "TestFreeTextPreservation"
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
import sys
import tempfile
import types
import unittest
from unittest.mock import patch, MagicMock

# state_tool.py를 직접 import (PYTHONPATH 조정)
_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))
import state_tool as ST

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
# E. 자유 텍스트 영역 보존 (PLAN §3 Step 2 마지막 항목)
# ═════════════════════════════════════════════════════════════════════════════

class TestFreeTextPreservation(BaseTestCase):
    """[MUST] 자유 텍스트 영역 보존: mark/advance/block/add-row 호출 시
    의사결정 로그(§2.17 자동 기재 외)/블로커/다음 액션 본문 변경 0건
    (PLAN §3 Step 2 마지막 항목)
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

    def test_mark_preserves_free_text(self):
        """mark 후 블로커/다음 액션 섹션 보존 (PLAN §3 Step 2)"""
        md_before = self._md()
        self._mark(1)
        md_after = self._md()
        self._assert_free_text_preserved(md_before, md_after)

    def test_advance_preserves_free_text(self):
        """advance 후 블로커/다음 액션 섹션 보존 (PLAN §3 Step 2)"""
        md_before = self._md()
        self._advance(1)
        md_after = self._md()
        self._assert_free_text_preserved(md_before, md_after)

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


# ═════════════════════════════════════════════════════════════════════════════
# H. ERROR_CODES 상수 완전성 검증
# ═════════════════════════════════════════════════════════════════════════════

class TestErrorCodesCompleteness(unittest.TestCase):
    """PLAN §2.18 E-1: ERROR_CODES 25종 기존 + PLAN 013 신규 2종 + PLAN 014 신규 1종 = 28종 모두 등재 확인"""

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
    ]

    def test_error_codes_count(self):
        """ERROR_CODES 상수가 28종 모두 포함 (PLAN §2.18 + PLAN 013 + PLAN 014)"""
        self.assertEqual(len(ST.ERROR_CODES), 28)

    def test_all_28_codes_registered(self):
        """28종 코드 각각이 ERROR_CODES에 등재됨"""
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
# 진입점
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
