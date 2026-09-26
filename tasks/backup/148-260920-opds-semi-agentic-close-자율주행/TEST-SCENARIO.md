---
template: sdlc-v2
---
# TEST-SCENARIO: semi-agentic 구현 이후 CLOSE 자율주행

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 프로젝트 source checkout과 임시 디렉터리에서 `opal/tools/state-tool/run.sh` 공개 CLI를 실행한다. 설치본 검증은 별도 배포 승인을 받은 경우에만 `~/.opal/tools/state-tool/run.sh`를 사용한다.
- 공통 데이터: 실제 Pilot pipeline fixture와 테스트가 생성하는 임시 `state.json`을 사용하며, `state.json`·pipeline JSON을 손편집해 통과시키지 않는다.
- 대역 사용과 한계: mock·patch·가짜 CLI를 사용하지 않는다. 파일 시스템과 공개 CLI subprocess를 실제로 실행하며, 설치본 검증은 source 검증을 대신하지 않는다.
- 실행 조건: 자동 실행. 허브 merge·push·배포·worktree 제거가 필요한 단계는 사용자 권한을 받은 뒤에만 실행하고, 권한이 없으면 source↔설치 대상 정적 동기화 검사까지만 수행한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-2, AC-3, AC-5, AC-8, C-1, C-3, C-6, H-2, H-3 | 사용자 확인 행이 있는 opd/opds fixture와 확인 행이 없는 opgc fixture를 각각 `interactive`, `semi-agentic`, `agentic`으로 초기화하고 CLOSE 직전 필수 행을 완료한다. | source `state-tool` 공개 CLI로 CLOSE 첫 행을 `advance`와 `mark` 양쪽에서 진입한 뒤 명시 `close.final`까지 순서대로 완료한다. | semi-agentic·agentic은 확인 행 유무와 무관하게 별도 사용자 발화 없이 첫 CLOSE가 성공하고, 확인 행이 있으면 `done/auto`와 `auto_approved`가 기록되며, 전이는 `continue/progress_report`를 유지하다 `close.final`에서만 `complete`가 된다. interactive는 `owner=user` 전에는 `await_user/decision_request`로 거부되고 승인 후에만 통과한다. 기존 row key·순서·스키마는 변하지 않는다. | Python unittest + 실제 `run.sh` subprocess | 구현 전 RED, 구현 후 |
| S-2 | AC-4, C-2 | semi-agentic fixture의 TASK·PLAN-equivalent 사용자 확인 행이 pending이다. | 다음 PLAN-equivalent 작업 행 진입을 공개 CLI로 시도한다. | 미완료 확인 행이 자동 승인되지 않고 `user_confirmation_required`와 `await_user/decision_request`가 반환되며 상태 파일은 승인 전 상태를 유지한다. | Python unittest + 실제 `run.sh` subprocess | 구현 후 |
| S-3 | AC-6, C-3, C-4 | 정상 진행 fixture와 함께 구조화 blocker, 실패 행, 사용자 선택 필요, 사람 전용 검증, 재시도 상한 초과 사례를 준비한다. | 각 사례에서 `show`와 해당 전이 명령을 실행하고 반환 JSON을 비교한다. | 정상 `progress_report + continue`만 다음 행으로 이어지고, 실제 미해결 사례는 `await_user` 또는 `blocked`와 `decision_request` 조합으로 멈춘다. CLOSE 자동진입 변경이 보안·데이터 손실·권한 부족 에스컬레이션을 우회하지 않는다. | 전이 계약 unittest + 공개 CLI JSON 검증 | 구현 후 |
| S-4 | AC-8, C-6, H-1 | CLOSE 직전 확인 행이 pending이고, 뒤따르는 artifact/stage guard가 실패하도록 실제 fixture를 구성한다. | 첫 호출의 `state.json` 바이트와 run-log 사건을 보존해 둔 뒤 실패하는 CLOSE 진입을 실행하고, 조건을 고친 뒤 같은 호출을 재시도한다. | 실패 호출은 확인 행만 먼저 승인하는 부분 저장을 남기지 않고 `state.json`이 바이트 동일하다. 성공 호출은 확인 행 승인과 CLOSE 전이를 한 번에 저장하고 `auto_approved`, owner, note, state.changed 순서가 일치한다. | 공개 CLI subprocess + 파일/JSONL 실측, mock 없음 | 구현 전 RED, 구현 후 |
| S-5 | AC-7, C-1, C-2, C-7 | 공통 mode/guard/state 문서, 세 mode 하네스, 10개 적용 대상 Pilot SKILL/README, 공개 README를 대상으로 한다. | 구계약 문자열과 새 공통 mode-aware 계약 포인터를 정적 검사하고 shared/conformance 테스트를 실행한다. | semi-agentic·agentic의 CLOSE 사용자 승인 필수/`--auto-pass` 거부 문구가 제거되거나 새 공통 계약으로 정합화되고, interactive 승인과 PLAN-equivalent 이전 semi-agentic 확인은 유지된다. Pilot별 중복 규칙은 공통 SSOT를 다시 정의하지 않는다. | `rg` 정적 검사 + Pilot shared/conformance unittest | 구현 후 |
| S-6 | AC-9, C-5, H-4 | source 테스트가 모두 통과하고 installer 입력 source와 배포 대상 목록을 확인할 수 있다. | source와 installer가 배치할 state-tool·하네스·Pilot 자산의 동기화를 검사한다. 별도 배포 승인이 있으면 installer 실행 후 설치본 공개 CLI로 S-1의 세 mode 대표 경로를 재실행한다. | 승인 전에는 `~/.opal/`을 쓰지 않고 source와 배포 대상 계약의 일치만 증명한다. 승인 후 설치본을 검증하는 경우 source와 동일한 mode별 CLOSE 전이·`close.final` 결과가 나온다. | 정적 배포 매핑 검사 + 승인 시 실제 installer/설치본 CLI | 설치 후 |
| S-7 | C-5 | 변경된 source와 태스크 산출물이 존재하고 외부 Git·배포·worktree 권한은 부여되지 않았다. | 테스트와 diff를 점검해 허브·기본 브랜치 commit/merge/push, rebase/reset/amend, 배포, worktree 제거 실행 여부를 확인한다. | 권한 밖 행동은 0건이고, 자동 CLOSE는 태스크 내부 행 전이에만 영향을 준다. `opal-pilot-project-build`의 P5 merge gate는 기존 사용자 권한 경계를 유지한다. | git status/diff 및 실행 로그 실측 | 구현 후 |
