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
├── dev-task-pilot/              핵심 오케스트레이터: TASK → ANALYSIS → PLAN → TODO → EXECUTE
├── api-analyzer/                외부 API 7단계 분석 및 명세서 생성
├── doc-writer/                  기술 문서 표준 템플릿 (모든 문서 스킬의 베이스)
├── interview/                   구조화된 Q&A 요구사항 수집
├── ui-designer/                 UI 구현 — wireframe.md → React + shadcn/ui 기반 UI
├── version-mgr/                 산출물 버전 관리 (v{Major}.{Minor}, 덮어쓰기 금지)
└── wireframe-builder/           UI 분석·설계 — 정책서/요구사항 → wireframe.md 생성

agents/                          ← 에이전트 (플랫폼별 포맷 분리)
├── claude/                      ← AGENT.md 디렉토리 기반
│   ├── dtp-agent/               워커 에이전트 (각 단계 실행)
│   ├── dtp-qa/                  산출물 품질 검증
│   ├── dtp-planner/             실행 아키텍처 설계
│   └── dtp-test/                코드 동적 검증
├── cursor/                      ← 플랫 파일 형식 (.md)
│   ├── dtp-agent.md
│   ├── dtp-qa.md
│   ├── dtp-planner.md
│   └── dtp-test.md
└── antigravity/                 ← SKILL.md로 통합
    ├── dtp-agent/
    ├── dtp-qa/
    ├── dtp-planner/
    └── dtp-test/

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
│   ├── dev-task-pilot/
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
    │   ├── dev-task-pilot/
    │   └── dtp-qa/              에이전트도 스킬로 통합
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
- **dev-task-pilot** → 개발 작업의 주 진입점 (5단계 파이프라인)
- **dtp-agent** → dev-task-pilot의 각 단계를 독립 컨텍스트에서 실행하는 워커 에이전트
- **dtp-qa** → dev-task-pilot 각 단계 완료 후 오케스트레이터가 호출하는 QA 에이전트
- **dtp-planner** → dev-task-pilot TODO 단계에서 복잡 모드 시 실행 아키텍처 설계
- **dtp-test** → dev-task-pilot EXECUTE 단계에서 복잡 모드 시 코드 동적 검증

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
6. 네이밍: `{대상 워크플로우}-{역할}` (예: `dtp-qa`)
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

