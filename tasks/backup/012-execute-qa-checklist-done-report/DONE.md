# DONE: EXECUTE 완료 시 QA 체크리스트 갱신 + 완료 리포트 생성 규칙 추가

> 완료일: 2026-03-15 | 모드: Short Task | 작업 유형: 기능 개선

## 완료 요약

task-flow EXECUTE 완료 후 QA 체크리스트 검증/갱신 규칙과 DONE.md 완료 리포트 생성 규칙을 task-flow 스킬에 정식 반영했다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `skills/task-flow/SKILL.md` | Full 단순/복잡/Short EXECUTE 3곳에 QA 체크리스트 갱신 단계 추가. DONE.md 생성 규칙+템플릿 신규 섹션. 산출물 저장 구조에 DONE.md 추가. 완료 보고 형식에 DONE.md 경로 추가 |
| 2 | `skills/task-flow/references/execute-guide.md` | 체크리스트 갱신 규칙을 실행/QA로 분리. 단순/복잡/Short 실행 흐름에 QA 갱신+DONE.md 단계 삽입. DONE.md 생성 규칙 섹션 신설 |
| 3 | `CLAUDE.md` | Full/Short 산출물 구조에 DONE.md 추가. 완료 보고 형식에 DONE.md 경로 추가 |

## 핵심 변경 사항

### Before
- 실행 체크리스트만 갱신, QA 체크리스트는 미갱신
- 태스크 완료 시 기록이 남지 않음

### After
- EXECUTE 완료 → QA 체크리스트 항목별 검증 + 체크박스 갱신 → QA 에이전트 호출 → DONE.md 생성
- DONE.md: 완료 요약, 변경 파일, Before/After, QA 결과, 산출물 목록

## QA 결과

- QA-PLAN: Pass (5/5)
- QA-EXECUTE: Pass (7/7)
- QA 체크리스트: 15/15 항목 Pass

## 산출물 목록

| 파일 | 설명 |
|------|------|
| TASK.md | 작업 정의서 |
| PLAN.md | 통합 PLAN (코드 분석 + 구현 계획 + 체크리스트) |
| QA-PLAN.md | PLAN QA 리뷰 |
| QA-EXECUTE.md | EXECUTE QA 리뷰 |
| DONE.md | 완료 리포트 (본 문서) |
