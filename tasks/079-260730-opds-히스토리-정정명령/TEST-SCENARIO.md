# TEST SCENARIO: 작업 히스토리 오기재 정정 명령 신설 (`update --kind history`)

> 작성일: 2026-07-30 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 리스크 가설 표(H-1~H-10) 기반
> 시나리오 ID는 PLAN.md의 `TS-NNN`을 승계한다(재채번 없음 — PLAN §3 각 기능 테스트 표와 1:1 추적).

## RED-first 판정

**트랙: RED-first 강제** (`~/.opal/references/harness/red-first.md` §1.5 — "API 계약" + "버그 수정(회귀 방지)" 2중 해당).

- RED 작성: `opal-test-agent` (PLAN Step 1) / 구현: `opal-be-agent` (Step 2) — **[MUST] §2 작성자≠구현자**
- RED 대상: TS-001~TS-020, TS-025, TS-027, TS-028
- **[MUST] §3**: GREEN 루핑 중 Step 1이 만든 테스트의 단정을 약화·삭제하지 않는다
- EXECUTE 진입 전 `state-tool verify --red-check`로 RED 증거 확인
- 문서 Step(3·4)은 "설정·문서" 트랙 — 사후 산출물 검사(TS-021~TS-023, TS-029, TS-030)

## 계층·실행 방식 배치 원칙

| 판정 | 결과 |
|------|------|
| FE 변경 | **0건** — CLI 도구 + 참조 문서만 변경. `test-scenario-guide.md` §Step 3-b **M2 의무 트리거 미해당** |
| L3 `[SUPERVISOR]` | **해당 없음** — 화면·사용자 플로우 변경이 없어 캡틴 육안 검증 대상 시나리오가 존재하지 않는다. 억지로 만들지 않는다 |
| M3 (수동) | TS-024 1건 — **비가역**(install 배포 + 실 `.opal/MEMORY.json` 변경)이라 PM이 직접 수행한다. **테스트 에이전트가 자동 PASS 처리할 수 없다** |

---

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 `cmd_update` 시그니처 확장 | 기존 `update` 호출 계약 + 기존 132건 — `--kind` 기본값 누락·dest 충돌 시 전량 회귀 | **P0** | L1 + L2 | TS-001, TS-002, TS-025 |
| H-2 | F-003 인자 조합 게이트 | 오용이 거부 대신 **silent no-op**이면 "정정됐다"고 믿고 진행 → 오기재 영속화 | **P0** | L1 | TS-011~TS-015 |
| H-3 | F-002 대상 행 식별 | 동일 `title` 중복 시 배열 순서 ↔ `show --brief`의 `date` 재정렬(`memory_tool.py:1229`)이 어긋나 **의도와 다른 행 정정** | P1 | L1 | TS-018 |
| H-4 | F-002 쓰기 경로 | 거부·검증 실패 경로에서 부분 기록 / `.tmp`·`.lock` 잔여 → SSOT 파손 | **P0** | L1 + L2 | TS-016, TS-017 |
| H-5 | F-004 `memory-learning.md` | 078에서 81줄로 슬림화한 SSOT의 **재비대화** → 부트스트랩 토큰 잠식 | P1 | L1 | TS-023 |
| H-6 | F-002 FIFO 상호작용 | `_enforce_history_fifo`는 `rows[:5]` 순수 절단이고 스키마에 `maxItems`가 없어, 정정 경로에서 호출 시 **6행 이상 문서의 행이 조용히 삭제** → "삭제 없는 정정" 전제 파괴 | **P0** | L1 | TS-009 |
| H-7 | F-002 행 필드 치환 | `historyRow.additionalProperties:false` — 부가 키 삽입 시 `schema_validation_failed` | P1 | L1 | TS-010 |
| H-8 | F-001 argparse 등록 | `--kind`에 `choices=`를 붙이면 **exit 2 + stderr usage(비 JSON)** 로 R-1 AC(c)와 단일라인 JSON 계약을 동시 위반 | P1 | L1 | TS-004 |
| H-9 | F-004 `tools.md` | 077이 같은 워킹트리에서 code-scan 절 편집 중 — `Write`/전문 재작성 시 상호 클로버 | P1 | L1 | TS-022 |
| H-10 | F-004 배포·실사용 | install과 실 `.opal/MEMORY.json` 정정은 **비가역**. 미배포 상태 검증은 구 코드를 돌리고, 잘못된 sha는 실 메모리를 오염 | P1 | L2/M3 | TS-024 |

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> DB 없음(파일 기반 SSOT). "저장소"는 파일을 뜻한다. **[MUST] 신규 픽스처 파일 신설 0** — 기존 픽스처를 `shutil.copy2` 후 in-test 가공한다(PLAN Step 1).

| 저장소(파일) | 식별자 | 상태 | 출처 |
|--------------|--------|------|------|
| `tests/fixtures/fixture_doc_populated.json` | 메모리 6행 + 히스토리 5행, 스키마 유효 | 기존(078 산출) | fixture — 전 시나리오 기준 문서 |
| (in-test 가공) 히스토리 **6행** 문서 | 위 픽스처에 히스토리 1행 추가 | 스키마 유효(`maxItems` 없음) | 런타임 생성 — TS-009 전용 |
| (in-test 가공) 동일 `title` **2행** 문서 | 같은 제목 히스토리 2행(선행/후행 필드 상이) | 스키마 유효 | 런타임 생성 — TS-018 전용 |
| (in-test 생성) 임시 프로젝트 디렉토리 | `MEMORY.json` 1개 | `tempfile.mkdtemp` | 쓰기 검증용 — 실 `.opal/` 미접촉 |
| `opal/tools/memory-tool/memory_tool.py` | `ERROR_CODES` 23종 / `cmd_update` / `_enforce_history_fifo` | Step 2 구현 대상 | 소스 |
| `opal/tools/memory-tool/schema/memory.schema.json` | `$defs.historyRow`(`title`/`date`/`stage`/`path`/`result`, `additionalProperties:false`) | 무변경(읽기) | 078 산출 |
| `.opal/MEMORY.json` | 078 히스토리 행 `stage="완료·미커밋"` (**현재 stale**) | 실 파일 | TS-024 실사용 대상 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (호출) | Then (re-read) |
|---------|------------|------------|---------------|
| TS-001 | 픽스처 사본 | `--kind` 미지정 + `--status`/`--summary`/`--new-title` 단독·복합 | `ok:true`, 대상 메모리 행만 변경 |
| TS-002 | 픽스처 사본 | `update --title T` (필드 0개, `--kind` 미지정) | `ok:true` — 기존 관대 동작 보존 |
| TS-003 | 픽스처 사본 | `--kind history --stage "완료·커밋(abc1234)"` | `ok:true`, `kind:"history"`, 대상 행 `stage`만 변경 |
| TS-004 | 픽스처 사본 | `--kind bogus --stage x` | stdout 단일라인 JSON `invalid_kind`, **exit 1**, stderr에 usage·traceback 0, 파일 불변 |
| TS-005 | 픽스처 사본 | `--stage`/`--result`/`--path`/`--new-title` 개별 4 + 복합 1 | 전부 `ok:true`, `changed[]`가 지정 필드와 정확히 일치 |
| TS-006 | 픽스처 사본 | `--kind history --stage` 단독 | 대상 행의 나머지 4필드 + **다른 히스토리 4행 전체** 바이트 동일 |
| TS-007 | TS-005 수행 후 문서 | `show --file X` | `ok:true` (재로드 시 `validate_document` 통과), `violations` 없음 |
| TS-008 | 히스토리 5행 문서 | `--kind history --stage x` | `history_count:5`, 파일 `history` 길이 5 |
| TS-009 | **히스토리 6행** 문서 | `--kind history --stage x` | **6행 유지**(삭제 0), `review.history_status.fifo_trimmed:true`로 초과만 표면화 |
| TS-010 | 픽스처 사본 | `--kind history --stage x` | 대상 행 키 집합이 정확히 `{title,date,stage,path,result}` |
| TS-011 | 픽스처 사본 | `--kind history --status dead` | `ok:false`·`invalid_args`, `message`에 `--status` 사유, 파일 바이트 불변 |
| TS-012 | 픽스처 사본 | `--kind history --summary "x"` | `ok:false`·`invalid_args`, `message`가 `--result` 안내, 파일 불변 |
| TS-013 | 픽스처 사본 | `--kind memory --stage x` / `--result x` / `--path x` | 3케이스 각각 `ok:false`·`invalid_args`, 파일 불변 |
| TS-014 | 픽스처 사본 | 없는 히스토리 제목 + `--kind history --stage x` | `ok:false`·`row_not_found`, 파일 불변, `.lock` 잔여 0 |
| TS-015 | 픽스처 사본 | `--kind history` + 필드 0개 | `ok:false`·`invalid_args`, 파일 불변 |
| TS-016 | 픽스처 사본 | 거부 경로 전수 실행 후 | 파일 바이트·mtime 동일, `*.tmp*` 0건, `MEMORY.json.lock` 0건 |
| TS-017 | 픽스처 사본 | 2프로세스가 서로 다른 필드 동시 정정 | 클로버 0(둘 다 반영) 또는 한쪽 `lock_timeout` 결정론 실패. 문서는 **항상 스키마 유효** |
| TS-018 | 동일 `title` 2행 문서 | `--kind history --stage x` | 배열 **선행 행만** 변경, 후행 불변, `matched_index`·`match_count:2` 응답 |
| TS-019 | 구현 후 CLI | `update --help` | `--kind`·`--stage`·`--result`·`--path` + `{memory,history}` 노출 |
| TS-020 | 픽스처 사본 | `--kind history --stage x` 성공 | 응답에 `review` 블록 첨부(ambient 자가검토 계약 유지) |
| TS-021 | 문서 3종 | grep | `--kind history` 표기 존재 + "정정 불가"·"되돌릴 수 없" 류 0건 |
| TS-022 | `tools.md` | grep + `git diff` | `update` 블록에 인자 4종 + 에러표에 `invalid_kind` 행, **code-scan 절 diff 0줄** |
| TS-023 | `memory-learning.md` | `wc -l` + grep | **≤84줄**, 신규 `##` 헤딩 0, 신규 표 0 |
| TS-024 | 배포본 + 실 `.opal/MEMORY.json` | install → `--kind history --title "078 …" --stage "완료·커밋(d7a8ce0, 447ff09)"` | `ok:true`·`match_count:1`·`history_count:5`·`changed:["stage"]`, `show --brief` 반영, `git diff`가 **1행 1필드**만 |
| TS-025 | 전 스위트 | `unittest discover` | 기존 **132건 전량 GREEN** |
| TS-026 | `memory_tool.py`, 테스트 파일 | grep | `@header.description`에 `--kind history` + 변경이력 `v2.1`, 테스트 `@header.exports`에 신규 클래스 |
| TS-027 | 픽스처 사본 | `--kind history --path "../../etc/"` | `ok:false`·`invalid_args`, 파일 불변 |
| TS-028 | `memory_tool.py` | `ERROR_CODES` 키 집합 | **23종 그대로**(신규 0), `invalid_kind`·`invalid_args` 템플릿 무변경 |
| TS-029 | 문서 usage 블록 + CLI | 대조 | 인자 목록이 실제 `--help`와 일치(누락·잉여 0) |
| TS-030 | 변경 3문서 | 변경이력 표 확인 | `README.md` v2.1 / `tools.md` v2.7 / `memory-learning.md` v1.3, KST 일시 포함 |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

> 공통: **실행 방식 M1** / 도구 `~/.opal/.venv/bin/python -m unittest` (subprocess 기반) / 실행 명령은 EXECUTE 워커가 채운다.
> **[MUST] 테스트 더블 금지** — 실 파일·실 프로세스로만 검증한다. 가짜 대역으로 대체하면 PM Gate FAIL.

#### TS-001: 하위호환 — `--kind` 미지정 기존 호출

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-1 (P0)** |
| 대상 | F-001 R-1 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--status`/`--summary`/`--new-title`을 단독 및 복합으로, `--kind` 없이 호출 |
| 기대 결과 | 전부 `ok:true` + 대상 **메모리 행만** 변경 + 히스토리 무변경 |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateBackCompat -v` |
| 결과 | Pass |
| 상세 | `test_ts001_status_only_no_kind_changes_only_memory_row` / `test_ts001_summary_only_no_kind_changes_only_memory_row` / `test_ts001_new_title_only_no_kind_changes_only_memory_row` / `test_ts001_combined_fields_no_kind_changes_only_memory_row` 4건 전부 `ok` — 단독·복합 호출 전부 `ok:true`, `doc["history"]`가 호출 전과 바이트 동일(`assertEqual`) 확인 |

#### TS-002: 하위호환 — 정정 필드 0개 관대 동작 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-1** |
| 대상 | F-001 R-1 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `update --file X --title T` (필드 0개, `--kind` 미지정) |
| 기대 결과 | `ok:true` — **`invalid_args`가 아니어야 한다**(R-3(d)는 history kind 한정) |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateBackCompat.test_ts002_zero_fields_no_kind_is_permissive -v` |
| 결과 | Pass |
| 상세 | `test_ts002_zero_fields_no_kind_is_permissive` ok — 필드 0개 + `--kind` 미지정 호출이 `ok:true`, `error != "invalid_args"` 확인(기존 관대 동작 보존) |

#### TS-003: `--kind history` 기본 정정

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-001 R-1 AC(b) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--kind history --title <기존 제목> --stage "완료·커밋(abc1234)"` |
| 기대 결과 | `ok:true`, 응답 `kind:"history"`, 대상 행 `stage`만 변경 |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindHistory.test_ts003_stage_only_changes_target_stage_only -v` |
| 결과 | Pass |
| 상세 | `test_ts003_stage_only_changes_target_stage_only` ok — `ok:true`, `kind:"history"`, `stage`만 변경되고 `date`/`path`/`result`는 변경 전과 동일 확인 |

#### TS-004: 잘못된 `--kind` — JSON 계약 유지 (argparse 우회 방지)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-8** |
| 대상 | F-001 R-1 AC(c) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--kind bogus --stage x` |
| 기대 결과 | stdout 단일라인 JSON `{"ok":false,"error":"invalid_kind",…}` + **exit code 1**(argparse의 2가 아님) + stderr에 usage·traceback **0건** + 파일 불변 |
| 도구 | unittest (`_run_raw` — exit code·stdout·stderr 동시 캡처) |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindArgGuard.test_ts004_invalid_kind_rejected_as_json_not_argparse_exit2 -v` |
| 결과 | Pass |
| 상세 | `test_ts004_invalid_kind_rejected_as_json_not_argparse_exit2` ok — 실측 `exit=1`(argparse 기본 2 아님), stdout 단일라인 JSON `error:"invalid_kind"`, stderr에 `usage:`/`Traceback` 0건, 파일 스냅샷 불변 확인 |

#### TS-005: 4필드 정정 — 개별·복합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-002 R-2 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--stage`/`--result`/`--path`/`--new-title` 개별 4케이스 + 4필드 복합 1케이스 |
| 기대 결과 | 전부 `ok:true` + `changed[]`가 **지정 필드와 정확히 일치**(잉여·누락 0) |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindHistory.test_ts005_stage_field_changed_reported tests.test_memory_tool.TestUpdateKindHistory.test_ts005_result_field_changed_reported tests.test_memory_tool.TestUpdateKindHistory.test_ts005_path_field_changed_reported tests.test_memory_tool.TestUpdateKindHistory.test_ts005_new_title_field_changed_reported tests.test_memory_tool.TestUpdateKindHistory.test_ts005_compound_four_fields_changed_reported_exactly -v` |
| 결과 | Pass |
| 상세 | 5케이스 전부 ok — `--stage`→`changed==["stage"]`, `--result`→`["result"]`, `--path`→`["path"]`, `--new-title`→`["title"]`, 4필드 복합→`["path","result","stage","title"]` 정확 일치(잉여·누락 0) |

#### TS-006: 미지정 필드·타 행 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-002 R-2 AC(b) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--kind history --stage` 단독 지정 |
| 기대 결과 | 대상 행의 `title`/`date`/`path`/`result` **및 다른 히스토리 4행 전체**가 바이트 동일 |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindHistory.test_ts006_unspecified_fields_and_other_rows_unchanged -v` |
| 결과 | Pass |
| 상세 | `test_ts006_unspecified_fields_and_other_rows_unchanged` ok — 대상 행 `title`/`date`/`path`/`result` 불변 + 다른 히스토리 4행(`others_after == others_before`) 바이트 동일 확인 |

#### TS-008: 행 수 불변 (5행)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | F-002 R-2 AC(d) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 히스토리 5행 문서 정정 |
| 기대 결과 | 응답 `history_count:5` + 파일 `history` 길이 5 (정정은 추가·삭제가 아니다) |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindHistory.test_ts008_five_row_history_count_unchanged -v` |
| 결과 | Pass |
| 상세 | `test_ts008_five_row_history_count_unchanged` ok — 픽스처 5행 전제 확인 후 정정, 응답 `history_count==5`, 파일 `history` 길이 5 유지 확인 |

#### TS-009: FIFO 미적용 — 6행 문서에서 조용한 삭제 없음 ★P0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-6 (P0)** |
| 대상 | F-002 R-2 AC(d) — "삭제 없는 정정" 전제의 핵심 게이트 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 히스토리 **6행** 문서(스키마에 `maxItems` 없어 유효)에 `--kind history --stage x` |
| 기대 결과 | **6행 유지 — 행 삭제 0건**. `_enforce_history_fifo` 미호출. 초과는 `review.history_status.fifo_trimmed:true`로 **표면화만** |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindHistory.test_ts009_six_row_history_no_silent_deletion -v` |
| 결과 | Pass |
| 상세 | `test_ts009_six_row_history_no_silent_deletion` ok — in-test 6행 문서 준비 확인, 정정 후 `history_count==6`, 파일 `history` 길이 6(삭제 0), `review.history_status.fifo_trimmed==true`·`count==6`로 초과만 표면화 확인(H-6 P0 게이트 통과) |

#### TS-010: 부가 키 삽입 금지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-7** |
| 대상 | F-002 R-2 AC(c) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 정정 후 대상 행의 키 집합 확인 |
| 기대 결과 | 정확히 `{title, date, stage, path, result}` — `corrected_at` 등 부가 키 0 (`additionalProperties:false`) |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindHistory.test_ts010_corrected_row_key_set_exact -v` |
| 결과 | Pass |
| 상세 | `test_ts010_corrected_row_key_set_exact` ok — 정정 후 대상 행 `set(row.keys()) == {"title","date","stage","path","result"}` 정확 일치, 부가 키 0 확인 |

#### TS-011: 오용 거부 — `history` + `--status`

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-2 (P0)** |
| 대상 | F-003 R-3 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--kind history --status dead` |
| 기대 결과 | `ok:false`·`invalid_args` + `message`에 `--status` 사유 + 파일 바이트 불변. **silent no-op 금지** |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindArgGuard.test_ts011_history_status_rejected -v` |
| 결과 | Pass |
| 상세 | `test_ts011_history_status_rejected` ok — `ok:false`, `error:"invalid_args"`, `message`에 `--status` 문자열 포함, 파일 스냅샷 불변 확인 |

#### TS-012: 오용 거부 — `history` + `--summary` (별칭 불허)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-2** |
| 대상 | F-003 R-3 AC(a) / P-2 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--kind history --summary "x"` |
| 기대 결과 | `ok:false`·`invalid_args` + `message`가 **`--result`를 안내** + 파일 불변. (`memoryRow.summary`에는 `maxLength:80`이 있고 `historyRow.result`에는 없어, 별칭 허용 시 검증 표면이 비결정적이 된다) |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindArgGuard.test_ts012_history_summary_rejected_with_result_guidance -v` |
| 결과 | Pass |
| 상세 | `test_ts012_history_summary_rejected_with_result_guidance` ok — `ok:false`, `error:"invalid_args"`, `message`에 `--result` 안내 포함(별칭 불허), 파일 불변 확인 |

#### TS-013: 오용 거부 — `memory` + 히스토리 전용 필드

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-2** |
| 대상 | F-003 R-3 AC(b) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--kind memory --stage x` / `--result x` / `--path x` 3케이스 |
| 기대 결과 | 각각 `ok:false`·`invalid_args` + 파일 불변 |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindArgGuard.test_ts013_memory_kind_rejects_stage tests.test_memory_tool.TestUpdateKindArgGuard.test_ts013_memory_kind_rejects_result tests.test_memory_tool.TestUpdateKindArgGuard.test_ts013_memory_kind_rejects_path -v` |
| 결과 | Pass |
| 상세 | 3케이스(`--stage`/`--result`/`--path` × `--kind memory`) 전부 `ok:false`·`error:"invalid_args"`, 파일 불변 확인 |

#### TS-014: 없는 제목 — `row_not_found` + 락 잔여 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-4 |
| 대상 | F-003 R-3 AC(c) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 존재하지 않는 히스토리 제목 + `--kind history --stage x` |
| 기대 결과 | `ok:false`·`row_not_found` + 파일 불변 + `MEMORY.json.lock` 잔여 **0건** |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindArgGuard.test_ts014_row_not_found_no_lock_residue -v` |
| 결과 | Pass |
| 상세 | `test_ts014_row_not_found_no_lock_residue` ok — `ok:false`, `error:"row_not_found"`, 파일 불변, `_residue(tmp_dir)==[]`(.lock/.tmp 잔여 0) 확인 |

#### TS-015: 정정 필드 0개 — `invalid_args`

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-2** |
| 대상 | F-003 R-3 AC(d) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--kind history` + 정정 필드 하나도 미지정 |
| 기대 결과 | `ok:false`·`invalid_args` + 파일 불변. (`--kind memory`의 필드 0개는 TS-002대로 계속 허용 — 하위호환) |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindArgGuard.test_ts015_history_zero_fields_rejected -v` |
| 결과 | Pass |
| 상세 | `test_ts015_history_zero_fields_rejected` ok — `--kind history` + 필드 0개 → `ok:false`, `error:"invalid_args"`, 파일 불변 확인(memory kind의 관대 동작이 history로 누수되지 않음) |

#### TS-016: 거부 경로 무손실 — 파일·잔여물

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-4 (P0)** |
| 대상 | F-002 R-4 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 거부 경로 전수(TS-004·TS-011~TS-015·TS-027) 실행 후 상태 확인 |
| 기대 결과 | `MEMORY.json` **바이트·mtime 동일** + 디렉토리에 `*.tmp*` **0건** + `MEMORY.json.lock` **0건** |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateHistoryLossless.test_ts016_rejection_paths_leave_no_residue -v` |
| 결과 | Pass |
| 상세 | `test_ts016_rejection_paths_leave_no_residue` ok — TS-004·TS-011~TS-015·TS-027에 해당하는 9개 거부 조합 전수 실행(모두 exit≠0), 실행 후 `_snapshot(md)` 바이트 동일, `_residue(tmp_dir)==[]`, `MEMORY.json.lock` 미존재 확인 |

#### TS-018: 동일 title 복수 매치 — 선행 1건 + 관측 노출

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-3** |
| 대상 | F-002 / P-4 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 동일 `title` 히스토리 2행 문서에 `--kind history --stage x` |
| 기대 결과 | 배열 **선행 행만** 변경 + 후행 행 불변 + 응답에 `matched_index:<선행 index>`·`match_count:2` (사용자가 복수 매치를 인지할 수 있어야 한다) |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindHistory.test_ts018_duplicate_title_corrects_leading_row_only -v` |
| 결과 | Pass |
| 상세 | `test_ts018_duplicate_title_corrects_leading_row_only` ok — 동일 title in-test 2행 구성, `matched_index==0`, `match_count==2`, 선행 행만 `stage` 변경·후행 행 바이트 동일(`trailing_before`) 확인 |

#### TS-019: `--help` 노출

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | F-001 R-1 / R-5 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `update --help` |
| 기대 결과 | `--kind`·`--stage`·`--result`·`--path` 및 `{memory,history}` 문자열이 모두 노출 (`choices=` 없이 `metavar`로) |
| 도구 | unittest / grep |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateBackCompat.test_ts019_help_exposes_kind_stage_result_path -v` + `python memory_tool.py update --help` 수동 확인 |
| 결과 | Pass |
| 상세 | `test_ts019_help_exposes_kind_stage_result_path` ok — `--help` returncode 0, stdout에 `--kind`/`--stage`/`--result`/`--path`/`{memory,history}` 전부 포함. 수동 실행 결과도 `--kind {memory,history}` 확인(`metavar` 방식, `choices=` argparse 강제 exit 2 아님) |

#### TS-020: 자가검토 블록 유지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-001 R-1 AC(b) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--kind history` 성공 호출 |
| 기대 결과 | 응답에 `review` 블록 첨부 — 변경 명령의 ambient 자가검토 계약이 신규 경로에서도 유지 |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindHistory.test_ts020_history_success_response_includes_review_block -v` |
| 결과 | Pass |
| 상세 | `test_ts020_history_success_response_includes_review_block` ok — 응답에 `"review"` 키 존재 + `review.history_status` 키 존재 확인 |

#### TS-021: 구형 서술 잔존 0 + 신형 표기 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-004 R-5 AC(a) — **교체형 AC의 "구형 잔존 0" 축** |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `README.md`·`tools.md`·`memory-learning.md` 3문서 grep |
| 기대 결과 | `--kind history` 표기 **존재** + "정정 불가"·"되돌릴 수 없" 류 서술 **0건** |
| 도구 | grep |
| 실행 명령 | `grep -n "kind history" opal/tools/memory-tool/README.md opal/core/references/tools.md opal/core/references/harness/memory-learning.md` + `grep -n "정정 불가\|되돌릴 수 없" <동 3문서>` |
| 결과 | Pass |
| 상세 | 3문서 모두 `--kind history`/`update --kind history` 표기 존재(README L78·L99, tools.md L605·L609·L698·L885, memory-learning.md L23·L83). 금지 서술("정정 불가"·"되돌릴 수 없") grep 매치 0건(exit 1) 확인 |

#### TS-022: `tools.md` — 077 영역 무변경 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-9** |
| 대상 | F-004 R-5 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `tools.md` grep + `git diff -- opal/core/references/tools.md` |
| 기대 결과 | `update` 블록에 `--kind`·`--stage`·`--result`·`--path` + 에러코드 표에 `invalid_kind` 행 + **code-scan 절 diff 0줄** |
| 도구 | grep + git diff |
| 실행 명령 | `git diff --stat -- opal/core/references/tools.md` + `git diff -- opal/core/references/tools.md` (전체 hunk 확인) |
| 결과 | Pass |
| 상세 | `git diff --stat`: 1 file changed, 6 insertions(+), 2 deletions(-). 전체 diff 확인 결과 변경 hunk는 `## memory-tool` 절(용도 1줄 + update 옵션 블록에 `--kind`/`--stage`/`--result`/`--path` 추가)과 변경이력 표 v2.8 추가행뿐 — `## code-scan`(L202) 절 및 기존 v2.5/v2.7 code-scan 행은 diff에 **0줄** 등장(077 영역 무클로버 확인). 단, `invalid_kind`는 기존 에러코드 표(L287 부근)에 078에서 이미 등재된 채였고 이번 diff에 신규 행 추가는 없었음 — 표기 존재 자체는 grep으로 확인(기존 유지, 회귀 없음) |

#### TS-023: `memory-learning.md` 재비대화 방지 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-5** |
| 대상 | F-004 R-5 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `wc -l` + 헤딩·표 grep |
| 기대 결과 | **≤84줄**(현재 81) + 신규 `##` 헤딩 **0건** + 신규 표 **0건**. 078의 슬림화 성과를 되돌리지 않는다 |
| 도구 | wc + grep |
| 실행 명령 | `wc -l opal/core/references/harness/memory-learning.md` + `git diff -- opal/core/references/harness/memory-learning.md \| grep "^+.*##"` |
| 결과 | Pass |
| 상세 | `wc -l` = 83줄(≤84 충족, 078의 81줄에서 +2). diff에 신규 `##` 헤딩 매치 0건(grep exit 1). diff 내용은 기존 FIFO 불릿 아래 정정 안내 1줄 추가 + 변경이력 표에 기존 v1.3 행 1줄 추가뿐 — 신규 표 0건 |

#### TS-026: `@header`·변경이력 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | 제약 — CONVENTIONS §@header 규칙 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `memory_tool.py`·테스트 파일 헤더 확인 |
| 기대 결과 | `@header.description`에 `--kind history` 반영 + 변경이력 `v2.1` 행 + 테스트 `@header.exports`에 신규 클래스 4종 등재 |
| 도구 | grep |
| 실행 명령 | `sed -n '1,25p' opal/tools/memory-tool/memory_tool.py` + `sed -n '1,20p' opal/tools/memory-tool/tests/test_memory_tool.py` |
| 결과 | Pass |
| 상세 | `memory_tool.py` `@header.description`에 "update --kind history로 작업 히스토리 행 정정(무손실·행수 불변, FIFO 미적용)" 반영 + 변경이력 "v2.1 2026-07-30 update --kind history 정정 명령 추가(079)" 행 확인. 테스트 파일 `@header.exports`에 `TestUpdateBackCompat`/`TestUpdateKindHistory`/`TestUpdateKindArgGuard`/`TestUpdateHistoryLossless` 4종 신규 클래스 등재 확인 |

#### TS-027: 경로 탈출 거부 (보안)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-4 |
| 대상 | F-003 보안 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--kind history --path "../../etc/"` |
| 기대 결과 | `ok:false`·`invalid_args` + 파일 불변 (기존 `_path_has_traversal` 재사용) |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindArgGuard.test_ts027_path_traversal_rejected -v` |
| 결과 | Pass |
| 상세 | `test_ts027_path_traversal_rejected` ok — `--path "../../etc/"` → `ok:false`, `error:"invalid_args"`, 파일 불변 확인(`_path_has_traversal` 재사용) |

#### TS-028: 에러코드 신설 0 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-003 / P-3 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `ERROR_CODES` 키 집합·템플릿 확인 |
| 기대 결과 | **23종 그대로**(신규 0) + `invalid_kind`·`invalid_args` 메시지 템플릿 **무변경** — 에러코드 동기화 회귀 0 |
| 도구 | unittest / grep |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindArgGuard.test_ts028_error_codes_unchanged_no_new_codes -v` |
| 결과 | Pass |
| 상세 | `test_ts028_error_codes_unchanged_no_new_codes` ok — `len(ERROR_CODES)==23`(신규 0), `invalid_kind` 템플릿 "--kind는 memory 또는 history 중 하나여야 함: {kind}" 무변경, `invalid_args` 템플릿 "인자 조합이 올바르지 않음: {detail}" 무변경 확인 |

#### TS-029: 문서 usage ↔ `--help` 일치 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | F-004 R-5 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 문서 usage 블록의 인자 목록 vs 실제 `update --help` 출력 |
| 기대 결과 | **누락·잉여 0** — 078 §5 결함 6(CLI help ↔ 문서 drift)의 재발 방지 게이트 |
| 도구 | diff |
| 실행 명령 | `~/.opal/.venv/bin/python opal/tools/memory-tool/memory_tool.py update --help` 실측 출력 vs `README.md`(L90-101)·`tools.md`(L601-611) usage 블록 대조 |
| 결과 | Pass |
| 상세 | 실제 `--help`: `--file`·`--title`·`--kind {memory,history}`·`--status`·`--summary`·`--new-title`·`--stage`·`--result`·`--path` 9개 인자. README.md는 2블록(`--kind` 생략 시 memory 예시: `--status`/`--summary`/`--new-title` + history 예시: `--stage`/`--result`/`--path`/`--new-title`)으로 7개 옵션 인자 전부 표기. tools.md는 1블록(`--kind {memory,history}`+7개 옵션) 전부 표기. 양쪽 모두 누락·잉여 0 확인 |

#### TS-030: 변경이력 3문서 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | 제약 — CONVENTIONS §변경이력 작성 의무 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 변경 3문서 변경이력 표 확인 |
| 기대 결과 (v1.1 정정) | 3문서에 **079 태스크 태그가 붙은 변경이력 행이 존재**한다: `README.md` v2.1 / `tools.md` **파일의 다음 순번**(작성 시점 예측 v2.7 → 실제 **v2.8**, 아래 근거) / `memory-learning.md` v1.3. **버전 번호는 파일 진실을 따른다** — 리터럴 고정값이 아니다 |
| 도구 | grep |
| 실행 명령 | `grep -n "^| v" opal/tools/memory-tool/README.md \| tail -5` + `grep -n "^| v2\." opal/core/references/tools.md \| tail -8` + `grep -n "^| v" opal/core/references/harness/memory-learning.md` |
| 결과 | **Pass** (초회 Partial Fail → 기대값 정정 후 Pass. PM 판정 2026-07-30) |
| 상세 (재판정, PM) | **기대값이 틀렸고 산출물은 옳았다.** PM 실측: `tools.md` v2.7은 **077 소관**(`2026-07-28 23:28`, code-scan validate 2분류), v2.8이 079 소관(`2026-07-30`, memory-tool `--kind history`). 즉 워커가 v2.8로 채번한 것은 H-9(동시 편집 클로버) 회피의 **정상 동작**이며, 시나리오가 PLAN 작성 시점(077의 v2.7 선점 이전)의 예측값을 리터럴로 굳힌 것이 오류다. → **기대 결과를 "파일의 다음 순번"으로 정정**하고 Pass로 전환. KST 시각 미포함 건도 `memory-learning.md` v1.0~v1.2가 동일하게 날짜만 쓰는 **기존 표 컨벤션**이므로 079발 회귀가 아니다(워커 관찰 그대로 수용). 3문서 전부 079 태그 행 존재 확인 |
| 상세 | README.md: `v2.1 \| 2026-07-30 11:49 KST (079)` 행 존재 — 시나리오 기대와 일치. memory-learning.md: `v1.3 \| 2026-07-30 \| 079 히스토리...` 행 존재하나 **KST 시각 미포함**(단, v1.0~v1.2도 동일하게 날짜만 표기하는 기존 표 컨벤션 — 079발 회귀 아님). tools.md: 실제 최신 행은 **v2.8**이며 시나리오가 기대한 **v2.7이 아님** — 원인은 077 태스크가 같은 워킹트리에서 이미 v2.7(code-scan validate)을 선점했고, 079 EXECUTE가 이를 인지해 클로버 회피차 v2.8로 채번함(H-9가 예견한 충돌을 회피한 정상 동작). 즉 기능적으로는 결함이 없으나, TEST-SCENARIO.md §2.2가 077 진행 상황을 반영하지 못해 리터럴 기대값(v2.7)과 실측(v2.8)이 어긋남 — **시나리오 문서 자체의 사전 정보 오류**로 판단, 코드/문서 수정 없이 보고만 함 |

---

### L2. 프로세스 통합 (자동, 실 파일 read→변경→re-read)

#### TS-007: 정정 후 문서 재로드 유효성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-002 R-2 AC(c) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | TS-005 수행 후 `show --file X` 재로드 |
| 기대 결과 | `ok:true` — `validate_document` 통과, `violations` 없음. 정정이 스키마를 깨지 않는다 |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateKindHistory.test_ts007_reload_after_correction_passes_validation -v` |
| 결과 | Pass |
| 상세 | `test_ts007_reload_after_correction_passes_validation` ok — 정정 후 `show --file` 재로드 `ok:true`(스키마 검증 통과), 재로드된 `history_rows`에서 대상 행 `stage` 반영 확인 |

#### TS-017: 동시 정정 — 클로버 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-4 (P0)** |
| 대상 | F-002 R-4 AC(b) |
| 계층 | L2 |
| **실행 방식** | **M1** (`subprocess.Popen` 실 병렬 기동 — 스레드·가짜 대역 금지) |
| 조건 | 2프로세스가 같은 문서의 **서로 다른 필드**를 동시 정정 |
| 기대 결과 | 클로버 0(둘 다 반영) **또는** 한쪽이 `lock_timeout`으로 결정론 실패. 어느 경우든 문서는 **항상 스키마 유효** + 잔여 락·tmp 0 |
| 도구 | unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m unittest tests.test_memory_tool.TestUpdateHistoryLossless.test_ts017_concurrent_different_field_corrections_no_clobber -v` |
| 결과 | Pass |
| 상세 | `test_ts017_concurrent_different_field_corrections_no_clobber` ok — 실 `subprocess.Popen` 2프로세스 병렬 기동(스레드·가짜 대역 아님), 실행 후 최소 1개 `ok:true`, 실패 시 반드시 `lock_timeout`, 재로드 `show` `ok:true`(스키마 유효), 락·tmp 잔여 0 확인 |

#### TS-025: 전 스위트 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-1 (P0)** |
| 대상 | F-001 R-1 AC(a) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `~/.opal/.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -t tests` |
| 기대 결과 | **기존 132건 전량 GREEN**(신규 케이스 제외 집계) + 신규 케이스 GREEN. FAIL 0 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/memory-tool && ~/.opal/.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -t tests` |
| 결과 | Pass |
| 상세 | 실행 출력: `Ran 163 tests in 18.566s` / `OK`(FAIL 0). T079 신규 클래스 4종(31개 메서드) 별도 `-v` 실행 확인 완료 → 163−31=132건이 기존분과 일치. 기존 132건 + 신규 31건 전량 GREEN |

#### TS-024: 목표달성 시나리오 — 배포본으로 078 히스토리 실정정 ★

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-10** (+ 태스크 목표 전체) |
| 대상 | F-004 R-5 AC(b) — **교체형 AC의 "신형 채택" 축** |
| 계층 | L2 (실환경) |
| **실행 방식** | **M3 (수동 — 알투(PM) 직접 실행)**. install 배포 + 실 `.opal/MEMORY.json` 변경은 **비가역**이므로 PM이 직접 수행한다. **op-dev-test-agent가 자동 PASS 처리할 수 없다**(PLAN Step 5 `agent: PM 직접 / 실행 방법: direct`) |
| 조건 | ① 사전 스냅샷(`git diff` 기준선 + 현재 `stage` 값 기록) ② `./scripts/install-mac.sh` ③ 배포본 CLI로 `update --file .opal/MEMORY.json --kind history --title "078 메모리 SSOT JSON 전환" --stage "완료·커밋(d7a8ce0, 447ff09)"` |
| 기대 결과 | `ok:true`·`match_count:1`·`history_count:5`·`changed:["stage"]` + `show --brief`에 새 `stage` 반영 + `git diff .opal/MEMORY.json`이 **1행 1필드만** 변경 + `~/.opal/` 직접 편집 0건 |
| 도구 | Bash (배포본 `run.sh`) + git diff |
| 실행 명령 | (PM 직접 실행 — M3, 비가역: install + 실 `.opal/MEMORY.json` 변경) `./scripts/install-mac.sh` → `update --file .opal/MEMORY.json --kind history --title "078 메모리 SSOT JSON 전환" --stage "완료·커밋(d7a8ce0, 447ff09)"` |
| 결과 | Pass |
| 상세 | PM(알투)이 비가역 실환경 작업이라 직접 수행(재실행 금지 지시에 따라 op-dev-test-agent는 재실행하지 않음). 응답 JSON: `{"ok": true, "command": "update", "kind": "history", "title": "078 메모리 SSOT JSON 전환", "matched_index": 0, "match_count": 1, "changed": ["stage"], "history_count": 5, "review": {"history_status": {"fifo_trimmed": false, "count": 5}, "violations": []}}`. `git diff .opal/MEMORY.json` 해당 hunk: `"stage": "완료·미커밋"` → `"stage": "완료·커밋(d7a8ce0, 447ff09)"` (1행 1필드). `show --brief` 발췌: `2026-07-29 \| 078 메모리 SSOT JSON 전환 \| 완료·커밋(d7a8ce0, 447ff09)`. 같은 파일의 `last_task_number: 78→79` 변경은 **079 채번(`task-number --bump`)에 의한 것으로 이번 정정과 무관** — 실측 `git diff` 재확인 결과도 이 2개 hunk(stage 1필드 + last_task_number)만 존재, `~/.opal/` 배포본은 memory_tool.py 바이트 비교로 재배포 정상 확인(직접 편집 흔적 0) |

> **왜 이것이 목표달성 시나리오인가**: 이 태스크는 "078이 만든 tool-gated 히스토리에 정정 경로가 없다"는 문제에서 출발했다. 그 최초 피해 사례(078 히스토리가 `완료·미커밋`으로 stale)를 **신설 기능으로 실제 해소**하는 것이 목표 달성의 정의다.

---

### L3. 사용자 협업

**해당 없음.** 이 태스크는 CLI 도구·참조 문서만 변경하며 화면·사용자 플로우 변경이 0건이다. `[SUPERVISOR]` 검증 대상 시나리오가 존재하지 않으므로 형식을 맞추기 위한 시나리오를 만들지 않는다. 비가역 실환경 작업(TS-024)은 PM 직접 수행(M3)으로 처리한다.

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 (a) 하위호환 | **H-1** | L1+L2 | TS-001, TS-002, TS-025 | `tests/test_memory_tool.py`:`TestUpdateBackCompat` [T079/L1-R1a] | 기존 132건 무변경 |
| R-1 (b) history 대상 동작 | H-1 | L1 | TS-003, TS-020 | `TestUpdateKindHistory` [T079/L1-R1b] | `review` 유지 |
| R-1 (c) 잘못된 kind 거부 | **H-8** | L1 | TS-004, TS-019 | `TestUpdateKindArgGuard` [T079/L1-R1c] | exit 1 + JSON |
| R-2 (a) 4필드 정정 | H-3 | L1 | TS-005 | `TestUpdateKindHistory` [T079/L1-R2a] | `changed[]` 정확성 |
| R-2 (b) 미지정 불변 | H-3 | L1 | TS-006 | `TestUpdateKindHistory` [T079/L1-R2b] | 타 행 포함 |
| R-2 (c) 스키마 통과 | **H-7** | L1+L2 | TS-007, TS-010 | `TestUpdateKindHistory` [T079/L2-R2c] | 부가 키 0 |
| R-2 (d) 행 수 불변 | **H-6 (P0)** | L1 | TS-008, **TS-009** | `TestUpdateKindHistory` [T079/L1-R2d] | 6행 FIFO 미적용 |
| R-3 (a) history 오용 | **H-2 (P0)** | L1 | TS-011, TS-012 | `TestUpdateKindArgGuard` [T079/L1-R3a] | `--status`·`--summary` |
| R-3 (b) memory 오용 | **H-2** | L1 | TS-013 | `TestUpdateKindArgGuard` [T079/L1-R3b] | 3케이스 |
| R-3 (c) 없는 제목 | H-2, H-4 | L1 | TS-014 | `TestUpdateKindArgGuard` [T079/L1-R3c] | 락 잔여 0 |
| R-3 (d) 필드 0개 | **H-2** | L1 | TS-015 | `TestUpdateKindArgGuard` [T079/L1-R3d] | history 한정 |
| R-4 (a) 거부 시 무손실 | **H-4 (P0)** | L1 | TS-016, TS-027 | `TestUpdateHistoryLossless` [T079/L1-R4a] | 바이트·mtime·잔여물 |
| R-4 (b) 동시 클로버 0 | **H-4** | L2 | TS-017 | `TestUpdateHistoryLossless` [T079/L2-R4b] | 실 subprocess 병렬 |
| R-5 (a) 구형 잔존 0 + 문서화 | H-5, H-9, H-8 | L1 | TS-021, TS-022, TS-023, TS-029, TS-030 | 산출물 검사 [T079/L1-R5a] | `≤84줄`·code-scan diff 0 |
| R-5 (b) 신형 채택 | **H-10** | L2 | **TS-024** | 실환경 M3 [T079/L2-R5b] | **목표달성 시나리오** |
| 제약 (@header·에러코드) | H-1 | L1 | TS-026, TS-028 | 산출물 검사 [T079/L1-CON] | ERROR_CODES 23 불변 |

**커버 확인**: TASK.md 요구사항 **R-1~R-5 전량 매핑**(누락 0), PLAN 기능 **F-001~F-004 전량**, 가설 **H-1~H-10 전량**. 미매핑 시나리오 0건.

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | N/A: 설정 부재 | N/A (대체 `py_compile` Pass) | 리포지토리 루트·`opal/tools/memory-tool/`에 `.flake8`/`ruff.toml`/`pyproject.toml`/`.pylintrc` 없음(`find` 결과 0건). 대체 증거: `python -m py_compile memory_tool.py tests/test_memory_tool.py` 정상 종료 |
| 2 | 타입 체크 | N/A: 설정 부재 | N/A (대체 `ast.parse` Pass) | `mypy` 미설치·설정 없음. 대체 증거: `ast.parse(open('memory_tool.py').read())` 정상 파싱 |
| 3 | 포맷터 | N/A: 설정 부재 | N/A | `black`/`autopep8` 설정 없음(미설치). 078 선례와 동일하게 정직 기재 |
| 4 | 표준 라이브러리 전용(외부 import 0건) | grep | Pass | `grep -n "^import\|^from" memory_tool.py` → `argparse/contextlib/json/os/pathlib/re/sys/time/datetime` 전부 표준 라이브러리. 외부 패키지 import 0건 |
| 5 | `@header` 갱신 + 변경이력 | grep(TS-026과 동일 근거) | Pass | `memory_tool.py` `@header.description`에 `--kind history` 반영 + 변경이력 `v2.1 2026-07-30` 행. 테스트 파일 `@header.exports`에 신규 클래스 4종 등재(TS-026 상세 참조) |

> 린트·타입·포맷 설정이 리포지토리에 없으면 `N/A: 설정 부재`로 정직하게 기재하고 `py_compile`/`ast.parse`를 대체 증거로 남긴다(078 선례).

---

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `git diff -- memory_tool.py \| grep -iE "password\|secret\|api[_-]?key\|token\|aws_\|private[_-]?key"` → 매치 0건(exit 1) |
| 2 | `--path` 경로 탈출 거부 (`_path_has_traversal` 재사용) | Pass | TS-027(`test_ts027_path_traversal_rejected`) ok — `--path "../../etc/"` → `invalid_args`, 파일 불변 |
| 3 | 락·tmp 파일이 대상 디렉토리 밖 미생성 + 실패 경로 잔여 0 | Pass | TS-016(9개 거부 조합 전수) + TS-014 + TS-017(동시성) 전부 `_residue(tmp_dir)==[]` 확인. `find opal/tools/memory-tool -iname "*.lock" -o -iname "*.tmp*"` 결과 0건(프로젝트 디렉토리 내 잔여 없음) |
| 4 | 실 `.opal/MEMORY.json` 변경이 도구 경유 1회로 한정(직접 편집 0) | Pass | `git diff .opal/MEMORY.json` = 2개 hunk(`stage` 1필드 + `last_task_number` 78→79)뿐 — TS-024(PM 직접 실행, `update --kind history` 1회) + 079 채번(`task-number --bump`) 1회, 총 도구 경유 2회 외 직접 편집 0건 |
| 5 | `~/.opal/` 배포본 직접 편집 0건 | Pass | `diff ~/.opal/tools/memory-tool/memory_tool.py opal/tools/memory-tool/memory_tool.py` → 바이트 동일(빈 diff). install 재배포로만 반영됐고 배포본 직접 편집 흔적 없음 |

---

## 7. 판정

**All Pass -- TS-001~TS-030 전량 30건 Pass.** 초회 판정은 `Partial Fail`(TS-030)이었으나, PM 재검증 결과 **기대값이 틀렸고 산출물은 옳았다** — `tools.md` v2.7은 077 소관(`2026-07-28 23:28`)이고 079가 v2.8을 쓴 것은 H-9 클로버 회피의 정상 동작이다. 시나리오의 리터럴 버전 기대값을 "파일의 다음 순번"으로 정정하고 **TS-030을 Pass로 전환**했다(상세는 TS-030 항목). 코드·산출물은 수정하지 않았다.

> 초회 판정 원문: Partial Fail -- TS-001~TS-029(29건) 전부 Pass(unittest 31개 신규 메서드 GREEN + 132건 기존 회귀 GREEN, 산출물 검사 전부 실측 통과) + TS-024(M3, PM 직접 수행) Pass + §5 코드 품질 5항목(N/A 3·Pass 2, 정직 기재) + §6 보안 5항목 전부 Pass. 유일한 결함은 TS-030 — 시나리오가 기대한 `tools.md v2.7`이 실측 `v2.8`과 불일치(원인: 077 태스크가 동일 워킹트리에서 이미 v2.7을 선점, 079가 H-9 클로버를 회피하고자 v2.8로 정상 채번 — 기능 결함 아닌 시나리오 문서의 사전 정보 오류). 핵심 기능(R-1~R-5, H-1~H-10 전 가설)은 전량 Pass이므로 Critical Fail 아님, 산출물 검사 1건(H-5 P1)만 문서 라벨 불일치라 Partial Fail로 판정. 코드/문서 수정 없이 보고만 함.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 — §3 서두에 테스트 더블 금지 명시
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 (7개 저장소)
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 (TS-001~TS-030 전량)
- [x] 가설↔시나리오 매핑(§4) 완전 — 미매핑 0건
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 `[SUPERVISOR]` — **해당 없음**(FE·화면 변경 0건). 형식 충족용 시나리오를 만들지 않는다는 판단을 §3 L3에 근거와 함께 명시
- [x] 리스크 가설 표(§1) H-1~H-10이 시나리오와 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M3) 명시
- [x] **FE 변경 시 M2 시나리오 포함** — **미해당**(FE 변경 0건, §계층·실행 방식 배치 원칙에 판정 근거 기재)
- [x] **목표 커버** — R-1~R-5 전량 §4 매핑 + 목표달성 시나리오 **TS-024**(078 히스토리 실정정) 존재

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-30 | 최초 작성 — PLAN H-1~H-10 기반 30 시나리오(L1 26 / L2 4). L3·M2는 근거를 들어 미해당 판정. 목표달성 시나리오 TS-024(078 stale 히스토리 실정정) 지정 |
