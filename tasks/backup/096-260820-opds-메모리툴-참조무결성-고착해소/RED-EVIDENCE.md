# RED-EVIDENCE: 096 memory-tool 참조 무결성 + 고아 행 정리 (Step 1)

> 작성: opal-test-agent (mode: red) | PLAN.md §4.2 Step 1 산출물
> [MUST] `opal/core/references/harness/red-first.md` §1 — RED 증거(exit≠0 + 실패 목록) 기록
> 대상 파일(유일 수정): `opal/tools/memory-tool/tests/test_memory_tool.py`
> 구현(GREEN)은 본 워커의 범위가 아니다 — `memory_tool.py`는 1바이트도 수정하지 않았다(red-first.md §2 작성자≠구현자).

---

## 1. 실행 환경

```
인터프리터: ~/.opal/.venv/bin/python (Python 3.14.3)
pytest:     9.1.0
실행 명령:  ~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q
```

## 2. 전체 실행 결과 (stdout 원문 — 요약)

```
$ ~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q
...
=========================== short test summary info ============================
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_qa001_missing_body_detected_in_violations
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_qa003_existing_four_violation_types_unchanged
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_qa004_call_sites_pass_json_path_and_six_commands_detect
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_qa005_traversal_row_reported_as_unresolvable_not_missing
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_ts036_mixed_vocab_review_distinguishes_missing_from_unresolvable
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa006_candidate_orphan_row_cleaned_real_layout_roundtrip
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa007_promoted_orphan_row_cleaned
SUBFAILED(status='active') opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa008_orphan_rejected_when_body_exists_all_statuses
SUBFAILED(status='dead') opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa008_orphan_rejected_when_body_exists_all_statuses
SUBFAILED(status='superseded') opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa008_orphan_rejected_when_body_exists_all_statuses
SUBFAILED(status='promoted') opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa008_orphan_rejected_when_body_exists_all_statuses
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa009_active_body_exists_orphan_rejected_bytes_unchanged
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa010_orphan_without_ref_rejected
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa012_provenance_log_records_reason_ref_and_summary
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa013_orphan_delete_leaves_no_residue_and_show_ok
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa014_single_call_no_status_transition_required
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa024_traversal_with_live_body_outside_memory_rejected
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa025_none_return_three_paths_all_rejected
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa026_ts039_vocabulary_consistency_across_three_commands
SUBFAILED(status='candidate') opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_ts037_orphan_and_promote_reject_regardless_of_status
SUBFAILED(status='dead') opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_ts037_orphan_and_promote_reject_regardless_of_status
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestLifecycleDocParity::test_qa015_lifecycle_table_matches_schema_enum
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestLifecycleDocParity::test_qa016_candidate_row_columns_filled
FAILED opal/tools/memory-tool/tests/test_memory_tool.py::TestLifecycleDocParity::test_qa017_new_error_codes_documented_in_readme_and_toolsmd
24 failed, 169 passed, 25 subtests passed in 21.40s
```

**exit code = 1** (확인 완료 — `echo $?` → 1).

> **[주의] pytest-subtests 리포팅 특성**: `test_qa008_...`와 `test_ts037_...`는 `unittest.TestCase.subTest()`로 4개/2개 하위 케이스를 반복 검증한다. pytest-subtests 9.x는 하위 케이스 실패를 `SUBFAILED` 라인으로 개별 보고하면서 **부모 테스트 노드 자체는 "passed" 그룹에 합산**하는 리포팅 방식을 쓴다(부모 메서드가 예외를 재전파하지 않고 subTest 컨텍스트 안에서 흡수하기 때문). 즉 위 요약의 "169 passed"에는 이 2개 부모 노드가 포함돼 있지만, **실질적으로는 하위 케이스 전부 FAIL이다** — 순수 표준 `unittest` 러너로 재확인했다(§3 참조). RED 판정은 pytest 요약 숫자가 아니라 이 표준 러너 재확인 결과를 근거로 한다.

## 3. `unittest` 표준 러너로 재확인 (pytest-subtests 리포팅 왜곡 배제)

```
$ ~/.opal/.venv/bin/python -m unittest \
    opal.tools.memory-tool.tests.test_memory_tool.TestDeleteOrphan.test_qa008_orphan_rejected_when_body_exists_all_statuses -v
...
FAILED (failures=4)

$ ~/.opal/.venv/bin/python -m unittest \
    opal.tools.memory-tool.tests.test_memory_tool.TestDeleteOrphan.test_ts037_orphan_and_promote_reject_regardless_of_status \
    opal.tools.memory-tool.tests.test_memory_tool.TestDeleteOrphan.test_ts038_no_flag_delete_allows_dead_unresolvable_row \
    opal.tools.memory-tool.tests.test_memory_tool.TestDeleteOrphan.test_qa011_no_flag_delete_still_requires_dead_or_superseded \
    opal.tools.memory-tool.tests.test_memory_tool.TestLifecycleDocParity.test_qa018_existing_four_rows_text_unchanged \
    opal.tools.memory-tool.tests.test_memory_tool.TestReviewReferenceIntegrity.test_qa002_no_false_positive_when_bodies_intact -v
...
Ran 5 tests in 0.308s
FAILED (failures=2)   ← ts037의 2개 subTest(candidate/dead)만 실패, 나머지 4개 테스트는 통과
```

결론: `test_qa008_...`(4/4 subTest 실패), `test_ts037_...`(2/2 subTest 실패) 모두 **실질 RED**다.

## 4. 신규 케이스 수 / RED 수 / 기존 통과 수 / 전체 collected 수

| 항목 | 수치 |
|------|------|
| 전체 collected (`--collect-only`) | **187** (기존 163 + 신규 24) |
| 신규 케이스 수 | **24** |
| 신규 케이스 중 RED(FAIL) | **20** |
| 신규 케이스 중 PASS(불변식 가드/하위호환 — 아래 §6 근거) | **4** |
| 기존 163건 회귀 | **0건** — 아래 §5로 별도 재확인 |
| 기존 25 subtests 회귀 | **0건** — 그대로 25 유지 |

케이스 수 감소 없음(24 신규 순증) — 삭제로 GREEN을 만들지 않았음을 수량으로 확인.

## 5. 기존 163건 무변경 재확인 (신규 3클래스 배제 실행)

```
$ ~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q \
    -k "not TestReviewReferenceIntegrity and not TestDeleteOrphan and not TestLifecycleDocParity"
163 passed, 24 deselected, 25 subtests passed in 18.52s
```

PLAN.md §5.2 기준선(`163 passed / 25 subtests passed`)과 **완전 일치** — 기존 테스트 0건 수정·삭제 확인.

## 6. 신규 케이스별 RED/PASS 분류 + 실패 사유

> [MUST] `docs/CONVENTIONS.md`/PLAN 완료 기준 (4): 실패 사유는 반드시 **"기능 부재"**여야 하며 fixture 오류·import 오류·오타는 RED 증거로 무효다. 아래 표는 각 실패의 1차 원인을 실제 예외/assert 메시지로 분류한다.

### 6.1 RED(FAIL) — 20건, 전건 "기능 부재"로 귀속

| # | 테스트 | 커버 TS | 1차 실패 지점 | 기능 부재 사유 |
|---|--------|---------|--------------|----------------|
| 1 | `test_qa001_missing_body_detected_in_violations` | TS-001 | `assertEqual(len(missing), 2)` → 실제 0 | `build_review_block()`이 아직 참조 무결성 검사를 하지 않음(`memory_file_missing` 미생성) |
| 2 | `test_qa003_existing_four_violation_types_unchanged` | TS-003 | `module.build_review_block(doc, json_path=None)` 호출 | `TypeError: build_review_block() got an unexpected keyword argument 'json_path'` — 시그니처 미변경 |
| 3 | `test_qa004_call_sites_pass_json_path_and_six_commands_detect` | TS-004 | `assertEqual(src.count("build_review_block(doc)"), 0)` → 실제 10 | 호출부 9곳 + def 1곳이 구형태(1-인자) 그대로 잔존 |
| 4 | `test_qa005_traversal_row_reported_as_unresolvable_not_missing` | TS-005 | `assertIn("memory_file_unresolvable", types)` → 미검출 | 경로 해석 실패 검사 자체가 없음(`memory_file_unresolvable` 어휘 미도입) |
| 5 | `test_ts036_mixed_vocab_review_distinguishes_missing_from_unresolvable` | TS-036 | `assertEqual(by_title.get("탈출-혼합"), "memory_file_unresolvable")` → None | 위와 동일 근본 원인(검출 로직 부재) |
| 6 | `test_qa006_candidate_orphan_row_cleaned_real_layout_roundtrip` | TS-006 | `_run(["delete", ..., "--orphan", "--ref", ...])` | `argparse: error: unrecognized arguments: --orphan --ref ...` — CLI 플래그 미신설 |
| 7 | `test_qa007_promoted_orphan_row_cleaned` | TS-007 | 상동 | 상동 |
| 8 | `test_qa008_orphan_rejected_when_body_exists_all_statuses` (4 subTest) | TS-008 | 상동 (4개 status 전수) | 상동 |
| 9 | `test_qa009_active_body_exists_orphan_rejected_bytes_unchanged` | TS-009 | 상동 | 상동 |
| 10 | `test_qa010_orphan_without_ref_rejected` | TS-010 | 상동 | 상동 |
| 11 | `test_qa012_provenance_log_records_reason_ref_and_summary` | TS-012 | 상동 | 상동 (provenance 기록 로직 자체도 미신설) |
| 12 | `test_qa013_orphan_delete_leaves_no_residue_and_show_ok` | TS-013 | 상동 | 상동 |
| 13 | `test_qa014_single_call_no_status_transition_required` | TS-014 | 상동 | 상동 |
| 14 | `test_qa024_traversal_with_live_body_outside_memory_rejected` | TS-034 (P0) | 상동 | 상동 |
| 15 | `test_qa025_none_return_three_paths_all_rejected` | TS-035 (P0) | 상동 (①②) | 상동 — ③(빈 file, 함수 직접 호출)은 기존 함수 동작이라 별도 통과(§6.1-보충 참조) |
| 16 | `test_qa026_ts039_vocabulary_consistency_across_three_commands` | TS-039 | `assertEqual(promote_result.get("error"), "memory_file_unresolvable")` → 실제 `"memory_file_not_found"` (구 어휘) | `cmd_promote()`의 `mem_file is None` 분기가 아직 `memory_file_not_found`를 반환(정정 3 미반영) + `--orphan` 미신설 |
| 17 | `test_ts037_orphan_and_promote_reject_regardless_of_status` (2 subTest) | TS-037 ①③ | `_run([..., "--orphan", ...])` | `--orphan` 미신설 |
| 18 | `test_qa015_lifecycle_table_matches_schema_enum` | TS-015 | `assertEqual(table_statuses, schema_statuses)` → 표={active,dead,superseded,promoted} ≠ 스키마 5종(`candidate` 누락) | `memory-learning.md` 라이프사이클 표에 `candidate` 행 미삽입 |
| 19 | `test_qa016_candidate_row_columns_filled` | TS-016 | `assertIsNotNone(row_match)` → None | 상동(`candidate` 행 자체가 표에 없음) |
| 20 | `test_qa017_new_error_codes_documented_in_readme_and_toolsmd` | TS-017 | `assertIn("memory_file_exists", codes)` → `ERROR_CODES`에 부재 | `ERROR_CODES` 신규 3종 미추가 |

QA-025 세부: ①경로 탈출·②resolve 예외(임베디드 null) 2경로는 위 표 15번과 함께 `--orphan` 미신설로 RED. ③(빈 `file`, 스키마 도달 불가로 `_resolve_memory_file()` 직접 호출)은 **기존 함수의 기존 동작**이라 이미 통과한다(GREEN 대상 아님 — PLAN §3.2.2 판정3, 아래 §6.2 참고).

### 6.2 PASS — 4건 (불변식 가드/하위호환 — RED 시점 통과가 정상, PLAN이 명시적으로 허용)

| # | 테스트 | 통과 사유 |
|---|--------|----------|
| 1 | `test_qa002_no_false_positive_when_bodies_intact` | 검출 로직이 아직 없으므로 `memory_file_missing`이 항상 0건 — "위양성 0"이 자명하게 성립(096 도입 후에는 진짜 회귀 가드로 전환) |
| 2 | `test_qa011_no_flag_delete_still_requires_dead_or_superseded` | PLAN §4.2 Step 1 완료 기준이 명시한 불변식 가드(QA-011) — 무플래그 `delete` 동작은 096 변경 대상이 아니므로 이미 통과 |
| 3 | `test_qa018_existing_four_rows_text_unchanged` | PLAN §4.2 Step 1 완료 기준이 명시한 불변식 가드(QA-018) — 기존 4행 텍스트는 아직 아무도 건드리지 않았으므로 이미 통과 |
| 4 | `test_ts038_no_flag_delete_allows_dead_unresolvable_row` | 음성 통제 — 무플래그 `delete`는 `mem_file`을 조회하지 않는 기존 `else` 3줄(`memory_tool.py:1355-1357`) 그대로이므로 이미 허용·통과. GREEN 이후에도 계속 통과해야 하며, 통과하지 않게 되면 PLAN [MUST] 위반 신호 |

## 7. mock/patch/MagicMock 금지 확인

```
$ grep -c "mock\|patch\|MagicMock" opal/tools/memory-tool/tests/test_memory_tool.py
3
```

3건 전부 **정책 서술 프로즈**(파일 상단 @header description의 "mock/patch/MagicMock 금지" 문구, `_write_doc`/QA-025 docstring의 "mock이 아니라 실 파일/실제 함수" 부정 서술)이며, 실제 `unittest.mock` import·`@patch`·`Mock(`/`MagicMock(` 사용은 0건이다(재확인 grep 무출력).

## 8. 완료 기준 대조 (PLAN §4.2 Step 1)

| 완료 기준 | 상태 |
|-----------|------|
| 신규 케이스 FAIL + 기존 163건 pass | ✅ RED 20/24, 기존 163 그대로 |
| RED 증거 stdout 산출물 기록 | ✅ 본 문서 §2·§3 |
| mock/patch/MagicMock 0건 | ✅ §7 |
| 실패 사유 "기능 부재" (fixture/import/오타 아님) | ✅ §6.1 — 전건 argparse 미인식·시그니처 불일치·검출 로직 부재·어휘 미정합·문서 미반영으로 귀속, fixture/import 오류 0건 |
| 불변식 가드(QA-011·QA-018) RED 시점 통과 허용 | ✅ §6.2 |

---

## 9. Scope 준수 확인

- 수정 파일: `opal/tools/memory-tool/tests/test_memory_tool.py` **1개만**.
- `opal/tools/memory-tool/memory_tool.py`: **무변경** (`git diff` 대상 0) — GREEN 미구현.
- 기존 3100줄 파일의 기존 코드는 삽입 지점(헬퍼 직후, 파일 말미) 외 어떤 라인도 수정하지 않았다.

---

## 10. Step 2(F-001 GREEN) 이후 교정 — RED fixture 결함 2건 (red-first.md §3)

> Step 2에서 `opal-be-agent`가 `build_review_block(doc, json_path)` + 호출부 9곳 배선을 구현했다.
> `TestReviewReferenceIntegrity` 6케이스 중 4건은 즉시 GREEN이었으나, 2건은 **구현 결함이 아니라
> RED 작성 시점의 assertion 오류**로 PM이 독립 실측 판정했다. red-first.md §3(GREEN 중 테스트
> 파일 수정 금지)에 따라 GREEN 워커가 아닌 **RED 작성자인 본 에이전트가 교정**했다.
> 교정은 `test_qa003_...`/`test_qa004_...` 2개 메서드 **본문만** 수정했으며, `memory_tool.py`는
> 이번 교정에서도 0바이트 변경했다(교정 후 `git diff --stat memory_tool.py`는 Step 2가 만든
> 24 insertions/10 deletions 그대로이며 추가 변경 없음).

### 10.1 교정 1 — `test_qa003_existing_four_violation_types_unchanged`

**결함**: fixture 제목이 `"긴제목" * 10` = 정확히 30자였는데 판정식은
`len(title) > TITLE_MAX_LENGTH`이고 `TITLE_MAX_LENGTH = 30`
(`memory_tool.py:856`, `schema/memory.schema.json:106`) — `30 > 30 == False`라
`title_too_long`이 구현과 무관하게 애초에 검출 불가능했다(검증 불능 fixture).

**변경 전 단언(핵심)**:
```python
{"title": "긴제목" * 10, ...}   # 정확히 30자 — 항상 미검출
...
self.assertEqual(violations[3]["type"], "title_too_long")
```

**변경 후 단언(핵심)**: 임계값을 하드코딩하지 않고 `module.TITLE_MAX_LENGTH`에서 직접 취득해
경계(30자, 미검출)와 초과(31자, 검출) 두 행으로 분리했다.
```python
max_len = module.TITLE_MAX_LENGTH
boundary_title = "가" * max_len          # 30자 — 미검출이 정상
over_title = "가" * (max_len + 1)        # 31자 — 검출이 정상
...
self.assertEqual(violations[3]["type"], "title_too_long")
self.assertEqual(violations[3]["title"], over_title)
self.assertEqual(violations[3]["length"], max_len + 1)
self.assertNotIn(boundary_title, [v.get("title") for v in violations],
                 f"경계값 정확히 {max_len}자 제목이 title_too_long으로 오탐됨")
```

**검증**: 단독 실행 결과 GREEN. 경계 축(⑥) 커버리지가 30자 미검출/31자 검출 양쪽으로 강화됨.

### 10.2 교정 2 — `test_qa004_call_sites_pass_json_path_and_six_commands_detect`

**결함**: append 이후에도 기대 `memory_file_missing` 카운트를 orphan 사전조건 그대로인
2로 두었다. PM 실측: `cmd_append`는 `file_field = _title_to_filename(title)`
(`memory_tool.py:965`)로 경로 문자열만 인덱스에 기록하며 `memory/<file>.md` 본문을
생성하지 않는다(`write_text` grep 결과 저장소 전체에서 MEMORY.json 원자적 쓰기용
tmp 파일 1건(`:345`)뿐, `memory/*.md` 대상 0건). 따라서 `append --kind memory`는
구조적으로 항상 본문 없는 신규 행을 만들고, F-001이 그 행을 append 시점에 즉시
검출하는 것이 **정상 동작**이다 — 오탐이 아니라 이 기능의 핵심 가치(태스크 배경의
"인덱스는 있는데 본문이 없는" 상태가 발생하는 실제 경로를 설명한다).

**변경 전 단언(핵심)**:
```python
append_result = _run(["append", ..., "--title", "QA-004 신규 메모리", ...])
self.assertEqual(_missing_count(append_result), 2, ...)   # 이하 update/prune/task-number/delete도 전부 2
```

**변경 후 단언(핵심)**: 기대치를 3(orphan 사전조건 2 + append 신규 1)으로 정정하고,
숫자만이 아니라 **append로 만든 행이 실제로 검출 목록에 title로 포함되는지**를
append 직후와 마지막 delete 이후(지속성) 양쪽에서 단언한다. 이후 update/prune/
task-number/delete의 기대치도 3으로 일괄 정정(누구도 그 신규 행의 본문 상태를
바꾸지 않으므로 3이 그대로 유지되는 것이 정상).
```python
appended_title = "QA-004 신규 메모리"
...
append_missing = _missing_titles(append_result)
self.assertEqual(len(append_missing), 3,
    f"append는 본문 없는 신규 행을 만들므로(memory_tool.py:965 — _title_to_filename만 "
    f"계산, .md 쓰기 없음) orphan 사전조건 2건 + 신규 1건 = 3건이 정상이다: {append_result}")
self.assertIn(appended_title, append_missing,
    f"append로 생성된 행 '{appended_title}' 자신이 검출 목록에 없음 — append 시점 검출이라는 "
    f"핵심 동작이 성립하지 않음: {append_missing}")
...
delete_missing = _missing_titles(delete_result)
self.assertEqual(len(delete_missing), 3, ...)
self.assertIn(appended_title, delete_missing,
    f"append로 생성된 행이 이후 명령(delete)까지 지속 검출되지 않음: {delete_missing}")
```
(update/prune/task-number 단계의 `_missing_count(...) == 2` 단언도 각각 `len(_missing_titles(...)) == 3`으로 정정)

**검증**: 단독 실행 결과 GREEN.

### 10.3 교정 후 검증 결과

```
$ ~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q -k "TestReviewReferenceIntegrity"
......                                                                   [100%]
6 passed, 181 deselected in 0.85s
```
→ `TestReviewReferenceIntegrity` **6케이스 전건 GREEN** (판정: 요약 라인 "6 passed" + exit code, pytest-subtests 왜곡 없음 — 이 클래스는 subTest 미사용).

```
$ ~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q \
    --deselect .../TestReviewReferenceIntegrity --deselect .../TestDeleteOrphan --deselect .../TestLifecycleDocParity
163 passed, 24 deselected, 25 subtests passed in 18.55s
```
→ **기존 163건 회귀 0** (기준선과 완전 일치).

```
$ ~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q   # 전체 재실행
19 failed, 174 passed, 25 subtests passed in 21.89s   (exit=1)
```
→ `TestDeleteOrphan`(Step 3 미구현)·`TestLifecycleDocParity`(Step 4 미구현)는 교정 전과 **동일하게 RED 유지**(FAIL 목록 완전 동일 — qa006/007/008(4 subtest)/009/010/012/013/014/024/025/026/ts037(2 subtest), qa015/016/017). 손대지 않았음을 FAIL 목록 불변으로 재확인.

### 10.4 Scope/규율 준수

- 이번 교정에서 수정한 파일: `opal/tools/memory-tool/tests/test_memory_tool.py` **1개만**(`test_qa003_...`/`test_qa004_...` 두 메서드 본문 한정).
- `memory_tool.py`: 이번 교정에서 **0바이트 추가 변경**.
- `TestDeleteOrphan`·`TestLifecycleDocParity`: **미접촉** — §10.3 FAIL 목록 불변으로 실증.
- 약화 없음: 두 교정 모두 assertion을 **삭제·완화가 아니라 추가·정확화**(경계 케이스 분리, title 기반 포함 단언 추가)하는 방향으로만 이루어졌다.

---

## 11. Step 3(F-002 GREEN) 이후 갱신 — 선재 079 회귀 가드와의 충돌 해소 (PM 판정)

> Step 3에서 `opal-be-agent`가 `delete --orphan --ref` + `ERROR_CODES` 3종 추가(§3.2.2)를
> 구현해 `TestDeleteOrphan` 14/14가 GREEN이 됐다. 그러나 **079 트랙의 선재 회귀 가드**
> `test_ts028_error_codes_unchanged_no_new_codes`(`TestUpdateKindArgGuard` 소속)가
> `len(codes) == 23`을 단정하고 있어 096의 26종과 정면 충돌했다. PM이 "가드를 삭제가
> 아니라 **갱신**한다"로 판정했고, 본 에이전트(RED 작성자)가 `test_ts028_...` 메서드
> **1건만** 교정했다(red-first.md §3 — GREEN 워커는 테스트를 고칠 수 없음).

### 11.1 `test_ts028_error_codes_unchanged_no_new_codes` — 변경 전/후

**변경 전(핵심 단언)** — 총 개수 하드코딩(079 시점 기준 23):
```python
self.assertEqual(len(codes), 23, f"ERROR_CODES 개수가 23이 아님(신규 코드 유입 의심): {sorted(codes)}")
```

**변경 후(핵심 단언)** — 총 개수 하드코딩을 제거하고 (1) 079 원본 23종 전건 생존(부분집합,
삭제·개명 시 즉시 FAIL) + (2) 추가분이 정확히 096의 3종과 일치(그 이상·이하도 아님)
2단 검사로 정밀화:
```python
_T079_ORIGINAL_ERROR_CODES = frozenset({... 23개 키 ...})  # 079 시점 SSOT, 하드코딩 기준선

missing = self._T079_ORIGINAL_ERROR_CODES - code_keys
self.assertEqual(missing, set(), f"079 원본 ERROR_CODES 중 삭제·개명된 키: {sorted(missing)}")

added = code_keys - self._T079_ORIGINAL_ERROR_CODES
self.assertEqual(
    added,
    {"memory_file_exists", "orphan_ref_missing", "memory_file_unresolvable"},
    f"079 원본 23종 이후 추가된 키가 096이 문서화한 3종과 불일치(...): {sorted(added)}",
)
# invalid_kind/invalid_args 템플릿 무변경 단언은 그대로 유지
```

**정밀화 효과**: 총 개수를 다시 `== 26`으로 하드코딩하지 않았으므로, 다음 태스크가 코드를
추가하면 이 가드가 다시 발동해 **의도적 갱신을 강제**한다. 동시에 079가 지정한 23종
(1)은 096 이후에도, 그리고 향후 어떤 태스크가 오더라도 삭제·개명되면 즉시 잡힌다 —
원래 가드가 지키려던 핵심("079 작업 중 의도치 않은 드리프트 차단")은 그대로 보존되고,
"영구히 23종 고정"이라는 부수 효과만 제거됐다.

**근거 실측(PM 제공, 본 에이전트 재확인)**: `git diff` 없이 모듈 직접 로드로 재확인 —
096 이후 `ERROR_CODES`는 079 원본 23종을 **1건도 잃지 않고 그대로 포함**하며, 추가된
키는 정확히 `{memory_file_exists, orphan_ref_missing, memory_file_unresolvable}` 3종
뿐이다(그 이상도 이하도 아님). `invalid_kind`/`invalid_args` 템플릿 문자열도 원문과
바이트 단위로 동일.

### 11.2 검증 결과

```
$ ~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q -k "test_ts028_error_codes_unchanged_no_new_codes"
1 passed, 186 deselected in 0.09s
```
→ 갱신된 가드 단독 GREEN.

```
$ ~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q \
    --deselect opal/tools/memory-tool/tests/test_memory_tool.py::TestLifecycleDocParity
183 passed, 4 deselected, 31 subtests passed in 21.41s   (exit=0)
```
→ PM 기대치(163 baseline + 6 F-001 + 14 F-002 = 183) **정확히 일치**. `TestLifecycleDocParity`
4건만 deselect 대상.

```
$ ~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q   # 전체 재실행
3 failed, 184 passed, 31 subtests passed in 21.73s   (exit=1)
```
→ 남은 FAIL 3건은 전부 `TestLifecycleDocParity`(`test_qa015_...`/`test_qa016_...`/
`test_qa017_...` — Step 4 문서 미구현이라 RED가 정상, 손대지 않음). 같은 클래스의
`test_qa018_...`(불변식 가드)는 여전히 PASS로 남아 이전 상태와 동일 — Step 3가 문서
파리티 클래스에 어떤 영향도 주지 않았음을 확인.

### 11.3 Scope/규율 준수

- 이번 갱신에서 수정한 파일: `opal/tools/memory-tool/tests/test_memory_tool.py` **1개만**,
  그중에서도 `test_ts028_error_codes_unchanged_no_new_codes` 메서드(+헬퍼 상수
  `_T079_ORIGINAL_ERROR_CODES`) **1건만** 변경.
- `memory_tool.py`: 이번 갱신에서 **0바이트 추가 변경**(Step 3 GREEN 상태 그대로).
- 다른 079 트랙 케이스(`TestUpdateBackCompat`/`TestUpdateKindHistory`/
  `TestUpdateKindArgGuard`의 나머지 메서드들/`TestUpdateHistoryLossless`): **미접촉**.
- `TestLifecycleDocParity` 4케이스: **미접촉** — §11.2 마지막 실행 결과의 FAIL 목록이
  Step 3 이전과 동일(qa015/016/017 FAIL, qa018 PASS)로 실증.
- 약화 없음: 총 개수 하드코딩을 제거했지만 검사 범위는 **원본 23종 부분집합 검사 +
  추가분 정확 일치 검사**로 오히려 넓어졌다 — 070 실패모드(assertion 삭제·완화로 GREEN
  조작)에 해당하지 않는다.
