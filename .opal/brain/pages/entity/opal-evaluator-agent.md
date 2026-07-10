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
related:
- oppl-two-loop-orchestrator
- skill-opal-pilot-gc
created: '2026-07-10'
updated: '2026-07-10'
status: active
---

## 개요

소유자가 규모 있는 프로젝트를 oppl 2-루프로 완주시킬 때, 구현 이전 단계에서 산출물 명세를 심판하는 전담 평가 에이전트다. "생성자 ≠ 평가자" 원칙을 집행하기 위해 Executor·Planner와 분리된 신규 에이전트로 신설되었다.

## 책임 (WHAT)

- CONTRACT 등 설계 산출물의 루브릭절 심판 — 구현 전 명세 리뷰 게이트(G)에서 verdict(pass/fail)만 반환한다 (`opal/agents/opal-evaluator-agent/AGENT.md`)
- 동작 검증 중 명세 이탈(drift)이 발견되면 재콜백 대상이 된다
- readonly 계약 — 소스·산출물 mutate 금지, `changed_files`에는 자기 보고서만 포함 가능

## 설계 배경 (WHY)

- 검증을 Evaluator(구현 전 명세 심판)와 test-agent(구현 후 동작 검증)로 2원화해, 명세 이탈과 동작 결함을 서로 다른 계층에서 잡는다 (근거: task:056 TASK.md 확정 설계 결정4, PLAN.md F-004)
- checker 패턴 B(`tools: [Read, Grep, Glob, Bash]` readonly, `[WORKER]` 마커 시 부트스트랩 스킵, 외부 기준 문서를 Read해 자기완결 보고서 생성, 진단 전담·소스 수정 금지)를 그대로 계승한 3번째 적용 사례다 — 선례는 opal-convention-checker·opal-security-checker (근거: task:056 PLAN.md §2.4.2)
- TASK 제약① "Evaluator 외 신규 에이전트 금지"의 유일한 예외로 신설되었다 — 기존 컴포넌트 재사용 원칙 하에서 이 에이전트만 신규 생성이 승인되었다 (근거: task:056 TASK.md 제약①)
- 드라이런에서 세션 에이전트 레지스트리가 신규 에이전트 타입을 아직 인식하지 못하는 경우, general-purpose 에이전트에 AGENT.md를 인라인 주입해 계약(readonly·verdict-only)을 자기준수시키는 폴백 경로가 유효함이 실증되었다 (근거: task:056 AGENTIC-LOG.md #17)

## 관계 (HOW)

- [[oppl-two-loop-orchestrator]] — 설계 루프 D6(산출물 검토)·게이트 G(구현 전 명세 리뷰)에서 이 에이전트를 디스패치하는 오케스트레이터
- [[skill-opal-pilot-gc]] — checker 패턴 B(opal-convention-checker·opal-security-checker)가 정의된 선행 진단 오케스트레이터

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| AGENT.md | `opal/agents/opal-evaluator-agent/AGENT.md` | 명세 심판 verdict-only 에이전트 정의 |
