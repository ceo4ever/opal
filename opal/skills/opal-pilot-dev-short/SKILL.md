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
모드: Short Task (TASK → PLAN → TEST-SCENARIO → EXECUTE → TEST)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

---

## STEP 1: TASK

harness "4. TASK 공통 프로세스" 참조. 다음 단계명: PLAN.

TASK 완료 → **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인) → 사용자 보고.

---

## STEP 2: PLAN

### PLAN 디스패치

op-dev-plan 워커 디스패치. **model**: advanced. 이전 산출물: TASK.md만 (ANALYSIS.md 없음).

> **Short Task는 단계를 줄이는 것이지, 분석을 줄이는 것이 아니다.** ANALYSIS.md 없이 호출되면 op-dev-plan이 코드 분석을 직접 수행한다. 분석 품질은 Full Task와 동일해야 한다.

> **[PM 컨텍스트 주입]** 워커 디스패치 프롬프트의 첫 줄에 `[WORKER]`를 삽입한다. `[WORKER]` 마커가 있으면 워커는 부트스트랩을 생략한다. PM은 디스패치 시 다음을 프롬프트에 포함해야 한다:
> 1. 하네스 Guards 핵심 규칙 (구현 금지 원칙, 커밋 규칙)
> 2. 관련 참조 문서 경로 (docs/PROJECT.md 문서 테이블 기반)
> 3. 기술 스택 연동 지시 (기존 "참조 문서 전달 의무" 통합)

### TEST-SCENARIO 스킵 조건

**문서 전용** 작업(PLAN.md 파일 변경 계획이 모두 `.md`, 소스 코드 없음)이면 스킵. 보고 시 "TEST-SCENARIO: 문서 전용 작업으로 스킵" 표기.

### TEST-SCENARIO 디스패치

PLAN 완료 직후 연속 디스패치. **model**: light. 이전 산출물: TASK.md + PLAN.md.

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함한다.

워커 완료
  → **State Gate**
  → **QA Gate** (op-dev-qa — PLAN.md + TEST-SCENARIO.md 동시 검토) → **State Gate**
  → **Artifact Gate** (하네스 §2.5 참조) → **State Gate**
  → **PM Gate** (체크리스트 갱신 상태 확인 — 하네스 interactive §3 참조. 미갱신 시 QA 재소환) → **State Gate**
  → 사용자에게 PLAN + TEST-SCENARIO 함께 보고. 승인 = EXECUTE 시작 허가.

---

## STEP 3: EXECUTE

op-dev-execute 워커 디스패치. **model**: standard. checklist_source: PLAN.md 섹션 "3. 실행 체크리스트". execution-plan.json 있으면 전달.

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함한다.

### EXECUTE 완료 후

워커가 changed_files를 반환하면:
→ **State Gate** → **TEST 단계 진입**

---

## STEP 4: TEST

op-dev-test-agent 워커 디스패치. TEST-SCENARIO.md 실행 + 결과 기록 + PASS/FAIL 판정.

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + TEST-SCENARIO.md 경로 + changed_files 전달.

워커 완료 → **State Gate**

### PASS 시

QA Gate (op-dev-qa — 체크리스트 갱신 포함) → **State Gate**
→ **PM Gate** (TEST 결과 검토 + 체크리스트 갱신 상태 확인. 미갱신 시 QA 재소환) → **State Gate**
→ 모든 체크리스트 갱신 완료 확인 후 DONE.md 생성
→ 사용자에게 완료 보고

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
3. fix 완료 → **State Gate** → op-dev-test-agent 재호출 (루프)
4. 3회 초과 시 사용자 에스컬레이션:
   "TEST {N}회 FAIL — 수동 개입 필요. 실패 항목: {목록}"

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

| 필드 | 값 |
|------|------|
| 모드 | Short Task |
| 단계 목록 | TASK / PLAN / TEST-SCENARIO / EXECUTE / TEST |

**진행 현황 행 예시** (STATE.md 초기 생성 시 이 구조로 작성):

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | 사용자 확인 | ⬜ | - |
| 3 | PLAN | 작업 | ⬜ | - |
| 4 | TEST-SCENARIO | 작업 | ⬜ | - |
| 5 | TEST-SCENARIO | State Gate | ⬜ | - |
| 6 | PLAN | QA Gate | ⬜ | - |
| 7 | PLAN | State Gate | ⬜ | - |
| 8 | PLAN | Artifact Gate | ⬜ | - |
| 9 | PLAN | State Gate | ⬜ | - |
| 10 | PLAN | PM Gate | ⬜ | - |
| 11 | PLAN | State Gate | ⬜ | - |
| 12 | PLAN | 사용자 확인 | ⬜ | - |
| 13 | EXECUTE | 작업 | ⬜ | - |
| 14 | EXECUTE | State Gate | ⬜ | - |
| 15 | TEST | 작업 | ⬜ | - |
| 16 | TEST | State Gate | ⬜ | - |
| 17 | TEST | QA Gate | ⬜ | - |
| 18 | TEST | State Gate | ⬜ | - |
| 19 | TEST | PM Gate | ⬜ | - |
| 20 | TEST | State Gate | ⬜ | - |
| 21 | TEST | 사용자 확인 | ⬜ | - |
```

> TEST 루핑 발생 시: "TEST | fix 작업 (N/3)", "TEST | State Gate (N/3)" 행을 동적 추가한다.

---

## Agentic Mode

opal-harness-agentic.md 참조. `--agentic` 플래그 활성화 시 이 스킬의 차이점만 기술한다.

### 활성화

`//opds --agentic {작업 설명}` 형식으로 호출. STATE.md 모드 필드를 `agentic`으로 기록한다.

### 자율 게이트 흐름

```
TASK (PM 직접) → PLAN+TEST-SCENARIO Gate → EXECUTE Gate → TEST Gate
                   PM 자율 검토              PM 자율 검토    PM 자율 검토
```

- TASK 이후 3개 게이트를 PM이 자율 통과
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- AGENTIC-LOG.md에 모든 판단/오류/수정/의사결정 기록

### 에스컬레이션 규칙 (agentic 유지)

에스컬레이션 규칙(Full Task 전환 제안)은 agentic mode에서도 유지한다. PM이 판단하여 자동 전환하지 않고, 사용자에게 에스컬레이션으로 보고한다.

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
