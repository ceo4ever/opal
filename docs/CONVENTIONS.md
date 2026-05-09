# 코드 컨벤션

> OPAL 프레임워크 작성 규칙

## 언어 규칙

| 대상 | 규칙 |
|------|------|
| 문서 본문 | 한국어 (기술 용어는 영어 병기) |
| 코드/변수/필드명 | English |
| YAML frontmatter 키 | English |
| 파일/폴더 이름 | English, kebab-case (Python 파일은 snake_case) |

## 네이밍 규칙

### 파일/폴더

- **kebab-case** 사용: `user-auth-implementation`, `op-dev-plan` (Python 파일은 **snake_case**: `creative_response.py`, `user_auth.py`)
- 스킬 폴더: `{그룹}-{역할}` — `opal-pilot-dev`, `op-dev-analysis`, `op-task-qa`
- OPAL 에이전트 폴더: `opal/agents/{agent-name}/` — `opal-task-agent`, `opal-fe-agent`, `opal-be-agent`, `opal-plan-agent`, `opal-test-agent`, `opal-planning-agent`, `opal-db-agent`
- 범용 에이전트 폴더: `agents/{agent-name}/` — `wtm-agent` (OPAL 무관)
- 전문 에이전트 네이밍: `opal-{domain}-agent` — `opal-fe-agent`, `opal-be-agent`, `opal-db-agent`
- 태스크 폴더: `{NNN}-{스킬약어 또는 대상}-{동작/설명}` — `055-opi-task-record`, `052-orchestrator-cleanup`
- SDD 명세 폴더: `specs/{NNN}-{feature-name}/` — 순번 3자리 0-패딩, kebab-case

### 컴포넌트 네이밍 체계

| 접두사 | 의미 | 예시 |
|--------|------|------|
| `opal-pilot-*` | 오케스트레이터 | opal-pilot-dev, opal-pilot-write-tech, opal-pilot-project |
| `op-dev-*` | dev 도메인 단계 스킬 | op-dev-analysis, op-dev-plan, op-dev-qa |
| `op-task-*` | 범용 단계 스킬 | op-task, op-task-qa, op-task-plan, op-task-execute |
| `opal-task-*` | 범용 워커 에이전트 | opal-task-agent |
| `opal-{domain}-agent` | 전문 워커 에이전트 | opal-fe-agent, opal-be-agent, opal-db-agent, opal-plan-agent, opal-test-agent, opal-planning-agent |
| `op-sdd-*` | SDD 단계 스킬 | op-sdd-spec, op-sdd-verify, op-sdd-plan, op-sdd-tasks |
| `opal-*` | OPAL 프레임워크 전용 | opal-project-init, opal-onboarding |

### 약어 (Alias)

| 약어 | 풀네임 |
|------|--------|
| opd | opal-pilot-dev |
| opds | opal-pilot-dev-short |
| opdw | opal-pilot-dev-wireframe |
| opwt | opal-pilot-write-tech |
| opp | opal-pilot-project |
| oppd | opal-pilot-project-dev |
| opi | opal-project-init |
| opsdd | opal-pilot-sdd |

## 파일 구조

### 스킬 구조

```
skills/{skill-name}/
├── SKILL.md              필수 — YAML frontmatter + 프로세스 정의
├── references/           선택 — 상세 가이드 (참조 문서)
│   └── {guide-name}.md
└── personas/             선택 — 페르소나 정의
    └── {persona-name}.md
```

### 에이전트 구조

```
opal/agents/{agent-name}/    OPAL 전용 에이전트 (전문 + 범용)
└── AGENT.md                 필수 — YAML frontmatter + 입출력 명세 + 실행 프로세스

agents/{agent-name}/          범용 에이전트 (OPAL 무관)
└── AGENT.md
```

### YAML Frontmatter

스킬과 에이전트 모두 YAML frontmatter를 포함한다:

```yaml
---
name: {컴포넌트 이름}
description: |
  {설명 — 트리거 키워드 포함}
triggers:             # 스킬만
  - "{트리거 문구}"
version: {X.Y.Z}     # 스킬만
model: {모델}         # 에이전트만
icon: {이모지}         # 에이전트만 (선택, 디폴트: ✨)
---
```

### 변경이력

스킬, 에이전트, 참조 문서의 변경이력은 일시(KST)를 포함한다:

```markdown
## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-30 14:00 | 초기 작성 |
```

- 일시 형식: `YYYY-MM-DD HH:mm` (KST 기준)
- 버전: semver (`vX.Y.Z`)

### 태스크 산출물 구조

```
tasks/{NNN}-{설명}/
├── TASK.md               요구사항 정의
├── ANALYSIS.md           코드베이스 분석 (Full Task)
├── PLAN.md               구현 계획
├── TEST-SCENARIO.md      테스트 시나리오
├── STATE.md              상태 관리
└── DONE.md               완료 보고
```

## 브랜치 전략

- `main`: 안정 브랜치
- `new-dtp-*`: 기능 개발 브랜치 (태스크 단위)
- 태스크 완료 후 main에 머지

## 커밋 규칙

### 형식

```
{type}({scope}): {한국어 설명}
```

### Type

| type | 용도 |
|------|------|
| feat | 새 스킬, 에이전트, 기능 추가 |
| fix | 버그 수정 |
| refactor | 리팩토링 (동작 변경 없음) |
| chore | 메모리 정리, 설정 변경 등 |
| docs | 문서만 변경 |

### Scope

태스크 번호 사용: `feat(043): opal-doc-standard v2.0`

### 규칙

- 커밋은 캡틴이 명시적으로 요청할 때만 수행
- 커밋 메시지는 한국어
- 하나의 태스크 = 하나의 커밋 (원칙)

## 구현 규칙

OPAL 본체(스킬·에이전트·도구·하네스)를 작성할 때 따라야 할 규칙. 워커가 코드/문서를 작성할 때 이 절을 직접 참조한다.

### Guards (구현 금지·승인 게이트)

- 사용자가 명시적으로 "승인", "진행해", "구현해" 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다.
  - 허용: 산출물 문서(.md) 작성, QA 에이전트 호출, 코드베이스 읽기·분석
  - 금지(승인 전): 소스 코드 파일 생성·수정, 패키지 설치, 설정 파일 수정
- CLOSE 단계 진입 직전에는 사용자의 명시적 확인(`승인`/`확인`/`확인완료`)이 반드시 있어야 한다 (agentic/semi-agentic 모드에서도 유지).
- 커밋은 사용자가 명시적으로 요청할 때만 수행한다 — EXECUTE 완료·DONE.md 생성·테스트 통과 후에도 자동 커밋 금지.
- 근거: `opal/core/references/opal-harness.md` §1 Guards

### 디스패치 의무

- 오케스트레이터 SKILL.md에서 "워커 디스패치"로 정의된 단계(ANALYSIS/PLAN/EXECUTE 등)는 반드시 서브에이전트를 디스패치한다. PM이 직접 실행으로 대체하지 않는다.
- 근거: `opal/core/references/opal-harness.md` §1 디스패치 의무 원칙

### @header 규칙

- 코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다 (해당 확장자에 한해).
- 변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 헤더 내 변경이력 라인으로 갱신한다.
- 근거: `opal/core/references/harness/header-rules.md`

### Citation Rules (인용)

- TASK.md / PLAN.md / ANALYSIS.md / QA 산출물 등을 작성할 때 모든 주장은 근거를 인용한다 (`{경로}:{라인}` 또는 `docs/문서명 §섹션`).
- `[MUST]` 토큰이 붙은 항목은 인용 누락 시 산출물 부적합 처리.
- 근거: `opal/core/references/harness/citation-rules.md`

### State 관리

- 파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. 마크다운 표 직접 편집 금지.
- 단계 진입/완료/Gate 통과/추가작업 행 삽입 모두 state-tool 서브 명령(`init`/`advance`/`mark`/`gate-pass`/`add-row` 등)으로 처리한다.
- 근거: `opal/core/references/opal-harness.md` §3 State

### 도구 우선 원칙

- 파일 처리·데이터 변환 작업이 필요할 때, 직접 코드를 작성하기 전에 OPAL 도구(`~/.opal/tools/`)를 우선 검토한다.
- 등록 도구 예: `xlsx-tool`, `state-tool`, `skill-registry`, `playwright-tool`.
- 근거: `opal/core/references/opal-harness.md` §9 OPAL Tools

### 변경이력 작성 의무

- 스킬·에이전트·참조 문서를 변경하면 "## 변경이력" 표에 행을 추가한다.
- 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(138)`.
- 배포 시 `install-mac.sh`가 변경이력 섹션을 자동 strip 한다 (소스에는 유지, 배포본에서는 제거).

### 배포 경계

- `~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다.
- 변경 후 `./scripts/install-mac.sh`(또는 후속 `opal install`)로 재배포하여 검증한다.

### 플랫폼 분기 격리

- Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층(부트스트래퍼·`emit_platform_agent_adapter`·MCP install 분기)에서만 흡수한다.
- 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다 (행위는 플랫폼 독립적으로 기술하고, 도구명은 어댑터에 위임).

---

> **참고 — 허브+링크 모델**
> OPAL 프레임워크 자체는 단일 `docs/CONVENTIONS.md`를 사용한다(단일 진입점).
> 다중 구성(FE/BE/Batch/Mobile 등) 프로젝트는 허브+링크 모델 적용 가능 —
> 영역별 상세 문서(`FE-CONVENTIONS.md`, `BE-CONVENTIONS.md` 등)를 분리하고 본 허브에서 링크로 연결한다.
> 규약: `opal/core/references/conventions-hub-model.md` 참조.
