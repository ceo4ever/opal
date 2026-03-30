# DONE: opal-task-action-agent 신규 생성

> 완료일: 2026-03-30 | 스킬: //opp

## 변경 파일

| # | 파일 | 변경 유형 | 설명 |
|---|------|----------|------|
| 1 | `agents/opal-task-action-agent/AGENT.md` | 신규 | 액션 에이전트 — 6단계 파이프라인 + 검증 루핑(L1~L3b) 내장 |
| 2 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 수정 | v3.1 — Phase 3: opd/opds → opal-task-action-agent 디스패치 전환 |
| 3 | `opal/core/references/agents.md` | 수정 | opal-task-action-agent 레지스트리 등록 |
| 4 | `docs/ARCHITECTURE.md` | 수정 | 에이전트 목록 + 다이어그램 + 수량 갱신 (4→5개) |

> 배포본(`~/.opal/`)도 모두 동기화 완료.

## 핵심 설계 요약

### opal-task-action-agent
- oppd Phase 3 전용 에이전트 (AGENT.md, model: advanced)
- 6단계 파이프라인: PLAN → QA → TEST-SCENARIO → EXECUTE → VERIFY(L1~L3b) → TEST
- 사용자 게이트 없음 — 결과만 oppd에 반환
- 검증 루핑 내장: lint(무제한) → build(2회) → test(3회) → E2E(1회) + 회귀 방지
- 실패 시 `status: failed` + `failure_context` 반환 → oppd가 사용자 에스컬레이션

### oppd Phase 3 전환
- opd/opds 호출 → opal-task-action-agent 디스패치
- 에이전트 결과(status/verdict) 기반 후속 처리 테이블 정의
- 병렬 실행: worktree + Agent 병렬 디스패치
- opd/opds는 독립 호출(사용자 `//` 커맨드)용으로 유지

## 선행 태스크
- 053: 자동 검증 루핑 + 병렬 실행 설계 (가이드 문서)
- 056: opal-task-action-agent 생성 + oppd 연동 (이 태스크)
