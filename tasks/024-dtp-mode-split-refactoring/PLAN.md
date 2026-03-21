# PLAN: dev-task-pilot 모드별 스킬/에이전트 분리 리팩토링

> 작성일: 2026-03-21 | 참조: TASK.md, ANALYSIS.md

---

## 1. 구현 범위

### 신규 생성 파일

| # | 파일 경로 | 역할 |
|---|-----------|------|
| 1 | `skills/dev-task-pilot/modes/dev-full.md` | Full Task 파이프라인 상세 정의 |
| 2 | `skills/dev-task-pilot/modes/dev-short.md` | Short Task 파이프라인 상세 정의 |
| 3 | `skills/dev-task-pilot/modes/wireframe-ui.md` | Wireframe UI 파이프라인 신규 정의 |
| 4 | `skills/dev-task-pilot/references/wireframe-task-guide.md` | Wireframe UI TASK 단계 가이드 |
| 5 | `skills/dev-task-pilot/references/wireframe-qa-guide.md` | Wireframe UI QA 검증 가이드 |
| 6 | `agents/claude/dtp-dev-full-agent/AGENT.md` | Full Task 워커 (Claude) |
| 7 | `agents/claude/dtp-dev-short-agent/AGENT.md` | Short Task 워커 (Claude) |
| 8 | `agents/claude/dtp-wireframe-ui-agent/AGENT.md` | Wireframe UI 워커 (Claude) |
| 9 | `agents/claude/dtp-qa-dev-agent/AGENT.md` | Full/Short QA 에이전트 (Claude) |
| 10 | `agents/claude/dtp-qa-wireframe-agent/AGENT.md` | Wireframe UI QA 에이전트 (Claude) |
| 11 | `agents/claude/dtp-action-plan-agent/AGENT.md` | 실행 아키텍처 설계 에이전트 (Claude) |
| 12 | `agents/claude/dtp-dev-test-agent/AGENT.md` | 코드 동적 검증 에이전트 (Claude) |
| 13 | `agents/cursor/dtp-dev-full-agent.md` | Full Task 워커 (Cursor) |
| 14 | `agents/cursor/dtp-dev-short-agent.md` | Short Task 워커 (Cursor) |
| 15 | `agents/cursor/dtp-wireframe-ui-agent.md` | Wireframe UI 워커 (Cursor) |
| 16 | `agents/cursor/dtp-qa-dev-agent.md` | Full/Short QA 에이전트 (Cursor) |
| 17 | `agents/cursor/dtp-qa-wireframe-agent.md` | Wireframe UI QA 에이전트 (Cursor) |
| 18 | `agents/cursor/dtp-action-plan-agent.md` | 실행 아키텍처 설계 에이전트 (Cursor) |
| 19 | `agents/cursor/dtp-dev-test-agent.md` | 코드 동적 검증 에이전트 (Cursor) |
| 20 | `agents/antigravity/dtp-dev-full-agent/SKILL.md` | Full Task 워커 (Antigravity) |
| 21 | `agents/antigravity/dtp-dev-short-agent/SKILL.md` | Short Task 워커 (Antigravity) |
| 22 | `agents/antigravity/dtp-wireframe-ui-agent/SKILL.md` | Wireframe UI 워커 (Antigravity) |
| 23 | `agents/antigravity/dtp-qa-dev-agent/SKILL.md` | Full/Short QA 에이전트 (Antigravity) |
| 24 | `agents/antigravity/dtp-qa-wireframe-agent/SKILL.md` | Wireframe UI QA 에이전트 (Antigravity) |
| 25 | `agents/antigravity/dtp-action-plan-agent/SKILL.md` | 실행 아키텍처 설계 에이전트 (Antigravity) |
| 26 | `agents/antigravity/dtp-dev-test-agent/SKILL.md` | 코드 동적 검증 에이전트 (Antigravity) |

### 수정 파일

| # | 파일 경로 | 변경 내용 |
|---|-----------|----------|
| 1 | `skills/dev-task-pilot/SKILL.md` | 라우터로 리팩토링: 모드 판별 + 디스패치 + 공통 규칙만 유지 (1039줄 → ~400줄). Full/Short 경로 섹션 제거, modes/ 참조로 대체. Wireframe UI 모드 추가. 에이전트명 갱신 (dtp-agent → 모드별 워커, dtp-qa → dtp-qa-dev-agent, dtp-planner → dtp-action-plan-agent, dtp-test → dtp-dev-test-agent) |
| 2 | `opal/core/references/agents.md` | 에이전트 목록 갱신: 기존 4개 → 신규 7개 |
| 3 | `CLAUDE.md` | 에이전트 구조 표 갱신 (agents/ 섹션) |

### 삭제 대상 (기존 에이전트 제거)

| # | 파일 경로 | 처리 방법 |
|---|-----------|----------|
| 1 | `agents/claude/dtp-agent/AGENT.md` | 삭제 (dtp-dev-full/short-agent로 완전 대체) |
| 2 | `agents/claude/dtp-qa/AGENT.md` | 삭제 (dtp-qa-dev-agent로 대체) |
| 3 | `agents/claude/dtp-planner/AGENT.md` | 삭제 (dtp-action-plan-agent로 리네임) |
| 4 | `agents/claude/dtp-test/AGENT.md` | 삭제 (dtp-dev-test-agent로 리네임) |
| 5 | `agents/cursor/dtp-agent.md` | 삭제 |
| 6 | `agents/cursor/dtp-qa.md` | 삭제 |
| 7 | `agents/cursor/dtp-planner.md` | 삭제 |
| 8 | `agents/cursor/dtp-test.md` | 삭제 |
| 9 | `agents/antigravity/dtp-agent/SKILL.md` | 삭제 |
| 10 | `agents/antigravity/dtp-qa/SKILL.md` | 삭제 |
| 11 | `agents/antigravity/dtp-planner/SKILL.md` | 삭제 |
| 12 | `agents/antigravity/dtp-test/SKILL.md` | 삭제 |

### 영향 확인 (변경 없지만 확인 필요)

| # | 파일 경로 | 확인 사항 |
|---|-----------|----------|
| 1 | `skills/dev-task-pilot/references/analysis-guide.md` | 기존 가이드 그대로 dtp-dev-full-agent가 사용 → 변경 불필요 확인 |
| 2 | `skills/dev-task-pilot/references/plan-guide.md` | Full/Short 섹션 모두 그대로 유지 → 변경 불필요 확인 |
| 3 | `skills/dev-task-pilot/references/execute-guide.md` | dtp-dev-full/short-agent 모두 동일하게 사용 → 변경 불필요 확인 |
| 4 | `skills/dev-task-pilot/references/todo-guide.md` | 변경 없음 확인 |
| 5 | `skills/wireframe-builder/SKILL.md` | Wireframe UI 모드에서 호출하는 스킬 — 인터페이스 파악 필요 |
| 6 | `skills/ui-designer/SKILL.md` | Wireframe UI 모드에서 호출하는 스킬 — 인터페이스 파악 필요 |

---

## 2. 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | modes/dev-full.md 작성 | `skills/dev-task-pilot/modes/dev-full.md` | 중 (기존 SKILL.md에서 Full 경로 추출 + 재구성) |
| 2 | modes/dev-short.md 작성 | `skills/dev-task-pilot/modes/dev-short.md` | 중 (기존 SKILL.md에서 Short 경로 추출 + 재구성) |
| 3 | modes/wireframe-ui.md 작성 | `skills/dev-task-pilot/modes/wireframe-ui.md` | 높 (신규 파이프라인 설계) |
| 4 | wireframe-task-guide.md 작성 | `skills/dev-task-pilot/references/wireframe-task-guide.md` | 중 (신규 가이드) |
| 5 | wireframe-qa-guide.md 작성 | `skills/dev-task-pilot/references/wireframe-qa-guide.md` | 중 (신규 가이드) |
| 6 | SKILL.md 리팩토링 (라우터화) | `skills/dev-task-pilot/SKILL.md` | 높 (구조적 대수술, 기존 동작 보존 필요) |
| 7 | Claude 에이전트 7개 생성 | `agents/claude/dtp-dev-*/AGENT.md` 등 | 중 (기존 에이전트 기반 파생) |
| 8 | Cursor 에이전트 7개 생성 | `agents/cursor/dtp-dev-*.md` 등 | 하 (Claude 버전과 내용 동일, 포맷만 플랫) |
| 9 | Antigravity 에이전트 7개 생성 | `agents/antigravity/dtp-dev-*/SKILL.md` 등 | 하 (Claude 버전과 내용 동일, 폴백 모드 설명 추가) |
| 10 | 기존 에이전트 12개 삭제 | `agents/claude|cursor|antigravity/dtp-{agent,qa,planner,test}/` | 하 (파일 삭제) |
| 11 | opal/core/references/agents.md 갱신 | `opal/core/references/agents.md` | 하 (목록 재작성) |
| 12 | CLAUDE.md 갱신 | `CLAUDE.md` | 하 (에이전트 목록 표 수정) |

---

## 3. 핵심 설계

### 3.1 SKILL.md 라우터 구조

리팩토링 후 SKILL.md는 다음 구조를 갖는다:

```
# 개발 작업 워크플로우 (Full Task / Short Task / Wireframe UI 멀티 모드)

## 구현 금지 원칙 (최우선 규칙)
## 워크플로우 개요 (3개 모드 포함 다이어그램)
## 모드 판별 규칙
  - Full Task 트리거
  - Short Task (기본)
  - Wireframe UI 트리거 (신규)
  - 사용자 오버라이드
  - 에스컬레이션 규칙
## 오케스트레이터-워커 실행 모델
  - 오케스트레이터 역할
  - 워커 에이전트 정의 (모드별 3개)
  - 워커 디스패치 규칙 (모드별 분기)
  - 워커 결과 수신
  - 워커 연속성 (Resume)
  - 크로스 플랫폼 폴백
## QA 에이전트 호출 규칙
  - dtp-qa-dev-agent (Full/Short)
  - dtp-qa-wireframe-agent (Wireframe UI)
## Planner 에이전트 호출 규칙 (dtp-action-plan-agent)
## Test 에이전트 호출 규칙 (dtp-dev-test-agent)
## 작업 유형 판별
## 산출물 저장 구조 (Full / Short / Wireframe UI)
## 프로젝트 컨텍스트 로딩
## 사전 점검: Git 커밋 확인
## STEP 1: TASK — 모드 판별 및 보고
## 모드별 파이프라인 → modes/ 파일로 위임
  - Full Task: modes/dev-full.md 참조
  - Short Task: modes/dev-short.md 참조
  - Wireframe UI: modes/wireframe-ui.md 참조
## 공통 완료 규칙 (DONE.md, STATE.md)
## 오케스트레이터 보고 형식
```

**핵심 변경사항:**
- 기존 "Full Task 경로" 섹션 (STEP 2~5, ~300줄) → `modes/dev-full.md` 위임
- 기존 "Short Task 경로" 섹션 (STEP 2~4, ~250줄) → `modes/dev-short.md` 위임
- 신규 Wireframe UI 경로 → `modes/wireframe-ui.md` 위임
- 에이전트 탐색 경로의 에이전트명 갱신

**모드별 워커 디스패치 분기 (SKILL.md 내 핵심 로직):**
```
모드 판별 결과:
  Full Task   → dtp-dev-full-agent 디스패치
  Short Task  → dtp-dev-short-agent 디스패치
  Wireframe UI → dtp-wireframe-ui-agent 디스패치
```

**QA 호출 분기:**
```
Full/Short 모드:  → dtp-qa-dev-agent 호출
Wireframe UI 모드: → dtp-qa-wireframe-agent 호출
```

---

### 3.2 modes/dev-full.md 구조

기존 SKILL.md의 "Full Task 경로" 섹션을 추출하여 독립 파일로 구성:

```markdown
# Full Task 파이프라인

> 참조: SKILL.md (오케스트레이터 라우터)

## 파이프라인 개요
TASK → ANALYSIS → PLAN → TODO → EXECUTE

## STEP 2: ANALYSIS
- 워커 디스패치 프롬프트 형식
- 이전 산출물: TASK.md
- 가이드: references/analysis-guide.md
- 워커 완료 시: dtp-qa-dev-agent 호출

## STEP 3: PLAN
- 워커 디스패치 프롬프트 형식
- 이전 산출물: TASK.md, ANALYSIS.md
- 가이드: references/plan-guide.md (Full 섹션)
- resume 권장: ANALYSIS 워커 resume
- 워커 완료 시: dtp-qa-dev-agent 호출

## STEP 4: TODO
- 워커 디스패치 프롬프트 형식
- 이전 산출물: TASK.md, ANALYSIS.md, PLAN.md
- 가이드: references/todo-guide.md
- 복잡 모드 판별 후 dtp-action-plan-agent 호출 분기

## STEP 5: EXECUTE
- 워커 디스패치 프롬프트 형식
- 이전 산출물: TASK.md, TODO.md
- 가이드: references/execute-guide.md
- 완료 시: dtp-dev-test-agent 호출 → DONE.md 생성
```

---

### 3.3 modes/dev-short.md 구조

기존 SKILL.md의 "Short Task 경로" 섹션을 추출:

```markdown
# Short Task 파이프라인

> 참조: SKILL.md (오케스트레이터 라우터)

## 파이프라인 개요
TASK → PLAN(통합) → TEST-SCENARIO → EXECUTE

## STEP 2: PLAN 통합
- 워커 디스패치 프롬프트 형식
- 이전 산출물: TASK.md
- 가이드: references/plan-guide.md (Short 섹션)
- 워커 완료 시: dtp-qa-dev-agent 호출

## STEP 3: TEST-SCENARIO 작성
- PLAN.md 기반 시나리오 도출
- 가이드: references/test-scenario-guide.md
- 사용자 승인 요청

## STEP 4: EXECUTE
- 워커 디스패치 프롬프트 형식
- 이전 산출물: TASK.md, PLAN.md
- 가이드: references/execute-guide.md
- 완료 시: dtp-dev-test-agent 호출 → DONE.md 생성
```

---

### 3.4 modes/wireframe-ui.md 구조 (신규)

Wireframe UI 전용 파이프라인:

```markdown
# Wireframe UI 파이프라인

> 참조: SKILL.md (오케스트레이터 라우터)

## 파이프라인 개요
TASK → WIREFRAME → EXECUTE → QA

## STEP 1: TASK (Wireframe 특화)
오케스트레이터가 직접 수행한다 (워커 불필요).
- 가이드: references/wireframe-task-guide.md
- 목표 확인, 기술 환경 검토, 입력물 분류
- 입력물 분류:
  a. wireframe.md 이미 존재 → WIREFRAME 단계 스킵, EXECUTE로 이동
  b. 정책서/요구사항 문서 존재 → wireframe-builder 스킬 호출 (WIREFRAME)
  c. 구두 요청만 → wireframe-builder 스킬 호출 전 interview 스킬로 요구사항 보강

## STEP 2: WIREFRAME
- wireframe.md가 이미 있으면 스킵
- wireframe-builder 스킬 호출 → wireframe.md 생성
- 생성 완료 시 dtp-qa-wireframe-agent 호출 (wireframe 품질 검증)
- 사용자 검토 및 승인 요청

## STEP 3: EXECUTE (UI 구현)
- dtp-wireframe-ui-agent 디스패치
- 워커가 ui-designer 스킬을 호출하여 UI 구현
- 이전 산출물: wireframe.md
- 워커 완료 시 변경 파일 목록 반환

## STEP 4: QA
- dtp-qa-wireframe-agent 호출
- 가이드: references/wireframe-qa-guide.md
- 빌드/린트 검증 + wireframe.md↔코드 대조 체크리스트
- 판정 후 DONE.md 생성
```

---

### 3.5 references/wireframe-task-guide.md 내용 명세

```markdown
# Wireframe UI TASK 단계 가이드

## 목적
오케스트레이터가 직접 수행하는 Wireframe UI TASK 단계 가이드.
개발 태스크의 TASK.md 작성과 달리, UI 구현의 목표·환경·입력물을 분류한다.

## 프로세스

### 1단계: 목표 확인
- 구현할 화면/기능 목록 파악
- 기술 환경: React 프레임워크 버전, shadcn/ui 설치 여부, 기존 컴포넌트 패턴
- 출력 모드 결정: 프로토타입(bundle.html) vs 프로덕션(Next.js)

### 2단계: 입력물 분류 및 경로 결정
| 입력물 상태 | 판별 방법 | 다음 단계 |
|------------|----------|----------|
| wireframe.md 존재 | 파일 존재 확인 | WIREFRAME 스킵 → EXECUTE |
| 정책서/요구사항 문서 존재 | .md/.txt/.pdf 파일 | WIREFRAME (wireframe-builder 호출) |
| 이미지(스케치/스크린샷) 존재 | .png/.jpg 파일 | WIREFRAME (wireframe-builder 호출) |
| 구두 요청만 | 파일 없음 | interview → WIREFRAME |

### 3단계: TASK.md 작성 (Wireframe 특화)
```markdown
# TASK: {화면명} UI 구현

> 작성일: YYYY-MM-DD | 작업 유형: Wireframe UI

## 구현 목표
{구현할 화면 목록}

## 기술 환경
- 프레임워크: {React/Next.js 버전}
- shadcn/ui: {설치됨/미설치}
- 출력 모드: {프로토타입/프로덕션}

## 입력물
- {입력물 유형}: {경로 또는 설명}

## wireframe.md 경로
- {기존 wireframe.md 경로, 또는 "생성 필요"}
```

### 4단계: 보고 및 승인 요청
```
[TASK] Wireframe UI 완료 보고
산출물: {TASK.md 경로}
입력물 분류: {wireframe.md 존재/생성 필요}
다음 단계: {WIREFRAME / EXECUTE}
진행할까요?
```
```

---

### 3.6 references/wireframe-qa-guide.md 내용 명세

```markdown
# Wireframe UI QA 가이드

## 목적
dtp-qa-wireframe-agent가 사용하는 QA 검증 기준.
두 가지 시점에서 호출된다:
1. WIREFRAME 단계 완료 후: wireframe.md 품질 검증
2. EXECUTE 단계 완료 후: 빌드/린트 + wireframe↔코드 대조

## WIREFRAME 단계 QA 기준
| # | 검증 항목 | 확인 내용 |
|---|----------|----------|
| W-1 | 섹션 완전성 | 서비스 개요, 전체 구조, 화면 목록, 화면별 상세, 공통 컴포넌트, shadcn 설치 목록 6개 섹션 존재 |
| W-2 | 화면 목록 완전성 | TASK.md에서 요청한 화면이 모두 wireframe.md에 포함되었는가 |
| W-3 | 상세 설계 충분성 | 각 화면의 ASCII 레이아웃, 구성 요소, 인터랙션이 명세되었는가 |
| W-4 | shadcn 컴포넌트 매핑 | 각 화면 요소가 shadcn 컴포넌트로 매핑되었는가 |
| W-5 | 구현 가능성 | ui-designer 스킬로 바로 구현 가능한 수준인가 |

## EXECUTE 단계 QA 기준
| # | 검증 항목 | 확인 내용 |
|---|----------|----------|
| E-1 | 빌드 성공 | 빌드 명령 실행 결과 오류 없음 |
| E-2 | 린트 통과 | ESLint/타입 체크 오류 없음 |
| E-3 | 화면 커버리지 | wireframe.md의 화면 목록이 모두 구현되었는가 |
| E-4 | 레이아웃 대조 | wireframe.md의 ASCII 레이아웃과 구현 화면 구조가 일치하는가 |
| E-5 | 컴포넌트 대조 | wireframe.md의 shadcn 컴포넌트 설치 목록이 모두 사용되었는가 |
| E-6 | 인터랙션 구현 | wireframe.md의 인터랙션 명세가 코드에 반영되었는가 |

## QA 문서 출력 형식
파일명: QA-WIREFRAME.md (WIREFRAME 단계) / QA-EXECUTE-UI.md (EXECUTE 단계)
형식: 기존 dtp-qa-dev-agent의 QA 문서 형식과 동일
```

---

### 3.7 에이전트 설계 명세

#### dtp-dev-full-agent (Claude)

**Frontmatter:**
```yaml
name: dtp-dev-full-agent
description: |
  dev-task-pilot Full Task 파이프라인의 각 단계(ANALYSIS/PLAN/TODO/EXECUTE)를
  독립 컨텍스트에서 실행하는 워커 에이전트.
  Full Task (TASK → ANALYSIS → PLAN → TODO → EXECUTE) 전용.
model: sonnet
color: blue
```

**내용**: 기존 dtp-agent AGENT.md와 동일하되, 단계 매핑 테이블을 Full Task 전용 단계(ANALYSIS/PLAN(Full)/TODO/EXECUTE)만 포함. "Full Task 워커" 명시.

---

#### dtp-dev-short-agent (Claude)

**Frontmatter:**
```yaml
name: dtp-dev-short-agent
description: |
  dev-task-pilot Short Task 파이프라인의 각 단계(PLAN/TEST-SCENARIO/EXECUTE)를
  독립 컨텍스트에서 실행하는 워커 에이전트.
  Short Task (TASK → PLAN(통합) → TEST-SCENARIO → EXECUTE) 전용.
model: sonnet
color: blue
```

**내용**: 기존 dtp-agent와 동일 구조. 단계 매핑을 Short Task 전용 단계만 포함.

---

#### dtp-wireframe-ui-agent (Claude)

**Frontmatter:**
```yaml
name: dtp-wireframe-ui-agent
description: |
  dev-task-pilot Wireframe UI 파이프라인의 EXECUTE 단계를 실행하는 워커 에이전트.
  wireframe.md를 입력으로 받아 ui-designer 스킬을 호출하여 UI를 구현한다.
model: sonnet
color: purple
```

**내용:**
- 역할: EXECUTE 단계에서 ui-designer 스킬을 호출하여 UI 구현
- 실행 프로세스:
  1. 오케스트레이터로부터 wireframe.md 경로, 출력 모드, 프로젝트 경로 수신
  2. wireframe.md 읽기
  3. ui-designer 스킬 실행 (스킬 경로 탐색 후 프로세스 따름)
  4. 변경된 파일 목록 수집
  5. 완료 시 changed_files, summary, status 반환

---

#### dtp-qa-dev-agent (Claude)

**Frontmatter:**
```yaml
name: dtp-qa-dev-agent
description: |
  dev-task-pilot Full/Short Task 산출물 품질 검증 에이전트.
  ANALYSIS, PLAN 단계 산출물을 독립적으로 검토하여 요약과 판정을 제공한다.
  기존 dtp-qa 에이전트를 Full/Short 모드 전용으로 리네임.
model: haiku
color: green
readonly: true
```

**내용**: 기존 dtp-qa AGENT.md와 동일 (내용 변경 없음, 이름만 변경).

---

#### dtp-qa-wireframe-agent (Claude)

**Frontmatter:**
```yaml
name: dtp-qa-wireframe-agent
description: |
  dev-task-pilot Wireframe UI 파이프라인 QA 에이전트.
  WIREFRAME 단계(wireframe.md 품질 검증)와 EXECUTE 단계(빌드/린트 + wireframe↔코드 대조)에서 호출된다.
model: haiku
color: green
readonly: false
```

**내용:**
- 호출 시점: WIREFRAME 완료 후 (Q-WIREFRAME.md 생성), EXECUTE 완료 후 (QA-EXECUTE-UI.md 생성)
- 실행 프로세스:
  1. wireframe-qa-guide.md 읽기
  2. WIREFRAME 단계: W-1~W-5 검증 항목 확인 → QA-WIREFRAME.md 생성
  3. EXECUTE 단계: 빌드/린트 실행 (readonly: false) + E-1~E-6 검증 → QA-EXECUTE-UI.md 생성
  4. Pass / Needs Revision 판정

---

#### dtp-action-plan-agent (Claude)

**Frontmatter:**
```yaml
name: dtp-action-plan-agent
description: |
  dev-task-pilot 실행 아키텍처 설계 에이전트. 기존 dtp-planner 리네임.
  TODO Part A(실행 체크리스트) + Part B(QA 체크리스트) 작성 완료 후 호출되어,
  복잡 모드 태스크의 실행 아키텍처(Part C)를 설계한다.
model: sonnet
color: purple
readonly: true
```

**내용**: 기존 dtp-planner AGENT.md와 동일 (내용 변경 없음, 이름만 변경).

---

#### dtp-dev-test-agent (Claude)

**Frontmatter:**
```yaml
name: dtp-dev-test-agent
description: |
  dev-task-pilot 코드 동적 검증 에이전트. 기존 dtp-test 리네임.
  EXECUTE 단계 완료 후 모든 모드에서 호출되어, TEST-SCENARIO.md를 입력으로 받아
  도구 결정 + 실행 + 결과 기록 + 판정을 수행한다.
model: sonnet
color: orange
readonly: false
```

**내용**: 기존 dtp-test AGENT.md와 동일 (내용 변경 없음, 이름만 변경).

---

#### 플랫폼별 포맷 규칙

**Cursor (.md 플랫 파일):**
- Claude 버전의 AGENT.md 내용과 동일
- Frontmatter 필드: name, description, model, readonly, tools, max_turns, timeout_mins
- 파일 확장자: `.md`

**Antigravity (SKILL.md):**
- Claude 버전 내용 + 폴백 모드 안내 문구 추가
- Frontmatter 필드: name, description, model
- model: `gemini-3.1-pro`
- 첫 섹션에 "실행 방식: Antigravity에서는 서브 에이전트가 지원되지 않으므로..." 안내

---

### 3.8 opal/core/references/agents.md 갱신 명세

기존 4개 → 신규 7개로 전면 교체:

```markdown
## dev-task-pilot 에이전트

### dtp-dev-full-agent
- **역할**: Full Task 워커 — ANALYSIS/PLAN/TODO/EXECUTE 단계 실행
- **호출 시점**: Full Task 각 단계 시작 시 오케스트레이터가 디스패치
- **입력**: 단계, 태스크 폴더 경로, 이전 산출물 경로, 가이드 경로
- **출력**: 산출물(.md) + 결과 반환

### dtp-dev-short-agent
- **역할**: Short Task 워커 — PLAN(통합)/TEST-SCENARIO/EXECUTE 단계 실행
- **호출 시점**: Short Task 각 단계 시작 시 오케스트레이터가 디스패치
- **입력**: 단계, 태스크 폴더 경로, 이전 산출물 경로, 가이드 경로
- **출력**: 산출물(.md) + 결과 반환

### dtp-wireframe-ui-agent
- **역할**: Wireframe UI 워커 — EXECUTE 단계(UI 구현) 실행
- **호출 시점**: Wireframe UI 파이프라인 EXECUTE 단계 시작 시
- **입력**: wireframe.md 경로, 출력 모드, 프로젝트 경로
- **출력**: 구현된 UI 파일 + 변경 파일 목록

### dtp-qa-dev-agent
- **역할**: Full/Short Task 산출물 품질 검증 (문서 리뷰)
- **호출 시점**: ANALYSIS, PLAN 완료 후 오케스트레이터가 호출
- **입력**: 검증 대상 산출물 경로, 모드(full/short), 단계
- **출력**: QA-{단계}.md 리뷰 문서

### dtp-qa-wireframe-agent
- **역할**: Wireframe UI 파이프라인 QA (wireframe 검증 + 빌드/코드 대조)
- **호출 시점**: WIREFRAME 완료 후, EXECUTE 완료 후
- **입력**: wireframe.md 경로, 구현 파일 경로 목록
- **출력**: QA-WIREFRAME.md / QA-EXECUTE-UI.md

### dtp-action-plan-agent
- **역할**: 실행 아키텍처 설계 (복잡 모드 Part C 생성)
- **호출 시점**: TODO 단계에서 복잡 태스크로 판별 시
- **입력**: TASK.md, ANALYSIS.md, PLAN.md, TODO.md (Part A+B)
- **출력**: TODO.md Part C (실행 토폴로지)

### dtp-dev-test-agent
- **역할**: 코드 동적 검증 (테스트 실행)
- **호출 시점**: EXECUTE 단계 완료 후 (Full/Short 모두)
- **입력**: TEST-SCENARIO.md, 변경된 파일 목록
- **출력**: TEST-SCENARIO.md (결과 채움 + 판정)
```

---

### 3.9 CLAUDE.md 갱신 명세

`agents/` 섹션의 에이전트 목록 표를 다음과 같이 갱신:

```markdown
├── claude/
│   ├── dtp-dev-full-agent/      Full Task 워커 에이전트
│   ├── dtp-dev-short-agent/     Short Task 워커 에이전트
│   ├── dtp-wireframe-ui-agent/  Wireframe UI 워커 에이전트
│   ├── dtp-qa-dev-agent/        Full/Short 문서 QA
│   ├── dtp-qa-wireframe-agent/  Wireframe UI QA
│   ├── dtp-action-plan-agent/   실행 아키텍처 설계 (Part C)
│   └── dtp-dev-test-agent/      코드 동적 검증
```

---

## 4. 의존성 및 환경 변경

- **추가 패키지**: 없음 (모두 마크다운 문서 작업)
- **환경 설정 변경**: 없음
- **외부 스킬 의존**:
  - `wireframe-builder`: Wireframe UI WIREFRAME 단계에서 호출 (기존 스킬 그대로 사용)
  - `ui-designer`: Wireframe UI EXECUTE 단계에서 dtp-wireframe-ui-agent가 호출 (기존 스킬 그대로 사용)

---

## 5. 테스트 전략

이 태스크는 코드가 아닌 마크다운 문서/에이전트 파일만 변경하므로, 테스트는 내용 검증 중심이다.

### 5.1 구조 검증 (자동)
- [ ] 신규 파일 26개 생성 확인: `Glob`으로 파일 존재 여부 확인
- [ ] 기존 에이전트 12개 삭제 확인: 해당 경로 파일 부재 확인
- [ ] modes/ 디렉토리 생성 확인

### 5.2 내용 검증 (수동)
- [ ] SKILL.md 라우터 구조: 모드별 워커 이름이 올바르게 기재되었는가
  - Full Task → `dtp-dev-full-agent`
  - Short Task → `dtp-dev-short-agent`
  - Wireframe UI → `dtp-wireframe-ui-agent`
- [ ] QA 호출 분기: Full/Short → `dtp-qa-dev-agent`, Wireframe UI → `dtp-qa-wireframe-agent`
- [ ] Planner/Test 에이전트명: `dtp-action-plan-agent`, `dtp-dev-test-agent`
- [ ] 기존 Full/Short Task 동작 보존: 기존 STEP 로직이 modes/ 파일에 완전히 추출되었는가

### 5.3 에이전트 파일 정합성 검증
- [ ] 각 에이전트 3플랫폼 동기화: 동일 역할/내용, 포맷만 다름
- [ ] Frontmatter 필수 필드 존재: name, description, model
- [ ] Antigravity 에이전트: 폴백 모드 안내 문구 존재

### 5.4 레지스트리 정합성 검증
- [ ] agents.md: 7개 에이전트 모두 등재, 역할/호출시점/입출력 완전 기재
- [ ] CLAUDE.md: agents/ 구조 표가 실제 파일 구조와 일치

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| SKILL.md 라우터 리팩토링 중 기존 로직 누락 | Full/Short Task 파이프라인 동작 불가 | 리팩토링 전 기존 SKILL.md의 Full/Short 경로 섹션을 줄 단위로 추출 확인. modes/ 파일 작성 후 기존 섹션과 대조 검증 |
| 에이전트 탐색 경로의 에이전트명 갱신 누락 | 오케스트레이터가 잘못된 워커 호출 | SKILL.md 내 에이전트 탐색 경로 섹션(워커/QA/Planner/Test) 4곳 모두 갱신 체크리스트 |
| Wireframe UI 모드의 스킬 연동 오류 | wireframe-builder / ui-designer 호출 실패 | EXECUTE 전 wireframe-builder, ui-designer SKILL.md를 Read하여 실제 입력/출력 형식 재확인 |
| 3플랫폼 에이전트 불일치 | 특정 플랫폼에서 에이전트 동작 오류 | Claude 버전 먼저 작성 → Cursor/Antigravity는 Claude 버전에서 포맷 변환으로 생성 (내용 비교 가능) |
| 기존 에이전트 삭제 시 참조 누락 | 기존 설정에서 구 에이전트명을 참조하는 경우 오류 | 삭제 전 `Grep`으로 전체 프로젝트에서 구 에이전트명(dtp-agent, dtp-qa, dtp-planner, dtp-test) 참조 검색 |
