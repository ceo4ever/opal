/**
 * @header {
 *   "module": "test-setup",
 *   "layer": "test",
 *   "domain": "test",
 *   "description": "@testing-library/jest-dom 매처를 vitest 전역에 등록 + happy-dom localStorage 폴리필. [T063] happy-dom의 기본 window.localStorage는 setItem/getItem이 미구현 상태(환경 제약)라 zustand persist 미들웨어(ui-store) import 시점에 TypeError가 발생 — 각 테스트 파일의 최초 import보다 먼저 실행되는 setupFiles 단계에서 in-memory Storage로 교체해 선점한다.",
 *   "exports": [],
 *   "task": "063",
 *   "changelog": ["2026-07-15 T063 R-8: localStorage 폴리필 추가 — RTL 테스트가 ui-store(zustand persist)를 import/mutate할 때 발생하던 'storage.setItem is not a function' 해소"]
 * }
 */
import '@testing-library/jest-dom'

// happy-dom localStorage 폴리필 — setItem이 없을 때만 in-memory Storage로 교체(정상 환경은 그대로 둠)
if (typeof window !== 'undefined' && typeof window.localStorage?.setItem !== 'function') {
  const store = new Map<string, string>()
  Object.defineProperty(window, 'localStorage', {
    configurable: true,
    value: {
      getItem: (key: string) => (store.has(key) ? store.get(key)! : null),
      setItem: (key: string, value: string) => {
        store.set(key, String(value))
      },
      removeItem: (key: string) => {
        store.delete(key)
      },
      clear: () => store.clear(),
      key: (index: number) => Array.from(store.keys())[index] ?? null,
      get length() {
        return store.size
      },
    },
  })
}
