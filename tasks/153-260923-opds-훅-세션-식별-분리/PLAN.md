---
template: sdlc-v2
---
# PLAN: 훅 세션 식별 분리

> 입력: [TASK.md](TASK.md), [REPRO-EVIDENCE.md](REPRO-EVIDENCE.md) (ANALYSIS 없음 — opds Short profile, actor=pm)

## Approach

결함은 훅 소비자 전원이 일반 CLI용 식별 함수 `ownership_core.resolve_session_id(env, payload)`
(`opal/tools/ownership-tool/ownership_tool/ownership_core.py:351-369`)를 그대로 호출하는 데서 나온다.
이 함수는 ① `OPAL_SESSION_ID` ② 플랫폼 env(`claude_adapter.session_id_from_env`, `claude_adapter.py:18-25`)
③ 봉투 `session_id` 순이므로, 부모 세션의 env를 상속한 자식 Claude CLI의 훅 이벤트가 **부모 신원**으로
판정된다. 호출 지점은 6곳이다.

| 훅 소비자 | 호출 지점 | 부모 신원으로 판정될 때의 효과 |
|---|---|---|
| SessionEnd | `session_end_hook.py:59` | 부모 lease `released`, 부모 registry `closed` (REPRO 재현) |
| SessionStart | `session_start_hook.py:213` | 부모 registry 레코드 덮어쓰기, 부모 id로 env 파일 기록·claim 시도 |
| PostToolUse heartbeat | `heartbeat_hook.py:102` | 자식 활동이 부모 lease·registry 만료를 연장 |
| PreToolUse guard | `pretooluse_guard_hook.py:143-144` | 자식이 부모 소유 태스크를 자기 소유로 판정해 쓰기 차단 우회 |
| Stop evaluator | `stop_evaluator.py:127`(`state_path_for_payload`), `:210`(`evaluate`) | 자식 Stop이 부모 태스크를 강제 후보로 판정·부모 id로 receipt 기록 |

접근은 **분리**다. 훅 전용 식별 함수 `ownership_core.hook_session_id(payload)`를 신설해 봉투
`session_id`만 읽고, 위 6곳을 전부 이 함수로 교체한다. 일반 CLI 경로(`cli.py:189`의
`resolve_session_id(os.environ, {})`)와 state-tool의 자체 env 식별(`opal/tools/state-tool/state_tool.py:646-647`)은
변경하지 않는다. 공용 함수의 우선순위는 바꾸지 않는다(C-1).

code-scan 근거(`~/.opal/tools/code-scan/run.sh depends`·`exports`, headerSource=inline):

| 모듈 | layer | depends | 비고 |
|---|---|---|---|
| `ownership_tool.session_end_hook` | util | ownership_core, lease, heartbeat_hook | depended by 없음 |
| `ownership_tool.heartbeat_hook` | util | ownership_core, lease, session_registry | depended by `session_end_hook.py` (`owned_task_paths` 재사용) |
| `ownership_core.py` exports | util | — | `resolve_session_id` 포함 — 이번에 `hook_session_id` 추가 |

범위 밖: task 152 코드, lease 저장 잠금 동시성, installer 기능, Stop 워크트리 분기(`resolve_worktree`는
세션 id를 쓰지 않음), `~/.opal` 배포.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 훅 신원 함수 `ownership_core.hook_session_id(payload)` 신설 | 입력이 dict이고 `payload["session_id"]`가 공백 아닌 `str`이면 strip 값을, 그 외(키 누락·`None`·공백·비문자·payload 비dict)는 `None`을 반환한다. env를 인자로 받지 않는다 | TASK C-1·C-2. env를 시그니처에서 제거해 부모 신원 대체 경로를 구조적으로 없앤다 |
| D-2. `resolve_session_id(env, payload)`는 **무변경** | 시그니처·우선순위(① `OPAL_SESSION_ID` ② 플랫폼 env ③ payload) 그대로. 호출자는 일반 CLI(`cli.py:189`)만 남는다 | C-1 "공용 함수의 전역 우선순위 교체로 일반 CLI 계약을 바꾸지 않는다" |
| D-3. 훅 소비자 6곳은 `hook_session_id(payload)`만 사용 | `session_start_hook`·`session_end_hook`·`heartbeat_hook`·`pretooluse_guard_hook`·`stop_evaluator`(2곳)에서 `resolve_session_id` 호출 0건. 훅 모듈 소스에 `OPAL_SESSION_ID`·`CLAUDE_CODE_SESSION_ID` 문자열 0건(단, `session_start_hook`의 env 파일 **기록** 키 `SESSION_ID_ENV_LINE_KEY`는 출력 계약이므로 유지) | AC-5 "훅 소비자에서 환경변수 우선 신원 판별 잔존이 없고" |
| D-4. 신원 없는 훅 이벤트 = 진단 + 무변경 | SessionStart·SessionEnd·heartbeat: 기존대로 `no_session_id` 진단 후 즉시 반환(파일 I/O 0). PreToolUse: `session_id=None`, `diagnostics`에 `no_session_id`, 차단 없음(기존 fail-open 유지). Stop: `diagnostics`에 `no_session_id` 추가, receipt는 기존 가드(`stop_evaluator.py:368` `if project_root is not None and session_id`)로 미기록, 판정 흐름은 무변경 | C-2, AC-4. Stop 판정 흐름을 조기 종료로 바꾸면 세션 id를 쓰지 않는 워크트리 분기 동작까지 바뀌므로 범위 밖 |
| D-5. `decisions.DIAGNOSTICS`에 `no_session_id` 추가(11→12종) | Stop evaluator 결과가 `decisions.validate()`를 계속 통과한다. PreToolUse도 같은 폐쇄 enum 어휘를 쓴다 | `pretooluse_guard_hook` 헤더 "진단 어휘는 decisions.DIAGNOSTICS 폐쇄 enum을 재사용하며 새 값을 만들지 않는다" — 새 진단이 필요하면 enum에 등록하는 것이 유일한 합법 경로. `no_session_id`는 이미 start/end/heartbeat가 쓰는 기존 어휘다 |
| D-6. PreToolUse `handle(..., session_id=None)` 명시 인자 유지 | 인자 우선, 없으면 `hook_session_id(payload)` | 기존 테스트의 직접 주입 경로 보존(무변경 호환) |
| D-7. 실 CLI 검증은 임시 배포본 2벌 + 임시 프로젝트 + 명시 훅 설정 | before=`git show HEAD:` 기준 ownership-tool 사본, after=작업본 사본. 임시 프로젝트 `.claude/settings.json`에 사본 훅만 배선하고 `claude --setting-sources project`로 사용자 전역 훅을 배제한다. 자식 env는 가짜 부모 id(`OPAL_SESSION_ID`·`CLAUDE_CODE_SESSION_ID` 둘 다)와 `OPAL_PROJECT_ROOT=<임시 루트>`로 고정한다 | C-3·C-4. 실제 부모 세션 lease·레지스트리를 절대 건드리지 않기 위해 전역 훅 배제와 루트 오버라이드를 이중으로 건다 |

[MUST] `opal/core/references/harness/worktree.md` §해제: "세션 종료 훅은 그 세션이 소유한 lease만 해제한다. 종료 신호 없이 사라진 세션의 lease는 만료가 회수한다."
[MUST] `opal/core/references/harness/worktree.md` §획득: "어느 경로도 다른 세션의 live lease에서 소유권을 빼앗지 않는다. 같은 세션의 재획득만 멱등하게 허용한다."
[MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 테스트 작성 | opal-test-agent (red mode — red-first §1.5 작성자≠구현자) | `opal/tools/ownership-tool/tests/test_hook_session_identity.py`(신규) | 훅 5종을 subprocess로 실행(env에 가짜 부모 id 주입, 봉투에 자식 id/누락/공백/비문자)해 AC-2·AC-3·AC-4 판정, `hook_session_id` 단위 표, 훅 모듈 AST/문자열 정적 검사(AC-5), CLI `status`가 env 신원을 유지하는지·타 세션 live lease claim 거부 회귀. 수정 전 실행해 실패를 기록 | 없음 | P1 | AC-2, AC-3, AC-4, AC-5, C-1, C-2 |
| W-2. 진단 enum 확장 | PM | `opal/tools/ownership-tool/ownership_tool/decisions.py`, `opal/tools/ownership-tool/tests/test_decisions.py` | `DIAGNOSTICS`에 `no_session_id` 추가, @header 개수(12종) 갱신, 기대 집합 갱신 | 없음 | P1 | AC-4 |
| W-3. 훅 신원 함수 신설 | PM | `opal/tools/ownership-tool/ownership_tool/ownership_core.py` | `hook_session_id(payload)` 추가(D-1), `__all__`·@header exports·description에 반영. `resolve_session_id` 무변경 | 없음 | P1 | AC-5, C-1, C-2 |
| W-6. 실 CLI 재현 스크립트·증거 | opal-test-agent (before=red mode, after=TEST 단계) | `tasks/153-260923-opds-훅-세션-식별-분리/run/real-cli/verify_real_cli.py`(신규, 태스크 산출물) | D-7 구성으로 before/after 각각 `claude mcp get context7`·`claude mcp list`를 실행해 종료코드·훅 봉투 캡처·lease/registry 상태를 JSON 증거로 저장. 실행 전후 실제 태스크 153 `owner.json` 해시 불변 확인 | 없음 | P1 | AC-1, AC-6, C-3, C-4 |
| W-4. 훅 소비자 교체 | PM | `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`, `opal/tools/ownership-tool/ownership_tool/session_end_hook.py`, `opal/tools/ownership-tool/ownership_tool/heartbeat_hook.py`, `opal/tools/ownership-tool/ownership_tool/pretooluse_guard_hook.py`, `opal/tools/ownership-tool/ownership_tool/stop_evaluator.py` | 6개 호출 지점을 `ownership_core.hook_session_id(payload)`로 교체(D-3), PreToolUse·Stop에 `no_session_id` 진단(D-4), 각 @header description의 "세션 ID 해석은 resolve_session_id(D-18)에 위임" 문구를 현재 사실로 교체 | W-2, W-3 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5 |
| W-5. 계약 문서 갱신 | PM | `opal/tools/ownership-tool/README.md`, `opal/core/references/harness/worktree.md` | README §세션 ID 해석: 훅=봉투 전용·CLI=env 체인 분리, DIAGNOSTICS 표에 `no_session_id`. worktree.md §해제에 "훅 이벤트의 세션은 봉투 session_id로만 식별하며 환경변수로 대체하지 않는다" 1문장 | W-4 | P3 | AC-5, C-1 |
| W-7. run-log 기록 코어 진단 사본 동기화 | PM | `opal/tools/run-log-tool/run_log_core.py`, `opal/tools/run-log-tool/tests/test_run_log_tool.py` | T147 D-4 기계 대조 계약에 따라 `_STOP_DIAGNOSTICS` 사본에 `no_session_id` 추가, @header의 "diagnostics 11종"을 12종으로, 대조 테스트의 개수 단언 11→12 | W-2 | P3 | AC-4, AC-6 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. `claude --setting-sources project` 하에서도 `mcp get context7`이 사용자 스코프 MCP를 찾아 exit 0으로 성공하고, 사용자 전역 훅은 발화하지 않는다 | AC-1 실 CLI 증거의 성립 조건 | 전역 훅이 발화하면 after 결과가 오염되고, MCP를 못 찾으면 "성공 종료" 조건이 깨진다 | W-6이 before 실행에서 봉투 캡처 래퍼로 훅 발화 주체를 기록하고 exit 0을 확인한다. before가 REPRO와 같이 released/closed를 재현해야 after 판정을 유효로 본다 |
| H-2. 자식 CLI의 훅 봉투에 자식 고유 `session_id`가 실린다 | D-1이 자식 이벤트를 자식 신원으로 판정한다는 전제 | 봉투에 부모 id가 실리면 분리가 무력화된다 | W-6이 봉투 원문의 `session_id`를 캡처해 가짜 부모 id와 다름을 증거로 남긴다. 누락이면 D-4에 따라 무변경이므로 AC-1은 여전히 성립한다 |

## Release and recovery

- 적용 순서: P1(W-1·W-6 before RED 기록 → scenario-lock → W-2·W-3) → P2(W-4, RED→GREEN) → P3(W-5). W-6 after 실행은 TEST 단계 opal-test-agent가 수행한다. 검증 통과 후 worktree 브랜치 `feat/OP-TASK-153`에만 체크포인트 커밋한다.
- 검증 범위: 결정론 — ownership-tool 전체 pytest, state-tool `test_state_tool_ownership.py`, worktree-tool `-k "ownership or session"`. 실제 연동 — W-6 실 `claude` CLI(임시 프로젝트·임시 배포본). 독립 검증 — `op-scenario-gate`, TEST 단계 `opal-test-agent`.
- 배포: `~/.opal` install·실사용 배포·merge·push는 승인 범위 밖이므로 수행하지 않는다. 검증 종료 지점은 소스 테스트와 임시 배포본 실 CLI 증거다.
- 실패 시: worktree 브랜치에서 보정 커밋으로 되돌린다. 실사용 HOME·허브·task 152는 건드리지 않으므로 복구 대상이 아니다.
