/**
 * @header {
 *   "module": "tasks-page",
 *   "layer": "page",
 *   "domain": "tasks",
 *   "description": "태스크 칸반 화면 — 상태 5컬럼(대기/진행중/블로킹/완료/아카이브) + 카드(ID·제목·진행률·badge·단계 뱃지 진행중 강조) + 카드 클릭→Sheet(right 사이드 패널, 파이프라인 스테퍼 stage 그룹 단계당 1스텝+done/total 카운트+산출물 탭 마크다운 스크롤). 완료·아카이브 컬럼 최근순 정렬. [MUST] 읽기 전용: dnd-kit sensors 비활성·🔒 badge 상시·grab 커서 미사용. contextProject(ui-store) 전역 구독 — 스위처 연동.",
 *   "exports": ["TasksPage"],
 *   "depends": ["api-client", "card", "badge", "progress", "sheet", "tabs", "scroll-area", "skeleton", "separator", "markdown-view", "ui-store"]
 * }
 */

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { useUiStore } from "@/store/ui-store";
import {
  Lock,
  Inbox,
  CheckCircle2,
  AlertTriangle,
  PlayCircle,
  Clock,
  FileText,
  ChevronRight,
  AlertCircle,
  Archive,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { MarkdownView } from "@/components/markdown-view";
import { cn } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/* 타입                                                                  */
/* ------------------------------------------------------------------ */

type KanbanColumn = "pending" | "in_progress" | "blocked" | "done" | "archive";

interface TaskCard {
  task_id: string;
  title: string;
  skill: string;
  mode: string;
  column: KanbanColumn;
  current_stage: string;
  progress: number;
  updated_at: string;
  artifact_count: number;
}

interface PipelineRow {
  row: number;
  stage: string;
  status: string;
  updated_at: string;
}

interface PipelineStageGroup {
  stage: string;
  done_count: number;
  total: number;
  status: string; // done | in_progress | pending | blocked
  rows: PipelineRow[];
}

interface TaskDetail {
  task_id: string;
  title: string;
  skill: string;
  mode: string;
  current_status: string;
  current_stage: string;
  progress: number;
  pipeline: PipelineStageGroup[];
  artifacts: string[];
  updated_at: string;
}

/* ------------------------------------------------------------------ */
/* 컬럼 설정                                                            */
/* ------------------------------------------------------------------ */

const COLUMNS: { key: KanbanColumn; label: string; icon: React.ComponentType<{ className?: string }>; statusClass: string }[] = [
  { key: "pending", label: "대기", icon: Inbox, statusClass: "text-status-todo" },
  { key: "in_progress", label: "진행중", icon: PlayCircle, statusClass: "text-status-running" },
  { key: "blocked", label: "블로킹", icon: AlertTriangle, statusClass: "text-status-blocked" },
  { key: "done", label: "완료", icon: CheckCircle2, statusClass: "text-status-done" },
  { key: "archive", label: "아카이브", icon: Archive, statusClass: "text-muted-foreground" },
];

function columnBorderClass(col: KanbanColumn) {
  return {
    pending: "border-l-status-todo",
    in_progress: "border-l-status-running",
    blocked: "border-l-status-blocked",
    done: "border-l-status-done",
    archive: "border-l-border",
  }[col];
}

function stageStatusClass(status: string) {
  if (status === "done") return "bg-status-done";
  if (status === "in_progress") return "bg-status-running";
  if (status === "blocked") return "bg-status-blocked";
  return "bg-status-todo";
}

/* ------------------------------------------------------------------ */
/* KanbanCard                                                            */
/* ------------------------------------------------------------------ */

function KanbanCard({
  card,
  onClick,
}: {
  card: TaskCard;
  onClick: () => void;
}) {
  return (
    <Card
      className={cn(
        "cursor-pointer border-l-2 hover:bg-accent transition-colors select-none",
        "hover:-translate-y-px",
        columnBorderClass(card.column),
      )}
      // [MUST] 읽기 전용: drag 없음 — onClick만 처리
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
      aria-label={`태스크 ${card.task_id} 상세 보기`}
    >
      <CardHeader className="p-3 pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-[10px] font-mono text-muted-foreground leading-none mb-1">
              {card.task_id}
            </p>
            <p className="text-sm font-medium leading-tight line-clamp-2">{card.title}</p>
          </div>
          {card.column === "blocked" && (
            <AlertCircle className="h-4 w-4 shrink-0 text-status-blocked mt-0.5" />
          )}
        </div>
      </CardHeader>
      <CardContent className="p-3 pt-0 space-y-2">
        {/* 진행률 */}
        <div className="space-y-1">
          <Progress value={card.progress} className="h-1.5" />
          <p className="text-[10px] text-muted-foreground text-right tabular-nums">
            {card.progress}%
          </p>
        </div>

        {/* badge 행 */}
        <div className="flex flex-wrap items-center gap-1">
          {card.skill && (
            <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-5">
              {card.skill}
            </Badge>
          )}
          {card.mode && (
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5">
              {card.mode}
            </Badge>
          )}
          {card.current_stage && (
            <Badge
              variant="outline"
              className={cn(
                "text-[10px] px-1.5 py-0 h-5 ml-auto font-mono",
                card.column === "in_progress"
                  ? "border-status-running text-status-running"
                  : "text-muted-foreground",
              )}
            >
              {card.current_stage}
            </Badge>
          )}
        </div>

        {/* 메타 */}
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>{card.updated_at || "—"}</span>
          {card.artifact_count > 0 && (
            <>
              <FileText className="h-3 w-3 ml-1" />
              <span>{card.artifact_count}</span>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* KanbanColumn                                                          */
/* ------------------------------------------------------------------ */

function KanbanColumnView({
  col,
  cards,
  onCardClick,
}: {
  col: (typeof COLUMNS)[number];
  cards: TaskCard[];
  onCardClick: (card: TaskCard) => void;
}) {
  const Icon = col.icon;

  return (
    <div className="flex flex-col min-w-[220px] flex-1">
      {/* 컬럼 헤더 */}
      <div className="flex items-center gap-2 px-1 pb-3 shrink-0">
        <Icon className={cn("h-4 w-4", col.statusClass)} />
        <span className="text-sm font-medium">{col.label}</span>
        <Badge variant="secondary" className="ml-auto text-xs tabular-nums">
          {cards.length}
        </Badge>
      </div>

      {/* 카드 리스트 */}
      <ScrollArea className="flex-1">
        <div className="space-y-2 pr-1 pb-4">
          {cards.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-8 text-muted-foreground border border-dashed border-border rounded-lg">
              <Inbox className="h-6 w-6 opacity-40" />
              <p className="text-xs">{col.key === "archive" ? "아카이브 없음" : "태스크 없음"}</p>
            </div>
          ) : (
            cards.map((card) => (
              <KanbanCard key={card.task_id} card={card} onClick={() => onCardClick(card)} />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PipelineStepper — 가로 스테퍼                                        */
/* ------------------------------------------------------------------ */

function PipelineStepper({ pipeline }: { pipeline: PipelineStageGroup[] }) {
  if (pipeline.length === 0) {
    return <p className="text-sm text-muted-foreground">파이프라인 데이터 없음</p>;
  }

  return (
    <div className="flex flex-wrap gap-2 items-center">
      {pipeline.map((g, idx) => (
        <React.Fragment key={g.stage}>
          <div className="flex flex-col items-center gap-1">
            <div
              className={cn(
                "h-2.5 w-2.5 rounded-full shrink-0",
                stageStatusClass(g.status),
              )}
            />
            <span className="text-[10px] font-mono text-center leading-tight max-w-[56px] break-words">
              {g.stage}
            </span>
            <span className="text-[9px] text-muted-foreground tabular-nums">
              {g.done_count}/{g.total}
            </span>
          </div>
          {idx < pipeline.length - 1 && (
            <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0 mb-4" />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* ArtifactViewer — 산출물 탭 마크다운                                  */
/* ------------------------------------------------------------------ */

function ArtifactContent({
  taskId,
  project,
  artifactName,
}: {
  taskId: string;
  project: string;
  artifactName: string;
}) {
  // query param 방식 — path segment에 절대경로 사용 시 FastAPI 매칭 실패 근본 수정
  const { data, isLoading } = useQuery<{ content: string }>({
    queryKey: ["artifact", project, taskId, artifactName],
    queryFn: () =>
      apiClient<{ content: string }>(
        `/api/tasks/artifact?project=${encodeURIComponent(project)}&task_id=${encodeURIComponent(taskId)}&name=${encodeURIComponent(artifactName)}`,
      ),
    retry: 1,
  });

  if (isLoading) {
    return (
      <div className="space-y-3 p-4">
        {[...Array(10)].map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
    );
  }

  if (!data?.content) {
    return <p className="text-sm text-muted-foreground p-4">산출물을 불러올 수 없습니다</p>;
  }

  return (
    <div className="p-4">
      <MarkdownView content={data.content} />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* TaskDrawer                                                            */
/* ------------------------------------------------------------------ */

function TaskDrawer({
  open,
  onClose,
  card,
  project,
}: {
  open: boolean;
  onClose: () => void;
  card: TaskCard | null;
  project: string;
}) {
  // query param 방식 — path segment에 절대경로 사용 시 FastAPI 매칭 실패 근본 수정
  const { data: detail, isLoading } = useQuery<TaskDetail>({
    queryKey: ["task-detail", project, card?.task_id],
    queryFn: () =>
      apiClient<TaskDetail>(
        `/api/tasks/detail?project=${encodeURIComponent(project)}&task_id=${encodeURIComponent(card!.task_id)}`,
      ),
    enabled: open && !!card,
    retry: 1,
  });

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent
        side="right"
        className="w-[min(50vw,800px)] sm:max-w-[min(50vw,800px)] p-0 flex flex-col h-full overflow-hidden"
      >
        {/* 고정 헤더 */}
        <SheetHeader className="border-b px-6 py-4 shrink-0">
          <SheetTitle className="text-sm font-semibold leading-tight">
            {card?.task_id} — {card?.title}
          </SheetTitle>
          <SheetDescription className="flex items-center gap-2 mt-1">
            {card?.skill && (
              <Badge variant="outline" className="text-[10px]">{card.skill}</Badge>
            )}
            {card?.mode && (
              <Badge variant="secondary" className="text-[10px]">{card.mode}</Badge>
            )}
          </SheetDescription>
        </SheetHeader>

        {/* 본문 — flex-1 + min-h-0 로 스크롤 컨테이너 구성 */}
        <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
          {isLoading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          ) : detail ? (
            <>
              {/* 파이프라인 스테퍼 — 고정 */}
              <div className="px-6 py-4 border-b shrink-0">
                <p className="text-xs font-medium text-muted-foreground mb-3">파이프라인 단계</p>
                <PipelineStepper pipeline={detail.pipeline} />
              </div>

              {/* 산출물 탭 — flex-1 + 내부 스크롤 */}
              {detail.artifacts.length > 0 ? (
                <Tabs defaultValue={detail.artifacts[0]} className="flex flex-1 flex-col min-h-0 overflow-hidden px-6 pt-4">
                  <TabsList className="shrink-0 w-fit">
                    {detail.artifacts.map((art) => (
                      <TabsTrigger key={art} value={art} className="text-xs font-mono">
                        {art}
                      </TabsTrigger>
                    ))}
                  </TabsList>
                  {detail.artifacts.map((art) => (
                    <TabsContent
                      key={art}
                      value={art}
                      className="flex-1 min-h-0 overflow-y-auto mt-3 border rounded-md"
                    >
                      <ArtifactContent
                        taskId={detail.task_id}
                        project={project}
                        artifactName={art}
                      />
                    </TabsContent>
                  ))}
                </Tabs>
              ) : (
                <div className="px-6 py-4">
                  <p className="text-sm text-muted-foreground">산출물 없음</p>
                </div>
              )}
            </>
          ) : (
            <div className="p-6">
              <p className="text-sm text-muted-foreground">상세 정보를 불러올 수 없습니다</p>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

/* ------------------------------------------------------------------ */
/* ProjectSelectGrid — 프로젝트 미선택 시 선택 그리드                    */
/* ------------------------------------------------------------------ */

interface ProjectInfo {
  name: string;
  path: string;
  is_opal: boolean;
}

function ProjectSelectGrid({ onSelect }: { onSelect: (path: string) => void }) {
  const { data: projects } = useQuery<ProjectInfo[]>({
    queryKey: ["projects"],
    queryFn: () => apiClient<ProjectInfo[]>("/api/projects"),
    retry: 1,
  });

  const opalProjects = (projects ?? []).filter((p) => p.is_opal);

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 p-6">
      <div className="text-center">
        <Inbox className="h-10 w-10 text-muted-foreground mx-auto mb-3 opacity-40" />
        <p className="text-sm font-medium">프로젝트를 선택하세요</p>
        <p className="text-xs text-muted-foreground mt-1">
          칸반 보드는 단일 프로젝트 컨텍스트로 동작합니다
        </p>
      </div>
      {opalProjects.length > 0 && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 w-full max-w-lg">
          {opalProjects.map((p) => (
            <button
              key={p.path}
              className="flex flex-col items-start gap-1 rounded-lg border border-border p-3 text-left hover:bg-accent transition-colors"
              onClick={() => onSelect(p.path)}
            >
              <span className="text-sm font-medium truncate w-full">{p.name}</span>
              <Badge
                variant="default"
                className="text-[10px] bg-status-done/20 text-status-done border-status-done/30"
              >
                OPAL
              </Badge>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* TasksPage — 루트 컴포넌트                                             */
/* ------------------------------------------------------------------ */

export function TasksPage() {
  // contextProject(ui-store)를 단일 소스로 구독 — 스위처 연동. searchParams는 딥링크용 보조.
  const [searchParams, setSearchParams] = useSearchParams();
  const { contextProject, setContextProject } = useUiStore();
  // 선택 우선순위: contextProject > searchParams?project (딥링크 진입 시 초기 동기)
  const projectParam = contextProject ?? searchParams.get("project");
  const [selectedCard, setSelectedCard] = useState<TaskCard | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const { data: tasks, isLoading, isError } = useQuery<TaskCard[]>({
    queryKey: ["tasks", projectParam],
    queryFn: () =>
      apiClient<TaskCard[]>(
        projectParam
          ? `/api/tasks?project=${encodeURIComponent(projectParam)}`
          : "/api/tasks",
      ),
    enabled: !!projectParam,
    retry: 1,
  });

  const handleCardClick = (card: TaskCard) => {
    setSelectedCard(card);
    setDrawerOpen(true);
  };

  const handleProjectSelect = (path: string) => {
    // contextProject 전역 동기 → 프로젝트 화면 등도 따라가게
    setContextProject(path);
    setSearchParams({ project: path });
  };

  // 컬럼별 카드 그룹핑 (BE가 정렬해서 반환하므로 FE는 그룹핑만 수행)
  const grouped = COLUMNS.reduce(
    (acc, col) => {
      acc[col.key] = (tasks ?? []).filter((t) => t.column === col.key);
      return acc;
    },
    {} as Record<KanbanColumn, TaskCard[]>,
  );

  if (!projectParam) {
    return <ProjectSelectGrid onSelect={handleProjectSelect} />;
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* 헤더 */}
      <div className="flex items-center gap-3 border-b px-6 py-3 shrink-0">
        <h1 className="text-sm font-semibold">태스크 칸반</h1>
        <span className="text-xs text-muted-foreground font-medium truncate max-w-[240px]">
          {projectParam.split("/").filter(Boolean).pop()}
        </span>
        {/* [MUST] 읽기 전용 badge — 상시 표시 (S-8, C-2/C-6, WIREFRAME §4.4) */}
        <Badge
          variant="secondary"
          className="ml-auto flex items-center gap-1 shrink-0 text-xs text-muted-foreground"
        >
          <Lock className="h-3 w-3" />
          읽기 전용
        </Badge>
      </div>

      {/* 에러 */}
      {isError && (
        <div className="px-6 pt-4">
          <div className="flex items-center gap-2 rounded-md border border-status-blocked/30 bg-status-blocked/5 px-4 py-3">
            <AlertTriangle className="h-4 w-4 text-status-blocked shrink-0" />
            <p className="text-sm">API 연결 실패. opal-cli console start를 실행하세요.</p>
          </div>
        </div>
      )}

      {/* 칸반 보드 */}
      {isLoading ? (
        <div className="flex gap-4 p-6 overflow-x-auto">
          {COLUMNS.map((col) => (
            <div key={col.key} className="flex flex-col min-w-[220px] flex-1 space-y-2">
              <Skeleton className="h-6 w-24" />
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-28 w-full" />
              ))}
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-1 gap-4 p-6 overflow-x-auto overflow-y-hidden">
          {COLUMNS.map((col) => (
            <React.Fragment key={col.key}>
              <KanbanColumnView
                col={col}
                cards={grouped[col.key]}
                onCardClick={handleCardClick}
              />
              {col.key !== "archive" && <Separator orientation="vertical" className="h-full" />}
            </React.Fragment>
          ))}
        </div>
      )}

      {/* 상세 Sheet (right 사이드 패널) */}
      <TaskDrawer
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedCard(null);
        }}
        card={selectedCard}
        project={projectParam}
      />
    </div>
  );
}
