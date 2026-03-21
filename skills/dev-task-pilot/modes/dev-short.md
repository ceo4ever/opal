# Short Task 파이프라인

> 참조: SKILL.md (오케스트레이터 라우터)
> 워커 에이전트: `dtp-dev-agent`
> QA 에이전트: `dtp-qa-dev-agent`

## 파이프라인 개요

```
TASK → PLAN(통합) → TEST-SCENARIO → EXECUTE
```

```
[워커: PLAN 통합] → [QA] → 검토
        │
[워커: TEST-SCENARIO 작성] → 검토/승인
        │
[워커: EXECUTE]
        │
[dtp-dev-test-agent 호출] → 완료 보고
```

> **Short Task는 단계를 줄이는 것이지, 분석을 줄이는 것이 아니다.** 코드 분석은 Full Task의 ANALYSIS와 동일한 깊이로 수행한다. 관련 코드를 실제로 읽고, 로직 흐름과 영향 범위를 파악한 뒤에 계획을 세운다.

---

## STEP 2: PLAN 통합 (코드 분석 + 구현 계획 + 체크리스트)

**오케스트레이터가 PLAN(통합) 워커를 디스패치한다.**

> **워커 디스패치**: 단계=PLAN-SHORT, 이전 산출물=TASK.md, 가이드=plan-guide.md (Short Task 섹션), 산출물=PLAN.md

**상세 가이드**: `references/plan-guide.md`의 "Short Task 통합 PLAN" 섹션을 읽고 따른다.

### Short Task PLAN.md 구조

```markdown
# PLAN: {태스크 제목}

> 작성일: YYYY-MM-DD | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일
| 파일 | 역할 | 변경 필요 |
|------|------|----------|

### 현재 구현
{핵심 로직 흐름: 입력 → 처리 → 출력}
{관련 함수/클래스 시그니처와 역할}

### 영향 범위
{호출자/피호출자 의존 관계}
{관련 테스트 파일}

## 2. 구현 계획

### 변경 파일
| # | 파일 경로 | 변경 내용 |
|---|----------|----------|

### 핵심 설계
{클래스/함수 시그니처, 변경 포인트 등}

## 3. 실행 체크리스트

- [ ] Step 1: {제목} — {파일} — {작업 내용}
- [ ] Step 2: ...

## 4. QA 체크리스트

### 기능 테스트
- [ ] {항목}

### 회귀 테스트
- [ ] {항목}

### 코드 품질
- [ ] {항목}
```

### 에스컬레이션 확인

PLAN 작성 중 아래 상황이 발생하면 에스컬레이션을 제안한다:
- 예상 변경 파일 ≥10개
- 다단계 기술 의사결정 필요
- 다중 모듈 간 연쇄 영향

### 워커 디스패치 프롬프트

```
dev-task-pilot PLAN-SHORT 워커로서 아래 태스크를 수행하라.

**태스크**: {태스크 제목}
**단계**: PLAN-SHORT
**태스크 폴더**: {tasks/{NNN}-{name}/}

**이전 산출물**:
- {tasks/{NNN}-{name}/TASK.md}

**단계 가이드**:
- {skills/dev-task-pilot/references/plan-guide.md 절대 경로} (Short Task 섹션)

**프로젝트 컨벤션**:
- {프로젝트 루트의 CLAUDE.md 절대 경로}

**산출물 저장 경로**: {tasks/{NNN}-{name}/PLAN.md}
```

### 워커 완료 시

워커가 PLAN.md를 반환하면, **오케스트레이터가 dtp-qa-dev-agent를 호출**한다. QA 결과를 포함하여 사용자에게 보고.

```
📋 [PLAN] 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/PLAN.md
📎 QA 리뷰: tasks/{NNN}-{태스크명}/QA-PLAN.md

[QA 요약]
- 검증 항목 {N}개 중 {통과}개 Pass, {경고}개 Warning
- 판정: {✅ Pass / ⚠️ Needs Revision}

승인하시면 TEST-SCENARIO 작성으로 넘어갑니다.
```

---

## STEP 3: TEST-SCENARIO (테스트 시나리오)

PLAN.md가 사용자의 승인을 받으면, **오케스트레이터가 TEST-SCENARIO 워커를 디스패치한다.**

> **워커 디스패치**: 단계=TEST-SCENARIO, 이전 산출물=TASK.md+PLAN.md, 가이드=test-scenario-guide.md, 산출물=TEST-SCENARIO.md

**상세 가이드**: `references/test-scenario-guide.md`를 읽고 따른다.

### 워커 디스패치 프롬프트

```
dev-task-pilot TEST-SCENARIO 워커로서 아래 태스크를 수행하라.

**태스크**: {태스크 제목}
**단계**: TEST-SCENARIO
**태스크 폴더**: {tasks/{NNN}-{name}/}

**이전 산출물**:
- {tasks/{NNN}-{name}/TASK.md}
- {tasks/{NNN}-{name}/PLAN.md}

**단계 가이드**:
- {skills/dev-task-pilot/references/test-scenario-guide.md 절대 경로}

**프로젝트 컨벤션**:
- {프로젝트 루트의 CLAUDE.md 절대 경로}

**산출물 저장 경로**: {tasks/{NNN}-{name}/TEST-SCENARIO.md}
```

워커 완료 시 사용자에게 보고:

```
📋 [TEST-SCENARIO] 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/TEST-SCENARIO.md

승인하시면 EXECUTE를 시작합니다.
```

---

## STEP 4: EXECUTE (실행)

TEST-SCENARIO.md가 사용자의 승인을 받으면, **오케스트레이터가 EXECUTE 워커를 디스패치한다.**

> **워커 디스패치**: 단계=EXECUTE-SHORT, 이전 산출물=TASK.md+PLAN.md, 가이드=execute-guide.md, 산출물=코드 변경

**상세 가이드**: `references/execute-guide.md`를 읽고 따른다.

### 체크리스트 갱신 규칙

워커가 각 Step 완료 시 PLAN.md의 실행 체크리스트를 즉시 갱신한다:
- `- [ ] Step N: ...` → `- [x] Step N: ...`

**QA 체크리스트 갱신**: 모든 실행 Step 완료 후, test 에이전트 호출 전에 워커가 QA 체크리스트(섹션 4)의 각 항목을 실제 검증하고 체크박스를 갱신한다:
- 통과 항목: `- [ ]` → `- [x]`
- 미통과 항목: `- [ ]` 유지 + 사유를 인라인 주석으로 기록 (예: `- [ ] 항목 <!-- 사유: ... -->`)

### 실행 흐름

1. 워커가 PLAN.md의 실행 체크리스트(섹션 3)를 순서대로 실행
2. 각 Step 완료 시: PLAN.md 체크박스 갱신
3. 블로커 발생 시 즉시 오케스트레이터에 반환
4. 모든 Step 완료 후:
   - QA 체크리스트(섹션 4)를 검증하고 체크박스 갱신 (통과: `[x]`, 미통과: `[ ]` + 사유)
   - 결과 반환 → **오케스트레이터가**:
     - **dtp-dev-test-agent 호출** → TEST-SCENARIO.md에 결과 채움 + 판정
     - **DONE.md 생성** (완료 리포트 규칙 참조)
     - 사용자에게 완료 보고

### 워커 디스패치 프롬프트

```
dev-task-pilot EXECUTE-SHORT 워커로서 아래 태스크를 수행하라.

**태스크**: {태스크 제목}
**단계**: EXECUTE-SHORT
**태스크 폴더**: {tasks/{NNN}-{name}/}

**이전 산출물**:
- {tasks/{NNN}-{name}/TASK.md}
- {tasks/{NNN}-{name}/PLAN.md}

**단계 가이드**:
- {skills/dev-task-pilot/references/execute-guide.md 절대 경로}

**프로젝트 컨벤션**:
- {프로젝트 루트의 CLAUDE.md 절대 경로}

**실행 규칙**:
1. PLAN.md의 실행 체크리스트(섹션 3)를 순서대로 실행한다
2. 각 Step 완료 시 PLAN.md 체크박스를 갱신한다
3. 모든 Step 완료 후 QA 체크리스트(섹션 4)를 검증한다
4. 완료 시 changed_files, summary, status를 반환한다
5. 블로커 발생 시 즉시 status: blocked로 반환한다
6. QA/Test 에이전트는 호출하지 않는다
```
