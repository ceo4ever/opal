---
name: opal-pilot-project
description: |
  **프로젝트 범용 오케스트레이터**. 문서 작성, 간단한 코드 수정, 설정 변경, 워크플로우 수행 등 프로젝트의 모든 범용 태스크를 3단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-project", "opp".
  코드 개발 태스크는 opal-pilot-dev-short(opds)를, 기획 산출물 세트는 opal-pilot-write-tech(opwt)를 사용한다.
---

# opal-pilot-project (프로젝트 범용 오케스트레이터)

## Harness

모드: Project Task (TASK → PLAN → EXECUTE → CLOSE)
**[MUST — pilot.start 이벤트 게이트]** 파일럿의 첫 작업 전에 아래 순서를 수행한다.

1. `~/.opal/tools/event-loader/run.sh load --event pilot.start > <pilot-receipt-path>`를 호출한다.
2. load 응답의 `documents[].content` 전문을 모두 현재 컨텍스트에 적용하고, `modes` 문서가 현재 플래그에 대해 라우팅한 서브 하네스 전문 하나만 Read한다.
3. `~/.opal/tools/state-tool/run.sh event-verify --event pilot.start --receipt <pilot-receipt-path>`가 성공한 뒤에만 진행한다.

**[MUST — 단계 이벤트 게이트]** 각 실제 단계의 첫 작업이나 `state-tool advance` 직전에 아래 매핑의 이벤트를 load하고, 응답 문서 전문을 적용한 뒤 같은 event id로 `state-tool event-verify`를 통과해야 한다.

| 실제 단계 | 이벤트 |
|---|---|
| TASK | stage.task |
| PLAN | stage.plan |
| EXECUTE | stage.execute |
| CLOSE | stage.close |

호출 형식은 `~/.opal/tools/event-loader/run.sh load --event <stage.*> > <stage-receipt-path>` 다음
`~/.opal/tools/state-tool/run.sh event-verify --event <stage.*> --receipt <stage-receipt-path>`이다.
문서 집합은 `events.json`만 SSOT로 사용하며 SKILL에 파일 목록을 복제하지 않는다. load 실패,
필수 문서 누락, stale receipt, wrong-event receipt는 해당 파일럿·단계 진입을 즉시 중단하는
blocker다. 부트 캐시를 근거로 공통 문서를 직접 재Read하는 우회는 금지한다.

---

## STEP 1: TASK

harness "4. TASK 공통 프로세스" 참조. 다음 단계명: PLAN.

TASK 완료 → 사용자 보고.

> **[MUST] 행 갱신**: `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step <task-step-key> --done` 호출. **[MUST] 파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다.** 행을 mark하는 것 자체가 state 기록이며 별도의 State Gate 행은 존재하지 않는다.
> **단계 시작 (P-3)**: `~/.opal/tools/state-tool/run.sh advance <task-path> --task-step <task-step-key>` 호출로 해당 단계 작업 행을 🔄로 전환.
> **단계 건너뛰기 차단**: state-tool stage-transition guard가 단계 N의 필수 행이 완료되지 않으면 단계 N+1 진입(mark)을 자동 거부한다. 행에 의존하지 않는다.
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §1.5 M-11 / §3 Step 8 P-1 / P-3

---

## STEP 2: PLAN

워커를 디스패치하여 범용 실행 계획을 수립한다.

### PLAN 디스패치

op-task-plan 워커 디스패치. **model**: advanced. 이전 산출물: TASK.md.

탐색 경로:
1. `{프로젝트}/.opal/skills/op-task-plan/SKILL.md`
2. `~/.opal/skills/op-task-plan/SKILL.md`

PLAN 완료
  → **PM Gate** (PLAN.md 직접 검증 — 점검 목록 참조):
    1. `{PLAN.md 경로}` Read — §3 실행 체크리스트, §4 확인
    2. 검증 체크리스트:
       - [ ] TASK.md 요구사항 전체 커버 여부 (PLAN.md §1 기능 목록 대조)
       - [ ] PLAN.md §3 실행 체크리스트 완성도 (완료 기준 명시)
       - [ ] 설계 피드백 섹션에 미해결 빈틈이 없는가
  → PM Gate 통과 후 해당 행(`plan.pm_gate`)을 단일 mark. 사용자에게 PLAN 보고. 승인 = EXECUTE 시작 허가.

> **단계 시작 (P-3)**: `~/.opal/tools/state-tool/run.sh advance <task-path> --task-step <task-step-key>` 호출로 해당 단계 작업 행을 🔄로 전환.
> 근거: `PLAN.md` §3 Step 8 P-3

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 주입 항목·핵심 제약(전 워커 공통 고정 포함)은 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿을 따른다 — 본 스킬은 항목을 열거하지 않는다.

보고 형식:
```
📋 [PLAN] 완료 보고
📎 산출물: tasks/{NNN}-{태스크명}/PLAN.md
전이: {transition_action} / 보고: {report_type}
다음 액션: {next_action}
```

`report_type=decision_request`인 경우에만 소유자 결정을 기다린다. `progress_report`와 `transition_action=continue`이면 EXECUTE로 이어간다.

---

## STEP 3: EXECUTE

op-task-execute 워커 디스패치. **model**: standard. checklist_source: PLAN.md 섹션 "3. 실행 체크리스트".

탐색 경로:
1. `{프로젝트}/.opal/skills/op-task-execute/SKILL.md`
2. `~/.opal/skills/op-task-execute/SKILL.md`

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 주입 항목·핵심 제약(전 워커 공통 고정 포함)은 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿을 따른다 — 본 스킬은 항목을 열거하지 않는다.

### EXECUTE 완료 후

워커가 changed_files를 반환하면:
1. **PM Gate** (EXECUTE 결과 직접 검증 — 점검 목록 참조):
   - `{PLAN.md 경로}` Read — §3 실행 체크리스트 완료 여부 확인
   - 검증 체크리스트:
     - [ ] PLAN.md §3 실행 체크리스트 모든 항목 완료
     - [ ] 컨벤션 자동 진단 PASS (changed_files 컨벤션 적용 대상 ≥1건 시 발동, GC-CONVENTION-*.md 보고서 Critical/High 0건)
     - [ ] 설계 피드백 미해결 빈틈 없음
   → PM Gate 통과 후 해당 행(EXECUTE PM Gate)을 단일 mark.
2. 사용자에게 완료 보고 후 CLOSE 단계 진입 승인 요청

> **EXECUTE Step 완료 (P-4)**: 워커가 `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step execute.implement --done --as-worker --worker-stage EXECUTE --action-step <N/M>` 호출 (T-10 워커 권한 게이트).
> **사용자 확인 (P-5)**: 이 행은 **모드에 따라 주체가 다르다**.
> - 자동 승인 구간(agentic 전 구간 / semi-agentic의 EXECUTE-equivalent 이후) — **PM은 호출하지 않는다.**
>   다음 단계 진입 시 도구가 자동 승인한다. 계약 SSOT: `opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`.
> - 그 외(interactive 전 구간 / semi-agentic의 모드 경계 내) — 소유자에게 보고하고 승인 발화를 받은 뒤
>   `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step execute.user_confirm --done --owner user --note '{owner_name} 확인: ...'` 호출.
> CLOSE 진입 전 이 행의 `owner=user` 여부를 도구가 자동 검증한다 (§2.16 G-13).
> **블로커 발생 (P-7)**: `~/.opal/tools/state-tool/run.sh block <task-path> --task-step <task-step-key> --reason '...'` 호출. STATE.md 블로커 섹션 자유 텍스트는 PM이 별도 작성.
> **추가작업 진입 (P-6)**: `~/.opal/tools/state-tool/run.sh add-row <task-path> --after <N> --stage CLOSE --item '...'` 호출 → current_status 자동 `additional_work` 전환. 완료 시 `~/.opal/tools/state-tool/run.sh status <task-path> --set additional_work_done`.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-4 / P-5 / P-6 / P-7 / §2.16 G-13

보고 형식:
```
📋 [EXECUTE] 완료 보고
📎 변경 파일: {changed_files}
전이: {transition_action} / 보고: {report_type}
다음 액션: CLOSE 진입 승인이 필요하면 `decision_request`로 보고한다.
```

> TEST-SCENARIO 없음: 범용 작업은 코드 테스트가 불필요하다.

---

## STEP 4: CLOSE

모든 체크리스트 갱신 완료 확인 후 태스크를 마감한다.

1. DONE.md 생성 후 `close.done_md` 행 mark (`~/.opal/tools/state-tool/run.sh mark <task-path> --task-step close.done_md --done` 호출 — P-1). 행을 mark하는 것 자체가 state 기록이다.
2. **관련 문서 업데이트** (op-brain-ingest 디스패치 직전 실행):
   - `<프로젝트-루트>/docs/PROJECT.md`의 "프로젝트 문서" 레지스트리와 이번 태스크의 `changed_files`(EXECUTE 산출)를 양쪽 종합하여, 태스크 결과로 내용이 달라진 관련 문서(ARCHITECTURE.md·기획서 등)를 식별한다.
   - 갱신 대상이 있으면 PM이 판단하여 직접 수정하거나 적합한 워커를 디스패치해 최신화한다. 갱신 대상이 없으면 자연 스킵(no-op) — CLOSE를 중단시키지 않는다.
   - 목적: brain ingest 이전에 기획·설계 문서를 최신 상태로 만들어 ingest 품질을 보장한다.
3. **op-brain-ingest 디스패치** (PM Gate 통과 후, DONE.md 생성 직후 실행):
   - `<프로젝트-루트>/.opal/brain/` 존재 여부를 확인한다.
   - **brain이 존재하면**: op-brain-ingest 워커를 디스패치하여 태스크 산출물(DONE.md·PLAN 결정·신규 엔티티)을 brain에 누적한다. PM Gate 통과 후 실행하므로 검증된 산출물만 누적된다.
   - **brain이 없으면**: 자연 스킵(no-op). CLOSE가 막히지 않는다.
   - op-brain-ingest 탐색 경로:
     1. `{프로젝트}/.opal/skills/op-brain-ingest/SKILL.md`
     2. `~/.opal/skills/op-brain-ingest/SKILL.md`
   - 디스패치 입력: 태스크 폴더 경로
   - 워커가 `status: skipped` 또는 `status: completed` 또는 `status: completed_with_errors` 반환 — 어떤 경우도 CLOSE를 중단시키지 않는다.
4. 완료 보고

> **CLOSE 진입 게이트 자동 검증**: CLOSE 단계 첫 행 mark 시 도구가 직전 단계 사용자 확인 행의 `owner=user` 여부를 자동 검증한다. 미통과 시 `close_gate_violation` 에러 반환 — agentic 모드의 `--auto-pass`도 거부됨 (§2.16 G-13 / PLAN §3 Step 8 P-8).
> **추가작업 진입 (P-6)**: `~/.opal/tools/state-tool/run.sh add-row <task-path> --after <N> --stage CLOSE --item '...'` 호출 → current_status 자동 `additional_work` 전환.
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §2.16 G-13 / §3 Step 8 P-1 / P-6 / P-8

보고 형식:
```
✅ [CLOSE] 태스크 완료
📎 산출물: tasks/{NNN}-{태스크명}/DONE.md
태스크가 완료되었습니다.
```

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 "추가작업 프로세스"를 따른다.

---

## STATE.md 도메인 치환값

> **[MUST] STATE.md 초기 생성**: `~/.opal/tools/state-tool/run.sh init <task-path> --skill opp --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-project/references/pipeline.json` 호출. 기본값: `semi-agentic`. 행 구성 SSOT는 `references/pipeline.json`(task-step key 포함) — `--rows-from`이 확장자로 분기해 파싱한다(070).
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §2.3 / §2.20.2 / §3 Step 8 (P-3 advance, P-1 mark) / `tasks/070-260720-opd-태스크스텝-키주소-1차/PLAN.md` §3.6.2 (pipeline.json 전환)

> **행 구성 SSOT**: `references/pipeline.json` `task_steps[]`. 현재 행 목록은
> `~/.opal/tools/state-tool/run.sh show <task-path>` 또는 pipeline.json을 직접 조회한다.

> TASK.md 생성은 `task.task_md` 행에 흡수, PLAN.md 생성은 `plan.plan_md` 행에 흡수. State Gate 행·QA Gate 행·QA 산출물 행은 제거 — State Gate는 state-tool stage-transition guard(PLAN §M-A)로 이전 완료, QA Gate는 PM Gate에 흡수.

---

## PM Gate 점검 목록

> **게이트 정의 SSOT**: `references/pipeline.json` `task_steps[].gate` — 산출물(`artifacts`)과
> 체크리스트(`checklist`)는 이곳에만 정의한다. `state-tool mark --task-step <게이트 key>` 호출 시
> artifacts 존재를 도구가 검증하고(미충족 시 `gate_artifact_missing`으로 거부) checklist를
> stdout `gate_checklist` 페이로드로 반환한다. 각 Phase의 판정 절차·기준은 STEP 2(PLAN)/STEP 3(EXECUTE)의 "PM Gate" 절을 따른다.

---

## Agentic / Semi-Agentic 모드

opal-harness-agentic.md / opal-harness-semi-agentic.md 참조. 본 절은 이 스킬의 차이점만 기술한다.

### 기본 모드 (semi-agentic)

기본 호출(`//opp {작업}`)은 semi-agentic 모드. PLAN-equivalent까지 사용자 검토, EXECUTE-equivalent 이후 PM 자율, CLOSE 진입은 사용자 승인 필수.

**모드 경계** (이 시점부터 PM 자율):
- PLAN 사용자 확인 행(`plan.user_confirm`) 통과 후 → EXECUTE 작업 행(`execute.implement`)부터 PM 자율

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//opp 작업` | semi-agentic (기본) |
| `//opp --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//opp --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

### 활성화

> **[MUST] agentic 모드 STATE 갱신**: 게이트 자율 통과 시 `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step <task-step-key> --done` 호출. **사용자 확인 행은 PM이 명시 호출하지 않는다** — 다음 단계 진입 시 도구가 자동 승인한다. 계약 SSOT: `opal/core/references/opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`.
>
> **[MUST] CLOSE 진입 게이트 거부 정책 (P-8 / §2.16 G-13)**: CLOSE 단계 첫 행은 `--auto-pass` 거부(`agentic_close_gate_requires_user` 에러). agentic/semi-agentic 모드라도 CLOSE 진입 직전 소유자에게 보고 후 사용자 발화("확인"/"승인")를 받아 직전 단계 사용자 확인 행을 `--owner user`로 mark한 뒤 CLOSE 첫 행을 진행한다.
>
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §2.15 G-12 / §2.16 G-13 / §3 Step 8 P-8

### 자율 게이트 흐름 (semi-agentic)

```
TASK → PLAN Gate → EXECUTE Gate → CLOSE
사용자 승인  사용자 승인    PM 자율      사용자 승인 필수
            (모드 경계)
```

- PLAN Gate까지 사용자 승인 필수 (interactive 동작)
- PLAN 사용자 확인 행 통과 후 EXECUTE Gate는 PM 자율 통과
- CLOSE 진입은 사용자 승인 필수 (공통 게이트 — P-8 CLOSE 진입 게이트 거부 정책 적용)
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- AGENTIC-LOG.md 생성: EXECUTE 등가 첫 행 advance/mark 시점

### CLOSE 진입 게이트 (공통)

semi-agentic / agentic 모두 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`). 소유자 발화 후 직전 사용자 확인 행 `--owner user` mark 필수.

### AGENTIC-LOG.md 생성 시점

- agentic: TASK 시작 시점
- semi-agentic: EXECUTE-equivalent 첫 행 advance 시점에 PM이 생성

### 단계 보고 전이 계약

각 단계 행 mark/advance 직후 `state-tool` stdout의 `transition_action` / `report_type` / `next_action`을 소비한다. `report_type=progress_report`는 비차단 보고이며 `transition_action=continue`이면 같은 응답에서 다음 단계로 이어간다. `report_type=decision_request`는 `transition_action=await_user|blocked`일 때만 사용하고, CLOSE 진입 승인 예외는 유지한다.

---
