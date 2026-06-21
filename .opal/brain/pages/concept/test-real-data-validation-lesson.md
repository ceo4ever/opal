---
type: concept
title: TEST 실데이터 검증이 build-only 가 놓친 결함을 발견한다
tags: [testing, lesson, test-strategy, real-data]
sources: [task:023]
related: [deploy-artifact-verification-lesson, opal-console, kanban-current-stage-derivation]
created: 2026-06-16
updated: 2026-06-16
status: active
---

## 개요

pytest + `npm run build` (build-only)가 모두 통과한 후에도, 실데이터로 실렌더를 검증하는 TEST 단계에서 결함이 추가로 발견된 사례. 실데이터 기반 검증은 build-only 검증이 커버하지 못하는 결함 유형을 찾아낸다.

## 결정 배경 (사례)

태스크 023 — OPAL Console 칸반 파이프라인 UX 개선:

- pytest (신규 12테스트 포함) GREEN, ruff clean, `npm run build` tsc 0에러 통과
- 그러나 실데이터(태스크 152) 실렌더에서 **진행중 카드가 미시작 `CLOSE`를 현재 단계로 표기**하는 결함 발견
- 원인: 파생 규칙이 "첫 미완료 행"을 current_stage로 사용 → 아직 도달하지 않은 `CLOSE(pending)`이 선택됨
- 또한 `na`/`skipped` status를 집계에서 미고려하는 결함도 실데이터에서 확인

build-only 단계에서는 실데이터의 `na`/`skipped` 조합이 테스트 픽스처에 포함되지 않았으므로 결함이 통과됨.

## 교훈

| 검증 방식 | 발견 가능 결함 | 발견 불가 결함 유형 |
|---------|-------------|-----------------|
| build-only (pytest + tsc) | 명시된 픽스처 케이스 / 타입 오류 | 실데이터 특유 status 조합(na/skipped 혼재) / 파생 규칙 엣지케이스 |
| TEST 실렌더 (실데이터) | 실데이터 특유 조합 / 파생 규칙 결과 시각 확인 | — |

**원칙**: 파생·집계 로직이 있는 경우, 실데이터로 L3(실렌더) 검증을 수행한다. pytest 픽스처만으로는 실운영 데이터의 다양한 status 조합을 모두 커버할 수 없다.

## 영향 범위

- TEST 단계 실렌더 검증 전략 (TEST-SCENARIO.md L3 항목)
- 파생/집계 로직을 포함하는 모든 BE 변경에 적용

## 관련 페이지

- [[deploy-artifact-verification-lesson]]
- [[opal-console]]
- [[kanban-current-stage-derivation]]
