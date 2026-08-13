# PLAN: state-tool task-step 키 주소 체계 도입 1차 — pipeline.json 표준화 + 그룹 A 전환

> 작성일: 2026-07-20 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (기능 7종)
> 실행 모드: 복잡 (§6 판별)

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

state-tool의 행 주소를 "불안정한 순번(`--row N`)" 의존에서 "SKILL.md 참조 JSON 스펙에 선언된 task-step key(`plan.pm_gate`)" 체계로 개선한다. 1차 범위: ① pipeline-spec 스키마 신설 + `spec-validate` 서브명령, ② state-tool 코어 확장(`--task-step`/`--task-step-id`/`--action-step`, `.json` 스펙 로딩, add-row `--key`), ③ state.json 스키마 1.1(rows[].key·conditional), ④ 그룹 A 표준형 4종(opp/opd/opds/opdw) `pipeline.json` 생성 + SKILL.md 전환, ⑤ opdd enum 드리프트 정정. 하위호환(--row·--step 별칭·.md 파싱·레거시 state.json)을 전 구간 유지한다 (→ D-8 TASK §제약).

### 1.2 PLAN에서 확정한 3대 위임 결정 (ANALYSIS 위임 → 본 PLAN 확정)

> ANALYSIS §5 R-A7 / §4 #2·#4가 PLAN 단계로 넘긴 3건을 여기서 잠근다. 하위 설계는 이 결정을 따른다.

| # | 결정 사항 | 확정값 | 근거 |
|---|----------|--------|------|
| DEC-1 | `conditional` 필드 런타임 의미 | **순수 메타데이터**. pipeline.json task_step에 `conditional:true` 선언, `build_rows_from_pipeline_json`이 state.json rows[].conditional로 **저장만** 하고 **자동 na 마킹은 하지 않는다**. opdw "#3-#5 `-` 표기"는 현행 문서 관례로 유지(코드 자동화 없음) | (→ D-1 §5 R-A7), (→ D-1 §4 #4). Simplicity First — 자동화는 dynamic_rows 범위(2차) |
| DEC-2 | `spec-validate` 검증 방식 | **jsonschema 패키지 없이 수작업 검증 함수**(`validate_pipeline_spec`). `pipeline-spec.schema.json`은 **문서 SSOT**로만 기능하고 런타임 검증은 `cmd_validate` 관례(하드코딩 필드/enum 체크)를 따른다 | (→ D-1 §4 #2), (→ D-1 §1.3). 표준 라이브러리만 허용(TASK 기술스택) — 코드베이스 정합 |
| DEC-3 | 테스트 실행기 | **unittest 표준**(T-11). 기본 실행: `~/.opal/.venv/bin/python -m unittest discover -s opal/tools/state-tool/tests -p 'test_*.py'`. pytest 설치 시 `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/`도 호환(unittest 스타일 수집 가능) | (→ D-1 §1.4), (→ D-1 §5 R-A6). `test_state_tool.py:19` [MUST] T-11 표준 라이브러리만 |

### 1.3 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | pipeline-spec 스키마 신설 + spec-validate 서브명령 | R-1, R-6 | P0 | 없음 |
| F-002 | init `.json` 스펙 로딩 + state.json 스키마 1.1(key·conditional) | R-2, R-3 | P0 | F-001 |
| F-003 | 행 주소 플래그 신설(`--task-step`/`--task-step-id`) + `--step`→`--action-step` | R-4, R-5 | P0 | F-002 |
| F-004 | add-row `--key` 지원(자동 생성·유일성) | R-9 | P1 | F-002, F-003 |
| F-005 | opdd 드리프트 정정(skill·stage enum 등록) | R-8 | P1 | 없음 |
| F-006 | 그룹 A 4종 pipeline.json 생성 + SKILL.md 전환 | R-7 | P0 | F-001, F-002 |
| F-007 | 테스트 보강(신규 케이스 + 회귀) | R-10 | P0 | F-001~F-006 |

### 1.4 기능 의존 그래프 (ASCII)

```
F-001 ─┬─ F-002 ─┬─ F-003 ─── F-004 ─┐
       │         │                    ├─ F-007
       └─────────┴─ F-006 ────────────┤
F-005 ───────────────────────────────┘
```

- F-001(스키마+검증)이 F-002(로딩)·F-006(스펙 저작)의 선행. F-005(enum)는 독립.

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력. ANALYSIS §5 R-A1~R-A7 반영. 각 가설은 검증 가능한 형태로 기술한다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `resolve_row_index` (F-003) — `find_row_index` 대체 | `--row` deprecated 별칭이 기존과 동일 row_index 산출 실패 → 엉뚱한 행 갱신 | P0 | L1(단위) + L2(subprocess CLI) 의무 | 동일 행을 `--task-step`/`--task-step-id`/`--row` 3방식으로 mark → 동일 결과 |
| H-2 | argparse `--row` required 해제 (F-003) | 주소 플래그 0개/2개 처리 — 기존 required=True가 하던 필수 강제가 사라져 무주소 호출이 조용히 통과 | P1 | L2(subprocess — argparse 우회 불가) | 주소 0개 → `task_step_addr_required`, 2개 → `task_step_addr_conflict` (→ D-1 §5 R-A4) |
| H-3 | state.schema.json `additionalProperties:false` + key/conditional 추가 (F-002) | key 있는 1.1 state.json이 "스키마 위반"으로 읽힘 / 레거시 1.0(key 없음) 검증 실패 | P1 | L1(스키마 대조 단위) | key 있는 1.1 + key 없는 1.0 둘 다 `validate` 통과 (→ D-1 §5 R-A2) |
| H-4 | `build_rows_from_pipeline_json` (F-002) — `.md` 파싱과 병존 | `.json` init 결과 행 수/순서/item이 `.md` 파싱 결과와 불일치 → 파이프라인 구조 변형 | P0 | L1 + L2(실제 init 실증) | opp/opd/opds/opdw json init → 행 수 9/15/10/9 + 전 행 key 존재 (→ D-1 §4 #4) |
| H-5 | add-row 자동 key 생성 (F-004) | 동적 행 자동 key가 기존 동적 행과 충돌 / 재정렬이 기존 key 훼손 | P1 | L1(전체 rows 스캔 유일성) | TEST fix 행 2회 add-row → `test.fix_1`·`test.fix_2`, 기존 key 불변 (→ D-1 §5 R-A3) |
| H-6 | STAGE_ENUM에 `DDL/MIGRATION`(슬래시 포함) 추가 (F-005) | slug 치환 미적용 상태에서 key 형식 검증 시 `/`가 패턴 위반 유발 | P1 | L1 + L2(`init --skill opdd`) | opdd init + DICT add-row가 enum 에러 없이 동작 (→ D-1 §4 #5) |
| H-7 | CLOSE 게이트·명확화 훅 (F-003 무변경 확인) | slug가 `user_confirm`으로 바뀌어도 게이트가 `item=="사용자 확인"`(한글) 의존 유지되는지 | P2 | L1(회귀 — 기존 CLOSE 게이트 테스트) | key 도입 후에도 CLOSE 게이트/명확화 훅 회귀 0 (→ D-1 §5 R-A5) |
| H-8 | 원 설계 SSOT(PLAN 134) 작업트리 부재 (F-006 인용) | D-5 경로 Read 실패로 근거 인용 단절 | P2 | 산출물 검사(인용 유효성) | `git show 4af79ae:...PLAN.md` 조회로 대체 (→ D-1 §5 R-A1) |

---

## 2. 기능별 분석

### F-001: pipeline-spec 스키마 신설 + spec-validate 서브명령

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스키마 | `opal/tools/state-tool/schema/pipeline-spec.schema.json` | 스펙 JSON Schema(Draft-07) 문서 SSOT | 신규 |
| 도구 | `opal/tools/state-tool/state_tool.py` | `validate_pipeline_spec`·`cmd_spec_validate`·argparse 서브파서 | 수정 |

#### 2.1.2 현재 구현
- `state.schema.json`도 `pipeline-spec.schema.json`도 런타임에 실제 JSON Schema 라이브러리로 검증되지 않는다 — 문서 SSOT일 뿐이며 검증은 `cmd_validate`의 수작업 코드로 수행된다 (→ D-1 §4 #2). `state_tool.py:14-23`은 `json/argparse/pathlib/re/subprocess`만 import — 서드파티 없음.
- 응답 계약: `ok(command, **kwargs)` / `err(command, code, ...)` 단일 라인 JSON. `err`는 `ERROR_CODES` 템플릿을 `.format(**kwargs)`로 채운다 (`state_tool.py:121-139`, `:68-103`).
- `cmd_validate`는 violations[]를 모아 `{ok, command, violations, violations_count}` 단일 라인 JSON을 출력하고 `sys.exit(0/1)`한다 (`state_tool.py:1163-1169`) — `spec-validate` 출력 계약의 참조 원형.

#### 2.1.3 영향 범위
- `build_parser()`(`state_tool.py:1788-1924`)에 `spec-validate` 서브파서 1개 추가. 서브명령이 9종→10종.
- `run.sh`는 `exec ... "$@"`로 전 인자를 전달하므로 **무변경**(`run.sh:12`) — ANALYSIS의 "run.sh 라우팅"은 별도 코드 추가 불요, argparse 서브파서 등록만으로 라우팅 완성.
- `validate_pipeline_spec`는 F-002(init 로딩)·F-006(스펙 저작 게이트)이 공유하는 단일 검증 지점.

### F-002: init `.json` 스펙 로딩 + state.json 스키마 1.1

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | `build_rows_from_pipeline_json`·cmd_init 확장자 분기 | 수정 |
| 스키마 | `opal/tools/state-tool/schema/state.schema.json` | rows[].key·conditional 추가, schema_version 1.1 병행 | 수정 |

#### 2.2.2 현재 구현
- 행 주입 3경로: `build_rows_from_spec`(inline JSON, `:470-514`)·`build_rows_from_skill_md`(SKILL.md 4단 regex, `:516-606`)·`parse_existing_state_md`(`:612-644`). 셋 다 `row_id=i+1`, `key` 미생성.
- cmd_init 분기(`state_tool.py:694-701`): `if args.rows_spec: build_rows_from_spec` / `elif args.rows_from: build_rows_from_skill_md`. **여기 `.json` 확장자 분기를 삽입**한다.
- state.schema.json `schema_version`은 `const:"1.0"`(`:22-24`), rows[].items는 `additionalProperties:false`(`:47`) + required 6필드(`:46`).
- agentic 자동 na 규칙: `mode=="agentic" and item=="사용자 확인" and stage!="CLOSE"` → na/auto (`:507-511`, `:599-603`).

#### 2.2.3 영향 범위
- `additionalProperties:false`이므로 rows[]에 key/conditional을 실으려면 **스키마 properties에 명시 등록 필수** — 안 하면 향후 검증 확장 시 오히려 위반 (→ D-1 §5 R-A2).
- `opal-action-monitor`/`opas`는 rows[]의 `row_id`/`stage`/`item`/`status`만 읽으므로 key 선택 필드 추가에 무영향 (→ D-1 §3.2).
- render_pipeline_table(STATE.md 표)는 **무변경** — key는 state.json에만 저장, 마크다운 표에는 노출하지 않는다(기존 5열 유지, `parse_existing_state_md` 회귀 방지).

### F-003: 행 주소 플래그 신설 + `--action-step` 개명

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | `resolve_row_index` 신설, mark/advance/block/add-row argparse 확장 | 수정 |

#### 2.3.2 현재 구현
- 행 주소 해석 지점은 `find_row`/`find_row_index`(`:354-366`) + `cmd_gate_pass` 인라인 순회(`:1290-1296`) 뿐. 상위 가드(`check_stage_transition_guard`·`check_close_gate`·`_run_clarification_hook`)는 모두 `row_index`(배열 위치)만 소비, 원본 주소 인자 비의존 (→ D-1 §1.2, §4 #1) → 주소 해석을 어떻게 하든 `row_index`만 정확히 산출하면 하위 로직 무변경 재사용.
- argparse: `--row`가 mark/advance/block에 `type=int, required=True`(`:1841,1848,1865`), add-row는 `--after type=int required=True`(`:1877`).
- `--step N/M`은 `_parse_step`(`:918-928`)이 파싱, cmd_mark 조기 done 가드(`:987-1004`)에서 소비. 로직·`row["step"]` 필드 무변경 — 별칭만 추가하면 되는 국소 변경.
- CLOSE 게이트(`:449-464`)·명확화 훅은 `item=="사용자 확인"`(한글) 의존 → slug 변경 무관 (→ D-1 §5 R-A5).

#### 2.3.3 영향 범위
- `find_row_index(state, args.row, command)` 호출부 4곳(cmd_mark `:949`, cmd_advance, cmd_block, cmd_add_row `:1184`)을 `resolve_row_index(...)`로 교체. `cmd_gate_pass`(deprecated)는 `--start` 숫자 유지 — 무변경.
- `--row` required 해제로 argparse 필수 강제 소멸 → `resolve_row_index`가 0개/2개 주소를 `task_step_addr_required`/`task_step_addr_conflict`로 대체 강제 (H-2).
- `worker_scope_violation` 게이트(`:952-963`)는 row_index 산출 이후 stage 비교만 하므로 주소 방식 무관 무변경 (→ D-1 §3.2, §5 R-A4).

### F-004: add-row `--key` 지원

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | cmd_add_row `--key` 처리 + 자동 생성·유일성 | 수정 |

#### 2.4.2 현재 구현
- cmd_add_row(`:1173-1227`): `--after` 위치에 삽입 후 `for i,row: row["row_id"]=i+1` 전체 재번호(`:1202-1204`). 재정렬은 row_id만 갱신 — 기존 key는 불변이라 안전(단 자동 생성 key의 전체 스캔 유일성 검증은 신규 필요, → D-1 §5 R-A3).
- 신규 행 dict(`:1188-1197`)에는 key 필드 없음 — 여기에 key 주입.

#### 2.4.3 영향 범위
- 자동 생성 key `{stage_slug}.{item_slug}_{n}`는 동일 stage 내 기존 동적 행과 충돌 방지 위해 rows[] 전체 스캔 필요(현재 없음, 신규 구현).
- `--after` 앵커도 key 주소 지원(R-4 "add-row 대응 포함") → `resolve_row_index` 재사용.

### F-005: opdd 드리프트 정정 (enum 등록만)

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | STAGE_ENUM·init `--skill` choices 확장 | 수정 |
| 스키마 | `opal/tools/state-tool/schema/state.schema.json` | skill·stage enum 확장 | 수정 |

#### 2.5.2 현재 구현
- `opal-pilot-data-design`은 `--skill opdd`를 지시하나 skill enum(`state.schema.json:15`, `state_tool.py:1817` choices)에 미등록, 단계 DICT/MODEL/DDL·MIGRATION도 stage 16종 enum(`state.schema.json:55-59`, `state_tool.py:29-33`)에 없어 현재 init 자체가 거부 (→ D-1 §3.2, §4 #5).
- opdd `DDL/MIGRATION` 단계명에 슬래시 포함(`opal-pilot-data-design/SKILL.md:237`) — key 형식 §6 "stage_slug는 `/`→`_`"가 이미 반영(`ddl_migration`). 단 opdd pipeline.json은 2차 범위이므로 1차는 STAGE_ENUM 문자열 추가만.

#### 2.5.3 영향 범위
- opdd SKILL.md 본문 **무변경** — enum 등록만으로 기존 `init --skill opdd` 호출이 거부→정상 전환(간접 수혜, → D-1 §3.2).
- `--worker-stage`(`:1852-1854`)·add-row `--stage`(`:1878`)는 choices=STAGE_ENUM 참조 → enum 추가 시 자동 반영.

### F-006: 그룹 A 4종 pipeline.json 생성 + SKILL.md 전환

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-pilot-project/references/pipeline.json` | opp 스펙(9 task-step) | 신규 |
| 스킬 | `opal/skills/opal-pilot-dev/references/pipeline.json` | opd 스펙(15 task-step) | 신규 |
| 스킬 | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | opds 스펙(10 task-step) | 신규 |
| 스킬 | `opal/skills/opal-pilot-dev-wireframe/references/pipeline.json` | opdw 스펙(9 task-step, 3~5 conditional) | 신규 |
| 스킬 | `opal/skills/opal-pilot-project/SKILL.md` | STATE.md 도메인 치환값 섹션 전환 | 수정 (`:153-179`) |
| 스킬 | `opal/skills/opal-pilot-dev/SKILL.md` | 동일 | 수정 (`:269-312`) |
| 스킬 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 동일 | 수정 (`:238-276`) |
| 스킬 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 동일 | 수정 (`:181-219`) |

#### 2.6.2 현재 구현
- 그룹 A 4종 표 행 수·구조가 TASK 서술과 정확히 일치: opp 9행(`opal-pilot-project/SKILL.md:165-177`)/opd 15행(`opal-pilot-dev/SKILL.md:281-299`)/opds 10행(`opal-pilot-dev-short/SKILL.md:250-263`)/opdw 9행+조건부 3~5(`opal-pilot-dev-wireframe/SKILL.md:193-208`) (→ D-1 §4 #4).
- 4종 SKILL.md 모두 `**[MUST] STATE.md 초기 생성**: ...run.sh init ... --rows-from <SKILL.md 경로>` 문구 + 마크다운 표 SSOT를 게재. R-7에서 `--rows-from`은 **동일 플래그명 유지, 경로만 `.md`→`references/pipeline.json`**으로 교체(→ D-1 §1.3).
- 게이트 4행 패턴(QA Gate/State Gate) 절대 생성 금지 — 그룹 A는 표준 구조(작업/PM Gate/사용자 확인/DONE.md 생성) (→ D-1 §1.2 gate-pass deprecated).

#### 2.6.3 영향 범위
- SKILL.md 표(마크다운 SSOT)는 참조 안내 + 지시문·근거로 축소하되, `.md` 파싱 폴백 하위호환을 위해 **표를 물리 삭제하지 않는다**(선택) — TASK.md는 "데이터 중복 게재 없이"를 권하나 폴백 회귀 방지를 위해 표를 남기고 "SSOT는 pipeline.json" 명시를 권고. EXECUTE 재량으로 판단(H-4 폴백 테스트가 안전망).

### F-007: 테스트 보강

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/tests/test_state_tool.py` | 신규 테스트 클래스 추가(기존 무변경) | 수정 |

#### 2.7.2 현재 구현
- unittest 기반(pytest 아님, `test_state_tool.py:19` [MUST] T-11). 패턴 1: `BaseTestCase` + `make_args()` SimpleNamespace 직접 호출(`:94-160`). 패턴 2: `subprocess.run(["bash", _RUN_SH]+args)`로 실제 CLI 구동(argparse 레벨 제약 검증, `:3496-3553`).
- `make_args(**kwargs)`의 defaults 딕셔너리에 신규 플래그(`task_step`/`task_step_id`/`action_step`/`key`/`after_task_step` 등) 기본값 추가 필수 — 안 하면 기존 테스트 `AttributeError` (→ D-1 §1.4).

#### 2.7.3 영향 범위
- argparse mutually-exclusive/required 관련 제약은 make_args 우회 불가 → 패턴 2(subprocess)로 검증(H-1·H-2·H-6).
- 하위호환 증명: `--row`/`--step` 별칭 회귀는 "기존 경로 비파괴"를 명시 검증하는 신규 테스트로(기존 케이스 무수정, → D-1 §1.4 하위호환 증명 패턴).

---

## 3. 기능별 설계

### F-001: pipeline-spec 스키마 신설 + spec-validate 서브명령

#### 3.1.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/state-tool/schema/pipeline-spec.schema.json` | 스키마 | 스펙 JSON Schema(Draft-07) 문서 SSOT | (→ D-2 R-1) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | `KEY_PATTERN`·`stage_to_slug`·`validate_pipeline_spec`·`cmd_spec_validate` 신설, ERROR_CODES 추가, argparse `spec-validate` 서브파서 | `state_tool.py:66-103,1788-1924` |

#### 3.1.2 API·데이터 모델·화면 설계

**pipeline-spec.schema.json 구조 (Draft-07, 문서 SSOT — DEC-2)**

```
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "OPAL pipeline.json Spec Schema",
  "type": "object",
  "required": ["spec_version", "skill", "meta", "task_steps"],
  "additionalProperties": false,
  "properties": {
    "spec_version": { "const": "1.0" },
    "skill":        { "enum": ["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd","oppl","opdd"] },
    "meta": {
      "type": "object",
      "required": ["mode_label", "stages"],
      "properties": {
        "mode_label": { "type": "string" },
        "stages":     { "type": "array", "items": {"type": "string"}, "minItems": 1 }
      }
    },
    "task_steps": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object",
        "required": ["id", "key", "stage", "item"],
        "additionalProperties": false,
        "properties": {
          "id":          { "type": "integer", "minimum": 1 },
          "key":         { "type": "string", "pattern": "^[a-z][a-z0-9_]*\\.[a-z][a-z0-9_]*(_[0-9]+)?$" },
          "stage":       { "type": "string" },
          "item":        { "type": "string", "minLength": 1 },
          "conditional": { "type": "boolean" }
        }
      }
    },
    "pm_gate": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["stage", "artifacts", "checklist"],
        "properties": {
          "stage":     { "type": "string" },
          "artifacts": { "type": "array", "items": {"type": "string"} },
          "checklist": { "type": "array", "items": {"type": "string"} }
        }
      }
    }
  }
}
```

> [MUST] `tasks/070.../TASK.md` §확정 방향 §6: "key 형식 `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$`, stage_slug는 stage enum 소문자화(`-`·`/`→`_`), 스펙 내 유일성 강제." — 스키마 pattern·`validate_pipeline_spec` 유일성 검사 모두 이 규칙을 집행한다.

**신규 상수·헬퍼 함수 시그니처**

```python
KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$")

def stage_to_slug(stage: str) -> str:
    """stage enum → slug. 소문자화 + '-'·'/' → '_'. (TASK §6)"""
    return stage.lower().replace("-", "_").replace("/", "_")

def load_pipeline_spec(spec_path: str, command: str) -> dict:
    """pipeline.json 로드. 없으면 spec_file_not_found, 파싱 실패 시 spec_invalid_json."""

def validate_pipeline_spec(spec: dict) -> list:
    """스펙 검증 → violations[] (DEC-2 수작업 검증). 검사 항목:
    ① 필수 필드(spec_version/skill/meta/task_steps) 존재 → spec_missing_field
    ② skill enum 정합 → spec_skill_invalid
    ③ task_steps[].stage ∈ STAGE_ENUM → spec_stage_invalid
    ④ key 형식(KEY_PATTERN) → spec_key_format_invalid
    ⑤ key 유일성(스펙 내) → spec_key_duplicate
    ⑥ id 1..N 순차 → spec_id_sequence_invalid
    ⑦ key의 stage_slug가 실제 stage와 정합(stage_to_slug(stage)==key.split('.')[0]) → spec_key_stage_mismatch
    반환: [{code, id?, key?, detail}] (cmd_validate violations 포맷 차용)"""

def cmd_spec_validate(args):
    """spec-validate <pipeline.json> — 단일 라인 JSON.
    {ok, command:'spec-validate', violations:[...], violations_count:N}, exit 0/1.
    (cmd_validate:1163-1169 출력 계약 동일)"""
```

**argparse 서브파서 (build_parser 내 추가)**

```python
p_spec = sub.add_parser("spec-validate", help="pipeline.json 스펙 검증 (R-6, DEC-2)")
p_spec.add_argument("spec_path", metavar="<pipeline.json>")
p_spec.set_defaults(func=cmd_spec_validate)
```
> `spec-validate`는 task-path가 아닌 **파일 경로**를 받는다(다른 서브명령과 구분). run.sh 무변경(`run.sh:12` `"$@"` 전달).

**신설 에러 코드 (ERROR_CODES 추가, `state_tool.py:68-103`)**
| 코드 | 메시지 템플릿 | 사용처 |
|------|-------------|--------|
| `spec_file_not_found` | `pipeline.json 스펙 파일 없음: {path}` | load_pipeline_spec |
| `spec_invalid_json` | `pipeline.json JSON 파싱 실패: {detail}` | load_pipeline_spec |
| `spec_validation_failed` | `pipeline.json 스펙 검증 실패: {detail}` | build_rows_from_pipeline_json(F-002) |

> violations[] 내부 코드(`spec_missing_field`/`spec_skill_invalid`/`spec_stage_invalid`/`spec_key_format_invalid`/`spec_key_duplicate`/`spec_id_sequence_invalid`/`spec_key_stage_mismatch`)는 cmd_validate의 `schema_violation`처럼 **인라인 문자열**로 쓰며 ERROR_CODES 템플릿 불요.

#### 3.1.3 환경 변경
해당 없음 (표준 라이브러리만, → D-1 §6.1).

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 산출물 검사 | pipeline-spec.schema.json 존재 + Draft-07 유효 JSON |
| TS-002 | R-6 AC | 기능 테스트 | 정상 스펙 → `ok:true, violations_count:0` |
| TS-003 | R-6 AC | 기능 테스트 | key 중복 스펙 → `spec_key_duplicate` violation |
| TS-004 | R-6 AC | 기능 테스트 | key 형식 위반(대문자/슬래시) → `spec_key_format_invalid` |
| TS-005 | R-6 AC | 기능 테스트 | stage enum 위반 → `spec_stage_invalid` |

### F-002: init `.json` 스펙 로딩 + state.json 스키마 1.1

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | `build_rows_from_pipeline_json` 신설, cmd_init `.json`/`.md` 확장자 분기 | `state_tool.py:694-701` |
| 2 | `opal/tools/state-tool/schema/state.schema.json` | 스키마 | rows[].key·conditional 추가, schema_version 1.1 병행 | `state.schema.json:22-24,48-101` |

#### 3.2.2 API·데이터 모델·화면 설계

**state.schema.json 1.1 diff**

```diff
  "schema_version": {
-   "const": "1.0",
-   "description": "스키마 버전 — 신규 enum 추가 시 1.1로 올림"
+   "enum": ["1.0", "1.1"],
+   "description": "스키마 버전 — 1.0(레거시·key 없음) / 1.1(key·conditional 지원) 병행 허용"
  },
  ...
  "rows": { "items": { "properties": {
      ... (기존 row_id/stage/item/status/status_label/timestamp/owner/note 유지) ...
+     "key": {
+       "type": "string",
+       "pattern": "^[a-z][a-z0-9_]*\\.[a-z][a-z0-9_]*(_[0-9]+)?$",
+       "description": "task-step key (문자 주소) — {stage_slug}.{item_slug} (1.1 신규, 선택)"
+     },
+     "conditional": {
+       "type": "boolean",
+       "description": "조건부 task-step (예: opdw WIREFRAME 스킵 대상). 1차 순수 메타데이터 — 자동 na 없음 (DEC-1)"
+     }
  } } }
```
> `key`·`conditional`은 **required에 추가하지 않는다**(선택 필드) → key 없는 레거시 1.0 state.json도 검증 통과 (H-3, → D-1 §5 R-A2). `additionalProperties:false`(`:47`) 유지하되 두 필드를 properties에 명시 등록해 위반 회피.

**build_rows_from_pipeline_json 시그니처**

```python
def build_rows_from_pipeline_json(spec_path: str, command: str, mode: str) -> list:
    """.json 스펙 → rows[] (R-2). 절차:
    1. spec = load_pipeline_spec(spec_path, command)
    2. violations = validate_pipeline_spec(spec)
       if violations: err(command, 'spec_validation_failed', detail=violations[0])
    3. for i, ts in enumerate(spec['task_steps']):
         row = {row_id: i+1, stage: ts['stage'], item: ts['item'],
                key: ts['key'],               # ← 1.1 key 영속화
                status:'pending', status_label:'⬜', timestamp:None,
                owner:'PM', note:None}
         if ts.get('conditional'): row['conditional'] = True   # DEC-1 저장만
         # agentic 자동 na — 기존 규칙 동일(:507-511)
         if mode=='agentic' and ts['item']=='사용자 확인' and ts['stage']!='CLOSE':
             row 상태 na/label '-'/owner 'auto'/note 'agentic auto-na at init'
         rows.append(row)
    return rows"""
```

**cmd_init 확장자 분기 (`state_tool.py:697-698` 교체)**

```python
elif args.rows_from:
    if args.rows_from.endswith(".json"):
        rows = build_rows_from_pipeline_json(args.rows_from, command, args.mode)
    else:
        print('{"warning":"--rows-from <SKILL.md> markdown 파싱은 deprecated. '
              'references/pipeline.json으로 이관하세요 (task 070)."}', file=sys.stderr)
        rows = build_rows_from_skill_md(args.rows_from, command, args.mode)
```
> [MUST] `tasks/070.../TASK.md` §제약: ".md 파싱 폴백 ... 동작 유지. 기존 테스트 케이스 수정 금지." — `.md` 분기는 로직 무변경 + stderr 경고 1줄만 추가(stdout JSON 계약 불변).

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음 — 레거시 1.0 state.json은 그대로 유효(스키마 병행). 마이그레이션 불요.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | R-2 AC | 기능 테스트 | `.json` init → rows[]에 key 전 행 존재 |
| TS-007 | R-2 AC | 기능 테스트 | `.md` init → 기존과 동일 결과 + stderr 경고 1줄 |
| TS-008 | R-3 AC | 산출물 검사 | key 있는 1.1 state.json이 state.schema 위반 아님 |
| TS-009 | R-3 AC | 회귀 테스트 | key 없는 1.0 레거시 state.json validate 통과 |
| TS-010 | R-2/DEC-1 | 기능 테스트 | conditional:true task_step → rows[].conditional=true, status는 na 아님(pending) |

### F-003: 행 주소 플래그 신설 + `--action-step` 개명

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | `resolve_row_index` 신설, mark/advance/block/add-row 호출부·argparse 확장, `--action-step` 별칭 | `state_tool.py:354-366,949,1184,1841-1881` |

#### 3.3.2 API·데이터 모델·화면 설계

**resolve_row_index 공통 해석 함수 시그니처**

```python
def resolve_row_index(state: dict, command: str,
                      key_val: str | None,
                      id_val: int | None,
                      row_val: int | None,
                      addr_label: str = "task-step") -> int:
    """key/id/deprecated-row 3주소를 row_index로 통일 해석 (R-4).
    - 제공된 주소 개수 집계(None 아닌 것):
        0개 → err(command, 'task_step_addr_required')
        2개+ → err(command, 'task_step_addr_conflict')
    - key_val: rows[]에서 row['key']==key_val 탐색.
        미매칭 → err('task_step_not_found', key=key_val,
                      candidates=[r.get('key') for r in rows if r.get('key')])
    - id_val / row_val: row_id 동등비교(기존 find_row_index 로직 재사용).
        미매칭 → err('row_not_found', row_id=...)
    반환: row_index(int)."""
```
> argparse `mutually_exclusive_group`을 쓰지 않고 3플래그를 독립 선언한 뒤 **런타임 개수 검사**로 `task_step_addr_conflict`를 JSON 에러로 방출한다(argparse mutex는 exit 2 usage 에러라 코드 방출 불가). (→ D-1 §5 R-A4)

**호출부 교체 (4곳)**
| 함수 | 기존 | 신규 |
|------|------|------|
| cmd_mark(`:949`) | `find_row_index(state, args.row, command)` | `resolve_row_index(state, command, args.task_step, args.task_step_id, args.row)` |
| cmd_advance(`:~890`) | 동일 | 동일 |
| cmd_block | 동일 | 동일 |
| cmd_add_row(`:1184`) | `find_row_index(state, args.after, command)` | `resolve_row_index(state, command, args.after_task_step, args.after_task_step_id, args.after, addr_label='after')` |

> `find_row_index`(`:361-366`)는 삭제하지 않고 존치 — `resolve_row_index` 내부 id/row 분기가 동일 로직 재사용(회귀 안전). `cmd_gate_pass`(deprecated) `--start`는 무변경.

**argparse 확장 (mark 예시 — advance/block 동형)**

```python
# 기존: p_mark.add_argument("--row", type=int, required=True)  → required 해제
p_mark.add_argument("--task-step", dest="task_step", metavar="<key>")
p_mark.add_argument("--task-step-id", dest="task_step_id", type=int, metavar="<n>")
p_mark.add_argument("--row", dest="row", type=int, metavar="<n> [deprecated]",
                    help="[deprecated] --task-step / --task-step-id 사용 권장")
# R-5: --action-step 별칭 (dest 공유)
p_mark.add_argument("--action-step", dest="step", metavar="N/M",
                    help="EXECUTE 액션 진행률 (구 --step)")
# 기존 --step 유지(별칭): p_mark.add_argument("--step", dest="step", metavar="N/M")
```
> [MUST] `tasks/070.../TASK.md` §확정 방향 §3: "기존 `--row`는 deprecated 별칭 유지. 기존 `--step`은 `--action-step`으로 개명(별칭 `--step` 유지)." — `--step`·`--action-step`은 `dest="step"` 공유로 `_parse_step`(`:918-928`)·`row["step"]` 로직 무변경.
> add-row는 `--after`(deprecated numeric) + `--after-task-step`(key) + `--after-task-step-id` 추가, `--after` required 해제.

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-4 AC | 기능 테스트 | `mark --task-step plan.pm_gate --done` → 해당 행 done |
| TS-012 | R-4 AC | 기능 테스트 | 동일 행에 `--task-step-id`·`--row`도 동일 결과(별칭 회귀) |
| TS-013 | R-4 AC | 기능 테스트(subprocess) | 주소 2개 동시 → `task_step_addr_conflict` |
| TS-014 | R-4 AC | 기능 테스트(subprocess) | 주소 0개 → `task_step_addr_required` |
| TS-015 | R-4 AC | 기능 테스트 | key 미매칭 → `task_step_not_found` + candidates 목록 |
| TS-016 | R-5 AC | 기능 테스트 | `--action-step 2/6`·`--step 2/6` 모두 기존 진행률 동작 동일 |
| TS-017 | R-4/R-A5 | 회귀 테스트 | slug user_confirm 도입 후 CLOSE 게이트·명확화 훅 회귀 0 |

### F-004: add-row `--key` 지원

#### 3.4.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | cmd_add_row `--key` 처리 + 자동 생성·전체 스캔 유일성 | `state_tool.py:1173-1227` |

#### 3.4.2 API·데이터 모델·화면 설계

**자동 key 생성 로직**

```python
def _auto_row_key(state: dict, stage: str, item: str) -> str:
    """{stage_slug}.{item_slug}_{n} 자동 생성. 전체 rows[] 스캔 유일성 (R-9, R-A3).
    - stage_slug = stage_to_slug(stage)
    - item_slug  = item에서 첫 [a-zA-Z][a-zA-Z0-9]* 토큰 소문자화, 없으면 'item'
      (예: 'fix 작업 (2/3)' → 'fix')
    - n = 동일 base로 이미 존재하는 key 개수 +1 부터 증가, 충돌 없을 때까지"""
```

**cmd_add_row 변경 (`:1188-1197` 신규 행 dict)**
```python
existing_keys = {r.get("key") for r in state["rows"] if r.get("key")}
if args.key:
    if not KEY_PATTERN.match(args.key):
        err(command, "task_step_key_invalid", key=args.key)
    if args.key in existing_keys:
        err(command, "task_step_key_duplicate", key=args.key)
    new_key = args.key
else:
    new_key = _auto_row_key(state, args.stage, args.item)   # 유일성 내장
new_row["key"] = new_key
```
> 재정렬(`:1202-1204`)은 row_id만 갱신, 기존 key 불변 → 안전(H-5, → D-1 §5 R-A3). `--after` 앵커는 `resolve_row_index`(F-003) 재사용으로 key 주소도 지원.

**신설 에러 코드**
| 코드 | 메시지 템플릿 |
|------|-------------|
| `task_step_key_invalid` | `key {key} 형식 위반 — 패턴 ^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$` |
| `task_step_key_duplicate` | `key {key} 중복 — 파일 내 유일해야 함` |

#### 3.4.3 환경 변경
해당 없음.

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-018 | R-9 AC | 기능 테스트 | `--key` 지정 add-row → 신규 행에 해당 key, 기존 key 불변 |
| TS-019 | R-9 AC | 기능 테스트 | key 미지정 → `{stage_slug}.{item}_{n}` 자동 생성 |
| TS-020 | R-9 AC | 기능 테스트 | TEST fix 2회 add-row → `test.fix_1`·`test.fix_2` (충돌 없음) |
| TS-021 | R-9 AC | 기능 테스트 | 기존 key와 중복 `--key` → `task_step_key_duplicate` |

### F-005: opdd 드리프트 정정 (enum 등록만)

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | STAGE_ENUM + `DICT`/`MODEL`/`DDL/MIGRATION`, init `--skill` choices + `opdd` | `state_tool.py:29-33,1817` |
| 2 | `opal/tools/state-tool/schema/state.schema.json` | 스키마 | skill enum + `opdd`, stage enum + 3종(16→19) | `state.schema.json:15,55-59` |

#### 3.5.2 API·데이터 모델·화면 설계

```diff
# state_tool.py:29-33
  STAGE_ENUM = [
    "TASK","ANALYSIS","PLAN","TEST-SCENARIO","EXECUTE","TEST",
    "WIREFRAME","QA","SPEC","REVIEW","DESIGN",
-   "VERIFY","SCAN","CHECK","REPORT","WBS","CLOSE"
+   "VERIFY","SCAN","CHECK","REPORT","WBS","CLOSE",
+   "DICT","MODEL","DDL/MIGRATION"
  ]
# state_tool.py:1817
- choices=["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd","oppl"]
+ choices=["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd","oppl","opdd"]
```
```diff
# state.schema.json:15
- "enum": ["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd","oppl"]
+ "enum": ["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd","oppl","opdd"]
# state.schema.json:55-59 stage enum 배열에 "DICT","MODEL","DDL/MIGRATION" 추가(19종)
```
> [MUST] `tasks/070.../TASK.md` R-8: "skill enum에 `opdd` 추가(state_tool.py choices + state.schema.json), stage enum에 `DICT`·`MODEL`·`DDL/MIGRATION` 추가(16→19종)." — 1차는 **enum 문자열 추가만**. opdd pipeline.json·slug 실적용은 2차(→ D-1 §4 #5). `MODE_BOUNDARY_STAGES` 분류(DICT/MODEL 설계단계 여부)는 opdd 전환 시점(2차)으로 이연.

#### 3.5.3 환경 변경
해당 없음.

#### 3.5.4 배치/마이그레이션
해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-022 | R-8 AC | 기능 테스트(subprocess) | `init --skill opdd ...` 거부 해소(정상 생성) |
| TS-023 | R-8 AC | 기능 테스트 | DICT 단계 `add-row --stage DICT` enum 에러 없이 동작 |

### F-006: 그룹 A 4종 pipeline.json 생성 + SKILL.md 전환

#### 3.6.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/opal-pilot-project/references/pipeline.json` | 스킬 | opp 9 task-step | (→ D-7) |
| 2 | `opal/skills/opal-pilot-dev/references/pipeline.json` | 스킬 | opd 15 task-step | (→ D-8) |
| 3 | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | 스킬 | opds 10 task-step | (→ D-9) |
| 4 | `opal/skills/opal-pilot-dev-wireframe/references/pipeline.json` | 스킬 | opdw 9 task-step(3~5 conditional) | (→ D-10) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1~4 | 4종 SKILL.md "STATE.md 도메인 치환값" 섹션 | 스킬 | `--rows-from` 경로 `.md`→`references/pipeline.json`, 표는 참조안내+근거로 축소(폴백 위해 존치 권고) | D-7~D-10 각 줄범위 |

#### 3.6.2 슬러그 명명 적용 + pipeline.json 전문(全文)

**slug 매핑 규칙 적용** (TASK §5): ① 산출물 스텝=산출물명(task_md/analysis_md/plan_md/test_scenario_md/wireframe_md), ② 행위 스텝=동사(implement/run_tests), ③ 게이트=pm_gate/user_confirm, CLOSE 산출물=done_md. item(한글 표시명)은 유지, key만 영문 slug (→ D-1 §5 R-A5).

> [MUST] `tasks/070.../TASK.md` §확정 방향 §5: "slug 규칙 — ① 산출물 스텝=산출물명 ② 행위 스텝=동사 ③ 게이트=pm_gate·user_confirm. `work` 사용 금지."

**opp — `opal/skills/opal-pilot-project/references/pipeline.json` (9 task-step)**
```json
{
  "spec_version": "1.0",
  "skill": "opp",
  "meta": { "mode_label": "Project Task", "stages": ["TASK", "PLAN", "EXECUTE", "CLOSE"] },
  "task_steps": [
    { "id": 1, "key": "task.task_md",        "stage": "TASK",    "item": "작업" },
    { "id": 2, "key": "task.user_confirm",   "stage": "TASK",    "item": "사용자 확인" },
    { "id": 3, "key": "plan.plan_md",        "stage": "PLAN",    "item": "작업" },
    { "id": 4, "key": "plan.pm_gate",        "stage": "PLAN",    "item": "PM Gate" },
    { "id": 5, "key": "plan.user_confirm",   "stage": "PLAN",    "item": "사용자 확인" },
    { "id": 6, "key": "execute.implement",   "stage": "EXECUTE", "item": "작업" },
    { "id": 7, "key": "execute.pm_gate",     "stage": "EXECUTE", "item": "PM Gate" },
    { "id": 8, "key": "execute.user_confirm","stage": "EXECUTE", "item": "사용자 확인" },
    { "id": 9, "key": "close.done_md",       "stage": "CLOSE",   "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "PLAN",    "artifacts": ["TASK.md", "PLAN.md"], "checklist": ["TASK.md 요구사항", "PLAN.md §3", "PLAN.md §4"] },
    { "stage": "EXECUTE", "artifacts": ["GC-CONVENTION-*.md"], "checklist": ["PLAN.md §3 실행 체크리스트", "컨벤션 자동 진단"] }
  ]
}
```

**opd — `opal/skills/opal-pilot-dev/references/pipeline.json` (15 task-step)**
```json
{
  "spec_version": "1.0",
  "skill": "opd",
  "meta": { "mode_label": "Full Task", "stages": ["TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO", "EXECUTE", "TEST", "CLOSE"] },
  "task_steps": [
    { "id": 1,  "key": "task.task_md",                 "stage": "TASK",          "item": "작업" },
    { "id": 2,  "key": "task.user_confirm",            "stage": "TASK",          "item": "사용자 확인" },
    { "id": 3,  "key": "analysis.analysis_md",         "stage": "ANALYSIS",      "item": "작업" },
    { "id": 4,  "key": "analysis.pm_gate",             "stage": "ANALYSIS",      "item": "PM Gate" },
    { "id": 5,  "key": "analysis.user_confirm",        "stage": "ANALYSIS",      "item": "사용자 확인" },
    { "id": 6,  "key": "plan.plan_md",                 "stage": "PLAN",          "item": "작업" },
    { "id": 7,  "key": "plan.pm_gate",                 "stage": "PLAN",          "item": "PM Gate" },
    { "id": 8,  "key": "plan.user_confirm",            "stage": "PLAN",          "item": "사용자 확인" },
    { "id": 9,  "key": "test_scenario.test_scenario_md","stage": "TEST-SCENARIO","item": "작업" },
    { "id": 10, "key": "test_scenario.user_confirm",   "stage": "TEST-SCENARIO", "item": "사용자 확인" },
    { "id": 11, "key": "execute.implement",            "stage": "EXECUTE",       "item": "작업" },
    { "id": 12, "key": "test.run_tests",               "stage": "TEST",          "item": "작업" },
    { "id": 13, "key": "test.pm_gate",                 "stage": "TEST",          "item": "PM Gate" },
    { "id": 14, "key": "test.user_confirm",            "stage": "TEST",          "item": "사용자 확인" },
    { "id": 15, "key": "close.done_md",                "stage": "CLOSE",         "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "ANALYSIS",      "artifacts": ["ANALYSIS.md"], "checklist": ["-"] },
    { "stage": "PLAN",          "artifacts": ["TASK.md", "PLAN.md"], "checklist": ["TASK.md 요구사항", "PLAN.md §4.2", "PLAN.md §5", "PLAN.md §리스크 가설 표"] },
    { "stage": "TEST-SCENARIO", "artifacts": ["TEST-SCENARIO.md"], "checklist": ["mock 부재(grep)", "사전 조건 데이터 채워짐", "Given/When/Then 3필드", "가설↔시나리오 매핑 완전", "L1/L2/L3 계층 명시", "L3 [SUPERVISOR] 마커", "실행 방식(M1/M2/M3) 명시"] },
    { "stage": "TEST",          "artifacts": ["TEST-SCENARIO.md", "GC-CONVENTION-*.md"], "checklist": ["시나리오 결과/코드품질/보안/회귀", "컨벤션 자동 진단 PASS"] }
  ]
}
```

**opds — `opal/skills/opal-pilot-dev-short/references/pipeline.json` (10 task-step)**
```json
{
  "spec_version": "1.0",
  "skill": "opds",
  "meta": { "mode_label": "Short Task", "stages": ["TASK", "PLAN", "EXECUTE", "TEST", "CLOSE"] },
  "task_steps": [
    { "id": 1,  "key": "task.task_md",         "stage": "TASK",    "item": "작업" },
    { "id": 2,  "key": "task.user_confirm",    "stage": "TASK",    "item": "사용자 확인" },
    { "id": 3,  "key": "plan.plan_md",         "stage": "PLAN",    "item": "작업" },
    { "id": 4,  "key": "plan.pm_gate",         "stage": "PLAN",    "item": "PM Gate" },
    { "id": 5,  "key": "plan.user_confirm",    "stage": "PLAN",    "item": "사용자 확인" },
    { "id": 6,  "key": "execute.implement",    "stage": "EXECUTE", "item": "작업" },
    { "id": 7,  "key": "test.run_tests",       "stage": "TEST",    "item": "작업" },
    { "id": 8,  "key": "test.pm_gate",         "stage": "TEST",    "item": "PM Gate" },
    { "id": 9,  "key": "test.user_confirm",    "stage": "TEST",    "item": "사용자 확인" },
    { "id": 10, "key": "close.done_md",        "stage": "CLOSE",   "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "PLAN", "artifacts": ["TASK.md", "PLAN.md", "TEST-SCENARIO.md"], "checklist": ["TASK.md 요구사항", "PLAN.md §4.2", "PLAN.md §5", "TEST-SCENARIO.md 시나리오 목록/보안/설계 피드백"] },
    { "stage": "TEST", "artifacts": ["TEST-SCENARIO.md", "GC-CONVENTION-*.md"], "checklist": ["시나리오 결과/코드품질/보안/회귀", "컨벤션 자동 진단 PASS"] }
  ]
}
```

**opdw — `opal/skills/opal-pilot-dev-wireframe/references/pipeline.json` (9 task-step, 3~5 conditional)**
```json
{
  "spec_version": "1.0",
  "skill": "opdw",
  "meta": { "mode_label": "Wireframe UI", "stages": ["TASK", "WIREFRAME", "EXECUTE", "CLOSE"] },
  "task_steps": [
    { "id": 1, "key": "task.task_md",           "stage": "TASK",      "item": "작업" },
    { "id": 2, "key": "task.user_confirm",      "stage": "TASK",      "item": "사용자 확인" },
    { "id": 3, "key": "wireframe.wireframe_md",  "stage": "WIREFRAME", "item": "작업",        "conditional": true },
    { "id": 4, "key": "wireframe.pm_gate",       "stage": "WIREFRAME", "item": "PM Gate",     "conditional": true },
    { "id": 5, "key": "wireframe.user_confirm",  "stage": "WIREFRAME", "item": "사용자 확인", "conditional": true },
    { "id": 6, "key": "execute.implement",       "stage": "EXECUTE",   "item": "작업" },
    { "id": 7, "key": "execute.pm_gate",         "stage": "EXECUTE",   "item": "PM Gate" },
    { "id": 8, "key": "execute.user_confirm",    "stage": "EXECUTE",   "item": "사용자 확인" },
    { "id": 9, "key": "close.done_md",           "stage": "CLOSE",     "item": "DONE.md 생성" }
  ],
  "pm_gate": [
    { "stage": "WIREFRAME", "artifacts": ["TASK.md", "wireframe.md"], "checklist": ["TASK.md 요구사항", "wireframe.md 화면 목록", "op-dev-qa 와이어프레임 검증 기준"] },
    { "stage": "EXECUTE",   "artifacts": ["changed_files", "GC-CONVENTION-*.md"], "checklist": ["빌드/린트 결과", "wireframe↔코드 대조", "컨벤션 자동 진단"] }
  ]
}
```

> [MUST] `tasks/070.../TASK.md` R-7 AC: "4종 모두 `spec-validate` 통과 + 실제 `init --rows-from references/pipeline.json` 실증으로 state.json 생성(행 수 9/15/10/9 일치, key 전 행 존재)."

**SKILL.md 전환 예시 (4종 공통 패턴)** — opp `:162` 예:
```diff
- > **[MUST] STATE.md 초기 생성**: `~/.opal/tools/state-tool/run.sh init <task-path> --skill opp --mode <...> --rows-from <SKILL.md 경로>` 호출. ... `--rows-from`이 아래 표를 파싱하여 행 구성을 자동 추출한다.
+ > **[MUST] STATE.md 초기 생성**: `~/.opal/tools/state-tool/run.sh init <task-path> --skill opp --mode <...> --rows-from opal/skills/opal-pilot-project/references/pipeline.json` 호출. 행 구성 SSOT는 `references/pipeline.json`(task-step key 포함). 아래 표는 사람 열람용 미러 — 편집 금지(폴백 파싱 잔존).
```

#### 3.6.3 환경 변경
해당 없음.

#### 3.6.4 배치/마이그레이션
해당 없음 — 신규 태스크부터 json 경로 사용. 진행 중 레거시 state.json은 그대로 동작.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-024 | R-7 AC | 산출물 검사 | 4종 pipeline.json 모두 `spec-validate` ok:true |
| TS-025 | R-7 AC | 통합 테스트 | opp/opd/opds/opdw json init → 행 수 9/15/10/9 일치 |
| TS-026 | R-7 AC | 통합 테스트 | 각 init 후 rows[] 전 행 key 존재 + 유일 |
| TS-027 | R-7 AC | 회귀 테스트 | opdw conditional 행 3~5가 status na 아님(pending, DEC-1) |

### F-007: 테스트 보강

#### 3.7.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/tests/test_state_tool.py` | 도구 | 신규 클래스 추가(기존 무변경) + make_args defaults 확장 | `test_state_tool.py:94-160,3496-3553` |

#### 3.7.2 API·데이터 모델·화면 설계

**신규 테스트 클래스 (컨벤션: 대상 기능 반영 클래스명 + docstring PLAN 인용)**
| 클래스 | 대상 | 패턴 |
|--------|------|------|
| `TestPipelineSpecValidate` | F-001 spec-validate | 1(직접) + 2(subprocess) |
| `TestPipelineJsonInit` | F-002 json 로딩·key 영속 | 1 |
| `TestStateSchema11Compat` | F-002 1.1/1.0 병행 | 1 |
| `TestTaskStepAddressing` | F-003 주소 3방식·conflict | 1 + 2(argparse 제약) |
| `TestActionStepRename` | F-003 --action-step 별칭 | 1 |
| `TestAddRowKey` | F-004 --key·자동 생성 | 1 |
| `TestOpddEnumDrift` | F-005 opdd init·DICT | 2(subprocess) |
| `TestGroupAPipelineSpecs` | F-006 4종 실증 | 1 + 2 |
| `TestBackwardCompatAliases` | 전역 --row/--step/.md 회귀 | 1 + 2 |

> [MUST] `tasks/070.../TASK.md` R-10 AC: "`pytest opal/tools/state-tool/tests/` 전체 PASS, 기존 케이스 수정 없이 통과(별칭 하위호환 증명)." + `test_state_tool.py:19` [MUST] T-11: "표준 라이브러리만 import (pytest/hypothesis 금지)" → 테스트 코드는 unittest, 실행은 DEC-3.
> `make_args()` defaults(`:94-128`)에 `task_step=None, task_step_id=None, action_step=None(→step), key=None, after_task_step=None, after_task_step_id=None` 추가 — 기존 테스트 AttributeError 방지(005 선례, → D-1 §1.4).

#### 3.7.3 환경 변경
DEC-3 실행기 확인: `~/.opal/.venv`에 pytest 미설치 시 unittest discover로 실행(→ D-1 §5 R-A6). 신규 패키지 설치 없음.

#### 3.7.4 배치/마이그레이션
해당 없음.

#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-028 | R-10 AC | 회귀 테스트 | 기존 테스트 전체 무수정 PASS |
| TS-029 | R-10 AC | 통합 테스트 | 신규 F-001~F-006 케이스 전체 PASS |
| TS-030 | R-10 AC | 회귀 테스트 | `.md` `--rows-from` 파싱 폴백 동작 유지 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-005 | 1, 2, 3 | opal-task-agent | Step1→2 순차(동일 파일), Step3 병렬 가능 | 스키마 신설·enum |
| 2 | F-002 | 4, 5 | opal-task-agent | 순차 | F-001 의존 |
| 3 | F-003, F-004 | 6, 7 | opal-task-agent | 순차(동일 파일) | F-002 의존 |
| 4 | F-006 | 8, 9 | opal-task-agent | Step8(json 4종) → Step9(SKILL.md) | F-001·F-002 의존 |
| 5 | F-007 | 10 | opal-task-agent | 순차 | 전 기능 의존 |
| 6 | 문서 | 11, 12 | opal-task-agent / PM 직접 | 순차 | README·docs 갱신 |

### 4.2 실행 체크리스트
> 총 12개 Step | Phase 6개 | 실행 모드: 복잡 | 전 Step agent: `opal-task-agent` (TASK 지정)

#### Step 1: pipeline-spec.schema.json 신설
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 스키마
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/schema/pipeline-spec.schema.json`
- **작업 내용**: §3.1.2 구조대로 Draft-07 스펙 스키마 작성(spec_version/skill/meta/task_steps[id,key,stage,item,conditional]/pm_gate). 문서 SSOT(DEC-2).
- **완료 기준**: 유효 JSON + 그룹 A 4종 스펙이 이 구조에 부합
- **테스트**: TS-001
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: state_tool.py — spec-validate + 검증 헬퍼 + slug/KEY 상수
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: `KEY_PATTERN`·`stage_to_slug`·`load_pipeline_spec`·`validate_pipeline_spec`·`cmd_spec_validate` 신설, ERROR_CODES 3종 추가, `spec-validate` argparse 서브파서 등록(§3.1.2)
- **완료 기준**: `spec-validate <경로>`가 정상/위반 스펙에 구분된 응답, run.sh 무변경
- **테스트**: TS-002~TS-005
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: opdd enum 드리프트 정정
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 도구, 스키마
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/schema/state.schema.json`
- **작업 내용**: STAGE_ENUM + DICT/MODEL/DDL·MIGRATION, init `--skill` choices + opdd, state.schema skill·stage enum 확장(§3.5.2). enum 문자열 추가만.
- **완료 기준**: `init --skill opdd` 거부 해소 + DICT add-row 동작
- **테스트**: TS-022, TS-023
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 2와 동일 파일 — 순차 편집 권고)

#### Step 4: state.schema.json 1.1 — key·conditional 추가
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 스키마
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/schema/state.schema.json`
- **작업 내용**: schema_version const→enum[1.0,1.1], rows[].items.properties에 key(pattern)·conditional(boolean) 선택 필드 추가(§3.2.2). required 미추가.
- **완료 기준**: key 있는 1.1 + key 없는 1.0 모두 유효
- **테스트**: TS-008, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 3 (동일 파일)

#### Step 5: state_tool.py — build_rows_from_pipeline_json + init 분기
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: `build_rows_from_pipeline_json`(key·conditional 영속, agentic na 규칙 재사용), cmd_init `.json`/`.md` 확장자 분기 + stderr deprecation 경고(§3.2.2)
- **완료 기준**: json init → key 전 행 존재, md init → 기존 결과 + 경고 1줄
- **테스트**: TS-006, TS-007, TS-010
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 4

#### Step 6: state_tool.py — resolve_row_index + 주소 플래그 + action-step
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: `resolve_row_index` 신설, mark/advance/block/add-row 호출부 교체, `--task-step`/`--task-step-id`/deprecated `--row`(required 해제)/`--after-task-step`, `--action-step` 별칭, ERROR_CODES 3종(addr_required/conflict/not_found) 추가(§3.3.2)
- **완료 기준**: 3주소 동일 행 해석 일치, conflict/required/not_found 구분 방출, `--action-step`≡`--step`
- **테스트**: TS-011~TS-017
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 7: state_tool.py — add-row --key
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: `_auto_row_key`(전체 스캔 유일성), cmd_add_row `--key` 처리(형식·중복 검증), ERROR_CODES 2종 추가(§3.4.2)
- **완료 기준**: --key 지정·자동 생성·중복 거부 동작, 기존 key 불변
- **테스트**: TS-018~TS-021
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 8: 그룹 A 4종 pipeline.json 생성
- [ ] 완료
- **소속 기능**: F-006
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe}/references/pipeline.json`
- **작업 내용**: §3.6.2 전문(全文) 그대로 4파일 생성(opp9/opd15/opds10/opdw9, opdw 3~5 conditional, slug 체계 적용)
- **완료 기준**: 4종 모두 `spec-validate` ok:true + init 실증 행 수 일치
- **테스트**: TS-024~TS-027
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 5

#### Step 9: 그룹 A 4종 SKILL.md 전환
- [ ] 완료
- **소속 기능**: F-006
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe}/SKILL.md`
- **작업 내용**: "STATE.md 도메인 치환값" 섹션 `--rows-from` 경로 `.md`→`references/pipeline.json`, 표는 미러+편집금지 안내로 축소(폴백 위해 존치), 변경이력 표 행 추가(태스크 070)
- **완료 기준**: 4종 init 예시가 json 경로 지시 + 변경이력 갱신
- **테스트**: TS-025 (경로 실증)
- **실행 방법**: sub-agent
- **의존**: Step 8

#### Step 10: 테스트 보강 + 회귀
- [ ] 완료
- **소속 기능**: F-007
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: §3.7.2 신규 클래스 9종 추가(기존 무변경), make_args defaults 확장. DEC-3 실행기로 전체 PASS 확인.
- **완료 기준**: 기존 무수정 PASS + 신규 케이스 PASS
- **테스트**: TS-028~TS-030
- **실행 방법**: sub-agent
- **의존**: Step 1~9

#### Step 11: README.md 갱신 (state-tool 도구 문서)
- [ ] 완료
- **소속 기능**: F-001~F-005
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/README.md`
- **작업 내용**: 신규 서브명령(spec-validate)·플래그(--task-step/--task-step-id/--action-step/add-row --key)·에러 코드 카탈로그 반영, 변경이력 행 추가(태스크 070)
- **완료 기준**: 서브명령 10종·신규 에러 코드가 README에 반영
- **테스트**: 산출물 검사
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 12: docs/CONVENTIONS.md State 관리 절 갱신
- [ ] 완료
- **소속 기능**: F-003 (새 규칙 도입)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/CONVENTIONS.md`
- **작업 내용**: §State 관리(`:183-187`)에 "행 주소는 `--task-step` key 우선(--row deprecated)" 규칙 1줄 추가 (→ D-12)
- **완료 기준**: 신규 주소 규칙이 CONVENTIONS.md에 명문화
- **테스트**: 산출물 검사
- **실행 방법**: direct
- **의존**: Step 6

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7 | 모두 `state_tool.py` 또는 `state.schema.json` 동일 파일 순차 편집 — 충돌 방지 위해 단일 에이전트 순차 |
| Step 1 ∥ Step 3 | pipeline-spec.schema.json vs state.schema.json/enum — 독립 파일이나 Step2와 파일 겹쳐 순차 권고 |
| Step 8 ∥ Step 6·7 | pipeline.json은 state_tool.py와 독립 — 단 Step2·5(검증·로딩) 완료 후 실증 가능 |
| Step 9 → Step 8 후 | SKILL.md 경로 교체는 json 존재 전제 |
| Step 10 최후 | 전 기능 통합 회귀 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | spec-validate 정상/위반 구분 | TS-002~005 | 구분된 violation 코드 방출 |
| F-002 | json 로딩 key 영속 + 스키마 1.1/1.0 병행 | TS-006~010 | key 전 행 존재, 양 버전 유효 |
| F-003 | 3주소 일치 + conflict/required 강제 + action-step 별칭 | TS-011~017 | 동일 행 해석, 구분 에러, 진행률 동일 |
| F-004 | --key 지정·자동생성·유일성 | TS-018~021 | 충돌 없는 자동 key, 중복 거부 |
| F-005 | opdd init 거부 해소 | TS-022~023 | enum 에러 없이 동작 |
| F-006 | 4종 spec-validate + init 실증 | TS-024~027 | 행 수 9/15/10/9, key 전 행 존재 |
| F-007 | 기존 무수정 PASS + 신규 PASS | TS-028~030 | 회귀 0 + 별칭 하위호환 증명 |

### 5.2 회귀 테스트
- [ ] `--row`·`--step` 별칭이 기존과 동일 동작 (TS-012, TS-016)
- [ ] `.md` `--rows-from` 파싱 폴백 유지 (TS-007, TS-030)
- [ ] key 없는 레거시 1.0 state.json validate 통과 (TS-009)
- [ ] CLOSE 게이트·명확화 훅 회귀 0 (TS-017)
- [ ] 기존 테스트 케이스 전체 무수정 PASS (TS-028)

### 5.3 코드/문서 품질
- [ ] 표준 라이브러리만 사용(서드파티 import 0, T-11)
- [ ] 신규 에러 코드가 ERROR_CODES 딕셔너리에 등록되어 err() 자동 완성
- [ ] 변경 파일(4종 SKILL.md·README.md·CONVENTIONS.md) 변경이력 표 행 추가(태스크 070)
- [ ] pipeline.json 4종이 pipeline-spec.schema.json 구조 부합

### 5.4 보안
- [ ] 코드에 하드코딩된 토큰/시크릿 없음 (내부 CLI 도구, 신규 시크릿 도입 없음)
- [ ] spec_path·rows_from 경로 입력 처리 시 예외(파일 부재/파싱 실패)가 err()로 안전 종료(크래시 없음)
- [ ] `~/.opal/` 배포 파일 직접 수정 없음 — 프로젝트 소스만 변경

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 12개 | 복잡 |
| 변경 파일 수 | 12개(신규 5 + 수정 7) | 복잡 |
| 모듈 범위 | 다중(도구·스키마·스킬·테스트·문서) | 복잡 |
| 작업 유형 | 대규모 개선(신규 서브명령·주소 체계) | 복잡 |
| 외부 의존성 | 없음(표준 라이브러리만) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- 파일 충돌 방지 원칙상 `state_tool.py`·`state.schema.json`을 만지는 Step(2,3,4,5,6,7)은 **단일 opal-task-agent 순차**로 배치(동일 파일 다중 편집 충돌 회피).
- Batch 1: Step 1(pipeline-spec.schema.json — 독립)
- Batch 2: Step 2→3→4→5→6→7 (state_tool.py/state.schema.json 순차 체인)
- Batch 3: Step 8→9 (pipeline.json 4종 → SKILL.md 4종)
- Batch 4: Step 10 (테스트 통합 회귀)
- Batch 5: Step 11(README), Step 12(CONVENTIONS — PM 직접)

```
Batch1: [S1]
Batch2: [S2→S3→S4→S5→S6→S7]   (S1 완료 후 S2 시작)
Batch3: [S8→S9]                (S5 완료 후 S8 시작 가능)
Batch4: [S10]                  (S1~S9 완료 후)
Batch5: [S11] [S12]            (S7/S6 완료 후)
```

### C-2. 스킬 요구사항
- 본 태스크는 op-dev-execute 표준 흐름으로 충분 — 신규 스킬 갭 없음. state-tool 확장은 인라인 지침(본 PLAN §3)으로 커버.

### C-3. 도구 요구사항
- CLI: `~/.opal/tools/state-tool/run.sh`(배포본 — 본 태스크 state 관리용), `~/.opal/.venv/bin/python`(테스트 실행, DEC-3).
- MCP: 불요(→ D-1 §6.3).
- 패키지: 신규 설치 없음(표준 라이브러리).

### C-4. 테스트 전략
- 기능 테스트: `test_state_tool.py` 신규 클래스 9종 — 패턴 1(직접 호출) + 패턴 2(subprocess CLI, argparse 제약 검증).
- 회귀 테스트: DEC-3 실행 명령으로 전체 스위트. 기존 케이스 무수정.
- 코드 품질: 서드파티 import 스캔(0 확인), ERROR_CODES 등록 확인.
- 보안: 경로 입력 예외 안전 종료, 배포 경계 준수.
- 실행 명령(DEC-3):
  - 기본: `~/.opal/.venv/bin/python -m unittest discover -s opal/tools/state-tool/tests -p 'test_*.py'`
  - 호환: `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/`

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 언어 | Python 3.14 (표준 라이브러리만) | op-dev-execute 인라인 지침 |
| 테스트 | unittest (pytest 호환 실행) | DEC-3 |
| 스키마 | JSON Schema Draft-07 (문서 SSOT) | DEC-2 |
| 셸 래퍼 | bash (run.sh 무변경) | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 표준 라이브러리 내부 도구 확장 — 외부 문서 조회 불요 (→ D-1 §6.3) |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | ANALYSIS.md | `tasks/070-260720-opd-태스크스텝-키주소-1차/ANALYSIS.md` | 코드 분석·리스크 R-A1~A7·발견사항 SSOT |
| D-2 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 수정 대상 본체(1,937줄) — 함수 시그니처·argparse 근거 |
| D-3 | 설계 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | 1.1 승격 대상 |
| D-4 | 설계 | state-tool README | `opal/tools/state-tool/README.md` | 서브명령·에러 카탈로그 SSOT — 갱신 대상 |
| D-5 | 설계 | 원 설계 SSOT(PLAN 134) | git `4af79ae:tasks/134-260501-opp-pipeline-state-tool/PLAN.md` | §2.1~§2.21 기존 설계 — 작업트리 부재, git show 조회(R-A1) |
| D-6 | 설계 | opdd SKILL.md | `opal/skills/opal-pilot-data-design/SKILL.md` | 드리프트 근거(DDL/MIGRATION 단계) |
| D-7 | 소스 | opp SKILL.md | `opal/skills/opal-pilot-project/SKILL.md:153-179` | 그룹 A 전환 대상 — 9행 |
| D-8 | 소스 | opd SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md:269-312` | 그룹 A 전환 대상 — 15행 |
| D-9 | 소스 | opds SKILL.md | `opal/skills/opal-pilot-dev-short/SKILL.md:238-276` | 그룹 A 전환 대상 — 10행 |
| D-10 | 소스 | opdw SKILL.md | `opal/skills/opal-pilot-dev-wireframe/SKILL.md:181-219` | 그룹 A 전환 대상 — 9행, 조건부 3~5 |
| D-11 | 소스 | 기존 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | 회귀 기준선(3,618줄) |
| D-12 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md:183-193` | State 관리·도구 우선 원칙 SSOT — 갱신 대상 |
| D-13 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 규칙 하네스 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1. 유형: 기획/설계/소스/외부.

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | `--row` required 해제로 무주소 호출이 조용히 통과 | F-003 | P1 | `resolve_row_index`가 `task_step_addr_required` 강제(H-2), subprocess 테스트 TS-014 |
| R-2 | additionalProperties:false + key 미등록 시 스키마 위반 | F-002 | P1 | key·conditional을 properties에 명시 등록(H-3), TS-008/009 |
| R-3 | 자동 key가 기존 동적 행과 충돌 | F-004 | P1 | `_auto_row_key` 전체 rows 스캔 유일성(H-5), TS-020 |
| R-4 | DDL/MIGRATION 슬래시가 향후 key 검증서 위반 유발 | F-005 | P1 | 1차 enum 등록만, slug 치환은 opdd 전환(2차)로 이연(H-6) |
| R-5 | conditional 자동화 범위 모호 | F-006 | P2 | DEC-1로 순수 메타데이터 확정(자동 na 없음), TS-027 |
| R-6 | 원 설계 SSOT 작업트리 부재 | F-006 | P2 | git show 4af79ae 조회(H-8, R-A1) |
| R-7 | pytest 미설치 실행 실패 | F-007 | P2 | DEC-3 unittest discover 대체(R-A6) |
| R-8 | SKILL.md 표 삭제 시 .md 폴백 회귀 | F-006 | P2 | 표 존치 + 미러 안내(폴백 하위호환 유지) |

> **용어 일관성 검토(citation-rules §7)**: `item`(한글 표시명, 예 "사용자 확인") ↔ `key`(영문 slug, 예 `user_confirm`)는 **의도된 분리**(item=화면 표시, key=주소)이며 불일치 리스크 아님 — CLOSE 게이트·명확화 훅이 item 한글 값에 의존하므로 slug 변경과 무관(→ D-1 §5 R-A5). decision_required 에스컬레이션 대상 없음.
