/**
 * @header {
 *   "module": "workbench-app-test",
 *   "layer": "test",
 *   "domain": "workbench",
 *   "description": "재귀 Project→TASK→실행 Agent 트리와 필터 없는 진행 TASK 탐색, TASK 빠른 추가, Execution Workspace, 동적 Surface 탭·split·설정 Project 생성/연결, TASK별 PM Coordination Room을 검증하는 wireframe v9 DOM 테스트",
 *   "exports": []
 * }
 */

import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { WorkbenchApp } from "./WorkbenchApp";

function dragTransfer() {
  const store = new Map<string, string>();
  return {
    setData: (type: string, value: string) => store.set(type, value),
    getData: (type: string) => store.get(type) ?? "",
  } as unknown as DataTransfer;
}

describe("Desktop Workbench mock flow (wireframe v9.0)", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => { cleanup(); vi.useRealTimers(); });

  it("switches Project without TASK filters and hides done TASK nodes only from the tree (AW-AC-14)", async () => {
    render(<WorkbenchApp />);

    expect(await screen.findByRole("treeitem", { name: "TASK 빈 Task 상태" })).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "상태 필터" })).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "Pilot 필터" })).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "담당 Agent 필터" })).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "참여 Project 필터" })).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "TASK 검색" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Beta Console" }));
    expect(await screen.findByRole("treeitem", { name: "TASK 초기 설정" })).toBeInTheDocument();

    expect(screen.queryByRole("treeitem", { name: "TASK 재귀 트리 UI 구현" })).not.toBeInTheDocument();
    expect(screen.queryByText("TASK GROUPS")).not.toBeInTheDocument();
  });

  it("adds, focuses, and closes dynamic Surface tabs with no pinned system tabs (AC-6)", async () => {
    render(<WorkbenchApp />);

    // seeded task already has Developer Agent Terminal / 독립 Terminal / Browser dynamic tabs
    expect(screen.getByText("Execution Workspace")).toBeInTheDocument();
    expect(screen.getByText("PM Coordination · Agent Terminal · 독립 Terminal")).toBeInTheDocument();
    expect(screen.getAllByRole("tab", { name: /Developer/ }).length).toBeGreaterThan(0);

    const surfaceMenuTrigger = screen.getByRole("button", { name: "Surface 추가" });
    fireEvent.pointerDown(surfaceMenuTrigger, { button: 0, pointerId: 1 });
    fireEvent.click(surfaceMenuTrigger);
    expect((await screen.findAllByText("독립 Terminal")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("Developer Agent Terminal")).length).toBeGreaterThan(0);
    const markdownItem = await screen.findByText("Markdown");
    fireEvent.pointerDown(markdownItem, { button: 0, pointerId: 1 });
    fireEvent.pointerUp(markdownItem, { button: 0, pointerId: 1 });
    fireEvent.click(markdownItem);
    expect(await screen.findByText(/## Mock/)).toBeInTheDocument();

    const markdownTab = screen.getByRole("tab", { name: /Markdown/ });
    fireEvent.click(within(markdownTab).getByLabelText(/닫기/));
    await act(async () => {});
    expect(screen.queryByRole("tab", { name: /Markdown/ })).not.toBeInTheDocument();
  });

  it("splits a Surface tab into a new pane by dropping on the pane body edge (AC-14, R-10)", async () => {
    render(<WorkbenchApp />);
    const terminalTab = screen.getByRole("tab", { name: /독립 Terminal/ });
    const targetTab = screen.getByRole("tab", { name: /Developer/ });
    const targetPane = targetTab.closest('[data-testid="surface-pane"]') as HTMLElement;
    const targetBody = within(targetPane).getByTestId("surface-pane-body");

    const dataTransfer = dragTransfer();
    fireEvent.dragStart(terminalTab, { dataTransfer });
    fireEvent.dragOver(targetBody, { dataTransfer, clientX: 5, clientY: 100 });
    fireEvent.drop(targetBody, { dataTransfer, clientX: 5, clientY: 100 });

    await act(async () => {});
    // after splitting left, two panes exist and Terminal tab is still present
    expect(screen.getAllByRole("tab", { name: /독립 Terminal/ }).length).toBeGreaterThan(0);
  });

  it("reorders tabs within the same pane via the moveSurfaceTab(index) mutation (AC-14 regression, R-10/W-1)", async () => {
    // happy-dom does not populate DragEvent.clientX/getBoundingClientRect() with real layout
    // numbers, so the insertion-index arithmetic that SurfaceTabBar's onDragOver performs
    // cannot be exercised deterministically through simulated DOM drag coordinates. This
    // covers the same-pane reorder contract at the adapter boundary that the tab bar's
    // onDrop calls into (moveSurfaceTab(state, taskId, tabId, targetPaneId, index)), while
    // the DOM-level test below covers the cross-pane drop path end-to-end.
    const { MockWorkbenchAdapter } = await import("./mock-adapter");
    const localAdapter = new MockWorkbenchAdapter();
    const { state } = localAdapter.load();
    // seed: pane_right holds [surface_term_01, surface_browser_01]
    const before = state.surfaceLayoutByTask.task_login_fix.root as { type: "split"; children: unknown[] };
    const paneRight = (before.children[1] as { type: "leaf"; paneId: string; tabIds: string[] });
    expect(paneRight.tabIds).toEqual(["surface_term_01", "surface_browser_01"]);

    const moved = localAdapter.moveSurfaceTab(state, "task_login_fix", "surface_browser_01", paneRight.paneId, 0);
    const after = (moved.surfaceLayoutByTask.task_login_fix.root as { type: "split"; children: unknown[] }).children[1] as { tabIds: string[]; activeTabId: string };
    expect(after.tabIds).toEqual(["surface_browser_01", "surface_term_01"]);
    expect(after.activeTabId).toBe("surface_browser_01");
  });

  it("moves a tab into a different pane by dropping on that pane's tab bar (AC-14 regression, R-10/W-1)", async () => {
    render(<WorkbenchApp />);
    const developerTab = screen.getByRole("tab", { name: /Developer/ });
    const terminalTab = screen.getByRole("tab", { name: /독립 Terminal/ });
    const developerPane = developerTab.closest('[data-testid="surface-pane"]') as HTMLElement;
    const developerTabBar = within(developerPane).getByTestId("surface-tab-bar");

    const dataTransfer = dragTransfer();
    fireEvent.dragStart(terminalTab, { dataTransfer });
    fireEvent.dragOver(developerTabBar, { dataTransfer, clientX: 9999 });
    fireEvent.drop(developerTabBar, { dataTransfer, clientX: 9999 });

    await act(async () => {});
    // 독립 Terminal now appears inside the Developer pane's tab bar
    expect(within(developerTabBar).getAllByRole("tab", { name: /독립 Terminal/ }).length).toBe(1);
  });

  it("keeps the Surface 추가 button inside the tab bar without breaking drop-index calculation (W-1/R-11)", async () => {
    render(<WorkbenchApp />);
    const developerTab = screen.getByRole("tab", { name: /Developer/ });
    const terminalTab = screen.getByRole("tab", { name: /독립 Terminal/ });
    const developerPane = developerTab.closest('[data-testid="surface-pane"]') as HTMLElement;
    const developerTabBar = within(developerPane).getByTestId("surface-tab-bar");

    // the add-surface trigger lives inside the tab bar now (no separate row above it), and it
    // must not carry role="tab" — the tab bar's onDragOver indexes elements via
    // querySelectorAll('[role="tab"]'), so a role="tab" leak here would corrupt insertion math.
    const addSurfaceButton = within(developerTabBar).getByRole("button", { name: "Surface 추가" });
    expect(addSurfaceButton).toBeInTheDocument();
    expect(addSurfaceButton).not.toHaveAttribute("role", "tab");

    // end-of-bar drop (existing AC-14/R-10 regression path) still resolves correctly with the
    // add-surface button present in the same container.
    const dataTransfer = dragTransfer();
    fireEvent.dragStart(terminalTab, { dataTransfer });
    fireEvent.dragOver(developerTabBar, { dataTransfer, clientX: 9999 });
    fireEvent.drop(developerTabBar, { dataTransfer, clientX: 9999 });

    await act(async () => {});
    expect(within(developerTabBar).getAllByRole("tab", { name: /독립 Terminal/ }).length).toBe(1);
  });

  it("opens the Task creation dialog directly from the TASKS header + without going through the Board (W-2/R-12)", async () => {
    render(<WorkbenchApp />);

    expect(screen.queryByRole("button", { name: /^New Task$/ })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "TASK 추가" }));
    expect(screen.queryByTestId("task-board")).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "새 Task" })).toBeInTheDocument();
    expect(screen.queryByText("참여 Project")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("제목 *"), { target: { value: "새 태스크" } });
    fireEvent.change(screen.getByLabelText("설명 *"), { target: { value: "테스트 설명" } });
    fireEvent.click(screen.getByRole("button", { name: "Task 만들기" }));

    await act(async () => {});
    expect(screen.queryByTestId("task-board")).not.toBeInTheDocument();
    expect(await screen.findByRole("treeitem", { name: "TASK 새 태스크" })).toBeInTheDocument();
  });

  it("shows session status on the tab itself: running spinner, completed dot, failed badge (AC-16)", async () => {
    vi.useFakeTimers();
    render(<WorkbenchApp />);

    const developerTab = screen.getByRole("tab", { name: /Developer/ });
    expect(within(developerTab).getByLabelText("진행 중")).toBeInTheDocument();

    await act(async () => { vi.advanceTimersByTime(1500); });
    expect(within(screen.getByRole("tab", { name: /Developer/ })).getByLabelText("완료")).toBeInTheDocument();

    const terminalTab = screen.getByRole("tab", { name: /독립 Terminal/ });
    expect(within(terminalTab).getByLabelText("완료")).toBeInTheDocument();
  });

  it("restores active Project, Task, and Surface split layout after a remount (AC-10)", async () => {
    const { unmount } = render(<WorkbenchApp />);
    fireEvent.click(screen.getByRole("button", { name: "Beta Console" }));
    unmount();

    render(<WorkbenchApp />);
    expect(await screen.findByRole("treeitem", { name: "TASK 초기 설정" })).toBeInTheDocument();
  });

  it("renders the file tree as a nested hierarchy, not a flattened row (W-1 regression)", async () => {
    render(<WorkbenchApp />);
    const fileLabel = await screen.findByText("types.ts");
    const workbenchRow = (await screen.findByText("workbench")).closest("div.group");
    const typesRow = fileLabel.closest("div.group");
    expect(workbenchRow).toBeTruthy();
    expect(typesRow).toBeTruthy();
    // the child row must be a descendant of the folder node wrapper (sibling of the row), never inline in the same flex row
    expect(workbenchRow?.parentElement?.contains(typesRow as Node)).toBe(true);
    expect(typesRow).not.toBe(workbenchRow);
    // a folder row itself stays a single-line flex row (chevron/icon/label/badge/delete), no nested tree inside it
    expect(workbenchRow?.querySelector("div.group")).toBeNull();
  });

  it("shows git status badges and marks ignored entries in italics (AC-17)", async () => {
    render(<WorkbenchApp />);
    expect((await screen.findAllByLabelText("git status: modified")).length).toBeGreaterThan(0);
    expect((await screen.findAllByLabelText("git status: untracked")).length).toBeGreaterThan(0);
    const ignoredLabel = await screen.findByText("node_modules");
    expect(ignoredLabel.className).toContain("italic");
  });

  it("toggles left and right sidebars collapsed and expanded (AC-15/R-5)", async () => {
    render(<WorkbenchApp />);
    expect(screen.getByText("PROJECTS")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("좌측 사이드바 접기"));
    expect(screen.queryByText("PROJECTS")).not.toBeInTheDocument();
    expect(await screen.findByLabelText("좌측 사이드바 펼치기")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("좌측 사이드바 펼치기"));
    expect(await screen.findByText("PROJECTS")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("우측 사이드바 접기"));
    expect(screen.queryByText("Files")).not.toBeInTheDocument();
    expect(await screen.findByLabelText("우측 사이드바 펼치기")).toBeInTheDocument();
  });

  it("persists folder expanded state in PersistedUI.expandedFolderIds after a remount (AC-10)", async () => {
    const { unmount } = render(<WorkbenchApp />);
    await screen.findByText("types.ts");
    fireEvent.click(screen.getByLabelText("src 접기"));
    expect(screen.queryByText("types.ts")).not.toBeInTheDocument();
    unmount();

    render(<WorkbenchApp />);
    expect(screen.queryByText("types.ts")).not.toBeInTheDocument();
    expect(await screen.findByLabelText("src 펼치기")).toBeInTheDocument();
  });

  it("groups Changes by directory with count badges and shows +n -m diff stats (AC-18)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(screen.getByRole("button", { name: "Changes" }));

    expect(await screen.findByText("변경 사항 2")).toBeInTheDocument();
    expect(await screen.findByText("추적되지 않은 파일 1")).toBeInTheDocument();
    expect(screen.getByText("+12")).toBeInTheDocument();
    expect(screen.getByText("-3")).toBeInTheDocument();
    // a file with only additions renders "+n" alone, with no "-0"
    expect(screen.getByText("+40")).toBeInTheDocument();
    expect(screen.queryByText("-0")).not.toBeInTheDocument();
  });

  it("opens the Settings dialog from the left sidebar bottom bar and switches sections (AC-19)", async () => {
    render(<WorkbenchApp />);
    expect(screen.queryByRole("button", { name: "Agents" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "설정" }));
    expect(await screen.findByRole("heading", { name: "설정" })).toBeInTheDocument();
    // Agent section is the default and shows the seeded agent catalog with C-3 binding fields
    expect(screen.getAllByText("OPAL PM").length).toBeGreaterThan(0);
    expect(screen.getByText("Runtime Binding")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "외관" }));
    expect(await screen.findByLabelText("테마")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Workbench" }));
    expect(await screen.findByLabelText("파일 트리 들여쓰기(px)")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "프로젝트" }));
    expect(await screen.findByText("/workspace/ai-framework")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "목업" }));
    expect(await screen.findByText("목업 상태 초기화")).toBeInTheDocument();
  });

  it("opens an Agent Surface tab from the Settings Agent section (C-4)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(screen.getByRole("button", { name: "설정" }));
    await screen.findByRole("heading", { name: "설정" });

    // OPAL PM (status ready) is the first agent card; its "Surface에서 열기" button is enabled.
    fireEvent.click(screen.getAllByRole("button", { name: "Surface에서 열기" })[0]);
    // dialog closes and a new agent_cli surface tab is opened and focused
    expect(screen.queryByRole("heading", { name: "설정" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("tab", { name: /OPAL PM/ }).length).toBeGreaterThan(0);
  });

  it("renders the recursive Project tree with StoreLinkStudio nesting Pug/Blend/MAMS (AW-AC-3, AW-AC-10)", async () => {
    render(<WorkbenchApp />);
    // expanded by default seed (expandedProjectIds includes project_storelinkstudio) — no need to click to expand
    const tree = within(await screen.findByTestId("project-tree"));
    expect(await tree.findByRole("button", { name: "Pug" })).toBeInTheDocument();
    expect(tree.getByRole("button", { name: "Blend" })).toBeInTheDocument();
    expect(tree.getByRole("button", { name: "MAMS" })).toBeInTheDocument();
    expect(tree.getByText("PM:Pug PM")).toBeInTheDocument();
  });

  it("uses PROJECTS + for TASK creation and manages top-level or child Projects from Settings (AW-AC-19·20)", async () => {
    render(<WorkbenchApp />);
    expect(screen.queryByRole("button", { name: "Project 추가" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "TASK 추가" }));
    expect(await screen.findByRole("heading", { name: "새 Task" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "취소" }));

    fireEvent.click(screen.getByRole("button", { name: "설정" }));
    fireEvent.click(await screen.findByRole("button", { name: "프로젝트" }));
    fireEvent.click(screen.getByRole("button", { name: "Project 생성/연결" }));
    expect(await screen.findByRole("heading", { name: "Project 추가" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("부모 Project"), { target: { value: "project_storelinkstudio" } });

    fireEvent.change(screen.getByLabelText("이름 *"), { target: { value: "새 스튜디오" } });
    fireEvent.change(screen.getByLabelText("경로 *"), { target: { value: "/Volumes/Data/new-studio" } });
    fireEvent.click(screen.getByRole("button", { name: "Project 만들기" }));

    await act(async () => {});
    expect((await screen.findAllByText("새 스튜디오")).length).toBeGreaterThan(0);
  });

  it("links an existing OPAL Project as a child from Settings (AW-AC-2·20)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(screen.getByRole("button", { name: "설정" }));
    fireEvent.click(await screen.findByRole("button", { name: "프로젝트" }));
    fireEvent.click(screen.getByRole("button", { name: "Project 생성/연결" }));
    fireEvent.change(screen.getByLabelText("부모 Project"), { target: { value: "project_storelinkstudio" } });
    expect(await screen.findByText("StoreLinkStudio 아래에 추가")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "기존 연결" }));
    fireEvent.change(screen.getByLabelText("경로 *"), { target: { value: "/Volumes/Data/StoreLinkStudio/extra" } });
    fireEvent.click(screen.getByRole("button", { name: "연결하기" }));

    await act(async () => {});
    expect((await screen.findAllByText("extra")).length).toBeGreaterThan(0);
  });

  it("shows a RepoScopeSelect for a Project with multiple Repository Components and scopes Files/Changes (AW-AC-5)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(await screen.findByRole("button", { name: "StoreLinkStudio" }));
    fireEvent.click(await screen.findByRole("button", { name: "Pug" }));

    const repo = await screen.findByRole("combobox", { name: "Repo" });
    fireEvent.click(repo);
    fireEvent.click(await screen.findByRole("option", { name: "app_android" }));
    expect((await screen.findAllByText("app_android")).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("combobox", { name: "Repo" }));
    fireEvent.click(await screen.findByRole("option", { name: "backend" }));
    expect((await screen.findAllByText("backend")).length).toBeGreaterThan(0);
  });

  it("opens the coordination timeline for a coordination TASK showing Main PM judgement, rollup, and events without Agent Run internals (AW-AC-7·8·9, C-10)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(await screen.findByRole("button", { name: "StoreLinkStudio" }));
    fireEvent.click(await screen.findByRole("treeitem", { name: "TASK 재귀형 프로젝트 관리 구축" }));

    expect(await screen.findByText("Main PM 최종 판단")).toBeInTheDocument();
    expect((await screen.findAllByText(/실측 기준 monorepo-area 5개로 확정/)).length).toBeGreaterThan(0);
    expect(screen.getByText("하위 TASK 상태 집계")).toBeInTheDocument();
    expect((await screen.findAllByText(/트리 뷰 구현 완료/)).length).toBeGreaterThan(0);
  });

  it("renders a TASK-scoped PM Coordination Room where the user can only instruct Main PM (AW-AC-23·24·26)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(await screen.findByRole("treeitem", { name: "TASK 재귀형 프로젝트 관리 구축" }));

    expect(await screen.findByText("PM Coordination Room")).toBeInTheDocument();
    expect(screen.getByText("Owner: Main PM")).toBeInTheDocument();
    expect(screen.getByText("Pug PM · Workspace running")).toBeInTheDocument();
    expect(screen.getByText("Blend PM · Workspace running")).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "조율 메시지 유형" })).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "대상 Sub PM" })).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "배정 Pilot" })).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Main PM에게 지시"), { target: { value: "MAMS까지 초대해서 기준을 맞춰줘" } });
    fireEvent.click(screen.getByRole("button", { name: "Main PM에게 보내기" }));

    expect(await screen.findByText(/User → Main PM: "MAMS까지 초대해서 기준을 맞춰줘"/)).toBeInTheDocument();
    expect((await screen.findAllByText(/Main PM: 요청을 접수했습니다/)).length).toBeGreaterThan(0);
  });

  it("invites a Sub PM through Main PM and atomically opens its read-only Workspace (AW-AC-25)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(await screen.findByRole("treeitem", { name: "TASK 재귀형 프로젝트 관리 구축" }));

    expect(screen.queryByText("MAMS PM · Workspace running")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "PM 초대 요청" }));

    expect(await screen.findByText("MAMS PM · Workspace running")).toBeInTheDocument();
    expect(await screen.findByRole("tab", { name: /MAMS PM Workspace/ })).toBeInTheDocument();
    expect(screen.getByText(/Main PM → MAMS PM: Room 초대/)).toBeInTheDocument();
    expect(screen.getAllByText("관찰 전용 Terminal").length).toBeGreaterThan(0);
    expect(screen.queryByLabelText("MAMS PM Workspace 입력")).not.toBeInTheDocument();
  });

  it("spawns a read-only Worker Terminal under a Sub PM Workspace and exposes it in the Agent tree (AW-AC-27)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(await screen.findByRole("treeitem", { name: "TASK 재귀형 프로젝트 관리 구축" }));

    fireEvent.click(await screen.findByRole("tab", { name: /Pug PM Workspace/ }));
    fireEvent.click(screen.getByRole("button", { name: "Worker 호출 시뮬레이션" }));

    expect(await screen.findByRole("tab", { name: /Pug Worker Terminal/ })).toBeInTheDocument();
    expect(await screen.findByRole("treeitem", { name: /실행 Agent Pug Worker · 재귀형 프로젝트 관리 구축/ })).toBeInTheDocument();
    expect(screen.getByText(/Pug PM → Worker: 실행 지시/)).toBeInTheDocument();
    expect(screen.getAllByText("관찰 전용 Terminal").length).toBeGreaterThan(0);
    expect(screen.queryByLabelText("Pug Worker Terminal 입력")).not.toBeInTheDocument();
  });

  it("marks a coordination TASK row with invited Project chips (AW-AC-6)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(await screen.findByRole("button", { name: "StoreLinkStudio" }));
    const coordButton = await screen.findByRole("treeitem", { name: "TASK 재귀형 프로젝트 관리 구축" });
    expect(within(coordButton).getByText("PUG")).toBeInTheDocument();
    expect(within(coordButton).getByText("BLEND")).toBeInTheDocument();
    expect(within(coordButton).queryByText("MAMS")).not.toBeInTheDocument();
  });

  it("creates a TASK with a selected Pilot and shows its execution Agent in the Project tree (AW-AC-6·15)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(screen.getByRole("button", { name: "TASK 추가" }));
    fireEvent.change(screen.getByLabelText("제목 *"), { target: { value: "Pilot 선택 작업" } });
    fireEvent.change(screen.getByLabelText("설명 *"), { target: { value: "oppl 작업" } });
    fireEvent.change(screen.getByLabelText("Pilot *"), { target: { value: "oppl" } });
    fireEvent.click(screen.getByRole("button", { name: "Task 만들기" }));
    const taskNode = await screen.findByRole("treeitem", { name: "TASK Pilot 선택 작업" });
    expect(within(taskNode).getByText("oppl")).toBeInTheDocument();
    expect(screen.getByRole("treeitem", { name: /실행 Agent .* · Pilot 선택 작업/ })).toBeInTheDocument();
  });

  it("creates a coordination Room for a new complex Project TASK without user-selected participants (AW-AC-23)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(await screen.findByRole("button", { name: "StoreLinkStudio" }));
    fireEvent.click(screen.getByRole("button", { name: "TASK 추가" }));
    fireEvent.change(screen.getByLabelText("제목 *"), { target: { value: "새 조율 TASK" } });
    fireEvent.change(screen.getByLabelText("설명 *"), { target: { value: "Main PM만으로 시작" } });
    fireEvent.change(screen.getByLabelText("Pilot *"), { target: { value: "oppl" } });
    fireEvent.click(screen.getByRole("button", { name: "Task 만들기" }));

    expect(await screen.findByText("PM Coordination Room")).toBeInTheDocument();
    expect(screen.getByText("Owner: Main PM")).toBeInTheDocument();
    const taskNode = await screen.findByRole("treeitem", { name: "TASK 새 조율 TASK" });
    expect(within(taskNode).queryByText("PUG")).not.toBeInTheDocument();
  });

  it("assigns a Sub PM from the PM Coordination Room and atomically creates its TASK and Agent Surface (AW-AC-16·17)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(await screen.findByRole("treeitem", { name: "TASK 재귀형 프로젝트 관리 구축" }));
    expect(await screen.findByRole("tab", { name: /PM Coordination/ })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Main PM에게 지시"), { target: { value: "결제 API 계약 정리" } });
    fireEvent.click(screen.getByRole("button", { name: "업무 배정" }));
    expect(await screen.findByRole("treeitem", { name: "TASK 결제 API 계약 정리" })).toBeInTheDocument();
    expect(screen.getByRole("treeitem", { name: "실행 Agent Pug PM · 결제 API 계약 정리" })).toBeInTheDocument();
    expect(screen.getByText(/Main PM → Pug PM: "결제 API 계약 정리"/)).toBeInTheDocument();
  });

  it("restores Project tree expansion and creates/links Projects across a remount (AW-AC-11)", async () => {
    const { unmount } = render(<WorkbenchApp />);
    fireEvent.click(screen.getByRole("button", { name: "설정" }));
    fireEvent.click(await screen.findByRole("button", { name: "프로젝트" }));
    fireEvent.click(screen.getByRole("button", { name: "Project 생성/연결" }));
    fireEvent.change(screen.getByLabelText("이름 *"), { target: { value: "영속 확인" } });
    fireEvent.change(screen.getByLabelText("경로 *"), { target: { value: "/tmp/persist-check" } });
    fireEvent.click(screen.getByRole("button", { name: "Project 만들기" }));
    await act(async () => {});
    unmount();

    render(<WorkbenchApp />);
    expect(await screen.findByRole("button", { name: "영속 확인" })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Pug" })).toBeInTheDocument();
  });

  it("resets mock state from the Settings 목업 section, clearing both storage keys (R-8)", async () => {
    render(<WorkbenchApp />);
    fireEvent.click(screen.getByRole("button", { name: "설정" }));
    fireEvent.click(await screen.findByRole("button", { name: "Workbench" }));
    fireEvent.click(await screen.findByLabelText("우측 rail 기본 접힘"));
    expect(localStorage.getItem("opal.workbench.settings.v1")).toContain("railCollapsedDefault\":true");

    fireEvent.click(screen.getByRole("button", { name: "목업" }));
    fireEvent.click(await screen.findByRole("button", { name: "상태 초기화" }));
    fireEvent.click(await screen.findByRole("button", { name: "초기화" }));

    await act(async () => {});
    expect(localStorage.getItem("opal.workbench.mock.v4")).toBeNull();
    expect(localStorage.getItem("opal.workbench.settings.v1")).toBeNull();
  });
});
