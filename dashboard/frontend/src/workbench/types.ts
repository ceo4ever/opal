/**
 * @header {
 *   "module": "workbench-types",
 *   "layer": "domain",
 *   "domain": "workbench",
 *   "description": "Desktop Workbench 목업의 Project·TaskGroup·Task·Surface(동적 탭+split)·Agent·Files/Changes·Settings 계약 (wireframe.md v5.0 §7)",
 *   "exports": ["Boundary", "TaskStatus", "SplitDirection", "SurfaceKind", "SessionStatus", "GitFileStatus", "ThemeMode", "FontScale", "Project", "TaskGroup", "Task", "Environment", "AgentDefinition", "RuntimeBinding", "SurfaceTab", "SplitNode", "SurfaceLayout", "FileNode", "ChangeEntry", "Settings", "PersistedUI", "WorkbenchState"]
 * }
 */

export type Boundary = "actual" | "simulated" | "not_connected";
export type TaskStatus = "todo" | "in_progress" | "review" | "done";
export type SplitDirection = "horizontal" | "vertical";
export type SurfaceKind = "terminal" | "browser" | "markdown" | "mobile_emulator" | "agent_cli" | "diff";
export type SessionStatus = "idle" | "running" | "completed" | "failed"; // AC-16

export interface Project {
  id: string;
  name: string;
  repositoryPath: string;
  taskGroupIds: string[];
}

export interface TaskGroup {
  id: string;
  projectId: string;
  name: string;
  taskIds: string[];
}

export interface Task {
  id: string;
  projectId: string;
  taskGroupId?: string;
  title: string;
  description: string;
  status: TaskStatus;
  leadAgentId: string;
  environmentId: string;
}

export interface Environment {
  id: string;
  taskId: string;
  worktreeLabel: string;
  terminalSessionIds: string[];
  browserSessionId?: string;
  boundary: Boundary;
}

export interface AgentDefinition {
  id: string;
  name: string;
  role: string;
  source: "project" | "framework" | "user";
  path: string;
  status: "ready" | "idle" | "offline";
}

export interface RuntimeBinding {
  agentId: string;
  runtime: string;
  model: string;
  mode: string;
  permission: "ask" | "allow";
  boundary: "simulated";
}

export interface SurfaceTab {
  id: string;
  taskId: string;
  kind: SurfaceKind;
  title: string;
  agentId?: string;
  boundary: Boundary;
  closable: true;
  sessionStatus: SessionStatus;
  failureSummary?: string;
  messages?: { author: string; body: string }[];
}

export type SplitNode =
  | { type: "leaf"; paneId: string; tabIds: string[]; activeTabId: string }
  | { type: "split"; direction: SplitDirection; sizes: number[]; children: SplitNode[] };

export interface SurfaceLayout {
  taskId: string;
  root: SplitNode;
}

export type GitFileStatus = "modified" | "untracked" | "ignored" | "clean"; // a·R-6 — 트리 행 우측 배지(M/U/⊘, clean은 배지 없음)

export interface FileNode {
  id: string;
  projectId: string;
  path: string;
  kind: "file" | "folder";
  children?: FileNode[];
  gitStatus: GitFileStatus;
}

export interface ChangeEntry {
  id: string;
  projectId: string;
  path: string;
  status: "staged" | "unstaged";
  diffPreview: string;
  linesAdded: number;
  linesRemoved: number;
}

export interface PersistedUI {
  version: 4;
  activeProjectId: string;
  taskGroupFilter?: string;
  taskId?: string;
  surfaceLayoutByTask: Record<string, SurfaceLayout>;
  railTab: "files" | "changes";
  railWidthPx: number;
  sidebarWidthPx: number;
  sidebarCollapsed: boolean;
  railCollapsed: boolean;
  expandedFolderIds: string[];
}

// R-8/W-4: 화면 상태 스냅샷(PersistedUI)과 분리된 사용자 기본값. localStorage 키도 별도(opal.workbench.settings.v1).
export type ThemeMode = "system" | "light" | "dark";
export type FontScale = "sm" | "md" | "lg";

export interface Settings {
  version: 1;
  theme: ThemeMode;
  fontScale: FontScale;
  defaultNewSurfaceKind: SurfaceKind;
  sidebarCollapsedDefault: boolean;
  railCollapsedDefault: boolean;
  treeIndentPx: number; // 12~16
}

export interface WorkbenchState {
  activeProjectId: string;
  taskGroupFilter?: string;
  taskId?: string;
  projects: Project[];
  taskGroups: TaskGroup[];
  tasks: Task[];
  environments: Environment[];
  agents: AgentDefinition[];
  bindings: RuntimeBinding[];
  surfaceTabs: SurfaceTab[];
  surfaceLayoutByTask: Record<string, SurfaceLayout>;
  fileNodesByProject: Record<string, FileNode[]>;
  changesByProject: Record<string, ChangeEntry[]>;
  railTab: "files" | "changes";
  railWidthPx: number;
  sidebarWidthPx: number;
  sidebarCollapsed: boolean;
  railCollapsed: boolean;
  expandedFolderIds: string[];
  failureMode: boolean;
  settings: Settings;
}
