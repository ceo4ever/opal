---
type: concept
title: 설계 게이트 gaps 해소 보고 왕복 계약 (previous_gaps/resolved_gaps)
tags:
- design-gate
- evaluator
- op-scenario-gate
- gaps-contract
sources:
- task:170
- task:172
related: [opal-evaluator-agent, op-scenario-gate-skill, design-gate-deterministic-pretier-separation, design-gate-scope-parallel-judgement-combine]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

설계 게이트 evaluator의 `design-rubric` 판정에 이전 회차 rewrite 지적(gaps)의 해소 여부를 다음 회차가 명시적으로 보고하게 하는 왕복 계약(`previous_gaps`/`resolved_gaps`). gaps 항목 포맷과 id 정의를 표준화해 "이전 회차에서 무엇을 채워야 하는지"를 기계적으로 추적 가능하게 했다.

## 결정 배경 (WHY)

(근거: task:170 TASK.md) evaluator rewrite 7회 중 6회가 `decision_clarity` 축 실패였다. 다음 회차가 이전 지적을 실제로 해소했는지 보고하는 구조가 없어, PM이 무엇을 채워야 하는지 지적에서 바로 알기 어려운 경우가 반복됐다. (근거: task:170 PLAN.md Decisions) scope 분리(`scope: design`/`scope: scenario` 병렬 디스패치) 시도 3회차 동안 previous_gaps/resolved_gaps의 id·echo·측정단위 관련 모순이 반복 재발해, scope 분리 자체는 범위에서 제외하고 이 gaps 해소 보고 계약만 기존 단일 `design-rubric` 호출 안에서 구현하기로 결정했다(AGENTIC-LOG #9).

## 결정 내용

- gaps 항목 포맷을 신규 작성분에 의무화한다: `{axis}-{n}: {위치} — {남은 선택}`(정규식 `^[\w_]+-\d+: .+ — .+`), `n`은 같은 축 안에서 1부터 시작하는 카운터. 설계 4축·시나리오 3축의 통과선·척도는 바꾸지 않으며 gaps 텍스트 표현 방식에만 적용된다.
- gaps id 정의(신규·레거시 포맷 공통 단일 규칙): "문자열에서 첫 번째 `: ` 앞부분 전체. `: `가 없으면 전체 문자열이 id다." 콜론 없는 레거시 gaps나 혼합 접두부 사례도 이 한 줄 규칙으로 예외 없이 계산된다.
- `previous_gaps` 조회 규칙: `op-scenario-gate`가 `design_gate.history`를 최신부터 역순 순회해, verdict가 `deterministic_fail`·`input_error`·`superseded`가 아닌 **가장 최근** 회차의 `run/design-gate-i{k}.json`에서 design+scenario 합산 gaps를 가져온다. 그 회차 파일이 없으면 더 이전 회차를 계속 보되, **그 회차의 gaps 배열이 비어 있으면 순회를 멈추고 생략한다**(더 이전 회차로 거슬러 올라가지 않는다) — "빈 gaps = 그 시점에 더 보고할 지적이 없다"로 의미를 확정했다.
- evaluator(`opal-evaluator-agent`)의 `design-rubric` phase 입력에 `previous_gaps`(있을 때만)를 추가하고, 출력(Phase 4 결과 계약)에 `resolved_gaps`(`[{id, status(resolved|unresolved), reason}]`)를 추가한다. 기존 `design`/`scenario`/`verdict`/`rewrite_target`/`advisories` 구조는 그대로 유지한다(scope 분기·결과 계약 교체 없음).
- 완전성 검증: `resolved_gaps`의 id 집합이 보낸 `previous_gaps`의 id 집합과 정확히 같아야 한다. 다르면 `op-scenario-gate`가 응답 수신 직후(단일 호출이므로 scope별 분기 없이 응답 1개만 확인) `--verdict input_error`로 기록한다 — 포맷 모호성이 아니라 실제 누락 신호이므로 완화하지 않는다.

## 후속 변경 (task:172)

- 위 결정은 scope 분리를 범위에서 제외했으나 task:172가 `scope` 분리와 `design-gate combine`을 도입했다 ([[design-gate-scope-parallel-judgement-combine]]).
- `previous_gaps` 조회·조립은 PM이 아니라 `state-tool design-gate start`가 한다. 응답이 `previous_gaps`·`previous_gaps_by_scope`·`previous_gaps_iteration`을 싣는다. 조회 규칙(최신부터 역순, `deterministic_fail`·`input_error`·`superseded` 제외, 빈 gaps면 생략)과 id 정의는 그대로이며 구현 주체만 바뀌었다 (근거: task:172 DONE.md AC-3).

## 영향 범위

`opal/agents/opal-evaluator-agent/AGENT.md`(§입력 명세 `previous_gaps`, gaps 포맷 [MUST], Phase 4 결과 계약 `resolved_gaps` 필드 추가), `opal/skills/op-scenario-gate/SKILL.md`(§6.1 ②previous_gaps 조회·전달, ③ 앞 resolved_gaps id-완전성 검증). evaluator의 다른 4개 phase(design-review/spec-review/drift-recheck/scenario-rubric 자체의 판정 기준)와 반복 상한 3회는 무변경.

## 관련 페이지

- [[opal-evaluator-agent]]
- [[op-scenario-gate-skill]]
- [[design-gate-deterministic-pretier-separation]]
- [[design-gate-scope-parallel-judgement-combine]]
