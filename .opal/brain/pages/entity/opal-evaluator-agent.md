---
type: entity
title: opal-evaluator-agent
source_ref: opal/agents/opal-evaluator-agent/AGENT.md
tags:
- agent
- checker
- verification
- oppl
sources:
- task:056
- task:170
- task:172
related: [oppl-two-loop-orchestrator, skill-opal-pilot-gc, op-scenario-gate-skill, design-gate-gaps-resolution-roundtrip, design-gate-scope-parallel-judgement-combine, agent-effort-policy-inherit-by-default, real-invocation-scenario-limit, evaluator-eval-set-label-fixture-measurement-lesson]
created: '2026-07-10'
updated: '2026-10-01'
status: active
---
## 개요

소유자가 규모 있는 프로젝트를 oppl 2-루프로 완주시킬 때, 구현 이전 단계에서 산출물 명세를 심판하는 전담 평가 에이전트다. "생성자 ≠ 평가자" 원칙을 집행하기 위해 Executor·Planner와 분리된 신규 에이전트로 신설되었다.

## 책임 (WHAT)

- CONTRACT 등 설계 산출물의 루브릭절 심판 — 구현 전 명세 리뷰 게이트(G)에서 verdict(pass/fail)만 반환한다 (`opal/agents/opal-evaluator-agent/AGENT.md`)
- 동작 검증 중 명세 이탈(drift)이 발견되면 재콜백 대상이 된다
- **`scope` 분리(task:172)**: `design-rubric` phase 입력에 `scope`(`design`/`scenario`/`all`)를 받아 설계 4축 또는 시나리오 3축만 판정할 수 있다. 부분 결과는 `design-gate combine`이 결정론으로 합쳐 단일 판정과 같은 형식을 만든다. 시나리오 가이드가 실호출을 한정하면서, 기록된 결과 파일로 같은 계약을 증명할 수 있는 실호출 시나리오는 `cheaper_layer` 권고로 지적한다 ([[design-gate-scope-parallel-judgement-combine]], [[real-invocation-scenario-limit]]).
- **model·effort 고정(task:172)**: `model: advanced`(opus) + `effort: low`. 1차 평가 세트 측정 뒤 소유자가 `medium`으로 정했다가, 라벨을 가린 재측정과 fixture 결손 보정 측정(ADD-3·4) 결과를 보고 `low`로 바꿨다 ([[agent-effort-policy-inherit-by-default]], [[evaluator-eval-set-label-fixture-measurement-lesson]]).
- readonly 계약 — 소스·산출물 mutate 금지, `changed_files`에는 자기 보고서만 포함 가능
- **`design-rubric` phase의 gaps 해소 보고 왕복(task:170)**: opd·opds PM 경로 설계 게이트에서 `design-rubric` phase 입력에 `previous_gaps`(있을 때만 — 직전 유효 회차의 design+scenario 합산 gaps)를 받으면, 출력에 그 안의 모든 id마다 `resolved_gaps`(`[{id, status(resolved|unresolved), reason}]`) 원소를 정확히 1개씩 채워 반환해야 한다. gaps 항목은 `{axis}-{n}: {위치} — {남은 선택}` 포맷([MUST])을 따른다(상세: [[design-gate-gaps-resolution-roundtrip]]).

## 설계 배경 (WHY)

- 검증을 Evaluator(구현 전 명세 심판)와 test-agent(구현 후 동작 검증)로 2원화해, 명세 이탈과 동작 결함을 서로 다른 계층에서 잡는다 (근거: task:056 TASK.md 확정 설계 결정4, PLAN.md F-004)
- checker 패턴 B(`tools: [Read, Grep, Glob, Bash]` readonly, `[WORKER]` 마커 시 부트스트랩 스킵, 외부 기준 문서를 Read해 자기완결 보고서 생성, 진단 전담·소스 수정 금지)를 그대로 계승한 3번째 적용 사례다 — 선례는 opal-convention-checker·opal-security-checker (근거: task:056 PLAN.md §2.4.2)
- TASK 제약① "Evaluator 외 신규 에이전트 금지"의 유일한 예외로 신설되었다 — 기존 컴포넌트 재사용 원칙 하에서 이 에이전트만 신규 생성이 승인되었다 (근거: task:056 TASK.md 제약①)
- 드라이런에서 세션 에이전트 레지스트리가 신규 에이전트 타입을 아직 인식하지 못하는 경우, general-purpose 에이전트에 AGENT.md를 인라인 주입해 계약(readonly·verdict-only)을 자기준수시키는 폴백 경로가 유효함이 실증되었다 (근거: task:056 AGENTIC-LOG.md #17)
- `design-rubric` phase의 rewrite 지적 7회 중 6회가 `decision_clarity` 축 실패로 반복됐으나, 다음 회차가 이전 지적을 실제로 해소했는지 보고하는 구조가 없어 PM이 무엇을 채워야 하는지 지적에서 바로 알기 어려웠다 — `previous_gaps`/`resolved_gaps` 왕복 계약과 gaps 포맷 표준화로 이를 보완했다(근거: task:170 TASK.md). 설계 4축·시나리오 3축의 판정 기준·반복 상한 3회 자체는 바뀌지 않았다.

- scope 분리 병렬 판정은 기본 경로로 유지되지만 실측에서 시간 이득이 확인되지 않았다(단일 호출 평균 96.1초, 병렬 쌍 벽시계 평균 91.8초). 이득은 이전 지적 조립과 결합의 결정론화에 있다 (근거: task:172 DONE.md 한계). S-13에서 설치된 evaluator가 `pass-161`을 병렬 한 쌍으로 판정해 `fail`을 낸 원인은 추가작업에서 분리됐다 — 지배 요인은 fixture 경로·receipt 이름의 사례 라벨이었고(라벨 경로 5/5 pass, 중립 경로 11/11 fail), 라벨을 가리면 세 후보 모두 pass 사례를 뒤집었다. 평가 세트 fixture에 참조 파일 REQUEST.md가 빠진 결손도 뒤집힘에 기여했다 (근거: task:172 ADD1-S13-REVIEW.md, EVAL-RESULT-4·5).

## 관계 (HOW)

- [[oppl-two-loop-orchestrator]] — 설계 루프 D6(산출물 검토)·게이트 G(구현 전 명세 리뷰)에서 이 에이전트를 디스패치하는 오케스트레이터
- [[skill-opal-pilot-gc]] — checker 패턴 B(opal-convention-checker·opal-security-checker)가 정의된 선행 진단 오케스트레이터
- [[op-scenario-gate-skill]] — opd·opds PM 경로에서 `design-rubric`/`scenario-rubric` phase로 이 에이전트를 디스패치하고 `previous_gaps`/`resolved_gaps` 완전성을 검증하는 컨트롤 스킬
- [[design-gate-scope-parallel-judgement-combine]] — task:172 scope 분리·결합 계약
- [[agent-effort-policy-inherit-by-default]] — task:172 effort 정책
- [[design-gate-gaps-resolution-roundtrip]] — task:170 gaps 해소 보고 왕복 계약 상세

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| AGENT.md | `opal/agents/opal-evaluator-agent/AGENT.md` | 명세 심판 verdict-only 에이전트 정의 |
