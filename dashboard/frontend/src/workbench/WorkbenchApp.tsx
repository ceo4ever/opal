/**
 * @header {
 *   "module": "workbench-app",
 *   "layer": "component",
 *   "domain": "workbench",
 *   "description": "SCR-001~003·005·006을 한 데스크톱 shell에서 연결하는 순수 동적 Surface 탭 + split 인터랙티브 목업. 좌·우 사이드바 접기, 계층형 파일 트리(셰브론·아이콘·git 배지), Changes 디렉터리별 그룹핑·diff 통계, 좌측 사이드바 바텀 바 설정 진입점과 Dialog 기반 설정 화면(Agent·외관·Workbench·프로젝트·목업), 탭 바/pane 본문 분리 드롭 타깃을 포함한다. Surface 추가(+)는 각 pane의 탭 바 안 마지막 탭 옆에 위치하고, Task 추가는 좌측 사이드바 TASKS 헤더의 + 버튼이 보드를 거치지 않고 Task 생성 Dialog(NewTaskDialog, Kanban 보드와 공유)를 직접 연다 (wireframe.md v5.1)",
 *   "exports": ["WorkbenchApp"],
 *   "depends": ["mock-workbench-adapter", "shadcn-ui"]
 * }
 */

import { useEffect, useMemo, useRef, useState } from "react";
import type { ImperativePanelHandle } from "react-resizable-panels";
import {
  Bot, Boxes, ChevronDown, ChevronRight, CircleDot, FileCode2, FileText, Folder, FolderPlus, Globe2, Loader2,
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
import { collectLeaves, MockWorkbenchAdapter } from "./mock-adapter";
import type {
  ChangeEntry, FileNode, FontScale, GitFileStatus, RuntimeBinding, SessionStatus, Settings, SplitDirection, SplitNode, SurfaceKind, SurfaceTab, TaskStatus, ThemeMode, WorkbenchState,
} from "./types";

const adapter = new MockWorkbenchAdapter();

const statusLabels: Record<TaskStatus, string> = { todo: "Todo", in_progress: "In progress", review: "Review", done: "Done" };

const surfaceMenuItems: { kind: SurfaceKind; label: string }[] = [
  { kind: "terminal", label: "Terminal" },
  { kind: "browser", label: "Browser" },
  { kind: "markdown", label: "Markdown" },
  { kind: "mobile_emulator", label: "모바일 에뮬레이터" },
];

const surfaceIcon: Record<SurfaceKind, React.ReactElement> = {
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
  const [taskGroupId, setTaskGroupId] = useState<string>(state.taskGroupFilter ?? "__none__");
  const [newGroupName, setNewGroupName] = useState("");
  const [error, setError] = useState("");
  const projectGroups = state.taskGroups.filter((group) => group.projectId === state.activeProjectId);

  const submit = () => {
    if (!title.trim() || !description.trim()) { setError("제목과 설명을 모두 입력하세요."); return; }
    let next = state;
    let groupId = taskGroupId && taskGroupId !== "__none__" ? taskGroupId : undefined;
    if (groupId === "__new__") {
      if (!newGroupName.trim()) { setError("새 태스크 그룹 이름을 입력하세요."); return; }
      next = adapter.createTaskGroup(next, newGroupName.trim());
      groupId = next.taskGroups[next.taskGroups.length - 1].id;
    }
    next = adapter.createTask(next, title.trim(), description.trim(), groupId, "opal-pm");
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
          <div className="flex flex-col gap-2">
            <Label>태스크 그룹</Label>
            <Select value={taskGroupId} onValueChange={setTaskGroupId}>
              <SelectTrigger aria-label="태스크 그룹"><SelectValue placeholder="그룹 없음" /></SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem value="__none__">그룹 없음</SelectItem>
                  {projectGroups.map((group) => <SelectItem key={group.id} value={group.id}>{group.name}</SelectItem>)}
                  <SelectItem value="__new__">+ 새로 만들기</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
            {taskGroupId === "__new__" && <Input aria-label="새 태스크 그룹 이름" placeholder="새 그룹 이름" value={newGroupName} onChange={(e) => setNewGroupName(e.target.value)} />}
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
function ProjectSection({ state, commit }: { state: WorkbenchState; commit: (next: WorkbenchState) => void }) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [pathDraft, setPathDraft] = useState("");
  const [removeTargetId, setRemoveTargetId] = useState<string | null>(null);

  if (state.projects.length === 0) {
    return <p className="text-sm text-muted-foreground">등록된 Project가 없습니다.</p>;
  }

  return (
    <div className="flex flex-col gap-2">
      {state.projects.map((project) => (
        <Card key={project.id}>
          <CardContent className="flex items-center gap-2 p-3">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{project.name}</p>
              {editingId === project.id ? (
                <Input aria-label={`${project.name} 경로`} className="mt-1" value={pathDraft} onChange={(e) => setPathDraft(e.target.value)} />
              ) : (
                <p className="truncate text-xs text-muted-foreground">{project.repositoryPath}</p>
              )}
            </div>
            {editingId === project.id ? (
              <>
                <Button size="sm" variant="outline" onClick={() => setEditingId(null)}>취소</Button>
                <Button size="sm" onClick={() => { commit(adapter.updateProjectPath(state, project.id, pathDraft.trim() || project.repositoryPath)); setEditingId(null); }}>저장</Button>
              </>
            ) : (
              <>
                <Button size="sm" variant="outline" onClick={() => { setEditingId(project.id); setPathDraft(project.repositoryPath); }}>경로 변경</Button>
                <Button size="sm" variant="outline" onClick={() => setRemoveTargetId(project.id)}>제거</Button>
              </>
            )}
          </CardContent>
        </Card>
      ))}
      <AlertDialog open={Boolean(removeTargetId)} onOpenChange={(open) => !open && setRemoveTargetId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>Project를 제거할까요?</AlertDialogTitle><AlertDialogDescription>연결된 Task·데이터는 이번 범위에서 함께 정리되지 않습니다.</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel>취소</AlertDialogCancel><AlertDialogAction onClick={() => { if (removeTargetId) commit(adapter.removeProject(state, removeTargetId)); setRemoveTargetId(null); }}>제거</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
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

function SurfaceView({ tab, onSend }: { tab: SurfaceTab; onSend: (body: string) => void }) {
  const [draft, setDraft] = useState("");
  const send = () => { if (!draft.trim()) return; onSend(draft.trim()); setDraft(""); };
  if (tab.kind === "terminal" || tab.kind === "agent_cli") {
    return (
      <div className="flex h-full flex-col gap-2 p-3">
        <div className="flex items-center justify-between"><span className="text-xs font-medium">{tab.title}{tab.kind === "terminal" ? " · Terminal" : ""}</span><BoundaryBadge type="simulated" /></div>
        <ScrollArea className="min-h-0 flex-1 rounded-md border bg-muted/30 p-2">
          <div className="flex flex-col gap-1 text-xs">
            {(tab.messages ?? []).map((message, index) => <div key={index}><span className="font-semibold">{message.author}:</span> {message.body}</div>)}
            {(tab.messages ?? []).length === 0 && <span className="text-muted-foreground">아직 출력이 없습니다.</span>}
          </div>
        </ScrollArea>
        <div className="flex gap-2">
          <Input aria-label={`${tab.title} 입력`} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={tab.kind === "terminal" ? "명령을 입력하세요" : "메시지를 입력하세요"} onKeyDown={(e) => { if (e.key === "Enter") send(); }} />
          <Button aria-label={`${tab.title} 전송`} onClick={send}>Send</Button>
        </div>
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
function SurfacePane({ pane, tabsById, onFocus, onClose, onSend, onTabBarDrop, onBodyDrop, addSurfaceAction }: {
  pane: SplitNode & { type: "leaf" };
  tabsById: Map<string, SurfaceTab>;
  onFocus: (paneId: string, tabId: string) => void;
  onClose: (tabId: string) => void;
  onSend: (tabId: string, body: string) => void;
  onTabBarDrop: (paneId: string, event: React.DragEvent, index: number) => void;
  onBodyDrop: (paneId: string, event: React.DragEvent) => void;
  /** W-1 (R-11): 마지막 탭 옆에 고정 배치하는 Surface 추가 버튼. 이 pane이 새 Surface의 대상일 때만 전달된다. */
  addSurfaceAction?: React.ReactNode;
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
        {activeTab ? <SurfaceView tab={activeTab} onSend={(body) => onSend(activeTab.id, body)} /> : <div className="flex h-full items-center justify-center text-sm text-muted-foreground">탭이 없습니다</div>}
        {dropHint && <div className={`pointer-events-none absolute z-10 bg-primary/20 ${
          dropHint === "left" ? "inset-y-0 left-0 w-1/4" : dropHint === "right" ? "inset-y-0 right-0 w-1/4" :
          dropHint === "top" ? "inset-x-0 top-0 h-1/4" : "inset-x-0 bottom-0 h-1/4"
        }`} data-testid="split-drop-hint" />}
      </div>
    </div>
  );
}

function SurfaceSplitRoot({ node, tabsById, onFocus, onClose, onSend, onTabBarDrop, onBodyDrop, addSurfacePaneId, addSurfaceAction }: {
  node: SplitNode;
  tabsById: Map<string, SurfaceTab>;
  onFocus: (paneId: string, tabId: string) => void;
  onClose: (tabId: string) => void;
  onSend: (tabId: string, body: string) => void;
  onTabBarDrop: (paneId: string, event: React.DragEvent, index: number) => void;
  onBodyDrop: (paneId: string, event: React.DragEvent) => void;
  /** W-1 (R-11): adapter.openSurface가 새 탭을 편입하는 pane(항상 첫 leaf)의 id. 이 pane의 tab bar에만 addSurfaceAction을 렌더한다. */
  addSurfacePaneId?: string;
  addSurfaceAction?: React.ReactNode;
}) {
  if (node.type === "leaf") {
    return (
      <SurfacePane
        pane={node}
        tabsById={tabsById}
        onFocus={onFocus}
        onClose={onClose}
        onSend={onSend}
        onTabBarDrop={onTabBarDrop}
        onBodyDrop={onBodyDrop}
        addSurfaceAction={node.paneId === addSurfacePaneId ? addSurfaceAction : undefined}
      />
    );
  }
  return (
    <ResizablePanelGroup direction={node.direction === "horizontal" ? "horizontal" : "vertical"}>
      {node.children.map((child, index) => (
        <>
          {index > 0 && <ResizableHandle key={`handle-${index}`} withHandle />}
          <ResizablePanel key={`pane-${index}`} defaultSize={node.sizes[index] ?? 100 / node.children.length} minSize={15}>
            <SurfaceSplitRoot node={child} tabsById={tabsById} onFocus={onFocus} onClose={onClose} onSend={onSend} onTabBarDrop={onTabBarDrop} onBodyDrop={onBodyDrop} addSurfacePaneId={addSurfacePaneId} addSurfaceAction={addSurfaceAction} />
          </ResizablePanel>
        </>
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
  const [newGroupName, setNewGroupName] = useState("");
  const [newGroupOpen, setNewGroupOpen] = useState(false);
  const [commitMessage, setCommitMessage] = useState("");
  const [collapsedChangeGroups, setCollapsedChangeGroups] = useState<Set<string>>(new Set());
  const sidebarPanelRef = useRef<ImperativePanelHandle>(null);
  const railPanelRef = useRef<ImperativePanelHandle>(null);

  const commit = (next: WorkbenchState) => { setState(next); adapter.save(next); adapter.saveSettings(next.settings); };
  const updateSettings = (partial: Partial<Settings>) => commit(adapter.updateSettings(state, partial));

  const task = state.tasks.find((item) => item.id === state.taskId);
  const projectTaskGroups = state.taskGroups.filter((group) => group.projectId === state.activeProjectId);
  const projectTasks = state.tasks.filter((item) => item.projectId === state.activeProjectId);
  const visibleTasks = useMemo(
    () => projectTasks.filter((item) => !state.taskGroupFilter || item.taskGroupId === state.taskGroupFilter),
    [projectTasks, state.taskGroupFilter],
  );
  const layout = task ? (state.surfaceLayoutByTask[task.id] ?? { taskId: task.id, root: { type: "leaf" as const, paneId: `pane_${task.id}`, tabIds: [], activeTabId: "" } }) : undefined;
  const tabsById = useMemo(() => new Map(state.surfaceTabs.filter((tab) => tab.taskId === task?.id).map((tab) => [tab.id, tab])), [state.surfaceTabs, task?.id]);
  const hasSurfaces = layout ? collectLeaves(layout.root).some((leaf) => leaf.tabIds.length > 0) : false;
  const files = state.fileNodesByProject[state.activeProjectId] ?? [];
  const changes = state.changesByProject[state.activeProjectId] ?? [];

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
        <span className="truncate text-sm text-muted-foreground">{projectTaskGroups.find((g) => g.id === task?.taskGroupId)?.name ?? "전체"} <ChevronRight className="inline size-4" /> {task?.title ?? "Task 선택"}</span>
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
            <p className="mb-2 text-xs font-semibold text-muted-foreground">PROJECT</p>
            <Select value={state.activeProjectId} onValueChange={(projectId) => commit(adapter.switchProject(state, projectId))}>
              <SelectTrigger aria-label="Project"><SelectValue /></SelectTrigger>
              <SelectContent><SelectGroup>{state.projects.map((project) => <SelectItem key={project.id} value={project.id}>{project.name}</SelectItem>)}</SelectGroup></SelectContent>
            </Select>
            <Separator className="my-3" />
            <div className="flex items-center justify-between"><p className="text-xs font-semibold text-muted-foreground">TASK GROUPS</p><Button size="sm" variant="ghost" onClick={() => setNewGroupOpen(true)}><Plus className="size-3.5" /></Button></div>
            <div className="mt-1 flex flex-col gap-1">
              <Button variant={!state.taskGroupFilter ? "secondary" : "ghost"} className="justify-between" onClick={() => commit(adapter.setTaskGroupFilter(state, undefined))}><span>전체</span><Badge variant="outline">{projectTasks.length}</Badge></Button>
              {projectTaskGroups.map((group) => (
                <Button key={group.id} variant={state.taskGroupFilter === group.id ? "secondary" : "ghost"} className="justify-between" onClick={() => commit(adapter.setTaskGroupFilter(state, group.id))}>
                  <span>{group.name}</span><Badge variant="outline">{projectTasks.filter((t) => t.taskGroupId === group.id).length}</Badge>
                </Button>
              ))}
            </div>
            {newGroupOpen && (
              <div className="mt-2 flex gap-1">
                <Input aria-label="새 태스크 그룹" placeholder="그룹 이름" value={newGroupName} onChange={(e) => setNewGroupName(e.target.value)} />
                <Button size="sm" onClick={() => { if (newGroupName.trim()) { commit(adapter.createTaskGroup(state, newGroupName.trim())); setNewGroupName(""); setNewGroupOpen(false); } }}>추가</Button>
              </div>
            )}
            <Separator className="my-3" />
            <div className="flex items-center justify-between"><p className="text-xs font-semibold text-muted-foreground">TASKS</p><Button aria-label="Task 추가" size="sm" variant="ghost" onClick={() => setNewTaskOpen(true)}><Plus className="size-3.5" /></Button></div>
            <ScrollArea className="min-h-0 flex-1">
              <div className="flex flex-col gap-1 pr-2">
                {visibleTasks.map((taskItem) => (
                  <Button key={taskItem.id} variant={taskItem.id === state.taskId ? "secondary" : "ghost"} className="h-auto justify-start py-2 text-left" onClick={() => commit(adapter.selectTask(state, taskItem.id))}>
                    <CircleDot data-icon="inline-start" />
                    <span className="min-w-0"><span className="block truncate">{taskItem.title}</span><span className="block text-xs text-muted-foreground">{statusLabels[taskItem.status]}</span></span>
                  </Button>
                ))}
              </div>
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
                            {state.agents.filter((a) => a.status !== "offline").map((agent) => <DropdownMenuItem key={agent.id} onSelect={() => openSurface("agent_cli", agent.name, agent.id)}>{agent.name}</DropdownMenuItem>)}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                      tabsById={tabsById}
                      onFocus={(paneId, tabId) => commit(adapter.focusSurfaceTab(state, task.id, paneId, tabId))}
                      onClose={(tabId) => commit(adapter.closeSurfaceTab(state, task.id, tabId))}
                      onSend={(tabId, body) => commit(adapter.sendSurfaceMessage(state, tabId, body))}
                      onTabBarDrop={handleTabBarDrop}
                      onBodyDrop={handleBodyDrop}
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
            {state.railTab === "files" ? (
              <div className="flex min-h-0 flex-1 flex-col p-2">
                <div className="mb-2 flex gap-1">
                  <Button size="sm" variant="outline" onClick={() => setNewFileOpen(true)}><FolderPlus className="size-3.5" data-icon="inline-start" />새 파일</Button>
                </div>
                {newFileOpen && (
                  <div className="mb-2 flex gap-1">
                    <Input aria-label="새 파일 이름" value={newFileName} onChange={(e) => setNewFileName(e.target.value)} placeholder="파일 이름" />
                    <Button size="sm" onClick={() => { if (newFileName.trim()) { commit(adapter.createFileNode(state, state.activeProjectId, undefined, newFileName.trim(), "file")); setNewFileName(""); setNewFileOpen(false); } }}>추가</Button>
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
                    onStageToggle={(change) => commit(adapter.stageMock(state, state.activeProjectId, change.id, change.status === "staged" ? "unstaged" : "staged"))}
                  />
                </ScrollArea>
                <Textarea aria-label="커밋 메시지" placeholder="커밋 메시지" value={commitMessage} onChange={(e) => setCommitMessage(e.target.value)} />
                <Button size="sm" onClick={() => { commit(adapter.commitMock(state, state.activeProjectId)); setCommitMessage(""); }}>커밋 mock</Button>
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
        onOpenSurface={(agentId, agentName) => { setSettingsOpen(false); openSurface("agent_cli", agentName, agentId); }}
        onReset={() => { const { state: fresh } = adapter.resetMockState(); setState(fresh); setSettingsOpen(false); }}
      />
      <AlertDialog open={Boolean(deleteTarget)} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>파일을 삭제할까요?</AlertDialogTitle><AlertDialogDescription>{deleteTarget?.path}</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel>취소</AlertDialogCancel><AlertDialogAction onClick={() => { if (deleteTarget) commit(adapter.deleteFileNode(state, state.activeProjectId, deleteTarget.id)); setDeleteTarget(null); }}>삭제</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
  );
}
