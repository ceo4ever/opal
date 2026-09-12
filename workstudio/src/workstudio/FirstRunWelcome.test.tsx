/**
 * @header {
 *   "module": "first-run-welcome-test",
 *   "layer": "test",
 *   "domain": "workstudio",
 *   "description": "OPAL WorkStudio 저장 상태가 없는 최초 실행에서 welcome onboarding 진입 화면과 데모/프로젝트 선택 흐름을 검증한다.",
 *   "exports": []
 * }
 */

import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { WORKSTUDIO_STORAGE_KEY } from "./mock-adapter";
import { WorkStudioApp } from "./WorkStudioApp";

describe("OPAL WorkStudio first-run welcome", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("shows welcome actions and empty recent Projects when no WorkStudio state is saved", async () => {
    render(<WorkStudioApp />);

    expect(await screen.findByRole("dialog", { name: "OPAL WorkStudio에 오신 것을 환영합니다" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "기존 프로젝트 열기" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "새 프로젝트 만들기" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "데모 둘러보기" })).toBeInTheDocument();
    expect(screen.getByText("최근 프로젝트가 없습니다")).toBeInTheDocument();
  });

  it("enters the seeded demo workspace and records state so welcome does not repeat", async () => {
    const { unmount } = render(<WorkStudioApp />);

    fireEvent.click(await screen.findByRole("button", { name: "데모 둘러보기" }));
    await act(async () => {});

    expect(screen.queryByRole("dialog", { name: "OPAL WorkStudio에 오신 것을 환영합니다" })).not.toBeInTheDocument();
    expect(await screen.findByText("Execution Workspace")).toBeInTheDocument();
    expect(localStorage.getItem(WORKSTUDIO_STORAGE_KEY)).not.toBeNull();

    unmount();
    render(<WorkStudioApp />);
    expect(screen.queryByRole("dialog", { name: "OPAL WorkStudio에 오신 것을 환영합니다" })).not.toBeInTheDocument();
  });

  it("keeps welcome open when existing Project directory selection is cancelled", async () => {
    vi.stubGlobal("opalWorkStudio", {
      project: {
        chooseDirectory: vi.fn(async () => ({ ok: false, code: "cancelled", message: "사용자가 선택을 취소했습니다." })),
        inspectDirectory: vi.fn(),
        registerFromSelection: vi.fn(),
        listFiles: vi.fn(),
      },
    });

    render(<WorkStudioApp />);
    fireEvent.click(await screen.findByRole("button", { name: "기존 프로젝트 열기" }));
    await act(async () => {});

    const welcome = screen.getByRole("dialog", { name: "OPAL WorkStudio에 오신 것을 환영합니다" });
    expect(welcome).toBeInTheDocument();
    expect(within(welcome).getByText("Project 선택이 취소되었습니다.")).toBeInTheDocument();
  });

  it("enters the workspace after a successful existing OPAL Project selection", async () => {
    vi.stubGlobal("opalWorkStudio", {
      project: {
        chooseDirectory: vi.fn(async () => ({
          ok: true,
          value: {
            path: "/tmp/opal-first-run",
            realPath: "/tmp/opal-first-run",
            name: "opal-first-run",
            isOpalProject: true,
            agentPath: "/tmp/opal-first-run/.opal/AGENT.md",
            pmName: "first-run PM",
          },
        })),
        inspectDirectory: vi.fn(),
        registerFromSelection: vi.fn(async (selection) => ({ ok: true, value: selection })),
        listFiles: vi.fn(),
      },
    });

    render(<WorkStudioApp />);
    fireEvent.click(await screen.findByRole("button", { name: "기존 프로젝트 열기" }));
    await act(async () => {});

    expect(screen.queryByRole("dialog", { name: "OPAL WorkStudio에 오신 것을 환영합니다" })).not.toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "opal-first-run" })).toBeInTheDocument();
    expect(await screen.findByText("first-run PM")).toBeInTheDocument();
  });

  it("S-2 loads recent Projects and opens a selected item into the workspace", async () => {
    const recent = {
      id: "recent-1",
      path: "/tmp/recent-one",
      realPath: "/tmp/recent-one",
      name: "recent-one",
      isOpalProject: true,
      pmName: "recent-one PM",
      createdAt: "2026-09-12T00:00:00.000Z",
      lastAccessedAt: "2026-09-13T00:00:00.000Z",
      status: "available",
    };
    const openRecent = vi.fn(async () => ({ ok: true, value: recent }));
    vi.stubGlobal("opalWorkStudio", {
      project: {
        listRecent: vi.fn(async () => ({ ok: true, value: { projects: [recent] } })),
        openRecent,
      },
    });

    render(<WorkStudioApp />);
    fireEvent.click(await screen.findByRole("button", { name: /recent-one/ }));
    await act(async () => {});

    expect(openRecent).toHaveBeenCalledWith("recent-1");
    expect(screen.queryByRole("dialog", { name: "OPAL WorkStudio에 오신 것을 환영합니다" })).not.toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "recent-one" })).toBeInTheDocument();
    expect(await screen.findByText("recent-one PM")).toBeInTheDocument();
  });

  it("S-3 marks a missing recent Project, blocks normal open, and repairs the same item", async () => {
    const missing = {
      id: "missing-1",
      path: "/tmp/missing-one",
      realPath: "/tmp/missing-one",
      name: "missing-one",
      isOpalProject: false,
      createdAt: "2026-09-12T00:00:00.000Z",
      lastAccessedAt: "2026-09-12T00:00:00.000Z",
      status: "missing",
    };
    const openRecent = vi.fn();
    const repairRecent = vi.fn(async () => ({
      ok: true,
      value: { ...missing, path: "/tmp/repaired", realPath: "/tmp/repaired", status: "available", isOpalProject: true },
    }));
    vi.stubGlobal("opalWorkStudio", {
      project: {
        listRecent: vi.fn(async () => ({ ok: true, value: { projects: [missing] } })),
        openRecent,
        chooseDirectory: vi.fn(async () => ({
          ok: true,
          value: { path: "/tmp/repaired", realPath: "/tmp/repaired", name: "repaired", isOpalProject: true },
        })),
        repairRecent,
      },
    });

    render(<WorkStudioApp />);
    expect(await screen.findByText("경로 유실")).toBeInTheDocument();
    const missingButton = screen.getByRole("button", { name: /missing-one/ });
    expect(missingButton).toBeDisabled();
    expect(openRecent).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /경로 복구/ }));
    await act(async () => {});
    expect(repairRecent).toHaveBeenCalledWith("missing-1", "/tmp/repaired");
  });
});
