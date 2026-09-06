# PLAN: 파이프라인 사용자 확인 행 — 자동 승인 경로 일원화

> 작성일: 2026-08-15 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (기능 6개 — ANALYSIS.md가 F-1~F-6을 명시)
> 문서 루트: `/Volumes/Data/AiStudio/workspace/opal/tasks/093-260815-opd-사용자확인행-자동승인-일원화/`
> 코드 루트: `/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_093/` (HEAD `d58a5df`) — 본 문서의 모든 코드 인용은 이 루트 기준이다

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

사용자 확인 행의 상태 전이를 `pending → done/auto`(자동 승인) 또는 `pending → done/user`(캡틴 승인) 단일 축으로 일원화한다. agentic 전용 우회였던 init 시점 `na` 소거 분기 3곳을 제거하고(F-1), 그 자리를 "다음 단계 진입 시 도구가 자동 승인"하는 훅으로 대체한다(F-2). 자동 승인 가능 여부 판정은 단일 함수로 통합하고(F-3), 불가 구간에서는 조치 지시가 담긴 전용 에러를 반환한다(F-4). 부수적으로 mark 멱등성(F-5)과 기존 `na` 하위호환·문서 정합(F-6)을 확보한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | agentic auto-na 분기 제거 (교체형) | R-1 (TASK.md F-1) | P0 | F-002 (동시 배포 필수) |
| F-002 | 자동 승인 훅 신설 | R-2 (TASK.md F-2) | P0 | F-003, F-004 |
| F-003 | 모드별 자동 승인 경계 단일 판정 | R-3 (TASK.md F-3) | P0 | 없음 |
| F-004 | 승인 필요 구간 전용 에러 | R-4 (TASK.md F-4) | P0 | F-003 |
| F-005 | mark 멱등성 | R-5 (TASK.md F-5) | P1 | 없음 |
| F-006 | 하위호환 + 문서 정합 | R-6 (TASK.md F-6) | P1 | F-001, F-002 |

> [MUST] `docs/CONVENTIONS.md` §언어 규칙: "코드/변수/필드명 — English" · "파일/폴더 이름 — English, kebab-case (Python 파일은 snake_case)" — 신규 함수·에러 코드 키는 영문 snake_case로 명명한다.
> [MUST] `docs/CONVENTIONS.md` §State 관리: "파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. 마크다운 표 직접 편집 금지." — 본 태스크의 어떤 검증 Step도 STATE.md/state.json을 손편집하지 않는다.
> [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다." — 전역 배포(`install-mac.sh`)는 CLOSE 이후 캡틴 수동 실행이며 본 PLAN의 Step에 포함하지 않는다.
> [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" — F-006 문서 Step의 완료 기준에 포함한다.
> [MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자의 확인된 지시(`승인`, `확인`, `확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가." — 설계 쟁점 2(CLOSE 제외 구조적 보장)의 상위 근거다.
> [MUST] `.opal/AGENT.md` §업무 수행 지침: "하네스 변경 시 `opal/core/references/opal-harness.md`(SSOT)를 수정한다. 다른 곳에서 발췌·복제하지 않는다."

### 1.3 기능 의존 그래프 (ASCII)

```
F-003 (단일 판정) ─┬─ F-004 (전용 에러) ─┐
                   │                     ├─ F-002 (자동 승인 훅) ─┬─ F-001 (auto-na 제거)
                   └─────────────────────┘                        └─ F-006 (하위호환·문서)
F-005 (mark 멱등성) ── 독립 (F-002와 같은 파일 구간이라 순차 배치)
```

> F-001과 F-002는 **동시 배포 필수**다. F-001만 먼저 배포하면 agentic 파이프라인에서 사용자 확인 행이 `pending`으로 남아 `check_stage_transition_guard`(`opal/tools/state-tool/state_tool.py:634-679`)가 다음 단계 진입을 전면 차단한다 — ANALYSIS §A.5 #3이 실측한 회귀 패턴 그대로다. 따라서 §4.1에서 F-001·F-002를 같은 Phase에 묶는다.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-002 훅 × `check_close_gate` | CLOSE 진입 게이트의 `owner=user` 요건(`state_tool.py:717-722`) — 훅이 CLOSE 직전 사용자 확인 행을 `owner=auto`로 마킹하면 캡틴 승인 없이 CLOSE 진입 가능 | **P0** (하네스 Guards 무력화) | L1(판정 함수 단위) + L2(실 파일 subprocess 전이) | S-후보: agentic 파이프라인에서 EXECUTE 사용자 확인 행을 pending으로 둔 채 CLOSE 첫 행 mark → `stage_transition_violation` 또는 `close_gate_violation`으로 차단되고 자동 승인이 **일어나지 않음**을 state.json 실측 |
| H-2 | F-002 훅 × 워커 스코프 | `worker_scope_violation` 게이트(`state_tool.py:1499-1509`) — 훅이 워커 경로에서 앞 단계 행을 자동 갱신하면 워커가 자기 단계 밖 행을 실질 변경 | **P0** (권한 경계 우회) | L1 + L2(`--as-worker --worker-stage` subprocess) | S-후보: `--as-worker --worker-stage EXECUTE`로 EXECUTE 행 mark 시 앞 단계 PLAN 사용자 확인 행이 pending 그대로 유지되고 `stage_transition_violation`이 나는지 확인 |
| H-3 | F-003 판정 함수 통합 | 모드×단계 자동 승인 경계(ANALYSIS §A.2) — 통합 과정에서 `cmd_mark` 사전검사 또는 `cmd_validate` 사후검사의 판정 결과가 이동 | P1 (오차단/오통과) | L1(경계 불변 회귀표 전 셀 파라미터화) | S-후보: §3.3.2 경계 불변 회귀표 9셀 + CLOSE 3셀을 표 그대로 테이블 드리븐 테스트로 실행 |
| H-4 | F-003 × `cmd_validate` | validate가 CLOSE stage의 `done/auto` 사용자 확인 행에 대해 **현재 위반을 내지 않는다**(`state_tool.py:1710-1732`에 CLOSE 축 부재) — 판정 함수를 무분별 적용하면 신규 위반이 생겨 기존 state.json이 validate 실패 | P1 (in-flight 파일 오탐) | L1 + L2(092 `na` 보유 파일 실측) | S-후보: CLOSE 사용자 확인 행이 `done/auto`인 state.json으로 validate → violations_count 0 유지 |
| H-5 | F-001 auto-na 제거 | 3개 빌더의 init 결과 계약(`state_tool.py:824-829`, `:916-921`, `:1050-1055`) — 3모드 행 단위 동형성 | P1 | L1(3모드 init diff) | S-후보: 동일 `--rows-from` 스펙을 interactive/semi-agentic/agentic로 init → rows[] 전 필드 diff 0 |
| H-6 | F-001/F-002 × 기존 `na` 보유 파일 | `_COMPLETE_STATUSES`(`:456`)·`build_todo_mirror` na 필터(`:481`) 하위호환 — 기존 `na` 행 보유 state.json의 advance/mark/validate | P1 (in-flight 태스크 중단) | L2(092 state.json 복사본 실호출) | S-후보: `tasks/092-*/state.json` 복사본에 advance/mark/validate 3종 실행 → exit 0, 위반 0 |
| H-7 | F-005 note 접두 멱등 | note 문자열 계약(`state_tool.py:1562-1567`) — 접두 중첩 제거 시 기존 단일 접두 케이스의 문자열이 바뀌면 STATE.md 렌더 회귀 | P2 | L1 | S-후보: 신규 auto-pass 1회 → `agentic auto-pass: X`, 동일 행 2회차 → 문자열 불변 + `ok:true` |
| H-8 | F-002 훅 × `_run_clarification_hook`·`check_gate_artifacts` 순서 | 가드 순차 실행 원칙(`state_tool.py:1531` 주석 "H-1 — save_state_json() 이전 검증 구간") — 훅이 state를 in-place mutate한 뒤 후속 가드가 실패하면 메모리상 오염 상태로 다른 검증에 잘못된 값 전달 | P1 | L1(훅 거부 경로에서 rows 미변경 확인) + L2(실패 후 파일 미저장 확인) | S-후보: 훅 통과 후 `check_gate_artifacts`가 `gate_artifact_missing`으로 실패하는 시나리오 → state.json 파일의 사용자 확인 행이 여전히 `pending`인지 확인 |
| H-9 | F-006 문서 정합 | pilot 10종 SKILL.md·하네스 2종의 `--auto-pass` PM 명시 호출 지시(ANALYSIS §A.6) — 문구를 고치다 CLOSE 첫 행 거부 지시(유지 대상)까지 건드리면 CLOSE 절차 서술이 붕괴 | P2 | L1(문자열 grep 전후 대조) | S-후보: A.6 "CLOSE 첫 행 거부 지시" 목록 25개 지점의 문자열이 변경 전후 동일함을 grep으로 확인 |

---

## 2. 기능별 분석

### F-001: agentic auto-na 분기 제거 (교체형)

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/state-tool/state_tool.py` | `build_rows_from_spec`(`:785-832`) / `build_rows_from_skill_md`(`:834-924`) / `build_rows_from_pipeline_json`(`:1021-1058`) 3 빌더의 agentic 분기 | 수정 |
| 공통 | `opal/tools/state-tool/schema/state.schema.json` | `rows[].status` enum에 `na` 존치 (R-6 하위호환) | **변경 없음** |
| 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | auto-na 고정 테스트 2건 | 수정 |

#### 2.1.2 현재 구현

3개 빌더가 동일 패턴을 복붙 보유한다 — `if mode == "agentic" and <item명> == "사용자 확인" and <stage> != "CLOSE":` 조건에서 `status="na" / status_label="-" / owner="auto" / note="agentic auto-na at init"`를 덮어쓴다(`state_tool.py:824-829`, `:916-921`, `:1050-1055`). `timestamp`는 `None`으로 남아 자동 승인 이력이 기록되지 않는다(ANALYSIS §4 #1).

#### 2.1.3 영향 범위

- 읽기 측 `_COMPLETE_STATUSES`(`:456`)·`build_todo_mirror` na 필터(`:481`)는 **변경하지 않는다** — 기존 `na` 보유 파일 하위호환(R-6, ANALYSIS §A.4).
- 직접 깨지는 테스트 2건: `test_init_agentic_auto_na_user_confirmation`(`tests/test_state_tool.py:293-309`), `test_rows_from_agentic_auto_na`(`:2200-2221`).
- F-002 부재 시 `check_stage_transition_guard`가 agentic 파이프라인 전이를 전면 차단 → 동시 배포 필수.

---

### F-002: 자동 승인 훅 신설

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/state-tool/state_tool.py` | 신규 독립 함수 + `cmd_advance`(`:1409-1457`)·`cmd_mark`(`:1474-1660`) 가드 구간 배선 | 수정 |
| 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | 훅 동작·CLOSE 제외·워커 스코프 회귀 | 수정 |

#### 2.2.2 현재 구현

자동 승인은 PM의 명시 호출(`mark --auto-pass`, `state_tool.py:1562-1567`)로만 발생하며, 다음 단계 진입 시점의 훅은 존재하지 않는다. `cmd_advance`는 `check_stage_transition_guard` → `check_close_gate` → `_run_clarification_hook` 순으로 가드를 호출하고(`:1425-1437`), `cmd_mark`는 여기에 semi-agentic 사전검사(`:1525-1529`)와 `check_gate_artifacts`(`:1532`)를 더한다. 두 함수 모두 `_guard_scope = "prior_stage_only" if as_worker else "full"`을 이미 계산해 둔다(`:1427`, `:1513`).

#### 2.2.3 영향 범위

- `check_stage_transition_guard`의 판정 결과를 사전에 바꾸므로 **훅은 이 가드보다 먼저** 실행되어야 한다.
- `check_close_gate`(`:685-723`)의 `owner=user` 요건과 정면 충돌 가능 — H-1.
- 워커 권한 게이트(`:1499-1509`)와 충돌 가능 — H-2.
- `link_memory_history()`가 CLOSE 마지막 행 mark 시 발동하므로(ANALYSIS §3.2) CLOSE 경로 오발동은 히스토리 오염으로 번진다.

---

### F-003: 모드별 자동 승인 경계 단일 판정

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/state-tool/state_tool.py` | `MODE_BOUNDARY_STAGES`(`:50-54`) 정의 유지 + 신규 판정 함수 + 호출자 2곳 재배선(`:1525-1529`, `:1719-1732`) | 수정 |
| 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | 경계 불변 회귀표 테이블 드리븐 | 수정 |

#### 2.3.2 현재 구현

"자동 승인 가능 여부"가 3곳에 하드코딩되어 있다(ANALYSIS §4 #2):

1. `MODE_BOUNDARY_STAGES` 상수 정의(`:50-54`) — TASK/ANALYSIS/PLAN/TEST-SCENARIO/SPEC/REVIEW/DESIGN/WBS/WIREFRAME 9종.
2. `cmd_mark` semi-agentic 사전검사 — `if args.auto_pass and state.get("mode") == "semi-agentic": if row["stage"] in MODE_BOUNDARY_STAGES:` → `semi_agentic_pre_execute_auto_pass_denied`(`:1526-1529`).
3. `cmd_validate` 사후검사 — `owner == "auto" and mode == "interactive"` → `auto_pass_in_interactive_mode`; `owner == "auto" and mode == "semi-agentic" and stage in MODE_BOUNDARY_STAGES` → `semi_agentic_pre_execute_auto_pass_denied`(`:1719-1732`).

`check_close_gate`(`:685-723`)는 `MODE_BOUNDARY_STAGES`를 전혀 참조하지 않는 **모드 독립 상수 규칙**이며(ANALYSIS §4 #2 실측), F-003 판정 함수의 별개 축이다.

#### 2.3.3 영향 범위

- `cmd_mark` 사전검사는 **interactive에서 현재 아무것도 막지 않는다**(`cmd_mark` 전체에 `mode == "interactive"` 분기 부재 — ANALYSIS §4 #3). 판정 함수를 그대로 에러 조건으로 쓰면 interactive mark가 신규 차단되어 경계가 바뀐다.
- `cmd_validate`는 CLOSE 축을 갖지 않는다. 판정 함수를 그대로 쓰면 CLOSE stage의 `done/auto` 행에 신규 위반이 생긴다 — H-4.

---

### F-004: 승인 필요 구간 전용 에러

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/state-tool/state_tool.py` | `ERROR_CODES`(`:81-133`) 1종 추가 + F-002 훅 내부 호출 | 수정 |
| 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | 에러 코드·페이로드 필드 검증 | 수정 |

#### 2.4.2 현재 구현

`ERROR_CODES`는 단일 SSOT 딕셔너리(`:81-133`, 현재 44종)이고 `err()` 헬퍼(`:155-159`)가 이를 참조해 표준 JSON 에러 + `sys.exit`를 방출한다. 자동 승인 불가를 알리는 전용 코드는 없다 — 현재는 `stage_transition_violation`(`:111`)이 "앞 행이 미완"이라고만 알려 PM이 무슨 조치를 해야 하는지 알 수 없다.

#### 2.4.3 영향 범위

- 신규 코드 추가는 계약 확장(하위호환) — 기존 코드 문자열 변경 없음(ANALYSIS §3.3).
- DEC-A에 따라 이 에러는 **F-002 훅 경로에서만** 방출되며, PM이 직접 호출하는 `mark --auto-pass` 경로의 기존 에러(`semi_agentic_pre_execute_auto_pass_denied`·`auto_pass_in_interactive_mode`)는 그대로 유지한다.

---

### F-005: mark 멱등성

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/state-tool/state_tool.py` | `cmd_mark` owner 결정 구간(`:1561-1575`) | 수정 |
| 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | 2회 호출 멱등 회귀 | 수정 |

#### 2.5.2 현재 구현

```
if args.auto_pass:
    row["owner"] = "auto"
    if note_text:
        row["note"] = f"agentic auto-pass: {note_text}"
    else:
        row["note"] = "agentic auto-pass"
```
(`state_tool.py:1562-1567`) — 재호출 시 `note_text`가 이미 `agentic auto-pass: …`인지 검사하지 않아 접두가 중첩된다. 실측 증거: `tasks/092-260815-opd-워크트리-작업공간-분리/state.json:71, 116, 163` 3건(ANALYSIS §4 #5).

#### 2.5.3 영향 범위

- `note` 문자열만 변경 — STATE.md 렌더(`sync_state_md`)가 그대로 소비하므로 렌더 로직 무변경.
- "이미 done인 행에 대한 재-auto-pass no-op"은 `save_state_json` 호출 자체를 건너뛰므로 `updated_at`·`timestamp` 갱신도 발생하지 않는다.

---

### F-006: 하위호환 + 문서 정합

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서(하네스) | `opal/core/references/opal-harness-agentic.md` | agentic `--auto-pass` PM 명시 호출 지시 SSOT (`:70`, `:81-86`) | 수정 |
| 문서(하네스) | `opal/core/references/opal-harness-semi-agentic.md` | semi-agentic 동일 패턴 (`:44`, `:54-55`) | 수정 |
| 문서(pilot) | `opal/skills/opal-pilot-dev/SKILL.md`(`:322`) 외 8종 | 단계별 사용자 확인 행 `--auto-pass` 지시 | 수정 |
| 문서(pilot) | `opal/skills/opal-pilot-project-dev/SKILL.md`(`:158`) | "조건부 행 자동 `na` 처리는 미구현… `na`는 현재 init 시점 agentic 사용자 확인 행에만 부여된다" 서술 | 수정 |
| 공통 | `opal/tools/state-tool/schema/state.schema.json`(`:69`) | status enum `na` 존치 확인 | **변경 없음** |
| 문서 | `docs/CONVENTIONS.md` §State 관리 | 신규 자동 승인 계약 1줄 등재 | 수정 |

#### 2.6.2 현재 구현

ANALYSIS §A.6이 두 부류를 분리 전수했다 — (a) **일반 단계 자동 통과 지시** 11지점(하네스 2종 4지점 + pilot 7종 7지점 + project-dev 1지점): F-002 훅으로 대체되어야 할 문구. (b) **CLOSE 첫 행 거부 지시** 약 25지점: R-3 "CLOSE 직전은 전 모드 불가"로 **그대로 유지**.

#### 2.6.3 영향 범위

- (b) 목록을 건드리면 CLOSE 절차 서술이 붕괴 — H-9.
- `.opal/AGENT.md` [MUST]에 따라 하네스 변경은 SSOT 문서에서만 수행하고 pilot SKILL.md는 SSOT를 가리키는 문구로 정리한다.

---

## 2.7 설계 결정 (DEC) — PM 결정 + PLAN 종결 쟁점

| DEC | 결정 | 근거 |
|-----|------|------|
| **DEC-A** | **경로 분리** — F-002 신설 훅 경로에서 interactive는 자동 마킹하지 않고 F-004 전용 에러(`user_confirmation_required`)를 반환한다. PM이 직접 호출하는 기존 `mark --auto-pass` 경로는 **현행 유지**(mark는 통과, 사후 `validate`가 `auto_pass_in_interactive_mode` 위반 표시). | PM 결정. TASK.md F-3 AC "모드×단계 조합에 대한 판정 결과가 변경 전과 동일함을 테스트로 확인한다(경계 불변)"와 R-4를 동시 충족. 현행 실측: `cmd_mark`(`state_tool.py:1474-1660`)에 `mode == "interactive"` 분기 부재, `interactive` 문자열은 `:1709`·`:1719`(둘 다 `cmd_validate`)에만 존재 — ANALYSIS §4 #3 |
| **DEC-B** | **별도 독립 함수 신설** — ANALYSIS §A.3 권고안 (c)를 채택한다. 판정(F-003 `can_auto_approve_user_confirmation`)과 집행(F-002 `auto_approve_prior_user_confirmations`)의 책임을 분리하고, `cmd_advance`/`cmd_mark` 양쪽이 집행 함수를 호출한다. | PM 결정. (a)안은 순수 검증 함수 `check_stage_transition_guard`의 책임을 "검증기 → 검증+변경기"로 오염시킨다(ANALYSIS §A.3 (a) 부분 상태 변경 위험 칼럼). (b)안은 로직을 두 커맨드에 중복 구현한다 |
| **DEC-C** (쟁점 1) | **훅 스캔 범위 = "대상 행 앞의 모든 미완 사용자 확인 행" + "워커 경로에서는 훅 전면 비활성"** | §3.2.2 (2) 참조 |
| **DEC-D** (쟁점 2) | **대상 행의 stage가 CLOSE이면 훅 전체가 즉시 no-op 반환** — CLOSE 진입 경로에서는 어떤 행도 자동 승인되지 않는다 | §3.2.2 (3) 참조 |
| **DEC-E** (쟁점 3) | 판정 함수는 `(stage, mode) → (allowed, deny_reason)`로 두 축을 합성한다. 호출자는 **거부 사유별로 소비 범위를 달리한다** — `cmd_mark` 사전검사는 `semi_agentic_pre_execute`만, `cmd_validate`는 `interactive_requires_user`·`semi_agentic_pre_execute`만 소비하고 `close_requires_user`는 무시한다 | §3.3.2 참조 |
| **DEC-F** (쟁점 4) | 깨질 테스트 3건은 **전부 "수정"**(삭제 0건, 대체 0건)이며, F-1 AC(b) 신형 채택 검증 테스트를 **신규 2건 추가**한다 | §3.1.5 · §4.2 Step 7 참조 |
| **DEC-G** (쟁점 5) | 기존 `na` 보유 state.json 회귀는 **`tasks/092-*/state.json` 복사본**을 tmp에 만들어 advance/mark/validate 3종을 subprocess 실호출로 검증한다. 원본은 읽기만 한다 | §3.6.5 · §4.2 Step 9 참조 |

---

## 3. 기능별 설계

### F-001: agentic auto-na 분기 제거 (교체형)

#### 3.1.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 공통 | `build_rows_from_spec`의 agentic 분기 6줄 삭제 | `state_tool.py:824-829` |
| 2 | `opal/tools/state-tool/state_tool.py` | 공통 | `build_rows_from_skill_md`의 agentic 분기 6줄 삭제 | `state_tool.py:916-921` |
| 3 | `opal/tools/state-tool/state_tool.py` | 공통 | `build_rows_from_pipeline_json`의 agentic 분기 6줄 삭제 | `state_tool.py:1050-1055` |

#### 3.1.2 API·데이터 모델 설계

세 빌더 모두 아래 블록을 **완전 삭제**한다 (주석 라인 포함):

```python
# 삭제 대상 (state_tool.py:824-829 / :916-921 / :1050-1055 동일 패턴)
# agentic 자동 마킹 (§2.20.1 — CLOSE 사용자 확인 행 제외)
if mode == "agentic" and name == "사용자 확인" and stage != "CLOSE":
    row["status"]       = "na"
    row["status_label"] = "-"
    row["owner"]        = "auto"
    row["note"]         = "agentic auto-na at init"
```

삭제 후 세 빌더의 사용자 확인 행은 각 빌더의 기본 행 딕셔너리를 그대로 사용한다 — `status="pending" / status_label="⬜" / timestamp=None / owner="PM" / note=None`(`state_tool.py:811-820`, `:906-915`, `:1034-1044`). 이것이 R-1 "전 모드 `pending / owner=PM`"의 구현이다.

> [MUST] `mode` 파라미터는 세 빌더의 시그니처에서 **제거하지 않는다** — `build_rows_from_spec(rows_spec, command, mode)` 등 호출부 계약을 유지해 Surgical Changes 원칙(`~/.opal/PRINCIPLES.md` §3 "Touch only what the plan names")을 지킨다. 미사용 인자가 되지만 시그니처 변경은 이번 요구사항 밖이다.

**데이터 모델(변경 없음)**: `state.schema.json:69`의 `rows[].status` enum `["pending", "in_progress", "done", "failed", "na"]`은 그대로 둔다 — R-6 하위호환. `na`를 제거하면 기존 `na` 보유 state.json이 스키마 검증에서 걸린다(ANALYSIS §A.4).

#### 3.1.3 환경 변경

해당 없음.

#### 3.1.4 배치/마이그레이션

해당 없음 — 기존 state.json 파일을 소급 변환하지 **않는다**. 읽기 경로(`_COMPLETE_STATUSES`, `build_todo_mirror`)가 `na`를 계속 인정하므로 in-flight 파일은 그대로 완주한다(R-6).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑) — 깨질 테스트 처리 방침 포함

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-1 AC(a) 구형 잔존 0 | 산출물 검사 | `state_tool.py`에서 `agentic auto-na at init` 문자열 grep 0건 |
| TS-002 | F-1 AC(a) | 회귀 테스트(수정) | `test_init_agentic_auto_na_user_confirmation`(`tests/test_state_tool.py:293-309`) → **수정**. 이름을 `test_init_agentic_user_confirmation_pending`으로 바꾸고 assert를 `status == "pending"` / `status_label == "⬜"` / `owner == "PM"`로 교체. CLOSE 사용자 확인 행 `pending` 유지 assert(`:308-309`)는 **그대로 보존**한다 |
| TS-003 | F-1 AC(a) | 회귀 테스트(수정) | `test_rows_from_agentic_auto_na`(`:2200-2221`) → **수정**. 이름을 `test_rows_from_agentic_user_confirmation_pending`으로 바꾸고 `:2219` assert를 `pending`으로 교체 |
| TS-004 | F-1 AC(b) 신형 채택 — 3모드 diff 0 | 기능 테스트(신규) | 동일 `--rows-from` pipeline.json 스펙을 interactive / semi-agentic / agentic 3모드로 init → `rows[]` 전 필드가 3모드 간 완전 일치(diff 0). **이 테스트가 F-1 AC(b)의 유일한 직접 검증이다** |
| TS-005 | F-1 AC(b) 신형 채택 — pending 초기화 + 훅 승인 결합 | 통합 테스트(신규) | agentic init 직후 사용자 확인 행이 `pending/PM/timestamp=None`이고, 이후 F-002 훅 발동으로 `done/auto/timestamp≠None`이 됨을 한 시나리오에서 연속 검증 (TS-011과 페어) |
| TS-006 | F-1 (주석 정합) | 산출물 검사 | `tests/test_state_tool.py:1251` 등 "agentic 모드에서 TASK 사용자 확인 행은 auto-na로 초기화됨" 주석을 사실에 맞게 갱신 (ANALYSIS §A.5 대조군 권고) |

> **깨질 테스트 3건 처리 방침 (DEC-F)**: 3건 모두 **수정**이며 삭제하지 않는다. ①`test_init_agentic_auto_na_user_confirmation` → TS-002로 수정. ②`test_rows_from_agentic_auto_na` → TS-003으로 수정. ③`test_close_gate_regression_via_task_step_addressing_subprocess` → TS-014로 수정(§3.2.5). **삭제만 하고 신형 검증을 추가하지 않으면 F-1 AC(b)가 성립하지 않으므로**, TS-004(3모드 diff 0)·TS-005(pending 초기화 + 훅 승인)를 신규로 추가해 신형 계약을 명시 검증한다.

---

### F-002: 자동 승인 훅 신설

#### 3.2.1 파일 변경 계획

**신규 생성**: 없음 (신규 파일 없음 — 기존 단일 파일 도구에 함수 추가)

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 공통 | 신규 함수 `auto_approve_prior_user_confirmations()` 추가 — `check_stage_transition_guard` 직후(`:679` 이후)에 배치 | ANALYSIS §A.3 권고 (c) / DEC-B |
| 2 | `opal/tools/state-tool/state_tool.py` | 공통 | `cmd_advance` 가드 구간에 훅 호출 삽입 — `check_stage_transition_guard`(`:1428`) **직전** | `state_tool.py:1425-1432` |
| 3 | `opal/tools/state-tool/state_tool.py` | 공통 | `cmd_mark` 가드 구간에 훅 호출 삽입 — `check_stage_transition_guard`(`:1514`) **직전** | `state_tool.py:1511-1519` |

#### 3.2.2 API 설계

##### (1) 함수 시그니처

```python
def auto_approve_prior_user_confirmations(
    state, row_index, command, *,
    as_worker=False, force=False, now_str=None,
):
    """R-2 조항 2 집행 — 대상 행 진입 시 앞의 미완 '사용자 확인' 행을 자동 승인한다.

    반환: 자동 승인한 row_id 리스트 (list[int]). 승인 대상이 없으면 [].
    부작용: state["rows"][i]를 in-place 갱신 (호출자가 save_state_json 책임).
    거부: 자동 승인 불가 구간이면 err(command, "user_confirmation_required", ...) 후 exit 1.
    """
```

> [MUST] 이 함수는 `save_state_json`을 호출하지 않는다 — `state_tool.py:1531` 주석 "H-1 — save_state_json() 이전 검증 구간"이 확립한 패턴(가드 전량 통과 후 1회 저장)을 유지해, 후속 가드 실패 시 파일이 오염되지 않는다(H-8).

##### (2) 스캔 범위 — 설계 쟁점 1 종결 (DEC-C)

**결론: "대상 행(row_index) 앞의 모든 미완 사용자 확인 행"을 대상으로 하되, 워커 경로(`as_worker=True`)에서는 훅을 전면 비활성화한다.**

```python
if as_worker:
    return []          # 워커 경로 — 자동 승인 없음 (DEC-C)
if force:
    return []          # --force 우회 경로 — 가드 자체가 스킵되므로 훅도 no-op
```

근거:

1. **`worker_scope_violation` 게이트 불변 보장** — `cmd_mark`의 워커 권한 게이트는 "워커가 자기 단계(`worker_stage`) 외 행을 갱신"하는 것을 차단한다(`state_tool.py:1499-1509`). 훅이 워커 경로에서 앞 단계 사용자 확인 행을 자동 승인하면 **주소를 지정하지 않고 같은 결과를 얻는 우회 경로**가 된다. ANALYSIS §5가 이를 심각도 "높음"으로 지목했다. 훅을 워커 경로에서 끄면 이 우회가 **구조적으로 불가능**하다.
2. **기존 동작 완전 보존** — 워커 경로에서 앞 단계 사용자 확인 행이 미완이면 `check_stage_transition_guard(scope="prior_stage_only")`가 지금과 동일하게 `stage_transition_violation`을 낸다(`:658-678`). 즉 워커 경로는 회귀 0이다.
3. **책임 정합** — 단계 전이의 주체는 PM이다. 앞 단계 사용자 확인 행의 승인은 PM이 다음 단계 첫 행을 `advance`/`mark`할 때 일어나야 하며, 워커가 자기 작업 행을 마킹할 때 일어날 일이 아니다.

"직전 1단계만" 대신 "앞의 모든 미완 행"을 택한 이유: PM 경로에서 훅이 커버하는 범위가 `check_stage_transition_guard(scope="full")`가 검사하는 범위(`[0, row_index)`, `:667`)와 **정확히 일치**해야 "훅이 통과시킨 뒤 가드가 막는" 모순이 생기지 않기 때문이다. 조건부 단계 스킵(예: `conditional` 행)으로 2단계 이상 앞의 행이 미완으로 남을 수 있어, "직전 1단계"로 좁히면 그 케이스에서 훅이 무력해진다. 워커 우회 리스크는 위 (1)로 이미 차단되었으므로 범위를 넓혀도 안전하다.

##### (3) CLOSE 제외 — 설계 쟁점 2 종결 (DEC-D)

**결론: 대상 행의 stage가 `CLOSE`이면 훅 전체가 즉시 `[]`를 반환한다(no-op).**

```python
target_row = state["rows"][row_index]
if target_row["stage"] == "CLOSE":
    return []          # [MUST] CLOSE 진입 경로에서는 어떤 행도 자동 승인하지 않는다 (DEC-D)
```

이것이 3중 방어의 1차이자 결정적 방어다. 필터를 "CLOSE 사용자 확인 행을 후보에서 제외"로 두는 것만으로는 **부족하다** — `check_close_gate`가 검사하는 것은 "CLOSE 첫 행의 **직전 사용자 확인 행**"(`state_tool.py:706-722`)이고 그 행의 stage는 보통 TEST/EXECUTE 등 CLOSE가 아니기 때문이다. 훅이 그 행을 `owner=auto`로 마킹하면 `:717`의 `owner != "user"` 검사가 통과해 게이트가 무력화된다(H-1).

3중 방어:

| 층 | 내용 | 위치 |
|----|------|------|
| 1차 (결정적) | 대상 행 stage == `CLOSE` → 훅 전체 no-op | `auto_approve_prior_user_confirmations` 초입 |
| 2차 | 후보 행 stage == `CLOSE` → 후보 집합에서 제외 | 후보 수집 루프 |
| 3차 | 판정 함수가 stage == `CLOSE`에 대해 무조건 `(False, "close_requires_user")` | `can_auto_approve_user_confirmation` (§3.3.2) |

> [MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자의 확인된 지시(`승인`, `확인`, `확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가." — 1차 방어는 이 Guard의 코드상 대응물이며, TASK.md R-3 "CLOSE 직전은 전 모드 불가"와 일치한다.

**부수 효과(의도됨)**: CLOSE 직전 단계의 사용자 확인 행은 자동 승인되지 않으므로, PM은 CLOSE 진입 전 반드시 보고 → 캡틴 발화 → `mark --owner user`를 수행해야 한다. 이는 `check_close_gate:717`가 이미 요구하는 것과 동일하며, F-004 전용 에러가 그 조치를 명시적으로 안내한다.

##### (4) 후보 수집 및 집행 로직

```python
approved = []
for i in range(row_index):                       # [0, row_index) — full scope와 동일 범위
    prev = state["rows"][i]
    if prev.get("item") != "사용자 확인":
        continue
    if prev.get("status") in _COMPLETE_STATUSES:  # done / additional_work_done / na
        continue                                  # 멱등 — 기존 na 행도 재승인하지 않는다 (R-6)
    if prev["stage"] == "CLOSE":
        continue                                  # 2차 방어

    allowed, deny_reason = can_auto_approve_user_confirmation(
        prev["stage"], state.get("mode", "interactive"))
    if not allowed:
        err(command, "user_confirmation_required",           # F-004
            row_id=prev["row_id"], stage=prev["stage"],
            key=prev.get("key"), item=prev["item"],
            mode=state.get("mode"), reason=deny_reason,
            required_action=(
                f"보고 → 캡틴 승인 → state mark <task-path> "
                f"--task-step {prev.get('key') or prev['row_id']} --done --owner user"
            ))

    prev["status"]       = "done"
    prev["status_label"] = "✅"
    prev["owner"]        = "auto"
    prev["timestamp"]    = now_str
    prev["note"]         = f"auto-approved on {target_row['stage']} entry"
    approved.append(prev["row_id"])
return approved
```

> [MUST] `state_tool.py:456`: `_COMPLETE_STATUSES = {"done", "additional_work_done", "na"}` — 훅은 이 상수를 재사용해 완료 판정한다. 별도 판정을 만들면 `na` 하위호환(R-6)이 깨진다.
> [MUST] note 문구는 `agentic auto-pass:` 접두를 쓰지 **않는다** — F-005 멱등 접두 로직(`state_tool.py:1562-1567`)과 문자열 공간을 분리해, 훅 승인분과 PM 명시 호출분을 사후에 구분할 수 있게 한다.

`now_str`은 호출자가 `get_kst_datetime(command)`로 취득해 전달한다 — 훅 내부에서 별도 호출하면 같은 커맨드 안에서 timestamp가 갈린다.

##### (5) 호출 배선 및 순서

`cmd_advance`(`state_tool.py:1425-1437`):

```python
_guard_scope = "prior_stage_only" if getattr(args, "as_worker", False) else "full"
_now = get_kst_datetime(command)                                    # 기존 :1439에서 앞당김
auto_approved = auto_approve_prior_user_confirmations(              # ← 신규
    state, row_index, command,
    as_worker=getattr(args, "as_worker", False),
    force=getattr(args, "force", False), now_str=_now)
check_stage_transition_guard(state, row_index, command, force=False, scope=_guard_scope)
check_close_gate(state, row_index, command)
_run_clarification_hook(...)
```

`cmd_mark`(`state_tool.py:1511-1532`)도 동일 위치(`check_stage_transition_guard` 직전)에 삽입하되 `force=args.force`를 전달한다.

**순서 근거**:
- 훅은 `check_stage_transition_guard`보다 **먼저** 실행되어야 한다 — 그래야 자동 승인된 행이 완료로 집계되어 가드가 통과한다.
- 훅은 `check_close_gate`보다 먼저 실행되지만, DEC-D 1차 방어로 CLOSE 경로에서 **아무것도 mutate하지 않으므로** `check_close_gate`는 언제나 훅 미접촉 상태를 본다. 이것이 "훅이 in-place mutate 후 다른 검증에 잘못된 값을 넘길 위험"(ANALYSIS §A.3 (a) 칼럼)의 해소책이다.
- 훅 이후 어떤 가드가 실패해도 `err()`가 `sys.exit`하고 `save_state_json`은 호출되지 않으므로 파일은 오염되지 않는다(H-8). 메모리상 mutate는 프로세스 종료로 소멸한다.

##### (6) 성공 응답 확장

`cmd_advance`/`cmd_mark`의 `ok(...)` 호출에 `auto_approved=auto_approved` 필드를 추가한다(`state_tool.py:1455-1457`, `:1604` 부근). 자동 승인이 없었으면 빈 리스트다. PM이 어떤 행이 훅으로 승인됐는지 즉시 알 수 있게 하는 관측 필드이며, 기존 필드는 변경하지 않는다(하위호환).

#### 3.2.3 환경 변경

해당 없음 — 표준 라이브러리만 사용(`state_tool.py:6` 헤더 "외부 의존 없음").

#### 3.2.4 배치/마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | F-2 AC | 통합 테스트(신규) | agentic 모드에서 ANALYSIS 사용자 확인 행을 `pending`으로 둔 채 PLAN 첫 행을 `advance` → `--auto-pass` 없이 해당 행이 `done / owner=auto / timestamp≠None`이 되고 advance가 exit 0 |
| TS-012 | H-1 / DEC-D | 보안·회귀 테스트(신규) | agentic 파이프라인에서 EXECUTE 사용자 확인 행을 `pending`으로 둔 채 CLOSE 첫 행 mark → 자동 승인이 **일어나지 않고** `stage_transition_violation`으로 exit 1. state.json 재로드 시 해당 행이 여전히 `pending` |
| TS-013 | H-2 / DEC-C | 보안·회귀 테스트(신규) | `--as-worker --worker-stage EXECUTE`로 EXECUTE 행 mark 시 앞 단계 PLAN 사용자 확인 행이 `pending` 유지 + `stage_transition_violation` exit 1 (워커 우회 불가) |
| TS-014 | F-2 AC / DEC-F ③ | 회귀 테스트(수정) | `test_close_gate_regression_via_task_step_addressing_subprocess`(`tests/test_state_tool.py:4806-4844`) → **수정**. ①주석(`:4827-4828`)을 "row 2·5는 F-2 훅이 자동 승인, row 8(execute.user_confirm)은 CLOSE 직전이라 캡틴 승인 필수"로 갱신 ②사전 mark 루프 `(1,3,4,6,7)` 유지 ③row 8을 `--done --owner user`로 mark하는 단계 추가 ④최종 assert(`agentic_close_gate_requires_user`, `:4843`)는 **불변** — `check_close_gate:700-701`이 owner 검사보다 앞서 `auto_pass and mode in (agentic, semi-agentic)`만으로 거부하므로 row 8 승인 여부와 무관하게 성립 |
| TS-015 | H-8 | 회귀 테스트(신규) | 훅 통과 후 `check_gate_artifacts`가 `gate_artifact_missing`으로 실패하는 시나리오 → 저장된 state.json의 사용자 확인 행이 여전히 `pending`(파일 미오염) |
| TS-016 | F-2 관측 | 기능 테스트(신규) | advance/mark 성공 응답 stdout JSON에 `auto_approved` 배열 필드가 존재하고, 승인된 row_id를 담는다 |

---

### F-003: 모드별 자동 승인 경계 단일 판정

#### 3.3.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 공통 | 신규 판정 함수 `can_auto_approve_user_confirmation()` 추가 — `MODE_BOUNDARY_STAGES` 정의(`:50-54`) 직후에 배치 | ANALYSIS §4 #2 |
| 2 | `opal/tools/state-tool/state_tool.py` | 공통 | `cmd_mark` semi-agentic 사전검사(`:1525-1529`)를 판정 함수 호출로 재배선 | `state_tool.py:1525-1529` |
| 3 | `opal/tools/state-tool/state_tool.py` | 공통 | `cmd_validate` 사후검사(`:1719-1732`)를 판정 함수 호출로 재배선 | `state_tool.py:1719-1732` |

#### 3.3.2 API 설계 — 두 축 합성 (설계 쟁점 3 종결, DEC-E)

##### (1) 함수 시그니처

```python
def can_auto_approve_user_confirmation(stage, mode):
    """R-3 — '이 사용자 확인 행을 자동 승인해도 되는가' 단일 판정.

    반환: (allowed: bool, deny_reason: str | None)
      deny_reason ∈ {"close_requires_user", "interactive_requires_user", "semi_agentic_pre_execute"}

    두 축 합성:
      축1 CLOSE 여부          — 모드 무관 무조건 거부 (check_close_gate와 동일 규범, 별개 상수 규칙)
      축2 모드별 경계          — interactive 전 stage 거부 / semi-agentic은 MODE_BOUNDARY_STAGES 한정 거부
    두 축은 상호 배타다 — "CLOSE" is not in MODE_BOUNDARY_STAGES (state_tool.py:50-54).
    """
    if stage == "CLOSE":
        return (False, "close_requires_user")            # 축1 — 최우선
    if mode == "interactive":
        return (False, "interactive_requires_user")      # 축2-a — stage 무관
    if mode == "semi-agentic" and stage in MODE_BOUNDARY_STAGES:
        return (False, "semi_agentic_pre_execute")       # 축2-b — stage 한정
    return (True, None)                                  # agentic 전 구간 / semi-agentic 경계 밖
```

**축 순서 근거**: CLOSE는 `MODE_BOUNDARY_STAGES`에 원래 없으므로(`state_tool.py:50-54`) 축1과 축2-b는 교차하지 않는다(ANALYSIS §4 #2). 축2-a(interactive)를 축2-b보다 먼저 두는 것은 interactive가 stage와 무관하게 전 구간 거부이기 때문이며, 순서를 바꿔도 `allowed` 값은 동일하고 `deny_reason` 라벨만 달라진다 — interactive + `MODE_BOUNDARY_STAGES` 조합에서 어느 사유가 나오는지를 확정하기 위해 순서를 고정한다.

> [MUST] `state_tool.py:50-54`: `MODE_BOUNDARY_STAGES = {"TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO", "SPEC", "REVIEW", "DESIGN", "WBS", "WIREFRAME"}` — 이 상수는 **삭제하지 않고 정의 위치도 옮기지 않는다**. 판정 함수가 이 상수의 유일한 참조자가 된다.

##### (2) 호출자 재배선 — 사유별 소비 범위 (경계 불변의 핵심)

| 호출자 | 소비하는 deny_reason | 무시하는 deny_reason | 무시 근거 |
|--------|---------------------|---------------------|----------|
| `cmd_mark` 사전검사 (`:1525-1529`) | `semi_agentic_pre_execute` → `semi_agentic_pre_execute_auto_pass_denied` | `interactive_requires_user`(DEC-A — 기존 미차단 유지), `close_requires_user`(앞선 `check_close_gate`가 이미 처리) | DEC-A / `check_close_gate` 호출이 `:1518`로 선행 |
| `cmd_validate` 사후검사 (`:1719-1732`) | `interactive_requires_user` → `auto_pass_in_interactive_mode`, `semi_agentic_pre_execute` → `semi_agentic_pre_execute_auto_pass_denied` | `close_requires_user` | **H-4** — 현행 validate는 CLOSE stage의 `done/auto` 사용자 확인 행에 위반을 내지 않는다(`:1710-1732`에 CLOSE 축 부재). 소비하면 기존 state.json에 신규 오탐이 발생한다 |
| `auto_approve_prior_user_confirmations` (신규, F-002) | 세 사유 전부 → `user_confirmation_required`(F-004) | 없음 | 신규 경로 — 기존 동작 불변(DEC-A) |

`cmd_mark` 재배선 후 코드:

```python
# semi-agentic 모드에서 EXECUTE-equivalent 이전 행은 --auto-pass 거부 (D-DEC-5, F-003 단일 판정 소비)
if args.auto_pass:
    _allowed, _deny = can_auto_approve_user_confirmation(row["stage"], state.get("mode"))
    if not _allowed and _deny == "semi_agentic_pre_execute":   # [MUST] 이 사유만 소비 (DEC-E)
        err(command, "semi_agentic_pre_execute_auto_pass_denied",
            row_id=row["row_id"], stage=row["stage"])
```

`cmd_validate` 재배선 후 코드:

```python
if owner == "auto":
    _allowed, _deny = can_auto_approve_user_confirmation(row.get("stage"), mode)
    if not _allowed and _deny == "interactive_requires_user":
        violations.append({"code": "auto_pass_in_interactive_mode",
                           "row_id": row["row_id"], "detail": "interactive mode but owner=auto"})
    if not _allowed and _deny == "semi_agentic_pre_execute":
        violations.append({"code": "semi_agentic_pre_execute_auto_pass_denied",
                           "row_id": row["row_id"],
                           "detail": f"semi-agentic mode but owner=auto on stage={row.get('stage')}"})
    # [MUST] close_requires_user는 소비하지 않는다 — 현행 경계 보존 (H-4)
```

`user_confirmation_owner_mismatch` 검사(`:1711-1718`)는 판정 함수와 무관하므로 **그대로 둔다**.

##### (3) 경계 불변 회귀표 (ANALYSIS §A.2 승격)

F-3 AC "모드×단계 조합에 대한 판정 결과가 변경 전과 동일함"의 검증 기준표다. **변경 전후 각 셀의 값이 동일해야 한다.**

**표 A — `mark --auto-pass` 즉시 차단 여부 (cmd_mark 경로, 사용자 확인 행 대상)**

| # | stage 분류 | mode | 변경 전 | 변경 후 (필수) | 근거 |
|---|-----------|------|---------|---------------|------|
| B-1 | `MODE_BOUNDARY_STAGES` | interactive | 차단 없음 (exit 0, `done/auto` 저장) | **동일** | `cmd_mark`에 interactive 분기 부재(ANALYSIS §4 #3) / DEC-A |
| B-2 | `MODE_BOUNDARY_STAGES` | semi-agentic | `semi_agentic_pre_execute_auto_pass_denied` exit 1 | **동일** | `state_tool.py:1526-1529` |
| B-3 | `MODE_BOUNDARY_STAGES` | agentic | 차단 없음 (exit 0) | **동일** | 해당 분기가 semi-agentic 한정 |
| B-4 | 그 외 일반 stage (EXECUTE/TEST/QA 등) | interactive | 차단 없음 | **동일** | 동상 |
| B-5 | 그 외 일반 stage | semi-agentic | 차단 없음 | **동일** | `MODE_BOUNDARY_STAGES` 밖 |
| B-6 | 그 외 일반 stage | agentic | 차단 없음 | **동일** | 동상 |
| B-7 | `CLOSE` 첫 행 | interactive | `agentic_close_gate_requires_user` **아님** → owner=user 미충족 시 `close_gate_violation` | **동일** | `state_tool.py:700`의 모드 조건이 `(agentic, semi-agentic)`만 검사 — interactive는 걸리지 않고 `:717`에서 거부 (ANALYSIS §A.2 주의) |
| B-8 | `CLOSE` 첫 행 | semi-agentic | `agentic_close_gate_requires_user` exit 1 | **동일** | `state_tool.py:700-701` |
| B-9 | `CLOSE` 첫 행 | agentic | `agentic_close_gate_requires_user` exit 1 | **동일** | `state_tool.py:700-701` |

> **B-7의 에러 코드 차이는 경계 불변 판정에 포함된다** — interactive+CLOSE는 `close_gate_violation`, agentic/semi-agentic+CLOSE는 `agentic_close_gate_requires_user`로 **서로 다른 코드**가 나온다. F-003 통합 후에도 이 차이가 유지되어야 한다(ANALYSIS §A.2 주의 문단). 회귀 테스트는 exit code만이 아니라 `error` 필드 문자열까지 대조한다.

**표 B — `validate` 사후 위반 방출 여부 (사용자 확인 행 `status=done, owner=auto` 기준)**

| # | stage 분류 | mode | 변경 전 | 변경 후 (필수) | 근거 |
|---|-----------|------|---------|---------------|------|
| V-1 | `MODE_BOUNDARY_STAGES` | interactive | `auto_pass_in_interactive_mode` | **동일** | `state_tool.py:1719-1724` |
| V-2 | `MODE_BOUNDARY_STAGES` | semi-agentic | `semi_agentic_pre_execute_auto_pass_denied` | **동일** | `state_tool.py:1725-1732` |
| V-3 | `MODE_BOUNDARY_STAGES` | agentic | 위반 없음 | **동일** | 해당 조건 미해당 |
| V-4 | 그 외 일반 stage | interactive | `auto_pass_in_interactive_mode` | **동일** | `:1719` (stage 무관) |
| V-5 | 그 외 일반 stage | semi-agentic | 위반 없음 | **동일** | `MODE_BOUNDARY_STAGES` 밖 |
| V-6 | 그 외 일반 stage | agentic | 위반 없음 | **동일** | 동상 |
| V-7 | `CLOSE` | interactive | `auto_pass_in_interactive_mode` | **동일** | `:1719`는 stage 무관이므로 CLOSE도 방출 |
| V-8 | `CLOSE` | semi-agentic | **위반 없음** | **동일 (위반 없음)** | CLOSE ∉ `MODE_BOUNDARY_STAGES` — **H-4 핵심 셀**. 판정 함수의 `close_requires_user`를 소비하면 이 셀이 깨진다 |
| V-9 | `CLOSE` | agentic | **위반 없음** | **동일 (위반 없음)** | 동상 — **H-4 핵심 셀** |

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-021 | F-3 AC (경계 불변) | 회귀 테스트(신규, 테이블 드리븐) | §3.3.2 (3) 표 A의 9셀(B-1~B-9)을 `subTest` 파라미터화로 실행 → exit code + `error` 필드 문자열이 표와 일치 |
| TS-022 | F-3 AC (경계 불변) / H-4 | 회귀 테스트(신규, 테이블 드리븐) | §3.3.2 (3) 표 B의 9셀(V-1~V-9)을 파라미터화로 실행 → `violations[].code` 집합이 표와 일치. 특히 V-8·V-9는 `violations_count == 0` |
| TS-023 | F-3 AC (단일화) | 산출물 검사 | `MODE_BOUNDARY_STAGES` 참조 지점이 `can_auto_approve_user_confirmation` 내부 1곳뿐임을 grep으로 확인(정의부 `:50-54` 제외) |
| TS-024 | F-3 (판정 함수 단위) | 기능 테스트(신규) | `can_auto_approve_user_confirmation`에 (stage, mode) 3×3+CLOSE 조합 직접 호출 → `(allowed, deny_reason)` 튜플이 명세와 일치 |

---

### F-004: 승인 필요 구간 전용 에러

#### 3.4.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 공통 | `ERROR_CODES`에 `user_confirmation_required` 1종 추가 | `state_tool.py:81-133` |

#### 3.4.2 API 설계

`ERROR_CODES` 딕셔너리 말미(`state_tool.py:132` 다음)에 추가한다:

```python
    # 093 F-004 R-4: 자동 승인 불가 구간 — 캡틴 승인 필요 (PLAN §3.4.2)
    "user_confirmation_required":
        "자동 승인 불가 — 사용자 확인 행(row {row_id}, stage={stage})에 캡틴 승인이 필요합니다"
        " (사유: {reason}). 보고 → 캡틴 승인 → mark --done --owner user",
```

> [MUST] `state_tool.py:80` 주석: "모든 error 응답 값은 이 상수의 키를 참조한다. 추가/임의 변형 금지." — 신규 코드는 이 딕셔너리에만 등록하고 `err()` 헬퍼(`:155`)로만 방출한다.

**응답 페이로드 계약** (F-004 AC "응답에 `row_id`와 대상 단계가 포함된다"):

| 필드 | 값 | 필수 |
|------|-----|------|
| `error` | `"user_confirmation_required"` | O |
| `row_id` | 승인이 필요한 사용자 확인 행의 `row_id` (int) | O |
| `stage` | 그 행의 stage (str) | O |
| `key` | 그 행의 `--task-step` key (없으면 `null`) | O |
| `item` | `"사용자 확인"` | O |
| `mode` | 현재 파이프라인 모드 | O |
| `reason` | `close_requires_user` / `interactive_requires_user` / `semi_agentic_pre_execute` | O |
| `required_action` | PM이 실행할 명령 문자열 | O |
| exit code | 1 | O |

#### 3.4.3 환경 변경

해당 없음.

#### 3.4.4 배치/마이그레이션

해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-031 | F-4 AC | 기능 테스트(신규) | interactive 모드에서 사용자 확인 행을 `pending`으로 둔 채 다음 단계 첫 행 advance → exit 1, `error == "user_confirmation_required"`, 응답에 `row_id`·`stage`·`reason == "interactive_requires_user"`·`required_action` 포함 |
| TS-032 | F-4 AC / DEC-A | 회귀 테스트(신규) | 동일 interactive 파이프라인에서 PM이 직접 `mark --auto-pass` 호출 → **기존대로 exit 0**으로 통과하고, 이어지는 `validate`가 `auto_pass_in_interactive_mode` 위반 1건 방출 (경로 분리 확인) |
| TS-033 | F-4 AC | 기능 테스트(신규) | semi-agentic 모드 + `MODE_BOUNDARY_STAGES` 소속 사용자 확인 행 `pending` → 다음 단계 advance 시 `user_confirmation_required` + `reason == "semi_agentic_pre_execute"` |
| TS-034 | F-4 (에러 SSOT) | 산출물 검사 | `ERROR_CODES`에 `user_confirmation_required` 키가 존재하고, 기존 44종 키의 문자열이 변경되지 않음 |

---

### F-005: mark 멱등성

#### 3.5.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 공통 | `cmd_mark` auto_pass note 접두 중첩 제거 | `state_tool.py:1562-1567` |
| 2 | `opal/tools/state-tool/state_tool.py` | 공통 | 이미 `done/auto`인 행에 대한 재-auto-pass no-op 조기 반환 | `state_tool.py:1531-1534` 구간 |

#### 3.5.2 API 설계

##### (1) note 접두 중첩 제거

```python
_AUTO_PASS_PREFIX = "agentic auto-pass"          # 모듈 상수로 추출 (문자열 중복 제거)

if args.auto_pass:
    row["owner"] = "auto"
    if not note_text:
        row["note"] = _AUTO_PASS_PREFIX
    elif note_text.startswith(f"{_AUTO_PASS_PREFIX}:"):
        row["note"] = note_text                   # 이미 접두 보유 → 그대로 (중첩 방지)
    else:
        row["note"] = f"{_AUTO_PASS_PREFIX}: {note_text}"
```

> [MUST] 접두 문자열 `"agentic auto-pass"`는 **변경하지 않는다** — `tasks/092-*/state.json` 등 기존 파일과 하네스 문서가 이 문자열을 참조한다. 중첩만 제거한다.

##### (2) 재-auto-pass no-op

`check_gate_artifacts`(`:1532`) 통과 직후, `get_kst_datetime`(`:1534`) 호출 **이전**에 삽입한다:

```python
# R-5 멱등성 — 이미 auto 승인된 행에 대한 재-auto-pass는 상태 변경 없이 성공 반환
if (args.auto_pass and not args.force and not _step_str
        and row.get("status") == "done" and row.get("owner") == "auto"):
    ok(command, row_id=row["row_id"], stage=row["stage"], item=row["item"],
       status="done", timestamp=row.get("timestamp"), idempotent=True,
       todo_mirror=build_todo_mirror(state, "update"))
    return
```

조건을 좁게 잡은 근거(`~/.opal/PRINCIPLES.md` §2 Simplicity First — "Solve only the current requirement"):
- `not args.force` — `--force`는 명시적 우회 의도이므로 no-op으로 삼키지 않는다.
- `not _step_str` — `--step N/M` 진행률 갱신은 상태 변경이 목적이므로 제외한다(`state_tool.py:1536-1551`).
- `owner == "auto"` — `owner=user`로 승인된 행을 auto로 덮어쓰는 시도는 no-op이 아니라 기존대로 진행되어야 한다(CLOSE 게이트 요건 보호).

> 주의: `_step_str` 파싱(`state_tool.py:1539`)은 현재 `now_str` 취득 이후에 있다. no-op 검사가 `_step_str`을 참조하므로 **`_step_str` 산출 2줄(`:1539-1540`)을 no-op 검사보다 앞으로 이동**한다. 이동 외 로직 변경은 없다.

#### 3.5.3 환경 변경

해당 없음.

#### 3.5.4 배치/마이그레이션

해당 없음 — 기존 파일의 중첩 note(`tasks/092-*/state.json:71, 116, 163`)는 **소급 수정하지 않는다**(`state.json` 손편집 금지, `docs/CONVENTIONS.md` §State 관리).

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-041 | F-5 AC | 기능 테스트(신규) | 동일 행에 `mark --auto-pass --note "X"` 2회 호출 → 2회차 `ok: true`, `note == "agentic auto-pass: X"`(접두 1회), `agentic auto-pass: agentic auto-pass:` 문자열 0건 |
| TS-042 | F-5 AC | 기능 테스트(신규) | 이미 `done/auto`인 행 재-auto-pass → 응답에 `idempotent: true`, `timestamp`가 1회차 값에서 **변경되지 않음**, `updated_at` 불변 |
| TS-043 | F-5 (경계) | 회귀 테스트(신규) | `owner=user`로 done인 행에 `mark --auto-pass` → no-op이 아니라 기존 동작대로 진행(멱등 조기 반환 미발동) |
| TS-044 | F-5 (092 실측) | 회귀 테스트(신규) | ANALYSIS §4 #5가 실측한 3건 패턴(`tasks/092-*/state.json:71, 116, 163`)을 재현하는 시퀀스 실행 → 중첩 0건 |

---

### F-006: 하위호환 + 문서 정합

#### 3.6.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-harness-agentic.md` | 문서(하네스) | `:70`, `:81-86` — "PM이 사용자 확인 행에 `--auto-pass`를 명시 호출" → "도구가 다음 단계 진입 시 자동 승인(`auto_approve_prior_user_confirmations`). PM 명시 호출은 불필요" | ANALYSIS §A.6 |
| 2 | `opal/core/references/opal-harness-semi-agentic.md` | 문서(하네스) | `:44`, `:54-55` — 동일 패턴 + `MODE_BOUNDARY_STAGES` 구간은 캡틴 승인 필요(`user_confirmation_required`) 명시 | ANALYSIS §A.6 |
| 3 | `opal/skills/opal-pilot-dev/SKILL.md` | 문서(pilot) | `:322` `--auto-pass` PM 지시 → 하네스 SSOT 참조 문구로 대체 | ANALYSIS §A.6 |
| 4 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 문서(pilot) | `:290` 동일 | ANALYSIS §A.6 |
| 5 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 문서(pilot) | `:245` 동일 | ANALYSIS §A.6 |
| 6 | `opal/skills/opal-pilot-project/SKILL.md` | 문서(pilot) | `:195` 동일 | ANALYSIS §A.6 |
| 7 | `opal/skills/opal-pilot-gc/SKILL.md` | 문서(pilot) | `:457, :459` 동일 | ANALYSIS §A.6 |
| 8 | `opal/skills/opal-pilot-sdd/SKILL.md` | 문서(pilot) | `:442, :444` 동일 | ANALYSIS §A.6 |
| 9 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 문서(pilot) | `:435` 동일 | ANALYSIS §A.6 |
| 10 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 문서(pilot) | `:158` "조건부 행 자동 `na` 처리는 미구현… `na`는 현재 init 시점 agentic 사용자 확인 행에만 부여된다" → F-001 후 사실 아님. 해당 괄호 서술 삭제 | ANALYSIS §A.6 / §1.1 |
| 11 | `docs/CONVENTIONS.md` | 문서 | §State 관리에 자동 승인 계약 1줄 추가 + 변경이력 행 추가 | `docs/CONVENTIONS.md` §State 관리 |

> **변경 금지 목록**: ANALYSIS §A.6 "CLOSE 첫 행 거부 지시" 약 25지점(`opal-pilot-data-design/SKILL.md:228, 285` 외)은 R-3 "CLOSE 직전은 전 모드 불가"로 그대로 유지한다 — H-9.

#### 3.6.2 문서 정합 설계

각 pilot SKILL.md의 수정은 **하네스 SSOT를 가리키는 방식**으로 한다:

> [MUST] `.opal/AGENT.md` §업무 수행 지침: "하네스 변경 시 `opal/core/references/opal-harness.md`(SSOT)를 수정한다. 다른 곳에서 발췌·복제하지 않는다." — 자동 승인 계약의 본문 서술은 `opal-harness-agentic.md`·`opal-harness-semi-agentic.md`에만 두고, pilot SKILL.md 9종은 "사용자 확인 행은 다음 단계 진입 시 도구가 자동 승인한다(`opal-harness-{모드}.md` §{N})"는 참조 문구로 정리한다. 계약 본문을 pilot마다 복제하지 않는다.

`docs/CONVENTIONS.md` §State 관리 추가 문안(1줄):

> 파이프라인 "사용자 확인" 행은 전 모드 `pending / owner=PM`으로 초기화되며, 다음 단계 진입 시 `state-tool`이 자동 승인한다(`done / owner=auto / timestamp`). 자동 승인 불가 구간(CLOSE 직전·interactive·semi-agentic의 `MODE_BOUNDARY_STAGES`)에서는 `user_confirmation_required` 에러가 반환되며 캡틴 승인(`mark --owner user`)이 필요하다 (093).

#### 3.6.3 환경 변경

해당 없음. 전역 배포(`scripts/install-mac.sh`)는 **본 PLAN의 Step에 포함하지 않는다** — TASK.md 제약 "install은 전역 단일 타겟이라 배포 검증이 실행 중 파이프라인에 영향". CLOSE 이후 캡틴 수동 실행.

#### 3.6.4 배치/마이그레이션

해당 없음.

#### 3.6.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-051 | F-6 AC(a) / DEC-G | 회귀 테스트(신규, 실 파일) | `tasks/092-260815-opd-워크트리-작업공간-분리/state.json`을 tmp에 **복사**한 뒤 worktree `run.sh`로 `validate` → exit 0, violations 0. 이어서 미완 행에 `advance` → exit 0. 이어서 `mark --done` → exit 0. 원본은 읽기만 하고 수정하지 않는다 |
| TS-052 | F-6 AC(a) | 회귀 테스트(신규) | `status="na"` 행을 수동 주입한 state로 `check_stage_transition_guard` 호출 → 완료로 간주되어 통과(`_COMPLETE_STATUSES` 존치 확인, `tests/test_state_tool.py:2882-2900` 대조군 유지) |
| TS-053 | F-6 AC(a) | 회귀 테스트(기존 유지) | `test_ts005_na_neutral`(`tests/test_state_tool.py:5356-5367`) 그린 유지 + "F-1 이후 이 경로는 수동 주입 `na`만 실측한다"는 주석 보강 (ANALYSIS §5 "na 중립 테스트의 의미 약화") |
| TS-054 | F-6 AC(b) | 산출물 검사 | 하네스 2종·pilot 9종에서 "PM이 `--auto-pass`를 호출한다"류 일반 단계 지시가 0건이고, ANALYSIS §A.6 "CLOSE 첫 행 거부 지시" 25지점의 문자열은 변경 전후 동일(H-9) |
| TS-055 | F-6 AC(b) | 산출물 검사 | 변경한 문서 전부에 `## 변경이력` 행이 추가되고 일시 형식이 `YYYY-MM-DD HH:mm`(KST), 변경내용에 `(093)` 포함 (`docs/CONVENTIONS.md` §변경이력 작성 의무) |

<!--PART3-->

---

## 4. 실행 계획

### 4.1 Phase 그룹핑

의존 순서는 §1.3 기능 의존 그래프를 그대로 따른다 — `F-003 → F-004 → F-002 → (F-001 동시) → F-006`, `F-005`는 독립이나 `cmd_mark` 동일 구간을 만지므로 F-002 배선 이후로 순차 배치한다.

| Phase | 목적 | 포함 F-ID | 포함 Step | 완료 시 확보되는 것 | 선행 Phase |
|-------|------|----------|----------|-------------------|-----------|
| **P1. 판정 기반** | 자동 승인 가부 판정과 전용 에러의 SSOT를 먼저 세운다. 이 Phase만으로는 **런타임 동작이 변하지 않아야 한다**(경계 불변) | F-003, F-004 | Step 1~4 | `can_auto_approve_user_confirmation` 단일 판정 + `user_confirmation_required` 에러 코드 + 경계 불변 회귀표 그린 | 없음 |
| **P2. 훅 신설 + auto-na 제거** | R-1(제거)과 R-2(대체)를 **한 Phase 안에서 동시 완결**한다 | F-002, F-001 | Step 5~12 | 다음 단계 진입 시 자동 승인 + CLOSE/워커 구조적 제외 + auto-na 0건 | P1 |
| **P3. 멱등성** | `cmd_mark` note/no-op 경로 정리 | F-005 | Step 13~15 | 접두 중첩 0건 + 재-auto-pass no-op | P2 (같은 `cmd_mark` 구간 충돌 회피) |
| **P4. 하위호환 회귀** | 기존 `na` 보유 파일과 전체 스위트의 무사고 확인 | F-006 (a) | Step 16~17 | 092 실파일 회귀 0건 + 기존 테스트 전량 통과 | P3 |
| **P5. 문서 정합** | 하네스 SSOT → pilot 참조 문구 → 프로젝트 문서 순 | F-006 (b) | Step 18~20 | 문서-코드 계약 일치 + 변경이력 등재 | P4 (코드 계약 확정 후 문서화) |

> [MUST] **P2 분할 배포 금지** — Step 8(F-001 auto-na 제거)은 Step 5~7(F-002 훅)이 완료되기 전에 착수하지 않는다. F-001만 선행하면 agentic 파이프라인의 사용자 확인 행이 `pending`으로 남아 `check_stage_transition_guard`(`state_tool.py:634-679`)가 다음 단계 진입을 전면 차단한다(§1.3 각주, ANALYSIS §A.5 #3).
> [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility." — 본 체크리스트의 어떤 Step도 §3이 명시하지 않은 함수·인자·설정을 추가하지 않는다. §4는 §3의 집행 분해이며 신규 설계를 포함하지 않는다.
> [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." — 모든 Step의 편집·실행 대상 경로는 **worktree 소스**(`/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_093/`) 기준이며, `scripts/install-mac.sh` 전역 배포는 본 체크리스트에 **포함하지 않는다**(CLOSE 이후 캡틴 수동 실행 — TASK.md §제약 조건 "배포 검증 제약").

**검증 실행 규약(전 Step 공통)**

- 단위/회귀 테스트: `cd <worktree> && python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q`
- subprocess 실호출 검증: worktree 소스의 `opal/tools/state-tool/run.sh`를 직접 호출한다. `~/.opal/tools/state-tool/run.sh`(전역 배포본)를 검증에 사용하지 않는다.
- [MUST] `docs/CONVENTIONS.md` §State 관리: "파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. 마크다운 표 직접 편집 금지." — 검증용 state.json은 **tmp 복사본**에만 만들고, 본 태스크의 실제 파이프라인 STATE.md/state.json은 어떤 Step에서도 손편집하지 않는다.

### 4.2 실행 체크리스트

#### Phase 1 — 판정 기반 (F-003, F-004)

- [x] **Step 1. F-003 판정 함수 `can_auto_approve_user_confirmation` 신설 (호출자 미배선)**
  - 소속 F-ID: F-003
  - 영역: 공통(`opal/tools/state-tool/state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: §3.3.2 (1) 시그니처·본문 그대로 `MODE_BOUNDARY_STAGES` 정의(`:50-54`) 직후에 배치. 두 축 합성 순서(CLOSE → interactive → semi-agentic+`MODE_BOUNDARY_STAGES`) 고정.
  - 완료 기준: 함수가 `(allowed, deny_reason)` 튜플을 반환하고 `deny_reason ∈ {close_requires_user, interactive_requires_user, semi_agentic_pre_execute, None}`. `MODE_BOUNDARY_STAGES` 상수는 **삭제·이동하지 않음**. 이 Step 종료 시점에 기존 테스트 전량 그린(호출자 미배선이므로 동작 변화 0).
  - 의존: 없음

- [x] **Step 2. F-004 `ERROR_CODES`에 `user_confirmation_required` 추가**
  - 소속 F-ID: F-004
  - 영역: 공통(`state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: §3.4.2 문안 그대로 `ERROR_CODES` 말미(`:132` 다음)에 1종 추가. `err()` 헬퍼(`:155-159`) 외 방출 경로를 만들지 않는다.
  - 완료 기준: 기존 44종 키의 **문자열이 1건도 변경되지 않음**(diff로 확인) + 신규 키 1종 존재 → TS-034.
  - 의존: 없음 (Step 1과 병렬 가능)

- [x] **Step 3. F-003 호출자 2곳 재배선 — 사유별 소비 범위 적용**
  - 소속 F-ID: F-003
  - 영역: 공통(`state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: §3.3.2 (2) 표대로 `cmd_mark` 사전검사(`:1525-1529`)는 `semi_agentic_pre_execute`**만** 소비, `cmd_validate` 사후검사(`:1719-1732`)는 `interactive_requires_user`·`semi_agentic_pre_execute`**만** 소비하고 `close_requires_user`는 무시. `user_confirmation_owner_mismatch` 검사(`:1711-1718`)는 손대지 않는다.
  - 완료 기준: `MODE_BOUNDARY_STAGES` 참조가 판정 함수 내부 1곳으로 수렴(정의부 제외) → TS-023. 기존 테스트 전량 그린.
  - 의존: Step 1
  > **[PM 승인 — PLAN 이탈 1건, 2026-08-15 21:5x]** 판정 함수에 키워드 전용 인자 `include_close_axis=True`를 추가하고 `cmd_validate`만 `False`로 호출하는 것을 **승인**한다.
  > **사유**: 본 PLAN §3.3.2 (2)의 "cmd_validate는 `close_requires_user`를 무시" 지시와 같은 절 (3) 표 B **V-7**(CLOSE × interactive → `auto_pass_in_interactive_mode` 방출)이 자기모순이었다. 판정 함수는 축1(CLOSE) 최우선이라 CLOSE 행에 항상 `close_requires_user`를 반환하므로, 단순 필터로는 V-7이 무위반으로 바뀐다. 축 순서를 뒤집으면 이번엔 S-25가 고정한 `("CLOSE","interactive") → (False,"close_requires_user")` 계약이 깨진다. RED 테스트는 불변이므로 필터만으로 두 제약을 동시에 만족할 수 없다.
  > **판정 근거**: 키워드 인자는 DEC-E의 "cmd_validate는 CLOSE 축을 갖지 않는다"(H-4)를 **필터가 아니라 축 자체의 부재**로 표현한 것이며, 판정 로직은 여전히 단일 함수에 있다. PM 실측 확인 — `MODE_BOUNDARY_STAGES` 참조가 정의부(`:51`) + 판정 함수 내부(`:80`) **2곳뿐**으로 S-25 계약 유지, 경계 불변 회귀표 **18 subtests 전량 통과**(V-7 포함). 위치 인자 2개 시그니처도 불변이다.

- [x] **Step 4. 【쟁점 3 집행】 경계 불변 회귀표 테이블 드리븐 테스트 신설**
  - 소속 F-ID: F-003
  - 영역: 테스트(`opal/tools/state-tool/tests/test_state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: §3.3.2 (3) **표 A 9셀(B-1~B-9) + 표 B 9셀(V-1~V-9)**을 `subTest` 파라미터화로 이식한다. 두 축("CLOSE 여부 = 모드 무관 무조건 거부" / "`MODE_BOUNDARY_STAGES` 소속 = semi-agentic 한정 거부")이 각각 독립적으로 검증되도록 셀을 분리한다. 판정 함수 단위 호출 테스트(TS-024)도 함께 추가.
  - 완료 기준: TS-021·TS-022·TS-023·TS-024 그린. 특히 ①**B-7의 에러 코드가 `close_gate_violation`**이고 **B-8·B-9는 `agentic_close_gate_requires_user`**로 서로 다름을 `error` 필드 문자열까지 대조(ANALYSIS §A.2 주의 문단), ②**V-8·V-9는 `violations_count == 0`**(H-4 핵심 셀). exit code만 비교하는 assert 금지.
  - 의존: Step 3

#### Phase 2 — 훅 신설 + auto-na 제거 (F-002, F-001)

- [x] **Step 5. 【쟁점 1 집행】 F-002 훅 함수 신설 — 스캔 범위 + 워커 비활성**
  - 소속 F-ID: F-002
  - 영역: 공통(`state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: §3.2.2 (1)(2)(4) 그대로 `auto_approve_prior_user_confirmations()`를 `check_stage_transition_guard` 직후(`:679` 이후)에 신설한다. 스캔 범위는 **"직전 1단계"가 아니라 `range(row_index)` = 대상 행 앞의 모든 미완 사용자 확인 행"**(DEC-C)이며, `as_worker=True`면 즉시 `[]` 반환(훅 전면 비활성), `force=True`도 `[]` 반환. 완료 판정은 `_COMPLETE_STATUSES`(`:456`) 재사용.
  - 완료 기준: ①스캔 범위가 `check_stage_transition_guard(scope="full")`의 검사 범위 `[0, row_index)`(`:667`)와 **동일 범위**임을 코드로 확인 ②`as_worker` 분기가 함수 초입에 존재해 워커 경로에서 `state["rows"]`를 **1건도 mutate하지 않음** ③함수가 `save_state_json`을 호출하지 않음(H-8) ④note는 `agentic auto-pass:` 접두를 쓰지 않고 `auto-approved on <stage> entry` 형식.
  - 의존: Step 1, Step 2

- [x] **Step 6. 【쟁점 2 집행】 F-002 CLOSE 구조적 제외 3중 방어 구현**
  - 소속 F-ID: F-002
  - 영역: 공통(`state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: §3.2.2 (3) 3중 방어를 모두 배선한다 — ①**1차(결정적)**: 대상 행 `stage == "CLOSE"`이면 훅 전체가 즉시 `[]` 반환 ②**2차**: 후보 수집 루프에서 후보 행 `stage == "CLOSE"` 제외 ③**3차**: 판정 함수가 `CLOSE`에 대해 무조건 `(False, "close_requires_user")`(Step 1에서 확보).
  - 완료 기준: [MUST] `opal/core/references/opal-harness.md` §1 Guards "사용자의 확인된 지시(`승인`, `확인`, `확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가" — CLOSE 진입 경로에서 훅이 `check_close_gate`(`:685-723`)가 요구하는 `owner=user` 요건(`:717`)을 **우회할 수 없음**이 코드 구조로 보장된다. 1차 방어가 없으면 훅이 CLOSE 첫 행의 **직전 사용자 확인 행**(그 행의 stage는 보통 TEST/EXECUTE라 2차·3차 방어에 걸리지 않는다)을 `owner=auto`로 마킹해 게이트가 무력화되므로, 2차·3차만으로 대체하지 않는다.
  - 의존: Step 5

- [x] **Step 7. F-002 훅 호출 배선 (`cmd_advance` + `cmd_mark`) + `auto_approved` 응답 필드**
  - 소속 F-ID: F-002
  - 영역: 공통(`state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: §3.2.2 (5)(6) 그대로 `cmd_advance`(`:1425-1437`)·`cmd_mark`(`:1511-1532`) 양쪽의 `check_stage_transition_guard` **직전**에 훅 호출을 삽입한다. `_guard_scope` 계산부(`:1427`, `:1513`)의 `as_worker` 값을 훅에 명시 전달하고, `now_str`은 호출자가 `get_kst_datetime(command)`로 1회 취득해 전달(`cmd_advance`는 기존 `:1439` 호출을 앞당김). `ok(...)`에 `auto_approved` 배열 필드 추가.
  - 완료 기준: ①두 커맨드 **모두**에 삽입됨(한쪽 누락 시 실패 — ANALYSIS §A.3 (b) 리스크) ②훅 → `check_stage_transition_guard` → `check_close_gate` → `_run_clarification_hook` 순서 ③기존 `ok()` 필드가 1건도 제거·개명되지 않음.
  - 의존: Step 6

- [x] **Step 8. F-001 agentic auto-na 분기 3곳 삭제**
  - 소속 F-ID: F-001
  - 영역: 공통(`state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: §3.1.2의 블록을 `build_rows_from_spec`(`:824-829`)·`build_rows_from_skill_md`(`:916-921`)·`build_rows_from_pipeline_json`(`:1050-1055`) 3곳에서 주석 라인 포함 완전 삭제. 세 빌더의 `mode` 파라미터 시그니처는 **제거하지 않는다**. `state.schema.json:69`의 `na` enum, `_COMPLETE_STATUSES`(`:456`), `build_todo_mirror` na 필터(`:481`)는 **변경 금지**(R-6).
  - 완료 기준: TS-001 — `state_tool.py`에서 `agentic auto-na at init` 문자열 grep **0건**. `--mode agentic` 신규 init 결과의 모든 사용자 확인 행이 `status=pending / status_label=⬜ / owner=PM / timestamp=None`.
  - 의존: **Step 7** (P2 분할 배포 금지 — §4.1 [MUST])

- [x] **Step 9. 【쟁점 4-a 집행】 깨질 테스트 3건 — 전부 "수정"(삭제 0건)**
  - 소속 F-ID: F-001, F-002
  - 영역: 테스트(`tests/test_state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: DEC-F에 따라 3건 모두 **수정**한다. ①`test_init_agentic_auto_na_user_confirmation`(`:293-309`) → `test_init_agentic_user_confirmation_pending`으로 개명 + assert를 `pending`/`⬜`/`PM`으로 교체하되 **CLOSE 사용자 확인 행 `pending` 유지 assert(`:308-309`)는 보존**(TS-002). ②`test_rows_from_agentic_auto_na`(`:2200-2221`) → `test_rows_from_agentic_user_confirmation_pending`으로 개명 + `:2219` assert를 `pending`으로 교체(TS-003). ③`test_close_gate_regression_via_task_step_addressing_subprocess`(`:4806-4844`) → 주석 갱신 + row 8을 `--done --owner user`로 mark하는 단계 추가, 최종 assert(`agentic_close_gate_requires_user`)는 **불변**(TS-014). 추가로 `:1251` 주석("agentic 모드에서 TASK 사용자 확인 행은 auto-na로 초기화됨")을 사실에 맞게 갱신(TS-006).
  - 완료 기준: 3건 모두 **삭제되지 않고 존재**하며 그린. 파일 내 테스트 함수 총 개수가 Step 8 이전 대비 감소하지 않음. 추가로 `grep -n "auto.na로 이미 완료\|agentic 자동 na"` 전수 재확인(ANALYSIS §A.5 요약 권고)으로 동일 패턴 잔여 테스트를 발굴해 함께 처리.
  - 의존: Step 8

- [x] **Step 10. 【쟁점 4-b 집행】 신형 채택 검증 테스트 신규 추가 (F-1 AC(b) 성립 요건)**
  - 소속 F-ID: F-001, F-002
  - 영역: 테스트(`tests/test_state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: [MUST] **구형(auto-na) 고정 테스트를 수정·삭제하는 것만으로는 F-1 AC(b) "신형 채택"이 검증되지 않는다.** 신형 계약(pending 초기화 + 자동 승인 훅)을 직접 검증하는 테스트를 신규로 추가한다 — ①TS-004: 동일 `--rows-from` pipeline.json 스펙을 interactive/semi-agentic/agentic 3모드로 init → `rows[]` 전 필드 **diff 0**(F-1 AC(b)의 유일한 직접 검증) ②TS-005: agentic init 직후 사용자 확인 행이 `pending/PM/timestamp=None`임을 확인한 뒤, 훅 발동으로 `done/auto/timestamp≠None`이 되는 것까지 **한 시나리오에서 연속** 검증 ③TS-011: agentic에서 ANALYSIS 사용자 확인 행 `pending` 상태로 PLAN 첫 행 `advance` → `--auto-pass` 없이 `done/owner=auto/timestamp≠None` + exit 0 ④TS-016: 성공 응답 stdout JSON에 `auto_approved` 배열이 승인된 row_id를 담음.
  - 완료 기준: TS-004·TS-005·TS-011·TS-016 그린. TS-005의 assert에 `timestamp is None`(init 직후)과 `timestamp is not None`(훅 이후)이 **둘 다** 존재.
  - 의존: Step 9

- [x] **Step 11. 【쟁점 1·2 검증】 CLOSE 제외 · 워커 스코프 · 파일 미오염 보안 회귀 테스트**
  - 소속 F-ID: F-002
  - 영역: 테스트(`tests/test_state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: ①TS-012(H-1/DEC-D): agentic 파이프라인에서 EXECUTE 사용자 확인 행을 `pending`으로 둔 채 CLOSE 첫 행 mark → 자동 승인이 **일어나지 않고** 차단되며, state.json 재로드 시 해당 행이 **여전히 `pending`** ②TS-013(H-2/DEC-C): `--as-worker --worker-stage EXECUTE`로 EXECUTE 행 mark → 앞 단계 PLAN 사용자 확인 행 `pending` 유지 + `stage_transition_violation` exit 1(워커 우회 불가) ③TS-015(H-8): 훅 통과 후 `check_gate_artifacts`가 `gate_artifact_missing`으로 실패 → **저장된 파일**의 사용자 확인 행이 여전히 `pending`.
  - 완료 기준: 3건 그린. ①②는 **worktree `run.sh` subprocess 실호출 + state.json 재로드**로 검증한다(메모리상 반환값만 보는 assert 금지 — 파일 실측이 회귀 방지의 요체).
  - 의존: Step 10

- [x] **Step 12. F-004 전용 에러 경로 테스트 + DEC-A 경로 분리 회귀**
  - 소속 F-ID: F-004
  - 영역: 테스트(`tests/test_state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: TS-031(interactive 훅 → `user_confirmation_required` + `row_id`/`stage`/`reason`/`required_action` 페이로드) · TS-032(**DEC-A 경로 분리** — 동일 interactive 파이프라인에서 PM 직접 `mark --auto-pass`는 **기존대로 exit 0**, 이어지는 `validate`가 `auto_pass_in_interactive_mode` 1건 방출) · TS-033(semi-agentic + `MODE_BOUNDARY_STAGES` → `reason == "semi_agentic_pre_execute"`) · TS-034(에러 SSOT).
  - 완료 기준: 4건 그린. 특히 TS-032가 "훅 경로는 차단, PM 명시 호출 경로는 현행 유지"라는 DEC-A를 실측한다.
  - 의존: Step 11

#### Phase 3 — 멱등성 (F-005)

- [x] **Step 13. F-005 note 접두 중첩 제거 + `_AUTO_PASS_PREFIX` 상수화**
  - 소속 F-ID: F-005
  - 영역: 공통(`state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: §3.5.2 (1) 그대로 `cmd_mark`(`:1562-1567`)를 3분기(`빈 note` / `이미 접두 보유` / `신규 접두 부여`)로 교체.
  - 완료 기준: [MUST] 접두 문자열 `"agentic auto-pass"` **자체는 변경하지 않는다**(기존 state.json·하네스 문서가 참조). 중첩만 제거.
  - 의존: Step 12

- [x] **Step 14. F-005 재-auto-pass no-op 조기 반환 + `_step_str` 산출 이동**
  - 소속 F-ID: F-005
  - 영역: 공통(`state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: §3.5.2 (2) 그대로 `check_gate_artifacts`(`:1532`) 직후·`get_kst_datetime`(`:1534`) 직전에 no-op 조기 반환을 삽입한다. 조건은 `auto_pass and not force and not _step_str and status == "done" and owner == "auto"` 4중으로 **좁게** 유지한다. `_step_str` 산출 2줄(`:1539-1540`)을 no-op 검사보다 앞으로 이동하되 **로직은 변경하지 않는다**.
  - 완료 기준: `owner=user`로 done인 행은 no-op에 걸리지 않고 기존 경로로 진행(CLOSE 게이트 요건 보호). `--force`·`--step N/M` 경로도 no-op에 삼켜지지 않음.
  - 의존: Step 13

- [x] **Step 15. F-005 멱등성 회귀 테스트**
  - 소속 F-ID: F-005
  - 영역: 테스트(`tests/test_state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: TS-041(2회 호출 → 접두 1회, `agentic auto-pass: agentic auto-pass:` 0건) · TS-042(`idempotent: true`, `timestamp`·`updated_at` 불변) · TS-043(`owner=user` done 행은 no-op 미발동) · TS-044(ANALYSIS §4 #5 실측 3건 패턴 재현 → 중첩 0건).
  - 완료 기준: 4건 그린. TS-044는 `tasks/092-*/state.json:71, 116, 163`의 3건 패턴을 **모두** 재현 대상으로 삼는다(2건이 아님 — TASK.md §PM 정정 2026-08-15 20:14).
  - 의존: Step 14

#### Phase 4 — 하위호환 회귀 (F-006 (a))

- [x] **Step 16. 【쟁점 5 집행】 기존 `na` 보유 state.json 하위호환 회귀 (092 실파일)**
  - 소속 F-ID: F-006
  - 영역: 테스트(`tests/test_state_tool.py`)
  - agent: `opal-task-agent`
  - 내용: DEC-G에 따라 `tasks/092-260815-opd-워크트리-작업공간-분리/state.json`을 **tmp에 복사**한 뒤 worktree `opal/tools/state-tool/run.sh`로 `validate` → `advance` → `mark --done` 3종을 subprocess 실호출한다(TS-051). 함께 TS-052(`status="na"` 수동 주입 행이 `_COMPLETE_STATUSES`로 완료 인정되어 `check_stage_transition_guard` 통과 — 대조군 `tests/test_state_tool.py:2882-2900` 유지) · TS-053(`test_ts005_na_neutral` 그린 유지 + 의미 약화 주석 보강)을 수행.
  - 완료 기준: [MUST] **원본 `tasks/092-*/state.json`은 읽기만 하고 수정하지 않는다**(`docs/CONVENTIONS.md` §State 관리 — 마크다운/상태 파일 직접 편집 금지). 3종 명령 모두 **exit 0, violations 0**. `na` enum·`_COMPLETE_STATUSES`·`build_todo_mirror` na 필터가 diff 0.
  - 의존: Step 15

- [x] **Step 17. 전체 테스트 스위트 전량 통과 확인**
  - 소속 F-ID: F-001~F-006
  - 영역: 테스트
  - agent: `opal-task-agent`
  - 내용: worktree에서 `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` 전량 실행. 실패 0 확인. 스킵/xfail이 새로 생겼다면 사유를 기록한다.
  - 완료 기준: TASK.md 완료기준 ⑦ "state-tool 기존 테스트 전량 통과" 충족. 신규 TS-001~TS-055 중 자동화 대상이 모두 수집됨.
  - 의존: Step 16

#### Phase 5 — 문서 정합 (F-006 (b))

- [x] **Step 18. 하네스 SSOT 2종 수정**
  - 소속 F-ID: F-006
  - 영역: 문서(하네스)
  - agent: `opal-task-agent`
  - 내용: §3.6.1 #1~#2 — `opal/core/references/opal-harness-agentic.md`(`:70`, `:81-86`)와 `opal-harness-semi-agentic.md`(`:44`, `:54-55`)의 "PM이 사용자 확인 행에 `--auto-pass`를 명시 호출" 지시를 "도구가 다음 단계 진입 시 자동 승인한다(`auto_approve_prior_user_confirmations`)"로 교체하고, semi-agentic 문서에는 `MODE_BOUNDARY_STAGES` 구간의 캡틴 승인 필요(`user_confirmation_required`)를 명시한다.
  - 완료 기준: [MUST] `.opal/AGENT.md` §업무 수행 지침 "하네스 변경 시 `opal/core/references/opal-harness.md`(SSOT)를 수정한다. 다른 곳에서 발췌·복제하지 않는다." — 자동 승인 계약의 **본문 서술은 하네스 2종에만** 존재한다. 각 문서에 `## 변경이력` 행 추가(`YYYY-MM-DD HH:mm` KST, semver, 변경내용에 `(093)` 포함).
  - 의존: Step 17

- [x] **Step 19. pilot SKILL.md 9종 참조 문구 정리 + CLOSE 지시 불변 확인**
  - 소속 F-ID: F-006
  - 영역: 문서(pilot)
  - agent: `opal-task-agent`
  - 내용: §3.6.1 #3~#10 — `opal-pilot-dev`(`:322`)·`dev-short`(`:290`)·`dev-wireframe`(`:245`)·`project`(`:195`)·`gc`(`:457, 459`)·`sdd`(`:442, 444`)·`project-loop`(`:435`) 7종의 `--auto-pass` PM 지시를 하네스 SSOT 참조 문구로 대체하고, `project-dev`(`:158`)의 "조건부 행 자동 `na` 처리는 미구현… `na`는 현재 init 시점 agentic 사용자 확인 행에만 부여된다" 괄호 서술을 삭제한다.
  - 완료 기준: TS-054 — ①일반 단계 "PM이 `--auto-pass`를 호출한다"류 지시 **0건** ②[MUST] ANALYSIS §A.6 **"CLOSE 첫 행 거부 지시" 약 25지점**(`opal-pilot-data-design/SKILL.md:228, 285` 외)의 문자열이 변경 전후 **동일**함을 grep 대조로 확인(H-9 — 이 목록을 건드리면 CLOSE 절차 서술이 붕괴한다) ③변경한 문서마다 `## 변경이력` 행 추가.
  - 의존: Step 18

- [x] **Step 20. `docs/` 갱신 — CONVENTIONS.md 자동 승인 계약 등재**
  - 소속 F-ID: F-006
  - 영역: 문서
  - agent: `opal-task-agent`
  - 내용: §3.6.2 문안 1줄을 `docs/CONVENTIONS.md` §State 관리에 추가한다(사용자 확인 행의 초기화·자동 승인·불가 구간 에러 계약). 본 태스크가 state-tool의 상태 계약을 바꾸므로 `docs/CONVENTIONS.md` 갱신이 필요하다.
  - 완료 기준: TS-055 — 변경한 문서 전부(`docs/CONVENTIONS.md` 포함)에 `## 변경이력` 행이 추가되고, 일시 형식이 `YYYY-MM-DD HH:mm`(KST)이며 변경내용에 `(093)`이 포함된다([MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무).
  - 의존: Step 19

> **5쟁점 ↔ Step 대응 요약**: 쟁점1(훅 스캔 범위) → **Step 5**(검증 Step 11) / 쟁점2(CLOSE 구조적 제외) → **Step 6**(검증 Step 11) / 쟁점3(두 축 합성 + 경계 불변 회귀표) → **Step 1·3**(검증 Step 4) / 쟁점4(깨질 테스트 3건 처리 + 신형 검증) → **Step 9·10** / 쟁점5(`na` 하위호환 회귀) → **Step 16**.

---

## 5. QA 체크리스트

PLAN 산출물 자체와 EXECUTE 완료본을 대상으로 하는 검수 항목이다. 각 항목은 근거 섹션을 명시한다.

### 5.1 설계 정합 (PLAN 자체 검수)

- [ ] Q-1. §1.2 기능 6개(F-001~F-006)가 TASK.md 요구사항 F-1~F-6과 1:1 대응하며 누락·추가가 없다.
- [ ] Q-2. §2.7 DEC-A~DEC-G 7건이 모두 §3의 특정 소절을 근거로 지목하고, 그 소절에 실제 결론이 서술되어 있다.
- [ ] Q-3. §4.2 전 Step에 **소속 F-ID / 영역 / agent / 완료 기준 / 의존**이 빠짐없이 기재되어 있고, `agent`는 전부 `opal-task-agent`다.
- [ ] Q-4. §4.2의 의존 관계가 §1.3 기능 의존 그래프 및 §4.1 Phase 순서와 모순되지 않는다(순환 의존 0).
- [ ] Q-5. §3의 모든 코드 인용이 코드 루트(`/.opal-worktrees/task_093/`) 기준 `파일:줄번호` 형식이며, `opal/core/references/harness/citation-rules.md` §2 인용 형식을 따른다.
- [ ] Q-6. 금지/강제 규칙이 `[MUST]` 포맷으로 표기되어 있다(`citation-rules.md` §4 — PLAN 단계 인라인 인용 필수).
- [ ] Q-7. §4가 §3에 없는 신규 설계(새 함수·새 인자·새 설정)를 도입하지 않았다([MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First).

### 5.2 5쟁점 종결 검수

- [ ] Q-8. **쟁점 1** — 훅 스캔 범위가 "직전 1단계"가 아니라 `range(row_index)` 전 범위로 확정되었고(DEC-C), 그 범위가 `check_stage_transition_guard(scope="full")`의 `[0, row_index)`(`state_tool.py:667`)와 일치한다. 워커 경로(`--as-worker`, `scope=prior_stage_only`)에서는 훅이 전면 비활성이다(Step 5).
- [ ] Q-9. **쟁점 2** — CLOSE 구조적 제외가 **1차(대상 행 stage==CLOSE 즉시 no-op)** 를 포함한 3중 방어로 구현되었다. 2차·3차만으로는 CLOSE 첫 행의 **직전 사용자 확인 행**(stage가 CLOSE가 아님)을 막지 못한다는 점이 Step 6 완료 기준에 명시되어 있다.
- [ ] Q-10. **쟁점 2 (회귀 방지)** — 훅이 `check_close_gate`의 `owner=user` 요건(`state_tool.py:717`)을 우회하지 못함이 파일 실측(TS-012)으로 검증된다.
- [ ] Q-11. **쟁점 3** — §3.3.2 판정 함수가 "CLOSE 여부(모드 무관 무조건 거부)"와 "`MODE_BOUNDARY_STAGES` 소속 여부(semi-agentic 한정 거부)" 두 축을 합성하며, 두 축이 상호 배타임이 근거와 함께 서술되어 있다.
- [ ] Q-12. **쟁점 3 (회귀표)** — ANALYSIS §A.2 현황표가 §3.3.2 (3) 표 A(B-1~B-9)·표 B(V-1~V-9)로 승격되었고, **interactive+CLOSE 조합의 에러 코드 차이**(B-7 `close_gate_violation` vs B-8/B-9 `agentic_close_gate_requires_user`)가 명시적으로 검증 대상이다.
- [ ] Q-13. **쟁점 3 (H-4)** — 표 B의 V-8·V-9(CLOSE + semi-agentic/agentic → 위반 없음)가 유지되며, `cmd_validate`가 `close_requires_user`를 소비하지 않는다.
- [ ] Q-14. **쟁점 4 (a)** — 깨질 테스트 3건 각각에 대해 삭제/수정/대체 중 무엇인지가 Step 9에 명시되어 있다(DEC-F: 3건 전부 수정, 삭제 0건).
- [ ] Q-15. **쟁점 4 (b)** — 구형 auto-na 고정 테스트를 수정·삭제하는 것과 **별개로**, 신형(pending 초기화 + 자동 승인 훅)을 검증하는 신규 테스트가 Step 10에 존재한다. 이것이 없으면 F-1 AC(b) "신형 채택"이 성립하지 않는다.
- [ ] Q-16. **쟁점 5** — 기존 `na` 보유 state.json(`tasks/092-*/state.json`)으로 advance/mark/validate가 무사고 동작함을 검증하는 Step 16이 존재하며, 원본 미수정·tmp 복사본 사용이 완료 기준에 있다.

### 5.3 구현 검수 (EXECUTE 완료 후)

- [ ] Q-17. `state_tool.py`에서 `agentic auto-na at init` 문자열 grep 0건이고, `--mode agentic` 신규 init의 사용자 확인 행이 전부 `pending/PM/timestamp=None`이다(TASK.md 완료기준 ①②).
- [ ] Q-18. 3모드(interactive/semi-agentic/agentic) init 결과가 행 단위 diff 0이다(F-1 AC(b), TS-004).
- [ ] Q-19. `--auto-pass` 명시 호출 **없이** 다음 단계 진입만으로 앞 단계 사용자 확인 행이 `done/auto/timestamp≠None`이 된다(TASK.md 완료기준 ③, TS-011).
- [ ] Q-20. 자동 승인 불가 구간에서 `user_confirmation_required`가 반환되고 페이로드에 `row_id`·`stage`·`reason`·`required_action`이 포함된다(TASK.md 완료기준 ④, TS-031).
- [ ] Q-21. 동일 행 재-mark 시 `agentic auto-pass: agentic auto-pass:` 중첩 0건이고, 재-auto-pass가 `idempotent: true`로 성공하며 `timestamp`가 불변이다(TASK.md 완료기준 ⑤, TS-041·TS-042).
- [ ] Q-22. `_COMPLETE_STATUSES`(`:456`)·`build_todo_mirror` na 필터(`:481`)·`state.schema.json:69` status enum이 **diff 0**이다(R-6 하위호환).
- [ ] Q-23. `ERROR_CODES` 기존 44종 키의 문자열이 1건도 변경되지 않았고 신규 1종만 추가되었다(TS-034).
- [ ] Q-24. `MODE_BOUNDARY_STAGES` 참조 지점이 판정 함수 내부 1곳뿐이다(정의부 제외, TS-023).
- [ ] Q-25. `state_tool.py` 전체 테스트 스위트가 실패 0으로 통과한다(TASK.md 완료기준 ⑦, Step 17).
- [ ] Q-26. 훅 함수가 `save_state_json`을 호출하지 않으며, 후속 가드 실패 시 파일이 오염되지 않는다(H-8, TS-015).

### 5.4 문서·운영 검수

- [ ] Q-27. 하네스 계약 본문이 `opal-harness-agentic.md`·`opal-harness-semi-agentic.md`에만 존재하고 pilot SKILL.md 9종은 참조 문구만 갖는다([MUST] `.opal/AGENT.md` §업무 수행 지침 — SSOT 발췌·복제 금지).
- [ ] Q-28. ANALYSIS §A.6 "CLOSE 첫 행 거부 지시" 약 25지점의 문자열이 변경 전후 동일하다(H-9, TS-054).
- [ ] Q-29. 변경한 스킬·에이전트·참조 문서 전부에 `## 변경이력` 행이 추가되고 형식이 `YYYY-MM-DD HH:mm`(KST) + semver + `(093)`이다([MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무, TS-055).
- [ ] Q-30. 어떤 Step도 `~/.opal/` 배포본을 직접 편집하거나 `scripts/install-mac.sh`를 실행하지 않았다([MUST] `.opal/AGENT.md` §금지사항 / TASK.md §제약 조건 "배포 검증 제약" — 전역 배포는 CLOSE 이후 캡틴 수동 실행).
- [ ] Q-31. 검증에 사용한 state.json이 전부 tmp 복사본이며, 실제 파이프라인 STATE.md/state.json을 손편집하지 않았다([MUST] `docs/CONVENTIONS.md` §State 관리).

---

## 8. 부록

### 8.3 참조 문서

> 스키마: `opal/core/references/harness/citation-rules.md` §3.1

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| P-1 | 기획 | TASK.md | `tasks/093-260815-opd-사용자확인행-자동승인-일원화/TASK.md` | 요구사항 F-1~F-6·확정 방향 R-1~R-6·제약 조건 원본 |
| P-2 | 분석 | ANALYSIS.md | `tasks/093-260815-opd-사용자확인행-자동승인-일원화/ANALYSIS.md` | §A.1 코드 위치표, §A.2 판정 현황표(경계 불변 회귀표의 원본), §A.3 훅 삽입 지점 비교, §A.5 깨질 테스트 전수, §A.6 문서 지시 전수 |
| P-3 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` (코드 루트) | 변경 본체 — 빌더 3종 auto-na(`:824-829`, `:916-921`, `:1050-1055`), 가드(`:634-679`, `:685-723`), `cmd_advance`(`:1409-1457`), `cmd_mark`(`:1474-1660`), `cmd_validate`(`:1691-1748`), `MODE_BOUNDARY_STAGES`(`:50-54`), `ERROR_CODES`(`:81-133`) |
| P-4 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` (코드 루트) | 회귀 기준 — 깨질 테스트 3건(`:293-309`, `:2200-2221`, `:4806-4844`), 대조군(`:2882-2900`, `:5356-5367`) |
| P-5 | 소스 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` (코드 루트) | `rows[].status` enum(`:69`) `na` 존치 판단 — R-6 하위호환 |
| P-6 | 소스 | 092 state.json | `tasks/092-260815-opd-워크트리-작업공간-분리/state.json` | 결함 실측 증거(`:20-30` na 행, `:71, 116, 163` note 이중 접두 3건) + 쟁점 5 하위호환 회귀 입력 |
| P-7 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` (코드 루트) | §1 Guards — CLOSE 진입 게이트(`:33`), 커밋 규칙. 쟁점 2 CLOSE 구조적 제외의 상위 근거 |
| P-8 | 설계 | opal-harness-agentic.md | `opal/core/references/opal-harness-agentic.md` (코드 루트) | agentic `--auto-pass` 지시 SSOT(`:70`, `:81-86`) — F-006 수정 대상 |
| P-9 | 설계 | opal-harness-semi-agentic.md | `opal/core/references/opal-harness-semi-agentic.md` (코드 루트) | semi-agentic 동일 패턴(`:44`, `:54-55`) — F-006 수정 대상 |
| P-10 | 설계 | opal-pilot-* SKILL.md 10종 | `opal/skills/opal-pilot-*/SKILL.md` (코드 루트) | `--auto-pass` PM 지시 지점(수정 대상 9종) 및 CLOSE 첫 행 거부 지시(불변 대상 약 25지점) |
| P-11 | 컨벤션 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 언어 규칙·State 관리·배포 경계·변경이력 작성 의무 — 본 PLAN의 [MUST] 제약 출처, F-006 갱신 대상 |
| P-12 | 규범 | AGENT.md (프로젝트) | `.opal/AGENT.md` | §금지사항(`~/.opal/` 직접 편집 금지·STATE.md 직접 편집 금지), §업무 수행 지침(하네스 SSOT 단일 수정) |
| P-13 | 규범 | PRINCIPLES.md | `~/.opal/PRINCIPLES.md` | §2 Simplicity First(투기적 추상화 금지 — F-005 no-op 조건 협소화 근거), §3 Surgical Changes(빌더 시그니처 불변 근거) |
| P-14 | 규범 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §2 인용 형식, §3.1 참조 문서 테이블 스키마, §4 PLAN 단계 인라인 인용·`[MUST]` 포맷 필수 |

<!--PART4-->

