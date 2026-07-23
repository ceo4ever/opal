# TEST SCENARIO: 파이프라인 todo 미러 hook 강제 자동화

> 작성일: 2026-07-23 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반 (self-confirming 방지 — PLAN 워커와 다른 작성자)

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 ok() 출력 계약 | todo_mirror 키 신설로 응답 dict 비교 소비자/테스트 파손 | P1 | L1 | S-3 |
| H-2 | F-001 파생 규칙 | na/failed 상태 집계 오판(미착수 단계 in_progress 오표시) | P1 | L1 | S-1 |
| H-3 | F-001 영속 경계 | todo_mirror를 state.json에 저장 시 schema additionalProperties:false 위반 | P1 | L1 | S-2 |
| **H-4** | **F-002 hook→도구 유발** | **hook additionalContext 주입이 실제 PM TaskCreate/TaskUpdate 호출을 유발하는지 불확실(플랫폼 계약 의존)** | **P0** | **L2+L3** | **S-4, S-9** |
| H-5 | F-002 stdout 파싱 | 경고/다중 라인 혼입 stdout에서 todo_mirror JSON 추출 실패 | P1 | L2 | S-4 |
| H-6 | F-002 matcher 광역성 | matcher:Bash가 비state-tool 호출에도 발동(소음·오주입) | P2 | L2 | S-5 |
| H-7 | F-003 merge 마커 | 소유권 마커 키를 Claude Code가 거부/경고해 settings 로드 실패 | P0 | L2+L3 | S-6, S-9 |
| H-8 | F-003 멱등·보존 | 외부 hook(orca) clobber / N회 재실행 시 OPAL 중복 누적 | P0 | L2 | S-6 |
| H-9 | 플랫폼 독립성 | Claude 전용 hook이 플랫폼 독립 원칙과 상충 | P1 | 산출물 검사 | S-8 |
| H-10 | F-004 교체 완전성 | prose-only 미러 의존 잔존(구형 미제거)/SSOT·능력감지 문구 유실 | P1 | 산출물 검사 | S-8 |
| H-11 | F-003 테스트 가능성 | merge 로직이 install 인라인에 매몰되어 결정론 검증 불가 | P1 | L1 | S-6 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 자원 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| state.json | opds 11행 init(agentic) | 전부 pending + 사용자확인 행 na | fixture(state-tool init) |
| state.json | 단계 부분완료 | TASK 전행 done, PLAN 작업 in_progress | fixture(advance/mark 적용) |
| state.json | 블로커 | EXECUTE 작업 failed(block) | fixture(block 적용) |
| stdin JSON | PostToolUse 이벤트(state-tool) | `{tool_name:"Bash", tool_input:{command:"...run.sh advance..."}, tool_response:{stdout:"<todo_mirror 포함 JSON>"}}` | 합성 |
| stdin JSON | PostToolUse 이벤트(비state-tool) | `{tool_name:"Bash", tool_input:{command:"ls -la"}, ...}` | 합성 |
| stdin JSON | 경고 혼입 stdout | deprecation 경고 라인 + 마지막 JSON 라인 | 합성 |
| settings.json | orca 선존재 | `hooks.PostToolUse=[{orca...}]`(마커 無) | fixture |
| claude-hooks.json | OPAL source | SubagentStop/Stop/PostToolUse(마커 대상) | 소스 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (사전) | When (실행) | Then (검증) |
|---------|------------|------------|------------|
| S-1 | 각 파생 상태 state.json | build_todo_mirror 호출 | 단계별 status 정확(na중립/전부pending→pending/전부done→completed/부분·failed→in_progress) |
| S-2 | init 직후 state | 4개 서브명령 실행 | state.json에 todo_mirror 부재 + schema 통과 |
| S-3 | 기존 테스트 스위트 | 전량 실행 | 회귀 0(응답 키 추가 하위호환) |
| S-4 | state-tool stdout(+경고) stdin | todo_mirror_hook.py 실행 | additionalContext에 지시문+payload 출력 |
| S-5 | 비state-tool/깨진 JSON stdin | todo_mirror_hook.py 실행 | 무출력·exit0(부작용0) |
| S-6 | orca 선존재 settings + OPAL source | merge_hooks 2회 실행 | orca 보존+OPAL upsert+2회 바이트 동일+유효JSON |
| S-7 | 수정된 install-mac.sh | `bash -n` | 문법 통과 |
| S-8 | 수정된 state.md | grep/문구 검사 | hook 강제 재서술+SSOT·능력감지 보존+prose-only 잔존0 |
| S-9 | install 재배포된 환경 | 새 세션에서 태스크 시작→state-tool 호출 연쇄 | todo 패널 시작 시 생성→단계마다 갱신→CLOSE까지 유지 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: build_todo_mirror 파생 규칙 (na 중립·경계값)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `build_todo_mirror(state, action)` 파생 로직 (state_tool.py) |
| 계층 | L1 |
| 실행 방식 | M1 (테스트 도구) |
| 조건 | 4종 state fixture(전부pending / 전부done 단계 / 부분완료 / 블로커 failed / agentic na 혼재) |
| 기대 결과 | 전부pending→pending, 전 행 done→completed, 부분·in_progress·failed→in_progress, na는 집계 중립(미착수 단계 오판 없음) |
| 도구 | python unittest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k TestTodoMirror` |
| 결과 | **Pass** |
| 상세 | `TestTodoMirror` 7/7 PASS: test_ts001_init_payload_all_pending, test_ts002_stage_all_done_completed, test_ts003_advance_and_partial_in_progress, test_ts004_untouched_stage_pending, test_ts005_na_neutral, test_ts006_block_keeps_in_progress, test_ts007_not_persisted_schema_passes. 전부pending→pending(ts001/ts004), 전행done→completed(ts002), 부분·failed→in_progress(ts003/ts006), na 중립 확인(ts005) — 기대 파생 규칙 전량 일치. |

#### S-2: todo_mirror 영속 경계 (state.json 무저장 + schema)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | 4개 서브명령 출력 vs state.json 영속 경계 |
| 계층 | L1 |
| 실행 방식 | M1 |
| 조건 | init/advance/mark/block 실행 후 state.json 로드 + schema validate |
| 기대 결과 | ok() stdout에는 todo_mirror 존재, state.json에는 부재, state.schema.json 통과 |
| 도구 | python unittest |
| 실행 명령 | `test_ts007_not_persisted_schema_passes` (TestTodoMirror 내 포함, S-1과 동일 실행으로 커버) — init/advance/mark/block 4개 서브명령 stdout에는 todo_mirror 존재, state.json 로드 후 `todo_mirror` 키 부재 + schema validate 통과 검증 |
| 결과 | **Pass** |
| 상세 | `test_ts007_not_persisted_schema_passes` PASS — ok() stdout dict에는 `todo_mirror` 키 존재 확인, 동일 태스크 state.json 파일을 다시 로드해 `"todo_mirror" not in loaded` assert 통과, `validate` 서브명령 별도 호출로 schema 검증(exit 0) 확인. additionalProperties:false 위반 없음(H-3 반증). |

#### S-3: state-tool 회귀 (응답 키 추가 하위호환)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | state-tool 기존 테스트 스위트 전량 |
| 계층 | L1 |
| 실행 방식 | M1 |
| 조건 | todo_mirror 추가 후 기존 테스트 재실행 |
| 기대 결과 | 기존 테스트 전량 PASS(회귀 0), 신규 TestTodoMirror PASS |
| 도구 | python unittest/pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v` |
| 결과 | **Pass (회귀 0)** |
| 상세 | 264 케이스(20 subtests 포함) 중 261 PASS, 3건 FAIL — 전량 **076 무관 기존 결함으로 검증 확인**: (1) `TestVerify::test_verify_passes_own_test_scenario_md` — 하드코딩 외부 경로(`/Volumes/Data/AiStudio/.../034-...`) 부재로 실패, 034 태스크 산출물 자체가 이 리포지토리 밖에 있어 076 이전부터 실패하던 결함. (2)(3) `TestGroupAPipelineSpecs::test_real_group_a_pipeline_json_files_if_present[opd/opds]` — `_GROUP_A_SPECS` 기대 행수(opd15/opds10) vs 실제 pipeline.json(opd16/opds11) 불일치. `git log`로 확인 결과 opd pipeline.json 최종 변경은 c8cb0b6(073), opds는 6b1eafb(075) — 둘 다 076 시작 전 커밋. `git diff HEAD`로 076 변경분(state_tool.py/test_state_tool.py 등)에 `_GROUP_A_SPECS` 및 pipeline.json 터치 0건 확인 — 076 기원 아님(073/075 선행 결함, PM 사전 통지와 일치). 신규 `TestTodoMirror` 7/7 PASS 포함 하위호환 확인. |

#### S-6: merge_hooks 멱등 upsert (보존·upsert·멱등·유효JSON)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7, H-8, H-11 |
| 대상 | `merge_hooks(target, source)` (scripts/merge-hooks.py) |
| 계층 | L1 |
| 실행 방식 | M1 |
| 조건 | orca PostToolUse 선존재 settings + OPAL source, merge 2회 연속 |
| 기대 결과 | orca 항목 보존, OPAL 항목 `_opal_managed:true` upsert, 2회 결과 바이트 동일(중복0), 산출 유효 JSON·마커 매처 블록 한정 |
| 도구 | python unittest |
| 실행 명령 | `python3 -m pytest scripts/tests/test_merge_hooks.py -v` |
| 결과 | **Pass** |
| 상세 | 5/5 PASS: test_missing_target_creates_from_empty, test_ts020_external_orca_preserved(orca PostToolUse 보존), test_ts021_opal_upsert_stamped(`_opal_managed:true` upsert), test_ts022_idempotent_byte_identical(2회 연속 merge 바이트 동일), test_ts023_valid_json_marker_only_on_matcher_blocks(산출 JSON 유효+마커가 매처 블록에 한정). H-7/H-8/H-11 전량 반증(결함 부재 확인). |

### L2. 프로세스 통합 (자동, 실 입출력)

#### S-4: hook 릴레이 — state-tool 이벤트 → additionalContext 주입

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4(L2), H-5 |
| 대상 | `todo_mirror_hook.py` main() 정상 경로 |
| 계층 | L2 |
| 실행 방식 | M1 (합성 stdin 주입) |
| 조건 | state-tool advance PostToolUse 이벤트 JSON(경고 라인 혼입 stdout 포함)을 stdin으로 주입 |
| 기대 결과 | stdout에 `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"<지시문+payload>"}}` 출력, 경고 혼입에도 todo_mirror 추출 성공 |
| 도구 | python unittest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_todo_mirror_hook.py -v -k "test_ts010 or test_ts012"` |
| 결과 | **Pass** |
| 상세 | test_ts010_state_tool_advance_injects_context PASS(정상 advance 이벤트 → `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"<지시문+payload>"}}` 출력 확인), test_ts012_stdout_with_warning_lines PASS(경고 라인 혼입 stdout에서도 마지막 JSON 라인 파싱하여 todo_mirror 추출 성공). H-4(L2)/H-5 반증. |

#### S-5: hook 비발동·fail-safe (비state-tool·깨진 입력)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6, DEC-9(fail-safe) |
| 대상 | `todo_mirror_hook.py` 비발동/예외 경로 |
| 계층 | L2 |
| 실행 방식 | M1 |
| 조건 | (a) 비state-tool Bash 명령 (b) todo_mirror 없는 출력 (c) 깨진 JSON stdin |
| 기대 결과 | 전 경로 무출력·exit0(툴 흐름 비차단, 부작용0) |
| 도구 | python unittest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_todo_mirror_hook.py -v -k "test_ts011 or test_ts013"` |
| 결과 | **Pass** |
| 상세 | 4/4 PASS: test_ts011_non_bash_tool_no_output(비Bash tool_name 무출력), test_ts011_non_state_tool_no_output(비state-tool Bash 명령 무출력), test_ts013_broken_json_stdin_no_output(깨진 stdin JSON → 무출력·exit0), test_ts013_broken_json_stdout_no_output/test_ts013_mirrored_cmd_without_payload_no_output(todo_mirror 부재 stdout → 무출력). 전 경로 exit0·부작용0 확인(H-6, DEC-9 fail-safe 반증). |

#### S-7: install 문법 무손상

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11(회귀), R-6 |
| 대상 | 수정된 `scripts/install-mac.sh` |
| 계층 | L2 |
| 실행 방식 | M1 |
| 조건 | merge_hooks_config 위임 개선 후 |
| 기대 결과 | `bash -n scripts/install-mac.sh` 통과, merge-hooks.py 위임 호출 존재 |
| 도구 | bash -n |
| 실행 명령 | `bash -n scripts/install-mac.sh` + `grep -n "merge-hooks\|merge_hooks" scripts/install-mac.sh` |
| 결과 | **Pass** |
| 상세 | `bash -n` 문법 통과(exit 0). grep 결과: v4.1 변경이력 라인(인라인 python clobber 제거→scripts/merge-hooks.py 위임, 076) + `merge_hooks_config()` 함수 내 `/usr/bin/python3 "$FRAMEWORK_ROOT/scripts/merge-hooks.py" "$target" "$hooks_json"` 위임 호출 확인 + 호출부(`merge_hooks_config "$settings" "$hooks_src"`) 존재. H-11(회귀) 반증. |

#### S-8: state.md 교체 정합 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9, H-10, R-4, R-5 |
| 대상 | 수정된 `opal/core/references/harness/state.md` §파이프라인 todo 미러 |
| 계층 | L2 (산출물 검사) |
| 실행 방식 | M1 (grep/문구 확인) |
| 조건 | F-004 정합 후 |
| 기대 결과 | (a) hook 강제 트리거+todo_mirror 페이로드 방식으로 재서술 (b) SSOT 불변·능력감지 게이트·읽기전용 거울 문구 보존 (c) "PM이 직접 재계산/직접 호출"류 prose-only 의존 잔존 0(grep) (d) 변경이력 v1.5 행 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n "todo\|SSOT\|능력감지\|능력 감지\|읽기 전용\|거울\|v1.5" opal/core/references/harness/state.md` + `grep -n "PM이 직접" opal/core/references/harness/state.md` |
| 결과 | **Pass** |
| 상세 | (a) hook 강제 재서술 확인: "**강제 메커니즘 (hook 트리거)**: 갱신은 산문 지시가 아니라 도구·hook로 집행된다" + PostToolUse hook 트리거·`todo_mirror` 페이로드 3단계 서술(§52-64행) 확인. (b) SSOT/능력감지 보존 확인: "[게이트 — 능력 감지]"(65행), "[SSOT 불변]"(66행) 원문 유지 확인. (c) prose-only 잔존 0: `grep "PM이 직접"` 결과 본문에는 0건, 유일 매치는 변경이력 v1.5 행에서 "PM이 직접 재계산 의존 **제거**"(과거형 서술)뿐 — 잔존 지시문 아님. (d) 변경이력 v1.5 행(2026-07-23 17:43, 076) 존재 확인. H-9/H-10/R-4/R-5 전량 충족. |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-9: 목표달성 실증 — 태스크 시작~CLOSE todo 패널 자동 표시 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4(L3, 핵심), H-7(L3) |
| 대상 | 전체 목표 — "태스크 시작 시 todo 패널 자동 생성 → 단계마다 갱신 → CLOSE까지 유지" |
| 계층 | L3 |
| 실행 방식 | M3 (사용자 협업) |
| 조건 | install 재배포(캡틴 지시) 후 **새 세션**에서 임의 태스크를 opds/opd로 시작 |
| 기대 결과 | (1) settings 로드 오류 없이 세션 기동(H-7) (2) state-tool init 직후 네이티브 todo 패널에 단계별 todo 생성(H-4) (3) advance/mark 마다 해당 단계 todo 자동 갱신 (4) CLOSE까지 패널 유지 (5) 기존 orca hook 정상 동작 유지 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **SUPERVISOR 대기(캡틴)** — op-dev-test-agent 실행 대상 아님(L3 마커 감지, 실행 없이 PM 반환) |
| 상세 | install 재배포 후 새 Claude Code 세션에서 실증 필요(H-4 핵심 목표달성 축). 본 TEST 단계에서는 미실행. |

> **[SUPERVISOR 요청 양식]** 캡틴께: install 재배포 후 새 Claude Code 세션을 열어 아무 태스크나 `//opds` 등으로 시작해 주세요. STATE init 직후 하단 todo 패널에 단계(TASK/PLAN/EXECUTE/TEST/CLOSE) todo가 뜨는지, 단계 진행마다 갱신되는지, 기존 알림(orca) hook이 여전히 작동하는지 확인 후 결과를 알려주시면 S-9를 기록하겠습니다. 이것이 이 태스크의 근본 성패(H-4)를 판정하는 시나리오입니다.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 (todo_mirror 출력·파생) | H-2 | L1 | S-1 | `test_state_tool.py:TestTodoMirror` | na중립·경계값 |
| R-1 (영속 경계) | H-3 | L1 | S-2 | `test_state_tool.py:TestTodoMirror` | state.json 무저장 |
| R-2 (hook 발동·주입) | H-4, H-5 | L2 | S-4 | `test_todo_mirror_hook.py` | additionalContext |
| R-2 (비발동·fail-safe) | H-6 | L2 | S-5 | `test_todo_mirror_hook.py` | 무출력 exit0 |
| R-2 (hook→PM 유발 실증) | H-4 | L3 | S-9 | (수동) | **핵심 목표달성** |
| R-3 (보존·upsert·멱등) | H-7, H-8, H-11 | L1 | S-6 | `test_merge_hooks.py` | 마커 기반 |
| R-4 (hook 강제 재서술·보존) | H-9, H-10 | L2 | S-8 | (grep) | 산출물 검사 |
| R-5 (교체 — 구형 잔존0) | H-10 | L2 | S-8 | (grep) | prose-only 0 |
| R-5 (교체 — 신형 채택 실증) | H-4 | L3 | S-9 | (수동) | 실세션 채택 |
| R-6 (회귀 — state-tool) | H-1 | L1 | S-3 | 기존 스위트 | 하위호환 |
| R-6 (회귀 — install 문법) | H-11 | L2 | S-7 | `bash -n` | 문법 |

> **목표달성 시나리오(①축)**: S-9(L3) — 사용자 계층에서 "태스크 시작~CLOSE todo 자동 표시" 태스크 목표를 직접 검증. scenario-gate.md §2 ①축 충족.
> **교체 검증(R-5)**: 구형(prose-only 잔존0, S-8) + 신형 채택(실세션 hook 트리거 동작, S-9) 양쪽 명시.

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | pyflakes/flake8(미설치 — 환경에 부재) → `py_compile` 대체 | Pass(대체 도구) | 프로젝트에 Python 린터 미구성(docs/CONVENTIONS.md에 강제 규정 없음). `python3 -m py_compile state_tool.py todo_mirror_hook.py merge-hooks.py` 전부 컴파일 성공 — 문법·임포트 결함 없음. 회귀 가드 목적(EXECUTE 단계 lint 중복 아님) 충족. |
| 2 | 타입 체크 | 해당 없음 | Skip | 프로젝트 Python 파일에 타입 힌트/mypy·pyright 설정 없음(비강제) — 해당 없음으로 스킵. |
| 3 | 포맷터 | black(미설치 — 환경에 부재) | N/A | 프로젝트에 포맷터 미구성. 수동 확인 결과 변경분 코드 스타일은 기존 파일 컨벤션과 일치(들여쓰기 4스페이스, snake_case 준수 — docs/CONVENTIONS.md §언어 규칙). |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `grep -nEi "(api[_-]?key\|secret\|password\|token\|bearer)\s*[:=]\s*['\"][A-Za-z0-9]{8,}"` 전 changed_files 대상 실행 — 매치 0건. |
| 2 | .gitignore 확인 | Pass | `.gitignore`에 `.env` 등록 확인. changed_files에 시크릿·자격증명 파일 없음. |
| 3 | hook stdin 예외 격리(임의 실행 없음) | Pass | `todo_mirror_hook.py`에 `subprocess`/`os.system`/`eval(`/`exec(` 0건(grep 확인) — 임의 코드 실행 경로 없음. main()이 최상위 `try/except Exception` 블록으로 감싸져 있고 성공/실패 모두 `sys.exit(0)`(130행)로 종료 — stdin 파싱 예외가 툴 흐름을 차단하지 않음(fail-safe, DEC-9). S-5 테스트(test_ts013_*)로 실행 증거 확보. |

## 7. 판정

**All Pass — L1/L2 시나리오 S-1~S-8 전량 Pass(실행 출력 증거 확보). state-tool 전체 스위트 261/264 PASS, 3건 FAIL은 073(TestGroupAPipelineSpecs opd)·075(동 opds)·034 태스크 산출물 외부 경로 부재 기원의 076 무관 기존 결함으로 `git log`/`git diff HEAD` 검증 확인(076 diff에 `_GROUP_A_SPECS`/pipeline.json 터치 0건) — 회귀 0으로 판정. 신규 TestTodoMirror(7) + TestTodoMirrorHook·TestHookPureFunctions(12) + TestMergeHooks(5) = 24건 신규 테스트 전량 PASS. 코드 품질(회귀 가드)·보안 검사 전량 Pass, 하드코딩 시크릿·임의 실행 경로 없음. S-9(L3 [SUPERVISOR])는 install 재배포+새 세션 수동 실증 필요 대상으로 실행하지 않고 SUPERVISOR 대기로 표기, PM 반환.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (합성 stdin·fixture는 실 입력, mock 아님)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-11 전부 S-N 매핑)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-9)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 없음 → M2(E2E) 의무 트리거 미해당 (Python/Bash/JSON/Markdown 전용)
- [x] 목표 커버 — TASK R-1~R-6 전체 §4 매핑, 목표달성 시나리오 S-9 존재
