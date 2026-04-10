# TASK: PM Gate 자가 진단 통합 + Artifact Gate 제거

> 작성일: 2026-04-10 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 대화 중 도출 (PLAN.md 체크리스트 미갱신 + Artifact Gate 설계 검토)
> 출력: TASK.md

---

## 작업 목표

Artifact Gate를 제거하고, PM Gate에 단계별 자가 진단을 통합한다.
PM Gate가 STATE.md에서 현재 Phase를 파악하여 파일 존재 + 체크리스트 완전성을 스스로 점검하는 단일 게이트로 강화한다.

---

## 배경

### 문제 1: PLAN.md 체크리스트가 갱신되지 않는다

체크리스트 갱신 의무가 3군데에 분산되어 있어 어느 단계에서든 누락되면 복구가 안 된다:

```
워커 (1차 책임 — EXECUTE 중 즉시 갱신)
  → QA 에이전트 (1차 갱신 — QA Gate에서 체크리스트 갱신)
    → PM Gate (2차 확인 — 미갱신 발견 시 QA 재소환)
```

PM Gate에 체크리스트 확인 절차가 정의되어 있으나 "확인한다"는 추상적 서술에 그쳐,
실제로 PM이 PLAN.md를 Read하는 강제 액션이 없다.

### 문제 2: Artifact Gate가 너무 단순하고 이름도 맞지 않는다

- **현재**: QA 산출물(QA-PLAN.md 등) 파일 존재 여부만 확인
- **이름 문제**: "Artifact"라는 이름이 파일 존재 확인에는 맞지만, 내용 완전성 확인으로 확장하면 맞지 않음
- **역할 문제**: QA Gate가 이미 산출물 품질을 검토했는데 Artifact Gate가 파일 존재만 다시 확인하는 것은 중복적이고 약함
- **구조 문제**: Gate 순서가 복잡해짐
  ```
  현재: QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate
  ```

### 해결 방향

Artifact Gate를 제거하고 PM Gate가 직접 자가 진단을 수행한다.
Artifact Gate(PM 직접 Read)가 잘 작동했던 이유는 PM이 직접 파일을 확인했기 때문이다.
PM Gate도 같은 방식으로 — STATE.md를 Read하여 현재 Phase를 파악하고,
Phase별 점검 항목(파일 존재 + 체크리스트 완전성)을 PM이 직접 Read하여 판단한다.

```
개선: QA Gate → State Gate → PM Gate (자가 진단 포함) → State Gate
```

---

## 요구사항

### R-1. opal-harness-interactive.md 재설계

**대상**: `opal/core/references/opal-harness-interactive.md`

#### R-1-1. §2.5 Artifact Gate 섹션 제거

전체 섹션 삭제. Gate Fail 공통 처리(§5)의 Artifact Gate 행도 함께 제거.

#### R-1-2. §3 PM Gate — 자가 진단 절차 추가 (알고리즘/데이터 분리 구조)

**설계 원칙**:
- **하네스** = 알고리즘 SSOT (PM이 따를 절차)
- **SKILL.md** = 데이터 선언 (스킬별 산출물 목록)
- PM은 하네스 한 곳만 읽어서 절차를 파악하고, 하네스 절차가 SKILL.md Read를 강제한다

**PM Gate 자가 진단 절차** (harness-interactive.md §3에 추가):
```
1. STATE.md Read → 현재 Phase 파악
2. 현재 SKILL.md "## PM Gate 점검 목록" 섹션 Read → 해당 Phase 행 확인
3. 점검 목록의 각 산출물 Read → 존재 + 내용 확인
4. 체크리스트 위치 Read → [ ] 발견 시:
     a. 해당 항목과 관련된 산출물 Read
     b. 실제로 작업이 완료됐는지 내용으로 판단
     c. 완료 확인 → [x]로 직접 갱신
     d. 미완료 확인 → 미완료 항목 목록에 추가
5. 판정:
     Pass (미완료 항목 없음) → PM 검토 기준(opal-pm.md §4)으로 진행
     Fail (미완료 항목 있음) → 항목별 이유 명시 + 사용자 보고
```

**SKILL.md "PM Gate 점검 목록" 섹션** (R-3 각 SKILL.md에 추가):
```markdown
## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| PLAN  | PLAN.md, QA-PLAN.md | PLAN.md §3, §4 |
| EXECUTE | QA-EXECUTE.md | PLAN.md §3 |
```
- 스킬별 Phase가 추가되는 경우 해당 Phase 행을 추가한다
- 체크리스트가 없는 Phase는 체크리스트 위치를 `-`로 표기

#### R-1-3. §4 체크리스트 검증 게이트 섹션 정리

PM Gate 자가 진단에 체크리스트 확인이 통합되었으므로 §4를 PM Gate(§3)로 통합하거나 제거한다.

#### R-1-4. §5 Gate Fail 공통 처리 — Artifact Gate 행 제거

재소환·재지시 처리 테이블에서 Artifact Gate 행 제거.

**AC**: PM Gate가 STATE.md → SKILL.md "PM Gate 점검 목록" → 산출물 Read → [ ] 내용 판단 → 직접 [x] 갱신 또는 사용자 보고 순서로 동작한다. 에이전트 재호출 없이 PM이 내용 기반으로 판단하며, 진짜 미완료 항목만 사용자에게 보고된다.

---

### R-2. opal-harness.md §3 진행 현황 행 구성 규칙 수정

**대상**: `opal/core/references/opal-harness.md`

**변경 내용**:
- 진행 현황 행 구성 규칙에서 `Artifact Gate` 행과 그 직후 `State Gate` 행 제거
- 산출물 행 규칙(§3 "산출물 행 규칙")에서 Artifact Gate 관련 내용 제거
- 변경 후 일반 단계 행 순서:
  ```
  작업 → {산출물} 생성 → QA Gate → {QA 산출물} 생성 → State Gate → PM Gate → State Gate → 사용자 확인
  ```

**AC**: 하네스 공통 진행 현황 행 구성 규칙에 Artifact Gate가 없다.

---

### R-3. 각 오케스트레이터 SKILL.md — 진행 현황 행 예시 수정

**대상**: 아래 6개 소스 파일의 "STATE.md 도메인 치환값" 진행 현황 행 예시

| 파일 | 제거 대상 행 |
|------|------------|
| `opal/skills/opal-pilot-project/SKILL.md` | Artifact Gate 행 + 직후 State Gate 행 (PLAN·EXECUTE 각 1쌍) |
| `opal/skills/opal-pilot-dev/SKILL.md` | Artifact Gate 행 + 직후 State Gate 행 (ANALYSIS·PLAN Gate 각 1쌍) |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | 동일 패턴 제거 + **TEST-SCENARIO 행 순서 정정** (PLAN 행 중간에 삽입된 순서 이상 수정) |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | Artifact Gate 행 + 직후 State Gate 행 (WIREFRAME 단계) |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | 모드별 Artifact Gate 행 + 직후 State Gate 행 제거 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | 105 태스크에서 반영된 Artifact Gate 행 제거 (Task 106 PM Gate 개선에 맞춰 재조율) |

SKILL.md 파이프라인 섹션(Phase별 Gate 설명)에서 `Artifact Gate` 참조 텍스트도 제거.

**제거 후 단계별 Gate 순서 (표준)**:
```
작업 → {산출물} 생성 → QA Gate → {QA 산출물} 생성 → State Gate → PM Gate → State Gate → 사용자 확인
```
(QA Gate 없는 단계: 작업 → {산출물} 생성 → State Gate → PM Gate → State Gate → 사용자 확인)

**AC**: 모든 오케스트레이터 SKILL.md의 진행 현황 행 예시에 Artifact Gate 행이 없고, Gate 순서가 표준을 따른다.

---

## 제약 조건

- `~/.opal/` 배포본 직접 수정 금지 — 소스(`opal/core/`, `opal/skills/`)에서만 수정 (확정 기준 #2)
- 하네스 변경이므로 모든 오케스트레이터 일관성 유지 필수
- 104 태스크(`tasks/104-opp-opsdd-state-gate-verify/`)와 opsdd SKILL.md 수정 범위 중복 — 104 EXECUTE 시 조율 필요

---

## 기술 스택

- Markdown 문서 (harness, SKILL.md)
- OPAL Harness 구조 (Guards, Gates, State)

---

## 관련 문서

- `opal/core/references/opal-harness-interactive.md` — §2.5 Artifact Gate, §3 PM Gate, §4 체크리스트 검증 게이트, §5 Gate Fail
- `opal/core/references/opal-harness.md` — §3 STATE.md 공통 구조, 진행 현황 행 구성 규칙
- `opal/skills/opal-pilot-project/SKILL.md` — opp 진행 현황 행 예시
- `opal/skills/opal-pilot-dev/SKILL.md` — opd 진행 현황 행 예시
- `opal/skills/opal-pilot-dev-short/SKILL.md` — opds 진행 현황 행 예시 + TEST-SCENARIO 순서 이상
- `opal/skills/opal-pilot-dev-wireframe/SKILL.md` — opdw 진행 현황 행 예시
- `opal/skills/opal-pilot-write-tech/SKILL.md` — opwt 진행 현황 행 예시 (모드별 가변)
- `opal/skills/opal-pilot-sdd/SKILL.md` — opsdd (105 태스크 조율)
- 선행 태스크 `tasks/090-opp-artifact-gate/` — Artifact Gate 도입 배경
- 선행 태스크 `tasks/097-opp-harness-gate-state/` — State Gate 도입 배경
- 연관 태스크 `tasks/105-opp-opsdd-state-gate-verify/` — opsdd SKILL.md 중복 수정 범위
