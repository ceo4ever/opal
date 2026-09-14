---
name: opal-pilot-project-loop
description: |
  **루프 기반 프로젝트 오케스트레이터**. 요청 분석→계획→목표 충족까지 반복(2-루프 수렴: 설계 수렴 루프 → 실행 수렴 루프)하여
  규모 있는 프로젝트를 완주시킨다. 선형 Phase가 아니라 종료조건(반복상한·예산·무진전·목표체크·사람게이트)이 있는 수렴 루프로
  구동하며, 검증을 Evaluator(구현 전 명세 심판)와 test-agent(구현 후 동작 검증)로 2원화한다. 3-SSOT
  tool-gated(backlog.json/state.json/test-scenario.json)로 백로그·진행상태·테스트결과 축을 분리한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-project-loop", "oppl", "루프 오케스트레이터", "수렴 루프", "프로젝트 루프".
  목표·계약·백로그를 한 번에 잠글 수 없고 실행 증거에 따라 반복 재구성해야 하는 수렴형 프로젝트에 사용한다.
  확정된 계약의 실행 효율화가 주목적인 프로젝트 Pilot과는 독립된 선택지이며 대체·후계 관계가 아니다.
triggers:
  - "^opal-pilot-project-loop$"
  - "^oppl$"
  - "(?i)(루프\\s*오케스트레이터|수렴\\s*루프|프로젝트\\s*루프)"
version: 1.0.0
---

# opal-pilot-project-loop (oppl)

규모 있는 프로젝트를 **종료조건이 있는 2-루프 수렴 구조**로 완주시킨다 — Loop 1(설계 수렴: 인터뷰~CONTRACT~백로그, 4요소 잠김까지 반복)과
Loop 2(실행 수렴: 태스크 선택~완료, 전 수용기준 GREEN까지 반복)가 순서대로 구동되며, 각 루프 내부는 매 회전(round)마다
목표 달성 여부를 도구 결과로 판정한다. 검증은 **Evaluator(명세 심판, 구현 전)** 와 **test-agent(동작 검증, 구현 후)** 로 2원화하고,
백로그·진행상태·테스트결과는 각각 전용 도구가 관리하는 JSON(3-SSOT)으로 축을 분리한다.

## 사용 기준

다음 질문에 `아니요`일 때 OPPL을 선택한다.

> 한 번의 설계 승인 후 목표·계약·백로그를 잠그고, 이후 변경을 예외로 처리할 수 있는가?

- `아니요`: 실행 증거가 목표·계약·백로그를 바꾸는 것이 정상 흐름이므로 OPPL을 사용한다.
- `예`: 고정된 실행 계약을 처리하는 프로젝트 Pilot을 사용한다.
- 단순 정보 결측, 파일 수, 프로젝트 규모, 높은 기술 난이도만으로 OPPL을 선택하지 않는다.
- 안정성 목표·실험형 품질 개선·탐색형 제품처럼 실패 증거가 다음 설계와 작업 순서를 결정하면
  OPPL 대상이다.

## Harness

모드: Project Loop (설계 루프 → 실행 루프)
**[MUST — pilot.start 이벤트 게이트]** 파일럿의 첫 작업 전에 아래 순서를 수행한다.

1. `~/.opal/tools/event-loader/run.sh load --event pilot.start > <pilot-receipt-path>`를 호출한다.
2. load 응답의 `documents[].content` 전문을 모두 현재 컨텍스트에 적용하고, `modes` 문서가 현재 플래그에 대해 라우팅한 서브 하네스 전문 하나만 Read한다.
3. `~/.opal/tools/state-tool/run.sh event-verify --event pilot.start --receipt <pilot-receipt-path>`가 성공한 뒤에만 진행한다.

**[MUST — 단계 이벤트 게이트]** 각 실제 단계의 첫 작업이나 `state-tool advance` 직전에 아래 매핑의 이벤트를 load하고, 응답 문서 전문을 적용한 뒤 같은 event id로 `state-tool event-verify`를 통과해야 한다.

| 실제 단계 | 이벤트 |
|---|---|
| 사전 조건·초기 TASK | stage.task |
| Loop 1 수집·분석 | stage.analysis |
| Loop 1 설계 확정 | stage.plan |
| Loop 2 실행 | stage.execute |
| Loop 2 검증 | stage.test |
| CLOSE | stage.close |

호출 형식은 `~/.opal/tools/event-loader/run.sh load --event <stage.*> > <stage-receipt-path>` 다음
`~/.opal/tools/state-tool/run.sh event-verify --event <stage.*> --receipt <stage-receipt-path>`이다.
문서 집합은 `events.json`만 SSOT로 사용하며 SKILL에 파일 목록을 복제하지 않는다. load 실패,
필수 문서 누락, stale receipt, wrong-event receipt는 해당 파일럿·단계 진입을 즉시 중단하는
blocker다. 부트 캐시를 근거로 공통 문서를 직접 재Read하는 우회는 금지한다.

---

## 계층 · 핵심 개념

**계층**: 프로젝트 > 태스크(얇은 수직 슬라이스) > 단계(T1~T5+G). 프로젝트는 Loop 1이 확정한 4요소(PRD/TRD/CONTRACT/BACKLOG)로
정의되고, 태스크는 그 백로그의 각 행 하나이며, 단계는 태스크 내부 파이프라인의 각 스텝이다.

**3-SSOT tool-gated**: oppl은 3개의 JSON을 각각 전용 CLI로만 갱신되게 만들어 절차 우회를 차단한다. 세 SSOT는 서로 참조하지 않는다(축 분리).

| SSOT | 도구 | 관리 대상 | 사람 뷰(자동 렌더 미러) |
|------|------|---------|----------------------|
| `backlog.json` | `backlog-tool` | 태스크 목록·상태·의존·우선순위 | `BACKLOG.md` |
| `state.json` | `state-tool` | 파이프라인 행(`rows[]`) 진행 상태 | `state-tool show`(조회) |
| `test-scenario.json` | `test-tool` (`scenario-*`) | 태스크별 테스트 시나리오 spec/result | (없음 — `scenario-status`로 조회) |

> STATE.md는 **의사결정 로그·블로커·자유 기재를 담는 저널**이다. 파이프라인 현황(행 상태·진행·다음 액션)의 SSOT는 `state.json`이며, 조회는 `state-tool show`로 한다.

> **[MUST] 파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다.** `BACKLOG.md`는 `backlog-tool`이 항상 렌더하는 자동 미러이며 PM은 손편집하지 않는다.

---

## 사전 조건 체크

`//oppl` 호출 시 프로젝트 루트의 `docs/PROJECT.md` 존재 여부를 확인한다.

| 조건 | 동작 |
|------|------|
| `docs/PROJECT.md` 존재 | Loop 1 D1 시작 |
| `docs/PROJECT.md` 미존재 | opi 자동 실행 → 완료 후 oppl 복귀 |

**opi 자동 실행 시**:
1. 사용자의 원래 요청을 보존한다
2. `~/.opal/skills/opal-project-init/SKILL.md`를 Read하여 opi를 실행한다
3. opi 완료 즉시, 보존한 원래 요청으로 oppl Loop 1을 시작한다

---

## 폴더 구조

```
tasks/{NNN}-oppl-{프로젝트명}/
├── TASK.md · STATE.md
├── BACKLOG.md            (backlog-tool 렌더 미러 — 손편집 금지)
├── backlog.json          (backlog-tool SSOT)
├── PRD.md · TRD.md · CONTRACT.md · USER_JOURNEY.md*   (설계 루프 산출 → D7 확정 후 docs/ 승격)
├── DONE.md
└── tasks/
    └── T{NN}-{태스크명}/  { PLAN.md, USER_FLOW.md*, test-scenario.json, QA-SPEC.md, DONE.md, (VERIFICATION.md) }
```

`*` 표시 산출물(USER_JOURNEY.md/USER_FLOW.md)은 조건부 — user-facing 프로젝트만 생성한다 (`references/journey-flow.md` §2).

> **[MUST]** 용어 구분: `BACKLOG.md`는 **프로젝트 백로그 미러**(backlog-tool 렌더)이고, 태스크 폴더 `PLAN.md`는 **해당 태스크의 미시 설계**다. 둘을 혼용하지 않는다.

`{NNN}`: 기존 `tasks/` 폴더의 최대 번호 + 1로 자동 채번.

### TASK.md 작성

```markdown
# TASK: {프로젝트명} 루프 개발

> 작성일: YYYY-MM-DD | 스킬: //oppl

## 목표

{사용자의 원래 요청}

## 참조 문서

| 문서 | 용도 | 읽는 시점 |
|------|------|----------|
| docs/PROJECT.md | 프로젝트 정의, 원칙 | 전체 |
| docs/ARCHITECTURE.md | 기술 스택 | Loop 1 |
| docs/CONVENTIONS.md | 코드 컨벤션 | Loop 2 |
| .opal/AGENT.md | PM 검토 기준 | 전체 |

## 루프

| Loop | 산출물 | 종료조건 |
|------|--------|---------|
| 1 — 설계 수렴 | PRD.md, TRD.md, CONTRACT.md, BACKLOG.md | 4요소 잠김 + Evaluator D6 미해결 0 |
| 2 — 실행 수렴 | tasks/T{NN}/ 완주 결과 | `backlog-tool done-check` all_done + 회귀 0 |
```

---

## STATE.md 초기 생성

state-tool을 호출하여 초기화한다:

```
~/.opal/tools/state-tool/run.sh init <task-path> --skill oppl --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-project-loop/references/pipeline.json
```

> state-tool의 `--skill` choices·schema enum에 `oppl`이 등록되어 있다(F-003). `state-tool`이 `references/pipeline.json`을 읽어 state.json을 초기화한다.

**[R-10 비표준 행 구성]** oppl은 Loop 기반 비표준 행 구조를 사용한다 — Loop 1(D1~D7)은 고정 행, Loop 2(태스크 파이프라인)는 `[R-13]` 동적 `add-row`로 태스크 행을 삽입한다. `gate-pass`는 deprecated — PM Gate/사용자 확인은 `mark` 개별 호출로 처리한다.

> **행 구성 SSOT**: `references/pipeline.json` `task_steps[]`. 현재 행 목록은
> `~/.opal/tools/state-tool/run.sh show <task-path>` 또는 pipeline.json을 직접 조회한다.
>
> **게이트 정의 SSOT**: `references/pipeline.json` `task_steps[].gate` — 산출물·체크리스트는 이곳에만 정의한다. `mark --task-step <게이트 key>` 호출 시 도구가 artifacts 존재를 검증하고 checklist를 stdout으로 반환한다.

> **[R-13] 태스크 동적 행**: Loop 2 진입(`execute.l0_select` advance) 후, backlog-tool `select-next`가 태스크를 반환할 때마다 `add-row`로 해당 태스크 행을 삽입한다:
> ```
> ~/.opal/tools/state-tool/run.sh add-row <task-path> --after 13 --stage EXECUTE --item 'T{NN}: {태스크 제목} (T1~T5+G)'
> ```
> 태스크 완료 시 해당 행을 `mark --done`한다. 태스크 상세 상태(수용기준·시나리오 결과)는 `backlog.json`/`test-scenario.json`에서 관리하며 STATE.md 행은 완료 여부만 추적한다(3-SSOT 축 분리 원칙).

---

## Loop 1 — 설계 수렴 루프

**목적**: 명확화 4요소(PRD/TRD/CONTRACT/BACKLOG)를 확정한다. **종료조건**: 4요소 잠김 + Evaluator D6 미해결 이슈 0 (미충족 시 D1~D6를 재회전).

```
D1 인터뷰 (사용자 명확화 4요소)
  ↓
D1.5 여정 매핑* — 조건부, user-facing 프로젝트만 (references/journey-flow.md §2)
  ↓
D2 PRD 작성 [워커 디스패치]
  ↓
D3 TRD 작성 [워커 디스패치]
  ↓
D4 CONTRACT 작성 [워커 디스패치] — 스키마·시그니처·경계 + 기계검증절 + 루브릭절 (references/contract.md §2)
  ↓
D5 백로그 생성 — backlog-tool init + add-task (얇은 수직 슬라이스로 분해)
  ↓
D6 Evaluator 설계 검토 [워커 디스패치, phase: design-review]
  ↓ (미해결 있음) ─── D2~D5 재작업 회전 (반복상한 — loop-control.md §2)
  ↓ (미해결 0)
D7 사용자 확정 게이트 — 4요소 잠김 확인 → docs/ 승격
```

**D1 인터뷰**: TASK.md와 동일한 명확화 4요소(목표/범위/제약/완료기준)를 도출한다. 프로젝트 유형(user-facing 여부)을 이 단계에서 판단해 D1.5 트리거 여부를 결정한다(`references/journey-flow.md` §2).

**D1.5 여정 매핑 (조건부)**: user-facing 프로젝트만 `USER_JOURNEY.md`(거시: 단계·행동·시스템 반응)를 작성한다. Planner가 작성하며, Mermaid `flowchart`/`sequenceDiagram`로 시각화한다. 인프라/라이브러리/CLI 내부 프로젝트는 스킵하고 STATE.md/PLAN.md에 스킵 근거를 1줄 기록한다.

**D2 PRD / D3 TRD 작성 [워커 디스패치]**: opal-planning-agent(또는 opal-plan-agent)를 디스패치한다.

```
[WORKER] {PRD|TRD} 작성 — 태스크 폴더: tasks/{NNN}-oppl-{프로젝트명}/
- 이전 산출물: {D1 인터뷰 결과, USER_JOURNEY.md(있으면)}
- 프로젝트 컨텍스트: docs/PROJECT.md, docs/ARCHITECTURE.md
- 출력: tasks/{NNN}-oppl-{프로젝트명}/{PRD.md|TRD.md} (작업본)
- 하네스 Guards: 구현 금지. 지정 산출물 외 파일 생성 금지.
```

**D4 CONTRACT 작성 [워커 디스패치]**: TRD 확정 후, 동일 Planner에게 CONTRACT.md를 디스패치한다 — 구조는 `references/contract.md` §2(스키마·시그니처·경계 + 기계검증절 + 루브릭절)를 따른다. [MUST] 디스패치 프롬프트는 `surfaces.json` 생성(표면 전수 나열·각 표면 `auth` 필드 선언·인증 표면 자체도 등재)과, 웹 클라이언트가 존재하는 프로젝트의 경우 `origins` 선언을 요구한다 — 구조 스펙은 `references/contract.md` §2.2.1로 위임한다.

**D5 백로그 생성**: PM이 PRD/TRD/CONTRACT을 얇은 수직 슬라이스로 분해하여 backlog-tool로 등록한다 (USER_JOURNEY.md가 있으면 "여정 단계 → 슬라이스" 매핑을 분해 기준으로 사용).

[MUST] D5 백로그의 의존 루트(P0) 태스크로 "실행 스켈레톤" 슬라이스를 의무화한다 — 구성: (a) BE 서버 기동+스웨거(OpenAPI) UI 노출(surfaces.json 연동), (b) FE dev 서버 기동, (c) `test-tool` E2E contract의 해당 profile에서 FE→BE 실 호출 1개 관통, (d) auth 표면 존재 시 로그인 관통. 이후 전 태스크의 real-http/real-usage 검증이 이 환경 위에서 실행된다(목 개발의 "실 BE 부재" 사유 원천 제거).

```
~/.opal/tools/backlog-tool/run.sh init <task-path> --project-title "{프로젝트명}" --mode <m> --goal "{목표 요약}"
~/.opal/tools/backlog-tool/run.sh add-task <task-path> --id T01 --title "{제목}" --slice "{슬라이스 설명}" --acceptance '["AC1","AC2"]' --area <fe|be|db|공통|통합> --priority <P0|P1|P2> [--depends <T00>] [--parallel-group <g>] [--covers '["<surface-id>", ...]']
```

`--covers`에는 해당 태스크가 커버하는 `surfaces.json`의 표면 id 배열을 지정한다 — 실행 스켈레톤·표면별 구현 태스크 모두 대응 표면 id를 `--covers`로 선언해야 D7 이전 `coverage-check`가 통과한다.

**D6 Evaluator 설계 검토 [워커 디스패치]**: opal-evaluator-agent를 `phase: design-review`로 디스패치한다.

```
[WORKER]
task_folder: tasks/{NNN}-oppl-{프로젝트명}/
phase: design-review
target_artifacts: [PRD.md, TRD.md, CONTRACT.md, BACKLOG.md]
contract_path: tasks/{NNN}-oppl-{프로젝트명}/CONTRACT.md
timestamp: {ISO8601}
project_root: {프로젝트 루트}
```

verdict가 `fail`이거나 미해결 이슈가 있으면 D2~D5로 재회전한다(재회전 상한은 `references/loop-control.md` §2). verdict `pass` + 미해결 0이면 D7로 진행한다.

**D7 사용자 확정 게이트**: 4요소(PRD/TRD/CONTRACT/BACKLOG)가 잠겼음을 사용자에게 보고하고 승인을 받는다. 승인 시 PRD/TRD/CONTRACT을 `docs/`에 승격(oppd 1-3 승격 판단 로직 준용 — greenfield/반복 델타 병합)하고 Loop 2로 진입한다. 이 게이트는 loop-control.md §9 "사람 게이트" 대상이다(TRD/PRD 확정 = 비가역 행동).

[MUST] D7 진입 전 PM은 `~/.opal/tools/backlog-tool/run.sh coverage-check <task-path> --surfaces <surfaces.json>`을 호출한다. `surface_uncovered`(미커버 표면 존재) 또는 `integration_task_missing`(병렬 그룹 존재+통합 태스크 부재) 거부 시 D7에 진입하지 않고 D5로 되돌려 백로그를 재작업한다.

Gate 시 state-tool 호출:
```
~/.opal/tools/state-tool/run.sh mark <task-path> --task-step review.pm_gate --done  # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --task-step review.d7_user_gate --done --owner user --note '{owner_name} 확인: Loop 1 확정'
```

---

## Loop 2 — 실행 수렴 루프

**목적**: 백로그의 모든 태스크를 완주시킨다. **종료조건**: `backlog-tool done-check` → `all_done:true` (전 태스크 수용기준 GREEN) + 회귀 0.

```
L0 태스크 선택 — backlog-tool select-next
  ↓ (next_task_id: null → done-check로 직행)
  ↓ (next_task_id 있음)
add-row로 STATE.md에 T{NN} 행 삽입 → mark --status in_progress
  ↓
태스크 내부 파이프라인 (T1~T5+G — 아래 "태스크 내부 파이프라인" 절)
  ↓
L∞ 관찰 — backlog-tool mark(완료/blocked) + (범위 확장 발견 시) add-task
  ↓
L0로 복귀 (다음 태스크 선택)
  ↓ (모든 태스크 done)
L✓ 종료 판정 — backlog-tool done-check
  ↓ (all_done:false) → 잔여 태스크 있음 → L0 재진입
  ↓ (all_done:true + 회귀 0) → Loop 2 종료 → DONE.md / CLOSE
```

**L0 태스크 선택**:
```
~/.opal/tools/backlog-tool/run.sh select-next <task-path>
```
`depends[]` 충족 + `priority` 최상위 pending 태스크를 반환한다. `next_task_id: null`이면 L✓로 직행한다.

**L∞ 관찰**: 태스크 완주 후 결과에 따라 상태를 반영한다.
```
~/.opal/tools/backlog-tool/run.sh mark <task-path> --id T{NN} --status done
```
파이프라인 도중 범위 확장(신규 슬라이스 필요)이 발견되면 `add-task`로 백로그에 새 태스크를 추가한다 — WBS를 정적으로 재작성하지 않고 백로그를 살아있는 문서로 유지한다.

**L✓ 종료 판정**:
```
~/.opal/tools/backlog-tool/run.sh done-check <task-path>
~/.opal/tools/test-tool/run.sh scenario-conformance --task-path <task-path> --surfaces <surfaces.json>
```
[MUST] Loop 2 종료는 3중 불리언 AND로 판정한다 — `done-check.all_done`(태스크 축) ∧ `scenario-conformance.all_surfaces_green`(표면 축) ∧ 회귀 0. 세 조건 중 하나라도 미충족이면 종료하지 않는다: `all_done:false`이면 `remaining[]`을 L0에 다시 투입하고, `all_surfaces_green:false`(`surface_unverified`)이면 해당 표면을 커버하는 태스크를 L0에 재투입한다. user-facing 프로젝트는 여기에 여정 스모크 1회(`references/journey-flow.md` §6)를 더한다. 이 판정은 무진전 감지(`references/loop-control.md` §4 "백로그 정체" 신호)의 관찰 대상이기도 하다.

Gate 시 state-tool 호출:
```
~/.opal/tools/state-tool/run.sh mark <task-path> --task-step verify.pm_gate --done  # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --task-step verify.user_confirm --done --owner user --note '{owner_name} 확인: Loop 2 완료'
```

---

## 태스크 내부 파이프라인

백로그의 태스크 하나가 거치는 파이프라인. **검증 2원화**(Evaluator 구현 전 / test-agent 구현 후)가 이 안에서 발생한다 — 상세는 "검증 2원화" 절과 `references/verification.md` 참조.

> [MUST] PM은 L0 태스크 선택 후 **태스크당 `opal-loop-action-agent`를 1회 디스패치**하며, T1~T5+G 전체를 루프 액션 에이전트가 내부 디스패치로 완주한다. PM의 L0/L∞/done-check/사람 게이트 소유는 불변이다.

```
T1 명세·설계 — PLAN.md (+ USER_FLOW.md*, 인터랙션 슬라이스만) [opal-agent 채널 — 동기/비동기]
  ↓
T2 테스트시나리오 — test-tool scenario-init, RED-first [opal-agent 채널 — 동기/비동기]
  ↓
G 명세 리뷰 게이트 — Evaluator, 구현 전 (phase: spec-review) [opal-agent 채널 — 동기/비동기] ★검증 2원화 ①
  ↓ (verdict: fail) → T1 재작업 (반복상한 — loop-control.md §2)
  ↓ (verdict: pass)
T3 구현 [opal-agent 채널 — 동기/비동기]
  ↓
T4a 테스트 — test-agent, 구현 후 [opal-agent 채널 — 동기/비동기] ★검증 2원화 ②
  ↓ (fail) → T3 재작업 (하네스 §1 재시도 한도)
  ↓ (pass)
T4b 규칙검사 — conv/sec-checker, 변경 파일 대상 [저위험 인라인 경량화 / 고위험 디스패치 — opal-agent 채널 — 동기/비동기]
  ↓
T5 마무리 — DONE.md
```

**T1 명세·설계**: 태스크의 `area`(fe|be|db|공통|통합)로 루프 액션 에이전트가 생성자를 resolve하여 내부 디스패치한다(아래 "디스패치" 절). PLAN.md(태스크 미시 설계)를 작성한다. 인터랙션 슬라이스면 `USER_FLOW.md`를 함께 작성한다(`references/journey-flow.md` §4). 순수 API/BE 슬라이스는 USER_FLOW.md 없이 CONTRACT.md 기계검증절의 계약 테스트로 대체한다.

**T2 테스트시나리오 (RED-first)**: 루프 액션 에이전트가 scenario-* 도구를 호출하고 test-agent(red)를 내부 디스패치한다 — test-tool `scenario-init`을 호출하고, opal-test-agent(mode: red)가 실패 테스트를 작성·실행해 RED를 실관찰한 후 `scenario-red`로 `red_confirmed`를 증거와 함께 tool-gated로 갱신한다.
```
~/.opal/tools/test-tool/run.sh scenario-init --task-path <T{NN}-path> --scenarios '[{...}]'
# opal-test-agent(mode: red) — 실패 테스트 작성·실행(RED 실관찰)
~/.opal/tools/test-tool/run.sh scenario-red --task-path <T{NN}-path> --id S1 --evidence "{RED 실패 출력 요약}"
~/.opal/tools/test-tool/run.sh scenario-lock --task-path <T{NN}-path>   # 전 시나리오 red_confirmed=true일 때만 통과
```
`scenario-init`은 `red_confirmed`를 항상 `false`로 생성한다(시드 입력 무시) — RED 미관찰 상태를 시드로 우회 선언하는 경로를 봉쇄한다. `red_confirmed`는 오직 `scenario-red`(RED 증거 tool-gated 갱신)로만 true가 될 수 있으며, `locked==true` 이후에는 `scenario-red`도 거부된다. `scenario-lock`이 `red_not_confirmed`를 반환하면 G 게이트에 진입하지 않는다 — self-confirming 테스트를 원천 차단한다(H-2, enforce-don't-advise 보강 — 056/ADD-1).

**G 명세 리뷰 게이트 [루프 액션 에이전트→Evaluator 내부 디스패치, 구현 전]**: 루프 액션 에이전트가 opal-evaluator-agent를 `phase: spec-review`로 내부 디스패치한다.
```
[WORKER]
task_folder: tasks/{NNN}-oppl-{프로젝트명}/tasks/T{NN}-{태스크명}/
phase: spec-review
target_artifacts: [PLAN.md, USER_FLOW.md(있으면), test-scenario.json]
contract_path: tasks/{NNN}-oppl-{프로젝트명}/CONTRACT.md
timestamp: {ISO8601}
project_root: {프로젝트 루트}
```
verdict `fail` → T3에 진입하지 않고 T1로 되돌린다. verdict `pass` → T3 진입.

**T3 구현 [루프 액션 에이전트→생성자 재개 지시]**: G verdict pass 후에만 루프 액션 에이전트가 생성자에게 구현 재개를 지시한다. 하네스 §1 자동 루핑 제약(lint/build/test 재시도 한도)을 따른다.

**T4a 테스트 [루프 액션 에이전트→test-agent 내부 디스패치, 구현 후]**: 루프 액션 에이전트가 opal-test-agent를 내부 디스패치하여 test-scenario.json의 시나리오를 실행하고 result존을 기록한다.
```
~/.opal/tools/test-tool/run.sh scenario-mark --task-path <T{NN}-path> --id S1 --result pass --evidence "{근거}"
~/.opal/tools/test-tool/run.sh scenario-status --task-path <T{NN}-path>
```
[MUST] T4a는 `test-tool scenario-fidelity-check` 통과(요구 충실도 충족)를 완료 요건으로 삼는다 — 요구 충실도 주입·게이트 호출 상세는 `opal/agents/opal-loop-action-agent/AGENT.md`로 위임한다.

**T4b 규칙검사**: 루프 액션 에이전트가 규모 판정 후 인라인 또는 내부 디스패치한다 — 변경 파일이 저위험(소규모·단일 파일)이면 opal-convention-checker/opal-security-checker를 인라인으로 결과만 요약하거나 생략 판단하고, 고위험(다중 파일·계약 영향)이면 내부 디스패치한다.

**T5 마무리**: DONE.md를 작성하고 L∞ 관찰로 복귀한다.

---

## 디스패치 (루프 액션 에이전트)

PM은 **태스크당 `opal-loop-action-agent`를 1회 디스패치**하며, 루프 액션 에이전트가 내부에서 생성자(constructor)·Evaluator·test-agent를 각각 별도 축으로 디스패치하여 T1~T5+G 전체를 완주한다.

| # | 시점 | 대상 | 역할 |
|---|------|------|------|
| PM 디스패치 | L0 태스크 선택 후 | `opal-loop-action-agent` | 태스크당 1회 — T1~T5+G 전체 위임 |

**루프 액션 에이전트 내부 디스패치** (루프 액션 에이전트가 내부에서 수행 — PM 디스패치 횟수에 포함되지 않음):

| # | 시점 | 대상 | 역할 |
|---|------|------|------|
| ①a | T1 | 생성자 (도메인 resolve) | 명세·설계 |
| ①b | T2 | test-agent(mode:red) | RED-first 시나리오 작성 |
| ② | G | opal-evaluator-agent | 명세 리뷰 (구현 전) |
| ③ | T3 (verdict pass 후 재개) | 생성자 (①a와 동일 에이전트) | 구현 |

루프 액션 에이전트 내부에서 T4a(test-agent, 구현 후)는 검증 2원화의 두 번째 축으로 별도 디스패치되며, T4b(conv/sec-checker)는 **저위험 슬라이스에서 인라인 경량화**(디스패치 생략, 결과만 요약)하여 내부 디스패치 수를 절약한다. **drift 재콜백**(구현/테스트 중 CONTRACT.md와의 불일치 발견 시에만) 외에는 Evaluator를 재호출하지 않는다(`references/contract.md` §4).

**생성자 도메인 resolve** — 루프 액션 에이전트가 태스크의 `area` 필드로 결정한다:

| area | 생성자 |
|------|--------|
| `fe` | opal-fe-agent |
| `be` | opal-be-agent |
| `db` | opal-db-agent |
| `공통` / `통합` | opal-task-agent (범용) |

**디스패치 idiom (PM → 루프 액션 에이전트)**: PM은 프롬프트 첫 줄에 `[WORKER]` 마커(부트스트랩 생략)를 넣고, `opal-loop-action-agent`의 입력 명세 10필드(`task_id, task_goal, task_scope, task_area, acceptance, task_folder, verify_commands, contract_path, project_root, project_context` — `opal/agents/opal-loop-action-agent/AGENT.md` §입력 명세 참조)를 전달한다.

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 주입 항목·핵심 제약(전 워커 공통 고정 포함)은 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿을 따른다 — 본 스킬은 항목을 열거하지 않는다.

**디스패치 idiom (루프 액션 에이전트 → 생성자/Evaluator/test-agent)**: opal-agent 채널 호출(동기/비동기 이원화·`[WORKER]` 마커 — `opal/agents/opal-loop-action-agent/AGENT.md` §실행 프로세스 참조)을 따른다 — 루프 액션 에이전트가 area로 생성자 도메인을 resolve한 후 내부 디스패치하며, T1~T5+G 전체가 루프 액션 에이전트 위임 범위다(G 게이트가 루프 액션 에이전트 내부에서 T2와 T3 사이를 끊는다).

**blocked 반환 시**: 루프 액션 에이전트가 `status: blocked`를 반환하면 PM은 즉시 자율 재시도를 중단하고 `blockers[]` 사유를 확인하여 사용자에게 에스컬레이션한다(`references/loop-control.md` §7·§9). 루프 액션 에이전트는 소유자에게 직접 에스컬레이션하지 않는다.

**진행 현황 모니터링**: 루프 액션 에이전트 실행 중/완료 후에는 `~/.opal/tools/opal-action-monitor/run.sh <task_folder> [--watch]`로 단계×축 현황판을 관측할 수 있다. 결과 파일 규약 v2·운행 일지(journal) 상세는 `opal/agents/opal-loop-action-agent/AGENT.md` 참조. 스킬 발동: `//opas [태스크폴더]` — 자동 탐지 + 해석 보고(읽기 전용).

---

## 검증 2원화

**루프 액션 에이전트 내부에서 Evaluator(명세 심판, 구현 전) → test-agent(동작 검증, 구현 후)** 순서로 진행하며, 순서가 뒤바뀌면 G 게이트가 무력화된다(H-9). 상세 규칙(순서 불변 4항목, drift 재콜백 예외, 순서 evidence 확인 방법)은 `references/verification.md` §3을 따른다.

검증 3-tier(① 결정론 code-based → ② 루브릭 LLM-judge → ③ 사람)와의 교차점: G 게이트 = "Evaluator" × "② 루브릭", T4a = "test-agent" × "① 결정론". 전체 tier 표·실패 시 되돌림 규칙은 `references/verification.md` §2를 따른다. 충실도 사다리·done 규범: `references/verification.md` §1.5.

---

## 루프 제어

Loop 1·Loop 2·태스크 내부 파이프라인 모두 아래 **5종 종료조건**을 갖는다 — 상세는 `references/loop-control.md`를 참조한다.

1. **반복 상한** — 루프별 hard iteration cap (`references/loop-control.md` §2; 공통 상한은 `pilot.start`가 전달한 `guards`의 자동 루핑 제약을 적용한다)
2. **예산** — 토큰/비용 예산, 태스크당 루프 액션 에이전트 1회 디스패치를 초과하는 재디스패치를 소진 신호로 관찰 (`references/loop-control.md` §3)
3. **무진전 감지** — 백로그 정체·동일 실패 반복·drift 반복 재콜백 등 신호 (`references/loop-control.md` §4)
4. **목표 달성 체크** — 도구 결과(`backlog-tool done-check`, `test-tool scenario-status`)로만 판정, 주관적 판단 배제 (`references/loop-control.md` §5)
5. **사람 게이트** — 배포·DB·TRD/PRD 확정·외부 계약 등 비가역 행동 전 항상 사용자 승인 (`references/loop-control.md` §9)

경로 분리(성공/실패/에스컬레이션)·에러 처리(복구가능 vs 하드블로커)·컨텍스트 관리(압축 작업기억)는 위 5종 종료조건을 안전하게 운용하기 위한 보조 장치이며 `references/loop-control.md` §6·§7·§8에서 상세히 다룬다.

---

## CONTRACT 거버넌스

CONTRACT.md는 oppl의 1급 산출물이다 — 작성=Planner(D4) / 리뷰=Evaluator(D6·G·drift 재콜백) / 반영=PM. 구조(스키마·시그니처·경계 + 기계검증절 + 루브릭절)와 변경 거버넌스 오너십 계층 4단계(무변경→PM 자율 / 내부조정→PM 자율 / 인터페이스변경→통합 게이트 / 외부노출→사용자)는 `references/contract.md`를 그대로 따른다. drift 판정은 Evaluator가 binary(yes/no)로만 하며, 반영 처리는 항상 PM 또는 거버넌스가 지정한 처리 주체(통합 게이트/사용자)를 통과한다 — Evaluator는 CONTRACT.md를 직접 수정하지 않는다(생성자≠평가자).

---

## Agentic / Semi-Agentic 모드

opal-harness-agentic.md / opal-harness-semi-agentic.md 참조. 본 절은 이 스킬의 차이점만 기술한다.

### 기본 모드 (semi-agentic)

기본 호출(`//oppl {요청}`)은 semi-agentic 모드. **Loop 1(설계 수렴, PLAN-equivalent)까지 사용자 검토**, **Loop 2(실행 수렴, EXECUTE-equivalent) 이후 PM 자율**, CLOSE 진입은 사용자 승인 필수.

**모드 경계** (이 시점부터 PM 자율):
- D7 사용자 확정 게이트(Loop 1 종료) 통과 후 → Loop 2 L0 첫 행부터 PM 자율
- Loop 1 내부(D1~D6)는 사용자 검토 영역 — 각 워커 디스패치 결과(PRD/TRD/CONTRACT/D6 verdict)를 D7 이전에 축적하여 한 번에 검토받는다(oppd Phase 1~2와 동일 정신)

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//oppl 요청` | semi-agentic (기본) |
| `//oppl --interactive 요청` | interactive — 모든 단계 사용자 승인 (Loop 2 태스크 시작 전마다 게이트) |
| `//oppl --agentic 요청` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

### 활성화

> STATE.md 초기 생성은 §STATE.md 초기 생성 참조.

### 자율 게이트 흐름 (semi-agentic)

```
TASK (사용자 승인)
  → Loop 1 D1~D6      -- 사용자 검토 (인터뷰/PRD/TRD/CONTRACT/백로그/D6 Evaluator 검토 축적)
  → D7 사용자 확정 게이트  -- 사용자 승인 (모드 경계)
  → Loop 2 L0~L✓       -- PM 자율 관리 (태스크별 루프 액션 에이전트 디스패치, G 게이트 + T4a/T4b 포함)
  → VERIFY (L✓ 종료 판정) -- PM 직접 확인 → 사용자 Gate (= CLOSE 진입 게이트)
  → CLOSE              -- (사용자 승인 후) DONE.md 생성 + 최종 보고
```

### 자율 게이트 흐름 (agentic)

동일 흐름에서 D7 게이트까지 PM이 자율 검토·확정하고(사용자 확인 행은 PM 명시 호출 없이 다음 단계 진입 시 도구가 자동 승인 — 계약 SSOT: `opal/core/references/opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`), Loop 2 전체를 PM이 자율 관리한다. **비가역 행동(loop-control.md §9)은 agentic에서도 예외 없이 사용자 승인을 받는다** — TRD/PRD 확정(D7)·배포·DB 마이그레이션이 여기 해당하므로, D7은 agentic에서도 자동 통과 대상이 아니다.

### G 게이트 재작업 루핑

명세 리뷰(G) verdict `fail` → T1 재지시 (재시도 한도: `references/loop-control.md` §2와 `pilot.start`가 전달한 `guards`의 PLAN 재진입 규칙). 한도 초과 → 사용자 에스컬레이션.

### CLOSE 진입 게이트 (공통)

semi-agentic / agentic 모두 CLOSE 첫 행(#19) `--auto-pass` 거부 (`agentic_close_gate_requires_user`). 소유자 발화 후 직전 사용자 확인 행(#18) `--owner user` mark 필수.

### AGENTIC-LOG.md 생성 시점

- agentic: TASK 시작 시점
- semi-agentic: Loop 2 L0 첫 행 advance 시점에 PM이 생성

### oppl 고유 에스컬레이션 조건

opal-harness-agentic.md 공통 기준에 추가:
- Evaluator drift 판정이 오너십 계층 #4(외부 노출)로 분류된 경우 (`references/contract.md` §4)
- 무진전 감지(`references/loop-control.md` §4) 신호가 관찰된 경우
- 반복 상한 초과 (`references/loop-control.md` §2)

---

## 산출물 · 기록 규칙

모든 단계·검사는 완료의 일부로 산출물을 자동 생성한다(done = verified 헌법). 기존 OPAL 리포트 포맷을 재사용한다 — 새 포맷을 만들지 않는다.

| 이벤트 | 자동 산출물 |
|--------|-----------|
| T2 테스트시나리오 작성 | test-scenario.json (spec존) |
| G 명세 리뷰 | QA-SPEC.md |
| T4a 테스트 | test-scenario.json (result존) |
| T4b 규칙검사 | `GC-CONVENTION-{ts}.md` · `GC-SECURITY-{ts}.md` |
| T5 마무리 | DONE.md (태스크) |

위 5종 리포트로 커버되지 않는 검사(예: 드라이런 E2E처럼 여러 검사가 복합된 경우)는 태스크 폴더 `VERIFICATION.md`에 기록한다. 모든 기록은 공통 결과 계약 `{대상, 결과(PASS/FAIL), 사유, 시점}`을 포함한다 — 상세는 `references/verification.md` §4·§5를 따른다.

---

## 병렬 실행

- **태스크 간 병렬**: 기본은 worktree 격리(`.worktrees/{task-id}/`) — 의존관계 없는 태스크는 병렬 디스패치한다.
- **태스크 내 FE/BE 병렬**: CONTRACT.md가 이미 고정(잠김)되어 있을 때만 허용한다 — 계약이 확정되지 않은 상태에서 FE/BE를 병렬로 진행하면 인터페이스 drift 위험이 커진다.
- **통합 태스크 필수**: 병렬 그룹마다 머지 후 통합 검증(계약 conformance + 회귀)을 담당하는 통합 태스크를 백로그에 별도로 둔다. 이 규칙은 prose 권고에 그치지 않는다 — `backlog-tool coverage-check`가 parallel_group 존재 + area=통합 태스크 부재를 `integration_task_missing`으로 거부하여 도구가 집행한다(D7 진입 게이트).
- **STATE.md는 PM 단독 갱신**: 병렬 실행 중에도 STATE.md는 오케스트레이터(PM)만 갱신한다(동시 쓰기 충돌 방지). backlog.json은 `backlog-tool mark`의 파일 락(H-3, README §4)으로 동시 쓰기 안전성을 보장하므로 태스크별 상태 반영은 각 태스크 완료 시점에 즉시 반영해도 된다.

---

## DONE.md / CLOSE

Loop 2 종료(L✓ all_done + 회귀 0) 및 사용자 확인(CLOSE 진입 게이트) 후 프로젝트를 마감한다.

```markdown
# DONE: {프로젝트명} 루프 개발

> 완료일: YYYY-MM-DD | 스킬: //oppl

## 생성 문서 (docs/ 승격)

| 문서 | Loop | 확정일 |
|------|------|--------|
| docs/PRD.md | 1 | YYYY-MM-DD |
| docs/TRD.md | 1 | YYYY-MM-DD |
| docs/CONTRACT.md (또는 태스크 폴더 유지) | 1 | YYYY-MM-DD |

## 실행 태스크

| # | 태스크 | 경로 | area | 결과 |
|---|------|------|------|------|
| T01 | {제목} | tasks/T01-.../ | be | 완료 |

## 프로젝트 요약

{전체 루프 진행 요약, 재회전 횟수, 에스컬레이션 이력, 다음 단계}
```

1. CLOSE 첫 행(#19) `--auto-pass` 거부 준수 — 위 "CLOSE 진입 게이트" 절 참조.
2. **관련 문서 업데이트** (op-brain-ingest 디스패치 직전): `docs/PROJECT.md` 문서 레지스트리와 이번 프로젝트의 `changed_files`를 종합하여 관련 문서(ARCHITECTURE.md 등)를 최신화한다. 대상 없으면 no-op.
3. **op-brain-ingest 디스패치** (DONE.md 생성 직후): `.opal/brain/` 존재 시 워커 디스패치(PRD/TRD/CONTRACT 결정·DONE.md를 brain에 누적), 부재 시 no-op — 어떤 경우도 CLOSE를 중단시키지 않는다.
   - 탐색 경로: `{프로젝트}/.opal/skills/op-brain-ingest/SKILL.md` → `~/.opal/skills/op-brain-ingest/SKILL.md`
4. 완료 보고:
```
✅ [CLOSE] oppl 프로젝트 완료
📎 산출물: tasks/{NNN}-oppl-{프로젝트명}/DONE.md
Loop 1 재회전 {N}회 · Loop 2 태스크 {M}개 완주.
```

---

## 스킬 탐색 경로

**opi (사전 조건 미충족 시)**:
1. `{프로젝트}/.opal/skills/opal-project-init/SKILL.md`
2. `~/.opal/skills/opal-project-init/SKILL.md`

**opal-loop-action-agent (Loop 2 루프 액션 에이전트, PM이 태스크당 1회 디스패치)**:
1. `{프로젝트}/.opal/agents/opal-loop-action-agent/AGENT.md`
2. `~/.opal/agents/opal-loop-action-agent/AGENT.md`

**opal-planning-agent / opal-plan-agent (Loop 1 D2~D4 생성자)**:
1. `{프로젝트}/.opal/agents/opal-planning-agent/AGENT.md`, `opal-plan-agent/AGENT.md`
2. `~/.opal/agents/opal-planning-agent/AGENT.md`, `opal-plan-agent/AGENT.md`

**opal-evaluator-agent (D6·G·drift 재콜백)**:
1. `{프로젝트}/.opal/agents/opal-evaluator-agent/AGENT.md`
2. `~/.opal/agents/opal-evaluator-agent/AGENT.md`

**생성자 (fe/be/db/opal-task-agent, T1~T3)**:
1. `{프로젝트}/.opal/agents/{opal-fe-agent|opal-be-agent|opal-db-agent|opal-task-agent}/AGENT.md`
2. `~/.opal/agents/{opal-fe-agent|opal-be-agent|opal-db-agent|opal-task-agent}/AGENT.md`

**opal-test-agent (T4a) / opal-convention-checker·opal-security-checker (T4b)**:
1. `{프로젝트}/.opal/agents/{opal-test-agent|opal-convention-checker|opal-security-checker}/AGENT.md`
2. `~/.opal/agents/{opal-test-agent|opal-convention-checker|opal-security-checker}/AGENT.md`

---

## 프로젝트 메모리 동기화

`{프로젝트}/.opal/MEMORY.json`이 존재하면, 루프 전환 시 작업 히스토리를 memory-tool로 갱신한다:

```
~/.opal/tools/memory-tool/run.sh append --file .opal/MEMORY.json --kind history \
  --title "<태스크명>" --stage "<단계>" --path "tasks/<폴더>/" --summary "<핵심결과>"
```

- Loop 1 확정: `--stage "Loop 1 확정 → Loop 2 진행"`
- Loop 2 태스크 완료마다: `--stage "Loop 2 — T{NN} 완료 ({M}/{전체})"`
- 전체 완료: `--stage "완료"`
- [MUST] 표·파일 직접 편집 금지 — 도구 호출만 사용한다. FIFO 5(도구 결정론 집행)는 상세: `opal/core/references/harness/observability.md` §프로젝트 메모리 동기화 참조.

---
