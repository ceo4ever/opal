# CONTRACT 작성·거버넌스 가이드

> opal-pilot-project-loop(oppl) Loop 1 D4(CONTRACT 산출) + Loop 1 D6/태스크 파이프라인 G 게이트에서 CONTRACT.md를 다루는 방법.
> SKILL.md `## CONTRACT 거버넌스` 절에서 인라인 참조한다.
> 근거: `tasks/056-260710-opd-oppl-루프-오케스트레이터/SPEC.html` §04 "검증 3-tier + 기준 항목", §05 "CONTRACT 거버넌스".

---

## 1. 개요

**CONTRACT.md는 oppl의 1급(first-class) 산출물**이다 — PRD/TRD와 동렬로 Loop 1 D4 단계에서 생성되고, `docs/` 승격 대상이며, 실행 루프의 매 태스크에서 검증 기준으로 재참조되는 "살아있는 문서"다 (SPEC §05). CONTRACT.md 없이는 G 게이트(명세 리뷰)와 Evaluator 판정이 기준을 잃으므로, Loop 1이 종료(D7 사용자 확정 게이트)되기 전까지 필수 확정 요소 중 하나다.

**책임 3분할**: 작성 = Planner, 리뷰 = Evaluator, 반영·확정 = PM. 세 역할은 서로 겹치지 않는다 — "평가자 ≠ 생성자" 헌법(SPEC §04 "평가자 ≠ 생성자" 원칙)을 CONTRACT.md에도 그대로 적용한 결과다.

---

## 2. CONTRACT.md 구조 (스키마·시그니처·경계 + 기계검증절 + 루브릭절)

CONTRACT.md는 **인터페이스 계약**을 기술한다 — "무엇을 만들지"가 아니라 "경계에서 무엇이 오가는지"를 확정한다. 최소 아래 3파트 + 2절을 포함한다.

### 2.1 계약 본문 3파트

| 파트 | 내용 |
|------|------|
| 스키마 (Schema) | 입출력 데이터 구조 — 필드·타입·필수/선택·enum·기본값 |
| 시그니처 (Signature) | 함수/API/CLI 서브명령의 호출 형태 — 파라미터·반환값·에러 형태 |
| 경계 (Boundary) | 모듈/서비스 간 책임 분리선 — 누가 무엇을 소유하는지, 어디까지가 이 계약의 관할인지 |

### 2.2 기계검증절 (Machine-Verifiable Section)

계약 중 **결정론적으로(코드로) 검증 가능한 항목**을 모아 별도 절로 명시한다. 이 절의 항목은 test-tool의 계약 conformance 테스트(스키마 일치·시그니처 일치)로 T4a에서 자동 검증된다 (SPEC §04 결정론 표 "계약 conformance" 행). Evaluator는 이 절을 판정하지 않는다 — 기계검증절은 test-agent/checker 소관이다.

### 2.3 루브릭절 (Rubric Section)

기계로 판정할 수 없는 **주관적 품질 기준**(완전성·일관성·설계 정합 등)을 앵커된 척도로 명시한다. Evaluator가 G 게이트·D6에서 판정하는 기준 원천이 바로 이 절이다.

- CONTRACT.md에 루브릭절이 있으면 Evaluator는 **그 루브릭절을 우선 기준**으로 판정한다.
- CONTRACT.md가 아직 없거나 루브릭절이 비어 있으면 Evaluator는 SPEC §04 Base 루브릭(계약 완전성·계약 일관성·설계 정합·drift 필요성·컨벤션 정신·아키텍처 적합, Likert 1–5, 통과선 ≥4)만으로 판정하고 그 사실을 보고서에 명시한다 — `opal/agents/opal-convention-checker`가 CONVENTIONS.md를 기준 문서로 읽는 패턴과 동일하다 (SPEC §06 "CONTRACT.md 루브릭절 (convention-checker가 CONVENTIONS.md 읽듯)").

---

## 3. 작성 · 리뷰 · 반영 (역할 분리)

| 역할 | 담당 | 시점 | 산출/처리 |
|------|------|------|----------|
| 작성 | Planner (planning-agent · plan-agent) | Loop 1 D4 (TRD 확정 후) | CONTRACT.md 초안 — 3파트 + 기계검증절 + 루브릭절 |
| 리뷰 | Evaluator (opal-evaluator-agent) | Loop 1 D6, 태스크 파이프라인 G 게이트, drift 재콜백 | 루브릭절 기준 판정 verdict — `{item, result, reason, suggestion}` |
| 반영·확정 | PM (오케스트레이터) | D6 verdict 수신 후 / G 게이트 통과 후 | verdict를 CONTRACT.md 갱신에 반영, 또는 §4 거버넌스에 따라 처리 주체에 위임 |

Evaluator는 verdict만 산출하며 **CONTRACT.md를 직접 수정하지 않는다** (readonly·mutate 금지 — `opal/agents/opal-evaluator-agent/AGENT.md` 행동 규칙). CONTRACT.md 반영은 항상 PM 또는 §4 거버넌스가 지정한 처리 주체(통합 게이트/사용자)를 통과한다.

---

## 4. 변경 거버넌스 — 오너십 계층 4단계

CONTRACT.md는 실행 루프 중에도 변경될 수 있다(drift). 변경의 **성격**에 따라 판단 주체와 처리 방식이 다르며, 아래 4단계 오너십 계층을 그대로 적용한다 (SPEC §05 "계약 변경 거버넌스" 표).

| # | 변경 성격 | 판단 주체 | 처리 |
|---|----------|----------|------|
| 1 | 무변경 (내부 구현만) | PM 자율 | 그대로 진행 — 계약 갱신 불필요 |
| 2 | 내부 조정 (경계 불변) | PM 자율 | 통합 슬라이스에서 재검증 |
| 3 | 인터페이스 변경 (타 슬라이스 영향) | 통합 게이트 | 영향 슬라이스 재검증(회귀) |
| 4 | 외부 노출·사양 변경 | 사용자 | TRD/PRD 게이트 연동 |

**판단 절차**:

1. 태스크 T3 구현 또는 T4a 테스트 중 계약과의 불일치가 발견되면 **drift 여부**를 먼저 판정한다 — Evaluator가 drift binary(yes/no)로 재콜백 판정한다 (SPEC §04 루브릭 표 "drift 필요성" 행; SPEC §03 note "구현/테스트 중 계약 drift 발견 시에만 Evaluator 재콜백").
2. drift=no면 §7 오류 처리(loop-control.md §7)의 복구가능 경로로 처리하고 계약은 불변.
3. drift=yes면 위 표에서 변경 성격을 4단계 중 하나로 분류한다.
4. 오너십 계층 #1·#2(PM 자율)는 PM이 즉시 CONTRACT.md를 갱신하고 실행 루프를 계속한다.
5. #3(통합 게이트)은 영향받는 모든 슬라이스의 재검증(회귀 테스트 포함)을 완료할 때까지 해당 태스크를 완료 처리하지 않는다.
6. #4(사용자)는 loop-control.md §9 "사람 게이트" 대상 행동이다 — TRD/PRD 게이트와 연동해 사용자 승인 없이 진행하지 않는다.

> **판단 기준의 원칙**: "타 슬라이스에 영향을 주는가"가 #2와 #3의 분기선이고, "프로젝트 경계 밖(외부 API·사용자 노출 사양)으로 나가는가"가 #3과 #4의 분기선이다. 애매한 경우 상위 계층(더 보수적인 판단 주체)으로 승격한다.

---

## 5. 태스크 파이프라인에서의 재참조

- G 게이트(구현 전)에서 Evaluator는 test-scenario.json·PLAN.md·USER_FLOW.md*가 CONTRACT.md의 스키마·시그니처·경계를 위반하지 않는지 먼저 확인한다.
- T4a(구현 후) test-agent는 기계검증절 기준으로 계약 conformance 테스트를 실행한다.
- T4a 통과 후에도 drift가 감지되면(§4 절차) Evaluator를 재콜백한다 — 이것이 검증 2원화에서 유일하게 순서를 역행하는(구현 후 → Evaluator) 예외 경로다 (`verification.md` §3 참조).

---

## 관련 문서

- `opal/skills/opal-pilot-project-loop/SKILL.md` — 본 가이드를 인라인 참조하는 오케스트레이터 본문 (`## CONTRACT 거버넌스` 절)
- `verification.md` — 검증 2원화(Evaluator 구현 전 / test-agent 구현 후) 및 drift 재콜백 예외
- `loop-control.md` §7, §9 — drift 판정 후 에러 처리·사람 게이트 연결
- `opal/agents/opal-evaluator-agent/AGENT.md` — 루브릭절 판정 실행 주체, verdict-only 행동 규칙
- `opal/agents/opal-convention-checker/AGENT.md` — "전담 에이전트 + 외부 기준 문서" 패턴 선례

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-10 16:33 | 초기 작성 — CONTRACT.md 1급 산출물 구조(스키마·시그니처·경계+기계검증절+루브릭절), 작성/리뷰/반영 역할 분리, 변경 거버넌스 오너십 4계층 정의 (056) |
