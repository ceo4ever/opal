# PLAN: 명확화 게이트 — TASK 4요소 잠금 기계적 집행

> 작성일: 2026-06-16
> 입력: TASK.md (R-1~R-5, 확정 A안, "## 명확화 결과" 4요소)
> 출력: PLAN.md

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 헌법 | PRINCIPLES.md §1 | `opal/core/PRINCIPLES.md` | 집행 대상 원칙 (재서술 금지, 참조만) — §1 "Lock acceptance criteria" |
| D-2 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | R-1·R-3 대상 — verify/ERROR_CODES/cmd_mark 훅 구조 |
| D-3 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | 기존 테스트 패턴 + 신규 테스트 위치 |
| D-4 | 소스 | op-task SKILL | `opal/skills/op-task/SKILL.md` | R-2 대상 — STEP 4 템플릿 |
| D-5 | 설계 | opal-harness SSOT | `opal/core/references/opal-harness.md` | R-4 대상 — §1 Guards |
| D-6 | 선례 | task 013 PLAN/DONE | `tasks/013-260607-opds-state-tool-enforcement/` | `verify --red-check`·ERROR_CODES 구조 선례 |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | @header·변경이력·배포 경계·네이밍 규칙 |
| D-8 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §5 레거시 호환 — 하위호환 정책 근거 |

> **[경로 정정]** 디스패치 프롬프트·TASK.md는 `opal/tools/state-tool/` 와 `opal/core/tools/state-tool/`를 혼용하나, 실제 파일은 **`opal/tools/state-tool/`** 단일 경로다 (`find` 검증). 본 PLAN은 실재 경로 `opal/tools/state-tool/`만 사용한다. TASK.md "어디에" 기재 경로(`opal/core/tools/`)는 오기로 간주.

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/state-tool/state_tool.py` | state-tool CLI 본체 | **수정** | verify(`:1448-1514`)·ERROR_CODES(`:68-101`)·cmd_mark 자동훅(`:1002-1012`)·cmd_advance(`:839-874`)·argparse verify(`:1633-1650`) |
| `opal/tools/state-tool/tests/test_state_tool.py` | pytest 단위 테스트 | **수정** | TestVerify(`:1752`)·TestErrorCodes(`:1738-1745`)·make_args(`:89-120`)·BaseTestCase(`:123`) |
| `opal/skills/op-task/SKILL.md` | TASK.md 작성 스킬 | **수정** | STEP 4 템플릿(`:107-151`)·작성 체크리스트(`:223-236`)·변경이력(`:247-254`) |
| `opal/core/references/opal-harness.md` | 하네스 SSOT | **수정** | §1 Guards(`:8-55`)·변경이력 표(말미) |
| `opal/core/PRINCIPLES.md` | 헌법 §1 | 참조만 (수정 없음) | §1(`:18-21`) — 재서술 금지 |
| `opal/tools/state-tool/run.sh` | venv 래퍼 | 변경 없음 | 인자 passthrough(`exec ... "$@"`) — 신규 플래그 자동 지원 |

### 현재 상태

**state-tool verify 구조 (013/016 선례 — D-2)**:
- `cmd_verify(args)` (`:1448`)는 `--red-check`/`--fix-mode` 등 플래그를 `getattr(args, …, False)`로 읽고, 검사 결과를 `checks` 딕셔너리에 누적 → 성공 시 `{ok, command, scenario, checks}` 단일 라인 JSON + exit 0, 위반 시 `err(...)` → 단일 라인 JSON + exit 1.
- 대상 파일 부재는 **graceful skip** 패턴: `_find_scenario_file()` (`:1317`)이 `None`이면 `{ok:true, skipped:true, reason:...}` + exit 0 (`:1480-1486`). → 하위호환 권고안의 직접 선례.
- `--red-check`는 기본 비활성(미지정 시 검사 자체를 건너뜀) → 하위호환을 "플래그 옵트인"으로 처리한 선례 (`:1500-1507`).

**자동 훅 구조 (D-2)**:
- `cmd_mark` (`:891`)는 행을 done 처리한 직후, **`row["stage"] == "TEST"`이면 verify 검사(mock/evidence)를 자동 실행**하고 위반 시 `err("mark", ...)`로 거부한다 (`:1002-1012`). → 본 태스크 자동 훅의 **동형 선례**. 같은 위치(mark 본문)에 stage 조건만 바꿔 끼운다.
- 단계 전환 차단은 `check_stage_transition_guard` (`:341`), CLOSE 진입은 `check_close_gate` (`:392`)가 `cmd_advance`(`:855-859`)·`cmd_mark`(`:928-933`) **둘 다**에서 호출된다. → 명확화 게이트도 advance·mark 양쪽에 거는 동일 패턴이 필요(advance/mark 어느 쪽이 "다음 단계 첫 행"을 먼저 건드릴지 모르므로).
- `--auto-pass` 거부 선례: `check_close_gate`가 `auto_pass and mode in (agentic, semi-agentic)`이면 `agentic_close_gate_requires_user` err (`:407-408`). → 명확화 게이트도 동일 우회 불가 처리 가능.

**ERROR_CODES (D-2 `:68-101`)**: 30종 딕셔너리. 추가는 키-값 1행. 테스트 `EXPECTED_CODES` 리스트(`:1700-1736`)와 `test_error_codes_count`(현재 30종 단언, `:1740`)를 함께 갱신해야 함.

**op-task 템플릿 (D-4 `:107-151`)**: "확정된 설계 방향" 섹션(`:126`) 직후, "요구사항"(`:130`) 앞에 신규 섹션을 끼울 자리가 있다. TASK.md 본 태스크가 이미 "## 명확화 결과" 4요소 표를 dogfooding으로 작성해 둠(`tasks/005-…/TASK.md:86-95`) → 이 표 형식이 사실상 확정 스펙.

**harness §1 Guards (D-5 `:8-55`)**: "CLOSE 진입 게이트"(`:30-33`) 절이 게이트 1줄 + agentic 유지 문구의 선례 포맷. 명확화 게이트 절을 동형으로 추가.

### 영향 범위

- **코드**: `state_tool.py` 단일 파일에 함수 2~3개 신설 + cmd_mark/cmd_advance 훅 1줄씩 + argparse 플래그 1개 + ERROR_CODES 1행. 신규 패턴 도입 없음 (verify/훅 구조 재사용 — Simplicity First, → D-1 §2).
- **테스트**: `test_state_tool.py`에 신규 테스트 클래스 1개 + ERROR_CODES 단언 2곳 갱신. 기존 테스트는 **불변** (게이트가 graceful skip이면 기존 픽스처에 "명확화 결과" 섹션이 없으므로 발동 안 함 → 회귀 0).
- **문서**: op-task 템플릿·체크리스트, harness §1 — 텍스트 추가만. 기존 행동 변경 없음.
- **배포**: install-mac.sh로 `~/.opal/tools/state-tool/`·`~/.opal/skills/op-task/`·`~/.opal/references/opal-harness.md` 재배포 후 실호출 검증 (배포 경계 — `~/.opal` 직접편집 금지, → D-7 §배포 경계).

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| - | (없음) | state_tool.py 단일 파일 확장 — 신규 파일 없음 (Simplicity First) | → D-1 §2 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/tools/state-tool/state_tool.py` | ① ERROR_CODES에 `clarification_gate_unmet` 1행 추가 ② `_find_task_md()`·`_parse_clarification_table()`·`_check_clarification_gate()` 헬퍼 신설 ③ `cmd_verify`에 `--clarification-check` 분기 추가 ④ argparse verify 파서에 `--clarification-check` 플래그 추가 ⑤ cmd_mark·cmd_advance에 TASK→다음단계 첫 행 자동 훅 추가 | → D-2 |
| M-2 | `opal/tools/state-tool/tests/test_state_tool.py` | ① `TestClarificationGate` 클래스 신설 (verify 직접 호출 + 자동 훅) ② `EXPECTED_CODES`에 `clarification_gate_unmet` 추가 ③ `test_error_codes_count` 30→31 갱신 ④ `make_args`에 신규 플래그 기본값 추가 | → D-3 |
| M-3 | `opal/skills/op-task/SKILL.md` | STEP 4 템플릿에 "## 명확화 결과" 섹션 추가(확정된 설계 방향 직후) + 작성 체크리스트 1행 + 변경이력 1행 | → D-4 `:126` |
| M-4 | `opal/core/references/opal-harness.md` | §1 Guards에 "명확화 게이트" 절 1~2줄 추가 + 변경이력 1행 | → D-5 `:30` |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음) | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | RED: 명확화 게이트 테스트 작성 (실패 확인) | test_state_tool.py | 중 |
| 2 | GREEN: ERROR_CODES + verify --clarification-check 구현 | state_tool.py | 중 |
| 3 | GREEN: 자동 훅 (mark/advance) 구현 | state_tool.py | 중 |
| 4 | 전체 테스트 통과 + 회귀 0 확인 | test_state_tool.py | 하 |
| 5 | op-task 템플릿 "명확화 결과" 섹션 추가 | op-task/SKILL.md | 하 |
| 6 | harness §1 Guards 참조 1줄 + ERROR_CODES 참조 추가 | opal-harness.md | 하 |
| 7 | 변경이력 기재 + install 재배포 + 실호출 검증 | (전 파일) | 하 |

### 핵심 설계

> [MUST] `opal/core/PRINCIPLES.md` §1: "Lock acceptance criteria before execution. Criteria added later are rationalization." — 본 게이트가 집행하는 원칙. PLAN/하네스/스킬은 이 문구를 **복제하지 않고 참조만** 한다 (→ D-1 §Governance: "Lower docs reference these principles; they don't restate them.").
>
> [MUST] `opal/core/PRINCIPLES.md` Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." — 게이트를 prose가 아닌 state-tool로 구현하는 근거.
>
> [MUST] TASK.md §제약: "state-tool 선례 정합 — task 013 verify --red-check 구조·ERROR_CODES 패턴을 따른다(신규 패턴 도입 최소화, Simplicity First)."
>
> [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스에서 수행한다." — install 재배포 경로로만 검증.
>
> [MUST] `docs/CONVENTIONS.md` §언어/네이밍: Python 파일은 snake_case(함수·헬퍼명), 본문은 한국어 + 영어 코드/필드명.

---

#### M-1: `state_tool.py` — verify --clarification-check + 자동 훅

**(1) ERROR_CODES 신규 1행** (`:68-101` 딕셔너리 말미, RED-first 트랙)

```python
"clarification_gate_unmet":
    "TASK 4요소(목표/범위/제약/완료기준) 미잠금 — 다음 단계 진입 거부 (PRINCIPLES §1 집행): {missing}",
```

- 키명은 TASK R-1/R-3 AC가 명시한 `clarification_gate_unmet` 그대로 (→ TASK.md:40,50). 변형 금지.
- `{missing}` 포맷 필드 — `err(...)` 호출 시 `missing=[...]`로 채운다 (기존 `err` 템플릿 포맷 메커니즘 재사용, `:128-133`).

**(2) 헬퍼 함수 3종 신설** (verify 헬퍼군 `:1305-1445` 근처에 배치 — `_find_scenario_file` 패턴 미러)

```python
def _find_task_md(task_path, task_md_arg):
    """TASK.md 경로 결정. --task-md 우선, 없으면 <task_path>/TASK.md. 부재 시 None."""
    p = pathlib.Path(task_md_arg) if task_md_arg else pathlib.Path(task_path) / "TASK.md"
    return p if p.exists() else None
```

```python
# 명확화 4요소 — 행 라벨(첫 셀)에서 식별. 순서/표기 변형 흡수를 위해 키워드 매칭.
_CLARIFICATION_ELEMENTS = ["목표", "범위", "제약", "완료기준"]
# "N/A: <사유>" 는 PASS로 간주 (명시적 해당없음). 공란·"TBD"(대소문자 무관)·"-" 단독은 FAIL.
_NA_PATTERN = re.compile(r"^N/?A\s*[:：]", re.IGNORECASE)
_TBD_PATTERN = re.compile(r"^\s*(TBD|-)?\s*$", re.IGNORECASE)

def _parse_clarification_table(lines):
    """TASK.md "## 명확화 결과" 섹션의 표를 파싱.
    반환: {element_label: confirmed_value_cell_text} 딕셔너리.
    섹션/표 부재 시 None 반환 (호출자가 graceful skip 또는 FAIL 판정).
    "확정값" 열을 헤더에서 식별; 없으면 2번째 셀(라벨 다음)을 확정값으로 간주.
    """
    # 1) "## 명확화 결과" 헤더 위치 탐색 → 다음 ## 헤더 직전까지 섹션 추출
    # 2) 표 헤더 행에서 "확정값" 열 인덱스 식별
    # 3) 데이터 행 파싱 → 첫 셀이 4요소 키워드를 포함하면 {라벨: 확정값셀}
    ...
```

```python
def _check_clarification_gate(task_md_path):
    """4요소 잠금 검증. 반환: missing[] (빈 리스트면 PASS).
    None 반환 = 섹션/표 부재 (호출자가 하위호환 정책 적용 — graceful skip).
    각 요소: 확정값 셀이 공란/"TBD"/"-"이면 미충족. "N/A: <사유>"는 충족."""
    lines = task_md_path.read_text(encoding="utf-8").splitlines()
    table = _parse_clarification_table(lines)
    if table is None:
        return None                      # 섹션/표 부재 신호
    missing = []
    for elem in _CLARIFICATION_ELEMENTS:
        cell = table.get(elem)
        if cell is None:                 # 요소 행 자체가 표에 없음
            missing.append(elem)
        elif _NA_PATTERN.match(cell.strip()):
            continue                     # N/A: <사유> → PASS
        elif _TBD_PATTERN.match(cell):   # 공란 / TBD / "-" → FAIL
            missing.append(elem)
    return missing
```

- 알고리즘 요지 — TASK R-1 AC와 디스패치 명세 정합 (→ TASK.md:40):
  - "## 명확화 결과" 섹션 파싱 → 4요소(목표/범위/제약/완료기준) 행의 **확정값** 셀 검사.
  - 셀이 공란 / "TBD" / "-" 단독 → 해당 요소 `missing`에 추가.
  - "N/A: <사유>" → PASS (명시적 해당없음, TASK R-2 AC "명시적 N/A: <사유>로 채운다"와 정합 — TASK.md:45).
  - 요소 행 누락 → `missing`에 요소명 추가.

**(3) cmd_verify 분기 추가** (`:1448-1514`, `--red-check` 분기와 동형 — `:1500-1507`)

```python
    clarification_check = getattr(args, "clarification_check", False)
    task_md_arg = getattr(args, "task_md", None)
    # ... (기존 fix_mode / scenario 처리 앞 또는 독립 분기로)
    if clarification_check:
        task_md_path = _find_task_md(task_path, task_md_arg)
        if task_md_path is None:
            # [하위호환 정책 §3 결정 항목] 파일 부재 → FAIL (정책 B) 또는 skip (정책 A)
            ...   # §3 decision_required 참조 — 권고안=정책 A(graceful skip)
        missing = _check_clarification_gate(task_md_path)
        if missing is None:
            # 섹션/표 부재 → 하위호환 정책 분기 (§3 권고안 = graceful skip + skipped:true)
            print(json.dumps({"ok": True, "command": command,
                              "clarification_check": "skipped",
                              "reason": "no '## 명확화 결과' section (backward-compat skip)"},
                             ensure_ascii=False)); sys.exit(0)
        if missing:
            err(command, "clarification_gate_unmet", missing=missing)
        print(json.dumps({"ok": True, "command": command,
                          "clarification_check": "pass"}, ensure_ascii=False)); sys.exit(0)
```

- 출력 JSON: 성공 `{ok:true, command:"verify", clarification_check:"pass"}` exit 0. 위반 `{ok:false, command:"verify", error:"clarification_gate_unmet", message:..., missing:[...]}` exit 1 (`err()`가 exit 1 — `:137`). TASK R-1 AC의 `{"ok": false, "error": "clarification_gate_unmet", ...}` 비정상 종료와 정합 (→ TASK.md:40).
- **`--clarification-check`는 기존 mock/evidence/red 검사와 독립** — 동시 지정 시 clarification 분기를 우선 처리 후 반환(verify 한 호출당 한 검사 책임, fix_mode와 같은 조기 반환 패턴 — `:1462-1477`).

**(4) argparse verify 파서 확장** (`:1633-1650`)

```python
    p_vfy.add_argument("--clarification-check", action="store_true", dest="clarification_check",
                       help="TASK 4요소 잠금 게이트 — 미충족 시 clarification_gate_unmet (PRINCIPLES §1 집행)")
    p_vfy.add_argument("--task-md", metavar="<path>", dest="task_md",
                       help="TASK.md 경로 명시 (기본: <task-path>/TASK.md)")
```

**(5) 자동 훅 — TASK→다음 단계 첫 행 진입 시 clarification-check 자동 실행** (TASK R-3, 확정 #3·#4)

- **발동 지점**: `cmd_mark`·`cmd_advance` **양쪽**에 동일 헬퍼 `_run_clarification_hook(task_path, state, row_index, command)` 호출을 삽입한다. 위치는:
  - `cmd_advance`: `check_close_gate(...)` 직후 (`:859` 뒤).
  - `cmd_mark`: `check_close_gate(...)` 직후 (`:933` 뒤). (TEST-stage verify 훅 `:1002`은 done 처리 *후*지만, 명확화 훅은 **진입 차단**이므로 상태 변경 *전*에 둔다 — close_gate와 동일 위치.)
- **훅 발동 조건** (close_gate의 "CLOSE 첫 행" 판정 `:402` 동형):
  ```python
  def _run_clarification_hook(task_path, state, row_index, command, auto_pass=False, force=False):
      row = state["rows"][row_index]
      rows = state["rows"]
      # TASK 단계가 존재하고, 대상 행이 "TASK 다음 단계의 첫 행"일 때만 발동
      task_stage_exists = any(r["stage"] == "TASK" for r in rows)
      if not task_stage_exists or row["stage"] == "TASK":
          return
      is_first_of_stage = (row_index == 0 or rows[row_index-1]["stage"] != row["stage"])
      # 직전 행이 TASK 단계(= TASK 마지막 필수 행 직후 첫 다음단계 행)인지
      prev_is_task = row_index > 0 and rows[row_index-1]["stage"] == "TASK"
      if not (is_first_of_stage and prev_is_task):
          return
      # --auto-pass 우회 거부 (close_gate 동형, §2.16 G-13 정합)
      if auto_pass:
          err(command, "clarification_gate_unmet",
              missing=["auto-pass cannot bypass clarification gate"])
      if force:
          return                              # --force --note 경로만 우회 허용 (긴급 탈출구)
      task_md = _find_task_md(task_path, None)
      if task_md is None:
          return                              # 하위호환: TASK.md 자체 부재 → skip
      missing = _check_clarification_gate(task_md)
      if missing is None:
          return                              # 하위호환: "명확화 결과" 섹션 부재 → skip
      if missing:
          err(command, "clarification_gate_unmet", missing=missing)
  ```
- **`--auto-pass` 거부**: TASK R-3 AC "agentic `--auto-pass`도 거부"와 정합 — close_gate가 auto-pass를 거부하는 패턴(`:407-408`)을 그대로 따른다 (→ TASK.md:50).
- **"마지막 필수 행 done 이후" 판정**: 다음 단계 첫 행을 advance/mark하려는 시점에는 이미 `check_stage_transition_guard`(`:341`)가 "앞 행 미완 시 stage_transition_violation"으로 차단한다. 즉 TASK 행이 전부 done이어야만 다음 단계 첫 행에 도달 → 훅이 "TASK 완료 직후" 시점에 정확히 1회 발동함이 보장된다(추가 상태 추적 불필요, Simplicity First).

#### M-2: `test_state_tool.py` — RED-first 테스트

- **`make_args` 기본값 추가** (`:89-120`): `"clarification_check": False, "task_md": None` (verify 직접 호출 시 AttributeError 방지 — 단, cmd_verify는 `getattr` 방어가 있어 필수는 아니나 명시 권장).
- **`TestClarificationGate(BaseTestCase)` 신설** — `TestVerify`의 `_write_scenario`/`_call_verify` 패턴 미러:
  - 헬퍼 `_write_task_md(content)` / `_call_clarification_verify()`.
  - 케이스(최소): ① 4요소 채워짐 → PASS exit 0 ② 1요소 공란 → FAIL `clarification_gate_unmet` exit 1 + `missing` 포함 ③ 1요소 "TBD" → FAIL ④ 섹션 부재 → skip ok exit 0 ⑤ TASK.md 파일 부재 → skip ok exit 0 ⑥ "N/A: <사유>" → PASS ⑦ 자동 훅: TASK 완료 후 다음 단계 첫 행 mark 시 미충족 → 거부 ⑧ 자동 훅: 충족 시 통과 ⑨ 자동 훅: `--auto-pass` 거부.
  - **회귀 보호 테스트**: 기존 SIMPLE/SAMPLE rows_spec 픽스처(명확화 섹션 없는 STATE)로 mark 진행 시 게이트 미발동 확인.
- **ERROR_CODES 단언 갱신**: `EXPECTED_CODES`(`:1700-1736`)에 `"clarification_gate_unmet"` 추가 + `test_error_codes_count`(`:1738-1740`) 30 → 31.

#### M-3: `op-task/SKILL.md` — "## 명확화 결과" 섹션

- STEP 4 템플릿(`:126` "## 확정된 설계 방향" 직후, `:130` "## 요구사항" 앞)에 삽입:

```markdown
## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다 (공란·TBD 금지).
> 미잠금 시 다음 단계(PLAN 등) 진입이 state-tool `verify --clarification-check`로 거부된다 (PRINCIPLES §1 집행).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | {1-2문장 확정} | - | - |
| 범위 | {포함/제외 확정} | - | - |
| 제약 | {기술·정책 제약} | - | - |
| 완료기준 | {검증 가능 기준} | - | - |
```

- 본 태스크 TASK.md가 작성해 둔 표(`tasks/005-…/TASK.md:90-95`)와 열 구성 동일 (확정값/미확정/의존 사실) — dogfooding 스펙 일치.
- TASK R-2 AC 정합: "확정된 설계 방향 직후 추가", "4요소별 확정값/미확정/의존 사실 열", "공란·TBD 금지" (→ TASK.md:45).
- 작성 체크리스트(`:223-236`)에 1행 추가: "[ ] '## 명확화 결과' 섹션에 4요소가 확정값 또는 'N/A: <사유>'로 잠겼는가 (공란·TBD 금지)".
- 변경이력(`:247-254`)에 1행: `| v1.9 | {KST} | STEP 4 템플릿에 "명확화 결과" 4요소 섹션 추가 — verify --clarification-check 검증 대상 표준화 (005) |`.

#### M-4: `opal-harness.md` §1 Guards — 참조 1줄 (재서술 금지)

- §1 "CLOSE 진입 게이트"(`:30-33`) 절 형식을 미러하여 신규 절 추가:

```markdown
### 명확화 게이트 (PRINCIPLES §1 집행)

TASK 4요소(목표·범위·제약·완료기준)가 TASK.md "## 명확화 결과" 섹션에 잠기지 않으면 다음 단계(PLAN 등) 진입 불가.
state-tool `verify --clarification-check`가 집행하며, 미충족 시 ERROR_CODES `clarification_gate_unmet`로 거부한다(agentic `--auto-pass` 우회 불가).
```

- TASK R-4 AC 정합: "§1 Guards에 1~2줄 + ERROR_CODES `clarification_gate_unmet` 참조 + PRINCIPLES §1 복제 금지" (→ TASK.md:55).
- **재서술 금지 준수**: 원칙 문구("Lock acceptance criteria…")를 복제하지 않고 "PRINCIPLES §1 집행"으로 참조만 한다 (→ D-1 §Governance).
- 변경이력 표 말미에 1행: `| v5.5 | {KST} | §1 Guards에 "명확화 게이트" 절 추가 — TASK 4요소 미잠금 시 다음 단계 진입 차단, state-tool --clarification-check 집행 + clarification_gate_unmet 참조 (005) |`.

---

## 3. 실행 체크리스트

> 총 7개 Step | Phase 5개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 순차 | RED 테스트 — state_tool.py 변경 전 작성·실패 확인 (RED-first 트랙) |
> | 2 | 2, 3 | 순차 | 동일 파일(state_tool.py) 수정 — 반드시 순차 |
> | 3 | 4 | 순차 | 전체 테스트 통과·회귀 확인 (Step 1~3 의존) |
> | 4 | 5, 6 | 병렬 | 독립 파일(op-task SKILL / harness) |
> | 5 | 7 | 순차 | 변경이력·배포·실호출 검증 (전 Step 의존) |
>
> **트랙 표기**: Step 1~4 = state-tool 코드 변경 → **RED-first 트랙**(게이트 로직=self-confirming 위험 영역, 헌법 §4). Step 5~7 = 문서/배포 트랙.

### Step 1: RED — 명확화 게이트 테스트 작성 (실패 확인)
- [ ] 완료
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: `TestClarificationGate` 클래스 신설 (M-2 케이스 ①~⑨ + 회귀 보호). `EXPECTED_CODES`에 `clarification_gate_unmet` 추가, `test_error_codes_count` 30→31. `make_args`에 `clarification_check`/`task_md` 기본값 추가.
- **완료 기준**: 신규 테스트가 **실패**한다(미구현이므로 FAIL/ERROR). 실패 출력(RED 증거)을 캡처한다. 기존 테스트는 영향 없음.
- **테스트**: `python -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestClarificationGate -v` → 신규 케이스 실패 확인.
- **의존**: 없음
- **RED-first**: 예 (RED 증거 선확보)

### Step 2: GREEN — ERROR_CODES + verify --clarification-check 구현
- [ ] 완료
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: M-1 (1)ERROR_CODES 1행 + (2)헬퍼 3종(`_find_task_md`/`_parse_clarification_table`/`_check_clarification_gate`) + (3)cmd_verify `--clarification-check` 분기 + (4)argparse `--clarification-check`/`--task-md` 플래그.
- **완료 기준**: Step 1 케이스 ①~⑥(verify 직접 호출분)이 GREEN. `verify <task> --clarification-check` 실호출 시 채워짐 PASS / 누락·TBD FAIL / 섹션·파일 부재 skip이 명세대로 동작.
- **테스트**: `pytest ...::TestClarificationGate -v` 중 verify 직접 케이스 통과.
- **의존**: Step 1
- **RED-first**: 예

### Step 3: GREEN — 자동 훅 (mark/advance) 구현
- [ ] 완료
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: M-1 (5) `_run_clarification_hook` 신설 + cmd_advance(`:859` 뒤)·cmd_mark(`:933` 뒤)에 훅 호출 삽입. `--auto-pass` 거부, `--force` 우회, 섹션/파일 부재 skip 처리.
- **완료 기준**: Step 1 케이스 ⑦~⑨(자동 훅) + 회귀 보호 케이스 GREEN. TASK 완료 후 다음 단계 첫 행 mark/advance 시 미충족이면 `clarification_gate_unmet` 거부, 충족이면 통과.
- **테스트**: `pytest ...::TestClarificationGate -v` 전체 통과.
- **의존**: Step 2
- **RED-first**: 예

### Step 4: 전체 테스트 통과 + 회귀 0 확인
- [ ] 완료
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py` (실행)
- **작업 내용**: 전체 테스트 스위트 실행. 기존 TestVerify/TestMark/TestAdvance/TestErrorCodes 등 **전부 통과** 확인 (게이트 graceful skip이므로 기존 픽스처에 미발동).
- **완료 기준**: `pytest opal/tools/state-tool/tests/test_state_tool.py` 전 케이스 통과(회귀 0). 신규 케이스 포함 전부 GREEN.
- **테스트**: `python -m pytest opal/tools/state-tool/tests/test_state_tool.py -v` → 0 failed.
- **의존**: Step 3
- **RED-first**: -

### Step 5: op-task 템플릿 "명확화 결과" 섹션 추가
- [ ] 완료
- **파일**: `opal/skills/op-task/SKILL.md`
- **작업 내용**: M-3 — STEP 4 템플릿에 "## 명확화 결과" 섹션(확정된 설계 방향 직후) + 작성 체크리스트 1행 + 변경이력 v1.9 1행.
- **완료 기준**: 템플릿에 4요소(목표/범위/제약/완료기준) 표 + 공란·TBD 금지 안내 + N/A 허용 명시 존재. TASK R-2 AC 충족.
- **테스트**: 문서 검토 — 섹션 위치·열 구성·안내 문구 확인 (PM Gate).
- **의존**: 없음

### Step 6: harness §1 Guards 참조 1줄 + ERROR_CODES 참조 추가
- [ ] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: M-4 — §1 "명확화 게이트" 절 1~2줄(PRINCIPLES §1 집행 + clarification_gate_unmet 참조, 원칙 복제 금지) + 변경이력 v5.5 1행.
- **완료 기준**: §1 Guards에 절 존재, PRINCIPLES §1 문구 복제 없이 참조만, ERROR_CODES 키 명시. TASK R-4 AC 충족.
- **테스트**: 문서 검토 — 재서술 금지 준수 확인 (PM Gate).
- **의존**: 없음

### Step 7: 변경이력 + install 재배포 + 실호출 검증
- [ ] 완료
- **파일**: `state_tool.py` @header 변경이력, (M-3·M-4 변경이력은 Step 5·6에서 기재)
- **작업 내용**: state_tool.py @header `description`에 "005: verify --clarification-check + TASK→다음단계 자동 훅" 1구 추가. `./scripts/install-mac.sh` 실행 → `~/.opal/tools/state-tool/`·`~/.opal/skills/op-task/SKILL.md`·`~/.opal/references/opal-harness.md` 재배포. 배포본으로 실호출 검증.
- **완료 기준**: 재배포 후 `~/.opal/tools/state-tool/run.sh verify <임시 task with 4요소 채워진 TASK.md> --clarification-check` → `{ok:true}` exit 0, 누락 TASK.md → `clarification_gate_unmet` exit 1. 배포 경계 위반 0(`~/.opal` 직접편집 없음).
- **테스트**: 실호출 2건(PASS/FAIL) + exit code 확인.
- **의존**: Step 1~6

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] R-1: `verify --clarification-check`가 4요소 채워짐→`{ok:true}` exit 0, 누락/TBD→`{ok:false, error:"clarification_gate_unmet", missing:[...]}` exit 1, 섹션/파일 부재→skip(하위호환 정책)으로 동작하는가
- [ ] R-1: 단위 테스트(채워짐 PASS / 누락 FAIL / 섹션부재 처리)가 통과하는가
- [ ] R-2: op-task 템플릿에 "## 명확화 결과" 4요소 표가 확정된 설계 방향 직후 추가되고 공란·TBD 금지·N/A 허용이 명시되었는가
- [ ] R-3: TASK 마지막 행 done 후 다음 단계 첫 행 advance/mark 시 미충족이면 `clarification_gate_unmet` 거부, `--auto-pass`도 거부, 충족 시 통과하는가
- [ ] R-3: 자동 훅 거부/통과 단위 테스트가 통과하는가
- [ ] R-4: harness §1 Guards에 명확화 게이트 절 + ERROR_CODES 참조가 추가되고 PRINCIPLES §1 문구 복제가 없는가
- [ ] R-5: 변경 파일 변경이력 행 추가 + install 재배포 + 실호출 검증 완료

### 일관성 테스트
- [ ] 기존 state-tool 테스트 전체 통과(회귀 0) — graceful skip으로 기존 픽스처 미발동
- [ ] ERROR_CODES 키명 `clarification_gate_unmet`이 코드·테스트·harness·TASK AC에서 동일 토큰으로 일치 (용어 일관성 — citation-rules §7)
- [ ] verify `--red-check`/`--clarification-check` 구조 동형 — 신규 패턴 미도입(Simplicity First)
- [ ] 자동 훅이 close_gate/transition_guard와 동일 발동 위치·우회 규칙(force/auto-pass)을 따르는가
- [ ] op-task 템플릿 4요소 표 ↔ verify 파서 인식 키워드(목표/범위/제약/완료기준) 일치

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] Python 함수/헬퍼명 snake_case, 파일/폴더 kebab-case(또는 Python snake_case)를 따르는가
- [ ] 변경이력 행에 KST 일시 + 태스크 005 참조가 포함되는가
- [ ] PRINCIPLES §1 원문을 복제하지 않고 참조만 했는가 (재서술 금지 — D-1 §Governance)

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-T1 | **[decision_required] 하위호환 정책 미확정** — 기존 태스크(섹션 부재) 회귀 | 강제 시 기존 in-flight 태스크 다음 단계 진입 전면 차단 | §아래 권고안 — graceful skip(권고) vs 강제. PM/캡틴 최종 결정 (decision_required) |
| R-T2 | 자동 훅 오발동 — 동일 stage 반복 행/CLOSE 등에서 의도치 않게 발동 | 정상 진행 차단 | 훅 발동 조건을 "직전 행이 TASK + 대상이 다음 단계 첫 행"으로 한정. 단위 테스트로 비발동 케이스(같은 stage 2번째 행, TASK 행 자체) 검증 |
| R-T3 | verify 단일 호출에 `--clarification-check`+`--red-check` 동시 지정 시 책임 혼선 | 검사 누락 가능 | clarification 분기를 조기 반환(fix_mode 패턴 동형)으로 분리 — verify 1호출 1검사 책임 |
| R-T4 | "확정값" 셀 식별 실패 — 표 헤더 표기 변형(확정값/결정 등) | 파싱 오류 → 오탐 | 헤더에서 "확정값" 열 인덱스 식별, 미발견 시 라벨 다음 셀(2번째)을 확정값으로 폴백. 테스트로 표 변형 케이스 커버 |
| R-T5 | "N/A" 표기 변형(N/A, NA, n/a, 해당없음) | PASS 오판/누락 | `_NA_PATTERN` 정규식으로 `N/A:`·`NA:` 흡수. "해당없음"은 비지원(템플릿 안내에 "N/A: <사유>" 고정 표기 강제) |
| R-T6 | 배포 경계 위반 위험 — `~/.opal` 직접 편집 | 헌법/메모리 위반 | [MUST] 프로젝트 소스만 수정, install 재배포로만 검증 (D-7 §배포 경계, `feedback_deploy_boundary`) |
| R-T7 | ERROR_CODES 개수 단언 테스트(30 하드코딩) 미갱신 | 테스트 실패 | Step 1에서 30→31 동시 갱신 (M-2에 명시) |
| R-T8 | RED-first 트랙 미준수 — 게이트 로직 self-confirming 위험 | 게이트가 실제로는 미작동인데 통과로 오인 | Step 1 RED 선작성·실패 캡처 강제, 헌법 §4 준수 |

---

### [decision_required] 하위호환 정책 — 권고안

> **결정 항목**: 기존 태스크(="## 명확화 결과" 섹션 없음)에 대해 명확화 게이트를 어떻게 처리할 것인가. PM/캡틴 최종 결정 필요.

**정책 A — graceful skip (권고)**: "## 명확화 결과" 섹션이 **있는** TASK.md에만 게이트가 발동한다. 섹션/파일 부재 시 `{ok:true, clarification_check:"skipped"}` exit 0으로 통과시킨다.

**정책 B — 강제**: 섹션 부재 시 `clarification_gate_unmet`으로 FAIL. 모든 태스크가 "## 명확화 결과" 섹션을 갖도록 강제.

| 축 | 정책 A (graceful skip) | 정책 B (강제) |
|----|----------------------|--------------|
| 기존 in-flight 태스크 | 영향 없음 (회귀 0) | 다음 단계 진입 전면 차단 (회귀 발생) |
| 신규 태스크 집행력 | op-task 템플릿이 섹션을 항상 생성 → 신규는 100% 게이트 적용 | 동일 |
| 선례 정합 | `_find_scenario_file → None → skip ok` (verify 013, `:1480-1486`) + citation-rules §5 "기존 산출물 소급 변경 불필요" 와 정합 | 선례 없음 (신규 강제 패턴) |
| Simplicity First | 신규 분기 0 (기존 skip 패턴 재사용) | 별도 회귀 마이그레이션 필요 |
| 구현 위험 | 낮음 | 높음 (기존 태스크 일괄 섹션 추가 작업 수반) |

**권고: 정책 A (graceful skip)**
- 근거 1 — **선례 정합**: state-tool의 모든 verify 게이트(mock/evidence/red)가 "대상 산출물 부재 시 graceful skip" 패턴을 채택(`:1480-1486`). 명확화 게이트만 강제하면 일관성이 깨진다.
- 근거 2 — **citation-rules §5 레거시 호환**: "이 규칙 도입 이전 산출물은 소급 변경하지 않는다. 신규 태스크부터 적용한다." — 정책 A와 직접 정합 (→ D-8 §5).
- 근거 3 — **TASK 제약 정합**: TASK.md §제약 "게이트는 '명확화 결과' 섹션이 있는 신규 TASK에만 발동하되, 섹션 부재 기존 태스크 회귀 영향은 PLAN에서 하위호환 정책으로 명시"(→ TASK.md:68) — 정책 A가 이 의도("신규에만 발동")와 일치.
- 근거 4 — **집행력 손실 없음**: op-task 템플릿(M-3)이 신규 TASK.md에 섹션을 항상 생성하므로, 신규 태스크는 정책 A에서도 예외 없이 게이트가 적용된다. graceful skip은 "구 산출물"에만 적용되는 안전망일 뿐 신규 집행력을 약화시키지 않는다.

```json
{
  "decision_required": [
    {
      "type": "backward_compat_policy",
      "summary": "기존 태스크('명확화 결과' 섹션 부재) 명확화 게이트 처리 — graceful skip vs 강제",
      "options": ["A: graceful skip (권고)", "B: 강제 FAIL"],
      "recommendation": "A",
      "areas": ["state-tool"],
      "source_refs": [
        "opal/tools/state-tool/state_tool.py:1480-1486",
        "opal/core/references/harness/citation-rules.md:241-243",
        "tasks/005-260616-opds-clarification-gate/TASK.md:68"
      ],
      "rationale": "verify 게이트 graceful skip 선례 + citation-rules §5 레거시 호환 + op-task 템플릿이 신규 집행력 보장 → 회귀 0이면서 신규 집행 100%",
      "escalation": "agentic 모드에서도 사용자 결정 필수 (citation-rules §7.5 결정성 이슈)"
    }
  ]
}
```
