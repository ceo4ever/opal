# TASK: state-tool 다중 Step EXECUTE 행 조기 done 가드

> 작성일: 2026-06-10 | 작업 유형: 수정(버그/가드) | 적용 스킬: opds | 모드: semi-agentic
> 입력: 사용자 요청 (016 후속)
> 출력: TASK.md

## 작업 목표

`state-tool`의 `mark`가 다중 Step이 흡수된 단일 EXECUTE 행에서, **마지막 Step이 아닌데(`--step N/M`, N<M) `--done`을 호출하면 행이 조기 완료**되는 문제를 가드로 차단한다. 진행률은 기록하되 행 완료는 마지막 Step에서만 일어나게 한다.

## 배경

태스크 016 EXECUTE에서, 7개 Step이 단일 행(행 6, EXECUTE 작업)에 흡수되는 opds 구조인데, Batch 1 워커가 `mark --row 6 --done --as-worker --worker-stage EXECUTE --step 1/7`을 호출하자 **Step 1만 끝났는데 EXECUTE 행 전체가 done으로 닫혔다**. `advance`는 done→in_progress를 지원하지 않아 복구도 불가했고, PM이 행을 수동 통제해 보정했다.

## 배경 분석 (대화에서 도출 — 016 AGENTIC-LOG)

- 원인 3겹: ① 직접 — 디스패치 프롬프트가 첫 Step 워커에 `--done`을 지시(PM 측 실수), ② 구조 — opds EXECUTE = 단일 행에 다중 Step 흡수, ③ **도구 갭 — `state-tool`이 `--step N/M`에서 N<M인데 `--done`을 허용**(조기 종료 방지 가드 부재).
- 본 태스크는 ③(도구 갭)을 근본 차단한다. ①은 운영 주의, ②는 설계 특성.
- 현재 `cmd_mark`는 `--step`을 진행률 표시 메타로만 받고 `--done`이면 무조건 행을 done 처리하는 것으로 보임(PLAN에서 코드 확인 필요).

## 확정된 설계 방향 (016에서 식별)

| # | 방향 | 비고 |
|---|------|------|
| C-1 | `--step N/M`에서 N<M + `--done`이면 행을 done으로 닫지 않고 **진행률만 기록(in_progress 유지)** | (a)진행률 유지로 확정 (캡틴 결정) — 기존 stage-transition guard와 자연 연동(행 미완 → 다음 단계 진입 자동 거부) |
| C-2 | 마지막 Step(N=M)에서만 `--done`이 행을 완료 처리 | |
| C-3 | RED-first 자기적용 | 016에서 도입한 트랙 적용 — self-confirming 위험(state-tool 행 상태 로직)이므로 RED-first 강제. 테스트 먼저 실패 확인 후 구현 |
| C-4 | 기존 동작 비파괴 | `--step` 없는 mark, 단일 Step, 비-EXECUTE 행은 기존대로 |
| C-5 | **조기 close 3층 가드 + 진행률 state.json 영속화** (캡틴 결정) | 진행률(`step: "N/M"`)을 state.json 행에 저장하고 ①행done(N==M) ②단계전환 ③CLOSE 진입 3지점에서 진행률 완료를 검증 |

## 요구사항

- [ ] **R-1 (조기 done 가드 + 진행률 영속화)**: `mark`에 `--step N/M`이 주어지고 N<M인데 `--done`이면, 행을 done으로 닫지 않고 진행률만 기록(in_progress 유지)한다.
  - **무엇을**: `cmd_mark`에 `--step` 파싱(N/M) + N<M 분기 + 진행률을 state.json 행에 저장(`step: "N/M"`)
  - **어디에**: `opal/tools/state-tool/state_tool.py`
  - **왜**: C-1, C-5, 배경(016 조기 done)
  - **AC**: `mark --row R --done --step 1/7` 호출 시 행이 **in_progress 유지**(done 아님) + state.json 행에 `step: "1/7"` 저장된다. 단위 테스트 PASS.

- [ ] **R-5 (조기 close 3층 가드)**: 진행률 미완(N<M) 상태에서 단계 전환·CLOSE 진입을 차단한다.
  - **무엇을**: ① 행 done은 N==M에서만(R-1) ② 다음 단계 행 advance/mark 시 직전 다중 Step 행의 진행률 완료 검증 ③ CLOSE 첫 행 진입 시 선행 다중 Step 행 전부 진행률 완료 검증. 신규 ERROR_CODE(예: `premature_stage_advance` 또는 기존 `stage_transition_violation` 확장)
  - **어디에**: `state_tool.py` (advance/mark 단계 전환 로직 + CLOSE 게이트)
  - **왜**: C-5 (캡틴 "조기 close 조건")
  - **AC**: 다중 Step 행이 진행률 미완(예: 1/7)인 상태에서 다음 단계 행 mark/advance → 거부(에러). 진행률 완료(7/7) 후엔 정상 전환. CLOSE 진입도 동일. 단위 테스트로 ①②③ 각각 검증 PASS. 기존 `stage_transition_violation` 동작 비파괴.

- [ ] **R-2 (마지막 Step 완료)**: `--step N/M`에서 N==M + `--done`이면 행이 정상 done 처리된다.
  - **무엇을**: N==M 분기에서 기존 done 동작
  - **어디에**: `state_tool.py`
  - **왜**: C-2
  - **AC**: `mark --row R --done --step 7/7` → 행 done. 단위 테스트 PASS.

- [ ] **R-3 (RED-first 자기적용 + 기존 비파괴)**: 본 가드의 테스트를 먼저 작성(RED)해 실패 확인 후 구현(GREEN). 기존 전체 스위트 비파괴.
  - **무엇을**: RED 테스트 → 구현 → GREEN. 회귀 0.
  - **어디에**: `opal/tools/state-tool/tests/test_state_tool.py` + `state_tool.py`
  - **왜**: C-3, C-4
  - **AC**: 신규 테스트가 미구현 시 실패(RED) → 구현 후 전체 `unittest discover` PASS(기존 165 + 신규). `--step` 없는 mark·단일 Step·비-EXECUTE 행 동작 불변.

- [ ] **R-4 (변경이력)**: `state_tool.py` @header + 관련 문서 변경이력에 017 반영.
  - **AC**: state_tool.py @header에 가드 내용 반영, 변경이력 추적 가능.

## 제약 조건

- **배포 경계**: `~/.opal/` 직접 수정 금지. `opal/tools/state-tool/`만 수정 후 install 재배포.
- **표준 라이브러리만** (T-11): pytest 금지, `unittest` 사용.
- **하위 호환**: 기존 28→30 ERROR_CODES·165 테스트·`--step` 미지정 mark 동작 비파괴.
- **RED-first 강제**: self-confirming 위험 영역(상태 전이 로직)이므로 016 red-first.md 트랙 적용.
- **opds 범위**: 단일 파일(state_tool.py) + 테스트라 Short Task 적합.

## 기술 스택

- Python 3 stdlib (`argparse`/`re`/`unittest`), `opal/tools/state-tool/`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | cmd_mark / --step 처리 / 행 done 로직 |
| D-2 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | mark 테스트 패턴 |
| D-3 | 설계 | RED-first SSOT | `opal/core/references/harness/red-first.md` | 016 도입 트랙 — 자기적용 |
| D-4 | 기획 | 016 DONE/AGENTIC-LOG | `tasks/016-260609-opds-tdd-red-first-track/` | 조기 done 이슈 근거 (#5/#8) |
