/**
 * @header {
 *   "module": "router",
 *   "layer": "config",
 *   "domain": "core",
 *   "description": "React Router 설정 — 5개 라우트(/ /projects /tasks /memory /doctor)를 AppShell로 래핑. 절대경로 식별자는 searchParams 방식(?project= ?task_id=) — path segment 라우트 제거(슬래시 포함 절대경로 매칭 실패 근본 수정)",
 *   "exports": ["router"],
 *   "depends": ["app-shell", "dashboard-page", "projects-page", "tasks-page", "memory-page", "doctor-page"]
 * }
 */

import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "@/components/app-shell/AppShell";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";
import { ProjectsPage } from "@/pages/projects/ProjectsPage";
import { TasksPage } from "@/pages/tasks/TasksPage";
import { MemoryPage } from "@/pages/memory/MemoryPage";
import { DoctorPage } from "@/pages/doctor/DoctorPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      // projects — 선택 상태는 ?project=<절대경로> searchParam으로 관리 (path segment 제거)
      { path: "projects", element: <ProjectsPage /> },
      // tasks — 태스크 선택은 Drawer 기반, project 필터는 ?project= searchParam
      { path: "tasks", element: <TasksPage /> },
      { path: "memory", element: <MemoryPage /> },
      { path: "doctor", element: <DoctorPage /> },
    ],
  },
]);
