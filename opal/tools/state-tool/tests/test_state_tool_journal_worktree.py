"""
@header {
  "module": "test_state_tool_journal_worktree",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool todo·memory 귀속·worktree·journal 계약 테스트",
  "exports": ["TestTodoMirror", "TestFinalizeAttributionHistoryLink", "TestS9CloseMarkNoImmediateMemoryAppend", "TestS10FinalizeAttribution", "TestTaskStepGate", "TestWorktreeFlag", "TestJournalResilience", "TestLegacyCoexistence", "TestShowAsQueryStandard"]
}
"""

from state_tool_test_support import *  # noqa: F401,F403

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


class TestFinalizeAttributionHistoryLink(BaseTestCase):
    """088 R-1~R-5의 히스토리 귀속 계약 — 118 D-4b(AC-4)로 **발동 지점만 이전**됐다.

    088 시점에는 CLOSE 마지막 행 mark가 즉시 memory-tool을 호출했으나, 118은 그
    즉시 호출을 제거하고(`TestS9CloseMarkNoImmediateMemoryAppend`가 이를 고정)
    `state-tool finalize-attribution <task-path> --allocator-root <abs>`를 유일한
    귀속 경로로 삼는다. 아래 TS-1~TS-7은 088이 지키던 관찰 가능한 계약
    (생성/멱등/부재/손상/선택성/리마인더/영속경계)을 **새 발동 지점 기준으로 그대로
    보존**한 것이다 — 계약을 약화하지 않고 트리거만 옮겼다.

    픽스처는 BaseTestCase의 평면 tmpdir 대신 **허브(allocator_root) 형태**를 구성한다:
        <tmpdir>/.opal/MEMORY.json    ← allocator_root 앵커
        <tmpdir>/tasks/<태스크폴더>/  ← task_path
    allocator_root는 명시 인자로만 전달하며 도구가 추론하지 않는다(worktree.md
    §task root와 allocator root 계약).
    """

    CLOSE_ROWS_SPEC = json.dumps([
        {"stage": "TASK",  "item": "사용자 확인"},
        {"stage": "CLOSE", "item": "DONE.md 생성"},
    ])

    def setUp(self):
        super().setUp()
        # BaseTestCase가 만든 평면 task_path는 사용하지 않는다 — 허브 루트 구조로 교체
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

    def _finalize(self, allocator_root=None):
        """finalize-attribution 공개 CLI 호출 → (code, stdout, stderr, parsed)."""
        argv = ["finalize-attribution", str(self.task_path)]
        if allocator_root is not None:
            argv += ["--allocator-root", str(allocator_root)]
        return _run094(argv)

    # ── TS-1 (R-1/R-2) ──────────────────────────────────────────────────────

    def test_ts1_finalize_attribution_creates_history_row(self):
        """TS-1 (R-1/R-2, 118 D-4b): finalize-attribution → MEMORY.json history[0]에
        1건 생성. title/path/stage/result는 도구 파생값, date는 memory-tool이 채운
        KST 당일. 088과 동일한 행 계약이며 발동 지점만 mark → finalize로 옮겼다."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        code, stdout, stderr, data = self._finalize(self.project_root)

        self.assertEqual(code, 0,
                         f"finalize-attribution 실패: stdout={stdout!r} stderr={stderr!r}")
        self.assertTrue(data.get("ok"), f"응답이 ok:true여야 함: {data}")

        history = self._history()
        self.assertEqual(len(history), 1,
                         f"history에 정확히 1건이 생성되어야 함, 실제: {history}")
        row = history[0]
        self.assertEqual(row.get("title"), _HL_EXPECTED_TITLE,
                         f"title은 task_id에서 파생되어야 함(§2.6), 실제: {row.get('title')!r}")
        self.assertEqual(row.get("path"), _HL_EXPECTED_PATH,
                         f"path는 allocator_root 상대경로여야 함, 실제: {row.get('path')!r}")
        self.assertEqual(row.get("stage"), _HL_STAGE_DONE,
                         f"stage는 '완료'여야 함(D-6), 실제: {row.get('stage')!r}")
        self.assertRegex(str(row.get("date")), r"^\d{4}-\d{2}-\d{2}$",
                         f"date는 KST YYYY-MM-DD여야 함, 실제: {row.get('date')!r}")
        self.assertEqual(row.get("result"), _HL_RESULT_PLACEHOLDER,
                         f"result는 플레이스홀더여야 함(§2.6), 실제: {row.get('result')!r}")

        link = data.get("attribution")
        self.assertIsInstance(link, dict,
                              f"응답에 attribution 객체가 있어야 함: {data}")
        self.assertEqual(link.get("status"), "created",
                         f"최초 생성은 status=created여야 함, 실제: {link.get('status')!r}")

    # ── TS-2 (R-3 멱등) ─────────────────────────────────────────────────────

    def test_ts2_duplicate_finalize_is_idempotent(self):
        """TS-2 (R-3): 동일 인자로 finalize-attribution을 2회 실행해도 해당 path 행은
        정확히 1건. 2회차 응답은 attribution.status=duplicate_skipped."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        code1, stdout1, stderr1, _ = self._finalize(self.project_root)
        self.assertEqual(code1, 0, f"1회차 실패: stdout={stdout1!r} stderr={stderr1!r}")

        code2, stdout2, stderr2, data2 = self._finalize(self.project_root)
        self.assertEqual(code2, 0, f"2회차 실패: stdout={stdout2!r} stderr={stderr2!r}")
        self.assertTrue(data2.get("ok"), f"2회차도 ok:true여야 함: {data2}")

        history = self._history()
        same_path = [r for r in history if r.get("path") == _HL_EXPECTED_PATH]
        self.assertEqual(len(same_path), 1,
                         f"동일 path 행이 정확히 1건이어야 함(멱등), 실제 history: {history}")

        link = data2.get("attribution")
        self.assertIsInstance(link, dict, f"2회차 응답에도 attribution이 있어야 함: {data2}")
        self.assertEqual(link.get("status"), "duplicate_skipped",
                         f"2회차는 duplicate_skipped여야 함, 실제: {link.get('status')!r}")

    # ── TS-3 (R-4a 부재 → 명시적 거부) ──────────────────────────────────────

    def test_ts3_missing_memory_json_is_explicit_error(self):
        """TS-3 (R-4a 이전분, 118 D-4b): allocator_root에 .opal/MEMORY.json이 없으면
        추론으로 다른 루트를 찾지 않고 명시적으로 거부한다.

        088에서는 mark 부수효과였으므로 비차단 skip이 옳았으나, 118에서 귀속은 전용
        커맨드의 **본 목적**이므로 조용한 skip이 아니라 exit 1 + ok:false로 표면화한다
        (mark의 ok:true 비차단 계약은 S-9가 별도로 고정한다)."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        self.memory_file.unlink()   # 블랙박스 결함 주입 — 앵커 제거

        code, stdout, stderr, data = self._finalize(self.project_root)
        self.assertEqual(code, 1,
                         f"MEMORY.json 부재는 exit 1이어야 함 — stdout={stdout!r} stderr={stderr!r}")
        self.assertIs(data.get("ok"), False, f"ok:false여야 함: {data}")
        self.assertEqual(data.get("error"), "allocator_root_invalid",
                         f"에러 코드가 allocator_root_invalid여야 함: {data}")
        self.assertFalse(self.memory_file.exists(), "MEMORY.json이 새로 생성되면 안 됨")

    # ── TS-4 (R-4b 손상 → 명시적 실패, 파일 무변경) ─────────────────────────

    def test_ts4_corrupt_memory_json_fails_without_mutating_file(self):
        """TS-4 (R-4b 이전분): MEMORY.json이 손상 JSON이면 exit 1 + ok:false로 실패하고
        파일은 바이트 그대로 남는다. 결함 주입은 파일 덮어쓰기(블랙박스)."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        corrupt = "{ this is not valid json "
        self.memory_file.write_text(corrupt, encoding="utf-8")

        code, stdout, stderr, data = self._finalize(self.project_root)
        self.assertEqual(code, 1,
                         f"손상 MEMORY.json은 exit 1이어야 함 — stdout={stdout!r} stderr={stderr!r}")
        self.assertIs(data.get("ok"), False, f"ok:false여야 함: {data}")
        self.assertEqual(data.get("error"), "finalize_attribution_failed",
                         f"에러 코드가 finalize_attribution_failed여야 함: {data}")
        self.assertTrue(str(data.get("message", "")).strip(),
                        f"message가 비공백이어야 함, 실제: {data.get('message')!r}")
        self.assertEqual(self.memory_file.read_text(encoding="utf-8"), corrupt,
                         "실패한 귀속이 MEMORY.json을 변경하면 안 됨")

    # ── TS-5 (회귀: mark는 어떤 행에서도 귀속하지 않는다) ───────────────────

    def test_ts5_no_mark_path_links_but_finalize_does(self):
        """TS-5 (회귀/선택성, 118 D-4b 갱신): 088에서는 '비CLOSE 행만 무발동'이었으나
        118에서는 **비CLOSE 행도 CLOSE 마지막 행도** MEMORY를 건드리지 않는다.

        무발동만 단언하면 기능이 아예 없어도 통과하는 공허한 가드가 되므로, 동일
        픽스처 안에서 finalize-attribution이 실제로 발동함을 대조군으로 확증한다."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        before = self._history()

        # (1) 비CLOSE 행 → 무발동
        code, result = self._mark_capture(1, owner="user")   # TASK/사용자 확인 (비CLOSE)
        self.assertEqual(code, 0, f"비CLOSE 행 mark 실패: {result}")
        self.assertNotIn("history_link", result,
                         f"mark 응답에는 history_link 키가 없어야 함(118 D-4b): {result}")
        self.assertEqual(len(self._history()), len(before),
                         "비CLOSE mark는 history를 변경하면 안 됨")

        # (2) CLOSE 마지막 행 → 118에서도 무발동
        code, close_result = self._mark_capture(2)
        self.assertEqual(code, 0, f"CLOSE 마지막 행 mark 실패: {close_result}")
        self.assertNotIn("history_link", close_result,
                         f"CLOSE mark 응답에도 history_link가 없어야 함(118 D-4b): {close_result}")
        self.assertEqual(len(self._history()), len(before),
                         "CLOSE 마지막 행 mark도 history를 변경하면 안 됨(118 AC-4)")

        # (3) 대조군 — finalize-attribution은 발동한다(무발동이 선택적임을 확증)
        fcode, fstdout, fstderr, _ = self._finalize(self.project_root)
        self.assertEqual(fcode, 0,
                         f"finalize-attribution 실패: stdout={fstdout!r} stderr={fstderr!r}")
        self.assertEqual(len(self._history()), len(before) + 1,
                         "finalize-attribution은 history를 1건 늘려야 함(대조군)")

    # ── TS-6 (R-5 리마인더) ─────────────────────────────────────────────────

    def test_ts6_reminder_contains_actionable_update_command(self):
        """TS-6 (R-5): attribution.reminder에 보강 명령의 구성요소가 모두 포함된다 —
        `update`, `--kind history`, `--result`, 그리고 실제 사용된 title."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        code, stdout, stderr, data = self._finalize(self.project_root)
        self.assertEqual(code, 0,
                         f"finalize-attribution 실패: stdout={stdout!r} stderr={stderr!r}")

        link = data.get("attribution")
        self.assertIsInstance(link, dict, f"attribution이 있어야 함: {data}")
        reminder = link.get("reminder")
        self.assertIsInstance(reminder, str,
                              f"reminder는 문자열이어야 함, 실제: {reminder!r}")
        for token in ("update", "--kind history", "--result", _HL_EXPECTED_TITLE):
            self.assertIn(token, reminder,
                          f"reminder에 {token!r}가 포함되어야 함(R-5), 실제: {reminder!r}")

    # ── TS-7 (H-3 영속 경계) ────────────────────────────────────────────────

    def test_ts7_attribution_not_persisted_schema_passes(self):
        """TS-7 (H-3 영속 경계, 076 TS-007 패턴): finalize-attribution 후 state.json
        어디에도 attribution/history_link 키가 없고 state.schema.json 검증을 통과한다."""
        self._init(rows_spec=self.CLOSE_ROWS_SPEC)
        code, stdout, stderr, data = self._finalize(self.project_root)
        self.assertEqual(code, 0,
                         f"finalize-attribution 실패: stdout={stdout!r} stderr={stderr!r}")
        # 선행 조건 — 발동 자체는 일어나야 한다(무발동으로 인한 위양성 통과 차단)
        self.assertIn("attribution", data, f"응답에 attribution이 있어야 함: {data}")

        state = self._state()
        for key in ("attribution", "history_link"):
            self.assertNotIn(key, state, f"{key}는 state.json에 영속되면 안 됨")
            for row in state["rows"]:
                self.assertNotIn(key, row, f"{key}는 rows[]에도 영속되면 안 됨")

        validated = self._validate()
        self.assertTrue(validated["ok"], f"state.schema.json 검증 실패: {validated}")
        self.assertEqual(validated["violations_count"], 0)


class TestS9CloseMarkNoImmediateMemoryAppend(BaseTestCase):
    """[T118 RED] S-9 (AC-4, H-1, C-4) — CLOSE 마지막 행 mark는 더 이상
    `.opal/MEMORY.json`을 즉시 변경하지 않아야 한다(D-4b: cmd_mark의 CLOSE
    마지막 행 분기에서 link_memory_history() 즉시호출을 제거). mark 응답은
    현행대로 ok:true를 유지하고, state.json의 current_status는
    "completed_unmerged"로 확정되어야 한다(history append는 신규
    `finalize-attribution` 서브커맨드가 전담 — TestS10FinalizeAttribution).

    RED 근거: 현재 cmd_mark(state_tool.py:1953-1958)는 CLOSE 마지막 행 완료 시
    link_memory_history()를 즉시 호출해 MEMORY.json history에 1건을 append한다
    (바로 위 TestCloseHistoryLink.test_ts1_close_last_mark_creates_history_row가
    이 현행 동작을 이미 양성으로 고정하고 있다). 또한 CLOSE 마지막 행 분기는
    `state["current_status"] = "done"`만 확정할 뿐(§2.11 G-6 계열),
    "completed_unmerged"라는 값 자체가 현재 코드 어디에도 존재하지 않는다.
    따라서 아래 해시 불변·history 불변·current_status 세 단정이 전부 실패한다."""

    def setUp(self):
        super().setUp()
        self.project_root = self.tmpdir
        self.memory_file = self.project_root / ".opal" / "MEMORY.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory_file.write_text(
            json.dumps(_HL_EMPTY_MEMORY_DOC, ensure_ascii=False, indent=2),
            encoding="utf-8")
        self.task_path = self.project_root / "tasks" / _S9_TASK_DIR
        self.task_path.mkdir(parents=True)
        self._init(rows_spec=_S9_CLOSE_ROWS_SPEC)

    def _sha256(self):
        return hashlib.sha256(self.memory_file.read_bytes()).hexdigest()

    def _mark_close_last(self):
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=1, done=True, owner="user")
            code0, result0 = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(code0, 0, f"픽스처 오류 — 사용자 확인 행 mark 실패: {result0}")
        with _mock_now():
            args = make_args(task_path=str(self.task_path), row=2, done=True)
            return self._call_cmd(ST.cmd_mark, args)

    def test_s9_close_mark_leaves_memory_json_byte_identical(self):
        """S-9 — mark 실행 전후 .opal/MEMORY.json sha256이 바이트 동일해야 하고,
        history 배열도 변하면 안 된다."""
        before_hash = self._sha256()
        before_doc = json.loads(self.memory_file.read_text(encoding="utf-8"))

        code, result = self._mark_close_last()

        self.assertEqual(code, 0, f"CLOSE 마지막 행 mark 실패: {result}")
        self.assertTrue(result.get("ok"),
                        f"mark 응답은 현행대로 ok:true여야 함(D-4b): {result}")

        after_hash = self._sha256()
        self.assertEqual(
            before_hash, after_hash,
            "CLOSE mark 전후 .opal/MEMORY.json sha256이 달라짐 — "
            "즉시 history append 제거(D-4b) 위반")

        after_doc = json.loads(self.memory_file.read_text(encoding="utf-8"))
        self.assertEqual(after_doc.get("history", []), before_doc.get("history", []),
                         "CLOSE mark가 MEMORY.json history를 append하면 안 됨(D-4b)")

    def test_s9_close_mark_confirms_completed_unmerged_status(self):
        """S-9 — mark 응답은 ok:true 유지, state.json current_status는
        "completed_unmerged"로 확정된다(D-4b, `link_memory_history` 호출 제거
        + `completed_unmerged` 확정)."""
        code, result = self._mark_close_last()

        self.assertEqual(code, 0, f"CLOSE 마지막 행 mark 실패: {result}")
        self.assertTrue(result.get("ok"), f"mark 응답은 ok:true여야 함: {result}")

        state = self._state()
        self.assertEqual(
            state.get("current_status"), "completed_unmerged",
            f"CLOSE mark 후 current_status는 completed_unmerged로 확정되어야 함"
            f"(D-4b) — 실제: {state.get('current_status')!r}")


class TestS10FinalizeAttribution(BaseTestCase):
    """[T118 RED] S-10 (AC-4, H-1) — 신규 서브커맨드
    `state-tool finalize-attribution <task-path> --allocator-root <abs>`.
    CLOSE mark에서 분리된 MEMORY history append를 이 커맨드가 전담한다(D-4b).

    (a) 정상 1회 실행 → 허브 MEMORY history에 정확히 1건 append.
    (b) 동일 인자로 재실행 → 중복 append 없음(멱등).
    (c) `--allocator-root` 미지정 또는 상대경로 → 추론 없이 거부.

    RED 근거: `finalize-attribution` 서브커맨드 자체가 state_tool.py의 argparse
    서브파서에 아직 등록되어 있지 않다. `run.sh finalize-attribution ...`은
    현재 argparse "invalid choice" usage 에러(exit 2, stdout에 JSON 미출력)로
    끝나므로, 아래 (a)/(b)는 exit 0·ok:true·history 1건 단정에서 실패하고,
    (c)는 이 도구의 기존 에러 응답 관례(`err()` 기본 exit_code=1 + 단일 라인
    JSON `ok:false`+`error` 키, state_tool.py:242-253)와 다른 exit 2/빈 stdout이
    나오므로 실패한다."""

    def setUp(self):
        super().setUp()
        self.project_root = self.tmpdir
        self.memory_file = self.project_root / ".opal" / "MEMORY.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self._write_memory(_HL_EMPTY_MEMORY_DOC)
        self.task_path = self.project_root / "tasks" / _S10_TASK_DIR
        self.task_path.mkdir(parents=True)
        self._init(rows_spec=SIMPLE_ROWS_SPEC)

    def _write_memory(self, doc):
        self.memory_file.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    def _history(self):
        return json.loads(self.memory_file.read_text(encoding="utf-8"))["history"]

    def test_s10a_first_run_appends_history_exactly_once(self):
        """S-10 (a) — 정상 1회 실행 → history에 정확히 1건, title/path는 기존
        derive_history_title 파생 규칙(§2.6)과 동일해야 한다."""
        code, stdout, stderr, data = _run094([
            "finalize-attribution", str(self.task_path),
            "--allocator-root", str(self.project_root),
        ])
        self.assertEqual(
            code, 0,
            f"finalize-attribution 정상 실행이 실패함: stdout={stdout!r} stderr={stderr!r}")
        self.assertTrue(data.get("ok"), f"응답은 ok:true여야 함: {data}")

        history = self._history()
        self.assertEqual(len(history), 1,
                         f"history에 정확히 1건이 append되어야 함, 실제: {history}")
        row = history[0]
        self.assertEqual(row.get("title"), _S10_EXPECTED_TITLE,
                         f"title은 기존 파생 규칙(§2.6)과 동일해야 함, 실제: {row.get('title')!r}")
        self.assertEqual(row.get("path"), _S10_EXPECTED_PATH,
                         f"path는 project_root 상대경로여야 함, 실제: {row.get('path')!r}")

    def test_s10b_rerun_with_same_args_is_idempotent(self):
        """S-10 (b) — 동일 인자로 재실행해도 중복 append가 없어야 한다(멱등)."""
        argv = [
            "finalize-attribution", str(self.task_path),
            "--allocator-root", str(self.project_root),
        ]
        code1, stdout1, stderr1, data1 = _run094(argv)
        self.assertEqual(
            code1, 0,
            f"1회차 finalize-attribution 실패: stdout={stdout1!r} stderr={stderr1!r}")

        code2, stdout2, stderr2, data2 = _run094(argv)
        self.assertEqual(
            code2, 0,
            f"2회차(재실행) finalize-attribution도 실패하면 안 됨(멱등): "
            f"stdout={stdout2!r} stderr={stderr2!r}")
        self.assertTrue(data2.get("ok"), f"2회차 응답도 ok:true여야 함: {data2}")

        history = self._history()
        same_path = [r for r in history if r.get("path") == _S10_EXPECTED_PATH]
        self.assertEqual(len(same_path), 1,
                         f"재실행 후에도 동일 path 행이 정확히 1건이어야 함(멱등), "
                         f"실제 history: {history}")

    def test_s10c_missing_or_relative_allocator_root_rejected_without_inference(self):
        """S-10 (c) — `--allocator-root` 미지정 또는 상대경로는 추론 없이
        거부되어야 한다. 이 도구의 기존 에러 응답 관례(err(), state_tool.py:242)를
        따라 exit 1 + 단일 라인 JSON `ok:false`+`error` 키를 기대한다."""
        # (c-1) --allocator-root 미지정
        code1, stdout1, stderr1, data1 = _run094([
            "finalize-attribution", str(self.task_path),
        ])
        self.assertEqual(
            code1, 1,
            f"--allocator-root 미지정은 exit 1(명시적 에러)이어야 함 — "
            f"실제: code={code1}, stdout={stdout1!r}, stderr={stderr1!r}")
        self.assertIs(data1.get("ok"), False,
                      f"미지정 시 ok:false 단일 라인 JSON이어야 함: {data1}")
        self.assertIn("error", data1, f"에러 코드 키가 있어야 함: {data1}")

        # (c-2) --allocator-root 상대경로
        code2, stdout2, stderr2, data2 = _run094([
            "finalize-attribution", str(self.task_path),
            "--allocator-root", "relative/path/only",
        ])
        self.assertEqual(
            code2, 1,
            f"상대경로 --allocator-root는 exit 1(명시적 에러)이어야 함 — "
            f"실제: code={code2}, stdout={stdout2!r}, stderr={stderr2!r}")
        self.assertIs(data2.get("ok"), False,
                      f"상대경로 시 ok:false 단일 라인 JSON이어야 함: {data2}")
        self.assertIn("error", data2, f"에러 코드 키가 있어야 함: {data2}")

        # 두 거부 케이스 모두 MEMORY.json history를 건드리면 안 됨(추론 금지 +
        # 부수효과 없음의 교차 확인)
        self.assertEqual(self._history(), [],
                         "거부된 호출이 MEMORY.json history를 변경하면 안 됨")


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
