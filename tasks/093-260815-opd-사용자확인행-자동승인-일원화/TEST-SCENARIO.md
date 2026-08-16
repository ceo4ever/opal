# TEST SCENARIO: 파이프라인 사용자 확인 행 — 자동 승인 경로 일원화

> 작성일: 2026-08-15 | 상태: 작성 완료
> 작성자: 알투(PM) | PLAN.md 가설 표(H-1~H-9) + TASK.md 요구사항(F-1~F-6)·목표 문장·채택/잔존 기준 기반
> self-confirming 방지: PLAN 작성자(opal-plan-agent)와 다른 작성자가 수행

## 0. 트랙 판정

### 0.1 RED-first 트랙 — 영역별 분기

[MUST] `opal/core/references/harness/red-first.md` §1.5: "판단 주체: PM이 변경 영역으로 판단(TEST-SCENARIO 작성 시점). 모호하면 RED-first 기본(안전측)."

| 변경 영역 | 대상 | 분류 근거 (§1.5) | 트랙 |
|----------|------|-----------------|------|
| `opal/tools/state-tool/state_tool.py` | 판정 함수·자동 승인 훅·mark/advance 배선 | **비즈니스 로직** + **API 계약**(CLI 서브명령 계약·exit code·JSON 응답) | **RED-first 강제** |
| `opal/tools/state-tool/schema/state.schema.json` | `na` enum 존치(변경 금지 대상) | 변경 없음 — 회귀 검증만 | RED-first 강제(회귀) |
| `opal/core/references/opal-harness-agentic.md`, `opal-harness-semi-agentic.md` | 자동 승인 계약 서술 | **설정·문서** | 구현 후 검증 |
| `opal/skills/opal-pilot-*/SKILL.md` 9종 | `--auto-pass` 지시 문구 | **설정·문서** | 구현 후 검증 |
| `docs/CONVENTIONS.md` | 상태 계약 등재 | **설정·문서** | 구현 후 검증 |

- RED 대상 = §3의 **M1 시나리오 전건**(S-2~S-19). RED 작성 주체는 `opal-test-agent(mode: red)`이며 EXECUTE 구현 워커와 분리한다(red-first §2).
- 문서 영역(S-20~S-22)은 구현 후 grep 검증이므로 RED 대상이 아니다.

### 0.2 M2(E2E 자동화) 의무 트리거 — 면제 판정

[MUST] `test-scenario-guide.md` §Step 3-b: "변경 영역에 FE 화면/컴포넌트·인증/인가·외부 API 연동 중 하나라도 포함되면 해당 시나리오에 L2/M2를 의무로 포함한다."

| 의무 트리거 | 본 태스크 변경 영역 해당 여부 | 근거 |
|------------|------------------------------|------|
| FE 화면/컴포넌트 | **미해당** | 변경 파일에 `.tsx`/`.vue`/`dashboard/frontend` 0건 (PLAN §4.2 Step 1~20 대상 전수) |
| 인증/인가 | **미해당** | 토큰·세션·권한 코드 없음. `worker_scope_violation`은 CLI 내부 가드로 인증 체계가 아님 |
| 외부 API 연동 | **미해당** | `state_tool.py`는 표준 라이브러리 전용, 외부 호출 없음(`state_tool.py:6` 헤더) |
| API 엔드포인트(BE M2 트리거) | **미해당** | HTTP 엔드포인트 없음. CLI 서브명령이며 Swagger UI 부재 |

**판정: M2 면제.** 누락이 아니라 트리거 전건 미해당으로 면제한 것이며, 위 대조표가 그 근거다.

### 0.3 테스트 도구 (test-tool resolve 결과)

| tier × scope | 도구 |
|--------------|------|
| unit × be | **pytest** |
| unit × be (lint) | ruff |
| unit × be (typecheck) | mypy |
| integration × be | pytest (subprocess 실호출) |

[MUST] 전 시나리오의 실행 대상은 **worktree 소스**다 — `/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_093/opal/tools/state-tool/run.sh`. 전역 배포본(`~/.opal/tools/state-tool/run.sh`)을 검증에 사용하지 않는다(PLAN §4.1 검증 실행 규약).

---

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-002 훅 × `check_close_gate` | CLOSE 진입의 `owner=user` 요건(`state_tool.py:717-722`)이 훅에 의해 우회 | **P0** | L1 + L2 | S-6, S-7 |
| H-2 | F-002 훅 × 워커 스코프 | `worker_scope_violation` 권한 경계(`state_tool.py:1499-1509`) 우회 | **P0** | L1 + L2 | S-8, S-9 |
| H-3 | F-003 판정 함수 통합 | 모드×단계 자동 승인 경계 이동(ANALYSIS §A.2) | P1 | L1 | S-12, S-13, S-14 |
| H-4 | F-003 × `cmd_validate` | CLOSE 축 부재(`:1710-1732`)에 판정 함수 무분별 적용 시 기존 파일 오탐 | P1 | L1 + L2 | S-14, S-18 |
| H-5 | F-001 auto-na 제거 | 3개 빌더 init 결과 계약(`:824-829`, `:916-921`, `:1050-1055`)의 3모드 동형성 | P1 | L1 | S-3, S-4 |
| H-6 | F-001/F-002 × 기존 `na` 보유 파일 | `_COMPLETE_STATUSES`(`:456`)·`build_todo_mirror` na 필터(`:481`) 하위호환 | P1 | L2 | S-17, S-18 |
| H-7 | F-005 note 접두 멱등 | note 문자열 계약(`:1562-1567`) 변경 시 STATE.md 렌더 회귀 | P2 | L1 | S-15, S-16 |
| H-8 | F-002 훅 × 후속 가드 순서 | 훅 in-place mutate 후 후속 가드 실패 시 메모리·파일 오염(`:1531` 주석 계약) | P1 | L1 + L2 | S-10, S-11 |
| H-9 | F-006 문서 정합 | pilot·하네스의 CLOSE 첫 행 거부 지시(유지 대상)까지 훼손 | P2 | L1 | S-21, S-22 |

> 가설 9건 → 시나리오 22건 (가설 N건 → 시나리오 N건 이상 충족).

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

DB가 없는 CLI 도구이므로 "테이블"은 **파일 자원**으로 대체한다.

| 자원 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 파이프라인 스펙 | `opal/skills/opal-pilot-dev/references/pipeline.json` | opd 16행, `*.user_confirm` 5행 포함 | 레포 실파일 (읽기 전용) |
| 파이프라인 스펙(대조군) | `opal/skills/opal-pilot-project/references/pipeline.json` | opp 스펙 | 레포 실파일 (읽기 전용) |
| 인라인 스펙 | `--rows-spec` JSON 문자열 | TASK/ANALYSIS/PLAN/EXECUTE/CLOSE 5단계 최소 스펙 | 테스트 내 fixture 문자열 |
| 레거시 SKILL.md 스펙 | tmp `SKILL.md` (행 표 포함) | `build_rows_from_skill_md` 경로 검증용 | 테스트 내 fixture (`_make_skill_md` 기존 헬퍼 재사용) |
| 태스크 폴더 | `tmp_path/tasks/T93-fixture/` | 빈 디렉토리 → `init`으로 state.json·STATE.md 생성 | pytest `tmp_path` |
| 기존 `na` 보유 실파일 | `tasks/092-260815-opd-워크트리-작업공간-분리/state.json` | `사용자 확인` 5행 중 `na` 2행·`done/auto` 3행 보유 | 레포 실파일 → **tmp 복사본**에만 조작 |
| PM Gate 산출물 | `gate.artifacts`가 가리키는 `.md` 파일 | **의도적 부재**(H-8 실패 유도용) | 미생성 상태 유지 |
| 문서 원본 스냅샷 | 하네스 2종 + pilot 9종 + `docs/CONVENTIONS.md` | 변경 전 grep 결과 저장 | Step 18 착수 전 `grep -c` 출력 |

> [MUST] 원본 `tasks/092-*/state.json`은 **읽기 전용**이다. 어떤 시나리오도 원본을 수정하지 않는다.
> [MUST] 본 태스크(093)의 실제 `state.json`/`STATE.md`는 어떤 시나리오에서도 조작 대상이 아니다.

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | opd pipeline.json, 빈 tmp 태스크 폴더 | `init --mode agentic` → `advance`/`mark` 연쇄로 TASK→EXECUTE 관통 | state.json 재로드 — `*.user_confirm` 4행이 `done/auto/timestamp≠None`, EXECUTE 행 진입 성공 |
| S-2 | 변경된 `state_tool.py` | `grep -c "agentic auto-na at init"` | 결과 0 |
| S-3 | opd pipeline.json | 동일 스펙을 3모드로 각각 `init` | 3개 state.json의 `rows[]` 전 필드 diff 0 |
| S-4 | 인라인 스펙 + tmp SKILL.md | `--rows-spec` / `--rows-from *.md` 각각 `init --mode agentic` | 사용자 확인 행 `pending/⬜/PM/timestamp=None` |
| S-5 | agentic init 직후 state.json | 다음 단계 첫 행 `advance` | 앞 단계 user_confirm 행 `pending`→`done/auto`, `timestamp` None→값 |
| S-6 | agentic 파이프라인, TEST user_confirm `pending` | CLOSE 첫 행 `mark --done` | 차단(exit 1) + 파일 재로드 시 해당 행 **여전히 `pending`** |
| S-7 | 동일 상태 | CLOSE 첫 행 `mark --done --auto-pass` | `agentic_close_gate_requires_user` 거부 + 행 `pending` 유지 |
| S-8 | agentic 파이프라인, PLAN user_confirm `pending` | `mark --as-worker --worker-stage EXECUTE` | `stage_transition_violation` exit 1 + PLAN user_confirm `pending` 유지 |
| S-9 | 동일 상태 | 동일 호출 후 state.json 재로드 | 파일의 어떤 행도 mutate되지 않음(전후 바이트 동일) |
| S-10 | `gate.artifacts` 미존재 상태의 PM Gate 행 | 훅 통과 후 `mark` → `gate_artifact_missing` 실패 | 저장 파일의 user_confirm 행 `pending` 유지(미저장) |
| S-11 | 동일 | 실패 응답 JSON | `auto_approved` 필드가 없거나 빈 배열 |
| S-12 | semi-agentic 파이프라인 | `MODE_BOUNDARY_STAGES` 구간 진입 | `user_confirmation_required` 반환(자동 승인 안 함) |
| S-13 | semi-agentic 파이프라인 | EXECUTE 이후 구간 진입 | 자동 승인 발생(`done/auto`) |
| S-14 | 모드×단계 18셀 fixture | 각 셀의 `mark`/`validate` 호출 | 셀별 판정이 변경 전과 동일(에러 코드 문자열까지) |
| S-24 | interactive 파이프라인 | (a) 훅 경로 진입 / (b) PM 직접 `mark --auto-pass` | (a) `user_confirmation_required` 거부 / (b) **exit 0** 후 `validate`가 `auto_pass_in_interactive_mode` 1건 |
| S-25 | 변경된 `state_tool.py` | `MODE_BOUNDARY_STAGES` 참조 지점 grep | 판정 함수 내부 1곳으로 수렴(정의부 제외) |
| S-26 | agentic 파이프라인 | 훅이 승인을 수행한 성공 호출 | 응답 JSON `auto_approved` 배열에 승인된 row_id가 담김 |
| S-15 | 사용자 확인 행 `pending` | `mark --done --auto-pass --note "X"` 1회 | note == `agentic auto-pass: X` |
| S-16 | S-15 직후 상태 | 동일 명령 2회차 | note 문자열 **불변** + `ok:true` + 상태 미변경 |
| S-17 | 092 state.json tmp 복사본 | `validate` → `advance` → `mark --done` 3종 | 전부 exit 0, violations 0 |
| S-18 | CLOSE user_confirm가 `done/auto`인 state.json | `validate` | `violations_count == 0`(H-4) |
| S-19 | worktree 전체 | `pytest opal/tools/state-tool/tests/test_state_tool.py -q` | failed 0, 기존 케이스 수 감소 0 |
| S-20 | 변경 후 하네스 2종 | 자동 승인 계약 문구 grep | 신규 계약 서술 존재 + 일반 단계 `--auto-pass` PM 지시 0건 |
| S-21 | 변경 전/후 pilot 9종 | CLOSE 첫 행 거부 지시 문자열 grep 대조 | 변경 전후 **동일**(H-9) |
| S-22 | 변경 문서 전체 | `## 변경이력` 행 grep | 변경한 문서마다 `(093)` 포함 행 1건 추가 |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-2: auto-na 구형 잔존 0건 [채택/잔존]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-001 — 빌더 3곳의 auto-na 분기 삭제 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | Step 8 완료 후 worktree `state_tool.py` |
| 기대 결과 | `agentic auto-na at init` 문자열 grep 결과 **0건**. 3개 빌더 함수의 `mode` 파라미터 시그니처는 존치 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoNaRemoval::test_auto_na_marker_absent_in_source_T093_L1_F1a'` |
| 결과 | **Pass** |
| 상세 | `TestT093AutoNaRemoval::test_auto_na_marker_absent_in_source_T093_L1_F1a` → `1 passed`. worktree `state_tool.py`에서 `agentic auto-na at init` 문자열 grep 0건 확인. 3개 빌더의 `mode` 파라미터 시그니처는 존치. |

#### S-3: 3모드 init 결과 동형성 [채택 — F-1 AC(b) 직접 검증]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-001 — 전 모드 `pending/PM` 통일 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 동일 `--rows-from opal/skills/opal-pilot-dev/references/pipeline.json`을 `--mode interactive` / `semi-agentic` / `agentic`으로 각각 init |
| 기대 결과 | 3개 state.json의 `rows[]` 전 필드가 **완전 동일**(diff 0). 특히 `*.user_confirm` 5행이 세 모드 모두 `status=pending / status_label=⬜ / owner=PM / timestamp=None / note=None` |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoNaRemoval::test_three_modes_init_rows_identical_T093_L1_F1b'` |
| 결과 | **Pass** |
| 상세 | `test_three_modes_init_rows_identical_T093_L1_F1b` → `1 passed`. 실 `opal-pilot-dev/references/pipeline.json`을 interactive/semi-agentic/agentic 3모드로 init한 결과 `rows[]` 전 필드 diff 0. `*.user_confirm` 5행이 3모드 모두 `pending/⬜/PM/timestamp=None`. |

#### S-4: 빌더 3경로 전건 pending 초기화

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-001 — `build_rows_from_spec` / `build_rows_from_skill_md` / `build_rows_from_pipeline_json` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 세 입력 경로(`--rows-spec` 인라인 JSON / `--rows-from *.md` / `--rows-from *.json`)를 각각 `--mode agentic`으로 init |
| 기대 결과 | 세 경로 모두 사용자 확인 행이 `pending/⬜/PM`. 어느 한 경로만 고쳐도 나머지에서 실패 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoNaRemoval::test_all_three_builders_init_pending_T093_L1_F1b'` |
| 결과 | **Pass** |
| 상세 | `test_all_three_builders_init_pending_T093_L1_F1b` → `1 passed`. `build_rows_from_spec`(인라인 JSON)·`build_rows_from_skill_md`(*.md)·`build_rows_from_pipeline_json`(*.json) 3경로 전부 사용자 확인 행 `pending/⬜/PM`. |

#### S-5: 자동 승인 훅 발동 — 명시 호출 없이 승인 [신형 채택]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-8 |
| 대상 | F-002 — `auto_approve_prior_user_confirmations` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | agentic init 직후(사용자 확인 행 `pending`, `timestamp=None`) → ANALYSIS 사용자 확인 행을 `pending`으로 둔 채 PLAN 첫 행 `advance` 호출. **`--auto-pass`를 전달하지 않는다** |
| 기대 결과 | advance가 exit 0이고, ANALYSIS 사용자 확인 행이 `done / owner=auto / timestamp≠None`. note가 `auto-approved on PLAN entry` 형식(`agentic auto-pass:` 접두를 쓰지 않음) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveHook::test_hook_fires_without_auto_pass_flag_T093_L2_F2'` |
| 결과 | **Pass** |
| 상세 | `test_hook_fires_without_auto_pass_flag_T093_L2_F2` → `1 passed`. `--auto-pass` 미전달 상태에서 PLAN 첫 행 `advance`만으로 ANALYSIS 사용자 확인 행이 `done/owner=auto/timestamp≠None`으로 전이. note가 `auto-approved on <stage> entry` 형식(`agentic auto-pass:` 접두 미사용). |

#### S-7: CLOSE 첫 행 auto-pass 거부 불변 [경계/부정]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-002 훅 × `check_close_gate` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | agentic·semi-agentic 각각에서 CLOSE 첫 행에 `mark --done --auto-pass` |
| 기대 결과 | 두 모드 모두 `agentic_close_gate_requires_user`로 거부(exit 1). 에러 코드 문자열까지 대조 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveBoundary::test_close_first_row_auto_pass_denied_T093_L1_F3'` |
| 결과 | **Pass** |
| 상세 | `test_close_first_row_auto_pass_denied_T093_L1_F3` → `1 passed`. agentic·semi-agentic 두 모드 모두 CLOSE 첫 행 `mark --done --auto-pass`가 exit 1 + `agentic_close_gate_requires_user`로 거부. 에러 코드 문자열까지 대조 일치. |

#### S-11: 훅 거부 경로에서 응답 오염 없음

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | F-002 — 훅과 후속 가드의 순서 계약 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 훅 통과 후 `check_gate_artifacts`가 `gate_artifact_missing`으로 실패하는 입력 |
| 기대 결과 | 실패 응답 JSON에 `auto_approved` 필드가 없거나 빈 배열. 훅 함수가 `save_state_json`을 호출하지 않음 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093HookGuardOrder::test_failed_response_has_no_auto_approved_T093_L1_F2o'` |
| 결과 | **Pass** |
| 상세 | `test_failed_response_has_no_auto_approved_T093_L1_F2o` → `1 passed`. `gate_artifact_missing` 실패 응답 JSON에 `auto_approved` 필드 부재/빈 배열 확인. 훅이 `save_state_json`을 호출하지 않음. |

#### S-12: semi-agentic — 경계 단계 자동 승인 거부 [경계/부정]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-003 판정 + F-004 전용 에러 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | semi-agentic 파이프라인에서 `MODE_BOUNDARY_STAGES`(TASK/ANALYSIS/PLAN/TEST-SCENARIO 등) 소속 단계 진입 시 훅 발동 |
| 기대 결과 | 자동 승인이 일어나지 않고 `user_confirmation_required` 반환. 응답에 `row_id`·`stage`·`reason == "semi_agentic_pre_execute"`·`required_action` 포함 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveBoundary::test_semi_agentic_boundary_requires_user_T093_L1_F4'` |
| 결과 | **Pass** |
| 상세 | `test_semi_agentic_boundary_requires_user_T093_L1_F4` → `1 passed`. semi-agentic + `MODE_BOUNDARY_STAGES` 소속 단계에서 자동 승인 미발생, `user_confirmation_required` 반환. 응답에 `row_id`·`stage`·`reason == "semi_agentic_pre_execute"`·`required_action` 전부 포함. |

#### S-13: semi-agentic — EXECUTE 이후 자동 승인 허용

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-003 판정 경계 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | semi-agentic 파이프라인에서 `MODE_BOUNDARY_STAGES` 밖 단계(EXECUTE→TEST) 진입 |
| 기대 결과 | 자동 승인 발생(`done/auto/timestamp≠None`), exit 0 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveHook::test_semi_agentic_post_execute_auto_approved_T093_L1_F3'` |
| 결과 | **Pass** |
| 상세 | `test_semi_agentic_post_execute_auto_approved_T093_L1_F3` → `1 passed`. semi-agentic에서 `MODE_BOUNDARY_STAGES` 밖(EXECUTE→TEST) 진입 시 자동 승인 발생(`done/auto/timestamp≠None`), exit 0. |

#### S-14: 경계 불변 회귀표 — 모드×단계 전 셀 [경계/부정]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-4 |
| 대상 | F-003 — 두 축 합성(CLOSE 무조건 / `MODE_BOUNDARY_STAGES` semi-agentic 한정) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest, subTest 파라미터화)** |
| 조건 | PLAN §3.3.2 표 A(B-1~B-9) + 표 B(V-1~V-9) 18셀을 그대로 파라미터화 |
| 기대 결과 | 전 셀이 변경 전 판정과 동일. 특히 ①**B-7은 `close_gate_violation`**, **B-8·B-9는 `agentic_close_gate_requires_user`** — 에러 코드 문자열까지 대조(exit code만 비교 금지) ②**V-8·V-9는 `violations_count == 0`**(H-4 핵심) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveBoundary::test_boundary_table_a_mark_auto_pass_T093_L1_F3' 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveBoundary::test_boundary_table_b_validate_T093_L1_F3'` |
| 결과 | **Pass** |
| 상세 | `test_boundary_table_a_mark_auto_pass_T093_L1_F3` + `test_boundary_table_b_validate_T093_L1_F3` → 각 `1 passed`(subTest 파라미터화 18셀 전건 통과). B-7 `close_gate_violation`, B-8·B-9 `agentic_close_gate_requires_user` 에러 코드 문자열 대조 일치. V-8·V-9 `violations_count == 0` 확인(H-4 핵심). |

#### S-15: note 접두 1회 부여

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-005 — note 접두 멱등 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 사용자 확인 행에 `mark --done --auto-pass --note "PM 판단 근거"` 1회 |
| 기대 결과 | note == `agentic auto-pass: PM 판단 근거`. 접두 문자열 `agentic auto-pass` 자체는 변경되지 않음 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093MarkIdempotency::test_auto_pass_note_prefix_applied_once_T093_L1_F5'` |
| 결과 | **Pass** |
| 상세 | `test_auto_pass_note_prefix_applied_once_T093_L1_F5` → `1 passed`. `mark --done --auto-pass --note "PM 판단 근거"` 1회 후 note == `agentic auto-pass: PM 판단 근거`. 접두 문자열 자체 불변. |

#### S-16: 재-auto-pass no-op 멱등 [경계/부정]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-005 — 재호출 no-op |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | S-15 직후 동일 행에 동일 명령 2회차 호출. 추가로 (a) `owner=user`로 done인 행 (b) `--force` (c) `--action-step 1/3` 3종 대조군 |
| 기대 결과 | 2회차가 `ok:true`이고 note 문자열 **불변**(`agentic auto-pass:` 접두 1회). 접두 중첩 0건. 대조군 3종은 no-op에 삼켜지지 않고 기존 경로로 진행 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093MarkIdempotency::test_re_auto_pass_is_noop_T093_L1_F5' 'opal/tools/state-tool/tests/test_state_tool.py::TestT093MarkIdempotency::test_noop_control_groups_T093_L1_F5'` |
| 결과 | **Pass** |
| 상세 | `test_re_auto_pass_is_noop_T093_L1_F5` + `test_noop_control_groups_T093_L1_F5` → 각 `1 passed`. 2회차 호출이 `ok:true` + note 문자열 불변(접두 중첩 0건). 대조군 3종(`owner=user` done 행 / `--force` / `--action-step 1/3`)은 no-op에 삼켜지지 않고 기존 경로로 진행. |

#### S-18: CLOSE `done/auto` 보유 파일 validate 무위반

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-6 |
| 대상 | F-003 × `cmd_validate` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | CLOSE stage의 사용자 확인 행이 `done/auto`인 state.json fixture |
| 기대 결과 | `validate`가 `violations_count == 0`. 판정 함수 도입으로 신규 위반이 생기지 않음 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveBoundary::test_close_done_auto_validate_no_violation_T093_L2_F6a'` |
| 결과 | **Pass** |
| 상세 | `test_close_done_auto_validate_no_violation_T093_L2_F6a` → `1 passed`. CLOSE stage 사용자 확인 행이 `done/auto`인 state.json에 대해 `validate`가 `violations_count == 0`. 판정 함수 도입에 따른 신규 위반 0건. |

#### S-19: 전체 스위트 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-5, H-6, H-7 |
| 대상 | F-001~F-006 전체 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | worktree에서 전체 테스트 스위트 실행 |
| 기대 결과 | failed 0. 테스트 함수 총 개수가 착수 전 대비 **감소하지 않음**(삭제 0건 — DEC-F). 신규 스킵/xfail 발생 시 사유 기록 |
| 명시적 예외 1건 | [MUST] `TestVerify::test_verify_passes_own_test_scenario_md`는 **worktree 환경 의존 실패**로 예외 처리한다. 근거(PM 직접 실측): worktree에서는 실패하나 **허브 체크아웃에서는 `1 passed`**로 통과한다 — sparse-checkout `repos`에 `tasks/`가 없어 픽스처(`tasks/034-*/TEST-SCENARIO.md`)를 못 찾는 것이 유일 원인이며, 본 태스크 변경과 무관하다. 이 1건은 **이름을 명시한 예외**이며 "failed 0"의 묵시적 완화가 아니다. 해소는 092 worktree 축의 후속 과제로 남긴다 |
| 도구 | pytest |
| 실행 명령 | `cd /Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_093 && python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` |
| 결과 | **Pass (명시적 예외 1건)** |
| 상세 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` → **`1 failed, 314 passed, 65 subtests passed in 14.54s`**. 유일 실패는 §3 S-19에 사전 명시된 `TestVerify::test_verify_passes_own_test_scenario_md`이며, 실패 사유는 `AssertionError: unexpectedly None : 034 TEST-SCENARIO.md 파일이 없음` — worktree sparse-checkout에 `tasks/`가 없어 픽스처를 찾지 못한 **환경 의존 실패**로 본 태스크 변경과 무관(PM 실증: 허브 체크아웃에서는 통과). 그 외 실패 0건. **테스트 함수 수 291 → 315(+24)로 감소 0건**(DEC-F 충족). 이름이 사라진 2건(`test_init_agentic_auto_na_user_confirmation`·`test_rows_from_agentic_auto_na`)은 **삭제가 아니라 개명**으로, F-001이 제거한 구형 `na` 계약을 단언하던 테스트가 신규 계약 단언(`..._user_confirmation_pending`)으로 교체된 것이며 단언 수는 유지·강화됨(4→5). 신규 skip/xfail 0건(base 1건 = after 1건). |

#### S-20: 하네스 SSOT 자동 승인 계약 등재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | F-006 (b) — 하네스 2종 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest — grep 기반 산출물 검사)** |
| 조건 | Step 18 완료 후 `opal-harness-agentic.md`·`opal-harness-semi-agentic.md` |
| 기대 결과 | ①자동 승인 계약(`auto_approve_prior_user_confirmations`) 서술이 하네스 2종에 존재 ②일반 단계에 대한 "PM이 `--auto-pass`를 호출한다"류 지시 0건 ③semi-agentic 문서에 `user_confirmation_required` 구간 명시 |
| 도구 | pytest |
| 실행 명령 | `cd /Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_093 && grep -n "auto_approve_prior_user_confirmations\|user_confirmation_required\|MODE_BOUNDARY_STAGES" opal/core/references/opal-harness-agentic.md opal/core/references/opal-harness-semi-agentic.md` (①③ 확인) + `grep -rn -- "--auto-pass" opal/skills/*/SKILL.md opal/core/references/*.md \| grep -viE "close\|변경이력" \| grep -vE ":\| v[0-9]"` (② 확인 — PM 일반 단계 지시 0건) |
| 결과 | **Pass** |
| 상세 | ①③ grep 결과 — 하네스 2종에 `auto_approve_prior_user_confirmations` 계약 서술 존재(agentic:78, semi-agentic:51), semi-agentic 문서에 `MODE_BOUNDARY_STAGES` 9종 열거 + `user_confirmation_required` 거부 구간 명시(:55, :58). ② PM 일반 단계 `--auto-pass` 지시 **0건** — 잔존 grep 히트 3건은 전부 비지시문으로 확인: `opal-harness-agentic.md:78`은 "PM이 `--auto-pass`를 별도로 호출하지 **않는다**"는 부정문(신규 계약 서술), `opal-harness.md:33`은 "`--auto-pass` **우회 불가**" 서술, `tools.md:100`은 CLI 사용법 synopsis. 셋 다 PM에게 호출을 지시하는 문구가 아님. |

#### S-21: CLOSE 거부 지시 문자열 불변 [경계/부정]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | F-006 (b) — pilot 9종 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest — grep 전후 대조)** |
| 조건 | Step 18 착수 **전** ANALYSIS §A.6 "CLOSE 첫 행 거부 지시" 약 25지점의 grep 결과를 스냅샷으로 저장 → Step 19 완료 후 재실행 |
| 기대 결과 | 전후 grep 출력이 **완전 동일**. CLOSE 절차 서술이 1글자도 훼손되지 않음 |
| 도구 | pytest |
| 실행 명령 | `cd /Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_093 && P="agentic_close_gate_requires_user\|CLOSE 첫 행\|CLOSE 진입\|prev_user_row"` → **전**: `git grep -nE "$P" HEAD -- 'opal/skills/*.md' 'opal/core/references/*.md' 'docs/*.md' \| sed 's/^HEAD://;s/:[0-9]*:/:/' \| grep -vE '\| v[0-9]' \| sort > /tmp/h9_before.txt` → **후**: `grep -rnE "$P" opal/skills/ opal/core/references/ docs/ --include='*.md' \| sed 's/:[0-9]*:/:/' \| grep -vE '\| v[0-9]' \| sort > /tmp/h9_after.txt` → `diff /tmp/h9_before.txt /tmp/h9_after.txt` (줄번호 제거·정렬로 시프트 무관 대조, 신규 `## 변경이력` 행은 `grep -vE '\| v[0-9]'`로 제외) |
| 결과 | **Pass (판정 근거는 보정 명령 기준)** |
| 상세 | **주의 — 시나리오에 기재된 원본 명령은 무효 검사였다.** 원본 필터 `grep -vE '\| v[0-9]'`는 BRE에서 `:` **또는** ` v` 매칭 행을 제거하는데, `grep -rn` 출력은 모든 행이 `파일:내용` 형태라 **전 행이 제거**되어 `before=0 / after=0`의 공허한(vacuous) diff가 된다. 이를 그대로 Pass로 기록하면 무검증 통과다. 따라서 변경이력 행만 배제하는 올바른 필터(`grep -vE '\| v[0-9]'`)로 재실행: **`before=100 / after=100`, `diff` 출력 없음(완전 동일)**. CLOSE 첫 행 거부 지시(`agentic_close_gate_requires_user`·`CLOSE 첫 행`·`CLOSE 진입`·`prev_user_row`) 100지점이 1글자도 훼손되지 않음 — H-9 충족. **시나리오 명령 문구 자체는 후속 보정 대상**(§7 잔여 지적 참조). |

#### S-22: 변경이력 등재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | F-006 (b) — 변경 문서 전체 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest — 산출물 검사)** |
| 조건 | Step 18~20에서 변경한 문서 전체 |
| 기대 결과 | 변경한 문서마다 `## 변경이력` 표에 행 1건 추가. 일시 형식 `YYYY-MM-DD HH:mm`(KST), 변경내용에 `(093)` 포함 |
| 도구 | pytest |
| 실행 명령 | `cd /Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_093 && for f in $(git diff --name-only -- '*.md'); do printf '%-60s %s\n' "$f" "$(grep -cE '^\| v.* 2026-08-15 21:48 \|.*\(093\)' "$f")"; done` — 변경 문서 11종 전부 `1` 반환 |
| 결과 | **Pass** |
| 상세 | 변경된 `.md` 11종 전부 `1` 반환 — `docs/CONVENTIONS.md`, `opal-harness-agentic.md`, `opal-harness-semi-agentic.md`, pilot 8종(`dev`, `dev-short`, `dev-wireframe`, `gc`, `project`, `project-dev`, `project-loop`, `sdd`). 각 문서 `## 변경이력`에 `| v… | 2026-08-15 21:48 | …(093) |` 행 정확히 1건씩 추가. |

#### S-24: interactive — 경로 분리(DEC-A) 실측 [경계/부정]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-004 — DEC-A 경로 분리 (훅 경로는 차단, PM 명시 호출 경로는 현행 유지) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 동일 interactive 파이프라인에서 (a) 훅 경로 진입 (b) PM이 직접 `mark --done --auto-pass` 호출 |
| 기대 결과 | **(a)** 자동 승인이 일어나지 않고 `user_confirmation_required` 거부(`reason == "interactive_requires_user"`) **(b)** `mark`가 **exit 0으로 성공**하고(현행 동작 불변), 이어지는 `validate`가 `auto_pass_in_interactive_mode` 위반 **1건**을 방출 |
| 검증 강도 | [MUST] (b)를 차단으로 바꾸면 F-3 AC "경계 불변"이 깨진다 — 이 시나리오가 그 경계를 고정한다 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveBoundary::test_interactive_path_split_T093_L1_F4'` |
| 결과 | **Pass** |
| 상세 | `test_interactive_path_split_T093_L1_F4` → `1 passed`. (a) 훅 경로는 자동 승인 미발생 + `user_confirmation_required`(`reason == "interactive_requires_user"`) 거부. (b) PM 직접 `mark --done --auto-pass`는 **exit 0으로 성공**(현행 동작 불변)하고 후속 `validate`가 `auto_pass_in_interactive_mode` 위반 **정확히 1건** 방출 — DEC-A 경로 분리 경계 고정 확인. |

#### S-25: F-3 구조적 단일화 검증 [채택]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-003 — 판정 로직이 실제로 단일 함수로 수렴했는가 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest — grep 기반 구조 검사)** |
| 조건 | Step 3 완료 후 worktree `state_tool.py` |
| 기대 결과 | `MODE_BOUNDARY_STAGES` 참조가 **판정 함수 내부 1곳으로 수렴**(정의부 `:50-54` 제외). `cmd_mark`·`cmd_validate`가 직접 참조하지 않고 판정 함수를 호출 |
| 검증 강도 | [MUST] 행동 불변(S-14)만 검증하면 **판정 로직을 3곳에 복붙해도 PASS**한다 — 이 시나리오가 F-3의 "단일 판정" 목표 자체를 검증한다 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093SingleDecisionSource::test_mode_boundary_stages_single_reference_T093_L1_F3s' 'opal/tools/state-tool/tests/test_state_tool.py::TestT093SingleDecisionSource::test_decision_function_contract_T093_L1_F3s'` |
| 결과 | **Pass** |
| 상세 | `test_mode_boundary_stages_single_reference_T093_L1_F3s` + `test_decision_function_contract_T093_L1_F3s` → 각 `1 passed`. `MODE_BOUNDARY_STAGES` 참조가 판정 함수(`can_auto_approve_user_confirmation`) 내부 1곳으로 수렴(정의부 제외). `cmd_mark`·`cmd_validate`가 상수를 직접 참조하지 않고 판정 함수를 호출 — 복붙 3중화가 아닌 실제 구조적 단일화 확인. |

#### S-26: 성공 응답 `auto_approved` 긍정 검증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | F-002 — 관측 계약 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | agentic 파이프라인에서 훅이 실제로 승인을 수행한 성공 호출(`advance`/`mark` 양쪽) |
| 기대 결과 | 응답 JSON `auto_approved` 배열에 **승인된 row_id가 정확히 담김**. 승인이 0건인 호출에서는 빈 배열 또는 필드 부재 |
| 검증 강도 | S-11이 부정 경로(오염 없음)만 보므로, 긍정 경로 관측 계약은 이 시나리오가 담당한다 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveHook::test_auto_approved_payload_positive_T093_L1_F2o'` |
| 결과 | **Pass** |
| 상세 | `test_auto_approved_payload_positive_T093_L1_F2o` → `1 passed`. `advance`/`mark` 양 경로의 성공 응답 JSON `auto_approved` 배열에 승인된 row_id가 정확히 담김. 승인 0건 호출에서는 빈 배열/필드 부재 — 긍정 관측 계약 확인. |

### L2. 프로세스 통합 (자동, 실 파일 read→CUD→re-read)

> DB가 없는 CLI 도구이므로 L2의 "실 DB read→CUD→re-read"는 **worktree `run.sh` subprocess 실호출 → state.json 파일 재로드**로 치환한다. 메모리상 반환값만 보는 검증은 금지한다 — 파일 실측이 회귀 방지의 요체다.

#### S-1: 파이프라인 관통 — 훅이 실제로 접합되어 동작한다 [목표달성]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2, H-5, H-8 (통합) |
| 대상 | 태스크 목표 전체 — "다음 단계 진입만으로 사용자 확인 행이 자동 승인된다" |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + worktree `run.sh` subprocess 실호출)** |
| 조건 | 실 `opal/skills/opal-pilot-dev/references/pipeline.json`으로 tmp 태스크 폴더에 `init --mode agentic` → 이후 **PM이 실제 파이프라인에서 하는 것과 동일한 순서**로 `advance`/`mark`를 연쇄 호출하여 TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE까지 진행. 어느 호출에도 `--auto-pass`를 전달하지 않는다 |
| 기대 결과 | ①연쇄 호출이 전부 exit 0으로 EXECUTE 행 진입까지 도달 ②state.json 재로드 시 TASK·ANALYSIS·PLAN·TEST-SCENARIO의 `user_confirm` 4행이 전부 `done / owner=auto / timestamp≠None` ③`na` 상태 행 0건 ④각 승인의 `timestamp`가 **해당 단계 진입 호출 시각**과 일치 |
| timestamp 비교 기준 | [MUST] `state.json`의 `created_at`(init 시각)과 **다른 값**이어야 하며, 승인된 행의 `timestamp`가 그 행을 승인시킨 `advance` 호출 응답의 `timestamp` 필드와 **문자열 일치**해야 한다. 분 단위 해상도(`YYYY-MM-DD HH:mm`)로 인해 동일 분 내 실행 시 `created_at`과 값이 같아질 수 있으므로, **응답 `timestamp`와의 일치**를 1차 기준으로 삼고 `created_at` 대조는 보조로 둔다 |
| 검증 강도 | [MUST] **훅이 호출되지 않게 접합되어도 통과하는 시나리오가 되어서는 안 된다** — 훅 미배선 시 이 시나리오는 `stage_transition_violation`으로 실패해야 한다(070 동형 공백 방지) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveHook::test_pipeline_traversal_auto_approves_T093_L2_GOAL'` |
| 결과 | **Pass** |
| 상세 | `test_pipeline_traversal_auto_approves_T093_L2_GOAL` → `1 passed`. 실 `opal-pilot-dev/references/pipeline.json`으로 agentic init 후 **`--auto-pass` 미전달**로 TASK→ANALYSIS→PLAN→TEST-SCENARIO→EXECUTE 연쇄 호출 전부 exit 0 도달. state.json 재로드 시 `user_confirm` 4행 전부 `done/owner=auto/timestamp≠None`, `na` 상태 행 0건. 승인 행 `timestamp`가 해당 승인을 유발한 `advance` 응답 `timestamp`와 문자열 일치. 검증 강도 요건대로 훅 미배선 시 `stage_transition_violation`으로 실패하는 구조 — 070 동형 공백 아님. |

#### S-6: CLOSE 진입 시 자동 승인 미발생 — 파일 실측 [경계/부정]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-002 — CLOSE 구조적 3중 방어 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + subprocess 실호출)** |
| 조건 | agentic 파이프라인에서 TEST 단계 `user_confirm` 행을 `pending`으로 둔 채 CLOSE 첫 행 `mark --done` 호출 |
| 기대 결과 | ①차단(exit 1) ②**state.json 파일 재로드** 시 TEST `user_confirm` 행이 **여전히 `pending`** — 훅이 CLOSE 직전 행을 `owner=auto`로 마킹하지 않음 ③이후 해당 행을 `--owner user`로 mark하면 CLOSE 진입이 정상 통과 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveBoundary::test_close_entry_does_not_auto_approve_T093_L2_GOAL'` |
| 결과 | **Pass** |
| 상세 | `test_close_entry_does_not_auto_approve_T093_L2_GOAL` → `1 passed`. ①CLOSE 첫 행 `mark --done` exit 1 차단 ②**state.json 파일 재로드** 시 TEST `user_confirm` 행이 여전히 `pending`(훅이 CLOSE 직전 행을 `owner=auto`로 마킹하지 않음) ③해당 행을 `--owner user`로 mark 후 CLOSE 진입 정상 통과. |

#### S-8: 워커 경로 자동 승인 비활성 [경계/부정]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-002 — `as_worker` 훅 전면 비활성 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + subprocess 실호출)** |
| 조건 | agentic 파이프라인에서 PLAN `user_confirm` 행을 `pending`으로 둔 채 `mark --as-worker --worker-stage EXECUTE`로 EXECUTE 행 mark |
| 기대 결과 | ①`stage_transition_violation` exit 1 ②state.json 재로드 시 PLAN `user_confirm` 행 `pending` 유지 — 워커가 자기 단계 밖 행을 실질 갱신하지 못함 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveBoundary::test_worker_path_hook_disabled_T093_L2_GOAL'` |
| 결과 | **Pass** |
| 상세 | `test_worker_path_hook_disabled_T093_L2_GOAL` → `1 passed`. `mark --as-worker --worker-stage EXECUTE` 호출이 `stage_transition_violation` exit 1로 차단되고, state.json 재로드 시 PLAN `user_confirm` 행 `pending` 유지 — 워커가 자기 단계 밖 행을 실질 갱신하지 못함. |

#### S-9: 워커 호출 후 파일 무변경 (바이트 대조)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-8 |
| 대상 | F-002 — 워커 경로 mutate 0건 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + subprocess 실호출)** |
| 조건 | S-8과 동일 호출. 호출 전 state.json 바이트를 저장 |
| 기대 결과 | 호출 후 state.json 바이트가 호출 전과 **완전 동일**(`updated_at` 포함 무변경) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093AutoApproveBoundary::test_worker_path_leaves_file_byte_identical_T093_L2_GOAL'` |
| 결과 | **Pass** |
| 상세 | `test_worker_path_leaves_file_byte_identical_T093_L2_GOAL` → `1 passed`. 워커 경로 호출 전후 state.json 바이트가 완전 동일(`updated_at` 포함 무변경) — 훅이 워커 경로에서 전면 no-op임을 파일 실측으로 확인. |

#### S-10: 후속 가드 실패 시 파일 미저장

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | F-002 — 훅 → 가드 순서, 부분 상태 변경 배제 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + subprocess 실호출)** |
| 조건 | `gate.artifacts`가 가리키는 산출물을 의도적으로 만들지 않은 상태에서 PM Gate 행 `mark --done` |
| 기대 결과 | ①`gate_artifact_missing` exit 1 ②**저장된 파일**의 앞 단계 `user_confirm` 행이 여전히 `pending` — 훅이 메모리에서 승인했더라도 파일에 반영되지 않음 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093HookGuardOrder::test_guard_failure_leaves_file_unsaved_T093_L2_F2'` |
| 결과 | **Pass** |
| 상세 | `test_guard_failure_leaves_file_unsaved_T093_L2_F2` → `1 passed`. `gate.artifacts` 산출물 부재 상태에서 PM Gate 행 `mark --done` → ①`gate_artifact_missing` exit 1 ②**저장된 파일**의 앞 단계 `user_confirm` 행이 여전히 `pending`. 훅이 메모리에서 승인했더라도 파일 미반영 — 부분 상태 변경 배제 확인. |

#### S-17: 기존 `na` 보유 실파일 하위호환 [하위호환]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | F-006 (a) — `na` 하위호환 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + subprocess 실호출)** |
| 조건 | `tasks/092-260815-opd-워크트리-작업공간-분리/state.json`을 **tmp에 복사**한 뒤 worktree `run.sh`로 `validate` → `advance` → `mark --done` 3종 실행 |
| 기대 결과 | 3종 모두 exit 0, violations 0. `na` 행이 `_COMPLETE_STATUSES`로 완료 인정되어 `check_stage_transition_guard`를 통과 |
| 제약 | [MUST] 원본 파일은 읽기만 한다. 수정 0건 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q 'opal/tools/state-tool/tests/test_state_tool.py::TestT093NaBackwardCompat::test_existing_na_state_json_still_operable_T093_L2_F6a'` |
| 결과 | **Pass** |
| 상세 | `test_existing_na_state_json_still_operable_T093_L2_F6a` → `1 passed`. 실 `tasks/092-260815-opd-워크트리-작업공간-분리/state.json`의 **tmp 복사본**에 worktree `run.sh`로 `validate`→`advance`→`mark --done` 3종 실행, 전부 exit 0 / violations 0. `na` 행이 `_COMPLETE_STATUSES`로 완료 인정되어 `check_stage_transition_guard` 통과. **원본 파일 수정 0건 검증**: `git status` 무변경 + mtime `Aug 15 19:52`(테스트 실행 이전) 유지. |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-23: 전역 배포 후 실파이프라인 동작 확인 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-5 |
| 대상 | 전역 배포본(`~/.opal/tools/state-tool/`)의 실동작 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)**. 자동화 불가 — `install-mac.sh`가 `$USER_HOME/.opal` 단일 타겟이라 배포 시 실행 중인 세션의 파이프라인이 교체된다 |
| 조건 | CLOSE 이후 캡틴이 `scripts/install-mac.sh`를 수동 실행하여 전역 배포 |
| 기대 결과 | 배포 후 신규 태스크를 `--agentic`으로 개설했을 때 ①사용자 확인 행이 `pending/PM`으로 생성되고 ②다음 단계 진입 시 `done/auto`로 자동 승인되며 ③CLOSE 진입은 여전히 캡틴 승인을 요구한다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | _{캡틴 확인 대기 — CLOSE 이후 수동 실행}_ |
| 상세 | _{캡틴 확인 대기 — CLOSE 이후 수동 실행}_ — L3 [SUPERVISOR] 마커 시나리오로 opal-test-agent가 실행하지 않았다. 전역 배포(`scripts/install-mac.sh`)는 `$USER_HOME/.opal` 단일 타겟이라 배포 시 실행 중 세션의 파이프라인이 교체되므로 자동화 불가. 미실행이며 Pass로 계상하지 않는다. |

**PM 표준 요청 양식** (TEST 단계에서 사용):

```
캡틴, [시나리오 S-23]은 사용자 협업 검증이 필요합니다.
요청 내용: CLOSE 완료 후 `scripts/install-mac.sh`로 전역 배포한 뒤,
          신규 태스크를 `--agentic`으로 개설해 사용자 확인 행의 초기 상태와
          다음 단계 진입 시 자동 승인 여부를 확인해주세요.
기대 결과: 초기 `pending/PM` → 다음 단계 진입 시 `done/auto`,
          CLOSE 진입은 여전히 캡틴 승인 요구.
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| F-1 AC (a) 구형 잔존 0 | H-5 | L1 | S-2 | `tests/test_state_tool.py:[T093/L1-F1a]` | 교체형 — 잔존 검증 |
| F-1 AC (b) 신형 채택 | H-5 | L1 | S-3, S-4 | `tests/test_state_tool.py:[T093/L1-F1b]` | 교체형 — 3모드 diff 0이 유일한 직접 검증 |
| F-2 AC 훅 자동 승인 | H-5, H-8 | L1 + L2 | S-5, **S-1** | `tests/test_state_tool.py:[T093/L2-F2]` | S-1이 목표달성 관통 |
| F-3 AC 경계 불변 | H-3, H-4 | L1 | S-12, S-13, S-14 | `tests/test_state_tool.py:[T093/L1-F3]` | 18셀 테이블 드리븐 |
| F-3 AC 단일 판정(구조) | H-3 | L1 | **S-25** | `tests/test_state_tool.py:[T093/L1-F3s]` | 행동 불변만으로는 복붙 통과 — 구조 검증 |
| F-4 AC 전용 에러 | H-3 | L1 | S-12, **S-24** | `tests/test_state_tool.py:[T093/L1-F4]` | S-24가 DEC-A 경로 분리 실측 |
| F-2 AC 관측 계약 | H-8 | L1 | **S-26**, S-11 | `tests/test_state_tool.py:[T093/L1-F2o]` | 긍정(S-26) + 부정(S-11) |
| F-5 AC 멱등성 | H-7 | L1 | S-15, S-16 | `tests/test_state_tool.py:[T093/L1-F5]` | 대조군 3종 포함 |
| F-6 AC (a) `na` 하위호환 | H-6 | L2 | S-17, S-18, S-19 | `tests/test_state_tool.py:[T093/L2-F6a]` | 092 실파일 |
| F-6 AC (b) 문서 정합 | H-9 | L1 | S-20, S-21, S-22 | `tests/test_state_tool.py:[T093/L1-F6b]` | grep 전후 대조 |
| TASK 완료기준 ③ | H-1, H-2 | L2 | S-1, S-6, S-8, S-9 | `tests/test_state_tool.py:[T093/L2-GOAL]` | 자동 승인 + 우회 불가 |
| TASK 완료기준 ⑦ | 전건 | L1 | S-19 | `tests/test_state_tool.py` 전체 | 회귀 |
| 전역 배포 실동작 | H-1, H-5 | L3 | S-23 | (수동) | CLOSE 이후 캡틴 |

**매핑 완전성**: H-1~H-9 전건이 시나리오에 연결됨. S-1~S-23 전건이 AC 또는 완료기준에 연결됨. 미매핑 0건.

---

## 5. 코드 품질

> 도구 조달 경위: `ruff`·`mypy` 모두 현재 파이썬 환경(`miniconda3`)에 **미설치**였고 레포에도 `pyproject.toml`/`ruff.toml` 등 설정 파일이 없다(= 본 프로젝트의 상시 툴체인이 아님). `/opt/homebrew/bin/uvx`(uv 0.10.8)로 격리 실행하여 **묵시적 통과로 만들지 않고 실제 수치를 확보**했다. 판정은 절대 건수가 아니라 **HEAD 기준선 대비 증감(delta)**으로 한다 — 기준선 자체가 이미 위반을 다수 보유하므로 절대 0을 요구하면 본 태스크와 무관한 부채를 전가하게 된다. 기준선은 `git show HEAD:<file>`로 추출해 동일 조건에서 측정했다.

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff 0.16.3 | **Pass (조건부 — 프로덕션 개선, 테스트 증가)** | 전체 `82 → 104`(+22). **파일별 분해가 판정의 핵심**: `state_tool.py`(프로덕션) **24 → 22 (−2, 신규 위반 0건 · 순개선)**, `tests/test_state_tool.py` **62 → 86 (+24)**. 증가분은 전량 신규 테스트 코드의 **비기능 스타일 규칙** — `RUF059`(미사용 튜플 언패킹 변수, 20→40) + `RUF012`(가변 클래스 속성 `ClassVar` 미표기, 6→10)이며, 픽스처 dict와 `code, stdout, stderr, data` 4튜플 언패킹 관용구에서 발생. 기능·정확성 규칙(`F`/`E`/`S`) 신규 0건이고 `SIM102`는 2→0으로 감소. 프로덕션 코드에 신규 린트 위반이 없으므로 Pass로 판정하되, 테스트 코드 `RUF059`/`RUF012` 정리는 비차단 후속 권고로 남긴다. |
| 2 | 타입 체크 | mypy 1.x (`--ignore-missing-imports`) | **Pass** | `opal/tools/state-tool/state_tool.py` → **`Success: no issues found in 1 source file`**. 본 태스크가 추가한 판정 함수(`can_auto_approve_user_confirmation`)·훅(`auto_approve_prior_user_confirmations`) 포함 타입 오류 0건. |
| 3 | 포맷터 | ruff format | **Skip (기준선 동일 — 회귀 0)** | `ruff format --check` 결과 변경 후 `2 files would be reformatted`, **기준선(HEAD)에서도 동일하게 `2 files would be reformatted`**. 즉 두 파일 모두 착수 전부터 ruff 포맷 규약을 따르지 않았고(레포가 ruff format을 채택한 적 없음) 본 태스크로 인한 **포맷 회귀는 0건**이다. 레포 컨벤션이 아닌 도구를 소급 적용해 대량 재포맷하는 것은 TEST 단계 권한 밖이므로 미적용 — 묵시적 통과가 아니라 **기준선 대비 무변화로 Skip** 처리한다. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **Pass** | 변경 파일 2종(`state_tool.py`, `tests/test_state_tool.py`)에 대해 `api_key`·`secret`·`password`·`token`·`credential`·`private_key`·`aws_access`·`bearer` 뒤에 12자 이상 값이 대입되는 패턴을 정규식 스캔 → **0건**(grep exit 1). 본 태스크 변경분은 상태 판정 로직·문서로 자격증명을 다루지 않으며, `state_tool.py`는 표준 라이브러리 전용으로 외부 호출·인증 경로가 없다. |
| 2 | .gitignore 확인 | **Pass** | `.gitignore` 존재. `__pycache__/`(10행)·`.env`(25행) 등재 확인 — 테스트 실행 산출물과 환경변수 파일이 커밋 대상에서 제외된다. 본 태스크는 테스트 픽스처를 전부 `tempfile.mkdtemp()` 하위에만 생성(`_T093Base.setUp`/`tearDown`)하므로 레포 내 잔여 산출물이 없고, `git status`에도 신규 untracked 파일이 나타나지 않았다. |

## 7. 판정

**All Pass — 실행 대상 25건(S-1~S-22, S-24~S-26) 전건 Pass, 핵심 기능·경계·보안 Fail 0건. S-23은 L3 [SUPERVISOR]로 미실행(Skip, CLOSE 이후 캡틴 수동 확인 대기)이며 Pass로 계상하지 않는다.**

### 집계

| 구분 | 건수 | 내역 |
|------|------|------|
| Pass | **25** | L1 19건(S-2~S-5, S-7, S-11~S-16, S-18~S-22, S-24~S-26) + L2 6건(S-1, S-6, S-8~S-10, S-17) |
| Fail | **0** | — |
| Skip | **1** | S-23 (L3 [SUPERVISOR] — 전역 배포 필요, 자동화 불가) |

### 판정 근거

1. **목표달성 관통(S-1) Pass** — `--auto-pass` 없이 단계 진입만으로 사용자 확인 4행이 `done/auto`로 자동 승인됨을 **파일 재로드로 실측**. TASK 완료기준 ③ 충족.
2. **P0 우회 경로 전건 차단** — H-1(CLOSE 게이트: S-6·S-7)·H-2(워커 스코프: S-8·S-9) 모두 차단 + **파일 무변경(바이트 동일)** 확인. 훅이 권한 경계를 뚫지 않는다.
3. **경계 불변** — 18셀 회귀표(S-14)가 에러 코드 문자열까지 변경 전과 동일. S-24가 DEC-A 경로 분리(interactive 훅 차단 / PM 직접 호출 exit 0)를 고정.
4. **구조 목표 달성** — S-25로 `MODE_BOUNDARY_STAGES` 판정이 단일 함수로 수렴함을 확인(행동 불변만으로는 복붙 통과 가능한 공백을 메움).
5. **하위호환** — 092 실파일 `na` 보유 state.json이 3종 명령 전부 exit 0(S-17), CLOSE `done/auto` validate 무위반(S-18).
6. **회귀** — 전체 스위트 `1 failed, 314 passed, 65 subtests passed`. 유일 실패는 사전 명시된 환경 의존 예외 1건이며 **이름을 특정한 예외**로, "failed 0"의 묵시적 완화가 아니다. 테스트 함수 291→315로 **삭제 0건**(DEC-F).
7. **품질·보안** — mypy 0 오류, 프로덕션 린트 순개선(24→22), 시크릿 0건, `.gitignore` 정상.

### TEST 단계에서 확인하지 못한 것 (판정 유보 사항)

- **S-23(전역 배포 실동작)** — 미실행. 본 판정은 **worktree 소스 기준**이며 전역 배포본(`~/.opal/tools/state-tool/`)의 실동작은 검증 범위 밖이다. CLOSE 이후 캡틴 확인 필요.

### TEST 단계에서 발견한 비차단 지적 (수정하지 않음 — PM 판단 대기)

1. **S-21 실행 명령이 공허한(vacuous) 검사였다** — 기재된 필터 `grep -vE '\| v[0-9]'`는 BRE 대체 연산으로 `:` 포함 행 전체를 제거하여 `grep -rn` 출력을 전멸시킨다(`before=0 / after=0`). 그대로 수행하면 **아무것도 대조하지 않고 Pass**가 된다. 올바른 필터(`grep -vE '\| v[0-9]'`)로 재실행해 `before=100 / after=100 / diff 없음`의 실질 증거를 확보했으므로 **S-21의 검증 목적(H-9)은 충족**되나, **TEST-SCENARIO 문서의 명령 문구 자체는 후속 보정 대상**이다.
2. **테스트 코드 린트 부채 +24건** — `RUF059`(미사용 언패킹 변수)·`RUF012`(`ClassVar` 미표기). 기능 영향 없음. 레포에 ruff 설정이 없어 강제 규약도 아니므로 비차단.
3. **`ruff format` 기준선 미준수 2파일** — 착수 전부터 존재하는 부채(회귀 0). 레포 차원의 포맷터 채택 여부는 별도 의사결정 사안.

> [MUST] 준수 확인: `state_tool.py` 수정 0건 · 테스트 코드 수정 0건(통과 목적 개변 없음) · `mock`/`patch`/`MagicMock` 사용 0건(T093 전 클래스가 `_run070` → `subprocess.run(["bash", run.sh])` 실호출 기반) · 검증 대상은 전건 **worktree 소스**(`_TOOL_DIR = __file__.parent.parent`) · 원본 `tasks/092-*/state.json` 무변경(mtime `Aug 15 19:52` 유지) · 093 `state.json`/`STATE.md` 손편집 0건.

### PM Gate 체크 (7대 강제 룰)

- [x] `mock`/`patch`/`MagicMock` 등 시나리오 본문에 부재 (grep 확인 — 시나리오 본문 0건. 본 체크리스트 항목명 자체는 백틱 인라인으로 격리)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 (9행 × 4열, 빈 칸 0)
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 (S-1~S-22, 22행)
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 0건)
- [x] L1/L2/L3 계층 명시 (S-1~S-23 전건)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-23)
- [x] 리스크 가설 표(§1) H-1~H-9와 시나리오 S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] **M2 의무 트리거** — §0.2 대조표로 트리거 4종 전건 미해당 확인 → **면제**(누락 아님)
- [x] **목표 커버** — TASK.md F-1~F-6 전건이 §4에 커버됨. 목표달성 시나리오 **S-1**(파이프라인 관통)이 §3 L2에 존재하며, 훅 미배선 시 실패하도록 검증 강도를 명시함

### 자기 인증 (실측 수치)

| 항목 | 수치 |
|------|------|
| 리스크 가설 | H-1~H-9 (9건) |
| 사전 조건 자원 | 9종 |
| 데이터 흐름 행 | S-1~S-26 (25행 — S-23은 L3 수동이라 데이터 흐름 비대상) |
| 시나리오 | S-1~S-26 (26건 — L1 19 / L2 6 / L3 1) |
| AC 매핑 행 | 14행 |

### 게이트 판정 후 편집 명시 (iteration 1)

> 목표-커버 게이트 iteration 1은 **결정론 exit 0 + Evaluator `verdict: pass`(goal 2 / adoption 2 / boundary 2, 평균 2.0)** 두 증거로 통과했다. 판정 시점 산출물은 **23건**이며, 이후 Evaluator가 비차단 권고로 남긴 A-1~A-4를 PM이 반영해 **26건**이 되었다.
>
> 편집 성격: **전부 additive** — 시나리오 삭제 0건, 기대 결과 약화 0건. 추가분은 S-24(interactive 경로 분리 실측) · S-25(F-3 구조적 단일화) · S-26(`auto_approved` 긍정 검증)이며, S-1에 timestamp 비교 기준을 명문화하고 §2.2의 S-14 행을 §3 본문(경계 불변 회귀표)과 일치시켰다.
>
> Producer가 판단축을 자가 채점해 pass를 만든 것이 아니며, 반영 후 `scenario-coverage-check`를 **재실행해 exit 0을 재확인**했다.
