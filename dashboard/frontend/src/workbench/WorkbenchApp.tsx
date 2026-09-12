/**
 * @header {
 *   "module": "workbench-app",
 *   "layer": "component",
 *   "domain": "workbench",
 *   "description": "SCR-001~003·005~008을 한 데스크톱 shell에서 연결하는 순수 동적 Surface 탭 + split 인터랙티브 목업. 좌측 사이드바는 필터 없이 재귀 Project→진행 TASK→실행 Agent 트리를 표시하고, PROJECTS +는 TASK 추가를 연다. Project 생성/연결은 설정 > 프로젝트에서 처리하며, 중앙 Execution Workspace는 TASK별 PM Coordination Room·Sub PM Workspace·Worker Terminal·독립 Terminal을 구분한다 (wireframe.md v9.0)",
 *   "exports": ["WorkbenchApp"],
 *   "depends": ["mock-workbench-adapter", "shadcn-ui"]
 * }
 */

import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import type { ImperativePanelHandle } from "react-resizable-panels";
import {
  Bot, Boxes, ChevronDown, ChevronRight, CircleDot, FileCode2, FileText, Folder, FolderPlus, Globe2, Loader2, MessageSquarePlus,
  PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, Plus, Settings as SettingsIcon,
  Smartphone, Terminal as TerminalIcon, Trash2, X,
} from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { collectLeaves, isDescendantProject, MockWorkbenchAdapter } from "./mock-adapter";
import type {
  ChangeEntry, CoordinationEvent, CoordinationEventType, FileNode, FontScale, GitFileStatus, Pilot, Project, RuntimeBinding, SessionStatus, Settings, SplitDirection, SplitNode, SurfaceKind, SurfaceTab, Task, TaskStatus, ThemeMode, WorkbenchState,
} from "./types";

const adapter = new MockWorkbenchAdapter();

const statusLabels: Record<TaskStatus, string> = { todo: "Todo", in_progress: "In progress", review: "Review", done: "Done" };
const pilots: Pilot[] = ["opp", "opd", "opds", "opdw", "oppl", "opsdd"];

const surfaceMenuItems: { kind: SurfaceKind; label: string }[] = [
  { kind: "coordination", label: "PM Coordination" },
  { kind: "terminal", label: "독립 Terminal" },
  { kind: "browser", label: "Browser" },
  { kind: "markdown", label: "Markdown" },
  { kind: "mobile_emulator", label: "모바일 에뮬레이터" },
];

const surfaceIcon: Record<SurfaceKind, React.ReactElement> = {
  coordination: <Boxes className="size-3.5" />,
  terminal: <TerminalIcon className="size-3.5" />,
  browser: <Globe2 className="size-3.5" />,
  markdown: <FileCode2 className="size-3.5" />,
  mobile_emulator: <Smartphone className="size-3.5" />,
  agent_cli: <Bot className="size-3.5" />,
  diff: <FileCode2 className="size-3.5" />,
};

function BoundaryBadge({ type }: { type: "actual" | "simulated" | "not_connected" }) {
  return <Badge variant={type === "actual" ? "default" : "outline"}>{type === "actual" ? "Actual" : type === "simulated" ? "Simulated" : "Not connected"}</Badge>;
}

/** AC-16: 탭 라벨 좌측 아이콘 슬롯에 idle(표시 없음)/running(스피너)/completed(초록 점)/failed(destructive 배지)를 표시한다. */
function SurfaceTabStatusIndicator({ status, failureSummary }: { status: SessionStatus; failureSummary?: string }) {
  if (status === "idle") return null;
  if (status === "running") return <Loader2 className="size-3 animate-spin text-muted-foreground" aria-label="진행 중" />;
  if (status === "completed") return <span className="inline-block size-2 rounded-full bg-emerald-500" aria-label="완료" />;
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-flex size-3 items-center justify-center rounded-full bg-destructive text-[8px] font-bold text-destructive-foreground" aria-label="실패">!</span>
      </TooltipTrigger>
      <TooltipContent>{failureSummary ?? "세션이 실패했습니다."}</TooltipContent>
    </Tooltip>
  );
}

function computeEdge(event: React.DragEvent, rect: DOMRect): { direction: SplitDirection; edge: "start" | "end" } | "center" {
  const x = (event.clientX - rect.left) / rect.width;
  const y = (event.clientY - rect.top) / rect.height;
  if (x < 0.25) return { direction: "horizontal", edge: "start" };
  if (x > 0.75) return { direction: "horizontal", edge: "end" };
  if (y < 0.25) return { direction: "vertical", edge: "start" };
  if (y > 0.75) return { direction: "vertical", edge: "end" };
  return "center";
}

/**
 * W-2 (R-12): Task 생성 Dialog. 좌측 사이드바 TASKS 헤더 `+`(보드를 거치지 않는 직행 경로)와
 * Kanban 보드 내부 진입점이 이 컴포넌트를 공유한다.
 */
function NewTaskDialog({ state, commit, open, onOpenChange }: {
  state: WorkbenchState; commit: (next: WorkbenchState) => void; open: boolean; onOpenChange: (open: boolean) => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [pilot, setPilot] = useState<Pilot>("opd");
  const [leadAgentId, setLeadAgentId] = useState(state.projects.find((project) => project.id === state.activeProjectId)?.pmAgentId ?? state.agents[0]?.id ?? "");
  const [error, setError] = useState("");

  const submit = () => {
    if (!title.trim() || !description.trim()) { setError("제목과 설명을 모두 입력하세요."); return; }
    let next = adapter.createTask(state, title.trim(), description.trim(), pilot, leadAgentId);
    // R-8: 새 Task 진입 시 Settings 기본값을 적용한다(이미 저장된 PersistedUI의 현재 접힘 상태는 덮어쓰지 않음 — 이 시점은 신규 생성이라 해당 없음).
    next = { ...next, sidebarCollapsed: next.settings.sidebarCollapsedDefault, railCollapsed: next.settings.railCollapsedDefault };
    commit(next);
    onOpenChange(false); setTitle(""); setDescription(""); setError("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>새 Task</DialogTitle><DialogDescription>현재 Project에 검토용 Task를 만듭니다.</DialogDescription></DialogHeader>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2"><Label htmlFor="task-title">제목 *</Label><Input id="task-title" value={title} onChange={(e) => setTitle(e.target.value)} aria-invalid={Boolean(error)} /></div>
          <div className="flex flex-col gap-2"><Label htmlFor="task-description">설명 *</Label><Textarea id="task-description" value={description} onChange={(e) => setDescription(e.target.value)} aria-invalid={Boolean(error)} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2"><Label htmlFor="task-pilot">Pilot *</Label><select id="task-pilot" value={pilot} onChange={(event) => setPilot(event.target.value as Pilot)} className="h-10 rounded-md border border-input bg-background px-3 text-sm">{pilots.map((item) => <option key={item} value={item}>{item}</option>)}</select></div>
            <div className="flex flex-col gap-2"><Label>담당 Agent *</Label><Select value={leadAgentId} onValueChange={setLeadAgentId}><SelectTrigger aria-label="담당 Agent"><SelectValue /></SelectTrigger><SelectContent><SelectGroup>{state.agents.map((agent) => <SelectItem key={agent.id} value={agent.id}>{agent.name}</SelectItem>)}</SelectGroup></SelectContent></Select></div>
          </div>
          {error && <Alert variant="destructive"><AlertTitle>입력을 확인하세요</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>}
        </div>
        <DialogFooter><Button variant="outline" onClick={() => onOpenChange(false)}>취소</Button><Button onClick={submit}>Task 만들기</Button></DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function TaskBoard({ state, commit, onClose }: { state: WorkbenchState; commit: (next: WorkbenchState) => void; onClose: () => void }) {
  const [open, setOpen] = useState(false);
  const statuses: TaskStatus[] = ["todo", "in_progress", "review", "done"];
  const projectTasks = state.tasks.filter((task) => task.projectId === state.activeProjectId);

  return (
    <div className="absolute inset-0 z-30 flex flex-col gap-4 bg-background p-5" data-testid="task-board">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">{state.projects.find((p) => p.id === state.activeProjectId)?.name} / Tasks</h2>
          <p className="text-sm text-muted-foreground">카드의 상태 Select로 Kanban 열을 이동합니다.</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setOpen(true)}><Plus data-icon="inline-start" />New Task</Button>
          <Button variant="outline" onClick={onClose}>Workbench로 돌아가기</Button>
        </div>
      </div>
      <div className="grid min-h-0 flex-1 grid-cols-4 gap-3">
        {statuses.map((status) => (
          <section key={status} className="flex min-w-0 flex-col gap-2 rounded-lg border bg-muted/30 p-3">
            <div className="flex items-center justify-between text-xs font-semibold uppercase">
              <span>{statusLabels[status]}</span>
              <Badge variant="secondary">{projectTasks.filter((task) => task.status === status).length}</Badge>
            </div>
            <ScrollArea className="min-h-0 flex-1">
              <div className="flex flex-col gap-2 pr-2">
                {projectTasks.filter((task) => task.status === status).map((task) => (
                  <Card key={task.id}>
                    <CardHeader className="p-3">
                      <CardTitle className="text-sm">{task.title}</CardTitle>
                      <CardDescription>{task.description}</CardDescription>
                    </CardHeader>
                    <CardFooter className="flex gap-1 p-3 pt-0">
                      <Button size="sm" variant="ghost" onClick={() => { commit(adapter.selectTask(state, task.id)); onClose(); }}>열기</Button>
                      <Select value={task.status} onValueChange={(value) => commit(adapter.moveTask(state, task.id, value as TaskStatus))}>
                        <SelectTrigger aria-label={`${task.title} 상태`} className="h-9"><SelectValue /></SelectTrigger>
                        <SelectContent><SelectGroup>{statuses.map((value) => <SelectItem key={value} value={value}>{statusLabels[value]}</SelectItem>)}</SelectGroup></SelectContent>
                      </Select>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </section>
        ))}
      </div>
      <NewTaskDialog state={state} commit={commit} open={open} onOpenChange={setOpen} />
    </div>
  );
}

/** v6.0(§4.6a·§5): TASK 행의 참여 Project 칩. 조율 TASK는 참여 Project 여러 개를 함께 표시한다(AW-AC-6·7). */
function TaskParticipantChip({ project }: { project: Project | undefined }) {
  if (!project) return null;
  return <Badge variant="outline" className="rounded-none px-1 text-[10px] font-semibold">{project.name.toUpperCase()}</Badge>;
}

const coordinationEventLabel: Record<CoordinationEventType, string> = {
  instruction: "지시", invitation: "초대", assignment: "배정", status: "상태", coordination: "조율", blocker: "블로커", decision: "결정", result: "결과", worker_spawn: "Worker",
};

/** v8.0(§4.6a): Project 트리 한 행 — 셰브론(자식 있을 때만)·이름·PM 배지·진행 TASK 수 배지·블로커 점. Project 생성/연결은 설정 > 프로젝트로 일원화한다. */
function ProjectTreeRow({ project, depth, hasChildren, expanded, pmName, activeTaskCount, hasBlocker, isActive, onSelect, onToggle }: {
  project: Project; depth: number; hasChildren: boolean; expanded: boolean; pmName: string; activeTaskCount: number; hasBlocker: boolean; isActive: boolean;
  onSelect: () => void; onToggle: () => void;
}) {
  return (
    <div
      className={`group flex items-center gap-1 rounded px-1 py-1 text-xs hover:bg-accent ${isActive ? "bg-accent font-medium" : ""}`}
      style={{ paddingLeft: depth * 14 }}
      role="treeitem"
      aria-expanded={hasChildren ? expanded : undefined}
    >
      {hasChildren ? (
        <button aria-label={`${project.name} ${expanded ? "접기" : "펼치기"}`} onClick={onToggle} className="shrink-0">
          {expanded ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
        </button>
      ) : (
        <span className="inline-block size-3.5 shrink-0" />
      )}
      <button className="flex min-w-0 flex-1 items-center gap-1 truncate text-left" onClick={onSelect}>
        <span className="truncate">{project.name}</span>
      </button>
      <Badge variant="secondary" className="shrink-0 text-[10px]">PM:{pmName}</Badge>
      <Badge variant="outline" className="shrink-0 text-[10px]">{activeTaskCount}</Badge>
      <span className={`inline-block size-1.5 shrink-0 rounded-full ${hasBlocker ? "bg-destructive" : "bg-transparent"}`} aria-label={hasBlocker ? "블로커 있음" : "블로커 없음"} />
    </div>
  );
}

/** v8.0(§2.1·§4.6a·§5): ProjectSelector·TaskGroup·필터 UI를 폐기하고 Project→진행 TASK→실행 Agent를 한 재귀 트리에서 렌더한다(AW-AC-3·14·15). */
function ProjectTree({ state, depth = 0, parentId, onSelect, onSelectTask, onToggle }: {
  state: WorkbenchState; depth?: number; parentId?: string;
  onSelect: (projectId: string) => void; onSelectTask: (task: Task, agentId?: string) => void; onToggle: (projectId: string) => void;
}) {
  const children = state.projects.filter((project) => project.parentProjectId === parentId);
  return (
    <div role="tree" data-testid={depth === 0 ? "project-tree" : undefined} className="flex flex-col gap-0.5">
      {children.map((project) => {
        const projectTasks = state.tasks.filter((task) => task.ownerProjectId === project.id && task.status !== "done");
        const hasProjectChildren = state.projects.some((p) => p.parentProjectId === project.id);
        const hasChildren = hasProjectChildren || projectTasks.length > 0;
        const expanded = state.expandedProjectIds.includes(project.id);
        const pm = state.agents.find((agent) => agent.id === project.pmAgentId);
        const activeTaskCount = state.tasks.filter((task) => task.ownerProjectId === project.id && task.status !== "done").length;
        const hasBlocker = state.coordinationEvents.some((event) => event.projectId === project.id && event.type === "blocker");
        return (
          <div key={project.id} className="flex flex-col">
            <ProjectTreeRow
              project={project}
              depth={depth}
              hasChildren={hasChildren}
              expanded={expanded}
              pmName={pm?.name ?? project.pmAgentId}
              activeTaskCount={activeTaskCount}
              hasBlocker={hasBlocker}
              isActive={project.id === state.activeProjectId}
              onSelect={() => onSelect(project.id)}
              onToggle={() => onToggle(project.id)}
            />
            {expanded && hasProjectChildren && <ProjectTree state={state} depth={depth + 1} parentId={project.id} onSelect={onSelect} onSelectTask={onSelectTask} onToggle={onToggle} />}
            {expanded && projectTasks.map((task) => {
              const executionAgentIds = Array.from(new Set([
                task.leadAgentId,
                ...state.surfaceTabs.filter((tab) => tab.taskId === task.id && tab.kind === "agent_cli" && tab.agentId).map((tab) => tab.agentId as string),
              ]));
              return <div key={task.id} className="flex flex-col" style={{ paddingLeft: (depth + 1) * 14 }}>
                <button role="treeitem" aria-label={`TASK ${task.title}`} className={`flex items-center gap-1 rounded px-1 py-1 text-left text-xs hover:bg-accent ${state.taskId === task.id ? "bg-accent" : ""}`} onClick={() => onSelectTask(task)}><CircleDot className="size-3" /><span className="min-w-0 flex-1 truncate">{task.title}</span>{task.participantProjectIds.length > 1 && task.participantProjectIds.map((id) => <TaskParticipantChip key={id} project={state.projects.find((item) => item.id === id)} />)}<Badge variant="outline" className="text-[10px]">{task.pilot}</Badge></button>
                {executionAgentIds.map((agentId) => {
                  const agent = state.agents.find((item) => item.id === agentId);
                  return <button key={agentId} role="treeitem" aria-label={`실행 Agent ${agent?.name ?? agentId} · ${task.title}`} className="flex items-center gap-1 rounded px-1 py-1 text-left text-[11px] text-muted-foreground hover:bg-accent" style={{ marginLeft: 14 }} onClick={() => onSelectTask(task, agentId)}><Bot className="size-3" /><span>{agent?.name ?? agentId}</span></button>;
                })}
              </div>;
            })}
          </div>
        );
      })}
    </div>
  );
}

/**
 * v8.0(SCR-007, §4.6): Project 생성/연결 Dialog. 설정 > 프로젝트에서 호출하며 부모 Project를 Dialog 안에서 선택한다.
 * 실제 폴더·Git·`.opal` 생성은 수행하지 않는다(제외 범위).
 */
function NewOrLinkProjectDialog({ state, commit, open, onOpenChange, parentProjectId }: {
  state: WorkbenchState; commit: (next: WorkbenchState) => void; open: boolean; onOpenChange: (open: boolean) => void; parentProjectId?: string;
}) {
  const [tab, setTab] = useState<"new" | "link">("new");
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const [pmAgentId, setPmAgentId] = useState(state.agents[0]?.id ?? "");
  const [linkPath, setLinkPath] = useState("");
  const [error, setError] = useState("");
  const [selectedParentProjectId, setSelectedParentProjectId] = useState(parentProjectId ?? "__top__");
  const parent = state.projects.find((p) => p.id === (selectedParentProjectId === "__top__" ? undefined : selectedParentProjectId));
  const discoveredProject = state.projects.find((project) => project.repositoryPath === linkPath.trim());
  const discoveredPm = state.agents.find((agent) => agent.id === discoveredProject?.pmAgentId) ?? state.agents[0];
  const discoveredRepoCount = discoveredProject?.repositoryComponentIds.length ?? (linkPath.trim() ? 1 : 0);

  const reset = () => { setName(""); setPath(""); setLinkPath(""); setError(""); setSelectedParentProjectId(parentProjectId ?? "__top__"); };
  const parentForSubmit = selectedParentProjectId === "__top__" ? undefined : selectedParentProjectId;

  const submitNew = () => {
    if (!name.trim() || !path.trim()) { setError("이름과 경로를 모두 입력하세요."); return; }
    const next = adapter.createProject(state, name.trim(), path.trim(), pmAgentId, parentForSubmit);
    commit(next);
    onOpenChange(false); reset();
  };

  const submitLink = () => {
    if (!linkPath.trim()) { setError("경로를 입력하세요."); return; }
    const next = adapter.linkProject(state, linkPath.trim(), discoveredPm?.id ?? "opal-pm", parentForSubmit);
    commit(next);
    onOpenChange(false); reset();
  };

  return (
    <Dialog open={open} onOpenChange={(next) => { onOpenChange(next); if (!next) reset(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Project 추가</DialogTitle>
          <DialogDescription>{parent ? `${parent.name} 아래에 추가` : "최상위 Project로 추가"}</DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-2">
          <Label htmlFor="new-project-parent">부모 Project</Label>
          <select
            id="new-project-parent"
            aria-label="부모 Project"
            value={selectedParentProjectId}
            onChange={(event) => setSelectedParentProjectId(event.target.value)}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="__top__">(최상위)</option>
            {state.projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
          </select>
        </div>
        <div className="inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground">
          <button type="button" role="tab" aria-selected={tab === "new"} className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ${tab === "new" ? "bg-background text-foreground shadow-sm" : ""}`} onClick={() => setTab("new")}>신규 생성</button>
          <button type="button" role="tab" aria-selected={tab === "link"} className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ${tab === "link" ? "bg-background text-foreground shadow-sm" : ""}`} onClick={() => setTab("link")}>기존 연결</button>
        </div>
        {tab === "new" ? (
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-2"><Label htmlFor="new-project-name">이름 *</Label><Input id="new-project-name" value={name} onChange={(e) => setName(e.target.value)} /></div>
            <div className="flex flex-col gap-2"><Label htmlFor="new-project-path">경로 *</Label><Input id="new-project-path" value={path} onChange={(e) => setPath(e.target.value)} /></div>
            <div className="flex flex-col gap-2">
              <Label>PM Agent</Label>
              <Select value={pmAgentId} onValueChange={setPmAgentId}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectGroup>{state.agents.map((agent) => <SelectItem key={agent.id} value={agent.id}>{agent.name}</SelectItem>)}</SelectGroup></SelectContent>
              </Select>
            </div>
            <Alert><AlertTitle>목업 경계</AlertTitle><AlertDescription>관리 repo·OPAL 구조 생성은 실제로 수행하지 않고 목업 상태로만 시뮬레이션됩니다.</AlertDescription></Alert>
            {error && <Alert variant="destructive"><AlertTitle>입력을 확인하세요</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>}
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-2"><Label htmlFor="link-project-path">경로 *</Label><Input id="link-project-path" value={linkPath} onChange={(e) => setLinkPath(e.target.value)} placeholder="/Volumes/Data/StoreLinkStudio/blend" /></div>
            <Alert><AlertTitle>발견됨(mock)</AlertTitle><AlertDescription>{linkPath.trim() ? `.opal/AGENT.md → PM ${discoveredPm?.name ?? "OPAL PM"}, Repository Component ${discoveredRepoCount}개` : "경로를 입력하면 PM과 Repository Component 후보를 표시합니다."}</AlertDescription></Alert>
            {error && <Alert variant="destructive"><AlertTitle>입력을 확인하세요</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>}
          </div>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => { onOpenChange(false); reset(); }}>취소</Button>
          {tab === "new" ? <Button onClick={submitNew}>Project 만들기</Button> : <Button onClick={submitLink}>연결하기</Button>}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function EventRow({ event }: { event: CoordinationEvent }) {
  const isMessage = event.type === "instruction" || event.type === "coordination" || event.type === "status";
  if (isMessage) {
    const isUser = event.pmAgentId === "user";
    return (
      <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
        <div className={`max-w-[78%] rounded-lg border px-3 py-2 text-xs ${isUser ? "bg-primary text-primary-foreground" : "bg-muted/40"}`}>
          <p>{event.summary}</p>
          <p className={`mt-1 text-[10px] ${isUser ? "text-primary-foreground/70" : "text-muted-foreground"}`}>{event.timestamp}</p>
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-start gap-2 rounded border bg-background p-2 text-xs">
      <Badge variant="outline" className="shrink-0">{coordinationEventLabel[event.type]}</Badge>
      <div className="min-w-0 flex-1">
        <p className="truncate">{event.summary}</p>
        <p className="text-[10px] text-muted-foreground">{event.timestamp}</p>
      </div>
    </div>
  );
}

/** v9.0(SCR-008, §4.7): TASK별 Main/Sub PM Room. 사용자는 Main PM에게만 지시하며 Sub PM 초대·Workspace 발동은 Main PM 동작으로 시뮬레이션한다. */
function PmCoordinationSurface({ state, task, onSelectProject, onAssign, onInstruction, onInvite }: {
  state: WorkbenchState; task: Task; onSelectProject: (projectId: string) => void;
  onAssign: (projectId: string, title: string, pilot: Pilot) => void;
  onInstruction: (summary: string) => void;
  onInvite: (projectId: string) => void;
}) {
  const [draft, setDraft] = useState("");
  const room = state.coordinationRooms.find((item) => item.taskId === task.id);
  const ownerProject = state.projects.find((project) => project.id === (room?.mainProjectId ?? task.ownerProjectId));
  const ownerPm = state.agents.find((agent) => agent.id === (room?.mainPmAgentId ?? task.leadAgentId));
  const invitedIds = room?.invitedProjectIds ?? task.participantProjectIds.filter((id) => id !== task.ownerProjectId);
  const participants = invitedIds.map((id) => state.projects.find((p) => p.id === id)).filter((p): p is Project => Boolean(p));
  const inviteCandidate = state.projects.find((project) => project.parentProjectId === task.ownerProjectId && !invitedIds.includes(project.id));
  const events = state.coordinationEvents.filter((event) => event.taskId === task.id).slice().sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  const finalResult = [...events].reverse().find((event) => event.type === "decision" || event.type === "status");
  const subResults = events.filter((event) => event.type === "result");
  const subTasks = state.tasks.filter((item) => item.coordinationTaskId === task.id);
  const submitInstruction = () => { if (!draft.trim()) return; onInstruction(draft.trim()); setDraft(""); };
  const assignFirstInvited = () => { if (!draft.trim() || participants.length === 0) return; onAssign(participants[0].id, draft.trim(), "opd"); setDraft(""); };

  return (
    <div className="flex h-full min-h-0 flex-col gap-3 overflow-auto p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold">PM Coordination Room</h3>
          <p className="text-xs text-muted-foreground">{task.title}</p>
          <div className="mt-1 flex flex-wrap items-center gap-1 text-xs">
            <Badge variant="secondary">Owner: {ownerPm?.name ?? ownerProject?.name ?? "Main PM"}</Badge>
            {participants.map((project) => {
              const pm = state.agents.find((agent) => agent.id === project.pmAgentId);
              const hasWorkspace = state.surfaceTabs.some((tab) => tab.taskId === task.id && tab.agentId === project.pmAgentId && tab.title.includes("Workspace"));
              return (
                <button key={project.id} onClick={() => onSelectProject(project.id)} className="rounded border px-2 py-0.5">
                  {pm?.name ?? project.name + " PM"} · Workspace {hasWorkspace ? "running" : "pending"}
                </button>
              );
            })}
          </div>
        </div>
        <Button size="sm" variant="outline" disabled={!inviteCandidate} onClick={() => inviteCandidate && onInvite(inviteCandidate.id)}>
          <MessageSquarePlus className="size-3.5" />PM 초대 요청
        </Button>
      </div>
      <Card className="border-primary/40 bg-primary/5">
        <CardHeader className="p-3"><CardTitle className="text-xs">Main PM 최종 판단</CardTitle></CardHeader>
        <CardContent className="p-3 pt-0 text-sm">{finalResult?.summary ?? "아직 조율 기록이 없습니다."}</CardContent>
      </Card>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-semibold text-muted-foreground">하위 TASK 상태 집계</span>
        {subTasks.length === 0 && <span className="text-muted-foreground">미배정</span>}
        {subTasks.map((sub) => {
          const project = state.projects.find((p) => p.id === sub.ownerProjectId);
          return (
            <span key={sub.id} className="flex items-center gap-1">
              <span className={`inline-block size-1.5 rounded-full ${sub.status === "done" ? "bg-emerald-500" : sub.status === "review" ? "bg-amber-500" : "bg-muted-foreground"}`} />
              {project?.name ?? sub.ownerProjectId}:{statusLabels[sub.status]}
            </span>
          );
        })}
      </div>
      <Separator />
      <ScrollArea className="min-h-0 flex-1">
        <div className="flex flex-col gap-2 pr-2">
          {events.length === 0 && <p className="text-xs text-muted-foreground">아직 조율 기록이 없습니다.</p>}
          {events.map((event) => <EventRow key={event.id} event={event} />)}
        </div>
      </ScrollArea>
      {subResults.length > 0 && (
        <div className="flex flex-col gap-1 text-xs">
          <span className="font-semibold text-muted-foreground">Sub PM 개별 결과</span>
          {subResults.map((event) => <p key={event.id} className="rounded border px-2 py-1">{event.summary}</p>)}
        </div>
      )}
      <div className="grid grid-cols-[1fr_auto_auto] gap-2 border-t pt-2">
        <Input aria-label="Main PM에게 지시" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Main PM에게 지시를 입력하세요" onKeyDown={(event) => { if (event.key === "Enter") submitInstruction(); }} />
        <Button variant="outline" onClick={assignFirstInvited} disabled={participants.length === 0}>업무 배정</Button>
        <Button onClick={submitInstruction}>Main PM에게 보내기</Button>
      </div>
    </div>
  );
}

/** R-8: v4.0 AgentCatalogSheet의 카탈로그·바인딩 폼을 그대로 SettingsDialog의 Agent 섹션으로 옮긴 것(기능 변경 없음, C-3 정의/바인딩 분리 유지). */
function AgentSection({ state, commit, onOpenSurface }: {
  state: WorkbenchState; commit: (next: WorkbenchState) => void; onOpenSurface: (agentId: string, agentName: string) => void;
}) {
  const [selectedId, setSelectedId] = useState(state.agents[0]?.id);
  const selected = state.agents.find((agent) => agent.id === selectedId) ?? state.agents[0];
  const binding = state.bindings.find((item) => item.agentId === selected?.id);
  const [draft, setDraft] = useState<RuntimeBinding | undefined>(binding);
  const [saved, setSaved] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [trackedAgentId, setTrackedAgentId] = useState(selected?.id);

  // 선택된 Agent가 바뀌면 렌더 중에 draft를 리셋한다(React "adjusting state on prop change" 패턴 — useEffect 미사용).
  if (trackedAgentId !== selected?.id) {
    setTrackedAgentId(selected?.id);
    setDraft(binding);
    setSaved(false);
  }

  const addAgent = () => {
    if (!name.trim()) return;
    commit(adapter.addAgent(state, name.trim(), role.trim() || "사용자 지정 역할"));
    setName(""); setRole(""); setAddOpen(false);
  };

  return (
    <div className="flex h-full min-h-0 gap-4">
      <ScrollArea className="h-full w-[260px] shrink-0 border-r pr-3">
        <div className="flex flex-col gap-2 py-1">
          {state.agents.map((agent) => (
            <Card key={agent.id} className={agent.id === selected?.id ? "border-primary" : undefined} onClick={() => setSelectedId(agent.id)} role="button">
              <CardHeader className="flex-row items-center gap-3 p-3">
                <Avatar><AvatarFallback>{agent.name.slice(0, 2)}</AvatarFallback></Avatar>
                <div className="min-w-0 flex-1">
                  <CardTitle className="text-sm">{agent.name}</CardTitle>
                  <CardDescription>{agent.source} · {agent.status}</CardDescription>
                </div>
              </CardHeader>
              <CardFooter className="p-3 pt-0">
                <Button size="sm" variant="outline" disabled={agent.status === "offline"} onClick={(e) => { e.stopPropagation(); onOpenSurface(agent.id, agent.name); }}>Surface에서 열기</Button>
              </CardFooter>
            </Card>
          ))}
          {addOpen ? (
            <Card>
              <CardContent className="flex flex-col gap-2 p-3">
                <Label htmlFor="new-agent-name">이름 *</Label><Input id="new-agent-name" value={name} onChange={(e) => setName(e.target.value)} />
                <Label htmlFor="new-agent-role">역할</Label><Input id="new-agent-role" value={role} onChange={(e) => setRole(e.target.value)} />
                <div className="flex justify-end gap-2 pt-1"><Button size="sm" variant="outline" onClick={() => setAddOpen(false)}>취소</Button><Button size="sm" onClick={addAgent}>추가</Button></div>
              </CardContent>
            </Card>
          ) : <Button variant="outline" onClick={() => setAddOpen(true)}><Plus data-icon="inline-start" />사용자 지정 Agent 추가</Button>}
        </div>
      </ScrollArea>
      {draft && (
        <ScrollArea className="h-full min-w-0 flex-1">
          <div className="flex flex-col gap-4 pr-2">
            <div className="flex items-center justify-between"><h3 className="font-semibold">Runtime Binding</h3><BoundaryBadge type="simulated" /></div>
            <div className="flex flex-col gap-2">
              <Label>Runtime</Label>
              <Select value={draft.runtime} onValueChange={(runtime) => setDraft({ ...draft, runtime, model: runtime === "Claude ACP" ? "claude-sonnet" : "gpt-5.5" })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectGroup><SelectItem value="Codex ACP">Codex ACP</SelectItem><SelectItem value="Claude ACP">Claude ACP</SelectItem></SelectGroup></SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label>Model</Label>
              <Select value={draft.model} onValueChange={(model) => setDraft({ ...draft, model })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectGroup><SelectItem value="gpt-5.5">gpt-5.5</SelectItem><SelectItem value="gpt-5.4">gpt-5.4</SelectItem><SelectItem value="claude-sonnet">Claude Sonnet</SelectItem></SelectGroup></SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between"><Label htmlFor="permission">도구 권한 자동 허용</Label><Switch id="permission" checked={draft.permission === "allow"} onCheckedChange={(checked) => setDraft({ ...draft, permission: checked ? "allow" : "ask" })} /></div>
            {saved && <Alert><AlertTitle>설정 저장됨</AlertTitle><AlertDescription>다음 Surface 세션부터 binding이 적용됩니다. [Simulated]</AlertDescription></Alert>}
            <div className="flex justify-end gap-2"><Button variant="outline" onClick={() => setDraft(binding)}>되돌리기</Button><Button onClick={() => { commit(adapter.updateBinding(state, draft)); setSaved(true); }}>설정 저장</Button></div>
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

/** R-8: 테마·폰트 크기(즉시 로컬 미리보기 적용). */
function AppearanceSection({ settings, updateSettings }: { settings: Settings; updateSettings: (partial: Partial<Settings>) => void }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label>테마</Label>
        <Select value={settings.theme} onValueChange={(theme) => updateSettings({ theme: theme as ThemeMode })}>
          <SelectTrigger aria-label="테마"><SelectValue /></SelectTrigger>
          <SelectContent><SelectGroup><SelectItem value="system">시스템</SelectItem><SelectItem value="light">라이트</SelectItem><SelectItem value="dark">다크</SelectItem></SelectGroup></SelectContent>
        </Select>
      </div>
      <div className="flex flex-col gap-2">
        <Label>폰트 크기</Label>
        <Select value={settings.fontScale} onValueChange={(fontScale) => updateSettings({ fontScale: fontScale as FontScale })}>
          <SelectTrigger aria-label="폰트 크기"><SelectValue /></SelectTrigger>
          <SelectContent><SelectGroup><SelectItem value="sm">작게</SelectItem><SelectItem value="md">보통</SelectItem><SelectItem value="lg">크게</SelectItem></SelectGroup></SelectContent>
        </Select>
      </div>
    </div>
  );
}

/** R-8: 새 Task 진입 시 기본값. 이미 저장된 PersistedUI의 현재 접힘 상태는 덮어쓰지 않는다. */
function WorkbenchSection({ settings, updateSettings }: { settings: Settings; updateSettings: (partial: Partial<Settings>) => void }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label>새 탭 기본 종류</Label>
        <Select value={settings.defaultNewSurfaceKind} onValueChange={(kind) => updateSettings({ defaultNewSurfaceKind: kind as SurfaceKind })}>
          <SelectTrigger aria-label="새 탭 기본 종류"><SelectValue /></SelectTrigger>
          <SelectContent><SelectGroup>{surfaceMenuItems.map((item) => <SelectItem key={item.kind} value={item.kind}>{item.label}</SelectItem>)}</SelectGroup></SelectContent>
        </Select>
      </div>
      <div className="flex items-center justify-between"><Label htmlFor="sidebar-collapsed-default">좌측 사이드바 기본 접힘</Label><Switch id="sidebar-collapsed-default" checked={settings.sidebarCollapsedDefault} onCheckedChange={(checked) => updateSettings({ sidebarCollapsedDefault: checked })} /></div>
      <div className="flex items-center justify-between"><Label htmlFor="rail-collapsed-default">우측 rail 기본 접힘</Label><Switch id="rail-collapsed-default" checked={settings.railCollapsedDefault} onCheckedChange={(checked) => updateSettings({ railCollapsedDefault: checked })} /></div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="tree-indent-px">파일 트리 들여쓰기(px)</Label>
        <Input
          id="tree-indent-px"
          type="number"
          min={12}
          max={16}
          value={settings.treeIndentPx}
          onChange={(e) => {
            const value = Number(e.target.value);
            if (Number.isFinite(value)) updateSettings({ treeIndentPx: Math.min(16, Math.max(12, value)) });
          }}
        />
      </div>
    </div>
  );
}

/** R-8: Project.repositoryPath 읽기 전용 표시 + mock 경로 변경/제거. */
/** v8.0(§4.3): Project 생성·기존 연결과 등록된 Project의 경로·PM·부모 관계·제거 사후 관리를 모두 담당한다. */
function ProjectSection({ state, commit }: { state: WorkbenchState; commit: (next: WorkbenchState) => void }) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [pathDraft, setPathDraft] = useState("");
  const [parentEditingId, setParentEditingId] = useState<string | null>(null);
  const [removeTargetId, setRemoveTargetId] = useState<string | null>(null);
  const [newProjectDialog, setNewProjectDialog] = useState<{ open: boolean; parentProjectId?: string }>({ open: false });
  const [componentProjectId, setComponentProjectId] = useState<string | null>(null);
  const [componentName, setComponentName] = useState("");
  const [componentPath, setComponentPath] = useState("");

  if (state.projects.length === 0) {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-sm text-muted-foreground">등록된 Project가 없습니다.</p>
        <Button className="w-fit" onClick={() => setNewProjectDialog({ open: true, parentProjectId: undefined })}><Plus data-icon="inline-start" />Project 생성/연결</Button>
        <NewOrLinkProjectDialog state={state} commit={commit} open={newProjectDialog.open} onOpenChange={(open) => setNewProjectDialog((current) => ({ ...current, open }))} parentProjectId={newProjectDialog.parentProjectId} />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="mb-2 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">Project 관리</h3>
          <p className="text-xs text-muted-foreground">최상위 또는 부모 Project를 지정해 신규 생성·기존 연결을 수행합니다.</p>
        </div>
        <Button onClick={() => setNewProjectDialog({ open: true, parentProjectId: undefined })}><Plus data-icon="inline-start" />Project 생성/연결</Button>
      </div>
      {state.projects.map((project) => {
        const pm = state.agents.find((agent) => agent.id === project.pmAgentId);
        const parent = state.projects.find((p) => p.id === project.parentProjectId);
        return (
          <Card key={project.id}>
            <CardContent className="flex flex-col gap-2 p-3">
              <div className="flex items-center gap-2">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{project.name}</p>
                  {editingId === project.id ? (
                    <Input aria-label={`${project.name} 경로`} className="mt-1" value={pathDraft} onChange={(e) => setPathDraft(e.target.value)} />
                  ) : (
                    <p className="truncate text-xs text-muted-foreground">{project.repositoryPath}</p>
                  )}
                </div>
                <Badge variant="secondary">PM:{pm?.name ?? project.pmAgentId}</Badge>
                <span className="text-xs text-muted-foreground">{parent ? parent.name : "(최상위)"}</span>
              </div>
              <div className="flex items-center gap-2">
                <Label className="text-xs">PM</Label><Select value={project.pmAgentId} onValueChange={(value) => commit(adapter.updateProjectPm(state, project.id, value))}><SelectTrigger aria-label={`${project.name} PM`} className="h-8 w-[180px]"><SelectValue /></SelectTrigger><SelectContent>{state.agents.map((agent) => <SelectItem key={agent.id} value={agent.id}>{agent.name}</SelectItem>)}</SelectContent></Select>
              </div>
              <div className="rounded border p-2 text-xs">
                <div className="mb-1 flex items-center justify-between"><span className="font-medium">Repository Components</span><Button size="sm" variant="ghost" onClick={() => setComponentProjectId(project.id)}><Plus className="size-3" />추가</Button></div>
                {state.repositoryComponents.filter((component) => component.projectId === project.id).map((component) => <div key={component.id} className="flex items-center gap-2 py-1"><Badge variant="outline">{component.kind}</Badge><span className="min-w-0 flex-1 truncate">{component.name} · {component.path}</span><Button size="sm" variant="ghost" aria-label={`${component.name} Component 제거`} onClick={() => commit(adapter.removeRepositoryComponent(state, project.id, component.id))}><Trash2 className="size-3" /></Button></div>)}
                {componentProjectId === project.id && <div className="grid grid-cols-[1fr_2fr_auto] gap-1 pt-2"><Input aria-label="Component 이름" value={componentName} onChange={(event) => setComponentName(event.target.value)} placeholder="이름"/><Input aria-label="Component 경로" value={componentPath} onChange={(event) => setComponentPath(event.target.value)} placeholder="경로"/><Button size="sm" onClick={() => { if (!componentName.trim() || !componentPath.trim()) return; commit(adapter.addRepositoryComponent(state, project.id, componentName.trim(), componentPath.trim(), "repo")); setComponentName(""); setComponentPath(""); setComponentProjectId(null); }}>저장</Button></div>}
              </div>
              <div className="flex justify-end gap-2">
                {editingId === project.id ? (
                  <>
                    <Button size="sm" variant="outline" onClick={() => setEditingId(null)}>취소</Button>
                    <Button size="sm" onClick={() => { commit(adapter.updateProjectPath(state, project.id, pathDraft.trim() || project.repositoryPath)); setEditingId(null); }}>저장</Button>
                  </>
                ) : parentEditingId === project.id ? (
                  <>
                    <Select value={project.parentProjectId ?? "__none__"} onValueChange={(value) => {
                      const nextParent = value === "__none__" ? undefined : value;
                      commit(adapter.updateProjectParent(state, project.id, nextParent));
                      setParentEditingId(null);
                    }}>
                      <SelectTrigger aria-label={`${project.name} 부모`} className="h-8 w-[180px]"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          <SelectItem value="__none__">(최상위)</SelectItem>
                          {state.projects.filter((p) => p.id !== project.id && !isDescendantProject(state.projects, project.id, p.id)).map((p) => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                    <Button size="sm" variant="outline" onClick={() => setParentEditingId(null)}>취소</Button>
                  </>
                ) : (
                  <>
                    <Button size="sm" variant="outline" onClick={() => { setEditingId(project.id); setPathDraft(project.repositoryPath); }}>경로 변경</Button>
                    <Button size="sm" variant="outline" onClick={() => setParentEditingId(project.id)}>부모 변경</Button>
                    <Button size="sm" variant="outline" onClick={() => setRemoveTargetId(project.id)}>제거</Button>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
      <AlertDialog open={Boolean(removeTargetId)} onOpenChange={(open) => !open && setRemoveTargetId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>Project를 제거할까요?</AlertDialogTitle><AlertDialogDescription>연결된 Task·데이터는 이번 범위에서 함께 정리되지 않습니다. 자식이 있는 Project는 제거 시 자식이 최상위로 승격됩니다.</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel>취소</AlertDialogCancel><AlertDialogAction onClick={() => { if (removeTargetId) commit(adapter.removeProject(state, removeTargetId)); setRemoveTargetId(null); }}>제거</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <NewOrLinkProjectDialog
        state={state}
        commit={commit}
        open={newProjectDialog.open}
        onOpenChange={(open) => setNewProjectDialog((current) => ({ ...current, open }))}
        parentProjectId={newProjectDialog.parentProjectId}
      />
    </div>
  );
}

/** R-8: `opal.workbench.mock.v4`와 `opal.workbench.settings.v1` 두 키를 모두 지우고 seed로 되돌린다. */
function MockSection({ onReset }: { onReset: () => void }) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  return (
    <div className="flex flex-col gap-3">
      <div>
        <p className="text-sm font-medium">목업 상태 초기화</p>
        <p className="text-xs text-muted-foreground">localStorage를 지우고 seed 데이터로 되돌립니다.</p>
      </div>
      <Button variant="destructive" className="w-fit" onClick={() => setConfirmOpen(true)}>상태 초기화</Button>
      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>정말 초기화할까요?</AlertDialogTitle><AlertDialogDescription>목업 상태와 환경설정이 모두 초기값으로 되돌아갑니다.</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel>취소</AlertDialogCancel><AlertDialogAction onClick={() => { setConfirmOpen(false); onReset(); }}>초기화</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

type SettingsSectionKey = "agent" | "appearance" | "workbench" | "project" | "mock";
const settingsNavItems: { key: SettingsSectionKey; label: string }[] = [
  { key: "agent", label: "Agent" },
  { key: "appearance", label: "외관" },
  { key: "workbench", label: "Workbench" },
  { key: "project", label: "프로젝트" },
  { key: "mock", label: "목업" },
];

/** R-7·R-8: SCR-003 — Dialog(large) + 좌측 SettingsNav + 우측 SettingsPanel. v4.0 AgentCatalogSheet를 Agent 섹션으로 흡수. */
function SettingsDialog({ open, onOpenChange, state, commit, updateSettings, onOpenSurface, onReset }: {
  open: boolean; onOpenChange: (open: boolean) => void; state: WorkbenchState; commit: (next: WorkbenchState) => void;
  updateSettings: (partial: Partial<Settings>) => void; onOpenSurface: (agentId: string, agentName: string) => void; onReset: () => void;
}) {
  const [section, setSection] = useState<SettingsSectionKey>("agent");
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[75vh] max-w-4xl flex-col">
        <DialogHeader><DialogTitle>설정</DialogTitle><DialogDescription>Agent·외관·Workbench·프로젝트·목업 설정을 확인하고 변경합니다.</DialogDescription></DialogHeader>
        <div className="flex min-h-0 flex-1 gap-4">
          <nav className="flex w-[140px] shrink-0 flex-col gap-1 border-r pr-2">
            {settingsNavItems.map((item) => (
              <Button key={item.key} variant={section === item.key ? "secondary" : "ghost"} className="justify-start" onClick={() => setSection(item.key)}>{item.label}</Button>
            ))}
          </nav>
          <div className="min-h-0 min-w-0 flex-1 overflow-auto pr-1">
            {section === "agent" && <AgentSection state={state} commit={commit} onOpenSurface={onOpenSurface} />}
            {section === "appearance" && <AppearanceSection settings={state.settings} updateSettings={updateSettings} />}
            {section === "workbench" && <WorkbenchSection settings={state.settings} updateSettings={updateSettings} />}
            {section === "project" && <ProjectSection state={state} commit={commit} />}
            {section === "mock" && <MockSection onReset={onReset} />}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/** R-7: 좌측 사이드바 최하단 고정 바, 설정 아이콘 1개만 배치. */
function SidebarBottomBar({ onOpenSettings }: { onOpenSettings: () => void }) {
  return (
    <div className="mt-2 shrink-0 border-t pt-2">
      <Button variant="ghost" className="w-full justify-start gap-2" onClick={onOpenSettings}>
        <SettingsIcon className="size-4" />설정
      </Button>
    </div>
  );
}

function SurfaceView({ tab, onSend, onSpawnWorker, coordinationView }: { tab: SurfaceTab; onSend: (body: string) => void; onSpawnWorker: (tabId: string) => void; coordinationView?: React.ReactNode }) {
  const [draft, setDraft] = useState("");
  const send = () => { if (!draft.trim()) return; onSend(draft.trim()); setDraft(""); };
  if (tab.kind === "coordination") return coordinationView ?? <div className="p-4 text-sm text-muted-foreground">조율 TASK를 선택하세요.</div>;
  if (tab.kind === "terminal" || tab.kind === "agent_cli") {
    const isAgentWorkspace = tab.kind === "agent_cli" && tab.readOnly && tab.title.includes("Workspace");
    return (
      <div className="flex h-full flex-col gap-2 p-3">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-medium">{tab.title}{tab.kind === "terminal" ? " · 독립 Terminal" : " · Agent Terminal"}</span>
          <div className="flex items-center gap-2">
            {tab.readOnly && <Badge variant="outline">관찰 전용 Terminal</Badge>}
            <BoundaryBadge type="simulated" />
          </div>
        </div>
        <ScrollArea className="min-h-0 flex-1 rounded-md border bg-muted/30 p-2">
          <div className="flex flex-col gap-1 text-xs">
            {(tab.messages ?? []).map((message, index) => <div key={index}><span className="font-semibold">{message.author}:</span> {message.body}</div>)}
            {(tab.messages ?? []).length === 0 && <span className="text-muted-foreground">아직 출력이 없습니다.</span>}
          </div>
        </ScrollArea>
        {tab.readOnly ? (
          <div className="flex justify-end">
            {isAgentWorkspace && <Button size="sm" variant="outline" onClick={() => onSpawnWorker(tab.id)}>Worker 호출 시뮬레이션</Button>}
          </div>
        ) : (
          <div className="flex gap-2">
            <Input aria-label={`${tab.title} 입력`} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={tab.kind === "terminal" ? "명령을 입력하세요" : "메시지를 입력하세요"} onKeyDown={(e) => { if (e.key === "Enter") send(); }} />
            <Button aria-label={`${tab.title} 전송`} onClick={send}>Send</Button>
          </div>
        )}
      </div>
    );
  }
  if (tab.kind === "browser") {
    return <div className="flex h-full flex-col gap-2 p-3"><div className="flex items-center justify-between"><span className="text-xs font-medium">Browser</span><BoundaryBadge type="simulated" /></div><div className="rounded-md border px-2 py-1 text-xs text-muted-foreground">localhost:5173</div><div className="flex flex-1 items-center justify-center rounded-md border bg-muted text-sm text-muted-foreground">(browser canvas mock)</div></div>;
  }
  if (tab.kind === "markdown") {
    return <div className="flex h-full flex-col gap-2 p-3"><div className="flex items-center justify-between"><span className="text-xs font-medium">Markdown</span><BoundaryBadge type="simulated" /></div><div className="rounded-md border p-3 text-sm">## Mock 문서 미리보기</div></div>;
  }
  if (tab.kind === "mobile_emulator") {
    return <div className="flex h-full flex-col items-center justify-center gap-2 p-3"><Smartphone className="size-8 text-muted-foreground" /><BoundaryBadge type="not_connected" /><p className="text-xs text-muted-foreground">CDP 미연결 — 정적 화면 mock</p></div>;
  }
  return <div className="flex h-full flex-col gap-2 p-3"><div className="flex items-center justify-between"><span className="text-xs font-medium">{tab.title}</span><BoundaryBadge type="simulated" /></div><pre className="overflow-auto rounded-md bg-muted p-3 text-xs">{tab.messages?.[0]?.body ?? "변경 없음"}</pre></div>;
}

/**
 * R-10 (W-1 결함 수정): 탭 바(SurfaceTabBar-local)와 pane 본문(SurfaceBody)을 별개의 드롭 타깃으로 분리한다.
 * 탭 바 드롭은 x좌표 기준 삽입 인덱스를 계산해 같은 pane이면 순서 변경, 다른 pane이면 탭 편입으로 처리한다.
 * pane 본문 드롭은 탭 바를 제외한 영역의 rect만으로 computeEdge를 판정해 가장자리 split만 수행한다.
 */
function SurfacePane({ pane, tabsById, onFocus, onClose, onSend, onSpawnWorker, onTabBarDrop, onBodyDrop, addSurfaceAction, coordinationView }: {
  pane: SplitNode & { type: "leaf" };
  tabsById: Map<string, SurfaceTab>;
  onFocus: (paneId: string, tabId: string) => void;
  onClose: (tabId: string) => void;
  onSend: (tabId: string, body: string) => void;
  onSpawnWorker: (tabId: string) => void;
  onTabBarDrop: (paneId: string, event: React.DragEvent, index: number) => void;
  onBodyDrop: (paneId: string, event: React.DragEvent) => void;
  /** W-1 (R-11): 마지막 탭 옆에 고정 배치하는 Surface 추가 버튼. 이 pane이 새 Surface의 대상일 때만 전달된다. */
  addSurfaceAction?: React.ReactNode;
  coordinationView?: React.ReactNode;
}) {
  const [insertIndex, setInsertIndex] = useState<number | null>(null);
  const [dropHint, setDropHint] = useState<"left" | "right" | "top" | "bottom" | null>(null);
  const activeTab = tabsById.get(pane.activeTabId);
  return (
    <div className="relative flex h-full min-h-0 flex-col" data-testid="surface-pane" data-pane-id={pane.paneId}>
      <div
        className="flex shrink-0 items-center border-b bg-muted/20"
        data-testid="surface-tab-bar"
        onDragOver={(event) => {
          event.preventDefault();
          const container = event.currentTarget;
          const tabEls = Array.from(container.querySelectorAll<HTMLElement>('[role="tab"]'));
          let idx = tabEls.length;
          for (let i = 0; i < tabEls.length; i += 1) {
            const r = tabEls[i].getBoundingClientRect();
            if (event.clientX < r.left + r.width / 2) { idx = i; break; }
          }
          setInsertIndex(idx);
        }}
        onDragLeave={() => setInsertIndex(null)}
        onDrop={(event) => {
          event.preventDefault();
          const idx = insertIndex ?? pane.tabIds.length;
          setInsertIndex(null);
          onTabBarDrop(pane.paneId, event, idx);
        }}
      >
        <div className="flex min-w-0 flex-1 items-center gap-0.5 overflow-x-auto px-1">
          {pane.tabIds.map((tabId, index) => {
            const tab = tabsById.get(tabId);
            if (!tab) return null;
            return (
              <div key={tabId} className="flex shrink-0 items-center">
                {insertIndex === index && <span className="mx-0.5 h-5 w-0.5 shrink-0 bg-primary" data-testid="tab-insert-caret" />}
                <div
                  role="tab"
                  aria-selected={tabId === pane.activeTabId}
                  draggable
                  onDragStart={(event) => { event.dataTransfer.setData("text/plain", JSON.stringify({ tabId, sourcePaneId: pane.paneId })); }}
                  onClick={() => onFocus(pane.paneId, tabId)}
                  className={`flex cursor-pointer items-center gap-1.5 border-b-2 px-2 py-1.5 text-xs ${tabId === pane.activeTabId ? "border-primary bg-background font-medium" : "border-transparent text-muted-foreground"}`}
                >
                  {surfaceIcon[tab.kind]}
                  <SurfaceTabStatusIndicator status={tab.sessionStatus} failureSummary={tab.failureSummary} />
                  <span className="max-w-[120px] truncate">{tab.title}</span>
                  <button aria-label={`${tab.title} 닫기`} onClick={(event) => { event.stopPropagation(); onClose(tabId); }} className="rounded p-0.5 hover:bg-muted"><X className="size-3" /></button>
                </div>
              </div>
            );
          })}
          {insertIndex === pane.tabIds.length && <span className="mx-0.5 h-5 w-0.5 shrink-0 bg-primary" data-testid="tab-insert-caret" />}
        </div>
        {addSurfaceAction && <div className="shrink-0 px-1">{addSurfaceAction}</div>}
      </div>
      <div
        className="relative min-h-0 flex-1"
        data-testid="surface-pane-body"
        onDragOver={(event) => {
          event.preventDefault();
          const rect = event.currentTarget.getBoundingClientRect();
          const result = computeEdge(event, rect);
          setDropHint(result === "center" ? null : `${result.direction === "horizontal" ? (result.edge === "start" ? "left" : "right") : (result.edge === "start" ? "top" : "bottom")}` as never);
        }}
        onDragLeave={() => setDropHint(null)}
        onDrop={(event) => { event.preventDefault(); setDropHint(null); onBodyDrop(pane.paneId, event); }}
      >
        {activeTab ? <SurfaceView tab={activeTab} onSend={(body) => onSend(activeTab.id, body)} onSpawnWorker={onSpawnWorker} coordinationView={coordinationView} /> : <div className="flex h-full items-center justify-center text-sm text-muted-foreground">탭이 없습니다</div>}
        {dropHint && <div className={`pointer-events-none absolute z-10 bg-primary/20 ${
          dropHint === "left" ? "inset-y-0 left-0 w-1/4" : dropHint === "right" ? "inset-y-0 right-0 w-1/4" :
          dropHint === "top" ? "inset-x-0 top-0 h-1/4" : "inset-x-0 bottom-0 h-1/4"
        }`} data-testid="split-drop-hint" />}
      </div>
    </div>
  );
}

function SurfaceSplitRoot({ node, tabsById, onFocus, onClose, onSend, onSpawnWorker, onTabBarDrop, onBodyDrop, addSurfacePaneId, addSurfaceAction, coordinationView }: {
  node: SplitNode;
  tabsById: Map<string, SurfaceTab>;
  onFocus: (paneId: string, tabId: string) => void;
  onClose: (tabId: string) => void;
  onSend: (tabId: string, body: string) => void;
  onSpawnWorker: (tabId: string) => void;
  onTabBarDrop: (paneId: string, event: React.DragEvent, index: number) => void;
  onBodyDrop: (paneId: string, event: React.DragEvent) => void;
  /** W-1 (R-11): adapter.openSurface가 새 탭을 편입하는 pane(항상 첫 leaf)의 id. 이 pane의 tab bar에만 addSurfaceAction을 렌더한다. */
  addSurfacePaneId?: string;
  addSurfaceAction?: React.ReactNode;
  coordinationView?: React.ReactNode;
}) {
  if (node.type === "leaf") {
    return (
      <SurfacePane
        pane={node}
        tabsById={tabsById}
        onFocus={onFocus}
        onClose={onClose}
        onSend={onSend}
        onSpawnWorker={onSpawnWorker}
        onTabBarDrop={onTabBarDrop}
        onBodyDrop={onBodyDrop}
        addSurfaceAction={node.paneId === addSurfacePaneId ? addSurfaceAction : undefined}
        coordinationView={coordinationView}
      />
    );
  }
  return (
    <ResizablePanelGroup direction={node.direction === "horizontal" ? "horizontal" : "vertical"}>
      {node.children.map((child, index) => (
        <Fragment key={`split-child-${index}`}>
          {index > 0 && <ResizableHandle withHandle />}
          <ResizablePanel defaultSize={node.sizes[index] ?? 100 / node.children.length} minSize={15}>
            <SurfaceSplitRoot node={child} tabsById={tabsById} onFocus={onFocus} onClose={onClose} onSend={onSend} onSpawnWorker={onSpawnWorker} onTabBarDrop={onTabBarDrop} onBodyDrop={onBodyDrop} addSurfacePaneId={addSurfacePaneId} addSurfaceAction={addSurfaceAction} coordinationView={coordinationView} />
          </ResizablePanel>
        </Fragment>
      ))}
    </ResizablePanelGroup>
  );
}

/** AC-17: git 상태를 M/U/⊘ 배지로 표시한다. clean은 배지 없음. */
function GitStatusBadge({ status }: { status: GitFileStatus }) {
  if (status === "clean") return null;
  const label = status === "modified" ? "M" : status === "untracked" ? "U" : "⊘";
  return <span className="shrink-0 rounded px-1 text-[10px] font-semibold text-muted-foreground" aria-label={`git status: ${status}`}>{label}</span>;
}

/** R-6·a: 셰브론/아이콘/라벨/배지/삭제 한 줄. FileTree 재귀는 이 행의 형제로 렌더된다. */
function FileTreeRow({ node, depth, expanded, indentPx, onToggleExpand, onSelectDiff, onDelete }: {
  node: FileNode; depth: number; expanded: boolean; indentPx: number;
  onToggleExpand: (node: FileNode) => void; onSelectDiff: (node: FileNode) => void; onDelete: (node: FileNode) => void;
}) {
  const isFolder = node.kind === "folder";
  const label = node.path.split("/").pop();
  return (
    <div className="group flex items-center gap-1 rounded px-1 py-0.5 text-xs hover:bg-accent" style={{ paddingLeft: depth * indentPx }}>
      {isFolder ? (
        <button aria-label={`${node.path} ${expanded ? "접기" : "펼치기"}`} onClick={() => onToggleExpand(node)} className="shrink-0">
          {expanded ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
        </button>
      ) : (
        <span className="inline-block size-3.5 shrink-0" />
      )}
      {isFolder ? <Folder className="size-3.5 shrink-0 text-muted-foreground" /> : <FileText className="size-3.5 shrink-0 text-muted-foreground" />}
      <button
        className={`flex-1 truncate text-left ${node.gitStatus === "ignored" ? "italic text-muted-foreground" : ""}`}
        onClick={() => (isFolder ? onToggleExpand(node) : onSelectDiff(node))}
      >
        {label}
      </button>
      <GitStatusBadge status={node.gitStatus} />
      <button aria-label={`${node.path} 삭제`} className="shrink-0 opacity-0 group-hover:opacity-100" onClick={() => onDelete(node)}><Trash2 className="size-3" /></button>
    </div>
  );
}

/** R-6: 노드 wrapper(flex-col) 안에서 행(FileTreeRow)과 자식 재귀(FileTree)가 형제로 세로로 쌓인다. */
function FileTree({ nodes, expandedFolderIds, indentPx, onToggleExpand, onSelectDiff, onDelete, depth = 0 }: {
  nodes: FileNode[]; expandedFolderIds: string[]; indentPx: number;
  onToggleExpand: (node: FileNode) => void; onSelectDiff: (node: FileNode) => void; onDelete: (node: FileNode) => void; depth?: number;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      {nodes.map((node) => {
        const expanded = expandedFolderIds.includes(node.id);
        return (
          <div key={node.id} className="flex flex-col">
            <FileTreeRow node={node} depth={depth} expanded={expanded} indentPx={indentPx} onToggleExpand={onToggleExpand} onSelectDiff={onSelectDiff} onDelete={onDelete} />
            {expanded && node.children && (
              <FileTree nodes={node.children} expandedFolderIds={expandedFolderIds} indentPx={indentPx} onToggleExpand={onToggleExpand} onSelectDiff={onSelectDiff} onDelete={onDelete} depth={depth + 1} />
            )}
          </div>
        );
      })}
    </div>
  );
}

/** W-5: 추가만 있으면 `-0`을 생략하고 `+n` 단독 표기한다. */
function DiffStatLabel({ linesAdded, linesRemoved }: { linesAdded: number; linesRemoved: number }) {
  return (
    <span className="shrink-0 text-[10px] tabular-nums text-muted-foreground">
      <span className="text-emerald-600">+{linesAdded}</span>
      {linesRemoved > 0 && <span className="ml-1 text-destructive">-{linesRemoved}</span>}
    </span>
  );
}

function dirOf(path: string): string {
  const idx = path.lastIndexOf("/");
  return idx === -1 ? "(root)" : path.slice(0, idx);
}

/** W-4: 디렉터리별 그룹 + 건수 배지, `변경 사항 N`/`추적되지 않은 파일 N` 2섹션. */
function ChangeGroupList({ changes, collapsedGroups, onToggleGroup, onSelectDiff, onStageToggle }: {
  changes: ChangeEntry[]; collapsedGroups: Set<string>; onToggleGroup: (key: string) => void;
  onSelectDiff: (change: ChangeEntry) => void; onStageToggle: (change: ChangeEntry) => void;
}) {
  const sections: { key: ChangeEntry["status"]; label: string }[] = [
    { key: "staged", label: "변경 사항" },
    { key: "unstaged", label: "추적되지 않은 파일" },
  ];
  return (
    <div className="flex flex-col gap-3">
      {sections.map((section) => {
        const items = changes.filter((change) => change.status === section.key);
        const groups = new Map<string, ChangeEntry[]>();
        for (const change of items) {
          const dir = dirOf(change.path);
          groups.set(dir, [...(groups.get(dir) ?? []), change]);
        }
        return (
          <div key={section.key} className="flex flex-col gap-1">
            <p className="text-xs font-semibold text-muted-foreground">{section.label} {items.length}</p>
            {items.length === 0 && <p className="text-xs text-muted-foreground">{section.key === "staged" ? "변경 사항이 없습니다." : "추적되지 않은 파일이 없습니다."}</p>}
            {[...groups.entries()].map(([dir, entries]) => {
              const groupKey = `${section.key}:${dir}`;
              const collapsed = collapsedGroups.has(groupKey);
              return (
                <div key={groupKey} className="flex flex-col gap-0.5">
                  <button className="flex items-center justify-between rounded px-1 py-0.5 text-left text-xs font-medium hover:bg-accent" onClick={() => onToggleGroup(groupKey)}>
                    <span className="flex items-center gap-1 truncate">{collapsed ? <ChevronRight className="size-3.5" /> : <ChevronDown className="size-3.5" />}{dir}</span>
                    <span className="shrink-0 rounded bg-muted px-1.5 text-[10px] text-muted-foreground">{entries.length}</span>
                  </button>
                  {!collapsed && entries.map((change) => (
                    <div key={change.id} className="flex items-center justify-between rounded px-2 py-1 text-xs" style={{ paddingLeft: 20 }}>
                      <button className="flex flex-1 items-center gap-1 truncate text-left" onClick={() => onSelectDiff(change)}>
                        <span className="w-3 shrink-0 font-semibold text-muted-foreground">{change.status === "staged" ? "M" : "U"}</span>
                        <span className="truncate">{change.path.split("/").pop()}</span>
                      </button>
                      <DiffStatLabel linesAdded={change.linesAdded} linesRemoved={change.linesRemoved} />
                      <Button size="sm" variant="ghost" onClick={() => onStageToggle(change)}>{change.status === "staged" ? "unstage" : "stage"}</Button>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

export function WorkbenchApp() {
  const [{ state: initialState, recovered }] = useState(() => adapter.load());
  const [state, setState] = useState<WorkbenchState>(initialState);
  const [board, setBoard] = useState(false);
  const [newTaskOpen, setNewTaskOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [recoveryAlert, setRecoveryAlert] = useState(recovered);
  const [newFileOpen, setNewFileOpen] = useState(false);
  const [newFileName, setNewFileName] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<FileNode | null>(null);
  const [commitMessage, setCommitMessage] = useState("");
  const [collapsedChangeGroups, setCollapsedChangeGroups] = useState<Set<string>>(new Set());
  const sidebarPanelRef = useRef<ImperativePanelHandle>(null);
  const railPanelRef = useRef<ImperativePanelHandle>(null);

  const commit = (next: WorkbenchState) => { setState(next); adapter.save(next); adapter.saveSettings(next.settings); };
  const updateSettings = (partial: Partial<Settings>) => commit(adapter.updateSettings(state, partial));

  const task = state.tasks.find((item) => item.id === state.taskId);
  const activeProject = state.projects.find((p) => p.id === state.activeProjectId);
  const activeRepositoryComponents = state.repositoryComponents.filter((component) => activeProject?.repositoryComponentIds.includes(component.id));
  const layout = task ? (state.surfaceLayoutByTask[task.id] ?? { taskId: task.id, root: { type: "leaf" as const, paneId: `pane_${task.id}`, tabIds: [], activeTabId: "" } }) : undefined;
  const tabsById = useMemo(() => new Map(state.surfaceTabs.filter((tab) => tab.taskId === task?.id).map((tab) => [tab.id, tab])), [state.surfaceTabs, task?.id]);
  const hasSurfaces = layout ? collectLeaves(layout.root).some((leaf) => leaf.tabIds.length > 0) : false;
  const activeRepoId = state.activeRepositoryComponentId ?? (activeRepositoryComponents.length === 1 ? activeRepositoryComponents[0].id : undefined);
  const filesScopeKey = activeRepoId ?? state.activeProjectId;
  const files = state.fileNodesByProject[filesScopeKey] ?? state.fileNodesByProject[state.activeProjectId] ?? [];
  const changes = state.changesByProject[filesScopeKey] ?? state.changesByProject[state.activeProjectId] ?? [];

  useEffect(() => {
    const timer = setInterval(() => { setState((current) => { const next = adapter.tick(current); if (next === current) return current; adapter.save(next); return next; }); }, 1500);
    return () => clearInterval(timer);
  }, []);

  const openSurface = (kind: SurfaceKind, title: string, agentId?: string) => { if (task) commit(adapter.openSurface(state, task.id, kind, title, agentId)); };

  /** R-10 (W-1): 탭 바 드롭 — 같은 pane이면 순서 변경, 다른 pane이면 삽입 인덱스로 탭을 편입한다. */
  const handleTabBarDrop = (targetPaneId: string, event: React.DragEvent, index: number) => {
    if (!task) return;
    const raw = event.dataTransfer.getData("text/plain");
    if (!raw) return;
    const { tabId } = JSON.parse(raw) as { tabId: string; sourcePaneId: string };
    commit(adapter.moveSurfaceTab(state, task.id, tabId, targetPaneId, index));
  };

  /** R-10 (W-1): pane 본문(탭 바 제외) 가장자리 드롭 — split만 수행한다. center 판정은 더 이상 사용하지 않는다. */
  const handleBodyDrop = (targetPaneId: string, event: React.DragEvent) => {
    if (!task) return;
    const raw = event.dataTransfer.getData("text/plain");
    if (!raw) return;
    const { tabId } = JSON.parse(raw) as { tabId: string; sourcePaneId: string };
    const rect = event.currentTarget.getBoundingClientRect();
    const result = computeEdge(event, rect);
    if (result === "center") return;
    commit(adapter.splitSurface(state, task.id, tabId, targetPaneId, result.direction, result.edge));
  };

  const toggleChangeGroup = (key: string) => {
    setCollapsedChangeGroups((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  return (
    <main className="relative flex h-screen min-h-[760px] min-w-[1024px] flex-col overflow-hidden bg-background text-foreground">
      {recoveryAlert && <Alert className="mx-4 mt-2 shrink-0" onClick={() => setRecoveryAlert(false)}><AlertTitle>저장된 상태를 복원하지 못했습니다</AlertTitle><AlertDescription>schema 불일치 또는 파싱 오류로 초기 mock 상태로 되돌렸습니다.</AlertDescription></Alert>}
      <header className="flex h-14 shrink-0 items-center gap-3 border-b px-4">
        <Boxes /><strong>OPAL</strong><Separator orientation="vertical" className="h-6" />
        <span className="truncate text-sm text-muted-foreground">{activeProject?.name ?? "Project"} <ChevronRight className="inline size-4" /> {task?.title ?? "TASK 선택"}</span>
        <div className="ml-auto flex items-center gap-2">
          <BoundaryBadge type="actual" /><Badge variant="outline">Interactive mock</Badge>
          <Button variant="outline" size="sm" onClick={() => setBoard(true)}>Board</Button>
        </div>
      </header>
      {state.sidebarCollapsed && (
        <div className="absolute left-0 top-14 z-20 flex w-6 flex-col items-center border-b border-r bg-background py-1">
          <Button aria-label="좌측 사이드바 펼치기" size="sm" variant="ghost" className="size-6 p-0" onClick={() => { try { sidebarPanelRef.current?.expand(); } catch { /* 레이아웃 측정 전(happy-dom 등)에는 imperative 호출이 실패할 수 있어 state가 진실원본 */ } commit(adapter.toggleSidebarCollapsed(state, false)); }}><PanelLeftOpen className="size-3.5" /></Button>
        </div>
      )}
      {state.railCollapsed && (
        <div className="absolute right-0 top-14 z-20 flex w-6 flex-col items-center border-b border-l bg-background py-1">
          <Button aria-label="우측 사이드바 펼치기" size="sm" variant="ghost" className="size-6 p-0" onClick={() => { try { railPanelRef.current?.expand(); } catch { /* see 좌측 expand */ } commit(adapter.toggleRailCollapsed(state, false)); }}><PanelRightOpen className="size-3.5" /></Button>
        </div>
      )}
      <ResizablePanelGroup direction="horizontal" className="min-h-0 flex-1">
        <ResizablePanel
          ref={sidebarPanelRef}
          defaultSize={20}
          minSize={18}
          maxSize={28}
          collapsible
          collapsedSize={0}
          onCollapse={() => commit(adapter.toggleSidebarCollapsed(state, true))}
          onExpand={() => commit(adapter.toggleSidebarCollapsed(state, false))}
        >
          {state.sidebarCollapsed ? null : (
          <aside className="flex h-full min-h-0 flex-col p-3">
            <div className="flex items-center justify-end">
              <Button aria-label="좌측 사이드바 접기" size="sm" variant="ghost" onClick={() => { try { sidebarPanelRef.current?.collapse(); } catch { /* see expand handler */ } commit(adapter.toggleSidebarCollapsed(state, true)); }}><PanelLeftClose className="size-4" /></Button>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-muted-foreground">PROJECTS</p>
              <Button aria-label="TASK 추가" title="TASK 추가" size="sm" variant="ghost" onClick={() => setNewTaskOpen(true)}><Plus className="size-3.5" /></Button>
            </div>
            <ScrollArea className="mt-1 min-h-0 flex-1">
              <ProjectTree
                state={state}
                onSelect={(projectId) => commit(adapter.switchProject(state, projectId))}
                onSelectTask={(selectedTask, agentId) => commit(adapter.selectTask(state, selectedTask.id, agentId))}
                onToggle={(projectId) => commit(adapter.toggleProjectExpanded(state, projectId))}
              />
            </ScrollArea>
            <SidebarBottomBar onOpenSettings={() => setSettingsOpen(true)} />
          </aside>
          )}
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={56} minSize={40}>
          <section className="relative flex h-full min-h-0 min-w-0 flex-col">
            {!task ? (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">연결된 Task가 없습니다</div>
            ) : (
              <>
                <div className="flex h-10 shrink-0 items-center justify-between border-b px-3">
                  <div className="min-w-0">
                    <h2 className="truncate text-xs font-semibold uppercase tracking-wide text-muted-foreground">Execution Workspace</h2>
                    <p className="truncate text-[11px] text-muted-foreground">PM Coordination · Agent Terminal · 독립 Terminal</p>
                  </div>
                </div>
                <div className="min-h-0 flex-1">
                  {hasSurfaces && layout ? (
                    <SurfaceSplitRoot
                      node={layout.root}
                      addSurfacePaneId={collectLeaves(layout.root)[0]?.paneId}
                      addSurfaceAction={(
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild><Button size="sm" variant="ghost" aria-label="Surface 추가"><Plus className="size-4" /></Button></DropdownMenuTrigger>
                          <DropdownMenuContent>
                            {surfaceMenuItems.map((item) => <DropdownMenuItem key={item.kind} onSelect={() => openSurface(item.kind, item.label)}>{item.label}</DropdownMenuItem>)}
                            <Separator className="my-1" />
                            {state.agents.filter((a) => a.status !== "offline").map((agent) => <DropdownMenuItem key={agent.id} onSelect={() => openSurface("agent_cli", `${agent.name} Agent Terminal`, agent.id)}>{agent.name} Agent Terminal</DropdownMenuItem>)}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                      tabsById={tabsById}
                      onFocus={(paneId, tabId) => commit(adapter.focusSurfaceTab(state, task.id, paneId, tabId))}
                      onClose={(tabId) => commit(adapter.closeSurfaceTab(state, task.id, tabId))}
                      onSend={(tabId, body) => commit(adapter.sendSurfaceMessage(state, tabId, body))}
                      onSpawnWorker={(tabId) => commit(adapter.spawnWorkerFromWorkspace(state, tabId))}
                      onTabBarDrop={handleTabBarDrop}
                      onBodyDrop={handleBodyDrop}
                      coordinationView={state.coordinationRooms.some((room) => room.taskId === task.id) ? <PmCoordinationSurface
                        state={state}
                        task={task}
                        onSelectProject={(projectId) => commit(adapter.switchProject(state, projectId))}
                        onAssign={(projectId, title, pilot) => commit(adapter.assignSubProjectTask(state, task.id, projectId, title, pilot))}
                        onInstruction={(summary) => commit(adapter.recordMainPmInstruction(state, task.id, summary))}
                        onInvite={(projectId) => commit(adapter.inviteSubPmToRoom(state, task.id, projectId))}
                      /> : undefined}
                    />
                  ) : (
                    <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-muted-foreground">
                      <p>열린 작업 공간이 없습니다</p>
                      <Button size="sm" onClick={() => openSurface(state.settings.defaultNewSurfaceKind, surfaceMenuItems.find((item) => item.kind === state.settings.defaultNewSurfaceKind)?.label ?? "Terminal")}>+ Surface 열기</Button>
                    </div>
                  )}
                </div>
              </>
            )}
          </section>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel
          ref={railPanelRef}
          defaultSize={24}
          minSize={14}
          maxSize={32}
          collapsible
          collapsedSize={0}
          onCollapse={() => commit(adapter.toggleRailCollapsed(state, true))}
          onExpand={() => commit(adapter.toggleRailCollapsed(state, false))}
        >
          {state.railCollapsed ? null : (
          <aside className="flex h-full min-h-0 flex-col border-l">
            <div className="grid grid-cols-[1fr_1fr_auto] items-center border-b">
              <button className={`p-2 text-xs font-medium ${state.railTab === "files" ? "border-b-2 border-primary" : "text-muted-foreground"}`} onClick={() => commit(adapter.setRailTab(state, "files"))}>Files</button>
              <button className={`p-2 text-xs font-medium ${state.railTab === "changes" ? "border-b-2 border-primary" : "text-muted-foreground"}`} onClick={() => commit(adapter.setRailTab(state, "changes"))}>Changes</button>
              <Button aria-label="우측 사이드바 접기" size="sm" variant="ghost" onClick={() => { try { railPanelRef.current?.collapse(); } catch { /* see 좌측 collapse */ } commit(adapter.toggleRailCollapsed(state, true)); }}><PanelRightClose className="size-4" /></Button>
            </div>
            {activeRepositoryComponents.length > 1 && (
              <div className="border-b p-2">
                <Select value={activeRepoId ?? ""} onValueChange={(value) => commit(adapter.setActiveRepositoryComponent(state, value))}>
                  <SelectTrigger aria-label="Repo" className="h-8"><SelectValue placeholder="repo 선택" /></SelectTrigger>
                  <SelectContent><SelectGroup>{activeRepositoryComponents.map((component) => <SelectItem key={component.id} value={component.id}>{component.name}</SelectItem>)}</SelectGroup></SelectContent>
                </Select>
              </div>
            )}
            {state.railTab === "files" ? (
              <div className="flex min-h-0 flex-1 flex-col p-2">
                <div className="mb-2 flex gap-1">
                  <Button size="sm" variant="outline" onClick={() => setNewFileOpen(true)}><FolderPlus className="size-3.5" data-icon="inline-start" />새 파일</Button>
                </div>
                {newFileOpen && (
                  <div className="mb-2 flex gap-1">
                    <Input aria-label="새 파일 이름" value={newFileName} onChange={(e) => setNewFileName(e.target.value)} placeholder="파일 이름" />
                    <Button size="sm" onClick={() => { if (newFileName.trim()) { commit(adapter.createFileNode(state, filesScopeKey, undefined, newFileName.trim(), "file")); setNewFileName(""); setNewFileOpen(false); } }}>추가</Button>
                  </div>
                )}
                <ScrollArea className="min-h-0 flex-1">
                  <FileTree
                    nodes={files}
                    expandedFolderIds={state.expandedFolderIds}
                    indentPx={state.settings.treeIndentPx}
                    onToggleExpand={(node) => commit(adapter.toggleFolderExpanded(state, node.id))}
                    onSelectDiff={(node) => task && commit(adapter.openDiffSurface(state, task.id, { id: node.id, projectId: state.activeProjectId, path: node.path, status: "unstaged", diffPreview: `${node.path} 변경 내용 mock`, linesAdded: 0, linesRemoved: 0 }))}
                    onDelete={(node) => setDeleteTarget(node)}
                  />
                </ScrollArea>
              </div>
            ) : (
              <div className="flex min-h-0 flex-1 flex-col gap-2 p-2">
                <ScrollArea className="min-h-0 flex-1">
                  <ChangeGroupList
                    changes={changes}
                    collapsedGroups={collapsedChangeGroups}
                    onToggleGroup={toggleChangeGroup}
                    onSelectDiff={(change) => task && commit(adapter.openDiffSurface(state, task.id, change))}
                    onStageToggle={(change) => commit(adapter.stageMock(state, filesScopeKey, change.id, change.status === "staged" ? "unstaged" : "staged"))}
                  />
                </ScrollArea>
                <Textarea aria-label="커밋 메시지" placeholder="커밋 메시지" value={commitMessage} onChange={(e) => setCommitMessage(e.target.value)} />
                <Button size="sm" onClick={() => { commit(adapter.commitMock(state, filesScopeKey)); setCommitMessage(""); }}>커밋 mock</Button>
              </div>
            )}
          </aside>
          )}
        </ResizablePanel>
      </ResizablePanelGroup>
      {board && <TaskBoard state={state} commit={commit} onClose={() => setBoard(false)} />}
      <NewTaskDialog state={state} commit={commit} open={newTaskOpen} onOpenChange={setNewTaskOpen} />
      <SettingsDialog
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        state={state}
        commit={commit}
        updateSettings={updateSettings}
        onOpenSurface={(agentId, agentName) => { setSettingsOpen(false); openSurface("agent_cli", `${agentName} Agent Terminal`, agentId); }}
        onReset={() => { const { state: fresh } = adapter.resetMockState(); setState(fresh); setSettingsOpen(false); }}
      />
      <AlertDialog open={Boolean(deleteTarget)} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>파일을 삭제할까요?</AlertDialogTitle><AlertDialogDescription>{deleteTarget?.path}</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel>취소</AlertDialogCancel><AlertDialogAction onClick={() => { if (deleteTarget) commit(adapter.deleteFileNode(state, filesScopeKey, deleteTarget.id)); setDeleteTarget(null); }}>삭제</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
  );
}
