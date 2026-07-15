/**
 * @header {
 *   "module": "ui-store",
 *   "layer": "store",
 *   "domain": "core",
 *   "description": "Zustand UI 상태 스토어 — 테마(다크/라이트/시스템, localStorage 영속) + 컨텍스트 프로젝트(URL 쿼리 동기) + 브레인 이탈가드 플래그(brainDirty, 비영속 — BrainPage가 turns.length>0일 때 true로 노출해 AppShell 프로젝트 스위처가 전환 전 확인 다이얼로그를 띄우도록 함, R-8)",
 *   "exports": ["useUiStore", "Theme"],
 *   "task": "063",
 *   "changelog": ["2026-07-15 T063 R-8: brainDirty/setBrainDirty 추가 — 프로젝트 스위처 이탈 가드용, partialize 미포함(비영속)"]
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
  /** 브레인 화면에 진행 중 대화(turns.length>0)가 있는지 여부 — 비영속. 프로젝트 스위처 이탈 가드에 사용 (R-8) */
  brainDirty: boolean;

  setTheme: (theme: Theme) => void;
  setContextProject: (project: string | null) => void;
  setBrainDirty: (dirty: boolean) => void;
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
      brainDirty: false,

      setTheme: (theme) => {
        applyTheme(theme);
        set({ theme });
      },

      setContextProject: (project) => {
        set({ contextProject: project });
      },

      setBrainDirty: (dirty) => {
        set({ brainDirty: dirty });
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
