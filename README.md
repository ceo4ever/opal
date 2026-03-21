# OPAL — Open Protocol for Agentic Links

AI 환경(Claude Code, Cursor, Codex 등)에서 IT 프로젝트를 체계적으로 수행하기 위한 **범용 AI 개발 프레임워크**.
에이전트, 스킬, 훅 등의 재사용 가능한 컴포넌트를 만들어 다양한 AI 도구와 프로젝트에 적용할 수 있다.

---

## 2계층 아키텍처

```
Global Layer (1회 설치 → 모든 프로젝트에서 사용)
┌───────────────────────────────────────────────────┐
│  ~/.opal/                                         │
│  ├── skills/          프레임워크 + OPAL 전용 스킬    │
│  ├── agents/          에이전트 (단일 AGENT.md 포맷)  │
│  ├── community-skills/ 커뮤니티 스킬 (31개)          │
│  ├── references/      참조 레지스트리                 │
│  ├── AGENT.md         OPAL AI 에이전트 코어          │
│  └── identity.md      에이전트 정체성                 │
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

### Skills (10개 프레임워크 + 31개 커뮤니티)

| 스킬 | 설명 | 용도 |
|------|------|------|
| **dev-task-pilot** | 핵심 오케스트레이터 | TASK → ANALYSIS → PLAN → TODO → EXECUTE 5단계 파이프라인 |
| **api-analyzer** | 외부 API 분석 | 7단계 분석 및 API 명세서 생성 |
| **doc-writer** | 기술 문서 표준 | 모든 문서 스킬의 베이스 템플릿 |
| **interview** | 요구사항 수집 | 구조화된 Q&A로 요구사항 수집 및 갭 탐지 |
| **opal-agent-creator** | 에이전트 생성 | OPAL 에이전트 생성 파이프라인 |
| **opal-skill-creator** | 스킬 생성 | OPAL 스킬 생성 파이프라인 |
| **ui-designer** | UI 구현 | wireframe.md → React + shadcn/ui 기반 UI 구현 |
| **version-mgr** | 버전 관리 | 산출물 v{Major}.{Minor} 버전 관리, 덮어쓰기 금지 |
| **web-to-markdown** | 웹 → 마크다운 | 웹 페이지 마크다운 변환 (2단계 폴백) |
| **wireframe-builder** | UI 분석·설계 | 정책서/요구사항 → wireframe.md 생성 |

**커뮤니티 스킬 (기본 번들 31개)**: Anthropic 공식 18개, Google Labs Stitch 5개, Vercel 개발 핵심 5개, 코드 품질 & 보안 3개. OPAL 내부(`~/.opal/community-skills/`)에만 설치. 추가 스킬은 `skill-manager`로 [skills.sh](https://skills.sh/) 생태계에서 검색/설치.

### Agents (7개, 단일 AGENT.md 포맷)

| 에이전트 | 설명 | 호출 시점 |
|---------|------|----------|
| **dtp-dev-agent** | Full/Short Task 워커 | 각 단계(ANALYSIS/PLAN/TODO/EXECUTE)를 독립 컨텍스트에서 실행 |
| **dtp-wireframe-ui-agent** | Wireframe UI 워커 | WIREFRAME/EXECUTE 단계 실행 |
| **dtp-qa-dev-agent** | Full/Short Task QA | 각 단계 산출물 작성 후 (5단계 문서 리뷰) |
| **dtp-qa-wireframe-agent** | Wireframe UI QA | wireframe.md 검증 + 빌드/린트 + 코드 대조 |
| **dtp-action-plan-agent** | 실행 아키텍처 설계 | TODO 단계에서 복잡 모드 판별 시 (Part C 생성) |
| **dtp-dev-test-agent** | 테스트 실행 | EXECUTE 완료 후 복잡 모드에서 (코드 동적 검증) |
| **wtm-worker** | 웹 마크다운 변환 워커 | web-to-markdown 스킬에서 호출 |

### OPAL AI 에이전트

크로스 플랫폼 AI 개인 비서 + 프로젝트 오케스트레이터.

| 스킬 | 설명 |
|------|------|
| **opal-onboarding** | 초기 정체성 인터뷰 → identity.md 생성 |
| **opal-project-init** | 프로젝트 에이전트 초기화 |
| **opal-orchestrator** | 프로젝트 오케스트레이션 (서브에이전트 관리) |
| **opal-skill-manager** | 커뮤니티 스킬 검색/설치/관리 (npx skills 연동) |

---

## 설치 가이드

### 자동 설치 (권장)

```bash
git clone {REPO_URL} ai-framework
cd ai-framework
./scripts/install-mac.sh
```

메뉴에서 설치 대상을 선택한다:
- `[1]` OPAL 설치 — skills + agents + 부트스트래퍼 → `~/.opal/`
- `[2]` MCP 서버 설정 — MCP 설정 → claude, cursor, gemini, antigravity
- `[3]` 전체 설치 — OPAL + MCP 서버

---

## 프로젝트 설정 가이드

글로벌 레이어 설치만으로는 스킬/에이전트가 프로젝트 컨텍스트를 알 수 없다. **프로젝트마다** 아래 설정을 해야 한다.

### Claude Code: CLAUDE.md

기존 `CLAUDE.md`에 누락된 섹션을 추가하는 방식으로 설정한다.

| 섹션 | 읽는 컴포넌트 | 필수 여부 |
|------|-------------|----------|
| Project Overview | dev-task-pilot (TASK 작성) | 필수 |
| Language Convention | doc-writer, dtp-qa | 필수 |
| Tech Stack | dtp-planner (도구 탐색) | 필수 |
| Architecture | dev-task-pilot (ANALYSIS), dtp-planner | 권장 |
| Code Conventions | dtp-qa (E-4), EXECUTE 서브에이전트 | 필수 |

### Cursor: .cursor/rules/

```bash
mkdir -p {프로젝트}/.cursor/rules
cp cursor-rules/*.mdc {프로젝트}/.cursor/rules/
```

| 파일 | 모드 | 설명 |
|------|------|------|
| `001-project-conventions.mdc` | Always | 프로젝트 핵심 규칙 |
| `002-development-workflow.mdc` | Always | dev-task-pilot 파이프라인 |
| `100-document-standards.mdc` | Agent Requested | 문서 표준 + 버전 관리 |
| `101-task-artifacts.mdc` | Agent Requested | 태스크 산출물 구조 |

### Antigravity: GEMINI.md

프로젝트 루트에 `GEMINI.md`를 생성한다.

---

## 핵심 워크플로우: dev-task-pilot

```
TASK → ANALYSIS → PLAN → TODO → EXECUTE
```

| 단계 | 목적 | 산출물 |
|------|------|--------|
| **TASK** | 작업 정의 | TASK.md |
| **ANALYSIS** | 기술 분석 | ANALYSIS.md |
| **PLAN** | 구현 설계 | PLAN.md |
| **TODO** | 실행 계획 | TODO.md (Part A + B + C) |
| **EXECUTE** | 코드 구현 | 승인된 계획에 따른 코드 변경 |

**핵심 규칙**: 사용자의 명시적 승인 전까지 코드 생성/수정 금지.

---

## 소스 구조

```
opal/
├── README.md
├── CLAUDE.md                    이 저장소 자체의 프로젝트 설정
├── skills/                      프레임워크 스킬 (10개, ~/.opal/skills/로 배포)
│   ├── dev-task-pilot/          핵심 오케스트레이터
│   ├── api-analyzer/            외부 API 분석
│   ├── doc-writer/              기술 문서 표준
│   ├── interview/               요구사항 수집
│   ├── opal-agent-creator/      에이전트 생성
│   ├── opal-skill-creator/      스킬 생성
│   ├── ui-designer/             UI 구현
│   ├── version-mgr/             버전 관리
│   ├── web-to-markdown/         웹 마크다운 변환
│   └── wireframe-builder/       UI 분석·설계
├── agents/                      에이전트 (7개, 단일 AGENT.md 포맷)
│   ├── dtp-dev-agent/           Full/Short Task 워커
│   ├── dtp-wireframe-ui-agent/  Wireframe UI 워커
│   ├── dtp-qa-dev-agent/        Full/Short Task QA
│   ├── dtp-qa-wireframe-agent/  Wireframe UI QA
│   ├── dtp-action-plan-agent/   실행 아키텍처 설계
│   ├── dtp-dev-test-agent/      코드 동적 검증
│   └── wtm-worker/              웹 마크다운 변환 워커
├── community-skills/            커뮤니티 스킬 기본 번들 (31개)
│   ├── anthropics/              Anthropic 공식 (18개)
│   ├── google-labs-code/        Google Labs Stitch (5개)
│   ├── vercel-labs/             Vercel 개발 핵심 (5개)
│   ├── trailofbits/             Trail of Bits (1개)
│   ├── getsentry/               Sentry (1개)
│   └── openai/                  OpenAI (1개)
├── opal/                        OPAL AI 에이전트 (크로스 플랫폼)
│   ├── bootstrapper/            부트스트래퍼 (플랫폼별)
│   ├── core/                    에이전트 코어 (AGENT.md, identity-template.md)
│   │   ├── references/          참조 레지스트리 (skills.md, agents.md, mcps.md)
│   │   └── mcps/                MCP 설정 템플릿 (서버별 JSON)
│   ├── skills/                  OPAL 전용 스킬 (4개, opal- 접두사)
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
