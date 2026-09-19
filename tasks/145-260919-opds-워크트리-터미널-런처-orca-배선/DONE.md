# DONE: 워크트리 전용 터미널 런처 orca 경로 배선

## 결과

`--wt` 태스크가 워크트리와 canonical task path만 만들고 끝나던 구간이, **전용 터미널을 열어 LLM을 기동하고 그 세션이 첫 턴을 스스로 시작해 태스크를 이어받은 뒤, 회수 시 터미널까지 정리하는** 흐름으로 이어졌다.

동작하지 않던 원인은 두 겹이었다. (1) `worktree-launcher` 호출부가 소스 전체에 0건이라 기동 코드가 실행된 적이 없었고, (2) orca 어댑터가 `orca terminal create --json`의 실제 응답 봉투(`result.terminal`)가 아니라 구현이 가정한 모양(`terminal`)을 읽어, **터미널은 실제로 떠 있는데 receipt가 비어 실패로 기록되고 상태가 원자 복귀**했다. 두 번째 결함이 통과한 이유는 단위 테스트가 subprocess를 목킹하고 그 가정 스키마를 스스로 넣어 파싱했기 때문이다 — 실물 CLI 응답과 대조한 적이 없었다.

**바뀐 것**

- 하네스에 **스텝 5.5**가 신설돼 `state init` 완료 후 launcher를 호출한다. 4.5는 포인터 1줄만 갖고 명령 블록은 5.5가 단독 소유한다.
- `worktree-launcher`가 실행 가능한 CLI(`launch`/`read`/`close`)를 갖는다. `run.sh`는 더 이상 `not_implemented`를 반환하지 않는다.
- orca 어댑터가 실물 봉투를 파싱하고 `worktreeId`(`<repoId>::<path>`)에서 cwd를 얻는다. prompt receipt 원천이 `launch_argv`로 확정되고 구형 `sessionstart_claim_observation`은 폐기됐다.
- 어댑터 seam이 3동사(`launch`/`read`/`close`)로 확장되고 보고 dict 스키마가 기계 검증 가능해졌다. 새 어댑터 추가 비용은 적합성 스위트에 이름 1줄과 fixture 등록이다.
- 원자 복귀 5경로 전건이 생성된 터미널을 닫는다. `worktree-tool remove`는 3중 가드 통과 뒤 `git worktree remove` 직전에 터미널을 스윕한다.
- 기동할 에이전트와 인자를 `launcher` 설정 블록으로 고를 수 있다. 미설정이면 코드 기본값으로 동작한다.
- 허브가 `worktree-tool status`의 `completed_unmerged`로 워크트리 세션의 종료를 감지한다.

**유지된 것**

- `--wt` 미사용 경로는 조건부 분기 0건으로 현행 동작 그대로다. 신설 분기는 전부 `execution_ownership.adapter` 기록 유무로만 열린다.
- `worktree-tool`이 worktree·registry·canonical task path의 단일 소유자로 남는다. orca `worktree create`로 대체하지 않는다.
- 상태 쓰기는 전부 `ownership-set` 경유이며 launcher에 사설 registry writer가 없다.
- 상속 계층을 만들지 않고 덕타이핑 seam을 유지했다.
- `main` merge·push·worktree 제거의 사용자 승인 경계는 불변이다. 워크트리 세션은 `completed_unmerged`까지만 진행한다.
- cmux·generic 어댑터는 범위 밖이며, 어댑터가 구성되지 않은 환경에서는 워크트리만 생기고 허브 세션이 그대로 작업한다.

## 변경 파일

- `opal/core/references/harness/task-process.md`
- `opal/core/references/harness/worktree.md`
- `opal/core/setting.default.json`
- `opal/tools/ownership-tool/tests/fixtures/README.md`
- `opal/tools/ownership-tool/tests/fixtures/launcher/orca-json-response.json`
- `opal/tools/ownership-tool/tests/fixtures/launcher/orca-terminal-read-response.json`
- `opal/tools/ownership-tool/tests/fixtures/launcher/orca-terminal-close-response.json`
- `opal/tools/worktree-launcher/README.md`
- `opal/tools/worktree-launcher/run.sh`
- `opal/tools/worktree-launcher/worktree_launcher/cli.py`
- `opal/tools/worktree-launcher/worktree_launcher/settings.py`
- `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py`
- `opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py`
- `opal/tools/worktree-launcher/tests/test_cli.py`
- `opal/tools/worktree-launcher/tests/test_settings.py`
- `opal/tools/worktree-launcher/tests/test_adapter_conformance.py`
- `opal/tools/worktree-launcher/tests/test_adapter_orca.py`
- `opal/tools/worktree-launcher/tests/test_launcher_core.py`
- `opal/tools/worktree-tool/worktree_tool.py`
- `opal/tools/worktree-tool/tests/test_worktree_tool.py`
- `tasks/145-260919-opds-워크트리-터미널-런처-orca-배선/` (TASK·PLAN·TEST-SCENARIO·TEST·AGENTIC-LOG·evidence·DONE)

## 검증

**결정론 (독립 검증자 재실행 수치)**

- `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-launcher/tests -q` → **110 passed, 1 skipped**(skip 1건은 `OPAL_LIVE_ORCA=1` opt-in live)
- `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests -q` → **146 passed**(기존 145 대비 실패 0)
- `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests -q` → **535 passed, 3 skipped, 339 subtests**
- `grep -rn "PROMPT_SOURCE_SESSIONSTART_CLAIM|sessionstart_claim_observation" worktree_launcher/` → **0건**

**실물 (배포본 경유, `evidence/S-11-live.md`가 원문 소유)**

- `run.sh launch --adapter orca --task 996` → `ok:true`, `status: worktree_session_owned`, `generation: 2`, `launch_receipt`·`prompt_receipt` 둘 다 registry에 객체 기록. `reported_cwd`가 워크트리 루트와 일치.
- 워크트리 터미널 상태줄 `task_996 │ feat/OP-TASK-996* │ 🎯 996` — 세션이 자기 태스크를 인지하고 **사람 입력 0회로 첫 턴 시작·완료**(`Brewed for 1m 10s`), PostToolUse hook 3/3 발화.
- 실패 주입(PATH에서 orca 제거) → `hub_owned` 복귀·`generation` 증가·receipt 소거·터미널 0개.
- dirty 워크트리 회수 → `GUARD_DIRTY` 거부, 그 시점 터미널 1개 유지(스윕 미도달).
- 클린 워크트리 회수 → `terminals_closed.exit_code: 0`, 잔존 터미널 0개.
- 목업 3건(994·995·996) 워크트리·브랜치·메타·터미널 전부 회수.

**게이트**

- 시나리오 15/15 PASS, RED 9/9 confirmed, `locked: true`
- PLAN 목표-커버 게이트: `coverage-check all_covered: true` + evaluator `scenario-rubric` verdict pass(목표 2 / 채택 2 / 경계 2, 평균 2.0)
- TEST 독립 검증: 생성자(PM) ≠ 평가자(`opal-test-agent`), All Pass 판정

## 회고적 학습 후보

.opal/brain/pages/concept/mock-only-adapter-verification-passes-schema-drift.md
.opal/brain/pages/concept/worktree-session-launch-order-and-ownership.md

## 참고

**증거 품질 결함 1건 (독립 검증자 지적, 수용)**

S-3의 RED 증거는 실제 관측이 아니라 사후 추론이었다. 적합성 스위트(W-7)는 P3에서 디스패치돼 W-4 GREEN(P2) 이후에 작성됐으므로 구조적으로 구현 전 실패를 볼 수 없었다. `scenario-red` 정정은 `scenario_already_locked`로 거부됐고(lock 이후 불변이 정상 동작), 정정은 `TEST.md`와 `AGENTIC-LOG.md`가 소유한다. 나머지 8건의 RED 증거는 각 워커 보고 수치와 대조돼 실측 인용으로 확인됐다.

**절차 이탈 1건 (자기 신고)**

RED 원장 기록 시점이 GREEN 이후였다. 재발 방지는 `scenario-init → scenario-red → scenario-lock`을 EXECUTE 첫 워커 디스패치 **전에** 끝내는 것이다 — 스위트를 나중에 신설하면 그 스위트는 RED를 관측할 수 없다.

**후속 태스크 후보 3건 (이번 AC 범위 밖, 실측으로 발견)**

1. `execution_ownership.owner_session_id`가 `None`으로 남는다. 허브가 launch 시점에 새 세션 id를 알 수 없기 때문이다. registry 전이는 receipt 2종만 요구해 성공하지만, `worktree-tool checkpoint`는 `owner_session_id == OPAL_SESSION_ID`를 요구하므로 **워크트리 세션이 자율 체크포인트 커밋 자격을 얻지 못한다.** 워크트리 세션이 자기 id로 소유권을 확정하는 경로가 필요하다.
2. `orca terminal close --worktree <selector> --all`의 응답 `closed`가 실제로 닫으면서도 항상 비어 있다(raw CLI로도 재현). `terminals_closed.closed`를 닫힌 개수의 증거로 쓰면 안 되며 판정은 `terminal list` 재조회로 해야 한다.
3. 실행 중인 에이전트 TUI를 스윕하면 orca가 비-0을 반환한다. 실제로는 닫히고 회수도 성공하지만(비차단 설계가 의도대로 작동) 경고가 false negative다. `sleep` 프로세스에서는 exit 0이었다.

**범위 밖으로 둔 것**

cmux·generic 어댑터 구현, W-7 C-1 정적 검사의 커밋 후 강도(현재 `git status` 기반이라 커밋 후 자동 통과), `argv_template`이라는 이름과 셸 문자열 값의 불일치.
