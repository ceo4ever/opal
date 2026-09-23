---
template: sdlc-v2
---
# TEST-SCENARIO: 터미널 호스트 부트스트랩 감지와 worktree 기동 연계

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: macOS fixture 기반 Python/pytest, source bootstrap audit, 임시 HOME의 installer 결과. opt-in cmux live 검증은 cmux CLI가 있고 사용자가 명시했을 때만 실행한다.
- 공통 데이터: cmux·Orca·일반 터미널·tmux 중첩 조합의 env/process-tree fixture, cmux CLI 성공·실패 응답 fixture.
- 대역 사용과 한계: process 조상과 cmux subprocess는 단위 테스트에서 대역한다. 대역은 실제 cmux 버전 drift를 보장하지 않으므로 현재 CLI help 계약 대조와 opt-in live 검증을 별도로 둔다.
- 실행 조건: 자동 실행. live cmux 시나리오는 생성한 workspace handle만 teardown에서 회수한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-2, AC-5, C-1, C-2, H-1 | cmux/Orca/TERM_PROGRAM/unknown, tmux client 조상, 서로 충돌하는 신호 fixture | `terminal-context` 공개 CLI를 호출하고 우선순위별 결과를 읽는다 | 출력은 정확히 4키이고 비밀값이 없으며, cmux/Orca/일반/unknown과 tmux 중첩이 D-B 순서로 판정된다. 다른 앱의 설치·실행 상태는 결과를 바꾸지 않는다 | unit + CLI integration | 구현 전 RED |
| S-2 | AC-3, C-3, H-3 | bootstrap off, `[WORKER]`, assistant, project 입력과 4종 bootstrapper | bootstrap audit로 terminal-context 호출 위치·횟수·body parity를 검사한다 | off/worker는 호출 0회, assistant/project는 게이트 후 1회이고 결과를 세션 terminal context로 소비하는 지시가 4종에 동일하다 | 정적 계약 + 모의 bootstrap integration | 구현 전 RED |
| S-3 | AC-4, AC-5, C-4, C-5, H-2, H-4 | cmux 성공·비정상 stdout·비-0 응답, Orca 회귀, unknown host | adapter 적합성 suite와 CLI test로 launch/read/close 및 host 소비 규칙을 실행한다 | cmux host는 cmux만, Orca host는 Orca만 명시 주입된다. tmux는 선택을 바꾸지 않고 unknown/미지원은 폴백 0회로 허브에 남는다. cmux 파싱 실패는 구조화 실패 dict이다 | unit + adapter conformance + CLI integration | 구현 전 RED |
| S-4 | AC-4, H-2 | 현재 cmux CLI와 임시 worktree 경로, opt-in 실행 플래그 | cmux adapter로 workspace를 생성하고 화면을 읽은 뒤 같은 handle만 닫는다 | workspace cwd와 command 전달이 확인되고 read가 유계 출력을 반환하며 teardown 후 해당 workspace가 없다 | opt-in live integration | 구현 후 |
| S-5 | AC-6, C-6 | source 전체 테스트 통과 후 임시 HOME 또는 승인된 installer 경로 | installer를 실행하고 terminal-context·bootstrap·harness·launcher 주요 파일을 source와 대조한다 | 신설 run.sh가 실행 가능하고 주요 파일의 바이트 parity가 맞으며 설치본 CLI도 4키 JSON을 반환한다 | installer integration + parity audit | 설치 후 |
