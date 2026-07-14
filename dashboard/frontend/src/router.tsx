/**
 * @header {
 *   "module": "router",
 *   "layer": "config",
 *   "domain": "core",
 *   "description": "React Router 설정 — 7개 라우트(/ /projects /tasks /memory /doctor /brain /settings)를 AppShell로 래핑. 절대경로 식별자는 searchParams 방식(?project= ?task_id=) — path segment 라우트 제거(슬래시 포함 절대경로 매칭 실패 근본 수정). [T061] /settings 추가 — 프로젝트별 환경 설정 화면(프라임 풀 토글·console.config·프로젝트 로컬 설정), 대상 프로젝트는 contextProject(ui-store) 스위처 연동.",
 *   "exports": ["router"],
 *   "depends": ["app-shell", "dashboard-page", "projects-page", "tasks-page", "memory-page", "doctor-page", "brain-page", "settings-page"],
 *   "task": "061",
 *   "changelog": ["2026-07-14 T061 Step10: /settings 라우트 추가 (F-005)"]
 * }
 */

import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "@/components/app-shell/AppShell";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";
import { ProjectsPage } from "@/pages/projects/ProjectsPage";
import { TasksPage } from "@/pages/tasks/TasksPage";
import { MemoryPage } from "@/pages/memory/MemoryPage";
import { DoctorPage } from "@/pages/doctor/DoctorPage";
import { BrainPage } from "@/pages/brain/BrainPage";
import { SettingsPage } from "@/pages/settings/SettingsPage";

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
      { path: "brain", element: <BrainPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
]);
