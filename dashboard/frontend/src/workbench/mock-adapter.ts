/**
 * @header {
 *   "module": "mock-workbench-adapter",
 *   "layer": "adapter",
 *   "domain": "workbench",
 *   "description": "Workbench seed·mutation·localStorage 복원을 단일 시뮬레이션 경계로 제공",
 *   "exports": ["MockWorkbenchAdapter", "WORKBENCH_STORAGE_KEY"]
 * }
 */

import type { Binding, TaskStatus, ToolView, WorkbenchState } from "./types";

export const WORKBENCH_STORAGE_KEY = "opal.workbench.mock.v1";

const seed: WorkbenchState = {
  version: 1,
  projectId: "project_opal",
  workstreamId: "development",
  taskId: "task_login_fix",
  activeToolView: "conversation",
  tasks: [
    { id: "task_product", workstreamId: "product", title: "Workbench UX 검토", description: "정보 구조 검토", status: "todo", leadAgentId: "opal-pm" },
    { id: "task_login_fix", workstreamId: "development", title: "로그인 오류 수정", description: "로그인 실패 상태를 재현하고 수정", status: "in_progress", leadAgentId: "opal-pm" },
    { id: "task_empty", workstreamId: "development", title: "빈 Task 상태", description: "Empty state 검토", status: "todo", leadAgentId: "developer" },
    { id: "task_review", workstreamId: "review", title: "결과 승인 검토", description: "검증 결과 승인", status: "review", leadAgentId: "reviewer" },
  ],
  messages: [
    { id: "msg_1", taskId: "task_login_fix", author: "OPAL PM", body: "요청을 분석하고 Developer에게 위임했습니다. [Simulated]" },
    { id: "msg_2", taskId: "task_login_fix", author: "Developer", body: "로그인 오류 재현 후 UI 상태를 수정 중입니다. [Simulated]" },
  ],
  runs: [
    { id: "run_01", taskId: "task_login_fix", agent: "OPAL PM", status: "completed", stage: "delegated", progress: 100 },
    { id: "run_02", taskId: "task_login_fix", agent: "Developer", parentRunId: "run_01", status: "running", stage: "implementation", progress: 60 },
  ],
  activities: [
    { id: "evt_1", sequence: 1, type: "message", summary: "사용자 요청 수신" },
    { id: "evt_2", sequence: 2, type: "delegation", summary: "PM → Developer 위임" },
    { id: "evt_3", sequence: 3, type: "run", summary: "Developer Run 실행 중" },
    { id: "evt_4", sequence: 4, type: "tool", summary: "Browser action 재생" },
    { id: "evt_5", sequence: 5, type: "file", summary: "3개 파일 변경" },
    { id: "evt_6", sequence: 6, type: "verification", summary: "2 PASS · 1 FAIL" },
    { id: "evt_7", sequence: 7, type: "result", summary: "승인 대기" },
  ],
  binding: { runtime: "Codex ACP", model: "gpt-5.5", mode: "agentic", permission: "ask" },
  verification: "failed",
  approved: false,
};

function cloneSeed(): WorkbenchState { return JSON.parse(JSON.stringify(seed)) as WorkbenchState; }

export class MockWorkbenchAdapter {
  load(): WorkbenchState {
    try {
      const raw = localStorage.getItem(WORKBENCH_STORAGE_KEY);
      if (!raw) return cloneSeed();
      const value = JSON.parse(raw) as WorkbenchState;
      return value.version === 1 ? value : cloneSeed();
    } catch { return cloneSeed(); }
  }

  save(state: WorkbenchState) { localStorage.setItem(WORKBENCH_STORAGE_KEY, JSON.stringify(state)); }
  select(state: WorkbenchState, patch: Partial<Pick<WorkbenchState, "workstreamId" | "taskId" | "activeToolView">>) { return { ...state, ...patch }; }
  createTask(state: WorkbenchState, title: string, description: string, workstreamId: string) {
    const task = { id: `task_${Date.now()}`, workstreamId, title, description, status: "todo" as const, leadAgentId: "opal-pm" };
    return { ...state, tasks: [...state.tasks, task], taskId: task.id, workstreamId, activities: [...state.activities, { id: `evt_${Date.now()}`, sequence: state.activities.length + 1, type: "task", summary: `Task 생성: ${title}` }] };
  }
  moveTask(state: WorkbenchState, taskId: string, status: TaskStatus) { return { ...state, tasks: state.tasks.map((task) => task.id === taskId ? { ...task, status } : task) }; }
  sendMention(state: WorkbenchState, body: string) {
    const taskId = state.taskId ?? "task_login_fix";
    const stamp = Date.now();
    const direct = body.toLowerCase().includes("@developer");
    const parent = direct ? undefined : `run_pm_${stamp}`;
    const newRuns = direct
      ? [{ id: `run_dev_${stamp}`, taskId, agent: "Developer", status: "running" as const, stage: "implementation", progress: 35 }]
      : [
          { id: parent!, taskId, agent: "OPAL PM", status: "completed" as const, stage: "delegated", progress: 100 },
          { id: `run_dev_${stamp}`, taskId, agent: "Developer", parentRunId: parent, status: "running" as const, stage: "implementation", progress: 35 },
        ];
    return {
      ...state,
      messages: [...state.messages, { id: `msg_user_${stamp}`, taskId, author: "You", body }, { id: `msg_agent_${stamp}`, taskId, author: direct ? "Developer" : "OPAL PM", body: direct ? "독립 Run을 시작했습니다. [Simulated]" : "요청을 정리해 Developer에게 위임했습니다. [Simulated]" }],
      runs: [...state.runs, ...newRuns],
      activities: [...state.activities, { id: `evt_${stamp}`, sequence: state.activities.length + 1, type: direct ? "run" : "delegation", summary: direct ? "Developer 직접 Run 시작" : "PM → Developer 위임" }],
    };
  }
  updateBinding(state: WorkbenchState, binding: Binding) { return { ...state, binding, activities: [...state.activities, { id: `evt_${Date.now()}`, sequence: state.activities.length + 1, type: "agent", summary: "Agent binding 업데이트" }] }; }
  setTool(state: WorkbenchState, activeToolView: ToolView) { return { ...state, activeToolView }; }
  rerunVerification(state: WorkbenchState) { return { ...state, verification: "passed" as const, activities: [...state.activities, { id: `evt_${Date.now()}`, sequence: state.activities.length + 1, type: "verification", summary: "재검증 3 PASS [Simulated]" }] }; }
  approveResult(state: WorkbenchState) { const taskId = state.taskId; return { ...state, approved: true, tasks: state.tasks.map((task) => task.id === taskId ? { ...task, status: "done" as const } : task), activities: [...state.activities, { id: `evt_${Date.now()}`, sequence: state.activities.length + 1, type: "result", summary: "Result 승인" }] }; }
}
