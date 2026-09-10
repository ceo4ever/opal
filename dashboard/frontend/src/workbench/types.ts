/**
 * @header {
 *   "module": "workbench-types",
 *   "layer": "domain",
 *   "domain": "workbench",
 *   "description": "Desktop Workbench 목업의 Project·Task·Run·검증 상태 계약",
 *   "exports": ["WorkbenchState", "Task", "Run", "ToolView", "TaskStatus"]
 * }
 */

export type ToolView = "conversation" | "runs" | "terminal" | "browser" | "files" | "diff" | "verification" | "result";
export type TaskStatus = "todo" | "in_progress" | "review" | "done";
export type RunStatus = "queued" | "running" | "waiting" | "completed" | "failed";

export interface Task {
  id: string;
  workstreamId: string;
  title: string;
  description: string;
  status: TaskStatus;
  leadAgentId: string;
}

export interface Message { id: string; taskId: string; author: string; body: string; }
export interface Run { id: string; taskId: string; agent: string; parentRunId?: string; status: RunStatus; stage: string; progress: number; }
export interface Activity { id: string; sequence: number; type: string; summary: string; }
export interface Binding { runtime: string; model: string; mode: string; permission: "ask" | "allow"; }

export interface WorkbenchState {
  version: 1;
  projectId: "project_opal";
  workstreamId: string;
  taskId?: string;
  activeToolView: ToolView;
  tasks: Task[];
  messages: Message[];
  runs: Run[];
  activities: Activity[];
  binding: Binding;
  verification: "failed" | "running" | "passed";
  approved: boolean;
}
