/**
 * @header {
 *   "module": "router",
 *   "layer": "config",
 *   "domain": "core",
 *   "description": "React Router 설정 — 9개 라우트(/ /projects /tasks /memory /doctor /brain /docs/skills /docs/skills/:skillId /settings)를 AppShell로 래핑. 절대경로 식별자는 searchParams 방식(?project= ?task_id=)으로 관리한다. /settings는 프로젝트별 환경 설정 화면(프라임 풀 토글·console.config·프로젝트 로컬 설정)이며, 대상 프로젝트는 contextProject(ui-store) 스위처와 연동된다.",
 *   "exports": ["router"],
 *   "depends": ["app-shell", "dashboard-page", "projects-page", "tasks-page", "memory-page", "doctor-page", "brain-page", "docs-catalog-page", "docs-detail-page", "settings-page"],
 *   "task": "061"
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
import { DocsCatalogPage } from "@/pages/docs/DocsCatalogPage";
import { DocsDetailPage } from "@/pages/docs/DocsDetailPage";

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
      { path: "docs/skills", element: <DocsCatalogPage /> },
      { path: "docs/skills/:skillId", element: <DocsDetailPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
]);
