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
| `opal/skills/` | OPAL 스킬 소스 | 오케스트레이터, 단계 스킬 등 OPAL 전용 (42종) |
| `opal/agents/` | 워커 에이전트 소스 | 모든 서브에이전트 정의 (15종) |
| `opal/tools/` | OPAL 도구 소스 | 결정론 집행 CLI (19종) |
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
| `opal-pilot-dev-short` | opds | 오케스트레이터 | Short Task (코드 변경 기본 진입점) — TASK → PLAN → EXECUTE → TEST → CLOSE. PLAN에서 규모 초과 판단 시 opd 에스컬레이션 제안 |
| `opal-pilot-dev-wireframe` | opdw | 오케스트레이터 | Wireframe UI — TASK → WIREFRAME → EXECUTE → CLOSE. 와이어프레임 설계부터 UI 구현까지 |
| `opal-pilot-project` | opp | 오케스트레이터 | Project Task 범용 (문서 작성·설정 변경·워크플로우) — TASK → PLAN → EXECUTE → CLOSE |
| `opal-pilot-write-tech` | opwt | 오케스트레이터 | 기획 산출물 네트워크 (PRD·TRD·정책서·IA) — TASK → ANALYSIS → PLAN → EXECUTE → QA → CLOSE. 워커 병렬 디스패치 + 교차 논리 검토·정합성 검증 |
| `opal-pilot-project-dev` | oppd | 오케스트레이터 | 프로젝트 개발 라이프사이클 3 Phase — PLAN → WBS → EXECUTE. 기획은 opwt, 코드 실행은 opal-task-action-agent에 위임하고 PM이 조율 |

**단계 스킬 (`op-dev-*` 7종)**

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `op-dev-analysis` | - | 단계 스킬 | ANALYSIS 단계 — 코드베이스 분석·기술 스택 식별·추천 스킬/MCP 매핑 (입력 TASK.md → 출력 ANALYSIS.md) |
| `op-dev-plan` | - | 단계 스킬 | PLAN 단계 — 기능(F-NNN) 중심 구현 청사진. Flat/Multi-Feature 모드 자동 선택 (출력 PLAN.md) |
| `op-dev-todo` | - | 단계 스킬 | TODO 단계 (Full Task 전용) — PLAN을 파일 단위 작업으로 분해 + QA 체크리스트·복잡도 판별 (출력 TODO.md) |
| `op-dev-test-scenario` | - | 단계 스킬 | TEST-SCENARIO 단계 — 리스크 가설 표 기반 L1/L2/L3 계층 시나리오·4열 매핑 표 (출력 TEST-SCENARIO.md) |
| `op-dev-execute` | - | 단계 스킬 | EXECUTE 단계 — 지정 체크리스트 기반 코드 작성·검증. 에이전트 이름 매핑으로 specialist/generalist 가이드 자동 선택 |
| `op-dev-qa` | - | 기준 라이브러리 | Dev 문서 QA 검증 기준 — 별도 QA 단계 없이 PM Gate가 직접 참조 (검증 ID·QA-{단계}.md 형식) |
| `op-dev-wireframe` | - | 단계 스킬 | WIREFRAME 단계 — wireframe-builder 스킬에 위임하여 wireframe.md 생성 |

**워커 에이전트 (`opal/agents/` 15종 중 Dev 계열 10종)**

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-task-agent` | - | 서브에이전트 | 범용 워커 — 단계 스킬 경로를 받아 독립 컨텍스트에서 실행 |
| `opal-plan-agent` | - | 서브에이전트 | PLAN 전문 워커 — 코드 분석·기능 중심 설계·테스트 시나리오 작성, 체크리스트 Step별 agent 배정 |
| `opal-be-agent` | - | 서브에이전트 | 백엔드 전문 워커 — PLAN.md의 BE 영역 Step 구현 |
| `opal-fe-agent` | - | 서브에이전트 | 프론트엔드 전문 워커 — PLAN.md의 FE 영역 Step 구현 |
| `opal-planning-agent` | - | 서브에이전트 | 서비스 기획 전문 워커 — opwt EXECUTE 단계 투입 (정책서·IA·와이어프레임·WBS·API 분석) |
| `opal-task-qa-agent` | - | 서브에이전트 | 범용 QA 워커 — qa_skill·검증 대상·단계명을 받아 독립 컨텍스트에서 검증 |
| `opal-test-agent` | - | 서브에이전트 | 테스트 전문 워커 — TEST-SCENARIO.md 기반 동적 검증, BE/FE/E2E 3모드 |
| `opal-task-action-agent` | - | 서브에이전트 | oppd Phase 3 액션 자율 실행 — PLAN → QA → TEST-SCENARIO → EXECUTE → 검증 루핑(L1~L3b) → TEST 완주 |
| `opal-sdd-action-agent` | - | 서브에이전트 | opsdd Phase 4 ACT 자율 실행 — PLAN → EXECUTE → VERIFY(L1~L3b) → TEST.md 완주 |
| `opal-wtm-agent` | wtm | 서브에이전트 | web-to-markdown 워커 — cmux-tool(1순위) → playwright-tool(fallback) 2단 폴백으로 웹 페이지 변환 |

> 나머지 워커 5종은 각 파이프라인 섹션에 등재된다 — `opal-db-agent`(Data Design) · `opal-evaluator-agent`·`opal-loop-action-agent`(Project Loop) · `opal-security-checker`·`opal-convention-checker`(GC).

> **트랙 라우팅 (Task 098)**: `//opd` 호출이어도 4축(설계 확정률·예상 변경 파일 수·신규 개념 유무·최고 검증 계층)을 전건(AND) 충족하면 `opds`로 자동 강등 진입한다. 판정 시점은 TASK 완료 직후 1회이며, 승격(`opds`→`opd`, PLAN 결과 시점)과 시점·임계가 상호배타여서 왕복 구조가 성립하지 않는다. 판정 불능·`## 확정된 설계 방향` 부재 시 fail-safe는 강등 불발(`opd` 유지)이다. 강등은 소유자 승인 왕복 없이 진입하고 4축 실측값을 사후 통보한다. 접합: opd STEP 1 직후 · opds §에스컬레이션 규칙 포인터. 임계값 수치는 SSOT에만 존치 — SSOT: `opal/core/references/harness/track-routing.md`.

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
| `opal-pilot-gc` | opgc / gc | 경량 오케스트레이터 | GC 4단계 Pilot: SCAN → CHECK → REPORT → CLOSE |
| `opal-security-checker` | - | 서브에이전트 | 보안 체크 — OWASP Top 10 / CWE Top 25 / SANS Top 25 Base + `docs/SECURITY.md` 누적 |
| `opal-convention-checker` | - | 서브에이전트 | 컨벤션 체크 — 프로젝트 `docs/CONVENTIONS.md` 유일 기준 (부재 시 초안 유도) |

## 주요 컴포넌트 (Project Brain)

llm-wiki 사상을 융합한 프로젝트 지식 위키 — 프로젝트의 WHY·HOW를 마크다운으로 누적·질의·정비 (2026-06 신설, 태스크 015).

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-brain` | opbr | operator (멀티모드) | 브레인 4모드 라우터: init · ingest · query · lint (단계 파이프라인·워커 디스패치 없음, brain-tool 직접 호출) |
| `op-brain-ingest` | - | 단계 스킬 | CLOSE 자동 ingest 워커 (pilot CLOSE 훅에서 디스패치, brain 부재 시 no-op) |
| `brain-tool` | - | 도구 | 지식 위키 결정론적 집행 CLI (10 서브명령 init/add-page/index/log/search/sync-header/lint/validate/**analyze**/**ingest-scan**). index·log·링크 무결성 집행, @header 단방향 시드. `analyze`는 code-scan @header 정량 집계(init 제안 입력), `ingest-scan`은 docs/skills/tasks 스캔 후 멱등 skip 판정 |

> brain은 `.opal/brain/`에 저장되는 **프로젝트 자산**이며 `//opbr init`으로 생성한다. code-scan(WHAT)·MEMORY(운영 기억)와 역할이 분리된다(WHY/HOW). 설계 SSOT: `docs/proposals/opal-brain-design.md`.

## 주요 컴포넌트 (Data Design 파이프라인)

데이터 설계 전담 파이프라인 — 사전 정의 → ERD 모델링 → DDL 생성 → 마이그레이션까지 일관된 흐름 제공 (2026-06 신설, 태스크 019).

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-pilot-data-design` | opdd | 오케스트레이터 | 데이터 설계 파이프라인: TASK → DICT → MODEL → DDL/MIGRATION → QA → CLOSE |
| `op-data-dictionary` | - | 단계 스킬 | DICT 단계 — 용어사전·도메인사전·코드사전 산출물 생성 |
| `op-data-model` | - | 단계 스킬 | MODEL 단계 — 개념(Mermaid) → 논리(Mermaid) → 물리(DBML) ERD 산출물 생성 |
| `op-data-ddl` | - | 단계 스킬 | DDL 단계 — DBML → DBMS별 CREATE TABLE 스크립트 생성 |
| `opal-db-agent` | - | 서브에이전트 | DB 모델 설계+구현 전문 워커 — 마이그레이션 코드 구현 담당 |

> `//erm` (erd-modeler) alias는 `op-data-model` 단독 호출로 하위호환됩니다. 신규 데이터 설계 작업은 `//opdd`를 사용하세요.

## 주요 컴포넌트 (Project Loop 파이프라인)

루프 기반 프로젝트 오케스트레이션 — 선형 Phase(oppd) 대신 종료조건 있는 2-루프 수렴 구조로 규모 있는 프로젝트를 완주 (2026-07 신설, 태스크 056. oppd 병행 유지, 검증 후 deprecate 검토).

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `opal-pilot-project-loop` | oppl | 오케스트레이터 | 2-루프 수렴: 설계 루프(인터뷰→PRD→TRD→CONTRACT→백로그) → 실행 루프(태스크 반복). 종료조건 5종(반복상한·예산·무진전·목표체크·사람게이트) |
| `opal-evaluator-agent` | - | 서브에이전트 | 명세 심판 전담 — CONTRACT 루브릭절 기준 구현 전 판정(verdict-only·readonly). 검증 2원화의 전단(후단은 opal-test-agent). phase 4종(design-review/spec-review/drift-recheck + `scenario-rubric` 목표-커버 판단축, 073) |
| `opal-loop-action-agent` | - | 서브에이전트 | Loop 2 루프 액션 에이전트 — PM이 태스크당 1회 디스패치, T1~T5+G를 내부 디스패치(생성자·Evaluator·test-agent·checker 4축)로 완주 후 소멸. 결과 계약 6필드 반환, 비가역·계약갱신 drift는 blocked 반환(PM 에스컬레이션) |
| `backlog-tool` | - | 도구 | backlog.json SSOT 관리 CLI (8서브명령 init/add-task/select-next/mark/update-task/done-check/coverage-check/show, BACKLOG.md 자동 렌더). `covers` 필드 + `coverage-check`(표면 커버리지·통합 태스크 게이트 — surfaces.json 소비) |
| `test-tool scenario-*` | - | 도구 확장 | test-scenario.json SSOT — RED-first 동결 게이트(scenario-init/red/lock/mark/status) + 충실도·표면 게이트(scenario-fidelity-check/scenario-conformance — required_fidelity·fidelity·surface_ref 필드, 증거 충실도 사다리 mock<real-http<real-usage) + 목표-커버 게이트(scenario-coverage-check — R/F/H 매핑 결정론, exit 16/17, 073) |
| `opal-action-monitor` | - | 도구 | 루프 액션 에이전트 진행 현황판 — `.oppl-run/`(events.jsonl·journal.md·exitcode) 파싱, 단계×축 상태 렌더 + `--json`/`--watch` (읽기 전용) |
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

## 주요 컴포넌트 (TEST-SCENARIO 목표-커버 게이트)

TEST-SCENARIO 단계를 "목표 달성 검증"으로 재정의 — 루브릭 채점 기반 작은 수렴 루프(작성→커버리지 도구 게이트→독립 평가자 루브릭 채점→종료조건→재작성)를 공유 컴포넌트로 구현. 070 사건(핵심 목표 미검증 완료)의 근본 대응. **opd·opds·opsdd 3종 접합**(oppl 제외 확정 — 자체 표면-게이트+독립평가 보유 / oppd 2차 유예). (2026-07 신설 태스크 073, opds·opsdd 확산 태스크 075).

| 컴포넌트 | 약어 | 유형 | 설명 |
|----------|------|------|------|
| `analysis-core.md` | - | 규칙 SSOT | ANALYSIS·PLAN 공유 분석 절차 SSOT — 지식 선조회 3단·증분 소비·델타 탐색·분석 깊이·관련 파일 맵 6영역 축·의존성/영향 범위·품질 체크리스트. 절차는 이 문서, 산출물 형식은 각 스킬이 소유. `opal/core/references/harness/analysis-core.md` |
| `scenario-gate.md` | - | 규칙 SSOT | 루브릭 6축(①목표달성~⑥경계/부정)·판정주체 분리(②③④ 결정론/①⑤⑥ 판단)·정규화 계약·종료조건 3종(수렴/반복상한/무진전)·tool-gated 집행. `opal/core/references/harness/` |
| `op-scenario-gate` | - | 단계 스킬 | 목표-커버 루프 컨트롤 — 정규화 페이로드 빌드→coverage-check→evaluator→종료조건 판정→verdict 반환. Step 2 pilot 변환기로 재사용(opd/opds/opsdd 3종 접합, oppl 제외·oppd 2차) |
| `test-tool scenario-coverage-check` | - | 도구 확장 | R/F/H↔시나리오 매핑 누락 결정론 판정(②③④). exit 0(전커버)/16(coverage_unmet)/17(입력오류). pilot-중립 정규화 페이로드 소비 |
| `opal-evaluator-agent scenario-rubric` | - | 서브에이전트 phase | 판단축 ①목표달성·⑤채택/잔존·⑥경계/부정 2점 척도 채점(각≥1 AND 평균≥1.5→pass). SCENARIO-GATE-{N}.md 산출. 기존 3 phase additive |

> tool-gated: 게이트 PASS는 coverage-check exit 0 AND evaluator verdict pass 두 증거 필수. Producer(PM+캡틴)≠Evaluator(opal-evaluator-agent) 매반복 분리. 루프 상한 수치 SSOT는 `opal-harness.md` §1. opd STEP 3.5 접합 — pipeline.json `test_scenario.scenario_gate` 행이 EXECUTE 진입을 구조적 차단. SSOT: `opal/core/references/harness/scenario-gate.md`.
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
| `.opal/AGENT.md` | PM 프로필 | PM 역할 및 검토 기준 | Framework | 부트스트랩 시 자동 |
| `docs/PROJECT.md` | 프로젝트 정의 (SSOT) | 프로젝트 개요, 원칙, 문서 허브 | Framework | 부트스트랩 시 자동 |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 | 구조, 컴포넌트 관계, 배포 모델 | Framework | 개발 작업 시 항상 |
| `docs/CONVENTIONS.md` | 코드 및 문서 컨벤션 | 네이밍, 파일 구조, 커밋 **메시지 형식·단위**, 구현 규칙(디스패치/@header/Citation/State/도구·배포 경계·플랫폼 분기). 승인 게이트·커밋 실행 시점 등 Guards 규칙 **원문**은 `opal/core/references/opal-harness.md` §1이 소유하고 본 문서는 포인터만 둔다 | Framework | 개발 작업 시 항상 |
| `.opal/MEMORY.json` | 프로젝트 메모리 인덱스 (JSON SSOT) | 메모리·작업 히스토리·피드백 추적 (`memory/` 하위 메모리 파일 인덱스). 변경은 `memory-tool`만 수행 | Framework | 부트스트랩 시 자동 (`memory-tool show --brief` 브리핑) |
| `README.md` | 프레임워크 공개 소개 문서 | Pilot 개념, 사용 사례, 프레임워크 철학 정의 | Framework | Pilot 추가/변경 시, 사용자 대면 문서 작업 시, 프레임워크 철학/방향 관련 작업 시 |
| `docs/architecture-diagram/opal_framework_architecture.html` | 프레임워크 구조 다이어그램 (시각 SSOT) | 3층 구조·파이프라인·도구 관계 시각화 (태스크 086 산출) | Framework | 구조 설명·온보딩 시 |
| `docs/SECURITY.md` | 프로젝트 보안 기준 | opal-security-checker가 OWASP/CWE/SANS Base에 병합하는 프로젝트 누적 기준 | Framework | 보안 체크(opgc CHECK) 시 |
| `docs/proposals/opal-brain-design.md` | Project Brain 설계 SSOT | brain 구조·모드·도구 계약 설계 근거 | Framework | Brain 관련 변경 시 |
| `docs/proposals/opal-data-design.md` | Data Design 파이프라인 설계 SSOT | 사전·ERD·DDL 흐름 설계 근거 | Framework | Data Design 관련 변경 시 |

---

## 변경이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-08-23 | 분석 코어 SSOT 신설 반영 — §주요 컴포넌트에 `analysis-core.md` 행 추가(ANALYSIS·PLAN 공유 절차 SSOT, 수치 복제 없이 경로 포인터만). 태스크 100 |
| 2026-08-21 22:18 | §주요 컴포넌트 (Dev 파이프라인)에 **트랙 라우팅** 항목 신설 — `opal/core/references/harness/track-routing.md`(규칙 SSOT) 등재. `//opd` 4축 AND 자동 강등, 판정 시점 분리(강등=TASK 직후 / 승격=PLAN 결과)로 승격 규칙과 상호배타, fail-safe는 강등 불발. 임계값 수치는 SSOT 단독 보유(복제 0건) (098) |
| 2026-08-21 15:30 | 문서 레지스트리 `docs/CONVENTIONS.md` 행 정합 — 용도 서술의 `커밋 규칙`을 `커밋 메시지 형식·단위`로 정정하고 구현 규칙 열거에서 `Guards/`를 제거. Guards 규칙 원문 소유권이 `opal/core/references/opal-harness.md` §1임을 명시해, CONVENTIONS.md 포인터화(v1.7.0)와의 내부 모순을 해소 (097) |
| 2026-08-16 15:55 | STATE.md 저널화 반영 — 3-SSOT 각주에서 "사람 뷰는 자동 렌더" 전제 제거. `BACKLOG.md`는 자동 렌더 유지, `state.json` 현황 조회는 `state-tool show`로 명시(STATE.md는 의사결정 로그·블로커 저널) (Task 094) |
| 2026-08-15 16:35 | `worktree-tool` 신설 반영 — 폴더 구조맵 `opal/tools/` 행 18종 → **19종**. 태스크별 코드 작업공간 격리(`--worktree`/`--wt` 축) 집행 도구 (Task 092) |
| 2026-08-11 13:26 | 문서 최신화 — 실측 1:1 대조 반영. 폴더 구조맵에서 루트 `agents/`(부재) 행 제거하고 누락 7폴더(`opal/agents/`·`opal/tools/`·`opal/bootstrapper/`·`opal/templates/`·`dashboard/`·`cursor-rules/`·`memory/`) 추가 + `.opal/` 설명을 실제 범위(브레인·메모리·코드맵 설정·로컬 설정)로 확장. 태스크 폴더 형식을 `{NNN}-{YYMMDD}-{스킬약어}-{태스크명}`으로 교체하고 실존 예시로 갱신(태스크명 한글 기본·앞 3요소 ASCII·공백 금지 명문화). **§주요 컴포넌트 (Dev 파이프라인) 신설** — 오케스트레이터 6종(opd/opds/opdw/opp/opwt/oppd)·`op-dev-*` 단계 스킬 7종·Dev 계열 워커 에이전트 10종이 SSOT에서 통째로 누락돼 있던 것을 등재. `brain-tool` 8→**10 서브명령**(`analyze`·`ingest-scan`) 정합. §프로젝트 구성 Framework 경로에서 `agents/` 제거. §프로젝트 문서 레지스트리 4행 추가 — 아키텍처 다이어그램 HTML(태스크 086 산출, 구조 시각 SSOT)·`SECURITY.md`(본문이 이미 참조 중이던 내부 모순 해소)·`proposals/` 설계 SSOT 2종 (Task 089) |
| 2026-08-04 | 코드맵 샤드 정책 확장 — `split`(제안 `--plan`/집행 `--groups`)·`init`(`.opal/code-scan.json` 비대화형 초안 생성, 차단 게이트 앞 배치) 2서브명령 신설(13→15). 과대 매니페스트 판정을 `shardPolicy` 3단 우선순위(프로젝트 `.opal/code-scan.json` > 전역 `~/.opal/setting.json` > 코드 상수 `maxBytes` 10240/`minFiles` 40, **셀 단위 머지**) 기반 **바이트 초과(`>`) AND 엔트리 수 이상(`>=`) 2축**으로 정교화(전면 비차단, 초과만으로는 exit 0). `split --plan`은 **5단계 제안 사다리**(첫 토큰 → 1~2토큰 결합 → 전체 토큰 → 마지막 토큰 → `depends` 공유, 각 단계는 직전 단계 미분류분만 입력)로 분류하고 잔여는 `unassigned`로 남긴다(임의 배분 없음 — 의미 경계는 사람의 몫). `op-data-dictionary` 산출물 표준단어사전.md를 **읽기 전용·옵셔널**로 대조(부재·파싱 실패·매칭 0건 전부 비차단 — code-scan이 `.opal/` 밖 문서를 읽는 첫 사례이자 `~/.opal/setting.json`을 읽는 첫 도구). 구 위치 `index.json`의 `manifestMaxBytes`는 값을 읽지 않고 안내만 한다(자동 변환 없음). code-scan v1.6.0 (Task 083) |
| 2026-08-03 | 코드맵 매니페스트 샤딩 — 한 소스 디렉토리의 매니페스트를 예약 폴더 `_shards/` 아래 **의미 단위 샤드로 분산**할 수 있게 하고(베이스 매니페스트가 `shards` 라벨 배열로 선언), 샤드 해석·`byKey` 합집합·중복 판정을 `resolveShards` **1곳에 봉인**. `index.json` 최상위 `manifestMaxBytes`(기본 20480바이트)로 **파일당 크기 상한을 비차단 감지·열거** — 초과가 있어도 다른 위반이 없으면 exit 0이라 CLOSE 게이트를 봉쇄하지 않는다. 샤드 미선언 자산은 조회 8커맨드·`target`·`scaffold` stdout이 **바이트 동일**(옵트인). `_shards` 예약어 충돌·라벨 path traversal 차단. code-scan v1.5.0 (Task 082) |
| 2026-08-02 | 코드 헤더 소스 단일화 — 기록 소스를 전역 `headerSource`(`inline`\|`manifest`) 2택 단일 키로 통일하고 `auto`·`readonly`·스코프별 오버라이드 3종을 폐기. 미설정·무효값은 전 명령 차단(암묵 기본값 금지), CLI `--header-source` > 전역 config 2층 우선순위. `scopes` 객체 형식(`include`/`exclude`) 파일 집합 필터 도입 — 판정 지점을 `resolveHeaderSource`·`isInScope` 각 1곳으로 봉인. code-scan v1.4.0 (Task 080) |
| 2026-07-23 | 파이프라인 todo 미러 hook 강제 자동화 — state-tool todo_mirror 페이로드 출력(init/advance/mark/block, stdout 전용·비영속) + PostToolUse hook 결정론 트리거(claude-hooks.json) + install merge_hooks 소유권-마커 멱등 upsert(외부 hook clobber 해소) + state.md 정합. prose 의존 → tool 강제(헌법 Enforce). S-9 L3(새 세션 todo 패널 실증) 후속 (Task 076) |
| 2026-07-23 | 목표-커버 게이트 opds·opsdd 확산 — op-scenario-gate Step 2 pilot 변환기(opds=opd동형/opsdd=SPEC.md FR·AC·EC 소스) + opds STEP 2(producer 확립·op-dev-plan 미접촉)·opsdd Phase 2 REVIEW(수동 커버리지→도구 게이트·self-confirming 해소) 배선. oppl 제외·oppd 2차. 신규 컴포넌트 0(배선만) (Task 075) |
| 2026-07-23 | TEST-SCENARIO 목표-커버 게이트 섹션 신설 — scenario-gate.md(규칙 SSOT)·op-scenario-gate(단계 스킬)·test-tool scenario-coverage-check(도구 확장)·opal-evaluator-agent scenario-rubric(phase). opd STEP 3.5 pipeline.json 게이트 행 접합(EXECUTE 진입 구조적 차단). 070 목표 미검증 완료 재발 방지, 1차 opd 선적용 (Task 073) |
| 2026-07-18 | Project Loop 표 backlog-tool(8서브명령 — covers·coverage-check)·test-tool scenario-*(fidelity·conformance 게이트) 정합 — oppl 계약 접합면 검증 강화: 표면 인벤토리(surfaces.json)·증거 충실도 사다리·여정 스모크·워킹 스켈레톤 의무 도입 (Task 069) |
| 2026-07-17 | Project Loop 표에 opal-loop-action-agent(루프 액션 에이전트) 행 추가 — 태스크당 1회 디스패치·내부 4축·blocked 계약 (Task 065) |
| 2026-07-17 | Project Loop 표에 oppl-monitor 행 추가 — `.oppl-run/` 파싱 진행 현황판(--json/--watch, 읽기 전용). 내부 채널 stream-json 전환·journal 규약과 함께 도입 (Task 067) |
| 2026-07-17 | 도구명 리네임 — `oppl-monitor` → `opal-action-monitor`(향후 oppd·opsdd 액션 에이전트 공통 관측 도구로 확장 예정이라 이름 중립화). Project Loop 표 행 갱신, 로직 무변경 (Task 067) |
| 2026-07-17 | Project Loop 표에 opal-action-status(opas) operator 행 추가 — 액션 에이전트 현황 발동층(자동 탐지+해석 보고, 읽기 전용) (Task 068) |
| 2026-06-12 | Data Design 파이프라인 섹션 추가 — opal-pilot-data-design(opdd), op-data-* 3종, opal-db-agent (Task 019) |
| 2026-06-15 | OPAL Console 섹션 추가 — dashboard/frontend(React+shadcn)·backend(FastAPI)·opal-cli console + 프로젝트 구성 Console FE/BE 영역 (Task 021) |
| 2026-06-18 | SDD 컴포넌트 표 정합 — op-sdd-tasks dangling 제거 + op-sdd-action-plan 등록. opal-brain 유형 오기재 교정 (오케스트레이터/Pilot → operator 멀티모드 라우터, alias opbr 불변) (Task 029) |
| 2026-06-22 | OPAL Console 6번째 메뉴 "프로젝트 브레인" 추가 — brain 질의(`//opbr query --read-only` 구독 합성·POST 격리·브라우저 localStorage 이력) + opbr SKILL v1.4 비대화형 read-only 계약 (Task 036) |
| 2026-06-30 | 부트스트랩 2-tier 전환 — 비서(전역 상시)/PM(opi 프로젝트 opt-in) 분리. AGENT.md Eager 2-phase·부트스트래퍼 절 반전·opi Codex AGENTS.md 보강·ARCHITECTURE 2-tier 절 (Task 049) |
| 2026-07-10 | Project Loop 파이프라인 섹션 추가 — opal-pilot-project-loop(oppl)·opal-evaluator-agent·backlog-tool·test-tool scenario-* 확장 (Task 056) |
| 2026-07-10 | OPAL Console `opal-cli console` 설명에 scan 서브명령 반영 — console.config.json 생성·머지 + install 1회 자동 실행 (Task 057) |
| 2026-07-14 | OPAL Console 7번째 화면 "설정" 반영 — 프라임 풀 토글 단일 기능, 설정 라우터 쓰기 격리(화이트리스트), 쓰기 예외 2종 명시 (Task 061) |
| 2026-07-15 | OPAL Console 프로젝트 브레인 세션 단순화 — 휘발성 단일 세션(localStorage 이력·멀티대화 관리 제거, 진입/새대화마다 새 세션·세션 내 멀티턴 유지), 프라임 풀 크기 1→2 + need 충전(연속 새대화 즉시 웜), 이탈 가드 4경로(메뉴·새로고침·프로젝트 스위처·새 대화 시 세션 소멸 확인) (Task 063) |
| 2026-07-17 | PM 개선 루프 서브시스템 신설 — opal-improve(opim) 스킬·improve-tool 도구·fw-inbox 수집소·4 pilot CLOSE 회고 하드스텝. 정의 3문서를 단일 SSOT(pm-improvement-loop.md)로 통합, memory-tool enum 확장(improvement/candidate), 로컬/FW 학습 분리 (Task 058) |
| 2026-07-28 | 코드 헤더 작성층 신설 — code-scan v1.3.2에 discover/scaffold/target/validate/feature 5서브명령 + 인라인·외부 소스 코드 지도(`.opal/code-map/`) 2소스 5단 상속 해석. 기록 위치 4단 자동 판정·워커 권한 경계·PostToolUse hook·`run.sh` 래퍼 신설. CLOSE 게이트는 회귀(`newly_uncovered`)만 차단하고 레거시 미커버는 비차단 보고 (Task 077) |
| 2026-07-28 | 프로젝트 메모리 SSOT 전환 — 문서 레지스트리 행 `.opal/MEMORY.md` → `.opal/MEMORY.json`(JSON SSOT, 변경은 memory-tool 전용), 참조 시점을 `memory-tool show --brief` 조회로 명시 (Task 078) |
