---
name: opal-agent-creator
description: |
  **OPAL 프레임워크 에이전트 생성 파이프라인**. create-subagents로 에이전트를 설계한 뒤, OPAL 규격 후처리(3플랫폼 파일 생성, 레지스트리 등록, 버전 태깅)를 자동 수행합니다.
  반드시 이 스킬을 사용해야 하는 상황: "에이전트 만들어줘", "에이전트 생성", "서브에이전트 추가", "에이전트 작성해줘", "에이전트 개선해줘", 기존 에이전트 수정/개선 요청 시, "에이전트 만들고 등록해줘", "OPAL 에이전트 추가".
  커뮤니티 create-subagents를 래핑하여 OPAL 프레임워크 규격을 자동 적용합니다. 단순히 에이전트 콘텐츠만 만드는 것이 아니라, 3플랫폼 파일 배치, 레지스트리 등록, 버전 태깅까지 한 번에 완료합니다.
---

# OPAL 프레임워크 에이전트 생성 파이프라인

> 작성일: 2026-03-20 | 버전: v1.0

create-subagents 커뮤니티 스킬로 에이전트 콘텐츠를 설계한 뒤, OPAL 프레임워크 규격에 맞는 후처리를 자동 수행하는 2단계 파이프라인이다.

## 의존 스킬

| 스킬 | 역할 | 필수 |
|------|------|------|
| create-subagents | Phase 1 콘텐츠 생성 위임 | O |
| version-mgr | Phase 2 버전 태깅 | O |
| doc-writer | 문서 표준 규칙 참조 | O |

## 진입 분기

사용자 요청을 분석하여 모드를 결정한다.

```
사용자 요청 수신
  |
  +-- 새 에이전트 요청 ("만들어줘", "생성", "추가") --> 신규 생성 모드
  |     +-- Phase 1: create-subagents (콘텐츠 설계)
  |     +-- Phase 2: OPAL 후처리
  |
  +-- 기존 에이전트 개선 ("개선해줘", "수정해줘", 에이전트명 지정) --> 개선 모드
        +-- 기존 에이전트 3개 파일 로드
        +-- Phase 1: create-subagents improve 플로우
        +-- Phase 2: OPAL 후처리 (3플랫폼 동기, 레지스트리 갱신, 버전 증가)
```

---

## Phase 1: 에이전트 콘텐츠 생성 (create-subagents 위임)

create-subagents 커뮤니티 스킬의 프로세스를 따라 에이전트 콘텐츠를 설계한다. create-subagents 자체를 수정하지 않는다.

### 실행 방법

1. create-subagents SKILL.md를 Read로 읽는다.
   - 탐색 경로: `~/.opal/community-skills/create-subagents/SKILL.md`
   - 대체 경로: `~/.opal/community-skills/glittercowboy/create-subagents/SKILL.md`

2. create-subagents의 references 7개를 설계 품질 참조로 활용한다.
   - `references/subagents.md` -- 파일 형식, 모델 선택, 도구 보안
   - `references/writing-subagent-prompts.md` -- 프롬프트 작성, XML 구조
   - `references/orchestration-patterns.md` -- 순차/병렬/계층 패턴
   - `references/context-management.md` -- 메모리 아키텍처, 컨텍스트 전략
   - `references/error-handling-and-recovery.md` -- 실패 모드, 복구 전략
   - `references/evaluation-and-testing.md` -- 평가 메트릭, 테스트 전략
   - `references/debugging-agents.md` -- 로깅, 진단 절차

3. create-subagents의 프로세스를 순서대로 따른다.

### 신규 생성 모드

create-subagents의 전체 프로세스를 실행한다:

1. **name** -- kebab-case, `{워크플로우}-{역할}` 패턴 권장 (예: `dtp-qa`, `wtm-worker`)
2. **description** -- 역할 + 언제 호출되는지 기술
3. **tools** -- 최소 권한 원칙 적용 (Read, Write, Edit, Bash, Grep, Glob 중 필요한 것만)
4. **model** -- 복잡도에 따라 선택 (opus: 복잡 추론, sonnet: 범용, haiku: 단순 작업)
5. **system prompt** -- 역할, 실행 프로세스, 반환 형식, 실행 규칙 포함

단, 에이전트 작성 시 아래 OPAL 규칙을 create-subagents에 컨텍스트로 전달한다:

- 한국어 본문, 영어 코드/필드명 (doc-writer 규칙)
- 명령형(imperative) 문체
- 시스템 프롬프트에 역할, 실행 프로세스, 반환 형식, 실행 규칙 필수 포함
- XML 태그 구조 또는 Markdown 구조 (에이전트 복잡도에 따라 선택)

### 개선 모드

1. 기존 에이전트의 Claude 버전(`agents/claude/{name}/AGENT.md`)을 Read로 로드한다.
2. create-subagents의 설계 원칙을 참조하여 개선 플로우를 실행한다.
3. 사용자 피드백에 따라 반복 개선한다.

### Phase 1 완료 조건

- Claude 형식의 AGENT.md 콘텐츠가 완성되었다.
- frontmatter(name, description, model, tools)와 본문(system prompt)이 모두 확정되었다.

---

## Phase 2: OPAL 규격 후처리

Phase 1에서 완성된 Claude AGENT.md를 기준으로 3플랫폼 파일 생성 및 후처리를 수행한다. 아래 5개 항목을 순차 수행한다.

### 2-1. 3플랫폼 에이전트 파일 생성

Phase 1에서 완성된 Claude AGENT.md를 기준으로 3개 플랫폼 파일을 생성한다.

```
Claude 원본 (AGENT.md)
  +-- 그대로 저장 --> agents/claude/{name}/AGENT.md
  +-- Cursor 변환 --> agents/cursor/{name}.md
  +-- Antigravity 변환 --> agents/antigravity/{name}/SKILL.md
```

#### Claude -> Cursor 변환 규칙

frontmatter 변환:

| Claude 필드 | Cursor 변환 |
|-------------|------------|
| `name` | 그대로 유지 |
| `description` | 그대로 유지 |
| `model` | 그대로 유지 |
| `color` | **삭제** |
| `tools` | 도구명 변환 (아래 테이블) |
| -- | `readonly: false` **추가** |
| -- | `max_turns: 50` **추가** |
| -- | `timeout_mins: 30` **추가** |

도구명 변환 테이블:

| Claude | Cursor |
|--------|--------|
| Read | read_file |
| Write | write_file |
| Edit | write_file |
| Bash | shell |
| Grep | grep_search |
| Glob | list_directory |

본문: 그대로 유지한다.

#### Claude -> Antigravity 변환 규칙

frontmatter 변환:
- `name` + `description`만 유지한다.
- `description`에 다음 문구를 추가한다: "Antigravity에서는 서브 에이전트 기능이 없으므로, 메인 에이전트가 이 SKILL.md를 Read하고 지시에 따라 직접 실행한다."
- `model`, `color`, `tools` 등 나머지 필드를 삭제한다.

파일 변환:
- 파일명을 `SKILL.md`로 변경한다 (AGENT.md가 아님).
- 제목에 "(폴백 모드)"를 추가한다.
- 제목 아래에 폴백 실행 방식 안내를 blockquote로 추가한다:
  ```
  > **실행 방식**: Antigravity에서는 서브 에이전트가 지원되지 않으므로, 메인 에이전트가 이 파일을 Read한 후 아래 프로세스를 직접 수행한다. 컨텍스트 격리 이점은 없으나, 동일한 절차와 규칙이 적용된다.
  ```
- 본문 내 도구 참조를 변환한다: Edit -> write_file 등.

### 2-2. YAML frontmatter 보정

3플랫폼 파일의 frontmatter가 규격에 맞는지 검증하고 보정한다.

| 필드 | Claude | Cursor | Antigravity |
|------|--------|--------|-------------|
| name | kebab-case | 동일 | 동일 |
| description | 역할 + 트리거 | 동일 | 동일 + 폴백 안내 |
| model | inherit/sonnet/opus/haiku | 동일 | 삭제 |
| color | 선택 (UI 색상) | 삭제 | 삭제 |
| tools | Claude 도구명 | Cursor 도구명 변환 | 삭제 |
| readonly | -- | false | -- |
| max_turns | -- | 50 (기본) | -- |
| timeout_mins | -- | 30 (기본) | -- |

검증 항목:
- `name`이 kebab-case이고 디렉토리명과 일치하는가
- `description`에 역할과 호출 시점이 명시되어 있는가
- 플랫폼별 고유 필드가 올바르게 적용되었는가

### 2-3. 에이전트 레지스트리 등록

`~/.opal/references/agents.md`에 항목을 추가한다.

**신규 생성 모드:**

에이전트가 속하는 워크플로우 섹션에 항목을 추가한다. 적절한 섹션이 없으면 새 섹션을 생성한다.

등록 형식:
```markdown
### {agent-name}

- **역할**: {한줄 설명}
- **호출 시점**: {언제 호출되는지}
- **입력**: {필요한 입력}
- **출력**: {생성하는 산출물}
```

**개선 모드:**

기존 항목의 역할/입출력이 변경되었으면 갱신한다. 변경이 없으면 그대로 둔다.

### 2-4. 버전 태깅

version-mgr 스킬의 규칙을 따른다.

**신규 생성 모드:**
- AGENT.md 상단에 메타정보를 추가한다:
  ```
  > 작성일: {오늘 날짜} | 버전: v1.0
  ```
- 3개 플랫폼 파일 모두 동일 버전을 부여한다.

**개선 모드:**
- 변경 범위를 파악하여 Major/Minor를 결정한다.
  - 구조적 변경 (역할 재정의, 프로세스 추가/삭제): Major 증가
  - 내용 수정 (기존 프로세스 수정, 버그 수정): Minor 증가
- 3개 플랫폼 파일 모두 동일 버전으로 갱신한다.

### 2-5. 탐색 경로 안내

에이전트를 호출하는 스킬이 있으면, 해당 SKILL.md에 탐색 경로를 명시하도록 안내한다.

```
탐색 경로 (우선순위):
1. {프로젝트}/.cursor/agents/{name}.md
2. {프로젝트}/.cursor/agents/{name}/AGENT.md
3. {프로젝트}/.claude/agents/{name}/AGENT.md
4. {프로젝트}/.agent/skills/{name}/SKILL.md
5. ~/.cursor/agents/{name}.md
6. ~/.cursor/agents/{name}/AGENT.md
7. ~/.claude/agents/{name}/AGENT.md
8. ~/.gemini/antigravity/skills/{name}/SKILL.md
```

사용자에게 호출하는 스킬의 SKILL.md 경로를 확인하고, 해당 파일에 위 탐색 경로를 추가하도록 안내한다.

---

## 완료 체크리스트

Phase 2 완료 후 아래 항목을 검증한다:

- [ ] Claude AGENT.md가 `agents/claude/{name}/AGENT.md`에 저장되었는가
- [ ] Cursor 파일이 `agents/cursor/{name}.md`에 저장되었는가
- [ ] Antigravity SKILL.md가 `agents/antigravity/{name}/SKILL.md`에 저장되었는가
- [ ] 3플랫폼 파일의 frontmatter가 각 플랫폼 규격에 맞는가
- [ ] `~/.opal/references/agents.md`에 항목이 등록되었는가
- [ ] 버전 태깅이 적용되었는가 (3플랫폼 동일 버전)
- [ ] name이 kebab-case이고 `{워크플로우}-{역할}` 패턴을 따르는가
- [ ] 한국어 본문 / 영어 코드 규칙을 준수하는가

모든 항목이 통과하면 사용자에게 결과를 보고한다:

```
[opal-agent-creator 완료]
- 에이전트: {name}
- Claude: agents/claude/{name}/AGENT.md
- Cursor: agents/cursor/{name}.md
- Antigravity: agents/antigravity/{name}/SKILL.md
- 버전: v{버전}
- 레지스트리: 등록 완료
- 호출 스킬: {탐색 경로 안내 완료 / 해당 없음}
```

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-20 | 초기 작성 |
