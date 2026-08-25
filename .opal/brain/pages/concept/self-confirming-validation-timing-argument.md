---
type: concept
title: 자기확인 검증의 시점 논거 판별 — 개정 대상 무변경 확인으로 순환 논증을 잡는다
tags:
- self-confirming
- verification
- evaluator
- scenario-gate
- opd
sources:
- task:101
related:
- prewrite-self-confirming-triple-defense
- blind-reproduction-verification-test
- template-precedence-over-prose-norms
- measurement-tool-more-fallible-than-artifact-lesson
created: '2026-08-24'
updated: '2026-08-24'
status: draft
---
## 개요

"개정된 규범이 지시 없이도 행동을 만드는가"라는 주장은, 그 규범을 이미 반영한 상태에서 만들어진 산출물을 근거로 스스로 증명할 수 없다 — 산출물이 규범을 따른 것이 규범 자체의 재현력 때문인지, 규범을 미리 알고 있었기 때문인지 구분되지 않는 순환 논증(self-confirming)이 되기 때문이다(근거: task:101 PLAN.md §C-4, SCENARIO-GATE-1.md).

## 결정 배경 (WHY)

- (근거: task:101 DONE.md §5 #2) PLAN이 "L3(배포본 재현 검증) 불요 — 본 태스크의 ANALYSIS.md·PLAN.md 자체가 규범이 지시 없이도 재현된 실증 사례"라고 주장했으나, 목표-커버 게이트의 독립 평가자가 이를 기각했다.
- 기각 근거는 **시점 논거**였다 — 개정 대상인 6개 문서가 그 산출물(ANALYSIS.md·PLAN.md)이 작성된 시점에 **전건 무변경** 상태였다(근거: task:101 DONE.md §5 #2, §6 회귀 항목). 즉 그 산출물은 아직 존재하지 않는 규범을 따를 수 없었으므로, 개정 후 규범이 만들어낸 행동의 증거가 될 수 없다.
- 이는 규범이 지시 없이 재현되는지를 다루는 [[template-precedence-over-prose-norms]]와 같은 질문 계열이지만, 이 페이지는 그 질문의 **답을 판별하는 방법**(시점 논거)에 초점을 둔다.

## 결정 내용

- self-confirming 검증 여부를 판별하려면, 산출물의 생성 시점에 그 산출물이 검증하려는 규범이 **이미 반영돼 있었는지**를 먼저 확인해야 한다 — 개정 대상 파일이 그 시점 기준으로 무변경이었다면, 그 산출물은 해당 규범의 재현 증거로 채택할 수 없다.
- 유효한 검증은 규범이 실제로 반영된 이후, 그 규범을 별도로 주입받지 않은 새 컨텍스트의 워커가 독립적으로 재생성한 산출물을 대조하는 방식이어야 한다 — 표준 프롬프트로 1회 재생성해 대조한 방식이 이 조건을 충족한 선례다(근거: 관련 페이지 [[template-precedence-over-prose-norms]] 타 태스크 재확인 절).
- 이 기준이 적용된 결과, 해당 태스크 자체도 L3 검증(배포본 재현 대조 3건)을 미실행 상태로 유지했다 — 재배포 이후 표준 프롬프트로 재생성해 대조해야 한다는 과제가 후속으로 남았다(근거: task:101 DONE.md §8 미수행 1).

## 영향 범위

목표-커버 게이트·PLAN 단계의 검증 계층(L1~L3) 존폐 판단, "규범이 행동을 만드는가"류 주장을 다루는 모든 검증 시나리오 설계. 산출물의 생성 시점과 규범의 반영 시점 사이의 선후 관계를 먼저 확인하는 절차가 필요하다.

## 관련 페이지

- [[prewrite-self-confirming-triple-defense]]
- [[blind-reproduction-verification-test]]
- [[template-precedence-over-prose-norms]]
- [[measurement-tool-more-fallible-than-artifact-lesson]]
