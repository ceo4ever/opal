# DONE: dev-task-pilot 모드별 스킬/에이전트 분리 리팩토링

> 완료일: 2026-03-21 | 모드: Full Task | 작업 유형: 개선

## 완료 요약

dev-task-pilot의 단일 SKILL.md(1039줄)를 모드별 파일로 분리하고, 에이전트 4개를 7개로 확장하여 Full Task / Short Task / Wireframe UI 멀티 모드 아키텍처를 구축했다. 3플랫폼(Claude/Cursor/Antigravity) 에이전트 21개를 생성하고, 기존 12개를 삭제했다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `skills/dev-task-pilot/SKILL.md` | 라우터로 리팩토링 (1039줄 → 652줄). 모드 판별 + 디스패치 + 공통 규칙만 유지 |
| 2 | `skills/dev-task-pilot/modes/dev-full.md` | Full Task 파이프라인 (신규) |
| 3 | `skills/dev-task-pilot/modes/dev-short.md` | Short Task 파이프라인 (신규) |
| 4 | `skills/dev-task-pilot/modes/wireframe-ui.md` | Wireframe UI 파이프라인 (신규) |
| 5 | `skills/dev-task-pilot/references/wireframe-task-guide.md` | Wireframe TASK 단계 가이드 (신규) |
| 6 | `skills/dev-task-pilot/references/wireframe-qa-guide.md` | Wireframe QA 검증 기준 (신규) |
| 7-13 | `agents/claude/dtp-{dev-full,dev-short,wireframe-ui,qa-dev,qa-wireframe,action-plan,dev-test}-agent/AGENT.md` | Claude 에이전트 7개 (신규) |
| 14-20 | `agents/cursor/dtp-*-agent.md` | Cursor 에이전트 7개 (신규) |
| 21-27 | `agents/antigravity/dtp-*-agent/SKILL.md` | Antigravity 에이전트 7개 (신규) |
| 28 | `opal/core/references/agents.md` | 레지스트리 갱신 (4개 → 7개) |
| 29 | `CLAUDE.md` | 에이전트 구조 표 갱신 |
| - | 기존 에이전트 12개 | 삭제 (dtp-agent, dtp-qa, dtp-planner, dtp-test × 3플랫폼) |

## 핵심 변경 사항

### Before
- SKILL.md 1039줄에 Full/Short 모든 로직이 포함
- 에이전트 4개 (dtp-agent, dtp-qa, dtp-planner, dtp-test)
- 모드 2개 (Full Task, Short Task)
- Wireframe UI 작업은 wireframe-builder + ui-designer를 수동으로 연결

### After
- SKILL.md 652줄 (라우터) + modes/ 3파일 (모드별 파이프라인)
- 에이전트 7개 (모드별 워커 3개 + QA 2개 + planner 1개 + test 1개)
- 모드 3개 (Full Task, Short Task, Wireframe UI)
- Wireframe UI 파이프라인이 TASK → WIREFRAME → EXECUTE → QA로 통합

## 테스트 결과

All Pass — 시나리오 18/18 Pass, 회귀 테스트 4/4 Pass, 문서 품질/보안 Pass

## 산출물 목록

| 파일 | 설명 |
|------|------|
| tasks/024-dtp-mode-split-refactoring/TASK.md | 작업 정의서 |
| tasks/024-dtp-mode-split-refactoring/ANALYSIS.md | 분석 결과 |
| tasks/024-dtp-mode-split-refactoring/QA-ANALYSIS.md | ANALYSIS QA 리뷰 |
| tasks/024-dtp-mode-split-refactoring/PLAN.md | 구현 계획 |
| tasks/024-dtp-mode-split-refactoring/QA-PLAN.md | PLAN QA 리뷰 |
| tasks/024-dtp-mode-split-refactoring/TODO.md | 실행 체크리스트 (12/12 완료) |
| tasks/024-dtp-mode-split-refactoring/TEST-SCENARIO.md | 테스트 시나리오 + 실행 결과 |
| tasks/024-dtp-mode-split-refactoring/DONE.md | 완료 리포트 (본 문서) |
