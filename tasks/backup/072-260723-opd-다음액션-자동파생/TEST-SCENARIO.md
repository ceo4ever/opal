# TEST SCENARIO: state-tool STATE.md "다음 액션" 자동 파생

> 작성일: 2026-07-23 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md §리스크 가설 표 기반
> **RED-first 트랙**: 적격(버그 수정 + 동작 변경 = self-confirming 위험, 헌법 §4 / red-first.md §1.5). `verify --red-check` ON. RED 대상 = `TestNextActionAutoDerive`가 파생 전 코드에서 실패(S-8).

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `TestFreeTextPreservation` (`test_state_tool.py:1516-1528`) | "다음 액션 불변" assert가 R-2 구현 시 필연 RED — **의도된 설계 반전이지 회귀 아님** | P0 | L1 | S-8, S-9 |
| H-2 | `_derive_next_action` 프론티어 정의 | "다음 대기 행" 오판 — 완료행/실패행/전체완료 경계에서 잘못된 문자열 파생 | P1 | L1 | S-2, S-3 |
| H-3 | `update_next_action_section` 정규식 치환 범위 | 섹션 전체 덮어써 PM 자유 기재 소실 / 첫 줄 치환이 다른 섹션 오염 | P1 | L1 | S-4 |
| H-4 | `state.schema.json` `required` 오추가 | `next_action`을 `required`에 넣으면 구버전 state.json 향후 실 validate 시 위반 → 하위호환 파괴 | P1(향후) | L1 | S-1 |
| H-5 | `sync_state_md` 시그니처 확장 | `next_action` 파라미터 추가가 block/add-row/status의 "다음 액션 미접촉" 계약 파괴 | P1 | L1 | S-5 |
| H-6 | install 배포본-소스 드리프트 | install 미실행/부분 실행으로 `~/.opal/tools/state-tool/`와 소스 불일치 | P1 | L1 | S-12 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 테이블 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 임시 태스크 폴더 | `tmp_task/` (unittest `setUp` tempdir) | `init` 직후 15행 파이프라인(opd) 또는 최소 rows fixture | fixture (`make_args` + `cmd_init`, `test_state_tool.py:97-141`) |
| state.json | `tmp_task/state.json` | `rows[]` = pending/in_progress/done 혼합 (경계 케이스별 조립) | fixture (직접 status 세팅) |
| state.json (구버전) | `tmp_task/state.json` (next_action 키 없음) | 하위호환 검증용 — 필드 부재 상태 | fixture (키 삭제 후 저장) |
| STATE.md | `tmp_task/STATE.md` | `## 다음 액션` 헤더 + 첫 줄(파생값) + 하위 자유 기재(`- 세부 액션 1/2`) | fixture (`TestFreeTextPreservation.setUp` 확장 패턴, `test_state_tool.py:1490-1497`) |
| 배포본 | `~/.opal/tools/state-tool/state_tool.py`, `schema/state.schema.json` | install 후 소스와 diff 0(변경이력 strip 제외) | install 실행 산출 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | 신규 태스크 폴더 | `cmd_init` (±`--next-action`) | state.json에 `next_action` 키 존재, schema `required` 불변, 구버전 로드 무손상 |
| S-2 | rows 순차 상태 | `advance`/`mark` 여러 행 순차 | 각 시점 state.json·STATE.md `next_action`=프론티어 행(pending "진입" / in_progress "진행 중") |
| S-3 | 모든 행 직전까지 done | 마지막(CLOSE) 행 `mark --done` | `next_action == "태스크 완료"` |
| S-4 | STATE.md `## 다음 액션` + 하위 자유기재 2줄 | `mark`/`advance` | 첫 줄만 파생값 치환, `- 세부 액션 1/2` 잔존 |
| S-5 | STATE.md `## 다음 액션` 섹션 | `block`/`add-row` | `## 다음 액션` 섹션 전체 불변(None 전달=미접촉) |
| S-6 | rows 상태 | `advance`/`mark --next-action "커스텀"` | `next_action == "커스텀"`(파생보다 우선) |
| S-7 | S-6 직후 상태 | `--next-action` 없는 후속 `advance`/`mark` | 자동 파생값으로 복귀(비지속) |
| S-8 | 파생 전(未구현) 코드 | `TestNextActionAutoDerive` 실행 | 실패(RED, exit≠0) — 증거 기록 |
| S-9 | 반전된 `TestFreeTextPreservation` | mark/advance 반전 2 + block/add-row 유지 3 실행 | 반전 2 GREEN(블로커 보존+파생+자유기재), 유지 3 GREEN |
| S-10 | 전체 스위트 | `python -m unittest` 전체 | 무관 1건 제외 240 pass + 신규/반전분 GREEN |
| S-11 | 소스 문서 | grep `state-template.md`/README | "다음 액션 수동" 잔존 0, 072 변경이력·@header 반영 |
| S-12 | install 실행 | `./scripts/install-mac.sh` 후 diff | 배포본-소스 diff 0(변경이력 strip 제외) |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: init `next_action` 영속화 + 스키마 optional 등록 + 하위호환

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-001 — `cmd_init` state 딕셔너리 `next_action` 기록, schema `properties` 등록(`required` 미포함), 구버전 state.json 무손상 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구 — unittest) |
| 조건 | 신규 태스크 `init`(기본값 및 `--next-action` 지정 양쪽), `next_action` 키 없는 구버전 state.json 로드 후 `advance`/`mark` |
| 기대 결과 | ①init 후 state.json에 `next_action` 키 존재(값=`--next-action` 또는 "PLAN 단계 진입") ②`state.schema.json` `required` 배열 불변(`next_action` 미포함) ③구버전 state.json으로 advance/mark 시 KeyError 없이 동작 ④기존 `init --next-action` 렌더 불변 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool/tests && ~/.opal/.venv/bin/python -m unittest test_state_tool.TestNextActionAutoDerive.test_r1_init_default_next_action_persisted_to_state_json test_state_tool.TestNextActionAutoDerive.test_r1_init_custom_next_action_persisted_to_state_json test_state_tool.TestNextActionAutoDerive.test_r1_schema_next_action_optional_registered_not_required test_state_tool.TestNextActionAutoDerive.test_r1_legacy_state_json_without_next_action_advance_no_keyerror -v` |
| 결과 | **Pass** — exit 0, `Ran 4 tests in 0.004s / OK` |
| 상세 | 4/4 ok: ①init 기본값 → `next_action`="PLAN 단계 진입" 영속 ②`--next-action "커스텀 초기 액션"` → 해당 값 영속 ③`state.schema.json` properties에 `next_action` 등록·`required` 배열 불변 확인 ④next_action 키 없는 구버전 state.json → advance 시 KeyError 없이 정상 동작 |

#### S-2: advance/mark 순차 전이 프론티어 파생 + 렌더 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-002 — `_derive_next_action`(프론티어=첫 미완료 행), `update_next_action_section`(첫 줄 치환), advance/mark 통합 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구 — unittest) |
| 조건 | 여러 행을 순차로 `advance`(→in_progress)·`mark --done`(→다음 행) 하며 각 시점 값 확인 |
| 기대 결과 | ①pending 프론티어 → `"{stage} {item} 진입"` ②in_progress 프론티어 → `"{stage} {item} 진행 중"` ③state.json `next_action`과 STATE.md `## 다음 액션` 첫 줄 일치(R-3) ④070 task-step key(`resolve_row_index`) 무접촉 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool/tests && ~/.opal/.venv/bin/python -m unittest test_state_tool.TestNextActionAutoDerive.test_r2_r3_sequential_frontier_derivation_advance_mark -v` |
| 결과 | **Pass** — exit 0, `Ran 1 test in 0.003s / OK` |
| 상세 | pending 프론티어 → `"{stage} {item} 진입"`, in_progress 프론티어 → `"{stage} {item} 진행 중"` 각 전이 시점 확인. state.json `next_action`과 STATE.md `## 다음 액션` 첫 줄 일치(R-3) 확인. 070 `resolve_row_index` 무접촉 유지 |

#### S-3: 전체 완료 시 "태스크 완료" (M-2 경계)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-002 — `_derive_next_action` 루프 미스 시 `return "태스크 완료"` |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구 — unittest) |
| 조건 | 마지막(CLOSE) 행까지 모두 `_COMPLETE_STATUSES` 상태로 만든 뒤 마지막 행 `mark --done` |
| 기대 결과 | 다음 대기 행 부재 → `next_action == "태스크 완료"`, STATE.md 첫 줄 동일 반영 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool/tests && ~/.opal/.venv/bin/python -m unittest test_state_tool.TestNextActionAutoDerive.test_r2_m2_all_rows_complete_next_action_task_complete -v` |
| 결과 | **Pass** — exit 0, `Ran 1 test in 0.003s / OK` |
| 상세 | 마지막(CLOSE) 행까지 모두 done 처리 후 `next_action == "태스크 완료"` 확인, STATE.md 첫 줄 동일 반영 확인 |

#### S-4: 첫 줄만 치환 — 하위 자유 기재 보존 (M-1)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-002 — `update_next_action_section` 정규식 `(^## 다음 액션\n)([^\n]*)` 첫 줄만 치환 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구 — unittest) |
| 조건 | `## 다음 액션` 헤더 + 첫 줄 + 하위 `- 세부 액션 1`/`- 세부 액션 2` 상태에서 `mark`/`advance` |
| 기대 결과 | ①첫 줄만 파생값으로 교체 ②`- 세부 액션 1/2` 잔존 ③다른 섹션(블로커 등) 오염 없음 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool/tests && ~/.opal/.venv/bin/python -m unittest test_state_tool.TestNextActionAutoDerive.test_m1_first_line_replaced_subordinate_free_text_preserved -v` |
| 결과 | **Pass** — exit 0, `Ran 1 test in 0.003s / OK` |
| 상세 | 첫 줄만 파생값으로 치환됨, `- 세부 액션 1`/`- 세부 액션 2` 잔존 확인, 다른 섹션(블로커 등) 오염 없음 확인 |

#### S-5: block/add-row/status "다음 액션" 미접촉 (H-5 계약 보존)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-002 — `sync_state_md(next_action=None)` 기본값, block/add-row/status 미전달 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구 — unittest) |
| 조건 | `## 다음 액션` 섹션이 있는 상태에서 `block`/`add-row` 호출 |
| 기대 결과 | `## 다음 액션` 섹션 전체(첫 줄 포함) 문자 그대로 불변 — TASK §범위 "블로커 섹션 동작 변경 제외"와 정합 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool/tests && ~/.opal/.venv/bin/python -m unittest test_state_tool.TestFreeTextPreservation.test_block_preserves_free_text test_state_tool.TestFreeTextPreservation.test_add_row_preserves_free_text -v` |
| 결과 | **Pass** — exit 0, `Ran 2 tests in 0.004s / OK` |
| 상세 | `block`/`add-row` 호출 후 `## 다음 액션` 섹션 전체(첫 줄 포함) 문자 그대로 불변 확인 — `sync_state_md(next_action=None)` 기본값 계약 유지 |

#### S-6: advance/mark `--next-action` 오버라이드 우선

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-003 — `args.next_action or _derive_next_action(state)` 우선순위 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구 — unittest) |
| 조건 | `advance`/`mark`에 `--next-action "커스텀 안내"` 지정 |
| 기대 결과 | `next_action == "커스텀 안내"`(자동 파생보다 우선), STATE.md 첫 줄 동일 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool/tests && ~/.opal/.venv/bin/python -m unittest test_state_tool.TestNextActionAutoDerive.test_r4_override_next_action_takes_priority_over_derivation -v` |
| 결과 | **Pass** — exit 0, `Ran 1 test in 0.161s / OK` |
| 상세 | `advance --next-action "커스텀 안내"` 지정 시 `next_action == "커스텀 안내"`(자동 파생값보다 우선) 확인, STATE.md 첫 줄 동일 반영 확인 |

#### S-7: 오버라이드 비지속 — 다음 전이 자동 파생 복귀 (M-3)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-003 — per-transition 비지속, state.json `next_action`은 "마지막 write" 미러 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구 — unittest) |
| 조건 | S-6 오버라이드 전이 → 이후 `--next-action` 없는 `advance`/`mark` |
| 기대 결과 | 후속 전이에서 커스텀 값이 자동 파생값으로 덮어써짐(stale 재도입 없음) |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool/tests && ~/.opal/.venv/bin/python -m unittest test_state_tool.TestNextActionAutoDerive.test_m3_override_non_persistent_reverts_to_derived_on_next_transition -v` |
| 결과 | **Pass** — exit 0, `Ran 1 test in 0.156s / OK` |
| 상세 | S-6 오버라이드 전이 직후 `--next-action` 없는 후속 advance/mark 실행 → 자동 파생값으로 복귀 확인(stale 커스텀 값 재도입 없음, 비지속 계약 확인) |

#### S-8: RED-first — 파생 전 코드에서 `TestNextActionAutoDerive` 실패

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-004 — 신규 `TestNextActionAutoDerive`(RED 증거) |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구 — unittest) |
| 조건 | 파생 로직 구현 **전** 코드에서 신규 클래스 실행 (`verify --red-check` ON) |
| 기대 결과 | 신규 클래스가 실패(RED, exit≠0) — advance/mark `--next-action` 부재 argparse 에러 또는 파생 미수행 assert 실패. RED 증거를 로그로 기록 |
| 도구 | unittest + `state-tool verify --red-check` |
| 실행 명령 | `cd opal/tools/state-tool/tests && ~/.opal/.venv/bin/python -m unittest test_state_tool.TestNextActionAutoDerive -v` |
| 결과 | **RED 확보** — exit code 1, 9 tests run / failures=11(8개 테스트 메서드 + `test_r2_r3_sequential_frontier_derivation_advance_mark`의 subTest 4건 포함) / 1 pass(하위호환 회귀 가드 `test_r1_legacy_state_json_without_next_action_advance_no_keyerror` — 파생 미구현 상태에서도 원래 성립하는 forward guard, 의도된 예외) |
| 상세 | 신규 8개 테스트 메서드 모두 실패: ①`test_r1_init_default_next_action_persisted_to_state_json`/`test_r1_init_custom_next_action_persisted_to_state_json` — state.json에 `next_action` 키 자체가 없어 `AssertionError: 'next_action' not found`/`None != '커스텀 초기 액션'` ②`test_r1_schema_next_action_optional_registered_not_required` — schema `properties`에 `next_action` 미등록 ③`test_r2_r3_sequential_frontier_derivation_advance_mark` — 4개 전이 시점 모두 `state.get("next_action")`이 `None`(파생 미수행) ④`test_r2_m2_all_rows_complete_next_action_task_complete` — 프론티어 파생값 `None != 'CLOSE State Gate 진입'` ⑤`test_m1_first_line_replaced_subordinate_free_text_preserved` — 첫 줄 미치환 ⑥`test_r4_override_next_action_takes_priority_over_derivation`/`test_m3_override_non_persistent_reverts_to_derived_on_next_transition` — advance에 `--next-action` 플래그 부재로 subprocess(run.sh) 실호출이 argparse 단계에서 `exit=2`, stderr=`state-tool: error: unrecognized arguments: --next-action 커스텀 안내`. 전체 스위트(`python -m unittest test_state_tool -v`) 1회 실행 결과: Ran 250 tests, failures=12 = 신규 8개 테스트 메서드(assert 실패 11건, subTest 포함) + 무관 기존 1건(`TestVerify.test_verify_passes_own_test_scenario_md`, 이동된 `tasks/backup/034-...` 경로 참조 — 본 태스크 무관, 사전 존재 실패). 기존 240 pass 불변 확인(250 - 9 실패 테스트 메서드 = 241 pass = 기존 240 + 신규 forward-guard 1건). **[TEST 단계 재확인 — GREEN 전환 확인]** 구현 후 동일 명령 재실행 결과: `Ran 9 tests in 0.334s / OK`(exit 0) — 8개 신규 메서드 전부 RED→GREEN 전환 확인, 1개(하위호환 forward-guard) 계속 pass 유지. RED-first 트랙 완주 확인(red-first.md §1.5 정합). |

#### S-9: `TestFreeTextPreservation` 반전 — 회귀 아님(의도된 설계 반전)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-004 — mark/advance 2개 반전("블로커 보존+다음액션 파생+자유기재 보존") + block/add-row/marker 3개 유지 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구 — unittest) |
| 조건 | 반전·유지 테스트 실행. ⚠️ **이 RED→갱신은 회귀가 아니라 설계 반전** — `state-template.md:34` 설계를 뒤집는 의도된 변경 |
| 기대 결과 | ①반전 2개(`test_mark_derives_next_action_preserves_others`·`test_advance_...`) GREEN ②유지 3개(block/add-row/marker) GREEN ③모든 테스트의 블로커 섹션 assert 불변 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool/tests && ~/.opal/.venv/bin/python -m unittest test_state_tool.TestFreeTextPreservation -v` |
| 결과 | **Pass** — exit 0, `Ran 5 tests in 0.009s / OK` |
| 상세 | 반전 2개 GREEN: `test_mark_derives_next_action_preserves_others`("mark 후: 블로커 섹션 보존 + '다음 액션' 첫 줄 파생 갱신 + 하위 자유기재 보존" ... ok), `test_advance_derives_next_action_preserves_others`(동일 패턴 ... ok) — `state-template.md:34` 舊설계("PM 수동 갱신") 반전을 검증하는 의도된 GREEN, 회귀 아님. 유지 3개 GREEN: `test_block_preserves_free_text`·`test_add_row_preserves_free_text`·`test_pipeline_marker_region_only_changed` 모두 ok. 전 5건 블로커 섹션 assert 불변 확인 |

#### S-10: 전체 회귀 — 무관 1건 제외 240 pass 유지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-004 — 베이스라인 회귀 기준 |
| 계층 | L1 |
| **실행 방식** | M1 (테스트 도구 — unittest) |
| 조건 | `test_state_tool.py` 전체 스위트 실행 |
| 기대 결과 | 무관 실패 1건(`TestVerify.test_verify_passes_own_test_scenario_md` — 이동된 `tasks/backup/034-...` 경로) **제외** 240 pass 유지 + 신규 `TestNextActionAutoDerive` + 반전분 GREEN. RED-first 클래스 GREEN 전환 |
| 도구 | unittest |
| 실행 명령 | `cd opal/tools/state-tool/tests && ~/.opal/.venv/bin/python -m unittest test_state_tool -v` |
| 결과 | **Pass(무관 1건 제외)** — exit 1, `Ran 250 tests in 4.593s / FAILED (failures=1)` |
| 상세 | 실패 1건은 `TestVerify.test_verify_passes_own_test_scenario_md` — `AssertionError: False is not true : 034 TEST-SCENARIO.md 파일이 없음`(034 태스크 폴더가 `tasks/backup/034-...`로 이동되어 경로 참조가 깨진 사전 존재 실패, 072 변경과 무관). 이 1건 제외 249 pass 확인 — 신규 `TestNextActionAutoDerive`(9) + 반전 `TestFreeTextPreservation`(5) 전부 GREEN 포함. exit code는 1이지만 무관 실패 배제 시 회귀 없음(§헌법 무관 실패 판정 근거 명시) |

#### S-11: 문서·설계 SSOT 반전 + @header/변경이력

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | F-005 — `state-template.md`(34/40/82) 반전, README·@header·변경이력 072 |
| 계층 | L1 |
| **실행 방식** | M1 (도구 — grep 산출물 검사) |
| 조건 | 소스 문서에 대해 grep/검사 |
| 기대 결과 | ①`state-template.md`에 "다음 액션 …수동…(state-tool 범위 밖)" 문언 잔존 0건 ②README init/advance/mark에 `next_action`·자동 파생·`--next-action` 반영 ③변경이력 표에 `(072)` 행 + KST 일시 ④state_tool.py @header에 072 요약 |
| 도구 | grep / 산출물 검사 |
| 실행 명령 | `grep -n "다음 액션.*수동" opal/core/references/harness/state-template.md; grep -n "072" opal/tools/state-tool/README.md opal/tools/state-tool/state_tool.py opal/core/references/harness/state-template.md` |
| 결과 | **Pass** |
| 상세 | ① `state-template.md:34,40`(현재 설계 섹션)는 "다음 액션…자동 파생·갱신"으로 반전 완료 — 유일 매치는 `:114` 변경이력 행이 舊설계 문구("다음 액션은 PM 수동 갱신")를 **인용**하여 반전 사실을 기록한 것(의도된 히스토리 기술, stale 잔존 아님). 현재 유효 설계 문언(34/40/82행)에 "수동" 잔존 0건 확인 ② README.md:56,92,99,115,125,353에 `next_action`/자동 파생/`--next-action` 오버라이드 반영 확인 ③ 변경이력에 `v1.6 2026-07-23 12:09 (072)` 행 존재(state-template.md:114, README.md:353 동일 KST 일시) ④ state_tool.py:6 @header에 "072: STATE.md '다음 액션' 자동 파생 …" 요약 반영, 코드 내 072 태그(318/365/453/934/1144/1290/2157/2185) 다수 확인 |

#### S-12: install 배포본-소스 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | F-005 — `./scripts/install-mac.sh` 재실행 후 배포본 정합 |
| 계층 | L1 |
| **실행 방식** | M1 (도구 — diff) |
| 조건 | install 실행 후 `~/.opal/tools/state-tool/state_tool.py`·`schema/state.schema.json`과 소스 비교 |
| 기대 결과 | 배포본-소스 diff 0(변경이력 섹션 strip 제외) |
| 도구 | diff / bash |
| 실행 명령 | `./scripts/install-mac.sh && diff opal/tools/state-tool/state_tool.py ~/.opal/tools/state-tool/state_tool.py && diff opal/tools/state-tool/schema/state.schema.json ~/.opal/tools/state-tool/schema/state.schema.json` |
| 결과 | **Pass** — install exit 0(`OPAL 설치 완료 (v0.6.10-2-gdafac7e)`), 양쪽 diff 모두 exit 0 / 출력 0줄 |
| 상세 | `state_tool.py` 소스-배포본 diff 0줄(변경이력 strip 여부와 무관하게 완전 일치 — 072 @header 요약 포함 동일), `state.schema.json` 소스-배포본 diff 0줄. 배포본-소스 드리프트 없음 확인(H-6 해소) |

### L2. 프로세스 통합

해당 없음 — 단일 Python CLI 도구의 단위 동작 검증이며, DB read→CUD→re-read 통합 흐름·다중 서비스 연동이 없다. FE 화면/컴포넌트·인증/인가·외부 API 연동 부재로 M2(E2E 자동화) 의무 트리거 미해당(`test-scenario-guide.md` §Step 3-b).

### L3. 사용자 협업

해당 없음 — 전 시나리오가 unittest/도구로 자동 검증 가능하다. [SUPERVISOR] 수동 확인이 필요한 FE 플로우·외부 시스템 연동이 없다.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 (state.json next_action) | H-4 | L1 | S-1 | `test_state_tool.py`:`TestNextActionAutoDerive` [T072/L1-R1] | init 영속+schema optional+하위호환 |
| R-2 (자동 파생) | H-2 | L1 | S-2, S-3 | `test_state_tool.py`:`TestNextActionAutoDerive` [T072/L1-R2] | 프론티어 파생+전체완료 경계 |
| R-2 / M-1 (첫줄치환) | H-3 | L1 | S-4 | `test_state_tool.py`:`TestNextActionAutoDerive` [T072/L1-M1] | 자유기재 보존 |
| R-2 / H-5 (계약보존) | H-5 | L1 | S-5 | `test_state_tool.py`:`TestFreeTextPreservation`(유지) [T072/L1-H5] | block/add-row 미접촉 |
| R-3 (렌더 반영) | H-2 | L1 | S-2 | `test_state_tool.py`:`TestNextActionAutoDerive` [T072/L1-R3] | state.json↔STATE.md 정합 |
| R-4 (오버라이드) | H-2 | L1 | S-6, S-7 | `test_state_tool.py`:`TestNextActionAutoDerive` [T072/L1-R4] | 우선순위+M-3 비지속 |
| R-5 (테스트) | H-1 | L1 | S-8, S-9, S-10 | `test_state_tool.py`:`TestNextActionAutoDerive`·`TestFreeTextPreservation`(반전) [T072/L1-R5] | RED-first+반전+베이스라인 |
| R-6 (문서·배포) | H-6 | L1 | S-11, S-12 | (산출물 검사) [T072/L1-R6] | SSOT 반전+배포 정합 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 구문 검사 | `py_compile` | Pass | `state_tool.py`·`test_state_tool.py` 컴파일 exit 0 |
| 1-보조 | 린트 | `ruff check`(프로젝트 미설정, 기본값 적용) | Pass(신규 코드 위반 0) | 전체 14건 검출(F401/F841/F541/E402) — 전부 072 변경 범위 밖 기존 코드(state_tool.py:24,679,1350,1394 / test_state_tool.py:37,42,556,823,906,1352,2690,3305) 소재 확인, 신규 072 추가분(state_tool.py:318,365,453,934,1144,1290,2157,2185 / `TestNextActionAutoDerive` 1588-1844행)에는 위반 0건. 회귀 판정에서 이 14건은 072와 무관한 기존 부채로 제외 |
| 2 | 타입 체크 | 해당 없음 | 해당 없음 | 프로젝트에 mypy 설정/의존성 부재(`which mypy` 없음, pyproject.toml/mypy.ini 없음) — 스킵 |
| 3 | 포맷터 | 해당 없음 | 해당 없음 | 프로젝트에 black/ruff-format 설정 부재(`which black` 없음) — 스킵 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | 7개 changed_files 대상 `api_key/secret/password/token/Bearer=값` 패턴 grep — 매치 0건(exit 1) |
| 2 | .gitignore 확인 | Pass | `.env`·`.venv`·`__pycache__`·`.ruff_cache`·`.mypy_cache` 등 민감·산출물 경로 커버 확인. changed_files는 전부 소스 트리(`opal/`) 내부로 무관 |
| 3 | `--next-action` 입력 정규식 치환 시 섹션 경계 오염 방지(`[^\n]*` 개행 미포함) | Pass | `update_next_action_section`(state_tool.py:317-327) 정규식 `r"(^## 다음 액션\n)([^\n]*)"` — 캡처그룹2가 `[^\n]*`로 개행 미포함, 헤더 다음 첫 줄까지만 매치·치환. S-4 테스트(하위 자유기재 보존) GREEN으로 실증 확인. 섹션 부재 시 미변경(fail-safe) 확인 |

## 7. 판정

**All Pass** -- S-1~S-9, S-11, S-12 전부 GREEN(exit 0, 실행 로그 증거 첨부). S-10 전체 스위트는 exit 1이나 유일 실패인 `TestVerify.test_verify_passes_own_test_scenario_md`가 034 태스크 폴더 이동(`tasks/backup/034-...`)으로 인한 072 변경과 무관한 사전 존재 실패임을 경로·에러 메시지로 확인했으므로 이를 제외하면 249 pass(신규 9 + 반전 5 포함) — 회귀 없음. S-8 RED-first 트랙은 사전 기록된 RED(9 tests, 8 fail)에서 구현 후 재실행 GREEN(9 tests, 0 fail) 전환을 실행 로그로 확인. 코드 품질(§5): py_compile Pass, ruff 14건 전부 072 변경 범위 밖 기존 코드로 신규 위반 0건, 타입/포맷터는 프로젝트 미설정으로 해당 없음. 보안(§6): 하드코딩 시크릿 0건, .gitignore 정상, 정규식 섹션 경계 보호(`[^\n]*`) 확인. 배포 정합(S-12): diff 0.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (실 init/advance/mark 호출 + 실 파일 검증)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (전 시나리오 L1, L2/L3 해당 없음 근거 명시)
- [x] L3 [SUPERVISOR] 마커 — 해당 없음(전 시나리오 자동 검증, 근거 명시)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전 (H-1~H-6 전부 매핑)
- [x] 모든 시나리오에 실행 방식(M1) 명시
- [x] FE 변경 M2 의무 — 해당 없음(FE/인증/외부 API 부재, §L2 근거 명시)
