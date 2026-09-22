# DONE: --wt 워크트리 세션으로의 태스크 소유권 이관 계약

## 결과

`--wt`로 시작한 태스크의 전용 워크트리 세션이 첫 쓰기부터 전건 차단되던 교착을 닫았다.

원인은 순서였다. 허브가 `state init` 직후 TASK 행을 mark하면서 `claim_source=state_transition`으로
lease를 선점하고, 그 뒤 기동된 워크트리 세션의 `session_start` claim이 live foreign lease를 만나
거절되는 구조였다. 실행 주체가 구조적으로 소유권을 받을 수 없었고, 해제 수단도 없었다
(`ownership-tool/run.sh`가 `not_implemented`를 반환했고 `lease.release` 호출자는 SessionEnd 훅 하나뿐이었다).
허브의 PostToolUse heartbeat가 lease를 매 턴 갱신하므로 TTL 만료로도 풀리지 않았다.

달라진 것:

- **대상 지정 이관(targeted handoff)** — lease에 `handoff_pending` 상태를 추가했다. 이관 레코드는
  소유자가 비고 `handoff_to_worktree_root`가 지정되며, 그 루트와 realpath 동치이거나 그 하위에서 온
  claim만 수용한다. 허브 재-claim과 제3자 탈취는 구조적으로 거부된다. 단순 해제 모델을 기각한 이유는
  허브가 기동 후에도 상태 전이를 계속해 수 초 내 소유를 되찾기 때문이다.
- **이관 시점은 터미널 기동 직전** — `worktree-launcher`가 `adapter.launch` 호출 직전에 1회 수행하고,
  기동 실패 5경로 전건에서 이관을 취소해 허브 소유로 원자 복귀한다. 취소 자체의 실패는 복귀를 막지 않고
  로그 필드로만 남는다. launcher는 lease 판정·쓰기를 복제하지 않고 ownership-tool CLI에 위임한다.
- **해제·조회 CLI 표면 신설** — `status` / `release` / `handoff` / `handoff-cancel` 4서브명령.
  `release`는 현 소유자에게만 허용하고 `--force` 강제 해제 표면을 만들지 않았다.
- **harness에 실행 소유권 계약 신설** — 획득·이관·해제·가드 적용 범위·저장 위치 5항목.
  이 결함의 근본 원인은 코드에만 lease가 있고 `harness/`에는 언급이 0건이라 순서 계약을 아무도
  읽을 수 없었던 것이다.
- **이관에는 짧은 만료(15분)** — 터미널이 끝내 부팅하지 않는 경로에서 태스크가 영구히 잠기지 않는다.
  만료된 이관은 무소유로 접혀 허브가 되찾는다.

유지된 것:

- PreToolUse 가드의 차단 판정을 바꾸지 않았다. 소유하지 않은 세션의 쓰기는 계속 막힌다 — 이관은
  소유권을 **옮기는** 것이지 검사를 끄는 것이 아니다.
- `classify`·`heartbeat`에 이관 분기를 추가하지 않았다. 이관 레코드는 `owner_session_id`가 비어
  기존 판정이 이미 무소유를 반환하고, 이 성질이 가드 비차단과 heartbeat no-op을 함께 성립시킨다.
- 상태 전이 도구는 획득 실패를 차단이 아니라 경고로 처리하는 fail-safe를 유지한다. 집행자는 쓰기 가드 하나다.
- `--wt` 미사용 경로의 동작과 `state.json` 산출물은 변경 전과 동일하다.
- 5개 훅의 전 경로 `except` + `exit 0` fail-safe 구조를 유지한다.

## 변경 파일

- `opal/tools/ownership-tool/ownership_tool/lease.py`
- `opal/tools/ownership-tool/ownership_tool/cli.py` (신규)
- `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`
- `opal/tools/ownership-tool/run.sh`
- `opal/tools/ownership-tool/README.md`
- `opal/tools/ownership-tool/tests/test_lease.py`
- `opal/tools/ownership-tool/tests/test_cli.py` (신규)
- `opal/tools/ownership-tool/tests/test_pretooluse_guard.py`
- `opal/tools/ownership-tool/tests/test_session_start.py`
- `opal/tools/ownership-tool/tests/test_heartbeat.py`
- `opal/tools/ownership-tool/tests/test_integration.py`
- `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py`
- `opal/tools/worktree-launcher/tests/test_launcher_core.py`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_state_tool_ownership.py`
- `opal/core/references/harness/worktree.md`
- `opal/core/references/harness/task-process.md`
- `scripts/install-mac.sh`

## 검증

RED-first: `test-tool scenario-init` 18건(`red_required` 9) → `scenario-red` 9건 기록 →
`scenario-lock`(2026-09-22T16:22:21+09:00). RED 9건은 전부 신설 API·모듈의 **부재로 인한 실패**였다
(`lease.handoff` 부재 AttributeError, `No module named ownership_tool.cli`,
`launcher_core has no attribute lease_handoff`).

시나리오 최종: `scenario-status` → `passed 18 / failed 0 / blocked 0 / awaiting_human 0`,
`scenario-fidelity-check` → `all_met: true (18/18)`.

회귀 5스위트 전건 통과·실패 0건:

- `opal/tools/ownership-tool` → `100 passed`
- `opal/tools/worktree-tool` → `147 passed`
- `opal/tools/worktree-launcher` → `117 passed, 1 skipped`
- `opal/tools/state-tool` → `556 passed, 3 skipped, 363 subtests passed`
- `scripts/tests/test_hook_parity.py` → `20 passed`

실환경 검증(배포 후):

- 배포 8파일이 소스와 byte 동일, `run.sh` 권한 `-rwxr-xr-x`, 배포본 진입점이 `not_implemented`가 아닌
  정상 JSON 반환(exit 0).
- 태스크 999로 결함 조건을 재현: 허브가 lease 선점 → `launch`가 `adapter.launch` 직전 handoff 수행
  (`status=handoff_pending`, `owner_session_id=null`, `handoff_to_worktree_root=.opal-worktrees/task_999`)
  → 워크트리 세션 `37737b1b`가 소비, registry `execution_ownership.owner_session_id=37737b1b`.
  허브가 mark 시도 시 `ownership_claim_skipped (diagnostic=foreign_owner)` 경고 1줄 후 전이만 성공하고
  소유권은 워크트리 세션에 유지됐다. 검증 후 worktree·브랜치·터미널 회수 완료.
- 배포본 PreToolUse 가드에 Write 봉투 직접 투입(env 격리): 워크트리 세션 → 무출력(허용),
  허브 세션 → `permissionDecision=deny` / `foreign_owner`. 태스크 149에서 관측된 차단 방향의 역전.
- 태스크 149 해소: 허브 세션이 `release` 실행 → 전 세션 기준 `unowned` → 149 워크트리 세션
  `818284b2`가 `state-tool advance`로 재획득(`generation` 1→2, `claim_source=state_transition`).

문서·잔존 검사: `grep -rln lease opal/core/references/harness/` → 2건.
`run.sh`·`README.md`의 미구현 서술 0건. 비-test `lease.claim(` 실호출부 2건
(`state_tool.py:757`, `session_start_hook.py:242`) 전건이 `claimant_root`를 동반한다.

## 회고적 학습 후보

.opal/brain/pages/concept/lease-handoff-before-terminal-launch.md
.opal/brain/pages/concept/contract-absent-from-harness-docs-passes-review.md
.opal/brain/pages/entity/ownership-tool.md

## 참고

- **타입 검사 미확보** — `test-tool unit`이 typecheck 레이어에서 `mypy: command not found`(exit 127)로
  중단됐다. 소유자 승인 아래 설치하지 않고 진행했다. lint 레이어는 ruff 0.15.17로 통과했고, 이번 산출
  프로덕션 소스(`lease.py`·`cli.py`·`launcher_core.py`)의 신규 지적은 0건이다. 레포에 ruff/mypy 설정
  파일이 없어 프로젝트가 집행하는 게이트가 아니다. 도구 정비는 별도 태스크 대상이다.
- **legacy 메타 한계** — registry meta에 `task_path`가 없는 legacy 워크트리는 이관 대상이 없어
  `registry_task_path_missing`으로 통과하며, 그 경로에서는 이번 결함이 그대로 남는다. 현행
  `worktree-tool create`는 항상 `task_ownership_version: 2`와 `task_path`를 발급하므로 신규 태스크에는
  영향이 없다. 경로를 cwd로 추론하면 C-4를 위반하므로 의도적 선택이다.
- **`state-tool` 스위트 6분 52초** — `test_state_tool_run_log.py::TestExistingRegressionBaseline::test_existing_suite_matches_baseline_and_frozen_files_untouched`
  단일 테스트가 198.87초(전체의 약 51%)다. 중첩 pytest로 나머지 8개 파일을 한 번 더 실행하는데, 그
  단언(`assertNotIn("failed", …)`)은 바깥 실행이 이미 증명하는 동어반복이고 자기 파일은 `--ignore`해
  자기 회귀를 잡지 못한다. 이 태스크의 AC-11이 같은 스위트 통과를 요구하므로 여기서 고치면 자기증명이
  되어 범위에서 분리했다. 별도 태스크 대상이다.
- **`scenario-coverage-build` 판단 플래그** — sdlc-v2 경로가 `is_goal_scenario`·`is_adoption_scenario`·
  `is_boundary_scenario`를 전건 `false`로 출력해 "미판정"과 "판정 결과 거짓"이 구분되지 않는다. 커버리지
  판정은 이 플래그를 읽지 않아 결과에 영향은 없으나, 파일만 읽는 사람이 오독할 여지가 있다. 별도 태스크 대상이다.
- **후속 순서** — 태스크 149가 같은 `opal/tools/ownership-tool` 파일들을 대상으로 진행 중이며, 149
  워크트리는 이 태스크의 변경을 포함하지 않은 base에서 분기했다. 이 태스크의 커밋·머지가 149의 PLAN 기준
  베이스를 확정한다.
