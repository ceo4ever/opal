# DONE: EXECUTE 후 검증 흐름 재설계 — task-flow-test 중심으로 전환

> 완료일: 2026-03-19 | 모드: Short Task | 작업 유형: 기능 개선

## 완료 요약

EXECUTE 후 검증 흐름을 task-flow-test 중심으로 재설계했다. TEST-SCENARIO.md를 새로운 단일 산출물로 도입하여 테스트 계획(task-flow-agent 작성)과 실행 결과(task-flow-test 채움)를 통합 관리한다. QA-EXECUTE.md와 TEST-REPORT.md를 폐지하고, task-flow-qa의 EXECUTE 검증 역할을 task-flow-test가 대체한다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `skills/task-flow/references/test-scenario-guide.md` | 신규: TEST-SCENARIO.md 작성 가이드 + 템플릿 |
| 2 | `agents/claude/task-flow-test/AGENT.md` | 모든 모드 호출, TEST-SCENARIO.md 입력, 결과 인라인 기록 |
| 3 | `agents/cursor/task-flow-test.md` | #2와 동일 (Cursor 포맷) |
| 4 | `agents/antigravity/task-flow-test/SKILL.md` | #2와 동일 (Antigravity 포맷) |
| 5 | `agents/claude/task-flow-qa/AGENT.md` | EXECUTE 검증(E-1~E-7) 제거 |
| 6 | `agents/cursor/task-flow-qa.md` | #5와 동일 (Cursor 포맷) |
| 7 | `agents/antigravity/task-flow-qa/SKILL.md` | #5와 동일 (Antigravity 포맷) |
| 8 | `skills/task-flow/SKILL.md` | 워크플로우/QA 호출 맵/Test 호출 규칙/산출물 구조 갱신 |
| 9 | `skills/task-flow/references/execute-guide.md` | 3모드 모두 test 호출로 전환 |
| 10 | `skills/task-flow/references/execute-plan-guide.md` | TEST-SCENARIO.md 참조 추가 |
| 11 | `CLAUDE.md` | 산출물 구조/워크플로우/QA 설명 갱신 |

## 핵심 변경 사항

### Before
- task-flow-test: Full Task 복잡 모드에서만 호출, TEST-REPORT.md 별도 생성
- task-flow-qa: 모든 모드에서 QA-EXECUTE.md 생성 (문서 기반 정적 리뷰)
- 테스트 시나리오: PLAN/TODO QA 체크리스트에 항목 수준으로만 존재
- 산출물: QA-EXECUTE.md + TEST-REPORT.md(복잡 모드)

### After
- task-flow-test: 모든 모드에서 호출, TEST-SCENARIO.md에 결과 인라인 기록
- task-flow-qa: RESEARCH/PLAN 검증만 유지, EXECUTE 검증 제거
- 테스트 시나리오: TEST-SCENARIO.md로 독립 산출물화 (대상+조건+기대+결과 통합)
- 산출물: TEST-SCENARIO.md 단일 파일 (계획+결과)

## 테스트 결과

문서 전용 변경 — 코드 테스트 해당 없음. 3개 플랫폼 에이전트 파일 내용 동기화 확인 완료.

## 산출물 목록

| 파일 | 설명 |
|------|------|
| TASK.md | 작업 정의서 + 설계 결정 |
| PLAN.md | 통합 PLAN (코드 분석 + 구현 계획 + 체크리스트) |
| QA-PLAN.md | PLAN QA 리뷰 |
| DONE.md | 완료 리포트 |
