---
template: sdlc-v2
---
# PLAN: TEST 단계 소요시간 단축

> 입력: [TASK.md](TASK.md), [REQUEST.md](REQUEST.md). 변경 후보는 `code-scan search 'state-tool|worktree-tool|opal-test-agent|opal-pilot-dev'` 조회 후 본문으로 확인했다.

## Approach

기존 TEST의 최종 PASS 기준과 독립 검증 주체를 유지한다. 사람 협업 요청·자동 실행을 TEST 시작 때 분리하고, 수정 반복은 영향 범위로 좁히되 최종 Gate에서 전체 회귀를 한 번 수행한다. 요구 변경은 fix와 별도로 계수한다. 시간은 사후 행 마크 시각이 아니라 실행·대기 시작/종료 사건으로 계측한다. 태스크 161 소유 test-tool 내부와 163의 산출물은 변경하지 않는다. 근거: `TASK.md` §Constraints·§Acceptance criteria, `REQUEST.md` §3.1~3.4.

## Findings

### 직접 변경

`opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/schema/state.schema.json`, `opal/tools/state-tool/tests/test_state_tool_test_cycle.py`, `opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/worktree-tool/tests/test_worktree_tool.py`, `opal/core/references/harness/test-cycle.md`, `opal/core/references/harness/guards.md`, `opal/core/references/events.json`, `opal/skills/opal-pilot-dev/SKILL.md`, `opal/agents/opal-test-agent/AGENT.md`, `opal/skills/op-dev-execute/references/execute-guide.md`, `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`, `opal/core/references/harness/pm-review-gate.md`, `opal/tools/event-loader/tests/test_event_loader_test_event.py`.

### 회귀 확인

`opal/tools/state-tool/tests/test_state_tool_core_cli.py`, `opal/tools/state-tool/tests/test_state_tool_mode_contracts.py`, `opal/tools/event-loader/tests/test_event_loader.py`, `opal/tools/worktree-tool/tests/conftest.py`, `opal/tools/test-tool/tests/test_test_tool.py`는 실행만 한다. 161 소유 `opal/tools/test-tool/test_tool.py`도 읽기·실행만 한다.

### 문서 갱신

`docs/PROJECT.md`, `docs/CONVENTIONS.md`의 변경된 계약·배포 경계를 동기화한다.

### 미확인 가정

H-1, H-2.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| TEST 실행 절차의 단일 원천 | `test-cycle.md`가 사람 협업 선요청, 증거 재사용, 반복 범위, 최종 Gate, 요구 변경 상한을 소유하고 pilot·agent·PM Gate는 참조한다. | `events.json`의 현재 `stage.test`는 실행 규칙을 로드하지 않는다. `REQUEST.md` §3.4, `opal/core/references/events.json:351-364`. |
| 사람 협업 선요청 | TEST 진입 직후 TEST-SCENARIO의 human step/handoff를 모두 모아 한 번 요청하고 기다리는 동안 자동 항목을 실행한다. 제출은 기존 verifier가 판정한다. | `REQUEST.md` §3.1, `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §Scenarios. |
| 변경 종류 분리 | state-tool의 TEST 추가 행에 `fix`와 `requirement_change` 유형을 명시한다. 요구 변경은 독립 상한 3회로 관리하며 초과 시 새 태스크 또는 PLAN 재진입의 사용자 결정을 요청한다. legacy 행은 종전 의미를 유지한다. | `REQUEST.md` §3.2, `opal/tools/state-tool/state_tool.py:4664`. 상한 3은 기존 fix 반복 상한과 같은 예측 가능한 경계로 두되 별도 카운터다. |
| 반복 재검증 | 실패 S-ID와 변경 파일 영향 S-ID만 재실행한다. 영향 계산이 불명확하면 해당 묶음 전체를 재실행한다. 최종 Gate에서는 필수 시나리오 전부 PASS와 전체 회귀 1회를 요구한다. | `TASK.md` C-3, `opal/core/references/harness/guards.md:101`, `opal/skills/opal-pilot-dev/SKILL.md:307-320`. |
| 실행 증거 재사용 | 동일 commit SHA, 동일 명령·환경 서명, PASS 증거 경로가 있는 EXECUTE lint/type/unit 결과만 TEST에서 재사용하고 TEST 보고에 원천을 남긴다. 변경 또는 증거 부재 시 재실행한다. | `REQUEST.md` §3.3, `opal/agents/opal-test-agent/AGENT.md:65-68`. |
| 기본 브랜치 선행 확인 | TEST 진입 전에 worktree-tool 읽기 전용 명령으로 동결 base-ref와 HEAD의 ahead/behind를 확인한다. behind가 있으면 통합 후 TEST를 재개한다. 통합 merge는 사용자 승인 경계에 둔다. | `REQUEST.md` §3.3, `opal/core/references/harness/worktree.md` §merge 경로, `TASK.md` AC-6. |
| 소요시간 | state-tool이 TEST 실행과 사람 대기 interval을 실제 시작/종료 호출 시각으로 기록하고 읽기 전용 요약 명령에서 자동 시간·대기 시간·두 유형의 반복 수를 반환한다. legacy는 모르는 값을 unknown으로 반환한다. | `REQUEST.md` §3.1 시점 한계, `TASK.md` AC-7. |
| 디스패치 경량 경로 | receipt 재사용은 채택하지 않는다. manifest가 같더라도 선별 프로젝트 문서·capability·권한 경계가 달라질 수 있고 워커별 verify가 보안 게이트다. 변경 범위에서 이를 줄이면 검증 비용보다 stale 입력 위험이 크다. | `REQUEST.md` §3.3, `opal/core/references/pm/dispatch-process.md` §워커 디스패치. |

### W-1 공개 CLI와 저장 계약

- `add-row ... --stage TEST --test-change-kind fix|requirement_change`를 확장한다. 이 옵션은 TEST 행에서만 허용하고 새 행에 `test_change_kind`를 저장한다. 옵션 없는 기존 호출·행은 그대로 두며 신규 카운터에서 제외한다. 요구 변경 상한은 같은 태스크의 `requirement_change` 행 3건이다. 네 번째 시도는 행을 만들지 않고 `current_status=blocked`, `transition_action=await_user`, `report_type=decision_request`, `next_action=새 태스크 또는 PLAN 재진입 선택`을 반환한다. 초과 사건은 STATE.md 결정 로그에 남긴다. 사용자가 경로를 고른 뒤 `status --set additional_work --note <사용자 결정>`으로 재개하고, 새 태스크 경로를 택하면 이 태스크에 네 번째 행을 추가하지 않는다. PLAN 재진입 경로는 PLAN 추가 행을 도구로 만들고 새 계획부터 재승인한다. 기본 3회 상한은 reset하지 않는다.
- `test-clock start|stop <task> --kind auto|human --id <시나리오 또는 실행 식별자>`를 추가한다. `state.json.test_timing.intervals[]`의 각 원소는 `kind`, `id`, `started_at` UTC ISO 8601, `ended_at` UTC ISO 8601 또는 null을 가진다. `(kind,id)` 열린 interval은 하나만 허용하고, 중복 start와 열린 interval 없는 stop은 오류로 거부한다. 각 호출은 호출 시점의 UTC를 도구가 찍고 상태 파일에 원자 기록하며, 행 mark 시각을 추정 입력으로 사용하지 않는다. 사람 대기는 묶음 요청 발송 시 start, 해당 제출의 verifier 최종 처리 시 stop한다. 여러 사람 항목이 동시에 열려도 `human_wait_seconds`는 interval 합산이 아니라 시간축 합집합 길이로 계산한다.
- `test-metrics <task>`는 읽기 전용 JSON으로 `auto_seconds`, `human_wait_seconds`, `fix_count`, `requirement_change_count`, `open_intervals`를 반환한다. 종류별 완료 interval이 없으면 초 값은 null이고 `open_intervals`에 진행 중 항목을 남긴다. 횟수는 유형을 가진 TEST 행에서만 계산하며, legacy 행의 미분류 가능성을 `legacy_unclassified_rows`로 명시한다. 기존 state에는 `test_timing`이 없어도 조회가 성공해야 한다.

### W-2 공개 CLI와 분기 판정

- `worktree-tool divergence --project-root <허브 절대경로> --task <NNN>`은 registry에 동결된 repo별 `base_ref`와 worktree HEAD에 대해 `git rev-list --left-right --count HEAD...<base_ref>`를 읽기 전용 실행한다. 응답에 repo별 `ahead`, `behind`, `base_ref`, `head_sha`를 반환한다. `behind>0`이 하나라도 있으면 `integration_required=true`다. 명령은 fetch/merge/reset을 하지 않는다.
- TEST 진입 전 `integration_required=true`면 TEST 자동 실행을 시작하지 않고 통합을 요청한다. merge 승인 이후 같은 명령을 다시 수행해 `behind=0`을 확인하고 진행한다. 실패/미확인은 통과로 취급하지 않는다.

### W-3 실행 순서와 증거 계약

- TEST 첫 순서는 분기 조회 → 사람 handoff 전체 추출·한 번에 요청 → 사람 대기 `test-clock start` → 자동 `test-clock start`와 실행이다. 자동 검사는 각 실행 후 stop하고 사람 제출을 기다리지 않는다. 사람 요청이 0건이면 human interval을 만들지 않는다.
- fix 후 tester는 실패 S-ID와 변경 파일 영향 S-ID를 합쳐 재실행한다. 관계가 없거나 불확실한 부분은 해당 시나리오 묶음 전체를 포함한다. 미재실행 PASS에는 기존 증거를 유지하되 SHA 변화가 해당 시나리오에 영향 없음이 확인돼야 한다. 최종 Gate는 모든 필수 S-ID PASS, 전체 회귀 1회, 보안 1회, 최종 수정 뒤 컨벤션 checker 1회를 독립 실행한다.
- EXECUTE lint/type/unit 재사용은 SHA·명령/환경 서명·PASS 출력 경로가 동일할 때만 허용하고 TEST 보고에 세 값과 증거 경로를 기록한다. 그 밖에는 TEST에서 다시 실행한다. `test-scenario.json`에 새 필드를 억지로 추가하지 않는다.

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. TEST 상태·계측 | opal-task-agent | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/schema/state.schema.json`, `opal/tools/state-tool/tests/test_state_tool_test_cycle.py` | 위 W-1 계약의 `add-row --test-change-kind`, `test-clock start/stop`, `test-metrics` 공개 CLI·저장 구조·오류·legacy 처리를 구현하고 실제 시각 기반 테스트를 추가한다. | 없음 | P1 | AC-2, AC-7, C-5, C-6, C-7 |
| W-2. 기본 브랜치 분기 조회 | opal-task-agent | `opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/worktree-tool/tests/test_worktree_tool.py` | 위 W-2 계약의 읽기 전용 divergence CLI를 만들고 실 git fixture에 동등/선행 사례를 추가한다. | 없음 | P1 | AC-6, C-1, C-7 |
| W-3. TEST 절차 계약 | opal-task-agent | `opal/core/references/harness/test-cycle.md`, `opal/core/references/harness/guards.md`, `opal/core/references/events.json`, `opal/skills/opal-pilot-dev/SKILL.md`, `opal/agents/opal-test-agent/AGENT.md`, `opal/skills/op-dev-execute/references/execute-guide.md`, `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`, `opal/core/references/harness/pm-review-gate.md`, `opal/tools/event-loader/tests/test_event_loader_test_event.py` | 선요청·병행·요구 변경·반복 범위·증거 재사용·최종 전체 회귀와 GC 1회·TEST 전 분기 확인을 한 SSOT로 접합한다. stage.test load/verify 회귀를 추가한다. | W-1, W-2 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-8, AC-9, C-2, C-3, C-4, C-5 |
| W-4. 프로젝트 문서·배포 검증 | opal-task-agent | `docs/PROJECT.md`, `docs/CONVENTIONS.md` | 새 계약의 문서 레지스트리와 배포 경계를 갱신한다. 전체 관련 회귀와 임시 설치 대상의 진입점을 검증한다. 실제 `~/.opal` 설치 직전에 사용자에게 보고한다. | W-3 | P3 | AC-10, C-1, C-6, C-7 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 시나리오와 변경 파일의 영향 관계가 없는 프로젝트 | 축소 재검증의 누락 | PASS 오판 | 관계가 불명확하면 해당 묶음 전체 재실행, 최종 전체 회귀 1회. W-3과 S-3. |
| H-2. TEST 계측을 시작하지 않은 legacy 태스크 | 시간 수치의 부정확성 | 잘못된 성능 비교 | unknown 반환, 행 mark 시각을 실행 시간으로 추정하지 않음. W-1과 S-7. |

## Release and recovery

- 적용 순서: P1 구현 및 독립 테스트 → P2 절차 접합 → P3 문서·회귀 → 임시 설치 대상 검증 → 외부 설치 승인 대기.
- 검증 범위: state/worktree/event-loader 공개 CLI·실 git 분기 사례·고정 TEST 시나리오·기존 관련 회귀. test-tool 내부는 변경하지 않는다.
- 실측 경계: 자동 실행은 start/end, 사람 대기는 요청/제출 시각, 반복은 상태 행 유형으로 계산한다. 호출이 없으면 unknown이다.
- 실패 시: worktree 변경만 되돌려 재작업한다. 실제 배포본은 사용자 승인 전 수정하지 않는다.
