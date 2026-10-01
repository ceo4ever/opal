# 계획: codex `--wt` 부팅 소유권 결함의 소스 수정과 배포

## Context

태스크 162를 codex 워크트리 세션으로 기동했지만 부팅 단계에서 두 번 멈췄다. 개인 설정 수정은 이 PC만 고치는 임시 대응이다. OPAL을 설치한 다른 개발자에게도 같은 결함이 있으므로 프레임워크 소스를 고쳐 install로 배포한다.

확인된 원인은 다음과 같다(탐색 결과, 경로는 소스 기준).

1. **워크트리 세션이 허브 파일을 써야 부팅이 끝나는 설계.**
   - `codex-start`는 lease를 워크트리 안에서 획득한 뒤, `session_start_hook._register_registry_owner`(`opal/tools/ownership-tool/ownership_tool/session_start_hook.py:115-171`)로 허브 `.opal-worktrees/.meta/task_N.json`을 쓴다.
   - codex `workspace-write` 샌드박스는 워크트리 밖 쓰기를 막는다. 그런데 하네스 계약은 "권한 판정의 유일한 입력은 lease"다(`opal/core/references/harness/worktree.md:76-82`). registry는 관측 기록일 뿐인데도 그 기록 실패가 부팅 실패가 된다(`codex_adapter.py:44-47`, `cli.py:193-199`).
2. **권한 거부를 잠금 경합으로 오보.**
   - `worktree_tool.py:934-959` `_acquire_registry_lock`과 `ownership_core.py:157-163` `_acquire_lock`은 `os.open`의 모든 `OSError`(EPERM 포함)를 재시도한다. 그래서 30초 뒤 `registry_lock_timeout`이 난다.
   - 에이전트는 권한 상승이 필요하다는 사실을 알 수 없다.
3. **launcher의 거짓 성공.**
   - `launcher_core.py:414-481`은 Orca가 exit 0이면 곧바로 `ownership-set worktree_session_owned --owner-from-lease`를 호출한다.
   - lease가 아직 `handoff_pending`이어도 owner 없이 성공 처리하고(`worktree_tool.py:1957-1964`), 자식 세션의 생존과 lease 획득은 확인하지 않는다.
   - 이후 실패는 수동 복구(`handoff-cancel` + `ownership-set --generation N+1`)가 필요했다.
4. **Orca×codex 소켓 경로 길이.**
   - codex app-server 데몬 소켓이 `SUN_LEN`을 넘어 즉시 종료된다.
   - launcher codex 기본 argv(`worktree_launcher/settings.py:38`, `opal/core/setting.default.json:12-20`)에 `--no-daemon`이 없다.

## 방향(원칙)

- 워크트리 세션은 **자기 워크트리 안 쓰기만으로 부팅을 끝낸다.** 허브 registry 전이는 허브(launcher)가 lease를 관측해 확정한다. 계약상 이미 "최종 registry 전이는 `--owner-from-lease` 경유"(`worktree.md:284-292`)이므로 그 계약을 실제로 성립시킨다.
- 샌드박스 권한 거부는 즉시 구분된 오류로 보고한다. 에이전트가 상승 요청이나 중단을 올바르게 판단하게 하기 위해서다.
- 플랫폼 분기(codex 전용)는 bootstrap·launcher 설정·install 어댑터 계층에만 둔다.

## 실행 방식

- 새 `//opd` 태스크(163 예정)로 수행한다. 수행 세션은 Claude(이 허브 세션 → 워크트리)다. codex는 이 결함 때문에 아직 쓸 수 없다.
- 162는 이 수정의 배포 뒤 codex로 재기동한다.
- **162 현재 상태(2026-09-27 재확인)**
  - Orca 터미널 `term_43caeb86…`은 connected 상태이고, codex 프로세스(PID 51444)가 부팅 중단 뒤 대기 화면으로 살아 있다.
  - lease는 기록상 `active`이고 owner는 codex 세션 `01a0dfe4…`인데, `lease_expires_at` 11:45가 지나 만료 판정이다.
  - registry는 `worktree_session_owned`, owner null이다.
  - **lease 만료만으로 자식 종료를 추정하지 않는다.**
- **162 복구 순서.** 각 단계의 확인이 실패하면 다음 단계로 가지 않고 멈춘다.
  1. 기존 터미널을 정확한 handle로 종료한다(`worktree-launcher close --adapter orca --terminal term_43caeb86…`).
  2. 종료를 확인한다. `orca terminal show --terminal term_43caeb86… --json`이 `terminal_handle_stale`이고, `orca terminal list --worktree path:<task_162 worktree> --json`에 그 handle이 없으며, codex 프로세스(PID 51444)가 없어야 한다. 셋 중 하나라도 확인되지 않거나 조회가 다른 오류로 실패하면 중단한다. 이 단계는 수정 배포 전 수동 절차이며, 배포 뒤에는 새 `status` 동사와 같은 판정이다.
  3. lease와 registry를 다시 조회한다(`ownership-tool status`, registry meta). 만료나 무소유이고, 다른 live 세션 소유가 없음을 확인한다.
  4. 그 뒤에만 registry를 `hub_owned`로 전이한다(generation 증가).
  5. 수정 배포 뒤 새 launcher로 재기동한다.
- 태스크 161(test-tool)과는 파일이 겹치지 않는다.

## 변경 내용

1. **launcher의 lease 획득 확인** — `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py`
   - 이 확인은 "자식 세션의 lease 획득"만 보장한다. 자식의 생존이나 작업 준비 완료를 증명한다고 표현하지 않는다(응답·문서 문구 포함).
   - prompt receipt 확인과 최종 `ownership-set` 사이에서 `_lease_cli("status")`(기존 :372 호출 재사용)를 bounded polling한다.
   - lease가 허브 세션이 아닌 세션 소유(`foreign_session_owned`, owner ≠ launcher 세션 ID)가 되면 최종 전이를 호출한다.
   - launcher는 최종 전이를 `ownership-set worktree_session_owned --owner-from-lease --expected-owner <polling에서 관측한 lease owner> --exclude-owner <launcher 세션 ID>`로 호출한다(3의 원자 비교).
     - 도구가 불일치로 거부하면 registry는 `session_launching`에 그대로 남는다. launcher는 아래 2의 실패 경로(`created`)로 간다. 2의 1단계(close 전 늦은 claim 판정)는 이 경우 **재시도하지 않는다**. 관측 owner가 바뀌는 상황을 반복 추격하지 않고, 불확실 상태로 보고 종료 확인 → `hub_owned` 또는 `recovery_required`로 판정한다.
     - 도구가 성공하면 반환 owner는 도구 계약상 기대 owner와 같다. launcher는 이를 사후 단언으로 확인한다. 다르면 전이 없이 `LauncherError(ownership_postcondition_violated)`를 올린다. 도구 계약 위반을 조용히 복귀로 덮지 않는다.
   - 대기 상한은 launcher 설정 키로 두되 코드 기본값을 갖는다.
2. **시간 초과 복구의 경쟁 상태 제거** — `launcher_core.py` `_revert`(:287-333)
   - `_revert`에 `failure_reason` 인자를 추가한다. 기존 호출은 `launch_failed`를 유지하고, 부팅 시간 초과는 `session_boot_timeout`을 넘긴다. 응답의 `failure_reason`(:323)도 인자값을 쓴다.
   - **시간 초과·실패 경로의 순서.** 단계 순서를 바꾸지 않는다.
     1. **늦은 claim 판정 — 터미널을 닫기 전.** lease를 마지막으로 조회해 허브 외 세션이 소유하고 있으면 복귀하지 않고 1의 최종 전이(성공 경로)로 합류한다. 터미널을 닫은 뒤 발견한 lease는 성공 세션으로 확정하지 않는다. 종료된 자식을 owner로 기록하게 되기 때문이다.
     2. **터미널 종료와 확인 — 터미널 생성 상태에 따라 분기.** `_revert` 호출자가 `terminal_creation`을 명시해 넘긴다.
        - `not_created`: `adapter.launch`를 호출하기 전 실패(:409 `lease_handoff_failed`). 종료 확인은 **해당 없음**으로 통과하고 3·4로 간다. 3에서 handoff 결과가 예외나 불명이면 lease를 재조회한다. 이 세션이 만든 `handoff_pending`이 보이면 cancel 성공을 요구한다.
        - `created`: report에서 handle을 얻은 경우(:431·:440·:447 중 handle 있음, :463, 부팅 시간 초과). close 성공 + `status(handle) == absent`를 요구한다.
        - `unknown`: 생성 여부나 handle을 알 수 없는 경우(:419 `adapter.launch` 예외, :423 report 비정상, :431·:440·:447 중 handle 없음). 종료를 확인할 수 없으므로 **`hub_owned`로 복귀하지 않고** `recovery_required`(`terminal_creation=unknown`)로 간다.
        - 호출 7곳 각각에 어느 분류를 넘기는지 코드에 명시하고, 분류 누락은 `unknown`으로 기본 처리한다(fail-safe).
     3. **이관 취소 — 실제로 시작된 이관에만.** launch 시 `handoff` 응답이 이관을 기록했으면(noop 아님) handoff-cancel 성공을 요구한다. `handoff`가 `no_live_lease` noop이었으면(`lease.py:276`) 취소할 이관이 없으므로 cancel을 호출하지 않는다. 이 경우 `not_handoff_owner`를 실패로 세지 않는다.
     4. **lease 재조회.** 허브 외 live 소유가 없어야 한다. 2 뒤에 lease가 허브 외 세션 소유로 보이면, 그 세션은 종료가 확인된 자식이다. 성공으로 확정하지 않고 불확실 상태로 분류한다(lease가 만료될 때까지 허브 쓰기도 막히므로).
   - **`hub_owned` 복귀 조건.** 2가 확인(`created`)되거나 해당 없음(`not_created`)이고, 3이 성공이거나 해당 없음이며, 4에서 허브 외 live 소유가 없을 때만 `hub_owned`(`failure_reason`=`launch_failed`|`session_boot_timeout`)로 복귀한다.
   - 하나라도 확인할 수 없으면 **`hub_owned`로 전이하지 않고** 새 상태 `recovery_required`로 전이한다. 대상은 close 실패·거부·미지원, handle 조회 불가·잔존, 시작된 이관의 cancel 실패, 재조회 실패, 종료 뒤 허브 외 lease다. 응답은 ok:false, `error=launch_recovery_required`이고, 미확인 항목·terminal handle·lease 상태를 담는다.
   - 기존 `_close_terminal`·`_cancel_lease_handoff`가 실패를 삼키는 동작(:233-285)은 로그 수집용으로 유지한다. 대신 그 반환값을 위 판정 입력으로 쓴다. "복귀는 정리 성공에 종속되지 않는다"는 `_revert` docstring 계약(:297-305)은 이 조건으로 교체한다.
2-2. **adapter 터미널 존재 확인 동사** — `opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py`(현재 `launch`·`read`·`close`만 있음), adapter seam 문서와 conformance 테스트
   - 새 동사 `status(handle)`와 `status_worktree(worktree_root)`는 각각 3값 중 하나를 반환한다: `present` / `absent` / `unknown`(사유 포함). `status_worktree`의 `absent`는 "그 worktree의 live 터미널 0개"를 뜻한다.
   - Orca 구현은 `orca terminal show --terminal <handle> --json`을 쓴다. 판정은 다음과 같다(2026-09-27 이 PC 실측).
     - 존재하는 handle은 `ok:true`와 `result.terminal`(`ptyId`·`incarnationId`·`orphaned` 등)을 반환한다 → `present`.
     - 존재하지 않는 handle은 `ok:false`, `error.code: terminal_handle_stale`, exit 1을 반환한다.
     - `absent`는 `terminal_handle_stale` 오류 코드와 보조 확인(`orca terminal list --worktree path:<worktree_root> --json`에 같은 handle·`ptyId`가 없음)이 **둘 다** 성립할 때만 판정한다.
     - `unknown`: orca 미설치, 비-0 종료이지만 코드가 다른 경우, JSON 파싱 실패, runtime 응답 없음, list 실패, show는 stale인데 list에 남아 있는 경우. **조회 실패를 부재로 오인하지 않는다.**
   - 2의 "터미널 종료 확인"과 `recover`는 `status == absent`일 때만 확인 성립으로 본다. `unknown`은 미확인이며 `recovery_required`로 간다.
   - 이 동사를 구현하지 않은 adapter(cmux, generic, opal_agent_fallback)는 `status`를 `unknown`(`status_unsupported`)으로 취급한다. 그런 adapter로 기동한 태스크의 실패 경로는 `hub_owned`가 아니라 `recovery_required`가 된다.
     - cmux에서 같은 동사를 구현할 수 있는지는 PLAN에서 CLI 지원을 확인하고 결정한다.
     - 구현 가능하면 같은 태스크에 포함하고, 아니면 미지원 근거와 이 동작을 README에 남긴다.
2-1. **복구 상태 `recovery_required` 도구 계약** — `worktree_tool.py`
   - `ALLOWED_OWNERSHIP_COMBOS`에 `(recovery_required, active)`를 추가한다. `failure_reason` 허용 규칙(:1899-1908, 현재 `hub_owned` 복귀만 허용)을 `hub_owned` 복귀 **또는** `recovery_required` 전이로 확장하고, 오류 사유 문구를 갱신한다.
   - 허용 전이는 두 가지뿐이다: `session_launching → recovery_required`, 그리고 `recovery_required → hub_owned`(복구 명령 경유). `recovery_required → session_launching·worktree_session_owned` 직행은 거부한다.
   - launcher는 이 상태를 `hub_owned`·`session_launching` 외 상태로 보고 기존 거부 분기(:391-399, `ownership_not_launchable`)로 재진입을 막는다. 새 분기는 만들지 않는다.
   - 복구 명령: `worktree-launcher recover --adapter … --project-root … --task …`를 추가한다. 위 2~4 확인을 다시 수행하고, 모두 확인될 때만 `hub_owned`로 전이한다. 확인에 실패하면 상태를 바꾸지 않고 미확인 항목을 반환한다.
   - **복구 입력 보존.** 현재 `ownership-set`은 `failure_reason`이 있으면 owner·`adapter_handle`·`launch_receipt`·`prompt_receipt`를 모두 지운다(:1981-1986, orphan owner 금지 C-13).
     - 이 소거는 `hub_owned` 복귀에만 적용한다.
     - `recovery_required` 전이에서는 `adapter`·`adapter_handle`·`launch_receipt`·`prompt_receipt`를 보존한다. 추가로 판정 시점에 관측한 lease owner를 별도 필드(예: `observed_lease_owner`)로 기록한다. 이 필드는 registry owner가 아니며 `owner_session_id`는 `None`을 유지한다(C-13 유지).
     - `recovery_required` 전이에 `terminal_creation`(`created`|`unknown`)을 함께 기록한다.
     - `recover`는 별도 인자 없이 registry 보존값만으로 확인 대상을 정한다.
       - `created`와 보존된 `adapter_handle`이 있으면 `status(handle) == absent`를 요구한다.
       - `unknown`이면 handle 대신 registry가 발급한 `worktree_root`로 worktree 단위 조회를 한다(adapter 동사 `status_worktree(worktree_root)`, Orca는 `orca terminal list --worktree path:<worktree_root> --json`). list가 성공하고 그 worktree의 live 터미널이 0개일 때만 확인 성립이다. list 실패나 파싱 실패는 `unknown`이고, 터미널이 1개 이상 있으면 확인 불가다. 태스크 전용 worktree이므로 사용자 탭 식별은 추론하지 않고, 남은 터미널이 있으면 안전 쪽(복구 보류)으로 판정한다.
       - `recovery_input_missing`은 `adapter`와 `worktree_root`가 모두 없거나 손상된 경우로 한정한다. 이때 상태는 불변이다.
     - `recover`가 `hub_owned`로 전이할 때 위 보존값을 소거한다.
   - 소비자 전수 갱신: registry 상태를 열거하거나 분기하는 곳을 PLAN에서 목록화하고 영향 있음/없음 근거를 남긴다. 예: `worktree-tool status`·`remove` 가드, canonical path 해석, ownership-tool `session_start_hook` 부트 등록 조건(:138-145), 허브 브리핑·console. 대상 문서는 `worktree.md` §실행 소유권, worktree-tool·launcher README, registry 스키마(`opal/tools/worktree-tool/schema/`)다.
3. **최종 전이 도구의 owner 필수화** — `worktree_tool.py` `cmd_ownership_set` `--owner-from-lease`(:1957-1964)
   - 유효한 lease owner가 없으면 `owner_session_id=None`으로 성공하던 동작을 거부(`owner_lease_unresolved`)로 바꾼다. 유효하지 않은 경우는 lease가 `handoff_pending`·만료·부재이거나, 판정 불가인 경우다.
   - 인자 두 개를 추가한다. `--owner-from-lease`와 함께 쓸 때 둘 다 필수다.
     - `--expected-owner <sid>`: registry lock 안에서 lease를 읽은 뒤, 아래 조건이 모두 성립할 때만 쓴다. 조건 불충족은 `owner_lease_mismatch`(실제 lease owner·상태 동봉)로 **registry를 쓰기 전에** 거부한다. 거부 시 registry의 state·generation·필드는 불변이다.
       - lease가 live 소유다(`handoff_pending`·만료·부재가 아님).
       - lease owner가 기대값과 같다.
       - lease owner가 제외값과 다르다.
     - `--exclude-owner <sid>`: launcher 세션 ID다. lease owner가 이 값이면 거부한다. `classify(record, None)`만으로는 허브 자신의 lease도 통과하기 때문이다.
   - 이로써 "최종 전이 성공 = registry owner가 launcher가 관측한 자식 lease owner와 같다"가 도구에서 원자적으로 보장된다. 성공 뒤 불일치로 인한 `worktree_session_owned` 고착 경로가 사라지므로, `worktree_session_owned → recovery_required` 전이는 추가하지 않는다.
   - 이 동작 변경에 기대던 기존 호출자(launcher :452-466, README의 "pending이면 owner 비움" fallback)를 전수 갱신한다.
4. **registry 기록 실패의 비치명화** — `session_start_hook.py`, `codex_adapter.py`
   - 비치명 대상은 **lease 획득 성공 + registry 쓰기의 권한 거부(`registry_write_denied`)** 하나로 한정한다. 이때 `ok:true`와 진단 `registry_owner_deferred_to_hub`를 반환한다. 허브 launcher가 3의 경로로 owner를 확정한다.
   - `foreign_registry_owner`, 그 외 `ownership_set_failed`, lease 미획득은 계속 ok:false다.
   - `README.md:259`의 "nonzero 진단" 문구를 이 분류로 갱신한다.
5. **권한 거부 즉시 구분**
   - `worktree_tool.py` `_acquire_registry_lock`/`registry_lock`과 `write_meta_atomic` 경로: `PermissionError`/EACCES/EPERM/EROFS를 재시도하지 않고 `registry_write_denied`로 즉시 반환한다.
   - `ownership_core._acquire_lock`에도 같은 규칙을 적용한다.
6. **codex bootstrap 문구** — `opal/bootstrapper/codex-bootstrap.md:24-29`
   - codex-start의 `ok`만 판정 입력으로 쓴다. 비치명 분류는 4가 도구 안에서 소유하고, bootstrap에 조건을 복제하지 않는다.
   - `ok:false`면 중단한다. 여기에는 `foreign_registry_owner`와 lease 미획득이 포함된다. "registry 진단과 무관하게 진행" 같은 문구는 쓰지 않는다.
   - 워크트리 밖 쓰기가 필요한 OPAL 명령(7 결과)이 `registry_write_denied`나 권한 오류를 내면 codex의 권한 상승 요청으로 재실행한다.
7. **워크트리 세션의 허브 쓰기 전수 확인**
   - `worktree-tool checkpoint`는 허브 `.git` 공통 디렉터리와 meta `checkpoint_shas`를 쓴다. 이 경로를 codex 샌드박스에서 실측한다.
   - 막히면 둘 중 하나로 처리하고 PLAN에 근거를 남긴다.
     - (a) meta 기록을 허브 측 확정(finalize/status)으로 이관한다.
     - (b) bootstrap에 권한 상승 경로를 명시한다.
8. **`--no-daemon` 기본값과 기존 사용자 이관**
   - `settings.py` 코드 기본값과 `setting.default.json`의 codex argv에 `--no-daemon`을 넣는다.
   - 지원 근거: 이 PC의 codex-cli 0.157.1 `codex --help`에서만 확인했다. 공식 문서에서 최소 지원 버전은 확인하지 못했다.
   - 검증 조건: 최소 지원 버전을 확인하거나, 미지원 버전에서의 동작을 실측한다. 미지원 버전에서 알 수 없는 인자로 즉시 종료하면 1·2의 부팅 확인이 `session_boot_timeout`으로 자동 복귀시키는지 테스트로 고정하고, 설치 안내에 codex 버전 요건을 명시한다.
   - install(`scripts/install-mac.sh` `install_opal_setting` :1157-1223, Windows `scripts/install/windows.ps1` 대응 함수)에 이관 로직을 넣는다. 기존 `launcher.agents.codex.argv_template`이 **구 기본값과 정확히 같을 때만** 새 값으로 올리고, 사용자 수정값은 보존한다. 기존 codex 모델 업그레이드 로직(:1188-1204) 패턴을 재사용한다.
9. **문서**
   - `opal/core/references/harness/worktree.md` §실행 소유권·Codex identity 절: 허브 확정 흐름, 부팅 확인, 권한 거부 오류를 반영한다.
   - `docs/ARCHITECTURE.md:550-556`
   - worktree-tool·worktree-launcher·ownership-tool README

## 테스트

- worktree-tool (`opal/tools/worktree-tool/tests/test_worktree_tool.py`)
  - lock 파일 `os.open`이 PermissionError면 즉시 `registry_write_denied`를 반환한다(재시도·30초 대기 없음).
  - `--owner-from-lease`: 유효 owner가 있고 `--expected-owner`와 같으면 기록한다. 다음은 모두 거부이고, 거부 시 registry의 state·generation·필드는 바이트 단위로 불변이다.
    - pending·만료·부재 → `owner_lease_unresolved`
    - live owner가 기대값과 다름 → `owner_lease_mismatch`
    - owner가 `--exclude-owner`와 같음 → 거부
    - `--expected-owner`·`--exclude-owner` 누락 → 인자 오류
- worktree-launcher 최종 전이
  - 원자 비교 거부 시 registry는 `session_launching`에 남는다.
  - launcher는 늦은 claim 재판정 없이 실패 경로로 간다. 종료가 확인되면 `hub_owned`, 확인되지 않으면 `recovery_required`다.
  - polling 뒤 lease owner가 바뀐 경우: 최종 전이가 거부되고 두 번째 owner로 재시도하지 않는다.
  - 도구가 성공했는데 반환 owner가 다른 가짜 응답 → `ownership_postcondition_violated`이고, 추가 전이 호출은 0회다.
- ownership-tool (`tests/test_session_start.py`, `tests/test_codex_identity.py`)
  - lease 획득 + registry 권한 거부 → codex-start ok:true와 진단.
  - foreign owner → 여전히 실패.
- worktree-launcher (`tests/test_launcher_core.py`, 기존 `_FakeAdapter`·`_lease_cli` monkeypatch 패턴)
  - 자식이 기한 내 claim하면 실제 owner가 기록되고, 응답 owner와 관측 owner가 일치한다.
  - 최종 전이 응답 owner가 비었거나 불일치하면 ok를 반환하지 않는다.
  - claim이 없으면 timeout 뒤 `hub_owned`, `failure_reason=session_boot_timeout`, ok:false이고 터미널이 close된다. 이관을 시작한 경우와 `no_live_lease` noop인 경우 두 가지를 모두 검증한다. noop이면 cancel 호출이 0회이고 복귀가 성공한다.
  - **늦은 claim(close 전)**: polling 기한 뒤, close 전 마지막 조회에서 자식이 소유하면 close 호출 0회이고 자식 owner로 확정된다.
  - **close 뒤 발견된 lease**: close와 handle 부재 확인 뒤 재조회에서 허브 외 lease가 보이면 성공으로 확정하지 않는다. `recovery_required`이고 `hub_owned` 전이 0회다.
  - **불확실한 상태에서는 허브 소유로 복귀하지 않는다.** 아래 각 경우에 registry는 `recovery_required`, ok:false, `error=launch_recovery_required`이고 `hub_owned` 전이 호출이 0회다.
    - 터미널 close 실패·거부·미지원
    - close 성공이지만 handle이 여전히 존재
    - 시작된 이관의 handoff-cancel 실패
    - lease 재조회 실패
  - `recovery_required`에서 launch를 다시 호출하면 `ownership_not_launchable`로 거부되고 새 터미널이 열리지 않는다.
  - `recover`: 확인이 모두 성공하면 `hub_owned`로 전이한다. 하나라도 실패하면 상태는 불변이고 미확인 항목을 반환한다.
- Orca adapter `status` (`tests/test_adapter_orca.py`, `tests/test_adapter_conformance.py`, subprocess fake 패턴)
  - `show` ok → `present`
  - `show` `terminal_handle_stale` + `list`에 없음 → `absent`
  - `show` stale인데 `list`에 남아 있음 → `unknown`
  - orca 미설치, 기타 오류 코드, JSON 파싱 실패, `list` 실패 → 각각 `unknown`. `absent`로 판정되지 않는다.
  - `status` 미구현 adapter → `unknown(status_unsupported)`이고 실패 경로가 `recovery_required`다.
- 복구 입력 보존
  - `recovery_required` 전이 뒤 registry에 `adapter_handle`·receipt·`observed_lease_owner`가 남고, `owner_session_id`는 `None`이다.
  - 인자 없는 `recover`가 보존된 handle로 `status`를 호출한다.
  - 보존값이 없으면 `recovery_input_missing`이고 상태는 불변이다.
  - `recover` 성공 시 `hub_owned`로 전이하고 보존값을 소거한다.
- 터미널 생성 상태별 복귀(`_revert` 호출 7곳 각각)
  - `:409` `lease_handoff_failed`(`not_created`): close·status 호출 0회, lease 확인 뒤 `hub_owned`로 복귀한다. handoff가 예외를 낸 뒤 lease에 이 세션의 `handoff_pending`이 남아 있으면 cancel 성공을 요구하고, cancel이 실패하면 `recovery_required`로 간다.
  - `:419` launch 예외, `:423` report 비정상, handle 없는 receipt 실패(`unknown`): `hub_owned` 전이 0회, `recovery_required(terminal_creation=unknown)`로 간다.
  - handle 있는 receipt 실패, `:463` 최종 전이 실패(`created`): close + `status == absent`일 때만 `hub_owned`로 복귀한다.
  - `unknown` 상태의 `recover`: worktree list가 0개면 `hub_owned`로 복귀한다. 1개 이상이거나 list가 실패하면 상태는 불변이다.
  - 분류 인자를 누락한 호출은 `unknown`으로 처리된다.
- worktree-tool 추가
  - `(recovery_required, active)` 허용.
  - `failure_reason`이 `recovery_required` 전이에서 허용된다.
  - 금지 전이(`recovery_required → session_launching·worktree_session_owned`)가 거부된다.
  - 기존 `_revert` 호출 경로의 `failure_reason=launch_failed`가 유지된다.
  - 기존 :809 사례가 회귀하지 않는다.
- installer (`scripts/tests/test_agent_adapter_fields.sh` 패턴)
  - 구 기본값은 이관된다.
  - 사용자 수정값은 보존된다.
  - 신규 설치는 새 기본값을 쓴다.

## 검증(end-to-end)

1. 소스 테스트 3종(pytest)과 installer bash 테스트가 통과한다.
2. 정식 install(`scripts/install-mac.sh`)로 배포한 뒤, 배포본 `~/.opal/tools/*`에서 변경 진입점을 확인한다.
3. 실측 1(실패 경로): 존재하지 않는 명령으로 launch하면 ok:false, `session_boot_timeout`, 자동 `hub_owned` 복귀가 된다. 수동 복구가 없어야 한다.
4. 실측 2(성공 경로): 162를 Orca + codex로 재기동한다.
   - codex-start가 ok다.
   - lease가 codex 세션 소유이고, registry owner가 codex 세션 ID다.
   - codex가 PLAN 행을 🔄로 전환한다.
   - 이 PC의 개인 codex 설정은 수정하지 않은 상태에서 확인한다.
5. 실측 3: codex 세션의 첫 `worktree-tool checkpoint`가 성공하거나 설계한 경로로 처리된다. 162 진행 중 관측한다.
