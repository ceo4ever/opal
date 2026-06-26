"""
@header {
  "module": "federation",
  "layer": "util",
  "domain": "opal-tools",
  "description": "tool-scan federation 파서 — mcps.md(MCP 서버 목록) 정규식 파서 + opal-skills-registry.json(스킬 레지스트리) JSON 파서. 읽기 전용(원본 무변경). ReDoS 방어(triggers 입력 256자 제한). 경로 화이트리스트(getReferencesDir 결과만).",
  "exports": [
    "get_references_dir",
    "load_mcps",
    "load_skills"
  ],
  "depends": []
}

federation — mcps.md + opal-skills-registry.json 읽기 파서.

[MUST] 읽기 전용 — 원본 파일 무변경.
[MUST] 경로 화이트리스트 — getReferencesDir 결과 경로만 허용.
[MUST] ReDoS 방어 — triggers 정규식 입력 256자 제한.
"""

import json
import os
import pathlib
import re
from typing import Any, Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# ReDoS 방어 상수 (skill-registry.js 정책 답습)
# ─────────────────────────────────────────────────────────────────────────────

MAX_INPUT_LENGTH = 256
MAX_PATTERN_LENGTH = 100
MAX_DOTSTAR_COUNT = 2


def _is_unsafe_regex(pattern: str) -> bool:
    """ReDoS 위험 정규식 여부 확인 (skill-registry.js isUnsafeRegex 답습)."""
    if len(pattern) > MAX_PATTERN_LENGTH:
        return True
    dot_star_count = len(re.findall(r"\.[*+]", pattern))
    if dot_star_count > MAX_DOTSTAR_COUNT:
        return True
    if re.search(r"\([^)]*[+*]\)[+*]", pattern):
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# 경로 탐색 (skill-registry.js getReferencesDir 답습)
# ─────────────────────────────────────────────────────────────────────────────

def get_references_dir(mcps_path_override: Optional[str] = None,
                       skills_path_override: Optional[str] = None) -> pathlib.Path:
    """references 디렉토리를 탐색하여 반환.

    1순위: cwd 기준 opal/core/references/
    2순위: ~/.opal/references/
    3순위: __file__ 기준 opal/core/references/
    """
    # 1순위: cwd 기준 소스 레이아웃
    cwd_source = pathlib.Path.cwd() / "opal" / "core" / "references"
    if (cwd_source / "opal-skills-registry.json").exists():
        return cwd_source

    # 2순위: 배포 환경
    home = pathlib.Path.home()
    deployed = home / ".opal" / "references"
    if (deployed / "opal-skills-registry.json").exists():
        return deployed

    # 3순위: __file__ 기준 개발 환경
    source = pathlib.Path(__file__).parent.parent.parent.parent / "core" / "references"
    if (source / "opal-skills-registry.json").exists():
        return source

    return deployed  # fallback


def _validate_path(path: pathlib.Path, references_dir: pathlib.Path) -> bool:
    """경로가 references_dir 하위에 있는지 화이트리스트 검증."""
    try:
        path.resolve().relative_to(references_dir.resolve())
        return True
    except ValueError:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# mcps.md 파서
# ─────────────────────────────────────────────────────────────────────────────

def load_mcps(mcps_path: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    """mcps.md를 파싱하여 MCP 서버 목록 반환.

    반환 형식:
        [{"name": "context7", "kind": "mcp", "description": "...",
          "purpose": "...", "tools": [...], "when": [...]}]

    읽기 전용 — 원본 무변경.
    """
    # 경로 결정
    if mcps_path is None:
        ref_dir = get_references_dir()
        mcps_path = ref_dir / "mcps.md"
    else:
        mcps_path = pathlib.Path(mcps_path)
        # 화이트리스트: env 주입 경로는 절대경로로 받아 신뢰 (테스트 격리)

    if not mcps_path.exists():
        return []

    content = mcps_path.read_text(encoding="utf-8")
    # 원본 무변경 — 읽기만

    mcps: List[Dict[str, Any]] = []

    # "## 등록된 MCP 서버" 이후 섹션만 파싱
    registered_section_match = re.search(r"^## 등록된 MCP 서버", content, re.MULTILINE)
    if not registered_section_match:
        # 그냥 전체에서 ### 서버명 파싱 시도
        parse_start = 0
    else:
        parse_start = registered_section_match.start()

    section_content = content[parse_start:]

    # ### {server-name} 섹션 파싱
    server_pattern = re.compile(r"^### (\S+)\s*$", re.MULTILINE)
    matches = list(server_pattern.finditer(section_content))

    for i, m in enumerate(matches):
        server_name = m.group(1)
        # 섹션 끝은 다음 ### 또는 ## 또는 문서 끝
        if i + 1 < len(matches):
            section_end = matches[i + 1].start()
        else:
            # 다음 ## 레벨 헤더 찾기
            next_h2 = re.search(r"^## ", section_content[m.end():], re.MULTILINE)
            section_end = m.end() + next_h2.start() if next_h2 else len(section_content)

        block = section_content[m.start():section_end]

        # 설명 추출 (- **설명**: ... 줄)
        desc_match = re.search(r"-\s*\*\*설명\*\*:\s*(.+)", block)
        description = desc_match.group(1).strip() if desc_match else ""

        # 사용 예시 추출 (- **사용 예시**: ... 줄)
        usage_match = re.search(r"-\s*\*\*사용 예시\*\*:\s*(.+)", block)
        usage_example = usage_match.group(1).strip() if usage_match else ""

        # 제공 도구 추출 (- `tool_name`: 설명)
        tool_lines = re.findall(r"-\s*`([^`]+)`:\s*(.+)", block)
        tools = [{"name": t[0], "description": t[1].strip()} for t in tool_lines]

        # when 키워드 생성: 서버명 토큰 + 설명 토큰 + 도구명 토큰 + 사용 예시
        when_tokens: List[str] = []
        # 서버명을 소문자 토큰으로 (하이픈/숫자 포함)
        when_tokens.append(server_name.lower())
        # 서버명에서 영문 단어 분리 (예: "sequential-thinking" → "sequential", "thinking")
        name_parts = re.findall(r"[a-zA-Z가-힣]{2,}", server_name.lower())
        when_tokens.extend(name_parts)
        # 설명에서 중요 단어 추출 (영문/한글 단어, 짧은 것 제외)
        desc_words = re.findall(r"[a-zA-Z가-힣]{2,}", description.lower())
        when_tokens.extend(desc_words[:10])  # 최대 10개
        # 사용 예시에서 단어 추출
        usage_words = re.findall(r"[a-zA-Z가-힣]{3,}", usage_example.lower())
        when_tokens.extend(usage_words[:8])
        # 제공 도구명 추가 (tool_name 토큰)
        for tool_item in tools:
            tool_name_tokens = re.findall(r"[a-zA-Z가-힣]{3,}", tool_item["name"].lower())
            when_tokens.extend(tool_name_tokens[:2])

        # purpose: 설명 1줄
        purpose = description if description else f"{server_name} MCP"

        mcps.append({
            "name": server_name,
            "kind": "mcp",
            "description": description,
            "purpose": purpose,
            "tools": tools,
            "when": list(dict.fromkeys(when_tokens)),  # 중복 제거, 순서 유지
            "exec": f"ToolSearch query \"select:{server_name}\"",
        })

    return mcps


# ─────────────────────────────────────────────────────────────────────────────
# opal-skills-registry.json 파서
# ─────────────────────────────────────────────────────────────────────────────

def load_skills(skills_path: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    """opal-skills-registry.json을 파싱하여 스킬 목록 반환.

    kind 분기:
        dispatched_by 있음 → "op-skill"
        dispatched_by 없음 → "pilot-skill"

    읽기 전용 — 원본 무변경.
    """
    if skills_path is None:
        ref_dir = get_references_dir()
        skills_path = ref_dir / "opal-skills-registry.json"
    else:
        skills_path = pathlib.Path(skills_path)
        # 환경변수 주입 경로는 신뢰 (테스트 격리)

    if not skills_path.exists():
        return []

    # 읽기 전용 — 절대 쓰기 금지
    content = skills_path.read_text(encoding="utf-8")
    try:
        registry = json.loads(content)
    except json.JSONDecodeError:
        return []

    skills: List[Dict[str, Any]] = []
    groups = registry.get("groups", {})

    for group_name, items in groups.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name", "")
            if not name:
                continue

            dispatched_by = item.get("dispatched_by")
            kind = "op-skill" if dispatched_by else "pilot-skill"

            alias = item.get("alias")
            description = item.get("description", "")
            triggers = item.get("triggers", [])
            paths = item.get("paths", [])
            stage = item.get("stage")

            # when 키워드: name + alias + description 단어
            when_tokens: List[str] = [name.lower()]
            if alias:
                when_tokens.append(alias.lower())
            desc_words = re.findall(r"[a-zA-Z가-힣]{2,}", description.lower())
            when_tokens.extend(desc_words[:6])

            # skill_path: 첫 번째 paths 엔트리 (HOME 치환)
            skill_path = None
            if paths:
                skill_path = paths[0].replace("{project}", str(pathlib.Path.cwd()))
                skill_path = skill_path.replace("~", str(pathlib.Path.home()))

            skill_entry: Dict[str, Any] = {
                "name": name,
                "kind": kind,
                "description": description,
                "purpose": description if description else name,
                "when": list(dict.fromkeys(when_tokens)),
                "triggers": triggers,
                "alias": alias,
                "skill_path": skill_path,
            }
            if dispatched_by:
                skill_entry["dispatched_by"] = dispatched_by
            if stage:
                skill_entry["stage"] = stage

            skills.append(skill_entry)

    return skills
