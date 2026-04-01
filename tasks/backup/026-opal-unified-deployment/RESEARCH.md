# RESEARCH: OPAL 프레임워크 배포 구조 통합 — ~/.opal/ 단일 배포

> 작성일: 2026-03-21 | 참조: TASK.md

## 1. 기존 코드 분석

### 관련 파일 목록

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `scripts/install-mac.sh` | 배포 스크립트 — 3개 플랫폼 + OPAL 설치 | 수정 (핵심) |
| `agents/claude/` (6개 에이전트) | Claude 포맷 에이전트 (AGENT.md) | 이동 → `agents/` 단일 |
| `agents/cursor/` (6개 에이전트) | Cursor 포맷 에이전트 (플랫 .md) | 삭제 |
| `agents/antigravity/` (6개 에이전트) | Antigravity 포맷 에이전트 (SKILL.md) | 삭제 |
| `opal/core/references/skills.md` | 스킬 레지스트리 — 프레임워크 스킬 탐색 경로 | 수정 |
| `opal/core/references/agents.md` | 에이전트 레지스트리 — 에이전트 탐색 경로 | 수정 |
| `opal/core/references/mcps.md` | MCP 레지스트리 — 설정 경로 참조 | 수정 불필요 (MCP는 플랫폼별 유지) |
| `opal/skills/onboarding/SKILL.md` | OPAL 전용 스킬 | 수정 불필요 (이미 `~/.opal/` 경로) |
| `opal/skills/orchestrator/SKILL.md` | OPAL 전용 스킬 | 수정 불필요 |
| `opal/skills/project-init/SKILL.md` | OPAL 전용 스킬 | 수정 불필요 |
| `opal/skills/skill-manager/SKILL.md` | OPAL 전용 스킬 | 수정 불필요 |
| `skills/dev-task-pilot/SKILL.md` | 에이전트/스킬 탐색 경로 명시 | 수정 |
| `skills/dev-task-pilot/modes/wireframe-ui.md` | 스킬 탐색 경로 명시 | 수정 |
| `skills/dev-task-pilot/references/execute-plan-guide.md` | 스킬 탐색 경로 명시 | 수정 |
| `skills/web-to-markdown/SKILL.md` | 에이전트 탐색 경로 명시 | 수정 |
| `skills/opal-agent-creator/SKILL.md` | 에이전트 탐색 경로 템플릿 | 수정 |
| `skills/opal-skill-creator/SKILL.md` | 스킬 경로 참조 | 수정 불필요 (이미 `~/.opal/` 경로) |
| `skills/ui-designer/SKILL.md` | `~/.opal/community-skills/` 경로 참조 | 수정 불필요 (이미 `~/.opal/` 경로) |
| `CLAUDE.md` | 프로젝트 아키텍처 설명 (소스 구조 + 배포 구조) | 수정 |
| `README.md` | 2계층 아키텍처 다이어그램 + 설치 가이드 | 수정 |

### 현재 구현 패턴

#### install-mac.sh 배포 로직

현재 인스톨러는 메뉴 기반 6가지 선택지를 제공한다:

1. **Claude Code** (`install_claude`): `skills/` → `~/.claude/skills/`, `agents/claude/` → `~/.claude/agents/`
2. **Cursor** (`install_cursor`): `skills/` → `~/.cursor/skills/`, `agents/cursor/` → `~/.cursor/agents/`
3. **Antigravity** (`install_antigravity`): `skills/` → `~/.gemini/antigravity/skills/`, `agents/antigravity/` → `~/.gemini/antigravity/skills/` (에이전트를 스킬로 병합), `agents/cursor/*.md` → `~/.gemini/agents/` (Gemini CLI용)
4. **OPAL** (`install_opal`): `AGENT.md`, `opal/skills/`, `opal/templates/`, `opal/core/references/`, `community-skills/` → `~/.opal/`, 부트스트래퍼 설치
5. **MCP 서버**: 플랫폼별 MCP 설정 머지
6. **전체 설치**: 1~5 모두 실행

핵심 함수:
- `install_dir()`: 디렉토리를 복사 (신규/덮어쓰기)
- `install_opal_section()`: OPAL 마커 기반으로 부트스트래퍼 삽입/교체
- `merge_mcp_config()`: JSON MCP 설정 머지
- `merge_hooks_config()`: Claude Code hooks 설정 머지

#### 에이전트 3벌 포맷 차이

| 차이점 | Claude (AGENT.md) | Cursor (플랫 .md) | Antigravity (SKILL.md) |
|--------|-------------------|-------------------|----------------------|
| **YAML frontmatter** | `name`, `description`, `model: sonnet`, `color` | `name`, `description`, `model: claude-sonnet-4-6`, `readonly`, `tools`, `max_turns`, `timeout_mins` | `name`, `description`, `model: gemini-3.1-pro` |
| **헤더 스타일** | `# dev-task-pilot 워커 에이전트` | `# dtp-dev-agent -- Full Task / Short Task 워커 에이전트` | `# dtp-dev-agent (폴백 모드)` |
| **설정 참조** | `프로젝트 CLAUDE.md` | `프로젝트 CLAUDE.md` | `프로젝트 설정 파일` |
| **모델 오버라이드** | 별도 섹션으로 단계별 권장 모델 표 존재 | 없음 | 없음 |
| **Edit 도구** | `Edit 도구` | `파일 편집 도구` | 없음 |
| **복잡 모드** | 서브 에이전트 배치 + 중첩 불가 플랫폼 분기 | 동일 | "Antigravity에서는 중첩 서브 에이전트 불가" 전용 문구 |
| **구분자** | 없음 | 섹션 사이 `---` | 없음 |
| **본문 내용** | ~95% 동일 | ~90% 동일 (Cursor 전용 메타 + 도구 지정) | ~80% 동일 (폴백 모드 설명 추가, 세부 생략) |

핵심 발견: **3벌의 본문 내용은 80-95% 동일**하다. 차이는 주로 (1) YAML frontmatter의 플랫폼별 메타데이터, (2) 플랫폼 특성에 따른 1-2줄 문구 차이뿐이다.

#### 스킬 내 탐색 경로 참조 현황

다음 파일들이 에이전트 또는 스킬의 탐색 경로를 명시한다:

**에이전트 탐색 경로** (현재 8개 경로):
```
1. {프로젝트}/.cursor/agents/{agent-name}.md
2. {프로젝트}/.cursor/agents/{agent-name}/AGENT.md
3. {프로젝트}/.claude/agents/{agent-name}/AGENT.md
4. {프로젝트}/.agent/skills/{agent-name}/SKILL.md
5. ~/.cursor/agents/{agent-name}.md
6. ~/.cursor/agents/{agent-name}/AGENT.md
7. ~/.claude/agents/{agent-name}/AGENT.md
8. ~/.gemini/antigravity/skills/{agent-name}/SKILL.md
```

명시하는 파일:
- `skills/dev-task-pilot/SKILL.md` (라인 120-131)
- `skills/web-to-markdown/SKILL.md` (라인 235-241)
- `skills/opal-agent-creator/SKILL.md` (라인 216-224)
- `opal/core/references/agents.md` (라인 62-69)

**스킬 탐색 경로** (현재 5개 경로):
```
1. {프로젝트}/.cursor/skills/{skill}/SKILL.md
2. {프로젝트}/.claude/skills/{skill}/SKILL.md
3. ~/.cursor/skills/{skill}/SKILL.md
4. ~/.claude/skills/{skill}/SKILL.md
5. ~/.gemini/antigravity/skills/{skill}/SKILL.md
```

명시하는 파일:
- `opal/core/references/skills.md` (라인 20-25)
- `skills/dev-task-pilot/modes/wireframe-ui.md` (라인 130-136, 191-197)
- `skills/dev-task-pilot/references/execute-plan-guide.md` (라인 59-63)

### 의존성 맵

```
install-mac.sh
  ├── agents/claude/*     → ~/.claude/agents/
  ├── agents/cursor/*     → ~/.cursor/agents/
  ├── agents/antigravity/* → ~/.gemini/antigravity/skills/
  ├── skills/*            → ~/.claude/skills/, ~/.cursor/skills/, ~/.gemini/antigravity/skills/
  ├── opal/core/*         → ~/.opal/
  ├── opal/skills/*       → ~/.opal/skills/
  ├── community-skills/*  → ~/.opal/community-skills/
  └── opal/bootstrapper/* → ~/.claude/CLAUDE.md, ~/.cursor/rules/, ~/.gemini/GEMINI.md

references/skills.md ← AGENT.md (부트스트랩 시 Read)
references/agents.md ← AGENT.md (부트스트랩 시 Read)
                     ← dev-task-pilot/SKILL.md (에이전트 호출 시 참조)

dev-task-pilot/SKILL.md → dtp-dev-agent, dtp-qa-dev-agent, dtp-action-plan-agent, dtp-dev-test-agent
web-to-markdown/SKILL.md → wtm-worker
```

## 2. 외부 조사 결과

해당 없음 (외부 API/라이브러리 없음, 내부 구조 변경 작업).

## 3. 영향 범위

### 직접 영향

| 영역 | 변경 내용 | 파일 수 |
|------|----------|---------|
| **소스 agents/ 구조** | `agents/{claude,cursor,antigravity}/` → `agents/` 플랫화 | ~20개 파일 이동/삭제 |
| **install-mac.sh** | 플랫폼별 스킬/에이전트 복사 로직 제거, `~/.opal/` 단일 배포로 변경 | 1개 |
| **references/skills.md** | 프레임워크 스킬 탐색 경로를 `~/.opal/skills/`로 변경 | 1개 |
| **references/agents.md** | 에이전트 탐색 경로를 `~/.opal/agents/`로 변경 | 1개 |
| **스킬 내 탐색 경로** | 6개 스킬 파일의 탐색 경로 블록 수정 | 6개 |
| **CLAUDE.md** | 소스 구조 + 배포 구조 다이어그램 업데이트 | 1개 |
| **README.md** | 2계층 아키텍처 다이어그램 + 설치 가이드 업데이트 | 1개 |

### 간접 영향

| 영역 | 영향 | 대응 |
|------|------|------|
| **기존 배포 환경** | `~/.claude/skills/`, `~/.cursor/skills/` 등에 이미 복사된 파일이 잔존 | install-mac.sh에 정리(cleanup) 로직 추가 또는 수동 안내 |
| **프로젝트 레벨 에이전트** | `{프로젝트}/.claude/agents/`, `{프로젝트}/.cursor/agents/`에 프로젝트별 오버라이드가 있을 수 있음 | 프로젝트 레벨 경로는 유지 (탐색 경로 우선순위 1-4번) |
| **install-mac.sh 메뉴** | [1] Claude, [2] Cursor, [3] Antigravity 옵션이 의미를 잃음 | 메뉴 구조 재설계 필요 |
| **OPAL 전용 스킬 이름** | TASK.md에서 `opal-` 접두사 적용 제안 (onboarding → opal-onboarding) | 프레임워크 스킬에는 이미 `opal-skill-creator`, `opal-agent-creator` 존재; OPAL 전용 스킬에만 적용 |

### 설정 영향

- **MCP 설정**: 변경 없음 (플랫폼별 네이티브 기능 유지)
- **부트스트래퍼**: 변경 없음 (알투가 `~/.opal/AGENT.md`를 읽는 기존 방식 유지)
- **Claude Code hooks**: 변경 없음 (`~/.claude/settings.json`에 머지, 플랫폼 네이티브)

## 4. 핵심 발견 사항

### 4-1. 에이전트 3벌은 본문 80-95% 동일, 통합 가능

3개 플랫폼별 에이전트 파일의 차이는 주로 YAML frontmatter(모델명, 도구 지정)와 1-2줄의 플랫폼 특화 문구뿐이다. Claude 포맷(AGENT.md)을 기준으로 통합하면 Cursor/Antigravity 전용 메타데이터만 소실되며, 이는 알투가 에이전트를 Read하여 서브에이전트에 전달하는 방식에서는 불필요하다.

### 4-2. 탐색 경로 수정이 필요한 파일은 9개

- `opal/core/references/skills.md` (프레임워크 스킬 경로 5개 → 1개)
- `opal/core/references/agents.md` (에이전트 경로 8개 → 1개)
- `skills/dev-task-pilot/SKILL.md` (에이전트 탐색 경로)
- `skills/dev-task-pilot/modes/wireframe-ui.md` (스킬 탐색 경로 2곳)
- `skills/dev-task-pilot/references/execute-plan-guide.md` (스킬 탐색 경로)
- `skills/web-to-markdown/SKILL.md` (에이전트 탐색 경로)
- `skills/opal-agent-creator/SKILL.md` (에이전트 탐색 경로 템플릿)
- `CLAUDE.md` (아키텍처 설명)
- `README.md` (아키텍처 다이어그램 + 설치 가이드)

### 4-3. TASK.md 목표 구조에 오류 있음

TASK.md의 목표 배포 구조(라인 69-79)에서 OPAL 전용 스킬(`opal-onboarding`, `opal-project-init` 등)이 `agents/` 하위에 배치되어 있다. 이는 오류로 보이며, `skills/` 하위에 있어야 한다:

```
현재 TASK.md (잘못됨):
├── agents/
│   ├── dtp-dev-agent/AGENT.md
│   ...
│   ├── opal-onboarding/        ← agents/ 아래에 있음
│   └── opal-skill-manager/

올바른 구조:
├── skills/                     ← 프레임워크 스킬
│   ├── dev-task-pilot/
│   ...
├── opal-skills/                ← OPAL 전용 스킬 (또는 skills/ 내 opal- 접두사)
│   ├── opal-onboarding/
│   └── opal-skill-manager/
├── agents/                     ← 에이전트
│   ├── dtp-dev-agent/AGENT.md
│   ...
```

### 4-4. 프레임워크 스킬에 이미 opal- 접두사 사용 중

`skills/` 디렉토리에 이미 `opal-skill-creator/`와 `opal-agent-creator/`가 존재한다. 이들은 프레임워크 스킬이면서 opal- 접두사를 사용한다. OPAL 전용 스킬(onboarding 등)에 `opal-` 접두사를 적용하면 네이밍 일관성이 생기지만, 프레임워크 스킬과 OPAL 전용 스킬의 구분이 모호해질 수 있다.

현재 구분:
- `skills/` → 프레임워크 스킬 (10개: api-analyzer, dev-task-pilot, doc-writer, interview, opal-agent-creator, opal-skill-creator, ui-designer, version-mgr, web-to-markdown, wireframe-builder)
- `opal/skills/` → OPAL 전용 스킬 (4개: onboarding, orchestrator, project-init, skill-manager)

통합 시: 프레임워크 스킬과 OPAL 전용 스킬이 모두 `~/.opal/skills/`로 배포되므로, OPAL 전용 스킬에 `opal-` 접두사를 붙이면 디렉토리 내에서 구분 가능하다.

### 4-5. install-mac.sh 메뉴 구조 재설계 필요

플랫폼별 스킬/에이전트 복사가 없어지면 기존 메뉴 [1]~[3]의 존재 의미가 크게 줄어든다. 남는 역할:
- [1] Claude Code: hooks 설정만 (스킬/에이전트 복사 제거)
- [2] Cursor: 아무것도 안 함 (제거 대상)
- [3] Antigravity: Gemini CLI agents 복사만 (스킬 복사 제거) -- 단, 이것도 통합 시 불필요
- [4] OPAL: 현재와 동일 + 프레임워크 스킬/에이전트 추가 배포
- [5] MCP: 현재와 동일

재설계 방향:
- **[1] OPAL 설치** (스킬 + 에이전트 + 참조 + 커뮤니티 스킬 + 부트스트래퍼)
- **[2] MCP 서버 설정** (플랫폼별 MCP 설정 머지)
- **[3] 전체 설치** (1+2)
- **[0] 종료**

## 5. 제약/리스크

### 5-1. 기존 배포 파일 잔존

`~/.claude/skills/`, `~/.cursor/skills/`, `~/.gemini/antigravity/skills/`에 이미 복사된 파일들이 남아 있으면, 에이전트가 기존 탐색 경로로 찾을 수 있다. 탐색 경로를 `~/.opal/`로 변경하면 기존 파일은 무시되지만, 디스크 공간을 차지한다.

**대응**: install-mac.sh에 cleanup 옵션을 추가하거나, 첫 실행 시 기존 경로 정리를 안내한다.

### 5-2. 프로젝트 레벨 오버라이드 경로 유지

프로젝트별로 `{프로젝트}/.claude/agents/`나 `{프로젝트}/.cursor/skills/`에 커스텀 에이전트/스킬을 둘 수 있다. 이 경로는 글로벌 경로보다 우선하므로, 통합 후에도 프로젝트 레벨 탐색 경로는 유지해야 한다.

**대응**: 탐색 경로에서 글로벌 경로만 `~/.opal/`로 변경하고, 프로젝트 레벨 경로는 기존대로 유지한다.

### 5-3. Gemini CLI agents 배포 경로

현재 `install_antigravity()`에서 `agents/cursor/*.md`를 `~/.gemini/agents/`로 복사하는 로직이 있다. Gemini CLI가 `~/.gemini/agents/` 경로의 에이전트를 네이티브로 인식하는 기능이므로, 이 부분은 통합 후에도 유지하거나 별도 처리가 필요하다.

**대응**: Gemini CLI의 에이전트 인식은 플랫폼 네이티브 기능이므로, MCP 설정과 마찬가지로 플랫폼별로 유지할 수 있다. 다만 AGENT.md 통합 후에는 Cursor 포맷(.md) 파일이 없으므로, AGENT.md에서 Gemini CLI용 플랫 파일을 생성하는 로직이 필요하거나, Gemini CLI 배포를 포기할 수 있다.

### 5-4. wtm-worker 에이전트의 존재

`agents/` 하위 3개 플랫폼 모두에 `wtm-worker/`가 존재한다. 이 에이전트는 `web-to-markdown` 스킬의 워커인데, TASK.md의 목표 구조에는 포함되어 있지 않다. 통합 대상에 포함해야 한다.

### 5-5. OPAL 전용 스킬 opal- 접두사 적용 시 참조 변경

OPAL 전용 스킬의 이름을 변경하면(`onboarding` → `opal-onboarding` 등), 다음 파일에서 경로 참조를 수정해야 한다:
- `opal/core/AGENT.md` (부트스트랩 절차에서 `~/.opal/skills/onboarding/` 참조)
- `opal/core/references/skills.md` (OPAL 전용 스킬 경로)
- `opal/skills/onboarding/SKILL.md` (자기 참조)
- `opal/bootstrapper/cursor-bootstrap.mdc` (`~/.opal/skills/onboarding/` 참조)

소스 디렉토리도 `opal/skills/onboarding/` → `opal/skills/opal-onboarding/`으로 변경 필요.
