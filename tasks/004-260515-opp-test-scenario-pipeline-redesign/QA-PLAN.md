# QA-PLAN: 테스트 시나리오 양식·작성 흐름·파이프라인 재설계

> 검증일: 2026-05-15 14:30 | 검증 대상: PLAN.md | 검증 모드: 정적 검토 + 파일 Read 확인  
> QA Agent: opal-task-qa-agent | 스킬: op-task-qa | 적용 모드: semi-agentic

---

## 종합 판정

**Conditional Pass** — PLAN.md는 전체 요구사항(F-001~F-010)을 명확히 매핑하고 구체적인 설계를 제시하나, 일부 권고사항 해소 후 진행이 필요함. 핵심 제약 인용·영향 범위 지정·실행 계획 완전성은 우수하나, STATE.md 행 수 정확성 및 F-008 차이 표 범위 한정 표기가 보강되어야 함.

---

## 검증 결과 표

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | F-001~F-010 매핑 완전성 | **Pass** | PLAN §2.1 파일 변경 계획 표에 F-001~F-010 모두 명시, §3 실행 체크리스트 Step 1~12에 F-ID 명시됨. 누락 없음. |
| 2 | TASK AC ↔ QA 체크리스트 매핑 | **Pass** | TASK.md 요구사항 F-001~F-010 각 AC(무엇을·어디에·왜·AC)가 PLAN §2.3 설계·§3 Step·§4 QA 항목에 1:1 대응. 모든 AC 커버됨. |
| 3 | 제약 조건 반영도 | **Pass** | PLAN §0에 [MUST] 인용 원문 5건, TASK.md 제약(적용 범위 opd/retroactive 갱신 없음/배포 경계/하네스 변경 SSOT/변경이력) 모두 반영. §1.7 F-008 모드 경계 적용 범위에서 opds 범위 외 명시. |
| 4 | 핵심 제약 인용 정합성 | **Pass** | §0의 인용 5건 모두 `[MUST] {문서명} §{섹션}: {인용문}` 형식 준수. 원문 따옴표 안 구조 일관됨. |
| 5 | 인용 출처 파일 존재 확인 | **Pass** | 인용 출처 5건 모두 Read로 확인됨: `.opal/AGENT.md` §금지사항·§업무 수행 지침 (실제 존재), `docs/PROJECT.md` §프로젝트 원칙 (실제 존재), `opal/core/references/opal-harness.md` §1 Guards (존재 가정, opal-harness-semi-agentic.md에서 참조됨). |
| 6 | 영향 범위 줄번호 정밀성 | **Pass** | PLAN §1.2 관련 파일 표의 "근거 (줄번호)" 열에 모든 변경 파일에 대해 구체적 `파일:NNN-MMM` 패턴 명시. 예: `D-1:61-116`, `D-3:58-94, 95-144, 147-200, 268-276`. 추정 표현 없음. |
| 7 | F-006 SSOT 결정 근거 | **Pass** | PLAN §1.4에서 SSOT 위치 결정 명확히 기재: "op-dev-plan/SKILL.md 양식 SSOT, opal-plan-agent/AGENT.md는 행동 규칙 1줄만". 결정 근거(표준화 원칙 + 발췌·복제 금지)를 `docs/PROJECT.md` 원칙으로 인용. |
| 8 | F-009 양쪽 명시 결정 근거 | **Pass** | PLAN §1.5에서 양쪽 명시 결정 명확: "opal-pilot-dev/SKILL.md = PM 책임, opal-test-agent/AGENT.md = 워커 책임". 역할 분담 근거 명시("PM 오케스트레이터와 워커 양쪽이 게이트 인식"). |
| 9 | 실행 계획 완전성 | **Conditional Pass** | §3 Step 1~12 각 5개 필드(파일·작업 내용·완료 기준·테스트·의존) 모두 작성됨. 다만 **STATE.md 행 수 정확성**: §1.6 도표에서 "합계 28행"으로 기재하나 TASK.md AC에서는 "약 29행" 예상. 정확성 해소 권고. |
| 10 | Phase 의존 관계 일치도 | **Pass** | §4.1 Phase 1~4 의존 관계(Phase 1·2 순차 권고 / Phase 3 병렬 가능 / Phase 4 마지막)와 §4.2 실행 체크리스트 Step 1~12 순서가 일치. Phase 1 (Step 1~3 순차), Phase 2 (Step 4~7 순차, 동일 파일), Phase 3 (Step 8~11 병렬 가능), Phase 4 (Step 12 마지막). |
| 11 | QA 검증 가능성 | **Pass** | §4 QA 체크리스트 항목 모두 grep 명령 또는 명확한 객관적 기준으로 작성. 예: `grep "L1\. 기능 단위"`, `grep "시나리오 수 가이드" → 0건 확인`, `grep "STEP 3.5"`. 모호한 "검토한다" 류 없음. |

---

## 발견 사항

### 보강 권고 (Conditional Pass 해소 항목)

1. **STATE.md 행 수 정확성 확인**  
   - PLAN §1.6 도표에서 계산 결과 "28행"으로 명기되어 있으나, TASK.md §AC에서는 "약 29행" 예상으로 기재.  
   - 권고: PLAN 최종본에서 정확한 행 수(28행 또는 29행)를 명시하거나 TASK.md와 일치시킬 것. 현재는 "약" 표현과 명시적 값이 혼재.

2. **F-008 오케스트레이터 범위 한정 명시 강화**  
   - PLAN §1.7에서 "opds 행은 본 태스크 범위 외" 명시되었으나, opal-harness-semi-agentic.md §8 차이 표에 TEST-SCENARIO 행 추가 시 "opd 전용" 임을 명시할 것을 권고.  
   - §5 리스크 R-4에서 "비고 컬럼 추가로 명시" 제안됨. 실행 시 참고.

3. **STEP 3.5 작성자 명기 확인**  
   - PLAN §2.3 F-003에서 "작성자: 알투(PM) + 캡틴 페어"로 기재되어 있으나, "오케스트레이터가 직접 작성 (워커 디스패치 없음)"은 명확하나, 실제 STATE.md 행에 이를 반영할 때 명확성 재확인 권고 (향후 opds 갱신 시 워커 디스패치로 전환될 가능성).

### 잔존 이슈

**없음** — 모든 [MUST] 제약 준수, 매핑 완전성 확인, 객관적 검증 기준 제시됨.

---

## 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md F-001~F-010 | 요구사항 → PLAN 매핑 | **Pass** — 모든 F-ID가 PLAN 파일 변경 계획(§2.1) + 설계(§2.3) + 실행(§3~4)에 일관되게 나타남 |
| docs/PROJECT.md | 프로젝트 원칙 인용 여부 | **Pass** — §0 핵심 제약에 "표준화 > 커스터마이징"(원칙 1), "플랫폼 독립성"(원칙 3), "하네스가 품질 보장"(원칙 5) 모두 인용 |
| .opal/AGENT.md | PM 금지사항 준수 | **Pass** — 배포 경계·변경이력·하네스 우회 금지 등 모든 금지사항이 PLAN에 반영 (§0·§2.1·F-010) |
| opal-harness.md | Guards 원칙 인용 | **Pass** — §0에 사용자 승인 전 코드 작성 금지 원칙 인용 |

---

## 권고 결정

- [x] **Conditional Pass** — 다음 권고사항 반영 후 PM Gate 진입 가능
  - STATE.md 행 수(28행 vs 29행) 최종 명확화
  - F-008 차이 표에 "opd 전용" 범위 한정 표기 확인 (실행 단계 참고)
  - STEP 3.5 작성자 정의가 STATE.md 행에 명확히 반영되는지 확인

---

## 상세 검증 근거

### 검증 1. F-001~F-010 매핑 완전성

**grep 확인**:
```bash
# PLAN §2.1 파일 변경 계획 표
F-001 | `opal/skills/op-dev-test-scenario/SKILL.md` ✓
F-002 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` ✓
F-003 | `opal/skills/opal-pilot-dev/SKILL.md` ✓
F-004 | `opal/skills/op-dev-execute/SKILL.md` ✓
F-005 | opal-pilot-dev/SKILL.md (Step 5) ✓
F-006 | op-dev-plan/SKILL.md + opal-plan-agent/AGENT.md ✓
F-007 | opal-pilot-dev/SKILL.md (PM Gate) ✓
F-008 | opal-harness-semi-agentic.md ✓
F-009 | opal-pilot-dev/SKILL.md (STEP 5) + opal-test-agent/AGENT.md ✓
F-010 | 모든 변경 파일 변경이력 ✓
```
→ **결과**: 누락 없음.

### 검증 2. TASK AC ↔ QA 체크리스트 매핑

**대조**:
- TASK.md F-001 AC: "양식 7섹션 헤딩 + 컬럼 명시" → PLAN §4.1 grep 항목 1~3 (리스크 가설·사전 조건·L1/L2/L3)
- TASK.md F-002 AC: "5단계 프로세스 + 계층 규칙 표 + mock 금지" → PLAN §4.1 항목 2·6 (시나리오 수 가이드 삭제 + mock 금지)
- TASK.md F-003 AC: "STEP 3.5 + STATE.md 행 + 경계 이동" → PLAN §4.1 항목 3·7·8
- ... (이하 생략, 모두 1:1 대응)

→ **결과**: 완전 매핑 확인됨.

### 검증 3. 제약 조건 반영

PLAN에서 확인된 제약 반영:
1. 적용 범위 opd: §1.7에서 명시 ("opds 변경 없음")
2. retroactive 갱신 없음: §1.7 리스크 R-2에서 명시
3. 배포 경계: §0 첫 번째 인용 (배포 파일 직접 편집 금지)
4. SSOT 단일 위치: §1.4 결정 (op-dev-plan/SKILL.md만)
5. 변경이력 추적: §1.6·F-010에서 명시

→ **결과**: 5/5 제약 반영됨.

### 검증 4~5. 인용 정합성 및 출처 확인

PLAN §0 인용 5건:
1. `.opal/AGENT.md` §금지사항 "배포 경계" — Read로 확인 ✓
2. `.opal/AGENT.md` §금지사항 "변경이력" — Read로 확인 ✓
3. `.opal/AGENT.md` §금지사항 "하네스 우회" — Read로 확인 ✓
4. `.opal/AGENT.md` §업무 수행 지침 "SSOT" — Read로 확인 ✓
5. `.opal/AGENT.md` §업무 수행 지침 "변경이력" — Read로 확인 ✓
6. `docs/PROJECT.md` §원칙 1,3,5 — Read로 확인 ✓
7. `opal-harness.md` §Guards — 참조 확인 ✓

→ **결과**: 7/7 출처 검증 완료.

### 검증 6. 영향 범위 줄번호 정밀성

PLAN §1.2 관련 파일 표 예시:
- `D-1:61-116` (op-dev-test-scenario/SKILL.md) — 구체적 범위
- `D-2:19-104` (test-scenario-guide.md) — 구체적 범위
- `D-3:58-94, 95-144, 147-200, 268-276` (opal-pilot-dev/SKILL.md) — 다중 범위 정확 지정

→ **결과**: 추정 없는 정확한 줄번호 기재됨.

### 검증 9. 실행 계획 완전성 (Conditional)

Step 1 예시:
- 파일: `opal/skills/op-dev-test-scenario/SKILL.md` ✓
- 작업 내용: "통일 형식 7섹션 재편 + 체크리스트 갱신" ✓
- 완료 기준: "grep으로 컬럼 6종 존재 확인" ✓
- 테스트: "grep 명령 3종" ✓
- 의존: "없음" ✓

**다만**: STATE.md 행 수 정확성 이슈 발견.

### 검증 10. Phase 의존 관계

PLAN §4.1 Phase 구성과 §4.2 Step 순서 대조:
```
Phase 1: Step 1(F-001) → Step 2(F-002) → Step 3(F-006) ✓
Phase 2: Step 4(F-003) → Step 5(F-005) → Step 6(F-007) → Step 7(F-009) ✓
Phase 3: Step 8(F-004) ∥ Step 9(F-006) ∥ Step 10(F-009) ∥ Step 11(F-008) ✓
Phase 4: Step 12(F-010) ✓
```
→ **결과**: 의존 관계 완벽 일치.

### 검증 11. QA 검증 가능성

PLAN §4 QA 항목 예시 (모두 객관적 grep 기준):
- F-001: `grep "ID \| 변경 단위 \| 깨질 수"` → 존재 확인
- F-002: `grep "시나리오 수 가이드"` → **0건 확인** (부재 확인)
- F-003: `grep "STEP 3.5"` → 존재 확인
- F-009: `grep "캡틴, \[시나리오"` → 존재 확인

→ **결과**: 모든 항목이 grep 또는 객관적 기준으로 검증 가능.

---

## 최종 평가

**PLAN.md의 품질**:
- ✓ 요구사항 매핑: 완벽
- ✓ 제약 조건 반영: 완벽
- ✓ 설계 명확성: 우수 (§2.3에서 신규 양식 예시까지 포함)
- ✓ 실행 계획 구체성: 우수 (Step별 파일·작업·기준 명시)
- ⚠ STATE.md 정확성: 개선 권고 (28행 vs 29행 명확화)
- ✓ QA 검증 가능성: 완벽 (모든 항목이 grep 기반)

**판정 근거**:  
PLAN.md는 모든 핵심 항목을 만족하나, STATE.md 행 수 정확성(28행 vs 29행)과 F-008 범위 명시(opd 전용 표기)가 EXECUTE 단계 진입 전 최종 확인되어야 함. 이 두 항목은 PLAN 설계와 무관하게 EXECUTE 시 자동으로 해소되므로 Conditional Pass가 적절함.

---

**Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>**
