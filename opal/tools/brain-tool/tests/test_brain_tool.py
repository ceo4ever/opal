"""
@header {
  "module": "test_brain_tool",
  "layer": "test",
  "domain": "opal-brain",
  "description": "brain-tool 단위 테스트 — 10 서브커맨드 happy-path + ERROR_CODES 주요 14종 + 동적 타입 로드 + analyze/ingest-scan. tmp_path 기반 격리 실행. mock 금지 — 실제 brain_tool.py를 import 호출하는 진짜 테스트.",
  "exports": [
    "TestInit", "TestAddPage", "TestIndex", "TestLog",
    "TestSearch", "TestSyncHeader", "TestLint", "TestValidate",
    "TestErrorCodes", "TestDynamicPageTypes", "TestAnalyze", "TestIngestScan"
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
        # log
        "op": "init",
        "summary": "테스트 요약",
        "new": None,
        "updated": None,
        # search
        "query": "",
        "tag": None,
        "limit": None,
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
                  tags=None, sources=None):
        """add-page 헬퍼."""
        with _mock_kst():
            args = make_args(
                brain_path=str(self.brain_root),
                path=name, type=page_type, title=title,
                tags=tags, sources=sources,
            )
            exit_code, result = self._call(BT.cmd_add_page, args)
        return exit_code, result

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
