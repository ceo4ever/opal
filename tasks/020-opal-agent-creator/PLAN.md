# PLAN: opal-agent-creator 스킬 생성

> 작성일: 2026-03-20 | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/opal-skill-creator/SKILL.md` | 동일 패턴 참조 (Phase 1→2 파이프라인) | X |
| `/tmp/taches-cc-resources/skills/create-subagents/SKILL.md` | Phase 1 위임 대상 (래핑) | X |
| `/tmp/taches-cc-resources/skills/create-subagents/references/*.md` (7개) | 에이전트 설계 방법론 | X |
| `agents/claude/dtp-agent/AGENT.md` | Claude 에이전트 형식 참조 | X |
| `agents/cursor/dtp-agent.md` | Cursor 에이전트 형식 참조 | X |
| `agents/antigravity/dtp-agent/SKILL.md` | Antigravity 에이전트 형식 참조 | X |
| `~/.opal/references/agents.md` | 에이전트 레지스트리 (등록 형식 참조) | X |
| `skills/version-mgr/SKILL.md` | 버전 관리 규칙 참조 | X |
| `skills/opal-agent-creator/SKILL.md` | **신규 생성** | O |
| `~/.opal/references/skills.md` | 레지스트리 등록 (EXECUTE 시) | O |

### 현재 구현

#### opal-skill-creator 패턴 (래핑 구조)

opal-skill-creator는 커뮤니티 skill-creator를 Phase 1으로 래핑하는 2단계 파이프라인이다.

- **진입 분기**: 신규 생성 모드 / 개선 모드
- **Phase 1**: skill-creator SKILL.md를 Read → 프로세스 위임 (Capture Intent → Interview → Write → Test → Improve)
  - OPAL 규칙(한국어 본문, 500줄 제한, references 분리)을 컨텍스트로 전달
- **Phase 2**: OPAL 후처리 5단계
  - 2-1. 디렉토리 구조 확정 (프레임워크 vs OPAL 전용)
  - 2-2. YAML frontmatter 보정 (name kebab-case, description 트리거 패턴)
  - 2-3. 레지스트리 등록 (`~/.opal/references/skills.md`)
  - 2-4. 버전 태깅 (version-mgr 규칙)
  - 2-5. 에이전트 생성 (선택, 3플랫폼)

opal-agent-creator는 이 구조를 거의 그대로 따르되, Phase 1 위임 대상이 create-subagents이고, Phase 2에서 에이전트 파일 생성이 "선택"이 아니라 "핵심"이 되는 차이가 있다.

#### create-subagents 커뮤니티 스킬

Claude Code 전용 에이전트 생성 가이드. 308줄 + references 7개.

- **진입점**: `/agents` 명령 → Create New Agent
- **생성 프로세스**: name → description → tools → model → system prompt 순서
- **frontmatter 필드**: `name`, `description`, `tools`, `model`, (선택) `color`
- **시스템 프롬프트**: XML 태그 구조 (`<role>`, `<workflow>`, `<constraints>`, `<output_format>`)
- **references 7개**: subagents.md, writing-subagent-prompts.md, orchestration-patterns.md, context-management.md, error-handling-and-recovery.md, evaluation-and-testing.md, debugging-agents.md

**한계**: Claude Code 단일 플랫폼만 지원. AGENT.md 형식만 생성.

#### 3플랫폼 에이전트 형식 비교

| 항목 | Claude (`AGENT.md`) | Cursor (`.md` flat) | Antigravity (`SKILL.md`) |
|------|---------------------|---------------------|--------------------------|
| **구조** | 디렉토리 기반 `agents/claude/{name}/AGENT.md` | 플랫 파일 `agents/cursor/{name}.md` | 스킬 통합 `agents/antigravity/{name}/SKILL.md` |
| **frontmatter** | name, description, model, color, tools | name, description, model, readonly, tools, max_turns, timeout_mins | name, description |
| **본문 차이** | 원본 그대로 | 원본 그대로 | "폴백 모드" 설명 추가, 도구명 변환 (Edit→write_file 등) |
| **고유 필드** | `color` (UI 색상) | `readonly`, `max_turns`, `timeout_mins` | 없음 (description에 폴백 설명) |
| **공통 필드** | name, description, model | name, description, model | name, description |

**핵심 변환 규칙** (Claude 원본 → 타 플랫폼):

1. **Claude → Cursor**: `color` 제거, `readonly: false` 추가, `max_turns`/`timeout_mins` 추가, `tools` 값을 Cursor 도구명으로 변환 (Read→read_file, Write→write_file, Edit→write_file, Bash→shell, Grep→grep_search, Glob→list_directory)
2. **Claude → Antigravity**: frontmatter를 name+description만 유지, description에 "서브 에이전트 미지원, 메인 에이전트가 Read하고 직접 실행" 안내 추가, 제목에 "(폴백 모드)" 추가, 도구명 본문 내 변환

#### agents.md 레지스트리 형식

섹션 기반 등록. 각 에이전트는 `### {name}` 헤딩 아래에 역할/호출 시점/입력/출력 4개 필드로 기술.

```markdown
### {agent-name}
- **역할**: {한줄 설명}
- **호출 시점**: {언제 호출되는지}
- **입력**: {필요한 입력}
- **출력**: {생성하는 산출물}
```

현재 dev-task-pilot 에이전트 섹션만 존재 (dtp-agent, dtp-qa, dtp-planner, dtp-test).

### 영향 범위

- **상위 의존 (이 스킬을 호출하는 쪽)**: OPAL 에이전트(알투)가 "에이전트 만들어줘" 요청 시 skills.md 레지스트리에서 매칭하여 호출
- **하위 의존 (이 스킬이 호출하는 쪽)**: create-subagents (Phase 1), version-mgr (Phase 2), doc-writer (규칙 참조)
- **공유 데이터**: `~/.opal/references/skills.md` (레지스트리 등록), `~/.opal/references/agents.md` (에이전트 레지스트리 등록)
- **관련 테스트**: 없음 (문서 기반 스킬)

---

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/opal-agent-creator/SKILL.md` | 신규 생성 -- 전체 파이프라인 스킬 정의 |

### 핵심 설계

#### SKILL.md 전체 구조

```
---
name: opal-agent-creator
description: |
  **OPAL 프레임워크 에이전트 생성 파이프라인**. create-subagents로 에이전트를 설계한 뒤...
  반드시 이 스킬을 사용해야 하는 상황: ...
---

# OPAL 프레임워크 에이전트 생성 파이프라인

## 의존 스킬
## 진입 분기 (신규 생성 / 개선)
## Phase 1: 에이전트 콘텐츠 생성 (create-subagents 위임)
## Phase 2: OPAL 규격 후처리
  ### 2-1. 3플랫폼 에이전트 파일 생성
  ### 2-2. YAML frontmatter 보정 (플랫폼별)
  ### 2-3. 에이전트 레지스트리 등록
  ### 2-4. 스킬 레지스트리 등록 (자기 자신)  ← EXECUTE 단계에서 수행
  ### 2-5. 버전 태깅
  ### 2-6. 탐색 경로 안내
## 완료 체크리스트
## 변경이력
```

#### Phase 1 상세 설계

opal-skill-creator와 동일한 위임 패턴. create-subagents SKILL.md를 Read → 프로세스 위임.

**신규 생성 모드**:
1. create-subagents의 프로세스 실행 (name → description → tools → model → system prompt)
2. OPAL 규칙을 컨텍스트로 전달:
   - 한국어 본문, 영어 코드/필드명
   - 시스템 프롬프트에 역할, 실행 프로세스, 반환 형식, 실행 규칙 포함
   - XML 태그 구조 또는 Markdown 구조 (에이전트 복잡도에 따라)
3. create-subagents의 references 7개를 설계 품질 참조로 활용

**개선 모드**:
1. 기존 에이전트 파일 3개(Claude/Cursor/Antigravity)를 Read
2. Claude 버전을 기준으로 create-subagents 개선 플로우 실행
3. 변경 사항을 3플랫폼에 동기 반영

**Phase 1 완료 조건**: Claude 형식의 AGENT.md 콘텐츠가 완성됨.

#### Phase 2 상세 설계 -- 핵심 차별점

##### 2-1. 3플랫폼 에이전트 파일 생성

Phase 1에서 완성된 Claude AGENT.md를 기준으로 3개 플랫폼 파일을 생성한다.

**생성 규칙**:

```
Claude 원본 (AGENT.md)
  ├─ 그대로 저장 → agents/claude/{name}/AGENT.md
  ├─ Cursor 변환 → agents/cursor/{name}.md
  └─ Antigravity 변환 → agents/antigravity/{name}/SKILL.md
```

**Claude → Cursor 변환 규칙**:
- frontmatter 변환:
  - `color` 필드 제거
  - `readonly: false` 추가
  - `max_turns: 50` 추가 (기본값)
  - `timeout_mins: 30` 추가 (기본값)
  - `tools` 값 변환: Read→read_file, Write→write_file, Edit→write_file, Bash→shell, Grep→grep_search, Glob→list_directory
- 본문: 그대로 유지

**Claude → Antigravity 변환 규칙**:
- frontmatter: name + description만 유지
  - description에 "Antigravity에서는 서브 에이전트 기능이 없으므로, 메인 에이전트가 이 SKILL.md를 Read하고 지시에 따라 직접 실행한다." 추가
- 파일명: SKILL.md (AGENT.md가 아님)
- 제목: "{원본 제목} (폴백 모드)" 추가
- 본문: 폴백 실행 방식 안내 1줄 추가 (blockquote)
- 도구 참조 본문 변환: Edit→write_file 등

##### 2-2. YAML frontmatter 플랫폼별 보정

| 필드 | Claude | Cursor | Antigravity |
|------|--------|--------|-------------|
| name | kebab-case | 동일 | 동일 |
| description | 역할 + 트리거 | 동일 | 동일 + 폴백 안내 |
| model | inherit/sonnet/opus/haiku | 동일 | 삭제 |
| color | 선택 (UI 색상) | 삭제 | 삭제 |
| tools | Claude 도구명 | Cursor 도구명 변환 | 삭제 |
| readonly | 삭제 | false | 삭제 |
| max_turns | 삭제 | 50 (기본) | 삭제 |
| timeout_mins | 삭제 | 30 (기본) | 삭제 |

##### 2-3. 에이전트 레지스트리 등록

`~/.opal/references/agents.md`에 항목 추가.

- **신규**: 적절한 섹션에 `### {name}` + 역할/호출시점/입력/출력 4필드 추가
  - 기존 "dev-task-pilot 에이전트" 섹션과 별도로, 에이전트가 속하는 워크플로우 섹션을 생성하거나 기존 섹션에 추가
- **개선**: 기존 항목의 역할/입출력이 변경되었으면 갱신

##### 2-4. 버전 태깅

version-mgr 규칙 적용:
- 신규: AGENT.md 상단 `> 작성일: {날짜} | 버전: v1.0` + 하단 변경이력 테이블
- 개선: Major/Minor 판단 → 새 버전 파일 생성 (기존 보존)
- 3개 플랫폼 파일 모두 동일 버전 부여

##### 2-5. 탐색 경로 안내

에이전트를 호출하는 스킬이 있으면, 해당 SKILL.md에 탐색 경로를 명시하도록 안내한다.

```
탐색 경로 (우선순위):
1. {프로젝트}/.cursor/agents/{name}.md
2. {프로젝트}/.claude/agents/{name}/AGENT.md
3. {프로젝트}/.agent/skills/{name}/SKILL.md
4. ~/.cursor/agents/{name}.md
5. ~/.claude/agents/{name}/AGENT.md
6. ~/.gemini/antigravity/skills/{name}/SKILL.md
```

#### 진입 분기 설계

```
사용자 요청 수신
  |
  +-- 새 에이전트 요청 ("에이전트 만들어줘", "생성", "추가") --> 신규 생성 모드
  |     +-- Phase 1: create-subagents (콘텐츠 설계)
  |     +-- Phase 2: OPAL 후처리 (3플랫폼 생성, 레지스트리, 버전)
  |
  +-- 기존 에이전트 개선 ("개선해줘", "수정해줘", 에이전트명 지정) --> 개선 모드
        +-- 기존 에이전트 3개 파일 로드
        +-- Phase 1: create-subagents improve 플로우
        +-- Phase 2: OPAL 후처리 (3플랫폼 동기, 레지스트리 갱신, 버전 증가)
```

#### 의존 스킬 테이블

| 스킬 | 역할 | 필수 |
|------|------|------|
| create-subagents | Phase 1 콘텐츠 생성 위임 | O |
| version-mgr | Phase 2 버전 태깅 | O |
| doc-writer | 문서 표준 규칙 참조 | O |

---

## 3. 실행 체크리스트

- [x] Step 1: SKILL.md 골격 작성 -- `skills/opal-agent-creator/SKILL.md` -- frontmatter(name, description) + 의존 스킬 + 진입 분기 섹션 작성
- [x] Step 2: Phase 1 섹션 작성 -- `skills/opal-agent-creator/SKILL.md` -- create-subagents 위임 프로세스 (신규/개선 모드), OPAL 컨텍스트 전달 규칙, references 7개 활용 안내
- [x] Step 3: Phase 2 섹션 작성 -- `skills/opal-agent-creator/SKILL.md` -- 2-1 3플랫폼 파일 생성 (변환 규칙 테이블 포함), 2-2 frontmatter 보정, 2-3 에이전트 레지스트리 등록, 2-4 버전 태깅, 2-5 탐색 경로 안내
- [x] Step 4: 완료 체크리스트 + 변경이력 작성 -- `skills/opal-agent-creator/SKILL.md` -- 검증 항목, 완료 보고 형식, 변경이력 테이블 (v1.0)
- [x] Step 5: skills.md 레지스트리 등록 -- `~/.opal/references/skills.md` -- 프레임워크 스킬 섹션에 opal-agent-creator 항목 추가

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] SKILL.md가 `skills/opal-agent-creator/SKILL.md`에 존재하는가
- [ ] Phase 1에서 create-subagents 탐색 경로가 명시되어 있는가 (`~/.opal/community-skills/` 하위)
- [ ] Phase 2의 3플랫폼 변환 규칙이 구체적인가 (Claude→Cursor, Claude→Antigravity 각각의 frontmatter 매핑과 본문 변환)
- [ ] 에이전트 레지스트리(`agents.md`) 등록 형식이 기존 형식과 일치하는가 (역할/호출시점/입력/출력)
- [ ] 신규 생성 모드와 개선 모드가 모두 정의되어 있는가
- [ ] version-mgr 규칙(v{Major}.{Minor}, 변경이력 테이블)이 반영되어 있는가
- [ ] 완료 체크리스트가 모든 Phase 2 항목을 커버하는가

### 회귀 테스트

- [ ] opal-skill-creator와 구조적 일관성이 유지되는가 (Phase 1→2 파이프라인, 의존 스킬, 진입 분기)
- [ ] create-subagents 원본을 수정하지 않고 래핑만 하는가
- [ ] 기존 agents.md 레지스트리의 형식을 깨뜨리지 않는가

### 코드 품질

- [ ] SKILL.md가 500줄 이하인가
- [ ] 한국어 본문 / 영어 코드 규칙을 준수하는가
- [ ] frontmatter의 name이 kebab-case이고 디렉토리명과 일치하는가
- [ ] description에 "반드시 이 스킬을 사용해야 하는 상황:" 패턴이 포함되어 있는가
- [ ] skills.md 레지스트리에 항목이 올바른 형식으로 등록되었는가
