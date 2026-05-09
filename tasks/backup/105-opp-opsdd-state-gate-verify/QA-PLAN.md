# QA-PLAN: opsdd STATE Gate 완성 + VERIFY Phase 추가

> 작성일: 2026-04-09 | 태스크: 105-opp-opsdd-state-gate-verify
> QA 대상: `tasks/105-opp-opsdd-state-gate-verify/PLAN.md`

---

## QA 결과 요약

| 항목 | 결과 | 비고 |
|------|------|------|
| §3 실행 체크리스트 R-1~R-5 커버 여부 | ✅ Pass | 5개 요구사항 모두 커버 |
| §2 구현 전략 의존 순서 논리성 | ⚠️ 이슈 1건 | SPEC/DESIGN 게이트 순서 오류 |
| §4 QA 체크리스트 충분성 | ✅ Pass | 단, PM 발견 이슈 항목 추가 필요 |
| 제약 조건 반영 (~/.opal/ 직접 수정 금지) | ✅ Pass | §4-5 마지막 항목에 명시됨 |
| §5 주의사항 실질적 리스크 식별 | ✅ Pass | 5개 리스크 항목 식별됨 |

---

## 세부 검증 결과

### QA-1. §3 실행 체크리스트 R-1~R-5 커버 여부

| 요구사항 | 대응 Step | 커버 여부 |
|---------|----------|---------|
| R-1: STATE.md 도메인 치환값 교체 | Step 3 | ✅ 커버 (진행 현황 24행, ACT 목록, TS 현황, SPEC 변경이력 포함) |
| R-2: VERIFY Phase 신설 | Step 4 | ✅ 커버 (YAML 업데이트, Phase 5 신설, Phase 6 DONE 이동 포함) |
| R-3: L1/L2 검증 루프 명시 | Step 1 + Step 4 | ✅ 커버 (execute-loop-guide.md ACT 목록 테이블 + SKILL.md Phase 4) |
| R-4: ACT 상태 필드 금지 원칙 | Step 2 | ✅ 커버 (spec-plan-guide.md 금지 원칙 추가) |
| R-5: harness.md §3 opsdd 예시 추가 | Step 5 | ✅ 커버 (opsdd 24행 진행 현황 행 예시 추가) |

**판정**: Pass

---

### QA-2. §2 구현 전략 논리성 및 의존 순서

#### 2-1. 적용 순서 (§2-1) — 의존 관계 논리성

```
Step 1: execute-loop-guide.md (R-3 부분)
  → Step 2: spec-plan-guide.md (R-4)
    → Step 3: SKILL.md R-1 STATE.md 치환값
      → Step 4: SKILL.md R-2 VERIFY Phase + R-3 L1/L2
        → Step 5: opal-harness.md (R-5)
```

- **Step 1 → 2**: execute-loop-guide.md의 ACT 목록 SSOT 구조 확정 후 spec-plan-guide.md에서 참조 — 논리적
- **Step 1,2 → 3**: ACT 관련 문서 정비 완료 후 SKILL.md STATE.md 치환값에서 컬럼 명세 — 논리적
- **Step 3 → 4**: STATE.md 진행 현황 행 구조 확정 후 VERIFY Phase 신설 — 논리적
- **Step 4 → 5**: SKILL.md 완성 후 harness.md 예시 작성 — 논리적

**판정**: ✅ 의존 순서 올바름

#### 2-2. 각 요구사항별 접근 방법 (§2-2) — 이슈 발견

**이슈: SPEC/DESIGN 단계 진행 현황 행의 Gate 순서 오류**

PLAN.md §2.2 R-1에서 SPEC 5행 구성을 다음과 같이 기술:
```
SPEC (5행): 작업 / SPEC.md 생성 / PM Gate / State Gate / 사용자 확인
```

그러나 TASK.md의 진행 현황 테이블 (R-1 요구사항의 정식 명세) 에서 SPEC 행은:
```
행 4: 워커 디스패치
행 5: SPEC.md 생성
행 6: State Gate   ← State Gate 먼저
행 7: PM Gate      ← PM Gate 나중
행 8: 사용자 확인
```

SKILL.md Phase 1 SPEC 섹션의 Gate 순서도 동일하게 `State Gate → PM Gate` 순서임:
> "→ **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인) → **PM Gate** → 사용자 Gate"

DESIGN 5행도 동일한 오류:
```
PLAN.md 기술: DESIGN (5행): 작업 / SPEC-PLAN.md 생성 / PM Gate / State Gate / 사용자 확인
TASK.md 정식 명세: 행 15 State Gate → 행 16 PM Gate
```

**PM이 사전 발견한 이슈와 일치**: §2.2의 SPEC 5행 설명 "PM Gate / State Gate"는 올바른 순서인 "State Gate / PM Gate"로 수정되어야 함.

**영향**: PLAN.md의 §2.2 기술이 실제 구현 시 SKILL.md에 잘못된 순서로 반영될 위험이 있음. §3 Step 3 체크리스트에도 Gate 순서 확인 항목이 없어 구현 오류가 QA 단계 전까지 발견되지 않을 수 있음.

**권고**: §2.2 R-1 SPEC/DESIGN 행 설명에서 "PM Gate / State Gate" → "State Gate / PM Gate"로 수정 필요.

**판정**: ⚠️ 이슈 — 기술 오류 수정 필요

---

### QA-3. §4 QA 체크리스트 충분성

| 항목 | 평가 |
|------|------|
| 4-1 STATE Gate 완성 검증 | ✅ 24행 구성, 단계별 Gate 구조 등 충분히 포함 |
| 4-2 ACT 목록 SSOT 검증 | ✅ execute-loop-guide.md 컬럼 일치, spec-plan-guide.md 금지 원칙 포함 |
| 4-3 VERIFY Phase 검증 | ✅ 다이어그램, YAML, 섹션 신설, Gate 순서 포함 |
| 4-4 L1/L2 검증 루프 검증 | ✅ ACT 목록 컬럼, SKILL.md Phase 4 명시, 재시도 규칙 포함 |
| 4-5 일관성 검증 | ✅ 6단계 일관성, agentic 모드, harness.md 일치 포함 |
| 4-6 변경이력 검증 | ✅ 4개 파일 변경이력 추가 포함 |

**누락 항목 식별**:

- §4-1에 **SPEC/DESIGN 단계 Gate 순서 확인** 항목이 없음. PM이 사전 발견한 이슈(§2.2 Gate 순서 오류)를 QA 체크리스트에서도 검증해야 함.
  - 추가 권고 항목: "SPEC/DESIGN 단계 진행 현황 행의 Gate 순서가 'State Gate → PM Gate'이다 (PM Gate가 State Gate보다 나중)"
- §4-3 VERIFY Phase Gate 순서 항목이 이미 포함되어 있어 VERIFY에 대해서는 검증 가능

**판정**: ✅ Pass (단, §4-1에 Gate 순서 항목 추가 권고)

---

### QA-4. 제약 조건 반영 (~/.opal/ 직접 수정 금지)

- §4-5 마지막 항목: "소스 경로(`opal/skills/`, `opal/core/`)만 수정되고 `~/.opal/` 직접 수정이 없다" ✅
- §5에 이 제약을 별도 언급하지는 않으나, §4-5에서 QA 항목으로 포함되어 있음 ✅
- §3 실행 체크리스트의 수정 대상 파일이 모두 `opal/` 하위 소스 경로임 ✅

**판정**: ✅ Pass

---

### QA-5. §5 주의 사항 실질적 리스크 식별

| 주의사항 | 리스크 실질성 평가 |
|---------|----------------|
| 5-1: 106 태스크와의 충돌 | ✅ 실질적 — SKILL.md 동시 수정 충돌 가능성 명시 |
| 5-2: EXECUTE 단계 진행 현황 행 설계 | ✅ 실질적 — ACT 동적 생성과 고정 행 구조 간 설계 결정 명시 |
| 5-3: SPEC/DESIGN의 QA Gate 없는 State Gate 구조 | ✅ 실질적 — interactive 하네스와의 차이 명시 |
| 5-4: REVIEW 단계 Gate 구조 | ✅ 실질적 — PM 직접 수행으로 Gate 최소화 설계 결정 명시 |
| 5-5: spec-plan-guide.md §8 존재 여부 | ✅ 실질적 — 실제 파일 확인 후 위치 결정 필요성 명시 |

**판정**: ✅ Pass

---

## 발견된 이슈 목록

| # | 위치 | 이슈 유형 | 내용 | 심각도 |
|---|------|---------|------|-------|
| I-1 | §2.2 R-1 SPEC 행 설명 | 기술 오류 | "PM Gate / State Gate" → 올바른 순서는 "State Gate / PM Gate" | 높음 |
| I-2 | §2.2 R-1 DESIGN 행 설명 | 기술 오류 | 동일 — DESIGN 5행도 PM Gate와 State Gate 순서 반전 기술 | 높음 |
| I-3 | §4-1 QA 체크리스트 | 누락 | SPEC/DESIGN 단계 "State Gate → PM Gate" 순서 확인 항목 없음 | 중간 |

---

## 권고사항

1. **[필수] §2.2 R-1 SPEC/DESIGN 행 기술 수정**: "PM Gate / State Gate" → "State Gate / PM Gate"
2. **[권고] §4-1에 Gate 순서 검증 항목 추가**: SPEC/DESIGN 단계가 "State Gate → PM Gate" 순서임을 확인하는 항목

---

## 최종 판정

**PLAN.md QA: ⚠️ 조건부 통과**

- §3 실행 체크리스트 R-1~R-5 완전 커버: ✅
- §2 구현 전략 의존 순서 올바름: ✅
- §4 QA 체크리스트 충분함: ✅ (항목 추가 권고)
- 제약 조건 반영: ✅
- §5 주의사항 실질적: ✅
- §2.2 Gate 순서 기술 오류 (I-1, I-2): ⚠️ 수정 필요

PLAN.md의 §2.2 기술 오류(I-1, I-2)를 수정하고 §4-1에 Gate 순서 검증 항목을 추가한 후 EXECUTE 진입이 권고됨.
