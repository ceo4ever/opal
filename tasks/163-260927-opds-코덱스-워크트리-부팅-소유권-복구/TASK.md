---
template: sdlc-v2
---
# TASK: Codex 워크트리 부팅 소유권 복구

## Problem
Codex 워크트리 세션이 허브 registry 쓰기 권한 오류로 부팅을 중단하며, launcher는 자식 lease 획득 전에 owner 없는 성공을 기록할 수 있다. 실패 복구도 살아 있는 자식과 허브 소유권이 겹칠 수 있어 태스크 162를 안전하게 재개하지 못한다.

## Proposed outcome
설치된 OPAL에서 Codex 워크트리 세션이 유효한 lease를 획득해 부팅하고, 허브가 같은 세션을 registry owner로 확정한다. 부팅 실패 시 확인된 상태에 따라 안전하게 복귀하거나 복구 필요 상태를 남기며, 원인과 다음 조치를 구조화해 보고한다. 수정·검증 범위의 상세 입력은 같은 폴더의 REQUEST.md에 보존한다.

## Affected users and systems
OPAL을 설치해 Codex 워크트리 태스크를 실행하는 사용자와 worktree-launcher, worktree-tool, ownership-tool, bootstrap, 설치 스크립트가 대상이다. 태스크 162는 배포 후 실제 재기동 검증 대상이다. 태스크 161의 작업 파일과 허브의 기존 미커밋 변경은 제외한다.

## Constraints
- C-1: 자식 세션의 쓰기 권한은 유효한 lease에 근거하며, 허브 registry의 최종 owner는 허브 측에서 확정한다.
- C-2: 종료·lease·owner 상태가 불확실하면 허브 소유로 추정 복귀하거나 새 자식을 중복 기동하지 않는다.
- C-3: 사용자 설정의 수정값과 다른 활성 워크트리의 파일·상태를 보존한다.
- C-4: 소스와 배포본을 함께 검증하고, 실제 명령과 터미널에서 성공·실패 경로를 확인한다.

## Acceptance criteria
- AC-1: Codex 워크트리 부팅 성공 시 lease owner와 registry owner가 동일한 실제 자식 세션 ID이며, owner 없는 성공이 발생하지 않는다.
- AC-2: 자식이 lease를 획득하지 못하거나 늦게 획득한 경우, 터미널 종료와 lease 상태에 맞는 결과가 반환되고 살아 있는 자식과 허브 소유권이 겹치지 않는다.
- AC-3: 종료나 lease 상태를 확인할 수 없는 실패는 복구 필요 상태로 남고, 명시 복구 절차 전에는 새 자식을 기동하지 않는다.
- AC-4: registry 권한 거부는 잠금 시간 초과와 구분되어 즉시 진단되며, lease 획득에 성공한 Codex 부팅은 그 기록 실패만으로 중단되지 않는다.
- AC-5: 구 Codex 기본 실행 명령을 쓰는 설치본은 지원되는 새 기본값으로 이관되고, 사용자 수정 명령은 보존된다.
- AC-6: 소스 테스트와 설치본 검증을 통과하고, 태스크 162의 재기동 및 첫 checkpoint 경로의 실제 결과가 기록된다.
