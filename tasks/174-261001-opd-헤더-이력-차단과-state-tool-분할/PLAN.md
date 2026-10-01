---
template: sdlc-v2
---
# PLAN: @header 이력 누적 코드 차단 + state-tool 동작 보존 분할

> 입력: [TASK.md](TASK.md)

## Approach

세 갈래를 한 태스크로 묶어 처리한다.

1. **차단 전환(code-scan)**: `header_history`를 비차단 경고에서 차단(exit 2)으로 바꾸고, 머리말이 읽기 범위(24,576바이트) 안에서 닫히지 않는 파일을 `uncovered:pre_existing`으로 흘리지 않고 새 차단 코드 `header_overflow`로 드러낸다. 읽기 범위 상수는 올리지 않는다(올리면 초과가 다시 숨는다).
2. **저장소 정리**: 차단을 켠 상태에서 `code-scan validate`(전체)가 exit 0이 되도록 `header_history` 10건(9개 파일)과 `uncovered:incomplete` 1건을 정리하고, 읽기 범위를 넘은 `state_tool.py` 머리말을 역할 한 줄 수준으로 줄인다.
3. **state-tool 분할**: `state_tool.py`를 책임 영역별 모듈 패키지로 나누고 `state_tool.py`는 머리말·재노출·진입점만 남긴다. 외부 계약(C-1)은 그대로다.

PM Gate는 이미 CLOSE 전 `validate --changed`의 `ok:true`를 요구하므로(`pm-review-gate.md:74-75`) 별도 게이트 코드를 추가하지 않는다. 종료 코드가 2가 되면 Gate가 통과하지 못하는 것이 AC-1의 집행 경로다.

PLAN 단계 재측정으로 TASK의 사실 한 가지를 바로잡았다(TASK.md Problem 반영 완료): 읽기 범위 초과 머리말은 `state_tool.py` 1건이며, `ownership-tool/tests`의 두 파일은 `# key: value` 형식 파싱 실패라 이 태스크 범위 밖이다.

## Findings

### 직접 변경
- `opal/tools/code-scan/code-scan.js` — 차단 목록(`:3600-3604`)에서 `header_history` 제외 제거, `header_overflow` 판정·집계 추가, `:42-44` 주석 갱신.
- `opal/tools/code-scan/tests/test-header-history.js` — 비차단을 단언하던 케이스(TS-010·TS-011 등)를 차단 기준으로 전환.
- `opal/tools/code-scan/tests/test-validate.js` — 읽기 범위 밖에서 닫히는 머리말 픽스처(`HanWinOut`·`HanWinEdge`)를 `uncovered:pre_existing`·exit 0으로 단언하던 `[T106/ADD-2]` c1·c2·c3·불변식 4건을 아래 Decisions '기존 읽기 범위 테스트 처리'대로 바꾸고 `header_overflow` 케이스 추가.
- `opal/tools/state-tool/state_tool.py` — 머리말 축소와 분할 후 재노출 진입점으로 전환.
- `opal/tools/state-tool/state_tool_parts/__init__.py` — 분할 모듈 패키지 신규 생성(같은 디렉토리의 책임별 모듈 포함).
- `opal/tools/state-tool/tests/test_pilot_shared_contract.py`, `opal/tools/oppb-runtime-tool/tests/test_pilot_isolation.py`, `opal/tools/state-tool/tests/test_state_tool_mode_contracts.py`, `opal/skills/opal-skill-tester/scripts/skill_tester.py` — 분할 후 소스 읽기 범위·설치본 드리프트 비교 범위를 하위 모듈까지 확장.
- `opal/tools/state-tool/tests/state_tool_test_support.py`, `opal/tools/state-tool/tests/test_state_tool_core_cli.py`, `opal/tools/state-tool/tests/test_state_tool_extended_contracts.py`, `opal/tools/state-tool/tests/test_state_tool_test_cycle.py`, `opal/tools/state-tool/tests/test_state_tool_ownership.py` — patch 대상 이동(`base` 모듈 속성)·단일 파일 복사·단독 적재 보정, ownership 테스트 머리말 정리.
- `opal/tools/state-tool/tests/test_split_surface.py`, `opal/tools/state-tool/tests/fixtures/state_tool_surface.json` — 분할 전 최상위 이름·코드표 표면 보존 검사(신규).
- `opal/tools/git-sync-tool/tests/conftest.py`, `opal/tools/git-sync-tool/tests/test_git_sync_tool.py`, `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`, `opal/tools/run-log-tool/tests/test_run_log_tool.py`, `opal/tools/worktree-tool/tests/test_worktree_tool.py`, `opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/oppb-runtime-tool/tests/test_product_flow.py`, `opal/tools/tool-scan/tests/test_tool_scan.py`, `opal/tools/test-tool/tests/test_e2e_action_value_redaction.py` — 머리말만 정리(이력·미정의 필드 제거, exports 보강).

### 회귀 확인
- `opal/skills/opal-self-pm/SKILL.md`, `opal/skills/opal-code-map-builder/SKILL.md` — 전체·변경 validate 소비 문구가 새 차단과 모순되지 않는지 확인만 한다.
- `opal/tools/event-loader/event_loader.py`, `opal/tools/ownership-tool/ownership_tool/stop_hook.py`, `opal/tools/run-log-tool/adapters/agent_tool_adapter.py` — `run.sh`·경로로 state-tool을 호출하는 외부 소비자이며 호출 경로·출력이 그대로인지 확인만 한다.
- `scripts/install-mac.sh` — `tools` 디렉토리 통째 복사(`install_dir`)라 새 하위 패키지가 배포에 포함되는지 확인만 한다.

### 문서 갱신
- `opal/core/references/harness/header-rules.md` — `:124`의 "비차단 경고(exit code 불변)"를 차단으로, `header_overflow` 설명 추가.
- `opal/core/references/header-standard.md` — `:182` 임계값 근거 문장을 차단 기준으로 고치고 어긋난 `code-scan.js` 줄번호 인용 제거.
- `opal/core/references/harness/pm-review-gate.md` — code-scan 판정 기준 문구(`newly_uncovered` 0건)에 `header_history`·`header_overflow` 0건을 한 줄로 명시한다. `validate --changed` ok:true 요구 자체는 그대로다.
- `docs/CONVENTIONS.md` — `:228`의 `header_history` 비차단 경고 서술을 차단 서술로 고친다.
- `opal/tools/code-scan/README.md` — 종료 코드 표(`:288-292`)·차단/비차단 분류에 `header_history` 차단과 `header_overflow` 반영.
- `opal/tools/state-tool/README.md` — 모듈 구조 절 추가, 파일 구성 서술 갱신.

### 미확인 가정
H-1, H-2, H-3.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| header_history 차단 범위 | `description`·`note`의 서로 다른 태스크 번호 2개 이상(`TASK_TAG_THRESHOLD`)과 미정의 필드(`undeclared_field`)는 전체·`--changed` 두 모드 모두 차단(exit 2). 판정 로직·임계값은 불변 | 정리 후 전체 0건이라(AC-3) 전체 모드 차단이 가능하고, `--changed`만 차단하면 미변경 파일의 누적이 계속 숨는다. 같은 `code`라 sub별 분기를 두지 않는다 |
| 읽기 범위 초과 | 신규 위반 코드 `header_overflow`(차단). 조건: 파일이 읽기 범위를 가득 채우고, 범위 안에 근접 `@header {`가 있으며, 닫는 `}`가 범위 안에 없다. 이 조건이면 `uncovered`를 중복 기록하지 않고 `header_overflow` 1건만 낸다. `counts.header_overflow` 추가. `HEADER_READ_BYTES`는 24,576 유지 | 현재는 `extractHeaderFromContent`가 `null`을 돌려 `classifyUncovered`가 `pre_existing`(비차단)으로 보낸다(`code-scan.js:1073-1085`, `:1170-1195`). 상한 상향은 초과를 다시 숨기므로 택하지 않는다 |
| 기존 읽기 범위 테스트 처리 | `test-validate.js` `[T106/ADD-2]` 4건은 `header_overflow` 적용으로 다음처럼 바꾼다. 실행을 둘로 나눠 `same`(창문 안 `winIn`만, exit 0·covered 1)과 `overflow`(`winOut`·`winEdge`, exit 2)로 한다. c1은 `same` 실행 기준으로 기존 단언을 유지한다. c2·c3는 `overflow` 실행에서 해당 파일의 `header_overflow` 위반 1건·`uncovered` 없음·exit 2를 단언하고 픽스처 전제 단언(바이트 위치, 한글 경계 절단)은 유지한다. 106 ADD-1 불변식(라이브 창문과 `classifyUncovered`의 HEAD 창문이 같은 바이트 창문)은 `winOut`·`winEdge`와 같은 크기 구성의 HEAD 사본을 커밋하고 작업본에서는 머리말을 제거한 대체 픽스처로 유지한다: HEAD 사본의 머리말이 창문 밖에서 닫히면 `uncovered:pre_existing`·비차단, 창문 안에서 닫히는 기존 대조군(`regressCtl`)은 `newly_uncovered`·exit 2. 라이브 창문 쪽 플립은 c1(안: covered)과 c2(밖: `header_overflow`)가 증명한다 | 차단 전환이 106 ADD-1 계약 검증을 없애지 않도록 한다. 대체 픽스처는 uncovered 분류 경로(`classifyUncovered`)를 계속 실행한다 |
| 게이트 집행 경로 | 코드 변경은 code-scan 종료 코드까지만. PM Gate·TEST Gate 문서 절차는 바꾸지 않는다 | `pm-review-gate.md:74-75`가 이미 `validate --changed` exit 0을 요구한다. TEST Gate는 code-scan 소비처가 아니다(`test-cycle.md` 언급 없음) |
| 분할 구조 | `state_tool.py`는 머리말·`sys.path` 보강·하위 모듈 재노출·`main()` 호출만 가진다. 코드는 `opal/tools/state-tool/state_tool_parts/` 아래 정확히 9개 모듈로 나눈다(분할 전 줄 범위, 아래 이동 예외 적용): `codes.py`(상수·코드표 64~527), `base.py`(전이 보조 함수 528~607, 출력·오류·외부 모듈 로더·상태 I/O 608~1080), `run_log.py`(1081~2483), `journal.py`(STATE.md·행 탐색·모드·todo·history·memory 2484~2965), `guards.py`(가드·전이 검사·행 빌드 2966~3478), `gates.py`(plan 계약·clarification·evidence 게이트·설계 게이트·`cmd_verify`·`cmd_event_verify` 5511~7798), `commands_core.py`(init·show·resolve·advance·mark·block·validate·add-row·status와 worker 소요 검사 3479~4880), `commands_run.py`(test-clock·run-start·attribution·부트 브리핑·gate-pass 4881~5510), `cli.py`(`build_parser`·`main` 7799~끝). 이동 예외(호출 그래프 실측으로 확정, 위반 0건): `_derive_next_action`·`_COMPLETE_STATUSES`는 `base.py`로, `_build_new_state_md`는 `journal.py`로, `_check_evidence`·`_check_mock_patterns`·`_find_scenario_file`·`_check_red_evidence`·`_match_test_files`·`_PASS_KEYWORDS`·`_MOCK_CODE_PATTERNS`는 `gates.py`로 옮긴다. import 방향은 `codes`<`base`<`run_log`<`journal`<`guards`<`gates`<(`commands_core`·`commands_run`)<`cli`만 허용한다. `commands_core`와 `commands_run`은 서로 import하지 않으며, 같은 층이 아닌 하위 모듈의 import는 허용하되 상위 모듈 import는 금지한다. 줄 범위는 함수 경계에 맞춘 조정만 허용하고 모듈 수는 바꾸지 않는다 |
| 하위 모듈 적재 | `state_tool.py`가 자기 디렉토리를 `sys.path`에 한 번 추가(이미 있으면 생략)하고 `import state_tool_parts`로 적재한다 | `run.sh`는 스크립트 직접 실행이라 같은 디렉토리가 이미 `sys.path[0]`이다. `spec_from_file_location` 단독 적재(`test_state_tool_test_cycle.py`)도 이 보강으로 동작한다. 외부 도구 적재의 sys.path 비오염 관례(GC-007)는 외부 모듈에 대한 것이며 자체 패키지 적재와 별개다 |
| 재노출과 patch 대상 | 모든 최상위 이름(밑줄 시작 포함)을 `state_tool` 모듈에 재노출해 `ST.<이름>` 읽기를 유지한다. 재노출은 이름을 하나씩 나열하는 import 문이 아니라 하위 모듈의 모듈 속성을 순회해 `state_tool` 전역에 채우는 방식으로 한다(`MODE_BOUNDARY_STAGES` 등 이름 출현 횟수를 세는 `test_state_tool_mode_contracts.py:773`을 보존하기 위함). 시간·모듈 로더 주입점인 `get_kst_datetime`·`_import_ownership_lease`·`_import_run_log_core`만 호출 지점에서 `base.<이름>(...)`으로 모듈 한정 호출한다(이 3개 이름의 호출 지점 기계적 치환만 허용, 나머지 코드는 원문 이동). 나머지 이름은 `from` import로 직접 바인딩한다. 테스트의 `patch.object(ST, "get_kst_datetime")`(`_mock_now()` 포함)·`patch.object(ST, "_import_ownership_lease")`는 `state_tool_parts.base` 모듈 속성을 겨냥하도록 바꾼다 | `base.<이름>` 한정 호출이면 한 곳의 patch가 모든 소비 모듈에 적용된다. `_mock_now()`가 98회 쓰이므로 정의 지점 한 곳(`state_tool_test_support.py:147`)만 고치면 된다 |
| 소스 텍스트를 읽는 소비자 | 저장소 전수 조사(`state_tool.py` 경로 상수를 쓰는 테스트·스킬 전건)로 소스 텍스트를 읽는 지점은 다음 5곳뿐이며 나머지는 모두 subprocess 실행이다: `test_pilot_shared_contract.py:422`, `test_pilot_isolation.py:384-385`, `test_state_tool_mode_contracts.py:60`·`:773`(`_SRC_093`)·`:1176`(`git show HEAD:./state_tool.py`). 앞의 4곳은 `state_tool.py`와 `state_tool_parts/*.py`를 이어 붙인 현재 소스를 읽도록, `:1176`은 HEAD의 `state_tool.py`와 HEAD의 `state_tool_parts/*.py`를 이어 붙여 읽도록 읽기 대상만 바꾼다(단언·정규식 불변, `test_pilot_isolation.py`의 baseline 쪽 `git show`와 `test_state_tool_run_log.py`의 옛 SHA `git show`는 옛 단일 파일 그대로). `opal-skill-tester`의 `_install_drift()`는 기존 `state_tool.py` 쌍(양쪽 모두 있을 때만 비교)에 더해, 설치본에 `tools/state-tool/state_tool.py`가 있을 때 소스(`opal/tools/state-tool/state_tool_parts/*.py`)와 설치본(`tools/state-tool/state_tool_parts/*.py`)의 파일명 합집합을 쌍으로 비교하며 한쪽에만 있는 하위 모듈과 내용이 다른 하위 모듈은 모두 드리프트 경고로 보고하고, `_framework_fingerprint()`(`skill_tester.py:415-423`)는 설치본 `OPAL/tools/state-tool/`에서 `state_tool.py` 바이트 뒤에 파일명 오름차순으로 정렬한 `state_tool_parts/*.py` 바이트를 이어 붙여 sha256을 계산한다 | 분할 후 리터럴(`STAGE_ENUM`·`skill_enum`·argparse `--skill` choices)이 하위 모듈로 이동하므로 읽기 범위를 맞춘다 |
| 동작 보존 증거 | (a) `test_split_surface.py`가 분할 전 최상위 이름 집합·`ERROR_CODES` 59종·`--help` 서브커맨드 목록 보존을 검사한다. (b) TEST에서 기준 트리(`git archive dee405ca opal`을 임시 디렉토리에 푼 것)와 분할본 트리(작업 트리의 `opal/`을 같은 모양으로 복사한 것)의 `opal/tools/state-tool/state_tool.py`를 같은 fixture로 각각 실행해(두 트리 모두 `__file__` 기준 형제 도구 경로가 유효하다) stdout JSON(시각·run id 정규화)과 종료 코드를 대표 명령으로 비교한다. (c) 기존 state-tool 테스트 전건 | AC-4 요구 "기존 테스트 전체와 대표 명령 출력이 같다"를 도구로 판정한다 |
| install | 이 태스크는 `~/.opal`에 install을 실행하지 않는다. `install_dir`의 디렉토리 통째 복사를 임시 디렉토리 복사 실행으로 확인한다 | 진행 중인 다른 태스크 세션(172·173)이 배포본 state-tool을 쓰고 있어 분할 중간 배포가 위험하다. 실제 install은 main 병합 뒤 사용자 승인 흐름이 소유한다 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. code-scan 차단 전환·`header_overflow` | opal-task-agent (code-scan 소유) | `opal/tools/code-scan/code-scan.js`, `opal/tools/code-scan/tests/test-header-history.js`, `opal/tools/code-scan/tests/test-validate.js`, `opal/tools/code-scan/README.md` | `blockingViolations`에서 `header_history` 제외 조건 삭제. `cmdValidate`의 미커버 분기에서 `header_overflow` 조건을 먼저 판정해 해당 시 `{code:'header_overflow', file, detail}`만 기록하고 `uncovered` 분류를 건너뜀(판정은 `readFileHead` 결과와 `extractHeaderFromContent` 로직 재사용, 근접 판정 중복 신설 금지). `counts.header_overflow` 추가. `:42-44` 주석과 `:3600` 부근 비차단 주석을 실측·차단 사실로 갱신. 기존 비차단 단언 테스트를 exit 2 단언으로 전환하고 `test-header-history.js`의 머리말 description(`이력 누적 비차단 감지기 … exit code 불변`)·단언 메시지·주석(`:6`·`:203`·`:580`·`:605` 부근)을 차단 서술로 바꾸고 overflow(범위 가득 참+닫힘 없음 → 차단, 짧은 닫힘 헤더·헤더 없는 대형 md → 비해당) 테스트 추가. README 종료 코드·분류 표 갱신 | 없음 | P1 | AC-1, AC-2, C-3 |
| W-2. state-tool 분할과 머리말 정리 | opal-task-agent (state-tool 소유) | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/state_tool_parts/__init__.py`(와 같은 디렉토리의 책임별 모듈), `opal/tools/state-tool/tests/state_tool_test_support.py`, `opal/tools/state-tool/tests/test_state_tool_core_cli.py`, `opal/tools/state-tool/tests/test_state_tool_extended_contracts.py`, `opal/tools/state-tool/tests/test_state_tool_test_cycle.py`, `opal/tools/state-tool/tests/test_state_tool_ownership.py`, `opal/tools/state-tool/tests/test_split_surface.py`, `opal/tools/state-tool/tests/fixtures/state_tool_surface.json`, `opal/tools/state-tool/tests/test_pilot_shared_contract.py`, `opal/tools/oppb-runtime-tool/tests/test_pilot_isolation.py`, `opal/tools/state-tool/tests/test_state_tool_mode_contracts.py`, `opal/skills/opal-skill-tester/scripts/skill_tester.py`, `opal/tools/state-tool/README.md` | 분할 전 `state_tool.py`에서 최상위 이름·`ERROR_CODES`·서브커맨드 목록을 추출해 fixture 저장(RED-first: surface 테스트가 분할 전엔 모듈 부재로 실패). PLAN §분할 구조의 모듈·이동 예외대로 함수·상수를 원문 그대로 이동(로직 수정 금지, 선언 순서·`_RUN_LOG_TERMINAL_EVENTS` 중복 정의의 후행 우선 의미 보존). 각 모듈에 짧은 인라인 @header(역할 한 줄, 이력 금지). `state_tool.py`는 머리말(역할 한 줄·exports 최소)·sys.path 보강·재노출·`main` 진입만. `__file__` 기반 경로 상수는 `state-tool` 디렉토리 기준으로 재계산해 동일 값 유지. 테스트 보정: patch 대상 3곳을 `state_tool_parts.base` 모듈 속성으로 이동, 소스 읽기 지점은 읽기 대상만 `state_tool.py`+`state_tool_parts/*.py` 결합으로 변경(`test_pilot_shared_contract.py:422`, `test_pilot_isolation.py:384-385`의 현재 소스 쪽, `test_state_tool_mode_contracts.py:60`·`:773`; `:1176`의 `git show HEAD:./state_tool.py`는 HEAD의 `state_tool.py`와 HEAD의 `state_tool_parts/*.py`를 `git ls-tree`·`git show`로 결합해 읽음), `skill_tester.py`의 `_install_drift()` 쌍 확장과 `_framework_fingerprint()` 해시 대상 확장(위 결정), `extended_contracts`의 단일 파일 복사를 패키지 포함 복사로, `test_cycle` 단독 적재 확인. `test_state_tool_ownership.py` 머리말의 이력 제거. README에 모듈 표 추가 | 없음 | P1 | AC-3, AC-4, C-1, C-2 |
| W-3. 저장소 머리말 정리 | opal-task-agent (각 도구 파일 소유) | `opal/tools/git-sync-tool/tests/conftest.py`, `opal/tools/git-sync-tool/tests/test_git_sync_tool.py`, `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`, `opal/tools/run-log-tool/tests/test_run_log_tool.py`, `opal/tools/worktree-tool/tests/test_worktree_tool.py`, `opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/oppb-runtime-tool/tests/test_product_flow.py`, `opal/tools/tool-scan/tests/test_tool_scan.py`, `opal/tools/test-tool/tests/test_e2e_action_value_redaction.py` | `description`·`note`의 태스크 번호 이력 단락을 지우고 현재 역할만 남김. 미정의 필드(`migration_note`·`track`·`ownership_contract`)는 값이 현재 사실이면 `description`에 흡수하고 키는 삭제. `test_e2e_action_value_redaction.py`는 누락된 `exports` 추가. `worktree_tool.py`가 인용하는 `state_tool.py:<줄번호>` 주석은 함수명 인용으로 교체. 코드 동작 변경 금지 | 없음 | P1 | AC-3, C-2 |
| W-4. 규칙·컨벤션 문서 갱신 | opal-task-agent (문서 소유) | `opal/core/references/harness/header-rules.md`, `opal/core/references/header-standard.md`, `opal/core/references/harness/pm-review-gate.md`, `docs/CONVENTIONS.md` | `header-rules.md:124`의 비차단 서술을 차단(exit 2)으로 바꾸고 `header_overflow` 처리 절차(머리말을 읽기 범위 안으로 줄임) 한 줄 추가. `header-standard.md:182` 근거 문장을 차단 기준으로 고치고 이 파일의 `code-scan.js:<줄번호>` 형태 인용은 어긋남 여부와 무관하게 전부 삭제해 기호 이름(`TASK_TAG_THRESHOLD` 등)만 인용한다. `## 변경 이력` 표의 기존 행은 과거 기록이므로 고치지 않고 새 행도 추가하지 않는다(수기 이력 절 추가 금지). `pm-review-gate.md`는 code-scan 판정 기준 문구(`newly_uncovered` 0건 서술)에 `header_history`·`header_overflow` 0건을 한 줄 추가하고 `validate --changed` ok:true 요구는 유지한다. `docs/CONVENTIONS.md:228`의 비차단 서술은 차단 서술로 교체한다 | 없음 | P1 | AC-1, AC-2, C-3 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 정리 후 전체 `validate`가 exit 0이 된다는 가정 | 실측상 현재 전체 validate는 `uncovered:incomplete` 1건 때문에 이미 exit 2이고, 다른 차단 코드는 0건이다. 이 외 숨은 차단이 정리 중 드러날 수 있다 | AC-3·"차단 켠 상태에서 저장소 전체 통과" 미달 | W-3이 incomplete 1건을 포함해 정리하고, TEST에서 전체 validate exit 0과 `header_history`·`header_overflow` 0건을 직접 실행 확인(S-3) |
| H-2. 분할 후 테스트의 파일 단위 가정 | `extended_contracts`의 단일 `state_tool.py` 복사, `test_cycle`의 단독 적재, `ST` 대상 patch 3곳, `state_tool.py` 소스를 정규식으로 읽는 테스트 3개 파일 5곳(state-tool 2개 파일·oppb-runtime-tool 1개 파일)이 형제 모듈 도입으로 실패할 수 있다 | 기존 테스트 전건 동일(AC-4) 미달 | W-2가 해당 테스트를 보정하되 단언 내용은 바꾸지 않는다. 보정 전후 테스트 수·이름 집합 동일을 S-5로 확인하고, state-tool 밖의 `test_pilot_isolation.py`는 S-6에서 별도 실행한다 |
| H-3. `header_overflow` 오탐·미탐 | 문서(md)가 `@header {`를 산문으로 인용하거나 큰 파일의 닫는 `}`가 범위 직후에 있는 경우 판정이 갈린다 | 정상 파일 차단 또는 초과 파일 누락 | 조건을 "범위 가득 참+근접 `@header {`+닫힘 없음"으로 한정하고 W-1 테스트에 경계(닫힘이 범위 직전, 닫힘이 범위 직후, 헤더 없는 대형 파일, 산문 인용) 포함 |

## Release and recovery

- 적용 순서: P1의 W-1~W-4는 변경 파일이 겹치지 않아 병렬 수행 후 통합한다. 통합 뒤 TEST 단계에서 검증한다. `~/.opal` install은 이 태스크에서 실행하지 않는다.
- 검증 범위: 결정론 — code-scan 테스트(`node --test opal/tools/code-scan/tests/`), state-tool 테스트 전건(`opal/tools/state-tool/run-tests.sh`)과 `opal/tools/oppb-runtime-tool/tests/test_pilot_isolation.py`, `test_split_surface.py`. `skill_tester.py`의 지문·드리프트 변경은 임시 디렉토리에서 `_framework_fingerprint()`·`_install_drift()`를 직접 호출해 확인(S-12). 실제 사례 측정 — 저장소 전체 `code-scan.js validate --json`(exit 0, `header_history`·`header_overflow` 0), 위반 머리말을 넣은 임시 파일로 `validate --changed` exit 2 확인, 기준 커밋과 분할본의 대표 명령(show·resolve-mode·resolve-start·init·advance·mark·verify·design-gate·event-verify) 출력 비교, 임시 디렉토리로 `tools/state-tool` 통째 복사 후 `run.sh` 방식 실행.
- 실측 경계: `validate` 전체 실행 시각은 비교하지 않는다. 출력 비교는 시각·run id·임시 경로를 정규화한 뒤 한다.
- 실패 시: 모두 소스 변경이며 배포 전이므로 해당 W의 커밋을 되돌리면 복구된다. 배포본(`~/.opal`)은 건드리지 않아 영향이 없다.
