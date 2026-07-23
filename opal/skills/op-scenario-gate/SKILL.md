---
name: op-scenario-gate
description: |
  **TEST-SCENARIO(또는 pilot별 등가 산출물) 목표-커버리지 루브릭 게이트 루프 스킬**. 결정론 커버리지 체크(test-tool `scenario-coverage-check`)와 판단 루브릭(opal-evaluator-agent `scenario-rubric`)을 배선하여, 시나리오 집합이 태스크 목표를 실제로 커버하는지 tool-gated로 판정하고 종료조건(수렴/반복상한/무진전) 3종으로 루프를 컨트롤한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(1차 opal-pilot-dev STEP 3.5)가 TEST-SCENARIO 작성 직후 목표-커버 게이트를 통과시켜야 할 때.
  필수 입력: task_folder, producer_artifact, pilot, iteration. 보장 출력: {verdict: pass|rewrite|escalate, missing, scores, gaps[], report_path, iteration}.
---

# op-scenario-gate — 목표-커버리지 루브릭 게이트 루프

## 실행 컨텍스트

- **호출자**: 오케스트레이터(1차 적용 = `opal-pilot-dev` STEP 3.5, TEST-SCENARIO.md 작성 직후) — 루프 컨트롤 자체는 오케스트레이터가 수행하며, 본 스킬은 `verdict`를 반환할 뿐 게이트 행 mark는 하지 않는다(그 권한은 호출자·state-tool에 있다).
- **실행 주체**: 호출자(PM+캡틴)가 직접 수행한다. 서브에이전트 디스패치는 **Step 4의 opal-evaluator-agent 1건**뿐이다.
- **규칙 SSOT**: `opal/core/references/harness/scenario-gate.md` — **[MUST] Step 1에서 반드시 먼저 Read**한다. 6축 정의(§2)·정규화 계약(§3)·루프 프로세스(§4)·종료조건 3종(§5)·tool-gated 집행(§6)이 이 문서에 정의되어 있으며, 본 SKILL은 그 규칙을 실행 절차로 배선할 뿐 규칙을 재정의하지 않는다.
- **입력**:
  - `task_folder` — 태스크 폴더 경로 (예: `tasks/{NNN}-{태스크명}/`)
  - `producer_artifact` — Producer가 작성한 시나리오 산출물 경로 (1차 opd = `{task_folder}/TEST-SCENARIO.md`)
  - `pilot` — 정규화 변환기 선택 키 (1차 = `opd` 고정. 후속 확산 시 `oppl`/`opds`/`opsdd`/`oppd`)
  - `iteration` — 루프 회차 N (최초 호출 = 1)
- **출력**: `{verdict: pass|rewrite|escalate, missing, scores, gaps[], report_path, iteration}`

## 프로세스

### Step 1. 규칙 SSOT 로드

`opal/core/references/harness/scenario-gate.md` 전체를 Read한다. §2(6축+판정주체 분리) · §3(정규화 계약) · §5(종료조건 3종) · §6(tool-gated 집행)을 특히 숙지한다.

### Step 2. 정규화 페이로드 빌드 (pilot별 변환기)

**[MUST] 경로 이탈 방지**: 본 Step은 `task_folder` 하위 파일만 Read/Write한다. 상위·외부 경로는 절대 미접촉한다.

`pilot=opd`(1차 접합)의 변환 규칙:

| 정규화 필드 | 소스 |
|------------|------|
| `goal` | `TASK.md` 목표/배경 절의 목표 문장 |
| `requirements` | `TASK.md`의 R-ID 목록 (요구사항) |
| `features` | `PLAN.md`의 F-ID 목록 (기능) |
| `hypotheses` | `PLAN.md` 리스크 가설 표 및/또는 `producer_artifact` §1(가설 표)의 H-ID 목록 |
| `scenarios[]` | `producer_artifact` §4(AC↔가설↔계층↔시나리오 매핑 표)의 각 행 → `{id, covers_requirements, covers_features, covers_hypotheses, is_goal_scenario, is_adoption_scenario, is_boundary_scenario}` |

`scenarios[]` 판단 플래그 산정 기준 (호출자가 매핑 표·시나리오 본문을 읽고 판단):
- `is_goal_scenario`: 해당 시나리오가 사용자/운영 계층에서 태스크 목표를 직접 검증하면 `true`
- `is_adoption_scenario`: 대응 AC가 교체형 목표(구형 잔존0·신형 채택, `op-task/SKILL.md` 패턴)이고 그 채택/잔존을 검증하는 시나리오면 `true`
- `is_boundary_scenario`: 경계값·부정 경로를 검증하는 시나리오면 `true`

산출: `{task_folder}/.scenario-coverage-input.json` (task_folder 하위 전용 파일).

> **확장성 근거**: 후속 pilot(oppl/opds/opsdd/oppd) 확산 시, 위 표의 소스 열(TASK.md/PLAN.md/producer_artifact)만 해당 pilot의 등가 문서로 교체하는 변환기를 추가하면 §3 정규화 계약과 Step 3~6은 그대로 재사용된다. 1차 적용은 opd 단일 호출로 한정한다.

### Step 3. 결정론 커버리지 게이트 (결정론, ②③④)

```
test-tool resolve
test-tool scenario-coverage-check --coverage-input {task_folder}/.scenario-coverage-input.json
```

- **exit 0**: `all_covered:true` → Step 4(판단 게이트)로 진행
- **exit 16** (`coverage_unmet`): `detail.missing`(requirements/features/hypotheses 누락 목록) 수집 → Step 4를 **건너뛰고** Step 5(종료조건 판정)로 직행 (하드 게이트 — 판단축 채점 이전에 결정론 미충족으로 확정 FAIL)
- **exit 17** (`coverage_input_invalid`): Step 2 페이로드 빌드 오류 — 루프 종료조건이 아니라 **입력 오류 블로커**로 즉시 중단·보고한다 (재작성 루프 대상 아님, Step 2를 수정 후 재시도)

### Step 4. 판단 루브릭 게이트 (판단, ①⑤⑥ — exit 0일 때만)

`opal-evaluator-agent`를 `phase: scenario-rubric`으로 디스패치한다:

```
[WORKER]
task_folder: {task_folder}
phase: scenario-rubric
target_artifacts: [{producer_artifact}]
contract_path: {task_folder}/CONTRACT.md (있으면. opd 1차 접합은 통상 부재 — scenario-rubric은 Phase 2 CONTRACT 병합을 건너뛰므로 부재가 판정에 영향 없음)
timestamp: {ISO8601}
project_root: {프로젝트 루트}
iteration: {N}
scenario_source: {producer_artifact}
```

수신: `{scores: {goal, adoption, boundary}, average, gaps[], verdict: pass|fail}` + 보고서 `{task_folder}/SCENARIO-GATE-{N}.md`.

> **[MUST] Producer≠Evaluator**: 작성자(PM+캡틴, `producer_artifact` 작성자)와 채점자(`opal-evaluator-agent` 서브에이전트 디스패치)는 매 반복 분리 유지한다. 호출자가 스스로 판단축을 채점하여 pass를 선언할 수 없다.

### Step 5. 종료조건 3종 판정

이력 관리: `{task_folder}/.scenario-gate-history.json`에 매 반복 `{iteration, missing, gaps, verdict}` 레코드를 append한다(없으면 이번 반복 레코드로 생성). "무진전" 판정의 비교 기준선으로 쓴다.

판정 순서 (scenario-gate.md §5, 먼저 성립하는 조건 채택):

1. **수렴**: Step 3 exit 0 **AND** Step 4 `verdict: pass` (즉 §2 판단축 각 ≥1점 AND 평균 ≥1.5점) → `verdict: pass` 반환, 루프 종료.
2. **반복 상한**: `iteration`이 상한을 초과 → `verdict: escalate`(사유: 반복상한). **상한 수치는 scenario-gate.md §5(→ `opal/core/references/opal-harness.md` §1 "시나리오 목표-커버 게이트" 행)가 유일한 SSOT다 — 본 스킬 본문에 리터럴로 기재하지 않는다.** 호출 시 해당 문서를 조회해 판정한다.
3. **무진전**: 직전 반복(N-1) 이력 레코드가 존재하고, 이번 반복의 신호 집합(`missing`의 requirements∪features∪hypotheses 합집합 ∪ Step 4 `gaps[]`)이 직전 반복 대비 **동일하거나 개선되지 않은(원소 수 비감소)** 상태가 **연속 2회** 관측되면 → `verdict: escalate`(사유: 무진전). (신호 정의는 `opal/skills/opal-pilot-project-loop/references/loop-control.md` §4 준용)
4. **그 외 (recoverable)**: 위 세 조건에 해당하지 않으면 → `verdict: rewrite` + `gaps` 반환.

> **[MUST] 수치 비복제**: 반복 상한·무진전 임계는 항상 scenario-gate.md §5를 조회하여 판정하며, 그 수치를 본 SKILL 본문에 하드코딩하지 않는다.

### Step 6. 반환

```json
{
  "verdict": "pass | rewrite | escalate",
  "missing": { "requirements": [], "features": [], "hypotheses": [] },
  "scores": { "goal": 0, "adoption": 0, "boundary": 0 },
  "gaps": [],
  "report_path": "{task_folder}/SCENARIO-GATE-{N}.md",
  "iteration": 0
}
```

- `verdict: rewrite` → Producer(PM+캡틴)가 `gaps`를 반영해 `producer_artifact`를 재작성한 뒤, `iteration+1`로 Step 2부터 재호출한다(루프).
- `verdict: escalate` → 호출자가 캡틴(사용자)에게 에스컬레이션하고 루프를 중단한다. 자율 재시도하지 않는다.
- `verdict: pass` → 호출자가 두 증거(Step 3 exit 0 + Step 4 verdict pass)를 근거로 게이트 행(`test_scenario.scenario_gate`) mark를 진행한다. 본 스킬 자신은 mark를 수행하지 않는다.

## [MUST] 규율

| # | 규율 | 근거 |
|---|------|------|
| 1 | **tool-gated**: `verdict: pass`는 오직 (Step 3) test-tool exit 0 **AND** (Step 4) evaluator `verdict: pass` 두 증거가 모두 존재할 때만 성립한다. 호출자가 산문 판단만으로 pass를 생성할 수 없다. | `scenario-gate.md` §6, `opal/core/PRINCIPLES.md:15` |
| 2 | **Producer≠Evaluator**: 작성자(PM+캡틴)와 채점자(opal-evaluator-agent 서브에이전트 디스패치)를 매 반복 분리 유지한다. | `scenario-gate.md` §4, TASK.md §확정된 설계 방향 3 |
| 3 | **수치 비복제**: 반복 상한/무진전 임계 수치는 `scenario-gate.md` §5(→ `opal-harness.md` §1)를 참조만 하고 본 SKILL 본문에 리터럴로 복제하지 않는다. | `scenario-gate.md` §5, `loop-control.md:41,143` |
| 4 | **1차 opd 단일 호출**: 1차 적용은 opd STEP 3.5의 단일 호출로 한정한다. 후속 확산(oppl/opds/opsdd/oppd)은 Step 2의 pilot별 정규화 변환기만 추가하면 재사용된다(정규화 계약이 확장성 근거). | TASK.md §범위, `scenario-gate.md` §3 |
| 5 | **경로 이탈 방지**: Step 2 페이로드 빌드는 `task_folder` 하위 파일만 Read/Write한다. | PLAN §5.4 보안 |

## 결과 반환 형식

```json
{
  "verdict": "pass | rewrite | escalate",
  "missing": { "requirements": [], "features": [], "hypotheses": [] },
  "scores": { "goal": 0, "adoption": 0, "boundary": 0 },
  "gaps": [],
  "report_path": "{task_folder}/SCENARIO-GATE-{N}.md",
  "iteration": 0
}
```

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-23 | 최초 작성 — 루프 프로세스 6단계(정규화 빌드→coverage-check→evaluator→종료조건→반환) 배선, tool-gated·Producer≠Evaluator·수치 비복제·1차 opd 단일 호출 [MUST] 명문화 (073/F-004) |
