---
name: dev-task-pilot
description: |
  **개발 작업 워크플로우 오케스트레이터**. Full Task / Short Task / Wireframe UI 멀티 모드로 작업 유형에 맞는 파이프라인을 제공합니다.
  - Full Task: TASK → ANALYSIS → PLAN → TODO → EXECUTE (복잡하거나 난이도 높은 작업)
  - Short Task: TASK → PLAN(통합) → TEST-SCENARIO → EXECUTE (기본 모드, 대부분의 작업)
  - Wireframe UI: TASK → WIREFRAME → EXECUTE → QA (UI 설계·구현 전용)
  반드시 이 스킬을 사용해야 하는 상황: "새 태스크", "개발 시작", "기능 개발", "오류 수정", "기능 수정", "기능 개선", "리서치해줘", "분석해줘", "계획 세워줘", "TODO 만들어줘", "와이어프레임", "UI 만들어줘", "화면 구현", 코드 작성/수정이 필요한 모든 개발 작업 요청 시.
  ⚠️ 승인 전까지 분석과 계획만 수행합니다. 실제 코드 구현은 사용자의 명시적 "승인" 후 EXECUTE 단계에서 수행됩니다.
---

# 개발 작업 워크플로우 (Full Task / Short Task / Wireframe UI 멀티 모드)

## 구현 금지 원칙 (최우선 규칙)

**사용자가 명시적으로 "승인", "진행해", "구현해", "개발 시작" 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다.**

이 규칙이 존재하는 이유: 개발은 되돌리기 비용이 높다. 잘못된 방향으로 코드를 작성하면 수정에 원래 작성 시간의 2~3배가 들 수 있다. 그래서 분석과 계획을 충분히 하고, 사용자가 방향을 확인한 뒤에 구현에 들어가는 것이 전체 프로젝트 효율을 높인다.

허용되는 행위 (분석·계획 단계):
- 산출물 문서(.md) 작성
- QA 에이전트 호출 및 QA 문서 생성
- 코드베이스 읽기/분석 (Read, Grep, Glob)
- 웹 검색을 통한 기술 조사

허용되는 행위 (EXECUTE — 승인 후):
- 소스 코드 파일 생성/수정
- 패키지 설치, DB 스키마 변경, 설정 파일 수정
- 테스트 실행, 서브 에이전트 실행

금지되는 행위 (승인 전):
- 소스 코드 파일 생성/수정 (.py, .ts, .tsx, .sql 등)
- 패키지 설치 (pip install, npm install 등)
- DB 스키마 변경, 설정 파일 수정 (.env, yaml 등)

---

## 워크플로우 개요

알투는 **오케스트레이터**로서 모드를 판별하고, 모드별 워커 에이전트를 디스패치하여 실행한다.

```
사용자 지시 → [Git 점검] → [TASK 직접] → 모드 판별 → 사용자 검토
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
              [Full Task]              [Short Task]            [Wireframe UI]
              modes/dev-full.md        modes/dev-short.md      modes/wireframe-ui.md
```

**핵심 규칙**: 사용자의 명시적 승인 전까지 코드 생성/수정 금지. 오케스트레이터가 워커를 디스패치하여 각 단계를 실행하고, 사용자에게 보고한다.

---

## 모드 판별 규칙

### 기본 모드: Short Task

모든 작업은 Short Task로 시작한다. Short Task는 단계를 줄여 속도를 높이는 것이지, 분석 품질을 낮추는 것이 아니다.

### Wireframe UI 트리거 조건

아래 조건 중 하나라도 해당하면 Wireframe UI 모드를 **적용**한다:

| # | 조건 | 판별 방법 |
|---|------|----------|
| 1 | 사용자 명시 요청 | "와이어프레임", "UI 만들어줘", "화면 구현", "프로토타입" |
| 2 | wireframe.md 제공 | wireframe.md가 입력물로 제공됨 |
| 3 | UI 구현 요청 + 정책서/기획서 | 정책서/기획서와 함께 UI 구현을 요청 |

### Full Task 트리거 조건

Wireframe UI가 아닌 경우, 아래 조건 중 하나라도 해당하면 Full Task를 **제안**한다 (최종 결정은 사용자):

| # | 조건 | 판별 방법 |
|---|------|----------|
| 1 | 사용자 명시 요청 | "Full로 해줘" 등 사용자가 직접 지정 |
| 2 | 예상 변경 파일 ≥10개 | TASK.md 요구사항에서 추정 (대규모 변경) |
| 3 | 다단계 기술 의사결정 필요 | 아키텍처 선택, 기술 스택 비교 등 별도 ANALYSIS가 필요한 수준 |
| 4 | 다중 모듈 간 연쇄 영향 | 변경 A가 B, C에 연쇄적으로 영향하여 독립적 분석이 필요 |

**조건 2~4에 해당하면 Full Task를 제안하되, 사용자가 "Short로 해줘"라고 하면 Short로 진행한다.**

### 사용자 오버라이드

사용자가 모드를 지정할 수 있다:
- "Full로 해줘" → Full Task 강제
- "Short로 해줘" → Short Task 강제
- "와이어프레임으로" → Wireframe UI 강제
- 지정하지 않으면 자동 판별 결과를 따름

### 에스컬레이션 규칙

Short Task 진행 중 PLAN 작성 시 Full Task 조건에 해당하는 상황이 발견된 경우:
- 예상 변경 파일 ≥10개, 다단계 기술 의사결정 필요, 다중 모듈 간 연쇄 영향 중 하나라도 해당 → 에스컬레이션 제안
- 사용자 승인 시 Full Task로 전환 (TASK.md 유지, ANALYSIS부터 시작)

---

## 오케스트레이터-워커 실행 모델

### 오케스트레이터(알투)의 역할

알투는 오케스트레이터로서 다음 역할만 수행한다:

1. **TASK 단계 직접 수행** — 사용자 지시를 구조화하는 것은 오케스트레이터의 본질적 역할
2. **워커 디스패치** — 모드별 워커 에이전트를 디스패치
3. **QA/Planner/Test 에이전트 호출** — 워커 완료 후 필요한 에이전트를 오케스트레이터가 직접 호출
4. **게이트 체크포인트 중계** — 워커 결과를 사용자에게 보고하고 승인을 받음
5. **태스크 상태 추적** — 각 태스크의 현재 단계, 워커 상태, 블로커 여부를 관리

### 모드별 워커 에이전트

| 모드 | 워커 에이전트 | 역할 |
|------|-------------|------|
| Full Task | `dtp-dev-agent` | ANALYSIS / PLAN / TODO / TEST-SCENARIO / EXECUTE |
| Short Task | `dtp-dev-agent` | PLAN-SHORT / TEST-SCENARIO / EXECUTE-SHORT |
| Wireframe UI | `dtp-wireframe-ui-agent` | WIREFRAME/EXECUTE-WIREFRAME |

### 에이전트 탐색 경로 (모든 에이전트 공통)

에이전트명을 `{agent-name}`으로 치환하여 탐색:

1. `{프로젝트}/.opal/agents/{agent-name}/AGENT.md`
2. `~/.opal/agents/{agent-name}/AGENT.md`

### 워커 디스패치 규칙

**디스패치 시점**: TASK 이후의 각 단계 시작 시

**프롬프트 구성**: 오케스트레이터가 워커를 디스패치할 때, 모드별 파이프라인 파일(`modes/*.md`)에 정의된 프롬프트 형식을 사용한다.

**단계별 model 오버라이드 (Claude Code 전용)**:

| 모드 | 단계 | model | 근거 |
|------|------|-------|------|
| Full | ANALYSIS | `haiku` | 정보 수집·코드 읽기 중심 |
| Full | PLAN | `sonnet` | 설계, 추론 필요 |
| Full | TODO | `haiku` | 체크리스트 분해, 경량 |
| Full | EXECUTE | `sonnet` | 코드 작성, 고성능 필요 |
| Short | PLAN-SHORT | `sonnet` | 분석+설계 통합 |
| Short | EXECUTE-SHORT | `sonnet` | 코드 작성 |
| Wireframe | WIREFRAME | `sonnet` | wireframe-builder 스킬 실행 |
| Wireframe | EXECUTE-WIREFRAME | `sonnet` | ui-designer 스킬 실행 |

> Cursor, Antigravity에서는 호출 시 model 오버라이드가 불가하므로, 에이전트 파일의 기본 model을 사용한다.

### 워커 결과 수신

워커가 완료되면 아래 형식으로 결과를 반환한다:

- **artifact_path**: 생성/수정한 산출물 경로
- **summary**: 핵심 요약 (3~5줄)
- **status**: `success` | `blocked`
- **blockers**: 블로커 목록 (있는 경우)
- **changed_files**: 변경 파일 목록 (EXECUTE 시)

**성공 시 (status: success)**:
1. 오케스트레이터가 QA 에이전트를 호출 (QA 호출 맵에 따라)
2. QA 결과를 포함하여 사용자에게 보고
3. 사용자 응답에 따라 다음 단계 진행 또는 수정

**블로커 시 (status: blocked)**:
1. 오케스트레이터가 블로커 내용을 사용자에게 중계
2. 사용자 지시에 따라 재개 또는 대응

### 워커 연속성 (Resume)

같은 태스크의 연속 단계에서 이전 워커를 이어서 사용하면 컨텍스트(코드 분석 결과 등)가 보존되어 품질이 향상된다.

**resume 가능 시** (Claude Code, Cursor):
- 동일 워커를 resume하여 다음 단계를 수행
- 추가 전달: "다음 단계는 {단계명}이다. {가이드}.md를 읽고 따르라."

**resume 불가 시** (Gemini CLI, Antigravity, 또는 새 워커):
- 새 워커에 이전 단계 산출물(.md) 경로를 전달
- 워커가 산출물을 Read하여 컨텍스트를 복원

**플랫폼별 resume 지원:**

| 플랫폼 | resume 지원 | 비고 |
|--------|-----------|------|
| Claude Code | O | Agent 도구의 resume 파라미터 |
| Cursor | O | Resume agent {id} |
| Gemini CLI | X | 매 단계 새 워커 |
| Antigravity | X | 폴백: 직접 실행 |

### 크로스 플랫폼 폴백

서브 에이전트 도구(Agent/Task)를 사용할 수 없는 플랫폼에서는, 오케스트레이터가 워커 에이전트 파일을 Read하고 직접 실행한다.

**폴백 규칙**:
1. 서브 에이전트 도구 사용 가능? → 워커 에이전트를 서브 에이전트로 디스패치
2. 사용 불가? → 워커 에이전트 파일을 Read → 지시 내용 확인 → 오케스트레이터가 직접 수행
3. 이 경우 컨텍스트 격리 이점은 없으나, **워커의 절차/규칙은 동일하게 적용**

> references/ 가이드는 실행 주체와 무관하게 동일하게 적용된다. "누가 실행하든" 같은 프로세스를 따른다.

---

## QA 에이전트 호출 규칙

QA가 필요한 단계에서 **오케스트레이터가** QA 에이전트를 **서브 에이전트(Task 도구)** 로 호출한다. 워커는 QA를 호출하지 않는다.

### 모드별 QA 에이전트

| 모드 | QA 에이전트 | 역할 |
|------|-----------|------|
| Full Task | `dtp-qa-dev-agent` | ANALYSIS, PLAN 산출물 검증 |
| Short Task | `dtp-qa-dev-agent` | PLAN 산출물 검증 |
| Wireframe UI | `dtp-qa-wireframe-agent` | wireframe.md 검증 + 빌드/코드 대조 |

### QA 호출 맵

| 단계 | Full Task | Short Task | Wireframe UI |
|------|-----------|------------|-------------|
| TASK | 생략 | 생략 | 생략 |
| ANALYSIS | **dtp-qa-dev-agent** | (해당 없음) | (해당 없음) |
| PLAN | **dtp-qa-dev-agent** | **dtp-qa-dev-agent** | (해당 없음) |
| WIREFRAME | (해당 없음) | (해당 없음) | **dtp-qa-wireframe-agent** |
| TODO | 생략 | (해당 없음) | (해당 없음) |
| EXECUTE | **dtp-dev-test-agent** | **dtp-dev-test-agent** | **dtp-qa-wireframe-agent** |

---

## Planner 에이전트 호출 규칙 (Full Task 복잡 모드 전용)

TODO 워커가 Part A + Part B + 복잡도 판별 결과를 반환하면, **오케스트레이터가** 판정을 확인하고 복잡 모드 시 Planner 에이전트를 호출하여 Part C를 생성한다.

**흐름**: TODO 워커 완료 → 오케스트레이터가 복잡 모드 확인 → Planner 호출 → Part C를 TODO.md에 추가 → 사용자에게 보고

**에이전트 이름**: `dtp-action-plan-agent`

---

## Test 에이전트 호출 규칙 (Full/Short EXECUTE 완료 후)

EXECUTE 워커 완료 후, **오케스트레이터가** Test 에이전트를 호출하여 TEST-SCENARIO.md에 실행 결과를 채운다.

**에이전트 이름**: `dtp-dev-test-agent`

**호출 방법**:
```
1. 에이전트 탐색 경로에서 에이전트 파일을 찾아 Read로 읽는다
2. 서브 에이전트(Task 도구)를 실행한다
3. 전달 정보:
   - task_path: 태스크 폴더 경로
   - scenario_path: TEST-SCENARIO.md 경로
   - changed_files: EXECUTE에서 변경된 파일 목록
   - mode: full-simple / full-complex / short
4. 서브 에이전트가 TEST-SCENARIO.md에 결과를 채우고 판정을 기록한다
```

> Wireframe UI 모드에서는 dtp-dev-test-agent 대신 dtp-qa-wireframe-agent가 빌드/린트 + 대조 검증을 수행한다.

---

## 작업 유형 판별

사용자의 지시를 받으면, 먼저 작업 유형을 판별한다. 유형에 따라 각 단계의 깊이가 달라진다.

| 유형 | 식별 키워드 | ANALYSIS 깊이 (Full) | PLAN 범위 |
|------|-----------|---------------------|----------|
| 🆕 신규 개발 | "새로 만들어", "추가해", "구현해" | 심층 (기술 선택, 아키텍처, 유사 사례) | 전체 설계 |
| 🔧 기능 개선 | "개선해", "최적화", "성능" | 중간 (현재 구현 + 개선 방안) | 변경 범위 특정 |
| 🐛 오류 수정 | "에러", "버그", "안 돼", "오류" | 집중 (원인 분석, 재현 조건) | 수정 포인트만 |
| ✏️ 기능 수정 | "변경해", "바꿔", "수정해" | 중간 (영향 범위 분석) | 변경 + 회귀 테스트 |
| 🎨 UI 구현 | "와이어프레임", "UI", "화면", "프로토타입" | (Wireframe UI 모드) | wireframe.md 기반 |

---

## 산출물 저장 구조

### Full Task

```
tasks/{NNN}-{태스크명}/
├── STATE.md             ← 실시간 상태 추적 (체크포인트)
├── TASK.md              ← 작업 정의서
├── ANALYSIS.md          ← 분석 결과
├── QA-ANALYSIS.md       ← ANALYSIS QA 리뷰
├── PLAN.md              ← 구현 계획
├── QA-PLAN.md           ← PLAN QA 리뷰
├── TODO.md              ← 실행 체크리스트 (+ Part C 복잡 모드)
├── TEST-SCENARIO.md     ← 테스트 시나리오 + 실행 결과 (단일 파일)
├── DONE.md              ← 완료 리포트
└── skills/              ← 동적 생성 스킬 (복잡 모드, 필요 시)
```

### Short Task

```
tasks/{NNN}-{태스크명}/
├── STATE.md             ← 실시간 상태 추적 (체크포인트)
├── TASK.md              ← 작업 정의서
├── PLAN.md              ← 통합 PLAN (코드 분석 + 구현 계획 + 체크리스트)
├── QA-PLAN.md           ← PLAN QA 리뷰
├── TEST-SCENARIO.md     ← 테스트 시나리오 + 실행 결과
└── DONE.md              ← 완료 리포트
```

### Wireframe UI

```
tasks/{NNN}-{태스크명}/
├── STATE.md             ← 실시간 상태 추적
├── TASK.md              ← 작업 정의서 (Wireframe 특화)
├── wireframe.md         ← wireframe-builder 산출물
├── QA-WIREFRAME.md      ← WIREFRAME 단계 QA 리뷰
├── QA-EXECUTE-UI.md     ← EXECUTE 단계 QA 리뷰 (빌드/린트 + 대조)
└── DONE.md              ← 완료 리포트
```

**순번 규칙**:
- 3자리 순번을 태스크명 앞에 붙인다
- 새 태스크 생성 시 `tasks/` 폴더의 기존 최대 번호 + 1
- `tasks/` 폴더가 없거나 비어있으면 001부터 시작

---

## 프로젝트 컨텍스트 로딩

작업 시작 시, 프로젝트의 컨텍스트를 반드시 확인한다:

1. **CLAUDE.md** (또는 프로젝트 설정 파일): 기술 스택, 코드 컨벤션, 아키텍처 규칙
2. **기존 산출물**: 프로젝트에 관련 문서(설계서, 명세서, 정책서 등)가 있으면 참조
3. **기존 코드 패턴**: 프로젝트의 기존 구현이 어떤 패턴을 따르는지 확인

---

## 사전 점검: Git 커밋 확인 (필수)

새 태스크를 시작하기 전에, **반드시** 현재 프로젝트의 미커밋 변경사항을 점검한다.

**점검 절차**:

1. 프로젝트가 git 저장소인지 확인한다 (아니면 스킵)
2. `git status`로 미커밋 변경사항을 확인한다
3. 변경사항이 있으면:
   - 사용자에게 변경 내역을 보고한다
   - 커밋 여부를 확인한다 ("커밋 후 진행할까요?")
   - 사용자가 커밋을 선택하면 커밋 수행
   - 사용자가 스킵을 선택하면 그대로 진행
4. 변경사항이 없으면 바로 STEP 1로 진행한다

> ⚠️ 미커밋 변경사항이 있는 상태에서 STEP 1을 시작하려면, 반드시 사용자의 명시적 확인을 받아야 한다.

---

## STEP 1: TASK (작업 정의) — 모든 모드 공통

사용자의 지시를 구조화된 작업 정의서로 정리한다.

### TASK.md 작성 항목 (Full/Short)

```markdown
# TASK: {태스크 제목}

> 작성일: YYYY-MM-DD | 작업 유형: {신규/개선/수정/오류}

## 작업 목표
{사용자의 지시를 한 문장으로 요약}

## 배경
{왜 이 작업이 필요한지}

## 요구사항
- [ ] {구체적 요구사항 1}
- [ ] {구체적 요구사항 2}

## 제약 조건
{기술적/비즈니스 제약사항}

## 관련 문서
{참조할 기존 산출물 경로}
```

### TASK.md 작성 항목 (Wireframe UI)

Wireframe UI 모드의 TASK.md는 `references/wireframe-task-guide.md`를 참조한다.

### 작업 정의 시 확인 사항

사용자의 지시가 모호하거나 빠진 부분이 있으면 **먼저 질문한다**. 추측하지 않는다.

### 모드 판별 및 보고

TASK.md 작성 완료 후:
1. 모드 판별 규칙에 따라 Full/Short/Wireframe UI를 판별한다
2. 사용자에게 보고한다:

```
📋 [TASK] 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/TASK.md

💡 모드 제안: {Short Task / Full Task / Wireframe UI}
   근거: {조건 충족/미충족 요약}

다음 단계로 넘어갈까요? (모드 변경도 가능합니다)
```

3. 사용자 응답에 따라:
   - 승인 → 해당 모드의 다음 단계 진행
   - 모드 변경 요청 → 변경된 모드로 진행
   - 피드백 → TASK.md 수정 후 재보고

---

## 모드별 파이프라인 → modes/ 파일로 위임

TASK 이후의 각 모드별 단계는 별도 파일에 정의되어 있다. 오케스트레이터는 모드 판별 후 해당 파일을 Read하여 파이프라인을 실행한다.

### Full Task

**파이프라인 파일**: `modes/dev-full.md`

```
TASK → ANALYSIS → PLAN → TODO → TEST-SCENARIO → EXECUTE
```

### Short Task

**파이프라인 파일**: `modes/dev-short.md`

```
TASK → PLAN(통합) → TEST-SCENARIO → EXECUTE
```

### Wireframe UI

**파이프라인 파일**: `modes/wireframe-ui.md`

```
TASK → WIREFRAME → EXECUTE → QA
```

---

## 완료 리포트 (DONE.md) 생성 규칙

### 생성 시점
모든 모드에서 최종 검증 완료 후, 완료 보고 직전에 생성한다.

### 생성 주체
**오케스트레이터**가 생성한다.

### 저장 경로
`tasks/{NNN}-{태스크명}/DONE.md`

### DONE.md 템플릿

```markdown
# DONE: {태스크 제목}

> 완료일: YYYY-MM-DD | 모드: {Full Task / Short Task / Wireframe UI} | 작업 유형: {신규/개선/수정/오류/Wireframe UI}

## 완료 요약
{작업 결과를 1~3문장으로 요약}

## 변경 파일
| # | 파일 | 변경 내용 |
|---|------|----------|

## 핵심 변경 사항
### Before
{변경 전 상태/동작}
### After
{변경 후 상태/동작}

## 테스트 결과
{TEST-SCENARIO.md 판정 또는 QA-EXECUTE-UI.md 판정}

## 산출물 목록
| 파일 | 설명 |
|------|------|
```

---

## STATE.md 체크포인트 시스템

태스크별 STATE.md를 통해 실시간 상태를 추적하고, 토큰 리밋 등으로 컨텍스트가 유실되어도 정확한 지점에서 작업을 재개할 수 있다.

### STATE.md 템플릿

```markdown
# STATE: {태스크 제목}

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: {Full Task / Short Task / Wireframe UI}
- 단계: {TASK / ANALYSIS / PLAN / TODO / WIREFRAME / EXECUTE}
- 진행: {Step N/M 완료 (EXECUTE 시) / 완료 (비-EXECUTE 시)}
- 상태: {진행 중 / 대기 중 / 블로커 / 완료}

## 완료 산출물
| 산출물 | 상태 |
|--------|------|
| TASK.md | {완료 / 미생성} |
| ANALYSIS.md | {완료 / 미생성 / 해당없음} |
| PLAN.md | {완료 / 진행 중 / 미생성 / 해당없음} |
| TODO.md | {완료 / 미생성 / 해당없음} |
| wireframe.md | {완료 / 미생성 / 해당없음} |
| QA-*.md | {완료 / 미생성} |
| DONE.md | {완료 / 미생성} |

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 사용자 지시 (미반영)
{산출물에 아직 반영되지 않은 사용자 피드백/수정 지시}

## 블로커
{현재 블로커 상황 또는 "없음"}

## 다음 액션
{다음으로 수행할 작업}
```

### STATE.md 갱신 규칙

**갱신 주체**: 오케스트레이터 + 워커 (역할 분담)

| 이벤트 | 갱신 주체 | 갱신 내용 |
|--------|----------|----------|
| 태스크 생성 (TASK.md 작성 후) | 오케스트레이터 | STATE.md 초기 생성 |
| 단계 시작 (워커 디스패치) | 오케스트레이터 | `단계`, `상태: 진행 중` 갱신 |
| 단계 완료 (워커 반환) | 오케스트레이터 | `완료 산출물` 테이블 갱신, `상태: 대기 중` |
| EXECUTE Step 완료 | 워커 | `진행: Step N/M 완료` 갱신 |
| 의사결정 발생 | 오케스트레이터/워커 | `의사결정 로그` 행 추가 |
| 블로커 발생 | 워커 | `상태: 블로커`, `블로커` 섹션 갱신 |
| 사용자 피드백 (미반영) | 오케스트레이터 | `사용자 지시 (미반영)` 섹션 갱신 |
| QA 완료 | 오케스트레이터 | `완료 산출물`에 QA 상태 추가 |
| DONE.md 생성 | 오케스트레이터 | `상태: 완료`, 전체 갱신 |

### STATE.md 복원 프로토콜

새 세션에서 태스크를 이어서 수행할 때 STATE.md를 활용한다:

1. `tasks/{NNN}-{name}/STATE.md` 존재 확인
2. **존재 시**: STATE.md Read → 현재 상태/단계/진행 파악 → 정확한 지점에서 재개
3. **미존재 시**: 기존 방식(산출물 존재 여부)으로 마지막 완료 단계 추론 → STATE.md 생성
4. 복원 내용을 사용자에게 보고:

```
📋 태스크 복원: {태스크명}
   단계: {단계} | 진행: {Step N/M} | 상태: {상태}
   미반영 지시: {있음/없음}
   이어서 진행할까요?
```

---

## 게이트 체크포인트 규칙

### QA가 있는 단계

```
📋 [{단계명}] 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/{단계}.md
📎 QA 리뷰: tasks/{NNN}-{태스크명}/QA-{단계}.md

[QA 요약]
- 검증 항목 {N}개 중 {통과}개 Pass, {경고}개 Warning
- {주요 지적 사항 요약}
- 판정: {✅ Pass / ⚠️ Needs Revision}

다음 단계({다음 단계명})로 넘어갈까요?
```

### QA가 없는 단계

```
📋 [{단계명}] 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/{단계}.md
{모드 제안 — TASK 단계 시}

다음 단계({다음 단계명})로 넘어갈까요?
```

### 사용자 응답 패턴

- **"확인", "다음", "넘어가", "승인"** → 다음 단계 진행
- **피드백/수정 요청** → 현재 단계 산출물 수정 후 재보고
- **"중단", "보류"** → 현재까지 산출물 저장하고 대기
- **모드 변경 요청** → 해당 모드로 전환

---

## 다중 태스크 실행

오케스트레이터-워커 모델을 활용하면, 여러 태스크를 동시에 진행할 수 있다.

### 동시 실행 모델

- 알투가 태스크 A의 사용자 검토 대기 중에 태스크 B의 워커를 디스패치할 수 있다
- 각 워커는 독립 컨텍스트에서 실행되므로, 태스크 간 간섭이 없다
- Claude Code에서는 `run_in_background` 를 활용하여 워커를 백그라운드로 실행 가능

### 태스크 상태 추적

오케스트레이터는 각 태스크의 상태를 STATE.md를 통해 추적한다. STATE.md가 없으면 `tasks/` 폴더의 산출물 존재 여부로 상태를 추론한다 (폴백).

### 파일 충돌 경고

여러 태스크의 EXECUTE 워커가 같은 파일을 수정하려 할 때, 오케스트레이터가 경고한다.

---

## 실행 모드 예시

### Full Task
```
사용자: "새 태스크: 사용자 인증 기능 개발"
→ TASK(직접) → (검토) → [dtp-dev-agent: ANALYSIS] → QA → (검토)
→ [dtp-dev-agent: PLAN] → QA → (검토) → [dtp-dev-agent: TODO] → (승인)
→ [dtp-dev-agent: TEST-SCENARIO] → (검토/승인) → [dtp-dev-agent: EXECUTE] → [dtp-dev-test-agent] → 완료
```

### Short Task
```
사용자: "버그 수정: 로그인 시 토큰 만료 에러"
→ TASK(직접) → (검토) → [dtp-dev-agent: PLAN 통합] → QA → (검토)
→ [dtp-dev-agent: TEST-SCENARIO] → (검토/승인) → [dtp-dev-agent: EXECUTE] → [dtp-dev-test-agent] → 완료
```

### Wireframe UI
```
사용자: "대시보드 UI 만들어줘" + 정책서.md 제공
→ TASK(직접, wireframe-task-guide 참조) → (검토)
→ [dtp-wireframe-ui-agent: WIREFRAME] → [dtp-qa-wireframe-agent] → (검토)
→ [dtp-wireframe-ui-agent: EXECUTE] → [dtp-qa-wireframe-agent] → 완료
```

### 이어하기
```
사용자: "인증 기능 작업 이어서 해줘"
→ tasks/{NNN}-{태스크명}/STATE.md 확인
  → 존재 시: STATE.md Read → 단계/진행/블로커/미반영 지시 파악 → 정확한 지점에서 재개
  → 미존재 시: 산출물 존재 여부로 마지막 완료 단계 추론 → STATE.md 생성 → 다음 단계부터 재개
```
