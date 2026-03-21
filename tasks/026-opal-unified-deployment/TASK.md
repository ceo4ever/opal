# TASK: OPAL 프레임워크 배포 구조 통합 — ~/.opal/ 단일 배포

> 작성일: 2026-03-21 | 작업 유형: 개선

## 작업 목표

현재 3개 플랫폼 네이티브 디렉토리(~/.claude/, ~/.cursor/, ~/.gemini/)에 분산 복사하던 스킬/에이전트를 `~/.opal/` 하나로 통합 배포한다. OPAL 에이전트(알투)가 프레임워크의 단일 진입점이 되어, 플랫폼별 포맷 차이 없이 하나의 에이전트 정의로 통합한다.

## 배경

- 현재 `install-mac.sh`가 skills/를 3개 플랫폼 디렉토리에 복사하고, agents/는 플랫폼별 포맷(AGENT.md, 플랫 .md, SKILL.md)으로 분리 관리
- 원래 의도: 알투 없이도 각 플랫폼에서 직접 스킬/에이전트 사용 가능하게
- 재평가: OPAL은 프레임워크이므로, 프레임워크의 진입점(알투)을 통하는 것이 자연스러움
- 알투가 이미 모든 플랫폼에서 부트스트랩되므로, 플랫폼 네이티브 배포는 불필요한 복잡도

## 요구사항

### 배포 구조 변경
- [ ] `~/.opal/` 하나로 스킬, 에이전트, 커뮤니티 스킬 통합 배포
- [ ] 플랫폼 네이티브 디렉토리(~/.claude/skills/, ~/.cursor/skills/ 등)에 더 이상 복사하지 않음
- [ ] MCP 설정은 플랫폼별로 유지 (플랫폼 네이티브 기능이므로)

### 에이전트 포맷 통합
- [ ] agents/{claude,cursor,antigravity}/ 3벌 → agents/ 단일 포맷(AGENT.md)
- [ ] 알투가 에이전트를 Read하여 플랫폼에 맞는 방식으로 서브에이전트에 전달

### 소스 구조 변경
- [ ] 소스 리포지토리의 agents/ 디렉토리 구조 변경 (플랫폼별 하위 디렉토리 제거)
- [ ] install-mac.sh 수정: 스킬/에이전트를 ~/.opal/로만 배포

### 경로 참조 수정
- [ ] opal/core/references/skills.md — 탐색 경로를 ~/.opal/skills/로 변경
- [ ] opal/core/references/agents.md — 탐색 경로를 ~/.opal/agents/로 변경
- [ ] 스킬 내 에이전트/스킬 탐색 경로 수정 (~6개 스킬)
- [ ] CLAUDE.md, README.md 아키텍처 설명 업데이트

## 제약 조건

- tasks/ 폴더의 과거 산출물은 이력이므로 수정하지 않음
- MCP 설정(~/.claude/.claude.json, ~/.cursor/mcp.json, ~/.gemini/settings.json)은 플랫폼별 유지
- OPAL 부트스트래퍼(CLAUDE.md, .cursorrules, GEMINI.md에 삽입)는 기존 방식 유지
- 기존 에이전트 3벌 중 Claude 포맷(AGENT.md)을 기준으로 통합

## 관련 문서

- `scripts/install-mac.sh` — 현재 배포 스크립트
- `opal/core/references/skills.md` — 스킬 레지스트리
- `opal/core/references/agents.md` — 에이전트 레지스트리
- `CLAUDE.md` — 프로젝트 아키텍처 설명

## 목표 배포 구조

```
~/.opal/
├── AGENT.md                    ← 알투 코어
├── identity.md
├── references/
│   ├── skills.md
│   ├── agents.md
│   └── mcps.md
├── skills/                     ← 프레임워크 스킬 (단일 소스)
│   ├── dev-task-pilot/
│   ├── api-analyzer/
│   ├── doc-writer/
│   ├── interview/
│   ├── ui-designer/
│   ├── version-mgr/
│   └── wireframe-builder/
├── agents/                     ← 에이전트 (단일 포맷, AGENT.md)
│   ├── dtp-dev-agent/AGENT.md
│   ├── dtp-wireframe-ui-agent/AGENT.md
│   ├── dtp-qa-dev-agent/AGENT.md
│   ├── dtp-qa-wireframe-agent/AGENT.md
│   ├── dtp-action-plan-agent/AGENT.md
│   └── dtp-dev-test-agent/AGENT.md
│   ├── opal-onboarding/        ← OPAL 전용 스킬 (opal- 접두사로 구분)
│   ├── opal-project-init/
│   ├── opal-orchestrator/
│   └── opal-skill-manager/
├── community-skills/           ← 커뮤니티 스킬 (31개)
└── templates/
```
