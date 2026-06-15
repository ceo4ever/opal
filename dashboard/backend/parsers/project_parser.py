"""
@header {
  "module": "parsers.project_parser",
  "layer": "service",
  "domain": "console",
  "description": "PROJECT.md·AGENT.md 메타(PM프로필·기술스택·문서) 파싱. docs/ 디렉토리 실제 스캔으로 문서 목록 반환. 읽기 전용 — open(read)만 사용, mtime 불변(H-6)",
  "exports": ["parse_project"],
  "depends": []
}
"""
from __future__ import annotations

import os
import re


def parse_project(project_path: str) -> dict:
    """PROJECT.md·AGENT.md 파싱 → ProjectDetail dict.

    Args:
        project_path: 프로젝트 루트 경로 (읽기 전용 접근)

    Returns:
        {
            "name": str,             # 프로젝트 이름 (디렉토리명)
            "path": str,
            "pm_profile": dict,      # AGENT.md 메타 (역할·페르소나 등)
            "agent_md": str,         # AGENT.md 원문
            "project_md": str,       # PROJECT.md 원문
            "tech_stack": list[str], # 기술스택 목록
            "docs": list[dict],      # 문서 목록
        }

    파싱 실패 시 graceful — 최소 구조 반환.
    mtime 불변 보장 — open(mode='r')만 사용.
    """
    try:
        return _do_parse(project_path)
    except Exception as exc:
        return {
            "name": os.path.basename(project_path),
            "path": project_path,
            "pm_profile": {},
            "agent_md": "",
            "project_md": "",
            "tech_stack": [],
            "docs": [],
            "warning": f"project 파싱 실패: {exc}",
        }


def _read_file(path: str) -> str:
    """읽기 전용 파일 읽기 — open(mode='r')만 사용"""
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def _parse_agent_md(content: str) -> dict:
    """AGENT.md 에서 PM 프로필 메타 추출.

    - YAML frontmatter의 name/description 필드
    - ## 역할 / ## 페르소나 / ## 금지사항 섹션
    """
    if not content:
        return {}

    profile: dict = {}

    # YAML frontmatter 추출 (--- ... ---)
    fm_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        for line in fm.splitlines():
            m = re.match(r"^(\w+):\s*(.+)$", line)
            if m:
                profile[m.group(1)] = m.group(2).strip()

    # 섹션 헤딩 파싱
    sections_found: list[str] = re.findall(r"^## (.+)$", content, re.MULTILINE)
    profile["sections"] = sections_found

    return profile


def _extract_tech_stack(project_md: str) -> list[str]:
    """PROJECT.md 에서 기술스택 목록 추출.

    ## 기술스택 또는 ## Tech Stack 섹션 하위 - 항목 파싱.
    """
    if not project_md:
        return []

    tech: list[str] = []
    in_section = False

    for line in project_md.splitlines():
        if re.match(r"^##\s+(기술스택|Tech Stack|기술 스택)", line):
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            m = re.match(r"^\s*[-*]\s+(.+)$", line)
            if m:
                tech.append(m.group(1).strip())

    return tech


def _scan_docs_dir(project_path: str) -> list[dict]:
    """docs/ 디렉토리의 *.md 파일을 실제 스캔하여 목록 반환.

    fragile한 PROJECT.md 표 파싱 대신 파일시스템 직접 스캔으로 교체(Task 021).
    읽기 전용 — os.listdir만 사용, 파일 내용 미접근.

    Returns:
        [{"title": "ARCHITECTURE.md", "path": "ARCHITECTURE.md"}, ...]
        title과 path 모두 파일명(basename) — /api/projects/doc?name= 파라미터와 1:1 대응.
    """
    docs_dir = os.path.join(project_path, "docs")
    if not os.path.isdir(docs_dir):
        return []

    docs: list[dict] = []
    try:
        for filename in sorted(os.listdir(docs_dir)):
            if filename.lower().endswith(".md") and not filename.startswith("."):
                docs.append({"title": filename, "path": filename})
    except OSError:
        pass

    return docs


def _do_parse(project_path: str) -> dict:
    name = os.path.basename(project_path)

    agent_md_path = os.path.join(project_path, ".opal", "AGENT.md")
    project_md_path = os.path.join(project_path, "docs", "PROJECT.md")

    agent_md_content = _read_file(agent_md_path)
    project_md_content = _read_file(project_md_path)

    pm_profile = _parse_agent_md(agent_md_content)
    tech_stack = _extract_tech_stack(project_md_content)
    docs = _scan_docs_dir(project_path)

    return {
        "name": name,
        "path": project_path,
        "pm_profile": pm_profile,
        "agent_md": agent_md_content,
        "project_md": project_md_content,
        "tech_stack": tech_stack,
        "docs": docs,
    }
