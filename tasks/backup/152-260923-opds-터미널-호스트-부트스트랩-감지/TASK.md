---
template: sdlc-v2
---
# TASK: 터미널 호스트 부트스트랩 감지와 worktree 기동 연계

## Problem
OPAL은 현재 프로세스가 cmux·Orca 같은 어느 터미널 앱에서 실행되는지 결정론적으로 판별하지 않는다. 또한 `--wt` 세션 기동은 호출자가 `--adapter`를 직접 지정해야 하고 Orca만 지원하므로, 설치된 앱과 실제 실행 호스트를 구분해 현재 터미널에 맞는 기동 경로를 선택할 수 없다 (`opal/tools/worktree-launcher/README.md:52-54`, `opal/tools/worktree-launcher/README.md:143-146`).

## Proposed outcome
OPAL bootstrap이 현재 프로세스의 실제 터미널 호스트와 중첩 multiplexer를 구조화된 결과로 감지하고 소비한다. 이후 `--wt` 태스크 기동은 bootstrap에서 확인한 호스트를 읽어 지원되는 worktree launcher adapter를 명시적으로 선택하며, 앱 설치 여부나 실행 중인 다른 앱 때문에 잘못된 adapter를 선택하지 않는다.

## Affected users and systems
OPAL을 cmux·Orca·tmux 및 일반 터미널에서 실행하는 사용자와 `session.assistant`·`session.project` bootstrap, 플랫폼별 bootstrapper 배포물, `worktree-launcher`, `--wt` 세션 기동 계약이 대상이다. `session.disabled`와 `[WORKER]`의 기존 스킵 의미, worktree 생성·lease·merge 계약은 변경하지 않는다 (`opal/core/AGENT.md:17-30`, `opal/core/references/harness/task-process.md:84-101`).

## Constraints
- C-1: 설치 여부나 전역 실행 프로세스가 아니라 현재 OPAL 프로세스의 환경과 프로세스 계보만 터미널 호스트의 직접 근거로 사용한다.
- C-2: 판별 결과는 `host`, `multiplexers`, `confidence`, `evidence`만 포함하고 비밀값·socket capability·세션 토큰·원시 환경변수 값은 노출하지 않는다.
- C-3: `bootstrap: off`와 `session.worker`는 기존처럼 전역 bootstrap 작업을 생략하고 terminal context 감지도 강제하지 않는다 (`opal/core/AGENT.md:19-20`, `opal/core/AGENT.md:30`).
- C-4: 플랫폼 차이는 판별 도구 또는 adapter 경계에 격리하고 bootstrap 문서와 launcher core에 플랫폼명 조건문을 확산하지 않는다.
- C-5: `--wt`의 worktree 생성, state 초기화, lease 이관, 실패 시 허브 복귀 순서를 보존한다 (`opal/core/references/harness/task-process.md:84-101`).
- C-6: `~/.opal/` 배포본을 직접 수정하지 않고 프로젝트 소스와 install 경로를 갱신한다.

## Acceptance criteria
- AC-1: Python 표준 라이브러리 기반 판별기와 얇은 `run.sh` 진입점이 cmux·Orca·일반 터미널의 `host` 및 tmux 중첩을 구조화 JSON으로 반환하고, fixture 기반 테스트에서 오탐 없이 통과한다.
- AC-2: 명시적 호스트 신호, 프로세스 조상, tmux client 조상, `TERM_PROGRAM`, `unknown`의 우선순위와 confidence/evidence가 테스트로 고정된다.
- AC-3: 모든 플랫폼 bootstrapper가 설정·marker 게이트 이후 허용된 session에서 판별기를 호출해 결과를 세션 컨텍스트로 소비하며, `session.disabled`·`session.worker`의 기존 무로드 계약이 회귀하지 않는다.
- AC-4: `--wt` 기동 경로가 소비한 terminal host를 지원 adapter 선택에 사용하고, cmux와 Orca 각각의 실제 CLI 경계를 adapter로 분리한다. 지원 불가·unknown 호스트는 다른 앱으로 추측 폴백하지 않고 비차단 실패로 허브 세션을 유지한다.
- AC-5: cmux와 Orca가 동시에 설치·실행되거나 동일 프로젝트가 양쪽에 등록돼 있어도, 현재 프로세스의 host만 adapter 선택 근거가 되는 회귀 테스트가 통과한다.
- AC-6: source 테스트, bootstrap 계약 감사, worktree-launcher 회귀 테스트, source→installed parity 검증이 모두 통과한다.
