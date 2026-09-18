/**
 * @header {
 *   "module": "api-error-test",
 *   "layer": "test",
 *   "domain": "core",
 *   "description": "apiClient ApiError additive 확장 RED 테스트 — S-11(DEC-7, AC-6, C-7). apiClient가 실패 시 status·code·message·details를 보존하는 ApiError를 던지는지 검증하고, 기존 FastAPI detail 메시지 추출·timeout 동작·generic message 폴백·기존 호출자 시그니처가 그대로 유지되는지 회귀 가드로 확인한다. 네트워크 fetch는 vi.fn 대역으로 치환한다.",
 *   "task": "140-260917-opdw-스킬-문서-화면",
 *   "scenarios": ["S-11"],
 *   "exports": []
 * }
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiClient, ApiError } from "./api";

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

/* ------------------------------------------------------------------ */
/* ① FastAPI detail만 있는 오류 응답 — 기존 메시지 추출 + 호출자 시그니처 유지 */
/* ------------------------------------------------------------------ */

describe("S-11 ①: FastAPI detail 오류 응답 (RED)", () => {
  it("detail 문자열이 있으면 기존과 동일하게 메시지에 반영된 Error를 throw한다", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 404,
          statusText: "Not Found",
          json: () => Promise.resolve({ detail: "스킬을 찾을 수 없습니다" }),
        } as Response),
      ),
    );

    await expect(apiClient("/api/docs/skills/unknown")).rejects.toThrow(
      "스킬을 찾을 수 없습니다",
    );
  });

  it("throw된 오류는 ApiError 인스턴스이며 status를 보존한다", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 404,
          statusText: "Not Found",
          json: () => Promise.resolve({ detail: "스킬을 찾을 수 없습니다" }),
        } as Response),
      ),
    );

    const err = await apiClient("/api/docs/skills/unknown").catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).status).toBe(404);
  });

  it("기존 호출자 시그니처(제네릭 T 반환)가 그대로 유지된다", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ state: "ready" }),
        } as Response),
      ),
    );

    const result = await apiClient<{ state: string }>("/api/brain/status");
    expect(result).toEqual({ state: "ready" });
  });
});

/* ------------------------------------------------------------------ */
/* ② {error:{code,message,details}} envelope 응답 — ApiError 보존           */
/* ------------------------------------------------------------------ */

describe("S-11 ②: error envelope 응답 (RED)", () => {
  it("ApiError가 status·code·message·details를 보존해 throw된다", async () => {
    const envelope = {
      error: {
        code: "source_missing",
        message: "원본 문서를 찾을 수 없습니다",
        skill_id: "opal-onboarding",
        retryable: false,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 200,
          statusText: "OK",
          json: () => Promise.resolve(envelope),
        } as Response),
      ),
    );

    const err = (await apiClient("/api/docs/skills/opal-onboarding").catch(
      (e: unknown) => e,
    )) as ApiError;

    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("source_missing");
    expect(err.message).toContain("원본 문서를 찾을 수 없습니다");
    expect(err.details).toEqual(
      expect.objectContaining({ skill_id: "opal-onboarding", retryable: false }),
    );
  });

  it("envelope 응답이 아닌 일반 detail 오류는 code가 undefined다 (기존 detail 경로 회귀 없음)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 422,
          statusText: "Unprocessable Entity",
          json: () =>
            Promise.resolve({
              detail: [{ loc: ["body", "q"], msg: "field required", type: "value_error" }],
            }),
        } as Response),
      ),
    );

    const err = (await apiClient("/api/docs/skills").catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBeUndefined();
    expect(err.message).toContain("field required");
  });
});

/* ------------------------------------------------------------------ */
/* ③ 타임아웃 — 기존 timeout 동작·메시지 유지                                */
/* ------------------------------------------------------------------ */

describe("S-11 ③: 타임아웃 동작 회귀 가드 (RED)", () => {
  it("timeoutMs 초과 시 기존과 동일하게 '요청 시간이 초과되었습니다' 메시지로 reject된다", async () => {
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

    const resultPromise = apiClient<unknown>("/api/docs/skills", { timeoutMs: 100 } as RequestInit & {
      timeoutMs?: number;
    });
    const expectation = expect(resultPromise).rejects.toThrow("요청 시간이 초과되었습니다");

    await vi.advanceTimersByTimeAsync(200);
    await expectation;
  });

  it("타임아웃으로 던져진 오류도 ApiError 인스턴스다", async () => {
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

    const errPromise = apiClient<unknown>("/api/docs/skills", { timeoutMs: 100 } as RequestInit & {
      timeoutMs?: number;
    }).catch((e: unknown) => e);

    await vi.advanceTimersByTimeAsync(200);
    const err = await errPromise;
    expect(err).toBeInstanceOf(ApiError);
  });
});

/* ------------------------------------------------------------------ */
/* ④ JSON이 아닌 오류 본문 — generic message 폴백 유지                       */
/* ------------------------------------------------------------------ */

describe("S-11 ④: JSON이 아닌 오류 본문 (RED)", () => {
  it("본문 파싱에 실패하면 generic 'API error {status}' 메시지로 폴백한다", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          statusText: "Internal Server Error",
          json: () => Promise.reject(new SyntaxError("Unexpected token < in JSON")),
        } as Response),
      ),
    );

    await expect(apiClient("/api/docs/skills")).rejects.toThrow("API error 500");
  });

  it("폴백 오류도 ApiError 인스턴스이며 status를 보존한다", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          statusText: "Internal Server Error",
          json: () => Promise.reject(new SyntaxError("Unexpected token < in JSON")),
        } as Response),
      ),
    );

    const err = (await apiClient("/api/docs/skills").catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(500);
    expect(err.code).toBeUndefined();
  });
});
