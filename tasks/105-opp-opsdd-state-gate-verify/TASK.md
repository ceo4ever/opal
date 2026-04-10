# TASK: opsdd STATE Gate 완성 + VERIFY Phase 추가

> 작성일: 2026-04-10 | 작업 번호: 105 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: mams/tasks/046-260409-opsdd-company-management-page/TASK-ADDED.md (046 회고)
> 출력: TASK.md

---

## 작업 목표

opsdd 파이프라인에 STATE Gate를 완성하고, VERIFY Phase를 신설하여 E2E 테스트를 파이프라인에 통합한다.

---

## 배경

opsdd SKILL.md(v2.1~v2.3)에서 State Gate를 참조하도록 명시했으나, STATE.md 도메인 치환값이
"완료 산출물" 독자 테이블 구조를 유지하여 State Gate가 실제로 동작할 수 없었다.
"opsdd는 Phase 기반 독자 구조이므로 진행 현황 행 대신 이 테이블로 산출물을 추적한다"는 주석이
진행 현황 행 구조 적용을 막고 있었던 것.

mams 프로젝트 task 046(회사 정보 관리 화면) 수행 중 아래 9가지 문제가 반복 발생하였고,
이를 회고하면서 STATE Gate 미적용 + VERIFY Phase 부재가 근본 원인임을 확인하였다.

| # | 문제 | 발생 시점 | 영향 |
|---|------|----------|------|
| 1 | EXECUTE 완료 후 빌드만 확인하고 "완료" 보고 — E2E 테스트 미수행 | EXECUTE→DONE | "테스트는 어떻게 한거지?" 지적 |
| 2 | TEST-SCENARIOS.md 실시간 갱신 안 함 | VERIFY 중 | "테스트 시나리오 확인한것들 업데이트 하고 있나요?" 지적 |
| 3 | BE DTO 변경 후 SDK 재생성 누락 | EXECUTE+VERIFY | 회사상태 변경이 저장 안 됨 → SDK 재생성 후 해결 |
| 4 | BE Service 로직 반영 누락 | EXECUTE+VERIFY | DTO에 필드 추가했으나 Service에서 처리 안 함 |
| 5 | SPEC-PLAN.md ACT 상태 6개 전부 "대기"로 방치 | EXECUTE 전체 | 작업은 끝났는데 기록은 안 한 상태 |
| 6 | STATE.md ACT 목록 비어있음 | EXECUTE 전체 | 동일 |
| 7 | Phase 전환이 텍스트로만 관리 — Gate 이력 없음 | 전 Phase | 어디까지 진행했는지 추적 어려움 |
| 8 | REVIEW 이후에도 SPEC 변경 발생 — 변경 추적 안 됨 | REVIEW→EXECUTE | 브랜드/매체 등록 범위 추가, 인증정보 정책 반영 등 |
| 9 | FE/BE 교차 변경 시 의존 체인 중간 누락 | EXECUTE+VERIFY | DB→모델→DTO→Service→SDK→Zod→폼 체인 끊김 |

---

## 요구사항

### R-1. STATE.md 도메인 치환값 교체 — 진행 현황 행 구조 적용 (STATE Gate 완성)

**대상**: `opal/skills/opal-pilot-sdd/SKILL.md` — "STATE.md 도메인 치환값" 섹션

**변경 내용**:
- 현재 "완료 산출물" 독자 테이블을 제거하고, 하네스 공통 "진행 현황" 행 구조로 교체
- EXECUTE Phase: 진행 현황에 요약 행 1개 + ACT 목록 테이블이 SSOT
- TS 현황 요약 섹션 추가 (상태별 건수 집계)
- SPEC 변경 이력 섹션 추가 (REVIEW 이후 SPEC 변경 추적)

**진행 현황 테이블 행 구성 (VERIFY Phase 포함, 24행)**:

| # | Phase | 항목 | 비고 |
|---|-------|------|------|
| 1 | TASK | TASK.md 작성 | |
| 2 | TASK | STATE.md 생성 | |
| 3 | TASK | 사용자 확인 | |
| 4 | SPEC | 워커 디스패치 | |
| 5 | SPEC | SPEC.md 생성 | |
| 6 | SPEC | State Gate | |
| 7 | SPEC | PM Gate | |
| 8 | SPEC | 사용자 확인 | |
| 9 | REVIEW | 구조 검증 (S-1~S-6) | |
| 10 | REVIEW | TEST-SCENARIOS.md 작성 | |
| 11 | REVIEW | FR↔TS 커버리지 확인 | |
| 12 | REVIEW | 사용자 확인 | |
| 13 | DESIGN | 워커 디스패치 | |
| 14 | DESIGN | SPEC-PLAN.md 생성 | |
| 15 | DESIGN | State Gate | |
| 16 | DESIGN | PM Gate | |
| 17 | DESIGN | 사용자 확인 | |
| 18 | EXECUTE | ACT 실행 (상세: ACT 목록 참조) | |
| 19 | EXECUTE | 사용자 확인 | |
| 20 | VERIFY | E2E 테스트 수행 | |
| 21 | VERIFY | TS 전체 Green 확인 | |
| 22 | VERIFY | 사용자 확인 | |
| 23 | DONE | DONE.md 생성 | |
| 24 | DONE | 사용자 확인 | |

**ACT 목록 테이블 (SSOT)**: SPEC-PLAN.md 기반으로 DESIGN 완료 후 동적 삽입
```
| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |
```
- `코드`: 구현 완료 여부 (⬜/✅)
- `L1 lint`: tsc --noEmit 결과 (⬜/✅/❌)
- `L2 build`: pnpm build 결과 (⬜/✅/❌)
- SPEC-PLAN.md에는 ACT 상태 필드를 두지 않는다 → STATE.md ACT 목록이 유일한 상태 추적처

**TS 현황 섹션**: TEST-SCENARIOS.md 추적 매트릭스 요약 (Green / Red / Fail / Skip 건수)

**SPEC 변경 이력 섹션**: REVIEW 이후 SPEC.md가 변경된 경우 기록

**AC**: STATE.md 도메인 치환값이 하네스 §3 진행 현황 행 구조를 준수하고, State Gate가 실제로 동작 가능한 구조로 바뀐다.

---

### R-2. VERIFY Phase 신설 (파이프라인 5→6단계)

**대상**: `opal/skills/opal-pilot-sdd/SKILL.md`

**변경 내용**:
- 파이프라인 단계를 5→6단계로 확장:
  ```
  TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → DONE
  ```
- YAML frontmatter description 업데이트 (5단계 → 6단계)
- VERIFY Phase 상세 섹션 신설 (현재 Phase 5 DONE → Phase 6 DONE으로 번호 이동)

**VERIFY Phase 정의**:

| 항목 | 내용 |
|------|------|
| 수행 주체 | PM 직접 (Playwright E2E) |
| 진입 조건 | EXECUTE-LOOP 전체 ACT ✅ + 빌드 검증(L2) Pass |
| 수행 내용 | TEST-SCENARIOS.md의 모든 시나리오를 E2E로 수행 |
| 갱신 의무 | 시나리오 Pass/Fail 확인 즉시 TEST-SCENARIOS.md 추적 매트릭스 갱신 (배치 금지) |
| 완료 조건 | 전체 TS Green (또는 Skip + 사유) + 사용자 확인 |
| Fail 시 | 해당 ACT 재지시 또는 코드 직접 수정 → 재검증 |
| Gate | State Gate → 사용자 Gate |

**AC**: 파이프라인 요약, 진행 현황 행, STATE.md 치환값 모두 VERIFY Phase를 포함하며 일관성을 유지한다.

---

### R-3. EXECUTE Phase — ACT별 L1/L2 검증 루프 명시

**대상**: `opal/skills/opal-pilot-sdd/SKILL.md` (Phase 4 EXECUTE-LOOP 섹션)
**대상 추가**: `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` (§9 ACT 목록 테이블 업데이트)

**변경 내용**:

PM이 각 ACT 완료 후 직접 검증을 실행한다:

```
ACT-N 완료 (코드)
  → L1: tsc --noEmit (lint + type check)
  → L2: pnpm build
    → Pass → ACT 목록 L1 ✅, L2 ✅, 상태 ✅
    → Fail → 워커에 SendMessage로 수정 지시
              → 수정 완료 → 재검증 (L1부터)
              → L2 2회 초과 → 캡틴 에스컬레이션
→ 다음 ACT (의존관계 충족 시)
```

| 검증 계층 | 최대 재시도 | 초과 시 |
|----------|-----------|--------|
| L1 lint/type | 제한 없음 | — |
| L2 build | 2회 | 캡틴 에스컬레이션 |

검증 시점 2회:
1. 매 ACT 완료 후: 해당 ACT 변경이 빌드를 깨뜨리지 않는지
2. 전체 ACT 완료 후: 최종 통합 빌드 확인

**execute-loop-guide.md §9.2 ACT 목록 테이블 업데이트**:
```
| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |
```
갱신 시점 테이블에 L1/L2 관련 이벤트 행 추가.

**AC**: EXECUTE Phase 섹션과 execute-loop-guide.md §9.2가 L1/L2 검증 루프와 재시도 한도를 명시한다.

---

### R-4. SPEC-PLAN.md — ACT 상태 필드 제거 명시

**대상**: `opal/skills/opal-pilot-sdd/references/spec-plan-guide.md`

> 참고: TASK-ADDED.md는 배포 경로 `~/.opal/skills/op-sdd-plan/references/spec-plan-guide.md`를 지정했으나,
> 소스에서는 `opal/skills/opal-pilot-sdd/references/spec-plan-guide.md`만 존재함. 소스 파일 기준으로 반영한다.

**변경 내용**:
- "ACT 블록에 상태 필드(`- **상태**: 대기/완료`)를 두지 않는다. ACT 실행 상태는 STATE.md ACT 목록이 SSOT" 라는 원칙을 가이드에 명시
- SPEC-PLAN.md의 역할: 설계 문서 (WHAT → HOW 변환). 실행 상태 추적 아님

**이유**: 이중 추적(SPEC-PLAN.md + STATE.md)은 갱신 누락의 직접 원인. 046 태스크에서 SPEC-PLAN.md ACT 상태 6개 전부 "대기"로 방치된 패턴이 실제 발생.

**AC**: spec-plan-guide.md에 ACT 상태 필드 금지 원칙이 명시된다.

---

### R-5. 하네스 §3 — opsdd 진행 현황 행 예시 추가 (중간 우선순위)

**대상**: `opal/core/references/opal-harness.md` §3 State

**변경 내용**:
- 오케스트레이터별 진행 현황 행 예시 섹션에 opsdd 예시 추가
  (현재 opp/opds/opdw 예시가 있는 경우 그에 준하여 추가)

**AC**: 하네스 §3에 opsdd 도메인의 진행 현황 행 구성 예시가 포함된다.

---

## 수정 대상 파일 정리

| 우선순위 | 파일 | 변경 내용 |
|---------|------|----------|
| 높음 | `opal/skills/opal-pilot-sdd/SKILL.md` | R-1 STATE.md 치환값 교체 + R-2 VERIFY Phase + R-3 L1/L2 루프 명시 |
| 높음 | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | R-3 ACT 목록 테이블 L1/L2 컬럼 + 갱신 시점 업데이트 |
| 중간 | `opal/skills/opal-pilot-sdd/references/spec-plan-guide.md` | R-4 ACT 상태 필드 금지 원칙 명시 |
| 중간 | `opal/core/references/opal-harness.md` | R-5 opsdd 진행 현황 행 예시 추가 |

---

## 제약 조건

- `~/.opal/` 배포본 직접 수정 금지 — 소스(`opal/core/`, `opal/skills/`)에서만 수정 (확정 기준 #2)
- 하네스 변경(R-5)은 모든 오케스트레이터에 영향을 주므로 기존 opp/opds/opdw 진행 현황 구조와 충돌하지 않도록 주의
- 기존 진행 중인 태스크(예: 098)의 STATE.md는 소급 변경 대상 아님

---

## 관련 문서

- `mams/tasks/046-260409-opsdd-company-management-page/TASK-ADDED.md` — 입력 회고 문서
- `opal/skills/opal-pilot-sdd/SKILL.md` — opsdd 오케스트레이터 메인 (v2.4)
- `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` — EXECUTE-LOOP 상세 가이드
- `opal/skills/opal-pilot-sdd/references/spec-plan-guide.md` — SPEC-PLAN.md 작성 가이드
- `opal/core/references/opal-harness.md` — §3 State Gate, 진행 현황 구조
- `opal/core/references/opal-harness-interactive.md` — §3 State Gate 절차
- 선행 태스크 `tasks/097-opp-harness-gate-state/` — State Gate 도입 배경
- 선행 태스크 `tasks/101-opp-state-artifact-integration/` — 진행 현황 행 산출물 통합
