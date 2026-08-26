---
type: concept
title: 서로 다른 시계 계열을 직접 비교하면 캐시가 상시 무효화된다
tags:
- cache
- clock
- bug
- opal-console
- lesson-learned
sources:
- task:103
related:
- opal-console
- measurement-tool-more-fallible-than-artifact-lesson
created: '2026-08-26'
updated: '2026-08-26'
status: draft
---
## 개요

만료 판정과 파일 변경 판정을 한 캐시 안에서 다루면서 서로 다른 시계 계열의 값을 직접 비교하면, 비교식이 항상 참이 되어 캐시가 **상시 무효화**된다 (근거: task:103 PLAN.md P-8, `dashboard/backend/cache.py:29`).

## 결정 배경 (WHY)

- 캐시는 두 가지 축으로 무효화된다 — 저장 후 일정 시간이 지났는가(만료)와, 원본 파일이 그 사이에 바뀌었는가(변경)다.
- 만료 축은 프로세스 시작 이후 경과를 재는 단조 시계를 쓰고, 파일 변경 시각은 절대 시각(epoch)으로 온다.
- 변경 판정의 기준값을 만료 축의 파생값으로 잡으면 절대 시각이 단조 시계 값보다 항상 크므로, 원본 파일을 지정한 항목은 매 조회마다 무효화된다.
- PM이 실측으로 확증했다 — 단조 시계 609,212 대 파일 시각 1,781,516,662 (근거: task:103 state.json 행 7 PLAN PM Gate 비고).

## 결정 내용

- 저장 시각을 만료용 단조 시계와 별도로 **절대 시각으로 함께 보관**하고, 파일 변경 판정은 그 값과만 비교한다(`dashboard/backend/cache.py:51`).
- 두 축의 시계를 분리해 두면 만료 판정은 단조 시계의 장점(시스템 시각 변경에 흔들리지 않음)을 유지하면서 변경 판정만 절대 시각으로 맞출 수 있다(`dashboard/backend/cache.py:27`).
- 공개 시그니처·만료 시간·키 전략은 손대지 않고 내부 저장 구조만 확장했다 (근거: task:103 state.json 행 7).

## 영향 범위

시간을 다루는 모든 캐시·재시도·타임아웃 로직. 한 모듈이 두 종류의 시각을 함께 쓰면, 어떤 값이 어느 계열인지 저장 구조에서 구별되게 두어야 하며 계열이 다른 값끼리 비교하는 식은 결함으로 본다.

## 관련 페이지

- [[opal-console]]
- [[measurement-tool-more-fallible-than-artifact-lesson]]
