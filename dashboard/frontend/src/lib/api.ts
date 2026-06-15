/**
 * @header {
 *   "module": "api-client",
 *   "layer": "api-client",
 *   "domain": "core",
 *   "description": "OPAL Console API 클라이언트 — fetch 래퍼 + TanStack QueryClient (refetchInterval 30s, staleTime 30s)",
 *   "exports": ["apiClient", "queryClient", "API_BASE_URL"]
 * }
 */

import { QueryClient } from "@tanstack/react-query";

export const API_BASE_URL = "http://127.0.0.1:7823";

/**
 * 기본 fetch 래퍼. 비정상 응답 시 Error를 throw한다.
 * 모든 API 호출은 이 함수를 경유한다.
 */
export async function apiClient<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText} (${path})`);
  }

  return res.json() as Promise<T>;
}

/**
 * TanStack Query 글로벌 클라이언트
 * - staleTime 30s: 30초 이내 재요청 시 캐시 사용
 * - refetchInterval 30s: 30초마다 자동 갱신 (연결 상태 상시 최신화)
 * - retry 1: 네트워크 오류 1회 재시도
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchInterval: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
