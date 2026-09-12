/**
 * @header {
 *   "module": "mock-workstudio-adapter",
 *   "layer": "adapter",
 *   "domain": "workstudio",
 *   "description": "OPAL WorkStudio의 Project/진행 TASK/Agent 트리, PM Coordination Room, PM별 시각 토큰, terminal scrollback, read-only file tree와 localStorage 스냅샷을 제공하는 mock adapter",
 *   "exports": ["MockWorkbenchAdapter", "WORKSTUDIO_STORAGE_KEY", "WORKBENCH_STORAGE_KEY", "SETTINGS_STORAGE_KEY", "normalizeOpalProjectPath", "hasDuplicateProjectPath", "findPaneForTab", "collectLeaves", "isDescendantProject"]
 * }
 */

import type {
  AgentDefinition,
  ChangeEntry,
  CoordinationEvent,
  CoordinationRoom,
  Environment,
  FileNode,
  PersistedUI,
  Pilot,
  Project,
  RepositoryComponent,
  RuntimeBinding,
  Settings,
  SplitDirection,
  SplitNode,
  SurfaceKind,
  SurfaceLayout,
  SurfaceTab,
  TerminalEntry,
  Task,
  TaskStatus,
  WorkbenchState,
} from "./types";

export const WORKSTUDIO_STORAGE_KEY = "opal.workstudio.mock.v1";
export const WORKBENCH_STORAGE_KEY = WORKSTUDIO_STORAGE_KEY;
export const SETTINGS_STORAGE_KEY = "opal.workstudio.settings.v1";

export function normalizeOpalProjectPath(input: string): string {
  return input.trim().replace(/\\/g, "/").replace(/\/+/g, "/").replace(/\/$/, "");
}

export function hasDuplicateProjectPath(projects: Project[], candidatePath: string): boolean {
  const normalizedCandidate = normalizeOpalProjectPath(candidatePath);
  if (!normalizedCandidate) return false;
  return projects.some((project) => project.repositoryPath && normalizeOpalProjectPath(project.repositoryPath) === normalizedCandidate);
}

function sanitizedProject(project: Project & { kind?: unknown }): Project {
  const { repositoryPath, ...rest } = project;
  delete (rest as { kind?: unknown }).kind;
  return { ...rest, ...(repositoryPath ? { repositoryPath: normalizeOpalProjectPath(repositoryPath) } : {}) };
}

function fileNode(input: Omit<FileNode, "sourceRootId" | "loadState" | "readonly"> & Partial<Pick<FileNode, "sourceRootId" | "loadState" | "readonly">>): FileNode {
  return {
    sourceRootId: input.sourceRootId ?? input.projectId,
    loadState: input.loadState ?? (input.kind === "folder" && input.children?.length === 0 ? "empty" : "loaded"),
    readonly: true,
    ...input,
  };
}

function terminalEntry(kind: TerminalEntry["kind"], text: string, timestamp: string, cwd?: string): TerminalEntry {
  return { id: `term_${timestamp}_${kind}_${text.slice(0, 12)}`, kind, text, timestamp, cwd };
}

function mockTerminalOutput(command: string): string {
  const normalized = command.trim();
  if (normalized === "pwd") return "/workspace";
  if (normalized === "ls") return "workstudio  dashboard  docs  tasks";
  if (!normalized) return "";
  return `mock: ${normalized} [Simulated]`;
}

const defaultSettings: Settings = {
  version: 1,
  theme: "system",
  fontScale: "md",
  defaultNewSurfaceKind: "terminal",
  sidebarCollapsedDefault: false,
  railCollapsedDefault: false,
  treeIndentPx: 14,
};

const seedProjects: Project[] = [
  { id: "project_opal", name: "OPAL", repositoryPath: "/workspace/ai-framework", pmAgentId: "opal-pm", repositoryComponentIds: [] },
  { id: "project_beta", name: "Beta Console", repositoryPath: "/workspace/beta-console", pmAgentId: "opal-pm", repositoryComponentIds: [] },
  // v7.0(W-8) — 실측 대표 구조: StoreLinkStudio Project 아래 Pug·Blend·MAMS 연결(AW-AC-10). StoreLinkStudio는 Main PM 조율용 상위 Project라 실 경로가 없다.
  { id: "project_storelinkstudio", name: "StoreLinkStudio", pmAgentId: "main-pm", repositoryComponentIds: [] },
  { id: "project_pug", name: "Pug", repositoryPath: "/Volumes/Data/StoreLinkStudio/pug", parentProjectId: "project_storelinkstudio", pmAgentId: "pug-pm", repositoryComponentIds: ["repo_pug_app_android", "repo_pug_app_ios", "repo_pug_backend", "repo_pug_frontend", "repo_pug_frontend_admin", "repo_pug_frontend_app"] },
  { id: "project_blend", name: "Blend", repositoryPath: "/Volumes/Data/StoreLinkStudio/blend", parentProjectId: "project_storelinkstudio", pmAgentId: "blend-pm", repositoryComponentIds: ["repo_blend_backend", "repo_blend_batch", "repo_blend_frontend_admin", "repo_blend_frontend_monitor"] },
  { id: "project_mams", name: "MAMS", repositoryPath: "/Volumes/Data/StoreLinkStudio/mams", parentProjectId: "project_storelinkstudio", pmAgentId: "mams-pm", repositoryComponentIds: ["repo_mams_backend", "repo_mams_docker", "repo_mams_frontend", "repo_mams_frontend_test", "repo_mams_frontend_wireframe"] },
];

const seedRepositoryComponents: RepositoryComponent[] = [
  { id: "repo_pug_app_android", projectId: "project_pug", name: "app_android", path: "/Volumes/Data/StoreLinkStudio/pug/app_android", kind: "repo" },
  { id: "repo_pug_app_ios", projectId: "project_pug", name: "app_ios", path: "/Volumes/Data/StoreLinkStudio/pug/app_ios", kind: "repo" },
  { id: "repo_pug_backend", projectId: "project_pug", name: "backend", path: "/Volumes/Data/StoreLinkStudio/pug/backend", kind: "repo" },
  { id: "repo_pug_frontend", projectId: "project_pug", name: "frontend", path: "/Volumes/Data/StoreLinkStudio/pug/frontend", kind: "repo" },
  { id: "repo_pug_frontend_admin", projectId: "project_pug", name: "frontend_admin", path: "/Volumes/Data/StoreLinkStudio/pug/frontend_admin", kind: "repo" },
  { id: "repo_pug_frontend_app", projectId: "project_pug", name: "frontend_app", path: "/Volumes/Data/StoreLinkStudio/pug/frontend_app", kind: "repo" },
  { id: "repo_blend_backend", projectId: "project_blend", name: "backend", path: "/Volumes/Data/StoreLinkStudio/blend/backend", kind: "repo" },
  { id: "repo_blend_batch", projectId: "project_blend", name: "batch", path: "/Volumes/Data/StoreLinkStudio/blend/batch", kind: "repo" },
  { id: "repo_blend_frontend_admin", projectId: "project_blend", name: "frontend_admin", path: "/Volumes/Data/StoreLinkStudio/blend/frontend_admin", kind: "repo" },
  { id: "repo_blend_frontend_monitor", projectId: "project_blend", name: "frontend_monitor", path: "/Volumes/Data/StoreLinkStudio/blend/frontend_monitor", kind: "repo" },
  { id: "repo_mams_backend", projectId: "project_mams", name: "backend", path: "/Volumes/Data/StoreLinkStudio/mams/workspace/backend", kind: "monorepo-area" },
  { id: "repo_mams_docker", projectId: "project_mams", name: "docker", path: "/Volumes/Data/StoreLinkStudio/mams/workspace/docker", kind: "monorepo-area" },
  { id: "repo_mams_frontend", projectId: "project_mams", name: "frontend", path: "/Volumes/Data/StoreLinkStudio/mams/workspace/frontend", kind: "monorepo-area" },
  { id: "repo_mams_frontend_test", projectId: "project_mams", name: "frontend_test", path: "/Volumes/Data/StoreLinkStudio/mams/workspace/frontend_test", kind: "monorepo-area" },
  { id: "repo_mams_frontend_wireframe", projectId: "project_mams", name: "frontend_wireframe", path: "/Volumes/Data/StoreLinkStudio/mams/workspace/frontend_wireframe", kind: "monorepo-area" },
];

const seedEnvironments: Environment[] = [
  { id: "env_01", taskId: "task_login_fix", worktreeLabel: "mock worktree", terminalSessionIds: ["term_01"], browserSessionId: "browser_01", boundary: "not_connected" },
  { id: "env_02", taskId: "task_product", worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" },
  { id: "env_03", taskId: "task_empty", worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" },
  { id: "env_04", taskId: "task_beta_setup", worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" },
  { id: "env_coord", taskId: "coord-storelinkstudio-hierarchy", worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" },
  { id: "env_pug_01", taskId: "task_pug_tree_ui", worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" },
  { id: "env_blend_01", taskId: "task_blend_tree_ui", worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" },
  { id: "env_mams_01", taskId: "task_mams_monorepo", worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" },
];

const seedTasks: Task[] = [
  { id: "task_login_fix", projectId: "project_opal", title: "로그인 오류 수정", description: "로그인 실패 상태를 재현하고 수정", status: "in_progress", leadAgentId: "opal-pm", environmentId: "env_01", ownerProjectId: "project_opal", pilot: "opd", participantProjectIds: ["project_opal"] },
  { id: "task_empty", projectId: "project_opal", title: "빈 Task 상태", description: "Empty state 검토", status: "todo", leadAgentId: "developer", environmentId: "env_03", ownerProjectId: "project_opal", pilot: "opd", participantProjectIds: ["project_opal"] },
  { id: "task_product", projectId: "project_opal", title: "Workbench UX 검토", description: "정보 구조 검토", status: "todo", leadAgentId: "opal-pm", environmentId: "env_02", ownerProjectId: "project_opal", pilot: "opp", participantProjectIds: ["project_opal"] },
  { id: "task_no_group", projectId: "project_opal", title: "분류 없는 Task", description: "별도 묶음 없이 상태·Pilot·담당자 필터로 찾는 Task", status: "todo", leadAgentId: "opal-pm", environmentId: "env_02", ownerProjectId: "project_opal", pilot: "opd", participantProjectIds: ["project_opal"] },
  { id: "task_beta_setup", projectId: "project_beta", title: "초기 설정", description: "Beta Console 초기 설정", status: "todo", leadAgentId: "opal-pm", environmentId: "env_04", ownerProjectId: "project_beta", pilot: "opd", participantProjectIds: ["project_beta"] },
  // v7.0(W-8/§7.1 seed) — StoreLinkStudio Main PM이 Pug/Blend/MAMS PM에게 배정한 조율 TASK
  { id: "coord-storelinkstudio-hierarchy", projectId: "project_storelinkstudio", title: "재귀형 프로젝트 관리 구축", description: "Pug·Blend·MAMS 재귀 Project 트리 도입 조율", status: "in_progress", leadAgentId: "main-pm", environmentId: "env_coord", ownerProjectId: "project_storelinkstudio", pilot: "oppl", participantProjectIds: ["project_pug", "project_blend"] },
  { id: "task_pug_tree_ui", projectId: "project_pug", title: "재귀 트리 UI 구현", description: "ProjectTreeRow 컴포넌트 구현", status: "done", leadAgentId: "pug-pm", environmentId: "env_pug_01", ownerProjectId: "project_pug", pilot: "opd", participantProjectIds: ["project_pug"], coordinationTaskId: "coord-storelinkstudio-hierarchy" },
  { id: "task_blend_tree_ui", projectId: "project_blend", title: "동일 패턴 적용", description: "Blend에도 ProjectTreeRow 패턴 적용", status: "done", leadAgentId: "blend-pm", environmentId: "env_blend_01", ownerProjectId: "project_blend", pilot: "opd", participantProjectIds: ["project_blend"], coordinationTaskId: "coord-storelinkstudio-hierarchy" },
  { id: "task_mams_monorepo", projectId: "project_mams", title: "monorepo-area 표기", description: "monorepo-area 기준 확정 대기", status: "in_progress", leadAgentId: "mams-pm", environmentId: "env_mams_01", ownerProjectId: "project_mams", pilot: "opd", participantProjectIds: ["project_mams"], coordinationTaskId: "coord-storelinkstudio-hierarchy" },
];

const seedCoordinationRooms: CoordinationRoom[] = [
  { id: "room_storelinkstudio_hierarchy", taskId: "coord-storelinkstudio-hierarchy", mainProjectId: "project_storelinkstudio", mainPmAgentId: "main-pm", invitedProjectIds: ["project_pug", "project_blend"] },
];

const seedCoordinationEvents: CoordinationEvent[] = [
  { id: "coord_evt_0", taskId: "coord-storelinkstudio-hierarchy", projectId: "project_storelinkstudio", pmAgentId: "main-pm", type: "instruction", summary: "User → Main PM: \"Pug·Blend 기준부터 맞춰줘\"", timestamp: "2026-09-11T09:00:00+09:00" },
  { id: "coord_evt_0a", taskId: "coord-storelinkstudio-hierarchy", projectId: "project_pug", pmAgentId: "main-pm", type: "invitation", summary: "Main PM → Pug PM: Room 초대 및 Workspace 발동", timestamp: "2026-09-11T09:05:00+09:00" },
  { id: "coord_evt_0b", taskId: "coord-storelinkstudio-hierarchy", projectId: "project_blend", pmAgentId: "main-pm", type: "invitation", summary: "Main PM → Blend PM: Room 초대 및 Workspace 발동", timestamp: "2026-09-11T09:06:00+09:00" },
  { id: "coord_evt_1", taskId: "coord-storelinkstudio-hierarchy", projectId: "project_pug", pmAgentId: "main-pm", type: "assignment", summary: "Main PM → Pug PM: \"재귀 트리 UI 구현\"", timestamp: "2026-09-11T09:10:00+09:00" },
  { id: "coord_evt_2", taskId: "coord-storelinkstudio-hierarchy", projectId: "project_blend", pmAgentId: "main-pm", type: "assignment", summary: "Main PM → Blend PM: \"동일 패턴 적용\"", timestamp: "2026-09-11T09:12:00+09:00" },
  { id: "coord_evt_3", taskId: "coord-storelinkstudio-hierarchy", projectId: "project_pug", pmAgentId: "pug-pm", type: "coordination", summary: "Pug PM ↔ Blend PM: \"ProjectTreeRow 컴포넌트 공유 합의\"", timestamp: "2026-09-11T10:40:00+09:00" },
  { id: "coord_evt_4", taskId: "coord-storelinkstudio-hierarchy", projectId: "project_mams", pmAgentId: "mams-pm", type: "blocker", summary: "MAMS PM: \"monorepo-area 표기 기준 확인 필요\"", timestamp: "2026-09-11T11:05:00+09:00" },
  { id: "coord_evt_5", taskId: "coord-storelinkstudio-hierarchy", projectId: "project_storelinkstudio", pmAgentId: "main-pm", type: "decision", summary: "Main PM: \"실측 기준 monorepo-area 5개로 확정\"", timestamp: "2026-09-11T11:20:00+09:00" },
  { id: "coord_evt_6", taskId: "coord-storelinkstudio-hierarchy", projectId: "project_pug", pmAgentId: "pug-pm", type: "result", summary: "Pug PM: \"트리 뷰 구현 완료\" (Sub PM 개별 결과)", timestamp: "2026-09-11T11:40:00+09:00" },
];

const seedAgents: AgentDefinition[] = [
  { id: "opal-pm", name: "OPAL PM", role: "Product lead", source: "project", path: ".opal/AGENT.md", status: "ready", avatarLabel: "OP", colorToken: "pm-slate", projectId: "project_opal" },
  { id: "developer", name: "Developer", role: "구현 담당", source: "framework", path: "framework/agents/developer.md", status: "idle", avatarLabel: "DV", colorToken: "pm-cyan" },
  { id: "reviewer", name: "Reviewer", role: "검토 담당", source: "framework", path: "framework/agents/reviewer.md", status: "idle", avatarLabel: "RV", colorToken: "pm-amber" },
  { id: "ui-coach", name: "UI Coach", role: "UI 코칭", source: "user", path: "user/agents/ui-coach.md", status: "offline", avatarLabel: "UI", colorToken: "pm-rose" },
  { id: "main-pm", name: "Main PM", role: "StoreLinkStudio 조율 PM", source: "project", path: ".opal/AGENT.md", status: "ready", avatarLabel: "M", colorToken: "pm-violet", projectId: "project_storelinkstudio" },
  { id: "pug-pm", name: "Pug PM", role: "Pug Project PM", source: "project", path: ".opal/AGENT.md", status: "ready", avatarLabel: "P", colorToken: "pm-emerald", projectId: "project_pug" },
  { id: "blend-pm", name: "Blend PM", role: "Blend Project PM", source: "project", path: ".opal/AGENT.md", status: "ready", avatarLabel: "B", colorToken: "pm-sky", projectId: "project_blend" },
  { id: "mams-pm", name: "MAMS PM", role: "MAMS Project PM", source: "project", path: ".opal/AGENT.md", status: "ready", avatarLabel: "M", colorToken: "pm-orange", projectId: "project_mams" },
  { id: "pug-worker", name: "Pug Worker", role: "Pug PM 호출 Worker", source: "framework", path: "framework/agents/worker.md", status: "idle", avatarLabel: "PW", colorToken: "pm-emerald" },
  { id: "blend-worker", name: "Blend Worker", role: "Blend PM 호출 Worker", source: "framework", path: "framework/agents/worker.md", status: "idle", avatarLabel: "BW", colorToken: "pm-sky" },
  { id: "mams-worker", name: "MAMS Worker", role: "MAMS PM 호출 Worker", source: "framework", path: "framework/agents/worker.md", status: "idle", avatarLabel: "MW", colorToken: "pm-orange" },
];

const seedBindings: RuntimeBinding[] = seedAgents.map((agent) => ({
  agentId: agent.id,
  runtime: agent.id === "ui-coach" ? "Claude ACP" : "Codex ACP",
  model: agent.id === "ui-coach" ? "claude-sonnet" : "gpt-5.5",
  mode: "agentic",
  permission: "ask",
  boundary: "simulated",
}));

const seedSurfaceTabs: SurfaceTab[] = [
  { id: "surface_coord_storelink", taskId: "coord-storelinkstudio-hierarchy", kind: "coordination", title: "PM Coordination", roomId: "room_storelinkstudio_hierarchy", boundary: "simulated", closable: true, sessionStatus: "running" },
  { id: "surface_pug_pm_workspace", taskId: "coord-storelinkstudio-hierarchy", kind: "agent_cli", title: "Pug PM Workspace", agentId: "pug-pm", parentAgentId: "main-pm", roomId: "room_storelinkstudio_hierarchy", readOnly: true, boundary: "simulated", closable: true, sessionStatus: "running", messages: [
    { author: "Main PM", body: "Room에 초대합니다. 재귀 트리 UI 기준을 조율해주세요." },
    { author: "Pug PM", body: "Workspace를 열고 담당 Worker를 준비합니다. [Simulated]" },
  ] },
  { id: "surface_blend_pm_workspace", taskId: "coord-storelinkstudio-hierarchy", kind: "agent_cli", title: "Blend PM Workspace", agentId: "blend-pm", parentAgentId: "main-pm", roomId: "room_storelinkstudio_hierarchy", readOnly: true, boundary: "simulated", closable: true, sessionStatus: "running", messages: [
    { author: "Main PM", body: "Room에 초대합니다. Pug PM과 컴포넌트 공유 기준을 맞춰주세요." },
    { author: "Blend PM", body: "Workspace를 열고 의존성을 확인합니다. [Simulated]" },
  ] },
  { id: "surface_dev_01", taskId: "task_login_fix", kind: "agent_cli", title: "Developer Agent Terminal", agentId: "developer", boundary: "simulated", closable: true, sessionStatus: "running", messages: [
    { author: "You", body: "로그인 오류를 구현해줘" },
    { author: "Developer", body: "원인을 분석합니다. [Simulated]" },
  ] },
  { id: "surface_term_01", taskId: "task_login_fix", kind: "terminal", title: "독립 Terminal", boundary: "simulated", closable: true, sessionStatus: "completed", messages: [
    { author: "system", body: "$ npm run dev" },
    { author: "system", body: "> ready [Simulated]" },
  ], terminalEntries: [
    terminalEntry("input", "npm run dev", "2026-09-12T07:29:00.000Z", "/workspace/ai-framework"),
    terminalEntry("output", "> ready [Simulated]", "2026-09-12T07:29:01.000Z", "/workspace/ai-framework"),
  ] },
  { id: "surface_browser_01", taskId: "task_login_fix", kind: "browser", title: "Browser", boundary: "simulated", closable: true, sessionStatus: "completed" },
];

const seedSurfaceLayoutByTask: Record<string, SurfaceLayout> = {
  "coord-storelinkstudio-hierarchy": {
    taskId: "coord-storelinkstudio-hierarchy",
    root: {
      type: "split",
      direction: "horizontal",
      sizes: [58, 42],
      children: [
        { type: "leaf", paneId: "pane_coord_storelink", tabIds: ["surface_coord_storelink"], activeTabId: "surface_coord_storelink" },
        { type: "leaf", paneId: "pane_sub_pm_workspaces", tabIds: ["surface_pug_pm_workspace", "surface_blend_pm_workspace"], activeTabId: "surface_pug_pm_workspace" },
      ],
    },
  },
  task_login_fix: {
    taskId: "task_login_fix",
    root: {
      type: "split",
      direction: "horizontal",
      sizes: [50, 50],
      children: [
        { type: "leaf", paneId: "pane_left", tabIds: ["surface_dev_01"], activeTabId: "surface_dev_01" },
        { type: "leaf", paneId: "pane_right", tabIds: ["surface_term_01", "surface_browser_01"], activeTabId: "surface_term_01" },
      ],
    },
  },
};

const seedFileNodesByProject: Record<string, FileNode[]> = {
  project_opal: [
    fileNode({
      id: "file_src", projectId: "project_opal", path: "src", kind: "folder", gitStatus: "modified", children: [
        fileNode({
          id: "file_workbench", projectId: "project_opal", path: "src/workstudio", kind: "folder", gitStatus: "modified", children: [
            fileNode({ id: "file_types", projectId: "project_opal", path: "src/workstudio/types.ts", kind: "file", gitStatus: "untracked" }),
            fileNode({ id: "file_adapter", projectId: "project_opal", path: "src/workstudio/mock-adapter.ts", kind: "file", gitStatus: "modified" }),
            fileNode({ id: "file_app", projectId: "project_opal", path: "src/workstudio/WorkStudioApp.tsx", kind: "file", gitStatus: "modified" }),
          ],
        }),
        fileNode({
          id: "file_components", projectId: "project_opal", path: "src/components", kind: "folder", gitStatus: "clean", children: [],
        }),
      ],
    }),
    fileNode({ id: "file_node_modules", projectId: "project_opal", path: "node_modules", kind: "folder", gitStatus: "ignored", children: [], loadState: "empty" }),
  ],
  project_beta: [
    fileNode({ id: "file_beta_src", projectId: "project_beta", path: "src", kind: "folder", gitStatus: "clean", children: [], loadState: "empty" }),
  ],
};

const seedChangesByProject: Record<string, ChangeEntry[]> = {
  project_opal: [
    { id: "change_1", projectId: "project_opal", path: "workstudio/src/workstudio/WorkStudioApp.tsx", status: "staged", diffPreview: "- pinned tabs\n+ dynamic surfaces", linesAdded: 12, linesRemoved: 3 },
    { id: "change_2", projectId: "project_opal", path: "tasks/115-…/wireframe.md", status: "staged", diffPreview: "+ 좌우 사이드바 토글 설계", linesAdded: 80, linesRemoved: 6 },
    { id: "change_3", projectId: "project_opal", path: "docs/proposals/new-file.md", status: "unstaged", diffPreview: "+ splitSurface / moveSurfaceTab", linesAdded: 40, linesRemoved: 0 },
  ],
  project_beta: [],
};

function cloneSeed(): WorkbenchState {
  const fileNodesByProject: Record<string, FileNode[]> = JSON.parse(JSON.stringify(seedFileNodesByProject));
  const changesByProject: Record<string, ChangeEntry[]> = JSON.parse(JSON.stringify(seedChangesByProject));
  for (const component of seedRepositoryComponents) {
    fileNodesByProject[component.id] = [fileNode({ id: `file_${component.id}`, projectId: component.id, sourceRootId: component.id, path: component.name, absolutePath: component.path, kind: "folder", gitStatus: "clean", children: [], loadState: "empty" })];
    changesByProject[component.id] = [];
  }
  return {
    activeProjectId: "project_opal",
    taskId: "task_login_fix",
    projects: JSON.parse(JSON.stringify(seedProjects)),
    repositoryComponents: JSON.parse(JSON.stringify(seedRepositoryComponents)),
    tasks: JSON.parse(JSON.stringify(seedTasks)),
    coordinationEvents: JSON.parse(JSON.stringify(seedCoordinationEvents)),
    coordinationRooms: JSON.parse(JSON.stringify(seedCoordinationRooms)),
    environments: JSON.parse(JSON.stringify(seedEnvironments)),
    agents: JSON.parse(JSON.stringify(seedAgents)),
    bindings: JSON.parse(JSON.stringify(seedBindings)),
    surfaceTabs: JSON.parse(JSON.stringify(seedSurfaceTabs)),
    surfaceLayoutByTask: JSON.parse(JSON.stringify(seedSurfaceLayoutByTask)),
    fileNodesByProject,
    changesByProject,
    railTab: "files",
    railWidthPx: 320,
    sidebarWidthPx: 280,
    sidebarCollapsed: false,
    railCollapsed: false,
    expandedFolderIds: ["file_src", "file_workbench"],
    expandedProjectIds: ["project_opal", "project_beta", "project_storelinkstudio", "project_pug", "project_blend", "project_mams"],
    activeRepositoryComponentId: undefined,
    failureMode: false,
    settings: JSON.parse(JSON.stringify(defaultSettings)),
  };
}

/** AW-AC-11: PersistedUI(UI 스냅샷)와 함께 사용자가 생성·연결한 mock 엔티티(Project/RepositoryComponent/Task/CoordinationEvent)도 같은 키에 저장한다. */
type StoredSnapshot = PersistedUI & {
  projects: Project[];
  repositoryComponents: RepositoryComponent[];
  tasks: Task[];
  coordinationEvents: CoordinationEvent[];
  coordinationRooms: CoordinationRoom[];
  environments: Environment[];
  surfaceTabs: SurfaceTab[];
  fileNodesByProject: Record<string, FileNode[]>;
  changesByProject: Record<string, ChangeEntry[]>;
};

function persistedFromState(state: WorkbenchState): StoredSnapshot {
  return {
    version: 5,
    activeProjectId: state.activeProjectId,
    taskId: state.taskId,
    surfaceLayoutByTask: state.surfaceLayoutByTask,
    railTab: state.railTab,
    railWidthPx: state.railWidthPx,
    sidebarWidthPx: state.sidebarWidthPx,
    sidebarCollapsed: state.sidebarCollapsed,
    railCollapsed: state.railCollapsed,
    expandedFolderIds: state.expandedFolderIds,
    expandedProjectIds: state.expandedProjectIds,
    activeRepositoryComponentId: state.activeRepositoryComponentId,
    projects: state.projects.map(sanitizedProject),
    repositoryComponents: state.repositoryComponents,
    tasks: state.tasks,
    coordinationEvents: state.coordinationEvents,
    coordinationRooms: state.coordinationRooms,
    environments: state.environments,
    surfaceTabs: state.surfaceTabs,
    fileNodesByProject: state.fileNodesByProject,
    changesByProject: state.changesByProject,
  };
}

/** Project 계층 순환 방지(§7): candidateParentId가 projectId 자신이거나 그 자손이면 true. */
export function isDescendantProject(projects: Project[], projectId: string, candidateParentId: string): boolean {
  let current = projects.find((p) => p.id === candidateParentId);
  while (current) {
    if (current.id === projectId) return true;
    current = current.parentProjectId ? projects.find((p) => p.id === current!.parentProjectId) : undefined;
  }
  return false;
}

function findPaneOfTab(node: SplitNode, tabId: string): (SplitNode & { type: "leaf" }) | undefined {
  if (node.type === "leaf") return node.tabIds.includes(tabId) ? node : undefined;
  for (const child of node.children) {
    const found = findPaneOfTab(child, tabId);
    if (found) return found;
  }
  return undefined;
}

/** 탭 제거 후 빈 leaf를 정리한다: leaf가 비면 부모 split에서 제거하고, split에 자식이 1개만 남으면 그 자식으로 대체한다. */
function pruneEmptyLeaves(node: SplitNode): SplitNode | undefined {
  if (node.type === "leaf") return node.tabIds.length === 0 ? undefined : node;
  const prunedChildren = node.children.map(pruneEmptyLeaves).filter((child): child is SplitNode => Boolean(child));
  if (prunedChildren.length === 0) return undefined;
  if (prunedChildren.length === 1) return prunedChildren[0];
  return { ...node, children: prunedChildren, sizes: prunedChildren.map(() => 100 / prunedChildren.length) };
}

function removeTabFromNode(node: SplitNode, tabId: string): SplitNode {
  if (node.type === "leaf") {
    if (!node.tabIds.includes(tabId)) return node;
    const tabIds = node.tabIds.filter((id) => id !== tabId);
    const activeTabId = node.activeTabId === tabId ? (tabIds[0] ?? "") : node.activeTabId;
    return { ...node, tabIds, activeTabId };
  }
  return { ...node, children: node.children.map((child) => removeTabFromNode(child, tabId)) };
}

let paneCounter = 0;
function nextPaneId() { paneCounter += 1; return `pane_${Date.now()}_${paneCounter}`; }

export class MockWorkbenchAdapter {
  /** parse 오류나 schema 불일치 시 seed로 복구하며, 호출자가 non-blocking Alert를 표시할 수 있게 alert 플래그를 반환한다. 구 v1/v2 키는 마이그레이션 없이 무시한다. Settings는 별도 키(SETTINGS_STORAGE_KEY)에서 독립적으로 로드해 병합한다(W-4). */
  load(): { state: WorkbenchState; recovered: boolean } {
    const settings = this.loadSettings();
    try {
      const raw = localStorage.getItem(WORKBENCH_STORAGE_KEY);
      if (!raw) return { state: { ...cloneSeed(), settings }, recovered: false };
      const persisted = JSON.parse(raw) as Partial<StoredSnapshot>;
      if (
        persisted.version !== 5 ||
        typeof persisted.activeProjectId !== "string" ||
        typeof persisted.surfaceLayoutByTask !== "object" ||
        persisted.surfaceLayoutByTask === null
      ) {
        return { state: { ...cloneSeed(), settings }, recovered: true };
      }
      const base = cloneSeed();
      return {
        state: {
          ...base,
          activeProjectId: persisted.activeProjectId,
          taskId: persisted.taskId,
          surfaceLayoutByTask: persisted.surfaceLayoutByTask as WorkbenchState["surfaceLayoutByTask"],
          railTab: persisted.railTab === "changes" ? "changes" : "files",
          railWidthPx: typeof persisted.railWidthPx === "number" ? persisted.railWidthPx : base.railWidthPx,
          sidebarWidthPx: typeof persisted.sidebarWidthPx === "number" ? persisted.sidebarWidthPx : base.sidebarWidthPx,
          sidebarCollapsed: typeof persisted.sidebarCollapsed === "boolean" ? persisted.sidebarCollapsed : base.sidebarCollapsed,
          railCollapsed: typeof persisted.railCollapsed === "boolean" ? persisted.railCollapsed : base.railCollapsed,
          expandedFolderIds: Array.isArray(persisted.expandedFolderIds) ? persisted.expandedFolderIds : base.expandedFolderIds,
          expandedProjectIds: Array.isArray(persisted.expandedProjectIds) ? persisted.expandedProjectIds : base.expandedProjectIds,
          activeRepositoryComponentId: persisted.activeRepositoryComponentId,
          projects: Array.isArray(persisted.projects) ? persisted.projects.map((project) => sanitizedProject(project as Project & { kind?: unknown })) : base.projects,
          repositoryComponents: Array.isArray(persisted.repositoryComponents) ? persisted.repositoryComponents : base.repositoryComponents,
          tasks: Array.isArray(persisted.tasks) ? persisted.tasks : base.tasks,
          coordinationEvents: Array.isArray(persisted.coordinationEvents) ? persisted.coordinationEvents : base.coordinationEvents,
          coordinationRooms: Array.isArray(persisted.coordinationRooms) ? persisted.coordinationRooms : base.coordinationRooms,
          environments: Array.isArray(persisted.environments) ? persisted.environments : base.environments,
          surfaceTabs: Array.isArray(persisted.surfaceTabs) ? persisted.surfaceTabs : base.surfaceTabs,
          fileNodesByProject: persisted.fileNodesByProject && typeof persisted.fileNodesByProject === "object" ? persisted.fileNodesByProject : base.fileNodesByProject,
          changesByProject: persisted.changesByProject && typeof persisted.changesByProject === "object" ? persisted.changesByProject : base.changesByProject,
          settings,
        },
        recovered: false,
      };
    } catch {
      return { state: { ...cloneSeed(), settings }, recovered: true };
    }
  }

  save(state: WorkbenchState) {
    localStorage.setItem(WORKBENCH_STORAGE_KEY, JSON.stringify(persistedFromState(state)));
  }

  /** R-8/W-4: Settings는 PersistedUI와 별도 키(SETTINGS_STORAGE_KEY)에 독립 저장한다. */
  loadSettings(): Settings {
    try {
      const raw = localStorage.getItem(SETTINGS_STORAGE_KEY);
      if (!raw) return { ...defaultSettings };
      const parsed = JSON.parse(raw) as Partial<Settings>;
      if (parsed.version !== 1) return { ...defaultSettings };
      return {
        version: 1,
        theme: parsed.theme ?? defaultSettings.theme,
        fontScale: parsed.fontScale ?? defaultSettings.fontScale,
        defaultNewSurfaceKind: parsed.defaultNewSurfaceKind ?? defaultSettings.defaultNewSurfaceKind,
        sidebarCollapsedDefault: typeof parsed.sidebarCollapsedDefault === "boolean" ? parsed.sidebarCollapsedDefault : defaultSettings.sidebarCollapsedDefault,
        railCollapsedDefault: typeof parsed.railCollapsedDefault === "boolean" ? parsed.railCollapsedDefault : defaultSettings.railCollapsedDefault,
        treeIndentPx: typeof parsed.treeIndentPx === "number" ? parsed.treeIndentPx : defaultSettings.treeIndentPx,
      };
    } catch {
      return { ...defaultSettings };
    }
  }

  saveSettings(settings: Settings) {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  }

  updateSettings(state: WorkbenchState, partial: Partial<Settings>): WorkbenchState {
    return { ...state, settings: { ...state.settings, ...partial } };
  }

  updateProjectPath(state: WorkbenchState, projectId: string, repositoryPath: string): WorkbenchState {
    const normalizedPath = normalizeOpalProjectPath(repositoryPath);
    if (hasDuplicateProjectPath(state.projects.filter((project) => project.id !== projectId), normalizedPath)) return state;
    return { ...state, projects: state.projects.map((project) => project.id === projectId ? { ...project, repositoryPath: normalizedPath || undefined } : project) };
  }

  updateProjectPm(state: WorkbenchState, projectId: string, pmAgentId: string): WorkbenchState {
    return { ...state, projects: state.projects.map((project) => project.id === projectId ? { ...project, pmAgentId } : project) };
  }

  /** v6.0(§4.3): Project 제거. 자식이 있으면 최상위로 승격한다(부모 Project·데이터는 정리하지 않음 — 목업 한계 명시). */
  removeProject(state: WorkbenchState, projectId: string): WorkbenchState {
    const projects = state.projects
      .filter((project) => project.id !== projectId)
      .map((project) => project.parentProjectId === projectId ? { ...project, parentProjectId: undefined } : project);
    const activeProjectId = state.activeProjectId === projectId ? (projects[0]?.id ?? "") : state.activeProjectId;
    return { ...state, projects, activeProjectId };
  }

  /** v6.0(§4.3): 부모 Project 변경. 순환(자기 자신·자손을 부모로 지정)이 되면 mutation을 거부하고 state를 그대로 반환한다. */
  updateProjectParent(state: WorkbenchState, projectId: string, parentProjectId: string | undefined): WorkbenchState {
    if (parentProjectId && (parentProjectId === projectId || isDescendantProject(state.projects, projectId, parentProjectId))) {
      return state;
    }
    return { ...state, projects: state.projects.map((project) => project.id === projectId ? { ...project, parentProjectId } : project) };
  }

  /** v6.0(SCR-007 신규 생성 탭, AW-AC-1): 실제 폴더·Git·`.opal` 생성 없이 mock Project 레코드만 추가한다. */
  createProject(state: WorkbenchState, name: string, repositoryPath: string, pmAgentId: string, parentProjectId?: string): WorkbenchState {
    const normalizedPath = normalizeOpalProjectPath(repositoryPath);
    if (normalizedPath && hasDuplicateProjectPath(state.projects, normalizedPath)) return state;
    const project: Project = { id: `project_${Date.now()}`, name, repositoryPath: normalizedPath || undefined, parentProjectId, pmAgentId, repositoryComponentIds: [] };
    const expandedProjectIds = parentProjectId && !state.expandedProjectIds.includes(parentProjectId)
      ? [...state.expandedProjectIds, parentProjectId]
      : state.expandedProjectIds;
    return { ...state, projects: [...state.projects, project], expandedProjectIds };
  }

  /** v6.0(SCR-007 기존 연결 탭, AW-AC-2): `.opal/AGENT.md` mock 발견 결과로 기존 OPAL Project를 연결한다. */
  linkProject(state: WorkbenchState, repositoryPath: string, discoveredPmAgentId: string, parentProjectId?: string): WorkbenchState {
    const normalizedPath = normalizeOpalProjectPath(repositoryPath);
    if (!normalizedPath || hasDuplicateProjectPath(state.projects, normalizedPath)) return state;
    const name = normalizedPath.split("/").filter(Boolean).pop() ?? normalizedPath;
    const stamp = Date.now();
    const projectId = `project_${stamp}`;
    const componentId = `repo_${stamp}`;
    const project: Project = { id: projectId, name, repositoryPath: normalizedPath, parentProjectId, pmAgentId: discoveredPmAgentId, repositoryComponentIds: [componentId] };
    const component: RepositoryComponent = { id: componentId, projectId, name, path: normalizedPath, kind: "repo" };
    return {
      ...state,
      projects: [...state.projects, project],
      repositoryComponents: [...state.repositoryComponents, component],
      expandedProjectIds: parentProjectId && !state.expandedProjectIds.includes(parentProjectId) ? [...state.expandedProjectIds, parentProjectId] : state.expandedProjectIds,
      fileNodesByProject: { ...state.fileNodesByProject, [componentId]: [] },
      changesByProject: { ...state.changesByProject, [componentId]: [] },
    };
  }

  /** v6.0(W-4/AW-AC-5): Repository Component 추가·제거. */
  addRepositoryComponent(state: WorkbenchState, projectId: string, name: string, path: string, kind: RepositoryComponent["kind"]): WorkbenchState {
    const normalizedPath = normalizeOpalProjectPath(path);
    const component: RepositoryComponent = { id: `repo_${Date.now()}`, projectId, name, path: normalizedPath, kind };
    return {
      ...state,
      repositoryComponents: [...state.repositoryComponents, component],
      projects: state.projects.map((project) => project.id === projectId ? { ...project, repositoryComponentIds: [...project.repositoryComponentIds, component.id] } : project),
      fileNodesByProject: { ...state.fileNodesByProject, [component.id]: [] },
      changesByProject: { ...state.changesByProject, [component.id]: [] },
    };
  }

  removeRepositoryComponent(state: WorkbenchState, projectId: string, componentId: string): WorkbenchState {
    const fileNodesByProject = { ...state.fileNodesByProject };
    const changesByProject = { ...state.changesByProject };
    delete fileNodesByProject[componentId];
    delete changesByProject[componentId];
    return {
      ...state,
      repositoryComponents: state.repositoryComponents.filter((component) => component.id !== componentId),
      projects: state.projects.map((project) => project.id === projectId ? { ...project, repositoryComponentIds: project.repositoryComponentIds.filter((id) => id !== componentId) } : project),
      activeRepositoryComponentId: state.activeRepositoryComponentId === componentId ? undefined : state.activeRepositoryComponentId,
      fileNodesByProject,
      changesByProject,
    };
  }

  /** v6.0(§4.6a/AW-AC-11): Project 트리 셰브론 펼침/접힘 토글. */
  toggleProjectExpanded(state: WorkbenchState, projectId: string): WorkbenchState {
    const expanded = state.expandedProjectIds.includes(projectId);
    return {
      ...state,
      expandedProjectIds: expanded ? state.expandedProjectIds.filter((id) => id !== projectId) : [...state.expandedProjectIds, projectId],
    };
  }

  /** v6.0(§4.5/AW-AC-5): Files/Changes가 대상으로 삼을 Repository Component를 전환한다. */
  setActiveRepositoryComponent(state: WorkbenchState, componentId: string | undefined): WorkbenchState {
    return { ...state, activeRepositoryComponentId: componentId };
  }

  /** v6.0(§4.7/AW-AC-7·8·9): 조율 타임라인에 이벤트를 기록한다. Agent Run 원본·도구 로그·검증 상세·승인 조작 필드는 두지 않는다(추가문서 113행). */
  recordCoordinationEvent(state: WorkbenchState, event: Omit<CoordinationEvent, "id" | "timestamp">): WorkbenchState {
    const entry: CoordinationEvent = { ...event, id: `coord_evt_${Date.now()}`, timestamp: new Date().toISOString() };
    return { ...state, coordinationEvents: [...state.coordinationEvents, entry] };
  }

  recordMainPmInstruction(state: WorkbenchState, taskId: string, body: string): WorkbenchState {
    const task = state.tasks.find((item) => item.id === taskId);
    const room = state.coordinationRooms.find((item) => item.taskId === taskId);
    if (!task || !room || !body.trim()) return state;
    const stamp = Date.now();
    const instruction: CoordinationEvent = {
      id: `coord_evt_${stamp}_instruction`,
      taskId,
      projectId: room.mainProjectId,
      pmAgentId: "user",
      type: "instruction",
      summary: `User → Main PM: "${body.trim()}"`,
      timestamp: new Date().toISOString(),
    };
    const reply: CoordinationEvent = {
      id: `coord_evt_${stamp}_reply`,
      taskId,
      projectId: room.mainProjectId,
      pmAgentId: room.mainPmAgentId,
      type: "status",
      summary: `Main PM: 요청을 접수했습니다. "${body.trim()}" 기준으로 Sub PM들과 조율합니다.`,
      timestamp: new Date(Date.now() + 1).toISOString(),
    };
    return { ...state, coordinationEvents: [...state.coordinationEvents, instruction, reply] };
  }

  private ensureCoordinationRoom(state: WorkbenchState, task: Task): { state: WorkbenchState; room: CoordinationRoom } {
    const existing = state.coordinationRooms.find((room) => room.taskId === task.id);
    if (existing) return { state, room: existing };
    const project = state.projects.find((item) => item.id === task.ownerProjectId);
    const room: CoordinationRoom = {
      id: `room_${task.id}`,
      taskId: task.id,
      mainProjectId: task.ownerProjectId,
      mainPmAgentId: project?.pmAgentId ?? task.leadAgentId,
      invitedProjectIds: [],
    };
    return { state: { ...state, coordinationRooms: [...state.coordinationRooms, room] }, room };
  }

  private addTabToFirstLeaf(state: WorkbenchState, taskId: string, tabId: string): WorkbenchState {
    const layout = this.layoutFor(state, taskId);
    const firstPaneId = collectLeaves(layout.root)[0]?.paneId;
    const addToLeaf = (node: SplitNode): SplitNode => {
      if (node.type === "leaf") {
        if (node.paneId !== firstPaneId) return node;
        return node.tabIds.includes(tabId) ? { ...node, activeTabId: tabId } : { ...node, tabIds: [...node.tabIds, tabId], activeTabId: tabId };
      }
      return { ...node, children: node.children.map(addToLeaf) };
    };
    return { ...state, surfaceLayoutByTask: { ...state.surfaceLayoutByTask, [taskId]: { taskId, root: addToLeaf(layout.root) } } };
  }

  private openWorkspaceInSplit(state: WorkbenchState, taskId: string, roomId: string, project: Project, mainPmAgentId: string): WorkbenchState {
    const existing = state.surfaceTabs.find((tab) => tab.taskId === taskId && tab.agentId === project.pmAgentId && tab.title.includes("Workspace"));
    if (existing) return this.addTabToFirstLeaf(state, taskId, existing.id);
    const stamp = Date.now();
    const projectName = project.name;
    const tabId = `surface_workspace_${project.id}_${stamp}`;
    const surface: SurfaceTab = {
      id: tabId,
      taskId,
      kind: "agent_cli",
      title: `${projectName} PM Workspace`,
      agentId: project.pmAgentId,
      parentAgentId: mainPmAgentId,
      roomId,
      readOnly: true,
      boundary: "simulated",
      closable: true,
      sessionStatus: "running",
      messages: [
        { author: "Main PM", body: `${projectName} PM을 Room에 초대하고 Workspace를 발동합니다. [Simulated]` },
        { author: `${projectName} PM`, body: "전용 Workspace에서 Worker 호출을 준비합니다. [Simulated]" },
      ],
    };
    const withSurface = { ...state, surfaceTabs: [...state.surfaceTabs, surface] };
    const layout = this.layoutFor(withSurface, taskId);
    const leaves = collectLeaves(layout.root);
    if (leaves.length > 1) {
      const targetPaneId = leaves[1].paneId;
      const addToSecondLeaf = (node: SplitNode): SplitNode => {
        if (node.type === "leaf") return node.paneId === targetPaneId ? { ...node, tabIds: [...node.tabIds, tabId], activeTabId: tabId } : node;
        return { ...node, children: node.children.map(addToSecondLeaf) };
      };
      return { ...withSurface, surfaceLayoutByTask: { ...withSurface.surfaceLayoutByTask, [taskId]: { taskId, root: addToSecondLeaf(layout.root) } } };
    }
    const firstLeaf = leaves[0] ?? { type: "leaf" as const, paneId: nextPaneId(), tabIds: [], activeTabId: "" };
    const nextRoot: SplitNode = {
      type: "split",
      direction: "horizontal",
      sizes: [58, 42],
      children: [
        firstLeaf,
        { type: "leaf", paneId: nextPaneId(), tabIds: [tabId], activeTabId: tabId },
      ],
    };
    return { ...withSurface, surfaceLayoutByTask: { ...withSurface.surfaceLayoutByTask, [taskId]: { taskId, root: nextRoot } } };
  }

  inviteSubPmToRoom(state: WorkbenchState, taskId: string, projectId: string): WorkbenchState {
    const task = state.tasks.find((item) => item.id === taskId);
    const project = state.projects.find((item) => item.id === projectId);
    if (!task || !project) return state;
    const ensured = this.ensureCoordinationRoom(state, task);
    const room = ensured.room;
    if (room.invitedProjectIds.includes(projectId)) return ensured.state;
    const stamp = Date.now();
    const rooms = ensured.state.coordinationRooms.map((item) => item.id === room.id ? { ...item, invitedProjectIds: [...item.invitedProjectIds, projectId] } : item);
    const request: CoordinationEvent = {
      id: `coord_evt_${stamp}_invite_request`,
      taskId,
      projectId: room.mainProjectId,
      pmAgentId: "user",
      type: "instruction",
      summary: `User → Main PM: "${project.name} PM 초대 요청"`,
      timestamp: new Date().toISOString(),
    };
    const invitation: CoordinationEvent = {
      id: `coord_evt_${stamp}_invitation`,
      taskId,
      projectId,
      pmAgentId: room.mainPmAgentId,
      type: "invitation",
      summary: `Main PM → ${project.name} PM: Room 초대 및 Workspace 발동`,
      timestamp: new Date(Date.now() + 1).toISOString(),
    };
    const next: WorkbenchState = {
      ...ensured.state,
      coordinationRooms: rooms,
      tasks: ensured.state.tasks.map((item) => item.id === taskId ? { ...item, participantProjectIds: [...new Set([...item.participantProjectIds, projectId])] } : item),
      coordinationEvents: [...ensured.state.coordinationEvents, request, invitation],
    };
    return this.openWorkspaceInSplit(next, taskId, room.id, project, room.mainPmAgentId);
  }

  spawnWorkerFromWorkspace(state: WorkbenchState, workspaceTabId: string): WorkbenchState {
    const workspace = state.surfaceTabs.find((tab) => tab.id === workspaceTabId);
    if (!workspace?.agentId) return state;
    const project = state.projects.find((item) => item.pmAgentId === workspace.agentId);
    if (!project) return state;
    const workerAgentId = `${project.name.toLowerCase()}-worker`;
    const worker = state.agents.find((agent) => agent.id === workerAgentId) ?? state.agents.find((agent) => agent.id.endsWith("-worker"));
    if (!worker) return state;
    const stamp = Date.now();
    const tabId = `surface_worker_${project.id}_${stamp}`;
    const workerSurface: SurfaceTab = {
      id: tabId,
      taskId: workspace.taskId,
      kind: "agent_cli",
      title: `${project.name} Worker Terminal`,
      agentId: worker.id,
      parentAgentId: workspace.agentId,
      roomId: workspace.roomId,
      readOnly: true,
      boundary: "simulated",
      closable: true,
      sessionStatus: "running",
      messages: [
        { author: `${project.name} PM`, body: `${project.name} PM → Worker: 실행 지시` },
        { author: worker.name, body: "작업 지시를 받고 실행 준비 중입니다. [Simulated]" },
      ],
    };
    const event: CoordinationEvent = {
      id: `coord_evt_${stamp}_worker`,
      taskId: workspace.taskId,
      projectId: project.id,
      pmAgentId: workspace.agentId,
      type: "worker_spawn",
      summary: `${project.name} PM → Worker: 실행 지시`,
      timestamp: new Date().toISOString(),
    };
    const next = { ...state, surfaceTabs: [...state.surfaceTabs, workerSurface], coordinationEvents: [...state.coordinationEvents, event] };
    return this.addTabToFirstLeaf(next, workspace.taskId, tabId);
  }

  /** v7.0(AW-AC-17): Main PM 배정을 하위 Project TASK·Environment·PM 실행 Surface와 한 번에 연결한다. */
  assignSubProjectTask(state: WorkbenchState, coordinationTaskId: string, targetProjectId: string, title: string, pilot: Pilot): WorkbenchState {
    const project = state.projects.find((item) => item.id === targetProjectId);
    if (!project || !title.trim()) return state;
    const stamp = Date.now();
    const taskId = `task_assignment_${stamp}`;
    const environmentId = `env_assignment_${stamp}`;
    const surfaceId = `surface_assignment_${stamp}`;
    const task: Task = {
      id: taskId, projectId: project.id, ownerProjectId: project.id, title: title.trim(), description: `Main PM 배정: ${title.trim()}`,
      status: "todo", leadAgentId: project.pmAgentId, environmentId, pilot, participantProjectIds: [project.id], coordinationTaskId,
    };
    const environment: Environment = { id: environmentId, taskId, worktreeLabel: `${project.name} mock worktree`, terminalSessionIds: [surfaceId], boundary: "not_connected" };
    const surface: SurfaceTab = { id: surfaceId, taskId, kind: "agent_cli", title: `${project.name} PM Agent Terminal`, agentId: project.pmAgentId, boundary: "simulated", closable: true, sessionStatus: "running", messages: [{ author: "Main PM", body: title.trim() }, { author: project.name + " PM", body: "업무를 확인하고 실행 Agent를 조율합니다. [Simulated]" }] };
    const event: CoordinationEvent = { id: `coord_evt_${stamp}`, taskId: coordinationTaskId, projectId: project.id, pmAgentId: project.pmAgentId, type: "assignment", summary: `Main PM → ${project.name} PM: "${title.trim()}" [${pilot}]`, timestamp: new Date().toISOString() };
    return {
      ...state,
      tasks: [...state.tasks, task],
      environments: [...state.environments, environment],
      surfaceTabs: [...state.surfaceTabs, surface],
      surfaceLayoutByTask: { ...state.surfaceLayoutByTask, [taskId]: { taskId, root: { type: "leaf", paneId: `pane_assignment_${stamp}`, tabIds: [surfaceId], activeTabId: surfaceId } } },
      coordinationEvents: [...state.coordinationEvents, event],
      expandedProjectIds: state.expandedProjectIds.includes(project.id) ? state.expandedProjectIds : [...state.expandedProjectIds, project.id],
    };
  }

  /** R-8: 목업 상태 초기화 — PersistedUI(opal.workbench.mock.v4)와 Settings(opal.workbench.settings.v1) 두 키를 모두 지우고 seed로 재부팅한다. */
  resetMockState(): { state: WorkbenchState } {
    localStorage.removeItem(WORKBENCH_STORAGE_KEY);
    localStorage.removeItem(SETTINGS_STORAGE_KEY);
    return { state: cloneSeed() };
  }

  switchProject(state: WorkbenchState, projectId: string): WorkbenchState {
    const firstTask = state.tasks.find((task) => task.projectId === projectId && task.status !== "done")
      ?? state.tasks.find((task) => task.projectId === projectId);
    return { ...state, activeProjectId: projectId, taskId: firstTask?.id, railTab: "files", activeRepositoryComponentId: undefined };
  }

  selectTask(state: WorkbenchState, taskId: string, agentId?: string): WorkbenchState {
    const task = state.tasks.find((item) => item.id === taskId);
    let next: WorkbenchState = { ...state, taskId, activeProjectId: task?.ownerProjectId ?? state.activeProjectId, activeRepositoryComponentId: undefined };
    if (agentId) {
      const surface = next.surfaceTabs.find((tab) => tab.taskId === taskId && tab.agentId === agentId);
      const pane = surface ? findPaneOfTab(this.layoutFor(next, taskId).root, surface.id) : undefined;
      if (surface && pane) next = this.focusSurfaceTab(next, taskId, pane.paneId, surface.id);
    }
    return next;
  }

  createTask(state: WorkbenchState, title: string, description: string, pilot: Pilot, leadAgentId: string): WorkbenchState {
    const envId = `env_${Date.now()}`;
    const task: Task = { id: `task_${Date.now()}`, projectId: state.activeProjectId, title, description, status: "todo", leadAgentId, environmentId: envId, ownerProjectId: state.activeProjectId, pilot, participantProjectIds: [state.activeProjectId] };
    const environment: Environment = { id: envId, taskId: task.id, worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" };
    let next: WorkbenchState = {
      ...state,
      tasks: [...state.tasks, task],
      environments: [...state.environments, environment],
      taskId: task.id,
    };
    const isComplexProject = state.projects.some((project) => project.parentProjectId === state.activeProjectId);
    if (isComplexProject && (pilot === "oppl" || pilot === "opsdd")) {
      const project = state.projects.find((item) => item.id === state.activeProjectId);
      const room: CoordinationRoom = { id: `room_${task.id}`, taskId: task.id, mainProjectId: state.activeProjectId, mainPmAgentId: project?.pmAgentId ?? leadAgentId, invitedProjectIds: [] };
      const surface: SurfaceTab = { id: `surface_coord_${task.id}`, taskId: task.id, kind: "coordination", title: "PM Coordination", roomId: room.id, boundary: "simulated", closable: true, sessionStatus: "running" };
      next = {
        ...next,
        coordinationRooms: [...next.coordinationRooms, room],
        surfaceTabs: [...next.surfaceTabs, surface],
        surfaceLayoutByTask: { ...next.surfaceLayoutByTask, [task.id]: { taskId: task.id, root: { type: "leaf", paneId: `pane_coord_${task.id}`, tabIds: [surface.id], activeTabId: surface.id } } },
      };
    }
    return next;
  }

  moveTask(state: WorkbenchState, taskId: string, status: TaskStatus): WorkbenchState {
    return { ...state, tasks: state.tasks.map((task) => task.id === taskId ? { ...task, status } : task) };
  }

  addAgent(state: WorkbenchState, name: string, role: string): WorkbenchState {
    const agent: AgentDefinition = { id: `agent_${Date.now()}`, name, role, source: "user", path: "user/agents/custom.md", status: "idle" };
    const binding: RuntimeBinding = { agentId: agent.id, runtime: "Codex ACP", model: "gpt-5.5", mode: "agentic", permission: "ask", boundary: "simulated" };
    return { ...state, agents: [...state.agents, agent], bindings: [...state.bindings, binding] };
  }

  updateBinding(state: WorkbenchState, binding: RuntimeBinding): WorkbenchState {
    return { ...state, bindings: state.bindings.map((item) => item.agentId === binding.agentId ? binding : item) };
  }

  setFailureMode(state: WorkbenchState, failureMode: boolean): WorkbenchState {
    return { ...state, failureMode };
  }

  private layoutFor(state: WorkbenchState, taskId: string): SurfaceLayout {
    return state.surfaceLayoutByTask[taskId] ?? { taskId, root: { type: "leaf", paneId: nextPaneId(), tabIds: [], activeTabId: "" } };
  }

  /** 새 Surface 탭을 만들어 활성 pane(없으면 새 leaf)에 추가한다. */
  openSurface(state: WorkbenchState, taskId: string, kind: SurfaceKind, title: string, agentId?: string): WorkbenchState {
    const now = new Date().toISOString();
    const tab: SurfaceTab = {
      id: `surface_${Date.now()}`,
      taskId,
      kind,
      title,
      agentId,
      boundary: kind === "mobile_emulator" ? "not_connected" : "simulated",
      closable: true,
      sessionStatus: "idle",
      messages: [],
      terminalEntries: kind === "terminal" ? [terminalEntry("system", "OPAL WorkStudio terminal ready", now, "/workspace")] : undefined,
    };
    const layout = this.layoutFor(state, taskId);
    const root = layout.root;
    const targetPaneId = collectLeaves(root)[0]?.paneId;
    const addToLeaf = (node: SplitNode): SplitNode => {
      if (node.type === "leaf") {
        if (node.paneId !== targetPaneId) return node;
        return { ...node, tabIds: [...node.tabIds, tab.id], activeTabId: tab.id };
      }
      return { ...node, children: node.children.map(addToLeaf) };
    };
    const nextRoot = addToLeaf(root);
    return {
      ...state,
      surfaceTabs: [...state.surfaceTabs, tab],
      surfaceLayoutByTask: { ...state.surfaceLayoutByTask, [taskId]: { taskId, root: nextRoot } },
    };
  }

  closeSurfaceTab(state: WorkbenchState, taskId: string, tabId: string): WorkbenchState {
    const layout = this.layoutFor(state, taskId);
    const removed = removeTabFromNode(layout.root, tabId);
    const pruned = pruneEmptyLeaves(removed) ?? { type: "leaf" as const, paneId: nextPaneId(), tabIds: [], activeTabId: "" };
    return {
      ...state,
      surfaceTabs: state.surfaceTabs.filter((tab) => tab.id !== tabId),
      surfaceLayoutByTask: { ...state.surfaceLayoutByTask, [taskId]: { taskId, root: pruned } },
    };
  }

  focusSurfaceTab(state: WorkbenchState, taskId: string, paneId: string, tabId: string): WorkbenchState {
    const layout = this.layoutFor(state, taskId);
    const setActive = (node: SplitNode): SplitNode => {
      if (node.type === "leaf") return node.paneId === paneId ? { ...node, activeTabId: tabId } : node;
      return { ...node, children: node.children.map(setActive) };
    };
    return { ...state, surfaceLayoutByTask: { ...state.surfaceLayoutByTask, [taskId]: { taskId, root: setActive(layout.root) } } };
  }

  /** 탭을 가장자리로 드래그해 드롭하면 해당 방향으로 pane을 split한다(AC-14). */
  splitSurface(state: WorkbenchState, taskId: string, sourceTabId: string, targetPaneId: string, direction: SplitDirection, edge: "start" | "end"): WorkbenchState {
    const layout = this.layoutFor(state, taskId);
    const removedFromSource = removeTabFromNode(layout.root, sourceTabId);
    const newPaneId = nextPaneId();
    const newLeaf: SplitNode = { type: "leaf", paneId: newPaneId, tabIds: [sourceTabId], activeTabId: sourceTabId };

    const splitAtTarget = (node: SplitNode): SplitNode => {
      if (node.type === "leaf") {
        if (node.paneId !== targetPaneId) return node;
        const children = edge === "start" ? [newLeaf, node] : [node, newLeaf];
        return { type: "split", direction, sizes: [50, 50], children };
      }
      return { ...node, children: node.children.map(splitAtTarget) };
    };
    const nextRoot = pruneEmptyLeaves(splitAtTarget(removedFromSource)) ?? newLeaf;
    return { ...state, surfaceLayoutByTask: { ...state.surfaceLayoutByTask, [taskId]: { taskId, root: nextRoot } } };
  }

  /**
   * 탭 바 드롭으로 탭을 이동/재배치한다(R-10, v5.0: `index` 인자 추가).
   * `sourcePaneId === targetPaneId`면 같은 pane 내 순서 변경으로 동작하고, 다르면 지정한 인덱스로 탭을 편입한다.
   * `index`를 생략하면 끝에 추가한다(하위 호환).
   */
  moveSurfaceTab(state: WorkbenchState, taskId: string, tabId: string, targetPaneId: string, index?: number): WorkbenchState {
    const layout = this.layoutFor(state, taskId);
    const removed = removeTabFromNode(layout.root, tabId);
    const addToTarget = (node: SplitNode): SplitNode => {
      if (node.type === "leaf") {
        if (node.paneId !== targetPaneId) return node;
        const tabIds = [...node.tabIds];
        const insertAt = index === undefined ? tabIds.length : Math.max(0, Math.min(index, tabIds.length));
        tabIds.splice(insertAt, 0, tabId);
        return { ...node, tabIds, activeTabId: tabId };
      }
      return { ...node, children: node.children.map(addToTarget) };
    };
    const nextRoot = pruneEmptyLeaves(addToTarget(removed)) ?? { type: "leaf" as const, paneId: nextPaneId(), tabIds: [tabId], activeTabId: tabId };
    return { ...state, surfaceLayoutByTask: { ...state.surfaceLayoutByTask, [taskId]: { taskId, root: nextRoot } } };
  }

  resizeSplit(state: WorkbenchState, taskId: string, paneId: string, sizes: number[]): WorkbenchState {
    const layout = this.layoutFor(state, taskId);
    const applySizes = (node: SplitNode): SplitNode => {
      if (node.type === "leaf") return node;
      const matchesChild = node.children.some((child) => (child.type === "leaf" ? child.paneId : "") === paneId);
      if (matchesChild) return { ...node, sizes };
      return { ...node, children: node.children.map(applySizes) };
    };
    return { ...state, surfaceLayoutByTask: { ...state.surfaceLayoutByTask, [taskId]: { taskId, root: applySizes(layout.root) } } };
  }

  /** wireframe.md v3.0 §7: mock timer가 sendSurfaceMessage 이후 sessionStatus를 running→completed(또는 failureMode에서 failed)로 진행시킨다. */
  sendSurfaceMessage(state: WorkbenchState, tabId: string, body: string): WorkbenchState {
    const now = new Date().toISOString();
    return {
      ...state,
      surfaceTabs: state.surfaceTabs.map((tab) => {
        if (tab.id !== tabId) return tab;
        const messages = [...(tab.messages ?? []), { author: "You", body }].slice(-50);
        const terminalEntries = tab.kind === "terminal"
          ? [
              ...(tab.terminalEntries ?? []),
              terminalEntry("input", body, now, "/workspace"),
              terminalEntry("output", mockTerminalOutput(body), new Date(Date.now() + 1).toISOString(), "/workspace"),
            ].slice(-100)
          : tab.terminalEntries;
        return { ...tab, sessionStatus: "running", messages, terminalEntries };
      }),
    };
  }

  tick(state: WorkbenchState): WorkbenchState {
    let changed = false;
    const surfaceTabs = state.surfaceTabs.map((tab) => {
      if (tab.sessionStatus !== "running") return tab;
      changed = true;
      if (state.failureMode) {
        return { ...tab, sessionStatus: "failed" as const, failureSummary: "mock 세션 실패 [Simulated]" };
      }
      const messages = [...(tab.messages ?? []), { author: tab.agentId ?? "system", body: "완료했습니다. [Simulated]" }].slice(-50);
      return { ...tab, sessionStatus: "completed" as const, messages };
    });
    if (!changed) return state;
    return { ...state, surfaceTabs };
  }

  createFileNode(state: WorkbenchState, projectId: string, parentPath: string | undefined, name: string, kind: "file" | "folder"): WorkbenchState {
    const path = parentPath ? `${parentPath}/${name}` : name;
    const node: FileNode = fileNode({ id: `file_${Date.now()}`, projectId, path, kind, gitStatus: "untracked", children: kind === "folder" ? [] : undefined });
    const insert = (nodes: FileNode[]): FileNode[] => {
      if (!parentPath) return [...nodes, node];
      return nodes.map((item) => {
        if (item.path === parentPath && item.kind === "folder") return { ...item, children: [...(item.children ?? []), node] };
        if (item.children) return { ...item, children: insert(item.children) };
        return item;
      });
    };
    const current = state.fileNodesByProject[projectId] ?? [];
    return { ...state, fileNodesByProject: { ...state.fileNodesByProject, [projectId]: insert(current) } };
  }

  deleteFileNode(state: WorkbenchState, projectId: string, nodeId: string): WorkbenchState {
    const remove = (nodes: FileNode[]): FileNode[] => nodes.filter((node) => node.id !== nodeId).map((node) => node.children ? { ...node, children: remove(node.children) } : node);
    const current = state.fileNodesByProject[projectId] ?? [];
    return { ...state, fileNodesByProject: { ...state.fileNodesByProject, [projectId]: remove(current) } };
  }

  stageMock(state: WorkbenchState, projectId: string, changeId: string, status: "staged" | "unstaged"): WorkbenchState {
    const changes = (state.changesByProject[projectId] ?? []).map((change) => change.id === changeId ? { ...change, status } : change);
    return { ...state, changesByProject: { ...state.changesByProject, [projectId]: changes } };
  }

  commitMock(state: WorkbenchState, projectId: string): WorkbenchState {
    const changes = (state.changesByProject[projectId] ?? []).filter((change) => change.status !== "staged");
    return { ...state, changesByProject: { ...state.changesByProject, [projectId]: changes } };
  }

  setRailTab(state: WorkbenchState, railTab: "files" | "changes"): WorkbenchState {
    return { ...state, railTab };
  }

  setRailWidth(state: WorkbenchState, railWidthPx: number): WorkbenchState {
    return { ...state, railWidthPx: Math.min(480, Math.max(168, railWidthPx)) };
  }

  setSidebarWidth(state: WorkbenchState, sidebarWidthPx: number): WorkbenchState {
    return { ...state, sidebarWidthPx: Math.min(360, Math.max(240, sidebarWidthPx)) };
  }

  toggleSidebarCollapsed(state: WorkbenchState, collapsed: boolean): WorkbenchState {
    return { ...state, sidebarCollapsed: collapsed };
  }

  toggleRailCollapsed(state: WorkbenchState, collapsed: boolean): WorkbenchState {
    return { ...state, railCollapsed: collapsed };
  }

  /** wireframe.md v4.0 §7: 폴더 펼침 상태는 FileNode가 아니라 PersistedUI.expandedFolderIds로만 관리한다(AC-10 확장). */
  toggleFolderExpanded(state: WorkbenchState, folderId: string): WorkbenchState {
    const expanded = state.expandedFolderIds.includes(folderId);
    return {
      ...state,
      expandedFolderIds: expanded
        ? state.expandedFolderIds.filter((id) => id !== folderId)
        : [...state.expandedFolderIds, folderId],
    };
  }

  openDiffSurface(state: WorkbenchState, taskId: string, change: ChangeEntry): WorkbenchState {
    const existing = state.surfaceTabs.find((tab) => tab.taskId === taskId && tab.kind === "diff" && tab.title === change.path);
    if (existing) return this.focusSurfaceTab(state, taskId, findPaneOfTab(this.layoutFor(state, taskId).root, existing.id)?.paneId ?? "", existing.id);
    const withTab = this.openSurface(state, taskId, "diff", change.path);
    const newTab = withTab.surfaceTabs[withTab.surfaceTabs.length - 1];
    return { ...withTab, surfaceTabs: withTab.surfaceTabs.map((tab) => tab.id === newTab.id ? { ...tab, messages: [{ author: "git", body: change.diffPreview }], sessionStatus: "completed" } : tab) };
  }
}

export function findPaneForTab(root: SplitNode, tabId: string) {
  return findPaneOfTab(root, tabId);
}

export function collectLeaves(node: SplitNode): (SplitNode & { type: "leaf" })[] {
  if (node.type === "leaf") return [node];
  return node.children.flatMap(collectLeaves);
}
