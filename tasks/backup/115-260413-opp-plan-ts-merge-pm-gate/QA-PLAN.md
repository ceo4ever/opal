# QA: PLAN — PLAN 워커 TEST-SCENARIO 통합 + QA Gate 제거 + PM Gate 검증 강화

> 검토일: 2026-04-13 | 판정: Needs Revision

## 1. 요약

`opal-pilot-dev` / `opal-pilot-dev-short`의 PLAN 단계에서 TEST-SCENARIO 별도 워커 디스패치와 QA Gate를 제거하고, `op-dev-plan` 워커가 PLAN.md + TEST-SCENARIO.md를 통합 작성하며 PM Gate가 두 산출물을 직접 검증하는 방식으로 파이프라인을 슬림화하는 PLAN.md다. 변경 대상은 마크다운 스킬 문서 3개이며, §1~§9 기능 중심 구조(Multi-Feature 모드, F-001~F-003)로 작성되었다. 소스 파일 현황 분석이 실제 소스와 정확히 일치하고, 설계 상세(Step 10 신설·PM Gate 강화·STATE.md 행 예시 갱신)가 TASK.md 요구사항을 완전히 커버한다. 단, §9 리스크 대응책에서 언급된 완료 기준 보강이 실제 §4.2 완료 기준에 반영되지 않은 불일치가 3건 발견되었다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | §3 설계 상세 + §4.2 실행 체크리스트 + 변경 전/후 명세가 충분. 실행자가 PLAN만으로 진행 가능. |
| GP-2 | 의존성 순서 | Pass | F-001 → F-002·F-003 순차, F-002‖F-003 병렬 구조가 올바르게 설계됨. §4.3 병렬/순차 근거도 명시. |
| GP-3 | TASK 반영 | Pass | R-1~R-5 전체가 F-001(R-1), F-002(R-2,R-3), F-003(R-4,R-5)로 1:1 커버. 누락 없음. |
| GP-4 | 파일 목록 완전성 | Pass | 변경 대상 3개 파일(`op-dev-plan/SKILL.md`, `opal-pilot-dev/SKILL.md`, `opal-pilot-dev-short/SKILL.md`) 모두 포함. 소스 확인 완료. |
| GP-5 | 설계 구체성 | Warning | §9 리스크 대응책에서 "완료 기준에 포함"이라고 명시한 항목 3건이 §4.2 완료 기준에 실제로 반영되어 있지 않음. (상세: §3 지적 사항) |
| GP-6 | 체크리스트 커버리지 | Pass | §4.2 Step 1~3이 R-1~R-5를 모두 분해. §5 QA 매트릭스도 TS-001~TS-011로 전 요구사항 커버. |

---

## 3. 지적 사항

### [Warning] §9 리스크 대응책과 §4.2 완료 기준 불일치 (3건)

**리스크 #1 — Agentic Mode 갱신 누락 리스크**

- §9 리스크 #1 대응: "Step 2·3에서 Agentic Mode 섹션의 자율 게이트 흐름도도 함께 갱신 (`PLAN+TEST-SCENARIO Gate` → `PLAN Gate`)"
- §4.2 Step 2·3 완료 기준: Agentic Mode 자율 게이트 흐름도 갱신 조건 없음
- 결과: EXECUTE 단계에서 갱신 누락이 검증되지 않을 수 있음

**리스크 #2 — STATE.md 행 번호 연속성 조건 누락**

- §9 리스크 #2 대응: "완료 기준에 '전체 행 번호가 1부터 연속적이어야 함' 조건 포함"
- §4.2 Step 2·3 완료 기준: 행 번호 연속성 조건 없음 (정성적 묘사만 존재)
- 결과: 행 번호 재조정 오류가 완료 판별 시 검출되지 않을 수 있음

**리스크 #3 — PLAN 디스패치 프롬프트 TEST-SCENARIO.md 경로 확인 조건 누락**

- §9 리스크 #3 대응: "Step 2·3 완료 기준에 '3-1 디스패치 프롬프트에 TEST-SCENARIO.md 경로 포함' 추가"
- §4.2 Step 2·3 완료 기준: 해당 조건 없음
- 결과: 디스패치 프롬프트에 TEST-SCENARIO.md 경로가 빠졌을 때 검증 불가

### 심각도 분류

- Warning: §9 리스크 대응책 3건이 §4.2 완료 기준에 반영되지 않음. EXECUTE 단계에서 오류 발견 가능성이 있으나, 핵심 설계 흐름(TEST-SCENARIO 통합, QA Gate 제거, PM Gate 강화)은 완전하고 명확하므로 즉시 진행은 가능. 완료 기준 보강 또는 EXECUTE 담당자 주의 지시로 대응 가능.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1 | PLAN.md F-001 Step 10 신설, frontmatter 갱신, Step 11 결과 반환 갱신 — 3가지 AC 모두 §3.1.2 설계에 명시됨 | Pass |
| TASK.md R-2 | PLAN.md F-002 STEP 3 구조 변경, PM Gate 강화 — TASK AC와 §3.2.2 설계 상세 일치 | Pass |
| TASK.md R-3 | PLAN.md F-002 STATE.md 행 예시 변경 전/후가 TASK AC와 일치. 실제 소스(opal-pilot-dev SKILL.md 172~192행)와도 일치 | Pass |
| TASK.md R-4 | PLAN.md F-003 STEP 2 구조 변경, PM Gate 강화 — TASK AC와 §3.3.2 설계 상세 일치 | Pass |
| TASK.md R-5 | PLAN.md F-003 STATE.md 행 예시 변경 전/후가 TASK AC와 일치. 실제 소스(opal-pilot-dev-short SKILL.md 160~182행)와도 일치 | Pass |
| TASK.md 제약 §5 | `op-dev-test-scenario/SKILL.md` 수정 금지 → PLAN.md 변경 대상 파일에 미포함. 읽기 전용으로만 참조 | Pass |
| TASK.md 제약 §6 | `~/.opal/` 직접 수정 금지 → PLAN.md 변경 대상이 `opal/skills/` 경로만 명시 | Pass |
| 소스 현황 일치성 | op-dev-plan/SKILL.md Step 1~10 구조, opal-pilot-dev/SKILL.md STEP 3 구조, opal-pilot-dev-short/SKILL.md STEP 2 구조 — §2 현재 구현 분석과 실제 소스 내용이 정확히 일치 | Pass |

---

## 5. 판정

**Needs Revision**

§9 리스크에서 스스로 인지한 대응책 3건(Agentic Mode 갱신 확인, 행 번호 연속성 조건, PLAN 디스패치 프롬프트 TEST-SCENARIO.md 경로 확인)이 §4.2 완료 기준에 반영되지 않았다. 핵심 설계 방향과 TASK 요구사항 커버리지는 완전하므로 수정 후 즉시 진행 가능하다.
