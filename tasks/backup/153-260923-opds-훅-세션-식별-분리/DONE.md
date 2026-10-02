# DONE: 훅 세션 식별 분리

## 결과

ownership-tool 훅이 이벤트의 세션을 봉투 `session_id`로만 식별한다. 부모 세션의 환경변수(`OPAL_SESSION_ID`·`CLAUDE_CODE_SESSION_ID`)를 상속한 자식 Claude CLI(`claude mcp get`·`claude mcp list` 등)가 끝나도 부모 태스크 lease와 세션 registry는 active로 남는다.

- 신설 `ownership_core.hook_session_id(payload)`: 봉투 `session_id`가 공백 아닌 문자열일 때만 그 값을, 그 외에는 None을 돌려준다. env를 받지 않는다.
- SessionStart·SessionEnd·PostToolUse heartbeat·PreToolUse guard·Stop evaluator(2곳) 6개 지점이 이 함수를 쓴다.
- 봉투 신원이 없거나 공백·비문자이면 `no_session_id` 진단만 남기고 소유권·세션·receipt 파일을 쓰지 않는다. PreToolUse는 차단 없이 통과(기존 fail-open 유지), Stop은 판정 흐름을 유지하되 receipt를 쓰지 않는다.
- `decisions.DIAGNOSTICS`에 `no_session_id`를 더했고(12종), run-log 기록 코어의 기계 대조 사본(`_STOP_DIAGNOSTICS`)을 함께 맞췄다.

유지한 것: 일반 CLI(`ownership-tool status/release`)의 `--session-id` > env 식별(`resolve_session_id` 무변경), state-tool의 env 기반 식별, 타 세션 live lease 획득 거부, Stop 워크트리 분기 동작. task 152 코드·lease 저장 동시성·installer는 건드리지 않았다. `~/.opal` 배포·merge·push는 하지 않았다.

## 변경 파일

- `opal/tools/ownership-tool/ownership_tool/ownership_core.py`
- `opal/tools/ownership-tool/ownership_tool/decisions.py`
- `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`
- `opal/tools/ownership-tool/ownership_tool/session_end_hook.py`
- `opal/tools/ownership-tool/ownership_tool/heartbeat_hook.py`
- `opal/tools/ownership-tool/ownership_tool/pretooluse_guard_hook.py`
- `opal/tools/ownership-tool/ownership_tool/stop_evaluator.py`
- `opal/tools/ownership-tool/tests/test_hook_session_identity.py` (신규)
- `opal/tools/ownership-tool/tests/test_decisions.py`
- `opal/tools/ownership-tool/README.md`
- `opal/core/references/harness/worktree.md`
- `opal/tools/run-log-tool/run_log_core.py`
- `opal/tools/run-log-tool/tests/test_run_log_tool.py`
- `tasks/153-260923-opds-훅-세션-식별-분리/run/real-cli/verify_real_cli.py` (신규, 실 CLI 재현 스크립트)

## 검증

- 실 CLI(`claude` 2.1.280, 임시 프로젝트·임시 배포본·`--setting-sources project`, 가짜 부모 id 상속): `mcp get context7`·`mcp list` 모두 exit 0. 구현 전(`ace8368`) 배포본은 부모 lease `released`·registry `closed`로 결함 재현, 작업본은 둘 다 `active` 유지. 훅 미배선 대조군은 `active` 유지(사용자 전역 훅 미발화 확인). 캡처한 SessionEnd 봉투의 `session_id`는 부모 id와 달랐고, 진행 세션의 실제 lease 필드는 모든 실행 전후 같았다 — `run/real-cli/evidence.json`
- `test-scenario.json`: S-1~S-9 9/9 pass, RED 대상 5건 구현 전 실패 확인 후 잠금
- `opal/tools/ownership-tool`: `pytest tests` 157 passed (신규 `test_hook_session_identity.py` 43건 포함)
- `opal/tools/state-tool`: `pytest tests/test_state_tool_ownership.py` 8 passed
- `opal/tools/worktree-tool`: `pytest tests -k "ownership or session"` 12 passed
- `opal/tools/run-log-tool`: `pytest tests/test_run_log_tool.py -k T147D4` 3 passed (진단 사본 대조)
- 목표-커버 게이트: coverage-check exit 0 + opal-evaluator-agent pass(2/2/2)
- 컨벤션 진단: Critical/High 0, Low 1(`stop_evaluator.state_path_for_payload`의 미사용 `env` 파라미터 — 호출 호환 위해 유지)
- `code-scan validate --changed`: ok, newly_uncovered 0 / `state-tool validate`: violations 0

## 회고적 학습 후보

.opal/brain/pages/entity/ownership-tool.md

## 참고

- run-log-tool `tests/test_run_log_tool.py`의 import 계열 4건(`test_import_agentic_idempotent`, `test_dry_run_makes_no_change`, `test_run_id_omitted_resolution_and_ambiguity`, `test_normal_agentic_log_still_imports`)은 구현 전 커밋 사본에서도 같게 실패하는 기존 결함이다. 이번 범위 밖이며 별도 태스크가 필요하다.
- 실사용 반영은 merge 후 install 재배포가 필요하다(이번 승인 범위 밖).
- S-2의 RED 증거는 fixture 보정 전 기록이 `test-scenario.json`에 잠겨 있고, 보정 후 재확인(구현 전 사본에서 `'active' == 'released'` 실패)은 AGENTIC-LOG #15와 워커 보고로 남겼다.
