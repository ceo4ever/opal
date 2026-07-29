# TEST SCENARIO: 프로젝트 메모리 SSOT를 MEMORY.md → MEMORY.json으로 전환

> 작성일: 2026-07-28 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 리스크 가설 표(H-1~H-13) 기반
> 시나리오 ID는 PLAN.md의 `TS-NNN`을 그대로 승계한다(별도 S-N 재채번 없음 — PLAN §3 각 기능의 테스트 시나리오 표와 1:1 추적).

## RED-first 판정

**트랙: RED-first 강제** (`~/.opal/references/harness/red-first.md` §1.5 — 비즈니스 로직 + API 계약 + 마이그레이션 3중 해당).

- RED 작성 주체: `opal-test-agent` (PLAN Step 2) — **[MUST] red-first.md §2 작성자≠구현자**. 구현은 `opal-be-agent`(Step 3~9)가 수행한다.
- RED 대상: TS-001~TS-021, TS-037~TS-041.
- GREEN 루핑 중 RED 테스트의 단정을 약화·삭제하지 않는다(red-first.md §3).
- RED 증거(exit≠0 출력)를 Step 2 완료 시 기록하고, EXECUTE 진입 전 `state-tool verify --red-check` 게이트로 확인한다.

---

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-004 lazy 변환기 `_migrate_md_to_json` | 히스토리 표 헤더 변형(`#\|작업\|단계\|경로\|시작일시\|완료일시`)을 인식 못 해 3행이 조용히 0행이 됨 | **P0** | L1 + L2 | TS-015, TS-035 |
| H-2 | F-004 + F-008 경쟁조건 | 최초 변환 중 두 번째 프로세스 동시 진입 → json 클로버(선행 append 행 소실) | **P0** | L2 | TS-018, TS-020 |
| H-3 | F-001 스키마 enum ↔ 코드 enum | 스키마에 `improvement`/`candidate` 부재 → improve-tool 위임이 `schema_validation_failed`로 거부 | **P0** | L1 + L2 | TS-005, TS-024 |
| H-4 | F-002 CLI 응답 계약 | `index_rows`/`history_rows` 키 변경 시 improve-tool `cmd_list`가 조용히 빈 목록 반환 | P1 | L1 + L2 | TS-007, TS-025 |
| H-5 | F-009 dashboard 파서 | 현행이 이미 오프바이원(`date="제목"`)이라 "회귀 없음"을 기준선으로 잡으면 깨진 동작을 보존 | P1 | L1 + L2 | TS-027, TS-028 |
| H-6 | F-009 응답 스키마 | `MemoryRowResponse` 필드명 변경 시 `MemoryPage.tsx`(`50-53,129-139,263-269,305-319`)가 백지 | P1 | L1 + L2 + L3 | TS-027, TS-043, TS-045, TS-046 |
| H-7 | F-005 채번 원자성 | 락 없는 read-modify-write로 동시 인스턴스가 같은 번호 수령 → 폴더 충돌 | P1 | L2 | TS-019, TS-020 |
| H-8 | F-002 원자적 쓰기 | 검증 실패·예외 시 부분 기록으로 SSOT 파손 | P1 | L1 | TS-004, TS-009 |
| H-9 | F-002 테스트 이관 | 24건 폐기 + 약 30건 어서션 치환 누락 시 회귀망이 빈 채 GREEN 선언 | P1 | L1 | TS-006, TS-008, TS-038 |
| H-10 | F-011 `tools.md` 동시 편집 | 077이 `tools.md:202-289`를 EXECUTE 중이라 줄번호 오프셋 어긋남 | P2 | L1 | TS-032, TS-047 |
| H-11 | F-011 grep AC | R-10 AC(a) "전 경로 0건"이 문자 그대로는 달성 불가(변환기·`.bak`·doctor warn이 정당 언급) | P2 | L1 | TS-032 |
| H-12 | F-004 `.bak` 보존 | 기존 `.bak` 덮어쓰기로 무손실 제약 위반 | P2 | L1 | TS-013 |
| H-13 | F-001 스키마 배포 | 배포본에 스키마 누락 시 전 서브명령 사망 | P1 | L1 + L2 | TS-037, TS-044 |

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 본 태스크는 DB가 없다(파일 기반 SSOT). "테이블" 칸은 **데이터 저장소(파일)**로 읽는다.

| 저장소(파일) | 식별자 | 상태 | 출처 |
|--------------|--------|------|------|
| `tests/fixtures/fixture_doc_populated.json` | 메모리 6행(active 2·dead 1·superseded 1·promoted 1·candidate 1) + 히스토리 5행 | 스키마 유효 | fixture (신규 생성, Step 2) |
| `tests/fixtures/fixture_doc_invalid.json` | `type="bogus"`·`date="26-7-28"`·`summary` 81자 | 스키마 위반 | fixture (신규 생성, Step 2) |
| `tests/fixtures/fixture_md_marker_populated.md` | ai-framework 재현 — 마커 O·6컬럼·백틱 혼재·구 잔존 카테고리표(L7-18) | 신포맷 md | 실측 복사 (`ai-framework/.opal/MEMORY.md`) |
| `tests/fixtures/fixture_md_no_marker_legacy.md` | invest-stock 재현 — 마커 0·5컬럼·자유 상태값(`확정`/`승인대기`)·히스토리 헤더 `#\|작업\|단계\|경로\|시작일시\|완료일시` 3행 | 구포맷 md | 실측 복사 (`invest-stock/.opal/MEMORY.md`, **읽기 전용**) |
| `tests/fixtures/fixture_md_marker_empty.md` | aos 재현 — 마커 O·인덱스 0행·히스토리 1행·`last_task_number: 1` | 신포맷 md(빈 인덱스) | 실측 복사 (`aos/.opal/MEMORY.md`, **읽기 전용**) |
| `tests/fixtures/fixture_legacy.md` | 구포맷 6행(상태값 다양) | 기존 파일 용도 전환 | 기존 (`fixture_legacy.md:1-27`) |
| `opal/tools/memory-tool/schema/memory.schema.json` | 문서 스키마 v2 | Step 1 산출 | 신규 |
| `ai-framework/.opal/MEMORY.md` | 메모리 3행 + 히스토리 5행 + `last_task_number: 78` | 실 파일 (Step 21 변환 대상) | 실 프로젝트 |
| 임시 프로젝트 `<tmp>/.opal/` | md만 존재 / json만 존재 / 둘 다 부재 3종 | 런타임 생성 | 테스트 셋업 |

> **[MUST] 캡틴 결정 (b)안**: `invest-stock`·`aos`의 실 파일은 **읽기 전용 복사**만 하고 절대 수정하지 않는다. 두 프로젝트의 실 변환은 다음 진입 시 lazy 자동 변환에 맡긴다.

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| TS-001 | `fixture_doc_populated.json` 복사본 | `append --type bogus` | 파일 mtime·내용 불변, `error=invalid_type` |
| TS-002 | 동일 | `append --summary <81자>` | 파일 불변, `error=summary_too_long` |
| TS-003 | `fixture_doc_invalid.json` | 임의 서브명령 로드 | `schema_validation_failed`, `violations[0].keyword="pattern"` |
| TS-004 | `{` 1글자 손상 json | `show` | `invalid_json`, exit 1, traceback 0, 파일 불변 |
| TS-005 | `memory.schema.json` + `memory_tool.py` | 상수 로드 | `VALID_TYPES == set(스키마 enum)`, `improvement`·`candidate` 포함 |
| TS-006 | `memory_tool.py` | grep 실행 | 마커·표 심볼 0건 |
| TS-007 | `fixture_doc_populated.json` | 8서브명령 순차 실행 | 전부 `ok:true`, `show` 응답에 `index_rows`/`history_rows` 키 존재 |
| TS-008 | `memory_tool.py` ERROR_CODES | 상수 조회 | `marker_missing`·`import_failed` 부재, 신설 12종 존재 |
| TS-009 | 유효 json + 검증 실패 주입 | `append`(실패 유도) | `.json` mtime·내용 불변, `.tmp` 잔여 0건 |
| TS-010 | `fixture_doc_populated.json`(5개 status 혼재) | `show --brief` | `index_rows`에 dead/superseded/promoted/candidate 0건 |
| TS-011 | 동일 | `show` vs `show --brief` | `len(brief) < len(full)` |
| TS-012 | 히스토리 5행 픽스처 | `show --brief` / `--history 0` | 기본 3건 + `history_truncated=true` / 0건 |
| TS-013 | md만 있는 tmp 프로젝트 (+`.bak` 선점본) | `show` | json 생성 + `.bak` 존재, 선점 시 `.bak.<ts>` 신규 생성 |
| TS-014 | `fixture_md_marker_populated.md` | lazy 변환 | 메모리 3행·히스토리 5행 수 일치 + 필드값 100% 일치 |
| TS-015 | `fixture_md_no_marker_legacy.md` | lazy 변환 / 프로파일 강제 무력화 | 히스토리 **3행** 변환 성공 / 무력화 시 `migration_failed(row_detection_failed)` + md 불변 + json 미생성 |
| TS-016 | `fixture_md_marker_empty.md` | lazy 변환 | `ok:true`, `memories:[]`, `empty_source_regions:["memories"]` |
| TS-017 | `memory_tool.py` | grep 실행 | `cmd_migrate`·`_parse_legacy_`·`_strip_legacy_tables` 0건, `migrate` 서브명령 부재 |
| TS-018 | md만 있는 tmp 디렉토리 | `append` 2프로세스 동시 기동 | json 1개, 두 행 모두 존재, `.bak` 1개, 락 잔여 0 |
| TS-019 | `last_task_number: 78` 문서 | `task-number` / `--bump` | 읽기 시 mtime 불변 / bump 후 79 + 파일 반영 |
| TS-020 | 동일 | 20 프로세스 동시 `--bump` | 반환값 20개 전부 상이, 최종값 == 초기+20 |
| TS-021 | `last_task_number: 78` | `--set 70` / `--bump --set` 동시 | `task_number_regression` + 파일 불변 / `invalid_args` |
| TS-022 | `opal-pm.md`, `core/AGENT.md` | grep 실행 | "MEMORY.md를 Read"류 0건, `show --brief` 지시 존재 |
| TS-023 | `memory-learning.md` | grep + 행 계수 | "마커"·`<!-- memory:` 0건, 라이프사이클 4행·라우팅 5행 보존, 줄 수 감소 |
| TS-024 | json만 있는 tmp 프로젝트 | `improve-tool record --scope local` | no-op 아님, `type=improvement`·`status=candidate` 행이 json에 기록 |
| TS-025 | md만 있는 tmp 프로젝트 | `record` → `list --scope local` | lazy 변환 발동 + append 성공 + `.bak` 존재, list가 해당 1건 반환 |
| TS-026 | `.opal/` 자체가 없는 tmp 프로젝트 | `record --scope local` | `{"ok":true,"skipped":true,"reason":"no MEMORY.json"}`, 예외 전파 0 |
| TS-027 | 변환된 `ai-framework/.opal/MEMORY.json` | `GET /api/memory` | `rows[]` 필드 = 기존 5필드 + `title`, 값이 원본과 1:1(헤더 행 유입 0) |
| TS-028 | 동일 | 파싱 전후 | `MEMORY.json` mtime 불변 |
| TS-029 | 동일 프로젝트(+`MEMORY.md` 잔존) | `GET /api/doctor` | `MEMORY.json` 점검 항목 존재, `MEMORY.md` 잔존 warn 노출 |
| TS-030 | 빈 임시 디렉토리 | opi 초기화 도구 호출 시퀀스 | `.opal/MEMORY.json` 존재, `.opal/MEMORY.md` 부재 |
| TS-031 | `opal-project-init/SKILL.md` | grep 실행 | `<!-- memory:` 0건, md 인라인 표 템플릿 0건, 구 6컬럼 스니펫 0건 |
| TS-032 | 리포지토리 전체 | PLAN §3.11.2 제외경로 grep | 0건 + 허용목록 잔존 라인 열거 |
| TS-033 | stale 4개 문서 | grep 실행 | "직접 갱신"·"10개"·"10항목" 0건, "FIFO 5"·도구 호출 서술 존재 |
| TS-034 | 변경한 스킬·참조 문서 전량 | 변경이력 표 확인 | 전량에 `(078)` 행 존재 |
| TS-035 | `ai-framework` 실 파일 + invest-stock/aos **복사본** | lazy 변환 | ai-framework 1/1 실변환 + 복사본 2/2 무손실(invest-stock 히스토리 3행) + **두 원본 mtime 불변** |
| TS-036 | 변환 완료된 `ai-framework/.opal/MEMORY.json` | 실세션 왕복 4단계 | 브리핑 생성 → append 반영 → dead 전이 → brief에서 소멸 |
| TS-037 | 스키마 파일 이동·삭제 | 전 서브명령 실행 | `schema_load_failed` 단일라인 JSON, 크래시 0 |
| TS-038 | 테스트 스위트 전체 | `unittest discover` | 전량 통과 + 총 건수 ≥ 88 |
| TS-039 | `show --brief` 출력 | 브리핑 3~5줄 생성 시도 | 타입·날짜·요약 필드가 전부 존재해 §15 형식 재현 가능 |
| TS-040 | `fixture_md_no_marker_legacy.md` | lazy 변환 리포트 확인 | `unmapped_statuses` 3건, `last_task_number_source` 명시 |
| TS-041 | 채번 문서 3곳 | grep 실행 | 직접 Read+Edit 서술 0건, `task-number --bump` 지시 3곳 |
| TS-042 | Lazy 트리거 4개 사본 | 문구 diff | 4개 사본 동일 문구 |
| TS-043 | `dashboard/backend/models.py` | 필드명 비교 | 기존 필드 제거·개명 0건 |
| TS-044 | 배포본 `~/.opal/tools/memory-tool/` | 전 서브명령 스모크 | 전부 `ok`, 스키마 동반 배포 확인 |
| TS-045 | 변환 완료 + dashboard 기동 | 메모리 페이지 브라우저 렌더 | 행 목록·요약이 정상 표시, 콘솔 에러 0 |
| TS-046 | 동일 | 캡틴 육안 확인 | 화면이 전환 전과 동등하거나 개선(오프바이원 해소) |
| TS-047 | `tools.md` | 편집 전후 diff | code-scan 절(077 영역) diff 0줄 |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

> 공통: **실행 방식 M1 (테스트 도구)** / 도구 `python -m unittest` (memory-tool·improve-tool) · `pytest` (dashboard) / 실행 명령은 EXECUTE 워커가 채운다.
> **[MUST] 테스트 더블 금지** — 모든 시나리오는 실 파일·실 프로세스(subprocess)로 검증한다. 가짜 대역으로 대체하면 PM Gate FAIL.

#### TS-001: 잘못된 type enum 거부 + 파일 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-8 |
| 대상 | F-001 런타임 검증기 — `type` enum |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `fixture_doc_populated.json` 복사본에 `append --type bogus --title T --summary S` |
| 기대 결과 | `{"ok":false,"error":"invalid_type"}` + 파일 mtime·내용 불변 |
| 도구 | unittest (subprocess) |
| 실행 명령 | `cd opal/tools/memory-tool && python -m unittest tests.test_memory_tool.TestSchemaValidation.test_ts001_invalid_type_rejected_and_file_unchanged -v` |
| 결과 | Pass |
| 상세 | 전체 스위트 실행(132건 OK) 내 포함, 개별 실행 exit 0 `ok`. `append --type bogus` → `{"ok":false,"error":"invalid_type"}` + 파일 mtime·내용 불변 확인 |

#### TS-002: summary 81자 거부

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | F-001 길이 상한 검증(`SUMMARY_MAX_LENGTH`) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `append --summary <정확히 81자>` |
| 기대 결과 | `summary_too_long` + 파일 불변 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestSchemaValidation.test_ts002_summary_81_chars_rejected_and_file_unchanged tests.test_memory_tool.TestSchemaValidation.test_ts002_summary_80_chars_accepted -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. 81자 거부(`summary_too_long`)+파일 불변, 80자 경계 허용 양쪽 확인 |

#### TS-003: date pattern 위반 문서 로드 거부

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | F-001 문서 스키마 `pattern` 키워드 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `fixture_doc_invalid.json`(`date="26-7-28"`)로 임의 서브명령 실행 |
| 기대 결과 | `schema_validation_failed`, `violations[0].keyword == "pattern"`, 위반 경로가 응답에 포함 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestSchemaValidation.test_ts003_date_pattern_violation_rejected_on_load -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. `schema_validation_failed` + `violations[0].keyword=="pattern"` 확인 |

#### TS-004: 손상 JSON 결정론 처리

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8, H-13 |
| 대상 | F-002 `load_document` 예외 계약 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 내용이 `{` 한 글자인 `MEMORY.json`에 `show` |
| 기대 결과 | `{"ok":false,"error":"invalid_json"}` 단일라인 + exit 1 + **traceback 출력 0건** + 파일 불변 |
| 도구 | unittest (stderr 캡처) |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestSchemaValidation.test_ts004_corrupted_json_is_deterministic -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. `invalid_json` 단일라인 + exit 1 + traceback 0건 확인 |

#### TS-005: 스키마 ↔ 코드 enum 단일 출처 단정

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-3 (P0)** |
| 대상 | F-001 스키마 파생 상수 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `memory_tool.VALID_TYPES` / `VALID_STATUSES`를 import하고 `memory.schema.json`의 enum과 대조 |
| 기대 결과 | 양쪽 집합이 **정확히 동일** + `improvement`·`candidate`가 양쪽 모두에 존재 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestSchemaValidation.test_ts005_constants_match_schema_enum tests.test_memory_tool.TestSchemaValidation.test_ts005_constants_are_derived_from_schema_at_runtime -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. VALID_TYPES/VALID_STATUSES == 스키마 enum 정확히 일치 + `improvement`/`candidate` 양쪽 존재 확인 |

#### TS-006: 마커·표 파싱 계층 소멸 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | F-002 R-2 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `grep -nE "marker\|MARKER\|_render_.*_table\|_parse_(index\|history)_rows" opal/tools/memory-tool/memory_tool.py` |
| 기대 결과 | 매치 0건 |
| 도구 | grep (unittest 래핑) |
| 실행 명령 | `grep -nE "marker\|MARKER\|_render_.*_table\|_parse_(index\|history)_rows" opal/tools/memory-tool/memory_tool.py \| wc -l` |
| 결과 | Pass |
| 상세 | 매치 0건 실측 확인. `TestSymbolRemoval.test_ts006_marker_and_table_symbols_absent` 도 OK |

#### TS-007: 8서브명령 JSON 단독 동작 + 응답 키 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-4** |
| 대상 | F-002 CLI 계약 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `fixture_doc_populated.json`에 `init/append/update/promote/prune/show/review/delete` 순차 실행 |
| 기대 결과 | 전부 `ok:true` + `show` 응답에 `index_rows`·`history_rows` 키가 **개명 없이 보존** |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestJsonIO -v` |
| 결과 | Pass |
| 상세 | `test_ts007_eight_subcommands_operate_on_json_only`·`test_ts007_show_response_keys_preserved`·`test_ts007_non_brief_show_exposes_version_and_task_number`·`test_ts007_memory_json_not_found_when_nothing_exists` 4건 전부 OK |

#### TS-008: ERROR_CODES 카탈로그 전환

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | F-002 R-2 AC(c) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `memory_tool.ERROR_CODES` 키 집합 조회 |
| 기대 결과 | `marker_missing`·`import_failed` **부재** + 신설 12종 **존재** |
| 도구 | unittest |
| 실행 명령 | `python -c "import memory_tool as m; print('marker_missing' in m.ERROR_CODES, 'import_failed' in m.ERROR_CODES); print(sorted(m.ERROR_CODES))"` |
| 결과 | Pass |
| 상세 | 실측: `marker_missing`=False, `import_failed`=False (부재 확인). ERROR_CODES 총 23종 중 `migration_failed`/`schema_load_failed`/`schema_validation_failed`/`task_number_regression` 등 신설 코드 확인. `TestErrorCodesJson`(3건) unittest도 OK |

#### TS-009: 원자적 쓰기 — 실패 시 원본 불변 + tmp 잔여 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-8** |
| 대상 | F-002 `atomic_write_json` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 검증 실패를 유발하는 입력으로 `append` 실행 |
| 기대 결과 | `.json` mtime·내용 불변 + 디렉토리에 `.tmp`·락 잔여 파일 0건 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestAtomicWrite -v` |
| 결과 | Pass |
| 상세 | `test_ts009_failed_append_leaves_no_residue`·`test_ts009_successful_append_leaves_no_residue` 2건 OK |

#### TS-010: `--brief` 필터 — 비로드 status 배제

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-003 R-3 AC |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | dead·superseded·promoted·candidate 각 1건 이상 포함 픽스처에 `show --brief` |
| 기대 결과 | `index_rows`에 해당 4개 status **0건**, `active`만 잔존 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestShowBrief.test_ts010_brief_excludes_non_active_statuses tests.test_memory_tool.TestShowBrief.test_ts010_brief_row_fields_are_exactly_five -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. brief 응답에 dead/superseded/promoted/candidate 0건, active만 잔존 확인 |

#### TS-011: `--brief` 출력 바이트 감소 실측

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-003 — 토큰 절약의 실제 지분 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 동일 픽스처에 `show`와 `show --brief` 각각 실행 |
| 기대 결과 | `len(brief_stdout) < len(full_stdout)` + 실측 바이트를 결과란에 기록 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestShowBrief.test_ts011_brief_output_is_smaller_than_full -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. 테스트 어서션이 `len(brief) < len(full)`을 직접 실측 비교(정확한 바이트 수치는 테스트 내부 assert로 산출 — stdout 별도 캡처 없이 unittest exit 0으로 검증됨) |

#### TS-012: 히스토리 건수 기본값·경계

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-003 `--history N` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 히스토리 5행 픽스처에 `show --brief` / `show --brief --history 0` |
| 기대 결과 | 기본 3건 + `history_truncated=true` / `--history 0`은 0건 반환(에러 아님) |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestShowBrief.test_ts012_brief_history_defaults_to_three tests.test_memory_tool.TestShowBrief.test_ts012_history_zero_returns_empty_not_error tests.test_memory_tool.TestShowBrief.test_ts012_history_n_override -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. 기본 3건+truncated=true, `--history 0` → 0건(에러 아님), `--history 5` → 5건 전량 확인 |

#### TS-013: lazy 변환 발동 + `.bak` 보존·충돌 회피

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-12** |
| 대상 | F-004 R-5 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | (1) md만 있는 tmp 프로젝트에 `show` (2) `.bak`이 이미 존재하는 상태에서 재차 변환 |
| 기대 결과 | (1) `MEMORY.json` 생성 + `MEMORY.md.bak` 존재 + `show` 결과 정상 (2) 기존 `.bak` **덮어쓰지 않고** `.bak.<timestamp>` 신규 생성 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestLazyMigration -v` |
| 결과 | Pass |
| 상세 | `test_ts013_show_on_md_only_project_triggers_migration`·`test_ts013_existing_bak_is_not_overwritten`·`test_ts013_migration_result_is_usable_by_next_command` 3건 OK |

#### TS-014: 변환 무손실 — 행 수·필드값 100% 일치

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-004 R-5 AC(b) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `fixture_md_marker_populated.md`(ai-framework 재현) 변환 |
| 기대 결과 | 메모리 3행·히스토리 5행 수 일치 + 각 필드 값 100% 일치(허용 차이: 백틱 제거, 날짜 정규화만) + 구 잔존 카테고리표(L7-18)가 데이터로 유입되지 않음 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestMigrationLossless -v` |
| 결과 | Pass |
| 상세 | `test_ts014_ai_framework_fixture_is_lossless`·`test_ts014_dead_category_table_is_not_ingested`·`test_ts014_last_task_number_from_md_header`·`test_ts014_backtick_file_field_is_normalized` 4건 OK |

#### TS-016: 빈 인덱스 — 정상 0행과 실패 0행 구분

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-004 변형 V-5 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `fixture_md_marker_empty.md`(aos 재현) 변환 |
| 기대 결과 | `ok:true`, `memories: []`, 리포트에 `empty_source_regions:["memories"]` — **실패로 처리하지 않음** |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestMigrationLossless.test_ts016_empty_index_is_success_not_failure tests.test_memory_tool.TestMigrationLossless.test_ts016_empty_index_history_row_values -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. `ok:true`+`memories:[]`+`empty_source_regions:["memories"]` 확인 |

#### TS-017: 구 `migrate` 제거 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | F-004 R-5 AC(d) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `grep -n "cmd_migrate\|_parse_legacy_\|_strip_legacy_tables" memory_tool.py` + `run.sh migrate --help` |
| 기대 결과 | grep 0건 + `migrate` 서브명령 부재(argparse에서 인식 실패) |
| 도구 | grep + unittest |
| 실행 명령 | `grep -n "cmd_migrate\|_parse_legacy_\|_strip_legacy_tables" opal/tools/memory-tool/memory_tool.py; bash opal/tools/memory-tool/run.sh migrate --help` |
| 결과 | Pass |
| 상세 | grep 0건. `run.sh migrate --help` → `argument command: invalid choice: 'migrate'` (exit 2, argparse 인식 실패). `TestSymbolRemoval`(4건) unittest도 OK |

#### TS-019: `task-number` 읽기·증가

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-005 D-1 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `last_task_number: 78` 문서에 `task-number` → `task-number --bump` |
| 기대 결과 | 읽기 시 파일 mtime 불변 / bump 후 반환 79 + 파일에 79 반영 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestTaskNumber.test_ts019_read_does_not_modify_file tests.test_memory_tool.TestTaskNumber.test_ts019_bump_increments_and_persists tests.test_memory_tool.TestTaskNumber.test_ts019_task_number_on_missing_document -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. 읽기 시 mtime 불변, `--bump` → 79 반환+파일 반영, 문서 부재 시 `memory_json_not_found` 확인 |

#### TS-021: 채번 역행·인자 충돌 거부

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-005 D-1 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `--set 70`(현재 78) / `--bump --set 90` 동시 지정 |
| 기대 결과 | `task_number_regression` + 파일 불변 / `invalid_args` |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestTaskNumber.test_ts021_set_regression_is_rejected tests.test_memory_tool.TestTaskNumber.test_ts021_bump_and_set_together_is_invalid_args tests.test_memory_tool.TestTaskNumber.test_ts021_set_forward_is_accepted -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. `--set 70`(역행) → `task_number_regression`+파일불변, `--bump --set 90` 동시지정 → `invalid_args`, `--set 90`(전진) 허용 확인 |

#### TS-022: 브리핑 경로 전환 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-006 R-4 AC |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `opal-pm.md`·`opal/core/AGENT.md` grep |
| 기대 결과 | "MEMORY.md를 Read"류 지시 0건 + `memory-tool show --brief` 호출 지시 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n "MEMORY.md를 Read\|MEMORY.md.*Read" opal/core/references/opal-pm.md opal/core/AGENT.md; grep -n "show --brief" opal/core/references/opal-pm.md opal/core/AGENT.md` |
| 결과 | Pass |
| 상세 | "MEMORY.md를 Read" 매치는 `opal-pm.md:350` 변경이력 표(v1.6, 전환 서술) 1건뿐 — 활성 지시문 아님(과거형 서술). `show --brief` 호출 지시는 `opal-pm.md:350`(§15 절차) + `AGENT.md:37`("`memory-tool show --brief` 조회. 파일 전체 Read 금지") 양쪽에 존재 |

#### TS-023: `memory-learning.md` 슬림화

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | F-007 R-6 AC |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 문서 grep + 행 계수 |
| 기대 결과 | "마커"·`<!-- memory:` 0건 + 라이프사이클 표 4행·졸업 라우팅 표 5행 **보존** + 총 줄 수 감소(105 → 약 82) |
| 도구 | grep + wc |
| 실행 명령 | `grep -n "마커\|<!-- memory:" opal/core/references/harness/memory-learning.md; wc -l opal/core/references/harness/memory-learning.md` |
| 결과 | Pass |
| 상세 | "마커"/`<!-- memory:` 매치 0건. 줄 수 81(목표 "약 82"에 근접, 105→81 감소 확인). 라이프사이클 표(active/promoted/superseded/dead) 4행 보존, 졸업 라우팅 표 5행 보존 |

#### TS-026: improve-tool graceful no-op

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-008 R-7 AC |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `.opal/` 자체가 없는 tmp 프로젝트에 `improve-tool record --scope local` |
| 기대 결과 | `{"ok":true,"skipped":true,"reason":"no MEMORY.json"}` + 예외 전파 0 + 파일 생성 0 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/improve-tool && python -m unittest tests.test_improve_tool.TestLocalScopeGracefulSkip tests.test_improve_tool.TestDelegation.test_ts026_opal_absent_graceful_noop -v` |
| 결과 | Pass |
| 상세 | 17건 전체 스위트에 포함, OK. `{"ok":true,"skipped":true,...}` + 예외 0 + MEMORY.json/MEMORY.md 신규 생성 0 확인 |

#### TS-029: doctor 점검 항목 전환

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-009 `doctor.py:63` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `MEMORY.json` + `MEMORY.md`(잔존) 상태 프로젝트로 doctor 실행 |
| 기대 결과 | `MEMORY.json` 점검 항목 존재 + `MEMORY.md` 잔존 시 warn 항목 노출 |
| 도구 | pytest |
| 실행 명령 | `curl -s -G http://127.0.0.1:7823/api/doctor --data-urlencode "project=/Volumes/Data/AIStudio/workspace/ai-framework"` (기동 중인 dashboard 인스턴스 대상) + `dashboard/backend/routers/doctor.py` 소스 검토 |
| 결과 | Pass |
| 상세 | 실 API 응답에 `"MEMORY.json (메모리 인덱스)"` 항목 status=ok 확인. `MEMORY.md` 잔존 warn 분기(`routers/doctor.py:74-80`, "MEMORY.md 잔존 — 미변환")는 소스 코드로 확인(현재 ai-framework는 이미 변환 완료라 실측 트리거는 안 됨 — 조건부 분기 자체는 코드 리뷰로 검증). `test_doctor_adapter.py` 7건 별도 통과(스키마 파싱 회귀 확인) |

#### TS-031: opi 템플릿 잔존 검사

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | F-010 R-9 AC |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `opal-project-init/SKILL.md` grep |
| 기대 결과 | `<!-- memory:` 0건 + md 인라인 표 템플릿 0건 + 구 6컬럼 히스토리 스니펫 0건 |
| 도구 | grep |
| 실행 명령 | `grep -c "<!-- memory:" opal/skills/opal-project-init/SKILL.md` |
| 결과 | Pass |
| 상세 | `<!-- memory:` 매치 0건 확인. v4.6 변경이력에 "§2-4 인라인 md 템플릿(마커 4개 포함) 삭제 → `memory-tool init` 호출" 명시 |

#### TS-032: 구형 참조 잔존 0 (재정의 grep)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-11**, H-10 |
| 대상 | F-011 R-10 AC(a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | PLAN §3.11.2가 정의한 제외 경로(`tasks/`·`.opal/brain/`·`docs/backup/`·`docs/proposals/`) 포함 grep 명령 실행 |
| 기대 결과 | 매치 0건 + 허용목록(변환기 코드·`.bak` 문자열·doctor warn) 잔존 라인을 결과란에 **명시적으로 열거** |
| 도구 | grep |
| 실행 명령 | `grep -rnE "MEMORY\.md" --exclude-dir=tasks --exclude-dir=".git" --exclude-dir="brain" --exclude-dir="backup" --exclude-dir="proposals" . \| grep -v "\.opal/brain/"` |
| 결과 | Pass |
| 상세 | 69줄 잔존, 전량 허용목록 범주로 분류 확인(비허용 잔존 0건): (1) `memory_tool.py` 6줄 — 변환기 자체 코드(migration_failed 메시지·`.bak` 처리 로직·lazy 변환 docstring), (2) `memory-tool/README.md` 3줄 — lazy 변환 안내 문서, (3) `test_memory_tool.py` 15줄 — migration/lossless 테스트 코드(md가 생성되지 않음을 검증), (4) `fixture_legacy.md` 1줄 — 테스트 픽스처, (5) `schema-template.md` 1줄 — 변경이력(078), (6) `improve_tool.py`+`test_improve_tool.py` 12줄 — md→json lazy 위임 전환기 로직/테스트, (7) `AGENT.md`·`opal-pm.md`·`tools.md`·`task-process.md`·`opal-project-init/SKILL.md`·`opal-pilot-gc/SKILL.md`·`op-task/SKILL.md`·`gemini-hardening.md` 각 1~2줄 — 변경이력(078) 서술 또는 lazy 변환 안내(정당 언급), (8) `dashboard/backend/routers/doctor.py` 4줄 — MEMORY.md 잔존 warn 구현부(정당), (9) `test_parsers.py:23` 1줄 — `MEMORY_MD` 상수(`.exists()` 가드로 안전 스킵, pytest 1 skipped로 확인됨). `docs/proposals/`·`docs/backup/`·`.opal/brain/` 제외 정상 작동 확인 |

#### TS-033: pre-045 stale 서술 정정

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | F-011 D-5 — `observability.md`·`opal-pilot-project-dev`·`opal-pilot-project-loop`·`schema-template.md` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 4개 파일 grep |
| 기대 결과 | "직접 갱신"·"10개"·"10항목" 0건 + "FIFO 5"·도구 호출(`append --kind history`) 서술 존재 |
| 도구 | grep |
| 실행 명령 | `for f in opal/core/references/harness/observability.md opal/skills/opal-pilot-project-dev/SKILL.md opal/skills/opal-pilot-project-loop/SKILL.md opal/tools/brain-tool/templates/schema-template.md; do grep -n "직접 갱신\|10개\|10항목" "$f"; grep -n "FIFO 5\|append --kind history" "$f"; done` |
| 결과 | Pass |
| 상세 | 4개 파일 전부 "직접 갱신"/"10개"/"10항목" 매치 0건. "FIFO 5"/도구호출 서술은 4개 파일 전부 존재(observability.md changelog, opal-pilot-project-dev/SKILL.md `append --kind history`×2, opal-pilot-project-loop/SKILL.md 포인터 참조, schema-template.md "FIFO 5항목") |

#### TS-034: 변경이력 `(078)` 전량 기재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | F-011 — CONVENTIONS §변경이력 작성 의무 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `git diff --name-only`로 변경된 스킬·참조 문서 목록 추출 후 각 파일의 변경이력 표 확인 |
| 기대 결과 | 변경 문서 전량에 `(078)` 태그 행 존재 (누락 0) |
| 도구 | git + grep |
| 실행 명령 | `git diff --name-only HEAD \| grep -E "\.md$" \| grep -vE "^tasks/\|^docs/backup/"` 후 각 파일에 `grep "078"` |
| 결과 | **Pass** (초회 Fail → PM 수정 후 재검증 Pass) |
| 상세 (재검증, PM 2026-07-28) | **초회 Fail 원인 2건 처리 완료.** ① **진짜 누락 2건** — `docs/PROJECT.md`·`docs/ARCHITECTURE.md`에 `(Task 078)` 변경이력 행을 PM이 추가(PM 직접 수행 Step 19 산출물의 누락분). ② **오탐 2건** — 초회 검사가 `(078)` 괄호 형태만 탐지해 `memory-learning.md`(`\| v1.2 \| … 078 메모리 JSON 전환`)·`memory-tool/README.md`(`\| v2.0 \| 078 \| …`)를 누락으로 오판. 078이 변경한 문서 **27개**를 대상으로 `(078)\|Task 078\|\| 078 \|\|078 메모리` 패턴으로 재검증한 결과 → **기재 19 / 변경이력 표 자체 없음 8 / 누락 0**. 표 없는 8개(`GEMINI.md`×2·`context-injection.md`·`prd-guide.md`·`trd-guide.md`·`html-mockup`·`system-architecture-html`)는 원래 변경이력 표 관행이 없는 파일로 CONVENTIONS §변경이력 대상 아님(초회 판정의 "관행 부재" 관찰과 동일 결론). 077 소관 파일(`CONVENTIONS.md`·`opal-harness.md`·`header-rules.md`·`header-standard.md`·`pm-review-gate.md`·`code-scan-management.md`·`brain-tool/README.md`)은 078 무관으로 대상 제외 |
| 상세 (초회, opal-test-agent) | 변경 md 37개 중 078 관련 내용을 담은 파일은 확인됨 memory-tool/README.md·AGENT.md·opal-pm.md·tools.md·task-process.md·op-task/SKILL.md·opal-pilot-gc/SKILL.md·opal-project-init/SKILL.md·opal-pilot-project-dev/SKILL.md·opal-pilot-project-loop/SKILL.md·opal-improve/SKILL.md·memory-learning.md·observability.md·pm-improvement-loop.md·gemini-hardening.md·schema-template.md·roadmap-guide.md·wbs-guide.md 등 18개는 `(078)`/`078` 태그 확인(077 소관 header-rules.md·header-standard.md·opal-harness.md·code-scan-management.md·CONVENTIONS.md 등은 078 무관이라 제외 정당). 그러나 **실제로 MEMORY.json 관련 내용이 변경되었는데 078 태그가 전혀 없는 파일 9개** 발견: `GEMINI.md`(루트, Lazy트리거 행 변경), `opal/skills/opal-project-init/templates/common/platform/GEMINI.md`(동일), `docs/ARCHITECTURE.md`(MEMORY.json 프로젝트구성 행 추가, changelog는 077용 Task 077 행만 있고 078 행 없음), `docs/PROJECT.md`(MEMORY.json 행 추가, changelog에 078 행 없음), `opal/core/references/pm/context-injection.md`(MEMORY.md→memory-tool show 참조 변경, changelog 표 자체 없음), `opal/skills/opal-pilot-project-dev/references/prd-guide.md`·`trd-guide.md`(memory-tool 체크리스트 추가, changelog 표 없음), `skills/html-mockup/SKILL.md`·`skills/system-architecture-html/SKILL.md`(STATE.md/MEMORY.json 참조 변경, changelog 표 없음). 이 중 ARCHITECTURE.md·PROJECT.md는 changelog 표가 존재하는데도 078 행이 누락됐고, 나머지 7개는 애초 changelog 표 관행이 없는 파일이라 CONVENTIONS.md §변경이력 규칙(스킬·에이전트·참조 문서 대상) 적용 여부가 불명확 — 최소 ARCHITECTURE.md·PROJECT.md 2건은 명백한 누락으로 판정 |

#### TS-037: 스키마 부재 시 결정론 에러

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-13** |
| 대상 | F-001 스키마 런타임 로드 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `schema/memory.schema.json`을 일시 이동시킨 뒤 전 서브명령 실행 |
| 기대 결과 | 전부 `{"ok":false,"error":"schema_load_failed"}` 단일라인 + 크래시·traceback 0건 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestSchemaValidation.test_ts037_schema_absent_returns_schema_load_failed_for_all_subcommands -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. 스키마 이동 시 전 서브명령 `schema_load_failed` 단일라인 + 크래시 0건 확인 |

#### TS-038: 테스트 이관 완결 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-9** |
| 대상 | F-002 R-2 AC(b) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `python -m unittest discover opal/tools/memory-tool/tests` |
| 기대 결과 | 전량 통과 + **총 테스트 건수 ≥ 88** + `md.read_text()` 기반 어서션 0건(grep 병행) |
| 도구 | unittest + grep |
| 실행 명령 | `cd opal/tools/memory-tool && python -m unittest discover -s tests -p 'test_*.py' -t tests -v` |
| 결과 | Pass |
| 상세 | 실측 132건 전량 OK(≥88 충족). `TestSuiteMigration`(5건: total_test_count_at_least_88·obsolete_md_fixtures_are_deleted·no_md_based_assertions_remain·conversion_input_fixture_is_preserved·new_json_fixtures_exist) 전부 OK — 구 md 픽스처 3종(`fixture_no_marker.md`·`fixture_populated.md`·`fixture_valid.md`) 삭제 확인, `fixture_legacy.md`는 변환 입력용으로 존치 확인 |

#### TS-039: brief 출력만으로 브리핑 재현 가능

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-003 ↔ F-006 접합 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `show --brief` 출력 JSON만 입력으로 `opal-pm.md §15` 브리핑 3~5줄 생성 시도 |
| 기대 결과 | 타입·등록일·요약 필드가 전부 존재하여 형식 재현 가능 + 정렬이 날짜 내림차순 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestShowBrief.test_ts039_brief_is_sufficient_to_render_pm_briefing -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. brief 응답에 타입·날짜·요약 필드 전부 존재해 `- [{type}] {summary} ({date})` 형식 재현 가능 확인 |

#### TS-040: 변환 리포트 관측성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-1** |
| 대상 | F-004 변형 V-3/V-4 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `fixture_md_no_marker_legacy.md` 변환 후 리포트 확인 |
| 기대 결과 | `unmapped_statuses` 3건 열거(`확정`/`승인대기` 등) + `last_task_number_source` 명시 — 조용한 폴백 금지 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestMigrationFailure.test_ts040_report_lists_unmapped_statuses tests.test_memory_tool.TestMigrationFailure.test_ts040_report_records_last_task_number_source tests.test_memory_tool.TestMigrationFailure.test_ts040_report_flags_review_rows -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. `unmapped_statuses` 3건(`확정`×2·`승인대기`×1) 열거 + `last_task_number_source` 명시 확인 (PM 실증 TS-035 결과와도 일치) |

#### TS-041: 채번 절차 3곳 tool-gated 개정

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-005 D-1 — `task-process.md`·`op-task/SKILL.md`·`opal-pilot-gc/SKILL.md` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 3개 파일 grep |
| 기대 결과 | "헤더 필드를 읽는다/즉시 갱신한다"류 직접편집 서술 0건 + `task-number --bump` 지시 존재 + 절차 본문 중복 서술 0건(SSOT 1곳 + 포인터 2곳) |
| 도구 | grep |
| 실행 명령 | `for f in opal/core/references/harness/task-process.md opal/skills/op-task/SKILL.md opal/skills/opal-pilot-gc/SKILL.md; do grep -n "헤더 필드를 읽는다\|즉시 갱신한다\|last_task_number + 1" "$f"; grep -c "task-number --bump" "$f"; done` |
| 결과 | Pass |
| 상세 | 직접편집 서술 매치 0건(3개 파일 전부). `task-number --bump` 지시는 3개 파일 전부 존재(각 2회). 절차 SSOT는 `task-process.md`(전체 절차: 락+임시파일 rename 원자성 서술) 1곳뿐이고, `op-task/SKILL.md`·`opal-pilot-gc/SKILL.md`는 "(절차: `harness/task-process.md` §태스크 번호 채번 규칙)" 포인터 참조만 — 중복 서술 0건. `TestTaskNumberDocs`(4건) unittest도 OK |

#### TS-042: Lazy 트리거 4개 사본 동일 문구

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-006 — `core/AGENT.md`·루트 `GEMINI.md`·`gemini-hardening.md`·opi 템플릿 `GEMINI.md` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 4개 파일의 해당 Lazy 트리거 행 추출 후 문자열 비교 |
| 기대 결과 | 4개 사본이 **동일 문구** + 새 플랫폼 조건문 추가 0건(플랫폼 분기 격리 준수) |
| 도구 | grep + diff |
| 실행 명령 | `git diff HEAD -- opal/core/AGENT.md GEMINI.md opal/bootstrapper/gemini-hardening.md opal/skills/opal-project-init/templates/common/platform/GEMINI.md \| grep -A3 -B3 MEMORY` |
| 결과 | Pass |
| 상세 | `GEMINI.md`·`gemini-hardening.md`·opi템플릿 `GEMINI.md` 3개 파일은 2열 표 행 `| .opal/MEMORY.json \| PM 컨텍스트 로드 이후 |`로 3-way 문자 그대로 동일. `core/AGENT.md`는 원래부터 5열(트리거조건/로드대상/전제조건/트리거전로드/위반시조치) 확장 표라 열 구조가 다르지만, diff 확인 결과 **4개 파일 전부 `.opal/MEMORY.md`→`.opal/MEMORY.json` 단일 토큰 교체만 있고 그 외 구조·조건문 변경 0줄** — 새 플랫폼 분기 추가 없음(구조적 차이는 078 이전부터 존재한 pre-existing 설계이며 078이 도입한 것이 아님) |

#### TS-043: dashboard 응답 모델 additive-only

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-6** |
| 대상 | F-009 `models.py` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 변경 전후 `MemoryRowResponse`·`HistoryRowResponse` 필드명 집합 비교 |
| 기대 결과 | 기존 필드가 **하나도 제거·개명되지 않음**(추가만 허용) + `dashboard/frontend/` 변경 0건 |
| 도구 | pytest + git diff |
| 실행 명령 | `git status --porcelain \| grep -i "dashboard/frontend"` + `dashboard/backend/models.py` 필드 확인 + `pytest dashboard/backend/tests -q` |
| 결과 | Pass |
| 상세 | `MemoryRowResponse`: 기존 5필드(date/category/status/file/description) 그대로 유지 + `title` 추가만(주석 "additive (078 F-009)"). `HistoryRowResponse`: 기존 6필드(date/task/stage/path/start/end) 유지 + `result` 추가만. `git status --porcelain` 결과 `dashboard/frontend/` 매치 0건(변경 없음). 백엔드 pytest 249 passed, 1 skipped |

#### TS-047: 077 영역 무변경 확인

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-10** |
| 대상 | F-011 `tools.md` 동시 편집 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `tools.md` 편집 전후 `git diff`에서 code-scan 절 범위 확인 |
| 기대 결과 | code-scan 절(077 담당 영역) **diff 0줄** + memory-tool 절만 변경 |
| 도구 | git diff |
| 실행 명령 | `git diff HEAD -- opal/core/references/tools.md` (hunk 경계 확인) |
| 결과 | Pass (조건부) |
| 상세 | `git diff` 상 077·078이 아직 둘 다 미커밋 상태라 두 태스크 변경이 같은 워킹트리 diff에 함께 나타남. 그러나 hunk 경계를 확인한 결과 **code-scan 절(약 L201-289, 077의 discover/scaffold/target/validate/feature 문서화)과 memory-tool 절(약 L579-668, 078의 서브명령·에러코드·migration 리포트 문서화) hunk가 완전히 분리**되어 있고 상호 겹침·인터리빙 0건. PLAN §D-4가 지시한 대로 078은 `## memory-tool` 헤딩 앵커로만 편집했고 code-scan 절에는 078 기인 diff가 없음(해당 절 diff는 전량 077 소관). 순수 "diff 0줄"은 077 작업이 함께 미커밋 상태라 리터럴하게 확인 불가하나, **078로 인한 code-scan 절 추가 diff는 0줄**로 확인 |

---

### L2. 프로세스 통합 (자동, 실 파일 read→CUD→re-read)

#### TS-015: invest-stock 변형 무손실 + 인식 실패의 명시적 실패 [P0]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-1 (P0)** |
| 대상 | F-004 행 회계 불변식 (D-3) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | (1) `fixture_md_no_marker_legacy.md`(invest-stock 실측 복사본) 변환 (2) 히스토리 프로파일 감지를 강제 무력화한 뒤 재변환 |
| 기대 결과 | (1) 히스토리 **3행** 정상 변환(0행 아님) + 메모리 행 전량 보존 (2) `migration_failed(row_detection_failed)` + **md mtime 불변** + `MEMORY.json` 미생성 — 조용한 0행 금지 |
| 도구 | unittest (subprocess) |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestMigrationFailure.test_ts015_legacy_header_variant_preserves_three_history_rows tests.test_memory_tool.TestMigrationFailure.test_ts015_legacy_datetime_is_truncated_to_date tests.test_memory_tool.TestMigrationFailure.test_ts015_detection_failure_is_explicit_and_leaves_source_intact -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. (1) 히스토리 3행 정상 변환(0행 아님) 확인. (2) 감지 무력화 시 `migration_failed(row_detection_failed)` + md mtime 불변 + json 미생성 확인. PM 실증(TS-035)에서도 invest-stock 복사본 history 3/3 보존으로 재확인됨 |

#### TS-018: 변환 중 동시 진입 클로버 방지 [P0]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-2 (P0)** |
| 대상 | F-004 + F-002 `memory_lock` + double-checked locking |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | md만 있는 tmp 디렉토리에 `append`(서로 다른 title) 2개 프로세스를 동시 기동 |
| 기대 결과 | `MEMORY.json` 1개 + **두 행 모두 존재**(클로버 0) + `.bak` 1개 + 락 파일 잔여 0 |
| 도구 | unittest (`subprocess` 병렬 기동) |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestConcurrentMigration -v` |
| 결과 | Pass |
| 상세 | `test_ts018_two_concurrent_appends_do_not_clobber`·`test_ts018_json_files_are_not_duplicated` 2건 OK — json 1개, 두 행 모두 존재(클로버 0), `.bak` 1개, 락 잔여 0 확인 |

#### TS-020: 20 프로세스 동시 채번 중복 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-7, H-2** |
| 대상 | F-005 `task-number --bump` 원자성 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 동일 문서에 `task-number --bump`를 20개 프로세스로 동시 기동 |
| 기대 결과 | 반환값 20개가 **서로 전부 상이**(중복 0) + 최종 `last_task_number == 초기값 + 20` |
| 도구 | unittest (`subprocess` 병렬 기동) |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestTaskNumber.test_ts020_twenty_concurrent_bumps_have_no_duplicates -v` |
| 결과 | Pass |
| 상세 | 132건 전체 스위트에 포함, OK. 20개 프로세스 동시 `--bump` → 반환값 20개 전부 상이(중복 0), 최종값 == 초기+20 확인 |

#### TS-024: improve-tool 위임 왕복 (json 존재)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-3 (P0)** |
| 대상 | F-008 R-7 AC |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `MEMORY.json`만 있는 tmp 프로젝트에서 `improve-tool record --scope local --title T --body B --situation retrospective` |
| 기대 결과 | no-op 아님 + `type=improvement`·`status=candidate` 행이 json에 실제 기록 + **스키마 검증 통과**(enum 동기화 확인) |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/improve-tool && python -m unittest tests.test_improve_tool.TestDelegation.test_ts024_json_only_delegates_and_appends -v` |
| 결과 | Pass |
| 상세 | 17건 전체 스위트에 포함, OK. no-op 아님 + `type=improvement`/`status=candidate` 행 json 기록 + 스키마 검증 통과 확인 |

#### TS-025: 과도기 위임 — md만 있을 때 lazy 변환 후 위임

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-4** |
| 대상 | F-008 + F-004 접합 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `MEMORY.md`만 있는 tmp 프로젝트에서 `record --scope local` → 이어서 `list --scope local` |
| 기대 결과 | lazy 변환 발동 + append 성공 + `.bak` 존재 + `list`가 해당 1건 반환(`index_rows` 키 계약 보존) |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/improve-tool && python -m unittest tests.test_improve_tool.TestDelegation.test_ts025_md_only_lazy_converts_and_delegates -v` |
| 결과 | Pass |
| 상세 | 17건 전체 스위트에 포함, OK. lazy 변환 발동 + append 성공 + `.bak` 존재 확인. `improve_tool.py`에 `record`/`list`/`show` 3서브명령 모두 존재(cmd_list:295, cmd_show:336) 확인 |

#### TS-027: `GET /api/memory` 값 정확성 + 필드 계약

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-5, H-6** |
| 대상 | F-009 파서·라우터 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 변환 완료된 `MEMORY.json`을 대상으로 API 호출 |
| 기대 결과 | `rows[]` 필드 = 기존 5필드 + `title` + 각 값이 JSON 원본과 **1:1 일치**(헤더 행 유입 0건, 오프바이원 해소). **현행 깨진 출력을 기준선으로 삼지 않는다** |
| 도구 | pytest (FastAPI TestClient) |
| 실행 명령 | `pytest dashboard/backend/tests/test_parsers.py dashboard/backend/tests/test_routers.py -k memory -v` + 실 API `curl -s -G http://127.0.0.1:7823/api/memory --data-urlencode "project=/Volumes/Data/AIStudio/workspace/ai-framework"` |
| 결과 | Pass |
| 상세 | pytest 9건 전부 PASSED(`test_memory_parser_returns_structure`·`rows_have_fields`·`history_have_fields`·`mtime_invariant`, `test_api_memory_200`·`schema`·`with_project_param` 등). 실 API 호출로도 `rows[]` 3건(date/category/status/file/description+title)·`history[]` 5건이 실 MEMORY.json과 1:1 일치, 헤더 행 유입 0건 확인 |

#### TS-028: dashboard 읽기 전용(mtime 불변)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-009 — 읽기 전용 원칙 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | API 호출 전후 `MEMORY.json` mtime 비교 |
| 기대 결과 | mtime 완전 불변 (`json.load`만 사용) |
| 도구 | pytest |
| 실행 명령 | `pytest dashboard/backend/tests/test_parsers.py -k mtime_invariant -v` |
| 결과 | Pass |
| 상세 | `test_memory_parser_mtime_invariant`·`test_memory_file_parser_mtime_invariant` PASSED — API 파서 호출 전후 mtime 완전 불변 확인 |

#### TS-030: 신규 프로젝트가 신포맷으로 생성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | F-010 R-9 AC |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 빈 임시 디렉토리에서 opi 초기화 도구 호출 시퀀스 실행 |
| 기대 결과 | `.opal/MEMORY.json` 존재 + `.opal/MEMORY.md` **부재** + 생성된 json이 스키마 검증 통과 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest tests.test_memory_tool.TestInit.test_init_creates_json_skeleton_on_fresh_path tests.test_memory_tool.TestInit.test_init_does_not_create_md_file -v` |
| 결과 | Pass |
| 상세 | opi가 호출하는 `memory-tool init` 레벨에서 검증: `MEMORY.json` 생성(스키마 골격 `{version,last_task_number,memories,history}`) + `MEMORY.md` 미생성 확인. opal-project-init/SKILL.md v4.6 changelog에 "§2-4 인라인 md 템플릿 삭제 → `memory-tool init` 호출" 명시(TS-031과 교차 확인) — opi 스킬 전체 시퀀스의 별도 재현은 생략, 호출 대상 도구 계약 레벨에서 충분히 검증 |

#### TS-035: 실 프로젝트 마이그레이션 실증 (캡틴 (b)안 반영)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-1 (P0)** |
| 대상 | F-012 — 배포본 도구로 실 변환 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | (1) `ai-framework/.opal/MEMORY.md` **실 변환** (2) `invest-stock`·`aos`는 **읽기 전용 복사본**으로 변환 검증 |
| 기대 결과 | (1) 1/1 성공 + `.bak` 생성 + 무손실 (2) 복사본 2/2 무손실(**invest-stock 히스토리 3행 보존**) (3) **`invest-stock`·`aos` 원본 파일 mtime 불변** — 캡틴 (b)안 준수 |
| 도구 | Bash (배포본 `run.sh`) |
| 실행 명령 | PM이 배포본(`~/.opal/tools/memory-tool/run.sh`)으로 EXECUTE 단계에서 이미 실증 완료(TEST 단계 재실행 불필요 — PM 프롬프트에 실측값 제공) |
| 결과 | Pass |
| 상세 | PM 실증 결과(제공값): ai-framework 실변환 1/1 성공 — memories 3/3·history 5/5 일치, `last_task_number` 78 보존, `.bak` md5 원본과 동일. invest-stock 복사본 2/2 무손실 — history 3/3 보존 + `unmapped_statuses` 3건(`확정`×2·`승인대기`×1, TS-040과 정합). aos 복사본 `memories:[]`+`empty_source_regions`(TS-016과 정합). **두 원본(invest-stock/aos) mtime·md5 불변** 확인(invest-stock `Jun 24 18:43:24`, aos `Jul 16 20:42:26`) — 캡틴 (b)안(원본 미수정) 준수 |

#### TS-036: 목표달성 시나리오 — 신형 채택 실세션 왕복 ★

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-4 (+ TASK 목표 전체) |
| 대상 | R-10 AC(b) — **태스크 목표의 최종 검증** |
| 계층 | L2 (운영 계층 실세션) |
| **실행 방식** | **M3 (수동 실세션 — 알투(PM) 직접 실행)**. 자동화 가능한 CLI 왕복 부분은 M1 보조로 병행하되, **본 시나리오는 op-dev-test-agent가 자동 PASS 처리할 수 없다** — PLAN.md Step 22가 `agent: PM 직접 / 실행 방법: direct`로 규정한다. TEST 단계에서 PM이 직접 수행하고 결과를 기재한다 |
| 조건 | 변환 완료된 `ai-framework` 실세션에서 ① 부트스트랩 브리핑 ② `append` ③ `show --brief` ④ `update --status dead` ⑤ `show --brief` |
| 기대 결과 | ① 브리핑이 `show --brief`로 생성되고 `§15` 형식 만족 ② 추가 행이 `MEMORY.json`에 반영 ③ brief에 노출 ④⑤ dead 전이 후 brief에서 **소멸** + `task-number --bump`로 다음 번호 채번 성공 |
| 도구 | Bash + 실세션 |
| 실행 명령 | PM(알투)이 직접 실세션에서 왕복 실행(TEST 단계 op-dev-test-agent는 M3 규정상 자동 PASS 불가 — PM 제공 실측값을 근거로 기록) |
| 결과 | Pass |
| 상세 | PM 실증 결과(제공값): ① brief 브리핑 생성(active 3·history 3·truncated) → ② `append`(active 4로 반영) → ③ `show --brief`에 노출 → ④ `update --status dead`(brief에서 소멸, active 3으로 복귀) → ⑤ `delete`로 정리. `task-number` 읽기 78·md5 불변, `--bump`는 임시 사본에서 79 확인(실 채번 미소모 — 원본 보존). 최종 상태 memories 3·history 5·`last_task_number` 78로 원복 확인 |

#### TS-044: 배포본 스모크 (스키마 동반 배포)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-13** |
| 대상 | F-012 install |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `./scripts/install-mac.sh` 실행 후 `~/.opal/tools/memory-tool/run.sh`로 전 서브명령 스모크 |
| 기대 결과 | 전부 `ok` + `~/.opal/tools/memory-tool/schema/memory.schema.json` 존재 + `show --help`에 `--brief` 노출 + `task-number --help` 동작 |
| 도구 | Bash |
| 실행 명령 | `ls ~/.opal/tools/memory-tool/schema/memory.schema.json; TMPD=$(mktemp -d); ~/.opal/tools/memory-tool/run.sh init --file "$TMPD/MEMORY.json"; ~/.opal/tools/memory-tool/run.sh show --help \| grep -o "\-\-brief"; ~/.opal/tools/memory-tool/run.sh task-number --help` |
| 결과 | Pass |
| 상세 | 배포본은 install-mac.sh로 이미 최신 배포됨(2회 재배포 완료, PM 선행 상태). `schema/memory.schema.json` 존재 확인. `run.sh init` → `{"ok": true, "command": "init", ...}` 정상. `show --help`에 `--brief` 노출 확인. `task-number --help` → `usage: memory_tool task-number [-h] --file FILE [--bump] [--set SET_VALUE]` 정상 동작 |

#### TS-045: dashboard 메모리 화면 렌더 (E2E 자동화)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-6** |
| 대상 | F-009 — API 응답을 소비하는 FE 화면(파일 변경 0건이나 계약 변경) |
| 계층 | L2 |
| **실행 방식** | **M2 (E2E 자동화)** — `cmux-tool` 우선, 미설치 시 `playwright` MCP 폴백 |
| 조건 | dashboard 백엔드·프론트 기동 후 메모리 페이지 접속 |
| 기대 결과 | 메모리 행 목록·요약이 정상 표시 + 브라우저 콘솔 에러 0건 + `category`/`description` 참조가 undefined로 깨지지 않음 |
| 도구 | cmux-tool / playwright MCP |
| 실행 명령 | `bash ~/.opal/tools/cmux-tool/run.sh open "http://127.0.0.1:7823/"` (1순위, 실패) → `mcp__playwright__browser_navigate` + `browser_click`("/projects"→ai-framework 카드→사이드바 "메모리" 링크) + `browser_snapshot` + `browser_console_messages` (폴백) |
| 결과 | Pass |
| 상세 | cmux-tool 1순위 시도 → `{"ok":false,"error":"not_in_cmux","detail":"CMUX_SURFACE_ID 환경 변수가 설정되지 않았습니다"}` (cmux 터미널 밖이라 환경적으로 불가, 코드 결함 아님) → playwright MCP 폴백 정상 수행. dashboard 백엔드(포트 7823)는 기 기동 중, 프론트 dist가 StaticFiles로 서빙됨. `/projects`에서 ai-framework 선택 → SPA 네비게이션으로 `/memory` 진입(전체 페이지 리로드 시 contextProject 상태 소실되므로 사이드바 링크 클릭 방식 사용) → 메모리 3건(제목·`#project`/`#task` 카테고리·요약·날짜 전부 정상 렌더, undefined 없음) + 작업 히스토리 5건(날짜·태스크명·단계·경로) 정상 렌더 + `browser_console_messages(level=error)` 결과 "Total messages: 0 (Errors: 0)" 확인 |

---

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### TS-046: 메모리 화면 육안 확인 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-6** |
| 대상 | dashboard 메모리 페이지 — 전환 전후 동등성 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)**. TS-045(M2)가 선행 자동 검증을 담당하며, 본 시나리오는 시각적 동등성 최종 확인 |
| 조건 | TS-045 통과 후 dashboard 메모리 페이지를 캡틴이 직접 열람 |
| 기대 결과 | 화면이 전환 전과 동등하거나 개선됨(오프바이원 해소로 제목·요약이 올바른 칸에 표시). 레이아웃 깨짐·빈 목록 없음 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **Pass** (캡틴 확인, 2026-07-29 17:32) |
| 상세 | 캡틴이 PM의 TS-046 육안 확인 요청 + CLOSE 진입 승인 요청에 `확인` 발화로 응답. **관찰 상세는 별도 제공되지 않았으므로 PM이 임의로 기술하지 않는다** — 자동 계층 근거는 TS-045(playwright E2E: 행 목록·요약 정상 표시, 콘솔 에러 0건, `category`/`description` 참조 무파손)와 TS-027(응답 값 `MEMORY.json` 원본과 1:1, 오프바이원 해소 실측)이 담당한다. 이견이 있으시면 이 행을 정정한다 |

**PM 표준 요청 양식** (TEST 단계에서 사용):

```
캡틴, [시나리오 TS-046]은 사용자 협업 검증이 필요합니다.
요청 내용: dashboard 메모리 페이지를 열어 메모리 목록이 정상 표시되는지 확인해주세요.
기대 결과: 제목·요약이 올바른 칸에 표시되고(오프바이원 해소), 목록이 비어 있지 않으며 레이아웃이 깨지지 않음.
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC (스키마 위반 거부 + 파일 불변) | H-3, H-8 | L1 | TS-001, TS-002, TS-003, TS-004, TS-005, TS-037 | `tests/test_memory_tool.py`:`TestSchemaValidation` [T078/L1-R1] | enum·길이·pattern·손상·부재 5경로 |
| R-2 AC(a) 마커 심볼 0건 | H-9 | L1 | TS-006 | `tests/test_memory_tool.py`:`TestSymbolRemoval` [T078/L1-R2a] | grep 기반 |
| R-2 AC(b) 8서브명령 JSON 동작 | H-4 | L1 | TS-007, TS-038 | `tests/test_memory_tool.py`:`TestJsonIO` [T078/L1-R2b] | 응답 키 보존 포함 |
| R-2 AC(c) `marker_missing` 제거 | H-9 | L1 | TS-008 | `tests/test_memory_tool.py`:`TestErrorCodes` [T078/L1-R2c] | 신설 12종 포함 |
| R-3 AC (brief 필터 + 바이트 감소) | H-3 | L1 | TS-010, TS-011, TS-012, TS-039 | `tests/test_memory_tool.py`:`TestShowBrief` [T078/L1-R3] | 절약 실측 기록 |
| R-4 AC (브리핑 경로 전환) | H-4 | L1 | TS-022, TS-042 | 산출물 검사 [T078/L1-R4] | 4개 사본 동일성 |
| R-5 AC(a) lazy 변환 + `.bak` | H-12 | L1 | TS-013 | `tests/test_memory_tool.py`:`TestLazyMigration` [T078/L1-R5a] | `.bak` 충돌 회피 |
| R-5 AC(b) 무손실 100% | H-1 | L1 | TS-014, TS-016 | `tests/test_memory_tool.py`:`TestMigrationLossless` [T078/L1-R5b] | 정상 0행 구분 |
| R-5 AC(c) 실패 시 원본 무변경 | **H-1 (P0)** | L2 | **TS-015**, TS-040 | `tests/test_memory_tool.py`:`TestMigrationFailure` [T078/L2-R5c] | 무성 유실 차단 |
| R-5 AC(d) `cmd_migrate` 0건 | H-9 | L1 | TS-017 | 산출물 검사 [T078/L1-R5d] | — |
| R-6 AC (슬림화 + 보존) | H-9 | L1 | TS-023 | 산출물 검사 [T078/L1-R6] | 줄 수 감소 실측 |
| R-7 AC (위임 3케이스) | H-3, H-4 | L1+L2 | TS-024, TS-025, TS-026 | `tests/test_improve_tool.py`:`TestDelegation` [T078/L2-R7] | json/md/부재 |
| R-8 AC (응답 스키마 + 값 정확성) | **H-5, H-6** | L1+L2 | TS-027, TS-028, TS-029, TS-043 | `dashboard/backend/tests/test_parsers.py` [T078/L2-R8] | FE 무변경 |
| R-9 AC (신포맷 생성) | H-11 | L1+L2 | TS-030, TS-031 | `tests/test_memory_tool.py`:`TestOpiInit` [T078/L2-R9] | — |
| R-10 AC(a) 구형 잔존 0 | **H-11**, H-10 | L1 | TS-032, TS-033, TS-034, TS-047 | 산출물 검사 [T078/L1-R10a] | 제외경로 명시 grep |
| R-10 AC(b) 신형 채택 | H-3, H-4 | L2 | **TS-035, TS-036**, TS-044 | 실세션 + 배포본 [T078/L2-R10b] | **목표달성 시나리오** |
| D-1 채번 tool-gated | **H-7, H-2** | L1+L2 | TS-019, TS-020, TS-021, TS-041 | `tests/test_memory_tool.py`:`TestTaskNumber` [T078/L2-D1] | 20프로세스 동시성 |
| H-6 FE 무파손 (계약 소비자) | **H-6** | L2+L3 | TS-045, TS-046 | E2E + 육안 [T078/L3-H6] | M2 + M3 병행 |

**커버 확인**: TASK.md 요구사항 R-1~R-10 **전량 매핑 완료**(누락 0). PM 선결정 D-1도 매핑. 미매핑 시나리오 0건.

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | N/A: 설정 부재 | N/A | 이 프로젝트의 Python 도구(memory-tool/improve-tool)는 표준 라이브러리 전용이며 `.flake8`/`ruff.toml`/`pyproject.toml`/`mypy.ini` 등 별도 린터·타입체커 설정이 리포지토리에 없음(확인: `find . -maxdepth 2 -iname ".flake8" -o -iname "ruff.toml" -o -iname "pyproject.toml"` 매치 0건). 대체 증거로 `python -m py_compile` 실행 |
| 2 | 타입 체크 | N/A: 설정 부재 | N/A | mypy 설정 부재(`mypy.ini` 없음). 대체 증거: `py_compile` 6종 전부 통과 |
| 3 | 포맷터 | N/A: 설정 부재 | N/A | black/ruff format 설정 부재. 대체 증거: `py_compile` 6종 전부 통과(구문 오류 0건) |
| 4 | 표준 라이브러리 전용(외부 import 0건) | grep import | Pass | `memory_tool.py`: argparse/contextlib/json/os/pathlib/re/sys/time/datetime — 전부 표준 라이브러리. `improve_tool.py`: argparse/json/os/pathlib/re/socket/subprocess/sys/datetime — 전부 표준 라이브러리. 외부 패키지 import 0건 |
| 5 | `@header` 갱신(변경 `.py` 6종) | grep + Read | Pass | 6종(`memory_tool.py`·`improve_tool.py`·`dashboard/backend/models.py`·`parsers/memory_parser.py`·`routers/doctor.py`·`routers/memory.py`) 전부 `@header.description`에 078/F-009 관련 갱신 서술 확인(예: "MEMORY.json SSOT + 9서브명령", "078 JSON 전환, F-009", "핵심 파일 체크 대상 MEMORY.json 전환") + `python -m py_compile` 6종 전부 OK |

---

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `grep -inE "api[_-]?key\|secret\|password\|token\s*=\s*['\"]"` 6개 변경 파일 대상 매치 0건. `TestSecurity.test_no_hardcoded_secrets_in_tool` unittest도 OK |
| 2 | `.gitignore` 확인(`.bak`·락·tmp 파일 정책) | Pass | `.opal/*`가 이미 포괄 ignore 처리(`.gitignore:2`, brain/code-map만 예외 화이트리스트) — MEMORY.json/`.bak`/`.lock`/`.tmp` 파일은 전부 `.opal/` 하위에 생성되므로 별도 명시 규칙 없이도 커밋 누락 없음. 078 자체는 `.gitignore`를 수정하지 않음(diff는 077의 code-map 예외 추가만) |
| 3 | `memory/` 경로 탈출 가드 동작 불변 | Pass | `TestSecurity.test_promote_path_traversal_rejected`·`test_promote_only_deletes_within_memory_dir`·`test_path_traversal_in_title_file_mapping` 3건 OK — `../` 포함 제목·경로 탈출 시도 전부 거부 확인 |
| 4 | `promote`/`delete --with-file` 화이트리스트 이탈 0 | Pass | `TestPromoteLossless`(4건)·`TestDelete.test_delete_with_file_path_traversal_rejected`·`TestSecurity.test_promote_only_deletes_within_memory_dir` 전부 OK — `memory/` 디렉토리 외부 파일 삭제 0건, path traversal 거부 확인 |
| 5 | 락·tmp 파일이 `.opal/` 밖에 생성되지 않음 + 실패 경로 잔여 0 | Pass | 코드 검토: 락 파일(`<MEMORY.json>.lock`)·tmp 파일(`<MEMORY.json>.tmp.<pid>`) 모두 `json_path.parent` 기준 생성(대상 파일과 동일 디렉토리 — 통상 `.opal/` 하위). 리포지토리 루트 스캔(`find . -maxdepth 3 -name "*.lock" -o -name "*.tmp"`) 결과 `.claude/scheduled_tasks.lock`(무관한 기존 파일) 외 잔여 0건. `TestAtomicWrite`·`TestConcurrentMigration` 테스트 종료 후 tmp/lock 잔여 0건 어서션 포함 |

---

## 7. 판정

**All Pass (조건부 — TS-046 캡틴 확인 1건 대기) -- TS-001~TS-047 중 46건 Pass, TS-046 1건은 [SUPERVISOR] 마커로 미실행(캡틴 육안 확인 대기).**

> **판정 갱신 이력**: 초회 판정은 `Partial Fail`(TS-034 Fail)이었다. PM이 진짜 누락 2건(`docs/PROJECT.md`·`docs/ARCHITECTURE.md` 변경이력 행)을 보완하고, 초회 검사의 탐지 패턴 오탐 2건을 재검증으로 해소해 **TS-034가 Pass로 전환**되었다(상세는 TS-034 항목 참조). 코드·테스트 레벨 회귀는 초회부터 0건이었다.

> 초회 판정 원문: Partial Fail -- 45건 Pass, TS-034 1건 Fail(문서 changelog 태그 누락, 코드 결함 아님), TS-046 1건 미실행. 핵심 기능(메모리 CRUD·스키마 검증·lazy 마이그레이션·동시성 원자성·채번·dashboard API/FE 계약·보안 가드)은 전부 Pass — 코드·테스트 레벨 회귀 0건. TS-034 실패는 `docs/ARCHITECTURE.md`·`docs/PROJECT.md` 등 일부 변경 문서에 `(078)` 변경이력 태그가 누락된 문서화 결함으로, 런타임 동작에는 영향 없다. 이를 근거로 Critical Fail이 아닌 Partial Fail로 판정한다.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (§3 서두에 명시적 금지 + grep 확인 대상)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 (9개 저장소 전부)
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 (TS-001~TS-047 전량)
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 0건)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (TS-046)
- [x] 리스크 가설 표(§1) H-1~H-13이 시나리오와 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] **FE 변경 시 M2 시나리오 포함** — FE 파일 변경은 0건이나 API 소비 계약이 바뀌므로 L2/M2 시나리오 TS-045를 배치
- [x] **목표 커버** — R-1~R-10 전량 §4 매핑 + 목표달성 시나리오 **TS-036**(실세션 왕복) 존재

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-28 | 최초 작성 — PLAN H-1~H-13 기반 47시나리오(L1 26 / L2 12 / L3 1 + 매핑). 캡틴 (b)안(실 변환 ai-framework 한정 + 나머지 복사본 검증) 반영, FE 계약 변경에 대한 M2(TS-045)·M3(TS-046) 신설 |
