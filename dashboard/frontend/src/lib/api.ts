/**
 * @header {
 *   "module": "api-client",
 *   "layer": "api-client",
 *   "domain": "core",
 *   "description": "OPAL Console API 클라이언트 — fetch 래퍼(선택적 timeoutMs AbortController 타임아웃 가드 + AbortError→사용자 친화 메시지 변환) + TanStack QueryClient (refetchInterval 30s, staleTime 30s). API_BASE_URL은 import.meta.env.VITE_API_BASE_URL(빌드·기동 시점 주입)이며 미주입 시 빈 문자열(동일 오리진 상대 경로)로 폴백한다 — base에 /api 접두사를 넣지 않는다(TRD.md TD-6, TASK.md C-8). 비정상 응답 시 JSON body의 detail 필드(FastAPI HTTPException=문자열, Pydantic 422=배열)를 파싱해 에러 메시지 뒤에 덧붙인다 — 파싱 실패 시 기존 메시지 그대로 폴백(안전 폴백).",
 *   "exports": ["apiClient", "queryClient", "API_BASE_URL", "ApiError"],
 *   "task": "061"
 * }
 */

import { QueryClient } from "@tanstack/react-query";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

/**
 * apiClient가 실패 시 던지는 오류. 기존 `Error`를 상속해 기존 호출자의
 * `catch (e) { e.message }` 경로를 그대로 유지하면서, HTTP status와
 * `{error:{code,message,details}}` envelope의 code·details를 추가로 보존한다.
 * (PLAN DEC-7, S-11)
 */
export class ApiError extends Error {
  readonly status?: number;
  readonly code?: string;
  readonly details?: unknown;

  constructor(
    message: string,
    options?: { status?: number; code?: string; details?: unknown; cause?: unknown },
  ) {
    super(message, options?.cause !== undefined ? { cause: options.cause } : undefined);
    this.name = "ApiError";
    this.status = options?.status;
    this.code = options?.code;
    this.details = options?.details;
  }
}

/**
 * 오류 응답 body가 `{error:{code,message,details...}}` envelope 형태인지 판별하고
 * code/message/details를 추출한다. envelope이 아니면 undefined 반환.
 */
function extractErrorEnvelope(
  body: unknown,
): { code?: string; message?: string; details?: unknown } | undefined {
  if (
    body === null ||
    typeof body !== "object" ||
    !("error" in body) ||
    body.error === null ||
    typeof (body as { error: unknown }).error !== "object"
  ) {
    return undefined;
  }
  const errorObj = (body as { error: Record<string, unknown> }).error;
  const { code, message, ...details } = errorObj;
  return {
    code: typeof code === "string" ? code : undefined,
    message: typeof message === "string" ? message : undefined,
    details: Object.keys(details).length > 0 ? details : undefined,
  };
}

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
      let envelope: { code?: string; message?: string; details?: unknown } | undefined;
      try {
        const parsedBody = await res.json();
        envelope = extractErrorEnvelope(parsedBody);
        detail = envelope?.message ?? extractErrorDetail(parsedBody);
      } catch {
        // body가 JSON이 아니거나 파싱 실패 — 기존 메시지로 안전 폴백
      }
      const baseMessage = `API error ${res.status}: ${res.statusText} (${path})`;
      throw new ApiError(detail ? `${baseMessage} — ${detail}` : baseMessage, {
        status: res.status,
        code: envelope?.code,
        details: envelope?.details,
      });
    }

    return res.json() as Promise<T>;
  } catch (e) {
    // AbortError → 사용자 친화 메시지 변환
    // Safari에서 AbortError가 "TypeError: Load failed"로 노출되는 것을 방지
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new ApiError(
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
