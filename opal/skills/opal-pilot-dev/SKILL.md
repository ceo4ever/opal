---
name: opal-pilot-dev
description: |
  **Full Task 오케스트레이터**. 대규모 개발 작업을 5단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-dev", "opd".
  코드를 읽기만 하는 설명 요청, API 명세서(api-analyzer), 기획 문서(opal-pilot-write-tech), PR 리뷰, git 작업, 단순 설정 변경은 이 스킬이 아니다.
---
# Full Task 오케스트레이터

## Harness
모드: Full Task (TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--interactive` 플래그 → `~/.opal/references/opal-harness-interactive.md`를 Read한다
- `--agentic` 플래그 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- 모드 플래그 없음 (기본) 또는 `--semi-agentic` → `~/.opal/references/opal-harness-semi-agentic.md`를 Read한다
- 다중 모드 플래그 동시 사용 시 즉시 사용자에게 보고 + state init도 거부 (`mode_flag_conflict`)

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

## STEP 1: TASK
opal-harness.md "TASK 공통 프로세스" 참조.

TASK 완료 → 사용자 보고.

> **[MUST] 행 갱신**: `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step <task-step-key> --done` 호출. **[MUST] 파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다.** 행을 mark하는 것 자체가 state 기록이며 별도의 State Gate 행은 존재하지 않는다.
> **단계 시작 (P-3)**: `~/.opal/tools/state-tool/run.sh advance <task-path> --task-step <task-step-key>` 호출로 해당 단계 작업 행을 🔄로 전환.
> **단계 건너뛰기 차단**: state-tool stage-transition guard가 단계 N의 필수 행이 완료되지 않으면 단계 N+1 진입(mark)을 자동 거부한다 (PLAN §M-A). 행에 의존하지 않는다.
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §1.5 M-11 / §3 Step 8 P-1 / P-3

## STEP 2: ANALYSIS
워커를 디스패치하여 코드베이스를 분석한다.

**디스패치 프롬프트**:
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
```
[WORKER]
op-dev-plan 스킬을 수행하라.
**스킬 경로**: {op-dev-plan/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}, {ANALYSIS.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {PLAN.md 경로}, {execution-plan.json 경로 (FE/BE 시)}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식으로 원문 인용 필수 항목. 요약 허용 항목은 일반 목록}
```
**model**: advanced

> **목표계열 선작성 착수 (PLAN 병렬)**: 위 PLAN 워커 디스패치와 **동시에**, 알투(PM)+캡틴 페어가 TASK.md만으로 Block A(채택 관점 — 목표 문장 · 요구사항 R 전체 · 교체형 시 채택/잔존 기준)를 도출해 TEST-SCENARIO.md 초안을 선작성한다. PLAN.md를 읽지 않은 상태에서 도출하여 PLAN 관점 오염을 원천 차단한다. 초안은 별도 임시 파일 없이 TEST-SCENARIO.md 본문에 직접 쓰고 보강 대기 마커를 남긴다.
>
> 이 시점에 목표-커버 게이트를 호출하지 않으며 `test_scenario.*` 행을 advance/mark하지 않는다. 선작성 초안과 PLAN.md 설계의 불일치는 PLAN PM Gate 시점의 조기 경보로 취급하여 사용자 보고에 포함한다.
>
> 규칙 SSOT: 트랙 = `opal/core/references/harness/red-first.md` §1.6 / 절차 = `op-dev-test-scenario/references/test-scenario-guide.md` §작성 프로세스 Step 1 Block A / 게이트 호출 시점 = `opal/core/references/harness/scenario-gate.md` §4. 선작성은 opt-in이며 미착수 시 STEP 3.5에서 Block A·B를 연속 수행한다(결과 동등).

PLAN 완료
  → **PM Gate** (PLAN.md 직접 검증 — 점검 목록 참조):
    1. `{PLAN.md 경로}` Read — §4.2 실행 체크리스트, §5 QA 체크리스트, §리스크 가설 표 확인
    2. 검증 체크리스트:
       - [ ] TASK.md 요구사항 전체 커버 여부 (PLAN.md §1.2 기능 목록 대조)
       - [ ] PLAN.md §4.2 실행 체크리스트 완성도 (소속 F-ID, 완료 기준 명시)
       - [ ] PLAN.md §리스크 가설 표에 H-N 가설이 작성되어 있는가
       - [ ] 설계 피드백/리스크 섹션에 미해결 빈틈이 없는가
  → PM Gate 통과 후 해당 행을 단일 mark. 사용자에게 PLAN 보고. 승인 = TEST-SCENARIO 단계 진입 허가.

## STEP 3.5: TEST-SCENARIO

> **[MUST] RED-first**: TEST-SCENARIO 작성 시 RED-first 트랙 적용 여부를 판단하고 기재한다. 규칙 SSOT: `opal/core/references/harness/red-first.md`. 목표계열 선작성 트랙은 동 문서 §1.6.

작성자: **알투(PM) + 캡틴 페어** — 오케스트레이터가 직접 작성 (워커 디스패치 없음).
이 단계는 self-confirming 방지를 위해 PLAN 워커(opal-plan-agent)와 다른 작성자가 수행한다.

1. **Block B 보강** — 선작성 초안(STEP 3 병렬 착수분)이 있으면, PLAN.md §리스크 가설 표(H-N)와 §1.2 기능 목록(F-NNN)을 도출 입력에 추가해 루브릭 ③기능커버·④리스크커버를 보강한다. 보강은 추가만이 아니라 초안 시나리오의 **수정·삭제를 포함**한다(→ `test-scenario-guide.md` §작성 프로세스 Step 1 Block B). 선작성하지 않았으면 Block A·B를 연속 수행한다(결과 동등).
2. `op-dev-test-scenario/SKILL.md`의 "TEST-SCENARIO.md 통일 형식"을 따라 TEST-SCENARIO.md 작성
3. `test-scenario-guide.md`의 5단계 프로세스 적용 (Step 3 계층 결정 + Step 3-b 실행 방식 M1/M2/M3 결정)
4. **보강 완료 판정 3조건**(`test-scenario-guide.md` Step 1 "보강 완료 판정")을 충족 확인한 뒤 해당 행을 단일 mark (`~/.opal/tools/state-tool/run.sh mark <task-path> --task-step test_scenario.test_scenario_md --done` 호출 — P-1)
5. **목표-커버 게이트 (1회)**: 4의 보강 완료 이후에만 호출한다 — 선작성 시점 호출 금지(`scenario-gate.md` §4). `~/.opal/tools/state-tool/run.sh advance <task-path> --task-step test_scenario.scenario_gate` 호출 후, `op-scenario-gate` 스킬을 호출한다.
   - 탐색 경로: `{프로젝트}/.opal/skills/op-scenario-gate/SKILL.md` → `~/.opal/skills/op-scenario-gate/SKILL.md`
   - 입력: `task_folder`(태스크 폴더 경로), `producer_artifact`(`{task_folder}/TEST-SCENARIO.md`), `pilot: opd`, `iteration`(최초 호출 = 1)
   - 수신 `verdict: pass` → 게이트 행 mark (`~/.opal/tools/state-tool/run.sh mark <task-path> --task-step test_scenario.scenario_gate --done` — Step 3 tool-gated 두 증거 근거로만 mark, 산문 판단으로 mark 금지)
   - 수신 `verdict: rewrite` → PM+캡틴이 `gaps`를 반영해 TEST-SCENARIO.md 재작성 후 `iteration+1`로 op-scenario-gate 재호출 (루프, 게이트 행은 아직 mark하지 않음)
   - 수신 `verdict: escalate` → 사용자에게 에스컬레이션하고 자율 재시도하지 않음
   - `test_scenario.scenario_gate` 행 mark 시점은 보강 완료(4) 후 `verdict: pass` 수신 이후다.
6. 사용자에게 TEST-SCENARIO 보고 — 승인 = EXECUTE 시작 허가

> **사용자 확인 (P-5)**: 이 행은 **모드에 따라 주체가 다르다**.
> - 자동 승인 구간(agentic 전 구간 / semi-agentic의 EXECUTE-equivalent 이후) — **PM은 호출하지 않는다.**
>   다음 단계 진입 시 도구가 자동 승인한다. 계약 SSOT: `opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`.
> - 그 외(interactive 전 구간 / semi-agentic의 모드 경계 내) — 소유자에게 보고하고 승인 발화를 받은 뒤
>   `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step test_scenario.user_confirm --done --owner user --note '{owner_name} 확인: ...'` 호출.
> CLOSE 진입 전 이 행의 `owner=user` 여부를 도구가 자동 검증한다 (§2.16 G-13).
> 근거: `PLAN.md` §3 Step 8 P-1 / P-5 / §2.16 G-13 / `tasks/073-260723-opd-시나리오-목표커버리지-루프/PLAN.md` §3.5.2 (목표-커버 게이트 접합)

## STEP 4: EXECUTE

> **[MUST] RED-first**: EXECUTE 진입 전 RED 증거 확보, fix 루핑 중 테스트 불변. 규칙 SSOT: `opal/core/references/harness/red-first.md`.
> RED-first 트랙인 경우, EXECUTE(GREEN) 진입 전 `~/.opal/tools/state-tool/run.sh verify <task> --red-check` 게이트를 호출하여 RED 증거를 확인한다. fix 루핑 시 `--fix-mode --changed-files ... --test-globs ...`로 테스트 불변성을 검사한다.

워커를 디스패치하여 코드를 작성한다. **model**: standard.

### 4-1. 분배 디스패치 절차 (v3.2 신설)

1. **PLAN.md §4.2 실행 체크리스트 Read** — 각 Step의 `영역`·`agent` 필드를 확인한다.
2. **영역별 Step 묶음 생성** — 동일 agent(opal-fe-agent, opal-be-agent, opal-db-agent, opal-task-agent)가 배정된 Step을 하나의 배치로 묶는다.
3. **Phase 순서 순회** — PLAN.md §4.1 Phase 그룹핑에 따라 Phase별로:
   - Phase 내 독립 배치가 복수면 Agent 도구 병렬 호출
   - 순차 의존이 있으면 순차 호출
4. **각 배치마다 워커 디스패치** — 해당 agent로 op-dev-execute 워커 디스패치.
5. **폴백** — PLAN.md §4.2에 agent 필드가 없거나 "미지정"인 경우 `opal-task-agent` 단일 디스패치로 PLAN 전체를 처리한다.

### 4-2. 디스패치 프롬프트

```
[WORKER]
op-dev-execute 스킬을 수행하라.
**스킬 경로**: {op-dev-execute/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**checklist_source**: {PLAN.md 경로}, 섹션: 4.2 실행 체크리스트
**scenario_source**: {TEST-SCENARIO.md 경로}
**완료 기준**: checklist 100% + 담당 Step 매핑 L1/L2 시나리오 PASS (L3는 TEST 단계 위임)
**자가 점검 절차**: 코드 작성 → 시나리오 "실행 명령" 추출 → Bash 실행 → PASS 확인 → 완료 보고
**담당 Step**: {이 워커가 처리할 Step 번호 목록 — 예: 3, 5, 7}
**Scope 제한**: {agent 영역 — FE / BE / DB / 공통}. 영역 외 파일 수정 시 즉시 블로커 보고.
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식으로 원문 인용 필수 항목. 요약 허용 항목은 일반 목록}
```

> **에이전트별 자동 가이드 선택**: 워커는 op-dev-execute/SKILL.md의 매핑 테이블에 따라 자기 에이전트 이름으로 execute-specialist-guide.md 또는 execute-generalist-guide.md를 자동 Read한다. PM이 `applied_guide` 파라미터를 주입하지 않는다.

### 4-3. FE/BE 병렬 (agent 필드 기반)

PLAN.md §4.2의 agent 필드에 따라 FE/BE 배치를 구성한다:
- **Phase 내 FE·BE 배치가 독립적**이면 병렬 호출
- **순차 의존**(FE → BE 통합 등)이 있으면 순차 호출

**폴백**: agent 필드 없거나 execution-plan.json만 존재 시 기존 방식 유지:
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

### 5-0. L3 시나리오 협업 게이트

TEST 단계 진입 시 opal-test-agent 디스패치 전에:
1. TEST-SCENARIO.md에서 `[SUPERVISOR]` 마커 시나리오 식별
2. `[SUPERVISOR]` 시나리오 존재 시:
   - opal-test-agent를 L3 제외 모드로 디스패치 (L1/L2만 실행)
   - PM이 사용자에게 아래 표준 양식으로 요청
3. 사용자 응답 수신 후 결과를 TEST-SCENARIO.md에 기록
4. L3 시나리오 없으면 정상 디스패치 진행

**PM 표준 요청 양식**:
```
캡틴, [시나리오 S-N]은 사용자 협업 검증이 필요합니다.
요청 내용: {시나리오 조건 요약}
기대 결과: {기대 결과 요약}
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

op-dev-test-agent 워커 디스패치. TEST-SCENARIO.md 실행 + 결과 기록 + PASS/FAIL 판정.

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + TEST-SCENARIO.md 경로 + changed_files 전달.

워커 완료 → 행 mark.

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
→ PM Gate 통과 후 해당 행을 단일 mark. 사용자에게 완료 보고 후 CLOSE 단계 진입 승인 요청.

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

## STEP 6: CLOSE

모든 체크리스트 갱신 완료 확인 후 태스크를 마감한다.

1. DONE.md 생성 후 행 mark (`~/.opal/tools/state-tool/run.sh mark <task-path> --task-step close.done_md --done` 호출 — P-1). 행을 mark하는 것 자체가 state 기록이다.
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
   - `~/.opal/tools/worktree-tool/run.sh status --project-root <프로젝트 루트> --task <NNN>`으로 현재 상태를 조회해 보고한다.
   - **[MUST] 자동 제거하지 않는다.** CLOSE 시점에 미머지 커밋이 남아 있는 것이 정상이다 — 커밋·머지는 캡틴의 권한이며 PM이 대행하지 않는다.
   - 안내 문구: "worktree `{worktree_root}`는 **머지 대기** 상태입니다. 머지·PR 처리 후 `~/.opal/tools/worktree-tool/run.sh remove --project-root <루트> --task <NNN>`으로 회수하세요."
   - `status` 호출 실패·메타 부재·worktree 부재는 전부 **no-op** — op-brain-ingest(스텝 3)·회고(스텝 4)와 동일하게 **CLOSE를 중단시키지 않는다**.
6. 완료 보고

> **CLOSE 진입 게이트 자동 검증**: CLOSE 단계 첫 행 mark 시 도구가 직전 단계 사용자 확인 행의 `owner=user` 여부를 자동 검증한다. 미통과 시 `close_gate_violation` 에러 반환 — agentic 모드의 `--auto-pass`도 거부됨 (§2.16 G-13 / PLAN §3 Step 8 P-8).
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

> **[MUST] STATE.md 초기 생성**: `~/.opal/tools/state-tool/run.sh init <task-path> --skill opd --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-dev/references/pipeline.json` 호출. 기본값: `semi-agentic`. 행 구성 SSOT는 `references/pipeline.json`(task-step key 포함) — `--rows-from`이 확장자로 분기해 파싱한다(070).
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

### 기본 모드 (semi-agentic)

기본 호출(`//opd {작업}`)은 semi-agentic 모드. TEST-SCENARIO-equivalent까지 사용자 검토, EXECUTE-equivalent 이후 PM 자율, CLOSE 진입은 사용자 승인 필수.

**모드 경계** (이 시점부터 PM 자율):
- TEST-SCENARIO 사용자 확인 행 통과 후 → EXECUTE 작업 행부터 PM 자율

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//opd 작업` | semi-agentic (기본) |
| `//opd --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//opd --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

### 활성화

> **[MUST] agentic 모드 STATE 갱신**: 게이트 자율 통과 시 `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step <task-step-key> --done` 호출 (P-8). **사용자 확인 행은 PM이 명시 호출하지 않는다** — 다음 단계 진입 시 도구가 자동 승인한다. 계약 SSOT: `opal/core/references/opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`.
>
> **[MUST] CLOSE 진입 게이트 거부 정책 (P-8 / §2.16 G-13)**: CLOSE 단계 첫 행은 `--auto-pass` 거부(`agentic_close_gate_requires_user` 에러). agentic/semi-agentic 모드라도 CLOSE 진입 직전 소유자에게 보고 후 사용자 발화("확인"/"승인")를 받아 직전 단계 사용자 확인 행을 `--owner user`로 mark한 뒤 CLOSE 첫 행을 진행한다.
>
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §2.15 G-12 / §2.16 G-13 / §3 Step 8 P-8

### 자율 게이트 흐름 (semi-agentic)

```
TASK → ANALYSIS Gate → PLAN Gate → TEST-SCENARIO Gate → EXECUTE Gate → TEST Gate → CLOSE
사용자   사용자 승인     사용자 승인    사용자 승인              PM 자율        PM 자율     사용자 승인 필수
                                      (모드 경계)
```

- TASK→ANALYSIS→PLAN→TEST-SCENARIO Gate까지 사용자 승인 필수 (interactive 동작)
- TEST-SCENARIO 사용자 확인 행 통과 후 EXECUTE/TEST Gate는 PM 자율 통과
- EXECUTE 진입 = PM이 대행 승인 (구현 금지 원칙의 "실행 허가"를 PM이 판단)
- CLOSE 진입은 사용자 승인 필수 (공통 게이트)
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- AGENTIC-LOG.md 생성: EXECUTE 등가 첫 행 advance/mark 시점

### CLOSE 진입 게이트 (공통)

semi-agentic / agentic 모두 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`). 소유자 발화 후 직전 사용자 확인 행 `--owner user` mark 필수.

### AGENTIC-LOG.md 생성 시점

- agentic: TASK 시작 시점
- semi-agentic: EXECUTE-equivalent 첫 행 advance 시점에 PM이 생성

## 변경이력
| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — dev-task-pilot 컴포지션 전환 |
| v1.1 | 2026-03-28 | TEST-SCENARIO를 TODO STEP에 통합, EXECUTE 후 커밋 규칙 추가 |
| v1.2 | 2026-03-28 | TODO를 PLAN에 흡수하여 5→4 STEP, TEST-SCENARIO를 PLAN STEP에 통합, TEST-SCENARIO 스킵 조건 추가 |
| v1.3 | 2026-03-28 | Harness 참조 전환으로 슬림화 (265→105줄) |
| v1.4 | 2026-03-29 | 컴포넌트 리네이밍 (042) |
| v1.5 | 2026-03-29 | model override를 레벨 기반으로 전환 (044) |
| v1.6 | 2026-03-31 | Agentic Mode 섹션 추가 (057) |
| v1.7 | 2026-03-31 | §7 참조 → opal-harness-agentic.md 참조 전환. EXECUTE 후 PM Gate + QA 체크리스트 갱신 추가 (058) |
| v1.8 | 2026-04-01 | 전체 워커 디스패치 프롬프트에 `[WORKER]` 마커 + 하네스 Guards + 참조 문서 주입 지침 추가 (063) |
| v1.9 | 2026-04-02 | PLAN PM Gate에 TASK.md 체크박스 갱신 명시 (072) |
| v2.0 | 2026-04-05 | QA Gate에 체크리스트 갱신 포함 + PM Gate에 갱신 상태 확인 + QA 재소환 절차 추가 (085) |
| v2.1 | 2026-04-05 | EXECUTE 후 추가작업 참조 가이드 추가 — 하네스 §3 추가작업 프로세스 (087) |
| v2.2 | 2026-04-07 | TASK/ANALYSIS/PLAN/EXECUTE 각 단계 Gate 순서에 State Gate 추가 (094) |
| v2.3 | 2026-04-07 | State Gate를 PM Gate 전 1개 → 각 Gate 직후로 재배치 (097) |
| v2.4 | 2026-04-08 | TEST-SCENARIO를 Gates 앞으로 이동 + TEST 단계 공식화 + TEST 루핑 구현 (100) |
| v2.5 | 2026-04-09 | STATE.md 도메인 설정 — 진행 현황 행 예시에 산출물 생성 행 추가 (101) |
| v2.6 | 2026-04-10 | ANALYSIS Gate 슬림화 — QA·PM Gate 제거, State Gate + Artifact Gate만 유지. PLAN QA 범위 확대 — ANALYSIS.md 포함 통합 검토 (107) |
| v2.7 | 2026-04-10 | Artifact Gate 제거 + PM Gate 점검 목록 섹션 추가 + 파이프라인 현황판 이름 변경 (106) |
| v2.8 | 2026-04-11 | PM Gate 점검 목록 — PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108) |
| v2.9 | 2026-04-13 | STEP 3에서 TEST-SCENARIO 별도 디스패치 + QA Gate 제거. PLAN 워커가 TEST-SCENARIO.md 통합 작성. PM Gate에 PLAN.md+TEST-SCENARIO.md Read + 검증 체크리스트 추가. STEP 5 TEST QA Gate 제거, PM Gate에 TEST-SCENARIO.md Read + 검증 체크리스트 추가. Agentic Mode 흐름도 갱신. STATE.md 행 예시 31→24행 갱신 (115) |
| v3.0 | 2026-04-15 | ANALYSIS/PLAN/EXECUTE 디스패치 프롬프트에 `**핵심 제약**:` 필드 추가 — `[MUST] <문서명> §N: <인용문>` 원문 인용 포맷 명시 (120) |
| v3.1 | 2026-04-15 | STEP 6 CLOSE 단계 신설 + TEST PM Gate 후 State Gate/사용자 확인 추가 + 진행 현황 행 CLOSE 2행 구조 반영 + 보고 형식 C안 적용 (121) |
| v3.2 | 2026-04-23 11:39 | STEP 4 EXECUTE에 PLAN.md §4.2 agent 필드 기반 분배 디스패치 절차 추가 — FE/BE 병렬 섹션 agent 필드 기반 일반화·담당 Step/Scope 제한 필드 추가·execution-plan.json 폴백 유지 (129) |
| v3.3 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
| v3.4 | 2026-05-01 | state-tool 도입 — STATE.md 직접 편집 금지 + `state-tool` 호출 표현 교체 (P-1~P-8 패턴 적용). "STATE.md 도메인 치환값" SSOT 보존 + `--rows-from` 파싱 SSOT 명시. agentic 활성화에 `--auto-pass` + CLOSE 진입 게이트 거부 정책(§2.16 G-13) 추가 (134) |
| v3.5 | 2026-05-08 | PM Gate 점검 목록 TEST 행 산출물에 GC-CONVENTION-*.md 추가 + STEP 5 TEST PM Gate 검증 체크리스트에 6번째 항목 '컨벤션 자동 진단 PASS' 신설 (136) |
| v3.6 | 2026-05-09 11:22 | 3-way 모드 체계 도입 — semi-agentic 기본 채택 + Agentic/Semi-Agentic 모드 절 확장 + Harness 절 3-way 분기 + state init choices 갱신 (140) |
| v3.7 | 2026-05-09 18:30 | 개인 식별자 "캡틴" → "소유자"/"사용자" 치환 — 배포 파일 정체성 누설 정정 (139) |
| v3.8 | 2026-05-15 16:40 | 5단계 파이프라인 재편 — STEP 3.5 TEST-SCENARIO 신설(PM 직접 작성, self-confirming 방지) + PLAN에서 TEST-SCENARIO.md 생성 제거 + STATE.md 28행 구조 갱신 + 모드 경계 이동(PLAN→TEST-SCENARIO) + 자율 게이트 흐름도 갱신 + EXECUTE 디스패치 scenario_source·완료기준·자가점검 필드 추가 + PM Gate TEST-SCENARIO Phase 행 추가 + STEP 5 L3 협업 게이트 신설 (004) |
| v3.9 | 2026-05-19 17:05 | PM Gate TEST-SCENARIO 행 체크리스트 7항목으로 확장 (⑦ 실행 방식 명시) + STEP 3.5 절차에 M1/M2/M3 결정 명시 (004 추가작업) |
| v4.0 | 2026-06-07 | STATE 행 재구성 — State Gate 행 제거(guard 이전)+QA Gate 행 제거(PM Gate 통합)+산출물 행 흡수+gate-pass→단일 mark (014 Phase 4) |
| v4.1 | 2026-06-10 10:13 | STEP 3.5/4에 RED-first 참조 + RED 게이트 절차 (016) |
| v4.2 | 2026-06-11 19:25 | STEP 6 CLOSE에 op-brain-ingest 디스패치 훅 삽입 — DONE.md 생성 직후 brain 존재 시 태스크 산출물 누적, brain 부재 시 no-op, 어떤 status도 CLOSE 비중단 (016-brain, 별도 PC 016과 중복 채번) |
| v4.3 | 2026-06-24 | CLOSE 단계 op-brain-ingest 디스패치 직전에 "관련 문서 업데이트" 스텝 삽입 — PROJECT.md 레지스트리 + changed_files 종합으로 관련 문서 최신화 후 ingest (없으면 no-op). 후속 항목 번호 재정렬 (042) |
| v4.4 | 2026-07-10 13:12 | note 예시(산문)의 소유자 확인 표기를 `{owner_name} 확인:` 형식으로 통일 — identity.md owner_name 재해석 규칙(AGENT.md §정체성 적용)과 정합, 오염 차단 (054) |
| v4.5 | 2026-07-17 13:05 | STEP 2 ANALYSIS 워커 model 레벨 상향 — light → standard (소유자 지시, L2) |
| v4.6 | 2026-07-17 | STEP 6 CLOSE에 "회고(개선 루프) 하드스텝" 삽입 — op-brain-ingest 직후·완료보고 직전, 궤적 신호→관찰/분류/기록(improve-tool record --scope local\|fw), 개선후보 0건 시 no-op 비차단(brain-ingest 패턴 답습) (058) |
| v4.7 | 2026-07-20 15:45 | task-step 키 주소 체계 도입 — `references/pipeline.json` 신설(15 task-step, SSOT), `--rows-from` 호출 경로를 SKILL.md에서 pipeline.json으로 교체(`.md` 파싱은 하위호환 폴백으로 존치), 표는 사람 열람용 미러로 축소 (070) |
| v4.8 | 2026-07-23 | STEP 3.5 목표-커버 게이트 접합 — `references/pipeline.json`에 `test_scenario.scenario_gate` 행 신설(id 10, 이후 11~16 재부여, 15→16 task-step), TEST-SCENARIO.md 작성 mark 후 `op-scenario-gate` 스킬 호출 절차 배선(verdict pass만 게이트 행 mark, rewrite=재작성 루프, escalate=사용자 에스컬레이션), 사람 열람 미러 표 16행 갱신 + 게이트 mark 조건 주석 추가. state-tool 소스 무변경(pipeline.json만 편집) (073) |
| v4.8 | 2026-07-23 09:56 | 본문 state-tool 명령 예시를 task-step key 주소로 전환(--row→--task-step, --step→--action-step). pipeline.json key 기준. (070 후속) |
| v4.9 | 2026-08-14 09:23 | pipeline.json 중복 정리 — STATE.md 진행 현황 미러 표 삭제 + 산문 `행 N` 참조를 task-step key로 전환, 모드·단계 목록 표 제거(meta 중복), PM Gate 점검 목록 표를 `references/pipeline.json` `task_steps[].gate` SSOT 포인터로 교체 (091) |
| v5.0 | 2026-08-15 16:30 | STEP 6 CLOSE에 "worktree 정리 안내" 스텝 삽입 — `--worktree`/`--wt` 태스크에서만 `worktree-tool status` 조회 결과를 근거로 "머지 대기" 안내(자동 제거하지 않음), 미사용 태스크는 no-op 비차단(op-brain-ingest·회고와 동일 패턴). 기존 "5. 완료 보고"를 6으로 재조정 (092) |
| v5.1 | 2026-08-15 21:48 | 사용자 확인 행 자동 승인 계약 반영 — agentic STATE 갱신 지시에서 PM `--auto-pass` 명시 호출 삭제, 다음 단계 진입 시 도구 자동 승인으로 전환하고 계약 본문은 하네스 SSOT(`opal-harness-agentic.md §4` / `opal-harness-semi-agentic.md §5`) 참조로 정리. CLOSE 진입 게이트 서술 불변 (093) |
| v5.2 | 2026-08-16 13:30 | 사용자 확인 (P-5) 3건(analysis/test_scenario/test) 산문을 모드 무분기 명령형 → 모드 분기 서술로 교체 — 자동 승인 구간(agentic 전 구간 / semi-agentic EXECUTE-equivalent 이후)은 PM 미호출·도구 자동 승인, 그 외 구간은 기존 mark 호출 유지. 지점별 --task-step 키·근거 인용 보존 (094 R-11 G-4). STEP 1 "[MUST] 행 갱신" 서술의 표 전제("LLM이 STATE.md 마크다운 표를 직접 편집하는 것은 금지된다")를 표준 문구 A("파이프라인 행 상태 변경은 `state-tool`로만 수행, `state.json` 직접 편집 금지, 조회는 `state-tool show`")로 치환 — STATE.md가 파생 표를 렌더하지 않는 저널로 재정의됨에 따른 정합(094 R-6/R-7, Step 8) |
| v5.3 | 2026-08-19 21:10 | STEP 3(PLAN) §3-1에 목표계열 선작성 병렬 착수 지시 + STEP 3.5 절차 1을 Block B 보강으로 재작성·4에 보강 완료 판정·5에 게이트 1회 전제 및 test_scenario.scenario_gate mark 시점 명시. STEP 2(ANALYSIS)·STEP 4(EXECUTE)·pipeline.json 무변경 (095) |
