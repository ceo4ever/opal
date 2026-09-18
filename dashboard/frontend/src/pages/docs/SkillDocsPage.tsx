/**
 * @header {
 *   "module": "skill-docs-page",
 *   "layer": "page",
 *   "domain": "docs",
 *   "description": "GET /api/docs/skills(무파라미터 1회) + GET /api/docs/skills/{skillId} 단일 컴포넌트 — PLAN 143 DEC-6대로 두 라우트(/docs/skills, /docs/skills/:skillId)에 동일 컴포넌트를 지정해 좌측 그룹 사이드바(listed=true만, display_group→파일럿/오퍼레이터/독립 3그룹, canonical+alias 병기, 선택 항목 aria-current)와 우측 본문(MarkdownView로 body.markdown 원문 렌더, origin=skill_md면 README 폴백 안내, origin=null이면 부재 상태)을 함께 렌더한다. 사이드바 목록 쿼리 키를 skillId와 무관하게 고정해(DEC-6·H-7) 항목 전환 시 재요청을 막고 사이드바 스크롤·선택 상태를 보존한다. 검색 입력·그룹/도메인 Select는 화면에 두지 않는다(AC-6, DEC-5) — 목록 요청에 q·group·domain을 보내지 않는다. 로딩(aria-busy)·목록 0건·목록 조회 실패(role=alert)·상세 404(전용 안내) 네 상태를 구분해 표시한다(AC-7). 모바일은 Sheet로 사이드바를 토글하고 데스크톱은 상시 노출한다(C-8) — Sheet는 기본 닫힘 상태라 테스트 환경에서 nav landmark가 중복되지 않는다. 기존 shadcn/ui(sheet·scroll-area·alert·skeleton·badge) 프리미티브와 전역 색상 토큰만 사용하고 raw HTML 렌더 플러그인을 추가하지 않는다(C-1, C-6).",
 *   "exports": ["SkillDocsPage"],
 *   "depends": ["api-client", "docs-types", "markdown-view", "sheet", "scroll-area", "alert", "skeleton", "badge"],
 *   "task": "143-260918-opds-스킬-문서-사이드바",
 *   "scenarios": ["S-8", "S-9", "S-10"]
 * }
 */

import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Menu } from "lucide-react";
import { apiClient, ApiError } from "@/lib/api";
import type { SkillCatalogItem, SkillCatalogListResponse, SkillDetailResponse } from "./types";
import { MarkdownView } from "@/components/markdown-view";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

const GROUP_ORDER = ["pilot", "operator", "standalone"] as const;
const GROUP_LABELS: Record<(typeof GROUP_ORDER)[number], string> = {
  pilot: "파일럿",
  operator: "오퍼레이터",
  standalone: "독립",
};

function groupListedItems(items: SkillCatalogItem[]) {
  const groups = new Map<string, SkillCatalogItem[]>();
  for (const item of items) {
    if (!item.listed) continue;
    const key = item.display_group;
    const bucket = groups.get(key) ?? [];
    bucket.push(item);
    groups.set(key, bucket);
  }
  return groups;
}

interface SidebarNavProps {
  items: SkillCatalogItem[];
  isLoading: boolean;
  isError: boolean;
  currentSkillId?: string;
  onNavigate?: () => void;
}

function SidebarNav({ items, isLoading, isError, currentSkillId, onNavigate }: SidebarNavProps) {
  const grouped = useMemo(() => groupListedItems(items), [items]);
  const hasAny = Array.from(grouped.values()).some((bucket) => bucket.length > 0);

  return (
    <nav aria-label="스킬 문서 사이드바" aria-busy={isLoading} className="flex h-full flex-col gap-4">
      <div className="flex flex-col gap-1 px-1">
        <h1 className="text-lg font-semibold">스킬 문서</h1>
        <p className="text-xs text-muted-foreground">OPAL 스킬 카탈로그를 그룹별로 열람합니다.</p>
      </div>

      {isLoading && (
        <div className="flex flex-col gap-2 px-1">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      )}

      {!isLoading && isError && (
        <Alert variant="destructive">
          <AlertDescription>스킬 목록을 불러오지 못했습니다</AlertDescription>
        </Alert>
      )}

      {!isLoading && !isError && !hasAny && (
        <p className="px-1 text-sm text-muted-foreground">문서화된 스킬이 없습니다</p>
      )}

      {!isLoading && !isError && hasAny && (
        <ScrollArea className="flex-1">
          <div className="flex flex-col gap-4 px-1 pb-4">
            {GROUP_ORDER.map((groupKey) => {
              const bucket = grouped.get(groupKey);
              if (!bucket || bucket.length === 0) return null;
              return (
                <div key={groupKey} className="flex flex-col gap-1">
                  <h2 className="px-1 text-xs font-semibold uppercase text-muted-foreground">
                    {GROUP_LABELS[groupKey]}
                  </h2>
                  <ul className="flex flex-col gap-0.5">
                    {bucket.map((item) => {
                      const isSelected = item.canonical_name === currentSkillId;
                      const extraAliases = item.aliases.filter(
                        (alias) => alias !== item.canonical_name,
                      );
                      return (
                        <li key={item.canonical_name}>
                          <Link
                            to={`/docs/skills/${item.canonical_name}`}
                            aria-current={isSelected ? "page" : undefined}
                            onClick={onNavigate}
                            className={cn(
                              "flex flex-col gap-0.5 rounded-md px-2 py-1.5 text-sm transition-colors",
                              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                              isSelected
                                ? "bg-accent text-accent-foreground font-medium"
                                : "hover:bg-accent/50",
                            )}
                          >
                            <span>{item.canonical_name}</span>
                            {extraAliases.length > 0 && (
                              <span className="text-xs text-muted-foreground">
                                {item.aliases.join(", ")}
                              </span>
                            )}
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      )}
    </nav>
  );
}

interface DetailPanelProps {
  skillId?: string;
  detail?: SkillDetailResponse;
  isLoading: boolean;
  apiError?: ApiError;
}

function DetailPanel({ skillId, detail, isLoading, apiError }: DetailPanelProps) {
  if (!skillId) {
    return (
      <div className="flex flex-1 items-center justify-center p-6">
        <p className="text-sm text-muted-foreground">
          왼쪽 사이드바에서 열람할 스킬을 선택하세요
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4 p-4 sm:p-6" aria-busy="true">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (apiError) {
    return (
      <div className="p-4 sm:p-6">
        <Alert variant="destructive">
          <AlertDescription>
            {apiError.code === "skill_not_found"
              ? "해당 스킬 문서를 찾을 수 없습니다"
              : "스킬 문서를 불러오는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!detail) {
    return null;
  }

  const { body } = detail;

  return (
    <div className="flex flex-col gap-4 p-4 sm:p-6">
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-xl font-semibold">{detail.description ?? detail.canonical_name}</h1>
          <Badge variant="secondary">{detail.display_group}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">{detail.canonical_name}</p>
        {detail.aliases.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {detail.aliases.map((alias) => (
              <Badge key={alias} variant="outline">
                {alias}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {body.origin === "skill_md" && (
        <Alert>
          <AlertDescription>
            README가 없어 SKILL.md 본문으로 대신 표시합니다.
          </AlertDescription>
        </Alert>
      )}

      {body.origin === null && (
        <p className="text-sm text-muted-foreground">이 스킬은 표시할 문서가 없습니다</p>
      )}

      {body.markdown && <MarkdownView content={body.markdown} />}
    </div>
  );
}

export function SkillDocsPage() {
  const { skillId } = useParams<{ skillId?: string }>();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const {
    data: catalog,
    isLoading: isListLoading,
    isError: isListError,
  } = useQuery({
    queryKey: ["docs-skills-sidebar"],
    queryFn: () => apiClient<SkillCatalogListResponse>("/api/docs/skills"),
  });

  const {
    data: detail,
    isLoading: isDetailLoading,
    isError: isDetailError,
    error: detailError,
  } = useQuery({
    queryKey: ["docs-skill", skillId],
    enabled: !!skillId,
    queryFn: () => apiClient<SkillDetailResponse>(`/api/docs/skills/${skillId}`),
  });

  const items = catalog?.items ?? [];
  const detailApiError = isDetailError ? (detailError as ApiError) : undefined;

  return (
    <div className="flex h-full min-h-0 flex-col sm:flex-row">
      <div className="flex items-center gap-2 border-b p-2 sm:hidden">
        <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
          <SheetTrigger asChild>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-accent"
            >
              <Menu className="h-4 w-4" />
              스킬 목록
            </button>
          </SheetTrigger>
          <SheetContent side="left" className="w-4/5 p-4">
            <SidebarNav
              items={items}
              isLoading={isListLoading}
              isError={isListError}
              currentSkillId={skillId}
              onNavigate={() => setMobileNavOpen(false)}
            />
          </SheetContent>
        </Sheet>
      </div>

      <aside className="hidden shrink-0 border-r p-3 sm:flex sm:w-72">
        <SidebarNav
          items={items}
          isLoading={isListLoading}
          isError={isListError}
          currentSkillId={skillId}
        />
      </aside>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <DetailPanel
          skillId={skillId}
          detail={detail}
          isLoading={!!skillId && isDetailLoading}
          apiError={detailApiError}
        />
      </div>
    </div>
  );
}
