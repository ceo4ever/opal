---
template: sdlc-v2
---
# PLAN: 워크트리 전용 터미널 런처 orca 경로 배선

> 입력: [TASK.md](TASK.md), [AGENTIC-LOG.md](AGENTIC-LOG.md)

## 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | worktree.md | `opal/core/references/harness/worktree.md` | 워크스페이스 축·루트 소유권·발급 계약·merge 경계 |
| D-2 | 설계 | task-process.md | `opal/core/references/harness/task-process.md` | 스텝 4.5·5 순서와 `--wt` 체크포인트/merge 경계 |
| D-3 | 설계 | guards.md | `opal/core/references/harness/guards.md` | 커밋·merge 승인 경계 |
| D-4 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 배포 경계·@header·State 관리·플랫폼 분기 격리 |
| D-5 | 소스 | launcher_core.py | `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py` | lifecycle·receipt 판정·원자 복귀 현행 구현 |
| D-6 | 소스 | adapters/orca.py | `opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py` | 봉투 파싱 결함 지점 |
| D-7 | 소스 | worktree_tool.py | `opal/tools/worktree-tool/worktree_tool.py` | `cmd_remove`·`cmd_status`·`cmd_ownership_set` 계약 |
| D-8 | 소스 | orca fixture | `opal/tools/ownership-tool/tests/fixtures/launcher/orca-json-response.json` | 목킹 전용 통과를 만든 가정 fixture |
| D-9 | 설계 | opal-model-mapping.md | `opal/core/references/opal-model-mapping.md` | 2-레이어 설정 머지·미설정 오류 규칙 선례 |
| D-10 | 소스 | setting.default.json | `opal/core/setting.default.json` | 전역 설정 블록 배치·`_help` 서술 규약 |
| D-11 | 소스 | session_start_hook.py | `opal/tools/ownership-tool/ownership_tool/session_start_hook.py` | SessionStart claim이 컨텍스트를 주입하지 않음 |
| D-12 | 외부 | orca CLI v1.4.205 | `orca terminal --help` / `create|close|read|list --help` | 실측 서브명령·플래그·selector 스킴 |

## Approach

결함은 "터미널은 떠 있는데 receipt가 비어 실패로 기록된다" 한 줄로 수렴한다. 따라서 **응답 원천을 실물로 고정하는 일**을 맨 앞에 두고, 그 위에 어댑터 3동사·CLI 표면·정리 경로·하네스 배선을 얹는다.

- 범위는 orca 어댑터 하나다(D-3 결정). `cmux`·`generic`·`opal_agent_fallback`은 계약을 확장 가능한 형태로 두되 이번에 손대지 않는다.
- 현행 덕타이핑 seam을 유지한다 — [MUST] `tasks/145-260919-opds-워크트리-터미널-런처-orca-배선/TASK.md` §Constraints: "상속 계층을 만들지 않는다. 현행 덕타이핑 seam을 유지하고 동사와 보고 스키마만 표준화한다."
- 상태 쓰기는 `ownership-set` 단일 경유를 유지한다(D-5:102-146). launcher에 사설 registry writer를 두지 않는다.
- `--wt` 미사용 경로에는 어떤 조건부 분기도 추가하지 않는다 — 신설 분기는 전부 `execution_ownership.adapter` 기록 유무로만 열린다(D-7:957-969이 정의한 원점은 `adapter: None`이므로 비워크트리·legacy 경로는 자연히 닫힌다).
- 변경 후보 탐색에는 `code-scan depends`를 사용했다. `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py`의 조회 결과는 `depends on: (none)` / `depended by: (none)`으로, TASK가 기록한 "호출부 0건"을 파생 스냅샷(E5) 수준에서 재확인해 준다. 호출부 신설 지점은 D-2 스텝 4.5·5 구간 하나다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| **D-A. `prompt_receipt`의 정식 원천은 기동 argv다.** `sessionstart_claim_observation`을 receipt 원천에서 **폐기**한다 | orca 어댑터는 `prompt_receipt_source = "launch_argv"`를 고정 방출한다. `prompt_id`는 실제로 argv에 실어 보낸 명령 문자열의 sha256 앞 16자, `submitted_at`은 launch 관측 시각이다. `orca terminal create`가 exit 0으로 돌아온 사실이 "그 argv가 셸에 전달됐다"의 증거이며, 그 밖의 값을 지어내지 않는다 | 현행 폴백 토큰은 `prompt_id`·`submitted_at`을 **채우지 않아** `build_prompt_receipt()`가 항상 `None`을 돌려주고 원자 복귀로 떨어진다(D-5:90-94). SessionStart hook은 컨텍스트를 주입하지 않고 전 경로 fail-safe exit 0이라 동기 receipt 원천이 될 수 없다(D-11 @header). 발화 소유자를 argv로 확정한 AGENTIC-LOG D-1과도 일치한다 |
| **D-B. Orca가 자동 생성한 fallback shell 탭은 채택하지 않는다** | launcher는 `--command`를 실은 **자기 탭 1개만** 만들고 그 handle만 `adapter_handle`로 기록한다. 자동 생성 탭은 건드리지 않는다 | 자동 탭은 우리가 만들지 않았고 `--command`를 주입할 수 없다. 그 탭을 "우리 것"으로 채택하려면 제목·시각으로 신원을 추론해야 하는데, 이는 [MUST] `opal/core/references/harness/worktree.md` §canonical path 발급 계약: "PM·워커·state-tool·run-log-tool은 이 발급값을 전달받아 사용한다. cwd에서 `.opal-worktrees` 문자열을 찾아 task path를 추측하지 않는다."의 정신과 어긋난다 |
| **D-C. close는 2스코프다** | `close(handle=…)` = 정밀 1개(원자 복귀용), `close(worktree_root=…, all=True)` = 워크스페이스 스윕(회수용). 각각 `orca terminal close --terminal <handle>` / `--worktree path:<root> --all`에 대응한다(D-12 실측 시그니처) | AC-4는 "우리가 만든 터미널만" 닫아야 하고(사용자의 다른 탭 보존), AC-6은 회수 시점에 워크트리 터미널 **0개**를 요구하므로 자동 생성 탭까지 포함한 스윕이 필요하다. 한 동사로 두 요구를 덮을 수 없다 |
| **D-D. `reported_cwd`는 `result.terminal.worktreeId`를 선언된 스킴대로 디코드해 얻는다** | 봉투는 `response["result"]["terminal"]`이다. cwd는 `worktreeId`(`<repoId>::<path>`)를 **첫 `::` 1회 분리**해 뒤쪽을 취한다. `cwd`·`worktree_selector` 키는 실물 응답에 없으므로 기대하지 않는다. 디코드 실패 시 `None`을 돌려 launcher가 launch 실패로 판정하게 둔다 | orca가 `--worktree` selector로 선언한 형식이 `id:<repo-id>::<path>`이므로(D-12 `create --help`), `worktreeId` 분해는 경로 문자열 추론이 아니라 **응답을 그 스킴대로 파싱**하는 행위다. 현행 `_reported_cwd()`는 실물에 없는 두 키만 본다(D-6:65-76) |
| **D-E. `launcher` 설정 블록은 `agents`·`default`만 소유하고 `adapter`는 소유하지 않는다** | 스키마: `launcher.default`(문자열), `launcher.agents.<name>.argv_template`(문자열), `launcher.utterance_template`(문자열). 플레이스홀더는 `{utterance}`·`{task_path}` 2종뿐이다. 2-레이어 머지는 전역 `~/.opal/setting.json` → `{프로젝트}/.opal/setting.local.json`이고 `launcher.agents.<name>`은 **이름 단위 통째 교체**, 그 위 키는 키 단위 덮어쓰기다 | 어댑터 선택은 [MUST] TASK §Acceptance criteria 1이 "`--adapter orca`로 지정한 어댑터를 명시 주입한다(자동 폴백 없음)"로 CLI 인자에 고정했으므로 설정이 소유하면 두 원천이 생긴다. 머지 입도는 D-9 §5.1의 셀 단위 선례를 그대로 따른다 |
| **D-F. `launcher` 미설정은 기본값, `models` 미설정은 중단** | 블록 전체 부재 시 `default="claude"`, `agents.claude.argv_template="claude \"{utterance}\""`, `utterance_template="{task_path} 이어서 수행"`을 코드 상수로 쓴다. 이 비대칭의 근거를 `setting.default.json`의 `launcher._help`에 한 문장으로 명시한다 | `models`는 비용·품질 결정이라 잘못된 추측이 조용히 산출물 품질을 바꾸므로 중단이 옳다(D-9:92-94 "디스패치를 중단하고 … 미설정 안내를 출력한다"). launcher는 OPAL 설치본에서 올바른 동작이 하나뿐이고, 중단을 택하면 블록을 쓴 적 없는 전 사용자의 `--wt`가 깨진다 |
| **D-G. 복귀 감지는 `worktree-tool status`의 기존 registry 조회를 넓히는 것으로 끝낸다** | `attribution_state` 방출 조건을 `execution_ownership` 보유에서 **`task_ownership_version` 보유**로 옮기고, 파생 불리언 `completed_unmerged`를 함께 싣는다. merge 가능 여부의 나머지 입력(`dirty`/`unpushed`/`merged`)은 이미 `entries[]`에 있으므로 새 필드를 만들지 않는다 | 새 통지 채널을 만들지 않는다는 AGENTIC-LOG D-4를 지킨다. 현행은 `execution_ownership`이 있을 때만 `attribution_state`를 싣는다(D-7:1735-1738)—launch가 한 번도 성공하지 못한 태스크가 `completed_unmerged`에 도달하면 허브가 못 읽는 구멍이다. legacy 메타(`task_ownership_version` 부재)는 판정에서 제외해 기존 출력을 바이트 보존한다 |
| **D-H. 터미널 정리는 `worktree-tool remove`가 3중 가드 통과 **뒤**, `git worktree remove` **앞**에 수행한다** | `execution_ownership.adapter`가 기록돼 있을 때만 `worktree-launcher/run.sh close --adapter <adapter> --worktree-root <root> --all --json`을 subprocess로 1회 호출한다. 결과는 응답의 `terminals_closed`에 싣고, 실패는 회수를 **차단하지 않고** `warnings`로 보고한다 | 가드 이전에 닫으면 회수가 거부됐을 때 사용자 터미널만 날아간다. `adapter` 미기록 경로(비워크트리·legacy·launch 미수행)는 이 분기에 진입조차 하지 않으므로 기존 응답 키 집합이 그대로다. 차단하면 orca 부재 환경에서 회수가 영구 실패한다 |
| **D-I. launcher 호출 지점은 스텝 4.5가 아니라 신설 스텝 5.5다** | 4.5 `ok: true` 목록에 "launcher 기동은 스텝 5 완료 후 5.5에서 수행한다" 1줄을 넣고, 실제 명령 블록은 5.5가 소유한다. 5.5 실패는 비차단이며 허브 세션이 그대로 태스크를 이어간다 | 워크트리 세션은 부팅 직후 `state.json`을 읽어 브리핑한다. state init(스텝 5) 전에 기동하면 첫 턴이 읽을 상태가 없다. 실패가 차단이 되면 `--wt`가 launcher 장애에 인질이 되므로, 4.5 `ok: false`가 이미 가진 비차단 폴백 규율을 그대로 승계한다 |
| **D-J. 어댑터 3동사 보고 스키마를 고정한다** | 공통 필수 키: `adapter`(str)·`exit_code`(int)·`fallback_attempted`(False 고정). `launch`는 여기에 `adapter_handle`·`reported_cwd`·`launched_at`·`prompt_id`·`submitted_at`·`prompt_receipt_source`·`launch_mode`를, `read`는 `handle`·`content`·`next_cursor`·`source`를, `close`는 `scope`(`terminal`\|`worktree_all`)·`closed`(list)를 더한다. 실패는 예외가 아니라 `exit_code != 0` + `failure_reason`·`detail`을 담은 같은 dict다 | 기계 검증 가능해야 적합성 스위트가 "새 어댑터 추가 비용"을 정의할 수 있다(AC-8). 예외 대신 dict를 쓰는 것은 현행 orca·generic이 이미 지키는 규약이므로(D-6:107-116) 새 규율이 아니다 |

폐기한 대안 1건: prompt receipt를 워크트리 lease 파일(`<canonical_task>/run/.runtime/owner.json`, `claim_source=session_start`)의 유계 폴링으로 얻는 안. 증거로는 더 강하지만 `launcher_core.run()`이 수 초간 블로킹되고 에이전트 부팅 속도에 따라 플레이키해지며, 실패 시 이미 뜬 터미널을 닫고 복귀해야 해 AC-4의 실패 표면을 넓힌다.

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 실물 orca 응답 캡처와 fixture 교체 | PM 직접 | `opal/tools/ownership-tool/tests/fixtures/launcher/orca-json-response.json`, `opal/tools/ownership-tool/tests/fixtures/launcher/orca-terminal-close-response.json`, `opal/tools/ownership-tool/tests/fixtures/launcher/orca-terminal-read-response.json`, `opal/tools/ownership-tool/tests/fixtures/README.md` | 실 워크트리에 `orca terminal create/read/close --json`을 각 1회 실행해 stdout 원문을 캡처하고 fixture 3종으로 저장한다. `create` fixture는 `result.terminal` 봉투와 `handle`·`worktreeId`·`ptyId`·`tabId`·`surface`를 실제 값 그대로 담되 워크트리 경로 성분만 `{WT}` 플레이스홀더로 치환한다. 기존 파일의 `_fixture_note`("실제 stdout 스키마는 미실측") 문구를 캡처 명령·일시로 교체한다. 캡처에 쓴 터미널은 같은 세션에서 `close`로 회수한다 | 없음 | P1 | AC-2 |
| W-2. launcher 설정 로더와 전역 블록 신설 | BE | `opal/tools/worktree-launcher/worktree_launcher/settings.py`, `opal/core/setting.default.json` | `settings.py`에 `load_launcher_settings(project_root=None)`와 `resolve_command(settings, agent=None, task_path=…)`를 추가한다. 전역 `~/.opal/setting.json` 위에 `{project_root}/.opal/setting.local.json`을 D-E 입도로 머지하고, 블록·키 부재는 D-F 기본 상수로 채운다(파일 부재·파싱 실패·타입 불일치 전건 기본값 폴백, 예외 전파 없음). `setting.default.json`에 `launcher` 블록(`_help`·`default`·`agents.claude`·`agents.codex`·`utterance_template`)을 추가하고 `_help`에 `models` 미설정 중단과의 비대칭 근거를 명시한다. 파일 상단에 @header 블록을 단다 | 없음 | P1 | AC-7 |
| W-3. worktree-tool 회수 전 터미널 정리와 복귀 감지 필드 | BE | `opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/worktree-tool/tests/test_worktree_tool.py` | `cmd_remove`에 D-H 계약의 `_close_worktree_terminals(meta)` 호출을 3중 가드 통과 직후·`git worktree remove` 루프 직전에 넣는다. `execution_ownership.adapter`가 없으면 즉시 반환해 기존 응답 키 집합을 보존하고, 있을 때만 `terminals_closed`(+실패 시 `warnings`)를 응답에 더한다. `cmd_status`는 D-G대로 `attribution_state` 방출 조건을 `task_ownership_version` 보유로 넓히고 파생 `completed_unmerged` 불리언을 더한다. 테스트에 (a) adapter 미기록 시 close 미호출·응답 바이트 동일, (b) adapter 기록 시 close 선행 호출, (c) close 실패가 회수를 차단하지 않음, (d) `completed_unmerged` 판정, (e) legacy 메타 출력 무변경 5건을 추가한다 | 없음 | P1 | AC-6, AC-9, AC-10 |
| W-4. orca 어댑터 3동사와 실물 봉투 파싱 | BE | `opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py` | `parse_response()`가 `response["result"]["terminal"]`을 읽도록 고치고 `_reported_cwd()`를 D-D의 `worktreeId` 첫 `::` 1회 분리로 교체한다. `PROMPT_SOURCE_SESSIONSTART_CLAIM`을 제거하고 D-A의 `launch_argv` 원천으로 대체한다(`prompt_id`=전송 명령 sha256 앞 16자, `submitted_at`=관측 시각). `read(handle, *, cursor=None, limit=None, screen=False)`와 `close(*, handle=None, worktree_root=None, all=False)`를 D-C·D-J 스키마로 추가하고, `close`는 `handle`·`worktree_root` 중 정확히 하나를 요구한다(둘 다/둘 다 아님은 `exit_code != 0` 실패 dict). @header의 `description`·`exports`를 3동사와 새 원천에 맞춰 갱신한다 | W-1 | P2 | AC-2, AC-8 |
| W-5. 원자 복귀 시 터미널 정리와 close seam 소비 | BE | `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py` | `_revert()`가 복귀 직전에 `adapter.close(handle=…)`를 1회 호출하도록 확장한다. handle은 launch 보고 dict의 `adapter_handle`에서만 취하고, 없으면 close를 시도하지 않는다(대상을 추측하지 않는다). close 실패·미구현(`AttributeError`)은 삼켜서 로그 필드(`terminal_close`)로만 남기고 `ownership-set` 복귀는 반드시 수행한다 — 복귀 실패가 정리 실패에 종속되면 dual owner가 남는다. `run()`의 4개 복귀 경로(`adapter_report_invalid`·`launch_receipt_missing`·`reported_cwd_mismatch`·`prompt_receipt_missing`) 전건이 같은 경로를 탄다. @header `description`을 갱신한다 | 없음 | P2 | AC-4 |
| W-6. CLI 표면 신설 | BE | `opal/tools/worktree-launcher/worktree_launcher/cli.py`, `opal/tools/worktree-launcher/run.sh` | `cli.py`에 `launch`/`read`/`close` 3개 서브명령을 argparse로 만든다. `--adapter`는 전 서브명령 필수이며 값은 폐쇄 목록(`orca`)에서만 해석하고 자동 폴백·자동 탐지를 하지 않는다. `launch`는 `--project-root`·`--task`·`--worktree-root` 필수, `--agent`·`--command`·`--owner-session-id` 선택이며 `--command` 미지정 시 W-2의 `resolve_command()`로 결정한다. 출력은 단일 라인 JSON, 성공 exit 0 / 실패 exit 1이다. `run.sh`의 `not_implemented` 블록을 `PYTHONPATH="$SCRIPT_DIR" "$VENV_PYTHON" -m worktree_launcher.cli "$@"` 위임으로 교체하고 venv·import 가드 2종은 유지한다 | W-2, W-4, W-5 | P3 | AC-1, AC-3, AC-7 |
| W-7. 어댑터 적합성 테스트 스위트 | BE | `opal/tools/worktree-launcher/tests/test_adapter_conformance.py` | 어댑터 모듈을 파라미터화해 D-J 계약을 집행하는 스위트를 만든다. 검사 항목: (1) `launch`/`read`/`close` 3동사 존재·호출 가능, (2) 각 보고 dict의 공통 필수 키와 타입, (3) 실패 경로가 예외가 아니라 `exit_code != 0` dict, (4) `fallback_attempted`가 항상 False, (5) `launch` argv에 worktree/checkout 생성 서브명령 0건, (6) 성공 보고가 `launcher_core.build_launch_receipt()`·`build_prompt_receipt()` 둘 다 non-None을 만족, (7) `close`의 인자 배타성. 새 어댑터는 이 파일에 모듈명 1줄을 추가해 전건 통과시키는 것이 유일한 추가 비용이다 | W-4, W-5 | P3 | AC-8 |
| W-8. orca 어댑터 단위 테스트 갱신과 실물 CLI 대조 | BE | `opal/tools/worktree-launcher/tests/test_adapter_orca.py` | 기존 3건을 실물 fixture 기준으로 고쳐 `adapter_handle`·`reported_cwd`가 둘 다 채워짐을 단언하고, `prompt_receipt_source == "launch_argv"`와 `prompt_id`·`submitted_at` 동시 충족을 추가한다. [MUST] TASK §Constraints: "적합성 테스트에 **실물 CLI 대조 1건**을 포함한다. 목킹 전용 검증은 이 결함을 다시 통과시킨다." — `orca`가 PATH에 있고 `OPAL_LIVE_ORCA=1`일 때만 도는 live 테스트 1건을 추가한다. 이 테스트는 실 워크트리에 터미널을 1개 만들고 `parse_response()`가 두 필드를 채우는지 확인한 뒤 `close(handle=…)`로 반드시 회수한다(teardown은 예외 경로에서도 실행). 그 외 환경에서는 skip이며 기본 스위트를 느리게 하지 않는다 | W-1, W-4 | P3 | AC-2, AC-8 |
| W-9. 하네스 배선 — 스텝 5.5와 회수·복귀 경계 등재 | PM 직접 | `opal/core/references/harness/task-process.md`, `opal/core/references/harness/worktree.md` | `task-process.md` 4.5 `ok: true` 목록에 "launcher 기동은 스텝 5 완료 후 5.5에서 수행한다" 1줄을 넣고, 스텝 5.5를 신설해 `worktree-launcher/run.sh launch --adapter orca --project-root … --task … --worktree-root …` 명령 블록과 비차단 실패 규율(D-I)을 기술한다. `--wt` 체크포인트·merge 절에 [MUST] `opal/core/references/harness/guards.md` §커밋 규칙: "`main`·기본 브랜치로의 merge와 그에 수반되는 merge commit은 항상 별도 사용자 승인 후 허브에서 수행한다."가 불변임을 재확인하는 포인터만 둔다(규정 복제 금지). `worktree.md`에는 실행 세션 기동·터미널 회수 경계 1개 절을 더하고 절차 원문은 `task-process.md`를 가리킨다 | W-6 | P4 | AC-5 |
| W-10. launcher README를 현행 사실로 갱신 | BE | `opal/tools/worktree-launcher/README.md` | "adapter 2종·CLI 표면은 후속 Work item이 채운다"·"test_adapter_*는 RED"·"adapter는 `launch` 한 메서드만 요구" 3개 stale 서술을 제거한다. 패키지 레이아웃에 `settings.py`·`cli.py`·`adapters/`·`tests/test_adapter_conformance.py`를 반영하고, D-J의 3동사 보고 스키마와 D-E 설정 스키마, live 테스트 실행 조건(`OPAL_LIVE_ORCA=1`)을 기재한다 | W-6 | P4 | AC-8 |
| W-11. 실물 완주 통합 검증 | PM 직접 | `opal/tools/worktree-launcher/tests/test_integration.py` | live 마커가 달린 end-to-end 케이스 1건을 추가한다 — 실 registry 태스크에 대해 `launcher_core.run()`이 orca 어댑터로 `worktree_session_owned`까지 전이하고 registry meta에 `launch_receipt`·`prompt_receipt` 2종이 객체로 남는지 확인하며, 실패 주입 케이스가 `hub_owned` 복귀 + 터미널 잔존 0개를 만족하는지 `orca terminal list --worktree path:<root>`로 대조한다. 이어서 `--wt` 태스크 1건을 실제로 만들어 워크트리 터미널의 LLM 첫 턴 자기시작과 태스크 이어받기를 관측하고, `worktree-tool remove` 후 터미널 0개를 확인한다. 관측 증거(명령·스코프·출력)를 태스크 폴더에 남긴다 | W-6, W-9 | P5 | AC-3, AC-5, AC-10 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. `worktreeId`의 `repoId` 성분에 `::`가 들어가지 않는다 | D-D의 첫 `::` 1회 분리로 얻는 `reported_cwd` | cwd 가드가 오탐해 정상 launch가 매번 `reported_cwd_mismatch`로 복귀한다 | W-4는 분리 실패·경로 비절대 시 값을 지어내지 않고 `None`을 반환한다. W-8의 live 대조가 실제 `repoId` 형태를 관측 증거로 고정한다 |
| H-2. `orca terminal create --json`의 봉투가 호스트·버전에 따라 다르다 | `result.terminal` 경로 고정 | 다른 Orca 버전에서 다시 `adapter_handle=null`로 회귀한다 | fixture에 캡처 일시와 `orca --version`을 함께 기록하고(W-1), 기본 스위트가 아니라 W-8의 live 테스트가 버전 드리프트를 잡는 유일한 관문임을 README에 명시한다(W-10) |
| H-3. argv에 실은 발화가 TUI에 실제로 제출되는지는 orca 응답이 확인해 주지 않는다 | D-A의 `launch_argv` receipt가 "첫 턴 자기시작"을 보증한다는 가정 | receipt는 성공인데 터미널은 프롬프트만 띄운 채 멈춘다(AC-5 미충족) | receipt 성립과 첫 턴 자기시작을 분리해 다룬다 — 후자는 W-11의 실물 완주 관측으로만 확정하며, 어떤 단위 테스트도 이를 대신한다고 주장하지 않는다 |
| H-4. 회수 시점에 워크트리 세션이 아직 살아 있을 수 있다 | D-H의 스윕 close가 사용자의 진행 중 작업 터미널을 닫는다 | 미저장 작업 손실 | close는 `remove`의 3중 가드(dirty → unpushed → unmerged)를 **통과한 뒤에만** 실행한다. dirty 워크트리는 가드에서 이미 거부되므로 스윕에 도달하지 않는다 |
| H-5. orca 부재·비-orca 환경 | `cmd_remove`의 신설 close 스텝 | 회수가 영구 실패해 슬롯이 잠긴다 | `execution_ownership.adapter` 미기록이면 분기 진입 자체를 하지 않고, 기록됐어도 close 실패는 `warnings` 비차단이다(D-H). W-3 테스트 (a)(c)가 두 경로를 고정한다 |
| H-6. 자동 생성 fallback shell 탭의 존재가 환경 설정(`externalWorktreeVisibility`)에 의존한다 | AC-6의 "터미널 0개" 판정 | 환경에 따라 AC-6이 통과/실패로 갈린다 | AC-4는 `--terminal <handle>` 정밀 close라 자동 탭에 영향받지 않고, AC-6은 `--worktree … --all` 스윕이라 자동 탭 유무와 무관하게 0개로 수렴한다(D-C). 두 스코프 분리가 이 의존을 흡수한다 |

## Release and recovery

- **적용 순서**: P1(fixture·설정·worktree-tool) → P2(어댑터·코어) → P3(CLI·테스트) → P4(하네스 문서·README) → P5(실물 완주). P4 완료 후 [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."에 따라 `./scripts/install-mac.sh`로 재배포한 뒤에만 P5에 진입한다 — 스텝 5.5는 배포본 `~/.opal/tools/worktree-launcher/run.sh`를 호출하므로 배포 전 검증은 무의미하다.
- **검증 범위**: 결정론 = `opal/tools/worktree-launcher/tests/`(현행 기준선 15건, `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-launcher/tests/ -q` 스코프)와 `opal/tools/worktree-tool/tests/`. 회귀 = `--wt` 미사용 경로의 worktree-tool·state-tool 기존 스위트 전건(AC-10). 실제 연동 = W-8의 live 대조 1건과 W-11의 `--wt` 완주 1건, 둘 다 `OPAL_LIVE_ORCA=1` 명시 opt-in이며 목킹으로 대체하지 않는다.
- **실패 시**: 배포 전에는 워크트리 브랜치 체크포인트로 되돌린다. 배포 후 launcher가 불안정하면 `run.sh`만 `not_implemented` 반환으로 되돌리면 된다 — 스텝 5.5는 비차단 설계(D-I)라 `--wt` 태스크 생성·진행은 허브 세션에서 그대로 완주하고, registry는 `_revert()` 경로로 `hub_owned`에 머물러 정합을 유지한다. W-3의 `cmd_remove` 변경은 `adapter` 미기록 시 진입하지 않으므로 별도 롤백 없이 무해하다.
