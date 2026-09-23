---
template: sdlc-v2
---
# TEST-SCENARIO: 훅 세션 식별 분리

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 작업본 `opal/tools/ownership-tool/` 소스, `~/.opal/.venv/bin/python`(pytest), 실제 `claude` 바이너리 2.1.280(`/Users/iskang/.local/bin/claude`).
- 공통 데이터: pytest `tmp_path` 아래 임시 프로젝트 루트(`.opal/AGENT.md` 마커, `tasks/<A>`·`tasks/<B>` 태스크, `<cwd>/.opal/task-ownership.json` 발급 사본)와 가짜 세션 id `parent-*`·`child-*`. 부모 lease·registry는 설치본이 아닌 작업본 `lease.claim`·`session_registry.register`로 만든다.
- 부모 신원 상속 재현: 모든 훅 실행 env에 `OPAL_SESSION_ID`와 `CLAUDE_CODE_SESSION_ID`를 가짜 부모 id로 넣고 `OPAL_PROJECT_ROOT=<임시 루트>`로 고정한다. 실제 세션의 env 값은 자식 env에 전달하지 않는다.
- 대역 사용과 한계: S-2~S-6은 훅 스크립트를 실제 subprocess로 실행하되 봉투는 캡처 형식의 JSON을 직접 만든다 — 실제 CLI가 봉투에 무엇을 싣는지는 S-1이 실 CLI로 확인한다. mock/patch는 쓰지 않는다.
- 실 CLI 격리(S-1): before=`git show HEAD:`로 복원한 ownership-tool 임시 배포본, after=작업본 사본. 임시 프로젝트 `.claude/settings.json`에 해당 사본의 SessionStart·PostToolUse·SessionEnd·Stop·PreToolUse 훅만 봉투 캡처 래퍼 경유로 배선하고 `claude --setting-sources project`로 사용자 전역 훅을 배제한다. 실행 전후 실제 태스크 153 `run/.runtime/owner.json`의 `owner_session_id`·`status`·`generation`을 비교한다(`heartbeat_at`은 현 세션 PostToolUse가 계속 갱신하므로 비교 대상이 아니다). `--setting-sources project`는 사용자 스코프 MCP를 읽지 않으므로 임시 프로젝트 `.mcp.json`에 context7을 프로젝트 스코프로 등록하고 `.claude/settings.json`에 `enableAllProjectMcpServers: true`를 둔다(탐침: 두 명령 exit 0 확인). 대조군으로 훅을 배선하지 않은 임시 프로젝트에서 같은 명령을 실행해 사용자 전역 훅이 발화하지 않음을 먼저 확인한다.
- 실행 조건: 자동 실행. 사람 협업 없음.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-6, C-3, C-4, H-1, H-2 | 임시 프로젝트에 가짜 부모 id의 active lease·active registry. 자식 env에 가짜 부모 id 상속, 훅은 before/after 임시 배포본 | `claude --setting-sources project mcp get context7`, `claude --setting-sources project mcp list`를 before·after 배포본으로 각각 실행 | 4회 모두 exit 0. before: 부모 lease `released`·registry `closed`(결함 재현). after: 부모 lease `active`·registry `active`. 캡처 봉투의 `session_id`가 부모 id와 다름(또는 누락). 대조군(훅 미배선)은 부모 lease·registry `active` 유지. 실제 태스크 153 `owner.json`의 `owner_session_id`·`status`·`generation` 전후 동일. 결과를 `run/real-cli/evidence.json`에 저장 | integration — 실제 claude CLI, 임시 프로젝트·임시 배포본 | 구현 전 RED(before), 구현 후(after) |
| S-2 | AC-2, C-1 | 부모가 태스크 A lease·registry 소유, 자식이 태스크 B lease·registry 소유. env에 부모 id | SessionEnd 훅 subprocess에 봉투 `session_id=child` 전달 | 태스크 B lease `released`, 자식 registry `closed`. 태스크 A `owner.json`과 부모 registry 파일 바이트가 실행 전과 동일 | integration — hook subprocess(pytest) | 구현 전 RED, 구현 후 |
| S-3 | AC-3 | 부모가 태스크 A lease·registry 소유. env에 부모 id | SessionEnd 훅 subprocess에 봉투 `session_id=parent` 전달 | 태스크 A lease `released`, 부모 registry `closed` | integration — hook subprocess(pytest) | 구현 후 |
| S-4 | AC-4, C-2 | 부모가 태스크 A lease·registry 소유. env에 부모 id | SessionStart·SessionEnd·PostToolUse heartbeat·PreToolUse·Stop 훅 각각에 봉투 `session_id` 누락·`"  "`·`123`·`null` 4종 전달(`handle`/`evaluate` 직접 호출 + SessionEnd는 subprocess 병행) | 모든 경우 결과 `diagnostics`에 `no_session_id`, 결과 `session_id`는 `None`. `.opal/run/.runtime` 이하와 태스크 lease 파일의 목록·바이트가 실행 전과 동일(receipt·registry·env 파일 신규 생성 0). Stop 결과는 `decisions.validate()` 통과 | unit + integration(pytest) | 구현 전 RED, 구현 후 |
| S-5 | AC-2, C-1 | 부모가 태스크 A lease 소유(워크트리 발급 사본으로 canonical 해석 가능), env에 부모 id | 봉투 `session_id=child`로 heartbeat 훅, PreToolUse 훅(`tool_name=Edit`), Stop 평가를 실행 | heartbeat: 부모 `heartbeat_at`·registry 불변, `noop: true`. PreToolUse: `classification=foreign_session_owned`, `decision=block`. Stop: 결과 `evidence.session_id=child`, 부모 id 명의 receipt 파일 미생성 | integration — handle/evaluate(pytest) | 구현 전 RED, 구현 후 |
| S-6 | AC-5, C-1 | 작업본 훅 모듈 5종 소스와 `ownership_core` | AST로 훅 모듈의 `resolve_session_id` 호출·`OPAL_SESSION_ID`·`CLAUDE_CODE_SESSION_ID` 문자열 리터럴을 탐색(`session_start_hook`의 기록 키 `SESSION_ID_ENV_LINE_KEY` 제외), `hook_session_id`에 env를 줄 방법이 없는지 시그니처 확인 | 탐색 결과 0건. `hook_session_id`의 파라미터는 `payload` 하나. `resolve_session_id`는 env `OPAL_SESSION_ID`를 여전히 1순위로 반환 | unit — AST 정적 검사(pytest) | 구현 전 RED, 구현 후 |
| S-7 | AC-5, C-1 | env `OPAL_SESSION_ID=<소유자>`, 다른 세션 소유 live lease 태스크 | `ownership-tool status`·`release`를 `--session-id` 없이 실행, 타 세션 live lease에 `lease.claim` 시도, state-tool 소유권 스위트 실행 | CLI는 env 신원으로 판정(소유자 release 성공, 비소유자 `not_owner`+비0 종료), 타 세션 live lease claim은 거부되고 레코드 불변, `test_state_tool_ownership.py` 전건 통과 | integration — CLI subprocess + 기존 스위트(pytest) | 구현 후 |
| S-8 | AC-6 | 구현 완료 작업본 | ownership-tool `tests/` 전체, state-tool `tests/test_state_tool_ownership.py`, worktree-tool `tests -k "ownership or session"` 실행 | 전건 통과, 실패 0 | regression — pytest | 구현 후 |
| S-9 | C-5, AC-6 | actor=pm 진행 중인 태스크 153 | 목표-커버 게이트 판정과 TEST 단계 시나리오 실행·판정을 PM이 아닌 서브에이전트(`opal-evaluator-agent`, `opal-test-agent`)에 디스패치하고 `state-tool show`·`.scenario-gate-history.json`·`test-scenario.json`을 확인 | `plan.scenario_gate` 행은 evaluator `verdict: pass` 기록 뒤에만 ✅, `test.run_tests` 행은 test-agent 실행 결과(S-1~S-8 PASS)와 워커 소요 기록 뒤에만 ✅. PM 산문 판단만으로 두 행이 ✅가 된 기록 0건 | process — state-tool·test-tool 기록 확인 | 구현 후 |
