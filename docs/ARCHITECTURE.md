# 아키텍처

> OPAL 시스템 아키텍처

## 시스템 구성

OPAL은 2-레이어 아키텍처로 동작한다.

```
┌─────────────────────────────────────────────────────────┐
│  AI 플랫폼 (Claude Code / Cursor / Gemini)              │
│  ┌───────────────────────────────────────────────────┐  │
│  │  부트스트래퍼 (CLAUDE.md / .cursorrules / GEMINI.md) │
│  │  → ~/.opal/AGENT.md Read → 에이전트 활성화          │
│  └───────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │  OPAL 에이전트 (알투)                               │
│  │  ├─ 정체성: ~/.opal/identity.md                    │
│  │  ├─ 레지스트리: ~/.opal/references/                │
│  │  └─ PM 역할: {프로젝트}/.opal/AGENT.md             │
│  └───────────────────────────────────────────────────┘  │
│            │                          │                  │
│     // 커맨드 또는                  자연어 요청          │
│     자연어 요청                       │                  │
│            ▼                          ▼                  │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │  오케스트레이터    │    │  독립 스킬                │   │
│  │  (opal-pilot-*)   │    │  (api-analyzer,          │   │
│  │                   │    │   interview, ui-designer  │   │
│  │  하네스 적용       │    │   등)                    │   │
│  │  Guards/Gates/    │    └──────────────────────────┘   │
│  │  State            │                                   │
│  └──────────────────┘                                    │
│            │                                             │
│            ▼                                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │  서브에이전트 (Agent 도구로 디스패치)               │   │
│  │  ├─ opal-task-agent: 단계 스킬 실행 워커            │   │
│  │  ├─ opal-task-qa-agent: QA 스킬 동적 실행          │   │
│  │  ├─ op-dev-test-agent: 테스트 실행                 │   │
│  │  └─ wtm-agent: 웹→마크다운 변환                    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 2-레이어 모델

### Global Layer (`~/.opal/`)

모든 프로젝트가 공유하는 프레임워크 자산. `install-mac.sh`로 1회 배포.

| 디렉토리 | 내용 |
|----------|------|
| `AGENT.md` | 에이전트 핵심 정의 (부트스트랩, 행동 규칙, PM 역할) |
| `identity.md` | 에이전트 정체성 (이름, 성격, 톤) |
| `skills/` | 독립 스킬 5개 + OPAL 스킬 24개 |
| `agents/` | 서브에이전트 4개 |
| `community-skills/` | 커뮤니티 스킬 37개 (6개 조직) |
| `references/` | 레지스트리 (skills.md, agents.md, mcps.md, opal-harness.md, opal-doc-standard.md) |
| `tools/` | 스킬 레지스트리 CLI (skill-registry.js) |
| `templates/` | 프로젝트 에이전트 템플릿 |

### Project Layer (`{프로젝트}/`)

개별 프로젝트의 컨텍스트. 프로젝트별로 다르다.

| 파일/디렉토리 | 내용 |
|--------------|------|
| `CLAUDE.md` / `.cursorrules` / `GEMINI.md` | 플랫폼 부트스트래퍼 (에이전트 로드 트리거) |
| `.opal/AGENT.md` | PM 프로필 (역할, 검토 기준, 금지사항) |
| `.opal/MEMORY.md` + `memory/` | 프로젝트 메모리 (히스토리, 피드백, 아키텍처 결정) |
| `docs/PROJECT.md` | 프로젝트 정의 SSOT + 문서 허브 |
| `docs/ARCHITECTURE.md` | 아키텍처 (개발 프로젝트) |
| `docs/CONVENTIONS.md` | 컨벤션 (개발 프로젝트) |
| `tasks/` | 태스크 산출물 폴더 |

## 컴포넌트 유형

### 스킬 (Skills)

특정 작업을 수행하는 절차적 가이드. `SKILL.md` + `references/` + `personas/` 구조.

| 그룹 | 스킬 | 설명 |
|------|------|------|
| **오케스트레이터** | opal-pilot-dev (opd) | Full Task: TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE |
| | opal-pilot-dev-short (opds) | Short Task (기본): TASK → PLAN → TEST-SCENARIO → EXECUTE |
| | opal-pilot-dev-wireframe (opdw) | Wireframe UI: TASK → WIREFRAME → EXECUTE |
| | opal-pilot-write (opw) | 범용 문서: TASK → PLAN → WRITE |
| | opal-pilot-write-tech (opwt) | 서비스 기획 산출물: 네트워크형 오케스트레이션 |
| | opal-project-pilot (opp) | 범용 프로젝트: TASK → PLAN → EXECUTE |
| **dev 단계** | op-dev-analysis | 코드베이스 분석 + 기술 컨텍스트 수집 |
| | op-dev-plan | 구현 계획 (PLAN+TODO 통합) |
| | op-dev-todo | 실행 체크리스트 확장 (Full Task 전용) |
| | op-dev-test-scenario | 테스트 시나리오 생성 |
| | op-dev-execute | 코드 실행 (체크포인트 기반) |
| | op-dev-wireframe | 와이어프레임 생성 |
| | op-dev-qa | Dev QA 검증 (코드 개발 산출물) |
| **범용 단계** | op-task | TASK.md 작성 |
| | op-task-qa | 범용 QA 검증 (도메인 무관 산출물) |
| | op-task-plan | 범용 계획 수립 (도메인 무관) |
| | op-task-execute | 범용 실행 (도메인 무관) |
| **독립** | api-analyzer | 외부 API 7단계 분석 |
| | interview | 구조화된 Q&A 요구사항 수집 |
| | ui-designer | wireframe.md → React + shadcn/ui 구현 |
| | wireframe-builder | 정책서/요구사항 → wireframe.md |
| | web-to-markdown | 웹 페이지 마크다운 변환 |
| **OPAL** | opal-project-init (opi) | 프로젝트 초기화/최신화 |
| | opal-agent-creator | 에이전트 생성 파이프라인 |
| | opal-skill-creator | 스킬 생성 파이프라인 |
| | opal-onboarding | 에이전트 온보딩 |
| | opal-orchestrator | 오케스트레이션 모드 |
| | opal-skill-manager | 스킬 관리 |

### 에이전트 (Agents)

독립 컨텍스트에서 자율 실행하는 서브에이전트. `AGENT.md` 단일 파일.

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| opal-task-agent | standard | 범용 워커 — 단계 스킬 실행 |
| opal-task-qa-agent | light | 범용 QA 워커 — qa_skill로 QA 스킬 동적 실행 |
| op-dev-test-agent | standard | Test — 동적 검증 (테스트 실행 + 판정) |
| wtm-agent | light | web-to-markdown 병렬 처리 |

### 커뮤니티 스킬 (Community Skills)

외부 조직이 제공하는 스킬. `~/.opal/community-skills/`에 배포.

| 조직 | 스킬 수 | 주요 스킬 |
|------|---------|----------|
| Anthropic | 19개 | webapp-testing, frontend-design, claude-api, pdf, xlsx |
| Vercel Labs | 6개 | next-best-practices, react-best-practices, shadcn |
| Google Labs | 6개 | stitch-loop, react-components, remotion |
| Trail of Bits | 2개 | modern-python |
| GetSentry | 2개 | code-review |
| OpenAI | 2개 | security-best-practices |

### 하네스 (Harness)

오케스트레이터가 공유하는 공통 인프라. `opal-harness.md`에 정의.

| 요소 | 역할 |
|------|------|
| Guards | 구현 금지 원칙, Git 사전 점검, 커밋 규칙 |
| Gates | 단계 게이트 (캡틴 승인), QA Gate, PM Gate |
| State | STATE.md 상태 관리, 세션 복원 |
| TASK 프로세스 | op-task 스킬로 TASK.md 작성 (오케스트레이터 직접 수행) |
| Observability | 스킬/에이전트 탐색 경로, 프로젝트 메모리 동기화 |

## 배포 모델

```
소스 (이 저장소)                    배포 대상 (~/.opal/)
─────────────────                  ──────────────────
skills/* (독립 5개) ──┐
opal/skills/* (24개)──┼─ install ─→  ~/.opal/skills/
agents/*            ──┤              ~/.opal/agents/
community-skills/*  ──┤              ~/.opal/community-skills/
opal/core/*         ──┘              ~/.opal/references/, tools/, templates/

opal/bootstrapper/* ──── install ─→  ~/.claude/CLAUDE.md (부트스트래퍼 삽입)
opal/core/mcps/*    ──── install ─→  ~/.cursor/rules/ (부트스트래퍼)
                                     ~/.gemini/GEMINI.md (부트스트래퍼)
                                     각 플랫폼 MCP 설정 머지
```

`install-mac.sh`가 소스에서 `~/.opal/`로 통합 배포한다. 플랫폼별 디렉토리에는 부트스트래퍼와 MCP 설정만 배치한다.

## 디렉토리 구조

```
opal/                                    ← 이 저장소
├── skills/                              독립 스킬 (5개, 파이프라인 없이 단독 사용)
│   ├── api-analyzer/                    외부 API 분석
│   ├── interview/                       요구사항 수집
│   ├── ui-designer/                     UI 구현
│   ├── wireframe-builder/               와이어프레임 설계
│   └── web-to-markdown/                 웹→마크다운
├── agents/                              에이전트 (4개)
│   ├── opal-task-agent/                 범용 워커
│   ├── opal-task-qa-agent/              범용 QA 워커
│   ├── op-dev-test-agent/               테스트 에이전트
│   └── wtm-agent/                       웹→마크다운 에이전트
├── community-skills/                    커뮤니티 스킬 (37개, 6개 조직)
├── opal/                                OPAL 코어
│   ├── bootstrapper/                    플랫폼별 부트스트래퍼
│   ├── core/                            에이전트 코어 + 레퍼런스 + MCP + 도구
│   ├── skills/                          OPAL 스킬 (24개)
│   │   ├── opal-pilot-dev/              오케스트레이터: Full Task (opd)
│   │   ├── opal-pilot-dev-short/        오케스트레이터: Short Task (opds)
│   │   ├── opal-pilot-dev-wireframe/    오케스트레이터: Wireframe UI (opdw)
│   │   ├── opal-pilot-write/            오케스트레이터: Write (opw)
│   │   ├── opal-pilot-write-tech/       오케스트레이터: Write-Tech (opwt)
│   │   ├── opal-project-pilot/          오케스트레이터: Project (opp)
│   │   ├── op-dev-{analysis,plan,todo,execute,test-scenario,qa,wireframe}/
│   │   │                                dev 단계 스킬 (7개)
│   │   ├── op-task{,-plan,-execute,-qa}/ 범용 단계 스킬 (4개)
│   │   ├── opal-project-init/           프로젝트 초기화 (opi)
│   │   ├── opal-agent-creator/          에이전트 생성
│   │   ├── opal-skill-creator/          스킬 생성
│   │   ├── opal-onboarding/             에이전트 온보딩
│   │   ├── opal-orchestrator/           오케스트레이션 모드
│   │   ├── opal-project-dev-pilot/      프로젝트 개발 파일럿 (opdp)
│   │   └── opal-skill-manager/          스킬 관리
│   └── templates/                       프로젝트 에이전트 템플릿
├── cursor-rules/                        Cursor 프로젝트 규칙 템플릿
├── scripts/                             설치 스크립트 (install-mac.sh)
├── tasks/                               태스크 산출물
├── docs/                                프로젝트 문서
└── .opal/                               이 프로젝트의 PM 프로필 + 메모리
