/**
 * @header {
 *   "module": "test-setup",
 *   "layer": "test",
 *   "domain": "test",
 *   "description": "@testing-library/jest-dom 매처를 vitest 전역에 등록 + happy-dom localStorage/navigator.clipboard 폴리필. happy-dom의 기본 window.localStorage는 setItem/getItem이 미구현 상태(환경 제약)라 zustand persist 미들웨어(ui-store) import 시점에 TypeError가 발생 — 각 테스트 파일의 최초 import보다 먼저 실행되는 setupFiles 단계에서 in-memory Storage로 교체해 선점한다. navigator.clipboard도 happy-dom에서 getter-only 상속 프로퍼티라 `Object.assign(navigator, { clipboard })` 형태의 테스트 대역이 'has only a getter' TypeError로 실패한다(T140 W-8, DocsDetailPage 예시 복사 테스트) — configurable 프로퍼티로 재정의해 각 테스트가 자유롭게 clipboard.writeText를 대역할 수 있게 한다.",
 *   "exports": [],
 *   "task": "063"
 * }
 */
import '@testing-library/jest-dom'

// happy-dom navigator.clipboard 폴리필 — getter-only 상속 프로퍼티를 configurable/writable로 재정의
if (typeof navigator !== 'undefined') {
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    writable: true,
    value: (navigator as { clipboard?: unknown }).clipboard ?? {},
  })
}

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
