/**
 * @header {
 *   "module": "app-shell",
 *   "layer": "component",
 *   "domain": "core",
 *   "description": "OPAL Console 글로벌 레이아웃 셸 — shadcn sidebar 기반 좌측 7개 네비 + 프로젝트 스위처 + 상단바(검색·테마토글·새로고침·연결상태·설정). [T061] NAV_ITEMS에 '설정' 추가 + TopBar 설정 버튼을 /settings NavLink로 연결(기존 no-op 제거). [T063 R-8] 프로젝트 스위처가 ui-store brainDirty(브레인 화면 turns.length>0)를 확인해, dirty 상태에서 다른 프로젝트로 전환 시 AlertDialog로 확인 후 진행(취소 시 잔류) — 브레인 화면이 아니면(brainDirty=false) 기존과 동일하게 즉시 전환.",
 *   "exports": ["AppShell"],
 *   "depends": ["ui-store", "api-client", "sidebar", "badge", "dropdown-menu", "tooltip", "alert-dialog"],
 *   "task": "063",
 *   "changelog": [
 *     "2026-07-14 T061 Step10: NAV_ITEMS '설정' 추가 + TopBar 설정 버튼 /settings 연결 (F-005)",
 *     "2026-07-15 T063 R-8: ProjectSwitcher에 brainDirty 가드 추가 — dirty 시 AlertDialog 확인 후 setContextProject 진행"
 *   ]
 * }
 */

import React, { useState } from "react";
import { Outlet, NavLink, useSearchParams } from "react-router-dom";
import {
  LayoutDashboard,
  FolderKanban,
  CheckSquare,
  Brain,
  Activity,
  MessageCircleQuestion,
  RefreshCw,
  Settings,
  Search,
  Sun,
  Moon,
  Monitor,
  ChevronDown,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarInset,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useUiStore, type Theme } from "@/store/ui-store";
import { apiClient } from "@/lib/api";

/** 3경로 공통 이탈 확인 문구 (R-8) — BrainPage 이탈 가드와 동일 문구 유지 */
const BRAIN_LEAVE_GUARD_TITLE = "화면을 나가면 이 대화 세션이 사라집니다";
const BRAIN_LEAVE_GUARD_DESCRIPTION = "나가시겠어요?";

/* ------------------------------------------------------------------ */
/* 상수                                                                  */
/* ------------------------------------------------------------------ */

/** 6개 네비 항목 */
interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "대시보드", icon: LayoutDashboard, end: true },
  { to: "/projects", label: "프로젝트", icon: FolderKanban },
  { to: "/tasks", label: "태스크", icon: CheckSquare },
  { to: "/memory", label: "메모리", icon: Brain },
  { to: "/doctor", label: "환경", icon: Activity },
  { to: "/brain", label: "프로젝트 브레인", icon: MessageCircleQuestion },
  { to: "/settings", label: "설정", icon: Settings },
];

const THEME_OPTIONS: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: "dark", label: "다크", icon: Moon },
  { value: "light", label: "라이트", icon: Sun },
  { value: "system", label: "시스템", icon: Monitor },
];

/* ------------------------------------------------------------------ */
/* ProjectSwitcher                                                       */
/* ------------------------------------------------------------------ */

interface ProjectInfo {
  name: string;
  path: string;
  is_opal: boolean;
}

function ProjectSwitcher() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { contextProject, setContextProject, brainDirty } = useUiStore();
  // 브레인 화면에서 turns>0 상태로 전환 시도 시 확인 대기 중인 전환 대상 (R-8 ③).
  // undefined = 확인 대기 없음. path 자체가 null(전체 프로젝트)일 수 있어 별도 sentinel로 구분.
  const [pendingSwitch, setPendingSwitch] = useState<{ path: string | null } | undefined>(undefined);

  const { data: projects } = useQuery<ProjectInfo[]>({
    queryKey: ["projects"],
    queryFn: () => apiClient<ProjectInfo[]>("/api/projects"),
    retry: false,
  });

  const selectedPath = contextProject ?? searchParams.get("project") ?? null;
  const selectedProject = projects?.find((p) => p.path === selectedPath);
  const displayName = selectedProject?.name ?? "전체 프로젝트";

  const applySelect = (path: string | null) => {
    setContextProject(path);
    if (path) {
      setSearchParams({ project: path });
    } else {
      setSearchParams({});
    }
  };

  const handleSelect = (path: string | null) => {
    if (path === selectedPath) return; // 동일 선택 — 전환 아님, 가드 불필요
    if (brainDirty) {
      setPendingSwitch({ path });
      return;
    }
    applySelect(path);
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-primary text-primary-foreground text-xs font-bold">
              O
            </span>
            <span className="truncate flex-1 text-left">{displayName}</span>
            <ChevronDown className="ml-auto h-4 w-4 shrink-0 opacity-50" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-56" align="start">
          <DropdownMenuItem onClick={() => handleSelect(null)}>
            <span className="font-medium">★ 전체 프로젝트</span>
          </DropdownMenuItem>
          {projects
            ?.filter((p) => p.is_opal)
            .map((p) => (
              <DropdownMenuItem key={p.path} onClick={() => handleSelect(p.path)}>
                {p.name}
              </DropdownMenuItem>
            ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* 이탈 확인 다이얼로그 (R-8 ③) — 브레인 화면 dirty(turns>0) 중 프로젝트 전환 시도 시 노출 */}
      <AlertDialog
        open={pendingSwitch !== undefined}
        onOpenChange={(open) => {
          if (!open) setPendingSwitch(undefined);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{BRAIN_LEAVE_GUARD_TITLE}</AlertDialogTitle>
            <AlertDialogDescription>{BRAIN_LEAVE_GUARD_DESCRIPTION}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setPendingSwitch(undefined)}>취소</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (pendingSwitch !== undefined) applySelect(pendingSwitch.path);
                setPendingSwitch(undefined);
              }}
            >
              나가기
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

/* ------------------------------------------------------------------ */
/* ConnectionStatus                                                      */
/* ------------------------------------------------------------------ */

function ConnectionStatus() {
  const { data, isError } = useQuery<{ status: string; version: string }>({
    queryKey: ["health"],
    queryFn: () => apiClient<{ status: string; version: string }>("/health"),
    refetchInterval: 15_000,
    retry: false,
  });

  const connected = !isError && !!data;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge
          variant={connected ? "default" : "destructive"}
          className={cn(
            "gap-1 text-xs cursor-default",
            connected
              ? "bg-status-done/20 text-status-done border-status-done/30"
              : "bg-status-blocked/20 text-status-blocked border-status-blocked/30",
          )}
        >
          {connected ? (
            <Wifi className="h-3 w-3" />
          ) : (
            <WifiOff className="h-3 w-3" />
          )}
          {connected ? "연결됨" : "오프라인"}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        {connected
          ? `API 연결 정상 (v${data?.version ?? "?"})`
          : "API 서버에 연결할 수 없습니다. opal-cli console start를 실행하세요."}
      </TooltipContent>
    </Tooltip>
  );
}

/* ------------------------------------------------------------------ */
/* TopBar                                                                */
/* ------------------------------------------------------------------ */

function TopBar() {
  const { theme, setTheme } = useUiStore();

  const currentThemeIcon = THEME_OPTIONS.find((t) => t.value === theme)?.icon ?? Sun;
  const ThemeIcon = currentThemeIcon;

  return (
    <header className="flex h-12 shrink-0 items-center gap-2 border-b bg-background px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="h-5" />

      {/* 검색 트리거 (⌘K) */}
      <button
        className="flex items-center gap-2 rounded-md border border-input bg-muted/50 px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
        onClick={() => {
          /* Phase 3에서 command 팔레트 구현 */
        }}
      >
        <Search className="h-3.5 w-3.5" />
        <span>검색...</span>
        <kbd className="ml-auto pointer-events-none hidden select-none rounded border border-input bg-muted px-1.5 py-0.5 font-mono text-[10px] font-medium sm:inline-flex">
          ⌘K
        </kbd>
      </button>

      <div className="ml-auto flex items-center gap-2">
        <ConnectionStatus />

        {/* 새로고침 */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => window.location.reload()}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>새로고침</TooltipContent>
        </Tooltip>

        {/* 테마 토글 */}
        <DropdownMenu>
          <Tooltip>
            <TooltipTrigger asChild>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <ThemeIcon className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
            </TooltipTrigger>
            <TooltipContent>테마 전환</TooltipContent>
          </Tooltip>
          <DropdownMenuContent align="end">
            {THEME_OPTIONS.map(({ value, label, icon: Icon }) => (
              <DropdownMenuItem
                key={value}
                onClick={() => setTheme(value)}
                className={cn(theme === value && "bg-accent")}
              >
                <Icon className="mr-2 h-4 w-4" />
                {label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* 설정 — /settings 이동 (T061) */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8" asChild>
              <NavLink to="/settings">
                <Settings className="h-4 w-4" />
              </NavLink>
            </Button>
          </TooltipTrigger>
          <TooltipContent>설정</TooltipContent>
        </Tooltip>
      </div>
    </header>
  );
}

/* ------------------------------------------------------------------ */
/* AppSidebar                                                            */
/* ------------------------------------------------------------------ */

function AppSidebar() {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <ProjectSwitcher />
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>네비게이션</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
                <SidebarMenuItem key={to}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={to}
                      end={end}
                      className={({ isActive }) =>
                        cn(
                          "flex items-center gap-2 w-full",
                          isActive && "font-medium text-primary",
                        )
                      }
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span>{label}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div className="px-2 py-1">
          <p className="text-[10px] text-muted-foreground">OPAL Console v0.1</p>
        </div>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}

/* ------------------------------------------------------------------ */
/* AppShell (루트 레이아웃)                                               */
/* ------------------------------------------------------------------ */

export function AppShell() {
  return (
    <TooltipProvider>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <TopBar />
          <main className="flex flex-1 flex-col overflow-auto">
            <Outlet />
          </main>
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  );
}
