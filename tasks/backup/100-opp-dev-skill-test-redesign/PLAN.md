# PLAN: opds/opd TEST-SCENARIO 흐름 재설계

> 태스크: tasks/100-opp-dev-skill-test-redesign/
> 스킬: opal-pilot-project (opp)
> 작성일: 2026-04-08

---

## 1. 변경 설계

### 1-1. opds (opal-pilot-dev-short) 변경 전/후

#### STEP 2: PLAN + TEST-SCENARIO 단계

**변경 전**

```
PLAN 디스패치
  → QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate
  → TEST-SCENARIO 디스패치 (연속)
  → 사용자 보고 (PLAN + TEST-SCENARIO 함께) → 승인 → EXECUTE
```

문제: QA/PM Gate가 PLAN만 검토. TEST-SCENARIO는 Gate 미통과.

**변경 후**

```
PLAN 디스패치
  → TEST-SCENARIO 디스패치 (연속) ← 이동: Gate 전으로
  → QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate
    (PLAN + TEST-SCENARIO 둘 다 검토 대상)
  → 사용자 보고 → 승인 → EXECUTE
```

핵심 변경:
- TEST-SCENARIO 디스패치를 QA Gate **앞**으로 이동
- QA Gate 검토 대상: PLAN.md + TEST-SCENARIO.md 동시 검토
- 단계 헤더: `## STEP 2: PLAN + TEST-SCENARIO` → `## STEP 2: PLAN` / `## STEP 2-b: TEST-SCENARIO` 로 논리 분리 (헤더 이름 자체는 검토)

#### STEP 3: EXECUTE → STEP 3: EXECUTE + TEST

**변경 전**

```
EXECUTE 디스패치 (op-dev-execute)
  → [EXECUTE 완료 후]
    1. op-dev-test-agent 호출 → 결과 채움 + 판정 → State Gate
    2. PM Gate → State Gate
    3. DONE.md 생성
    4. 완료 보고
```

문제: TEST가 "완료 후" 서브스텝에 묻힘. STATE.md 별도 행 없음. 실패 시 재시도 없음.

**변경 후**

```
EXECUTE 디스패치 (op-dev-execute)
  → EXECUTE 완료 선언 → State Gate

[TEST 단계 진입 — 공식 단계]
  → op-dev-test-agent 디스패치 → TEST-SCENARIO 실행 + 결과 기록 + PASS/FAIL 판정 → State Gate
    ↓ PASS
  QA Gate → State Gate → PM Gate → State Gate → DONE.md → 완료 보고
    ↓ FAIL
  [TEST 루핑 — 최대 3회]
  op-dev-execute (fix 모드) 디스패치 → State Gate
  op-dev-test-agent 재호출 → 재판정 → State Gate
  ... (최대 3회)
  3회 초과 → 사용자 에스컬레이션
```

#### opds STATE.md 진행 현황 템플릿

**변경 전**

| 필드 | 값 |
|------|------|
| 모드 | Short Task |
| 단계 목록 | TASK / PLAN+TEST-SCENARIO / EXECUTE |

진행 현황 행: TASK(2행) + PLAN(8행) + EXECUTE(6행) = 16행

**변경 후**

| 필드 | 값 |
|------|------|
| 모드 | Short Task |
| 단계 목록 | TASK / PLAN / TEST-SCENARIO / EXECUTE / TEST |

진행 현황 행 — 추가 내역:
- PLAN 단계: Gates는 PLAN.md + TEST-SCENARIO.md 검토로 변경 (행 수 동일, 설명 변경)
- TEST-SCENARIO 단계: "작업", "State Gate" 행 신설 (2행 추가)
- EXECUTE 단계: 기존 행 유지 + EXECUTE 완료 State Gate 분리
- TEST 단계: "작업", "State Gate", "QA Gate", "State Gate", "PM Gate", "State Gate" 행 신설 (6행)

새 템플릿 (전체):

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
| 15 | TEST | 작업 (op-dev-test-agent) | ⬜ | - |
| 16 | TEST | State Gate | ⬜ | - |
| 17 | TEST | QA Gate | ⬜ | - |
| 18 | TEST | State Gate | ⬜ | - |
| 19 | TEST | PM Gate | ⬜ | - |
| 20 | TEST | State Gate | ⬜ | - |
| 21 | TEST | 사용자 확인 | ⬜ | - |
```

> TEST 루핑 발생 시: 루핑 회차별로 "TEST | fix 작업 (1/3)" 등의 행을 동적 추가한다.

---

### 1-2. opd (opal-pilot-dev) 변경 전/후

#### STEP 3: PLAN + TEST-SCENARIO 단계

**변경 전**

```
PLAN 디스패치 (3-1)
  → QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate
TEST-SCENARIO 디스패치 (3-2, 연속)
  → 사용자 보고 → 승인 → EXECUTE
```

**변경 후**

```
PLAN 디스패치 (3-1)
TEST-SCENARIO 디스패치 (3-2, 연속) ← 이동: Gate 전으로
  → QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate
    (PLAN + TEST-SCENARIO 둘 다 검토 대상)
  → 사용자 보고 → 승인 → EXECUTE
```

핵심 변경: opds와 동일한 논리. TEST-SCENARIO를 QA Gate 앞으로 이동.

#### STEP 4: EXECUTE + TEST 단계

opds의 STEP 3 변경과 동일한 구조를 STEP 4에 적용.

```
EXECUTE 디스패치 (op-dev-execute)
  → EXECUTE 완료 → State Gate

[TEST 단계]
  → op-dev-test-agent 디스패치 → 판정 → State Gate
    ↓ PASS: QA Gate → State Gate → PM Gate → State Gate → DONE.md
    ↓ FAIL: fix 루핑 (최대 3회) → 초과 시 에스컬레이션
```

#### opd STATE.md 진행 현황 템플릿

**변경 전**

| 필드 | 값 |
|------|------|
| 모드 | Full Task |
| 단계 | TASK / ANALYSIS / PLAN+TEST-SCENARIO / EXECUTE |

**변경 후**

| 필드 | 값 |
|------|------|
| 모드 | Full Task |
| 단계 | TASK / ANALYSIS / PLAN / TEST-SCENARIO / EXECUTE / TEST |

진행 현황 행 — opd는 ANALYSIS 단계가 추가되므로:
- ANALYSIS 단계 행 유지 (변경 없음)
- PLAN 행: opds와 동일 변경 적용
- TEST-SCENARIO, EXECUTE, TEST 행: opds와 동일 구조

---

## 2. TEST 루핑 설계

### 루핑 의사코드

```
PROCEDURE run_test_stage(task_folder, test_scenario_path):
  attempt = 0
  MAX_ATTEMPTS = 3

  WHILE attempt < MAX_ATTEMPTS:
    attempt += 1

    # op-dev-test-agent 디스패치
    result = dispatch_worker(
      worker = "op-dev-test-agent",
      inputs = {
        task_folder: task_folder,
        test_scenario: test_scenario_path,
        changed_files: execute_changed_files
      }
    )
    update_state_gate()  # State Gate

    IF result.verdict == "PASS":
      # 정상 종료 → QA Gate → PM Gate → DONE
      run_qa_gate()         # State Gate
      run_pm_gate()         # State Gate
      generate_done_md()
      report_completion()
      RETURN PASS

    ELSE:  # FAIL
      IF attempt >= MAX_ATTEMPTS:
        # 에스컬레이션
        escalate_to_user(
          message = f"TEST {attempt}회 FAIL — 사용자 판단 필요",
          failed_items = result.failed_scenarios
        )
        RETURN ESCALATED

      # fix 모드 디스패치
      dispatch_worker(
        worker = "op-dev-execute",
        mode = "fix",
        inputs = {
          task_folder: task_folder,
          fix_context = {
            failed_scenarios: result.failed_scenarios,
            test_run: attempt,
            max_attempts: MAX_ATTEMPTS
          }
        }
      )
      update_state_gate()  # State Gate
      # → 루프 계속 (재TEST)
```

### 흐름도

```
TEST 단계 진입
     │
     ▼
[op-dev-test-agent 디스패치]
     │
     ▼
PASS/FAIL 판정
     │
 ┌───┴───┐
PASS    FAIL
 │       │
 │    attempt < 3?
 │    ┌──┴──┐
 │   YES    NO
 │    │     │
 │  [fix]  [에스컬레이션]
 │    │     사용자에게 보고
 │    │     + 실패 항목 전달
 │    ▼
 │  [재TEST]
 │    │
 └────┘(루프)
 │
 ▼
QA Gate → State Gate
PM Gate → State Gate
DONE.md 생성
완료 보고
```

### fix 모드 워커 디스패치 — 컨텍스트 주입 설계

op-dev-execute를 fix 모드로 디스패치할 때 다음 컨텍스트를 프롬프트에 주입한다:

```
[WORKER]
op-dev-execute 스킬을 수행하라 (fix 모드).
**스킬 경로**: {op-dev-execute/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**모드**: fix
**fix 컨텍스트**:
  - 실패한 TEST-SCENARIO 항목: {TEST-SCENARIO.md의 FAIL 항목 목록}
  - 현재 시도 회차: {attempt}/{MAX_ATTEMPTS}
  - 실패 요약: {op-dev-test-agent가 기록한 결과 요약}
**checklist_source**: PLAN.md 섹션 "3. 실행 체크리스트" (실패 항목에 집중)
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. fix 범위를 실패 항목으로 한정. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
```

핵심 설계 원칙:
- **실패 항목 전달**: op-dev-test-agent가 TEST-SCENARIO.md에 기록한 FAIL 항목을 그대로 추출하여 프롬프트에 삽입
- **fix 범위 한정**: fix 모드 워커는 실패 항목과 직접 관련된 코드만 수정 (과도한 리팩토링 방지)
- **회귀 방지**: 하네스 §1 회귀 방지 규칙 명시 — 수정 후 이전 통과 항목 재검증

---

## 3. 실행 체크리스트

- [ ] `opal/skills/opal-pilot-dev-short/SKILL.md`
- [ ] `opal/skills/opal-pilot-dev/SKILL.md`

### `opal/skills/opal-pilot-dev-short/SKILL.md` 변경 섹션

| 섹션 | 변경 내용 |
|------|----------|
| `## Harness` 모드 선언 | `Short Task (TASK → PLAN+TEST-SCENARIO → EXECUTE)` → `Short Task (TASK → PLAN → TEST-SCENARIO → EXECUTE → TEST)` |
| `## STEP 2: PLAN + TEST-SCENARIO` | 헤더 분리 불필요 — 단계 내에서 순서 재배치: PLAN 디스패치 → TEST-SCENARIO 디스패치 → Gates 순으로 재작성 |
| TEST-SCENARIO 디스패치 위치 | QA Gate 통과 후 → QA Gate 전 (PLAN 직후)으로 이동 |
| QA Gate 검토 대상 명시 | PLAN + TEST-SCENARIO 동시 검토임을 명시 |
| `## STEP 3: EXECUTE` | "EXECUTE 완료 후" 서브스텝 → 독립 TEST 단계로 분리 |
| TEST 단계 신설 | EXECUTE 완료 → State Gate → TEST 단계 진입 (op-dev-test-agent 디스패치 + 루핑 로직 + 에스컬레이션) |
| `## STATE.md 도메인 치환값` | 단계 목록 갱신 + 진행 현황 행 예시 갱신 (TEST-SCENARIO 행, TEST 행 추가) |
| `## 변경이력` | v2.5 항목 추가 |

### `opal/skills/opal-pilot-dev/SKILL.md` 변경 섹션

| 섹션 | 변경 내용 |
|------|----------|
| `## Harness` 모드 선언 | `Full Task (TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE)` → `Full Task (TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST)` |
| `## STEP 3: PLAN + TEST-SCENARIO` | TEST-SCENARIO 디스패치를 3-2에서 3-1.5(Gate 전)으로 재배치. 3-2 섹션을 "3-2. QA/PM Gates"로 재명명하고 검토 대상에 TEST-SCENARIO 포함 명시 |
| `## STEP 4: EXECUTE` | opds STEP 3와 동일한 변경 적용 (TEST 단계 신설, 루핑 로직) |
| `## STATE.md 도메인 설정` | 단계 목록 갱신 (`TASK / ANALYSIS / PLAN / TEST-SCENARIO / EXECUTE / TEST`) + 진행 현황 행 예시 신설 |
| `## 변경이력` | v2.4 항목 추가 (opd 기존 v2.3 이후) |

---

## 4. 검토 포인트

### 4-1. 하네스 루핑 가드 (§1) 정합성

하네스 §1 "자동 루핑 제약" 테이블:

| 실패 유형 | 최대 재시도 | 초과 시 동작 |
|----------|-----------|------------|
| unit/integration test (L3a) | **3회** | 사용자 에스컬레이션 |

TEST 단계 루핑은 `unit/integration test (L3a)` 분류로 최대 3회 적용. 설계와 정합.

추가 적용 규칙:
- **회귀 방지**: fix 후 이전 PASS 항목 재실행 → 회귀 발생 시 루프 즉시 중단 + 에스컬레이션
- **사용자 게이트 유지**: 루핑은 자동이나 최종 PASS 확인은 QA Gate / PM Gate를 거침

### 4-2. fix 워커 디스패치 프롬프트 설계

실패 항목 전달 방식:

1. **op-dev-test-agent**는 TEST-SCENARIO.md에 각 시나리오 결과를 기록한다 (기존 동작).
2. PM(오케스트레이터)이 TEST-SCENARIO.md에서 `status: FAIL` 항목을 추출한다.
3. 추출된 항목을 프롬프트의 `fix 컨텍스트 > 실패한 TEST-SCENARIO 항목`에 삽입한다.
4. fix 워커는 해당 항목의 실패 원인을 우선 분석하고 수정 범위를 PLAN.md 체크리스트로 한정한다.

> TASK.md의 확정 설계(§ "새 TEST 단계 흐름")에 `op-dev-execute (fix 모드)` 표현이 이미 존재.
> fix 모드 처리 방식은 op-dev-execute SKILL.md에 이미 구현되어 있는지 EXECUTE 단계에서 확인 필요.
> 미구현 시 별도 처리: 프롬프트 컨텍스트만으로 fix 범위를 충분히 안내 가능.

### 4-3. STATE.md 단계 목록 명칭 변경

| 스킬 | 기존 | 변경 |
|------|------|------|
| opds | TASK / PLAN+TEST-SCENARIO / EXECUTE | TASK / PLAN / TEST-SCENARIO / EXECUTE / TEST |
| opd | TASK / ANALYSIS / PLAN+TEST-SCENARIO / EXECUTE | TASK / ANALYSIS / PLAN / TEST-SCENARIO / EXECUTE / TEST |

`PLAN+TEST-SCENARIO`를 `PLAN`과 `TEST-SCENARIO`로 분리하는 이유:
- TEST-SCENARIO를 독립 단계로 추적 가능하게 함
- Gate가 PLAN + TEST-SCENARIO를 함께 검토하므로, 각 산출물 상태를 별도 행으로 관리

### 4-4. oppd/opsdd 범위 제외

이번 태스크는 **opds와 opd만 수정** 대상이다.

- `oppd` (opal-pilot-project-dev): 이번 범위 제외
- `opsdd` (opal-pilot-sdd): 이번 범위 제외

두 스킬은 별도 태스크로 동일 변경을 적용할 수 있으나, 이번 태스크 완료 기준에는 포함되지 않는다.

---

## 5. 리스크 및 고려사항

| 항목 | 내용 | 대응 |
|------|------|------|
| fix 모드 미지원 | op-dev-execute가 fix 모드를 별도로 정의하지 않을 수 있음 | 프롬프트 컨텍스트로 충분히 안내. 필요 시 별도 fix 워커 정의를 후속 태스크로 분리 |
| TEST-SCENARIO 행 위치 | STATE.md에서 TEST-SCENARIO 행이 PLAN 단계 Gates 앞에 위치 — 직관적이지 않을 수 있음 | TASK.md 확정 설계 기준으로 구현. 이후 피드백 반영 |
| 루핑 중 State Gate | fix + 재TEST 매 회차마다 State Gate 필요 — 행이 동적으로 늘어남 | 루핑 행을 `TEST \| fix 작업 (N/3)`, `TEST \| State Gate (N/3)` 패턴으로 동적 추가 |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-08 | 초기 작성 — opds/opd TEST-SCENARIO 흐름 재설계 PLAN |
