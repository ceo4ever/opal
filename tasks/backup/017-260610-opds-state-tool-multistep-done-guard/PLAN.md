# PLAN: state-tool 다중 Step EXECUTE 행 조기 done 가드

> 작성일: 2026-06-10 | 입력: TASK.md (ANALYSIS.md 없음 — opds이나 PLAN에서 ANALYSIS 수준 직접 코드 분석 수행)
> 모드: Flat (기능 1개 — 단일 파일 가드 보강)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`state-tool mark`가 다중 Step이 단일 EXECUTE 행에 흡수된 구조에서 `--step N/M`(N<M) + `--done`을 받으면 행을 조기에 done으로 닫는 도구 갭(016 회귀)을 차단한다. 진행률을 state.json 행에 영속화(`step: "N/M"`)하고, N<M이면 행을 in_progress로 유지, N==M에서만 done 처리한다. 진행률 미완 행은 기존 stage-transition guard / close gate가 자동으로 차단한다. RED-first 자기적용(self-confirming 위험 영역 — 상태 전이 로직).

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 다중 Step 조기 done 가드 + 진행률 영속화 (3층 가드) | R-1, R-2, R-3, R-4, R-5 | P0 | 없음 |

> 기능 1개 → **Flat 모드**. §2·§3 F 하위 섹션 생략, 평면 작성.

### 1.3 기능 의존 그래프

생략 (단일 기능).

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `cmd_mark` `--step` 파싱 + N<M 분기 (`state_tool.py:928-931`) | `--done`이면 항상 status=done이던 계약 변경 → `--step` 없는 단일 Step mark도 영향받으면 전체 파이프라인 붕괴 | P0 | L1(단위) 의무 + L2(전체 스위트 회귀) 의무 | S-1, S-5 |
| H-2 | 진행률 영속화 `row["step"]` 필드 추가 (행 스키마 변경) | 기존 state.json엔 `step` 필드 없음 → `render_pipeline_table`/`validate`/`show`가 신규 키에 KeyError 또는 마커 렌더 깨짐 | P1 | L1(단위) + L2(show/validate 회귀) 의무 | S-1, S-2, S-6 |
| H-3 | N<M 행 in_progress 유지 → 다음 단계 mark/advance 차단 (기존 `check_stage_transition_guard` `state_tool.py:341-385` 의존) | in_progress가 `_COMPLETE_STATUSES`에 없으므로 자동 차단되리라 가정 — 가정이 틀리면 ②단계전환 가드 미동작 | P0 | L1(단위) 의무 — 실제 거부 동작 증거 | S-3 |
| H-4 | CLOSE 진입 시 선행 다중 Step 행 진행률 완료 검증 (`check_close_gate` `state_tool.py:392-429` 경로) | 선행 EXECUTE 행이 in_progress(N<M)면 CLOSE 첫 행 mark/advance가 차단돼야 함 — H-3 guard가 close 경로에도 적용되는지 | P0 | L1(단위) 의무 | S-4 |
| H-5 | `--step` 형식 파싱(`re`/split) | `"1/7"` 외 비정형 입력(`"abc"`, `"3"`, `"0/0"`)에 ValueError → 도구 크래시 | P2 | L1(단위) 경계값 | S-7 |
| H-6 | ERROR_CODES 개수 완전성 테스트(`test_error_codes_count`, 현재 30 고정 `test_state_tool.py:1740`) | 신규 ERROR_CODE 추가 시 30→N 카운트 깨짐 (회귀) | P1 | L2(완전성 테스트) — 코드 추가 여부에 따라 갱신 | S-6 |

**핵심 결론(H-3)**: in_progress는 `_COMPLETE_STATUSES = {"done","additional_work_done","na"}`(`state_tool.py:338`)에 **포함되지 않으므로**, R-1이 N<M 행을 in_progress로 유지하면 기존 stage-transition guard가 그 행을 "미완"으로 판정하여 다음 단계 mark/advance를 자동 차단한다. ②단계 전환 가드는 **신규 ERROR_CODE 불필요** (상세 §3.6 D-3).

---

## 2. 기능별 분석 (Flat)

### 2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | `cmd_mark` `--step` 파싱·N<M 분기·진행률 영속화 + @header 갱신 | 수정 |
| 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | R-1/R-2/R-5 RED 테스트 + 하위호환·회귀 케이스 | 수정 |
| 배치 | `~/.opal/tools/state-tool/` (install 재배포) | 수정본 배포 (직접 편집 금지 — install 경유) | 배포 |
| 문서 | `tasks/017.../DONE.md` 등 변경이력 | R-4 변경이력 (CLOSE 단계 PM 처리) | 수정 |

> [MUST] `.opal/AGENT.md`: `~/.opal/` 직접 편집 금지 — `opal/tools/state-tool/`만 수정 후 install 재배포 (→ D-5 §배포 경계, TASK §제약).

### 2.2 현재 구현 (직접 코드 분석)

**(a) `--step`의 현재 처리 — 진행률 표시 메타로만 사용, state.json 미저장**
- argparse 정의: `p_mark.add_argument("--step", metavar="N/M")` (`state_tool.py:1557`) — 자유 문자열, N/M 파싱·검증 없음.
- `cmd_mark` 내 유일한 사용처: `if args.as_worker and getattr(args, "step", None): progress_text = f"Step {args.step} 완료"` (`state_tool.py:966-967`). STATE.md `- 진행:` 라인 표시용일 뿐, **state.json 행에는 저장되지 않는다**.

**(b) `--done` 처리 — 무조건 done**
- `cmd_mark`는 `--done` required(`state_tool.py:1551`)이며, 본문에서 `row["status"]="done"; row["status_label"]="✅"`를 **무조건** 실행한다(`state_tool.py:929-931`). `--step` 값과 무관 — 이것이 016 조기 done의 도구 갭(TASK §17 ③).

**(c) stage-transition guard — 행 done 기준**
- `check_stage_transition_guard`(`state_tool.py:341-385`): 대상 행 앞의 행이 `_COMPLETE_STATUSES = {"done","additional_work_done","na"}`(`state_tool.py:338`)에 없으면 `stage_transition_violation`(`state_tool.py:382-385`). 멱등(이미 done 행 재mark)·force·na는 통과. `scope="prior_stage_only"`(워커)는 같은 stage 앞 행 검증 제외, `scope="full"`(PM)은 전체.

**(d) close gate — prev_user_row 기준**
- `check_close_gate`(`state_tool.py:392-429`): CLOSE 단계 첫 행일 때만 동작. 직전 "사용자 확인" 행(역순 검색)이 `status=="done"` & `owner=="user"`가 아니면 `close_gate_violation`(`state_tool.py:420-429`). agentic/semi-agentic + auto_pass면 `agentic_close_gate_requires_user`(`state_tool.py:407-408`).
- mark/advance는 **stage-transition guard를 먼저** 호출(`mark` `state_tool.py:912-916`, `advance` `state_tool.py:852-856`)한 뒤 close gate 호출. 따라서 CLOSE 첫 행 진입 시 선행 EXECUTE 행이 in_progress면 stage-transition guard가 **먼저** 차단한다(close gate까지 도달 전).

**(e) 행 스키마**
- `build_rows_from_spec`(`state_tool.py:461-470`) / `build_rows_from_skill_md`(`state_tool.py:553-562`) / `parse_existing_state_md`(`state_tool.py:598-607`)가 생성하는 행 필드: `row_id / stage / item / status / status_label / timestamp / owner / note`. **`step` 필드 없음** → 신규 필드 추가는 하위 호환 필요(기존 state.json엔 부재).
- `render_pipeline_table`(`state_tool.py:216-221`)은 `row['row_id'/'stage'/'item'/'status_label']` + `row.get("timestamp")`만 참조 → `step` 추가해도 마커 렌더 영향 없음(추가 필드는 무시됨).
- `cmd_validate`(`state_tool.py:1034-1091`)는 `step` 필드를 참조하지 않음 → 신규 키 무해.

**(f) ERROR_CODES 30종**
- `ERROR_CODES`(`state_tool.py:68-101`) 30종. 완전성 테스트 `test_error_codes_count`가 `len==30` 고정(`test_state_tool.py:1740`), `EXPECTED_CODES` 30개 리스트(`test_state_tool.py:1701-1736`).

**(g) 기존 테스트 패턴**
- `make_args`(`test_state_tool.py:89-120`)는 이미 `"step": None` 키 보유(`test_state_tool.py:108`). `_mark` 헬퍼는 `step=` 인자 지원(`test_state_tool.py:176-188`).
- `BaseTestCase`(`test_state_tool.py:123`) + `_init`(`test_state_tool.py:154`) fixture: tempdir + `_mock_now()`(date.js 모킹). `TestStageTransitionGuard`(`test_state_tool.py:1996`)·`TestNewStandardRowStructure`(`test_state_tool.py:2259`)가 guard/close 패턴 SSOT.

### 2.3 영향 범위

- **상위 의존(호출자)**: `mark` CLI 호출 측 — opds EXECUTE 워커(`--step N/M --done` 디스패치). 동작 변경: N<M이면 done 미처리 → 워커가 진행률만 누적.
- **하위 의존(피호출)**: `check_stage_transition_guard` / `check_close_gate`는 변경 불요(행 status가 이미 진실을 표현). `render_pipeline_table` / `cmd_validate` / `cmd_show`는 신규 `step` 키에 무영향(읽지 않음).
- **공유 상태**: state.json 행 스키마(+`step`). 하위 호환: 기존 행에 `step` 부재 → `row.get("step")` None-safe 접근.
- **관련 테스트**: `TestMark`(`test_state_tool.py:390`), `TestStageTransitionGuard`(1996), `TestNewStandardRowStructure`(2259), `TestErrorCodesCompleteness`(1698). 전체 165 비파괴 필수.

---

## 3. 기능별 설계 (Flat)

### 3.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| - | (없음) | - | 신규 파일 없음 — 기존 파일 보강 | - |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | `cmd_mark`에 `--step N/M` 파싱 헬퍼 + N<M 분기(in_progress 유지 + `step` 저장) / N==M 분기(done). 단일 Step·`--step` 미지정은 기존 done. @header 017 갱신 | `state_tool.py:928-967` (현 done 무조건 분기) |
| 2 | `opal/tools/state-tool/tests/test_state_tool.py` | 테스트 | R-1/R-2/R-5 RED 테스트 클래스 신설 + 하위호환·회귀 케이스 | `test_state_tool.py:390,1996,2259` 패턴 |
| 3 | `~/.opal/tools/state-tool/` | 배치 | install 재배포 (직접 편집 금지) | (→ D-5 §배포 경계) |

### 3.2 API·데이터 모델 설계

#### 3.2.1 `--step` 파싱 헬퍼 (신규 모듈 함수)

```python
def _parse_step(step_str, command):
    """--step "N/M" → (N:int, M:int) 반환. 형식 위반 시 None 반환(보수적 — 기존 동작 유지).
    표준 라이브러리만 (T-11) — re 사용."""
    # 형식: 정수/정수, M>=1, N>=0, N<=M
    m = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", step_str or "")
    if not m:
        return None
    n, total = int(m.group(1)), int(m.group(2))
    if total < 1 or n < 0 or n > total:
        return None
    return (n, total)
```

- 시그니처: `_parse_step(step_str: str, command: str) -> tuple[int,int] | None`.
- [MUST] T-11(`state_tool.py:14`): 표준 라이브러리만 — `re` 사용, 외부 패키지 금지 (→ D-1 §제약).
- 비정형/None 입력 시 `None` 반환 → 호출부는 "step 미지정"과 동일하게 기존 done 경로(하위 호환). 이는 H-5 크래시 방어 (C-4 비파괴).
- 공개 인터페이스 검증 원칙(red-first.md §4): 내부 함수지만 검증은 `cmd_mark`의 관측 행위(state.json status/step, exit code)로 수행한다 (→ D-3 §4).

#### 3.2.2 `cmd_mark` 분기 설계 (핵심)

현재 `state_tool.py:928-931`의 무조건 done을 아래 분기로 교체한다.

```python
now_str = get_kst_datetime(command)

# --- 017: 다중 Step 진행률 파싱 + 조기 done 가드 ---
step_pair = _parse_step(getattr(args, "step", None), command) if getattr(args, "step", None) else None

if step_pair is not None:
    n, total = step_pair
    row["step"] = f"{n}/{total}"          # 진행률 영속화 (R-1, C-5)
    row["timestamp"] = now_str
    if n < total:
        # 마지막 Step 아님 → 행을 done으로 닫지 않고 in_progress 유지 (R-1, C-1)
        row["status"]       = "in_progress"
        row["status_label"] = "🔄"
        # owner/note는 아래 공통 블록에서 처리(워커 진행률 기록 목적)
        _mark_step_done = False
    else:
        # n == total → 마지막 Step → 정상 done (R-2, C-2)
        row["status"]       = "done"
        row["status_label"] = "✅"
        _mark_step_done = True
else:
    # --step 미지정 또는 비정형 → 기존 동작(즉시 done) 유지 (C-4 하위 호환)
    row["status"]       = "done"
    row["status_label"] = "✅"
    row["timestamp"]    = now_str
    _mark_step_done = True
```

설계 결정:
- **진행률 영속화**: `row["step"] = "N/M"` 문자열로 저장. 기존 행 스키마에 신규 키 추가 — `render_pipeline_table`(`state_tool.py:216`)·`validate`(`state_tool.py:1034`)가 읽지 않으므로 하위 호환(H-2). [MUST] 신규 키는 `row.get("step")` None-safe로만 소비 (→ D-1 §하위 호환).
- **N<M → in_progress 유지**: status를 `in_progress`로 둠으로써 `_COMPLETE_STATUSES`(`state_tool.py:338`)에 미포함 → 후속 단계 guard가 자동 차단(H-3). `--done`을 받았어도 닫지 않음 — 이것이 R-1 핵심.
- **N==M → done**: 마지막 Step에서만 done (R-2).
- **CLOSE 마지막 행 / verify 훅 / owner 블록과의 순서**: 기존 owner 결정 블록(`state_tool.py:933-948`)·`is_close_last` 판정(`state_tool.py:956-963`)·TEST verify 훅(`state_tool.py:972-981`)·decision 로그(`state_tool.py:983-1000`)는 **status 분기 이후** 그대로 둔다. 단 `is_close_last`의 done 전환과 `_mark_step_done=False`(in_progress) 충돌 방지: `is_close_last` 블록은 `row["status"]=="done"`일 때만 current_status=done 처리하도록 가드 추가 (in_progress면 스킵).

> [MUST] in_progress로 남긴 행은 current_status=done 전환에서 제외한다 — CLOSE 마지막 행이 다중 Step이고 N<M이면 태스크가 done으로 오판되면 안 된다 (`state_tool.py:956-963` 보강).

#### 3.2.3 ②단계 전환 가드 — 기존 guard 재사용 (신규 코드 없음)

- R-1이 N<M 행을 in_progress로 유지하면, 다음 단계 행 advance/mark 시 `check_stage_transition_guard`가 그 in_progress 행을 incomplete로 판정 → `stage_transition_violation` 자동 발생(`state_tool.py:377-385`). **별도 분기·신규 ERROR_CODE 불요** (→ D-3 §3.6 결론).
- 워커 경로(`scope="prior_stage_only"`): 다음 단계 워커가 자기 단계 행을 mark할 때, 직전 단계(EXECUTE)의 in_progress 행은 "앞 단계"이므로 prior_stage_only 검증 대상에 포함 → 차단됨.

#### 3.2.4 ③CLOSE 진입 가드 — 기존 guard 체인 재사용

- CLOSE 첫 행 mark/advance는 `check_stage_transition_guard`를 **먼저** 호출(`state_tool.py:912-916`/`852-856`)한다. 선행 EXECUTE 다중 Step 행이 in_progress(N<M)면 여기서 `stage_transition_violation`으로 차단 → close gate 도달 전 거부. 별도 보강 불요.
- close gate 자체(`check_close_gate`)는 사용자 확인 owner 검증만 담당(불변). 진행률 완료 검증은 stage-transition guard가 책임지는 구조 — 책임 분리 유지.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 기능(RED→GREEN) | `mark --row R --done --step 1/7` → 행 status=in_progress(done 아님), state.json 행에 `step:"1/7"` 저장. RED: 미구현 시 status=done으로 실패 |
| TS-002 | R-2 AC | 기능 | `mark --row R --done --step 7/7` → status=done, `step:"7/7"` 저장 |
| TS-003 | R-5 AC ② | 기능(가드) | EXECUTE 행 1/7(in_progress) 상태에서 다음 단계 행 mark/advance → `stage_transition_violation` exit 1 |
| TS-004 | R-5 AC ③ | 기능(가드) | 선행 EXECUTE 행 1/7 상태에서 CLOSE 첫 행 mark → 거부(stage_transition_violation, close 도달 전) |
| TS-005 | R-3/C-4 AC | 회귀(하위호환) | `--step` 없는 mark / 단일 Step / 비-EXECUTE 행 → 기존대로 즉시 done. `step` 키 없는 기존 state.json 정상 처리 |
| TS-006 | R-3 AC | 회귀(전체) | `unittest discover` 전체 165 + 신규 PASS. `test_error_codes_count` == 30 유지(신규 코드 0) |
| TS-007 | H-5 경계 | 기능(경계) | `--step "abc"`/`"3"`/`"0/0"` → None 처리 → 기존 done 경로(크래시 없음) |
| TS-008 | R-1 추가 | 기능 | 같은 행 `--step 1/7` → 2/7 → 7/7 순차 mark: 1·2에서 in_progress 유지, 7에서 done. `step` 필드 갱신 |

### 3.3 환경 변경

해당 없음 (Python 3 stdlib만 — `re` 기존 import `state_tool.py:20`).

### 3.4 배치/마이그레이션

- **install 재배포**: `opal/tools/state-tool/` 수정 후 `~/.opal/tools/state-tool/`로 재배포 (install 스크립트 경유). 직접 편집 금지.
- **state.json 마이그레이션 불요**: `step`은 옵셔널 신규 키 — 기존 state.json은 `row.get("step")` None으로 안전 처리. 역방향 호환(신규 도구가 구 state.json 읽기) 보장.

### 3.5 RED-first 자기적용 (C-3, D-3)

- [MUST] red-first.md §1(`opal/core/references/harness/red-first.md:23`): RED 단계에서 실패 테스트를 작성·실행하여 실패(exit≠0) 증거 기록 후 GREEN 진입. self-confirming 위험 영역(상태 전이 로직)이므로 강제 (→ D-3 §1.5).
- [MUST] red-first.md §2(`:52`): 작성자≠구현자 — RED 테스트는 opal-test-agent(mode: red)가 작성, GREEN 구현 워커와 분리.
- [MUST] red-first.md §3(`:58`): GREEN/fix 루핑 중 RED 테스트 파일 수정 금지.
- TEST-SCENARIO L1 시나리오(S-1~S-4)가 곧 R-1/R-5의 RED 테스트. `verify --red-check`로 RED 증거 게이트 적용 가능(red-first.md §1.5 state-tool 연동).
- RED 증거: 미구현 상태에서 TS-001(status=done으로 잘못 닫힘) / TS-003·004(차단 미발생) 테스트가 AssertionError로 실패하는 출력을 기록.

### 3.6 핵심 설계 결정 5종 (TASK 디스패치 요구 답변)

| # | 결정 사항 | 결론 | 근거 |
|---|----------|------|------|
| D-DEC-1 | 진행률 영속화 방식 | state.json 행에 `row["step"]="N/M"` 문자열 저장. 기존 행 스키마에 옵셔널 신규 키 추가, `row.get("step")` None-safe 소비로 하위 호환 | `state_tool.py:461-470` 행 스키마 / `216-221` 렌더가 step 미참조 (H-2) |
| D-DEC-2 | ①행 done 가드 (R-1) | `cmd_mark`에서 `_parse_step` → N<M+`--done`이면 status=in_progress 유지+step 저장, N==M에서만 done. **`--step` 미지정/비정형은 기존 즉시 done 유지** | `state_tool.py:928-931` 현 무조건 done / C-1·C-4 |
| D-DEC-3 | ②단계 전환 가드 (R-5) | **기존 `stage_transition_violation` 확장도 신규 코드도 불필요.** in_progress가 `_COMPLETE_STATUSES`에 미포함이므로 N<M 행은 기존 guard가 자동 차단 | `state_tool.py:338,377-385` (H-3 — 검증된 결론) |
| D-DEC-4 | ③CLOSE 진입 가드 (R-5) | 신규 코드 불요. mark/advance가 stage-transition guard를 close gate보다 먼저 호출하므로, 선행 in_progress 행이 close 도달 전 차단. close gate는 사용자 확인 검증만 유지(책임 분리) | `state_tool.py:912-919`/`852-859` 호출 순서 (H-4) |
| D-DEC-5 | RED-first 자기적용 | TEST-SCENARIO L1(S-1~S-4)을 RED로 선작성·실패 확인 후 GREEN 구현. 작성자≠구현자, 테스트 불변, `verify --red-check` ON | red-first.md §1/§1.5/§2/§3 (C-3, D-3) |

> **신규 ERROR_CODE 추가 여부 결론**: **추가하지 않는다.** ②③ 가드 모두 기존 `stage_transition_violation`이 in_progress 행을 미완으로 판정하여 자동 집행한다. ERROR_CODES 30종·`test_error_codes_count`(==30) 비파괴 (C-4, H-6).

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 (RED) | F-001 | 1 | opal-test-agent (mode: red) | 순차 | RED 테스트 작성·실패 확인 (작성자≠구현자) |
| 2 (GREEN) | F-001 | 2 | opal-task-agent | 순차 | state_tool.py 구현 (RED 통과시킴, 테스트 불변) |
| 3 (회귀) | F-001 | 3 | opal-test-agent | 순차 | 전체 unittest discover + 경계/하위호환 |
| 4 (배포) | F-001 | 4 | opal-task-agent | 순차 | install 재배포 |
| 5 (문서) | F-001 | 5 | PM 직접 | 순차 | @header·변경이력 반영 (R-4) |

### 4.2 실행 체크리스트

> 총 5개 Step | Phase 5개 | 실행 모드: 단순

#### Step 1: RED 테스트 작성 + 실패 확인 (R-1/R-2/R-5)
- [x] 완료
- **소속 기능**: F-001
- **영역**: 테스트
- **agent**: opal-test-agent (mode: red)
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: `TestMultiStepDoneGuard(BaseTestCase)` 신설. TS-001(N<M in_progress + step 저장), TS-002(N==M done), TS-003(다음 단계 차단), TS-004(CLOSE 차단), TS-008(순차 진행률) 케이스 작성. `make_args`의 기존 `step` 키(`test_state_tool.py:108`)·`_mark(step=)`(`test_state_tool.py:176`) 재사용. 미구현 상태에서 실행하여 실패(exit≠0) 증거 확보.
- **완료 기준**: 신규 테스트가 현재 코드에서 FAIL(AssertionError) — RED 증거 출력 기록. 작성자는 GREEN 구현자와 분리.
- **테스트**: TS-001~004, TS-008 (RED 단계)
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: GREEN 구현 — `cmd_mark` 분기 + `_parse_step` (R-1/R-2)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: `_parse_step` 헬퍼 추가(§3.2.1). `cmd_mark` 무조건 done 블록(`state_tool.py:928-931`)을 §3.2.2 분기로 교체 — N<M in_progress+step 저장, N==M done, 미지정/비정형 기존 done. `is_close_last` 블록(`state_tool.py:956-963`)에 `row["status"]=="done"` 가드 추가.
- **완료 기준**: Step 1 RED 테스트 전부 GREEN(PASS). RED 테스트 파일 미수정(불변성).
- **테스트**: TS-001~004, TS-008
- **실행 방법**: direct
- **의존**: Step 1

#### Step 3: 하위호환·경계·전체 회귀 검증 (R-3/C-4)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 테스트
- **agent**: opal-test-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: TS-005(--step 없는 mark/단일 Step/비-EXECUTE 즉시 done + step 없는 기존 state.json), TS-007(비정형 step 경계) 케이스 추가. 전체 `python3 -m unittest discover -s tests -p 'test_*.py'` 실행.
- **완료 기준**: 전체 165 + 신규 전부 PASS. `test_error_codes_count`==30 유지. 실행 출력(`Ran N tests ... OK`) 증거 기록.
- **테스트**: TS-005, TS-006, TS-007
- **실행 방법**: direct
- **의존**: Step 2

#### Step 4: install 재배포
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `~/.opal/tools/state-tool/` (install 경유)
- **작업 내용**: `opal/tools/state-tool/` 수정본을 install 스크립트로 `~/.opal/`에 재배포. 직접 편집 금지.
- **완료 기준**: `~/.opal/tools/state-tool/state_tool.py`가 수정본과 일치. 배포 후 smoke(`mark ... --step 1/2`) 1회 정상.
- **테스트**: 배포 후 smoke 1회
- **실행 방법**: direct
- **의존**: Step 3

#### Step 5: @header + 변경이력 반영 (R-4)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `opal/tools/state-tool/state_tool.py` (@header `state_tool.py:6`) + 태스크 DONE.md 변경이력
- **작업 내용**: @header description에 017 가드(다중 Step 조기 done 차단 + step 영속화) 1줄 추가. 변경이력에 017 반영.
- **완료 기준**: @header에 017 내용 명시, 변경이력 추적 가능.
- **테스트**: 산출물 검사
- **실행 방법**: direct
- **의존**: Step 2 (코드 변경 후)

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | RED→GREEN 순서 강제 (red-first.md §1). 작성자≠구현자 분리 |
| Step 2 → Step 3 | 구현 후 회귀 검증 |
| Step 3 → Step 4 | 회귀 통과 후 배포 |
| Step 2 → Step 5 | 코드 변경 후 @header/이력 갱신 (Step 3·4와 병렬 가능하나 단순 모드라 순차) |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | N<M done 차단 + 진행률 저장 | TS-001 | status=in_progress, `step:"1/7"` 저장 |
| F-001 | N==M done | TS-002 | status=done, `step:"7/7"` |
| F-001 | 단계 전환 미완 거부 | TS-003 | stage_transition_violation exit 1 |
| F-001 | CLOSE 진입 미완 거부 | TS-004 | 거부(stage_transition_violation) |
| F-001 | 하위호환(--step 없는 mark) | TS-005 | 기존대로 즉시 done, step 없는 state.json 정상 |
| F-001 | 전체 회귀 | TS-006 | 165+신규 PASS, error_codes==30 |

### 5.2 회귀 테스트

- [ ] `python3 -m unittest discover -s tests -p 'test_*.py'` 전체 PASS (기존 165 비파괴)
- [ ] `test_error_codes_count`==30 유지 (신규 ERROR_CODE 0)
- [ ] `--step` 미지정 mark·단일 Step·비-EXECUTE 행 동작 불변
- [ ] `step` 키 없는 기존 state.json에서 mark/show/validate 정상

### 5.3 코드/문서 품질

- [ ] T-11 준수 — 표준 라이브러리만 (`re` 기존 import)
- [ ] @header 017 갱신 + 변경이력 기록 (R-4)
- [ ] `row.get("step")` None-safe 접근 (하위 호환)

### 5.4 보안

- [ ] state.json/STATE.md에 시크릿·토큰 미포함 (해당 없음 — 상태 메타만)
- [ ] `~/.opal/` 직접 편집 없음 — install 경유 배포 (배포 경계 준수)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 5개 | 단순 |
| 변경 파일 수 | 2개 (state_tool.py, test_state_tool.py) | 단순 |
| 모듈 범위 | 단일 모듈 (state-tool) | 단순 |
| 작업 유형 | 버그/가드 수정 | 단순 |
| 외부 의존성 | 없음 (stdlib) | 단순 |
| **실행 모드** | **단순** | |

> 단순 모드 → 실행 아키텍처(§7) 생략. 단, RED-first 자기적용으로 Step 1(작성자)≠Step 2(구현자) 분리는 유지.

---

## 7. 실행 아키텍처

해당 없음 (단순 모드).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 | Python 3 stdlib (`argparse`/`re`/`unittest`) | trailofbits/modern-python (참고 — stdlib 한정이라 적용 최소) |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 외부 라이브러리 없음 — stdlib만, MCP 불요 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | cmd_mark(`:878`)·--step(`:1557`)·done 분기(`:928-931`)·행 스키마(`:461`)·_COMPLETE_STATUSES(`:338`)·ERROR_CODES(`:68`) |
| D-2 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | make_args step 키(`:108`)·_mark(`:176`)·TestStageTransitionGuard(`:1996`)·error_codes_count(`:1740`) |
| D-3 | 설계 | RED-first SSOT | `opal/core/references/harness/red-first.md` | RED→GREEN(`:23`)·적용기준(`:27`)·작성자≠구현자(`:52`)·불변성(`:58`)·verify 연동(`:46`) |
| D-4 | 기획 | TASK.md | `tasks/017-260610-opds-state-tool-multistep-done-guard/TASK.md` | C-1~C-5 확정 방향, R-1~R-5 요구사항, 제약 |
| D-5 | 설계 | 프로젝트 AGENT/제약 | `.opal/AGENT.md` / TASK §제약 | `~/.opal/` 직접 편집 금지·STATE.md state-tool만·변경이력 |
| D-6 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | PLAN 인라인 인용 의무 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| H-1 | done 무조건 분기 교체가 단일 Step mark까지 영향 → 파이프라인 붕괴 | F-001 | P0 | `--step` 미지정/비정형은 기존 done 경로 그대로(C-4). 전체 165 회귀(TS-006) |
| H-2 | 신규 `step` 키가 render/validate/show 깨뜨림 | F-001 | P1 | `row.get("step")` None-safe만 소비, 렌더 미참조 확인. TS-005 step 없는 state.json |
| H-3 | in_progress가 guard에 의해 자동 차단 안 됨(가정 오류) | F-001 | P0 | in_progress ∉ _COMPLETE_STATUSES 코드 확인 완료(`:338`). TS-003로 실거부 증거 |
| H-4 | CLOSE 진입 차단이 close gate가 아닌 stage-transition guard 경유 | F-001 | P0 | 호출 순서(guard→close `:912-919`) 확인. TS-004로 검증 |
| H-5 | 비정형 `--step` 입력 크래시 | F-001 | P2 | `_parse_step`가 None 반환→기존 done. TS-007 경계 |
| H-6 | 신규 ERROR_CODE 추가로 count 30 깨짐 | F-001 | P1 | 신규 코드 0 (기존 guard 재사용). TS-006로 count==30 확인 |
