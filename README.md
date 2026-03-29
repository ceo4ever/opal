# OPAL — Open Protocol for Agentic Links

AI 환경(Claude Code, Cursor, Codex 등)에서 IT 프로젝트를 체계적으로 수행하기 위한 **범용 AI 개발 프레임워크**.
에이전트, 스킬, 훅 등의 재사용 가능한 컴포넌트를 만들어 다양한 AI 도구와 프로젝트에 적용할 수 있다.

---

## 2계층 아키텍처

```
Global Layer (1회 설치 → 모든 프로젝트에서 사용)
┌───────────────────────────────────────────────────┐
│  ~/.opal/                                         │
│  ├── skills/          스킬 (opal-pilot + op-dev    │
│  │                    + op-task + standalone + opal)│
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

### 오케스트레이터 (opal-pilot)

| 스킬 | 약어 | 설명 |
|------|------|------|
| **opal-pilot-dev** | opd | Full Task 파이프라인 (TASK → ANALYSIS → PLAN → EXECUTE) |
| **opal-pilot-dev-short** | opds | Short Task 파이프라인 (TASK → PLAN → EXECUTE, 기본 모드) |
| **opal-pilot-dev-wireframe** | opdw | Wireframe UI 파이프라인 (TASK → WIREFRAME → EXECUTE) |
| **opal-pilot-write** | opw | 범용 문서 작성 (TASK → PLAN → WRITE) |
| **opal-pilot-write-tech** | opwt | 서비스 기획 산출물 네트워크 (Phase 1~4) |

### 단계 스킬 (op-dev / op-task)

| 스킬 | 성격 | 설명 |
|------|------|------|
| **op-task** | 범용 | TASK.md 작성 |
| **op-task-qa** | 범용 | QA 검증 |
| **op-dev-analysis** | dev | 코드베이스 분석 |
| **op-dev-plan** | dev | 구현 계획 |
| **op-dev-todo** | dev | 실행 체크리스트 확장 (Full Task 전용) |
| **op-dev-test-scenario** | dev | 테스트 시나리오 |
| **op-dev-execute** | dev | 코드 실행 |
| **op-dev-wireframe** | dev | 와이어프레임 생성 |

### 독립 스킬 (standalone)

| 스킬 | 설명 |
|------|------|
| **api-analyzer** | 외부 API 7단계 분석 및 명세서 생성 |
| **interview** | 구조화된 Q&A 요구사항 수집 |
| **wireframe-builder** | UI 분석·설계 — 정책서/요구사항 → wireframe.md 생성 |
| **ui-designer** | UI 구현 — wireframe.md → React + shadcn/ui 기반 UI |
| **web-to-markdown** | 웹 페이지 마크다운 변환 (2단계 폴백) |

### 에이전트 (4개, 단일 AGENT.md 포맷)

| 에이전트 | 설명 | 호출 시점 |
|---------|------|----------|
| **op-dev-agent** | 범용 워커 | 각 단계 스킬을 독립 컨텍스트에서 실행 |
| **op-task-qa-agent** | QA 에이전트 | 산출물 품질 검증 |
| **op-dev-test-agent** | Test 에이전트 | EXECUTE 완료 후 코드 동적 검증 |
| **wtm-agent** | 웹 마크다운 변환 에이전트 | web-to-markdown 스킬에서 호출 |

### OPAL AI 에이전트

크로스 플랫폼 AI 개인 비서 + 프로젝트 오케스트레이터.

| 스킬 | 설명 |
|------|------|
| **opal-onboarding** | 초기 정체성 인터뷰 → identity.md 생성 |
| **opal-project-init** | 프로젝트 에이전트 초기화 |
| **opal-orchestrator** | 프로젝트 오케스트레이션 (서브에이전트 관리) |
| **opal-skill-manager** | 커뮤니티 스킬 검색/설치/관리 (npx skills 연동) |

**커뮤니티 스킬 (기본 번들 31개)**: Anthropic 공식 18개, Google Labs Stitch 5개, Vercel 개발 핵심 5개, 코드 품질 & 보안 3개. OPAL 내부(`~/.opal/community-skills/`)에만 설치. 추가 스킬은 `skill-manager`로 [skills.sh](https://skills.sh/) 생태계에서 검색/설치.

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
| Project Overview | op-task (TASK 작성) | 필수 |
| Language Convention | opal-doc-standard, op-task-qa | 필수 |
| Tech Stack | op-dev-plan (도구 탐색) | 필수 |
| Architecture | op-dev-analysis, op-dev-plan | 권장 |
| Code Conventions | op-task-qa, op-dev-execute | 필수 |

### Cursor: .cursor/rules/

```bash
mkdir -p {프로젝트}/.cursor/rules
cp cursor-rules/*.mdc {프로젝트}/.cursor/rules/
```

| 파일 | 모드 | 설명 |
|------|------|------|
| `001-project-conventions.mdc` | Always | 프로젝트 핵심 규칙 |
| `002-development-workflow.mdc` | Always | opal-pilot 파이프라인 |
| `100-document-standards.mdc` | Agent Requested | 문서 표준 + 버전 관리 |
| `101-task-artifacts.mdc` | Agent Requested | 태스크 산출물 구조 |

### Antigravity: GEMINI.md

프로젝트 루트에 `GEMINI.md`를 생성한다.

---

## 핵심 워크플로우

### opal-pilot-dev (Full Task)

```
TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE
```

### opal-pilot-dev-short (Short Task, 기본 모드)

```
TASK → PLAN+TEST-SCENARIO → EXECUTE
```

| 단계 | 목적 | 산출물 |
|------|------|--------|
| **TASK** | 작업 정의 | TASK.md |
| **ANALYSIS** | 기술 분석 (Full Task) | ANALYSIS.md |
| **PLAN** | 구현 설계 | PLAN.md |
| **EXECUTE** | 코드 구현 | 승인된 계획에 따른 코드 변경 |

**핵심 규칙**: 사용자의 명시적 승인 전까지 코드 생성/수정 금지.

---

## 소스 구조

```
opal/
├── README.md
├── CLAUDE.md                    이 저장소 자체의 프로젝트 설정
├── skills/                      스킬 (~/.opal/skills/로 배포)
│   ├── opal-pilot-dev/          오케스트레이터: Full Task (opd)
│   ├── opal-pilot-dev-short/    오케스트레이터: Short Task (opds)
│   ├── opal-pilot-dev-wireframe/ 오케스트레이터: Wireframe UI (opdw)
│   ├── opal-pilot-write/        오케스트레이터: Write (opw)
│   ├── opal-pilot-write-tech/   오케스트레이터: Write-Tech (opwt)
│   ├── op-task/                 범용 단계: TASK.md 작성
│   ├── op-task-qa/              범용 단계: QA 검증
│   ├── op-dev-analysis/         dev 단계: 코드베이스 분석
│   ├── op-dev-plan/             dev 단계: 구현 계획
│   ├── op-dev-todo/             dev 단계: 실행 체크리스트
│   ├── op-dev-test-scenario/    dev 단계: 테스트 시나리오
│   ├── op-dev-execute/          dev 단계: 코드 실행
│   ├── op-dev-wireframe/        dev 단계: 와이어프레임 생성
│   ├── api-analyzer/            독립: 외부 API 분석
│   ├── interview/               독립: 요구사항 수집
│   ├── opal-agent-creator/      OPAL: 에이전트 생성
│   ├── opal-skill-creator/      OPAL: 스킬 생성
│   ├── ui-designer/             독립: UI 구현
│   ├── web-to-markdown/         독립: 웹 마크다운 변환
│   └── wireframe-builder/       독립: UI 분석·설계
├── agents/                      에이전트 (4개, 단일 AGENT.md 포맷)
│   ├── op-dev-agent/            범용 워커
│   ├── op-task-qa-agent/        QA 에이전트
│   ├── op-dev-test-agent/       Test 에이전트
│   └── wtm-agent/               웹 마크다운 변환 에이전트
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
│   │   ├── references/          참조 레지스트리 + JSON 스킬 레지스트리
│   │   └── mcps/                MCP 설정 템플릿 (서버별 JSON)
│   ├── skills/                  OPAL 전용 스킬 (4개, opal- 접두사)
│   ├── tools/                   CLI 도구 (skill-registry, check-env)
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
