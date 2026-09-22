"""
@header {
  "module": "test_state_tool_verification_gates",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool 검증·게이트·RED-first·증거 계약 테스트",
  "exports": ["TestVerify", "TestAddRowSchemaValidate", "TestStageTransitionGuard", "TestNewStandardRowStructure", "TestGatePassDeprecation", "TestStandardItemsConstants", "TestRedFirst", "TestMultiStepDoneGuard", "TestClarificationGate", "TestT098EvidenceCheck"]
}
"""

from state_tool_test_support import *  # noqa: F401,F403

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
        `task_root()`(state_tool.py:553 — `.opal/MEMORY.json` 보유
        조상 탐색, 088 §2.3에서 이미 검증된 패턴)를 재사용한다 — 이 함수는
        worktree/허브(전체 체크아웃) 양쪽에서 정확히 허브 루트를 반환한다."""
        import io
        from contextlib import redirect_stdout

        # 092 경로 계약(tasks/는 허브 고정) — task_root()로 허브 루트를
        # 찾는다. worktree에서 실행돼도 `.opal/MEMORY.json` 보유 조상(허브)까지
        # 거슬러 올라가므로 정확하다(088 §2.3 선례 재사용, 신규 헬퍼 미신설).
        repo_root = ST.task_root(str(_TOOL_DIR))
        self.assertIsNotNone(
            repo_root,
            f"task_root({_TOOL_DIR})가 None을 반환함 — .opal/MEMORY.json "
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


class TestNewStandardRowStructure(BaseTestCase):
    """014 Phase 4: 새 표준 행 구조(QA Gate/State Gate 행 없음)에서 도구가 정상 동작하는지 검증.
    - guard가 새 구조에서 단계 건너뛰기를 정상 차단 (기능 약화 금지)
    - CLOSE 마지막 행이 "DONE.md 생성"이어도 완료 전환 정상 동작
      (118 D-4b: current_status=completed_unmerged)
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
        current_status=completed_unmerged. guard가 정상 통과하고 CLOSE "DONE.md 생성" 행에서
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
        self.assertEqual(state["current_status"], "completed_unmerged")

    def test_new_structure_close_done_row_triggers_done_status(self):
        """새 구조: CLOSE 마지막 행 항목이 'DONE.md 생성'이어도 완료 전환
        (118 D-4b: current_status=completed_unmerged).
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
        self.assertEqual(state["current_status"], "completed_unmerged")

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
        repo_root = ST.task_root(str(_TOOL_DIR))
        self.assertIsNotNone(
            repo_root,
            "task_root가 None을 반환함 — .opal/MEMORY.json 보유 조상을 찾지 못함"
        )
        task_dir = _find_repo_task_dir(repo_root, "098-")
        task_md_path = task_dir / "TASK.md"
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
        repo_root = ST.task_root(str(_TOOL_DIR))
        self.assertIsNotNone(repo_root, "task_root가 None을 반환함")
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
