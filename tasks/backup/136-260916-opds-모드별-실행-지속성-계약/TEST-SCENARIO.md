---
template: sdlc-v2
---
# TEST-SCENARIO: 모드별 실행 지속성 계약

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: task 136 worktree의 Python 테스트 환경, Bash, Node.js, `state-tool`, 전체 Pilot pipeline JSON과 source 하네스·어댑터 파일
- 공통 데이터: 테스트가 임시 디렉토리에 생성하는 mode별 state fixture와 저장소의 Pilot pipeline fixture
- 대역 사용과 한계: 외부 서비스 대역은 사용하지 않는다. 플랫폼 Stop 행동은 source 훅 계약과 설치 산출물을 자동 검사하고, 실제 런타임의 응답 종료 억제 가용성은 해당 플랫폼 어댑터 지원 범위로 한정한다.
- 실행 조건: 자동 실행. 테스트는 사용자 소유 파일·허브 worktree를 변경하지 않는다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-2, AC-3, C-1, C-2, C-3, C-4, H-3 | interactive·semi-agentic·agentic mode와 Pilot별 단계 경계 fixture가 있다. | 각 경계에서 공개 CLI로 상태를 전이하고 구조화 출력을 수집한다. | 모든 결과가 `continue`, `await_user`, `blocked`, `complete` 중 하나이며, interactive는 단계별 `await_user`, semi-agentic은 Pilot 경계 전/후에 따라 `await_user`/`continue`, agentic은 예외 외 `continue`를 반환한다. 산문 보고 문구는 판정을 바꾸지 않는다. | Python unit·CLI integration | 구현 전 RED |
| S-2 | AC-2, AC-7, C-4 | TASK·PLAN 등 중간 단계가 완료되고 `transition_action=continue`이다. | 공통 하네스와 모든 Pilot의 단계 보고·승인 문구를 계약 테스트로 검사한다. | 비차단 보고는 `progress_report`로 분류되고 승인 질문을 내보내지 않으며, 실제 판단이 필요한 경우만 `decision_request`와 `await_user`를 같이 내보낰다. | Python contract test·source scan | 구현 전 RED |
| S-3 | AC-4, C-1, C-2, C-3, H-1 | TASK 완료 직후, 일반 단계 중간, CLOSE tail 중간에 종료된 state fixture가 있다. | `resolve-mode` 후 `show`와 다음 행 `advance`/`mark`로 재개한다. | 저장 mode와 프론티어가 유지되고, 마지막 완료 행 이전에는 `complete`를 반환하지 않으며, legacy 단일 CLOSE 행 state도 호환 경로로 재개된다. | Python unit·CLI integration | 구현 전 RED |
| S-4 | AC-4, AC-5, C-5, H-1 | 각 Pilot pipeline에 명시적 CLOSE tail이 정의되어 있다. | DONE.md, 문서 동기화, brain ingest, 회고, worktree finalize/attribution, final 행을 순차로 완료한다. | CLOSE 진입은 사용자 소유 승인 없이 차단되고, tail 중간은 `continue`이며, 명시 final 행이 끝난 뒤에만 `completed_unmerged`/`complete`가 된다. | Python unit·pipeline fixture integration | 구현 전 RED |
| S-5 | AC-3, AC-4, AC-7, C-1, C-2, C-3, C-5 | dev full/short, legacy short, wireframe, project, write-tech, data-design, GC, SDD, project-dev, project-loop pipeline이 있다. | cross-Pilot conformance 검사를 실행한다. | 모든 Pilot이 모드 경계 메타데이터·공통 전이 vocabulary를 사용하고, 명시적 CLOSE final 행을 가지며, 무조건 승인 요청 문구와 중복 전이 정의가 없다. | Python contract test·JSON schema validation | 구현 전 RED |
| S-6 | AC-6, C-3, C-4, H-2 | state-tool이 `transition_action=continue`을 내보내고 플랫폼 어댑터·훅 source가 있다. | Claude Stop hook과 설치 어댑터 계약 테스트를 실행하고, 훅 미지원 플랫폼의 재개 정보를 검사한다. | 지원 플랫폼은 `continue`인 활성 state의 응답 종료를 감지해 계속·재개를 유도하고, 미지원 플랫폼도 `next_action`/`transition_action`을 손실하지 않는다. | Hook fixture·install script contract test | 구현 후 |
| S-7 | AC-7, C-6 | source 변경이 있고 허브에 사용자 미커밋 변경이 존재한다. | source 회귀, archive/install 계약, 변경 경로 경계를 검증한다. | 설치 산출물은 source 계약과 일치하고, 기존 사용자 변경은 유지되며, 커밋·병합이 실행되지 않는다. | Git diff boundary·archive/install tests | 구현 후 |
