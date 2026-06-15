/**
 * @header {
 *   "module": "doctor-page",
 *   "layer": "page",
 *   "domain": "doctor",
 *   "description": "환경(doctor) 화면 — 4섹션 accordion + 체크 아이콘(상태색 토큰) + MCP 카드 + 스킬 목록 + 실패 alert. contextProject(ui-store) 구독으로 스위처 연동.",
 *   "exports": ["DoctorPage"],
 *   "depends": ["api-client", "card", "accordion", "badge", "alert", "tooltip", "skeleton", "ui-store"]
 * }
 */

import { useQuery } from "@tanstack/react-query";
import { useUiStore } from "@/store/ui-store";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Stethoscope,
  Plug,
  Wrench,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/* 타입                                                                  */
/* ------------------------------------------------------------------ */

interface CheckItem {
  status: string; // "ok" | "warn" | "fail"
  message: string;
}

interface DoctorSection {
  name: string;
  index: number;
  total_sections: number;
  items: CheckItem[];
}

interface DoctorCounts {
  ok: number;
  warn: number;
  fail: number;
  total: number;
}

interface DoctorReport {
  sections: DoctorSection[];
  counts: DoctorCounts;
  verdict: string;
  skills: Record<string, unknown>[];
  warning: string | null;
}

/* ------------------------------------------------------------------ */
/* 유틸                                                                  */
/* ------------------------------------------------------------------ */

function StatusIcon({ status }: { status: string }) {
  if (status === "ok") {
    return <CheckCircle2 className="h-4 w-4 text-status-done shrink-0" />;
  }
  if (status === "warn") {
    return <AlertTriangle className="h-4 w-4 text-status-stale shrink-0" />;
  }
  return <XCircle className="h-4 w-4 text-status-blocked shrink-0" />;
}

function verdictBadgeClass(verdict: string): string {
  if (verdict.includes("정상") || verdict.toLowerCase().includes("ok") || verdict.toLowerCase().includes("pass")) {
    return "bg-status-done/20 text-status-done border-status-done/30";
  }
  if (verdict.includes("경고") || verdict.toLowerCase().includes("warn")) {
    return "bg-status-stale/20 text-status-stale border-status-stale/30";
  }
  return "bg-status-blocked/20 text-status-blocked border-status-blocked/30";
}

/* ------------------------------------------------------------------ */
/* CheckSectionView                                                      */
/* ------------------------------------------------------------------ */

function CheckSectionView({ section }: { section: DoctorSection }) {
  const hasFail = section.items.some((i) => i.status === "fail");
  const hasWarn = section.items.some((i) => i.status === "warn");

  return (
    <AccordionItem value={section.name} className="border rounded-lg mb-2 px-0 overflow-hidden">
      <AccordionTrigger className="px-4 py-3 hover:no-underline hover:bg-accent/50 [&[data-state=open]]:bg-accent/30">
        <div className="flex items-center gap-3 w-full text-left">
          <span
            className={cn(
              "h-2 w-2 rounded-full shrink-0",
              hasFail ? "bg-status-blocked" : hasWarn ? "bg-status-stale" : "bg-status-done",
            )}
          />
          <span className="text-sm font-medium flex-1">{section.name}</span>
          <div className="flex items-center gap-1.5 mr-2">
            {section.items.filter((i) => i.status === "ok").length > 0 && (
              <span className="text-[10px] text-status-done tabular-nums">
                ✓{section.items.filter((i) => i.status === "ok").length}
              </span>
            )}
            {section.items.filter((i) => i.status === "warn").length > 0 && (
              <span className="text-[10px] text-status-stale tabular-nums">
                ⚠{section.items.filter((i) => i.status === "warn").length}
              </span>
            )}
            {section.items.filter((i) => i.status === "fail").length > 0 && (
              <span className="text-[10px] text-status-blocked tabular-nums">
                ✗{section.items.filter((i) => i.status === "fail").length}
              </span>
            )}
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent className="px-4 pb-3 pt-1">
        {section.items.length === 0 ? (
          <p className="text-xs text-muted-foreground">항목 없음</p>
        ) : (
          <ul className="space-y-1.5">
            {section.items.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <StatusIcon status={item.status} />
                <span className={cn(
                  "text-sm",
                  item.status === "fail" && "text-status-blocked",
                  item.status === "warn" && "text-status-stale",
                )}>
                  {item.message}
                </span>
              </li>
            ))}
          </ul>
        )}
      </AccordionContent>
    </AccordionItem>
  );
}

/* ------------------------------------------------------------------ */
/* McpCards                                                              */
/* ------------------------------------------------------------------ */

function McpCards({ sections }: { sections: DoctorSection[] }) {
  // doctor 섹션에서 MCP 관련 섹션 추출
  const mcpSection = sections.find(
    (s) => s.name.toLowerCase().includes("mcp") || s.name.toLowerCase().includes("server"),
  );

  if (!mcpSection || mcpSection.items.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Plug className="h-4 w-4 text-muted-foreground" />
            MCP 서버
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">MCP 정보 없음</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Plug className="h-4 w-4 text-muted-foreground" />
          MCP 서버
          <Badge variant="secondary" className="ml-auto text-xs tabular-nums">
            {mcpSection.items.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
          {mcpSection.items.map((item, idx) => (
            <Tooltip key={idx}>
              <TooltipTrigger asChild>
                <div
                  className={cn(
                    "flex items-center gap-2 rounded-md border px-3 py-2 text-xs",
                    item.status === "ok"
                      ? "border-status-done/30 bg-status-done/5"
                      : item.status === "warn"
                        ? "border-status-stale/30 bg-status-stale/5"
                        : "border-status-blocked/30 bg-status-blocked/5",
                  )}
                >
                  <StatusIcon status={item.status} />
                  <span className="truncate">{item.message.split(":")[0]?.trim() ?? item.message}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent className="text-xs max-w-xs">
                {item.message}
              </TooltipContent>
            </Tooltip>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* SkillList                                                             */
/* ------------------------------------------------------------------ */

function SkillList({ skills }: { skills: Record<string, unknown>[] }) {
  if (skills.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Wrench className="h-4 w-4 text-muted-foreground" />
          스킬 목록
          <Badge variant="secondary" className="ml-auto text-xs tabular-nums">
            {skills.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {skills.map((skill, idx) => {
            const name = String(skill.name ?? skill.id ?? `skill-${idx}`);
            const version = skill.version ? `v${String(skill.version)}` : null;
            return (
              <Tooltip key={idx}>
                <TooltipTrigger asChild>
                  <Badge variant="outline" className="text-xs cursor-default">
                    {name}
                    {version && <span className="ml-1 text-muted-foreground">{version}</span>}
                  </Badge>
                </TooltipTrigger>
                {skill.description != null && (
                  <TooltipContent className="text-xs max-w-xs">
                    {String(skill.description)}
                  </TooltipContent>
                )}
              </Tooltip>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* FailureAlerts — 실패 항목 alert                                      */
/* ------------------------------------------------------------------ */

function FailureAlerts({ sections }: { sections: DoctorSection[] }) {
  const failItems: { section: string; message: string }[] = [];
  for (const sec of sections) {
    for (const item of sec.items) {
      if (item.status === "fail") {
        failItems.push({ section: sec.name, message: item.message });
      }
    }
  }

  if (failItems.length === 0) return null;

  return (
    <Alert variant="destructive" className="border-status-blocked/50 bg-status-blocked/5">
      <XCircle className="h-4 w-4" />
      <AlertTitle className="text-sm">환경 점검 실패 {failItems.length}건</AlertTitle>
      <AlertDescription>
        <ul className="mt-2 space-y-1">
          {failItems.map((f, i) => (
            <li key={i} className="text-xs">
              <span className="font-medium">[{f.section}]</span> {f.message}
            </li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  );
}

/* ------------------------------------------------------------------ */
/* DoctorPage — 루트 컴포넌트                                            */
/* ------------------------------------------------------------------ */

export function DoctorPage() {
  const contextProject = useUiStore((s) => s.contextProject);
  const projectParam = contextProject ?? "";

  // 프로젝트 경로에서 마지막 디렉토리명 추출 (표시용)
  const projectDisplayName = projectParam
    ? projectParam.split("/").filter(Boolean).pop() ?? projectParam
    : null;

  const { data, isLoading, isError } = useQuery<DoctorReport>({
    queryKey: ["doctor", projectParam],
    queryFn: () =>
      apiClient<DoctorReport>(
        projectParam
          ? `/api/doctor?project=${encodeURIComponent(projectParam)}`
          : "/api/doctor",
      ),
    retry: 1,
  });

  return (
    <div className="flex flex-1 flex-col gap-4 p-6 overflow-auto">
      {/* 헤더 */}
      <div className="flex items-center gap-3">
        <Stethoscope className="h-5 w-5 text-muted-foreground" />
        <h1 className="text-sm font-semibold">
          환경 점검{projectDisplayName && <span className="ml-2 font-normal text-muted-foreground text-xs">— {projectDisplayName}</span>}
        </h1>
        {data?.verdict && (
          <Badge
            variant="outline"
            className={cn("ml-auto text-xs", verdictBadgeClass(data.verdict))}
          >
            {data.verdict}
          </Badge>
        )}
        {data?.counts && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground ml-2">
            <span className="text-status-done tabular-nums">✓{data.counts.ok}</span>
            {data.counts.warn > 0 && (
              <span className="text-status-stale tabular-nums">⚠{data.counts.warn}</span>
            )}
            {data.counts.fail > 0 && (
              <span className="text-status-blocked tabular-nums">✗{data.counts.fail}</span>
            )}
          </div>
        )}
      </div>

      {/* 에러 상태 */}
      {isError && (
        <Alert variant="destructive" className="border-status-blocked/50 bg-status-blocked/5">
          <XCircle className="h-4 w-4" />
          <AlertTitle className="text-sm">API 연결 실패</AlertTitle>
          <AlertDescription className="text-xs">
            opal-cli console start 명령으로 데몬을 기동하세요.
          </AlertDescription>
        </Alert>
      )}

      {/* 경고 */}
      {data?.warning && (
        <Alert className="border-status-stale/30 bg-status-stale/5">
          <AlertTriangle className="h-4 w-4 text-status-stale" />
          <AlertDescription className="text-sm">{data.warning}</AlertDescription>
        </Alert>
      )}

      {/* 실패 alert */}
      {!isLoading && data && <FailureAlerts sections={data.sections} />}

      {/* 로딩 */}
      {isLoading && (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      )}

      {/* 섹션 accordion */}
      {!isLoading && data && data.sections.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
            체크 섹션
          </p>
          <Accordion type="multiple" defaultValue={data.sections.map((s) => s.name)}>
            {data.sections.map((section) => (
              <CheckSectionView key={section.name} section={section} />
            ))}
          </Accordion>
        </div>
      )}

      {/* 데이터 없을 때 */}
      {!isLoading && !isError && data && data.sections.length === 0 && (
        <div className="flex flex-col items-center gap-3 py-12 text-muted-foreground">
          <Stethoscope className="h-10 w-10 opacity-30" />
          <p className="text-sm">점검 결과 없음</p>
          <p className="text-xs">opal-cli doctor를 실행하면 결과가 표시됩니다</p>
        </div>
      )}

      {/* MCP 카드 */}
      {!isLoading && data && <McpCards sections={data.sections} />}

      {/* 스킬 목록 */}
      {!isLoading && data && data.skills.length > 0 && (
        <SkillList skills={data.skills} />
      )}
    </div>
  );
}
