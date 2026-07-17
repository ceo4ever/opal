---
type: concept
title: oppl 실행자 위임 구조 — 태스크 단위 컨텍스트 격리
tags:
- oppl
- executor
- delegation
- context-isolation
- ssot-boundary
- blocked-contract
sources:
- task:065
related:
- opal-loop-action-agent
- oppl-two-loop-orchestrator
- oppl-3-ssot-tool-gated-separation
- oppl-scenario-red-confirmed-gap
created: '2026-07-17'
updated: '2026-07-17'
status: active
---

## 개념 요약

oppl Loop 2의 태스크 내부 파이프라인(T1~T5+G)을 태스크당 1회 디스패치되는 일회용 실행자(`opal-loop-action-agent`)에 위임하기로 한 설계 결정 묶음. 목적은 태스크당 노미널 3~4회였던 PM 개입을 결과 보고 1건으로 압축해, 소유자(PM)의 롱런 워크플로우 컨텍스트 누적을 태스크 단위로 격리하는 것이다.

## 배경·문제 (WHY)

기존 oppl은 생성자(T1 설계+T2 시나리오) → Evaluator(G) → 생성자 재개(T3) → test-agent(T4a) 순으로 PM이 직접 지휘하는 "하이브리드 C" 구조였다. 백로그가 태스크 10~20개 규모면 PM 컨텍스트가 포화되고, 플랫폼 자동 요약(compaction)이 태스크 진행 중간에 발생하면 판단 품질이 저하되는 문제가 있었다 (근거: task:065 TASK.md §배경). oppd(`opal-task-action-agent`)·opsdd(`opal-sdd-action-agent`) 선례는 중간층 실행자가 하위 워커를 재디스패치하고 PM은 디스패치 1회 + 결과 1건만 받는 구조가 이미 검증되어 있었다.

## 결정 내용 (HOW)

- **계층 구조**: PM은 L0 태스크 선택·L∞ 관찰·done-check·사람 게이트·소유자 보고를 유지하고, 태스크 내부(T1~T5+G)만 실행자에게 위임한다. 실행자는 태스크 1개 수명의 일회용 인스턴스다 — 상주형 부-PM은 누적 문제를 실행자로 이전할 뿐이므로 배제한다.
- **내부 디스패치 토폴로지 4축 분리**: 생성자(T1/T3)·Evaluator(G)·test-agent(T2 RED/T4a GREEN)·컨벤션·보안 체커(T4b)를 각각 별도 에이전트로 내부 디스패치하여 생성자≠평가자(H-9)를 유지한다.
- **3-SSOT 도구 호출 경계**: 실행자는 `test-tool scenario-*`만 호출하고, `backlog-tool`·`state-tool`은 호출하지 않는다 — 백로그(L∞)와 STATE는 PM 단독 갱신 오너십으로 남긴다.
- **CONTRACT drift 경계**: 실행자는 `CONTRACT.md`를 직접 수정하지 않는다. 계약 미접촉은 정상 진행하되, 계약 갱신이 필요한 drift를 감지하면 blocked로 반환하고 PM이 오너십 계층 분류·반영·에스컬레이션을 수행한다.
- **검증 2원화 순서 강행**: G(구현 전, Evaluator)는 항상 T3 이전에 완료되어야 하며, T4a(구현 후, test-agent)는 T3 완료 후에만 진입한다. 순서 증거는 QA-SPEC.md(G) 시점 < test-scenario.json result 존재(T4a) 시점으로 남긴다. `scenario-lock`이 `red_not_confirmed`를 반환하면 G 진입을 거부해 self-confirming RED를 차단한다.
- **재시도 상한 SSOT 비복제**: 실행자 문서는 하네스 §1 자동 루핑 제약 표를 참조만 하고 구체 수치를 복제하지 않는다.
- **blocked 반환 트리거 7종**: 비가역 행동 요구, 에스컬레이션 대상, 계약 갱신 필요 drift, 무진전 감지, 반복 상한 초과, 하드블로커(순서 역전·SSOT 손상·readonly 위반), decision_required(용어 불일치). 실행자는 소유자에게 직접 에스컬레이션하지 않고 PM이 수행한다.
- **결과 계약 6필드**: `{task_id, verdict, scenario_results, changed_files, done_md_path, blockers}`.
- **실행자 직접 갱신 금지 대상**: STATE.md(PM에게 위임), CONTRACT.md(계약 갱신 drift는 blocked).

## 영향·관계

`opal/agents/opal-loop-action-agent/AGENT.md`(신규 실행자 정의), `opal/skills/opal-pilot-project-loop/SKILL.md`(태스크 내부 파이프라인·디스패치 절이 실행자 위임 구조로 개편, v1.2), `opal/skills/opal-pilot-project-loop/references/loop-control.md`(§3 예산 관찰 단위가 "실행자 1회 디스패치" 기준으로 정합, v1.1), `opal/skills/opal-pilot-project-loop/references/contract.md`(§4에 실행자 CONTRACT drift 경계 문단 추가, v1.1)에 영향을 준다. `opal/skills/opal-pilot-project-loop/references/verification.md`는 순서 불변 규칙이 주체 중립(PM/실행자 동일 적용)이라 무변경이다. `docs/PROJECT.md`/`docs/ARCHITECTURE.md`의 Project Loop 컴포넌트 표·구조도에도 실행자 계층이 반영되었다.

- [[opal-loop-action-agent]] — 이 결정으로 신설된 실행자 엔티티.
- [[oppl-two-loop-orchestrator]] — 실행자를 디스패치하는 상위 오케스트레이터.
- [[oppl-3-ssot-tool-gated-separation]] — 3-SSOT 경계가 참조하는 선행 개념.
- [[oppl-scenario-red-confirmed-gap]] — RED-first self-confirming 차단 로직과 연결되는 선행 개념.

## 근거 출처

task:065 — TASK.md §확정된 설계 방향·명확화 결과, PLAN.md §1.5 M-1~M-13, DONE.md 요약.
