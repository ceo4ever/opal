# PLAN: task-flow Full Task / Short Task 듀얼 모드 분리

> 작성일: 2026-03-13 | 참조: TASK.md, RESEARCH.md

## 1. 구현 범위

### 신규 생성 파일

없음 (기존 파일 수정만)

### 수정 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/task-flow/SKILL.md` | 듀얼 모드 파이프라인, 모드 판별, QA 호출 변경, 체크리스트 갱신 규칙 |
| 2 | `skills/task-flow/references/plan-guide.md` | Short Task 통합 PLAN 가이드 추가 |
| 3 | `skills/task-flow/references/todo-guide.md` | Full Task 전용 명시, 체크박스 형식 통일 |
| 4 | `skills/task-flow/references/execute-guide.md` | 체크리스트 갱신 규칙 (`[ ]`→`[x]`), 상태 이모지 폐지 |
| 5 | `skills/task-flow/references/research-guide.md` | Full Task 전용 명시 |
| 6 | `agents/claude/task-flow-qa/AGENT.md` | 호출 시점 변경, mode 입력 추가, Short Task PLAN 검증 기준 |
| 7 | `agents/cursor/task-flow-qa.md` | #6과 동기화 |
| 8 | `agents/antigravity/task-flow-qa/SKILL.md` | #6과 동기화 |
| 9 | `CLAUDE.md` | Core Workflow 섹션 듀얼 모드 다이어그램 |

### 영향 확인 (변경 없지만 검증 필요)

| # | 파일 경로 | 확인 사항 |
|---|----------|----------|
| 1 | `agents/claude/task-flow-planner/AGENT.md` | Full Task 복잡 모드에서 기존대로 호출되는지 |
| 2 | `agents/claude/task-flow-test/AGENT.md` | Full Task 복잡 모드에서 기존대로 호출되는지 |
| 3 | `skills/task-flow/references/execute-plan-guide.md` | Part C 참조가 기존과 동일한지 |

## 2. 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | SKILL.md 전면 재구성 | `skills/task-flow/SKILL.md` | 높음 |
| 2 | plan-guide.md — Short Task 통합 PLAN 가이드 추가 | `references/plan-guide.md` | 중간 |
| 3 | research-guide.md — Full Task 전용 명시 | `references/research-guide.md` | 낮음 |
| 4 | todo-guide.md — Full Task 전용 + 체크박스 통일 | `references/todo-guide.md` | 중간 |
| 5 | execute-guide.md — 체크리스트 갱신 규칙 | `references/execute-guide.md` | 중간 |
| 6 | QA 에이전트 (claude) | `agents/claude/task-flow-qa/AGENT.md` | 중간 |
| 7 | QA 에이전트 (cursor) | `agents/cursor/task-flow-qa.md` | 낮음 (동기화) |
| 8 | QA 에이전트 (antigravity) | `agents/antigravity/task-flow-qa/SKILL.md` | 낮음 (동기화) |
| 9 | CLAUDE.md Core Workflow 업데이트 | `CLAUDE.md` | 낮음 |

## 3. 핵심 설계

### 3.1 SKILL.md 구조 (재구성 후)

```
frontmatter (description에 Short Task 트리거 추가)
├── 구현 금지 원칙 (공통, 변경 없음)
├── 워크플로우 개요 (듀얼 모드 다이어그램)
├── 모드 판별 규칙 ★신규
│   ├── Short Task 진입 조건 (5개 AND)
│   ├── 사용자 오버라이드
│   └── 에스컬레이션 규칙
├── QA 에이전트 호출 규칙 (공통, mode 필드 추가)
├── Planner 에이전트 호출 규칙 (Full Task 전용 명시)
├── Test 에이전트 호출 규칙 (Full Task 전용 명시)
├── 작업 유형 판별 (공통, 변경 없음)
├── 산출물 저장 구조 (Full/Short 분기)
├── 프로젝트 컨텍스트 로딩 (공통, 변경 없음)
├── Git 커밋 점검 (공통, 변경 없음)
├── STEP 1: TASK (공통)
│   ├── TASK.md 작성 (변경 없음)
│   ├── 모드 판별 + 제안 ★신규
│   └── QA 생략, 사용자 검토 ★변경
├── === Full Task 경로 ===
│   ├── STEP 2: RESEARCH (QA 호출 + 사용자 검토)
│   ├── STEP 3: PLAN (QA 호출 + 사용자 검토)
│   ├── STEP 4: TODO (QA 생략, 사용자 검토)
│   └── STEP 5: EXECUTE (체크리스트 갱신 + QA)
├── === Short Task 경로 ===
│   ├── STEP 2: PLAN 통합 (QA 호출 + 사용자 검토)
│   └── STEP 3: EXECUTE (체크리스트 갱신 + QA)
├── 게이트 체크포인트 규칙 (공통, QA 있는 단계만)
└── 실행 모드 (전체/단계별/이어하기 — 모드별 예시)
```

### 3.2 워크플로우 다이어그램 (변경 후)

```
사용자 지시 → [Git 점검] → [TASK] → 모드 판별 → 사용자 검토
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
              [Full Task]                             [Short Task]
                    │                                       │
          [RESEARCH] → [QA] → 검토                [PLAN 통합] → [QA] → 검토
                    │                                       │
          [PLAN] → [QA] → 검토                        승인 → [EXECUTE]
                    │                                       │
          [TODO] → 검토                             [QA] → 완료 보고
                    │
              승인 → [EXECUTE]
                    │
              [QA] → 완료 보고
```

### 3.3 모드 판별 로직

TASK.md 작성 완료 후, 아래 조건을 **모두** 충족하면 Short Task 제안:

| # | 조건 | 판별 방법 |
|---|------|----------|
| 1 | 예상 변경 파일 ≤3개 | TASK.md 요구사항에서 추정 |
| 2 | 예상 Step 수 ≤5개 | 요구사항 분해 시 추정 |
| 3 | 단일 모듈 범위 | 요구사항이 하나의 모듈/레이어에 한정 |
| 4 | 외부 의존성 없음 | 새 API, 패키지, 도구 불필요 |
| 5 | 작업 유형 적합 | 버그 수정, 단순 기능 수정, 설정 변경, 문서 수정 |

**사용자 보고 형식:**
```
📋 [TASK] 완료 보고

📎 산출물: tasks/{NNN}-{name}/TASK.md

💡 모드 제안: {Short Task / Full Task}
   근거: {조건 충족/미충족 요약}

다음 단계로 넘어갈까요? (모드 변경도 가능합니다)
```

### 3.4 Short Task 통합 PLAN 템플릿

```markdown
# PLAN: {태스크 제목}

> 작성일: YYYY-MM-DD | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일
| 파일 | 역할 | 변경 필요 |
|------|------|----------|

### 현재 구현
{핵심 코드 구조 요약}

### 영향 범위
{변경이 미치는 영향}

## 2. 구현 계획

### 변경 파일
| # | 파일 경로 | 변경 내용 |
|---|----------|----------|

### 핵심 설계
{클래스/함수 시그니처, 데이터 모델 등}

## 3. 실행 체크리스트

- [ ] Step 1: {제목} — {파일} — {작업 내용}
- [ ] Step 2: ...
- [ ] ...

## 4. QA 체크리스트

### 기능 테스트
- [ ] {항목}

### 회귀 테스트
- [ ] {항목}

### 코드 품질
- [ ] {항목}
```

### 3.5 Full Task TODO.md 체크박스 형식 변경

**기존 (이모지 상태):**
```markdown
### Step 1: {제목}
- **상태**: ⬜ 대기
```

**변경 후 (체크박스):**
```markdown
### Step 1: {제목}
- [ ] 완료
- **파일**: ...
- **작업 내용**: ...
```

EXECUTE 시 `- [ ] 완료` → `- [x] 완료`로 갱신.

### 3.6 QA 에이전트 변경 설계

**입력 필드 추가:**
```
| mode | 태스크 모드 (`full` / `short`) |
```

**호출 시점 변경:**
```
Full Task:
  [RESEARCH.md 완료] → QA → 사용자 검토
  [PLAN.md 완료] → QA → 사용자 검토
  [EXECUTE 완료] → QA → 사용자 보고

Short Task:
  [PLAN.md 완료] → QA → 사용자 검토
  [EXECUTE 완료] → QA → 사용자 보고
```

**Short Task PLAN 검증 기준 추가:**

| # | 검증 항목 | 확인 내용 |
|---|----------|----------|
| SP-1 | 코드 분석 충분성 | 관련 파일을 실제로 읽고 분석했는가? |
| SP-2 | 구현 계획 구체성 | 변경 파일별 구체적 작업이 명시되었는가? |
| SP-3 | 체크리스트 완전성 | TASK.md 요구사항이 모두 Step으로 분해되었는가? |
| SP-4 | QA 항목 커버리지 | 기능/회귀/품질 테스트가 포함되었는가? |
| SP-5 | Short Task 적정성 | 이 작업이 Short Task로 적합한가? (에스컬레이션 필요 여부) |

## 4. 의존성 및 환경 변경

없음. 마크다운 파일 수정만 수행.

## 5. 테스트 전략

이 태스크는 코드가 아닌 **스킬/에이전트 정의 파일(.md)** 수정이므로, 동적 테스트 대신 **문서 정합성 검증**으로 대체:

- [ ] Full Task 파이프라인: TASK→RESEARCH(QA)→PLAN(QA)→TODO→EXECUTE(QA) 흐름이 SKILL.md에 일관되게 기술
- [ ] Short Task 파이프라인: TASK→PLAN(QA)→EXECUTE(QA) 흐름이 SKILL.md에 일관되게 기술
- [ ] 모든 references/ 가이드가 올바른 모드를 참조
- [ ] QA 에이전트 3개 플랫폼 파일의 내용 동일
- [ ] CLAUDE.md 다이어그램이 SKILL.md와 일치
- [ ] 기존 에이전트(planner, test) 호출 경로가 변경되지 않음

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| SKILL.md 대폭 재구성으로 기존 Full Task 회귀 | 높음 | 기존 STEP 2~5 로직을 최대한 보존, QA 호출 여부만 변경 |
| QA 에이전트 3개 플랫폼 동기화 누락 | 중간 | claude 버전을 먼저 완성 후 cursor/antigravity에 복사 |
| Short Task 모드 판별 오류 | 중간 | 에스컬레이션 규칙 + QA의 SP-5 검증 |
