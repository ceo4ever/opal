---
template: sdlc-v2
---
# TASK: 코덱스 세션 이관 복구

## Problem
사용자 장애 보고: Orca의 Codex에서 `//opds --agentic --pm --wt` 실행 시 워크트리는 생성되지만 `session_id_unresolved`로 lease 이관이 실패하고 `hub_owned`로 복귀한다. 소스에서도 Codex 환경변수 해석 누락과 launcher의 명시 신원 미전달을 확인했다 (`opal/tools/ownership-tool/ownership_tool/ownership_core.py:352`, `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py:187`).

## Proposed outcome
수동 export 없이 Codex 허브에서 Orca 전용 Codex 세션으로 작업 소유권을 이관하고 새 세션이 자기 신원으로 lease를 획득·유지한다. 실패하면 기존 안전 복귀와 터미널 정리를 유지하고 실제 원인을 구별할 수 있다.

## Affected users and systems
OPAL ownership-tool, worktree-launcher, 필요한 Codex 시작 통합과 worktree-tool 신원 소비 경로, 관련 테스트·계약 문서·배포 검증. 원래 장애 프로젝트 opal-studio/task_008은 읽기 참고만 하며 변경하지 않는다.

## Constraints
- C-1: 플랫폼 변수 접근은 adapter에 격리하고 OPAL_SESSION_ID 우선순위와 Claude 기존 동작을 보존한다.
- C-2: 임의 UUID를 생성하지 않는다. CODEX_SESSION_ID의 실제 수명·유일성 및 CODEX_THREAD_ID와 차이를 관측/공식 근거로 확인하고 불확실하면 명시한다.
- C-3: 부모 OPAL_SESSION_ID를 새 자식 세션의 신원으로 재사용하지 않는다. 훅은 payload session_id만 신뢰하는 기존 경계를 유지한다.
- C-4: source만 수정한다. ~/.opal 배포 파일 직접 수정, 다른 태스크/허브 변경의 커밋, 임의 강제 lease 탈취 금지.
- C-5: registry는 관측 상태이며 writer 권한은 lease로만 판정한다. 실패 시 hub_owned 원자 복귀와 terminal 정리를 보존한다.
- C-6: 실제 Orca/Codex 실행 증거를 mock 성공으로 대체하지 않는다. merge/push는 별도 승인 경계를 유지한다.

## Acceptance criteria
- AC-1: CODEX_SESSION_ID만 있을 때 ownership-tool status가 정상 해석하며 OPAL_SESSION_ID가 함께 있으면 중립 신원이 우선한다. 공백·누락 및 Claude 경로도 회귀 검증한다.
- AC-2: 명시 owner_session_id가 handoff와 handoff-cancel에 동일하게 전달되고 ambient 신원과 충돌해도 명시값을 따른다.
- AC-3: 새 Codex 세션이 부모와 다른 실제 신원으로 lease를 claim하고 heartbeat를 유지한다. 상속된 부모 OPAL_SESSION_ID를 사용하지 않는다.
- AC-4: 정상 이관 뒤 registry가 worktree_session_owned이고 lease의 새 세션 소유를 관측한다. 허브는 해당 태스크 writer를 중단한다.
- AC-5: 기동 실패 시 terminal 정리 및 hub_owned 원복을 유지하고 lease 실패 원인과 adapter·가용 신원 출처 이름을 진단한다. 식별자 원문을 불필요하게 노출하지 않는다.
- AC-6: 사용자 보고의 9개 회귀 시나리오를 테스트에 연결하고 관련 도구 회귀·독립 검증을 통과한다. 코드·계약·설치 경로 정합성과 source/installed 차이를 기록한다.
