---
name: opal-pilot-dev-wireframe
description: |
  **Wireframe UI 오케스트레이터**. 와이어프레임 설계부터 UI 구현까지 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-dev-wireframe", "opdw".
  "화면 구현", "UI 만들어줘", "화면 수정" 등 기존 프로젝트 기반 UI 작업은 opal-pilot-dev 또는 opal-pilot-dev-short에서 ui-designer plan-driven 모드로 수행한다.
---

# Wireframe UI 오케스트레이터

## Harness
모드: Wireframe UI (TASK → WIREFRAME → EXECUTE → CLOSE)
**[MUST — pilot.start 이벤트 게이트]** 파일럿의 첫 작업 전에 아래 순서를 수행한다.

1. `~/.opal/tools/event-loader/run.sh load --event pilot.start > <pilot-receipt-path>`를 호출한다.
2. load 응답의 `documents[].content` 전문을 모두 현재 컨텍스트에 적용하고, `modes` 문서가 현재 플래그에 대해 라우팅한 서브 하네스 전문 하나만 Read한다.
3. `~/.opal/tools/state-tool/run.sh event-verify --event pilot.start --receipt <pilot-receipt-path>`가 성공한 뒤에만 진행한다.

**[MUST — 단계 이벤트 게이트]** 각 실제 단계의 첫 작업이나 `state-tool advance` 직전에 아래 매핑의 이벤트를 load하고, 응답 문서 전문을 적용한 뒤 같은 event id로 `state-tool event-verify`를 통과해야 한다.

| 실제 단계 | 이벤트 |
|---|---|
| TASK | stage.task |
| WIREFRAME | stage.plan |
| EXECUTE | stage.execute |
| CLOSE | stage.close |

호출 형식은 `~/.opal/tools/event-loader/run.sh load --event <stage.*> > <stage-receipt-path>` 다음
`~/.opal/tools/state-tool/run.sh event-verify --event <stage.*> --receipt <stage-receipt-path>`이다.
문서 집합은 `events.json`만 SSOT로 사용하며 SKILL에 파일 목록을 복제하지 않는다. load 실패,
필수 문서 누락, stale receipt, wrong-event receipt는 해당 파일럿·단계 진입을 즉시 중단하는
blocker다. 부트 캐시를 근거로 공통 문서를 직접 재Read하는 우회는 금지한다.

---

## 입력물에 따른 분기

| 입력물 상태 | 판별 방법 | 다음 단계 |
|------------|----------|----------|
| wireframe.md 존재 | 파일 존재 확인 | WIREFRAME 스킵 → EXECUTE |
| 정책서/요구사항 문서 | .md/.txt/.pdf/.docx 파일 | WIREFRAME |
| 이미지(스케치/스크린샷) | .png/.jpg 파일 | WIREFRAME |
| 구두 요청만 | 파일 없음 | interview → WIREFRAME |

---

## STEP 1: TASK (Wireframe 특화)

Harness "TASK 공통 프로세스"를 따르되, 아래를 추가:
- 기술 환경 (React/Next.js 버전, shadcn/ui 여부)
- 출력 모드: 프로토타입(bundle.html) vs 프로덕션(Next.js)
- 입력물 분류 + wireframe.md 경로 (기존/생성 필요)
- 보고 시 입력물 분기 판별 결과 포함

TASK 완료 → 사용자 보고.

> **[MUST] 행 갱신**: `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step <task-step-key> --done` 호출. **[MUST] 파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다.** 행을 mark하는 것 자체가 state 기록이며 별도의 State Gate 행은 존재하지 않는다.
> **단계 시작 (P-3)**: `~/.opal/tools/state-tool/run.sh advance <task-path> --task-step <task-step-key>` 호출로 해당 단계 작업 행을 🔄로 전환.
> **단계 건너뛰기 차단**: state-tool stage-transition guard가 단계 N의 필수 행이 완료되지 않으면 단계 N+1 진입(mark)을 자동 거부한다 (PLAN §M-A). 행에 의존하지 않는다.
> **사용자 확인 (P-5)**: 이 행은 **모드에 따라 주체가 다르다**.
> - 자동 승인 구간(agentic 전 구간 / semi-agentic의 EXECUTE-equivalent 이후) — **PM은 호출하지 않는다.**
>   다음 단계 진입 시 도구가 자동 승인한다. 계약 SSOT: `opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`.
> - 그 외(interactive 전 구간 / semi-agentic의 모드 경계 내) — 소유자에게 보고하고 승인 발화를 받은 뒤
>   `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step task.user_confirm --done --owner user --note '{owner_name} 확인: TASK 완료'` 호출.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-3 / P-5

---

## STEP 2: WIREFRAME

> wireframe.md가 이미 존재하면 **스킵** → EXECUTE.

워커 디스패치로 wireframe.md 생성. **model**: standard.
- 스킬: op-dev-wireframe, 입력: TASK.md + 정책서/이미지
- 완료
  → **PM Gate** (TASK.md 요구사항 체크박스 갱신 + wireframe 직접 검증 — 점검 목록 참조):
    1. `{wireframe.md 경로}` Read — 화면 목록·요구사항 커버 확인
    2. 검증 체크리스트:
       - [ ] TASK.md 요구사항 전체 커버 여부 (wireframe.md 화면 대조)
       - [ ] 화면 구성 및 레이아웃의 완성도 (op-dev-qa/SKILL.md 와이어프레임 검증 기준 참조)
       - [ ] 설계 피드백 섹션에 미해결 빈틈이 없는가
       - [ ] TASK.md 요구사항 체크박스 갱신 완료
  → PM Gate 통과 후 해당 행을 단일 mark. 사용자에게 WIREFRAME 결과 보고.

state-tool 호출:

```
~/.opal/tools/state-tool/run.sh mark <task-path> --task-step wireframe.pm_gate --done  # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --task-step wireframe.user_confirm --done --owner user --note '{owner_name} 확인: WIREFRAME 완료'
```

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 주입 항목·핵심 제약(전 워커 공통 고정 포함)은 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿을 따른다 — 본 스킬은 항목을 열거하지 않는다.

---

## STEP 3: EXECUTE (UI 구현)

### 3-1. 라우팅 결정 (v2.2 신설)

와이어프레임 파이프라인의 EXECUTE는 **FE 단일 라우팅**을 사용한다 (분배 디스패치 대상 아님).

- **기본 에이전트**: `opal-fe-agent` (FE 전문)
- **근거**: wireframe.md에는 PLAN.md §4.2와 같은 agent 필드가 없다(op-dev-wireframe 산출물). 와이어프레임 구현은 본질적으로 FE 작업이므로 UI 전문 에이전트를 직접 지정한다.
- **폴백**: `opal-fe-agent` 사용 불가 플랫폼이면 `opal-task-agent`로 디스패치 (op-dev-execute/SKILL.md 매핑에 따라 generalist-guide로 폴백).

### 3-2. 디스패치 프롬프트

워커 디스패치로 wireframe.md 기반 UI 구현. **model**: standard.

```
[WORKER]
op-dev-execute 스킬을 수행하라.
**스킬 경로**: {op-dev-execute/SKILL.md 탐색 경로}
**태스크 폴더**: tasks/{NNN}-{태스크명}/
**checklist_source**: wireframe.md
**UI 구현 모드**: ui-designer scaffold(프로토타입) 또는 plan-driven(프로덕션)
**담당 Step**: wireframe.md 전체 (분배 없음)
**Scope 제한**: FE 영역. 영역 외 파일 수정 시 즉시 블로커 보고.
**하네스 Guards**: wireframe.md에 없는 화면 추가 금지. 설계 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식 원문 인용}
```

> **에이전트별 자동 가이드 선택**: `opal-fe-agent`로 라우팅되면 워커는 op-dev-execute/SKILL.md 매핑에 따라 execute-specialist-guide.md를 자동 Read한다.

### 3-3. 완료 후

1. **PM Gate** (빌드/린트 결과 + wireframe↔코드 대조 직접 검증 + 체크리스트 갱신 — 점검 목록 참조):
   1. `{wireframe.md 경로}` Read — wireframe.md 화면 목록 확인
   2. 변경 파일 코드 리뷰 — 빌드/린트 결과 및 코드 품질 확인
   3. 검증 체크리스트:
      - [ ] 빌드/린트 오류 없음 (op-dev-qa/SKILL.md EXECUTE-UI 검증 기준 참조)
      - [ ] wireframe.md 화면 목록 전체 구현 여부 (wireframe↔코드 대조)
      - [ ] 컨벤션 자동 진단 PASS (changed_files 컨벤션 적용 대상 ≥1건 시 발동, GC-CONVENTION-*.md Critical/High 0건)
      - [ ] TASK.md 요구사항 체크박스 갱신 완료
   → PM Gate 통과 후 해당 행을 단일 mark.
2. 사용자에게 완료 보고 후 CLOSE 단계 진입 승인 요청

state-tool 호출:

```
~/.opal/tools/state-tool/run.sh mark <task-path> --task-step execute.pm_gate --done  # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --task-step execute.user_confirm --done --owner user --note '{owner_name} 확인: EXECUTE 완료'
```

보고 형식:
```
📋 [EXECUTE] 완료 보고
📎 변경 파일: {changed_files}
📎 산출물: {GC-CONVENTION-*.md 등}
다음 단계(CLOSE)로 넘어갈까요?
```

---

## STEP 4: CLOSE

모든 체크리스트 갱신 완료 확인 후 태스크를 마감한다.

1. DONE.md 생성 후 close.done_md 행 mark (`~/.opal/tools/state-tool/run.sh mark <task-path> --task-step close.done_md --done` 호출 — P-1). 행을 mark하는 것 자체가 state 기록이다.
2. **관련 문서 업데이트** (op-brain-ingest 디스패치 직전 실행):
   - `<프로젝트-루트>/docs/PROJECT.md`의 "프로젝트 문서" 레지스트리와 이번 태스크의 `changed_files`(EXECUTE 산출)를 양쪽 종합하여, 태스크 결과로 내용이 달라진 관련 문서(ARCHITECTURE.md·기획서·와이어프레임 등)를 식별한다.
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

> **CLOSE 진입 게이트 자동 검증 (§2.16 G-13)**: CLOSE 단계 첫 행 mark 시 도구가 직전 단계 사용자 확인 행의 `owner=user` 여부를 자동 검증한다. 미통과 시 `close_gate_violation` 에러 반환 — agentic 모드의 `--auto-pass`도 거부됨.

> **추가작업 발생 시 (P-6)**: `~/.opal/tools/state-tool/run.sh add-row <task-path> --after 9 --stage CLOSE --item '추가 작업 항목'` 호출 → current_status 자동 `additional_work` 전환.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-6 / P-8 / §2.16 G-13

4. 완료 보고

보고 형식:
```
✅ [CLOSE] 태스크 완료
📎 산출물: tasks/{NNN}-{태스크명}/DONE.md
태스크가 완료되었습니다.
```

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 "추가작업 프로세스"를 따른다.

---

## STATE.md 도메인 치환값

Harness STATE.md 템플릿에 적용:
- `{산출물 목록}`: TASK.md, wireframe.md(기존 존재 가능), GC-CONVENTION-*.md, DONE.md

**진행 현황 행 예시** (아래 표는 사람 열람용 미러 — SSOT는 `references/pipeline.json`. `.md` 파싱은 하위호환 폴백으로만 존치, 편집 금지):

> **[MUST] STATE.md 초기 생성**: `~/.opal/tools/state-tool/run.sh init <task-path> --skill opdw --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-dev-wireframe/references/pipeline.json` 호출. 기본값: `semi-agentic`. 행 구성 SSOT는 `references/pipeline.json`(task-step key 포함, WIREFRAME 3~5행 `conditional:true`) — `--rows-from`이 확장자로 분기해 파싱한다(070). 행 데이터를 직접 편집하지 않는다.
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §2.3 / §2.20.2 / §3 Step 8 (P-3 advance, P-1 mark) / `tasks/070-260720-opd-태스크스텝-키주소-1차/PLAN.md` §3.6.2 (pipeline.json 전환)

> **행 구성 SSOT**: `references/pipeline.json` `task_steps[]`. 현재 행 목록은
> `~/.opal/tools/state-tool/run.sh show <task-path>` 또는 pipeline.json을 직접 조회한다.

> TASK.md 생성은 task.task_md 행에 흡수. wireframe.md 생성은 wireframe.wireframe_md 행에 흡수. State Gate 행은 state-tool stage-transition guard(PLAN §M-A)로 이전 완료 — 행으로 강제하지 않는다.
> WIREFRAME 스킵 시 (wireframe.md 기존 존재): WIREFRAME 단계 행(#3-#5)을 `-`로 표기한다.

---

## PM Gate 점검 목록

> **게이트 정의 SSOT**: `references/pipeline.json` `task_steps[].gate` — 산출물(`artifacts`)과
> 체크리스트(`checklist`)는 이곳에만 정의한다. `state-tool mark --task-step <게이트 key>` 호출 시
> artifacts 존재를 도구가 검증하고(미충족 시 `gate_artifact_missing`으로 거부) checklist를
> stdout `gate_checklist` 페이로드로 반환한다.

---

## Agentic / Semi-Agentic 모드

opal-harness-agentic.md / opal-harness-semi-agentic.md 참조. 본 절은 이 스킬의 차이점만 기술한다.

### 기본 모드 (semi-agentic)

기본 호출(`//opdw {작업}`)은 semi-agentic 모드. WIREFRAME(PLAN-equivalent)까지 사용자 검토, EXECUTE-equivalent 이후 PM 자율, CLOSE 진입은 사용자 승인 필수.

**모드 경계** (이 시점부터 PM 자율):
- WIREFRAME 사용자 확인 행 통과 후 → EXECUTE 작업 행부터 PM 자율

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//opdw 작업` | semi-agentic (기본) |
| `//opdw --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//opdw --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

### 활성화

STATE.md 모드 필드를 지정하여 기록한다 (기본: `semi-agentic`):

> STATE.md 초기 생성은 §STATE.md 도메인 치환값 참조.

### 자율 게이트 흐름 (semi-agentic)

```
TASK → WIREFRAME Gate → EXECUTE Gate → CLOSE
사용자   사용자 승인        PM 자율         사용자 승인 필수
         (모드 경계)
```

- WIREFRAME Gate까지 사용자 승인 필수 (interactive 동작)
- WIREFRAME 사용자 확인 행 통과 후 EXECUTE Gate는 PM 자율 통과
- CLOSE 진입은 사용자 승인 필수 (공통 게이트)
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- 자율 통과 시 `mark --task-step <task-step-key> --done` 호출 (P-8). 사용자 확인 행은 PM이 명시 호출하지 않으며 다음 단계 진입 시 도구가 자동 승인한다 (계약 SSOT: `opal/core/references/opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`)
- **CLOSE 단계 최초 진입 행은 `--auto-pass` 금지** (`agentic_close_gate_requires_user` — §2.16 G-13)
- AGENTIC-LOG.md 생성: EXECUTE 등가 첫 행 advance/mark 시점

### CLOSE 진입 게이트 (공통)

semi-agentic / agentic 모두 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`). 소유자 발화 후 직전 사용자 확인 행 `--owner user` mark 필수.

### AGENTIC-LOG.md 생성 시점

- agentic: TASK 시작 시점
- semi-agentic: EXECUTE-equivalent 첫 행 advance 시점에 PM이 생성

---
