# QA: PLAN — Artifact Gate 설계 및 적용

> 검토일: 2026-04-06 | 판정: Pass (Warning 2개)

---

## 1. 요약

QA Gate 완료 후 PM Gate 진입 전에 QA 산출물 파일 존재를 구조적으로 확인하는 **Artifact Gate** 메커니즘을 3개 하네스 파일과 opwt SKILL.md에 적용하는 계획이다. 변경은 §2.5 신설(interactive), §4 항목 추가(agentic), QA 표준 파일명 서브섹션 추가(harness), ANALYSIS/EXECUTE 게이트 수정(opwt) 5개 Step으로 구성된다. 공통화 전략으로 harness에서 표준 파일명을 관리하고 스킬별 오버라이드를 허용한다. 변경 대상 파일 4개 모두 실제 존재 확인됨.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | §2 요구사항별 변경 명세에 파일 경로, 변경 위치, 추가 내용이 코드블록 수준으로 상세 기술되어 있어 즉시 실행 가능 |
| GP-2 | 의존성 순서 | Pass | Step 1(interactive) → Step 2(agentic) → Step 3(harness) → Step 4~5(opwt SKILL.md) 순서는 공통 하네스 먼저, 스킬별 오버라이드 후 순으로 합리적 |
| GP-3 | TASK 반영 | Warning | TASK 요구사항 6개 중 5개 완전 반영. 요구사항 5 AC 불일치 (상세: §3) |
| GP-4 | 파일 목록 완전성 | Pass | 변경 파일 4개 모두 실존 확인. 수정 없는 파일 명시도 포함 |
| GP-5 | 설계 구체성 | Pass | 각 요구사항마다 변경 위치, 추가 내용 마크다운 코드블록, 변경이력 버전 번호까지 명세 |
| GP-6 | 체크리스트 커버리지 | Warning | 실행 체크리스트(§3)와 QA 체크리스트(§4) 분리 구성은 양호. 단, QA 체크리스트 항목이 실행 완료 후 검증용으로 적절하나 EXECUTE 워커가 활용하기 위한 안내 없음 (Info 수준) |

---

## 3. 지적 사항

### [Warning] GP-3: 요구사항 5 AC 불일치

**TASK.md 요구사항 5 AC**:
> "opwt ANALYSIS 게이트 절차에 **'QA Gate → PM Gate → 사용자 확인'** 순서가 명시되어 있다"

**PLAN.md §5 (요구사항 5) 설계 내용**:
> ANALYSIS 단계는 PM이 워커 결과를 직접 취합하는 구조이므로, 외부 QA 에이전트 호출이 아닌 **자가 체크(Self-check)** 방식. 따라서 변경 후 절차는 "**PM Gate(자가 체크) → 사용자 확인**"이며 QA Gate는 없다.

**불일치 내용**: TASK.md AC는 "QA Gate → PM Gate → 사용자 확인"을 명시하지만, PLAN.md는 ANALYSIS 단계 특성상 외부 QA Gate 없이 PM 자가 체크만 추가하는 방향으로 설계했다.

**심각도**: Warning — 설계 근거("다른 스킬 opd 등의 ANALYSIS PM Gate와 일관성")가 §5에 명시되어 있고 합리적이지만, TASK.md AC와 표면적으로 불일치한다. 사용자가 이 차이를 인지하고 의도적 편차로 승인했는지 확인이 필요하다. EXECUTE 단계에서 그대로 구현 시 AC 불충족 상태로 기록될 수 있다.

**권장 조치**: PLAN.md §5 설계 근거 섹션 또는 §6 설계 판단 기록에 "TASK AC는 'QA Gate → PM Gate'를 명시했으나, ANALYSIS 단계는 PM 직접 수행 구조이므로 QA Gate를 생략하고 PM 자가 체크로 대체함 — 사전 PM 분석에서 확정된 방향"이라는 명시적 편차 기록을 추가하면 완전하다.

---

### [Info] GP-6: QA 체크리스트 활용 안내

§4 QA 체크리스트가 존재하나, 이것이 EXECUTE 완료 후 QA 워커가 사용할 기준인지 아니면 PLAN 단계에서 사전 검증용인지 역할이 명시되어 있지 않다. 진행에 영향 없음.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | 6개 요구사항 PLAN 반영 여부 | Warning (요구사항 5 AC 표면적 불일치) |
| TASK.md §확정된 설계 방향 | Artifact Gate 위치(QA 완료 후 PM 진입 전) | Pass — PLAN §2.5 위치와 일치 |
| TASK.md §제약 조건 | ~/.opal/ 직접 수정 금지, opal/core/references/ 및 opal/skills/ 수정 | Pass — PLAN §5 변경 파일 목록이 제약 경로 준수 |
| TASK.md §확정된 설계 방향 §3 | 각 오케스트레이터 SKILL.md 산출물 명세 공통화 또는 인라인 | Pass — harness 공통화 결정이 TASK 허용 범위 내 |

---

## 5. TASK.md 체크리스트 갱신

PLAN.md가 커버하는 요구사항:

- [x] **Artifact Gate 규칙 추가 — opal-harness-interactive.md** — PLAN §요구사항1에서 완전 명세
- [x] **Artifact Gate 규칙 추가 — opal-harness-agentic.md** — PLAN §요구사항2에서 완전 명세
- [x] **필수 산출물 명세 추가 — 오케스트레이터 SKILL.md (공통 또는 인라인)** — PLAN §요구사항3에서 harness 공통화로 명세
- [x] **자가 점검 프롬프트 추가** — PLAN §요구사항4(요구사항1에 통합)에서 확인
- [x] **opwt ANALYSIS 단계 PM Gate 추가** — PLAN §요구사항5에서 명세 (단, AC와 표면 불일치 — Warning)
- [x] **opwt EXECUTE 배치 "PM 검토" → PM Gate 명확화** — PLAN §요구사항6에서 완전 명세

---

## 6. 판정

**Pass (Warning 2개)**

6개 요구사항이 모두 PLAN에 반영되어 있고 변경 파일 4개의 실존이 확인되었다. 요구사항 5의 TASK AC("QA Gate → PM Gate") 대비 PLAN 설계("PM 자가 체크만 추가") 불일치는 설계 근거가 명시된 의도적 편차로 판단되나, 사용자 확인을 권장한다. Critical 항목 없음.
