/**
 * @header {
 *   "module": "auth",
 *   "layer": "api-client",
 *   "domain": "core",
 *   "description": "OPAL Console 인증 부트스트랩(D-13) — 모듈 단일 Promise로 진입을 정확히 1회 수행한다(StrictMode 이중 effect 방어). location.hash가 #entry=<token>이면 교환 요청 전에 history.replaceState로 fragment를 제거한 뒤 POST /api/auth/exchange, 아니면 GET /api/auth/session을 호출해 authed/locked를 결정한다. csrf_token은 모듈 메모리에만 보관한다(localStorage·sessionStorage·쿠키 접근 금지, C-2). apiClient가 401 auth_required에서 markLocked()를 호출해 잠금으로 전환한다. useAuthStatus()는 useSyncExternalStore 기반 React hook이다. 프로젝트·설정·계정 정보는 다루지 않는다.",
 *   "exports": ["bootstrapAuth", "getAuthStatus", "useAuthStatus", "getCsrfToken", "markLocked", "AuthStatus"],
 *   "depends": [],
 *   "task": "175"
 * }
 */

import { useEffect, useSyncExternalStore } from "react";

export type AuthStatus = "pending" | "authed" | "locked";

interface AuthResponse {
  authenticated?: boolean;
  csrf_token?: string;
}

// api.ts와의 순환 import를 피하기 위해 base URL을 직접 읽는다(동일 규칙: 미주입 시 빈 문자열).
const BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const ENTRY_PREFIX = "#entry=";

let status: AuthStatus = "pending";
let csrfToken: string | null = null;
let bootPromise: Promise<AuthStatus> | null = null;
const listeners = new Set<() => void>();

function setState(next: AuthStatus, csrf: string | null): void {
  status = next;
  csrfToken = next === "authed" ? csrf : null;
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getAuthStatus(): AuthStatus {
  return status;
}

export function getCsrfToken(): string | null {
  return csrfToken;
}

/** 인증 후 401 auth_required 수신 시 apiClient가 호출한다. */
export function markLocked(): void {
  if (status === "locked") return;
  setState("locked", null);
}

/** 진입 fragment에서 token을 꺼내고, 요청 전에 fragment를 주소창에서 제거한다. */
function takeEntryToken(): string | null {
  const hash = window.location.hash;
  if (!hash.startsWith(ENTRY_PREFIX)) return null;
  const token = decodeURIComponent(hash.slice(ENTRY_PREFIX.length));
  window.history.replaceState(null, "", window.location.pathname + window.location.search);
  return token || null;
}

async function runBootstrap(): Promise<AuthStatus> {
  try {
    const token = takeEntryToken();
    const res = token
      ? await fetch(`${BASE}/api/auth/exchange`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ token }),
        })
      : await fetch(`${BASE}/api/auth/session`, {
          method: "GET",
          credentials: "include",
        });
    if (res.ok) {
      const body = (await res.json()) as AuthResponse;
      if (body.authenticated === true && typeof body.csrf_token === "string") {
        setState("authed", body.csrf_token);
        return status;
      }
    }
  } catch {
    // 네트워크·파싱 실패는 잠금으로 처리한다(상세 사유는 노출하지 않음).
  }
  setState("locked", null);
  return status;
}

/** 모듈 단일 Promise — 여러 번 호출해도 진입(교환/세션 조회)은 1회만 수행한다. */
export function bootstrapAuth(): Promise<AuthStatus> {
  if (bootPromise === null) bootPromise = runBootstrap();
  return bootPromise;
}

export function useAuthStatus(): AuthStatus {
  useEffect(() => {
    void bootstrapAuth();
  }, []);
  return useSyncExternalStore(subscribe, getAuthStatus, getAuthStatus);
}
