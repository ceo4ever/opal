---
type: concept
title: 부작용 관측이 실행-시간 검증을 자동화한다
tags:
- verification
- testing
- skill-wizard
- task-114
sources:
- task:114
related:
- negative-scenario-requires-3-condition-and
- negative-control-proves-verification-not-weakened
- scenario-goal-coverage-gate-loop
created: '2026-09-09'
updated: '2026-09-09'
status: draft
---
## 개요

문서·절차형 산출물(마크다운 스킬 등)은 「규칙이 쓰여 있는가」만 정적으로 검사하기 쉽다. 그러나 그 절차가 실제로 수행하는 행동이 파일시스템 변화로 나타나는 경우, 「무엇이 생겼는가 / 생기지 않았는가」를 검사하는 것만으로 실행-시간 검증이 자동화된다.

## 결정 배경 (WHY)

(근거: task:114 DONE.md §3) 태스크 114의 목표-커버 게이트 1회차에서 Evaluator가 "문서에 규칙이 쓰여 있다"와 "설치 절차가 실제로 그렇게 행동한다"를 구분하지 못한다고 지적했다. 이 간극에 대해 Evaluator는 사용자 수동 확인(M3) 승격을 제시했으나, 절차의 행동이 결국 파일시스템 변화(설치 여부, 레지스트리 파일 생성 여부, 전역 자산 변화 여부)로 나타나므로 그 변화를 기계로 관측하면 M1 자동화로도 실행-시간 검증이 성립한다는 반론이 채택되어 ⑤축 판정이 1 → 2로 상향됐다.

## 결정 내용

- 검증 대상 절차가 파일시스템에 남기는 흔적을 사전/사후 스냅샷으로 비교해 관측한다.
- 가장 강한 형태는 **긍정+부정 관측의 짝**이다 — 「의도한 변화가 일어났다」(설치 성립)와 「의도하지 않은 변화는 일어나지 않았다」(전역 자산 무변화)를 함께 검사해야 절차가 정확한 경계 안에서 동작했다는 증거가 완성된다.
- 이 방법론은 M3(수동 확인) 대비 재현 가능하고 회귀 감지가 되는 이점이 있다 — 사람의 눈이 아니라 스냅샷 diff가 판정 근거가 되기 때문이다.

## 영향 범위

- 부작용 관측은 「없다」만으로 판정하지 않는다는 원칙([[negative-scenario-requires-3-condition-and]])과 짝을 이룬다 — 부작용 부재는 3조건 중 하나일 뿐, 그 자체로 게이트 성공을 증명하지 못한다.
- 파일시스템 변화를 남기는 모든 절차형 스킬·워커의 시나리오 설계에 재사용 가능한 검증 방법론이다.

## 관련 페이지

- [[negative-scenario-requires-3-condition-and]]
- [[negative-control-proves-verification-not-weakened]]
- [[scenario-goal-coverage-gate-loop]]
