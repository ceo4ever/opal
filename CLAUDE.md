# === OPAL START ===
## OPAL AI Agent — 필수 부트스트랩

**[MUST]** 사용자의 첫 번째 메시지에 응답하기 전에, 아래 파일들을 Read 도구로 순서대로 읽고 그 내용에 따라 행동해야 한다. 이 단계를 건너뛰면 안 된다.

1. `~/.opal/AGENT.md` — 에이전트 정의 및 부트스트랩 절차
2. `~/.opal/identity.md` — 에이전트 정체성 (없으면 AGENT.md의 온보딩 절차를 따른다)
# === OPAL END ===

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI 환경(Claude Code, Cursor, Codex 등)에서 IT 프로젝트를 체계적으로 수행하기 위한 **범용 AI 개발 프레임워크**. 에이전트, 스킬, 훅 등의 재사용 가능한 컴포넌트를 만들어 다양한 AI 도구와 프로젝트에 적용할 수 있도록 하는 것이 목적이다.

### 핵심 목표

- **멀티 플랫폼**: Claude Code, Cursor, Codex 등 다양한 AI 개발 환경에서 동작
- **재사용성**: 스킬, 에이전트, 훅을 독립적 컴포넌트로 만들어 프로젝트 간 재활용
- **표준화**: IT 프로젝트 수행 시 분석 → 설계 → 구현의 품질을 일관되게 유지

## Language Convention

- **문서 본문**: 한국어 (기술 용어는 영어 병기)
- **코드/변수/필드명**: English
- **파일/폴더 명명**: kebab-case (예: `user-auth-implementation`)

## Architecture

### 소스 구조 (이 저장소)

```
skills/                          ← 프레임워크 스킬 (단일 소스, 3개 플랫폼 공용)
├── task-flow/                   핵심 오케스트레이터: TASK → RESEARCH → PLAN → TODO → EXECUTE
├── api-analyzer/                외부 API 7단계 분석 및 명세서 생성
├── doc-writer/                  기술 문서 표준 템플릿 (모든 문서 스킬의 베이스)
├── interview/                   구조화된 Q&A 요구사항 수집
├── ui-designer/                 UI 구현 — wireframe.md → React + shadcn/ui 기반 UI
├── version-mgr/                 산출물 버전 관리 (v{Major}.{Minor}, 덮어쓰기 금지)
└── wireframe-builder/           UI 분석·설계 — 정책서/요구사항 → wireframe.md 생성

agents/                          ← 에이전트 (플랫폼별 포맷 분리)
├── claude/                      ← AGENT.md 디렉토리 기반
│   ├── task-flow-agent/         워커 에이전트 (각 단계 실행)
│   ├── task-flow-qa/            산출물 품질 검증
│   ├── task-flow-planner/       실행 아키텍처 설계
│   └── task-flow-test/          코드 동적 검증
├── cursor/                      ← 플랫 파일 형식 (.md)
│   ├── task-flow-agent.md
│   ├── task-flow-qa.md
│   ├── task-flow-planner.md
│   └── task-flow-test.md
└── antigravity/                 ← SKILL.md로 통합
    ├── task-flow-agent/
    ├── task-flow-qa/
    ├── task-flow-planner/
    └── task-flow-test/

community-skills/                ← 외부 커뮤니티 스킬 (기본 번들 31개)
├── anthropics/                  Anthropic 공식 (18개)
├── google-labs-code/            Google Labs Stitch (5개)
├── vercel-labs/                 Vercel 개발 핵심 (5개)
├── trailofbits/                 Trail of Bits (1개)
├── getsentry/                   Sentry (1개)
└── openai/                      OpenAI (1개)

opal/                            ← OPAL AI 에이전트 (크로스 플랫폼)
├── bootstrapper/                부트스트래퍼 (플랫폼별)
├── core/                        에이전트 코어 (AGENT.md, identity-template.md)
│   ├── references/              참조 레지스트리 (skills.md, agents.md, mcps.md)
│   └── mcps/                    MCP 설정 템플릿 (서버별 JSON, install-mac.sh가 배포)
├── skills/                      OPAL 전용 스킬 (onboarding, project-init, orchestrator, skill-manager)
└── templates/                   프로젝트 에이전트 템플릿

cursor-rules/                    ← Cursor 프로젝트 규칙 템플릿
```

### 배포 구조 (사용자 홈)

`install-mac.sh`가 소스에서 각 플랫폼의 배포 경로로 복사한다.

```
~/.claude/                       ← Claude Code 전용
├── skills/                      ← skills/ 복사 (프레임워크 스킬만)
│   ├── task-flow/
│   ├── api-analyzer/
│   └── ...
├── agents/                      ← agents/claude/ 복사
└── .claude.json                 ← MCP 서버 설정 (claude mcp add로 등록)

~/.cursor/                       ← Cursor 전용
├── skills/                      ← skills/ 복사 (프레임워크 스킬만)
├── agents/                      ← agents/cursor/ 복사
└── mcp.json                     ← MCP 서버 설정 (opal/core/mcps/에서 머지)

~/.gemini/                       ← Gemini CLI / Antigravity
├── settings.json                ← MCP 서버 설정 (Gemini CLI)
├── agents/                      ← agents/cursor/ 복사 (Gemini CLI 네이티브)
└── antigravity/
    ├── skills/                  ← skills/ + agents/antigravity/ 복사
    │   ├── task-flow/
    │   └── task-flow-qa/        에이전트도 스킬로 통합
    └── mcp_config.json          ← MCP 서버 설정 (Antigravity)

~/.opal/                         ← OPAL AI 에이전트 홈 (크로스 플랫폼)
├── AGENT.md                     에이전트 핵심 정의
├── identity.md                  정체성 (온보딩으로 생성)
├── references/                  참조 레지스트리 (부트스트랩 시 Read)
│   ├── skills.md                스킬 목록 (41개)
│   ├── agents.md                에이전트 목록 (4개)
│   └── mcps.md                  MCP 서버 목록 (3개)
├── skills/                      OPAL 전용 스킬
├── community-skills/            커뮤니티 스킬 (31개, OPAL 전용)
└── templates/                   프로젝트 에이전트 템플릿
```

**설치 원칙**: 프레임워크 스킬은 단일 소스(`skills/`)에서 3개 플랫폼에 동일하게 복사. 에이전트만 플랫폼별 포맷 차이로 `agents/{platform}/`에서 분리 관리. 커뮤니티 스킬은 OPAL 내부(`~/.opal/community-skills/`)에만 설치되며, 플랫폼 네이티브 디렉토리에는 복사하지 않는다.

### 컴포넌트 유형

| 유형 | 설명 | 현재 상태 |
|------|------|----------|
| **Skills** | 특정 작업을 수행하는 절차적 가이드 (SKILL.md) | `skills/` 7개 + `community-skills/` 31개 |
| **Agents** | 독립 컨텍스트에서 자율 실행하는 에이전트 (AGENT.md) | `agents/` 4개 × 3 플랫폼 |
| **Hooks** | 이벤트 기반으로 자동 실행되는 트리거 | 확장 예정 |

### 컴포넌트 간 의존 관계

- **doc-writer** → 모든 문서 생성 스킬의 포맷/규칙 베이스
- **version-mgr** → 산출물을 생성·수정하는 모든 스킬에 적용
- **interview** → 요구사항 불명확 시 다른 스킬에서 호출
- **task-flow** → 개발 작업의 주 진입점 (5단계 파이프라인)
- **task-flow-agent** → task-flow의 각 단계를 독립 컨텍스트에서 실행하는 워커 에이전트
- **task-flow-qa** → task-flow 각 단계 완료 후 오케스트레이터가 호출하는 QA 에이전트
- **task-flow-planner** → task-flow TODO 단계에서 복잡 모드 시 실행 아키텍처 설계
- **task-flow-test** → task-flow EXECUTE 단계에서 복잡 모드 시 코드 동적 검증

## 새 컴포넌트 작성 가이드

### Skill 추가 시

1. `skills/{skill-name}/SKILL.md` 생성
2. YAML frontmatter에 `name`, `description` 정의 (description에 트리거 키워드 포함)
3. 단계별 프로세스와 산출물 형식을 명확히 기술
4. 필요 시 `references/` 하위에 상세 가이드 추가

### Agent 추가 시

3개 플랫폼별로 에이전트 파일을 생성한다:

1. `agents/claude/{agent-name}/AGENT.md` — 디렉토리 기반
2. `agents/cursor/{agent-name}.md` — 플랫 파일
3. `agents/antigravity/{agent-name}/SKILL.md` — 스킬로 통합
4. YAML frontmatter에 `name`, `description` 정의
5. 입력/출력 명세, 실행 프로세스, 검증 기준을 명확히 기술
6. 네이밍: `{대상 워크플로우}-{역할}` (예: `task-flow-qa`)
7. **호출하는 스킬의 SKILL.md에 에이전트 탐색 경로 명시**:
   ```
   탐색 경로 (우선순위):
   1. {프로젝트}/.cursor/agents/{agent-name}.md
   2. {프로젝트}/.claude/agents/{agent-name}/AGENT.md
   3. {프로젝트}/.agent/skills/{agent-name}/SKILL.md
   4. ~/.cursor/agents/{agent-name}.md
   5. ~/.claude/agents/{agent-name}/AGENT.md
   6. ~/.gemini/antigravity/skills/{agent-name}/SKILL.md
   ```

## Core Workflow: task-flow

모든 개발 작업의 중심 파이프라인. 작업 규모에 따라 Full Task / Short Task 듀얼 모드로 동작한다. 알투는 오케스트레이터로서 워커 에이전트(`task-flow-agent`)를 디스패치하고, 실제 분석/설계/실행은 워커의 격리된 컨텍스트에서 수행한다.

### Full Task (대규모 변경, 사용자 요청 시)

```
사용자 지시 → [TASK 직접] → 검토 → [워커: RESEARCH] → [QA] → 검토
                                                              ↓
                                                    [워커: PLAN] → [QA] → 검토
                                                              ↓
                                                    [워커: TODO] → 검토
                                                              ↓
                                           승인 → [워커: EXECUTE] → [QA] → 완료 보고
```

### Short Task (기본 모드)

```
사용자 지시 → [TASK 직접] → 검토 → [워커: PLAN 통합] → [QA] → 승인 → [워커: EXECUTE] → [QA] → 완료 보고
```

**모드 판별**: 모든 작업은 Short Task로 시작. Full Task 트리거 (변경 파일 ≥10, 다단계 기술 의사결정, 다중 모듈 연쇄 영향) 해당 시 Full을 제안하고 사용자가 결정.

**핵심 규칙**: 사용자의 명시적 승인 전까지 코드 생성/수정 금지.

**QA 호출**: TASK와 TODO에서는 QA 생략(사용자 직접 검토). RESEARCH, PLAN, EXECUTE에서 오케스트레이터가 QA 에이전트를 호출하여 1차 검토.

**적응적 실행**: Full Task의 TODO 단계에서 복잡도를 판별하여, 단순 태스크는 워커가 직접 실행하고, 복잡 태스크는 워커 내부에서 Planner가 설계한 토폴로지에 따라 서브 에이전트가 병렬 실행한다.

### 산출물 저장 구조

**Full Task:**
```
tasks/{NNN}-{kebab-case-task-name}/
├── STATE.md             ← 실시간 상태 추적 (체크포인트)
├── TASK.md, RESEARCH.md, QA-RESEARCH.md
├── PLAN.md, QA-PLAN.md
├── TODO.md
├── QA-EXECUTE.md
├── TEST-REPORT.md (복잡 모드)
├── DONE.md
└── skills/ (동적 생성, 복잡 모드)
```

**Short Task:**
```
tasks/{NNN}-{kebab-case-task-name}/
├── STATE.md             ← 실시간 상태 추적 (체크포인트)
├── TASK.md
├── PLAN.md, QA-PLAN.md
├── QA-EXECUTE.md
└── DONE.md
```

태스크 폴더명에 3자리 순번을 접두사로 붙인다 (예: `001-user-auth-implementation`). 새 태스크 생성 시 `tasks/` 폴더의 기존 최대 번호 + 1, 폴더가 없으면 001부터 시작.

### 작업 유형별 분석 깊이

| 유형 | 트리거 키워드 | RESEARCH 깊이 |
|------|-------------|--------------|
| 신규 개발 | "새로 만들어", "추가해" | 심층 (기술 선택, 아키텍처) |
| 기능 개선 | "개선해", "최적화" | 중간 (현재 구현 + 개선 방안) |
| 오류 수정 | "에러", "버그", "안 돼" | 집중 (원인 분석) |
| 기능 수정 | "변경해", "바꿔" | 중간 (영향 범위 분석) |

## 문서 표준

모든 기술 문서 헤더:

```markdown
# [제목]

> 작성일: YYYY-MM-DD | 작성자: [작성자] | 버전: v{X.Y}
```

하단 변경이력 테이블:

```markdown
| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
```

## 버전 관리 규칙

- `v{Major}.{Minor}` 형식
- **Major**: 구조적 변경 (섹션 추가/삭제, 엔티티 신규, 아키텍처 변경)
- **Minor**: 내용 수정 (보강, 오류 수정, 세부 조정)
- 기존 파일 덮어쓰기 금지 — 항상 새 버전 파일 생성
- 이전 버전의 변경이력을 새 버전에 전부 계승

## 단계 완료 보고 형식

```
📋 [{단계명}] 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/{단계}.md
📎 QA 리뷰: tasks/{NNN}-{태스크명}/QA-{단계}.md
📎 완료 리포트: tasks/{NNN}-{태스크명}/DONE.md  ← EXECUTE 단계만

[QA 요약]
- 검증 항목 {N}개 중 {통과}개 Pass, {경고}개 Warning
- {주요 지적 사항 요약}
- 판정: {✅ Pass / ⚠️ Needs Revision}

다음 단계로 넘어갈까요?
```

QA가 없는 단계 (TASK, TODO)의 보고 형식:

```
📋 [{단계명}] 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/{단계}.md

다음 단계로 넘어갈까요?
```
