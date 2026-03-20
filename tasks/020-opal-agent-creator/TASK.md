# TASK: opal-agent-creator 스킬 생성

> 작성일: 2026-03-20 | 작업 유형: 신규

## 작업 목표

glittercowboy/create-subagents 커뮤니티 스킬을 Phase 1으로 래핑하고, OPAL 프레임워크 규격 후처리(3플랫폼 에이전트 파일 생성, 레지스트리 등록, 버전 태깅)를 Phase 2로 자동 수행하는 파이프라인 스킬을 만든다.

## 배경

현재 OPAL 프레임워크에서 새 에이전트를 만들려면:
1. 에이전트 콘텐츠(역할, 프로세스, 입출력)를 설계하고
2. 3개 플랫폼별로 수동으로 파일을 생성해야 한다:
   - `agents/claude/{name}/AGENT.md` (디렉토리 기반)
   - `agents/cursor/{name}.md` (플랫 파일)
   - `agents/antigravity/{name}/SKILL.md` (스킬 통합)
3. `~/.opal/references/agents.md` 레지스트리에 수동 등록

opal-skill-creator(태스크 018)와 동일한 패턴으로, 에이전트 생성도 자동화한다.

## 커뮤니티 스킬 비교 결과

### 후보 스킬 비교

| 항목 | glittercowboy/create-subagents | tech-leads-club/subagent-creator |
|------|------|------|
| **분량** | SKILL.md 308줄 + references 7개 | SKILL.md 305줄 단독 |
| **플랫폼** | Claude Code 전용 | 플랫폼 무관 (agent-agnostic) |
| **구조** | XML 태그 기반 (`<role>`, `<workflow>`) | Markdown 기반 |
| **생성 프로세스** | `/agents` 명령 연동 + 가이드 | 4단계 (Purpose → Metadata → Prompt → Checklist) |
| **references** | 7개 (오케스트레이션, 디버깅, 에러처리, 컨텍스트 관리 등) | 없음 |
| **패턴 예시** | 1개 (code-reviewer) | 4개 (verifier, debugger, security-auditor, code-reviewer) |
| **frontmatter** | name, description, tools, model, color | name, description, model, readonly |

### 선정: glittercowboy/create-subagents

- references 7개가 에이전트 설계 방법론을 깊이 있게 다룸 (오케스트레이션, 에러처리, 컨텍스트 관리, 프롬프트 작성, 평가/테스트, 디버깅)
- Claude Code 네이티브라 AGENT.md frontmatter 호환성이 높음 (color, tools 등)
- 다만 Claude Code 단일 플랫폼이므로, Phase 2에서 3플랫폼 확장이 우리의 차별점
- 소스 경로: `/tmp/taches-cc-resources/skills/create-subagents/`

### 미선정: tech-leads-club/subagent-creator

- 플랫폼 무관하지만 references가 없어 가이드 깊이가 얕음
- 패턴 예시는 많지만 실질적 생성 프로세스가 단순

### 참고: Claude Code 빌트인 /agents 명령어

Claude Code에는 `/agents` 빌트인 CLI 명령어가 있어 인터랙티브하게 에이전트를 생성할 수 있다:
- Create new agent 선택 → 이름, 설명, 도구, 모델, 색상, 시스템 프롬프트 순서로 입력
- `~/.claude/agents/{name}/AGENT.md` 또는 `.claude/agents/{name}/AGENT.md` 생성
- glittercowboy/create-subagents가 이 명령어를 활용하는 가이드 역할

Anthropic 공식 커뮤니티 스킬(anthropics/*)에는 에이전트 생성 전용 스킬이 없다 (skill-creator만 있음).

## 요구사항

- [ ] glittercowboy/create-subagents를 Phase 1(에이전트 콘텐츠 생성)으로 활용
- [ ] Phase 2에서 OPAL 프레임워크 후처리를 자동 수행:
  - [ ] 3플랫폼 에이전트 파일 자동 생성 (Claude/Cursor/Antigravity)
  - [ ] 플랫폼별 형식 변환 (AGENT.md → .md 플랫 파일 → SKILL.md 통합)
  - [ ] `~/.opal/references/agents.md` 레지스트리 등록
  - [ ] version-mgr 초기 버전(v1.0) 태깅
  - [ ] 호출하는 스킬의 SKILL.md에 에이전트 탐색 경로 명시 안내
- [ ] 기존 에이전트 수정/개선 시에도 사용 가능
- [ ] 프레임워크 스킬로 배치 (`skills/opal-agent-creator/SKILL.md`)
- [ ] create-subagents의 references 7개를 활용하여 에이전트 설계 품질 확보

## 제약 조건

- create-subagents 커뮤니티 스킬 자체를 수정하지 않는다 (래핑만)
- 기존 스킬 간 의존 관계를 준수한다 (doc-writer, version-mgr)
- 3개 플랫폼(Claude Code, Cursor, Gemini/Antigravity)에서 동작해야 한다
- opal-skill-creator와 일관된 패턴(Phase 1 → Phase 2 파이프라인)을 유지한다

## 관련 문서

- `/tmp/taches-cc-resources/skills/create-subagents/SKILL.md` — create-subagents 커뮤니티 스킬
- `/Volumes/Data/AIStudio/workspace/ai-framework/skills/opal-skill-creator/SKILL.md` — opal-skill-creator (동일 패턴 참조)
- `/Volumes/Data/AIStudio/workspace/ai-framework/CLAUDE.md` — 프레임워크 아키텍처 및 Agent 추가 가이드
- `~/.opal/references/agents.md` — 에이전트 레지스트리
- `/Volumes/Data/AIStudio/workspace/ai-framework/agents/` — 기존 에이전트 3플랫폼 구조 참조
