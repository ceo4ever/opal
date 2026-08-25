---
type: concept
title: 승계 계약과 표 스키마의 불일치 — 원천 재지정으로 해소(스키마 확장 대신 분리)
tags:
- contract
- schema
- handoff
- verification-gap
- opd
sources:
- task:100
- task:101
related:
- analysis-drift-pm-cross-verify-lesson
- shared-ssot-procedure-artifact-role-split
- decision-vs-fact-claim-separation
created: '2026-08-24'
updated: '2026-08-24'
status: active
---
## 개요

규범이 "표를 승계하라"고 [MUST]로 요구해도, 실제 표의 스키마(열 구성)가 승계받는 쪽이 필요로 하는 필드를 애초에 담고 있지 않으면 승계는 실행될 수 없고 재도출이 발생한다(근거: task:100 DONE.md §6 S-33 Fail). 이 계약 불일치는 후속 태스크에서 **승계 원천을 나누는 방식**으로 해소됐다(근거: task:101 DONE.md §3.1, §4 결정 ⓑ 채택).

## 결정 배경 (WHY)

- (근거: task:100 DONE.md §6 S-33) 핸드오프 표 스키마가 `항목 | 확정값 | 근거` 3열인데, `plan-guide.md` 2.N.1이 승계 대상으로 요구하는 필드는 파일·6영역 라벨·변경 유형·순서였다 — 3열 표에는 애초에 이 필드들이 없다.
- 이는 행 수가 부족한 문제가 아니라 스키마(열 구성) 자체의 문제였다 — 행을 더 채워도 해결되지 않는다. baseline 8행도 동일한 스키마 결함을 그대로 갖고 있었다.
- 승계를 `[MUST]`로 요구하는 규범(plan-guide.md `:92`)과 승계 가능한 표의 실제 스키마가 서로 맞물리지 않는 계약 불일치였다.
- 해소 시점에 두 해법이 경합했다 — ⓑ 원천을 나누는 안(파일 맵은 ANALYSIS §1.1에서, 결정형 확정값은 §8에서 각각 승계)과 ⓒ §8 표의 열을 확장해 파일형·결정형 항목을 한 표에 같이 담는 안(근거: task:101 DONE.md §4 결정 행). ⓒ는 결정형·파일형을 한 표에 섞어 각 행에 다른 항목용 열이 공란으로 남는 **희소 표**를 만들고, `analysis-core.md` §5가 이미 소유한 6영역 축을 §8에서 다시 정의하는 꼴이 되어 SSOT 포인터 원칙과 충돌하므로 기각됐다(근거: task:101 DONE.md §4 결정 근거).

## 결정 내용

- **채택안 ⓑ — 승계 원천 2원 재지정**: 파일 맵(영역·경로·역할·변경 유형)은 ANALYSIS §1.1에서, 결정형 확정값(항목·확정값·근거)은 §8에서 각각 승계하도록 원천을 나눴다(근거: task:101 DONE.md §3.1 표).
- 부수 조치로 ANALYSIS §1.1 템플릿을 4열→5열로 확장(`영역` 선두 신설, `파일`→`경로`, `변경 필요`→`변경 유형`)해 PLAN이 열 순서 그대로 복사 승계할 수 있게 했다(근거: task:101 DONE.md §3.1, §4 결정 D-A).
- **일반화된 패턴**: "표를 승계하라"는 요구가 그릇 스키마와 맞지 않을 때, 스키마를 확장(이질적 항목을 한 표에 욱여넣기)하기보다 **승계 원천을 나누는 것**이 더 나은 해법일 수 있다. 스키마 확장은 희소 표를 만들고 기존 SSOT 축의 재정의를 유발하는 반면, 원천 분리는 각 표가 원래 소유한 스키마를 그대로 유지하면서 승계 지시문만 재지정하면 된다.
- (경과) 이 페이지는 애초에 불일치를 발견만 하고 두 방향(ⓐ 파일 맵 하위에 별도 표 신설 / ⓑ §1.1 직접 인용)을 후속 이월로 남겼었다(근거: task:100 DONE.md §8) — 후속 태스크가 ⓑ 계열 해법을 채택해 이를 해소했다.

## 영향 범위

단계 간 정보를 표·구조화 데이터로 승계시키는 모든 규범 설계. 승계 의무를 신설할 때 그 표의 열 구성이 승계 요구 필드를 실제로 포함하는지 대조하는 점검을 함께 넣어야 한다. 실제 개정 파일: `op-dev-analysis/SKILL.md`, `op-dev-plan/references/plan-guide.md`, `harness/analysis-core.md`, `opal-pilot-dev/references/pipeline.json`, `op-dev-qa/SKILL.md`(+qa-dev-guide.md) (근거: task:101 DONE.md §3.1 표).

## 관련 페이지

- [[analysis-drift-pm-cross-verify-lesson]]
- [[shared-ssot-procedure-artifact-role-split]]
- [[decision-vs-fact-claim-separation]]
