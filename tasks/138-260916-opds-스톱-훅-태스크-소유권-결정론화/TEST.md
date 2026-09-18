# TEST — `--wt` 전용 세션·Stop 훅 태스크 소유권 결정론화 (138)

> TEST 단계 산출물. mode: BE. 실행 환경: 워크트리 `feat/OP-TASK-138`
> (`/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_138`).
> 허브(`/Volumes/Data/AIStudio/workspace/ai-framework`)는 읽기만 했다 — 작업 전후
> `git status --porcelain | wc -l` = 42 (변화 없음, 이 워커 소행 0건).

## 1. 스위트 실행 결과 (5종, 병렬 규칙 준수)

캡틴 지시대로 스위트별 호출을 분리해 동시에 띄웠다. state-tool·worktree-tool을
먼저 백그라운드로 띄우고, 그 사이 빠른 3종(ownership-tool·worktree-launcher·
scripts/tests)을 포그라운드로 돌렸다.

| 스위트 | 명령 | 결과 | 실측 소요 |
|---|---|---|---|
| ownership-tool | `~/.opal/.venv/bin/python -m pytest opal/tools/ownership-tool/tests -q` | **56 passed** | 4.33s |
| worktree-tool | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests -q` | **135 passed** | 103.30s (백그라운드) |
| worktree-launcher | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-launcher/tests -q` | **15 passed** | 1.08s |
| state-tool | `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests -q` | **535 passed, 3 skipped** | 322.56s (백그라운드) |
| scripts/tests | `~/.opal/.venv/bin/python -m pytest scripts/tests -q` | **1 failed, 20 passed** | 0.69s |

추가로 S-7/S-8/S-9/S-11/S-26 매핑을 위해 개별 파일 3종을 재확인 실행했다:
`~/.opal/.venv/bin/python -m pytest scripts/tests/test_hook_parity.py scripts/tests/test_merge_hooks.py opal/tools/state-tool/tests/test_state_tool_ownership.py -v`
→ **22 passed** (hook_parity 10 + merge_hooks 9 + state_tool_ownership 3).

### scripts/tests 유일 실패 — 범위 밖 판정 근거

`test_task113_bootstrap_contract.py::test_source_audit_passes` —
`event_contract_missing: worker.dispatch, path=.../opal-agents/opal-capability-agent/AGENT.md`.
`opal-capability-agent/AGENT.md`는 이 태스크(138)가 변경한 파일이 아니며
(`ownership-tool`/`worktree-tool`/`worktree-launcher`/`state-tool`/hook 계열
외 파일 미수정), main 브랜치에 이미 존재하는 결함이다. PM이 디스패치 전
사전 확인한 수치(1 failed/20 passed)와 본 세션 재확인 수치가 완전히 일치한다.
**코드 수정 금지 지시에 따라 고치지 않았다.**

## 2. 시나리오 ↔ 증거 매핑표 (S-1~S-29)

| ID | 판정 | 증거 |
|---|---|---|
| S-1 | **pass** | `test_stop_evaluator.py::test_s1_hub_fossil_ambiguous_not_forced_block_continue` |
| S-2 | **pass** | `test_stop_evaluator.py::test_s2_closed_attribution_state_hub_canonical_block_continue` |
| S-3 | **pass** | `test_resolver.py::test_s3_worktree_resolver_returns_single_canonical_candidate` + `test_s3_invalid_registry_json_classified_invalid_registry` + `test_s3_no_filesystem_scan_in_resolver_source` |
| S-4 | **pass** | `test_resolver.py::test_s4_resolve_hub_excludes_foreign_session_owned_from_forced_candidates` + `test_s4_classify_allows_two_leases_for_same_session` + `test_lease.py::test_s4_two_leases_same_session_both_current_session_owned` |
| S-5 | **pass** | `test_stop_evaluator.py::test_s5_hub_multi_defer_to_pm` |
| S-6 | **pass** | `test_stop_evaluator.py::test_s6_repeat_stop_fingerprint_variants`(3변형) + `test_s6_block_cap_reached` + `test_fingerprint.py::test_fingerprint_stable_across_note_and_runlog_only_changes` |
| S-7 | **pass** | `scripts/tests/test_hook_parity.py`(10 passed) — `grep 'python -c'│OPAL_TASK_PATH│ADD-3' opal/core/hooks/claude-hooks.json` = 0건, `claude-hooks.json:70`이 `stop_hook.py` 직접 호출만 수행. evaluator standalone import는 ownership-tool 56 passed(훅 미개입 단위테스트)로 방증 |
| S-8 | **pass** | `scripts/tests/test_merge_hooks.py`(9 passed) + `test_hook_parity.py::test_project_and_worktree_settings_untouched` |
| S-9 | **pass** | `test_hook_parity.py::test_installed_event_set_matches_source` + `test_n_redeploys_byte_identical` + `test_retired_commands_are_reclaimed_not_reinserted` + `test_non_opal_hooks_preserved` + `test_installer_targets_home_settings_only` |
| S-10 | **pass** | `test_session_start.py::test_s10_worktree_cwd_claims_lease_and_registers_session` + `test_s10_hub_cwd_creates_zero_leases` + `test_s10_missing_env_file_is_fail_safe_exit0` |
| S-11 | **pass** | `opal/tools/state-tool/tests/test_state_tool_ownership.py::TestS11OwnershipSessionIntegration`(3 tests) + state-tool 535 passed/3 skipped/0 failed(`ALLOWED_TRANSITIONS`·`_derive_transition`·`cmd_block` 회귀 유지) |
| S-12 | **pass** | `test_lease.py::test_s12_heartbeat_updates_expiry_for_owning_session` + `test_s12_heartbeat_from_foreign_session_is_noop` + `test_s12_release_marks_status_released` + `test_s12_ttl_expiry_classified_lease_expired` |
| S-13 | **pass**\* | `test_session_start.py::test_s13_foreign_session_claim_rejected` + `test_pretooluse_guard.py::test_foreign_owner_blocks_edit_and_git_commit`/`test_foreign_owner_allows_read_and_ls_with_diagnostic`/`test_outside_registered_worktree_exits_immediately_no_io` + `test_integration.py::test_same_worktree_two_sessions_guard_blocks_then_unblocks_after_release`. **\*단서**: "Stop → 비차단 통과(진단 `foreign_owner`)" 전용 단정 테스트는 미발견 — `test_resolver.py::test_s4_resolve_hub_excludes_foreign_session_owned_from_forced_candidates`(강제 후보 제외 메커니즘 동일)로 구조적 방증만 가능 |
| S-14 | **pass** | `test_worktree_tool.py::TestOwnershipSetRed`(5 tests: allowed_combo/opaque_receipt/receipt_registry_type/forbidden_combo/legacy_meta) |
| S-15 | **pass** | `test_launcher_core.py`(5 tests: success_path/launch_failed/prompt_failed/cwd_mismatch/no_dual_owner_or_orphan) |
| S-16 | **pass** | `test_adapter_orca.py::test_orca_launch_invokes_expected_argument_shape` + `test_orca_absent_returns_failure_no_fallback` + `test_prompt_receipt_missing_falls_back_to_sessionstart_claim_observation` |
| S-17 | **pass** | `test_adapter_generic.py`(4 tests: substitutes_template_placeholders_only/source_has_zero_os_name_branches/opal_agent_fallback_launch/fallback_reported_cwd_mismatch) |
| S-18 | **pass** | `test_worktree_tool.py::TestCreateSettingsProvisioningRed`(3 tests: permissions_only/hooks_present_rejected/missing_settings_file_noop) |
| S-19 | **pass** | `test_worktree_tool.py::TestCheckpointRed`(4 tests: commits_owned_scope/scope_violation/mode_denied/forbidden_git_command) |
| S-20 | **blocked** | 매핑 불가 — "검증 실패→보정→재검증 통과" 재시도 시퀀스 전용 테스트 미발견(`TestCheckpointRed`는 4건뿐, retry 관련 0건; worktree-tool·state-tool 전체 grep으로도 미발견) |
| S-21 | *(미마킹)* | e2e profile=manual — 아래 §3 참조 |
| S-22 | **pass** | `git diff main -- opal/skills/opal-pilot-dev/references/pipeline.json pipeline-short.json`: CLOSE 행 12-16/17-21 key·순서·개수 무변경, `close.worktree_finalize` item 문구만 "허브 수행" 추가, `close_final_key`/`semi_agentic_boundary` 무변경 + state-tool 535 passed(해당 `pipeline.json`을 `--rows-from`으로 쓰는 기존 테스트 다수, `test_state_tool.py:642/827/1855/1912/2041/2095`) |
| S-23 | **pass** | ownership-tool 56 passed + worktree-launcher 15 passed(전건 pass) + `grep -rn "subprocess\.(run|Popen|call)"` 두 tests 디렉터리 전체 = 0건 |
| S-24 | **fail** | scripts/tests 1 failed/20 passed(범위 밖 선존 결함, §1 참조) — state-tool·worktree-tool은 전건 pass이나 "전건 pass" 문구 기준 미충족 |
| S-25 | *(미마킹)* | e2e profile=manual — 아래 §3 참조 |
| S-26 | **pass** | `grep 'def _is_owned' scripts/merge-hooks.py`→`:24` 존재, `def merge_hooks(target_settings, source_hooks, retired_hooks=None)` 3-인자(`:37`) + `test_merge_hooks.py` 9 passed(마커 유실 관련 `test_marker_stripped_duplicates_collapse`·`test_marker_stripped_idempotent_byte_identical`·`test_retired_only_event_is_cleaned` + `test_hook_parity.py::test_n_redeploys_byte_identical_after_marker_loss`) |
| S-27 | **pass** | 정적 경로 분석: `ownership_core.py:47` `hub_lease_path`→`<task_path>/run/.runtime/owner.json`(`.gitignore:49` `tasks/**/run/.runtime/` 커버), `ownership_core.py:50-51` `stop_receipt_path`→`<project_root>/.opal/run/.runtime/stop-guard/<sid>.json`(`.gitignore:2` `.opal/*` 커버), `session_registry.py` 세션 registry→`<project_root>/.opal/run/.runtime/sessions/<sid>.json`(`.opal/*` 커버). `git status --porcelain`에 `.gitignore` 미등장=무변경 |
| S-28 | **pass** | `test_decisions.py::test_decision_kinds_enum_has_exactly_seven_members` + `test_diagnostics_enum_is_closed_member_set` + `test_schema_validator_rejects_values_outside_enum` + `test_distinct_decision_kinds_for_distinct_states` |
| S-29 | **pass**\* | `fixtures/hook-payloads/*.json`(5종, `_fixture.captured:false`—필드 부재 여부 기록됨) + `ENV-CAPTURE.md`(서브에이전트 Bash 실측: `OPAL_SESSION_ID` unset, `CLAUDE_ENV_FILE` unset) + `AGENTIC-LOG.md` #21·#22(부재 수용·fail-safe 전환 결정 기록) + 대체 검증 S-10/S-11/S-12 전건 pass. **\*단서**: "132 shadow 1회 비차단 실관측"(항목4)은 실제 설치·라이브 세션이 필요해 W-20 §3·§4 수동 절차로 이관되었고 이 TEST 실행(격리 pytest 환경) 범위 밖이다 |

## 3. 수동 2건 (awaiting_human — 마킹하지 않음)

- **S-21**(AC-24, C-21, profile=manual): 활성 하네스 7문서의 자동 커밋 금지 문구
  부재·체크포인트 절 존재 여부를 사람이 직접 Read로 대조해야 한다. `test-scenario.json`의
  `handoff`가 `S-21-handoff`/`submission_path: run/.runtime/handoff/S-21.json`로
  정의돼 있고, 실제 handoff 발행·제출은 이 TEST 실행 범위 밖(도구 미보유: `test-tool e2e`
  human executor 경로 미호출)이라 임의로 pass 처리하지 않았다.
- **S-25**(AC-4, AC-29, C-22, H-3, profile=manual): 실제 Claude TUI 기동·
  `opal-agent --provider claude --cwd <worktree_root> -p` 실행·`--wt` 소유권 전이
  실관측이 필요하다. 캡틴/소유자가 실제 세션에서 수행해야 하는 항목이라 임의로
  pass 처리하지 않았다.

두 건 모두 `result`/`operational_status`를 건드리지 않아 `scenario-status`의
`awaiting_human: 0`으로 남아 있다(실제 handoff 발행 전 상태) — locked 스펙과 다르게
임의 완료 처리하지 않았다는 뜻으로 해석해야 한다.

## 4. `scenario-status` 최종 출력

```
{"ok": true, "command": "scenario-status", "locked": true, "total": 29,
 "red_confirmed": 17, "red_required": 17, "red_confirmed_required": 17,
 "passed": 25, "failed": 1, "blocked": 1, "awaiting_human": 0,
 "status_counts": {"pass": 25, "fail": 1, "executor_unavailable": 0,
                    "infra_error": 0, "blocked": 1, "awaiting_human": 0}}
```

25(pass) + 1(fail:S-24) + 1(blocked:S-20) + 2(미마킹:S-21,S-25) = 29. 일치.

## 5. 허브 무쓰기 확인

- 작업 전: `git -C /Volumes/Data/AIStudio/workspace/ai-framework status --porcelain | wc -l` → **42**
- 작업 후: 동일 명령 → **42** (변화 없음)
