# PLAN: 서브에이전트 플랫폼별 모델 지정

> 작성일: 2026-03-20 | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `agents/claude/dtp-agent/AGENT.md` | Claude Code dtp-agent 에이전트 | O |
| `agents/claude/dtp-qa/AGENT.md` | Claude Code dtp-qa 에이전트 | O |
| `agents/claude/dtp-planner/AGENT.md` | Claude Code dtp-planner 에이전트 | O |
| `agents/claude/dtp-test/AGENT.md` | Claude Code dtp-test 에이전트 | O |
| `agents/claude/wtm-worker/AGENT.md` | Claude Code wtm-worker 에이전트 | O |
| `agents/cursor/dtp-agent.md` | Cursor dtp-agent 에이전트 | O |
| `agents/cursor/dtp-qa.md` | Cursor dtp-qa 에이전트 | O |
| `agents/cursor/dtp-planner.md` | Cursor dtp-planner 에이전트 | O |
| `agents/cursor/dtp-test.md` | Cursor dtp-test 에이전트 | O |
| `agents/cursor/wtm-worker.md` | Cursor wtm-worker 에이전트 | O |
| `agents/antigravity/dtp-agent/SKILL.md` | Antigravity dtp-agent 스킬 | O |
| `agents/antigravity/dtp-qa/SKILL.md` | Antigravity dtp-qa 스킬 | O |
| `agents/antigravity/dtp-planner/SKILL.md` | Antigravity dtp-planner 스킬 | O |
| `agents/antigravity/dtp-test/SKILL.md` | Antigravity dtp-test 스킬 | O |
| `agents/antigravity/wtm-worker/SKILL.md` | Antigravity wtm-worker 스킬 | O |
| `skills/dev-task-pilot/SKILL.md` | 오케스트레이터 스킬 (워커 디스패치 규칙) | O |

### 현재 구현

**에이전트 파일 frontmatter 구조**: 모든 에이전트 파일의 YAML frontmatter에 `model` 필드가 존재하며, 현재 값은 전부 `inherit`이다.

- **Claude Code** (`agents/claude/*/AGENT.md`): 5개 파일 모두 `model: inherit`. frontmatter에 `name`, `description`, `model`, `color` 필드 사용.
- **Cursor** (`agents/cursor/*.md`): 5개 파일 모두 `model: inherit`. frontmatter에 `name`, `description`, `model`, `readonly`, `tools`, `max_turns`, `timeout_mins` 등 사용.
- **Antigravity** (`agents/antigravity/*/SKILL.md`): dtp-qa만 `model: inherit` 필드가 있고, 나머지 4개(dtp-agent, dtp-planner, dtp-test, wtm-worker)는 frontmatter에 model 필드 자체가 없다.

**dev-task-pilot SKILL.md 워커 디스패치 규칙** (130~163행): 디스패치 시점, 프롬프트 구성, 단계별 이전 산출물 매핑이 정의되어 있으나, model 지정 관련 규칙은 현재 없다. Claude Code의 Agent 도구는 `model` 파라미터를 지원하므로 디스패치 시 오버라이드가 가능하다.

### 영향 범위

**호출자**: dev-task-pilot SKILL.md의 오케스트레이터가 각 에이전트를 호출할 때 model 필드를 참조한다.
- Claude Code: Agent 도구 호출 시 `model` 파라미터로 에이전트 기본 model을 오버라이드 가능
- Cursor: 서브 에이전트 호출 시 에이전트 파일의 `model` 필드를 참조
- Antigravity: 폴백 모드(직접 실행)이므로 model 필드는 가이드용

**피호출자**: 에이전트 파일 자체는 정의 문서로, 다른 코드에 의존하지 않는다.

**설치 스크립트 영향**: `install-mac.sh`가 소스에서 배포 경로로 복사하므로, 소스 변경 후 재설치가 필요하다. 그러나 설치 스크립트 자체의 변경은 불필요하다.

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `agents/claude/dtp-agent/AGENT.md` | frontmatter `model: inherit` → `model: sonnet` |
| 2 | `agents/claude/dtp-qa/AGENT.md` | frontmatter `model: inherit` → `model: haiku` |
| 3 | `agents/claude/dtp-planner/AGENT.md` | frontmatter `model: inherit` → `model: sonnet` |
| 4 | `agents/claude/dtp-test/AGENT.md` | frontmatter `model: inherit` → `model: sonnet` |
| 5 | `agents/claude/wtm-worker/AGENT.md` | frontmatter `model: inherit` → `model: haiku` |
| 6 | `agents/cursor/dtp-agent.md` | frontmatter `model: inherit` → `model: claude-sonnet-4-6` |
| 7 | `agents/cursor/dtp-qa.md` | frontmatter `model: inherit` → `model: claude-haiku-4-5` |
| 8 | `agents/cursor/dtp-planner.md` | frontmatter `model: inherit` → `model: claude-sonnet-4-6` |
| 9 | `agents/cursor/dtp-test.md` | frontmatter `model: inherit` → `model: claude-sonnet-4-6` |
| 10 | `agents/cursor/wtm-worker.md` | frontmatter `model: inherit` → `model: claude-haiku-4-5` |
| 11 | `agents/antigravity/dtp-agent/SKILL.md` | frontmatter에 `model: gemini-3.1-pro` 추가 |
| 12 | `agents/antigravity/dtp-qa/SKILL.md` | frontmatter `model: inherit` → `model: gemini-3-flash` |
| 13 | `agents/antigravity/dtp-planner/SKILL.md` | frontmatter에 `model: gemini-3.1-pro` 추가 |
| 14 | `agents/antigravity/dtp-test/SKILL.md` | frontmatter에 `model: gemini-3-flash` 추가 |
| 15 | `agents/antigravity/wtm-worker/SKILL.md` | frontmatter에 `model: gemini-3-flash` 추가 |
| 16 | `skills/dev-task-pilot/SKILL.md` | 워커 디스패치 규칙에 단계별 model 매핑 테이블 추가 |

### 핵심 설계

#### 에이전트 파일 frontmatter 변경

단순 값 교체. Claude Code와 Cursor는 기존 `model: inherit`를 목표 값으로 교체. Antigravity는 model 필드가 없는 파일(4개)에 `model:` 행을 추가하고, dtp-qa(1개)는 기존 값을 교체.

Antigravity model 필드 추가 위치: frontmatter `description:` 블록 종료 직후, `---` 닫힘 태그 직전. dtp-agent는 description 뒤에 바로 `---`이므로 그 사이에 삽입.

#### dev-task-pilot SKILL.md 단계별 model 오버라이드 규칙

"워커 디스패치 규칙" 섹션(130행 부근)의 프롬프트 구성 블록 아래에 다음 테이블을 추가:

```markdown
**단계별 model 오버라이드 (Claude Code 전용)**:

dtp-agent의 기본 model은 sonnet이지만, Claude Code에서 Agent 도구 호출 시 단계에 따라 오버라이드한다:

| 단계 | model | 근거 |
|------|-------|------|
| ANALYSIS | `haiku` | 정보 수집·코드 읽기 중심 |
| PLAN | `sonnet` | 설계, 추론 필요 (기본값과 동일) |
| TODO | `haiku` | 체크리스트 분해, 경량 |
| EXECUTE | `sonnet` | 코드 작성, 고성능 필요 (기본값과 동일) |

> Cursor, Antigravity에서는 호출 시 model 오버라이드가 불가하므로, 에이전트 파일의 기본 model을 사용한다. dtp-agent는 EXECUTE 기준(가장 높은 요구)으로 고정.
```

삽입 위치: 163행(프롬프트 구성 코드블록 닫힘) 직후, "단계별 이전 산출물 매핑:" 직전.

## 3. 실행 체크리스트

- [x] Step 1: Claude Code 에이전트 model 변경 — `agents/claude/` 5개 파일 — frontmatter `model: inherit`를 각각 sonnet/haiku로 교체
- [x] Step 2: Cursor 에이전트 model 변경 — `agents/cursor/` 5개 파일 — frontmatter `model: inherit`를 각각 claude-sonnet-4-6/claude-haiku-4-5로 교체
- [x] Step 3: Antigravity 에이전트 model 추가/변경 — `agents/antigravity/` 5개 파일 — model 필드 추가(4개) 또는 교체(1개), gemini-3.1-pro/gemini-3-flash
- [x] Step 4: dev-task-pilot SKILL.md에 단계별 model 오버라이드 규칙 추가 — `skills/dev-task-pilot/SKILL.md` — 워커 디스패치 규칙 섹션에 테이블 삽입

## 4. QA 체크리스트

### 기능 테스트
- [x] Claude Code 5개 에이전트 파일의 model 값이 TASK.md 매핑과 일치하는가
- [x] Cursor 5개 에이전트 파일의 model 값이 TASK.md 매핑과 일치하는가
- [x] Antigravity 5개 에이전트 파일의 model 값이 TASK.md 매핑과 일치하는가
- [x] dev-task-pilot SKILL.md에 단계별 model 오버라이드 테이블이 정확한가

### 회귀 테스트
- [x] 변경된 파일의 YAML frontmatter 구조가 유효한가 (--- 구분자, 들여쓰기)
- [x] frontmatter 외의 에이전트 본문 내용이 변경되지 않았는가
- [x] SKILL.md의 기존 워커 디스패치 규칙이 훼손되지 않았는가

### 코드 품질
- [x] Antigravity 파일의 model 필드 위치가 다른 플랫폼과 일관적인가 (description 뒤)
- [x] 오버라이드 테이블이 "Cursor/Antigravity 불가" 제약 조건을 명시하는가
