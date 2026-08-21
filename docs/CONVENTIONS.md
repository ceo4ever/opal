# 코드 컨벤션

> OPAL 프레임워크 작성 규칙

## 언어 규칙

| 대상 | 규칙 |
|------|------|
| 문서 본문 | 한국어 (기술 용어는 영어 병기) |
| 코드/변수/필드명 | English |
| YAML frontmatter 키 | English |
| 파일/폴더 이름 | English, kebab-case (Python 파일은 snake_case) |

## 네이밍 규칙

### 파일/폴더

- **kebab-case** 사용: `user-auth-implementation`, `op-dev-plan` (Python 파일은 **snake_case**: `creative_response.py`, `user_auth.py`)
- 스킬 폴더: `{그룹}-{역할}` — `opal-pilot-dev`, `op-dev-analysis`, `op-task-qa`
- 에이전트 폴더: `opal/agents/{agent-name}/` — 에이전트는 모두 이 경로 하나에 둔다 (루트 `agents/` 없음)
  - 전체 15종: `opal-task-agent`, `opal-task-action-agent`, `opal-task-qa-agent`, `opal-loop-action-agent`, `opal-sdd-action-agent`, `opal-plan-agent`, `opal-planning-agent`, `opal-fe-agent`, `opal-be-agent`, `opal-db-agent`, `opal-test-agent`, `opal-wtm-agent`, `opal-evaluator-agent`, `opal-convention-checker`, `opal-security-checker` (상세: `opal/agents/`)
- 전문 에이전트 네이밍: `opal-{domain}-agent` — `opal-fe-agent`, `opal-be-agent`, `opal-db-agent`
- 태스크 폴더: `{NNN}-{YYMMDD}-{스킬약어}-{태스크명}` — `088-260811-opp-클로즈-메모리히스토리-자동연결`, `080-260801-opd-헤더소스-단일화`
  - `{태스크명}`은 **[기본] 한글**로 작성한다. 영문 kebab-case·혼용은 소유자가 명시 요청할 때만 사용한다.
  - **공백 금지**(셸 안정성), 단어 구분은 하이픈(`-`), 앞 3요소(`{NNN}-{YYMMDD}-{스킬약어}`)는 **ASCII 고정**(파싱 안정성).
  - `{YYMMDD}`는 `node ~/.opal/tools/date/date.js yymmdd`로 취득한다 (KST 기준, 추측 금지).
  - SSOT: `opal/core/references/harness/task-process.md` §태스크 번호 채번 규칙 · §저장 경로 규칙
- SDD 명세 폴더: `specs/{NNN}-{feature-name}/` — 순번 3자리 0-패딩, kebab-case

### 컴포넌트 네이밍 체계

| 접두사 | 의미 | 예시 |
|--------|------|------|
| `opal-pilot-*` | 오케스트레이터 | opal-pilot-dev, opal-pilot-write-tech, opal-pilot-project |
| `op-dev-*` | dev 도메인 단계 스킬 | op-dev-analysis, op-dev-plan, op-dev-qa |
| `op-task-*` | 범용 단계 스킬 | op-task, op-task-qa, op-task-plan, op-task-execute |
| `opal-task-*` | 범용 워커 에이전트 | opal-task-agent |
| `opal-{domain}-agent` | 전문 워커 에이전트 | opal-fe-agent, opal-be-agent, opal-db-agent, opal-plan-agent, opal-test-agent, opal-planning-agent |
| `op-sdd-*` | SDD 단계 스킬 | op-sdd-spec, op-sdd-verify, op-sdd-plan, op-sdd-action-plan |
| `opal-*` | OPAL 프레임워크 전용 | opal-project-init, opal-onboarding |

### 약어 (Alias)

> **SSOT: `opal/core/references/opal-skills-registry.json`** — 약어의 등록·변경은 레지스트리에서만 수행한다.
> 아래 표는 레지스트리의 사본이며, 불일치 시 레지스트리가 우선한다. 현재 **27종**.

**오케스트레이터 (파일럿)**

| 약어 | 풀네임 |
|------|--------|
| opp | opal-pilot-project |
| opd | opal-pilot-dev |
| opds | opal-pilot-dev-short |
| opdw | opal-pilot-dev-wireframe |
| opwt | opal-pilot-write-tech |
| opsdd | opal-pilot-sdd |
| opgc | opal-pilot-gc |
| opdd | opal-pilot-data-design |
| oppd | opal-pilot-project-dev |
| oppl | opal-pilot-project-loop |

**프레임워크 운영**

| 약어 | 풀네임 |
|------|--------|
| opi | opal-project-init |
| onb | opal-onboarding |
| next | opal-next |
| help | opal-help |
| osc | opal-skill-creator |
| oac | opal-agent-creator |
| osm | opal-skill-manager |
| opbr | opal-brain |
| opas | opal-action-status |
| opws | opal-workspace-sync |
| opim | opal-improve |

**독립 스킬**

| 약어 | 풀네임 |
|------|--------|
| wfb | wireframe-builder |
| uid | ui-designer |
| wtm | web-to-markdown |
| erm | erd-modeler |
| mockup | html-mockup |
| html-sa | system-architecture-html |

## 파일 구조

### 스킬 구조

```
skills/{skill-name}/
├── SKILL.md              필수 — YAML frontmatter + 프로세스 정의
├── references/           선택 — 상세 가이드 (참조 문서)
│   └── {guide-name}.md
└── personas/             선택 — 페르소나 정의
    └── {persona-name}.md
```

### 에이전트 구조

```
opal/agents/{agent-name}/    에이전트 (전문 + 범용) — 단일 경로
└── AGENT.md                 필수 — YAML frontmatter + 입출력 명세 + 실행 프로세스
```

### YAML Frontmatter

스킬과 에이전트 모두 YAML frontmatter를 포함한다:

```yaml
---
name: {컴포넌트 이름}
description: |
  {설명 — 트리거 키워드 포함}
triggers:             # 스킬만
  - "{트리거 문구}"
version: {X.Y.Z}     # 스킬만
model: {모델}         # 에이전트만
icon: {이모지}         # 에이전트만 (선택, 디폴트: ✨)
---
```

### 변경이력

스킬, 에이전트, 참조 문서의 변경이력은 일시(KST)를 포함한다:

```markdown
## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-30 14:00 | 초기 작성 |
```

- 일시 형식: `YYYY-MM-DD HH:mm` (KST 기준)
- 버전: semver (`vX.Y.Z`)

### 태스크 산출물 구조

```
tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/
├── TASK.md               요구사항 정의
├── ANALYSIS.md           코드베이스 분석 (Full Task)
├── PLAN.md               구현 계획
├── TEST-SCENARIO.md      테스트 시나리오
├── state.json            상태 SSOT — state-tool이 소유 (직접 편집 금지)
├── STATE.md              의사결정 로그·블로커 저널 (로그는 도구 자동, 블로커·자유기재는 PM 수동)
├── AGENTIC-LOG.md        agentic 실행 로그
├── GC-*.md               GC 체크 보고서 (opal-pilot-gc 실행 시)
└── DONE.md               완료 보고
```

- STATE.md는 **의사결정 로그·블로커·자유 기재를 담는 저널**이다. 파이프라인 현황(행 상태·진행·다음 액션)의 SSOT는 `state.json`이며, 조회는 `state-tool show`로 한다. `state.json`은 `state-tool`이 전량 갱신하고, STATE.md는 저널 골격 보증(`ensure_journal_skeleton`)과 의사결정 로그 기재(`append_decision_log`)만 `state-tool`이 자동 수행하며, 블로커 내용·자유 기재는 PM이 수동으로 기록한다.

## 브랜치 전략

- `main`: 안정 브랜치이자 **기본 작업 브랜치** — 태스크 커밋은 브랜치 분리 없이 main에 직접 수행한다.
- 예외적으로 브랜치를 분리할 때는 `feat/{NNN}-{스킬약어}-{설명}` 형식을 쓰고, 태스크 완료 후 main에 머지한다.
- **위 규칙은 OPAL 저장소 자체에만 적용된다.** `--worktree`/`--wt`로 생성하는 **대상 프로젝트의 코드 브랜치**는 `{프로젝트}/.opal/worktree.json`의 `branchTemplate`(기본 `feat/OP-TASK-{NNN}`)을 따르며 본 절의 적용 대상이 아니다. 두 규칙은 충돌이 아니라 **적용 대상이 다른 별개 규칙**이다 (092 DEC-1).

## 커밋 규칙

### 형식

```
{type}({scope}): {한국어 설명}
```

### Type

| type | 용도 |
|------|------|
| feat | 새 스킬, 에이전트, 기능 추가 |
| fix | 버그 수정 |
| refactor | 리팩토링 (동작 변경 없음) |
| chore | 메모리 정리, 설정 변경 등 |
| docs | 문서만 변경 |

### Scope

태스크 번호 사용: `feat(043): opal-doc-standard v2.0`

### 규칙

- 커밋 실행 시점 규칙(사용자 요청 시에만 수행 · 자동 커밋 금지)은 `opal/core/references/opal-harness.md` §1 Guards가 소유한다 — 본 절은 커밋 **메시지 형식·단위**만 규정한다.
- 커밋 메시지는 한국어
- 하나의 태스크 = 하나의 커밋 (원칙)
- CLOSE 시 메모리 히스토리 행은 `state-tool mark`가 자동 생성한다(088). PM은 `result` 필드를 보강한 뒤 커밋하며, 히스토리 갱신용 별도 커밋을 만들지 않는다.

## 구현 규칙

OPAL 본체(스킬·에이전트·도구·하네스)를 작성할 때 따라야 할 규칙. 워커가 코드/문서를 작성할 때 이 절을 직접 참조한다.

### Guards (구현 금지·승인 게이트)

- 사용자가 명시적으로 "승인", "진행해", "구현해" 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다.
  - 허용: 산출물 문서(.md) 작성, QA 에이전트 호출, 코드베이스 읽기·분석
  - 금지(승인 전): 소스 코드 파일 생성·수정, 패키지 설치, 설정 파일 수정
- CLOSE 단계 진입 직전에는 사용자의 명시적 확인(`승인`/`확인`/`확인완료`)이 반드시 있어야 한다 (agentic/semi-agentic 모드에서도 유지).
- 근거: `opal/core/references/opal-harness.md` §1 Guards

### 디스패치 의무

- 오케스트레이터 SKILL.md에서 "워커 디스패치"로 정의된 단계(ANALYSIS/PLAN/EXECUTE 등)는 반드시 서브에이전트를 디스패치한다. PM이 직접 실행으로 대체하지 않는다.
- 근거: `opal/core/references/opal-harness.md` §1 디스패치 의무 원칙

### @header 규칙

- 코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다 (해당 확장자에 한해).
- **기록 위치는 `code-scan target <file>` 판정을 따른다** — 인라인 주석 또는 외부 소스 코드 지도(`.opal/code-map/`) 2소스 중 하나이며, 사람·워커가 임의 선택하지 않는다(전역 `headerSource`가 `manifest`이면 code-map 강제).
- **기록 소스는 `.opal/code-scan.json`의 전역 `headerSource` 단일 키가 결정한다** — `inline` \| `manifest` 2택이며 스코프별 오버라이드는 없다. 미설정·무효값이면 code-scan 전 명령이 exit 1로 차단된다 (Task 080).
- 변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 헤더 내 변경이력 라인으로 갱신한다.
- 근거: `opal/core/references/harness/header-rules.md`, `opal/core/references/header-standard.md` §7(2소스 표현)

### Citation Rules (인용)

- TASK.md / PLAN.md / ANALYSIS.md / QA 산출물 등을 작성할 때 모든 주장은 근거를 인용한다 (`{경로}:{라인}` 또는 `docs/문서명 §섹션`).
- `[MUST]` 토큰이 붙은 항목은 인용 누락 시 산출물 부적합 처리.
- 근거 등급(E1 실행 관측 ~ E5 파생 스냅샷)과 AS-IS/TO-BE 관할 2축의 규정 **원문**은 `opal/core/references/harness/citation-rules.md` §9 근거 등급과 관할이 소유한다 — 본 문서는 포인터만 둔다.
- 근거: `opal/core/references/harness/citation-rules.md`

### State 관리

- **[MUST] 파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다.**
- 단계 진입/완료/차단/추가작업 행 삽입 모두 state-tool 서브 명령(`init`/`advance`/`mark`/`block`/`add-row`/`spec-validate` 등)으로 처리한다.
- 행 주소는 `--task-step <key>`(예: `plan.pm_gate`) 우선 사용, `--task-step-id <N>`은 숫자 폴백 — `--row`는 deprecated 별칭(신규 문서·프롬프트에 사용 금지). key 정의는 pilot `references/pipeline.json`이 SSOT.
- `state-tool init --rows-from`은 pilot `references/pipeline.json`을 지정한다. SKILL.md 마크다운 파싱(`build_rows_from_skill_md`)은 deprecated이며 신규 지시에 사용 금지 — **10/10 pilot 전환 완료(090)**.
- **PM Gate 정의의 SSOT는 pilot `references/pipeline.json`의 `task_steps[].gate`**(`artifacts`·`checklist`)다 — SKILL.md에 산출물·체크리스트를 표로 중복 게재하지 않는다. `mark`가 `artifacts` 존재를 결정론 검증하여 미충족 시 `gate_artifact_missing`으로 거부하고, 통과 시 `checklist`를 stdout `gate_checklist`로 반환한다. `artifacts`에는 **해당 게이트 시점에 반드시 존재하는 태스크 폴더 기준 상대 경로/글롭만** 올린다 — 조건부 산출물·논리 개념은 `checklist`에 문안으로 둔다(잘못 올리면 그 게이트가 영구 차단된다). `--force --note`로 우회하면 STATE.md 의사결정 로그에 `gate_artifact_force`가 강제 기록된다 (091).
- 파이프라인 "사용자 확인" 행은 전 모드 `pending / owner=PM`으로 초기화되며, 다음 단계 진입 시 `state-tool`이 자동 승인한다(`done / owner=auto / timestamp`). 자동 승인 불가 구간(CLOSE 직전·interactive·semi-agentic의 `MODE_BOUNDARY_STAGES`)에서는 `user_confirmation_required` 에러가 반환되며 캡틴 승인(`mark --owner user`)이 필요하다 (093).
- 근거: `opal/core/references/opal-harness.md` §3 State

### 도구 우선 원칙

- 파일 처리·데이터 변환 작업이 필요할 때, 직접 코드를 작성하기 전에 OPAL 도구(`~/.opal/tools/`)를 우선 검토한다.
- 상시 사용 핵심 도구: `state-tool`, `code-scan`, `memory-tool`, `brain-tool`, `test-tool`, `backlog-tool`.
- **전체 목록: `opal/tools/` (19종)** — 위 6종 외 `xlsx-tool`, `skill-registry`, `playwright-tool`, `improve-tool`, `cmux-tool`, `git-sync-tool`, `worktree-tool`, `date`, `doctor`, `tool-scan`, `opal-cli`, `opal-agent`, `opal-action-monitor`.
- 근거: `opal/core/references/opal-harness.md` §9 OPAL Tools

### 변경이력 작성 의무

- 스킬·에이전트·참조 문서를 변경하면 "## 변경이력" 표에 행을 추가한다.
- 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(138)`.
- 배포 시 `install-mac.sh`가 변경이력 섹션을 자동 strip 한다 (소스에는 유지, 배포본에서는 제거).

### 배포 경계

- `~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다.
- 변경 후 `./scripts/install-mac.sh`(또는 후속 `opal install`)로 재배포하여 검증한다.
- **런타임 사용자 데이터 쓰기는 이 금지의 대상이 아니다** — skill-manager가 스킬 설치/제거 시 `~/.opal/community-skills/`(스킬 본체·`user-registry.json`)를 갱신하는 것은 사용자 요청 기반 런타임 데이터 조작이며, 프레임워크 파일 직접 편집과 구분된다.
- **커뮤니티 스킬 레지스트리 이원 경계**: 프레임워크 카탈로그는 소스 `opal/core/references/community-skills-registry.json`에만 실재하며(루트 `community-skills/` 디렉토리는 없다), 배포본(`~/.opal/references/community-skills-registry.json`)은 install이 덮어써 갱신을 전파하고, 사용자 설치 등록분은 `~/.opal/community-skills/user-registry.json`(install 불가침 — 142 D-4)에 기록한다. 사용자 등록분을 references 쪽에 기록하지 않는다 (Task 064).

### 플랫폼 분기 격리

- Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층(부트스트래퍼·`emit_platform_agent_adapter`·MCP install 분기)에서만 흡수한다.
- 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다 (행위는 플랫폼 독립적으로 기술하고, 도구명은 어댑터에 위임).

---

> **참고 — 허브+링크 모델**
> OPAL 프레임워크 자체는 단일 `docs/CONVENTIONS.md`를 사용한다(단일 진입점).
> 다중 구성(FE/BE/Batch/Mobile 등) 프로젝트는 허브+링크 모델 적용 가능 —
> 영역별 상세 문서(`FE-CONVENTIONS.md`, `BE-CONVENTIONS.md` 등)를 분리하고 본 허브에서 링크로 연결한다.
> 규약: `opal/core/references/conventions-hub-model.md` 참조.

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.1.0 | 2026-08-11 13:26 | 실측 대조 기반 전면 최신화 — 태스크 폴더·에이전트 경로 네이밍 정정, 에이전트 15종·alias 27종·도구 18종 인벤토리 반영, 브랜치·커밋·State·배포 경계를 현행 관행에 정합, 변경이력 절 신설 (089) |
| v1.2.0 | 2026-08-13 17:19 | §State 관리에 행 원천 규칙 1줄 추가 — `init --rows-from`은 pilot `references/pipeline.json`을 지정하며 SKILL.md 마크다운 파싱(`build_rows_from_skill_md`)은 deprecated·신규 지시 사용 금지. 미전환 6 pilot(opdd·opgc·opwt·opsdd·oppl·oppd) 이관으로 10/10 전환 완료, deprecated 경로 호출자 0건 (090) |
| v1.3.0 | 2026-08-14 09:38 | §State 관리에 PM Gate 정의 SSOT 규칙 추가 — 게이트 산출물·체크리스트의 원천을 pilot `references/pipeline.json` `task_steps[].gate`로 확정하고 SKILL.md 표 중복 게재를 금지. `mark`의 `artifacts` 결정론 존재 검증(`gate_artifact_missing` 거부)·`checklist` stdout 반환(`gate_checklist`)·`--force --note` 우회 시 `gate_artifact_force` 의사결정 로그 강제를 명문화. artifacts 적격 토큰을 "게이트 시점 필재 상대 경로/글롭"으로 한정(조건부 산출물·논리 개념은 checklist로 — 오등재 시 영구 차단) (091) |
| v1.4.0 | 2026-08-15 16:35 | 도구 인벤토리 18종 → **19종**(`worktree-tool` 추가) + §브랜치 전략에 **적용 범위 명시** — 본 절 규칙은 OPAL 저장소 자체 전용이고, worktree 대상 프로젝트의 코드 브랜치는 `{프로젝트}/.opal/worktree.json` `branchTemplate`(기본 `feat/OP-TASK-{NNN}`)을 따른다. 두 규칙의 충돌이 아니라 적용 범위 미표기가 문제였다 (092 DEC-1) |
| v1.5.0 | 2026-08-15 21:48 | §State 관리에 사용자 확인 행 자동 승인 계약 1줄 추가 — 전 모드 `pending/owner=PM` 초기화, 다음 단계 진입 시 state-tool 자동 승인(`done/owner=auto/timestamp`), 자동 승인 불가 구간(CLOSE 직전·interactive·semi-agentic `MODE_BOUNDARY_STAGES`)의 `user_confirmation_required` 거부와 캡틴 `mark --owner user` 승인 명문화 (093) |
| v1.6.0 | 2026-08-16 13:36 | STATE.md 저널화 반영 — §State 관리 첫 항목을 도구 규율 표준 문구로 교체("마크다운 표 직접 편집 금지" 서술 제거 + `state-tool show <task-path>` 조회 경로 명시), §태스크 산출물 구조의 STATE.md 행 설명을 "의사결정 로그·블로커 저널"로 정정, "상태 SSOT는 state.json이며 STATE.md는 이를 렌더한 읽기용 뷰다" 서술을 "STATE.md는 의사결정 로그·블로커·자유 기재를 담는 저널이며 파이프라인 현황의 SSOT는 state.json, 조회는 state-tool show"로 교체 — STATE.md는 더 이상 state.json의 렌더 뷰가 아니다 (094) |
| v1.6.1 | 2026-08-16 15:05 | §태스크 산출물 구조 STATE.md 행 말미 정정 — "두 파일 모두 `state-tool`이 갱신한다"(부정확, 블로커·자유 기재는 도구 미접촉)를 코드 실측(`state_tool.py` `ensure_journal_skeleton`/`append_decision_log`/`cmd_block`) 기준으로 "state.json은 state-tool 전량 갱신, STATE.md는 저널 골격·의사결정 로그만 자동 갱신, 블로커·자유 기재는 PM 수동"으로 세분화 (094 Step 14) |
| v1.7.0 | 2026-08-21 15:30 | 커밋 실행 시점 규칙의 원문 복제 2건을 하네스 포인터로 축약 — §커밋 규칙 §규칙 첫 항목과 §구현 규칙 §Guards 커밋 항목을 제거하고, 규칙 소유권이 `opal/core/references/opal-harness.md` §1 Guards에 있음을 명시. 본 문서는 커밋 **메시지 형식·단위**만 규정한다. 에이전트 행동 Guard를 코드 컨벤션 문서에 복제하면 프로젝트마다 존재 여부가 갈리는 우발 경로가 되므로, 워커 도달은 `pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿의 전 워커 공통 고정 항목이 담당한다 (097) |
| v1.8.0 | 2026-08-21 22:18 | §Citation Rules에 근거 등급·관할 SSOT 포인터 1줄 추가 — 등급 5단계(E1~E5)와 AS-IS/TO-BE 관할 2축의 원문 소유권이 `opal/core/references/harness/citation-rules.md` §9임을 명시. 본 문서는 포인터만 두어 등급표 복제를 차단한다 (098) |
