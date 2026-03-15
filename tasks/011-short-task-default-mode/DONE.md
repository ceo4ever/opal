# DONE: Short Task 기본 모드 전환 및 판별 조건 개선

> 완료일: 2026-03-15 | 모드: Short Task | 작업 유형: 기능 개선

## 완료 요약

Short Task를 기본 모드로 전환하고, 기존 5개 AND 진입 조건을 제거하여 Full Task 4개 OR 트리거 조건으로 역전했다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `skills/task-flow/SKILL.md` | 모드 판별 규칙 섹션 전면 교체 (Short 기본 + Full 트리거), description 부제 수정, 에스컬레이션 기준 갱신 |
| 2 | `CLAUDE.md` | Full/Short 부제 변경, 모드 판별 한줄 설명 갱신 |

## 핵심 변경 사항

### Before
- Short Task 진입: 5개 조건 **모두** 충족 필요 (파일 ≤3, Step ≤5, 단일 모듈, 외부 의존성 없음, 작업 유형 적합)
- 하나라도 미충족 → Full Task
- Short = "간단한 버그 수정, 설정 변경 등"

### After
- **Short Task가 기본 모드** — 모든 작업은 Short로 시작
- Full Task 트리거: (1) 사용자 명시 요청, (2) 변경 파일 ≥10개, (3) 다단계 기술 의사결정, (4) 다중 모듈 간 연쇄 영향
- 트리거 해당 시 Full을 **제안**, 사용자가 결정
- Short = "기본 모드, 대부분의 작업"

## QA 결과

- QA-PLAN: Pass (5/5)
- QA-EXECUTE: Pass (7/7)
- QA 체크리스트: 11/11 항목 Pass

## 산출물 목록

| 파일 | 설명 |
|------|------|
| TASK.md | 작업 정의서 |
| PLAN.md | 통합 PLAN (코드 분석 + 구현 계획 + 체크리스트) |
| QA-PLAN.md | PLAN QA 리뷰 |
| QA-EXECUTE.md | EXECUTE QA 리뷰 |
| DONE.md | 완료 리포트 (본 문서) |
