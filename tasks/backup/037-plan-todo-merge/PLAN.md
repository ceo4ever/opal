# PLAN: otp-dev PLAN과 TODO 단계 통합

> 작성일: 2026-03-28
> 입력: TASK.md
> 출력: PLAN.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/otp-dev/SKILL.md` | Full Task 오케스트레이터 — 5단계 파이프라인 정의 | **수정** |
| `skills/dtp-plan/SKILL.md` | 구현 계획 스킬 — PLAN.md 생성 절차 | **수정** |
| `skills/dtp-plan/references/plan-guide.md` | PLAN 상세 가이드 — 구현 계획 작성 규칙 | **수정** |
| `skills/dtp-todo/SKILL.md` | TODO 스킬 — 실행 체크리스트 확장 (통합 대상, 레거시 보존) | 변경 없음 |
| `skills/dtp-todo/references/todo-guide.md` | TODO 상세 가이드 — Part A/B/C 규칙 | 변경 없음 (흡수 원본) |
| `skills/dtp-todo/references/execute-plan-guide.md` | 실행 아키텍처 설계 가이드 — Part C 상세 | 변경 없음 (흡수 원본) |
| `skills/dtp-execute/SKILL.md` | 코드 실행 스킬 — checklist_source 참조 | **수정** |
| `skills/dtp-execute/references/execute-guide.md` | EXECUTE 상세 가이드 — 체크리스트 소스 분기 | **수정** |

### 현재 구현

#### otp-dev/SKILL.md (Full Task 오케스트레이터)

파이프라인 5단계:
```
STEP 1: TASK → STEP 2: ANALYSIS → [QA] → 검토
  → STEP 3: PLAN → [QA] → 검토
  → STEP 4: TODO(4-1) + TEST-SCENARIO(4-2) → 검토/승인
  → STEP 5: EXECUTE → [Test] → 완료
```

- STEP 4에서 dtp-todo 워커(haiku)를 먼저 디스패치하고, 완료 후 dtp-test-scenario 워커(haiku)를 연속 디스패치
- STEP 5의 `checklist_source`가 `TODO.md 경로, 섹션: Part A`로 지정됨
- STATE.md 템플릿의 단계 목록: `TASK / ANALYSIS / PLAN / TODO+TEST-SCENARIO / EXECUTE`
- STATE.md 산출물 테이블에 `TODO.md` 행이 존재

#### dtp-plan/SKILL.md (구현 계획 스킬)

- 현재 "3. 실행 체크리스트" 형식: `- [ ] Step N: {제목} -- {파일} -- {작업 내용}` (간략한 인라인 형식)
- "4. QA 체크리스트": 기능 테스트 / 회귀 테스트 / 코드 품질 (3개 카테고리, **보안 없음**)
- 복잡도 판별 로직 없음
- 실행 아키텍처(Part C) 섹션 없음

#### dtp-todo/SKILL.md (통합 대상)

- Part A: Step별 상세 필드 — 파일, 작업 내용, 완료 기준, 테스트, 실행 방법(direct/sub-agent), 의존
- Part B: QA 4개 카테고리 — B-1 기능 / B-2 회귀 / B-3 코드 품질 / **B-4 보안**
- 복잡도 판별: Step수/파일수/모듈범위/작업유형/외부의존성 기준으로 단순/복잡 결정
- Part C (복잡 모드 전용): 에이전트 토폴로지, 스킬 요구사항, 도구 요구사항, 테스트 전략
- execute-plan-guide.md: DAG 구성, 그룹핑 알고리즘, 배치 결정, 스킬 매칭, 도구 탐색, 테스트 전략 구체화

#### dtp-execute/SKILL.md (체크리스트 소스 참조)

- checklist_source 분기:
  - Full Task: `TODO.md Part A` 또는 `execution-plan.json`
  - Short Task: `PLAN.md 섹션 3`
- QA 체크리스트 분기:
  - Full Task: `TODO.md Part B`
  - Short Task: `PLAN.md 섹션 4`
- 체크박스 갱신 분기도 동일하게 Full/Short로 나뉨

### 영향 범위

- **dtp-execute**: checklist_source가 `TODO.md` → `PLAN.md`로 변경됨. Full/Short 분기가 통합되어 단순해짐
- **dtp-qa**: QA가 PLAN 단계에서 호출되므로, QA 대상 산출물에 확장된 실행 체크리스트와 보안 항목이 포함됨
- **dtp-test-scenario**: 현재 STEP 4(4-2)에서 TODO 후 실행 → STEP 3 완료 후(PLAN과 같은 STEP)로 이동
- **STATE.md 템플릿**: 단계 목록, 산출물 테이블에서 TODO 관련 항목 변경

## 2. 구현 계획

### 파일 변경 계획

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/dtp-plan/SKILL.md` | 실행 체크리스트 형식 확장, QA에 보안 추가, 복잡도 판별 섹션, 실행 아키텍처 섹션(조건부), PLAN.md 출력 형식 업데이트 |
| 2 | `skills/dtp-plan/references/plan-guide.md` | 실행 체크리스트 상세 가이드 흡수, QA B-4 보안, 복잡도 판별 기준, Part C 실행 아키텍처 절차, 품질 체크리스트 확장 |
| 3 | `skills/otp-dev/SKILL.md` | 5 STEP → 4 STEP, TODO 디스패치 제거, TEST-SCENARIO를 PLAN 이후 STEP으로 이동, STATE.md 템플릿 갱신, EXECUTE checklist_source 변경, TEST-SCENARIO 스킵 조건 추가 |
| 3b | `skills/otp-dev-short/SKILL.md` | TEST-SCENARIO 스킵 조건 추가 (문서 전용 작업 시) |
| 4 | `skills/dtp-execute/SKILL.md` | Full Task checklist_source를 `PLAN.md 섹션 3`으로 통일, QA를 `PLAN.md 섹션 4`로 통일 |
| 5 | `skills/dtp-execute/references/execute-guide.md` | Full/Short 분기를 `PLAN.md` 단일 소스로 통합, TODO.md 참조 제거 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | dtp-plan/references/plan-guide.md에 TODO 고유 가치 흡수 | plan-guide.md | 높음 |
| 2 | dtp-plan/SKILL.md 프로세스 및 출력 형식 확장 | dtp-plan/SKILL.md | 보통 |
| 3 | otp-dev/SKILL.md 파이프라인 재설계 (5→4 STEP) | otp-dev/SKILL.md | 보통 |
| 4 | dtp-execute/SKILL.md checklist_source 통일 | dtp-execute/SKILL.md | 쉬움 |
| 5 | dtp-execute/references/execute-guide.md 참조 통일 | execute-guide.md | 쉬움 |

### 핵심 설계

#### 1. plan-guide.md 확장 내용

**실행 체크리스트 상세 가이드 흡수** (todo-guide.md Part A에서):
- 기존 인라인 형식 `- [ ] Step N: {제목} -- {파일} -- {작업}` 을 블록 형식으로 확장
- 각 Step에 다음 필드 추가: 완료 기준, 테스트, 실행 방법(direct/sub-agent), 의존
- 분해 규칙 흡수: 1파일=1작업, 독립 테스트 가능, 의존성 순서

**QA 체크리스트 확장** (todo-guide.md Part B에서):
- B-4 보안 카테고리 추가: .env/.gitignore 확인, 하드코딩 토큰/시크릿 스캔

**복잡도 판별 섹션 추가** (todo-guide.md에서):
- Step수/파일수/모듈범위/작업유형/외부의존성 5개 기준 테이블
- 하나라도 복잡 기준에 해당하면 복잡 모드
- 단순 모드: 모든 Step `direct`, Part C 생략
- 복잡 모드: Part C(실행 아키텍처) 포함

**실행 아키텍처 섹션 추가** (execute-plan-guide.md에서):
- Part C는 복잡 모드일 때만 PLAN.md에 조건부 포함
- C-1 에이전트 토폴로지 (DAG, 그룹핑, 배치)
- C-2 스킬 요구사항 (기존 매칭 + 갭 판별)
- C-3 도구 요구사항 (CLI, MCP, 패키지)
- C-4 테스트 전략 (dtp-test 실행 계획)
- execute-plan-guide.md를 `dtp-plan/references/`로 복사하거나, 기존 위치(`dtp-todo/references/`)를 참조 경로로 유지. **설계 결정: plan-guide.md에 핵심 내용을 인라인 흡수하여 외부 참조 없이 자족적으로 만든다.**

#### 2. dtp-plan/SKILL.md 변경 사항

**프로세스 확장**:
- Step 4(구현 계획 수립) 이후에 "Step 4.5: 복잡도 판별" 단계 추가
- Step 4.5 결과가 복잡 모드이면 "Step 4.6: 실행 아키텍처 설계" 추가
- Step 6(PLAN.md 작성)에서 확장된 출력 형식 사용

**PLAN.md 출력 형식 변경**:

```markdown
## 3. 실행 체크리스트

> 총 {N}개 Step | 실행 모드: {단순 / 복잡}

### Step 1: {작업 제목}
- [ ] 완료
- **파일**: {대상 파일 경로}
- **작업 내용**: {구체적 구현 내용}
- **완료 기준**: {검증 가능한 완료 조건}
- **테스트**: {검증 명령어 또는 방법}
- **실행 방법**: {direct / sub-agent}
- **의존**: {선행 Step 번호 또는 "없음"}

### Step 2: ...

## 4. QA 체크리스트
### 기능 테스트
- [ ] {항목}
### 회귀 테스트
- [ ] {항목}
### 코드 품질
- [ ] {항목}
### 보안                          ← 추가
- [ ] {항목}

## 5. 복잡도 판별                   ← 추가 (기존 5→7로 번호 시프트)
| 기준 | 값 | 판정 |
| 실행 모드 | {단순 / 복잡} |

## 6. 실행 아키텍처 (복잡 모드 시)    ← 조건부 추가
### C-1. 에이전트 토폴로지
### C-2. 스킬 요구사항
### C-3. 도구 요구사항
### C-4. 테스트 전략

## 7. 기술 컨텍스트               ← 기존 5→7
## 8. 리스크 및 대응               ← 기존 6→8
```

**섹션 번호 재배치 요약**:

| 기존 | 변경 후 | 내용 |
|------|---------|------|
| 1. 코드 분석 | 1. 코드 분석 | 동일 |
| 2. 구현 계획 | 2. 구현 계획 | 동일 |
| 3. 실행 체크리스트 | 3. 실행 체크리스트 | **확장** (블록 형식 + 완료기준/테스트/실행방법/의존) |
| 4. QA 체크리스트 | 4. QA 체크리스트 | **확장** (보안 카테고리 추가) |
| — | 5. 복잡도 판별 | **신규** |
| — | 6. 실행 아키텍처 | **신규** (복잡 모드 조건부) |
| 5. 기술 컨텍스트 | 7. 기술 컨텍스트 | 번호만 변경 |
| 6. 리스크 및 대응 | 8. 리스크 및 대응 | 번호만 변경 |

#### 3. otp-dev/SKILL.md 파이프라인 재설계

**변경 전 (5 STEP)**:
```
STEP 1: TASK → STEP 2: ANALYSIS → [QA] → 검토
  → STEP 3: PLAN → [QA] → 검토
  → STEP 4: TODO(4-1) + TEST-SCENARIO(4-2) → 검토/승인
  → STEP 5: EXECUTE → [Test] → 완료
```

**변경 후 (4 STEP)**:
```
STEP 1: TASK → STEP 2: ANALYSIS → [QA] → 검토
  → STEP 3: PLAN + TEST-SCENARIO → [QA] → 검토/승인
  → STEP 4: EXECUTE → [Test] → 완료
```

**STEP 3 변경 상세**:
- 3-1: dtp-plan 워커 디스패치 (opus) — 기존과 동일하지만, 확장된 PLAN.md를 생성
- 3-2: dtp-test-scenario 워커 디스패치 (haiku) — PLAN 완료 후 연속 실행
- dtp-qa 워커 호출 → PM 검토 게이트 → 사용자 보고 (승인 = EXECUTE 시작 허가)

**STEP 4 (기존 STEP 5) 변경 상세**:
- `checklist_source`: `PLAN.md 경로, 섹션: 3. 실행 체크리스트`
- `TODO.md 경로, 섹션: Part A` 참조 제거

**STATE.md 템플릿 변경**:
- 단계 목록: `{TASK / ANALYSIS / PLAN+TEST-SCENARIO / EXECUTE}` (TODO+TEST-SCENARIO → PLAN+TEST-SCENARIO)
- 산출물 테이블에서 `TODO.md` 행 제거

**파이프라인 다이어그램 변경**:
```
dtp-task → dtp-analysis → [QA] → 검토
  → dtp-plan → dtp-test-scenario → [QA] → 검토/승인
  → dtp-execute → [Test] → 완료
```

#### 5. TEST-SCENARIO 스킵 조건 (문서 전용 작업)

otp-dev, otp-dev-short 양쪽에 다음 스킵 조건을 추가:

```markdown
### TEST-SCENARIO 스킵 조건

작업 유형이 **문서 전용**(코드 변경 없음, SKILL.md/가이드/설정 문서만 수정)인 경우:
- TEST-SCENARIO 워커 디스패치를 **스킵**한다
- QA + PM 검토만으로 승인 게이트를 구성한다
- 사용자 보고 시 "TEST-SCENARIO: 문서 전용 작업으로 스킵" 표기
```

**판별 기준**: PLAN.md의 파일 변경 계획에서 수정 대상이 모두 `.md` 파일이고, 소스 코드(.ts/.js/.py/.go 등)가 없으면 문서 전용으로 판별.

#### 6. dtp-execute 참조 통일

**dtp-execute/SKILL.md 변경**:
- Full Task checklist_source: `TODO.md Part A` → `PLAN.md 섹션 3 실행 체크리스트`
- Full Task QA: `TODO.md Part B` → `PLAN.md 섹션 4 QA 체크리스트`
- Full/Short 분기가 사실상 동일해지므로 단순화 가능

**dtp-execute/references/execute-guide.md 변경**:
- checklist_source 우선순위 리스트에서 `TODO.md Part A` 제거
- QA 참조에서 `TODO.md Part B` 제거
- Full/Short 체크박스 갱신 분기를 `PLAN.md` 단일 소스로 통합

### 의존성 및 환경 변경

없음. 모든 변경은 마크다운 문서 수정이다.

### 테스트 전략

- **문서 정합성 검증**: 변경된 파일 간 상호 참조가 정확한지 확인
  - otp-dev에서 dtp-plan 디스패치 시 전달하는 산출물 경로가 SKILL.md의 입출력과 일치하는지
  - dtp-execute의 checklist_source가 PLAN.md의 실제 섹션 번호와 일치하는지
- **기존 호환성**: otp-dev-short는 변경 없이 동작하는지 확인
- **레거시 보존**: dtp-todo/SKILL.md가 수정 없이 남아 있는지 확인

## 3. 실행 체크리스트

> 총 5개 Step | 실행 모드: 단순

### Step 1: plan-guide.md에 TODO 고유 가치 흡수
- [ ] 완료
- **파일**: `skills/dtp-plan/references/plan-guide.md`
- **작업 내용**:
  - "실행 체크리스트 작성" 섹션을 블록 형식으로 확장 (Step별 완료 기준, 테스트, 실행 방법, 의존 필드 추가)
  - 분해 규칙 추가 (1파일=1작업, 독립 테스트 가능, 의존성 순서)
  - "QA 체크리스트 작성" 섹션에 B-4 보안 카테고리 추가
  - "복잡도 판별" 섹션 신규 추가 (5개 기준 테이블, 단순/복잡 판정)
  - "실행 아키텍처 (복잡 모드)" 섹션 신규 추가 (C-1~C-4, execute-plan-guide.md 핵심 내용 인라인)
  - 품질 체크리스트에 복잡도/보안/실행 아키텍처 항목 추가
- **완료 기준**: plan-guide.md만 읽으면 기존 todo-guide.md + execute-plan-guide.md의 모든 고유 가치를 수행할 수 있어야 함
- **테스트**: 변경된 plan-guide.md의 섹션 목록이 todo-guide.md Part A/B/C와 execute-plan-guide.md의 핵심 내용을 모두 포함하는지 대조
- **실행 방법**: direct
- **의존**: 없음

### Step 2: dtp-plan/SKILL.md 프로세스 및 출력 형식 확장
- [ ] 완료
- **파일**: `skills/dtp-plan/SKILL.md`
- **작업 내용**:
  - 프로세스에 "Step 4.5: 복잡도 판별", "Step 4.6: 실행 아키텍처 설계 (조건부)" 추가
  - PLAN.md 출력 형식 변경: 섹션 3 블록 형식, 섹션 4 보안 추가, 섹션 5 복잡도 판별, 섹션 6 실행 아키텍처 (조건부), 기존 5→7 기술 컨텍스트, 기존 6→8 리스크
  - 품질 체크리스트에 복잡도/보안/실행 아키텍처 관련 항목 추가
  - description 업데이트: 보장 출력에 확장된 PLAN.md 내용 반영
- **완료 기준**: SKILL.md의 출력 형식이 핵심 설계의 섹션 번호 재배치와 정확히 일치
- **테스트**: SKILL.md의 출력 형식 템플릿과 plan-guide.md의 가이드 내용이 상호 정합하는지 대조
- **실행 방법**: direct
- **의존**: Step 1

### Step 3: otp-dev/SKILL.md 파이프라인 재설계
- [ ] 완료
- **파일**: `skills/otp-dev/SKILL.md`
- **작업 내용**:
  - description 업데이트: "5단계" → "4단계"
  - 파이프라인 다이어그램 변경
  - STEP 3를 "PLAN + TEST-SCENARIO"로 확장 (3-1: dtp-plan, 3-2: dtp-test-scenario)
  - 기존 STEP 4(TODO+TEST-SCENARIO) 섹션 제거
  - 기존 STEP 5(EXECUTE) → STEP 4로 번호 변경
  - STEP 4의 checklist_source를 `PLAN.md 경로, 섹션: 3. 실행 체크리스트`로 변경
  - STATE.md 템플릿 갱신: 단계 목록, 산출물 테이블에서 TODO.md 제거
  - 변경이력 테이블에 v1.2 추가
- **완료 기준**: 파이프라인이 4 STEP으로 동작하고, TODO 디스패치가 제거되며, STATE.md 템플릿에 TODO 흔적이 없음
- **테스트**: STEP 번호가 1~4로 연속이고, 모든 디스패치 프롬프트의 경로/섹션 참조가 정확한지 확인
- **실행 방법**: direct
- **의존**: Step 2

### Step 4: dtp-execute/SKILL.md checklist_source 통일
- [ ] 완료
- **파일**: `skills/dtp-execute/SKILL.md`
- **작업 내용**:
  - Full Task checklist_source를 `TODO.md Part A` → `PLAN.md 섹션 3 실행 체크리스트`로 변경
  - Full Task QA 참조를 `TODO.md Part B` → `PLAN.md 섹션 4 QA 체크리스트`로 변경
  - Full/Short 분기가 동일해지므로, 분기 설명을 PLAN.md 단일 소스로 단순화
- **완료 기준**: dtp-execute/SKILL.md에 `TODO.md` 참조가 없음 (레거시 호환 주석 제외)
- **테스트**: 파일 내 `TODO.md` 문자열 검색 결과가 0이거나 레거시 주석만 포함
- **실행 방법**: direct
- **의존**: Step 2

### Step 5: dtp-execute/references/execute-guide.md 참조 통일
- [ ] 완료
- **파일**: `skills/dtp-execute/references/execute-guide.md`
- **작업 내용**:
  - checklist_source 우선순위에서 `TODO.md Part A` 제거
  - QA 참조에서 `TODO.md Part B` 제거
  - Full/Short 체크박스 갱신 분기를 `PLAN.md` 단일 소스로 통합
  - 관련 설명 텍스트 업데이트
- **완료 기준**: execute-guide.md에 `TODO.md` 참조가 없음
- **테스트**: 파일 내 `TODO.md` 문자열 검색 결과가 0
- **실행 방법**: direct
- **의존**: Step 4

## 4. QA 체크리스트

### 기능 테스트
- [ ] PLAN.md 출력 형식에 확장된 실행 체크리스트(블록 형식 + 6개 필드)가 포함됨
- [ ] QA 체크리스트에 보안(B-4) 카테고리가 추가됨
- [ ] 복잡도 판별 섹션이 PLAN.md 출력 형식에 존재함
- [ ] 실행 아키텍처 섹션이 복잡 모드 조건부로 포함됨
- [ ] otp-dev 파이프라인이 4 STEP으로 동작함
- [ ] TEST-SCENARIO가 PLAN 이후 같은 STEP에서 실행됨
- [ ] dtp-execute가 PLAN.md를 단일 checklist_source로 사용함

### 회귀 테스트
- [ ] otp-dev-short 파이프라인에 변경 없음
- [ ] dtp-todo/SKILL.md가 수정 없이 보존됨
- [ ] execution-plan.json 생성 로직이 유지됨
- [ ] dtp-execute의 execution-plan.json 기반 FE/BE 병렬 로직이 변경 없음

### 코드 품질
- [ ] 모든 파일 간 상호 참조(경로, 섹션 번호)가 일관됨
- [ ] 마크다운 형식이 올바름 (헤딩 레벨, 테이블 구문)
- [ ] 변경이력이 업데이트됨

### 보안
- [ ] 해당 없음 (마크다운 문서 변경만 수행)

## 5. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 | Markdown (SKILL.md, 가이드) | — |

### 사용 MCP

해당 없음.

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| dtp-execute의 섹션 번호 참조 오류 | EXECUTE 단계에서 잘못된 체크리스트 참조 | Step 4~5에서 PLAN.md 섹션 번호와 dtp-execute 참조를 교차 검증 |
| 기존 진행중인 태스크의 STATE.md 호환 | 이전 STATE.md에 TODO 단계가 남아 있을 수 있음 | 세션 복원 시 STATE.md의 단계 목록을 현재 파이프라인에 맞게 해석하도록 otp-dev에 폴백 규칙 추가 고려 (이번 태스크 범위 외) |
| PLAN.md 크기 증가 | 복잡 모드 시 Part C까지 포함하면 문서가 길어짐 | Part C는 조건부이므로 단순 모드에서는 기존과 동일한 크기 유지 |
