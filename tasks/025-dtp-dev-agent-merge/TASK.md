# TASK: dtp-dev-full-agent + dtp-dev-short-agent → dtp-dev-agent 통합

> 작성일: 2026-03-21 | 작업 유형: 개선

## 작업 목표

dtp-dev-full-agent와 dtp-dev-short-agent를 하나의 dtp-dev-agent로 통합한다. 90% 동일한 내용(실행 프로세스, 반환 형식, 실행 규칙, STATE.md 갱신)을 공통 섹션으로 묶고, 차이점(단계별 가이드 매핑, EXECUTE 모드별 규칙)만 개별 섹션으로 분리한다.

## 배경

- 024 태스크에서 모드별로 에이전트를 분리했으나, 비교 결과 두 에이전트의 90%가 동일
- 오케스트레이터가 이미 단계명(ANALYSIS/PLAN-SHORT 등)을 명시적으로 전달하므로, 에이전트가 모드를 구분할 필요 없음
- execute-guide.md도 이미 단순/복잡/Short 3가지를 하나로 통합해서 다루고 있음
- 에이전트 파일 6개(2×3플랫폼)를 3개(1×3플랫폼)로 줄여 관리 부담 감소

## 요구사항

- [ ] R1: dtp-dev-full-agent + dtp-dev-short-agent → dtp-dev-agent 통합 (claude)
- [ ] R2: dtp-dev-agent 통합 (cursor)
- [ ] R3: dtp-dev-agent 통합 (antigravity)
- [ ] R4: 기존 dtp-dev-full-agent, dtp-dev-short-agent 삭제 (3플랫폼 × 2 = 6파일)
- [ ] R5: SKILL.md 라우터의 워커 에이전트명 갱신 (dtp-dev-full/short-agent → dtp-dev-agent)
- [ ] R6: modes/dev-full.md, modes/dev-short.md의 워커 에이전트명 갱신
- [ ] R7: agents.md 레지스트리 갱신 (2개 → 1개)
- [ ] R8: CLAUDE.md 에이전트 구조 갱신

## 제약 조건

- 기존 Full Task / Short Task / Wireframe UI 동작에 영향 없어야 함
- dtp-dev-agent 구조: 공통 섹션 + 개별 섹션(Full/Short 단계 매핑, EXECUTE 규칙)
- dtp-wireframe-ui-agent는 별도 유지 (스킬 호출 구조가 다름)

## 관련 문서

- 현재 dtp-dev-full-agent: `agents/claude/dtp-dev-full-agent/AGENT.md`
- 현재 dtp-dev-short-agent: `agents/claude/dtp-dev-short-agent/AGENT.md`
- SKILL.md: `skills/dev-task-pilot/SKILL.md`
- modes/: `skills/dev-task-pilot/modes/dev-full.md`, `modes/dev-short.md`
