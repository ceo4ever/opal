---
type: concept
title: 목표계열 선작성 트랙 — 도출 입력 2계열 분리와 게이트 계약 경계
tags:
- scenario-gate
- testing
- prewrite
- opd
- opds
- task-095
sources:
- task:095
- task:073
- task:075
related:
- 070-derivation-engine-perspective-bias-lesson
- scenario-goal-coverage-gate-loop
- scenario-normalized-contract-pilot-neutral
- opds-testscenario-producer-establishment
- test-scenario-pipeline-redesign
- prewrite-track-quality-not-efficiency-measurement
- prewrite-self-confirming-triple-defense
created: '2026-08-19'
updated: '2026-08-19'
status: draft
---
## 개요

시나리오 도출 입력을 두 계열로 갈라, 설계 문서(PLAN.md)에서 오는 입력을 기다리지 않고 태스크 정의(TASK.md)에서 오는 입력만으로 시나리오 절반을 먼저 도출하는 트랙이다. 설계 워커가 도는 동안 병렬로 착수하되, 설계 확정 후 나머지 계열을 보강하고 목표-커버 게이트를 1회 통과해야 종료된다. 강제가 아닌 선택 트랙이다.

## 결정 배경 (WHY)

- 애초 검토된 안은 "시나리오 작성과 구현을 병렬"이었으나 부적격 판정했다. 구현 워커가 시나리오 문서를 **완료 판정 기준**으로 소비하므로(`opal/skills/opal-pilot-dev/SKILL.md:131-134`) 병렬은 완료 기준을 사후에 만드는 것이고, 헌법이 이를 사후 합리화로 명시 금지한다(근거: `opal/core/PRINCIPLES.md` §1, task:095 DONE.md §1). 도구 층의 단계 전이 가드도 이를 이미 차단한다(`opal/tools/state-tool/state_tool.py:634`).
- 반면 "설계와 시나리오를 병렬"은 순서를 뒤집지 않고 **앞당기는** 방향이라 위반 지점이 없다(근거: task:095 DONE.md §1, TASK.md D-1·D-2).
- 실측하니 도출 입력이 이미 두 계열로 갈려 있었다 — 채택 관점(목표 문장·요구사항 전체·교체형 목표의 채택·잔존 기준)은 태스크 정의에서 오고, 파괴 관점(리스크 가설·기능 목록)만 설계 문서에서 온다(근거: task:095 PLAN.md §3.2.2 계열 매핑 표).
- **계약적 근거**: 게이트 정규화 계약에서 목표·요구사항은 태스크 정의 유래이고 기능·리스크 가설만 설계 문서 유래다(`opal/core/references/harness/scenario-gate.md` §3). 즉 루브릭 6축 중 4축(목표 달성·요구 커버·채택·잔존·경계·부정)은 설계 문서 없이 도출 가능하다 — 이 경계가 선작성 가능 범위의 계약적 근거다(→ [[scenario-normalized-contract-pilot-neutral]]).

## 결정 내용

- **2계열 분할**: 채택 관점 블록은 태스크 정의만 입력으로 쓰고 루브릭 ①목표달성·②요구커버·⑤채택·잔존·⑥경계·부정을 담당한다. 파괴 관점 블록은 설계 확정 후 리스크 가설·기능 목록을 입력에 추가하여 ③기능커버·④리스크커버를 보강한다(`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:21,34,48`).
- **선작성 구간 입력 제한**: 위 3종 밖의 입력을 쓰지 않으며 **설계 문서를 읽지 않는다** — 설계 관점 오염을 원천 차단하는 것이 트랙의 존재 이유다(`opal/core/references/harness/red-first.md:50`).
- **보강 없이 종료 금지**: 선작성 초안만으로 시나리오 작성을 끝낼 수 없고, 보강 완료 판정 3조건(보강 대기 마커 잔존 0건 · 리스크 가설 전건 전재 · 매핑 표의 가설·계층 전건 기재)을 충족해야 한다(`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:64`).
- **게이트는 보강 완료 후 1회**: 선작성 시점 호출은 금지된다 — 기능·리스크 가설 페이로드가 미확정이어서 결정론 축 판정이 불가하다(`opal/core/references/harness/scenario-gate.md:81`). 게이트 행을 조기 진행시키려는 시도는 단계 전이 가드가 거부한다(`opal/tools/state-tool/state_tool.py:634`).
- **선택 트랙(opt-in)**: 착수하지 않고 두 블록을 연속 수행해도 결과는 동등하며, 문서 전용 작업처럼 시나리오 문서 자체가 스킵되는 경로에서는 이 트랙도 자연 스킵된다. 착수 판단 기준은 "설계 워커 소요가 선작성 소요보다 길고, 목표가 파괴 관점으로 환원되지 않을 때"이며 **판단이 서지 않으면 순차가 기본**이다(`opal/core/references/harness/red-first.md:50` (f)).
- **규칙 1소유자 배치**: 트랙 정의는 강제 검증 트랙 규칙 문서가, 2계열 도출 절차는 시나리오 작성 가이드가, 게이트 호출 시점은 게이트 규칙 문서가 각각 단독 소유하고, 두 오케스트레이터 문서는 순서만 배선하며 규칙 본문을 0줄 갖는다(근거: task:095 PLAN.md §규칙 소유권 표, → [[governance-single-owner-rule-mapping]]).
- **공용 설계 워커 스킬 미접촉**: 여러 오케스트레이터가 공유하는 설계 워커 스킬은 건드리지 않고 오케스트레이터 2문서와 하네스 규칙에만 배선했다 — task:075가 확립한 원칙을 계승한 것이며 변경 0을 실측 확인했다(→ [[opds-testscenario-producer-establishment]]).

## 영향 범위

- `opal/core/references/harness/red-first.md:50` — 트랙 정의 SSOT(신설 절).
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:21` — 2계열 도출 절차 SSOT.
- `opal/core/references/harness/scenario-gate.md:81` — 게이트 호출 시점 규율.
- `opal/skills/opal-pilot-dev-short/SKILL.md:54` · `opal/skills/opal-pilot-dev/SKILL.md:74,97` — 배선(순서만). 현재 배선 범위는 이 두 파이프라인이며, 다른 오케스트레이터는 규칙 SSOT만 상속한다.
- 도구 코드·파이프라인 정의 변경 0 — 선작성은 파이프라인 행 밖 초안 작업으로 수행한다(근거: task:095 DONE.md §3).

## 관련 페이지

- [[070-derivation-engine-perspective-bias-lesson]]
- [[scenario-goal-coverage-gate-loop]]
- [[scenario-normalized-contract-pilot-neutral]]
- [[opds-testscenario-producer-establishment]]
- [[test-scenario-pipeline-redesign]]
- [[prewrite-track-quality-not-efficiency-measurement]]
- [[prewrite-self-confirming-triple-defense]]
