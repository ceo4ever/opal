---
type: concept
title: WBS 세분화 원칙 — 단일 책임 + 수용 시나리오 기준
tags:
- oppd
- wbs
- sizing
- be
- fe
- acceptance-scenario
sources:
- task:031
related:
- skill-opal-pilot-project-dev
- b7-action-completion-loop
- oppd-prd-trd-task-folder-promote
created: '2026-06-21'
updated: '2026-06-21'
status: active
---

## 개념 요약

oppd WBS의 액션 크기 기준을 "1~3일 분량"에서 "단일 책임 + 단일 수용 시나리오로 독립 검증 가능한 단위"로 교체. BE 원자 5종, FE 3계층(T0/T1/T2), 통합 액션 타입이 함께 도입됐다.

## 배경·문제 (WHY)

시간 기반 기준("1~3일")은 다개념 묶음 액션(화면 3개, BE 4책임 묶음)을 규칙 위반 없이 허용했다. 세분화 규칙 부재 → 독립 검증 불가 → 병렬성 제한 → 재작업 비용 증가. 수행 단위가 작을수록 명확해지고 완성도가 올라간다는 캡틴 원칙을 구조적으로 집행하기 위해 기준을 교체했다.

## 결정 내용 (HOW)

### 크기 기준 (공통)

단일 책임 + 단일 수용 시나리오로 독립 검증 가능한 단위. 둘 이상의 책임/수용 기준이 섞이면 재분할, 관찰 가능한 동작이 없는 헬퍼·타입 단독이면 흡수.

너무 큼 신호 → 재분할: 독립 책임 2+ / 독립 수용 기준 2+ / 단일 수용 시나리오 작성 불가.
너무 작음 신호 → 흡수: 관찰 가능한 동작이 없는 헬퍼·타입 단독.

### BE 원자 5종

모델·마이그레이션 / 엔드포인트 / 도메인 서비스 / 외부 연동 / 인증. 레이어 경계 = 액션 경계 (BE ≠ FE).

### FE 3계층 (T0/T1/T2)

T0 컴포넌트 설계(UI 계약 정의) → T1 공통 컴포넌트(병렬, UI킷 우선·2+ 화면 기준) → T2 화면 모듈(병렬). 소규모 예외(화면 ≤3) = T0/T1 생략 가능.

### 수용 시나리오 용어 계층

수용 시나리오(상위) = 자연어 완료 기준 + 기계적 검증 명령. 이것이 액션 TEST-SCENARIO.md(RED-first) 씨앗. 완료 기준·검증 명령(하위) = 수용 시나리오의 기계적 부분. generic 검증 명령(`npm run lint && npm test`) 금지.

### 통합 액션 타입

병렬 그룹 머지 후 "합쳐서 E2E 통과"를 책임지는 별도 채번된 액션. 병렬 그룹마다 1개 필수. 통합 ≠ 병렬 실행 방식.

### 병렬의 위치

병렬 = 세분화 DAG의 파생. "세분화↑ → 충돌↓ → 병렬↑" 인과. 병렬성이 1차 목표 아님.

## 영향·관계

- `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` — sizing 단일책임, 너무 큼/작음 기준, 수용시나리오 용어 계층, 통합 액션 타입, BE 원자 5종, FE 3계층, BE/FE 매트릭스, PM 검수 4종
- `opal/skills/opal-pilot-project-dev/SKILL.md` — §2-2 분할 원칙 #4 교체
- `opal/agents/opal-fe-agent/AGENT.md` — FE 3계층(T0/T1/T2) + 컴포넌트 API 계약
- `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` — §1 목적 재서술

교차참조: [[skill-opal-pilot-project-dev]], [[b7-action-completion-loop]], [[oppd-prd-trd-task-folder-promote]]

## 근거 출처

task:031 — DONE.md §캡틴 확정 결정 #2·#6·#7, PLAN.md §F-010~F-018
