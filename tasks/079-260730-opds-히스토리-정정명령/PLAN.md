# PLAN: 작업 히스토리 오기재 정정 명령 신설 (`update --kind history`)

> 작성일: 2026-07-30 | 입력: TASK.md (ANALYSIS.md 없음 — opds, 코드 분석 본 PLAN에서 직접 수행)
> 모드: Multi-Feature (기능 4개)
> 실행 모드: **복잡** (§6)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`memory-tool update`에 `--kind {memory,history}`를 신설하여 **잘못 기재된 작업 히스토리 행을 삭제 없이 정정**한다. 078의 MEMORY.json 단독 SSOT 전환으로 히스토리 관리가 전량 tool-gated가 된 결과 오기재를 되돌릴 경로가 사라졌고, 남은 선택지는 FIFO 밀어내기 또는 손편집(078이 없애려 한 행위)뿐이다. `--kind` 기본값을 `memory`로 두어 기존 호출·기존 테스트 132건을 무변경 통과시키고, 새 쓰기 경로를 만들지 않고 기존 `memory_lock`+`atomic_write_json`을 재사용한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | `update --kind {memory,history}` 인자 계약 + 분기 골격 | R-1 | P0 | 없음 |
| F-002 | 히스토리 정정 필드 적용 (무손실·원자성 보존) | R-2, R-4 | P0 | F-001 |
| F-003 | 인자 조합 오용 결정론 거부 | R-3 | P0 | F-001 |
| F-004 | 문서·배포 반영 + 실사용 검증 | R-5 | P0 | F-001, F-002, F-003 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (--kind 계약·분기) ─┬─ F-002 (필드 적용·무손실) ─┬─ F-004 (문서·배포·실사용)
                          └─ F-003 (조합 오용 거부) ────┘
```

F-001~F-003은 **동일 함수(`cmd_update`)·동일 파일(`memory_tool.py`)** 을 수정하므로 물리적으로 1 Step에 합류한다(§4.3 파일 충돌 방지). F 분해는 추적·QA 매핑 목적이다.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 `cmd_update` 시그니처 확장 (`memory_tool.py:998`) | 기존 `update --title … --status …` 호출 계약 + 기존 테스트 132건 (`tests/test_memory_tool.py`) — `--kind` 기본값 누락·argparse dest 충돌 시 전량 회귀 | **P0** | L1(단위/CLI) + L2(전 스위트 회귀) 의무 | TS-001, TS-002, TS-025 |
| H-2 | F-003 인자 조합 게이트 | 오용 조합이 **거부 대신 무시(silent no-op)** 되면 PM이 "정정됐다"고 믿고 진행 → 오기재 영속화. `--status`는 `historyRow`에 없는 필드(`schema/memory.schema.json:72`) | **P0** | L1(4거부 케이스 전수) 의무 | TS-011~TS-015 |
| H-3 | F-002 대상 행 식별 | 히스토리는 동일 `title` 중복 가능(재작업). 배열 순서 ↔ `show --brief`의 `date` 정렬 순서가 실제로 어긋남(`memory_tool.py:1229`; fixture index0=076/2026-07-21 vs index1=077/2026-07-23) → 사용자가 화면 순서로 "최신"을 판단하면 **의도와 다른 행을 정정** | P1 | L1(중복 title 2행 픽스처) 의무 + 응답 `match_count` 노출 | TS-018 |
| H-4 | F-002 쓰기 경로 | 거부·검증 실패 경로에서 `MEMORY.json` 부분 기록 / `.tmp` · `.lock` 잔여 → SSOT 파손. `atomic_write_json`(`:334-353`)·`memory_lock`(`:360-405`) 재사용 이탈 시 발생 | **P0** | L1(mtime·바이트 동일 + 잔여 파일 0건) + L2(동시 2프로세스) 의무 | TS-016, TS-017 |
| H-5 | F-004 `memory-learning.md` | 078에서 81줄로 슬림화한 SSOT가 신규 절·표 추가로 **재비대화** → 부트스트랩 토큰 잠식 | P1 | L1(줄 수 상한 게이트) 의무 | TS-023 |
| H-6 | F-002 FIFO 상호작용 | `_enforce_history_fifo`(`:774-778`)는 `rows[:5]` 순수 절단 — 정정 경로에서 호출하면 **>5행 문서(스키마에 maxItems 없음, `schema:25-29`)의 행이 조용히 삭제**되어 "삭제 없는 정정" 전제 파괴 | **P0** | L1(6행 문서 정정 → 6행 유지) 의무 | TS-009 |
| H-7 | F-002 행 필드 치환 | `historyRow.additionalProperties: false`(`schema:71`) — 정정 시 `corrected_at` 등 부가 키를 넣으면 `schema_validation_failed`. `show` 계약도 키 집합을 strict 단정(`tests/test_memory_tool.py:2055`) | P1 | L1(키 집합 동일성) 의무 | TS-010 |
| H-8 | F-001 argparse 등록 방식 | `--kind`에 `choices=`를 붙이면 위반 시 argparse가 **exit 2 + stderr usage(비 JSON)** 를 내어 R-1 AC(c)(`invalid_kind`)와 "응답은 단일라인 JSON, traceback 금지" 계약을 동시 위반. `append`는 `choices=`를 쓰므로(`:1395`) 무비판 복사 위험 | P1 | L1(exit code·stdout JSON 동시 단정) 의무 | TS-004 |
| H-9 | F-004 `tools.md` | 077이 같은 워킹트리에서 `tools.md` code-scan 절을 편집 중 — `Write`/전문 재작성 시 상호 클로버 | P1 | L1(077 소유 절 무변경 diff 확인) 의무 | TS-022 |
| H-10 | F-004 배포·실사용 | `install`(배포)과 실 `.opal/MEMORY.json` 정정은 **비가역**. 미배포 상태로 실사용 검증하면 구 코드가 돌고, 잘못된 sha를 넣으면 실 메모리가 오염 | P1 | L3(실환경 1회, 사전 백업·사후 `show --brief` 대조) 의무 | TS-024 |

---

## 2. 기능별 분석

### F-001: `update --kind {memory,history}` 인자 계약 + 분기 골격

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/memory-tool/memory_tool.py` | `cmd_update`(`:998-1045`) + `main()` argparse `p_update`(`:1405-1412`) | 수정 |
| BE | `opal/tools/memory-tool/memory_tool.py` | `ERROR_CODES`(`:121-146`) — `invalid_kind`(`:125`)·`invalid_args`(`:145`) 재사용 | 참조(무변경) |
| 공통 | `opal/tools/memory-tool/schema/memory.schema.json` | `$defs.historyRow`(`:69-97`) 필드 정의 | 참조(무변경) |
| BE | `opal/tools/memory-tool/tests/test_memory_tool.py` | 132건 회귀 기준선 + RED 신규 케이스 | 수정 |

#### 2.1.2 현재 구현

`cmd_update`(`memory_tool.py:998-1045`)의 흐름:

1. `--file`→`json_path`, `--title` 공백 검증 → `title_required`(`:1002-1005`)
2. `memory_lock(json_path,"update")` 진입 → `load_document(..., already_locked=True)` (`:1007-1008`) → `_pop_migration_report()`
3. `doc["memories"]`를 순회하여 **첫 title 일치 행**을 `target`으로 잡고, 없으면 `row_not_found`(`:1011-1017`)
4. `--new-title`/`--status`/`--summary`를 `is not None` 조건으로 개별 적용, 각각 `title_required`/`invalid_status`/`summary_too_long` 검증(`:1019-1035`)
5. `validate_document(doc)` → 위반 시 `schema_validation_failed`, 통과 시 `atomic_write_json`(`:1037-1041`)
6. 락 해제 후 `build_review_block(doc)` → `ok("update", title=…, status=…, review=…, migration=…)`(`:1044-1045`)

`--kind` 인자는 **없다**. argparse `p_update`는 `--file`/`--title`(required) + `--status`/`--summary`/`--new-title`(모두 `default=None`)만 등록한다(`:1405-1412`). 따라서 히스토리 제목을 넘기면 3단계에서 `doc["memories"]`에 없어 `row_not_found`로 거부된다(078 실측 = TASK 배경 분석 (1)).

**선례**: `cmd_append`는 이미 동일 함수 안에서 `kind`로 분기한다 — `kind = args.kind` → `if kind not in ("memory","history"): err("append","invalid_kind")`(`:924-926`) → `memory_lock` 안에서 `if kind == "memory": … else: # kind == "history"`(`:935`, `:966`)로 갈라지고, `validate_document`+`atomic_write_json`+`build_review_block`+`ok()` 골격을 공유한다. 응답에도 `kind=kind`를 additive로 실어 보낸다(`:989`, `:991`).

`invalid_kind`는 **이미 `ERROR_CODES`에 존재**한다 — `"--kind는 memory 또는 history 중 하나여야 함: {kind}"`(`:125`).

#### 2.1.3 영향 범위

- **상위 의존(호출자)**: `~/.opal/tools/memory-tool/run.sh` 경유 CLI 호출 전량. `improve_tool.py`는 `append`/`show`만 위임하며(`tools.md:764-765`, `:790`) `update`를 호출하지 않는다 → `update` 응답 키 변경의 파급은 없다.
- **하위 의존(피호출자)**: `memory_lock`·`load_document`·`validate_document`·`atomic_write_json`·`build_review_block` — 전부 **재사용, 무변경**.
- **공유 상태**: `MEMORY.json` 문서 dict. `main()`의 `SCHEMA is None` 게이트(`:1462-1463`)가 모든 서브명령 앞에 있으므로 스키마 부재 경로는 자동 상속된다.
- **관련 테스트**: `TestUpdateStatusTransition`(`:602-676`), `TestUpdateNewTitle`(`:1267-1379`, 기존 `--status`/`--summary` 회귀 단정 2건 포함), `TestReviewAmbient.test_update_response_has_review`(`:803`), `TestMarkerGuard`(`:202-224`), `TestSuiteMigration`(`:1718~`), `TestSkeleton.test_all_eight_subcommands_registered`(`:125-136`). 응답 **키 집합을 strict 단정하는 테스트는 없다**(strict 단정은 `show` 행 대상 — `:1984`, `:2055`) → 응답에 `kind` 등 additive 키 추가는 안전.

---

### F-002: 히스토리 정정 필드 적용 (무손실·원자성 보존)

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/memory-tool/memory_tool.py` | `cmd_update` history 분기 신설 | 수정 |
| BE | `opal/tools/memory-tool/memory_tool.py` | `_enforce_history_fifo`(`:774-778`) — **호출하지 않음**(§3.2.2 P-5) | 참조(무변경) |
| BE | `opal/tools/memory-tool/memory_tool.py` | `atomic_write_json`(`:334-353`) / `memory_lock`(`:360-405`) / `load_document`(`:412-461`) | 재사용(무변경) |
| BE | `opal/tools/memory-tool/tests/test_memory_tool.py` | 무손실·원자성·복수매치 케이스 | 수정 |

#### 2.2.2 현재 구현

- **히스토리 배열 규약**: `append --kind history`는 `doc["history"].insert(0, new_row)` 후 `_enforce_history_fifo`를 적용한다(`:978-979`). 스키마는 `"맨 앞=최신"`을 명시한다(`schema/memory.schema.json:28`). → **배열 index 0 = 가장 최근 삽입 행.**
- **FIFO 집행체**: `_enforce_history_fifo(rows)`의 본체는 `return rows[:HISTORY_FIFO_LIMIT]`(`:774-778`) — 길이 절단만 하는 순수 함수. `HISTORY_FIFO_LIMIT`은 스키마 `x-constants`에서 파생(`:80`).
- **스키마 강제 아님**: `properties.history`에 `maxItems`가 **없다**(`schema:25-29`) → 6행 이상 문서도 `validate_document`를 통과한다. FIFO는 append/prune 시점 규칙일 뿐이다.
- **행 필드 계약**: `historyRow.required = [title,date,stage,path,result]` + `additionalProperties: false`(`schema:70-72`). `result`에는 `maxLength`가 **없고**(`schema:92-95`), `memoryRow.summary`에만 `maxLength: 80`이 있다(`schema:62-66`).
- **표시 순서 주의**: `cmd_show`는 `--brief` 또는 `--history N`일 때 `sorted(history_rows, key=date, reverse=True)`로 **재정렬**한다(`:1229`). 비-brief `show`는 배열 원순서를 그대로 낸다(`:1209`, `:1237`). 실제로 `fixture_doc_populated.json`의 index0=`076…`(2026-07-21)·index1=`077…`(2026-07-23)로 배열 순서와 날짜 순서가 어긋난다 → H-3.
- **원자성 기전**: `memory_lock`은 `O_CREAT|O_EXCL` 배타 클레임 + stale 60s + 타임아웃 5s(`:360-390`), `finally`에서 반드시 `unlink`(`:396-405`). `atomic_write_json`은 tmp→`fsync`→`os.replace`이며 실패 시 tmp를 정리하고 예외를 전파해 원본을 보존한다(`:334-353`). **검증(`validate_document`)이 쓰기보다 앞에 있으므로**(`:1037-1041`) 스키마 위반은 파일에 닿지 않는다.

#### 2.2.3 영향 범위

- **공유 상태**: `doc["history"]` 리스트. in-place 필드 치환이므로 `len()` 불변 → `build_review_block`의 `history_status.count`/`fifo_trimmed`(`:870-876`) 계산 결과가 정정 전후 동일.
- **하위 소비자**: `dashboard/backend/parsers/memory_parser.py`는 JSON 기준 기대값으로 재작성됨(078 DONE §5-1) — 행 수·키 집합이 불변이므로 무영향.
- **관련 테스트**: `TestHistoryFIFO`(`:311-354`), `TestPruneIdempotent`(`:355-395`), `TestAtomicWrite`, `TestJsonIO`(`:2055` 히스토리 키 strict 단정).

---

### F-003: 인자 조합 오용 결정론 거부

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/memory-tool/memory_tool.py` | `_check_update_kind_args` 신설(모듈 private 헬퍼) | 수정(함수 추가) |
| BE | `opal/tools/memory-tool/memory_tool.py` | `ERROR_CODES` — `invalid_kind`(`:125`)·`invalid_args`(`:145`) **재사용, 신설 없음** | 참조(무변경) |
| BE | `opal/tools/memory-tool/memory_tool.py` | `_path_has_traversal`(`:816-818`) — `--path` 값 가드에 재사용 | 참조(무변경) |

#### 2.3.2 현재 구현

- `ERROR_CODES`는 23종. `invalid_kind`(`:125`)와 `invalid_args`("인자 조합이 올바르지 않음: {detail}", `:145`)가 이미 있다. `invalid_args`의 선례 사용처는 `cmd_task_number`의 `--bump`/`--set` 동시 지정 거부(`:1337-1338`, `detail=` 인자로 구체 사유 주입).
- `err()`는 `ERROR_CODES[code]`를 템플릿으로 `format(**kwargs)`한 뒤 단일라인 JSON을 출력하고 `sys.exit(exit_code)`한다(`:161-174`) — traceback 없음.
- **`--kind memory` 필드 0개는 현재 허용**된다: 3개 필드 전부 `None`이면 아무 것도 적용하지 않고 그대로 `atomic_write_json` → `ok`(`:1019-1045`). 기존 계약이므로 유지해야 한다(H-1).
- `append`는 `--summary`를 히스토리에서 `result`로 매핑한다(`:967`, `:976`) — 한 플래그가 두 스키마 필드를 겸하는 **기존 와트**. 신규 `update` 경로에 이를 전파할지가 P-2 결정 사항.

#### 2.3.3 영향 범위

- 신설 게이트는 **락 획득 전**에 위치하므로 파일·락에 전혀 접근하지 않는다 → R-4 AC(a)(파일 mtime·내용 불변, `.tmp`·락 잔여 0건)를 구조적으로 만족.
- `append`의 `--kind` argparse `choices=`(`:1395-1396`)는 **무변경**(TASK 비범위: 타 서브명령 `--kind` 확장) → 회귀 없음.

---

### F-004: 문서·배포 반영 + 실사용 검증

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/tools/memory-tool/README.md` | §`update`(`:89-101`) 계약 상세 SSOT + §에러 코드 표(`:253-283`) + §변경이력(`:285-291`) | 수정 |
| 문서 | `opal/core/references/tools.md` | §memory-tool(`:580-660`) — `update` 커맨드 블록(`:605-607`) + 에러코드 표 + 변경이력(`:880`) | 수정(**Edit 전용**) |
| 문서 | `opal/core/references/harness/memory-learning.md` | §정리 FIFO 불릿(`:22`) 인접 1줄 + 변경이력(`:81`) | 수정(최소) |
| 배치 | `scripts/install-mac.sh` | `~/.opal/` 배포 | 실행(무변경) |
| 배치 | `.opal/MEMORY.json` | R-5 AC(b) 실사용 검증 대상(078 히스토리 `stage`) | 도구 경유 변경 |

#### 2.4.2 현재 구현

- **README §`update`**(`:89-101`): usage 블록에 `--status`/`--summary`/`--new-title`만, 에러는 `title_required | row_not_found | invalid_status | summary_too_long | schema_validation_failed`. `--kind` 언급 없음. §에러 코드 표에는 `invalid_kind`가 이미 있으나 "`--kind`가 `memory`/`history` 외 값"으로만 서술되어 `append` 전용으로 읽힌다.
- **tools.md §memory-tool**(`:580-660`): `update` 블록(`:605-607`)에 `[--status] [--summary] [--new-title]`만. 에러코드 표(`:654~`)에 `invalid_kind` 행 **없음**. `v2.6` 변경이력 행이 078 반영분(`:880`).
- **memory-learning.md**: 총 81줄. `:22`가 "작업 히스토리는 최대 5개 FIFO [MUST] … 결정론적으로 제거", `:60`대에 `[MUST] delete 무손실 가드` 블록. 히스토리 **정정** 경로 서술 없음.
- **docs/ 갱신 판정**: `docs/PROJECT.md:170`("변경은 `memory-tool`만 수행")·`docs/ARCHITECTURE.md:82`(memory-tool 역할 1줄) 모두 **서브명령 인자 수준을 서술하지 않는다**. 새 API 엔드포인트/컴포넌트/시스템 구조/신규 컨벤션 어디에도 해당하지 않으므로 → **docs/ 갱신 Step 불필요(판정: 해당 없음)**. §5.3에 판정 근거 확인 항목으로 남긴다.
- **실사용 대상 현황**(실측 `.opal/MEMORY.json`): 히스토리 5행, index0 = `title="078 메모리 SSOT JSON 전환"`, `stage="완료·미커밋"`, `path="tasks/078-260728-opd-메모리-json전환/"`.

#### 2.4.3 영향 범위

- `tools.md`는 077과 **공유 파일**(078 DONE §8 규율) — `Edit` 전용·헤딩 앵커 편집으로 code-scan 절 무변경 보존.
- `memory-learning.md`는 부트스트랩 로드 대상 → 줄 수 증가가 곧 토큰 비용(H-5).
- 배포는 `~/.opal/` 전체를 갱신하므로 077 진행분과 함께 나갈 수 있다 → 배포 Step은 PM 직접 수행·의도 확인.

---

## 3. 기능별 설계

### F-001: `update --kind {memory,history}` 인자 계약 + 분기 골격

#### 3.1.1 파일 변경 계획

**신규 생성**: 없음.

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/memory-tool/memory_tool.py` | BE | `main()` `p_update`에 `--kind`/`--stage`/`--result`/`--path` 4인자 추가 | `memory_tool.py:1405-1412` |
| 2 | `opal/tools/memory-tool/memory_tool.py` | BE | `cmd_update`를 `kind` 2분기 구조로 재편(기존 memory 블록 무변경 이식) | `memory_tool.py:998-1045`, 선례 `:935`·`:966` |
| 3 | `opal/tools/memory-tool/memory_tool.py` | BE | `@header.description` 갱신 + 변경이력 `v2.1` 행 추가 | `memory_tool.py:1-22`, (→ D-9 §@header 규칙) |

#### 3.1.2 API 설계 — **P-1 결정: `cmd_update` 내부 `kind` 분기 + 락 밖 사전 게이트 헬퍼**

**결정**: (a) `cmd_update` 내부 분기 채택. (b) 별도 `cmd_update_history` 분리·(c) dispatch 테이블은 **기각**.

근거:
- `cmd_append`가 이미 동일 패턴이다 — 단일 함수 안에서 `kind` 검증 후 `memory_lock` 내부에서 `if kind == "memory": … else:`로 갈라지고 검증·쓰기·review·응답 골격을 공유한다(`memory_tool.py:924-991`). 페르소나 원칙 4(프로젝트 기존 패턴 존중)·PRINCIPLES §2 Simplicity.
- 별도 함수 분리는 `memory_lock`+`load_document`+`validate_document`+`atomic_write_json` 골격을 복제하게 되어 [MUST] `TASK.md` §제약 조건: "**원자성·락 재사용** — 새 쓰기 경로를 만들지 않는다." 를 위반한다.
- dispatch 테이블은 이 파일 어디에도 없는 신규 패턴(9서브명령이 모두 `set_defaults(func=…)` + 함수 내 분기) → 불필요한 구조 도입.

**argparse 등록** (`main()`, `:1411` 다음에 삽입):

```python
p_update.add_argument("--kind", default="memory", metavar="{memory,history}",
                      help="정정 대상 — memory(기본: 메모리 인덱스 행) | history(작업 히스토리 행)")
p_update.add_argument("--stage",  default=None, help="새 단계 (history 전용)")
p_update.add_argument("--result", default=None, help="새 핵심결과 (history 전용)")
p_update.add_argument("--path",   default=None, help="새 tasks/<폴더>/ 경로 (history 전용)")
```

> **[MUST] `--kind`에 `choices=`를 사용하지 않는다.** argparse `choices` 위반은 exit 2 + stderr usage(비 JSON)를 내므로 `TASK.md` R-1 AC(c)("`invalid_kind`로 거부")와 [MUST] `TASK.md` §제약 조건: "**응답 계약** — `{"ok": true|false, ...}` 단일라인 JSON, traceback 금지." 를 **동시에 위반**한다. 허용값은 `metavar`+`help`로 `--help`에 노출하고, 값 검증은 코드에서 수행해 `err("update","invalid_kind",kind=…)`를 낸다. `append`의 `choices=`(`:1395`)는 비범위이므로 무변경. (H-8)

> `--kind` 기본값이 `"memory"`이므로 `--kind` 미지정 호출은 기존 경로에 그대로 들어간다 — [MUST] `TASK.md` §제약 조건: "**하위호환** — `--kind` 기본값 `memory`. 기존 `update` 호출·기존 테스트가 무변경으로 통과해야 한다."

**`cmd_update` 골격**:

```python
def cmd_update(args):
    """메모리 인덱스 행(--kind memory, 기본) 또는 작업 히스토리 행(--kind history) 수정.
    history 분기는 정정 전용 — 행 추가·삭제 없음(행 수 불변, FIFO 미적용).
    """
    json_path = pathlib.Path(args.file)
    title = (args.title or "").strip()
    if not title:
        err("update", "title_required")

    kind = getattr(args, "kind", "memory")
    _check_update_kind_args(kind, args)      # 락 밖 사전 게이트 — 위반 시 err()로 종료 (R-4 AC a)

    with memory_lock(json_path, "update"):
        doc = load_document(json_path, "update", already_locked=True)
        migration = _pop_migration_report()

        if kind == "memory":
            ...  # 기존 :1011-1035 블록 무변경 이식
            result_kwargs = {"status": target.get("status")}
        else:  # kind == "history"
            target, matched_index, match_count, changed = _apply_history_correction(doc, title, args)
            result_kwargs = {"matched_index": matched_index, "match_count": match_count,
                             "changed": changed, "history_count": len(doc["history"])}

        violations = validate_document(doc)          # 쓰기 전 검증 — 위반 시 파일 무접촉 (:1037-1039)
        if violations:
            err("update", "schema_validation_failed", violations=violations)
        atomic_write_json(json_path, doc)            # 기존 원자적 쓰기 재사용 (:334)

    review = build_review_block(doc)
    ok("update", kind=kind, title=title, review=review, migration=migration, **result_kwargs)
```

**응답 계약**:

| kind | 응답 키 | 하위호환 |
|------|---------|---------|
| `memory` | `ok`·`command`·**`kind`(신규 additive)**·`title`·`status`·`review`·`migration` | 기존 키 전량 보존. 응답 키 집합을 strict 단정하는 테스트 없음(strict 단정은 `show` 행 대상 `tests/test_memory_tool.py:1984`·`:2055`) → additive 안전. `append`도 `kind`를 응답에 싣는다(`:989`) |
| `history` | `ok`·`command`·`kind`·`title`(조회 키)·`matched_index`·`match_count`·`changed[]`·`history_count`·`review`·`migration` | 신규 경로 — 제약 없음 |

- `title`은 **조회에 사용한 값**을 반환한다(memory 경로의 기존 관례 `:1045`와 통일). 정정 후 제목은 `changed`에 `"title"`이 포함되는지로 판정한다.
- `history_count`는 `append --kind history` 응답 키(`:991`)와 동일 명칭 — R-2 AC(d)(행 수 불변)를 **응답만으로 관측 가능**하게 한다.
- `match_count > 1`은 H-3을 호출자에게 표면화하는 유일한 신호다(§3.2.2 P-4).

#### 3.1.3 환경 변경

해당 없음. [MUST] `memory_tool.py` @header(`:6`): "표준 라이브러리만." → `argparse` 외 신규 import 없음.

#### 3.1.4 배치/마이그레이션

해당 없음(문서 스키마 무변경 → `version` 불변, lazy 마이그레이션 경로 무영향).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 (a) | 회귀 테스트 | `--kind` 미지정 + `--status`/`--summary`/`--new-title` 각각 단독·복합 호출 시 정정 전과 동일하게 `ok:true`, 대상 메모리 행만 변경 |
| TS-002 | R-1 (a) | 회귀 테스트 | `update --file X --title T`(정정 필드 0개, `--kind` 미지정) → `ok:true` (기존 관대 동작 보존, `invalid_args` 아님) |
| TS-003 | R-1 (b) | 기능 테스트 | `--kind history --stage "완료·커밋(abc1234)"` → `ok:true`, `kind:"history"`, 대상 히스토리 행 `stage`만 변경 |
| TS-004 | R-1 (c) | 기능 테스트 | `--kind bogus` → stdout 단일라인 JSON `ok:false`·`error:"invalid_kind"`, **exit code 1**(argparse의 2 아님), stderr에 usage/traceback 없음, 파일 불변 |
| TS-019 | R-1, R-5 (a) | 산출물 검사 | `update --help` 출력에 `--kind`·`--stage`·`--result`·`--path` 및 `{memory,history}` 문자열이 모두 노출 |
| TS-020 | R-1 (b) | 기능 테스트 | `--kind history` 성공 응답에 `review` 블록 첨부(기존 ambient 자가검토 계약 유지) |
| TS-025 | R-1 (a) | 회귀 테스트 | `python -m unittest` 전 스위트 — 기존 132건 전량 GREEN(신규 케이스 제외 집계) |
| TS-026 | 제약 | 산출물 검사 | `memory_tool.py` `@header.description`에 `--kind history` 반영 + 변경이력 `v2.1` 행 존재; 테스트 파일 `@header.exports`에 신규 클래스 등재 |

---

### F-002: 히스토리 정정 필드 적용 (무손실·원자성 보존)

#### 3.2.1 파일 변경 계획

**신규 생성**: 없음(픽스처 파일도 신설하지 않는다 — 6행·중복 title 문서는 기존 `fixture_doc_populated.json`을 in-test로 로드·가공하여 구성).

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/memory-tool/memory_tool.py` | BE | `_apply_history_correction(doc, title, args)` 헬퍼 신설 — 대상 식별 + 필드 in-place 치환 | `schema:69-97`, `memory_tool.py:1011-1035` |
| 2 | `opal/tools/memory-tool/tests/test_memory_tool.py` | BE | `TestUpdateKindHistory`·`TestUpdateHistoryLossless` 클래스 신설 | (→ D-3) |

#### 3.2.2 API 설계

**헬퍼 시그니처**:

```python
_HISTORY_CORRECTABLE_FIELDS = ("stage", "result", "path")   # argparse dest == historyRow 필드명

def _apply_history_correction(doc, title, args):
    """히스토리 행 정정 — (target, matched_index, match_count, changed[]) 반환.
    행 추가·삭제 없음. 미지정 필드는 불변. 새 키 삽입 금지.
    """
    rows = doc["history"]
    matches = [i for i, r in enumerate(rows) if r.get("title") == title]
    if not matches:
        err("update", "row_not_found", title=title)      # R-3 AC(c) — 락 안이지만 쓰기 전이므로 파일 불변
    idx = matches[0]                                      # 배열 선행 = 가장 최근 append (P-4)
    target = rows[idx]
    changed = []
    if args.new_title is not None:
        new_title = args.new_title.strip()
        if not new_title:
            err("update", "title_required")
        target["title"] = new_title
        changed.append("title")
    for field in _HISTORY_CORRECTABLE_FIELDS:
        value = getattr(args, field, None)
        if value is not None:
            target[field] = value.strip()
            changed.append(field)
    return target, idx, len(matches), changed
```

> **[MUST] `historyRow.additionalProperties: false`** (`opal/tools/memory-tool/schema/memory.schema.json:71`) — 정정 시 `corrected_at`·`corrected_by` 등 **부가 키를 삽입하지 않는다**. 삽입하면 `validate_document`가 `schema_validation_failed`로 거부하며(`memory_tool.py:1037-1039`), `show` 히스토리 행 키 집합 strict 단정(`tests/test_memory_tool.py:2055`)도 깨진다. 정정 이력은 git과 `tasks/`가 추적한다. (H-7)

> **[MUST] `date`는 정정 대상이 아니다.** `TASK.md` §배경 분석 (2)가 `date`를 "낮음(자동 기록)"으로 분류하고 R-2가 대상 필드를 `--stage`/`--result`/`--path`/`--new-title` 4개로 못박았다 → `--date` 인자를 신설하지 않는다(범위 고정).

**P-4 결정 — 복수 매치 정책: 배열 선행 1건(`matches[0]`) + `match_count` 응답 노출**

| 후보 | 채택 | 판단 |
|------|------|------|
| **배열 선행 1건** | ✅ | 결정론적이며 문서화된 불변식에 기반 |
| 거부(ambiguous 에러) | ❌ | 재작업으로 동일 title이 2행이 되는 순간 **주 유스케이스(078 `stage` 사후 확정)가 영구 봉쇄**된다. 범위상 index 선택자(`--index`)를 신설할 수 없어 탈출구가 없다 |
| 전량 정정 | ❌ | 한 번의 오지정이 여러 행에 번진다 — "정정"의 반대 방향 |

근거·트레이드오프:
- **결정론**: `append`가 `insert(0, …)`로만 행을 넣고(`memory_tool.py:978`) 스키마가 `"맨 앞=최신"`을 규약으로 명시하므로(`schema:28`), `matches[0]`은 임의 선택이 아니라 **"가장 최근에 append된 행"** 이라는 정의된 대상이다. `memories` 경로의 first-match 의미론(`memory_tool.py:1011-1015`)과도 동일한 정신 모델이다.
- **오정정 위험의 비대칭**: 이 명령은 삭제를 하지 않는다. 잘못된 행을 정정해도 **같은 명령으로 되정정 가능**하며, 원값은 git(`.opal/MEMORY.json` 이력)으로 복구된다. 반면 거부 정책의 비용(주 유스케이스 봉쇄)은 되돌릴 수 없다. 따라서 결정론적 단일 대상 + 관측 신호가 최적점이다.
- **잔여 위험 표면화**(H-3): 배열 순서와 `show --brief`의 `date` 정렬 순서는 실제로 어긋난다(`memory_tool.py:1229`; 픽스처 index0=076/07-21 vs index1=077/07-23). 따라서 ① 응답에 `match_count`(>1이면 PM이 중복을 인지)와 `matched_index`를 실어 보내고, ② 문서에 "대상 판별은 **비-brief `show`의 `history_rows` 배열 순서** 기준"임을 명시한다(§3.4.2). FIFO=5 상한 덕에 중복 규모는 최대 5행으로 제한된다.

**P-5 결정 — FIFO 재적용: 하지 않는다 [MUST]**

> **[MUST] 정정 경로에서 `_enforce_history_fifo`를 호출하지 않는다.**

근거(불필요 + 유해):
1. **불필요** — 정정은 `rows[idx]`의 필드만 in-place 치환하므로 `len(doc["history"])`가 변하지 않는다(R-2 AC d). `_enforce_history_fifo`의 본체는 `rows[:HISTORY_FIFO_LIMIT]`(`memory_tool.py:774-778`)로 **길이 절단만** 하며, 입력 문서는 이미 `load_document`→`validate_document`를 통과한 상태다(`:457-459`).
2. **유해** — `properties.history`에 `maxItems`가 없어(`schema:25-29`) 6행 이상 문서도 유효하다(마이그레이션 산물·과거 손편집 잔재). 이때 FIFO를 적용하면 **정정 명령이 조용히 행을 삭제**하여 이 태스크의 전제("삭제 없는 정정")와 [MUST] `TASK.md` R-4: "부분 기록으로 SSOT 파손 금지"의 무손실 정신을 함께 깨뜨린다. (H-6)
3. **역할 분리** — 초과 상태는 `build_review_block`의 `history_status.fifo_trimmed`(`memory_tool.py:871`)가 응답에서 자동 표면화하고, 실제 정리는 `prune` 전담이다(`README.md:125-133`). 정정 명령이 정리를 겸하면 단일책임이 깨진다.

**원자성·락 재사용 매핑** (R-4):

| 요구 | 재사용 지점 | 보증 |
|------|-----------|------|
| 배타 접근 | `memory_lock(json_path,"update")` (`:360-405`) | `O_EXCL` + stale 60s + 타임아웃 5s → `lock_timeout`, `finally` unlink |
| 원자적 교체 | `atomic_write_json` (`:334-353`) | tmp→`fsync`→`os.replace`, 실패 시 tmp 정리 후 예외 전파 |
| 쓰기 전 검증 | `validate_document` → `err` (`:1037-1039`) | 스키마 위반은 파일에 닿지 않음 |
| 조합 오용 | `_check_update_kind_args` (**락 밖**, §3.3.2) | 락·파일 전혀 접근하지 않음 → `.lock`·`.tmp` 잔여 0건 |

신규 쓰기 경로·신규 락 파일·신규 임시파일 규약을 **만들지 않는다**.

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

해당 없음. 문서 `version` 불변(`schema:10-14`) → 기존 MEMORY.json 재검증·재작성 불필요.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R-2 (a) | 기능 테스트 | `--stage`/`--result`/`--path`/`--new-title` 개별 지정 4케이스 + 4필드 복합 1케이스 → 전부 `ok:true`, `changed[]`가 지정 필드와 정확히 일치 |
| TS-006 | R-2 (b) | 기능 테스트 | `--stage`만 지정 → 대상 행의 `title`/`date`/`path`/`result` 및 **다른 히스토리 4행 전체**가 바이트 동일 |
| TS-007 | R-2 (c) | 통합 테스트 | 정정 직후 `show --file X`가 `ok:true`(재로드 시 `validate_document` 통과) + 응답 `violations` 없음 |
| TS-008 | R-2 (d) | 기능 테스트 | 5행 문서 정정 → `history_count:5`, 파일 내 `history` 길이 5 |
| TS-009 | R-2 (d), H-6 | 기능 테스트 | **6행** 히스토리 문서 정정 → 6행 유지(FIFO 미적용, 행 삭제 0), `review.history_status.fifo_trimmed:true`로 초과만 표면화 |
| TS-010 | R-2 (c), H-7 | 기능 테스트 | 정정 후 대상 행의 키 집합이 정확히 `{title,date,stage,path,result}` |
| TS-016 | R-4 (a) | 보안/통합 테스트 | 거부 경로 전수(TS-004·TS-011~TS-015·TS-018 실패분) 후 `MEMORY.json` 바이트·mtime 동일 + 디렉토리에 `*.tmp*` 0건 + `MEMORY.json.lock` 0건 |
| TS-017 | R-4 (b) | 통합 테스트 | 2 프로세스가 서로 다른 필드를 동시 정정 → 클로버 0(둘 다 반영) 또는 한쪽이 `lock_timeout`으로 결정론 실패, 문서는 항상 스키마 유효 |
| TS-018 | H-3, P-4 | 기능 테스트 | 동일 `title` 2행 문서 → 배열 선행 행만 변경, 후행 행 불변, 응답 `matched_index:<선행 index>`·`match_count:2` |

---

### F-003: 인자 조합 오용 결정론 거부

#### 3.3.1 파일 변경 계획

**신규 생성**: 없음.

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/memory-tool/memory_tool.py` | BE | `_check_update_kind_args(kind, args)` 신설 — 락 밖 사전 게이트 | `TASK.md` R-3, `memory_tool.py:1337-1338` 선례 |
| 2 | `opal/tools/memory-tool/tests/test_memory_tool.py` | BE | `TestUpdateKindArgGuard` 클래스 신설 | (→ D-3) |

#### 3.3.2 API 설계

**P-3 결정 — 신규 에러코드 신설 없음. `invalid_kind`·`invalid_args` 재사용.**

- `invalid_kind`는 **이미 `ERROR_CODES`에 존재**한다: `"--kind는 memory 또는 history 중 하나여야 함: {kind}"` (`memory_tool.py:125`). `cmd_append:924-926`이 이미 이 코드를 쓴다. TASK가 언급한 `invalid_kind`는 **신설 대상이 아니라 재사용 대상**이다. README 에러 코드 표에도 이미 등재되어 있다(`README.md` §에러 코드 `invalid_kind` 행).
- 조합 위반 4종은 전부 `invalid_args`("인자 조합이 올바르지 않음: {detail}", `:145`)로 처리하고 **`detail`로 사유를 구체화**한다. `cmd_task_number`의 `--bump`/`--set` 동시 지정 거부가 동일 패턴(`:1337-1338`). 위반 유형마다 코드를 늘리면 `ERROR_CODES` 23종이 27종으로 팽창하고, 호출자는 `invalid_args`+`detail`만으로 충분히 분기·표시할 수 있다(PRINCIPLES §2 Simplicity).
- **결과**: `ERROR_CODES` 딕셔너리 **무변경** → 에러코드 표 동기화 테스트(`tests/test_memory_tool.py:1026-1063` `TestErrorCodes`)에 회귀 위험 없음.

**P-2 결정 — 인자 조합 규칙 확정표**

| # | 조합 | 결과 | 코드 / `detail` |
|---|------|------|----------------|
| 1 | `--kind` 미지정 + `--status`/`--summary`/`--new-title` 임의 조합 | **허용** (기존 동작 그대로) | — |
| 2 | `--kind memory` + `--status`/`--summary`/`--new-title` | 허용 | — |
| 3 | `--kind memory` + `--stage`/`--result`/`--path` 중 1개 이상 | **거부** (R-3 b) | `invalid_args` / `"--stage/--result/--path는 --kind history 전용"` |
| 4 | `--kind history` + `--status` | **거부** (R-3 a) | `invalid_args` / `"--status는 히스토리 행에 없는 필드 — --kind memory 전용"` |
| 5 | `--kind history` + `--summary` | **거부** | `invalid_args` / `"--summary는 --kind memory 전용 — 히스토리 핵심결과는 --result"` |
| 6 | `--kind history` + `--stage`/`--result`/`--path`/`--new-title` 중 1개 이상 | 허용 | — |
| 7 | `--kind history` + 정정 필드 0개 | **거부** (R-3 d) | `invalid_args` / `"정정 필드(--stage/--result/--path/--new-title) 중 최소 1개 필요"` |
| 8 | `--kind memory` + 정정 필드 0개 | **허용** (기존 동작 보존) | — |
| 9 | `--kind` 가 `memory`/`history` 외 값 | **거부** (R-1 c) | `invalid_kind` / (템플릿 `:125`) |
| 10 | `--kind history` + `--path` 값에 `..` 포함 | **거부**(보안 권고) | `invalid_args` / `"--path에 상위 경로 탈출(..) 문자열 금지"` |

**`--summary` 판단 (P-2 명시 요구)**: 히스토리에서 `--summary`는 **거부한다. 별칭 허용하지 않는다.**
- 근거 1 — 스키마 정합: 히스토리 행에 `summary` 필드가 없고(`schema:72` required = `title,date,stage,path,result`) 대응 필드는 `result`다(`schema:92-95`).
- 근거 2 — 검증 계약 충돌: `memoryRow.summary`에는 `maxLength: 80`(`schema:64`)이 있고 `cmd_update`가 `summary_too_long`을 던지지만(`:1031-1034`), `historyRow.result`에는 길이 제약이 **없다**. 별칭을 허용하면 같은 플래그가 kind에 따라 길이 제약을 켜고 끄는 비결정적 표면이 된다.
- 근거 3 — 기존 와트를 전파하지 않는다: `append --kind history`는 `--summary`를 `result`로 매핑하는데(`memory_tool.py:967`·`:976`) 이는 한 플래그가 두 스키마 필드를 겸하는 알려진 와트다. 하위호환 때문에 `append`는 손대지 않되(비범위), 신규 `update` 표면에는 복제하지 않는다. 대신 거부 메시지가 `--result`를 직접 안내하여 학습 비용을 0으로 만든다.

**`--path` 탈출 가드(#10)**: 히스토리 `path`는 스키마상 자유 문자열이고(`schema:88-91`) memory-tool은 이 값으로 파일을 열지 않지만, 대시보드 등 후속 소비자가 링크로 소비하므로 저장 시점에 차단한다. 기존 `_path_has_traversal`(`memory_tool.py:816-818`)을 **재사용**한다(신규 헬퍼 없음). AC 필수 항목은 아니며 §5.4 보안 QA로 추적한다.

**헬퍼 시그니처**:

```python
_UPDATE_HISTORY_ONLY_ARGS = ("stage", "result", "path")
_UPDATE_MEMORY_ONLY_ARGS  = ("status", "summary")

def _check_update_kind_args(kind, args):
    """--kind ↔ 필드 인자 조합 사전 검증. 락 획득·파일 접근 이전에 호출한다 (R-4 AC a).
    위반 시 err()가 단일라인 JSON을 출력하고 exit 1로 종료한다.
    """
```

동작 순서: ① `kind` 화이트리스트(위 #9) → ② `kind == "memory"`면 history 전용 인자 지정 여부(#3) → ③ `kind == "history"`면 memory 전용 인자 지정 여부(#4·#5) → ④ `kind == "history"`면 정정 필드 최소 1개(#7) → ⑤ `--path` 탈출 가드(#10). `getattr(args, dest, None) is not None`으로 판정한다(모든 필드 인자의 `default=None`, `:1409-1411` + §3.1.2).

> 게이트가 **락 밖**에 있으므로 거부 시 `MEMORY.json`·`.lock`·`.tmp`에 단 한 번도 접근하지 않는다 → R-4 AC(a)를 구조적으로 보장(테스트로 재확인: TS-016).

#### 3.3.3 환경 변경 / 3.3.4 배치·마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-3 (a) | 기능 테스트 | `--kind history --status dead` → `ok:false`·`error:"invalid_args"`, `message`에 `--status` 사유, 파일 바이트 불변 |
| TS-012 | R-3 (a), P-2 | 기능 테스트 | `--kind history --summary "x"` → `ok:false`·`invalid_args`, `message`가 `--result`를 안내, 파일 불변 |
| TS-013 | R-3 (b) | 기능 테스트 | `--kind memory --stage x` / `--result x` / `--path x` 3케이스 각각 `ok:false`·`invalid_args`, 파일 불변 |
| TS-014 | R-3 (c) | 기능 테스트 | 존재하지 않는 히스토리 제목 + `--kind history --stage x` → `ok:false`·`error:"row_not_found"`, 파일 불변, `.lock` 잔여 0 |
| TS-015 | R-3 (d) | 기능 테스트 | `--kind history` + 정정 필드 0개 → `ok:false`·`invalid_args`, 파일 불변 |
| TS-027 | 보안(#10) | 보안 테스트 | `--kind history --path "../../etc/"` → `ok:false`·`invalid_args`, 파일 불변 |
| TS-028 | P-3 | 산출물 검사 | `ERROR_CODES` 키 집합이 23종 그대로(신규 코드 0) + `invalid_kind`·`invalid_args` 템플릿 무변경 |

---

### F-004: 문서·배포 반영 + 실사용 검증

#### 3.4.1 파일 변경 계획

**신규 생성**: 없음.

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/memory-tool/README.md` | 문서 | §`update` 절 전면 개정(usage + 조합 규칙 표 + 대상 판별 정책 + 에러 목록) + §변경이력 `v2.1` 행 | `README.md:89-101`, `:285-291` |
| 2 | `opal/core/references/tools.md` | 문서 | §memory-tool `update` 커맨드 블록 + 에러코드 표에 `invalid_kind` 행 + 변경이력 `v2.7` 행 (**Edit 전용·헤딩 앵커**) | `tools.md:605-607`, `:654~`, `:880` |
| 3 | `opal/core/references/harness/memory-learning.md` | 문서 | §정리 불릿에 **1줄** 추가 + 변경이력 `v1.3` 1행 (신규 절·표 금지) | `memory-learning.md:22`, `:81` |
| 4 | `.opal/MEMORY.json` | 배치 | 배포본 CLI로 078 히스토리 `stage` 정정(도구 경유) | `TASK.md` R-5 AC(b) |

#### 3.4.2 문서 설계 — **P-7 결정: 3문서 역할 분담 + 서술 상한**

| 문서 | 역할 | 쓸 내용 | 분량 상한 |
|------|------|---------|----------|
| `README.md` §`update` | memory-tool **계약 상세 SSOT** | ① usage 블록에 `--kind {memory,history}` + `--stage`/`--result`/`--path` 추가 ② P-2 조합 규칙 표(10행 중 대표 7행) ③ 대상 판별 정책 1줄 — "동일 `title` 복수 시 **배열 선행 1건**(= 가장 최근 append). 배열 순서는 **비-brief `show`의 `history_rows` 순서**이며 `--brief`는 `date` 재정렬이므로 대상 판별 기준이 아니다" ④ FIFO 미적용·행 수 불변 1줄 ⑤ 에러 목록에 `invalid_kind`·`invalid_args` 추가 | 기존 13줄 → **≤45줄** |
| `tools.md` §memory-tool | **도구 인벤토리**(시그니처 수준) | ① `update` 커맨드 블록에 `[--kind {memory,history}] [--stage <단계>] [--result <핵심결과>] [--path <경로>] # history 전용` ② 주석 1줄 "히스토리 오기재 정정 — 행 추가·삭제 없음, 상세는 README §update" ③ 에러코드 표에 `invalid_kind` 행 추가 ④ §용도 1줄에 "히스토리 오기재 정정(update --kind history)" 삽입 | **≤8줄 순증** |
| `memory-learning.md` | 메모리 형식·라이프사이클 **SSOT(부트스트랩 로드)** | §정리 FIFO 불릿(`:22`) **바로 아래 1줄**: "히스토리 **오기재는 삭제가 아니라 정정** [MUST] — `update --kind history`로 `stage`/`result`/`path`/`title`을 고친다(행 수 불변). 조합 규칙·대상 판별은 `opal/tools/memory-tool/README.md` §update 참조." | **1줄 + 변경이력 1행 = 총 ≤84줄** |

> **[MUST] `memory-learning.md`에 신규 절(`##`)·신규 표를 추가하지 않는다.** 078이 81줄로 슬림화한 부트스트랩 문서다 — 상세는 README 포인터로 위임하고 본문은 1줄만 늘린다. 최종 줄 수 **84줄 이하**를 게이트로 검증한다(TS-023). (H-5)

> **[MUST] `tools.md`는 `Edit` 전용·헤딩 앵커 편집.** [MUST] `TASK.md` §제약 조건: "**동시 태스크 주의** — 077이 같은 워킹트리에서 진행 중일 수 있다. 공유 파일(`tools.md`)은 `Edit` 전용·헤딩 앵커로 편집한다." → `Write`로 전문 재작성 금지, `## memory-tool` 헤딩 이후 구간만 국소 `Edit`, 작업 전후 `git diff -- opal/core/references/tools.md`로 code-scan 절(`:879` v2.5 관련 구간) 무변경 확인. (H-9)

> **`--help` ↔ 문서 정합 [MUST]**: 078 §5 결함 6("CLI `--help`가 실제 동작과 반대")의 재발 방지 — 문서 usage 블록은 **구현 완료 후 실제 `update --help` 출력과 대조**하여 작성한다(§4.3 Phase 순차 근거).

**구형 서술 제거 대상**(R-5 AC a "구형 서술 잔존 0") — 3문서 grep 체크:
- "히스토리는 정정 불가" / "되돌릴 수 없" / "손편집" 류 서술: 현재 3문서에 **없음**(실측) → 신규로 만들지 않는 것으로 충족. `TASK.md` 배경의 서술은 태스크 문서이므로 대상 아님.
- `README.md:89` 헤딩 `### \`update\` — 상태/요약 수정` → `### \`update\` — 메모리 상태/요약 수정 + 히스토리 정정`으로 갱신(구형 범위 서술 정정).
- `tools.md:604` 주석 `# 메모리 상태/요약/제목 수정 (라이프사이클 전이…)` → 히스토리 정정 포함으로 갱신.

#### 3.4.3 환경 변경

`scripts/install-mac.sh` 실행으로 `~/.opal/` 배포. [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." → 어떤 Step도 `~/.opal/` 파일을 직접 편집하지 않는다.

#### 3.4.4 배치/마이그레이션 — 실사용 검증 절차 (R-5 AC b)

1. `scripts/install-mac.sh` 실행 → 배포 성공 확인.
2. 사전 안전장치: `git status --short .opal/MEMORY.json` 및 현재 값 스냅샷(`~/.opal/tools/memory-tool/run.sh show --file .opal/MEMORY.json`)으로 배열 순서·`stage` 실측.
3. **배포본 CLI**로 정정:
   ```bash
   ~/.opal/tools/memory-tool/run.sh update --file .opal/MEMORY.json \
     --kind history --title "078 메모리 SSOT JSON 전환" \
     --stage "완료·커밋(d7a8ce0, 447ff09)"
   ```
   (현행 실측: index0 = `title="078 메모리 SSOT JSON 전환"`, `stage="완료·미커밋"`)
4. 응답 검증: `ok:true`·`kind:"history"`·`match_count:1`·`matched_index:0`·`history_count:5`·`changed:["stage"]`.
5. `run.sh show --file .opal/MEMORY.json --brief`로 반영 확인 + `git diff .opal/MEMORY.json`이 **해당 1행 `stage` 한 필드만** 변경했음을 확인(H-10).

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-021 | R-5 (a) | 산출물 검사 | 3문서에 `--kind history` 표기 존재 + "정정 불가"/"되돌릴 수 없" 류 서술 0건(grep) |
| TS-022 | R-5 (a), H-9 | 산출물 검사 | `tools.md` `update` 블록에 `--kind`·`--stage`·`--result`·`--path` 존재 + 에러코드 표에 `invalid_kind` 행 존재 + `git diff`상 code-scan 절 무변경 |
| TS-023 | R-5 (a), H-5 | 산출물 검사 | `wc -l memory-learning.md` ≤ 84, 신규 `##` 헤딩 0건, 신규 표 0건 |
| TS-024 | R-5 (b) | 통합 테스트(실환경) | install 후 배포본 CLI로 078 `stage` 정정 성공 + `show --brief`에 `완료·커밋(d7a8ce0, 447ff09)` 반영 + `git diff`가 1행 1필드만 변경 |
| TS-029 | R-5 (a) | 산출물 검사 | 문서 usage 블록의 인자 목록이 실제 `update --help` 출력과 일치(누락·잉여 0) |
| TS-030 | 제약 | 산출물 검사 | 변경 3문서에 변경이력 행 추가(`README.md` v2.1 / `tools.md` v2.7 / `memory-learning.md` v1.3), KST 일시 포함 (→ D-9 §변경이력 작성 의무) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001~F-004(코드 AC) | 1 | `opal-test-agent` (mode: red) | 단독 | **RED-first [MUST]** — 실패 증거 확보 후 GREEN 진입. 작성자≠구현자(§P-6) |
| 2 | F-001, F-002, F-003 | 2 | `opal-be-agent` | 단독 | `memory_tool.py` **단일 파일** — 3기능이 같은 함수를 고치므로 1 Step·1 에이전트 순차 (파일 충돌 방지) |
| 3 | F-004 | 3, 4 | `opal-task-agent` ×2 | **병렬 가능** | 서로 다른 파일(README.md ↔ tools.md+memory-learning.md). Phase 2 완료 후 진입(`--help` 대조 필요) |
| 4 | F-004 | 5 | **PM 직접** | 단독 | install 배포 + 실 `.opal/MEMORY.json` 정정 — **비가역** 작업이므로 PM이 직접 수행·확인 (H-10) |

**docs/ 갱신 Step 판정: 해당 없음.** `docs/PROJECT.md:170`·`docs/ARCHITECTURE.md:82`는 memory-tool을 역할 수준으로만 서술하고 서브명령 인자를 다루지 않으며, 이 태스크는 새 API 엔드포인트·컴포넌트·시스템 구조 변경·신규 컨벤션 도입에 해당하지 않는다 → docs/ 갱신 Step을 생성하지 않는다(§5.3에서 판정 재확인).

### 4.2 실행 체크리스트

> 총 **5개** Step | Phase **4개** | 실행 모드: **복잡**

#### Step 1: RED 테스트 작성 — `update --kind history` 계약 전량

- [ ] 완료
- **소속 기능**: F-001, F-002, F-003, F-004(코드 검증 가능 AC)
- **영역**: BE
- **agent**: `opal-test-agent` (mode: red)
- **파일**: `opal/tools/memory-tool/tests/test_memory_tool.py`
- **작업 내용**:
  - 신규 클래스 4종 추가 — `TestUpdateKindHistory`(TS-003, TS-005~TS-010, TS-018, TS-020), `TestUpdateKindArgGuard`(TS-004, TS-011~TS-015, TS-027, TS-028), `TestUpdateHistoryLossless`(TS-016, TS-017), `TestUpdateBackCompat`(TS-001, TS-002, TS-019, TS-025).
  - 테스트 프리픽스 `[T079/...]`, 픽스처는 **기존 `fixture_doc_populated.json`** 을 `shutil.copy2` 후 in-test JSON 가공으로 6행·중복 title 케이스 구성(신규 픽스처 파일 신설 금지 — 자산 증가 억제).
  - 헬퍼 `_run`/`_run_raw`/`_setup_populated`(`tests/test_memory_tool.py:57-113`) 재사용. [MUST] mock/patch/MagicMock 금지 — 실 프로세스(subprocess)·실 파일만(`tests/test_memory_tool.py:6` @header).
  - TS-004는 **exit code와 stdout JSON을 동시 단정**(`_run_raw` 사용) — argparse exit 2 회귀를 잡는 유일한 케이스(H-8).
  - TS-016은 정정 전 `MEMORY.json` 바이트·mtime을 캡처하고 거부 후 동일성 + `glob("*.tmp*")`·`MEMORY.json.lock` 부재를 단정.
  - `@header.exports`에 신규 클래스 4종 등재 + 변경이력 `v1.2` 행 추가.
- **완료 기준**: 신규 케이스 전량 **FAIL**(RED 증거, exit≠0)이고 **기존 132건은 GREEN 유지**. 두 집계를 실행 로그로 보고.
- **테스트**: 자기 자신(RED 증거). `python -m unittest opal.tools.memory-tool.tests.test_memory_tool` 또는 `~/.opal/.venv/bin/python -m unittest discover -s opal/tools/memory-tool/tests`
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: `cmd_update` `--kind` 분기 구현 (GREEN)

- [ ] 완료
- **소속 기능**: F-001, F-002, F-003
- **영역**: BE
- **agent**: `opal-be-agent`
- **파일**: `opal/tools/memory-tool/memory_tool.py` (단일 파일)
- **작업 내용**:
  - `main()` `p_update`에 `--kind`(default `"memory"`, **`choices=` 금지**, `metavar="{memory,history}"`)·`--stage`·`--result`·`--path` 추가 (§3.1.2).
  - `_check_update_kind_args(kind, args)` 신설 — P-2 표 10행 전량, `invalid_kind`/`invalid_args` **재사용**(신규 에러코드 0), `--path` 탈출은 기존 `_path_has_traversal`(`:816`) 재사용. **`memory_lock` 진입 전**에 호출.
  - `_apply_history_correction(doc, title, args)` 신설 — `matches[0]` 대상 선정, 4필드 in-place 치환, `(target, idx, match_count, changed)` 반환. **부가 키 삽입 금지**, **`_enforce_history_fifo` 호출 금지**.
  - `cmd_update`를 `kind` 2분기로 재편 — 기존 memory 블록(`:1011-1035`)은 **로직 무변경 이식**. `validate_document`→`atomic_write_json`→`build_review_block` 골격 공유.
  - 응답: memory 경로에 `kind` additive 추가(기존 키 전량 보존), history 경로에 `matched_index`/`match_count`/`changed`/`history_count`.
  - `@header.description`에 `update --kind history` 반영 + 변경이력 `v2.1 2026-07-30 …(079)` 행 추가 (→ D-9 §@header 규칙·§변경이력 작성 의무).
- **완료 기준**: 신규 TS 전량 GREEN + **기존 132건 GREEN**(총 GREEN, FAIL 0). `ERROR_CODES` 키 수 23 불변. `git diff`에 `memory_tool.py` 외 코드 파일 변경 0. [MUST] `TASK.md` §제약: 표준 라이브러리 외 import 0.
- **테스트**: TS-001~TS-020, TS-025, TS-027, TS-028 / 전 스위트 `unittest` 실행
- **실행 방법**: sub-agent
- **의존**: Step 1 (RED 증거 확보 — `red-first.md` §1 [MUST])

#### Step 3: `README.md` §`update` 절 개정

- [ ] 완료
- **소속 기능**: F-004
- **영역**: 문서
- **agent**: `opal-task-agent`
- **파일**: `opal/tools/memory-tool/README.md`
- **작업 내용**:
  - `### \`update\`` 헤딩 제목을 "메모리 상태/요약 수정 + 히스토리 정정"으로 갱신.
  - usage 블록에 `[--kind {memory,history}]`·`[--stage …]`·`[--result …]`·`[--path …]` 추가하고 **실제 `update --help` 출력과 대조**(TS-029).
  - P-2 조합 규칙 표 삽입(허용/거부 + 에러코드), 대상 판별 정책 1줄(배열 선행 1건 = 최근 append, `--brief`는 `date` 재정렬이므로 기준 아님), FIFO 미적용·행 수 불변 1줄.
  - 에러 목록에 `invalid_kind`·`invalid_args` 추가. §에러 코드 표 `invalid_kind` 설명을 `append`/`update` 공용으로 정정.
  - §변경이력에 `v2.1 | 079 | …` 행 추가.
- **완료 기준**: TS-021·TS-029·TS-030 통과. §`update` 절 ≤45줄. `--help` 대조 결과를 보고에 첨부.
- **테스트**: TS-021, TS-029, TS-030
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: 참조 문서 2건 개정 (`tools.md` + `memory-learning.md`)

- [ ] 완료
- **소속 기능**: F-004
- **영역**: 문서
- **agent**: `opal-task-agent`
- **파일**: `opal/core/references/tools.md`, `opal/core/references/harness/memory-learning.md`
- **작업 내용**:
  - **`tools.md`** — [MUST] `Edit` **전용**·`## memory-tool` 헤딩 앵커 국소 편집(`Write` 금지). `update` 커맨드 블록(`:605-607`)에 history 인자 4종 + 주석 1줄, 에러코드 표에 `invalid_kind` 행, §용도 1줄에 "히스토리 오기재 정정" 삽입, 변경이력 `v2.7` 행. **순증 ≤8줄.** 작업 전후 `git diff -- opal/core/references/tools.md`로 077 소유 code-scan 절 무변경 확인.
  - **`memory-learning.md`** — §정리 FIFO 불릿(`:22`) 바로 아래 **1줄만** 추가(§3.4.2 문안) + 변경이력 `v1.3` 1행. [MUST] 신규 `##` 절·신규 표 추가 금지.
- **완료 기준**: TS-021·TS-022·TS-023·TS-030 통과. `wc -l memory-learning.md` ≤ 84. `tools.md` diff에 code-scan 절 변경 0.
- **테스트**: TS-021, TS-022, TS-023, TS-030
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 5: install 배포 + 실사용 검증 (078 히스토리 `stage` 정정)

- [ ] 완료
- **소속 기능**: F-004
- **영역**: 배치
- **agent**: **PM 직접** (비가역 작업 — 배포 + 실 메모리 변경, H-10)
- **파일**: `scripts/install-mac.sh` 실행, `.opal/MEMORY.json`(도구 경유 변경)
- **작업 내용**: §3.4.4 절차 1~5 — 배포 → 현재 값 스냅샷 → 배포본 CLI로 `--kind history --title "078 메모리 SSOT JSON 전환" --stage "완료·커밋(d7a8ce0, 447ff09)"` → 응답 필드 검증 → `show --brief` + `git diff` 대조.
- **완료 기준**: `ok:true`·`match_count:1`·`history_count:5`·`changed:["stage"]`; `show --brief`에 새 `stage` 반영; `git diff .opal/MEMORY.json`이 **1행 1필드**만 변경. `~/.opal/` 직접 편집 0건.
- **테스트**: TS-024
- **실행 방법**: direct
- **의존**: Step 3, Step 4 (배포는 문서 갱신분까지 함께 나가야 한다 — `~/.opal/core/references/` 배포 대상)

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | [MUST] `red-first.md` §1: "RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입." + §2 작성자≠구현자 |
| Step 2 내부 (F-001·F-002·F-003 합류) | 3기능이 모두 `memory_tool.py` `cmd_update` 동일 함수를 수정 — 분리 시 동일 파일 동시 편집 충돌. 단일 에이전트 순차 처리 |
| Step 2 → Step 3, Step 2 → Step 4 | 문서 usage 블록은 실제 `update --help` 출력과 대조해 작성해야 한다 — 078 §5 결함 6(CLI help ↔ 문서 drift)의 재발 방지 |
| Step 3 ∥ Step 4 | 독립 파일(`README.md` ↔ `tools.md`+`memory-learning.md`), 상호 참조는 경로 문자열 수준(내용 의존 없음) |
| Step 4 내부 (2파일 순차) | 둘 다 참조 문서·동일 에이전트. `tools.md`는 077과 공유하므로 `Edit` 전용 규율을 한 컨텍스트에서 일관 적용 |
| Step 3, Step 4 → Step 5 | install이 `~/.opal/core/references/`·`~/.opal/tools/memory-tool/`를 함께 배포 — 문서 미완 상태 배포 시 R-5 AC(a)와 배포본이 불일치 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | `--kind` 미지정 시 기존 동작·기존 테스트 무변경 | TS-001, TS-002, TS-025 | 기존 132건 GREEN, 필드 0개 update `ok:true` |
| F-001 | `--kind history` 지정 시 히스토리 행 대상 동작 | TS-003, TS-020 | `kind:"history"` + 대상 행 변경 + `review` 첨부 |
| F-001 | `--kind` 이상값 거부가 JSON 계약 준수 | TS-004 | `error:"invalid_kind"`, exit 1, stderr usage/traceback 0 |
| F-001 | `--help` 인자 노출 | TS-019, TS-029 | `--kind`/`--stage`/`--result`/`--path` + `{memory,history}` 노출, 문서와 일치 |
| F-002 | 4필드 개별·복합 정정 | TS-005 | 5케이스 전량 `ok:true`, `changed[]` 정확 |
| F-002 | 미지정 필드 불변 | TS-006 | 대상 행 잔여 필드 + 타 행 전체 바이트 동일 |
| F-002 | 정정 후 스키마 유효 + 키 집합 유지 | TS-007, TS-010 | 재로드 `ok:true`, 키 집합 `{title,date,stage,path,result}` |
| F-002 | 행 수 불변 + FIFO 미적용 | TS-008, TS-009 | 5→5, **6→6**(삭제 0) |
| F-002 | 복수 매치 결정론 | TS-018 | 배열 선행 1건만 변경, `match_count:2` 응답 |
| F-002 | 원자성·락 무손실 | TS-016, TS-017 | 거부 시 바이트·mtime 동일 + `.tmp`/`.lock` 0건; 동시 2프로세스 클로버 0 |
| F-003 | R-3 4거부 케이스 전수 | TS-011~TS-015 | 4케이스 전량 `ok:false` + 파일 불변 |
| F-003 | 신규 에러코드 0 (재사용 확인) | TS-028 | `ERROR_CODES` 23종 불변, 템플릿 무변경 |
| F-003 | `--path` 탈출 차단 | TS-027 | `..` 포함 시 `invalid_args`, 파일 불변 |
| F-004 | 3문서 구형 서술 0 + 신형 채택 | TS-021, TS-022 | grep 결과 0건 + `--kind history` 표기 3문서 존재 |
| F-004 | `memory-learning.md` 재비대화 방지 | TS-023 | ≤84줄, 신규 절·표 0 |
| F-004 | 배포 후 실사용 검증 | TS-024 | 078 `stage` 정정 반영 + `git diff` 1행 1필드 |
| F-004 | 변경이력 갱신 | TS-030 | 3문서 + `memory_tool.py` + 테스트 파일 변경이력 행 존재 |

### 5.2 회귀 테스트

- [ ] `~/.opal/.venv/bin/python -m unittest discover -s opal/tools/memory-tool/tests` — **기존 132건 전량 GREEN**, FAIL 0 (H-1)
- [ ] `update --title X --status dead` / `--summary` / `--new-title` 기존 3경로 무변경 동작 (`tests/test_memory_tool.py:1338`, `:1358` 회귀 단정 포함)
- [ ] `append --kind history` 동작 무변경 — `--summary`→`result` 매핑(`memory_tool.py:967`)·`choices=`(`:1395`) 손대지 않음
- [ ] `prune` / `show --brief` / `review` / `task-number` 무영향 (`ERROR_CODES`·스키마 무변경)
- [ ] `dashboard/backend/parsers/memory_parser.py` 무영향 — 히스토리 행 수·키 집합 불변
- [ ] `improve-tool record --scope local`(memory-tool `append` 위임, `tools.md:764`) 무영향
- [ ] `tools.md` 077 소유 code-scan 절 무변경 (`git diff` 확인, H-9)

### 5.3 코드/문서 품질

- [ ] [MUST] `memory_tool.py` @header(`:6`): "표준 라이브러리만." — 신규 import 0
- [ ] [MUST] `docs/CONVENTIONS.md` §@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다" — `memory_tool.py`·테스트 파일 @header 갱신
- [ ] [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다" — `tools.md` v2.7 / `memory-learning.md` v1.3 / `README.md` v2.1, KST 일시 포함
- [ ] [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지" — 전 Step에서 `~/.opal/` 파일 직접 편집 0건, 배포는 Step 5 install 단독
- [ ] [MUST] `TASK.md` §제약 조건: 응답은 `{"ok": …}` 단일라인 JSON, traceback 금지 — 신규 경로 전량 확인(TS-004 포함)
- [ ] 비범위 침범 0 — `delete --kind history` 미신설 / 히스토리 스키마 무변경(`schema/memory.schema.json` diff 0) / 타 서브명령 `--kind` 미변경
- [ ] docs/ 갱신 판정 재확인 — `docs/PROJECT.md`·`docs/ARCHITECTURE.md`가 서브명령 인자를 서술하지 않음을 grep으로 확인, 갱신 불필요 결론 유지
- [ ] `_enforce_history_fifo` 호출부 grep — `cmd_update` 경로에 등장 0건 (P-5 [MUST])

### 5.4 보안

- [ ] `--path` 값의 `..` 탈출 차단 — 기존 `_path_has_traversal`(`memory_tool.py:816-818`) 재사용, TS-027 (신규 가드 함수 0)
- [ ] `--kind`/`--stage`/`--result` 값이 파일 경로·셸로 흘러가지 않음 확인(전부 JSON 문서 필드 값으로만 소비)
- [ ] 코드·문서·테스트에 하드코딩 토큰/시크릿 0 (`tests/test_memory_tool.py:974` `test_no_hardcoded_secrets_in_tool` 유지)
- [ ] 거부 경로에서 `.lock`·`.tmp` 잔여 0건 — 락 파일 누수로 인한 후속 명령 DoS 방지 (TS-016)
- [ ] 에러 메시지에 절대경로·환경정보 과다 노출 없음(기존 `err()` 템플릿 재사용으로 상속)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 5개 | 단순 |
| 변경 파일 수 | 5개 (`memory_tool.py`, `test_memory_tool.py`, `README.md`, `tools.md`, `memory-learning.md`) | **복잡** |
| 모듈 범위 | 다중 (도구 코드 + 테스트 + 참조 문서 2 + 배포) | **복잡** |
| 작업 유형 | 기존 서브명령의 계약 확장(개선) + 하위호환 [MUST] | 단순 |
| 외부 의존성 | 없음(표준 라이브러리, 신규 패키지·MCP 0) | 단순 |
| **실행 모드** | **복잡** | 2기준 해당 → 복잡 모드 적용, §7 포함 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1:  [opal-test-agent (mode: red)]        Step 1  — tests/test_memory_tool.py
             │ (RED 증거 = exit≠0)
Batch 2:  [opal-be-agent]                      Step 2  — memory_tool.py (단일 파일)
             │
Batch 3:  [opal-task-agent A] ∥ [opal-task-agent B]
             │  Step 3            Step 4
             │  README.md         tools.md + memory-learning.md
Batch 4:  [PM 직접]                            Step 5  — install + 실사용 검증
```

**그룹핑 근거**:
1. **파일 충돌 방지** — `memory_tool.py`를 만지는 Step은 Step 2 하나뿐(F-001·F-002·F-003 합류). `tests/test_memory_tool.py`는 Step 1 전용.
2. **모듈 응집도** — 참조 문서 2건을 하나의 에이전트(B)에 묶어 `Edit` 전용 규율(H-9)을 단일 컨텍스트에서 일관 적용.
3. **병렬 극대화** — Batch 3의 두 에이전트는 파일 교집합 0.
4. **검증 2원화** — RED 작성(`opal-test-agent`) ≠ 구현(`opal-be-agent`) ([MUST] `red-first.md` §2). 비가역 배포·실데이터 변경은 PM이 직접 수행하여 워커 자율 실행에서 제외.

### C-2. 스킬 요구사항

| Step | 스킬 | 갭 |
|------|------|----|
| 1 | `op-dev-execute` + `red-first.md` (RED 트랙 규칙) | 없음 |
| 2 | `op-dev-execute` | 없음 |
| 3, 4 | `op-dev-execute` (문서 편집) | 없음 — 신규 스킬 후보 아님(동일 패턴 Step 2개, 임계 N=3 미달) |
| 5 | 없음(PM 직접 CLI) | 없음 |

### C-3. 도구 요구사항

- `~/.opal/.venv/bin/python` (표준 라이브러리) — 기존.
- `scripts/install-mac.sh` — 기존 배포 스크립트.
- 신규 CLI·MCP·패키지 **0건**. context7/shadcn MCP 미사용(Python stdlib CLI 태스크, FE 없음).

### C-4. 테스트 전략 — **P-6 RED-first 판정**

**판정: RED-first 트랙 강제 (코드 Step)** — [MUST] `red-first.md` §1.5 "RED-first 강제" 목록의 **"API 계약"** 및 **"버그 수정(회귀 방지)"** 에 해당한다. 이 태스크는 CLI 인자 계약·에러코드 계약을 확장하며, 핵심 요구가 "기존 132건 무변경 통과"라는 회귀 방지다. 모호 판정 시 안전측(RED-first) 규칙도 같은 결론.

**문서 Step(3·4)**: `red-first.md` §1.5 "구현 후 시나리오 검증 허용" 목록의 **"설정·문서"** → 산출물 검사(TS-021~TS-023, TS-029, TS-030)로 사후 검증. 단 공통 불변 3항(테스트 코드 산출물·작성자≠구현자·TEST 단계 검증)은 유지된다.

**state-tool 연동**: RED-first 트랙 → `verify --red-check` **ON**.

**불변 규율**: [MUST] `red-first.md` §3: "GREEN/fix 루핑 중 RED 테스트 파일 수정 금지. 위반 시 블로커." → Step 2 에이전트는 `tests/test_memory_tool.py`를 **수정하지 않는다**(단정 약화·조건 완화 금지). @header/변경이력 갱신도 Step 1 담당.

**검증 계층**:

| 계층 | 대상 | 명령 |
|------|------|------|
| L1 (단위/CLI) | TS-001~TS-020, TS-025, TS-027~TS-030 | `~/.opal/.venv/bin/python -m unittest discover -s opal/tools/memory-tool/tests -v` |
| L2 (동시성·실파일) | TS-016, TS-017 | 동일 스위트 내 subprocess 2프로세스 케이스 |
| L3 (실환경 1회) | TS-024 | 배포본 `run.sh update --kind history` + `show --brief` + `git diff` |

**회귀 기준선**: 현행 `tests/test_memory_tool.py` 테스트 메서드 132건(실측 `grep -c "    def test"`). Step 2 완료 시 132 + 신규 케이스 전량 GREEN.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| BE | Python 3 표준 라이브러리 (`argparse`/`json`/`pathlib`/`os`/`re`/`time`) | `trailofbits/modern-python` **미설치**(`~/.opal/community-skills/`에 `obra`만 존재) — 또한 [MUST] `memory_tool.py` @header: "표준 라이브러리만."이므로 uv/ruff/외부 패키지 권고는 이 태스크에 부적합 → 미적용 |
| BE(테스트) | `unittest` + `subprocess` 실프로세스 | mock/patch 금지(헌법 §4, `tests/test_memory_tool.py:6`) |
| 문서 | 마크다운 (README·참조 문서) | — |
| FE | **없음** | ui-designer/shadcn 미해당 |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| context7 | **미사용** — 외부 라이브러리 0(표준 라이브러리 전용). 최신 API 문서 조회 불필요 |
| shadcn MCP | **미사용** — FE 화면 없음 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | memory_tool.py | `opal/tools/memory-tool/memory_tool.py` | `cmd_update`(:998-1045)·`cmd_append` kind 분기 선례(:924-991)·`ERROR_CODES`(:121-146)·`memory_lock`(:360-405)·`atomic_write_json`(:334-353)·`_enforce_history_fifo`(:774-778)·`build_review_block`(:825-878)·argparse(:1378-1464) |
| D-2 | 소스 | 문서 스키마 | `opal/tools/memory-tool/schema/memory.schema.json` | `$defs.historyRow`(:69-97) 필드·`additionalProperties:false`(:71)·`history` maxItems 부재(:25-29)·`x-constants.HISTORY_FIFO_LIMIT`(:100) |
| D-3 | 소스 | memory-tool 테스트 | `opal/tools/memory-tool/tests/test_memory_tool.py` | 132건 회귀 기준선, 헬퍼(:57-113), `update` 기존 케이스(:602-676, :1267-1379), show 행 strict 단정(:1984, :2055) |
| D-4 | 기획 | TASK.md (079) | `tasks/079-260730-opds-히스토리-정정명령/TASK.md` | R-1~R-5 요구사항·AC·제약 조건 원문 |
| D-5 | 기획 | 078 완료 보고 | `tasks/078-260728-opd-메모리-json전환/DONE.md` | §5 발견 결함(6: CLI help ↔ 문서 drift)·§7 잔여·§8 운영 규율(077 공유 파일 `Edit` 전용, 검증 2원화) |
| D-6 | 설계 | 메모리 형식·라이프사이클 SSOT | `opal/core/references/harness/memory-learning.md` | FIFO 불릿(:22)·`delete` 무손실 가드 블록·81줄 현황(H-5 게이트 기준) |
| D-7 | 설계 | 도구 인벤토리 | `opal/core/references/tools.md` | §memory-tool(:580-660) `update` 블록(:605-607)·에러코드 표·077 공유 파일 |
| D-8 | 소스 | memory-tool README | `opal/tools/memory-tool/README.md` | §`update`(:89-101) 계약 상세·§에러 코드 표(:253-283)·§변경이력(:285-291) |
| D-9 | 설계 | 프로젝트 컨벤션 | `docs/CONVENTIONS.md` | §@header 규칙(:171-175)·§변경이력 작성 의무(:197-201)·§네이밍 규칙(:14-22) |
| D-10 | 설계 | RED-first 트랙 SSOT | `opal/core/references/harness/red-first.md` | §1 RED→GREEN 순서·§1.5 트랙 판정(API 계약/회귀 방지)·§2 작성자≠구현자·§3 테스트 불변성 |
| D-11 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | §2 인용 포맷·§2.4 [MUST] 포맷·§4 PLAN 단계 의무 수준 |
| D-12 | 설계 | 프로젝트 정의·아키텍처 | `docs/PROJECT.md`, `docs/ARCHITECTURE.md` | docs/ 갱신 필요 여부 판정(:170 / :82 — 서브명령 인자 미서술 → 갱신 불필요) |
| D-13 | 소스 | 실 메모리 문서 | `.opal/MEMORY.json` | R-5 AC(b) 실사용 대상 현황 실측(078 행 index0, `stage="완료·미커밋"`) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | `--kind` 도입이 기존 132건을 회귀시킨다 (H-1) | F-001 | P0 | `default="memory"` + 기존 memory 블록 **로직 무변경 이식** + 응답 키 additive만. Step 1 RED에 하위호환 클래스(TS-001·TS-002) 선배치, Step 2 완료 기준에 "132건 GREEN" 명시 |
| R-2 | 조합 오용이 silent no-op으로 흘러 오기재가 영속화 (H-2) | F-003 | P0 | P-2 표 10행을 **락 밖 사전 게이트**로 전량 명시 거부. `invalid_args` + `detail` 사유 문자열. TS-011~TS-015로 4거부 케이스 전수 |
| R-3 | 동일 title 복수 행에서 의도와 다른 행을 정정 (H-3) | F-002 | P1 | 배열 선행 1건 결정론 정책 + `matched_index`/`match_count` 응답 노출 + 문서에 "판별 기준은 비-brief `show` 배열 순서, `--brief`는 `date` 재정렬" 명시. 삭제 없음 → 되정정 가능 |
| R-4 | 새 쓰기 경로·락 누수로 원자성 회귀 (H-4) | F-002 | P0 | `memory_lock`/`atomic_write_json`/`validate_document` **재사용만**. 조합 거부는 락 밖. TS-016(바이트·mtime·잔여파일)·TS-017(동시 2프로세스) |
| R-5 | FIFO 재적용으로 >5행 문서에서 조용한 삭제 (H-6) | F-002 | P0 | [MUST] `_enforce_history_fifo` 호출 금지. TS-009(6행→6행) + §5.3 grep 체크 |
| R-6 | 부가 키 삽입으로 스키마·show 계약 위반 (H-7) | F-002 | P1 | `additionalProperties:false` [MUST] 명시, 정정 이력은 git 위임. TS-010 키 집합 단정 |
| R-7 | `choices=` 무비판 복사로 응답 계약 파괴 (H-8) | F-001 | P1 | `choices=` 금지 [MUST] + `metavar` 대체. TS-004가 exit code·stdout JSON 동시 단정 |
| R-8 | `memory-learning.md` 재비대화 (H-5) | F-004 | P1 | 1줄 + 변경이력 1행만, 신규 절·표 금지 [MUST], ≤84줄 게이트(TS-023) |
| R-9 | 077과 `tools.md` 상호 클로버 (H-9) | F-004 | P1 | `Edit` 전용·헤딩 앵커 국소 편집, 작업 전후 `git diff`로 code-scan 절 무변경 확인(TS-022) |
| R-10 | 비가역 배포·실데이터 오조작 (H-10) | F-004 | P1 | Step 5를 **PM 직접**으로 격리, 사전 `show` 스냅샷 → 정정 → `show --brief` + `git diff` 1행 1필드 확인(TS-024) |
| R-11 | 용어 불일치 — 히스토리 핵심결과를 `append`는 `--summary`, `update`는 `--result`로 받는다 | F-003 | P2 | 스키마 필드명(`result`)을 신규 표면의 SSOT로 채택하고 거부 메시지로 안내(P-2 근거 3). `append` 변경은 비범위 — **후속 개선 후보로 DONE.md에 기록**(계약 파괴 위험이 있으므로 이 태스크에서 통일하지 않음) |
