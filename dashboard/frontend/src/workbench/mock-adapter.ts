/**
 * @header {
 *   "module": "mock-workbench-adapter",
 *   "layer": "adapter",
 *   "domain": "workbench",
 *   "description": "Workbench seed·mutation(Project 전환/TaskGroup/Task/Agent/Binding/동적 Surface 탭·split·탭 바 삽입 인덱스 이동/세션 상태 전이/Files·Changes/좌우 사이드바 접힘·파일 트리 펼침/Settings)과 localStorage(PersistedUI v4·Settings v1 별도 키) 복원을 단일 시뮬레이션 경계로 제공 (wireframe.md v5.0 §7)",
 *   "exports": ["MockWorkbenchAdapter", "WORKBENCH_STORAGE_KEY", "SETTINGS_STORAGE_KEY", "findPaneForTab", "collectLeaves"]
 * }
 */

import type {
  AgentDefinition,
  ChangeEntry,
  Environment,
  FileNode,
  PersistedUI,
  Project,
  RuntimeBinding,
  Settings,
  SplitDirection,
  SplitNode,
  SurfaceKind,
  SurfaceLayout,
  SurfaceTab,
  Task,
  TaskGroup,
  TaskStatus,
  WorkbenchState,
} from "./types";

export const WORKBENCH_STORAGE_KEY = "opal.workbench.mock.v4";
export const SETTINGS_STORAGE_KEY = "opal.workbench.settings.v1";

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
  { id: "project_opal", name: "OPAL", repositoryPath: "/workspace/ai-framework", taskGroupIds: ["group_development", "group_product"] },
  { id: "project_beta", name: "Beta Console", repositoryPath: "/workspace/beta-console", taskGroupIds: ["group_beta_dev"] },
];

const seedTaskGroups: TaskGroup[] = [
  { id: "group_development", projectId: "project_opal", name: "Development", taskIds: ["task_login_fix", "task_empty"] },
  { id: "group_product", projectId: "project_opal", name: "Product", taskIds: ["task_product"] },
  { id: "group_beta_dev", projectId: "project_beta", name: "Development", taskIds: ["task_beta_setup"] },
];

const seedEnvironments: Environment[] = [
  { id: "env_01", taskId: "task_login_fix", worktreeLabel: "mock worktree", terminalSessionIds: ["term_01"], browserSessionId: "browser_01", boundary: "not_connected" },
  { id: "env_02", taskId: "task_product", worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" },
  { id: "env_03", taskId: "task_empty", worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" },
  { id: "env_04", taskId: "task_beta_setup", worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" },
];

const seedTasks: Task[] = [
  { id: "task_login_fix", projectId: "project_opal", taskGroupId: "group_development", title: "로그인 오류 수정", description: "로그인 실패 상태를 재현하고 수정", status: "in_progress", leadAgentId: "opal-pm", environmentId: "env_01" },
  { id: "task_empty", projectId: "project_opal", taskGroupId: "group_development", title: "빈 Task 상태", description: "Empty state 검토", status: "todo", leadAgentId: "developer", environmentId: "env_03" },
  { id: "task_product", projectId: "project_opal", taskGroupId: "group_product", title: "Workbench UX 검토", description: "정보 구조 검토", status: "todo", leadAgentId: "opal-pm", environmentId: "env_02" },
  { id: "task_no_group", projectId: "project_opal", title: "그룹 미지정 Task", description: "TaskGroup 없이도 존재할 수 있는 Task", status: "todo", leadAgentId: "opal-pm", environmentId: "env_02" },
  { id: "task_beta_setup", projectId: "project_beta", taskGroupId: "group_beta_dev", title: "초기 설정", description: "Beta Console 초기 설정", status: "todo", leadAgentId: "opal-pm", environmentId: "env_04" },
];

const seedAgents: AgentDefinition[] = [
  { id: "opal-pm", name: "OPAL PM", role: "Product lead", source: "project", path: ".opal/AGENT.md", status: "ready" },
  { id: "developer", name: "Developer", role: "구현 담당", source: "framework", path: "framework/agents/developer.md", status: "idle" },
  { id: "reviewer", name: "Reviewer", role: "검토 담당", source: "framework", path: "framework/agents/reviewer.md", status: "idle" },
  { id: "ui-coach", name: "UI Coach", role: "UI 코칭", source: "user", path: "user/agents/ui-coach.md", status: "offline" },
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
  { id: "surface_dev_01", taskId: "task_login_fix", kind: "agent_cli", title: "Developer", agentId: "developer", boundary: "simulated", closable: true, sessionStatus: "running", messages: [
    { author: "You", body: "로그인 오류를 구현해줘" },
    { author: "Developer", body: "원인을 분석합니다. [Simulated]" },
  ] },
  { id: "surface_term_01", taskId: "task_login_fix", kind: "terminal", title: "Terminal", boundary: "simulated", closable: true, sessionStatus: "completed", messages: [
    { author: "system", body: "$ npm run dev" },
    { author: "system", body: "> ready [Simulated]" },
  ] },
  { id: "surface_browser_01", taskId: "task_login_fix", kind: "browser", title: "Browser", boundary: "simulated", closable: true, sessionStatus: "completed" },
];

const seedSurfaceLayoutByTask: Record<string, SurfaceLayout> = {
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
    {
      id: "file_src", projectId: "project_opal", path: "src", kind: "folder", gitStatus: "modified", children: [
        {
          id: "file_workbench", projectId: "project_opal", path: "src/workbench", kind: "folder", gitStatus: "modified", children: [
            { id: "file_types", projectId: "project_opal", path: "src/workbench/types.ts", kind: "file", gitStatus: "untracked" },
            { id: "file_adapter", projectId: "project_opal", path: "src/workbench/mock-adapter.ts", kind: "file", gitStatus: "modified" },
            { id: "file_app", projectId: "project_opal", path: "src/workbench/WorkbenchApp.tsx", kind: "file", gitStatus: "modified" },
          ],
        },
        {
          id: "file_components", projectId: "project_opal", path: "src/components", kind: "folder", gitStatus: "clean", children: [],
        },
      ],
    },
    { id: "file_node_modules", projectId: "project_opal", path: "node_modules", kind: "folder", gitStatus: "ignored", children: [] },
  ],
  project_beta: [
    { id: "file_beta_src", projectId: "project_beta", path: "src", kind: "folder", gitStatus: "clean", children: [] },
  ],
};

const seedChangesByProject: Record<string, ChangeEntry[]> = {
  project_opal: [
    { id: "change_1", projectId: "project_opal", path: "dashboard/frontend/src/workbench/WorkbenchApp.tsx", status: "staged", diffPreview: "- pinned tabs\n+ dynamic surfaces", linesAdded: 12, linesRemoved: 3 },
    { id: "change_2", projectId: "project_opal", path: "tasks/115-…/wireframe.md", status: "staged", diffPreview: "+ 좌우 사이드바 토글 설계", linesAdded: 80, linesRemoved: 6 },
    { id: "change_3", projectId: "project_opal", path: "docs/proposals/new-file.md", status: "unstaged", diffPreview: "+ splitSurface / moveSurfaceTab", linesAdded: 40, linesRemoved: 0 },
  ],
  project_beta: [],
};

function cloneSeed(): WorkbenchState {
  return {
    activeProjectId: "project_opal",
    taskGroupFilter: undefined,
    taskId: "task_login_fix",
    projects: JSON.parse(JSON.stringify(seedProjects)),
    taskGroups: JSON.parse(JSON.stringify(seedTaskGroups)),
    tasks: JSON.parse(JSON.stringify(seedTasks)),
    environments: JSON.parse(JSON.stringify(seedEnvironments)),
    agents: JSON.parse(JSON.stringify(seedAgents)),
    bindings: JSON.parse(JSON.stringify(seedBindings)),
    surfaceTabs: JSON.parse(JSON.stringify(seedSurfaceTabs)),
    surfaceLayoutByTask: JSON.parse(JSON.stringify(seedSurfaceLayoutByTask)),
    fileNodesByProject: JSON.parse(JSON.stringify(seedFileNodesByProject)),
    changesByProject: JSON.parse(JSON.stringify(seedChangesByProject)),
    railTab: "files",
    railWidthPx: 320,
    sidebarWidthPx: 280,
    sidebarCollapsed: false,
    railCollapsed: false,
    expandedFolderIds: ["file_src", "file_workbench"],
    failureMode: false,
    settings: JSON.parse(JSON.stringify(defaultSettings)),
  };
}

function persistedFromState(state: WorkbenchState): PersistedUI {
  return {
    version: 4,
    activeProjectId: state.activeProjectId,
    taskGroupFilter: state.taskGroupFilter,
    taskId: state.taskId,
    surfaceLayoutByTask: state.surfaceLayoutByTask,
    railTab: state.railTab,
    railWidthPx: state.railWidthPx,
    sidebarWidthPx: state.sidebarWidthPx,
    sidebarCollapsed: state.sidebarCollapsed,
    railCollapsed: state.railCollapsed,
    expandedFolderIds: state.expandedFolderIds,
  };
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
      const persisted = JSON.parse(raw) as Partial<PersistedUI>;
      if (
        persisted.version !== 4 ||
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
          taskGroupFilter: persisted.taskGroupFilter,
          taskId: persisted.taskId,
          surfaceLayoutByTask: persisted.surfaceLayoutByTask as WorkbenchState["surfaceLayoutByTask"],
          railTab: persisted.railTab === "changes" ? "changes" : "files",
          railWidthPx: typeof persisted.railWidthPx === "number" ? persisted.railWidthPx : base.railWidthPx,
          sidebarWidthPx: typeof persisted.sidebarWidthPx === "number" ? persisted.sidebarWidthPx : base.sidebarWidthPx,
          sidebarCollapsed: typeof persisted.sidebarCollapsed === "boolean" ? persisted.sidebarCollapsed : base.sidebarCollapsed,
          railCollapsed: typeof persisted.railCollapsed === "boolean" ? persisted.railCollapsed : base.railCollapsed,
          expandedFolderIds: Array.isArray(persisted.expandedFolderIds) ? persisted.expandedFolderIds : base.expandedFolderIds,
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
    return { ...state, projects: state.projects.map((project) => project.id === projectId ? { ...project, repositoryPath } : project) };
  }

  removeProject(state: WorkbenchState, projectId: string): WorkbenchState {
    const projects = state.projects.filter((project) => project.id !== projectId);
    const activeProjectId = state.activeProjectId === projectId ? (projects[0]?.id ?? "") : state.activeProjectId;
    return { ...state, projects, activeProjectId };
  }

  /** R-8: 목업 상태 초기화 — PersistedUI(opal.workbench.mock.v4)와 Settings(opal.workbench.settings.v1) 두 키를 모두 지우고 seed로 재부팅한다. */
  resetMockState(): { state: WorkbenchState } {
    localStorage.removeItem(WORKBENCH_STORAGE_KEY);
    localStorage.removeItem(SETTINGS_STORAGE_KEY);
    return { state: cloneSeed() };
  }

  switchProject(state: WorkbenchState, projectId: string): WorkbenchState {
    const firstTask = state.tasks.find((task) => task.projectId === projectId);
    return { ...state, activeProjectId: projectId, taskGroupFilter: undefined, taskId: firstTask?.id, railTab: "files" };
  }

  setTaskGroupFilter(state: WorkbenchState, taskGroupId: string | undefined): WorkbenchState {
    return { ...state, taskGroupFilter: taskGroupId };
  }

  createTaskGroup(state: WorkbenchState, name: string): WorkbenchState {
    const group: TaskGroup = { id: `group_${Date.now()}`, projectId: state.activeProjectId, name, taskIds: [] };
    return {
      ...state,
      taskGroups: [...state.taskGroups, group],
      projects: state.projects.map((project) => project.id === state.activeProjectId ? { ...project, taskGroupIds: [...project.taskGroupIds, group.id] } : project),
    };
  }

  selectTask(state: WorkbenchState, taskId: string): WorkbenchState {
    return { ...state, taskId };
  }

  createTask(state: WorkbenchState, title: string, description: string, taskGroupId: string | undefined, leadAgentId: string): WorkbenchState {
    const envId = `env_${Date.now()}`;
    const task: Task = { id: `task_${Date.now()}`, projectId: state.activeProjectId, taskGroupId, title, description, status: "todo", leadAgentId, environmentId: envId };
    const environment: Environment = { id: envId, taskId: task.id, worktreeLabel: "mock worktree", terminalSessionIds: [], boundary: "not_connected" };
    return {
      ...state,
      tasks: [...state.tasks, task],
      environments: [...state.environments, environment],
      taskGroups: taskGroupId ? state.taskGroups.map((group) => group.id === taskGroupId ? { ...group, taskIds: [...group.taskIds, task.id] } : group) : state.taskGroups,
      taskId: task.id,
    };
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
    return {
      ...state,
      surfaceTabs: state.surfaceTabs.map((tab) => {
        if (tab.id !== tabId) return tab;
        const messages = [...(tab.messages ?? []), { author: "You", body }].slice(-50);
        return { ...tab, sessionStatus: "running", messages };
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
    const node: FileNode = { id: `file_${Date.now()}`, projectId, path, kind, gitStatus: "untracked", children: kind === "folder" ? [] : undefined };
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
