# OPAL

> AI 환경에서 IT 프로젝트를 체계적으로 수행하기 위한 범용 AI 개발 프레임워크

## 프로젝트 개요

| 항목 | 값 |
|------|-----|
| 프로젝트명 | OPAL (Open Protocol for Agentic Loops) |
| 도메인 | AI 에이전트 프레임워크 |
| 현재 Phase | 아키텍처 안정화 (하네스 통합, 문서 표준화 완료, 멀티 플랫폼 확장 중) |

## 프로젝트 원칙

1. **표준화 > 커스터마이징** — 컴포넌트 구조와 인터페이스를 일관되게 유지한다
2. **재사용성 > 편의성** — 스킬, 에이전트, 참조 문서는 프로젝트 간 재활용 가능해야 한다
3. **플랫폼 독립성** — Claude Code, Cursor, Gemini, Codex 등 어디서든 동작해야 한다
4. **컴포지션 > 모놀리식** — 스킬과 에이전트를 조합해서 파이프라인을 구성한다
5. **하네스가 품질을 보장한다** — 오케스트레이터 공통 인프라(Guards, Gates, State)로 누가 실행해도 일정한 산출물 품질이 나와야 한다

## 프로젝트 기준

- 표준화 > 커스터마이징
- 재사용성 > 편의성
- 하네스 준수 > 개별 최적화
- 프로세스 일관성 > 속도

## 프로젝트 구조

### 폴더 구조맵

| 폴더 | 역할 | 설명 |
|------|------|------|
| `docs/` | 프로젝트 문서 | 아키텍처, 컨벤션 등 프로젝트 레벨 문서 |
| `tasks/` | 태스크 산출물 | `{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/` 형식의 작업 단위 폴더 |
| `skills/` | 독립 스킬 소스 | 파이프라인 없이 단독 사용하는 스킬 (8종) |
| `opal/skills/` | OPAL 스킬 소스 | 오케스트레이터, 단계 스킬 등 OPAL 전용 (44종) |
| `opal/agents/` | 워커 에이전트 소스 | 모든 서브에이전트 정의 (16종) |
| `opal/tools/` | OPAL 도구 소스 | 결정론 집행 CLI (27종, `event-loader`와 `ego-browser-tool` 포함) |
| `opal/core/` | 프레임워크 코어 | 레퍼런스, MCP 설정, 도구 |
| `opal/bootstrapper/` | 부트스트래퍼 | 플랫폼별 부트스트랩 진입점 (claude/codex/cursor/gemini) |
| `opal/templates/` | 템플릿 | 배포 시 참조하는 설정 템플릿 |
| `dashboard/` | OPAL Console 소스 | `frontend/`(React) + `backend/`(FastAPI) |
| `cursor-rules/` | Cursor 규칙 | Cursor 플랫폼용 `.mdc` 규칙 파일 |
| `memory/` | 메모리 본문 | `.opal/MEMORY.json`이 인덱싱하는 메모리 파일 |
| `scripts/` | 설치 스크립트 | install-mac.sh 등 |
| `.opal/` | 프로젝트 로컬 자산 | PM 프로필(`AGENT.md`) · 프로젝트 브레인(`brain/`) · 메모리(`memory/`, `MEMORY.json`) · 코드맵 설정(`code-scan.json`) · 로컬 설정(`setting.local.json`) |

### 네이밍 규칙

| 폴더 | 네이밍 규칙 | 예시 |
|------|-----------|------|
| `tasks/` | `{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/` | `086-260810-opp-아키텍처-다이어그램-재작성/`, `082-260803-opds-코드맵-매니페스트-샤딩/` |
| `skills/` | `{기능명}/` (kebab-case) | `api-analyzer/`, `interview/` |
| `opal/skills/` | `{그룹}-{역할}/` (접두사 체계) | `opal-pilot-dev/`, `op-dev-plan/` |
| `opal/agents/` | `opal-{대상}-agent/` 또는 `opal-{역할}-checker/` | `opal-task-agent/`, `opal-security-checker/` |
| `docs/` | `{대문자}.md` | `PROJECT.md`, `ARCHITECTURE.md` |

> 태스크 폴더 규칙: 앞 3요소(`{NNN}`·`{YYMMDD}`·`{스킬약어}`)는 ASCII 고정이고, `{태스크명}`은 **한글을 기본**으로 하며 단어는 `-`로 잇는다. 전체 경로에 공백을 쓰지 않는다.

## 주요 컴포넌트 (Dev 파이프라인)

코드·문서·기획 작업의 주력 파이프라인 — 오케스트레이터가 단계 스킬을 워커 에이전트에 디스패치하는 3층 구조(오케스트레이터 → 단계 스킬 → 워커).

**오케스트레이터**

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-pilot-dev` | opd | 오케스트레이터 | Full Task — TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE. 대규모 개발 작업용 |
| `opal-pilot-dev` | opds logical alias | 오케스트레이터 | Short profile (canonical Dev Pilot 내부 선택) — TASK → PLAN → EXECUTE → TEST → CLOSE. PLAN 완료 후 미결정 동작·계약·구조가 발견될 때만 opd 전환 제안 |
| `opal-pilot-dev-wireframe` | opdw | 오케스트레이터 | Wireframe UI — TASK → WIREFRAME → EXECUTE → CLOSE. 와이어프레임 설계부터 UI 구현까지 |
| `opal-pilot-project` | opp | 오케스트레이터 | Project Task 범용 (문서 작성·설정 변경·워크플로우) — TASK → PLAN → EXECUTE → CLOSE |
| `opal-pilot-write-tech` | opwt | 오케스트레이터 | 기획 산출물 네트워크 (PRD·TRD·정책서·IA) — TASK → ANALYSIS → PLAN → EXECUTE → QA → CLOSE. 워커 병렬 디스패치 + 교차 논리 검토·정합성 검증 |
| `opal-pilot-project-dev` | oppd | 오케스트레이터 | 프로젝트 개발 라이프사이클 3 Phase — PLAN → WBS → EXECUTE. 기획은 opwt, 코드 실행은 opal-task-action-agent에 위임하고 PM이 조율 |
| `opal-pilot-project-build` | oppb | 오케스트레이터 | 프로젝트 빌드 — 이미 확정된 실행 계약을 capability 단위 미니 태스크로 소화. P0~P5 6단계·사용자 게이트 6종, 프로젝트 worktree 1개·실행 계약 `INTENT.md` 1개. P0~P2·P5는 대화형 Product Flow가, P3~P4는 `oppb-runtime-tool start` 1회로 Runtime Supervisor가 headless 무인 실행 |

> **actor 축**: `--pm`은 모드 축과 직교하는 별도 실행 주체(actor) 축이다 — 지원 Pilot 폐쇄 목록은 `opal-pilot-dev`(alias `opd`·`opds`) 하나뿐이며, `//opds --pm ...`처럼 조합하면 PM이 각 단계 skill을 워커 디스패치 없이 직접 수행한다. 정의·지원 범위·실행 계약 원문 SSOT는 `opal/core/references/harness/actor.md`.

> **Pilot 선택 기준**: 목표·계약·백로그가 실행 증거에 따라 반복 변경되는 **수렴형 프로젝트는 `oppl`**, 한 번의 설계 승인으로 목표·계약·완료조건을 잠글 수 있는 **확정 실행 계약의 무인 소화는 `oppb`**다. 제품 명세(PRD·TRD) 작성부터 필요하면 `oppd`(또는 `opwt`로 명세를 만든 뒤 `oppb`로 실행), 단일 태스크 규모면 `opd`·`opds`다. 네 Pilot은 병존하며 대체·후계·deprecate 관계가 아니다. `oppb`에서 무인 실행이 보장되는 구간은 P3~P4뿐이며, P0~P2와 P5는 대화형 세션(Product Flow)이 몰고 간다 — P5 merge 게이트는 `--auto-pass`를 거부하고 소유자 발화를 요구한다.

**단계 스킬 (`op-dev-*` 6종)**

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `op-dev-analysis` | - | 단계 스킬 | ANALYSIS 단계 — 프로젝트 지식·코드맵·PROJECT.md 선별 문서를 먼저 소비하고 남은 코드 차이만 분석 (입력 TASK.md → 출력 ANALYSIS.md) |
| `op-dev-plan` | - | 단계 스킬 | PLAN 단계 — 결정·계약과 Work items에 담당·선행·병렬 그룹·변경 대상·검증 명령을 정의 (출력 PLAN.md) |
| `op-dev-test-scenario` | - | 단계 스킬 | TEST-SCENARIO 단계 — PLAN 리스크 가설과 목표 커버 입력 기반 L1/L2/L3 계층 시나리오·검증 계약 생성 (출력 TEST-SCENARIO.md) |
| `op-dev-execute` | - | 단계 스킬 | EXECUTE 단계 — PLAN Work items의 담당·순서·병렬 그룹 기준으로 코드 작성·검증. 필요한 docs 갱신은 PROJECT.md 레지스트리 기반 주입 문서 범위에서 수행 |
| `op-dev-qa` | - | 기준 라이브러리 | Dev 문서 QA 검증 기준 — 별도 QA 단계 없이 PM Gate가 직접 참조 (검증 ID·QA-{단계}.md 형식) |
| `op-dev-wireframe` | - | 단계 스킬 | WIREFRAME 단계 — wireframe-builder 스킬에 위임하여 wireframe.md 생성 |

**워커 에이전트 (`opal/agents/` 16종 중 Dev 계열 11종)**

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-task-agent` | - | 서브에이전트 | 범용 워커 — 단계 스킬 경로와 PM 주입 프로젝트 문서 목록을 받아 독립 컨텍스트에서 실행 |
| `opal-plan-agent` | - | 서브에이전트 | PLAN 전문 워커 — 코드 분석·기능 중심 설계·테스트 시나리오 작성, sdlc-v2 Work items `담당` 배정 |
| `opal-be-agent` | - | 서브에이전트 | 백엔드 전문 워커 — PLAN.md의 BE Work item 구현 |
| `opal-fe-agent` | - | 서브에이전트 | 프론트엔드 전문 워커 — PLAN.md의 FE Work item 구현 |
| `opal-planning-agent` | - | 서브에이전트 | 서비스 기획 전문 워커 — opwt EXECUTE 단계 투입 (정책서·IA·와이어프레임·WBS·API 분석) |
| `opal-task-qa-agent` | - | 서브에이전트 | 범용 QA 워커 — qa_skill·검증 대상·단계명을 받아 독립 컨텍스트에서 검증 |
| `opal-test-agent` | - | 서브에이전트 | 테스트 전문 워커 — TEST-SCENARIO.md 기반 동적 검증, BE/FE/E2E 3모드 |
| `opal-task-action-agent` | - | 서브에이전트 | oppd Phase 3 액션 자율 실행 — PLAN → QA → TEST-SCENARIO → EXECUTE → 검증 루핑(L1~L3b) → TEST 완주 |
| `opal-sdd-action-agent` | - | 서브에이전트 | opsdd Phase 4 ACT 자율 실행 — PLAN → EXECUTE → VERIFY(L1~L3b) → TEST.md 완주 |
| `opal-capability-agent` | - | 서브에이전트 | oppb P3 미니 태스크 capability owner — Supervisor의 headless attempt로 실행되며 execution packet의 lease 4축 안에서 RUN·PROVE를 수행하고 구조화 result만 반환. Git·Controller state·MEMORY·brain 수정 금지, ACCEPT 판정은 외부 Checkpoint Tool·Verifier 소유 |
| `opal-wtm-agent` | wtm | 서브에이전트 | web-to-markdown 워커 — 공개 검색은 기존 web search, 브라우저 추출은 Ego Lite → cmux → Playwright 순서로 변환 |

> 나머지 워커 5종은 각 파이프라인 섹션에 등재된다 — `opal-db-agent`(Data Design) · `opal-evaluator-agent`·`opal-loop-action-agent`(Project Loop) · `opal-security-checker`·`opal-convention-checker`(GC).

> **트랙 라우팅**: 사용자가 선택한 `opd`/`opds`를 기본 수행하며, 파일 수·변경량은 전환 기준에서 제외한다. `opd`는 ANALYSIS 완료 직후 PLAN 전에 "외부 영향이 있는 동작·계약·구조 결정을 새로 해야 하는가?"를 1회 검토해, 아니오일 때만 `opds` 강등을 제안한다. `opds`는 PLAN 완료 직후 EXECUTE 전에 같은 핵심 질문을 검토해, 예일 때만 `opd` 강업을 제안한다. 제안은 `report_type=progress_report`, `transition_action=continue`인 비차단 보고이며 자동 전환하지 않는다. 현재 트랙이 실행 불가능할 때만 `decision_request` 또는 `blocked`로 전환하고, 판단 불능은 현재 트랙 유지 또는 강업 제안 쪽의 fail-safe로 처리한다. SSOT: `opal/skills/opal-pilot-dev/references/track-routing.md` · `opal/skills/opal-pilot-dev/references/track-escalation.md`.

> **프로젝트 문서 주입 계약 (Task 111)**: Dev 파이프라인의 PM은 `pm.activate` 이벤트에서 `docs/PROJECT.md`를 읽고 §프로젝트 문서 레지스트리의 적용 범위·참조 시점으로 작업 도메인에 필요한 프로젝트/기획/설계 문서를 선별해 워커에 주입한다. 개발 워커는 주입된 문서만 읽으며, `docs/` 전체나 고정 파일명을 자체 가정하지 않는다. `docs/PROJECT.md`가 없는 프로젝트에서만 기존 영역별 최소 폴백 문서를 허용한다.

> **실행 지속성 계약 (Task 136)**: 모든 Pilot의 단계 경계는 `state-tool`의 `transition_action`(`continue`/`await_user`/`blocked`/`complete`), `report_type`(`progress_report`/`decision_request`), `next_action`을 소비한다. interactive/semi-agentic/agentic 차이는 `opal/core/references/harness/modes.md`와 각 pipeline `transition_contract`가 소유하고, 신규 pipeline CLOSE는 `close.done_md` 뒤 tail 행을 거쳐 `close.final`에서만 완료된다. 플랫폼별 종료 방지·재개 안내는 hook/adapter 계층이 소유한다.

## 주요 컴포넌트 (SDD 파이프라인)

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-pilot-sdd` | opsdd | 오케스트레이터 | SDD 기반 오케스트레이터: SPEC → VERIFY → PLAN → TASKS → EXECUTE |
| `op-sdd-spec` | - | 단계 스킬 | SPEC 단계 — SDD 명세 작성 |
| `op-sdd-verify` | - | 단계 스킬 | VERIFY 단계 — SDD 명세 검증 |
| `op-sdd-plan` | - | 단계 스킬 | SPEC-PLAN 단계 — SDD 구현 계획 수립 |
| `op-sdd-action-plan` | - | 단계 스킬 | PLAN(ACT) 단계 — SDD ACT 전용 경량 구현 청사진 작성 (opal-sdd-action-agent 디스패치) |

## 주요 컴포넌트 (GC 파이프라인)

커밋 전 코드 보안·컨벤션 점검용 경량 Pilot (2026-04 신설).

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-pilot-gc` | opgc / gc | 경량 오케스트레이터 (thin wrapper) | GC 4단계 Pilot: SCAN → CHECK → REPORT → CLOSE. 범위 확정·상태·Gate·CLOSE만 소유하고 검사 절차는 `op-gc-*` 단계 스킬에 위임 |
| `op-gc-security` | - | 단계 스킬 | CHECK 단계 보안 검사 — `docs/SECURITY.md` 우선, 승인된 공식 표준(OWASP/CWE/SANS) baseline. `opal-pilot-gc` 없이 단독 호출 가능 |
| `op-gc-convention` | - | 단계 스킬 | CHECK 단계 컨벤션 검사 — `docs/CONVENTIONS.md` 우선, 부재 시 관측 기반 advisory 수행(생략 아님). 단독 호출 가능 |
| `op-gc-report` | - | 단계 스킬 | REPORT 단계 결과 정규화·릴리스 판정 — 중복 병합·baseline delta·차단 계산·문서 업데이트 트리거 |
| `opal-security-checker` | - | 서브에이전트 (thin role) | `op-gc-security`를 독립 컨텍스트에서 실행하는 read-only role. 검사 기준 미보유 |
| `opal-convention-checker` | - | 서브에이전트 (thin role) | `op-gc-convention`을 독립 컨텍스트에서 실행하는 read-only role. 검사 기준 미보유 |

> finding schema·판정(PASS/PASS_WITH_ADVISORIES/FAIL/INCOMPLETE)·fingerprint·baseline delta의 SSOT는 `opal/core/references/harness/gc-finding-schema.md`다. 세 스킬과 두 role은 이 문서를 참조하고 필드·판정표를 복제하지 않는다.

## 주요 컴포넌트 (Project Brain)

llm-wiki 사상을 융합한 프로젝트 지식 위키 — 프로젝트의 WHY·HOW를 마크다운으로 누적·질의·정비 (2026-06 신설, 태스크 015).

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-brain` | opbr | operator (멀티모드) | 브레인 4모드 라우터: init · ingest · query · lint (단계 파이프라인·워커 디스패치 없음, brain-tool 직접 호출) |
| `op-brain-ingest` | - | 단계 스킬 | CLOSE 자동 ingest 워커 (pilot CLOSE 훅에서 디스패치, brain 부재 시 no-op) |
| `brain-tool` | - | 도구 | 지식 위키 결정론적 집행 CLI (10 서브명령 init/add-page/index/log/search/sync-header/lint/validate/**analyze**/**ingest-scan**). index·log·링크 무결성 집행, @header 단방향 시드. `analyze`는 code-scan @header 정량 집계(init 제안 입력), `ingest-scan`은 docs/skills/tasks 스캔 후 멱등 skip 판정 |

> brain은 `.opal/brain/`에 저장되는 **프로젝트 자산**이며 `//opbr init`으로 생성한다. code-scan(WHAT)·MEMORY(운영 기억)와 역할이 분리된다(WHY/HOW).

## 주요 컴포넌트 (Data Design 파이프라인)

데이터 설계 전담 파이프라인 — 사전 정의 → ERD 모델링 → DDL 생성 → 마이그레이션까지 일관된 흐름 제공 (2026-06 신설, 태스크 019).

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-pilot-data-design` | opdd | 오케스트레이터 | 데이터 설계 파이프라인: TASK → DICT → MODEL → DDL/MIGRATION → QA → CLOSE |
| `op-data-dictionary` | - | 단계 스킬 | DICT 단계 — 용어사전·도메인사전·코드사전 산출물 생성 |
| `op-data-model` | - | 단계 스킬 | MODEL 단계 — 트랙별 ERD 산출물 생성. 신규(greenfield): 개념(Mermaid) → 논리(Mermaid) → 물리(DBML) / 역공학(reverse): 물리 → 논리 (개념 제외) |
| `op-data-ddl` | - | 단계 스킬 | DDL 단계 — DBML → DBMS별 CREATE TABLE 스크립트 생성 |
| `opal-db-agent` | - | 서브에이전트 | DB 모델 설계+구현 전문 워커 — 마이그레이션 코드 구현 담당 |

> `//erm` (erd-modeler) alias는 `op-data-model` 단독 호출로 하위호환됩니다. 신규 데이터 설계 작업은 `//opdd`를 사용하세요.

## 주요 컴포넌트 (Project Loop 파이프라인)

루프 기반 프로젝트 오케스트레이션 — 목표·계약·백로그를 실행 전에 잠글 수 없고 실행 증거에 따라 반복 재구성해야 하는 수렴형 프로젝트를 종료조건 있는 2-루프로 완주한다. 고정된 실행 계약을 처리하는 프로젝트 Pilot과는 독립된 선택지이며 대체·후계·deprecate 관계가 아니다 (2026-07 신설, 태스크 056).

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-pilot-project-loop` | oppl | 오케스트레이터 | 2-루프 수렴: 설계 루프(인터뷰→PRD→TRD→CONTRACT→백로그) → 실행 루프(태스크 반복). 종료조건 5종(반복상한·예산·무진전·목표체크·사람게이트) |
| `opal-evaluator-agent` | - | 서브에이전트 | 명세 심판 전담 — CONTRACT 루브릭절 기준 구현 전 판정(verdict-only·readonly). 검증 2원화의 전단(후단은 opal-test-agent). phase 4종(design-review/spec-review/drift-recheck + `scenario-rubric` 목표-커버 판단축, 073) |
| `opal-loop-action-agent` | - | 서브에이전트 | Loop 2 루프 액션 에이전트 — PM이 태스크당 1회 디스패치, T1~T5+G를 내부 디스패치(생성자·Evaluator·test-agent·checker 4축)로 완주 후 소멸. 결과 계약 6필드 반환, 비가역·계약갱신 drift는 blocked 반환(PM 에스컬레이션) |
| `backlog-tool` | - | 도구 | backlog.json SSOT 관리 CLI (8서브명령 init/add-task/select-next/mark/update-task/done-check/coverage-check/show, BACKLOG.md 자동 렌더). `covers` 필드 + `coverage-check`(표면 커버리지·통합 태스크 게이트 — surfaces.json 소비) |
| `test-tool e2e` | - | 도구 확장 | E2E 실행 계약 집행 — `run`·`resume`·`status`·`clean` 4서브명령. 대상 3종(`source-main`/`source-worktree`/`installed`) 해석·포트 임대·SUT 기동·health gate, driver 후보 체인(agent-browser orca-managed → cmux → agent-browser standalone → ego-lite → playwright opt-in, `provider_unavailable`일 때만 다음 후보)과 executor 3종(browser/api/human), 증적 단일 관문(`evidence.py`+`redaction.py`). `real-usage` 정의와 충실도 승격 조건을 이 도구가 소유하며 파이프라인 문서는 참조만 한다 (127) |
| `test-tool scenario-*` | - | 도구 확장 | test-scenario.json SSOT — RED-first 동결 게이트(scenario-init/red/lock/mark/status) + 충실도·표면 게이트(scenario-fidelity-check/scenario-conformance — required_fidelity·fidelity·surface_ref 필드, 증거 충실도 사다리 mock<real-http<real-usage) + 목표-커버 게이트(scenario-coverage-check — R/F/H 매핑 결정론, exit 16/17, 073) + E2E profile·executor·final/operational status·구조화 assertion/evidence/handoff 판정 계약. 실제 executor와 Runtime Manager는 별도 구현 범위 |
| `oppl-runtime-tool` | - | 도구 | `.oppl-run/runtime.json` 운영 ledger 관리 CLI — round·project dispatch·task attempt·resume·예산 admission과 실패 지문 무진전 판정을 소유한다. 3-SSOT(backlog/state/test-scenario)와 별개의 런타임 가드 축이며 업무·파이프라인·검증 상태를 복제하지 않는다. attempt 원문(PID·PGID·heartbeat·terminal result)은 `opal-agent`의 attempt record가 소유하고 ledger는 `attempt_id`·경로만 외래 참조한다 |
| `opal-action-monitor` | - | 도구 | 루프 액션 에이전트 진행 현황판 — `.oppl-run/`(events.jsonl·journal.md·exitcode) 파싱, 단계×축 상태 렌더 + `--json`/`--watch`. 7상태와 잔여 상한 표시는 `oppl-runtime-tool` ledger에 위임한다 (읽기 전용) |
| `opal-action-status` | opas | operator | 액션 에이전트 현황 발동층 — `//opas [태스크폴더]` 자동 탐지 + opal-action-monitor/backlog-tool 소비 + 해석 보고 (읽기 전용). 커버리지 oppl 한정, 069/070 전환 시 무변경 확장 |

> 3-SSOT tool-gated: backlog.json(backlog-tool) · state.json(state-tool) · test-scenario.json(test-tool) — 손편집 금지. 사람 뷰는 도구가 제공한다: `BACKLOG.md`는 자동 렌더, `state.json` 현황 조회는 `state-tool show`(094 저널화 이후 STATE.md는 렌더 뷰가 아니라 의사결정 로그·블로커 저널이다).

## 주요 컴포넌트 (OPAL Console)

로컬 OPAL 프로젝트를 한 웹 화면에서 조망하는 읽기 전용 관리 대시보드 (2026-06 신설, 태스크 021). 상세 구조: `docs/ARCHITECTURE.md §OPAL Console`.

| 컴포넌트 | 유형 | 설명 |
|----------|------|------|
| `dashboard/frontend` | FE 앱 | React+TS+Vite+shadcn/ui — 7개 화면(대시보드/프로젝트/태스크 칸반/메모리/환경/프로젝트 브레인/설정) |
| `dashboard/backend` | BE 데몬 | FastAPI — `.opal/AGENT.md` 마커 스캐너 + read-only 도구 어댑터 + 마크다운 파서 + 쓰기 예외 2종 격리(브레인 POST·설정 라우터) (127.0.0.1:7823) |
| `opal-cli console` | CLI | 데몬 기동/관리 서브커맨드 (start/stop/status/open/scan) — scan은 `console.config.json`(스캔 루트 설정)을 생성·머지 갱신하며 install이 1회 자동 실행 |

> 소스는 `dashboard/`, 배포는 install 경유 `~/.opal/dashboard-server/`. 읽기 전용(쓰기/편집·브레인 화면은 2차). 시그니처 3색은 `:root` 전역 CSS 변수로 교체 용이.

## 주요 컴포넌트 (PM 개선 루프)

PM의 학습·자기개선을 tool-gated로 집행하는 서브시스템 — 정의만 있고 호출 0건이던 학습 루프를 op-brain-ingest 패턴(CLOSE 하드연결 + 도구 집행 + 증거 산출)으로 재설계 (2026-07 신설, 태스크 058).

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-improve` | opim | 스킬 | PM 개선 루프 — 관찰→분류→기록→보고→승인 5단계. scope 2원화(결정론 게이트→루브릭→동점 에스컬레이션)로 로컬 PM 개선 / FW 개선 분류 |
| `improve-tool` | - | 도구 | 개선 산출 결정론 집행 CLI (record/list/show, scope local/fw 분기). local=memory-tool 위임, fw=fw-inbox write, JSON `"ok"` 계약 |
| 회고 하드스텝 | - | pilot CLOSE 훅 | opd·opwt·opgc·oppd CLOSE에 삽입 — 태스크/세션 궤적 신호로 개선후보 도출→기록, 개선후보 0건 시 no-op(CLOSE 비차단) |

> 학습 2분류: 로컬 PM 개선 → 프로젝트 `.opal/`(memory) / FW 개선 → 전역 `~/.opal/fw-inbox/`(출처메타 자기완결 항목, install 배포 경유 반영). SSOT: `opal/core/references/harness/pm-improvement-loop.md` — 정의 3문서(구 `pm-learning-loop.md`·`self-improvement.md`·opal-pm §5 stub)를 단일 SSOT로 통합. hook 미채택(플랫폼 독립).

## 주요 컴포넌트 (PM 직접 수행)

PM이 직접 조회·작성·수정·검증을 수행하는 대화형 operator 스킬 — `opal-brain`과 같은 유형(단계 파이프라인·워커 디스패치 없음)이며, Dev 파이프라인 actor 축(`--pm`)과는 별개 진입 경로다 (2026-09 신설, 태스크 122).

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-self-pm` | oppm | operator (대화형 루프) | 종료 조건을 가진 질문 반복형 PM 직접 수행 루프 — 질문 1개→조회·정리 반복으로 범위 확정 → 작업 계약 승인 → PM 직접 수행·검증 → 8영역(기획·설계·프로젝트 문서·CONVENTIONS·SECURITY·brain·memory·code-scan) 지식 동기화 판정 → 사용자 최종 확인 |
| `self-pm-tool` | - | 도구 | `opal-self-pm` 실행 기록(8필드 JSON) 전담 CLI. `state.json`·`test-scenario.json`·`backlog.json` 3-SSOT는 읽지도 쓰지도 않는다 |

> 독립 검증 경계(생성자≠평가자 예외)와 GC 3종(`op-gc-security`·`op-gc-convention`·`op-gc-report`) 호출 지점의 공유 계약은 `opal/core/references/harness/actor.md` §독립 검증 경계와 GC 호출 지점이 소유한다.

## 주요 컴포넌트 (TEST-SCENARIO 목표-커버 게이트)

TEST-SCENARIO 단계를 "목표 달성 검증"으로 재정의 — 루브릭 채점 기반 작은 수렴 루프(작성→커버리지 도구 게이트→독립 평가자 루브릭 채점→종료조건→재작성)를 공유 컴포넌트로 구현. 070 사건(핵심 목표 미검증 완료)의 근본 대응. **opd·opds·opsdd 3종 접합**(oppl 제외 확정 — 자체 표면-게이트+독립평가 보유 / oppd 2차 유예). (2026-07 신설 태스크 073, opds·opsdd 확산 태스크 075).

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `analysis-core.md` | - | 규칙 SSOT | ANALYSIS·PLAN 공유 분석 절차 SSOT — 지식 선조회 3단·증분 소비·델타 탐색·분석 깊이·관련 파일 맵 6영역 축·의존성/영향 범위·품질 체크리스트. 절차는 이 문서, 산출물 형식은 각 스킬이 소유. `opal/core/references/harness/analysis-core.md` |
| `scenario-gate.md` | - | 규칙 SSOT | 루브릭 6축(①목표달성~⑥경계/부정)·판정주체 분리(②③④ 결정론/①⑤⑥ 판단)·정규화 계약·종료조건 3종(수렴/반복상한/무진전)·tool-gated 집행. `opal/core/references/harness/` |
| `op-scenario-gate` | - | 단계 스킬 | 목표-커버 루프 컨트롤 — 정규화 페이로드 빌드→coverage-check→evaluator→종료조건 판정→verdict 반환. Step 2 pilot 변환기로 재사용(opd/opds/opsdd 3종 접합, oppl 제외·oppd 2차) |
| `test-tool scenario-coverage-check` | - | 도구 확장 | R/F/H↔시나리오 매핑 누락 결정론 판정(②③④). exit 0(전커버)/16(coverage_unmet)/17(입력오류). pilot-중립 정규화 페이로드 소비 |
| `opal-evaluator-agent scenario-rubric` | - | 서브에이전트 phase | 판단축 ①목표달성·⑤채택/잔존·⑥경계/부정 2점 척도 채점(각≥1 AND 평균≥1.5→pass). SCENARIO-GATE-{N}.md 산출. 기존 3 phase additive |

> tool-gated: 게이트 PASS는 coverage-check exit 0 AND evaluator verdict pass 두 증거 필수. Producer(PM+캡틴)≠Evaluator(opal-evaluator-agent) 매반복 분리. 루프 상한 수치 SSOT는 `opal/core/references/harness/guards.md`, 게이트 절차 SSOT는 `opal/core/references/harness/scenario-gate.md`다. opd STEP 3.5의 pipeline.json `test_scenario.scenario_gate` 행이 EXECUTE 진입을 구조적으로 차단한다.
>
> **목표계열 선작성 트랙 (Task 095)**: 도출 입력을 Block A(TASK 유래 — 목표·R·채택/잔존 → 축 ①②⑤⑥)와 Block B(PLAN 유래 — F·H → 축 ③④)로 분리하고, Block A를 PLAN 워커 실행과 **병렬 선작성**할 수 있다. opt-in이며 목적은 효율이 아니라 **관점 편향 차단**(070 실패모드 방어)이다. 보강 없이는 게이트가 `coverage_unmet`으로 거부하고, 게이트는 보강 완료 후 1회만 호출한다. 접합: opds STEP 2 · opd STEP 3/3.5. SSOT: `opal/core/references/harness/red-first.md` §1.6 · 절차: `op-dev-test-scenario/references/test-scenario-guide.md` §Step 1.

## 프로젝트 구성

> 프로젝트의 기술적 요소를 영역별로 정의한다. opgc SCAN/디스패치, PM 컨텍스트 주입 시 이 표를 기반으로 영역 매칭과 전문 에이전트 선정이 이루어진다. 부재 시 오케스트레이터는 단일 요소 기본값(프로젝트 전체 × 체커)으로 폴백한다.

| 요소 | 경로 | 기술 스택 | 전문 에이전트 |
|------|------|-----------|--------------|
| Framework | `opal/`, `skills/` | Markdown, YAML, Bash, Node.js | opal-task-agent (범용) |
| Console FE | `dashboard/frontend/` | React, TypeScript, Vite, Tailwind, shadcn/ui | opal-fe-agent |
| Console BE | `dashboard/backend/` | Python, FastAPI, uvicorn | opal-be-agent |

## 프로젝트 문서

| 문서 | 설명 | 용도 | 적용 범위 | 참조 시점 |
|------|------|------|----------|----------|
| `.opal/AGENT.md` | PM 프로필 | PM 역할 및 검토 기준 | Framework | `pm.activate` 이벤트 |
| `docs/PROJECT.md` | 프로젝트 정의·문서 레지스트리 (SSOT) | 프로젝트 개요, 원칙, 문서 허브, PM 컨텍스트 선별 기준 | Framework | `pm.activate` 이벤트. 세션 부트에서는 로드 금지, 이후 워커 디스패치 문서 선별에 사용 |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 | 구조, 컴포넌트 관계, 배포 모델 | Framework | PROJECT.md 레지스트리가 구조 변경·영향 분석에 필요하다고 지시할 때 |
| `docs/CONVENTIONS.md` | 코드 및 문서 컨벤션 | 네이밍, 파일 구조, 커밋 **메시지 형식·단위**, 구현 규칙(디스패치/@header/Citation/State/도구·배포 경계·플랫폼 분기). 실행 규칙 원문은 `opal/core/references/harness/`의 owner 문서, 문서 이력 규칙은 `opal/core/references/opal-doc-standard.md` §5가 소유 | Framework | `pm.activate` 후 PROJECT 레지스트리가 구현·문서 컨벤션 판단에 필요하다고 지시할 때 |
| `.opal/MEMORY.json` | 프로젝트 메모리 인덱스 (JSON SSOT) | 메모리·작업 히스토리·피드백 추적 (`memory/` 하위 메모리 파일 인덱스). 변경은 `memory-tool`만 수행 | Framework | `session.project`에서 `event-loader project-brief`가 `memory-tool show --boot-brief`를 통해 검토 후보만 선택 로드. 본문·전체 history는 로드 금지 |
| `README.md` | 프레임워크 공개 소개 문서 | Pilot 개념, 사용 사례, 프레임워크 철학 정의 | Framework | Pilot 추가/변경 시, 사용자 대면 문서 작업 시, 프레임워크 철학/방향 관련 작업 시 |
| `docs/architecture-diagram/opal_framework_architecture.html` | 프레임워크 구조 다이어그램 (시각 SSOT) | 3층 구조·파이프라인·도구 관계 시각화 (태스크 086 산출) | Framework | 구조 설명·온보딩 시 |
| `docs/SECURITY.md` | 프로젝트 보안 기준 | `op-gc-security`가 공식 표준 baseline보다 우선 적용하는 프로젝트 누적 기준 | Framework | 보안 체크(opgc CHECK) 시 |
| `opal/core/references/harness/actor.md` | 실행 주체(actor) 축 SSOT | 모드 축과 직교하는 `--pm` 정의, 지원 Pilot 폐쇄 목록, `--pm` 실행 계약, 독립 검증 경계·GC 호출 지점 | Framework | `pilot.start` 이벤트 |
| `opal/core/references/harness/modes.md` | 실행 모드 SSOT | interactive/semi-agentic/agentic의 단계 경계·자동 계속·사용자 대기 계약 | Framework | `pilot.start` 이벤트와 기존 태스크 재개, mode 전이 판단 시 |
| `opal/core/references/harness/state.md` | state-tool 전이 계약 | `transition_action`/`report_type`/`next_action`, CLOSE final, 사용자 확인 자동 승인 예외 | Framework | 상태 전이·재개·CLOSE tail·사용자 확인 행 처리 시 |
| `opal/core/references/harness/task-process.md` | TASK 단계 전이 계약 | TASK 완료 보고가 구조화 전이 출력을 소비하고, 산문 승인 질문을 전이 판정 근거로 쓰지 않도록 하는 단계 경계 규칙 | Framework | TASK 작성·완료 직후 다음 행동 판정 시 |
| `opal/core/hooks/claude-hooks.json` | Claude Code hook source | Stop hook은 `ownership-tool`의 stop hook 어댑터에 위임한다 — 세션 소유 태스크를 registry로 판정한 뒤 `transition_action=continue`이면 종료 차단·`next_action` 재개 안내를 반환하고, 무소유·타세션 소유·판정 불능은 통과시킨다 | Framework | 설치·아카이브 검증과 Claude 플랫폼 실행 지속성 점검 시 |
| `opal/skills/opal-pilot-*/references/pipeline*.json` | Pilot pipeline fixture | 단계 행 key, gate, `transition_contract`, CLOSE tail(`close.done_md`~`close.final`)의 기계가독 SSOT | Framework | state-tool init, cross-Pilot conformance, 모드 경계·CLOSE 완료 판정 시 |
| `docs/run-log/PRD.md` | 태스크 실행 로그 제품 요구 | 목표·비목표·요구(R-1~R-21)·Phase 인도 범위·성공 판정 귀속 | Framework | 실행 로그 관련 작업의 범위·우선순위 판단 시 |
| `docs/run-log/TRD.md` | 태스크 실행 로그 기술 결정 | 아키텍처 결정(D-1~D-9)·구성요소 책임 경계·데이터 흐름·동시성/시간/보안 모델·단계별 도입 순서 | Framework | run-log 구현·확산 태스크의 설계 판단 시 |
| `docs/run-log/CONTRACT.md` | 태스크 실행 로그 인터페이스 계약 (SSOT) | 사건 스키마·허용 조합·오류 코드·CLI 시그니처·경계·기계검증절(MV)·루브릭절. 구현 전 명세 심판의 판정 기준 원천 | Framework | run-log 관련 구현·검증·명세 리뷰 전 |
| `docs/run-log/surfaces.json` | 표면 인벤토리 (기계가독) | CLI 17종 + 변환기 2종의 호출 형태·응답·오류 집합. 커버리지·적합성 게이트가 소비하는 유일한 IR | Framework | 백로그 커버리지 판정·오류 코드 대응 검사 시 |
| `docs/proposals/` | 미적용 제안서 | 채택 전 설계 제안. 적용 완료분은 `archives/`로 이관되며 규범 원문은 owner 문서가 소유한다 | Framework | 제안 검토·결정 시 |
| `opal/core/references/harness/done-template.md` | 표준 CLOSE DONE.md 템플릿 (SSOT) | DONE.md 절 구성 + `## 회고적 학습 후보` 절 계약(레포 상대 page 경로 1행 1건, finalize 재진입 판정의 선언 집합). 오케스트레이터 SKILL은 포인터만 두고 템플릿 본문을 복제하지 않는다 | Framework | CLOSE 단계에서 DONE.md를 작성할 때, merge 후 귀속·worktree finalize 판단 시 |
