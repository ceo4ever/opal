# QA: PLAN — QA 체크리스트 갱신 강제 (085)

> 검토일: 2026-04-05 | 판정: Pass

---

## 1. 요약

PLAN.md는 PM이 QA 체크리스트 갱신을 반복 누락하는 구조적 문제를 2단계(QA 에이전트 1차 갱신 + PM Gate 2차 확인)로 해결하는 계획을 담고 있다. 수정 대상은 하네스 공통·interactive, QA 스킬 2종(op-task-qa, op-dev-qa), 오케스트레이터 3종(opp, opds, opd) 총 7개 파일이다. 현황 조사, 파일 변경 계획, 핵심 설계, 실행 체크리스트, QA 체크리스트 구조가 모두 갖추어져 있으며 TASK.md 요구사항 3건을 빠짐없이 커버한다.

---

## 2. 검증 결과

### 2-1. R1~R3 요구사항 매핑 검증

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R1-a | op-task-qa 체크리스트 갱신 프로세스 추가 | Pass | Step 3 → §D에 Step 4 신설 + 단계별 갱신 대상 테이블 명시 |
| R1-b | op-dev-qa 체크리스트 갱신 프로세스 추가 | Pass | 동일 패턴 + TEST-SCENARIO 결과 반영 명시 |
| R1-c | PLAN QA 시 TASK.md 요구사항 체크박스 갱신 | Pass | §D 테이블 "PLAN 단계 → TASK.md 요구사항 체크박스" 행 명시 |
| R1-d | EXECUTE QA 시 PLAN.md §3+§4 체크리스트 갱신 | Pass | §D 테이블 "EXECUTE 단계 → PLAN.md §3+§4" 행 명시 |
| R2-a | 모든 PM Gate에 체크리스트 갱신 상태 확인 절차 추가 | Pass | §C에 PLAN/EXECUTE PM Gate별 확인 절차 서술 + Step 5~7에서 오케스트레이터 적용 |
| R2-b | PM 직접 갱신 금지 + QA 재소환 원칙 | Pass | §A·§C·§D 모두에 명시 |
| R3 | QA 미발동 시에도 PM Gate에서 감지 → QA 소환 | Pass | §C EXECUTE PM Gate 3번 + §A 구조도에 명시 |

### 2-2. 의존성 검증

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| D-1 | Phase 1 순차 (Step 1 → Step 2) | Pass | Step 2가 Step 1의 원칙을 참조하므로 순차 필수 |
| D-2 | Phase 2 병렬 (Step 3, Step 4) | Pass | op-task-qa, op-dev-qa는 서로 독립 |
| D-3 | Phase 3 병렬 (Step 5, Step 6, Step 7) | Pass | 오케스트레이터 3개 파일은 서로 독립. 단, Step 2 완료 후 진행(§C 정의 전제) |
| D-4 | Step 5~7의 Step 2 의존 명시 여부 | Pass | 각 Step 하단 "의존: Step 2" 명시 |

### 2-3. QA 체크리스트 요구사항 커버리지 검증

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| QA-1 | R1 관련 기능 테스트 3건 | Pass | §4 기능 테스트 첫 3행이 R1 하위 항목 각각을 커버 |
| QA-2 | R2 관련 기능 테스트 2건 | Pass | §4 기능 테스트 4~5행이 R2를 커버 |
| QA-3 | R3 관련 기능 테스트 1건 | Pass | §4 기능 테스트 6행이 R3를 커버 |
| QA-4 | 일관성 테스트 3건 | Pass | 하네스 공통/interactive, QA 스킬 2개, 오케스트레이터 3개 커버 |
| QA-5 | 문서 품질 테스트 2건 | Pass | 한국어+영어 규칙, 변경이력 커버 |

### 2-4. 추가 검증 — R1 QA 에이전트 양쪽 적용

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| AV-1 | PLAN QA에서 체크리스트 갱신 적용 | Pass | §D "PLAN 단계 → TASK.md 요구사항 체크박스" 명시 |
| AV-2 | EXECUTE QA에서 체크리스트 갱신 적용 | Pass | §D "EXECUTE 단계 → PLAN.md §3+§4" 명시 |
| AV-3 | PLAN PM Gate에서 갱신 상태 확인 | Pass | §C "PLAN PM Gate 시" 1~3번 절차 명시 |
| AV-4 | EXECUTE PM Gate에서 갱신 상태 확인 | Pass | §C "EXECUTE PM Gate 시" 1~4번 절차 명시 |

### 2-5. 핵심 설계 구체성 평가

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| CS-1 | §B opal-harness.md 변경 — Before/After 명시 | Pass | 현재/변경 텍스트 모두 제시 |
| CS-2 | §C opal-harness-interactive.md 변경 — 삽입 위치 명시 | Pass | §3 PM Gate 하위 추가, §4 2차 검증 변경 모두 명시 |
| CS-3 | §D QA 스킬 Step 추가 — 번호 재배정 포함 | Pass | Step 3.5 → Step 4, 기존 Step 4/5 → Step 5/6 명시 |
| CS-4 | §E 오케스트레이터 변경 패턴 — 적용 위치 명시 | Pass | opp/opds/opd별 적용 Gate 열거 |
| CS-5 | `checklist_path` 입력 필드 추가 여부 | Pass | Step 3/4 작업 내용에 입력 테이블 필드 추가 명시 |
| CS-6 | Warning/Fail 처리 규칙 명시 | Pass | §D 갱신 규칙에 Pass/Fail/Warning 처리 모두 서술 |

---

## 3. 지적 사항

### Warning

**W-1 — op-dev-qa의 단계명 불일치 가능성 (Info 수준, 진행에 영향 없음)**

`op-dev-qa`의 현재 `stage` 입력값은 `ANALYSIS / PLAN / WIREFRAME / EXECUTE-UI`이다. PLAN.md §D에서 "EXECUTE 단계"로 서술하지만, op-dev-qa의 EXECUTE 단계는 `EXECUTE-UI`이다. 구현 시 단계명 매핑 테이블을 정확히 대응시켜야 한다. PLAN 텍스트는 개념적 설명으로 허용 가능하나, SKILL.md 작성 시 실제 stage 값을 정확히 사용해야 함을 유의한다.

**→ 이 항목은 Warning 수준으로, PLAN 전체 판정에는 영향 없음. EXECUTE 단계에서 구현자가 주의할 사항으로 기재한다.**

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R1 | PLAN §3 Step 3+4 + 핵심 설계 §D 에 매핑 | Pass |
| TASK.md R2 | PLAN §3 Step 5~7 + 핵심 설계 §C·§E에 매핑 | Pass |
| TASK.md R3 | PLAN §C "EXECUTE PM Gate 시 3번" + §3 각 Step에 매핑 | Pass |
| opal-harness.md §2 | PLAN §B에서 현재 상태 정확히 인용 | Pass |
| opal-harness-interactive.md §3/§4 | PLAN §C에서 현재 상태 정확히 인용 | Pass |
| op-task-qa SKILL.md | 현재 Step 구조(Step 1~5) 확인 — §D Step 삽입 위치 일치 | Pass |
| op-dev-qa SKILL.md | 현재 Step 구조(Step 1~5) 확인 — §D Step 삽입 위치 일치 | Pass |
| opal-pilot-project SKILL.md | 현재 PLAN PM Gate, EXECUTE PM Gate 위치 확인 — §E 적용 위치 일치 | Pass |
| opal-pilot-dev-short SKILL.md | 현재 PLAN PM Gate, EXECUTE PM Gate 위치 확인 — §E 적용 위치 일치 | Pass |
| opal-pilot-dev SKILL.md | 현재 ANALYSIS PM Gate, PLAN PM Gate, EXECUTE PM Gate 위치 확인 — §E 적용 위치 일치 | Pass |

---

## 5. 판정

**Pass**

TASK.md 요구사항 R1~R3이 PLAN의 실행 체크리스트(Step 1~7)와 핵심 설계(§A~§E)에 빠짐없이 매핑된다. Step 간 의존성이 논리적으로 올바르고, QA 체크리스트가 요구사항을 모두 커버한다. 핵심 설계의 Before/After, 삽입 위치, Step 번호 재배정, 갱신 규칙이 구체적으로 서술되어 있어 이 PLAN만 보고 즉시 실행 가능한 수준이다. Warning 1건(op-dev-qa stage 명 주의)은 EXECUTE 단계에서 구현자가 확인하면 충분하며 PLAN 품질에는 영향 없다.
