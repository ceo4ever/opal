# TEST SCENARIO: state-tool task-step 키 주소 체계 도입 1차

> 작성일: 2026-07-20 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반
> **RED-first 트랙: 적용(강제)** — 근거: state-tool은 파이프라인 게이트 계약(비즈니스 로직)이며 CLI 공개 인터페이스 계약 변경(red-first.md §1.5 "비즈니스 로직·API 계약" 해당). RED 작성자: opal-test-agent(mode: red) — EXECUTE 구현 워커와 분리(§2). EXECUTE(GREEN) 진입 전 `verify --red-check` 게이트 통과 필수.

## 1. 리스크 가설 표

PLAN.md §리스크 가설 표(H-1~H-8)를 입력으로 사용한다. 매핑은 §4 참조.

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 데이터 | 값/생성 방법 |
|--------|-------------|
| 임시 태스크 폴더 | `tempfile.mkdtemp()` (BaseTestCase 관례) + STATE.md 마커 포함 |
| 유효 스펙 4종 | `opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe}/references/pipeline.json` (Step 8 산출물 — 실파일) |
| 위반 스펙 3종 | 임시 파일로 생성: key 중복 / key 형식 위반(`Plan.PM_Gate`) / stage enum 외(`FOO`) |
| 레거시 state.json | `.md` 파싱 init으로 생성한 1.0(key 없음) 실파일 |

### 2.2 시나리오별 데이터 흐름

json init → state.json(1.1, key 有) → mark/advance/block 3주소 갱신 → add-row 재정렬 → validate. 레거시 흐름은 md init → 1.0(key 無) → --row 갱신 → validate.

## 3. 검증 시나리오

> 실행 방식: 전 시나리오 **M2(테스트 코드 자동)** — `test_state_tool.py` 신규 클래스(L1: cmd 직접 호출 / L2: run.sh subprocess). [SUPERVISOR] L3 시나리오 없음(사용자 협업 불요 — 전부 CLI 관찰 가능).
> 실행 명령(DEC-3): `~/.opal/.venv/bin/python -m unittest discover -s opal/tools/state-tool/tests -p 'test_*.py'`

### L1. 기능 단위 (자동, 실 데이터 입력)

| ID | 가설 | Given | When | Then | 결과 |
|----|------|-------|------|------|------|
| S-1 | H-4 | 그룹 A 스펙 4종 실파일 | `init --rows-from references/pipeline.json` (4회) | 행 수 9/15/10/9 일치 + 전 행 `key` 존재 + opdw 3~5행 `conditional:true` 저장(자동 na 없음 — DEC-1) | PASS |
| S-2 | H-1 | json init 완료 state.json | 동일 행을 `--task-step plan.pm_gate` / `--task-step-id 4` / `--row 4`로 각각 mark | 3방식 모두 동일 행 갱신·동일 응답(row_id=4) | PASS |
| S-3 | H-1 | 존재하지 않는 key | `mark --task-step plan.qa_gate` | `task_step_not_found` + 후보 목록 포함 + exit 1 | PASS |
| S-4 | H-3 | key 有 1.1 + key 無 1.0 state.json 각 1건 | `validate` 각각 실행 | 둘 다 ok:true (violations 0) | PASS |
| S-5 | H-5 | json init 후 TEST 단계 | `add-row --after N --stage TEST --item 'fix 작업'` 2회 (--key 미지정) | 자동 key `test.fix_1`·`test.fix_2` 부여, 기존 43행 key 불변, row_id만 재정렬 | PASS |
| S-6 | H-5 | 기존 key와 동일한 `--key` 지정 | `add-row --key plan.pm_gate` | 중복 거부 에러 + exit 1 | PASS |
| S-7 | - (R-1/R-6) | 유효 스펙 + 위반 스펙 3종 | `spec-validate` 4회 | 유효=ok:true, 위반 3종 각각 구분된 에러 코드(중복/형식/stage) | PASS |
| S-8 | H-6 | enum 정정 코드 | `init --skill opdd` + `add-row --stage DICT` | 거부 해소 — enum 에러 없이 동작 | PASS |
| S-9 | - (R-5) | mark 대상 EXECUTE 행 | `--action-step 2/6`과 `--step 2/6` 각각 | 동일 동작(N<M in_progress 유지, N==M done) — 진행률 가드 회귀 0 | PASS |

### L2. 프로세스 통합 (자동, subprocess run.sh 실호출 — argparse 레벨)

| ID | 가설 | Given | When | Then | 결과 |
|----|------|-------|------|------|------|
| S-10 | H-2 | json init 완료 태스크 | 주소 플래그 0개로 `mark --done` | `task_step_addr_required` + exit 1 (조용한 통과 금지) | PASS |
| S-11 | H-2 | 동일 | `--task-step`+`--row` 동시 지정 | `task_step_addr_conflict` + exit 1 | PASS |
| S-12 | H-4 | 그룹 A `.md` 경로 | `init --rows-from <SKILL.md>` | 기존과 동일 결과(1.0 호환) + stderr deprecation 경고 1줄 | PASS |
| S-13 | H-7 | json init(agentic) 파이프라인 완주 직전 | CLOSE 첫 행 `--auto-pass` 시도 → 이후 정상 절차 | `agentic_close_gate_requires_user` 거부 유지 + `--owner user` 후 통과 — CLOSE 게이트 회귀 0 (item 한글 판정 불변) | PASS |
| S-14 | H-1/전체 | 기존 테스트 스위트 | DEC-3 실행기로 전체 실행 | 기존 클래스 무수정 전체 PASS (하위호환 증명) | PASS (기준선 유지 — 239 tests 중 238 PASS + 1 선재 FAIL(TestVerify.test_verify_passes_own_test_scenario_md, 034 폴더 부재로 070 무관·베이스라인 동일 확증)) |

### L3. 사용자 협업 — 해당 없음 (전 시나리오 CLI 자동 관찰 가능)

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| TASK AC | 가설 | 계층 | 시나리오 |
|---------|------|------|---------|
| 완료기준 ① 테스트 전체 PASS | H-1~H-7 | L1+L2 | S-14 |
| 완료기준 ② 그룹 A init+key mark 실증 | H-4, H-1 | L1 | S-1, S-2 |
| 완료기준 ③ opdd 거부 해소 | H-6 | L1 | S-8 |
| 완료기준 ④ --row/--step 별칭 회귀 0 | H-1, H-2 | L1+L2 | S-2, S-9, S-12, S-14 |
| R-1/R-6 spec-validate AC | - | L1 | S-7 |
| R-9 add-row key AC | H-5 | L1 | S-5, S-6 |
| R-3 스키마 1.1 AC | H-3 | L1 | S-4 |
| H-8 (인용 유효성) | H-8 | 산출물 검사 | PM Gate에서 PLAN 인용 확인(완료) |

## GREEN 실행 결과 (opal-test-agent, mode: BE)

### 전체 테스트 스위트

```
~/.opal/.venv/bin/python -m unittest discover -s opal/tools/state-tool/tests -p 'test_*.py'
```

- `Ran 239 tests in 4.019s` → `FAILED (failures=1)` → **238 PASS + 1 FAIL**
- 1 FAIL = `TestVerify.test_verify_passes_own_test_scenario_md`(034 TEST-SCENARIO.md 폴더 부재) — RED 증거 §④에서 070 이전에도 동일하게 존재함이 확증된 선재(pre-existing) 실패. 070 변경과 무관.
- 기대 기준선(238 PASS + 1 FAIL) **정확히 일치** → 신규 32개 메서드 전부 GREEN 전환 확인.

### 추가 실증 (문서 기록용)

1. `bash opal/tools/state-tool/run.sh spec-validate opal/skills/opal-pilot-dev/references/pipeline.json` → `{"ok": true, "command": "spec-validate", "violations": [], "violations_count": 0}` — ok:true 확인.
2. 임시 폴더 스모크: `init --skill opd --mode agentic --rows-from opal/skills/opal-pilot-dev/references/pipeline.json <tmp>` → `rows_count: 15` 정상 생성 → `mark --task-step plan.plan_md <tmp> --done` → key `plan.plan_md`를 정확히 row_id=6(pipeline.json 정의와 일치)으로 해석 → 이후 `stage_transition_violation`(앞 행 1,3,4 미완료)로 거부. 이는 기존 stage-transition guard의 정상 동작이며, 핵심 검증 대상인 **key→row 해석(H-1)이 정확히 동작**함을 실측 확인. 임시 폴더는 검증 후 삭제 완료.

## 5. 코드 품질

- [x] 문법/실행 오류 없음 — `python3 -m py_compile opal/tools/state-tool/state_tool.py` → 오류 없음.
- [x] 기존 테스트 케이스 무수정 — `git diff --stat`: test_state_tool.py 993 insertions / 6 deletions. 6개 삭제 라인 전수 확인 결과 ① @header description 070 요약 추가 ② test_classes 목록에 신규 9클래스 append ③ `test_error_codes_count`/`test_all_28_codes_registered` 2개 메서드의 EXPECTED_CODES 카운트(31→39, 070 신규 8종 반영) 갱신뿐 — 승인 범위(2개 메서드+EXPECTED_CODES) 외 기존 케이스 변경 없음(추가만 허용 원칙 충족).
- [x] @header 메타블록 갱신 — state_tool.py 상단 description에 "070: task-step 키 주소 체계 도입 1차 — spec-validate 서브명령... ERROR_CODES 8종 추가" 반영 확인. 코드 내 070 주석 마킹 다수(spec-validate, resolve_row_index, add-row --key 등) 확인.

## 6. 보안

- [x] 시크릿/자격증명 노출 없음 — changed_files 전체(state_tool.py, schema/*.json, README.md, SKILL.md 4종, references/pipeline.json 4종, test_state_tool.py, docs/CONVENTIONS.md) grep `api[_-]?key|secret|token|password` 실행 결과, "key" 매칭은 전부 task-step 키 주소 체계(feature 자체의 `key`/`--key`/`item_slug` 등) 관련이며 시크릿·자격증명 패턴 0건.
- [x] 경로 주입 방어 — `load_pipeline_spec()`(state_tool.py:664)이 `pathlib.Path(spec_path)`로 처리하며, 기존 `--task-path` 처리(state_tool.py:824, 동일하게 `pathlib.Path(args.task_path)`)와 동일한 resolve 관례를 따름. 셸 실행·eval 등 신규 인젝션 표면 없음.

## 7. 판정

**전 시나리오 PASS (S-1~S-14, S-14는 기준선 유지로 PASS) + 코드 품질 3/3 충족 + 보안 2/2 충족 → All Pass.**

- 회귀 FAIL 없음: 기존 207개 테스트 중 070 이전부터 존재하던 1건(TestVerify, 034 폴더 부재)을 제외하고 전부 PASS, 070으로 인한 신규 회귀 0건.
- 신규 기능(spec-validate, task-step 3주소, add-row --key, opdd enum, --action-step 별칭) 32개 RED 메서드 전부 GREEN 전환.

## RED 증거

> 작성: opal-test-agent(mode: red) | 대상: `opal/tools/state-tool/tests/test_state_tool.py` (신규 클래스 9종 추가, 기존 클래스·케이스 무수정) | 하네스: `opal/core/references/harness/red-first.md` §1·§2·§4

### ① 실행 명령

```
~/.opal/.venv/bin/python -m unittest discover -s opal/tools/state-tool/tests -p 'test_*.py'
```

### ② 실패 요약 (신규 클래스별 FAIL/ERROR/SKIP 수 — 테스트 메서드 단위, subTest fan-out 제외)

| 클래스 | 메서드 수 | FAIL | ERROR | SKIP | 커버 시나리오 |
|--------|----------|------|-------|------|--------------|
| TestPipelineSpecValidate | 6 | 1 | 5 | 0 | S-7 |
| TestPipelineJsonInit | 3 | 2 | 1 | 0 | S-1 |
| TestStateSchema11Compat | 4 | 4 | 0 | 0 | S-4 |
| TestTaskStepAddressing | 5 | 5 | 0 | 0 | S-2, S-3, S-10, S-11, S-13 |
| TestActionStepRename | 3 | 3 | 0 | 0 | S-9 |
| TestAddRowKey | 3 | 3 | 0 | 0 | S-5, S-6 |
| TestOpddEnumDrift | 2 | 2 | 0 | 0 | S-8 |
| TestGroupAPipelineSpecs | 3 | 1 | 1 | 1 | S-1 (후반 실파일 서브테스트는 의도된 사전조건 skip — graceful skip 아님, GREEN Step 8 후 활성화) |
| TestBackwardCompatAliases | 3 | 3 | 0 | 0 | S-12 (+ S-9 보강) |
| **합계** | **32** | **24** | **7** | **1** | S-1~S-14 전 커버 |

- 신규 32개 메서드 중 31개가 FAIL/ERROR, 1개는 명시적 skipTest(그룹 A 실파일 부재 — GREEN Step 8 이후 자동 활성화) — **PASS는 0건**으로 정상 RED다.
- unittest 원본 로그의 `FAILED (failures=29, errors=10, skipped=1)`는 subTest(스킬 4종·주소 3방식 등) 전개로 인해 위 표의 메서드 수보다 많게 집계된 값이다(총 239 tests 중 39 non-pass 라인, skip 1).

### ③ 실패 출력 대표 20줄 (원문)

```
======================================================================
FAIL: test_three_way_addressing_same_row_same_result (test_state_tool.TestTaskStepAddressing.test_three_way_addressing_same_row_same_result) (addr='task_step')
[T070/S-2, H-1] 동일 행(row_id=4, plan.pm_gate)을 --task-step/--task-step-id/--row
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../test_state_tool.py", line 4087, in test_three_way_addressing_same_row_same_result
    self.assertEqual(exit_code, 0, f"--task-step mark 실패: {result}")
AssertionError: 1 != 0 : --task-step mark 실패: {'ok': False, 'command': 'mark', 'error': 'row_not_found', 'message': '--row None에 해당하는 행이 state.json에 없음', 'row_id': None}

======================================================================
FAIL: test_task_step_not_found_returns_candidates (test_state_tool.TestTaskStepAddressing.test_task_step_not_found_returns_candidates)
[T070/S-3] 존재하지 않는 key(--task-step plan.qa_gate) → task_step_not_found +
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../test_state_tool.py", line 4108, in test_task_step_not_found_returns_candidates
    self.assertEqual(result.get("error"), "task_step_not_found", ...)
AssertionError: 'row_not_found' != 'task_step_not_found'
 : 미매칭 key인데 task_step_not_found 아님: {'ok': False, 'command': 'mark', 'error': 'row_not_found', 'message': '--row None에 해당하는 행이 state.json에 없음', 'row_id': None}

======================================================================
ERROR: test_all_four_fixtures_spec_validate_ok (test_state_tool.TestGroupAPipelineSpecs.test_all_four_fixtures_spec_validate_ok) (skill='opp')
[T070/S-1] 그룹 A 4종 임시 픽스처 모두 spec-validate ok:true (직접 호출).
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../test_state_tool.py", line 4433, in test_all_four_fixtures_spec_validate_ok
    violations = ST.validate_pipeline_spec(_deepcopy_json(spec))
AttributeError: module 'state_tool' has no attribute 'validate_pipeline_spec'
```

### ④ 기존 테스트 PASS 수

- 기존(070 이전) 테스트: 총 207개, 그중 206개 PASS + 1개 FAIL(`TestVerify.test_verify_passes_own_test_scenario_md` — "034 TEST-SCENARIO.md 파일이 없음").
- 위 1건은 **070 변경과 무관한 사전 존재 실패**임을 `git stash` 후 베이스라인(070 변경 전) 재실행으로 확인함 — 베이스라인도 동일하게 `Ran 207 tests ... FAILED (failures=1)`, 동일 테스트·동일 메시지. `tasks/` 베이스라인 리셋(ANALYSIS §4 발견사항 #3)으로 034 태스크 폴더 자체가 삭제되어 발생한 기존 이슈이며, 본 태스크(070) defaults 추가·신규 클래스와 인과관계 없음 — 070 RED 게이트 대상 아님(별도 이슈로 PM 보고).
- 결론: **기존 테스트는 070 적용 전후 동일하게 206 PASS + 1 pre-existing FAIL**로 회귀 0 확인. `make_args()` defaults 확장(task_step/task_step_id/action_step/key/after_task_step/after_task_step_id)이 기존 테스트에 AttributeError를 유발하지 않음을 실측으로 검증함.
- 전체 실행: `Ran 239 tests ... FAILED (failures=29, errors=10, skipped=1)` (239 = 기존 207 + 신규 32).
