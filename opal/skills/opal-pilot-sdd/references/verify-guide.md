# REVIEW Phase 가이드

> opal-pilot-sdd Phase 2: REVIEW의 PM 직접 검증 지침.
> PM이 워커 디스패치 없이 직접 SPEC.md를 검증하고 TEST-SCENARIOS.md를 작성할 때 참조한다.
> SKILL.md에서 분리된 상세 내용.

---

## 1. 개요

REVIEW Phase는 SPEC.md를 SSOT(단일 진실 원천)로 확정하는 단계다. PM이 직접 수행하며 워커 디스패치가 없다.

**핵심 원칙**:
- TEST-SCENARIOS.md를 작성하는 행위 자체가 SPEC 검증의 실천적 형태다
- FR이 모호하면 TS를 못 씀 → 즉시 발견
- 경계조건 정의 과정에서 누락 케이스 드러남
- FR 간 모순이 있으면 TS가 충돌 → 즉시 발견

**3단계 흐름**:

```
1. 구조 검증 (PM 직접, 빠르게)       — S-1~S-6 항목 체크
2. TEST-SCENARIOS.md 작성 (PM 직접)  — FR → TS 도출, 의미적/도메인 검증 자연 수행
3. 목표-커버 게이트 (op-scenario-gate) — scenario-coverage-check 결정론 판정 + 독립 evaluator 채점, 미달 시 재작성
```

---

## 2. 구조 검증 체크리스트 (S-1~S-6)

SPEC.md를 Read하여 아래 항목을 체크한다. 규칙 기반이므로 빠르게 수행 가능.

| # | 항목 | 기준 | 실패 시 |
|---|------|------|---------|
| S-1 | 필수 섹션 10개 존재 | Background, Goals, Non-goals, User Stories, Functional Requirements, Acceptance Criteria, Edge Cases, Non-functional Requirements, Constraints, Open Questions | SPEC.md 보완 요청 |
| S-2 | AC 형식 (GIVEN/WHEN/THEN) | 모든 AC가 GIVEN, WHEN, THEN 3요소를 포함 | SPEC.md 보완 요청 |
| S-3 | Open Questions 해소 | OQ 섹션이 "없음" 또는 비어있음 | 소유자 판단 또는 SPEC.md 보완 |
| S-4 | AC 최소 3개 | AC가 3개 이상 정의됨 | SPEC.md 보완 요청 |
| S-5 | FR 번호 체계 | [FR-NN] 형식으로 번호가 부여됨 | Warning — SPEC.md 보완 권고 |
| S-6 | 버전/상태 메타데이터 | 버전, 작성일, 상태가 기재됨 | Warning — SPEC.md 보완 권고 |

**구조 검증 판정**:

| 판정 | 조건 | 후속 조치 |
|------|------|----------|
| Pass | Fail 항목 없음 | TEST-SCENARIOS.md 작성 진행 |
| Pass with Warnings | Fail 0개 + Warning 1~2개 | Warning을 기록하고 TS 작성 진행 |
| Fail | Fail 1개 이상 | op-sdd-spec 워커 재디스패치 → SPEC.md 보완 후 재검증 |

---

## 3. TEST-SCENARIOS.md 작성

### 3-1. 도출 프로세스

1. SPEC.md의 모든 AC를 순회한다.
2. 각 AC의 GIVEN/WHEN/THEN을 테스트 케이스로 변환한다:
   - **정상 케이스**: GIVEN + WHEN → THEN 그대로
   - **예외 케이스**: GIVEN 변형 (전제 위반) → 에러 기대
   - **경계값 케이스**: WHEN 변형 (경계 입력) → 동작 기대
3. Edge Cases(EC) 항목에서 추가 시나리오를 도출한다.
4. 유형을 분류한다:
   - `unit`: 단일 함수/컴포넌트 검증
   - `integration`: 복수 컴포넌트/API 통합 검증
   - `e2e`: 사용자 시나리오 전체 흐름 검증

### 3-2. 도출 기준

| 기준 | 요구 사항 |
|------|----------|
| AC 커버리지 | 모든 AC에서 최소 1개 시나리오 |
| EC 커버리지 | 모든 EC에서 최소 1개 시나리오 |
| 케이스 다양성 | 정상 + 예외 + 경계값 |
| 유형 균형 | unit 편향 금지 — integration/e2e도 포함 (해당 시) |

### 3-3. 도출 불가 AC 처리

AC에서 테스트 시나리오를 도출할 수 없으면 AC 자체의 품질 문제다:
- AC가 너무 모호하여 테스트로 변환할 수 없음 → **AC 재작성 (SPEC.md 보완)**
- AC가 검증 불가능한 내용 → **AC 재작성 또는 NFR 이관**

### 3-4. TEST-SCENARIOS.md 구조

```markdown
# Test Scenarios: {기능명}

> 버전: 1.0 | 작성일: YYYY-MM-DD | SPEC.md v{X.Y} 기준
> 상태: Red (TDD — 시나리오만 정의, 구현 전)

## 추적 매트릭스

| AC | 시나리오 ID | 유형 | 설명 | 상태 |
|----|-----------|------|------|------|
| AC-01 | TS-01 | unit | {시나리오 설명} | Red |
| AC-01 | TS-02 | integration | {시나리오 설명} | Red |
| AC-02 | TS-03 | unit | {시나리오 설명} | Red |
| EC-01 | TS-04 | unit | {엣지 케이스 설명} | Red |

## 시나리오 상세

### TS-01: {시나리오명}

- **출처**: AC-01
- **유형**: unit / integration / e2e
- **GIVEN**: {사전 조건}
- **WHEN**: {행위}
- **THEN**: {기대 결과}
- **테스트 케이스**:
  - 정상: {정상 입력 → 기대 출력}
  - 예외: {예외 입력 → 기대 에러}
  - 경계값: {경계 입력 → 기대 동작}
- **검증 방법**: {자동/수동, 도구}
- **담당 ACT**: 미할당 (DESIGN Phase에서 할당)
- **상태**: Red

### TS-02: {시나리오명}
...
```

### 3-5. 시나리오 ID 규칙

- 시나리오 ID: `TS-NN` (01부터 순차, 2자리 zero-padded)
- 유형: `unit` / `integration` / `e2e`
- 상태: 초기값 `Red` (TDD Red 단계)

### 3-6. 상태 값

| 상태 | 의미 | 전이 시점 |
|------|------|----------|
| Red | 시나리오 정의됨, 테스트 미작성 | REVIEW Phase 완료 시 |
| Green | 테스트 작성 + 통과 | EXECUTE-LOOP ACT 완료 시 |
| Fail | 테스트 작성 + 실패 | ACT 검증 루프에서 실패 |
| Skip | 의도적 제외 (사유 명시) | PM/소유자 판단 |

---

## 4. 목표-커버 게이트 (scenario-coverage-check + 독립 evaluator)

TEST-SCENARIOS.md 작성 완료 후, 수동 FR↔TS 커버리지 확인 대신 op-scenario-gate(pilot: opsdd)를 호출한다. 커버리지 판정은 test-tool `scenario-coverage-check`가 결정론으로 수행한다:

- `requirements`(SPEC FR) / `features`(SPEC AC) / `hypotheses`(SPEC EC) ↔ 시나리오 매핑 누락을 exit 0(전커버)/16(coverage_unmet)로 판정 — 기존 §4-2 커버리지 기준(AC/FR/EC 100%)과 동형이나 도구 집행.
- exit 16이면 `detail.missing`을 gaps로 반영해 TEST-SCENARIOS.md 재작성 또는 SPEC.md 보완 후 재호출.
- 목표 달성 관점(①⑤⑥)은 opal-evaluator-agent가 별도 채점(수동 확인이 놓치던 관점 편향 보강, `scenario-gate.md` §1 070 사건 근거).

규칙 SSOT: `opal/core/references/harness/scenario-gate.md`.

---

## 5. REVIEW Phase 완료 판정

| 판정 | 조건 | 후속 조치 |
|------|------|----------|
| **Pass** | S-1~S-4 모두 Pass + 목표-커버 게이트 verdict:pass(coverage exit 0 AND evaluator pass) | 사용자 Gate → Phase 3: DESIGN 진행 |
| **Pass with Warnings** | Fail 없음 + Warning(S-5/S-6) 있음 + 목표-커버 게이트 verdict:pass | Warning을 STATE.md 의사결정 로그에 기록 → 사용자 Gate → Phase 3 진행 |
| **Fail** | S-1~S-4 Fail 1개 이상 또는 목표-커버 게이트 verdict:rewrite/escalate 미해소 | op-sdd-spec 재디스패치 → SPEC.md 보완 → REVIEW 재수행 |

---

## 6. 의미적/도메인 검증 참고 항목

PM이 TS 작성 과정에서 자연스럽게 수행하게 되는 검증. 별도 체크리스트로 수행하지 않아도 되지만, 의심되는 경우 참고한다.

### 의미적 검증 참고

| # | 항목 | 확인 방법 |
|---|------|----------|
| M-1 | Goals ↔ FR ↔ AC 정합 | Goals 목록에서 FR로의 매핑, FR에서 AC로의 매핑을 양방향 추적 |
| M-2 | Non-goals와 Goals 모순 없음 | Goals와 Non-goals의 키워드를 비교하여 충돌 탐지 |
| M-3 | 제약 조건 실현 가능 | Constraints의 각 항목이 FR/AC 달성을 불가능하게 하지 않는지 확인 |
| M-5 | Edge Case 반영 | EC 항목이 AC 또는 FR의 정상 경로에서 벗어난 시나리오를 다루는지 확인 |
| M-6 | NFR 측정 가능성 | NFR 항목에 수치(ms, %, 횟수 등)가 포함되어 있는지 확인 |

### 도메인 검증 참고

| # | 항목 | 확인 방법 |
|---|------|----------|
| D-1 | 아키텍처 정합 | spec의 기능이 기존 아키텍처와 호환 가능한지 (docs/ARCHITECTURE.md 대조) |
| D-2 | 컨벤션 준수 | 네이밍, 구조, 패턴이 CONVENTIONS.md와 일치하는지 |

---

## 관련 문서

- `opal-pilot-sdd/SKILL.md` — opsdd 오케스트레이터 메인 (Phase 2: REVIEW 개요)
- `op-sdd-verify/SKILL.md` — 구조 검증 항목 참조 (S-1~S-6 상세)
- `execute-loop-guide.md` — EXECUTE-LOOP ACT 루프 구조
- `spec-guide.md` — SPEC.md 구조 (REVIEW 검증 대상)

---

## 변경이력

| 버전 | 일자 | 변경 내용 |
|------|------|----------|
| v1.1 | 2026-07-23 | §4 수동 FR↔TS 커버리지 → scenario-coverage-check 게이트 대체, §2 S-1~S-6 존치 (075) |
