"""
@header {
  "module": "test_parsers",
  "layer": "test",
  "domain": "console",
  "description": "파서 RED-first 테스트 — S-4 시나리오 (L2/M1). memory_parser는 078 F-009 JSON 전환 — fixture_doc_populated.json 원본 대조로 재작성(H-5: 현행 오프바이원 출력을 기준선으로 잡지 않음). 그 외 파서는 실 파일 + mtime 불변 검증",
  "exports": ["[T021/L2-R3] test_memory_parser_returns_structure", "[T021/L2-R3] test_memory_parser_mtime_invariant", "[T021/L2-R3] test_memory_file_parser", "[T021/L2-R3] test_project_parser", "[T021/L2-R3] test_markdown_reader"],
  "depends": ["parsers.memory_parser", "parsers.memory_file_parser", "parsers.project_parser", "parsers.markdown_reader"],
  "task": "078",
  "changelog": [
    "2026-07-28 T078 F-009: memory_parser 관련 4건(returns_structure/rows_have_fields/history_have_fields/mtime_invariant)을 MEMORY.json 원본(fixture_doc_populated.json) 1:1 대조 기준으로 재작성 — H-5 오프바이원 해소 검증"
  ]
}
"""
import json
import os
import pytest
from pathlib import Path


# ─── 실 프로젝트 경로 ─────────────────────────────────────────
AI_FRAMEWORK_ROOT = Path(__file__).parents[3]
MEMORY_MD = AI_FRAMEWORK_ROOT / ".opal" / "MEMORY.md"
MEMORY_DIR = AI_FRAMEWORK_ROOT / ".opal" / "memory"
PROJECT_MD = AI_FRAMEWORK_ROOT / "docs" / "PROJECT.md"
AGENT_MD = AI_FRAMEWORK_ROOT / ".opal" / "AGENT.md"

# memory_parser 테스트 전용 — MEMORY.json 원본 대조 픽스처 (읽기 전용, 수정 금지)
MEMORY_JSON_FIXTURE = (
    AI_FRAMEWORK_ROOT
    / "opal"
    / "tools"
    / "memory-tool"
    / "tests"
    / "fixtures"
    / "fixture_doc_populated.json"
)


# ─── memory_parser (078 F-009 — JSON 원본 대조, H-5) ──────────
def test_memory_parser_returns_structure() -> None:
    """[T021/L2-R3][078 F-009] MEMORY.json → rows/history 구조화 dict 반환. 헤더 행 유입 없음(H-5)"""
    if not MEMORY_JSON_FIXTURE.exists():
        pytest.skip("fixture_doc_populated.json 없음")

    from dashboard.backend.parsers.memory_parser import parse_memory_index

    content = MEMORY_JSON_FIXTURE.read_text(encoding="utf-8")
    source = json.loads(content)
    result = parse_memory_index(content)

    assert isinstance(result, dict), "dict 반환 필요"
    assert "rows" in result, "'rows' 키 필요"
    assert "history" in result, "'history' 키 필요"
    assert isinstance(result["rows"], list)
    assert isinstance(result["history"], list)
    # 오프바이원 해소 확인: 행 수가 원본 memories/history 개수와 정확히 일치(헤더 행 유입 0건)
    assert len(result["rows"]) == len(source["memories"])
    assert len(result["history"]) == len(source["history"])


def test_memory_parser_rows_have_fields() -> None:
    """[T021/L2-R3][078 F-009] rows 항목이 MEMORY.json memories[] 원본과 1:1 일치(date/category/status/file/description/title)"""
    if not MEMORY_JSON_FIXTURE.exists():
        pytest.skip("fixture_doc_populated.json 없음")

    from dashboard.backend.parsers.memory_parser import parse_memory_index

    content = MEMORY_JSON_FIXTURE.read_text(encoding="utf-8")
    source = json.loads(content)
    result = parse_memory_index(content)

    assert result["rows"], "rows가 비어있으면 안 됨(fixture에 6건 존재)"
    for row, mem in zip(result["rows"], source["memories"]):
        assert row["date"] == mem["date"]
        assert row["category"] == mem["type"], "category는 memories[].type 매핑"
        assert row["status"] == mem["status"]
        assert row["file"] == mem["file"], "오프바이원 해소 — file이 밀리지 않음"
        assert row["description"] == mem["summary"], "description은 memories[].summary 매핑"
        assert row["title"] == mem["title"], "title은 additive 신필드"


def test_memory_parser_history_have_fields() -> None:
    """[T021/L2-R3][078 F-009] history 항목이 MEMORY.json history[] 원본과 1:1 일치(date/task/stage/path/result)"""
    if not MEMORY_JSON_FIXTURE.exists():
        pytest.skip("fixture_doc_populated.json 없음")

    from dashboard.backend.parsers.memory_parser import parse_memory_index

    content = MEMORY_JSON_FIXTURE.read_text(encoding="utf-8")
    source = json.loads(content)
    result = parse_memory_index(content)

    assert result["history"], "history가 비어있으면 안 됨(fixture에 항목 존재)"
    for hist, h in zip(result["history"], source["history"]):
        assert hist["date"] == h["date"]
        assert hist["task"] == h["title"], "task는 history[].title 매핑"
        assert hist["stage"] == h["stage"]
        assert hist["path"] == h["path"]
        assert hist["result"] == h["result"], "result는 additive 신필드"
        assert hist["start"] is None, "구 6컬럼 유물 — 대응 필드 없어 항상 None"
        assert hist["end"] is None


def test_memory_parser_mtime_invariant() -> None:
    """[T021/L2-R3][078 F-009] MEMORY.json 파서 호출 전후 mtime 불변 (읽기 전용, json.loads만 사용)"""
    if not MEMORY_JSON_FIXTURE.exists():
        pytest.skip("fixture_doc_populated.json 없음")

    from dashboard.backend.parsers.memory_parser import parse_memory_index

    mtime_before = os.path.getmtime(str(MEMORY_JSON_FIXTURE))
    content = MEMORY_JSON_FIXTURE.read_text(encoding="utf-8")
    parse_memory_index(content)
    mtime_after = os.path.getmtime(str(MEMORY_JSON_FIXTURE))

    assert mtime_before == mtime_after, "MEMORY.json mtime이 변경됨 (읽기 전용 위반)"


# ─── memory_file_parser ───────────────────────────────────────
def test_memory_file_parser_returns_meta(tmp_path: Path) -> None:
    """[T021/L2-R3] memory/*.md 블록쿼트 메타 파싱"""
    md_file = tmp_path / "test_memory.md"
    md_file.write_text(
        "# 테스트 메모리\n\n> 등록일: 2026-06-15 | 카테고리: preferences | 등록 태스크: 021\n\n## 요지\n\n내용\n",
        encoding="utf-8",
    )

    from dashboard.backend.parsers.memory_file_parser import parse_memory_file

    result = parse_memory_file(str(md_file))
    assert isinstance(result, dict), "dict 반환 필요"


def test_memory_file_parser_mtime_invariant(tmp_path: Path) -> None:
    """[T021/L2-R3] memory file 파서 호출 후 mtime 불변"""
    md_file = tmp_path / "test_memory.md"
    md_file.write_text("# test\n\n> key: value\n", encoding="utf-8")

    from dashboard.backend.parsers.memory_file_parser import parse_memory_file

    mtime_before = os.path.getmtime(str(md_file))
    parse_memory_file(str(md_file))
    mtime_after = os.path.getmtime(str(md_file))

    assert mtime_before == mtime_after, "memory file mtime 변경됨"


# ─── project_parser ───────────────────────────────────────────
def test_project_parser_returns_detail() -> None:
    """[T021/L2-R3] PROJECT.md/AGENT.md 파싱 → ProjectDetail 구조"""
    if not AGENT_MD.exists():
        pytest.skip("AGENT.md 없음")

    from dashboard.backend.parsers.project_parser import parse_project

    result = parse_project(str(AI_FRAMEWORK_ROOT))
    assert isinstance(result, dict), "dict 반환 필요"
    # 최소 필드 확인
    assert "name" in result or "agent_md" in result or "pm_profile" in result


def test_project_parser_mtime_invariant() -> None:
    """[T021/L2-R3] project_parser 호출 전후 AGENT.md mtime 불변"""
    if not AGENT_MD.exists():
        pytest.skip("AGENT.md 없음")

    from dashboard.backend.parsers.project_parser import parse_project

    mtime_before = os.path.getmtime(str(AGENT_MD))
    parse_project(str(AI_FRAMEWORK_ROOT))
    mtime_after = os.path.getmtime(str(AGENT_MD))

    assert mtime_before == mtime_after, "AGENT.md mtime 변경됨 (읽기 전용 위반)"


# ─── markdown_reader ──────────────────────────────────────────
def test_markdown_reader_returns_content(tmp_path: Path) -> None:
    """[T021/L2-R3] .md 파일 원문 read → str 반환"""
    md_file = tmp_path / "TASK.md"
    md_file.write_text("# Task\n\n내용입니다.\n", encoding="utf-8")

    from dashboard.backend.parsers.markdown_reader import read_markdown

    content = read_markdown(str(md_file))
    assert isinstance(content, str), "str 반환 필요"
    assert "Task" in content


def test_markdown_reader_mtime_invariant(tmp_path: Path) -> None:
    """[T021/L2-R3] markdown_reader 호출 후 mtime 불변"""
    md_file = tmp_path / "PLAN.md"
    md_file.write_text("# Plan\n", encoding="utf-8")

    from dashboard.backend.parsers.markdown_reader import read_markdown

    mtime_before = os.path.getmtime(str(md_file))
    read_markdown(str(md_file))
    mtime_after = os.path.getmtime(str(md_file))

    assert mtime_before == mtime_after, "markdown_reader가 파일 mtime 변경함"


def test_markdown_reader_nonexistent_file() -> None:
    """[T021/L2-R3] 존재하지 않는 파일 → None 또는 빈 문자열 반환 (예외 전파 없음)"""
    from dashboard.backend.parsers.markdown_reader import read_markdown

    result = read_markdown("/nonexistent/path/file.md")
    assert result is None or result == "", f"예외 전파 없이 None/빈 문자열 반환 필요: {result!r}"


def test_all_parsers_mtime_invariant_real_files() -> None:
    """[T021/L2-R3] 실 ai-framework 파일 전체 파서 호출 후 mtime 모두 불변 (H-6)"""
    real_files = []
    for path in [MEMORY_MD, AGENT_MD, PROJECT_MD]:
        if path.exists():
            real_files.append(path)

    if not real_files:
        pytest.skip("실 파일 없음")

    mtimes_before = {str(f): os.path.getmtime(str(f)) for f in real_files}

    # memory_parser
    if MEMORY_MD.exists():
        from dashboard.backend.parsers.memory_parser import parse_memory_index
        parse_memory_index(MEMORY_MD.read_text(encoding="utf-8"))

    # project_parser
    if AGENT_MD.exists():
        from dashboard.backend.parsers.project_parser import parse_project
        parse_project(str(AI_FRAMEWORK_ROOT))

    # markdown_reader
    if PROJECT_MD.exists():
        from dashboard.backend.parsers.markdown_reader import read_markdown
        read_markdown(str(PROJECT_MD))

    mtimes_after = {str(f): os.path.getmtime(str(f)) for f in real_files}

    for path_str in mtimes_before:
        assert mtimes_before[path_str] == mtimes_after[path_str], (
            f"mtime 변경됨: {path_str}"
        )
