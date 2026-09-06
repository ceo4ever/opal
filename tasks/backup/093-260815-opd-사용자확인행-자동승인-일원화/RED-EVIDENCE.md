# RED EVIDENCE: 파이프라인 사용자 확인 행 — 자동 승인 경로 일원화

> 실행 시각: 2026-08-15 21:15 (KST, `~/.opal/tools/date/date.js datetime`)
> 작성자: `opal-test-agent` (mode: red) — PLAN/EXECUTE 작성자와 분리 (red-first.md §2 작성자≠구현자)
> 코드 루트: `/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_093/`
> 대상 파일: `opal/tools/state-tool/tests/test_state_tool.py` (기존 파일에 **순수 추가** — 기존 케이스 수정·삭제 0건)
> 구현체(`state_tool.py`) 수정: **0줄** (red-first.md §2)

---

## 1. 실행 명령

```
cd /Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_093
python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q
```

## 2. 실행 결과 (exit code ≠ 0)

```
19 failed, 296 passed, 54 subtests passed in 14.19s
```

신규 케이스만 선별 실행:

```
python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q -k T093
→ 18 failed, 6 passed, 291 deselected, 22 subtests passed in 10.55s
```

## 3. 착수 전 baseline (git stash로 실측)

```
python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q   # 신규 케이스 제거 상태
→ 1 failed, 290 passed, 32 subtests passed in 3.94s
```

- **기존 케이스 통과 수: 290 → 290 (회귀 0건).** 추가 후 296 pass = 기존 290 + 신규 GREEN 6.
- baseline의 `1 failed`는 **선행 결함**이며 본 태스크 소관이 아니다:
  `TestVerify::test_verify_passes_own_test_scenario_md` —
  `034 TEST-SCENARIO.md 파일이 없음 (탐색: <worktree>/tasks/034-.../TEST-SCENARIO.md)`.
  worktree가 sparse checkout(42%)이라 `tasks/`가 존재하지 않아 발생하는 **환경 의존 실패**다.

---

## 4. 신규 케이스 목록 (18건 함수 + 서브테스트 22건)

### 4.1 RED — 구현체 부재가 유일한 실패 원인 (18건 중 12 함수 + 6 함수)

| # | 시나리오 | 케이스 (클래스::함수) | 실패 사유 (실제 출력 요약) |
|---|---------|--------------------|--------------------------|
| 1 | S-2 | `TestT093AutoNaRemoval::test_auto_na_marker_absent_in_source_T093_L1_F1a` | `'agentic auto-na at init' 라인 [829, 921, 1055]` — F-001 미착수 |
| 2 | S-3 | `TestT093AutoNaRemoval::test_three_modes_init_rows_identical_T093_L1_F1b` | `S-3/agentic: row 2(TASK) status='na', 기대 'pending'` |
| 3 | S-4 | `TestT093AutoNaRemoval::test_all_three_builders_init_pending_T093_L1_F1b` | `S-4(a) rows-spec: row 1(TASK) status='na', 기대 'pending'` |
| 4 | S-1 | `TestT093AutoApproveHook::test_pipeline_traversal_auto_approves_T093_L2_GOAL` | `S-1 task.user_confirm status=na` (관통 후 done/auto 미달) |
| 5 | S-5 | `TestT093AutoApproveHook::test_hook_fires_without_auto_pass_flag_T093_L2_F2` | 훅 부재 — ANALYSIS user_confirm이 `na`(done/auto 아님) |
| 6 | S-13 | `TestT093AutoApproveHook::test_semi_agentic_post_execute_auto_approved_T093_L1_F3` | `stage_transition_violation ... 앞 행 [2]이(가) 완료되지 않았음` — 훅 미배선 |
| 7 | S-26 | `TestT093AutoApproveHook::test_auto_approved_payload_positive_T093_L1_F2o` | `auto_approved` 필드 부재 (`None != [2]`) |
| 8 | S-6 | `TestT093AutoApproveBoundary::test_close_entry_does_not_auto_approve_T093_L2_GOAL` | `S-6 전제: TEST 사용자 확인 행은 init 직후 pending` — 현재 `na` |
| 9 | S-8 | `TestT093AutoApproveBoundary::test_worker_path_hook_disabled_T093_L2_GOAL` | 동상 — PLAN user_confirm이 init 시 `na` |
| 10 | S-9 | `TestT093AutoApproveBoundary::test_worker_path_leaves_file_byte_identical_T093_L2_GOAL` | 동상 |
| 11 | S-12 | `TestT093AutoApproveBoundary::test_semi_agentic_boundary_requires_user_T093_L1_F4` | `'stage_transition_violation' != 'user_confirmation_required'` — F-004 에러 코드 부재 |
| 12 | S-24 | `TestT093AutoApproveBoundary::test_interactive_path_split_T093_L1_F4` | 동상 (`reason == interactive_requires_user` 미방출) |
| 13 | S-10 | `TestT093HookGuardOrder::test_guard_failure_leaves_file_unsaved_T093_L2_F2` | `s10-gate 전제: 사용자 확인 행은 init 직후 pending` — 현재 `na` |
| 14 | S-11 | `TestT093HookGuardOrder::test_failed_response_has_no_auto_approved_T093_L1_F2o` | 동상 |
| 15 | S-15 | `TestT093MarkIdempotency::test_auto_pass_note_prefix_applied_once_T093_L1_F5` | 접두 보유 note 재전달 시 `agentic auto-pass: agentic auto-pass: …` 중첩 |
| 16 | S-16 | `TestT093MarkIdempotency::test_re_auto_pass_is_noop_T093_L1_F5` | `S-16 idempotent 미표기` — 재-auto-pass no-op 조기 반환 부재 |
| 17 | S-25 | `TestT093SingleDecisionSource::test_mode_boundary_stages_single_reference_T093_L1_F3s` | `참조 2곳 — (1527, cmd_mark), (1727, cmd_validate)` |
| 18 | S-25 | `TestT093SingleDecisionSource::test_decision_function_contract_T093_L1_F3s` | `판정 함수 can_auto_approve_user_confirmation 부재` |

> 18건 전건의 실패 원인이 **F-001~F-005 미구현**이며, 테스트 자체의 결함(픽스처 오류·경로 오류)은 0건이다.
> 실패 원인이 명세 밖 축(005 명확화 게이트)이던 초기 2건은 픽스처를 교정해 해당 축을 제거했다(주석 명기).

### 4.2 GREEN-by-design — 경계 불변/하위호환 (6건, 22 서브테스트)

RED-first §1은 "신규 계약"에 실패 증거를 요구한다. 아래 6건은 **변경 전후가 동일해야 하는 경계**를
고정하는 회귀 케이스이므로 지금 통과하는 것이 정상이며, GREEN 이후에도 통과해야 한다.

| 시나리오 | 케이스 | 역할 |
|---------|-------|------|
| S-14 표 A | `TestT093AutoApproveBoundary::test_boundary_table_a_mark_auto_pass_T093_L1_F3` | B-1~B-9 9셀 subTest — exit code + `error` 문자열 대조 |
| S-14 표 B | `TestT093AutoApproveBoundary::test_boundary_table_b_validate_T093_L1_F3` | V-1~V-9 9셀 subTest — V-8·V-9는 `violations_count == 0` (H-4 핵심) |
| S-7 | `TestT093AutoApproveBoundary::test_close_first_row_auto_pass_denied_T093_L1_F3` | agentic·semi-agentic 2 subTest — `agentic_close_gate_requires_user` 불변 |
| S-18 | `TestT093AutoApproveBoundary::test_close_done_auto_validate_no_violation_T093_L2_F6a` | CLOSE `done/auto` 신규 오탐 0 (H-4) |
| S-16 대조군 | `TestT093MarkIdempotency::test_noop_control_groups_T093_L1_F5` | `owner=user` / `--force` / `--action-step` 3종이 no-op에 삼켜지지 않음 |
| S-17 | `TestT093NaBackwardCompat::test_existing_na_state_json_still_operable_T093_L2_F6a` | 092 **스냅샷 픽스처(주)** + **실파일 복사본(부가)** 양쪽에 validate→add-row/advance→mark 3종 exit 0 |

---

## 5. 검증 방식 준수 확인

- [x] `mock` / `patch` / `MagicMock` 미사용 — 신규 블록 전건이 `run.sh` subprocess 실호출(`_run070`) +
      실 `state.json` 파일 재로드로만 관찰한다. 시각도 실 `date.js`를 통과한 KST 값을 쓴다.
- [x] 내부 구현·private 결합 없음 — 관찰 대상은 exit code / stdout JSON / `state.json` 파일 상태 /
      `state_tool.py` 소스 텍스트(S-2·S-25 구조 검사) 뿐이다.
- [x] 실 데이터 사용 — `opal/skills/opal-pilot-dev/references/pipeline.json`(S-1·S-3·S-4·S-5),
      `tasks/092-260815-opd-워크트리-작업공간-분리/state.json`(S-17, **읽기 전용 + 원본 바이트 대조 assert**).
- [x] 실패 입력·경계조건 포함 — S-6~S-12·S-24는 전부 거부 경로다.
- [x] 기존 케이스 수정·삭제 0건 (PLAN Step 7/9의 기존 3건 수정은 GREEN 구현 워커 몫).
- [x] `TEST-SCENARIO.md`의 "실행 명령" 칸은 비워 둔 채로 유지 (EXECUTE 워커 몫).
- [x] tmp 작업 폴더는 `tempfile.mkdtemp()` 하위 — 레포/`~/.opal/`/본 태스크 state.json 미접촉.
      tmp에는 `.opal/MEMORY.json`이 없어 CLOSE 마지막 행 mark의 `link_memory_history()`가
      `skipped`로 무해하게 끝난다(실 메모리 파일 미오염).

---

## 6. 변경 이력 — S-17 스냅샷 픽스처 전환 (PM 판정 ② 반영)

> 반영 시각: 2026-08-15 21:22 (KST) | 지시: PM 추가 지시 "②만 반영"

### 6.1 전환 사유

전환 전 S-17은 `tasks/092-*/state.json` **실파일에만** 의존했고, 미탐색 시 `skipTest`로
빠졌다. 092가 `tasks/backup/`으로 아카이브 이관되면 시나리오 전체가 **조용히 무력화**되어
"검증하지 않은 것이 통과로 보이는" 상태가 된다 — 헌법 §4 위반 경로다. PM 판정에 따라
스냅샷 픽스처를 **주 경로**로 승격하고 `skipTest` 경로를 제거했다.

### 6.2 전환 후 구조 (케이스 1건, subTest 2개)

| 경로 | 실행 조건 | 내용 |
|------|----------|------|
| 주 — `subTest(source="snapshot")` | **무조건 실행** | 파일 내 동봉 `_SNAPSHOT_092` 딕셔너리 → tmp state.json. STATE.md는 손으로 쓰지 않고 **실 CLI `init` 산물**을 사용해 마커 계약을 위조하지 않는다 |
| 부가 — `subTest(source="real-file")` | 실파일 탐색 성공 시 | 실파일 복사본에 동일 검증 + 원본 **바이트 대조**로 읽기 전용 제약 증명. 탐색 경로에 `tasks/backup/`을 추가 |

두 경로 모두 공통 헬퍼 `_exercise_na_state()`를 타므로 검증 강도가 갈리지 않는다:
`validate`(violations 0) → `add-row` → `advance` → `mark --done` 3종 exit 0 +
**기존 `na` 행이 소급 변환되지 않음**(PLAN §3.1.4 미마이그레이션 계약) 확인.

### 6.3 스냅샷이 보존한 특징 (실파일에서 그대로 발췌한 값)

| # | 특징 | 근거 행 |
|---|------|--------|
| ① | `status="na" / status_label="-" / owner="auto" / note="agentic auto-na at init"` | row 2 `task.user_confirm` — F-001 구형 산물 |
| ② | `status="done" / owner="auto"` + note에 `agentic auto-pass:` 접두 **중첩** | row 4 `analysis.user_confirm` — ANALYSIS §4 #5 실측 결함(원문 `state.json:71`) |
| ③ | `status="done" / owner="user"` (CLOSE 게이트 요건 충족 행) | row 6 `test.user_confirm` |
| ④ | `schema_version: "1.1"` · `mode: "agentic"` · `skill: "opd"` | root |
| ⑤ | task-step key 체계(`stage_slug.item_slug`) 전 행 부여 | rows 1~8 |
| ⑥ | CLOSE stage에 `add-row` 산물(`close.item_1`, 추가작업 행) 존재 | row 8 |
| ⑦ | root 필드 구성 9종(`task_id`/`skill`/`mode`/`schema_version`/`created_at`/`updated_at`/`current_status`/`rows`/`next_action`) | root |

축약은 **행 수만** 17 → 8로 줄였고(각 stage 대표 행 유지), 필드 구성·값 형식·상태 조합은
원본 그대로다. 실측 전제(`na` 행 존재 / 접두 중첩 행 존재)는 헬퍼 초입에서 assert로 고정해,
스냅샷이 훼손되면 테스트가 조용히 통과하지 않고 실패한다.

### 6.4 전후 케이스 수

| 항목 | 전환 전 | 전환 후 |
|------|--------|--------|
| 신규 테스트 함수 | 18 | **18 (불변)** |
| 신규 subTest 셀 | 22 | **24** (S-17이 snapshot/real-file 2셀로 분리) |
| 전체 스위트 | `19 failed, 296 passed, 54 subtests passed` | `19 failed, 296 passed, **56** subtests passed` |
| T093 선별 | `18 failed, 6 passed, 22 subtests` | `18 failed, 6 passed, **24** subtests` |
| 기존 케이스 통과 | 290 | **290 (유지, 회귀 0건)** |
| `state_tool.py` 변경 | 0줄 | **0줄** |
| `skipTest` 경로 | 1건 | **0건** |

> PM 판정 ①(`TestVerify::test_verify_passes_own_test_scenario_md`)은 지시대로 **손대지 않았다.**
> 해당 1건은 sparse-checkout 환경 의존 실패이며 PM이 S-19 완료기준에 명시적 예외로 기재한다.

---

## 7. GREEN 진입 조건

위 4.1의 18건이 전부 통과하고, 4.2의 6건(22 서브테스트)이 계속 통과하며,
baseline 290건이 감소하지 않아야 한다(DEC-F 삭제 0건).
