# 코드 컨벤션

> OPAL 프레임워크 작성 규칙

## 언어 규칙

| 대상 | 규칙 |
|------|------|
| 문서 본문 | 한국어 (기술 용어는 영어 병기) |
| 코드/변수/필드명 | English |
| YAML frontmatter 키 | English |
| 파일/폴더 이름 | English, kebab-case |

## 네이밍 규칙

### 파일/폴더

- **kebab-case** 사용: `user-auth-implementation`, `op-dev-plan`
- 스킬 폴더: `{그룹}-{역할}` — `opal-pilot-dev`, `op-dev-analysis`, `op-task-qa`
- 에이전트 폴더: `{대상 워크플로우}-{역할}` — `opal-task-agent`, `opal-task-qa-agent`, `wtm-agent`
- 태스크 폴더: `{NNN}-{스킬약어 또는 대상}-{동작/설명}` — `055-opi-task-record`, `052-orchestrator-cleanup`
- SDD 명세 폴더: `specs/{NNN}-{feature-name}/` — 순번 3자리 0-패딩, kebab-case

### 컴포넌트 네이밍 체계

| 접두사 | 의미 | 예시 |
|--------|------|------|
| `opal-pilot-*` | 오케스트레이터 | opal-pilot-dev, opal-pilot-write-tech, opal-pilot-project |
| `op-dev-*` | dev 도메인 단계 스킬 | op-dev-analysis, op-dev-plan, op-dev-qa |
| `op-task-*` | 범용 단계 스킬 | op-task, op-task-qa, op-task-plan, op-task-execute |
| `opal-task-*` | 범용 워커 에이전트 | opal-task-agent |
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
agents/{agent-name}/
└── AGENT.md              필수 — YAML frontmatter + 입출력 명세 + 실행 프로세스
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
