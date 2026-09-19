---
template: sdlc-v2
---
# TEST-SCENARIO: 세션 상속과 Stop 가드 목업 검증

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md), [PROBE-BASELINE.md](PROBE-BASELINE.md) | 작성자: PM

## Setup

- 환경: macOS · 태스크 999 전용 git worktree(`/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999`, 브랜치 `feat/OP-TASK-999`) · 허브 `/Volumes/Data/AIStudio/workspace/ai-framework` · 배포본 `~/.opal` · 러너 `~/.opal/.venv/bin/python -m pytest`.
- 공통 데이터: 실제 SessionStart·Stop hook 봉투(`session_id`·`cwd`·`hook_event_name`·`transcript_path`·`stop_hook_active`). 허브 registry `.opal-worktrees/.meta/task_999.json`. 태스크 lease `run/.runtime/owner.json`. run-log `run/run-log-*.jsonl`. 수정 전 기준값은 `PROBE-BASELINE.md` §1 P-1~P-10과 §5.1~§5.4가 소유한다.
- 대역 사용과 한계: hook 진입점·CLI·registry·lease는 **실물만** 사용한다(C-4). 유일한 대체는 `CLAUDE_ENV_FILE`을 임시 파일로 지정하는 것이며, 이유는 플랫폼 소유 `~/.claude/session-env/`를 오염시키지 않기 위함이다. 한계 — 이 대체는 "hook이 쓰고 쉘이 source한다"는 부모 경계를 재현할 뿐, **진짜 새 Claude 세션의 종단 동작을 대신하지 않는다.** 실세션 종단 확인(S-3b·S-4b)은 PM Gate 증거 축에서 별도로 관측한다(PLAN §Release and recovery).
- 실행 조건: S-1·S-9~S-11·S-3b·S-4b는 PM Gate 증거 축(현재 세션 관측). 그 외는 워커 자동 실행. 모든 워커는 착수 직후 세션 식별자 3종(`CLAUDE_CODE_SESSION_ID`·`OPAL_SESSION_ID`·봉투 `session_id`)을 산출물 첫 표에 기록하고, registry `owner_session_id`와 불일치하면 추측 없이 blocked로 반환한다(H-5).

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1 | 수정 전 워크트리 agentic 세션 | 부모 세션 ID·Bash `OPAL_SESSION_ID`·`typeset -p`·자식 상속·run-log `actor.session_id`·`owner.json`·evaluator 입력을 한 묶음으로 기록 | `PROBE-BASELINE.md` §1에 P-1~P-10이 한 표로 존재하고, P-3 미export·P-4/P-5 미상속·P-6 `ownership_session_id_missing`·P-7 `null`·P-8 `session_start`가 모두 기록됨 | manual · 현재 세션 관측 | 구현 전 (완료) |
| S-2 | AC-2, C-3, H-1 | W-1 반영 + 재배포 후 | 실제 `session_start_hook.py`에 실제 봉투를 주입(`CLAUDE_ENV_FILE`=임시 파일)하고, 기록된 줄과 `source` 후 자식 상속을 확인 | 기록된 줄이 `export OPAL_SESSION_ID=`로 시작하고, `typeset -p`에 `-x`가 있으며, `sh -c 'echo $OPAL_SESSION_ID'`가 봉투 `session_id`와 **바이트 일치**한다. 불일치면 즉시 revert 대상 | integration · 워크트리 셸 | 구현 후·설치 후 |
| S-2r | AC-2, C-3 | W-1 착수 전 | `test_session_start.py`의 env 파일 단언을 `export ` 접두 + 값 일치로 좁힌다 | 수정 전 코드에서 해당 테스트가 **실패**한다(RED 증거) | unit · pytest | 구현 전 RED |
| S-2n | AC-2 | `CLAUDE_ENV_FILE` 미제공 / 쓰기 실패 / 허브 cwd 경로 | 세 경로를 각각 실행 | `env_file_not_provided`·`env_file_write_failed:` 진단과 `registered=True`·exit 0·허브 lease 0건이 수정 **전후 모두** 동일하다(불변 계약 — 수정 전에도 통과해야 정상) | unit · pytest | 구현 전 GREEN·구현 후 GREEN |
| S-3 | AC-3 | S-2의 `source`된 쉘 | 태스크 999에 `state-tool advance` 또는 `mark` 1회 실행 | stderr에 `ownership_session_id_missing`이 없고, run-log `actor.session_id`와 `owner.json.owner_session_id`가 **동일한 비어 있지 않은 값**이며 `claim_source=state_transition`이다 | integration · CLI 실물 | 구현 후·설치 후 |
| S-3i | AC-3 | S-3 직후 | `owner.json`의 `generation`·`claimed_at`·`owner_session_id`를 §1 P-8·P-9와 대조 | 세 필드가 불변이고 `claim_source`만 `session_start`→`state_transition`으로 승격됨(강등·재생성 없음) | integration · 파일 대조 | 구현 후 |
| S-3b | AC-3 | 재배포 후 **진짜 새** Orca 워크트리 세션 | 그 세션의 Bash에서 `typeset -p`와 `state-tool` 1회 전이를 관측 | S-2·S-3과 같은 결과가 실세션에서도 재현됨 | manual · 실세션 | 설치 후 (PM Gate 증거) |
| S-4 | AC-4, C-4 | S-3 통과 후 | 실제 Stop 봉투를 `~/.opal/.venv/bin/python ~/.opal/tools/ownership-tool/ownership_tool/stop_hook.py`에 stdin 주입 | 후보 `classification=current_session_owned`, `evidence.forced_count=1`, `decision_kind=block_continue`. stdout이 차단 결정 1줄 | integration · hook 진입점 실물 | 구현 후·설치 후 |
| S-4n | AC-4, C-4 | 같은 프로브 | 산출물 자기기술이 아니라 **실제 실행된 명령**을 관측한다 — S-4 프로브를 `set -x`로 기록한 셸 트랜스크립트와 주입한 stdin 봉투 원문을 파일로 남기고, PM이 그 트랜스크립트를 검사한다 | 트랜스크립트에 실행된 명령이 공개 hook 진입점 1건(+stdin 봉투 1건)뿐이고, `show_json`·`lease.claim`·`owner.json` 쓰기·`monkeypatch`·`unittest.mock` 호출이 **0건**이다. 봉투 원문이 실제 Stop 봉투 필드 집합을 갖는다 | integration · 셸 트랜스크립트 grep | 구현 후 |
| S-4b | AC-4 | 재배포 후 진짜 새 세션 | 같은 봉투 프로브를 실세션에서 1회 반복 | 동일 3값이 재현됨 | manual · 실세션 | 설치 후 (PM Gate 증거) |
| S-5 | AC-5, C-2 | S-4 통과 **후에만** | 세션 재시작 직후 / 상태 전이 없는 재개 / state view 부재 / block cap 미설정 4경로를 실제 봉투로 실측 | 각 경로의 `claim_source`·`forced_count`·`decision_kind`·`diagnostics`·`fingerprint` 유무·`stop_hook_block_cap` 반환이 기록되고, 경로마다 `이번 구현`/`후속 경계`가 PLAN D-M 2항 기준과 함께 확정됨 | integration · hook 진입점 | 구현 후 |
| S-6 | AC-6, C-6 | S-5 완료 후에만 | 봉투 `transcript_path`의 존재·읽기 가능성·크기만 관측 | transcript가 Stop 집행 판정의 입력으로 **추가되지 않았음**이 코드·산출물로 확인되고, PM 활동 로그를 남긴 경우 `progress`/`decision`이 구분된 관측 자료로만 존재함 | manual · 산출물·코드 검토 | 구현 후 |
| S-7 | AC-7 | W-1·W-6 반영 후 | `pytest opal/tools/{ownership-tool,state-tool,worktree-tool,worktree-launcher}/tests -q` 4개 스위트 실행 | 4개 스위트 전건 통과(실패 0). `test_launcher_core.py`의 복귀 경로 단언 3건과 `test_state_tool_ownership.py`·`test_stop_evaluator.py`·`test_integration.py`가 회귀 없이 통과 | unit·integration · pytest | 구현 후 |
| S-8 | AC-8, C-5, C-6 | S-4 통과 후 | 단순 진행 보고 → Stop → 후속 도구 호출 흐름을 태스크 999 자산만으로 관측 | 보고 시점 `transition_action=continue`, stop-guard receipt의 `block_count`·저장 시각, 그 **이후** 시각의 추가 도구 호출과 다음 `state.changed`(동일 `actor.session_id`)가 시각 순서로 확인됨 | integration · 파일 증거 3종 | 구현 후 |
| S-8b | AC-8 | 같은 흐름 | `await_user` 경계와 CLOSE 진입 게이트를 확인 | 두 경계는 차단 대상이 아니며 기존 계약대로 사용자 발화를 요구함 | manual · 관측 | 구현 후 |
| S-9 | AC-9 | 이번 `--wt` 실행 | registry `execution_ownership`의 `launch_receipt` 4필드·`prompt_receipt` 2필드를 확인 | 6필드가 모두 존재하고 `reported_cwd`가 발급 `worktree_root`와 일치 | manual · registry 대조 | 구현 전 (완료) |
| S-10 | AC-10 | 현재 워크트리 세션 | 세션 cwd·git toplevel·현재 브랜치·`.opal/task-ownership.json` 6필드를 registry와 대조 | cwd·toplevel이 `worktree_root`와, 브랜치가 registry `branch`와, 6필드가 발급값과 전건 일치 | manual · 대조 | 구현 전 (완료) |
| S-11 | AC-11 | 현재 세션 | 부트 재개와 최소 1회 상태 전이의 run-log 기록을 확인 | `state.changed` 사건이 존재한다. 수정 전에는 `actor.session_id`가 `null`이고, S-3 이후에는 같은 검사에서 세션 ID가 채워진다 | manual·integration · run-log | 구현 전 (완료) + 구현 후 |
| S-12 | AC-12, C-9 | W-6 반영 + 재배포 후 | hook 진입점 + 실제 봉투로 부트 경계를 1회 재현하고 registry를 확인 | 허브 registry `execution_ownership.owner_session_id`가 그 세션 ID로 채워지고, 값이 `owner.json.owner_session_id`와 일치하며, 전이가 `worktree-tool ownership-set` 경유로만 일어나 meta 파일 직접 쓰기가 없음 | integration · registry 대조 | 구현 후·설치 후 |
| S-12r | AC-12, C-9 | W-6 착수 전 | 임시 허브 registry fixture로 4분기(등록 성공 / 이미 자기 세션 / 타 세션 owner / state 불일치) 테스트를 세움 | 수정 전 코드에서 등록 성공 분기가 **실패**한다(RED 증거). 나머지 3분기는 호출 없음·진단만 | unit · pytest | 구현 전 RED |
| S-13 | AC-13, C-10 | S-3·S-12 통과 후 | 브랜치가 registry `branch`와 일치함을 확인하고 `worktree-tool checkpoint --mode agentic --stage execute --owned-scope ...`를 1회 호출 | `checkpoint_ownership_denied`가 없고 응답 `commit`이 채워지며, 같은 SHA가 허브 registry `checkpoint_shas[]`에 append됨 | integration · CLI 실물 | 구현 후 |
| S-13n | C-10 | 같은 시점 | git 이력과 원격 상태를 확인 | `main` commit·merge·push가 0건이고 커밋이 `feat/OP-TASK-999`에만 존재 | manual · git | 구현 후 |
| S-14 | AC-14, H-2 | S-12·S-13 전후 | registry `state`·`generation`·`failure_reason`·receipt 2종을 대조 | `state=worktree_session_owned` 유지, `generation`이 §5.1의 `2`에서 단조 증가(역행 0), `failure_reason=null`(`hub_owned` 복귀 없음), receipt 2종 보존, 고아 터미널 없음 | integration · registry 대조 | 구현 후 |
| S-15 | C-1, H-3 | 전 구간 | 변경 파일 경로와 재배포 절차를 확인 | 모든 소스 수정이 워크트리 안에만 있고 `~/.opal/` 직접 편집이 0건이며, 실효는 `install-mac.sh` 재배포 후에만 나타난다. 재배포 직후 배포본에 `export` 접두가 반영됐음을 1회 확인한 뒤 프로브를 시작함 | manual · git·파일 대조 | 구현 후 |
| S-16 | C-2 | 전 구간 | S-4 판정 시각을 기준으로 P4 이후 산출물의 최초 생성 시각을 대조한다. 대조 원천은 실행 전에 고정한다 — `PROBE-STOP.md`의 판정 기록 시각, `state.json` 행 timestamp, `AGENTIC-LOG.md`의 `GATE` 엔트리 시각, `git log --diff-filter=A` 상 P4 산출물(`PROBE-GAPS.md`·`PROBE-MOCKUP.md`·W-6 변경분)의 최초 등장 시각 4종 | P4 이후 산출물의 최초 생성 시각이 전건 S-4 통과 시각보다 **늦다** | manual · 시각 대조 | 구현 후 |
| S-16n | C-2 | S-4가 미달로 판정되는 경우 | 그 시점에 P4 이후 산출물의 존재 여부를 확인한다 | `PROBE-GAPS.md`·`PROBE-MOCKUP.md`가 **존재하지 않고** W-6 변경분이 0건이다(게이트가 실제로 닫혔음). S-4가 통과한 실행에서는 이 시나리오를 `해당 없음`으로 기록하되 생략하지 않는다 | manual · 파일 부재 확인 | 구현 후 |
| S-17 | C-3 | W-1 반영분 | 변경 지점을 확인 | hook 프로세스 자신의 `os.environ`을 수정한 코드가 없고, 변경이 부모 쉘에서 실행되는 프리앰블 파일의 내용에만 있음 | manual · 코드 검토 | 구현 후 |
| S-18 | C-5, C-8 | 전 구간 | 다른 태스크·슬롯의 lease·registry·run-log·터미널을 확인 | 태스크 999 외 자산의 수정이 0건(`task_128`·`task_142` 메타 불변, 타 태스크 `owner.json` 불변) | manual · 파일 대조 | 구현 후 |
| S-19 | C-7 | W-1·W-6 반영 후 | `state_tool.py`의 세션 ID 소비 지점을 확인 | `_current_session_id()`가 여전히 `OPAL_SESSION_ID` 하나만 읽고, 플랫폼 고유 변수명이 `state-tool`에 0건이며 `claude_adapter`에만 존재 | unit·manual · 코드·grep | 구현 후 |
| S-20 | H-4 | 각 재배포 직후 | `git status --porcelain dashboard/` 확인 | `dashboard/frontend/dist/`가 저장소에 남지 않는다. 생겼으면 삭제 후 재확인하고, S-13 stage 전에 한 번 더 확인 | manual · git | 설치 후 |
| S-21 | H-5 | 각 워커 착수 직후 | 세션 식별자 3종을 산출물 첫 표에 기록하고 registry `owner_session_id`와 대조 | 일치하면 진행. 불일치면 추측 없이 blocked로 반환하고 PM이 PM Gate 증거 축과 대조해 재배정 판정 | manual · 산출물 검토 | 구현 후 |
