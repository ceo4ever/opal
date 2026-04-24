# QA: PLAN — Citation Rules 하네스 보편화 — SSOT 완성 + Trigger 주입

> 검토일: 2026-04-24 | 판정: Pass

---

## 1. 요약

PLAN.md는 TASK.md R-1~R-8을 모두 Step으로 분해하여 총 20개 Step, 4개 Phase로 구성한다.
citation-rules.md를 SSOT 본체로 완성하는 Step 1을 선행 처리하고, opal-harness.md(Step 2), pilot/스킬/가이드 18개 파일(Step 3~20)을 G1 완료 후 병렬 처리하는 의존 구조가 명확하다.
SSOT+Trigger 원칙(규칙 복제 금지, 단일 공통 템플릿 1줄)이 §2 C-3에 구체적으로 명세되어 있고, 하위호환(기존 §1~§6 구조 보존) 전략이 섹션 번호 충돌 없이 설계되어 있다.
decision_required JSON 스키마에 TASK.md 요구 필드(type/summary/tokens/areas) 전부가 포함되어 있으며, 에스컬레이션 원칙이 opal-harness-agentic.md §6과 정합한다.
Phase 테이블의 G3b/G3c Step 범위 표기(11~16 / 17~20)가 실제 Step 배정(G3b=11~17, G3c=18~20)과 1~2 Step 어긋나는 경미한 표기 오류가 있으나, 각 Step 개별 의존 정보가 완전하므로 실행에 지장 없다.

---

## 2. 검증 결과

### 핵심 검증 포인트 (QP-1 ~ QP-10)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| QP-1 | 요구사항 커버리지 (R-1~R-8) | Pass | R-1~R-5 → Step 1, R-6 → Step 2, R-7 → Step 3~20, R-8 → 각 Step 내포. 1:1 완전 매핑. |
| QP-2 | citation-rules.md 하위호환 보장 | Pass | §2 C-1 서두 "기존 §1~§6 구조 보존, 신설은 §0/§1.5/§2.5/§7로 배치" 명시. Step 1 완료 기준에도 "기존 §1~§6 번호·내용 보존" 명시. 영향 범위 표에도 동일 원칙 반복 선언. |
| QP-3 | SSOT + Trigger 원칙 준수 | Pass | §2 C-3에 단일 공통 템플릿 1줄 제시. QA 일관성 테스트 항목 "규칙 내용 복제 없음" 포함. Step 3~20 모두 "트리거 1줄 + 변경이력"으로 동일 패턴 기술. |
| QP-4 | 수정 대상 파일 누락 없음 | Pass | F-1~F-18 모두 존재 확인 완료. Step 3~20 각각 파일 경로 명시(18개 1:1 매핑). citation-rules.md + opal-harness.md 포함 총 20개 파일 커버. |
| QP-5 | decision_required 스키마 완전성 | Pass | §7.4 JSON 스키마에 type/summary/tokens/areas 모두 포함. source_refs/suggested_resolution 추가 필드는 확장으로 TASK.md R-4 AC와 충돌 없음. |
| QP-6 | 에스컬레이션 원칙 정합성 | Pass | §7.5 [MUST] "결정성 이슈는 agentic 모드에서도 사용자 에스컬레이션 필수, PM이 자율 결정 불가" ↔ opal-harness-agentic.md §6 "판단 모호 시 에스컬레이션 기본, 올려야 할 것을 안 올리는 것도 PM 실패" — 정합. |
| QP-7 | 의존 순서 정합 | Pass | Step 1 의존: "없음". Step 2~20 전부 "의존: Step 1". 완전한 선행 의존 관계. |
| QP-8 | 병렬 그룹 정합 | Warning | Phase 테이블 G3b "Step 11~16 (6개)"로 표기했으나 실제 Step 11~17이 PLAN/TASK/ANALYSIS 파일(7개). G3c "Step 17~20"으로 표기했으나 Step 17(op-dev-analysis)은 G3b 범주, 실제 G3c는 Step 18~20(3개). 각 파일은 단일 Step에만 배정되므로 동일 파일 워커 분산 금지 원칙은 준수. 표기 오류 수준이며 개별 Step 의존 정보가 완전하여 실행 영향 없음. |
| QP-9 | 리스크 대응 충분성 | Pass | §5 리스크 6개 모두 현실적이며 구체 대응(§번호 보존 전략, 단일 템플릿 강제, Lazy/의무 블록 역할 분리, pilot Gate 별도 후속 태스크 명시, 파일 구조 사전 조사 완료, 버전 증분 방법 명시) 포함. |
| QP-10 | TASK.md 체크리스트 갱신 | Pass | PLAN이 R-1~R-8 전부 커버 확인 → TASK.md §7 R-1~R-8 체크박스 전부 [x]로 갱신 완료(본 QA Step 4). |

### 표준 PLAN 검증 기준 (GP-1 ~ GP-6)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | 각 Step에 파일 경로, 작업 내용, 완료 기준, Grep 테스트, 의존 Step이 모두 명시되어 있음. |
| GP-2 | 의존성 순서 | Pass | Step 1(SSOT 본체) 선행, Step 2~20 병렬 처리. 의존 방향 일관. |
| GP-3 | TASK 반영 | Pass | R-1~R-8 전부 PLAN Step에 반영. |
| GP-4 | 파일 목록 완전성 | Pass | 20개 파일(citation-rules + harness + 18개) 전부 수정 대상으로 열거. |
| GP-5 | 설계 구체성 | Pass | §2 C-1에 신설 섹션 내용(§0/§1.5/§2.5/§7), Good/Bad 예시, JSON 스키마까지 완전 명세. |
| GP-6 | 체크리스트 커버리지 | Pass | R-1~R-8이 20개 Step으로 완전 분해. QA 체크리스트(§4)에도 R-1~R-8 + 일관성 + 문서 품질 항목 포함. |

---

## 3. 지적 사항

### Warning

#### W-1 Phase 테이블 G3b/G3c Step 범위 표기 오류 (QP-8)

**심각도**: Warning

**위치**: PLAN.md §3 실행 체크리스트 Phase 테이블 (G3b / G3c 행)

**현상**:
- G3b 행: "Step 11~16, PLAN/TASK/ANALYSIS 스킬 6개"로 표기
- 실제 배정: Step 11(op-dev-plan/SKILL.md), Step 12(plan-guide.md), Step 13(op-task-plan), Step 14(op-sdd-plan), Step 15(op-sdd-action-plan), Step 16(op-task/SKILL.md), Step 17(op-dev-analysis/SKILL.md) = 7개 파일, Step 11~17
- G3c 행: "Step 17~20, QA 스킬 2개 + QA 가이드 1개 + 기타"로 표기
- 실제 G3c 해당: Step 18(op-dev-qa/SKILL.md), Step 19(qa-dev-guide.md), Step 20(op-task-qa/SKILL.md) = 3개, Step 18~20

**영향**: EXECUTE 디스패치 시 오케스트레이터가 Phase 테이블 Step 범위를 보고 그룹을 배정할 경우 혼동 가능. 단, 각 Step 개별 의존 항목("의존: Step 1")이 완전하여 실제 실행 오류로 이어지지 않음.

**권고**: Step 범위를 G3b: 11~17 (7개), G3c: 18~20 (3개)으로 수정 권장. 단, EXECUTE 전 수정 없이도 진행 가능.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md §7 R-1~R-8 | PLAN Step이 각 요구사항을 누락 없이 커버하는가 | Pass |
| TASK.md §8 제약 조건 | 하위호환, SSOT, 복제 금지, 파일 없으면 스킵, 충돌 금지 모두 PLAN에 반영되었는가 | Pass |
| TASK.md §5 로드맵 C-1~C-7 | C-1~C-7 모두 Step에 매핑되는가 | Pass |
| TASK.md §6 병렬 디스패치 전략 (G1~G4) | PLAN §3 Phase 테이블의 병렬 구조가 동일한가 | Pass (표기 오류 제외, 구조 정합) |
| opal-harness-agentic.md §6 | §7.5 에스컬레이션 원칙이 정합하는가 | Pass |
| TASK.md R-4 decision_required 페이로드 | §7.4 JSON 스키마 필드가 요구 필드를 모두 포함하는가 | Pass |

---

## 5. 판정

**Pass**

R-1~R-8 요구사항 커버리지 완전, 하위호환 전략 명확, SSOT+Trigger 원칙 준수, 20개 파일 1:1 Step 매핑, decision_required 스키마 완전, 에스컬레이션 원칙 정합, 의존 순서 정합, 리스크 대응 구체적. Phase 테이블 G3b/G3c Step 범위 표기 오류는 Warning 1건이며 실행에 영향을 주지 않아 진행 가능 판정.
