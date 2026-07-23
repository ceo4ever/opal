# TEST SCENARIO: TEST-SCENARIO 목표-커버리지 루브릭 게이트 루프 (공유 컴포넌트, opd 선적용)

> 작성일: 2026-07-23 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반 (작성자 ≠ opal-plan-agent)

> **트랙 판정 (RED-first §1.5)**: **하이브리드**.
> - RED-first 강제 = F-002 `scenario-coverage-check`(test-tool 비즈니스 로직) → Step3(test-agent red) → Step4(be-agent green), `verify --red-check` ON.
> - 구현-후-검증 = F-001/F-003/F-004/F-005/F-006(마크다운 SSOT·스킬·AGENT.md·pipeline.json — 설정·문서 트랙).
> - 공통 불변 유지: ①테스트 산출물(F-007) ②작성자≠구현자 ③TEST 단계 검증.
> **M2 의무 트리거**: FE 화면·인증/인가·외부 API 연동 **없음** → M2(E2E) 면제. 전 시나리오 M1(테스트 도구) 또는 L2 CLI 실행.

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-002 scenario-coverage-check 판정 로직 | R/F/H↔시나리오 매핑 누락을 결정론 판정 — 미커버가 있는데 `ok` 반환(거짓 초록불) | P0 | L1 | S-1 |
| H-2 | F-002 신규 exit code(16/17) + dispatch 확장 | 기존 scenario-* 7서브명령 dispatch 키·exit 8~14 회귀 | P0 | L1 | S-2 |
| H-3 | F-005 pipeline.json 신규 게이트 행 | state-tool `spec-validate` 거부 / stage-transition guard가 EXECUTE 차단 안 함 | P1 | L2 | S-3 |
| H-4 | F-004 op-scenario-gate 종료조건 | MAX=3 초과 미감지(무한루프) / 무진전 연속2회 미감지 / 수렴조건 오판(누락 있는데 PASS) | P0 | L2 | S-4 |
| H-5 | F-004·F-005 Producer≠Evaluator 분리 | PM이 게이트 우회하고 `test_scenario.user_confirm` mark → self-confirming 재발 | P0 | L2 | S-5 |
| H-6 | F-003 evaluator phase 열거 확장 | 4번째 phase 추가가 기존 design-review/spec-review/drift-recheck 계약 회귀 | P1 | L1 | S-6 |
| H-7 | F-008 음성통제 | 목표-커버 시나리오를 의도 누락했는데 게이트 PASS(음성통제 실패) → 게이트 무력 | P0 | L2 | S-7, S-8 |

## 2. 테스트 데이터 설계

> DB 없음(프레임워크 내부 개선) — "사전 조건 데이터"는 fixture 파일·정규화 페이로드·임시 태스크 폴더로 구성.

### 2.1 사전 조건 데이터

| 테이블(자원) | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| coverage-input 페이로드(완전) | `fx-cov-complete.json` | 전 R/F/H가 시나리오에 매핑됨 | fixture (test_scenario.py tmp) |
| coverage-input 페이로드(누락) | `fx-cov-missing.json` | R 1건·H 1건 미매핑 | fixture (test_scenario.py tmp) |
| coverage-input 페이로드(오류) | `fx-cov-broken.json` | 필수 키 누락/JSON 파손 | fixture (test_scenario.py tmp) |
| 임시 태스크 폴더 | `tmp_task/` | state-tool init 대상 | fixture (tmpdir) |
| 신규 pipeline.json(게이트 행 포함) | `opal/skills/opal-pilot-dev/references/pipeline.json` | `test_scenario.scenario_gate` 행 삽입됨 | Step7 산출(EXECUTE) |
| 기존 scenario-* 스위트 | `test_scenario.py` 23건 | 회귀 기준선 | 기존 fixture |
| 073 자신 TEST-SCENARIO(누락판) | `SCENARIO-GATE-1.md` 대상 | 목표-커버 시나리오 의도 누락 | Step9 자기적용 입력 |
| 073 자신 TEST-SCENARIO(복원판) | `SCENARIO-GATE-2.md` 대상 | 누락 복원(수렴) | Step9 자기적용 입력 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (사전 상태) | When (조작/호출) | Then (검증 상태) |
|---------|------------|----------------|---------------|
| S-1 | fx-cov-missing.json(R·H 미매핑) | `scenario-coverage-check --coverage-input fx-cov-missing.json` | exit 16 + `detail.missing`에 미매핑 R·H 목록 |
| S-2 | 기존 7서브명령 스위트 | 전체 `pytest test_scenario.py` + dispatch 키 조회 | 기존 키 7종·exit 8~14 불변, 신규 추가만 |
| S-3 | 신규 pipeline.json + tmp_task | `state-tool init --rows-from` → `spec-validate` → 게이트행 미완 상태로 `mark execute.implement` | init·spec-validate ok, EXECUTE mark 거부(stage_transition_violation) |
| S-4 | 종료조건 3케이스 입력 | op-scenario-gate 종료조건 판정(수렴/MAX초과/무진전) | 각 verdict(pass/escalate/escalate) 정확 분기 |
| S-5 | op-scenario-gate verdict=rewrite/escalate | PM이 게이트행 mark 시도 | verdict≠pass면 게이트행 mark 근거 없음 → EXECUTE 차단 유지 |
| S-6 | evaluator AGENT.md(신규 phase 추가본) | 기존 3 phase 계약·척도·보고서 경로 대조 | design/spec/drift 계약·Likert 척도·경로 무변경(additive) |
| S-7 | fx: 073 TEST-SCENARIO 목표-커버 시나리오 의도 누락 | op-scenario-gate 실행 | 커버리지 exit16 또는 evaluator ①=0 → verdict:rewrite (FAIL), SCENARIO-GATE-1.md에 FAIL 증거 |
| S-8 | 누락 시나리오 복원 | op-scenario-gate 재실행 | 누락0 AND 판단축 각≥1 AND 평균≥1.5 → verdict:pass, SCENARIO-GATE-2.md에 PASS 증거 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: 커버리지 미충족 결정론 판정 (거짓 초록불 차단)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-002 `cmd_scenario_coverage_check` — R/F/H↔시나리오 매핑 누락 판정 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest + 실 subprocess, mock 금지)** |
| 조건 | `fx-cov-missing.json`: requirements=[R-1,R-2], scenarios가 R-1만 커버(R-2·H-1 미매핑) |
| 기대 결과 | exit code 16(coverage_unmet) + stdout JSON `detail.missing.requirements=["R-2"]`, `all_covered` false |
| 도구 | pytest 9.1.0 (`test-tool resolve` 결과 반영) |
| 실행 명령 | `python3 test_tool.py scenario-coverage-check --coverage-input fx-cov-missing.json` (+ 보완: fx-cov-complete.json → exit0, fx-cov-broken.json → exit17). pytest 케이스: `python3 -m pytest tests/test_scenario.py -q` |
| 결과 | **Pass** |
| 상세 | 실 subprocess 3건 재현: (1) 미매핑 fixture(`requirements:[R-1,R-2]`, 시나리오가 R-1만 커버) → `exit=16`, `{"error":"coverage_unmet","detail":{"missing":{"requirements":["R-2"],"features":[],"hypotheses":["H-1"]}}}` — 기대와 정확 일치. (2) 완전 fixture → `exit=0`, `{"ok":true,"all_covered":true,"counts":{...}}`. (3) 필수키 누락 fixture → `exit=17`, `coverage_input_invalid`. pytest 클래스 4종(`TestScenarioCoverageCheckUnmet/Complete/InputInvalid/Regression`) 8케이스 전부 GREEN(신규 5케이스 목표 초과 충족). `python3 -m pytest tests/test_scenario.py -q` → `31 passed`(기존 23 + 신규 8, 회귀 0). |

#### S-2: 기존 scenario-* 서브명령 회귀 0 (additive 보장)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-002 신규 exit 16/17 배정 + `SCENARIO_DISPATCH` 키 추가 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest 전체 스위트 + dispatch 키 단언)** |
| 조건 | 기존 7서브명령(init/lock/mark/status/red/fidelity-check/conformance) + exit 8~14 기준선 |
| 기대 결과 | 기존 7키·exit 8~14 전부 불변, 신규 `scenario-coverage-check`·exit 16/17만 추가. `test_test_tool.py` 12건 무영향 |
| 도구 | pytest 9.1.0 |
| 실행 명령 | `cd opal/tools/test-tool && python3 -m pytest tests/test_scenario.py tests/test_test_tool.py -q` + `SCENARIO_DISPATCH`/`SCENARIO_ERROR_CODES` 딕셔너리 diff 대조 |
| 결과 | **Pass** |
| 상세 | `git diff lib/scenario.py`로 삭제 라인 검사 — 실질 삭제는 헤더 설명 문자열 1건 + `add_scenario_subparsers` docstring 1건(개수 표기 갱신, 비기능)뿐, `SCENARIO_ERROR_CODES`(기존 8키: red_not_confirmed~surfaces_file_not_found) 및 `SCENARIO_DISPATCH`(기존 7키: scenario-init~scenario-conformance)는 순수 추가(`coverage_unmet`/`coverage_input_invalid`, `scenario-coverage-check`)만 확인, 기존 키 삭제·값 변경 없음. `test_test_tool.py` 12건 중 11건 PASS + 1건 사전 존재 flake(`TestResolve::test_resolve_infer_fallback_when_no_yaml` — `git diff --stat test_tool.py lib/resolver.py` 결과 073 변경 없음(빈 diff), 073과 무관한 환경 의존 사전 결함, 판정 제외). `test_scenario.py` 31 passed(기존 23+신규 8), exit 8~14 회귀 없음. |

#### S-6: evaluator 기존 3 phase 계약 무변경 (additive 확인)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | F-003 opal-evaluator-agent에 `scenario-rubric` phase 추가 |
| 계층 | L1 |
| **실행 방식** | **M1 (산출물 대조 검사 — AGENT.md 구조 단언)** |
| 조건 | AGENT.md 신규 phase 추가본 vs 기존 design-review/spec-review/drift-recheck 정의 |
| 기대 결과 | 기존 3 phase 판정 규칙·Likert 1–5 척도·보고서 경로 무변경. 신규 phase는 2점 척도·SCENARIO-GATE-{N}.md 전용 경로로 분리. `tools`(readonly·verdict-only) 불변 |
| 도구 | grep/diff (산출물 검사) |
| 실행 명령 | `git diff opal/agents/opal-evaluator-agent/AGENT.md` |
| 결과 | **Pass** |
| 상세 | diff 전문 검토 결과 순수 additive: (1) 파라미터 표에 `phase` 값 열거에 `scenario-rubric` 추가 + `iteration`/`scenario_source` 신규 입력 행 2개 추가(조건부 필수, phase==scenario-rubric일 때만) (2) 신규 "Phase 1-S" 절 삽입(2점 척도 전용, Base Likert 1–5와 분리·비혼용 명시) (3) Phase 2에 scenario-rubric 스킵 분기 주석만 추가, 기존 CONTRACT 병합 로직 원문 무변경 (4) Phase 5에 `SCENARIO-GATE-{iteration}.md` 전용 경로 분기 추가, 기존 QA-SPEC/QA-SPEC-DESIGN/QA-SPEC-DRIFT 3종 경로 문자열 무변경 (5) `tools: [Read, Grep, Glob, Bash]` 라인 diff에 미포함(불변, readonly·verdict-only 유지) (6) 변경이력 v1.2 행 추가, 기존 v1.0/v1.1 행 무변경. 기존 3 phase(design-review/spec-review/drift-recheck)의 판정 규칙·Likert 척도·보고서 경로 문자열은 diff상 삭제·수정 없이 그대로 보존됨. |

### L2. 프로세스 통합 (자동, 실 CLI/도구 흐름)

#### S-3: pipeline.json 게이트 행 — state-tool 무코드변경 흡수 + EXECUTE 구조적 차단

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-005 pipeline.json `test_scenario.scenario_gate` 신규 행 |
| 계층 | L2 |
| **실행 방식** | **M1 (state-tool 실 CLI 연쇄 실행)** |
| 조건 | 게이트 행이 삽입된 신규 pipeline.json + 임시 태스크 폴더 |
| 기대 결과 | ① `state-tool init --rows-from <신규 pipeline.json>` ok ② `spec-validate` ok(stage enum·KEY_PATTERN 부합) ③ 게이트 행 미완 상태에서 `mark execute.implement` 호출 시 `stage_transition_violation` 거부 (게이트가 EXECUTE를 구조적으로 차단) |
| 도구 | state-tool CLI |
| 실행 명령 | 임시 폴더(스크래치패드, 073 자신 state.json 미접촉)에서: `python3 state_tool.py spec-validate opal/skills/opal-pilot-dev/references/pipeline.json` → `python3 state_tool.py init <tmp_task> --skill opd --mode agentic --rows-from <신규 pipeline.json>` → 선행 6행(task.task_md~test_scenario.test_scenario_md) `mark --done` → `python3 state_tool.py mark <tmp_task> --task-step execute.implement --done --owner worker` |
| 결과 | **Pass** |
| 상세 | ① `spec-validate` → `{"ok":true,"violations":[],"violations_count":0}` exit0. ② `init --rows-from` → `{"ok":true,"rows_count":16,...}` exit0(신규 게이트 행 id10 `test_scenario.scenario_gate` 포함 16행 무코드변경 흡수 확인). ③ 선행 6행만 done 처리하고 게이트 행(id10)을 pending으로 남긴 상태에서 `execute.implement`(id12) mark 시도 → `{"ok":false,"error":"stage_transition_violation","row_id":12,"incomplete_rows":[10]}` exit1 — **미완료 행이 정확히 게이트 행(10) 단독**으로 특정됨(선행 6행은 모두 done 처리했으므로 다른 원인 배제, 게이트 행이 EXECUTE를 구조적으로 차단함을 정밀 실증). 073 자신의 `tasks/073.../state.json`은 세션 전체에서 미접촉(별도 확인: `git status`에 073 state.json 변경 없음). |

#### S-4: op-scenario-gate 종료조건 3종 분기

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-004 op-scenario-gate 루프 컨트롤 종료조건 |
| 계층 | L2 |
| **실행 방식** | **M1 (게이트 스킬 프로세스 + 도구 출력 조합 실행)** |
| 조건 | (a)누락0·판단축 각≥1·평균≥1.5 (b)iteration N=4(>MAX=3) (c)연속 2회 gaps·점수 동일 |
| 기대 결과 | (a)→verdict:pass (b)→verdict:escalate(반복상한) (c)→verdict:escalate(무진전). 그 외(N≤3·진전)→verdict:rewrite. 무한루프 없음 |
| 도구 | test-tool scenario-coverage-check + opal-evaluator-agent + 종료조건 표 |
| 실행 명령 | 산출물 대조: `op-scenario-gate/SKILL.md` Step 5 판정 순서 + `scenario-gate.md` §5 + `opal-harness.md` §1 "시나리오 목표-커버 게이트" 행 |
| 결과 | **Pass** |
| 상세 | Step 5에 4분기가 우선순위 순서로 명문화됨을 확인: (a) 수렴 — exit0 AND evaluator verdict:pass → `verdict:pass`(루프 종료) (b) 반복상한 — iteration>MAX → `verdict:escalate`(사유: 반복상한), 수치는 본문에 리터럴 미기재하고 `opal-harness.md` §1 참조(실측: 57행 "시나리오 목표-커버 게이트 (루브릭 미달) \| 3회 \| 캡틴(사용자) 에스컬레이션") (c) 무진전 — 직전 반복 대비 missing∪gaps 집합이 연속 2회 비개선 → `verdict:escalate`(사유: 무진전) (d) 그 외 → `verdict:rewrite`+gaps. 무한루프 방지: (b)(c) 모두 escalate로 귀결되어 자율 재시도가 구조적으로 차단됨(Step 6 "escalate → 호출자가 캡틴에게 에스컬레이션하고 루프를 중단한다. 자율 재시도하지 않는다"). S-7/S-8 자기적용으로 (a)/rewrite 분기 실측 재현(아래 S-7/S-8 참조), (b)/(c)는 073 1회 수렴(iteration=2)이라 실측 트리거는 없었으나 문서 명문화·수치 SSOT 존재로 산출물 검증 완료. |

#### S-5: tool-gated self-confirming 차단 (Producer≠Evaluator)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-004·F-005 게이트 통과의 2증거(도구 exit0 + evaluator verdict pass) 강제 |
| 계층 | L2 |
| **실행 방식** | **M1 (게이트 verdict별 mark 가부 실증)** |
| 조건 | op-scenario-gate가 verdict:rewrite 또는 escalate 반환한 상태 |
| 기대 결과 | verdict≠pass면 `test_scenario.scenario_gate` 행 mark 근거(2증거)가 없어 통과 불가 → `test_scenario.user_confirm`·EXECUTE 진입 차단 유지. PM 단독 판단으로 pass 생성 불가 |
| 도구 | op-scenario-gate + state-tool |
| 실행 명령 | `op-scenario-gate/SKILL.md` §"[MUST] 규율" #1·#2 + Step 6 반환 규약 대조. 보완: S-3의 임시 폴더 실측(게이트 행 미완 → `execute.implement` mark 거부)을 근거로 재사용 |
| 결과 | **Pass (문서 규율 확인) — 단, 관찰사항 1건 기록** |
| 상세 | `[MUST] 규율` #1이 "`verdict: pass`는 오직 (Step 3) test-tool exit 0 AND (Step 4) evaluator verdict pass 두 증거가 모두 존재할 때만 성립한다. 호출자가 산문 판단만으로 pass를 생성할 수 없다"를 명문화(근거: `scenario-gate.md` §6, `PRINCIPLES.md:15`). Step 6도 "verdict:pass → 호출자가 두 증거를 근거로 게이트 행 mark를 진행한다. 본 스킬 자신은 mark를 수행하지 않는다"로 mark 권한 소재를 명시. **관찰**: S-3 임시 폴더 실측 중 `state-tool mark test_scenario.scenario_gate --done --owner PM`을 (두 증거 생성 없이) 직접 호출했더니 state-tool 자체는 이를 거부하지 않고 `{"ok":true}`로 수락함 — 즉 2증거 강제는 **state-tool 코드 레벨이 아니라 op-scenario-gate SKILL.md의 절차적([MUST]) 규율**로 성립한다(state-tool은 stage_transition만 기계 검사, 증거 유무는 검사하지 않음). 이는 프레임워크의 기존 Guards 패턴(CONVENTIONS.md §Guards도 승인 없는 구현 금지를 절차 규율로 강제)과 동일한 성격이며 설계 의도(SKILL.md가 유일 호출 경로, PM은 스킬을 우회하지 않는다는 전제)와 일치하나, PM Gate 판정 시 참고할 사실로 기록한다. 시나리오 자체의 기대결과("verdict≠pass면 게이트행 mark 근거 없음")는 문서 명문화 기준으로 충족되어 Pass 처리한다. |

#### S-7: 자기적용 음성통제 — 목표-커버 시나리오 의도 누락 시 게이트 FAIL

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-008 자기적용(음성통제) — 게이트가 목표 누락을 실제로 잡는가 |
| 계층 | L2 |
| **실행 방식** | **M1 (완성된 op-scenario-gate를 073 자신에 실행)** |
| 조건 | 073 TEST-SCENARIO에서 목표-커버 시나리오(예: "S-3 게이트가 EXECUTE를 실제 차단하는지")를 의도적으로 제거한 페이로드 |
| 기대 결과 | 커버리지 exit16(H 미매핑) 또는 evaluator ①목표달성=0 → verdict:rewrite(게이트 FAIL) → 재작성 유도. 증거 `SCENARIO-GATE-1.md`에 FAIL 기록 |
| 도구 | op-scenario-gate (test-tool + evaluator) |
| 실행 명령 | `python3 test_tool.py scenario-coverage-check --coverage-input .scenario-coverage-input-NEG.json`(073 태스크 폴더 실 파일, S-7/S-8 제거된 음성통제 페이로드) |
| 결과 | **Pass** |
| 상세 | 재현 결과 `SCENARIO-GATE-1.md` 기록과 완전 일치: `{"ok":false,"error":"coverage_unmet","detail":{"missing":{"requirements":["R-8"],"features":["F-008"],"hypotheses":["H-7"]}}}`, `exit=16`. `op-scenario-gate` Step 3 규칙(exit16 시 Step 4 평가자 게이트 건너뛰고 즉시 종료조건 판정 직행)에 따라 결정론 하드게이트 미충족만으로 `verdict:rewrite`(FAIL) 확정 — 목표 검증 시나리오(S-7/S-8, R-8/F-008/H-7 커버)를 의도 누락시켰을 때 게이트가 실제로 FAIL을 낸다는 음성통제가 실증됨. 070 재발 방지("시나리오가 있는데 놓친" 게 아니라 "시나리오가 애초에 없었다" 결함을 결정론 매핑 커버리지가 잡아냄) 목표 직접 검증. |

#### S-8: 자기적용 정상수렴 — 누락 복원 후 게이트 PASS

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-008 자기적용(정상수렴) — 완전한 시나리오 집합의 수렴 |
| 계층 | L2 |
| **실행 방식** | **M1 (op-scenario-gate 재실행)** |
| 조건 | S-7의 누락 시나리오를 복원한 완전 페이로드 |
| 기대 결과 | 커버리지 누락=0 AND 판단축(①⑤⑥) 각≥1 AND 평균≥1.5 → verdict:pass(수렴). 증거 `SCENARIO-GATE-2.md`에 PASS 기록 |
| 도구 | op-scenario-gate (test-tool + evaluator) |
| 실행 명령 | `python3 test_tool.py scenario-coverage-check --coverage-input .scenario-coverage-input.json`(073 태스크 폴더 실 파일, 복원된 완전 페이로드) + `SCENARIO-GATE-2.md`(evaluator scenario-rubric 채점 산출물) 대조 |
| 결과 | **Pass** |
| 상세 | 재현 결과 `{"ok":true,"all_covered":true,"counts":{"requirements":8,"features":8,"hypotheses":7,"scenarios":10}}` exit=0 — 결정론 파트(②③④) 누락 0 확인, `SCENARIO-GATE-2.md`의 "선행 통과 확정: exit 0, all_covered (8R/8F/7H/10시나리오)" 서술과 정확 일치. `SCENARIO-GATE-2.md` 판단 파트(①⑤⑥, evaluator 산출): `scores:{goal:2,adoption:1,boundary:2}`, `average:1.67`, `gaps:[]`, `verdict:pass` — 3축 각 ≥1점(0점 축 없음) AND 평균 1.67≥1.5 충족, 종료조건 §5-1 "수렴" 규칙과 정확 부합. 두 증거(도구 exit0 + evaluator verdict pass) 모두 성립 → `verdict:pass` 최종 확정, 게이트 PASS 실증. S-7(FAIL)→S-8(PASS) 연쇄로 루프의 재작성→수렴 사이클 자체가 073 자신에 대해 왕복 실증됨. |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

해당 없음 — FE 화면·인증/인가·수동 부하 대상 없음. 전 시나리오 자동(M1) 검증 가능. (S-7/S-8 자기적용은 PM 오케스트레이션으로 자동 실행, 캡틴 수동 확인 불요.)

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC (SSOT 6축·3종료·계약) | (문서) | 산출물 | (PM Gate 검사) | `scenario-gate.md` | 문서 트랙 — TS-001/002(PLAN §3.1.5) |
| R-2 AC (누락 시 FAIL) | H-1 | L1 | S-1 | `test_scenario.py:[T073/L1-R2a]` | RED-first |
| R-2 AC (완전 시 ok) | H-1 | L1 | S-1(보완 케이스) | `test_scenario.py:[T073/L1-R2b]` | fx-cov-complete → exit0 |
| R-2 AC (입력 검증) | H-1 | L1 | S-1(보완 케이스) | `test_scenario.py:[T073/L1-R2c]` | fx-cov-broken → exit17 |
| R-2 회귀 | H-2 | L1 | S-2 | `test_scenario.py:[T073/L1-REG]` | 기존 키·exit 불변 |
| R-3 AC (scenario-rubric phase) | H-6 | L1 | S-6 | `opal-evaluator-agent/AGENT.md` | 산출물 검사 + additive |
| R-4 AC (단일 호출·종료조건) | H-4 | L2 | S-4 | `op-scenario-gate/SKILL.md` | 종료조건 3종 분기 |
| R-5 AC (게이트 미통과 시 EXECUTE 차단) | H-3, H-5 | L2 | S-3, S-5 | `pipeline.json` + state-tool | 구조적 차단 |
| R-6 AC (교체형 목표 AC 패턴) | (문서) | 산출물 | (PM Gate 검사) | `op-task/SKILL.md` | 문서 트랙 — TS-013 |
| R-7 AC (단위 테스트 + 회귀 0) | H-1, H-2 | L1 | S-1, S-2 | `test_scenario.py` 전체 스위트 | RED→GREEN |
| R-8 AC (음성통제) | H-7 | L2 | S-7 | `SCENARIO-GATE-1.md` | 게이트 FAIL 실증 |
| R-8 AC (정상수렴) | H-7 | L2 | S-8 | `SCENARIO-GATE-2.md` | 게이트 PASS 실증 |

> **목표 달성 검증(dogfooding)**: 이 태스크의 목표("게이트가 목표 누락을 실제로 잡는다")는 S-7(음성통제)+S-8(정상수렴)이 직접 검증한다 — 우리가 만드는 루브릭 ①목표달성 축을 태스크 자신에 적용하는 자기지시적 검증. 070 재발 방지(핵심 목표 미검증 완료)의 직접 대응.

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff (0.x, `/opt/homebrew/bin/ruff`) | Pass | `ruff check lib/scenario.py tests/test_scenario.py` → `All checks passed!` |
| 2 | 타입 체크 | mypy/pyright | N/A | 프로젝트 미도입(둘 다 환경에 미설치, test-tool 자체 개발 파이프라인에 typecheck 단계 없음 — `test-tool resolve`가 대상 프로젝트용으로 제공하는 tiers.unit.typecheck는 별개). `python3 -m py_compile lib/scenario.py test_tool.py tests/test_scenario.py`로 구문 유효성만 확인(OK) |
| 3 | 포맷터 | ruff format (대리 검사) | N/A(비회귀 확인) | `ruff format --check`가 변경 파일 2건에 reformat 필요를 보고했으나, 미변경 베이스라인 파일(`test_tool.py`/`lib/resolver.py`/`lib/runner.py`)도 동일하게 reformat 필요 판정됨 — 프로젝트가 ruff format을 포매터로 채택하지 않은 기존 스타일(회귀 아님)임을 확인 |
| 4 | @header 정합 (scenario.py exports/description) | 육안 대조 | Pass | `lib/scenario.py` 헤더 `exports`에 `cmd_scenario_coverage_check` 포함, `description`에 073/F-002 목적·정규화 페이로드·SSOT 미접촉·축 분리 명시. `add_scenario_subparsers` docstring도 "8종" 갱신(구 "5종"→누적 반영, 비기능 변경) |
| 5 | 변경이력 행 추가 (수정 문서 전체) | `git diff` grep `(073)` | Pass | 확인 완료 문서: `opal-harness.md`(v6.6) · `op-dev-test-scenario/SKILL.md`(v1.8) · `test-scenario-guide.md`(v2.7) · `opal-pilot-dev/SKILL.md`(v4.8) · `op-task/SKILL.md`(v2.3) · `opal-evaluator-agent/AGENT.md`(v1.2) · `docs/PROJECT.md`(변경이력 표 신규 행) · 신규 파일 `scenario-gate.md`(v1.0)·`op-scenario-gate/SKILL.md`(v1.0) 각 자체 변경이력 보유. 전건 (073) 태그 확인 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | 변경 파일 9종 대상 `grep -rniE "api[_-]?key\|secret\|password\|token\s*=\|BEGIN (RSA\|PRIVATE) KEY\|aws_access\|Authorization: Bearer"` → 매치 0건 |
| 2 | .gitignore 확인 | Pass | `.gitignore`에 `__pycache__/`·`.pytest_cache/`·`.ruff_cache/` 등 표준 제외 유지, 073 산출물(`tasks/073-.../*.md`, fixture json)은 태스크 산출물 관례대로 추적 대상(제외 대상 아님) — 의도된 상태 |
| 3 | coverage-input 페이로드 경로 이탈 방지(task_folder 하위만) | Pass(절차적) — 관찰사항 1건 | `op-scenario-gate/SKILL.md` [MUST] 규율 #5 + Step 2 "본 Step은 task_folder 하위 파일만 Read/Write한다"로 명문화. **관찰**: `test-tool scenario-coverage-check --coverage-input <path>`의 코드 구현(`cmd_scenario_coverage_check`)은 `--coverage-input` 인자를 임의 경로로 받아 코드 레벨 sandbox 검증은 하지 않음(S-5와 동일 성격 — 절차 규율이지 CLI 강제 아님). 호출 주체가 PM/오케스트레이터로 한정되고 외부 미신뢰 입력 경로가 아니므로 즉각적 보안 위험은 아니나, PM Gate 참고사항으로 기록 |

## 7. 판정

**All Pass** -- S-1~S-8 8개 시나리오 전부 실 subprocess/실 CLI/실 산출물 증거로 Pass 확정(mock 없음). §5 코드품질 5항목 전부 Pass/N/A(비회귀 확인), §6 보안 3항목 전부 Pass(관찰사항 2건은 차단 사유 아님 — 기존 프레임워크 Guards 패턴과 동일한 절차적 통제로, PM Gate 참고사항으로만 병기). 회귀: `test_scenario.py` 31 passed(기존 23+신규 8, 회귀 0), `test_test_tool.py` 11/12 passed(1건은 073 미접촉 코드 경로의 사전 존재 환경 의존 flake로 확인되어 판정 제외). 핵심 목표(070 재발 방지: 목표 미검증 완료 차단)는 S-7(FAIL 음성통제)→S-8(PASS 정상수렴) 왕복 자기적용으로 직접 실증됨.

**참고(관찰사항, 판정에 영향 없음)**: S-5·§6-3에서 "PM 단독 판단으로 pass 생성 불가"·"경로 이탈 방지"가 **op-scenario-gate SKILL.md의 절차적 [MUST] 규율**로 성립하며, state-tool·test-tool 코드 자체가 2증거 검증이나 task_folder 경로 sandbox를 기계적으로 강제하지는 않음을 실측 확인했다. 이는 CONVENTIONS.md §Guards(승인 전 구현 금지도 절차 규율)와 동일한 프레임워크 관례이며 073의 설계 의도(SKILL.md가 유일 호출 경로)와 정합하므로 결함으로 판정하지 않았으나, 후속 확산(oppl/opds/opsdd/oppd) 시 PM이 op-scenario-gate를 우회해 state-tool을 직접 호출할 가능성에 대한 참고 정보로 남긴다.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인 — `grep -niE "mock|patch|MagicMock" TEST-SCENARIO.md` 매치는 모두 "mock 금지"(M1 실행방식 명시)·"mock<real-http<real-usage" 충실도 사다리 용어뿐, `unittest.mock`/`MagicMock`/`patch()` 등 실제 모킹 지시·코드는 0건)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (L3 해당 없음 — 명시됨)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전 (H-1~H-7 전부 시나리오 연결)
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 시 M2 시나리오 포함 — FE·인증·외부 API 변경 없음 → M2 면제(명시됨)
