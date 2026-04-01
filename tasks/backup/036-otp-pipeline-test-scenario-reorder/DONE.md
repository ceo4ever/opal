# DONE: otp 파이프라인 TEST-SCENARIO 단계 재배치 + EXECUTE 후 커밋 규칙 명시

> 완료일: 2026-03-28

## 변경 요약

### otp-dev-short (Short Task)
- 4 STEP → **3 STEP**: TEST-SCENARIO를 STEP 2(PLAN)에 통합
- 흐름: TASK → PLAN + TEST-SCENARIO → EXECUTE
- EXECUTE 후 커밋 규칙 명시

### otp-dev (Full Task)
- 6 STEP → **5 STEP**: TEST-SCENARIO를 STEP 4(TODO)에 통합
- 흐름: TASK → ANALYSIS → PLAN → TODO + TEST-SCENARIO → EXECUTE
- EXECUTE 후 커밋 규칙 명시

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `skills/otp-dev-short/SKILL.md` | STEP 재구성 (4→3), 파이프라인 다이어그램, STATE.md 템플릿, 커밋 규칙 |
| `skills/otp-dev/SKILL.md` | STEP 재구성 (6→5), 파이프라인 다이어그램, STATE.md 템플릿, 커밋 규칙 |

## 검증

- [x] 파이프라인 다이어그램이 STEP 내용과 일치
- [x] STEP 번호 연속성 (빠짐/중복 없음)
- [x] TEST-SCENARIO 디스패치 프롬프트 보존
- [x] STATE.md 템플릿 단계 목록 정합성
- [x] 커밋 규칙 양쪽 모두 명시
- [x] 비변경 섹션 보존 (에스컬레이션, 구현 금지 원칙, Git 사전 점검, FE/BE 병렬 등)
