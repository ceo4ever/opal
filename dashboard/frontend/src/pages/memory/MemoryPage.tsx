/**
 * @header {
 *   "module": "memory-page",
 *   "layer": "page",
 *   "domain": "memory",
 *   "description": "메모리 화면 — 카테고리 리스트(badge·검색·태그칩 필터) + 작업 히스토리 타임라인 + 상세 Drawer 마크다운. contextProject(ui-store) 구독으로 스위처 연동.",
 *   "exports": ["MemoryPage"],
 *   "depends": ["api-client", "badge", "input", "select", "scroll-area", "drawer", "skeleton", "separator", "ui-store"]
 * }
 */

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useUiStore } from "@/store/ui-store";
import {
  Brain,
  Search,
  Clock,
  BookOpen,
  ChevronRight,
  Inbox,
} from "lucide-react";
import { MarkdownView } from "@/components/markdown-view";
import { apiClient } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/* 타입                                                                  */
/* ------------------------------------------------------------------ */

interface MemoryRow {
  date: string;
  category: string;
  status: string;
  file: string;
  description: string;
}

interface HistoryRow {
  date: string;
  task: string;
  stage: string;
  path: string;
  start: string | null;
  end: string | null;
}

interface MemoryIndex {
  rows: MemoryRow[];
  history: HistoryRow[];
  warning: string | null;
}

/* ------------------------------------------------------------------ */
/* 유틸                                                                  */
/* ------------------------------------------------------------------ */

const CATEGORY_COLORS: Record<string, string> = {
  feedback: "bg-status-running/20 text-status-running border-status-running/30",
  project: "bg-brand-primary/20 text-brand-primary border-brand-primary/30",
  user: "bg-status-stale/20 text-status-stale border-status-stale/30",
  reference: "bg-status-done/20 text-status-done border-status-done/30",
};

function categoryClass(category: string): string {
  return CATEGORY_COLORS[category.toLowerCase()] ?? "bg-muted text-muted-foreground";
}

// 한 줄 요약(description)을 구조화: 원문자(①②③) 앞 + 'XX). ' 문장 경계 뒤에 단락 구분.
// 본문 파일 없는 메모리의 인덱스 요약을 일목요연하게 렌더하기 위함.
function structureMemoryText(text: string): string {
  return text
    .replace(/([①-⑳])/g, "\n\n$1 ") // ①~⑳ 앞 단락 구분
    .replace(/\)\.\s+/g, ").\n\n") // '...). ' 문장 경계 뒤 단락 구분
    .replace(/^\n+/, "") // 선두 빈 줄 제거
    .trim();
}

function stageClass(stage: string): string {
  if (stage.toLowerCase().includes("done")) return "bg-status-done";
  if (stage.toLowerCase().includes("execute")) return "bg-status-running";
  if (stage.toLowerCase().includes("blocked")) return "bg-status-blocked";
  return "bg-status-todo";
}

/* ------------------------------------------------------------------ */
/* MemoryListItem                                                        */
/* ------------------------------------------------------------------ */

function MemoryListItem({
  row,
  isSelected,
  onClick,
}: {
  row: MemoryRow;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={cn(
        "w-full flex items-start gap-3 rounded-md px-3 py-3 text-left transition-colors hover:bg-accent",
        isSelected && "bg-accent",
      )}
      onClick={onClick}
    >
      <Brain className="h-4 w-4 shrink-0 text-muted-foreground mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge
            variant="outline"
            className={cn("text-[10px] px-1.5 py-0 shrink-0", categoryClass(row.category))}
          >
            #{row.category}
          </Badge>
          {row.file && (
            <span className="text-[10px] font-mono text-muted-foreground truncate">
              {row.file}
            </span>
          )}
        </div>
        <p className="text-sm mt-1 leading-snug line-clamp-2">{row.description}</p>
        {row.date && (
          <p className="text-[10px] text-muted-foreground mt-1">{row.date}</p>
        )}
      </div>
      <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground mt-1" />
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* HistoryTimeline                                                       */
/* ------------------------------------------------------------------ */

function HistoryTimeline({ history }: { history: HistoryRow[] }) {
  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-12 text-muted-foreground">
        <Clock className="h-8 w-8 opacity-40" />
        <p className="text-sm">작업 히스토리 없음</p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {history.map((row, idx) => (
        <div key={idx} className="flex gap-3">
          {/* 타임라인 라인 + 점 */}
          <div className="flex flex-col items-center">
            <div className={cn("mt-3 h-2.5 w-2.5 rounded-full shrink-0", stageClass(row.stage))} />
            {idx < history.length - 1 && (
              <div className="w-px flex-1 bg-border mt-1" />
            )}
          </div>

          {/* 콘텐츠 */}
          <div className="pb-4 min-w-0 flex-1">
            <div className="flex items-baseline gap-2 flex-wrap">
              <span className="text-xs font-mono text-muted-foreground shrink-0">
                {row.date}
              </span>
              {row.task && (
                <span className="text-sm font-medium truncate">{row.task}</span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-0.5 flex-wrap">
              {row.stage && (
                <Badge variant="outline" className="text-[10px] font-mono px-1.5 py-0">
                  {row.stage}
                </Badge>
              )}
              {row.path && (
                <span className="text-[10px] text-muted-foreground font-mono truncate max-w-[200px]">
                  {row.path}
                </span>
              )}
            </div>
            {(row.start || row.end) && (
              <p className="text-[10px] text-muted-foreground mt-0.5">
                {row.start && `시작: ${row.start}`}
                {row.start && row.end && " · "}
                {row.end && `완료: ${row.end}`}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* MemoryDrawer                                                          */
/* ------------------------------------------------------------------ */

function MemoryDrawer({
  open,
  onClose,
  row,
  project,
}: {
  open: boolean;
  onClose: () => void;
  row: MemoryRow | null;
  project: string;
}) {
  const { data, isLoading } = useQuery<{ content: string }>({
    queryKey: ["memory-detail", project, row?.file],
    queryFn: () =>
      apiClient<{ content: string }>(
        `/api/memory?project=${encodeURIComponent(project)}&file=${encodeURIComponent(row!.file)}`,
      ),
    enabled: open && !!row?.file && !!project,
    retry: 1,
  });

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent
        side="right"
        className="w-[min(50vw,800px)] sm:max-w-[min(50vw,800px)] p-0 flex flex-col h-full overflow-hidden"
      >
        <SheetHeader className="border-b px-6 py-4 shrink-0">
          <SheetTitle className="flex items-center gap-2 text-sm">
            <BookOpen className="h-4 w-4" />
            {row?.file ?? "메모리 상세"}
          </SheetTitle>
        </SheetHeader>
        <div className="flex-1 min-h-0 overflow-y-auto px-6 py-4">
          {!row?.file ? (
            <p className="text-sm text-muted-foreground">파일 정보 없음</p>
          ) : isLoading ? (
            <div className="space-y-3">
              {[...Array(8)].map((_, i) => (
                <Skeleton key={i} className="h-4 w-full" />
              ))}
            </div>
          ) : data?.content ? (
            <MarkdownView content={data.content} />
          ) : (
            <div className="space-y-3">
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground">카테고리</p>
                <Badge variant="outline" className={cn("text-xs", categoryClass(row.category))}>
                  #{row.category}
                </Badge>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">내용</p>
                <MarkdownView content={structureMemoryText(row.description)} />
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

/* ------------------------------------------------------------------ */
/* MemoryPage — 루트 컴포넌트                                            */
/* ------------------------------------------------------------------ */

export function MemoryPage() {
  const contextProject = useUiStore((s) => s.contextProject);
  const projectParam = contextProject ?? "";
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [selectedRow, setSelectedRow] = useState<MemoryRow | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const { data, isLoading, isError } = useQuery<MemoryIndex>({
    queryKey: ["memory", projectParam],
    queryFn: () =>
      apiClient<MemoryIndex>(
        projectParam
          ? `/api/memory?project=${encodeURIComponent(projectParam)}`
          : "/api/memory",
      ),
    retry: 1,
    enabled: !!projectParam,
  });

  // 카테고리 목록 추출
  const categories = useMemo(() => {
    const cats = new Set((data?.rows ?? []).map((r) => r.category).filter(Boolean));
    return Array.from(cats);
  }, [data?.rows]);

  // 필터링
  const filteredRows = useMemo(() => {
    return (data?.rows ?? []).filter((row) => {
      const matchSearch =
        !search ||
        row.description.toLowerCase().includes(search.toLowerCase()) ||
        row.file.toLowerCase().includes(search.toLowerCase());
      const matchCategory = categoryFilter === "all" || row.category === categoryFilter;
      return matchSearch && matchCategory;
    });
  }, [data?.rows, search, categoryFilter]);

  const handleMemoryClick = (row: MemoryRow) => {
    setSelectedRow(row);
    setDrawerOpen(true);
  };

  // 프로젝트 경로에서 마지막 디렉토리명 추출 (표시용)
  const projectDisplayName = projectParam
    ? projectParam.split("/").filter(Boolean).pop() ?? projectParam
    : null;

  if (!projectParam) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 p-6 text-muted-foreground">
        <Inbox className="h-10 w-10 opacity-30" />
        <p className="text-sm">사이드바에서 프로젝트를 선택하세요</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* 헤더 */}
      <div className="border-b px-6 py-4 space-y-3 shrink-0">
        <div className="flex items-center justify-between">
          <h1 className="text-sm font-semibold">
            메모리{projectDisplayName && <span className="ml-2 font-normal text-muted-foreground">— {projectDisplayName}</span>}
          </h1>
          <span className="text-xs text-muted-foreground font-mono truncate max-w-[240px]">
            {projectParam}
          </span>
        </div>
        {/* 검색 + 필터 */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              className="pl-8 h-8 text-xs"
              placeholder="메모리 검색..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger className="h-8 w-32 text-xs">
              <SelectValue placeholder="카테고리" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all" className="text-xs">전체</SelectItem>
              {categories.map((cat) => (
                <SelectItem key={cat} value={cat} className="text-xs">
                  #{cat}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* 태그칩 필터 */}
        {categories.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            <button
              className={cn(
                "rounded-full px-2.5 py-0.5 text-xs border transition-colors",
                categoryFilter === "all"
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border hover:bg-accent",
              )}
              onClick={() => setCategoryFilter("all")}
            >
              전체
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                className={cn(
                  "rounded-full px-2.5 py-0.5 text-xs border transition-colors",
                  categoryFilter === cat
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border hover:bg-accent",
                )}
                onClick={() => setCategoryFilter(categoryFilter === cat ? "all" : cat)}
              >
                #{cat}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 메인 영역 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 좌: 메모리 리스트 */}
        <div className="flex w-[55%] flex-col border-r overflow-hidden">
          <ScrollArea className="flex-1">
            <div className="p-3 space-y-0.5">
              {isLoading ? (
                [...Array(5)].map((_, i) => (
                  <div key={i} className="px-3 py-3 space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-full" />
                  </div>
                ))
              ) : isError ? (
                <div className="px-3 py-8 text-center text-sm text-muted-foreground">
                  데이터를 불러올 수 없습니다
                </div>
              ) : filteredRows.length === 0 ? (
                <div className="flex flex-col items-center gap-2 py-12 text-muted-foreground">
                  <Brain className="h-8 w-8 opacity-40" />
                  <p className="text-sm">메모리 없음</p>
                </div>
              ) : (
                filteredRows.map((row, idx) => (
                  <MemoryListItem
                    key={idx}
                    row={row}
                    isSelected={selectedRow === row}
                    onClick={() => handleMemoryClick(row)}
                  />
                ))
              )}
            </div>
          </ScrollArea>
        </div>

        {/* 우: 히스토리 타임라인 */}
        <div className="flex flex-col overflow-hidden flex-1">
          <div className="border-b px-4 py-3 shrink-0">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-medium">작업 히스토리</span>
              {data?.history && (
                <Badge variant="secondary" className="ml-auto text-xs tabular-nums">
                  {data.history.length}
                </Badge>
              )}
            </div>
          </div>
          <ScrollArea className="flex-1 px-4 py-4">
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex gap-3">
                    <Skeleton className="h-3 w-3 rounded-full mt-1 shrink-0" />
                    <div className="space-y-1 flex-1">
                      <Skeleton className="h-3 w-24" />
                      <Skeleton className="h-4 w-48" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <HistoryTimeline history={data?.history ?? []} />
            )}
          </ScrollArea>
        </div>
      </div>

      {/* 메모리 상세 Drawer */}
      <MemoryDrawer
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedRow(null);
        }}
        row={selectedRow}
        project={projectParam}
      />
    </div>
  );
}
