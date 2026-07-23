# TASK: state-tool `--import-existing` task-step key 유실 결함 수정

> 작성일: 2026-07-23 | 작업 유형: 오류(FW 결함) | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청(태스크 073 진행 중 발견한 FW 도구 결함 에스컬레이션)
> 출력: TASK.md

## 작업 목표

`state-tool init --import-existing`가 기존 task-step key를 전부 유실시키는 결함을 수정하여, import 복구 경로가 070 도입한 `--task-step` 주소 체계를 깨뜨리지 않도록 한다.

## 배경

태스크 073 진행 중, 캡틴이 `state-tool init --force --import-existing` 호출 시 task-step key가 전부 사라지는 현상을 발견하고 에스컬레이션했다. `--task-step`/`--task-step-id` 주소가 전면 불능이 되며, 회피책(`--import-existing` 없이 fresh init + 상태 수동 복원)으로만 우회 가능했다.

## 배경 분석 (대화에서 도출)

PM이 `opal/tools/state-tool/state_tool.py`를 직접 분석하여 근본 원인을 확정했다.

- **원인**: `cmd_init`의 import 경로가 rows를 STATE.md 마크다운 표에서 재파싱한다 — `state_tool.py:900~904` → `parse_existing_state_md` (`state_tool.py:819`).
- **lossy projection**: 렌더 표 컬럼은 `| # | 단계 | 항목 | 상태 | 시점 |` (`state_tool.py:271`)로 **key 컬럼이 없다**. 070이 도입한 `key`는 state.json/pipeline.json에만 존재하고 STATE.md에는 렌더되지 않는다.
- **결과**: `parse_existing_state_md`가 생성하는 rows는 전부 keyless → `--force`가 기존 state.json(key 보유)을 keyless rows로 덮어씀.
- **2차 파급**: keyless rows → `schema_version` "1.1"→"1.0" 강등 (`state_tool.py:932`), `--task-step`/`--task-step-id` 주소 전면 불능 (070 기능 무력화, ERROR `task_step_not_found`).
- **정상 경로 대비**: `build_rows_from_pipeline_json`은 key를 정상 주입 (`state_tool.py:795`) — 캡틴 회피책이 유효한 이유.
- **설계 결함 본질**: `--import-existing`의 복구 원천을 lossy한 렌더 표에 둔 것. 권위 원천(기존 state.json 또는 pipeline.json 스펙)에서 key를 재접합해야 한다.

## 확정된 설계 방향 (대화에서 합의)

PM 권고안 = **key-보존 import**. import 파싱 후 key를 우선순위로 재접합한다.

1. 기존 state.json 존재 → row 매칭(row_id 및/또는 stage+item)으로 key 계승 (`--force --import-existing` 케이스 직접 해소)
2. `--rows-from <pipeline.json>` 동반 시 → stage+item 매칭으로 key 재도출
3. 둘 다 없으면 keyless 유지 + 경고 (하위호환)

> 우선순위 매칭 키(row_id vs stage+item)와 schema_version 승격 처리 등 세부 알고리즘은 PLAN에서 확정한다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `--import-existing` 복구 경로가 기존 task-step key를 보존하도록 수정 | - | `state_tool.py:900~904` 결함 |
| 범위 | 포함: `cmd_init` import 경로 key 재접합 로직 + 회귀 방지 테스트. 제외: STATE.md 렌더 표에 key 컬럼 추가(별도 UX 결정), 070 주소 체계 자체 변경 | key 매칭 알고리즘 세부는 PLAN 확정 | - |
| 제약 | 하위호환 유지(key 원천 부재 시 기존 keyless 동작 보존), state_tool.py 단일 파일 수정 원칙, 변경이력·@header 규칙 준수 | - | PRINCIPLES §3 surgical |
| 완료기준 | (1) `init --force --import-existing` 후 기존 key 100% 보존 (2) key 보존 시 schema_version "1.1" 유지 (3) key 원천 부재 시 keyless + 경고(하위호환) (4) RED-first 회귀 테스트 신규 추가·GREEN (5) 기존 테스트 전량 통과 | - | - |

## 요구사항

- [ ] **무엇을**: `--import-existing` 경로에서 keyless 파싱 후 기존 state.json의 key를 row 매칭으로 재접합 / **어디에**: `state_tool.py` `cmd_init` import 분기 / **왜**: 배경 분석 원인 §1 / **AC**: 기존 state.json(key 보유) 존재 시 `init --force --import-existing` 결과 rows의 key가 원본과 100% 일치
- [ ] **무엇을**: `--rows-from <pipeline.json>` 동반 시 stage+item 매칭으로 key 재도출(state.json 부재 폴백) / **어디에**: `state_tool.py` `cmd_init` import 분기 / **왜**: 확정 방향 §2 / **AC**: state.json 없이 `--import-existing --rows-from pipeline.json` 실행 시 key가 스펙 기준으로 복원됨
- [ ] **무엇을**: key 원천이 전무하면 기존 keyless 동작 + 경고 1줄 / **어디에**: `state_tool.py` `cmd_init` import 분기 / **왜**: 하위호환 / **AC**: state.json·pipeline.json 모두 없을 때 keyless rows 생성 + stderr 경고, 기존 테스트 불변
- [ ] **무엇을**: key 보존 시 schema_version "1.1" 유지 확인 / **어디에**: `state_tool.py:932` 승격 로직 검증 / **왜**: 2차 파급 차단 / **AC**: key 보존된 import 결과 state.json의 schema_version == "1.1"
- [ ] **무엇을**: RED-first 회귀 테스트 추가 / **어디에**: `opal/tools/state-tool/tests/test_state_tool.py` / **왜**: 완료기준 (4) / **AC**: 수정 전 FAIL(RED) → 수정 후 PASS(GREEN), 기존 테스트 전량 통과

## 제약 조건

- **surgical**: `state_tool.py` 단일 파일 + 테스트 파일만 수정. 인접 로직 개선 금지 (PRINCIPLES §3).
- **하위호환**: key 원천 부재 시 기존 keyless 복구 동작을 그대로 보존.
- **배포 경계**: `~/.opal/` 직접 편집 금지 — 프로젝트 소스(`opal/tools/state-tool/`) 수정 후 install 재배포는 별도 캡틴 승인 사항.
- **추적성**: state_tool.py DESCRIPTION 변경이력에 태스크 074 항목 추가.

## 기술 스택

- Python 3 (state-tool CLI, `state_tool.py` 표준 라이브러리 기반)
- pytest (`tests/test_state_tool.py`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 결함 위치·수정 대상 |
| D-2 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | 회귀 테스트 추가 대상 |
| D-3 | 설계 | 070 태스크 PLAN | `tasks/070-260720-opd-태스크스텝-키주소-1차/PLAN.md` | task-step key 주소 체계 원설계 |
