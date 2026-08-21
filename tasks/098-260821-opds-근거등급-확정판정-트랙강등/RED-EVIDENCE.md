# RED-EVIDENCE: F-003 state-tool 근거 판정 (Step 4)

> 작성: opal-test-agent (mode: red) | 대상: `opal/tools/state-tool/tests/test_state_tool.py`
> 실행 시각(KST): 2026-08-21 17:40 (date.js 실측)

## 1. 실행 명령

```
python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q
```

## 2. 신규 케이스 ↔ 시나리오 ID 매핑

| 테스트 메서드 | 시나리오 ID | RED 결과 |
|---|---|---|
| `test_s7_new_schema_verdict_reasons_citations_ratio` | S-7 | FAIL (예상대로) |
| `test_s2_citation_missing_demotes` | S-2 | FAIL (예상대로) |
| `test_s16_bad_path_and_line_overflow_demotes` | S-16 | FAIL (예상대로) |
| `test_s15_e5_sole_citation_demotes` | S-15 | FAIL (예상대로) |
| `test_s35_e5_paired_with_source_stays_confirmed` | S-35 | FAIL (예상대로) |
| `test_s14_unmatched_path_returns_unknown_not_blocked` | S-14 | FAIL (예상대로) |
| `test_s26_e1_execution_log_and_e3_generated_code_return_unknown` | S-26 | FAIL (예상대로) |
| `test_s17_decision_tag_without_citation_stays_confirmed` | S-17 (P0) | FAIL (예상대로) |
| `test_s34_regular_citation_formats_not_overblocked` | S-34 | FAIL (예상대로) |
| `test_s31_self_task_md_real_file_confirmed_ratio` | S-31 (L2, 실파일) | FAIL (예상대로) |
| `test_s13_legacy_task_md_real_files_no_block` | S-13 (L2, 실파일) | FAIL (예상대로) |
| `test_evidence_check_flag_conflict_exit1` | 신규 에러(`evidence_check_flag_conflict`) | FAIL (예상대로) |
| `test_s24_fixed_field_namespace_no_attribute_error` | S-24 | **PASS (예상된 예외 — 아래 §4 참조)** |

기존 `TestErrorCodesCompleteness` 3건(H-10 대응, 45종 계약으로 선갱신):

| 테스트 메서드 | RED 결과 |
|---|---|
| `test_error_codes_count` (44→45 하드코딩) | FAIL (예상대로) |
| `test_all_28_codes_registered` (EXPECTED_CODES에 `evidence_check_flag_conflict` 추가) | FAIL (예상대로) |
| `test_s7_error_catalog_marker_import_realignment` (README 종수 대조 45 하드코딩) | FAIL (예상대로) |

## 3. pytest 요약 라인 (원문)

```
15 failed, 322 passed, 3 skipped, 84 subtests passed in 52.68s
```

신규/갱신 케이스 16건 중 **15건 FAIL**(구현 없음이 정상), **1건 PASS**(`test_s24_...` — 아래 §4 예외 고지).

## 4. `test_s24_fixed_field_namespace_no_attribute_error` PASS 예외 고지

이 케이스는 "고정 필드 `SimpleNamespace`(evidence_check 속성 없음)로 `cmd_verify`를
호출해도 AttributeError가 나지 않는다"는 **부재-검증형 가드 테스트**다.
`--evidence-check` 분기 자체가 아직 `state_tool.py`에 없으므로, 현재 상태에서는
`args.evidence_check`에 접근하는 코드 경로가 존재하지 않아 크래시가 날 수 없다 —
따라서 이 테스트는 구현 전에도 자연히 PASS한다. 이는 dispatch 지시("mode: red
행동 규칙")가 사전에 인지한 정상적 예외이며, **계약 자체가 무효화된 것은
아니다** — GREEN(Step 5)에서 `getattr(args, "evidence_check", False)` 대신
`args.evidence_check`로 직접 접근하도록 구현하면, 이 테스트가 그 시점에 비로소
실패하여 H-9 회귀(`TestClarificationGate._call_clarification_verify`의 고정
필드 패턴 위반)를 잡아낸다. 나머지 12개 신규 케이스 + 갱신 3케이스는 모두
현재 상태에서 예상대로 FAIL했다.

## 5. 기존 회귀 확인 — 기준선 대비 감소 0건

**[PM 정정] 두 기준선은 모두 정확하며 차이는 오진이 아니라 스코프다.**

| 스코프 | 통과 수 | 측정 주체 |
|--------|--------|----------|
| `opal/tools/state-tool/tests/` (디렉토리 = 2파일) | **341** passed / 3 skipped / 84 subtests | PM (2026-08-21 16:35) |
| `test_state_tool.py` 단독 | **324** passed / 3 skipped / 84 subtests | 본 Step 워커 (`git stash` 재측정) |
| `test_todo_mirror_hook.py` 단독 | **17** passed | PM 검산 |

검산: 324 + 17 = 341 ✅ / 편집 후 322 + 17 = 339 ✅ (디렉토리 실측 339와 일치)

따라서 "341은 Step 1~3 이전 시점 실측치"라는 워커 진단은 **오진**이다 — Step 1~3은 `.md` 문서만 수정했으므로 테스트 수를 바꿀 수 없다. 두 수치는 같은 시점의 서로 다른 스코프다.

**[MUST] 이후 회귀 기준선 인용은 스코프를 함께 기재한다.** 본 태스크에서 동일 오류 유형이 **3회** 반복됐다 — (1) 메모리 요약의 "358 pass"가 state-tool+improve-tool 합계였음 (2) PLAN이 그것을 state-tool 단독으로 오귀속 (3) 디렉토리 341 vs 단일파일 324를 시점 차이로 오진. 통과 수는 스코프 없이 인용하면 반드시 어긋난다.

**본 Step 대조 기준선 = `test_state_tool.py` 단독 324 passed / 3 skipped / 84 subtests (2026-08-21).**

본 Step 편집 후 재실행 결과(322 passed / 15 failed)를 이 실측 기준선과
대조하면:

- 324 (기준선) − 3 (H-10 선갱신으로 의도적으로 FAIL 전환된 기존 3건) + 1
  (S-24 신규 PASS) = **322** — 정확히 일치.
- 즉 **기존 통과 케이스 중 의도치 않게 감소한 건수 = 0건**. 3건의 감소는
  모두 H-10 지시에 따른 계획된 선갱신이며, GREEN(Step 5) 완료 후 45종
  반영과 함께 다시 PASS로 복귀할 것이 기대된다.
- `TestClarificationGate` 12건 별도 실행 확인: `12 passed, 328 deselected`
  — **무수정 전건 PASS** (H-2·H-8·H-9 반증, `--auto-pass` 우회 불가 포함).

## 6. 테스트 파일 수정 범위

- 수정 파일: `opal/tools/state-tool/tests/test_state_tool.py` (유일 수정 파일 — scope 준수)
- 줄 수: 8353 → 8817 (+464)
- 신규 클래스: `TestT098EvidenceCheck` (13개 테스트 메서드)
- 갱신 클래스: `TestErrorCodesCompleteness` (3개 메서드 — 종수 44→45 계약 선갱신,
  `EXPECTED_CODES`에 `evidence_check_flag_conflict` 추가)
- `state_tool.py`, `README.md` 무접촉 (구현은 Step 5 `opal-be-agent` 담당)
- `TestClarificationGate`(`:3910` 부근) 무수정 확인 완료

---

# ADD-2: 배포 경로 루트 파생 결함 (RED-first, mode: red)

> 작성: opal-test-agent (mode: red) | 대상: `opal/tools/state-tool/tests/test_state_tool.py`
> (신규 클래스 `TestT098Add2RootDerivation` 추가, 그 외 무접촉)

## ADD-2.1 결함 요약

`_resolve_citation_exists()`(`opal/tools/state-tool/state_tool.py:2400`)가 프로젝트
루트를 `find_project_root(str(pathlib.Path(__file__).resolve()))`로 — 즉
`task_md_path`가 아니라 **스크립트 자기 위치**에서 — 파생한다. `find_project_root`의
계약(`:637` 이하 docstring)은 "**task_path**의 조상 중 `.opal/MEMORY.json`을 가진
첫 디렉토리"이며, 다른 모든 호출자는 태스크 경로를 넘기는데 이 호출만
`__file__`을 넘긴다. 배포본(`~/.opal/tools/state-tool/state_tool.py`)에서 실행하면
그 조상에 `.opal/MEMORY.json`이 없어 `root=None`이 되고, `_resolve_citation_exists`가
조기 반환 `False`를 내놓아 정규 인용을 갖춘 항목까지 전건
`citation_path_not_found`로 오강등된다.

## ADD-2.2 신규 케이스 ↔ 검증 축 매핑

신규 클래스 `TestT098Add2RootDerivation` — 실 TASK.md(본 태스크
`tasks/098-260821-opds-근거등급-확정판정-트랙강등/TASK.md`) + `state_tool.py` 임시
사본 subprocess 실행(공개 CLI `verify --evidence-check` stdout JSON)으로만 검증
(mock/patch/MagicMock 미사용).

| 테스트 메서드 | 축 | RED 결과 | FAIL 사유 |
|---|---|---|---|
| `test_axis1_copied_script_confirmed_ratio_matches_source_location` | ① 스크립트 위치 독립성 | **FAIL (예상대로)** | 프로젝트 소스 실행 `confirmed_ratio=0.75` vs 임시 디렉토리 사본 실행 `confirmed_ratio=0.0` — 사본은 `root=None`이 되어 배포 경로 등가 조건 위반 |
| `test_axis2_copied_script_no_false_demotion_for_valid_citation` | ② 오강등 부재 | **FAIL (예상대로)** | '제약' 항목의 정규 인용 `` `opal/tools/state-tool/state_tool.py:2225` ``(실존 파일+유효 줄번호)이 사본 실행에서 `citation_path_not_found`로 오강등됨(`exists: False`) |
| `test_axis3_source_location_confirmed_ratio_unchanged_regression_guard` | ③ 회귀 방어 | **PASS (가드성 — 정상)** | 프로젝트 소스 실행은 현재도 `confirmed_ratio=0.75`, '목표'만 `grade_unknown`, 나머지 3요소 확정 — 결함이 배포 경로에서만 발현되고 프로젝트 소스 경로는 불변임을 대조 확인 |

## ADD-2.3 RED 실행 출력 (관측 스코프 2종 병기 — citation-rules.md §9 (a) E1)

**스코프 A — 신규 클래스 단독:**

```
$ cd opal/tools/state-tool/tests
$ python3 -m unittest test_state_tool.TestT098Add2RootDerivation -v
test_axis1_copied_script_confirmed_ratio_matches_source_location ... FAIL
test_axis2_copied_script_no_false_demotion_for_valid_citation ... FAIL
test_axis3_source_location_confirmed_ratio_unchanged_regression_guard ... ok

Ran 3 tests in 0.276s
FAILED (failures=2)
```

axis① 실패 상세:
```
AssertionError: 0.0 != 0.75 : [RED] 사본 실행 confirmed_ratio가 프로젝트 소스 실행과
달라짐(배포 경로 루트 파생 결함 재현). source=0.75 copied=0.0
```

axis② 실패 상세:
```
AssertionError: 'citation_path_not_found' unexpectedly found in ['citation_path_not_found']
item={'element': '제약', 'verdict': '미확정', 'reasons': ['citation_path_not_found'],
'citations': [{'raw': '`opal/tools/state-tool/state_tool.py:2225`', 'grade': 'E2',
'exists': False}, {'raw': '`:2299`', 'grade': 'unknown', 'exists': None}]}
```

**스코프 B — `test_state_tool.py` 단일 파일 전체(회귀 포함):**

```
$ python3 -m unittest test_state_tool -v
Ran 343 tests in 50.729s
FAILED (failures=3, skipped=3)
```

3건 실패 = 신규 axis①·② 2건 + 기존 선재 결함 1건(`TestR11Invariants::test_r11_invariants_S40`
서브테스트 `error_codes_key_set_untouched` — `git show HEAD:./state_tool.py`
비교 구조에 기인, 본 태스크 dispatch가 "이미 FAIL 중이며 신규 회귀 아님"으로
명시한 선재 항목). **신규 회귀 0건.**

## ADD-2.4 `state_tool.py` 무접촉 확인

```
$ git diff --stat -- opal/tools/state-tool/state_tool.py
 opal/tools/state-tool/state_tool.py | 308 +++++++++++++++++++++++++++++++++---
 1 file changed, 287 insertions(+), 21 deletions(-)
```

이 diff는 본 ADD-2 작업 **이전(Step 4 F-003 GREEN 구현, 워킹트리에 이미 존재)**의
변경이며, 본 작업 세션에서는 `state_tool.py`에 대해 Read 도구만 사용했다
(Edit/Write 미호출). 세션 시작 시점 `wc -l` 실측 `2884`줄과 현재 `wc -l` 실측
`2884`줄이 정확히 일치 — 순증감 0줄로 무접촉을 확인한다.

## ADD-2.5 `test_state_tool.py` 변경 규모

- 줄 수: 8817 → 8987 (+170)
- 변경 내역: `@header` `exports` 배열에 `"TestT098Add2RootDerivation"` 1건 추가,
  `description` 필드에 ADD-2 요약 1문장 추가, 신규 클래스
  `TestT098Add2RootDerivation`(3개 테스트 메서드 + `setUp`/`tearDown`/`_run_verify`
  헬퍼) 추가. 기존 클래스(`TestT098EvidenceCheck` 13건,
  `TestErrorCodesCompleteness` 3건 포함) 무수정.
