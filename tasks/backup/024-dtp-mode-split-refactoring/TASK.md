# TASK: dev-task-pilot 모드별 스킬/에이전트 분리 리팩토링

> 작성일: 2026-03-21 | 작업 유형: 개선

## 작업 목표

dev-task-pilot의 단일 SKILL.md(1040줄)를 모드별 파일로 분리하고, 에이전트도 모드별로 분리하여 확장성과 유지보수성을 개선한다. 동시에 Wireframe UI 모드를 신규 추가한다.

## 배경

- 현재 SKILL.md에 Full Task + Short Task 로직이 모두 포함되어 1040줄로 비대
- Wireframe UI 파이프라인(TASK → WIREFRAME → EXECUTE → QA) 추가 필요
- 모드 추가 시마다 SKILL.md가 비대해지는 구조적 문제 해결 필요
- dtp-agent 하나가 모든 모드의 모든 단계를 처리하는 구조 → 모드별 전문 워커로 분리

## 요구사항

### 스킬 분리
- [ ] R1: SKILL.md를 라우터로 변환 (모드 판별 + 디스패치 + 공통 규칙만)
- [ ] R2: modes/dev-full.md — Full Task 파이프라인 분리
- [ ] R3: modes/dev-short.md — Short Task 파이프라인 분리
- [ ] R4: modes/wireframe-ui.md — Wireframe UI 파이프라인 신규 생성

### 에이전트 분리 (각 에이전트 × 3플랫폼: claude, cursor, antigravity)
- [ ] R5: dtp-agent 제거 → dtp-dev-full-agent, dtp-dev-short-agent, dtp-wireframe-ui-agent
- [ ] R6: dtp-qa 제거 → dtp-qa-dev-agent, dtp-qa-wireframe-agent
- [ ] R7: dtp-planner → dtp-action-plan-agent (리네임)
- [ ] R8: dtp-test → dtp-dev-test-agent (리네임)

### 신규 References
- [ ] R9: references/wireframe-task-guide.md — TASK 단계 가이드 (환경 검토, 입력물 분석)
- [ ] R10: references/wireframe-qa-guide.md — QA 검증 기준 (빌드/린트 + wireframe↔코드 대조)

### 레지스트리 업데이트
- [ ] R11: opal/core/references/agents.md — 에이전트 목록 갱신
- [ ] R12: CLAUDE.md — 에이전트 목록/구조 갱신

### Wireframe UI 모드 파이프라인
- [ ] R13: TASK 단계 — 목표 + 환경 검토 + 입력물 분류 (wireframe.md 있음/정책서/구두)
- [ ] R14: WIREFRAME 단계 — wireframe-builder 스킬로 wireframe.md 생성 (또는 스킵)
- [ ] R15: EXECUTE 단계 — ui-designer 스킬로 UI 구현
- [ ] R16: QA 단계 — 빌드/린트 + wireframe.md↔코드 대조 체크리스트

## 제약 조건

- 기존 Full Task / Short Task 동작에 영향을 주지 않아야 함
- 3플랫폼(claude, cursor, antigravity) 에이전트 포맷 규칙 준수
- references/ 기존 가이드(analysis-guide.md, plan-guide.md 등)는 수정하지 않음
- COMPONENT-CATALOG.md는 산출물에서 제외 (불필요)

## 관련 문서

- 현재 SKILL.md: `skills/dev-task-pilot/SKILL.md`
- 현재 dtp-agent: `agents/claude/dtp-agent/AGENT.md`
- 현재 dtp-qa: `agents/claude/dtp-qa/AGENT.md`
- 현재 dtp-planner: `agents/claude/dtp-planner/AGENT.md`
- 현재 dtp-test: `agents/claude/dtp-test/AGENT.md`
- wireframe-builder: `skills/wireframe-builder/SKILL.md`
- ui-designer: `skills/ui-designer/SKILL.md`
- 에이전트 레지스트리: `opal/core/references/agents.md`
