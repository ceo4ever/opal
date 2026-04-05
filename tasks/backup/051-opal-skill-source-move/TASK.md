# TASK: OPAL 전용 스킬 소스 디렉토리 이동

> 작성일: 2026-03-30 | 작업 유형: 수정
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL 전용 스킬 20개를 `skills/` → `opal/skills/`로 이동하여, `skills/`에는 standalone 스킬만 남기고 소스 구조의 관심사를 분리한다.

## 배경

042 리네이밍 이후 스킬 이름은 정리되었으나, 소스 위치는 미변경 상태. `skills/`에 OPAL 내부 스킬 20개 + 독립 스킬 5개가 혼재하여 프레임워크 구조가 불명확하다. `opal/skills/`에는 이미 4개 스킬(opal-onboarding, opal-orchestrator, opal-project-dev-pilot, opal-skill-manager)이 존재한다.

## 이동 대상

### opal/skills/로 이동 (20개)

**오케스트레이터 (6개)**:
- opal-pilot-dev, opal-pilot-dev-short, opal-pilot-dev-wireframe
- opal-pilot-write, opal-pilot-write-tech, opal-project-pilot

**dev 단계 스킬 (7개)**:
- op-dev-analysis, op-dev-plan, op-dev-todo, op-dev-execute
- op-dev-test-scenario, op-dev-qa, op-dev-wireframe

**범용 단계 스킬 (4개)**:
- op-task, op-task-plan, op-task-execute, op-task-qa

**OPAL 전용 (3개)**:
- opal-project-init, opal-agent-creator, opal-skill-creator

### skills/에 잔류 (5개)

- api-analyzer, interview, ui-designer, web-to-markdown, wireframe-builder

## 요구사항

- [ ] 20개 스킬 디렉토리를 `skills/` → `opal/skills/`로 이동한다
- [ ] install-mac.sh의 배포 로직을 갱신한다 (opal/skills/ 경로 반영)
- [ ] opal-skills-registry.json의 경로를 갱신한다
- [ ] 하네스(opal-harness.md)의 스킬 탐색 경로를 갱신한다
- [ ] 에이전트 레지스트리(agents.md)의 탐색 경로를 확인한다
- [ ] 스킬 레지스트리(skills.md)의 경로를 갱신한다
- [ ] CLAUDE.md, README.md 등 문서의 소스 구조 설명을 갱신한다
- [ ] 배포본(~/.opal/skills/)은 변경 없음을 확인한다 (런타임 영향 없음)
- [ ] 이동 후 install-mac.sh 실행하여 배포 정상 동작을 확인한다

## 제약 조건

- 배포 경로(~/.opal/skills/)는 변경하지 않는다 — 소스 구조만 변경
- 스킬 내부의 SKILL.md, references/, personas/ 내용은 변경하지 않는다
- opal/skills/에 이미 존재하는 4개 스킬은 이동하지 않는다 (이미 위치)

## 기술 스택

- Shell (install-mac.sh)
- JSON (registry)
- Markdown (문서)

## 관련 문서

- `.opal/memory/project_skill_source_move.md` — 기존 예정 메모리
- `scripts/install-mac.sh` — 배포 스크립트
- `opal/core/references/opal-skills-registry.json` — 스킬 레지스트리
- `opal/core/references/opal-harness.md` — 하네스
- `opal/core/references/skills.md` — 스킬 목록
