---
template: sdlc-v2
---
# TEST-SCENARIO: Codex 워크트리 부팅 소유권 복구

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 격리된 테스트용 허브와 전용 worktree에서 source pytest 및 installer bash 테스트를 실행한다. 실제 터미널 검증은 Orca가 설치된 호스트에서 수행한다.
- 공통 데이터: lease가 pending/live/expired/absent인 fixture와 registry가 session_launching/recovery_required인 fixture. 실제 162 세션은 배포 승인 후에만 다룬다.
- 대역 사용과 한계: 단위 테스트의 fake adapter·lease는 실패 순서와 도구 호출 횟수 검증에 한정한다. 실제 Codex 부팅, 허브 registry 권한, Orca 터미널 종료, 설치본 checkpoint를 대신하지 않는다.
- 실행 조건: source 테스트는 자동 실행. install과 162 종료·재기동·첫 checkpoint는 권한 경계에 닿기 전 멈춰 보고하고 별도 승인 뒤 실제 환경에서 수행한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1 | pending·만료·부재 lease 및 live 허브 owner | `ownership-set --owner-from-lease`를 호출 | 앞의 세 lease는 `owner_lease_unresolved`, 허브 owner는 `owner_lease_mismatch`; 전부 registry 바이트 불변 | pytest / worktree-tool | 구현 전 RED |
| S-2 | AC-1, AC-2, C-1, C-2 | 자식 live lease owner와 기대 owner 일치 또는 불일치 | 최종 전이를 호출하고 동시 owner 변경을 삽입 | 일치 시 registry owner가 실제 자식 ID, 불일치 시 전이 0회·단일 실패 복구 경로 | pytest / worktree-tool·launcher | 구현 전 RED |
| S-3 | AC-2, AC-3, C-2 | claim 없음, close 성공·실패·잔존, handoff noop·실패, lease 재조회 실패 | timeout과 실패 복구를 실행 | 확인된 종료와 안전한 lease만 hub_owned; 불명은 recovery_required와 `launch_recovery_required`, 재기동 차단 | pytest / launcher | 구현 전 RED |
| S-4 | AC-2, AC-3, C-2, H-1 | Orca show가 present/stale/기타 오류이고 list가 비거나 남음 | `status(handle)`와 `status_worktree(root)` 호출 | stale와 list 부재의 이중 증거만 absent; 나머지 오류·모호함은 unknown | pytest / Orca adapter fixture 및 실제 조회 | 구현 전 RED |
| S-5 | AC-3, C-2 | recovery_required에 handle 또는 worktree root가 보존됨 | `recover`를 실패·성공 조건에서 각각 호출 | 부재 확인·cancel·lease 확인 전에는 상태 불변; 모두 확인되면 hub_owned와 보존값 소거 | pytest / launcher·worktree-tool | 구현 전 RED |
| S-6 | AC-4, C-1 | lock `os.open`이 EPERM/EACCES/EROFS를 반환; lease claim 성공 후 허브 registry 기록만 거부 | worktree-tool·ownership-tool·codex-start 호출 | 권한 오류는 30초 대기 없이 `registry_write_denied`; codex-start는 이 경우만 ok와 `registry_owner_deferred_to_hub` 진단, foreign owner는 실패 | pytest / 두 도구 및 실제 Codex sandbox | 구현 전 RED |
| S-7 | AC-5, C-3 | 신규 설정·정확한 구 기본 argv·사용자 수정 argv | Mac/Windows 설정 이관 함수를 실행 | 신규·구 기본은 `--no-daemon`, 수정 argv는 바이트 보존 | installer bash/PowerShell 테스트 | 구현 후 |
| S-8 | AC-2, AC-5, H-2 | 지원되지 않는 Codex 인자 또는 존재하지 않는 실행 명령 | 테스트용 worktree launcher를 실제 기동 | 자식 lease 미획득 후 bounded timeout, 터미널 부재 확인, `session_boot_timeout`과 hub_owned 자동 복귀 | source integration + 실제 Orca 터미널 | 설치 후 |
| S-9 | AC-1, AC-4, AC-6, C-1, C-4 | source 테스트 통과 및 install 완료; 162 기존 자식 종료 3중 확인 | 개인 launcher 설정을 수정하지 않고 162를 Codex로 재기동 | codex-start ok, lease·registry owner가 동일한 자식 ID, PLAN 행 in_progress | 설치본·실제 Orca/Codex | 배포 후 |
| S-10 | AC-6, C-3, C-4, H-3 | S-9에서 획득한 자식 세션과 정상 worktree branch | 첫 `worktree-tool checkpoint` 실행 | checkpoint SHA와 registry 기록이 일치하거나, 권한 거부이면 설계한 상승·허브 확정 경로가 명시적으로 작동 | 설치본·실제 Codex sandbox | 배포 후 |
