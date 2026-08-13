# PLAN: op-scenario-gate 목표-커버 게이트 확산 1차 (opds·opsdd)

> 작성일: 2026-07-23 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (ANALYSIS.md `features[]` 상당 다기능 + R-1~R-6 다분기)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

073에서 구축한 목표-커버 게이트 공유 컴포넌트(scenario-gate.md SSOT · op-scenario-gate 스킬 · test-tool `scenario-coverage-check` · opal-evaluator-agent `scenario-rubric`)를 opds·opsdd에 확산한다. **신규 tool/agent/pilot 0** — op-scenario-gate Step 2에 pilot별 정규화 변환기(opds·opsdd)를 추가하고, 각 오케스트레이터에 게이트 호출을 배선하는 것만이 신규 작업이다. test-tool·evaluator 코드는 pilot-중립이 이미 확인되어(ANALYSIS §1.2, `scenario.py:474-477`) 무변경 재사용한다. 편집 대상은 프로젝트 소스(`opal/...`) 마크다운/JSON 5개뿐이다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | op-scenario-gate Step 2 pilot 변환기 확장 (opds·opsdd 분기 + 규율/산문 정합) | R-1 | P0 | 없음 |
| F-002 | opds producer 확립 + 게이트 배선 (SKILL STEP 2 + pipeline.json 게이트 행) | R-2 | P0 | F-001 |
| F-003 | opsdd Phase 2 REVIEW 게이트 배선 (STATE 표 삽입·재정렬·`--row N` 전수 수정) | R-3 | P0 | F-001 |
| F-004 | opsdd verify-guide §4 커버리지 대체 (scenario-coverage-check, S-1~S-6 존치) | R-4 | P0 | F-001, F-003 |
| F-005 | 회귀 검증 (opd 1차 접합·SSOT·도구·기존 파이프라인 무손상 + opds spec-validate) | R-5 | P0 | F-001~F-004 |
| F-006 | 자기적용 실증 (누락→FAIL / 완전→PASS, opds 라이브 + opsdd 계약) | R-6 | P0 | F-001~F-004 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (변환기 확장) ─┬─ F-002 (opds 배선) ─────┐
                     └─ F-003 (opsdd 배선) ─┬─ F-004 (verify-guide) ─┤
                                            └────────────────────────┼─ F-005 (회귀)
                                                                     └─ F-006 (자기적용)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. (ANALYSIS §5 R-A~R-F를 가설로 승격)

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-002 opds producer 확립 | opds가 TEST-SCENARIO.md를 생성하지 않으면 게이트 `producer_artifact` 부재 → 게이트가 빈 산출물을 가리켜 오판/블로커 (ANALYSIS 발견①, R-A) | P0 | L1(산출물 검사) + L2(게이트 실호출) | S-1, S-4 |
| H-2 | F-001 opsdd 변환기 소스 | TEST-SCENARIOS.md만 읽고 SPEC.md를 안 읽으면 `requirements`(FR)·`hypotheses`(EC) 소스 부재 → 정규화 페이로드 불완전 → exit 17 오류 (ANALYSIS 발견②, R-B) | P1 | L1(정규화 페이로드 검사) | S-2, S-6 |
| H-3 | F-003 opsdd STATE 표 재정렬 | 게이트 행 삽입 후 `--row N` 리터럴 전수 수정 누락 → Phase 3~6 mark가 엉뚱한 행을 가리켜 기존 파이프라인 회귀 (ANALYSIS 발견④, R-C) | P0 | L1(`--row N` 전수 대조) + L2(init `--rows-from` 파싱 rows_count) | S-3, S-7 |
| H-4 | F-002 opds pipeline.json id 재정렬 | 스펙 위반(id 연속성·key 유일성·stage enum) 발생 시 `state-tool spec-validate` 실패 → init 거부 (ANALYSIS 발견④/R-D) | P1 | L1(`spec-validate` exit 0) | S-8 |
| H-5 | F-001 pilot 분기 추가 | 기존 `pilot=opd` 행/coverage-check/evaluator 회귀 — 코드 pilot-중립이라 위험 낮으나 표 편집이 opd 행을 훼손할 수 있음 (ANALYSIS R-E) | P1 | L1(opd 변환기 행 diff 무변경 확인) | S-9 |
| H-6 | F-001 [MUST] 규율 #4·산문 | 확산 후 "1차 opd 단일 호출" 문구가 사실과 불일치 (ANALYSIS 발견⑤, R-F) | P2 | L1(문구 정합 검사) | S-10 |

---

## 2. 기능별 분석

### F-001: op-scenario-gate Step 2 pilot 변환기 확장

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-scenario-gate/SKILL.md` | Step 2 정규화 변환기 표(현재 `pilot=opd` 단일) + 실행 컨텍스트 pilot enum + [MUST] 규율 #4 | 수정 |
| 참조(무변경) | `opal/core/references/harness/scenario-gate.md` §3 | pilot-중립 정규화 계약 SSOT | 참조만 |
| 참조(무변경) | `opal/skills/opal-pilot-sdd/references/spec-guide.md` §3-5~3-7 | opsdd 변환기 소스 ID 체계(FR/AC/EC) 확정 근거 | 참조만 |

#### 2.1.2 현재 구현

`op-scenario-gate/SKILL.md:29-50`가 Step 2다. `pilot=opd`(1차) 단일 변환 규칙 표만 존재하며(`SKILL.md:33-41`), 소스는 TASK.md(R)·PLAN.md(F/H)·producer_artifact(TEST-SCENARIO.md §1/§4). 산출물은 `{task_folder}/.scenario-coverage-input.json`. `SKILL.md:50` 산문("1차 적용은 opd 단일 호출로 한정")과 `SKILL.md:120` [MUST] 규율 #4, `SKILL.md:19` 입력 설명("`pilot` — 1차 = opd 고정")이 확산 후 사실과 불일치한다(ANALYSIS 발견⑤). Step 3~6(coverage-check→evaluator→종료조건→반환)은 pilot-중립이므로 무변경 재사용된다(`SKILL.md:52-111`).

#### 2.1.3 영향 범위

- 소비자: test-tool `scenario-coverage-check`(§2 ②③④)·opal-evaluator-agent `scenario-rubric`(§2 ①⑤⑥)는 정규화 페이로드만 소비 — pilot 필드 미검사(`scenario.py:474-477`) → 무변경.
- 호출자: opd STEP 3.5(`pilot: opd`) — 기존 행을 수정하지 않고 신규 행만 "추가"하면 회귀 없음(H-5).
- scenario-gate.md §3 정규화 계약이 변환기 추가의 확장성 근거(`SKILL.md:50`).

### F-002: opds producer 확립 + 게이트 배선

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-dev-short/SKILL.md` | STEP 2 PLAN 절차·PM Gate·STATE 미러 표·행 번호 산문 | 수정 |
| 배치(SSOT) | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | opds 10-task-step 정의 (task-step key 체계, 070 그룹A) | 수정 |
| 참조(무접촉) | `opal/skills/op-dev-plan/SKILL.md` | opd·opds 공용 PLAN 워커 스킬 — **[MUST] 미접촉**(opd 회귀 방지) | 미접촉 |
| 참조(선례) | `opal/skills/opal-pilot-dev/SKILL.md` STEP 3.5 + `references/pipeline.json` | opd 게이트 배선 동형 패턴 | 참조만 |

#### 2.2.2 현재 구현

opds 5단계(TASK/PLAN/EXECUTE/TEST/CLOSE, `opal-pilot-dev-short/SKILL.md:13`)에는 opd STEP 3.5에 대응하는 별도 TEST-SCENARIO 단계가 없다. STEP 2(`SKILL.md:39-71`)는 `op-dev-plan` 워커 디스패치 후 "op-dev-plan 워커가 PLAN.md와 TEST-SCENARIO.md를 **통합 작성**한다"(`SKILL.md:54`)고 서술한다. 그러나 `op-dev-plan/SKILL.md:6,35,146`은 TEST-SCENARIO.md를 출력 범위에서 **명시 제외**한다 — 두 SSOT 문서 상충으로 opds 실행 시 TEST-SCENARIO.md가 생성되지 않을 위험이 있다(ANALYSIS 발견①/H-1). pipeline.json(`references/pipeline.json:5-16`)은 10 task-step이며 게이트 행이 없다. SKILL 본문 명령은 task-step key 주소를 쓰나(v4.3), 산문 "행 N" 라벨과 미러 표는 숫자 기반이다(`SKILL.md:67,109,123,136,174,251-263,266`).

#### 2.2.3 영향 범위

- op-dev-plan/SKILL.md는 **절대 미접촉**(opd 공용, 회귀 방지 — [MUST] 캡틴 결정1). producer 확립은 opds STEP 2 서술 보강으로만 해결한다(TEST-SCENARIO.md를 PM+캡틴 페어가 op-dev-test-scenario 통일 형식으로 직접 작성 — opd STEP 3.5 동형).
- pipeline.json id 재정렬은 `state-tool spec-validate` 재검증 대상(H-4). key는 안정적이라 SKILL 본문 key 기반 명령은 무영향, 산문 "행 N" 라벨과 미러 표만 갱신 필요.

### F-003: opsdd Phase 2 REVIEW 게이트 배선

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터(SSOT) | `opal/skills/opal-pilot-sdd/SKILL.md` | 6단계 파이프라인 + REVIEW 절차 + STATE 표(24행, `--rows-from` 파싱 대상) + `--row N` 본문 리터럴 | 수정 |
| 참조(무변경) | `opal/tools/state-tool/state_tool.py` STAGE_ENUM | REVIEW stage 등록 확인(무변경) | 참조만 |

#### 2.3.2 현재 구현

opsdd 6단계(TASK→SPEC→REVIEW→DESIGN→EXECUTE-LOOP→VERIFY→CLOSE, `SKILL.md:23`). Phase 2 REVIEW는 PM 직접 3단계(구조 검증 S-1~S-6 / TEST-SCENARIOS.md 작성 / FR↔TS 커버리지 확인, `SKILL.md:142-158`)로 **워커 디스패치 없이 PM 단독**이다 — 작성·검증·게이트를 모두 PM이 수행하는 self-confirming 구조(ANALYSIS 발견③). opsdd는 pipeline.json 미전환 — `--rows-from opal/skills/opal-pilot-sdd/SKILL.md`로 SKILL.md 자신의 24행 파이프라인 현황판 표(`SKILL.md:348-373`)를 파싱하는 레거시 경로다(`SKILL.md:331`, `state-tool/README.md:55`). 본문 전 구간이 `--row N` 숫자 주소(`--row 6/7/15/16/18/19/24`, `#24`, `#18~#19`, `--after 17`)로 작성돼 있다(`SKILL.md:130-131,190-191,242,245-246,288,291,338,340,471`). REVIEW 시점에는 PLAN.md류 F/H 산출물이 없다 — SPEC.md의 FR/AC/EC가 유일 소스다(발견②).

#### 2.3.3 영향 범위

- STATE 표 행 삽입 시 이후 행 전수 재정렬 + 본문 `--row N` 리터럴 전수 수정 필요 — 누락 시 Phase 3~6 mark가 엉뚱한 행을 가리켜 회귀(H-3, 최고 리스크). 070 pipeline.json 전환은 **범위 밖**(별도 후속, [MUST] 캡틴 결정3).
- REVIEW의 게이트가 미통과이면 stage-transition guard가 DESIGN(Phase 3) 진입 mark를 거부해야 한다 — 게이트 행이 REVIEW stage에 속하므로 REVIEW 미완 = DESIGN 차단(발견③).

### F-004: opsdd verify-guide §4 커버리지 대체

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/opal-pilot-sdd/references/verify-guide.md` | REVIEW Phase 지침 — §4 수동 FR↔TS 커버리지 확인(대체 대상) / §2 S-1~S-6(존치) | 수정 |

#### 2.4.2 현재 구현

verify-guide.md §4(`137-164`)는 PM이 SPEC.md FR 목록 나열→AC 확인→TS 확인→갭 처리를 **수동**으로 수행하는 절차다. §4-2 커버리지 기준(AC/FR/EC 각 100%, `verify-guide.md:150-154`)은 scenario-coverage-check ②③④(requirements/features/hypotheses 누락 결정론 판정)와 정확히 동형이다. §2 구조 검증 S-1~S-6(`verify-guide.md:29-48`)은 SPEC.md 섹션·형식 검증으로 커버리지와 별개 관심사 — **존치**([MUST] 캡틴 결정4). §5 완료 판정(`166-172`)은 "S-1~S-4 + 커버리지 100%"를 조합하므로 커버리지 근거를 게이트로 교체하는 정합 갱신 필요.

#### 2.4.3 영향 범위

- §4 대체는 F-003 REVIEW 절차 배선과 짝을 이룬다(같은 게이트를 SKILL.md 표와 verify-guide 절차 양쪽에서 참조).
- S-1~S-6은 무변경 — 커버리지 게이트가 구조 검증을 대신하지 않는다.

### F-005 / F-006: 회귀·자기적용 (분석)

- F-005 회귀: 편집 5파일 외 무변경 확인 + opds pipeline.json `spec-validate` exit 0 + 기존 test-tool 스위트(073 8케이스, pilot-중립) PASS. opd 1차 접합(STEP 3.5·opd pipeline.json 행 10)·scenario-gate.md·test-tool·evaluator는 diff 0이어야 한다(ANALYSIS §3.2, R-E).
- F-006 자기적용: op-scenario-gate를 opds·opsdd 각 pilot 페이로드로 실제 호출 — 목표 시나리오 누락 페이로드→FAIL(exit 16 또는 evaluator fail), 완전 페이로드→PASS. 게이트 호출은 evaluator 서브에이전트 디스패치를 포함하므로 오케스트레이터(PM) 활동이다.

---

## 3. 기능별 설계

### F-001: op-scenario-gate Step 2 pilot 변환기 확장

#### 3.1.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-scenario-gate/SKILL.md` | 스킬 | Step 2에 `pilot=opds`·`pilot=opsdd` 변환기 표 추가(§3.1.2), 실행 컨텍스트 입력 설명 pilot enum 갱신, [MUST] 규율 #4·확장성 산문 정합 갱신, 변경이력 v1.1 | (→ D-1 §Step 2) |

#### 3.1.2 변환기 설계 (Step 2 신규 분기)

기존 `pilot=opd` 표(`SKILL.md:33-41`)는 **그대로 두고**(H-5 회귀 방지), 아래 두 분기 표를 그 아래에 additive로 추가한다.

**`pilot=opds` 변환 규칙** (opd 동형 — 소스 문서만 opds 산출물로 동일 매핑):

| 정규화 필드 | 소스 |
|------------|------|
| `goal` | `TASK.md` 목표/배경 절의 목표 문장 |
| `requirements` | `TASK.md`의 R-ID 목록 |
| `features` | `PLAN.md`의 F-ID 목록 |
| `hypotheses` | `PLAN.md` 리스크 가설 표 및/또는 `producer_artifact` §1 H-ID 목록 |
| `scenarios[]` | `producer_artifact` §4(AC↔가설↔계층↔시나리오 매핑 표) 각 행 |

- `producer_artifact` = `{task_folder}/TEST-SCENARIO.md` (opd와 동일 형식, → D-10 op-dev-test-scenario §1/§4).
- 플래그(`is_goal/adoption/boundary_scenario`) 산정 기준은 opd와 동일(`SKILL.md:43-46`).

**`pilot=opsdd` 변환 규칙** (SPEC.md 소스 — REVIEW 시점 PLAN.md 부재, 발견②/H-2):

| 정규화 필드 | 소스 |
|------------|------|
| `goal` | `TASK.md` 목표 문장 |
| `requirements` | `SPEC.md` `[FR-NN]` 목록 (§5, → D-11 spec-guide §3-5) |
| `features` | `SPEC.md` `AC-NN` 목록 (§6, → D-11 spec-guide §3-6) — opsdd에는 PLAN F 계층이 없어 AC를 기능 단위로 대체 |
| `hypotheses` | `SPEC.md` `[EC-NN]` 목록 (§7, → D-11 spec-guide §3-7) |
| `scenarios[]` | `producer_artifact`(TEST-SCENARIOS.md) 추적 매트릭스 각 행(`AC \| 시나리오 ID \| 유형 \| 설명 \| 상태`) → 아래 매핑 |

- `producer_artifact` = `{task_folder}/TEST-SCENARIOS.md`. **추가 Read**: `{task_folder}/SPEC.md`(FR/AC/EC 소스) — task_folder 하위이므로 [MUST] 규율 #5 경로 이탈 방지 준수(`SKILL.md:121`).
- `scenarios[]` 행별 매핑:
  - `covers_requirements` ← 해당 AC 상단 "대응 FR: FR-NN" 역참조(→ D-11 spec-guide §3-6 FR-AC 양방향 추적성 `spec-guide.md:123`)
  - `covers_features` ← 해당 행의 AC-ID 자신
  - `covers_hypotheses` ← 해당 행이 EC 기원(AC 컬럼 값이 `EC-NN`)일 때만 EC-ID, 아니면 빈 배열
  - `is_goal_scenario` ← 유형 `e2e` 또는 사용자/운영 계층 목표 검증 시 `true`
  - `is_adoption_scenario` ← 대응 AC가 교체형 목표 검증이면 `true`
  - `is_boundary_scenario` ← EC 기원 행 또는 경계/예외 케이스면 `true`
- 산출: `{task_folder}/.scenario-coverage-input.json` (opd/opds와 동일 파일, Step 3~6 무변경 소비).

> **[MUST] `opal/core/references/harness/scenario-gate.md` §3**: "게이트 입출력은 5 pilot(opd/opds/opsdd/oppl/oppd) 어디에서 호출되든 동일한 형태를 따른다. pilot별 문서 형식에서 이 계약으로의 변환 책임은 호출 스킬(op-scenario-gate)이 지며, test-tool·evaluator는 pilot-중립 페이로드만 소비한다." → 변환기 추가만으로 확산 완결, 도구/에이전트 무변경. (→ D-2 §3)

#### 3.1.3 산문·규율 정합 갱신 (발견⑤/H-6)

- `SKILL.md:19` 입력 설명: "`pilot` — 정규화 변환기 선택 키 (1차 = `opd` 고정. 후속 확산 시 ...)" → "지원 pilot: `opd`/`opds`/`opsdd` (oppl 제외 확정·oppd 2차 유예)".
- `SKILL.md:50` 확장성 근거 산문 말미 "1차 적용은 opd 단일 호출로 한정한다." → "opds·opsdd 확산 완료(3종 지원). oppl은 자체 표면-게이트+독립평가자 보유로 제외 확정, oppd는 2차 유예."
- `SKILL.md:120` [MUST] 규율 #4: "1차 opd 단일 호출" → "다중 pilot 지원: opd(STEP 3.5)·opds(STEP 2)·opsdd(Phase 2 REVIEW) 3종 접합. 확산은 Step 2 pilot 변환기 추가만으로 재사용(정규화 계약이 확장성 근거). oppl 제외·oppd 2차."
  - 근거: 이 갱신은 6축·정규화 계약·tool-gated·Producer≠Evaluator 원칙 자체를 변경하지 않는 **사실 서술 갱신**이므로 R-5(회귀 없음) 위반이 아니다(ANALYSIS 발견⑤).

> **[MUST] `opal/core/references/harness/scenario-gate.md` §6**: "게이트 PASS는 test-tool exit 0 AND evaluator verdict pass 두 증거가 모두 존재할 때만 성립." — 확산 대상 pilot 전부가 이 tool-gated 계약을 계승하며 변경하지 않는다. (→ D-2 §6)

#### 3.1.4 환경 변경 / 3.1.5 배치·마이그레이션

해당 없음.

#### 3.1.6 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC(opds 페이로드) | 산출물 검사 | `pilot=opds` 호출 시 `.scenario-coverage-input.json`이 `{goal,requirements,features,hypotheses,scenarios[]}` 정확 생성 (opd 동형) |
| TS-002 | R-1 AC(opsdd 페이로드) | 산출물 검사 | `pilot=opsdd` 호출 시 SPEC.md FR/AC/EC + TEST-SCENARIOS.md 매트릭스로부터 정규화 페이로드 정확 생성, covers_requirements=FR 역참조 |
| TS-010 | R-1(정합) | 산출물 검사 | `SKILL.md` [MUST] 규율 #4·산문·pilot enum이 3종 지원 사실과 일치, opd 변환기 행 diff 0 |

### F-002: opds producer 확립 + 게이트 배선

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 오케스트레이터 | STEP 2에 (a) TEST-SCENARIO.md producer 확립 서술 (b) op-scenario-gate 호출 절차 삽입; PM Gate mark 행번호 정합; STATE 미러 표 10→11행 + 게이트 행; 산문 "행 N" 라벨 +1 재정렬; 변경이력 v4.4 | (→ D-4, D-8 STEP 3.5) |
| 2 | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | 배치 | `plan.scenario_gate` 게이트 행 삽입(plan.plan_md 직후) + id 재정렬 | (→ D-8 opd pipeline.json id 10, D-9) |

#### 3.2.2 설계 상세

**(a) producer 확립** ([MUST] 캡틴 결정1, 옵션1 — op-dev-plan/SKILL.md 미접촉):

`opal-pilot-dev-short/SKILL.md:54`의 "op-dev-plan 워커가 PLAN.md와 TEST-SCENARIO.md를 통합 작성한다"를 아래로 교체한다.

> op-dev-plan 워커는 PLAN.md만 작성한다(op-dev-plan/SKILL.md가 TEST-SCENARIO.md를 출력 범위에서 제외). PLAN.md 수신 후, **알투(PM) + 캡틴 페어**가 `op-dev-test-scenario/SKILL.md`의 "TEST-SCENARIO.md 통일 형식"(§1 리스크 가설 표 / §4 AC↔가설↔계층↔시나리오 매핑 표)을 명시 참조하여 TEST-SCENARIO.md를 직접 작성한다. 이는 self-confirming 방지를 위해 PLAN 워커(opal-plan-agent)와 다른 작성자가 수행하는 opd STEP 3.5 동형 절차다. (문서 전용 작업 시 스킵 — 이 경우 게이트도 자연 스킵.)

- 근거: `op-dev-plan/SKILL.md`는 opd·opds 공용이며 TEST-SCENARIO.md를 명시 제외한다(`op-dev-plan/SKILL.md:6,35,146`). opds 오케스트레이터가 producer를 책임지도록 확정하여 `producer_artifact` 존재를 보장한다(발견①/H-1 해소). op-dev-plan/SKILL.md는 **미접촉** → opd 무영향.

**(b) 게이트 배선** — STEP 2 PLAN 절차에 opd STEP 3.5(→ D-8 `opal-pilot-dev/SKILL.md:95-100`) 동형 삽입. TEST-SCENARIO.md 작성 완료 후, PM Gate 직전에:

```
목표-커버 게이트: state-tool advance <task-path> --task-step plan.scenario_gate 호출 후 op-scenario-gate 스킬 호출.
  - 탐색: {프로젝트}/.opal/skills/op-scenario-gate/SKILL.md → ~/.opal/skills/op-scenario-gate/SKILL.md
  - 입력: task_folder, producer_artifact={task_folder}/TEST-SCENARIO.md, pilot: opds, iteration(최초=1)
  - verdict: pass  → 게이트 행 mark (state-tool mark <task-path> --task-step plan.scenario_gate --done — Step 3 exit 0 AND Step 4 verdict pass 두 증거 근거로만 mark, 산문 판단 mark 금지)
  - verdict: rewrite → PM+캡틴이 gaps 반영해 TEST-SCENARIO.md 재작성 후 iteration+1로 재호출 (루프)
  - verdict: escalate → 사용자 에스컬레이션, 자율 재시도 금지
```

**pipeline.json 게이트 행** — id 3(`plan.plan_md`) 직후, id 4(`plan.pm_gate`) 직전 삽입, 이후 id +1 재정렬(→ D-9 `pipeline.json:5-16`):

```
{ "id": 3, "key": "plan.plan_md",      "stage": "PLAN", "item": "작업" }
{ "id": 4, "key": "plan.scenario_gate","stage": "PLAN", "item": "목표-커버 게이트" }   ← 신규
{ "id": 5, "key": "plan.pm_gate",      "stage": "PLAN", "item": "PM Gate" }            ← 4→5
{ "id": 6, "key": "plan.user_confirm", "stage": "PLAN", "item": "사용자 확인" }         ← 5→6
{ "id": 7, "key": "execute.implement", "stage": "EXECUTE", ... }                       ← 6→7
... (id 7→8, 8→9, 9→10, 10→11 재정렬, 총 11행)
```

- 배치 이유: 게이트 행이 PLAN stage에 속해야 stage-transition guard가 EXECUTE 진입(execute.implement mark)을 게이트 미완 시 구조적으로 차단한다(opd 선례 동형, `opal-pilot-dev/SKILL.md:309` [MUST] 주석). PM Gate 앞에 두어 PM Gate가 tool-gated 게이트 증거 위에서 검증하도록 한다.
- `pm_gate[]` 배열(`pipeline.json:17-20`)은 stage 기반 매칭이라 id 재정렬 무영향. PLAN checklist에 "목표-커버 게이트 verdict:pass" 항목 추가(R-D 중복 서술 정리).
- key는 안정적 — SKILL 본문 key 기반 명령(`--task-step plan.user_confirm` 등)은 무영향.

**SKILL.md STATE 미러 표 + 산문 행번호** (`SKILL.md:251-263,67,109,123,136,174,266`):

STATE 미러 표에 게이트 행 삽입 + 이후 행 +1 (10→11행):
```
| 4 | PLAN | 목표-커버 게이트 | ⬜ | - |   ← 신규
| 5 | PLAN | PM Gate | ... |               ← 4→5
| 6 | PLAN | 사용자 확인 | ... |            ← 5→6
| 7 | EXECUTE | 작업 | ... |               ← 6→7 ... 11 CLOSE
```
산문 "행 N" +1 갱신: `SKILL.md:67` 행4→행5, `:109` 행6→행7, `:123` 행7→행8, `:136` 행8→행9, `:174` 행10→행11, `:266` `--after 9`→`--after 10`. `:265` 흡수 주석에 게이트 행 mark 조건([MUST] verdict:pass만 mark, 미완 시 guard가 EXECUTE 진입 거부) 추가.

#### 3.2.3 환경 / 3.2.4 배치

pipeline.json 변경은 `state-tool spec-validate opal/skills/opal-pilot-dev-short/references/pipeline.json` exit 0 재검증 대상(F-005/H-4). 마이그레이션 없음.

#### 3.2.6 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-003 | R-2(a) producer | 산출물 검사 | opds STEP 2 서술이 TEST-SCENARIO.md 작성 주체(PM+캡틴)를 명시, op-dev-plan/SKILL.md diff 0 |
| TS-004 | R-2(b) 배선 | 기능 테스트 | pipeline.json에 `plan.scenario_gate`(PLAN stage) 존재, guard가 게이트 미완 시 execute.implement mark 거부 |
| TS-008 | R-2 spec | 산출물 검사 | `state-tool spec-validate` exit 0, rows_count 11 |

### F-003: opsdd Phase 2 REVIEW 게이트 배선

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-sdd/SKILL.md` | 오케스트레이터 | STATE 표에 게이트 2행 반영(§3.3.2), 이후 행 재정렬, `--row N`/`#N`/`--after N` 본문 리터럴 전수 수정, Phase 2 REVIEW 절차 배선, 6단계 요약 갱신, 변경이력 v3.6.0 | (→ D-6, D-8) |

#### 3.3.2 STATE 표 재구성 설계 (DD-1)

> **[MUST] 설계 결정 DD-1**: opsdd는 pipeline.json 미전환 최소변경([MUST] 캡틴 결정3). 게이트는 REVIEW의 두 tool-gated 증거를 두 행으로 명시화한다 — 행 10을 scenario-coverage-check(결정론 ②③④)로 **교체**하고, 그 직후 신규 행에서 op-scenario-gate(evaluator ①⑤⑥ 포함 verdict)를 배치한다(ANALYSIS 발견③). 이는 opsdd REVIEW가 원래 "FR↔TS 커버리지 확인"을 독립 단계로 가졌던 구조와 정합하며, "게이트 행 삽입 + 이후 행 재정렬" 결정을 순변경 +1로 구현한다. op-scenario-gate는 **1회 호출**이며 Step 3(coverage exit 0)이 행 10, Step 4(verdict pass)가 행 11 증거가 된다(scenario-gate.md §6 "두 증거"의 STATE 가시화).

현행 24행 → 신규 25행. REVIEW 구간:

```
| 8  | REVIEW | 구조 검증 (S-1~S-6) |                          ← 무변경 (S-1~S-6 존치)
| 9  | REVIEW | TEST-SCENARIOS.md 작성 |                       ← 무변경 (producer)
| 10 | REVIEW | 커버리지 게이트 (scenario-coverage-check) |     ← "FR↔TS 커버리지 확인" 교체 (R-4)
| 11 | REVIEW | 목표-커버 게이트 (op-scenario-gate evaluator) |  ← 신규 (R-3 독립 evaluator)
| 12 | REVIEW | PM Gate |                                      ← 11→12
| 13 | REVIEW | 사용자 확인 |                                   ← 12→13
| 14~25 | ... DESIGN/EXECUTE/VERIFY/CLOSE |                     ← 13~24 전부 +1
```

**본문 `--row N`/`#N`/`--after N` 전수 수정** (rows ≥ 11 은 +1):

| 위치 | 현재 | 변경 | 대상 |
|------|------|------|------|
| `SKILL.md:130` | `--row 6` | (불변) | SPEC PM Gate (row 6 < 11) |
| `SKILL.md:131` | `--row 7` | (불변) | SPEC 사용자 확인 |
| `SKILL.md:190` | `--row 15` | `--row 16` | DESIGN PM Gate |
| `SKILL.md:191` | `--row 16` | `--row 17` | DESIGN 사용자 확인 |
| `SKILL.md:242` | `#18~#19` | `#19~#20` | EXECUTE Gate 설명 |
| `SKILL.md:245` | `--row 18` | `--row 19` | EXECUTE PM Gate |
| `SKILL.md:246` | `--row 19` | `--row 20` | EXECUTE 사용자 확인 |
| `SKILL.md:288` | `--row 24` | `--row 25` | CLOSE DONE.md |
| `SKILL.md:291,471` | `#24` | `#25` | CLOSE 게이트 제약 |
| `SKILL.md:338` | `#17` | `#18` | R-13 ACT 실행 행 |
| `SKILL.md:340` | `--after 17` | `--after 18` | R-13 ACT add-row |
| `SKILL.md:366` | 표 행 17 EXECUTE ACT 실행 | 행 18 | STATE 표 |
| `SKILL.md:334,336` | "24행" | "25행" | rows_count 서술 |

> **[MUST] 회귀 방지**: 위 리터럴 전수 수정 누락 시 Phase 3~6 mark가 엉뚱한 행을 가리켜 기존 파이프라인이 깨진다(H-3 최고 리스크). EXECUTE에서 `--rows-from` init 후 `rows_count: 25` 파싱 정상 확인이 완료 기준(F-005 회귀 항목).

#### 3.3.3 Phase 2 REVIEW 절차 배선

`SKILL.md:142-158` REVIEW 3단계 흐름을 4단계로 재작성:

```
1. 구조 검증 (PM 직접) — verify-guide.md §2 S-1~S-6 (무변경 존치)
2. TEST-SCENARIOS.md 작성 (PM+캡틴 페어, producer)
3. 목표-커버 게이트: op-scenario-gate 호출 (pilot: opsdd)
   - 입력: task_folder, producer_artifact={task_folder}/TEST-SCENARIOS.md, pilot: opsdd, iteration
   - Step 3 coverage-check exit 0 → 행 10 mark (커버리지 게이트 = 구 수동 FR↔TS 대체)
   - Step 4 evaluator verdict pass → 행 11 mark (독립 evaluator = self-confirming 해소, Producer≠Evaluator)
   - verdict: rewrite → TEST-SCENARIOS.md 재작성 후 iteration+1 재호출
   - verdict: escalate → 사용자 에스컬레이션
4. PM Gate → 사용자 Gate (게이트 두 증거 위에서 검증)
```

6단계 요약(`SKILL.md:44-45`)의 "→ FR↔TS 커버리지 확인" → "→ 목표-커버 게이트(coverage-check + 독립 evaluator)"로 갱신.

> **[MUST] `opal/core/PRINCIPLES.md:15` (Enforce, don't just advise)**: opsdd REVIEW self-confirming 해소는 산문 지침이 아니라 독립 evaluator 서브에이전트 디스패치로 **구조 집행**한다 — PM은 두 도구 증거 없이 게이트 통과를 선언할 수 없다. (→ D-2 §6)

#### 3.3.4 배치

DESIGN(Phase 3) 진입 차단: 게이트 행(10·11)이 REVIEW stage에 속하므로 REVIEW 미완 시 stage-transition guard가 DESIGN 첫 행(#14 워커 디스패치) mark를 거부한다(발견③, `state_tool.py` `stage_transition_violation`).

#### 3.3.6 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R-3 배선 | 기능 테스트 | REVIEW 절차가 op-scenario-gate(pilot:opsdd) 호출, verdict:pass 후에만 DESIGN 진입 — 게이트 미통과 시 guard가 DESIGN mark 거부 |
| TS-007 | R-3 재정렬 | 산출물 검사 | `--row N`/`#N`/`--after N` 전수 수정, `--rows-from` init `rows_count: 25` 파싱 정상 |
| TS-011 | R-3 self-confirming | 산출물 검사 | 독립 evaluator(opal-evaluator-agent)가 채점 주체 — Producer(PM)≠Evaluator 명시 |

### F-004: opsdd verify-guide §4 커버리지 대체

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-sdd/references/verify-guide.md` | 가이드 | §4 수동 FR↔TS 커버리지 확인 절 → scenario-coverage-check 게이트 안내로 대체, §5 완료 판정 커버리지 근거 정합, S-1~S-6(§2) 무변경, 변경이력 행 신설 | (→ D-7) |

#### 3.4.2 설계 상세

`verify-guide.md:137-164` §4 "FR↔TS 커버리지 확인"을 재작성:

> ## 4. 목표-커버 게이트 (scenario-coverage-check + 독립 evaluator)
> TEST-SCENARIOS.md 작성 완료 후, 수동 FR↔TS 커버리지 확인 대신 op-scenario-gate(pilot: opsdd)를 호출한다. 커버리지 판정은 test-tool `scenario-coverage-check`가 결정론으로 수행한다:
> - `requirements`(SPEC FR) / `features`(SPEC AC) / `hypotheses`(SPEC EC) ↔ 시나리오 매핑 누락을 exit 0(전커버)/16(coverage_unmet)로 판정 — 기존 §4-2 커버리지 기준(AC/FR/EC 100%)과 동형이나 도구 집행.
> - exit 16이면 `detail.missing`을 gaps로 반영해 TEST-SCENARIOS.md 재작성 또는 SPEC.md 보완 후 재호출.
> - 목표 달성 관점(①⑤⑥)은 opal-evaluator-agent가 별도 채점(수동 확인이 놓치던 관점 편향 보강, scenario-gate.md §1 070 사건 근거).
> 규칙 SSOT: `opal/core/references/harness/scenario-gate.md`.

- §5 완료 판정 표(`verify-guide.md:166-172`)의 "커버리지 100%" 조건을 "목표-커버 게이트 verdict:pass(coverage exit 0 AND evaluator pass)"로 정합 갱신.
- §2 S-1~S-6(`29-48`)·§6 의미적/도메인 검증(`176-196`)은 **무변경 존치** — 구조/의미 검증은 커버리지와 별개 관심사([MUST] 캡틴 결정4).
- 문서 하단에 변경이력 표 신설(부재 시): `| v1.1 | 2026-07-23 | §4 수동 FR↔TS 커버리지 → scenario-coverage-check 게이트 대체, S-1~S-6 존치 (075) |`.

> **[MUST] TASK.md §제약**: "opsdd verify-guide 커버리지 대체 시 SPEC 구조검증(S-1~S-6) 존치" — S-1~S-6 절대 미변경. (→ TASK.md §제약 조건)

#### 3.4.6 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | R-4 대체 | 산출물 검사 | verify-guide §4가 scenario-coverage-check 게이트로 대체, §2 S-1~S-6 diff 0, 변경이력 행 존재 |

### F-005: 회귀 검증

#### 3.5.1 설계

- 편집 5파일 외 무변경: `git diff --name-only`가 정확히 5파일(op-scenario-gate SKILL, opds SKILL, opds pipeline.json, opsdd SKILL, verify-guide) + PLAN 산출물만.
- opd 무손상: `opal/skills/opal-pilot-dev/SKILL.md`·`references/pipeline.json`·`scenario-gate.md`·`op-scenario-gate/SKILL.md`의 `pilot=opd` 행·`opal/tools/test-tool/`·`opal/agents/opal-evaluator-agent/` diff 0(R-E, 코드 pilot-중립).
- opds pipeline.json: `state-tool spec-validate opal/skills/opal-pilot-dev-short/references/pipeline.json` exit 0.
- 도구 스위트: test-tool `scenario-coverage-check` 기존 8케이스(073) PASS(pilot-중립, 무변경).

#### 3.5.2 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-009 | R-5 회귀 | 회귀 테스트 | 편집 5파일 외 diff 0, opd 접합 무손상, spec-validate exit 0, 기존 test-tool 스위트 PASS |

### F-006: 자기적용 실증

#### 3.6.1 설계

op-scenario-gate를 각 pilot 페이로드로 실제 호출하여 음성/수렴을 실증한다(오케스트레이터=PM 활동, evaluator 디스패치 포함).

- **opds (대표 라이브 실증)**: 목표 시나리오 누락 TEST-SCENARIO.md → `pilot=opds` 게이트 호출 → coverage exit 16 또는 evaluator goal<1 → verdict FAIL(rewrite/escalate) → EXECUTE 진입 차단 확인. 목표 시나리오 복원 → verdict pass → 게이트 행 mark 가능.
- **opsdd (계약 실증)**: SPEC.md FR/AC/EC + TEST-SCENARIOS.md 매트릭스로 `pilot=opsdd` 변환기가 정규화 페이로드를 정확 생성하는지(TS-002) + 누락 페이로드 FAIL / 완전 페이로드 PASS 계약 검증.

#### 3.6.2 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R-6 음성 | 통합 테스트 | opds·opsdd 각 목표 시나리오 누락 페이로드 → 게이트 verdict FAIL → 다음 단계(EXECUTE/DESIGN) 진입 차단 |
| TS-013 | R-6 수렴 | 통합 테스트 | 완전 페이로드 → coverage exit 0 AND evaluator pass → verdict pass → 게이트 행 mark 가능 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-task-agent | 순차 | 변환기 확장 — opds·opsdd 배선의 선행 |
| 2 | F-002, F-003, F-004 | 2, 3, 4, 5 | opal-task-agent | 부분 병렬 | opds(2) ∥ opsdd(3→4). 서로 다른 파일군 |
| 3 | 문서 | 6 | PM 직접 | 순차 | PROJECT.md 확산 반영 (Phase 1~2 후) |
| 4 | F-005 | 7 | opal-test-agent | 순차 | 회귀 (전 기능 후) |
| 5 | F-006 | 8 | PM 직접 | 순차 | 자기적용 실증 (게이트 실호출) |

### 4.2 실행 체크리스트

> 총 8개 Step | Phase 5개 | 실행 모드: 복잡

#### Step 1: op-scenario-gate Step 2 pilot 변환기 확장
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-scenario-gate/SKILL.md`
- **작업 내용**: Step 2에 `pilot=opds`(opd 동형)·`pilot=opsdd`(SPEC.md 소스) 변환기 표 additive 추가(§3.1.2); producer_artifact/추가 Read(SPEC.md) 명시; 실행 컨텍스트 pilot enum(:19)·확장성 산문(:50)·[MUST] 규율 #4(:120)를 3종 지원 사실로 정합 갱신(§3.1.3); 변경이력 v1.1. 기존 `pilot=opd` 행은 diff 0 유지.
- **완료 기준**: opds·opsdd 변환기 표 존재 + 소스 매핑 정확(FR/AC/EC, covers_* 역참조 규칙 기재); opd 행 무변경; 규율 #4·산문·enum 정합; scenario-gate.md §3·§6 인용.
- **테스트**: TS-001, TS-002, TS-010
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: opds producer 확립 + 게이트 배선 (SKILL + pipeline.json)
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 오케스트레이터, 배치
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`, `opal/skills/opal-pilot-dev-short/references/pipeline.json`
- **작업 내용**: (a) STEP 2 :54 서술을 PM+캡틴 TEST-SCENARIO.md 직접 작성(op-dev-test-scenario 통일 형식 참조)으로 교체 — op-dev-plan/SKILL.md 미접촉; (b) STEP 2에 op-scenario-gate(pilot:opds) 호출 절차 삽입(§3.2.2); pipeline.json `plan.scenario_gate` 행 삽입 + id 재정렬(11행); STATE 미러 표 게이트 행 + 산문 "행 N" +1 전수(:67/109/123/136/174/266) + :265 게이트 mark 조건 주석; PM Gate checklist 게이트 항목; 변경이력 v4.4.
- **완료 기준**: pipeline.json `plan.scenario_gate`(PLAN stage) 존재·`spec-validate` exit 0; op-dev-plan/SKILL.md diff 0; SKILL 행번호·미러 표 정합; STEP 2가 producer 확립+게이트 호출 명시.
- **테스트**: TS-003, TS-004, TS-008
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: opsdd Phase 2 REVIEW 게이트 배선 (STATE 표 + `--row N` 전수)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-sdd/SKILL.md`
- **작업 내용**: STATE 표 행 10 교체(커버리지 게이트) + 행 11 신설(목표-커버 게이트) + 이후 24→25행 재정렬(§3.3.2); `--row N`/`#N`/`--after N`/"24행" 리터럴 전수 수정(§3.3.2 표); Phase 2 REVIEW 절차 4단계 배선(§3.3.3); 6단계 요약(:44-45) 갱신; 변경이력 v3.6.0.
- **완료 기준**: `--rows-from` init `rows_count: 25` 파싱 정상; `--row N` 리터럴 전수 정합(Phase 3~6 행 참조 무손상); REVIEW가 op-scenario-gate(pilot:opsdd) 호출·verdict:pass 후 DESIGN 진입 명시; PRINCIPLES §15 인용.
- **테스트**: TS-005, TS-007, TS-011
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: opsdd verify-guide §4 커버리지 대체
- [x] 완료
- **소속 기능**: F-004
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-sdd/references/verify-guide.md`
- **작업 내용**: §4 수동 FR↔TS 커버리지 확인 → scenario-coverage-check 게이트 안내로 재작성(§3.4.2); §5 완료 판정 커버리지 근거 정합; §2 S-1~S-6·§6 무변경; 변경이력 표 신설/행 추가.
- **완료 기준**: §4가 게이트 대체 서술; §2 S-1~S-6 diff 0; §5 verdict:pass 근거; 변경이력 행 존재.
- **테스트**: TS-006
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 3

#### Step 5: (Step 2·3·4 배치 조정) — Phase 2 병렬 디스패치 통제
- [ ] 완료
- **소속 기능**: F-002, F-003, F-004
- **영역**: 공통
- **agent**: PM 직접
- **파일**: (조정만)
- **작업 내용**: Step 2(opds 파일군) ∥ Step 3(opsdd SKILL) 병렬 디스패치; Step 4는 Step 3 완료 후 순차(같은 opsdd 관심사, 게이트 참조 일관성). 파일 충돌 없음 확인.
- **완료 기준**: Step 2·3·4 changed_files 병합, 파일 중복 편집 0.
- **테스트**: -
- **실행 방법**: direct
- **의존**: Step 1

#### Step 6: docs/PROJECT.md 확산 반영
- [ ] 완료
- **소속 기능**: 문서
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`
- **작업 내용**: §TEST-SCENARIO 목표-커버 게이트 섹션의 "1차 opd 선적용" → "opd·opds·opsdd 접합(oppl 제외·oppd 2차)" 정합; op-scenario-gate 행 설명 "5 pilot 재사용 단일 호출 지점(1차 opd)" 갱신; 변경이력 행 추가(075).
- **완료 기준**: PROJECT.md가 확산 사실 반영, 변경이력 행.
- **테스트**: -
- **실행 방법**: direct
- **의존**: Step 2, Step 3, Step 4

#### Step 7: 회귀 검증
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: (검증만)
- **작업 내용**: `git diff --name-only` 편집 파일 한정 확인(opd 접합·scenario-gate.md·test-tool·evaluator diff 0); `state-tool spec-validate` opds pipeline.json exit 0; opsdd `--rows-from` init rows_count 25 검증; test-tool `scenario-coverage-check` 기존 스위트 실행.
- **완료 기준**: opd 무손상 diff 0, spec-validate exit 0, opsdd rows_count 25, 기존 스위트 PASS.
- **테스트**: TS-009
- **실행 방법**: sub-agent
- **의존**: Step 2, 3, 4, 6

#### Step 8: 자기적용 실증
- [ ] 완료
- **소속 기능**: F-006
- **영역**: 공통
- **agent**: PM 직접
- **파일**: (게이트 실호출)
- **작업 내용**: opds(대표 라이브) — 목표 시나리오 누락 페이로드로 op-scenario-gate(pilot:opds) 호출→verdict FAIL/EXECUTE 차단 확인, 복원→pass; opsdd(계약) — pilot:opsdd 변환기 정규화 페이로드 정확 생성 + 누락 FAIL/완전 PASS. evaluator 디스패치 포함(오케스트레이터 활동).
- **완료 기준**: 각 pilot 누락→FAIL·완전→PASS 실증, 다음 단계 진입 차단 확인.
- **테스트**: TS-012, TS-013
- **실행 방법**: direct
- **의존**: Step 2, 3, 4

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2·3·4 | 변환기(op-scenario-gate)가 opds·opsdd 게이트 호출의 선행 계약 |
| Step 2 ∥ Step 3 | opds 파일군(opds SKILL+pipeline.json)과 opsdd SKILL은 독립 파일 — 충돌 없음 |
| Step 3 → Step 4 | 같은 opsdd 관심사, verify-guide §4가 SKILL REVIEW 절차 게이트를 참조 — 일관성 위해 순차 |
| Step 6 ← Step 2·3·4 | PROJECT.md 확산 반영은 실제 배선 완료 후 |
| Step 7·8 ← 전 기능 | 회귀·자기적용은 배선 완결 후 검증 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | opds·opsdd 변환기 정규화 페이로드 정확성 | TS-001, TS-002 | `{goal,requirements,features,hypotheses,scenarios[]}` 정확 생성, opsdd covers_requirements=FR 역참조 |
| F-001 | opd 회귀·규율 정합 | TS-010 | opd 변환기 행 diff 0, [MUST] 규율 #4·enum 3종 지원 사실 일치 |
| F-002 | opds producer 확립 | TS-003 | STEP 2가 PM+캡틴 TEST-SCENARIO.md 작성 명시, op-dev-plan/SKILL.md diff 0 |
| F-002 | opds 게이트 배선·차단 | TS-004, TS-008 | plan.scenario_gate(PLAN stage) 존재, guard가 EXECUTE 차단, spec-validate exit 0 |
| F-003 | opsdd 게이트 배선·차단 | TS-005 | REVIEW가 op-scenario-gate 호출, verdict:pass 후 DESIGN 진입 |
| F-003 | opsdd 재정렬 무손상 | TS-007 | `--row N` 전수 정합, rows_count 25 |
| F-003 | self-confirming 해소 | TS-011 | 독립 evaluator 채점 주체, Producer≠Evaluator |
| F-004 | verify-guide §4 대체·S-1~S-6 존치 | TS-006 | §4 게이트 대체, §2 diff 0 |
| F-005 | 회귀 0 | TS-009 | opd 접합·SSOT·도구·evaluator diff 0, 기존 스위트 PASS |
| F-006 | 자기적용 음성/수렴 | TS-012, TS-013 | 누락→FAIL/차단, 완전→PASS |

### 5.2 회귀 테스트
- [ ] `pilot=opd` 변환기 행·opd STEP 3.5·opd pipeline.json 행 10 diff 0
- [ ] `op-dev-plan/SKILL.md` 완전 미접촉 (diff 0) — opd 회귀 방지
- [ ] scenario-gate.md·test-tool·opal-evaluator-agent diff 0 (pilot-중립)
- [ ] opds `state-tool spec-validate` exit 0 (H-4)
- [ ] opsdd `--rows-from` init `rows_count: 25` + Phase 3~6 `--row N` 정합 (H-3)
- [ ] test-tool `scenario-coverage-check` 기존 8케이스 PASS

### 5.3 코드/문서 품질
- [ ] 변경 5파일 @header/변경이력 기록 (버전·KST 일시·태스크 번호)
- [ ] 배포 경계 준수 — `opal/...` 소스만 편집, `~/.opal/` 무편집
- [ ] scenario-gate.md §3·§6, PRINCIPLES §15 인용 정확

### 5.4 보안
- [ ] `.scenario-coverage-input.json`은 `task_folder` 하위 전용 — 경로 이탈 없음 ([MUST] 규율 #5)
- [ ] 변환기가 task_folder 외부 파일 Read/Write 안 함 (opsdd SPEC.md도 task_folder 하위)
- [ ] 하드코딩 시크릿·토큰 없음 (문서/JSON 편집)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 8개 | 복잡 |
| 변경 파일 수 | 5파일(+PROJECT.md 6) | 복잡 |
| 모듈 범위 | 다중(op-scenario-gate·opds·opsdd 3 오케스트레이터/스킬) | 복잡 |
| 작업 유형 | 확산 개선(다 pilot 배선) | 복잡 |
| 외부 의존성 | 없음(기존 tool/agent 재사용) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1: [opal-task-agent] Step 1 (op-scenario-gate 변환기)          — 선행 계약
Batch 2: [opal-task-agent#A] Step 2 (opds SKILL+pipeline.json)   ∥
         [opal-task-agent#B] Step 3 (opsdd SKILL) → Step 4 (verify-guide)  — 파일군 분리
Batch 3: [PM 직접] Step 5 배치 조정 병합, Step 6 PROJECT.md
Batch 4: [opal-test-agent] Step 7 (회귀)
Batch 5: [PM 직접] Step 8 (자기적용 게이트 실호출)
```

**그룹핑 근거**:
- 파일 충돌 방지: opds 파일군(#A)과 opsdd 파일군(#B)은 disjoint — 병렬 안전. Step 3·4는 같은 opsdd 관심사(게이트 참조 일관성)라 #B 내 순차.
- Step 1은 두 배선의 공통 선행 → 반드시 Batch 1 단독.

### C-2. 스킬 요구사항

- 기존 스킬 재사용: op-scenario-gate(변환기 확장 대상), op-dev-test-scenario(opds producer 형식 참조). 신규 스킬 갭 없음(배선 작업).

### C-3. 도구 요구사항

- `state-tool spec-validate`(opds pipeline.json 검증), `state-tool init --rows-from`(opsdd rows_count 검증), `test-tool scenario-coverage-check`(기존 스위트·자기적용). 신규 도구/패키지 없음.

### C-4. 테스트 전략

- 산출물 검사(grep/diff): TS-001~003,006~011 — 문서 구조·리터럴 정합.
- 기능/통합: TS-004,005,012,013 — 게이트 실호출·차단·verdict.
- 회귀: TS-009 — diff 0 + spec-validate + 기존 스위트.
- 자기적용(F-006)은 op-scenario-gate 실호출이라 오케스트레이터(PM) 수행 — evaluator 서브에이전트 디스패치 포함.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 | Markdown (SKILL.md·SSOT·verify-guide) | 없음(프레임워크 내부 편집) |
| 데이터 스펙 | JSON (pipeline.json, task-step key 체계 spec_version 1.0) | 없음 |
| 도구 | Python 3 (state-tool·test-tool) — 무변경 재사용 | 없음 |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 외부 라이브러리/API 조사 대상 없음 (순수 내부 배선) |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | op-scenario-gate SKILL | `opal/skills/op-scenario-gate/SKILL.md` | Step 2 변환기 확장 대상, 규율/enum 정합 |
| D-2 | 설계 | scenario-gate.md SSOT | `opal/core/references/harness/scenario-gate.md` | §3 정규화 계약·§6 tool-gated (계승, 무변경) |
| D-3 | 설계 | 073 DONE | `tasks/073-260723-opd-시나리오-목표커버리지-루프/DONE.md` | 공유 컴포넌트·확산 근거 |
| D-4 | 설계 | opds SKILL | `opal/skills/opal-pilot-dev-short/SKILL.md` | STEP 2 producer 확립·배선 지점 |
| D-5 | 설계 | op-dev-plan SKILL | `opal/skills/op-dev-plan/SKILL.md` | TEST-SCENARIO.md 출력 제외 확인 — **미접촉** |
| D-6 | 설계 | opsdd SKILL | `opal/skills/opal-pilot-sdd/SKILL.md` | Phase 2 REVIEW·24행 파이프라인 배선 |
| D-7 | 설계 | opsdd verify-guide | `opal/skills/opal-pilot-sdd/references/verify-guide.md` | §4 대체·S-1~S-6 존치 |
| D-8 | 설계 | opd 접합 선례 | `opal/skills/opal-pilot-dev/SKILL.md:95-100` + `references/pipeline.json:14-15` | 게이트 배선 동형 패턴 |
| D-9 | 설계 | opds pipeline.json | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | R-2 게이트 행 삽입 지점 |
| D-10 | 설계 | op-dev-test-scenario SKILL | `opal/skills/op-dev-test-scenario/SKILL.md` | opds producer TEST-SCENARIO 통일 형식(§1/§4) |
| D-11 | 설계 | opsdd spec-guide | `opal/skills/opal-pilot-sdd/references/spec-guide.md:90-165` | opsdd 변환기 소스 FR/AC/EC ID·FR-AC 역참조 |
| D-12 | 소스 | test-tool scenario.py | `opal/tools/test-tool/lib/scenario.py:474-477` | coverage-check pilot-중립(무변경 근거) |
| D-13 | 소스 | state-tool state_tool.py | `opal/tools/state-tool/state_tool.py:716-785` | spec-validate·STAGE_ENUM(REVIEW) 확인 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| H-1 | opds producer_artifact 부재(발견①) | F-002 | P0 | STEP 2 서술 보강으로 PM+캡틴 TEST-SCENARIO.md 작성 확정, op-dev-plan 미접촉 |
| H-2 | opsdd 변환기 SPEC.md 미Read(발견②) | F-001 | P1 | 변환기 표에 SPEC.md 추가 Read 명시(FR/AC/EC), task_folder 하위 |
| H-3 | opsdd `--row N` 재정렬 누락(발견④) | F-003 | P0 | §3.3.2 리터럴 전수 표 + rows_count 25 파싱 검증 완료 기준 |
| H-4 | opds pipeline.json 스펙 위반(R-D) | F-002 | P1 | `state-tool spec-validate` exit 0 완료 기준 |
| H-5 | pilot 분기가 opd 회귀(R-E) | F-001 | P1 | opd 행 diff 0 유지 + 회귀 스위트 |
| H-6 | 규율 #4 문구 불일치(발견⑤) | F-001 | P2 | 사실 서술 갱신(계약 무변경) |
| R-신규 | Step 2·3 병렬 시 changed_files 병합 누락 | F-002,003 | P1 | Step 5 배치 조정에서 disjoint 파일군 확인·병합 |
