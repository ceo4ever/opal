"""
@header {
  "module": "test_state_tool_mode_contracts",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool 모드 경계·자동 승인·CLOSE 전이 계약 테스트",
  "exports": ["TestT093AutoNaRemoval", "TestT093AutoApproveHook", "TestT093AutoApproveBoundary", "TestT093HookGuardOrder", "TestT093MarkIdempotency", "TestT093NaBackwardCompat", "TestT093SingleDecisionSource", "TestR11ModeBoundary", "TestR11CloseGateFallback", "TestR11DerivedSignals", "TestR11Invariants"]
}
"""

from state_tool_test_support import *  # noqa: F401,F403

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
        (d / "test-scenario.json").write_text(
            json.dumps({"version": 1, "scenarios": []}, ensure_ascii=False),
            encoding="utf-8",
        )
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


class TestT093AutoApproveBoundary(_T093Base):
    """F-002 CLOSE·워커 구조적 제외 + F-003 경계 불변 + F-004 전용 에러."""

    def test_close_entry_auto_approves_in_agentic_mode_T093_L2_GOAL(self):
        """[T093/L2-GOAL] S-6 — agentic CLOSE entry atomically approves its prior confirmation."""
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
        self.assertEqual(code, 0, f"S-6 CLOSE 첫 행 mark가 통과하지 않음 (stdout={stdout!r})")
        r2 = self._row(d, 2)
        self.assertEqual(r2["status"], "done", r2)
        self.assertEqual(r2.get("owner"), "auto", r2)
        self.assertEqual(self._row(d, 3)["status"], "done")

    def test_close_first_row_auto_pass_allowed_T093_L1_F3(self):
        """[T093/L1-F3] S-7 — autonomous modes accept CLOSE auto-pass."""
        for mode in ("agentic", "semi-agentic"):
            with self.subTest(mode=mode):
                d = self._init_b(mode, name=f"s7-{mode}")
                self._assert_ok(self._mark(d, 1), "prep row1")
                self._assert_ok(self._mark(d, 2, "--owner", "user"), "prep row2")
                self._assert_ok(self._mark(d, 3, "--worker-duration-unknown"), "prep row3")
                self._assert_ok(self._mark(d, 4, "--auto-pass"), "prep row4")
                code, stdout, stderr, data = self._mark(d, 5, "--auto-pass")
                self.assertEqual(code, 0, f"S-7/{mode} CLOSE auto-pass가 통과하지 않음 (stdout={stdout!r})")
                self.assertTrue(data.get("ok"), f"S-7/{mode} mode-aware CLOSE 회귀 — {data!r}")

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
        ("B-8", 5, "semi-agentic", 0, None),
        ("B-9", 5, "agentic",      0, None),
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
                    self._assert_ok(self._mark(d, 3, "--worker-duration-unknown"), f"{cell} prep row3")
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
            ("CLOSE",   "interactive",  (False, "interactive_requires_user")),
            ("CLOSE",   "semi-agentic", (True,  None)),
            ("CLOSE",   "agentic",      (True,  None)),
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

    def test_opgc_and_opd_close_entry_are_mode_aware_S35(self):
        """S-35 — agentic CLOSE entry proceeds with or without a confirmation row."""
        with self.subTest(case="opgc-owner-user-passes-without-force"):
            d = self._opgc_ready("s35-owner-user")
            code, stdout, stderr, data = self._mark_key(d, "close.done_md", "--owner", "user")
            self.assertEqual(code, 0,
                f"S-35 확인 행 0개(opgc) CLOSE 첫 행이 --owner user로도 통과하지 못함"
                f"(폴백 미구현 — --force 없이는 영구 데드락) — {stdout!r}")
            self.assertEqual(data.get("status"), "done", f"S-35 {data!r}")

        with self.subTest(case="opgc-without-owner-proceeds"):
            d2 = self._opgc_ready("s35-no-owner")
            code, stdout, stderr, data = self._mark_key(d2, "close.done_md")
            self.assertEqual(code, 0, f"S-35 agentic opgc CLOSE가 진행하지 못함 — {stdout!r}")
            self.assertTrue(data.get("ok"), data)

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
                    if r.get("item") != "사용자 확인":
                        r["worker_duration_unknown"] = True
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
            code, stdout, stderr, data = self._mark_key(d3, "close.done_md")
            self.assertEqual(code, 0, f"S-35 agentic opd CLOSE가 진행하지 못함 — {stdout!r}")
            self.assertTrue(data.get("ok"), data)


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
        (d / "test-scenario.json").write_text(
            json.dumps({"version": 1, "scenarios": []}, ensure_ascii=False),
            encoding="utf-8",
        )
        return d

    def _next_action(self, d):
        code, stdout, stderr, data = _run070(["show", str(d), "--format", "json"])
        self.assertEqual(code, 0, f"S-36 show 실패: {stdout!r}/{stderr!r}")
        return (data.get("data") or {}).get("next_action")

    def test_agentic_next_action_suppresses_hollow_confirmation_S36(self):
        """S-36 — agentic opd 16행 전 구간에서 next_action이 '사용자 확인'을 가리키지
        않는다. CLOSE 직전(test.user_confirm)도 자동 진입 경계이므로 다음 CLOSE 행을
        가리킨다. 대조군 — interactive 모드는 확인 프론티어를 정상적으로 노출해야 한다
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

        with self.subTest(check="close-adjacent-confirmation-is-suppressed"):
            na = captured["test.pm_gate"]
            self.assertIsNotNone(na, "S-36 test.pm_gate 이후 next_action 미획득")
            self.assertIn("CLOSE DONE.md 생성", na,
                          "S-36 agentic CLOSE 직전 확인 행이 자동 진입 경로를 가리키지 않음")

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
            #
            # [106 종수 갱신] HEAD 대조는 "R-11 축의 변경이 ERROR_CODES를 접촉하지
            # 않았다"를 보는 장치이고, HEAD는 「이번 태스크 반영 전」을 뜻하는
            # 이동 기준점이다. 106 F-004가 `code_scan_citation_unmet` 1종을
            # 신규 등재(Step 4, `state_tool.py`)했으므로 HEAD와의 차분이 정확히
            # 그 1종이 된다 — 그래서 등가 비교를 (삭제 0건 고정) + (추가는 태스크가
            # 선언한 종목으로 한정)으로 분해한다. 미선언 종목 추가와 임의 삭제는
            # 그대로 FAIL하며, 106 커밋 후에는 차분이 공집합이 되어 부분집합
            # 판정이 양쪽 시점에서 모두 성립한다(단언 무력화 아님) (106).
            declared_new_codes = {
                "code_scan_citation_unmet",  # 106 F-004 R-4
                "plan_contract_unmet",       # 111 W-1
                # 118 W-4 (AC-4) — finalize-attribution 전용. allocator_root를
                # 추론하지 않고 명시 인자로만 받는 계약을 에러 코드로 집행한다.
                "allocator_root_required",
                "allocator_root_not_absolute",
                "allocator_root_invalid",
                "finalize_attribution_failed",
                "actor_unsupported_for_skill",  # 122 W-2
                "state_json_malformed",         # 134 W-2
                # 156 W-1 — resolve-start 충돌·재개 축 잠금, init actor·workspace 게이트
                "workspace_flag_conflict",
                "actor_flag_conflict",
                "workspace_required_for_skill",
                "resume_axis_locked",
                "actor_pm_retired",
                "worktree_path_required",
            }
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
                head_keys - current_keys, set(),
                f"S-40 ERROR_CODES 종목이 삭제됨 — "
                f"삭제={sorted(head_keys - current_keys)!r} "
                "(삭제는 어떤 태스크도 선언하지 않았다)")
            self.assertLessEqual(
                current_keys - head_keys, declared_new_codes,
                f"S-40 선언되지 않은 ERROR_CODES 종목이 추가됨 — "
                f"추가={sorted(current_keys - head_keys)!r} "
                f"선언={sorted(declared_new_codes)!r} "
                "(종수는 S-7·S-15가 실측 기준으로 판정 — 여기서 재고정 금지)")
