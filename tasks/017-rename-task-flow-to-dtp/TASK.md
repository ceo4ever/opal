# TASK: task-flow → dev-task-pilot(DTP) 및 RESEARCH → ANALYSIS 리네임

> 작성일: 2026-03-19 | 작업 유형: 기능 수정

## 작업 목표

`task-flow` 스킬/에이전트 전체를 `dev-task-pilot(DTP)`로 리네임하고, 단계명 `RESEARCH`를 `ANALYSIS`로 변경한다.

## 확정된 규칙

- 스킬명: `task-flow` → `dev-task-pilot`, 호출: `/dtp` (또는 `/dev-task-pilot`)
- 에이전트명: `task-flow-{role}` → `dtp-{role}` (약어)
  - `task-flow-agent` → `dtp-agent`
  - `task-flow-qa` → `dtp-qa`
  - `task-flow-planner` → `dtp-planner`
  - `task-flow-test` → `dtp-test`
- 단계명: `RESEARCH` → `ANALYSIS`, `QA-RESEARCH` → `QA-ANALYSIS`
- 가이드 파일: `research-guide.md` → `analysis-guide.md`
- `tasks/` 폴더 기존 산출물: 변경 없음 (히스토리 보존)
- 범위: `scripts/install-mac.sh` 포함

## 요구사항

- [ ] 디렉토리 rename
  - `skills/task-flow/` → `skills/dev-task-pilot/`
  - `agents/claude/task-flow-{agent,qa,planner,test}/` → `agents/claude/dtp-{agent,qa,planner,test}/`
  - `agents/antigravity/task-flow-{agent,qa,planner,test}/` → `agents/antigravity/dtp-{agent,qa,planner,test}/`
- [ ] 파일 rename
  - `agents/cursor/task-flow-*.md` → `agents/cursor/dtp-*.md`
  - `research-guide.md` → `analysis-guide.md`
- [ ] 내용 수정 (tasks/ 제외한 모든 파일)
  - `task-flow-agent/qa/planner/test` → `dtp-agent/qa/planner/test`
  - `task-flow` (스킬명) → `dev-task-pilot`
  - `RESEARCH` → `ANALYSIS`
  - `research-guide` → `analysis-guide`
- [ ] `scripts/install-mac.sh` 경로/변수명 업데이트
- [ ] `CLAUDE.md`, `README.md`, `opal/core/references/*.md` 내용 업데이트

## 제약 조건

- `tasks/` 폴더 내 기존 산출물(.md) 내용은 수정하지 않는다
- 에이전트 YAML frontmatter의 `name` 필드도 변경한다
