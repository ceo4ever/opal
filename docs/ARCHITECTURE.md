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
│  │  서브에이전트 10개 (Agent 도구로 디스패치)           │   │
│  │  ├─ opal-task-agent: 범용 워커 (폴백)              │   │
│  │  ├─ opal-plan-agent: PLAN 단계 전문 (advanced)     │   │
│  │  ├─ opal-fe-agent: FE EXECUTE 전문                 │   │
│  │  ├─ opal-be-agent: BE EXECUTE 전문                 │   │
│  │  ├─ opal-db-agent: DB 설계+구현 전문               │   │
│  │  ├─ opal-planning-agent: 서비스 기획 전문          │   │
│  │  ├─ opal-test-agent: 테스트 전문 (도메인별 모드)   │   │
│  │  ├─ opal-task-qa-agent: QA 스킬 동적 실행          │   │
│  │  ├─ opal-task-action-agent: oppd Phase 3 액션 자율 실행  │
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
| `agents/` | 서브에이전트 10개 (전문 6 + 범용 4) |
| `community-skills/` | 커뮤니티 스킬 37개 (6개 조직) |
| `references/` | 레지스트리 (skills.md, agents.md, mcps.md, opal-harness.md, opal-doc-standard.md, tools.md) |
| `tools/` | CLI 도구 (skill-registry/, xlsx-tool/, check-env.js, requirements.txt) |
| `.venv/` | Python 가상환경 (openpyxl, pandas, playwright 등 — requirements.txt로 관리) |
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
| | opal-pilot-write-tech (opwt) | 서비스 기획 산출물: 네트워크형 오케스트레이션 |
| | opal-pilot-project (opp) | 프로젝트 범용: TASK → PLAN → EXECUTE |
| | opal-pilot-project-dev (oppd) | 프로젝트 개발 라이프사이클: opwt → WBS → opd/opds |
| | opal-pilot-sdd (opsdd) | SDD 기반 오케스트레이터: SPEC → SPEC-VERIFY → SPEC-PLAN → TASKS → TASKS-VERIFY → EXECUTE-LOOP → DONE |
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
| **SDD 단계** | op-sdd-spec | SPEC 단계 — SDD 명세 작성 |
| | op-sdd-verify | VERIFY 단계 — SDD 명세 검증 |
| | op-sdd-plan | SPEC-PLAN 단계 — SDD 구현 계획 수립 |
| | op-sdd-tasks | TASKS 단계 — SDD 태스크 분해 |
| **독립** | api-analyzer | 외부 API 7단계 분석 |
| | interview | 구조화된 Q&A 요구사항 수집 |
| | ui-designer | wireframe.md → React + shadcn/ui 구현 |
| | wireframe-builder | 정책서/요구사항 → wireframe.md |
| | web-to-markdown | 웹 페이지 마크다운 변환 |
| | erd-modeler | DB ERD 모델링 (개념→논리→물리→DDL) |
| **OPAL** | opal-project-init (opi) | 프로젝트 초기화/최신화 |
| | opal-agent-creator | 에이전트 생성 파이프라인 |
| | opal-skill-creator | 스킬 생성 파이프라인 |
| | opal-onboarding | 에이전트 온보딩 |
| | opal-orchestrator | 오케스트레이션 모드 |
| | opal-skill-manager | 스킬 관리 |

### 에이전트 (Agents)

독립 컨텍스트에서 자율 실행하는 서브에이전트. `AGENT.md` 단일 파일.

**범용 에이전트 (기존)**

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| opal-task-agent | standard | 범용 워커 — 단계 스킬 실행 (폴백) |
| opal-task-qa-agent | light | 범용 QA 워커 — qa_skill로 QA 스킬 동적 실행 |
| opal-task-action-agent | advanced | 액션 에이전트 — oppd Phase 3 자율 실행 |
| opal-sdd-action-agent | advanced | SDD 액션 에이전트 |
| wtm-agent | light | web-to-markdown 병렬 처리 |

**전문 에이전트 (Specialist)**

| 에이전트 | 모델 | 단계 | 영역 | 역할 |
|---------|------|------|------|------|
| opal-plan-agent | advanced | PLAN | 공통 | 코드 분석 + 기능 설계 + 에이전트 라우팅 |
| opal-fe-agent | standard | EXECUTE | FE | 프론트엔드 구현 전문 |
| opal-be-agent | standard | EXECUTE | BE | 백엔드 구현 전문 |
| opal-db-agent | standard | PLAN, EXECUTE | DB | DB 모델 설계 + 마이그레이션 구현 |
| opal-planning-agent | advanced | EXECUTE | 기획 | 서비스 기획 산출물 작성/관리 |
| opal-test-agent | standard | TEST | 공통 | 테스트 전문 (BE/FE/E2E 모드) |

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
skills/* (독립 6개) ──┐
opal/skills/* (24개)──┼─ install ─→  ~/.opal/skills/
opal/agents/* (10개)──┤              ~/.opal/agents/  (source 캐시 — 어댑터 재생성용)
agents/* (범용 1개) ──┤
community-skills/*  ──┤              ~/.opal/community-skills/
opal/core/          ──┤              ~/.opal/AGENT.md
  references/       ──┤              ~/.opal/references/
opal/tools/         ──┤              ~/.opal/tools/
opal/templates/     ──┘              ~/.opal/templates/

opal/tools/requirements.txt ──────→  ~/.opal/.venv/ (Python 가상환경 생성/업데이트)

opal/bootstrapper/* ──── install ─→  ~/.claude/CLAUDE.md
                                     ~/.cursor/rules/000-opal-agent.mdc
                                     ~/.gemini/GEMINI.md

opal/core/mcps/*    ──── install ─→  claude mcp add --scope user (Claude)
                                     gemini mcp add -s user (Gemini)
                                     ~/.cursor/mcp.json (Cursor)
                                     ~/.gemini/antigravity/mcp_config.json (Antigravity)

# 어댑터 자동 생성 (실제 LLM 이 런타임에 읽는 곳)
~/.opal/agents/* ──── install (emit) ─→ ~/.claude/agents/{name}.md   (Claude Code 형식)
                                        ~/.cursor/agents/{name}.md   (Cursor 형식)
                                        ~/.gemini/agents/{name}.md   (Gemini 형식)
```

`install-mac.sh`가 소스에서 `~/.opal/`로 통합 배포한다. 플랫폼별 디렉토리(`~/.claude/`, `~/.cursor/`, `~/.gemini/`)에는 부트스트래퍼·MCP 설정과 함께 **에이전트 어댑터**가 배치된다.

**source vs runtime 구분**: `~/.opal/agents/`는 OPAL 표준 형식의 source 캐시이며 LLM 이 직접 읽지 않는다. 런타임에 PM 디스패치가 `Task(subagent_type=…)`로 호출하면 각 플랫폼은 **자기 어댑터 디렉토리**(`~/.claude/agents/` 등)에서 매칭한다. `~/.opal/agents/` 는 install/update 시 어댑터 재생성을 위한 단일 진실 원본 역할을 한다.

## 외부 의존 서비스

OPAL이 동작·배포 시 의존하는 외부 자원이다. 신규/변경 시 이 표를 SSOT로 사용하고, 설치 스크립트와 PROJECT.md "프로젝트 문서" 테이블의 정합성을 유지한다.

### MCP 서버 (`opal/core/mcps/*.json`)

| 이름 | 용도 | 적용 플랫폼 | 설치 방식 |
|------|------|----------|----------|
| context7 | 라이브러리·프레임워크 최신 문서 조회 | Claude / Cursor / Gemini | CLI 또는 config_merge |
| playwright | 브라우저 자동화 | Claude / Cursor / Gemini | CLI 또는 config_merge |
| shadcn | shadcn/ui 컴포넌트 카탈로그 | Claude / Cursor | CLI 또는 config_merge |
| sequential-thinking | 단계적 사고 도구 | Claude / Cursor | config_merge |
| Notion | Notion 페이지 연동 (인증 필요) | Claude | CLI |
| (기타) | `opal/core/mcps/*.json` 참조 | - | install 스크립트가 자동 처리 |

설치 진입점: `install-mac.sh`의 `[2] MCP 서버 설정` 메뉴. 등록 방식은 플랫폼별 — `claude mcp add --scope user` / `gemini mcp add -s user` / Cursor·Antigravity는 `mcp.json` config_merge.

### Anthropic Claude API

- 일부 스킬·에이전트가 Claude API를 직접 호출하는 경우 사용 (해당 시 환경변수 `ANTHROPIC_API_KEY` 필요).
- 모델 매핑: `~/.opal/references/opal-model-mapping.md` — 플랫폼 중립 레벨(`light`/`standard`/`advanced`) ↔ 모델(`haiku`/`sonnet`/`opus`).

### Python 의존성 (`opal/tools/requirements.txt`)

- 설치 시 `~/.opal/.venv/`에 Python venv를 생성하고 의존성을 설치한다.
- 주요 패키지: Playwright, openpyxl, pandas (xlsx-tool), MCP SDK 등.
- Playwright 브라우저(Chromium / Firefox / WebKit)는 별도 설치 명령으로 다운로드: `~/.opal/.venv/bin/playwright install chromium`.

### Node.js 도구

- `skill-registry`, `state-tool`, `check-env.js` 등 일부 CLI 도구가 Node.js 18+ 의존.
- 설치 스크립트가 `node --version`을 점검하고 누락 시 경고만 출력 (강제 종료하지 않음).

### 배포 채널

| 채널 | 단계 | 상태 | 비고 |
|------|------|------|------|
| GitHub Releases | 1차 | **현행** | 태그 기반 tarball + sha256sums.txt + `actions/attest-build-provenance@v2` |
| `opal-cli` CLI | 1차 | **현행** | `install`/`update`/`doctor`/`uninstall`/`mcp` 단일 진입점 (`~/.opal/bin/opal-cli`) |
| One-liner installer | 1차 | **현행** | `curl \| bash`(mac/linux) / `iex (irm)`(Windows) 진입점 (`scripts/install.sh`, `scripts/install.ps1`) |
| Homebrew tap | 2차 | 예정 | macOS 사용자 대상 `brew install opal-cli` (명칭은 별도 결정) |
| npm 패키지 | 후속 | 예정 | cross-platform 통합 |

> 결정 근거: 태스크 138(opi) 검토 → 139(P1)에서 1차 채널 구현 완료 — 캡틴 결정 D1 = `opal-cli` 명칭(Homebrew core `opal`/opalrb 충돌 회피), D2 = `https://github.com/ceo4ever/opal`.

## 디렉토리 구조

```
opal/                                    ← 이 저장소
├── skills/                              독립 스킬 (6개, 파이프라인 없이 단독 사용)
│   ├── api-analyzer/                    외부 API 분석
│   ├── erd-modeler/                     DB ERD 모델링 (개념→논리→물리→DDL)
│   ├── interview/                       요구사항 수집
│   ├── ui-designer/                     UI 구현
│   ├── wireframe-builder/               와이어프레임 설계
│   └── web-to-markdown/                 웹→마크다운
├── agents/                              범용 에이전트 (OPAL 무관)
│   └── wtm-agent/                       웹→마크다운 에이전트
├── community-skills/                    커뮤니티 스킬 (37개, 6개 조직)
├── opal/                                OPAL 코어
│   ├── bootstrapper/                    플랫폼별 부트스트래퍼
│   ├── core/                            에이전트 코어 + 레퍼런스 + MCP
│   │   ├── references/                  레지스트리 (harness, skills, agents, mcps, tools 등)
│   │   ├── mcps/                        MCP 설정 (shadcn, context7, playwright 등)
│   │   └── hooks/                       Claude Code hooks 설정
│   ├── tools/                           CLI 도구
│   │   ├── skill-registry/              스킬 레지스트리 CLI (skill-registry.js)
│   │   ├── xlsx-tool/                   xlsx 읽기/쓰기 CLI (run.sh)
│   │   ├── check-env.js                 Node.js 환경 체크
│   │   └── requirements.txt             Python 의존성 (venv 관리)
│   ├── skills/                          OPAL 스킬 (24개)
│   │   ├── opal-pilot-dev/              오케스트레이터: Full Task (opd)
│   │   ├── opal-pilot-dev-short/        오케스트레이터: Short Task (opds)
│   │   ├── opal-pilot-dev-wireframe/    오케스트레이터: Wireframe UI (opdw)
│   │   ├── opal-pilot-write-tech/       오케스트레이터: Write-Tech (opwt)
│   │   ├── opal-pilot-project/          오케스트레이터: Project (opp)
│   │   ├── opal-pilot-project-dev/      오케스트레이터: Project Dev (oppd)
│   │   ├── op-dev-{analysis,plan,todo,execute,test-scenario,qa,wireframe}/
│   │   │                                dev 단계 스킬 (7개)
│   │   ├── op-task{,-plan,-execute,-qa}/ 범용 단계 스킬 (4개)
│   │   ├── opal-project-init/           프로젝트 초기화 (opi)
│   │   ├── opal-agent-creator/          에이전트 생성
│   │   ├── opal-skill-creator/          스킬 생성
│   │   ├── opal-onboarding/             에이전트 온보딩
│   │   ├── opal-orchestrator/           오케스트레이션 모드
│   │   └── opal-skill-manager/          스킬 관리
│   ├── agents/                          OPAL 에이전트 (10개: 전문 6 + 범용 4)
│   │   ├── opal-plan-agent/             전문: PLAN 설계 (advanced)
│   │   ├── opal-fe-agent/               전문: FE 구현
│   │   ├── opal-be-agent/               전문: BE 구현
│   │   ├── opal-db-agent/               전문: DB 설계+구현
│   │   ├── opal-planning-agent/         전문: 서비스 기획 (advanced)
│   │   ├── opal-test-agent/             전문: 테스트 (도메인별 모드)
│   │   ├── opal-task-agent/             범용 워커 (폴백)
│   │   ├── opal-task-qa-agent/          범용 QA 워커
│   │   ├── opal-task-action-agent/      액션 에이전트 (oppd)
│   │   └── opal-sdd-action-agent/       SDD 액션 에이전트
│   └── templates/                       프로젝트 에이전트 템플릿
├── cursor-rules/                        Cursor 프로젝트 규칙 템플릿
├── scripts/                             설치 스크립트 (install-mac.sh)
├── tasks/                               태스크 산출물
├── docs/                                프로젝트 문서
└── .opal/                               이 프로젝트의 PM 프로필 + 메모리
