/**
 * @header {
 *   "module": "api-client",
 *   "layer": "api-client",
 *   "domain": "core",
 *   "description": "OPAL Console API 클라이언트 — fetch 래퍼(선택적 timeoutMs AbortController 타임아웃 가드 + AbortError→사용자 친화 메시지 변환) + TanStack QueryClient (refetchInterval 30s, staleTime 30s). timeoutMs 미전달 시 기존 동작 완전 불변. [T061] 비정상 응답 시 JSON body의 detail 필드(FastAPI HTTPException=문자열, Pydantic 422=배열)를 파싱해 기존 에러 메시지 뒤에 덧붙인다 — 파싱 실패 시 기존 메시지 그대로 폴백(안전 폴백), 성공 경로·기존 호출부 시그니처는 불변.",
 *   "exports": ["apiClient", "queryClient", "API_BASE_URL"],
 *   "task": "061",
 *   "changelog": [
 *     "2026-07-14 T061 PM 승인 스코프 확장: 에러 응답 body의 detail 필드를 파싱해 메시지에 병기 — SettingsPage 저장 실패 Alert에 백엔드 사유(예: '프로젝트를 찾을 수 없습니다', Pydantic 필드 오류) 노출 (S-10/TS-043 대응)"
 *   ]
 * }
 */

import { QueryClient } from "@tanstack/react-query";

export const API_BASE_URL = "http://127.0.0.1:7823";

/**
 * 에러 응답 body에서 FastAPI/Pydantic detail 사유를 문자열화한다.
 * - FastAPI HTTPException: `{ detail: string }`
 * - Pydantic 422 검증 오류: `{ detail: [{ loc, msg, type }, ...] }`
 * - 위 형태가 아니거나 파싱 실패 시 undefined 반환 (안전 폴백 — 호출부가 기존 메시지 유지)
 */
function extractErrorDetail(body: unknown): string | undefined {
  if (body === null || typeof body !== "object" || !("detail" in body)) {
    return undefined;
  }
  const detail = (body as { detail: unknown }).detail;

  if (typeof detail === "string" && detail.length > 0) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) =>
        item && typeof item === "object" && "msg" in item
          ? String((item as { msg: unknown }).msg)
          : undefined,
      )
      .filter((msg): msg is string => !!msg);
    if (messages.length > 0) return messages.join("; ");
  }

  return undefined;
}

/**
 * 기본 fetch 래퍼. 비정상 응답 시 Error를 throw한다.
 * 모든 API 호출은 이 함수를 경유한다.
 *
 * @param path   API 경로 (예: "/api/brain/query")
 * @param options RequestInit + 선택적 timeoutMs (ms 단위).
 *   timeoutMs 지정 시 AbortController + setTimeout으로 abort 트리거.
 *   미지정 시 AbortController/timer 미생성 — 기존 동작 완전 불변.
 *   AbortError 발생 시 Safari "TypeError: Load failed" 대신
 *   "요청 시간이 초과되었습니다 (...)" 명시 메시지로 변환.
 */
export async function apiClient<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number },
): Promise<T> {
  const { timeoutMs, ...rest } = options ?? {};

  const controller = timeoutMs ? new AbortController() : undefined;
  const timer = timeoutMs
    ? setTimeout(() => controller!.abort(), timeoutMs)
    : undefined;

  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      signal: controller?.signal,
      ...rest,
    });

    if (!res.ok) {
      let detail: string | undefined;
      try {
        detail = extractErrorDetail(await res.json());
      } catch {
        // body가 JSON이 아니거나 파싱 실패 — 기존 메시지로 안전 폴백
      }
      const baseMessage = `API error ${res.status}: ${res.statusText} (${path})`;
      throw new Error(detail ? `${baseMessage} — ${detail}` : baseMessage);
    }

    return res.json() as Promise<T>;
  } catch (e) {
    // AbortError → 사용자 친화 메시지 변환
    // Safari에서 AbortError가 "TypeError: Load failed"로 노출되는 것을 방지
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error(
        `요청 시간이 초과되었습니다 (${timeoutMs}ms). 잠시 후 다시 시도해주세요. (${path})`,
        { cause: e },
      );
    }
    throw e;
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
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
