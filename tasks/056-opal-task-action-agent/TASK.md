# TASK: opal-task-action-agent 신규 생성

> 작성일: 2026-03-30 | 작업 유형: 신규
> 입력: 053 태스크 논의 결과 (A/B/C안 검토 → C안 채택)
> 출력: TASK.md

## 작업 목표

oppd Phase 3에서 각 액션을 자율적으로 실행하는 `opal-task-action-agent`를 신규 생성한다. 기존 opd/opds를 수정하지 않고, 동일한 워커(opal-task-agent)와 단계 스킬(op-dev-plan, op-dev-execute 등)을 재사용하되, 사용자 게이트 없이 agentic하게 파이프라인을 완주하는 에이전트다.

## 배경

oppd(opal-pilot-project-dev)는 아이디어 → product까지 agentic 완주를 지향한다. 053 태스크에서 자동 검증 루핑 + 병렬 실행을 설계했으나, Phase 3에서 opd/opds를 호출하면 다음 문제가 발생한다:

1. **게이트 충돌**: opd/opds는 단계마다 사용자 승인을 요구 → agentic 완주 불가
2. **검증 루핑 중복**: opd/opds 내부 테스트와 oppd 레벨 검증 루핑이 겹침
3. **중첩 오케스트레이터**: 하네스에 정의되지 않은 패턴

A안(oppd 직접 오케스트레이션), B안(opd/opds agentic 모드), C안(새 에이전트)을 검토한 결과:
- C안 채택: 기존 opd/opds 수정 없이, 에이전트로 만들어 하네스 게이트 이슈 회피

## 요구사항

### 에이전트 정의

- [ ] `opal-task-action-agent` AGENT.md 신규 작성
- [ ] 입력: 액션 정의(목표, 범위, 검증 명령), 태스크 폴더 경로, 프로젝트 컨텍스트
- [ ] 프로세스: PLAN → QA → EXECUTE → 검증 루핑(L1~L3b) → TEST → 결과 반환
- [ ] 기존 워커(opal-task-agent) + 단계 스킬(op-dev-plan, op-dev-execute 등) 재사용
- [ ] op-dev-test-agent로 TEST-SCENARIO 기반 검증 수행
- [ ] 사용자 게이트 없음 — 결과만 oppd에 반환
- [ ] 실패 시 구조화된 결과 반환 (status, verdict, verification_log, failure_context)

### 검증 루핑 내장

- [ ] EXECUTE 완료 후 L1(lint) → L2(build) → L3a(unit/integration) → L3b(E2E) 계층적 검증
- [ ] 053에서 작성한 `verification-loop-guide.md`를 참조하여 구현
- [ ] 하네스 Guards의 재시도 한도 준수 (lint 무제한, build 2회, test 3회, E2E 1회)
- [ ] 회귀 방지 가드: 자동 수정 후 이전 통과 테스트 재실행
- [ ] 한도 초과/회귀 시 `status: failed`로 oppd에 반환

### oppd 연동

- [ ] oppd SKILL.md Phase 3 수정: "opd/opds 호출" → "opal-task-action-agent 디스패치"
- [ ] oppd에서 병렬 디스패치 가능 (worktree + Agent 도구)
- [ ] 053에서 작성한 `parallel-execution-guide.md` 참조
- [ ] STATE.md에 액션 결과 기록

### 레지스트리/문서 반영

- [ ] `agents.md` 레지스트리에 opal-task-action-agent 등록
- [ ] `docs/ARCHITECTURE.md` 에이전트 목록 갱신

## 제약 조건

- opd/opds SKILL.md 수정 금지 — 기존 사용자 주도 워크플로우 유지
- 하네스(opal-harness.md) 수정 최소화 — 에이전트이므로 게이트 적용 대상 아님
- 기존 단계 스킬(op-dev-plan, op-dev-execute 등) 수정 금지 — 재사용만
- 기존 워커(opal-task-agent, op-dev-test-agent) 수정 금지 — 재사용만
- 플랫폼 독립성 유지 (Claude/Cursor/Gemini 공통)

## 기술 스택

- OPAL 프레임워크 (마크다운 기반 스킬/에이전트 정의)
- 재사용 워커: opal-task-agent (standard), op-dev-test-agent (standard)
- 재사용 단계 스킬: op-dev-plan, op-dev-execute, op-dev-test-scenario, op-dev-qa
- 참조 가이드: verification-loop-guide.md, parallel-execution-guide.md

## 관련 문서

- `tasks/053-oppd-agentic-loop/` — 선행 태스크 (자동 검증 루핑 + 병렬 실행 설계)
- `~/.opal/skills/opal-pilot-project-dev/SKILL.md` — oppd 현재 구조
- `~/.opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` — 검증 루핑 가이드
- `~/.opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` — 병렬 실행 가이드
- `~/.opal/agents/opal-task-agent/AGENT.md` — 기존 범용 워커 (참고)
- `~/.opal/agents/op-dev-test-agent/AGENT.md` — 기존 테스트 에이전트 (참고)
- `~/.opal/references/opal-harness.md` — 하네스 (Guards, Gates, State)
- `docs/ARCHITECTURE.md` — 시스템 아키텍처
- `docs/CONVENTIONS.md` — 코드 컨벤션
