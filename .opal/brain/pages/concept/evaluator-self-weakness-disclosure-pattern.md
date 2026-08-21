---
type: concept
title: 평가자에 PM 자기약점 명시 전달 + 신고사실 감점면제 금지 명문화
tags:
- lesson
- evaluator
- governance
- opds
sources:
- task:098
related:
- worker-role-boundary-exposes-pm-measurement-error
- measurement-tool-more-fallible-than-artifact-lesson
created: '2026-08-21'
updated: '2026-08-21'
status: draft
---
## 개요

평가자 프롬프트에 "워커가 스스로 신고했다는 사실만으로 감점을 면제하지 말라"를 명문화하고, PM이 자신의 약점(자기 판단에 자신 없는 지점)을 평가자에게 미리 명시 전달하면, 그중 실제 결함(gap)이 검출될 확률이 올라간다.

## 결정 배경 (WHY)

- (근거: task:098 DONE §6) 본 태스크에서 PM은 자기 약점 3건을 평가자에게 명시 전달했고, 그중 2건이 실제 gap으로 판정됐다.
- (근거: task:098 DONE §6) 평가자의 지적이 PM의 면제 근거를 정당하게 반박한 사례가 있었다 — "규칙 신설 태스크 내부에서는 자동 검증이 불가하다"는 PM의 일반화된 면제 주장은 특정 요구사항(R-6)에는 참이었지만 다른 요구사항(R-4 도구 집행)에는 거짓이었다. 이 태스크의 TASK.md 자체가 신 스키마를 적용할 수 있는 유일한 실파일이라 in-task 검증 경로가 이미 존재했기 때문이다.
- 과잉 일반화된 면제("이건 원래 검증 안 되는 종류다")는 검증 공백을 만든다 — 평가자가 그 일반화를 개별 항목 단위로 재검토해야 공백이 드러난다.

## 결정 내용

- 평가자 프롬프트에 "신고했다는 사실 자체가 감점 면제 사유가 되지 않는다"를 명문화한다 — 워커·PM이 스스로 한계를 인정했다고 해서 실제 결함 여부 판정을 건너뛰지 않는다.
- PM은 자신이 확신하지 못하는 판단·면제 주장을 숨기지 않고 평가자에게 명시적으로 전달한다 — 약점을 감추면 평가자가 검토할 대상 자체를 놓친다.
- 면제 주장이 나오면 그 주장을 요구사항 단위로 쪼개 재검토한다 — "이 종류는 검증 불가"라는 일반화가 모든 하위 항목에 똑같이 적용되는지 확인한다.

## 영향 범위

목표-커버 게이트·evaluator 디스패치 프롬프트 설계, PM의 완료 보고 작성 습관.

## 관련 페이지

- [[worker-role-boundary-exposes-pm-measurement-error]]
- [[measurement-tool-more-fallible-than-artifact-lesson]]
