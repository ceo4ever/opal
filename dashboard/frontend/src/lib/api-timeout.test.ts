/**
 * @header {
 *   "module": "api-timeout-test",
 *   "layer": "test",
 *   "domain": "core",
 *   "description": "apiClient timeoutMs 타임아웃 가드 RED 테스트 — S-8(timeoutMs 초과 → 명시 메시지), S-11(timeoutMs 미전달 → 기존 동작 불변 회귀). 네트워크 fetch는 vi.fn 대역으로 치환, 타임아웃은 fake timer로 결정론적 처리.",
 *   "task": "037-260622-opd-브레인질의-타임아웃-견고화",
 *   "scenarios": ["S-8", "S-11"]
 * }
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiClient } from "./api";

/* ------------------------------------------------------------------ */
/* fetch 대역 셋업                                                       */
/* ------------------------------------------------------------------ */

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

/* ------------------------------------------------------------------ */
/* S-8: timeoutMs 초과 → AbortError → 명시 메시지 throw               */
/*                                                                     */
/* [RED 이유] 현재 api.ts의 apiClient에는 timeoutMs 파라미터 수용 코드가  */
/* 없고 AbortController도 없다. timeoutMs를 전달해도 무시되므로           */
/* 지연 fetch는 그대로 대기하며 "요청 시간이 초과되었습니다" 메시지로       */
/* throw되지 않는다 → 이 테스트는 현재 FAIL(RED)이어야 한다.              */
/* ------------------------------------------------------------------ */

describe("S-8: apiClient timeoutMs 초과 → 명시 에러 메시지 (RED)", () => {
  it("timeoutMs 초과 시 '요청 시간이 초과되었습니다' 메시지로 reject된다", async () => {
    // Given: abort 시그널에 반응하여 reject하는 지연 fetch 대역 (실 fetch 동작 모사)
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init?: RequestInit) =>
          new Promise<Response>((_, reject) => {
            init?.signal?.addEventListener("abort", () =>
              reject(new DOMException("The operation was aborted.", "AbortError")),
            );
          }),
      ),
    );

    // When: timeoutMs=100ms로 apiClient 호출 + 200ms 타이머 진행
    const resultPromise = apiClient<{ job_id: string }>("/api/brain/query", {
      method: "POST",
      body: JSON.stringify({ question: "test" }),
      timeoutMs: 100,
    } as RequestInit & { timeoutMs?: number });
    // 타이머 진행 전에 rejection 핸들러를 붙여 unhandled rejection 방지
    const expectation = expect(resultPromise).rejects.toThrow(
      "요청 시간이 초과되었습니다",
    );

    // 타이머를 100ms 이상 진행시켜 AbortController가 abort를 트리거하게 한다
    await vi.advanceTimersByTimeAsync(200);

    // Then: "요청 시간이 초과되었습니다" 류 명시 메시지로 reject
    await expectation;
  });

  it("timeoutMs 초과 시 던져진 에러에 경로(path) 정보가 포함된다", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init?: RequestInit) =>
          new Promise<Response>((_, reject) => {
            init?.signal?.addEventListener("abort", () =>
              reject(new DOMException("The operation was aborted.", "AbortError")),
            );
          }),
      ),
    );

    const resultPromise = apiClient<unknown>("/api/brain/job/test-job-id", {
      timeoutMs: 100,
    } as RequestInit & { timeoutMs?: number });
    const expectation = expect(resultPromise).rejects.toThrow(
      "/api/brain/job/test-job-id",
    );

    await vi.advanceTimersByTimeAsync(200);

    await expectation;
  });

  it("timeoutMs 초과 시 'TypeError: Load failed' 원시 오류가 노출되지 않는다", async () => {
    // Safari에서 AbortError가 TypeError: Load failed로 노출되는 것을 방지
    const abortError = new DOMException("The operation was aborted.", "AbortError");
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(abortError)));

    const resultPromise = apiClient<unknown>("/api/brain/query", {
      timeoutMs: 100,
    } as RequestInit & { timeoutMs?: number });
    // 즉시 reject되므로 핸들러를 먼저 붙여 unhandled rejection 방지
    const errPromise = resultPromise.catch((e: unknown) => e);

    await vi.advanceTimersByTimeAsync(200);

    const err = await errPromise;
    expect(err).toBeInstanceOf(Error);
    expect((err as Error).message).not.toContain("Load failed");
    expect((err as Error).message).toContain("요청 시간이 초과되었습니다");
  });
});

/* ------------------------------------------------------------------ */
/* S-11: timeoutMs 미전달 → 기존 fetch 동작 불변 (회귀 가드)              */
/*                                                                     */
/* [이 케이스는 구현 완료 후에도 PASS여야 한다 — 회귀 방지 가드]           */
/* 현재 api.ts는 timeoutMs를 모르므로, 미전달 시 동작은 이미 "불변"이다.   */
/* GREEN 구현 후에도 이 테스트가 PASS임을 검증한다.                        */
/* ------------------------------------------------------------------ */

describe("S-11: apiClient timeoutMs 미전달 → 기존 동작 불변 (회귀 가드)", () => {
  it("timeoutMs 없이 호출하면 정상 응답을 그대로 반환한다", async () => {
    // Given: 즉시 200 응답 대역
    const mockPayload = { state: "ready", session_active: true, message: "ok" };
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockPayload),
        } as Response),
      ),
    );

    // When: timeoutMs 미전달 (기존 5화면류 호출 패턴)
    const result = await apiClient<typeof mockPayload>("/api/brain/status?project=p&session_id=s");

    // Then: 정상 응답 반환
    expect(result).toEqual(mockPayload);
  });

  it("timeoutMs 없이 호출하면 fetch에 signal이 전달되지 않는다 (AbortController 미생성)", async () => {
    // Given: fetch 호출 인자를 캡처하는 대역
    let capturedSignal: AbortSignal | undefined | null = undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) => {
        capturedSignal = init?.signal;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ ok: true }),
        } as Response);
      }),
    );

    // When: timeoutMs 없이 호출
    await apiClient<{ ok: boolean }>("/api/brain/status");

    // Then: signal이 undefined 또는 null이어야 한다 (AbortController 미생성)
    // 현재 구현은 signal을 전달하지 않으므로 undefined여야 한다
    expect(capturedSignal).toBeUndefined();
  });

  it("timeoutMs 없이 호출 시 API 에러는 기존 메시지 형식으로 throw된다", async () => {
    // Given: 500 응답 대역
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          statusText: "Internal Server Error",
        } as Response),
      ),
    );

    // Then: 기존 에러 형식 "API error 500: ..." 유지
    await expect(
      apiClient("/api/brain/status"),
    ).rejects.toThrow("API error 500");
  });
});
