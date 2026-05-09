# PLAN: PLAN 워커 TEST-SCENARIO 통합 + QA Gate 제거 + PM Gate 검증 강화

> 작성일: 2026-04-13 | 입력: TASK.md
> 모드: Multi-Feature

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`opal-pilot-dev` / `opal-pilot-dev-short`의 **PLAN 단계**와 **EXECUTE/TEST 단계** 양쪽에서 QA Gate를 제거하고, PM Gate가 직접 산출물을 Read·검증하는 방식으로 파이프라인을 슬림화한다. PLAN 단계는 TEST-SCENARIO 별도 워커 디스패치를 제거하고 PLAN 워커(`op-dev-plan`)가 PLAN.md + TEST-SCENARIO.md를 통합 작성한다. EXECUTE/TEST 단계는 QA-EXECUTE 에이전트를 제거하고 PM Gate가 TEST-SCENARIO.md를 직접 Read하여 검증한다. 변경 대상은 markdown 스킬 문서 3개(`op-dev-plan/SKILL.md`, `opal-pilot-dev/SKILL.md`, `opal-pilot-dev-short/SKILL.md`)다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | op-dev-plan TEST-SCENARIO 통합 | R-1 | P0 | 없음 |
| F-002 | opal-pilot-dev 파이프라인 전체 슬림화 | R-2, R-3, R-6 | P0 | F-001 |
| F-003 | opal-pilot-dev-short 파이프라인 전체 슬림화 | R-4, R-5, R-7 | P0 | F-001 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (op-dev-plan 통합)
    ├── F-002 (opal-pilot-dev 전체 슬림화: PLAN + EXECUTE/TEST)
    └── F-003 (opal-pilot-dev-short 전체 슬림화: PLAN + EXECUTE/TEST)
```

F-001이 선행되어야 F-002·F-003의 디스패치 프롬프트 설명이 정확해진다. F-002·F-003은 서로 독립적으로 병렬 작성 가능하다. F-002는 동일 파일의 PLAN + EXECUTE/TEST 변경을 한 번에 처리한다 (파일을 두 번 여는 것 방지).

---

## 2. 기능별 분석

### F-001: op-dev-plan TEST-SCENARIO 통합

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-dev-plan/SKILL.md` | PLAN 워커 스킬 정의 | 수정 |
| 참조(형식) | `opal/skills/op-dev-test-scenario/SKILL.md` | TEST-SCENARIO.md 출력 형식 참조 | 읽기 전용 |

#### 2.1.2 현재 구현

- **프로세스 Step 수**: Step 1(가이드 로딩) ~ Step 10(결과 반환), 총 10 Step
- **보장 출력**: `PLAN.md` 단독 (frontmatter `description` 및 `입력/출력` 테이블)
- **Step 10 내용**: "워커는 PLAN.md 경로와 요약을 오케스트레이터에 반환한다. 워커는 QA를 호출하지 않는다. 오케스트레이터가 QA 에이전트를 별도로 호출한다."
- **TEST-SCENARIO 관련 언급**: 없음 (완전히 별도 스킬로 위임)

#### 2.1.3 영향 범위

- `opal-pilot-dev/SKILL.md` — PLAN 워커가 두 산출물을 반환하면 "3-2. TEST-SCENARIO 디스패치" 섹션이 불필요해짐
- `opal-pilot-dev-short/SKILL.md` — 동일한 이유로 "TEST-SCENARIO 디스패치" 섹션 제거 가능
- `op-dev-test-scenario/SKILL.md` — 수정 대상 아님 (호출하지 않는 것으로 충분, TASK.md 제약 §5)

---

### F-002: opal-pilot-dev 파이프라인 전체 슬림화

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | Full Task 오케스트레이터 | 수정 |

#### 2.2.2 현재 구현

**STEP 3 구조**:
- 3-1. PLAN 디스패치 (advanced 모델)
- 3-2. TEST-SCENARIO 디스패치 (light 모델) — PLAN 완료 직후 연속 디스패치
- TEST-SCENARIO 스킵 조건 (문서 전용 작업)
- 두 워커 완료 → State Gate → **QA Gate** (op-dev-qa) → State Gate → **PM Gate** → State Gate → 사용자 보고

**STATE.md 진행 현황 행 예시 (PLAN 관련)**:
```
| 10 | PLAN | 작업 | ⬜ | - |
| 11 | PLAN | PLAN.md 생성 | ⬜ | - |
| 12 | TEST-SCENARIO | 작업 | ⬜ | - |
| 13 | TEST-SCENARIO | TEST-SCENARIO.md 생성 | ⬜ | - |
| 14 | TEST-SCENARIO | State Gate | ⬜ | - |
| 15 | PLAN | QA Gate | ⬜ | - |
| 16 | PLAN | QA-PLAN.md 생성 | ⬜ | - |
| 17 | PLAN | State Gate | ⬜ | - |
| 18 | PLAN | PM Gate | ⬜ | - |
| 19 | PLAN | State Gate | ⬜ | - |
| 20 | PLAN | 사용자 확인 | ⬜ | - |
```

**STEP 5 (TEST) PASS 시 구조**:
```
QA Gate (op-dev-qa — 체크리스트 갱신 포함) → State Gate
→ PM Gate (TEST 결과 검토 + 체크리스트 갱신 상태 확인. 미갱신 시 QA 재소환) → State Gate
→ 모든 체크리스트 갱신 완료 확인 후 DONE.md 생성
```

**STATE.md TEST 단계 행 예시**:
```
| 25 | TEST | QA Gate | ⬜ | - |
| 26 | TEST | QA-EXECUTE.md 생성 | ⬜ | - |
| 27 | TEST | State Gate | ⬜ | - |
| 28 | TEST | PM Gate | ⬜ | - |
| 29 | TEST | DONE.md 생성 | ⬜ | - |
| 30 | TEST | State Gate | ⬜ | - |
| 31 | TEST | 사용자 확인 | ⬜ | - |
```

**PM Gate 점검 목록**:
- PLAN+TEST-SCENARIO Phase: TASK.md, PLAN.md, TEST-SCENARIO.md, **QA-PLAN.md** | 체크리스트 위치: TASK.md 요구사항, PLAN.md §3, §4
- EXECUTE Phase: **QA-EXECUTE.md** | 체크리스트 위치: PLAN.md §3

#### 2.2.3 영향 범위

- STATE.md 도메인 설정의 단계 목록(`TEST-SCENARIO` 단계 제거 여부 검토 필요)
- Harness 헤더의 모드 설명에 `TEST-SCENARIO` 표기 — 단계로서는 제거되지만 산출물은 존재하므로 표기 유지 가능 (설계 결정: 단계 목록에서 TEST-SCENARIO를 PLAN 하위로 흡수)

---

### F-003: opal-pilot-dev-short 파이프라인 전체 슬림화

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-dev-short/SKILL.md` | Short Task 오케스트레이터 | 수정 |

#### 2.3.2 현재 구현

**STEP 2 구조**:
- PLAN 디스패치 (advanced 모델)
- TEST-SCENARIO 스킵 조건
- TEST-SCENARIO 디스패치 (PLAN 완료 직후 연속 디스패치, light 모델)
- 워커 완료 → State Gate → **QA Gate** → State Gate → **PM Gate** → State Gate → 사용자 보고

**STATE.md 진행 현황 행 예시 (PLAN 관련)**:
```
| 4 | PLAN | 작업 | ⬜ | - |
| 5 | PLAN | PLAN.md 생성 | ⬜ | - |
| 6 | TEST-SCENARIO | 작업 | ⬜ | - |
| 7 | TEST-SCENARIO | TEST-SCENARIO.md 생성 | ⬜ | - |
| 8 | TEST-SCENARIO | State Gate | ⬜ | - |
| 9 | PLAN | QA Gate | ⬜ | - |
| 10 | PLAN | QA-PLAN.md 생성 | ⬜ | - |
| 11 | PLAN | State Gate | ⬜ | - |
| 12 | PLAN | PM Gate | ⬜ | - |
| 13 | PLAN | State Gate | ⬜ | - |
| 14 | PLAN | 사용자 확인 | ⬜ | - |
```

**STEP 4 (TEST) PASS 시 구조**:
```
QA Gate (op-dev-qa — 체크리스트 갱신 포함) → State Gate
→ PM Gate (TEST 결과 검토 + 체크리스트 갱신 상태 확인. 미갱신 시 QA 재소환) → State Gate
→ 모든 체크리스트 갱신 완료 확인 후 DONE.md 생성
```

**STATE.md TEST 단계 행 예시**:
```
| 19 | TEST | QA Gate | ⬜ | - |
| 20 | TEST | QA-EXECUTE.md 생성 | ⬜ | - |
| 21 | TEST | State Gate | ⬜ | - |
| 22 | TEST | PM Gate | ⬜ | - |
| 23 | TEST | DONE.md 생성 | ⬜ | - |
| 24 | TEST | State Gate | ⬜ | - |
| 25 | TEST | 사용자 확인 | ⬜ | - |
```

**PM Gate 점검 목록**:
- PLAN+TEST-SCENARIO Phase: TASK.md, PLAN.md, TEST-SCENARIO.md, **QA-PLAN.md** | 체크리스트 위치: TASK.md 요구사항, PLAN.md §3, §4
- EXECUTE Phase: **QA-EXECUTE.md** | 체크리스트 위치: PLAN.md §3

#### 2.3.3 영향 범위

- 행 번호 재정렬 필요 (TEST-SCENARIO 행 4개 + QA Gate 행 3개 제거 → 번호 압축)
- Harness 헤더의 모드 설명: `Short Task (TASK → PLAN → TEST-SCENARIO → EXECUTE → TEST)` — "TEST-SCENARIO" 를 독립 단계에서 제거할지 검토 필요 (PLAN에 통합됨을 반영)

---

## 3. 기능별 설계

### F-001: op-dev-plan TEST-SCENARIO 통합

#### 3.1.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 |
|---|------|------|--------------|
| 1 | `opal/skills/op-dev-plan/SKILL.md` | 스킬 | frontmatter 보장 출력 갱신, Step 10 추가(TEST-SCENARIO 작성), 기존 Step 10을 Step 11로 이동 |

#### 3.1.2 설계 상세

**frontmatter `description` 변경**:
- 변경 전: `보장 출력: PLAN.md (기능 중심 구조, 실행 체크리스트+복잡도 판별+기능-QA 매트릭스 포함).`
- 변경 후: `보장 출력: PLAN.md (기능 중심 구조, 실행 체크리스트+복잡도 판별+기능-QA 매트릭스 포함), TEST-SCENARIO.md.`

**입력/출력 테이블 변경**:
- `보장 출력` 행에 `PLAN.md, TEST-SCENARIO.md` 명시

**프로세스 Step 추가 (Step 10 신설, 기존 Step 10 → Step 11)**:

Step 10: TEST-SCENARIO.md 작성

```
### Step 10: TEST-SCENARIO.md 작성

PLAN.md 완료 후 연속으로 TEST-SCENARIO.md를 작성한다.

PLAN 단계에서 코드 분석과 설계를 완료한 상태이므로, 이 시점이 테스트 시나리오 작성에 가장 적합하다.

**형식**: `op-dev-test-scenario/SKILL.md`의 "TEST-SCENARIO.md 통일 형식"을 따른다.

**작성 범위**:
- **시나리오 목록**: TASK.md 요구사항 × PLAN.md 기능별 설계(§3.N.5 테스트 시나리오)를 기반으로 S-NNN 단위로 도출. 각 시나리오에 대상/조건/기대 결과/도구를 작성한다. (실행 명령/결과/상세는 op-dev-test-agent가 채움)
- **코드 품질**: 린트 / 타입 체크 / 포맷터 항목 (결과/상세는 op-dev-test-agent가 채움)
- **보안**: 하드코딩 시크릿 스캔 / .gitignore 확인 항목
- **회귀 테스트**: 테스트 스위트 항목
- **판정**: op-dev-test-agent가 채울 영역 표기
- **설계 피드백**: 시나리오 도출 과정에서 발견한 PLAN 빈틈 기록 (없으면 "없음")

**스킵 조건**: 작업 유형이 문서 전용(`.md` 파일만 수정, 소스 코드 없음)이면 TEST-SCENARIO.md 작성을 스킵한다. 스킵 시 결과 반환에 "TEST-SCENARIO: 문서 전용 작업으로 스킵" 표기.

**저장 경로**: `tasks/{NNN}-{태스크명}/TEST-SCENARIO.md`
```

**Step 11(결과 반환) 변경**:
- 변경 전: "워커는 PLAN.md 경로와 요약을 오케스트레이터에 반환한다."
- 변경 후: "워커는 PLAN.md 경로와 TEST-SCENARIO.md 경로(또는 스킵 여부)를 요약과 함께 오케스트레이터에 반환한다."
- "워커는 QA를 호출하지 않는다. 오케스트레이터가 QA 에이전트를 별도로 호출한다." 문구 제거 (QA Gate가 PLAN 단계에서 제거되므로)

**변경이력 추가**:
```
| v2.1 | 2026-04-13 | Step 10 TEST-SCENARIO.md 작성 추가 + Step 11 결과 반환 갱신. 보장 출력에 TEST-SCENARIO.md 포함. (115) |
```

#### 3.1.3 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC ①: Step 10 존재 | 문서 검증 | 프로세스 섹션에 Step 10이 존재하고 TEST-SCENARIO.md 형식이 명시됨 |
| TS-002 | R-1 AC ②: frontmatter 보장 출력 | 문서 검증 | `description`의 보장 출력에 TEST-SCENARIO.md가 포함됨 |
| TS-003 | R-1 AC ③: 결과 반환 Step에 경로 포함 | 문서 검증 | Step 11(결과 반환)에 TEST-SCENARIO.md 경로 포함 명시 |

---

### F-002: opal-pilot-dev 파이프라인 전체 슬림화

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 |
|---|------|------|--------------|
| 1 | `opal/skills/opal-pilot-dev/SKILL.md` | 오케스트레이터 | STEP 3에서 3-2 TEST-SCENARIO 디스패치 제거 + QA Gate 제거 + PM Gate 강화 + STATE.md 행 예시 갱신 |

#### 3.2.2 설계 상세

**Harness 헤더 모드 설명 변경**:
- 변경 전: `모드: Full Task (TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST)`
- 변경 후: `모드: Full Task (TASK → ANALYSIS → PLAN → EXECUTE → TEST)`
  - TEST-SCENARIO는 PLAN 워커 내부에서 작성되므로 독립 단계에서 제거

**STEP 3 구조 변경**:

변경 전:
```
3-1. PLAN 디스패치 (advanced)
3-2. TEST-SCENARIO 디스패치 (PLAN 완료 직후, light)
TEST-SCENARIO 스킵 조건
두 워커 완료 → State Gate → QA Gate → State Gate → PM Gate → State Gate → 사용자 보고
```

변경 후:
```
3-1. PLAN 디스패치 (advanced)
  - 산출물 저장 경로에 TEST-SCENARIO.md 경로 추가
PLAN 완료
  → State Gate
  → PM Gate (PLAN.md + TEST-SCENARIO.md 검증 — 점검 목록 참조) → State Gate
  → 사용자에게 PLAN + TEST-SCENARIO 함께 보고. 승인 = EXECUTE 시작 허가.
```

**3-1. PLAN 디스패치 프롬프트 수정**:
- 기존 `**산출물 저장 경로**: {PLAN.md 경로}, {execution-plan.json 경로 (FE/BE 시)}`
- 변경: `**산출물 저장 경로**: {PLAN.md 경로}, {TEST-SCENARIO.md 경로}, {execution-plan.json 경로 (FE/BE 시)}`

**PM Gate 내용 강화** (STEP 3 내 서술):

```
→ **PM Gate** (PLAN.md + TEST-SCENARIO.md 직접 검증):
  1. `{PLAN.md 경로}` Read — §4.2 실행 체크리스트, §5 QA 체크리스트 확인
  2. `{TEST-SCENARIO.md 경로}` Read — 시나리오 목록, 코드 품질, 보안 항목 확인
  3. 검증 체크리스트:
     - [ ] TASK.md 요구사항 전체 커버 여부 (PLAN.md §1.2 기능 목록 대조)
     - [ ] PLAN.md §4.2 실행 체크리스트 완성도 (소속 F-ID, 완료 기준 명시)
     - [ ] TEST-SCENARIO.md 시나리오가 TASK.md 요구사항 전체를 커버하는가
     - [ ] TEST-SCENARIO.md 보안 항목(시크릿 스캔, .gitignore) 포함 여부
     - [ ] 설계 피드백 섹션에 미해결 빈틈이 없는가
→ **State Gate**
```

**STATE.md 도메인 설정 변경**:
- 단계 목록: `TASK / ANALYSIS / PLAN / EXECUTE / TEST` (TEST-SCENARIO 독립 단계 제거)
- 산출물: `TASK.md, ANALYSIS.md, PLAN.md, TEST-SCENARIO.md, DONE.md` (QA-PLAN.md 제거)

**STATE.md 진행 현황 행 예시 변경**:

변경 전 (10~20행):
```
| 10 | PLAN | 작업 | ⬜ | - |
| 11 | PLAN | PLAN.md 생성 | ⬜ | - |
| 12 | TEST-SCENARIO | 작업 | ⬜ | - |
| 13 | TEST-SCENARIO | TEST-SCENARIO.md 생성 | ⬜ | - |
| 14 | TEST-SCENARIO | State Gate | ⬜ | - |
| 15 | PLAN | QA Gate | ⬜ | - |
| 16 | PLAN | QA-PLAN.md 생성 | ⬜ | - |
| 17 | PLAN | State Gate | ⬜ | - |
| 18 | PLAN | PM Gate | ⬜ | - |
| 19 | PLAN | State Gate | ⬜ | - |
| 20 | PLAN | 사용자 확인 | ⬜ | - |
```

변경 후 (10~16행, 이후 행 번호 재조정):
```
| 10 | PLAN | 작업 | ⬜ | - |
| 11 | PLAN | PLAN.md 생성 | ⬜ | - |
| 12 | PLAN | TEST-SCENARIO.md 생성 | ⬜ | - |
| 13 | PLAN | State Gate | ⬜ | - |
| 14 | PLAN | PM Gate | ⬜ | - |
| 15 | PLAN | State Gate | ⬜ | - |
| 16 | PLAN | 사용자 확인 | ⬜ | - |
```

이후 EXECUTE·TEST 행들은 번호를 재조정한다 (21→17, 22→18, ... 31→24).

**PM Gate 점검 목록 섹션 변경**:

변경 전:
```
| PLAN+TEST-SCENARIO | TASK.md, PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | TASK.md 요구사항, PLAN.md §3, §4 |
```

변경 후:
```
| PLAN | TASK.md, PLAN.md, TEST-SCENARIO.md | TASK.md 요구사항, PLAN.md §4.2, §5; TEST-SCENARIO.md 시나리오 목록/보안/설계 피드백 |
```

**[추가] STEP 5 (TEST) PASS 시 구조 변경** (R-6):

변경 전:
```
QA Gate (op-dev-qa — 체크리스트 갱신 포함) → State Gate
→ PM Gate (TEST 결과 검토 + 체크리스트 갱신 상태 확인. 미갱신 시 QA 재소환) → State Gate
→ 모든 체크리스트 갱신 완료 확인 후 DONE.md 생성
```

변경 후:
```
→ PM Gate (TEST-SCENARIO.md 직접 검증):
  1. `{TEST-SCENARIO.md 경로}` Read — 시나리오 PASS/FAIL 전체 확인
  2. 검증 체크리스트:
     - [ ] TEST-SCENARIO.md 모든 시나리오 PASS
     - [ ] 코드 품질 항목(린트/타입/포맷) 모두 Pass
     - [ ] 보안 항목(시크릿 스캔/.gitignore) Pass
     - [ ] 회귀 테스트 항목 Pass
     - [ ] 설계 피드백 미해결 빈틈 없음
→ State Gate
→ DONE.md 생성
→ 사용자에게 완료 보고
```

**[추가] PM Gate 점검 목록 EXECUTE 행 변경**:
- 변경 전: `| EXECUTE | QA-EXECUTE.md | PLAN.md §3 |`
- 변경 후: `| TEST | TEST-SCENARIO.md | TEST-SCENARIO.md 시나리오 결과/코드품질/보안/회귀 |`

**[추가] 산출물 목록 최종 변경**:
- F-002(PLAN 변경)에서 이미 QA-PLAN.md 제거. R-6으로 QA-EXECUTE.md도 제거.
- 결과: `산출물: TASK.md, ANALYSIS.md, PLAN.md, TEST-SCENARIO.md, DONE.md`

**[추가] STATE.md TEST 단계 행 예시 변경** (F-002 PLAN 변경 이후 번호 기준):

변경 전 (TEST QA Gate 관련 3행):
```
| N | TEST | QA Gate | ⬜ | - |
| N+1 | TEST | QA-EXECUTE.md 생성 | ⬜ | - |
| N+2 | TEST | State Gate | ⬜ | - |
| N+3 | TEST | PM Gate | ⬜ | - |
...
```

변경 후 (QA Gate 3행 제거, 이후 번호 재조정):
```
| N | TEST | 작업 | ⬜ | - |
| N+1 | TEST | State Gate | ⬜ | - |
| N+2 | TEST | PM Gate | ⬜ | - |
| N+3 | TEST | DONE.md 생성 | ⬜ | - |
| N+4 | TEST | State Gate | ⬜ | - |
| N+5 | TEST | 사용자 확인 | ⬜ | - |
```

> 행 번호는 PLAN 변경(F-002) 적용 후 재조정된 번호 기준으로 연속 재조정한다. 최종 전체 행 번호는 1부터 연속적이어야 한다.

**변경이력 추가**:
```
| v2.9 | 2026-04-13 | STEP 3에서 TEST-SCENARIO 별도 디스패치 + QA Gate 제거. PLAN 워커가 TEST-SCENARIO.md 통합 작성. PM Gate에 PLAN.md+TEST-SCENARIO.md Read + 검증 체크리스트 추가. STEP 5 TEST QA Gate 제거, PM Gate에 TEST-SCENARIO.md Read + 검증 체크리스트 추가. STATE.md 행 예시 전체 갱신. (115) |
```

#### 3.2.3 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | R-2 AC ①: TEST-SCENARIO 별도 디스패치 없음 | 문서 검증 | STEP 3에 "3-2. TEST-SCENARIO 디스패치" 섹션이 없음 |
| TS-005 | R-2 AC ②: PLAN QA Gate 없음 | 문서 검증 | STEP 3 흐름에 QA Gate / QA-PLAN.md 참조 없음 |
| TS-006 | R-2 AC ③: PLAN PM Gate Read 절차 | 문서 검증 | PM Gate에 PLAN.md Read → TEST-SCENARIO.md Read → 체크리스트 절차 명시 |
| TS-007 | R-3 AC: PLAN STATE.md 행 예시 갱신 | 문서 검증 | TEST-SCENARIO 단계 행 없음. PLAN 하위에 TEST-SCENARIO.md 생성 행 존재. QA Gate/QA-PLAN.md 행 없음 |
| TS-012 | R-6 AC ①: TEST QA Gate 없음 | 문서 검증 | STEP 5 PASS 흐름에 QA Gate / QA-EXECUTE.md 참조 없음 |
| TS-013 | R-6 AC ②: TEST PM Gate Read 절차 | 문서 검증 | STEP 5 PM Gate에 TEST-SCENARIO.md Read → 검증 체크리스트 절차 명시 |
| TS-014 | R-6 AC ③: PM Gate 점검 목록 갱신 | 문서 검증 | PM Gate 점검 목록에 QA-EXECUTE.md 없음. TEST-SCENARIO.md 검증 항목 존재 |
| TS-015 | R-6 AC ④: TEST STATE.md 행 예시 갱신 | 문서 검증 | TEST 단계에 QA Gate / QA-EXECUTE.md 생성 행 없음. 전체 행 번호 연속 |

---

### F-003: opal-pilot-dev-short 파이프라인 전체 슬림화

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 |
|---|------|------|--------------|
| 1 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 오케스트레이터 | STEP 2에서 TEST-SCENARIO 별도 디스패치 제거 + QA Gate 제거 + PM Gate 강화 + STATE.md 행 예시 갱신 |

#### 3.3.2 설계 상세

**Harness 헤더 모드 설명 변경**:
- 변경 전: `모드: Short Task (TASK → PLAN → TEST-SCENARIO → EXECUTE → TEST)`
- 변경 후: `모드: Short Task (TASK → PLAN → EXECUTE → TEST)`

**STEP 2 구조 변경**:

변경 전:
```
PLAN 디스패치 (advanced)
TEST-SCENARIO 스킵 조건
TEST-SCENARIO 디스패치 (light)
워커 완료 → State Gate → QA Gate → State Gate → PM Gate → State Gate → 사용자 보고
```

변경 후:
```
PLAN 디스패치 (advanced)
  - 산출물 저장 경로에 TEST-SCENARIO.md 경로 추가
  - 문서 전용 스킵 조건 안내 포함 (op-dev-plan이 자체 판별)
PLAN 완료
  → State Gate
  → PM Gate (PLAN.md + TEST-SCENARIO.md 검증 — 점검 목록 참조) → State Gate
  → 사용자에게 PLAN + TEST-SCENARIO 함께 보고. 승인 = EXECUTE 시작 허가.
```

**PM Gate 내용 강화** (opal-pilot-dev와 동일 구조):

```
→ **PM Gate** (PLAN.md + TEST-SCENARIO.md 직접 검증):
  1. `{PLAN.md 경로}` Read — §4.2 실행 체크리스트, §5 QA 체크리스트 확인
  2. `{TEST-SCENARIO.md 경로}` Read (문서 전용 스킵 시 해당 없음)
  3. 검증 체크리스트:
     - [ ] TASK.md 요구사항 전체 커버 여부 (PLAN.md §1.2 기능 목록 대조)
     - [ ] PLAN.md §4.2 실행 체크리스트 완성도 (소속 F-ID, 완료 기준 명시)
     - [ ] TEST-SCENARIO.md 시나리오가 TASK.md 요구사항 전체를 커버하는가
     - [ ] TEST-SCENARIO.md 보안 항목(시크릿 스캔, .gitignore) 포함 여부
     - [ ] 설계 피드백 섹션에 미해결 빈틈이 없는가
     - [ ] 규모 기준 초과 시 Full Task 에스컬레이션 검토 여부
→ **State Gate**
```

**STATE.md 도메인 치환값 변경**:
- 단계 목록: `TASK / PLAN / EXECUTE / TEST` (TEST-SCENARIO 독립 단계 제거)

**STATE.md 진행 현황 행 예시 변경**:

변경 전 (4~14행):
```
| 4 | PLAN | 작업 | ⬜ | - |
| 5 | PLAN | PLAN.md 생성 | ⬜ | - |
| 6 | TEST-SCENARIO | 작업 | ⬜ | - |
| 7 | TEST-SCENARIO | TEST-SCENARIO.md 생성 | ⬜ | - |
| 8 | TEST-SCENARIO | State Gate | ⬜ | - |
| 9 | PLAN | QA Gate | ⬜ | - |
| 10 | PLAN | QA-PLAN.md 생성 | ⬜ | - |
| 11 | PLAN | State Gate | ⬜ | - |
| 12 | PLAN | PM Gate | ⬜ | - |
| 13 | PLAN | State Gate | ⬜ | - |
| 14 | PLAN | 사용자 확인 | ⬜ | - |
```

변경 후 (4~10행, 이후 행 번호 재조정):
```
| 4 | PLAN | 작업 | ⬜ | - |
| 5 | PLAN | PLAN.md 생성 | ⬜ | - |
| 6 | PLAN | TEST-SCENARIO.md 생성 | ⬜ | - |
| 7 | PLAN | State Gate | ⬜ | - |
| 8 | PLAN | PM Gate | ⬜ | - |
| 9 | PLAN | State Gate | ⬜ | - |
| 10 | PLAN | 사용자 확인 | ⬜ | - |
```

이후 EXECUTE·TEST 행들은 번호를 재조정한다 (15→11, 16→12, ... 25→18).

**PM Gate 점검 목록 섹션 변경**:

변경 전:
```
| PLAN+TEST-SCENARIO | TASK.md, PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | TASK.md 요구사항, PLAN.md §3, §4 |
```

변경 후:
```
| PLAN | TASK.md, PLAN.md, TEST-SCENARIO.md | TASK.md 요구사항, PLAN.md §4.2, §5; TEST-SCENARIO.md 시나리오 목록/보안/설계 피드백 |
```

**[추가] STEP 4 (TEST) PASS 시 구조 변경** (R-7):

변경 전:
```
QA Gate (op-dev-qa — 체크리스트 갱신 포함) → State Gate
→ PM Gate (TEST 결과 검토 + 체크리스트 갱신 상태 확인. 미갱신 시 QA 재소환) → State Gate
→ 모든 체크리스트 갱신 완료 확인 후 DONE.md 생성
```

변경 후 (opal-pilot-dev와 동일 구조):
```
→ PM Gate (TEST-SCENARIO.md 직접 검증):
  1. `{TEST-SCENARIO.md 경로}` Read — 시나리오 PASS/FAIL 전체 확인
  2. 검증 체크리스트:
     - [ ] TEST-SCENARIO.md 모든 시나리오 PASS
     - [ ] 코드 품질 항목(린트/타입/포맷) 모두 Pass
     - [ ] 보안 항목(시크릿 스캔/.gitignore) Pass
     - [ ] 회귀 테스트 항목 Pass
     - [ ] 설계 피드백 미해결 빈틈 없음
→ State Gate
→ DONE.md 생성
→ 사용자에게 완료 보고
```

**[추가] PM Gate 점검 목록 EXECUTE 행 변경**:
- 변경 전: `| EXECUTE | QA-EXECUTE.md | PLAN.md §3 |`
- 변경 후: `| TEST | TEST-SCENARIO.md | TEST-SCENARIO.md 시나리오 결과/코드품질/보안/회귀 |`

**[추가] STATE.md TEST 단계 행 예시 변경** (F-003 PLAN 변경 이후 번호 기준):

변경 전 (TEST QA Gate 관련 3행):
```
| N | TEST | QA Gate | ⬜ | - |
| N+1 | TEST | QA-EXECUTE.md 생성 | ⬜ | - |
| N+2 | TEST | State Gate | ⬜ | - |
| N+3 | TEST | PM Gate | ⬜ | - |
...
```

변경 후 (QA Gate 3행 제거, 이후 번호 재조정):
```
| N | TEST | 작업 | ⬜ | - |
| N+1 | TEST | State Gate | ⬜ | - |
| N+2 | TEST | PM Gate | ⬜ | - |
| N+3 | TEST | DONE.md 생성 | ⬜ | - |
| N+4 | TEST | State Gate | ⬜ | - |
| N+5 | TEST | 사용자 확인 | ⬜ | - |
```

> 행 번호는 PLAN 변경(F-003) 적용 후 재조정된 번호 기준으로 연속 재조정한다. 최종 전체 행 번호는 1부터 연속적이어야 한다.

**변경이력 추가**:
```
| v2.9 | 2026-04-13 | STEP 2에서 TEST-SCENARIO 별도 디스패치 + QA Gate 제거. PLAN 워커가 TEST-SCENARIO.md 통합 작성. PM Gate에 PLAN.md+TEST-SCENARIO.md Read + 검증 체크리스트 추가. STEP 4 TEST QA Gate 제거, PM Gate에 TEST-SCENARIO.md Read + 검증 체크리스트 추가. STATE.md 행 예시 전체 갱신. (115) |
```

#### 3.3.3 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | R-4 AC ①: TEST-SCENARIO 별도 디스패치 없음 | 문서 검증 | STEP 2에 "TEST-SCENARIO 디스패치" 섹션이 없음 |
| TS-009 | R-4 AC ②: PLAN QA Gate 없음 | 문서 검증 | STEP 2 흐름에 QA Gate / QA-PLAN.md 참조 없음 |
| TS-010 | R-4 AC ③: PLAN PM Gate Read 절차 | 문서 검증 | PM Gate에 PLAN.md Read → TEST-SCENARIO.md Read → 체크리스트 절차 명시 |
| TS-011 | R-5 AC: PLAN STATE.md 행 예시 갱신 | 문서 검증 | TEST-SCENARIO 단계 행 없음. PLAN 하위에 TEST-SCENARIO.md 생성 행 존재. QA Gate/QA-PLAN.md 행 없음 |
| TS-016 | R-7 AC ①: TEST QA Gate 없음 | 문서 검증 | STEP 4 PASS 흐름에 QA Gate / QA-EXECUTE.md 참조 없음 |
| TS-017 | R-7 AC ②: TEST PM Gate Read 절차 | 문서 검증 | STEP 4 PM Gate에 TEST-SCENARIO.md Read → 검증 체크리스트 절차 명시 |
| TS-018 | R-7 AC ③: PM Gate 점검 목록 갱신 | 문서 검증 | PM Gate 점검 목록에 QA-EXECUTE.md 없음. TEST-SCENARIO.md 검증 항목 존재 |
| TS-019 | R-7 AC ④: TEST STATE.md 행 예시 갱신 | 문서 검증 | TEST 단계에 QA Gate / QA-EXECUTE.md 생성 행 없음. 전체 행 번호 연속 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | 실행 | 비고 |
|-------|------|------|------|------|
| Phase 1 | F-001 | Step 1 | 순차 | F-002·F-003의 선행 조건 |
| Phase 2 | F-002, F-003 | Step 2, Step 3 | 병렬 가능 | 서로 독립적. 각 파일의 PLAN + EXECUTE/TEST 변경을 한 번에 처리 |

### 4.2 실행 체크리스트

> 총 3개 Step | Phase 2개 | 실행 모드: 단순

#### Step 1: op-dev-plan SKILL.md TEST-SCENARIO 통합

- [ ] 완료
- **소속 기능**: F-001
- **파일**: `opal/skills/op-dev-plan/SKILL.md`
- **작업 내용**:
  1. frontmatter `description`의 보장 출력에 `TEST-SCENARIO.md` 추가
  2. `입력/출력` 테이블 `보장 출력` 행 갱신 (`PLAN.md, TEST-SCENARIO.md`)
  3. Step 10 신설: TEST-SCENARIO.md 작성 (형식·범위·스킵 조건·저장 경로 포함)
  4. 기존 Step 10 → Step 11 이동. Step 11 내용을 "PLAN.md + TEST-SCENARIO.md 경로(또는 스킵) + 요약 반환"으로 갱신. QA 호출 금지 문구 제거.
  5. 변경이력 v2.1 추가
- **완료 기준**:
  - 프로세스 섹션에 "Step 10: TEST-SCENARIO.md 작성"이 존재한다
  - TEST-SCENARIO.md 형식(시나리오 목록/코드 품질/보안/회귀 테스트/판정/설계 피드백 섹션)이 Step 10에 명시된다
  - frontmatter `description`의 보장 출력에 `TEST-SCENARIO.md`가 포함된다
  - Step 11 결과 반환에 TEST-SCENARIO.md 경로가 언급된다
- **테스트**: TS-001, TS-002, TS-003
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: opal-pilot-dev SKILL.md PLAN 단계 슬림화

- [ ] 완료
- **소속 기능**: F-002
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**:
  1. Harness 헤더 모드 설명에서 `TEST-SCENARIO` 독립 단계 제거
  2. STEP 3에서 "3-2. TEST-SCENARIO 디스패치" 섹션 전체 제거
  3. 3-1. PLAN 디스패치 프롬프트에 `{TEST-SCENARIO.md 경로}` 산출물 경로 추가
  4. STEP 3 흐름: `두 워커 완료 → State Gate → QA Gate → QA-PLAN.md → State Gate → PM Gate`를 `PLAN 완료 → State Gate → PM Gate(Read 절차 + 검증 체크리스트) → State Gate`로 교체
  5. STATE.md 도메인 설정 단계 목록에서 `TEST-SCENARIO` 제거, 산출물에서 `QA-PLAN.md` 제거
  6. STATE.md 진행 현황 행 예시 갱신: TEST-SCENARIO 단계 행(12~14) + QA Gate 행(15~17) 제거, PLAN 하위에 TEST-SCENARIO.md 생성 행 추가, 이후 행 번호 재조정
  7. PM Gate 점검 목록 갱신: QA-PLAN.md 제거, Read 절차 + 체크리스트 위치 갱신
  8. 변경이력 v2.9 추가
- **작업 내용 (R-6 추가)**:
  9. STEP 5(TEST) PASS 시: "QA Gate (op-dev-qa) → State Gate" 제거
  10. STEP 5(TEST) PM Gate를 "TEST-SCENARIO.md Read + 검증 체크리스트" 방식으로 교체
  11. PM Gate 점검 목록: EXECUTE 행(`QA-EXECUTE.md`) → TEST 행(`TEST-SCENARIO.md 시나리오 결과/코드품질/보안/회귀`)으로 교체
  12. 산출물 목록 최종 갱신: `QA-*.md` 완전 제거 → `TASK.md, ANALYSIS.md, PLAN.md, TEST-SCENARIO.md, DONE.md`
  13. STATE.md TEST 단계 행: QA Gate + QA-EXECUTE.md 생성 + State Gate(QA 후) 3행 제거, 이후 행 번호 재조정 (전체 1부터 연속)
- **완료 기준**:
  - STEP 3에 "3-2" 섹션 또는 TEST-SCENARIO 별도 디스패치 내용이 없다
  - STEP 3 흐름에 QA Gate / QA-PLAN.md 참조가 없다
  - PM Gate에 "PLAN.md Read → TEST-SCENARIO.md Read → 검증 체크리스트" 절차가 있다
  - STEP 5 PASS 흐름에 QA Gate / QA-EXECUTE.md 참조가 없다
  - STEP 5 PM Gate에 "TEST-SCENARIO.md Read → 검증 체크리스트" 절차가 있다
  - PM Gate 점검 목록에 QA-PLAN.md, QA-EXECUTE.md가 없고 TEST-SCENARIO.md 검증 항목이 있다
  - STATE.md 행 예시에 TEST-SCENARIO 단계 행이 없고, PLAN 단계 하위에 TEST-SCENARIO.md 생성 행이 있다
  - STATE.md 행 예시 TEST 단계에 QA Gate / QA-EXECUTE.md 생성 행이 없다
  - STATE.md 전체 행 번호가 1부터 연속적이다
- **테스트**: TS-004, TS-005, TS-006, TS-007, TS-012, TS-013, TS-014, TS-015
- **실행 방법**: direct
- **의존**: Step 1 (F-001 완료 후)

#### Step 3: opal-pilot-dev-short SKILL.md PLAN 단계 슬림화

- [ ] 완료
- **소속 기능**: F-003
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**:
  1. Harness 헤더 모드 설명에서 `TEST-SCENARIO` 독립 단계 제거
  2. STEP 2에서 "TEST-SCENARIO 디스패치" 섹션 및 관련 서술 제거
  3. STEP 2 PLAN 디스패치 서술에 TEST-SCENARIO.md 산출물 저장 경로 안내 추가
  4. STEP 2 흐름: `워커 완료 → State Gate → QA Gate → QA-PLAN.md → State Gate → PM Gate`를 `PLAN 완료 → State Gate → PM Gate(Read 절차 + 검증 체크리스트) → State Gate`로 교체
  5. STATE.md 도메인 치환값 단계 목록에서 `TEST-SCENARIO` 제거
  6. STATE.md 진행 현황 행 예시 갱신: TEST-SCENARIO 단계 행(6~8) + QA Gate 행(9~11) 제거, PLAN 하위에 TEST-SCENARIO.md 생성 행 추가, 이후 행 번호 재조정
  7. PM Gate 점검 목록 갱신: QA-PLAN.md 제거, Read 절차 + 체크리스트 위치 갱신
  8. 변경이력 v2.9 추가
- **작업 내용 (R-7 추가)**:
  9. STEP 4(TEST) PASS 시: "QA Gate (op-dev-qa) → State Gate" 제거
  10. STEP 4(TEST) PM Gate를 "TEST-SCENARIO.md Read + 검증 체크리스트" 방식으로 교체
  11. PM Gate 점검 목록: EXECUTE 행(`QA-EXECUTE.md`) → TEST 행(`TEST-SCENARIO.md 시나리오 결과/코드품질/보안/회귀`)으로 교체
  12. STATE.md TEST 단계 행: QA Gate + QA-EXECUTE.md 생성 + State Gate(QA 후) 3행 제거, 이후 행 번호 재조정 (전체 1부터 연속)
- **완료 기준**:
  - STEP 2에 TEST-SCENARIO 별도 디스패치 내용이 없다
  - STEP 2 흐름에 QA Gate / QA-PLAN.md 참조가 없다
  - PM Gate에 "PLAN.md Read → TEST-SCENARIO.md Read → 검증 체크리스트" 절차가 있다
  - STEP 4 PASS 흐름에 QA Gate / QA-EXECUTE.md 참조가 없다
  - STEP 4 PM Gate에 "TEST-SCENARIO.md Read → 검증 체크리스트" 절차가 있다
  - PM Gate 점검 목록에 QA-PLAN.md, QA-EXECUTE.md가 없고 TEST-SCENARIO.md 검증 항목이 있다
  - STATE.md 행 예시에 TEST-SCENARIO 단계 행이 없고, PLAN 단계 하위에 TEST-SCENARIO.md 생성 행이 있다
  - STATE.md 행 예시 TEST 단계에 QA Gate / QA-EXECUTE.md 생성 행이 없다
  - STATE.md 전체 행 번호가 1부터 연속적이다
- **테스트**: TS-008, TS-009, TS-010, TS-011, TS-016, TS-017, TS-018, TS-019
- **실행 방법**: direct
- **의존**: Step 1 (F-001 완료 후); Step 2와 병렬 가능

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2·3 순차 | op-dev-plan 스킬이 TEST-SCENARIO를 통합 작성하는 것이 확정되어야, 오케스트레이터 SKILL.md에서 "별도 디스패치 제거"와 "PLAN 워커 산출물에 TEST-SCENARIO.md 포함" 서술이 정확해짐 |
| Step 2 ‖ Step 3 병렬 | 변경 대상 파일이 서로 다르고(`opal-pilot-dev` vs `opal-pilot-dev-short`), 두 파일 간 의존성 없음 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | Step 10 존재 확인 | TS-001 | "Step 10: TEST-SCENARIO.md 작성" 헤더와 본문 존재 |
| F-001 | 보장 출력 갱신 확인 | TS-002 | frontmatter description에 TEST-SCENARIO.md 포함 |
| F-001 | 결과 반환 Step 갱신 확인 | TS-003 | Step 11에 TEST-SCENARIO.md 경로 언급 |
| F-001 | TEST-SCENARIO 형식 명시 확인 | TS-001 | 시나리오 목록/코드 품질/보안/회귀 테스트/판정/설계 피드백 섹션 언급 |
| F-001 | 스킵 조건 명시 확인 | TS-001 | 문서 전용 스킵 조건이 Step 10에 명시됨 |
| F-002 | TEST-SCENARIO 별도 디스패치 제거 | TS-004 | "3-2" 섹션 없음 |
| F-002 | PLAN QA Gate 제거 | TS-005 | STEP 3 흐름에 QA Gate / QA-PLAN.md 없음 |
| F-002 | PLAN PM Gate Read 절차 추가 | TS-006 | Read 절차 + 5개 체크리스트 항목 존재 |
| F-002 | PLAN STATE.md 행 예시 갱신 | TS-007 | TEST-SCENARIO 단계 행 없음, PLAN 하위 TEST-SCENARIO.md 생성 행 존재, QA-PLAN.md 행 없음 |
| F-002 | TEST QA Gate 제거 | TS-012 | STEP 5 PASS 흐름에 QA Gate / QA-EXECUTE.md 없음 |
| F-002 | TEST PM Gate Read 절차 추가 | TS-013 | STEP 5 PM Gate에 TEST-SCENARIO.md Read + 체크리스트 존재 |
| F-002 | PM Gate 점검 목록 갱신 | TS-014 | QA-EXECUTE.md 없음, TEST-SCENARIO.md 검증 항목 존재 |
| F-002 | TEST STATE.md 행 예시 갱신 | TS-015 | TEST 단계 QA Gate / QA-EXECUTE.md 행 없음, 전체 번호 연속 |
| F-003 | TEST-SCENARIO 별도 디스패치 제거 | TS-008 | "TEST-SCENARIO 디스패치" 섹션 없음 |
| F-003 | PLAN QA Gate 제거 | TS-009 | STEP 2 흐름에 QA Gate / QA-PLAN.md 없음 |
| F-003 | PLAN PM Gate Read 절차 추가 | TS-010 | Read 절차 + 5~6개 체크리스트 항목 존재 |
| F-003 | PLAN STATE.md 행 예시 갱신 | TS-011 | TEST-SCENARIO 단계 행 없음, PLAN 하위 TEST-SCENARIO.md 생성 행 존재, QA-PLAN.md 행 없음 |
| F-003 | TEST QA Gate 제거 | TS-016 | STEP 4 PASS 흐름에 QA Gate / QA-EXECUTE.md 없음 |
| F-003 | TEST PM Gate Read 절차 추가 | TS-017 | STEP 4 PM Gate에 TEST-SCENARIO.md Read + 체크리스트 존재 |
| F-003 | PM Gate 점검 목록 갱신 | TS-018 | QA-EXECUTE.md 없음, TEST-SCENARIO.md 검증 항목 존재 |
| F-003 | TEST STATE.md 행 예시 갱신 | TS-019 | TEST 단계 QA Gate / QA-EXECUTE.md 행 없음, 전체 번호 연속 |

### 5.2 회귀 테스트

- [ ] `opal-pilot-dev/SKILL.md` EXECUTE 단계 내용(STEP 4)이 의도치 않게 변경되지 않았는가
- [ ] `opal-pilot-dev/SKILL.md` STEP 5 FAIL 루핑 로직이 유지되었는가
- [ ] `opal-pilot-dev-short/SKILL.md` EXECUTE 단계 내용(STEP 3)이 의도치 않게 변경되지 않았는가
- [ ] `opal-pilot-dev-short/SKILL.md` STEP 4 FAIL 루핑 로직이 유지되었는가
- [ ] `opal-pilot-dev/SKILL.md` Agentic Mode 섹션이 영향받지 않았는가 (자율 게이트 흐름도 동일하게 갱신 필요 여부 검토)
- [ ] `opal-pilot-dev-short/SKILL.md` 에스컬레이션 규칙이 유지되었는가
- [ ] 변경이력 버전이 올바르게 부여되었는가 (기존 최신 버전 기준 +0.1)

### 5.3 코드/문서 품질

- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] 변경된 파일 모두에 변경이력(버전) 행이 추가되었는가
- [ ] 마크다운 테이블 형식이 올바른가 (| 구분, 헤더 행)
- [ ] kebab-case 파일/폴더 네이밍이 유지되었는가
- [x] PLAN.md §4.2 체크리스트 참조 위치가 현행 op-dev-plan v2.0 구조(§4.2)와 일치하는가

### 5.4 보안

- [x] 스킬 문서에 시크릿/인증 정보가 포함되지 않았는가
- [x] `~/.opal/` 경로를 직접 수정하지 않았는가 (소스 경로 `opal/skills/`만 수정)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 3개 | 단순 |
| 변경 파일 수 | 3개 (각 파일당 변경 영역 증가) | 단순 |
| 모듈 범위 | 단일 (스킬 문서 수정) | 단순 |
| 작업 유형 | 문서 수정 (Markdown) | 단순 |
| 외부 의존성 | 없음 | 단순 |
| **실행 모드** | **단순** | |

---

## 7. 실행 아키텍처

단순 모드 — 생략.

---

## 8. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 스킬 | Markdown 문서 | — |
| 가이드 | op-dev-test-scenario SKILL.md (TEST-SCENARIO 형식 참조) | 읽기 전용 |

### 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 라이브러리 API 조회 불필요 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | Agentic Mode 자율 게이트 흐름도(`PLAN+TEST-SCENARIO Gate`)가 갱신 누락될 수 있음 | F-002, F-003 | agentic 모드 사용 시 흐름도와 실제 프로세스 불일치 | Step 2·3에서 Agentic Mode 섹션의 자율 게이트 흐름도도 함께 갱신 (`PLAN+TEST-SCENARIO Gate` → `PLAN Gate`) |
| 2 | STATE.md 행 번호 재조정 시 누락/중복 발생 가능 | F-002, F-003 | STATE.md 초기 생성 시 번호 오류 | 완료 기준에 "전체 행 번호가 1부터 연속적이어야 함" 조건 포함 |
| 3 | PLAN 디스패치 프롬프트에 TEST-SCENARIO.md 저장 경로가 누락될 경우 워커가 TEST-SCENARIO.md를 어디에 저장해야 할지 알 수 없음 | F-001 | TEST-SCENARIO.md 미생성 또는 잘못된 경로에 저장 | Step 1 완료 기준에 "Step 10에 저장 경로 명시" 포함, Step 2·3 완료 기준에 "3-1 디스패치 프롬프트에 TEST-SCENARIO.md 경로 포함" 추가 |
