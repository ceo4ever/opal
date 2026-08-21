---
type: concept
title: 실행 관측 인용은 스코프 병기 필수 — 단일파일 vs 디렉토리 수치 상이
tags:
- lesson
- measurement
- citation
- opds
sources:
- task:098
related:
- measurement-tool-more-fallible-than-artifact-lesson
- evidence-tier-asis-tobe-jurisdiction
created: '2026-08-21'
updated: '2026-08-21'
status: draft
---
## 개요

실행 관측(E1급 근거)을 인용할 때 관측 스코프(무엇을 대상으로 실행했는지)를 함께 적지 않으면, 같은 시점·같은 대상을 관측한 결과라도 수치가 서로 달라 보인다.

## 결정 배경 (WHY)

- (근거: task:098 DONE §5·§6) 같은 테스트 스위트를 단일 파일로 실행한 결과(324 passed)와 디렉토리 전체로 실행한 결과(341 passed)가 13건 차이를 보였다. 두 수치 모두 같은 시점의 정당한 관측이지만 스코프가 다르다.
- (근거: task:098 DONE §6) 이 스코프 차이를 명시하지 않고 회귀 기준선을 인용하면, 다른 스코프의 수치를 서로 대조해 "회귀가 발생했다"거나 "회귀가 없다"고 잘못 판단할 위험이 있다.
- (근거: task:098 DONE §3 ADD-1) 이 문제가 반복 관측되어 §9 E1 조항에 "관측 스코프·명령 병기 의무"로 승격됐다.

## 결정 내용

- 실행 관측 결과를 인용할 때는 결과 수치와 함께 **실행 스코프(대상 경로 범위)**와 **실행 명령**을 병기한다.
- 회귀 비교는 반드시 같은 스코프의 수치끼리만 대조한다 — 스코프가 다른 두 수치를 직접 비교하지 않는다.

## 영향 범위

`citation-rules.md` §9 E1 조항. 테스트 회귀 판정·목표-커버 게이트 등 실행 결과를 근거로 삼는 모든 산출물 서술.

## 관련 페이지

- [[measurement-tool-more-fallible-than-artifact-lesson]]
- [[evidence-tier-asis-tobe-jurisdiction]]
