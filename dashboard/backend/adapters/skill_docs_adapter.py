"""
@header {
  "module": "adapters.skill_docs_adapter",
  "layer": "service",
  "domain": "console",
  "description": "Docs 스킬 문서 화면용 read-only corpus adapter. corpus_root의 실제 물리 레이아웃(소스 저장소: opal/core/references/opal-skills-registry.json + opal/skills·skills / 배포본: references/opal-skills-registry.json + skills / 테스트 fixture: registry.json + opal_skills·skills)을 순서대로 판정해 registry 위치와 bundled skills root들을 해석한 뒤, canonical 병합해 canonical index·alias index를 만들고, 검색(이름·alias·설명·용도)·그룹/도메인 필터·facet count·related skills 정규화·OPPB pipeline 단계 요약을 제공한다. corpus root는 호출자가 DI로만 주입한다(경로 파라미터화 금지, PLAN DEC-6). 매 호출마다 재구성하며 캐시하지 않는다(DEC-4).",
  "exports": [
    "SkillDocsCorpus",
    "SkillDocsCorpusError",
    "RegistryUnavailableError",
    "ParseError",
    "SkillNotFoundError",
    "AmbiguousAliasError",
    "build_skill_docs_corpus"
  ],
  "depends": ["parsers.skill_parser"]
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dashboard.backend.parsers.skill_parser import (
    SkillMarkdownParseError,
    parse_skill_source,
)

# registry.json의 그룹 키 → 화면 표시 그룹. 그룹 키만으로 판정이 애매한 경우
# entry 필드(pipeline/stage)로 보강한다.
_PILOT_GROUP_KEYS = {"opal-pilot"}
_STANDALONE_GROUP_KEYS = {"standalone"}

# corpus_root 레이아웃 해석 순서. registry.json의 실제 물리 위치는 배포 형태마다
# 다르며(소스 저장소 / 배포본 / 테스트 fixture), registry entry의 paths[0]은 항상
# 템플릿("{project}/..." · "~/...") 이거나 fixture 상대경로일 뿐 물리 root를
# 그대로 가리키지 않는다(task 140 W-5/W-7 결함). 따라서 corpus_root 자체의
# 물리 구조를 순서대로 판정해 registry 위치와 skills bundle root들을 결정한다.
#
#   1) 소스 저장소: opal/core/references/opal-skills-registry.json +
#      opal/skills, skills 두 bundle root.
#   2) 배포본(~/.opal 등 installer 산출물): references/opal-skills-registry.json +
#      skills bundle root 하나만(opal/skills 번들 없음).
#   3) 테스트 fixture: registry.json(루트 직속) + opal_skills, skills 두 bundle root.
#
# 어느 레이아웃에도 맞지 않으면 RegistryUnavailableError.


def _resolve_corpus_layout(corpus_root: Path) -> tuple[Path, list[tuple[Path, str]]]:
    """corpus_root로부터 (registry_path, [(physical_skills_root, public_prefix), ...])를 결정한다.

    public_prefix는 응답 source_path에 노출되는 사용자 대면 접두사다(절대경로 금지).
    """
    source_registry = corpus_root / "opal" / "core" / "references" / "opal-skills-registry.json"
    if source_registry.is_file():
        return source_registry, [
            (corpus_root / "opal" / "skills", "opal/skills"),
            (corpus_root / "skills", "skills"),
        ]

    deployed_registry = corpus_root / "references" / "opal-skills-registry.json"
    if deployed_registry.is_file():
        return deployed_registry, [
            (corpus_root / "skills", "skills"),
        ]

    fixture_registry = corpus_root / "registry.json"
    if fixture_registry.is_file():
        return fixture_registry, [
            (corpus_root / "opal_skills", "opal/skills"),
            (corpus_root / "skills", "skills"),
        ]

    raise RegistryUnavailableError(
        f"registry.json not found under {corpus_root}",
        registry_path=str(corpus_root),
    )


def _resolve_physical_skill_path(
    skills_roots: list[tuple[Path, str]], canonical_name: str
) -> tuple[Path, str]:
    """canonical_name의 SKILL.md 물리 경로와 공개용 source_path를 결정한다.

    skills_roots를 순서대로 시도해 실제 존재하는 첫 파일을 사용한다. 어느
    root에도 없으면(예: fixture의 opal-source-missing) 첫 root 기준 경로를
    반환해 parse_skill_source가 available=False로 처리하게 둔다.
    """
    fallback: tuple[Path, str] | None = None
    for root_dir, public_prefix in skills_roots:
        candidate = _safe_join(root_dir, f"{canonical_name}/SKILL.md")
        source_path = f"{public_prefix}/{canonical_name}/SKILL.md"
        if fallback is None:
            fallback = (candidate, source_path)
        if candidate.is_file():
            return candidate, source_path
    assert fallback is not None  # skills_roots는 항상 1개 이상
    return fallback


class SkillDocsCorpusError(Exception):
    """Docs 스킬 corpus 처리 중 발생하는 도메인 에러의 베이스."""

    code = "internal_error"

    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class RegistryUnavailableError(SkillDocsCorpusError):
    code = "registry_unavailable"


class ParseError(SkillDocsCorpusError):
    code = "parse_error"


class SkillNotFoundError(SkillDocsCorpusError):
    code = "skill_not_found"


class AmbiguousAliasError(SkillDocsCorpusError):
    code = "ambiguous_alias"


@dataclass
class SkillDocsCorpus:
    """corpus_root 하나에 대해 build() 시점에 완전히 구성되는 불변 index.

    records: canonical_name -> 상세 레코드(dict)
    order: 등록 순서(안정적인 목록 노출을 위해 보존)
    alias_index: alias(소문자 비교 없이 원문 그대로) -> canonical_name
    """

    records: dict[str, dict[str, Any]] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)
    alias_index: dict[str, str] = field(default_factory=dict)

    # ── 조회 ────────────────────────────────────────────────────────────

    def resolve(self, id_or_alias: str) -> tuple[str, dict[str, str]]:
        """id를 canonical_name으로 정규화하고 resolved_from을 함께 반환한다."""
        if not id_or_alias or "/" in id_or_alias or ".." in id_or_alias:
            raise SkillNotFoundError(f"invalid skill id: {id_or_alias!r}")
        if id_or_alias in self.records:
            return id_or_alias, {"kind": "canonical", "value": id_or_alias}
        canonical = self.alias_index.get(id_or_alias)
        if canonical is not None:
            return canonical, {"kind": "alias", "value": id_or_alias}
        raise SkillNotFoundError(f"skill not found: {id_or_alias!r}")

    def get_detail(self, id_or_alias: str) -> dict[str, Any]:
        canonical, resolved_from = self.resolve(id_or_alias)
        record = self.records[canonical]
        return {**record, "resolved_from": resolved_from}

    def list_items(
        self,
        *,
        q: str | None = None,
        group: str | None = None,
        domain: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """목록 조회 — 검색·그룹/도메인 필터를 적용하고 facet count를 계산한다.

        facet count는 그룹·domain 필터를 뺀 나머지 필터(q)만 적용한 뒤 계산해
        "현재 검색 조건에서 각 도메인을 골랐을 때 몇 건이 남는가"를 보여준다.
        """
        base = [self.records[name] for name in self.order]
        if q:
            base = [r for r in base if self._matches_query(r, q)]

        items = base
        if group:
            items = [r for r in items if r["display_group"] == group]
        if domain:
            items = [r for r in items if r["domain"] == domain]

        domain_counts: dict[str, int] = {}
        for r in base if not group else [x for x in base if x["display_group"] == group]:
            d = r["domain"]
            if d:
                domain_counts[d] = domain_counts.get(d, 0) + 1

        facets = {
            "domains": [
                {"value": value, "count": count}
                for value, count in domain_counts.items()
            ]
        }
        meta = {"total": len(items)}
        return [self._list_view(r) for r in items], {"facets": facets, "meta": meta}

    # ── 내부 ────────────────────────────────────────────────────────────

    @staticmethod
    def _list_view(record: dict[str, Any]) -> dict[str, Any]:
        return {
            "canonical_name": record["canonical_name"],
            "aliases": record["aliases"],
            "description": record["description"],
            "display_group": record["display_group"],
            "domain": record["domain"],
            "source_path": record["source_path"],
        }

    @staticmethod
    def _matches_query(record: dict[str, Any], q: str) -> bool:
        needle = q.strip().lower()
        if not needle:
            return True
        haystack_parts = [
            record["canonical_name"],
            *record["aliases"],
            record.get("description") or "",
            *(record.get("use_cases") or []),
        ]
        haystack = " ".join(haystack_parts).lower()
        return needle in haystack


def build_skill_docs_corpus(corpus_root: Path) -> SkillDocsCorpus:
    """corpus_root(registry.json + bundled source roots)로부터 index를 구성한다.

    Args:
        corpus_root: registry.json이 위치한 루트. 실서비스에서는 프로젝트
            루트(레지스트리 + opal/skills, skills 번들 root를 포함)이고,
            테스트에서는 fixture 디렉토리다. 호출자는 이 값을 DI로만 주입해야
            하며, 사용자 요청 경로로부터 파생시켜서는 안 된다(DEC-6).

    Returns:
        SkillDocsCorpus: 완전히 구성된 불변 index.

    Raises:
        RegistryUnavailableError: registry.json이 없거나 JSON 파싱 실패.
        ParseError: 어느 canonical의 SKILL.md frontmatter YAML 파싱 실패.
        AmbiguousAliasError: 동일 alias가 서로 다른 canonical을 가리킴.
    """
    corpus_root = Path(corpus_root).resolve()
    registry_path, skills_roots = _resolve_corpus_layout(corpus_root)

    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryUnavailableError(
            f"registry.json unreadable: {exc}", registry_path=str(registry_path)
        ) from exc

    groups = registry.get("groups", {})
    if not isinstance(groups, dict):
        raise RegistryUnavailableError(
            "registry.json malformed: 'groups' must be an object",
            registry_path=str(registry_path),
        )

    entries: list[tuple[str, dict[str, Any]]] = []
    for group_key, group_entries in groups.items():
        if not isinstance(group_entries, list):
            continue
        for entry in group_entries:
            entries.append((group_key, entry))

    records: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    canonical_by_registry_name: dict[str, str] = {}

    # 1차 패스: canonical identity·물리 경로·display_group·본문 파싱까지 완료
    for group_key, entry in entries:
        paths = entry.get("paths") or []
        if not paths:
            continue
        canonical_name = entry.get("name")
        if not canonical_name:
            continue

        physical_path, source_path = _resolve_physical_skill_path(
            skills_roots, canonical_name
        )
        try:
            parsed = parse_skill_source(physical_path)
        except SkillMarkdownParseError as exc:
            raise ParseError(
                f"failed to parse SKILL.md for {canonical_name}: {exc}",
                canonical_name=canonical_name,
            ) from exc

        display_group = _display_group(group_key, entry)

        aliases = _derive_aliases(
            canonical_name=canonical_name,
            registry_alias=entry.get("alias"),
            source_name=parsed.get("source_name"),
        )

        pipeline = None
        if parsed["available"]:
            pipeline = _load_pipeline(physical_path.parent)

        description = entry.get("description") or parsed.get("description")

        record = {
            "canonical_name": canonical_name,
            "source_name": parsed.get("source_name"),
            "registry_name": entry.get("name"),
            "aliases": aliases,
            "description": description,
            "domain": entry.get("domain"),
            "display_group": display_group,
            "source_path": source_path,
            "source": {
                "available": parsed["available"],
                "content_hash": parsed["content_hash"],
            },
            "usage_markdown": parsed["usage_markdown"],
            "when_to_use_markdown": parsed["when_to_use_markdown"],
            "quick_start": parsed["quick_start"],
            "arguments": parsed["arguments"],
            "options": parsed["options"],
            "examples": parsed["examples"],
            "use_cases": parsed["use_cases"],
            "pipeline": pipeline,
            "related_skills": [],
            "_dispatched_by": entry.get("dispatched_by") or [],
        }
        records[canonical_name] = record
        order.append(canonical_name)
        if entry.get("name"):
            canonical_by_registry_name[entry["name"]] = canonical_name

    # 2차 패스: related_skills 정규화(registry dispatched_by → canonical, 양방향, 중복 제거)
    reverse_related: dict[str, list[str]] = {}
    for canonical_name in order:
        record = records[canonical_name]
        dispatched_by = record.pop("_dispatched_by", [])
        related: list[str] = []
        for raw_name in dispatched_by:
            target = canonical_by_registry_name.get(raw_name, raw_name)
            if target in records and target not in related:
                related.append(target)
                reverse_related.setdefault(target, [])
                if canonical_name not in reverse_related[target]:
                    reverse_related[target].append(canonical_name)
        record["related_skills"] = [{"canonical_name": name} for name in related]

    for target, related_names in reverse_related.items():
        record = records[target]
        existing = {r["canonical_name"] for r in record["related_skills"]}
        for name in related_names:
            if name not in existing:
                record["related_skills"].append({"canonical_name": name})
                existing.add(name)

    # alias index 구성 (ambiguous alias는 즉시 실패)
    alias_index: dict[str, str] = {}
    for canonical_name in order:
        for alias in records[canonical_name]["aliases"]:
            existing_target = alias_index.get(alias)
            if existing_target is not None and existing_target != canonical_name:
                raise AmbiguousAliasError(
                    f"alias {alias!r} points to both {existing_target!r} and {canonical_name!r}",
                    alias=alias,
                )
            alias_index[alias] = canonical_name

    return SkillDocsCorpus(records=records, order=order, alias_index=alias_index)


def _safe_join(root: Path, relpath: str) -> Path:
    """root 하위로만 결합을 허용하는 방어적 경로 결합(DEC-6)."""
    candidate = (root / relpath).resolve()
    if root not in candidate.parents and candidate != root:
        raise SkillNotFoundError(f"path escapes corpus root: {relpath!r}")
    return candidate


def _display_group(group_key: str, entry: dict[str, Any]) -> str:
    if entry.get("pipeline"):
        return "pilot"
    if entry.get("stage") or entry.get("dispatched_by"):
        return "internal-stage"
    if group_key in _PILOT_GROUP_KEYS:
        return "pilot"
    if group_key in _STANDALONE_GROUP_KEYS:
        return "standalone"
    return "operator"


def _derive_aliases(
    *, canonical_name: str, registry_alias: str | None, source_name: str | None
) -> list[str]:
    """DEC-2: registry alias → source_name(frontmatter name) 순서로 파생·중복 제거.

    canonical과 동일한 값은 alias로 노출하지 않는다.
    """
    aliases: list[str] = []
    for candidate in (registry_alias, source_name):
        if candidate and candidate != canonical_name and candidate not in aliases:
            aliases.append(candidate)
    return aliases


def _load_pipeline(skill_dir: Path) -> dict[str, Any] | None:
    pipeline_path = skill_dir / "references" / "pipeline.json"
    if not pipeline_path.is_file():
        return None
    try:
        data = json.loads(pipeline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    meta = data.get("meta") or {}
    stages = meta.get("stages")
    if not stages:
        return None
    return {
        "mode_label": meta.get("mode_label"),
        "steps": [{"id": stage} for stage in stages],
    }
