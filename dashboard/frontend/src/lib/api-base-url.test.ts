/**
 * @header {
 *   "module": "api-base-url-test",
 *   "layer": "test",
 *   "domain": "core",
 *   "description": "S-1/S-3 — API_BASE_URL이 import.meta.env.VITE_API_BASE_URL을 참조하고, 미주입 시 빈 문자열 동일 오리진 상대 경로로 조립되는지 검증한다.",
 *   "task": "127-260912-oppl-E2E-하네스-구현",
 *   "scenarios": ["S-1", "S-3"],
 *   "exports": []
 * }
 */

import { describe, it, expect, vi, afterEach } from "vitest";
import apiSource from "./api.ts?raw";
import { API_BASE_URL, apiClient } from "./api";

describe("S-1: api.ts 고정 주소 리터럴 제거 (RED)", () => {
  it("api.ts 소스에 http://127.0.0.1:7823 리터럴이 없다 (MV-24)", () => {
    expect(apiSource).not.toContain("http://127.0.0.1:7823");
  });

  it("api.ts 소스가 import.meta.env.VITE_API_BASE_URL을 참조한다 (MV-24)", () => {
    expect(apiSource).toContain("import.meta.env.VITE_API_BASE_URL");
  });
});

describe("S-3: VITE_API_BASE_URL 미주입 시 동일 오리진 상대 경로 (RED)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("API_BASE_URL이 빈 문자열이다 (vitest mode=test, .env.development 미로드)", () => {
    expect(API_BASE_URL).toBe("");
  });

  it("apiClient 호출 시 fetch에 전달되는 URL이 /api/... 상대 경로다", async () => {
    let capturedUrl: string | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        capturedUrl = url;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        } as Response);
      }),
    );

    await apiClient("/api/dashboard");

    expect(capturedUrl).toBe("/api/dashboard");
    expect(capturedUrl).not.toContain("127.0.0.1:7823");
  });
});
