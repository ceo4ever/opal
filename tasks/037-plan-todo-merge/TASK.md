# TASK: otp-dev PLAN과 TODO 단계 통합

> 작성일: 2026-03-28 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

otp-dev(Full Task) 파이프라인에서 PLAN(STEP 3)과 TODO(STEP 4 내 4-1)를 통합하여 단계 수를 줄이고 효율성을 높인다.

## 배경

현재 PLAN과 TODO의 역할이 상당 부분 중복되어 별도 단계로 유지하는 실효성이 낮다:

| 항목 | PLAN에 이미 있음 | TODO가 추가하는 것 |
|------|-----------------|-------------------|
| 실행 체크리스트 | "3. 실행 체크리스트" (Step별 파일+작업) | 완료 기준, 테스트 방법, 실행 방법(direct/sub-agent), 의존 |
| QA 체크리스트 | "4. QA 체크리스트" (기능/회귀/품질) | Part B (기능/회귀/품질/**보안**) — 거의 동일 |
| 복잡도 판별 | 없음 | 단순/복잡 모드 결정 |
| 실행 아키텍처 | execution-plan.json (FE/BE 병렬) | Part C (에이전트 토폴로지, 스킬 요구사항) — 복잡 모드 전용 |

2개 단계 + 2번의 워커 디스패치 + 2번의 검토 게이트로 오버헤드가 발생한다.

## 요구사항

- [ ] PLAN에 TODO의 고유 가치(완료 기준, 테스트 방법, 실행 방법, 보안 QA, 복잡도 판별, 실행 아키텍처)를 흡수
- [ ] otp-dev 파이프라인에서 TODO 독립 단계 제거 — 5 STEP → 4 STEP
- [ ] dtp-plan/SKILL.md와 references/plan-guide.md에 흡수된 내용 반영
- [ ] otp-dev/SKILL.md 파이프라인 다이어그램 및 STEP 번호 업데이트
- [ ] dtp-todo/SKILL.md는 삭제하지 않음 (레거시 보존) — 단 otp-dev에서 호출하지 않도록 변경
- [ ] otp-dev-short는 변경 없음 (이미 TODO 단계 없음)

## 제약 조건

- dtp-execute가 참조하는 checklist_source가 PLAN.md로 통일되는지 확인 필요
- execution-plan.json 생성 로직은 PLAN에 이미 존재하므로 유지
- Part C(실행 아키텍처)의 복잡 모드 로직을 PLAN에 어떻게 흡수할지 설계 필요

## 기술 스택

- 마크다운 문서 (SKILL.md)

## 관련 문서

- [skills/otp-dev/SKILL.md](skills/otp-dev/SKILL.md) — Full Task 오케스트레이터
- [skills/dtp-plan/SKILL.md](skills/dtp-plan/SKILL.md) — 구현 계획 스킬
- [skills/dtp-plan/references/plan-guide.md](skills/dtp-plan/references/plan-guide.md) — PLAN 상세 가이드
- [skills/dtp-todo/SKILL.md](skills/dtp-todo/SKILL.md) — TODO 스킬 (통합 대상)
