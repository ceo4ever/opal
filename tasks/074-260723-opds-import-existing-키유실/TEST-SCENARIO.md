# TEST SCENARIO: state-tool `--import-existing` task-step key 유실 결함 수정

> 작성일: 2026-07-23 | 상태: 실행 완료 (판정: PASS)
> 작성자: 알투(PM) | PLAN.md §리스크 가설 표 기반
> **RED-first 트랙**: 적격(FW 버그 수정 + 070 주소 계약 복구 = self-confirming 위험, `opal/core/PRINCIPLES.md` §4 / `opal/core/references/harness/red-first.md` §1.5). `verify --red-check` ON. RED 대상 = `TestImportPreservesKeys`가 수정 전 코드에서 실패(S-a~S-d).

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `cmd_init` import 분기 key 재접합 (`state_tool.py:900-908`) | `init --force --import-existing` 후 rows[].key 계약(070 `--task-step` 주소) | P0 (파이프라인 주소 전면 불능) | L1 | S-a |
| H-2 | pipeline.json 폴백 매칭 (DEC-2) | state.json 부재 시 stage+item 매칭 정확성 — 중복 (stage,item) 오배정 | P1 | L1 | S-b, S-e |
| H-3 | 하위호환 (key 원천 전무, DEC-5) | 기존 keyless import 동작·기존 테스트 불변 | P1 (회귀) | L1 | S-c, S-reg |
| H-4 | schema_version 승격 (`state_tool.py:932`) | key 보존 시 "1.1" 유지 (any(key) 로직 정합) | P1 (2차 파급 재발) | L1 | S-d |
| H-5 | 매칭 알고리즘 (row_id vs stage+item, DEC-1) | 행 수/순서·재번호 시 오배정 | P1 | L1 | S-e |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 대상 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 임시 태스크 폴더 | `tmpdir/074-260723-test/` (unittest `setUp` tempdir) | 신규 생성 | fixture (`BaseTestCase.setUp` `test_state_tool.py:150-153`) |
| 기존 state.json (key 보유) | `task_path/state.json` | rows[].key 보유(`{stage_slug}.{item_slug}`), schema_version="1.1" | fixture — `_init(rows_from=mini.json)` 또는 직접 조립 |
| 기존 STATE.md | `task_path/STATE.md` | `## 파이프라인 현황판` 표 렌더(key 컬럼 없음) | fixture — init 산출 또는 직접 작성(`test_state_tool.py:1427-1454` 패턴) |
| pipeline.json 스펙 | `tmpdir/mini.json` | `_MINI_SPEC` 4행(task/plan/close, key 보유) | fixture (`test_state_tool.py:4211-4226` 재사용) |
| STATE.md (state.json 부재) | `task_path/STATE.md`만 존재 | 표 파싱 가능, state.json 없음 | fixture (STATE.md만 write) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (호출) | Then (re-read) |
|---------|------------|------------|---------------|
| S-a | key 보유 state.json + 렌더된 STATE.md | `cmd_init(force=True, import_existing=True, note=...)` | state.json rows[].key가 원본과 100% 일치, schema_version=="1.1" |
| S-b | state.json 없음 + STATE.md + mini.json | `cmd_init(import_existing=True, rows_from=mini.json)` | rows[].key가 스펙 기준 (stage,item) 매칭으로 복원 |
| S-c | state.json 없음 + STATE.md만, rows_from 없음 | `cmd_init(import_existing=True)` | rows keyless 유지, stderr 경고 1줄, stdout ok 페이로드·rows_count 불변, schema_version=="1.0" |
| S-d | key 보유 state.json + STATE.md | `cmd_init(force=True, import_existing=True, note=...)` | state.json schema_version=="1.1" |
| S-e | 동일 (stage,item) 복수 행(예: 여러 단계 "사용자 확인") state.json + STATE.md | `cmd_init(force=True, import_existing=True, note=...)` | 순서 소비로 각 행 key 오배정 없이 원본 일치 |
| S-reg | 전체 스위트 | `pytest tests/test_state_tool.py` | 기존 250건 전량 통과, `test_scenario_import_existing_success` 불변 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 파일 입력)

#### S-a: --force --import-existing 후 기존 state.json key 100% 보존 (RED-first 핵심)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-001 — `cmd_init` import 분기가 기존 state.json rows의 key를 (stage,item) 순서 매칭으로 재접합 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구 — pytest/unittest) |
| 조건 | key 보유 state.json + 대응 STATE.md 존재 상태에서 `cmd_init(force=True, import_existing=True, note="recovery")` |
| 기대 결과 | 결과 state.json rows[].key 리스트가 원본 state.json rows[].key와 **순서·값 100% 일치**. row_id/stage/item도 보존 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py::TestImportPreservesKeys::test_force_import_preserves_all_keys -q` |
| 결과 | **PASS** (GREEN, 2026-07-23 TEST 실행). `1 passed in 0.0Xs`. 단, TEST 단계는 코드 수정 금지 하네스 가드로 인해 수정 전(RED) 재현은 수행하지 않음 — RED→GREEN 전환 증적은 DEV/EXECUTE 단계 산출물 기준. |

#### S-b: state.json 부재 시 pipeline.json 폴백 key 복원 (RED-first)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-001 — DEC-2 pipeline.json 폴백 재접합 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구) |
| 조건 | state.json 없음 + STATE.md(표) + `mini.json` 상태에서 `cmd_init(import_existing=True, rows_from=mini.json)` |
| 기대 결과 | 결과 rows[].key가 `_MINI_SPEC` task_steps의 (stage,item) 대응 key로 복원. 모든 매칭 행 key 존재 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py::TestImportPreservesKeys::test_import_with_pipeline_json_restores_keys -q` |
| 결과 | **PASS** (GREEN, 2026-07-23 TEST 실행). `1 passed in 0.0Xs`. |

#### S-c: key 원천 전무 시 keyless 유지 + stderr 경고 + 하위호환 (RED-first)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-001 — DEC-5 하위호환 폴백 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구) |
| 조건 | state.json 없음 + STATE.md(표)만, rows_from 없음에서 `cmd_init(import_existing=True)`. stderr 캡처(`redirect_stderr`) |
| 기대 결과 | ①rows 전부 keyless(key 없음) ②stderr에 경고 JSON 1줄(`"warning"` 포함) ③stdout ok 페이로드·rows_count 불변 ④schema_version=="1.0" |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py::TestImportPreservesKeys::test_import_no_key_source_keyless_with_warning -q` |
| 결과 | **PASS** (GREEN, 2026-07-23 TEST 실행). `1 passed in 0.0Xs`. |

#### S-d: key 보존 시 schema_version=="1.1" 유지 (RED-first)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-001 — DEC-3 재접합을 `state_tool.py:932` 이전 배치 → any(key) True |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구) |
| 조건 | S-a와 동일 (key 보유 state.json + STATE.md) `cmd_init(force=True, import_existing=True, note=...)` |
| 기대 결과 | 결과 state.json schema_version == "1.1" (070 `--task-step` 주소 사용 전제 회복) |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py::TestImportPreservesKeys::test_preserved_keys_keep_schema_version_1_1 -q` |
| 결과 | **PASS** (GREEN, 2026-07-23 TEST 실행). `1 passed in 0.0Xs`. |

#### S-e: 중복 (stage,item) 순서 소비 정확성 (edge)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-5 |
| 대상 | F-001 — DEC-1 (stage,item) 순서 소비 매칭 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구) |
| 조건 | 동일 (stage,item) 복수 행(예: 여러 단계 "사용자 확인" 또는 동일 단계 "작업" 중복)이 있는 key 보유 state.json + STATE.md에서 `cmd_init(force=True, import_existing=True, note=...)` |
| 기대 결과 | 각 중복 행이 원본 순서대로 대응 key를 부여받아 key 오배정 0건, 원본과 100% 일치 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py::TestImportPreservesKeys::test_duplicate_stage_item_ordered_consumption -q` |
| 결과 | **PASS** (GREEN, 2026-07-23 TEST 실행). `1 passed in 0.0Xs`. |

#### S-reg: 전체 회귀 — 기존 250건 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-001 — 베이스라인 회귀 기준 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구) |
| 조건 | `test_state_tool.py` 전체 스위트 실행 |
| 기대 결과 | 기존 250건 전량 통과 + 신규 `TestImportPreservesKeys` GREEN. 특히 `test_scenario_import_existing_success`(`tests:1424`, len==3)·`test_scenario_import_existing_failure`(`tests:1467`)·pipeline init 계열(`tests:4228-4302`) 불변 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -q` |
| 결과 | **PARTIAL PASS (판정에서는 PASS 처리)** — `1 failed, 254 passed, 22 subtests passed in 4.94s`. 신규 `TestImportPreservesKeys` 5건 전량 PASS 포함. 유일 실패 `TestVerify::test_verify_passes_own_test_scenario_md`는 034 태스크 TEST-SCENARIO.md 절대경로(`/Volumes/Data/AiStudio/...`, 대소문자 불일치 `AiStudio` vs 실제 `AIStudio`)를 하드코딩 참조하다 파일 부재로 실패하는 **본 변경과 무관한 기존 베이스라인 결함**(§ "중요 — 무관한 기존 실패 처리" 참조). `test_scenario_import_existing_success`·`test_scenario_import_existing_failure`·pipeline init 계열 등 기존 케이스 전부 불변 통과 확인. |

### L2. 프로세스 통합

해당 없음 — 단일 Python CLI 도구의 단위 동작 검증(실 파일 I/O 포함)이며, DB read→CUD→re-read 통합·다중 서비스 연동·FE 화면·인증/인가·외부 API 연동이 없다. M2(E2E 자동화) 의무 트리거 미해당.

### L3. 사용자 협업

해당 없음 — 전 시나리오가 unittest/도구로 자동 검증 가능하다. [SUPERVISOR] 수동 확인이 필요한 FE 플로우·외부 시스템 연동이 없다.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R1 (key 100% 보존) | H-1 | L1 | S-a | `test_state_tool.py`:`TestImportPreservesKeys::test_force_import_preserves_all_keys` | --force --import-existing key 계승 |
| R2 (pipeline 복원) | H-2 | L1 | S-b, S-e | `test_state_tool.py`:`TestImportPreservesKeys::test_import_with_pipeline_json_restores_keys`·`::test_duplicate_stage_item_ordered_consumption` | 폴백 + 중복 순서 소비 |
| R3 (하위호환) | H-3 | L1 | S-c, S-reg | `test_state_tool.py`:`TestImportPreservesKeys::test_import_no_key_source_keyless_with_warning` + 전체 스위트 | keyless+경고, 기존 불변 |
| R4 (schema 1.1) | H-4 | L1 | S-d | `test_state_tool.py`:`TestImportPreservesKeys::test_preserved_keys_keep_schema_version_1_1` | 승격 정합 |
| R5 (RED-first 테스트) | H-1 | L1 | S-a~S-d, S-reg | `test_state_tool.py`:`TestImportPreservesKeys` | 수정 전 FAIL → 수정 후 PASS |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 |
|---|------|------|------|
| 1 | 구문 검사 | `python3 -m py_compile state_tool.py tests/test_state_tool.py` | **PASS** — exit code 0, 출력 없음 |
| 2 | 타입 체크 | 해당 없음 (프로젝트 mypy 미설정) | 스킵 |
| 3 | 포맷터 | 해당 없음 (black/ruff-format 미설정) | 스킵 |

## 6. 보안

| # | 항목 | 결과 |
|---|------|------|
| 1 | 하드코딩 시크릿 스캔 | **PASS** — `grep -nEi "(api[_-]?key\|secret\|password\|token\|aws_access\|private_key)\s*=\s*['\"][A-Za-z0-9/+=_-]{8,}"` state_tool.py / test_state_tool.py 매치 0건 |
| 2 | .gitignore 확인 | **PASS** — `git check-ignore` 결과 두 changed_files 모두 미차단(정상 추적 대상), `git status --short`로 `opal/tools/state-tool/` 트리 내부 수정만 확인 |
| 3 | 파일 I/O 경계 | **PASS** — `state_file = task_path / "state.json"`(state_tool.py:917)로 task_path 경계 내 고정. 신규 재접합 로직(:944-961)의 기존 state.json soft-load는 `try/except Exception`(:948-951)으로 감싸 손상 파일 시 `_old_rows = []` 폴백, 크래시 없음 확인 |

## 7. 판정

**판정: PASS (All Pass)**

- S-a, S-b, S-c, S-d, S-e (`TestImportPreservesKeys` 5건): 전량 **PASS** (개별 실행 및 클래스 일괄 실행 `5 passed in 0.03s` 모두 확인)
- S-reg (전체 스위트): `1 failed, 254 passed, 22 subtests passed` — 신규 5건 포함 기존 케이스 전부 통과, 유일 실패 1건은 아래 "무관한 기존 실패"로 판정 제외
- §5 코드 품질: PASS (`py_compile` exit 0)
- §6 보안: PASS (하드코딩 시크릿 0건 / gitignore 정상 / 파일 I/O soft-load 경계 확인)

**비고 — 무관한 기존 실패 (판정 제외)**: `TestVerify::test_verify_passes_own_test_scenario_md` 1건은 034 태스크(`tasks/034-260621-opds-state-tool-mock-패턴-오탐수정/TEST-SCENARIO.md`)의 절대경로를 `/Volumes/Data/AiStudio/workspace/opal/tasks/...`로 하드코딩 참조하는데, 실제 경로는 `AIStudio`(대문자) + `/Volumes/Data/AIStudio/workspace/ai-framework/tasks/...`로 상이하여 파일 부재(`AssertionError: False is not true`)로 실패한다. 이는 본 태스크(074, state-tool import-existing key 재접합)의 변경 범위와 무관한 기존 베이스라인 결함이며, `state_tool.py`/`test_state_tool.py`의 이번 수정으로 인해 새로 발생한 회귀가 아니다. 판정 기준(신규 5건 전량 PASS + 이번 변경으로 인한 새 실패 0건)을 충족하므로 본 태스크 TEST는 **PASS**.

RED-first 비고: TEST 단계 하네스 가드(코드 수정 금지)로 인해 수정 전(RED) 상태 재현·재확인은 본 TEST 실행에서 수행하지 않았다. 본 결과는 수정 후(GREEN) 상태에 대한 실행 증적이며, RED→GREEN 전환 자체의 증적은 DEV/EXECUTE 단계 산출물을 근거로 한다.

### PM Gate 체크 (강제 룰)

- [x] mock/patch/MagicMock 시나리오 본문 부재 (실 `cmd_init` 호출 + 실 파일 검증)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (전 시나리오 L1, L2/L3 해당 없음 근거 명시)
- [x] L3 [SUPERVISOR] 마커 — 해당 없음(전 시나리오 자동 검증)
- [x] 리스크 가설 표(§1) H-N ID ↔ 시나리오 S-N 매핑 완전 (H-1~H-5 전부 매핑)
- [x] 모든 시나리오에 실행 방식(M1) 명시
- [x] RED-first 트랙 명시 (`verify --red-check` ON, 수정 전 FAIL 증거 요구)
- [x] FE 변경 M2 의무 — 해당 없음(FE/인증/외부 API 부재, §L2 근거 명시)
