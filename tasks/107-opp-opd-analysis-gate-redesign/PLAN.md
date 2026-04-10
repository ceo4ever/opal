---
task_id: "107"
status: PLAN
---

# PLAN: opd ANALYSIS Gate 슬림화 + PLAN QA 범위 확대

## 수정 파일

- `opal/skills/opal-pilot-dev/SKILL.md`

## 변경 상세

### 1. STEP 2 ANALYSIS — Gate 재설계

**현재 코드**:
```
워커 완료
  → **QA Gate** (op-dev-qa — 체크리스트 갱신 포함) → **State Gate**
  → **Artifact Gate** (하네스 §2.5 참조) → **State Gate**
  → **PM Gate** (종합 검토) → **State Gate** → 사용자 보고.
```

**변경 후**:
```
워커 완료
  → **State Gate**
  → **Artifact Gate** (ANALYSIS.md 존재 확인)
  → 사용자 보고 (분석 방향 검토 후 PLAN 진입 승인).
```

### 2. STEP 3 PLAN — QA Gate 검토 범위 확대

**현재 코드**:
```
  → **QA Gate** (op-dev-qa — PLAN.md + TEST-SCENARIO.md 동시 검토, 체크리스트 갱신 포함) → **State Gate**
```

**변경 후**:
```
  → **QA Gate** (op-dev-qa — ANALYSIS.md + PLAN.md + TEST-SCENARIO.md 통합 검토, 체크리스트 갱신 포함) → **State Gate**
```

### 3. STATE.md 진행 현황 행 예시 — 전면 교체

ANALYSIS 행 5개로 축소 + 행 번호 전체 재정렬 (37행 → 32행).

| # | 단계 | 항목 |
|---|------|------|
| 1 | TASK | 작업 |
| 2 | TASK | TASK.md 생성 |
| 3 | TASK | 사용자 확인 |
| 4 | ANALYSIS | 작업 |
| 5 | ANALYSIS | ANALYSIS.md 생성 |
| 6 | ANALYSIS | State Gate |
| 7 | ANALYSIS | Artifact Gate |
| 8 | ANALYSIS | 사용자 확인 |
| 9 | PLAN | 작업 |
| 10 | PLAN | PLAN.md 생성 |
| 11 | TEST-SCENARIO | 작업 |
| 12 | TEST-SCENARIO | TEST-SCENARIO.md 생성 |
| 13 | TEST-SCENARIO | State Gate |
| 14 | PLAN | QA Gate |
| 15 | PLAN | QA-PLAN.md 생성 |
| 16 | PLAN | State Gate |
| 17 | PLAN | Artifact Gate |
| 18 | PLAN | State Gate |
| 19 | PLAN | PM Gate |
| 20 | PLAN | State Gate |
| 21 | PLAN | 사용자 확인 |
| 22 | EXECUTE | 작업 |
| 23 | EXECUTE | State Gate |
| 24 | TEST | 작업 |
| 25 | TEST | State Gate |
| 26 | TEST | QA Gate |
| 27 | TEST | QA-EXECUTE.md 생성 |
| 28 | TEST | State Gate |
| 29 | TEST | PM Gate |
| 30 | TEST | DONE.md 생성 |
| 31 | TEST | State Gate |
| 32 | TEST | 사용자 확인 |

### 4. 변경이력 추가

```
| v2.6 | 2026-04-10 | ANALYSIS Gate 슬림화 — QA·PM Gate 제거, State Gate + Artifact Gate만 유지. PLAN QA 범위 확대 — ANALYSIS.md 포함 통합 검토 (107) |
```

> 기존 v2.5가 STATE.md 도메인 설정(101)이므로 이 변경은 v2.6.

## 실행 체크리스트

- [ ] STEP 2 ANALYSIS 워커 완료 후 Gate 블록 교체
- [ ] STEP 3 QA Gate 검토 범위 텍스트 수정
- [ ] STATE.md 행 예시 전체 교체 (행 번호 재정렬)
- [ ] 변경이력 행 추가
