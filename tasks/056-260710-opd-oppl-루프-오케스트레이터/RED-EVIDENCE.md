<!--
@header {
  "module": "056-red-evidence",
  "layer": "report",
  "domain": "opal-pipeline",
  "description": "T056 RED-first 트랙 실패 테스트 실행 증거 (backlog-tool/test-tool scenario-*/state-tool oppl). opal-test-agent(mode: red) 작성 — 작성자≠구현자(red-first.md §2).",
  "exports": ["RED 실행 로그 3건", "케이스별 실패 요약"]
}
-->

# RED-EVIDENCE: T056 opal-pilot-project-loop(oppl) RED-first 실패 테스트

> 작성: opal-test-agent(mode: red) | 시점: 2026-07-10 16:29 (KST)
> 규칙 SSOT: `~/.opal/references/harness/red-first.md` §1(RED→GREEN 순서), §4(공개 인터페이스 검증)
> 검증 방식: 전 케이스 `subprocess`로 대상 `run.sh`를 실호출(공개 인터페이스: stdout JSON + exit code) — mock/patch/MagicMock 미사용(단, state-tool 신규 케이스는 기존 파일 관례상 `subprocess`만 사용, 기존 mock 패턴과 무결합).

## 0. 신규/수정 파일

| # | 파일 | 유형 | 대상 시나리오 |
|---|------|------|-------------|
| 1 | `opal/tools/backlog-tool/tests/test_backlog_tool.py` | 신규 | S-001, S-002, S-003, S-004, S-007(backlog 몫), S-006, S-001b |
| 2 | `opal/tools/test-tool/tests/test_scenario.py` | 신규 | S-011, S-012, S-007(scenario 몫), S-014(존재 확인만) |
| 3 | `opal/tools/state-tool/tests/test_state_tool.py` | 기존 파일에 케이스 추가 (`TestOpplSkillInit` 클래스) | S-020 |

기존 케이스(위 3번 파일의 `TestOpplSkillInit` 이전 모든 클래스)는 수정하지 않았다 — `@header` description/exports 메타데이터와 `import subprocess` 1줄만 추가.

---

## 1. 실행 명령 · 결과

### 1.1 backlog-tool (S-001, S-002, S-003, S-004, S-007, S-006, S-001b)

```
~/.opal/.venv/bin/python -m pytest opal/tools/backlog-tool/tests/test_backlog_tool.py -v
```

- **exit code: 1** (전 케이스 FAIL)
- 결과: **18 failed, 0 passed** (18 items collected)
- 원인: `opal/tools/backlog-tool/run.sh` 및 `backlog_tool.py` 자체가 아직 존재하지 않음(도구 미구현) → `bash <run.sh>` 호출이 "No such file or directory"로 즉시 실패(exit 127) 하거나 stdout 미생성으로 JSON 파싱 실패.

| 케이스 | 결과 |
|---|---|
| `TestInit::test_init_creates_backlog_json_and_md` | FAIL — backlog.json/BACKLOG.md 미생성 |
| `TestInit::test_init_twice_rejects_with_already_initialized` | FAIL — 1회차부터 실패 |
| `TestInit::test_init_stdout_is_single_line` | FAIL — stdout 0줄 |
| `TestSelectNext::test_returns_highest_priority_pending_with_depends_met` | FAIL — select-next 미동작 |
| `TestSelectNext::test_returns_dependent_task_after_dependency_done` | FAIL |
| `TestSelectNext::test_returns_null_when_exhausted` | FAIL |
| `TestMarkTransition::test_valid_transition_pending_to_in_progress_to_done` | FAIL |
| `TestMarkTransition::test_invalid_transition_done_to_pending_rejected` | FAIL |
| `TestDoneCheck::test_all_done_false_with_remaining` | FAIL |
| `TestDoneCheck::test_all_done_true_when_all_tasks_done` | FAIL |
| `TestResultContract::test_init_success_and_error_contract` | FAIL — 단일라인 JSON 계약 위반(빈 stdout) |
| `TestResultContract::test_add_task_success_and_error_contract` | FAIL |
| `TestResultContract::test_select_next_success_and_notfound_contract` | FAIL |
| `TestResultContract::test_mark_success_and_error_contract` | FAIL |
| `TestResultContract::test_done_check_contract` | FAIL |
| `TestResultContract::test_show_contract` | FAIL — exit 127 (run.sh 부재) |
| `TestBacklogMdMirror::test_md_reflects_json_after_cud_chain` | FAIL — BACKLOG.md FileNotFoundError |
| `TestConcurrentMark::test_parallel_mark_no_silent_corruption` | FAIL — backlog.json 미생성 |

### 1.2 test-tool scenario-* (S-011, S-012, S-007, S-014)

```
~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_scenario.py -v
```

- **exit code: 1**
- 결과: **10 failed, 3 passed** (13 items collected)
- 원인: `scenario-init/scenario-lock/scenario-mark/scenario-status` 서브명령이 `test_tool.py`의 `dispatch`/argparse에 아직 등록되지 않음 → run.sh 호출 시 stdout이 비거나 argparse 사용법 오류로 종료, 단일라인 JSON 계약 위반.
- **S-014 3건(`TestExistingSuiteRegressionPresence`)은 의도대로 PASS** — 기존 `test_test_tool.py` 스위트 존재·4서브명령 클래스 존재·dispatch dict 기존 키 보존을 "산출물 존재 확인"으로만 검증(로직 재실행 아님), 기존 파일은 미수정.

| 케이스 | 결과 |
|---|---|
| `TestScenarioLockRedGate::test_lock_rejected_when_any_scenario_red_unconfirmed` | FAIL |
| `TestScenarioLockRedGate::test_lock_succeeds_when_all_scenarios_red_confirmed` | FAIL |
| `TestScenarioMarkLockGate::test_mark_rejected_before_lock` | FAIL |
| `TestScenarioMarkLockGate::test_mark_succeeds_after_lock` | FAIL |
| `TestScenarioResultContract::test_scenario_init_success_contract` | FAIL |
| `TestScenarioResultContract::test_scenario_init_invalid_json_contract` | FAIL |
| `TestScenarioResultContract::test_scenario_status_not_initialized_contract` | FAIL |
| `TestScenarioResultContract::test_scenario_status_success_contract` | FAIL |
| `TestScenarioResultContract::test_scenario_lock_error_contract` | FAIL |
| `TestScenarioResultContract::test_scenario_mark_error_contract` | FAIL |
| `TestExistingSuiteRegressionPresence::test_existing_suite_file_exists` | **PASS**(의도된 존재 확인) |
| `TestExistingSuiteRegressionPresence::test_existing_suite_covers_four_subcommands` | **PASS** |
| `TestExistingSuiteRegressionPresence::test_test_tool_dispatch_unchanged_keys_present` | **PASS** |

### 1.3 state-tool oppl init (S-020)

```
~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/test_state_tool.py -k TestOpplSkillInit -v
```

- **exit code: 1**
- 결과: **1 failed, 1 passed**

| 케이스 | 결과 | 상세 |
|---|---|---|
| `TestOpplSkillInit::test_init_with_skill_oppl_succeeds` | **FAIL (RED)** | `--skill` choices에 `"oppl"` 미등록 → argparse usage error, 실제 exit code **2** (기대: 0). `AssertionError: 2 != 0` |
| `TestOpplSkillInit::test_existing_eight_skills_regression_unaffected` | PASS | 기존 스킬(`opp`) init은 회귀 없이 exit 0 — 신규 케이스 추가가 기존 경로를 깨뜨리지 않음을 사전 확인 |

전체 회귀 확인(참고, 본 케이스 포함):
```
~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/test_state_tool.py -q
```
→ `2 failed, 203 passed, 3 subtests passed`. 실패 2건 중 1건은 본 RED 케이스(`TestOpplSkillInit::test_init_with_skill_oppl_succeeds`), 나머지 1건(`TestVerify::test_verify_passes_own_test_scenario_md`)은 태스크 034 경로(`tasks/034-260621-opds-state-tool-mock-패턴-오탐수정/TEST-SCENARIO.md`) 참조로 인한 **본 태스크와 무관한 기존 환경성 실패**(해당 경로가 `tasks/backup/`로 이관되어 발생, 034 완료 이후 발생한 사전 존재 이슈 — 056 변경과 무관, 수정 범위 밖).

참고(비교, 미수정): `test-tool` 기존 스위트도 동일하게 확인:
```
~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py -q
```
→ `1 failed, 11 passed, 9 subtests passed`. 실패 1건(`TestResolve::test_resolve_infer_fallback_when_no_yaml`)은 로컬 환경에 `~/.opal` 전역 `test-tools.yaml`이 존재해 `source: global`이 반환되는 **환경 의존적 사전 존재 이슈**(scenario-* 추가와 무관, 미수정).

---

## 2. 종합

| 파일 | 총 케이스 | RED(FAIL) | 의도된 PASS(존재확인/회귀) |
|---|---|---|---|
| `test_backlog_tool.py` | 18 | 18 | 0 |
| `test_scenario.py` | 13 | 10 | 3 (S-014 존재확인) |
| `test_state_tool.py::TestOpplSkillInit` | 2 | 1 | 1 (회귀 확인) |
| **합계** | **33** | **29 FAIL** | **4 의도된 PASS** |

- 대상 도구(backlog-tool, test-tool scenario-*, state-tool `--skill oppl`)의 신규 동작을 요구하는 모든 케이스가 예상대로 **RED(실패)** 상태다.
- "의도된 PASS" 4건은 신규 기능이 아니라 (a) 기존 test-tool 회귀 스위트의 존재·불변성 확인(S-014), (b) state-tool 기존 8스킬 회귀 무결성 확인 — 신규 요구사항과 무관하므로 RED 대상이 아니다.
- RED-first 게이트(`state-tool verify <task> --red-check`) 통과 조건인 "실패 테스트 코드 작성·실행·exit code≠0 증거 기록"을 충족했다.
- EXECUTE(GREEN) 진입 전 이 문서를 RED 증거로 제출한다. GREEN/fix 루핑 중 위 3개 테스트 파일의 기존 작성 케이스 수정을 금지한다(red-first.md §3).

---

## 3. 구현자(GREEN) 참고 — 기대 계약 요약

- **backlog-tool**: PLAN.md §3.1.2·§3.1.3 그대로 — 6서브명령(init/add-task/select-next/mark/done-check/show), 에러코드 exit 0/1/2, backlog.json 스키마(schema_version/project_title/mode/created_at/updated_at/goal/tasks[]).
- **test-tool scenario-***: PLAN.md §3.2.2 그대로 — `lib/scenario.py` 신규 모듈, 에러코드 exit 8(`red_not_confirmed`)/9(`scenario_not_locked`)/10(`scenario_not_initialized`)/11(`scenario_spec_invalid_json`), 기존 4서브명령 dispatch 키·로직 불변.
- **state-tool**: PLAN.md §3.3.2 그대로 — `--skill` choices에 `"oppl"` 1건 추가 + `schema/state.schema.json` enum 동기화. 기존 8스킬 동작 불변(추가만).

이 문서는 TEST 단계에서 opal-test-agent가 GREEN 이후 결과를 채우는 TEST-SCENARIO.md와 별개로, RED 시점의 실패 증거만을 기록한다. TEST-SCENARIO.md는 본 작업에서 수정하지 않았다.
