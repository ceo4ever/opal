---
type: concept
title: 선작성 구간 self-confirming 퇴행 방어 3종 — 작성자 분리만으로는 불충분
tags:
- scenario-gate
- testing
- self-confirming
- prewrite
- task-095
sources:
- task:095
- task:004
related:
- test-scenario-pipeline-redesign
- scenario-prewrite-goal-series-track
- 070-derivation-engine-perspective-bias-lesson
- scenario-goal-coverage-gate-loop
- blind-reproduction-verification-test
created: '2026-08-19'
updated: '2026-08-19'
status: draft
---
## 개요

시나리오 선작성 구간은 입력이 태스크 정의(목표·요구사항·완료 조건)뿐이므로, 요구 조건을 그대로 옮긴 "당연한 시나리오"만 양산하는 자기확인 구조로 퇴행할 위험이 있다. 작성자를 설계 워커와 분리하는 기존 방어만으로는 불충분하다고 판정하고, 방어 3종을 규칙으로 고정했다.

## 결정 배경 (WHY)

- 자기확인 문제의 원인은 두 층이었다 — (i) 작성 주체가 설계 워커여서 자기 설계를 자기가 검증하는 구조 (ii) 도출 입력이 완료 조건 중심이어서 "당연한 시나리오"가 양산되는 구조(근거: task:004, → [[test-scenario-pipeline-redesign]]).
- 선작성 트랙은 (i)의 해법(작성자=PM과 소유자 페어)을 그대로 물려받지만 (ii)는 **오히려 강화된다** — 그 구간의 유일한 입력이 태스크 정의이기 때문이다(근거: task:095 PLAN.md §리스크 가설 표 H-a 판정).
- 따라서 "작성자 분리 유지만으로 충분한가"라는 물음에 **불충분**으로 답하고 추가 방어를 규칙화했다(근거: task:095 PLAN.md H-a, DONE.md §2).

## 결정 내용

- **방어 1 — 경계·부정 축 동시 도출 의무**: 채택 관점 블록은 목표·요구·채택 축뿐 아니라 ⑥경계·부정 축도 담당하므로, 각 요구사항의 경계값과 부정 경로(실패·거부·미충족 입력)를 요구사항별로 1회 이상 질의해 최소 1건을 산출한다. 경계·부정은 "당연한 시나리오"의 정반대 방향이므로 편향 상쇄로 작동한다(`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:41`).
- **방어 2 — 보강은 추가만으로 끝내지 않는다**: 설계 확정 후 보강 단계에서 선작성 초안의 각 시나리오를 리스크 가설·기능 목록과 대조하여 중복·과잉·설계와 어긋나는 시나리오를 **수정 또는 삭제**한다. 이것이 없으면 선작성 단계의 당연한 시나리오가 최종 집합에 그대로 잔존한다. 초안과 설계의 불일치는 그 자체가 조기 경보 신호로 PM 게이트에서 표면화한다(`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:61`).
- **방어 3 — 게이트를 최종 방어선으로 유지**: 목표-커버 게이트를 보강 완료 후 1회 호출하므로 채점 대상은 **최종 집합 전체**다. 선작성 초안이 게이트를 우회하는 경로는 존재하지 않으며 독립 평가자의 판단축 채점이 그대로 적용된다(`opal/core/references/harness/scenario-gate.md:81`, → [[scenario-goal-coverage-gate-loop]]).
- **실증**: 최초 적용 태스크의 보강 단계에서 실제로 초안 시나리오 1건을 정정하고 1건을 신설했으며, 요구 조건 되읽기형 비율이 과반 미달(6/16)임을 독립 평가자가 판정했다(근거: task:095 TEST-SCENARIO.md §0 보강 이력, SCENARIO-GATE-1.md).
- 일반 원칙: 자기확인 방어는 "누가 쓰는가"와 "무엇으로 도출하는가"가 별개 축이다. 작성자 분리는 전자만 고치므로, 입력이 좁아지는 구간에서는 입력 축 방어를 별도로 세워야 한다.

## 영향 범위

- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:41,61` — 방어 1·2의 정의 지점.
- `opal/core/references/harness/scenario-gate.md:81` — 방어 3(게이트 호출 시점 규율).
- 두 오케스트레이터 문서는 이 규칙들을 재서술하지 않고 순서만 배선한다(`opal/skills/opal-pilot-dev-short/SKILL.md:67` · `opal/skills/opal-pilot-dev/SKILL.md:97`).

## 관련 페이지

- [[test-scenario-pipeline-redesign]]
- [[scenario-prewrite-goal-series-track]]
- [[070-derivation-engine-perspective-bias-lesson]]
- [[scenario-goal-coverage-gate-loop]]
- [[blind-reproduction-verification-test]]
