/**
 * @header {
 *   "module": "docs-catalog-page",
 *   "layer": "page",
 *   "domain": "docs",
 *   "description": "GET /api/docs/skills 카탈로그 화면 — 검색·그룹/도메인 필터를 URL 쿼리(q/group/domain)와 동기화하고 새로고침·직접 진입 시 복원한다(PLAN DEC-8, S-12⑦). 로딩은 aria-busy 리전으로 표시하고, 빈 상태는 전체 0건(\"아직 문서화된 스킬이 없습니다\")과 검색 결과 0건(\"조건에 맞는 스킬이 없습니다\")을 구분한다(AC-3). 오류는 apiClient가 던지는 ApiError.code로 분기 — registry_unavailable은 role=alert + 재시도 버튼, 그 외(parse_error 포함)는 절대경로·스택을 노출하지 않는 일반 오류 메시지만 표시한다(C-1 읽기 전용 화면의 안전한 실패 노출). 카드는 role=link(react-router Link)로 상세 화면(/docs/skills/:skillId)에 연결되며 접근 가능한 이름에 canonical name·alias가 포함된다. 기존 shadcn/ui primitives(card·badge·input·select·alert·skeleton)와 전역 색상 토큰만 사용하고 별도 문서 프레임워크를 추가하지 않는다(C-1, DEC-8).",
 *   "exports": ["DocsCatalogPage"],
 *   "depends": ["api-client", "docs-types", "card", "badge", "input", "select", "alert", "skeleton"],
 *   "task": "140-260917-opdw-스킬-문서-화면",
 *   "scenarios": ["S-12"]
 * }
 */

import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient, ApiError } from "@/lib/api";
import type { SkillCatalogListResponse } from "./types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";

const ALL_VALUE = "__all__";

function buildQueryString(q: string, group: string, domain: string): string {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (group) params.set("group", group);
  if (domain) params.set("domain", domain);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function DocsCatalogPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get("q") ?? "";
  const group = searchParams.get("group") ?? "";
  const domain = searchParams.get("domain") ?? "";

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["docs-skills", q, group, domain],
    queryFn: () =>
      apiClient<SkillCatalogListResponse>(
        `/api/docs/skills${buildQueryString(q, group, domain)}`,
      ),
  });

  const apiError = isError ? (error as ApiError) : undefined;

  function updateParam(key: "q" | "group" | "domain", value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    setSearchParams(next, { replace: true });
  }

  const groupOptions = useMemo(() => data?.facets.groups ?? [], [data]);
  const domainOptions = useMemo(() => data?.facets.domains ?? [], [data]);

  const isSearchScoped = q.length > 0 || group.length > 0 || domain.length > 0;
  const totalCount = data?.meta.total ?? 0;
  const filteredCount = data?.meta.filtered ?? data?.items.length ?? 0;

  return (
    <div className="flex flex-col gap-4 p-4 sm:p-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold">스킬 문서</h1>
        <p className="text-sm text-muted-foreground">
          OPAL 스킬 카탈로그를 검색하고 상세 문서를 열람합니다.
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex-1">
          <label htmlFor="docs-skill-search" className="sr-only">
            스킬 검색
          </label>
          <Input
            id="docs-skill-search"
            type="search"
            role="textbox"
            aria-label="스킬 검색"
            placeholder="스킬 이름, alias, 설명으로 검색"
            value={q}
            onChange={(e) => updateParam("q", e.target.value)}
          />
        </div>

        <Select
          value={group || ALL_VALUE}
          onValueChange={(v) => updateParam("group", v === ALL_VALUE ? "" : v)}
        >
          <SelectTrigger className="sm:w-48" aria-label="그룹 필터">
            <SelectValue placeholder="전체 그룹" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_VALUE}>전체 그룹</SelectItem>
            {groupOptions.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label ?? opt.value} ({opt.count})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={domain || ALL_VALUE}
          onValueChange={(v) => updateParam("domain", v === ALL_VALUE ? "" : v)}
        >
          <SelectTrigger className="sm:w-48" aria-label="도메인 필터">
            <SelectValue placeholder="전체 도메인" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_VALUE}>전체 도메인</SelectItem>
            {domainOptions.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label ?? opt.value} ({opt.count})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div aria-busy={isLoading} aria-live="polite" className="flex flex-col gap-4">
        {isLoading && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-32 w-full rounded-lg" />
            ))}
          </div>
        )}

        {!isLoading && apiError && apiError.code === "registry_unavailable" && (
          <Alert variant="destructive">
            <AlertDescription className="flex flex-col gap-2">
              <span>{apiError.message}</span>
              <button
                type="button"
                role="button"
                onClick={() => refetch()}
                className="w-fit rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-accent"
              >
                다시 시도
              </button>
            </AlertDescription>
          </Alert>
        )}

        {!isLoading && apiError && apiError.code !== "registry_unavailable" && (
          <Alert variant="destructive">
            <AlertDescription>
              스킬 목록을 불러오는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.
            </AlertDescription>
          </Alert>
        )}

        {!isLoading && !apiError && data && data.items.length === 0 && totalCount === 0 && (
          <p className="text-sm text-muted-foreground">아직 문서화된 스킬이 없습니다</p>
        )}

        {!isLoading &&
          !apiError &&
          data &&
          data.items.length === 0 &&
          totalCount > 0 &&
          (isSearchScoped || filteredCount === 0) && (
            <p className="text-sm text-muted-foreground">조건에 맞는 스킬이 없습니다</p>
          )}

        {!isLoading && !apiError && data && data.items.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((item) => (
              <Link
                key={item.canonical_name}
                to={`/docs/skills/${item.canonical_name}`}
                role="link"
                aria-label={`${item.canonical_name}${
                  item.aliases.length > 0 ? ` (${item.aliases.join(", ")})` : ""
                }`}
                className="block rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <Card className="h-full transition-colors hover:bg-accent/50">
                  <CardHeader className="flex flex-col gap-1 pb-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold">{item.canonical_name}</span>
                      <Badge variant="secondary">{item.display_group}</Badge>
                    </div>
                    {item.aliases.filter((alias) => alias !== item.canonical_name).length >
                      0 && (
                      <div className="flex flex-wrap gap-1">
                        {item.aliases
                          .filter((alias) => alias !== item.canonical_name)
                          .map((alias) => (
                            <Badge key={alias} variant="outline">
                              {alias}
                            </Badge>
                          ))}
                      </div>
                    )}
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {item.description ?? "설명 없음"}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
