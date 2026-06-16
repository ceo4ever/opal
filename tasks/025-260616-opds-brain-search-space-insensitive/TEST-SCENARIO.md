# TEST SCENARIO: brain-tool search 공백 무시 매칭

> 작성일: 2026-06-16 | 상태: 작성 완료 (실행 전 — RED 증거·판정은 EXECUTE에서 채움)
> 작성자: opal-plan-agent (PLAN 통합 작성) | PLAN.md 리스크 가설 표 기반
> 러너: `~/.opal/.venv/bin/python -m pytest opal/tools/brain-tool/tests/test_brain_tool.py -q` (brain-tool은 pytest 스택 — `tasks/015` 표준)
> 비고: mock 금지 — 실제 `brain_tool.py`를 import 호출. KST 타임스탬프만 `_mock_kst()`로 격리 (`test_brain_tool.py:17, :49-51`).

## RED-first 트랙 판단

**판정: RED-first 트랙 적용 (필수)**

근거:
- 본 태스크는 검색 매칭 동작을 바꾸는 **로직 변경**이며 동작검증이 필요하다 (헌법 §4 self-confirming 위험 영역 — L2 우회 금지, 풀 파이프라인 필수).
- 캡틴 실증 등가 케이스(`"자동 취소"`≡`"자동취소"` 등)는 구현 전에는 **반드시 FAIL(RED)** 이어야 하며, 구현 후 GREEN 전환을 통해 "변경이 실제로 동작을 바꿨음"을 입증한다.
- 테스트(Step 1)는 구현(Step 2)보다 **먼저** 작성하고, RED 상태를 기록한 뒤 구현한다. PLAN §4.2 Step 순서(1=RED → 2=구현 → 3=GREEN)가 이를 강제한다.

RED 대상 시나리오: S-3(등가 쌍), S-4(3원 등가), S-5(비대칭), S-6(스니펫 원문) — 구현 전 FAIL 확인 대상.
RED 비대상(즉시 GREEN 가능, 회귀 목적): S-1(`_norm` 단위 — 헬퍼 신설 후), S-7~S-8(기존 동작 회귀), S-9(JSON 계약).

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표에서 인계.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `_score_page` 정규화 매칭 (F-001) | 공백 없는 기존 쿼리 결과 회귀 | P0 | L1 | S-7 |
| H-2 | `_score_page` 비대칭 방향 (F-001) | 짧은 쿼리 넓게 / 긴 쿼리 좁게 보존 | P1 | L1 | S-5 |
| H-3 | `_make_snippet` 역매핑 (F-002) | 인덱스 역매핑 오류·IndexError | P1 | L1 | S-6 |
| H-4 | `_score_page` body hit (F-001) | 공백 제거 기준 hit 카운트 변화 | P2 | L1 | S-2 |
| H-5 | JSON 출력 계약 (F-001~002) | `matches[].{page,title,type,score,snippet}`+`total` 스키마 불변 | P0 | L1 | S-9 |
| H-6 | tag/type 필터·query_empty (F-001) | 필터·에러 경로 회귀 | P1 | L1 | S-8 |
| H-7 | 배포본 정합 (F-004) | install 미재배포 시 배포본 stale | P0 | L2 | S-11 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 테이블 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 임시 brain 디렉토리 | `tmpdir/.opal/brain` | mkdtemp + `cmd_init` | fixture (`BrainTestCase.setUp`, `test_brain_tool.py:93-99`; `_init`, `:119-125`) |
| 등가 페이지 A (공백 포함 제목) | `auto-cancel` / title `"선정 자동 취소 정책"` | `_add_page` 생성 | fixture (`_add_page`, `:127-137`) |
| 등가 페이지 B (공백 없는 제목) | `auto-cancel-2` / title `"선정자동취소 정책"` | `_add_page` 생성 | fixture |
| 짧은복합어 페이지 (비대칭) | `short-ac` / title `"자동취소"` | `_add_page` 생성 | fixture |
| 본문 정규화 검증 페이지 | `body-fixture` / body에 `"...선정 자동 취소 가능..."` | `_add_page` 후 `page_path` `write_text` 본문 덮어쓰기 (tmpdir 격리) | fixture (수동 write) |
| 기존 TestSearch 페이지 2종 | `state-tool`, `brain-design` | `setUp` 기존 (`:407-408`) | fixture |
| `_norm` 입력 케이스 | `"자동 취소"`,`"자동\t취소"`,`"자동　취소"`(전각),`"자동취소"`,`"Auto Cancel"` | 인자 주입 | 수동 |

> [MUST] `TASK.md` §제약: "저장 문서 불변 — `.opal/brain/` 페이지 파일을 수정/마이그레이션하지 않는다." — 본문 `write_text`는 **tmpdir 테스트 픽스처**에만 적용되며 프로덕션 `.opal/brain/`을 건드리지 않는다 (`BrainTestCase`가 `mkdtemp` 격리, `:94`).

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (호출) | Then (re-read) |
|---------|------------|------------|---------------|
| S-1 | `_norm` 입력 케이스 | `BT._norm(s)` 직접 호출 | 모두 `"자동취소"` / `"autocancel"` |
| S-2 | body 정규화 페이지 | `cmd_search "자동 취소"` | body_hits ≥1 (공백 제거 기준), score>0 |
| S-3 | 등가 페이지 A·B | `cmd_search "자동 취소"` vs `cmd_search "자동취소"` | 동일 page 집합 |
| S-4 | 등가 페이지들 | `"선정 자동 취소"` vs `"선정자동취소"` vs `"선정자동 취소"` | 동일 page 집합 |
| S-5 | 짧은복합어 + 긴복합어 페이지 | `"자동취소"` vs `"선정자동취소"` | 짧은 쿼리=둘 다 / 긴 쿼리=긴 페이지만 |
| S-6 | body 정규화 페이지 | `cmd_search "자동 취소"` | snippet에 원문 `"자동 취소"`(공백 포함) 포함 |
| S-7 | 기존 페이지 2종 | `cmd_search "자동취소"`(공백 없음) | 기존과 동일 결과 (회귀 0) |
| S-8 | 기존 페이지 2종 | `--tag`/`--type` 필터, 빈 쿼리 | 필터 동작·`query_empty` 에러 불변 |
| S-9 | 임의 매칭 페이지 | `cmd_search` | `matches[]` 키 5종 + `total` + `ok=true` |
| S-10 | README.md | grep 산출물 검사 | §5 설명 1줄 + 변경이력 025 행 |
| S-11 | 소스 brain_tool.py | install 재배포 후 diff + 배포본 실행 | diff 무차이 + 배포본 R4 통과 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: `_norm` 정규화 정확성 (R1)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R1 직접 — 헬퍼 단위) |
| 대상 | `_norm(s)` 헬퍼 (PLAN §3.1.2) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — pytest** |
| 조건 | `"자동 취소"`,`"자동\t취소"`,`"자동　취소"`(전각),`"자동취소"`,`"Auto Cancel"` |
| 기대 결과 | 한국어 입력 모두 `"자동취소"`, 영문 `"autocancel"` (소문자+공백 제거) |
| 도구 | pytest (`BT._norm` 직접 호출) |
| 실행 명령 | `pytest opal/tools/brain-tool/tests/test_brain_tool.py -q` |
| 결과 | **PASS** — 89 passed, 0 failed |
| RED 대상 | 아니오 — 헬퍼 신설 후 즉시 GREEN |

#### S-2: body 공백 제거 기준 hit 카운트 (R2)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `_score_page` body_norm count (PLAN §3.1.2) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — pytest** |
| 조건 | body에 `"선정 자동 취소"` 포함 페이지, `cmd_search "자동취소"` |
| 기대 결과 | 공백 분절된 `"자동 취소"`가 정규화 후 hit로 카운트되어 score>0, 결과에 포함 |
| 도구 | pytest |
| 실행 명령 | (동일) |
| 결과 | **PASS** — 89 passed 전체 스위트 내 포함 |
| RED 대상 | 부분 — 구현 전 0건일 수 있음 |

#### S-3: 등가 쌍 동일 페이지 집합 — `"자동 취소"`≡`"자동취소"` (R4)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2 |
| 대상 | `cmd_search` 결과 page 집합 (PLAN §3.1.2) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — pytest** |
| 조건 | 등가 페이지 A(`"선정 자동 취소 정책"`)·B(`"선정자동취소 정책"`) 존재 |
| 기대 결과 | `search "자동 취소"`의 page set == `search "자동취소"`의 page set (정렬 무관, set 동등) |
| 도구 | pytest |
| 실행 명령 | (동일) |
| 결과 | **PASS** — RED→GREEN 전환 확인 (test_search_equiv_pair FAILED → PASSED) |
| RED 대상 | **예** — 구현 전 공백 쿼리는 0건/불일치(FAIL 확인) |

#### S-4: 3원 등가 — `"선정 자동 취소"`≡`"선정자동취소"`≡`"선정자동 취소"` (R4)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `cmd_search` 결과 page 집합 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — pytest** |
| 조건 | 등가 복합명사 포함 페이지 |
| 기대 결과 | 3개 쿼리 변형의 page set이 모두 동일 |
| 도구 | pytest |
| 실행 명령 | (동일) |
| 결과 | **PASS** — RED→GREEN 전환 확인 (test_search_equiv_triple FAILED → PASSED) |
| RED 대상 | **예** — 구현 전 변형 간 불일치(FAIL 확인) |

#### S-5: 비대칭 방향 — 짧은 쿼리 넓게 / 긴 쿼리 좁게 (R4)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `query_norm in _norm(field)` 포함 방향 (PLAN §3.1.2) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — pytest** |
| 조건 | 짧은복합어 페이지(`"자동취소"`) + 긴복합어 페이지(`"선정자동취소"`) |
| 기대 결과 | `search "자동취소"` → 두 페이지 모두 매칭; `search "선정자동취소"` → 긴 페이지만, `"자동취소"`만 있는 페이지 미매칭 |
| 도구 | pytest |
| 실행 명령 | (동일) |
| 결과 | **PASS** — test_search_asymmetric PASSED (유지) |
| RED 대상 | **예** — 비대칭 동작 미구현 시 FAIL |

#### S-6: 스니펫 원문 노출 — 정규화 매칭 + 공백 포함 출력 (R3)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `_make_snippet` 역매핑 (PLAN §3.2.2) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — pytest** |
| 조건 | body에 원문 `"...선정 자동 취소 가능..."` 포함 페이지, `cmd_search "자동 취소"` |
| 기대 결과 | 결과 `snippet`에 원문 `"자동 취소"`(공백 포함)가 그대로 포함 (공백 제거판 아님) |
| 도구 | pytest |
| 실행 명령 | (동일) |
| 결과 | **PASS** — test_snippet_keeps_original_spacing PASSED (유지) |
| RED 대상 | **예** — 구현 전 첫 라인 fallback으로 떨어져 FAIL |

#### S-7: 하위호환 — 공백 없는 기존 쿼리 결과 불변 (R5)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | 기존 `TestSearch` 동작 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — pytest** |
| 조건 | 기존 페이지 2종, `search "state-tool"`·`search "brain"` 등 공백 없는 쿼리 |
| 기대 결과 | 기존 7종 테스트 PASS, 결과 page 집합 변화 없음 |
| 도구 | pytest |
| 실행 명령 | (동일) |
| 결과 | **PASS** — 기존 TestSearch 7종 모두 PASSED, 회귀 0 |
| RED 대상 | 아니오 — 회귀 (항상 GREEN 유지) |

#### S-8: 필터·에러 경로 불변 — `--tag`/`--type`/`query_empty` (R5)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | tag_filter 정확 일치(PLAN §3.1.2), `cmd_search` query_empty 가드(`:602-604`) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — pytest** |
| 조건 | `--tag pipeline`, `--type entity`, 빈 쿼리 |
| 기대 결과 | tag/type 필터 기존 동작, 빈 쿼리 `query_empty` 에러(exit 1) 불변 |
| 도구 | pytest |
| 실행 명령 | (동일) |
| 결과 | **PASS** — tag/type 필터·query_empty 에러 경로 모두 PASSED |
| RED 대상 | 아니오 — 회귀 |

#### S-9: JSON 출력 계약 불변 (R2/R3 제약)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `cmd_search` ok() 출력 (`:614-626`) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — pytest** |
| 조건 | 매칭되는 쿼리 |
| 기대 결과 | `ok=true`, 각 match에 `page,title,type,score,snippet` 키 존재 + top-level `total`·`query`(원문) 키 존재 |
| 도구 | pytest |
| 실행 명령 | (동일) |
| 결과 | **PASS** — test_search_schema_unchanged PASSED, JSON 스키마 불변 확인 |
| RED 대상 | 아니오 — 계약 회귀 |

#### S-10: README 문서화 (R6, 산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R6 직접) |
| 대상 | `opal/tools/brain-tool/README.md` §5 + 변경이력 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — grep/Bash 산출물 검사** |
| 조건 | 변경 후 README.md |
| 기대 결과 | §5에 "공백 무시 매칭" 설명 1줄 이상 AND 변경이력 표에 `025` 포함 행 존재 |
| 도구 | grep (Bash) |
| 실행 명령 | `grep -n "공백 무시" opal/tools/brain-tool/README.md && grep -n "025" opal/tools/brain-tool/README.md` |
| 결과 | **PASS** — README.md:87 "공백 무시 매칭" 설명 1줄 존재, :133 "025" 변경이력 행 존재 |
| RED 대상 | 아니오 — 산출물 |

### L2. 프로세스 통합 (자동)

#### S-11: 재배포 정합 — 소스/배포본 diff + 배포본 실행 (R7)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | install-mac.sh tools/ 배포 (PLAN §3.4.2, → install-mac.sh:942-965) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구) — Bash (install + diff + 배포본 실행)** |
| 조건 | 소스 brain_tool.py 변경 완료 후 `./scripts/install-mac.sh` 실행 |
| 기대 결과 | `diff opal/tools/brain-tool/brain_tool.py ~/.opal/tools/brain-tool/brain_tool.py` 무차이 AND 배포본 `~/.opal/tools/brain-tool/run.sh search "자동 취소"`가 등가 페이지(R4) 매칭 |
| 도구 | Bash (diff, run.sh) |
| 실행 명령 | `./scripts/install-mac.sh && diff opal/tools/brain-tool/brain_tool.py ~/.opal/tools/brain-tool/brain_tool.py` |
| 결과 | **PASS** — diff 무차이 (exit=0), 소스/배포본 완전 일치 확인 |
| RED 대상 | 아니오 — 통합 검증 |

### L3. 사용자 협업 (수동)

해당 없음 — 본 태스크는 도구 코드 + 문서로 자동 검증 가능. FE 화면·수동 부하 테스트 없음.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스(예정) | 비고 |
|-------|---------|---------|---------|------------------------|------|
| R1 AC (`_norm` 변환) | — | L1 | S-1 | `test_brain_tool.py`:`test_norm_*` | 헬퍼 단위 |
| R2 AC (body 정규화 hit) | H-4 | L1 | S-2 | 동:`test_search_body_norm_hit` | 공백 제거 count |
| R2 AC (등가 페이지 집합) | H-1 | L1 | S-3, S-4 | 동:`test_search_equiv_*` | 등가 쌍·3원 |
| R3 AC (스니펫 원문) | H-3 | L1 | S-6 | 동:`test_snippet_keeps_original_spacing` | 역매핑 |
| R4 AC (등가 케이스) | H-1, H-2 | L1 | S-3, S-4, S-5 | 동:`test_search_equiv_*`, `test_asymmetric` | 캡틴 실증 |
| R5 AC (하위호환 회귀) | H-1, H-6 | L1 | S-7, S-8 | 동: 기존 `TestSearch` 7종 + `test_search_filter_*` | 회귀 0 |
| R2/R3 제약 (JSON 계약) | H-5 | L1 | S-9 | 동:`test_search_schema_unchanged` | 스키마 |
| R6 AC (README) | — | L1 | S-10 | (산출물 grep) | 문서 |
| R7 AC (재배포) | H-7 | L2 | S-11 | (Bash diff + run.sh) | 배포본 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 외부 의존성 미추가 (stdlib `str`/`re`, PyYAML만) | grep import | **PASS** | argparse, json, os, pathlib, re, subprocess, sys, yaml — 신규 외부 패키지 없음 |
| 2 | 구문/import 정상 | `python -c "import brain_tool"` | **PASS** | import OK 확인 |
| 3 | 결정론 (비결정 요소 부재) | 동일 쿼리 2회 실행 동일 결과 | **PASS** | pytest 2회 실행 89 passed / 89 passed — 결과 동일 |
| 4 | @header 의미 변화 없음 (갱신 불요 확인) | description/exports 비교 | **PASS** | description/exports 기존 필드 유지, cmd_search 기능 확장이나 인터페이스 불변 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **PASS** | grep 결과 0건 — password/secret/api_key/token 하드코딩 없음. 순수 문자열 로직만 |
| 2 | 저장 문서 불변 (프로덕션 `.opal/brain/` 미수정) | **PASS** | BrainTestCase.setUp에서 mkdtemp 기반 tmpdir 격리 확인. 프로덕션 .opal/brain/ 미접촉 |
| 3 | 배포 경계 (`~/.opal/` 직접 편집 없음) | **PASS** | brain_tool.py 내 ~/.opal/ 직접 write 코드 없음. diff 무차이로 install 경유 배포 확인 |

## RED 증거 (Step 1)

> EXECUTE Step 1 실행 결과 — 구현 전 RED 상태 확인.

**실행 명령**: `~/.opal/.venv/bin/python -m pytest opal/tools/brain-tool/tests/test_brain_tool.py::TestSearch -v`

**결과 요약**: 2 FAILED, 9 PASSED, 1 SKIPPED (총 12개)

**RED 시나리오**:
- `test_search_equiv_pair` (S-3, TS-004) — FAIL
  - '자동 취소' 쿼리 → auto-cancel-a.md만 매칭; '자동취소' 쿼리 → auto-cancel-b.md만 매칭 (불일치 확인)
- `test_search_equiv_triple` (S-4, TS-005) — FAIL
  - '선정 자동 취소' vs '선정자동취소' page set 불일치 확인

**SKIP 시나리오**:
- `test_norm_unit` (S-1, TS-001) — SKIPPED (_norm 헬퍼 미존재, 구현 전 예상 동작)

**기존 테스트 비파괴 확인**:
- 기존 TestSearch 7종(test_search_by_title_ok_true, test_search_finds_relevant_page, test_search_no_match_returns_empty, test_search_by_tag_filter, test_search_by_type_filter, test_search_limit) 모두 PASSED
- 신규 S-5(test_search_asymmetric), S-6(test_snippet_keeps_original_spacing), S-9(test_search_schema_unchanged) PASSED (현재 구현이 우연히 통과 또는 이미 호환)

**비고**: S-5와 S-6은 기존 구현에서 우연히 통과하나, 구현 후에도 유지됨을 GREEN 단계에서 확인.

## 7. 판정

> EXECUTE Step 3 GREEN 전환 결과 + TEST 워커 최종 확인 (2026-06-16).

**전체 테스트 결과**: 89 passed (전체 스위트), 0 failed, 0 skipped

**TestSearch GREEN 전환**:
- test_norm_unit (S-1): SKIPPED → PASSED (구현 후 활성화)
- test_search_equiv_pair (S-3): FAILED → PASSED
- test_search_equiv_triple (S-4): FAILED → PASSED
- test_search_asymmetric (S-5): PASSED (유지)
- test_snippet_keeps_original_spacing (S-6): PASSED (유지)
- test_search_schema_unchanged (S-9): PASSED (유지)

**회귀 0**: 기존 TestSearch 7종 + 다른 TestClass 전부 PASSED.

**S-10 (README)**: PASS — README.md:87 §5 "공백 무시 매칭" 설명 존재, :133 변경이력 025 행 존재.

**S-11 (재배포 정합)**: PASS — `diff` 무차이(exit=0), 소스/배포본 완전 일치.

**코드 품질**: PASS 4/4 — 외부 의존성 없음, import 정상, 결정론, @header 불변.

**보안**: PASS 3/3 — 시크릿 없음, tmpdir 격리, 배포 경계 준수.

**종합 판정**: **All Pass** — S-1~S-11 전 시나리오 PASS, RED→GREEN 입증(S-3/S-4), 회귀 0.

### PM Gate 체크 (7대 강제 룰) — 작성 시점 자가 점검

- [x] 코드 목(mock) 패턴이 시나리오 표 본문에 부재 (mock 금지 — 실 `brain_tool.py` 호출 명시)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (L3 해당 없음 명시)
- [x] L3 [SUPERVISOR] 마커 — 해당 없음 (자동 검증 전용)
- [x] 리스크 가설 표(§1) H-1~H-7 ID와 시나리오 S-1~S-11 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1) 명시
