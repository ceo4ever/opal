"""
@header {
  "module": "test_state_tool_extended_contracts",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool worker duration·citation·SDLC·actor·ownership·OPPB 계약 테스트",
  "exports": ["TestT098Add2RootDerivation", "TestT100DirectionEvidence", "TestT103WorkerDuration", "TestT103WorkerDurationWarning", "TestT103WorkerEnforce", "TestT106CodeScanCitationBehavior", "TestT111SdlcV2Contracts", "TestT111SdlcV2StateContracts", "TestActorFlag", "TestT138W9OwnershipClaimBoundary", "TestT138W9ActorSessionId", "TestT132OppbStageEnumExtension", "TestT132OppbSpecValidateSkillEnum"]
}
"""

from state_tool_test_support import *  # noqa: F401,F403

class TestT098Add2RootDerivation(unittest.TestCase):
    """098 ADD-2 RED — `_resolve_citation_exists()`(`state_tool_parts/gates.py:1003`)가 프로젝트
    루트를 `task_root(str(pathlib.Path(__file__).resolve()))`로, 즉
    `task_md_path`가 아니라 스크립트 자기 위치에서 파생하는 결함의 배포 경로
    등가성 실패 테스트.

    결함 재현: `state_tool.py`를 프로젝트 밖(조상에 `.opal/MEMORY.json`이 없는
    임시 디렉토리)으로 복사한 사본으로 실행하면 `task_root`가 None을
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
        # 109 — 자기 저장소 루트 가정 + 폴더명 하드코딩 결함 수정: 워크트리에서도
        # 허브를 가리키는 task_root + Step 7 `_find_repo_task_dir`(접두사
        # 탐색, tasks/ 직속·tasks/backup/ 모두 커버)로 대상을 동적 해석한다.
        # 0건·2건은 헬퍼가 AssertionError로 fail시킨다 — skipTest로 강등하지 않는다.
        repo_root = ST.task_root(str(_TOOL_DIR))
        assert repo_root is not None, (
            "task_root가 None을 반환함 — .opal/MEMORY.json 보유 조상을 찾지 못함"
        )
        cls._task_path = _find_repo_task_dir(repo_root, "098-")
        assert (cls._task_path / "TASK.md").is_file(), (
            f"본 태스크 TASK.md 부재 — 실파일 입력 전제가 깨짐: {cls._task_path}"
        )

    def setUp(self):
        self._copy_dir = pathlib.Path(tempfile.mkdtemp())
        self._copied_script = self._copy_dir / "state_tool.py"
        # 힌트: memory_tool.py는 `verify` 경로에서 미참조(_MEMORY_TOOL은
        # link_memory_history 전용 — cmd_mark에서만 소비)이므로 복사 불필요.
        shutil.copy2(_SRC_093, self._copied_script)
        shutil.copytree(_SRC_093.parent / "state_tool_parts", self._copy_dir / "state_tool_parts",
                        ignore=shutil.ignore_patterns("__pycache__"))

    def tearDown(self):
        shutil.rmtree(self._copy_dir, ignore_errors=True)

    def _run_verify(self, script_path):
        """공개 CLI `verify <task-path> --evidence-check` subprocess 실행 →
        stdout JSON dict. exit code는 라우터형이라 항상 0 기대(차단 없음,
        PLAN §3.3.2)."""
        result = subprocess.run(
            [sys.executable, str(script_path), "verify",
             str(self._task_path), "--evidence-check"],
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
        항목, 여기서는 '제약' 요소의 `opal/tools/state-tool/state_tool_parts/gates.py:876`)이
        `citation_path_not_found`를 받지 않아야 한다. 결함 현재: 사본 실행은
        실존 파일 인용까지 미존재로 오판정 — 지금 FAIL 기대."""
        copied_result = self._run_verify(self._copied_script)
        by_elem = {it.get("element"): it for it in copied_result.get("items", [])}

        constraint_item = by_elem.get("제약", {})
        citation = None
        for c in constraint_item.get("citations", []):
            if "state_tool_parts/gates.py:876" in str(c.get("raw", "")):
                citation = c
                break
        self.assertIsNotNone(
            citation,
            f"[RED] '제약' 항목에서 `state_tool_parts/gates.py:876` 인용을 찾지 못함 — "
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
        "opal/tools/state-tool/state_tool_parts/codes.py:100",
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
        (`state_tool_parts/gates.py:2326` `:2335` `:2345` — 신규 플래그 신설 금지)"""
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


class TestT103WorkerDuration(_T093Base):
    """103 R-15 — `mark --worker-duration-minutes`와 `rows[].worker_duration_minutes`.

    핵심 계약 3가지:
      (1) 인자를 넘기면 해당 행에 분 단위 정수로 기록된다
      (2) 넘기지 않으면 **필드를 만들지 않는다** — state.json·응답 키 집합 모두 종전과 동일
      (3) 음수·비정수는 거부되고, 거부 시 행이 전혀 변경되지 않는다(부분 상태 변경 부재)
    """

    def _fresh(self, mode="interactive", name="t103"):
        d = self._task_dir(name)
        # [재타겟] --run-log-mode 기본값이 shadow로 바뀌면서 미지정 init은 더 이상
        # 레거시(1.0/1.1) 태스크의 응답 형태를 재현하지 않는다. 이 계약(103 R-15/H-11)의
        # 취지는 "레거시 태스크의 mark 응답 키 집합 불변"이므로, fixture를
        # --run-log-mode off로 명시해 그 레거시 형태를 재현한다(계약 완화 아님).
        self._init(d, mode, rows_spec=_T103_SPEC, run_log_mode="off")
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
        """[T103/R-15 + 106/111 종수 갱신 + 122 W-2 종수 갱신] 값 검증은 argparse가
        파싱 시점에 수행하므로 ERROR_CODES는 건드리지 않는다 — 카탈로그 종수
        고정 테스트(S-7/S-15)와 충돌하지 않는다.

        [106/111] 이 케이스의 계약은 "103 축이 종목을 늘리지 않았다"이며(첫 단언),
        종수 리터럴은 실측 SSOT를 따라 45→47로 옮긴다 — 106 F-004와 111 W-1
        등재분은 103 축과 무관하다.

        [122 W-2] 종수 리터럴을 51→52로 옮긴다 — `actor_unsupported_for_skill`
        등재분이며 103 축과 무관하다. [134 W-2] `state_json_malformed` 등재로
        52→53이며 역시 103 축과 무관하다. [156 W-1] resolver·init 게이트 6종 등재로
        53→59이며 103 축과 무관하다."""
        self.assertNotIn("worker_duration_invalid", ST.ERROR_CODES,
                         "103이 ERROR_CODES를 신설했음 — 카탈로그 종수 계약 위반")
        self.assertEqual(len(ST.ERROR_CODES), 59,
                         f"ERROR_CODES 종수가 변했음(156 W-1 기준 59): {len(ST.ERROR_CODES)}")


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
        # [재타겟] 사유는 TestT103WorkerDuration._fresh와 동일 — 레거시 태스크의
        # mark 응답/산출물 형태를 재현하려면 --run-log-mode off를 명시해야 한다.
        self._init(d, mode, rows_spec=_T103W_SPEC, run_log_mode="off")
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
        # [재타겟] 사유는 TestT103WorkerDuration._fresh와 동일 — 레거시 태스크의
        # 응답 키 집합을 재현하려면 --run-log-mode off를 명시해야 한다.
        self._init(d, "interactive", rows_spec=_T103W_SPEC, run_log_mode="off")
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
        """[T103/R-21 + 106/111 종수 갱신 + 122 W-2 종수 갱신] 경고는 에러가 아니다 —
        경고 코드는 별도 사전(`WARNING_CODES`)에 살고 R-21은 `ERROR_CODES`를
        늘리지 않는다. 카탈로그를 공유하면 `err()`가 sys.exit로 끝나는 탓에
        '경고인데 차단'이라는 오용 경로가 생긴다.

        [106/111] 종수 리터럴은 실측 SSOT를 따라 45→47로 옮긴다 — 106 F-004와
        111 W-1 등재분이며 R-21 축과 무관하다.

        [122 W-2] 종수 리터럴을 51→52로 옮긴다 — `actor_unsupported_for_skill`
        등재분이며 R-21 축과 무관하다. [134 W-2] `state_json_malformed` 등재로
        52→53이며 역시 R-21 축과 무관하다. [156 W-1] resolver·init 게이트 6종 등재로
        53→59이며 R-21 축과 무관하다."""
        self.assertNotIn(self._CODE, ST.ERROR_CODES,
                         "R-21이 ERROR_CODES를 늘렸음 — 카탈로그 종수 계약 위반")
        self.assertEqual(len(ST.ERROR_CODES), 59,
                         f"ERROR_CODES 종수가 변했음(156 W-1 기준 59): {len(ST.ERROR_CODES)}")
        self.assertIn(self._CODE, ST.WARNING_CODES,
                      "WARNING_CODES에 worker_duration_missing 미등재")


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


class TestT106CodeScanCitationBehavior(_T093Base):
    """106 F-004/F-005 + S-25 — 게이트 동작 4케이스 + H-7 순서 계약.

    고정하는 계약:
    - C1 인용 0건 + `.py` + `--force --note` → exit 0 + `code_scan_citation_force`
      의사결정 로그 **1건**(091 `gate_artifact_force` 동형 — 도구가 기재를 집행한다).
    - C2 문서 전용 태스크(§4.2 대상 `.md`만) + force → exit 0 + **무기재**(오탐 0건).
      같은 트리에 `--auto-pass`를 넣어도 통과해야 한다 — 게이트 ⑥이 ③④⑤ **뒤**라는
      [MUST] 순서 계약(H-7)의 직접 관측점이다.
    - C3 인용 존재 + force → exit 0 + **무기재**(거부될 상태가 아니면 로그를 남기지 않는다).
    - C4 인용 0건 + `--auto-pass`(force 없음) → 거부 불변(exit 1, 게이트 ⑥).
    """

    def setUp(self):
        super().setUp()
        # 실 파일 픽스처 — tmpdir을 프로젝트 루트로 만든다.
        # `task_root`는 조상 중 `.opal/MEMORY.json` 보유 첫 디렉토리를 루트로 잡으므로
        # 이 파일 없이는 게이트 ③이 무조건 이탈해 관찰이 불가능하다.
        opal_dir = self.tmpdir / ".opal"
        opal_dir.mkdir(parents=True, exist_ok=True)
        (opal_dir / "MEMORY.json").write_text(
            _t093_json({"history": []}), encoding="utf-8")
        (opal_dir / "code-scan.json").write_text(
            _t093_json({"headerSource": "inline",
                        "extensions": [".py", ".js", ".ts"]}), encoding="utf-8")

    # ── 픽스처 ────────────────────────────────────────────────────────────
    def _execute_ready(self, name, plan_body):
        """EXECUTE 첫 행(row 3) 직전까지 진행된 실 태스크 폴더를 만든다."""
        d = self._task_dir(name)
        self._init(d, "semi-agentic", rows_spec=_T106_ROWS_SPEC)
        (d / "PLAN.md").write_text(plan_body, encoding="utf-8")
        self._assert_ok(self._mark(d, 1), f"{name} row1(TASK)")
        self._assert_ok(self._mark(d, 2), f"{name} row2(PLAN)")
        return d

    # ── 관찰 ──────────────────────────────────────────────────────────────
    def _decision_rows(self, task_dir):
        """STATE.md 「## 의사결정 로그」 표의 **데이터 행**만 셀 리스트로 돌려준다."""
        md = (task_dir / "STATE.md").read_text(encoding="utf-8")
        rows, in_section = [], False
        for line in md.splitlines():
            if line.startswith("## "):
                in_section = (line.strip() == "## 의사결정 로그")
                continue
            if not in_section or not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells[:1] == ["#"]:                       # 표 헤더
                continue
            if set("".join(cells)) <= {"-"}:             # 구분선
                continue
            rows.append(cells)
        return rows

    def _code_scan_decision_rows(self, task_dir):
        """의사결정 로그 중 **code-scan 게이트가 남긴** 행만 골라낸다.

        `--auto-pass`는 그 자체로 `agentic auto-pass at row N` 행을 남기는 별개
        계약(093)이다. 전체 로그 공백을 단언하면 그 무관한 행에 걸려 게이트 축을
        관찰할 수 없으므로, 게이트가 쓰는 결정 코드로 좁힌다.
        """
        return [r for r in self._decision_rows(task_dir)
                if "code_scan_citation" in r[2]]

    # ── C1 ────────────────────────────────────────────────────────────────
    def test_c1_force_bypass_records_decision_log(self):
        """[T106/C1] 인용 0건 + `.py` 대상 + `--force --note` → exit 0 + 로그 1건.

        S-25 계약: force는 조기 반환하지 않고 ③④⑤ skip·⑥⑦ 판정을 통과해
        "실제로 거부될 상태였는지"를 확정한 뒤 우회 사유를 반환하고, `cmd_mark`가
        `code_scan_citation_force`를 의사결정 로그에 **강제 기재**한다.
        """
        d = self._execute_ready("c1", _T106_PLAN_CODE_NO_CITATION)
        code, stdout, stderr, data = self._mark(
            d, 3, "--force", "--note", _T106_NOTE)
        self.assertEqual(code, 0,
                         f"C1 force 우회는 통과해야 한다 (stdout={stdout!r} stderr={stderr!r})")
        self.assertTrue(data.get("ok"), f"C1 ok:true 기대 — {stdout!r}")
        self.assertEqual(self._row(d, 3)["status"], "done", "C1 row 3이 done이어야 한다")

        logged = self._decision_rows(d)
        self.assertEqual(len(logged), 1,
                         f"C1 의사결정 로그 1건 기대 — 실제 {len(logged)}건: {logged!r}")
        decision, reason = logged[0][2], logged[0][3]
        self.assertIn("code_scan_citation_force", decision,
                      f"C1 결정 셀에 우회 코드가 없다: {decision!r}")
        self.assertIn("row 3", decision, f"C1 결정 셀에 행 식별자가 없다: {decision!r}")
        self.assertIn("citation_absent", decision,
                      f"C1 결정 셀에 실제 미충족 사유가 없다: {decision!r}")
        self.assertEqual(reason, _T106_NOTE, "C1 근거 셀은 --note 원문이어야 한다")

    # ── C2 ────────────────────────────────────────────────────────────────
    def test_c2_doc_only_task_leaves_no_decision_log(self):
        """[T106/C2 ★] 문서 전용 태스크는 force에서도 **무기재** + auto-pass 통과.

        ⑤ 적용 범위 게이트에서 조용히 이탈하므로 우회할 것이 없다 — 여기서 로그가
        남으면 문서 태스크마다 허위 우회 기록이 쌓인다(오탐).
        후반부는 [MUST] H-7 — ⑥(auto_pass 거부)이 ③④⑤ **앞**으로 올라가면
        문서 전용 태스크가 `--auto-pass`에서 차단되며 즉시 실패한다.
        """
        d = self._execute_ready("c2-force", _T106_PLAN_DOC_ONLY)
        code, stdout, stderr, _data = self._mark(
            d, 3, "--force", "--note", _T106_NOTE)
        self.assertEqual(code, 0,
                         f"C2 문서 전용 태스크는 통과해야 한다 (stdout={stdout!r} stderr={stderr!r})")
        self.assertEqual(self._decision_rows(d), [],
                         "C2 ⑤에서 이탈했으므로 의사결정 로그가 비어야 한다(오탐 0건)")

        # H-7 순서 관측 — force 없이 --auto-pass만으로도 ⑤ 이탈이 우선해야 한다.
        d2 = self._execute_ready("c2-autopass", _T106_PLAN_DOC_ONLY)
        code2, stdout2, stderr2, _d2 = self._mark(d2, 3, "--auto-pass")
        self.assertEqual(code2, 0,
                         "C2/H-7 ⑥이 ③④⑤보다 앞에 있으면 문서 전용 태스크가 auto-pass에서 "
                         f"오탐 차단된다 (stdout={stdout2!r} stderr={stderr2!r})")
        self.assertEqual(self._code_scan_decision_rows(d2), [],
                         "C2/H-7 auto-pass 통과 경로에도 게이트 우회 기록이 남지 않아야 한다")

    # ── C3 ────────────────────────────────────────────────────────────────
    def test_c3_citation_present_leaves_no_decision_log(self):
        """[T106/C3] 인용이 **존재**하면 force에서도 무기재.

        `--force`는 상시 붙는 인자다. 통과 상태에서도 로그를 남기면 우회 기록이
        신호를 잃는다(091 `gate_artifact_force` 동형 — 미충족 시에만 기재).
        """
        d = self._execute_ready("c3", _T106_PLAN_CODE_WITH_CITATION)
        code, stdout, stderr, _data = self._mark(
            d, 3, "--force", "--note", _T106_NOTE)
        self.assertEqual(code, 0,
                         f"C3 인용 존재 시 통과해야 한다 (stdout={stdout!r} stderr={stderr!r})")
        self.assertEqual(self._row(d, 3)["status"], "done", "C3 row 3이 done이어야 한다")
        self.assertEqual(self._decision_rows(d), [],
                         "C3 거부될 상태가 아니므로 의사결정 로그가 비어야 한다")

    # ── C4 ────────────────────────────────────────────────────────────────
    def test_c4_auto_pass_cannot_bypass_gate(self):
        """[T106/C4] 인용 0건 + `--auto-pass`(force 없음) → 거부 불변(게이트 ⑥).

        차단은 `save_state_json()` 이전 검증 구간에서 일어나므로 실 파일이
        오염되지 않아야 한다 — 부분 상태 변경 부재까지 함께 고정한다.
        """
        d = self._execute_ready("c4", _T106_PLAN_CODE_NO_CITATION)
        code, stdout, _stderr, data = self._mark(d, 3, "--auto-pass")
        self.assertEqual(code, 1, f"C4 auto-pass 우회는 거부돼야 한다 — {stdout!r}")
        self.assertEqual(data.get("error"), "code_scan_citation_unmet",
                         f"C4 기존 에러 코드로 닫혀야 한다(신규 코드 금지) — {stdout!r}")
        self.assertIn("auto-pass cannot bypass code-scan citation gate",
                      data.get("missing") or [],
                      f"C4 missing이 ⑥ 사유를 지목해야 한다 — {stdout!r}")
        self.assertEqual(self._row(d, 3)["status"], "pending",
                         "C4 거부 시 row 3 상태가 변하지 않아야 한다")
        self.assertEqual(self._decision_rows(d), [],
                         "C4 거부 경로는 의사결정 로그를 남기지 않아야 한다")


class TestT111SdlcV2Contracts(unittest.TestCase):
    """sdlc-v2 신규 TASK/PLAN 계약은 새 라우트로 판정하고 legacy는 기존 경로로 둔다."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="opal-state-t111-"))
        opal_dir = self.tmpdir / ".opal"
        opal_dir.mkdir(parents=True, exist_ok=True)
        (opal_dir / "MEMORY.json").write_text(_t093_json({"history": []}), encoding="utf-8")
        (opal_dir / "code-scan.json").write_text(
            _t093_json({"headerSource": "inline", "extensions": [".py"]}), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _task_dir(self, name):
        d = self.tmpdir / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _verify(self, task_dir, *args):
        cmd = ["bash", str(_RUN_SH), "verify", str(task_dir)] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        stdout = result.stdout.strip()
        try:
            data = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            data = {"_raw": stdout}
        return result.returncode, stdout, data

    def test_sdlc_v2_task_required_sections_pass(self):
        d = self._task_dir("task-pass")
        (d / "TASK.md").write_text(_T111_TASK_OK, encoding="utf-8")
        code, stdout, data = self._verify(d, "--clarification-check")

        self.assertEqual(code, 0, stdout)
        self.assertEqual(data.get("clarification_check"), "pass")

    def test_sdlc_v2_task_missing_required_section_fails(self):
        d = self._task_dir("task-missing")
        (d / "TASK.md").write_text(
            _T111_TASK_OK.replace("## Constraints\n- C-1. 상태는 state.json만 소유한다.\n\n", ""),
            encoding="utf-8",
        )
        code, stdout, data = self._verify(d, "--clarification-check")

        self.assertEqual(code, 1, stdout)
        self.assertEqual(data.get("error"), "clarification_gate_unmet")
        self.assertIn("Constraints", data.get("missing") or [])

    def test_sdlc_v2_plan_work_items_contract_passes(self):
        d = self._task_dir("plan-pass")
        (d / "TASK.md").write_text(_T111_TASK_OK, encoding="utf-8")
        (d / "PLAN.md").write_text(_T111_PLAN_OK, encoding="utf-8")
        code, stdout, data = self._verify(d, "--plan-contract-check")

        self.assertEqual(code, 0, stdout)
        self.assertEqual(data.get("plan_contract_check"), "pass")
        self.assertEqual(data.get("work_items"), ["W-1", "W-2"])

    def test_sdlc_v2_plan_rejects_unknown_dependency_and_completion_ref(self):
        d = self._task_dir("plan-bad-ref")
        (d / "TASK.md").write_text(_T111_TASK_OK, encoding="utf-8")
        bad = _T111_PLAN_OK.replace("| W-2. 문서 갱신 | opal-task-agent | `opal/tools/state-tool/README.md` | README 갱신 | W-1 | P2 | AC-1 |",
                                    "| W-2. 문서 갱신 | opal-task-agent | `opal/tools/state-tool/README.md` | README 갱신 | W-9 | P2 | AC-9 |")
        (d / "PLAN.md").write_text(bad, encoding="utf-8")
        code, stdout, data = self._verify(d, "--plan-contract-check")

        self.assertEqual(code, 1, stdout)
        self.assertEqual(data.get("error"), "plan_contract_unmet")
        missing = "\n".join(data.get("missing") or [])
        self.assertIn("unknown dependency W-9", missing)
        self.assertIn("unknown completion ref AC-9", missing)

    def test_sdlc_v2_plan_rejects_same_group_file_conflict(self):
        d = self._task_dir("plan-conflict")
        (d / "TASK.md").write_text(_T111_TASK_OK, encoding="utf-8")
        bad = _T111_PLAN_OK.replace("| W-2. 문서 갱신 | opal-task-agent | `opal/tools/state-tool/README.md` | README 갱신 | W-1 | P2 | AC-1 |",
                                    "| W-2. 문서 갱신 | opal-task-agent | `opal/tools/state-tool/state_tool.py` | 같은 파일 병렬 수정 | 없음 | P1 | AC-1 |")
        (d / "PLAN.md").write_text(bad, encoding="utf-8")
        code, stdout, data = self._verify(d, "--plan-contract-check")

        self.assertEqual(code, 1, stdout)
        self.assertEqual(data.get("error"), "plan_contract_unmet")
        self.assertTrue(any("file conflict W-1/W-2" in m for m in data.get("missing") or []))

    def test_code_scan_citation_reads_sdlc_v2_work_items(self):
        d = self._task_dir("plan-code-scan")
        (d / "TASK.md").write_text(_T111_TASK_OK, encoding="utf-8")
        no_citation = _T111_PLAN_OK.replace("code-scan 조회 결과를 인용한다.\n\n", "")
        (d / "PLAN.md").write_text(no_citation, encoding="utf-8")
        code, stdout, data = self._verify(d, "--code-scan-citation-check")

        self.assertEqual(code, 1, stdout)
        self.assertEqual(data.get("error"), "code_scan_citation_unmet")
        self.assertIn("opal/tools/state-tool/state_tool.py", data.get("target_files") or [])


class TestT111SdlcV2StateContracts(_T093Base):
    """111 W-1 — 공개 CLI 기준 RED-first 계약 테스트."""

    def _write_task(self, task_dir, body=_T111_TASK_V2):
        (task_dir / "TASK.md").write_text(body, encoding="utf-8")

    def _write_plan(self, task_dir, body=_T111_PLAN_V2):
        (task_dir / "PLAN.md").write_text(body, encoding="utf-8")

    def _v2_task_without_section(self, section):
        lines = _T111_TASK_V2.splitlines()
        out, skipping = [], False
        for line in lines:
            if line.strip() == f"## {section}":
                skipping = True
                continue
            if skipping and line.startswith("## "):
                skipping = False
            if not skipping:
                out.append(line)
        return "\n".join(out) + "\n"

    def _project_ready_task(self, name):
        opal_dir = self.tmpdir / ".opal"
        opal_dir.mkdir(parents=True, exist_ok=True)
        (opal_dir / "MEMORY.json").write_text(
            _t093_json({"history": []}), encoding="utf-8")
        (opal_dir / "code-scan.json").write_text(
            _t093_json({"headerSource": "inline",
                        "extensions": [".py", ".js", ".ts"]}), encoding="utf-8")
        d = self._task_dir(name)
        self._write_task(d)
        return d

    def _verify(self, task_dir, *flags):
        return _run070(["verify", str(task_dir), *flags])

    def test_s1_sdlc_v2_task_required_sections_pass(self):
        """S-1 — first YAML frontmatter `template: sdlc-v2` + 필수 5절 채움 → pass."""
        d = self._task_dir("t111-task-pass")
        self._write_task(d)
        code, stdout, stderr, data = self._verify(d, "--clarification-check")
        self.assertEqual(code, 0, f"v2 TASK 완전본은 통과해야 한다: {stdout!r} {stderr!r}")
        self.assertEqual(data.get("clarification_check"), "pass")
        self.assertEqual(data.get("template"), "sdlc-v2")

    def test_s2_sdlc_v2_task_missing_required_sections_fail(self):
        """S-2 — v2 TASK 필수 5절 각각의 누락은 skip 없이 거부한다."""
        required = [
            "Problem", "Proposed outcome", "Affected users and systems",
            "Constraints", "Acceptance criteria",
        ]
        for section in required:
            with self.subTest(section=section):
                d = self._task_dir(f"t111-task-missing-{section.replace(' ', '-')}")
                self._write_task(d, self._v2_task_without_section(section))
                code, stdout, _stderr, data = self._verify(d, "--clarification-check")
                self.assertEqual(code, 1, f"{section} 누락은 거부되어야 한다: {stdout!r}")
                self.assertEqual(data.get("error"), "clarification_gate_unmet")
                self.assertIn(section, data.get("missing") or [])

    def test_s3_legacy_task_still_uses_legacy_clarification_path(self):
        """S-3 — legacy TASK는 기존 `## 명확화 결과` 경로로 판정한다."""
        d = self._task_dir("t111-legacy-task")
        (d / "TASK.md").write_text(_TASK_MD_ALL_FILLED, encoding="utf-8")
        code, stdout, _stderr, data = self._verify(d, "--clarification-check")
        self.assertEqual(code, 0, f"legacy 정상 TASK는 기존 경로로 통과해야 한다: {stdout!r}")
        self.assertEqual(data.get("clarification_check"), "pass")
        self.assertEqual(data.get("template"), "legacy")

    def test_s4_plan_contract_pass_and_legacy_skip(self):
        """S-4 — v2 Work items 정상본은 통과하고 legacy PLAN은 명시 skip한다."""
        d = self._task_dir("t111-plan-pass")
        self._write_task(d)
        self._write_plan(d)
        code, stdout, _stderr, data = self._verify(d, "--plan-contract-check")
        self.assertEqual(code, 0, f"v2 PLAN 정상본은 통과해야 한다: {stdout!r}")
        self.assertEqual(data.get("plan_contract_check"), "pass")
        self.assertEqual(data.get("work_item_ids"), ["W-1", "W-2"])

        legacy = self._task_dir("t111-plan-legacy")
        self._write_plan(legacy, _T111_PLAN_LEGACY)
        code2, stdout2, _stderr2, data2 = self._verify(legacy, "--plan-contract-check")
        self.assertEqual(code2, 0, f"legacy PLAN은 명시 skip이어야 한다: {stdout2!r}")
        self.assertEqual(data2.get("plan_contract_check"), "skipped")
        self.assertEqual(data2.get("reason"), "legacy_plan")

    def test_s4_plan_contract_rejects_bad_work_items(self):
        """S-4 — 필수 열·중복 W·미확인 선행·순환·P 역행·파일 충돌·AC/C 미연결을 거부한다."""
        cases = {
            "missing_column": _T111_PLAN_V2.replace(" | 완료 기준 연결", ""),
            "duplicate_w": _T111_PLAN_V2.replace("W-2. PLAN 검사", "W-1. PLAN 검사"),
            "unknown_dep": _T111_PLAN_V2.replace("W-1 | P2", "W-99 | P2"),
            "cycle": _T111_PLAN_V2.replace("없음 | P1", "W-2 | P1"),
            "group_order": _T111_PLAN_V2.replace("W-1 | P2", "W-1 | P0"),
            "same_group_file_conflict": _T111_PLAN_V2.replace(
                "`opal/tools/state-tool/tests/test_state_tool.py` | Work items 계약을 검사한다. | W-1 | P2",
                "`opal/tools/state-tool/state_tool.py` | Work items 계약을 검사한다. | 없음 | P1",
            ),
            "unknown_ac": _T111_PLAN_V2.replace("AC-2, C-2", "AC-99, C-2"),
            "unlinked_w": _T111_PLAN_V2.replace("AC-2, C-2", "H-1"),
        }
        for name, plan_body in cases.items():
            with self.subTest(name=name):
                d = self._task_dir(f"t111-plan-bad-{name}")
                self._write_task(d)
                self._write_plan(d, plan_body)
                code, stdout, _stderr, data = self._verify(d, "--plan-contract-check")
                self.assertEqual(code, 1, f"{name}은 거부되어야 한다: {stdout!r}")
                self.assertEqual(data.get("error"), "plan_contract_unmet")
                self.assertTrue(data.get("violations"), f"{name} violations 필요: {stdout!r}")

    def test_s5_code_scan_citation_reads_v2_work_items_targets(self):
        """S-5 — code-scan 인용 검사는 v2 Work items 변경 대상을 우선 인식한다."""
        d = self._project_ready_task("t111-citation-missing")
        self._write_plan(d, _T111_PLAN_V2.replace("code-scan 결과 domain 필드를 확인했다.\n\n", ""))
        code, stdout, _stderr, data = self._verify(d, "--code-scan-citation-check")
        self.assertEqual(code, 1, f"v2 Work items의 .py 대상은 인용 누락을 거부해야 한다: {stdout!r}")
        self.assertEqual(data.get("error"), "code_scan_citation_unmet")
        self.assertIn("opal/tools/state-tool/state_tool.py", data.get("target_files") or [])

        ok_dir = self._project_ready_task("t111-citation-pass")
        self._write_plan(ok_dir)
        code2, stdout2, _stderr2, data2 = self._verify(ok_dir, "--code-scan-citation-check")
        self.assertEqual(code2, 0, f"v2 Work items 대상 + 인용 존재는 통과해야 한다: {stdout2!r}")
        self.assertEqual(data2.get("code_scan_citation_check"), "pass")
        self.assertIn("domain", data2.get("matched_tokens") or [])

    def test_s12_state_tool_mode_contracts_remain_unchanged(self):
        """S-12 — state-tool 3-way mode 선택지와 자동 승인 경계는 기존 계약 그대로다."""
        parser = ST.build_parser()
        init_action = next(a for a in parser._subparsers._group_actions
                           if isinstance(a, argparse._SubParsersAction)).choices["init"]
        mode_action = next(a for a in init_action._actions if a.dest == "mode")
        self.assertEqual(set(mode_action.choices), {"interactive", "semi-agentic", "agentic"})
        self.assertEqual(tuple(ST.can_auto_approve_user_confirmation("TASK", "semi-agentic")),
                         (False, "semi_agentic_pre_execute"))
        self.assertEqual(tuple(ST.can_auto_approve_user_confirmation("EXECUTE", "semi-agentic")),
                         (True, None))
        self.assertEqual(tuple(ST.can_auto_approve_user_confirmation("CLOSE", "agentic")),
                         (True, None))


class TestActorFlag(BaseTestCase):
    """122: `state-tool init --actor pm` — TEST-SCENARIO.md S-1~S-4 (PLAN D-4/W-2)."""

    def setUp(self):
        super().setUp()
        self.assertTrue(
            _OPDS_REAL_PIPELINE_SHORT_JSON.exists(),
            f"실 pipeline-short.json이 없음: {_OPDS_REAL_PIPELINE_SHORT_JSON}",
        )
        self.assertTrue(
            _S1_BASELINE_ROWS_FIXTURE.exists(),
            f"S-1 기준 스냅샷 fixture가 없음: {_S1_BASELINE_ROWS_FIXTURE}",
        )

    def _new_task_path(self, name):
        p = self.tmpdir / name
        p.mkdir()
        return p

    def _init_opds(self, task_path, actor=None):
        """`--skill opds --mode agentic --rows-from pipeline-short.json`(실 파일)로
        init. actor가 주어지면 --actor 값으로 함께 전달한다(현재 argparse/cmd_init에는
        --actor 처리가 없으므로 그대로 무시되는 것이 RED 증거)."""
        kwargs = dict(
            task_path=str(task_path),
            skill="opds",
            mode="agentic",
            rows_from=str(_OPDS_REAL_PIPELINE_SHORT_JSON),
            force=False,
            note=None,
            import_existing=False,
            next_action=None,
            task_title=None,
        )
        if actor is not None:
            kwargs["actor"] = actor
        with _mock_now():
            args = make_args(**kwargs)
            return self._call_cmd(ST.cmd_init, args)

    # ── S-1: --actor 미전달 시 actor 키 부재 + rows[] 16행이 기준과 동일 ────

    def test_s1_actor_unspecified_no_actor_key_and_rows_match_baseline(self):
        """[T122/S-1] --actor 미전달로 opds init 실행 → state.json에 "actor" 키가
        부재하고, rows[] 16행이 Task 136 CLOSE tail 반영 기준 스냅샷(fixtures/s1_baseline_rows.json)
        과 (row_id/stage/item/key/status/owner/gate 등) 정규화 후 동일해야 한다."""
        task_path = self._new_task_path("s1_no_actor")
        exit_code, _ = self._init_opds(task_path)
        self.assertEqual(exit_code, 0, "--actor 미전달 init은 exit 0이어야 한다")

        state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        self.assertNotIn("actor", state, "미지정인데 actor 키가 생성됨(AC-4/H-1 위반)")

        baseline_rows = json.loads(_S1_BASELINE_ROWS_FIXTURE.read_text(encoding="utf-8"))
        rows = state.get("rows")
        self.assertEqual(len(rows), 16, "task_steps[] 는 16행이어야 한다")
        self.assertEqual(len(baseline_rows), 16, "기준 스냅샷도 16행이어야 한다(fixture 자체 점검)")

        # 실행마다 달라지는 필드는 없다 — rows[] 항목은 created_at/updated_at/task_id에
        # 의존하지 않으므로 정규화 없이 바로 비교 가능(정규화 대상은 top-level 3필드뿐).
        self.assertEqual(
            rows, baseline_rows,
            "rows[] 16행의 key·순서·상태가 Task 136 기준 스냅샷과 달라짐(C-3 위반)",
        )

    # ── S-2: --actor coordinator --skill opds → state["actor"] == "coordinator", 행 16개 유지 ──
    # [156 W-1] legacy `pm`은 신규 init에서 actor_pm_retired로 거부되므로(test_start_resolution
    # S-4) 조건부 영속화 계약은 새 PM 조율 값 `coordinator`로 검증한다.

    def test_s2_actor_coordinator_skill_opds_sets_actor_key_rows_unchanged(self):
        """[T122/S-2 → 156] `--actor coordinator --skill opds` → state["actor"] ==
        "coordinator"이고 rows[]는 S-1과 동일하게 16행이어야 한다."""
        task_path = self._new_task_path("s2_actor_coordinator")
        exit_code, _ = self._init_opds(task_path, actor="coordinator")
        self.assertEqual(exit_code, 0, "--actor coordinator --skill opds init은 exit 0이어야 한다")

        state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            state.get("actor"), "coordinator",
            "--actor coordinator 지정 시 state['actor']가 'coordinator'여야 한다",
        )
        rows = state.get("rows")
        self.assertEqual(len(rows), 16, "actor 지정과 무관하게 rows[]는 16행이어야 한다(AC-4)")

        baseline_rows = json.loads(_S1_BASELINE_ROWS_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(
            rows, baseline_rows,
            "actor 지정이 rows[] key·순서·상태를 바꾸면 안 된다(AC-4 위반)",
        )

    # ── S-3: --actor coordinator --skill opwt → exit 1, ok:false / actor_unsupported_for_skill ──

    def test_s3_actor_pm_skill_opwt_rejected_with_dedicated_error(self):
        """[T122/S-3 → 156] `--actor coordinator --skill opwt` → exit 1 + stdout JSON
        `ok:false`·`error == "actor_unsupported_for_skill"`. traceback(미포착 예외)이
        발생하지 않아야 한다 — SystemExit 이외의 예외가 나면 이 테스트 자체가 에러로
        실패해 그 사실을 드러낸다."""
        task_path = self._new_task_path("s3_actor_coordinator_opwt")
        kwargs = dict(
            task_path=str(task_path),
            skill="opwt",
            mode="agentic",
            rows_spec=SIMPLE_ROWS_SPEC,
            force=False,
            note=None,
            import_existing=False,
            next_action=None,
            task_title=None,
            actor="coordinator",
        )
        with _mock_now():
            args = make_args(**kwargs)
            exit_code, result = self._call_cmd(ST.cmd_init, args)

        self.assertEqual(
            exit_code, 1,
            f"--actor coordinator --skill opwt는 exit 1로 거부되어야 한다(현재 결과: {result!r})",
        )
        self.assertFalse(result.get("ok"), f"ok:false여야 한다: {result!r}")
        self.assertEqual(
            result.get("error"), "actor_unsupported_for_skill",
            f"error 코드가 actor_unsupported_for_skill이어야 한다: {result!r}",
        )


class TestT138W9OwnershipClaimBoundary(unittest.TestCase):
    """W-9 — 상태 전이 진입 경계의 자동 claim과 fail-safe."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.task_path = pathlib.Path(self.tmp.name) / "tasks" / "138-w9"
        self.task_path.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    # ── 실행 헬퍼 ────────────────────────────────────────────────────────────
    def _run(self, args, session_id=None):
        env = dict(os.environ)
        env.pop("OPAL_SESSION_ID", None)
        if session_id is not None:
            env["OPAL_SESSION_ID"] = session_id
        return subprocess.run(
            [sys.executable, str(_TOOL_DIR / "state_tool.py"), *args],
            capture_output=True, text=True, env=env)

    def _init(self, session_id=None, run_log_mode=None):
        args = ["init", str(self.task_path), "--skill", "opds", "--mode", "agentic",
                "--task-title", "138 W-9", "--rows-spec", _W9_ROWS_SPEC]
        if run_log_mode:
            args += ["--run-log-mode", run_log_mode]
        result = self._run(args, session_id=session_id)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    @property
    def _lease_file(self):
        return self.task_path / "run" / ".runtime" / "owner.json"

    def _lease(self):
        return json.loads(self._lease_file.read_text(encoding="utf-8"))

    def _row_status(self, row_id):
        state = json.loads((self.task_path / "state.json").read_text(encoding="utf-8"))
        return next(r for r in state["rows"] if r["row_id"] == row_id)["status"]

    def _run_log_events(self):
        events = []
        for segment in sorted((self.task_path / "run").glob("run-log-*.jsonl")):
            for line in segment.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))
        return events

    # ── 1. env 있음 + live lease 없음 → 최초 경계에서 원자 생성 ────────────
    def test_session_env_set_claims_lease_at_first_transition(self):
        """AC-12 — init은 claim하지 않고, 첫 상태 전이(advance)에서 lease가 원자 생성된다."""
        self._init(session_id="sess-w9-0001")
        self.assertFalse(
            self._lease_file.exists(),
            "init은 claim 경계가 아니다 — lease가 생기면 중복 삽입이다")

        result = self._run(["advance", str(self.task_path), "--row", "1"],
                           session_id="sess-w9-0001")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self._lease_file.exists(),
                        f"첫 전이에서 lease가 생성되어야 한다 — stderr={result.stderr!r}")
        lease = self._lease()
        self.assertEqual(lease["owner_session_id"], "sess-w9-0001")
        self.assertEqual(lease["status"], "active")
        self.assertEqual(lease["generation"], 1)
        self.assertEqual(self._row_status(1), "in_progress")

        # 같은 세션의 다음 전이는 멱등 — generation이 늘지 않는다(중복 claim 없음).
        result2 = self._run(["mark", str(self.task_path), "--row", "1", "--done"],
                            session_id="sess-w9-0001")
        self.assertEqual(result2.returncode, 0, result2.stderr)
        self.assertEqual(self._lease()["generation"], 1)
        self.assertEqual(self._lease()["claimed_at"], lease["claimed_at"])

    # ── 2. env 있음 + 다른 세션의 live lease → claim 안 함, 전이는 정상 ────
    def test_foreign_live_lease_is_not_taken_over_but_state_advances(self):
        """AC-13 — 타 세션 live lease는 이전하지 않으나 state 갱신은 막지 않는다."""
        self._init(session_id="sess-w9-owner")
        first = self._run(["advance", str(self.task_path), "--row", "1"],
                          session_id="sess-w9-owner")
        self.assertEqual(first.returncode, 0, first.stderr)
        before = self._lease()

        second = self._run(["mark", str(self.task_path), "--row", "1", "--done"],
                           session_id="sess-w9-intruder")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self._row_status(1), "done",
                         "타 세션 lease가 있어도 state 갱신은 차단되지 않는다")
        after = self._lease()
        self.assertEqual(after["owner_session_id"], before["owner_session_id"])
        self.assertEqual(after["generation"], before["generation"])
        self.assertEqual(after["heartbeat_at"], before["heartbeat_at"])
        self.assertIn("ownership_claim_skipped", second.stderr)
        self.assertIn("foreign_owner", second.stderr)

    # ── 3. env 부재 → claim 시도 없음, 차단 없음, 경고만 ───────────────────
    def test_session_env_absent_skips_claim_without_blocking(self):
        """C-9 — OPAL_SESSION_ID 부재는 경고만 남기고 기존 전이 계약을 그대로 둔다."""
        self._init()
        result = self._run(["advance", str(self.task_path), "--row", "1"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._row_status(1), "in_progress")
        self.assertFalse(self._lease_file.exists(),
                         "세션 식별자가 없으면 lease를 만들지 않는다")
        self.assertIn("ownership_session_id_missing", result.stderr)
        # 경고는 stdout JSON 계약을 오염시키지 않는다.
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertNotIn("warnings", payload)

    # ── 4-a. lease 도구가 오류를 반환 → 차단 없음, 경고만 ─────────────────
    def test_lease_write_failure_is_fail_safe(self):
        """C-9 — lease 기록이 실패해도(런타임 경로 점유) 상태 전이는 통과한다."""
        self._init(session_id="sess-w9-failsafe")
        runtime_dir = self.task_path / "run" / ".runtime"
        runtime_dir.parent.mkdir(parents=True, exist_ok=True)
        runtime_dir.write_text("lease 디렉터리 자리를 일반 파일이 점유", encoding="utf-8")

        result = self._run(["advance", str(self.task_path), "--row", "1"],
                           session_id="sess-w9-failsafe")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._row_status(1), "in_progress")
        self.assertTrue(runtime_dir.is_file(), "점유 파일이 그대로 남아야 한다")
        self.assertRegex(result.stderr,
                         r"ownership_claim_(skipped|failed)")

    # ── 4-b. ownership-tool 적재 자체가 불가능한 환경 → 예외 없이 경고만 ──
    def test_ownership_tool_import_failure_is_fail_safe(self):
        """C-9 — ownership-tool을 적재할 수 없어도 state-tool은 죽지 않는다."""
        with patch.dict(os.environ, {"OPAL_SESSION_ID": "sess-w9-noimport"}), \
                patch.object(ST_BASE, "_import_ownership_lease",
                             side_effect=ModuleNotFoundError("ownership_tool")):
            outcome = ST._claim_task_lease_if_needed(self.task_path)
        self.assertFalse(outcome["claimed"])
        self.assertEqual(outcome["warning"], "ownership_claim_failed")
        self.assertFalse(self._lease_file.exists())


class TestT138W9ActorSessionId(unittest.TestCase):
    """W-9 — run-log 4개 기록부의 actor.session_id 채움 (AC-27, run-log CONTRACT §58 선택 필드)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.task_path = pathlib.Path(self.tmp.name) / "tasks" / "138-w9-actor"
        self.task_path.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, args, session_id=None):
        env = dict(os.environ)
        env.pop("OPAL_SESSION_ID", None)
        if session_id is not None:
            env["OPAL_SESSION_ID"] = session_id
        return subprocess.run(
            [sys.executable, str(_TOOL_DIR / "state_tool.py"), *args],
            capture_output=True, text=True, env=env)

    def _events(self):
        events = []
        for segment in sorted((self.task_path / "run").glob("run-log-*.jsonl")):
            for line in segment.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))
        return events

    def _record_all(self, session_id):
        """4개 기록부를 모두 지나가는 최소 시나리오."""
        init = self._run(
            ["init", str(self.task_path), "--skill", "opds", "--mode", "agentic",
             "--task-title", "138 W-9 actor", "--run-log-mode", "shadow",
             "--rows-spec", _W9_ROWS_SPEC],
            session_id=session_id)                       # run.started 기록부
        self.assertEqual(init.returncode, 0, init.stderr)
        for args in (
            ["advance", str(self.task_path), "--row", "1"],          # state.changed
            ["log-event", str(self.task_path), "--event", "activity",
             "--kind", "decision", "--summary", "W-9 activity"],     # PM activity
            ["gate-request", str(self.task_path), "--gate-id", "g-w9",
             "--summary", "W-9 gate"],                               # gate.requested
        ):
            result = self._run(args, session_id=session_id)
            self.assertEqual(result.returncode, 0, f"{args}: {result.stderr}")
        return {e["event"]: e for e in self._events()}

    def test_session_id_filled_in_all_four_record_sites(self):
        """AC-27 — run.started/state.changed/activity/gate.requested 전부에 채워진다."""
        by_event = self._record_all("sess-w9-actor")
        for event_name in ("run.started", "state.changed", "activity", "gate.requested"):
            self.assertIn(event_name, by_event, f"{event_name} 사건이 기록되지 않았다: {list(by_event)}")
            self.assertEqual(
                by_event[event_name]["actor"]["session_id"], "sess-w9-actor",
                f"{event_name}의 actor.session_id가 OPAL_SESSION_ID 값이어야 한다")

    def test_session_id_stays_none_without_env(self):
        """회귀 — OPAL_SESSION_ID 부재 시 4개 기록부 모두 종전처럼 None이다(스키마 무변경)."""
        by_event = self._record_all(None)
        for event_name in ("run.started", "state.changed", "activity", "gate.requested"):
            self.assertIn(event_name, by_event)
            self.assertIsNone(by_event[event_name]["actor"]["session_id"],
                              f"{event_name}의 actor.session_id는 None이어야 한다")


class TestT132OppbStageEnumExtension(unittest.TestCase):
    """W-3 [G1] state-tool additive enum 확장 — TEST-SCENARIO S-6(AC-1, C-6).

    현재는 `--skill` choices에 "oppb"가 없고 STAGE_ENUM에 "P0"~"P5"가 없어
    신규 수용 테스트(test_t132_s6_*)가 RED(실패)한다. 기존 skill(opd/oppd/oppl)
    회귀 테스트(test_t132_s6_regression_*)는 W-3 적용 전에도 이미 PASS해야 하며,
    GREEN 이후에도 계속 PASS해야 한다(additive-only 검증 — 기존 분기 무변경).
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _new_task_path(self, name):
        p = self.tmpdir / name
        p.mkdir()
        return p

    def _round_trip_all_rows(self, task_path, row_count, mark_owners=None):
        """1..row_count까지 순서대로 advance→mark 전이를 `run.sh` subprocess로만
        수행한다(state.json 직접 편집 금지). 기존 왕복 관례(advance(row)→mark(row)를
        row_id 오름차순 반복)와 동일 순서를 따른다. `mark_owners`는
        {row_id: owner} 형태로, CLOSE 게이트가 요구하는 "사용자 확인" 행처럼
        mark 시 --owner가 필요한 행에만 사용한다(check_close_gate §2.16 G-13)."""
        mark_owners = mark_owners or {}
        for row_id in range(1, row_count + 1):
            code, stdout, stderr, data = _run070([
                "advance", str(task_path), "--row", str(row_id),
            ])
            self.assertEqual(
                code, 0,
                f"row{row_id} advance 실패(exit={code}): stdout={stdout!r} stderr={stderr!r}",
            )
            mark_args = ["mark", str(task_path), "--row", str(row_id), "--done"]
            owner = mark_owners.get(row_id)
            if owner:
                mark_args += ["--owner", owner]
            code, stdout, stderr, data = _run070(mark_args)
            self.assertEqual(
                code, 0,
                f"row{row_id} mark 실패(exit={code}): stdout={stdout!r} stderr={stderr!r}",
            )

    # ── 신규 수용: --skill oppb + P0~P5 (S-6 본체, RED) ──────────────────────

    def test_t132_s6_init_skill_oppb_accepts_p0_p5_rows(self):
        """[T132/S-6] `init --skill oppb --rows-spec <P0~P5 6행>` → exit 0, ok:true,
        rows[] 6행 전부 stage P0~P5 순서로 생성된다. 현재는 `--skill` choices에
        "oppb"가 없어 argparse usage error(exit 2)로 거부된다(정상 RED)."""
        task_path = self._new_task_path("s6_oppb_init")
        code, stdout, stderr, data = _run070([
            "init", str(task_path),
            "--skill", "oppb", "--mode", "agentic",
            "--task-title", "OPPB enum 확장 RED fixture",
            "--rows-spec", _OPPB_P0_P5_ROWS_SPEC,
        ])
        self.assertEqual(
            code, 0,
            f"RED: state-tool init --skill oppb 실패 — W-3 enum 확장 전 정상 실패. "
            f"exit={code}\nstdout={stdout!r}\nstderr={stderr!r}",
        )
        self.assertTrue(data.get("ok"), f"init 응답 ok 아님: {data}")
        self.assertTrue((task_path / "state.json").exists(), "state.json 미생성")

        state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state.get("skill"), "oppb", f"skill 필드 불일치: {state.get('skill')!r}")
        rows = state.get("rows") or []
        self.assertEqual(len(rows), 6, f"rows[] 6행이어야 함: {len(rows)}행")
        self.assertEqual(
            [r.get("stage") for r in rows],
            ["P0", "P1", "P2", "P3", "P4", "P5"],
            f"rows[].stage 순서가 P0~P5가 아님: {[r.get('stage') for r in rows]}",
        )

    def test_t132_s6_oppb_advance_mark_round_trip_all_stages(self):
        """[T132/S-6] `--skill oppb` P0~P5 6행 전체를 advance→mark 왕복시켜
        전 행이 done으로 전이되고 validate 위반이 없는지 확인한다. init 단계부터
        RED다(--skill oppb 미등록)."""
        task_path = self._new_task_path("s6_oppb_roundtrip")
        code, stdout, stderr, data = _run070([
            "init", str(task_path),
            "--skill", "oppb", "--mode", "agentic",
            "--rows-spec", _OPPB_P0_P5_ROWS_SPEC,
        ])
        self.assertEqual(
            code, 0,
            f"RED: state-tool init --skill oppb 실패(왕복 전제 조건) — "
            f"exit={code}\nstdout={stdout!r}\nstderr={stderr!r}",
        )

        self._round_trip_all_rows(task_path, 6)

        state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        rows = state.get("rows") or []
        self.assertTrue(
            all(r.get("status") == "done" for r in rows),
            f"P0~P5 전 행이 done으로 전이되지 않음: {[(r.get('stage'), r.get('status')) for r in rows]}",
        )

        code, stdout, stderr, data = _run070(["validate", str(task_path)])
        self.assertEqual(
            code, 0,
            f"validate 실패(왕복 후 정합성 위반) — exit={code}\nstdout={stdout!r}\nstderr={stderr!r}",
        )
        self.assertEqual(
            data.get("violations"), [],
            f"P0~P5 왕복 후 violations가 비어있지 않음: {data.get('violations')}",
        )

    # ── STAGE_ENUM 독립 검증: 기존 skill(opp)에 add-row --stage P0 ──────────

    def test_t132_s6_stage_p0_rejected_independent_of_skill_oppb(self):
        """[T132/S-6] STAGE_ENUM 확장은 `--skill oppb`와 독립적으로도 검증되어야
        한다 — 기존 skill(`opp`)에 `add-row --stage P0`를 시도해도 현재는
        STAGE_ENUM에 P0가 없어 거부된다(TestOpddEnumDrift의 DICT 검증과 동일 패턴,
        정상 RED)."""
        task_path = self._new_task_path("s6_stage_p0_add_row")
        code, stdout, stderr, data = _run070([
            "init", str(task_path),
            "--skill", "opp", "--mode", "interactive",
            "--rows-spec", json.dumps([
                {"stage": "TASK",  "item": "작업"},
                {"stage": "CLOSE", "item": "DONE.md 생성"},
            ]),
        ])
        self.assertEqual(code, 0, f"사전 init(opp) 실패: {stdout!r}")

        code, stdout, stderr, data = _run070([
            "add-row", str(task_path),
            "--after", "1", "--stage", "P0", "--item", "P0 작업",
        ])
        self.assertEqual(
            code, 0,
            f"RED: add-row --stage P0 실패 — STAGE_ENUM 확장 전 정상 실패. "
            f"exit={code}\nstdout={stdout!r}\nstderr={stderr!r}",
        )
        self.assertTrue(data.get("ok"), f"add-row 응답 ok 아님: {data}")

    # ── 기존 무변경 회귀: opd·oppd·oppl 왕복 + 기존 stage 값 수용 ────────────

    def _assert_existing_skill_round_trip_unchanged(self, skill):
        task_path = self._new_task_path(f"s6_regress_{skill}")
        code, stdout, stderr, data = _run070([
            "init", str(task_path),
            "--skill", skill, "--mode", "agentic",
            "--rows-spec", _EXISTING_SKILL_REGRESSION_ROWS_SPEC,
        ])
        self.assertEqual(
            code, 0,
            f"기존 skill '{skill}' init이 W-3 enum 확장 전인데도 실패함(회귀) — "
            f"exit={code}\nstdout={stdout!r}\nstderr={stderr!r}",
        )
        self.assertTrue(data.get("ok"), f"'{skill}' init 응답 ok 아님: {data}")

        state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        rows = state.get("rows") or []
        self.assertEqual(
            [r.get("stage") for r in rows],
            _EXISTING_SKILL_REGRESSION_STAGES,
            f"'{skill}' 기존 stage 값 수용 실패: {[r.get('stage') for r in rows]}",
        )

        self._round_trip_all_rows(
            task_path, _EXISTING_SKILL_REGRESSION_ROW_COUNT,
            mark_owners={_EXISTING_SKILL_REGRESSION_CONFIRM_ROW_ID: "user"},
        )

        final_state = json.loads((task_path / "state.json").read_text(encoding="utf-8"))
        final_rows = final_state.get("rows") or []
        self.assertTrue(
            all(r.get("status") == "done" for r in final_rows),
            f"'{skill}' 왕복 후 일부 행이 done 아님(회귀): "
            f"{[(r.get('stage'), r.get('status')) for r in final_rows]}",
        )

    def test_t132_s6_regression_opd_round_trip_unchanged(self):
        """[T132/S-6] 기존 skill `opd` — init·advance·mark 왕복과 기존 stage 값
        수용이 W-3 적용 전후 무변경이어야 한다(회귀 가드, W-3 적용 전에도 PASS)."""
        self._assert_existing_skill_round_trip_unchanged("opd")

    def test_t132_s6_regression_oppd_round_trip_unchanged(self):
        """[T132/S-6] 기존 skill `oppd` — init·advance·mark 왕복과 기존 stage 값
        수용이 W-3 적용 전후 무변경이어야 한다(회귀 가드, W-3 적용 전에도 PASS)."""
        self._assert_existing_skill_round_trip_unchanged("oppd")

    def test_t132_s6_regression_oppl_round_trip_unchanged(self):
        """[T132/S-6] 기존 skill `oppl` — init·advance·mark 왕복과 기존 stage 값
        수용이 W-3 적용 전후 무변경이어야 한다(회귀 가드, W-3 적용 전에도 PASS)."""
        self._assert_existing_skill_round_trip_unchanged("oppl")


class TestT132OppbSpecValidateSkillEnum(unittest.TestCase):
    """W-3 보강 — validate_pipeline_spec() 로컬 skill_enum에 "oppb" 누락 RED.

    PM이 W-3 GREEN 완료 후 실측으로 잡은 결함: state_tool_parts/guards.py:424의
    skill_enum(로컬 상수)에는 "oppb"가 없어 `spec-validate`(및 이를 거치는
    `init --rows-from`)가 spec_skill_invalid로 거부한다. `--skill` argparse
    choices(별도 목록, GREEN 완료)와는 독립적으로 검증되어야 한다.
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_spec(self, name, spec_dict):
        p = self.tmpdir / name
        p.write_text(json.dumps(spec_dict, ensure_ascii=False), encoding="utf-8")
        return p

    # ── 신규 수용(RED): oppb pipeline.json spec-validate ok:true ────────────

    def test_t132_oppb_spec_validate_accepts_skill(self):
        """[T132/W-3 보강] `skill: "oppb"` + P0~P5 task_steps spec →
        `spec-validate` exit 0, ok:true, violations_count 0. 지금은
        validate_pipeline_spec() 로컬 skill_enum에 "oppb"가 없어
        spec_skill_invalid violation으로 exit 1(정상 RED)."""
        spec_path = self._write_spec("oppb.json", _OPPB_MIN_PIPELINE_SPEC)
        code, stdout, stderr, data = _run070(["spec-validate", str(spec_path)])
        self.assertEqual(
            code, 0,
            f"RED: oppb spec-validate가 실패함 — skill_enum에 'oppb' 미등록. "
            f"exit={code}\nstdout={stdout!r}\nstderr={stderr!r}",
        )
        self.assertTrue(data.get("ok"), f"spec-validate 응답 ok 아님: {data}")
        self.assertEqual(
            data.get("violations_count"), 0,
            f"oppb spec인데 violations 발생: {data.get('violations')}",
        )
        codes = [v.get("code") for v in (data.get("violations") or [])]
        self.assertNotIn(
            "spec_skill_invalid", codes,
            f"RED: spec_skill_invalid가 남아있음(skill_enum 미확장): {data.get('violations')}",
        )

    # ── 기존 무변경 회귀(지금 통과해야 함) ───────────────────────────────────

    def test_t132_regression_existing_skill_opd_spec_validate_unchanged(self):
        """[회귀] 기존 skill `opd`(실 pipeline.json 전문 인용 fixture) spec-validate
        는 W-3 적용 전후 무변경으로 계속 ok:true여야 한다."""
        spec_path = self._write_spec("opd.json", _OPD_PIPELINE_SPEC)
        code, stdout, stderr, data = _run070(["spec-validate", str(spec_path)])
        self.assertEqual(code, 0, f"opd spec-validate 실패(회귀): stdout={stdout!r}")
        self.assertTrue(data.get("ok"), f"opd spec-validate ok 아님(회귀): {data}")
        self.assertEqual(data.get("violations_count"), 0)

    def _assert_existing_skill_variant_still_valid(self, skill):
        spec = _deepcopy_json(_OPD_PIPELINE_SPEC)
        spec["skill"] = skill
        spec_path = self._write_spec(f"{skill}.json", spec)
        code, stdout, stderr, data = _run070(["spec-validate", str(spec_path)])
        self.assertEqual(code, 0, f"'{skill}' spec-validate 실패(회귀): stdout={stdout!r}")
        self.assertTrue(data.get("ok"), f"'{skill}' spec-validate ok 아님(회귀): {data}")
        codes = [v.get("code") for v in (data.get("violations") or [])]
        self.assertNotIn(
            "spec_skill_invalid", codes,
            f"'{skill}'가 기존 skill_enum에 있는데 spec_skill_invalid 발생(회귀): {data.get('violations')}",
        )

    def test_t132_regression_existing_skill_oppd_still_valid(self):
        """[회귀] 기존 skill `oppd`는 spec-validate에서 계속 spec_skill_invalid 없이
        통과해야 한다(skill_enum 확장은 additive-only)."""
        self._assert_existing_skill_variant_still_valid("oppd")

    def test_t132_regression_existing_skill_oppl_still_valid(self):
        """[회귀] 기존 skill `oppl`은 spec-validate에서 계속 spec_skill_invalid 없이
        통과해야 한다(skill_enum 확장은 additive-only)."""
        self._assert_existing_skill_variant_still_valid("oppl")

    def test_t132_regression_unknown_skill_still_rejected(self):
        """[회귀] 존재하지 않는 skill(`nope`)은 계속 spec_skill_invalid로
        거부되어야 한다(skill_enum 확장이 검증 자체를 무력화하지 않음)."""
        spec = _deepcopy_json(_OPD_PIPELINE_SPEC)
        spec["skill"] = "nope"
        spec_path = self._write_spec("nope.json", spec)
        code, stdout, stderr, data = _run070(["spec-validate", str(spec_path)])
        self.assertEqual(code, 1, f"미지정 skill인데 spec-validate가 exit 0(회귀 실패): stdout={stdout!r}")
        self.assertFalse(data.get("ok"), f"미지정 skill인데 ok=true(회귀 실패): {data}")
        codes = [v.get("code") for v in (data.get("violations") or [])]
        self.assertIn(
            "spec_skill_invalid", codes,
            f"미지정 skill 'nope'인데 spec_skill_invalid 없음(회귀 실패): {data.get('violations')}",
        )
