/**
 * @header {
 *   "module": "docs-types",
 *   "layer": "type",
 *   "domain": "docs",
 *   "description": "Docs 스킬 문서 화면(사이드바+본문 단일 화면)의 표현 타입 — GET /api/docs/skills · GET /api/docs/skills/{skill_id} 응답 형태(PLAN 143 DEC-1·DEC-3·DEC-4)를 FE에서 소비하기 위한 로컬 인터페이스. 태스크 143에서 슬롯 필드(usage_markdown·when_to_use_markdown·quick_start·arguments·options·examples·use_cases)를 제거하고 `body`(원문 Markdown + origin + source_path)와 `listed`(사이드바 노출 여부, 서버 파생)를 추가했다. `source.available=false`이거나 `body.origin=null`이어도 HTTP는 200이며 header metadata는 유지된다(DEC-2 200-partial).",
 *   "task": "143-260918-opds-스킬-문서-사이드바",
 *   "exports": [
 *     "SkillFacetOption",
 *     "SkillFacets",
 *     "SkillListMeta",
 *     "SkillCatalogItem",
 *     "SkillCatalogListResponse",
 *     "ResolvedFrom",
 *     "SkillSourceInfo",
 *     "SkillBody",
 *     "PipelineStep",
 *     "PipelineSummary",
 *     "RelatedSkillRef",
 *     "SkillDetailResponse"
 *   ]
 * }
 */

export interface SkillFacetOption {
  value: string;
  label?: string;
  count: number;
}

export interface SkillFacets {
  groups?: SkillFacetOption[];
  domains?: SkillFacetOption[];
}

export interface SkillListMeta {
  total: number;
  filtered?: number;
  query?: string;
}

export interface SkillCatalogItem {
  canonical_name: string;
  source_name?: string;
  aliases: string[];
  description?: string | null;
  display_group: string;
  registry_group?: string;
  domain?: string | null;
  pipeline_summary?: string | null;
  source_path: string;
  listed: boolean;
}

export interface SkillCatalogListResponse {
  items: SkillCatalogItem[];
  facets: SkillFacets;
  meta: SkillListMeta;
}

export interface ResolvedFrom {
  kind: "canonical" | "alias";
  value: string;
}

export interface SkillSourceInfo {
  path?: string;
  available: boolean;
  content_hash?: string | null;
}

/** 렌더용 본문 원문 — DEC-1: 서버는 heading을 해석하지 않고 원문을 그대로 싣는다. */
export interface SkillBody {
  markdown: string | null;
  origin: "readme" | "skill_md" | null;
  source_path: string | null;
}

export interface PipelineStep {
  id: string;
}

export interface PipelineSummary {
  mode_label?: string | null;
  steps?: PipelineStep[];
}

export interface RelatedSkillRef {
  canonical_name: string;
}

export interface SkillDetailResponse {
  canonical_name: string;
  source_name?: string;
  aliases: string[];
  description?: string | null;
  display_group: string;
  registry_group?: string;
  domain?: string | null;
  pipeline_summary?: string | null;
  source_path: string;
  source: SkillSourceInfo;
  body: SkillBody;
  listed: boolean;
  pipeline?: PipelineSummary | null;
  related_skills: RelatedSkillRef[];
  resolved_from: ResolvedFrom;
}
