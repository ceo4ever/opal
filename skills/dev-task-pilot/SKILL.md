---
name: dev-task-pilot
description: |
  코드 작성·수정이 수반되는 모든 개발 작업의 워크플로우 오케스트레이터.
  버그 수정, 기능 추가/수정/개선, 성능 최적화, 리팩토링, UI 구현,
  와이어프레임 설계 등 실제 코드 변경이 필요한 작업에 사용한다.
  코드를 읽기만 하는 설명 요청, API 명세서 작성(api-analyzer),
  문서 작성(doc-writer), PR 리뷰(code-review), git 작업,
  단순 설정 1줄 변경은 이 스킬이 아니다.
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

모든 작업은 Short Task로 시작한다. Short Task는 단계를 줄여 속도를 높이는 것이지, 분석 품질을 낮추는 것이 아니다. 대부분의 개발 작업은 별도 ANALYSIS 단계 없이 PLAN에서 분석과 설계를 통합해도 충분하며, 불필요한 단계는 오히려 사용자의 시간을 낭비한다.

### Wireframe UI 트리거 조건

사용자가 **"와이어프레임"을 명시적으로 언급**한 경우에만 적용한다.
"화면 구현", "UI 만들어줘", "화면 수정" 등은 Wireframe UI가 **아니다** — Short/Full Task에서 ui-designer plan-driven 모드로 수행한다.

| # | 조건 | 판별 방법 |
|---|------|----------|
| 1 | 사용자가 "와이어프레임" 언급 | "와이어프레임 만들어줘", "wireframe", "와이어프레임으로 해줘" |
| 2 | wireframe.md 제공 | wireframe.md가 입력물로 제공됨 |

**그 외 모든 FE/UI 작업은 Short/Full Task**:

| 상황 | 모드 | UI 구현 방법 |
|------|------|------------|
| 기존 프로젝트에 화면 추가 | Short/Full Task | EXECUTE에서 ui-designer plan-driven 모드 |
| 기존 화면 UI 수정 | Short/Full Task | EXECUTE에서 ui-designer plan-driven 모드 |
| API + 화면 동시 개발 | Short/Full Task | FE/BE 병렬 — FE는 ui-designer, BE는 직접 구현 |
| 와이어프레임부터 설계 | Wireframe UI | wireframe-builder → ui-designer scaffold 모드 |

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

> **주의**: "화면 수정해줘", "UI 고쳐줘", "컴포넌트 추가해줘" 같은 요청은 **기존 프로젝트 작업**이므로 Wireframe UI가 아니라 **Short/Full Task**로 진행한다. EXECUTE에서 ui-designer plan-driven 모드가 FE 화면 작업을 담당한다.

### 에스컬레이션 규칙

Short Task 진행 중 PLAN 작성 시 Full Task 조건에 해당하는 상황이 발견될 수 있다. 이때 Short Task로 억지로 진행하면 분석 누락으로 EXECUTE에서 재작업이 발생하므로, 조기에 Full Task로 전환하는 것이 전체 비용을 줄인다.
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

### 워커 연속성 & 크로스 플랫폼 폴백

같은 태스크의 연속 단계에서 이전 워커를 resume하면 컨텍스트가 보존되어 품질이 향상된다. resume이 가능한 플랫폼(Claude Code, Cursor)에서는 동일 워커를 이어서 사용하고, 불가능한 플랫폼(Gemini CLI 등)에서는 새 워커에 이전 산출물 경로를 전달하여 컨텍스트를 복원한다.

서브 에이전트 도구 자체를 사용할 수 없는 플랫폼에서는 오케스트레이터가 워커 에이전트 파일을 Read하고 직접 수행한다. 이 경우에도 워커의 절차/규칙은 동일하게 적용된다.

---

## QA 에이전트 호출 규칙

QA가 필요한 단계에서 **오케스트레이터가** QA 에이전트를 **서브 에이전트(Task 도구)** 로 호출한다. 워커는 QA를 호출하지 않는다. 워커가 자기 산출물을 스스로 검증하면 편향이 생기므로, 독립된 QA 에이전트가 별도 컨텍스트에서 검증해야 객관성이 보장된다.

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

**전달 정보**: task_path, scenario_path(TEST-SCENARIO.md), changed_files, mode(full-simple/full-complex/short). Wireframe UI에서는 dtp-qa-wireframe-agent가 빌드/린트 + 대조 검증을 수행한다.

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
├── execution-plan.json  ← 실행 계획 (PLAN에서 생성, FE/BE 작업 시)
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
├── execution-plan.json  ← 실행 계획 (PLAN에서 생성, FE/BE 작업 시)
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

프로젝트의 기존 패턴을 모르고 작업하면, 기존 코드와 일관성 없는 구현이 나온다. 컨벤션 위반, 중복 코드, 아키텍처 불일치 등이 EXECUTE 단계에서야 발견되면 전체 재작업으로 이어질 수 있다. 작업 시작 시 반드시 확인한다:

1. **CLAUDE.md** (또는 프로젝트 설정 파일): 기술 스택, 코드 컨벤션, 아키텍처 규칙
2. **기존 산출물**: 프로젝트에 관련 문서(설계서, 명세서, 정책서 등)가 있으면 참조
3. **기존 코드 패턴**: 프로젝트의 기존 구현이 어떤 패턴을 따르는지 확인
4. **기술 스택 사전 판별**: TASK 단계에서 프로젝트 기술 스택을 빠르게 파악한다
   - `package.json` (Node.js/React/Next.js), `pyproject.toml` (Python/FastAPI), `go.mod`, `pom.xml`, `Cargo.toml`
   - `~/.opal/references/skills.md`의 "기술 스택별 추천 스킬" 참조
   - 판별 결과를 TASK.md에 "기술 스택" 필드로 기록

---

## 프로세스 변경 정책

일회성 지시를 영구 정책으로 오해하면 프로세스가 점진적으로 무너진다. 반대로 영구 변경을 매번 다시 지시하게 만들면 사용자가 불편하다. 이 두 가지를 명확히 구분한다.

- **일회성 변경은 해당 태스크에만 적용**: 소유자가 QA 생략, 테스트 생략, 단계 축소 등을 지시하면 현재 태스크에만 적용한다. 다음 태스크는 기본 프로세스(모드별 전체 파이프라인)로 복귀한다.
- **영구 변경은 명시적 지시 필요**: "앞으로 항상", "모든 태스크에" 등의 표현이 있을 때만 영구 정책으로 반영한다.

---

## 사전 점검: Git 커밋 확인 (필수)

새 태스크를 시작하기 전에, **반드시** 현재 프로젝트의 미커밋 변경사항을 점검한다. 미커밋 변경이 있는 상태에서 새 작업을 시작하면, 이전 작업과 새 작업의 변경사항이 섞여 롤백이 어려워진다.

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

## 완료 리포트 & 게이트 체크포인트

DONE.md 생성 규칙, 단계별 보고 형식, 사용자 응답 처리는 `references/checkpoint-guide.md`를 참조한다.

---

## STATE.md 체크포인트 시스템

태스크별 STATE.md로 실시간 상태를 추적하여, 컨텍스트 유실 시에도 정확한 지점에서 재개할 수 있다. 템플릿, 갱신 규칙, 복원 프로토콜은 `references/state-guide.md`를 참조한다.

---

## 다중 태스크 실행

오케스트레이터가 태스크 A의 사용자 검토 대기 중에 태스크 B의 워커를 디스패치할 수 있다. 각 워커는 독립 컨텍스트에서 실행되므로 태스크 간 간섭이 없다. 여러 EXECUTE 워커가 같은 파일을 수정하려 할 때는 오케스트레이터가 경고한다.
