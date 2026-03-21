# DONE: OPAL 프레임워크 배포 구조 통합 — ~/.opal/ 단일 배포

> 완료일: 2026-03-21 | 모드: Full Task | 작업 유형: 개선

## 완료 요약

3개 플랫폼 네이티브 디렉토리(~/.claude/, ~/.cursor/, ~/.gemini/)에 분산 복사하던 스킬/에이전트를 `~/.opal/` 하나로 통합 배포하도록 변경했다. 에이전트를 플랫폼별 3벌(Claude AGENT.md / Cursor 플랫 .md / Antigravity SKILL.md)에서 단일 AGENT.md 포맷으로 통합하고, OPAL 전용 스킬에 `opal-` 접두사를 적용했다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `agents/` (7개 디렉토리) | `agents/claude/`에서 `agents/`로 플랫화 |
| 2 | `agents/cursor/` | 삭제 (7개 파일) |
| 3 | `agents/antigravity/` | 삭제 (7개 파일) |
| 4 | `opal/skills/opal-onboarding/` | `onboarding/`에서 이름 변경 |
| 5 | `opal/skills/opal-orchestrator/` | `orchestrator/`에서 이름 변경 |
| 6 | `opal/skills/opal-project-init/` | `project-init/`에서 이름 변경 |
| 7 | `opal/skills/opal-skill-manager/` | `skill-manager/`에서 이름 변경 |
| 8 | `opal/core/AGENT.md` | OPAL 전용 스킬 경로에 opal- 접두사 적용 |
| 9 | `opal/bootstrapper/cursor-bootstrap.mdc` | onboarding 경로에 opal- 접두사 적용 |
| 10 | `opal/core/references/skills.md` | 탐색 경로 5개 → 2개, opal- 접두사 적용 |
| 11 | `opal/core/references/agents.md` | 탐색 경로 8개 → 2개, wtm-worker 추가 |
| 12 | `skills/dev-task-pilot/SKILL.md` | 에이전트 탐색 경로 2개로 축소 |
| 13 | `skills/dev-task-pilot/modes/wireframe-ui.md` | 스킬 탐색 경로 2개로 축소 |
| 14 | `skills/dev-task-pilot/references/execute-plan-guide.md` | 스킬 탐색 경로 2개로 축소 |
| 15 | `skills/web-to-markdown/SKILL.md` | 에이전트 탐색 경로 2개로 축소 |
| 16 | `skills/opal-agent-creator/SKILL.md` | 에이전트 탐색 경로 2개로 축소, 단일 포맷 반영 |
| 17 | `scripts/install-mac.sh` | 메뉴 3개로 재설계, 플랫폼별 함수 삭제, ~/.opal/ 통합 배포 |
| 18 | `CLAUDE.md` | 소스 구조/배포 구조/컴포넌트 테이블/에이전트 가이드 업데이트 |
| 19 | `README.md` | 아키텍처/설치 가이드/에이전트 섹션 업데이트 |
| 20 | `agents/dtp-action-plan-agent/AGENT.md` | 스킬 등록 경로 ~/.opal/로 변경 |
| 21 | `agents/dtp-wireframe-ui-agent/AGENT.md` | 스킬 탐색 경로 2개로 축소 |

## 핵심 변경 사항

### Before
- 스킬: `skills/` → `~/.claude/skills/`, `~/.cursor/skills/`, `~/.gemini/antigravity/skills/` (3곳 복사)
- 에이전트: `agents/claude/`, `agents/cursor/`, `agents/antigravity/` (3벌 관리)
- 탐색 경로: 플랫폼별 5~8개
- install-mac.sh 메뉴: 6개 (플랫폼별 + OPAL + MCP + 전체)

### After
- 스킬/에이전트: `~/.opal/skills/`, `~/.opal/agents/` (1곳 통합)
- 에이전트: `agents/{name}/AGENT.md` (단일 포맷)
- 탐색 경로: `{프로젝트}/.opal/` + `~/.opal/` (2개)
- install-mac.sh 메뉴: 3개 (OPAL 설치 / MCP 설정 / 전체)

## QA 결과

| 단계 | 결과 | 비고 |
|------|------|------|
| QA-RESEARCH | Pass | 6/6 항목 통과 |
| QA-PLAN | Pass | 5/6 Pass, 1 Warning (EXECUTE에서 보완) |
| QA-EXECUTE | Pass | 7/7 검증 포인트 통과 |

## 산출물 목록

| 파일 | 설명 |
|------|------|
| tasks/026-opal-unified-deployment/TASK.md | 작업 정의서 |
| tasks/026-opal-unified-deployment/RESEARCH.md | 분석 결과 |
| tasks/026-opal-unified-deployment/QA-RESEARCH.md | RESEARCH QA |
| tasks/026-opal-unified-deployment/PLAN.md | 구현 계획 |
| tasks/026-opal-unified-deployment/QA-PLAN.md | PLAN QA |
| tasks/026-opal-unified-deployment/TODO.md | 실행 체크리스트 (13 Step 완료) |
| tasks/026-opal-unified-deployment/QA-EXECUTE.md | EXECUTE QA |
| tasks/026-opal-unified-deployment/STATE.md | 상태 추적 |
| tasks/026-opal-unified-deployment/DONE.md | 완료 리포트 |
