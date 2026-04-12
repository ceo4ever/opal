# QA: PLAN — opal-harness.md 구조화 리팩토링

> 검토일: 2026-04-12 | 판정: Pass

## 1. 요약

opal-harness.md의 §3 State 섹션에서 도메인 특화 내용(opsdd 파이프라인 예시, oppd 병렬 실행 State)을 제거하고 해당 스킬로 귀속시키는 리팩토링 계획이다. 총 4개 Step, 2개 Phase로 구성되며 변경 대상 파일은 4개(신규 생성 없음)다. R-1~R-5 요구사항 전체가 Step으로 매핑되어 있고, 각 Step의 완료 기준이 Grep/Read 기반으로 검증 가능한 형태로 명세되어 있다. 현황 조사에서 opsdd SKILL.md(lines 287-330)와 oppd 참조 파일에 이미 동일 내용이 존재함을 확인하여, 제거 후 운용 손실이 없음을 보장한다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | 파일 경로, 삭제 범위(line 번호), 변경 후 문구가 모두 명시되어 즉시 실행 가능 |
| GP-2 | 의존성 순서 | Pass | Phase 1(Step 1,2 병렬) → Phase 2(Step 3,4 병렬): Step 3,4가 하네스 내 참조 제거 이후 실행되는 논리적 의존관계 정확히 반영 |
| GP-3 | TASK 반영 | Pass | R-1~R-5 전체가 Step 1~4(+ 변경이력)로 분해되어 모두 커버됨 |
| GP-4 | 파일 목록 완전성 | Pass | opal-harness.md, opal-harness-interactive.md, oppd SKILL.md, parallel-execution-guide.md — 4개 파일 모두 포함. TASK.md가 언급한 관련 문서와 일치 |
| GP-5 | 설계 구체성 | Pass | 삭제 line 범위(233-273, 330-386), 교체 전후 문구, 참조 경로 변경 내용이 구체적으로 명세됨 |
| GP-6 | 체크리스트 커버리지 | Pass | §3 실행 체크리스트와 §4 QA 체크리스트가 기능/일관성/품질 항목을 모두 포함 |

## 3. 지적 사항

### Warning

**W-1 (Info): R-2 삭제 범위 경계 서술 부정확**

PLAN.md §2 핵심 설계에서 "삭제 후 빈 줄 정리 — `### 추가작업 프로세스` 서브섹션 종료 구분선 뒤에 바로 `### 세션 복원`이 이어지도록 함"이라고 기술하고 있으나, 실제 파일에서는 `### 병렬 실행 State` 앞에 `---` 구분선(line 328)과 빈 줄(line 329)이 먼저 오고 line 330부터 삭제 범위가 시작된다. 즉, 삭제 이후 `### 추가작업 프로세스` → `---` → `### 세션 복원` 순으로 연결되는데, 이는 자연스러운 구조이지만 PLAN 설명의 "종료 구분선 뒤에 바로 이어진다"는 표현이 실제 삭제 대상에 `---`와 빈 줄을 포함하지 않음을 혼동하게 할 수 있다.

- 심각도: **Info** — 실행 시 혼란 가능성이 낮고, 구분선(line 328)은 삭제 범위(330~)에 포함되지 않으므로 구조는 올바르다.

---

지적 사항은 위 1건(Info)이며 실행에 영향을 주지 않는다.

### 심각도 분류
- Critical: 없음
- Warning: 없음
- Info: 1건 (W-1)

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1 | opsdd SKILL.md lines 287-330에 5컬럼 파이프라인 현황판이 실제 존재 → 순수 제거 가능 | Pass |
| TASK.md R-2 | oppd SKILL.md lines 520-536, parallel-execution-guide.md lines 370-382에 병렬 실행 State 내용이 실제 존재 | Pass |
| TASK.md R-2 | 하네스 참조 문구 3곳(oppd SKILL.md line 430, guide line 308, 372) 모두 PLAN이 갱신 대상으로 포함 | Pass |
| TASK.md R-3 | opal-harness.md line 403에 deprecated 상태값(`QA Gate 대기`, `PM Gate 대기`, `사용자 확인 대기`) 실제 존재 확인 | Pass |
| TASK.md R-4 | opal-harness-interactive.md lines 119-127 `### 순서 강제 원칙` 서브섹션 실제 존재 확인 | Pass |
| TASK.md R-5 | 변경이력 v3.7 / v2.3 버전 번호가 기존 흐름(v3.6, v2.2)과 자연스럽게 이어짐 | Pass |
| parallel-execution-guide.md | §7 "STATE.md 갱신", §7-2, §7-3 섹션 실제 존재 → 새 참조 경로 유효 | Pass |
| 의존성 | Step 3, 4의 논리적 의존(Step 1 이후)이 Phase 2로 올바르게 그룹핑됨 | Pass |

## 5. 판정

**Pass**

R-1~R-5 전체 요구사항이 Step으로 분해되어 있고, 핵심 line 번호 참조(233, 273, 330, 386, 403, 180)가 실제 파일과 일치한다. 대상 스킬(opsdd, oppd)에 이관 대상 내용이 이미 존재하여 의미 손실 없이 제거 가능하며, 새 참조 경로도 유효하다. Info 1건은 실행에 영향 없다. 다음 단계(EXECUTE) 진행 가능.
