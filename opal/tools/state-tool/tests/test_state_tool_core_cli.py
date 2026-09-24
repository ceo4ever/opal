"""
@header {
  "module": "test_state_tool_core_cli",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool 기본 CLI·오류·상태 전이·검증 계약 테스트",
  "exports": ["TestBootSummary", "TestInit", "TestShow", "TestAdvance", "TestMark", "TestBlock", "TestValidate", "TestAddRow", "TestStatus", "TestGatePass", "TestErrorCodes", "TestG7StatusTransitions", "TestG10GatePass", "TestG12UserConfirmation", "TestG13CloseGate", "TestG14G15DecisionLog", "TestBasicScenarios", "TestFreeTextPreservation", "TestNextActionAutoDerive", "TestConflictConstraints", "TestRowsFrom", "TestErrorCodesCompleteness"]
}
"""

from state_tool_test_support import *  # noqa: F401,F403

class TestBootSummary(unittest.TestCase):
    """W-1 RED: direct + canonical worktree boot summary contracts."""

    def _state(self, task_dir, status, updated, stage="EXECUTE", next_action="계속 진행",
               task_id=None):
        task_dir.mkdir(parents=True)
        (task_dir / "state.json").write_text(json.dumps({
            "task_id": task_id or task_dir.name,
            "current_status": status,
            "updated_at": updated,
            "next_action": next_action,
            "rows": [{"stage": stage, "status": "in_progress"}],
        }, ensure_ascii=False), encoding="utf-8")

    def _registry_meta(self, root, name, task_dir, *, task_folder=None,
                       attribution_state="attribution_pending"):
        meta_dir = root / ".opal-worktrees" / ".meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "task_path": str(task_dir.resolve()),
            "task_folder": task_folder or task_dir.name,
            "allocator_root": str(root.resolve()),
        }
        if attribution_state is not None:
            meta["attribution_state"] = attribution_state
        path = meta_dir / name
        path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        return path

    def _boot_cli(self, root, *, cwd=None):
        completed = subprocess.run(
            ["bash", str(_RUN_SH), "boot-summary", str(root)],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed, json.loads(completed.stdout)

    def test_latest_unfinished_only_and_fields(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self._state(root / "tasks" / "101-old", "in_progress", "2026-09-10 10:00")
            self._state(root / "tasks" / "102-new", "blocked", "2026-09-11 10:00", "QA", "수정 필요")
            self._state(root / "tasks" / "103-done", "done", "2026-09-11 11:00")
            before = (root / "tasks" / "102-new" / "state.json").read_bytes()
            result = ST.collect_boot_summary(root)
            self.assertEqual(result, [{"title": "102-new", "stage": "QA", "next_action": "수정 필요"}])
            self.assertEqual(before, (root / "tasks" / "102-new" / "state.json").read_bytes())

    def test_missing_and_corrupt_states_are_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            tasks = root / "tasks"
            (tasks / "missing").mkdir(parents=True)
            (tasks / "broken").mkdir(parents=True)
            (tasks / "broken" / "state.json").write_text("{bad", encoding="utf-8")
            self.assertEqual(ST.collect_boot_summary(root), [])

    def test_cli_output_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self._state(root / "tasks" / "long", "in_progress", "2026-09-11 10:00",
                        next_action="x" * 10000)
            cmd = ["bash", str(_RUN_SH), "boot-summary", str(root)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertLessEqual(len(result.stdout.strip().encode("utf-8")), 1024)

    def test_registry_only_uses_canonical_task_path_independent_of_cwd(self):
        """Task 133 S-2 / PLAN D-2: registry path is authority, not cwd/layout inference."""
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            root = pathlib.Path(d) / "hub"
            root.mkdir()
            canonical = pathlib.Path(d) / "allocator-issued-location" / "tasks" / "202-wt"
            self._state(canonical, "in_progress", "2026-09-13 12:00", "EXECUTE", "GREEN 구현")
            self._registry_meta(root, "task_202.json", canonical)

            before = (canonical / "state.json").read_bytes()
            first, first_payload = self._boot_cli(root, cwd=pathlib.Path(other))
            second, second_payload = self._boot_cli(root, cwd=root)

            self.assertEqual(first_payload, second_payload)
            self.assertEqual(
                first_payload["items"][0],
                {
                    "title": "202-wt",
                    "stage": "EXECUTE",
                    "next_action": "GREEN 구현",
                    "mode": "interactive",
                    "mode_source": "fail_closed",
                },
            )
            self.assertNotIn(str(canonical), first.stdout)
            self.assertEqual(before, (canonical / "state.json").read_bytes())

    def test_registry_missing_attribution_state_key_is_active(self):
        """Task 133 S-2: worktree §상태 의존 해석 defines a missing key as active."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d) / "hub"
            root.mkdir()
            canonical = pathlib.Path(d) / "issued" / "tasks" / "203-key-absent"
            self._state(canonical, "in_progress", "2026-09-13 12:30", "EXECUTE", "계속")
            meta_path = self._registry_meta(
                root,
                "task_203.json",
                canonical,
                attribution_state=None,
            )
            before = {
                meta_path: meta_path.read_bytes(),
                canonical / "state.json": (canonical / "state.json").read_bytes(),
            }

            _, payload = self._boot_cli(root)

            self.assertEqual(
                [item["title"] for item in payload["items"]],
                ["203-key-absent"],
            )
            self.assertNotIn(
                "registry_meta_missing_fields",
                json.dumps(payload["anomalies"], ensure_ascii=False),
            )
            self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_mixed_sources_sort_dedupe_and_separate_registry_anomalies(self):
        """Task 133 S-3 / PLAN D-1~D-4, H-1: canonical candidates and anomalies differ."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d) / "hub"
            root.mkdir()
            self._state(root / "tasks" / "301-direct", "in_progress", "2026-09-13 09:00")

            canonical = pathlib.Path(d) / "issued-a" / "tasks" / "302-shared"
            self._state(canonical, "in_progress", "2026-09-13 11:00", task_id="302-canonical")
            self._registry_meta(root, "task_302.json", canonical, task_folder="302-shared")
            self._state(root / "tasks" / "302-shared", "in_progress", "2026-09-13 12:00",
                        task_id="302-hub-copy")

            duplicate_a = pathlib.Path(d) / "issued-b" / "tasks" / "303-duplicate"
            duplicate_b = pathlib.Path(d) / "issued-c" / "tasks" / "303-duplicate"
            self._state(duplicate_a, "in_progress", "2026-09-13 13:00")
            self._state(duplicate_b, "in_progress", "2026-09-13 14:00")
            self._registry_meta(root, "task_303_a.json", duplicate_a)
            self._registry_meta(root, "task_303_b.json", duplicate_b)

            meta_dir = root / ".opal-worktrees" / ".meta"
            (meta_dir / "task_304.json").write_text(
                json.dumps({"task_folder": "304-missing-fields"}), encoding="utf-8")
            (meta_dir / "task_305.json").write_text(json.dumps({
                "task_path": str(pathlib.Path(d) / "gone" / "tasks" / "305-gone"),
                "task_folder": "305-gone",
                "allocator_root": str(root),
                "attribution_state": "attribution_pending",
            }), encoding="utf-8")
            (meta_dir / "task_306.json").write_text("{broken", encoding="utf-8")

            _, payload = self._boot_cli(root)
            self.assertEqual(
                [item["title"] for item in payload["items"]],
                ["302-canonical", "301-direct"],
            )
            self.assertEqual(
                [item["title"] for item in payload["items"]].count("302-canonical"), 1)
            self.assertNotIn("302-hub-copy", [item["title"] for item in payload["items"]])

            anomalies = json.dumps(payload["anomalies"], ensure_ascii=False)
            for code in (
                "task_path_ambiguous",
                "registry_meta_missing_fields",
                "registry_task_path_missing",
                "registry_active_duplicate",
                "registry_meta_corrupt",
            ):
                with self.subTest(code=code):
                    self.assertIn(code, anomalies)

    def test_many_multibyte_candidates_are_bounded_and_inputs_are_immutable(self):
        """Task 133 S-5 / PLAN D-5, H-2: JSON preserves counts within 1 KiB."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            for number in range(1, 6):
                self._state(
                    root / "tasks" / f"40{number}-fixture",
                    "in_progress",
                    f"2026-09-13 {number + 10:02d}:00",
                    next_action="다국어 다음 행동 " * 80,
                    task_id=f"40{number}-" + "아주 긴 제목 " * 80,
                )
            meta_dir = root / ".opal-worktrees" / ".meta"
            meta_dir.mkdir(parents=True)
            (meta_dir / "task_499.json").write_text("{broken", encoding="utf-8")
            inputs = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}

            completed, payload = self._boot_cli(root)

            self.assertEqual(len(payload["items"]), 3)
            self.assertEqual(payload["other_count"], 2)
            self.assertEqual(len(payload["anomalies"]), 1)
            self.assertLessEqual(len(completed.stdout.strip().encode("utf-8")), 1024)
            self.assertEqual(inputs, {path: path.read_bytes() for path in inputs})


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
        """[T094 수정 / T118 D-4b 갱신] G-6: CLOSE 마지막 행 mark →
        current_status=completed_unmerged (PLAN §2.11 G-6 + 118 D-4b/AC-4 —
        CLOSE mark는 완료를 확정하되 허브 MEMORY 귀속은 하지 않는다).
        '- 상태: 완료' STATE.md 렌더는 D-1로 제거되었다 — 동일 정보는
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
        self.assertEqual(state["current_status"], "completed_unmerged")

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
    def test_agentic_close_auto_pass_preserves_clarification_guard(self):
        """#16 agentic CLOSE no longer emits the legacy close-gate error, but --auto-pass
        may not bypass the independent clarification guard."""
        rows = json.dumps([
            {"stage": "TASK",  "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows, mode="agentic")
        # 093 F-001: 사용자 확인 행은 init 시 pending이며, CLOSE 직전 행이라 훅이
        # 자동 승인하지 않는다(DEC-D) — 캡틴 승인으로 CLOSE 게이트 축까지 도달시킨다.
        self._mark(1, owner="user")
        before = (self.task_path / "state.json").read_bytes()
        # agentic 모드에서 CLOSE 첫 행에 auto-pass 시도
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=2, done=True, auto_pass=True,
            )
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1, result)
        self.assertEqual(result.get("error"), "clarification_gate_unmet", result)
        self.assertNotEqual(result.get("error"), "agentic_close_gate_requires_user", result)
        self.assertEqual((self.task_path / "state.json").read_bytes(), before)

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

    def test_g13_agentic_close_auto_pass_remains_clarification_guarded(self):
        """G-13: agentic CLOSE does not use the legacy close error; independent
        clarification protection still rejects manual --auto-pass."""
        self._init(rows_spec=self._make_close_rows(), mode="agentic")
        # 093 F-001: TASK 사용자 확인 행은 전 모드 pending으로 초기화된다.
        # CLOSE 직전 사용자 확인 행이므로 훅이 자동 승인하지 않는다(DEC-D) — 캡틴 승인 필수.
        self._mark(1, owner="user")
        before = (self.task_path / "state.json").read_bytes()
        # CLOSE 첫 행에 auto-pass 시도
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=2, done=True, auto_pass=True,
            )
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1, result)
        self.assertEqual(result.get("error"), "clarification_gate_unmet", result)
        self.assertNotEqual(result.get("error"), "agentic_close_gate_requires_user", result)
        self.assertEqual((self.task_path / "state.json").read_bytes(), before)

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
        """[T072/L1-R2,M-2][T094 수정][T118 D-4b] S-3 — 마지막 행까지 모두 완료
        (current_status=completed_unmerged)되면 프론티어(다음 대기 행)가 부재하므로
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

        code2 = self._mark(2)  # CLOSE State Gate → done, current_status=completed_unmerged
        self.assertEqual(code2, 0, "row2(CLOSE State Gate) mark 실패")

        state_final = self._state()
        self.assertEqual(state_final.get("current_status"), "completed_unmerged")
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

    def test_c6_agentic_auto_pass_close_first_row_preserves_clarification_guard(self):
        """C-6: the obsolete close-gate rejection is removed without weakening the
        clarification guard for manual --auto-pass."""
        rows = json.dumps([
            {"stage": "TASK",  "item": "사용자 확인"},
            {"stage": "CLOSE", "item": "State Gate"},
        ])
        self._init(rows_spec=rows, mode="agentic", force=True, note="재초기화")
        # 093 F-001/F-002: 사용자 확인 행은 pending 초기화 + CLOSE 직전이라 훅 제외(DEC-D)
        self._mark(1, owner="user")
        before = (self.task_path / "state.json").read_bytes()
        with _mock_now():
            args = make_args(
                task_path=str(self.task_path),
                row=2, done=True, auto_pass=True,
            )
            exit_code, result = self._call_cmd(ST.cmd_mark, args)
        self.assertEqual(exit_code, 1, result)
        self.assertEqual(result.get("error"), "clarification_gate_unmet", result)
        self.assertNotEqual(result.get("error"), "agentic_close_gate_requires_user", result)
        self.assertEqual((self.task_path / "state.json").read_bytes(), before)


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
    갱신됐다. 목록·카운트 둘 다 실측값(43)에 맞춰 동기화한다.

    [122 W-2] --actor 미지원 skill 거부 코드 1종 등재로 51→52.
    [134 W-2] 손상 state.json의 mode 복원 거부 코드 1종 등재로 52→53. PM 승인
    (카탈로그 정합 보존).
    [156 W-1] 세 축 resolver·init workspace 게이트 거부 코드 6종 등재로 53→59."""

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
        # 106 신규 1종 (F-004 R-4 — PLAN.md §4.2 code-scan 결과 인용 미충족 게이트)
        "code_scan_citation_unmet",
        # 111 신규 1종 — sdlc-v2 PLAN Work items 계약 위반
        "plan_contract_unmet",
        # 118 W-4 신규 4종 (AC-4 — finalize-attribution 전용, allocator_root 추론 금지 집행)
        "allocator_root_required",
        "allocator_root_not_absolute",
        "allocator_root_invalid",
        "finalize_attribution_failed",
        # 122 W-2 신규 1종 (--actor pm이 opd/opds 외 skill과 결합 시 거부 게이트)
        "actor_unsupported_for_skill",
        # 156 W-1 신규 6종 (resolve-start 충돌·재개 축 잠금, init actor·workspace 게이트)
        "workspace_flag_conflict",
        "actor_flag_conflict",
        "workspace_required_for_skill",
        "resume_axis_locked",
        "actor_pm_retired",
        "worktree_path_required",
        # 134 W-2 신규 1종 (손상 state.json의 mode 복원 하드 블록)
        "state_json_malformed",
    ]

    def test_error_codes_count(self):
        """[098 H-10 선갱신 + 106/111/122/134 종수 갱신] ERROR_CODES 53종 —
        093 시점 44종에서 098 F-003이 `evidence_check_flag_conflict` 1종을 등재해
        45종이 되고, 106 F-004가 `code_scan_citation_unmet` 1종을 등재해 46종,
        111 W-1이 `plan_contract_unmet` 1종을 등재해 47종, 118 W-4가
        finalize-attribution 전용 4종을 등재해 51종, 122 W-2가
        `actor_unsupported_for_skill` 1종을 등재해 52종, 134 W-2가
        `state_json_malformed` 1종을 등재해 53종, 156 W-1이 resolver·init
        게이트 코드 6종을 등재해 59종이다.

        갱신 근거: 신규 에러 코드 등재가 종수 단언을 같이 깨므로 등재 태스크가
        기대값을 함께 옮긴다. 111 W-1은 PLAN Work items 계약을 차단형 게이트로
        집행하므로 전용 에러 코드를 추가한다. 122 W-2는 `--actor pm`이 opd/opds
        외 skill과 결합될 때 전용 에러 코드로 거부한다(PM 승인, 카탈로그 정합
        보존)."""
        self.assertEqual(len(ST.ERROR_CODES), 59,
                         "[156 W-1] resolver·init 게이트 코드 6종 등재 후 59종 기대")

    def test_all_28_codes_registered(self):
        """[098 H-10 선갱신 + 106/111/122/134 종수 갱신] 53종 각각이 ERROR_CODES에 등재됨."""
        for code in self.EXPECTED_CODES:
            self.assertIn(code, ST.ERROR_CODES, f"에러 코드 {code} 미등재")
        self.assertEqual(len(self.EXPECTED_CODES), len(ST.ERROR_CODES),
                         "EXPECTED_CODES 목록 건수가 실측 ERROR_CODES 종수와 불일치")

    def test_s7_error_catalog_marker_import_realignment(self):
        """[T094/L1-F002 + 098 H-10 선갱신 + 106 종수 갱신] S-7 — 에러 카탈로그 코드↔문서
        정합(D-5 ①, R-3 AC(b)).

        기대: `marker_missing`·`import_failed`가 `ERROR_CODES`에서 삭제되고
        `import_existing_removed`가 신규 등재되며, 실측 `len(ERROR_CODES)`가
        `README.md`의 카탈로그 헤더 기재 종수와 일치해야 한다(설계 목표 43이나
        실측값을 채택 — PLAN §1.5 D-5 각주). 098부터는 두 종수 모두 45종을
        명시 기대했고(H-10 대응, PLAN §3.3.2 신규 에러 코드 1종), 106 F-004가
        `code_scan_citation_unmet` 1종을 등재해 **46종**으로 옮긴다 (106).

        갱신 근거(106, PLAN §4.2 Step 15): Step 4가 `state_tool.py`에 1종을
        등재해 실측 `len(ERROR_CODES)`가 46이 됐다. 코드↔문서 정합(D-5 ①)은
        두 축이 함께 움직여야 성립하므로 본 Step 15가 아래 하드코딩 종수
        기대값 2건과 `README.md` 카탈로그 헤더를 같은 46으로 맞춘다."""
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
        # [156 W-1] 종수 59 하드 기대 — resolver·init 게이트 6종 등재 반영
        self.assertEqual(actual_count, 59,
                         "[156 W-1] len(ERROR_CODES)==59 기대 — allocator_root_* / "
                         "finalize_attribution_failed / actor_unsupported_for_skill "
                         "/ state_json_malformed 등재가 유실되면 실패")
        self.assertEqual(readme_count, 59,
                         "[156 W-1] README 헤더 종수==59 기대 — 카탈로그 정정 누락")
