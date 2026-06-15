/**
 * @header {
 *   "module": "projects-page",
 *   "layer": "page",
 *   "domain": "projects",
 *   "description": "프로젝트 화면 — 목록(OPAL badge·검색) + resizable 우측 상세(개요/PM프로필/문서 3탭). 개요=project_md MarkdownView, PM프로필=agent_md MarkdownView, 문서=docs/ 실제 스캔 목록+클릭→Sheet(right 사이드 패널) MarkdownView+스크롤. 스택 탭 제거. 색 토큰 경유(C-12). selectedPath=contextProject(ui-store) 전역 구독 — 스위처 연동. searchParams는 딥링크용 보조 동기.",
 *   "exports": ["ProjectsPage"],
 *   "depends": ["api-client", "markdown-view", "card", "badge", "tabs", "resizable", "sheet", "scroll-area", "avatar", "skeleton", "ui-store"]
 * }
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { useUiStore } from "@/store/ui-store";
import {
  FolderOpen,
  CheckCircle2,
  XCircle,
  FileText,
  ChevronRight,
  Search,
  BookOpen,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { MarkdownView } from "@/components/markdown-view";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ResizableHandle,
  ResizablePanelGroup,
  ResizablePanel,
} from "@/components/ui/resizable";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/* 타입                                                                  */
/* ------------------------------------------------------------------ */

interface ProjectInfo {
  name: string;
  path: string;
  is_opal: boolean;
  task_count: number;
  last_updated: string | null;
}

interface DocItem {
  title: string;
  path: string;
}

interface ProjectDetail {
  name: string;
  path: string;
  is_opal: boolean;
  pm_profile: Record<string, unknown>;
  agent_md: string;
  project_md: string;
  tech_stack: string[];
  docs: DocItem[];
  warning: string | null;
}

/* ------------------------------------------------------------------ */
/* ProjectListItem                                                       */
/* ------------------------------------------------------------------ */

function ProjectListItem({
  project,
  isSelected,
  onClick,
}: {
  project: ProjectInfo;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={cn(
        "w-full flex items-start gap-3 rounded-md px-3 py-3 text-left transition-colors hover:bg-accent",
        isSelected && "bg-accent",
        !project.is_opal && "opacity-60",
      )}
      onClick={onClick}
    >
      <div className="mt-0.5">
        {project.is_opal ? (
          <CheckCircle2 className="h-4 w-4 text-status-done shrink-0" />
        ) : (
          <XCircle className="h-4 w-4 text-muted-foreground shrink-0" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium truncate">{project.name}</span>
          <Badge
            variant={project.is_opal ? "default" : "secondary"}
            className={cn(
              "shrink-0 text-[10px] px-1.5 py-0",
              project.is_opal
                ? "bg-status-done/20 text-status-done border-status-done/30"
                : "text-muted-foreground",
            )}
          >
            {project.is_opal ? "OPAL" : "미적용"}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground font-mono truncate mt-0.5">
          {project.path}
        </p>
        {project.is_opal && (
          <p className="text-xs text-muted-foreground mt-0.5">
            태스크 {project.task_count}개
            {project.last_updated && (
              <span className="ml-2 opacity-70">갱신 {project.last_updated}</span>
            )}
          </p>
        )}
      </div>
      <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground mt-1" />
    </button>
  );
}

/* PmProfileView 제거됨 — agent_md 원문을 MarkdownView로 직접 렌더 (Task 021) */

/* ------------------------------------------------------------------ */
/* ProjectDetailPanel                                                    */
/* ------------------------------------------------------------------ */

function ProjectDetailPanel({
  projectId,
  onDocClick,
}: {
  projectId: string;
  onDocClick: (doc: DocItem) => void;
}) {
  // query param 방식 — path segment에 절대경로 사용 시 FastAPI 매칭 실패 근본 수정
  const { data, isLoading } = useQuery<ProjectDetail>({
    queryKey: ["project-detail", projectId],
    queryFn: () =>
      apiClient<ProjectDetail>(
        `/api/projects/detail?path=${encodeURIComponent(projectId)}`,
      ),
    enabled: !!projectId,
    retry: 1,
  });

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-64" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <p className="text-sm text-muted-foreground">프로젝트를 선택하세요</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* 헤더 */}
      <div className="flex items-center gap-3 border-b px-6 py-4 shrink-0">
        <Avatar className="h-9 w-9">
          <AvatarFallback className="bg-primary text-primary-foreground text-sm font-bold">
            {data.name[0]?.toUpperCase() ?? "P"}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold truncate">{data.name}</h2>
            <Badge
              variant={data.is_opal ? "default" : "secondary"}
              className={cn(
                "text-[10px]",
                data.is_opal && "bg-status-done/20 text-status-done border-status-done/30",
              )}
            >
              {data.is_opal ? "OPAL" : "미적용"}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground font-mono truncate">{data.path}</p>
        </div>
      </div>

      {/* 탭 — 3개: 개요/PM프로필/문서 (스택 탭 제거 — Task 021) */}
      <Tabs defaultValue="overview" className="flex flex-1 flex-col overflow-hidden">
        <TabsList className="mx-6 mt-4 shrink-0 w-fit">
          <TabsTrigger value="overview" className="text-xs">개요</TabsTrigger>
          <TabsTrigger value="pm" className="text-xs">PM 프로필</TabsTrigger>
          <TabsTrigger value="docs" className="text-xs">문서</TabsTrigger>
        </TabsList>

        <ScrollArea className="flex-1 px-6 py-4">
          {/* 개요 탭 — project_md 원문을 MarkdownView로 렌더 */}
          <TabsContent value="overview" className="mt-0">
            {data.project_md ? (
              <MarkdownView content={data.project_md} />
            ) : (
              <p className="text-sm text-muted-foreground">PROJECT.md 없음</p>
            )}
          </TabsContent>

          {/* PM 프로필 탭 — agent_md 원문을 MarkdownView로 렌더 (구조화 추출 폐기) */}
          <TabsContent value="pm" className="mt-0">
            {data.agent_md ? (
              <MarkdownView content={data.agent_md} />
            ) : (
              <p className="text-sm text-muted-foreground">AGENT.md 없음</p>
            )}
          </TabsContent>

          {/* 문서 탭 — docs/ 실제 스캔 목록 + 클릭 시 Drawer */}
          <TabsContent value="docs" className="mt-0 space-y-1">
            {data.docs.length === 0 ? (
              <p className="text-sm text-muted-foreground">docs/ 폴더에 문서 없음</p>
            ) : (
              data.docs.map((doc) => (
                <button
                  key={doc.path}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left hover:bg-accent transition-colors"
                  onClick={() => onDocClick(doc)}
                >
                  <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <span className="text-sm">{doc.title}</span>
                  <ChevronRight className="ml-auto h-4 w-4 text-muted-foreground" />
                </button>
              ))
            )}
          </TabsContent>
        </ScrollArea>
      </Tabs>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* MarkdownDrawer                                                        */
/* ------------------------------------------------------------------ */

function MarkdownDrawer({
  open,
  onClose,
  title,
  projectId,
  docName,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  projectId: string;
  docName: string;
}) {
  // query param 방식 — path segment에 절대경로 사용 시 FastAPI 매칭 실패 근본 수정
  const { data, isLoading } = useQuery<{ content: string }>({
    queryKey: ["project-doc", projectId, docName],
    queryFn: () =>
      apiClient<{ content: string }>(
        `/api/projects/doc?path=${encodeURIComponent(projectId)}&name=${encodeURIComponent(docName)}`,
      ),
    enabled: open && !!projectId && !!docName,
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
          <SheetTitle className="flex items-center gap-2 text-sm font-semibold">
            <BookOpen className="h-4 w-4" />
            {title}
          </SheetTitle>
        </SheetHeader>
        {/* 본문 — flex-1 + overflow-y-auto 로 세로 스크롤 확보 */}
        <div className="flex-1 min-h-0 overflow-y-auto px-6 py-4">
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(8)].map((_, i) => (
                <Skeleton key={i} className="h-4 w-full" />
              ))}
            </div>
          ) : data?.content ? (
            <MarkdownView content={data.content} />
          ) : (
            <p className="text-sm text-muted-foreground">문서를 불러올 수 없습니다</p>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

/* ------------------------------------------------------------------ */
/* ProjectsPage — 루트 컴포넌트                                          */
/* ------------------------------------------------------------------ */

export function ProjectsPage() {
  // contextProject(ui-store)를 단일 소스로 구독 — 스위처 연동. searchParams는 딥링크용 보조.
  const [searchParams, setSearchParams] = useSearchParams();
  const { contextProject, setContextProject } = useUiStore();
  const [search, setSearch] = useState("");
  const [drawerDoc, setDrawerDoc] = useState<{ doc: DocItem; projectId: string } | null>(null);

  // 선택 우선순위: contextProject > searchParams?project (딥링크 진입 시 초기 동기)
  const selectedPath = contextProject ?? searchParams.get("project");

  const { data: projects, isLoading } = useQuery<ProjectInfo[]>({
    queryKey: ["projects"],
    queryFn: () => apiClient<ProjectInfo[]>("/api/projects"),
    retry: 1,
  });

  // OPAL 적용 프로젝트만 리스트업 (미적용 제외 — 캡틴 결정 2026-06-15)
  const filtered = (projects ?? []).filter(
    (p) =>
      p.is_opal &&
      (p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.path.toLowerCase().includes(search.toLowerCase())),
  );

  const opalCount = (projects ?? []).filter((p) => p.is_opal).length;

  const handleSelect = (path: string) => {
    // contextProject 전역 동기 → 다른 화면(태스크 등)도 따라가게
    setContextProject(path);
    // searchParams도 동기 — 딥링크/새로고침 보조
    setSearchParams({ project: path });
  };

  return (
    <div className="flex flex-1 overflow-hidden" style={{ height: "calc(100vh - 3rem)" }}>
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* 좌: 목록 */}
        <ResizablePanel defaultSize={35} minSize={25} maxSize={50}>
          <div className="flex h-full flex-col border-r">
            {/* 검색/헤더 */}
            <div className="border-b px-4 py-4 space-y-3 shrink-0">
              <div className="flex items-center justify-between">
                <h1 className="text-sm font-semibold">OPAL 프로젝트</h1>
                <Badge variant="secondary" className="text-xs">
                  {opalCount}개
                </Badge>
              </div>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                <Input
                  className="pl-8 h-8 text-xs"
                  placeholder="프로젝트 검색..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>

            {/* 프로젝트 목록 */}
            <ScrollArea className="flex-1">
              <div className="p-2 space-y-0.5">
                {isLoading ? (
                  [...Array(5)].map((_, i) => (
                    <div key={i} className="px-3 py-3 space-y-2">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-3 w-48" />
                    </div>
                  ))
                ) : filtered.length === 0 ? (
                  <div className="flex flex-col items-center gap-2 py-12 text-muted-foreground">
                    <FolderOpen className="h-8 w-8 opacity-40" />
                    <p className="text-sm">프로젝트 없음</p>
                  </div>
                ) : (
                  filtered.map((p) => (
                    <ProjectListItem
                      key={p.path}
                      project={p}
                      isSelected={selectedPath === p.path}
                      onClick={() => handleSelect(p.path)}
                    />
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        </ResizablePanel>

        <ResizableHandle />

        {/* 우: 상세 */}
        <ResizablePanel defaultSize={65}>
          {selectedPath ? (
            <ProjectDetailPanel
              projectId={selectedPath}
              onDocClick={(doc) => setDrawerDoc({ doc, projectId: selectedPath })}
            />
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-muted-foreground">
              <FolderOpen className="h-12 w-12 opacity-30" />
              <p className="text-sm">좌측에서 프로젝트를 선택하세요</p>
            </div>
          )}
        </ResizablePanel>
      </ResizablePanelGroup>

      {/* 마크다운 Drawer */}
      {drawerDoc && (
        <MarkdownDrawer
          open={!!drawerDoc}
          onClose={() => setDrawerDoc(null)}
          title={drawerDoc.doc.title}
          projectId={drawerDoc.projectId}
          docName={drawerDoc.doc.title}
        />
      )}
    </div>
  );
}
