---
template: sdlc-v2
---
# TASK: 모드별 실행 지속성 계약

## Problem
현재 Pilot 지시와 공통 TASK 프로세스에는 단계 보고 후 사용자 승인을 받도록 하는 문구와 agentic 자동 전이 계약이 함께 존재한다(`opal/core/references/harness/task-process.md:83`, `opal/skills/opal-pilot-dev/SKILL.md:67-74`). 이 충돌로 인해 TASK.md 등 중간 산출물을 작성한 다음, 실행 모드가 계속을 요구해도 응답이 종료될 수 있다. CLOSE의 마지막 상태 행이 후속 문서 동기화·brain·회고·worktree 처리보다 먼저 완료를 표시하는 구조도 있다(`opal/tools/state-tool/state_tool.py:2771-2786`).

## Proposed outcome
interactive, semi-agentic, agentic 각 모드가 모든 Pilot의 단계 경계에서 하나의 공통 전이 계약을 따르고, 결정론적 상태가 `continue`이면 중간 보고 후에도 다음 단계를 계속한다. 사용자 판단이 필요한 예외는 `await_user`, 실행 불가는 `blocked`, 전체 마감은 `complete`로 구분한다. CLOSE는 사용자 승인 후 모든 하위 절차가 끝난 뒤에만 완료로 표시된다.

## Affected users and systems
영향 대상은 OPAL Pilot을 사용하는 소유자·PM·워커, Pilot 오케스트레이터와 공통 하네스, `state-tool`, 플랫폼 어댑터·훅, 관련 회귀 테스트다. 범위는 `opd`/`opds`에 한정하지 않고 현재 Pilot 전체의 단계 전이와 CLOSE tail을 포함한다. 커밋·병합·외부 시스템 변경은 범위에서 제외한다.

## Constraints
- C-1: interactive는 각 단계 경계에서 사용자 확인을 기다린다.
- C-2: semi-agentic는 Pilot별 자율성 경계 이전에만 사용자를 기다리고, 경계 이후는 예외가 없으면 계속한다.
- C-3: agentic은 파괴적·비가역적·외부 영향 행위, 중대한 모호성, 재시도 한도 초과, 사람 전용 검증·권한, CLOSE 진입 승인 외에는 중단하지 않는다.
- C-4: 사용자 통지는 비차단 `progress_report`와 차단 `decision_request`로 구분하고, 전이 판정은 산문이 아닌 결정론적 상태·도구 출력을 근거로 한다.
- C-5: CLOSE 진입은 모드와 무관하게 사용자 승인을 유지하며, CLOSE 하위 절차를 명시적 상태 행으로 관리한다.
- C-6: 사용자의 기존 변경과 태스크를 보존하고, 커밋은 명시 요청 없이 수행하지 않는다.

## Acceptance criteria
- AC-1: 공통 전이 결과 `continue | await_user | blocked | complete`와 모드별 판정 규칙이 단일 계약으로 정의되고 모든 Pilot이 이를 참조한다.
- AC-2: TASK·ANALYSIS·PLAN·TEST-SCENARIO·EXECUTE·TEST 등 전체 단계의 중간 보고가 agentic `continue`를 종료 신호로 바꾸지 않는다.
- AC-3: interactive, semi-agentic, agentic 세 모드×전체 단계 경계 매트릭스가 자동 테스트로 검증된다.
- AC-4: 중단 주입 후 재개, TASK 직후 계속, CLOSE tail 재개, Pilot 간 정합성이 회귀 테스트로 검증된다.
- AC-5: CLOSE의 완료 상태는 DONE.md, 관련 문서 동기화, brain ingest, 회고, worktree finalize 등 필수·조건부 하위 행이 모두 정상 종료된 후에만 설정된다.
- AC-6: 플랫폼이 지원하는 경우 `continue`인 상태에서 응답 종료를 방지하는 어댑터·훅 가드가 작동하고, 미지원 플랫폼은 상태 계약으로 동일한 재개 정보를 보존한다. 현재 Claude Stop hook은 통지만 수행한다(`opal/core/hooks/claude-hooks.json:33-43`).
- AC-7: 단계 보고 문구, Track 변경 제안, 상태 전이, CLOSE 마감 구조의 충돌 표현이 제거되고 관련 문서·설치 산출물 회귀가 통과한다.
