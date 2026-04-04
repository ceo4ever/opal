# PLAN: 하네스/스킬 문서 4건 정비 — STATE.md 누락 방지 + 병렬 판별 추가

> 작성일: 2026-04-04
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/opal-harness.md` | 오케스트레이터 공통 인프라 — §4 TASK 공통 프로세스 | O (R1, R2) |
| `opal/skills/op-task/SKILL.md` | TASK 단계 스킬 — 사용자 요청 구조화 | O (R3) |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | Short Task 오케스트레이터 | O (R4) |
| `opal/skills/op-dev-plan/SKILL.md` | PLAN 단계 스킬 — 구현 계획 수립 | O (R6) |
| `opal/skills/op-dev-plan/references/plan-guide.md` | PLAN 상세 가이드 | O (R5) |
| `docs/CONVENTIONS.md` | 코드/문서 컨벤션 | X (참조만) |

### 현재 상태

**이슈 1 — STATE.md 생성 시점 분산 (R1, R2, R3)**

- `opal-harness.md` §4 (line 214~233): TASK 공통 프로세스 6단계 중 5번째가 "STATE.md를 생성한다"이나, 이것이 하네스 공통 영역인지 스킬 영역인지 마커가 없다.
- `opal-harness.md` §3 (line 105~118): STATE.md 기본 구조에서 "오케스트레이터 전용. 단계 스킬은 STATE.md를 갱신하지 않는다"고 명시. 즉 STATE.md 생성은 오케스트레이터 책임이다.
- `op-task/SKILL.md` (line 133~140): 완료 보고 형식에 STATE.md에 대한 언급이 전혀 없다. 오케스트레이터가 이 스킬을 따라가다 보면 STATE.md 생성을 놓칠 수 있다.

**이슈 2 — 하네스 §4와 스킬 프로세스 관계 암묵적 (R1)**

- `opal-harness.md` §4는 6개 절차를 나열하지만, 어디까지가 "op-task 스킬 프로세스"이고 어디부터가 "오케스트레이터 공통"인지 구분이 없다.
- 실제 흐름: 1~2번(스킬 로드+실행) → 3~6번(오케스트레이터 후처리). 이 구분이 암묵적이라 오케스트레이터가 후처리를 누락하기 쉽다.

**이슈 3 — 에스컬레이션 판단 시점 (R4)**

- `opal-pilot-dev-short/SKILL.md` 에스컬레이션 규칙 (line 73~89): "op-dev-plan 결과에서" 조건을 감지하여 Full Task 전환을 제안하도록 되어 있다. 즉 PLAN 완료 후에만 에스컬레이션이 가능하다.
- TASK 단계에서 이미 요구사항 수/범위가 명백히 Short 범위를 초과하는 경우(예: 요구사항 10개 이상, 다중 모듈 명시)에도 PLAN까지 진행해야만 에스컬레이션이 발생한다. 이는 불필요한 PLAN 디스패치 비용을 초래한다.

**이슈 4 — PLAN 병렬/순차 Phase 판별 누락 (R5, R6)**

- `op-dev-plan/references/plan-guide.md`의 "실행 체크리스트 작성" (line 179~225): Step 간 의존성 명시는 있으나, 독립 Step들을 Phase/Group으로 묶어 병렬 실행 가능 여부를 표시하는 지침이 없다.
- `opal-harness.md` §7 (line 274~354): "병렬 가능한 작업은 무조건 병렬로" 원칙이 있지만, PLAN 단계에서 이를 반영하는 Phase 그룹핑 지침이 없어 단순 모드에서 모든 Step이 순차 나열된다.
- `op-dev-plan/SKILL.md` 품질 체크리스트 (line 307~325): Phase 그룹핑 확인 항목이 없다.

### 영향 범위

- 하네스 변경(R1, R2)은 모든 `opal-pilot-*` 오케스트레이터에 영향. 기존 참조 관계(`harness "4. TASK 공통 프로세스" 참조`)를 깨지 않아야 한다.
- op-task 변경(R3)은 모든 오케스트레이터의 TASK 단계에 영향 (op-task는 공용 스킬).
- opds 변경(R4)은 Short Task 오케스트레이터에만 영향.
- plan-guide.md 변경(R5)은 op-dev-plan을 사용하는 모든 오케스트레이터(opd, opds)에 영향.
- op-dev-plan 변경(R6)은 PLAN 워커에 영향.

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

없음

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/references/opal-harness.md` | §4에 스킬/공통 영역 구분 마커 추가 + STATE.md 생성 단계 강조 (R1, R2) |
| 2 | `opal/skills/op-task/SKILL.md` | 완료 보고 형식 위에 STATE.md 생성 리마인더 추가 (R3) |
| 3 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 에스컬레이션 규칙에 조기 에스컬레이션 조항 추가 (R4) |
| 4 | `opal/skills/op-dev-plan/references/plan-guide.md` | 실행 체크리스트 섹션에 Phase 그룹핑 지침 추가 (R5) |
| 5 | `opal/skills/op-dev-plan/SKILL.md` | 품질 체크리스트에 Phase 그룹핑 확인 항목 추가 (R6) |
| 6 | `opal/skills/op-task-plan/references/plan-guide.md` | 실행 체크리스트 섹션에 Phase 그룹핑 지침 추가 (R7) |
| 7 | `opal/skills/op-task-plan/SKILL.md` | 품질 체크리스트에 Phase 그룹핑 확인 항목 추가 (R8) |

#### 삭제

없음

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 하네스 §4 영역 마커 + STATE.md 강조 | opal-harness.md | 쉬움 |
| 2 | op-task STATE.md 리마인더 추가 | op-task/SKILL.md | 쉬움 |
| 3 | opds 조기 에스컬레이션 조항 추가 | opal-pilot-dev-short/SKILL.md | 쉬움 |
| 4 | plan-guide Phase 그룹핑 지침 추가 | plan-guide.md | 보통 |
| 5 | op-dev-plan 품질 체크리스트 항목 추가 | op-dev-plan/SKILL.md | 쉬움 |
| 6 | op-task-plan plan-guide Phase 그룹핑 지침 추가 | op-task-plan/references/plan-guide.md | 보통 |
| 7 | op-task-plan 품질 체크리스트 항목 추가 | op-task-plan/SKILL.md | 쉬움 |

### 핵심 설계

#### 수정 1: opal-harness.md §4 — 영역 마커 + STATE.md 강조 (R1, R2)

현재 §4 (line 214~233)의 6단계를 **스킬 영역**과 **오케스트레이터 공통 영역**으로 구분하는 마커를 추가한다. STATE.md 생성 단계에 강조 표시를 추가한다.

**변경 전** (line 216~226):
```markdown
1. `op-task/SKILL.md`를 Read한다.
   - 탐색: `{프로젝트}/.opal/skills/op-task/SKILL.md` -> `~/.opal/skills/op-task/SKILL.md`
2. 스킬 프로세스를 따라 TASK.md를 작성한다.
3. **STEP 5(오케스트레이터 선택)에서 결정된 스킬약어**를 폴더명과 TASK.md 헤더 `적용 스킬` 필드에 반영한다.
4. **`--agentic` 플래그 여부를 TASK.md 헤더 `모드` 필드에 반드시 기록한다** (`interactive` 또는 `agentic`).
5. STATE.md를 생성한다.
6. 사용자에게 보고하고 다음 단계 승인을 받는다.
```

**변경 후**:
```markdown
#### 스킬 영역 (op-task 프로세스)

1. `op-task/SKILL.md`를 Read한다.
   - 탐색: `{프로젝트}/.opal/skills/op-task/SKILL.md` -> `~/.opal/skills/op-task/SKILL.md`
2. 스킬 프로세스를 따라 TASK.md를 작성한다.

#### 오케스트레이터 공통 영역 (스킬 완료 후 후처리)

3. **STEP 5(오케스트레이터 선택)에서 결정된 스킬약어**를 폴더명과 TASK.md 헤더 `적용 스킬` 필드에 반영한다.
4. **`--agentic` 플래그 여부를 TASK.md 헤더 `모드` 필드에 반드시 기록한다** (`interactive` 또는 `agentic`).
5. **[필수] STATE.md를 생성한다** (§3 템플릿 참조). 이 단계를 건너뛰면 세션 복원과 상태 추적이 불가능하다.
6. 사용자에게 보고하고 다음 단계 승인을 받는다.
```

설계 의도: "스킬 영역 / 오케스트레이터 공통 영역" 소제목으로 영역을 명시적으로 분리. STATE.md 단계에 `[필수]` 마커와 누락 시 영향을 기재하여 강조.

#### 수정 2: op-task/SKILL.md — STATE.md 생성 리마인더 (R3)

현재 완료 보고 형식 (line 133~140) 직전에 리마인더 블록을 추가한다.

**삽입 위치**: `#### 완료 보고 형식` 직전 (line 133 앞)

**추가할 텍스트**:
```markdown
#### STATE.md 리마인더

> **[오케스트레이터 후처리]** op-task 프로세스 완료 후, 오케스트레이터는 하네스 §4 "오케스트레이터 공통 영역"을 수행해야 한다. 특히 **STATE.md 생성**을 잊지 않는다.
```

설계 의도: op-task 스킬 문서 내에서 오케스트레이터의 후처리 의무를 리마인드. 스킬 자체가 STATE.md를 생성하는 것이 아니라, 오케스트레이터가 해야 한다는 점을 명확히 한다.

#### 수정 3: opal-pilot-dev-short/SKILL.md — 조기 에스컬레이션 조항 (R4)

현재 에스컬레이션 규칙 (line 73~89)은 "op-dev-plan 결과에서" 감지하는 사후 에스컬레이션만 있다. TASK 단계 직후 조기 판단 조항을 추가한다.

**삽입 위치**: `## 에스컬레이션 규칙` 본문(line 75) 바로 아래, 기존 테이블 앞

**추가할 텍스트**:
```markdown
### 조기 에스컬레이션 (TASK 완료 직후)

TASK.md 작성 완료 시점에서 아래 조건이 **명백히** 해당하면, PLAN 디스패치 전에 에스컬레이션을 제안한다:

| 조건 | 판별 방법 |
|------|----------|
| 요구사항 항목 >= 8개 | TASK.md 요구사항 체크박스 카운트 |
| 다중 모듈/서비스 명시 | TASK.md 배경/요구사항에 3개 이상 독립 모듈이 명시적으로 언급됨 |

> **주의**: 조기 에스컬레이션은 TASK.md만으로 **명백히** 판단 가능한 경우에만 적용한다. 불확실하면 PLAN을 진행하여 정확한 판별을 받는다.

### PLAN 결과 에스컬레이션 (기존)
```

그리고 기존 "op-dev-plan 결과에서 아래 조건이 감지되면" 문구를 "### PLAN 결과 에스컬레이션 (기존)" 소제목 아래로 이동한다.

설계 의도: 조기 에스컬레이션 조건을 보수적으로 설정(명백한 경우만)하여 오판을 최소화하면서, 명백한 오버스코프는 PLAN 디스패치 비용 없이 처리 가능하게 한다.

#### 수정 4: plan-guide.md — Phase 그룹핑 지침 (R5)

현재 "실행 체크리스트 작성" 섹션 (line 83~104) 뒤에 Phase 그룹핑 지침을 추가한다.

**삽입 위치**: Step 형식 코드 블록(line 104) 뒤, `---` 구분선 앞

**추가할 텍스트**:
```markdown
### Phase 그룹핑 (병렬 판별)

하네스 §7 병렬 처리 원칙에 따라, 실행 체크리스트의 Step을 Phase로 그룹핑한다.

**그룹핑 규칙**:
1. `의존: "없음"` 이고 서로 다른 파일을 대상으로 하는 Step들 → **같은 Phase** (병렬 실행 가능)
2. 선행 의존이 있는 Step → 선행 Step의 Phase 이후 Phase에 배치
3. 동일 파일을 수정하는 Step → **반드시 순차** (같은 Phase에 넣지 않음)

**표기 방법**: 실행 체크리스트 상단에 Phase 요약을 추가한다:

```markdown
> 총 {N}개 Step | Phase {M}개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1, 2 | 병렬 | 독립 파일 |
> | 2     | 3    | 순차 | Step 1 의존 |
> | 3     | 4, 5 | 병렬 | 독립 파일 |
```

**단순 모드에서의 적용**: 단순 모드(모든 Step이 direct)에서도 Phase 그룹핑을 수행한다. 오케스트레이터가 병렬 툴콜 또는 순차 실행을 결정하는 기준으로 사용된다.

**Phase가 1개인 경우**: 모든 Step이 순차 의존이면 Phase 요약 테이블의 실행 컬럼을 모두 "순차"로 표기한다.
```

설계 의도: 기존 Step 형식은 유지하면서 Phase 요약 테이블을 추가. 오케스트레이터가 어떤 Step을 병렬로 디스패치할 수 있는지 한눈에 파악 가능. 단순 모드에서도 적용하여 일관성 확보.

#### 수정 5: op-dev-plan/SKILL.md — 품질 체크리스트 항목 추가 (R6)

현재 품질 체크리스트 (line 307~325) 마지막에 Phase 그룹핑 확인 항목을 추가한다.

**삽입 위치**: line 325 (`- [ ] 복잡 모드일 경우 실행 아키텍처(C-1~C-4)가 포함되어 있는가?`) 뒤

**추가할 텍스트**:
```markdown
- [ ] 실행 체크리스트에 Phase 그룹핑(병렬/순차 판별)이 수행되었는가?
```

설계 의도: 워커가 PLAN 작성 시 Phase 그룹핑을 빠뜨리지 않도록 체크 항목으로 강제.

#### 수정 6: op-task-plan/references/plan-guide.md — Phase 그룹핑 지침 (R7)

op-dev-plan의 plan-guide.md(수정 4)와 동일한 Phase 그룹핑 지침을 op-task-plan의 plan-guide.md에도 추가한다.

**삽입 위치**: "실행 체크리스트 작성" 섹션의 Step 형식 코드 블록(line 104) 뒤, `---` 구분선 앞

**추가할 텍스트**: 수정 4와 동일 내용. 단, "단순 모드에서의 적용" 문구 대신 "op-task-plan은 항상 direct 실행이지만, 오케스트레이터가 Phase 정보를 기반으로 병렬 툴콜을 판단한다"로 대체.

설계 의도: dev 계열과 범용 계열의 PLAN 품질을 통일. opp에서도 독립 Step을 병렬로 실행할 수 있도록 Phase 정보를 제공.

#### 수정 7: op-task-plan/SKILL.md — 품질 체크리스트 항목 추가 (R8)

수정 5와 동일. op-task-plan SKILL.md 품질 체크리스트 마지막 항목 뒤에 Phase 그룹핑 확인 항목을 추가한다.

**삽입 위치**: `- [ ] 각 Step의 완료 기준이 명확하고 검증 가능한가?` (line 131) 뒤

**추가할 텍스트**:
```markdown
- [ ] 실행 체크리스트에 Phase 그룹핑(병렬/순차 판별)이 수행되었는가?
```

## 3. 실행 체크리스트

> 총 7개 Step | Phase 4개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1, 2 | 병렬 | 하네스와 op-task는 독립 파일 |
> | 2     | 3    | 순차 | 독립 파일이지만 R4 단독 |
> | 3     | 4, 5, 6, 7 | 병렬 | dev plan-guide, dev SKILL, task plan-guide, task SKILL 모두 독립 파일 |

### Step 1: 하네스 §4 영역 마커 + STATE.md 강조
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: §4 TASK 공통 프로세스의 6단계를 "스킬 영역" / "오케스트레이터 공통 영역" 소제목으로 분리. 5번 STATE.md 단계에 `[필수]` 마커와 누락 시 영향 문구 추가. 변경이력에 v2.5 행 추가.
- **완료 기준**: §4에 `#### 스킬 영역`, `#### 오케스트레이터 공통 영역` 소제목이 존재하고, STATE.md 단계에 `[필수]` 마커가 있다.
- **테스트**: 파일을 Read하여 마커와 소제목 존재 확인
- **의존**: 없음

### Step 2: op-task STATE.md 리마인더 추가
- [x] 완료
- **파일**: `opal/skills/op-task/SKILL.md`
- **작업 내용**: `#### 완료 보고 형식` (line 133) 직전에 `#### STATE.md 리마인더` 소섹션 추가. 오케스트레이터 후처리 의무와 STATE.md 생성을 리마인드하는 blockquote 삽입.
- **완료 기준**: 완료 보고 형식 위에 STATE.md 리마인더 블록이 존재한다.
- **테스트**: 파일을 Read하여 리마인더 블록 존재 확인
- **의존**: 없음

### Step 3: opds 조기 에스컬레이션 조항 추가
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**: 에스컬레이션 규칙 섹션을 "조기 에스컬레이션 (TASK 완료 직후)" + "PLAN 결과 에스컬레이션 (기존)" 두 소섹션으로 재구성. 조기 에스컬레이션 조건 테이블(요구사항 >= 8개, 다중 모듈 명시)과 주의 blockquote 추가. 변경이력에 v2.0 행 추가.
- **완료 기준**: `### 조기 에스컬레이션` 소제목과 조건 테이블이 존재하고, 기존 PLAN 결과 에스컬레이션 내용이 보존되어 있다.
- **테스트**: 파일을 Read하여 두 소섹션과 조건 테이블 존재 확인
- **의존**: 없음

### Step 4: plan-guide Phase 그룹핑 지침 추가
- [x] 완료
- **파일**: `opal/skills/op-dev-plan/references/plan-guide.md`
- **작업 내용**: "실행 체크리스트 작성" 섹션의 Step 형식 코드 블록 뒤에 `### Phase 그룹핑 (병렬 판별)` 소섹션 추가. 그룹핑 규칙(3개), Phase 요약 테이블 표기 방법, 단순 모드 적용 원칙, Phase 1개인 경우 처리 방법 포함.
- **완료 기준**: `### Phase 그룹핑 (병렬 판별)` 소제목과 그룹핑 규칙 3개, Phase 요약 테이블 예시가 존재한다.
- **테스트**: 파일을 Read하여 소섹션과 규칙/예시 존재 확인
- **의존**: 없음

### Step 5: op-dev-plan 품질 체크리스트 항목 추가
- [x] 완료
- **파일**: `opal/skills/op-dev-plan/SKILL.md`
- **작업 내용**: 품질 체크리스트 마지막 항목 뒤에 `- [ ] 실행 체크리스트에 Phase 그룹핑(병렬/순차 판별)이 수행되었는가?` 항목 추가.
- **완료 기준**: 품질 체크리스트에 Phase 그룹핑 확인 항목이 존재한다.
- **테스트**: 파일을 Read하여 항목 존재 확인
- **의존**: 없음

### Step 6: op-task-plan plan-guide Phase 그룹핑 지침 추가
- [x] 완료
- **파일**: `opal/skills/op-task-plan/references/plan-guide.md`
- **작업 내용**: "실행 체크리스트 작성" 섹션의 Step 형식 코드 블록 뒤에 `### Phase 그룹핑 (병렬 판별)` 소섹션 추가. Step 4(op-dev-plan용)와 동일한 그룹핑 규칙 3개, Phase 요약 테이블 표기 방법, Phase 1개인 경우 처리 방법을 포함한다. 단, 복잡도 판별/실행 아키텍처 관련 문구는 op-task-plan에 해당하지 않으므로 제외.
- **완료 기준**: `### Phase 그룹핑 (병렬 판별)` 소제목과 그룹핑 규칙 3개, Phase 요약 테이블 예시가 존재한다.
- **테스트**: 파일을 Read하여 소섹션과 규칙/예시 존재 확인
- **의존**: 없음

### Step 7: op-task-plan 품질 체크리스트 항목 추가
- [x] 완료
- **파일**: `opal/skills/op-task-plan/SKILL.md`
- **작업 내용**: 품질 체크리스트 마지막 항목 뒤에 `- [ ] 실행 체크리스트에 Phase 그룹핑(병렬/순차 판별)이 수행되었는가?` 항목 추가.
- **완료 기준**: 품질 체크리스트에 Phase 그룹핑 확인 항목이 존재한다.
- **테스트**: 파일을 Read하여 항목 존재 확인
- **의존**: 없음

## 4. QA 체크리스트

### 기능 테스트
- [x] R1: 하네스 §4에 스킬/공통 영역 구분 마커가 존재하는가
- [x] R2: 하네스 §4 STATE.md 단계에 `[필수]` 강조가 있는가
- [x] R3: op-task 완료 보고 형식 위에 STATE.md 리마인더가 있는가
- [x] R4: opds 에스컬레이션 규칙에 조기 에스컬레이션 조항이 있는가
- [x] R5: plan-guide에 Phase 그룹핑 지침이 있는가
- [x] R6: op-dev-plan 품질 체크리스트에 Phase 그룹핑 확인 항목이 있는가
- [x] R7: op-task-plan plan-guide에 Phase 그룹핑 지침이 있는가
- [x] R8: op-task-plan 품질 체크리스트에 Phase 그룹핑 확인 항목이 있는가

### 일관성 테스트
- [x] 하네스 §4 변경 후 기존 참조(`harness "4. TASK 공통 프로세스" 참조`)가 여전히 유효한가
- [x] op-task SKILL.md의 기존 프로세스 흐름(STEP 1~5)이 변경되지 않았는가
- [x] opds 기존 PLAN 결과 에스컬레이션 조건/형식이 보존되었는가
- [x] plan-guide의 기존 Step 형식이 변경되지 않았는가
- [x] 변경이력이 추가된 파일에 올바른 버전/일시가 기재되었는가

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] kebab-case 파일/폴더 네이밍을 따르는가
- [x] 추가된 텍스트가 기존 문서 톤/스타일과 일관적인가

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 하네스 §4 소제목 추가로 기존 "§4 참조" 동작 변화 | 오케스트레이터가 §4를 찾지 못할 가능성 | `## 4. TASK 공통 프로세스` 제목은 변경하지 않음. 하위 소제목(####)만 추가하므로 기존 참조 무영향 |
| 조기 에스컬레이션 오판으로 불필요한 Full Task 전환 | 작업 효율 저하 | 조건을 보수적으로 설정 (요구사항 8개 이상, 3개 이상 독립 모듈 "명시적" 언급) + "불확실하면 PLAN 진행" 안전장치 |
| Phase 그룹핑 추가로 PLAN 작성 부담 증가 | 워커 생산성 저하 | Phase 요약 테이블은 간소한 형식. Step 의존 필드에서 자동 도출 가능한 정보이므로 추가 분석 부담 최소 |
