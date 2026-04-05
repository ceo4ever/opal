# TASK: opi 스킬에 tasks/ 태스크 기록 추가

> 작성일: 2026-03-30 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

opi(opal-project-init) 스킬이 초기화/최신화 수행 시 `tasks/` 폴더에 태스크 기록(TASK.md, DONE.md)을 남기도록 개선하여, 다른 오케스트레이터와 동일한 추적 일관성을 확보한다.

## 배경

현재 opi는 `.opal/MEMORY.md` 작업 히스토리에 1줄만 기록하고, `tasks/` 폴더에는 산출물을 남기지 않는다. 다른 오케스트레이터(opd, opds, opp)는 모두 `tasks/{NNN}-{name}/`에 체계적 기록을 남기는데 opi만 예외.

캡틴과 논의한 결과:
- tasks/ 기록이 필요 (추적 일관성, 최신화 이력, 파이프라인 일관성)
- opi는 독립 스킬이므로 최소한의 기록으로 충분 (TASK.md + DONE.md)
- STATE.md는 불필요 (opi는 세션 복원이 필요한 장기 작업이 아님)

## 요구사항

- [ ] opi SKILL.md에 tasks/ 태스크 기록 생성 프로세스 추가
- [ ] 태스크 폴더 구조: `tasks/{NNN}-opi-{프로젝트명}/` (TASK.md + DONE.md)
- [ ] TASK.md: Phase 1 분석 결과(프로젝트 카테고리, 기술 스택, 인터뷰 요약) 구조화
- [ ] DONE.md: 생성/변경된 문서 목록 + 핵심 결정 사항
- [ ] 기존 MEMORY.md 작업 히스토리 기록은 유지 (tasks/ 기록과 병행)

## 제약 조건

- opi의 기존 Phase 1~4 흐름을 깨지 않음
- STATE.md는 추가하지 않음 (불필요)
- PLAN.md, TEST-SCENARIO.md 등 복잡한 산출물 불필요

## 기술 스택

- 마크다운 문서

## 관련 문서

- `~/.opal/skills/opal-project-init/SKILL.md` — 수정 대상
- `~/.opal/references/opal-harness.md` — 하네스 공통 인프라 참조
