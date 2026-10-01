---
type: concept
title: opal-e2e — E2E 여정 operator 스킬
tags:
- e2e
- testing
- skill
sources:
- skill:opal-e2e
related: [test-tool, e2e-candidate-order-and-fidelity-ownership, e2e-cmux-first-playwright-fallback]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

프로젝트 E2E 여정과 재사용 조각을 설정·작성·실행·조회하는 operator 스킬이다. 단계 파이프라인과 워커 디스패치는 없고, 실행·판정·승격 자격은 테스트 도구가 소유하며 이 스킬은 명령을 호출하고 결과를 해석만 한다(`opal/skills/opal-e2e/SKILL.md:4`, `:17-19`).

## 현재 계약

- 모드는 환경 설정(setup)·여정 작성(author)·실행(run)·조회(status) 네 가지이며, 가져오기(import) 모드는 없다(`opal/skills/opal-e2e/SKILL.md:23-31`).
- 환경이 준비되지 않았으면 작성·실행 전에 환경 설정을 먼저 안내한다(`opal/skills/opal-e2e/SKILL.md:37`).
- 환경 설정은 도구의 읽기 전용 검토로 표면 후보를 찾고, 부족하면 프로젝트 정의 문서의 구성 절에서 추정하되 "추정"과 근거 위치를 표시한다. 이 추정은 스킬 층의 해석이며 도구는 결정론으로 남는다(`opal/skills/opal-e2e/SKILL.md:39-45`).

## 관련 페이지

- [[test-tool]] — E2E 실행·판정 소유
- [[e2e-candidate-order-and-fidelity-ownership]]
- [[e2e-cmux-first-playwright-fallback]]
