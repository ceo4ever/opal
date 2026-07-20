---
type: concept
title: oppl 루프 액션 에이전트 내부 채널 opal-agent 전환 — 축×호출모드 이원화
tags:
- oppl
- executor
- opal-agent
- headless-channel
- session-continuity
- observability-boundary
sources:
- task:066
related:
- opal-loop-action-agent
- oppl-executor-delegation-architecture
- opal-agent-stream-json-passthrough
- oppl-run-record-journal-dual-observability
created: '2026-07-17'
updated: '2026-07-17'
status: active
---

## 개념 요약

루프 액션 에이전트가 내부 4축(생성자·Evaluator·test-agent·체커)을 디스패치하던 통로를 플랫폼 Agent 도구에서 opal-agent(claude 헤드리스 CLI) 채널로 전환한 설계 결정 묶음이다. 호출 방식은 단계별로 동기/비동기 이원화되며, 결과 수거는 파일 3종 분리 캡처로 결정론화된다.

## 배경·문제 (WHY)

기존 통로(Agent 도구)에서는 부모 턴 조기 종료·손자 보고 우회·생성자 세션 재개 불가 같은 관측 릴레이 마찰이 반복 관찰되었다 (근거: task:066 DONE.md 요약, PLAN§1.1). 별도 통로가 필요했던 이유는 헤드리스 프로세스가 결과 파일과 세션 ID를 통해 결정론적으로 완료·재개를 판별할 수 있어, 위 마찰을 구조적으로 제거하기 때문이다.

## 결정 내용 (HOW)

- **축(정체성)×호출모드(단계별) 직교 분리**: "누구를 부르는가"(축 — 생성자/Evaluator/test-agent/체커, 검증 2원화의 근거)와 "어떻게 부르는가"(호출모드 — 단계별 동기/비동기)를 별개 축으로 분리했다. 동일 test-agent축이 RED 단계에서는 비동기, GREEN 단계에서는 동기로 호출되는 것은 모순이 아니라 호출모드가 축이 아닌 단계 기준으로 결정되기 때문이다 (근거: task:066 PLAN§3.1.2 결정 R-A).
- **결과 파일 3-분리 캡처 규약**: 각 단계 실행 결과를 stdout(`result.json`)·stderr(`err.log`)·종료코드(`exitcode`) 세 파일로 나눠 캡처한다. 완료 마커는 `.exitcode` 파일의 존재 여부이며, 결과 본문(`result.json`)의 존재 여부로 완료를 판정하지 않는다 — 하드에러 시 표준출력이 완전히 비어 있을 수 있기 때문이다 (근거: task:066 PLAN§3.2.2 결정 R-I). 결과 스키마는 결정론 보장이 확인된 5개 필드(텍스트 결과·세션 ID·에러 여부·비용·소요시간)만 참조한다 (근거: task:066 PLAN§3.2.2 결정 R-H).
- **생성자 세션 연속성(cold prime → warm resume)**: 첫 단계 디스패치 전에 세션 ID를 미리 확정해 보존해 두고(cold prime), 이후 재개 단계에서 동일 ID로 세션을 이어 붙인다(warm resume). 이 방식은 첫 단계 결과 파싱 성공 여부와 무관하게 재개 명령을 미리 조립할 수 있게 한다 (근거: task:066 PLAN§3.3.2 결정 #8).
- **축별 권한(allowedTools) 표준화**: 각 축은 필요한 도구만 화이트리스트로 명시하고, 전체 권한을 우회하는 플래그는 사용하지 않는다 — 자동 실행 범위를 화이트리스트로만 제한한다 (근거: task:066 PLAN§3.4.2 결정 R-4, TASK.md §제약 조건).
- **관측성 경계 축소**: 기존 관측 규칙(행위주체 표시·아이콘 룩업)은 소유자(PM)가 Agent 도구로 디스패치하는 경우에만 적용된다. 루프 액션 에이전트 내부의 opal-agent 채널 디스패치는 이 규칙의 적용 대상이 아니며, 대신 결과 파일과 결과 요약으로 자체 관측성을 확보한다 (근거: task:066 PLAN§3.5.2 결정 #9).
- **1차 릴리스 범위**: 세션 재개를 포함한 전체 기능은 1차로 claude 채널에 한정하고, 다른 채널은 opal-agent 검증 상태가 올라가는 대로 점진 확대한다 (근거: task:066 PLAN§3.6.2 결정 R-6).

## 영향·관계

`opal/agents/opal-loop-action-agent/AGENT.md`(내부 디스패치 절 전면 재작성 본체), `opal/core/references/harness/observability.md`(관측성 적용 범위 명확화), `opal/core/references/opal-harness.md`(SSOT 포인터 보강), `opal/skills/opal-pilot-project-loop/SKILL.md`(디스패치 서술 정합 + test-agent축 귀속 정정)에 영향을 준다. 기존 위임 구조 결정([[oppl-executor-delegation-architecture]])이 정의한 4축 분리·결과 계약 6필드·blocked 7종 트리거·3-SSOT 경계는 이번 전환에서도 불변으로 유지된다 — 이번 결정은 "내부 축을 무엇으로 부르는가"가 아니라 "그 축을 어떤 통로로 어떻게 호출하는가"만 바꾼다.

- [[opal-loop-action-agent]] — 이 채널 전환이 적용되는 엔티티.
- [[oppl-executor-delegation-architecture]] — 4축·결과 계약 6필드 등 불변 유지되는 선행 결정.

## 근거 출처

task:066 — TASK.md §확정된 방향, PLAN.md §1.5/§3(결정 R-A, R-B, R-C, R-G, R-I, R-H, #8, R-4, #9, R-6), DONE.md 요약·완료기준 대조표.
