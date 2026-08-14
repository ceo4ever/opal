---
type: concept
title: 조건부 산출물은 존재 게이트 대상이 아니다
tags:
- gate-design
- verification
- artifact
- task-091
sources:
- task:091
related:
- pm-gate-artifact-tool-enforcement
- expected-total-as-reference-not-gate-criterion
- silent-render-failure-deterministic-gate
created: '2026-08-14'
updated: '2026-08-14'
status: draft
---
## 개요

어떤 산출물이 "특정 조건을 만족할 때만 생성되도록" 정의돼 있다면, 그 산출물의 부재를 기계적으로 확인하는 게이트에 그대로 넣으면 안 된다. 조건이 애초에 성립하지 않아 산출물이 없는 정상 상태와, 조건이 성립했는데 만들지 않은 위반 상태를 도구가 구분할 수 없기 때문이다.

## 결정 배경 (WHY)

- (근거: task:091 DONE.md §2 미결-1) 컨벤션 자동 진단 보고서는 "대상이 1건 이상일 때만" 만들어지는 산출물이다(`opal/skills/opal-pilot-dev/SKILL.md:201` 외 3곳). 이런 산출물을 존재 게이트에 그대로 넣으면, 대상이 0건이라 정상적으로 만들지 않은 태스크마저 영구히 게이트를 통과하지 못하게 된다.
- (근거: task:091 DONE.md §2 미결-1) 또 다른 항목인 "변경된 파일 목록"은 애초에 파일 경로가 아니라 논리적인 개념이었다 — 진행 갱신 도구는 git 변경 이력을 조회하는 기능이 없어 그 자체로 존재를 확인할 방법이 없었다.

## 결정 내용

- 존재 게이트에 넣을 수 있는 항목은 고정된 경로이거나, 정해진 두 가지 형태의 와일드카드(글롭) 패턴뿐이다. 조건부로만 생성되는 산출물이나, 파일이 아닌 논리적 개념은 이 자리에 넣지 않는다.
- 그런 항목은 삭제하는 대신 사람이 확인하는 체크리스트로 옮긴다 — 원문 표현은 그대로 보존하고, 판별을 도구가 아니라 사람에게 맡긴다.
- 판별 기준: "이 산출물이 없는 것이 정상일 수 있는가?"에 그렇다고 답할 수 있으면 존재 게이트에서 제외한다. 결정론 검사는 "있어야 하는데 없으면 항상 위반"인 항목에만 쓴다.

## 영향 범위

산출물 존재를 기계적으로 확인하는 모든 게이트 설계에 적용된다. 산출물 목록을 게이트로 승격시키기 전에, 그 목록 안에 조건부 항목이나 비-경로 개념이 섞여 있는지 먼저 감사해야 한다.

## 관련 페이지

- [[pm-gate-artifact-tool-enforcement]]
- [[expected-total-as-reference-not-gate-criterion]]
- [[silent-render-failure-deterministic-gate]]
