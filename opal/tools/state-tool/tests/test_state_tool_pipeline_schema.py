"""
@header {
  "module": "test_state_tool_pipeline_schema",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool pipeline·schema·task-step 호환 계약 테스트",
  "exports": ["TestOwnerNamePlaceholder", "TestOpplSkillInit", "TestSchemaModeEnumSemiAgentic", "TestPipelineSpecValidate", "TestPipelineJsonInit", "TestStateSchema11Compat", "TestTaskStepAddressing", "TestActionStepRename", "TestAddRowKey", "TestOpddEnumDrift", "TestGroupAPipelineSpecs", "TestBackwardCompatAliases"]
}
"""

from state_tool_test_support import *  # noqa: F401,F403

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
        real_pipeline_specs = [
            ("opal-pilot-project", "opal-pilot-project/references/pipeline.json"),
            ("opal-pilot-dev", "opal-pilot-dev/references/pipeline.json"),
            ("opal-pilot-dev-short", "opal-pilot-dev/references/pipeline-short.json"),
            ("opal-pilot-dev-wireframe", "opal-pilot-dev-wireframe/references/pipeline.json"),
            ("opal-pilot-write-tech", "opal-pilot-write-tech/references/pipeline.json"),
            ("opal-pilot-sdd", "opal-pilot-sdd/references/pipeline.json"),
            ("opal-pilot-data-design", "opal-pilot-data-design/references/pipeline.json"),
            ("opal-pilot-project-dev", "opal-pilot-project-dev/references/pipeline.json"),
            ("opal-pilot-project-loop", "opal-pilot-project-loop/references/pipeline.json"),
            ("opal-pilot-gc", "opal-pilot-gc/references/pipeline.json"),
        ]
        for skill_label, rel_path in real_pipeline_specs:
            spec_path = repo_root / "opal" / "skills" / rel_path
            with self.subTest(skill=skill_label):
                self.assertTrue(spec_path.exists(), f"실 pipeline.json 부재: {spec_path}")
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                violations = ST.validate_pipeline_spec(spec)
                self.assertEqual(violations, [],
                                  f"{skill_label} pipeline spec이 유효해야 하는데 violations: {violations}")
                code, stdout, stderr, data = _run070(["spec-validate", str(spec_path)])
                self.assertEqual(code, 0, f"{skill_label} spec-validate exit!=0 (stdout={stdout!r})")
                self.assertTrue(data.get("ok"), f"{skill_label} spec-validate ok:false: {data}")


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
        """[T070/S-4] schema_version이 enum이고 1.0/1.1을 함께 허용해야 함.

        123/T05(AC-4)이 로그 계약 블록을 가진 1.2를 같은 enum에 등재했으므로 판정은
        **완전 일치가 아니라 포함**이다 — 이 단언이 지키는 계약은 "1.1 병행 허용"이지
        "enum이 정확히 2종"이 아니다. 1.0/1.1 태스크가 계속 유효하다는 C-3 보장은
        아래 포함 단언으로 그대로 유지된다.
        """
        version_schema = self.schema["properties"]["schema_version"]
        self.assertIn("enum", version_schema,
                      f"schema_version이 아직 enum이 아님(1.1 병행 미지원): {version_schema}")
        self.assertLessEqual({"1.0", "1.1"}, set(version_schema["enum"]))

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
        """[T070/S-13, H-7] agentic CLOSE first row reaches mode-aware auto entry by task-step.
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
            extra = ["--worker-duration-unknown"] if rid in (3, 6) else []
            code, stdout, stderr, data = _run070(
                ["mark", str(agentic_task), "--row", str(rid), "--done", *extra]
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
        self.assertEqual(code, 0, f"agentic CLOSE 첫 행 auto-pass가 통과해야 함 (stdout={stdout!r})")
        self.assertTrue(data.get("ok"), f"CLOSE 게이트 회귀 — 실제 응답: {data!r}")


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
        for skill, spec, expected_count, _real_count, _skill_dir, _pipeline_file in _GROUP_A_SPECS:
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
        for skill, spec, _count, _real_count, _skill_dir, _pipeline_file in _GROUP_A_SPECS:
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
        for skill, _spec, _fixture_count, real_count, skill_dir, pipeline_file in _GROUP_A_SPECS:
            real_path = skills_root / skill_dir / "references" / pipeline_file
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
