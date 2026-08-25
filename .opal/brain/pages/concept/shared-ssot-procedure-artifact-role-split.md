---
type: concept
title: 분석 코어 공유 SSOT — 절차와 산출물의 역할 분리
tags:
- ssot
- analysis-core
- role-separation
- architecture
- opd
sources:
- task:100
- task:101
related:
- new-ssot-pointer-not-value-copy
- template-precedence-over-prose-norms
- handoff-contract-table-schema-mismatch
created: '2026-08-24'
updated: '2026-08-24'
status: draft
---
## 개요

ANALYSIS·PLAN 두 단계가 공유하는 분석 절차를 단일 SSOT(`harness/analysis-core.md`)로 신설하고, "절차는 SSOT가 소유, 산출물 형식은 각 스킬이 소유"하는 역할 분리를 확정했다(근거: task:100 DONE.md §3.1).

## 결정 배경 (WHY)

- (근거: task:100 DONE.md §1) ANALYSIS와 PLAN이 지식 선조회·증분 소비·델타 탐색·분석 깊이·관련 파일 맵 등 동일한 분석 절차를 각자 서술하면서 중복·drift가 발생했다.
- (근거: task:100 DONE.md §3.2) 두 스킬의 가이드 문서(analysis-guide.md, plan-guide.md)에서 절차 서술 분량을 줄이고 SSOT 포인터로 대체했다(analysis-guide.md 163→108줄, plan-guide.md 477→459줄).

## 결정 내용

- 새 SSOT `opal/core/references/harness/analysis-core.md`(184줄)가 §1 지식 선조회 3단·§2 증분 소비 규율·§3 델타 탐색 규율·§4 분석 깊이 기준·§5 관련 파일 맵 6영역 축·§6 의존성·영향 범위 도출·§7 분석 품질 체크리스트를 단독 소유한다(근거: task:100 DONE.md §3.1).
- 절차 SSOT와 산출물 형식(각 스킬 SKILL.md의 템플릿)을 분리해, 절차가 바뀌면 SSOT 한 곳만 고쳐도 ANALYSIS·PLAN 양쪽 단계에 전파되도록 했다.
- 하네스 등록은 최상위 절 신설 없이 `opal-harness.md` §2 모듈 표 행 추가 + §2 하위 stub 서브섹션으로 처리했다 — 선례(QA 표준·인용 규칙)와 동형 배치이며, 기존 문서의 `opal-harness.md §N` 인용을 깨뜨리지 않기 위한 선택이다(근거: task:100 DONE.md §3.2, PLAN.md PD-2).
- **후속 정합(task:101)**: 이 SSOT(`analysis-core.md:59`)가 소유한 확정 입력 승계 지시를 §8 단독 소유에서 §1.1+§8 2원 소유로 재지정했다 — SSOT 문서 자체는 유지한 채, 그 문서가 지정하는 승계 경로만 조정한 사례다(근거: task:101 DONE.md §3.1). 계약 불일치의 구체적 해소 내용은 [[handoff-contract-table-schema-mismatch]] 참조.

## 영향 범위

`opal/skills/op-dev-analysis/`·`op-dev-plan/` 두 스킬 계열과 `opal-pilot-dev` 파이프라인의 ANALYSIS·PLAN 게이트. 분석 절차를 다루는 신규 스킬을 추가할 때도 이 SSOT를 참조해야 한다.

## 관련 페이지

- [[new-ssot-pointer-not-value-copy]]
- [[template-precedence-over-prose-norms]]
- [[handoff-contract-table-schema-mismatch]]
