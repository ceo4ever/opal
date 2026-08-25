---
type: concept
title: 결정과 사실 주장의 분리 — 결정은 근거 판정 대상이 아니다
tags:
- evidence
- citation
- decision
- opds
sources:
- task:098
related:
- evidence-tier-asis-tobe-jurisdiction
- verdict-tool-fail-safe-direction-design
- clarification-gate
- handoff-contract-table-schema-mismatch
created: '2026-08-21'
updated: '2026-08-21'
status: draft
---
## 개요

TASK.md의 확정 서술을 "결정"(권한의 산물)과 "사실 주장"(틀릴 수 있는 것)으로 나누고, 결정은 근거 등급 판정 대상에서 제외한다. 결정은 소유자가 승인했다는 사실 자체가 근거이지 별도 인용을 요구할 대상이 아니다.

## 결정 배경 (WHY)

- (근거: task:098 DONE §1) 개정 전 TASK.md는 "소유자가 확정한 것"과 "누군가 주장한 사실"을 같은 무게로 취급했다. 이 둘은 성격이 다르다 — 결정은 권한 행사의 결과이고, 사실 주장은 실증으로 틀릴 수 있다.
- (근거: task:098 DONE §1) 구분이 없으면 근거 없는 사실 주장이 결정과 같은 확정 지위를 얻어 후속 설계의 전제로 굳어지는 문제가 있었다.
- (근거: task:098 DONE §3, 과잉 차단 대조군 S-17) 만약 이 구분 없이 근거 판정 규칙을 신설하면, 소유자의 새 요구사항(결정)까지 근거 부족으로 미확정 판정을 받아 강등되고 파이프라인 자체가 멈춘다.

## 결정 내용

- TASK.md "## 확정된 설계 방향" 항목에 `[결정]` / `[사실]` 접두 태그를 의무화한다.
- `[결정]` 태그 항목은 근거 없이도 확정 지위를 유지한다 — 근거 판정(state-tool `--evidence-check`)의 분모·분자 계산에서 애초에 판정 대상이 아니다.
- `[사실]` 태그 항목만 근거 등급 판정 대상이며, 근거가 미확보되거나 등급이 낮으면 미확정으로 계상된다.

## 영향 범위

TASK.md 작성 스키마, state-tool `--evidence-check`의 확정률 계산 로직. 이 구분이 없는 상태에서 근거 판정을 도입하면 결정 신설 자체가 구조적으로 막힌다는 것이 이 태스크의 핵심 발견이다.

## 관련 페이지

- [[evidence-tier-asis-tobe-jurisdiction]]
- [[verdict-tool-fail-safe-direction-design]]
- [[clarification-gate]]
- [[handoff-contract-table-schema-mismatch]] — `[결정]`/`[사실]` 유사 2계열 구분이 ANALYSIS§8 확정 입력 판정값에도 별도 맥락으로 재적용된 사례(근거: task:101 DONE.md §3.2)
