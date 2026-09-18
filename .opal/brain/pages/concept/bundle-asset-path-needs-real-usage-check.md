---
type: concept
title: 컴포넌트 테스트 GREEN은 화면 부팅을 보장하지 않는다 — 번들 자산 경로는 실측으로만 잡힌다
tags:
- lesson
- verification
- frontend
- build
- real-usage
sources:
- task:143
related:
- green-tests-do-not-imply-contract-conformance
- fixture-vs-real-blind-spot-lesson
created: '2026-09-18'
updated: '2026-09-18'
status: draft
---
## 개요

백엔드 439건·프런트 153건 총 612건이 전부 GREEN인 상태에서 배포본 화면은 백지였다. `vite.config.ts`의 `base: './'`가 산출 `index.html`의 자산 참조를 `./assets/...`로 만들었고, `/docs/skills`는 Console에서 유일한 2단 경로라 브라우저가 `/docs/assets/...`로 해석했다. 그 경로는 SPA fallback이 HTML을 돌려주어 모듈 스크립트 MIME 검사에 걸렸다.

## 결정 배경 (WHY)

- 단위·통합 테스트는 컴포넌트를 **직접 마운트**한다. 번들러가 만든 `index.html`도, 자산 URL 해석도 그 경로에 들어오지 않는다. 컴포넌트 계약이 아무리 촘촘해도 부팅 실패는 잡히지 않는다.
- 회귀 단계는 `npm run build`의 **exit code만** 확인했다. 빌드는 성공했다. 실패한 것은 빌드가 아니라 산출물이 놓일 URL 공간과의 정합이었다.
- 1단 경로(`/tasks`, `/brain` 등)에서는 `./assets/`가 `/assets/`로 우연히 맞아떨어진다. 그래서 7개 화면이 멀쩡했고, 문제는 2단 경로가 처음 생긴 태스크 140부터 잠복했다.
- 140에서 드러나지 않은 이유는 검증이 **메뉴 클릭 진입**에 머물렀기 때문이다. 클라이언트 라우팅은 자산을 다시 받지 않는다. 화면이 보이므로 정상으로 판정됐고, URL 직접 접근은 시험되지 않았다.

## 결정 내용

- 새 라우트의 **경로 깊이가 기존과 달라지면** 번들 자산 해석이 달라질 수 있다고 보고, 그 라우트를 URL 직접 접근으로 1회 실측한다. 메뉴 클릭 확인은 이 검증을 대체하지 못한다.
- 빌드 검증은 exit code에서 멈추지 않고 **산출 `index.html`의 자산 경로 형태**를 단언 대상으로 삼는다. 서버 루트 SPA는 `/assets/...` 절대경로여야 한다.
- 컴포넌트 테스트 전건 GREEN은 "화면이 뜬다"의 근거가 아니다. 부팅·자산·라우팅은 real-usage 실측이 유일한 판정 수단이며, 설치본 실측 시나리오를 완료 기준에서 빼지 않는다.

## 영향 범위

번들러 산출물을 정적 서빙하는 모든 SPA 화면. 특히 라우트 깊이가 2단 이상으로 늘어나는 변경, `base` 설정을 상대경로로 둔 프로젝트.
