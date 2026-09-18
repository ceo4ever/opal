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
    "test_fixture_layout_still_resolves"
  ],
  "depends": ["adapters.skill_docs_adapter"]
}
"""
from __future__ import annotations

from pathlib import Path

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
