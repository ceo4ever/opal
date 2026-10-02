/**
 * @header {
 *   "module": "auth-test",
 *   "layer": "test",
 *   "domain": "core",
 *   "description": "S-10 RED — FE 인증 부트스트랩(D-13) 계약 테스트. #entry fragment 교환(replaceState 선행·StrictMode 1회)·교환 실패 잠금·세션 조회·apiClient credentials/CSRF·401 auth_required 잠금·index.html referrer meta를 검증한다. fetch는 vi.fn 대역.",
 *   "exports": [],
 *   "depends": ["auth", "api-client"],
 *   "task": "175",
 *   "scenarios": ["S-10"]
 * }
 */

/*
 * GREEN 구현자가 따를 export 계약 (`@/lib/auth`, PLAN D-13):
 *   - bootstrapAuth(): Promise<AuthStatus>   모듈 단일 Promise. 여러 번 호출해도 진입(교환/세션 조회)은 1회
 *   - getAuthStatus(): "pending" | "authed" | "locked"
 *   - useAuthStatus(): AuthStatus            React hook (useSyncExternalStore 등). 마운트 시 bootstrapAuth 호출
 *   - getCsrfToken(): string | null          메모리 보관만 (storage 금지)
 *   - markLocked(): void                     apiClient가 401 auth_required에서 호출
 * `@/lib/api`의 apiClient: 모든 fetch에 credentials:"include", GET·HEAD 외에는 X-CSRF-Token 헤더.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
// @ts-expect-error TS2591 — node:fs 타입 미해석(@types/node 미설치, api-env-files.test.ts와 같은 관례)
import { readFileSync } from "node:fs";
// @ts-expect-error TS2591 — node:path 타입 미해석(@types/node 미설치)
import { resolve } from "node:path";
import { createElement, StrictMode } from "react";
import { render, screen, cleanup, waitFor } from "@testing-library/react";

type FetchCall = { url: string; init: RequestInit };
let calls: FetchCall[];

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function stubFetch(handler: (url: string, init: RequestInit) => Promise<Response> | Response) {
  const fn = vi.fn((url: string, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    return Promise.resolve(handler(String(url), init ?? {}));
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

async function freshAuth() {
  vi.resetModules();
  return import("./auth");
}

beforeEach(() => {
  calls = [];
  window.history.replaceState(null, "", "/");
  window.localStorage.clear();
  window.sessionStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("S-10 ① #entry 진입 교환", () => {
  it("교환 fetch가 해결되기 전에 fragment가 제거되고, StrictMode 이중 마운트에도 교환은 1회이며 성공 시 authed", async () => {
    window.history.replaceState(null, "", "/#entry=tok-123");
    const order: string[] = [];
    const realReplace = window.history.replaceState.bind(window.history);
    vi.spyOn(window.history, "replaceState").mockImplementation((...args) => {
      order.push("replaceState");
      return realReplace(...args);
    });
    let release!: (r: Response) => void;
    const gate = new Promise<Response>((r) => (release = r));
    const fn = vi.fn((url: string, init?: RequestInit) => {
      order.push(`fetch:${url}`);
      calls.push({ url: String(url), init: init ?? {} });
      return gate;
    });
    vi.stubGlobal("fetch", fn);

    const auth = await freshAuth();
    const Probe = () => createElement("div", { "data-testid": "st" }, auth.useAuthStatus());
    render(createElement(StrictMode, null, createElement(Probe)));

    await waitFor(() => expect(fn).toHaveBeenCalled());
    // 교환 요청이 나가는 시점에 이미 fragment는 제거되어 있어야 한다
    expect(order.indexOf("replaceState")).toBeGreaterThanOrEqual(0);
    expect(order.indexOf("replaceState")).toBeLessThan(
      order.findIndex((o) => o.startsWith("fetch:")),
    );
    expect(window.location.hash).toBe("");

    release(jsonResponse(200, { authenticated: true, csrf_token: "csrf-abc" }));
    await waitFor(() => expect(screen.getByTestId("st").textContent).toBe("authed"));

    const exchanges = calls.filter((c) => c.url.endsWith("/api/auth/exchange"));
    expect(exchanges).toHaveLength(1);
    expect(exchanges[0].init.method).toBe("POST");
    expect(JSON.parse(exchanges[0].init.body as string)).toEqual({ token: "tok-123" });
    expect(auth.getCsrfToken()).toBe("csrf-abc");
  });
});

describe("S-10 ② 교환 실패", () => {
  it("401 entry_token_invalid이면 locked", async () => {
    window.history.replaceState(null, "", "/#entry=bad");
    stubFetch(() => jsonResponse(401, { error: { code: "entry_token_invalid", message: "x" } }));
    const auth = await freshAuth();
    await auth.bootstrapAuth();
    expect(auth.getAuthStatus()).toBe("locked");
    expect(auth.getCsrfToken()).toBeNull();
  });
});

describe("S-10 ③ fragment 없음 + 세션 없음", () => {
  it("GET /api/auth/session만 호출하고 미인증이면 locked", async () => {
    stubFetch(() => jsonResponse(200, { authenticated: false }));
    const auth = await freshAuth();
    await auth.bootstrapAuth();
    expect(auth.getAuthStatus()).toBe("locked");
    expect(calls.map((c) => c.url.replace(/^https?:\/\/[^/]+/, ""))).toEqual(["/api/auth/session"]);
    expect((calls[0].init.method ?? "GET").toUpperCase()).toBe("GET");
  });
});

describe("S-10 ③' fragment 없음 + 유효 세션 쿠키", () => {
  it("교환 0회, authed, csrf_token은 메모리에만 보관", async () => {
    stubFetch(() => jsonResponse(200, { authenticated: true, csrf_token: "csrf-mem" }));
    const auth = await freshAuth();
    await auth.bootstrapAuth();
    expect(auth.getAuthStatus()).toBe("authed");
    expect(calls.filter((c) => c.url.includes("/api/auth/exchange"))).toHaveLength(0);
    expect(auth.getCsrfToken()).toBe("csrf-mem");
    expect(JSON.stringify({ ...window.localStorage })).not.toContain("csrf-mem");
    expect(JSON.stringify({ ...window.sessionStorage })).not.toContain("csrf-mem");
    expect(document.cookie).not.toContain("csrf-mem");
  });
});

describe("S-10 ④ apiClient credentials·CSRF", () => {
  it("모든 요청 credentials include, POST만 X-CSRF-Token, 값은 storage·cookie에 없음", async () => {
    stubFetch((url) =>
      url.includes("/api/auth/session")
        ? jsonResponse(200, { authenticated: true, csrf_token: "csrf-xyz" })
        : jsonResponse(200, { ok: true }),
    );
    const auth = await freshAuth();
    await auth.bootstrapAuth();
    const { apiClient } = await import("./api");
    calls.length = 0;

    await apiClient("/api/projects");
    await apiClient("/api/thing", { method: "POST", body: "{}" });

    expect(calls).toHaveLength(2);
    for (const c of calls) expect(c.init.credentials).toBe("include");
    const hdr = (c: FetchCall, k: string) =>
      new Headers(c.init.headers as HeadersInit).get(k);
    expect(hdr(calls[0], "X-CSRF-Token")).toBeNull();
    expect(hdr(calls[1], "X-CSRF-Token")).toBe("csrf-xyz");
    expect(JSON.stringify({ ...window.localStorage })).not.toContain("csrf-xyz");
    expect(JSON.stringify({ ...window.sessionStorage })).not.toContain("csrf-xyz");
    expect(document.cookie).not.toContain("csrf-xyz");
  });
});

describe("S-10 ⑤ 인증 후 401 auth_required", () => {
  it("인증 상태가 locked로 전환된다", async () => {
    stubFetch((url) =>
      url.includes("/api/auth/session")
        ? jsonResponse(200, { authenticated: true, csrf_token: "c" })
        : jsonResponse(401, { error: { code: "auth_required", message: "login" } }),
    );
    const auth = await freshAuth();
    await auth.bootstrapAuth();
    expect(auth.getAuthStatus()).toBe("authed");
    const { apiClient } = await import("./api");
    await expect(apiClient("/api/projects")).rejects.toBeTruthy();
    expect(auth.getAuthStatus()).toBe("locked");
  });
});

describe("S-10 ⑥ index.html", () => {
  it("referrer no-referrer meta가 있다", () => {
    // @ts-expect-error TS2591 — process(node global) 타입 미해석(@types/node 미설치)
    const html = readFileSync(resolve(process.cwd(), "index.html"), "utf-8");
    expect(html).toMatch(/<meta\s+name="referrer"\s+content="no-referrer"\s*\/?>/);
  });
});
