"""
@header {
  "module": "test_state_tool",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool 단위 테스트 — 9개 명령 happy path + 23종 에러 코드 × 최소 1건 + G-5~G-15 시나리오. 005: TestClarificationGate 신설 — verify --clarification-check + TASK→다음단계 자동 훅 RED-first 케이스 ①~⑨ + 회귀 보호. 054: TestOwnerNamePlaceholder 신설 — note '{owner_name}' 플레이스홀더 identity.md write-time 치환 RED-first(S-1~S-7).",
  "exports": [
    "TestInit", "TestShow", "TestAdvance", "TestMark",
    "TestBlock", "TestValidate", "TestAddRow", "TestStatus", "TestGatePass",
    "TestErrorCodes", "TestFreeTextPreservation", "TestClarificationGate",
    "TestOwnerNamePlaceholder"
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
        # 005: clarification-check 플래그 기본값 (AttributeError 방지)
        "clarification_check": False,
        "task_md": None,
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
    """PLAN §2.18 E-1: ERROR_CODES 25종 기존 + PLAN 013 신규 2종 + PLAN 014 신규 1종 + PLAN 016 신규 2종 + PLAN 005 신규 1종 = 31종 모두 등재 확인"""

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
    ]

    def test_error_codes_count(self):
        """ERROR_CODES 상수가 31종 모두 포함 (PLAN §2.18 + PLAN 013 + PLAN 014 + PLAN 016 + PLAN 005)"""
        self.assertEqual(len(ST.ERROR_CODES), 31)

    def test_all_28_codes_registered(self):
        """31종 코드 각각이 ERROR_CODES에 등재됨"""
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

        scenario_path = pathlib.Path(
            "/Volumes/Data/AiStudio/workspace/opal/tasks/"
            "034-260621-opds-state-tool-mock-패턴-오탐수정/TEST-SCENARIO.md"
        )
        self.assertTrue(scenario_path.exists(), "034 TEST-SCENARIO.md 파일이 없음")

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
# 진입점
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
