---
template: sdlc-v2
---
# TASK: 훅 세션 식별 분리

## Problem
작업 중인 부모 세션의 ID를 상속한 자식 Claude CLI가 종료될 때 부모 태스크 lease와 세션 레지스트리가 해제·종료 처리된다. 원인은 훅 봉투의 session_id보다 환경변수 OPAL_SESSION_ID를 우선하는 식별 경로다 (`opal/tools/ownership-tool/ownership_tool/ownership_core.py:351`, `session_end_hook.py:59`). 격리 프로젝트에서 실 CLI `claude mcp get context7`와 `claude mcp list` 성공 종료 후 부모 owner.json= released, 세션=closed를 독립 재현했고 부모 ID를 제거한 대조에서는 둘 다 active였다 (REPRO-EVIDENCE.md).

## Proposed outcome
자식 CLI 실행과 종료가 부모 태스크 소유권을 변경하지 않는다. 훅은 해당 이벤트가 식별한 세션에만 작용하며, 신원이 없는 이벤트는 부모 신원으로 대체하지 않는다. 일반 CLI의 명시 세션/환경변수 기반 사용은 호환을 유지한다.

## Affected users and systems
OPAL PM·워커, ownership-tool 훅과 일반 CLI 소비자, installer나 headless 실행에서 자식 Claude 명령을 실행하는 사용자. ownership-tool 코드·테스트·관련 계약 문서가 대상이다. task 152 코드, lease 저장 잠금의 동시성 개선, installer 기능 변경은 제외한다.

## Constraints
- C-1: 훅 이벤트의 세션 ID와 일반 CLI의 세션 식별을 분리한다. 공용 함수의 전역 우선순위 교체로 일반 CLI 계약을 바꾸지 않는다.
- C-2: 훅 이벤트의 ID가 없거나 유효하지 않으면 부모 환경변수로 대체하지 않고 진단과 무변경으로 종료한다.
- C-3: 실제 사용자 세션의 lease를 해제하거나 다른 탭을 종료하지 않는다. 모든 실 CLI 검증은 임시 프로젝트·가짜 세션·격리된 훅 설정 및 임시 배포본에서 수행한다.
- C-4: 프로젝트 소스를 수정한다. ~/.opal 배포본 직접 편집, 허브 변경 덮어쓰기, 무단 merge/push/실사용 배포는 하지 않는다.
- C-5: 사용자는 agentic PM 직접 수행과 전용 worktree를 승인했다. 독립 시나리오 평가·테스트 경계를 유지한다.

## Acceptance criteria
- AC-1: 부모 ID를 상속한 실제 claude mcp get/list 성공 종료 후 부모 lease와 세션 레지스트리가 active로 유지된다.
- AC-2: 부모와 다른 자식 ID의 종료 이벤트는 자식 소유 lease만 해제하고 부모 lease·레지스트리의 바이트를 보존한다.
- AC-3: 부모 자신의 정상 종료 이벤트는 부모 lease를 released, 레지스트리를 closed로 전환한다.
- AC-4: ID 누락·공백·비문자 훅 이벤트는 진단을 반환하고 소유권·세션 파일을 변경하지 않는다.
- AC-5: ownership-tool 훅 소비자에서 환경변수 우선 신원 판별 잔존이 없고, 일반 CLI·state-tool의 환경변수 기반 사용 및 타 세션 live lease 획득 거부는 회귀 없이 유지된다.
- AC-6: ownership-tool 관련 회귀 스위트와 독립 검증이 통과하고, 실 CLI 재현의 수정 전 실패·수정 후 성공 증거를 보존한다.
