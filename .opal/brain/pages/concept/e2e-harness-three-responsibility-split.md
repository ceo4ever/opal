---
type: concept
title: 범용 E2E 하네스 — 3책임 분리와 실행 profile
tags:
- e2e
- harness
- proposal
sources:
- doc:docs/proposals/archives/opal-e2e-harness.md
related: [test-tool, opal-e2e, e2e-journey-library, e2e-candidate-order-and-fidelity-ownership]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

OPAL의 E2E를 브라우저 자동화가 아니라 "공개 진입점에서 실제 시스템 결과까지 이어지는 사용자 목표 검증"으로 정의하고, 이를 위한 하네스 계약을 정한 적용완료 제안서다. 구현 태스크 9건이 모두 끝났고, 규범 원문은 테스트 도구 문서·계약 모듈과 아키텍처 문서가 소유한다(`docs/proposals/archives/opal-e2e-harness.md:13-15`, `:27`).

## 핵심 결정

- 책임을 셋으로 나눈다. 검증 대상 소스 트리에서 서버를 띄우고 상태·포트·로그를 관리하는 대상 시스템 하네스, 요구의 실제 표면에 맞는 실행 방식을 고르는 시나리오 조정자, 동작·확인·증적을 수행하는 실행자다(`docs/proposals/archives/opal-e2e-harness.md:29-31`).
- 실행 방식은 브라우저·API·혼합·사람 협업·수동 다섯 가지이며, API 방식은 브라우저를 설치하지 않고 협업 방식은 사용자 응답 대기 상태를 보존한 채 같은 실행을 재개한다(`docs/proposals/archives/opal-e2e-harness.md:33-39`, `:52`).
- 브라우저는 Orca 관리 세션 → cmux 소유 화면 → 독립 agent-browser → Playwright(호환용) 순으로 고르며, Orca와 독립 agent-browser는 같은 드라이버의 세션 소유 방식 차이로 본다(`docs/proposals/archives/opal-e2e-harness.md:41-50`).
- 후속 설계(여정·조각 라이브러리)는 별도 제안서가 이었다(`docs/proposals/archives/opal-e2e-harness.md:16`).

## 관련 페이지

- [[test-tool]] — E2E 실행 계약 소유
- [[opal-e2e]] · [[e2e-journey-library]]
- [[e2e-candidate-order-and-fidelity-ownership]]
