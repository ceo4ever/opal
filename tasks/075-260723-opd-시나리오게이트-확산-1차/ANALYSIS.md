# ANALYSIS: op-scenario-gate 목표-커버 게이트 확산 1차 (opds·opsdd) — 접합 실사

> 작성일: 2026-07-23
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | op-scenario-gate SKILL | `opal/skills/op-scenario-gate/SKILL.md` | Step 2 변환기 확장 대상(pilot 분기), Step 3~6 재사용 계약 확인 |
| D-2 | 설계 | scenario-gate.md SSOT | `opal/core/references/harness/scenario-gate.md` | 6축·판정주체 분리·정규화 계약(§3)·종료조건(§5) — 변경 대상 아님, 계승 확인 |
| D-3 | 설계 | 073 DONE | `tasks/073-260723-opd-시나리오-목표커버리지-루프/DONE.md` | 공유 컴포넌트 목록·확산 후속 근거(§6) |
| D-4 | 설계 | opds SKILL | `opal/skills/opal-pilot-dev-short/SKILL.md` | opds STEP 2(PLAN) 접합 지점, pipeline.json 구조 |
| D-5 | 설계 | op-dev-plan SKILL | `opal/skills/op-dev-plan/SKILL.md` | opds가 TEST-SCENARIO.md를 실제로 어디서 작성하는지 — **주의: 이 문서 자체가 TEST-SCENARIO.md를 출력 범위에서 제외한다고 선언(발견①)** |
| D-6 | 설계 | opsdd SKILL | `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd Phase 2 REVIEW 접합 지점, 24행 비표준 파이프라인 구조 |
| D-7 | 설계 | opsdd verify-guide | `opal/skills/opal-pilot-sdd/references/verify-guide.md` | REVIEW 수동 커버리지(§4) 대체 대상, S-1~S-6 존치 대상(§2) |
| D-8 | 설계 | opd 접합 선례 | `opal/skills/opal-pilot-dev/SKILL.md` + `opal/skills/opal-pilot-dev/references/pipeline.json` | STEP 3.5·게이트 행(id 10) 패턴 — opds/opsdd 배선 참조 모델 |
| D-9 | 설계 | opds pipeline.json | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | opds가 이미 task-step key 체계로 전환되어 있음(070 그룹A) — R-2 삽입 지점 확인 |
| D-10 | 설계 | op-dev-test-scenario SKILL | `opal/skills/op-dev-test-scenario/SKILL.md` | opd의 TEST-SCENARIO.md 통일 형식(§1/§4) 정의 문서 — opds가 실제로 이 형식을 참조하지 않음(발견①) |
| D-11 | 설계 | opsdd spec-guide | `opal/skills/opal-pilot-sdd/references/spec-guide.md` | SPEC.md FR/AC/EC ID 체계·FR-AC 상호 추적성(§3-5~3-7) — opsdd 변환기 소스 확정 근거 |
| D-12 | 소스 | test-tool scenario.py | `opal/tools/test-tool/lib/scenario.py:474-477` | scenario-coverage-check가 pilot 필드를 전혀 검사하지 않는 pilot-중립 확인(R-1/R-5 무변경 근거) |
| D-13 | 소스 | opal-evaluator-agent AGENT.md | `opal/agents/opal-evaluator-agent/AGENT.md:27-196` | scenario-rubric phase 입출력 계약(무변경 확인) |
| D-14 | 소스 | state-tool README/본체 | `opal/tools/state-tool/README.md`, `opal/tools/state-tool/state_tool.py:30-52` | opsdd `--rows-from .md` 레거시 경로·STAGE_ENUM(REVIEW 포함) 확인 |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/op-scenario-gate/SKILL.md` | Step 2 정규화 변환기 표(현재 `pilot=opd` 단일) | ✅ pilot=opds/opsdd 분기 추가 | `opal/skills/op-scenario-gate/SKILL.md:33-50` |
| `opal/core/references/harness/scenario-gate.md` | 6축·정규화 계약·종료조건 SSOT | ❌ (계승만, TASK.md 제약) | `opal/core/references/harness/scenario-gate.md:29-65` |
| `opal/skills/opal-pilot-dev-short/references/pipeline.json` | opds 10-task-step 행 정의 | ✅ 게이트 행 1개 삽입(id 재정렬) | `opal/skills/opal-pilot-dev-short/references/pipeline.json:5-16` |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds STEP 2(PLAN) 절차 서술 | ✅ op-scenario-gate 호출 절차 삽입 + PM Gate 체크리스트 정합 | `opal/skills/opal-pilot-dev-short/SKILL.md:39-71` |
| `opal/skills/op-dev-plan/SKILL.md` | PLAN 워커 스킬(TEST-SCENARIO.md 출력 제외 선언) | ⚠️ opds 문맥 정합 여부 PLAN에서 확정 필요(발견①) | `opal/skills/op-dev-plan/SKILL.md:6,35,146` |
| `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd 24행 비표준 파이프라인(SSOT 자체) | ✅ REVIEW Phase 행 삽입·재정렬 + Phase 2 절차 배선 | `opal/skills/opal-pilot-sdd/SKILL.md:138-163, 343-373` |
| `opal/skills/opal-pilot-sdd/references/verify-guide.md` | REVIEW 수동 FR/AC/EC 커버리지 절차(§4) | ✅ scenario-coverage-check 대체 + 변경이력 행 | `opal/skills/opal-pilot-sdd/references/verify-guide.md:137-164` |
| `opal/skills/opal-pilot-sdd/references/spec-guide.md` | SPEC.md FR/AC/EC ID 규칙 | ❌ (변환기가 소비만, 수정 불요) | `opal/skills/opal-pilot-sdd/references/spec-guide.md:90-123, 150-165` |
| `opal/tools/test-tool/lib/scenario.py` | scenario-coverage-check 구현 | ❌ (pilot-중립 기확보) | `opal/tools/test-tool/lib/scenario.py:474-477` |
| `opal/agents/opal-evaluator-agent/AGENT.md` | scenario-rubric phase | ❌ (무변경, 재사용만) | `opal/agents/opal-evaluator-agent/AGENT.md:59-154` |
| `opal/core/references/opal-harness.md` | 루프 상한 SSOT(§1) | ❌ (참조만) | `scenario-gate.md:84,90` 인용 근거 |

### 1.2 아키텍처 패턴

- op-scenario-gate는 **호출자(PM+캡틴) 직접 수행 + Step 4 evaluator 1건만 서브에이전트 디스패치**하는 "얇은 컨트롤 스킬" 패턴이다 (`op-scenario-gate/SKILL.md:13-14`). 확산은 이 패턴을 그대로 재사용하고, Step 2 표에 pilot 행만 추가한다(`op-scenario-gate/SKILL.md:50` "확장성 근거").
- pilot별 파이프라인은 두 세대가 공존한다: opd·opds는 `references/pipeline.json` + task-step key 주소(070 그룹A 전환, `opal-pilot-dev-short/references/pipeline.json:1-21`), opsdd는 **SKILL.md 자체가 `--rows-from`의 파싱 대상**인 레거시 `--row N` 숫자 주소 체계다(`opal-pilot-sdd/SKILL.md:331` `--rows-from opal/skills/opal-pilot-sdd/SKILL.md`, 본문 전체가 `--row 6`, `--row 15`, `--row 18`, `--row 24` 식 숫자 참조 — `opal-pilot-sdd/SKILL.md:130-131,190-191,245-246,288`). state-tool README는 `.md` 파싱 경로를 "레거시" + "deprecation 경고 1줄"로 명시한다(`opal/tools/state-tool/README.md:55`).
- test-tool `scenario-coverage-check`와 opal-evaluator-agent `scenario-rubric`은 **pilot-중립 정규화 페이로드만 소비**하도록 이미 설계되어 있다 — pilot 필드를 검사하는 코드가 존재하지 않는다(`scenario.py:474-477` 확인). 즉 R-1~R-5는 순수하게 **호출측(op-scenario-gate Step 2 + 각 오케스트레이터 배선)** 작업이며 도구/에이전트 코드 변경이 필요 없다.

### 1.3 의존성 맵

```
op-scenario-gate/SKILL.md (Step 2 정규화 변환기)
  ├─ [pilot=opd]   TASK.md(R) + PLAN.md(F/H) + TEST-SCENARIO.md §1/§4  (기존)
  ├─ [pilot=opds]  TASK.md(R) + PLAN.md(F/H) + TEST-SCENARIO.md §1/§4  (신규 분기, opd와 동일 소스 — 단 producer_artifact 실제 생성 경로 불확실, 발견① 참조)
  └─ [pilot=opsdd] TASK.md(goal) + SPEC.md(FR/AC/EC) + TEST-SCENARIOS.md(추적 매트릭스)  (신규 분기, opd/opds와 소스 구조가 다름 — 발견②)
        │
        ▼
  Step 3: test-tool scenario-coverage-check (무변경, pilot-중립)
        ▼
  Step 4: opal-evaluator-agent scenario-rubric (무변경, pilot-중립)
        ▼
  Step 5: 종료조건 판정 (scenario-gate.md §5, 무변경)
        ▼
  Step 6: verdict 반환 → 호출자(오케스트레이터)가 게이트 행 mark
```

- opds 게이트 행 삽입: `opal-pilot-dev-short/references/pipeline.json`(id 3 `plan.plan_md` 직후, id 4 `plan.pm_gate` 직전) → 이후 행 id 전부 +1 재정렬.
- opsdd 게이트 행 삽입: `opal-pilot-sdd/SKILL.md` 파이프라인 현황판 표(행 10 `FR↔TS 커버리지 확인` 직후, 행 11 `PM Gate` 직전) → 행 11~24를 12~25로 재정렬 + 본문 내 모든 `--row N` 리터럴(Phase 3 이후) 동반 수정 필요.

### 1.4 테스트 현황

- test-tool `scenario-coverage-check` 단위 테스트는 073에서 이미 pilot-중립 페이로드 기준으로 8케이스 작성됨(`tasks/073.../DONE.md` R-7). 075는 이 도구를 호출만 하므로 신규 python 테스트는 발생하지 않는다(TASK.md §기술 스택).
- opd 자기적용(R-8, 073)은 op-scenario-gate 루프 자체의 동작 증거이며, opds/opsdd 확산은 **각 pilot의 Step 2 변환기 정확성**(TASK.md R-1 AC: `{goal,R[],F[],H[],scenarios[]}` 정확 생성)을 자기적용으로 재입증해야 한다(R-6) — 이는 EXECUTE/TEST 단계 대상이며 ANALYSIS 범위 밖이다.

---

## 2. 외부 조사 결과

해당 없음 — 순수 내부 프레임워크 문서/스킬 배선 작업으로 외부 라이브러리·API 조사 대상이 없다.

---

## 3. 영향 범위

### 3.1 직접 영향

| 파일 | 변경 내용 |
|------|----------|
| `opal/skills/op-scenario-gate/SKILL.md` | Step 2 표에 `pilot=opds`, `pilot=opsdd` 행 추가(§3.N 신설), 실행 컨텍스트 입력 설명의 `pilot` enum 주석 갱신 |
| `opal/skills/opal-pilot-dev-short/references/pipeline.json` | task_steps 배열에 게이트 행 삽입, id 재정렬, `pm_gate[]`의 PLAN 항목 checklist 문구 정합(중복 문구 정리 여부는 발견③ 참조) |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | STEP 2 절차에 op-scenario-gate 호출 서술(D-8 STEP 3.5 패턴 준용) 삽입, 변경이력 버전업 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | 파이프라인 현황판 표 재정렬(24→25행), Phase 2 REVIEW 절차에 게이트 호출 삽입, `--row N` 리터럴 전수 갱신, 변경이력 버전업 |
| `opal/skills/opal-pilot-sdd/references/verify-guide.md` | §4 "FR↔TS 커버리지 확인" 절 재작성(수동 절차 → scenario-coverage-check 호출 안내로 대체) + 변경이력 행, §2 S-1~S-6은 무변경 |

### 3.2 간접 영향

- **opd 1차 접합**: `opal/skills/op-scenario-gate/SKILL.md` Step 2 표에 새 행을 "추가"만 하고 기존 `pilot=opd` 행을 수정하지 않으면 회귀 없음(R-5). 단 Step 2 상단 산문("1차는 opd 단일 호출로 한정")과 [MUST] 규율 #4("1차 opd 단일 호출")는 확산 완료 후 사실과 불일치하게 되므로 갱신 필요(§5 리스크 R-F 참조 — 소스 변경이지만 "무변경" 대상이 아니라 "사실 정합" 목적의 문구 갱신이며 6축·정규화 계약 자체는 변경하지 않음).
- **oppl**: TASK.md에서 이미 제외 확정(D-3, 근거: 자체 표면-게이트+독립평가자 보유). 이 세션에서 oppl 관련 파일 미접촉 확인.
- **oppd**: 2차 유예. 미접촉.
- **op-dev-plan/SKILL.md(D-5)**: 075의 직접 편집 대상은 아니나(TASK.md 범위 표에 없음), 발견①(아래)이 R-2 설계의 전제조건에 해당하므로 PLAN 단계에서 반드시 재확인 필요.

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [ ] API 인터페이스 변경 — 해당 없음
- [ ] 설정/환경변수 변경 — 해당 없음
- [x] 빌드/배포 파이프라인 변경 — state-tool `pipeline.json`(opds) 스펙 변경 시 `spec-validate` 재검증 필요(회귀 확인 항목, R-5)

---

## 4. 핵심 발견 사항

### 발견① [중요] opds의 TEST-SCENARIO.md 작성 주체가 두 SSOT 문서 간에 상충한다 — R-2 설계의 선행 전제조건

- `opal-pilot-dev-short/SKILL.md:54`: "op-dev-plan 워커가 PLAN.md와 TEST-SCENARIO.md를 **통합 작성**한다."
- 그러나 `op-dev-plan/SKILL.md:6`(설명 프론트매터)와 `op-dev-plan/SKILL.md:35`(입출력 표 "제외 출력"), `op-dev-plan/SKILL.md:146`(Step 10)는 모두 동일하게 "TEST-SCENARIO.md는 **opal-pilot-dev STEP 3.5**에서 PM이 별도 작성하므로 PLAN 워커의 출력 범위에 포함하지 않는다"고 선언한다.
- `op-dev-plan/SKILL.md`는 opd·opds 공용 스킬이다(양쪽 오케스트레이터가 동일 경로를 디스패치). 이 제외 선언은 opd의 STEP 3.5 도입(`opal-pilot-dev/SKILL.md` 변경이력 v3.8, 2026-05-15, 태스크 004: "STEP 3.5 TEST-SCENARIO 신설(PM 직접 작성) + PLAN에서 TEST-SCENARIO.md 생성 제거")과 **같은 태스크(004)**에서 `op-dev-plan/SKILL.md`에도 반영된 것으로 추정된다(`op-dev-plan/SKILL.md` 변경이력 v2.6도 동일 태스크 004, 단 "리스크 가설 표 신설"만 명기 — 출력 제외 문구 자체의 변경이력 항목은 없음). 반면 opds 오케스트레이터(`opal-pilot-dev-short/SKILL.md`) STEP 2의 "통합 작성" 서술은 그 이전 세대(v2.9, 2026-04-13, 태스크 115) 그대로 남아 있고, opds 자체에는 opd의 STEP 3.5에 대응하는 별도 TEST-SCENARIO 단계가 없다(opds 5단계: TASK/PLAN/EXECUTE/TEST/CLOSE — `opal-pilot-dev-short/SKILL.md:13`).
- **결론**: 현재 스킬 문서 상태만 놓고 보면, opds가 op-dev-plan 워커를 디스패치했을 때 워커가 op-dev-plan/SKILL.md 자신의 지시(Step 10 제외 선언)를 따르면 TEST-SCENARIO.md가 **작성되지 않을 수 있다** — op-scenario-gate의 `producer_artifact`가 될 산출물 자체가 없을 위험이 있다. 실무에서는 opds 오케스트레이터(PM)가 디스패치 프롬프트에 "TEST-SCENARIO.md도 작성하라"고 명시적으로 재지시함으로써 우회되고 있을 가능성이 높으나, 이는 `[MUST] scenario-gate.md §6` "PM은 산문 판단만으로 게이트 통과를 선언할 수 없다"는 tool-gated 원칙과 결이 같은 취약점 — **문서 SSOT 간 불일치를 프롬프트 재지시로 메우는 구조**다.
- **PLAN 결정 필요(decision_required)**: (a) `opal-pilot-dev-short/SKILL.md` STEP 2의 "통합 작성" 서술을 op-dev-test-scenario의 통일 형식(D-10)을 명시 참조하도록 보강하여 producer_artifact 생성을 확정하거나, (b) `op-dev-plan/SKILL.md`의 제외 선언에 "단, opds 호출 시에는 예외적으로 TEST-SCENARIO.md를 통합 작성한다" 분기를 추가한다. 이 결정 없이는 R-2(opds 접합) 게이트가 가리킬 producer_artifact 존재가 불확실하다. 075 범위(TASK.md §범위: "opds pipeline 게이트 행 추가")는 이 문제의 해결을 명시하지 않으므로 PLAN에서 범위 포함 여부를 확정해야 한다.

### 발견② opsdd는 PLAN.md류 F/H 소스가 REVIEW 시점에 존재하지 않는다 — opd/opds와 다른 변환기 소스 구조 필요

- opsdd 6단계는 `TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE`다(`opal-pilot-sdd/SKILL.md:23`). TEST-SCENARIOS.md는 **Phase 2 REVIEW**에서 작성되고(`opal-pilot-sdd/SKILL.md:79,156`), ACT 분해를 담은 SPEC-PLAN.md(PLAN.md의 F-ID/H-ID 표에 대응하는 유일한 후보)는 **Phase 3 DESIGN**에서만 생성된다(`opal-pilot-sdd/SKILL.md:80,168`). 즉 REVIEW 시점에는 opd/opds의 `PLAN.md §리스크 가설 표(H-ID)`나 `§1.2 기능 목록(F-ID)`에 대응하는 산출물이 **아직 존재하지 않는다**.
- 대신 SPEC.md는 그 자체로 3단 ID 체계를 갖는다(`spec-guide.md:90-123,150-165`): `[FR-NN]`(기능 요구사항) → `AC-NN`(수용 기준, AC 상단에 "대응 FR: FR-01" 명시로 **FR↔AC 양방향 추적성**이 이미 문서화되어 있음, `spec-guide.md:123`) → `[EC-NN]`(엣지 케이스). TEST-SCENARIOS.md 추적 매트릭스는 `AC | 시나리오 ID | 유형 | 설명 | 상태` 컬럼 구조이며, AC 컬럼 값에 EC-ID도 함께 수록된다(예시 행 `EC-01 | TS-04 | unit | ... | Red`, `verify-guide.md:97` 대응 구조).
- 따라서 opsdd 변환기의 합리적 소스 매핑(권고, PLAN 확정 필요):
  - `goal` ← TASK.md 목표 문장 (opd/opds와 동일 패턴)
  - `requirements` ← SPEC.md `[FR-NN]` 목록(§5, `spec-guide.md:90-104`)
  - `features` ← SPEC.md `AC-NN` 목록(§6) — opsdd에는 PLAN.md 상당의 별도 "기능" 계층이 없으므로 AC를 기능 단위로 대체 사용
  - `hypotheses` ← SPEC.md `[EC-NN]` 목록(§7) — TASK.md R-4 문구("수동 FR/AC/EC 커버리지 확인 절을 대체")가 이미 AC/EC를 커버리지 축으로 명시하고 있어 이 매핑과 정합
  - `scenarios[]` ← TEST-SCENARIOS.md 추적 매트릭스 각 행, `covers_requirements`는 해당 AC의 "대응 FR" 역참조로 도출, `covers_features`는 해당 AC-ID 자신, `covers_hypotheses`는 해당 행이 EC 기원일 때만 채움
- **TASK.md R-1 재확인 필요**: TASK.md 원문(§요구사항 R-1)은 "opsdd=TEST-SCENARIOS.md(AC↔TS 매핑)"만 소스로 명시했으나, 위 분석에 따르면 **SPEC.md도 함께 Read해야** FR 목록·FR-AC 역참조·EC 목록을 확보할 수 있다. Step 2 확장 시 op-scenario-gate가 `task_folder` 하위 SPEC.md를 추가로 읽는 것은 기존 opd 패턴(TASK.md+PLAN.md+producer_artifact 3문서 병행 Read, `op-scenario-gate/SKILL.md:33-41`)과 구조적으로 동일하므로 신규 컴포넌트를 요구하지 않는다.

### 발견③ opsdd Phase 2는 REVIEW 전 구간이 PM 단독 수행 — self-confirming 정확한 위치 특정

- Phase 2 REVIEW의 3단계(구조 검증 S-1~S-6 / TEST-SCENARIOS.md 작성 / FR↔TS 커버리지 확인)는 모두 "PM 직접, 워커 디스패치 없음"이다(`opal-pilot-sdd/SKILL.md:140`, `verify-guide.md:11`). 파이프라인 현황판 행 8·9·10(`opal-pilot-sdd/SKILL.md:357-359`)과 이어지는 행 11 PM Gate(`SKILL.md:360`)까지 전부 동일 주체(PM)가 작성·검증·게이트를 수행한다. REVIEW를 통과시키는 유일한 타자 개입은 행 12 "사용자 확인"(`SKILL.md:361`)뿐이다.
- op-scenario-gate 삽입 지점(권고): 행 10 "FR↔TS 커버리지 확인"을 **scenario-coverage-check 결정론 판정으로 교체**하고, 그 직후(신규 행)에서 op-scenario-gate Step 4(opal-evaluator-agent 서브에이전트 디스패치)를 호출하여 PM이 아닌 별도 판단 주체가 ①⑤⑥축을 채점하게 한다. 이렇게 하면 행 11 PM Gate는 "산문 판단"이 아니라 "두 tool-gated 증거(coverage exit 0 + evaluator verdict pass)를 확인하는 절차"로 성격이 바뀌어 self-confirming이 구조적으로 해소된다(R-3 AC 충족).
- DESIGN(Phase 3) 진입 차단은 opd 패턴과 동일하게 게이트 행이 stage-transition guard 미완 상태로 있으면 `mark`가 거부되는 방식으로 구현 가능하다(`state_tool.py` `stage_transition_violation`, D-8 opd 선례 `opal-pilot-dev/references/pipeline.json:309` 대응 주석 패턴 준용).

### 발견④ opsdd는 pipeline.json 미전환 상태 — 게이트 행 삽입 방식이 opd/opds와 다른 메커니즘을 요구한다

- opd·opds는 이미 `references/pipeline.json` + task-step key 주소 체계로 전환되어 있다(070 그룹A, `opal-pilot-dev-short/references/pipeline.json:1-21`, `opal-pilot-dev/references/pipeline.json:1-29`). opsdd는 `--rows-from opal/skills/opal-pilot-sdd/SKILL.md`로 **SKILL.md 자신의 마크다운 표를 직접 파싱**하는 레거시 경로를 그대로 쓴다(`opal-pilot-sdd/SKILL.md:331`, `state-tool/README.md:55` "`.md`이면 기존 SKILL.md 표 파싱(레거시) + deprecation 경고"). 본문 전체가 `--row N`(예: `--row 6`, `--row 15`, `--row 18`, `--row 24`) 숫자 주소로 작성되어 있다(`opal-pilot-sdd/SKILL.md:130-131, 190-191, 245-246, 288`).
- **PLAN 결정 필요(decision_required, 범위 확대 여부)**: (a) 최소 변경 — 기존 레거시 `--row N` 숫자 체계를 유지한 채 24행 표에 신규 행 1개를 삽입하고 이후 행 11~24를 12~25로 전수 재정렬 + 본문 내 모든 `--row N` 리터럴 동반 수정(opsdd를 pipeline.json으로 전환하지 않음, TASK.md "신규 컴포넌트 0/배선만" 제약에 가장 부합), 또는 (b) opsdd를 pipeline.json + task-step key로 선제 전환 후 게이트 행 추가(070 전환의 연장선이나, TASK.md 범위 표에 명시되지 않은 별도 마이그레이션 작업이므로 075 스코프 초과 가능성). **권고**: (a) 최소변경 — 070 그룹A 전환은 별도 후속 태스크로 남겨두고 075는 배선에 집중한다. `STAGE_ENUM`에 `REVIEW`가 이미 등록되어 있어(`state_tool.py:32`) `add-row --stage REVIEW`류 런타임 삽입도 기술적으로는 가능하나, 신규 태스크 초기화(`init --rows-from`) 시 기본 포함되려면 SKILL.md 표 자체(정적 베이스라인)의 수정이 필요하다.

### 발견⑤ opd 1차 단독 접합 문구의 사실 불일치(회귀 아님, 정합 갱신 필요)

- `op-scenario-gate/SKILL.md:120`의 [MUST] 규율 #4: "1차 opd 단일 호출: 1차 적용은 opd STEP 3.5의 단일 호출로 한정한다." 확산 완료 후에는 이 문장이 더 이상 사실과 맞지 않으므로, R-1 구현 시 이 규율 문구를 "1차 opd, 2차 opds/opsdd 확산 완료(pilot=opd/opds/opsdd 3종 지원)" 형태로 갱신해야 한다. 이는 6축·정규화 계약·tool-gated 원칙 자체의 변경이 아니라 사실 서술 갱신이므로 R-5(회귀 없음) 위반이 아니다.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-A | opds TEST-SCENARIO.md 작성 주체 불일치(발견①) — R-2 게이트가 가리킬 producer_artifact가 SSOT 문서상 불확실 | 높음 | `opal-pilot-dev-short/SKILL.md:54` vs `op-dev-plan/SKILL.md:6,35,146` |
| R-B | opsdd REVIEW 시점 PLAN.md류 F/H 부재(발견②) — SPEC.md 추가 Read 필요, TASK.md R-1 소스 서술 보강 필요 | 중간 | `spec-guide.md:90-123,150-165`, TASK.md §요구사항 R-1 |
| R-C | opsdd 비표준 파이프라인(발견④) — 게이트 행 삽입 시 24→25행 전수 재정렬 + `--row N` 리터럴 전수 수정 필요, 실수 시 기존 Phase 3~6 행 참조 깨짐(회귀 위험) | 높음 | `opal-pilot-sdd/SKILL.md:130-131,190-191,245-246,288,343-373` |
| R-D | opds pipeline.json id 재정렬 시 `pm_gate[]` 배열의 `stage`값 매칭 및 기존 PLAN pm_gate checklist 문구("TEST-SCENARIO.md 시나리오가... 커버하는가")와 신규 tool-gated 게이트 간 중복 서술 — 정합 정리 필요(경미, self-confirming 위험은 아님 — evaluator가 이미 독립 주체이므로) | 낮음 | `opal-pilot-dev-short/SKILL.md:63`, `references/pipeline.json:18` |
| R-E | scenario-coverage-check/evaluator 코드는 pilot-중립이 이미 확인되어 회귀 위험 없음 — 오직 문서(SKILL.md 3종 + pipeline.json 1종 + verify-guide.md 1종) 배선 오류만이 회귀 경로 | 낮음(확인됨) | `scenario.py:474-477`, `AGENT.md:27-196` |
| R-F | op-scenario-gate [MUST] 규율 #4 문구가 확산 후 사실과 불일치(발견⑤) | 낮음 | `op-scenario-gate/SKILL.md:120` |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 문서 | Markdown(SKILL.md·SSOT·verify-guide) | - |
| 데이터 스펙 | JSON(`pipeline.json`, task-step key 체계) | spec_version 1.0 |
| 도구 | Python 3(state-tool, test-tool) — 무변경 재사용 | 기존 버전 유지 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| 없음 | 프레임워크 내부 스킬/SSOT 편집 작업이며 외부 커뮤니티 스킬 적용 대상 아님 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| 없음 | 외부 라이브러리/API 조사 불요 |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-23 | 최초 작성 — R-1~R-6 구현 접합점 실사(opds/opsdd), 발견 5건(opds 작성주체 SSOT 상충·opsdd F/H 소스 부재·REVIEW self-confirming 위치·opsdd 비표준 파이프라인·규율 문구 정합) + 리스크 6건 |
