<!--
원본: 태스크 163(opds-코덱스-워크트리-부팅-소유권-복구), 설계 게이트 i1 (verdict=fail, rewrite_target=plan)
인용 gaps 원문:
"checkpoint 허브 쓰기 실패의 권한 상승 또는 허브 확정 중 하나를 확정해야 한다."
"cmux status 지원 여부와 미지원 계약을 확정해야 한다."
axes: completeness=PASS, decision_clarity=FAIL, executability=FAIL, recoverability=PASS
이 fixture는 170 W-5 평가 세트용 합성 최소 재현본이다. design-gate를 이 파일에 실제로 돌리지 않는다.
-->
---
template: sdlc-v2
---
# TASK: 코덱스 워크트리 부팅 소유권 복구(합성 축소판)

## Problem

코덱스 어댑터로 워크트리를 부팅할 때 checkpoint 커밋이 허브 쓰기 권한 부족으로 실패하는 경우가 있다.

## Proposed outcome

워크트리 부팅 시 checkpoint 커밋이 허브 쓰기 실패 상황에서도 명확한 복구 경로를 갖는다.

## Affected users and systems

worktree-tool, 코덱스 어댑터, cmux 세션.

## Constraints

- C-1: 기존 checkpoint 커밋 포맷을 바꾸지 않는다.

## Acceptance criteria

- AC-1: checkpoint 허브 쓰기가 실패하면 명확한 오류 코드와 복구 안내를 반환한다.
- AC-2: cmux 세션이 없는 환경에서도 부팅이 안전하게 동작하거나 명확히 실패한다.
