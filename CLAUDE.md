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
skills/                          ← 스킬 (단일 소스, ~/.opal/skills/로 배포)
├── opal-pilot-dev/              오케스트레이터: Full Task (opd)
├── opal-pilot-dev-short/        오케스트레이터: Short Task (opds, 기본 진입점)
├── opal-pilot-dev-wireframe/    오케스트레이터: Wireframe UI (opdw)
├── opal-pilot-write/            오케스트레이터: 범용 문서 작성 (opw)
├── opal-pilot-write-tech/       오케스트레이터: 서비스 기획 산출물 (opwt)
├── opal-project-pilot/          오케스트레이터: 범용 프로젝트 (opp)
│   └── SKILL.md
├── op-task/                     범용 단계: TASK.md 작성
│   ├── references/task-guide.md
│   └── personas/service-planner.md
├── op-task-qa/                  범용 단계: QA 검증
│   ├── references/              qa-dev-guide.md, qa-wireframe-guide.md
│   └── personas/qa-engineer.md
├── op-task-plan/                범용 단계: 계획 수립 (도메인 무관)
│   ├── references/plan-guide.md
│   └── personas/generalist-architect.md
├── op-task-execute/             범용 단계: 실행 (도메인 무관)
│   ├── references/execute-guide.md
│   └── personas/generalist-executor.md
├── op-dev-analysis/             dev 단계: 코드베이스 분석
│   ├── references/              analysis-guide.md, tech-context-guide.md
│   └── personas/application-architect.md
├── op-dev-plan/                 dev 단계: 구현 계획
│   ├── references/plan-guide.md
│   └── personas/software-architect.md
├── op-dev-todo/                 dev 단계: 실행 체크리스트 확장 (Full Task 전용)
│   ├── references/              todo-guide.md, execute-plan-guide.md
│   └── personas/software-architect.md
├── op-dev-test-scenario/        dev 단계: 테스트 시나리오
│   ├── references/test-scenario-guide.md
│   └── personas/qa-engineer.md
├── op-dev-execute/              dev 단계: 코드 실행
│   ├── references/              execute-guide.md, checkpoint-guide.md
│   └── personas/                frontend-engineer.md, backend-engineer.md
├── op-dev-wireframe/            dev 단계: 와이어프레임 생성
│   └── personas/service-planner.md
├── api-analyzer/                독립: 외부 API 7단계 분석 및 명세서 생성
├── interview/                   독립: 구조화된 Q&A 요구사항 수집
├── opal-agent-creator/          OPAL: 에이전트 생성 파이프라인
├── opal-skill-creator/          OPAL: 스킬 생성 파이프라인
├── ui-designer/                 독립: UI 구현 — wireframe.md → React + shadcn/ui 기반 UI
├── web-to-markdown/             독립: 웹 페이지 마크다운 변환 (2단계 폴백)
└── wireframe-builder/           독립: UI 분석·설계 — 정책서/요구사항 → wireframe.md 생성

agents/                          ← 에이전트 (단일 AGENT.md 포맷)
├── opal-task-agent/             범용 워커 (단계 스킬 실행)
├── op-task-qa-agent/            QA 에이전트 (산출물 검증)
├── op-dev-test-agent/           Test 에이전트 (동적 검증)
└── wtm-agent/                   web-to-markdown 병렬 처리 에이전트

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
├── skills/                      OPAL 전용 스킬 (opal-onboarding, opal-project-init, opal-orchestrator, opal-skill-manager)
└── templates/                   프로젝트 에이전트 템플릿

cursor-rules/                    ← Cursor 프로젝트 규칙 템플릿

.opal/                           ← 이 프로젝트의 PM 프로필 및 메모리 (opal-project-init이 생성)
├── AGENT.md                     PM 프로필 (역할, 페르소나, 의사결정 원칙, 프로젝트 규칙)
├── MEMORY.md                    메모리 인덱스 (카테고리 + 작업 히스토리)
└── memory/                      개별 메모리 파일 (작업 기록, 아키텍처 결정, 도메인 지식 등)
```

### 배포 구조 (사용자 홈)

`install-mac.sh`가 소스에서 `~/.opal/`로 통합 배포한다. 플랫폼별 디렉토리에는 부트스트래퍼와 MCP 설정만 배치한다.

```
~/.opal/                         ← 통합 배포 경로 (모든 플랫폼 공유)
├── AGENT.md                     에이전트 핵심 정의
├── identity.md                  정체성 (온보딩으로 생성)
├── skills/                      스킬 (opal-pilot + op-dev + op-task + standalone + opal)
│   ├── opal-pilot-dev/          ← skills/ 에서 복사
│   ├── op-dev-plan/
│   ├── opal-onboarding/         ← opal/skills/ 에서 복사
│   ├── opal-orchestrator/
│   └── ...
├── agents/                      에이전트 (4개, 단일 AGENT.md 포맷)
│   ├── opal-task-agent/
│   ├── op-task-qa-agent/
│   └── ...
├── references/                  참조 레지스트리 (부트스트랩 시 Read)
│   ├── skills.md                스킬 목록
│   ├── agents.md                에이전트 목록
│   └── mcps.md                  MCP 서버 목록
├── community-skills/            커뮤니티 스킬 (31개)
└── templates/                   프로젝트 에이전트 템플릿

~/.claude/                       ← Claude Code (부트스트래퍼 + MCP + hooks만)
├── CLAUDE.md                    OPAL 부트스트래퍼 삽입
├── settings.json                Claude Code hooks 설정
└── .claude.json                 MCP 서버 설정 (claude mcp add로 등록)

~/.cursor/                       ← Cursor (부트스트래퍼 + MCP만)
├── rules/000-opal-agent.mdc     OPAL 부트스트래퍼
└── mcp.json                     MCP 서버 설정 (opal/core/mcps/에서 머지)

~/.gemini/                       ← Gemini CLI / Antigravity (부트스트래퍼 + MCP만)
├── GEMINI.md                    OPAL 부트스트래퍼
├── settings.json                MCP 서버 설정 (Gemini CLI)
└── antigravity/
    └── mcp_config.json          MCP 서버 설정 (Antigravity)
```

**설치 원칙**: 프레임워크 스킬과 에이전트는 `~/.opal/`에 단일 배포한다. 플랫폼별 네이티브 디렉토리(`~/.claude/`, `~/.cursor/`, `~/.gemini/`)에는 부트스트래퍼와 MCP 설정만 배치하며, 스킬/에이전트를 복사하지 않는다. 커뮤니티 스킬도 `~/.opal/community-skills/`에만 설치된다.

### 컴포넌트 유형

| 유형 | 설명 | 현재 상태 |
|------|------|----------|
| **Skills** | 특정 작업을 수행하는 절차적 가이드 (SKILL.md) | `skills/` 24개 + `community-skills/` 31개 |
| **Agents** | 독립 컨텍스트에서 자율 실행하는 에이전트 (AGENT.md) | `agents/` 4개 × 1 포맷 |
| **Hooks** | 이벤트 기반으로 자동 실행되는 트리거 | 확장 예정 |

### 컴포넌트 간 의존 관계

- **opal-pilot-*** → 태스크 파이프라인 오케스트레이터 (dev: opd/opds/opdw, write: opw/opwt)
- **opal-project-pilot (opp)** → 범용 프로젝트 오케스트레이터 (TASK → PLAN → EXECUTE)
- **op-dev-*** → dev 도메인 단계 스킬 (analysis/plan/todo/test-scenario/execute/wireframe)
- **op-task / op-task-qa** → 범용 단계 스킬 (TASK.md 작성, QA 검증)
- **op-task-plan / op-task-execute** → 범용 단계 스킬 (도메인 무관 계획/실행, opal-project-pilot이 사용)
- **opal-task-agent** → 범용 워커 (단계 스킬 실행)
- **op-task-qa-agent** → QA 에이전트 (산출물 검증)
- **op-dev-test-agent** → Test 에이전트 (EXECUTE 완료 후 동적 검증)
- **opal-doc-standard** → 모든 문서 산출물의 표준 규칙 (doc-writer + version-mgr 통합, ~/.opal/references/)
- **interview** → 요구사항 불명확 시 다른 스킬에서 호출

## 새 컴포넌트 작성 가이드

### Skill 추가 시

1. `skills/{skill-name}/SKILL.md` 생성
2. YAML frontmatter에 `name`, `description` 정의 (description에 트리거 키워드 포함)
3. 단계별 프로세스와 산출물 형식을 명확히 기술
4. 필요 시 `references/` 하위에 상세 가이드 추가

### Agent 추가 시

단일 포맷으로 에이전트 파일을 생성한다:

1. `agents/{agent-name}/AGENT.md` 생성
2. YAML frontmatter에 `name`, `description` 정의
3. 입력/출력 명세, 실행 프로세스, 검증 기준을 명확히 기술
4. 네이밍: `{대상 워크플로우}-{역할}` (예: `op-task-qa`)
5. **호출하는 스킬의 SKILL.md에 에이전트 탐색 경로 명시**:
   ```
   탐색 경로 (우선순위):
   1. {프로젝트}/.opal/agents/{agent-name}/AGENT.md
   2. ~/.opal/agents/{agent-name}/AGENT.md
   ```
