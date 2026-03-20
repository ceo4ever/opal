# DONE: 서브에이전트 플랫폼별 모델 지정

> 완료일: 2026-03-20 | 모드: Short Task | 작업 유형: 개선

## 완료 요약
5개 서브에이전트의 `model: inherit`를 역할 무게에 맞는 구체적 모델로 변경하고, 3개 플랫폼(Claude Code, Cursor, Antigravity)별로 적정 모델을 배정했다. 추가로 dev-task-pilot에서 dtp-agent 호출 시 단계별 model 오버라이드 규칙을 추가했다.

## 변경 파일
| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `agents/claude/dtp-agent/AGENT.md` | model: inherit → sonnet |
| 2 | `agents/claude/dtp-qa/AGENT.md` | model: inherit → haiku |
| 3 | `agents/claude/dtp-planner/AGENT.md` | model: inherit → sonnet |
| 4 | `agents/claude/dtp-test/AGENT.md` | model: inherit → sonnet |
| 5 | `agents/claude/wtm-worker/AGENT.md` | model: inherit → haiku |
| 6 | `agents/cursor/dtp-agent.md` | model: inherit → claude-sonnet-4-6 |
| 7 | `agents/cursor/dtp-qa.md` | model: inherit → claude-haiku-4-5 |
| 8 | `agents/cursor/dtp-planner.md` | model: inherit → claude-sonnet-4-6 |
| 9 | `agents/cursor/dtp-test.md` | model: inherit → claude-sonnet-4-6 |
| 10 | `agents/cursor/wtm-worker.md` | model: inherit → claude-haiku-4-5 |
| 11 | `agents/antigravity/dtp-agent/SKILL.md` | model: gemini-3.1-pro 추가 |
| 12 | `agents/antigravity/dtp-qa/SKILL.md` | model: inherit → gemini-3-flash |
| 13 | `agents/antigravity/dtp-planner/SKILL.md` | model: gemini-3.1-pro 추가 |
| 14 | `agents/antigravity/dtp-test/SKILL.md` | model: gemini-3-flash 추가 |
| 15 | `agents/antigravity/wtm-worker/SKILL.md` | model: gemini-3-flash 추가 |
| 16 | `skills/dev-task-pilot/SKILL.md` | 단계별 model 오버라이드 규칙 추가 |

## 핵심 변경 사항
### Before
모든 서브에이전트가 `model: inherit`로 설정되어, 세션 기본 모델(Opus 등)을 그대로 상속받아 경량 작업에도 고성능 모델을 사용하는 비효율 발생.

### After
에이전트 역할 무게에 따라 3단계 모델 배정:
- **Heavy** (dtp-agent, dtp-planner): sonnet / claude-sonnet-4-6 / gemini-3.1-pro
- **Medium** (dtp-test): sonnet / claude-sonnet-4-6 / gemini-3-flash
- **Light** (dtp-qa, wtm-worker): haiku / claude-haiku-4-5 / gemini-3-flash

Claude Code에서는 dtp-agent 호출 시 단계별 오버라이드 가능 (ANALYSIS/TODO=haiku, PLAN/EXECUTE=sonnet).

## 테스트 결과
All Pass — 시나리오 5/5 Pass, 코드 품질 3/3 Pass, 회귀 테스트 2/2 Pass, 보안 Pass.

## 산출물 목록
| 파일 | 설명 |
|------|------|
| `tasks/022-subagent-model-assignment/TASK.md` | 작업 정의서 |
| `tasks/022-subagent-model-assignment/PLAN.md` | 통합 PLAN (코드 분석 + 구현 계획 + 체크리스트) |
| `tasks/022-subagent-model-assignment/QA-PLAN.md` | PLAN QA 리뷰 |
| `tasks/022-subagent-model-assignment/TEST-SCENARIO.md` | 테스트 시나리오 + 실행 결과 |
| `tasks/022-subagent-model-assignment/DONE.md` | 완료 리포트 |
