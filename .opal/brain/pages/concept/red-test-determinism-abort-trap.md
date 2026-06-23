---
type: concept
title: RED 테스트 결정론성 함정 — neverResolve fetch 대역의 abort 무반응
tags: [testing, red-first, determinism, abort, fetch-mock]
sources: [task:037]
related: [opal-console]
created: 2026-06-23
updated: 2026-06-23
status: active
---

## 개요

RED-first 테스트 작성 시 `neverResolve` fetch 대역(never-settling Promise)이 AbortController signal을 처리하지 않으면 테스트가 무한 행(hang)을 일으킨다. 테스트 자체가 결정론적이지 않아 워커 watchdog을 중단시키고 파이프라인 진행을 막는 함정.

## 결정 배경 (WHY)

- `api-timeout.test.ts`에서 `timeoutMs` 초과 후 AbortController abort를 검증하는 RED 테스트를 작성할 때, fetch mock이 `new Promise(() => {})` (neverResolve)로 구현되었다.
- `AbortController.abort()` 호출 시 mock이 abort signal에 반응하지 않아 Promise가 영구 pending 상태로 남았다.
- 결과적으로 vitest 타임아웃(959초)까지 테스트가 행, 워커 watchdog이 중단됐다.

## 결정 내용 (HOW)

**교정 방법**: fetch mock이 abort signal을 감지하고 `DOMException(AbortError)`를 throw하도록 변경.

```typescript
// 잘못된 패턴 (neverResolve + abort 무반응)
vi.stubGlobal('fetch', () => new Promise(() => {}));

// 올바른 패턴 (abort 반응 대역)
vi.stubGlobal('fetch', (_url: string, options?: RequestInit) =>
  new Promise((_resolve, reject) => {
    options?.signal?.addEventListener('abort', () => {
      reject(new DOMException('Aborted', 'AbortError'));
    });
  })
);
```

**핸들러 선부착 원칙**: abort 리스너를 Promise 생성 시점에 즉시 등록한다. 나중에 등록하면 abort가 먼저 발생했을 때 핸들러가 없어 여전히 행이 발생한다.

## 영향 범위

- 테스트 인프라 패턴: `dashboard/frontend/src/lib/api-timeout.test.ts` — abort 반응 대역 적용
- 원칙: **모든 시간 기반 abort 테스트는 fetch mock이 signal.addEventListener('abort', ...)를 등록해야 결정론적**

## 관련 페이지

- [[opal-console]]
