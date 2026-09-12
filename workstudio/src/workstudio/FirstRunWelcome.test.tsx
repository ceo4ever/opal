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
});
