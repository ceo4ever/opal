---
name: opal-pilot-dev
description: |
  **Dev Pilot 오케스트레이터**. `opd` Full profile과 `opds` Short profile을 하나의 canonical 스킬로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-dev", "opd", "opds".
  코드를 읽기만 하는 설명 요청, API 명세서(api-analyzer), 기획 문서(opal-pilot-write-tech), PR 리뷰, git 작업, 단순 설정 변경은 이 스킬이 아니다.
---
# Full Task 오케스트레이터

**[MUST — 세 축 선결]** 태스크 경로를 확정한 뒤 `state-tool resolve-start <task-path> --skill <opd|opds> [--new-task] <사용자 원문 플래그>`를 서브 하네스 로드보다 먼저 호출하고, 응답의 `effective_mode`·`workspace`·`actor`만 사용한다. 신규 태스크 기본값은 agentic·worktree·PM 조율(`actor=coordinator`)이며 원문은 `harness/modes.md`·`harness/worktree.md`·`harness/actor.md`가 소유한다. 기존 태스크 재호출·세션 재개·사용자 검토 왕복은 무플래그면 저장 mode·workspace·actor를 상속하고, 명시 mode 플래그만 resolver가 mode를 갱신한다. 충돌·재개 축 변경은 resolver 오류 코드로 멈춘다.

## Harness
모드: Full Task (TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE)
**[MUST — pilot.start 이벤트 게이트]** 파일럿의 첫 작업 전에 아래 순서를 수행한다.

1. `~/.opal/tools/event-loader/run.sh load --event pilot.start > <pilot-receipt-path>`를 호출한다.
2. load 응답의 `documents[].content` 전문을 모두 현재 컨텍스트에 적용하고, 위 `resolve-start` 결과의 `effective_mode`로 `modes` 문서가 라우팅한 서브 하네스 전문 하나만 Read한다.
3. `~/.opal/tools/state-tool/run.sh event-verify --event pilot.start --receipt <pilot-receipt-path>`가 성공한 뒤에만 진행한다.

**[MUST — 단계 이벤트 게이트]** 각 실제 단계의 첫 작업이나 `state-tool advance` 직전에 아래 매핑의 이벤트를 load하고, 응답 문서 전문을 적용한 뒤 같은 event id로 `state-tool event-verify`를 통과해야 한다.

| 실제 단계 | 이벤트 |
|---|---|
| TASK | stage.task |
| ANALYSIS | stage.analysis |
| PLAN | stage.plan |
| TEST-SCENARIO | stage.test_scenario |
| EXECUTE | stage.execute |
| TEST | stage.test |
| CLOSE | stage.close |

호출 형식은 `~/.opal/tools/event-loader/run.sh load --event <stage.*> > <stage-receipt-path>` 다음
`~/.opal/tools/state-tool/run.sh event-verify --event <stage.*> --receipt <stage-receipt-path>`이다.
문서 집합은 `events.json`만 SSOT로 사용하며 SKILL에 파일 목록을 복제하지 않는다. load 실패,
필수 문서 누락, stale receipt, wrong-event receipt는 해당 파일럿·단계 진입을 즉시 중단하는
blocker다. 부트 캐시를 근거로 공통 문서를 직접 재Read하는 우회는 금지한다.

### actor 축

[MUST] actor 값·신규 기본값·재개 상속·PM 조율 계약·독립 검증 경계는 `opal/core/references/harness/actor.md`(SSOT)를 따른다. 원문을 이 스킬에 복제하지 않는다.

이 스킬의 단계별 분기는 저장 actor 세 값만 본다.

| 저장 actor | 진입 | ANALYSIS·PLAN | EXECUTE 구현·TEST FAIL 수정 |
|---|---|---|---|
| `coordinator` | 신규 기본 또는 `--pm` | PM 직접 작성 | PLAN `담당`의 전문 워커 디스패치 |
| `worker` | `--no-pm` 또는 actor 키 부재(legacy) | 전문 워커 디스패치 | 전문 워커 디스패치 |
| `pm` | legacy 재개 전용 | PM 직접 작성 | PM 직접 수행 |

최초 단계 보고 시 `harness/observability.md` §행위 주체 표시 형식으로 저장 actor 선언 1행을 포함한다.

## 프로필 선택

[MUST] 사용자가 선택한 프로필을 기본 수행한다. `//opd`는 Full profile, `//opds`는 Short profile이다.

- Full profile은 아래 STEP 1~6을 수행한다.
- Short profile은 `references/pipeline-short.json`을 상태 행 SSOT로 사용하고, TASK 후 아래 Short PLAN 절을 거쳐 Full profile의 STEP 4~6(EXECUTE·TEST·CLOSE 공통 절차)을 재사용한다.
- 프로필 전환은 자동으로 수행하지 않는다. 강등·강업은 해당 기준 문서에 따른 사용자 제안으로만 처리한다.

### Short profile PLAN

Short profile(`opds`)은 Full profile의 ANALYSIS를 생략하고, PLAN 작성자(`coordinator`·legacy `pm`은 PM, `worker`는 `op-dev-plan` 워커)가 TASK와 프로젝트 문서를 직접 분석해 PLAN을 작성한다.

1. `references/pipeline-short.json`으로 STATE를 초기화한다.
2. `stage.plan` 이벤트 게이트 통과 후 아래 STEP 3-1의 actor 분기대로 PLAN을 작성한다.
3. PLAN 수신 후 PM이 TEST-SCENARIO를 작성하고 `plan.scenario_gate`와 `plan.pm_gate`를 통과시킨다.
4. PLAN 완료 직후, EXECUTE 진입 전에 [track-escalation.md](references/track-escalation.md)의 핵심 질문을 1회 검토한다.
   - 미결정 동작·계약·구조가 없으면 `opds`를 계속한다.
   - 미결정 사항이 있으면 사용자에게 `opd` 전환을 제안한다.
   - 사용자가 거절하면 `opds`를 계속하고, 결정 없이는 실행할 수 있을 때만 blocker로 보고한다.
5. 사용자 확인 또는 agentic 자동 승인 후 Full profile의 STEP 4 EXECUTE로 진입한다. 강업 제안을 사용자가 수락하면 TASK·PLAN을 인계해 Full profile의 STEP 2 ANALYSIS부터 재개한다.

강업 제안은 `track-escalation.md`의 판정 시점·1회 제안·사용자 선택 계약을 따른다. 파일 수·변경량은 판정에 사용하지 않는다.

## STEP 1: TASK
`stage.task`가 전달한 `task-process` 전문을 따른다.

TASK 완료 → 사용자 보고.

> **[MUST] 행 갱신**: `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step <task-step-key> --done` 호출. **[MUST] 파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다.** 행을 mark하는 것 자체가 state 기록이며 별도의 State Gate 행은 존재하지 않는다.
> **단계 시작 (P-3)**: `~/.opal/tools/state-tool/run.sh advance <task-path> --task-step <task-step-key>` 호출로 해당 단계 작업 행을 🔄로 전환.
> **단계 건너뛰기 차단**: state-tool stage-transition guard가 단계 N의 필수 행이 완료되지 않으면 단계 N+1 진입(mark)을 자동 거부한다 (PLAN §M-A). 행에 의존하지 않는다.
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §1.5 M-11 / §3 Step 8 P-1 / P-3

> **[MUST] 트랙 강등 제안**: 사용자가 선택한 `opd`를 기본 수행한다. `ANALYSIS` 완료 직후 `PLAN` 진입 전에 `opal/skills/opal-pilot-dev/references/track-routing.md`(SSOT)의 핵심 질문 — "현재 단계 이후에 외부 영향이 있는 동작·계약·구조 결정을 새로 해야 하는가?" — 을 1회 검토한다. 답이 아니오일 때만 `opds` 강등을 사용자에게 제안하며, 자동 전환하지 않는다. 판단 불능이면 `opd`를 유지한다.

## STEP 2: ANALYSIS

**actor=worker**: 워커를 디스패치하여 코드베이스를 분석한다(아래 디스패치 프롬프트).
**actor=coordinator·legacy pm**: PM이 `op-dev-analysis/SKILL.md`를 직접 Read하고 아래 디스패치 프롬프트와 같은 입력·출력·산출물 경로 계약(태스크 폴더·이전 산출물·프로젝트 컨텍스트·산출물 저장 경로·하네스 Guards·참조 문서·분석 질문)을 적용해 ANALYSIS.md를 직접 작성한다. 이 작성에는 워커를 호출하지 않으므로 `worker.dispatch`가 발생하지 않는다.

**디스패치 프롬프트** (actor=worker):
```
[WORKER]
op-dev-analysis 스킬을 수행하라.
**스킬 경로**: {op-dev-analysis/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {ANALYSIS.md 경로}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식으로 원문 인용 필수 항목. 요약 허용 항목은 일반 목록}
**분석 질문**: {Q1~QN — PM이 이번 분석에서 답을 받아야 할 질문. 없으면 "없음"}
```
**model**: standard

워커 완료
  → **PM Gate** (분석 방향 종합 검토)
  → 사용자 보고 (분석 방향 검토 후 PLAN 진입 승인).

> **사용자 확인 (P-5)**: 이 행은 **모드에 따라 주체가 다르다**.
> - 자동 승인 구간(agentic 전 구간 / semi-agentic의 EXECUTE-equivalent 이후) — **PM은 호출하지 않는다.**
>   다음 단계 진입 시 도구가 자동 승인한다. 계약 SSOT: `opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`.
> - 그 외(interactive 전 구간 / semi-agentic의 모드 경계 내) — 소유자에게 보고하고 승인 발화를 받은 뒤
>   `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step analysis.user_confirm --done --owner user --note '{owner_name} 확인: ...'` 호출.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-5

## STEP 3: PLAN

### 3-1. PLAN 디스패치

**actor=worker**: 워커를 디스패치한다(아래 디스패치 프롬프트).
**actor=coordinator**: PM이 `op-dev-plan/SKILL.md`를 직접 Read하고 아래 디스패치 프롬프트와 같은 입력·출력·산출물 경로 계약을 적용해 PLAN.md를 직접 작성한다. PLAN.md `Work items`의 `담당` 열에는 구현을 맡을 전문 워커 역할명(`docs/PROJECT.md` 프로젝트 구성 매핑, 없으면 `opal-task-agent`)을 기록하고, 같은 실행 그룹에는 선행 관계가 없고 변경 파일이 겹치지 않는 W만 둔다.
**actor=pm(legacy)**: 위와 같이 PM이 직접 작성하되 `담당` 열은 `PM`으로 기록한다.

```
[WORKER]
op-dev-plan 스킬을 수행하라.
**스킬 경로**: {op-dev-plan/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}, {ANALYSIS.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {PLAN.md 경로}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식으로 원문 인용 필수 항목. 요약 허용 항목은 일반 목록}
```
**model**: advanced

> sdlc-v2 신규 경로에서는 PLAN 병렬 TEST-SCENARIO 선작성을 기본 수행하지 않는다. TEST-SCENARIO는 STEP 3.5에서 TASK.md의 AC/C와 PLAN.md의 Risks/Work items를 함께 읽고 한 번에 작성한다. legacy 태스크 재개나 사용자가 명시한 RED-first opt-in에서만 기존 선작성 규칙을 적용한다.

PLAN 완료
  → **PM Gate** (PLAN.md 직접 검증 — 점검 목록 참조):
    1. `{PLAN.md 경로}` Read — sdlc-v2 `Approach`, `Decisions and contracts`, `Work items`, `Risks`, `Release and recovery` 확인
    2. 검증 체크리스트:
       - [ ] TASK.md AC/C가 Work items의 완료 기준 연결에 반영되어 있는가
       - [ ] Work items에 담당·변경 대상·구체적 변경·선행 작업·실행 그룹·완료 기준 연결이 채워졌는가
       - [ ] Risks에 실제 추가 검증 위험만 H-N으로 작성되었거나, 위험 없음이 명시되었는가
       - [ ] Release and recovery에 source→installed 검증, 실제 사례 측정, 실패 복구 기준이 있는가
       - [ ] `state-tool verify <task-folder> --plan-contract-check`와 `--code-scan-citation-check`가 통과 또는 의도된 skip인지 확인했는가
  → PM Gate 통과 후 해당 행을 단일 mark. 사용자에게 PLAN 보고. 승인 = TEST-SCENARIO 단계 진입 허가.

## STEP 3.5: TEST-SCENARIO

> **[MUST] RED-first**: TEST-SCENARIO 작성 시 RED-first 트랙 적용 여부를 판단하고 기재한다. 규칙 SSOT: `opal/core/references/harness/red-first.md`. 목표계열 선작성 트랙은 동 문서 §1.6.

작성자: **PM** — actor와 무관하게 오케스트레이터가 직접 작성한다(작성 워커 디스패치 없음). 사용자 확인은 현재 진행 모드의 `test_scenario.user_confirm` 경계를 따른다.
`actor=worker`는 PLAN 작성자(opal-plan-agent)와 작성자가 분리된다. `coordinator`·legacy `pm`은 PM이 PLAN도 쓰므로, 자기 확인 방지는 아래 목표-커버 게이트의 독립 evaluator와 TEST 단계의 opal-test-agent가 맡는다(`harness/actor.md` §독립 검증 경계).

1. TASK.md의 AC/C와 PLAN.md `Risks`의 H-N, `Work items`의 변경 대상·실행 그룹을 입력으로 사용한다.
2. `op-dev-test-scenario/SKILL.md`와 `test-scenario-guide.md`에 따라 `Setup / Scenarios`를 한 번 작성한다.
3. 작성 계약을 확인한 뒤 문서 작성 행을 mark한다 (`~/.opal/tools/state-tool/run.sh mark <task-path> --task-step test_scenario.test_scenario_md --done` — P-1).
4. **목표-커버 게이트**: `~/.opal/tools/state-tool/run.sh advance <task-path> --task-step test_scenario.scenario_gate` 호출 후, `op-scenario-gate` 스킬을 호출한다.
   - 탐색 경로: `{프로젝트}/.opal/skills/op-scenario-gate/SKILL.md` → `~/.opal/skills/op-scenario-gate/SKILL.md`
   - 입력: `task_folder`(태스크 폴더 경로), `producer_artifact`(`{task_folder}/TEST-SCENARIO.md`), `pilot: opd`, `iteration`(최초 호출 = 1)
   - 수신 `verdict: pass` → 게이트 행 mark (`~/.opal/tools/state-tool/run.sh mark <task-path> --task-step test_scenario.scenario_gate --done` — Step 3 tool-gated 두 증거 근거로만 mark, 산문 판단으로 mark 금지)
   - 수신 `verdict: rewrite` → PM이 `gaps`를 반영해 TEST-SCENARIO.md를 보완한 후 `iteration+1`로 op-scenario-gate 재호출 (루프, 게이트 행은 아직 mark하지 않음)
   - 수신 `verdict: escalate` → 사용자에게 에스컬레이션하고 자율 재시도하지 않음
   - `test_scenario.scenario_gate` 행 mark 시점은 문서 작성 완료(3) 후 `verdict: pass` 수신 이후다.
5. 사용자에게 TEST-SCENARIO 보고 — 승인 = EXECUTE 시작 허가

> **[MUST] actor 무관 유지**: 목표-커버 게이트(`op-scenario-gate` 디스패치와 `verdict: pass` 요건)는 `actor` 값과 무관하게 항상 동일하게 적용된다 — PM이 TEST-SCENARIO를 쓰는 어느 actor에서도 PM 산문 판단만으로 `test_scenario.scenario_gate`(opds는 `plan.scenario_gate`) 행을 mark할 수 없다(`harness/actor.md` §독립 검증 경계).

> **사용자 확인 (P-5)**: 이 행은 **모드에 따라 주체가 다르다**.
> - 자동 승인 구간(agentic 전 구간 / semi-agentic의 EXECUTE-equivalent 이후) — **PM은 호출하지 않는다.**
>   다음 단계 진입 시 도구가 자동 승인한다. 계약 SSOT: `opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`.
> - 그 외(interactive 전 구간 / semi-agentic의 모드 경계 내) — 소유자에게 보고하고 승인 발화를 받은 뒤
>   `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step test_scenario.user_confirm --done --owner user --note '{owner_name} 확인: ...'` 호출.
> CLOSE 전이는 이 행의 mode-aware 자동 승인 여부를 포함해 `harness/modes.md` §CLOSE 전이 계약이 소유한다.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-5 / §2.16 G-13 / `tasks/073-260723-opd-시나리오-목표커버리지-루프/PLAN.md` §3.5.2 (목표-커버 게이트 접합)

## STEP 4: EXECUTE

**actor 분기**: `coordinator`와 `worker`는 모든 Work item을 PLAN `담당`의 전문 워커에게 아래 4-1~4-3 절차로 디스패치한다 — PM은 구현하지 않고 분배·파일 소유권·결과 검토·재작업 지시를 맡는다. legacy `pm` 태스크에서 `담당`이 `PM`인 행만 PM이 `op-dev-execute/SKILL.md`를 직접 Read하고 4-2 디스패치 프롬프트와 같은 입력·출력(checklist_source·scenario_source·완료 기준·자가 점검 절차·Scope 제한)을 적용해 직접 구현한다(`harness/actor.md` §legacy `pm` 재개 계약).

> **[MUST] RED-first**: EXECUTE 진입 전 RED 증거 확보, fix 루핑 중 테스트 불변. 규칙 SSOT: `opal/core/references/harness/red-first.md`.
> sdlc-v2는 TEST-SCENARIO의 `시점`을 기준으로 `test-tool scenario-init`의 `red_required`를 설정한다. RED 대상은 opal-test-agent red mode가 실제 실패를 관찰한 뒤 `scenario-red`로 증거를 기록하고, PM은 `scenario-lock` 통과 후에만 GREEN 구현을 시작한다. RED 대상이 없으면 init 직후 lock한다. legacy만 `state-tool verify <task> --red-check`를 사용한다. fix 루핑 시 `--fix-mode --changed-files ... --test-globs ...`로 테스트 불변성을 검사한다.

워커를 디스패치하여 코드를 작성한다. **model**: standard.

### 4-1. 분배 디스패치 절차 (v3.2 신설)

1. **PLAN.md `Work items` Read** — 각 W의 `담당`, `변경 대상`, `선행 작업`, `실행 그룹`을 확인한다.
2. **계약 검사** — `state-tool verify <task-folder> --plan-contract-check`와 `--code-scan-citation-check`를 호출한다.
3. **실행 그룹 순회** — `P1`, `P2` 순서대로:
   - 실행 그룹 내 배치가 서로 선행 관계가 없고 변경 파일이 겹치지 않을 때만 Agent 도구 병렬 호출
   - 선행 관계나 파일 중첩이 있으면 순차 호출
4. **각 배치마다 워커 디스패치** — 해당 담당 agent로 op-dev-execute 워커 디스패치.
5. **폴백** — `template: sdlc-v2`가 없는 legacy PLAN은 기존 §4.2/§3/execution-plan.json 방식을 사용한다.

### 4-2. 디스패치 프롬프트

```
[WORKER]
op-dev-execute 스킬을 수행하라.
**스킬 경로**: {op-dev-execute/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**checklist_source**: {PLAN.md 경로}, 섹션: Work items (sdlc-v2) 또는 legacy §4.2
**scenario_source**: {TEST-SCENARIO.md 경로}
**완료 기준**: checklist 100% + 담당 Step 매핑 L1/L2 시나리오 PASS (L3는 TEST 단계 위임)
**자가 점검 절차**: 코드 작성 → 시나리오 "실행 명령" 추출 → Bash 실행 → PASS 확인 → 완료 보고
**담당 Work items**: {이 워커가 처리할 W-ID 목록 — 예: W-1, W-3}
**Scope 제한**: {agent 영역 — FE / BE / DB / 공통}. 영역 외 파일 수정 시 즉시 블로커 보고.
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식으로 원문 인용 필수 항목. 요약 허용 항목은 일반 목록}
```

> **에이전트별 자동 가이드 선택**: 워커는 op-dev-execute/SKILL.md의 매핑 테이블에 따라 자기 에이전트 이름으로 execute-specialist-guide.md 또는 execute-generalist-guide.md를 자동 Read한다. PM이 `applied_guide` 파라미터를 주입하지 않는다.

### 4-3. FE/BE 병렬 (`담당` 필드 기반)

PLAN.md Work items의 담당·실행 그룹 필드에 따라 배치를 구성한다:
- **Phase 내 FE·BE 배치가 선행 관계 없고 변경 파일이 겹치지 않으면** 병렬 호출
- **순차 의존**(FE → BE 통합 등)이나 파일 중첩이 있으면 순차 호출

**폴백**: legacy §4.2의 agent 필드가 없거나 execution-plan.json만 존재 시 기존 방식 유지:
1. Phase 1: Common → 단일 워커 순차
2. Phase 2: FE + BE 워커 병렬
3. Phase 3: 양쪽 완료 후 통합

### 4-4. EXECUTE 완료 후

모든 배치 완료 → changed_files 병합 → 행 mark → **TEST 단계 진입**.

> **EXECUTE Step 완료 (P-4)**: 워커가 `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step execute.implement --done --as-worker --worker-stage EXECUTE --action-step <N/M>` 호출 (T-10 워커 권한 게이트).
> **블로커 발생 (P-7)**: `~/.opal/tools/state-tool/run.sh block <task-path> --task-step <task-step-key> --reason '...'` 호출. STATE.md 블로커 섹션 자유 텍스트는 PM이 별도 작성.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-4 / P-7 / §2.11 G-6

---

## STEP 5: TEST

opal-test-agent 워커 디스패치. TEST-SCENARIO.md를 실행 명세로 읽고, `test-tool scenario-status`로 잠금 상태를 확인한 뒤 각 결과·증거를 `scenario-mark`로 기록하고 PASS/FAIL/BLOCKED를 판정한다. E2E 결과는 `test-tool` E2E contract의 final status `pass` / `fail` / `executor_unavailable` / `infra_error` / `blocked`와 operational `awaiting_human`을 보존한다. 사용자 행동이 필요한 시나리오는 구조화 handoff로 `awaiting_human`을 반환하고, 사람 제출을 verifier가 검증한 뒤 final status로 전이한다.

> **[MUST] actor 무관 유지**: TEST 단계(`opal-test-agent` 디스패치·`test.run_tests`+`test.pm_gate`의 실제 실행 증거 요건)는 `actor` 값과 무관하게 항상 서브에이전트가 수행한다 — `coordinator`·legacy `pm`에서도 생략되지 않는다(`harness/actor.md` §독립 검증 경계).

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 주입 항목·핵심 제약(전 워커 공통 고정 포함)은 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿을 따른다 — 본 스킬은 항목을 열거하지 않는다. 단계 추가 전달: TEST-SCENARIO.md 경로 · changed_files.

워커 완료 → 행 mark.

### PASS 시

→ **PM Gate** (TEST-SCENARIO.md 명세 + test-scenario.json 결과 검증):
  1. `{TEST-SCENARIO.md 경로}` Read — 검증 기준 확인
  2. `{test-scenario.json 경로}` Read — 시나리오 PASS/FAIL/BLOCKED와 증거 확인
  3. 검증 체크리스트:
     - [ ] test-scenario.json 모든 필수 시나리오 PASS
     - [ ] 코드 품질 항목(린트/타입/포맷) 모두 Pass
     - [ ] 보안 항목(시크릿 스캔/.gitignore) Pass
     - [ ] 회귀 테스트 항목 Pass
     - [ ] 설계 피드백 미해결 빈틈 없음
     - [ ] 컨벤션 자동 진단 PASS (changed_files 컨벤션 적용 대상 ≥1건 시 발동, GC-CONVENTION-*.md 보고서 Critical/High 0건)
→ PM Gate 통과 후 해당 행을 단일 mark. 완료를 비차단 보고하고 state-tool 전이 출력에 따라 CLOSE를 계속한다.

> **사용자 확인 (P-5)**: 이 행은 **모드에 따라 주체가 다르다**.
> - 자동 승인 구간(agentic 전 구간 / semi-agentic의 EXECUTE-equivalent 이후) — **PM은 호출하지 않는다.**
>   다음 단계 진입 시 도구가 자동 승인한다. 계약 SSOT: `opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`.
> - 그 외(interactive 전 구간 / semi-agentic의 모드 경계 내) — 소유자에게 보고하고 승인 발화를 받은 뒤
>   `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step test.user_confirm --done --owner user --note '{owner_name} 확인: ...'` 호출.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-5

보고 형식:
```
📋 [TEST] 완료 보고
📎 변경 파일: {changed_files}
📎 산출물: {TEST-SCENARIO.md 등}
전이: {transition_action} / 보고: {report_type}
다음 액션: `decision_request`는 실제 미해결 이슈일 때만 보고하고, `progress_report + continue`면 CLOSE를 계속한다.
```

### FAIL 시 (루핑 — 최대 3회, 하네스 §1 L3a)

1. PM이 `test-scenario.json`에서 FAIL/BLOCKED 항목을 추출하고, 해당 S-ID의 기준은 TEST-SCENARIO.md에서 확인한다
2. 실패 항목의 Work item을 구현한 전문 워커에게 op-dev-execute를 fix 모드로 디스패치한다(`coordinator`·`worker`). legacy `pm` 태스크에서 `담당`이 `PM`인 항목만 PM이 같은 fix 계약으로 직접 수정한다:
   ```
   [WORKER]
   op-dev-execute 스킬을 수행하라 (fix 모드).
   **모드**: fix
   **fix 컨텍스트**:
     - 실패한 TEST-SCENARIO 항목: {FAIL 항목 목록}
     - 현재 시도 회차: {N}/3
     - 실패 요약: {opal-test-agent 결과 요약}
   **checklist_source**: PLAN.md 실행 체크리스트 (실패 항목 집중)
   **하네스 Guards**: fix 범위를 실패 항목으로 한정. 회귀 방지: 이전 PASS 항목 재실행.
   ```
3. fix 완료 → fix 행 mark → opal-test-agent 재호출 (루프)
4. 3회 초과 시 사용자 에스컬레이션:
   "TEST {N}회 FAIL — 수동 개입 필요. 실패 항목: {목록}"

---

## STEP 6: CLOSE

모든 체크리스트 갱신 완료 확인 후 태스크를 마감한다.

1. DONE.md 생성 후 행 mark (`~/.opal/tools/state-tool/run.sh mark <task-path> --task-step close.done_md --done` 호출 — P-1). 행을 mark하는 것 자체가 state 기록이다.
   - **DONE.md 템플릿 SSOT**: `opal/core/references/harness/done-template.md`. 절 구성과 `## 회고적 학습 후보` 계약을 그 문서에서 읽는다 — 여기에 템플릿 본문을 복제하지 않는다.
2. **관련 문서 업데이트** (op-brain-ingest 디스패치 직전 실행):
   - `<프로젝트-루트>/docs/PROJECT.md`의 "프로젝트 문서" 레지스트리와 이번 태스크의 `changed_files`(EXECUTE 산출)를 양쪽 종합하여, 태스크 결과로 내용이 달라진 관련 문서(ARCHITECTURE.md·기획서 등)를 식별한다.
   - 갱신 대상이 있으면 PM이 판단하여 직접 수정하거나 적합한 워커를 디스패치해 최신화한다. 갱신 대상이 없으면 자연 스킵(no-op) — CLOSE를 중단시키지 않는다.
   - 목적: brain ingest 이전에 기획·설계 문서를 최신 상태로 만들어 ingest 품질을 보장한다.
3. **op-brain-ingest 디스패치** (DONE.md 생성 직후 실행):
   - `<프로젝트-루트>/.opal/brain/` 존재 여부를 확인한다.
   - **brain이 존재하면**: op-brain-ingest 워커를 디스패치하여 태스크 산출물(DONE.md·PLAN 결정·신규 엔티티)을 brain에 누적한다.
   - **brain이 없으면**: 자연 스킵(no-op). CLOSE가 막히지 않는다.
   - op-brain-ingest 탐색 경로:
     1. `{프로젝트}/.opal/skills/op-brain-ingest/SKILL.md`
     2. `~/.opal/skills/op-brain-ingest/SKILL.md`
   - 디스패치 입력: 태스크 폴더 경로
   - 워커가 `status: skipped` 또는 `status: completed` 또는 `status: completed_with_errors` 반환 — 어떤 경우도 CLOSE를 중단시키지 않는다.
4. **회고(개선 루프) 하드스텝** (op-brain-ingest 직후 실행):
   - 입력: 태스크/세션 궤적 신호 — 워커 재시도·폴백, 소유자 재지시·피드백, PM Gate 반복 이슈, PLAN 재진입, 검증/재설계 루프 로그(STATE.md). ※ 산출물 재독이 아님(그건 PM Gate/QA 담당). 산출 = 프로세스·규칙 개선점.
   - 관찰→분류(로컬 PM 개선 / FW 개선)→기록: 개선 후보별로 `~/.opal/tools/improve-tool/run.sh record --scope <local|fw> --title ... --body ... --situation retrospective --source-task <NNN> --project-root <루트>` 호출.
   - 산출 결정론 기록: 개선 후보 N건은 improve-tool이 결정론적으로 기록(로컬→.opal / FW→fw-inbox).
   - **no-op 안전 [MUST]**: 궤적 신호에서 개선 후보가 **없으면** 기록 없이 "개선후보 0건" 보고 — op-brain-ingest의 skipped와 동일하게 **CLOSE를 중단시키지 않는다**.
   - 개선 루프 프로세스 SSOT: `opal/core/references/harness/pm-improvement-loop.md`.
5. **worktree 정리 안내** (`--worktree`/`--wt` 태스크에서만 — 미사용 시 자연 스킵):
   - **(a) PM이 CLOSE 안에서 수행 — merge _전_ finalize**:
     - 회고(스텝 4) 직후 `~/.opal/tools/worktree-tool/run.sh finalize --project-root <허브 절대경로> --task <NNN>`을 실행한다. `--project-root`는 **항상 허브 절대경로**로 명시한다 — 워크트리에 내려온 `.opal/worktree.json` 사본은 읽기 snapshot이며 워크트리를 허브로 오인하지 않는다.
     - finalize는 DONE.md `## 회고적 학습 후보` 선언 집합을 `S ⊆ D` 판정의 입력으로 쓴다. 선언 계약 원문은 `opal/core/references/harness/done-template.md` §회고적 학습 후보 계약이 소유한다 — 여기에 복제하지 않는다.
     - finalize가 성공하면 태스크 캡슐이 dirty해진다(`memory-index-request.json`의 해당 요청 `status`가 `applied`로 전이). **이 캡슐 변경을 태스크 커밋(merge 대상 브랜치)에 포함**하도록 안내한다 — merge 결과에 코드 변경과 태스크 캡슐이 함께 나타나야 한다.
     - 이어서 `~/.opal/tools/worktree-tool/run.sh status --project-root <허브 절대경로> --task <NNN>`으로 현재 상태를 조회해 보고한다.
     - finalize가 `ATTRIBUTION_COMMIT_BLOCKED`를 반환하면 동봉된 **위반 경로를 그대로 보고**하되 **CLOSE를 막지 않는다**.
     - finalize·`status` 호출 실패·메타 부재·worktree 부재는 전부 **no-op** — op-brain-ingest(스텝 3)·회고(스텝 4)와 동일하게 **CLOSE를 중단시키지 않는다**.
   - **(b) 사용자 merge 이후 실행 명령 안내**:
     - **[MUST] 자동 제거하지 않는다.** CLOSE 시점에 미머지 커밋이 남아 있는 것이 정상이다 — 커밋·머지는 사용자의 권한이며 PM이 대행하지 않는다.
     - 안내 문구: "worktree `{worktree_root}`는 **머지 대기** 상태입니다. 아래 순서로 마감하세요."
       1. 허브에서 `git merge --ff-only feat/OP-TASK-{NNN}` 또는 `git merge --no-ff feat/OP-TASK-{NNN}` (허용 merge 경로는 이 둘뿐이다)
       2. `~/.opal/tools/state-tool/run.sh finalize-attribution <task-path> --allocator-root <허브 절대경로>`
       3. `~/.opal/tools/state-tool/run.sh status <task-path> --set done`
       4. `~/.opal/tools/worktree-tool/run.sh remove --project-root <허브 절대경로> --task <NNN>`
     - `<task-path>`는 `worktree-tool`이 발급한 canonical task path다(merge 확인 뒤에는 허브에 merge된 task path). 해석 규칙 원문은 `opal/core/references/harness/worktree.md` §canonical path 발급 계약이 소유한다.
     - **회수 거부 사유 안내**: `remove`는 미처리 memory index 요청이 남아 있으면 `MEMORY_INDEX_REQUEST_PENDING`으로 먼저 거부하고, 이어서 dirty→unpushed→unmerged 3중 가드를 적용한다. 해소 경로는 `--force` 우회가 아니라 **(a)의 merge _전_ `worktree-tool finalize`** 실행이다 — merge 후 실행이 아니다.
6. 완료 보고

> **CLOSE 전이**: 해당 Pilot의 행 키와 mode-aware 승인·거부·`close.final` 계약은 `harness/modes.md` §CLOSE 전이 계약을 따른다.
> **추가작업 진입 (P-6)**: `~/.opal/tools/state-tool/run.sh add-row <task-path> --after <N> --stage CLOSE --item '...'` 호출 → current_status 자동 `additional_work` 전환. 완료 시 `~/.opal/tools/state-tool/run.sh status <task-path> --set additional_work_done`.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-6 / P-8 / §2.16 G-13

보고 형식:
```
✅ [CLOSE] 태스크 완료
📎 산출물: tasks/{NNN}-{태스크명}/DONE.md
태스크가 완료되었습니다.
```

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 추가작업 프로세스를 따른다.

## STATE.md 도메인 치환값

> **[MUST] STATE.md 초기 생성**: `~/.opal/tools/state-tool/run.sh init <task-path> <resolve-start init_args> [--worktree <worktree_root>] --rows-from opal/skills/opal-pilot-dev/references/pipeline.json`(Short profile은 `pipeline-short.json`) 호출. `init_args`는 `--skill`·`--mode`·`--workspace`·`--actor`를 담으며, `workspace=worktree`면 `harness/task-process.md` 스텝 4.5가 발급한 `--worktree`를 반드시 덧붙인다. 행 구성 SSOT는 `references/pipeline.json`(task-step key 포함) — `--rows-from`이 확장자로 분기해 파싱한다(070).
> **[MUST] actor 영속화**: `init_args`의 `--actor coordinator|worker`를 그대로 전달한다. legacy `--actor pm`은 `actor_pm_retired`로 거부된다. 지원 범위·거부 조건은 `harness/actor.md`(SSOT)를 따른다.
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §2.3 / §2.20.2 / §3 Step 8 (P-3 advance, P-1 mark) / `tasks/070-260720-opd-태스크스텝-키주소-1차/PLAN.md` §3.6.2 (pipeline.json 전환)

> **행 구성 SSOT**: `references/pipeline.json` `task_steps[]`. 현재 행 목록은
> `~/.opal/tools/state-tool/run.sh show <task-path>` 또는 pipeline.json을 직접 조회한다.

> TASK.md 생성은 `task.task_md` 행에 흡수, ANALYSIS.md 생성은 `analysis.analysis_md` 행에 흡수, PLAN.md 생성은 `plan.plan_md` 행에 흡수, TEST-SCENARIO.md 생성은 `test_scenario.test_scenario_md` 행에 흡수. State Gate 성격의 판정은 개별 행이 아니라 state-tool stage-transition guard(PLAN §M-A)가 자동 수행한다 — 행으로 강제하지 않는다.
> **[MUST] `test_scenario.scenario_gate` 행(목표-커버 게이트)은 `op-scenario-gate` 스킬 반환 `verdict: pass`일 때만 mark한다** — PM이 산문 판단만으로 mark할 수 없으며, 이 행이 미완이면 stage-transition guard가 EXECUTE(`execute.implement`) 진입을 구조적으로 거부한다(073/F-005, R-5).
> TEST 루핑 발생 시: `~/.opal/tools/state-tool/run.sh add-row <task-path> --after 15 --stage TEST --item 'fix 작업 (N/3)'` 호출로 동적 추가한다 (P-6 추가작업 행 추가 패턴).

## PM Gate 점검 목록

> **게이트 정의 SSOT**: `references/pipeline.json` `task_steps[].gate` — 산출물(`artifacts`)과
> 체크리스트(`checklist`)는 이곳에만 정의한다. `state-tool mark --task-step <게이트 key>` 호출 시
> artifacts 존재를 도구가 검증하고(미충족 시 `gate_artifact_missing`으로 거부) checklist를
> stdout `gate_checklist` 페이로드로 반환한다. 각 Phase의 판정 절차·기준은 STEP 2(ANALYSIS)/STEP 3(PLAN)/STEP 3.5(TEST-SCENARIO)/STEP 5(TEST)의 "PM Gate" 절을 따른다.

---

## Agentic / Semi-Agentic 모드

opal-harness-agentic.md / opal-harness-semi-agentic.md 참조. 본 절은 이 스킬의 차이점만 기술한다.

### 기본 모드 (agentic)

무플래그 신규 호출(`//opd {작업}`·`//opds {작업}`)은 agentic 모드다(`harness/modes.md` §신규 태스크 기본 mode). 기존 태스크 재개는 저장 mode를 상속한다.

**semi-agentic 모드 경계** (`--semi-agentic` 명시 시, 이 시점부터 PM 자율):
- TEST-SCENARIO 사용자 확인 행 통과 후 → EXECUTE 작업 행부터 PM 자율

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//opd 작업` | agentic (신규 기본) — 정상 전 구간과 CLOSE final까지 PM 자율 |
| `//opd --semi-agentic 작업` | semi-agentic — TEST-SCENARIO-equivalent까지 사용자 검토 |
| `//opd --interactive 작업` | interactive — 모든 단계 사용자 승인 |

### 활성화

> **[MUST] agentic 모드 STATE 갱신**: 게이트 자율 통과 시 `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step <task-step-key> --done` 호출 (P-8). **사용자 확인 행은 PM이 명시 호출하지 않는다** — 다음 단계 진입 시 도구가 자동 승인한다. 계약 SSOT: `opal/core/references/opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`.
>
> **[MUST] CLOSE 전이**: `harness/modes.md` §CLOSE 전이 계약을 따른다. `semi-agentic`·`agentic`은 실제 미해결 이슈가 없으면 `test.user_confirm`을 자동 처리하고 `close.done_md`부터 `close.final`까지 계속한다. interactive만 `--owner user` 확인을 유지한다.
>
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §2.15 G-12 / §2.16 G-13 / §3 Step 8 P-8

### 자율 게이트 흐름 (`--semi-agentic` 명시 시)

```
TASK → ANALYSIS Gate → PLAN Gate → TEST-SCENARIO Gate → EXECUTE Gate → TEST Gate → CLOSE
사용자   사용자 승인     사용자 승인    사용자 승인              PM 자율        PM 자율     공통 CLOSE 계약
                                      (모드 경계)
```

- TASK→ANALYSIS→PLAN→TEST-SCENARIO Gate까지 사용자 승인 필수 (interactive 동작)
- TEST-SCENARIO 사용자 확인 행 통과 후 EXECUTE/TEST Gate는 PM 자율 통과
- EXECUTE 진입 = PM이 대행 승인 (구현 금지 원칙의 "실행 허가"를 PM이 판단)
- CLOSE는 공통 mode-aware 계약을 따른다 (`harness/modes.md` §CLOSE 전이 계약)
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- AGENTIC-LOG.md 생성: EXECUTE 등가 첫 행 advance/mark 시점

### CLOSE 전이 (공통)

행 키는 `close.done_md`와 `close.final`이다. 자동/대기 판정은 공통 SSOT를 따르며, `progress_report + continue`는 tail을 계속하고 실제 미해결 이슈만 대기한다 (`harness/modes.md` §CLOSE 전이 계약).

> **[MUST] actor 무관 유지**: CLOSE 전이는 `actor` 값(`coordinator`·`worker`·legacy `pm`)과 무관하게 같은 effective mode 판정을 적용한다. interactive/fail-closed는 `--owner user`를 유지하고 semi-agentic·agentic은 실제 미해결 이슈가 없으면 자동 진행한다. merge/push/deploy 등 별도 권한 경계는 `harness/guards.md` §커밋 규칙과 `harness/modes.md` §CLOSE 전이 계약을 따른다.

### AGENTIC-LOG.md 생성 시점

- agentic: TASK 시작 시점
- semi-agentic: EXECUTE-equivalent 첫 행 advance 시점에 PM이 생성

### 단계 보고 전이 계약

각 단계 행 mark/advance 직후 `state-tool` stdout의 `transition_action` / `report_type` / `next_action`을 소비한다. `report_type=progress_report`는 비차단 보고이며 `transition_action=continue`이면 같은 응답에서 다음 단계와 CLOSE tail로 이어간다. `report_type=decision_request`는 `transition_action=await_user|blocked`일 때만 사용한다.
