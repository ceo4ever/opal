---
name: opal-pilot-dev-short
description: |
  **Short Task 오케스트레이터 (기본 모드)**. 코드 변경이 수반되는 모든 개발 작업의 기본 진입점. 3단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-dev-short", "opds".
  PLAN 단계에서 규모가 크다고 판단되면 Full Task(opal-pilot-dev) 에스컬레이션을 제안한다.
  코드를 읽기만 하는 설명 요청, API 명세서(api-analyzer), 기획 문서(opal-pilot-write-tech), PR 리뷰, git 작업, 단순 설정 변경은 이 스킬이 아니다.
---

# Short Task 오케스트레이터

## Harness
모드: Short Task (TASK → PLAN → EXECUTE → TEST → CLOSE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--interactive` 플래그 → `~/.opal/references/opal-harness-interactive.md`를 Read한다
- `--agentic` 플래그 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- 모드 플래그 없음 (기본) 또는 `--semi-agentic` → `~/.opal/references/opal-harness-semi-agentic.md`를 Read한다
- 다중 모드 플래그 동시 사용 시 즉시 사용자에게 보고 + state init도 거부 (`mode_flag_conflict`)

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

---

## STEP 1: TASK

harness "4. TASK 공통 프로세스" 참조. 다음 단계명: PLAN.

TASK 완료 → 사용자 보고.

> **[MUST] 행 갱신**: `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step <task-step-key> --done` 호출. **[MUST] 파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다.** 행을 mark하는 것 자체가 state 기록이며 별도의 State Gate 행은 존재하지 않는다.
> **단계 시작 (P-3)**: `~/.opal/tools/state-tool/run.sh advance <task-path> --task-step <task-step-key>` 호출로 해당 단계 작업 행을 🔄로 전환.
> **단계 건너뛰기 차단**: state-tool stage-transition guard가 단계 N의 필수 행이 완료되지 않으면 단계 N+1 진입(mark)을 자동 거부한다 (PLAN §M-A). 행에 의존하지 않는다.
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §1.5 M-11 / §3 Step 8 P-1 / P-3

---

## STEP 2: PLAN

> **[MUST] RED-first**: PLAN 단계에서 RED-first 트랙 적용 여부를 판단하고 TEST-SCENARIO.md에 기재한다. 규칙 SSOT: `opal/core/references/harness/red-first.md`. 목표계열 선작성 트랙은 동 문서 §1.6.

### PLAN 디스패치

op-dev-plan 워커 디스패치. **model**: advanced. 이전 산출물: TASK.md만 (ANALYSIS.md 없음).

> **Short Task는 단계를 줄이는 것이지, 분석을 줄이는 것이 아니다.** ANALYSIS.md 없이 호출되면 op-dev-plan이 코드 분석을 직접 수행한다. 분석 품질은 Full Task와 동일해야 한다.

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 주입 항목·핵심 제약(전 워커 공통 고정 포함)은 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿을 따른다 — 본 스킬은 항목을 열거하지 않는다.

### TEST-SCENARIO 작성 — 목표계열 선작성 → 보강 → 게이트 (3단계)

> op-dev-plan 워커는 PLAN.md만 작성한다(op-dev-plan/SKILL.md가 TEST-SCENARIO.md를 출력 범위에서 제외). TEST-SCENARIO.md는 **알투(PM) + 캡틴 페어**가 `op-dev-test-scenario/SKILL.md`의 "TEST-SCENARIO.md 통일 형식"(§1 리스크 가설 표 / §4 AC↔가설↔계층↔시나리오 매핑 표)을 명시 참조하여 직접 작성한다(self-confirming 방지 — PLAN 워커와 다른 작성자, opd STEP 3.5 동형). 문서 전용 작업 시 스킵(게이트도 자연 스킵).
>
> **규칙 SSOT** — 선작성 트랙: `opal/core/references/harness/red-first.md` §1.6 / 2계열 도출 절차: `op-dev-test-scenario/references/test-scenario-guide.md` §작성 프로세스 Step 1 / 게이트 호출 시점: `opal/core/references/harness/scenario-gate.md` §4. 본 절은 규칙을 재정의하지 않고 **순서만 배선**한다.

**(a) 선작성 착수 — PLAN 디스패치와 동시**
- 위 "PLAN 디스패치"와 **동시에** 착수한다. PLAN.md를 읽지 않은 상태에서 TASK.md만으로 Block A(채택 관점: 목표 문장 · 요구사항 R 전체 · 교체형 시 채택/잔존 기준)를 도출해 TEST-SCENARIO.md 초안을 작성한다.
- 초안은 별도 임시 파일 없이 TEST-SCENARIO.md 본문에 직접 쓰고, 보강 대기 지점에 마커를 남긴다(포맷: `test-scenario-guide.md` Step 1 Block A).
- 이 시점에 목표-커버 게이트를 호출하지 않으며 `plan.scenario_gate` 행을 advance/mark하지 않는다.

**(b) PLAN.md 수신 후 Block B 보강**
- PLAN.md의 F-NNN(§1.2)·H-N(§리스크 가설 표)을 도출 입력에 추가해 루브릭 ③기능커버·④리스크커버를 보강한다.
- 보강은 추가만이 아니라 **선작성 초안의 수정·삭제를 포함**한다. 선작성 초안과 PLAN 설계의 불일치는 PLAN PM Gate 시점의 조기 경보로 취급하여 사용자 보고에 포함한다.
- 보강 완료 판정 3조건(`test-scenario-guide.md` Step 1)을 충족시킨다.

**(c) 목표-커버 게이트 1회 호출**
- (b) 완료 후에만 호출한다 — (a) 시점 호출 금지(`scenario-gate.md` §4).
- `~/.opal/tools/state-tool/run.sh advance <task-path> --task-step plan.scenario_gate` 호출 후 `op-scenario-gate` 스킬을 호출한다.
  - 탐색 경로: `{프로젝트}/.opal/skills/op-scenario-gate/SKILL.md` → `~/.opal/skills/op-scenario-gate/SKILL.md`
  - 입력: `task_folder`(태스크 폴더 경로), `producer_artifact`(`{task_folder}/TEST-SCENARIO.md`), `pilot: opds`, `iteration`(최초 호출 = 1)
  - 수신 `verdict: pass` → 게이트 행 mark (`~/.opal/tools/state-tool/run.sh mark <task-path> --task-step plan.scenario_gate --done` 호출 — Step 3 coverage-check exit 0 AND Step 4 evaluator verdict pass 두 증거 근거로만 mark, 산문 판단으로 mark 금지)
  - 수신 `verdict: rewrite` → PM+캡틴이 `gaps`를 반영해 TEST-SCENARIO.md 재작성 후 `iteration+1`로 op-scenario-gate 재호출 (루프, 게이트 행은 아직 mark하지 않음)
  - 수신 `verdict: escalate` → 사용자에게 에스컬레이션하고 자율 재시도하지 않음
  - 문서 전용 작업 시(TEST-SCENARIO.md 스킵) 게이트도 자연 스킵
- `plan.scenario_gate` 행 mark 시점은 **(c)의 `verdict: pass` 수신 이후**다 — (a)·(b) 시점에는 mark하지 않는다.

PLAN 완료
  → **PM Gate** (PLAN.md + TEST-SCENARIO.md 직접 검증 — 점검 목록 참조):
    1. `{PLAN.md 경로}` Read — §4.2 실행 체크리스트, §5 QA 체크리스트 확인
    2. `{TEST-SCENARIO.md 경로}` Read — 시나리오 목록, 코드 품질, 보안 항목 확인 (스킵 시 해당 없음)
    3. 검증 체크리스트:
       - [ ] TASK.md 요구사항 전체 커버 여부 (PLAN.md §1.2 기능 목록 대조)
       - [ ] PLAN.md §4.2 실행 체크리스트 완성도 (소속 F-ID, 완료 기준 명시)
       - [ ] TEST-SCENARIO.md 시나리오가 TASK.md 요구사항 전체를 커버하는가
       - [ ] TEST-SCENARIO.md 보안 항목(시크릿 스캔, .gitignore) 포함 여부
       - [ ] 목표-커버 게이트 verdict: pass (스킵 시 해당 없음)
       - [ ] 설계 피드백 섹션에 미해결 빈틈이 없는가
       - [ ] 규모 기준 초과 시 Full Task 에스컬레이션 검토 여부
  → PM Gate 통과 후 해당 행(P-4, `plan.pm_gate`)을 단일 mark. 사용자에게 PLAN + TEST-SCENARIO 함께 보고. 승인 = EXECUTE 시작 허가.

> **사용자 확인 (P-5)**: 이 행은 **모드에 따라 주체가 다르다**.
> - 자동 승인 구간(agentic 전 구간 / semi-agentic의 EXECUTE-equivalent 이후) — **PM은 호출하지 않는다.**
>   다음 단계 진입 시 도구가 자동 승인한다. 계약 SSOT: `opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`.
> - 그 외(interactive 전 구간 / semi-agentic의 모드 경계 내) — 소유자에게 보고하고 승인 발화를 받은 뒤
>   `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step plan.user_confirm --done --owner user --note '{owner_name} 확인: ...'` 호출.
> CLOSE 진입 전 이 행의 `owner=user` 여부를 도구가 자동 검증한다 (§2.16 G-13).
> 근거: `PLAN.md` §3 Step 8 P-1 / P-5

---

## STEP 3: EXECUTE

> **[MUST] RED-first**: EXECUTE 진입 전 RED 증거 확보, fix 루핑 중 테스트 불변. 규칙 SSOT: `opal/core/references/harness/red-first.md`.
> RED-first 트랙(하이브리드 분기상 self-confirming 위험 작업)인 경우, EXECUTE(GREEN) 진입 전 `~/.opal/tools/state-tool/run.sh verify <task> --red-check` 게이트를 호출하여 RED 증거를 확인한다. fix 루핑 시 `--fix-mode --changed-files ... --test-globs ...`로 테스트 불변성을 검사한다.

### 3-1. 분배 디스패치 절차 (v3.1 신설)

1. **PLAN.md §4.2 실행 체크리스트 Read** — 각 Step의 `영역`·`agent` 필드를 확인한다.
2. **영역별 Step 묶음 생성** — 동일 agent(opal-fe-agent, opal-be-agent, opal-db-agent, opal-task-agent)가 배정된 Step을 하나의 배치로 묶는다.
3. **Phase 순서 순회** — PLAN.md §4.1 Phase 그룹핑에 따라 Phase별로:
   - Phase 내 독립 배치가 복수면 Agent 도구 병렬 호출
   - 순차 의존이 있으면 순차 호출
4. **각 배치마다 워커 디스패치** — 해당 agent로 op-dev-execute 워커 디스패치 (model: standard).
5. **폴백** — PLAN.md §4.2에 agent 필드가 없거나 "미지정"인 경우 `opal-task-agent` 단일 디스패치로 PLAN 전체를 처리한다.

### 3-2. 디스패치 프롬프트

```
[WORKER]
op-dev-execute 스킬을 수행하라.
**스킬 경로**: {op-dev-execute/SKILL.md 탐색 경로}
**태스크 폴더**: tasks/{NNN}-{태스크명}/
**checklist_source**: {PLAN.md 경로}, 섹션: 4.2 실행 체크리스트
**담당 Step**: {이 워커가 처리할 Step 번호 목록 — 예: 3, 5, 7}
**Scope 제한**: {agent 영역 — FE / BE / DB / 공통}. 영역 외 파일 수정 시 즉시 블로커 보고.
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식 원문 인용}
```

> **에이전트별 자동 가이드 선택**: 워커는 op-dev-execute/SKILL.md의 매핑 테이블에 따라 자기 에이전트 이름으로 execute-specialist-guide.md 또는 execute-generalist-guide.md를 자동 Read한다. PM이 `applied_guide` 파라미터를 주입하지 않는다.

### 3-3. EXECUTE 완료 후

모든 배치 완료 → changed_files 병합 → `execute.implement` 행 mark → **TEST 단계 진입**.

> **EXECUTE Step 완료 (P-4)**: 워커가 `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step execute.implement --done --as-worker --worker-stage EXECUTE --action-step <N/M>` 호출 (T-10 워커 권한 게이트).
> **블로커 발생 (P-7)**: `~/.opal/tools/state-tool/run.sh block <task-path> --task-step <task-step-key> --reason '...'` 호출.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-4 / P-7

---

## STEP 4: TEST

op-dev-test-agent 워커 디스패치. TEST-SCENARIO.md 실행 + 결과 기록 + PASS/FAIL 판정.

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 주입 항목·핵심 제약(전 워커 공통 고정 포함)은 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿을 따른다 — 본 스킬은 항목을 열거하지 않는다. 단계 추가 전달: TEST-SCENARIO.md 경로 · changed_files.

워커 완료 → `test.run_tests` 행 mark.

### PASS 시

→ **PM Gate** (TEST-SCENARIO.md 직접 검증):
  1. `{TEST-SCENARIO.md 경로}` Read — 시나리오 PASS/FAIL 전체 확인
  2. 검증 체크리스트:
     - [ ] TEST-SCENARIO.md 모든 시나리오 PASS
     - [ ] 코드 품질 항목(린트/타입/포맷) 모두 Pass
     - [ ] 보안 항목(시크릿 스캔/.gitignore) Pass
     - [ ] 회귀 테스트 항목 Pass
     - [ ] 설계 피드백 미해결 빈틈 없음
     - [ ] 컨벤션 자동 진단 PASS (changed_files 컨벤션 적용 대상 ≥1건 시 발동, GC-CONVENTION-*.md 보고서 Critical/High 0건)
→ PM Gate 통과 후 해당 행(`test.pm_gate`)을 단일 mark. 사용자에게 완료 보고 후 CLOSE 단계 진입 승인 요청.

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
다음 단계(CLOSE)로 넘어갈까요?
```

### FAIL 시 (루핑 — 최대 3회, 하네스 §1 L3a)

1. PM이 TEST-SCENARIO.md에서 FAIL 항목을 추출한다
2. op-dev-execute 워커 디스패치 (fix 모드):
   ```
   [WORKER]
   op-dev-execute 스킬을 수행하라 (fix 모드).
   **모드**: fix
   **fix 컨텍스트**:
     - 실패한 TEST-SCENARIO 항목: {FAIL 항목 목록}
     - 현재 시도 회차: {N}/3
     - 실패 요약: {op-dev-test-agent 결과 요약}
   **checklist_source**: PLAN.md 실행 체크리스트 (실패 항목 집중)
   **하네스 Guards**: fix 범위를 실패 항목으로 한정. 회귀 방지: 이전 PASS 항목 재실행.
   ```
3. fix 완료 → fix 행 mark → op-dev-test-agent 재호출 (루프)
4. 3회 초과 시 사용자 에스컬레이션:
   "TEST {N}회 FAIL — 수동 개입 필요. 실패 항목: {목록}"

---

## STEP 5: CLOSE

모든 체크리스트 갱신 완료 확인 후 태스크를 마감한다.

1. DONE.md 생성 후 `close.done_md` 행 mark (`~/.opal/tools/state-tool/run.sh mark <task-path> --task-step close.done_md --done` 호출 — P-1). 행을 mark하는 것 자체가 state 기록이다.
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
4. 완료 보고

> **CLOSE 진입 게이트 자동 검증**: CLOSE 단계 첫 행 mark 시 도구가 직전 단계 사용자 확인 행의 `owner=user` 여부를 자동 검증한다. 미통과 시 `close_gate_violation` 에러 반환 — agentic 모드의 `--auto-pass`도 거부됨 (§2.16 G-13 / PLAN §3 Step 8 P-8).
> **추가작업 진입 (P-6)**: `~/.opal/tools/state-tool/run.sh add-row <task-path> --after <N> --stage CLOSE --item '...'` 호출 → current_status 자동 `additional_work` 전환.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-6 / P-8 / §2.16 G-13

보고 형식:
```
✅ [CLOSE] 태스크 완료
📎 산출물: tasks/{NNN}-{태스크명}/DONE.md
태스크가 완료되었습니다.
```

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 추가작업 프로세스를 따른다.

---

## 에스컬레이션 규칙

### 조기 에스컬레이션 (TASK 완료 직후)

TASK.md 작성 완료 시점에서 아래 조건이 **명백히** 해당하면, PLAN 디스패치 전에 에스컬레이션을 제안한다:

| 조건 | 판별 방법 |
|------|----------|
| 요구사항 항목 >= 8개 | TASK.md 요구사항 체크박스 카운트 |
| 다중 모듈/서비스 명시 | TASK.md 배경/요구사항에 3개 이상 독립 모듈이 명시적으로 언급됨 |

> **주의**: 조기 에스컬레이션은 TASK.md만으로 **명백히** 판단 가능한 경우에만 적용한다. 불확실하면 PLAN을 진행하여 정확한 판별을 받는다.

> **참고**: 하향 강등(`opd`→`opds`)은 `opal/core/references/harness/track-routing.md`(SSOT)가 별도로 규정하며, 판정 시점이 TASK 직후(강등)/PLAN 결과(본 절 승격)로 분리되어 상호배타 — 아래 승격 규칙과 충돌하지 않는다.

### PLAN 결과 에스컬레이션 (기존)

op-dev-plan 결과에서 아래 조건이 감지되면 **Full Task(opal-pilot-dev) 전환을 제안**한다:

| 조건 | 판별 방법 |
|------|----------|
| 예상 변경 파일 >= 10개 | PLAN.md 파일 변경 계획에서 카운트 |
| 다단계 기술 의사결정 | 아키텍처 선택, 기술 스택 비교가 필요한 수준 |
| 다중 모듈 연쇄 영향 | 변경이 3개 이상 독립 모듈에 연쇄 영향 |

```
[에스컬레이션 제안]
이 작업은 Short Task 범위를 초과할 수 있습니다: {해당 조건}
Full Task(opal-pilot-dev)로 전환할까요?
- "Full로 해줘" -> Full Task 전환
- "Short로 진행해" -> Short Task 유지
```

---

## STATE.md 도메인 치환값

> **[MUST] STATE.md 초기 생성**: `~/.opal/tools/state-tool/run.sh init <task-path> --skill opds --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-dev-short/references/pipeline.json` 호출. 기본값: `semi-agentic`. 행 구성 SSOT는 `references/pipeline.json`(task-step key 포함) — `--rows-from`이 확장자로 분기해 파싱한다(070).
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §2.3 / §2.20.2 / §3 Step 8 (P-3 advance, P-1 mark) / `tasks/070-260720-opd-태스크스텝-키주소-1차/PLAN.md` §3.6.2 (pipeline.json 전환)

> **행 구성 SSOT**: `references/pipeline.json` `task_steps[]`. 현재 행 목록은
> `~/.opal/tools/state-tool/run.sh show <task-path>` 또는 pipeline.json을 직접 조회한다.

> TASK.md 생성은 `task.task_md` 행에 흡수, PLAN.md·TEST-SCENARIO.md 생성은 `plan.plan_md` 행에 흡수. State Gate 성격의 판정은 개별 행이 아니라 state-tool stage-transition guard(PLAN §M-A)가 자동 수행한다 — 행으로 강제하지 않는다. `plan.scenario_gate` 행(목표-커버 게이트)은 **[MUST]** `verdict: pass` tool-gated 증거로만 mark — 문서 전용 작업으로 TEST-SCENARIO.md가 스킵된 경우에만 자연 스킵, 그 외 산문 판단으로 mark 금지(guard가 미완 시 EXECUTE 진입을 구조적으로 차단).
> TEST 루핑 발생 시: `~/.opal/tools/state-tool/run.sh add-row <task-path> --after 10 --stage TEST --item 'fix 작업 (N/3)'` 호출로 동적 추가한다 (P-6 추가작업 행 추가 패턴).

---

## PM Gate 점검 목록

> **게이트 정의 SSOT**: `references/pipeline.json` `task_steps[].gate` — 산출물(`artifacts`)과
> 체크리스트(`checklist`)는 이곳에만 정의한다. `state-tool mark --task-step <게이트 key>` 호출 시
> artifacts 존재를 도구가 검증하고(미충족 시 `gate_artifact_missing`으로 거부) checklist를
> stdout `gate_checklist` 페이로드로 반환한다. 각 Phase의 판정 절차·기준은 STEP 2(PLAN)/STEP 4(TEST)의 "PM Gate" 절을 따른다.

---

## Agentic / Semi-Agentic 모드

opal-harness-agentic.md / opal-harness-semi-agentic.md 참조. 본 절은 이 스킬의 차이점만 기술한다.

### 기본 모드 (semi-agentic)

기본 호출(`//opds {작업}`)은 semi-agentic 모드. PLAN-equivalent까지 사용자 검토, EXECUTE-equivalent 이후 PM 자율, CLOSE 진입은 사용자 승인 필수.

**모드 경계** (이 시점부터 PM 자율):
- PLAN 사용자 확인 행 통과 후 → EXECUTE 작업 행부터 PM 자율

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//opds 작업` | semi-agentic (기본) |
| `//opds --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//opds --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

### 활성화

> **[MUST] agentic 모드 STATE 갱신**: 게이트 자율 통과 시 `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step <task-step-key> --done` 호출 (P-8). **사용자 확인 행은 PM이 명시 호출하지 않는다** — 다음 단계 진입 시 도구가 자동 승인한다. 계약 SSOT: `opal/core/references/opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`.
>
> **[MUST] CLOSE 진입 게이트 거부 정책 (P-8 / §2.16 G-13)**: CLOSE 단계 첫 행은 `--auto-pass` 거부. agentic/semi-agentic 모드라도 CLOSE 진입 직전 소유자에게 보고 후 사용자 발화를 받아 사용자 확인 행을 `--owner user`로 mark한 뒤 진행한다.
>
> 근거: `PLAN.md` §2.16 G-13 / §3 Step 8 P-8

### 자율 게이트 흐름 (semi-agentic)

```
TASK → PLAN Gate → EXECUTE Gate → TEST Gate → CLOSE
사용자   사용자 승인    PM 자율         PM 자율     사용자 승인 필수
         (모드 경계)
```

- PLAN Gate까지 사용자 승인 필수 (interactive 동작)
- PLAN 사용자 확인 행 통과 후 EXECUTE/TEST Gate는 PM 자율 통과
- CLOSE 진입은 사용자 승인 필수 (공통 게이트)
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- AGENTIC-LOG.md 생성: EXECUTE 등가 첫 행 advance/mark 시점

### CLOSE 진입 게이트 (공통)

semi-agentic / agentic 모두 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`). 소유자 발화 후 직전 사용자 확인 행 `--owner user` mark 필수.

### AGENTIC-LOG.md 생성 시점

- agentic: TASK 시작 시점
- semi-agentic: EXECUTE-equivalent 첫 행 advance 시점에 PM이 생성

### 에스컬레이션 규칙

에스컬레이션 규칙(Full Task 전환 제안)은 agentic/semi-agentic mode에서도 유지한다. PM이 판단하여 자동 전환하지 않고, 사용자에게 에스컬레이션으로 보고한다.

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 -- dev-task-pilot 컴포지션 전환 |
| v1.1 | 2026-03-28 | TEST-SCENARIO를 PLAN STEP에 통합, EXECUTE 후 커밋 규칙 추가 |
| v1.2 | 2026-03-28 | TEST-SCENARIO 문서 전용 스킵 조건 추가 |
| v1.3 | 2026-03-28 | harness 참조 슬림화 -- 공통 인프라를 opal-harness.md로 위임 |
| v1.4 | 2026-03-29 | 컴포넌트 리네이밍 (042) |
| v1.5 | 2026-03-29 | model override를 레벨 기반으로 전환 (044) |
| v1.6 | 2026-03-31 | Agentic Mode 섹션 추가 (057) |
| v1.7 | 2026-03-31 | §7 참조 → opal-harness-agentic.md 참조 전환. EXECUTE 후 PM Gate + QA 체크리스트 갱신 추가 (058) |
| v1.8 | 2026-04-01 | 전체 워커 디스패치 서술에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 (063) |
| v1.9 | 2026-04-02 | PLAN PM Gate에 TASK.md 체크박스 갱신 명시 (072) |
| v2.0 | 2026-04-04 | 에스컬레이션 규칙에 조기 에스컬레이션 (TASK 완료 직후) 조항 추가 (083) |
| v2.1 | 2026-04-05 | QA Gate에 체크리스트 갱신 포함 + PM Gate에 갱신 상태 확인 + QA 재소환 절차 추가 (085) |
| v2.2 | 2026-04-05 | EXECUTE 후 추가작업 참조 가이드 추가 — 하네스 §3 추가작업 프로세스 (087) |
| v2.3 | 2026-04-07 | TASK/PLAN/EXECUTE 각 단계 Gate 순서에 State Gate 추가 (094) |
| v2.4 | 2026-04-07 | State Gate를 PM Gate 전 1개 → 각 Gate 직후로 재배치 (097) |
| v2.5 | 2026-04-08 | TEST-SCENARIO를 Gates 앞으로 이동 + TEST 단계 공식화 + TEST 루핑 구현 (100) |
| v2.6 | 2026-04-09 | STATE.md 도메인 치환값 — 진행 현황 행 예시에 산출물 생성 행 추가 (101) |
| v2.7 | 2026-04-10 | Artifact Gate 제거 + PM Gate 점검 목록 섹션 추가 + 파이프라인 현황판 이름 변경 (106) |
| v2.8 | 2026-04-11 | PM Gate 점검 목록 — PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108) |
| v2.9 | 2026-04-13 | STEP 2에서 TEST-SCENARIO 별도 디스패치 + QA Gate 제거. PLAN 워커가 TEST-SCENARIO.md 통합 작성. PM Gate에 PLAN.md+TEST-SCENARIO.md Read + 검증 체크리스트 추가. STEP 4 TEST QA Gate 제거, PM Gate에 TEST-SCENARIO.md Read + 검증 체크리스트 추가. Agentic Mode 흐름도 갱신. STATE.md 행 예시 25→18행 갱신 (115) |
| v3.0 | 2026-04-15 | STEP 5 CLOSE 단계 신설 + TEST PM Gate 후 State Gate/사용자 확인 추가 + 진행 현황 행 CLOSE 2행 구조 반영 + 보고 형식 C안 적용 (121) |
| v3.1 | 2026-04-23 11:39 | STEP 3 EXECUTE에 PLAN.md §4.2 agent 필드 기반 분배 디스패치 절차 추가 — 영역별 Step 묶음·Phase 순서 순회·담당 Step/Scope 제한 필드 추가·agent 필드 없음 폴백 규칙 명시 (129) |
| v3.2 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
| v3.3 | 2026-05-01 | state-tool 도입 — STATE.md 직접 편집 금지 + `state-tool` 호출 표현 교체 (P-1~P-8 패턴 적용). "STATE.md 도메인 치환값" SSOT 보존 + `--rows-from` 파싱 SSOT 명시. agentic 활성화에 `--auto-pass` + CLOSE 진입 게이트 거부 정책 추가 (134) |
| v3.4 | 2026-05-08 | PM Gate 점검 목록 TEST 행 산출물에 GC-CONVENTION-*.md 추가 + STEP 4 TEST PM Gate 검증 체크리스트에 6번째 항목 '컨벤션 자동 진단 PASS' 신설 (136) |
| v3.5 | 2026-05-09 11:22 | 3-way 모드 체계 도입 — semi-agentic 기본 채택 + Agentic/Semi-Agentic 모드 절 확장 + Harness 절 3-way 분기 + state init choices 갱신 (140) |
| v3.6 | 2026-05-09 18:30 | 개인 식별자 "캡틴" → "소유자"/"사용자" 치환 — 배포 파일 정체성 누설 정정 (139) |
| v3.7 | 2026-06-07 | STATE 행 19→10 재구성 — State Gate 행 제거(guard로 이전)+산출물 행 흡수, gate-pass 제거 (014) |
| v3.8 | 2026-06-10 10:13 | STEP 2/3에 RED-first(red-first.md) 참조 + EXECUTE 진입 전 verify --red-check 게이트·fix 불변성 절차 (016) |
| v3.9 | 2026-06-11 19:25 | CLOSE 단계 DONE.md 생성 직후 op-brain-ingest 훅 삽입 — brain 존재 시 디스패치, 부재 시 no-op, CLOSE 비중단 (016-brain, 별도 PC 016과 중복 채번) |
| v4.0 | 2026-06-24 | CLOSE 단계 op-brain-ingest 디스패치 직전에 "관련 문서 업데이트" 스텝 삽입 — PROJECT.md 레지스트리 + changed_files 종합으로 관련 문서 최신화 후 ingest (없으면 no-op). 후속 항목 번호 재정렬 (042) |
| v4.1 | 2026-07-10 13:12 | note 예시(산문)의 소유자 확인 표기를 `{owner_name} 확인:` 형식으로 통일 — identity.md owner_name 재해석 규칙(AGENT.md §정체성 적용)과 정합, 오염 차단 (054) |
| v4.2 | 2026-07-20 15:45 | task-step 키 주소 체계 도입 — `references/pipeline.json` 신설(10 task-step, SSOT), `--rows-from` 호출 경로를 SKILL.md에서 pipeline.json으로 교체(`.md` 파싱은 하위호환 폴백으로 존치), 표는 사람 열람용 미러로 축소 (070) |
| v4.3 | 2026-07-23 09:56 | 본문 state-tool 명령 예시를 task-step key 주소로 전환(--row→--task-step, --step→--action-step). pipeline.json key 기준. (070 후속) |
| v4.4 | 2026-07-23 15:26 | STEP 2 producer를 op-dev-plan(PLAN.md만) → 알투(PM)+캡틴 페어 직접 작성(TEST-SCENARIO.md, opd STEP 3.5 동형)으로 확립 — op-dev-plan/SKILL.md 미접촉; PLAN 절차에 목표-커버 게이트(op-scenario-gate, pilot:opds) 호출 삽입; pipeline.json `plan.scenario_gate` 행 추가(10→11행) + STATE 미러 표·산문 "행 N" 전수 +1 재정렬; PM Gate checklist에 게이트 항목 추가 (075) |
| v4.5 | 2026-08-14 09:23 | pipeline.json 중복 정리 — STATE.md 진행 현황 미러 표 삭제 + 산문 `행 N` 참조를 task-step key로 전환, 모드·단계 목록 표 제거(meta 중복), PM Gate 점검 목록 표를 `references/pipeline.json` `task_steps[].gate` SSOT 포인터로 교체 (091) |
| v4.6 | 2026-08-15 21:48 | 사용자 확인 행 자동 승인 계약 반영 — agentic STATE 갱신 지시에서 PM `--auto-pass` 명시 호출 삭제, 다음 단계 진입 시 도구 자동 승인으로 전환하고 계약 본문은 하네스 SSOT(`opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`) 참조로 정리. CLOSE 진입 게이트 서술 불변 (093) |
| v4.7 | 2026-08-16 13:30 | 사용자 확인 (P-5) 2건(plan/test) 산문을 모드 무분기 명령형 → 모드 분기 서술로 교체 — 자동 승인 구간(agentic 전 구간 / semi-agentic EXECUTE-equivalent 이후)은 PM 미호출·도구 자동 승인, 그 외 구간은 기존 mark 호출 유지. 지점별 --task-step 키·근거 인용 보존 (094 R-11 G-4). STEP 1 "[MUST] 행 갱신" 서술의 표 전제("LLM이 STATE.md 마크다운 표를 직접 편집하는 것은 금지된다")를 표준 문구 A("파이프라인 행 상태 변경은 `state-tool`로만 수행, `state.json` 직접 편집 금지, 조회는 `state-tool show`")로 치환 — STATE.md가 파생 표를 렌더하지 않는 저널로 재정의됨에 따른 정합(094 R-6/R-7, Step 8) |
| v4.8 | 2026-08-19 21:10 | STEP 2에 목표계열 선작성 3단계 배선 — (a) PLAN 디스패치와 동시 선작성 착수 (b) PLAN.md 수신 후 Block B 보강(수정·삭제 포함) (c) 보강 완료 후 게이트 1회 호출 + `plan.scenario_gate` mark 시점 명시. 규칙 본문 0줄(SSOT 포인터만), pipeline.json·PM Gate 체크리스트 무변경 (095) |
| v4.9 | 2026-08-21 15:19 | §[PM 컨텍스트 주입] 블록 2건(PLAN·TEST 디스패치)을 `pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿 포인터로 일원화 — 주입 항목 열거(하네스 Guards·참조 문서·기술 스택 3항목)를 제거하고 SSOT 참조 1줄로 대체. 전 워커 공통 고정(git 이력 변경 금지 포함)이 파일럿 종류와 무관하게 도달하도록 함 (097) |
| v5.0 | 2026-08-21 22:15 | 에스컬레이션 규칙에 하향 강등(`opd`→`opds`) SSOT 포인터 1줄 추가 — `opal/core/references/harness/track-routing.md` 참조, 판정 시점 분리(강등=TASK 직후/승격=PLAN 결과)로 상호배타임을 명시. 승격 임계값 표·문장 무변경 (098) |
