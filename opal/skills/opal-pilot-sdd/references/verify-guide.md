# 검증 상세 가이드

> opal-pilot-sdd Phase 2: SPEC-VERIFY 및 Phase 5: TASKS-VERIFY의 상세 검증 지침.
> op-sdd-verify 스킬과 연동된다.

---

## 1. 개요

검증은 opsdd 파이프라인에서 **구현 전 품질 보장**의 핵심이다. SPEC.md 작성 후, TASKS.md 분해 후 각각 전문 검증을 수행하여 환각, 스코프 드리프트, 추적성 갭을 사전에 차단한다.

**검증 시점**:
- Phase 2: SPEC-VERIFY -- SPEC.md 3계층 검증 + TEST-SCENARIOS.md 도출 (mode=spec)
- Phase 5: TASKS-VERIFY -- TASKS.md 커버리지/의존관계 검증 (mode=tasks)
- Phase 7: DONE -- 최종 검증 (VERIFY.md에 DONE 검증 섹션 추가)

**원칙**:
- 검증 수행자(op-sdd-verify)와 검증 리뷰어(opal-task-qa-agent)는 분리한다
- 판정에 반드시 구체적 근거를 첨부한다
- spec 내용을 직접 수정하지 않고, 판정과 피드백만 제공한다

---

## 2. 검증 3계층 상세

### 2-1. 구조적 검증

형식과 필수 요소의 존재를 확인한다. 규칙 기반 체크로 자동화 가능한 영역.

| # | 항목 | 기준 | 실패 시 판정 |
|---|------|------|-------------|
| S-1 | 필수 섹션 10개 존재 | Background, Goals, Non-goals, User Stories, Functional Requirements, Acceptance Criteria, Edge Cases, Non-functional Requirements, Constraints, Open Questions | Fail |
| S-2 | AC 형식 (GIVEN/WHEN/THEN) | 모든 AC가 GIVEN, WHEN, THEN 3요소를 포함 | Fail |
| S-3 | Open Questions 해소 | OQ 섹션이 "없음" 또는 비어있음 | Fail |
| S-4 | AC 최소 3개 | AC가 3개 이상 정의됨 | Fail |
| S-5 | FR 번호 체계 | [FR-NN] 형식으로 번호가 부여됨 | Warning |
| S-6 | 버전/상태 메타데이터 | 버전, 작성일, 상태가 기재됨 | Warning |

**검증 방법**: SPEC.md를 Read하여 각 항목을 체크한다. 구조적 검증은 내용 품질과 무관하게 형식만 확인한다.

### 2-2. 의미적 검증

내용의 일관성과 완전성을 확인한다. AI 에이전트 분석이 필요한 영역.

| # | 항목 | 기준 | 실패 시 판정 |
|---|------|------|-------------|
| M-1 | Goals <-> FR <-> AC 정합 | 모든 Goal에 대응 FR 존재, 모든 FR에 대응 AC 존재 | Fail |
| M-2 | Non-goals와 Goals 모순 없음 | Goals와 Non-goals 사이에 모순/중복 없음 | Fail |
| M-3 | 제약 조건 실현 가능 | Constraints가 FR/AC와 모순되지 않음 | Warning |
| M-4 | 기존 코드/문서 충돌 없음 | ARCHITECTURE.md, CONVENTIONS.md와 충돌 없음 | Warning |
| M-5 | Edge Case 반영 | EC가 AC 또는 FR에 반영되었는지 교차 확인 | Warning |
| M-6 | NFR 측정 가능성 | NFR이 정량적 기준을 포함 | Warning |

**검증 방법**:
- M-1: Goals 목록에서 FR로의 매핑, FR에서 AC로의 매핑을 양방향 추적
- M-2: Goals와 Non-goals의 키워드를 비교하여 충돌 탐지
- M-3: Constraints의 각 항목이 FR/AC 달성을 불가능하게 하지 않는지 확인
- M-4: docs/ARCHITECTURE.md, docs/CONVENTIONS.md를 Read하여 교차 확인
- M-5: EC 항목이 AC 또는 FR의 정상 경로에서 벗어난 시나리오를 다루는지 확인
- M-6: NFR 항목에 수치(ms, %, 횟수 등)가 포함되어 있는지 확인

### 2-3. 도메인 검증

프로젝트 아키텍처 및 컨벤션과의 정합성을 확인한다. 프로젝트 문서 대조 방식.

| # | 항목 | 기준 | 실패 시 판정 |
|---|------|------|-------------|
| D-1 | 아키텍처 정합 | spec의 기능이 기존 아키텍처와 호환 가능 | Fail |
| D-2 | 컨벤션 준수 | 네이밍, 구조, 패턴이 CONVENTIONS.md와 일치 | Warning |

**검증 방법**:
- D-1: ARCHITECTURE.md의 레이어/컴포넌트 구조와 spec의 기능 범위를 대조. 기존 구조에 자연스럽게 통합 가능한지 판단
- D-2: CONVENTIONS.md의 네이밍/코드 규칙과 spec의 도메인 용어/파일 구조를 대조

---

## 3. VERIFY.md 누적 저널 구조

VERIFY.md는 모든 검증 결과를 **하나의 파일에 시간순으로 누적**하는 저널이다. Phase별로 섹션이 추가된다.

### 3-1. 전체 구조

```markdown
# Validation Journal: {기능명}

## SPEC 검증 (Phase 2: SPEC-VERIFY)
- 수행일: YYYY-MM-DD
- 워커: opal-task-agent -> op-sdd-verify (mode=spec)

### 구조적 검증
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| S-1 | 필수 섹션 10개 존재 | {Pass/Fail} | |
| S-2 | AC 형식 (GIVEN/WHEN/THEN) | {Pass/Fail} | {N}개 AC |
| S-3 | Open Questions 해소 | {Pass/Fail} | {N}개 잔존 |
| S-4 | AC 최소 3개 | {Pass/Fail} | |
| S-5 | FR 번호 체계 | {Pass/Warning} | |
| S-6 | 버전/상태 메타데이터 | {Pass/Warning} | |

### 의미적 검증
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| M-1 | Goals <-> FR <-> AC 정합 | {Pass/Fail} | |
| M-2 | Non-goals와 Goals 모순 없음 | {Pass/Fail} | |
| M-3 | 제약 조건 실현 가능 | {Pass/Warning} | |
| M-4 | 기존 코드/문서 충돌 없음 | {Pass/Warning} | |
| M-5 | Edge Case 반영 | {Pass/Warning} | |
| M-6 | NFR 측정 가능성 | {Pass/Warning} | |

### 도메인 검증
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| D-1 | 아키텍처 정합 | {Pass/Fail} | |
| D-2 | 컨벤션 준수 | {Pass/Warning} | |

### 테스트 시나리오 도출
- 총 시나리오: {N}개 (unit: {n}, integration: {n}, e2e: {n})
- AC 커버리지: {n}% ({n}/{n} AC -> {n} 시나리오)

### 판정: {Pass / Pass with Warnings / Fail}

---

## TASKS 검증 (Phase 5: TASKS-VERIFY)
- 수행일: YYYY-MM-DD
- 워커: opal-task-agent -> op-sdd-verify (mode=tasks)

### 검증 항목
| # | 항목 | 결과 | 비고 |
|---|------|------|------|
| T-1 | AC 커버리지 (모든 AC >= 1 태스크) | {Pass/Fail} | |
| T-2 | 역매핑 완전성 | {Pass/Warning} | |
| T-3 | TS 커버리지 (모든 TS >= 1 태스크) | {Pass/Fail} | |
| T-4 | 테스트 유형 균형 | {Pass/Warning} | |
| T-5 | 순환 의존 없음 | {Pass/Fail} | |
| T-6 | 누락 의존 없음 | {Pass/Fail} | |
| T-7 | 불필요 의존 없음 | {Pass/Warning} | |
| T-8 | 각 태스크 독립 완료 가능 | {Pass/Fail} | |
| T-9 | 입출력 명확 | {Pass/Warning} | |
| T-10 | 과대 태스크 없음 | {Pass/Warning} | |
| T-11 | 과소 태스크 없음 | {Pass/Warning} | |

### 추적 매트릭스 (최종)
| AC | FR | TS | 담당 태스크 | 커버리지 |
|----|----|----|-----------|----------|

### 판정: {Pass / Fail}

---

## DONE 검증 (Phase 7)
(Phase 6 완료 시 추가)
```

### 3-2. 누적 규칙

- VERIFY.md가 없으면 신규 생성한다
- 기존 VERIFY.md가 있으면 해당 Phase 섹션을 **하단에 추가**한다
- 이전 Phase의 검증 결과는 수정하지 않는다
- 재검증 시 이전 판정 아래에 `### 재검증 ({N}차)` 섹션을 추가한다

### 3-3. DONE 검증 섹션 (Phase 7)

Phase 6(EXECUTE-LOOP) 완료 후 최종 검증 결과를 추가한다:

```markdown
## DONE 검증 (Phase 7)
- 수행일: YYYY-MM-DD
- 검증자: opsdd 오케스트레이터 + QA 에이전트

### 전체 TS 상태
| 시나리오 ID | AC | 상태 | 담당 태스크 |
|------------|-----|------|-----------|
| TS-01 | AC-01 | Green | T1 |
| TS-02 | AC-01 | Green | T2 |
| ... | ... | ... | ... |

### 회귀 테스트
- 전체 테스트 스위트: {Pass / Fail}
- 회귀 발생: {없음 / {상세}}

### 최종 판정: {Pass / Fail}
```

---

## 4. TEST-SCENARIOS.md 구조

mode=spec에서 AC로부터 도출한 테스트 시나리오를 기록하는 문서이다.

### 4-1. 전체 구조

```markdown
# Test Scenarios: {기능명}

> 버전: 1.0 | 작성일: YYYY-MM-DD | SPEC.md v{X.Y} 기준
> 상태: Red (TDD -- 시나리오만 정의, 구현 전)

## 추적 매트릭스

| AC | 시나리오 ID | 유형 | 설명 | 상태 |
|----|-----------|------|------|------|
| AC-01 | TS-01 | unit | {시나리오 설명} | Red |
| AC-01 | TS-02 | integration | {시나리오 설명} | Red |
| AC-02 | TS-03 | unit | {시나리오 설명} | Red |
| EC-01 | TS-04 | unit | {엣지 케이스 설명} | Red |
| ... | ... | ... | ... | ... |

## 시나리오 상세

### TS-01: {시나리오명}

- **출처**: AC-01
- **유형**: unit / integration / e2e
- **GIVEN**: {사전 조건}
- **WHEN**: {행위}
- **THEN**: {기대 결과}
- **테스트 케이스**:
  - 정상: {정상 입력 -> 기대 출력}
  - 예외: {예외 입력 -> 기대 에러}
  - 경계값: {경계 입력 -> 기대 동작}
- **검증 방법**: {자동/수동, 도구}
- **매핑**: 태스크 미할당 (TASKS 단계에서 할당)
- **상태**: Red

### TS-02: {시나리오명}
...
```

### 4-2. 추적 매트릭스 규칙

- 모든 AC에서 최소 1개 시나리오를 도출한다 (AC 커버리지 100%)
- Edge Cases(EC)에서도 시나리오를 도출한다
- 시나리오 ID: `TS-NN` (01부터 순차, 2자리 zero-padded)
- 유형: `unit` / `integration` / `e2e`
- 설명: 1줄 요약

### 4-3. 시나리오 상세 규칙

- **출처**: 해당 시나리오를 도출한 AC 또는 EC ID
- **GIVEN/WHEN/THEN**: AC의 GIVEN/WHEN/THEN을 구체화하되, 테스트 입력/출력 수준으로 상세화
- **테스트 케이스**: 최소 정상 + 예외 케이스. 경계값은 해당 시
- **검증 방법**: 자동 테스트 도구 (Jest, Pytest, Playwright 등) 또는 수동 검증
- **매핑**: 초기에는 `태스크 미할당`. TASKS 단계(op-sdd-tasks)에서 태스크 ID가 할당됨

### 4-4. 상태 값

| 상태 | 의미 | 전이 시점 |
|------|------|----------|
| Red | 시나리오 정의됨, 테스트 미작성 (TDD Red) | SPEC-VERIFY 완료 시 |
| Green | 테스트 작성 + 통과 | EXECUTE-LOOP 태스크 완료 시 |
| Fail | 테스트 작성 + 실패 | 검증 루프에서 실패 |
| Skip | 의도적 제외 (사유 명시) | PM/소유자 판단 |

**상태 전이**:
```
Red  ->  Green  (태스크 구현 + 테스트 통과)
Red  ->  Fail   (태스크 구현 + 테스트 실패)
Fail ->  Green  (검증 루프에서 수정 후 통과)
Red  ->  Skip   (PM/소유자 판단으로 제외)
```

---

## 5. 판정 기준 상세

### 5-1. SPEC 검증 (mode=spec) 판정

| 판정 | 조건 | 후속 조치 |
|------|------|----------|
| **Pass** | 모든 항목 Pass (Warning 0개) | Phase 3(SPEC-PLAN) 진행 |
| **Pass with Warnings** | Fail 0개 + Warning 1~2개 | Phase 3 진행 가능, Warning을 VERIFY.md에 기록 |
| **Fail** | Fail 1개 이상, 또는 Warning 3개 이상 | 재작성 지시 -> op-sdd-spec에 피드백 |

### 5-2. TASKS 검증 (mode=tasks) 판정

| 판정 | 조건 | 후속 조치 |
|------|------|----------|
| **Pass** | 모든 Fail 항목 0개 | Phase 6(EXECUTE-LOOP) 진행 |
| **Fail** | Fail 1개 이상 | 재작성 지시 -> op-sdd-tasks에 피드백 |

TASKS 검증에서는 "Pass with Warnings" 판정이 없다. 커버리지 갭이나 의존관계 문제는 구현 단계에서 큰 비용을 발생시키므로 Warning도 Fail로 분류하여 사전에 해소한다.

### 5-3. Fail 시 재작성 지시 형식

검증이 Fail로 판정되면 원본 작성 스킬(op-sdd-spec 또는 op-sdd-tasks)에 재작성을 지시한다.

```markdown
## 재작성 지시

판정: Fail
사유: {Fail 항목 요약}

### 수정 필요 항목
| # | 항목 | 현재 상태 | 수정 방향 |
|---|------|----------|----------|
| 1 | {검증 항목 ID + 이름} | {문제 설명} | {구체적 수정 지침} |
| 2 | {검증 항목 ID + 이름} | {문제 설명} | {구체적 수정 지침} |

### 우선순위
1. {가장 중요한 수정 -- Fail 항목 우선}
2. {다음 수정}
3. {Warning 항목 -- 함께 수정 권장}
```

**재작성 지시 규칙**:
- `수정 방향`은 추상적이지 않고 구체적으로 작성한다
- 어떤 섹션을 어떻게 변경해야 하는지 명확히 제시한다
- 가능하면 예시를 포함한다

---

## 6. SPEC 검증에서 테스트 시나리오 도출

SPEC-VERIFY의 핵심 산출물 중 하나가 TEST-SCENARIOS.md이다. 이것이 TDD의 "Red" 단계에 해당한다.

### 6-1. 도출 프로세스

1. SPEC.md의 모든 AC를 순회한다
2. 각 AC의 GIVEN/WHEN/THEN을 테스트 케이스로 변환한다:
   - **정상 케이스**: GIVEN + WHEN -> THEN 그대로
   - **예외 케이스**: GIVEN 변형 (전제 위반) -> 에러 기대
   - **경계값 케이스**: WHEN 변형 (경계 입력) -> 동작 기대
3. Edge Cases(EC) 항목에서 추가 시나리오를 도출한다
4. 유형을 분류한다:
   - `unit`: 단일 함수/컴포넌트 검증
   - `integration`: 복수 컴포넌트/API 통합 검증
   - `e2e`: 사용자 시나리오 전체 흐름 검증

### 6-2. 도출 기준

| 기준 | 요구 사항 |
|------|----------|
| AC 커버리지 | 모든 AC에서 최소 1개 시나리오 |
| EC 커버리지 | 모든 EC에서 최소 1개 시나리오 |
| 케이스 다양성 | 정상 + 예외 + 경계값 |
| 유형 균형 | unit 편향 금지 -- integration/e2e도 포함 (해당 시) |

### 6-3. 도출 불가 AC 처리

AC에서 테스트 시나리오를 도출할 수 없으면 AC 자체의 품질 문제이다:
- AC가 너무 모호하여 테스트로 변환할 수 없음 -> **AC 재작성 권고** (Fail 피드백)
- AC가 검증 불가능한 내용 -> **AC 재작성 또는 NFR 이관 권고**

---

## 7. TASKS 검증 상세

### 7-1. 커버리지 검증

| # | 항목 | 상세 |
|---|------|------|
| T-1 | AC 커버리지 | SPEC.md의 **모든** AC가 TASKS.md의 최소 1개 태스크에 매핑. 빈틈 = 구현 누락 |
| T-2 | 역매핑 완전성 | TASKS.md의 **모든** 태스크가 최소 1개 AC에 매핑. 매핑 없는 태스크 = 불필요 태스크 |
| T-3 | TS 커버리지 | TEST-SCENARIOS.md의 **모든** 시나리오가 최소 1개 태스크에 할당. 미할당 TS = 테스트 누락 |
| T-4 | 테스트 유형 균형 | unit만 있고 integration/e2e가 없으면 Warning |

### 7-2. 의존관계 검증

| # | 항목 | 상세 |
|---|------|------|
| T-5 | 순환 의존 | DAG(방향 비순환 그래프)인지 확인. 순환 발견 시 Fail |
| T-6 | 누락 의존 | 의존 대상 태스크가 TASKS.md에 실제 존재하는지 확인 |
| T-7 | 불필요 의존 | 실제로는 의존 관계가 없는데 의존 선언한 경우 Warning (병렬성 저해) |

### 7-3. 자기 완결성 검증

| # | 항목 | 상세 |
|---|------|------|
| T-8 | 독립 완료 가능 | 의존 태스크 완료 후 해당 태스크만으로 완결 가능한지. 외부 의존이 암묵적이면 Fail |
| T-9 | 입출력 명확 | 각 태스크의 입력(의존 산출물)과 출력(생성 파일/코드)이 명시적인지 |

### 7-4. 크기 적정성 검증

| # | 항목 | 상세 |
|---|------|------|
| T-10 | 과대 태스크 | 단일 태스크가 AC 3개 이상을 커버하면 Warning (분할 권장) |
| T-11 | 과소 태스크 | 의미 있는 단위가 아닌 지나치게 세분화된 태스크. 예: "import 추가" 수준 |

---

## 관련 문서

- `op-sdd-verify/SKILL.md` -- 검증 스킬 프로세스 (mode=spec/tasks)
- `spec-guide.md` -- SPEC.md 작성 가이드 (검증 대상)
- `spec-plan-guide.md` -- SPEC-PLAN.md 작성 가이드 (TASKS-VERIFY 참조)
- `execute-loop-guide.md` -- EXECUTE-LOOP 검증 루프 (L1-L3b)
- `~/.opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` -- oppd 검증 루프 원본
