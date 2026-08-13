# PLAN: state-tool `--import-existing` task-step key 유실 결함 수정

> 작성일: 2026-07-23 | 입력: TASK.md (ANALYSIS.md 없음 — 코드 직접 분석)
> 모드: Flat (단일 기능)
> 트랙: **RED-first** (버그 수정·회귀 방지, `opal/core/references/harness/red-first.md` §1.5)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`state-tool init --import-existing`가 기존 task-step key를 전부 유실시키는 FW 결함을 수정한다. 근본 원인은 import 복구 원천을 **key 컬럼이 없는 STATE.md 렌더 표**에 둔 lossy projection이다 (`opal/tools/state-tool/state_tool.py:271`, `:900-908`). 수정 방향은 **key-보존 import** — import 파싱으로 얻은 keyless rows에 권위 원천(기존 state.json → pipeline.json 스펙)의 key를 (stage,item) 매칭으로 재접합한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | key-보존 import (state.json→pipeline.json→keyless 폴백) | R1~R5 (TASK §요구사항) | P0 | 없음 |

> 단일 기능 → **Flat 모드**. §2·§3의 F 하위 섹션을 생략하고 평면으로 작성한다.

### 1.3 기능 의존 그래프

생략 (단일 기능).

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `cmd_init` import 분기 key 재접합 | `init --force --import-existing` 후 state.json rows[].key 계약(070 `--task-step` 주소) | P0 (파이프라인 주소 전면 불능) | L1(단위, 실 파일 I/O) | S-a |
| H-2 | pipeline.json 폴백 매칭 | state.json 부재 시 stage+item 매칭 정확성 — 중복 (stage,item) 오배정 | P1 | L1(단위) | S-b, S-e |
| H-3 | 하위호환 (key 원천 전무) | 기존 keyless import 동작·기존 테스트 불변 | P1 (회귀) | L1 + 전량 회귀 | S-c, S-reg |
| H-4 | schema_version 승격 (`state_tool.py:932`) | key 보존 시 "1.1" 유지 (any(key) 로직 정합) | P1 (2차 파급 재발) | L1(단위) | S-d |
| H-5 | 매칭 알고리즘 선택 (row_id vs stage+item) | 행 수/순서 불일치·재번호 시 오배정 | P1 | L1(edge) | S-e |

---

## 2. 기능별 분석 (Flat)

### 2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `opal/tools/state-tool/state_tool.py` | state-tool CLI 단일 파일 — `cmd_init` import 분기 + 신규 key 재접합 헬퍼 | 수정 |
| 배치 | `opal/tools/state-tool/tests/test_state_tool.py` | pytest 회귀 테스트 (RED→GREEN) | 수정 |
| 문서 | `opal/tools/state-tool/state_tool.py` @header DESCRIPTION | 변경이력에 074 항목 추가 | 수정 |

> state-tool은 Python 표준 라이브러리 CLI 단일 파일 도구 — FE/BE/DB 6영역 매칭이 없어 "배치(도구)" 영역으로 분류한다.

### 2.2 현재 구현 (직접 코드 분석)

**결함 경로** — `cmd_init` import 분기 (`state_tool.py:900-908`):

```
if import_mode:
    md_content = load_state_md(task_path)          # :901
    if md_content:
        rows = parse_existing_state_md(md_content)  # :904 — keyless rows 생성
```

- `parse_existing_state_md` (`state_tool.py:819-851`)는 STATE.md 마크다운 표를 정규식으로 파싱해 rows를 만든다. 표 컬럼은 `| # | 단계 | 항목 | 상태 | 시점 |`뿐(`render_pipeline_table` `state_tool.py:271`)이라 **key 컬럼이 원천에 존재하지 않는다**. 결과 row에 `key` 필드가 없다(`state_tool.py:840-849`).
- row_id는 파싱 순번으로 **재부여**된다 (`state_tool.py:841`: `"row_id": i + 1`) — 원본 state.json의 row_id를 신뢰할 수 없음.
- schema_version은 `any(r.get("key") for r in rows)`로 계산 (`state_tool.py:932`) → keyless rows면 "1.0"으로 강등.
- `--force`는 멱등성 체크를 통과(`state_tool.py:890`)하고 line 957 `save_state_json`이 기존 state.json(key 보유)을 keyless rows로 덮어쓴다. 이때 기존 state.json은 line 950-955에서 `created_at` 보존 목적으로만 읽히며 **key는 계승되지 않는다**.

**정상 경로 대비** — `build_rows_from_pipeline_json` (`state_tool.py:778-813`)은 `ts["key"]`를 row에 정상 주입(`state_tool.py:795`)한다. 캡틴 회피책(`--rows-from pipeline.json`)이 유효한 이유.

**key 자동 생성 규약** — `_auto_row_key` (`state_tool.py:1441-1457`)와 `KEY_PATTERN`(`state_tool.py:40`)은 key가 `{stage_slug}.{item_slug}(_N)?` 형식으로 **stage에 종속**됨을 보인다. 즉 key는 (stage, item)에 의미적으로 결속된다.

**row_id 변동성** — `cmd_add_row`는 행 삽입 후 row_id를 전체 재번호(`state_tool.py:1506-1508`)하지만 **기존 key는 불변**으로 유지한다. → row_id는 위치 인덱스로서 변동 가능, key/(stage,item)이 안정적 조인축이다.

### 2.3 영향 범위

- **호출자**: `main`/`build_parser` → `cmd_init` (`state_tool.py:2093-`). 인자 `--import-existing`(`dest=import_existing`), `--rows-from`, `--force`.
- **피호출자**: `parse_existing_state_md`, `build_rows_from_pipeline_json`, `load_state_md`, `save_state_json`, `render_pipeline_table` — 신규 헬퍼 외에는 시그니처 불변.
- **공유 상태**: state.json `rows[].key`가 070 `--task-step`/`--task-step-id` 주소 해석(`resolve_row_index` `state_tool.py:406`)의 SSOT. schema_version "1.1"이 key 주소 사용 전제.
- **관련 테스트**: `test_scenario_import_existing_success`(`tests:1424`), `test_scenario_import_existing_failure`(`tests:1467`), pipeline.json init 계열(`tests:4203-4302`), schema_version 계열(`tests:4284-4302`). 전량 250건(`pytest --collect-only`).

---

## 3. 기능별 설계 (Flat)

### 3.1 파일 변경 계획

**신규 생성**: 없음.

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 배치 | 신규 헬퍼 `_key_source_index`·`_reattach_import_keys` 추가 + `cmd_init` import 분기에 key 재접합 블록 삽입 | `state_tool.py:900-908`, `:932` |
| 2 | `opal/tools/state-tool/state_tool.py` | 문서 | @header DESCRIPTION 변경이력에 074 항목 추가 | (→ D-4 §@header 규칙) |
| 3 | `opal/tools/state-tool/tests/test_state_tool.py` | 배치 | RED-first 회귀 테스트 클래스 추가 (S-a~S-e) | (→ D-2) |

> [MUST] `docs/CONVENTIONS.md` §@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다" — state_tool.py DESCRIPTION에 074 변경이력 라인 추가 (→ D-4 §171-175).
> [MUST] TASK §제약: surgical — `state_tool.py` 단일 파일 + 테스트 파일만 수정, 인접 로직 개선 금지 (`opal/core/PRINCIPLES.md` §3).

### 3.2 API·데이터 모델·설계

#### 3.2.1 설계 결정 (TASK §PLAN에서 확정할 5개)

**DEC-1 — 매칭 알고리즘: (stage, item) 순서 소비(ordered consumption)를 1차 축으로 채택** (→ H-1, H-5)

- **근거**: (1) key 자체가 `{stage_slug}.{item_slug}` 형식으로 stage에 결속되어 (stage,item)이 자연 조인축이다 (`state_tool.py:40`, `:1446-1449`). (2) row_id는 import 파싱 시 순번으로 재부여되어(`state_tool.py:841`) 원본을 신뢰할 수 없고, add-row가 재번호(`state_tool.py:1506-1508`)하므로 위치 변동적이다.
- **알고리즘**: 원천 rows에서 `(stage,item) → [key,...]` 순서 큐를 만들고, import된 keyless rows를 **순서대로** 순회하며 동일 (stage,item) 큐에서 앞에서부터 pop해 부여한다. 동일 (stage,item)이 복수여도(예: 여러 단계의 "사용자 확인", 동일 단계 "작업" 중복) STATE.md가 state.json을 순서대로 렌더하므로 순서 소비로 1:1 정렬된다.
- **행 수/순서 불일치 처리**: 매칭 안 되는 import 행은 keyless로 남긴다(row-level graceful). 남는 원천 key는 무시. → best-effort 복구, 절대 오류로 중단하지 않는다.
- **rejected**: row_id 단독 매칭 — 재부여/재번호로 위치 변동적이라 hand-edited STATE.md(복구 시나리오의 흔한 원인)에서 오배정 위험.

**DEC-2 — pipeline.json 폴백: state.json에 key가 하나도 없을 때만, 그리고 재접합 후에도 keyless 행이 남을 때만 `--rows-from *.json`을 원천으로 재접합** (→ H-2)

- **중복 (stage,item) 처리**: DEC-1과 동일한 순서 소비. 스펙 task_steps 순서 == 초기 렌더 순서이므로 정렬 보장.
- **에러 전파**: `--rows-from`이 명시된 이상 스펙이 invalid면 `build_rows_from_pipeline_json`이 기존과 동일하게 `spec_validation_failed`로 err(`state_tool.py:786-787`) — 정상 경로와 일관.

**DEC-3 — schema_version 승격: line 932 로직 무변경, 재접합을 line 932 이전에 수행** (→ H-4)

- key 재접합을 import 파싱(`:908`) 직후 ~ schema_version 계산(`:932`) **이전**에 배치하면, `any(r.get("key") for r in rows)`가 자동으로 True가 되어 "1.1"이 stamp된다. line 932 자체는 수정하지 않는다(정합 유지). → [MUST] TASK §완료기준 (2) 충족.

**DEC-4 — --force 상호작용: key 원천 state.json을 덮어쓰기(`save_state_json` `:957`) 이전에 로드** (→ H-1)

- import 분기(`:900`)는 `save_state_json`(`:957`)보다 앞이므로, 이 시점 디스크의 기존 state.json은 아직 원본(key 보유)이다. line 950-955의 `created_at` 보존과 동일한 soft-load 패턴(`state_file.exists()` + `try/except json.loads`)으로 rows를 읽어 key 원천으로 사용한다. `load_state_json`(`:197`, 부재 시 err)은 쓰지 않는다(폴백 안전성).

**DEC-5 — 하위호환: key 원천 전무 시 keyless 유지 + stderr 경고 1줄** (→ H-3)

- 재접합 후에도 어떤 행에도 key가 없으면 stderr에 JSON 경고 1줄 출력(기존 deprecation 경고 패턴 `state_tool.py:919-920`과 동일 방식). stdout(ok 페이로드)은 불변 → 기존 테스트·소비자 불변. schema_version은 "1.0" 유지.

#### 3.2.2 신규 헬퍼 시그니처

```python
def _key_source_index(source_rows):
    """원천 rows에서 (stage,item) -> [key,...] 순서 큐 구성. key 없는 행은 제외.
    반환: dict[tuple[str,str], list[str]]"""

def _reattach_import_keys(imported_rows, source_rows):
    """imported_rows의 keyless 행에 source_rows의 key를 (stage,item) 순서 소비로 재접합.
    imported_rows를 in-place 수정. 반환: 재접합된 행 수(int).
    - 이미 key 있는 행은 건너뜀(체이닝 안전)
    - 동일 (stage,item) 큐에서 앞에서부터 pop → 중복 순서 정렬"""
```

#### 3.2.3 `cmd_init` 삽입 로직 (의사코드, `state_tool.py:908` 직후)

```python
# 074: keyless import rows에 key 재접합 (우선순위: 기존 state.json → pipeline.json)
if import_mode and rows:
    matched = 0
    # (1) 기존 state.json (DEC-4: 덮어쓰기 전 soft-load)
    if state_file.exists():
        try:
            _old_rows = json.loads(state_file.read_text(encoding="utf-8")).get("rows", [])
        except Exception:
            _old_rows = []
        if any(r.get("key") for r in _old_rows):
            matched += _reattach_import_keys(rows, _old_rows)
    # (2) pipeline.json 폴백 (DEC-2: 아직 keyless 행이 남고 .json 스펙이 있을 때만)
    if any(not r.get("key") for r in rows) and \
       getattr(args, "rows_from", None) and args.rows_from.endswith(".json"):
        matched += _reattach_import_keys(rows, build_rows_from_pipeline_json(args.rows_from, command, args.mode))
    # (3) 원천 전무 → 경고 (DEC-5: 하위호환)
    if not any(r.get("key") for r in rows):
        print('{"warning":"--import-existing: key 원천(기존 state.json/pipeline.json) 부재 — '
              'keyless 유지(하위호환). --task-step 주소 불가 (task 074)."}', file=sys.stderr)
```

> 설계 근거: import 분기 위치 `state_tool.py:900-908`, schema 승격 `state_tool.py:932`, force created_at soft-load 선례 `state_tool.py:950-955`, deprecation stderr 경고 선례 `state_tool.py:919-920`.

### 3.3 환경 변경

해당 없음 (표준 라이브러리만 사용, `state_tool.py:16-24`).

### 3.4 배치/마이그레이션

해당 없음. 기존 state.json/schema.json 스키마 무변경 — schema_version enum은 이미 "1.0"/"1.1" 허용(`tests:4325`).

### 3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R1 AC (key 100% 보존) | 회귀(RED-first) | 기존 state.json(key 보유) 존재 시 `init --force --import-existing` 후 rows[].key가 원본과 100% 일치 |
| TS-002 | R2 AC (pipeline 복원) | 회귀(RED-first) | state.json 없이 `--import-existing --rows-from mini.json` 시 rows[].key가 스펙 기준 복원 |
| TS-003 | R3 AC (하위호환) | 회귀(RED-first) | state.json·pipeline.json 모두 없을 때 keyless rows + stderr 경고 1줄, ok stdout 불변 |
| TS-004 | R4 AC (schema 1.1) | 회귀(RED-first) | key 보존된 import 결과 state.json의 schema_version == "1.1" |
| TS-005 | R5 AC (기존 불변) | 회귀 | 기존 테스트 250건 전량 통과, `test_scenario_import_existing_success` 불변 |
| TS-006 | R2 AC (중복 매칭) | 기능(edge) | 동일 (stage,item) 복수 행(예: 여러 단계 "사용자 확인")에서 순서 소비로 key 오배정 없이 정렬 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 (RED) | F-001 | 1 | opal-test-agent (mode: red) | 순차 | 오케스트레이터 디스패치 (red-first §2 작성자≠구현자) |
| 2 (GREEN) | F-001 | 2 | opal-task-agent | 순차 | RED FAIL 증거 후 진입 |
| 3 | F-001 | 3 | opal-task-agent | 순차 | Step 2와 동일 파일(묶음 가능) |
| 4 (검증) | F-001 | 4 | opal-test-agent | 순차 | 오케스트레이터 디스패치 |

### 4.2 실행 체크리스트

> 총 4개 Step | Phase 4개 | 실행 모드: 단순

#### Step 1: RED 회귀 테스트 작성 (실패 확인)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 배치
- **agent**: opal-test-agent (mode: red)
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: TS-001~004, TS-006 테스트 케이스 추가 (신규 클래스 `TestImportPreservesKeys`). state.json(key 보유) fixture 생성 → `init --force --import-existing` 후 key 100% 일치 단언 등. TEST-SCENARIO.md S-a~S-e 시나리오 구현.
- **완료 기준**: 신규 테스트가 수정 전 코드에서 **FAIL**(exit≠0) — RED 증거 기록 (red-first §1)
- **테스트**: TS-001, TS-002, TS-003, TS-004, TS-006
- **실행 방법**: sub-agent (오케스트레이터 디스패치)
- **의존**: 없음

#### Step 2: key 재접합 로직 구현 (GREEN)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: 신규 헬퍼 `_key_source_index`·`_reattach_import_keys` 추가(§3.2.2), `cmd_init` import 분기(`state_tool.py:908` 직후)에 재접합 블록 삽입(§3.2.3). line 932 무변경(DEC-3).
- **완료 기준**: Step 1 RED 테스트가 **PASS**(GREEN)로 전환. RED 테스트 파일 미수정(red-first §3).
- **테스트**: TS-001~004, TS-006
- **실행 방법**: direct
- **의존**: Step 1

#### Step 3: @header 변경이력 갱신
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: @header DESCRIPTION에 "074: --import-existing key-보존 재접합 — cmd_init import 분기가 파싱 후 기존 state.json→pipeline.json (stage,item) 순서 매칭으로 key 재접합(schema_version 1.1 유지), 원천 전무 시 keyless+경고(하위호환); _key_source_index/_reattach_import_keys 신규" 라인 추가.
- **완료 기준**: DESCRIPTION에 074 항목 존재. Step 2와 동일 파일이므로 함께 처리 가능.
- **테스트**: 산출물 검사 (@header 라인 존재)
- **실행 방법**: direct
- **의존**: Step 2

#### Step 4: 전량 회귀 검증
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 배치
- **agent**: opal-test-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -q` 전량 실행. 신규 포함 전건 PASS, 기존 250건 불변 확인.
- **완료 기준**: 전량 GREEN, 실패 0건. `test_scenario_import_existing_success` 불변 통과.
- **테스트**: TS-005
- **실행 방법**: sub-agent (오케스트레이터 디스패치)
- **의존**: Step 2, Step 3

> docs/ 갱신 Step: 불필요. 이 변경은 내부 도구 버그 수정으로 새 API/컴포넌트/시스템 구조 변경이 없다. `docs/CONVENTIONS.md` §State 관리(`--task-step` 우선)는 이미 070에서 반영됨 — 본 수정은 그 규칙의 복구 경로 정합을 회복할 뿐 규칙 자체 변경 없음.

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | RED 증거 후 GREEN 진입 (red-first §1) |
| Step 2 → Step 3 | 동일 파일 순차 수정 (state_tool.py) |
| Step 2, 3 → Step 4 | 구현·이력 완료 후 전량 검증 |

---

## 5. QA 체크리스트

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | state.json key 계승 (--force --import-existing) | TS-001 | rows[].key 원본과 100% 일치 |
| F-001 | pipeline.json 폴백 복원 | TS-002 | key가 스펙 기준 복원 |
| F-001 | 하위호환 keyless + 경고 | TS-003 | keyless 유지, stderr 경고 1줄, stdout 불변 |
| F-001 | schema_version 승격 | TS-004 | schema_version == "1.1" |
| F-001 | 중복 (stage,item) 순서 소비 | TS-006 | key 오배정 없음 |

### 5.2 회귀 테스트

- [ ] 기존 250건 전량 통과 (TS-005)
- [ ] `test_scenario_import_existing_success`(`tests:1424`) 불변 통과 — keyless import + 경고 시나리오로 재해석되나 단언(len==3)은 유지
- [ ] `test_scenario_import_existing_failure`(`tests:1467`) 불변 — import_failed 경로 무변경
- [ ] pipeline.json init 계열(`tests:4228-4302`) 불변

### 5.3 코드/문서 품질

- [ ] surgical 준수 — state_tool.py + 테스트 파일만 수정 (인접 로직 개선 금지)
- [ ] @header DESCRIPTION 074 변경이력 라인 추가 (→ D-4 §@header 규칙)
- [ ] 표준 라이브러리만 사용 (신규 import 없음)
- [ ] line 932 무변경 (DEC-3 정합)

### 5.4 보안

- [ ] 하드코딩 토큰/시크릿 없음 (도구 로직, 해당 없음)
- [ ] 파일 I/O는 task_path 경계 내 (기존 패턴 준수)
- [ ] soft-load try/except로 손상된 state.json에도 크래시 없음

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 4개 | 단순 |
| 변경 파일 수 | 2개 (state_tool.py, test_state_tool.py) | 단순 |
| 모듈 범위 | 단일 파일 | 단순 |
| 작업 유형 | 오류 수정(버그 fix) | 단순 |
| 외부 의존성 | 없음 (표준 라이브러리) | 단순 |
| **실행 모드** | **단순** | |

> 단순 모드 → §7 실행 아키텍처 생략.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| CLI 도구 | Python 3 (표준 라이브러리) | trailofbits/modern-python (참조 — 신규 패턴 미도입) |
| 테스트 | pytest / unittest | - |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 표준 라이브러리·기존 패턴만 사용, 외부 API 조회 불필요 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 결함 위치·수정 대상 (cmd_init `:900-908`, render `:271`, parse `:819`, schema `:932`, build_rows_from_pipeline_json `:778`) |
| D-2 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | 회귀 테스트 추가 대상·기존 테스트 패턴(import `:1424`, pipeline `:4203`) |
| D-3 | 설계 | 070 태스크 PLAN | `tasks/070-260720-opd-태스크스텝-키주소-1차/PLAN.md` | task-step key 주소 체계 원설계 |
| D-4 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | @header 규칙(§171-175)·변경이력 의무(§196-200)·State 관리(§183-188) |
| D-5 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | RED-first 트랙 규칙(§1 RED→GREEN, §2 작성자≠구현자, §3 테스트 불변) |

---

## 9. 리스크 및 대응

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 중복 (stage,item) 순서 소비가 hand-edited STATE.md(행 재배치)에서 오배정 | F-001 | P1 | best-effort 복구 문서화, 미매칭 행 keyless graceful, TS-006 edge 검증 |
| R-2 | 기존 `test_scenario_import_existing_success` 의미 변화(경고 추가) | F-001 | P1 | 경고는 stderr only, stdout ok 불변 → 단언 유지. TS-005 회귀 확인 |
| R-3 | pipeline.json 폴백 시 invalid 스펙이 init 전체를 err로 중단 | F-001 | P2 | 정상 경로와 동일한 `spec_validation_failed` 계약 — 의도된 동작. 폴백은 `--rows-from` 명시 시에만 |
| R-4 | 손상된 기존 state.json 읽기 실패 | F-001 | P2 | soft-load try/except로 무시하고 다음 원천/keyless로 진행 (DEC-4) |

> 용어 일관성(citation-rules §7): FE↔BE 등 영역 쌍 없음(단일 CLI 도구). `key`/`row_id`/`task-step` 용어는 070 설계(D-3)와 정합 유지 — 불일치 없음. `decision_required` 없음.
