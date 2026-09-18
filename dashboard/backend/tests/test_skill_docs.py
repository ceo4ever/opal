"""
@header {
  "module": "tests.test_skill_docs",
  "layer": "test",
  "domain": "console",
  "description": "Docs 스킬 문서 화면 공개 계약 RED-first 테스트 — S-3~S-10 (task 140 W-2). 임시 corpus fixture(축소 registry JSON + 형식이 다른 SKILL.md + pipeline.json)를 DI로 주입해 실제 GET 라우터를 FastAPI TestClient로 호출한다. mock 대체 금지, 실 파일 읽기. PLAN DEC-1·5·6·9·10·11 계약을 고정한다. 구현(routers/docs_skills.py·parsers/skill_parser.py·adapters/skill_docs_adapter.py)이 없는 현재 상태에서 전부 실패(RED)해야 한다.",
  "exports": [
    "test_s3_list_no_filter_row_count",
    "test_s3_list_search_by_name_fragment",
    "test_s3_list_search_by_alias",
    "test_s3_list_search_by_description_word",
    "test_s3_list_search_by_use_case_phrase",
    "test_s3_list_group_filter_covers_all_groups",
    "test_s3_list_domain_filter_facet_count_matches",
    "test_s4_folder_vs_frontmatter_name_no_duplicate_card",
    "test_s4_alias_and_canonical_resolve_same_detail",
    "test_s5_oppb_detail_pipeline_stage_summary",
    "test_s5_internal_stage_skills_linked_to_oppb",
    "test_s6_source_missing_returns_200_partial",
    "test_s7_unknown_id_returns_404_skill_not_found",
    "test_s7_registry_unavailable_returns_500",
    "test_s7_broken_yaml_returns_500_parse_error",
    "test_s8_write_methods_return_405",
    "test_s8_path_traversal_rejected",
    "test_s8_no_absolute_path_in_response",
    "test_s9_examples_have_no_prompt_chars_or_regex_metachars",
    "test_s9_registry_triggers_not_exposed",
    "test_s10_standard_heading_extracts_all_sections",
    "test_s10_no_heading_returns_null_or_empty",
    "test_s10_partial_heading_extracts_only_available_section",
    "test_s4_shared_path_registry_entries_stay_independent_canonicals",
    "test_s4_shared_path_alias_resolves_to_own_canonical",
    "test_s4_shared_path_no_duplicate_in_order"
  ],
  "depends": ["routers.docs_skills", "adapters.skill_docs_adapter", "main"]
}
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CORPUS_ROOT = FIXTURES_DIR / "skill_docs_corpus"
BROKEN_YAML_CORPUS_ROOT = FIXTURES_DIR / "skill_docs_corpus_broken_yaml"
MISSING_REGISTRY_ROOT = FIXTURES_DIR / "skill_docs_corpus_missing_registry"

# fixture 폴더 수(= canonical 개수 기대치): opal-pilot-project-build,
# opal-pilot-dev, opal-pilot-dev-short, op-oppb-project-slice,
# op-oppb-knowledge-finalize, opal-onboarding, opal-skill-manager,
# opal-source-missing, opal-standard-heading, opal-no-heading,
# opal-partial-heading, standalone-example
#
# opal-pilot-dev와 opal-pilot-dev-short는 실제 opal-skills-registry.json과
# 동형으로 같은 paths(opal_skills/opal-pilot-dev/SKILL.md)를 공유하는 별도
# registry 엔트리다. adapter가 canonical_name을 registry `name`이 아니라
# Path(paths[0]).parent.name에서 파생하는 한 두 엔트리가 "opal-pilot-dev" 하나로
# 접혀 opal-pilot-dev-short가 소실된다 — 이 폴더 수 기대치(12)는 그 소실이
# 고쳐졌을 때만 성립하는 RED 고정값이다(PM Gate 결함 분석, PLAN DEC-5).
EXPECTED_CANONICAL_COUNT = 12


def _client_for_corpus_root(corpus_root: Path) -> TestClient:
    """DI로 corpus root를 주입한 TestClient를 생성한다.

    구현 계약(PLAN W-5/W-7): adapter의 corpus root는 DI로만 주입되어 호출자가
    요청 경로로 지정할 수 없어야 한다. 여기서는 앱 의존성 오버라이드를 통해서만
    주입한다 — 아직 `docs_skills` 라우터/의존성이 존재하지 않으므로 이 함수 자체가
    ImportError로 실패하는 것이 기대되는 RED 상태다.
    """
    from dashboard.backend.main import app
    from dashboard.backend.routers.docs_skills import get_skill_docs_corpus_root

    app.dependency_overrides[get_skill_docs_corpus_root] = lambda: corpus_root
    return TestClient(app)


@pytest.fixture()
def client() -> TestClient:
    return _client_for_corpus_root(CORPUS_ROOT)


# ── S-3: 목록 검색·필터·facet (AC-2, C-2, C-3) ───────────────────────────────

def test_s3_list_no_filter_row_count(client: TestClient) -> None:
    resp = client.get("/api/docs/skills")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["items"]) == EXPECTED_CANONICAL_COUNT, body
    assert body["meta"]["total"] == EXPECTED_CANONICAL_COUNT


def test_s3_list_search_by_name_fragment(client: TestClient) -> None:
    resp = client.get("/api/docs/skills", params={"q": "onboarding"})
    assert resp.status_code == 200, resp.text
    names = [it["canonical_name"] for it in resp.json()["items"]]
    assert "opal-onboarding" in names


def test_s3_list_search_by_alias(client: TestClient) -> None:
    resp = client.get("/api/docs/skills", params={"q": "oppb"})
    assert resp.status_code == 200, resp.text
    names = [it["canonical_name"] for it in resp.json()["items"]]
    assert "opal-pilot-project-build" in names


def test_s3_list_search_by_description_word(client: TestClient) -> None:
    resp = client.get("/api/docs/skills", params={"q": "관리"})
    assert resp.status_code == 200, resp.text
    names = [it["canonical_name"] for it in resp.json()["items"]]
    assert "opal-skill-manager" in names


def test_s3_list_search_by_use_case_phrase(client: TestClient) -> None:
    resp = client.get("/api/docs/skills", params={"q": "신규 사용자"})
    assert resp.status_code == 200, resp.text
    names = [it["canonical_name"] for it in resp.json()["items"]]
    assert "opal-onboarding" in names


def test_s3_list_group_filter_covers_all_groups(client: TestClient) -> None:
    for group in ("pilot", "standalone", "operator", "internal-stage"):
        resp = client.get("/api/docs/skills", params={"group": group})
        assert resp.status_code == 200, resp.text
        items = resp.json()["items"]
        assert len(items) > 0, f"group={group} 결과가 0건이면 안 된다"
        assert all(it["display_group"] == group for it in items)


def test_s3_list_domain_filter_facet_count_matches(client: TestClient) -> None:
    resp = client.get("/api/docs/skills", params={"domain": "ops"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    domain_facet = next(
        (f for f in body["facets"]["domains"] if f["value"] == "ops"), None
    )
    assert domain_facet is not None
    assert domain_facet["count"] == len(body["items"])


# ── S-4: canonical 정규화 중복 카드 0 (AC-5) ────────────────────────────────

def test_s4_folder_vs_frontmatter_name_no_duplicate_card(client: TestClient) -> None:
    resp = client.get("/api/docs/skills")
    assert resp.status_code == 200, resp.text
    names = [it["canonical_name"] for it in resp.json()["items"]]
    assert names.count("opal-onboarding") == 1
    assert names.count("opal-skill-manager") == 1
    # frontmatter raw name이 별도 카드로 나오면 안 된다
    assert "onboarding" not in names
    assert "skill-manager" not in names


@pytest.mark.parametrize(
    "canonical,frontmatter_alias",
    [("opal-onboarding", "onboarding"), ("opal-skill-manager", "skill-manager")],
)
def test_s4_alias_and_canonical_resolve_same_detail(
    client: TestClient, canonical: str, frontmatter_alias: str
) -> None:
    resp_canonical = client.get(f"/api/docs/skills/{canonical}")
    resp_alias = client.get(f"/api/docs/skills/{frontmatter_alias}")
    assert resp_canonical.status_code == 200, resp_canonical.text
    assert resp_alias.status_code == 200, resp_alias.text
    body_canonical = resp_canonical.json()
    body_alias = resp_alias.json()
    assert body_canonical["canonical_name"] == canonical
    assert body_alias["canonical_name"] == canonical
    assert frontmatter_alias in body_canonical["aliases"]
    assert body_alias["resolved_from"] == {"kind": "alias", "value": frontmatter_alias}
    assert body_canonical["resolved_from"] == {"kind": "canonical", "value": canonical}


# ── S-4 추가: 같은 paths를 공유하는 registry 엔트리(opal-pilot-dev/-short) ──
# 실제 opal-skills-registry.json은 opal-pilot-dev(alias opd)와
# opal-pilot-dev-short(alias opds) 두 엔트리가 동일 paths
# (opal_skills/opal-pilot-dev/SKILL.md)를 가리킨다. adapter가 canonical_name을
# registry `name`이 아니라 Path(paths[0]).parent.name에서 파생하는 한 두
# 엔트리가 "opal-pilot-dev" 하나로 접혀 opal-pilot-dev-short가 사라진다
# (PM Gate 실측: len(records)=54 vs registry canonical=55). 아래 3건은 그
# 소실을 고정하는 RED이며, canonical 파생 규칙 정정(다음 배치) 전에는 실패해야
# 한다.


def test_s4_shared_path_registry_entries_stay_independent_canonicals(
    client: TestClient,
) -> None:
    resp_dev = client.get("/api/docs/skills/opal-pilot-dev")
    resp_short = client.get("/api/docs/skills/opal-pilot-dev-short")
    assert resp_dev.status_code == 200, resp_dev.text
    assert resp_short.status_code == 200, resp_short.text
    body_dev = resp_dev.json()
    body_short = resp_short.json()
    assert body_dev["canonical_name"] == "opal-pilot-dev"
    assert body_short["canonical_name"] == "opal-pilot-dev-short"


def test_s4_shared_path_alias_resolves_to_own_canonical(client: TestClient) -> None:
    resp_opd = client.get("/api/docs/skills/opd")
    resp_opds = client.get("/api/docs/skills/opds")
    assert resp_opd.status_code == 200, resp_opd.text
    assert resp_opds.status_code == 200, resp_opds.text
    assert resp_opd.json()["canonical_name"] == "opal-pilot-dev"
    assert resp_opds.json()["canonical_name"] == "opal-pilot-dev-short"


def test_s4_shared_path_no_duplicate_in_order(client: TestClient) -> None:
    resp = client.get("/api/docs/skills")
    assert resp.status_code == 200, resp.text
    names = [it["canonical_name"] for it in resp.json()["items"]]
    assert names.count("opal-pilot-dev") == 1
    assert names.count("opal-pilot-dev-short") == 1
    assert len(names) == len(set(names)), "order/records에 중복 canonical이 있으면 안 된다"


# ── S-5: OPPB 단계 요약·내부 단계 관계 (AC-4) ───────────────────────────────

def test_s5_oppb_detail_pipeline_stage_summary(client: TestClient) -> None:
    resp = client.get("/api/docs/skills/oppb")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["canonical_name"] == "opal-pilot-project-build"
    assert body["display_group"] == "pilot"
    assert "oppb" in body["aliases"]
    assert body["pipeline"] is not None
    step_ids = [s["id"] for s in body["pipeline"]["steps"]]
    assert step_ids == ["P0", "P1", "P2", "P3", "P4", "P5"]
    # task row(22건) 등이 단계 카드로 오인되지 않는다 — 단계 수는 pipeline.json meta.stages 크기와 같다
    assert len(body["pipeline"]["steps"]) == 6


def test_s5_internal_stage_skills_linked_to_oppb(client: TestClient) -> None:
    for canonical in ("op-oppb-project-slice", "op-oppb-knowledge-finalize"):
        resp = client.get(f"/api/docs/skills/{canonical}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["display_group"] == "internal-stage"
        related_names = [r["canonical_name"] for r in body["related_skills"]]
        assert related_names.count("opal-pilot-project-build") == 1, (
            "oppb가 관련 스킬로 중복 없이 정확히 1회 연결되어야 한다"
        )


# ── S-6: source 부재 200 partial (AC-3, AC-6) ───────────────────────────────

def test_s6_source_missing_returns_200_partial(client: TestClient) -> None:
    resp = client.get("/api/docs/skills/opal-source-missing")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["source"]["available"] is False
    assert body["source"]["content_hash"] is None
    assert body["usage_markdown"] is None
    assert body["when_to_use_markdown"] is None
    assert body["quick_start"] is None
    assert body["arguments"] == []
    assert body["options"] == []
    assert body["examples"] == []
    assert body["related_skills"] == []
    # header metadata는 유지된다
    assert body["canonical_name"] == "opal-source-missing"
    assert body["description"]
    assert body["display_group"]
    assert isinstance(body["aliases"], list)
    assert body["source_path"]


# ── S-7: 오류 계약 (AC-6) ────────────────────────────────────────────────────

def test_s7_unknown_id_returns_404_skill_not_found(client: TestClient) -> None:
    resp = client.get("/api/docs/skills/does-not-exist-anywhere")
    assert resp.status_code == 404, resp.text
    body = resp.json()
    assert body["error"]["code"] == "skill_not_found"
    assert "traceback" not in json.dumps(body).lower()
    assert "Traceback (most recent call last)" not in resp.text


def test_s7_registry_unavailable_returns_500() -> None:
    client_missing_registry = _client_for_corpus_root(MISSING_REGISTRY_ROOT)
    resp = client_missing_registry.get("/api/docs/skills")
    assert resp.status_code == 500, resp.text
    body = resp.json()
    assert body["error"]["code"] == "registry_unavailable"
    assert "Traceback (most recent call last)" not in resp.text


def test_s7_broken_yaml_returns_500_parse_error() -> None:
    client_broken_yaml = _client_for_corpus_root(BROKEN_YAML_CORPUS_ROOT)
    resp = client_broken_yaml.get("/api/docs/skills/opal-broken-yaml")
    assert resp.status_code == 500, resp.text
    body = resp.json()
    assert body["error"]["code"] == "parse_error"
    assert "Traceback (most recent call last)" not in resp.text


# ── S-8: GET-only·traversal 차단·절대경로 미노출 (C-5, C-7) ─────────────────

@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
@pytest.mark.parametrize(
    "path", ["/api/docs/skills", "/api/docs/skills/opal-onboarding"]
)
def test_s8_write_methods_return_405(client: TestClient, method: str, path: str) -> None:
    resp = getattr(client, method)(path)
    assert resp.status_code == 405, f"{method.upper()} {path} -> {resp.status_code}: {resp.text}"


@pytest.mark.parametrize(
    "traversal_id",
    [
        "../../../../etc/passwd",
        "..%2F..%2F..%2Fetc%2Fpasswd",
        "%2e%2e%2fetc%2fpasswd",
        "/etc/passwd",
    ],
)
def test_s8_path_traversal_rejected(client: TestClient, traversal_id: str) -> None:
    resp = client.get(f"/api/docs/skills/{traversal_id}")
    assert resp.status_code in (404, 422), f"{traversal_id} -> {resp.status_code}"
    assert "root:" not in resp.text  # /etc/passwd 내용이 노출되지 않는다


def test_s8_no_absolute_path_in_response(client: TestClient) -> None:
    resp = client.get("/api/docs/skills/opal-onboarding")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    source_path = body["source_path"]
    assert not source_path.startswith("/")
    assert str(CORPUS_ROOT) not in source_path
    assert re.match(r"^(opal/skills|skills)/opal-onboarding/SKILL\.md$", source_path), source_path


# ── S-9: 예시 원문·트리거 비노출 (C-4) ───────────────────────────────────────

_PROMPT_PREFIX_RE = re.compile(r"^\s*[$%>]")
_REGEX_METACHAR_RE = re.compile(r"[\^$]|\(\?[a-zA-Z]|\|")


def test_s9_examples_have_no_prompt_chars_or_regex_metachars(client: TestClient) -> None:
    checked_any = False
    for canonical in (
        "opal-standard-heading",
        "opal-pilot-project-build",
        "opal-onboarding",
        "opal-skill-manager",
    ):
        resp = client.get(f"/api/docs/skills/{canonical}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        for example in body["examples"]:
            checked_any = True
            command = example["command"]
            assert not _PROMPT_PREFIX_RE.match(command), command
            assert not _REGEX_METACHAR_RE.search(command), command
        if body["quick_start"]:
            command = body["quick_start"]["command"]
            assert not _PROMPT_PREFIX_RE.match(command), command
            assert not _REGEX_METACHAR_RE.search(command), command
    assert checked_any, "예시가 하나도 검사되지 않았다 — fixture 또는 추출 계약을 확인하라"


def test_s9_registry_triggers_not_exposed(client: TestClient) -> None:
    resp = client.get("/api/docs/skills/oppb")
    assert resp.status_code == 200, resp.text
    raw = resp.text
    assert "^oppb$" not in raw
    assert "(?i)" not in raw


# ── S-10: 본문 구조 상이 → 부분 추출 (AC-3, H-2) ────────────────────────────

def test_s10_standard_heading_extracts_all_sections(client: TestClient) -> None:
    resp = client.get("/api/docs/skills/opal-standard-heading")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["usage_markdown"] is not None
    assert body["when_to_use_markdown"] is not None
    assert len(body["arguments"]) >= 1
    assert len(body["options"]) >= 1
    assert len(body["examples"]) >= 1


def test_s10_no_heading_returns_null_or_empty(client: TestClient) -> None:
    resp = client.get("/api/docs/skills/opal-no-heading")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["usage_markdown"] is None
    assert body["when_to_use_markdown"] is None
    assert body["arguments"] == []
    assert body["options"] == []
    assert body["examples"] == []
    assert body["quick_start"] is None


def test_s10_partial_heading_extracts_only_available_section(client: TestClient) -> None:
    resp = client.get("/api/docs/skills/opal-partial-heading")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["usage_markdown"] is not None
    assert "opal-partial-heading go" in body["usage_markdown"]
    assert body["when_to_use_markdown"] is None
    assert body["arguments"] == []
    assert body["options"] == []
    # 다른 스킬(opal-standard-heading)의 내용이 섞이지 않는다
    assert "opal-standard-heading" not in body["usage_markdown"]
