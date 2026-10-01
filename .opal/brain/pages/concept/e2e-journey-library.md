---
type: concept
title: E2E 여정 라이브러리 — 승격된 여정·조각 자산
tags:
- e2e
- testing
- docs
sources:
- doc:docs/e2e/README.md
- doc:docs/proposals/archives/e2e-journey-fragment-library.md
related: [opal-e2e, test-tool]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

검증을 통과해 프로젝트 자산으로 승격된 E2E 여정(사용자 관점의 완결 흐름)과 여러 여정이 공유하는 재사용 조각을 보관하는 문서 폴더다. 각 문서 안의 YAML 한 벌이 계약 원본이며 테스트 도구가 그것을 직접 읽는다(`docs/e2e/README.md:3-7`).

## 현재 계약

- 조각은 식별자·매개변수·단계와 하나 이상의 사후 조건을 갖고, 입력값은 원문이 아니라 환경 변수 이름으로 선언한다. 여정은 조각을 참조만 하며 조각끼리는 중첩하지 않는다(`docs/e2e/README.md:9-12`).
- 펼쳐진 조각 단계는 회차가 붙은 고유 식별자를 받아 여정 본문 단계와 구분되고, 각 동작이 실행 기록 한 줄로 남는다(`docs/e2e/README.md:14-16`).
- 실행 산출물과 로컬 상태는 이 폴더가 아니라 Git에서 제외되는 프로젝트 `.e2e/` 아래에 둔다(`docs/e2e/README.md:18-19`).
- 태스크의 여정 초안은 같은 여정의 실행이 완전한 통과 증적을 남기고, 도구의 승격 자격 검사가 자격 있음을 낼 때만 이 폴더로 올라온다. 사람의 산문 판단이나 실패·불완전 실행은 근거가 아니다(`docs/e2e/README.md:23-32`).

## 관련 페이지

- [[opal-e2e]] — 여정 작성·실행 operator
- [[test-tool]] — 승격 자격 판정 소유
