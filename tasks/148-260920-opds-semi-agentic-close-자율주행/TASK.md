---
template: sdlc-v2
---
# TASK: semi-agentic 구현 이후 CLOSE 자율주행

## Problem
현재 `semi-agentic`은 PLAN-equivalent 사용자 승인 이후 EXECUTE·TEST를 자율 수행하면서도 CLOSE 진입 직전에 다시 사용자 승인을 요구한다. 해결 가능한 이슈가 없고 필수 검증이 모두 통과해도 파이프라인이 멈추므로, 비차단 진행 보고와 `transition_action=continue` 계약이 실제 완료까지 이어지지 않는다.

## Proposed outcome
`semi-agentic`은 PLAN-equivalent 승인 이후 구현·검증·CLOSE 최종 행까지 연속 수행하며, 구조화된 미해결 이슈나 별도 권한이 필요한 행동이 있을 때만 사용자 결정을 기다린다. `agentic`도 같은 CLOSE 자동진입 계약을 사용하고 `interactive`의 명시 승인 경계는 보존한다.

## Affected users and systems
영향 대상은 OPAL Pilot을 사용하는 소유자와 PM, 공통 mode/guard/state 전이 계약, `state-tool`, 각 Pilot 스킬과 배포 설치본이다. 허브 merge·push·배포·worktree 제거의 별도 사용자 권한은 범위에서 제외한다.

## Constraints
- C-1: `interactive`의 단계별 사용자 승인과 CLOSE 승인 계약은 변경하지 않는다.
- C-2: `semi-agentic`의 PLAN-equivalent 이전 사용자 확인 경계는 변경하지 않는다.
- C-3: 계속·대기·차단 판정은 산문이 아니라 `state-tool`의 `transition_action`과 `report_type`이 소유해야 한다.
- C-4: 요구사항 모호성, 계약 충돌, 사용자 선택, 사람 전용 검증, 권한 부족, 보안·데이터 손실 위험, 재시도 상한 초과는 기존 에스컬레이션 경계를 유지한다.
- C-5: 허브·기본 브랜치 merge와 push, 배포, 이력 재작성, worktree 제거는 자동 CLOSE 권한에 포함하지 않는다.
- C-6: 기존 `state.json`과 Pilot별 pipeline 행 구조를 깨지 않는 하위호환 변경이어야 한다.
- C-7: 실행 규칙은 공통 SSOT에 두고 Pilot별 문서의 중복·상충 문구를 제거하거나 공통 계약 참조로 정합화한다.

## Acceptance criteria
- AC-1: `semi-agentic`에서 PLAN-equivalent 사용자 승인이 완료된 뒤 EXECUTE·TEST/VERIFY가 통과하면 추가 사용자 발화 없이 CLOSE 첫 행과 `close.final`까지 진행한다.
- AC-2: `agentic`은 정상 경로에서 별도 CLOSE 사용자 승인 없이 `close.final`까지 진행한다.
- AC-3: `interactive`는 종전처럼 CLOSE 진입 전에 `owner=user` 확인이 없으면 도구가 거부한다.
- AC-4: `semi-agentic`의 PLAN-equivalent 이전 미완료 사용자 확인 행은 자동 승인되지 않는다.
- AC-5: 사용자 확인 행이 없는 Pilot도 `semi-agentic`·`agentic`이면 CLOSE에 자동 진입하고 `interactive`이면 사용자 승인을 요구한다.
- AC-6: `transition_action=await_user|blocked`인 실제 미해결 이슈에서는 자율주행이 중단되고, `progress_report + continue`에서는 보고 후 다음 행으로 이어진다.
- AC-7: 모든 적용 대상 Pilot 문서와 README에서 CLOSE 사용자 승인 예외 문구가 새 mode-aware 계약과 일치한다.
- AC-8: `state-tool` mode/transition/CLOSE 회귀 테스트가 세 모드와 확인 행 유무를 포함해 통과한다.
- AC-9: source와 설치본의 변경 계약이 동기화되고 실제 공개 CLI 검증이 통과한다.
