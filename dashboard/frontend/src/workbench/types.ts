/**
 * @header {
 *   "module": "workbench-types",
 *   "layer": "domain",
 *   "domain": "workbench",
 *   "description": "Desktop Workbench v9 목업의 필터 없는 Project→진행 TASK→Agent 트리, TASK별 PM Coordination Room, PM/Worker Workspace, Repository Component, 동적 Surface·Files/Changes 계약",
 *   "exports": ["Boundary", "TaskStatus", "Pilot", "SplitDirection", "SurfaceKind", "SessionStatus", "GitFileStatus", "ThemeMode", "FontScale", "RepositoryComponentKind", "CoordinationEventType", "Project", "RepositoryComponent", "Task", "CoordinationEvent", "CoordinationRoom", "Environment", "AgentDefinition", "RuntimeBinding", "SurfaceTab", "SplitNode", "SurfaceLayout", "FileNode", "ChangeEntry", "Settings", "PersistedUI", "WorkbenchState"]
 * }
 */

export type Boundary = "actual" | "simulated" | "not_connected";
export type TaskStatus = "todo" | "in_progress" | "review" | "done";
export type Pilot = "opp" | "opd" | "opds" | "opdw" | "oppl" | "opsdd";
export type SplitDirection = "horizontal" | "vertical";
export type SurfaceKind = "coordination" | "terminal" | "browser" | "markdown" | "mobile_emulator" | "agent_cli" | "diff";
export type SessionStatus = "idle" | "running" | "completed" | "failed"; // AC-16

// v6.0(추가문서): Project는 재귀 트리 노드다. 단순/복합 유형은 parentProjectId·자식 존재 여부로 파생하며 별도 필드로 저장하지 않는다. 계층은 순환을 허용하지 않는다.
export interface Project {
  id: string;
  name: string;
  repositoryPath: string;
  parentProjectId?: string; // 신규(v6.0) — 없으면 최상위. 정본 부모 하나만 가짐(다중 부모 없음)
  pmAgentId: string; // 신규(v6.0) — Project당 PM Agent 1명
  repositoryComponentIds: string[]; // 신규(v6.0) — 관리 대상 Repository Component
}

export type RepositoryComponentKind = "repo" | "monorepo-area";

// 신규(v6.0): Project가 관리하는 실제 repo/monorepo 영역. 독립 PM·TASK·의사결정을 갖지 않는다.
export interface RepositoryComponent {
  id: string;
  projectId: string;
  name: string;
  path: string;
  kind: RepositoryComponentKind;
}

export interface Task {
  id: string;
  projectId: string;
  title: string;
  description: string;
  status: TaskStatus;
  leadAgentId: string;
  environmentId: string;
  ownerProjectId: string; // 신규(v6.0) — TASK를 소유하는 단일 Project
  pilot: Pilot;
  participantProjectIds: string[]; // 신규(v6.0) — 조율 TASK의 참여 Project(칩 표시), 일반 TASK는 [ownerProjectId] 1개
  coordinationTaskId?: string; // 신규(v6.0) — 이 TASK가 상위 조율 TASK에 속할 때 그 TASK id
}

export type CoordinationEventType = "instruction" | "invitation" | "assignment" | "status" | "coordination" | "blocker" | "decision" | "result" | "worker_spawn";

// 신규(v6.0): Project PM 수준 조율 이벤트. Agent Run 원본·도구 로그·검증 상세·승인 조작 필드는 두지 않는다(추가문서 113행).
export interface CoordinationEvent {
  id: string;
  taskId: string;
  projectId: string;
  pmAgentId: string;
  type: CoordinationEventType;
  summary: string;
  timestamp: string;
}

// 신규(v9.0): 조율 TASK마다 하나만 존재하는 PM Coordination Room. 사용자의 입력 수신자는 mainPmAgentId로 고정한다.
export interface CoordinationRoom {
  id: string;
  taskId: string;
  mainProjectId: string;
  mainPmAgentId: string;
  invitedProjectIds: string[];
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
  parentAgentId?: string; // 신규(v9.0) — Sub PM이 호출한 Worker Terminal의 부모 PM Agent
  roomId?: string; // 신규(v9.0) — PM Coordination Room 문맥의 관찰 Surface
  readOnly?: boolean; // 신규(v9.0) — PM/Worker Agent Terminal은 사용자 관찰 전용
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
  version: 5;
  activeProjectId: string;
  taskId?: string;
  surfaceLayoutByTask: Record<string, SurfaceLayout>;
  railTab: "files" | "changes";
  railWidthPx: number;
  sidebarWidthPx: number;
  sidebarCollapsed: boolean;
  railCollapsed: boolean;
  expandedFolderIds: string[];
  expandedProjectIds: string[]; // 신규(v6.0) — Project 트리 셰브론 펼침 상태 복원(AW-AC-11), Project.id 집합
  activeRepositoryComponentId?: string; // 신규(v6.0) — Repository Component가 여럿인 Project의 현재 Files/Changes 대상(AW-AC-5)
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
  taskId?: string;
  projects: Project[];
  repositoryComponents: RepositoryComponent[];
  tasks: Task[];
  coordinationEvents: CoordinationEvent[];
  coordinationRooms: CoordinationRoom[];
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
  expandedProjectIds: string[];
  activeRepositoryComponentId?: string;
  failureMode: boolean;
  settings: Settings;
}
