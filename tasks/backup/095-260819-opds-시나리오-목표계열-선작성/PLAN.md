# PLAN: TEST-SCENARIO 목표계열 선작성 — PLAN 병렬 도출 트랙 신설

> 작성일: 2026-08-19 | 입력: TASK.md (ANALYSIS.md 없음 — opds Short Task, 코드/문서 분석 직접 수행)
> 모드: Multi-Feature (F-001~F-006)
> 작성자: opal-plan-agent | 출력 범위: PLAN.md **만** (TEST-SCENARIO.md는 PM+캡틴 페어가 별도 작성 — `op-dev-plan/SKILL.md` §입력/출력 "제외 출력")

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

TEST-SCENARIO 도출 입력을 **TASK 유래(채택 관점)**와 **PLAN 유래(파괴 관점)** 2계열로 명시 분리하고, TASK 유래 계열을 PLAN 워커 실행과 **병렬 선작성**하는 트랙을 SSOT 3문서(`red-first.md`·`test-scenario-guide.md`·`scenario-gate.md`) + pilot 2문서(opds·opd)에 신설한다. 도구 코드·`pipeline.json` 행 구조는 불변이며, 선작성은 STATE 행 밖 초안 작업으로 수행한다.

설계의 축은 **규칙 소유권 단일화**다 — 규칙 본문은 하네스 SSOT 또는 도출 엔진 중 한 곳에만 정의하고, pilot SKILL.md 2종은 참조 + 순서 배선만 담는다(§규칙 소유권 표가 집행 기준).

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 선작성 트랙 규칙 정의 — `red-first.md` §1.6 신설 | R-1 | P0 | 없음 |
| F-002 | 도출 엔진 2계열 분할 — `test-scenario-guide.md` Step 1 재구성 | R-2 | P0 | F-001 |
| F-003 | 게이트 호출 시점 규율 — `scenario-gate.md` §4 [MUST] 추가 | R-3 | P0 | F-002 |
| F-004 | opds 배선 — `opal-pilot-dev-short/SKILL.md` STEP 2 (a)(b)(c) 3단계 | R-4 | P0 | F-001, F-002, F-003 |
| F-005 | opd 배선 — `opal-pilot-dev/SKILL.md` STEP 3(PLAN) + STEP 3.5 | R-5 | P0 | F-001, F-002, F-003 |
| F-006 | 변경이력 5행 + install 재배포 + 배포본 정합 | R-6 | P0 | F-001~F-005 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ── F-002 ── F-003 ──┬── F-004 ──┐
 (§1.6)   (Step 1)  (§4)   │  (opds)   ├── F-006 (변경이력 + install)
                           └── F-005 ──┘
                              (opd)
```

- F-001 → F-002: 도출 엔진 Step 1이 `red-first.md` §1.6을 트랙 규칙 SSOT로 참조 → 절 번호 확정 선행 필요
- F-002 → F-003: `scenario-gate.md` §4의 "보강 완료" 판정이 `test-scenario-guide.md` Step 1 "보강 완료 판정"을 참조 → 앵커 확정 선행 필요
- F-003 → F-004·F-005: pilot 배선이 세 SSOT의 절 앵커(§1.6 / Step 1 Block A·B / §4)를 인용
- F-004 ∥ F-005: 서로 다른 파일, 상호 참조 없음 (동일 배치 내 순차 편집)

---

## 규칙 소유권 표 (SSOT 이중화 금지 집행용)

> **집행 규칙**: 아래 표의 `정의(SSOT)` 열에 기재된 문서 **1곳에만** 규칙 본문을 쓴다. `참조` 열의 문서는 규칙 본문을 재서술하지 않고 앵커 포인터(`문서 §N`)만 기재한다. 근거: [MUST] `.opal/AGENT.md` §프로젝트별 추가 지침: "하네스 변경 시: `opal/core/references/opal-harness.md`(SSOT)를 수정한다. 다른 곳에서 발췌·복제하지 않는다." / TASK.md §제약 조건 "SSOT 단일화".

| 규칙 ID | 규칙 | 정의 (SSOT) | 참조만 | 검증 방법 |
|---------|------|-----------|--------|----------|
| RULE-A1 | 목표계열 선작성 트랙의 존재·전제 (PLAN 워커 실행과 병렬 착수 허용) | `red-first.md` §1.6 | `test-scenario-guide.md` Step 1 · opds SKILL.md STEP 2 · opd SKILL.md STEP 3 | grep: 트랙 정의 문단이 red-first.md에만 존재 |
| RULE-A2 | 선작성 가능 입력 3종 (목표 문장 / 요구사항 R / 채택·잔존 기준) — 정규 열거 + 이 3종 밖 입력 사용 금지 | `red-first.md` §1.6 (a) | `test-scenario-guide.md` Step 1 Block A (축 매핑 표에서 축과 대응만) | grep: "선작성 가능 입력" 정규 열거가 red-first.md 1곳 |
| RULE-A3 | PLAN 확정 후 ③④축 보강 필수 (선작성만으로 종료 금지) | `red-first.md` §1.6 (b) | `test-scenario-guide.md` Step 1 Block B(절차) · opds (b) · opd STEP 3.5 1 | grep: `[MUST]` 보강 필수 원칙 문장 1곳 |
| RULE-A4 | 작성자≠PLAN 워커 불변 (선작성으로 시점이 앞당겨져도 분리 유지) | `test-scenario-guide.md` §목적 1 (**기존 SSOT — 신설 아님**) | `red-first.md` §1.6 (c) · `scenario-gate.md` §4 Producer≠Evaluator(기존) · pilot 2종(기존) | grep: 새 정의 추가 0건, 포인터만 |
| RULE-A5 | RED→GREEN 순서 불변 (본 트랙은 도출 시점만 앞당김) | `red-first.md` §1 (**기존**) + §1.6 (d) 재확인 포인터 | pilot 2종 기존 RED-first 콜아웃 | grep: §1 원문 무변경 |
| RULE-B1 | 도출 입력 2계열 분할 절차 (Block A / Block B) | `test-scenario-guide.md` Step 1 | opds (a)(b) · opd STEP 3 / 3.5 | grep: Block A/B 절차 본문 1곳 |
| RULE-B2 | 계열 ↔ 루브릭 축 매핑 (TASK 유래 → ①②⑤⑥ / PLAN 유래 → ③④) | `test-scenario-guide.md` Step 1 (매핑 표) | `red-first.md` §1.6 · pilot 2종 | grep: 매핑 표 1곳. 6축 **정의**는 `scenario-gate.md` §2가 SSOT — 재서술 금지 |
| RULE-B3 | 선작성 초안 저장 위치·보강 대기 마커 포맷 (`<!-- PENDING-BLOCK-B -->`) | `test-scenario-guide.md` Step 1 Block A | pilot 2종 · `scenario-gate.md` §4(보강 완료 판정 포인터) | grep: 마커 리터럴 정의 1곳 |
| RULE-B4 | 보강 완료 판정 3조건 | `test-scenario-guide.md` Step 1 Block B | `scenario-gate.md` §4 · pilot 2종 | grep: 3조건 열거 1곳 |
| RULE-B5 | 보강 additive-only 금지 (초안 시나리오 수정·삭제 포함) | `test-scenario-guide.md` Step 1 Block B | opds (b) · opd STEP 3.5 1 | grep: 원칙 문장 1곳 |
| RULE-B6 | Step 2(데이터 설계)·Step 3(계층 결정) 선작성 대상 아님 | `test-scenario-guide.md` Step 1 (선작성 대상이 아닌 Step 절) | — | grep: 1곳 |
| RULE-C1 | 게이트 호출 시점 = PLAN 확정 + 보강 완료 후 **1회** [MUST] | `scenario-gate.md` §4 | `red-first.md` §1.6 (e) · opds (c) · opd STEP 3.5 5 | grep: `[MUST]` 호출 시점 문장 1곳 |
| RULE-C2 | 선작성 시점 호출 금지 근거 (F/H 미확정 → ③④ 결정론 판정 불가) | `scenario-gate.md` §4 | pilot 2종 | grep: 근거 문단 1곳 |
| RULE-C3 | 루브릭 6축 정의 · 판정 주체 분리 · 정규화 계약 · 종료조건 (**기존**) | `scenario-gate.md` §2·§3·§5 (**무변경**) | 전 문서 | diff: §2·§3·§5 무변경 |
| WIRE-D | opds STEP 2 실행 순서 (a) 선작성 착수 → (b) 보강 → (c) 게이트 1회 + 행 mark 시점 | `opal-pilot-dev-short/SKILL.md` STEP 2 | — | 배선 전용 — 규칙 본문 0줄 |
| WIRE-E | opd STEP 3(PLAN) 선작성 착수 + STEP 3.5 보강 → 게이트 순서 + 행 mark 시점 | `opal-pilot-dev/SKILL.md` STEP 3 / 3.5 | — | 배선 전용 — 규칙 본문 0줄 |

> **미접촉 확정**: [MUST] brain `.opal/brain/pages/concept/opds-testscenario-producer-establishment.md` §결정 내용: "**공용 스킬 미접촉 원칙**: 상충의 한쪽인 공용 설계 워커 스킬은 절대 건드리지 않는다." → `opal/skills/op-dev-plan/SKILL.md` 은 본 태스크 수정 대상이 **아니다**(diff 0 유지). 선작성 배선은 오케스트레이터 2문서 + 하네스 SSOT에만 넣는다.
> **미접촉 확정 2**: `opal/skills/op-dev-test-scenario/SKILL.md`(통일 형식 소유)도 수정 대상이 아니다 — 통일 형식의 `> 상태:` enum을 늘리지 않고, 초안 표기를 HTML 주석 마커(RULE-B3)로 해결하여 6번째 파일 확산을 차단한다.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨 (`test-scenario-guide.md` §작성 프로세스 Step 1).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-a | F-002 (`test-scenario-guide.md` Step 1 Block A) | **self-confirming 퇴행** — 선작성은 TASK.md의 AC/R만 입력이므로 task:004가 문제로 지목한 "AC 중심 당연한 시나리오 양산" 구조로 되돌아간다. 작성자 분리(PM+캡틴)는 *누가* 쓰는지만 고치고 *무엇으로* 도출하는지는 고치지 못한다 | P0 | L1(산출물 검사) + L2(자기적용 — 본 태스크 시나리오에 ⑥축 존재 확인) | S: Block A 절에 "⑥경계·부정 최소 1건 포함" [MUST]가 존재 / S: Block B 절에 "보강 additive-only 금지" [MUST]가 존재 / S: 게이트가 최종 방어선임(선작성이 게이트를 우회하지 않음)이 문서로 확인 |
| H-b | F-002 (opd·opds **공용** 도출 엔진) | Step 1 재구성이 opd 순차 경로를 회귀시킨다 — Step 번호 체계 변경 시 `opal-pilot-dev/SKILL.md:93` "5단계 프로세스 적용" 및 `op-dev-test-scenario/SKILL.md:166,192` "§Step 3-b" 인용이 파손 | P0 | L1 + L2(회귀 grep) | S: 재구성 후 `### Step 1`~`### Step 5` 헤딩 5개 유지 / S: 기존 정규 문장("가설 없이 시나리오를 도출하면…", 계층 결정 규칙 표, Step 3-b) 잔존 / S: 선작성 미착수 시 Block A→B 연속 수행 = 현행 동등(opt-in) 문구 존재 |
| H-c | F-002·F-004·F-005 (선작성 초안 산출물) | 선작성 초안이 STATE 행 밖 산출물이라 추적 불가·유실. 임시 파일을 새로 만들면 태스크 폴더 오염 + `plan.pm_gate` gate.artifacts 정합 붕괴 | P1 | L1 | S: "초안은 별도 임시 파일 없이 TEST-SCENARIO.md 본문에 직접 작성" 규정 존재 / S: `pipeline.json` diff 0건(행·gate 무변경) / S: opds `plan.pm_gate` artifacts에 이미 TEST-SCENARIO.md가 있어 추가 등재 불필요 |
| H-d | F-003 (게이트 호출 시점) | 규율 미준수로 선작성 시점 호출 → `features`·`hypotheses` 미확정 → coverage-check가 `missing` 반환 FAIL → §5-2 반복 상한(3회) 무의미 소모 | P1 (도구 층이 이미 부분 차단 — 아래 근거) | L1 + L2(도구 집행 실증) | S: `[MUST]` 호출 시점 문장 + 금지 근거 존재 / S: 게이트 행 조기 `advance` 시 `stage_transition_violation` 거부 실증(`opal/tools/state-tool/state_tool.py:634` guard, advance 경로 `:1423` `force=False`) |
| H-e | F-001~F-005 전체 (5문서) | 5문서에 동일 규칙이 중복 서술되어 SSOT 이중화 발생 → 이후 개정 시 문서 간 표류 | P1 | L1(grep 매트릭스) | S: §규칙 소유권 표의 RULE-A1~C2 각 행에 대해 `정의` 1곳 / `참조` 문서에 규칙 본문 0줄 grep 검증 |
| H-f | F-001 (`red-first.md` 절 삽입) | 기존 §2~§6 번호를 이동시키면 **60건 이상의 외부 인용이 일괄 파손** — `red-first.md §2`(작성자≠구현자) / `§3`(테스트 불변성) / `§4`(공개 인터페이스) / `§5`(graceful skip)가 8개 도구 테스트 스위트 및 `coding-principles.md:53`·`opal-test-agent/AGENT.md:91`에서 인용 중 | P0 | L1 + L2(회귀 grep) | S: 신설 절이 **§1.6**(§1.5 직후 삽입)이고 기존 `## 2.`~`## 6.` 헤딩 문자열이 문자 단위 불변 / S: `grep -rn 'red-first.md §[2-6]'` 대상 인용의 지시 내용이 여전히 유효 |
| H-g | F-006 (install 재배포) | 배포본-소스 정합 검증이 변경이력 strip 특성을 무시하면 오탐(전부 diff)·미탐(검증 생략) 발생. install은 `^## 변경이력$`부터 파일 끝까지 제거한다(`scripts/install-mac.sh:219-222`, `:227-232`) | P1 | L2(실 diff 실행) | S: strip-후 diff 0건 × 5파일 (사전 실측: install 전 baseline이 5/5 IDENTICAL — 이 AC가 달성 가능함이 확인됨) |
| H-h | F-005 (opd 절 번호) | **TASK.md R-5의 "STEP 2(PLAN)" 지목이 실제 문서와 불일치** — `opal-pilot-dev/SKILL.md`의 STEP 2는 **ANALYSIS**이고 PLAN은 **STEP 3**이다. 지목대로 STEP 2에 배선하면 ANALYSIS 단계에 선작성이 붙어, PLAN 착수보다 이르게(그리고 ANALYSIS PM Gate 이전에) 도출이 시작된다 | P0 | L1 | S: 선작성 착수 지시가 `## STEP 3: PLAN` §3-1 하위에 위치 / S: `## STEP 2: ANALYSIS` 절 diff 0건 |
| H-i | F-002·F-004·F-005 | 선작성이 필수처럼 읽히면 **문서 전용 작업의 자연 스킵 경로가 막힌다** — opds STEP 2·`plan.scenario_gate`는 "문서 전용 작업 시 스킵(게이트도 자연 스킵)"을 전제로 설계됨(`opal-pilot-dev-short/SKILL.md:56`) | P1 | L1 | S: §1.6 (f)에 opt-in 성격 명시 / S: opds 기존 "문서 전용 작업 시 스킵" 문구 잔존 |

**가설 → 방어 판정 (H-a 요청 판정)**: **작성자 분리 유지만으로는 불충분하다.** task:004가 지목한 원인은 두 층이었다 — (i) 작성 주체가 PLAN 워커라 self-confirming (ii) 도출 입력이 AC 중심이라 "당연한 시나리오" 양산(근거: brain `test-scenario-pipeline-redesign.md` §배경·문제). 선작성 트랙은 (i)의 해법(작성자=PM+캡틴 페어)을 그대로 물려받지만, (ii)는 **선작성 구간에서 오히려 강화**된다 — 그 구간의 유일한 입력이 TASK 유래(목표·R·AC)이기 때문이다. 따라서 추가 방어 3종을 규칙으로 못박는다:
1. **⑥경계·부정 축 동시 도출 의무** (RULE-B2 파생, `test-scenario-guide.md` Step 1 Block A) — Block A는 ①②⑤ 외에 ⑥축을 담당하므로, 각 R의 경계값·부정 경로를 R별로 1회 이상 질의해 최소 1건을 산출한다. 경계·부정은 "당연한 시나리오"의 정반대 방향이므로 편향 상쇄로 작동한다.
2. **보강 additive-only 금지** (RULE-B5) — Block B 보강은 시나리오 추가로 끝내지 않고, 선작성 초안을 H-N·F-NNN과 대조해 **중복·과잉·PLAN 설계와 어긋나는 시나리오를 수정·삭제**한다. 이것이 없으면 선작성 단계의 당연한 시나리오가 최종 집합에 그대로 잔존한다.
3. **게이트가 최종 방어선임을 유지** (RULE-C1) — 게이트를 보강 완료 후 1회 호출하므로 채점 대상은 **최종 집합 전체**다. 선작성 초안이 게이트를 우회하는 경로는 존재하지 않으며, `opal-evaluator-agent`의 판단축 ①⑤⑥(각 ≥1점 AND 평균 ≥1.5) 채점이 그대로 적용된다(`scenario-gate.md` §5-1).

---

## 2. 기능별 분석

### F-001: 선작성 트랙 규칙 정의 — `red-first.md` §1.6 신설

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/harness/red-first.md` | RED-first TDD 트랙 규칙 SSOT (86줄) | 수정 |
| 가이드 | `opal/core/PRINCIPLES.md` | 헌법 §4 — 원칙 SSOT (상속원, 재서술 금지) | 미변경 (참조) |
| 가이드 | `opal/core/references/opal-harness.md` | §2 하네스 모듈 테이블에 `harness/red-first.md` 등록됨 (`:111`) | 미변경 (등록 이미 존재) |

#### 2.1.2 현재 구현

`red-first.md` 구조 (실측): frontmatter(module/role/load/상속) → §0 상속 → §1 RED→GREEN 순서 → §1.5 적용 기준(하이브리드 자동분기) → §2 작성자≠구현자 → §3 테스트 불변성 → §4 공개 인터페이스 검증 → §5 graceful skip → §6 STATE 행 정책 → 변경이력(v1.0 단일 행).

§1.5는 이미 **판단 시점**을 명시한다: "**판단 주체**: PM이 변경 영역으로 판단(TEST-SCENARIO 작성 시점)" 및 "**공통 불변**: 어느 트랙이든 ① 테스트 코드 산출물 ② 작성자≠구현자 ③ TEST 단계 검증을 유지한다"(`opal/core/references/harness/red-first.md:33-45`). 즉 §1.5 인접 위치가 "언제 무엇을 판단/도출하는가"를 다루는 자연 지점이며, R-1이 지목한 삽입 위치와 정합한다.

#### 2.1.3 영향 범위

- **상위 의존(이 문서를 인용하는 쪽)**: `opal-harness.md:111`(모듈 등록), `coding-principles.md:53`(§4 인용), `opal/agents/opal-test-agent/AGENT.md:91`(SSOT 지정), `op-dev-test-scenario/SKILL.md:60`, `op-dev-execute/SKILL.md:115`, opds `:41,:85`, opd `:86,:108`, 그리고 **8개 도구 테스트 스위트에서 `red-first.md §2/§3/§4/§5` 절 번호 직접 인용 60건 이상**(`opal/tools/{test-tool,memory-tool,state-tool,brain-tool,improve-tool,tool-scan,backlog-tool,code-scan,opal-agent}/tests/*`).
- **하위 의존**: `opal/core/PRINCIPLES.md` §4 (상속, 재서술 금지).
- **결론(H-f)**: **기존 §번호 재부여 절대 금지.** 신설 절은 §1.5와 §2 사이에 **§1.6**으로 삽입한다.

---

### F-002: 도출 엔진 2계열 분할 — `test-scenario-guide.md` Step 1 재구성

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | TEST-SCENARIO 도출 엔진 (213줄, opd·opds·opsdd 공용) | 수정 |
| 스킬 | `opal/skills/op-dev-test-scenario/SKILL.md` | 통일 형식 SSOT + PM Gate 7대 룰 | 미변경 (§규칙 소유권 표 미접촉 확정 2) |
| 가이드 | `opal/core/references/harness/scenario-gate.md` | 루브릭 6축 정의 SSOT (§2) | 미변경 (본 F에서는 참조만) |

#### 2.2.2 현재 구현

- §목적 3항목 (`:11-17`): ① 리스크 가설 기반 시나리오 설계(+ "self-confirming 방지를 위해 PLAN 작성자(opal-plan-agent)와 다른 작성자가 수행" — **RULE-A4 기존 SSOT**) ② TDD red-green 연결 ③ 목표 달성(채택 관점) 검증.
- §작성 프로세스 Step 1 (`:23-36`) 현행 제목: `### Step 1: PLAN 가설 표 + TASK 목표/R/채택 기준 Read`. 본문 = (가) PLAN.md §리스크 가설 표 Read 지시 5항목 + (나) "가설 없이 시나리오를 도출하면 '당연한 시나리오'만 생산된다" 경고 + (다) `**[MUST] 목표/채택 관점 도출 입력 병행**` 3항목(요구사항 R / 목표 문장 / 채택·잔존 기준).
- **즉 2계열이 이미 한 Step 안에 물리적으로 공존**한다 — (가)(나)가 PLAN 유래, (다)가 TASK 유래. R-2는 이 둘을 블록으로 갈라 선작성 가능 범위를 판별 가능하게 만드는 작업이다.
- Step 2(데이터 설계, `:38-49`)·Step 3(계층 결정, `:51-70`)은 계층 결정 규칙 표가 **"변경 영역"을 행 축**으로 쓰므로 PLAN 확정 의존 — D-6과 정합.
- Step 4-a는 `test-tool resolve` 단일 호출로 도구 결정을 위임(`:139-145`), Step 5는 4열 매핑 표.

#### 2.2.3 영향 범위

- **공용 도출 엔진**: opd STEP 3.5(`opal-pilot-dev/SKILL.md:93` "`test-scenario-guide.md`의 **5단계 프로세스** 적용"), opds STEP 2(간접), opsdd `verify-guide.md`(scenario-gate 경유), `opal-test-agent/AGENT.md:86`(탐지 4단계 인용 — Step 4-a 무관 구간).
- **앵커 인용**: `op-dev-test-scenario/SKILL.md:166,192`가 `§Step 3-b`를 인용 → Step 3-b 헤딩 불변 필수.
- **줄번호 인용**: `scenario-gate.md:12`가 `test-scenario-guide.md:11-14`(§목적)를 인용 — Step 1(23줄 이후) 편집은 11-14를 밀어내지 않으므로 **안전**.
- **결론(H-b)**: Step 번호 체계(Step 1~5)를 유지하고 **Step 1 내부만 Block A/Block B로 분할**한다. 기존 정규 문장은 삭제하지 않고 해당 Block으로 재배치한다(additive 재구성).

---

### F-003: 게이트 호출 시점 규율 — `scenario-gate.md` §4

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/harness/scenario-gate.md` | 목표-커버 게이트 규칙 SSOT (99줄) | 수정 (§4에 [MUST] 블록 추가) |
| 스킬 | `opal/skills/op-scenario-gate/SKILL.md` | 게이트 루프 배선 스킬 | 미변경 (호출 시점은 호출자 책임) |
| 소스 | `opal/tools/state-tool/state_tool.py` | `check_stage_transition_guard` (`:634`) | 미변경 (**도구 변경 0** 검증용) |
| 소스 | `opal/tools/test-tool/lib/scenario.py` | `scenario-coverage-check` 핸들러 (`:475`) | 미변경 |

#### 2.3.2 현재 구현

- §2 루브릭 6축 + 판정 주체 분리: ②③④ = test-tool 결정론 / ①⑤⑥ = opal-evaluator-agent 판단.
- §3 정규화 계약: 입력 페이로드 `{goal, requirements, features, hypotheses, scenarios[]}`. **`goal`·`requirements`는 TASK 유래 / `features`·`hypotheses`는 PLAN 유래** — 계열 경계의 계약적 근거. 출력 결정론 파트: "`missing`의 세 배열 중 하나라도 비어있지 않으면 FAIL".
- §4 루프 프로세스: 5단계 + `[MUST] Producer≠Evaluator`. **호출 시점(언제 1회 호출하는가)에 대한 규정은 현재 없다** — R-3이 채우는 공백.
- §5 종료조건 3종, §6 tool-gated 집행.
- 도구 층 실측: `check_stage_transition_guard(state, row_index, command, force=False, scope)` — PM 경로는 `scope="full"`로 "대상 행 앞의 **모든** 행이 완료"를 요구(`state_tool.py:634-645`), `advance`는 `force=False` 하드코딩(`:1422-1423`). 따라서 opds `plan.scenario_gate`(id 4)는 `plan.plan_md`(id 3) 완료 전 advance 불가, opd `test_scenario.scenario_gate`(id 10)는 id 1~9 완료 전 advance 불가 — **조기 호출이 도구 층에서 이미 부분 차단**된다.

#### 2.3.3 영향 범위

- `opal-evaluator-agent/AGENT.md:69,186`이 `scenario-gate.md` §2·§5를 인용 → §2·§5 무변경 필수.
- `op-scenario-gate/SKILL.md:15,27,121,124,128,151-154`가 §2·§3·§4·§5·§6을 인용 → **§번호 재부여 금지**, §4 내부 추가만 허용.
- `opal-pilot-sdd/SKILL.md:170`·`verify-guide.md:143,145`가 규칙 SSOT로 지정 — opsdd는 본 태스크 범위 밖(배선 미변경)이나 §4 추가 규율은 SSOT 상속으로 자동 적용된다. 이는 의도된 효과이며 opsdd 배선 변경 없이 규율만 전파된다.

---

### F-004: opds 배선 — `opal-pilot-dev-short/SKILL.md` STEP 2

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-dev-short/SKILL.md` | Short Task 오케스트레이터 (364줄) | 수정 (STEP 2) |
| 오케스트레이터 | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | 11 task-step SSOT | 미변경 (**행 구조 불변** 검증용) |

#### 2.4.2 현재 구현

- `## STEP 2: PLAN` 구성: (i) `[MUST] RED-first` 콜아웃(`:41`) → (ii) `### PLAN 디스패치` + Short Task 분석 깊이 주의 + PM 컨텍스트 주입 → (iii) producer 확립 인용 블록(`:54-56`) "op-dev-plan 워커는 PLAN.md만 작성한다 … PLAN.md **수신 후**, 알투(PM) + 캡틴 페어가 … TEST-SCENARIO.md를 직접 작성한다 … 문서 전용 작업 시 스킵(게이트도 자연 스킵)" → (iv) "PLAN.md + TEST-SCENARIO.md 작성 완료 → **목표-커버 게이트**" + verdict 분기 4 bullet → (v) PM Gate 검증 체크리스트 7항목 → (vi) 사용자 확인 P-5.
- `pipeline.json`: `plan.plan_md`(id 3) → `plan.scenario_gate`(id 4) → `plan.pm_gate`(id 5, gate.artifacts에 `TEST-SCENARIO.md` 이미 포함) → `plan.user_confirm`(id 6).
- 즉 **현행은 "PLAN.md 수신 후" 순차**이며, 병렬 선작성은 신규 배선이다(TASK.md §배경 분석 5).

#### 2.4.3 영향 범위

- STEP 2 (v) PM Gate 체크리스트는 산문 bullet — [MUST] `docs/CONVENTIONS.md` §State 관리: "**PM Gate 정의의 SSOT는 pilot `references/pipeline.json`의 `task_steps[].gate`**(`artifacts`·`checklist`)다 — SKILL.md에 산출물·체크리스트를 표로 중복 게재하지 않는다." → **체크리스트 항목을 SKILL.md에 표로 추가하지 않는다.** 선작성/PLAN 불일치 표면화는 배선 산문으로 기술한다.
- `plan.scenario_gate` mark 조건은 "STATE.md 도메인 치환값" 절(`:334`)에도 명시됨 — 해당 문장은 무변경(게이트 mark 조건 자체가 바뀌지 않음).

---

### F-005: opd 배선 — `opal-pilot-dev/SKILL.md` STEP 3(PLAN) + STEP 3.5

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | Full Task 오케스트레이터 (390줄) | 수정 (STEP 3 §3-1, STEP 3.5) |
| 오케스트레이터 | `opal/skills/opal-pilot-dev/references/pipeline.json` | 16 task-step SSOT | 미변경 (**행 구조 불변** 검증용) |

#### 2.5.2 현재 구현 — **문서/코드 불일치 발견 (H-h)**

실측 헤딩 구조: `## STEP 1: TASK` → `## STEP 2: ANALYSIS` → `## STEP 3: PLAN`(`### 3-1. PLAN 디스패치` + PM Gate 4항목) → `## STEP 3.5: TEST-SCENARIO`(1~6 절차) → `## STEP 4: EXECUTE` → `## STEP 5: TEST` → `## STEP 6: CLOSE`.

**TASK.md R-5 및 디스패치 프롬프트의 참조 문서 표는 "STEP 2(PLAN)"으로 기재했으나, 실제 문서의 STEP 2는 ANALYSIS이고 PLAN은 STEP 3이다.** 문서/코드 불일치 규칙에 따라 **실제 문서(코드) 기준**으로 작업한다 → 선작성 착수 지시는 `## STEP 3: PLAN` `### 3-1. PLAN 디스패치` 하위에 배선한다. R-5 AC의 실질("STEP 2에 선작성 착수 지시가 존재")은 "PLAN 디스패치 절에 선작성 착수 지시가 존재"로 충족 판정한다.

- STEP 3.5 현행 절차: 작성자 명시(PM+캡틴, "self-confirming 방지를 위해 PLAN 워커(opal-plan-agent)와 다른 작성자가 수행") → 1. PLAN.md §리스크 가설 표 Read → 2. 통일 형식 따라 작성 → 3. `test-scenario-guide.md` **5단계 프로세스** 적용 → 4. `test_scenario.test_scenario_md` mark → 5. 목표-커버 게이트(advance + op-scenario-gate + verdict 4분기) → 6. 사용자 보고.
- STEP 4 EXECUTE 디스패치 프롬프트가 `**scenario_source**` + `**완료 기준**: checklist 100% + 담당 Step 매핑 L1/L2 시나리오 PASS`를 소비(`:214-216`) — 완료기준 사전 잠금의 실체. 본 태스크는 이 순서를 건드리지 않는다(D-1 기각안과의 차이).

#### 2.5.3 영향 범위

- STEP 3 PM Gate 4항목(bullet)·STEP 3.5 절차 번호(1~6)를 소비하는 외부 인용 없음 → 절차 항목 내용 수정 가능. 단 `test_scenario.*` task-step key 문자열은 `pipeline.json` SSOT → 문자 단위 불변.
- opd `plan.pm_gate`(id 7) gate.artifacts = `["TASK.md","PLAN.md"]` — TEST-SCENARIO.md 미포함. 즉 opd에서는 선작성 초안 파일이 PLAN PM Gate 시점에 존재해도 게이트 판정에 영향이 없다(artifacts 존재 검증만 수행). **`pipeline.json` 무변경으로 안전**.
- `docs/PROJECT.md:202` "opd STEP 3.5 접합 — pipeline.json `test_scenario.scenario_gate` 행이 EXECUTE 진입을 구조적 차단" — 서술이 여전히 유효하나 "선작성 트랙" 사실이 추가되므로 F-006 후속 docs/ 갱신 Step 대상.

---

### F-006: 변경이력 + install 재배포 + 배포본 정합

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드/오케스트레이터 | 위 5문서의 `## 변경이력` 표 | 변경이력 행 추가 | 수정 (각 파일 편집 Step에 포함) |
| 배치 | `scripts/install-mac.sh` | `~/.opal/` 재배포 | 실행 (미변경) |
| 문서 | `docs/PROJECT.md` | §주요 컴포넌트(목표-커버 게이트) + 작업 히스토리 | 수정 |

#### 2.6.2 현재 구현

- `install-mac.sh` 변환 로직 실측: `strip_deploy_md()` (`:219-222`)와 `strip_deploy_md_recursive()` (`:227-232`) 가 `/usr/bin/awk 'BEGIN{keep=1} /^## 변경이력$/{keep=0} keep==1{print}'` 로 **`## 변경이력` 헤딩부터 파일 끝까지 제거**한다. 적용 지점: `strip_deploy_md_recursive "$opal_home/skills"` (`:1071`), `strip_deploy_md_recursive "$ref_dst"` (`:1571`).
- 5문서 전부 `## 변경이력` 헤딩 표기가 정확히 일치 → strip 대상.
- 배포 경로 실측(존재 확인): `~/.opal/references/harness/red-first.md`, `~/.opal/references/harness/scenario-gate.md`, `~/.opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`, `~/.opal/skills/opal-pilot-dev-short/SKILL.md`, `~/.opal/skills/opal-pilot-dev/SKILL.md`.
- **사전 실측(baseline)**: 현 시점에서 `diff <(strip 소스) 배포본` 이 5/5 **IDENTICAL** — 즉 "strip-후 diff 0건"이 달성 가능한 AC임이 검증되었다(H-g 해소 근거).
- 버전 현황: `red-first.md` v1.0 / `scenario-gate.md` v1.0 / `test-scenario-guide.md` v2.7 / opds v4.5 / opd v4.9. pilot 2종 SKILL.md frontmatter에는 `version` 키가 없다(변경이력 표만 갱신).

#### 2.6.3 영향 범위

- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(138)`."
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다."
- install은 전 스킬·참조 문서를 재배포하므로 5문서 외 파일의 배포본도 갱신될 수 있다 — 정합 검증은 **본 태스크 5파일에 한정**한다(PRINCIPLES §3).

---

## 3. 기능별 설계

### F-001: 선작성 트랙 규칙 정의 — `red-first.md` §1.6 신설

#### 3.1.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/red-first.md` | 가이드 | `## 1.5 적용 기준` 절 **직후**, `## 2. 작성자≠구현자` **직전**에 `## 1.6 목표계열 선작성 트랙 (PLAN 병렬)` 신설. 기존 §0~§6 헤딩 문자열 불변 | (→ D-2) R-1 / H-f |
| 2 | 동 파일 `## 변경이력` 표 | 가이드 | v1.1 행 추가 (F-006 병합 — 동일 파일이므로 같은 Step에서 순차 편집) | (→ D-11) R-6 |

#### 3.1.2 설계 — §1.6 절 구조 명세

신설 절은 **리드 문단 + 6개 항목 (a)~(f)**를 순서대로 담는다. **(a)(b)(c)는 R-1 AC 필수 3항목**이며 각 항목에 근거 인용을 붙인다.

**(리드) 트랙 목적 = 품질(관점 편향 차단). 효율은 목적이 아니다** — 095 자기적용 실측 반영 (개선 A).
- 문장: "본 트랙의 목적은 **도출 엔진의 관점 편향 차단**이다 — PLAN.md를 읽지 않은 상태에서 목표로부터 시나리오를 도출해, 리스크 가설(파괴 관점)에 갇혀 목표 달성(채택 관점) 시나리오가 누락되는 070 실패모드를 구조적으로 막는다."
- 문장: "**wall-clock 단축은 본 트랙의 목적이 아니다.** 선작성 소요가 PLAN 워커 실행 구간에 숨는 만큼의 절감은 있으나, PLAN 확정 후 보강 라운드에서 정정 비용이 발생하여 순 절감은 작다."
- 근거 인용: `tasks/095-260819-opds-시나리오-목표계열-선작성/DONE.md` §자기적용 실측 — 최초 적용 태스크(095)에서 PLAN 워커 소요 18분 30초 중 선작성 5분이 숨었으나 보강이 8분으로 늘어 순 절감은 약 7%에 그쳤고, 반면 선작성 고유 시나리오 3건(채택 검증·음성통제·목표 달성)이 PLAN 유래 도출(TS-001~029)에서 **대응 0건**으로 확인되어 품질 이득이 실측됐다.
- 규범 문장: "따라서 효율을 기대해 본 트랙을 켜지 말고, **관점 편향 위험이 실재하는 태스크**(교체형 목표·핵심 목표가 파괴 관점으로 환원되지 않는 태스크)에서 켠다."

> **[명세 근거]** 개선 A는 R-1 AC 범위 내 문구 확정이다(신규 요구사항 아님). 근거: 095 실사용 관측 — 효율을 목적으로 서술하면 후속 사용자가 잘못된 기대로 트랙을 켜고, 소규모 태스크에서 오히려 지연을 겪는다. [MUST] `.opal/AGENT.md` §프로젝트별 추가 지침: "프레임워크-우선 개선 원칙 — 에이전트 행동 개선 필요를 발견하면 프레임워크 소스 SSOT에 규칙을 반영하고 install로 배포한다."


**(a) 선작성 가능 입력 3종 (TASK 유래)** — RULE-A2 정의. 표 형식으로 3행:

| # | 입력 | 원천 | 대응 루브릭 축 | 근거 |
|---|------|------|--------------|------|
| 1 | 목표 문장 | TASK.md §작업 목표 | ① 목표 달성 | `scenario-gate.md` §3 정규화 계약 `goal` |
| 2 | 요구사항 R 전체 목록 | TASK.md §요구사항 | ② 요구 커버 | 동 §3 `requirements` |
| 3 | (교체형 목표인 경우) 채택/잔존 기준 | TASK.md | ⑤ 채택/잔존 | 동 §2 ⑤ |

- 규범 문장: "이 3종 **밖의 입력을 선작성에 쓰지 않는다** — 특히 PLAN.md를 읽지 않는다(PLAN 관점 오염 차단)."
- 경계 근거 문장: "게이트 정규화 계약에서 `goal`·`requirements`는 TASK 유래이고 `features`·`hypotheses`만 PLAN 유래다 — 이 경계가 선작성 가능 범위의 계약적 근거다 (→ `opal/core/references/harness/scenario-gate.md` §3)."
- 절차 위임 포인터: "계열↔축 매핑과 도출 절차는 `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §작성 프로세스 Step 1이 SSOT다."

**(b) [MUST] PLAN 확정 후 ③④축 보강 필수** — RULE-A3 정의.
- 문장: `[MUST]` 선작성 초안만으로 TEST-SCENARIO 작성을 종료하지 않는다. PLAN.md 확정 후 PLAN 유래 계열(`features` F-NNN · `hypotheses` H-N)을 도출 입력에 추가하여 루브릭 ③기능커버·④리스크커버를 보강한다.
- 근거 인용: `[MUST]` `opal/core/references/harness/scenario-gate.md` §2: "③ 기능 커버 | PLAN F ↔ 시나리오 매핑 완전 | test-tool(결정론)".
- 절차·완료 판정 위임: "보강 절차와 완료 판정 3조건은 `test-scenario-guide.md` §작성 프로세스 Step 1 Block B가 SSOT다."

**(c) [MUST] 작성자≠PLAN 워커 불변** — RULE-A4 **포인터**(신규 정의 금지).
- 문장: `[MUST]` 선작성 주체는 알투(PM)+캡틴 페어이며 PLAN.md 작성 주체(`opal-plan-agent`)와 분리 유지한다. 도출 시점이 앞당겨져도 이 분리는 변하지 않는다.
- 근거 인용: `[MUST]` `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §목적 1: "self-confirming 방지를 위해 PLAN 작성자(opal-plan-agent)와 다른 작성자가 수행." / 채점 측 분리는 `scenario-gate.md` §4 Producer≠Evaluator.

**(d) RED→GREEN 순서 불변** — RULE-A5 재확인 포인터.
- 문장: 본 트랙은 시나리오 **도출 시점만** 앞당기며 §1 RED→GREEN 순서와 §1.5 강제/허용 분기를 변경하지 않는다. 선작성은 RED 테스트 코드 작성이 아니다(마크다운 시나리오 초안 작성이며, RED 테스트 코드 작성 주체는 §2에 따라 `opal-test-agent(mode: red)`로 유지된다).
- 근거: `opal/core/references/harness/red-first.md` §1 (동일 문서 자기참조) / TASK.md §확정된 설계 방향 D-8.

**(e) 게이트 호출 금지 구간** — RULE-C1 포인터.
- 문장: 선작성 시점(PLAN 워커 실행 중)에는 목표-커버 게이트를 호출하지 않는다. 호출 시점 규율 SSOT는 `opal/core/references/harness/scenario-gate.md` §4.

**(f) 트랙 성격 = opt-in (자연 스킵 보존)** — H-i 방어.
- 문장: 본 트랙은 강제가 아니다. 선작성을 착수하지 않고 PLAN 확정 후 Block A·B를 연속 수행해도 결과는 동등하다(순차 경로 = 현행 동작). 문서 전용 작업 등 TEST-SCENARIO.md 자체가 스킵되는 경로에서는 본 절도 자연 스킵된다.
- **착수 판단 기준** (개선 D — 095 자기적용 실측 반영):

| 조건 | 판단 |
|------|------|
| PLAN 워커 예상 소요가 선작성 소요보다 **길다** | 선작성 유리 — 선작성이 PLAN 구간에 숨는다 |
| PLAN 워커 예상 소요가 선작성 소요보다 **짧거나 비슷하다** (소규모 태스크) | **순차 권장** — 선작성이 PLAN을 기다리게 만들어 오히려 지연된다 |
| 목표가 파괴 관점(리스크 가설)으로 환원되지 않는다 / 교체형 목표다 | 선작성 유리 — 관점 편향 위험이 실재한다 |
| 목표가 단일 결함 수정이고 검증 관점이 파괴 관점과 사실상 일치한다 | **순차 권장** — 선작성의 품질 이득이 발생하지 않는다 |

- 규범 문장: "예상 소요를 사전에 정확히 알 수 없으므로, **판단이 서지 않으면 순차(현행)를 택한다** — 순차는 결과가 동등하고 정정 전파 위험이 없다."
- 리스크 문장: "선작성한 시나리오가 PLAN 확정 후 보강에서 절반 이상 수정·삭제되면, 그 태스크는 선작성 부적격이었다는 신호다 — 다음 태스크의 착수 판단에 반영한다."
- 근거: 095 실측 — 선작성 단계의 미검증 전제(TASK.md의 오배선 지목)가 시나리오 3곳으로 전파되어 정정 지점이 순차 대비 2곳 늘었다(`AGENTIC-LOG.md` #8~#9).

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음 (install 재배포는 F-006).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (a) | 산출물 검사 | `red-first.md` §1.6에 선작성 가능 입력 3종(목표 문장·요구사항 R·채택/잔존 기준)이 열거되고 각 행에 근거 인용이 존재 |
| TS-002 | R-1 AC (b) | 산출물 검사 | §1.6에 `[MUST]` 토큰이 붙은 "PLAN 확정 후 ③④축 보강 필수" 문장 + `scenario-gate.md` §2 근거 인용 존재 |
| TS-003 | R-1 AC (c) | 산출물 검사 | §1.6에 `[MUST]` 작성자≠PLAN 워커 문장 + `test-scenario-guide.md` §목적 1 원문 인용 존재 |
| TS-004 | H-f | 회귀 테스트 | `grep -c '^## [2-6]\.' red-first.md` 결과가 변경 전과 동일하고, `## 2. 작성자≠구현자`/`## 3. 테스트 불변성`/`## 4. 공개 인터페이스 검증`/`## 5. graceful skip`/`## 6. STATE 행 정책` 5개 헤딩 문자열이 문자 단위 불변 |
| TS-005 | H-i | 산출물 검사 | §1.6 (f)에 opt-in·자연 스킵 문구 존재 |

---

### F-002: 도출 엔진 2계열 분할 — `test-scenario-guide.md` Step 1 재구성

#### 3.2.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §작성 프로세스 Step 1 | 가이드 | Step 1을 계열 매핑 표 + `#### Block A`(TASK 유래) + `#### Block B`(PLAN 유래) + `#### 선작성 대상이 아닌 Step` 4블록으로 재구성. Step 번호 체계(Step 1~5) 불변 | (→ D-4) R-2 / H-b |
| 2 | 동 파일 §작성 체크리스트 | 가이드 | 3행 추가(⑥축 포함 / 마커 0건 / 초안 대조 수정·삭제) | R-2 AC 보강 |
| 3 | 동 파일 `## 변경이력` 표 | 가이드 | v2.8 행 추가 | R-6 |

> **[MUST] 삭제 금지 목록** — 아래 기존 정규 문장은 Block으로 **재배치만** 하고 내용을 삭제·약화하지 않는다: (i) PLAN.md §리스크 가설 표 Read 5항목 (ii) "가설 없이 시나리오를 도출하면 '당연한 시나리오'만 생산된다 — PLAN.md 가설 표가 누락되었으면 PLAN 단계로 되돌아간다" (iii) `[MUST] 목표/채택 관점 도출 입력 병행` 3항목. 근거: H-b (opd 공용 엔진 회귀 방지) / [MUST] `opal/core/PRINCIPLES.md` §3: "Touch only what the plan names. Don't improve adjacent code."

#### 3.2.2 설계 — Step 1 재구성 명세

**새 Step 1 제목**: `### Step 1: 도출 입력 2계열 Read (Block A: TASK 유래 / Block B: PLAN 유래)`

**리드 문단 + 계열 매핑 표 (RULE-B1·B2 정의)**:

| 계열 | 도출 입력 | 원천 | 커버 루브릭 축 | 선작성 가능 |
|------|----------|------|--------------|-----------|
| **Block A. 채택 관점 (TASK 유래)** | 목표 문장 / 요구사항 R 전체 / (교체형 시) 채택·잔존 기준 | TASK.md | ① 목표달성 ② 요구커버 ⑤ 채택·잔존 ⑥ 경계·부정 | ✓ PLAN 워커 실행과 병렬 |
| **Block B. 파괴 관점 (PLAN 유래)** | 리스크 가설 H-N / 기능 F-NNN | PLAN.md §리스크 가설 표 · §1.2 기능 목록 | ③ 기능커버 ④ 리스크커버 | ✗ PLAN 확정 필요 |

- 표 하단 주석: "루브릭 6축의 **정의·판정 주체**는 `opal/core/references/harness/scenario-gate.md` §2가 SSOT다 — 본 표는 계열↔축 매핑만 소유한다." (RULE-C3 이중화 차단)
- 리드 문단 포인터: "트랙 규칙 SSOT: `opal/core/references/harness/red-first.md` §1.6."

**`#### Block A. 채택 관점 입력 (TASK 유래 — 선작성 가능)`**
- 기존 `[MUST] 목표/채택 관점 도출 입력 병행` 3항목을 이 블록으로 이동(문장 보존) + 각 항목에 대응 축 인라인 표기(→ `scenario-gate.md` §2 ①/②/⑤).
- **신설 `[MUST]` ⑥경계·부정 축 동시 도출** (H-a 방어 1): "Block A만으로 도출할 때 AC를 그대로 옮긴 '당연한 시나리오'만 남으면 self-confirming 구조로 퇴행한다(근거: `scenario-gate.md` §1 '도출 엔진의 관점 편향'). Block A 산출에는 **⑥경계·부정 축 시나리오를 최소 1건 포함**한다 — 각 R의 경계값·부정 경로(실패·거부·미충족 입력)를 R별로 1회 이상 질의하여 도출한다."
- **신설 선작성 시 `[MUST]` 3항목** (RULE-B3, H-c·H-d 방어):
  1. 초안은 별도 임시 파일을 만들지 않고 **TEST-SCENARIO.md 본문에 직접** 작성한다 (태스크 폴더 밖 산출물 금지 / STATE 행 신설 금지 — 도구 변경 0).
  2. Block B 보강이 필요한 지점에 보강 대기 마커 `<!-- PENDING-BLOCK-B -->` 를 남긴다. 최소 2곳 — §1 리스크 가설 표, §4 매핑 표의 "가설 ID" 열.
  3. 이 시점에 목표-커버 게이트를 호출하지 않는다 (→ `scenario-gate.md` §4).

**`#### Block B. 파괴 관점 입력 (PLAN 유래 — PLAN 확정 후)`**
- 기존 (i) PLAN.md §리스크 가설 표 Read 5항목 + (ii) "가설 없이…되돌아간다" 경고를 이 블록으로 이동(문장 보존).
- 신설 1줄: "PLAN.md §1.2 기능 목록에서 F-NNN 전체를 Read하여 §4 매핑 표의 전 F 커버 여부를 확인한다 (→ `scenario-gate.md` §2 ③)."
- **신설 `[MUST]` 보강은 additive-only가 아니다** (RULE-B5, H-a 방어 2): "선작성 초안이 있는 경우 Block B 보강을 시나리오 추가만으로 끝내지 않는다. 초안의 각 시나리오를 H-N·F-NNN과 대조하여 **중복·과잉·PLAN 설계와 어긋나는 시나리오를 수정 또는 삭제**한다. 선작성 초안과 PLAN 설계의 불일치는 그 자체가 조기 경보 신호이므로 PM Gate에서 표면화한다."
- **신설 보강 완료 판정 3조건** (RULE-B4):
  1. `<!-- PENDING-BLOCK-B -->` 마커 0건 (grep 확인)
  2. §1 리스크 가설 표에 PLAN.md H-N 전건 전재
  3. §4 매핑 표의 모든 시나리오 행에 가설 ID·검증 계층이 채워짐
- 문장: "목표-커버 게이트는 이 3조건 충족 상태에서만 호출한다 (→ `scenario-gate.md` §4)."

**`#### 선작성 대상이 아닌 Step`** (RULE-B6, D-6):
- `[MUST]` Step 2(데이터 설계)·Step 3(계층 결정)은 **변경 영역 의존**이므로 선작성 대상이 아니다 — 계층 결정 규칙 표(Step 3)가 "변경 영역"을 행 축으로 쓰고, Step 2 §2.1 사전 조건 데이터는 PLAN 파일 변경 계획 확정 후에만 채울 수 있다. PLAN 확정 후 Block B와 함께 수행한다. 근거: (→ D-4) `test-scenario-guide.md` §작성 프로세스 Step 2·Step 3 / TASK.md D-6.

**§작성 체크리스트 추가 3행**:
- `- [ ] (선작성 트랙 사용 시) Block A 산출에 ⑥경계·부정 축 시나리오가 최소 1건 포함되었는가?`
- `- [ ] (선작성 트랙 사용 시) <!-- PENDING-BLOCK-B --> 마커가 0건인가? (grep 확인)`
- `- [ ] (선작성 트랙 사용 시) Block B 보강에서 초안 시나리오를 H-N·F-NNN과 대조해 수정·삭제를 검토했는가?`

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | R-2 AC (2블록 분리) | 산출물 검사 | Step 1 하위에 `#### Block A`·`#### Block B` 헤딩이 각 1개 존재 |
| TS-007 | R-2 AC (축 매핑 표) | 산출물 검사 | Step 1에 계열↔루브릭 축 매핑 표가 존재하고 TASK 유래 행에 ①②⑤⑥, PLAN 유래 행에 ③④가 기재 |
| TS-008 | R-2 AC (Step 2·3 명시) | 산출물 검사 | `#### 선작성 대상이 아닌 Step` 절에 Step 2·Step 3이 선작성 대상 아님이 `[MUST]`로 기재 |
| TS-009 | H-a | 산출물 검사 | Block A에 ⑥경계·부정 최소 1건 `[MUST]`, Block B에 additive-only 금지 `[MUST]`가 각각 존재 |
| TS-010 | H-b | 회귀 테스트 | `grep -c '^### Step '` 결과가 변경 전과 동일(Step 1~5 유지) / `### Step 3-b:` 헤딩 불변 / 삭제 금지 목록 (i)(ii)(iii) 문장 전건 잔존 |
| TS-011 | H-c | 산출물 검사 | "별도 임시 파일을 만들지 않고 TEST-SCENARIO.md 본문에 직접" 규정 + `<!-- PENDING-BLOCK-B -->` 마커 포맷 정의가 존재 |

---

### F-003: 게이트 호출 시점 규율 — `scenario-gate.md` §4

#### 3.3.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/scenario-gate.md` §4 루프 프로세스 | 가이드 | 기존 `[MUST] Producer≠Evaluator` 인용 블록 **직후**에 `[MUST] 호출 시점` 인용 블록 신설(3문단: 규율 / 금지 근거 / 도구 층 정합). §1·§2·§3·§5·§6 무변경 | (→ D-3) R-3 |
| 2 | 동 파일 `## 변경이력` 표 | 가이드 | v1.1 행 추가 | R-6 |

#### 3.3.2 설계 — §4 추가 블록 명세

**문단 1 — 규율 (RULE-C1)**:
> `[MUST] 호출 시점 — PLAN 확정 + 보강 완료 후 1회`: 목표-커버 게이트는 ① PLAN.md 확정(F-NNN·H-N 확정) **AND** ② 도출 입력 2계열 보강 완료(→ `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §작성 프로세스 Step 1 "보강 완료 판정" 3조건) 두 조건을 모두 충족한 뒤 **1회** 호출한다. 목표계열 선작성 시점(PLAN 워커 실행 중)에는 호출하지 않는다. (여기서 "1회"는 최초 진입 1회를 뜻하며, `verdict: rewrite` 수신 후의 §5-4 재작성 루프 재호출은 이 규율의 예외가 아니라 동일 게이트 1건의 반복이다.)

**문단 2 — 금지 근거 (RULE-C2, F/H 매핑 결정론)**:
> 선작성 시점에는 §3 정규화 입력의 `features`·`hypotheses`가 미확정(빈 배열 또는 부분)이다. 이 상태로 호출하면 §2 ③기능커버·④리스크커버를 결정론 판정할 수 없고, §3 "`missing`의 세 배열 중 하나라도 비어있지 않으면 FAIL(§2 ②③④ 미달)"에 따라 확정 FAIL이 되어 §5-2 반복 상한을 무의미하게 소모한다. 트랙 규칙 SSOT는 `opal/core/references/harness/red-first.md` §1.6이다.

**문단 3 — 도구 층 정합 (H-d 보강)**:
> **도구 층 보강 집행**: pilot의 게이트 행(opd `test_scenario.scenario_gate` / opds `plan.scenario_gate`)은 state-tool stage-transition guard가 앞 행 전부 완료를 요구하므로(`opal/tools/state-tool/state_tool.py:634`, advance 경로는 `force=False` 하드코딩 `:1423`), PLAN.md 작성 행 미완 상태의 조기 `advance`는 `stage_transition_violation`으로 거부된다. 본 규율은 그 도구 집행과 정합하는 산문 규율이며, 도구 코드를 변경하지 않는다.

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R-3 AC ([MUST] 호출 시점) | 산출물 검사 | §4에 `[MUST]` 토큰이 붙은 호출 시점 문장이 존재하고 "PLAN 확정"·"보강 완료"·"1회" 3요소를 모두 포함 |
| TS-013 | R-3 AC (금지 근거) | 산출물 검사 | §4에 선작성 시점 호출 금지 근거(F/H 미확정 → ③④ 결정론 판정 불가)가 §3 인용과 함께 기재 |
| TS-014 | H-d | 통합 테스트 | opds 태스크에서 `plan.plan_md` 미완 상태로 `advance --task-step plan.scenario_gate` 호출 시 `stage_transition_violation` 반환(도구 무변경 실증) |
| TS-015 | RULE-C3 | 회귀 테스트 | `scenario-gate.md` §1·§2·§3·§5·§6 구간 diff 0건 (변경이력·§4 외 무변경) |

---

### F-004: opds 배선 — `opal-pilot-dev-short/SKILL.md` STEP 2

#### 3.4.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-dev-short/SKILL.md` STEP 2 | 오케스트레이터 | producer 인용 블록 뒤에 `### TEST-SCENARIO 작성 — 목표계열 선작성 → 보강 → 게이트 (3단계)` 소절 신설. 기존 게이트 호출 서술을 (c) 하위로 재배치(bullet 4종 문안 보존). `[MUST] RED-first` 콜아웃(`:41`)에 §1.6 포인터 1구 추가 | (→ D-5) R-4 |
| 2 | 동 파일 `## 변경이력` 표 | 오케스트레이터 | v4.6 행 추가 | R-6 |

#### 3.4.2 설계 — STEP 2 배선 명세 (WIRE-D)

**소절 헤딩**: `### TEST-SCENARIO 작성 — 목표계열 선작성 → 보강 → 게이트 (3단계)`

**리드 인용 블록** (기존 producer 확립 문안 보존 + SSOT 포인터 추가):
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
- 기존 bullet 4종(탐색 경로 / 입력 `pilot: opds` / verdict pass·rewrite·escalate 처리 / 문서 전용 자연 스킵)을 **문안 그대로** 이 하위에 둔다.
- 추가 1줄: "`plan.scenario_gate` 행 mark 시점은 **(c)의 `verdict: pass` 수신 이후**다 — (a)·(b) 시점에는 mark하지 않는다."

> **[MUST] 금지**: PM Gate 검증 체크리스트에 항목을 추가하지 않는다. 근거: `[MUST]` `docs/CONVENTIONS.md` §State 관리: "**PM Gate 정의의 SSOT는 pilot `references/pipeline.json`의 `task_steps[].gate`**(`artifacts`·`checklist`)다 — SKILL.md에 산출물·체크리스트를 표로 중복 게재하지 않는다." → 기존 STEP 2 PM Gate 체크리스트 7항목은 무변경.

**RED-first 콜아웃 보강** (`:41`): 기존 문장 끝에 " 목표계열 선작성 트랙은 동 문서 §1.6." 1구 추가.

#### 3.4.3 환경 변경
해당 없음.

#### 3.4.4 배치/마이그레이션
해당 없음. `references/pipeline.json` **미변경**(행 11개·gate 정의 불변).

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-016 | R-4 AC (a)(b)(c) 순서 | 산출물 검사 | STEP 2 안에 (a) 선작성 착수 → (b) 보강 → (c) 게이트 1회 호출이 이 순서로 기재 |
| TS-017 | R-4 AC (mark 시점) | 산출물 검사 | `plan.scenario_gate` 행 mark 시점이 (c) `verdict: pass` 이후임이 명시 |
| TS-018 | H-e | 산출물 검사 | STEP 2에 규칙 본문 신설 0건 — 선작성 입력 3종 열거·루브릭 축 정의·보강 완료 3조건 본문이 SKILL.md에 재서술되지 않고 포인터만 존재 |
| TS-019 | H-i / CONVENTIONS §State | 회귀 테스트 | "문서 전용 작업 시 스킵(게이트도 자연 스킵)" 문구 잔존 / PM Gate 체크리스트 7항목 diff 0건 / `pipeline.json` diff 0건 |

---

### F-005: opd 배선 — `opal-pilot-dev/SKILL.md` STEP 3(PLAN) + STEP 3.5

#### 3.5.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-dev/SKILL.md` `## STEP 3: PLAN` `### 3-1. PLAN 디스패치` | 오케스트레이터 | `**model**: advanced` 줄 직후에 "목표계열 선작성 착수(병렬)" 인용 블록 신설 | (→ D-6) R-5 / H-h |
| 2 | 동 파일 `## STEP 3.5: TEST-SCENARIO` | 오케스트레이터 | 절차 1을 "Block B 보강"으로 재작성, 2·3 유지, 4에 보강 완료 판정 확인 추가, 5에 "보강 완료 이후 1회" 전제 명시 + mark 시점 1줄 추가. `[MUST] RED-first` 콜아웃(`:86`)에 §1.6 포인터 1구 추가 | (→ D-6) R-5 |
| 3 | 동 파일 `## 변경이력` 표 | 오케스트레이터 | v5.0 행 추가 | R-6 |

> **[MUST] 위치 정정**: 선작성 착수 지시는 `## STEP 3: PLAN`에 넣는다. `## STEP 2: ANALYSIS` 절은 **diff 0건**을 유지한다. TASK.md R-5의 "STEP 2(PLAN)" 표기는 실제 문서와 불일치하며(실측: STEP 2 = ANALYSIS / STEP 3 = PLAN), 문서/코드 불일치 규칙에 따라 실제 문서 기준으로 배선한다 (H-h).

#### 3.5.2 설계 — STEP 3 / STEP 3.5 배선 명세 (WIRE-E)

**STEP 3 §3-1 추가 인용 블록**:
> **목표계열 선작성 착수 (PLAN 병렬)**: 위 PLAN 워커 디스패치와 **동시에**, 알투(PM)+캡틴 페어가 TASK.md만으로 Block A(채택 관점 — 목표 문장 · 요구사항 R 전체 · 교체형 시 채택/잔존 기준)를 도출해 TEST-SCENARIO.md 초안을 선작성한다. PLAN.md를 읽지 않은 상태에서 도출하여 PLAN 관점 오염을 원천 차단한다. 초안은 별도 임시 파일 없이 TEST-SCENARIO.md 본문에 직접 쓰고 보강 대기 마커를 남긴다.
>
> 이 시점에 목표-커버 게이트를 호출하지 않으며 `test_scenario.*` 행을 advance/mark하지 않는다. 선작성 초안과 PLAN.md 설계의 불일치는 PLAN PM Gate 시점의 조기 경보로 취급하여 사용자 보고에 포함한다.
>
> 규칙 SSOT: 트랙 = `opal/core/references/harness/red-first.md` §1.6 / 절차 = `op-dev-test-scenario/references/test-scenario-guide.md` §작성 프로세스 Step 1 Block A / 게이트 호출 시점 = `opal/core/references/harness/scenario-gate.md` §4. 선작성은 opt-in이며 미착수 시 STEP 3.5에서 Block A·B를 연속 수행한다(결과 동등).

**STEP 3.5 절차 재작성** (기존 1~6 구조·번호 유지):
1. **Block B 보강** — 선작성 초안(STEP 3 병렬 착수분)이 있으면, PLAN.md §리스크 가설 표(H-N)와 §1.2 기능 목록(F-NNN)을 도출 입력에 추가해 루브릭 ③기능커버·④리스크커버를 보강한다. 보강은 추가만이 아니라 초안 시나리오의 **수정·삭제를 포함**한다(→ `test-scenario-guide.md` §작성 프로세스 Step 1 Block B). 선작성하지 않았으면 Block A·B를 연속 수행한다(결과 동등).
2. `op-dev-test-scenario/SKILL.md`의 "TEST-SCENARIO.md 통일 형식"을 따라 TEST-SCENARIO.md를 완성 *(기존 문안 유지)*
3. `test-scenario-guide.md`의 5단계 프로세스 적용 (Step 3 계층 결정 + Step 3-b 실행 방식 M1/M2/M3 결정) *(기존 문안 그대로 — H-b 앵커 보존)*
4. **보강 완료 판정 3조건**(`test-scenario-guide.md` Step 1 "보강 완료 판정")을 충족 확인한 뒤 해당 행을 단일 mark (`... mark <task-path> --task-step test_scenario.test_scenario_md --done` — P-1)
5. **목표-커버 게이트 (1회)**: 4의 보강 완료 이후에만 호출한다 — 선작성 시점 호출 금지(`scenario-gate.md` §4). `advance <task-path> --task-step test_scenario.scenario_gate` 호출 후 `op-scenario-gate` 스킬 호출. *(기존 bullet 4종 문안 보존)* + 추가 1줄: "`test_scenario.scenario_gate` 행 mark 시점은 보강 완료(4) 후 `verdict: pass` 수신 이후다."
6. 사용자에게 TEST-SCENARIO 보고 — 승인 = EXECUTE 시작 허가 *(기존 유지)*

**RED-first 콜아웃 보강** (`:86`): 기존 문장 끝에 " 목표계열 선작성 트랙은 동 문서 §1.6." 1구 추가.

**미변경 확정**: `## STEP 2: ANALYSIS` / `## STEP 4: EXECUTE`(`scenario_source`·완료 기준 포함) / `## STEP 5: TEST` / `## STEP 6: CLOSE` / `references/pipeline.json` — 전부 diff 0건.

#### 3.5.3 환경 변경
해당 없음.

#### 3.5.4 배치/마이그레이션
해당 없음. `references/pipeline.json` **미변경**(행 16개·gate 정의 불변).

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R-5 AC (선작성 착수) | 산출물 검사 | `## STEP 3: PLAN` §3-1 하위에 선작성 착수 지시가 존재 |
| TS-021 | R-5 AC (보강→게이트 순서) | 산출물 검사 | STEP 3.5 절차 1이 Block B 보강, 5가 게이트 호출로 이 순서 유지 |
| TS-022 | R-5 AC (mark 시점) | 산출물 검사 | `test_scenario.scenario_gate` 행 mark 시점이 보강 완료 후임이 명시 |
| TS-023 | H-h | 회귀 테스트 | `## STEP 2: ANALYSIS` 절 diff 0건 / `## STEP 4: EXECUTE` 절 diff 0건 / `pipeline.json` diff 0건 |
| TS-024 | H-b | 회귀 테스트 | STEP 3.5 절차 3의 "5단계 프로세스" 문안 및 "Step 3-b" 인용 불변 |

---

### F-006: 변경이력 + install 재배포 + 배포본 정합

#### 3.6.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | 5문서 `## 변경이력` 표 | 가이드/오케스트레이터 | 각 1행 추가 — **각 파일의 본문 편집 Step에 병합 수행**(동일 파일 다중 편집 분리 금지) | (→ D-11) R-6 |
| 2 | `scripts/install-mac.sh` | 배치 | **실행만** (파일 미변경) | R-6 |
| 3 | `docs/PROJECT.md` | 문서 | §주요 컴포넌트(TEST-SCENARIO 목표-커버 게이트) 하단 주석에 선작성 트랙 1줄 + 작업 히스토리 표에 095 행 추가 | plan-guide.md §docs/ 갱신 Step 자동 생성 규칙 |

#### 3.6.2 설계 — 변경이력 행 문안 + 정합 검증

**변경이력 행 (일시 = 실행 시점 KST `YYYY-MM-DD HH:mm`, `node ~/.opal/tools/date/date.js datetime` 취득 — 추측 금지)**

| 파일 | 새 버전 | 변경내용 (095 포함) |
|------|--------|--------------------|
| `red-first.md` | v1.1 | `§1.6 목표계열 선작성 트랙(PLAN 병렬) 신설 — 선작성 가능 입력 3종(TASK 유래)·PLAN 확정 후 ③④축 보강 필수·작성자≠PLAN 워커 불변·RED→GREEN 순서 불변·게이트 호출 금지 구간·opt-in 성격. 기존 §2~§6 번호 불변(외부 인용 60건+ 보호) (095)` |
| `test-scenario-guide.md` | v2.8 | `§작성 프로세스 Step 1을 도출 입력 2계열로 재구성 — Block A(TASK 유래, 선작성 가능, ①②⑤⑥)/Block B(PLAN 유래, ③④) 분할 + 계열↔루브릭 축 매핑 표 + ⑥경계·부정 동시 도출 [MUST] + 선작성 초안 저장·마커 규정 + 보강 additive-only 금지 + 보강 완료 판정 3조건 + Step 2·3 선작성 제외 명시. Step 번호 체계(1~5)·Step 3-b 앵커 불변 (095)` |
| `scenario-gate.md` | v1.1 | `§4에 [MUST] 게이트 호출 시점 규율 추가 — PLAN 확정 + 보강 완료 후 1회 호출, 선작성 시점 호출 금지(F/H 미확정 → ③④ 결정론 판정 불가), state-tool stage-transition guard 정합. §1~§3·§5·§6 무변경 (095)` |
| `opal-pilot-dev-short/SKILL.md` | v4.6 | `STEP 2에 목표계열 선작성 3단계 배선 — (a) PLAN 디스패치와 동시 선작성 착수 (b) PLAN.md 수신 후 Block B 보강(수정·삭제 포함) (c) 보강 완료 후 게이트 1회 호출 + plan.scenario_gate mark 시점 명시. 규칙 본문 0줄(SSOT 포인터만), pipeline.json·PM Gate 체크리스트 무변경 (095)` |
| `opal-pilot-dev/SKILL.md` | v5.0 | `STEP 3(PLAN) §3-1에 목표계열 선작성 병렬 착수 지시 + STEP 3.5 절차 1을 Block B 보강으로 재작성·4에 보강 완료 판정·5에 게이트 1회 전제 및 test_scenario.scenario_gate mark 시점 명시. STEP 2(ANALYSIS)·STEP 4(EXECUTE)·pipeline.json 무변경 (095)` |

**install 재배포 + 정합 검증 절차 (결정론)**:
```bash
cd <프로젝트 루트>
./scripts/install-mac.sh
strip(){ /usr/bin/awk 'BEGIN{keep=1} /^## 변경이력$/{keep=0} keep==1{print}' "$1"; }
for pair in \
  "opal/core/references/harness/red-first.md|$HOME/.opal/references/harness/red-first.md" \
  "opal/core/references/harness/scenario-gate.md|$HOME/.opal/references/harness/scenario-gate.md" \
  "opal/skills/op-dev-test-scenario/references/test-scenario-guide.md|$HOME/.opal/skills/op-dev-test-scenario/references/test-scenario-guide.md" \
  "opal/skills/opal-pilot-dev-short/SKILL.md|$HOME/.opal/skills/opal-pilot-dev-short/SKILL.md" \
  "opal/skills/opal-pilot-dev/SKILL.md|$HOME/.opal/skills/opal-pilot-dev/SKILL.md" ; do
  src="${pair%%|*}"; dst="${pair##*|}"
  diff <(strip "$src") "$dst" >/dev/null && echo "OK  $dst" || echo "NG  $dst"
done
```
- **기대**: 5행 전부 `OK`. 근거: install이 `^## 변경이력$`부터 파일 끝까지 strip한다(`scripts/install-mac.sh:219-222`, `:227-232`) → 배포본 diff는 변경이력 섹션을 제외해야 0건이 된다.
- **사전 실측 baseline**: install 실행 전 현 시점 소스 대비 5/5 `OK` 확인됨 → 이 AC는 달성 가능하며, 편집 후 `NG`가 나오면 install 미실행 또는 배포 경로 오류다.
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다." → `NG` 발생 시 배포본을 손으로 고치지 않고 install을 재실행한다.

**`docs/PROJECT.md` 갱신 문안**:
- `:202` 주석 문단 끝에 1문장 추가: "목표계열 선작성 트랙(095) — 도출 입력을 TASK 유래(①②⑤⑥)/PLAN 유래(③④) 2계열로 분리하고 TASK 유래 계열을 PLAN 워커 실행과 병렬 선작성. 게이트는 PLAN 확정 + 보강 완료 후 1회 호출. 트랙 SSOT `harness/red-first.md` §1.6 · 절차 SSOT `test-scenario-guide.md` Step 1 · 호출 시점 SSOT `harness/scenario-gate.md` §4."
- 작업 히스토리 표에 `| 2026-08-19 | TEST-SCENARIO 목표계열 선작성 트랙 신설 — … (Task 095) |` 행 추가.

#### 3.6.3 환경 변경
해당 없음 (install은 기존 스크립트 실행).

#### 3.6.4 배치/마이그레이션
`./scripts/install-mac.sh` 1회 실행. 롤백은 `git checkout -- <5파일>` 후 install 재실행.

#### 3.6.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-025 | R-6 AC (변경이력) | 산출물 검사 | 5문서 변경이력 표 각각에 KST `YYYY-MM-DD HH:mm` 일시 + `(095)` 포함 행이 1건 추가 |
| TS-026 | R-6 AC (배포본 정합) | 통합 테스트 | install 실행 후 §3.6.2 스크립트가 5행 전부 `OK` 출력 |
| TS-027 | H-g | 통합 테스트 | strip 미적용 diff는 변경이력 구간만 차이로 나오고, 그 외 구간 차이 0건 |
| TS-028 | 제약 (도구 변경 0) | 회귀 테스트 | `git diff --stat` 에 `opal/tools/**` 및 두 `references/pipeline.json` 이 0건 |
| TS-029 | 제약 (공용 스킬 미접촉) | 회귀 테스트 | `git diff --stat opal/skills/op-dev-plan/ opal/skills/op-dev-test-scenario/SKILL.md` 가 0건 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 산출 파일 수 | 비고 |
|-------|------|------|-------|------|------------|------|
| 1 | F-001, F-002, F-003 | 1, 2, 3 | `opal-task-agent` | 단일 배치 내 **순차** | **3** | 규칙 SSOT 3문서. F-001→F-002→F-003 앵커 의존이므로 병렬 불가 |
| 2 | F-004, F-005 | 4, 5 | `opal-task-agent` | 단일 배치 내 순차 (상호 독립이나 동일 배치) | **2** | pilot 배선 2문서. Phase 1의 §1.6 / Step 1 / §4 앵커 확정 후 |
| 3 | F-006 | 6 | PM 직접 | 순차 | **0** (검증만) | 제약 회귀 3건 + SSOT grep 매트릭스 (소스 기준 — install 불요) |
| 4 (TEST 단계) | F-006 | install + S-7 | PM 직접 | TEST 시나리오 17건 전건 통과 **후** | **0** | install 재배포 + 배포본 정합 검증 — **캡틴 승인 반영 순서 변경** |
| 5 (CLOSE 단계) | F-006 | PROJECT.md | PM 직접 | 순차 | **1** | `docs/PROJECT.md` 갱신 — CLOSE §2 '관련 문서 업데이트'로 이관(중복 실행 방지) |

> **[순서 변경 — 캡틴 승인 2026-08-19]** 최초 설계는 EXECUTE Step 6에서 install을 실행한 뒤 TEST 단계로 넘어가는 순서였다. `install-mac.sh`가 전역 배포본(`~/.opal/`)을 덮어써 **검증 미완 규칙이 모든 프로젝트에 즉시 활성화**되는 문제를 PM이 제기하고 캡틴이 순서 변경을 승인했다. 변경 내용: ① Step 6을 **소스 기준 검증만**(제약 회귀 3건 + SSOT grep)으로 축소하고 EXECUTE에 유지 ② install 실행 + S-7(배포본 정합)을 **TEST 시나리오 17건 전건 통과 후**로 이관 ③ `docs/PROJECT.md` 갱신을 CLOSE §2 '관련 문서 업데이트'로 이관. **`pipeline.json` 행 구조는 불변**이다(STATE 11행 유지) — 변경된 것은 EXECUTE 행 내부의 action-step 구성뿐이다.

> **산출량 상한 준수 (2배치 분할)**: 근거 [MUST] `opal/core/references/pm/dispatch-process.md` §Step 6 항목 5: "단일 디스패치가 생성·수정하는 **산출 파일이 3개를 초과하면** 파일 집합을 비중첩(non-overlapping)으로 분할하여 별도 디스패치로 배치한다." → 총 5문서를 Phase 1(3파일) / Phase 2(2파일)로 **비중첩 분할**했다. 두 배치의 파일 집합 교집합은 공집합이다.
> **동일 파일 순차 편집**: 각 문서의 본문 편집과 변경이력 행 추가는 **같은 Step 안에서** 처리한다 — 동 항목 5: "동일 파일을 2개 이상 Step이 변경하면 분할하지 않고 같은 디스패치에 묶어 순차 편집한다". 변경이력을 별도 배치로 떼면 5파일을 다시 열게 되어 상한을 위반한다.

### 4.2 실행 체크리스트

> 총 **7개 Step** | Phase **4개** | 실행 모드: **복잡** (§6 참조) | 배치 구성: Batch A(Step 1~3, 3파일) / Batch B(Step 4~5, 2파일) / Batch C(Step 6, 0파일) / PM 직접(Step 7, 1파일)

#### Step 1: `red-first.md` §1.6 목표계열 선작성 트랙 신설
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: `opal-task-agent`
- **파일**: `opal/core/references/harness/red-first.md`
- **작업 내용**: §3.1.2 명세대로 `## 1.5 적용 기준 (하이브리드 자동분기)` 절 직후 · `## 2. 작성자≠구현자` 직전에 `## 1.6 목표계열 선작성 트랙 (PLAN 병렬)` 삽입. **리드 문단(트랙 목적 = 품질, 효율 아님 — 개선 A)** + 항목 (a)~(f) 전건 작성 — (a) 입력 3종 표(원천·대응 축·근거 인용) + "3종 밖 입력 금지"·"PLAN.md 미독" 규범 문장, (b) `[MUST]` ③④축 보강 필수 + `scenario-gate.md` §2 원문 인용, (c) `[MUST]` 작성자≠PLAN 워커 + `test-scenario-guide.md` §목적 1 원문 인용, (d) RED→GREEN 순서 불변, (e) 게이트 호출 금지 구간 + §4 포인터, (f) opt-in·자연 스킵 **+ 착수 판단 기준 4행 표 + 판단 유보 시 순차 규범 + 폐기율 신호 문장(개선 D)**. 이어서 `## 변경이력` 표에 v1.1 행 추가(일시는 `node ~/.opal/tools/date/date.js datetime` 취득).
- **완료 기준**: (1) `## 1.6` 헤딩이 §1.5와 §2 사이에 1개 존재 (2) (a)(b)(c) 3항목이 모두 존재하고 각각 근거 인용 포함 (3) `## 2.`~`## 6.` 헤딩 5개 문자열이 변경 전과 문자 단위 동일 (4) 변경이력에 `(095)` 포함 v1.1 행 1건 (5) 다른 절 본문 diff 0건 (6) **리드 문단에 '효율은 목적이 아니다' 취지 문장 + 095 실측 근거 인용이 존재**(개선 A) (7) **(f)에 착수 판단 기준 표 4행 + '판단이 서지 않으면 순차' 규범 문장이 존재**(개선 D)
- **테스트**: TS-001, TS-002, TS-003, TS-004, TS-005
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: `test-scenario-guide.md` Step 1 도출 입력 2계열 재구성
- [x] 완료
- **소속 기능**: F-002
- **영역**: 가이드
- **agent**: `opal-task-agent`
- **파일**: `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
- **작업 내용**: §3.2.2 명세대로 `### Step 1:` 제목을 `### Step 1: 도출 입력 2계열 Read (Block A: TASK 유래 / Block B: PLAN 유래)`로 교체하고, 리드 문단 + 계열↔루브릭 축 매핑 표 + `#### Block A` + `#### Block B` + `#### 선작성 대상이 아닌 Step` 4블록으로 재구성. **삭제 금지 목록 (i)(ii)(iii)** 문장은 해당 Block으로 이동만 한다. Block A에 ⑥경계·부정 `[MUST]` + 선작성 시 `[MUST]` 3항목(직접 작성 / `<!-- PENDING-BLOCK-B -->` 마커 / 게이트 호출 금지), Block B에 F-NNN Read 1줄 + additive-only 금지 `[MUST]` + 보강 완료 판정 3조건 신설. **판정 조건 1(마커 잔존 0건)에는 반드시 '인라인 백틱(`` ` ``) 구간을 제거한 뒤 검사한다'는 전처리 규정을 함께 명시한다** — 마커 리터럴을 설명하는 규칙 문서·시나리오 문서 본문의 백틱 표기까지 잡히면 판정이 영구 FAIL하는 메타-순환 오탐이 발생한다(095 실측: 본 태스크 TEST-SCENARIO.md grep 2건이 전부 설명 문맥). 선례 해법: `opal/tools/state-tool/state_tool.py:2010,2025`가 034에서 동일 문제를 `re.sub(r"`[^`]*`", "", line)` 전처리로 해소했다. §작성 체크리스트에 3행 추가. `## 변경이력` 표에 v2.8 행 추가.
- **완료 기준**: (1) `### Step ` 헤딩 개수가 변경 전과 동일(Step 1~5 유지, `### Step 3-b:`·`### Step 4-a`·`### Step 4-b`·`### Step 4-c` 헤딩 문자열 불변) (2) `#### Block A`·`#### Block B`·`#### 선작성 대상이 아닌 Step` 3개 헤딩 존재 (3) 계열↔축 매핑 표에 ①②⑤⑥ / ③④ 기재 (4) 삭제 금지 목록 3문장 전건 잔존(grep) (5) 6축 **정의** 재서술 0건 — `scenario-gate.md` §2 포인터만 (6) 변경이력 v2.8 행 1건 (7) **보강 완료 판정 조건 1에 인라인 백틱 제거 전처리 규정이 명시되고 `state_tool.py:2010,2025` 선례 인용이 존재**(095 메타-순환 오탐 방어)
- **테스트**: TS-006, TS-007, TS-008, TS-009, TS-010, TS-011
- **실행 방법**: sub-agent
- **의존**: Step 1 (§1.6 앵커 확정 후 참조)

#### Step 3: `scenario-gate.md` §4 게이트 호출 시점 규율 추가
- [x] 완료
- **소속 기능**: F-003
- **영역**: 가이드
- **agent**: `opal-task-agent`
- **파일**: `opal/core/references/harness/scenario-gate.md`
- **작업 내용**: §3.3.2 명세대로 §4 루프 프로세스의 기존 `> [MUST] Producer≠Evaluator` 인용 블록 **직후**에 `[MUST] 호출 시점` 인용 블록(문단 1 규율 / 문단 2 금지 근거 / 문단 3 도구 층 정합) 추가. `## 변경이력` 표에 v1.1 행 추가.
- **완료 기준**: (1) §4에 `[MUST]` 호출 시점 문장이 존재하고 "PLAN 확정"·"보강 완료"·"1회" 3요소 포함 (2) 금지 근거에 §3 `missing` FAIL 규칙 인용 + `red-first.md` §1.6 포인터 존재 (3) 문단 3에 `state_tool.py:634`·`:1423` 인용 존재 (4) §1·§2·§3·§5·§6 구간 diff 0건 (5) 변경이력 v1.1 행 1건
- **테스트**: TS-012, TS-013, TS-015
- **실행 방법**: sub-agent
- **의존**: Step 2 (Step 1 "보강 완료 판정" 앵커 확정 후 참조)

#### Step 4: opds `SKILL.md` STEP 2 선작성 3단계 배선
- [x] 완료
- **소속 기능**: F-004
- **영역**: 오케스트레이터
- **agent**: `opal-task-agent`
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**: §3.4.2 명세대로 STEP 2에 `### TEST-SCENARIO 작성 — 목표계열 선작성 → 보강 → 게이트 (3단계)` 소절 신설. 기존 producer 인용 블록 문안을 리드로 보존하고 SSOT 포인터 3종 추가. (a)/(b)/(c) 3단계 작성, 기존 게이트 호출 서술 + verdict bullet 4종을 (c) 하위로 **문안 그대로** 재배치, `plan.scenario_gate` mark 시점 1줄 추가. RED-first 콜아웃에 §1.6 포인터 1구 추가. `## 변경이력` 표에 v4.6 행 추가.
- **완료 기준**: (1) (a)→(b)→(c) 순서 기재 (2) `plan.scenario_gate` mark 시점이 (c) `verdict: pass` 이후로 명시 (3) 규칙 본문 신설 0건 — 입력 3종 열거·6축 정의·보강 3조건 본문이 SKILL.md에 없고 포인터만 존재 (4) "문서 전용 작업 시 스킵(게이트도 자연 스킵)" 문구 잔존 (5) PM Gate 검증 체크리스트 7항목 diff 0건 (6) `references/pipeline.json` diff 0건 (7) 변경이력 v4.6 행 1건
- **테스트**: TS-016, TS-017, TS-018, TS-019
- **실행 방법**: sub-agent
- **의존**: Step 3 (SSOT 3문서 앵커 전부 확정 후)

#### Step 5: opd `SKILL.md` STEP 3 / STEP 3.5 배선
- [x] 완료
- **소속 기능**: F-005
- **영역**: 오케스트레이터
- **agent**: `opal-task-agent`
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**: §3.5.2 명세대로 (1) `## STEP 3: PLAN` `### 3-1. PLAN 디스패치` 의 `**model**: advanced` 줄 직후에 "목표계열 선작성 착수 (PLAN 병렬)" 인용 블록 신설 — **`## STEP 2: ANALYSIS` 에 넣지 않는다(H-h)**. (2) `## STEP 3.5: TEST-SCENARIO` 절차 1을 "Block B 보강"으로 재작성, 2·3 문안 유지, 4에 보강 완료 판정 3조건 확인 추가, 5에 "4의 보강 완료 이후에만 호출" 전제 + mark 시점 1줄 추가. (3) RED-first 콜아웃(STEP 3.5 상단)에 §1.6 포인터 1구 추가. (4) `## 변경이력` 표에 v5.0 행 추가.
- **완료 기준**: (1) 선작성 착수 지시가 `## STEP 3: PLAN` 하위에 존재 (2) `## STEP 2: ANALYSIS` 절 diff 0건 (3) STEP 3.5 절차 1=보강 / 5=게이트 순서 (4) `test_scenario.scenario_gate` mark 시점 명시 (5) 절차 3의 "5단계 프로세스"·"Step 3-b" 문안 불변 (6) `## STEP 4: EXECUTE` 절 diff 0건(`scenario_source`·완료 기준 포함) (7) `references/pipeline.json` diff 0건 (8) 변경이력 v5.0 행 1건
- **테스트**: TS-020, TS-021, TS-022, TS-023, TS-024
- **실행 방법**: sub-agent
- **의존**: Step 3 (Step 4와 동일 배치, 순차)

#### Step 6: 제약 회귀 검증 + SSOT grep 매트릭스 (소스 기준)
- [x] 완료
- **소속 기능**: F-006
- **영역**: 검증
- **agent**: PM 직접
- **파일**: (파일 수정 없음) 검증 대상 = 프로젝트 소스
- **작업 내용**: install에 의존하지 않는 소스 기준 검증을 수행한다. (i) `git diff --stat opal/tools/` = 0건 (ii) 두 `references/pipeline.json` diff = 0건 + `state-tool spec-validate` 10 pilot 통과 + 행 수 opd 16 · opds 11 유지 (iii) `git diff --name-only opal/skills/op-dev-plan/ opal/skills/op-dev-test-scenario/SKILL.md` = 0건 (iv) 후속 3 pilot(opsdd·oppl·oppd) diff = 0건 (v) §규칙 소유권 표 기준 SSOT 이중화 grep 매트릭스 — 각 규칙의 `정의` 문서 1곳 / `참조` 문서에 규칙 본문 0줄
- **완료 기준**: (1)~(v) 전건 통과. `~/.opal/` 직접 편집 0건
- **테스트**: TS-028, TS-029 + S-8·S-9·S-10·S-14·S-18
- **실행 방법**: direct (PM)
- **의존**: Step 4, Step 5
- **실측 결과 (2026-08-19 21:2x 수행)**: (i) 0건 / (ii) diff 0건 · spec-validate **10-10 pass** · opd 16 · opds 11 / (iii) 0건 / (iv) 0건 / (v) 정의 1곳 · 참조 본문 0줄 — **전건 통과**. 변경 파일은 소스 5개 + 태스크 폴더뿐이며 `.opal/MEMORY.json`(`last_task_number` 91→92)은 PM측 태스크 채번 부산물이다

#### Step 7 (TEST 단계 이관): install 재배포 + 배포본 정합 검증
- [x] 완료
- **소속 기능**: F-006
- **영역**: 배치
- **agent**: PM 직접
- **파일**: (파일 수정 없음) 실행 대상 `scripts/install-mac.sh` / 검증 대상 `~/.opal/` 배포본 5파일
- **선행 조건 [MUST]**: **TEST 시나리오 17건(S-7 제외) 전건 PASS 후에만 실행한다.** 검증 미완 규칙의 전역 배포를 차단하기 위한 캡틴 승인 조건이다
- **작업 내용**: `./scripts/install-mac.sh` 실행 후 §3.6.2 스크립트로 strip-후 diff 5건을 검증한다. install은 `^## 변경이력$`부터 파일 끝까지 제거하므로(`scripts/install-mac.sh:219-232`) 변경이력 구간을 비교에서 제외한다
- **완료 기준**: (1) install 종료 코드 0 (2) 5파일 전부 strip-후 diff `OK` (3) `~/.opal/` 직접 편집 0건
- **테스트**: TS-026, TS-027 + **S-7**
- **실행 방법**: direct (PM)
- **의존**: TEST 단계 시나리오 17건 전건 PASS

#### Step 8 (CLOSE 단계 이관): `docs/PROJECT.md` 갱신
- [x] 완료
- **소속 기능**: F-006
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`
- **작업 내용**: §3.6.2 문안대로 §주요 컴포넌트(TEST-SCENARIO 목표-커버 게이트) 하단 주석(`:202`)에 선작성 트랙 1문장 추가 + 작업 히스토리 표에 095 행 추가
- **완료 기준**: `:202` 주석에 선작성 트랙 서술 1문장 + 작업 히스토리 `(Task 095)` 행 1건. 그 외 diff 0건
- **실행 방법**: direct (PM)
- **의존**: Step 7 (배포본 정합 확인 후 사실 기반 서술)
- **비고**: CLOSE 단계 §2 "관련 문서 업데이트"에서 수행한다 — **중복 실행 금지**

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | Step 2가 `red-first.md` §1.6을 트랙 규칙 SSOT로 인용 — 절 번호 확정 선행 필요 |
| Step 2 → Step 3 | Step 3의 "보강 완료" 규율이 `test-scenario-guide.md` Step 1 "보강 완료 판정" 앵커를 인용 |
| Step 3 → Step 4 · Step 3 → Step 5 | pilot 배선이 §1.6 / Step 1 Block A·B / §4 세 앵커를 모두 인용 — SSOT 3문서 확정 후 |
| Step 4 ∥ Step 5 (논리적 독립, 동일 배치 순차 실행) | 서로 다른 파일이며 상호 인용 없음. 단 2파일이 산출량 상한(3) 이내이므로 배치를 더 쪼개지 않고 한 워커가 순차 편집 — `dispatch-process.md` §Step 6 항목 5 |
| Batch A ∥ Batch B **불가** | Batch B가 Batch A의 §앵커를 인용하므로 병렬 시 앵커 미확정 인용 위험 |
| Step 4, 5 → Step 6 | install은 소스 편집 전건 완료 후 1회만 실행 (중간 install은 부분 배포로 오탐 유발) |
| Step 6 → Step 7 | 배포본 정합 확인 후 프로젝트 문서 레지스트리를 갱신해야 사실 기반 서술이 가능 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | §1.6 신설 절이 R-1 AC 3항목 + 근거 인용을 모두 담는가 | TS-001, TS-002, TS-003 | (a)(b)(c) 각 항목에 `[MUST]` 또는 근거 인용 1건 이상 |
| F-001 | 기존 §2~§6 번호·헤딩 문자열 불변 (외부 인용 60건+ 보호) | TS-004 | `## 2.`~`## 6.` 헤딩 5개 문자 단위 동일 |
| F-001 | opt-in·자연 스킵 성격 명시 | TS-005 | §1.6 (f) 존재 |
| F-002 | Step 1이 Block A/B 2계열로 분리되고 축 매핑 표가 존재 | TS-006, TS-007 | 헤딩 2개 + 매핑 표 1개(①②⑤⑥ / ③④) |
| F-002 | Step 2·3 선작성 제외가 `[MUST]`로 명시 | TS-008 | 전용 소절 1개 |
| F-002 | self-confirming 퇴행 방어 2종 존재 (H-a 판정 반영) | TS-009 | ⑥축 `[MUST]` + additive-only 금지 `[MUST]` |
| F-002 | opd 공용 엔진 회귀 없음 | TS-010 | Step 1~5 번호 유지 + Step 3-b 앵커 불변 + 삭제 금지 3문장 잔존 |
| F-002 | 선작성 초안 저장 위치·마커 규정 존재 | TS-011 | 직접 작성 규정 + 마커 리터럴 정의 |
| F-003 | 호출 시점 `[MUST]` + 금지 근거가 §4에 존재 | TS-012, TS-013 | 3요소(PLAN 확정/보강 완료/1회) + F/H 결정론 근거 |
| F-003 | 도구 층 조기 호출 차단 실증 | TS-014 | `stage_transition_violation` 반환 |
| F-003 | §2·§3·§5·§6 무변경 (외부 인용 보호) | TS-015 | 해당 구간 diff 0건 |
| F-004 | opds STEP 2에 (a)(b)(c) 3단계 + mark 시점 명시 | TS-016, TS-017 | 순서 기재 + mark 시점 문장 |
| F-004 | 규칙 본문 재서술 0건 (SSOT 이중화 방지) | TS-018 | 포인터만 존재 |
| F-004 | 자연 스킵 경로·PM Gate·pipeline.json 무변경 | TS-019 | 3건 전부 확인 |
| F-005 | 선작성 착수가 STEP 3(PLAN)에 배선 (H-h 정정) | TS-020, TS-023 | STEP 3 하위 존재 + STEP 2 diff 0건 |
| F-005 | STEP 3.5 보강→게이트 순서 + mark 시점 명시 | TS-021, TS-022 | 절차 1/5 순서 + mark 시점 문장 |
| F-005 | EXECUTE 완료기준 경로 무변경 | TS-023, TS-024 | STEP 4 diff 0건 + "5단계"·"Step 3-b" 문안 불변 |
| F-006 | 5문서 변경이력 095 행 + KST 일시 | TS-025 | 5건 |
| F-006 | 배포본-소스 정합 (strip 후 diff 0) | TS-026, TS-027 | 5파일 `OK` |
| F-006 | 제약 회귀 — 도구·pipeline.json·공용 스킬 미접촉 | TS-028, TS-029 | 3건 전부 0건 |

### 5.2 회귀 테스트

- [ ] `red-first.md` §2/§3/§4/§5를 인용하는 8개 도구 테스트 스위트(`opal/tools/{test-tool,memory-tool,state-tool,brain-tool,improve-tool,tool-scan,backlog-tool,code-scan,opal-agent}/tests/*`)의 인용 지시 내용이 여전히 유효한가 (절 번호·내용 불변 확인)
- [ ] `coding-principles.md:53`, `opal-test-agent/AGENT.md:91`, `op-dev-test-scenario/SKILL.md:60`, `op-dev-execute/SKILL.md:115` 의 `red-first.md` 인용이 유효한가
- [ ] `op-scenario-gate/SKILL.md:15,27,121,124,128,151-154` 의 `scenario-gate.md` §2·§3·§4·§5·§6 인용이 유효한가
- [ ] `opal-evaluator-agent/AGENT.md:69,186` 의 `scenario-gate.md` §2·§5 인용이 유효한가
- [ ] `op-dev-test-scenario/SKILL.md:166,192` 의 `test-scenario-guide.md` §Step 3-b 인용이 유효한가
- [ ] `opal-pilot-dev/SKILL.md` STEP 3.5 절차 3의 "5단계 프로세스" 서술이 재구성 후에도 사실인가 (Step 1~5 유지)
- [ ] `scenario-gate.md:12` 의 `test-scenario-guide.md:11-14` 줄번호 인용이 여전히 §목적을 가리키는가 (Step 1 편집은 11-14 이후 구간만 이동)
- [ ] opsdd(`opal-pilot-sdd/SKILL.md:170`, `verify-guide.md:143-145`)가 `scenario-gate.md`를 SSOT로 참조 — §4 신규 규율이 opsdd 배선 변경 없이 상속되며 기존 REVIEW 절차를 깨지 않는가 (본 태스크 범위 밖이므로 **문서 정합 확인만**, 수정 금지)
- [ ] 기존 순차 경로(선작성 미착수) 실행 시 산출 결과가 변경 전과 동등한가 (opt-in 검증)

### 5.3 코드/문서 품질

- [ ] SSOT 이중화 grep 매트릭스 — §규칙 소유권 표의 RULE-A1~C2 각 행에 대해 `정의` 문서 1곳 / `참조` 문서에 규칙 본문 0줄
- [ ] 5문서 전부 `## 변경이력` 표에 KST `YYYY-MM-DD HH:mm` + semver + `(095)` 형식 준수 — [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무
- [ ] `~/.opal/` 직접 편집 0건 — [MUST] `docs/CONVENTIONS.md` §배포 경계
- [ ] pilot SKILL.md에 PM Gate 산출물·체크리스트 표 중복 게재 0건 — [MUST] `docs/CONVENTIONS.md` §State 관리
- [ ] 문서 본문 한국어 + 기술 용어 영어 병기 — `docs/CONVENTIONS.md` §언어 규칙
- [ ] 신설·수정 문단에 근거 인용(`경로 §N` / `경로:줄번호`) 존재 — [MUST] `opal/core/references/harness/citation-rules.md` §0
- [ ] 범위 밖 파일 수정 0건 — [MUST] `opal/core/PRINCIPLES.md` §3: "Touch only what the plan names. Don't improve adjacent code."
- [ ] `docs/PROJECT.md` 갱신이 Step 7에서 1회만 수행되고 CLOSE §2에서 중복되지 않음

### 5.4 보안

- [ ] 5문서 신설 문단에 토큰·시크릿·개인 식별자 하드코딩 0건 (grep: `sk-`, `ghp_`, `token`, 이메일 패턴)
- [ ] 절대 경로 노출은 `~/.opal/` 형태의 홈 상대 표기만 사용 — 사용자명이 박힌 절대 경로(`/Users/<name>/`) 문서 기재 0건
- [ ] `install-mac.sh` 실행이 `~/.opal/` 외부 경로에 쓰기를 수행하지 않음 (실행 로그 확인)
- [ ] 문서 내 개인 식별자 표기는 배포본 정체성 규약 준수 — 배포 대상 문서에서는 "소유자"/"사용자" 표기 유지(opds v3.6 선례). 단 기존 문안에 이미 "캡틴"이 있는 문장은 문안 보존 원칙상 손대지 않는다
- [ ] `.gitignore` 변경 0건 / 신규 자격증명 파일 생성 0건

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 7개 | 복잡 (6개 이상) |
| 변경 파일 수 | 6개 (SSOT 3 + pilot 2 + `docs/PROJECT.md` 1) | 복잡 (4개 이상) |
| 모듈 범위 | 다중 (`opal/core/references/harness/` + `opal/skills/` 2종 + `docs/`) | 복잡 |
| 작업 유형 | 대규모 개선 (규칙 신설 + 2 pilot 배선) | 복잡 |
| 외부 의존성 | 없음 (신규 API·패키지·도구 0) | 단순 |
| **실행 모드** | **복잡** | §7 실행 아키텍처 포함 |

### 6.1 규모 판정 — opds 유지 vs opd 에스컬레이션

`opal-pilot-dev-short/SKILL.md` §에스컬레이션 규칙 "PLAN 결과 에스컬레이션" 3기준으로 판정한다:

| 조건 | 실측값 | 판정 |
|------|--------|------|
| 예상 변경 파일 >= 10개 | **6개** (`red-first.md`, `test-scenario-guide.md`, `scenario-gate.md`, opds `SKILL.md`, opd `SKILL.md`, `docs/PROJECT.md`) | 미해당 |
| 다단계 기술 의사결정 (아키텍처 선택·기술 스택 비교) | **없음.** 유일한 설계 판단은 "규칙을 어느 문서가 소유하는가"이며, 이는 §규칙 소유권 표로 1회 확정된 문서 배치 결정이다. 아키텍처 선택지 비교나 신규 기술 도입 0건, 신규 컴포넌트 0건, 도구·스키마 변경 0건 | 미해당 |
| 다중 모듈 연쇄 영향 (3개 이상 독립 모듈에 연쇄) | **2개 모듈**(`harness/` 참조 문서 · pilot 스킬 2종). `docs/`는 레지스트리 반영이라 연쇄가 아니다. opsdd는 SSOT 상속으로 규율만 전파되며 배선 변경 0건이므로 연쇄 대상이 아니다 | 미해당 |

**판정: opds(Short Task) 유지.** 3기준 모두 미해당이다. Step 수 7개는 `plan-guide.md` §4.2 "Short Task: 5개 이하 Step 권장"을 2개 초과하지만, (i) 초과분은 `dispatch-process.md` §Step 6 산출량 상한을 준수하려는 **배치 분할의 결과**이며 작업 자체의 복잡도 증가가 아니다 (ii) Step 6은 파일 편집 0건의 검증 Step, Step 7은 PM 직접 1파일이라 실질 편집 Step은 5개다 (iii) Step 수는 §6 실행 모드(복잡)를 결정하는 축이지 pilot 에스컬레이션 축이 아니다. 따라서 opds에서 복잡 모드로 진행한다.

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch A (opal-task-agent)            Batch B (opal-task-agent)         Batch C (opal-task-agent)      PM 직접
┌───────────────────────────┐        ┌──────────────────────┐          ┌───────────────────┐        ┌──────────────┐
│ Step 1 red-first.md       │        │ Step 4 opds SKILL.md │          │ Step 6 install    │        │ Step 7       │
│   ↓ (§1.6 앵커)           │  ───▶  │   ↓                  │  ───▶    │   + 정합 검증     │  ───▶  │ PROJECT.md   │
│ Step 2 test-scenario-guide│        │ Step 5 opd SKILL.md  │          │   + 제약 회귀     │        │              │
│   ↓ (Step 1 앵커)         │        │                      │          │   + SSOT grep     │        │              │
│ Step 3 scenario-gate.md   │        │ 산출 2파일           │          │ 산출 0파일        │        │ 산출 1파일   │
│ 산출 3파일                │        └──────────────────────┘          └───────────────────┘        └──────────────┘
└───────────────────────────┘
```

**그룹핑 근거**:
1. **파일 충돌 방지**: 각 파일은 정확히 1개 Step만 수정한다(변경이력 행 추가를 해당 Step에 병합). 동일 파일을 2개 Step이 건드리는 구성은 없다.
2. **모듈 응집도**: Batch A = 규칙 SSOT 계층(`harness/` 2 + 도출 엔진 1) / Batch B = 오케스트레이터 계층.
3. **산출량 상한**: Batch A 3파일(상한 3 이내) / Batch B 2파일 — 비중첩 분할. 5파일 단일 디스패치는 상한 위반이므로 금지.
4. **병렬 불가 근거**: Batch B가 Batch A의 §앵커를 인용하므로 순차. Batch A 내부도 앵커 체인(§1.6 → Step 1 → §4)으로 순차.

**배치 실행 순서**: Batch A → Batch B → Batch C → PM 직접 (전 구간 순차, 병렬 0)

### C-2. 스킬 요구사항

| 필요 역량 | 매칭 스킬 | 갭 |
|----------|----------|-----|
| PLAN 체크리스트 기반 구현 | `op-dev-execute` (탐색: `{프로젝트}/.opal/skills/` → `~/.opal/skills/`) | 없음 |
| Markdown SSOT 문서 부분 편집 | 범용 — `opal-task-agent` + `op-dev-execute` 제너럴리스트 가이드 | 없음 (전용 스킬 신설 불필요 — 동일 패턴 Step이 2~5개이나 인라인 지침으로 충분, `plan-guide.md` §C-2 "1~2개 → 인라인 지침" 준용은 경계선이지만 신규 스킬 도입은 PRINCIPLES §2 "No abstractions for single-use code" 위반) |
| 배포 검증 | 없음 — Bash 인라인 스크립트(§3.6.2) | 없음 |

**전 Step 공통 인라인 지침 (디스패치 프롬프트에 주입)**:
- [MUST] 대상 파일 전체 통독 금지 — grep으로 위치 특정 후 해당 구간만 Read하고 Edit로 부분 편집
- [MUST] 증분 저장 — 산출물 1개 완결 저장 후 다음으로 이동, 말미 일괄 저장 금지
- [MUST] 기존 §번호·헤딩 문자열 불변 (외부 인용 보호)
- [MUST] 규칙 본문은 §규칙 소유권 표의 `정의` 문서에만 작성, `참조` 문서에는 포인터만

### C-3. 도구 요구사항

| 도구 | 용도 | 비고 |
|------|------|------|
| `node ~/.opal/tools/date/date.js datetime` | 변경이력 KST 일시 취득 | 추측 금지 — 필수 호출 |
| `./scripts/install-mac.sh` | `~/.opal/` 재배포 | Step 6, 1회 |
| `git diff --stat` | 제약 회귀 검증 (도구·pipeline.json·공용 스킬 미접촉) | Step 6 |
| `grep` / `diff` / `awk` | 산출물 검사·strip 후 정합 검증 | Step 6 |
| `~/.opal/tools/state-tool/run.sh` | STATE 행 mark (PM) / TS-014 조기 advance 거부 실증 | 도구 코드 **미변경** |

**신규 설치·설정 0건.** MCP 사용 0건.

### C-4. 테스트 전략

| 계층 | 대상 | 실행 명령 / 방법 | 기대 |
|------|------|----------------|------|
| L1 (산출물 검사, M1) | TS-001~013, TS-016~022, TS-025 | `grep -n` 기반 존재·순서·형식 검사 | 전건 PASS |
| L1 (회귀 grep, M1) | TS-004, TS-010, TS-015, TS-019, TS-023, TS-024, TS-028, TS-029 | `git diff` 구간 검사 + 헤딩 문자열 비교 + `git diff --stat` | diff 0건 |
| L2 (배포 정합, M1) | TS-026, TS-027 | §3.6.2 install + strip-diff 루프 | 5행 `OK` |
| L2 (도구 집행 실증, M1) | TS-014 | 임시 태스크 폴더에서 `state-tool init` 후 `plan.plan_md` 미완 상태로 `advance --task-step plan.scenario_gate` 호출 | `stage_transition_violation` |
| 회귀 스위트 | 도구 무변경 확인 | 본 태스크는 Python 도구를 수정하지 않으므로 도구 테스트 스위트 실행은 **선택** — `git diff --stat opal/tools/` 0건으로 대체 가능 | 0건 |
| M2 (E2E) | **면제** | 변경 영역이 FE 화면/인증·인가/외부 API 연동 중 어느 것도 아니고 API 엔드포인트 변경도 없다 — `test-scenario-guide.md` §Step 3-b "M2 의무 트리거" 및 "BE API M2 트리거" 미해당 | — |
| M3 (사용자 협업) | **없음** | 자동화 불가 항목 0건. `[SUPERVISOR]` 시나리오 미발생 | — |

> RED-first 트랙 판정: 본 태스크는 **Markdown 규칙 문서·오케스트레이터 배선 변경**이므로 `red-first.md` §1.5 "구현 후 시나리오 검증 허용(설정·문서)" 트랙에 해당한다. 비즈니스 로직·DB 스키마·API 계약·인증/인가·버그 수정 5종 중 어느 것도 포함하지 않는다. 단 TS-014(도구 집행 실증)는 도구 동작 관찰이므로 실행 시 실 호출로 검증한다. 최종 트랙 판정 주체는 PM(TEST-SCENARIO 작성 시점)이다 — `red-first.md` §1.5.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| SSOT 규칙 문서 | Markdown (하네스 참조 문서 / 스킬 references) | `op-dev-execute` (제너럴리스트 가이드) |
| 오케스트레이터 | Markdown SKILL.md (YAML frontmatter + 프로세스) | `op-dev-execute` |
| 배포 | Bash (`scripts/install-mac.sh`) | 인라인 Bash |
| 검증 | grep / diff / awk / `state-tool` CLI | 인라인 Bash |
| 참조 전용 (미변경) | Python 3 (`state-tool`·`test-tool`) | — |

> FE/BE/DB 영역 해당 없음 — React·Next.js·shadcn·Python 스택 스킬(`vercel-labs/*`, `trailofbits/modern-python`, `ui-designer`) 및 context7·shadcn MCP는 본 태스크에 적용 대상이 없어 Read하지 않았다. 근거: `op-dev-plan/SKILL.md` §Step 2 "기술 스택에 따라 **선택적** Read".

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 외부 라이브러리·컴포넌트 조회 불필요 (프로젝트 내부 Markdown SSOT 편집 작업) |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL 헌법 | `opal/core/PRINCIPLES.md` | §1 완료기준 사전 잠금 / §3 수술적 변경 / §4 RED-first 원칙 SSOT |
| D-2 | 설계 | RED-first 트랙 규칙 | `opal/core/references/harness/red-first.md` | R-1 수정 대상 — §1 순서 / §1.5 하이브리드 분기 / §2~§6 인용 보호 |
| D-3 | 설계 | 목표-커버 게이트 규칙 | `opal/core/references/harness/scenario-gate.md` | R-3 수정 대상 — §1 070 근본원인 / §2 6축·판정주체 / §3 정규화 계약(계열 경계 근거) / §4 루프 / §5 종료조건 / §6 tool-gated |
| D-4 | 설계 | TEST-SCENARIO 작성 가이드 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | R-2 수정 대상 — §목적 3역할(RULE-A4 SSOT) / Step 1(2계열 원천) / Step 2·3(선작성 제외 근거) / Step 3-b(앵커 보호) |
| D-5 | 설계 | Short Task 오케스트레이터 | `opal/skills/opal-pilot-dev-short/SKILL.md` | R-4 수정 대상 — STEP 2 producer 확립·게이트 배선·PM Gate·자연 스킵 |
| D-6 | 설계 | Full Task 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | R-5 수정 대상 — STEP 2=ANALYSIS / STEP 3=PLAN(H-h 정정 근거) / STEP 3.5 / STEP 4 `scenario_source` 완료기준 의존 |
| D-7 | 소스 | state-tool | `opal/tools/state-tool/state_tool.py:634`, `:1415-1430` | `check_stage_transition_guard` scope full/prior_stage_only, advance `force=False` — 조기 게이트 호출 도구 차단 근거 (수정 대상 아님) |
| D-8 | 설계 | opds 파이프라인 SSOT | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | 11 task-step, `plan.scenario_gate`=id 4, `plan.pm_gate` gate.artifacts에 TEST-SCENARIO.md 포함 (미변경 정합 확인) |
| D-9 | 설계 | opd 파이프라인 SSOT | `opal/skills/opal-pilot-dev/references/pipeline.json` | 16 task-step, `test_scenario.scenario_gate`=id 10, `plan.pm_gate` artifacts에 TEST-SCENARIO.md 미포함 (미변경 정합 확인) |
| D-10 | 설계 | 게이트 루프 배선 스킬 | `opal/skills/op-scenario-gate/SKILL.md` | Step 2 pilot 변환기(opd/opds `features`←PLAN.md F-ID / `hypotheses`←PLAN.md H-N) — 선작성 시점 F/H 미확정 근거 |
| D-11 | 설계 | 코드 컨벤션 | `docs/CONVENTIONS.md` | 변경이력 작성 의무 / 배포 경계 / State 관리(PM Gate SSOT) / Citation Rules / 언어 규칙 |
| D-12 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | §0 근거 제시 원칙 / §2 포맷 4종 / §2.4 [MUST] / §4 PLAN 단계 의무 수준 |
| D-13 | 설계 | 디스패치 프로세스 | `opal/core/references/pm/dispatch-process.md:157-159` | §Step 6 항목 5 산출량 상한 3파일 — 배치 분할 근거 |
| D-14 | 설계 | 하네스 공통 인프라 | `opal/core/references/opal-harness.md:101-113`, `:56` | §2 하네스 모듈 테이블(red-first 등록됨) / §1 자동 루핑 제약 "시나리오 목표-커버 게이트 MAX 3회" |
| D-15 | 소스 | install 스크립트 | `scripts/install-mac.sh:219-232`, `:1071`, `:1571` | `strip_deploy_md`/`strip_deploy_md_recursive` awk 변경이력 strip — 배포본 정합 검증 설계 근거 |
| D-16 | 기획 | brain — opds producer 확립 | `.opal/brain/pages/concept/opds-testscenario-producer-establishment.md` | **공용 스킬 미접촉 원칙** — `op-dev-plan/SKILL.md` 수정 금지 근거 |
| D-17 | 기획 | brain — 070 관점 편향 교훈 | `.opal/brain/pages/concept/070-derivation-engine-perspective-bias-lesson.md` | 도출 엔진 관점 편향 근본원인 / 결정론 커버리지만으로는 편향 미검출 |
| D-18 | 기획 | brain — 시나리오 파이프라인 재설계 | `.opal/brain/pages/concept/test-scenario-pipeline-redesign.md` | task:004 — PLAN 워커의 AC 중심 self-confirming 구조(H-a 판정 근거) |
| D-19 | 기획 | 태스크 요구사항 | `tasks/095-260819-opds-시나리오-목표계열-선작성/TASK.md` | R-1~R-6 AC / D-1~D-8 확정 설계 방향 / 제약 조건 / 명확화 결과 4요소 |
| D-20 | 설계 | 프로젝트 개요 | `docs/PROJECT.md:191-202`, `:240-242` | §주요 컴포넌트(목표-커버 게이트) 레지스트리 — Step 7 갱신 대상 |
| D-21 | 설계 | 아키텍처 | `docs/ARCHITECTURE.md:107-108`, `:136` | pilot 파이프라인 단계 서술 — 단계 시퀀스 무변경이라 갱신 대상 아님을 판정한 근거 |
| D-22 | 설계 | 통일 형식 SSOT | `opal/skills/op-dev-test-scenario/SKILL.md:17`, `:64-136`, `:166-192` | TEST-SCENARIO.md 7섹션 통일 형식 / `> 상태:` enum — 6번째 파일 확산 차단 판단 근거 (미접촉) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | self-confirming 퇴행 — 선작성 구간의 입력이 AC 중심이라 task:004 실패모드로 회귀 | F-002 | P0 | 방어 3종 규칙화: ⑥경계·부정 동시 도출 `[MUST]` / 보강 additive-only 금지 `[MUST]` / 게이트 최종 방어선 유지. 판정 상세는 §리스크 가설 표 H-a |
| R-2 | 공용 도출 엔진 회귀 (opd) | F-002 | P0 | Step 번호 체계 불변 + 삭제 금지 목록 3문장 명시 + opt-in(순차 경로 동등) 규정 + TS-010 회귀 grep |
| R-3 | `red-first.md` §번호 이동으로 외부 인용 60건+ 파손 | F-001 | P0 | 신설 절을 §1.6으로 고정(§1.5 직후 삽입), §2~§6 헤딩 문자 단위 불변, TS-004 회귀 검사 |
| R-4 | opd 절 번호 오배선 (TASK.md의 "STEP 2(PLAN)" 오기) | F-005 | P0 | §3.5.1 `[MUST] 위치 정정` 명시 + STEP 2 diff 0건 완료 기준 + TS-023. PM 보고 필수 |
| R-5 | SSOT 이중화 (5문서 규칙 중복) | F-001~F-005 | P1 | §규칙 소유권 표를 집행 기준으로 삼고 Step 6에서 grep 매트릭스 대조 |
| R-6 | 선작성 초안 유실·태스크 폴더 오염 | F-002, F-004, F-005 | P1 | 초안을 TEST-SCENARIO.md 본문에 직접 작성(임시 파일 금지) + `<!-- PENDING-BLOCK-B -->` 마커 + 보강 완료 판정 3조건 |
| R-7 | 게이트 조기 호출로 반복 상한 소모 | F-003 | P1 | §4 `[MUST]` 호출 시점 규율 + pilot 배선 (a)에 호출 금지 명시 + state-tool guard 정합 서술(TS-014 실증) |
| R-8 | 배포본-소스 불일치 오탐/미탐 | F-006 | P1 | strip-후 diff 검증 스크립트 확정 + install 전 baseline 5/5 `OK` 사전 실측으로 AC 달성 가능성 확인 |
| R-9 | 문서 전용 작업 자연 스킵 경로 파손 | F-002, F-004 | P1 | §1.6 (f) opt-in 명시 + opds "문서 전용 작업 시 스킵" 문구 잔존 검증(TS-019) |
| R-10 | 범위 확산 — 6번째 파일(`op-dev-test-scenario/SKILL.md`) 또는 `pipeline.json` 접촉 유혹 | F-002, F-004, F-005 | P1 | §규칙 소유권 표 미접촉 확정 2건 명시 + 초안 표기를 HTML 주석 마커로 해결 + TS-028·TS-029 회귀 검증 |
| R-11 | opsdd 간접 영향 — `scenario-gate.md` §4 신규 규율이 opsdd에도 상속되나 opsdd 배선은 미변경 | F-003 | P2 | 상속은 의도된 효과(규율만 전파, 배선 무변경). §5.2 회귀 항목으로 정합 확인만 수행하고 **수정하지 않는다**(TASK.md §범위 "후속 분리") |
| R-12 | `opal-harness.md` §2 하네스 모듈 테이블에 `scenario-gate.md` 행이 **미등록**(실측: `red-first.md`만 등록, `:111`) | — | P2 | **본 태스크 범위 밖 선재 결함.** PRINCIPLES §3에 따라 손대지 않고 PM에 보고 → 별도 태스크 처리 |
| R-13 | 용어 일관성 — 배포 문서의 인물 표기가 "캡틴"(내부)과 "소유자/사용자"(배포 규약, opds v3.6)로 혼재 | F-004, F-005 | P2 | 신설 문단은 "알투(PM) + 캡틴 페어"를 기존 문안(opds `:55`, opd STEP 3.5)과 동일하게 사용해 국소 일관성을 유지한다. 전면 치환은 범위 밖 — `citation-rules.md` §7.2 "다름의 발견" 리스크로 기재 후 PM 보고 |
