/**
 * @header {
 *   "module": "docs-detail-page",
 *   "layer": "page",
 *   "domain": "docs",
 *   "description": "GET /api/docs/skills/{skillId} 상세 화면 — alias URL로 진입하면 canonical URL로 navigate(replace:true)해 뒤로가기 히스토리를 늘리지 않는다(S-12⑥). source.available=false(DEC-1, 200 partial)는 오류가 아니라 메타(제목·설명·aliases 등)는 유지한 채 role=alert로 본문 부재를 알린다. Quick Start 예시 명령은 프롬프트 문자 없는 원문 그대로 상시 노출하고(C-4, DEC-9) 복사 버튼(\"예시 복사\")은 navigator.clipboard.writeText로 그 원문을 전달하며 성공 시 \"복사됨\" 피드백을, 클립보드 API 실패 시에도 명령 문자열이 화면에 노출된 채 유지되는 수동 복사 폴백을 제공한다. 본문 Markdown(usage_markdown·when_to_use_markdown)은 기존 markdown-view(원격 raw HTML 플러그인 없음)로 렌더한다(DEC-8). 적용 불가한 섹션(quick_start·pipeline·related_skills 등)은 거짓 기본값 대신 생략하거나 \"없음\"으로 표시한다(DEC-3/AC-3). 기존 shadcn/ui primitives와 전역 색상 토큰만 사용한다(C-1).",
 *   "exports": ["DocsDetailPage"],
 *   "depends": ["api-client", "docs-types", "markdown-view", "card", "badge", "alert"],
 *   "task": "140-260917-opdw-스킬-문서-화면",
 *   "scenarios": ["S-12"]
 * }
 */

import { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient, ApiError } from "@/lib/api";
import type { SkillDetailResponse } from "./types";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { MarkdownView } from "@/components/markdown-view";

export function DocsDetailPage() {
  const { skillId } = useParams<{ skillId: string }>();
  const navigate = useNavigate();
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["docs-skill", skillId],
    enabled: !!skillId,
    queryFn: () => apiClient<SkillDetailResponse>(`/api/docs/skills/${skillId}`),
  });

  // alias로 진입한 경우 canonical URL로 replace — 뒤로가기 히스토리를 늘리지 않는다 (S-12⑥)
  useEffect(() => {
    if (data && data.resolved_from.kind === "alias" && data.canonical_name !== skillId) {
      navigate(`/docs/skills/${data.canonical_name}`, { replace: true });
    }
  }, [data, skillId, navigate]);

  const apiError = isError ? (error as ApiError) : undefined;

  async function handleCopy(command: string) {
    try {
      await navigator.clipboard.writeText(command);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
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

  if (!data) {
    return null;
  }

  const quickStartCommand = data.quick_start?.command;

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6">
      <div className="flex flex-col gap-2">
        <Link to="/docs/skills" className="w-fit text-sm text-muted-foreground hover:underline">
          ← 스킬 목록으로
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-xl font-semibold">{data.description ?? data.canonical_name}</h1>
          <Badge variant="secondary">{data.display_group}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">{data.canonical_name}</p>
        {data.aliases.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {data.aliases.map((alias) => (
              <Badge key={alias} variant="outline">
                {alias}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {!data.source.available && (
        <Alert variant="destructive">
          <AlertDescription>
            원본 문서(SKILL.md)를 읽을 수 없어 본문을 표시할 수 없습니다. 위 요약 정보만
            제공됩니다.
          </AlertDescription>
        </Alert>
      )}

      {quickStartCommand && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-muted-foreground">Quick Start</h2>
          <div className="flex flex-col gap-2 rounded-md border bg-muted/40 p-3">
            <code className="whitespace-pre-wrap break-all text-sm">{quickStartCommand}</code>
            <div className="flex items-center gap-2">
              <button
                type="button"
                role="button"
                onClick={() => handleCopy(quickStartCommand)}
                className="w-fit rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-accent"
              >
                예시 복사
              </button>
              {copyState === "copied" && (
                <span className="text-sm text-muted-foreground">복사됨</span>
              )}
              {copyState === "failed" && (
                <span className="text-sm text-muted-foreground">
                  자동 복사에 실패했습니다. 위 명령을 직접 선택해 복사해주세요.
                </span>
              )}
            </div>
          </div>
        </section>
      )}

      {data.when_to_use_markdown ? (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-muted-foreground">언제 사용하나요</h2>
          <MarkdownView content={data.when_to_use_markdown} />
        </section>
      ) : (
        !data.source.available && (
          <section className="flex flex-col gap-2">
            <h2 className="text-sm font-semibold text-muted-foreground">언제 사용하나요</h2>
            <p className="text-sm text-muted-foreground">없음</p>
          </section>
        )
      )}

      {data.usage_markdown ? (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-muted-foreground">사용법</h2>
          <MarkdownView content={data.usage_markdown} />
        </section>
      ) : (
        !data.source.available && (
          <section className="flex flex-col gap-2">
            <h2 className="text-sm font-semibold text-muted-foreground">사용법</h2>
            <p className="text-sm text-muted-foreground">없음</p>
          </section>
        )
      )}

      {data.arguments.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-muted-foreground">Arguments</h2>
          <ul className="flex flex-col gap-1 text-sm">
            {data.arguments.map((arg) => (
              <li key={arg.name}>
                <code>{arg.name}</code>
                {arg.required ? " (필수)" : ""} — {arg.description ?? "설명 없음"}
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.options.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-muted-foreground">Options</h2>
          <ul className="flex flex-col gap-1 text-sm">
            {data.options.map((opt) => (
              <li key={opt.name}>
                <code>{opt.name}</code> — {opt.description ?? "설명 없음"}
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.examples.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-muted-foreground">Examples</h2>
          <ul className="flex flex-col gap-2 text-sm">
            {data.examples.map((ex, idx) => (
              <li key={`${ex.command}-${idx}`} className="rounded-md border bg-muted/40 p-2">
                <code className="whitespace-pre-wrap break-all">{ex.command}</code>
                {ex.description && (
                  <p className="mt-1 text-muted-foreground">{ex.description}</p>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.related_skills.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-muted-foreground">관련 스킬</h2>
          <div className="flex flex-wrap gap-2">
            {data.related_skills.map((rel) => (
              <Link
                key={rel.canonical_name}
                to={`/docs/skills/${rel.canonical_name}`}
                className="text-sm text-primary hover:underline"
              >
                {rel.canonical_name}
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
