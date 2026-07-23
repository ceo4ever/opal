"""
@header {
  "module": "test_brain_tool",
  "layer": "test",
  "domain": "opal-brain",
  "description": "brain-tool 단위 테스트 — 10 서브커맨드 happy-path + ERROR_CODES 주요 14종 + 동적 타입 로드 + analyze/ingest-scan + 027(term 동적로드·draft search 필터·lint term_duplicate/alias_collision). tmp_path 기반 격리 실행. mock 금지 — 실제 brain_tool.py를 import 호출하는 진짜 테스트. [053] validate_frontmatter 링크필드(related) 거부/통과 케이스 + add-page --related 지정/미지정 케이스 추가. [071] RED-first — add-page 미실체 마커 거부 게이트(--body-file/--force/--note, speculative_content)·lint speculative kind·draft-term 불변(M-3) 계약 테스트(TestSpeculativeGate071, TS-201~209). 구현(brain_tool.py) 없이 작성된 RED 테스트 — GREEN은 op-dev-execute 담당.",
  "task": "027",
  "exports": [
    "TestInit", "TestAddPage", "TestIndex", "TestLog",
    "TestSearch", "TestSyncHeader", "TestLint", "TestValidate",
    "TestErrorCodes", "TestDynamicPageTypes", "TestAnalyze", "TestIngestScan",
    "TestTermDraft027", "TestTermLint027", "TestSpeculativeGate071"
  ]
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 제약
# - [MUST] TASK §제약: 실제 brain_tool.py를 import/subprocess로 호출하는 진짜 테스트 (mock 금지).
# - [MUST] TASK §제약: tmp_path 기반 — 실제 프로젝트 .opal/brain 오염 금지.
# - [MUST] @header 규칙: @header 주석 블록 작성 (Python = snake_case 파일, docs/CONVENTIONS.md).
# - KST 타임스탬프(get_kst_datetime)는 date.js subprocess를 사용하므로 unittest.mock.patch 허용
#   (외부 Node.js 의존성 격리 목적 — 코드 흐름 자체는 실제 brain_tool.py 경로를 타도록 유지).
# ─────────────────────────────────────────────────────────────────────────────

import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

# brain_tool.py를 직접 import (state_tool 테스트 패턴 준용)
_TOOL_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_TOOL_DIR))
import brain_tool as BT  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# 공통 상수·헬퍼
# ─────────────────────────────────────────────────────────────────────────────

_FIXED_DATETIME = "2026-06-10 12:00"
_FIXED_DATE = "2026-06-10"


def _mock_kst():
    """get_kst_datetime을 고정 KST 문자열로 패치하는 컨텍스트."""
    return patch.object(BT, "get_kst_datetime", return_value=_FIXED_DATETIME)


def make_args(**kwargs):
    """argparse Namespace 유사 객체 생성 헬퍼 (state_tool 테스트 패턴)."""
    defaults = {
        # init
        "brain_path": ".",
        "force": False,
        "types": None,
        # add-page / search type filter (None = 필터 없음)
        "path": "my-page",
        "type": None,
        "title": "테스트 페이지",
        "tags": None,
        "sources": None,
        "related": None,
        # add-page 미실체 게이트 (071) — body_file 미지정 시 기존 템플릿 본문 경로(하위호환)
        "note": None,
        "body_file": None,
        # log
        "op": "init",
        "summary": "테스트 요약",
        "new": None,
        "updated": None,
        # search
        "query": "",
        "tag": None,
        "limit": None,
        "include_draft": False,
        # sync-header
        "scope": None,
        "page": None,
        # ingest-scan
        "source": "all",
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class BrainTestCase(unittest.TestCase):
    """임시 디렉토리 기반 테스트 베이스.

    [MUST] 실제 프로젝트 .opal/brain 오염 금지 — tmpdir 내 brain 경로만 사용.
    KST 타임스탬프는 Node.js date.js에 의존하므로 모든 테스트에서 _mock_kst()로 격리한다.
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        # brain 경로: <tmpdir>/.opal/brain (resolve_brain_path 규칙과 동형)
        self.brain_root = self.tmpdir / ".opal" / "brain"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ── 공통 호출 도우미 ────────────────────────────────────────────────────

    def _call(self, fn, args):
        """brain_tool 명령 함수를 호출 → (exit_code, result_dict) 반환.

        ok()는 print 후 반환, err()는 SystemExit를 일으키므로 둘 다 처리한다.
        """
        out = io.StringIO()
        exit_code = 0
        with redirect_stdout(out):
            try:
                fn(args)
            except SystemExit as e:
                exit_code = int(e.code) if e.code is not None else 0
        output = out.getvalue().strip()
        result = json.loads(output) if output else {}
        return exit_code, result

    def _init(self, force=False):
        """brain init 헬퍼 — tmpdir 기반 brain_path 사용."""
        with _mock_kst():
            args = make_args(brain_path=str(self.tmpdir), force=force)
            exit_code, result = self._call(BT.cmd_init, args)
        self.assertEqual(exit_code, 0, f"init 실패: {result}")
        return result

    def _add_page(self, name="test-page", page_type="concept", title="테스트 개념",
                  tags=None, sources=None, related=None):
        """add-page 헬퍼."""
        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                path=name, type=page_type, title=title,
                tags=tags, sources=sources, related=related,
            )
            exit_code, result = self._call(BT.cmd_add_page, args)
        return exit_code, result

    def _write_term_page(self, name, title, status="active", aliases=None, sources="[task:027]"):
        """term 페이지를 직접 파일로 생성한다 (add-page 우회 — status/sources 제어용). 027 공통 헬퍼."""
        page_dir = self.brain_root / "pages" / "term"
        page_dir.mkdir(parents=True, exist_ok=True)
        aliases_yaml = ""
        if aliases:
            aliases_list = "\n".join(f"  - {a}" for a in aliases)
            aliases_yaml = f"aliases:\n{aliases_list}\n"
        content = (
            f"---\n"
            f"type: term\n"
            f"title: {title}\n"
            f"{aliases_yaml}"
            f"tags: []\n"
            f"sources: {sources}\n"
            f"related: []\n"
            f"created: 2026-06-17\n"
            f"updated: 2026-06-17\n"
            f"status: {status}\n"
            f"---\n\n"
            f"업무 의미 설명.\n"
        )
        (page_dir / f"{name}.md").write_text(content, encoding="utf-8")

    def _err_code(self, fn, args):
        """에러 응답의 error 코드 추출 헬퍼."""
        out = io.StringIO()
        with redirect_stdout(out):
            try:
                fn(args)
            except SystemExit:
                pass
        output = out.getvalue().strip()
        return json.loads(output).get("error") if output else None


# ═════════════════════════════════════════════════════════════════════════════
# 1. init — happy-path
# ═════════════════════════════════════════════════════════════════════════════

class TestInit(BrainTestCase):
    """init 서브커맨드 — 골격 생성 + SCHEMA/index/log 파일 검증."""

    def test_init_happy_path_ok_true(self):
        """init: JSON ok=true + command='init' 반환."""
        result = self._init()
        self.assertTrue(result["ok"])
        self.assertEqual(result["command"], "init")
        self.assertTrue(result["schema_written"])

    def test_init_creates_schema(self):
        """init: SCHEMA.md 생성 확인."""
        self._init()
        self.assertTrue((self.brain_root / "SCHEMA.md").exists())

    def test_init_creates_index_and_log(self):
        """init: index.md 와 log.md 생성 확인."""
        self._init()
        self.assertTrue((self.brain_root / "index.md").exists())
        self.assertTrue((self.brain_root / "log.md").exists())

    def test_init_creates_page_dirs(self):
        """init: pages/{entity,concept,flow,synthesis}/ + sources/ 디렉토리 생성."""
        self._init()
        for d in BT.BRAIN_DIRS:
            self.assertTrue((self.brain_root / d).exists(), f"디렉토리 부재: {d}")

    def test_init_created_list_contains_brain_root(self):
        """init: 응답 created 리스트에 brain_root 경로 포함.
        macOS /var → /private/var symlink 때문에 resolve()로 비교한다.
        """
        result = self._init()
        # brain_tool.py 는 pathlib.Path.resolve()로 경로를 기록하므로 동일하게 resolve
        brain_root_resolved = str(self.brain_root.resolve())
        created_resolved = [str(pathlib.Path(p).resolve()) for p in result["created"]]
        self.assertIn(brain_root_resolved, created_resolved)

    def test_init_force_reinitializes(self):
        """init --force: 이미 초기화된 brain을 재초기화."""
        self._init()
        result = self._init(force=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["force"])


# ═════════════════════════════════════════════════════════════════════════════
# 2. add-page — happy-path (entity·concept)
# ═════════════════════════════════════════════════════════════════════════════

class TestAddPage(BrainTestCase):
    """add-page 서브커맨드 — entity·concept 페이지 생성 + index 자동 등록."""

    def setUp(self):
        super().setUp()
        self._init()

    def test_add_concept_page_ok_true(self):
        """add-page concept: ok=true + indexed=true 반환."""
        exit_code, result = self._add_page(
            name="pipeline-design", page_type="concept", title="파이프라인 설계")
        self.assertEqual(exit_code, 0, f"add-page 실패: {result}")
        self.assertTrue(result["ok"])
        self.assertTrue(result["indexed"])

    def test_add_entity_page_ok_true(self):
        """add-page entity: ok=true + type='entity' 반환."""
        exit_code, result = self._add_page(
            name="state-tool", page_type="entity", title="state-tool 엔티티")
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["type"], "entity")

    def test_add_page_file_created(self):
        """add-page: pages/{type}/<name>.md 파일 생성 확인."""
        self._add_page(name="my-concept", page_type="concept", title="테스트")
        page_file = self.brain_root / "pages" / "concept" / "my-concept.md"
        self.assertTrue(page_file.exists())

    def test_add_page_frontmatter_valid(self):
        """add-page: 생성된 페이지의 frontmatter 필수 키 완비 확인."""
        self._add_page(name="fm-test", page_type="concept", title="FM 검증")
        page_file = self.brain_root / "pages" / "concept" / "fm-test.md"
        text = page_file.read_text(encoding="utf-8")
        fm, _ = BT.parse_frontmatter(text)
        self.assertIsNotNone(fm)
        for key in BT.REQUIRED_FRONTMATTER:
            self.assertIn(key, fm, f"필수 키 누락: {key}")

    def test_add_page_with_tags(self):
        """add-page --tags: tags frontmatter에 반영 확인."""
        self._add_page(name="tagged-page", page_type="concept",
                       title="태그 테스트", tags="tool,pipeline")
        page_file = self.brain_root / "pages" / "concept" / "tagged-page.md"
        text = page_file.read_text(encoding="utf-8")
        fm, _ = BT.parse_frontmatter(text)
        self.assertIn("tool", fm.get("tags", []))
        self.assertIn("pipeline", fm.get("tags", []))

    def test_add_page_updates_index(self):
        """add-page: 완료 후 index.md에 새 페이지 제목이 반영됨."""
        self._add_page(name="index-check", page_type="concept", title="인덱스 확인")
        index_text = (self.brain_root / "index.md").read_text(encoding="utf-8")
        self.assertIn("index-check", index_text)

    def test_add_flow_page(self):
        """add-page flow: 정상 생성 확인."""
        exit_code, result = self._add_page(name="my-flow", page_type="flow",
                                            title="흐름 페이지")
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])

    def test_add_page_with_related(self):
        """053 R-4: add-page --related a,b: related frontmatter에 평탄 리스트로 반영 확인."""
        exit_code, result = self._add_page(name="related-page", page_type="concept",
                                            title="related 테스트", related="state-tool,brain-tool")
        self.assertEqual(exit_code, 0, f"add-page 실패: {result}")
        page_file = self.brain_root / "pages" / "concept" / "related-page.md"
        text = page_file.read_text(encoding="utf-8")
        fm, _ = BT.parse_frontmatter(text)
        self.assertEqual(fm.get("related"), ["state-tool", "brain-tool"])

    def test_add_page_without_related_keeps_default(self):
        """053 R-4: --related 미지정 시 템플릿 기본값(related: []) 유지(기존 동작 불변)."""
        self._add_page(name="no-related-page", page_type="concept", title="related 미지정 테스트")
        page_file = self.brain_root / "pages" / "concept" / "no-related-page.md"
        text = page_file.read_text(encoding="utf-8")
        fm, _ = BT.parse_frontmatter(text)
        self.assertEqual(fm.get("related"), [], f"related 미지정 시 템플릿 기본값이 변경됨: {fm.get('related')}")

    def test_add_synthesis_page(self):
        """add-page synthesis: 정상 생성 확인."""
        exit_code, result = self._add_page(name="my-synthesis", page_type="synthesis",
                                            title="합성 페이지")
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])


# ═════════════════════════════════════════════════════════════════════════════
# 3. index — happy-path
# ═════════════════════════════════════════════════════════════════════════════

class TestIndex(BrainTestCase):
    """index 서브커맨드 — pages/ 스캔 + index.md 재생성."""

    def setUp(self):
        super().setUp()
        self._init()

    def test_index_empty_brain_ok_true(self):
        """index: 페이지 없는 brain에서 ok=true + pages_scanned=0."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            exit_code, result = self._call(BT.cmd_index, args)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["pages_scanned"], 0)
        self.assertTrue(result["index_written"])

    def test_index_with_pages_scanned_count(self):
        """index: 페이지 추가 후 pages_scanned=N 반환."""
        self._add_page("page-a", "concept", "A")
        self._add_page("page-b", "entity", "B")
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            exit_code, result = self._call(BT.cmd_index, args)
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["pages_scanned"], 2)

    def test_index_renders_category_headers(self):
        """index: index.md에 5개 카테고리 헤더(도메인/개념/엔티티/흐름/합성) 포함."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            self._call(BT.cmd_index, args)
        index_text = (self.brain_root / "index.md").read_text(encoding="utf-8")
        for cat in BT.CATEGORY_ORDER:
            self.assertIn(f"## {cat}", index_text)

    def test_index_renders_page_entries(self):
        """index: 등록된 페이지가 index.md 해당 카테고리 섹션에 표시됨."""
        self._add_page("my-concept-x", "concept", "개념 X")
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            self._call(BT.cmd_index, args)
        index_text = (self.brain_root / "index.md").read_text(encoding="utf-8")
        self.assertIn("my-concept-x", index_text)
        self.assertIn("개념 X", index_text)


# ═════════════════════════════════════════════════════════════════════════════
# 4. log — happy-path
# ═════════════════════════════════════════════════════════════════════════════

class TestLog(BrainTestCase):
    """log 서브커맨드 — log.md append-only 기록."""

    def setUp(self):
        super().setUp()
        self._init()

    def test_log_init_op_ok_true(self):
        """log --op init: ok=true + logged=true 반환."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             op="init", summary="brain 초기화")
            exit_code, result = self._call(BT.cmd_log, args)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertTrue(result["logged"])

    def test_log_ingest_op_ok_true(self):
        """log --op ingest: ok=true 반환."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             op="ingest", summary="ingest 테스트")
            exit_code, result = self._call(BT.cmd_log, args)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])

    def test_log_appends_to_log_md(self):
        """log: log.md에 엔트리가 append됨."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             op="init", summary="append 확인 테스트")
            self._call(BT.cmd_log, args)
        log_text = (self.brain_root / "log.md").read_text(encoding="utf-8")
        self.assertIn("append 확인 테스트", log_text)

    def test_log_timestamp_in_response(self):
        """log: 응답 timestamp 필드가 KST 형식으로 반환됨."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             op="lint", summary="lint 실행")
            _, result = self._call(BT.cmd_log, args)
        self.assertIn("timestamp", result)
        self.assertEqual(result["timestamp"], _FIXED_DATETIME)

    def test_log_with_new_and_updated(self):
        """log --new·--updated: log.md에 신규·갱신 항목 목록 포함."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             op="ingest", summary="신규·갱신 테스트",
                             new="page-a,page-b", updated="page-c")
            self._call(BT.cmd_log, args)
        log_text = (self.brain_root / "log.md").read_text(encoding="utf-8")
        self.assertIn("[[page-a]]", log_text)
        self.assertIn("[[page-b]]", log_text)
        self.assertIn("[[page-c]]", log_text)

    def test_log_multiple_appends_accumulate(self):
        """log: 여러 번 호출 시 log.md에 누적 저장됨 (append-only)."""
        for i in range(3):
            with _mock_kst():
                args = make_args(brain_path=str(self.brain_root),
                                 op="query", summary=f"쿼리 {i}")
                self._call(BT.cmd_log, args)
        log_text = (self.brain_root / "log.md").read_text(encoding="utf-8")
        self.assertEqual(log_text.count("쿼리"), 3)


# ═════════════════════════════════════════════════════════════════════════════
# 5. search — happy-path
# ═════════════════════════════════════════════════════════════════════════════

class TestSearch(BrainTestCase):
    """search 서브커맨드 — 제목·태그·본문 검색."""

    def setUp(self):
        super().setUp()
        self._init()
        # 검색 대상 페이지 2개 추가
        self._add_page("state-tool", "entity", "state-tool 엔티티", tags="tool,pipeline")
        self._add_page("brain-design", "concept", "brain 설계 결정", tags="design")

    def test_search_by_title_ok_true(self):
        """search: 제목 키워드 매칭 → ok=true + matches 반환."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root), query="state-tool")
            exit_code, result = self._call(BT.cmd_search, args)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertIn("matches", result)

    def test_search_finds_relevant_page(self):
        """search: 제목 키워드로 해당 페이지 반환.
        type 필터 없이 검색해야 concept 페이지도 포함된다.
        """
        with _mock_kst():
            # make_args 기본값 type="entity"를 None으로 재정의
            args = make_args(brain_path=str(self.brain_root), query="brain", type=None)
            _, result = self._call(BT.cmd_search, args)
        titles = [m["title"] for m in result.get("matches", [])]
        self.assertTrue(
            any("brain" in t.lower() for t in titles),
            f"'brain' 포함 제목 없음: {titles}"
        )

    def test_search_no_match_returns_empty(self):
        """search: 매칭 없는 쿼리 → ok=true + matches=[] 반환."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             query="존재하지않는쿼리xyz")
            exit_code, result = self._call(BT.cmd_search, args)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["matches"], [])

    def test_search_by_tag_filter(self):
        """search --tag: 특정 태그를 가진 페이지만 반환."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             query="tool", tag="pipeline")
            _, result = self._call(BT.cmd_search, args)
        # pipeline 태그는 state-tool 페이지에만 있음
        for m in result.get("matches", []):
            self.assertNotIn("brain", m["title"].lower())

    def test_search_by_type_filter(self):
        """search --type: 특정 타입의 페이지만 반환."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             query="tool", type="entity")
            _, result = self._call(BT.cmd_search, args)
        for m in result.get("matches", []):
            self.assertEqual(m["type"], "entity")

    def test_search_limit(self):
        """search --limit: 결과 수 제한 확인."""
        # 여러 페이지 추가
        for i in range(5):
            self._add_page(f"extra-page-{i}", "concept", f"추가 페이지 {i}")
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             query="페이지", limit=2)
            _, result = self._call(BT.cmd_search, args)
        self.assertLessEqual(len(result.get("matches", [])), 2)

    # ── 025: 공백 무시 매칭 신규 테스트 ────────────────────────────────────────

    def test_norm_unit(self):
        """S-1: _norm 헬퍼 — 공백류 제거 + 소문자화 (TS-001, R1).
        _norm 이 없으면 스킵 (구현 전 헬퍼 미존재 시 RED 의미).
        """
        norm = getattr(BT, "_norm", None)
        if norm is None:
            self.skipTest("_norm 헬퍼 미구현 — Step 2 구현 후 활성화")
        self.assertEqual(norm("자동 취소"), "자동취소")
        self.assertEqual(norm("자동\t취소"), "자동취소")
        # 전각 공백 (U+3000) — Python str.split()이 공백류로 처리
        self.assertEqual(norm("자동　취소"), "자동취소")
        self.assertEqual(norm("자동취소"), "자동취소")
        self.assertEqual(norm("Auto Cancel"), "autocancel")

    def test_search_equiv_pair(self):
        """S-3: 등가 쌍 — "자동 취소" ≡ "자동취소" 동일 page 집합 반환 (TS-004, R4, RED 대상).
        픽스처: 제목에 등가 복합명사를 심은 페이지 2종.
        """
        # 등가 픽스처 추가 — 공백 포함 제목과 공백 없는 제목
        self._add_page("auto-cancel-a", "concept", "선정 자동 취소 정책")
        self._add_page("auto-cancel-b", "concept", "선정자동취소 정책")

        with _mock_kst():
            args_space = make_args(brain_path=str(self.brain_root),
                                   query="자동 취소", type=None)
            _, res_space = self._call(BT.cmd_search, args_space)
            args_nospace = make_args(brain_path=str(self.brain_root),
                                     query="자동취소", type=None)
            _, res_nospace = self._call(BT.cmd_search, args_nospace)

        pages_space = {m["page"] for m in res_space.get("matches", [])}
        pages_nospace = {m["page"] for m in res_nospace.get("matches", [])}
        self.assertEqual(
            pages_space, pages_nospace,
            f"등가 쌍 불일치:\n  '자동 취소' → {pages_space}\n  '자동취소'  → {pages_nospace}"
        )

    def test_search_equiv_triple(self):
        """S-4: 3원 등가 — "선정 자동 취소" ≡ "선정자동취소" ≡ "선정자동 취소" (TS-005, R4, RED 대상)."""
        self._add_page("auto-cancel-c", "concept", "선정 자동 취소 가이드라인")
        self._add_page("auto-cancel-d", "concept", "선정자동취소 가이드라인")

        with _mock_kst():
            def search(q):
                _, r = self._call(BT.cmd_search,
                                  make_args(brain_path=str(self.brain_root),
                                            query=q, type=None))
                return {m["page"] for m in r.get("matches", [])}

            pages_a = search("선정 자동 취소")
            pages_b = search("선정자동취소")
            pages_c = search("선정자동 취소")

        self.assertEqual(pages_a, pages_b,
                         f"3원 등가 불일치 a≠b: {pages_a} vs {pages_b}")
        self.assertEqual(pages_b, pages_c,
                         f"3원 등가 불일치 b≠c: {pages_b} vs {pages_c}")

    def test_search_asymmetric(self):
        """S-5: 비대칭 — 짧은 쿼리 넓게/긴 쿼리 좁게 (TS-006, R4 비대칭, RED 대상).
        짧은복합어 페이지("자동취소")와 긴복합어 페이지("선정자동취소")가 존재할 때:
          - "자동취소" → 두 페이지 모두 매칭
          - "선정자동취소" → 긴 페이지만 매칭, 짧은 페이지 미매칭
        """
        _, res_short_pg = self._add_page("short-ac", "concept", "자동취소")
        _, res_long_pg = self._add_page("long-ac", "concept", "선정자동취소")
        short_page = res_short_pg.get("page", "")
        long_page = res_long_pg.get("page", "")

        with _mock_kst():
            _, res_short_q = self._call(BT.cmd_search,
                                        make_args(brain_path=str(self.brain_root),
                                                  query="자동취소", type=None))
            _, res_long_q = self._call(BT.cmd_search,
                                       make_args(brain_path=str(self.brain_root),
                                                 query="선정자동취소", type=None))

        pages_short_q = {m["page"] for m in res_short_q.get("matches", [])}
        pages_long_q = {m["page"] for m in res_long_q.get("matches", [])}

        # 짧은 쿼리 → 두 페이지 모두 포함 (넓게)
        self.assertIn(short_page, pages_short_q,
                      "짧은 쿼리 '자동취소'가 짧은 페이지를 못 잡음")
        self.assertIn(long_page, pages_short_q,
                      "짧은 쿼리 '자동취소'가 긴 페이지를 못 잡음 (비대칭 넓은 방향)")
        # 긴 쿼리 → 짧은 페이지 미매칭 (좁게)
        self.assertNotIn(short_page, pages_long_q,
                         "긴 쿼리 '선정자동취소'가 짧은 페이지를 잡음 (비대칭 좁은 방향 위반)")

    def test_snippet_keeps_original_spacing(self):
        """S-6: 스니펫 원문 노출 — 공백 포함 원문 그대로 반환 (TS-003, R3, RED 대상).
        body에 "선정 자동 취소 가능" 원문 포함 페이지, "자동 취소" 쿼리로 검색 시
        snippet에 원문(공백 포함) "자동 취소"가 포함되어야 한다.
        """
        _, res_pg = self._add_page("body-fixture", "concept", "본문 정규화 검증")
        page_path = pathlib.Path(res_pg.get("page", ""))
        # 본문에 원문 복합명사 삽입 (tmpdir 격리 — 프로덕션 .opal/brain/ 불변)
        page_path.write_text(
            page_path.read_text(encoding="utf-8").replace(
                "\n\n",
                "\n\n이 정책은 선정 자동 취소 가능 조건을 명시한다.\n\n",
                1
            ),
            encoding="utf-8"
        )

        with _mock_kst():
            _, result = self._call(BT.cmd_search,
                                   make_args(brain_path=str(self.brain_root),
                                             query="자동 취소", type=None))

        matches = result.get("matches", [])
        body_match = next(
            (m for m in matches if "body-fixture" in m.get("page", "")), None
        )
        self.assertIsNotNone(body_match,
                             "body-fixture 페이지가 '자동 취소' 검색에 매칭되지 않음")
        snippet = body_match.get("snippet", "")
        self.assertIn("자동 취소", snippet,
                      f"스니펫에 원문 '자동 취소'(공백 포함)가 없음: '{snippet}'")

    def test_search_schema_unchanged(self):
        """S-9: JSON 출력 계약 불변 — matches[] 키 5종 + total + ok=true (TS-009, H-5)."""
        self._add_page("schema-check", "concept", "스키마 검증 페이지")

        with _mock_kst():
            _, result = self._call(BT.cmd_search,
                                   make_args(brain_path=str(self.brain_root),
                                             query="스키마", type=None))

        self.assertTrue(result.get("ok"), "ok=true 아님")
        self.assertIn("total", result, "top-level 'total' 키 없음")
        self.assertIn("query", result, "top-level 'query' 키 없음")
        matches = result.get("matches", [])
        self.assertGreater(len(matches), 0, "matches 비어 있음")
        required_keys = {"page", "title", "type", "score", "snippet"}
        for m in matches:
            missing = required_keys - m.keys()
            self.assertFalse(missing,
                             f"match에 필수 키 누락: {missing}, match={m}")


# ═════════════════════════════════════════════════════════════════════════════
# 6. sync-header — happy-path (code_scan_json_missing 에러 포함)
# ═════════════════════════════════════════════════════════════════════════════

class TestSyncHeader(BrainTestCase):
    """sync-header 서브커맨드 — 단방향(code-scan → entity frontmatter) 동기화."""

    def setUp(self):
        super().setUp()
        self._init()

    def test_sync_header_no_code_scan_json_error(self):
        """sync-header: .opal/code-scan.json 부재 시 code_scan_json_missing 에러."""
        # tmpdir에 code-scan.json 없음 → _load_code_scan_json이 err() 반환
        with _mock_kst():
            # cwd를 tmpdir로 패치하여 .opal/code-scan.json 탐색 경로를 제어
            with patch.object(pathlib.Path, "cwd", return_value=self.tmpdir):
                args = make_args(brain_path=str(self.brain_root))
                code = self._err_code(BT.cmd_sync_header, args)
        self.assertEqual(code, "code_scan_json_missing")

    def test_sync_header_with_stub_code_scan(self):
        """sync-header: code-scan.json 존재 + code-scan.js stub → ok=true 반환.

        단방향 동기화: code-scan @header → entity frontmatter (역방향 코드 부재 확인).
        실제 code-scan.js 실행 없이, _load_code_scan_json 반환값을 패치하여
        sync-header 흐름(페이지 필터링·drift 비교·stale 표시)을 진짜 코드로 실행.
        """
        # entity 페이지 1개 추가 (source_ref 포함)
        self._add_page("stub-entity", "entity", "스텁 엔티티")
        entity_file = self.brain_root / "pages" / "entity" / "stub-entity.md"
        text = entity_file.read_text(encoding="utf-8")
        fm, body = BT.parse_frontmatter(text)
        fm["source_ref"] = "opal/tools/stub/stub.py"
        fm["module"] = "old_module"
        fm["layer"] = "util"
        fm["domain"] = "opal-test"
        fm_yaml = __import__("yaml").safe_dump(
            fm, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()
        entity_file.write_text(f"---\n{fm_yaml}\n---\n{body}", encoding="utf-8")

        # code-scan.json이 있는 것처럼 config_path 존재 패치 + _load_code_scan_json 반환값 스텁
        stub_headers = {
            "opal/tools/stub/stub.py": {
                "module": "new_module",
                "layer": "tool",
                "domain": "opal-brain",
                "exports": ["cmd_test"],
            }
        }
        with _mock_kst():
            with patch.object(BT, "_load_code_scan_json", return_value=stub_headers):
                args = make_args(brain_path=str(self.brain_root))
                exit_code, result = self._call(BT.cmd_sync_header, args)
        self.assertEqual(exit_code, 0, f"sync-header 실패: {result}")
        self.assertTrue(result["ok"])
        # drift 발생: module·layer·domain 3개 필드 변경
        drift_fields = {d["field"] for d in result.get("drift", [])}
        self.assertIn("module", drift_fields)
        self.assertIn("layer", drift_fields)
        # 갱신된 frontmatter 검증 (단방향 확인)
        updated_text = entity_file.read_text(encoding="utf-8")
        updated_fm, _ = BT.parse_frontmatter(updated_text)
        self.assertEqual(updated_fm["module"], "new_module")
        self.assertEqual(updated_fm["layer"], "tool")

    def test_sync_header_stale_marking(self):
        """sync-header: code-scan에 없는 source_ref → status=stale 표시 (단방향 집행)."""
        # entity 페이지 + 존재하지 않는 source_ref
        self._add_page("orphan-entity", "entity", "고아 엔티티")
        entity_file = self.brain_root / "pages" / "entity" / "orphan-entity.md"
        text = entity_file.read_text(encoding="utf-8")
        fm, body = BT.parse_frontmatter(text)
        fm["source_ref"] = "opal/tools/nonexistent.py"
        fm["status"] = "active"
        fm_yaml = __import__("yaml").safe_dump(
            fm, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()
        entity_file.write_text(f"---\n{fm_yaml}\n---\n{body}", encoding="utf-8")

        # code-scan에 해당 source_ref 없음 → stale 표시
        with _mock_kst():
            with patch.object(BT, "_load_code_scan_json", return_value={}):
                args = make_args(brain_path=str(self.brain_root))
                exit_code, result = self._call(BT.cmd_sync_header, args)
        self.assertEqual(exit_code, 0)
        self.assertIn("orphan-entity", result.get("stale_marked", []))
        # 파일에 stale이 기록됐는지 확인
        updated_fm, _ = BT.parse_frontmatter(
            entity_file.read_text(encoding="utf-8"))
        self.assertEqual(updated_fm["status"], "stale")


# ═════════════════════════════════════════════════════════════════════════════
# 7. lint — happy-path
# ═════════════════════════════════════════════════════════════════════════════

class TestLint(BrainTestCase):
    """lint 서브커맨드 — 링크 무결성·고아·stale·근거 누락 탐지."""

    def setUp(self):
        super().setUp()
        self._init()

    def test_lint_empty_brain_no_issues(self):
        """lint: 빈 brain → issues=[] 반환."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            exit_code, result = self._call(BT.cmd_lint, args)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["issues"], [])

    def test_lint_detects_orphan_page(self):
        """lint: 링크 없는 고립 페이지 → kind=orphan 이슈 검출."""
        self._add_page("orphan-page", "entity", "고립 엔티티")
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            _, result = self._call(BT.cmd_lint, args)
        kinds = [i["kind"] for i in result.get("issues", [])]
        self.assertIn("orphan", kinds)

    def test_lint_detects_broken_link(self):
        """lint: 존재하지 않는 페이지 [[링크]] → kind=broken_link 검출."""
        # 존재하지 않는 페이지를 wikilink로 참조하는 페이지 수동 생성
        page_dir = self.brain_root / "pages" / "concept"
        broken_page = page_dir / "broken-link-page.md"
        content = (
            "---\n"
            "type: concept\n"
            "title: 링크 깨진 페이지\n"
            "created: 2026-06-10\n"
            "updated: 2026-06-10\n"
            "status: active\n"
            "---\n\n"
            "[[nonexistent-target]] 을 참조한다.\n"
        )
        broken_page.write_text(content, encoding="utf-8")
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            _, result = self._call(BT.cmd_lint, args)
        kinds = [i["kind"] for i in result.get("issues", [])]
        self.assertIn("broken_link", kinds)

    def test_lint_detects_unsourced_concept(self):
        """lint: sources 없는 concept 페이지 → kind=unsourced 검출."""
        self._add_page("no-source-concept", "concept", "근거 없는 개념")
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            _, result = self._call(BT.cmd_lint, args)
        kinds = [i["kind"] for i in result.get("issues", [])]
        self.assertIn("unsourced", kinds)

    def test_lint_detects_stale_page(self):
        """lint: status=stale 페이지 → kind=stale 검출."""
        self._add_page("stale-page", "entity", "stale 엔티티")
        # 페이지의 status를 stale로 변경
        stale_file = self.brain_root / "pages" / "entity" / "stale-page.md"
        text = stale_file.read_text(encoding="utf-8")
        fm, body = BT.parse_frontmatter(text)
        fm["status"] = "stale"
        fm_yaml = __import__("yaml").safe_dump(
            fm, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()
        stale_file.write_text(f"---\n{fm_yaml}\n---\n{body}", encoding="utf-8")
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            _, result = self._call(BT.cmd_lint, args)
        kinds = [i["kind"] for i in result.get("issues", [])]
        self.assertIn("stale", kinds)

    def test_lint_issues_count_field(self):
        """lint: issues_count 필드가 issues 배열 길이와 일치."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            _, result = self._call(BT.cmd_lint, args)
        self.assertEqual(result["issues_count"], len(result["issues"]))


# ═════════════════════════════════════════════════════════════════════════════
# 8. validate — happy-path
# ═════════════════════════════════════════════════════════════════════════════

class TestValidate(BrainTestCase):
    """validate 서브커맨드 — 구조·frontmatter 표준 검증."""

    def setUp(self):
        super().setUp()
        self._init()

    def test_validate_clean_brain_valid(self):
        """validate: 정상 초기화 brain → valid=true + violations=[]."""
        args = make_args(brain_path=str(self.brain_root))
        # validate는 violations 있으면 exit 1, 없으면 exit 0
        out = io.StringIO()
        with redirect_stdout(out):
            try:
                BT.cmd_validate(args)
            except SystemExit:
                pass
        result = json.loads(out.getvalue().strip())
        self.assertTrue(result["ok"])
        self.assertTrue(result["valid"])
        self.assertEqual(result["violations"], [])

    def test_validate_detects_missing_schema(self):
        """validate: SCHEMA.md 삭제 → violations에 structure 규칙 위반 포함.

        require_brain 은 SCHEMA.md 존재 여부로 초기화 판정을 한다. SCHEMA.md를
        삭제하면 brain_not_initialized 에러가 먼저 발생하므로, is_brain_initialized
        를 True 로 패치하여 validate 내부의 구조 검증 로직까지 진입하도록 한다.
        """
        (self.brain_root / "SCHEMA.md").unlink()
        args = make_args(brain_path=str(self.brain_root))
        out = io.StringIO()
        # is_brain_initialized 를 항상 True 로 패치 → require_brain 통과 후 validate 실행
        with patch.object(BT, "is_brain_initialized", return_value=True):
            with redirect_stdout(out):
                try:
                    BT.cmd_validate(args)
                except SystemExit:
                    pass
        result = json.loads(out.getvalue().strip())
        self.assertFalse(result["valid"])
        rules = [v["rule"] for v in result["violations"]]
        self.assertIn("structure", rules)

    def test_validate_detects_frontmatter_violation(self):
        """validate: 필수 키 누락 페이지 → violations에 frontmatter 규칙 위반 포함."""
        # 잘못된 frontmatter 페이지 수동 생성
        page_dir = self.brain_root / "pages" / "concept"
        bad_page = page_dir / "bad-fm.md"
        bad_page.write_text(
            "---\ntype: concept\n---\n본문 내용\n", encoding="utf-8"
        )
        args = make_args(brain_path=str(self.brain_root))
        out = io.StringIO()
        with redirect_stdout(out):
            try:
                BT.cmd_validate(args)
            except SystemExit:
                pass
        result = json.loads(out.getvalue().strip())
        self.assertFalse(result["valid"])
        rules = [v["rule"] for v in result["violations"]]
        self.assertIn("frontmatter", rules)

    def test_validate_violations_count_field(self):
        """validate: violations_count 필드가 violations 배열 길이와 일치."""
        args = make_args(brain_path=str(self.brain_root))
        out = io.StringIO()
        with redirect_stdout(out):
            try:
                BT.cmd_validate(args)
            except SystemExit:
                pass
        result = json.loads(out.getvalue().strip())
        self.assertEqual(result["violations_count"], len(result["violations"]))

    def test_validate_command_field_in_response(self):
        """validate: 응답 command 필드 = 'validate'."""
        args = make_args(brain_path=str(self.brain_root))
        out = io.StringIO()
        with redirect_stdout(out):
            try:
                BT.cmd_validate(args)
            except SystemExit:
                pass
        result = json.loads(out.getvalue().strip())
        self.assertEqual(result["command"], "validate")


# ═════════════════════════════════════════════════════════════════════════════
# 9. ERROR_CODES 주요 에러 경로 (14종)
# ═════════════════════════════════════════════════════════════════════════════

class TestErrorCodes(BrainTestCase):
    """ERROR_CODES 카탈로그 키 정합 + 주요 에러 경로 커버리지."""

    # ── E-1: brain_already_initialized ────────────────────────────────────────
    def test_brain_already_initialized(self):
        """init 두 번 호출 (--force 없음) → brain_already_initialized."""
        self._init()
        with _mock_kst():
            args = make_args(brain_path=str(self.tmpdir), force=False)
            code = self._err_code(BT.cmd_init, args)
        self.assertEqual(code, "brain_already_initialized")

    # ── E-2: brain_not_initialized (add-page) ─────────────────────────────────
    def test_brain_not_initialized_add_page(self):
        """미초기화 brain에 add-page → brain_not_initialized."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             path="test", type="concept", title="테스트")
            code = self._err_code(BT.cmd_add_page, args)
        self.assertEqual(code, "brain_not_initialized")

    # ── E-3: brain_not_initialized (index) ─────────────────────────────────────
    def test_brain_not_initialized_index(self):
        """미초기화 brain에 index → brain_not_initialized."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            code = self._err_code(BT.cmd_index, args)
        self.assertEqual(code, "brain_not_initialized")

    # ── E-4: brain_not_initialized (log) ──────────────────────────────────────
    def test_brain_not_initialized_log(self):
        """미초기화 brain에 log → brain_not_initialized."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             op="init", summary="테스트")
            code = self._err_code(BT.cmd_log, args)
        self.assertEqual(code, "brain_not_initialized")

    # ── E-5: brain_not_initialized (search) ───────────────────────────────────
    def test_brain_not_initialized_search(self):
        """미초기화 brain에 search → brain_not_initialized."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root), query="test")
            code = self._err_code(BT.cmd_search, args)
        self.assertEqual(code, "brain_not_initialized")

    # ── E-6: duplicate_page ───────────────────────────────────────────────────
    def test_duplicate_page(self):
        """동일 경로 페이지 재생성 시도 → duplicate_page."""
        self._init()
        self._add_page("dup-page", "concept", "중복 테스트")
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             path="dup-page", type="concept", title="중복 재생성")
            code = self._err_code(BT.cmd_add_page, args)
        self.assertEqual(code, "duplicate_page")

    # ── E-7: frontmatter_invalid (invalid type) ───────────────────────────────
    def test_invalid_page_type(self):
        """유효하지 않은 타입으로 add-page → invalid_page_type."""
        self._init()
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             path="bad-type", type="invalid_type", title="테스트")
            code = self._err_code(BT.cmd_add_page, args)
        self.assertEqual(code, "invalid_page_type")

    # ── E-8: query_empty ──────────────────────────────────────────────────────
    def test_query_empty(self):
        """빈 검색어로 search → query_empty."""
        self._init()
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root), query="")
            code = self._err_code(BT.cmd_search, args)
        self.assertEqual(code, "query_empty")

    def test_query_empty_whitespace(self):
        """공백만 있는 검색어 → query_empty."""
        self._init()
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root), query="   ")
            code = self._err_code(BT.cmd_search, args)
        self.assertEqual(code, "query_empty")

    # ── E-9: code_scan_json_missing ───────────────────────────────────────────
    def test_code_scan_json_missing(self):
        """code-scan.json 없는 상태에서 sync-header → code_scan_json_missing."""
        self._init()
        with _mock_kst():
            with patch.object(pathlib.Path, "cwd", return_value=self.tmpdir):
                args = make_args(brain_path=str(self.brain_root))
                code = self._err_code(BT.cmd_sync_header, args)
        self.assertEqual(code, "code_scan_json_missing")

    # ── E-10: invalid_log_op ──────────────────────────────────────────────────
    def test_invalid_log_op(self):
        """유효하지 않은 log op → invalid_log_op."""
        self._init()
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root),
                             op="invalid_op", summary="테스트")
            code = self._err_code(BT.cmd_log, args)
        self.assertEqual(code, "invalid_log_op")

    # ── E-11: brain_not_initialized (lint) ────────────────────────────────────
    def test_brain_not_initialized_lint(self):
        """미초기화 brain에 lint → brain_not_initialized."""
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            code = self._err_code(BT.cmd_lint, args)
        self.assertEqual(code, "brain_not_initialized")

    # ── E-12: brain_not_initialized (validate) ────────────────────────────────
    def test_brain_not_initialized_validate(self):
        """미초기화 brain에 validate → brain_not_initialized."""
        args = make_args(brain_path=str(self.brain_root))
        code = self._err_code(BT.cmd_validate, args)
        self.assertEqual(code, "brain_not_initialized")

    # ── E-13: ERROR_CODES 키 정합 검증 ────────────────────────────────────────
    def test_error_codes_catalog_keys_present(self):
        """ERROR_CODES 상수에 PLAN 결정3 명시 14개 키가 모두 포함됨."""
        required_keys = [
            "brain_already_initialized",
            "brain_path_invalid",
            "brain_not_initialized",
            "invalid_page_type",
            "frontmatter_invalid",
            "duplicate_page",
            "index_write_failed",
            "date_tool_failed",
            "log_append_failed",
            "query_empty",
            "code_scan_json_missing",
            "header_parse_failed",
            "invalid_log_op",
            "template_missing",
        ]
        for key in required_keys:
            self.assertIn(key, BT.ERROR_CODES,
                          f"ERROR_CODES에 키 누락: {key}")

    # ── E-14: JSON ok:bool 구조 검증 ──────────────────────────────────────────
    def test_ok_response_has_ok_and_command_fields(self):
        """모든 성공 응답이 ok=True + command 필드를 포함함 (PLAN 결정3)."""
        self._init()
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            exit_code, result = self._call(BT.cmd_index, args)
        self.assertIn("ok", result)
        self.assertIn("command", result)
        self.assertTrue(result["ok"])
        self.assertIsInstance(result["ok"], bool)

    def test_err_response_has_ok_false_and_error_field(self):
        """에러 응답이 ok=False + error 필드(ERROR_CODES 키)를 포함함 (PLAN 결정3)."""
        out = io.StringIO()
        with redirect_stdout(out):
            try:
                with _mock_kst():
                    args = make_args(brain_path=str(self.brain_root), query="")
                    BT.cmd_search(args)
            except SystemExit:
                pass
        result = json.loads(out.getvalue().strip())
        self.assertFalse(result["ok"])
        self.assertIn("error", result)
        self.assertIn(result["error"], BT.ERROR_CODES)


# ═════════════════════════════════════════════════════════════════════════════
# 10. 동적 페이지 타입 로드 테스트
# ═════════════════════════════════════════════════════════════════════════════

class TestDynamicPageTypes(BrainTestCase):
    """동적 타입 로드 — 커스텀 타입 선언 인식 / SCHEMA 부재 폴백 / --type 무효값."""

    def _write_custom_schema(self, types_table):
        """brain_root/SCHEMA.md에 커스텀 타입 테이블 작성."""
        schema_text = (
            "# Project Brain SCHEMA\n\n"
            "## 1.5 페이지 타입 정의 (brain-tool 동적 로드 SSOT)\n\n"
            "> brain-tool은 이 블록에서 타입 세트를 동적 로드한다.\n\n"
            "| type | category | 설명 |\n"
            "|------|----------|------|\n"
        )
        for ptype, category, desc in types_table:
            schema_text += f"| {ptype} | {category} | {desc} |\n"
        schema_text += "\n"
        (self.brain_root / "SCHEMA.md").write_text(schema_text, encoding="utf-8")

    def test_load_page_types_from_schema_custom_type(self):
        """SCHEMA §1.5에 커스텀 타입 'decision' 선언 시 load_page_types가 인식."""
        self._init()
        self._write_custom_schema([
            ("entity", "엔티티", "코드 모듈"),
            ("decision", "결정", "아키텍처 결정"),
        ])
        types, type_to_cat = BT.load_page_types(self.brain_root)
        self.assertIn("decision", types)
        self.assertEqual(type_to_cat.get("decision"), "결정")
        self.assertIn("entity", types)

    def test_load_page_types_schema_absent_fallback(self):
        """SCHEMA.md 부재 시 DEFAULT_PAGE_TYPES로 폴백."""
        # brain_root가 없는 경로 사용 (SCHEMA 부재)
        nonexistent = self.tmpdir / "no-brain"
        types, type_to_cat = BT.load_page_types(nonexistent)
        self.assertEqual(types, BT.DEFAULT_PAGE_TYPES)
        self.assertEqual(type_to_cat, BT._DEFAULT_TYPE_TO_CATEGORY)

    def test_load_page_types_schema_no_table_fallback(self):
        """SCHEMA.md가 있으나 §1.5 테이블 없으면 DEFAULT_PAGE_TYPES 폴백."""
        self._init()
        (self.brain_root / "SCHEMA.md").write_text(
            "# SCHEMA\n\n아무 테이블 없는 SCHEMA\n", encoding="utf-8"
        )
        types, type_to_cat = BT.load_page_types(self.brain_root)
        self.assertEqual(types, BT.DEFAULT_PAGE_TYPES)

    def test_add_page_with_custom_type_recognized(self):
        """커스텀 타입 'decision'이 타입 검증을 통과함 (SCHEMA 동적 인식 확인).

        커스텀 타입은 타입 검증(invalid_page_type)을 통과하되,
        해당 템플릿(page-decision.md) 부재 시 template_missing 에러가 나는 것이
        정상 동작이다. invalid_page_type이 아닌 다른 에러여야 한다.
        """
        self._init()
        # SCHEMA에 decision 타입 추가
        self._write_custom_schema([
            ("entity", "엔티티", "코드 모듈"),
            ("concept", "개념", "아키텍처"),
            ("flow", "흐름", "파이프라인"),
            ("synthesis", "합성", "분석"),
            ("decision", "결정", "아키텍처 결정"),
        ])
        # decision 타입 디렉토리 수동 생성
        (self.brain_root / "pages" / "decision").mkdir(parents=True, exist_ok=True)
        # decision 타입 페이지 생성 시도 → 타입 검증은 통과, 템플릿 부재로 다른 에러
        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                path="arch-decision-001",
                type="decision",
                title="아키텍처 결정 001",
            )
            code = self._err_code(BT.cmd_add_page, args)
        # invalid_page_type이 아닌 에러여야 함 (타입 자체는 유효하게 인식)
        self.assertNotEqual(
            code, "invalid_page_type",
            "SCHEMA 동적 타입 'decision'이 invalid_page_type으로 거부됨 — 동적 로드 실패"
        )

    def test_add_page_invalid_type_returns_invalid_page_type(self):
        """--type에 무효값 → invalid_page_type 에러 코드 (argparse choices 제거 후에도 유지)."""
        self._init()
        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                path="bad-type-page",
                type="nonexistent_type_xyz",
                title="테스트",
            )
            code = self._err_code(BT.cmd_add_page, args)
        self.assertEqual(code, "invalid_page_type")

    def test_default_page_types_alias_preserved(self):
        """BT.PAGE_TYPES alias가 DEFAULT_PAGE_TYPES와 동일 (기존 테스트 호환)."""
        self.assertEqual(BT.PAGE_TYPES, BT.DEFAULT_PAGE_TYPES)


# ═════════════════════════════════════════════════════════════════════════════
# 11. analyze happy-path
# ═════════════════════════════════════════════════════════════════════════════

class TestAnalyze(BrainTestCase):
    """analyze 서브커맨드 — code-scan @header 정량 집계."""

    def test_analyze_no_code_scan_json_error(self):
        """code-scan.json 없는 상태에서 analyze → code_scan_json_missing."""
        with patch.object(pathlib.Path, "cwd", return_value=self.tmpdir):
            args = make_args()
            code = self._err_code(BT.cmd_analyze, args)
        self.assertEqual(code, "code_scan_json_missing")

    def test_analyze_happy_path_ok_true(self):
        """analyze: stub code-scan.json 결과로 정량 집계 → ok=true + 집계 필드 포함."""
        stub_headers = {
            "opal/tools/brain-tool/brain_tool.py": {
                "module": "brain_tool",
                "layer": "util",
                "domain": "opal-brain",
                "exports": ["cmd_init", "cmd_add_page", "cmd_index"],
            },
            "opal/tools/state-tool/state_tool.py": {
                "module": "state_tool",
                "layer": "tool",
                "domain": "opal-pipeline",
                "exports": ["cmd_init", "cmd_mark"],
            },
            "opal/core/AGENT.md": {
                "module": "agent",
                "layer": "orchestrator",
                "domain": "opal-pipeline",
                "exports": [],
            },
        }
        with patch.object(BT, "_load_code_scan_json", return_value=stub_headers):
            args = make_args()
            exit_code, result = self._call(BT.cmd_analyze, args)
        self.assertEqual(exit_code, 0, f"analyze 실패: {result}")
        self.assertTrue(result["ok"])
        self.assertEqual(result["command"], "analyze")
        # 집계 필드 존재 확인
        self.assertIn("total_files", result)
        self.assertEqual(result["total_files"], 3)
        self.assertIn("domain_counts", result)
        self.assertIn("layer_counts", result)
        self.assertIn("seed_candidates", result)
        # opal-brain domain: 1개, opal-pipeline: 2개
        self.assertEqual(result["domain_counts"].get("opal-brain"), 1)
        self.assertEqual(result["domain_counts"].get("opal-pipeline"), 2)

    def test_analyze_seed_candidates_threshold(self):
        """analyze: exports >= 3 또는 seed_layers 해당 파일이 seed_candidates에 포함."""
        stub_headers = {
            "tool_a.py": {
                "module": "tool_a",
                "layer": "util",
                "domain": "domain-x",
                "exports": ["a", "b", "c"],  # exports_min=3 충족
            },
            "tool_b.py": {
                "module": "tool_b",
                "layer": "orchestrator",  # seed_layers 충족
                "domain": "domain-x",
                "exports": [],
            },
            "tool_c.py": {
                "module": "tool_c",
                "layer": "util",
                "domain": "domain-x",
                "exports": ["x"],  # 미충족
            },
        }
        with patch.object(BT, "_load_code_scan_json", return_value=stub_headers):
            args = make_args()
            _, result = self._call(BT.cmd_analyze, args)
        seed_modules = {s["module"] for s in result.get("seed_candidates", [])}
        self.assertIn("tool_a", seed_modules)
        self.assertIn("tool_b", seed_modules)
        self.assertNotIn("tool_c", seed_modules)

    def test_analyze_empty_headers_ok(self):
        """analyze: 빈 code-scan 결과 → total_files=0 + ok=true."""
        with patch.object(BT, "_load_code_scan_json", return_value={}):
            args = make_args()
            exit_code, result = self._call(BT.cmd_analyze, args)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["total_files"], 0)
        self.assertEqual(result["seed_candidates"], [])


# ═════════════════════════════════════════════════════════════════════════════
# 12. ingest-scan happy-path
# ═════════════════════════════════════════════════════════════════════════════

class TestIngestScan(BrainTestCase):
    """ingest-scan 서브커맨드 — docs/skills/tasks 스캔 목록 반환."""

    def setUp(self):
        super().setUp()
        self._init()
        # 테스트용 가짜 프로젝트 구조 생성
        # docs/
        (self.tmpdir / "docs").mkdir(exist_ok=True)
        (self.tmpdir / "docs" / "ARCHITECTURE.md").write_text(
            "# Architecture\n", encoding="utf-8")
        (self.tmpdir / "docs" / "CONVENTIONS.md").write_text(
            "# Conventions\n", encoding="utf-8")
        # tasks/001-test-task/
        task_dir = self.tmpdir / "tasks" / "001-test-task"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "DONE.md").write_text("# DONE\n", encoding="utf-8")
        (task_dir / "PLAN.md").write_text("# PLAN\n", encoding="utf-8")
        # tasks/002-another-task/
        task_dir2 = self.tmpdir / "tasks" / "002-another-task"
        task_dir2.mkdir(parents=True, exist_ok=True)
        (task_dir2 / "PLAN.md").write_text("# PLAN\n", encoding="utf-8")
        # opal/skills/test-skill/
        skill_dir = self.tmpdir / "opal" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("# SKILL\n", encoding="utf-8")

    def test_ingest_scan_docs_ok(self):
        """ingest-scan --source docs: docs/*.md 목록 반환 → ok=true."""
        with patch.object(pathlib.Path, "cwd", return_value=self.tmpdir):
            args = make_args(brain_path=str(self.brain_root), source="docs")
            exit_code, result = self._call(BT.cmd_ingest_scan, args)
        self.assertEqual(exit_code, 0, f"ingest-scan 실패: {result}")
        self.assertTrue(result["ok"])
        self.assertEqual(result["command"], "ingest-scan")
        self.assertIn("items", result)
        kinds = {item["kind"] for item in result["items"]}
        self.assertIn("doc", kinds)
        self.assertEqual(result["total"], 2)

    def test_ingest_scan_tasks_ok(self):
        """ingest-scan --source tasks: tasks/NNN-xxx 목록 반환 → ok=true."""
        with patch.object(pathlib.Path, "cwd", return_value=self.tmpdir):
            args = make_args(brain_path=str(self.brain_root), source="tasks")
            exit_code, result = self._call(BT.cmd_ingest_scan, args)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        task_items = [i for i in result["items"] if i["kind"] == "task"]
        self.assertEqual(len(task_items), 2)
        task_nums = {i["task_num"] for i in task_items}
        self.assertIn("001", task_nums)
        self.assertIn("002", task_nums)

    def test_ingest_scan_tasks_has_done_field(self):
        """ingest-scan tasks: has_done 필드가 정확히 반영됨."""
        with patch.object(pathlib.Path, "cwd", return_value=self.tmpdir):
            args = make_args(brain_path=str(self.brain_root), source="tasks")
            _, result = self._call(BT.cmd_ingest_scan, args)
        items_by_num = {i["task_num"]: i for i in result["items"] if i["kind"] == "task"}
        self.assertTrue(items_by_num["001"]["has_done"])
        self.assertFalse(items_by_num["002"]["has_done"])

    def test_ingest_scan_skills_ok(self):
        """ingest-scan --source skills: SKILL.md 목록 반환 → ok=true."""
        with patch.object(pathlib.Path, "cwd", return_value=self.tmpdir):
            args = make_args(brain_path=str(self.brain_root), source="skills")
            exit_code, result = self._call(BT.cmd_ingest_scan, args)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        skill_items = [i for i in result["items"] if i["kind"] == "skill"]
        self.assertEqual(len(skill_items), 1)

    def test_ingest_scan_all_ok(self):
        """ingest-scan --source all: 모든 소스 합산 반환 → ok=true."""
        with patch.object(pathlib.Path, "cwd", return_value=self.tmpdir):
            args = make_args(brain_path=str(self.brain_root), source="all")
            exit_code, result = self._call(BT.cmd_ingest_scan, args)
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertGreater(result["total"], 0)
        kinds = {item["kind"] for item in result["items"]}
        self.assertIn("doc", kinds)
        self.assertIn("task", kinds)
        self.assertIn("skill", kinds)

    def test_ingest_scan_skip_already_ingested(self):
        """ingest-scan: 이미 ingest된 sources가 있는 항목은 skip=true."""
        # task:001을 이미 ingest된 것으로 표시하는 페이지 추가
        page_dir = self.brain_root / "pages" / "concept"
        page_dir.mkdir(parents=True, exist_ok=True)
        page_content = (
            "---\n"
            "type: concept\n"
            "title: 태스크 001 결정\n"
            "created: 2026-06-10\n"
            "updated: 2026-06-10\n"
            "status: active\n"
            "sources: [task:001]\n"
            "---\n\n내용\n"
        )
        (page_dir / "task-001-decision.md").write_text(page_content, encoding="utf-8")

        with patch.object(pathlib.Path, "cwd", return_value=self.tmpdir):
            args = make_args(brain_path=str(self.brain_root), source="tasks")
            _, result = self._call(BT.cmd_ingest_scan, args)
        items_by_num = {i["task_num"]: i for i in result["items"] if i["kind"] == "task"}
        self.assertTrue(items_by_num["001"]["skip"])
        self.assertFalse(items_by_num["002"]["skip"])
        self.assertEqual(result["skip_count"], 1)
        self.assertEqual(result["pending_count"], 1)

    def test_ingest_scan_not_initialized_brain_error(self):
        """미초기화 brain에 ingest-scan → brain_not_initialized."""
        uninit_brain = self.tmpdir / "uninit" / ".opal" / "brain"
        with patch.object(pathlib.Path, "cwd", return_value=self.tmpdir):
            args = make_args(brain_path=str(uninit_brain), source="all")
            code = self._err_code(BT.cmd_ingest_scan, args)
        self.assertEqual(code, "brain_not_initialized")


# ═════════════════════════════════════════════════════════════════════════════
# 14. validate_frontmatter 단위 테스트 (내부 헬퍼)
# ═════════════════════════════════════════════════════════════════════════════

class TestValidateFrontmatter(unittest.TestCase):
    """validate_frontmatter 내부 함수 단위 검증."""

    def _valid_fm(self):
        return {
            "type": "entity",
            "title": "테스트",
            "created": "2026-06-10",
            "updated": "2026-06-10",
            "status": "active",
        }

    def test_valid_frontmatter_no_issues(self):
        """필수 키 완비 frontmatter → issues=[]."""
        issues = BT.validate_frontmatter(self._valid_fm())
        self.assertEqual(issues, [])

    def test_missing_required_key(self):
        """필수 키(title) 누락 → issues 포함."""
        fm = self._valid_fm()
        del fm["title"]
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(any("title" in i for i in issues))

    def test_invalid_type_enum(self):
        """type이 enum 외 값 → issues 포함."""
        fm = self._valid_fm()
        fm["type"] = "unknown"
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(any("invalid type" in i for i in issues))

    def test_invalid_status_enum(self):
        """status가 enum 외 값 → issues 포함."""
        fm = self._valid_fm()
        fm["status"] = "published"
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(any("invalid status" in i for i in issues))

    def test_none_frontmatter(self):
        """fm=None → frontmatter block missing 이슈."""
        issues = BT.validate_frontmatter(None)
        self.assertTrue(len(issues) > 0)
        self.assertIn("frontmatter block missing or unparseable", issues)

    def test_all_page_types_valid(self):
        """entity·concept·flow·synthesis 4종 모두 유효."""
        for ptype in BT.PAGE_TYPES:
            fm = self._valid_fm()
            fm["type"] = ptype
            issues = BT.validate_frontmatter(fm)
            type_issues = [i for i in issues if "invalid type" in i]
            self.assertEqual(type_issues, [], f"type={ptype}가 invalid로 판정됨")

    # ── 035: 평탄성 검사 RED-first 케이스 ──────────────────────────────────

    # --- 검출 케이스 (RED 대상 — 수정 전 FAIL) ---

    def test_flatness_nested_related_detected(self):
        """TS-001: related=[['a','b']] (중첩 리스트) → 'related must be a flat list of strings' issue 포함."""
        fm = self._valid_fm()
        fm["related"] = [["a", "b"]]
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(
            any("related must be a flat list" in i for i in issues),
            f"related 중첩 리스트가 violation으로 검출되지 않음. issues={issues}",
        )

    def test_flatness_nested_tags_detected(self):
        """TS-004: tags=[['x']] (중첩 리스트) → 'tags must be a flat list of strings' issue 포함."""
        fm = self._valid_fm()
        fm["tags"] = [["x"]]
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(
            any("tags must be a flat list" in i for i in issues),
            f"tags 중첩 리스트가 violation으로 검출되지 않음. issues={issues}",
        )

    def test_flatness_nonstring_sources_detected(self):
        """TS-005: sources=[1, 2] (비문자열 int) → 'sources must be a flat list of strings' issue 포함."""
        fm = self._valid_fm()
        fm["sources"] = [1, 2]
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(
            any("sources must be a flat list" in i for i in issues),
            f"sources 비문자열 요소가 violation으로 검출되지 않음. issues={issues}",
        )

    def test_flatness_nonstring_related_detected(self):
        """TS-006: related=[1] (비문자열 int) → 'related must be a flat list of strings' issue 포함."""
        fm = self._valid_fm()
        fm["related"] = [1]
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(
            any("related must be a flat list" in i for i in issues),
            f"related 비문자열 요소가 violation으로 검출되지 않음. issues={issues}",
        )

    def test_flatness_tags_not_a_list_detected(self):
        """TS-004b: tags='notalist' (list 아님, 문자열) → 'tags must be a flat list of strings' issue 포함."""
        fm = self._valid_fm()
        fm["tags"] = "notalist"
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(
            any("tags must be a flat list" in i for i in issues),
            f"tags가 list가 아닌 경우가 violation으로 검출되지 않음. issues={issues}",
        )

    # --- 통과 케이스 (수정 전·후 모두 PASS — 오탐 방지) ---

    def test_flatness_valid_flat_lists_pass(self):
        """TS-002: tags=['a','b'], sources=['code:x'], related=['page-y'] (정상 flat string[]) → 평탄성 issue 0."""
        fm = self._valid_fm()
        fm["tags"] = ["a", "b"]
        fm["sources"] = ["code:x"]
        fm["related"] = ["page-y"]
        issues = BT.validate_frontmatter(fm)
        flatness_issues = [i for i in issues if "must be a flat list" in i]
        self.assertEqual(
            flatness_issues,
            [],
            f"정상 flat string[] 값이 오탐으로 검출됨. flatness_issues={flatness_issues}",
        )

    def test_flatness_optional_fields_absent_pass(self):
        """TS-003a: 선택 필드 전부 부재 (필수 5필드만) → issues=[]."""
        fm = self._valid_fm()
        # tags/sources/related 키 없음
        issues = BT.validate_frontmatter(fm)
        self.assertEqual(issues, [], f"선택 필드 부재 시 오탐 발생. issues={issues}")

    def test_flatness_empty_lists_pass(self):
        """TS-003b: tags=[], sources=[], related=[] (빈 리스트) → 평탄성 issue 0 (H-4 경계 검증)."""
        fm = self._valid_fm()
        fm["tags"] = []
        fm["sources"] = []
        fm["related"] = []
        issues = BT.validate_frontmatter(fm)
        flatness_issues = [i for i in issues if "must be a flat list" in i]
        self.assertEqual(
            flatness_issues,
            [],
            f"빈 리스트가 오탐으로 검출됨. flatness_issues={flatness_issues}",
        )

    # ── 053: 링크필드(related) 검사 RED-first 케이스 ──────────────────────

    # --- 거부 케이스 (RED 대상 — 구현 전 FAIL) ---

    def test_link_field_bracket_related_detected(self):
        """053 R-2: related=["[[state-tool]]"] (wiki-link 문법) → 'must be a plain page slug' issue 포함."""
        fm = self._valid_fm()
        fm["related"] = ["[[state-tool]]"]
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(
            any("must be a plain page slug" in i for i in issues),
            f"related '[[...]]' 값이 violation으로 검출되지 않음. issues={issues}",
        )

    def test_link_field_md_suffix_related_detected(self):
        """053 R-2: related=["state-tool.md"] (.md 접미사) → 'must be a plain page slug' issue 포함."""
        fm = self._valid_fm()
        fm["related"] = ["state-tool.md"]
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(
            any("must be a plain page slug" in i for i in issues),
            f"related '.md' 접미사 값이 violation으로 검출되지 않음. issues={issues}",
        )

    def test_link_field_partial_closing_bracket_detected(self):
        """053 R-2: related=["a]]"] (부분 닫는 토큰) → 'must be a plain page slug' issue 포함."""
        fm = self._valid_fm()
        fm["related"] = ["a]]"]
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(
            any("must be a plain page slug" in i for i in issues),
            f"related ']]' 부분 토큰이 violation으로 검출되지 않음. issues={issues}",
        )

    def test_link_field_partial_opening_bracket_detected(self):
        """053 R-2: related=["[[a"] (부분 여는 토큰) → 'must be a plain page slug' issue 포함."""
        fm = self._valid_fm()
        fm["related"] = ["[[a"]
        issues = BT.validate_frontmatter(fm)
        self.assertTrue(
            any("must be a plain page slug" in i for i in issues),
            f"related '[[' 부분 토큰이 violation으로 검출되지 않음. issues={issues}",
        )

    # --- 통과 케이스 (구현 전·후 모두 PASS — 오탐 방지) ---

    def test_link_field_valid_slugs_pass(self):
        """053 R-2: related=["state-tool","brain-tool"] (정상 슬러그) → 링크필드 issue 0."""
        fm = self._valid_fm()
        fm["related"] = ["state-tool", "brain-tool"]
        issues = BT.validate_frontmatter(fm)
        link_issues = [i for i in issues if "must be a plain page slug" in i]
        self.assertEqual(
            link_issues,
            [],
            f"정상 슬러그가 오탐으로 검출됨. link_issues={link_issues}",
        )

    def test_link_field_none_pass(self):
        """053 R-2: related=None (부재) → 링크필드 issue 0."""
        fm = self._valid_fm()
        fm["related"] = None
        issues = BT.validate_frontmatter(fm)
        link_issues = [i for i in issues if "must be a plain page slug" in i]
        self.assertEqual(link_issues, [], f"related=None이 오탐으로 검출됨. link_issues={link_issues}")

    def test_link_field_empty_list_pass(self):
        """053 R-2: related=[] (빈 리스트) → 링크필드 issue 0."""
        fm = self._valid_fm()
        fm["related"] = []
        issues = BT.validate_frontmatter(fm)
        link_issues = [i for i in issues if "must be a plain page slug" in i]
        self.assertEqual(link_issues, [], f"related=[]가 오탐으로 검출됨. link_issues={link_issues}")


# ═════════════════════════════════════════════════════════════════════════════
# 035: validate 평탄성 통합 테스트 (TS-008 — cmd_validate 종단)
# ═════════════════════════════════════════════════════════════════════════════

class TestValidateFlatness035(BrainTestCase):
    """TS-008: cmd_validate 종단 통합 — 중첩 related 페이지가 frontmatter violation으로 표면화."""

    def setUp(self):
        super().setUp()
        self._init()

    def test_validate_detects_nested_related_violation(self):
        """TS-008: pages/concept/에 related=[['a','b']] 페이지 작성 → cmd_validate가 rule=frontmatter violation 반환 + valid=False."""
        # YAML에서 [[a, b]]는 중첩 시퀀스로 파싱됨
        page_dir = self.brain_root / "pages" / "concept"
        nested_page = page_dir / "nested-related.md"
        nested_page.write_text(
            "---\n"
            "type: concept\n"
            "title: 중첩 related 테스트\n"
            "created: 2026-06-22\n"
            "updated: 2026-06-22\n"
            "status: active\n"
            "related:\n"
            "  - - a\n"
            "    - b\n"
            "---\n"
            "본문 내용\n",
            encoding="utf-8",
        )
        args = make_args(brain_path=str(self.brain_root))
        out = io.StringIO()
        with redirect_stdout(out):
            try:
                BT.cmd_validate(args)
            except SystemExit:
                pass
        result = json.loads(out.getvalue().strip())
        self.assertFalse(
            result["valid"],
            f"중첩 related 페이지가 valid=True로 통과됨 (종단 violation 누락). result={result}",
        )
        rules = [v["rule"] for v in result["violations"]]
        self.assertIn(
            "frontmatter",
            rules,
            f"violations에 rule='frontmatter'가 없음 (issue→violation 매핑 실패). violations={result['violations']}",
        )


# ═════════════════════════════════════════════════════════════════════════════
# 027: term 동적 로드 + draft search 필터 + lint term_duplicate/alias_collision
# ═════════════════════════════════════════════════════════════════════════════

class TestTermDraft027(BrainTestCase):
    """027: term 동적 로드 + search draft 필터 (R-6 term 한정).

    테스트 구조:
    - term 타입이 SCHEMA §1.5에 있으면 load_page_types가 인식한다.
    - add-page --type term이 통과한다 (page-term.md 템플릿 필요).
    - type=term + status=draft 페이지는 기본 검색에서 제외, --include-draft로 포함.
    - type=concept + status=draft 페이지는 기본 검색에 노출 (R-6 회귀 케이스).
    - 기존 검색 동작 보존 회귀 케이스.
    """

    def _write_schema_with_term(self):
        """brain_root/SCHEMA.md에 term 타입이 포함된 §1.5 테이블 작성."""
        schema_text = (
            "# Project Brain SCHEMA\n\n"
            "## 1.5 페이지 타입 정의 (brain-tool 동적 로드 SSOT)\n\n"
            "> brain-tool은 이 블록에서 타입 세트를 동적 로드한다.\n\n"
            "| type | category | 설명 |\n"
            "|------|----------|------|\n"
            "| term | 도메인 | 프로젝트 비즈니스 표준 용어 (1페이지=1용어) |\n"
            "| entity | 엔티티 | 코드 모듈·서비스·도구·스킬 |\n"
            "| concept | 개념 | 아키텍처 결정·설계 배경 |\n"
            "| flow | 흐름 | 파이프라인·프로세스 흐름 |\n"
            "| synthesis | 합성 | 질의 파생 분석 |\n"
        )
        (self.brain_root / "SCHEMA.md").write_text(schema_text, encoding="utf-8")

    # ── TestDynamicPageTypes 확장: term 동적 로드 ───────────────────────────

    def test_load_page_types_includes_term(self):
        """027-T1: SCHEMA §1.5에 term 행 → load_page_types가 term을 반환."""
        self._init()
        self._write_schema_with_term()
        types, type_to_cat = BT.load_page_types(self.brain_root)
        self.assertIn("term", types,
                      f"load_page_types가 term을 반환하지 않음. 반환값: {types}")
        self.assertEqual(type_to_cat.get("term"), "도메인",
                         f"term의 category가 '도메인'이 아님: {type_to_cat.get('term')}")

    def test_add_page_term_type_recognized(self):
        """027-T2: add-page --type term이 타입 검증을 통과한다.

        커스텀 타입은 타입 검증(invalid_page_type)을 통과하되,
        page-term.md 템플릿이 있으면 성공해야 한다.
        invalid_page_type 에러가 나면 동적 로드 실패.
        """
        self._init()
        self._write_schema_with_term()
        # term 타입 디렉토리 생성
        (self.brain_root / "pages" / "term").mkdir(parents=True, exist_ok=True)
        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                path="test-term-page",
                type="term",
                title="테스트 용어",
            )
            code, result = self._call(BT.cmd_add_page, args)
        # invalid_page_type이 나면 동적 로드 실패
        if code != 0:
            error = result.get("error", "")
            self.assertNotEqual(
                error, "invalid_page_type",
                "SCHEMA 동적 타입 'term'이 invalid_page_type으로 거부됨 — 동적 로드 실패"
            )
        else:
            # 성공 시 페이지가 생성됐는지 확인
            page_path = self.brain_root / "pages" / "term" / "test-term-page.md"
            self.assertTrue(page_path.exists(), "term 페이지 파일이 생성되지 않음")

    # ── TestSearch 확장: draft 필터 (R-6 term 한정) ────────────────────────

    def test_search_term_draft_excluded_by_default(self):
        """027-S1: type=term + status=draft 페이지는 기본 검색에서 제외 (R-6 term 한정)."""
        self._init()
        self._write_schema_with_term()
        # term 페이지를 draft 상태로 생성
        self._write_term_page("draft-term", "초안용어", status="draft")

        with _mock_kst():
            # --include-draft 없음 (기본값 False)
            args = make_args(
                brain_path=str(self.brain_root),
                query="초안용어",
                type=None,
                include_draft=False,
            )
            _, result = self._call(BT.cmd_search, args)

        matches = result.get("matches", [])
        term_draft_pages = [m for m in matches if "draft-term" in m.get("page", "")]
        self.assertEqual(
            term_draft_pages, [],
            f"draft term 페이지가 기본 검색에 노출됨(R-6 위반): {term_draft_pages}"
        )

    def test_search_term_draft_included_with_flag(self):
        """027-S2: type=term + status=draft 페이지는 --include-draft로 포함."""
        self._init()
        self._write_schema_with_term()
        self._write_term_page("draft-term-b", "드래프트용어B", status="draft")

        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                query="드래프트용어B",
                type=None,
                include_draft=True,
            )
            _, result = self._call(BT.cmd_search, args)

        matches = result.get("matches", [])
        term_draft_pages = [m for m in matches if "draft-term-b" in m.get("page", "")]
        self.assertGreater(
            len(term_draft_pages), 0,
            "--include-draft 지정 시 draft term 페이지가 검색 결과에 없음"
        )

    def test_search_concept_draft_still_visible(self):
        """027-S3: type=concept + status=draft 페이지는 기본 검색에 노출 (R-6 회귀 케이스).

        add-page가 전 타입을 draft로 생성하므로, concept draft는 기본 검색에 노출돼야 한다.
        """
        self._init()
        # concept 페이지 추가 (add-page는 status=draft로 생성)
        self._add_page("concept-draft-page", "concept", "개념페이지드래프트")

        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                query="개념페이지드래프트",
                type=None,
                include_draft=False,  # draft 필터 기본값
            )
            _, result = self._call(BT.cmd_search, args)

        matches = result.get("matches", [])
        concept_pages = [m for m in matches if "concept-draft-page" in m.get("page", "")]
        self.assertGreater(
            len(concept_pages), 0,
            "concept draft 페이지가 기본 검색에서 제외됨 — R-6 회귀 발생 (concept은 draft여도 노출돼야 함)"
        )

    def test_search_term_active_always_visible(self):
        """027-S4: type=term + status=active 페이지는 기본 검색에 노출 (회귀 케이스)."""
        self._init()
        self._write_schema_with_term()
        self._write_term_page("active-term", "활성용어", status="active")

        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                query="활성용어",
                type=None,
                include_draft=False,
            )
            _, result = self._call(BT.cmd_search, args)

        matches = result.get("matches", [])
        active_term_pages = [m for m in matches if "active-term" in m.get("page", "")]
        self.assertGreater(
            len(active_term_pages), 0,
            "status=active term 페이지가 기본 검색에서 제외됨 — draft 필터가 active도 제외함 (버그)"
        )


class TestTermLint027(BrainTestCase):
    """027: lint term_duplicate + alias_collision 신규 검출 2종.

    테스트 구조:
    - 동일 정규화 표준명 term 2개 → term_duplicate 검출.
    - term A의 alias가 term B의 title과 동일 정규화 → alias_collision 검출.
    - term 미존재 brain → 신규 kind 0건 (회귀 0).
    """

    # ── ① term_duplicate 검출 ─────────────────────────────────────────────

    def test_lint_detects_term_duplicate(self):
        """027-L1: 동일 정규화 표준명 term 2개 → kind=term_duplicate 검출.

        "자동취소" 와 "자동 취소" 는 _norm 기준 동일 정규화 → term_duplicate.
        """
        self._init()
        self._write_term_page("term-a", "자동취소")
        self._write_term_page("term-b", "자동 취소")  # 정규화 동일

        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            _, result = self._call(BT.cmd_lint, args)

        kinds = [i["kind"] for i in result.get("issues", [])]
        self.assertIn(
            "term_duplicate", kinds,
            f"term_duplicate 미검출. 검출된 kind: {kinds}"
        )

    # ── ② alias_collision 검출 ────────────────────────────────────────────

    def test_lint_detects_alias_collision_with_title(self):
        """027-L2: term A의 alias가 term B의 title과 동일 정규화 → alias_collision 검출."""
        self._init()
        self._write_term_page("term-x", "주문취소")
        self._write_term_page("term-y", "선정취소", aliases=["주문취소"])  # term-x title과 충돌

        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            _, result = self._call(BT.cmd_lint, args)

        kinds = [i["kind"] for i in result.get("issues", [])]
        self.assertIn(
            "alias_collision", kinds,
            f"alias_collision 미검출. 검출된 kind: {kinds}"
        )

    def test_lint_detects_alias_collision_between_aliases(self):
        """027-L2b: term A의 alias가 term B의 alias와 동일 정규화 → alias_collision 검출."""
        self._init()
        self._write_term_page("term-p", "구매취소", aliases=["purchase cancel"])
        self._write_term_page("term-q", "결제취소", aliases=["purchase  cancel"])  # 정규화 동일 (공백 2개)

        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            _, result = self._call(BT.cmd_lint, args)

        kinds = [i["kind"] for i in result.get("issues", [])]
        self.assertIn(
            "alias_collision", kinds,
            f"alias_collision 미검출 (alias↔alias). 검출된 kind: {kinds}"
        )

    # ── ③ term 미존재 brain → 신규 kind 0건 (회귀 0) ────────────────────

    def test_lint_no_term_pages_zero_new_kinds(self):
        """027-L3: term 페이지 없는 brain → term_duplicate/alias_collision 0건 (회귀 0).

        concept/entity 등 비-term 페이지만 있는 brain에서 신규 kind가 나오면 회귀.
        """
        self._init()
        # concept 페이지만 추가 (term 없음)
        self._add_page("concept-only", "concept", "개념페이지")

        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            _, result = self._call(BT.cmd_lint, args)

        kinds = [i["kind"] for i in result.get("issues", [])]
        self.assertNotIn(
            "term_duplicate", kinds,
            "term 페이지 없는 brain에서 term_duplicate 검출됨 — 회귀 발생"
        )
        self.assertNotIn(
            "alias_collision", kinds,
            "term 페이지 없는 brain에서 alias_collision 검출됨 — 회귀 발생"
        )

    def test_lint_issues_count_consistent_with_term_issues(self):
        """027-L4: issues_count가 term 이슈 포함 후에도 len(issues)와 일치."""
        self._init()
        self._write_term_page("term-dup-1", "중복용어")
        self._write_term_page("term-dup-2", "중복 용어")  # 정규화 동일 → term_duplicate

        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            _, result = self._call(BT.cmd_lint, args)

        self.assertEqual(
            result["issues_count"], len(result["issues"]),
            "issues_count가 issues 배열 길이와 불일치"
        )


# ═════════════════════════════════════════════════════════════════════════════
# 15. 071 RED — 미실체 지식 등록 차단 게이트 (add-page 거부 + lint 소급)
# ═════════════════════════════════════════════════════════════════════════════
#
# [MUST] RED-first (opal/core/references/harness/red-first.md §1.5/§2/§3):
#   본 클래스는 opal-test-agent(mode: red)가 작성한 실패 우선 테스트다.
#   brain_tool.py의 SPECULATIVE_MARKERS·detect_speculative_markers·
#   ERROR_CODES["speculative_content"]·add-page --body-file/--force/--note 게이트·
#   lint speculative kind는 아직 구현되지 않았다(GREEN = op-dev-execute 담당,
#   opal-be-agent). 작성자≠구현자 — 이 클래스를 GREEN 작업 중 수정하지 말 것.
#   검증은 공개 인터페이스(CLI JSON ok/error/markers/issues/warning/override_note)
#   + frontmatter 파일 내용만 사용한다(private 결합 금지).
#
# PLAN.md §3.2.5 / TEST-SCENARIO.md §3 L1 S-1~S-9 (TS-201~209) 계약을 그대로 옮김.

# pointail 등가 미실체 본문 — 헤딩에 구조적 마커("아직 미착수, 설계 기록 단계"/"미확정 이슈")
# 포함. 산문이 아닌 '#' 헤딩 라인에 마커가 있어야 detect_speculative_markers가 검출한다(M-1).
_SPECULATIVE_BODY_071 = (
    "## 개요\n\n"
    "이 개념은 향후 브레인 게이트 강화를 위한 검토 초안이다.\n\n"
    "## 구현 영향 범위 (HOW) — 아직 미착수, 설계 기록 단계\n\n"
    "구현은 이후 진행 예정이며 세부 사항은 아직 미정이다.\n\n"
    "## 미확정 이슈\n\n"
    "- 세부 정책 미확정\n"
    "- 우회 조건 미확정\n"
)

# 정상 정착 본문 — 헤딩은 page-concept 템플릿 정착 구조(개요/결정 내용/영향·관계)만 사용해
# 마커 0이어야 한다. 산문(비헤딩)에 "향후"를 단순 언급해도 오검출되지 않아야 한다(H-1 방어).
_NORMAL_BODY_071 = (
    "## 개요\n\n"
    "이 개념은 파이프라인 재시도 정책을 정의한다.\n\n"
    "## 결정 내용 (HOW)\n\n"
    "재시도는 최대 3회, 지수 백오프를 적용한다. "
    "향후 모니터링 강화도 고려하나 이 결정 자체는 확정 사항이다.\n\n"
    "## 영향·관계\n\n"
    "이 결정은 브레인 파이프라인 안정성에 영향을 준다.\n"
)


class TestSpeculativeGate071(BrainTestCase):
    """071 RED — add-page 미실체 마커 거부 게이트 + lint speculative 소급 검출.

    TS-201~209 (PLAN.md §3.2.5, TEST-SCENARIO.md §3 S-1~S-9) 계약:
    - add-page: --body-file 미실체 거부 / --force만 거부(note 필수) /
      --force+--note 우회+경고 기재 / 정상 본문 통과 / body_file 미지정 하위호환.
    - lint: speculative kind 정탐(pointail 등가) / 오탐 없음(정상 active) /
      override 페이지 비파괴(리포트 유지 + 파일 불변).
    - M-3 회귀: draft term 기본 search 제외 유지(_score_page term 한정 필터 불변).

    [MUST] mock 금지 — 실제 BT.cmd_add_page/BT.cmd_lint/BT.cmd_search를 tmpdir
    격리 상에서 직접 호출한다. KST만 _mock_kst()로 격리(기존 정책과 동형).
    """

    def setUp(self):
        super().setUp()
        self._init()

    # ── 071 fixture 헬퍼 (신규 클래스 내부 전용 — 기존 BrainTestCase 무변경) ──────

    def _write_concept_page(self, name, title, status="active", body="", sources=None):
        """concept 페이지를 직접 파일로 생성한다 (add-page 우회 — status/본문/sources 제어용).

        _write_term_page(BrainTestCase:143-165) 패턴 준용. add-page 경로를 타지 않으므로
        add-page 게이트(GREEN 구현)와 독립적으로 lint의 소급 검출(backstop)을 검증할 수 있다.
        """
        page_dir = self.brain_root / "pages" / "concept"
        page_dir.mkdir(parents=True, exist_ok=True)
        sources_yaml = BT.yaml.safe_dump(
            sources if sources is not None else [],
            allow_unicode=True, default_flow_style=True,
        ).strip()
        content = (
            f"---\n"
            f"type: concept\n"
            f"title: {title}\n"
            f"tags: []\n"
            f"sources: {sources_yaml}\n"
            f"related: []\n"
            f"created: 2026-06-17\n"
            f"updated: 2026-06-17\n"
            f"status: {status}\n"
            f"---\n\n"
            f"{body}\n"
        )
        page_path = page_dir / f"{name}.md"
        page_path.write_text(content, encoding="utf-8")
        return page_path

    def _write_body_file(self, filename, body):
        """--body-file 입력용 tmpdir 스크래치 .md 작성 (frontmatter 없음 — 본문만)."""
        body_path = self.tmpdir / filename
        body_path.write_text(body, encoding="utf-8")
        return body_path

    # ── add-page 거부 게이트 (TS-201~205 / S-1~S-5) ─────────────────────────

    def test_add_page_rejects_speculative_body_file(self):
        """TS-201/S-1: 미실체 본문(--body-file) add-page → ok:false + error=speculative_content
        + markers 비어있지 않음 + 페이지 파일 미생성."""
        body_file = self._write_body_file("spec-body.md", _SPECULATIVE_BODY_071)
        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                path="spec-reject-page", type="concept", title="미실체 개념",
                body_file=str(body_file),
            )
            exit_code, result = self._call(BT.cmd_add_page, args)

        self.assertNotEqual(exit_code, 0, f"미실체 본문이 거부되지 않음(exit=0): {result}")
        self.assertFalse(result.get("ok"), f"ok=true — 미실체 본문 거부 실패: {result}")
        self.assertEqual(
            result.get("error"), "speculative_content",
            f"error 코드가 speculative_content가 아님: {result}"
        )
        self.assertTrue(result.get("markers"), f"markers 필드가 비어있음: {result}")

        page_file = self.brain_root / "pages" / "concept" / "spec-reject-page.md"
        self.assertFalse(page_file.exists(), "거부됐어야 할 미실체 페이지 파일이 생성됨")

    def test_add_page_force_without_note_still_rejected(self):
        """TS-202/S-2: --force만(note 없음) → 여전히 ok:false (note 필수, 백도어 차단)."""
        body_file = self._write_body_file("spec-body-force-only.md", _SPECULATIVE_BODY_071)
        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                path="spec-force-only-page", type="concept", title="미실체 개념 force만",
                body_file=str(body_file), force=True, note=None,
            )
            exit_code, result = self._call(BT.cmd_add_page, args)

        self.assertNotEqual(
            exit_code, 0,
            f"--force만으로(note 없이) 통과됨 — 백도어 우회 발생: {result}"
        )
        self.assertFalse(
            result.get("ok"),
            f"ok=true — --force만으로 note 없이 우회됨(백도어): {result}"
        )

        page_file = self.brain_root / "pages" / "concept" / "spec-force-only-page.md"
        self.assertFalse(page_file.exists(), "note 없는 force 우회로 페이지가 생성됨(백도어)")

    def test_add_page_force_with_note_overrides_and_records(self):
        """TS-203/S-3: --force --note '<사유>' → ok:true + warning/speculative_markers/
        override_note 응답 + 생성 페이지 frontmatter에 speculative_override:true·override_note 기록."""
        body_file = self._write_body_file("spec-body-override.md", _SPECULATIVE_BODY_071)
        override_note = "캡틴 승인 — 설계 기록 목적 사전 등록"
        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                path="spec-override-page", type="concept", title="미실체 개념 override",
                body_file=str(body_file), force=True, note=override_note,
            )
            exit_code, result = self._call(BT.cmd_add_page, args)

        self.assertEqual(exit_code, 0, f"--force --note 우회가 실패함: {result}")
        self.assertTrue(result.get("ok"), f"ok=false — --force --note 우회 실패: {result}")
        self.assertIn("warning", result, f"응답에 warning 필드 없음: {result}")
        self.assertIn("speculative_markers", result, f"응답에 speculative_markers 필드 없음: {result}")
        self.assertEqual(
            result.get("override_note"), override_note,
            f"응답 override_note 불일치: {result}"
        )

        page_file = self.brain_root / "pages" / "concept" / "spec-override-page.md"
        self.assertTrue(page_file.exists(), "override 통과했는데 페이지 파일이 생성되지 않음")
        fm, _ = BT.parse_frontmatter(page_file.read_text(encoding="utf-8"))
        self.assertIsNotNone(fm, "override 페이지 frontmatter 파싱 실패")
        self.assertTrue(
            fm.get("speculative_override"),
            f"frontmatter에 speculative_override:true 기록 안 됨: {fm}"
        )
        self.assertEqual(
            fm.get("override_note"), override_note,
            f"frontmatter override_note 불일치: {fm}"
        )

    def test_add_page_normal_body_file_passes(self):
        """TS-204/S-4: 정상 concept 본문(마커 0, 산문 '향후' 단순 언급 포함) --body-file
        → ok:true, 거부 없음 (H-1 오탐 방어 회귀)."""
        body_file = self._write_body_file("clean-body.md", _NORMAL_BODY_071)
        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                path="normal-body-page", type="concept", title="정상 개념",
                body_file=str(body_file),
            )
            exit_code, result = self._call(BT.cmd_add_page, args)

        self.assertEqual(exit_code, 0, f"정상 본문이 거부됨(오검출 발생): {result}")
        self.assertTrue(result.get("ok"), f"ok=false — 정상 본문 오검출: {result}")

        page_file = self.brain_root / "pages" / "concept" / "normal-body-page.md"
        self.assertTrue(page_file.exists(), "정상 본문 페이지가 생성되지 않음")

    def test_add_page_without_body_file_backward_compat(self):
        """TS-205/S-5: body_file=None(기존 호출) → 템플릿 본문으로 정상 생성 ok:true
        (하위호환 — 마커 스캔이 템플릿에 미발동)."""
        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                path="legacy-page", type="concept", title="레거시 호출",
            )
            exit_code, result = self._call(BT.cmd_add_page, args)

        self.assertEqual(exit_code, 0, f"body_file 미지정 기존 호출이 회귀됨: {result}")
        self.assertTrue(result.get("ok"), f"ok=false — 하위호환 회귀: {result}")
        page_file = self.brain_root / "pages" / "concept" / "legacy-page.md"
        self.assertTrue(page_file.exists(), "하위호환 경로에서 페이지가 생성되지 않음")

    # ── lint 소급 검출 (TS-206~208 / S-6~S-8) ────────────────────────────────

    def test_lint_detects_speculative_concept_page(self):
        """TS-206/S-6: pointail 등가 fixture(concept/active + 미실체 헤딩) 직접 write
        → lint issues에 {"kind":"speculative","page":...,"markers":[...]} 포함."""
        self._write_concept_page(
            "pointail-equiv", "포인테일 등가 개념", status="active",
            body=_SPECULATIVE_BODY_071, sources=["task:071"],
        )
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            exit_code, result = self._call(BT.cmd_lint, args)

        self.assertEqual(exit_code, 0, f"lint 실행 실패: {result}")
        speculative_issues = [
            i for i in result.get("issues", []) if i.get("kind") == "speculative"
        ]
        self.assertTrue(
            speculative_issues,
            f"미실체 fixture에서 speculative kind가 검출되지 않음: {result.get('issues')}"
        )
        matching = [i for i in speculative_issues if i.get("page") == "pointail-equiv"]
        self.assertTrue(
            matching,
            f"pointail-equiv 페이지에 대한 speculative 이슈가 없음: {speculative_issues}"
        )
        self.assertTrue(matching[0].get("markers"), f"speculative 이슈 markers 필드 비어있음: {matching[0]}")

    def test_lint_no_false_positive_on_normal_concept(self):
        """TS-207/S-7: 정상 active concept(마커 0) → lint issues에 speculative 미출현
        (기존 kind는 정상 동작 — H-4 오탐측 회귀)."""
        self._write_concept_page(
            "normal-active-concept", "정상 활성 개념", status="active",
            body=_NORMAL_BODY_071, sources=["task:071"],
        )
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            exit_code, result = self._call(BT.cmd_lint, args)

        self.assertEqual(exit_code, 0, f"lint 실행 실패: {result}")
        page_issues = [
            i for i in result.get("issues", []) if i.get("page") == "normal-active-concept"
        ]
        kinds = [i.get("kind") for i in page_issues]
        self.assertNotIn(
            "speculative", kinds,
            f"정상 active concept에서 speculative가 오검출됨: {page_issues}"
        )

    def test_lint_override_page_still_reported_and_unchanged(self):
        """TS-208/S-8: speculative_override:true 페이지 → lint가 여전히 리포트하되
        페이지 파일 내용은 lint 실행 전후 불변(자동 삭제·수정 0 — 비파괴 제약)."""
        page_path = self._write_concept_page(
            "override-existing", "override 기재된 개념", status="active",
            body=_SPECULATIVE_BODY_071, sources=["task:071"],
        )
        # override 플래그를 frontmatter에 직접 주입 (add-page override 경로와 독립적으로
        # lint의 비파괴·리포트 유지 계약만 검증하기 위한 fixture 조작)
        text = page_path.read_text(encoding="utf-8")
        fm, body = BT.parse_frontmatter(text)
        fm["speculative_override"] = True
        fm["override_note"] = "캡틴 승인 — 사전 기재"
        fm_yaml = BT.yaml.safe_dump(
            fm, allow_unicode=True, sort_keys=False, default_flow_style=False
        ).strip()
        page_path.write_text(f"---\n{fm_yaml}\n---\n{body}", encoding="utf-8")

        before_bytes = page_path.read_bytes()
        with _mock_kst():
            args = make_args(brain_path=str(self.brain_root))
            exit_code, result = self._call(BT.cmd_lint, args)
        after_bytes = page_path.read_bytes()

        self.assertEqual(exit_code, 0, f"lint 실행 실패: {result}")
        speculative_issues = [
            i for i in result.get("issues", [])
            if i.get("kind") == "speculative" and i.get("page") == "override-existing"
        ]
        self.assertTrue(
            speculative_issues,
            f"override 페이지가 lint에서 여전히 리포트돼야 하는데 누락됨: {result.get('issues')}"
        )
        self.assertEqual(
            before_bytes, after_bytes,
            "lint 실행 후 override 페이지 파일 내용이 변경됨 — 비파괴 제약 위반(자동 삭제·수정 금지)"
        )

    # ── M-3 draft-term 불변 회귀 (TS-209 / S-9) ──────────────────────────────

    def test_search_draft_term_excluded_default_m3_regression(self):
        """TS-209/S-9: status:draft term 페이지가 기본 search(include_draft=False)에서
        제외 유지 — _score_page term 한정 draft 필터([R-6] 2026-06-17 결정) 불변 회귀."""
        self._write_term_page("m3-draft-term", "M3불변용어", status="draft")
        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root), query="M3불변용어",
                type=None, include_draft=False,
            )
            exit_code, result = self._call(BT.cmd_search, args)

        self.assertEqual(exit_code, 0, f"search 실행 실패: {result}")
        matches = result.get("matches", [])
        draft_term_matches = [m for m in matches if "m3-draft-term" in m.get("page", "")]
        self.assertEqual(
            draft_term_matches, [],
            f"draft term 페이지가 기본 search에 노출됨 — M-3 회귀 발생: {draft_term_matches}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
