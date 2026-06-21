---
type: concept
title: B7 액션 완성도 루프 — triage 기반 경계 재설계 순환 구조
tags:
- oppd
- action-loop
- triage
- verification
- b7
sources:
- task:031
related:
- skill-opal-pilot-project-dev
- wbs-세분화-단일책임-수용시나리오
- loop-upper-bound-ssot-pattern
created: '2026-06-21'
updated: '2026-06-21'
status: active
---

## 개념 요약

oppd Phase 3의 액션 실행을 선형 6단계에서 triage 기반 경계 재설계 루프로 전환한 설계 결정. VERIFY 실패를 구현/설계/회귀 3종으로 분류해 계층별 라우팅하며, Guards 상한 내에서 성공까지 순환한다.

## 배경·문제 (WHY)

기존 선형 구조(PLAN→QA→TEST-SCENARIO→EXECUTE→VERIFY→TEST)는 VERIFY 실패 시 EXECUTE 코드 수정 루프만 허용하고 PLAN 회귀 경로가 없었다. 설계가 틀렸을 때 수렴이 불가능 — 설계 결함을 코드로만 두드리는 구조였다. "작게 → 명확 → 구현+테스트 → 완성도" 원칙을 구조적으로 보장하기 위해 재설계 루프가 필요했다.

## 결정 내용 (HOW)

### triage 3분류

| 분류 | 성격 | 신호 | 라우팅 |
|------|------|------|--------|
| 구현(impl) | 코드·로직 오류 | lint/build/test 실패 | EXECUTE 재시도 (fix 루프) |
| 설계(design) | 설계·아키텍처 이슈 | fix 한도 초과 후 자동승격 또는 에이전트 1차분류 | 3계층 라우팅 |
| 회귀(regression) | 기존 동작 파손 | regression 감지 | 즉시 중단 |

### 분류 주체

액션 에이전트 1차분류 + fix 한도초과 자동승격. 구현으로 1차 분류 후 fix 한도 초과 시 설계 수준 자동 승격. 분류 근거는 `verification_log`에 기록.

### 설계 실패 3계층 라우팅

| 계층 | scope | 소유권 | 처리 |
|------|-------|--------|------|
| 액션-로컬 | action | 에이전트 | 자율 재PLAN (재설계 루프) |
| WBS 수정 | wbs | PM | WBS 변경 2단 기준 적용 |
| TRD/PRD 변경 | trd | 사용자 | 항상 사용자 게이트 |

WBS 변경 2단 기준: scope·인터페이스 불변 조정 → PM 자율+AGENTIC-LOG / scope·기능 변경 → 사용자.

### 반환 신호

`failure_context.scope: action|wbs|trd` 신규 필드.

### 명명 구분

- **재설계 루프(PLAN 재진입)**: 이번 신설 — VERIFY 실패 → 설계 수준 재PLAN
- **PLAN 재지시(QA 피드백)**: 기존 유지 — QA 게이트 Needs Revision 시 1회

루프 상한(N=2)은 `opal/core/references/opal-harness.md` §1 자동 루핑 제약 표 SSOT 단독 기재, 타 문서 포인터만.

## 영향·관계

- `opal/agents/opal-task-action-agent/AGENT.md` — B7 경계 재설계 루프, triage, 1차분류+자동승격, 3계층 라우팅, scope 반환, WBS/TRD 직접수정 금지 가드
- `opal/skills/opal-pilot-project-dev/SKILL.md` — Phase 3 scope 분기, WBS 2단 기준, TRD/PRD 게이트, STATE 재설계 루프 로그
- `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` — triage 3분류, §3-5 QA scope별 분기, §7 PLAN 재진입 포인터
- `opal/core/references/opal-harness.md` — §1 자동 루핑 제약 표 PLAN 재진입 행 신설

교차참조: [[skill-opal-pilot-project-dev]], [[wbs-세분화-단일책임-수용시나리오]], [[loop-upper-bound-ssot-pattern]]

## 근거 출처

task:031 — DONE.md §캡틴 확정 결정 #3·#4·#5, PLAN.md §F-020~F-027
