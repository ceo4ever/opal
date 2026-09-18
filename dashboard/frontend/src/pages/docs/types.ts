/**
 * @header {
 *   "module": "docs-types",
 *   "layer": "type",
 *   "domain": "docs",
 *   "description": "Docs 스킬 문서 화면(카탈로그·상세)의 표현 타입 — GET /api/docs/skills · GET /api/docs/skills/{skill_id} 응답 형태(W-5/W-7 backend 계약, PLAN DEC-1·DEC-8)를 FE에서 소비하기 위한 로컬 인터페이스. 백엔드 Pydantic 모델의 선택 필드 확장(facets.groups 등 실측 응답에만 존재할 수 있는 필드)을 허용하기 위해 optional로 넉넉히 정의한다. source.available=false(DEC-1)는 오류가 아니라 200 partial이며 본문 필드는 null/빈 배열로 온다.",
 *   "task": "140-260917-opdw-스킬-문서-화면",
 *   "exports": [
 *     "SkillFacetOption",
 *     "SkillFacets",
 *     "SkillListMeta",
 *     "SkillCatalogItem",
 *     "SkillCatalogListResponse",
 *     "ResolvedFrom",
 *     "SkillSourceInfo",
 *     "ArgumentItem",
 *     "ExampleBlock",
 *     "QuickStart",
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
  use_cases?: string[];
  display_group: string;
  registry_group?: string;
  domain?: string | null;
  pipeline_summary?: string | null;
  source_path: string;
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

export interface ArgumentItem {
  name: string;
  type?: string | null;
  required?: boolean;
  default?: string | null;
  description?: string | null;
}

export interface ExampleBlock {
  command: string;
  description?: string | null;
}

export interface QuickStart {
  id?: string;
  label?: string;
  language?: string;
  command: string;
  kind?: string;
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
  use_cases?: string[];
  display_group: string;
  registry_group?: string;
  domain?: string | null;
  pipeline_summary?: string | null;
  source_path: string;
  source: SkillSourceInfo;
  usage_markdown?: string | null;
  when_to_use_markdown?: string | null;
  quick_start?: QuickStart | null;
  arguments: ArgumentItem[];
  options: ArgumentItem[];
  examples: ExampleBlock[];
  pipeline?: PipelineSummary | null;
  related_skills: RelatedSkillRef[];
  resolved_from: ResolvedFrom;
}
