---
template: sdlc-v2
---
# TEST-SCENARIO: --wt 워크트리 세션으로의 태스크 소유권 이관 계약

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: macOS. OPAL 소스 checkout `/Volumes/Data/AIStudio/workspace/ai-framework`, 실행 인터프리터 `~/.opal/.venv/bin/python`. 단위 검증은 임시 task 디렉터리와 고정 `now` 인자로 수행하며 실제 `~/.opal` 배포본과 진행 중인 태스크를 건드리지 않는다.
- 공통 데이터: 임시 허브 루트 아래 `.opal-worktrees/.meta/task_NNN.json`(registry meta 발급 6종 필드)과 `<task_path>/run/.runtime/owner.json`을 케이스별로 조립한다.
- 대역 사용과 한계: launcher 단위 검증에서 터미널 어댑터는 launch 보고 dict를 반환하는 stub을 주입한다. 이유는 실제 터미널 기동이 단위 환경에서 재현·정리 불가능하기 때문이다. 한계는 실제 SessionStart 훅 발화와 훅 배선 경로를 검증하지 못한다는 점이며, 이 부분은 S-14가 설치 후 실제 `--wt` 태스크 1건으로 별도 확인한다.
- 실행 조건: S-1~S-13과 S-16~S-18은 자동 실행이다. S-14와 S-15는 `scripts/install-mac.sh` 실행과 실제 lease 변경을 수반하므로 소유자 승인이 필요한 협업 조건이며, 승인 전에는 태스크 149의 `run/.runtime/owner.json`을 변경하지 않는다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-3, H-2 | 허브 세션이 소유한 live lease를 그 세션이 이관한 직후. 허브 cwd는 허브 루트다 | 허브 세션 id와 허브 루트를 claimant 루트로 삼아 claim을 재시도한다 | claim이 거부되고 진단이 이관 대기를 가리킨다. 레코드의 소유자 필드는 비어 있고 이관 대상 루트는 registry 발급값 그대로다 | unit, pytest, 임시 task 디렉터리 + 고정 now | 구현 전 RED |
| S-2 | AC-2, C-2, H-1 | 이관 대기 상태의 lease. claimant 루트가 (a) registry 발급 worktree 루트와 realpath 동치 (b) 그 하위 디렉터리 (c) symlink를 경유해 같은 실체를 가리키는 경로 3가지 | 각 루트에서 세션 id로 claim한 뒤, 같은 세션으로 PreToolUse 가드 판정 함수를 Edit·Write·쓰기 Bash 명령 봉투로 호출한다 | (a)·(b)·(c) 모두 claim 성공이며 generation이 1 증가한다. 가드 판정이 차단을 반환하지 않는다 | unit, pytest — 가드는 `pretooluse_guard_hook.handle`을 직접 호출 | 구현 전 RED |
| S-3 | AC-1, H-4 | 이관 대기 상태의 lease와, 그 이관을 수행한 허브 세션 id | 허브 세션 id로 heartbeat 갱신을 호출한다 | 아무 파일도 쓰이지 않고 no-op으로 반환된다. 레코드의 소유자 필드와 이관 필드가 변하지 않는다 | unit, pytest | 구현 후 |
| S-4 | C-3 | 이관 대기 상태의 lease. claimant 루트가 이관 대상 루트와 무관한 제3 경로다 | 제3 세션 id로 claim한다. claimant 루트를 생략한 claim도 같이 시도한다 | 두 경우 모두 거부된다. 레코드가 변하지 않는다 | unit, pytest | 구현 전 RED |
| S-5 | AC-5, AC-7, C-5 | CLI 표면 신설 후. 소유자 세션과 비소유자 세션 2종 | 조회·해제·이관·이관취소 4서브명령을 정상 인자로 실행하고, 비소유자 세션으로 해제를 실행하고, 상대경로 인자로 실행한다 | 전 경로가 단일 라인 JSON을 반환한다. 비소유자 해제는 소유자 불일치 오류와 0이 아닌 종료코드다. 상대경로는 절대경로 아님 오류로 거부된다. CLI 모듈 본문에 플랫폼 고유 환경변수명이 없다 | unit, pytest + 소스 grep | 구현 전 RED |
| S-6 | AC-6 | 임시 태스크에 특정 세션이 소유한 live lease가 있다 | 그 세션으로 해제를 실행한 뒤 조회하고, 이어서 다른 세션 id로 claim한다 | 해제가 성공하고 조회 결과가 무소유다. 다른 세션의 claim이 성공한다 | unit, pytest | 구현 전 RED |
| S-7 | AC-3, AC-4 | lease가 이관 대기 상태다. (a) 이관 대상 worktree 루트를 cwd로 하는 SessionStart 봉투 (b) 이관 대상이 아닌 cwd의 SessionStart 봉투 | 각각 SessionStart 처리 함수를 호출한다 | (a)는 claim 성공이고 registry의 실행 소유자 세션 id가 실제 세션 id로 기록된다. (b)는 claim 실패이며 registry 미등록 사유가 진단 목록에 남고 반환 키 집합은 변하지 않는다 | unit, pytest | 구현 전 RED |
| S-8 | AC-1, C-4 | registry meta가 발급한 worktree 루트와 canonical task 경로. 어댑터는 정상 launch 보고를 반환하는 stub | launcher 실행 함수를 1회 호출하고 호출 순서를 기록한다 | 이관 호출이 어댑터 launch 호출보다 먼저 정확히 1회 발생한다. 이관에 전달된 대상 루트와 task 경로가 registry 발급값과 일치한다. launcher 모듈 본문에 lease 파일 쓰기·락 코드가 없다 | unit, pytest + 소스 grep | 구현 전 RED |
| S-9 | AC-1 | 어댑터 stub이 launch 실패 5경로를 각각 유발한다 | 각 경로로 launcher 실행 함수를 호출한다. 별도로 이관취소 자체가 실패하는 경우도 1건 넣는다 | 5경로 전건에서 이관취소가 호출되고 registry가 허브 소유로 복귀한다. lease 소유자가 이관 전 허브 세션으로 되돌아온다. 이관취소 실패 케이스에서도 registry 복귀는 수행되고 실패 사실은 반환 로그 필드로만 남는다 | unit, pytest | 구현 전 RED |
| S-10 | H-5 | 이관 대기 상태이고 이관 만료 시각이 이미 지난 lease | 만료 이후 시각을 고정 now로 주고 판정·claim을 호출한다. 별도로 만료 전 레코드에 이관취소를 실행한다 | 만료 레코드는 무소유로 판정되어 허브가 claim할 수 있다. 이관취소는 이관을 수행한 세션 소유로 레코드를 되돌리고, 다른 세션의 이관취소는 거부된다 | unit, pytest, 고정 now | 구현 전 RED |
| S-11 | AC-10, C-6 | 이관 필드가 없는 기존 형식 lease와 worktree 키가 없는 태스크 | 기존 claim·판정·heartbeat·해제를 호출하고, 상태 전이 도구로 행 전이를 수행한다 | 반환 값과 레코드 필드가 변경 전과 동일하다. 상태 전이 응답의 키 집합·종료코드와 `state.json` 산출물이 변경 전과 동일하다 | unit, pytest — 변경 전 기준값과 비교 | 구현 후 |
| S-12 | AC-11, C-7 | 전 Work item 구현 완료 상태 | ownership-tool·worktree-tool·worktree-launcher·state-tool 테스트 전건과 `scripts/tests/test_hook_parity.py`를 실행한다 | 전건 통과하고 실패·오류 0건이다 | integration, pytest + bash | 구현 후 |
| S-13 | AC-8, AC-9, H-3 | harness 문서 갱신 완료 상태 | `grep -rln lease opal/core/references/harness/`를 실행하고, 갱신된 두 문서에서 획득·이관·해제·가드 적용 범위·저장 위치 5항목과 스텝 5·5.5의 이관 시점 기술을 확인한다 | grep 결과가 1건 이상이다. 5항목과 이관 시점·실패 복귀 기술이 모두 존재한다. 수기 누적 이력 절이 없다 | unit, bash grep + 문서 확인 | 구현 후 |
| S-14 | AC-12, C-8, H-2, H-4 | `scripts/install-mac.sh` 실행 완료. 소유자 승인 후. 기동한 허브 세션은 종료하지 않고 살아 있으며, 기동 직후 허브가 같은 태스크에 상태 전이를 1회 이상 수행한다 | 배포본의 ownership-tool 진입점으로 조회를 1회 실행하고, 새 `--wt` 태스크 1건을 기동해 워크트리 세션이 첫 쓰기와 상태 전이를 수행하게 한다 | 진입점이 미구현 오류가 아닌 정상 JSON을 반환한다. 기동 후 lease 소유자가 워크트리 세션이고 registry 실행 소유자 세션 id가 비어 있지 않으며, 허브의 전이·heartbeat가 진행된 뒤에도 소유자가 워크트리 세션으로 유지되고 워크트리 세션의 쓰기가 차단되지 않는다 | manual, 실제 설치본 + 실제 터미널 기동 | 설치 후 |
| S-15 | AC-6 | 태스크 149의 lease를 현재 허브 세션이 소유한 상태. 소유자 승인 후 | 허브 세션에서 해제를 실행하고 조회한 뒤, 다른 세션이 claim을 시도한다 | 해제가 성공하고 조회 결과가 무소유다. 다른 세션의 claim이 성공한다 | manual, 실제 태스크 149 | 배포 후 |
| S-16 | C-1 | 이관 경로에서 예외를 유발하는 조건(권한 없는 lease 경로, 손상된 JSON 레코드) | 그 조건으로 SessionStart·SessionEnd·PostToolUse·PreToolUse·Stop 훅 진입점을 각각 실행한다 | 전 훅이 종료코드 0으로 끝나고 차단 출력을 내지 않는다. 예외가 밖으로 전파되지 않는다 | unit, pytest | 구현 후 |
| S-17 | AC-5, AC-1 | 전 Work item 구현 완료 상태 | ownership-tool 진입점 스크립트 소스와 README에서 미구현 반환 문자열 및 CLI 미구현 서술을 grep하고, 테스트를 제외한 전 소스에서 lease claim 호출부를 전수 grep한다 | 진입점 소스의 미구현 반환 문자열이 0건이고 README에 CLI 미구현 서술이 남아 있지 않다. claim 호출부가 정확히 2건이며 두 건 모두 claimant 루트 인자를 동반한다 | unit, bash grep | 구현 후 |
| S-18 | C-2, C-3, AC-6 | 이관을 소비해 워크트리 세션 A가 lease를 보유한 상태에서 같은 worktree 루트로 다른 세션 id B가 SessionStart를 발화한다. (a) A가 정상 종료된 경우 (b) A가 종료 신호 없이 사라진 경우 | (a)는 A 세션 id로 SessionEnd 처리 함수를 먼저 호출한 뒤 B의 SessionStart 처리 함수를 호출한다. (b)는 SessionEnd 없이 B의 SessionStart 처리 함수를 호출하고, 이어서 A 세션 id로 해제를 실행한 뒤 B가 재시도한다 | (a)는 SessionEnd 처리가 A의 lease를 해제해 B의 claim이 성공한다. (b)는 A의 lease가 살아 있어 B의 claim이 거부되고 진단이 남으며, 해제 실행 후 B의 claim이 성공한다 | unit, pytest | 구현 후 |
