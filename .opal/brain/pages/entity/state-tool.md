---
type: entity
title: state-tool
module: state_tool
layer: util
domain: opal-pipeline
exports: [cmd_init, cmd_show, cmd_advance, cmd_mark, cmd_block, cmd_validate, cmd_add_row, cmd_status, cmd_gate_pass]
source_ref: opal/tools/state-tool/state_tool.py
header_synced: 2026-06-10
tags: [tool, pipeline]
sources: [code:opal/tools/state-tool/, task:013, task:014, task:005]
related: [brain-tool, opal-brain-system, clarification-gate]
created: 2026-06-10
updated: 2026-06-16
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

## 관련 페이지

- [[brain-tool]] — state-tool 패턴(run.sh+venv python, ERROR_CODES, KST date.js)을 복제한 동형 도구
- [[opal-brain-system]] — brain의 집행 철학이 state-tool에서 유래
- [[clarification-gate]] — task:005에서 추가된 verify --clarification-check 게이트 상세
