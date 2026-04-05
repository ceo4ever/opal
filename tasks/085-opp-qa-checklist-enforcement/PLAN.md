# PLAN: QA 체크리스트 갱신 강제 — QA 에이전트 책임 + PM Gate 확인

> 작성일: 2026-04-05 | 태스크: 085
> 입력: TASK.md
> 출력: PLAN.md

---

## 1. 현황 조사 결과

### 문제 구조

PM이 DONE.md 생성 전 체크리스트 갱신을 반복 누락하는 근본 원인:

1. **갱신 주체가 PM** — `opal-harness.md` §2에서 "PM이 QA 결과 확인 후 갱신"으로 명시. PM은 오케스트레이션 업무 중 갱신을 잊기 쉬움
2. **QA 에이전트에 갱신 역할 없음** — `op-task-qa`, `op-dev-qa` SKILL.md에 체크리스트 갱신 관련 프로세스가 전혀 없음. QA는 검증만 하고 리포트만 반환
3. **PM Gate에 강제 확인 절차 없음** — `opal-harness-interactive.md` §3에 PM Gate가 있으나, 체크리스트 갱신 상태 확인이 명시적 필수 절차가 아님
4. **§4 체크리스트 검증 게이트의 한계** — 1차 워커, 2차 PM으로 되어 있지만 "PM이 직접 갱신"이라 PM 누락 시 방어 불가

### 수정 대상 파일 현재 상태

| 파일 | 현재 상태 | 변경 필요 |
|------|----------|----------|
| `opal/core/references/opal-harness.md` §2 | PM이 갱신 주체 | QA 에이전트를 1차 갱신 주체로 변경 |
| `opal/core/references/opal-harness-interactive.md` §3 | PM Gate에 체크리스트 확인 없음 (TASK.md 체크박스 갱신만 있음) | PM Gate에 체크리스트 갱신 상태 확인 + QA 재소환 절차 추가 |
| `opal/core/references/opal-harness-interactive.md` §4 | 2차 PM 직접 갱신 | 2차 PM 확인 → 미갱신 시 QA 재소환으로 변경 |
| `opal/skills/op-task-qa/SKILL.md` | 검증만 수행, 갱신 없음 | 체크리스트 갱신 프로세스 추가 |
| `opal/skills/op-dev-qa/SKILL.md` | 검증만 수행, 갱신 없음 | 체크리스트 갱신 프로세스 추가 |
| `opal/skills/opal-pilot-project/SKILL.md` | QA Gate 후 PM Gate 서술에 체크리스트 갱신 상태 확인 없음 | PM Gate에 갱신 확인 절차 명시 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | 동일 | 동일 |
| `opal/skills/opal-pilot-dev/SKILL.md` | 동일 | 동일 |

---

## 2. 파일 변경 계획

#### 신규 생성

없음.

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/references/opal-harness.md` | §2 QA 체크리스트 검증 테이블 — 갱신 주체를 "QA 에이전트 1차 갱신 + PM 확인"으로 변경 |
| 2 | `opal/core/references/opal-harness-interactive.md` | §3 PM Gate에 체크리스트 갱신 상태 확인 필수 절차 추가 + §4 2차 검증을 "PM 확인 → QA 재소환"으로 변경 |
| 3 | `opal/skills/op-task-qa/SKILL.md` | 프로세스에 "체크리스트 갱신" Step 추가 (Step 3과 Step 4 사이) |
| 4 | `opal/skills/op-dev-qa/SKILL.md` | 프로세스에 "체크리스트 갱신" Step 추가 (동일 패턴) |
| 5 | `opal/skills/opal-pilot-project/SKILL.md` | STEP 2 PM Gate, STEP 3 PM Gate에 갱신 확인 절차 명시 |
| 6 | `opal/skills/opal-pilot-dev-short/SKILL.md` | STEP 2 PM Gate, STEP 3 PM Gate에 갱신 확인 절차 명시 |
| 7 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 2~3 PM Gate, STEP 4 PM Gate에 갱신 확인 절차 명시 |

#### 삭제

없음.

---

## 2-1. 구현 순서

의존성: 하네스 공통(#1) → 하네스 interactive(#2) → QA 스킬(#3, #4 병렬) → 오케스트레이터(#5, #6, #7 병렬)

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 하네스 공통 — QA 체크리스트 검증 테이블 갱신 주체 변경 | `opal-harness.md` | 낮음 |
| 2 | 하네스 interactive — PM Gate 확인 절차 + §4 변경 | `opal-harness-interactive.md` | 중간 |
| 3 | 범용 QA 스킬 — 체크리스트 갱신 프로세스 추가 | `op-task-qa/SKILL.md` | 중간 |
| 4 | Dev QA 스킬 — 체크리스트 갱신 프로세스 추가 | `op-dev-qa/SKILL.md` | 중간 |
| 5 | opp — PM Gate 갱신 확인 절차 | `opal-pilot-project/SKILL.md` | 낮음 |
| 6 | opds — PM Gate 갱신 확인 절차 | `opal-pilot-dev-short/SKILL.md` | 낮음 |
| 7 | opd — PM Gate 갱신 확인 절차 | `opal-pilot-dev/SKILL.md` | 낮음 |

---

## 2-2. 핵심 설계

### A. 2단계 갱신 구조 (공통 원칙)

```
[1차] QA 에이전트가 검증 수행 시 체크리스트를 직접 갱신
      ↓
[2차] PM Gate에서 갱신 상태를 확인
      ├─ 갱신 완료 → 다음 단계 진행
      └─ 미갱신 발견 → QA 에이전트 재소환하여 갱신 (PM 직접 갱신 금지)
```

### B. `opal-harness.md` §2 변경

현재:
```
| opp | QA Gate (QA 에이전트) + PM Gate | PM이 QA 결과 확인 후 갱신 |
```

변경:
```
| opp | QA Gate (QA 에이전트) + PM Gate | QA 에이전트가 검증 시 갱신 → PM Gate에서 갱신 상태 확인 |
```

`opd/opds`도 동일 패턴 적용 — TEST-SCENARIO 결과 기반이지만 QA 체크리스트 갱신은 QA 에이전트 담당으로 변경.

갱신 의무 문구도 보완: "QA 에이전트가 1차 갱신하고, PM Gate에서 갱신 상태를 확인한다. 미갱신 항목 발견 시 PM이 직접 갱신하지 않고 QA 에이전트를 재소환한다."

### C. `opal-harness-interactive.md` 변경

**§3 PM Gate** — 기존 "TASK.md 체크박스 갱신" 하위에 체크리스트 갱신 상태 확인 절차를 추가:

```markdown
### 체크리스트 갱신 상태 확인 (모든 PM Gate 공통)

PM Gate에서 다음을 확인한다:

**PLAN PM Gate 시**:
1. TASK.md 요구사항 체크박스 갱신 상태를 확인한다
2. 미갱신 항목이 있으면 QA 에이전트(op-task-qa 또는 op-dev-qa)를 재소환하여 갱신하게 한다
3. PM이 직접 체크박스를 갱신하지 않는다

**EXECUTE PM Gate 시**:
1. PLAN.md §3 실행 체크리스트 갱신 상태를 확인한다
2. PLAN.md §4 QA 체크리스트 갱신 상태를 확인한다
3. 미갱신 항목이 있으면 QA 에이전트를 재소환하여 갱신하게 한다
4. **모든 체크리스트가 갱신 완료된 후에만** DONE.md 생성으로 진행한다
```

**§4 체크리스트 검증 게이트** — 2차 검증의 "PM이 직접 갱신"을 "PM이 QA 재소환"으로 변경:

```markdown
**2차 검증 — 오케스트레이터(PM)**:
- 워커 결과 수신 후 PLAN.md를 Read하여 체크리스트 갱신 상태 확인
- 미갱신 항목 발견 시: QA 에이전트를 재소환하여 갱신 (PM 직접 갱신 금지)
- **체크리스트 완전 갱신 확인 후에만** DONE.md / 완료 보고로 진행
```

### D. QA 스킬 프로세스 확장 (`op-task-qa`, `op-dev-qa`)

기존 Step 3(품질 검증)과 Step 4(판정) 사이에 **"Step 3.5. 체크리스트 갱신"**을 추가한다. 번호 재배정하여 Step 4로 편입, 기존 Step 4/5를 Step 5/6으로 밀림.

**op-task-qa 추가 내용**:

```markdown
### Step 4. 체크리스트 갱신

QA 검증 결과를 바탕으로 해당 시점의 체크리스트를 Read하고, 검증 통과 항목을 `[x]`로 갱신한다.

| 현재 단계 | 갱신 대상 | 갱신 내용 |
|-----------|----------|----------|
| PLAN | TASK.md 요구사항 체크박스 | PLAN.md가 커버하는 요구사항 → `[x]` |
| EXECUTE | PLAN.md §3 실행 체크리스트 + §4 QA 체크리스트 | 검증 통과 항목 → `[x]` |

**갱신 규칙**:
- 검증을 통과한 항목만 `[x]`로 갱신한다
- 검증 실패(Fail) 항목은 `[ ]` 유지 + QA 리포트에 사유 기재
- Warning 항목은 `[x]`로 갱신하되 QA 리포트에 비고 기재
```

**op-dev-qa 추가 내용**: 동일 패턴이나, EXECUTE 단계에서 TEST-SCENARIO 결과도 반영.

### E. 오케스트레이터 SKILL.md 변경 패턴

각 오케스트레이터의 PM Gate 서술에 다음을 추가:

```
PM Gate — {기존 내용} + **체크리스트 갱신 상태 확인** (하네스 interactive §3 "체크리스트 갱신 상태 확인" 참조). 미갱신 시 QA 에이전트 재소환.
```

구체적으로:
- **opp**: STEP 2 PM Gate + STEP 3 EXECUTE 완료 후 PM Gate
- **opds**: STEP 2 PM Gate + STEP 3 EXECUTE 완료 후 PM Gate
- **opd**: STEP 2 QA Gate 후 PM Gate + STEP 3-1 PLAN PM Gate + STEP 4 EXECUTE 완료 후 PM Gate

---

## 3. 실행 체크리스트

> 총 7개 Step | Phase 3개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1, 2 | 순차 | 하네스 공통 → interactive (의존) |
> | 2     | 3, 4 | 병렬 | 독립 QA 스킬 파일 |
> | 3     | 5, 6, 7 | 병렬 | 독립 오케스트레이터 파일 |

### Step 1: 하네스 공통 — QA 체크리스트 검증 테이블 갱신 주체 변경
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**:
  - §2 QA 체크리스트 검증 테이블의 "QA 체크리스트 갱신 주체" 컬럼 값을 변경:
    - `opd/opds`: "PM이 TEST-SCENARIO 결과 확인 후 갱신" → "QA 에이전트가 검증 시 갱신 → PM Gate에서 확인"
    - `opp`: "PM이 QA 결과 확인 후 갱신" → "QA 에이전트가 검증 시 갱신 → PM Gate에서 확인"
  - 갱신 의무 문구 보완: PM 직접 갱신 금지, QA 재소환 원칙 추가
  - 변경이력 추가
- **완료 기준**: 갱신 주체가 모든 행에서 "QA 에이전트 → PM 확인"으로 변경됨
- **테스트**: 테이블 내 "PM이 ... 갱신" 문구가 남아있지 않은지 확인
- **의존**: 없음

### Step 2: 하네스 interactive — PM Gate 확인 절차 + §4 변경
- [x] 완료
- **파일**: `opal/core/references/opal-harness-interactive.md`
- **작업 내용**:
  - §3 PM Gate에 "체크리스트 갱신 상태 확인 (모든 PM Gate 공통)" 하위 섹션 추가 (핵심 설계 §C 내용)
  - §4 2차 검증에서 "PM이 직접 갱신" → "QA 에이전트 재소환"으로 변경 (핵심 설계 §C 내용)
  - 변경이력 추가
- **완료 기준**: §3에 PLAN/EXECUTE PM Gate별 체크리스트 확인 절차가 명시됨. §4에서 PM 직접 갱신 문구가 제거됨
- **테스트**: "PM이 직접 갱신" 문구가 §4에 남아있지 않은지 확인
- **의존**: Step 1 (하네스 공통에서 정의한 원칙을 참조)

### Step 3: 범용 QA 스킬 — 체크리스트 갱신 프로세스 추가
- [x] 완료
- **파일**: `opal/skills/op-task-qa/SKILL.md`
- **작업 내용**:
  - 기존 Step 3(품질 검증)과 Step 4(판정) 사이에 "Step 4. 체크리스트 갱신" 추가 (핵심 설계 §D)
  - 기존 Step 4(판정) → Step 5, Step 5(QA 리포트) → Step 6으로 번호 재배정
  - 입력 테이블에 `checklist_path` 필드 추가 (TASK.md 또는 PLAN.md 경로)
  - 변경이력 추가
- **완료 기준**: Step 4에 단계별 갱신 대상 테이블과 갱신 규칙이 명시됨
- **테스트**: 프로세스 Step 번호가 1~6으로 연속적인지, 갱신 대상 테이블에 PLAN/EXECUTE 단계가 모두 포함되는지 확인
- **의존**: 없음

### Step 4: Dev QA 스킬 — 체크리스트 갱신 프로세스 추가
- [x] 완료
- **파일**: `opal/skills/op-dev-qa/SKILL.md`
- **작업 내용**:
  - op-task-qa와 동일 패턴으로 "Step 4. 체크리스트 갱신" 추가
  - Dev 도메인 특성 반영: EXECUTE 단계에서 TEST-SCENARIO 결과도 체크리스트 갱신에 반영
  - 기존 Step 4/5 → Step 5/6 번호 재배정
  - 입력 테이블에 `checklist_path` 필드 추가
  - 변경이력 추가
- **완료 기준**: Step 4에 ANALYSIS/PLAN/EXECUTE 단계별 갱신 대상이 명시됨
- **테스트**: 프로세스 Step 번호가 1~6으로 연속적인지 확인
- **의존**: 없음

### Step 5: opp 오케스트레이터 — PM Gate 갱신 확인 절차 명시
- [x] 완료
- **파일**: `opal/skills/opal-pilot-project/SKILL.md`
- **작업 내용**:
  - STEP 2 (PLAN): PM Gate 서술에 "체크리스트 갱신 상태 확인 (하네스 interactive §3 참조). 미갱신 시 QA 에이전트 재소환" 추가
  - STEP 3 (EXECUTE): PM Gate 서술에 동일 확인 절차 추가. "모든 체크리스트 갱신 완료 후 DONE.md 생성" 강조
  - 변경이력 추가
- **완료 기준**: STEP 2, STEP 3 모두에 체크리스트 갱신 확인 + QA 재소환 절차가 명시됨
- **테스트**: PM Gate 서술에 "체크리스트 갱신 상태 확인" 문구가 포함되는지 확인
- **의존**: Step 2 (하네스 interactive §3 정의 완료 전제)

### Step 6: opds 오케스트레이터 — PM Gate 갱신 확인 절차 명시
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**:
  - STEP 2 (PLAN): PM Gate 서술에 체크리스트 갱신 확인 + QA 재소환 절차 추가
  - STEP 3 (EXECUTE): PM Gate 서술에 동일 확인 절차 추가
  - 변경이력 추가
- **완료 기준**: STEP 2, STEP 3 모두에 체크리스트 갱신 상태 확인이 명시됨
- **테스트**: PM Gate 서술에 "체크리스트 갱신 상태 확인" 문구가 포함되는지 확인
- **의존**: Step 2

### Step 7: opd 오케스트레이터 — PM Gate 갱신 확인 절차 명시
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**:
  - STEP 2 (ANALYSIS): PM Gate 서술에 체크리스트 갱신 확인 추가 (ANALYSIS 단계는 체크리스트 갱신 대상이 제한적이므로 간략)
  - STEP 3 (PLAN): PM Gate 서술에 TASK.md 체크박스 갱신 상태 확인 + QA 재소환 절차 추가
  - STEP 4 (EXECUTE): PM Gate 서술에 실행/QA 체크리스트 갱신 확인 + QA 재소환 절차 추가
  - 변경이력 추가
- **완료 기준**: 모든 PM Gate에 체크리스트 갱신 상태 확인이 명시됨
- **테스트**: PM Gate 서술에 "체크리스트 갱신 상태 확인" 문구가 포함되는지 확인
- **의존**: Step 2

---

## 4. QA 체크리스트

### 기능 테스트
- [x] R1 충족: op-task-qa, op-dev-qa에 체크리스트 갱신 프로세스가 추가되었는가
- [x] R1 충족: PLAN QA 시 TASK.md 요구사항 체크박스 갱신이 명시되었는가
- [x] R1 충족: EXECUTE QA 시 PLAN.md §3 + §4 체크리스트 갱신이 명시되었는가
- [x] R2 충족: 모든 PM Gate에 체크리스트 갱신 상태 확인 절차가 추가되었는가
- [x] R2 충족: PM 직접 갱신 금지 + QA 재소환 원칙이 명시되었는가
- [x] R3 충족: QA 미발동 시에도 PM Gate에서 미갱신 감지 → QA 소환 절차가 있는가

### 일관성 테스트
- [x] 하네스 공통(opal-harness.md)과 interactive 서브 하네스의 원칙이 일관적인가
- [x] QA 스킬 2개(op-task-qa, op-dev-qa)의 갱신 패턴이 일관적인가
- [x] 오케스트레이터 3개(opp, opds, opd)의 PM Gate 서술이 일관적인가

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] 변경이력이 모든 수정 파일에 추가되었는가
