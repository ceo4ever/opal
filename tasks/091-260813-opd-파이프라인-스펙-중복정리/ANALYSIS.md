# ANALYSIS: 파이프라인 스펙 중복정리 — SKILL.md 감량 + PM Gate SSOT 승격

> 작성일: 2026-08-13 | 입력: TASK.md | 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| 1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | `cmd_mark`·`build_rows_from_pipeline_json`·`validate_pipeline_spec` 전문 실측 (A-1/A-2) |
| 2 | 설계 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | rows[] `additionalProperties:false` 확인 (A-2) |
| 3 | 설계 | pipeline-spec.schema.json | `opal/tools/state-tool/schema/pipeline-spec.schema.json` | task_steps[] 현행 허용 필드, pm_gate 문서 스키마 확인 (A-2/A-3) |
| 4 | 소스 | pipeline.json × 10 | `opal/skills/opal-pilot-*/references/pipeline.json` | pm_gate 보유/미보유 실측, artifacts 토큰 실측 (A-3/A-6) |
| 5 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | 테스트 클래스·헬퍼·RED-first 관례 실측 (A-4) |
| 6 | 소스 | run.sh | `opal/tools/state-tool/run.sh` | subprocess 실호출 경로 확인 (A-4) |
| 7 | 소스 | opal-convention-checker/AGENT.md | `opal/agents/opal-convention-checker/AGENT.md` | GC-CONVENTION-*.md 산출 규칙(타임스탬프+요소 접미사) (A-3) |
| 8 | 소스 | state_adapter.py / models.py | `dashboard/backend/adapters/state_adapter.py`, `dashboard/backend/models.py` | 외부 소비처 필드 의존성 확인 (A-5) |
| 9 | 소스 | todo_mirror_hook.py | `opal/tools/state-tool/todo_mirror_hook.py` | PostToolUse hook의 stdout 키 화이트리스트 확인 (A-5) |
| 10 | 설계 | pilot SKILL.md × 10 | `opal/skills/opal-pilot-*/SKILL.md` | 미러 표/`--row`/`행 N`/PM Gate 절/치환값 절 정밀 실측 (A-6) |
| 11 | 설계 | 090 DONE.md | `tasks/090-260813-opds-파이프라인-스펙-마이그레이션/DONE.md` | 이월 4건 원출처 |
| 12 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` §State 관리 (`docs/CONVENTIONS.md:224-230`) | `--row` deprecated 규정 |
| 13 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` §4 | RED-first 테스트 배치 원칙(공개 인터페이스 검증) |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/state-tool/state_tool.py` | mark/init/validate 로직 본체 | Yes — R-9~R-11 | `cmd_mark:1383-1553`, `build_rows_from_pipeline_json:937-972`, `validate_pipeline_spec:875-934` |
| `opal/tools/state-tool/schema/pipeline-spec.schema.json` | task_steps[] 문서 스키마 (비집행) | Yes — `gate` 필드 추가 | `pipeline-spec.schema.json:20-47` |
| `opal/tools/state-tool/schema/state.schema.json` | state.json 집행 스키마(문서, jsonschema 미연동) | PLAN 결정에 따라 Yes/No | `state.schema.json:44-113`(rows 항목 `additionalProperties:false`) |
| `opal/tools/state-tool/tests/test_state_tool.py` | 단위 테스트 SSOT | Yes — RED-first 신규 클래스 | 5560줄, 269 tests |
| `opal/tools/state-tool/todo_mirror_hook.py` | mark stdout → 세션 주입 hook | 선택적(체크리스트 자동 주입 원할 시) | `todo_mirror_hook.py:64-82`(`_extract_payload` 키 화이트리스트) |
| `opal/skills/opal-pilot-*/references/pipeline.json` × 10 | 행 구성 + (일부) pm_gate SSOT | Yes — R-9 이관 | 개별 파일, §A-3/A-6 표 참조 |
| `opal/skills/opal-pilot-*/SKILL.md` × 10 | 미러 표·`--row`·`행 N`·PM Gate 절 | Yes — R-1~R-8, R-12 | §A-6 표 참조 |
| `opal/skills/opal-pilot-data-design/SKILL.md` | R-1 정정 대상 | Yes | `:241`(아래 표를 파싱), `:242`(줄번호 인용 오류) |
| `opal/skills/opal-pilot-sdd/SKILL.md` | R-1 정정 대상 | Yes | `:386`, `:399`(위 SSOT 표를 기준으로) |
| `opal/core/references/harness/state-template.md` | R-2 정정 대상 | Yes | `:94` |
| `opal/core/references/harness/qa-standards.md` | R-2 정정 대상 | Yes | `:46` |
| `dashboard/backend/adapters/state_adapter.py` | state-tool show 소비처 | No (read-only, 필드 무접촉) | 전문 55줄 |
| `dashboard/backend/models.py` | `PipelineRow` Pydantic 모델 | No (필드 명시적 선별 생성) | `:136-141` |

### 1.2 아키텍처 패턴

- **SSOT 계층 분리 확립(070/090)**: `references/pipeline.json`(task_steps[])이 행 구성의 유일한 원천이고, `state_tool.py`는 이를 `build_rows_from_pipeline_json()`으로 소비해 `state.json`을 만든다(`state_tool.py:937-972`). pilot SKILL.md의 미러 표는 "사람 열람용"이라고 각 pilot이 스스로 주석 처리해 두었다(예: `opal-pilot-dev/SKILL.md:282`).
- **가드 체인 패턴**: `cmd_mark`는 상태를 변경하기 전에 여러 독립 가드 함수를 순차 호출하고 각 가드는 `err()`로 즉시 종료하거나(예외 아님, `sys.exit`) 조용히 반환한다(`resolve_row_index→worker 권한 게이트→check_stage_transition_guard→check_close_gate→_run_clarification_hook→semi-agentic auto-pass 거부`, `state_tool.py:1401-1438`). 신규 게이트도 이 체인에 합류하는 것이 기존 패턴과 정합적이다.
- **stdout 전용 확장 패턴(076/088)**: `todo_mirror`(076)·`history_link`(088)는 `state.json`에 저장하지 않고 `ok()` 응답에만 추가되는 페이로드다. `build_todo_mirror()` docstring이 이 이유를 명시한다 — "state.schema.json §root additionalProperties:false 위반 회피"(`state_tool.py:458`). 반대로 `key`·`conditional`은 070에서 **state.json에 실제로 영속**되는 필드로 추가됐다(`state_tool.py:950-962`, `state.schema.json:102-110`). 즉 이 코드베이스에는 "행에 귀속된 정적 정의값은 영속(key/conditional 패턴)" vs "매 호출 파생값은 stdout 전용(todo_mirror 패턴)" 두 가지 확립된 선례가 공존한다 — `gate`가 전자에 가깝다(§A-2 상세).
- **주소 체계**: 070부터 `--task-step <key>` 우선, `--task-step-id <n>` 숫자 폴백, `--row <n>`는 deprecated(`state_tool.py:2390-2395`, `docs/CONVENTIONS.md:228`). `resolve_row_index()`(`state_tool.py:407-451`)가 3주소를 단일 인덱스로 해석한다.

### 1.3 의존성 맵

```
opal-pilot-*/SKILL.md (10) ──rows-from──> state_tool.py:build_rows_from_pipeline_json()
opal-pilot-*/references/pipeline.json (10) ──load_pipeline_spec/validate_pipeline_spec──> build_rows_from_pipeline_json()
state_tool.py:cmd_mark() ──save_state_json──> {task_path}/state.json
                         ──sync_state_md──> {task_path}/STATE.md
                         ──ok() stdout──> Claude Code Bash 도구 출력
                                          └─ todo_mirror_hook.py(PostToolUse) ──키 화이트리스트 추출("todo_mirror","history_link")──> 세션 additionalContext
dashboard/backend/adapters/state_adapter.py ──subprocess "show --format json"──> state_tool.py:cmd_show()
dashboard/backend/models.py:PipelineRow(row,stage,status,updated_at) ← routers/tasks.py에서 필드별 명시 생성(**row 언패킹 없음)
```

의존성 방향은 전부 pipeline.json/state.json → 소비처로 단방향이며, `gate` 필드 추가가 상류(pipeline.json 스키마)에서 하류(state.json 스키마 → dashboard) 순으로 전파된다. dashboard 쪽은 명시적 필드 선별 생성이라 이 전파 체인이 거기서 끊긴다(§A-5).

### 1.4 테스트 현황

- `opal/tools/state-tool/tests/test_state_tool.py` 269 tests + `test_todo_mirror_hook.py` 15 tests = **284 tests, 실행 결과 전부 PASS**(§A-4 실측, 재현 명령 포함).
- 44개 TestCase 클래스, 기능 단위로 클래스를 신설하는 관례가 070/072/074/076/088 전부에서 일관됨(§A-4 상세).
- RED-first 트랙 적용 근거: `opal/core/references/harness/red-first.md` §1.5 — "비즈니스 로직·API 계약"은 RED-first 강제 대상이며, mark 게이트 소비는 이 분류에 해당한다.

---

## 2. 외부 조사 결과

해당 없음 — 이 태스크는 순수 내부 코드베이스(OPAL 프레임워크 자체) 정리 작업이며 신규 외부 라이브러리/API 도입이 없다.

---

## 3. 영향 범위

### 3.1 직접 영향

- `opal/tools/state-tool/state_tool.py` — `cmd_mark`, `validate_pipeline_spec`, `build_rows_from_pipeline_json`, `ERROR_CODES`
- `opal/tools/state-tool/schema/pipeline-spec.schema.json` — `task_steps[].gate` 속성 추가(§A-2)
- `opal/tools/state-tool/schema/state.schema.json` — PLAN이 "영속" 방향을 택할 경우 `rows[].gate` 속성 추가 필요(§A-2)
- `opal/skills/opal-pilot-*/SKILL.md` × 10, `references/pipeline.json` × 10 — 본문 감량 + gate 이관
- `opal/core/references/harness/state-template.md:94`, `opal/core/references/harness/qa-standards.md:46` — 미러 표 의무 서술 정정

### 3.2 간접 영향

- `opal/tools/state-tool/tests/test_state_tool.py` — 신규 RED-first 클래스 추가(기존 284건 회귀 보호 포함)
- `opal/tools/state-tool/todo_mirror_hook.py` — checklist stdout 세션 주입을 원하면 `_extract_payload` 키 확장 필요(§A-5, PLAN 결정 사항. 하지 않아도 Bash 도구 stdout 자체는 호출자에게 노출되므로 무발동이 곧 실패는 아님)
- `dashboard/backend` — **영향 없음**(§A-5 확정, `models.py:136-141` 명시적 필드 생성으로 신규 키 자동 무시)
- `~/.opal/` 배포본 전체 — install 재배포 대상(R-14)

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [x] API 인터페이스 변경 — `state-tool mark`의 ok() 응답에 신규 필드(checklist) 추가 가능성, `spec-validate`에 신규 violation 코드 추가
- [x] 설정/환경변수 변경 — 없음(JSON 스키마 파일 자체는 "설정"이 아닌 소스 코드로 취급)
- [ ] 빌드/배포 파이프라인 변경 — install-mac.sh 스크립트 자체 변경 없음(단순 재배포 대상 파일 추가뿐)

---

## 4. 핵심 발견 사항

1. **`pipeline-spec.schema.json`/`state.schema.json`은 실제로 집행되지 않는 문서 스키마다.** `state_tool.py`에 `import jsonschema`가 없고(`state_tool.py:17-25`), `load_pipeline_spec()`/`validate_pipeline_spec()`(`state_tool.py:864-934`) 모두 이 JSON 파일을 열지 않는다. 실제 검증은 순수 Python 조건문이다. 따라서 R-9/R-10의 "스키마 신설"은 **`validate_pipeline_spec()` 함수 수정이 본체**이고, `.schema.json` 파일 수정은 문서 동기화(비집행) 작업이다 — 이 구분을 PLAN 산정에 반영해야 한다.
2. **state.json에는 pipeline.json 원본 경로가 전혀 저장되지 않는다.** `cmd_init`에서 `args.rows_from`은 그 호출 프레임에서만 쓰이고 버려진다(`state_tool.py:1125-1133`). `mark` 시점에 pipeline.json을 다시 읽으려면 신규 CLI 인자나 skill→디렉토리 매핑 상수가 필요하다(현재 존재하지 않음, grep으로 미확인). 반대로 `key`/`conditional`은 init 시점에 row에 복사되어 state.json에 영속된다(`state_tool.py:950-962`) — `gate`도 이 선례를 따르는 것이 구조적으로 더 간단하다.
3. **`opgc`는 PM Gate 개념 자체가 없다.** pipeline.json에 `pm_gate` 키가 전무하고(다른 9종은 최소 `[]`는 존재) SKILL.md에도 "## PM Gate 점검 목록" 절이 없다(`opal-pilot-gc/SKILL.md` 헤딩 목록 확인). opgc의 게이트는 "완료 확인"(워커)·"사용자 확인"(REPORT)·"CLOSE 진입 게이트" 3종으로 이미 다른 메커니즘이 담당한다(`opal-pilot-gc/SKILL.md:249,309,347`). R-9의 "미보유 6종 이관"은 opgc에는 적용되지 않는다(이관할 원본이 없음).
4. **`opwt`(opal-pilot-write-tech)는 3모드 중 1모드만 pipeline.json에 반영되어 있다.** `references/pipeline.json`의 `meta.mode_label`은 `"작성"`이고 `task_steps[]`에 ANALYSIS 단계가 없다(`pipeline.json` 실측). 그런데 SKILL.md는 "수정"/"분석" 모드에서 ANALYSIS 단계 + 자체 PM Gate를 명시하고(`opal-pilot-write-tech/SKILL.md:208-255`), EXECUTE 단계도 배치별 동적 PM Gate/사용자 확인 행을 전제로 한다(`opal-pilot-write-tech/SKILL.md:324-335`, `--row <ANALYSIS_PM_Gate_N>`·`<EXECUTE_Batch_PM_Gate_N>` 등 플레이스홀더). 이 두 지점은 pipeline.json에 대응 `key`가 **존재하지 않는다** — R-4/R-5 좌표계 전환의 단순 치환으로는 해소되지 않는 구조적 공백이며 090이 D-1(행 구성 이관)에서 opwt를 "작성" 모드 단일 변형으로만 다뤘기 때문으로 추정된다. PLAN에서 반드시 처리 방침을 정해야 한다(§5 R-1).
5. **`GC-CONVENTION-*.md`는 파일명이 실행마다 달라지는 진짜 glob 대상이고, 실제로는 opgc(다른 파일럿)의 산출물이다.** `opal-convention-checker/AGENT.md:150-154`가 `{task_folder}/GC-CONVENTION-{timestamp}[-{scope}].md` 형식을 정의하며, 실제 태스크 폴더에 `GC-CONVENTION-2026-08-13T15-00-54.md`류의 파일이 다수 존재한다(`tasks/082-.../GC-CONVENTION-2026-08-03T15-00-54.md` 등, §A-3 표). `changed_files`는 파일이 아니라 EXECUTE 변경분의 논리적 집합이며, `cmd_verify --changed-files`(`state_tool.py:2481-2482`, `_match_test_files:2028-2040`)에 이미 "호출자가 목록을 CLI로 주입" 선례가 있다 — mark가 같은 패턴을 재사용할 수 있다.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-1 | opwt pipeline.json이 3모드 중 1모드만 반영 — ANALYSIS 단계·배치별 동적 게이트가 SSOT에 없어 `--row`→`--task-step` 치환 대상 key가 존재하지 않음 | 높음 | `opal-pilot-write-tech/SKILL.md:249,253,329,334`, `references/pipeline.json`(meta.stages에 ANALYSIS 없음) |
| R-2 | 게이트 검증을 `cmd_mark` 어디에 넣어도 088(`link_memory_history`)·017(다중 Step)·005(명확화)·G-13(CLOSE 게이트)과 순서 충돌 가능 — 특히 `--force` 시 다른 가드는 전부 우회되는데 게이트 아티팩트 검증도 우회할지 미정 | 중간 | `state_tool.py:640-641`(stage guard force bypass), `:697-698`(close gate force bypass) — 신규 게이트만 force 예외가 없으면 UX 비일관 |
| R-3 | `state.json` rows[]는 `additionalProperties:false` — `gate`를 영속하려면 스키마 추가가 스킵 불가능한 선행 조건(§A-2) | 중간 | `state.schema.json:47` |
| R-4 | `--row N` 실제 건수는 45건(비-변경이력)이며, TASK.md 배경 분석 §2의 46건과 다르다 — opsdd 변경이력 행(`:544`)에 포함된 리터럴 1건이 이중 집계됨(§A-6 상세) | 낮음(수치 정정) | `opal-pilot-sdd/SKILL.md:544` |
| R-5 | 산문 `행 N` 리터럴은 변경이력 제외 36건 + 변경이력 포함 49건 — R-5의 AC 문구("`행 [0-9]+` grep 0건")가 변경이력 배제를 명시하지 않아 문언대로 적용하면 불변 대상인 변경이력까지 손대야 하는 것으로 오독될 수 있음 | 낮음(AC 명확화 필요) | §A-6 표, `docs/CONVENTIONS.md`상 변경이력 불변 원칙과 상충 소지 |
| R-6 | oppd/oppl은 PM Gate 행은 있지만(id 5·8·11 / 11·14·17) SKILL.md에 artifacts/checklist 분해 표가 없음 — R-9 이관 시 opwt/opsdd/opdd(표 존재)와 달리 신규 저술이 필요 | 중간 | `opal-pilot-project-dev/SKILL.md:136-141`, `opal-pilot-project-loop/SKILL.md:131` |
| R-7 | `todo_mirror_hook.py`는 stdout JSON에서 미리 정의된 키(`todo_mirror`,`history_link`)만 추출한다 — checklist를 세션에 자동 주입하려면 이 파일도 확장해야 하며, 하지 않으면 stdout에는 찍히되 088 이전의 "결정론 주입" 수준에는 못 미침 | 낮음(기능 범위 결정 필요) | `todo_mirror_hook.py:64-82` |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python | 3(표준 라이브러리만, `state_tool.py:16-25`) |
| 언어 | Markdown | pilot SKILL.md, 하네스 참조 문서 |
| 데이터 | JSON Schema | draft-07(문서용, 비집행) |
| 테스트 | unittest + pytest 러너 | 284 tests(`test_state_tool.py` 269 + `test_todo_mirror_hook.py` 15) |
| 셸 | Bash | `run.sh` 래퍼 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| (해당 없음) | 이 태스크는 프레임워크 내부 도구/문서 정리이며 외부 스킬 도입 대상이 아님 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| (해당 없음) | 외부 라이브러리 조사 불필요 — 순수 내부 코드베이스 실측 |

---

## A-1. `state_tool.py` mark 경로 회귀 표면 (상세)

`cmd_mark`(`state_tool.py:1383-1553`) 실행 순서와 각 기존 기능의 정확한 위치:

| 순서 | 기능 | 위치(`state_tool.py`) | 종류 |
|------|------|----------------------|------|
| 1 | task_path/state 로드 | `:1386-1387` | 준비 |
| 2 | `--auto-pass`/`--owner` 배타(C-2) | `:1390-1391` | 가드(err) |
| 3 | `--as-worker`→`--worker-stage` 필수(C-3) | `:1394-1395` | 가드(err) |
| 4 | `--force`→`--note` 필수(C-4) | `:1398-1399` | 가드(err) |
| 5 | `resolve_row_index()` → row 확정 | `:1401-1405` | 준비 |
| 6 | 워커 권한 게이트(`worker_scope_violation`, §2.4/T-10) | `:1407-1418` | 가드(err, `--force`로 우회 가능·note에 기재) |
| 7 | **017** `check_stage_transition_guard()` — 다중 Step 조기 done 가드의 전제(단계 건너뛰기 차단) | `:1420-1424` (함수 본체 `:628-672`) | 가드(err, `force` 파라미터로 우회) |
| 8 | CLOSE 진입 게이트(`check_close_gate()`, §2.16 G-13) | `:1426-1428` (함수 본체 `:679-716`) | 가드(err, `force`로 우회하되 agentic auto-pass는 우회 불가) |
| 9 | **005** 명확화 게이트(`_run_clarification_hook()`) | `:1430-1432` | 가드(err) |
| 10 | semi-agentic pre-execute auto-pass 거부 | `:1434-1438` | 가드(err) |
| — | **← 검증 전용 구간 끝. 이하부터 실제 상태 변경(mutation) 시작.** | | |
| 11 | `now_str` 취득 | `:1440` | 준비 |
| 12 | **017** `--step N/M` 파싱 + 조기 done 가드(진행률 영속화, `row["step"]`) | `:1442-1462` | mutation |
| 13 | note 소유자 치환(054) | `:1464-1465` | mutation |
| 14 | owner 결정 | `:1467-1481` | mutation |
| 15 | `state["updated_at"]` | `:1483` | mutation |
| 16 | CLOSE 마지막 행 판정(G-6, `current_status="done"`) | `:1485-1498` | mutation |
| 17 | EXECUTE Step 진행 문구 | `:1500-1502` | mutation |
| 18 | **072** `_derive_next_action()` | `:1504-1505` | mutation |
| 19 | `save_state_json()` — **state.json 파일 쓰기(영속 경계)** | `:1507` | 영속 |
| 20 | TEST stage verify 훅(013, mock/evidence 검사) | `:1509-1519` | 후처리(err 가능 — 단, state.json은 이미 저장된 뒤) |
| 21 | decision/reason 로그 문자열 구성 | `:1521-1534` | 준비 |
| 22 | `sync_state_md()` — **STATE.md 파일 쓰기** | `:1536-1539` | 영속 |
| 23 | **088** `link_memory_history()` — CLOSE 마지막 행 완료 시에만, 예외 흡수·항상 ok:true | `:1541-1546` (함수 본체 `:575-627`) | 후처리(비차단) |
| 24 | **076** `ok()` 응답 — `build_todo_mirror()` 포함 | `:1548-1553` (함수 본체 `:453-488`) | 응답 |

**게이트 검증(artifacts 존재 확인) 삽입 후보 지점**: 순서 10(`:1438`) 직후 ~ 순서 11(`:1440`) 직전. 이유:
- 이 지점까지는 전부 "검증 실패 시 err()로 즉시 종료, 성공 시 상태는 아직 무변경" 구간이다. 여기 삽입하면 게이트 미충족 시 `save_state_json()`(`:1507`)이 전혀 호출되지 않아 **부분 상태 변경이 발생하지 않는다** — 기존 4개 가드(워커 권한/단계 전환/CLOSE 진입/명확화)와 동일한 불변식을 유지한다.
- 순서 7·8(017/088이 이미 얹힌 지점) **뒤**에 두면 안전하다 — 017의 다중 Step 로직(순서 12)은 상태 변경 로직이므로 그 앞에 있어야 게이트 실패 시 `row["step"]` 오염을 막는다.
- `--force` 우회 여부는 PLAN 결정 필요(§5 R-2) — 기존 가드 2종(순서 7·8)은 `force` 파라미터를 받아 조건부 스킵하므로, 신규 게이트도 동일 시그니처(`force=False`)를 받는 것이 일관적이다.

**checklist stdout 주입 삽입 후보 지점**: 순서 24(`:1548-1552`) `_ok_kwargs` 구성부. `todo_mirror`(076)·`history_link`(088)와 동일한 층 — `row.get("gate")`가 있으면 `_ok_kwargs["<필드명>"] = row["gate"]["checklist"]`를 조건부 추가하는 것이 기존 확장 패턴과 100% 동형이다.

---

## A-2. 게이트 정의를 읽으려면 무엇이 필요한가 (상세)

### 현재 `build_rows_from_pipeline_json()`이 state.json에 영속시키는 필드

`state_tool.py:948-971`에서 row 딕셔너리는 `row_id, stage, item, key, status, status_label, timestamp, owner, note`를 항상 채우고, `ts.get("conditional")`가 참일 때만 `conditional: True`를 추가한다(`:961-962`). **`gate`는 현재 전혀 복사되지 않는다** — `build_rows_from_pipeline_json()`은 `ts["key"]`만 참조하고 `ts.get("gate")`는 어디서도 읽지 않는다(전문 확인, `:937-972`).

### (a) state.json에 영속 vs (b) mark 때마다 pipeline.json 재로드 — 실제 제약 비교

| 축 | (a) init 시 영속 (key/conditional 선례 확장) | (b) mark 시 pipeline.json 재로드 |
|---|---|---|
| 스키마 변경 필요성 | **필수** — `state.schema.json:44-113`의 rows 항목이 `additionalProperties:false`(`:47`)라 `gate` 미등록 시 스키마 검증 위반. 등록은 `key`(:102-106)/`conditional`(:107-110) 옆에 속성 하나 추가하는 낮은 난이도 변경 | **불필요** — state.json 스키마 무변경 |
| pipeline.json 경로를 mark 시점에 아는가 | 문제 없음 — init 시점에 이미 알고 있음(`args.rows_from`) | **불가능(현재 코드 기준)** — `cmd_init`은 `args.rows_from`을 어떤 형태로도 state.json에 저장하지 않는다(`:1122-1169` 전수 확인, `spec_path`/`rows_from`/`source` 필드 grep 결과 0건). skill enum→pilot 디렉토리 매핑 상수도 없음(`opal-pilot-dev` 등 문자열이 `state_tool.py` 안에 존재하지 않음, grep 결과 070 주석 1건뿐). 재로드하려면 (b-1) mark에 신규 `--spec-path` 인자를 추가해 매 호출마다 호출자가 주입하거나 (b-2) `skill` enum→디렉토리 매핑 테이블을 신설해야 한다 |
| 드리프트 특성 | pipeline.json이 init **이후** 수정되면 이미 생성된 state.json은 구 버전 gate를 들고 있다(정적 스냅샷) | 항상 최신 pipeline.json을 반영(매 mark마다 재검증) — 단, 076 `build_todo_mirror`가 이미 "비영속=최신성" 트레이드오프를 명시적으로 감내한 선례가 있음(`:453-458`) |
| 구현 난이도 | 낮음 — `build_rows_from_pipeline_json()` 1줄 추가(`row["gate"] = ts["gate"]` if 존재) + 스키마 1개 속성 | 중간~높음 — 신규 CLI 인자 전파(모든 pilot SKILL.md의 mark 호출 예시 46+건에 `--spec-path` 추가 필요) 또는 매핑 테이블 유지보수 부담 |
| 기존 선례와의 정합성 | `key`/`conditional`이 이미 이 패턴(정적 정의값의 init-time 복사)을 사용 중 — **직접 확장** | 선례 없음 — `spec-validate` 서브명령만 유일하게 pipeline.json을 직접 인자로 받는다(`:2466-2468`), mark류 명령은 전혀 받지 않음 |

### 스키마 파일 위치와 검증 지점

- `opal/tools/state-tool/schema/state.schema.json` — state.json 구조 문서. **비집행**(§4 핵심 발견 1 참조, `import jsonschema` 없음).
- `opal/tools/state-tool/schema/pipeline-spec.schema.json` — pipeline.json 구조 문서. 마찬가지로 비집행, `task_steps[].additionalProperties:false`(`:25`)이며 허용 속성은 `id/key/stage/item/conditional`뿐(`:26-32`) — **`gate` 추가 시 이 문서 스키마도 갱신해야 문서-코드 정합이 유지되지만, 갱신하지 않아도 `validate_pipeline_spec()` 동작에는 영향이 없다**(두 파일이 결합되어 있지 않음).
- 실제 검증 지점은 유일하게 `validate_pipeline_spec()`(`state_tool.py:875-934`, 순수 Python) — R-10의 실질 구현 대상.

**결론(사실 제시, 선택은 PLAN)**: (a) 영속 경로가 스키마 변경 1건 + 함수 1줄 확장으로 끝나는 반면, (b) 재로드 경로는 상태 비저장 원칙(mark는 원래 pipeline.json을 몰라도 됨)을 깨고 신규 인자 전파를 모든 pilot SKILL.md에 요구한다. `key`/`conditional`이 이미 (a)의 선례이므로 코드베이스 관성은 (a) 쪽에 있다.

---

## A-3. artifacts 토큰 3종 처리 비교 (상세)

### 실측: artifacts 토큰 7종 전량 (10 pilot pm_gate 배열 스캔)

| 토큰 | 등장 pilot | 검증 성격 |
|------|-----------|----------|
| `TASK.md` | opd, opds, opp | 태스크 폴더 기준 정적 파일명 — `pathlib.Path(task_path)/artifact` 존재 확인으로 충분 |
| `PLAN.md` | opd, opds, opp | 동일 |
| `ANALYSIS.md` | opd | 동일 |
| `TEST-SCENARIO.md` | opd, opds | 동일 |
| `wireframe.md` | opdw | 동일 |
| `GC-CONVENTION-*.md` | opds, opdw, opp, opd(TEST 단계) | **glob 패턴** — 아래 상세 |
| `changed_files` | opdw | **경로 아님, 논리 개념** — 아래 상세 |

### `GC-CONVENTION-*.md` 실측

- 산출 규칙 SSOT: `opal/agents/opal-convention-checker/AGENT.md:150-154` — `{task_folder}/GC-CONVENTION-{file_suffix}.md`, `scope=="all"` 또는 단일 호출 시 `{timestamp}`(예: `GC-CONVENTION-2026-05-08T14-32-18.md`), 특정 영역 지정 시 `{scope}-{timestamp}`.
- `opal-pilot-gc/SKILL.md:247`은 요소가 여러 개일 때 `-{요소명}` 접미사 추가를 명시(`GC-CONVENTION-{ts}-backend.md` 등) — **파일명이 실행마다·요소마다 달라지므로 정적 문자열 존재 확인이 원천적으로 불성립**.
- 실물 확인(레포 전역 검색): `tasks/082-260803-.../GC-CONVENTION-2026-08-03T15-00-54.md`, `tasks/backup/070-260720-.../GC-CONVENTION-260720.md` 등 **타임스탬프 표기 형식조차 시기별로 4종 이상 갈라져 있다**(`YYYY-MM-DDTHH-MM-SS`, `YYMMDD`, `YYMMDD-HHmm`, `YYYYMMDDHHmm`) — 고정 포맷 정규식 매칭도 위험하다는 뜻이며, `*.md` glob이 사실상 유일하게 안전한 매칭 방식이다.
- 생성 주체가 **다른 파일럿(opgc)**이라는 점도 특이하다 — opd/opds/opdw/opp가 자기 TEST/EXECUTE 게이트에서 opgc 산출물을 아티팩트로 참조한다. 이는 이미 코드베이스에 "다른 pilot이 만든 파일을 내 게이트가 확인" 관계가 있다는 뜻이고, mark 게이트의 존재 확인 로직이 task_path 기준 상대경로 glob이면 pilot 경계와 무관하게 동작하므로 문제 없다.

### `changed_files` 실측

- `state_tool.py`의 유일한 선례는 `cmd_verify --changed-files`(`nargs="*"`, `:2481-2482`)로, **호출자가 CLI 인자로 파일 목록을 명시적으로 주입**하고 `_match_test_files()`(`:2028-2040`, `fnmatch` 사용)가 이를 test_globs와 대조한다.
- pm_gate의 `changed_files`는 이런 명시적 목록이 아니라 "EXECUTE 단계에서 무엇이 바뀌었는가"라는 **암묵적 개념**이다 — state-tool은 git이나 파일시스템 diff에 접근하지 않으므로 자체적으로 이 목록을 산출할 수 없다(코드에 git 관련 import/subprocess 호출 없음, `state_tool.py` 전문 import 목록 `:17-25` 확인).
- 따라서 `changed_files`를 존재-검증 가능한 아티팩트로 만들려면 (i) mark에 `--changed-files` 인자를 신설해 verify와 동일하게 호출자 주입을 받거나 (ii) 검증 대상에서 제외해 checklist(체크리스트, 판단 위임)로 강등해야 한다. state-tool 자체로 파일 존재를 확인하는 방식은 이 토큰에는 적용할 수 없다.

### 3안 비교표

| 안 | 내용 | 코드 난이도 | 부작용 |
|---|------|------|--------|
| ① 스키마에서 검증 대상/비대상을 타입으로 분리 | `gate.artifacts`를 문자열 배열이 아니라 `{path: [...], glob: [...], external: [...]}` 같은 타입 구분 구조로 재정의 | 높음 — `validate_pipeline_spec()`·마크 시점 검증 로직·10개 pipeline.json 전부 구조 변경 | 표현력은 가장 높지만 스키마 복잡도 증가, 090이 이미 "행 구성 단순화"를 지향한 방향과 반대 |
| ② glob만 지원하고 `changed_files`는 checklist로 강등 | `artifacts`는 문자열 배열 유지, 값 자체가 `*`를 포함하면 `pathlib.Path(task_path).glob()`으로 판정, 존재 검증이 불가능한 `changed_files`는 pm_gate 이관 시 `artifacts`에서 빼고 `checklist`에 병합 | 낮음 — `fnmatch`/`pathlib.glob` 기존 이디엄 재사용(§핵심발견 5), pipeline.json 1개 필드(opdw EXECUTE) 소폭 수정 | `changed_files`가 "차단"에서 "주입만"으로 격하 — C-3의 "결정론 판정 가능한 지점만 차단" 원칙과 오히려 더 정합적 |
| ③ 비-경로 토큰은 비차단 통과 | `artifacts` 배열의 각 항목을 파일 존재 시도, 실패해도 `changed_files`처럼 알 수 없는 항목은 경고만 하고 mark는 통과 | 낮음 | "차단"이 목적인 R-11의 취지를 일부 약화 — 다만 glob 대상(`GC-CONVENTION-*.md`)까지 함께 비차단 처리하면 C-3가 요구하는 "결정론 차단"이 무력화될 위험 |

**중립적 관찰**: ②는 `GC-CONVENTION-*.md`(glob, 결정론 차단 가능)와 `changed_files`(논리 개념, 차단 불가능)의 실측된 성격 차이를 정확히 반영하며 기존 `fnmatch`/`glob` 이디엄을 재사용해 코드 난이도가 가장 낮다. ①은 가장 표현력이 높지만 090의 단순화 방향과 충돌한다. ③은 가장 구현이 쉽지만 두 토큰의 성격 차이(glob은 결정론 판정 가능, changed_files는 불가능)를 뭉개 C-3 원칙을 약화시킨다. 최종 선택은 PLAN에서 한다.

---

## A-4. 테스트 자산 현황 (상세)

### 실행 결과 (실제로 실행해서 확인)

```
$ cd opal/tools/state-tool && python3 -m pytest tests/ -q
........................................................................ [ 25%]
.................................................................... [ 49%]
..................................................................... [ 73%]
......................................................... [ 93%]
..................                                                       [100%]
284 passed, 22 subtests passed in 6.23s
```

`--collect-only` 재확인: `test_state_tool.py` 269 tests + `test_todo_mirror_hook.py` 15 tests = 284 tests. **전건 PASS.**

### 테스트 클래스 목록 (`test_state_tool.py`, 44개)

`TestInit, TestShow, TestAdvance, TestMark, TestBlock, TestValidate, TestAddRow, TestStatus, TestGatePass, TestErrorCodes, TestG7StatusTransitions, TestG10GatePass, TestG12UserConfirmation, TestG13CloseGate, TestG14G15DecisionLog, TestBasicScenarios, TestImportPreservesKeys, TestFreeTextPreservation, TestNextActionAutoDerive, TestConflictConstraints, TestRowsFrom, TestErrorCodesCompleteness, TestVerify, TestAddRowSchemaValidate, TestStageTransitionGuard, TestNewStandardRowStructure, TestGatePassDeprecation, TestStandardItemsConstants, TestRedFirst, TestMultiStepDoneGuard, TestClarificationGate, TestOwnerNamePlaceholder, TestOpplSkillInit, TestSchemaModeEnumSemiAgentic, TestPipelineSpecValidate, TestPipelineJsonInit, TestStateSchema11Compat, TestTaskStepAddressing, TestActionStepRename, TestAddRowKey, TestOpddEnumDrift, TestGroupAPipelineSpecs, TestBackwardCompatAliases, TestTodoMirror, TestCloseHistoryLink`(`state_tool.py:146-5335` 순서대로 등장).

관례: **기능 단위로 신규 TestCase 클래스를 만든다**(070→9개 신설, 072→`TestNextActionAutoDerive`, 074→`TestImportPreservesKeys`, 076→`TestTodoMirror`, 088→`TestCloseHistoryLink`). 클래스명은 `Test{FeatureName}` 패턴이며 파일 최하단에 시간순으로 누적된다.

### 실행 방법 / 두 가지 호출 패턴

| 패턴 | 헬퍼 | 용도 | 근거 |
|------|------|------|------|
| 직접 호출 | `BaseTestCase._call_cmd(fn, args)`(`:159-175`), 070계열 `_call070(fn, args)`(`:4200-4215`) | `cmd_*` 함수를 stdout 캡처로 직접 호출 — 내부 로직·다수 케이스 조합에 빠름 | red-first.md §4 "공개 인터페이스"는 `cmd_*` 함수 자체를 공개 표면으로 인정(내부 private 함수 직접 호출은 없음) |
| subprocess 실호출 | `_run070(args_list)`(`:4218-4228`) — `["bash", str(_RUN_SH)] + args_list` | argparse 레벨 제약(mutex, choices), CLI 계약 자체를 검증 | red-first.md §4 "mock/patch 금지" 명시 준수, 056/070/074 전례 |

두 패턴이 병행되며, 신규 기능도 "직접 호출로 로직 커버 + subprocess 1~2건으로 CLI 계약 확인" 조합이 관례다(`TestPipelineSpecValidate` 5개 메서드 중 4개 직접 호출·1개 subprocess, `:4378-4433`).

### 게이트 기능 RED-first 테스트 배치 제안

- **위치**: 파일 최하단(`TestCloseHistoryLink` 이후, `:5335-5560` 다음) — 088 선례와 동일하게 시간순 누적.
- **클래스명 제안**: `TestTaskStepGate`(또는 `TestPmGateConsumption`) — `state_steps[].gate` 소비 로직 전용.
- **베이스**: `BaseTestCase` 상속(`_init`/`_mark` 헬퍼 재사용 가능하도록 `rows_spec`에 `gate` 필드를 실은 커스텀 스펙 필요 — 단, 현재 `BaseTestCase._init()`은 `--rows-spec`(인라인 JSON, `build_rows_from_spec()`)을 쓰므로 `build_rows_from_spec()`도 `gate` 통과를 지원해야 함을 PLAN이 확인해야 한다. 070계열은 이 대신 `--rows-from`(`.json` 파일, `build_rows_from_pipeline_json()`) 경로를 쓰는 `TestPipelineJsonInit`류 패턴을 사용했다 — 게이트 테스트는 `build_rows_from_pipeline_json()` 경로이므로 이쪽 패턴이 더 적합).
- **`validate_pipeline_spec()` 확장분(R-10)**: 기존 `TestPipelineSpecValidate`(`:4359-4433`)에 케이스 추가가 자연스럽다(이미 "키 누락/타입 오류/빈 배열" 같은 violation 테스트 패턴을 보유).
- **`cmd_mark` 소비분(R-11)**: 신규 클래스에서 직접 호출(아티팩트 존재/부재 분기) + subprocess 1건(`gate_artifact_missing` exit code 확인)을 조합.

---

## A-5. 외부 소비처 영향 (상세)

### `dashboard/backend/adapters/state_adapter.py`

`state-tool show <task_dir> --format json`을 subprocess로 호출해 dict를 그대로 반환한다(`state_adapter.py:23-54`, 전문). **가공 없이 통과** — `gate` 필드가 state.json에 추가돼도 이 어댑터 코드는 영향 없음.

### `dashboard/backend/models.py` — `PipelineRow`

```python
class PipelineRow(BaseModel):
    row: int
    stage: str
    status: str
    updated_at: str = ""
```
(`models.py:136-141`) — `routers/tasks.py:254-260`에서 `PipelineRow(...)`를 필드별로 명시 생성한다(`**row` 언패킹 없음, grep 확인). **`gate`/`key`/`conditional` 등 state.json rows[]의 기존 확장 필드도 이미 무시되고 있으며, `gate` 추가도 동일하게 무영향**이다. Pydantic 모델이 `extra="forbid"`가 아니어도(기본 `ignore`) 애초에 raw dict를 모델에 통과시키지 않으므로 이 경로는 어떤 설정에서도 안전하다.

### 그 외 stdout/state.json 소비처 (hook 포함, 레포 전역 검색)

- `opal/tools/state-tool/todo_mirror_hook.py` — Claude Code **PostToolUse hook**(`opal/core/hooks/claude-hooks.json`에 등록, install이 배포)으로 `state-tool/run.sh {init,advance,mark,block}` 호출을 감지해 stdout에서 페이로드를 추출한다. `_extract_payload(stdout, key)`(`:64-82`)는 **키 화이트리스트 방식**이다 — `todo_mirror`·`history_link` 두 키만 추출하고 그 외 키(예: 게이트 checklist용 신규 키)는 **조용히 무시**한다(에러 없음, 그냥 세션 주입이 안 될 뿐). 즉 이 hook은 신규 필드 추가로 **깨지지 않지만**, checklist를 076/088처럼 "결정론 세션 주입"까지 원한다면 `extract_todo_mirror`/`extract_history_link` 옆에 신규 `extract_*` 함수와 `build_additional_context()` 확장이 필요하다(§5 R-7).
- `opal/tools/backlog-tool/backlog_tool.py`, `opal/tools/memory-tool/tests/test_memory_tool.py` — grep 히트는 각자의 `*.schema.json`/자체 상태 파일에 대한 것으로 state-tool의 state.json과는 무관(다른 도구의 동명 패턴).
- 그 외 `.claude/settings.json`, `.claude/settings.local.json`에 등록된 hook은 `todo_mirror_hook.py` 1건뿐(PostToolUse), state.json을 직접 파싱하는 별도 스크립트는 발견되지 않았다.

**결론**: dashboard는 완전 무영향, `todo_mirror_hook.py`는 무영향이지만 "체크리스트 자동 세션 주입"이라는 부가 기능을 원하면 확장 필요 — 이는 R-11의 "stdout에 반환"이라는 기본 요구사항과는 별개의 선택 사항이다(Bash 도구 stdout 자체는 어차피 호출자에게 그대로 보인다).

---

## A-6. pilot SKILL.md 감량 대상 정밀 실측 (상세, PM 실측 재검증)

### 미러 표 — 줄 범위 + 행수 (재검증 결과: **PM 수치와 일치, 134행 확정**)

| pilot | 파일:시작-끝(헤더~마지막 데이터행) | 데이터 행수 | PM 수치 대조 |
|-------|-----------------------------------|------------|-------------|
| opd | `opal/skills/opal-pilot-dev/SKILL.md:288-305` | 16 | 일치 |
| opds | `opal/skills/opal-pilot-dev-short/SKILL.md:260-272` | 11 | 일치 |
| opdw | `opal/skills/opal-pilot-dev-wireframe/SKILL.md:194-204` | 9 | 일치 |
| opp | `opal/skills/opal-pilot-project/SKILL.md:166-176` | 9 | 일치 |
| opwt | `opal/skills/opal-pilot-write-tech/SKILL.md:444-455` | 10 | 일치 |
| oppd | `opal/skills/opal-pilot-project-dev/SKILL.md:120-134` | 13 | 일치 |
| opsdd | `opal/skills/opal-pilot-sdd/SKILL.md:356-382` | 25 | 일치 |
| opdd | `opal/skills/opal-pilot-data-design/SKILL.md:245-261` | 15 | 일치 |
| oppl | `opal/skills/opal-pilot-project-loop/SKILL.md:137-157` | 19 | 일치 |
| opgc | `opal/skills/opal-pilot-gc/SKILL.md:442-450` | 7 | 일치 |
| **합계** | | **134** | **PM 수치(134) 정확** |

주: oppd/oppl은 "## STATE.md 도메인 치환값" 헤딩이 없어 미러 표가 "## 파이프라인"/"## STATE.md 초기 생성" 절 본문에 직접 박혀 있다(별도 절 구조 아님) — §A-6 하단 형식 분류 참조.

### `--row N` — 재검증 결과: **PM 수치(46)와 45로 1건 차이**

단어 경계(`--rows-from`/`--rows-acts`와 구분) + 변경이력 절 제외 기준:

| pilot | 비-변경이력(실전환 대상) | 변경이력 내 리터럴 | PM 표 수치 | 비교 |
|-------|------------------------|-------------------|-----------|------|
| opd/opds/opdw/opp | 0 | 각 1(전환 완료 서술) | 0 | 일치 |
| opwt | 11 | 0 | 11 | 일치 |
| oppd | 5 | 0 | 5 | 일치 |
| opsdd | **9** | 1(`:544`) | **10** | **PM 수치는 변경이력 리터럴 1건을 포함해 10 — 실전환 대상은 9** |
| opdd | 14 | 0 | 14 | 일치 |
| oppl | 4 | 0 | 4 | 일치 |
| opgc | 2 | 0 | 2 | 일치 |
| **합계(실전환 대상)** | **45** | | **46** | **PM 총합보다 1 적음** |

**차이 원인**: `opal-pilot-sdd/SKILL.md:544`(변경이력 표, v3.6.0 항목)에 `` `--row N`/`#N`/`--after N` 본문 리터럴 전수 재정렬 ``이라는 서술이 있고, 이 줄이 grep 패턴 `--row`에 매칭된다. R-4의 AC는 "변경이력 행을 제외한" 잔존 0건을 요구하므로, 실제 전환 대상(코드 예시로 등장하는 것)은 opsdd 9건이며 PM의 opsdd=10은 이 변경이력 리터럴을 포함한 것으로 보인다. **실작업 대상 총량은 45건**이다(변경이력 자체는 불변 대상이라 건드리지 않는다).

opwt 11건 중 2건(`--row <ANALYSIS_PM_Gate_N>`, `<ANALYSIS_사용자확인_N>`, `:249,253`)과 2건(`<EXECUTE_Batch_PM_Gate_N>`, `<EXECUTE_Batch_사용자확인_N>`, `:329,334`)은 pipeline.json에 대응 key가 없다(§4 핵심 발견 4) — 나머지 7건만 아래 표처럼 즉시 key 매핑이 가능하다.

**`--row N` → `task_steps[].key` 매핑 (매핑 가능분 전량)**:

| pilot | 줄 | 현재 리터럴 | 매핑될 key |
|-------|----|-----------|-----------|
| opwt | 197,198 | `--row 1` | `task.task_md` |
| opwt | 199 | `--row 2` | `task.user_confirm` |
| opwt | 295 | `--row <PLAN_PM_Gate_N>` | `plan.pm_gate` |
| opwt | 299 | `--row <PLAN_사용자확인_N>` | `plan.user_confirm` |
| opwt | 362 | `--row <QA_PM_Gate_N>` | `qa.pm_gate` |
| opwt | 383 | `--row <CLOSE_DONE_행N>` | `close.done_md` |
| opwt | 249,253,329,334 | (ANALYSIS·EXECUTE 배치 게이트) | **매핑 불가 — pipeline.json에 key 없음(§4 발견 4)** |
| oppd | 140 | `--row <PM_Gate_N>` | 문맥상 `plan.pm_gate`/`wbs.pm_gate`/`execute.pm_gate` 중 하나(범용 안내문, 특정 행 비고정) |
| oppd | 281 | `--row <Phase1_확정_행N>` | `plan.user_confirm` |
| oppd | 366 | `--row <Phase2_확정_행N>` | `wbs.user_confirm` |
| oppd | 420 | `--row <Phase3_액션_행N>` | `execute.actions`(동적 행 — add-row 대상) |
| oppd | 431 | `--row <그룹_행N>` | 동적 그룹 행(pipeline.json에 고정 key 없음, `add-row`로 생성되는 행) |
| opsdd | 130 | `--row 6` | `spec.pm_gate` |
| opsdd | 131 | `--row 7` | `spec.user_confirm` |
| opsdd | 198 | `--row 16` | `design.pm_gate` |
| opsdd | 199 | `--row 17` | `design.user_confirm` |
| opsdd | 245 | `--row <ACT_행N>` | `execute.act_run`(동적 ACT 행) |
| opsdd | 253 | `--row 19` | `execute.pm_gate` |
| opsdd | 254 | `--row 20` | `execute.user_confirm` |
| opsdd | 296 | `--row 25` | `close.done_md` |
| opsdd | 478 | `--row N`(Agentic 모드 범용 예시) | 범용 템플릿, 특정 key 비고정 |
| opdd | 79,80 | `--row 1` | `task.task_md` |
| opdd | 84 | `--row 2` | `task.user_confirm` |
| opdd | 113 | `--row 4` | `dict.pm_gate` |
| opdd | 114 | `--row 5` | `dict.user_confirm` |
| opdd | 143 | `--row 7` | `model.pm_gate` |
| opdd | 144 | `--row 8` | `model.user_confirm` |
| opdd | 175 | `--row 9` | `ddl_migration.ddl_scripts` |
| opdd | 176 | `--row 10` | `ddl_migration.pm_gate` |
| opdd | 177 | `--row 11` | `ddl_migration.user_confirm` |
| opdd | 194 | `--row 12` | `qa.review` |
| opdd | 195 | `--row 13` | `qa.pm_gate` |
| opdd | 196 | `--row 14` | `qa.user_confirm` |
| opdd | 207 | `--row 15` | `close.done_md` |
| oppl | 237 | `--row 11` | `review.pm_gate` |
| oppl | 238 | `--row 12` | `review.d7_user_gate` |
| oppl | 285 | `--row 17` | `verify.pm_gate` |
| oppl | 286 | `--row 18` | `verify.user_confirm` |
| opgc | 343 | `--row 7` | `close.done_md` |
| opgc | 477 | `--row N`(Agentic 모드 범용 예시) | 범용 템플릿 |

### 산문 `행 N` — 재검증 결과: **PM 수치(49)와 일치(변경이력 포함 시)**

| pilot | 비-변경이력 | 변경이력 내 | 합계 |
|-------|-----------|-----------|------|
| opd | 6 | 0 | 6 |
| opds | 9 | 1 | 10 |
| opdw | 3 | 2 | 5 |
| opp | 8 | 3 | 11 |
| opwt | 1 | 0 | 1 |
| oppd | 0 | 0 | 0 |
| opsdd | 2 | 5 | 7 |
| opdd | 7 | 1 | 8 |
| oppl | 0 | 0 | 0 |
| opgc | 0 | 1 | 1 |
| **합계** | **36** | **13** | **49** |

**PM의 49는 변경이력 포함 총계와 정확히 일치한다.** 다만 R-5의 AC("`행 [0-9]+` grep이 0건")를 변경이력 배제 없이 문자 그대로 적용하면 13건의 불변 대상(변경이력)까지 손대야 하는 것으로 오독될 위험이 있다(§5 R-5) — R-4가 "변경이력 행을 제외한"을 명시한 것과 표현이 다르다.

### `## PM Gate 점검 목록` 절 — 존재 여부 및 줄 범위

| pilot | 존재 | 줄 범위 | 현재 내용 형태 |
|-------|------|--------|--------------|
| opd | Y | `:312-321`(다음 헤딩 전) | `\| Phase \| 산출물 \| 체크리스트 위치 \|` 3열 표, 4행(ANALYSIS/PLAN/TEST-SCENARIO/TEST) |
| opds | Y | `:280-288` | 동형 표, 2행 |
| opdw | Y | `:212-219` | 동형 표, 2행(WIREFRAME/EXECUTE) |
| opp | Y | `:183-191` | 동형 표, 2행(PLAN/EXECUTE) |
| opwt | Y | `:472-480` | 동형 표(정확한 데이터행 미상 — 헤딩만 확인, 본문은 §A-3 실측 범위 밖) |
| opsdd | Y | `:412-421` | 동형 표 |
| opdd | Y | `:268-279` | 동형 표 |
| oppd | **N** | — | 헤딩 없음. 대신 "## 파이프라인" 절 내 블록쿼트 2문장(`:136-141`)으로 "PM Gate 단일 mark" 절차만 서술 — **산출물/체크리스트 분해 표 자체가 없음**(§4 핵심 발견과 연동, R-9 시 신규 저술 필요) |
| oppl | **N** | — | 헤딩 없음. `:131` 블록쿼트 1문장으로 "PM Gate/사용자 확인은 mark 개별 호출" 서술만 존재, 분해 표 없음 |
| opgc | **N** | — | 헤딩 없음. **PM Gate 개념 자체가 없음**(§4 핵심 발견 3) — R-9 대상 아님 |

**PM의 "pm_gate 보유 4종/미보유 6종"(pipeline.json 기준)과 별개로, SKILL.md 레벨에서는 7종이 "## PM Gate 점검 목록" 헤딩을 갖고 3종(oppd/oppl/opgc)은 갖지 않는다** — 이 3종 중 opgc는 개념이 없어 이관 대상이 아니고, oppd/oppl은 행은 있지만 이관할 표가 없어 신규 저술이 필요하다는 것이 PM 배경 분석에는 없던 세분화다.

### `## STATE.md 도메인 치환값` 절 — 형식 분류 및 줄 범위

| pilot | 존재 | 줄 범위 | 형식 |
|-------|------|--------|------|
| opd | Y | `:275-311` | 표(필드/값 2열) |
| opds | Y | `:247-279` | 표 |
| opp | Y | `:153-182` | 표 |
| opsdd | Y | `:327-411` | 표 |
| opdd | Y | `:232-267` | 표 |
| opgc | Y | `:424-455` | 표 |
| opdw | Y | `:181-211` | **불릿**(`` - `{모드}`: ... ``) |
| opwt | Y | `:419-462` | **혼합**(상단 불릿 + 굵은 라벨 뒤 파이프 구분 텍스트 — 실제 markdown 표 아님, "네트워크 상태"/"배치 계획"을 표처럼 서술한 산문) |
| oppd | **N** | — | 헤딩 없음(§A-6 미러 표 절 참조 — "## 파이프라인" 절에 흡수) |
| oppl | **N** | — | 헤딩 없음 |

**PM의 "표 6종/불릿/혼합" 분류가 정확하다** — 표 6건(opd/opds/opp/opsdd/opdd/opgc) + 불릿 1건(opdw) + 혼합 1건(opwt) = 8건, 이 8종이 헤딩을 보유한 전체이며 oppd/oppl 2종은 헤딩 자체가 없다(10종 전체에 대한 명시적 서술은 없었으나 8종 한정으로는 정확).

---

## 7. 불일치 요약 (TASK.md 배경 분석 대비)

| # | TASK.md 서술 | 실측 결과 | 판정 |
|---|--------------|----------|------|
| 1 | 미러 표 134행(pilot별 세부수치) | 완전 일치(재검증) | **정확** |
| 2 | `--row N` 46건 | 실측 45건(비-변경이력) — opsdd 변경이력 리터럴 1건이 포함된 것으로 추정 | **경미한 불일치(-1)** |
| 3 | 산문 `행 N` 49건 | 완전 일치(변경이력 13건 포함 시) | **정확(단, 변경이력 포함 전제가 R-4와 다른 기준이라는 점은 명시 필요)** |
| 4 | pm_gate 보유 4종/미보유 6종 | pipeline.json 기준 정확. 단 SKILL.md "## PM Gate 점검 목록" 헤딩 기준으로는 7종 보유/3종 미보유(oppd·oppl·opgc)로 갈리고, opgc는 개념 자체 부재, oppd·oppl은 행은 있으나 이관 원본 표가 없음 — TASK.md에 없는 세분화 | **보강 필요(신규 발견)** |
| 5 | `pipeline-spec.schema.json`을 "gate 인라인 신설 대상"(D-4)으로 명시 | 맞으나, 이 스키마 파일은 비집행 문서다 — 실질 집행은 `validate_pipeline_spec()` Python 함수뿐 | **보강 필요(구분 명시)** |
| 6 | (미기재) opwt pipeline.json이 3모드 중 "작성" 모드만 반영, ANALYSIS·배치별 동적 게이트 미포함 | 신규 발견 — R-4/R-5 전환의 구조적 공백 | **신규 발견, PLAN 필수 처리 항목** |
