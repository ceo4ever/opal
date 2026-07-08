<!-- S-7 시연본 — 개선된 opal-brain SKILL 5섹션 규율로 생성. 실제 brain에 미반영(검토 전용). -->
---
type: entity
title: state-tool
module: state_tool
layer: util
domain: opal-pipeline
exports: [cmd_init, cmd_show, cmd_advance, cmd_mark, cmd_block, cmd_validate, cmd_add_row, cmd_status, cmd_gate_pass]
source_ref: opal/tools/state-tool/state_tool.py
header_synced: 2026-06-23
tags: [tool, pipeline]
sources: [code:opal/tools/state-tool/state_tool.py, ref:opal-harness.md§3, ref:PRINCIPLES.md§4]
related: [brain-tool, clarification-gate]
created: 2026-06-23
updated: 2026-06-23
status: active
---

# state-tool

## 개요

파이프라인 작업의 진행 현황판을 사람도 AI도 손으로 흩뜨리지 못하게, **상태 변경을 단일 도구로만 집행**하는 명령줄 도구다. 작업이 단계를 순서대로 밟았는지, 게이트를 통과했는지, 동작 증거를 갖췄는지를 도구가 결정론적으로 판정하여 통과·거부한다. 사람이 보는 현황판(STATE.md)과 기계가 읽는 상태(state.json)를 한 소스로 일치시키는 것이 역할이다.

## 책임 (WHAT)

- **현황판 초기화** — 태스크 시작 시 현황판과 상태 파일을 생성한다 (`state_tool.py:619`).
- **단계 전이** — 행 상태를 대기→진행→완료로 한 칸씩 옮긴다. 워커 완료·게이트 통과를 행 단위로 기록한다 (`state_tool.py:841`, `state_tool.py:898`).
- **게이트 검증** — 명확화 4요소 잠금·RED 증거·mock 부재·테스트 불변성을 검사한다 (`state_tool.py:1648`).
- **블로커/추가행/상태 조회** — 진행 중단 기록, 추가작업 행 삽입, 현황 조회를 제공한다 (`state_tool.py:1049`, `state_tool.py:1137`, `state_tool.py:1195`).
- **위반 거부** — 정의된 오류 카탈로그 키로 규칙 위반을 거부한다 (`state_tool.py:68`).

## 설계 배경 (WHY)

- 현황판을 사람·AI가 직접 손으로 고치면 행 상태 정합성이 깨지므로, 상태 변경을 도구로만 허용한다 — 헌법의 "Enforce, don't just advise"를 집행하는 지점이다 (근거: `opal-harness.md §3` [MUST] state-tool 사용 의무 / `PRINCIPLES.md` Core Stance).
- 앞 단계 필수 행이 끝나지 않으면 다음 단계 진입을 막는다(단계 건너뛰기 차단) — 파이프라인 순서가 품질을 보장한다는 전제 때문이다 (근거: `opal-harness.md §3` 단계 건너뛰기 차단 / 원설계 task 134 — 태스크 폴더 삭제로 직접 인용 불가).
- 동작 증거 없는 "완료"를 막기 위해 mock 코드 패턴·증거 누락을 검증 단계에서 검출한다 — 헌법 §4(완료는 증거를 요구)를 기계로 집행한다 (근거: `PRINCIPLES.md §4`).
- 워커가 자기 권한을 넘는 행을 완료 처리하지 못하게 권한 경계를 도구가 지킨다 (추론: 코드패턴 — 오류 카탈로그의 `worker_scope_violation` + `--as-worker` 게이트 구조에서 도출).
- 마크다운 표 직접 편집을 원천 차단한 구체적 동기(어떤 사고가 있었는지)는 기록이 남아있지 않다 (WHY 미확보 — task 134 PLAN 폴더 삭제).

## 관계 (HOW)

- [[brain-tool]] — state-tool의 패턴(run.sh + venv python 래퍼, 오류 카탈로그, KST 타임스탬프)을 그대로 복제한 동형 도구다.
- [[clarification-gate]] — 명확화 게이트(verify 서브명령)의 상세 계약을 정의하는 개념 페이지.

## 소스 커버리지

| 심볼 | 경로:줄 | 역할 |
|------|---------|------|
| `cmd_init` | `state_tool.py:619` | 현황판·상태 초기화 |
| `cmd_show` | `state_tool.py:782` | 현황 조회(표 렌더) |
| `cmd_advance` | `state_tool.py:841` | 단계 시작(⬜→🔄) |
| `cmd_mark` | `state_tool.py:898` | 행 완료(→✅) |
| `cmd_block` | `state_tool.py:1049` | 블로커 기록 |
| `cmd_validate` | `state_tool.py:1076` | 구조·정합 검증 |
| `cmd_add_row` | `state_tool.py:1137` | 추가작업 행 삽입 |
| `cmd_status` | `state_tool.py:1195` | current_status 전환 |
| `cmd_gate_pass` | `state_tool.py:1237` | [deprecated] 레거시 게이트 |
| `cmd_verify` | `state_tool.py:1648` | 명확화·RED·mock·불변성 게이트 |
| `ERROR_CODES` | `state_tool.py:68` | 오류 카탈로그 (위반 거부 키) |
| `main` | `state_tool.py:1894` | CLI 엔트리포인트 |
