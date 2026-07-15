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
│  │  서브에이전트 12개 (Agent 도구로 디스패치)           │   │
│  │  ├─ opal-task-agent: 범용 워커 (폴백)              │   │
│  │  ├─ opal-plan-agent: PLAN 단계 전문 (advanced)     │   │
│  │  ├─ opal-fe-agent: FE EXECUTE 전문                 │   │
│  │  ├─ opal-be-agent: BE EXECUTE 전문                 │   │
│  │  ├─ opal-db-agent: DB 설계+구현 전문               │   │
│  │  ├─ opal-planning-agent: 서비스 기획 전문          │   │
│  │  ├─ opal-test-agent: 테스트 전문 (도메인별 모드)   │   │
│  │  ├─ opal-task-qa-agent: QA 스킬 동적 실행          │   │
│  │  ├─ opal-task-action-agent: oppd Phase 3 액션 자율 실행  │
│  │  └─ opal-wtm-agent: 웹→마크다운 변환                │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 부트스트랩 진입 모델 (2-tier)

부트스트랩은 **2-tier**로 동작한다 — 전역 마커는 항상 **비서 tier**를 로드하고, **PM tier**는 OPAL 프로젝트(`.opal/AGENT.md` 존재)에서만 승격된다. SSOT는 `~/.opal/AGENT.md` Eager 단계(소스 `opal/core/AGENT.md`).

| Tier | 트리거 | 로드 대상 | 모드 |
|------|--------|----------|------|
| **Phase A — 비서(Lite)** | 전역 마커(install이 `~/.claude/CLAUDE.md` 등에 1회 삽입) — 모든 세션 상시 | 스킵게이트(setting.json 머지) + identity + PRINCIPLES(헌법) + 보고형식·도구맵·`//` 레지스트리 해석 | 자비스 비서 |
| **Phase B — PM(Full)** | cwd에 `.opal/AGENT.md` 존재 시에만 승격 | (Phase A에 더해) opal-harness(Guards/State) + opal-pm(PM 프로세스) + 프로젝트 `.opal/AGENT.md` + PROJECT/MEMORY 브리핑 | 프로젝트 PM |

- **opt-in 모델**: `.opal/AGENT.md`가 없는 비-opi 디렉토리에서는 Phase B가 스킵되어 PM/파이프라인이 로드되지 않는다. `//opi`로 초기화하면 `.opal/AGENT.md`가 생성되어 다음 진입부터 PM tier로 승격된다.
- **`//opi` 불변식**: `//` 커맨드 해석은 비서 tier에 속하므로(Lazy 트리거 전제조건 없음), 비-opi 폴더에서도 `//opi` 발동이 보장된다 — 새 프로젝트 OPAL화의 진입점.
- **전역 비서 유지**: 전역 마커는 제거가 아니라 경량 비서 마커로 유지된다. `setting.json bootstrap:off`는 비서·PM 양쪽을 스킵하는 킬스위치(전역/프로젝트 공통).
- **첫 줄 마커 3단 스킵 사다리**: 프롬프트/디스패치 첫 줄 마커로 로드 범위를 결정한다 — `[WORKER]`(전부 스킵: Phase A·B·공통) / `[ASSISTANT]`(비서 tier만: Phase A — `.opal/AGENT.md`가 있어도 Phase B 승격 억제) / 무마커(비서+PM: 프로젝트면 승격). `[ASSISTANT]`는 `claude -p` 등 headless 호출이 프로젝트 cwd에서도 PM tier 오염 없이 비서 tier로 동작하게 하는 캡이며, 첫 소비자는 대시보드 브레인 질의 어댑터(`dashboard/backend/adapters/opbr_adapter.py`)다. `//` 커맨드는 비서 tier 능력이므로 `[ASSISTANT]` 캡 상태에서도 `//opbr` 등이 정상 완주한다.

## 2-레이어 모델

### Global Layer (`~/.opal/`)

모든 프로젝트가 공유하는 프레임워크 자산. `install-mac.sh`로 1회 배포.

| 디렉토리 | 내용 |
|----------|------|
| `AGENT.md` | 에이전트 핵심 정의 (부트스트랩, 행동 규칙, PM 역할) |
| `identity.md` | 에이전트 정체성 (이름, 성격, 톤) |
| `skills/` | 독립 스킬 5개 + OPAL 스킬 25개 |
| `agents/` | 서브에이전트 12개 (전문 7 + 범용 4 + 도구성 1) |
| `community-skills/` | 커뮤니티 스킬 — `npx skills` (vercel-labs/skills)로 사용자가 온디맨드 fetch |
| `references/` | 레지스트리 (skills.md, agents.md, mcps.md, opal-harness.md, opal-doc-standard.md, tools.md) |
| `tools/` | CLI 도구 (skill-registry/, xlsx-tool/, tool-scan/ — capability 검색·live 사용법, memory-tool/ — 메모리 인덱스·히스토리 결정론적 집행·docs/brain 졸업 워크플로우, check-env.js, requirements.txt) |
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
| | opal-pilot-project-loop (oppl) | 루프 기반 프로젝트 오케스트레이터: 설계 루프(인터뷰→PRD→TRD→CONTRACT→백로그) → 실행 루프(태스크 반복, 종료조건 5종·3-SSOT tool-gated) |
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
| opal-wtm-agent | light | web-to-markdown 워커 (Phase 1 WebFetch → Phase 2 cmux → Phase 3 playwright-tool CLI) |
| opal-security-checker | advanced | 보안 체크 — OWASP Top 10 / CWE Top 25 / SANS Top 25 Base + `docs/SECURITY.md` 누적 |
| opal-convention-checker | standard | 컨벤션 체크 — 프로젝트 `docs/CONVENTIONS.md` 유일 기준 (부재 시 초안 유도) |

**전문 에이전트 (Specialist)**

| 에이전트 | 모델 | 단계 | 영역 | 역할 |
|---------|------|------|------|------|
| opal-plan-agent | advanced | PLAN | 공통 | 코드 분석 + 기능 설계 + 에이전트 라우팅 |
| opal-fe-agent | standard | EXECUTE | FE | 프론트엔드 구현 전문 |
| opal-be-agent | standard | EXECUTE | BE | 백엔드 구현 전문 |
| opal-db-agent | standard | PLAN, EXECUTE | DB | DB 모델 설계 + 마이그레이션 구현 |
| opal-planning-agent | advanced | EXECUTE | 기획 | 서비스 기획 산출물 작성/관리 |
| opal-test-agent | standard | TEST | 공통 | 테스트 전문 (BE/FE/E2E 모드) |
| opal-evaluator-agent | advanced | 명세 리뷰 (oppl G/D6) | 평가 | 계약·설계 루브릭 심판 — CONTRACT.md 루브릭절 기준 구현 전 판정 (verdict-only·readonly) |

### 커뮤니티 스킬 (Community Skills)

외부 조직이 제공하는 스킬. OPAL은 번들로 배포하지 않으며, 사용자가 `//skill-manager` 또는 `// 커맨드` 첫 호출 시 동의 prompt를 거쳐 [skills.sh](https://skills.sh/) 카탈로그(vercel-labs/skills)에서 fetch한다.

| 항목 | 값 |
|------|-----|
| 카탈로그 SSOT | [skills.sh](https://skills.sh/) — `npx skills find` |
| 설치 명령 | `npx skills add {owner/repo@skill}` (알투 자동 호출 또는 `//skill-manager`) |
| 설치 위치 | `~/.opal/community-skills/{owner}/{skill}/SKILL.md` |
| 레지스트리 | `~/.opal/references/community-skills-registry.json` (v2 메타데이터 카탈로그 — 트리거/source_repo/license) |
| 라이선스 책임 | 사용자 fetch 시점 발생 (OPAL repo는 third-party 코드 재배포 안 함) |

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
opal/agents/* (12개)──┤              ~/.opal/agents/  (source 캐시 — 어댑터 재생성용)
agents/* (범용 1개) ──┤
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

# 커뮤니티 스킬은 install이 배포하지 않음. 사용자가 //skill-manager로 fetch:
~/.opal/community-skills/  ←  npx skills add {owner/repo@skill}  ←  사용자 동의 prompt
```

`install-mac.sh`가 소스에서 `~/.opal/`로 통합 배포한다. 플랫폼별 디렉토리(`~/.claude/`, `~/.cursor/`, `~/.gemini/`)에는 부트스트래퍼·MCP 설정과 함께 **에이전트 어댑터**가 배치된다.

**source vs runtime 구분**: `~/.opal/agents/`는 OPAL 표준 형식의 source 캐시이며 LLM 이 직접 읽지 않는다. 런타임에 PM 디스패치가 `Task(subagent_type=…)`로 호출하면 각 플랫폼은 **자기 어댑터 디렉토리**(`~/.claude/agents/` 등)에서 매칭한다. `~/.opal/agents/` 는 install/update 시 어댑터 재생성을 위한 단일 진실 원본 역할을 한다.

## OPAL Console (로컬 프로젝트 관리 대시보드)

로컬에서 OPAL로 작업하는 모든 프로젝트를 한 웹 화면에서 조망하는 **읽기 전용 대시보드**(태스크 021 신설). 데이터 SSOT를 새로 만들지 않고, OPAL 도구의 read-only 커맨드 + 마크다운 파서로 각 프로젝트 데이터를 수집·렌더한다.

```
┌─ Web UI (React + shadcn/ui, 7개 화면) ──────────────────┐
│  대시보드·프로젝트·태스크(칸반)·메모리·환경·프로젝트 브레인·설정 │
└───────────────┬──────────────────────────────────────────┘
                │ HTTP (127.0.0.1:7823)
┌───────────────▼──────────────────────────────────────────┐
│  FastAPI 데몬 (~/.opal/dashboard-server/backend)          │
│  • 프로젝트 스캐너 (.opal/AGENT.md 마커 디스크 스캔)        │
│  • read-only 어댑터: state-tool/code-scan/skill-registry/doctor │
│  • 마크다운 파서: MEMORY.md·memory/*·PROJECT/AGENT.md      │
│  • TTL 캐시(mtime 무효화) · 읽기 전용                       │
│  • [예외·격리] 브레인 질의 라우터만 POST + opbr CLI(태스크036)│
│  • [예외·격리] 설정 라우터만 파일 쓰기 — 화이트리스트 2종(태스크061)│
└───────────────────────────────────────────────────────────┘
```

### 프로젝트 브레인 질의 (태스크 036)

콘솔에서 프로젝트 brain 지식을 질의·답변받는 6번째 메뉴. **읽기 전용 대시보드의 유일한 POST·LLM 경로**이며 brain 질의 라우터 하나에만 격리한다(기존 5라우터·어댑터는 GET·read-only 불변).

| 항목 | 값 |
|------|-----|
| LLM 합성 | 로컬 `claude -p '//opbr query --read-only "<질의>"' --output-format json` 서브프로세스 → **각 사용자 Claude 구독**으로 실행(종량제 API·키 미사용). backend는 opbr 출력의 JSON 펜스만 추출하는 얇은 프록시(opbr이 brain 검색/인용 전담 — DRY) |
| opbr 계약 | `opal-brain` SKILL.md `//opbr query --read-only`(v1.4): 자동 선별·항상 최종답변·순수 read-only(brain 무변경)·JSON 출력 |
| 세션 | `BrainSession`(B1): 일회성 `claude -p` + 디스크 세션 `--session-id`(콜드 프라임)→`--resume`(웜). prime-on-intent(메뉴 진입 시 백그라운드 프라임) + 5트리거 리셋(서버재실행·컨텍스트임계·유휴·크래시·수동) + `threading.Lock` 직렬화. 실측 콜드~90s/웜~20s |
| 프라임 연결 풀 (태스크 060·063) | `console.config.json`의 `prewarm_projects`(절대경로 배열, 기본 `[]`)에 지정한 프로젝트만 서버 기동 시(lifespan 훅) 백그라운드 선프라임하여 **프로젝트별 웜 핸들 풀**(크기 2 — 태스크 063 상향)에 적재. 새 대화 첫 진입(`BrainSessionRegistry._get_or_create`)·"새 대화" 시 풀에서 lock 하 체크아웃→세션에 이식(즉시 ready·첫 질의 `--resume` 웜)하고 `prewarm()`이 `need=pool_size-have`만큼 충전(태스크 063 — 상수만 올리면 풀이 1까지만 차던 결함 수정, 연속 새대화 즉시 웜 배정). 동시 프라임은 `Semaphore(2)` 상한, 풀 비면 기존 콜드 폴백(API 5종 계약·FE 불변). 풀은 인메모리 전용(무상태 원칙) |
| 엔드포인트 | `GET /api/brain/auth`(claude CLI 가용·인증) · `POST /api/brain/prime`(백그라운드 프라임) · `POST /api/brain/query`(질의→`{answer, citations}`) |
| 세션 수명·이력 (태스크 063) | **휘발성 단일 세션(미영속)**. FE는 메뉴 mount·"새 대화"마다 새 `session_id`(UUID)를 발급하고, 단일 대화창에서 그 세션이 살아있는 동안 멀티턴(`--resume`)을 이어간다. 대화 이력은 저장하지 않는다(localStorage 이력·멀티대화 관리 제거) — 새로고침·재오픈·타 브라우저 접속 시 백지에서 시작(의도된 동작). "새 대화"는 재오픈과 동일 동작(내역 초기화 + 새 session_id + 즉시 웜). backend·brain 무상태/무변경 |

### 프로젝트별 환경 설정 화면 (태스크 061)

콘솔 7번째 메뉴 `/settings`. 읽기 전용 원칙의 두 번째 예외로, 브레인 POST 격리 선례를 따라 **설정 라우터(`routers/config.py`) 1곳에만 파일 쓰기를 허용**한다. 이번 범위는 **프라임 풀 토글 단일 기능**(캡틴 확정 — 화면 기능은 필요 시 하나씩 추가, JSON 설정은 파일 수동 편집 유지).

| 항목 | 값 |
|------|-----|
| 쓰기 화이트리스트 | `~/.opal/console.config.json` **1종만**(prewarm_projects 갱신 한정). project는 스캔 프로젝트 매칭(400 게이트)으로 검증 — FE 경로 문자열 불신뢰 |
| 기능 | 프라임 풀(사전 예열) 토글 — `GET /api/config`(상태 조회) + `POST /api/config/prewarm` {project, enabled}: ON 시 `prewarm_projects` 머지 반영(멱등) + 목록 신규 추가 시 `BrainSessionRegistry.prewarm()` 즉시 호출(재기동 불요), OFF 시 목록 제거. 화면은 토글 + prewarm_projects 읽기 전용 표시 |
| 동시 쓰기 방어 | 모듈 `threading.Lock`(read-modify-write 직렬화) + temp 파일 후 `os.replace`(atomic rename) — 머지 보존(미지 키 유지) |
| 범위 제외(후속) | console.config 전반 편집·프로젝트 로컬 `.opal/setting.local.json` 편집 — 파일 수동 편집으로 관리, 미사용 쓰기 API는 표면 최소화 위해 미노출 |
| 불변 | LLM 호출 0회(브레인 라우터 격리 유지) · 기존 read-only 5종 + 브레인 POST 계약 불변 · 127.0.0.1 바인딩 |

| 항목 | 값 |
|------|-----|
| 소스 | `{프로젝트}/dashboard/` (frontend: React+TS+Vite+shadcn / backend: FastAPI) |
| 배포 | `~/.opal/dashboard-server/` (install이 FE 빌드+BE 복사, venv는 `~/.opal/.venv` 공유) |
| 기동 | `opal-cli console {start\|stop\|status\|open\|scan}` (127.0.0.1:7823) |
| 프로젝트 식별 | `.opal/AGENT.md` 마커 디스크 스캔 (`~/.opal/console.config.json` scan_roots/depth/exclude) — config는 `opal-cli console scan [기준경로...]`이 생성·머지 갱신(기존 roots 보존, `--prune` 옵트인)하며 install(`install_dashboard`)이 1회 자동 실행. `start`는 config 부재 시 scan 안내 출력 |
| 원칙 | 읽기 전용(쓰기/편집은 2차) · 데이터 SSOT는 각 프로젝트 파일 · 데몬은 도구 오케스트레이터 |
| 디자인 토큰 | 시그니처 3색(`--brand-primary/secondary/tertiary`)을 `:root` 1곳 전역 CSS 변수화 (교체 용이) |

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
| `opal-cli` CLI | 1차 | **현행** | `update`/`doctor`/`uninstall`/`mcp`/`console` 단일 진입점 (`~/.opal/bin/opal-cli`) — 신규 설치는 One-liner installer |
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
├── agents/                              범용 에이전트 슬롯 (현재 비어있음)
├── opal/                                OPAL 코어
│   ├── bootstrapper/                    플랫폼별 부트스트래퍼
│   ├── core/                            에이전트 코어 + 레퍼런스 + MCP
│   │   ├── references/                  레지스트리 (harness, skills, agents, mcps, tools 등)
│   │   ├── mcps/                        MCP 설정 (shadcn, context7, playwright 등)
│   │   └── hooks/                       Claude Code hooks 설정
│   ├── tools/                           CLI 도구
│   │   ├── skill-registry/              스킬 레지스트리 CLI (skill-registry.js)
│   │   ├── xlsx-tool/                   xlsx 읽기/쓰기 CLI (run.sh)
│   │   ├── cmux-tool/                   cmux browser 래퍼 (run.sh) — 3모드(A/B/C) + user_owned 시그널
│   │   ├── check-env.js                 Node.js 환경 체크
│   │   └── requirements.txt             Python 의존성 (venv 관리)
│   ├── skills/                          OPAL 스킬 (25개)
│   │   ├── opal-pilot-dev/              오케스트레이터: Full Task (opd)
│   │   ├── opal-pilot-dev-short/        오케스트레이터: Short Task (opds)
│   │   ├── opal-pilot-dev-wireframe/    오케스트레이터: Wireframe UI (opdw)
│   │   ├── opal-pilot-write-tech/       오케스트레이터: Write-Tech (opwt)
│   │   ├── opal-pilot-project/          오케스트레이터: Project (opp)
│   │   ├── opal-pilot-project-dev/      오케스트레이터: Project Dev (oppd)
│   │   ├── opal-pilot-project-loop/     오케스트레이터: Project Loop (oppl)
│   │   ├── op-dev-{analysis,plan,todo,execute,test-scenario,qa,wireframe}/
│   │   │                                dev 단계 스킬 (7개)
│   │   ├── op-task{,-plan,-execute,-qa}/ 범용 단계 스킬 (4개)
│   │   ├── opal-project-init/           프로젝트 초기화 (opi)
│   │   ├── opal-agent-creator/          에이전트 생성
│   │   ├── opal-skill-creator/          스킬 생성
│   │   ├── opal-onboarding/             에이전트 온보딩
│   │   └── opal-skill-manager/          스킬 관리
│   ├── agents/                          OPAL 에이전트 (12개: 전문 7 + 범용 4 + 도구성 1)
│   │   ├── opal-plan-agent/             전문: PLAN 설계 (advanced)
│   │   ├── opal-fe-agent/               전문: FE 구현
│   │   ├── opal-be-agent/               전문: BE 구현
│   │   ├── opal-db-agent/               전문: DB 설계+구현
│   │   ├── opal-planning-agent/         전문: 서비스 기획 (advanced)
│   │   ├── opal-test-agent/             전문: 테스트 (도메인별 모드)
│   │   ├── opal-evaluator-agent/        전문: 명세 심판 (advanced, verdict-only)
│   │   ├── opal-task-agent/             범용 워커 (폴백)
│   │   ├── opal-task-qa-agent/          범용 QA 워커
│   │   ├── opal-task-action-agent/      액션 에이전트 (oppd)
│   │   ├── opal-sdd-action-agent/       SDD 액션 에이전트
│   │   └── opal-wtm-agent/              웹→마크다운 워커 (Phase 1 WebFetch → Phase 2 cmux → Phase 3 playwright-tool CLI)
│   └── templates/                       프로젝트 에이전트 템플릿
├── dashboard/                           OPAL Console (로컬 프로젝트 관리 대시보드 — 태스크 021)
│   ├── frontend/                        React + TS + Vite + shadcn/ui (6개 화면 — 브레인 질의 포함, 태스크 036)
│   └── backend/                         FastAPI 데몬 (스캐너 + read-only 어댑터 + 파서)
├── cursor-rules/                        Cursor 프로젝트 규칙 템플릿
├── scripts/                             설치 스크립트 (install-mac.sh)
├── tasks/                               태스크 산출물
├── docs/                                프로젝트 문서
└── .opal/                               이 프로젝트의 PM 프로필 + 메모리

---

## 변경이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-06-18 | opal-orchestrator 잔존 행 2곳 삭제 (폴더·레지스트리 항목 부재 — dangling. Task 029) |
| 2026-06-30 | 부트스트랩 진입 모델 2-tier 절 추가 — 비서(Lite·전역 상시)/PM(Full·`.opal/AGENT.md` 존재 시 승격) 분리. opt-in 모델·`//opi` 불변식·전역 비서 유지 (Task 049) |
| 2026-07-02 | 부트스트랩 진입 모델에 첫 줄 마커 3단 스킵 사다리 추가 — `[ASSISTANT]` 마커 신설로 headless(claude -p) 호출을 비서 tier(Phase A)로 캡(PM tier 승격 억제). 첫 소비자 opbr_adapter (Task 051) |
| 2026-07-10 | 배포 채널 표 `opal-cli` CLI 서브커맨드 목록에서 install 제거 — install 서브커맨드 완전 제거에 정합(신규 설치는 One-liner installer, 갱신은 update) (Task 055) |
| 2026-07-10 | Project Loop 파이프라인 반영 — 오케스트레이터 표 oppl 행, 전문 에이전트 표 opal-evaluator-agent 행, 폴더 트리 oppl 스킬·evaluator 에이전트, 서브에이전트 수 12개(전문 7)로 정합 (Task 056) |
| 2026-07-10 | OPAL Console 표 갱신 — `console scan` 서브명령 반영(기동 행 scan 추가, 프로젝트 식별 행에 config 생성·머지·install 자동 실행·start 안내 명기) (Task 057) |
| 2026-07-14 | OPAL Console 브레인 질의 표에 "프라임 연결 풀" 행 신설 — prewarm_projects 선프라임·프로젝트별 웜 핸들 풀(크기 1)·체크아웃+백그라운드 리필·Semaphore(2) 상한·콜드 폴백·인메모리 전용 (Task 060) |
| 2026-07-14 | OPAL Console 7번째 화면 "설정" 신설 절 추가 — 설정 라우터 쓰기 격리(화이트리스트)·프라임 풀 토글 단일 기능(캡틴 범위 확정: console.config·로컬 설정 편집은 수동 유지, 후속 단위 추가)·Lock+atomic rename·다이어그램 7화면 갱신 (Task 061) |
| 2026-07-15 | OPAL Console 브레인 세션 단순화 — "이력" 행을 **휘발성 단일 세션(미영속)**으로 전환(localStorage 이력·멀티대화 관리 제거, mount·새 대화마다 새 session_id, 단일 대화창 멀티턴 유지), 프라임 연결 풀 크기 1→2 + `prewarm()` need-based 충전(연속 새대화 즉시 웜, 상수만 상향 시 풀 1까지만 차던 결함 수정) (Task 063) |
