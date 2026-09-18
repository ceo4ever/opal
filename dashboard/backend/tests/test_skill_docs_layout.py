"""
@header {
  "module": "tests.test_skill_docs_layout",
  "layer": "test",
  "domain": "console",
  "description": "Docs 스킬 문서 화면 — 실레이아웃(소스 저장소·배포본) RED 테스트 (task 140 W-2 결함 정정). 기존 test_skill_docs.py는 fixture root만 주입해 34건 전부 GREEN이지만, adapter가 전제하는 registry.json + opal_skills/ + skills/ 물리 레이아웃은 실재하지 않는다(실측: 소스 저장소는 opal/core/references/opal-skills-registry.json + opal/skills + skills, 배포본은 ~/.opal/references/opal-skills-registry.json + ~/.opal/skills). 본 파일은 실제 corpus_root(저장소 루트, ~/.opal)를 build_skill_docs_corpus에 직접 주입해 실패를 고정한다. 구현하지 않는다 — 레이아웃 해석기 구현은 다음 배치(opal-be-agent) 담당.",
  "exports": [
    "test_source_repo_layout_resolves_corpus",
    "test_source_repo_layout_known_canonicals_present",
    "test_source_repo_layout_shared_path_canonicals_both_present",
    "test_deployed_layout_resolves_corpus",
    "test_deployed_layout_source_path_relative",
    "test_deployed_layout_shared_path_canonicals_both_present",
    "test_source_repo_source_path_relative_and_prefixed",
    "test_fixture_layout_still_resolves",
    "test_source_repo_listed_true_count_is_33",
    "test_source_repo_display_group_distribution_matches_e1",
    "test_source_repo_at_least_one_real_skill_readme_origin_nonempty",
    "test_source_repo_all_skills_body_origin_never_null"
  ],
  "depends": ["adapters.skill_docs_adapter"]
}
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from dashboard.backend.adapters.skill_docs_adapter import (
    SkillDocsCorpusError,
    build_skill_docs_corpus,
)

# 저장소 루트 = 이 테스트 파일 기준 상위 4단계
# (.../dashboard/backend/tests/test_skill_docs_layout.py -> repo root)
REPO_ROOT = Path(__file__).resolve().parents[3]
DEPLOYED_ROOT = Path.home() / ".opal"

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE_CORPUS_ROOT = FIXTURES_DIR / "skill_docs_corpus"

EXPECTED_SOURCE_CANONICAL_COUNT = 55
EXPECTED_DEPLOYED_CANONICAL_COUNT = 55
EXPECTED_SOURCE_KNOWN_CANONICALS = {
    "opal-pilot-project-build",
    "op-oppb-project-slice",
    "op-oppb-knowledge-finalize",
    "opal-onboarding",
}
# opal-pilot-dev(alias opd)와 opal-pilot-dev-short(alias opds)는 registry에서
# 같은 paths(opal-pilot-dev/SKILL.md)를 공유하는 별도 엔트리다. PM Gate 실측:
# 두 canonical이 각각 조회되어야 하며(len(records)=55), 접혀서 하나가
# 사라지면(len(records)=54) 안 된다.
EXPECTED_SHARED_PATH_CANONICALS = {"opal-pilot-dev", "opal-pilot-dev-short"}


# ── 1. 소스 저장소 레이아웃 ──────────────────────────────────────────────


def test_source_repo_layout_resolves_corpus():
    """저장소 루트를 corpus_root로 주면 canonical 55건이 구성되어야 한다.

    registry는 opal/core/references/opal-skills-registry.json에서,
    skills root는 opal/skills와 skills에서 와야 한다(PM 결함 분석).
    len(records)를 기준으로 센다 — order는 중복을 포함할 수 있어(PM Gate 실측:
    opal-pilot-dev-short 소실 시 order=55·records=54) 소실을 가릴 수 있다.
    order 자체에도 중복이 없어야 한다.
    """
    corpus = build_skill_docs_corpus(REPO_ROOT)
    assert len(corpus.records) == EXPECTED_SOURCE_CANONICAL_COUNT
    assert len(corpus.order) == len(set(corpus.order)) == len(corpus.records)


def test_source_repo_layout_known_canonicals_present():
    """PM이 지목한 4개 canonical이 소스 저장소 레이아웃에서 조회되어야 한다."""
    corpus = build_skill_docs_corpus(REPO_ROOT)
    for canonical in EXPECTED_SOURCE_KNOWN_CANONICALS:
        detail = corpus.get_detail(canonical)
        assert detail["canonical_name"] == canonical


def test_source_repo_layout_shared_path_canonicals_both_present():
    """opal-pilot-dev와 opal-pilot-dev-short가 소스 저장소 레이아웃에서 각각
    독립 canonical로 조회되어야 한다(둘 다 registry paths가
    opal-pilot-dev/SKILL.md를 가리키지만 접히면 안 된다)."""
    corpus = build_skill_docs_corpus(REPO_ROOT)
    for canonical in EXPECTED_SHARED_PATH_CANONICALS:
        assert canonical in corpus.records, f"{canonical} 소실됨 — records={sorted(corpus.records)}"
        detail = corpus.get_detail(canonical)
        assert detail["canonical_name"] == canonical


def test_source_repo_source_path_relative_and_prefixed():
    """소스 저장소 레이아웃의 source_path는 절대경로가 아니고
    opal/skills/{canonical}/SKILL.md 또는 skills/{canonical}/SKILL.md 형태다.
    """
    corpus = build_skill_docs_corpus(REPO_ROOT)
    for canonical in EXPECTED_SOURCE_KNOWN_CANONICALS:
        detail = corpus.get_detail(canonical)
        source_path = detail["source_path"]
        assert not Path(source_path).is_absolute()
        assert source_path == f"opal/skills/{canonical}/SKILL.md" or source_path == (
            f"skills/{canonical}/SKILL.md"
        )


# ── 2. 배포본 레이아웃 ──────────────────────────────────────────────────


def test_deployed_layout_resolves_corpus():
    """~/.opal을 corpus_root로 주면 canonical 55건이 구성되어야 한다(PM 실측:
    폴더 55개, registry canonical 55건, verify-bundle {"ok":true,"total":55}).

    registry는 references/opal-skills-registry.json에서, skills root는
    skills에서 와야 한다. 읽기 전용 — ~/.opal 아래 아무것도 쓰지 않는다.
    len(records) 기준으로 세고 order 중복 0도 함께 확인한다(소스 저장소
    레이아웃과 동일 사유). 배포본이 없는 환경에서는 skip한다.
    """
    if not (DEPLOYED_ROOT / "references" / "opal-skills-registry.json").is_file():
        pytest.skip("deployed root not found: ~/.opal/references/opal-skills-registry.json")

    corpus = build_skill_docs_corpus(DEPLOYED_ROOT)
    assert len(corpus.records) == EXPECTED_DEPLOYED_CANONICAL_COUNT
    assert len(corpus.order) == len(set(corpus.order)) == len(corpus.records)


def test_deployed_layout_shared_path_canonicals_both_present():
    """배포본 레이아웃에서도 opal-pilot-dev와 opal-pilot-dev-short가 각각
    독립 canonical로 조회되어야 한다."""
    if not (DEPLOYED_ROOT / "references" / "opal-skills-registry.json").is_file():
        pytest.skip("deployed root not found: ~/.opal/references/opal-skills-registry.json")

    corpus = build_skill_docs_corpus(DEPLOYED_ROOT)
    for canonical in EXPECTED_SHARED_PATH_CANONICALS:
        assert canonical in corpus.records, f"{canonical} 소실됨 — records={sorted(corpus.records)}"
        detail = corpus.get_detail(canonical)
        assert detail["canonical_name"] == canonical


def test_deployed_layout_source_path_relative():
    """배포본 레이아웃의 source_path도 절대경로가 아니고 skills/{canonical}/SKILL.md
    (배포본은 opal/skills 번들이 없으므로 skills/ 프리픽스만 기대) 형태다.
    """
    if not (DEPLOYED_ROOT / "references" / "opal-skills-registry.json").is_file():
        pytest.skip("deployed root not found: ~/.opal/references/opal-skills-registry.json")

    corpus = build_skill_docs_corpus(DEPLOYED_ROOT)
    assert len(corpus.order) >= 1
    sample_canonical = corpus.order[0]
    detail = corpus.get_detail(sample_canonical)
    source_path = detail["source_path"]
    assert not Path(source_path).is_absolute()
    assert source_path == f"skills/{sample_canonical}/SKILL.md"


# ── 3. fixture 레이아웃 회귀 방지 ────────────────────────────────────────


def test_fixture_layout_still_resolves():
    """기존 tests/fixtures/skill_docs_corpus는 여전히 해석되어야 한다(회귀 방지)."""
    corpus = build_skill_docs_corpus(FIXTURE_CORPUS_ROOT)
    assert len(corpus.order) >= 1


# ── 4. 실자산 단언 (task 143 W-1) ────────────────────────────────────────
#
# 합성 fixture 통과만으로는 완료 근거로 인정하지 않는다(fixture-vs-real 맹점,
# 140 재발 방지). 저장소 루트 corpus를 직접 읽어 DEC-4(listed)·DEC-1(body)
# 계약을 전수로 검증한다. records 기준으로 집계한다(len(order)는 중복을
# 가릴 수 있다 — 위 테스트들과 동일한 사유).
#
# 구현(W-3) 전까지 `listed`·`body`는 adapter record에 없는 키이므로
# record.get(...)는 None을 반환해 아래 단언이 실패(RED)한다.

EXPECTED_LISTED_TRUE_COUNT = 33
EXPECTED_DISPLAY_GROUP_DISTRIBUTION = {
    "pilot": 12,
    "operator": 14,
    "standalone": 8,
    "internal-stage": 21,
}


def test_source_repo_listed_true_count_is_33():
    """DEC-4: `display_group != internal-stage` AND `paths[0]` 폴더명이
    canonical과 같은 엔트리만 listed=true다. 저장소 실 corpus에서 정확히
    33건이어야 한다(55 - internal-stage 21 - opal-pilot-dev-short 1)."""
    corpus = build_skill_docs_corpus(REPO_ROOT)
    listed_count = sum(
        1 for record in corpus.records.values() if record.get("listed") is True
    )
    assert listed_count == EXPECTED_LISTED_TRUE_COUNT, (
        f"listed=true 개수가 33이어야 한다(records 기준 실측={listed_count})"
    )


def test_source_repo_display_group_distribution_matches_e1():
    """E-1 실측(PLAN §Approach)과 동일한 분포가 유지되어야 한다. records
    기준으로 집계하며 합은 55(canonical 총계)와 같아야 한다."""
    corpus = build_skill_docs_corpus(REPO_ROOT)
    distribution: dict[str, int] = {}
    for record in corpus.records.values():
        key = record["display_group"]
        distribution[key] = distribution.get(key, 0) + 1
    for group, expected_count in EXPECTED_DISPLAY_GROUP_DISTRIBUTION.items():
        assert distribution.get(group) == expected_count, (
            f"{group} 분포 기대치={expected_count}, 실측={distribution.get(group)}"
        )
    assert sum(distribution.values()) == 55


def test_source_repo_at_least_one_real_skill_readme_origin_nonempty():
    """DEC-1·2: 실존 스킬 1건 이상이 README 원문을 그대로 실어야 한다
    (origin=readme, markdown 비어있지 않음). 표본이 아니라 전수 순회로
    첫 매치를 찾는다. 하한선 스모크 테스트 — 전수 계약은
    test_source_repo_all_skills_body_origin_never_null이 소유한다."""
    corpus = build_skill_docs_corpus(REPO_ROOT)
    found = None
    for canonical_name, record in corpus.records.items():
        body = record.get("body")
        if body and body.get("origin") == "readme" and body.get("markdown"):
            found = canonical_name
            break
    assert found is not None, (
        "origin=readme이고 markdown이 비어 있지 않은 실존 스킬이 1건 이상 있어야 한다"
    )


def test_source_repo_all_skills_body_origin_never_null():
    """S-7 (TEST-SCENARIO.md, SSOT): "corpus의 모든 스킬을 순회해 body를
    집계한다 — origin이 null인 건수가 0이고, 모든 건의 body.markdown이
    공백이 아니며, origin이 readme 또는 skill_md 중 하나다. 표본이 아니라
    전수 집계로 단언한다."

    len(order)가 아니라 corpus.records 기준으로 순회한다(order는 중복을
    포함할 수 있어 소실을 가릴 수 있다 — 다른 레이아웃 테스트와 동일 사유).
    위반 스킬은 assertion 메시지에 이름 목록으로 노출해 W-3 구현 디버깅을
    돕는다.
    """
    corpus = build_skill_docs_corpus(REPO_ROOT)
    assert len(corpus.records) > 0, "corpus.records가 비어 있으면 전수 검증이 성립하지 않는다"

    null_origin: list[str] = []
    empty_or_blank_markdown: list[str] = []
    invalid_origin_value: list[tuple[str, Any]] = []

    for canonical_name, record in corpus.records.items():
        body = record.get("body")
        origin = body.get("origin") if body else None
        markdown = body.get("markdown") if body else None

        if origin is None:
            null_origin.append(canonical_name)
        elif origin not in ("readme", "skill_md"):
            invalid_origin_value.append((canonical_name, origin))

        if markdown is None or markdown.strip() == "":
            empty_or_blank_markdown.append(canonical_name)

    assert null_origin == [], (
        f"body.origin이 null인 건수는 0이어야 한다(S-7). 위반 스킬"
        f"({len(null_origin)}건): {sorted(null_origin)}"
    )
    assert invalid_origin_value == [], (
        "body.origin은 'readme' 또는 'skill_md'만 허용된다(S-7). 위반 스킬: "
        f"{sorted(invalid_origin_value)}"
    )
    assert empty_or_blank_markdown == [], (
        f"모든 스킬의 body.markdown이 비어 있지 않아야 한다(S-7, 공백만도 실패). "
        f"위반 스킬({len(empty_or_blank_markdown)}건): {sorted(empty_or_blank_markdown)}"
    )
