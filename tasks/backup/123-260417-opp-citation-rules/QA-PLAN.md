---
@header
module: tasks/123-260417-opp-citation-rules
layer: qa
description: QA-PLAN — PLAN.md 품질 검증 리포트
---

# QA: PLAN — 산출물 인용 위치 추적 하네스 (Citation Rules)

> 검토일: 2026-04-17 | 판정: Pass

---

## 1. 요약

PLAN.md는 6개 스킬 파일 수정 + 신규 하네스 모듈 1개 작성으로 구성된 8-Step 계획이다.
Phase 1(Step 1→2 순차)에서 citation-rules.md SSOT를 먼저 확립하고, Phase 2(Step 3~8 병렬)에서 스킬/가이드를 일제히 갱신하는 구조로 의존성이 명확하다.
인용 포맷 3종(문서/코드/MUST)과 단계별 의무 수준 매트릭스(TASK/ANALYSIS/PLAN × 테이블/인라인/MUST)가 §2에서 구체적으로 설계되었다.
TASK.md R-1~R-6 전 요구사항이 Step 1~8과 QA 체크리스트에 매핑되어 있다.
install-mac.sh의 `cp -Rf opal/core/references/. ~/.opal/references/` 구조에 의해 신규 `harness/citation-rules.md`는 자동 배포된다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | 각 Step에 파일 경로, 작업 내용, 완료 기준, 테스트 방법, 의존 관계가 모두 기재됨 |
| GP-2 | 의존성 순서 | Pass | Step 1(citation-rules.md) → Step 2(harness 등록) → Step 3~8(병렬)의 순차·병렬 구간이 명확히 분리됨 |
| GP-3 | TASK 반영 | Pass | R-1~R-6 전항목이 N-1, M-1~M-7과 1:1 매핑됨. §4 QA 체크리스트에서도 R-N 태그로 재확인 |
| GP-4 | 파일 목록 완전성 | Pass | TASK.md 관련 문서 7개 + plan-guide 2개 = 9개 파일 모두 §3.1에 신규/수정/삭제로 분류됨 |
| GP-5 | 설계 구체성 | Pass | §3.3에서 파일별 변경 위치(줄번호)·변경 전/후 형식·근거 문서 인용 포함 |
| GP-6 | 체크리스트 커버리지 | Pass | 8개 Step이 R-1~R-6 전부를 커버. QA §5에 기능/일관성/문서 품질 3구간 체크리스트 완비 |
| FCS-1 | 인용 포맷 3종 설계 명확성 | Pass | §2.1 문서 근거, §2.2 코드 근거, §2.3 MUST 포맷이 각각 포맷 + 예시로 구분 정의됨 |
| FCS-2 | 단계별 의무 매트릭스 완전성 | Pass | TASK/ANALYSIS/PLAN × 참조 문서 테이블/인라인 인용/MUST 포맷 3×3 테이블이 §2.3에 완비 |
| FCS-3 | install-mac.sh 배포 경로 정합성 | Pass | `opal/core/references/harness/` → `~/.opal/references/harness/` 자동 복사 확인 (scripts/install-mac.sh:635) |
| FCS-4 | Phase 2 병렬 Step 독립성 | Pass | Step 3~8은 서로 다른 파일(op-task, op-dev-analysis, op-dev-plan×2, op-task-plan×2) — 공유 리소스 없음. citation-rules.md/opal-harness.md는 읽기 전용 참조만 |
| FCS-5 | R-3 AC ↔ PLAN 테이블 컬럼 일치 | Warning | TASK.md R-3 AC: "문서명/경로/섹션/인용 내용 컬럼" 요구. PLAN M-2: `# \| 문서 \| 경로 \| 참조 이유` 4컬럼 채택 — "섹션"과 "인용 내용" 컬럼이 없음 |
| FCS-6 | R-2 AC "적용 주체" 테이블 반영 | Info | R-2 AC "로드 조건/적용 주체/적용 시점" 요구. 하네스 테이블 스키마(`모듈\|파일\|로드 시점\|해당 §`)에 "적용 주체" 컬럼이 없으나, §2.4에서 "로드 주체: 워커"로 산문 명시됨. 기존 스키마 한계로 간주 |

---

## 3. 지적 사항

### FCS-5 — Warning: R-3 AC와 PLAN 테이블 컬럼 불일치

**심각도**: Warning

**TASK.md R-3 AC 원문**:
> "TASK.md 템플릿에 문서명/경로/섹션/인용 내용 컬럼이 있는 테이블 구조가 포함되어 있다"

**PLAN.md M-2 채택 컬럼**: `# | 문서 | 경로 | 참조 이유`

**불일치 항목**:
- TASK AC에서 요구한 "섹션" 컬럼이 PLAN 설계에 없음
- TASK AC에서 요구한 "인용 내용" 컬럼이 PLAN 설계에 없음 ("참조 이유"로 대체됨)

**평가**: TASK.md 작성 시점에서 "섹션"과 "인용 내용"이 명시된 이유는 초기 설계 아이디어였고, PLAN 단계에서 `# | 문서 | 경로 | 참조 이유` 4컬럼으로 의도적으로 단순화한 것으로 보인다. 단, PLAN.md에 이 결정의 근거(섹션과 인용 내용을 별도 컬럼으로 두지 않은 이유)가 명시되어 있지 않아 추적 불가. 실행에는 지장 없으나 R-3 AC 완전 충족 여부가 불명확함.

**권장 조치**: PLAN §3.3 M-2 하단 또는 §2.2 설계 결정에 "섹션/인용 내용 대신 참조 이유 컬럼으로 통합한 근거" 1줄 추가.

---

### FCS-6 — Info: R-2 AC "적용 주체" 테이블 미반영

**심각도**: Info

하네스 §2 테이블 스키마가 `모듈 | 파일 | 로드 시점 | 해당 §`로 고정되어 있어 "적용 주체" 컬럼을 별도 추가하기 어려운 구조적 한계. §2.4에서 산문 명시가 되어 있으므로 실용적으로 충족됨.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1 | citation-rules.md 신규 생성 + §1~§6 구조 + 인용 포맷/의무 수준/탐색 가이드 AC → PLAN Step 1 완료 기준에 그대로 반영 | Pass |
| TASK.md R-2 | opal-harness.md §2 모듈 테이블 citation-rules 행 추가 AC → PLAN Step 2에 행 내용(`인용 규칙 \| \`harness/citation-rules.md\` \| TASK/ANALYSIS/PLAN 산출물 작성 시 \| §2`)까지 명시 | Pass |
| TASK.md R-3 | op-task TASK.md 관련 문서 섹션 테이블화 → PLAN M-2 반영. AC 컬럼 불일치는 FCS-5 Warning으로 처리 | Warning |
| TASK.md R-4 | op-dev-analysis ANALYSIS.md 인용 필드 추가 AC → PLAN M-3: §0 참조 문서 테이블 + §1.1/§5 근거 컬럼 확장 반영 | Pass |
| TASK.md R-5 | op-dev-plan SKILL.md §3 인라인 + §8 참조 테이블 + plan-guide 3단계 지시 추가 AC → PLAN M-4, M-5 반영 | Pass |
| TASK.md R-6 | op-task-plan PLAN.md 인용 구조 적용 → PLAN M-6 반영. R-6 AC는 SKILL.md만 언급하나 PLAN은 plan-guide(M-7)도 포함하여 초과 달성 | Pass |
| TASK.md 제약 #1 | `~/.opal/` 직접 수정 금지 → PLAN 전체 수정 대상이 `opal/core/` 및 `opal/skills/`에 한정됨 | Pass |
| TASK.md 제약 #2 | 레거시 소급 변경 불필요 → PLAN §6 리스크 및 citation-rules.md §5 예외 규칙에 명시 예정 | Pass |
| TASK.md 미확정 사항 | 인용 형식 설계(인라인 vs 테이블 vs 혼합) → PLAN §2.1~§2.3에서 혼합 방식으로 확정. 단계별 의무 수준 → §2.3 매트릭스로 확정 | Pass |

---

## 5. 판정

**Pass**

PLAN.md는 TASK.md R-1~R-6을 모두 커버하며, 의존성 순서(Phase 1→2)와 병렬 독립성(Step 3~8)이 명확하다. FCS-5(Warning 1개) — R-3 AC 컬럼 불일치 — 는 설계 단순화 결정으로 보이나 근거 기재가 누락된 경미한 수준이다. 실행 진행에 지장 없음.
