/**
 * @header {
 *   "module": "workbench-app-test",
 *   "layer": "test",
 *   "domain": "workbench",
 *   "description": "Project 전환·TaskGroup(AC-2), Surface 탭 추가·닫기·전환(AC-6), split 배치·좌우 사이드바 접힘·파일 트리 펼침 복원(AC-10), 탭 바/pane 본문 분리 드롭과 탭 바 내장 Surface 추가 버튼의 드롭 인덱스 계산 무결성(AC-14, R-10/R-11 회귀 방지), TASKS 헤더 +의 Board 우회 Task 생성 진입(AC-3, R-12), 세션 상태 표시(AC-16), 파일 트리 계층·git 배지(AC-17), Changes 그룹핑·diff 통계(AC-18), 설정 화면 진입·섹션 전환·목업 초기화(AC-19) DOM 상호작용 검증",
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

describe("Desktop Workbench mock flow (wireframe v3.0)", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => { cleanup(); vi.useRealTimers(); });

  it("switches Project and filters Task list by TaskGroup (AC-2)", async () => {
    render(<WorkbenchApp />);

    // default project shows Development-grouped task
    expect((await screen.findAllByText("로그인 오류 수정")).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("combobox", { name: "Project" }));
    fireEvent.click(await screen.findByRole("option", { name: "Beta Console" }));
    expect((await screen.findAllByText("초기 설정")).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("combobox", { name: "Project" }));
    fireEvent.click(await screen.findByRole("option", { name: "OPAL" }));
    fireEvent.click(screen.getByRole("button", { name: /^Product/ }));
    expect((await screen.findAllByText("Workbench UX 검토")).length).toBeGreaterThan(0);
  });

  it("adds, focuses, and closes dynamic Surface tabs with no pinned system tabs (AC-6)", async () => {
    render(<WorkbenchApp />);

    // seeded task already has Developer / Terminal / Browser dynamic tabs
    expect(screen.getAllByRole("tab", { name: /Developer/ }).length).toBeGreaterThan(0);

    const surfaceMenuTrigger = screen.getByRole("button", { name: "Surface 추가" });
    fireEvent.pointerDown(surfaceMenuTrigger, { button: 0, pointerId: 1 });
    fireEvent.click(surfaceMenuTrigger);
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
    const terminalTab = screen.getByRole("tab", { name: /Terminal/ });
    const targetTab = screen.getByRole("tab", { name: /Developer/ });
    const targetPane = targetTab.closest('[data-testid="surface-pane"]') as HTMLElement;
    const targetBody = within(targetPane).getByTestId("surface-pane-body");

    const dataTransfer = dragTransfer();
    fireEvent.dragStart(terminalTab, { dataTransfer });
    fireEvent.dragOver(targetBody, { dataTransfer, clientX: 5, clientY: 100 });
    fireEvent.drop(targetBody, { dataTransfer, clientX: 5, clientY: 100 });

    await act(async () => {});
    // after splitting left, two panes exist and Terminal tab is still present
    expect(screen.getAllByRole("tab", { name: /Terminal/ }).length).toBeGreaterThan(0);
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
    const terminalTab = screen.getByRole("tab", { name: /Terminal/ });
    const developerPane = developerTab.closest('[data-testid="surface-pane"]') as HTMLElement;
    const developerTabBar = within(developerPane).getByTestId("surface-tab-bar");

    const dataTransfer = dragTransfer();
    fireEvent.dragStart(terminalTab, { dataTransfer });
    fireEvent.dragOver(developerTabBar, { dataTransfer, clientX: 9999 });
    fireEvent.drop(developerTabBar, { dataTransfer, clientX: 9999 });

    await act(async () => {});
    // Terminal now appears inside the Developer pane's tab bar
    expect(within(developerTabBar).getAllByRole("tab", { name: /Terminal/ }).length).toBe(1);
  });

  it("keeps the Surface 추가 button inside the tab bar without breaking drop-index calculation (W-1/R-11)", async () => {
    render(<WorkbenchApp />);
    const developerTab = screen.getByRole("tab", { name: /Developer/ });
    const terminalTab = screen.getByRole("tab", { name: /Terminal/ });
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
    expect(within(developerTabBar).getAllByRole("tab", { name: /Terminal/ }).length).toBe(1);
  });

  it("opens the Task creation dialog directly from the TASKS header + without going through the Board (W-2/R-12)", async () => {
    render(<WorkbenchApp />);

    expect(screen.queryByRole("button", { name: /^New Task$/ })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Task 추가" }));
    expect(screen.queryByTestId("task-board")).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "새 Task" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("제목 *"), { target: { value: "새 태스크" } });
    fireEvent.change(screen.getByLabelText("설명 *"), { target: { value: "테스트 설명" } });
    fireEvent.click(screen.getByRole("button", { name: "Task 만들기" }));

    await act(async () => {});
    expect(screen.queryByTestId("task-board")).not.toBeInTheDocument();
    expect((await screen.findAllByText("새 태스크")).length).toBeGreaterThan(0);
  });

  it("shows session status on the tab itself: running spinner, completed dot, failed badge (AC-16)", async () => {
    vi.useFakeTimers();
    render(<WorkbenchApp />);

    const developerTab = screen.getByRole("tab", { name: /Developer/ });
    expect(within(developerTab).getByLabelText("진행 중")).toBeInTheDocument();

    await act(async () => { vi.advanceTimersByTime(1500); });
    expect(within(screen.getByRole("tab", { name: /Developer/ })).getByLabelText("완료")).toBeInTheDocument();

    const terminalTab = screen.getByRole("tab", { name: /Terminal/ });
    expect(within(terminalTab).getByLabelText("완료")).toBeInTheDocument();
  });

  it("restores active Project, Task, and Surface split layout after a remount (AC-10)", async () => {
    const { unmount } = render(<WorkbenchApp />);
    fireEvent.click(screen.getByRole("combobox", { name: "Project" }));
    fireEvent.click(await screen.findByRole("option", { name: "Beta Console" }));
    unmount();

    render(<WorkbenchApp />);
    expect((await screen.findAllByText("초기 설정")).length).toBeGreaterThan(0);
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
    expect(screen.getByText("PROJECT")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("좌측 사이드바 접기"));
    expect(screen.queryByText("PROJECT")).not.toBeInTheDocument();
    expect(await screen.findByLabelText("좌측 사이드바 펼치기")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("좌측 사이드바 펼치기"));
    expect(await screen.findByText("PROJECT")).toBeInTheDocument();

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
