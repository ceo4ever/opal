# AI 개발 프레임워크

AI 환경(Claude Code, Cursor, Antigravity 등)에서 IT 프로젝트를 체계적으로 수행하기 위한 **범용 AI 개발 프레임워크**.
에이전트, 스킬, 훅 등의 재사용 가능한 컴포넌트를 만들어 다양한 AI 도구와 프로젝트에 적용할 수 있다.

---

## 2계층 아키텍처

```
Global Layer (1회 설치 → 모든 프로젝트에서 사용)
┌───────────────────────────────────────────────────┐
│  Claude Code : ~/.claude/skills/ + agents/         │
│  Cursor      : ~/.cursor/skills/ + agents/         │
│  Antigravity : ~/.gemini/antigravity/skills/       │
│  OPAL        : ~/.opal/ (크로스 플랫폼 AI 에이전트)  │
└────────────────────┬──────────────────────────────┘
                     │ READ
Project Layer (프로젝트마다 설정)
┌────────────────────▼──────────────────────────────┐
│  Claude Code  : {프로젝트}/CLAUDE.md                │
│  Cursor       : {프로젝트}/.cursor/rules/*.mdc      │
│  Antigravity  : {프로젝트}/GEMINI.md                 │
│                                                   │
│  언어 규칙, 기술 스택, 아키텍처,                       │
│  코드 컨벤션, 문서 표준, 워크플로우                     │
└───────────────────────────────────────────────────┘
```

---

## 컴포넌트 목록

### Skills (6개 프레임워크 + 31개 커뮤니티)

| 스킬 | 설명 | 용도 |
|------|------|------|
| **task-flow** | 핵심 오케스트레이터 | TASK → RESEARCH → PLAN → TODO → EXECUTE 5단계 파이프라인 |
| **api-analyzer** | 외부 API 분석 | 7단계 분석 및 API 명세서 생성 |
| **doc-writer** | 기술 문서 표준 | 모든 문서 스킬의 베이스 템플릿 |
| **interview** | 요구사항 수집 | 구조화된 Q&A로 요구사항 수집 및 갭 탐지 |
| **version-mgr** | 버전 관리 | 산출물 v{Major}.{Minor} 버전 관리, 덮어쓰기 금지 |
| **wireframe-builder** | 와이어프레임 | 단일 HTML 인터랙티브 와이어프레임 생성 |

**커뮤니티 스킬 (기본 번들 31개)**: Anthropic 공식 18개, Google Labs Stitch 6개, Vercel 개발 핵심 4개, 코드 품질 & 보안 3개. OPAL 내부(`~/.opal/community-skills/`)에만 설치. 추가 스킬은 `skill-manager`로 [skills.sh](https://skills.sh/) 생태계에서 검색/설치.

### Agents (3개)

| 에이전트 | 설명 | 호출 시점 |
|---------|------|----------|
| **task-flow-qa** | 산출물 품질 검증 | 각 단계 산출물 작성 후 (5단계 문서 리뷰) |
| **task-flow-planner** | 실행 아키텍처 설계 | TODO 단계에서 복잡 모드 판별 시 (Part C 생성) |
| **task-flow-test** | 테스트 실행 | EXECUTE 완료 후 복잡 모드에서 (코드 동적 검증) |

### OPAL AI 에이전트

크로스 플랫폼 AI 개인 비서 + 프로젝트 오케스트레이터.

| 스킬 | 설명 |
|------|------|
| **onboarding** | 초기 정체성 인터뷰 → identity.md 생성 |
| **project-init** | 프로젝트 에이전트 초기화 |
| **orchestrator** | 프로젝트 오케스트레이션 (서브에이전트 관리) |
| **skill-manager** | 커뮤니티 스킬 검색/설치/관리 (npx skills 연동) |

---

## 설치 가이드

### 자동 설치 (권장)

```bash
git clone {REPO_URL} ai-framework
cd ai-framework
./scripts/install-mac.sh
```

메뉴에서 설치 대상을 선택한다:
- `[1]` Claude Code — skills + agents → `~/.claude/`
- `[2]` Cursor — skills + agents → `~/.cursor/`
- `[3]` Antigravity — skills → `~/.gemini/antigravity/`
- `[4]` OPAL — AI 에이전트 + 참조 레지스트리 + 커뮤니티 스킬 + 부트스트래퍼
- `[5]` 전체 설치

### 수동 설치

```bash
# Claude Code
cp -r skills/* ~/.claude/skills/
cp -r agents/claude/* ~/.claude/agents/

# Cursor
cp -r skills/* ~/.cursor/skills/
cp -r agents/cursor/* ~/.cursor/agents/

# Antigravity
mkdir -p ~/.gemini/antigravity/skills
cp -r skills/* ~/.gemini/antigravity/skills/
cp -r agents/antigravity/* ~/.gemini/antigravity/skills/
```

---

## 프로젝트 설정 가이드

글로벌 레이어 설치만으로는 스킬/에이전트가 프로젝트 컨텍스트를 알 수 없다. **프로젝트마다** 아래 설정을 해야 한다.

### Claude Code: CLAUDE.md

기존 `CLAUDE.md`에 누락된 섹션을 추가하는 방식으로 설정한다.

| 섹션 | 읽는 컴포넌트 | 필수 여부 |
|------|-------------|----------|
| Project Overview | task-flow (TASK 작성) | 필수 |
| Language Convention | doc-writer, task-flow-qa | 필수 |
| Tech Stack | task-flow-planner (도구 탐색) | 필수 |
| Architecture | task-flow (RESEARCH), task-flow-planner | 권장 |
| Code Conventions | task-flow-qa (E-4), EXECUTE 서브에이전트 | 필수 |

### Cursor: .cursor/rules/

```bash
mkdir -p {프로젝트}/.cursor/rules
cp cursor-rules/*.mdc {프로젝트}/.cursor/rules/
```

| 파일 | 모드 | 설명 |
|------|------|------|
| `001-project-conventions.mdc` | Always | 프로젝트 핵심 규칙 |
| `002-development-workflow.mdc` | Always | task-flow 파이프라인 |
| `100-document-standards.mdc` | Agent Requested | 문서 표준 + 버전 관리 |
| `101-task-artifacts.mdc` | Agent Requested | 태스크 산출물 구조 |

### Antigravity: GEMINI.md

프로젝트 루트에 `GEMINI.md`를 생성한다.

---

## 핵심 워크플로우: task-flow

```
TASK → RESEARCH → PLAN → TODO → EXECUTE
```

| 단계 | 목적 | 산출물 |
|------|------|--------|
| **TASK** | 작업 정의 | TASK.md |
| **RESEARCH** | 기술 분석 | RESEARCH.md |
| **PLAN** | 구현 설계 | PLAN.md |
| **TODO** | 실행 계획 | TODO.md (Part A + B + C) |
| **EXECUTE** | 코드 구현 | 승인된 계획에 따른 코드 변경 |

**핵심 규칙**: 사용자의 명시적 승인 전까지 코드 생성/수정 금지.

---

## 소스 구조

```
ai-framework/
├── README.md
├── CLAUDE.md                    이 저장소 자체의 프로젝트 설정
├── skills/                      프레임워크 스킬 (6개, 3개 플랫폼 공용)
│   ├── task-flow/
│   ├── api-analyzer/
│   ├── doc-writer/
│   ├── interview/
│   ├── version-mgr/
│   └── wireframe-builder/
├── agents/                      에이전트 (플랫폼별 포맷 분리)
│   ├── claude/                  AGENT.md 디렉토리 기반
│   ├── cursor/                  플랫 파일 .md
│   └── antigravity/             SKILL.md로 통합
├── community-skills/            커뮤니티 스킬 기본 번들 (31개)
│   ├── anthropics/              Anthropic 공식 (18개)
│   ├── google-labs-code/        Google Labs Stitch (6개)
│   ├── vercel-labs/             Vercel 개발 핵심 (4개)
│   ├── trailofbits/             Trail of Bits (1개)
│   ├── getsentry/               Sentry (1개)
│   └── openai/                  OpenAI (1개)
├── opal/                        OPAL AI 에이전트 (크로스 플랫폼)
│   ├── bootstrapper/            부트스트래퍼 (플랫폼별)
│   ├── core/                    에이전트 코어 (AGENT.md)
│   │   └── references/          참조 레지스트리 (skills.md, agents.md, mcps.md)
│   ├── skills/                  OPAL 전용 스킬 (4개)
│   └── templates/               프로젝트 에이전트 템플릿
├── cursor-rules/                Cursor 프로젝트 규칙 템플릿
├── scripts/                     설치 스크립트
│   └── install-mac.sh
└── tasks/                       태스크 산출물
```

---

## 언어 규칙

| 대상 | 언어 |
|------|------|
| 문서 본문 | 한국어 (기술 용어는 영어 병기) |
| 코드/변수/필드명 | English |
| 파일/폴더 명명 | kebab-case |
