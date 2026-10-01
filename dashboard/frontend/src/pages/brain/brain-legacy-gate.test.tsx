/**
 * @header {
 *   "module": "brain-legacy-gate-test",
 *   "layer": "test",
 *   "domain": "brain",
 *   "description": "S-11 RED — 구형 Brain 게이트(D-19) 계약 테스트. 꺼짐 상태 첫 진입 화면(안내·위험 3종·선택지·prime/status/query 호출 0회), 위험 확인 체크 전후 버튼, 켜기 POST 본문 1회, 켜진 화면(legacy 배지·끄기), 끄기 응답 running_turns 안내, Settings 선프라임 토글 안내를 검증한다. apiClient는 상태 보유 mock.",
 *   "exports": [],
 *   "depends": ["brain-legacy-gate", "brain-page", "settings-page", "api-client"],
 *   "task": "172",
 *   "scenarios": ["S-11"]
 * }
 */

/*
 * GREEN 구현자가 따를 export 계약:
 *   - `@/pages/brain/BrainLegacyGate` : named export `BrainLegacyGate` ({children}를 감싸는 컴포넌트).
 *     GET /api/brain/legacy → {enabled, running_turns}; 꺼짐이면 children 미마운트.
 *     켜기: POST /api/brain/legacy {enabled:true, risk_acknowledged:true}. 끄기: POST {enabled:false, risk_acknowledged:false}.
 *   - `@/pages/brain/BrainPage` : `BrainPage`가 내부적으로 BrainLegacyGate로 감싸진다(기존 export 헬퍼 유지).
 *   - `@/pages/settings/SettingsPage` : `SettingsPage`가 GET /api/brain/legacy를 읽어 꺼짐이면 "동작하지 않" 안내를 선프라임 섹션에 덧붙인다.
 *   - UI 문구: "구형 Brain 켜기"(버튼), 위험 확인 체크박스(role=checkbox), 배지 "legacy", "구형 Brain 끄기".
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent, cleanup } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrainPage } from "./BrainPage";
import { SettingsPage } from "@/pages/settings/SettingsPage";
import { useUiStore } from "@/store/ui-store";
import { apiClient } from "@/lib/api";

const PROJECT = "/path/to/project-a";

const legacy = { enabled: false, running_turns: 0 };
let offResponse = { enabled: false, running_turns: 0 };

vi.mock("@/lib/api", () => ({
  apiClient: vi.fn((path: string, options?: RequestInit) => {
    if (path.startsWith("/api/brain/legacy")) {
      if (options?.method === "POST") {
        const body = JSON.parse(options.body as string) as { enabled: boolean };
        if (body.enabled) {
          legacy.enabled = true;
          return Promise.resolve({ enabled: true, running_turns: 0 });
        }
        legacy.enabled = false;
        return Promise.resolve(offResponse);
      }
      return Promise.resolve({ ...legacy });
    }
    if (path.startsWith("/api/brain/auth")) {
      return Promise.resolve({ authenticated: true, cli_available: true, message: "" });
    }
    if (path.startsWith("/api/brain/prime")) return Promise.resolve({ priming: true });
    if (path.startsWith("/api/brain/status")) {
      return Promise.resolve({ state: "ready", session_active: true, message: "" });
    }
    if (path.startsWith("/api/config")) {
      return Promise.resolve({ scan_roots: [], scan_depth: 2, exclude: [], prewarm_projects: [] });
    }
    return Promise.reject(new Error(`[test] unmocked apiClient path: ${path}`));
  }),
}));

function paths(): string[] {
  return vi.mocked(apiClient).mock.calls.map(([p]) => p as string);
}
function legacyPosts() {
  return vi
    .mocked(apiClient)
    .mock.calls.filter(([p, o]) => p.startsWith("/api/brain/legacy") && o?.method === "POST");
}

function renderWith(element: React.ReactNode, path: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const router = createMemoryRouter([{ path, element }], { initialEntries: [path] });
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  legacy.enabled = false;
  legacy.running_turns = 0;
  offResponse = { enabled: false, running_turns: 0 };
  useUiStore.setState({ contextProject: PROJECT, brainDirty: false });
});
afterEach(() => cleanup());

async function waitGate() {
  await screen.findByText(/새 Brain 출시 전까지/);
}

describe("S-11 ① 꺼짐 상태 첫 진입 화면", () => {
  it("안내·위험 3종·선택지가 함께 보이고 prime·status·query 호출 0회", async () => {
    renderWith(<BrainPage />, "/brain");
    await waitGate();
    expect(screen.getByText(/기본적으로 사용할 수 없/)).toBeInTheDocument();
    expect(screen.getByText(/업그레이드/)).toBeInTheDocument();
    expect(screen.getByText(/파일 읽기/)).toBeInTheDocument();
    expect(screen.getByText(/Bash/)).toBeInTheDocument();
    expect(screen.getByText(/네트워크/)).toBeInTheDocument();
    expect(screen.getByText(/새 경로 출시를 기다린다/)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/질문을 입력하세요/)).not.toBeInTheDocument();
    await new Promise((r) => setTimeout(r, 50));
    const p = paths();
    expect(p.filter((x) => /\/api\/brain\/(prime|status|query)/.test(x))).toHaveLength(0);
  });
});

describe("S-11 ② ③ 위험 확인 → 켜기", () => {
  it("체크 전 버튼 비활성, 체크 후 활성, 클릭 시 POST 정확히 1회", async () => {
    renderWith(<BrainPage />, "/brain");
    await waitGate();
    const btn = screen.getByRole("button", { name: "구형 Brain 켜기" });
    expect(btn).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox"));
    await waitFor(() => expect(btn).toBeEnabled());
    fireEvent.click(btn);
    await waitFor(() => expect(legacyPosts()).toHaveLength(1));
    expect(JSON.parse(legacyPosts()[0][1]!.body as string)).toEqual({
      enabled: true,
      risk_acknowledged: true,
    });
  });
});

describe("S-11 ④ 켜진 상태 화면", () => {
  it("대화 UI, legacy 배지, 구형 Brain 끄기가 보인다", async () => {
    legacy.enabled = true;
    renderWith(<BrainPage />, "/brain");
    await screen.findByPlaceholderText("질문을 입력하세요... (⌘Enter로 제출)");
    expect(screen.getByText("legacy")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "구형 Brain 끄기" })).toBeInTheDocument();
    expect(screen.queryByText(/새 Brain 출시 전까지/)).not.toBeInTheDocument();
  });
});

describe("S-11 ⑤ 끄기 응답 running_turns", () => {
  it("진행 중인 2개 질의는 끝까지 진행됩니다 표시", async () => {
    legacy.enabled = true;
    offResponse = { enabled: false, running_turns: 2 };
    renderWith(<BrainPage />, "/brain");
    fireEvent.click(await screen.findByRole("button", { name: "구형 Brain 끄기" }));
    await screen.findByText(/진행 중인 2개 질의는 끝까지 진행됩니다/);
  });
});

describe("S-11 ⑥ Settings 선프라임 토글", () => {
  it("꺼짐 상태에서는 동작하지 않는다는 안내가 보인다", async () => {
    renderWith(<SettingsPage />, "/settings");
    await screen.findByText(/동작하지 않/);
    expect(screen.getByText("프라임 풀 토글")).toBeInTheDocument();
  });
});
