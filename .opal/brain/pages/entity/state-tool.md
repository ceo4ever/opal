---
type: entity
title: state-tool
module: state_tool
layer: util
domain: opal-pipeline
exports:
- cmd_init
- cmd_show
- cmd_advance
- cmd_mark
- cmd_block
- cmd_validate
- cmd_add_row
- cmd_status
- cmd_gate_pass
- cmd_spec_validate
- link_memory_history
source_ref: opal/tools/state-tool/state_tool.py
header_synced: 2026-08-16
tags:
- tool
- pipeline
sources:
- code:opal/tools/state-tool/
- task:013
- task:014
- task:005
- task:070
- task:072
- task:074
- task:088
- task:093
- task:094
- task:167
- task:170
related: [brain-tool, opal-brain-system, clarification-gate, state-tool-task-step-key-address, pipeline-json-spec, state-tool-next-action-auto-derivation, state-tool-import-existing-key-reattachment, close-history-auto-link-enforce-conversion, memory-tool, state-md-journal-redefinition, mirror-gate-must-not-hostage-ssot-record, mark-force-decision-log-scope, test-tool, op-scenario-gate-skill, scenario-economy-advisory-gate, design-gate-deterministic-pretier-separation]
created: 2026-06-10
updated: '2026-10-01'
status: active
---
# state-tool

## 개요

OPAL 파이프라인 현황판의 JSON SSOT(`state.json`)를 결정론적으로 집행하는 CLI 도구. 9개 서브 명령(init/show/advance/mark/block/validate/add-row/status/gate-pass) + verify + spec-validate를 제공하며 3-way 모드(interactive/semi-agentic/agentic)를 지원한다. task:094부터 `STATE.md`는 현황 표시 화면이 아니라 **의사결정 로그·블로커만 담는 저널**이며, 현황 조회는 전량 `show` 서브명령으로 일원화됐다(상세: [[state-md-journal-redefinition]]).

## 설계 배경 (WHY)

- **LLM 직접 편집 차단**: STATE.md 마크다운 표를 LLM이 직접 편집하면 행 상태 정합성이 깨진다. 그래서 행 상태 변경(⬜→🔄→✅)은 state-tool로만 수행하도록 강제한다 — "enforce, don't advise"(헌법) 집행 지점.
- **단계 건너뛰기 차단**: stage-transition guard가 앞 단계 필수 행 미완료 시 다음 단계 진입을 거부한다 (PLAN §M-A). 이번 태스크 015에서도 PLAN 행을 건너뛰려다 `stage_transition_violation`으로 차단당해 순서대로 처리했다.
- **동작 증거 게이트 (task 013)**: verify 서브명령이 mock 코드 패턴·증거 누락을 검출해 헌법 §4(동작 증거)를 기계적으로 집행한다.
- **행 재구성 (task 014)**: QA Gate/State Gate 행을 제거하고 PM Gate로 통합, gate-pass를 deprecate했다. 이 직후라 pilot STATE 행 일괄 변경은 회귀 위험이 크다 — 015가 CLOSE ingest를 opp 단독 파일럿으로 한정한 근거.
- **미러가 SSOT를 인질로 잡던 구조 해소 (task:094)**: STATE.md에 마커가 없으면 상태 변경 자체를 거부하던 `marker_missing` 게이트는, 표시용 미러(STATE.md)의 결손이 원본 기록(`state.json` 갱신·의사결정 로그 기재)까지 막는 역방향 의존이었다. 094가 이 게이트를 제거해 STATE.md 삭제·손상·마커 제거 상태에서도 `advance`/`mark`/`block`이 정상 동작하도록 뒤집었다(상세: [[mirror-gate-must-not-hostage-ssot-record]]).
- **목표-커버 게이트의 담당자 재량 재발 차단 (task:167)**: 목표-커버 게이트 행(`test_scenario.scenario_gate`·`plan.scenario_gate`)이 이력 기록 없이도 완료로 mark될 수 있던 구조는, PM 경로 설계 게이트에만 있던 completion guard(`apply_pm_design_guards`)가 목표-커버 경로에는 적용되지 않아 생긴 비대칭이었다. evaluator의 개선 제안(`advisories[]`)에 대한 응답도 강제되지 않아 반영 여부가 담당자 재량으로 소실됐다(근거: task:167 PLAN 확인 사실).
- **설계 게이트 결정론/evaluator 2-tier 분리 (task:170)**: 과거 18회차(161~168) 실측에서 결정론 실패 5회가 evaluator 호출 전 규칙 검사에서 났는데도 `design-gate start`가 회차를 먼저 올려 반복 상한을 소모했다. 결정론 검사를 evaluator 호출 전에 회차·상태 소비 없이 미리 실행할 수 있도록 노출해 이 소모를 없앴다(상세: [[design-gate-deterministic-pretier-separation]]).

## 인터페이스

`~/.opal/tools/state-tool/run.sh <command> <task-path> [options]` — venv python 래퍼. 출력 JSON `{ok, ...}`, 에러는 ERROR_CODES 카탈로그 키. **종수 SSOT는 코드다** — 실측 종수는 `opal/tools/state-tool/README.md` §에러 코드 카탈로그를 참조하고, 그 값을 다시 산문에 복제하지 않는다(task:094 R-9, 코드 44 / README 39 / 하네스 23의 3중 불일치를 정정하며 확정한 규율).

주요 서브커맨드 추가 (task:005):
- `verify <task-path> --clarification-check [--task-md <path>]` — TASK.md "## 명확화 결과" 4요소 잠금 검사. 미충족 시 `clarification_gate_unmet` exit 1. 섹션/파일 부재 시 graceful skip exit 0 (`opal/tools/state-tool/state_tool.py`)
- `mark`/`advance` — TASK→다음단계 첫 행 진입 시 명확화 게이트 자동 훅 발동. `--auto-pass` 우회 불가, `--force`만 긴급 탈출구.

행 주소 체계 확장 (task:070 — 상세는 [[state-tool-task-step-key-address]]):
- `--task-step <key>`·`--task-step-id <n>` — pilot이 선언한 task-step key(`{stage_slug}.{item_slug}`, 예: `plan.pm_gate`) 또는 1-based 숫자로 행 주소 지정. 기존 `--row N`은 deprecated 별칭으로 유지되며 3방식 모두 동일 행을 산출한다. 주소 플래그 0개는 `task_step_addr_required`, 2개 이상 동시 지정은 `task_step_addr_conflict`로 거부.
- `--action-step N/M` — 기존 `--step N/M`(액션 진행률) 개명. `--step` 별칭 유지.
- `spec-validate <pipeline.json>` — pilot `references/pipeline.json` 스펙(→ [[pipeline-json-spec]])을 검증하는 신규 서브명령. 파일 경로를 받는 유일한 서브명령이다.
- `init --rows-from <path>` — `.json`이면 pipeline.json 스펙 로딩(key 영속화, schema_version 1.1), `.md`면 기존 SKILL.md 표 파싱(레거시, stderr deprecation 경고).
- `add-row --key <key>` — 동적 행 삽입 시 key 지정, 미지정 시 `{stage_slug}.{item_slug}_{n}` 자동 생성(유일성 보장).

STATE.md "다음 액션" 자동 파생 (task:072 — 설계 반전 상세는 [[state-tool-next-action-auto-derivation]]):
- `advance`/`mark`는 행 상태 반영 후 파이프라인 프론티어(첫 미완료 행)에서 "다음 액션" 문구를 자동 계산해 `state.json` `next_action` 필드에 기록하고 STATE.md "## 다음 액션" 첫 줄만 치환한다(`_derive_next_action`·`update_next_action_section` — `opal/tools/state-tool/state_tool.py`). 하위 자유 기재 라인은 보존된다.
- `advance`/`mark`의 `--next-action <text>`는 해당 전이 1회 한정 오버라이드(비지속) — 다음 전이부터 자동 파생으로 복귀한다.
- `block`/`add-row`/`status` 등 나머지 명령은 "다음 액션" 섹션을 접촉하지 않는다(`sync_state_md(next_action=None)` 기본값 유지).

`--import-existing` **완전 제거 (task:094 D-2, R-4 — task:074가 고쳤던 기능 자체가 소멸)**:
- STATE.md가 파생 표 없는 저널로 재정의되면서(R-1) 표 파싱 대상 자체가 사라졌다. `cmd_init`은 `--import-existing` 지정 즉시 신규 에러 `import_existing_removed`로 거부한다(exit 1). argparse 인자는 `help=argparse.SUPPRESS`로 존치하되(삭제 시 `unrecognized arguments`가 비-JSON exit 2를 내 stdout 계약을 깨기 때문), `parse_existing_state_md`·`_key_source_index`·`_reattach_import_keys`·마커 재삽입 폴백은 전부 삭제됐다. task:074가 고쳤던 key 재접합 결함(아래 문단, 역사적 기록)은 이 제거로 대상 자체가 소멸했다 — 상세는 [[state-tool-import-existing-key-reattachment]] §이후 갱신.
- 신규 태스크는 전량 `init --rows-from pipeline.json` 경로다(10/10 pilot 전환 완료, task:090).

<details><summary>역사적 기록 — task:074 key 재접합 결함 수정 (094로 대상 기능 소멸)</summary>

- `cmd_init` import 분기(`parse_existing_state_md`)가 STATE.md 렌더 표(key 컬럼 없음)만 원천으로 삼아 keyless rows를 생성하던 결함을 수정했다. `--force`가 이 keyless rows로 기존 state.json(key 보유)을 덮어써 schema_version이 "1.1"→"1.0"으로 강등되고 `--task-step`/`--task-step-id` 주소가 전면 불능이 되는 2차 파급이 있었다.
- 신규 헬퍼 `_key_source_index`·`_reattach_import_keys`가 (stage,item) 순서 소비 매칭으로 keyless import 행에 기존 state.json(1순위) → `--rows-from` pipeline.json(2순위, 폴백) 순으로 key를 재접합한다. 두 원천 모두 없으면 keyless 유지 + stderr 경고(하위호환, stdout 불변).

</details>

완료 단계 히스토리 자동 연결 (task:088 — 아키텍처 결정 상세는 [[close-history-auto-link-enforce-conversion]]):
- 완료 단계의 마지막 행이 완료로 확정되는 순간(`is_close_last and row["status"] == "done"`, `cmd_mark` 기존 판정 재사용), `link_memory_history(task_path, state)`가 형제 도구인 memory-tool을 별도 프로세스로 호출해 작업 히스토리 행을 생성한다. 이 접합은 state.json·STATE.md 영속화가 끝난 뒤에 실행되어, 연동 실패가 진행 상태 기록 자체를 되돌리는 일이 없다(`opal/tools/state-tool/state_tool.py`).
- 제목·경로는 `find_project_root()`(조상 디렉토리에서 `.opal/MEMORY.json` 앵커 탐색)와 `derive_history_title()`(task_id 분해)로 결정론적으로 파생하고, 핵심결과는 소유자 보강 대기 플레이스홀더로 채운 뒤 그대로 실행 가능한 보강 명령을 `build_history_reminder()`로 함께 반환한다.
- 연동 결과·경고는 `ok()` stdout 페이로드의 `history_link` 필드에만 실리며 state.json에는 영속하지 않는다(스키마 `additionalProperties:false` 위반 회피 — 076 진행 미러 선례 답습). 프로젝트 미탐지·히스토리 저장소 손상·타임아웃 등 어떤 실패도 완료 처리 자체(`ok: true`)를 막지 않는다.
- 훅(`todo_mirror_hook.py`)의 `build_additional_context`가 기존 진행 미러 안내에 히스토리 보강 안내를 병존 추가하도록 확장됐다 — 훅 미설정 환경에서도 동일한 보강 명령이 stdout에 남아 있어 안내가 유실되지 않는다.

STATE.md 저널 재정의 + 조회 경로 단일화 (task:094 — 아키텍처 결정 상세는 [[state-md-journal-redefinition]]):
- STATE.md 생성·갱신 산출물에서 `state.json` 파생 섹션(파이프라인 현황판 표·마커·"## 현재 상태"·"## 다음 액션" 자동 파생)을 전부 제거하고, "## 의사결정 로그"·"## 블로커"만 남긴 저널로 재정의했다. `state.json` `rows[]` 스키마·`next_action` 필드는 무변경(제거는 STATE.md 렌더 쪽만).
- `show`(마커 유무와 무관하게 md/json 모두 `state.json`에서만 렌더 — R-5)가 현황 조회의 유일한 표준 경로로 승격됐다. 마커가 남은 레거시(001~093) STATE.md를 열람할 때는 "이 표는 동결 텍스트이며 SSOT는 state.json"이라는 배너를 출력에 prepend하되 파일에는 바이트를 쓰지 않는다.
- 저널 쓰기는 fail-open이다 — 쓰기 실패(권한·I/O 오류)가 파이프라인을 막지 않고 `ok:true` + stdout `journal_warning`으로 원문을 표면화한다. 상세는 [[mirror-gate-must-not-hostage-ssot-record]].

agentic 승인 계약 표시 층 정합 (task:094 R-11 — 093이 집행 층에 일원화한 `can_auto_approve_user_confirmation()`을 표시·게이트 층까지 확장):
- 모드 경계 상수에 `DICT`/`MODEL`/`DDL·MIGRATION` 3개 stage를 추가해, semi-agentic(기본 모드) opdd에서 설계 확정 3단계가 소유자 노출 없이 자동 승인되던 주권 침해를 해소했다.
- CLOSE 게이트에 "사용자 확인 행이 0개인 파이프라인"(예: opgc) 폴백을 추가했다 — CLOSE 첫 행 자체를 소유자 승인 지점으로 삼아, 확인 행이 없어 `--force` 없이는 영원히 종료할 수 없던 데드락을 해소했다.
- "다음 액션" 파생과 진행 미러(todo mirror) 계산이 자동 승인 예정 확인 행을 판정에서 제외하도록 바꿔, 실제로는 자동 통과될 행이 "사용자 확인 대기"로 잘못 표시되는 헛 신호를 없앴다(CLOSE 진입 직전은 실제 승인 지점이므로 예외).

PM 경로 설계 게이트 advisory 응답·refinement, 목표-커버 게이트 mark 가드 (task:167):
- `design-gate record`가 `--advisory-responses <json>`을 받는다. evaluator 결과 최상위 `advisories[]`(`_validate_advisories()`, `opal/tools/state-tool/state_tool.py:7044`)를 pass이고 refinement 회차가 아닐 때 검사하고, 응답 파일(`_load_advisory_responses()`, `:7072`)의 ID 집합 불일치·중복·공백 사유 `retain`은 `advisory_response_invalid`로 상태를 바꾸지 않고 거부한다. 응답에 `apply`가 1건 이상이면 history에 `verdict: rewrite`·`reason: advisory_apply`를 기록하고(`--rewrite-target` 필수) `design_gate.refinement_pending=true`로 전환한다(`cmd_design_gate_record()`, `:7107`).
- 다음 `design-gate start`는 `refinement_pending`이면 이번 시도와 evaluator 입력에 `refinement: true`를 싣는다. refinement 회차의 record는 응답 요구·형식 검사 없이 `advisories: []`로 기록하며, pass면 `refinement_pending=false`로 복귀하고 비-pass면 `reason: advisory_refinement_failed`와 함께 기존 `retry_limit`·`await_user`·`decision_request` 전이를 탄다. start의 결정론 검사 실패도 같은 접두사로 동일 전이를 탄다.
- `advisory_apply` 회차와 refinement 회차는 새 상태 값 없이 `limit_from`을 1 올려 반복 상한 계산에서 제외한다(기존 history verdict 5값은 바뀌지 않는다).
- **목표-커버 게이트 mark 가드**: `apply_scenario_gate_mark_guard()`(`opal/tools/state-tool/state_tool.py:6658`)가 `cmd_mark`(`:4277`)에서 key `test_scenario.scenario_gate`·`plan.scenario_gate` 행을 미완에서 완료로 바꾸는 시점에 형제 test-tool의 `scenario-gate-verify --task-folder <task>`를 subprocess로 호출한다. exit 0이 아니면 `scenario_gate_record_required`로 state.json을 바꾸지 않고 거부하며, `--force`·`--auto-pass`·`--as-worker`로 우회할 수 없다. 이미 완료된 행·다른 key·`plan.design_gate`에는 적용하지 않는다.
- `advisory_response_invalid`·`scenario_gate_record_required`가 `DESIGN_GATE_ERROR_CODES`(총 17종)에 추가됐다(`ERROR_CODES` 키 집합 동결은 유지).

설계 게이트 결정론 사전검사 노출 (task:170 — 아키텍처 결정 상세는 [[design-gate-deterministic-pretier-separation]]):
- `verify --design-gate-check` 플래그가 기존 `_gate_flags` 상호배타 그룹의 6번째 멤버로 추가됐다. PM 경로 태스크(`plan.design_gate` 행 보유)의 `state.json`에 대해 기존 `_design_gate_deterministic_check(task_path)`와 신규 `_decision_clarity_lint(task_path)`를 호출해 `{"ok": true, "design_gate_check": ("unmet" if deterministic_missing else "pass"), "deterministic_missing": [...], "decision_clarity_candidates": [...]}`를 항상 exit 0·회차·상태 변경 없이 반환한다(비차단, 사전 확인용).
- `_decision_clarity_lint()`는 PLAN.md 본문에서 펜스 코드 블록·인라인 코드 스팬을 제외한 산문만 고정 패턴 12개로 줄 단위 스캔해 `"PLAN.md:<줄번호>: <해당 줄 발췌>"` 형식 후보 문자열을 반환한다 — 판정이 아니므로 `decision_clarity_candidates`가 있어도 그 자체로 `"unmet"`을 만들지 않는다.
- `state.json` 부재 시 다른 5개 게이트 플래그와 동일한 graceful skip(exit 0), PM 경로가 아닌 태스크(`plan.design_gate` 행 없음)면 `{"ok": true, "design_gate_check": "skipped", "reason": "not a PM design path"}`를 반환한다.
- `_decision_clarity_lint()`는 `_design_gate_deterministic_check` 함수 정의 끝(`:6853`) 이후에 추가되어 태스크 168이 동시에 편집한 `apply_opd2_gate_mark_guard`(`:6702-6763`) 및 그 앞 상수 블록(`:6513-6534`)과 물리적으로 겹치지 않는다.

## 관련 페이지

- [[brain-tool]] — state-tool 패턴(run.sh+venv python, ERROR_CODES, KST date.js)을 복제한 동형 도구
- [[opal-brain-system]] — brain의 집행 철학이 state-tool에서 유래
- [[clarification-gate]] — task:005에서 추가된 verify --clarification-check 게이트 상세
- [[state-tool-task-step-key-address]] — task:070 task-step 키 주소 체계 아키텍처 결정
- [[pipeline-json-spec]] — task:070 pilot 파이프라인 정의 SSOT(pipeline.json)
- [[state-tool-next-action-auto-derivation]] — task:072 "다음 액션" 자동 파생 설계 반전
- [[state-tool-import-existing-key-reattachment]] — task:074 import-existing key 재접합 결함 수정 설계 (task:094로 기능 자체 소멸 — 역사적 기록)
- [[close-history-auto-link-enforce-conversion]] — task:088 완료 단계 히스토리 자동 연결 아키텍처 결정
- [[memory-tool]] — task:088에서 state-tool이 형제 프로세스로 호출하기 시작한 히스토리 도구
- [[state-md-journal-redefinition]] — task:094 STATE.md 파생 섹션 제거 + 저널 재정의 아키텍처 결정
- [[mirror-gate-must-not-hostage-ssot-record]] — task:094 미러 게이트 역방향 의존 해소 + fail-open 저널 쓰기 경계 설계
- [[mark-force-decision-log-scope]] — task:094가 재확인한 의사결정 로그 자동 기재 3트리거
- [[test-tool]] — task:167부터 목표-커버 게이트 mark 가드가 형제 프로세스로 호출하는 검증 주체
- [[op-scenario-gate-skill]] — 이 도구의 design-gate record/start를 호출하는 PM 경로 컨트롤 스킬
- [[scenario-economy-advisory-gate]] — task:167 advisory 응답 게이트·목표-커버 기록·mark 가드 전체 계약
- [[design-gate-deterministic-pretier-separation]] — task:170 결정론/evaluator 2-tier 분리 + 사전검사 아키텍처 결정
