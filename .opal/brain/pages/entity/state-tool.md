---
type: entity
title: state-tool
module: state_tool
layer: util
domain: opal-pipeline
exports: [cmd_init, cmd_show, cmd_advance, cmd_mark, cmd_block, cmd_validate, cmd_add_row, cmd_status, cmd_gate_pass, cmd_spec_validate]
source_ref: opal/tools/state-tool/state_tool.py
header_synced: 2026-06-10
tags: [tool, pipeline]
sources: [code:opal/tools/state-tool/, task:013, task:014, task:005, task:070, task:072, task:074]
related: [brain-tool, opal-brain-system, clarification-gate, state-tool-task-step-key-address, pipeline-json-spec, state-tool-next-action-auto-derivation, state-tool-import-existing-key-reattachment]
created: 2026-06-10
updated: 2026-07-23
status: active
---

# state-tool

## 개요

OPAL 파이프라인 현황판(STATE.md)의 JSON SSOT를 결정론적으로 집행하는 CLI 도구. 9개 서브 명령(init/show/advance/mark/block/validate/add-row/status/gate-pass) + verify를 제공하며 3-way 모드(interactive/semi-agentic/agentic)를 지원한다.

## 설계 배경 (WHY)

- **LLM 직접 편집 차단**: STATE.md 마크다운 표를 LLM이 직접 편집하면 행 상태 정합성이 깨진다. 그래서 행 상태 변경(⬜→🔄→✅)은 state-tool로만 수행하도록 강제한다 — "enforce, don't advise"(헌법) 집행 지점.
- **단계 건너뛰기 차단**: stage-transition guard가 앞 단계 필수 행 미완료 시 다음 단계 진입을 거부한다 (PLAN §M-A). 이번 태스크 015에서도 PLAN 행을 건너뛰려다 `stage_transition_violation`으로 차단당해 순서대로 처리했다.
- **동작 증거 게이트 (task 013)**: verify 서브명령이 mock 코드 패턴·증거 누락을 검출해 헌법 §4(동작 증거)를 기계적으로 집행한다.
- **행 재구성 (task 014)**: QA Gate/State Gate 행을 제거하고 PM Gate로 통합, gate-pass를 deprecate했다. 이 직후라 pilot STATE 행 일괄 변경은 회귀 위험이 크다 — 015가 CLOSE ingest를 opp 단독 파일럿으로 한정한 근거.

## 인터페이스

`~/.opal/tools/state-tool/run.sh <command> <task-path> [options]` — venv python 래퍼. 출력 JSON `{ok, ...}`, 에러는 ERROR_CODES 카탈로그(31종) 키.

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

`--import-existing` key 재접합 결함 수정 (task:074 — 설계 상세는 [[state-tool-import-existing-key-reattachment]]):
- `cmd_init` import 분기(`parse_existing_state_md`)가 STATE.md 렌더 표(key 컬럼 없음)만 원천으로 삼아 keyless rows를 생성하던 결함을 수정했다. `--force`가 이 keyless rows로 기존 state.json(key 보유)을 덮어써 schema_version이 "1.1"→"1.0"으로 강등되고 `--task-step`/`--task-step-id` 주소가 전면 불능이 되는 2차 파급이 있었다.
- 신규 헬퍼 `_key_source_index`·`_reattach_import_keys`가 (stage,item) 순서 소비 매칭으로 keyless import 행에 기존 state.json(1순위) → `--rows-from` pipeline.json(2순위, 폴백) 순으로 key를 재접합한다. 두 원천 모두 없으면 keyless 유지 + stderr 경고(하위호환, stdout 불변).

## 관련 페이지

- [[brain-tool]] — state-tool 패턴(run.sh+venv python, ERROR_CODES, KST date.js)을 복제한 동형 도구
- [[opal-brain-system]] — brain의 집행 철학이 state-tool에서 유래
- [[clarification-gate]] — task:005에서 추가된 verify --clarification-check 게이트 상세
- [[state-tool-task-step-key-address]] — task:070 task-step 키 주소 체계 아키텍처 결정
- [[pipeline-json-spec]] — task:070 pilot 파이프라인 정의 SSOT(pipeline.json)
- [[state-tool-next-action-auto-derivation]] — task:072 "다음 액션" 자동 파생 설계 반전
- [[state-tool-import-existing-key-reattachment]] — task:074 import-existing key 재접합 결함 수정 설계
