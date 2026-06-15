/**
 * @header {
 *   "module": "ui-store",
 *   "layer": "store",
 *   "domain": "core",
 *   "description": "Zustand UI 상태 스토어 — 테마(다크/라이트/시스템, localStorage 영속) + 컨텍스트 프로젝트(URL 쿼리 동기)",
 *   "exports": ["useUiStore", "Theme"]
 * }
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "dark" | "light" | "system";

interface UiState {
  /** 현재 테마 설정 (localStorage 영속) */
  theme: Theme;
  /** 현재 선택된 컨텍스트 프로젝트 경로 (URL ?project= 쿼리와 동기) */
  contextProject: string | null;

  setTheme: (theme: Theme) => void;
  setContextProject: (project: string | null) => void;
}

/**
 * 테마를 실제 document에 적용한다.
 * - "dark"  → <html class="dark">
 * - "light" → <html class=""> (dark 제거)
 * - "system" → 시스템 prefers-color-scheme 따름
 */
function applyTheme(theme: Theme) {
  const root = document.documentElement;
  if (theme === "system") {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.classList.toggle("dark", prefersDark);
  } else {
    root.classList.toggle("dark", theme === "dark");
  }
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      theme: "dark",
      contextProject: null,

      setTheme: (theme) => {
        applyTheme(theme);
        set({ theme });
      },

      setContextProject: (project) => {
        set({ contextProject: project });
      },
    }),
    {
      name: "opal-console-ui",
      partialize: (state) => ({ theme: state.theme }),
      onRehydrateStorage: () => (state) => {
        // 앱 로드 시 저장된 테마 즉시 적용
        if (state?.theme) {
          applyTheme(state.theme);
        }
      },
    },
  ),
);
