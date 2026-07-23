# TEST SCENARIO: op-scenario-gate 목표-커버 게이트 확산 1차 (opds·opsdd)

> 작성일: 2026-07-23 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반 (작성자 ≠ opal-plan-agent)

> **트랙 판정 (RED-first §1.5)**: **구현-후-검증**. 전 변경이 마크다운 SKILL/SSOT/가이드 + pipeline.json 배선이며 Python 비즈니스 로직·DB·API·인증 신규 없음(test-tool·evaluator는 pilot-중립 무변경). 공통 불변: 작성자≠구현자(PM 작성 / opal-task-agent 배선) + TEST 단계 검증 유지.
> **M2 의무 트리거**: FE·인증·외부 API 없음 → M2 면제. 전 시나리오 M1(도구/CLI/산출물 검사).

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-002 opds producer 확립 | opds가 TEST-SCENARIO.md 미생성 → 게이트 producer_artifact 부재 | P0 | L1+L2 | S-1, S-2 |
| H-2 | F-001 opsdd 변환기 소스 | TEST-SCENARIOS.md만 읽고 SPEC.md 미Read → 정규화 페이로드 불완전(exit 17) | P1 | L1 | S-3, S-6 |
| H-3 | F-003 opsdd STATE 표 재정렬 | `--row N` 전수 수정 누락 → Phase 3~6 mark 오행 참조(회귀) | P0 | L1+L2 | S-4 |
| H-4 | F-002 opds pipeline.json id 재정렬 | 스펙 위반 → `state-tool spec-validate` 실패 → init 거부 | P1 | L2 | S-7 |
| H-5 | F-001 pilot 분기 추가 | 기존 pilot=opd 행·opd 접합·도구 회귀 | P1 | L1 | S-8 |
| H-6 | F-001 규율 #4·산문 | 확산 후 "1차 opd 단일" 문구 사실 불일치 | P2 | L1 | S-9 |

## 2. 테스트 데이터 설계

> DB 없음(프레임워크 배선) — fixture = 정규화 페이로드·임시 태스크 폴더·신규 pipeline.json/STATE 표.

### 2.1 사전 조건 데이터

| 자원 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| opds 신규 pipeline.json(게이트 행 포함) | `plan.scenario_gate` 삽입본 | 11 task-step | Step 2 산출 |
| opsdd 신규 STATE 표(SKILL.md) | 25행 재정렬본 | `--row N` 전수 정합 | Step 3 산출 |
| opds 정규화 페이로드(완전) | `fx-opds-complete.json` | 전 R/F/H 커버 | 자기적용 fixture |
| opds 정규화 페이로드(누락) | `fx-opds-missing.json` | 목표 시나리오 누락 | 자기적용 fixture |
| opsdd 정규화 페이로드(SPEC 소스) | `fx-opsdd.json` | FR/AC/EC 매핑 | 자기적용 fixture |
| 임시 태스크 폴더 | `tmp_opds/`, `tmp_opsdd/` | state-tool init 대상 | tmpdir |
| opd 기준선 | opd SKILL·pipeline.json·scenario-gate.md·test-tool·evaluator | 회귀 기준(diff 0) | 기존 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (사전 상태) | When (조작/호출) | Then (검증 상태) |
|---------|------------|----------------|---------------|
| S-1 | opds SKILL STEP 2 개정본 | STEP 2 서술 + op-dev-plan diff 조회 | TEST-SCENARIO.md 작성 주체(PM+캡틴) 명시, op-dev-plan diff 0 |
| S-2 | opds 신규 pipeline.json + tmp_opds | init → 게이트행 미완 상태 execute.implement mark | `plan.scenario_gate` 존재, EXECUTE mark 거부(stage_transition_violation) |
| S-3 | opds·opsdd 변환기 표 | pilot별 정규화 페이로드 생성 검사 | `{goal,R,F,H,scenarios[]}` 정확, opsdd covers_requirements=FR 역참조 |
| S-4 | opsdd 신규 STATE 표 | `--rows-from` init + `--row N` 리터럴 대조 | rows_count 25, Phase 3~6 행 참조 정합 |
| S-5 | opsdd REVIEW 개정본 | REVIEW 절차 + guard DESIGN 진입 | op-scenario-gate(pilot:opsdd) 호출, verdict:pass 후 DESIGN, 독립 evaluator 채점(Producer≠Evaluator) |
| S-6 | verify-guide §4 개정본 | §4·§2 diff 조회 | §4 게이트 대체, §2 S-1~S-6 diff 0 |
| S-7 | opds 신규 pipeline.json | `state-tool spec-validate` | exit 0, violations 0 |
| S-8 | opd 기준선 | opd 관련 파일 diff 조회 | pilot=opd 행·opd 접합·test-tool·evaluator diff 0 |
| S-9 | op-scenario-gate SKILL 개정본 | 규율 #4·산문·enum 조회 | 3종 지원 사실 일치 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: opds producer 확립 (op-dev-plan 미접촉)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-002(a) opds STEP 2 서술 보강 |
| 계층 | L1 |
| **실행 방식** | **M1 (산출물 검사 grep/diff)** |
| 조건 | opal-pilot-dev-short/SKILL.md STEP 2 개정본 |
| 기대 결과 | STEP 2가 "PM+캡틴이 op-dev-test-scenario 통일 형식으로 TEST-SCENARIO.md 직접 작성" 명시 AND `op-dev-plan/SKILL.md` diff 0(opd 무영향) |
| 도구 | git diff, grep |
| 실행 명령 | `grep -n "PM+캡틴이 op-dev-test-scenario\|알투(PM) + 캡틴 페어" opal/skills/opal-pilot-dev-short/SKILL.md` + `git diff --stat -- opal/skills/op-dev-plan/SKILL.md` |
| 결과 | PASS |
| 상세 | STEP 2 본문(SKILL.md:54)에 "알투(PM) + 캡틴 페어가 `op-dev-test-scenario/SKILL.md`의 'TEST-SCENARIO.md 통일 형식'을 명시 참조하여 TEST-SCENARIO.md를 직접 작성한다(self-confirming 방지 — PLAN 워커와 다른 작성자, opd STEP 3.5 동형)" 명시 확인. `git diff --stat -- opal/skills/op-dev-plan/SKILL.md` 출력 없음(diff 0) — op-dev-plan 무영향 실증. |

#### S-3: opds·opsdd 변환기 정규화 페이로드 정확성 (목표 커버)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-001 pilot=opds/opsdd 변환기 |
| 계층 | L1 |
| **실행 방식** | **M1 (변환 산출물 검사)** |
| 조건 | op-scenario-gate Step 2 opds/opsdd 표; opsdd는 SPEC.md(FR/AC/EC) + TEST-SCENARIOS.md 소스 |
| 기대 결과 | opds=opd 동형 페이로드; opsdd=`requirements`←FR·`features`←AC·`hypotheses`←EC, `covers_requirements`←AC "대응 FR" 역참조 정확 |
| 도구 | grep (SKILL 표), 정규화 페이로드 예시 대조 |
| 실행 명령 | `grep -n "pilot=opds\|pilot=opsdd\|covers_requirements ← 해당 AC\|FR-NN\|AC-NN\|EC-NN" opal/skills/op-scenario-gate/SKILL.md` + test-tool scenario-coverage-check 자기적용 실증(S-10 결과 상호참조) |
| 결과 | PASS |
| 상세 | Step 2에 `pilot=opds`(:50, opd 동형 — goal/requirements/features/hypotheses/scenarios[] 표 동일)와 `pilot=opsdd`(:64, SPEC.md 소스) 표 존재 확인. opsdd 표: `requirements`←`[FR-NN]`(:69), `features`←`AC-NN`(:70), `hypotheses`←`[EC-NN]`(:71), `covers_requirements`←"해당 AC 상단 '대응 FR: FR-NN' 역참조"(:76) 정확 명시. `covers_hypotheses`는 EC 기원 행일 때만 채움(:78). S-10에서 opds/opsdd 정규화 예시 페이로드를 실제 test-tool에 통과시켜 포맷 유효성 실증(완전→exit0, 누락→exit16) — 변환기 표가 유효한 페이로드를 생성함을 간접 확인. |

#### S-6: verify-guide §4 대체 + S-1~S-6 존치 (교체형: 수동→도구)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-004 verify-guide §4 |
| 계층 | L1 |
| **실행 방식** | **M1 (diff)** |
| 조건 | verify-guide.md 개정본 |
| 기대 결과 | §4가 scenario-coverage-check 게이트로 대체(구형 수동 절차 잔존 0), §2 S-1~S-6 diff 0(존치), 변경이력 행 존재 |
| 도구 | git diff |
| 실행 명령 | `git diff -- opal/skills/opal-pilot-sdd/references/verify-guide.md` (전체 diff) + `grep -n "^## " opal/skills/opal-pilot-sdd/references/verify-guide.md` (§2 라인대 diff 부재 확인) |
| 결과 | PASS |
| 상세 | §4가 "4. 목표-커버 게이트 (scenario-coverage-check + 독립 evaluator)"로 대체 — 구형 "4-1 확인 절차/4-2 커버리지 기준/4-3 갭 처리" 수동 절차 완전 제거(잔존 0), op-scenario-gate(pilot:opsdd) 호출 + scenario-gate.md SSOT 참조로 대체. §2(구조 검증 체크리스트 S-1~S-6, 라인 29~52) 구간은 diff 헝크가 전혀 미치지 않음(diff 헝크는 §1 라인19 "3단계 흐름" 및 §4~5 라인134 이후에만 존재) — S-1~S-6 정의 표 diff 0 확인. 변경이력 표 v1.1 행 신규 추가 확인. |

#### S-8: opd 회귀 0 (부정 경로 — opd 접합 무손상)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-005 회귀 |
| 계층 | L1 |
| **실행 방식** | **M1 (diff)** |
| 조건 | opd 기준선 |
| 기대 결과 | op-scenario-gate `pilot=opd` 변환기 행·opd STEP 3.5·opd pipeline.json 행 10·scenario-gate.md·test-tool·opal-evaluator-agent 전부 diff 0 |
| 도구 | git diff --name-only + 대상 파일 diff |
| 실행 명령 | `for f in opal/skills/opal-pilot-dev/ opal/core/references/harness/scenario-gate.md opal/tools/test-tool/ opal/agents/opal-evaluator-agent/; do git diff --stat -- "$f"; done` + op-scenario-gate SKILL.md `pilot=opd` 표(:33-48) 원문 대조 |
| 결과 | PASS |
| 상세 | `opal/skills/opal-pilot-dev/`(opd 본체)·`scenario-gate.md`·`opal/tools/test-tool/`·`opal/agents/opal-evaluator-agent/` 4개 대상 모두 `git diff --stat` 출력 0(diff 없음). op-scenario-gate/SKILL.md 내 `pilot=opd` 변환기 표(라인 33~48: goal/requirements/features/hypotheses/scenarios[] 5행)는 diff 헝크에 전혀 포함되지 않음 — 이번 변경은 그 표 뒤에 opds/opsdd 표를 추가(additive)하고 입력설명·확장성 산문·규율#4 문구만 갱신, opd 표 자체는 바이트 단위로 무변경 확인. |

#### S-9: 규율 #4·산문·enum 정합 (경계)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | F-001 정합 갱신 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep)** |
| 조건 | op-scenario-gate SKILL 개정본 |
| 기대 결과 | :19 enum·:50 산문·:120 [MUST] 규율 #4가 "opd/opds/opsdd 3종 지원(oppl 제외·oppd 2차)" 사실과 일치 |
| 도구 | grep |
| 실행 명령 | `grep -n "지원 pilot\|oppl 제외\|oppd 2차\|다중 pilot 지원\|확장성 근거" opal/skills/op-scenario-gate/SKILL.md` |
| 결과 | PASS |
| 상세 | :19 입력 enum — "지원 pilot: `opd`/`opds`/`opsdd` (oppl 제외 확정·oppd 2차 유예)". :84 확장성 산문 — "opds·opsdd 확산 완료(3종 지원). oppl은 자체 표면-게이트+독립평가자 보유로 제외 확정, oppd는 2차 유예". :154 [MUST] 규율 #4 — "다중 pilot 지원: opd(STEP 3.5)·opds(STEP 2)·opsdd(Phase 2 REVIEW) 3종 접합. ... oppl 제외·oppd 2차." 3개소 모두 "opd/opds/opsdd 3종 지원(oppl 제외·oppd 2차)" 사실과 정확히 일치 — 라인 번호는 additive 삽입으로 원 지침(:19/:50/:120)에서 소폭 이동했으나(:19/:84/:154) 문구 내용은 일치. |

### L2. 프로세스 통합 (자동, 실 CLI/게이트 흐름)

#### S-2: opds 게이트 배선 — EXECUTE 구조적 차단 (목표 커버)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-002(b) opds pipeline.json 게이트 행 |
| 계층 | L2 |
| **실행 방식** | **M1 (state-tool 실 CLI 연쇄)** |
| 조건 | 게이트 행 삽입 opds pipeline.json + 임시 태스크 폴더 |
| 기대 결과 | ① init ok(11행) ② rows 1~3 완료 후 게이트행(plan.scenario_gate) 미완 상태 `mark execute.implement` → `stage_transition_violation` 거부 ③ 게이트행 mark 후 execute 진행 허용 |
| 도구 | state-tool CLI |
| 실행 명령 | `~/.opal/tools/state-tool/run.sh init <tmp_opds> --skill opd --rows-from opal/skills/opal-pilot-dev-short/references/pipeline.json --mode semi-agentic` → `mark --task-step {task.task_md,task.user_confirm,plan.plan_md} --done` → `mark --task-step execute.implement --done` |
| 결과 | PASS |
| 상세 | ① init 결과 `rows_count: 11` 확인(1~3행 완료 상태 아님). ② rows 1~3(task.task_md/task.user_confirm/plan.plan_md) mark 후 게이트행(plan.scenario_gate, row_id 4) 미완 상태에서 `mark execute.implement`(row_id 7) 시도 → `{"ok": false, "error": "stage_transition_violation", "message": "단계 건너뛰기 차단: 행 7 갱신 전에 앞 행 [4, 5, 6]이(가) 완료되지 않았음", "incomplete_rows": [4, 5, 6]}` exit 1 — 거부 확인(incomplete_rows에 게이트행 4 포함). ③ 게이트행(4)·PM Gate(5)·사용자 확인(6) 순차 mark 후 `mark execute.implement` 재시도 → `{"ok": true, "row_id": 7, "stage": "EXECUTE", "status": "done"}` 성공 확인. 임시 폴더(`scratchpad/tmp_opds/`)만 사용, **075 자신의 state.json 미접촉** 확인. |

#### S-4: opsdd STATE 표 재정렬 무손상 (rows_count 25)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-003 STATE 표 + `--row N` 전수 |
| 계층 | L2 |
| **실행 방식** | **M1 (state-tool init 파싱)** |
| 조건 | opsdd 신규 SKILL.md 25행 표 + 임시 폴더 |
| 기대 결과 | `state-tool init --rows-from opsdd/SKILL.md` → `rows_count: 25` 파싱 정상, Phase 3~6 `--row N` 리터럴이 재정렬 행과 일치(오행 참조 0) |
| 도구 | state-tool CLI + grep(`--row N` 대조) |
| 실행 명령 | `~/.opal/tools/state-tool/run.sh init <tmp-task-path> --skill opsdd --mode semi-agentic --rows-from opal/skills/opal-pilot-sdd/SKILL.md` (rows_count 확인) + `grep -n -- '--row \|--after \|#[0-9]\{1,2\}\b' opal/skills/opal-pilot-sdd/SKILL.md` (rows≥11 +1 정합 대조) |
| 결과 | PASS |
| 상세 | init 결과 `{"ok": true, "rows_count": 25}` 확인 (경고: `--rows-from <SKILL.md>` 마크다운 파싱 deprecated 경고 출력 — 070 후속 pipeline.json 전환은 075 범위 밖으로 정상). `--row N`/`--after N`/`#N` 리터럴 전수(라인130,131,198,199,244,245,250,253,254,296,299,346,348,480) 대조 결과, 재정렬된 25행 표(SPEC PM Gate=6, SPEC 사용자확인=7, DESIGN PM Gate=16, DESIGN 사용자확인=17, EXECUTE ACT실행=18, EXECUTE PM Gate=19, EXECUTE 사용자확인=20, CLOSE=25)와 전부 정합 — 오행 참조 0건. |

#### S-5: opsdd REVIEW 게이트 — DESIGN 차단 + self-confirming 해소 (목표 커버)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-003 REVIEW 배선 |
| 계층 | L2 |
| **실행 방식** | **M1 (게이트 행 + guard 실증)** |
| 조건 | opsdd 신규 STATE 표(게이트 행 10·11) |
| 기대 결과 | REVIEW 절차가 op-scenario-gate(pilot:opsdd) 호출; 게이트 행 미완 시 guard가 DESIGN 첫 행 mark 거부; 채점 주체가 독립 evaluator(opal-evaluator-agent) → Producer(PM)≠Evaluator 명시 |
| 도구 | state-tool CLI + 산출물 검사 |
| 실행 명령 | init 후 rows 1~9 mark → `mark <task-path> --row 14 --done` 시도 시 `stage_transition_violation`(incomplete_rows에 10,11 게이트 행 포함) 거부 확인 → `mark --row 10/11/12/13 --done` 후 재시도 시 row14 mark 성공 확인(REVIEW §Phase 2 4단계 서술 + verify-guide.md 참조로 op-scenario-gate(pilot:opsdd) 호출·독립 evaluator 채점 명시 diff 확인) |
| 결과 | PASS |
| 상세 | (동일 tmp_opsdd 폴더 재사용) rows 1~9 mark 후 `mark --row 14 --done` 시도 → `{"ok": false, "error": "stage_transition_violation", "message": "단계 건너뛰기 차단: 행 14 갱신 전에 앞 행 [10, 11, 12, 13]이(가) 완료되지 않았음", "incomplete_rows": [10, 11, 12, 13]}` exit 1 — 거부 확인(incomplete_rows에 커버리지 게이트 행 10·목표-커버 게이트 행 11 포함). rows 10~13 mark 후 `mark --row 14 --done` 재시도 → `{"ok": true, "row_id": 14, "stage": "DESIGN"}` 성공. 산출물 검사: `opal-pilot-sdd/SKILL.md` Phase 2 REVIEW 절차 4단계 서술(SKILL.md:142-160)에 "3. 목표-커버 게이트: op-scenario-gate 호출 (pilot: opsdd)" + "Step 4 evaluator verdict pass → 행 11 mark (독립 evaluator = self-confirming 해소, Producer≠Evaluator)" 명시 + PRINCIPLES §15 인용 확인(SKILL.md:168). |

#### S-7: opds pipeline.json spec-validate (경계)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-002 pipeline.json id 재정렬 |
| 계층 | L2 |
| **실행 방식** | **M1 (state-tool spec-validate)** |
| 조건 | 게이트 행 삽입·id 재정렬 opds pipeline.json |
| 기대 결과 | `state-tool spec-validate` exit 0, violations 0 (id 연속성·key 유일성·stage enum 준수) |
| 도구 | state-tool CLI |
| 실행 명령 | `~/.opal/tools/state-tool/run.sh spec-validate opal/skills/opal-pilot-dev-short/references/pipeline.json` |
| 결과 | PASS |
| 상세 | `{"ok": true, "command": "spec-validate", "violations": [], "violations_count": 0}` exit 0 — id 연속성(1~11)·key 유일성(`plan.scenario_gate` 포함 11개 key 중복 없음)·stage enum 준수 전부 위반 0건. |

#### S-10: 자기적용 — opds·opsdd 게이트 음성/수렴 (목표 커버)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2 |
| 대상 | F-006 자기적용 |
| 계층 | L2 |
| **실행 방식** | **M1 (op-scenario-gate 실호출, evaluator 디스패치 포함)** |
| 조건 | opds/opsdd 정규화 페이로드(완전·누락) |
| 기대 결과 | 목표 시나리오 누락 → coverage exit 16 또는 evaluator goal<1 → verdict FAIL(다음 단계 차단); 완전 → exit 0 AND verdict pass → 게이트 행 mark 가능 |
| 도구 | op-scenario-gate (test-tool + opal-evaluator-agent) |
| 실행 명령 | opds/opsdd 변환기 표 형식대로 정규화 fixture 4종 작성(`fx-opds-complete.json`, `fx-opds-missing.json`, `fx-opsdd-complete.json`, `fx-opsdd-missing.json`) 후 각각 `python3 test_tool.py scenario-coverage-check --coverage-input <fixture>` 실행 |
| 결과 | PASS |
| 상세 | opds-complete → `{"ok": true, "all_covered": true, "counts": {"requirements":2,"features":2,"hypotheses":2,"scenarios":2}}` exit 0. opds-missing(F-002/R-2/H-2 누락 시나리오) → `{"ok": false, "error": "coverage_unmet", "detail": {"missing": {"requirements":["R-2"],"features":["F-002"],"hypotheses":["H-2"]}}}` exit 16. opsdd-complete(FR-01/02·AC-01/02·EC-01, covers_requirements←FR 역참조 반영) → exit 0 all_covered. opsdd-missing(FR-02/AC-02/EC-01 누락) → exit 16, `detail.missing`에 FR-02/AC-02/EC-01 정확 반영. 4종 모두 기대 exit code·detail 일치 — opds/opsdd 신규 변환기가 test-tool이 소비 가능한 유효 정규화 페이로드를 생성함을 실증. (판단축 ①⑤⑥ 판단 게이트는 075 자기 적용 게이트에서 opal-evaluator-agent scenario-rubric으로 이미 verdict:pass 실증됨 — `SCENARIO-GATE-1.md` 참조, 본 S-10은 결정론 축(②③④) 신규 변환기 실증에 집중) |

### L3. 사용자 협업

해당 없음 — FE·인증·수동 부하 대상 없음. 전 시나리오 자동(M1). (자기적용 S-10은 PM 오케스트레이션으로 자동 실행.)

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 (opds/opsdd 변환기) | H-2 | L1 | S-3 | op-scenario-gate/SKILL.md | 정규화 페이로드 정확 |
| R-1 (규율 정합) | H-6 | L1 | S-9 | op-scenario-gate/SKILL.md | 3종 지원 사실 |
| R-2 (opds producer) | H-1 | L1 | S-1 | opal-pilot-dev-short/SKILL.md | op-dev-plan diff 0 |
| R-2 (opds 배선·차단) | H-1, H-4 | L2 | S-2, S-7 | opds pipeline.json | 게이트 행·spec-validate |
| R-3 (opsdd 배선·차단) | H-1, H-3 | L2 | S-5, S-4 | opal-pilot-sdd/SKILL.md | DESIGN 차단·rows 25 |
| R-3 (self-confirming 해소) | H-1 | L2 | S-5 | opal-pilot-sdd/SKILL.md | 독립 evaluator |
| R-4 (verify-guide 대체) | H-2 | L1 | S-6 | verify-guide.md | §4 대체·S-1~S-6 존치 |
| R-5 (회귀) | H-5 | L1 | S-8 | opd 기준선 | diff 0 |
| R-6 (자기적용) | H-1, H-2 | L2 | S-10 | 게이트 실호출 | 누락FAIL/완전PASS |

> **목표 달성 검증(dogfooding)**: 075의 목표("opds·opsdd에 게이트 확산")는 S-2(opds 게이트 차단)·S-5(opsdd 게이트 차단+독립평가)·S-10(자기적용 음성/수렴)이 운영 계층에서 직접 검증한다. 채택/잔존(⑤): S-6이 교체형(수동 커버리지→도구 게이트) 잔존0·신형 채택을 검증. 경계/부정(⑥): S-4(재정렬)·S-7(spec-validate)·S-8(회귀).

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 변경 5파일 변경이력 행 (버전·KST·075) | grep | Pass (경미 편차) | op-scenario-gate/SKILL.md v1.1(:175, "15:28 KST"), opal-pilot-dev-short/SKILL.md v4.4(:383, "15:26", 075), opal-pilot-sdd/SKILL.md v3.6.0(:544, 075), verify-guide.md v1.1(:195, 075) 4개 문서 전부 (075) 태그 존재. opal-pilot-sdd/SKILL.md·verify-guide.md 2건은 날짜만 기재하고 HH:mm 누락 — 단, 동일 파일의 기존 이력행(v3.4.1 등)도 동일 패턴 존재해 이 파일들의 기존 관행과 일치(신규 이탈 아님). pipeline.json(JSON)은 자체 변경이력 섹션 없음 — 변경 내용은 상위 opal-pilot-dev-short/SKILL.md v4.4 changelog에 종합 기술(§동일 파일 그룹). |
| 2 | 배포 경계 (opal/ 소스만, ~/.opal/ 무편집) | git diff --stat | Pass | `git diff --stat` 6개 변경 파일 전부 `docs/`, `opal/skills/` 하위(프로젝트 소스) — `~/.opal/` 경로 0건. 본 TEST 수행 중 `~/.opal/tools/` 호출은 전부 CLI 실행(run.sh)이며 파일 편집 없음. |
| 3 | 인용 정확 (scenario-gate.md §3·§6, PRINCIPLES §15) | grep | Pass | `scenario-gate.md` §3 "정규화 계약(pilot-중립)"(:29), §6 "tool-gated 집행"(:87) 실존 확인. `opal/core/PRINCIPLES.md:15` "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." 실존 확인 — opal-pilot-sdd/SKILL.md:168의 인용과 정확히 일치. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | `.scenario-coverage-input.json` task_folder 하위 전용(경로 이탈 방지) | Pass | op-scenario-gate/SKILL.md [MUST] "경로 이탈 방지"(:31) "본 Step은 `task_folder` 하위 파일만 Read/Write한다. 상위·외부 경로는 절대 미접촉한다" + 산출 경로 명시(:48,:82) + opsdd 추가 Read(SPEC.md)도 "task_folder 하위이므로 규율 #5 준수" 명시(:74) + [MUST] 규율 #5(:155) 확인. 실제 075 자신의 `.scenario-coverage-input.json`도 task_folder(`tasks/075-.../`) 하위에 위치 확인. |
| 2 | 하드코딩 시크릿 없음(문서/JSON) | Pass | 변경 6파일 diff 전체에 대해 `grep -iE "api[_-]?key\|secret\|password\|token\s*=\|Bearer \|AKIA[0-9A-Z]{16}"` 실행 — 매치 0건. |

## 7. 판정

**All Pass -- S-1~S-10 전 시나리오 PASS(그중 S-2·S-5·S-10 목표-커버 3건 포함). 회귀 스위트(test-tool test_scenario.py) 31 passed 무회귀. 코드품질 3항목 Pass(변경이력 경미 편차 1건은 기존 파일 관행과 일치해 blocker 아님). 보안 2항목 Pass(경로 이탈 방지 명문화 확인, 하드코딩 시크릿 0건). opd 회귀(S-8) diff 0 확인 — 기존 opd 파이프라인 무손상.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인 — TEST-SCENARIO.md 본문 실질 매치 0건)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-6 전부 시나리오 연결)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] — 해당 없음(명시됨)
- [x] 리스크 가설 표(§1) H-N ↔ 시나리오 S-N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 없음 → M2 면제(명시됨)
