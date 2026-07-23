# ANALYSIS: state-tool task-step 키 주소 체계 도입 1차 — pipeline.json 표준화 + 그룹 A 전환

> 작성일: 2026-07-20
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 수정 대상 본체 (1,937줄) |
| D-2 | 설계 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | 1.1 승격 대상, rows[].key 필드 추가 지점 |
| D-3 | 설계 | state-tool README | `opal/tools/state-tool/README.md` | 서브명령·에러 카탈로그 SSOT(25종) |
| D-4 | 소스 | run.sh 래퍼 | `opal/tools/state-tool/run.sh` | `~/.opal/.venv/bin/python` 호출 패턴 |
| D-5 | 소스 | 기존 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | 회귀 기준선(3,618줄, 직접 import 패턴) |
| D-6 | 설계 | 원 설계 SSOT (PLAN 134) | git 이력 `4af79ae:tasks/134-260501-opp-pipeline-state-tool/PLAN.md` | §2.1~§2.21 기존 설계 근거 — **현재 작업 트리에는 부재**(§5 리스크 R-A1 참조), git show로 확보 |
| D-7 | 설계 | opp SKILL.md | `opal/skills/opal-pilot-project/SKILL.md:153-179` | 그룹 A 전환 대상 — 9행 |
| D-8 | 설계 | opd SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md:269-312` | 그룹 A 전환 대상 — 15행 |
| D-9 | 설계 | opds SKILL.md | `opal/skills/opal-pilot-dev-short/SKILL.md:238-276` | 그룹 A 전환 대상 — 10행 |
| D-10 | 설계 | opdw SKILL.md | `opal/skills/opal-pilot-dev-wireframe/SKILL.md:181-219` | 그룹 A 전환 대상 — 9행, 조건부 3~5행 |
| D-11 | 설계 | opdd SKILL.md | `opal/skills/opal-pilot-data-design/SKILL.md:232-264` | 드리프트 근거 — 15행, `DDL/MIGRATION` 단계 |
| D-12 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md:183-193` | State 관리·도구 우선 원칙 SSOT |
| D-13 | 설계 | red-first.md | `opal/core/references/harness/red-first.md:64-67` | §4 공개 인터페이스 검증 원칙 — argparse 레벨 신규 케이스 테스트 패턴 근거 |
| D-14 | 설계 | install-mac.sh | `scripts/install-mac.sh:209-223`, `1060-1071`, `1112-1114` | 디렉토리 재귀 배포(`cp -r`/`cp -Rf`) 확인 |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/state-tool/state_tool.py` | CLI 본체 — 9서브명령+verify, argparse, 행 조회/갱신 로직 | O (R-2~R-6, R-9) | 전체 1,937줄 |
| `opal/tools/state-tool/schema/state.schema.json` | state.json JSON Schema | O (R-3, R-8) | 전체 106줄 |
| `opal/tools/state-tool/schema/pipeline-spec.schema.json` | (신규) 스펙 JSON Schema | O (R-1, 신규 생성) | - |
| `opal/tools/state-tool/README.md` | 서브명령·에러 카탈로그 SSOT | O (R-4~R-9 반영) | 전체 297줄 |
| `opal/tools/state-tool/tests/test_state_tool.py` | pytest 회귀 기준선 | O (R-10, 케이스 추가만) | 전체 3,618줄 |
| `opal/skills/opal-pilot-project/SKILL.md` | opp STATE.md 도메인 치환값 섹션 | O (R-7) | `:153-179` |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd STATE.md 도메인 치환값 섹션 | O (R-7) | `:269-312` |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds STATE.md 도메인 치환값 섹션 | O (R-7) | `:238-276` |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw STATE.md 도메인 치환값 섹션 | O (R-7) | `:181-219` |
| `opal/skills/opal-pilot-project/references/pipeline.json` | (신규) opp 스펙 | O (R-7, 신규 생성) | - |
| `opal/skills/opal-pilot-dev/references/pipeline.json` | (신규) opd 스펙 | O (R-7, 신규 생성) | - |
| `opal/skills/opal-pilot-dev-short/references/pipeline.json` | (신규) opds 스펙 | O (R-7, 신규 생성) | - |
| `opal/skills/opal-pilot-dev-wireframe/references/pipeline.json` | (신규) opdw 스펙 | O (R-7, 신규 생성) | - |
| `opal/skills/opal-pilot-data-design/SKILL.md` | opdd 단계 목록·`--skill opdd` 참조 | X (표현 변경 없음, enum만 코드 등록) | `:75, 232-262` |
| `scripts/install-mac.sh` | 배포 스크립트 | X (재귀 복사라 무변경으로 충분 — §3.3 근거) | `:209-223, 1060-1071, 1112-1114` |

### 1.2 아키텍처 패턴

- **응답 계약**: 모든 서브명령이 `ok(command, **kwargs)` / `err(command, code, message=None, exit_code=1, **kwargs)` 단일 라인 JSON 헬퍼로 응답 (`state_tool.py:121-139`). `err`는 `ERROR_CODES` 딕셔너리에서 메시지 템플릿을 조회해 `.format(**kwargs)`로 채운다 — 신규 에러 코드(`task_step_not_found`, `task_step_addr_conflict` 등)는 이 딕셔너리에 등록해야 `err()` 호출 시 메시지가 자동 완성된다(`state_tool.py:68-103`).
- **행 조회 공통 헬퍼**: `find_row(state, row_id, command)` / `find_row_index(state, row_id, command)` (`state_tool.py:354-366`)가 모든 서브명령(advance/mark/block/add-row의 `--after`)에서 `--row` 값을 `row_id`와 단순 동등비교로 조회한다. **행 주소 해석 지점은 이 두 함수 + `cmd_gate_pass`의 인라인 순회(`state_tool.py:1290-1296`) 뿐** — 신규 `--task-step`/`--task-step-id` 도입 시 이 지점들을 공통 해석 함수로 대체하면 파급이 좁게 국한된다.
- **행 갱신 파이프라인 공통 구조**: `resolve_task_path` → `load_state_json` → `find_row_index` → (권한/게이트 가드) → 상태 변경 → `save_state_json` → `sync_state_md`. 가드 함수(`check_stage_transition_guard`, `check_close_gate`, `_run_clarification_hook`)는 모두 `row_index`(정수 인덱스, `rows[]` 배열 위치)를 인자로 받으며 `row_id`나 `--row` 원본 인자에 의존하지 않는다(`state_tool.py:376-465`, `1523-1579`) — 즉 주소 해석을 어떤 방식(row_id/key)으로 하든 `row_index`만 정확히 산출하면 하위 가드 로직은 **무변경으로 재사용 가능**하다.
- **행 주입 3경로**: `build_rows_from_spec`(inline JSON, `:470-514`) / `build_rows_from_skill_md`(SKILL.md 4단 regex 파싱, `:516-606`) / `parse_existing_state_md`(`--import-existing`, `:612-644`). 셋 다 `row_id = i + 1`로 배열 인덱스 기반 순번을 부여하며 `key` 필드를 생성하지 않는다 — R-2/R-9 구현 시 이 3함수 중 `.json` 스펙 전용 신규 함수(예: `build_rows_from_pipeline_json`)를 추가하고, 기존 2개 함수는 하위호환을 위해 그대로 둔다.
- **argparse 구조**: `build_parser()`(`:1788-1924`) 단일 함수가 9개 서브파서를 순차 정의. `--row`는 `mark`/`advance`/`block`/`add-row(--after)`에 개별 `type=int, required=True`로 선언되어 있어(`:1841, 1848, 1865, 1877`), `--task-step`/`--task-step-id`/deprecated `--row` alias를 도입하려면 각 서브파서에 mutually-exclusive 그룹을 추가해야 한다(현재 `owner_group`/`rows_group`과 동일 패턴, `:1822, 1856`).
- **`--step N/M`(액션 진행률)**: `_parse_step(step_str)`(`:918-928`)가 `"N/M"` 정규식 파싱 후 `cmd_mark` 내부에서 조기 done 가드로 사용(`:987-1004`). `--action-step` 개명(R-5)은 이 인자 하나(`p_mark.add_argument("--step", ...)`, `:1855`)에 별칭 그룹만 추가하면 되는 국소 변경 — 로직(`_parse_step`, `row["step"]` 필드)은 무변경.
- **`gate-pass`는 deprecated**(`state_tool.py:1273-1281` 주석, README `:199-215`) — 014 Phase 4 이후 신규 pilot(그룹 A 4종 포함)은 QA Gate/State Gate 행이 없는 표준 구조(작업/PM Gate/사용자 확인/DONE.md 생성)를 쓰므로, 본 태스크의 pipeline.json 생성 시 4행 게이트 패턴을 절대 생성하지 않아야 한다(TASK.md 요구사항과 정합).

### 1.3 의존성 맵

- `run.sh` → `$HOME/.opal/.venv/bin/python state_tool.py` (`run.sh:12`) — venv 파이썬 실행, 표준 라이브러리만 사용(`state_tool.py:14-23`, `import json/argparse/pathlib/re/subprocess/sys` 뿐, `jsonschema` 등 서드파티 없음).
- `state_tool.py` → `~/.opal/tools/date/date.js`(node) subprocess 호출(`get_kst_datetime`, `:145-161`) — KST 시점 취득. state-tool 자체는 이 외 외부 프로세스 의존 없음.
- `resolve_owner_placeholder`(`:207-234`) → `$OPAL_HOME/identity.md` 또는 `~/.opal/identity.md` 읽기 — note/reason의 `{owner_name}` 치환. R-1~R-9 신규 로직과 무관.
- 8개 `opal-pilot-*` SKILL.md → `opal/tools/state-tool/run.sh init ... --rows-from <SKILL.md>` 호출 (그룹 A 4종은 D-7~D-10 참조) — 이 문서화 호출부가 R-7에서 `--rows-from <SKILL.md>`(md 파싱)에서 `--rows-from references/pipeline.json`(json 파싱)으로 교체된다. `--rows-from`은 **동일 플래그명 유지, 확장자로 분기**(TASK 확정 방향 §4)이므로 SKILL.md의 인자 표기 자체는 크게 바뀌지 않고 경로만 `.md`→`.json`으로 바뀐다.
- `opal/tools/state-tool/schema/state.schema.json`은 **런타임에 프로그램적으로 검증되지 않는다** — `state_tool.py` 어디에도 `state.schema.json`을 로드/검증하는 코드가 없음(grep 결과 0건, README `:278`도 "JSON Schema Draft-07 참조용"이라 명시). 스키마는 **문서 SSOT**로만 기능하며, 실제 검증은 `cmd_validate`(`:1112-1169`)의 하드코딩된 개별 필드/enum 체크로 수행된다. `pipeline-spec.schema.json`(R-1)도 동일 관례를 따를지, 아니면 `spec-validate`(R-6)가 최초로 실제 파일을 열어 자체 검증 로직을 구현할지는 PLAN 단계 결정 필요 — 표준 라이브러리만 허용되므로(TASK 기술스택 §), `jsonschema` 패키지 없이 Draft-07 문서를 참조 삼아 수작업 검증 함수를 작성하는 기존 관례(=`cmd_validate` 패턴)를 따르는 것이 코드베이스 정합적이다.
- `test_state_tool.py` → `import state_tool as ST`(`sys.path.insert`, `:35-38`) 직접 import + `make_args()` SimpleNamespace 헬퍼로 `cmd_*` 함수 직접 호출(§1.4 상세). 단, argparse `choices=[...]` 레벨 제약(enum 미등록 등)은 직접 함수 호출로 우회되므로 이런 케이스는 `subprocess.run(["bash", str(_RUN_SH)], ...)`로 실제 CLI를 구동하는 별도 패턴을 쓴다(`TestOpplSkillInit`, `:3496-3553`).

### 1.4 테스트 현황

- **프레임워크**: 표준 라이브러리 `unittest`(pytest 아님, `[MUST] TASK T-11: 표준 라이브러리만 import (pytest/hypothesis 금지)`, `test_state_tool.py:19`) — TASK.md R-10 AC가 "pytest 전체 PASS"라고 명시하지만 실제 실행은 `python -m pytest`(pytest는 unittest 스타일 테스트도 수집·실행 가능하므로 호환)로 이해해야 한다. `pytest`가 `~/.opal/.venv`에 설치되어 있는지는 미확인 — PLAN 단계에서 실행 방법(예: `~/.opal/.venv/bin/python -m pytest` 또는 `python -m unittest`) 확정 필요.
- **패턴 1 (표준, 대다수)**: `BaseTestCase(unittest.TestCase)`(`:131-237`) — `setUp`에서 `tempfile.mkdtemp()`로 임시 task_path 생성, `tearDown`에서 `shutil.rmtree`. `_call_cmd(fn, args, expect_ok=True)`(`:144-160`)가 stdout을 `redirect_stdout`으로 캡처하고 `SystemExit`(err 경로)을 잡아 `(exit_code, result_dict)` 반환. `make_args(**kwargs)`(`:94-128`)가 argparse Namespace를 흉내낸 `types.SimpleNamespace`를 생성 — **신규 플래그(`--task-step`, `--task-step-id`, `--action-step`, `--key` 등)를 추가하면 이 함수의 `defaults` 딕셔너리에도 기본값을 추가해야 기존 테스트가 `AttributeError` 없이 통과한다**(005 명확화 게이트 도입 시 `clarification_check`/`task_md` 키를 추가한 선례, `:122-124`).
- **패턴 2 (공개 인터페이스, argparse 레벨 제약)**: `TestOpplSkillInit`(`:3496-3553`), `TestSchemaModeEnumSemiAgentic`(`:3559~`) — `subprocess.run(["bash", str(_RUN_SH)] + args, ...)`로 실제 CLI 프로세스를 구동해 stdout JSON + exit code만 관찰(`red-first.md §4` "내부 구현/private 결합 금지, 공개 인터페이스·관찰 행위로 검증"). **R-4의 `task_step_addr_conflict`(주소 플래그 2개 이상 동시 사용 거부)처럼 argparse `mutually_exclusive_group`으로 구현될 제약은 이 패턴으로 테스트해야 한다** — `make_args()` 직접 호출은 argparse 파싱 단계 자체를 우회하므로 mutually-exclusive 위반을 재현할 수 없다.
- **회귀 보호 관례**: 기존 테스트 클래스명에 대상 기능(`TestG7StatusTransitions`, `TestMultiStepDoneGuard`, `TestRedFirst`, `TestClarificationGate` 등)을 그대로 반영하고 클래스 docstring에 `PLAN §N.M` 인용을 남기는 패턴(`:1038, 2777, 2602, 3106`) — 신규 클래스(예: `TestTaskStepAddressing`, `TestPipelineSpecValidate`)도 이 컨벤션을 따라야 한다.
- **하위호환 증명 패턴**: TASK.md 제약 "기존 테스트 케이스 수정 금지"는 `TestOpplSkillInit.test_existing_eight_skills_regression_unaffected`(`:3543-3552`) 같은 "기존 경로가 깨지지 않았다"를 명시적으로 검증하는 신규 테스트 추가 관례로 이미 확립되어 있다 — R-10 구현 시 `--row`/`--step` 별칭 회귀도 이 패턴(신규 테스트가 구 동작을 검증)으로 작성하면 된다.

---

## 2. 외부 조사 결과 (해당 시)

해당 없음 — 본 태스크는 표준 라이브러리만 사용하는 내부 CLI 도구 확장이며, 외부 라이브러리/API 신규 도입이 없다(TASK.md 기술 스택: "Python 3.14 표준 라이브러리만"). context7/WebSearch 조사 불필요.

---

## 3. 영향 범위

### 3.1 직접 영향

- `opal/tools/state-tool/state_tool.py`: argparse 서브파서 4개(mark/advance/block/add-row) 인자 확장, `find_row`/`find_row_index` 대체 또는 확장(공통 해석 함수 신설), `cmd_init`의 rows 구축 분기(`.json`/`.md` 확장자 분기), `ERROR_CODES`에 `task_step_not_found`/`task_step_addr_conflict` 등 신규 코드 추가, `STAGE_ENUM`에 `DICT`/`MODEL`/`DDL/MIGRATION` 추가, `--skill` choices에 `opdd` 추가.
- `opal/tools/state-tool/schema/state.schema.json`: `schema_version` const `"1.0"` → enum(`["1.0","1.1"]`) 또는 `oneOf` 전환(하위호환 병행 허용, R-3 AC), `rows[].items.properties`에 `key` 선택 필드 추가.
- `opal/tools/state-tool/schema/pipeline-spec.schema.json`: 신규 생성.
- `opal/skills/{opal-pilot-project,opal-pilot-dev,opal-pilot-dev-short,opal-pilot-dev-wireframe}/references/pipeline.json`: 신규 생성 4건.
- `opal/skills/{opal-pilot-project,opal-pilot-dev,opal-pilot-dev-short,opal-pilot-dev-wireframe}/SKILL.md`: "STATE.md 도메인 치환값" 섹션 내 `--rows-from` 호출 경로 교체 + 마크다운 표 → JSON 참조 안내로 축소.
- `opal/tools/state-tool/README.md`: 신규 서브명령(`spec-validate`)·플래그(`--task-step`/`--task-step-id`/`--action-step`/`add-row --key`)·에러 코드 반영.
- `opal/tools/state-tool/tests/test_state_tool.py`: R-1~R-9 대응 신규 테스트 클래스 추가(기존 클래스 무변경).

### 3.2 간접 영향

- **opdd(`opal-pilot-data-design`)**: `state.schema.json`의 `skill` enum·`stage` enum이 확장되면 opdd의 기존 `init --skill opdd --rows-from <SKILL.md>` 호출(`opal-pilot-data-design/SKILL.md:75, 241`)이 현재의 `skill_md_parse_error`류 거부에서 정상 동작으로 전환된다 — opdd SKILL.md 본문은 변경 없이 **동작만 바뀌는 간접 수혜**(TASK.md R-8 AC).
- **그룹 B(opgc/opsdd/oppd) 및 그룹 C(opwt/oppl)**: `--row`가 deprecated alias로 유지되므로 이들 pilot의 기존 `run.sh mark --row N` 호출 문서·워커 프롬프트는 **변경 없이 그대로 동작** — 단, TASK 제약상 이번 태스크에서 이들의 SKILL.md/문서 24곳은 일괄 갱신하지 않으므로 `--row` 사용처로 계속 남는다(TASK.md 범위 "제외" 항목과 일치).
- **`opal-action-monitor`/`opal-action-status`(opas)**: `.oppl-run/` 파싱·backlog-tool 연동 도구는 `state.json`의 `rows[]` 구조(`row_id`/`stage`/`item`/`status`)를 읽는데, `key` 필드는 **선택 필드로 추가**되므로 이 도구들의 파싱 로직에 영향 없음(추가 필드 무시 원칙, JSON Schema `additionalProperties: false`가 `state.schema.json:7`에 걸려 있어 **스키마 자체에는 `key`를 명시적으로 등록해야** 검증 통과 — 안 하면 오히려 기존 검증 실패 위험, §5 리스크 참조).
- **PM/워커 디스패치 프롬프트**: `--as-worker --worker-stage <stage>` 게이트(`state_tool.py:952-963`)는 row_index 산출 이후 stage 비교만 하므로, PM이 워커에게 `--task-step <key>` 형태로 호출 예시를 주입하도록 프롬프트 관례가 바뀔 수 있으나 **게이트 로직 자체는 무변경**.
- **회귀 테스트 스위트 실행 방식**: `python -m pytest opal/tools/state-tool/tests/`(TASK R-10 AC)와 `unittest` 기반 기존 코드(§1.4) 간 실행기 확인 필요 — `~/.opal/.venv`에 pytest 설치 여부 미확인(§5 리스크).

### 3.3 영향 범위 요약

- [x] DB 스키마 변경 — 해당 없음(JSON Schema 파일 2종 변경/신설이며 관계형 DB 아님)
- [x] API 인터페이스 변경 — CLI 인자 인터페이스 확장(하위호환 필수, TASK 제약)
- [x] 설정/환경변수 변경 — 없음(신규 env var 도입 없음, `resolve_owner_placeholder`의 `OPAL_HOME`은 기존 관례 재사용)
- [ ] 빌드/배포 파이프라인 변경 — 없음(§1.1, install-mac.sh 무변경으로 충분, §3.3 근거 D-14)

---

## 4. 핵심 발견 사항

1. **행 조회 지점이 2개 함수(`find_row`/`find_row_index`, `state_tool.py:354-366`)로 국소화되어 있어, 주소 해석을 key/row_id 겸용으로 바꾸는 리팩터링의 파급 범위가 예상보다 좁다** — 상위 가드 로직(`check_stage_transition_guard`/`check_close_gate`/`_run_clarification_hook`)이 모두 `row_index`(배열 위치)만 소비하고 원본 주소 인자에 의존하지 않기 때문(§1.2).
2. **`state.json`도 `pipeline-spec.schema.json`(예정)도 런타임에 실제 JSON Schema 라이브러리로 검증되지 않는다** — `state.schema.json`은 문서 SSOT일 뿐이며, 검증은 `cmd_validate`의 수작업 코드로 수행된다(§1.3). R-1의 "그룹 A 4종 pipeline.json이 스키마 검증을 통과" AC를 만족시키려면 `spec-validate`(R-6)가 `jsonschema` 패키지 없이 Draft-07 문서 구조를 참조해 자체 검증 함수를 새로 작성해야 하며, 이는 기존 코드베이스 관례와 일치한다.
3. **TASK.md D-5가 인용하는 `tasks/134-260501-opp-pipeline-state-tool/PLAN.md`는 현재 작업 트리에 존재하지 않는다** — `git log`로 확인 결과 `chore: tasks/ 베이스라인 리셋`(커밋 `b1b7618`) 시점에 태스크 폴더 전체(TASK/PLAN/STATE/state.json/DONE/QA-PLAN)가 삭제되었고, `4af79ae`(원 커밋)에서만 git 이력으로 조회 가능하다. 후속 PLAN 워커가 D-5를 인용하려면 `git show 4af79ae:tasks/134-260501-opp-pipeline-state-tool/PLAN.md`로 조회해야 하며, 파일 경로를 그대로 Read하면 실패한다(§5 리스크 R-A1).
4. **그룹 A 4종의 표 행 수·구조가 TASK.md 서술과 정확히 일치한다** — opp 9행(`opal-pilot-project/SKILL.md:165-177`)/opd 15행(`opal-pilot-dev/SKILL.md:281-299`)/opds 10행(`opal-pilot-dev-short/SKILL.md:250-263`)/opdw 9행+조건부 3~5행(`opal-pilot-dev-wireframe/SKILL.md:193-208`, "WIREFRAME 스킵 시... #3-#5를 `-`로 표기") 모두 확인. opdw의 조건부 표기는 현재 "행 값을 `-`로 표기"하는 **문서 관례**일 뿐 `state_tool.py`에 조건부 처리 로직은 없다 — R-1의 `task_steps[].conditional` 필드가 초기화 시 무엇을 하는지(단순 메타데이터 vs 실제 `na` 자동 마킹)는 PLAN 단계 결정 필요.
5. **opdd의 `DDL/MIGRATION` 단계명에 슬래시(`/`)가 포함되어 있다**(`opal-pilot-data-design/SKILL.md:237, 255-257`) — TASK 확정 §6 key 형식 규칙 "stage_slug는 stage enum 소문자화(`-`·`/`→`_`)"이 이미 이 케이스를 반영해 설계되었음을 재확인(`ddl_migration`로 치환). 다만 opdd는 이번 1차 범위에서 enum 등록만 하고 pipeline.json은 만들지 않으므로(TASK 범위 제외 항목), 이 치환 규칙이 실제 코드에 적용되는 것은 opdd 전환 시점(후속 태스크)이다 — 1차에서는 `STAGE_ENUM` 리스트에 문자열만 추가하면 된다.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-A1 | TASK.md D-5가 가리키는 `tasks/134-260501-opp-pipeline-state-tool/PLAN.md`가 작업 트리에 부재(베이스라인 리셋으로 삭제) — git 이력(`4af79ae`)에서만 조회 가능 | 중 | `git log --all --oneline -- "tasks/134*"`, 커밋 `b1b7618` diff stat (PLAN.md -1452줄) |
| R-A2 | `state.schema.json`이 `additionalProperties: false`(`state.schema.json:7, 47`)이므로 `rows[].key` 신규 필드를 `properties`에 명시적으로 추가하지 않으면, 문서 SSOT상 key 있는 state.json이 "스키마 위반"으로 읽힌다(런타임 강제 검증은 없지만 §4 핵심발견 #2처럼 향후 `spec-validate`/`validate` 확장 시 기준이 됨) | 중 | `opal/tools/state-tool/schema/state.schema.json:7,47` |
| R-A3 | `cmd_add_row`의 row_id 전체 재정렬(`state_tool.py:1202-1204`, "삽입 후 전체 재번호")과 `--key` 유일성 검증(R-9)이 상호작용 — 재정렬은 `row_id`만 갱신하고 기존 행의 `key`는 불변이라 안전하나, **자동 생성 key**(`{stage_slug}.{item기반 slug}_{n}`)가 동일 stage 내 기존 동적 행과 충돌하지 않도록 검증 시점에 전체 rows[]를 스캔해야 한다 — 현재 `add-row`에는 이런 전체 스캔 로직이 없음(신규 구현 필요) | 중 | `state_tool.py:1173-1227`(cmd_add_row 전체) |
| R-A4 | `worker_scope_violation` 게이트(`state_tool.py:952-963`)는 `row["stage"] != allowed_stage`만 비교하고 원본 주소 인자 종류(--row/--task-step/--task-step-id)를 구분하지 않음 — `--task-step` 도입 자체는 이 게이트와 충돌하지 않으나, `task_step_addr_conflict`(주소 플래그 2개 이상 동시 사용 거부, R-4 AC)는 argparse 레벨 mutually-exclusive 그룹으로 구현해야 하며 `make_args()` 직접 호출 테스트로는 검증 불가(§1.4 패턴 2 참조) | 낮 | `state_tool.py:952-963`, `test_state_tool.py:3496-3522`(subprocess 패턴) |
| R-A5 | CLOSE 게이트(`check_close_gate`, `state_tool.py:427-464`)와 `_run_clarification_hook`(`:1523-1579`)은 "직전 행이 특정 `item` 문자열(`"사용자 확인"`)인지"로 판정 — key 주소 체계 도입으로 slug 명명이 `user_confirm`(TASK 확정 §5)으로 바뀌어도 이 판정은 `item` 필드(한글 "사용자 확인") 값에 의존하므로 **영향 없음**(item 필드와 key 필드는 별개, item은 화면 표시용 한글 유지) — 단, PLAN 단계에서 이 분리를 명시적으로 확인해야 재해석 오류를 막을 수 있음 | 낮 | `state_tool.py:451, 1549-1556` |
| R-A6 | `python -m pytest`(TASK R-10 AC 문구) 실행 가능 여부가 `~/.opal/.venv`에 pytest 설치되어 있는지에 좌우되는데, 코드/테스트 파일 자체는 `unittest`만 사용(`[MUST] TASK T-11`, `test_state_tool.py:19`) — pytest 미설치 시 `python -m unittest discover`로 대체 실행해야 함 | 낮 | `test_state_tool.py:19,23-33`(표준 라이브러리 import만) |
| R-A7 | opdw "WIREFRAME 스킵 시 #3-#5를 `-`로 표기"(`opal-pilot-dev-wireframe/SKILL.md:208`)는 현재 **문서 관례**일 뿐 `state_tool.py`에 대응 코드가 없음 — R-1의 `conditional` 스펙 필드가 `init` 시 무엇을 자동화할지(단순 표시 vs 자동 na 마킹) 결정되지 않으면 PLAN 단계에서 구현 범위가 모호해질 수 있음 | 중 | `opal-pilot-dev-wireframe/SKILL.md:208`, TASK.md §확정된 설계 방향 #7 |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python | 3.14 (표준 라이브러리만 — `state_tool.py:14-23`) |
| 테스트 | unittest (pytest 호환 실행 가능) | `test_state_tool.py:19` |
| 스키마 | JSON Schema | Draft-07 (참조용, 런타임 미검증 — §4 #2) |
| 셸 래퍼 | bash | `run.sh:1-12` |
| 시점 취득 | Node.js (`date.js`) | subprocess 호출(`state_tool.py:145-161`) |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-plan | 본 ANALYSIS 이후 PLAN 단계에서 §2.1~§2.21 스타일의 설계 SSOT 재구성(D-6 부재 보완) |

### 6.3 추천 MCP

해당 없음 — 표준 라이브러리 내부 도구 확장이라 외부 라이브러리 문서 조회(context7) 불필요.
