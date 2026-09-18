---
name: opal-pilot-project-build
description: |
  **프로젝트 빌드 오케스트레이터**. 이미 확정된 실행 계약을 capability 단위 미니 태스크로 무인 소화한다.
  프로젝트 worktree 하나·OPAL 태스크 하나 안에서 비충돌 미니 태스크를 병렬 실행하며, 미니 태스크마다
  worktree·branch·태스크 번호·문서 파이프라인을 만들지 않는다. 실행 계약은 `INTENT.md` 하나로 확정하고,
  기존 OPAL 프로젝트에서는 `docs/PROJECT.md` 문서 레지스트리가 등록한 현재 범위 관련 문서만 읽어
  PRD·TRD를 신규 생성하지 않는다. P0~P5 여섯 단계와 사용자 게이트 6종만 외부 표면으로 노출하고,
  스케줄·예산·lease·checkpoint·evidence는 `oppb-runtime-tool`이 결정론적으로 집행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-project-build", "oppb", "프로젝트 빌드", "capability 빌드".
  목표·계약·완료조건을 한 번의 설계 승인으로 잠글 수 있는 프로젝트에 사용한다. 수렴형 프로젝트(oppl)·
  제품 명세 라이프사이클(oppd)과는 독립된 네 번째 프로젝트 Pilot이며 대체·후계 관계가 아니다.
triggers:
  - "^opal-pilot-project-build$"
  - "^oppb$"
  - "(?i)(프로젝트\\s*빌드|capability\\s*빌드)"
version: 1.0.0
---

# opal-pilot-project-build (oppb)

확정된 실행 계약을 **프로젝트 worktree 1개 · OPAL 태스크 1건 · 실행 계약 문서 1개**로 완주시킨다.
사용자와 미니 태스크가 마주하는 표면은 P0~P5 여섯 단계와 §사용자 게이트의 6개 호출 시점뿐이며,
DAG·Ready queue·예산·lease·candidate checkpoint·evidence는 `oppb-runtime-tool`이 소유한다.

설계 SSOT는 `docs/proposals/opal-oppb-project-build-pilot.md`다. 이 스킬은 그 문서의 §5(P0~P5)·§7(문서)·
§11(사용자 게이트)을 진입점 절차로 옮긴 것이며, 충돌하면 제안서가 이긴다.

## 사용 기준

다음 질문에 `예`일 때 OPPB를 선택한다.

> 한 번의 설계 승인으로 목표·계약·완료조건·백로그를 잠그고, 이후 변경을 예외로 처리할 수 있는가?

| 조건 | 선택 |
|---|---|
| 계약을 잠글 수 있고 capability 단위 수직 분할과 변경 소유권 분리가 가능하다 | **OPPB** |
| 실행 증거가 목표·계약·백로그를 정상적으로 바꾼다 | OPPL (`//oppl`) |
| 제품 명세(PRD·TRD) 작성부터 필요하다 | OPPD (`//oppd`), 또는 `//opwt`로 명세를 먼저 만들고 OPPB로 실행 |
| 단일 태스크로 끝나는 규모다 | `//opd`·`//opds` |

> **[MUST]** OPPB는 기존 Pilot을 교체하지 않는다. `//oppd`·`//oppl`·`//opsdd`의 스킬·상태·회귀는 무변경이며
> OPPB 결함의 복구 경로는 revert가 아니라 "`//oppd`를 그대로 쓴다"이다. 따라서 **실행 방식 선택 옵션·
> `--engine` 플래그·런타임 라우터를 만들지 않는다.** 하나의 Pilot 안에 두 실행 경로를 넣지 않는다.

---

## Harness

모드: Project Build (P0 → P5 단방향, 미니 태스크만 Repair 재진입)

**[MUST — pilot.start 이벤트 게이트]** 파일럿의 첫 작업 전에 아래 순서를 수행한다.

1. `~/.opal/tools/event-loader/run.sh load --event pilot.start > <pilot-receipt-path>`를 호출한다.
2. load 응답의 `documents[].content` 전문을 모두 현재 컨텍스트에 적용하고, `modes` 문서가 현재 플래그에 대해 라우팅한 서브 하네스 전문 하나만 Read한다.
3. `~/.opal/tools/state-tool/run.sh event-verify --event pilot.start --receipt <pilot-receipt-path>`가 성공한 뒤에만 진행한다.

**[MUST — 단계 이벤트 게이트]** 각 단계의 첫 작업이나 `state-tool advance` 직전에 아래 매핑의 이벤트를 load하고, 응답 문서 전문을 적용한 뒤 같은 event id로 `state-tool event-verify`를 통과해야 한다.

| 단계 | 이벤트 |
|---|---|
| P0 ENTRY & CONTEXT | stage.task |
| P1 INTENT | stage.analysis |
| P2 PROJECT DESIGN & SLICE | stage.plan |
| P3 CONTINUOUS MINI-TASK EXECUTION | stage.execute |
| P4 PROJECT VERIFY | stage.test |
| P5 MERGE · KNOWLEDGE · CLOSE | stage.close |

호출 형식은 `~/.opal/tools/event-loader/run.sh load --event <stage.*> > <stage-receipt-path>` 다음
`~/.opal/tools/state-tool/run.sh event-verify --event <stage.*> --receipt <stage-receipt-path>`이다.
문서 집합은 `events.json`만 SSOT로 사용하며 SKILL에 파일 목록을 복제하지 않는다. load 실패, 필수 문서
누락, stale receipt, wrong-event receipt는 해당 단계 진입을 즉시 중단하는 blocker다. 부트 캐시를 근거로
공통 문서를 직접 재Read하는 우회는 금지한다.

---

## 계층 · 핵심 개념

**계층**: 프로젝트(= OPAL 태스크 1건) > 미니 태스크(capability 1개) > work item(같은 미니 태스크 내부 FE·BE·DB 작업).
미니 태스크는 OPAL 태스크가 아니다 — 번호·폴더·worktree·branch를 갖지 않고 `workgraph.json`의 record로만 존재한다.

**2-SSOT 축 분리**: 프로젝트 바깥 단계와 미니 태스크 내부 상태는 서로 직접 쓰지 않는다.

| SSOT | 도구 | 관리 대상 | 조회 |
|---|---|---|---|
| `state.json` | `state-tool` | P0~P5 프로젝트 파이프라인 행 | `state-tool show <task-path>` |
| `workgraph.json` | Controller (`oppb-runtime-tool`) | 미니 태스크 DAG·계약·예산·상태 | `oppb-runtime-tool workgraph` |

> **[MUST]** Controller는 `state.json`을 쓰지 않고, Product Flow는 `workgraph.json`을 쓰지 않는다. P0~P5 전이는
> Product Flow가 `state-tool`로만, 미니 태스크 전이는 Controller가 revision lock 아래 `workgraph.json`으로만 수행한다.
> `state.json` 직접 편집은 금지한다.

**책임 경계** (제안서 §4 원문이 SSOT — 여기서는 진입점이 지켜야 할 경계만 옮긴다):

| 주체 | 수행 | 금지 |
|---|---|---|
| OPPB Product Flow (이 스킬) | 진입점·조건부 Discovery·사용자 게이트·최종 경험 | 프로세스 직접 감시·미니 태스크 직접 디스패치 |
| PM Agent | INTENT 확정·설계 승인·계약 변경·귀속 불명 실패 판단 | 작업 프로세스 수확·Git 조작·코드 구현 |
| Controller·Supervisor·Lease·Checkpoint·Evidence | 상태·예산·스케줄·격리·증거 | 자연어 설계·코드 수정 |
| `opal-capability-agent` | 미니 태스크 하나의 RUN·PROVE·내부 통합 | Git·Controller state·MEMORY·brain 수정 |

> **[MUST] 신규 owner는 `opal-capability-agent` 1종뿐이다.** 미니 태스크 실행 경로는 이 에이전트 하나이며,
> **`opal-task-action-agent`를 직접 호출하지 않는다.** 그 에이전트는 `//oppd`의 실행 에이전트로 계속 살아 있고
> OPPB는 호출하지 않을 뿐 제거하지 않는다. 전문·검증 역할은 기존 에이전트를 재사용한다 (§디스패치).

---

## 사전 조건 체크

`//oppb` 호출 시 프로젝트 루트를 판정한다.

| 조건 | 동작 |
|---|---|
| `docs/PROJECT.md` 존재 (기존 OPAL 프로젝트) | P0 시작 — 레지스트리 라우팅 경로 |
| `docs/PROJECT.md` 미존재 (greenfield) | opi 자동 실행 → 완료 후 oppb 복귀 — greenfield 분기 |

**opi 자동 실행 시**:
1. 사용자의 원래 요청을 보존한다.
2. `~/.opal/skills/opal-project-init/SKILL.md`를 Read하여 opi를 실행한다.
3. opi 완료 즉시, 보존한 원래 요청으로 oppb P0을 시작한다.

greenfield에서 생성하는 문서는 `PROJECT.md` 하나다. opi가 만드는 것 외에 PRD·TRD를 이 시점에 만들지 않는다.

---

## 문서 라우팅 — PRD·TRD 신규 생성 0

> **[MUST]** 기존 OPAL 프로젝트에서 관련 문서가 충분하면 **PRD·TRD를 신규 생성하지 않는다.** 이것은 권고가
> 아니라 수용기준 1이다.

| 프로젝트 상태 | 읽는 문서 | 생성 문서 |
|---|---|---|
| 기존 OPAL · 레지스트리가 현재 범위를 덮는다 | `docs/PROJECT.md` 레지스트리가 **등록한 현재 범위 관련 문서만** | `INTENT.md` (+ P2 `PROJECT-DESIGN.md`) |
| 기존 OPAL · 재사용할 제품 명세가 명시적으로 필요 | 위 + 외부 `PRD.md` | `INTENT.md`는 requirement ID만 선택 |
| greenfield | opi 산출 `PROJECT.md` | `PROJECT.md` · `INTENT.md` (+ P2 `PROJECT-DESIGN.md`) |

- `docs/` 전체를 읽지 않는다. 레지스트리에 없는 문서를 추측으로 로드하지 않는다.
- 환경·컨벤션·아키텍처를 새 TRD에 복사하지 않는다. 현재 상태는 ARCHITECTURE·CONVENTIONS·SECURITY 등
  기존 기술 SSOT가 계속 소유한다.
- 기존 문서를 읽기 전용으로 재사용한다 — 범위에 포함되지 않은 기존 PRD·TRD를 수정하지 않는다.
- **TRD 작성 조건**: greenfield의 기술 기준을 처음 세우거나, 기존 SSOT에 없는 중대한 기술 결정을 승인받을
  때만 `TRD.md` delta를 만든다. 이 경우 P2 사용자 게이트(행 10)가 열린다.
- **PRD 작성 조건**: 재사용할 제품 명세가 필요하다고 사용자가 확인했을 때만 `opwt`·`opal-planning-agent`
  경로를 호출한다. OPPB가 자체 PRD 포맷을 만들지 않는다.
- 결측 문서는 INTENT 인터뷰로 메운다. 문서 부재를 새 문서 생성의 근거로 삼지 않는다.

---

## 실행 계약 — `INTENT.md` 하나

> **[MUST]** 실행 계약 문서는 `INTENT.md` **하나로 확정한다** (수용기준 2). CONTRACT.md·SPEC.md·REQUIREMENTS.md
> 같은 병렬 실행 계약 문서를 추가로 만들지 않고, 미니 태스크별 계약 문서도 만들지 않는다.
> `workgraph.json`의 `execution_contract`는 항상 `INTENT.md`를 가리킨다.

```markdown
# INTENT: {프로젝트명}

> 작성일: YYYY-MM-DD | 스킬: //oppb

## 목표
{한 문단. 무엇을 끝내면 이 프로젝트가 끝나는가}

## 제외 범위
{이번에 하지 않는 것 — 슬라이서가 DAG에 넣지 않을 근거}

## 완료조건
- C-1 {관측 가능한 결과}
- C-2 {관측 가능한 결과}

## 비가역 제약
{실제 배포·외부 호출·데이터 마이그레이션 등 사용자 승인 없이 하지 않는 것}

## 예산
attempt {N}회, 프로세스 {M}개 (§9.3 동시성 예산 3종)

## 참조 문서 (레지스트리가 등록한 것만)
| 문서 | 용도 | 신규 생성 |
|---|---|---|
| docs/PRD.md | 요구 ID 선택 | 아니오 (기존 재사용) |
| docs/ARCHITECTURE.md | 기술 기준 | 아니오 (기존 재사용) |
```

완료조건은 P2의 `acceptance.json` 역인덱스와 P4 Acceptance Evaluator 판정의 유일한 입력이다.
INTENT가 잠긴 뒤의 목표·범위 변경은 §사용자 게이트 2번(기능 범위·외부 계약 변경)으로만 처리한다.

---

## 폴더 구조

```
tasks/{NNN}-oppb-{프로젝트명}/          (추적 — 프로젝트 태스크 캡슐 1개)
├── TASK.md · STATE.md · state.json
├── INTENT.md                          (P1 — 유일한 실행 계약)
├── PROJECT-DESIGN.md                  (P2 — 설계·슬라이스 근거·통합 전략)
└── DONE.md                            (P5 — evidence manifest 포함, Controller가 렌더)

.opal/oppb-environment.json            (추적 — P2 봉인된 실행 profile)

<allocator_root>/.opal-runs/<run_id>/   (미추적 — run root, worktree 회수와 함께 삭제하지 않는다)
├── workgraph.json · acceptance.json
├── attempts/<task_id>/<attempt_id>/{execution-packet.json, result.json}
├── evidence/<scope>/<evidence_id>.json
├── environment-deltas/<fingerprint>.json
├── events.jsonl
└── knowledge-receipt.json
```

`{NNN}`: 허브 allocator가 한 번 발급한다. `worktree-tool create`로 `.opal-worktrees/task_{NNN}` 프로젝트
worktree **하나**를 만든다.

> **[MUST] 프로젝트 worktree 1개, 미니 태스크 worktree·branch 0개** (수용기준 3). 미니 태스크에 OPAL 번호·
> 태스크 폴더·worktree·branch를 만들지 않는다. 미니 태스크는 같은 작업본에서 서로 겹치지 않는 lease로
> 작업하고, Git writer는 Checkpoint Tool 하나뿐이다.

### 미니 태스크 문서 규칙

| 구분 | 산출물 |
|---|---|
| 항상 생성 | `workgraph.json` task record · `execution-packet.json` · `result.json` · `evidence/<scope>/<id>.json` |
| 조건부 생성 | `DESIGN.md`(Standard에서 설계 선택 보존 필요 또는 Critical) · `TEST-SCENARIO.md`(계약·E2E·보안 시나리오가 독립 문서를 요구할 때) |
| **생성하지 않음** | 미니 태스크별 `TASK.md`·`DONE.md`·`ANALYSIS.md`·`PLAN.md`·`QA.md`·`CLOSE.md`, 미니 태스크별 MEMORY·brain 기록 |

> **[MUST]** Fast 미니 태스크의 **상시 산출물은 packet·result·evidence뿐이다** (수용기준 8). 사람이 검토할
> 필요가 있으면 Controller가 task record의 Markdown view를 임시 렌더링할 수 있으나 별도 SSOT로 저장하지 않는다.
> 프로젝트 단위 `DONE.md` 1건은 P5 산출물로 허용된다.

---

## STATE.md 초기 생성

```
~/.opal/tools/state-tool/run.sh init <task-path> --skill oppb --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-project-build/references/pipeline.json
```

> **행 구성 SSOT**: `references/pipeline.json` `task_steps[]` (P0~P5 22행). 현재 행 목록은
> `~/.opal/tools/state-tool/run.sh show <task-path>`로 조회한다.
>
> **게이트 정의 SSOT**: `references/pipeline.json` `task_steps[].gate` — 산출물·체크리스트는 이곳에만 정의한다.
> `mark --task-step <게이트 key>` 호출 시 도구가 artifacts 존재를 검증하고 checklist를 stdout으로 반환한다.

> **[MUST]** 파이프라인 행 상태 변경은 `state-tool`로만 수행한다. 미니 태스크마다 행을 동적 추가하지 않는다 —
> 미니 태스크 진행은 `workgraph.json`이 소유하고 `state.json`은 P0~P5만 추적한다(축 분리).

---

## P0. ENTRY & CONTEXT

| 항목 | 내용 |
|---|---|
| 실행 주체 | OPPB Product Flow · PM Agent |
| 보조 | `opi`, `docs/PROJECT.md` 문서 레지스트리 loader |
| 종료 조건 | 프로젝트 컨텍스트와 결측 정보가 식별됨 |

1. OPAL 프로젝트 여부·프로젝트 태스크 번호·단일 worktree·기존 문서·사용자 입력 충분성을 판정한다
   (`p0.context_probe`). 기존 OPAL 프로젝트에서는 §문서 라우팅의 레지스트리 경로만 읽는다.
2. 프로젝트 태스크 캡슐과 P0~P5 `state.json`을 만든다 (`p0.task_capsule`) — 위 `state-tool init` 호출.
3. `oppb-runtime-tool init --allocator-root <허브 최상위 절대경로> --project-root <프로젝트 절대경로>`로
   run root·cache root를 연다. 이 명령은 `.git/info/exclude` 등록과 실제 ignore 판정 확인에 실패하면
   run 시작을 거부한다. 거부는 우회하지 않고 blocker로 보고한다.

---

## P1. INTENT

| 항목 | 내용 |
|---|---|
| 실행 주체 | PM Agent |
| 조건부 주체 | 재사용할 제품 명세가 필요할 때만 `opwt`·`opal-planning-agent` |
| 사용자 역할 | 목표·제외 범위·완료조건·비가역 제약 승인 |
| 종료 조건 | 실행 목표·범위·완료조건·예산이 명확함 |

1. `p1.intent_draft` — §실행 계약 템플릿으로 `INTENT.md`를 작성한다. PRD가 있으면 requirement ID만 선택하고,
   없으면 사용자 입력을 직접 INTENT로 정규화한다.
2. `p1.conditional_prd` — §문서 라우팅 표로 PRD 필요 여부를 **명시 판정**하고 근거를 STATE.md 저널에 남긴다.
   기존 문서가 충분하면 여기서 끝난다. 부족할 때만 `opwt`·planning agent를 호출한다.
3. `p1.user_gate` — **사용자 게이트 ①**. INTENT 4요소 승인과 PRD 신규 생성 여부 확정.

---

## P2. PROJECT DESIGN & SLICE

| 항목 | 내용 |
|---|---|
| 초안 작성 | `opal-plan-agent` + `op-oppb-project-slice` 단계 스킬 주입 |
| 승인·판단 | PM Agent |
| 조건부 검토 | Critical 결정만 `opal-evaluator-agent`(design-review) |
| 기계 검증 | Controller Tool |
| 종료 조건 | DAG·계약·완료조건 역인덱스·probe로 봉인한 병렬 lease 범위가 유효함 |

1. `p2.project_design` — `PROJECT-DESIGN.md` 작성. 슬라이스 단위는 **동일한 비즈니스 개념·변경 이유·정책을
   공유하며 사용자가 끝까지 사용할 수 있는 하나의 응집된 capability**다. 파일 수·레이어 수·endpoint 수를
   1차 분할 기준으로 쓰지 않으며, 단독 가치가 없는 수평 레이어 분할(API와 그 전용 화면 분리 등)을 만들지 않는다.
2. `p2.workgraph` — `workgraph.json`·`acceptance.json` 생성과 Controller 기계 검증. 각 미니 태스크는 capability ID
   하나·응집된 acceptance cluster·독립 end-to-end 검증을 가진다. 병렬 sibling은 tracked/ephemeral write·contract·
   business rule·acceptance·runtime resource·global output 교집합이 0일 때만 허용하고, 증명할 수 없으면 합치거나
   `parallel_eligible: false`로 순차 실행한다.
3. `p2.critical_review` — Critical 기술 결정이 있을 때만 Design Evaluator를 1회 호출한다.
4. `p2.environment_seal` — Environment Probe를 실행해 `.opal/oppb-environment.json`에 미추적 쓰기 경로·cache
   adapter·runtime resource·입력 hash를 봉인한다. greenfield는 최소 환경 bootstrap capability 하나를 exclusive로
   먼저 accepted한 뒤 probe·봉인하고 나머지 병렬 dispatch를 연다.
5. `p2.user_gate` — **사용자 게이트 ②** (조건부, 중대한 신규 기술 결정·TRD delta가 있을 때만).

---

## P3. CONTINUOUS MINI-TASK EXECUTION

| 항목 | 내용 |
|---|---|
| 스케줄 결정 | Controller Tool |
| 프로세스 실행·회수 | Runtime Supervisor → `opal-agent` headless attempt |
| 코드 작업 | `opal-capability-agent` · 조건부 기존 전문 Executor |
| 확정 | Checkpoint Tool · 조건부 Verifier |
| 종료 조건 | 모든 필수 미니 태스크 accepted 또는 구조화 blocked |

1. `p3.supervisor_start` — `oppb-runtime-tool start --run-root <run_root>`를 **한 번** 호출한다. Supervisor가
   run lock을 잡고 tick loop를 돌며, 대화 세션과 독립적으로 동작한다.
2. `p3.continuous_execution` — 고정 Wave를 쓰지 않는다. 의존성이 풀리고 세 lease 집합이 겹치지 않는 태스크를
   즉시 실행한다. 미니 태스크는 `RUN → PROVE → ACCEPT` 세 단계만 갖는다.

| 미니 단계 | 수행 | 주체 |
|---|---|---|
| M1 RUN | capability micro design → 내부 work item 조율 → 구현 → formatter·lint | `opal-capability-agent` |
| M2 PROVE | 영향 테스트·기존 보안 회귀 | `opal-capability-agent` |
| M3 ACCEPT | 범위·변경 파일 컨벤션·조건부 수용/계약/보안 판정 후 candidate 확정 | Checkpoint Tool·조건부 Verifier |

| Profile | RUN | PROVE | ACCEPT | 추가 에이전트 |
|---|---|---|---|---|
| Fast | 바로 구현 | 직접 테스트 | scope·기본 checkpoint 검증 | 없음이 기본 |
| Standard | capability micro design | 수직 수용·영향 테스트 | 외부 계약·컨벤션 | 필요 시 FE·BE·DB Executor |
| Critical | 보존할 설계 작성 | 심층 시나리오 | 독립 계약·보안·컨벤션 | Design Evaluator·Security Verifier |

> **[MUST]** PM은 capability owner나 Verifier를 대화형 Agent 도구로 직접 디스패치·회수하지 않는다. P3 이후
> 모든 실행은 Supervisor의 `opal-agent` headless attempt 채널이다. Supervisor start 뒤 사용자 게이트까지
> PM tick·수동 재촉·강제 resume은 0이어야 한다(수용기준 10).

**Repair**: 실패한 미니 태스크는 같은 대화를 resume하지 않는다. 동일 task ID·남은 예산·압축 execution packet을
받은 **새 attempt**로 수행한다. Repair·일반 미니 태스크 완료·상태 확인에는 사용자를 호출하지 않는다.

**needs_revalidation**: 외부 계약 revision이 바뀌면 그 계약의 직접 consumer만 재검증한다. 무관하거나 아직
실행 전인 태스크는 재검증하지 않는다.

**blocked**: Controller가 구조화 blocked를 반환하면 PM은 자율 재시도를 중단하고 사유를 §에스컬레이션 기준으로
판정한다. `scope_violation`·`disk_budget_exceeded` 같은 거부 코드는 재해석·조건부 무시 없이 그대로 사유가 된다.

3. `p3.pm_gate` — PM Gate. 모든 필수 미니 태스크 accepted 또는 구조화 blocked.

---

## P4. PROJECT VERIFY

| 항목 | 내용 |
|---|---|
| 실행 주체 | Integration · Security · Convention Verifier |
| 완료 판정 | Acceptance Evaluator (`opal-evaluator-agent` phase: acceptance) |
| PM 역할 | 귀속 불명 실패·계약 변경만 판단 |
| 종료 조건 | 전체 회귀·통합 보안·컨벤션·완료조건 통과 |

1. `p4.project_checkpoint` — 모든 write lease를 닫고 최종 project checkpoint를 만든다.
2. `p4.three_verifiers` — 세 Verifier를 실행한다. Verifier는 read-only이며 직접 수정하지 않고, 실패를 귀속 가능한
   Repair 또는 PM decision으로 반환한다.
3. `p4.acceptance` — INTENT 완료조건 ↔ evidence 대응을 판정한다.
4. `p4.pm_gate` — PM Gate. 차단 지표 All Pass, 신규 차단 결함 0, 귀속 불명 실패 0.

---

## P5. MERGE · KNOWLEDGE · CLOSE

| 항목 | 내용 |
|---|---|
| 사용자 | 승인된 project head의 허브 merge 승인·확인 |
| merge 확인 | Runtime Supervisor · Git 조상 관계 검사 |
| 지식 반영 | Project Knowledge Finalizer (`op-oppb-knowledge-finalize`) |
| 최종 보고 | PM Agent · OPPB Product Flow |
| 종료 조건 | 허브 merge · MEMORY·brain batch · registry close · worktree 회수 완료 |

1. `p5.pre_finalize_guard` — active lease 0, 미처리 result 0, checkpoint 밖 dirty source 0, MEMORY·brain diff 0을
   확인한다. 하나라도 실패하면 merge로 진행하지 않는다.
2. `p5.user_merge_gate` — **사용자 게이트 ⑥**. 최종 project head 허브 merge 승인.
3. `p5.knowledge_batch` — **MEMORY·brain 반영은 여기서 정확히 1회다.**
4. `p5.done_md` — 프로젝트 `DONE.md`·evidence manifest를 acceptance 결과에서 결정론적으로 렌더한다. PM은 DONE을
   직접 쓰지 않고 최종 사용자 보고만 작성한다.
5. `p5.worktree_finalize` — `worktree-tool finalize`·귀속 확정·worktree 회수. 미추적 run root는 함께 삭제하지 않으며
   DONE의 manifest가 경로·content hash를 가리킨다.

> **[MUST] 지식 반영 1회 계약**: MEMORY·brain은 P5 이전까지 **읽기 전용**이다(수용기준 11). 미니 태스크마다
> `op-brain-ingest`·`opal-improve` hook을 호출하지 않는다. 실패·폐기된 미니 태스크 후보를 제거한 뒤, 최종 허브
> merge **이후** 프로젝트 단위로 정확히 한 번 반영한다(수용기준 12). 반영 결과는 `knowledge-receipt.json`으로 남는다.

---

## 디스패치

PM은 미니 태스크를 직접 디스패치하지 않는다. P0~P2의 bounded planning만 대화형 Agent 도구로 호출하고,
P3 이후는 Supervisor가 `opal-agent` headless attempt로 실행한다.

| 시점 | 호출 주체 | 대상 에이전트 | 주입 스킬 |
|---|---|---|---|
| P1 조건부 PRD | Product Flow (대화형) | `opal-planning-agent` | `opwt` 경로 |
| P2 슬라이스 초안 | Product Flow (대화형) | `opal-plan-agent` | `op-oppb-project-slice` |
| P2 Critical 검토 | Product Flow (대화형) | `opal-evaluator-agent` | phase: design-review |
| P3 미니 태스크 | Supervisor (headless) | **`opal-capability-agent`** | — |
| P3 내부 work item | `opal-capability-agent` | `opal-fe-agent`·`opal-be-agent`·`opal-db-agent`·`opal-task-agent` | 선택 단계 스킬 |
| P3·P4 Verifier | Supervisor (headless) | `opal-test-agent`·`opal-security-checker`·`opal-convention-checker` | `op-gc-security`·`op-gc-convention` |
| P4 완료 판정 | Supervisor (headless) | `opal-evaluator-agent` | phase: acceptance |
| P5 지식 반영 | Product Flow | `opal-task-agent` | `op-oppb-knowledge-finalize` |

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 주입 항목·핵심 제약은
> `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿을 따른다 — 본 스킬은 항목을 열거하지 않는다.

**금지 호출**:
- `opal-task-action-agent` 직접 호출 0 — OPPD 전용이며 OPPB는 확장하지도 호출하지도 않는다.
- `opal-loop-action-agent`·`opal-sdd-action-agent` 호출 0 — 각각 OPPL·SDD 소유다.
- 실행 방식 선택 옵션·라우터 0 — 미니 태스크 실행 경로는 `opal-capability-agent` 하나뿐이다.
- capability owner가 하위 PL·범용 오케스트레이터를 생성하는 것 0 — 전문 Executor는 같은 task ID와 승인된
  work item lease 안에서만 작업하고 독립 상태·checkpoint·완료조건을 갖지 않는다.

---

## 사용자 게이트

사용자를 부르는 시점은 아래 6개뿐이다. `pipeline.json`의 `gate` 배치가 이 표의 기계 표현이다.

| # | 시점 | 파이프라인 행 |
|---|---|---|
| ① | INTENT 승인 | 5 `p1.user_gate` |
| ② | 중대한 신규 기술 결정 승인 (조건부) | 10 `p2.user_gate` |
| ③ | 기능 범위·외부 계약 변경 | 13 `p3.pm_gate` (변경 발생 시) |
| ④ | 비가역 작업·실제 배포 / 예산 초과 | 17 `p4.pm_gate` |
| ⑤ | 귀속되지 않은 외부 workspace 변경 | 19 `p5.user_merge_gate` 직전 guard |
| ⑥ | 최종 project head 허브 merge와 CLOSE | 19 `p5.user_merge_gate` · 21 `p5.done_md` |

일반 미니 태스크 완료·Repair·상태 확인에는 사용자를 호출하지 않는다.

> OPPB v1은 §9.3 동시성 예산 3종(`max_active_runners`·`max_active_executors`·`max_total_agent_processes`)만
> 집행한다. 비용·벽시계 예산과 무진전 판정은 후속 태스크가 소유한다.

---

## Agentic / Semi-Agentic 모드

`opal-harness-agentic.md` / `opal-harness-semi-agentic.md` 참조. 본 절은 이 스킬의 차이점만 기술한다.

- 기본 호출(`//oppb {요청}`)은 semi-agentic. **P2 사용자 게이트까지 사용자 검토**, P3 Supervisor 기동 이후 PM 자율,
  CLOSE 진입은 사용자 승인 필수.
- P3은 설계상 무인 구간이다. agentic·semi-agentic 어느 모드에서도 Supervisor tick을 사람이 재촉하지 않는다.
- CLOSE 진입 게이트(공통): `p5.user_merge_gate`는 `--auto-pass`를 거부한다. 소유자 발화 후에만 `--owner user`로 mark한다.
- AGENTIC-LOG.md 생성 시점 — agentic: P0 시작 시점 / semi-agentic: P3 첫 행 advance 시점.

**oppb 고유 에스컬레이션 조건** (공통 기준에 추가):
- Controller가 `scope_violation`·`disk_budget_exceeded`·`split_required`를 반환한 경우
- 귀속되지 않은 외부 workspace 변경이나 Runner의 Git 상태 변경이 관측된 경우
- pre-finalize guard 4항목 중 하나라도 실패한 경우

---

## DONE.md / CLOSE

```markdown
# DONE: {프로젝트명} 프로젝트 빌드

> 완료일: YYYY-MM-DD | 스킬: //oppb

## 완료조건 판정
| ID | 완료조건 | 결과 | evidence |
|---|---|---|---|
| C-1 | {INTENT 완료조건} | PASS | evidence/<scope>/<id>.json (sha256) |

## 미니 태스크
| task_id | capability | profile | 결과 | attempt |
|---|---|---|---|---|

## evidence manifest
| 경로 | content hash | 생성 시각 |
|---|---|---|

## 남은 위험
{미해결 위험·후속 태스크 후보}
```

1. `DONE.md`는 Controller가 acceptance 결과에서 렌더한다 — PM이 손으로 쓰지 않는다.
2. 관련 문서 업데이트: `docs/PROJECT.md` 레지스트리와 이번 프로젝트의 changed files를 종합해 관련 기술 문서를
   최신화한다. 대상 없으면 no-op. **여기서도 PRD·TRD를 새로 만들지 않는다.**
3. 지식 반영은 `p5.knowledge_batch` 1회로 끝났다 — CLOSE에서 `op-brain-ingest`를 별도 디스패치하지 않는다.
4. 완료 보고:

```
✅ [CLOSE] oppb 프로젝트 완료
📎 산출물: tasks/{NNN}-oppb-{프로젝트명}/DONE.md
미니 태스크 {M}개 accepted · 완료조건 {K}건 PASS · 지식 batch 1회.
```

---

## 스킬 탐색 경로

**opi (사전 조건 미충족 시)**:
1. `{프로젝트}/.opal/skills/opal-project-init/SKILL.md`
2. `~/.opal/skills/opal-project-init/SKILL.md`

**opal-capability-agent (P3 미니 태스크 owner)**:
1. `{프로젝트}/.opal/agents/opal-capability-agent/AGENT.md`
2. `~/.opal/agents/opal-capability-agent/AGENT.md`

**opal-plan-agent + op-oppb-project-slice (P2 슬라이스 초안)**:
1. `{프로젝트}/.opal/agents/opal-plan-agent/AGENT.md`, `{프로젝트}/.opal/skills/op-oppb-project-slice/SKILL.md`
2. `~/.opal/agents/opal-plan-agent/AGENT.md`, `~/.opal/skills/op-oppb-project-slice/SKILL.md`

**opal-evaluator-agent (P2 design-review · P4 acceptance)**:
1. `{프로젝트}/.opal/agents/opal-evaluator-agent/AGENT.md`
2. `~/.opal/agents/opal-evaluator-agent/AGENT.md`

**Verifier (opal-test-agent · opal-security-checker · opal-convention-checker)**:
1. `{프로젝트}/.opal/agents/{opal-test-agent|opal-security-checker|opal-convention-checker}/AGENT.md`
2. `~/.opal/agents/{opal-test-agent|opal-security-checker|opal-convention-checker}/AGENT.md`

**op-oppb-knowledge-finalize (P5 지식 반영)**:
1. `{프로젝트}/.opal/skills/op-oppb-knowledge-finalize/SKILL.md`
2. `~/.opal/skills/op-oppb-knowledge-finalize/SKILL.md`

---

## 프로젝트 메모리 동기화

`{프로젝트}/.opal/MEMORY.json`이 존재하면 **P5에서만** 갱신한다 — P0~P4에서 MEMORY는 읽기 전용이다.

```
~/.opal/tools/memory-tool/run.sh append --file .opal/MEMORY.json --kind history \
  --title "<프로젝트명>" --stage "완료" --path "tasks/<폴더>/" --summary "<핵심결과>"
```

- [MUST] 표·파일 직접 편집 금지 — 도구 호출만 사용한다. 상세: `opal/core/references/harness/observability.md`
  §프로젝트 메모리 동기화.
- 미니 태스크 단위 history append를 하지 않는다 — 수용기준 11·12를 깨는 경로다.
