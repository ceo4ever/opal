# DONE: otp-dev PLAN과 TODO 단계 통합

> 완료일: 2026-03-28

## 변경 요약

### otp-dev (Full Task)
- 5 STEP → **4 STEP**: TODO 독립 단계 제거, PLAN에 흡수
- 흐름: TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE
- TEST-SCENARIO 문서 전용 스킵 조건 추가

### dtp-plan (구현 계획 스킬)
- 실행 체크리스트: 인라인 → 블록 형식 (완료 기준, 테스트, 실행 방법, 의존 필드)
- QA 체크리스트: 보안 카테고리 추가
- 복잡도 판별 섹션 신규
- 실행 아키텍처 (복잡 모드 전용) 섹션 신규
- PLAN.md 출력 형식: 6→8 섹션

### dtp-execute (코드 실행 스킬)
- Full/Short 분기를 PLAN.md 단일 소스로 통합
- TODO.md 참조 완전 제거

### otp-dev-short
- TEST-SCENARIO 문서 전용 스킵 조건 추가

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `skills/dtp-plan/references/plan-guide.md` | TODO 고유 가치 흡수 (분해 규칙, 보안 QA, 복잡도, 실행 아키텍처) |
| `skills/dtp-plan/SKILL.md` | 프로세스 확장 (9 Step), 출력 형식 8 섹션 |
| `skills/otp-dev/SKILL.md` | 5→4 STEP, TODO 제거, TEST-SCENARIO 스킵 조건 |
| `skills/otp-dev-short/SKILL.md` | TEST-SCENARIO 스킵 조건 추가 |
| `skills/dtp-execute/SKILL.md` | checklist_source PLAN.md 통일 |
| `skills/dtp-execute/references/execute-guide.md` | Full/Short 분기 통합, TODO 참조 제거 |

## 검증

- [x] otp-dev STEP 번호 1~4 연속
- [x] dtp-execute에 TODO.md 참조 0건
- [x] 복잡도 판별 + 실행 아키텍처 섹션 존재
- [x] TEST-SCENARIO 스킵 조건 양쪽 모두 적용
- [x] 비변경 섹션 보존
