# PLAN: 오케스트레이터 게이트 점검 -- TASK.md 체크박스 갱신 + 누락 게이트 보완

> 작성일: 2026-04-02
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/opal-harness-interactive.md` | interactive 모드 서브 하네스 (단계 게이트, QA Gate, PM Gate, 체크리스트 검증 게이트) | O1: TASK.md 체크박스 갱신 원칙 추가 |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd Full Task 오케스트레이터 | O2: PLAN PM Gate에 TASK.md 갱신 명시 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds Short Task 오케스트레이터 | O2: PLAN PM Gate에 TASK.md 갱신 명시 |
| `opal/skills/opal-pilot-project/SKILL.md` | opp 범용 오케스트레이터 | O2: PLAN PM Gate에 TASK.md 갱신 명시 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw Wireframe UI 오케스트레이터 | O3: 서브 하네스 [MUST] + PM Gate 추가 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt 기획 산출물 오케스트레이터 | O4: ANALYSIS/PLAN/EXECUTE 게이트 보완 |

### 현재 상태

#### opal-harness-interactive.md (61줄)
- 4개 섹션: 단계 게이트(SS1), QA Gate(SS2), PM Gate(SS3), 체크리스트 검증 게이트(SS4)
- TASK.md 체크박스 갱신에 대한 언급이 전혀 없음
- PM Gate(SS3)는 `.opal/AGENT.md` 기반 검토만 서술

#### opd SKILL.md (v1.8)
- STEP 3 (PLAN+TEST-SCENARIO): PLAN 워커 완료 -> QA Gate (op-dev-qa) -> PM Gate 순서
- PM Gate에서 TASK.md 체크박스 갱신 언급 없음
- 디스패치 프롬프트는 서술형 (코드블록 내 텍스트)

#### opds SKILL.md (v1.8)
- STEP 2 (PLAN+TEST-SCENARIO): PLAN 워커 완료 -> QA Gate (op-dev-qa) -> PM Gate 순서
- PM Gate에서 TASK.md 체크박스 갱신 언급 없음
- `[PM 컨텍스트 주입]` 블록 방식

#### opp SKILL.md (v1.6)
- STEP 2 (PLAN): 워커 완료 -> QA Gate (op-task-qa) -> PM Gate -> 사용자 보고 순서
- PM Gate에서 TASK.md 체크박스 갱신 언급 없음
- `[PM 컨텍스트 주입]` 블록 방식

#### opdw SKILL.md (v1.4)
- Harness 섹션: `opal-harness.md` Read 지시만 있고, **서브 하네스 로딩 `[MUST]` 지시가 없음** (opd/opds/opp에는 있음)
- STEP 2 (WIREFRAME): QA Gate (op-dev-qa) 있으나 PM Gate 없음 (44줄: "완료 -> op-dev-qa 호출 -> 사용자 보고")
- STEP 3 (EXECUTE): QA Gate (op-dev-qa) 있으나 PM Gate 없음 (62-63줄: "op-dev-qa 호출 -> DONE.md 생성 -> 사용자 완료 보고")

#### opwt SKILL.md (v2.1)
- 서브 하네스 `[MUST]` 지시 **있음** (18-20줄)
- ANALYSIS 단계: 워커 분석 결과 취합 후 STATE 갱신만 서술, **사용자 확인 / PM 자율 승인 게이트 없음**
- PLAN 단계: "게이트: PLAN.md + 배치 계획 사용자 확인 (interactive) / PM 자율 승인 (agentic)" 서술 있으나, **QA Gate(op-task-qa) 호출이 없음**
- EXECUTE 단계: 배치별 "PM 검토 -> 사용자 확인" 있으나, **QA Gate(op-task-qa) 호출이 없음**
- QA 단계: 자체 `references/consistency-rules.md` 기반 QA 워커. 이 단계는 문서 정합성 특화이므로 유지. 단, PLAN/EXECUTE 단계에 하네스 표준 QA Gate 추가가 별도로 필요

### 영향 범위

- 하네스 변경(O1)은 모든 interactive 오케스트레이터에 공통 적용되는 원칙이므로, 각 스킬이 이 원칙을 참조하게 됨
- O2(opd/opds/opp)는 각 스킬의 PLAN PM Gate 서술에 한 줄 추가 수준
- O3(opdw)는 구조적 보완 -- 서브 하네스 로딩 누락 + PM Gate 2개 추가
- O4(opwt)는 단계별 게이트 보완 -- ANALYSIS 게이트 + PLAN QA Gate + EXECUTE 배치별 QA Gate 추가

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

없음.

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/references/opal-harness-interactive.md` | SS3 PM Gate 하위에 "TASK.md 체크박스 갱신" 항목 추가 + 변경이력 |
| 2 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 3 PM Gate 서술에 TASK.md 갱신 단계 추가 + 변경이력 |
| 3 | `opal/skills/opal-pilot-dev-short/SKILL.md` | STEP 2 PM Gate 서술에 TASK.md 갱신 단계 추가 + 변경이력 |
| 4 | `opal/skills/opal-pilot-project/SKILL.md` | STEP 2 PM Gate 서술에 TASK.md 갱신 단계 추가 + 변경이력 |
| 5 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 서브 하네스 [MUST] 추가 + WIREFRAME/EXECUTE PM Gate 추가 + 변경이력 |
| 6 | `opal/skills/opal-pilot-write-tech/SKILL.md` | ANALYSIS 게이트 + PLAN QA Gate + EXECUTE 배치별 QA Gate 추가 + 변경이력 |

#### 삭제

없음.

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 하네스에 TASK.md 체크박스 갱신 원칙 추가 (O1) | opal-harness-interactive.md | 낮음 |
| 2 | opd PLAN PM Gate에 TASK.md 갱신 명시 (O2) | opal-pilot-dev/SKILL.md | 낮음 |
| 3 | opds PLAN PM Gate에 TASK.md 갱신 명시 (O2) | opal-pilot-dev-short/SKILL.md | 낮음 |
| 4 | opp PLAN PM Gate에 TASK.md 갱신 명시 (O2) | opal-pilot-project/SKILL.md | 낮음 |
| 5 | opdw 서브 하네스 + PM Gate 보완 (O3) | opal-pilot-dev-wireframe/SKILL.md | 중간 |
| 6 | opwt 단계별 게이트 보완 (O4) | opal-pilot-write-tech/SKILL.md | 중간 |

의존성: Step 1 완료 후 Step 2-6 (Step 1의 원칙을 스킬에서 참조). Step 2-6은 상호 독립.

### 핵심 설계

#### Step 1: opal-harness-interactive.md -- TASK.md 체크박스 갱신 원칙

**위치**: §3 PM Gate 하위에 새 하위 섹션 추가 (§3과 §4 사이, 또는 §3 본문 확장)

**추가 내용** (§3 PM Gate 본문 뒤에 삽입):

```markdown
### TASK.md 체크박스 갱신 (PLAN PM Gate 시)

PLAN 단계 PM Gate에서 다음을 수행한다:

1. TASK.md 요구사항 체크박스와 PLAN.md 실행 체크리스트를 대조한다
2. PLAN.md가 커버하는 요구사항 항목을 TASK.md에서 `[x]`로 갱신한다
3. 커버되지 않는 항목이 있으면 PLAN 재지시 또는 사유를 기록한다

이 갱신은 모든 오케스트레이터의 PLAN PM Gate에서 공통 적용한다.
```

**변경이력 추가**: `v1.1 | 2026-04-02 | §3 PM Gate에 TASK.md 체크박스 갱신 원칙 추가 (072)`

#### Step 2: opd SKILL.md -- PLAN PM Gate에 TASK.md 갱신 명시

**위치**: STEP 3 (PLAN+TEST-SCENARIO) 섹션, 57줄 `워커 완료 → **QA Gate** (op-dev-qa) → **PM Gate**.` 뒤

**추가 내용**: 기존 `→ **PM Gate**.` 를 확장하여 TASK.md 갱신 책임을 명시. opd는 서술형이므로:

```
워커 완료 → **QA Gate** (op-dev-qa) → **PM Gate** (TASK.md 요구사항 체크박스 갱신 포함 — 하네스 §3 참조).
```

**변경이력 추가**: `v1.9 | 2026-04-02 | PLAN PM Gate에 TASK.md 체크박스 갱신 명시 (072)`

#### Step 3: opds SKILL.md -- PLAN PM Gate에 TASK.md 갱신 명시

**위치**: STEP 2 (PLAN+TEST-SCENARIO) 섹션, 37줄 `워커 완료 -> **QA Gate** (op-dev-qa) -> **PM Gate**.`

**추가 내용**: `[PM 컨텍스트 주입]` 블록 방식에 맞춰:

```
워커 완료 -> **QA Gate** (op-dev-qa) -> **PM Gate** (TASK.md 요구사항 체크박스 갱신 포함 — 하네스 §3 참조).
```

**변경이력 추가**: `v1.9 | 2026-04-02 | PLAN PM Gate에 TASK.md 체크박스 갱신 명시 (072)`

#### Step 4: opp SKILL.md -- PLAN PM Gate에 TASK.md 갱신 명시

**위치**: STEP 2 (PLAN) 섹션, 40줄 `워커 완료 -> **QA Gate** (op-task-qa) -> **PM Gate** -> 사용자에게 보고.`

**추가 내용**:

```
워커 완료 -> **QA Gate** (op-task-qa) -> **PM Gate** (TASK.md 요구사항 체크박스 갱신 포함 — 하네스 §3 참조) -> 사용자에게 보고.
```

**변경이력 추가**: `v1.7 | 2026-04-02 | PLAN PM Gate에 TASK.md 체크박스 갱신 명시 (072)`

#### Step 5: opdw SKILL.md -- 서브 하네스 [MUST] + PM Gate 추가

**5-a. 서브 하네스 로딩 [MUST] 추가**

**위치**: Harness 섹션 (12-13줄), 기존 내용:
```
모드: Wireframe UI (TASK → WIREFRAME → EXECUTE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.
```

**변경 후**: `opal-harness.md` Read 지시 뒤에 서브 하네스 [MUST] 블록 추가:
```
모드: Wireframe UI (TASK → WIREFRAME → EXECUTE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다
```

**5-b. WIREFRAME 단계 PM Gate 추가**

**위치**: STEP 2 (WIREFRAME) 섹션, 44줄 `완료 → op-dev-qa 호출 (단계: WIREFRAME) → 사용자 보고`

**변경 후**:
```
완료 → op-dev-qa 호출 (단계: WIREFRAME) → **PM Gate** (TASK.md 요구사항 체크박스 갱신 포함 — 하네스 §3 참조) → 사용자 보고
```

**5-c. EXECUTE 단계 PM Gate 추가**

**위치**: STEP 3 (EXECUTE) 완료 후 섹션 (62-63줄), 기존:
```
1. op-dev-qa 호출 (단계: EXECUTE-UI) → 빌드/린트 + wireframe↔코드 대조
2. DONE.md 생성 → 사용자 완료 보고
```

**변경 후**:
```
1. op-dev-qa 호출 (단계: EXECUTE-UI) → 빌드/린트 + wireframe↔코드 대조
2. **PM Gate** — QA 결과 + 실행 결과 검토 + 체크리스트 갱신 (하네스 §2, §3 참조)
3. DONE.md 생성 → 사용자 완료 보고
```

**변경이력 추가**: `v1.5 | 2026-04-02 | 서브 하네스 [MUST] 추가 + WIREFRAME/EXECUTE PM Gate 추가 (072)`

#### Step 6: opwt SKILL.md -- 단계별 게이트 보완

**6-a. ANALYSIS 단계 완료 후 게이트 추가**

**위치**: ANALYSIS 단계 섹션, STATE 갱신(97-98줄) 뒤에 게이트 항목 추가

**추가 내용**:
```markdown
### 게이트

ANALYSIS 완료 → 사용자 확인 (interactive) / PM 자율 승인 (agentic)
```

**6-b. PLAN 단계 QA Gate 추가**

**위치**: PLAN 단계 "공통" 섹션 (133줄), 기존:
```
- **STATE 갱신**: 단계 시작/완료 시 STATE.md 갱신
- **게이트**: PLAN.md + 배치 계획 사용자 확인 (interactive) / PM 자율 승인 (agentic)
```

**변경 후**:
```
- **STATE 갱신**: 단계 시작/완료 시 STATE.md 갱신
- **QA Gate** (op-task-qa) — PLAN.md 검증
- **PM Gate** (TASK.md 요구사항 체크박스 갱신 포함 — 하네스 §3 참조)
- **게이트**: PLAN.md + 배치 계획 사용자 확인 (interactive) / PM 자율 승인 (agentic)
```

**6-c. EXECUTE 배치별 QA Gate 추가**

**위치**: EXECUTE 단계 "게이트 (배치별)" 섹션 (158-160줄), 기존:
```
배치 완료 → PM 검토 → 사용자 확인 (interactive) / PM 자율 승인 후 다음 배치 (agentic)
배치 완료 후 `docs/PROJECT.md` 등록 확인
```

**변경 후**:
```
배치 완료 → **QA Gate** (op-task-qa) → PM 검토 → 사용자 확인 (interactive) / PM 자율 승인 후 다음 배치 (agentic)
배치 완료 후 `docs/PROJECT.md` 등록 확인
```

**변경이력 추가**: `v2.2 | 2026-04-02 | ANALYSIS 게이트 + PLAN QA Gate + EXECUTE 배치별 QA Gate 추가 (072)`

---

## 3. 실행 체크리스트

> 총 6개 Step

### Step 1: 하네스에 TASK.md 체크박스 갱신 원칙 추가
- [x] 완료
- **파일**: `opal/core/references/opal-harness-interactive.md`
- **작업 내용**: §3 PM Gate 본문 뒤(§4 앞)에 "TASK.md 체크박스 갱신 (PLAN PM Gate 시)" 하위 섹션 추가. 갱신 시점(PLAN PM Gate), 갱신 절차(TASK.md <-> PLAN.md 대조 후 `[x]`), 미커버 시 대응을 명세. 변경이력 v1.1 추가.
- **완료 기준**: §3 하위에 TASK.md 갱신 원칙이 명시되어 있고, 변경이력에 072 태스크 기록 존재
- **테스트**: 문서 Read로 §3 하위 섹션 존재 및 내용 확인
- **의존**: 없음

### Step 2: opd PLAN PM Gate에 TASK.md 갱신 명시
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**: STEP 3 섹션의 PLAN PM Gate 서술(57줄)에 "(TASK.md 요구사항 체크박스 갱신 포함 -- 하네스 SS3 참조)" 삽입. 변경이력 v1.9 추가.
- **완료 기준**: STEP 3 PM Gate 서술에 TASK.md 갱신 참조가 포함
- **테스트**: 문서 Read로 해당 줄 확인
- **의존**: Step 1

### Step 3: opds PLAN PM Gate에 TASK.md 갱신 명시
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**: STEP 2 섹션의 PLAN PM Gate 서술(37줄)에 "(TASK.md 요구사항 체크박스 갱신 포함 -- 하네스 SS3 참조)" 삽입. 변경이력 v1.9 추가.
- **완료 기준**: STEP 2 PM Gate 서술에 TASK.md 갱신 참조가 포함
- **테스트**: 문서 Read로 해당 줄 확인
- **의존**: Step 1

### Step 4: opp PLAN PM Gate에 TASK.md 갱신 명시
- [x] 완료
- **파일**: `opal/skills/opal-pilot-project/SKILL.md`
- **작업 내용**: STEP 2 섹션의 PLAN PM Gate 서술(40줄)에 "(TASK.md 요구사항 체크박스 갱신 포함 -- 하네스 SS3 참조)" 삽입. 변경이력 v1.7 추가.
- **완료 기준**: STEP 2 PM Gate 서술에 TASK.md 갱신 참조가 포함
- **테스트**: 문서 Read로 해당 줄 확인
- **의존**: Step 1

### Step 5: opdw 서브 하네스 [MUST] + PM Gate 보완
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
- **작업 내용**:
  - (a) Harness 섹션(13줄 뒤)에 서브 하네스 `[MUST]` 로딩 블록 추가 (opd/opds/opp와 동일 패턴)
  - (b) STEP 2 WIREFRAME 완료 서술(44줄)에 QA Gate 뒤 PM Gate 추가
  - (c) STEP 3 EXECUTE 완료 후 목록(62-63줄)에 PM Gate 항목 삽입 (QA -> PM -> DONE.md 순서)
  - 변경이력 v1.5 추가
- **완료 기준**: Harness에 [MUST] 서브 하네스 블록 존재, WIREFRAME/EXECUTE 모두 PM Gate 포함, 변경이력 기록
- **테스트**: 문서 Read로 3개 위치(Harness, WIREFRAME, EXECUTE) 확인
- **의존**: Step 1

### Step 6: opwt 단계별 게이트 보완
- [x] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`
- **작업 내용**:
  - (a) ANALYSIS 단계 STATE 갱신 뒤에 "게이트" 하위 섹션 추가: 사용자 확인 (interactive) / PM 자율 승인 (agentic)
  - (b) PLAN 단계 "공통" 섹션에 QA Gate(op-task-qa) + PM Gate(TASK.md 갱신 포함) 추가 (기존 사용자 확인 게이트 앞에)
  - (c) EXECUTE 단계 "게이트 (배치별)" 서술에 QA Gate(op-task-qa) 삽입 (PM 검토 앞에)
  - 변경이력 v2.2 추가
- **완료 기준**: ANALYSIS에 게이트 존재, PLAN에 QA Gate + PM Gate 존재, EXECUTE 배치별에 QA Gate 존재, 변경이력 기록
- **테스트**: 문서 Read로 3개 단계의 게이트 확인
- **의존**: Step 1

---

## 4. QA 체크리스트

### 기능 테스트
- [x] O1: opal-harness-interactive.md §3에 TASK.md 체크박스 갱신 원칙이 명시되어 있는가
- [x] O2: opd/opds/opp 각각의 PLAN PM Gate에 TASK.md 갱신 참조가 있는가
- [x] O3: opdw에 서브 하네스 [MUST] 블록이 opd/opds/opp와 동일 패턴으로 존재하는가
- [x] O3: opdw WIREFRAME/EXECUTE 모두 PM Gate가 QA Gate 뒤에 위치하는가
- [x] O4: opwt ANALYSIS에 사용자 확인/PM 자율 승인 게이트가 있는가
- [x] O4: opwt PLAN에 QA Gate(op-task-qa)가 사용자 확인 앞에 있는가
- [x] O4: opwt EXECUTE 배치별에 QA Gate(op-task-qa)가 PM 검토 앞에 있는가

### 일관성 테스트
- [x] 모든 스킬의 QA -> PM Gate 순서가 일관되는가 (QA 먼저, PM 나중)
- [x] 서브 하네스 [MUST] 블록 문구가 기존 opd/opds/opp의 패턴과 동일한가
- [x] opwt QA Gate가 op-task-qa를 사용하는가 (op-dev-qa가 아닌 -- 범용 오케스트레이터 기준)
- [x] 변경이력이 모든 수정 파일에 추가되었는가

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] 변경이력 형식이 CONVENTIONS.md 규칙(일시 KST, semver)을 따르는가
- [x] 하네스 섹션 번호 참조(§2, §3)가 실제 문서 구조와 일치하는가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| opdw에 Agentic Mode 섹션이 없음 | 서브 하네스 [MUST] 추가 시 agentic 분기는 있으나 Agentic Mode 전체 섹션은 미존재. 이번 태스크 범위 밖 | 서브 하네스 [MUST] 블록만 추가. Agentic Mode 전체 섹션 추가는 별도 태스크로 분리 |
| opwt QA 단계와 PLAN/EXECUTE QA Gate 혼동 | opwt는 자체 QA 단계(consistency-rules.md 기반)와 하네스 표준 QA Gate(op-task-qa)가 공존 | PLAN/EXECUTE에는 하네스 표준 op-task-qa 사용, 최종 QA 단계는 기존 consistency-rules.md 유지. 역할 분리 명확히 서술 |
