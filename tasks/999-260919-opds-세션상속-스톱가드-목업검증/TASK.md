---
template: sdlc-v2
---
# TASK: 세션 상속과 Stop 가드 목업 검증

## Problem
진행 보고 뒤 실행이 종료된 사례에서 상태 전이는 `continue`였지만, state-tool이 읽는 `OPAL_SESSION_ID`가 Bash subprocess에 전달되지 않아 run-log의 `actor.session_id`와 태스크 lease가 비어 있었다. 이 상태에서는 Stop evaluator가 활성 태스크를 강제 후보로 분류하지 못하므로 최초 차단이 발화하지 않는다. 기존 실측 fixture도 서브에이전트 Bash에서 `OPAL_SESSION_ID`와 `CLAUDE_ENV_FILE`이 unset이었음을 기록한다 (`opal/tools/ownership-tool/tests/fixtures/hook-payloads/ENV-CAPTURE.md:1-28`). 현행 소스에는 SessionStart env 파일 기록 경로가 추가돼 있으나 (`opal/tools/ownership-tool/ownership_tool/session_start_hook.py:88-149`), 실제 부모 세션에서 subprocess와 state-tool까지 상속되는지는 실사용 경로로 재검증되지 않았다.

## Proposed outcome
격리된 worktree의 실제 agentic 실행에서 세션 식별자가 부모 실행 경계부터 Bash subprocess, state-tool run-log, state-transition lease, Stop evaluator까지 동일하게 이어지는지 먼저 입증한다. 실패하면 전달 경계만 최소 수정하고 같은 프로브를 다시 실행해 `block_continue` 전환을 확인한다. 이 게이트를 통과한 뒤에만 재개 claim, state view, block cap의 잔여 갭을 실측해 후속 범위를 확정하며, transcript 판정은 마지막 단계에 두고 PM 활동 로그는 집행이 아닌 관측 용도로 한정한다.

## Affected users and systems
영향 사용자는 agentic·semi-agentic Pilot을 사용하는 캡틴과 PM/전문 워커다. 영향 시스템은 Claude SessionStart 어댑터, worktree launcher, Bash subprocess 환경, state-tool의 run-log·lease claim, ownership-tool Stop evaluator 및 관련 통합 테스트다. 추가 범위로 worktree-tool registry(`execution_ownership` 블록)와 `checkpoint` 소유권 검사, worktree-launcher의 receipt·ownership-set 경로, Orca 어댑터로 기동된 워크트리 전용 터미널 세션의 부트 경계가 포함된다. 허브 기본 브랜치 merge·push·배포와 `unowned + continue` 자동 강제 승격 정책은 이번 태스크 범위에서 제외한다.

## Constraints
- C-1: `~/.opal/` 배포본을 직접 수정하지 않고 worktree의 프로젝트 소스만 변경한다 (`.opal/AGENT.md` §프로젝트별 추가 지침).
- C-2: 첫 구현 범위는 세션 식별자 전달 경계와 subprocess 상속 검증으로 제한하며, 동일 프로브의 `block_continue` 성공 전에는 claim 확대·state view·block cap·transcript 정책을 변경하지 않는다.
- C-3: SessionStart hook 자식 프로세스 안의 단순 `export`를 해결로 인정하지 않고, 이후 Bash/state-tool이 상속하는 부모 실행 경계 또는 플랫폼 env-file 계약을 검증한다.
- C-4: 실측은 공개 CLI와 실제 hook 봉투를 사용하며 evaluator에 `show_json`이나 lease를 테스트 내부에서 직접 주입한 결과만으로 통과시키지 않는다.
- C-5: 기존 태스크나 다른 worktree의 lease·registry·run-log를 수정하지 않으며 태스크 999 전용 자산만 사용한다.
- C-6: PM 활동 사건은 관측 전용으로 유지하고 Stop 집행 판정의 신규 입력으로 사용하지 않는다.
- C-7: 플랫폼 고유 세션 변수 처리는 어댑터 경계에 격리하고 state-tool은 `OPAL_SESSION_ID`만 소비하는 현행 중립 계약을 보존한다 (`opal/tools/state-tool/state_tool.py:643-644`).
- C-8: worktree 실사용 검증은 이번에 실제로 기동된 태스크 999 워크트리와 Orca 터미널 세션만 대상으로 하며, 허브나 다른 슬롯의 registry·터미널을 조작하지 않는다.
- C-9: registry `execution_ownership`의 쓰기는 `worktree-tool ownership-set` 경유만 사용한다. registry meta 파일을 직접 편집하지 않는다.
- C-10: `checkpoint` 실증은 태스크 999 소유 worktree 브랜치에 한정하고, `main` 브랜치 commit·merge·push는 이번 범위에서 수행하지 않는다.

## Acceptance criteria
- AC-1: 수정 전 baseline 프로브가 부모 세션 ID, Bash subprocess의 `OPAL_SESSION_ID`, run-log `actor.session_id`, `owner.json`의 세션 ID, evaluator 결과를 한 증거 묶음으로 기록한다.
- AC-2: baseline이 세션 상속 실패를 재현하면 최소 수정 후 subprocess 실호출 테스트에서 부모가 주입한 `OPAL_SESSION_ID`가 동일 값으로 상속되고, 미설정 경로는 기존 동작을 유지한다.
- AC-3: 새 세션에서 실제 state-tool `advance` 또는 `mark`를 수행한 뒤 run-log `actor.session_id`와 `owner.json.owner_session_id`가 동일한 비어 있지 않은 값이며 `claim_source=state_transition`이다.
- AC-4: 실제 Stop hook stdin 봉투를 사용한 동일 프로브의 evaluator 판정이 `classification=owned`, `forced_count=1`, `decision_kind=block_continue`로 확인된다.
- AC-5: AC-4 통과 후 세션 재시작 직후, 상태 전이 없는 재개, state view 부재, block cap 미설정의 네 경로를 실측하고 claim·state view·block cap 구현 범위를 증거와 함께 확정한다.
- AC-6: transcript 기반 진행 판정은 AC-5 이후에만 검토되며, PM 활동 로그를 추가할 경우 `progress`와 `decision`을 구분하는 관측 자료로만 기록된다.
- AC-7: hook main 경유 E2E, subprocess 상속, state-tool lease/run-log, Stop evaluator 회귀 테스트가 모두 통과하고 기존 ownership-tool·state-tool 관련 테스트에 회귀가 없다.
- AC-8: 단순 진행 보고 뒤 `transition_action=continue`인 목업 흐름이 추가 도구 호출과 다음 상태 전이까지 이어지며, 사용자 결정이 필요한 경계와 CLOSE 진입 게이트는 기존 계약을 유지한다.
- AC-9: 이번 `--wt` 실행의 launcher receipt가 증거로 확인된다 — registry `execution_ownership.launch_receipt`의 `adapter`·`adapter_handle`·`launched_at`·`reported_cwd`와 `prompt_receipt`의 `prompt_id`·`submitted_at`이 모두 존재하고, `reported_cwd`가 발급된 `worktree_root`와 일치한다.
- AC-10: 새 Orca 터미널 세션이 워크트리를 정확히 인식했음이 증거로 확인된다 — 세션의 cwd가 `worktree_root`와 일치하고, `.opal/task-ownership.json` 발급 사본의 `task_path`·`task_folder`가 registry 발급값과 같으며, 현재 git 브랜치가 registry `branch`(`feat/OP-TASK-999`)와 일치한다.
- AC-11: 초기 prompt 제출과 단계 진행이 실제로 이어졌음이 확인된다 — 세션이 `state.json`을 읽어 재개했고, TASK 확정부터 최소 1회의 `state-tool` 상태 전이가 같은 세션에서 수행된 기록이 run-log에 남는다.
- AC-12: registry `execution_ownership.owner_session_id`가 `null`인 반면 `run/.runtime/owner.json.owner_session_id`에는 현재 세션 ID가 있는 불일치의 원인과 영향이 판정된다. 최소한 (a) 어느 주체가 각 필드를 쓰는지, (b) 워크트리 세션 부트 이후 registry 쪽을 채우는 주체가 존재하는지, (c) 이 불일치가 `worktree-tool checkpoint`의 소유권 검사(`checkpoint_ownership_denied` / `reason=foreign_owner`)에 미치는 영향을 코드 근거와 함께 확정한다.
- AC-13: AC-12의 판정에 따라 체크포인트 권한이 실증된다 — 수정 후 태스크 999 소유 worktree 브랜치에서 `worktree-tool checkpoint`가 `checkpoint_ownership_denied` 없이 1회 성공하고, 성공 SHA가 registry `execution_ownership.checkpoint_shas[]`에 append된다. 수정 범위가 후속으로 분리된다면 그 근거와 후속 경계를 명시한다.
- AC-14: `execution_ownership.state`가 `worktree_session_owned`이고 `generation`이 역행하지 않으며, 위 검증 과정에서 `hub_owned` 복귀나 고아 터미널이 발생하지 않음이 확인된다.
