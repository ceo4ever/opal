/**
 * @header {
 *   "module": "lock-screen-test",
 *   "layer": "test",
 *   "domain": "core",
 *   "description": "S-10 RED — 잠금 화면(D-14) 계약 테스트. 미인증 시 App이 라우터를 마운트하지 않고 LockScreen만 보이며, 이 동안 /api/auth/session 외 API 호출 0회·프로젝트/설정/계정 정보 없음·opal-cli console open 안내 존재, 인증 시 라우터 마운트·교환 0회를 검증한다.",
 *   "exports": [],
 *   "depends": ["lock-screen", "app", "auth"],
 *   "task": "172",
 *   "scenarios": ["S-10"]
 * }
 */

/*
 * GREEN 구현자가 따를 export 계약:
 *   - `@/components/auth/LockScreen` : named export `LockScreen` (props 없음, API 호출 없음, 정적 안내 + 상태 재확인 버튼 1개)
 *   - `@/App` : default export App. `useAuthStatus()`가 "authed"일 때만 `@/router`의 router를 마운트, 그 외 pending은 라우터 미마운트, locked는 LockScreen.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { StrictMode } from "react";

vi.mock("@/router", async () => {
  const { createMemoryRouter } = await import("react-router-dom");
  return {
    router: createMemoryRouter([{ path: "/", element: <div>인증된 화면 마운트됨</div> }]),
  };
});

const calls: string[] = [];

function stubSession(body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      calls.push(String(url).replace(/^https?:\/\/[^/]+/, ""));
      return Promise.resolve(
        new Response(JSON.stringify(body), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );
}

beforeEach(() => {
  calls.length = 0;
  vi.resetModules();
  window.history.replaceState(null, "", "/");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("S-10 LockScreen", () => {
  it("단독 렌더: 안내 문구만 있고 API 호출 0회, 재확인 버튼 1개, 프로젝트/설정/계정 정보 없음", async () => {
    stubSession({ authenticated: false });
    const { LockScreen } = await import("./LockScreen");
    const { container } = render(<LockScreen />);
    expect(container.textContent).toContain("opal-cli console open");
    expect(screen.getAllByRole("button")).toHaveLength(1);
    expect(calls).toHaveLength(0);
    for (const word of ["Settings", "설정", "프로젝트", "Account", "계정", "Brain"]) {
      expect(container.textContent).not.toContain(word);
    }
  });

  it("③ 세션 없음: App은 잠금 화면만 보이고 /api/auth/session 외 호출 0회, 라우터 미마운트", async () => {
    stubSession({ authenticated: false });
    const { default: App } = await import("@/App");
    render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
    await screen.findByText(/opal-cli console open/);
    expect(screen.queryByText("인증된 화면 마운트됨")).not.toBeInTheDocument();
    expect(calls.length).toBeGreaterThan(0);
    for (const c of calls) expect(c).toBe("/api/auth/session");
  });

  it("③' 유효 세션: 라우터가 마운트되고 교환 요청 0회", async () => {
    stubSession({ authenticated: true, csrf_token: "c1" });
    const { default: App } = await import("@/App");
    render(<App />);
    await waitFor(() => expect(screen.getByText("인증된 화면 마운트됨")).toBeInTheDocument());
    expect(calls.filter((c) => c.includes("/api/auth/exchange"))).toHaveLength(0);
    expect(screen.queryByText(/opal-cli console open/)).not.toBeInTheDocument();
  });
});
