---
name: op-sdd-verify
description: |
  **SDD 명세/태스크 검증 단계 스킬**. mode에 따라 SPEC.md 또는 TASKS.md를 검증하고 VERIFY.md 저널에 결과를 누적 기록한다.
  반드시 이 스킬을 사용해야 하는 상황: opsdd 오케스트레이터가 SPEC-VERIFY 또는 TASKS-VERIFY Phase를 디스패치할 때.
  필수 입력: mode + spec_path. 보장 출력: VERIFY.md (해당 섹션 추가) + TEST-SCENARIOS.md (mode=spec 시).
---

# op-sdd-verify -- SDD 명세/태스크 검증

## 실행 컨텍스트

- **호출자**: opsdd 오케스트레이터가 SPEC-VERIFY 또는 TASKS-VERIFY Phase를 디스패치
- **실행 주체**: 워커 에이전트 (opal-task-agent)
- **mode**: `spec` (Phase 2) 또는 `tasks` (Phase 5)

## 페르소나

```
Read {skill_dir}/personas/spec-verifier.md
```

페르소나 파일이 없으면 다음 역할을 따른다:
- SDD 검증 전문가
- 3계층(구조적/의미적/도메인) 검증을 체계적으로 수행한다
- 판정에 반드시 구체적 근거를 첨부한다
- spec 내용을 직접 수정하지 않고 판정과 피드백만 제공한다

## mode 분기

| mode | Phase | 역할 | model |
|------|-------|------|-------|
| `spec` | Phase 2: SPEC-VERIFY | SPEC.md 3계층 검증 + TEST-SCENARIOS.md 도출 | advanced |
| `tasks` | Phase 5: TASKS-VERIFY | TASKS.md 커버리지/의존관계 검증 | standard |

---

## 입력 (mode별)

### mode=spec

| 입력 | 설명 | 필수 |
|------|------|------|
| `spec_path` | specs/{NNN}-{feature}/ 경로 | 필수 |
| `SPEC.md` | spec_path/SPEC.md -- 검증 대상 명세 | 필수 |
| `docs/PROJECT.md` | 프로젝트 정의 | 선택 |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 | 선택 |
| `docs/CONVENTIONS.md` | 코드 컨벤션 | 선택 |

### mode=tasks

| 입력 | 설명 | 필수 |
|------|------|------|
| `spec_path` | specs/{NNN}-{feature}/ 경로 | 필수 |
| `TASKS.md` | spec_path/TASKS.md -- 검증 대상 태스크 분해 | 필수 |
| `SPEC.md` | spec_path/SPEC.md -- 원본 명세 (교차 검증) | 필수 |
| `TEST-SCENARIOS.md` | spec_path/tests/TEST-SCENARIOS.md -- TS 커버리지 검증 | 필수 |
| `SPEC-PLAN.md` | spec_path/SPEC-PLAN.md -- 설계 참조 | 선택 |

## 출력 (mode별)

### mode=spec

| 출력 | 경로 | 설명 |
|------|------|------|
| VERIFY.md (SPEC 검증 섹션) | `{spec_path}/VERIFY.md` | 신규 생성 또는 SPEC 검증 섹션 추가 |
| TEST-SCENARIOS.md | `{spec_path}/tests/TEST-SCENARIOS.md` | AC에서 도출한 테스트 시나리오 |

### mode=tasks

| 출력 | 경로 | 설명 |
|------|------|------|
| VERIFY.md (TASKS 검증 섹션 추가) | `{spec_path}/VERIFY.md` | 기존 VERIFY.md에 TASKS 검증 섹션 누적 |

---

## 프로세스: mode=spec

### Step 1. 입력 로딩

1. `{spec_path}/SPEC.md`를 Read한다
2. 프로젝트 컨텍스트를 Read한다 (docs/PROJECT.md, docs/ARCHITECTURE.md, docs/CONVENTIONS.md)

### Step 2. 구조적 검증

형식과 필수 요소의 존재를 확인한다.

| # | 검증 항목 | 기준 | 실패 시 판정 |
|---|----------|------|-------------|
| S-1 | 필수 섹션 10개 존재 | Background, Goals, Non-goals, User Stories, Functional Requirements, Acceptance Criteria, Edge Cases, Non-functional Requirements, Constraints, Open Questions | Fail |
| S-2 | AC 형식 (GIVEN/WHEN/THEN) | 모든 AC가 GIVEN/WHEN/THEN 3요소를 포함 | Fail |
| S-3 | Open Questions 해소 | OQ 섹션이 "없음" 또는 비어있음 | Fail |
| S-4 | AC 최소 3개 | AC가 3개 이상 정의됨 | Fail |
| S-5 | FR 번호 체계 | [FR-NN] 형식으로 번호가 부여됨 | Warning |
| S-6 | 버전/상태 메타데이터 | 버전, 작성일, 상태가 기재됨 | Warning |

### Step 3. 의미적 검증

내용의 일관성과 완전성을 확인한다.

| # | 검증 항목 | 기준 | 실패 시 판정 |
|---|----------|------|-------------|
| M-1 | Goals <-> FR <-> AC 정합 | 모든 Goal에 대응 FR 존재, 모든 FR에 대응 AC 존재 | Fail |
| M-2 | Non-goals와 Goals 모순 없음 | Goals와 Non-goals 사이에 모순/중복 없음 | Fail |
| M-3 | 제약 조건 실현 가능 | Constraints가 FR/AC와 모순되지 않음 | Warning |
| M-4 | 기존 코드/문서 충돌 없음 | ARCHITECTURE.md, CONVENTIONS.md와 충돌 없음 | Warning |
| M-5 | Edge Case 반영 | EC가 AC 또는 FR에 반영되었는지 교차 확인 | Warning |
| M-6 | NFR 측정 가능성 | NFR이 정량적 기준을 포함 | Warning |

### Step 4. 도메인 검증

프로젝트 아키텍처 및 컨벤션과의 정합성을 확인한다.

| # | 검증 항목 | 기준 | 실패 시 판정 |
|---|----------|------|-------------|
| D-1 | 아키텍처 정합 | spec의 기능이 기존 아키텍처와 호환 | Fail |
| D-2 | 컨벤션 준수 | 네이밍, 구조, 패턴이 CONVENTIONS.md와 일치 | Warning |

### Step 5. 테스트 시나리오 도출 (TDD Red)

모든 AC에서 테스트 시나리오를 생성한다.

1. 각 AC의 GIVEN/WHEN/THEN을 테스트 케이스로 변환한다
2. 정상 케이스 + 예외 케이스 + 경계값 케이스를 모두 포함한다
3. Edge Cases(EC) 항목에서 추가 시나리오를 도출한다
4. 유형을 분류한다: `unit` / `integration` / `e2e`
5. `{spec_path}/tests/TEST-SCENARIOS.md`에 작성한다

### Step 6. VERIFY.md 작성

검증 결과를 VERIFY.md의 SPEC 검증 섹션으로 작성한다 (아래 출력 형식 참조).

### Step 7. 판정

판정 로직에 따라 최종 판정을 내리고 VERIFY.md에 기록한다.

---

## 프로세스: mode=tasks

### Step 1. 입력 로딩

1. `{spec_path}/TASKS.md`를 Read한다
2. `{spec_path}/SPEC.md`를 Read한다
3. `{spec_path}/tests/TEST-SCENARIOS.md`를 Read한다
4. `{spec_path}/SPEC-PLAN.md`를 Read한다 (존재 시)

### Step 2. AC 커버리지 검증

| # | 검증 항목 | 기준 | 실패 시 판정 |
|---|----------|------|-------------|
| T-1 | 모든 AC >= 1 태스크에 매핑 | SPEC.md의 모든 AC가 TASKS.md의 최소 1개 태스크에 할당 | Fail |
| T-2 | 역매핑 완전성 | TASKS.md의 모든 태스크가 최소 1개 AC에 매핑 | Warning |

### Step 3. TS 커버리지 검증

| # | 검증 항목 | 기준 | 실패 시 판정 |
|---|----------|------|-------------|
| T-3 | 모든 TS >= 1 태스크에 할당 | TEST-SCENARIOS.md의 모든 시나리오가 최소 1개 태스크에 할당 | Fail |
| T-4 | 테스트 유형 균형 | unit/integration/e2e가 적절히 분포 | Warning |

### Step 4. 의존관계 유효성 검증

| # | 검증 항목 | 기준 | 실패 시 판정 |
|---|----------|------|-------------|
| T-5 | 순환 의존 없음 | 태스크 간 의존 그래프에 순환이 없음 | Fail |
| T-6 | 누락 의존 없음 | 의존 대상 태스크가 TASKS.md에 존재 | Fail |
| T-7 | 불필요 의존 없음 | 실제 의존 관계가 아닌 의존 선언 없음 | Warning |

### Step 5. 자기 완결성 검증

| # | 검증 항목 | 기준 | 실패 시 판정 |
|---|----------|------|-------------|
| T-8 | 각 태스크 독립 완료 가능 | 의존 태스크 완료 후 단독 실행 가능 | Fail |
| T-9 | 입출력 명확 | 각 태스크의 입력/출력이 명시됨 | Warning |

### Step 6. 크기 적정성 검증

| # | 검증 항목 | 기준 | 실패 시 판정 |
|---|----------|------|-------------|
| T-10 | 과대 태스크 없음 | 단일 태스크가 AC 3개 이상 커버하지 않음 | Warning |
| T-11 | 과소 태스크 없음 | 의미 있는 단위로 분해됨 (지나치게 세분화되지 않음) | Warning |

### Step 7. 추적 매트릭스 최종화

AC <-> FR <-> TS <-> 태스크 간 추적 매트릭스를 작성하여 VERIFY.md에 포함한다.

### Step 8. VERIFY.md 갱신

검증 결과를 기존 VERIFY.md의 TASKS 검증 섹션으로 누적 추가한다 (아래 출력 형식 참조).

### Step 9. 판정

판정 로직에 따라 최종 판정을 내리고 VERIFY.md에 기록한다.

---

## 판정 로직

### 판정 기준

| 판정 | 조건 | 후속 조치 |
|------|------|----------|
| **Pass** | 모든 항목 통과 (Warning 0개) | 다음 Phase 진행 |
| **Pass with Warnings** | Fail 0개 + Warning 1~2개 | 다음 Phase 진행 가능, Warning 기록 |
| **Fail** | Fail 1개 이상, 또는 Warning 3개 이상 | 재작성 지시 |

### Fail 시 재작성 지시 형식

```
## 재작성 지시

판정: Fail
사유: {Fail 항목 요약}

### 수정 필요 항목
| # | 항목 | 현재 상태 | 수정 방향 |
|---|------|----------|----------|
| 1 | {항목} | {문제 설명} | {구체적 수정 지침} |

### 우선순위
1. {가장 중요한 수정}
2. {다음 수정}
```

---

## 출력 형식: VERIFY.md

VERIFY.md는 누적 저널 방식으로 Phase별 섹션을 추가한다.

### VERIFY.md 전체 구조

```markdown
# Validation Journal: {기능명}

## SPEC 검증 (Phase 2: SPEC-VERIFY)
- 수행일: YYYY-MM-DD
- 워커: opal-task-agent -> op-sdd-verify (mode=spec)

### 구조적 검증
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| S-1 | 필수 섹션 10개 존재 | {Pass/Warning/Fail} | |
| S-2 | AC 형식 (GIVEN/WHEN/THEN) | {Pass/Warning/Fail} | {N}개 AC |
| S-3 | Open Questions 해소 | {Pass/Warning/Fail} | {N}개 잔존 |
| S-4 | AC 최소 3개 | {Pass/Warning/Fail} | |
| S-5 | FR 번호 체계 | {Pass/Warning/Fail} | |
| S-6 | 버전/상태 메타데이터 | {Pass/Warning/Fail} | |

### 의미적 검증
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| M-1 | Goals <-> FR <-> AC 정합 | {Pass/Warning/Fail} | |
| M-2 | Non-goals와 Goals 모순 없음 | {Pass/Warning/Fail} | |
| M-3 | 제약 조건 실현 가능 | {Pass/Warning/Fail} | |
| M-4 | 기존 코드/문서 충돌 없음 | {Pass/Warning/Fail} | |
| M-5 | Edge Case 반영 | {Pass/Warning/Fail} | |
| M-6 | NFR 측정 가능성 | {Pass/Warning/Fail} | |

### 도메인 검증
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| D-1 | 아키텍처 정합 | {Pass/Warning/Fail} | |
| D-2 | 컨벤션 준수 | {Pass/Warning/Fail} | |

### 테스트 시나리오 도출
- 총 시나리오: {N}개 (unit: {n}, integration: {n}, e2e: {n})
- AC 커버리지: {n}% ({n}/{n} AC -> {n} 시나리오)

### 판정: {Pass / Pass with Warnings / Fail}

---

## TASKS 검증 (Phase 5: TASKS-VERIFY)
- 수행일: YYYY-MM-DD
- 워커: opal-task-agent -> op-sdd-verify (mode=tasks)

### 검증 항목
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| T-1 | AC 커버리지 (모든 AC >= 1 태스크) | {Pass/Warning/Fail} | |
| T-2 | 역매핑 완전성 | {Pass/Warning/Fail} | |
| T-3 | TS 커버리지 (모든 TS >= 1 태스크) | {Pass/Warning/Fail} | |
| T-4 | 테스트 유형 균형 | {Pass/Warning/Fail} | |
| T-5 | 순환 의존 없음 | {Pass/Warning/Fail} | |
| T-6 | 누락 의존 없음 | {Pass/Warning/Fail} | |
| T-7 | 불필요 의존 없음 | {Pass/Warning/Fail} | |
| T-8 | 각 태스크 독립 완료 가능 | {Pass/Warning/Fail} | |
| T-9 | 입출력 명확 | {Pass/Warning/Fail} | |
| T-10 | 과대 태스크 없음 | {Pass/Warning/Fail} | |
| T-11 | 과소 태스크 없음 | {Pass/Warning/Fail} | |

### 추적 매트릭스 (최종)
| AC | FR | TS | 담당 태스크 | 커버리지 |
|----|----|----|-----------|----------|

### 판정: {Pass / Fail}

---

## DONE 검증 (Phase 7)
(Phase 6 완료 시 추가)
```

---

## 출력 형식: TEST-SCENARIOS.md

mode=spec에서 AC로부터 도출한 테스트 시나리오를 작성한다.

### TEST-SCENARIOS.md 구조

```markdown
# Test Scenarios: {기능명}

> 버전: 1.0 | 작성일: YYYY-MM-DD | SPEC.md v{X.Y} 기준
> 상태: Red (TDD -- 시나리오만 정의, 구현 전)

## 추적 매트릭스

| AC | 시나리오 ID | 유형 | 설명 | 상태 |
|----|-----------|------|------|------|
| AC-01 | TS-01 | unit | {시나리오 설명} | Red |
| AC-01 | TS-02 | integration | {시나리오 설명} | Red |
| AC-02 | TS-03 | unit | {시나리오 설명} | Red |
| ... | ... | ... | ... | ... |

## 시나리오 상세

### TS-01: {시나리오명}

- **출처**: AC-01
- **유형**: unit / integration / e2e
- **GIVEN**: {사전 조건}
- **WHEN**: {행위}
- **THEN**: {기대 결과}
- **테스트 케이스**:
  - 정상: {정상 입력 -> 기대 출력}
  - 예외: {예외 입력 -> 기대 에러}
  - 경계값: {경계 입력 -> 기대 동작}
- **검증 방법**: {자동/수동, 도구}
- **매핑**: 태스크 미할당 (TASKS 단계에서 할당)

### TS-02: {시나리오명}
...
```

### 상태 값

| 상태 | 의미 |
|------|------|
| Red | 시나리오 정의됨, 테스트 미작성 (TDD Red) |
| Green | 테스트 작성 + 통과 |
| Fail | 테스트 작성 + 실패 |
| Skip | 의도적 제외 (사유 명시) |

---

## 품질 체크리스트

### mode=spec 체크리스트

SPEC 검증 완료 후 자체 검증한다:

- [ ] 구조적 검증 6개 항목(S-1~S-6)을 모두 수행했는가
- [ ] 의미적 검증 6개 항목(M-1~M-6)을 모두 수행했는가
- [ ] 도메인 검증 2개 항목(D-1~D-2)을 모두 수행했는가
- [ ] 모든 AC에서 최소 1개 테스트 시나리오를 도출했는가
- [ ] 정상/예외/경계값 케이스를 포함했는가
- [ ] TEST-SCENARIOS.md의 추적 매트릭스가 완전한가
- [ ] VERIFY.md SPEC 검증 섹션이 템플릿 형식에 맞는가
- [ ] 판정에 구체적 근거가 첨부되었는가

### mode=tasks 체크리스트

TASKS 검증 완료 후 자체 검증한다:

- [ ] 커버리지 검증 4개 항목(T-1~T-4)을 모두 수행했는가
- [ ] 의존관계 검증 3개 항목(T-5~T-7)을 모두 수행했는가
- [ ] 자기 완결성 검증 2개 항목(T-8~T-9)을 모두 수행했는가
- [ ] 크기 적정성 검증 2개 항목(T-10~T-11)을 모두 수행했는가
- [ ] 추적 매트릭스(AC<->FR<->TS<->태스크)가 완전한가
- [ ] VERIFY.md TASKS 검증 섹션이 기존 내용에 누적 추가되었는가
- [ ] 판정에 구체적 근거가 첨부되었는가

---

## 완료 후 동작

워커는 검증을 직접 종결하지 않는다. 검증이 완료되면 결과를 오케스트레이터에 반환한다. 문서 QA(요구사항→설계 검토)는 별도 QA Gate 단계 없이 PM이 PM Gate에서 직접 수행한다. (동작 검증(TEST-SCENARIO 실행 등)은 본 verify 워커가 수행하는 독립 영역으로 불변.)

**반환 형식**:

mode=spec:
```
SPEC-VERIFY 완료: {spec_path}/VERIFY.md + {spec_path}/tests/TEST-SCENARIOS.md | 판정: {Pass / Pass with Warnings / Fail}
```

mode=tasks:
```
TASKS-VERIFY 완료: {spec_path}/VERIFY.md (TASKS 섹션 추가) | 판정: {Pass / Fail}
```

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-05 | 초기 작성 (080-opp-opsdd-design-proposal Step 3) |
| v1.1 | 2026-06-07 | QA→PM Gate 통합 정합화 — "완료 후 동작"의 "오케스트레이터가 QA Gate 실행 여부 결정" 표현을 "문서 QA는 PM Gate가 직접 수행(별도 QA Gate 없음)"으로 수정. 본 verify 워커의 동작 검증(TEST-SCENARIO 실행) 영역은 독립·불변임을 명시 (014 Phase 4-2) |
