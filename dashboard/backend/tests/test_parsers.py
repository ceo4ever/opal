"""
@header {
  "module": "test_parsers",
  "layer": "test",
  "domain": "console",
  "description": "마크다운 파서 RED-first 테스트 — S-4 시나리오 (L2/M1). 실 파일 + mtime 불변 검증",
  "exports": ["[T021/L2-R3] test_memory_parser_returns_structure", "[T021/L2-R3] test_memory_parser_mtime_invariant", "[T021/L2-R3] test_memory_file_parser", "[T021/L2-R3] test_project_parser", "[T021/L2-R3] test_markdown_reader"],
  "depends": ["parsers.memory_parser", "parsers.memory_file_parser", "parsers.project_parser", "parsers.markdown_reader"]
}
"""
import os
import pytest
from pathlib import Path


# ─── 실 프로젝트 경로 ─────────────────────────────────────────
AI_FRAMEWORK_ROOT = Path(__file__).parents[3]
MEMORY_MD = AI_FRAMEWORK_ROOT / ".opal" / "MEMORY.md"
MEMORY_DIR = AI_FRAMEWORK_ROOT / ".opal" / "memory"
PROJECT_MD = AI_FRAMEWORK_ROOT / "docs" / "PROJECT.md"
AGENT_MD = AI_FRAMEWORK_ROOT / ".opal" / "AGENT.md"


# ─── memory_parser ────────────────────────────────────────────
def test_memory_parser_returns_structure() -> None:
    """[T021/L2-R3] MEMORY.md → rows/history 구조화 dict 반환"""
    if not MEMORY_MD.exists():
        pytest.skip("MEMORY.md 없음")

    from dashboard.backend.parsers.memory_parser import parse_memory_index

    content = MEMORY_MD.read_text(encoding="utf-8")
    result = parse_memory_index(content)

    assert isinstance(result, dict), "dict 반환 필요"
    assert "rows" in result, "'rows' 키 필요"
    assert "history" in result, "'history' 키 필요"
    assert isinstance(result["rows"], list)
    assert isinstance(result["history"], list)


def test_memory_parser_rows_have_fields() -> None:
    """[T021/L2-R3] rows 항목이 date/category/status/file/description 필드 보유"""
    if not MEMORY_MD.exists():
        pytest.skip("MEMORY.md 없음")

    from dashboard.backend.parsers.memory_parser import parse_memory_index

    content = MEMORY_MD.read_text(encoding="utf-8")
    result = parse_memory_index(content)

    if result["rows"]:
        row = result["rows"][0]
        for field in ("date", "category", "status", "file", "description"):
            assert field in row, f"rows 항목에 '{field}' 필드 없음"


def test_memory_parser_history_have_fields() -> None:
    """[T021/L2-R3] history 항목이 date/task/stage/path 필드 보유"""
    if not MEMORY_MD.exists():
        pytest.skip("MEMORY.md 없음")

    from dashboard.backend.parsers.memory_parser import parse_memory_index

    content = MEMORY_MD.read_text(encoding="utf-8")
    result = parse_memory_index(content)

    if result["history"]:
        hist = result["history"][0]
        for field in ("date", "task", "stage", "path"):
            assert field in hist, f"history 항목에 '{field}' 필드 없음"


def test_memory_parser_mtime_invariant() -> None:
    """[T021/L2-R3] MEMORY.md 파서 호출 전후 mtime 불변 (읽기 전용)"""
    if not MEMORY_MD.exists():
        pytest.skip("MEMORY.md 없음")

    from dashboard.backend.parsers.memory_parser import parse_memory_index

    mtime_before = os.path.getmtime(str(MEMORY_MD))
    content = MEMORY_MD.read_text(encoding="utf-8")
    parse_memory_index(content)
    mtime_after = os.path.getmtime(str(MEMORY_MD))

    assert mtime_before == mtime_after, "MEMORY.md mtime이 변경됨 (읽기 전용 위반)"


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
