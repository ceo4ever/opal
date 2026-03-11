# RESEARCH: Antigravity 플랫폼 지원 추가 및 QA 호출 구조 개선

> 작성일: 2026-03-07 | 참조: TASK.md

## 1. 기존 코드 분석

### 관련 파일 목록

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `claude/skills/task-flow/SKILL.md` | task-flow 핵심 스킬 (QA/Planner/Test 에이전트 탐색 경로 포함) | 수정 — 에이전트 탐색 경로에 Antigravity/Cursor 플랫 경로 추가, QA 호출 강조 |
| `claude/skills/task-flow/references/research-guide.md` | RESEARCH 상세 가이드 | 수정 — QA 에이전트 호출 단계 추가 |
| `claude/skills/task-flow/references/plan-guide.md` | PLAN 상세 가이드 | 수정 — QA 에이전트 호출 단계 추가 |
| `claude/skills/task-flow/references/todo-guide.md` | TODO 상세 가이드 | 수정 — QA 에이전트 호출 단계 추가 |
| `claude/skills/task-flow/references/execute-guide.md` | EXECUTE 상세 가이드 | 수정 — QA 에이전트 호출 단계 추가 |
| `claude/skills/task-flow/references/execute-plan-guide.md` | Planner 에이전트 상세 가이드 | 확인 — QA 관련 없으므로 수정 불필요 |
| `claude/agents/task-flow-qa/AGENT.md` | QA 에이전트 정의 | 수정 — "자동 호출" 표현 수정 |
| `claude/agents/task-flow-planner/AGENT.md` | Planner 에이전트 정의 | 없음 |
| `claude/agents/task-flow-test/AGENT.md` | Test 에이전트 정의 | 없음 |
| `claude/skills/api-analyzer/SKILL.md` | API 분석 스킬 | 없음 — 그대로 복사 |
| `claude/skills/doc-writer/SKILL.md` | 문서 작성 스킬 | 없음 — 그대로 복사 |
| `claude/skills/interview/SKILL.md` | 인터뷰 스킬 | 없음 — 그대로 복사 |
| `claude/skills/version-mgr/SKILL.md` | 버전 관리 스킬 | 없음 — 그대로 복사 |
| `claude/skills/wireframe-builder/SKILL.md` | 와이어프레임 스킬 | 없음 — 그대로 복사 |
| `cursor/agents/task-flow-qa/AGENT.md` | Cursor용 QA 에이전트 | 삭제 → 플랫 파일로 재생성 |
| `cursor/agents/task-flow-planner/AGENT.md` | Cursor용 Planner 에이전트 | 삭제 → 플랫 파일로 재생성 |
| `cursor/agents/task-flow-test/AGENT.md` | Cursor용 Test 에이전트 | 삭제 → 플랫 파일로 재생성 |
| `templates/cursor-rules/*.mdc` (4개) | Cursor Rules 템플릿 | 없음 — 원본 유지 |
| `templates/CLAUDE.md` | CLAUDE.md 프로젝트 템플릿 | 참조 — GEMINI.md 템플릿 작성 시 원본 |
| `templates/r2/000-r2-persona.mdc` | 알투 Cursor 페르소나 | 없음 — Antigravity 스니펫 작성 시 참조 |
| `templates/r2/claude-snippet.md` | 알투 Claude Code 스니펫 | 없음 — Antigravity 스니펫 작성 시 참조 |
| `CLAUDE.md` | 프로젝트 아키텍처 정의 | 수정 — Antigravity 섹션 추가, Cursor 에이전트 구조 업데이트 |
| `README.md` | 설치/설정 가이드 | 수정 — Antigravity 가이드 추가 |

**신규 생성 파일:**

| 파일 | 역할 |
|------|------|
| `antigravity/skills/task-flow/SKILL.md` | Antigravity용 task-flow (에이전트 탐색 경로 Antigravity 추가) |
| `antigravity/skills/{나머지 5개}/SKILL.md` | Antigravity용 스킬 (claude/와 동일 내용 복사) |
| `antigravity/skills/task-flow-qa/SKILL.md` | Antigravity용 QA 에이전트 (AGENT.md → SKILL.md 포맷 변환) |
| `antigravity/skills/task-flow-planner/SKILL.md` | Antigravity용 Planner 에이전트 (AGENT.md → SKILL.md 포맷 변환) |
| `antigravity/skills/task-flow-test/SKILL.md` | Antigravity용 Test 에이전트 (AGENT.md → SKILL.md 포맷 변환) |
| `cursor/agents/task-flow-qa.md` | Cursor용 QA 에이전트 (플랫 파일) |
| `cursor/agents/task-flow-planner.md` | Cursor용 Planner 에이전트 (플랫 파일) |
| `cursor/agents/task-flow-test.md` | Cursor용 Test 에이전트 (플랫 파일) |
| `templates/GEMINI.md` | Antigravity 프로젝트 컨텍스트 템플릿 (CLAUDE.md의 Antigravity 버전) |
| `templates/r2/gemini-snippet.md` | 알투 GEMINI.md 스니펫 (프로젝트 또는 글로벌 GEMINI.md에 삽입) |

### 현재 구현 패턴

#### 소스 구조 패턴

프레임워크는 **플랫폼별 소스 디렉토리**를 사용한다:

```
claude/     ← Claude Code 원본 (skills/ + agents/)
cursor/     ← Cursor 미러 (동일 SKILL.md/AGENT.md 복사)
```

배포 시 각 플랫폼 디렉토리에 복사:
- `claude/skills/` → `~/.claude/skills/`
- `cursor/skills/` → `~/.cursor/skills/`

#### 에이전트 구조 패턴

**Claude Code**: 디렉토리 기반
```
claude/agents/task-flow-qa/AGENT.md
```

**Cursor**: 현재 디렉토리 기반(잘못됨) → 플랫 파일로 변경 필요
```
현재: cursor/agents/task-flow-qa/AGENT.md
정상: cursor/agents/task-flow-qa.md
```

#### Rules 템플릿 패턴

Cursor의 `.mdc` 포맷:
```yaml
---
description: 설명 텍스트
globs:
alwaysApply: true/false
---
본문 (Markdown)
```

#### 알투(R2) 설정 패턴

- Cursor: `000-r2-persona.mdc` (`.cursor/rules/`에 배치)
- Claude Code: `claude-snippet.md` (`~/.claude/CLAUDE.md`에 삽입)

### 의존성 맵

```
SKILL.md (task-flow)
  ├── references/research-guide.md
  ├── references/plan-guide.md
  ├── references/todo-guide.md
  ├── references/execute-guide.md
  ├── references/execute-plan-guide.md (planner용)
  ├── → task-flow-qa AGENT.md (QA 에이전트 호출)
  ├── → task-flow-planner AGENT.md (복잡 모드)
  └── → task-flow-test AGENT.md (복잡 모드)

CLAUDE.md ← README.md 참조
templates/cursor-rules/ ← templates/CLAUDE.md와 동일 내용의 Cursor 버전
templates/r2/ ← 알투 설정 (플랫폼별)
```

## 2. 외부 조사 결과

### Antigravity 설정 체계 (검증 완료)

| 영역 | 경로 | 포맷 | 검증 상태 |
|------|------|------|----------|
| **프로젝트 컨텍스트/룰** | `GEMINI.md` (프로젝트 루트) | Plain Markdown | ✅ 확인 |
| **글로벌 컨텍스트/룰** | `~/.gemini/GEMINI.md` | Plain Markdown | ✅ 확인 |
| **프로젝트 Skills** | `.agent/skills/{name}/SKILL.md` | Agent Skills 오픈 표준 | ✅ Google Codelabs 확인 |
| **글로벌 Skills** | `~/.gemini/antigravity/skills/{name}/SKILL.md` | Agent Skills 오픈 표준 | ✅ Google Codelabs 확인 |
| **프로젝트 Workflows** | `.agent/workflows/*.md` | Markdown | ✅ 확인 |
| **글로벌 Workflows** | `~/.gemini/antigravity/global_workflows/*.md` | Markdown | ✅ 확인 |
| **MCP 설정** | `~/.gemini/antigravity/mcp_config.json` | JSON | ✅ 확인 |

> **⚠️ 중요**: Antigravity에는 `.agent/rules/` 디렉토리가 **존재하지 않는다**. 프로젝트 룰/컨텍스트는 모두 `GEMINI.md` 단일 파일에 작성한다. 이는 Claude Code의 `CLAUDE.md` 방식과 동일한 패턴이다.

### Antigravity 프로젝트 컨텍스트 (GEMINI.md)

Antigravity의 프로젝트 설정은 `GEMINI.md` 단일 파일로 관리한다:

```markdown
# 프로젝트 제목

## 프로젝트 개요
{프로젝트 설명}

## 기술 스택
{사용 기술}

## 코드 컨벤션
{스타일 규칙}

## 개발 워크플로우
{작업 규칙, 절차}
```

**Claude Code / Cursor와의 매핑:**
- Claude Code: `CLAUDE.md` (단일 파일) → Antigravity: `GEMINI.md` (단일 파일) — **동일 패턴**
- Cursor: `.cursor/rules/*.mdc` (모듈형 파일) → Antigravity: `GEMINI.md` (단일 파일) — **다른 패턴**

따라서 Antigravity용 프로젝트 템플릿은 `templates/CLAUDE.md`를 기반으로 `templates/GEMINI.md`를 만들면 된다 (Cursor Rules 변환이 아님).

### Antigravity Skills 포맷 (SKILL.md)

Agent Skills 오픈 표준 채택. Claude Code/Cursor와 **동일한 SKILL.md 포맷** 사용:

```markdown
---
name: skill-name
description: |
  스킬 설명. 이 description이 자동 매칭 트리거로 사용됨.
---
# 스킬 내용
```

**차이점**: Antigravity는 `description` 필드를 시맨틱 매칭에 사용하여 사용자의 자연어 요청과 자동 매칭한다. Claude Code/Cursor보다 `description`의 키워드 풍부성이 더 중요.

### Antigravity 에이전트 체계

Antigravity에는 `agents/` 디렉토리 컨벤션이 **없다**. 에이전트 오케스트레이션은 Manager View UI로 처리한다.

**프레임워크 에이전트 적용 방안 분석:**

| 방안 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **A. Skills로 변환** | 에이전트를 Skills로 변환하여 `.agent/skills/`에 배치 | Antigravity 네이티브, 자동 발견 | 독립 컨텍스트 실행 보장 어려움 |
| **B. Workflows로 변환** | 에이전트를 Workflows로 변환하여 `/task-flow-qa` 커맨드로 호출 | 명시적 호출, 슬래시 커맨드 | 자동 호출 불가, 수동 트리거만 |
| **C. SKILL.md 내 인라인** | task-flow SKILL.md 내에 에이전트 지시를 직접 포함 | 단일 파일, 간단 | 독립 검토 객관성 저하 |

**권장: 방안 A (Skills로 변환)**

이유:
1. Skills는 Antigravity가 자동 발견하고 컨텍스트에 맞게 활성화
2. task-flow SKILL.md에서 "이 스킬을 호출하라"는 지시를 통해 체인 가능
3. `description` 필드에 트리거 조건을 명시하면 자동 매칭도 가능
4. 기존 AGENT.md의 내용을 SKILL.md 포맷으로 변환하면 됨 (구조 유사)

### 3-플랫폼 매핑 종합

| 컴포넌트 | Claude Code | Cursor | Antigravity |
|----------|------------|--------|-------------|
| **Skills 소스** | `claude/skills/` | `cursor/skills/` | `antigravity/skills/` |
| **Skills 배포** | `~/.claude/skills/` | `~/.cursor/skills/` | `~/.gemini/antigravity/skills/` |
| **Skills 포맷** | `SKILL.md` | `SKILL.md` | `SKILL.md` (동일) |
| **Agents 소스** | `claude/agents/{name}/AGENT.md` | `cursor/agents/{name}.md` | `antigravity/skills/{name}/SKILL.md` |
| **Agents 배포** | `~/.claude/agents/{name}/AGENT.md` | `~/.cursor/agents/{name}.md` | `~/.gemini/antigravity/skills/{name}/SKILL.md` |
| **Agents 포맷** | `AGENT.md` (디렉토리 기반) | `{name}.md` (플랫 파일) | `SKILL.md` (Skills로 변환) |
| **프로젝트 컨텍스트/룰** | `CLAUDE.md` (단일 파일) | `.cursor/rules/*.mdc` (모듈형) | `GEMINI.md` (단일 파일) |
| **R2 설정** | `~/.claude/CLAUDE.md` 삽입 | `.cursor/rules/000-r2-persona.mdc` | `GEMINI.md` 삽입 (프로젝트 또는 `~/.gemini/GEMINI.md`) |

## 3. 영향 범위

### 직접 영향

| 영역 | 영향 내용 |
|------|----------|
| `claude/skills/task-flow/SKILL.md` | 에이전트 탐색 경로에 Antigravity 경로 추가 + QA 호출 강조 블록 |
| `claude/skills/task-flow/references/*.md` (4개) | QA 에이전트 호출 단계 추가 |
| `claude/agents/task-flow-qa/AGENT.md` | "자동 호출" 표현 수정 |
| `cursor/agents/` | 디렉토리 기반 → 플랫 파일 구조 변경 |
| `CLAUDE.md` | 아키텍처 섹션 3-플랫폼 구조 반영 |
| `README.md` | Antigravity 설치/설정 가이드 추가 |

### 간접 영향

| 영역 | 영향 내용 |
|------|----------|
| `templates/CLAUDE.md` | `templates/GEMINI.md` 작성 시 원본으로 활용 — 직접 변경 불필요 |

### 영향 없는 영역

- `claude/skills/` (task-flow 제외 5개) — 내용 변경 없이 Antigravity 디렉토리에 복사
- `claude/agents/task-flow-planner/`, `task-flow-test/` — 내용 변경 없음 (Cursor 플랫 파일 + Antigravity Skills 변환만)
- `templates/cursor-rules/` — 원본 유지

## 4. 핵심 발견 사항

### 발견 1: Skills 포맷이 3-플랫폼 공통

Agent Skills 오픈 표준 덕분에 SKILL.md가 Claude Code, Cursor, Antigravity에서 **동일 포맷**으로 동작한다. 스킬 6개는 내용 변경 없이 디렉토리만 복사하면 된다. 단, task-flow만 에이전트 탐색 경로 때문에 플랫폼별 약간의 차이가 발생한다.

### 발견 2: Antigravity 에이전트는 Skills로 변환이 최선

Antigravity에 `agents/` 디렉토리가 없으므로, 기존 3개 에이전트(task-flow-qa, task-flow-planner, task-flow-test)를 SKILL.md 포맷으로 변환하여 `.agent/skills/`에 배치하는 것이 자연스럽다. 에이전트의 검증 기준, 입출력 명세는 그대로 유지하되 YAML frontmatter만 변경.

### 발견 3: Cursor 에이전트 플랫 파일 전환은 내용 변경 없이 구조만 변경

`cursor/agents/task-flow-qa/AGENT.md`의 내용을 `cursor/agents/task-flow-qa.md`로 옮기면 된다. YAML frontmatter와 본문은 그대로.

### 발견 4: Antigravity 프로젝트 컨텍스트는 CLAUDE.md와 동일 패턴

Antigravity에는 `.agent/rules/` 디렉토리가 존재하지 않는다. 프로젝트 룰/컨텍스트는 `GEMINI.md` 단일 파일에 작성한다.

**플랫폼별 프로젝트 컨텍스트 패턴:**
- Claude Code: `CLAUDE.md` (단일 파일) — 프로젝트의 모든 규칙/컨텍스트를 하나의 파일에
- Cursor: `.cursor/rules/*.mdc` (모듈형) — 규칙을 파일별로 분리
- Antigravity: `GEMINI.md` (단일 파일) — Claude Code와 동일 패턴

따라서 Antigravity 템플릿은 Cursor `.mdc` 변환이 아니라, `templates/CLAUDE.md`를 기반으로 `templates/GEMINI.md`를 작성해야 한다.

### 발견 5: QA 호출 누락의 구조적 원인이 명확

references 가이드 4개(research, plan, todo, execute)가 각각 "품질 체크리스트"로 끝나는데, 이것은 **자체 검증**이지 QA 에이전트 호출이 아니다. 에이전트가 가이드를 충실히 따라가면 QA 호출 단계를 만나지 못하고 자체 검증만 하고 끝나는 구조.

`execute-plan-guide.md`는 task-flow-planner 에이전트용이므로 QA 호출과 무관 — 수정 불필요.

## 5. 제약/리스크

### 리스크 1: Antigravity 프리뷰 단계 변경 가능성

Antigravity는 현재 공개 프리뷰 중이다. `.agent/` 디렉토리 구조나 SKILL.md 포맷이 GA(정식 출시) 시 변경될 수 있다.

**완화 방안**: 현재 공식 문서 기준으로 구현하되, 변경 시 영향 받는 파일을 `antigravity/`와 `templates/GEMINI.md`로 격리하여 업데이트 범위를 최소화.

### 리스크 2: Antigravity 에이전트→Skills 변환 시 독립 컨텍스트 보장

Claude Code의 Task 도구는 서브 에이전트를 독립 컨텍스트에서 실행한다. Antigravity에서 Skills로 변환하면 같은 컨텍스트 내에서 실행될 수 있어, QA의 **객관적 검토**가 약해질 수 있다.

**완화 방안**: SKILL.md 내에 "독립적 관점에서 검토하라"는 지시를 강화. Antigravity의 Manager View에서 별도 에이전트로 실행하는 것도 사용자에게 안내.

### 리스크 3: Cursor 에이전트 구조 변경 시 기존 사용자 영향

이미 `~/.cursor/agents/task-flow-qa/AGENT.md`로 배포한 사용자가 있을 수 있다. 플랫 파일로 변경하면 기존 경로가 무효화된다.

**완화 방안**: README.md 마이그레이션 가이드에 "기존 디렉토리 삭제 후 플랫 파일 배치" 안내 추가.

### 리스크 4: `~/.gemini/GEMINI.md` 충돌

Antigravity IDE와 Gemini CLI가 `~/.gemini/GEMINI.md`를 공유한다 (GitHub issue #16058). 알투 설정을 여기에 넣으면 Gemini CLI에도 영향.

**완화 방안**: 글로벌 `~/.gemini/GEMINI.md`에는 최소한의 알투 스니펫만 삽입하고, 상세 설정은 프로젝트 레벨 `GEMINI.md`에 포함하도록 안내. Gemini CLI와의 충돌 가능성을 README에 명시.
