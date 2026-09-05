# 아키텍처

> OPAL 시스템 아키텍처

## 시스템 구성

OPAL은 2-레이어 아키텍처로 동작한다.

> **정본 시각 자산**: 10계층 전체 구조도는 [`docs/architecture-diagram/opal_framework_architecture.html`](architecture-diagram/opal_framework_architecture.html)가 정본이다(태스크 086, `system-architecture-html` 스킬 산출). 아래 ASCII 다이어그램은 **진입 흐름 요약본**이며, 계층 상세는 HTML을 기준으로 한다.

```
┌─────────────────────────────────────────────────────────┐
│  AI 플랫폼 (Claude Code / Cursor / Gemini / Codex)       │
│  ┌───────────────────────────────────────────────────┐  │
│  │  부트스트래퍼 (CLAUDE.md / .cursorrules /           │  │
│  │                GEMINI.md / AGENTS.md)              │  │
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
│  │  서브에이전트 15개 (Agent 도구로 디스패치)           │   │
│  │  ├─ 전문 8: plan / fe / be / db / planning /       │   │
│  │  │          test / evaluator / loop-action         │   │
│  │  └─ 범용 7: task / task-qa / task-action /         │   │
│  │             sdd-action / wtm /                     │   │
│  │             security-checker / convention-checker  │   │
│  │  (개별 역할은 §컴포넌트 유형 — 에이전트 표 참조)      │   │
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
| `skills/` | 독립 스킬 8개 + OPAL 스킬 45개 |
| `agents/` | 서브에이전트 15개 (전문 8 + 범용 7) |
| `community-skills/` | 커뮤니티 스킬 — clone-copy(git)로 사용자가 온디맨드 설치 (검색은 `npx skills find`). 사용자 등록분 `user-registry.json` 포함, install 불가침 |
| `references/` | 레지스트리·표준 문서 **19 엔트리**(최상위 17파일 + 하위 디렉토리 2). 범주별로 — **레지스트리 4종**(`skills.md`·`agents.md`·`mcps.md`·`tools.md`) + JSON 카탈로그 2종(`opal-skills-registry.json`·`community-skills-registry.json`) / **하네스 4종**(`opal-harness.md` + agentic·semi-agentic·interactive 변형) / **표준 문서**(`opal-doc-standard.md`·`header-standard.md`·`conventions-hub-model.md`·`test-tools-schema.yaml`) / **운영 정의**(`opal-pm.md`·`opal-model-mapping.md`·`bootstrapper-management.md`). 하위 디렉토리 2종: `harness/`(하네스 세부 규약 19파일 — 코딩 원칙·게이트·검증 등) · `pm/`(PM 프로세스 세부 6파일 — `orchestration.md`·`dispatch-process.md`·`context-injection.md`·`specialist-agent.md`·`code-scan-management.md`·`asis-analysis.md`(태스크 084 신설)) |
| `tools/` | CLI 도구 **19종**(도구 디렉토리 기준). 범주별로 — **파이프라인 집행**: `state-tool/`(현황판 JSON SSOT 관리·서브명령 11종), `test-tool/`(테스트 단계별 결정론 집행 — resolve/check/unit/integration + scenario-* 7종), `backlog-tool/`(oppl 2-루프 백로그 `backlog.json` SSOT), `opal-action-monitor/`(루프 액션 에이전트 `.oppl-run/` 진행 현황판 렌더 — 읽기 전용) / **환경·배포**: `opal-cli/`(update·doctor·uninstall·mcp·console 단일 진입점), `doctor/`(4섹션 환경 진단 — Dependencies/OPAL Paths/MCP/Bootstrappers), `git-sync-tool/`(워크스페이스 직속 git 저장소 일괄 안전 최신화 — clean+ff-only, dirty/diverged/detached는 skip 후 보고만), `improve-tool/`(PM 개선 루프 record/list/show — scope local/fw 2원 분기), `worktree-tool/`(태스크별 코드 작업공간 git worktree 격리 — create/list/status/remove 4서브명령. `.opal/worktree.json` 선언 기반 multi-repo(레포별 worktree)·monorepo(sparse-checkout) 2 layout 분기, `remove`는 dirty·unpushed·미머지 3중 가드로 거부하고 `--force`로만 우회, `setup[]`은 실행하지 않고 `pending_setup`으로 열거만 — lazy) / **탐색·연동**: `skill-registry/`(스킬 레지스트리 조회·병합 로드 + `scan-risk` — 커뮤니티 스킬 설치 전 위험 패턴 1층 하드 필터, `context` 태그로 오탐 억제), `tool-scan/`(capability 검색·live 사용법), `opal-agent/`(claude·gemini·codex·grok headless 서브에이전트 호출 라이브러리+CLI), `cmux-tool/`(cmux browser 래퍼 — 3모드 + user_owned 시그널), `playwright-tool/`(웹 페이지 수집 CLI — wtm 폴백 2단계), `xlsx-tool/`, `date/`(현재 일시 취득) / **지식·코드 지도**: `brain-tool/`(프로젝트 브레인 지식 위키 결정론적 집행), memory-tool/ — 메모리 인덱스·히스토리 결정론적 집행·docs/brain 졸업 워크플로우. CLOSE 마지막 행 mark 시 state-tool이 이 도구를 subprocess로 직접 호출해 작업 히스토리 행을 자동 생성한다(생성=도구 / `result` 보강=PM, 실패해도 mark 비차단), code-scan/ — @header 조회 + **헤더 작성층**(discover/scaffold/target/validate·인라인 및 `.opal/code-map/` 2소스) + **샤드 분할층**(`split --plan`/`--groups`, `init`). 기록 소스는 `.opal/code-scan.json`의 전역 `headerSource`(`inline`\|`manifest`) 단일 키가 결정하며 미설정 시 전 명령 차단(`init`으로 초안 생성). 매니페스트는 예약 폴더 `_shards/` 아래 **의미 단위 샤드로 분산** 가능하며(베이스가 `shards` 라벨 배열로 선언, 미선언 자산은 무변경), 과대 매니페스트는 `shardPolicy`(프로젝트 `.opal/code-scan.json` > 전역 `~/.opal/setting.json` > 코드 상수 3단 우선순위, 셀 단위 머지)의 **바이트 초과 AND 엔트리 수 이상 2축**으로 비차단 열거되며 `split --plan`(5단계 제안 사다리) → `--groups`(원자적 집행)로 분할하며, `--plan`은 `op-data-dictionary` 산출물(표준단어사전.md)을 **읽기 전용·옵셔널**로 대조한다(부재 시 건너뜀 — code-scan이 `.opal/` 밖 문서를 읽는 첫 사례). 구 위치 `index.json`의 `manifestMaxBytes`는 값을 읽지 않고 안내만 한다. — **도구 외 보조 스크립트**(위 19종에 포함하지 않음): `check-env.js`(Node.js 환경 체크) · `requirements.txt`(Python 의존성 — venv 관리). |
| `.venv/` | Python 가상환경 (openpyxl, pandas, playwright 등 — requirements.txt로 관리) |
| `templates/` | 프로젝트 에이전트 템플릿 |

### Project Layer (`{프로젝트}/`)

개별 프로젝트의 컨텍스트. 프로젝트별로 다르다.

| 파일/디렉토리 | 내용 |
|--------------|------|
| `CLAUDE.md` / `.cursorrules` / `GEMINI.md` | 플랫폼 부트스트래퍼 (에이전트 로드 트리거) |
| `.opal/AGENT.md` | PM 프로필 (역할, 검토 기준, 금지사항) |
| `.opal/MEMORY.json` + `memory/` | 프로젝트 메모리 (히스토리, 피드백, 아키텍처 결정). 인덱스는 JSON SSOT, 본문은 `memory/*.md` |
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
| | opal-pilot-sdd (opsdd) | SDD 기반 오케스트레이터: TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE (7 Phase, Phase 4는 ACT 루프) |
| | opal-pilot-project-loop (oppl) | 루프 기반 프로젝트 오케스트레이터: 설계 루프(인터뷰→PRD→TRD→CONTRACT→백로그) → 실행 루프(태스크 반복, 종료조건 5종·3-SSOT tool-gated) |
| | opal-pilot-data-design (opdd) | DB 설계 파이프라인: 데이터 사전 확립 → 모델링(개념/논리/물리) → DDL·마이그레이션 6단계 |
| | opal-pilot-gc (opgc) | 경량 Pilot — 커밋 전 보안·컨벤션 진단 4단계 (진단 전담, 수정 없음) |
| **dev 단계** | op-dev-analysis | 코드베이스 분석 + 기술 컨텍스트 수집 |
| | op-dev-plan | 구현 계획 (PLAN+TODO 통합) |
| | op-dev-todo | 실행 체크리스트 확장 (Full Task 전용) |
| | op-dev-test-scenario | 테스트 시나리오 생성 |
| | op-dev-execute | 코드 실행 (체크포인트 기반) |
| | op-dev-wireframe | 와이어프레임 생성 |
| | op-dev-qa | Dev QA 검증 (코드 개발 산출물) |
| **데이터 단계** | op-data-dictionary | 표준사전·표준코드 관리(CRUD) — 표준단어/도메인/코드 사전 3종 md SSOT + xlsx 단방향 export |
| | op-data-model | DB 모델링 — 개념(Mermaid)/논리(Mermaid)/물리(DBML) 3모드 분리 발동 |
| | op-data-ddl | DDL·마이그레이션 생성 — 물리(DBML) 입력 → DBMS별 DDL + ORM 마이그레이션 |
| **범용 단계** | op-task | TASK.md 작성 |
| | op-task-qa | 범용 QA 검증 (도메인 무관 산출물) |
| | op-task-plan | 범용 계획 수립 (도메인 무관) |
| | op-task-execute | 범용 실행 (도메인 무관) |
| **SDD 단계** | op-sdd-spec | SPEC 단계 — SDD 명세 작성 |
| | op-sdd-verify | VERIFY 단계 — SDD 명세 검증 |
| | op-sdd-plan | SPEC-PLAN 단계 — SDD 구현 계획 수립 |
| | op-sdd-action-plan | ACT 전용 경량 PLAN — SPEC.md + SPEC-PLAN.md + TEST-SCENARIOS.md + ACT 정의 기반 (Phase 4 액션 에이전트 내부) |
| **보조 단계** | op-brain-ingest | CLOSE 단계 경량 워커 — 태스크 산출물을 프로젝트 brain에 자동 누적 |
| | op-scenario-gate | TEST-SCENARIO 목표-커버리지 루브릭 게이트 루프 — 결정론 커버리지 체크(test-tool) + 판단 루브릭 |
| | op-spec-validator | SDD 명세 검증 워커 — PRD/TRD 체크리스트 기반 완성도 판정 |
| **독립** | api-analyzer | 외부 API 7단계 분석 |
| | interview | 구조화된 Q&A 요구사항 수집 |
| | ui-designer | wireframe.md → React + shadcn/ui 구현 |
| | wireframe-builder | 정책서/요구사항 → wireframe.md |
| | web-to-markdown | 웹 페이지 마크다운 변환 |
| | erd-modeler | DB ERD 모델링 (개념→논리→물리→DDL) |
| | html-mockup | CDN 기반 정적 HTML 화면 빠른 생성 (태스크 컨텍스트 흡수 + 인터뷰) |
| | system-architecture-html | 시스템·인프라 레이어 구조 다이어그램 → 단일 자기완결 HTML |
| **OPAL** | opal-project-init (opi) | 프로젝트 초기화/최신화 |
| | opal-agent-creator | 에이전트 생성 파이프라인 |
| | opal-skill-creator | 스킬 생성 파이프라인 |
| | opal-onboarding | 에이전트 온보딩 |
| | opal-skill-manager | 스킬 관리 |
| | opal-brain (opbr) | 프로젝트 브레인 — 영속 지식 위키 생성·누적·질의·정비 |
| | opal-help (help) | 스킬 카탈로그 & 사용법 안내 (목록 Mode 1 / 개별 안내 Mode 2) |
| | opal-next (next) | 재진입 가이드 — 환경 상태 진단 후 다음 액션 권유 |
| | opal-improve (opim) | PM 개선 루프 — 관찰→분류→기록→보고→승인 5단계 (로컬 `.opal/` / FW `~/.opal/fw-inbox`) |
| | opal-action-status (opas) | 루프 액션 에이전트 진행 현황 발동층 — 자동 탐지 + 해석 보고 |
| | opal-workspace-sync | 워크스페이스 Git 일괄 동기화 — 직속 자식 저장소 안전 최신화(clean+ff-only) |

### 에이전트 (Agents)

독립 컨텍스트에서 자율 실행하는 서브에이전트. `AGENT.md` 단일 파일.

**범용 에이전트 (기존)**

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| opal-task-agent | advanced | 범용 워커 — 단계 스킬 실행 (폴백) |
| opal-task-qa-agent | light | 범용 QA 워커 — qa_skill로 QA 스킬 동적 실행 |
| opal-task-action-agent | advanced | 액션 에이전트 — oppd Phase 3 자율 실행 |
| opal-sdd-action-agent | advanced | SDD 액션 에이전트 |
| opal-wtm-agent | light | web-to-markdown 워커 (2단 폴백 — Phase 1 cmux-tool → Phase 2 playwright-tool CLI) |
| opal-security-checker | advanced | 보안 체크 — OWASP Top 10 / CWE Top 25 / SANS Top 25 Base + `docs/SECURITY.md` 누적 |
| opal-convention-checker | standard | 컨벤션 체크 — 프로젝트 `docs/CONVENTIONS.md` 유일 기준 (부재 시 초안 유도) |

**전문 에이전트 (Specialist)**

| 에이전트 | 모델 | 단계 | 영역 | 역할 |
|---------|------|------|------|------|
| opal-plan-agent | advanced | PLAN | 공통 | 코드 분석 + 기능 설계 + 에이전트 라우팅 |
| opal-fe-agent | standard | EXECUTE | FE | 프론트엔드 구현 전문 |
| opal-be-agent | advanced | EXECUTE | BE | 백엔드 구현 전문 |
| opal-db-agent | standard | PLAN, EXECUTE | DB | DB 모델 설계 + 마이그레이션 구현 |
| opal-planning-agent | advanced | EXECUTE | 기획 | 서비스 기획 산출물 작성/관리 |
| opal-test-agent | standard | TEST | 공통 | 테스트 전문 (BE/FE/E2E 모드) |
| opal-evaluator-agent | advanced | 명세 리뷰 (oppl G/D6) | 평가 | 계약·설계 루브릭 심판 — CONTRACT.md 루브릭절 기준 구현 전 판정 (verdict-only·readonly) |
| opal-loop-action-agent | advanced | 태스크 실행 (oppl Loop 2) | 공통 | 루프 액션 에이전트 — PM→루프 액션 에이전트→워커 계층에서 T1~T5+G를 태스크당 1회 디스패치로 완주 (내부 4축 디스패치, 3-SSOT 중 test-tool만 호출) |

### 커뮤니티 스킬 (Community Skills)

외부 조직이 제공하는 스킬. OPAL은 번들로 배포하지 않으며, 사용자가 `//skill-manager` 또는 `// 커맨드` 첫 호출 시 upstream 저장소에서 **clone-copy**(git clone → vendor 중첩 경로 복사)로 설치한다. 설치 가부는 **2축 판정**으로 결정한다 — ① 본문 위험 패턴 스캔(`skill-registry.js scan-risk`, 1층 하드 필터) ② 라이선스 확인. 두 축을 합쳐 **SAFE / CAUTION / RISKY / UNKNOWN 4단**으로 판정하며, SAFE는 자동 설치, CAUTION과 Unknown 라이선스는 확인 게이트, RISKY는 추천 후보에서 제외한다. 1층은 필요조건이며 사람 검토를 대체하지 않는다(산문 영역 위험 지시는 미탐 가능).

| 항목 | 값 |
|------|-----|
| 카탈로그 SSOT | [skills.sh](https://skills.sh/) — `npx skills find` (검색·업데이트 확인 전용) |
| 설치 방식 | clone-copy — `git clone --depth 1` → `{vendor}/{skill}/` 복사 + clone 시점 commit_sha 기록 (opal-skill-manager §설치, 알투 자동 호출 또는 `//skill-manager`) |
| 설치 위치 | `~/.opal/community-skills/{vendor}/{skill}/SKILL.md` (vendor 중첩 SSOT — flat 잔재는 `skill-registry.js migrate`로 정규화) |
| 레지스트리 (이원) | 프레임워크 카탈로그 `~/.opal/references/community-skills-registry.json` (install이 덮어써 갱신 전파) + 사용자 등록분 `~/.opal/community-skills/user-registry.json` (install 불가침 — 142 D-4, skill-registry가 병합 로드). 사용자 등록분은 기존 7필드에 판정 3필드(`trust`·`capabilities`·`scanned_at`)를 additive로 함께 기록한다 — 스키마 교체 없이 `validate`가 미지 필드를 무시하는 성질을 이용한다 |
| 라이선스 책임 | 사용자 설치 시점 발생 (OPAL repo는 third-party 코드 재배포 안 함) |

### 하네스 (Harness)

오케스트레이터가 공유하는 공통 인프라. `opal-harness.md`에 정의.

| 요소 | 역할 |
|------|------|
| Guards | 구현 금지 원칙, Git 사전 점검, 커밋 규칙 |
| Gates | 단계 게이트 (캡틴 승인), QA Gate, PM Gate |
| State | `state.json` 파이프라인 SSOT(state-tool) + STATE.md 저널, 세션 복원 |
| TASK 프로세스 | op-task 스킬로 TASK.md 작성 (오케스트레이터 직접 수행) |
| Observability | 스킬/에이전트 탐색 경로, 프로젝트 메모리 동기화 |

## 배포 모델

```
소스 (이 저장소)                    배포 대상 (~/.opal/)
─────────────────                  ──────────────────
skills/* (독립 8개) ──┐
opal/skills/* (45개)──┼─ install ─→  ~/.opal/skills/
opal/agents/* (15개)──┤              ~/.opal/agents/  (source 캐시 — 어댑터 재생성용)
opal/core/          ──┤              ~/.opal/AGENT.md
  references/       ──┤              ~/.opal/references/
opal/tools/         ──┤              ~/.opal/tools/
opal/templates/     ──┘              ~/.opal/templates/

opal/tools/requirements.txt ──────→  ~/.opal/.venv/ (Python 가상환경 생성/업데이트)

opal/bootstrapper/* ──── install ─→  ~/.claude/CLAUDE.md          (claude-bootstrap.md)
                                     ~/.cursor/rules/000-opal-agent.mdc (cursor-bootstrap.mdc)
                                     ~/.gemini/GEMINI.md          (gemini-bootstrap.md)
                                     ~/.codex/AGENTS.md           (codex-bootstrap.md)

opal/core/mcps/*    ──── install ─→  claude mcp add --scope user (Claude)
                                     gemini mcp add -s user (Gemini)
                                     codex mcp add (Codex)
                                     ~/.cursor/mcp.json (Cursor)
                                     ~/.gemini/antigravity/mcp_config.json (Antigravity)

# 어댑터 자동 생성 (실제 LLM 이 런타임에 읽는 곳)
~/.opal/agents/* ──── install (emit) ─→ ~/.claude/agents/{name}.md   (Claude Code 형식)
                                        ~/.cursor/agents/{name}.md   (Cursor 형식)
                                        ~/.gemini/agents/{name}.md   (Gemini 형식)
                                        ~/.codex/agents/{name}.md    (Codex 형식)
                                        + ~/.codex/config.toml [agents] 멱등 작성

# 커뮤니티 스킬은 install이 배포하지 않음. 사용자가 //skill-manager 또는 // 첫 호출로 설치:
~/.opal/community-skills/{vendor}/{skill}/  ←  clone-copy (git clone → 복사 + commit_sha)  ←  라이선스 확인 시 자동 / Unknown만 동의 게이트
```

`install-mac.sh`가 소스에서 `~/.opal/`로 통합 배포한다. 플랫폼별 디렉토리(`~/.claude/`, `~/.cursor/`, `~/.gemini/`, `~/.codex/`)에는 부트스트래퍼·MCP 설정과 함께 **에이전트 어댑터**가 배치된다.

**지원 플랫폼 4종**: Claude Code · Cursor · Gemini(Antigravity 포함) · Codex. Codex 경로는 `install_codex_agents()`(어댑터 emit + 모델 매핑 `light`=gpt-5.4-mini / `standard`=gpt-5.4 / `advanced`=gpt-5.5)와 `install_codex_config()`(`~/.codex/config.toml`의 `[agents]` 멱등 작성 — `max_concurrent_threads_per_session`/`max_depth`/`job_max_runtime_seconds`)로 구성되며, 부트스트래퍼는 `~/.codex/AGENTS.md`에 OPAL 마커 구간으로 삽입된다. `install_codex_config()`는 3분기(신규 append / 기존 `[agents]` 블록 내 legacy 키 in-place 치환 / 정식 키 보유 시 스킵)로 동작하여 기존 설치 머신도 정식 키로 마이그레이션한다.

**어댑터 확장 필드 통로**: `emit_platform_agent_adapter()`·`install_codex_agents()`의 frontmatter 재조립은 `OPAL_ADAPTER_FIELD_SPEC`(mac) / `$OpalAdapterFieldSpec`(windows) **JSON 스펙 상수 순회**로 수행된다. OPAL 필드 → 플랫폼 필드 변환은 필드명·값·배치 방식 3중 변환을 이 스펙 하나가 소유하며, emit은 배치 모드 3종(`key` / `model_param` / `omit`)에만 분기하고 플랫폼명 조건문을 두지 않는다. 스펙에 등재되지 않은 필드는 제거된다. 첫 확장 필드는 `effort`(Claude=`effort` / Codex=`model_reasoning_effort` / Cursor·Gemini=생략)이며, 새 필드 추가는 스펙 1행 추가로 끝난다. mac·windows 두 스크립트의 스펙 JSON은 센티넬 주석 구간으로 감싸 **바이트 동일**을 규약으로 하고 테스트가 이를 기계 검증한다. 변환 규칙 SSOT는 `opal/core/references/agents.md` §frontmatter 변환 규칙이다.

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
│  • 파서: MEMORY.json(JSON)·memory/*·PROJECT/AGENT.md      │
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

### 태스크 진행 통계 (태스크 103)

태스크 상세 패널과 대시보드가 `tasks/*/state.json` 파이프라인 행을 집계해 **병목 단계**와 **캡틴 대기 구간**을 수치로 드러낸다. 통계 전용 화면은 만들지 않고 기존 2화면을 확장했다. 읽기 전용 원칙은 유지된다(쓰기 동작 0건).

| 항목 | 값 |
|------|-----|
| 집계 코어 | `dashboard/backend/stats.py` — 집계 정의 SSOT. **import는 `__future__`·`datetime`·`statistics` 3종뿐**(모델·라우터·캐시 미의존 → 순환 회피, 파일 I/O 0건). 공개 함수 7종 `parse_ts`·`format_duration`·`owner_series`·`row_durations`·`task_static_stats`·`task_live_stats`·`workflow_stats`. 라우터 2곳(`tasks.py`·`dashboard.py`)과 FE는 계산하지 않고 이 모듈만 소비한다 |
| 분해축 | **총 리드타임 = 작업(`owner`가 `PM`·`auto`) + 대기(`owner`가 `user`)**. 병목은 작업 계열, 대기 축소는 대기 계열을 본다 |
| 소요 계산 | 앵커 `created_at` → 각 done 행, 직전 done 행 대비 차이. `status != "done"` 전부 제외. **역행 타임스탬프는 0으로 clamp**(실측 1건) |
| 비교 단위 | **워크플로우(`skill`)별 분리** — opd 7단계 / opds 5단계 / opp 4단계로 파이프라인 구성이 달라 혼합 집계는 제공하지 않는다. 대표값은 중앙값(평균은 보조), `n<5`는 「표본 부족」 표기 |
| 모수 | **대시보드는 완료 태스크만**(진행 중은 건수만 별도), **태스크 상세는 실시간**. 실시간 함수는 전부 `now` 파라미터를 받아 결정론을 유지한다 |
| 실시간 대기 귀속 | 완료 행은 `owner`, 현재 행은 `key`의 `*.user_confirm` 패턴 — `pending` 행 `owner`는 `state-tool init` 기본값(`PM`)이라 신뢰할 수 없다 |
| 필드 명명 | **원천 용어 정렬** — 응답 키는 `state.json` 스키마 용어(`skill`·`timestamp`·`row_id`). 사표 필드 `updated_at`·`row`는 deprecated 별칭으로 존치하되 값을 채운다. 「워크플로우」는 UI 표시 라벨 전용 |
| 표시 문자열 | **BE 소유** — `*_minutes` + `*_label` 쌍으로 내리고 `format_duration`을 `stats.py` 단일 지점에 둔다(FE 무계산) |
| 캐시 | 정적 파생만 캐시(`source_path`에 태스크 `state.json` 경로 전달), **실시간 파생은 캐시 밖에서 조립**. 이 과정에서 `cache.py`의 mtime 비교가 monotonic 파생값과 epoch를 직접 비교하던 결함을 wall-clock 기준으로 교정했다 |
| 검증 | 기준일 스냅샷 `STATS-BASELINE.md`(태스크 산출물, 런타임 미배치)와 대조. 모수는 **태스크 ID 목록으로 동결**해 후속 태스크 완료로 중앙값이 이동해도 검증이 깨지지 않는다 |

| 항목 | 값 |
|------|-----|
| 소스 | `{프로젝트}/dashboard/` (frontend: React+TS+Vite+shadcn / backend: FastAPI) |
| 배포 | `~/.opal/dashboard-server/` (install이 FE 빌드+BE 복사, venv는 `~/.opal/.venv` 공유) |
| 기동 | `opal-cli console {start\|stop\|status\|open\|scan\|log}` (127.0.0.1:7823) — `log`는 데몬 로그 조회 |
| 프로젝트 식별 | `.opal/AGENT.md` 마커 디스크 스캔 (`~/.opal/console.config.json` scan_roots/depth/exclude) — config는 `opal-cli console scan [기준경로...]`이 생성·머지 갱신(기존 roots 보존, `--prune` 옵트인)하며 install(`install_dashboard`)이 1회 자동 실행. `start`는 config 부재 시 scan 안내 출력 |
| 원칙 | 읽기 전용(쓰기/편집은 2차) · 데이터 SSOT는 각 프로젝트 파일 · 데몬은 도구 오케스트레이터 |
| 디자인 토큰 | 시그니처 3색(`--brand-primary/secondary/tertiary`)을 `:root` 1곳 전역 CSS 변수화 (교체 용이) |

## 외부 의존 서비스

OPAL이 동작·배포 시 의존하는 외부 자원이다. 신규/변경 시 이 표를 SSOT로 사용하고, 설치 스크립트와 PROJECT.md "프로젝트 문서" 테이블의 정합성을 유지한다.

### MCP 서버 (`opal/core/mcps/*.json`)

| 이름 | 용도 | 적용 플랫폼 | 설치 방식 |
|------|------|----------|----------|
| context7 | 라이브러리·프레임워크 최신 문서 조회 | Claude / Cursor / Gemini / Antigravity / Codex | config_merge |
| playwright | 브라우저 자동화 (JS 렌더링 페이지 크롤링 — wtm browser 모드) | Claude / Cursor / Gemini / Antigravity / Codex | config_merge |
| shadcn | shadcn/ui 컴포넌트 검색·조회·설치 | Claude / Cursor / Gemini / Antigravity / Codex | config_merge |
| sequential-thinking | 단계적 사고 도구 | Claude / Cursor / Gemini / Antigravity / Codex | config_merge |
| (기타) | `opal/core/mcps/*.json` 참조 | - | install 스크립트가 자동 처리 |

`install_type`은 4종 모두 `config_merge`다 — json 정의는 플랫폼 중립이며, **CLI 등록(`claude mcp add` 등)은 install 스크립트의 플랫폼 분기가 선택하는 집행 수단**이지 MCP 정의의 속성이 아니다.

설치 진입점: `install-mac.sh`의 `[2] MCP 서버 설정` 메뉴(대상 5종 — claude·cursor·gemini·antigravity·codex). 등록 방식은 플랫폼별 — `claude mcp add --scope user` / `gemini mcp add -s user` / `codex mcp add` / Cursor·Antigravity는 `mcp.json` config_merge.

### Anthropic Claude API

- 일부 스킬·에이전트가 Claude API를 직접 호출하는 경우 사용 (해당 시 환경변수 `ANTHROPIC_API_KEY` 필요).
- 모델 매핑: `~/.opal/references/opal-model-mapping.md` — 플랫폼 중립 레벨(`light`/`standard`/`advanced`) ↔ 모델(`haiku`/`sonnet`/`opus`).

### Python 의존성 (`opal/tools/requirements.txt`)

- **요구 Python 3.11 이상 (권장 3.14)** — `mcp` SDK가 Python 3.10+ 를 요구하므로 하한을 3.11로 둔다.
- 설치 스크립트가 인터프리터를 탐색해 하한을 검사하고, **미달 시 설치를 중단하고 설치 방법을 안내한다** (Node.js와 달리 경고 후 진행하지 않는다). macOS는 Homebrew, Windows는 winget으로 권장 버전 자동 설치를 시도하며 `OPAL_AUTO_INSTALL_PYTHON=0` 으로 옵트아웃한다. Linux는 자동 설치 없이 안내만 한다.
- 기존 venv도 설치 시 버전을 재검증하여 하한 미달이면 폐기 후 재생성한다.
- 설치 시 `~/.opal/.venv/`에 Python venv를 생성하고 의존성을 설치한다.
- 주요 패키지: Playwright, openpyxl, pandas (xlsx-tool), MCP SDK 등.
- Playwright 브라우저(Chromium / Firefox / WebKit)는 별도 설치 명령으로 다운로드: `~/.opal/.venv/bin/playwright install chromium`.

### Node.js 도구

- `skill-registry`, `state-tool`, `check-env.js` 등 일부 CLI 도구가 Node.js 18+ 의존.
- 설치 스크립트가 `node --version`을 점검하고 누락 시 경고만 출력 (강제 종료하지 않음).

### 배포 채널

| 채널 | 단계 | 상태 | 비고 |
|------|------|------|------|
| GitHub Releases | 1차 | **현행** | 태그 기반 tarball + sha256sums.txt + `actions/attest-build-provenance@v2`. **소비 규약(DL-CONTRACT)**: 설치·업데이트는 릴리즈 자산(`opal-{tag}.tar.gz`)을 1순위로 내려받아 같은 파일의 체크섬으로 검증한다 — 다운로드 대상과 검증 대상이 동일해야 하며, 자산이 없으면 자동 아카이브(`archive/refs/tags`)로 폴백하고 이때는 UNVERIFIED 정책(옵트인·대화형 프롬프트·비대화형 거부)을 적용한다. 자산명은 하드코딩하지 않고 `sha256sums.txt`의 파일명 컬럼에서 파생한다 |
| `opal-cli` CLI | 1차 | **현행** | `update`/`doctor`/`uninstall`/`mcp`/`console` 단일 진입점 (`~/.opal/bin/opal-cli`) — 신규 설치는 One-liner installer. 다운로드 소스 규약은 `GitHub Releases` 행 참조 |
| One-liner installer | 1차 | **현행** | `curl \| bash`(mac/linux) / `iex (irm)`(Windows) 진입점 (`scripts/install.sh`, `scripts/install.ps1`). 다운로드 소스 규약은 `GitHub Releases` 행 참조 |
| Homebrew tap | 2차 | 예정 | macOS 사용자 대상 `brew install opal-cli` (명칭은 별도 결정) |
| npm 패키지 | 후속 | 예정 | cross-platform 통합 |

> 결정 근거: 태스크 138(opi) 검토 → 139(P1)에서 1차 채널 구현 완료 — 캡틴 결정 D1 = `opal-cli` 명칭(Homebrew core `opal`/opalrb 충돌 회피), D2 = `https://github.com/ceo4ever/opal`.

## 디렉토리 구조

```
opal/                                    ← 이 저장소
├── README.md                            저장소 소개
├── LICENSE                              라이선스
├── VERSION                              배포 버전 (릴리스 태그 기준)
├── CLAUDE.md                            이 프로젝트의 Claude 부트스트래퍼
├── GEMINI.md                            이 프로젝트의 Gemini 부트스트래퍼
├── skills/                              독립 스킬 (8개, 파이프라인 없이 단독 사용)
│   ├── api-analyzer/                    외부 API 분석
│   ├── erd-modeler/                     DB ERD 모델링 (개념→논리→물리→DDL)
│   ├── html-mockup/                     CDN 기반 정적 HTML 화면 생성
│   ├── interview/                       요구사항 수집
│   ├── system-architecture-html/        시스템·인프라 구조 다이어그램 HTML 생성
│   ├── ui-designer/                     UI 구현
│   ├── web-to-markdown/                 웹→마크다운
│   └── wireframe-builder/               와이어프레임 설계
├── opal/                                OPAL 코어
│   ├── bootstrapper/                    플랫폼별 부트스트래퍼 (claude / cursor / gemini / codex + gemini-hardening)
│   ├── core/                            에이전트 코어 + 레퍼런스 + MCP
│   │   ├── AGENT.md                     에이전트 핵심 정의 (부트스트랩 SSOT)
│   │   ├── PRINCIPLES.md                헌법 — 최상위 행동 원칙
│   │   ├── identity-template.md         온보딩용 정체성 템플릿
│   │   ├── setting.default.json         전역 setting 기본값
│   │   ├── references/                  레지스트리·표준 19 엔트리 (harness/ 19파일 · pm/ 6파일 포함)
│   │   ├── mcps/                        MCP 설정 4종 (context7, playwright, shadcn, sequential-thinking)
│   │   └── hooks/                       Claude Code hooks 설정
│   ├── tools/                           CLI 도구 19종 (+ check-env.js 보조 스크립트, requirements.txt)
│   │   ├── state-tool/                  파이프라인 현황판 JSON SSOT (서브명령 11종)
│   │   ├── test-tool/                   테스트 단계 결정론 집행 (resolve/check/unit/integration + scenario-*)
│   │   ├── backlog-tool/                oppl 백로그 backlog.json SSOT
│   │   ├── opal-action-monitor/         루프 액션 에이전트 진행 현황판 (읽기 전용)
│   │   ├── brain-tool/                  프로젝트 브레인 지식 위키 집행
│   │   ├── memory-tool/                 메모리 인덱스·히스토리 집행 + docs/brain 졸업
│   │   ├── code-scan/                   @header 조회·작성층 + 매니페스트 샤드 분할층
│   │   ├── opal-cli/                    update/doctor/uninstall/mcp/console 단일 진입점
│   │   ├── doctor/                      환경 진단 4섹션
│   │   ├── git-sync-tool/               워크스페이스 git 일괄 안전 최신화 (clean + ff-only)
│   │   ├── improve-tool/                PM 개선 루프 record/list/show (scope local/fw)
│   │   ├── skill-registry/              스킬 레지스트리 CLI (skill-registry.js)
│   │   ├── tool-scan/                   도구 capability 검색·live 사용법
│   │   ├── opal-agent/                  claude/gemini/codex/grok headless 호출 라이브러리 + CLI
│   │   ├── cmux-tool/                   cmux browser 래퍼 (run.sh) — 3모드(A/B/C) + user_owned 시그널
│   │   ├── playwright-tool/             웹 페이지 수집 CLI (wtm 폴백 2단계)
│   │   ├── xlsx-tool/                   xlsx 읽기/쓰기 CLI (run.sh)
│   │   ├── date/                        현재 일시 취득 (date.js)
│   │   ├── check-env.js                 Node.js 환경 체크
│   │   └── requirements.txt             Python 의존성 (venv 관리)
│   ├── skills/                          OPAL 스킬 (45개)
│   │   ├── opal-pilot-dev/              오케스트레이터: Full Task (opd)
│   │   ├── opal-pilot-dev-short/        오케스트레이터: Short Task (opds)
│   │   ├── opal-pilot-dev-wireframe/    오케스트레이터: Wireframe UI (opdw)
│   │   ├── opal-pilot-write-tech/       오케스트레이터: Write-Tech (opwt)
│   │   ├── opal-pilot-project/          오케스트레이터: Project (opp)
│   │   ├── opal-pilot-project-dev/      오케스트레이터: Project Dev (oppd)
│   │   ├── opal-pilot-project-loop/     오케스트레이터: Project Loop (oppl)
│   │   ├── opal-pilot-sdd/              오케스트레이터: SDD (opsdd)
│   │   ├── opal-pilot-data-design/      오케스트레이터: DB 설계 (opdd)
│   │   ├── opal-pilot-gc/               오케스트레이터: 보안·컨벤션 진단 (opgc)
│   │   ├── op-dev-{analysis,plan,todo,execute,test-scenario,qa,wireframe}/
│   │   │                                dev 단계 스킬 (7개)
│   │   ├── op-data-{dictionary,model,ddl}/
│   │   │                                데이터 설계 단계 스킬 (3개)
│   │   ├── op-task{,-plan,-execute,-qa}/ 범용 단계 스킬 (4개)
│   │   ├── op-sdd-{spec,verify,plan,action-plan}/
│   │   │                                SDD 단계 스킬 (4개)
│   │   ├── op-{brain-ingest,scenario-gate,spec-validator}/
│   │   │                                보조 단계 스킬 (3개)
│   │   ├── opal-project-init/           프로젝트 초기화 (opi)
│   │   ├── opal-agent-creator/          에이전트 생성
│   │   ├── opal-skill-creator/          스킬 생성
│   │   ├── opal-skill-manager/          스킬 관리
│   │   ├── opal-onboarding/             에이전트 온보딩
│   │   ├── opal-brain/                  프로젝트 브레인 (opbr)
│   │   ├── opal-help/                   스킬 카탈로그·사용법 안내
│   │   ├── opal-next/                   재진입 가이드
│   │   ├── opal-improve/                PM 개선 루프 (opim)
│   │   ├── opal-action-status/          루프 액션 진행 현황 (opas)
│   │   └── opal-workspace-sync/         워크스페이스 Git 일괄 동기화
│   ├── agents/                          OPAL 에이전트 (15개: 전문 8 + 범용 7)
│   │   ├── opal-plan-agent/             전문: PLAN 설계 (advanced)
│   │   ├── opal-fe-agent/               전문: FE 구현
│   │   ├── opal-be-agent/               전문: BE 구현 (advanced)
│   │   ├── opal-db-agent/               전문: DB 설계+구현
│   │   ├── opal-planning-agent/         전문: 서비스 기획 (advanced)
│   │   ├── opal-test-agent/             전문: 테스트 (도메인별 모드)
│   │   ├── opal-evaluator-agent/        전문: 명세 심판 (advanced, verdict-only)
│   │   ├── opal-loop-action-agent/      전문: 루프 액션 (advanced, oppl Loop 2)
│   │   ├── opal-task-agent/             범용 워커 (advanced, 폴백)
│   │   ├── opal-task-qa-agent/          범용 QA 워커
│   │   ├── opal-task-action-agent/      액션 에이전트 (oppd)
│   │   ├── opal-sdd-action-agent/       SDD 액션 에이전트
│   │   ├── opal-wtm-agent/              웹→마크다운 워커 (cmux → playwright 2단 폴백)
│   │   ├── opal-security-checker/       보안 체크 (OWASP/CWE/SANS + docs/SECURITY.md)
│   │   └── opal-convention-checker/     컨벤션 체크 (docs/CONVENTIONS.md 유일 기준)
│   └── templates/                       프로젝트 에이전트 템플릿
├── dashboard/                           OPAL Console (로컬 프로젝트 관리 대시보드 — 태스크 021)
│   ├── frontend/                        React + TS + Vite + shadcn/ui (7개 화면 — 설정 포함, 태스크 061)
│   └── backend/                         FastAPI 데몬 (스캐너 + read-only 어댑터 + 파서)
├── cursor-rules/                        Cursor 프로젝트 규칙 템플릿
├── scripts/                             설치 스크립트
│   ├── install.sh                       One-liner installer 진입점 (mac / linux)
│   ├── install.ps1                      One-liner installer 진입점 (Windows)
│   ├── install-mac.sh                   통합 설치 본체
│   ├── install/                         플랫폼 어댑터 (linux.sh · macos.sh · windows.ps1)
│   ├── merge-hooks.py                   Claude Code hooks 병합
│   └── tests/                           설치 스크립트 테스트
├── memory/                              이 프로젝트의 메모리 본문 (memory/*.md)
├── tasks/                               태스크 산출물
├── docs/                                프로젝트 문서
│   └── architecture-diagram/            정본 10계층 구조도 HTML (태스크 086)
└── .opal/                               이 프로젝트의 PM 프로필 + 메모리 인덱스(MEMORY.json)
```

---

## 변경이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-09-03 13:15 | **§배포 구조에 「어댑터 확장 필드 통로」 서술 신설** — `emit_platform_agent_adapter()`·`install_codex_agents()`의 frontmatter 재조립이 `name`/`description`/`model` 3필드 하드코딩에서 `OPAL_ADAPTER_FIELD_SPEC` JSON 스펙 순회로 전환됐다. 필드명·값·배치 3중 변환을 스펙 하나가 소유하고 emit은 배치 모드 3종(`key`/`model_param`/`omit`)에만 분기하여 플랫폼명 조건문을 두지 않는다. 첫 확장 필드 `effort`(Claude=`effort` / Codex=`model_reasoning_effort` / Cursor·Gemini=생략) 적용. mac·windows 스펙 JSON은 센티넬 구간 바이트 동일을 규약으로 하며 테스트가 기계 검증한다. 함께 `install_codex_config()` 서술을 legacy `max_threads` → `max_concurrent_threads_per_session`으로 정정하고 3분기 마이그레이션(신규 append / 기존 블록 in-place 치환 / 스킵)을 명시. `docs/architecture-diagram/opal_framework_architecture.html:599`의 동일 legacy 키 표기도 정정 (태스크 105) |
| 2026-09-03 00:59 | **§커뮤니티 스킬 설치 판정을 라이선스 1축 → 2축·4단으로 갱신** — 본문 위험 패턴 스캔(`skill-registry.js scan-risk` 신설, 1층 하드 필터)과 라이선스를 합쳐 SAFE/CAUTION/RISKY/UNKNOWN 4단으로 판정한다. 1층은 필요조건이며 사람 검토를 대체하지 않음을 명시(산문 영역 미탐 한계). §레지스트리(이원) 행에 사용자 등록분 판정 3필드(`trust`·`capabilities`·`scanned_at`) additive 기록 반영 — `validate`가 미지 필드를 무시하는 성질을 이용해 스키마 교체 없이 확장. §핵심 디렉토리 `tools/` 표 `skill-registry/` 항목에 `scan-risk` 반영. 근거 — `opal/skills/opal-skill-manager/SKILL.md` v1.5(§1·§2 6단 흐름 재작성), `opal/tools/skill-registry/skill-registry.js`(`scan-risk` 서브명령) (태스크 105) |
| 2026-08-25 17:55 | **§OPAL Console에 「태스크 진행 통계」 절 신설** — 태스크 상세·대시보드가 `tasks/*/state.json`을 집계해 병목 단계와 캡틴 대기 구간을 표시한다. 집계 코어 `dashboard/backend/stats.py` 신설(표준 라이브러리 3종만 의존해 순환 회피, 공개 함수 7종, 라우터·FE는 소비만) · 분해축 「총 리드타임 = 작업 + 대기」 · 워크플로우별 분리 집계(혼합 미제공, opd 7·opds 5·opp 4단계로 구성 상이) · 대시보드는 완료 태스크 모수 / 상세는 실시간(`now` 주입 결정론) · 실시간 대기 귀속은 `key`의 `*.user_confirm` 패턴(`pending` 행 `owner`는 `init` 기본값이라 비신뢰) · 필드 명명 원천 용어 정렬(`skill`·`timestamp`·`row_id`, 사표 필드는 별칭 존치) · 표시 문자열 BE 소유 · 정적만 캐시하고 실시간은 캐시 밖 조립. 부수 교정 — `cache.py`의 mtime 비교가 monotonic 파생값과 epoch를 직접 비교해 `source_path` 지정 시 상시 무효화되던 결함을 wall-clock 기준으로 수정 (태스크 103) |
| 2026-08-23 13:09 | `harness/` 파일 수 정정 — 트리 뷰 `harness/ 17파일` → **19파일**(선재 stale 1건 + 태스크 100 `analysis-core.md` 신규 1건 실측 반영). §핵심 디렉토리 `references/` 행(`:80`)도 같은 줄 안에 `harness/`(하네스 세부 규약 **17파일**) 언급을 별도로 갖고 있어 함께 **19파일**로 정정 — 동일 줄에 '17파일'이 2회 등장하며 앞의 '최상위 17파일'은 references/ 최상위 실측값이라 무변경, 뒤의 harness/ 수치만 정정. **정정 경위**: 최초 조치에서 앞의 1건만 확인하고 무변경으로 판단했으나 TEST S-28이 잔존을 검출해 보완(H-12 재현). 태스크 100 |
| 2026-08-16 13:36 | 하네스 표 State 행 서술 정정 — "STATE.md 상태 관리" → "`state.json` 파이프라인 SSOT(state-tool) + STATE.md 저널", 세션 복원. STATE.md는 파이프라인 현황(행 상태·진행·다음 액션)의 SSOT가 아니라 의사결정 로그·블로커를 담는 저널이며, 현황 조회는 `state-tool show`가 담당한다 (094) |
| 2026-08-15 16:35 | `worktree-tool` 신설 반영 — 도구 인벤토리 **18종 → 19종**(§핵심 디렉토리 `tools/` 행 '환경·배포' 범주에 항목 추가 + 디렉토리 트리 1행). 태스크별 코드 작업공간을 `{프로젝트}/.opal-worktrees/task_{NNN}/`에 git worktree로 격리하는 `--worktree`/`--wt` 축(모드 축과 직교, `opal-harness.md` §2.5)의 집행 도구다 (Task 092) |
| 2026-09-04 23:05 | OPAL 스킬 수 42개 → **45개** 정합 3지점(§폴더 구조 표·§배포 모델 다이어그램·§디렉토리 트리) — 실측 대조 결과 신설 `opal-code-map-builder` 반영 전에도 이미 2건 드리프트였다(문서 42 vs 실측 44). 신설분 +1을 더해 45로 확정 (106) |
| 2026-08-11 13:25 | opi 최신화 — 실측 1:1 대조 결과 32건을 전건 반영. 수량 정합(서브에이전트 12→**15개**, 내역 "전문 7 + 범용 4 + 도구성 1"→**전문 8 + 범용 7** / 독립 스킬 5·6→**8개** / OPAL 스킬 24·25→**42개** / `tools/` 6→**18종**), **Codex 플랫폼 신설**(어댑터 emit·`~/.codex/config.toml` `[agents]`·`~/.codex/AGENTS.md` 부트스트래퍼·`codex mcp add` — 종전에는 지원 플랫폼 하나가 배포 모델 전 경로에서 비가시였다), 스킬 표에 미문서화 16종 추가(Pilot 2 + **데이터 단계 3종 그룹 신설** + **보조 단계 3종 그룹 신설** + OPAL 6 + 독립 2)하고 실물 없는 `op-sdd-tasks`를 `op-sdd-action-plan`으로 교체 + opsdd 파이프라인 단계명을 실측 7 Phase로 정정, model 2건 정정(`opal-task-agent`·`opal-be-agent` standard→**advanced**), wtm 폴백 3단→**2단**(WebFetch 제거), MCP 4종 적용 플랫폼을 **5종**으로 통일하고 미배포 `Notion` 행 삭제 + `install_type` 전건 `config_merge` 명시, `references/`를 6종 열거에서 **범주 서술**로 전환(`harness/` 17파일 · `pm/` 6파일 포함), `console` 서브명령에 `log` 추가, 디렉토리 트리 재작성(부재하는 루트 `agents/` 삭제 · `opal/core/` 직속 4파일 · 저장소 루트 6항목 · `scripts/` 6엔트리 · frontend 6→**7화면** · `docs/architecture-diagram/` · 미종료 코드펜스 복구), 변경이력 **날짜 역순 정렬 복구** (Task 089) |
| 2026-08-11 | tools/ 표 memory-tool 행에 **CLOSE 자동 연결** 반영 — CLOSE 마지막 행 mark 시 state-tool이 memory-tool을 subprocess로 직접 호출해 작업 히스토리 행을 결정론적으로 생성한다. 종전에는 히스토리 갱신이 ambient 트리거로만 정의되어 커밋 뒤로 밀렸고 태스크마다 히스토리 전용 후속 커밋이 1건 추가됐다. 판단이 개입하지 않는 title·date·stage·path는 도구가 채우고 `result`만 PM이 보강하며(`"(PM 보강 대기)"` 플레이스홀더 + 실행 가능한 리마인더), 연동 실패는 `history_link.warning`으로만 표면화되어 mark를 차단하지 않는다. pilot 10종 CLOSE 스펙 무수정 — 도구 계층 단일 지점 변경으로 전 pilot 동시 적용 (Task 088) |
| 2026-08-10 | Python 의존성 절에 **요구 버전(3.11 이상, 권장 3.14)과 미달 시 설치 중단 동작** 명시 — 종전에는 설치 스크립트가 PATH의 `python3`를 버전 확인 없이 사용해 macOS 기본 3.9.6으로 venv가 생성되고 `mcp>=1.1.0` 의존성 해석에서 실패했다. 인터프리터 탐색·하한 게이트·기존 venv 재검증을 신설하고, 자동 설치를 macOS(Homebrew)·Windows(winget) 어댑터로 대칭화했다(Linux는 안내만, 옵트아웃 `OPAL_AUTO_INSTALL_PYTHON=0`). Node.js 절이 "경고만 출력"인 것과 달리 Python은 강제 중단이므로 서술 비대칭을 해소 (Task 087) |
| 2026-08-10 22:59 | §시스템 구성에 **정본 시각 자산 포인터** 신설 — 10계층 전체 구조도 `docs/architecture-diagram/opal_framework_architecture.html`(`system-architecture-html` 스킬 산출)를 정본으로 명시하고, 기존 ASCII 다이어그램은 **진입 흐름 요약본**으로 위치를 낮췄다. 종전에는 ASCII와 HTML이 상호 포인터 없이 병존해, 정본을 1종으로 통일한 뒤에도 ASCII가 2차 진실로 굳을 위험이 있었다. 디렉토리 트리 `docs/` 하위에 `architecture-diagram/` 반영 (Task 086) |
| 2026-08-07 | 배포 채널 표에 **다운로드 소스 규약(DL-CONTRACT)** 명시 — 설치·업데이트 3경로(`install.sh`·`install.ps1`·`opal-cli update`)가 릴리즈 자산을 1순위로 소비하고 같은 파일의 체크섬으로 검증하도록 정합. 종전에는 체크섬이 `git archive` 산출 자산에 대해 발행되는데 스크립트는 GitHub 자동 아카이브를 받아 검증이 구조적으로 불가능했다(`opal-cli update` 하드 실패 / `install.ps1` 예외 중단 / `install.sh` 무결성 검증 무음 스킵). 자산명은 `sha256sums.txt` 파일명 컬럼에서 파생하고, 자산 부재 시 자동 아카이브 폴백 + UNVERIFIED 정책(옵트인·프롬프트·비대화형 거부)을 유지하며, 아카이브 상위 디렉토리 유무에 따라 `--strip-components`를 자동 판정한다 (Task 085) |
| 2026-08-06 11:33 | Global Layer `references/` 행에 `pm/` 하위 디렉토리 반영 — PM 대화형 AS-IS 분석 워크플로우 `opal/core/references/pm/asis-analysis.md`(5단계 SSOT + 읽기전용 수집 예외) 신설. 종전에는 `references/`를 최상위 6파일 열거로만 서술해 `harness/`·`pm/` 하위 디렉토리의 존재 자체가 드러나지 않았고, 신설 문서가 아키텍처 문서에 반영될 자리가 없었다 (Task 084) |
| 2026-08-04 | tools/ 표 code-scan 행에 샤드 정책 확장 반영 — `split`(제안 `--plan`/집행 `--groups`)·`init`(비대화형 설정 초안) 서브명령 신설(13→15), 과대 매니페스트 판정을 `shardPolicy` 3단 우선순위(프로젝트 > 전역 `~/.opal/setting.json` > 코드 상수, 셀 단위 머지) 기반 **바이트 초과 AND 엔트리 수 이상 2축**(비차단)으로 정교화, `split --plan`의 5단계 제안 사다리 + `op-data-dictionary` 표준단어사전.md 옵셔널·읽기 전용 대조(code-scan이 `.opal/` 밖 문서를 읽는 첫 사례) 반영, 구 위치 `manifestMaxBytes` 폐기 안내. code-scan v1.6.0 (Task 083) |
| 2026-08-03 | tools/ 표 code-scan 행에 매니페스트 샤딩 반영 — 예약 폴더 `_shards/` 의미 단위 분산(베이스 `shards` 라벨 배열 선언, `resolveShards` 1곳 봉인, 미선언 자산 바이트 동일 하위호환) + `index.json` 최상위 `manifestMaxBytes` 파일당 크기 상한 비차단 열거. code-scan v1.5.0 (Task 082) |
| 2026-08-02 | tools/ 표 code-scan 행에 헤더 소스 단일화 반영 — 기록 소스를 `.opal/code-scan.json` 전역 `headerSource`(`inline`\|`manifest`) 단일 키가 결정하고 스코프별 오버라이드를 제거, 미설정·무효값 시 전 명령 차단. `readonly` 스코프 플래그 폐기 (Task 080) |
| 2026-07-28 | 프로젝트 메모리 SSOT 전환 — Project Layer 표 `.opal/MEMORY.md` → `.opal/MEMORY.json`(인덱스는 JSON SSOT·본문은 `memory/*.md`), Console 파서 서술을 마크다운 파서에서 `MEMORY.json`(JSON) 파싱으로 정정 (Task 078) |
| 2026-07-28 | `tools/` 표 code-scan 행 현행화 — @header 조회에 더해 **헤더 작성층**(discover/scaffold/target/validate) 및 인라인·외부 소스 코드 지도(`.opal/code-map/`) 2소스 해석 반영 (Task 077) |
| 2026-07-17 | 전문 에이전트 표에 opal-loop-action-agent 행 추가 — oppl Loop 2 루프 액션 에이전트, PM→루프 액션 에이전트→워커 계층 반영 (Task 065) |
| 2026-07-17 | 커뮤니티 스킬 설치 방식 clone-copy 전환 — `npx skills add` 제거(경로 지정 불가 실측·D4), vendor 중첩 SSOT + migrate 정규화, 레지스트리 이원화(카탈로그=references / 사용자 등록분=community-skills/user-registry.json·install 불가침), npx는 find/check 전용 (Task 064) |
| 2026-07-15 | OPAL Console 브레인 세션 단순화 — "이력" 행을 **휘발성 단일 세션(미영속)**으로 전환(localStorage 이력·멀티대화 관리 제거, mount·새 대화마다 새 session_id, 단일 대화창 멀티턴 유지), 프라임 연결 풀 크기 1→2 + `prewarm()` need-based 충전(연속 새대화 즉시 웜, 상수만 상향 시 풀 1까지만 차던 결함 수정) (Task 063) |
| 2026-07-14 | OPAL Console 7번째 화면 "설정" 신설 절 추가 — 설정 라우터 쓰기 격리(화이트리스트)·프라임 풀 토글 단일 기능(캡틴 범위 확정: console.config·로컬 설정 편집은 수동 유지, 후속 단위 추가)·Lock+atomic rename·다이어그램 7화면 갱신 (Task 061) |
| 2026-07-14 | OPAL Console 브레인 질의 표에 "프라임 연결 풀" 행 신설 — prewarm_projects 선프라임·프로젝트별 웜 핸들 풀(크기 1)·체크아웃+백그라운드 리필·Semaphore(2) 상한·콜드 폴백·인메모리 전용 (Task 060) |
| 2026-07-10 | OPAL Console 표 갱신 — `console scan` 서브명령 반영(기동 행 scan 추가, 프로젝트 식별 행에 config 생성·머지·install 자동 실행·start 안내 명기) (Task 057) |
| 2026-07-10 | Project Loop 파이프라인 반영 — 오케스트레이터 표 oppl 행, 전문 에이전트 표 opal-evaluator-agent 행, 폴더 트리 oppl 스킬·evaluator 에이전트, 서브에이전트 수 12개(전문 7)로 정합 (Task 056) |
| 2026-07-10 | 배포 채널 표 `opal-cli` CLI 서브커맨드 목록에서 install 제거 — install 서브커맨드 완전 제거에 정합(신규 설치는 One-liner installer, 갱신은 update) (Task 055) |
| 2026-07-02 | 부트스트랩 진입 모델에 첫 줄 마커 3단 스킵 사다리 추가 — `[ASSISTANT]` 마커 신설로 headless(claude -p) 호출을 비서 tier(Phase A)로 캡(PM tier 승격 억제). 첫 소비자 opbr_adapter (Task 051) |
| 2026-06-30 | 부트스트랩 진입 모델 2-tier 절 추가 — 비서(Lite·전역 상시)/PM(Full·`.opal/AGENT.md` 존재 시 승격) 분리. opt-in 모델·`//opi` 불변식·전역 비서 유지 (Task 049) |
| 2026-06-18 | opal-orchestrator 잔존 행 2곳 삭제 (폴더·레지스트리 항목 부재 — dangling. Task 029) |
