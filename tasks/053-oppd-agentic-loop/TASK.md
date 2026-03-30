# TASK: oppd Phase 3 agentic 자율 루핑 + 병렬 실행 설계

> 작성일: 2026-03-30 | 작업 유형: 신규
> 입력: 사용자 요청 + 메모리(task_agentic_loop.md) + 캡틴 피드백
> 출력: TASK.md

## 작업 목표

oppd가 아이디어 → product까지 자율 완주할 수 있도록, Phase 2(로드맵)에서 테스트 가능한 소단위 분할 원칙을 수립하고, Phase 3에서 자동 검증 루핑 + 병렬 태스크 실행 장치를 설계한다.

## 배경

oppd(opal-pilot-project-dev)는 아이디어 → product까지 agentic AI를 지향한다. 현재 Phase 3에서 opd/opds가 각 태스크를 실행하지만, 다음 한계가 있다:

1. **자동 수정 부재**: QA/TEST 실패 시 사용자가 직접 판단하고 재지시해야 함
2. **순차 실행만 가능**: 독립적인 태스크도 하나씩 순서대로만 실행
3. **태스크 단위 과대**: 로드맵 단계에서 테스트 가능성을 고려하지 않아, 실패 범위가 넓어 자동 수정이 어려움

현재 흐름:
- opd/opds 내부: EXECUTE → TEST-SCENARIO → (실패 시) 사용자 보고 → 사용자 판단
- oppd Phase 3: 태스크 완료 보고 → 사용자 승인 → 다음 태스크 (순차)
- QA Gate: 실패 시 워커에게 재지시 (최대 1회) → 여전히 실패 시 사용자 에스컬레이션

## 요구사항

### A. 로드맵 세분화 + actions 구조 (Phase 2 강화)

- [ ] 태스크 분할 시 "자동 테스트 가능성" 기준 추가 — 성공/실패를 기계적으로 판정할 수 있는 단위로 분할
- [ ] 각 태스크에 lint/build/test로 검증 가능한 명확한 완료 기준 명시
- [ ] 태스크 간 의존성 그래프를 작성하여 병렬 실행 가능 그룹 식별
- [ ] 분할된 태스크를 "액션(action)"으로 명명, `actions/A{NN}-{name}/` 하위에서 관리 (top-level tasks/ 오염 방지)

### B. 자동 검증 루핑 (Phase 3 — Layered Verification)

- [ ] 실패 유형별 루핑 전략 설계:
  - lint/format 오류 → 즉시 자동 수정 (루핑 카운트 제외)
  - 빌드/타입 에러 → 에러 메시지 기반 자동 수정 (1~2회)
  - 테스트 실패 → 실패 컨텍스트 전달 후 자동 수정 (최대 N회)
  - QA 리뷰 이슈 (설계/아키텍처) → 즉시 에스컬레이션
- [ ] 단계적 검증: EXECUTE 스텝마다 즉시 검증 (lint/build → test → 다음 스텝)
- [ ] 회귀 방지 가드: 자동 수정 후 이전 통과 테스트 재실행, 실패 시 루프 중단
- [ ] PM 루프 모니터링: 루프 한도 초과 시 사용자 에스컬레이션 흐름

### C. 병렬 태스크 실행 (Phase 3 — Parallel Execution)

- [ ] 의존성 그래프 기반 병렬 실행 가능 태스크 그룹 판별
- [ ] worktree 활용한 격리된 병렬 실행 전략 설계 (동시에 여러 태스크 수행)
- [ ] 병렬 태스크 완료 후 머지 전략 및 충돌 해결 흐름 정의
- [ ] 병렬 실행 시 STATE.md 동시 갱신 전략

### D. 스킬/하네스 반영

- [ ] oppd SKILL.md Phase 2(로드맵) 세분화 원칙 반영
- [ ] oppd SKILL.md Phase 3 자동 루핑 + 병렬 실행 반영
- [ ] 필요 시 opd/opds SKILL.md, 하네스(opal-harness.md) 변경 범위 정의
- [ ] roadmap-guide.md 태스크 분할 기준 강화

## 제약 조건

- 하네스 기존 규칙(Guards, Gates, State) 위반 불가 — 확장만 허용
- 기존 opd/opds의 내부 QA Gate 로직은 유지하고, oppd 레벨에서 상위 루핑을 추가하는 구조
- 무한 루프 방지: 반드시 최대 재시도 횟수 제한 존재
- 사용자 게이트는 유지 — agentic이지만 사용자 최종 확정 원칙 불변
- 플랫폼 독립성 유지 (Claude/Cursor/Gemini 공통)
- 병렬 실행 시 각 워커의 독립성 보장 (상호 간섭 없음)

## 기술 스택

- OPAL 프레임워크 (마크다운 기반 스킬/에이전트 정의)
- 대상 스킬: opal-pilot-project-dev (oppd), opal-pilot-dev (opd), opal-pilot-dev-short (opds)
- 관련 하네스: opal-harness.md (Guards, Gates, State)
- 병렬 실행: Agent 도구 (서브에이전트 병렬 디스패치), worktree (git 격리 브랜치)

## 관련 문서

- `~/.opal/skills/opal-pilot-project-dev/SKILL.md` — oppd 현재 구조
- `~/.opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` — 로드맵 가이드
- `~/.opal/skills/opal-pilot-dev/SKILL.md` — opd (Full Task)
- `~/.opal/skills/opal-pilot-dev-short/SKILL.md` — opds (Short Task)
- `~/.opal/references/opal-harness.md` — 하네스 공통 인프라
- `docs/ARCHITECTURE.md` — 시스템 아키텍처
- `.opal/memory/task_agentic_loop.md` — 캡틴 원래 요청
