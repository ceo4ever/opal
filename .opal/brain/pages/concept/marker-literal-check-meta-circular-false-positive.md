---
type: concept
title: 마커 리터럴 검사의 메타-순환 오탐 — 표기 문맥 제거 전처리를 규칙과 함께 정의
tags:
- false-positive
- verification
- documentation
- scenario-gate
- task-095
sources:
- task:095
- task:034
related:
- state-tool-mock-guard-skill-false-positive
- scenario-prewrite-goal-series-track
- prewrite-self-confirming-triple-defense
- verification-command-4-standard
created: '2026-08-19'
updated: '2026-08-19'
status: draft
---
## 개요

마커 리터럴의 잔존 여부를 단순 문자열 검색으로 판정하면, 그 마커를 설명하는 문서 자신이 영구히 실패 판정을 받는다. 규칙 문서와 시나리오 문서 본문이 마커를 인용 표기로 담고 있기 때문이다. 판정 조건을 정의할 때 **표기 문맥 제거 전처리를 규칙과 함께 명시**해야 한다.

## 배경 (WHY)

- 선작성 트랙의 보강 완료 판정 첫 조건은 "보강 대기 마커 잔존 0건"이다. 그런데 마커는 HTML 주석 리터럴이고, 그 리터럴을 정의·설명하는 규칙 문서와 시나리오 문서 본문이 같은 문자열을 백틱 표기로 담는다(근거: task:095 PLAN.md §4.2 Step, DONE.md §6).
- 실측에서 최초 적용 태스크의 시나리오 문서 검색 결과 2건이 **전부 설명 문맥**이었다 — 실제 미보강 지점은 0건인데 판정은 실패로 나온다. 규칙이 자기 자신을 위반한 것으로 보이는 메타-순환 오탐이다(근거: task:095 PLAN.md §4.2, DONE.md §6).
- 동형 문제의 선례가 있었다. 코드 패턴 금지 가드가 표준 안내 문구에 등장한 단어를 오탐한 사건이며(→ [[state-tool-mock-guard-skill-false-positive]]), 인라인 백틱 구간을 제거한 뒤 검사하는 전처리로 해소됐다(`opal/tools/state-tool/state_tool.py:2010,2025`).

## 결정 내용

- 판정 조건 본문에 전처리를 의무화했다 — 각 줄의 인라인 백틱 구간을 제거한 뒤 검사한다. 작성 체크리스트 문항에도 같은 전처리를 병기했다(`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:64,236`).
- 선례 해법을 근거로 인용해 규칙과 구현이 같은 판정 규약을 쓰게 했다 — 코드펜스 내부는 원문 그대로 검사하고, 백틱이 닫히지 않은 줄은 구간을 제거하지 않는다(의심 시 검사 방향으로 안전 실패)(`opal/tools/state-tool/state_tool.py:2005-2030`).
- 사람 가독성용 산문 표기와 판정 기준 마커를 분리했다 — 판정은 주석 리터럴 기준이고 산문 표기는 병기이며, 둘은 보강 시 함께 제거한다(근거: task:095 TEST-SCENARIO.md §0 보강 이력 3).
- 일반 원칙: 규칙 문서가 자신이 집행하는 리터럴을 설명해야 하는 구조에서는, 리터럴 검사 규칙을 정의하는 **같은 자리에** 표기 문맥 제거 전처리를 함께 정의한다. 전처리 없는 리터럴 검사는 문서가 규칙을 설명할수록 더 강하게 실패한다.

## 영향 범위

- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:64,236` — 전처리 규정과 체크리스트 문항.
- `opal/tools/state-tool/state_tool.py:2005-2030` — 동형 전처리의 선례 구현(본 태스크에서 변경하지 않음).

## 관련 페이지

- [[state-tool-mock-guard-skill-false-positive]]
- [[scenario-prewrite-goal-series-track]]
- [[prewrite-self-confirming-triple-defense]]
- [[verification-command-4-standard]]
