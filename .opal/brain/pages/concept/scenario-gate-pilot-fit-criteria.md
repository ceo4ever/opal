---
type: concept
title: 목표-커버 게이트 pilot 접합 판정 기준
tags:
- scenario-gate
- pilot-fit
- tool-gated
- self-confirming
- task-075
sources:
- task:075
related:
- scenario-goal-coverage-gate-loop
- scenario-normalized-contract-pilot-neutral
- op-scenario-gate-skill
- oppl-coverage-conformance-axis-split
- 070-derivation-engine-perspective-bias-lesson
created: '2026-07-23'
updated: '2026-07-23'
status: draft
---
## 개요

목표-커버 게이트를 어느 pilot에 접합할지는 pilot마다 판정이 다르다. 판정 기준은 "그 pilot이 이미 독립 평가·도구-게이트를 갖고 있는가"와 "접합 지점이 오케스트레이터 표면에 노출돼 있는가"다. task:075 확산 검토에서 5개 pilot을 이 기준으로 분류해 opd·opds·opsdd 3종에 접합하고, oppl은 제외 확정, oppd는 별도 태스크로 분리했다.

## 결정 배경 (WHY)

- 목표-커버 게이트의 핵심 가치는 "담당자가 스스로 통과를 선언하지 못하도록 독립 평가자를 끼워 self-confirming을 차단"하는 데 있다(근거: `opal/core/references/harness/scenario-gate.md` §6, [[scenario-goal-coverage-gate-loop]]). 따라서 이미 독립 평가자와 도구-게이트를 보유한 pilot에 게이트를 또 얹으면 커버리지 중복·SSOT 훼손만 남는다(근거: task:075 TASK.md §배경).
- 반대로 작성·검증·통과 판정을 한 주체가 모두 수행하던 pilot일수록 게이트가 메우는 공백이 크다 — 정확히 그 약점을 겨냥해 접합해야 가치가 높다(근거: task:075 TASK.md §배경 opsdd 행).
- 070 사건에서 핵심 목표 검증 시나리오가 도출조차 안 된 채 완료 처리된 선례가 접합 우선순위의 근거다(근거: task:075 TASK.md §배경, [[070-derivation-engine-perspective-bias-lesson]]).

## 결정 내용

pilot별 판정을 세 범주로 나눈다.

- **접합(1차)** — opd·opds: 마크다운 시나리오 산출물을 쓰고 설계 워커가 흡수 작성하는 동형 구조라 접합 난도가 가장 낮다. opds의 접합 지점(PLAN 단계에서 작성자가 직접 시나리오를 쓰는 지점)은 opd의 그것과 동형이다(근거: task:075 TASK.md §배경 opds 행).
- **접합(고가치)** — opsdd: REVIEW가 작성·검증·통과 판정을 한 주체(PM 자기검증)로 수행하는 self-confirming + 수동 커버리지 구조였다. 게이트가 독립 평가자와 결정론 커버리지 판정으로 이 약점을 정면으로 메우므로 가치가 높다(근거: task:075 TASK.md §배경 opsdd 행, DONE.md §2 R-3).
- **제외 확정** — oppl: 이미 backlog 커버리지-체크·시나리오 적합성 도구-게이트 + 독립 평가자를 산출 기반으로 보유한다. 게이트를 얹으면 3중 커버리지와 SSOT 훼손이 발생하므로 접합하지 않는다(근거: task:075 TASK.md §배경 oppl 행, [[oppl-coverage-conformance-axis-split]]).
- **별도 태스크로 분리** — oppd: 자율·무인 실행이라 게이트 가치는 가장 높으나 접합 지점이 오케스트레이터 표면이 아니라 액션 에이전트 내부 파이프라인이라 접합 복잡도가 크다. 1차 확산 범위에서 분리해 독립 태스크로 판정했다(근거: task:075 TASK.md §배경 oppd 행, DONE.md §5).

## 영향 범위

- task:075에서 접합 판정에 따라 편집된 대상: `opal/skills/opal-pilot-dev-short/SKILL.md`(opds), `opal/skills/opal-pilot-sdd/SKILL.md`·`opal/skills/opal-pilot-sdd/references/verify-guide.md`(opsdd).
- oppl·oppd 파이프라인은 이 판정에 따라 무변경으로 남겼다.
- 이 기준은 접합 확산이 이어질 때 재사용되는 판정 규칙이다.

## 관련 페이지

- [[scenario-goal-coverage-gate-loop]]
- [[scenario-normalized-contract-pilot-neutral]]
- [[op-scenario-gate-skill]]
- [[oppl-coverage-conformance-axis-split]]
- [[070-derivation-engine-perspective-bias-lesson]]
