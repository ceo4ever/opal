# TASK: Harness State Gate — 상태 관리 강제화

> 작성일: 2026-04-07 | 스킬: //opp

## 적용 스킬

`opal-pilot-project (opp)` — 문서 수정 태스크

## 배경

현재 하네스는 Gate 구조(QA Gate, Artifact Gate, PM Gate)를 통해 산출물 품질을 강제하지만,
STATE.md 갱신은 각 스킬/오케스트레이터의 자율에 맡기고 있다.
분석 결과, opd/opds/opdw/opp 스킬에서 단계별 STATE.md 갱신 명시가 없고,
세션 복원도 oppd를 제외한 모든 스킬에 없다.

PM은 산출물 품질만 검토하고, 상태 전이는 암묵적으로 처리되어
"이전 상태 미갱신 → 다음 단계 진행" 가능한 허점이 있다.

## 분석 결과 (2026-04-07 대화 기반)

### 파일럿 스킬 파이프라인 & Gate 구조

| 스킬 | 단계 | Gate 구조 |
|------|------|-----------|
| **opd** | TASK → ANALYSIS → PLAN+TS → EXECUTE | 각 단계: QA Gate → Artifact Gate → PM Gate |
| **opds** | TASK → PLAN+TS → EXECUTE | PLAN/EXECUTE: QA → Artifact → PM Gate |
| **opdw** | TASK → WIREFRAME → EXECUTE | WIREFRAME/EXECUTE: QA → PM Gate |
| **opp** | TASK → PLAN → EXECUTE | PLAN/EXECUTE: QA → Artifact → PM Gate |
| **opsdd** | TASK → SPEC → SPEC-VERIFY → SPEC-PLAN → TASKS → TASKS-VERIFY → EXECUTE-LOOP → DONE | Phase별 이중 Gate |
| **opwt** | TASK → [ANALYSIS] → PLAN → EXECUTE → QA | ANALYSIS: PM 자가체크, PLAN/EXECUTE(배치별): QA→PM |
| **oppd** | 사전체크 → TASK 생성 → Phase1(opwt) → Phase2(WBS) → Phase3(action) | Phase별: PM 검수→사용자 확정 |

### STATE.md 관리 현황

| 스킬 | 도메인 치환값 | 단계별 갱신 명시 | 세션 복원 | 구조 예시 |
|------|--------------|----------------|----------|----------|
| opd | ✅ | ❌ (harness 의존) | ❌ | ❌ |
| opds | ✅ | ❌ (harness 의존) | ❌ | ❌ |
| opdw | ✅ | ❌ (harness 의존) | ❌ | ❌ |
| opp | ✅ | ❌ (harness 의존) | ❌ | ❌ |
| opsdd | ✅ + 전용 구조 | ✅ (EXECUTE-LOOP만) | ❌ | ✅ |
| opwt | ✅ + 네트워크 확장 | ✅ (각 단계 명시) | ❌ | ❌ |
| oppd | ✅ + 병렬 State | ✅ (병렬 그룹 추적) | ✅ | ✅ |

**핵심 문제**: harness §3에 STATE.md 갱신 이벤트 테이블(8개 이벤트)이 있지만,
이를 **강제**하는 메커니즘이 없다. Gate는 산출물 품질을 검증하지만 State 전이는 각 스킬 자율.

### 누락/불일치 항목

1. **STATE.md 단계별 갱신 미명시** — opd/opds/opdw/opp: 도메인 치환값만 있고 갱신 시점 지시 없음
2. **세션 복원 메커니즘 누락** — oppd만 존재, 나머지 6개 스킬 없음
3. **TASK 단계 STATE.md 초기화 암묵적** — opwt/oppd만 명시, 나머지는 harness §3에 위임
4. **QA 스킬 도메인 매핑 불완전** — harness-interactive §2 테이블: dev/범용만 있고 opsdd/opwt 누락
5. **opdw Agentic Mode 없음** — opd/opds/opp/opsdd에는 있지만 opdw 누락
6. **opsdd 세션 복원 없음** — 7단계로 가장 긴 스킬임에도 불구

## 목표

1. **State Gate 신설**: 모든 단계 시작/완료 시 STATE.md 갱신을 Gate 수준으로 강제한다.
   이전 상태가 갱신되지 않으면 다음 단계 진입을 명시적으로 금지한다.
2. **PM 상태 관리 최종 책임자 지정**: PM이 State Gate를 소유하고, 갱신 여부를 검증하며,
   미갱신 시 진행을 차단하는 조율·통제·감독 역할을 하네스에 명시한다.
3. **공통화**: 6개 pilot 스킬(opd/opds/opdw/opp/opsdd/opwt)에서 STATE.md 갱신 의무를
   하네스 공통으로 일관 적용한다. 세션 복원 절차도 공통 정의한다.
4. **QA 도메인 테이블 확장**: harness-interactive §2에 opsdd/opwt 누락 항목 추가.

## 요구사항

- [ ] **[harness §3 강화]** STATE.md 갱신 이벤트 테이블에 "강제" 명시 + 미갱신 시 진행 차단 규칙 추가
- [ ] **[harness §3 신설]** State Gate 정의 — PM이 단계 시작/완료 시 STATE.md 갱신 여부를 확인하는 절차
- [ ] **[harness §3 신설]** 세션 복원 공통 절차 — STATE.md Read → 현재 Phase/상태 파악 → 재개
- [ ] **[harness-interactive §2 수정]** QA 도메인 테이블에 opsdd, opwt 추가
- [ ] **[harness-interactive §3 강화]** PM Gate에 State Gate 연동 — 이전 State 미갱신 시 PM Gate 차단 추가
- [ ] **[각 pilot SKILL.md 갱신]** opd/opds/opdw/opp의 각 단계에 STATE.md 갱신 지시 명시 (State Gate 참조)
- [ ] **[opsdd/opwt SKILL.md 점검]** State Gate와의 정합성 확인, 필요 시 참조 추가
- [x] **[op-task SKILL.md 개선]** STEP 4 "대화 내용 반영"에 "사전 분석/조사 결과" 섹션 추가
  - 현재: "확정된 설계 방향 (대화에서 합의)" 섹션만 안내
  - 개선: 분석/조사/현황 파악 결과가 있을 때 "배경 분석 (대화에서 도출)" 섹션도 캡처하도록 가이드 추가
  - 작성 체크리스트에도 동일하게 반영
  - AC: 대화에서 분석/조사가 선행된 경우, 그 결과가 TASK.md에 포함되어 워커가 컨텍스트를 독립적으로 파악할 수 있어야 한다

## 범위

- 수정 대상: `opal/core/references/opal-harness.md`, `opal/core/references/opal-harness-interactive.md`
- 수정 대상: `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev-short/SKILL.md`
- 수정 대상: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`, `opal/skills/opal-pilot-project/SKILL.md`
- 점검 대상: `opal/skills/opal-pilot-sdd/SKILL.md`, `opal/skills/opal-pilot-write-tech/SKILL.md`
- 수정 대상: `opal/skills/op-task/SKILL.md`

## 제약

- `~/.opal/` 직접 수정 금지 — 모든 변경은 `opal/` 소스에서 수행
- 하네스 변경은 모든 오케스트레이터에 영향 → 파급 범위를 PLAN에서 사전 분석
- 기존 Gate 구조(QA Gate, Artifact Gate, PM Gate)를 대체하지 않고 State Gate를 추가
