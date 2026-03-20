# TASK: 서브에이전트 플랫폼별 모델 지정

> 작성일: 2026-03-20 | 작업 유형: 개선

## 작업 목표
모든 서브에이전트의 `model: inherit`를 각 에이전트의 역할 무게에 맞는 구체적 모델로 변경하고, 플랫폼별로 적절한 모델을 지정한다.

## 배경
현재 5개 서브에이전트(dtp-agent, dtp-qa, dtp-planner, dtp-test, wtm-worker)가 모두 `model: inherit`로 설정되어 있어, 세션의 기본 모델(예: Opus)을 그대로 사용한다. 경량 작업(QA 리뷰, URL 변환)에 고성능 모델을 쓰는 것은 비효율적이므로, 역할별로 적정 모델을 배정한다.

추가로, Claude Code에서는 Agent 도구 호출 시 model 파라미터로 오버라이드가 가능하므로, dtp-agent의 경우 dev-task-pilot 스킬에서 단계별로 다른 모델을 지정할 수 있다.

## 요구사항

### 1. 에이전트 파일 model 필드 변경 (3개 플랫폼)

대상 에이전트 및 모델 매핑:

| 에이전트 | 역할 무게 | Claude Code | Cursor | Antigravity |
|---------|----------|-------------|--------|-------------|
| dtp-agent | Heavy | `sonnet` | `claude-sonnet-4-6` | `gemini-3.1-pro` |
| dtp-planner | Heavy | `sonnet` | `claude-sonnet-4-6` | `gemini-3.1-pro` |
| dtp-test | Medium | `sonnet` | `claude-sonnet-4-6` | `gemini-3-flash` |
| dtp-qa | Light | `haiku` | `claude-haiku-4-5` | `gemini-3-flash` |
| wtm-worker | Light | `haiku` | `claude-haiku-4-5` | `gemini-3-flash` |

변경 대상 파일:
- [ ] `agents/claude/dtp-agent/AGENT.md` — model: sonnet
- [ ] `agents/claude/dtp-qa/AGENT.md` — model: haiku
- [ ] `agents/claude/dtp-planner/AGENT.md` — model: sonnet
- [ ] `agents/claude/dtp-test/AGENT.md` — model: sonnet
- [ ] `agents/claude/wtm-worker/AGENT.md` — model: haiku
- [ ] `agents/cursor/dtp-agent.md` — model: claude-sonnet-4-6
- [ ] `agents/cursor/dtp-qa.md` — model: claude-haiku-4-5
- [ ] `agents/cursor/dtp-planner.md` — model: claude-sonnet-4-6
- [ ] `agents/cursor/dtp-test.md` — model: claude-sonnet-4-6
- [ ] `agents/cursor/wtm-worker.md` — model: claude-haiku-4-5
- [ ] `agents/antigravity/dtp-agent/SKILL.md` — model: gemini-3.1-pro
- [ ] `agents/antigravity/dtp-qa/SKILL.md` — model: gemini-3-flash
- [ ] `agents/antigravity/dtp-planner/SKILL.md` — model: gemini-3.1-pro
- [ ] `agents/antigravity/dtp-test/SKILL.md` — model: gemini-3-flash
- [ ] `agents/antigravity/wtm-worker/SKILL.md` — model: gemini-3-flash

### 2. dev-task-pilot 단계별 모델 오버라이드 (Claude Code 전용)

dtp-agent는 기본 model: sonnet이지만, Claude Code에서 Agent 도구 호출 시 단계별로 오버라이드:

| 단계 | model 오버라이드 | 근거 |
|------|-----------------|------|
| ANALYSIS | `haiku` | 정보 수집·코드 읽기 중심 |
| PLAN | `sonnet` | 설계, 추론 필요 |
| TODO | `haiku` | 체크리스트 분해, 경량 |
| EXECUTE | `sonnet` | 코드 작성, 고성능 필요 |

변경 대상:
- [ ] `skills/dev-task-pilot/SKILL.md` — 워커 디스패치 규칙에 단계별 model 매핑 추가

## 제약 조건
- 호출 시 model 오버라이드는 Claude Code의 Agent 도구에서만 가능 (Cursor, Antigravity 불가)
- Cursor/Antigravity의 dtp-agent는 EXECUTE 기준으로 고정 모델 사용
- Antigravity 모델 ID는 실제 플랫폼에서 확인된 값 기준 (gemini-3.1-pro, gemini-3-flash)

## 관련 문서
- `agents/claude/` — Claude Code 에이전트 파일
- `agents/cursor/` — Cursor 에이전트 파일
- `agents/antigravity/` — Antigravity 에이전트 파일
- `skills/dev-task-pilot/SKILL.md` — 워커 디스패치 규칙
