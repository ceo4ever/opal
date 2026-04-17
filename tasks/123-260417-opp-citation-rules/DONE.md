---
@header
module: tasks/123-260417-opp-citation-rules
layer: task
description: DONE — 산출물 인용 위치 추적 하네스 (Citation Rules) 완료 보고
---

# DONE: 산출물 인용 위치 추적 하네스 (Citation Rules)

> 태스크: 123 | 적용 스킬: opp | 모드: interactive
> 시작: 2026-04-17 08:35 | 완료: 2026-04-17 09:25 (KST)

---

## 1. 요약

TASK/ANALYSIS/PLAN 3단계 산출물에 설계 결정의 **근거 문서 + 위치를 인용하는 규칙**을 OPAL 하네스에 필수 모듈로 도입했다.

신규 `harness/citation-rules.md` 모듈이 인용 포맷 4종(문서/코드/외부/MUST) + 단계별 의무 수준 매트릭스 + 사람/AI 탐색 가이드를 SSOT로 정의하고, 관련 6개 스킬/가이드 파일이 이를 참조하도록 갱신되었다.

## 2. 요구사항 달성 (R-1 ~ R-6)

| # | 요구사항 | 결과 | 변경 위치 |
|---|---------|------|---------|
| R-1 | harness/citation-rules.md 신규 생성 (§1~§6) | ✅ | `opal/core/references/harness/citation-rules.md` |
| R-2 | opal-harness.md §2 모듈 테이블에 citation-rules 등록 | ✅ | `opal/core/references/opal-harness.md` (v4.3) |
| R-3 | op-task TASK.md "관련 문서" 섹션 테이블화 | ✅ | `opal/skills/op-task/SKILL.md` (v1.3) |
| R-4 | op-dev-analysis ANALYSIS.md §0 참조 문서 + 근거 컬럼 추가 | ✅ | `opal/skills/op-dev-analysis/SKILL.md` (v1.3) |
| R-5 | op-dev-plan PLAN.md §3 근거 컬럼 + §8.3 신설 + plan-guide 갱신 | ✅ | `opal/skills/op-dev-plan/SKILL.md` (v2.3), `references/plan-guide.md` (v2.2) |
| R-6 | op-task-plan PLAN.md §1 참조 테이블 + §2 인용 필드 + plan-guide 갱신 | ✅ | `opal/skills/op-task-plan/SKILL.md` (v1.2), `references/plan-guide.md` (v1.1) |

## 3. 핵심 설계 결정

| 결정 | 내용 |
|------|------|
| 인용 포맷 4종 | 문서(`경로 §N`) / 코드(`경로:줄번호`) / 외부(`[사이트명](URL)`) / 필수제약(`[MUST] 경로 §N: 원문`) |
| 혼합 방식 | 참조 문서 테이블(개요) + 인라인 인용(구체 근거) |
| 단계별 의무 강화 | TASK(테이블 필수, 인라인 선택) → ANALYSIS(인라인 필수) → PLAN(인라인+MUST 필수) |
| PM 포맷 통일 | `opal-pm.md §3 Step 3`의 `[MUST]` 포맷을 워커 산출물 기록 포맷으로 재사용 |
| SSOT | 6개 파일 모두 citation-rules.md를 참조하고 포맷을 자체 기재하지 않음 |

## 4. 변경 파일 (8개)

### 신규 생성 (1개)
- `opal/core/references/harness/citation-rules.md` (v1.0) — 인용 규칙 하네스 모듈

### 수정 (7개)
- `opal/core/references/opal-harness.md` (v4.3) — §2 모듈 테이블 citation-rules 행 추가
- `opal/skills/op-task/SKILL.md` (v1.3) — "관련 문서" 테이블화
- `opal/skills/op-dev-analysis/SKILL.md` (v1.3) — §0 참조 문서 + §1.1/§5 근거 컬럼
- `opal/skills/op-dev-plan/SKILL.md` (v2.3) — §3 근거 컬럼 + §8.3 참조 문서 테이블
- `opal/skills/op-dev-plan/references/plan-guide.md` (v2.2) — 3단계 인용 지시 + 3.5단계
- `opal/skills/op-task-plan/SKILL.md` (v1.2) — §1 참조 문서 테이블 + §2 인용 필드
- `opal/skills/op-task-plan/references/plan-guide.md` (v1.1) — 현황 조사 + 근거 인용

## 5. Gate 통과 이력

| 단계 | Gate | 결과 |
|------|------|------|
| TASK | 사용자 확인 | ✅ Pass |
| PLAN | QA Gate → State Gate → PM Gate | ✅ Pass |
| PLAN | 사용자 확인 | ✅ Pass |
| EXECUTE | 작업 (8 Step / 2 Phase) | ✅ |
| EXECUTE | QA Gate → State Gate → PM Gate | ✅ Pass (Warning 1 Info급) |
| CLOSE | 진입 게이트 (사용자 확인 "확인 및 커밋") | ✅ Pass |

## 6. 산출물

- **TASK.md**: 요구사항 정의 (R-1~R-6)
- **PLAN.md**: 8 Step / 2 Phase 실행 계획
- **QA-PLAN.md**: PLAN 검증 (Pass)
- **QA-EXECUTE.md**: EXECUTE 검증 (Pass)
- **STATE.md**: 파이프라인 현황판 (20행)
- **DONE.md**: 본 문서

## 7. 후속 권고

- **배포**: 개발 완료. 캡틴의 "배포" 지시 시 `install-mac.sh` 실행 (확정 기준 #2)
- **다음 태스크부터 적용**: 신규 TASK.md/ANALYSIS.md/PLAN.md 작성 시 citation-rules.md §4 의무 수준 기준 적용
