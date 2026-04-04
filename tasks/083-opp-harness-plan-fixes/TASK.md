# TASK: 하네스/스킬 문서 4건 정비 — STATE.md 누락 방지 + 병렬 판별 추가

> 작성일: 2026-04-04 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

하네스와 스킬 문서 간 암묵적/분산된 지침을 명시적으로 정비하여, 오케스트레이터와 워커의 프로세스 누락을 방지한다.

## 배경

다른 프로젝트에서 STATE.md 생성이 반복 누락되었다. 원인을 추적하니 하네스 §4와 op-task SKILL.md 사이에 STATE.md 생성 시점이 분산되어 있고, 스킬/공통 영역 구분이 불명확했다. 추가로 에스컬레이션 시점, PLAN의 병렬 판별 누락도 함께 발견되었다.

## 요구사항

- [x] R1. 하네스 §4 TASK 공통 프로세스에 스킬/공통 영역 구분 마커를 추가한다
- [x] R2. 하네스 §4에 STATE.md 생성 단계를 강조 표시한다
- [x] R3. op-task/SKILL.md 완료 보고 형식 위에 STATE.md 생성 리마인더를 추가한다
- [x] R4. opal-pilot-dev-short/SKILL.md 에스컬레이션 규칙에 조기 에스컬레이션 조항을 추가한다
- [x] R5. op-dev-plan/references/plan-guide.md 실행 체크리스트 섹션에 병렬/순차 Phase 판별 지침을 추가한다
- [x] R6. op-dev-plan/SKILL.md 품질 체크리스트에 Phase 그룹핑 확인 항목을 추가한다
- [x] R7. op-task-plan/references/plan-guide.md 실행 체크리스트 섹션에 병렬/순차 Phase 판별 지침을 추가한다
- [x] R8. op-task-plan/SKILL.md 품질 체크리스트에 Phase 그룹핑 확인 항목을 추가한다

## 제약 조건

- 기존 프로세스 흐름을 변경하지 않고 명시적 지침만 추가한다
- 하네스 변경은 모든 오케스트레이터에 영향을 주므로 기존 참조 관계를 깨지 않는다

## 기술 스택

- Markdown 문서

## 관련 문서

- `opal/core/references/opal-harness.md` — 하네스 §4 TASK 공통 프로세스
- `opal/skills/op-task/SKILL.md` — TASK 단계 스킬
- `opal/skills/opal-pilot-dev-short/SKILL.md` — Short Task 오케스트레이터
- `opal/skills/op-dev-plan/SKILL.md` — PLAN 단계 스킬
- `opal/skills/op-dev-plan/references/plan-guide.md` — PLAN 상세 가이드 (dev)
- `opal/skills/op-task-plan/SKILL.md` — 범용 PLAN 단계 스킬
- `opal/skills/op-task-plan/references/plan-guide.md` — 범용 PLAN 상세 가이드
