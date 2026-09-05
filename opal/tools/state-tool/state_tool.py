"""
@header {
  "module": "state_tool",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "OPAL 파이프라인 현황판 JSON SSOT 관리 CLI — 10개 서브 명령(init/show/advance/mark/block/validate/add-row/status/spec-validate/gate-pass[deprecated]) + verify + 3-way 모드(interactive/semi-agentic/agentic) 지원. 014 Phase 4: 새 표준 행 구조(QA Gate/State Gate 행 없음)와 정합 — gate-pass deprecate, CLOSE 마지막 행 판정 항목명 비의존화. 016: verify --red-check(RED 증거 게이트) + --fix-mode/--changed-files/--test-globs(테스트 불변성 게이트) 추가 — RED-first TDD 트랙 deterministic 집행. 017: mark --step N/M 다중 Step 조기 done 가드 — N<M이면 in_progress 유지(done 미처리) + 진행률(step) 영속화, N==M에서만 done; 미완 행은 기존 stage-transition guard가 단계전환·CLOSE 진입을 자동 차단. 005: verify --clarification-check + TASK→다음단계 자동 훅 — TASK 4요소(목표/범위/제약/완료기준) 미잠금 시 다음 단계 진입 거부(PRINCIPLES §1 집행), 정책 A graceful skip(섹션/파일 부재 시 하위호환). 034: mock 가드 false positive 수정 — _MOCK_CODE_PATTERNS 정규식 'MagicMock' 맨 단어 대안 제거(#1 산문 오탐) + _check_mock_patterns 인라인 백틱 제거 전처리 추가(#2 메타-순환 해소); 헌법 §4 정탐 유지. 054: resolve_owner_placeholder() 신설 — note-write 6경로(advance/mark/add-row/block/status/init)에서 '{owner_name}' 플레이스홀더를 identity.md owner_name으로 write-time 치환(fail-safe: 부재/공란/파싱실패 시 원문 유지). 070: task-step 키 주소 체계 도입 1차 — spec-validate 서브명령(pipeline.json 스펙 검증) + KEY_PATTERN/stage_to_slug/resolve_row_index 신설, build_rows_from_pipeline_json(init --rows-from .json 확장자 분기, .md는 deprecation 경고 유지), advance/mark/block에 --task-step/--task-step-id/--row(deprecated) 3주소·add-row에 --after-task-step/--after-task-step-id/--key(자동 생성) 추가, --step→--action-step 별칭(dest 공유), opdd skill·DICT/MODEL/DDL·MIGRATION stage enum 등록, ERROR_CODES 8종 추가. 072: STATE.md '다음 액션' 자동 파생 — state.json next_action 필드 신설(init 영속화·schema optional 등록), _derive_next_action(파이프라인 프론티어=첫 미완료 행 기준 파생)·update_next_action_section(첫 줄만 치환, 하위 자유기재 보존) 신규, advance/mark가 상태 반영 후 next_action 계산·저장·렌더(block/add-row/status는 미접촉), advance/mark --next-action per-transition 오버라이드(비지속 — 다음 전이 자동 파생 복귀). 074: --import-existing key-보존 재접합 — cmd_init import 분기가 파싱 후 기존 state.json→pipeline.json (stage,item) 순서 매칭으로 key 재접합(schema_version 1.1 유지), 원천 전무 시 keyless+경고(하위호환); _key_source_index/_reattach_import_keys 신규. 076: build_todo_mirror() 신설 — init/advance/mark/block ok() stdout 페이로드에 단계 단위 todo 미러(파생: na 중립·전부pending→pending·전부done→completed·부분/failed→in_progress) 추가, PostToolUse hook이 이를 세션에 결정론 주입(파이프라인 todo 미러 hook 강제); todo_mirror는 stdout 전용 비영속(state.json 미접촉 — schema additionalProperties:false 보존). 088: CLOSE 마지막 행 mark 시 메모리 히스토리 자동 연결 — link_memory_history()가 형제 memory_tool.py를 sys.executable subprocess로 호출해 `<프로젝트루트>/.opal/MEMORY.json` history에 행을 자동 생성(find_project_root 조상 탐색·derive_history_title·build_history_reminder·_run_memory_tool 신설), path 사전 조회로 멱등 보장, 예외/실패 전부 흡수해 mark는 항상 ok:true 유지(cmd_mark ok() stdout에 history_link 필드 조건부 추가, state.json 미접촉). 091: PM Gate 집행 배선(F-004) — validate_pipeline_spec()에 task_steps[].gate 검사 4건 추가(spec_gate_type_invalid/spec_gate_missing_field/spec_gate_field_type_invalid/spec_gate_checklist_empty, artifacts:[] 단독은 위반 아님); _is_safe_artifact_token()·check_gate_artifacts() 신설 — gate.artifacts 존재 검증(정적 경로/글롭 지원, 절대경로·'..' 토큰 태스크 폴더 밖 이탈 차단), gate 미보유 행·artifacts:[] 행은 즉시 통과(기존 동작 불변), 미충족 시 gate_artifact_missing 거부(--force+--note로만 우회 가능, 우회 시 decision 로그 gate_artifact_force 강제 기록); build_gate_payload() 신설 — 통과 시 checklist를 dict로 stdout 반환(todo_mirror_hook 릴레이용); build_rows_from_pipeline_json()/build_rows_from_spec()에 gate 필드 init-time 영속화 각 1줄 추가; cmd_mark가 save_state_json() 이전 검증 구간에서 가드를 호출하여 부분 상태 변경을 배제하고 _ok_kwargs에 gate_checklist 조건부 추가; ERROR_CODES 5종 신규(gate_artifact_missing 포함). 092: `init --worktree <path>` 조건부 영속화(F-005) — argparse `init`에 `--worktree` optional 인자 추가, cmd_init이 state dict 구성 직후 `getattr(args, \"worktree\", None)`으로 조건부 대입(미지정 시 키 자체 미생성 — H-1), state.schema.json properties에 `worktree` optional 등록(required 미변경); `_build_new_state_md`/`render_pipeline_table`/`build_todo_mirror`/`cmd_show` 무변경으로 STATE.md 렌더·`show --format json` 노출 하위호환 보장(H-11). 093: 사용자 확인 행 자동 승인 경로 일원화 — can_auto_approve_user_confirmation() 신설(F-003, CLOSE 축 + 모드 축 2축 합성 단일 판정; semi-agentic 모드 경계 상수의 유일 참조자이며 cmd_mark 사전검사와 cmd_validate 사후검사가 거부 사유별로 소비 범위를 달리한다 — validate는 include_close_axis=False로 CLOSE 축을 평가하지 않아 기존 경계를 보존, H-4); auto_approve_prior_user_confirmations() 신설(F-002, cmd_advance·cmd_mark가 stage-transition guard 직전에 호출해 대상 행 앞 [0,row_index) 구간의 미완 '사용자 확인' 행을 done/auto/timestamp로 자동 승인하고 note에 'auto-approved on <stage> entry' 기록 — as_worker/force/대상 행 stage=CLOSE면 즉시 no-op이고 save_state_json을 호출하지 않아 후속 가드 실패 시 파일이 오염되지 않는다(H-8), 승인 불가 구간은 user_confirmation_required로 거부(F-004)); advance/mark ok() 응답에 auto_approved 배열 관측 필드 추가(기존 필드 불변); build_rows_from_spec/build_rows_from_skill_md/build_rows_from_pipeline_json의 init 시점 agentic auto-na 분기 3곳 삭제(F-001 — 전 모드 pending/⬜/PM 동형 초기화; 세 빌더의 mode 파라미터 시그니처, state.schema.json status enum의 na, _COMPLETE_STATUSES, build_todo_mirror na 필터는 하위호환으로 존치, R-6); cmd_mark 멱등성(F-005) — _AUTO_PASS_PREFIX 모듈 상수 신설 후 auto-pass note를 3분기(빈 note/이미 접두 보유→중첩 방지/신규 부여)로 부여하고, check_gate_artifacts 통과 직후 재-auto-pass no-op 조기 반환(auto_pass and not force and not action_step and status=='done' and owner=='auto' 4중 조건 — 상태·timestamp·updated_at 불변, 응답에 idempotent:true; --force·--action-step N/M·owner=user done 행은 기존 경로 유지). 094: STATE.md를 state.json 파생 섹션(마커/파이프라인 표/'## 현재 상태'/'## 다음 액션') 없는 저널(의사결정 로그+블로커)로 재정의 — `_build_new_state_md` 2인자 축소·`ensure_journal_skeleton` 신설·`sync_state_md` fail-open 축소판 재작성(6개 호출부 인자 정리, journal_warning 조건부 stdout 표면화)·`append_decision_log` 오프바이원 수정+표 셀 이스케이프(`_escape_table_cell`)·`replace_pipeline_section`/`update_current_status_section`/`update_next_action_section` 삭제·`ERROR_CODES`에서 `marker_missing`/`import_failed` 삭제 후 `import_existing_removed` 추가·`cmd_init` import 분기·`parse_existing_state_md`/`_key_source_index`/`_reattach_import_keys` 삭제(--import-existing은 help=SUPPRESS로 존치, 항상 거부)·`cmd_validate` 마커 검사 삭제·`cmd_show` md/full 3분기를 state.json 단일 파생으로 재설계(`LEGACY_FROZEN_BANNER`, `STATUS_TEXT`)·`render_pipeline_table`에 '비고'(note) 열 추가 — `render_pipeline_table`/`PIPELINE_MARKER_*`/`update_state_md_header`는 레거시(001~093) STATE.md 공존을 위해 존치. 094 R-11: 093 집행 층(can_auto_approve_user_confirmation 단일 판정) 일원화를 표시·게이트 층에 정합 — G-1) 모드 경계 상수에 `DICT`/`MODEL`/`DDL/MIGRATION` 3원소 추가로 semi-agentic(기본 모드) opdd에서 설계 확정 3단계가 소유자 미노출로 자동 승인되던 주권 침해 해소; G-2) `check_close_gate`에 확인 행 0개 파이프라인(opgc) 폴백 신설 + `owner` 인자 추가(CLOSE 첫 행 자체를 소유자 승인 지점으로 삼아 `--force` 없이 종료 불가하던 데드락 해소); G-3) `_derive_next_action`·`build_todo_mirror`가 `can_auto_approve_user_confirmation()`을 재사용해 자동 승인 예정 사용자 확인 행을 각각 프론티어/집계에서 제외(CLOSE 직전은 예외 유지)해 agentic 헛 확인 신호 소멸. 094 SEC-FOLLOWUP: `sync_state_md` except 절이 `journal_warning.reason`에 예외 메시지(`str(e)`)를 원문 그대로 담아 태스크 절대경로·홈 디렉토리 경로를 노출하던 결함(PLAN.md §5.4) 수정 — `_redact_path_like()` 신설(공백 토큰 단위로 `/` 또는 홈 경로로 시작하는 조각을 `os.path.basename`으로 치환, 특정 OS/Errno 포맷 비가정) 후 except 절 `reason` 조합에 적용; 예외 타입명·파일명(예: `STATE.md`)은 보존해 진단 가치 유지, `decision`/`note` 필드는 미접촉. 098: `verify --evidence-check` 신설(F-003) — TASK.md '## 명확화 결과' 표의 '의존 사실' 셀을 근거 등급 4축(인용 존재·인용 유효·등급 부여·E5 단독 아님)으로 판정해 항목별 확정/미확정+사유를 반환하는 라우터(항상 exit 0, 차단 없음); `_locate_clarification_table()` 신설(표 탐색 전용, H-8) 후 `_parse_clarification_table()`을 그 위에 얇게 재구성(dict 반환 계약 불변)·`_extract_citations()`/`_grade_citation()`/`_check_evidence_gate()` 신규(인용 형식 4종 파싱: `경로:N`/`경로` §N/`[사이트](URL)`/`(→ D-N §N)`, 등급 패턴 기본 세트 E5/E4/E2/unknown, `unknown`은 `confirmed_ratio`에서 미확정 계상), `cmd_verify`가 `clarification_check` 분기 뒤·`fix_mode` 분기 앞에서 처리하며 `--clarification-check`와 동시 지정 시 `evidence_check_flag_conflict`로 거부(ERROR_CODES 44→45); `_grade_citation`의 경로 실존 검사는 `_is_safe_artifact_token()`을 재사용해 절대경로·`..` 이탈 토큰을 미존재로 fail-safe 처리. 098 ADD-2: `_resolve_citation_exists()`가 프로젝트 루트를 스크립트 자기 위치(`__file__`)에서 파생해 배포본(`~/.opal/tools/state-tool/`) 실행 시 root=None → 정규 인용 전건 오강등되던 결함 수정 — `_check_evidence_gate`가 `find_project_root(task_md_path)`를 우선 시도하고 실패 시 기존 `__file__` 파생으로 폴백하는 `root`를 1회 계산해 `_evaluate_evidence_item`→`_grade_citation`→`_resolve_citation_exists`로 트레일링 옵셔널 인자로 전달(세 함수 시그니처에 `root=None` 각 1개 추가, 기존 2-인자 호출 형태 하위호환); 폴백까지 실패한 `root=None`은 기존 fail-safe(미존재 처리) 그대로 유지. 100: `verify --evidence-check` 파싱 대상 확장(F-007, PLAN §3.7.2) — `_locate_confirmed_direction_items()` 신설(`_locate_clarification_table`의 형제 함수, 표가 아닌 불릿 리스트 전용 파서: `## 확정된 설계 방향` 섹션의 최상위 불릿만 수집하고 중첩 불릿·그 이어쓰기 행은 비수집, 섹션 부재 시 None·항목 0건 시 [] 반환, `element`에 불릿 본문 원문 보존 — 인덱스형 불투명 라벨 금지)·`_has_fact_tag()`/`_CONFIRMED_VERDICTS` 신설, `_evaluate_evidence_item()`의 4축 통과 분기가 `[사실]` 태그 보유 시 verdict `승계`를 반환(상류 대조 확인 승계 — 재확인 면제, 계수상 `확정`과 동등; 태그 없는 기존 항목은 `확정` 그대로), `_check_evidence_gate()`가 두 소스를 하나의 `items[]`로 병합하며 각 항목에 `source`(`clarification`|`confirmed_direction`) 필드 부여 + 신규 키 `direction_confirmed_ratio` 반환(섹션 부재·항목 0건 시 None — 분모 0 나눗셈 없음), **기존 `confirmed_ratio`의 분모는 `## 명확화 결과` 항목 수로 불변**(PD-1 분리형 — 분모 확대는 소비자를 조용히 깨뜨린다), `cmd_verify` evidence 분기 JSON에 신규 키 1줄 추가(플래그 신설 없음·`evidence_check_flag_conflict` 로직 불변·exit 0 3경로 불변). 103 R-15: 워커 소요 계측 필드 신설 — `state.schema.json` rows[].items.properties에 `worker_duration_minutes`(integer, minimum 0) **선택** 등록(required·additionalProperties:false 불변), `_worker_duration_minutes()` argparse type 파서 신설(음수·소수·비수치를 파싱 시점 exit 2로 거부 — `--owner` choices와 동일 계열이므로 ERROR_CODES 신설 없음, 45종 불변), `mark --worker-duration-minutes <n>` 인자 추가 후 cmd_mark가 지정된 경우에만 `row[\"worker_duration_minutes\"]` 기록 + ok() stdout에 동명 키 조건부 추가(미지정 호출은 state.json·응답 키 집합 모두 종전과 바이트 동일 — H-1/H-11); 093 F-005 재-auto-pass no-op 조건에 `_worker_minutes is None`을 더해 값이 실린 호출이 조용히 버려지지 않게 했다(기존 호출은 항상 None이라 조건 동형). 미기록 행은 집계에서 PM 계열로 전액 축퇴한다(103 집계 기준 16/16-a/16-b). 103 R-19: 시각 해상도 초 확장 — `get_kst_datetime`이 date.js `datetime-sec`(신규 포맷, 순수 additive)를 1순위로 요청하고 형식 불일치 시 `datetime`(분)으로 폴백해, 배포본이 아직 신규 포맷을 모르는 구간에도 종전 값을 그대로 낸다(`TS_PATTERN_SEC`/`TS_PATTERN_MIN`·`_date_js_path`·`_run_date_js` 신설, date.js 경로는 형제 배치 우선 해석이라 배포 레이아웃에서는 종전과 동일 경로). `state.schema.json`의 `created_at`·`updated_at`·`rows[].timestamp` pattern에 `(:\\d{2})?`를 더해 초 있음/없음을 모두 수용한다 — 기존 분 해상도 기록 전건이 그대로 통과하며, 집계는 초 부재를 `:00`으로 읽어 분 단위 차분이 항등이다. 103 R-21: 워커 소요 누락 경고 — `WARNING_CODES`(ERROR_CODES와 분리된 신규 사전, 45종 불변) 1종(`worker_duration_missing`)과 `build_worker_duration_warning()` 신설, `mark`가 워커 디스패치 행(`--as-worker` 또는 `--worker-stage`)을 `done`으로 닫으면서 `--worker-duration-minutes`를 넘기지 않으면 stdout JSON에 `warnings` 배열을 조건부로 싣는다(**exit 0 유지·차단 없음**, `state.json`/`STATE.md` 바이트 동일). 오탐 차단 4관문: 값 보유·억제 인자·워커 신호 부재(PM 직접 수행 행)·`--action-step N/M`(N<M) 중간 진행 행은 모두 무경고이며, `owner==\"user\"`(사용자 확인 행)와 093 F-005 재-auto-pass no-op 경로도 제외된다. 억제 인자 `--worker-duration-unknown`(store_true)은 `--worker-duration-minutes`와 argparse 배타 그룹으로 묶이며, 지정 시 경고·필드 모두 생성하지 않는다(기록 결과는 인자 미지정과 동형). 106 F-004/F-005: code-scan 인용 집행을 PM 자기판정 → 도구 판정으로 승격 — `_collect_plan_target_files()`(PLAN.md §4.2 Step `**파일**:` 경로 토큰 수집)·`_check_code_scan_citation()`(pm-review-gate.md 항목 14 Pass 토큰 9종 중 1건 본문 존재 판정, §4.2 부재 시 None skip)·`_run_code_scan_citation_hook()`(EXECUTE 첫 행 자동 훅) 3함수 신설 + `ERROR_CODES` 1종(`code_scan_citation_unmet`) + `verify --code-scan-citation-check` 라우터(`evidence_check` 뒤·`fix_mode` 앞, 3플래그 배타 `evidence_check_flag_conflict` 재사용) + `cmd_advance`·`cmd_mark` 검증 구간(save 전) 훅 호출 각 1줄. **게이트 순서가 계약이다**(code-map-hook.js:121-124 동형) — ①발동(EXECUTE 첫 행)→②force→③자산(`.opal/code-scan.json` `headerSource`)→④산출물(PLAN.md)→⑤범위(`extensions` 0건)→⑥auto_pass 거부→⑦판정, ⑥은 graceful skip ③④⑤ **뒤**(앞에 두면 문서 전용·미보급 프로젝트에서 오탐이 난다, H-7 — 형제 훅 `_run_clarification_hook` 배치 비답습). skip 사유는 훅·라우터 공통 3값(`code_scan_unavailable`/`plan_md_absent`/`doc_only_task`)으로 닫고, `state.json`·`STATE.md`·`schema/*.json` 무변경(신규 영속 필드 0건). S-25: force 우회는 조기 반환 대신 ③④⑤ skip·⑥⑦를 통과해 **실제 거부 상태에서만** missing을 반환하고(force에 err 없음, ② 계약 보존) `cmd_mark`가 `code_scan_citation_force` decision으로 의사결정 로그에 강제 기재(091 `gate_artifact_force` 동형·46종 불변; `cmd_advance`는 `--force` 부재로 무경로).",
  "exports": [
    "cmd_init", "cmd_show", "cmd_advance", "cmd_mark",
    "cmd_block", "cmd_validate", "cmd_add_row", "cmd_status",
    "cmd_spec_validate", "cmd_gate_pass", "build_todo_mirror",
    "link_memory_history",
    "can_auto_approve_user_confirmation", "auto_approve_prior_user_confirmations",
    "_collect_plan_target_files", "_check_code_scan_citation",
    "_run_code_scan_citation_hook"
  ]
}
"""

# PLAN §2.1 구현 명세 — TASK T-11: 표준 라이브러리만 import
import argparse
import fnmatch
import json
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# 상수 (PLAN §2.2 G-4, §2.18 E-1, §2.13 G-10)
# ─────────────────────────────────────────────────────────────────────────────

STAGE_ENUM = [
    "TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO", "EXECUTE", "TEST",
    "WIREFRAME", "QA", "SPEC", "REVIEW", "DESIGN",
    "VERIFY", "SCAN", "CHECK", "REPORT", "WBS", "CLOSE",
    # 070 R-8: opdd 드리프트 정정 — opal-pilot-data-design 단계 enum 등록(enum 문자열 추가만, pipeline.json은 2차)
    "DICT", "MODEL", "DDL/MIGRATION",
]

# 070 F-001 R-1/R-6: pipeline.json 스펙 key 형식 — {stage_slug}.{item_slug}(_N)?
# (TASK.md §확정 방향 §6, PLAN §3.1.2)
KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$")


def stage_to_slug(stage: str) -> str:
    """stage enum → slug. 소문자화 + '-'·'/' → '_'. (TASK §6, PLAN §3.1.2)"""
    return stage.lower().replace("-", "_").replace("/", "_")

# semi-agentic 모드 경계 — 이 stage 집합에 속하는 행은 EXECUTE-equivalent 이전으로 간주
# (PLAN-equivalent 단계까지 사용자 검토 강제) — D-DEC-5 (140)
MODE_BOUNDARY_STAGES = {
    "TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO",
    "SPEC", "REVIEW", "DESIGN",
    "WBS", "WIREFRAME",
    # 094 R-11 G-1: opdd 설계 확정 3단계(070에서 STAGE_ENUM에는 등록됐으나
    # 경계 상수 누락 — semi-agentic 기본 모드에서 소유자 미노출 통과 결함)
    "DICT", "MODEL", "DDL/MIGRATION",
}


# 093 F-003 R-3: '이 사용자 확인 행을 자동 승인해도 되는가' 단일 판정 (PLAN §3.3.2 (1))
def can_auto_approve_user_confirmation(stage, mode, *, include_close_axis=True):
    """R-3 — 사용자 확인 행 자동 승인 가부 단일 판정.

    반환: (allowed: bool, deny_reason: str | None)
      deny_reason ∈ {"close_requires_user", "interactive_requires_user",
                     "semi_agentic_pre_execute"}

    두 축 합성:
      축1 CLOSE 여부  — 모드 무관 무조건 거부 (check_close_gate와 동일 규범, 별개 상수 규칙)
      축2 모드별 경계  — interactive는 전 stage 거부 / semi-agentic은 모드 경계 상수 한정 거부
    두 축은 상호 배타다 — "CLOSE"는 모드 경계 상수에 속하지 않는다.

    include_close_axis=False — 축1을 평가하지 않고 축2만 합성한다. cmd_validate 전용
    (H-4): 현행 validate는 CLOSE 축을 갖지 않으므로 CLOSE 행에도 모드 축 판정을 그대로
    적용해야 표 B V-7(CLOSE×interactive → auto_pass_in_interactive_mode)과
    V-8·V-9(CLOSE×semi-agentic/agentic → 위반 없음)가 동시에 성립한다.
    """
    if include_close_axis and stage == "CLOSE":
        return (False, "close_requires_user")            # 축1 — 최우선
    if mode == "interactive":
        return (False, "interactive_requires_user")      # 축2-a — stage 무관
    if mode == "semi-agentic" and stage in MODE_BOUNDARY_STAGES:
        return (False, "semi_agentic_pre_execute")       # 축2-b — stage 한정
    return (True, None)                                  # agentic 전 구간 / semi-agentic 경계 밖


STATUS_LABEL_MAP = {
    "pending":     "⬜",
    "in_progress": "🔄",
    "done":        "✅",
    "failed":      "❌",
    "na":          "-",
}
LABEL_STATUS_MAP = {v: k for k, v in STATUS_LABEL_MAP.items()}

# 094 F-003: current_status → 한글 라벨 (cmd_show '- 상태:' 라인 전용 SSOT)
STATUS_TEXT = {
    "in_progress":          "진행 중",
    "done":                 "완료",
    "blocked":              "블로커",
    "additional_work":      "추가작업중",
    "additional_work_done": "추가작업완료",
}

# PLAN §2.2 G-4 표준 항목 상수
# 014 Phase 4: 새 표준 행 구조에서는 "작업 / PM Gate / 사용자 확인 / DONE.md 생성"만 사용한다.
#   "QA Gate"/"State Gate"는 deprecated — State Gate는 stage-transition guard(§M-A)로 이전,
#   QA Gate는 PM Gate로 통합됨. 단 in-flight 레거시 state.json 하위호환을 위해 enum에서 즉시
#   제거하지 않고 deprecated 항목으로 남겨둔다(이 상수는 강제 검증에 쓰이지 않는 문서용 SSOT).
STANDARD_ITEMS = {
    "작업", "PM Gate", "사용자 확인", "DONE.md 생성",
}
DEPRECATED_ITEMS = {
    "QA Gate", "State Gate",  # 014 Phase 4 — 신규 생성 권장 안 함, 레거시 허용
}
# gate-pass(deprecated) 전용 4행 패턴 — 레거시 state.json에만 존재.
GATE_PATTERN = ["QA Gate", "State Gate", "PM Gate", "State Gate"]

# PLAN §2.18 에러 코드 카탈로그 23종 SSOT — 라인 53부터
# 모든 error 응답 값은 이 상수의 키를 참조한다. 추가/임의 변형 금지.
ERROR_CODES = {
    "worker_scope_violation":         "워커가 자기 단계({worker_stage}) 외 행(row {row_id}, stage={stage}) 갱신 시도",
    "already_initialized":            "state.json이 이미 존재합니다. --force로 덮어쓰기 가능",
    "date_tool_failed":               "node ~/.opal/tools/date/date.js datetime 호출 실패 — STATE.md 변경 없음(원자성)",
    # 094 R-4/D-2: --import-existing은 저널화로 제거됨 — 파싱 대상(파이프라인 표) 자체가 STATE.md에서 소멸
    "import_existing_removed":
        "--import-existing은 094(STATE.md 저널화)에서 제거되었습니다 — "
        "STATE.md 파이프라인 표가 더 이상 존재하지 않습니다. "
        "행 구성은 --rows-from <pipeline.json> 또는 --rows-spec을 사용하세요.",
    "invalid_status_transition":      "current_status 전이 그래프(§2.11 G-7) 위반: {from_status} → {to_status}",
    "row_not_found":                  "--row {row_id}에 해당하는 행이 state.json에 없음",
    "invalid_stage_enum":             "--stage {value}는 §2.2 G-3 enum 16종에 없음",
    "gate_pattern_mismatch":          "--start {row} 위치 연속 4행이 [QA Gate, State Gate, PM Gate, State Gate] 패턴과 불일치",
    "gate_stage_mixed":               "gate-pass 4행이 모두 동일 stage가 아님",
    "state_not_initialized":          "state.json이 존재하지 않습니다. state init을 먼저 실행하세요",
    "user_confirmation_owner_mismatch": "사용자 확인 행(row {row_id})이 done이지만 owner가 user/auto가 아님",
    "owner_flag_conflict":            "--owner와 --auto-pass는 동시 사용 불가",
    "auto_pass_in_interactive_mode":  "interactive 모드에서 사용자 확인 행(row {row_id})이 owner=auto로 done 처리됨",
    "close_gate_violation":           "CLOSE 단계 첫 행 진입 — 직전 단계 사용자 확인 행이 owner=user/status=done이 아님",
    "agentic_close_gate_requires_user": "agentic/semi-agentic 모드 CLOSE 첫 행에 --auto-pass 사용 불가 (§2.16 G-13)",
    "semi_agentic_pre_execute_auto_pass_denied":
        "semi-agentic 모드에서 EXECUTE-equivalent 단계 이전 행(row {row_id}, stage={stage})에 --auto-pass 사용 불가 — PLAN-equivalent까지 사용자 검토 필수",
    "mode_flag_conflict":
        "다중 모드 플래그 동시 사용 — --interactive/--semi-agentic/--agentic 중 하나만 사용 가능",
    "note_required_for_force":        "--force 사용 시 --note 필수 (트리거 §2.17 #1/#3/#8)",
    "rows_spec_invalid_json":         "--rows-spec 인자가 유효한 JSON 배열이 아님",
    "skill_md_parse_error":           "--rows-from SKILL.md에서 행 추출 실패: {reason}",
    "task_path_not_found":            "<task-path> 디렉토리가 존재하지 않음: {path}",
    "worker_stage_required":          "--as-worker 사용 시 --worker-stage 필수",
    "rows_input_conflict":            "--rows-spec과 --rows-from은 동시 사용 불가",
    "rows_acts_not_implemented":      "--rows-acts는 본 태스크 범위 밖 (시그니처만 정의 — R-13)",
    "mock_in_scenario":               "TEST-SCENARIO.md에 mock 코드 패턴 발견 — 헌법 §4 'Don't fake it' 위반: {lines}",
    "evidence_missing":               "TEST-SCENARIO.md Pass 시나리오에 실행 증거 누락 — 헌법 §4 'Completion requires evidence' 위반: {lines}",
    "stage_transition_violation":     "단계 건너뛰기 차단: 행 {row_id} 갱신 전에 앞 행 {incomplete_rows}이(가) 완료되지 않았음 (PLAN §M-A stage-transition guard)",
    "red_evidence_missing":           "RED 증거(실패 출력) 누락 — GREEN/EXECUTE 진입 차단: {detail}",
    "test_modified_in_fix":           "fix 루핑 중 RED 테스트 파일 수정 거부: {files}",
    "clarification_gate_unmet":
        "TASK 4요소(목표/범위/제약/완료기준) 미잠금 — 다음 단계 진입 거부 (PRINCIPLES §1 집행): {missing}",
    # 070 F-001 R-1/R-6: pipeline.json 스펙 로딩/검증 (PLAN §3.1.2)
    "spec_file_not_found":            "pipeline.json 스펙 파일 없음: {path}",
    "spec_invalid_json":              "pipeline.json JSON 파싱 실패: {detail}",
    "spec_validation_failed":         "pipeline.json 스펙 검증 실패: {detail}",
    # 070 F-003 R-4: task-step 주소 해석 (PLAN §3.3.2)
    "task_step_addr_required":        "행 주소 미지정 — {flags} 중 하나 필요",
    "task_step_addr_conflict":        "행 주소 플래그 2개 이상 동시 사용 — {flags} 중 하나만 사용",
    "task_step_not_found":            "{flag} {key}에 해당하는 행이 state.json에 없음",
    # 070 F-004 R-9: add-row --key (PLAN §3.4.2)
    "task_step_key_invalid":          r"key {key} 형식 위반 — 패턴 ^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$",
    "task_step_key_duplicate":        "key {key} 중복 — 파일 내 유일해야 함",
    # 091 F-004 R-10/R-11: task_steps[].gate 스펙 검사 + mark 게이트 집행 (PLAN §3.4.2)
    "gate_artifact_missing":          "PM Gate 산출물 미충족 — 행 {row_id}({key}) 게이트 아티팩트 부재: {missing}",
    "spec_gate_type_invalid":         "task_steps[].gate가 object가 아님: {detail}",
    "spec_gate_missing_field":        "task_steps[].gate 필수 필드 누락: {detail}",
    "spec_gate_field_type_invalid":   "task_steps[].gate 필드 타입 오류(문자열 배열 필요): {detail}",
    "spec_gate_checklist_empty":      "task_steps[].gate.checklist가 비어 있음: {detail}",
    # 093 F-004 R-4: 자동 승인 불가 구간 — 캡틴 승인 필요 (PLAN §3.4.2)
    "user_confirmation_required":
        "자동 승인 불가 — 사용자 확인 행(row {row_id}, stage={stage})에 캡틴 승인이 필요합니다"
        " (사유: {reason}). 보고 → 캡틴 승인 → mark --done --owner user",
    # 098 F-003 R-4: 근거 등급 확정/미확정 판정 게이트 (PLAN §3.3.2)
    "evidence_check_flag_conflict":
        "--evidence-check와 --clarification-check는 동시 사용 불가 (무성 무시 방지)",
    # 106 F-004 R-4: code-scan 결과 인용 게이트 (PLAN §3.4.2 (4))
    "code_scan_citation_unmet":
        "PLAN.md에 code-scan 결과 인용 없음 — EXECUTE 진입 차단 (pm-review-gate.md 항목 14): {missing}",
}

# ─────────────────────────────────────────────────────────────────────────────
# 경고 카탈로그 (103 R-21) — ERROR_CODES와 별개 사전이다.
#   경고는 에러가 아니다: exit 0을 유지하고 err()를 타지 않으며 상태 변경을 막지도
#   않는다. ERROR_CODES에 넣지 않는 이유는 두 가지다 — (1) err()는 sys.exit()로
#   끝나므로 카탈로그를 공유하면 "경고인데 차단"이라는 오용 경로가 생긴다,
#   (2) ERROR_CODES 키 집합은 회귀 테스트(TestErrorCodesCompleteness / S-40)가
#   HEAD와 대조해 고정하고 있어 종수를 늘리면 계약이 깨진다.
# ─────────────────────────────────────────────────────────────────────────────
WARNING_CODES = {
    "worker_duration_missing":
        "워커를 디스패치한 행(row {row_id}, stage={stage})을 완료 처리하면서 "
        "--worker-duration-minutes를 넘기지 않았습니다. 워커 완료 알림의 duration_ms는 "
        "세션과 함께 사라지고 행에는 완료 시각만 남아 시작 시각을 되살릴 수 없으므로, "
        "지금 적지 않으면 이 소요는 영구히 소실되고 통계에서 PM 몫으로 잘못 귀속됩니다 "
        "— 소급 복구 경로가 없습니다. 알림에 실린 duration_ms를 분으로 환산해 "
        "`--worker-duration-minutes <분>`으로 다시 mark하거나, 실제로 알 수 없는 경우"
        "(중단된 워커·PM 직접 수행·소급 불가 과거 데이터)라면 "
        "`--worker-duration-unknown`으로 미측정임을 명시하십시오.",
}

PIPELINE_MARKER_START = "<!-- pipeline:start -->"
PIPELINE_MARKER_END   = "<!-- pipeline:end -->"

# 094 F-003 (§3.3.2 (1)(2)): 레거시(001~093) STATE.md는 마커+표를 동결 텍스트로
# 보유한다. cmd_show가 그 동결 표를 최신인 양 반환하지 않도록 배너로 명시한다.
LEGACY_FROZEN_BANNER = (
    "> [레거시] 이 태스크의 STATE.md에는 파이프라인 표가 남아 있으나 더 이상 "
    "갱신되지 않는 동결 텍스트입니다. 현황의 SSOT는 state.json이며 아래 렌더가 최신입니다."
)

# current_status 전이 그래프 (PLAN §2.11 G-7)
ALLOWED_TRANSITIONS = {
    "in_progress":          {"done", "blocked", "additional_work"},
    "done":                 {"additional_work", "blocked"},
    "blocked":              {"in_progress", "done"},
    "additional_work":      {"additional_work_done", "blocked", "in_progress"},
    "additional_work_done": {"additional_work", "blocked"},
}

# ─────────────────────────────────────────────────────────────────────────────
# 응답 헬퍼 (PLAN §2.1, D-11 패턴 차용)
# ─────────────────────────────────────────────────────────────────────────────

def ok(command, **kwargs):
    """성공 응답 — 단일 라인 JSON, exit 0"""
    print(json.dumps({"ok": True, "command": command, **kwargs}, ensure_ascii=False, default=str))

def err(command, code, message=None, exit_code=1, **kwargs):
    """에러 응답 — 단일 라인 JSON, exit {exit_code}
    code는 ERROR_CODES 키 중 하나여야 한다 (§2.18 SSOT).
    추가 필드(kwargs)로 에러 컨텍스트(row_id, stage 등)를 포함한다.
    """
    if message is None:
        template = ERROR_CODES.get(code, code)
        try:
            message = template.format(**kwargs)
        except (KeyError, IndexError):
            message = template
    payload = {"ok": False, "command": command, "error": code, "message": message}
    payload.update(kwargs)
    print(json.dumps(payload, ensure_ascii=False, default=str))
    sys.exit(exit_code)

# ─────────────────────────────────────────────────────────────────────────────
# 시점 취득 (PLAN §2.11 G-5, TASK T-5)
# ─────────────────────────────────────────────────────────────────────────────

# 시각 문자열 형식 — 초 해상도가 1순위, 분 해상도가 하위호환 폴백이다 (103 R-19).
TS_PATTERN_SEC = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
TS_PATTERN_MIN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


def _date_js_path():
    """date.js 실경로 — 형제 배치(`<tools>/date/date.js`) 우선, 없으면 배포본.

    배포 레이아웃(`~/.opal/tools/state-tool/`)에서는 형제 경로가 곧
    `~/.opal/tools/date/date.js`라 종전과 동일하게 해석된다. 레포 소스에서
    직접 실행할 때만 레포의 date.js를 쓰게 되어, 배포 전 검증이 가능하다.
    """
    sibling = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir, "date", "date.js")
    sibling = os.path.normpath(sibling)
    if os.path.exists(sibling):
        return sibling
    return os.path.expanduser("~/.opal/tools/date/date.js")


def _run_date_js(date_js, fmt):
    """date.js 1회 호출 → (returncode, stdout, stderr). 예외는 호출자가 처리한다."""
    result = subprocess.run(
        ["node", date_js, fmt],
        capture_output=True, text=True, timeout=10
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_kst_datetime(command="(unknown)"):
    """date.js 호출 → KST `YYYY-MM-DD HH:mm:ss` 반환 (103 R-19).

    `datetime-sec`(초 해상도)를 먼저 요청하고, 응답이 형식에 맞지 않으면
    `datetime`(분 해상도)으로 폴백한다 — date.js가 아직 `datetime-sec`를
    모르는 배포본이면 사용법 안내를 exit 0으로 출력하므로, 반환값 형식 검사가
    지원 여부 판정을 겸한다. 폴백 값은 종전과 바이트 동일한 분 해상도 문자열이며
    스키마·집계 양쪽이 두 형식을 모두 수용한다.

    두 형식 모두 얻지 못하면 date_tool_failed 에러 응답 후 exit 2.
    """
    date_js = _date_js_path()
    try:
        code, out, stderr = _run_date_js(date_js, "datetime-sec")
        if code == 0 and TS_PATTERN_SEC.match(out):
            return out

        code, out, stderr = _run_date_js(date_js, "datetime")
        if code == 0 and TS_PATTERN_MIN.match(out):
            return out

        err(command, "date_tool_failed",
            message=f"exit={code}, stderr={stderr}",
            exit_code=2)
    except Exception as e:
        err(command, "date_tool_failed", message=str(e), exit_code=2)

# ─────────────────────────────────────────────────────────────────────────────
# 파일 I/O 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def resolve_task_path(task_path_str, command):
    """task-path 디렉토리 존재 검증. 미존재 시 task_path_not_found + exit 1."""
    p = pathlib.Path(task_path_str).resolve()
    if not p.is_dir():
        err(command, "task_path_not_found", path=str(p))
    return p

def load_state_json(task_path, command):
    """state.json 로드. 미존재 시 state_not_initialized + exit 1."""
    state_file = task_path / "state.json"
    if not state_file.exists():
        err(command, "state_not_initialized")
    with open(state_file, encoding="utf-8") as f:
        return json.load(f)

def save_state_json(task_path, state):
    """state.json 저장 (UTF-8, 들여쓰기 2칸)."""
    state_file = task_path / "state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")

def load_state_md(task_path):
    """STATE.md 텍스트 반환. 없으면 None."""
    md_file = task_path / "STATE.md"
    if not md_file.exists():
        return None
    with open(md_file, encoding="utf-8") as f:
        return f.read()

def save_state_md(task_path, content):
    """STATE.md 저장."""
    md_file = task_path / "STATE.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(content)

# ─────────────────────────────────────────────────────────────────────────────
# 소유자 호칭 치환 (PLAN §3.1.2, TASK 054)
# ─────────────────────────────────────────────────────────────────────────────

def resolve_owner_placeholder(text: str) -> str:
    """note 등 사용자 free text에 담긴 '{owner_name}' 플레이스홀더를 identity.md의
    owner_name 값으로 write-time 치환한다.

    fail-safe(원문 유지): 플레이스홀더 미포함, identity.md 부재, owner_name 공란/미발견,
    또는 파일 읽기·파싱 중 예외 발생 시 모두 원문 text를 그대로 반환한다 — note 저장
    자체를 실패시키지 않는다. 경로는 OPAL_HOME env 우선(플랫폼 독립, ~/.opal 하드코딩 분기 금지).
    T-11: 표준 라이브러리(re/os/pathlib)만 사용 — PyYAML 등 신규 패키지 도입 금지.
    """
    if not text or "{owner_name}" not in text:
        return text
    try:
        opal_home = os.environ.get("OPAL_HOME") or os.path.expanduser("~/.opal")
        identity_path = pathlib.Path(opal_home) / "identity.md"
        if not identity_path.exists():
            return text
        content = identity_path.read_text(encoding="utf-8")
        fm_match = re.search(r"^---\s*$(.*?)^---\s*$", content, re.M | re.S)
        block = fm_match.group(1) if fm_match else content
        m = re.search(r"^owner_name:\s*(.*)$", block, re.M)
        if not m:
            return text
        owner_name = m.group(1).strip().strip("\"'")
        if not owner_name:
            return text
        return text.replace("{owner_name}", owner_name)
    except Exception:
        return text

# ─────────────────────────────────────────────────────────────────────────────
# 마크다운 렌더 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def render_pipeline_table(rows):
    """state.json rows[]를 마크다운 표로 렌더 (마커 제외).
    094: cmd_show --format md의 유일한 렌더 경로로 용도가 격하되었다 — 파일에
    고정 저장하는 미러가 아니라 요청 시 생성하는 뷰(§3.2.2 (4)). '비고' 열에
    row.note를 노출해, 렌더가 STATE.md 동결 텍스트가 아니라 state.json 최신
    값을 반영함을 조회 결과로도 구분할 수 있게 한다(F-003 렌더 원천 단일화)."""
    lines = [
        "## 파이프라인 현황판",
        "",
        "> 상태값: ⬜ 대기 / 🔄 진행 중 / ✅ 완료 / ❌ 실패 / - 해당 없음",
        "> **수행 원칙**: 위에서 아래로 순서대로 처리한다. 현재 행이 ✅가 아니면 다음 행으로 진행 불가.",
        "",
        "| # | 단계 | 항목 | 상태 | 시점 | 비고 |",
        "|---|------|------|------|------|------|",
    ]
    for row in rows:
        ts = row.get("timestamp") or ""
        note = row.get("note") or ""
        lines.append(
            f"| {row['row_id']} | {row['stage']} | {row['item']} | {row['status_label']} | {ts} | {note} |"
        )
    return "\n".join(lines)

def update_state_md_header(md_content, new_datetime):
    """G-5(D-3 존치): STATE.md '> 최종 갱신:' 라인 교체. 저널 축소판에서도
    계속 호출되어 advance/mark 후 헤더 타임스탬프가 갱신된다(094 §3.1.2 (3))."""
    return re.sub(
        r"^(> 최종 갱신: ).*$",
        lambda m: f"{m.group(1)}{new_datetime}",
        md_content, count=1, flags=re.MULTILINE
    )

# ─────────────────────────────────────────────────────────────────────────────
# 의사결정 로그 자동 기재 (PLAN §2.17 G-14/G-15, 094 §3.1.2 (2)(6))
# ─────────────────────────────────────────────────────────────────────────────

def _escape_table_cell(value):
    """094 S-32: 의사결정 로그 표 셀에 들어갈 값의 '|'·개행을 이스케이프해
    표 구조 파괴(열 증가·행 분열)를 방지한다. '|' → '&#124;', 개행 → '<br>' —
    원문 토큰은 삭제되지 않고 치환되므로 복원 가능성이 보존된다."""
    text = "" if value is None else str(value)
    return text.replace("|", "&#124;").replace("\r\n", "<br>").replace("\n", "<br>")


def ensure_journal_skeleton(md, task_title, now_str):
    """저널 필수 골격('## 의사결정 로그' 표 헤더)을 보증한다 (094 §3.1.2 (2)).
    - md is None            → _build_new_state_md(task_title, now_str) 반환
    - 표 헤더 정규식 미매칭 → 헤딩이 있으면 그 직후에 표 헤더만 복구 삽입,
                              헤딩조차 없으면 파일 끝에 '## 의사결정 로그' 빈 표 블록을 append
    - 이미 존재            → md 원문 그대로 반환 (멱등)
    레거시 STATE.md(마커·표 보유)는 본문을 일절 건드리지 않는다 — append/삽입만 수행한다.
    """
    if md is None:
        return _build_new_state_md(task_title, now_str)

    full_pattern = re.compile(r"## 의사결정 로그\n\| # \| 시점 \| 결정 \| 근거 \|\n\|[-| ]+\|\n")
    if full_pattern.search(md):
        return md  # 이미 골격 존재 — 멱등

    header_block = "| # | 시점 | 결정 | 근거 |\n|---|------|------|------|\n"
    heading_match = re.search(r"^## 의사결정 로그\n", md, re.MULTILINE)
    if heading_match:
        # 헤딩은 있으나 표 헤더/구분행이 손상됨 — 헤딩 직후에 표 헤더만 복구
        insert_at = heading_match.end()
        return md[:insert_at] + header_block + md[insert_at:]

    # 헤딩 자체가 없음 — 파일 끝에 전체 섹션 append
    return md.rstrip("\n") + "\n\n## 의사결정 로그\n" + header_block


def append_decision_log(md_content, now_str, decision, reason):
    """STATE.md '## 의사결정 로그' 표에 1행 추가.
    표가 없거나 헤더를 못 찾으면 무시 (자유 텍스트 영역 외 안전 보장).
    """
    pattern = re.compile(
        r"(## 의사결정 로그\n\| # \| 시점 \| 결정 \| 근거 \|\n\|[-| ]+\|\n)((?:\|[^\n]*\|\n)*)",
        re.MULTILINE
    )
    m = pattern.search(md_content)
    if not m:
        return md_content  # 표 없으면 조용히 패스

    # 기존 행 수 파악 → 새 # 컬럼값
    # 094: 오프바이원 수정 — 캡처 그룹 문자열이 '\n'으로 시작하지 않는 경계
    # (기존 행이 정확히 1개일 때)를 정확히 세기 위해 실제 '|'로 시작하는 줄
    # 수를 직접 카운트한다(기존 "\n| " count 방식은 그 경계에서 0으로 오카운트).
    existing_rows = m.group(2)
    row_count = len([l for l in existing_rows.splitlines() if l.strip().startswith("|")])
    new_num = row_count + 1
    safe_decision = _escape_table_cell(decision)
    safe_reason   = _escape_table_cell(reason)
    new_row = f"| {new_num} | {now_str} | {safe_decision} | {safe_reason} |\n"

    replacement = m.group(1) + existing_rows + new_row
    return md_content[:m.start()] + replacement + md_content[m.end():]

# ─────────────────────────────────────────────────────────────────────────────
# 저널 후처리 (094: 구 '미러 동기화'에서 의미 재정의 — fail-open)
# ─────────────────────────────────────────────────────────────────────────────

def _redact_path_like(text):
    """예외 메시지에 섞여 나오는 절대경로/홈 디렉토리 경로를 파일명(basename)
    으로 치환한다(R-11 SEC 후속 — journal_warning.reason 경로 노출 차단,
    PLAN.md §5.4). 특정 OS·예외의 메시지 포맷(Errno 구조 등)을 가정하지 않고,
    공백으로 나눈 토큰 중 '/'로 시작하거나 사용자 홈 경로로 시작하는 것을
    일반적으로 탐지해 basename만 남긴다 — 예외 타입명·파일명 등 진단 가치는
    보존하고 경로 프리픽스만 절삭한다."""
    home = str(pathlib.Path.home())

    def _shrink(token):
        m = re.match(r"^([\"'`]*)(.*?)([\"'`.,;:]*)$", token, re.DOTALL)
        prefix, core, suffix = m.groups() if m else ("", token, "")
        if core and (core.startswith("/") or core.startswith(home)):
            base = os.path.basename(core.rstrip("/")) or core
            return f"{prefix}{base}{suffix}"
        return token

    return " ".join(_shrink(tok) for tok in text.split(" "))


def sync_state_md(task_path, state, now_str, command, decision=None, reason=None):
    """저널 후처리 (094 §3.1.2 (3)):
    1. G-5(D-3) 최종 갱신 헤더 교체
    2. decision이 있으면 저널 골격을 보증(ensure_journal_skeleton)한 뒤
       G-14/G-15 의사결정 로그 기재
    반환: dict | None — 실패 시 {"journal_warning": {...}}, 성공(또는 no-op) 시 None.
    [MUST] 어떤 경로에서도 err()/sys.exit()를 호출하지 않는다(fail-open) — 저널
    쓰기 실패가 파이프라인을 막아서는 안 되지만, 실패 자체는 stdout
    journal_warning으로 표면화해 결정 로그 원문이 조용히 증발하지 않게 한다.
    """
    try:
        md = load_state_md(task_path)
        if decision is not None:
            md = ensure_journal_skeleton(md, state.get("task_id", "task"), now_str)
        if md is None:
            return None  # 갱신할 저널 없음 + 기재할 결정 없음 → no-op

        md = update_state_md_header(md, now_str)
        if decision is not None:
            md = append_decision_log(md, now_str, decision, reason or "(none)")

        save_state_md(task_path, md)
        return None
    except Exception as e:  # 디스크/권한 등 I/O 오류만 도달
        return {"journal_warning": {
            "reason": _redact_path_like(f"{type(e).__name__}: {e}"),
            "decision": decision, "note": reason,
        }}

# ─────────────────────────────────────────────────────────────────────────────
# 행 조회 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def find_row(state, row_id, command):
    """row_id에 해당하는 행 반환. 없으면 row_not_found + exit 1."""
    for row in state["rows"]:
        if row["row_id"] == row_id:
            return row
    err(command, "row_not_found", row_id=row_id)

def find_row_index(state, row_id, command):
    """row_id에 해당하는 인덱스 반환. 없으면 row_not_found + exit 1."""
    for i, row in enumerate(state["rows"]):
        if row["row_id"] == row_id:
            return i
    err(command, "row_not_found", row_id=row_id)


def resolve_row_index(state, command, key_val=None, id_val=None, row_val=None,
                      addr_label="task-step"):
    """key/id/deprecated-row 3주소를 row_index로 통일 해석 (070 F-003 R-4, PLAN §3.3.2).

    - addr_label로 에러 메시지에 노출할 실제 플래그명을 결정한다:
        "after"    → add-row 컨텍스트: --after-task-step/--after-task-step-id/--after
        그 외(기본) → advance/mark/block 컨텍스트: --task-step/--task-step-id/--row(deprecated)
    - 제공된 주소 개수 집계(None 아닌 것):
        0개  → err(command, 'task_step_addr_required', flags=...)
        2개+ → err(command, 'task_step_addr_conflict', flags=...)
    - key_val: rows[]에서 row['key']==key_val 탐색. 미매칭 시 'task_step_not_found'
      (flag=키 주소 플래그명, candidates=존재하는 key 목록).
    - id_val / row_val: row_id 동등비교(find_row_index 로직 재사용). 미매칭 시 'row_not_found'.
    반환: row_index(int).
    """
    if addr_label == "after":
        flags = "--after-task-step/--after-task-step-id/--after"
        key_flag = "--after-task-step"
    else:
        flags = "--task-step/--task-step-id/--row(deprecated)"
        key_flag = "--task-step"

    provided = [v for v in (key_val, id_val, row_val) if v is not None]
    if len(provided) == 0:
        err(command, "task_step_addr_required", flags=flags)
    if len(provided) >= 2:
        err(command, "task_step_addr_conflict", flags=flags)

    if key_val is not None:
        for i, row in enumerate(state["rows"]):
            if row.get("key") == key_val:
                return i
        candidates = [r.get("key") for r in state["rows"] if r.get("key")]
        err(command, "task_step_not_found", key=key_val, flag=key_flag, candidates=candidates)

    row_id = id_val if id_val is not None else row_val
    return find_row_index(state, row_id, command)

# ─────────────────────────────────────────────────────────────────────────────
# 단계 건너뛰기 차단 (PLAN §M-A stage-transition guard)
# ─────────────────────────────────────────────────────────────────────────────

# 완료로 간주하는 상태값 — 이 상태의 앞 행은 건너뛰기 검증에서 제외
_COMPLETE_STATUSES = {"done", "additional_work_done", "na"}

# 093 F-005: --auto-pass note 접두 (기존 state.json·하네스 문서가 참조 — 문자열 불변)
_AUTO_PASS_PREFIX = "agentic auto-pass"


def build_todo_mirror(state, action):
    """076 R-1: state.json rows[] → 단계(stage) 단위 todo 미러 페이로드.

    action: "create"(init) | "update"(advance/mark/block).
    비영속 — ok() stdout 페이로드에만 사용하며 save_state_json 미접촉
    (H-3, state.schema.json §root additionalProperties:false 위반 회피).

    파생 규칙(state.md §파이프라인 todo 미러 정합):
      - na 행은 집계에서 중립(제외) — agentic auto-na 오판 방지(DEC-2).
      - effective 없음 or 전부 done/additional_work_done → completed.
      - 전부 pending → pending.
      - 그 외(in_progress·failed·부분완료 혼합) → in_progress
        — 블로커(failed)는 in_progress 유지(DEC-3, todo에 실패 상태 없음).

    단계 순서는 rows 등장 순서를 보존한다(dict.fromkeys 패턴, _build_new_state_md 선례).
    status 열거값(pending/in_progress/completed)은 네이티브 할일 도구 status와 직접 매핑되어
    소유자(PM)가 그대로 릴레이한다(DEC-1)."""
    rows = state.get("rows", [])
    stages = list(dict.fromkeys(r["stage"] for r in rows))
    todos = []
    for stage in stages:
        srows = [r for r in rows if r["stage"] == stage]
        effective = []
        for r in srows:
            if r.get("status") == "na":
                continue                       # na 중립(DEC-2, 기존)
            if r.get("item") == "사용자 확인":   # R-11 G-3-b: 자동 승인 예정 행도 중립
                allowed, _ = can_auto_approve_user_confirmation(
                    r.get("stage"), state.get("mode"))
                if allowed:
                    continue
            effective.append(r.get("status"))
        if not effective or all(s in ("done", "additional_work_done") for s in effective):
            st = "completed"
        elif all(s == "pending" for s in effective):
            st = "pending"
        else:  # in_progress / failed / 부분완료 혼합 → in_progress(블로커 유지 DEC-3)
            st = "in_progress"
        todos.append({
            "id":         f"stage:{stage}",       # 세션 내 안정 키
            "content":    f"{stage} 단계",         # TaskCreate/TaskUpdate content
            "activeForm": f"{stage} 단계 진행 중",  # 진행형 표현(native todo 스키마)
            "status":     st,                      # pending | in_progress | completed
        })
    return {"action": action, "todos": todos}


def _derive_next_action(state):
    """072 G-16: 파이프라인 프론티어(첫 미완료 행)에서 '다음 액션' 문자열 파생.
    전체 완료 시 '태스크 완료'(M-2). 070 정합: row 순서 스캔 + _COMPLETE_STATUSES 재사용
    (resolve_row_index/task-step key 체계 무접촉)."""
    mode = state.get("mode")
    rows = state.get("rows", [])
    for idx, row in enumerate(rows):
        st = row.get("status")
        if st in _COMPLETE_STATUSES:
            continue
        # R-11 G-3-a: 다음 진입 시 도구가 자동 승인할 사용자 확인 행은 프론티어가 아니다.
        # 단, CLOSE 진입 직전 확인 행은 예외 — auto_approve_prior_user_confirmations가
        # target_row.stage=="CLOSE"이면 무조건 자동 승인을 no-op하므로(H-8 1차 방어와 동형),
        # 바로 다음 행이 CLOSE면 이 확인 행은 실제로 소유자 승인이 필요한 프론티어다.
        if row.get("item") == "사용자 확인":
            next_row = rows[idx + 1] if idx + 1 < len(rows) else None
            next_is_close = bool(next_row and next_row.get("stage") == "CLOSE")
            if not next_is_close:
                allowed, _ = can_auto_approve_user_confirmation(row.get("stage"), mode)
                if allowed:
                    continue
        stage, item = row.get("stage", ""), row.get("item", "")
        if st == "in_progress":
            return f"{stage} {item} 진행 중"
        if st == "failed":
            return f"{stage} {item} 블로커 해소"
        return f"{stage} {item} 진입"   # pending
    return "태스크 완료"


# ─────────────────────────────────────────────────────────────────────────────
# CLOSE 완료 시 메모리 히스토리 자동 연결 (PLAN 088 §2.1~§2.7, §2.9)
# ─────────────────────────────────────────────────────────────────────────────

# historyRow stage 값 — D-6 확정(2026-08-11부로 "완료·커밋" 표기 폐기)
HISTORY_STAGE_DONE = "완료"
# result(핵심결과) 초기값 — 빈 문자열 대신 PM 보강 대기를 식별 가능하게 표면화(§2.6)
HISTORY_RESULT_PLACEHOLDER = "(PM 보강 대기)"
# task_id("{NNN}-{yymmdd}-{skill}-{설명}") → title 파생 패턴(§2.6). 불일치 시 원문 폴백.
HISTORY_TITLE_PATTERN = re.compile(r"^(\d{3})-\d{6}-[a-z]+-(.+)$")

# 형제 memory-tool CLI 경로 — state-tool/memory-tool은 항상 같은 tools/ 부모를 공유한다(§2.2)
_MEMORY_TOOL = pathlib.Path(__file__).resolve().parent.parent / "memory-tool" / "memory_tool.py"


def find_project_root(task_path):
    """task_path의 조상 중 .opal/MEMORY.json을 파일로 가진 첫 디렉토리를 반환한다(§2.3).
    없으면 None — 호출자는 subprocess를 아예 띄우지 말고 조기 반환해야 한다."""
    p = pathlib.Path(task_path).resolve()
    for cand in (p, *p.parents):
        if (cand / ".opal" / "MEMORY.json").is_file():
            return cand
    return None


def derive_history_title(task_id):
    """task_id(태스크 폴더명)에서 히스토리 title을 파생한다(§2.6).
    '{NNN}-{yymmdd}-{skill}-{설명}' 패턴이면 '{NNN} {설명(하이픈→공백)}',
    패턴 불일치 시 task_id 원문으로 폴백(state.json에 별도 제목 필드가 없음)."""
    m = HISTORY_TITLE_PATTERN.match(task_id or "")
    if not m:
        return task_id
    number, rest = m.group(1), m.group(2)
    return f"{number} {rest.replace('-', ' ')}"


def build_history_reminder(title, memory_file):
    """result(핵심결과) 보강을 즉시 실행 가능한 명령 문자열로 안내한다(§2.7).
    PM 실행 경로는 사용자 대면 표준인 run.sh로 안내한다."""
    return (
        "[메모리 히스토리] 작업 히스토리 행이 자동 생성되었다(핵심결과 미기재). 지금 보강하라:\n"
        f'"$HOME/.opal/tools/memory-tool/run.sh" update --file {memory_file} '
        f'--kind history --title "{title}" --result "<무엇을 바꿨는지 + 결과>"'
    )


def _run_memory_tool(argv):
    """형제 memory_tool.py를 sys.executable subprocess로 실행한다(§2.2 — import·run.sh 경유 배제).
    반환: (returncode, dict|None) — stdout 중 마지막으로 파싱되는 JSON 라인. 파싱 실패 시 None."""
    result = subprocess.run(
        [sys.executable, str(_MEMORY_TOOL), *argv],
        capture_output=True, text=True, timeout=10,
    )
    parsed = None
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            continue
        if isinstance(obj, dict):
            parsed = obj
    return result.returncode, parsed


def link_memory_history(task_path, state):
    """CLOSE 마지막 행 mark 성공 시 memory-tool history 행을 자동 생성한다(§2.1/§2.4/§2.5).

    항상 payload dict를 반환하고 예외를 전파하지 않는다 — err()를 호출하지 않으며,
    memory-tool 부재/실패/타임아웃이 있어도 mark 자체를 실패시키지 않는다(R-4).
    판정 키는 path(§2.4) — show로 사전 조회해 동일 path 행이 있으면 append를 건너뛴다.
    """
    try:
        project_root = find_project_root(task_path)
        if project_root is None:
            return {"status": "skipped",
                    "warning": f"프로젝트 루트(.opal/MEMORY.json)를 찾지 못함: {task_path}"}
        if not _MEMORY_TOOL.is_file():
            return {"status": "skipped",
                    "warning": f"memory_tool.py를 찾지 못함: {_MEMORY_TOOL}"}

        memory_file = project_root / ".opal" / "MEMORY.json"
        rel_path = pathlib.Path(task_path).resolve().relative_to(project_root).as_posix() + "/"
        title = derive_history_title(state.get("task_id", ""))

        rc, show_result = _run_memory_tool(["show", "--file", str(memory_file)])
        if rc != 0 or show_result is None:
            warning = (show_result or {}).get("message") or f"memory-tool show 실패 (rc={rc})"
            return {"status": "failed", "warning": str(warning)}

        history_rows = show_result.get("history_rows") or []
        if any(r.get("path") == rel_path for r in history_rows):
            return {
                "status": "duplicate_skipped",
                "title": title, "path": rel_path, "stage": HISTORY_STAGE_DONE,
                "memory_file": str(memory_file),
                "reminder": build_history_reminder(title, memory_file),
            }

        rc, append_result = _run_memory_tool([
            "append", "--file", str(memory_file), "--kind", "history",
            "--title", title, "--stage", HISTORY_STAGE_DONE,
            "--path", rel_path, "--summary", HISTORY_RESULT_PLACEHOLDER,
        ])
        if rc != 0 or append_result is None:
            warning = (append_result or {}).get("message") or f"memory-tool append 실패 (rc={rc})"
            return {"status": "failed", "warning": str(warning)}

        return {
            "status": "created",
            "title": title, "path": rel_path, "stage": HISTORY_STAGE_DONE,
            "memory_file": str(memory_file),
            "reminder": build_history_reminder(title, memory_file),
        }
    except Exception as e:
        return {"status": "failed", "warning": str(e)}


def check_stage_transition_guard(state, row_index, command, force=False, scope="full"):
    """대상 행(row_index) 앞의 행이 완료 상태인지 검증.
    미완 행이 있으면 stage_transition_violation 에러 응답 후 exit 1.
    force=True면 우회 (--note 필수는 호출자가 이미 보장).

    완료로 간주: done / additional_work_done / na (agentic auto-na 포함).
    이미 done인 행을 재 mark 하는 경우(멱등)도 앞 행 검증 통과 후 허용.

    scope="full"         (PM 경로, 기본): 대상 행 앞의 모든 행이 완료여야 함.
    scope="prior_stage_only" (워커 경로): 대상 행의 stage보다 앞 stage에 속한
                             행만 검증. 같은 stage 내 앞 행은 검증 제외.
    """
    if force:
        return

    row = state["rows"][row_index]
    # 이미 완료 상태인 행의 재 mark(멱등) — 앞 행이 미완이어도 허용
    if row.get("status") in _COMPLETE_STATUSES:
        return

    target_stage = row["stage"]

    # prior_stage_only: 대상 행의 stage가 처음 등장하는 인덱스를 경계로 삼는다.
    # 그 인덱스 미만의 행(= 앞 단계 행)만 검증한다.
    if scope == "prior_stage_only":
        # 대상 stage가 처음 등장하는 위치를 찾는다
        stage_start = 0
        for i, r in enumerate(state["rows"]):
            if r["stage"] == target_stage:
                stage_start = i
                break
        check_up_to = stage_start  # [0, stage_start) 범위만 검증
    else:
        check_up_to = row_index    # [0, row_index) 전체 검증

    incomplete = []
    for i in range(check_up_to):
        prev = state["rows"][i]
        if prev.get("status") not in _COMPLETE_STATUSES:
            incomplete.append(prev["row_id"])

    if incomplete:
        err(command, "stage_transition_violation",
            row_id=row["row_id"],
            incomplete_rows=incomplete)


# ─────────────────────────────────────────────────────────────────────────────
# 자동 승인 훅 (093 F-002 R-2, PLAN §3.2.2)
# ─────────────────────────────────────────────────────────────────────────────

def auto_approve_prior_user_confirmations(
    state, row_index, command, *,
    as_worker=False, force=False, now_str=None,
):
    """R-2 조항 2 집행 — 대상 행 진입 시 앞의 미완 '사용자 확인' 행을 자동 승인한다.

    반환: 자동 승인한 row_id 리스트 (list[int]). 승인 대상이 없으면 [].
    부작용: state["rows"][i]를 in-place 갱신 (호출자가 save_state_json 책임).
    거부: 자동 승인 불가 구간이면 err(command, "user_confirmation_required", ...) 후 exit 1.

    [MUST] 이 함수는 save_state_json을 호출하지 않는다 — 가드 전량 통과 후 1회 저장
    패턴을 유지해, 후속 가드 실패 시 파일이 오염되지 않는다 (H-8).
    """
    if as_worker:
        return []          # 워커 경로 — 자동 승인 없음 (DEC-C)
    if force:
        return []          # --force 우회 경로 — 가드 자체가 스킵되므로 훅도 no-op

    target_row = state["rows"][row_index]
    if target_row["stage"] == "CLOSE":
        return []          # [MUST] CLOSE 진입 경로에서는 어떤 행도 자동 승인하지 않는다 (DEC-D 1차 방어)

    approved = []
    for i in range(row_index):                        # [0, row_index) — full scope와 동일 범위
        prev = state["rows"][i]
        if prev.get("item") != "사용자 확인":
            continue
        if prev.get("status") in _COMPLETE_STATUSES:  # done / additional_work_done / na
            continue                                  # 멱등 — 기존 na 행도 재승인하지 않는다 (R-6)
        if prev["stage"] == "CLOSE":
            continue                                  # DEC-D 2차 방어

        allowed, deny_reason = can_auto_approve_user_confirmation(   # DEC-D 3차 방어 포함
            prev["stage"], state.get("mode", "interactive"))
        if not allowed:
            err(command, "user_confirmation_required",               # F-004
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


# ─────────────────────────────────────────────────────────────────────────────
# CLOSE 진입 게이트 검증 (PLAN §2.16 G-13)
# ─────────────────────────────────────────────────────────────────────────────

def check_close_gate(state, row_index, command, auto_pass=False, force=False, owner=None):
    """CLOSE 단계 첫 행 갱신 시 게이트 검증.
    위반 시 close_gate_violation 또는 agentic_close_gate_requires_user.
    force=True면 스킵.

    owner: 이번 호출로 이 행에 적용될 예정인 --owner 값(cmd_mark 전용, 094 R-11 G-2).
    CLOSE 첫 행 갱신 시점에는 row["owner"]가 아직 갱신 전(=기존 값, 통상 'PM')이므로
    확인 행 0개 파이프라인의 소유자 승인 판정은 반드시 이 인자로 해야 한다 —
    row.get("owner")를 참조하면 항상 갱신 전 값을 보게 되어 폴백이 무의미해진다.
    """
    row = state["rows"][row_index]
    if row["stage"] != "CLOSE":
        return  # CLOSE 아니면 무관

    # CLOSE 단계 첫 행 여부 확인
    is_first_close = (row_index == 0 or state["rows"][row_index - 1]["stage"] != "CLOSE")
    if not is_first_close:
        return

    # agentic / semi-agentic 모드 + auto-pass 거부 (§2.16 G-13 / D-DEC-5b)
    if auto_pass and state.get("mode") in ("agentic", "semi-agentic"):
        err(command, "agentic_close_gate_requires_user", row_id=row["row_id"])

    if force:
        return  # force 우회

    # 직전 단계 사용자 확인 행 검색 (역순)
    prev_user_row = None
    for i in range(row_index - 1, -1, -1):
        if state["rows"][i].get("item") == "사용자 확인":
            prev_user_row = state["rows"][i]
            break

    if prev_user_row is None:
        # 094 R-11 G-2: 확인 행이 없는 파이프라인(opgc 등) — CLOSE 첫 행 자체를
        # 소유자 승인 지점으로 삼는다(정상 형태로 인정, 데드락 폴백).
        if owner != "user":
            err(command, "close_gate_violation",
                violation_detail=(
                    "pipeline has no user confirmation row — "
                    "CLOSE first row must be marked with --owner user"))
        return

    if prev_user_row["status"] != "done" or prev_user_row.get("owner") != "user":
        err(command, "close_gate_violation",
            violation_detail=(
                f"user confirmation row {prev_user_row['row_id']} is not done with owner=user "
                f"(status={prev_user_row['status']}, owner={prev_user_row.get('owner')})"
            ))

# ─────────────────────────────────────────────────────────────────────────────
# PM Gate 아티팩트 검증 (091 F-004 R-11, PLAN §3.4.2 (2))
# ─────────────────────────────────────────────────────────────────────────────

def _is_safe_artifact_token(t):
    """gate.artifacts 토큰의 태스크 폴더 밖 이탈 여부 검사 (H-4).
    절대경로이거나 '..' 파트를 포함하면 안전하지 않음 → False."""
    pp = pathlib.PurePosixPath(t)
    if pp.is_absolute():
        return False
    if ".." in pp.parts:
        return False
    return True

def check_gate_artifacts(task_path, row, command, force=False):
    """091 R-11: gate.artifacts 존재 검증. 미충족 시 gate_artifact_missing으로 mark 거부.
    gate 미보유 행 또는 artifacts가 빈 배열이면 즉시 return — 기존 동작 불변(H-3)."""
    gate = row.get("gate")
    if not isinstance(gate, dict):
        return None
    tokens = gate.get("artifacts") or []
    if not tokens:
        return None
    base = pathlib.Path(task_path)
    missing = []
    for t in tokens:
        if not _is_safe_artifact_token(t):        # 절대경로·상위경로 토큰 거부 (H-4)
            missing.append(t)
            continue
        if any(c in t for c in "*?["):
            if not any(base.glob(t)):
                missing.append(t)
        elif not (base / t).exists():
            missing.append(t)
    if not missing:
        return None
    if force:
        return missing                            # 우회 — 호출자가 의사결정 로그에 기재
    err(command, "gate_artifact_missing",
        row_id=row["row_id"], key=row.get("key"), missing=missing)

def build_gate_payload(row):
    """091 R-11(b): 게이트 통과 시 stdout으로 반환할 checklist 페이로드.
    dict로 감싼다 — todo_mirror_hook._extract_payload가 dict만 통과시킨다(H-6)."""
    gate = row.get("gate")
    if not isinstance(gate, dict):
        return None
    return {
        "key":       row.get("key"),
        "stage":     row["stage"],
        "item":      row["item"],
        "artifacts": gate.get("artifacts") or [],
        "checklist": gate.get("checklist") or [],
        "reminder":  "[PM Gate 점검] 아래 checklist 전 항목을 확인한 뒤 다음 단계로 진행하라. "
                     "SSOT는 해당 pilot references/pipeline.json task_steps[].gate 이다.",
    }

# ─────────────────────────────────────────────────────────────────────────────
# 행 주입 공통 처리 (PLAN §2.20)
# ─────────────────────────────────────────────────────────────────────────────

def build_rows_from_spec(spec_json_str, command, mode):
    """--rows-spec inline JSON → rows[] 반환 (§2.20.1)."""
    try:
        items = json.loads(spec_json_str)
    except json.JSONDecodeError as e:
        err(command, "rows_spec_invalid_json", detail=str(e))
    if not isinstance(items, list):
        err(command, "rows_spec_invalid_json", detail="top-level not array")

    rows = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            err(command, "rows_spec_invalid_json", detail=f"item[{i}] is not object")
        stage = item.get("stage")
        name  = item.get("item")
        if not stage or not name:
            err(command, "rows_spec_invalid_json",
                detail=f"item[{i}] missing 'stage' or 'item'")
        if stage not in STAGE_ENUM:
            err(command, "rows_spec_invalid_json",
                detail=f"item[{i}].stage '{stage}' not in enum")
        if len(name) < 1:
            err(command, "rows_spec_invalid_json",
                detail=f"item[{i}].item is empty")

        owner_default = item.get("owner_default", "PM")
        row = {
            "row_id":       i + 1,
            "stage":        stage,
            "item":         name,
            "status":       "pending",
            "status_label": "⬜",
            "timestamp":    None,
            "owner":        owner_default,
            "note":         None,
        }
        if item.get("gate"):
            row["gate"] = item["gate"]  # 091 F-004 R-9(a): --rows-spec 인라인 경로도 동형 지원

        rows.append(row)
    return rows

def build_rows_from_skill_md(skill_md_path, command, mode):
    """--rows-from SKILL.md 파싱 → rows[] 반환 (§2.20.2 10단계)."""
    p = pathlib.Path(skill_md_path)
    if not p.exists():
        err(command, "skill_md_parse_error", path=str(p), reason="file not found")

    # 단계 1: 파일 읽기
    content = p.read_text(encoding="utf-8")

    # 단계 2: 헤더 패턴 매칭
    header_pattern = re.compile(
        r"^(##|###|####)\s+.*STATE\.md\s*도메인\s*치환값.*$",
        re.MULTILINE
    )
    hm = header_pattern.search(content)
    if not hm:
        err(command, "skill_md_parse_error",
            path=str(p), reason="header not found")

    # 단계 3: 헤더 이후 섹션 본문 추출
    section_start = hm.end()
    # 다음 같은 레벨 또는 상위 헤더 직전까지
    level = len(hm.group(1))  # ## → 2, ### → 3 등
    next_header_pattern = re.compile(
        r"^#{1," + str(level) + r"}\s+",
        re.MULTILINE
    )
    nh = next_header_pattern.search(content, section_start)
    section = content[section_start: nh.start() if nh else len(content)]

    # 단계 4: 마크다운 표 헤더 식별
    table_header_pattern = re.compile(
        r"^\|\s*#\s*\|\s*(?:단계|Phase)\s*\|\s*항목\s*\|",
        re.MULTILINE
    )
    thm = table_header_pattern.search(section)
    if not thm:
        err(command, "skill_md_parse_error",
            path=str(p), reason="table header not found")

    # 단계 5: 구분선 다음부터 데이터 행 추출
    after_header_pos = thm.end()
    # 구분선 건너뛰기
    sep_end = section.find("\n", after_header_pos)
    sep_end2 = section.find("\n", sep_end + 1)
    data_text = section[sep_end2 + 1:]

    # 단계 6: 각 행 파싱
    row_pattern = re.compile(
        r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([⬜🔄✅❌\-])\s*\|",
        re.MULTILINE
    )
    matches = row_pattern.findall(data_text)

    # 단계 7: 0건이면 에러
    if not matches:
        err(command, "skill_md_parse_error",
            path=str(p), reason="no rows found")

    rows = []
    for i, (rid, stage, item, status_label) in enumerate(matches):
        stage = stage.strip()
        item  = item.strip()

        # 단계 9: stage enum 검증
        if stage not in STAGE_ENUM:
            err(command, "invalid_stage_enum",
                value=stage, detail=f"row {rid}")

        # 단계 8: status_label → status 매핑
        status = LABEL_STATUS_MAP.get(status_label, "pending")

        row = {
            "row_id":       i + 1,
            "stage":        stage,
            "item":         item,
            "status":       "pending",  # init 시 모두 pending으로 초기화
            "status_label": "⬜",
            "timestamp":    None,
            "owner":        "PM",
            "note":         None,
        }
        rows.append(row)
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# pipeline.json 스펙 로딩·검증 (070 F-001/F-002, PLAN §3.1.2/§3.2.2)
# ─────────────────────────────────────────────────────────────────────────────

def load_pipeline_spec(spec_path, command):
    """pipeline.json 로드. 없으면 spec_file_not_found, 파싱 실패 시 spec_invalid_json."""
    p = pathlib.Path(spec_path)
    if not p.exists():
        err(command, "spec_file_not_found", path=str(p))
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(command, "spec_invalid_json", detail=str(e))


def validate_pipeline_spec(spec):
    """pipeline.json 스펙 검증 → violations[] (070 F-001 R-1/R-6, PLAN §3.1.2 DEC-2).

    검사 항목:
    ① 필수 필드(spec_version/skill/meta/task_steps) 존재       → spec_missing_field
    ② skill enum 정합                                          → spec_skill_invalid
    ③ task_steps[].stage ∈ STAGE_ENUM                          → spec_stage_invalid
    ④ key 형식(KEY_PATTERN)                                    → spec_key_format_invalid
    ⑤ key 유일성(스펙 내)                                       → spec_key_duplicate
    ⑥ id 1..N 순차                                              → spec_id_sequence_invalid
    ⑦ key의 stage_slug가 실제 stage와 정합                     → spec_key_stage_mismatch
    반환: [{code, id?, key?, detail}] (cmd_validate violations 포맷 차용)
    """
    violations = []

    required_top = ["spec_version", "skill", "meta", "task_steps"]
    for f in required_top:
        if f not in spec:
            violations.append({"code": "spec_missing_field", "detail": f"missing field: {f}"})
    if violations:
        # 최상위 필수 필드가 없으면 하위 검사(task_steps 순회 등)는 의미가 없다
        return violations

    skill_enum = ["opp", "opd", "opds", "opdw", "opwt", "opgc", "oppd", "opsdd", "oppl", "opdd"]
    if spec.get("skill") not in skill_enum:
        violations.append({"code": "spec_skill_invalid", "detail": f"skill '{spec.get('skill')}' not in enum"})

    task_steps = spec.get("task_steps") or []
    seen_keys = {}
    for idx, ts in enumerate(task_steps):
        ts_id = ts.get("id")
        ts_key = ts.get("key")
        ts_stage = ts.get("stage")

        if ts_stage not in STAGE_ENUM:
            violations.append({"code": "spec_stage_invalid", "id": ts_id, "key": ts_key,
                                "detail": f"stage '{ts_stage}' not in STAGE_ENUM"})

        if ts_key is not None:
            if not KEY_PATTERN.match(ts_key):
                violations.append({"code": "spec_key_format_invalid", "id": ts_id, "key": ts_key,
                                    "detail": f"key '{ts_key}' does not match pattern"})
            if ts_key in seen_keys:
                violations.append({"code": "spec_key_duplicate", "id": ts_id, "key": ts_key,
                                    "detail": f"key '{ts_key}' duplicated (also id {seen_keys[ts_key]})"})
            else:
                seen_keys[ts_key] = ts_id

            if ts_stage in STAGE_ENUM and "." in ts_key:
                expected_slug = stage_to_slug(ts_stage)
                actual_slug = ts_key.split(".", 1)[0]
                if actual_slug != expected_slug:
                    violations.append({"code": "spec_key_stage_mismatch", "id": ts_id, "key": ts_key,
                                        "detail": f"key stage_slug '{actual_slug}' != stage_to_slug('{ts_stage}')='{expected_slug}'"})

        if ts_id != idx + 1:
            violations.append({"code": "spec_id_sequence_invalid", "id": ts_id, "key": ts_key,
                                "detail": f"expected id {idx + 1}, got {ts_id}"})

        # 091 F-004 R-10: task_steps[].gate 검사 4건 (PLAN §3.4.2 (1))
        gate = ts.get("gate")
        if gate is not None:
            if not isinstance(gate, dict):
                violations.append({"code": "spec_gate_type_invalid", "id": ts_id, "key": ts_key,
                                   "detail": f"gate must be object, got {type(gate).__name__}"})
            else:
                for f in ("artifacts", "checklist"):
                    if f not in gate:
                        violations.append({"code": "spec_gate_missing_field", "id": ts_id, "key": ts_key,
                                           "detail": f"gate missing field: {f}"})
                    elif not isinstance(gate[f], list) or any(not isinstance(x, str) for x in gate[f]):
                        violations.append({"code": "spec_gate_field_type_invalid", "id": ts_id, "key": ts_key,
                                           "detail": f"gate.{f} must be array of string"})
                if isinstance(gate.get("checklist"), list) and len(gate["checklist"]) == 0:
                    violations.append({"code": "spec_gate_checklist_empty", "id": ts_id, "key": ts_key,
                                       "detail": "gate.checklist must not be empty"})

    return violations


def build_rows_from_pipeline_json(spec_path, command, mode):
    """.json 스펙 → rows[] (070 F-002 R-2, PLAN §3.2.2). 절차:
    1. spec = load_pipeline_spec(spec_path, command)
    2. violations = validate_pipeline_spec(spec); 있으면 spec_validation_failed
    3. task_steps[] 순회하며 row 구성(key·conditional 영속. 093 F-001 이후 모드별 분기 없음
       — 사용자 확인 행도 전 모드 pending/PM으로 초기화되고 자동 승인은 진입 훅이 담당)
    """
    spec = load_pipeline_spec(spec_path, command)
    violations = validate_pipeline_spec(spec)
    if violations:
        err(command, "spec_validation_failed", detail=violations[0])

    rows = []
    for i, ts in enumerate(spec["task_steps"]):
        row = {
            "row_id":       i + 1,
            "stage":        ts["stage"],
            "item":         ts["item"],
            "key":          ts["key"],
            "status":       "pending",
            "status_label": "⬜",
            "timestamp":    None,
            "owner":        "PM",
            "note":         None,
        }
        if ts.get("conditional"):
            row["conditional"] = True  # DEC-1 — 순수 메타데이터, 자동 na 없음
        if ts.get("gate"):
            row["gate"] = ts["gate"]  # 091 F-004 R-9(a): init-time 정적 스냅샷 영속화

        rows.append(row)
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# 9개 서브 명령 구현
# ─────────────────────────────────────────────────────────────────────────────

# ── 1. init ──────────────────────────────────────────────────────────────────

def cmd_init(args):
    """PLAN §2.11 G-8 — state.json + STATE.md 생성"""
    command = "init"
    # init은 신규 태스크 폴더를 최초 초기화하는 명령이므로, 상위 디렉토리가 쓰기
    # 가능하면 리프 디렉토리를 자동 생성한다(하위호환: 기존 디렉토리 존재 시 무해,
    # 생성 불가 시 기존과 동일하게 task_path_not_found).
    _p = pathlib.Path(args.task_path)
    if not _p.is_dir():
        try:
            _p.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass  # 아래 resolve_task_path가 동일하게 task_path_not_found 처리
    task_path = resolve_task_path(args.task_path, command)

    # --rows-acts 시그니처 정의만 (§2.20.3, R-13)
    if getattr(args, "rows_acts", None):
        err(command, "rows_acts_not_implemented",
            note="opsdd ACT dynamic injection is out of scope for task 134. Track at R-13.",
            exit_code=2)

    # 094 R-4/D-2: --import-existing 제거 — STATE.md 저널화로 파싱 대상(파이프라인
    # 표)이 소멸했으므로 명시적으로 거부한다. argparse 정의는 하위 호환을 위해
    # 유지하되 help는 감춘다(§3.2.2 (2)).
    if getattr(args, "import_existing", False):
        err(command, "import_existing_removed")

    # C-1: --rows-spec / --rows-from 배타 (§2.19)
    if args.rows_spec and args.rows_from:
        err(command, "rows_input_conflict")

    state_file = task_path / "state.json"

    # C-4: --force 사용 시 --note 필수 (§2.17 트리거 #1)
    if args.force and not args.note:
        err(command, "note_required_for_force")

    # 멱등성 검증 (T-8)
    if state_file.exists() and not args.force and not args.import_existing:
        err(command, "already_initialized")

    # 시점 취득 (T-5)
    now_str = get_kst_datetime(command)

    # 행 구성 결정
    rows = []

    if args.rows_spec:
        rows = build_rows_from_spec(args.rows_spec, command, args.mode)
    elif args.rows_from:
        # 070 R-2: --rows-from 확장자 분기 — .json(신규 pipeline.json 스펙) vs
        # .md(레거시 SKILL.md 파싱, deprecated stderr 경고 1줄).
        if args.rows_from.endswith(".json"):
            rows = build_rows_from_pipeline_json(args.rows_from, command, args.mode)
        else:
            print('{"warning":"--rows-from <SKILL.md> markdown 파싱은 deprecated. '
                  'references/pipeline.json으로 이관하세요 (task 070)."}', file=sys.stderr)
            rows = build_rows_from_skill_md(args.rows_from, command, args.mode)
    else:
        # 행 없이 init — 최소 1행 빈 구조는 허용 안 함, 경고 없이 빈 rows로 진행
        rows = []

    # task_id = 마지막 디렉토리명
    task_id = task_path.name

    # 070 후속 R-3: rows[]에 key가 하나라도 있으면(pipeline.json 경로) schema_version
    # "1.1" 승격. .md 파싱/--rows-spec/--import-existing(key 없음) 경로는 "1.0" 유지.
    # 단순·결정론 규칙(PLAN §3.2.2 diff, task 070 후속 Part B).
    schema_version = "1.1" if any(r.get("key") for r in rows) else "1.0"

    # 072 F-001: '다음 액션' state.json 영속화 (R-1) — 계산식은 기존 관례 그대로 재사용
    next_action = args.next_action or "PLAN 단계 진입"

    state = {
        "task_id":        task_id,
        "skill":          args.skill,
        "mode":           args.mode,
        "schema_version": schema_version,
        "created_at":     now_str,
        "updated_at":     now_str,
        "current_status": "in_progress",
        "rows":           rows,
        "next_action":    next_action,
    }

    # 092 F-5: worktree 경로 조건부 영속화.
    # [MUST] 미지정 시 키 자체를 생성하지 않는다 — 기존 state.json과 스키마·바이트 동일(TASK F-5 AC).
    if getattr(args, "worktree", None):
        state["worktree"] = args.worktree

    # force 사용 시 기존 state.json의 created_at 보존
    if state_file.exists() and args.force:
        try:
            old = json.loads(state_file.read_text(encoding="utf-8"))
            state["created_at"] = old.get("created_at", now_str)
        except Exception:
            pass

    save_state_json(task_path, state)

    # 094 §3.2.2 (2): STATE.md 저널 생성 (import 분기 소멸 — 항상 신규 템플릿)
    task_title = args.task_title or task_id
    new_md = _build_new_state_md(task_title, now_str)
    save_state_md(task_path, new_md)

    # force 사용 시 의사결정 로그 기재 (§2.17 트리거 #1)
    if args.force:
        updated_md = load_state_md(task_path)
        updated_md = append_decision_log(
            updated_md, now_str,
            "force flag used at init",
            resolve_owner_placeholder(args.note)
        )
        save_state_md(task_path, updated_md)

    ok(command,
       task_path=str(task_path),
       task_id=task_id,
       rows_count=len(rows),
       created_at=now_str,
       # 094 D-2: --import-existing 제거 후에도 응답 키는 유지하고 값만 고정(제약 ③)
       import_existing=False,
       todo_mirror=build_todo_mirror(state, "create"))


def _build_new_state_md(task_title, now_str):
    """신규 STATE.md 저널 템플릿 생성 (094 §3.1.2 (1), D-1).
    파생 섹션(마커/파이프라인 표/'## 현재 상태'/'## 다음 액션')을 전부 제거하고
    의사결정 로그·블로커만 남긴 저널로 재정의한다. 기계 상태(rows/현재 상태/
    다음 액션)의 SSOT는 state.json 단일이며, 조회는 `state-tool show`로 일원화된다."""
    return f"""# STATE: {task_title}

> 최종 갱신: {now_str}
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음
"""

# ── 2. show ───────────────────────────────────────────────────────────────────

def cmd_show(args):
    """094 §3.3.2 — 파이프라인 현황 조회. R-5: state.json이 파생 표시의 유일한
    렌더 원천이다(md/json 공통). 레거시(001~093, 마커+표 보유) STATE.md는 동결
    텍스트로만 취급되며 절대 최신 현황으로 오반환되지 않는다(H-5)."""
    command = "show"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)
    fmt       = getattr(args, "format", "md") or "md"

    md = load_state_md(task_path)
    legacy = bool(md) and (PIPELINE_MARKER_START in md and PIPELINE_MARKER_END in md)

    if fmt == "json":
        ok(command, format="json", marker_present=legacy, data=state)
        return

    if fmt == "full":
        if md is None:
            ok(command, format="full", content="(STATE.md 없음)")
            return
        banner = (LEGACY_FROZEN_BANNER + "\n\n") if legacy else ""
        ok(command, format="full", content=banner + md)
        return

    # md (기본) — state.json 단일 파생(§3.3.2 (1))
    head = [
        "## 현재 상태",
        f"- 모드: {state.get('mode')}",
        f"- 상태: {STATUS_TEXT.get(state.get('current_status'), state.get('current_status'))}",
        f"- 다음 액션: {state.get('next_action') or '-'}",
        "",
    ]
    body = render_pipeline_table(state["rows"])
    banner = (LEGACY_FROZEN_BANNER + "\n\n") if legacy else ""
    ok(command, format="md", marker_present=legacy,
       content=banner + "\n".join(head) + body)

# ── 3. advance ────────────────────────────────────────────────────────────────

def cmd_advance(args):
    """PLAN §2.1, T-7 — ⬜→🔄 전환"""
    command = "advance"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)
    row_index = resolve_row_index(state, command,
                                  getattr(args, "task_step", None),
                                  getattr(args, "task_step_id", None),
                                  args.row)
    row       = state["rows"][row_index]

    if row["status"] not in ("pending",):
        err(command, "row_not_found",
            message=f"row {row['row_id']} is already {row['status']}, advance only allows pending→in_progress",
            row_id=row["row_id"])

    # 단계 건너뛰기 차단 (PLAN §M-A)
    # PM 경로: 앞 모든 행 검증 (full). 워커 경로: 앞 단계 행만 검증 (prior_stage_only).
    _guard_scope = "prior_stage_only" if getattr(args, "as_worker", False) else "full"

    # 093 F-002 R-2: 앞 단계 미완 사용자 확인 행 자동 승인 (stage-transition guard보다 먼저)
    now_str = get_kst_datetime(command)
    auto_approved = auto_approve_prior_user_confirmations(
        state, row_index, command,
        as_worker=getattr(args, "as_worker", False),
        force=getattr(args, "force", False), now_str=now_str)

    check_stage_transition_guard(state, row_index, command, force=False,
                                 scope=_guard_scope)

    # CLOSE 진입 게이트 (§2.16 G-13)
    check_close_gate(state, row_index, command)

    # 005 명확화 게이트 — TASK→다음 단계 첫 행 진입 차단 (상태 변경 전)
    _run_clarification_hook(task_path, state, row_index, command,
                            auto_pass=getattr(args, "auto_pass", False),
                            force=getattr(args, "force", False))

    # 106 code-scan 인용 게이트 — EXECUTE 첫 행 진입 차단 (save_state_json() 이전)
    _run_code_scan_citation_hook(task_path, state, row_index, command,
                                 auto_pass=getattr(args, "auto_pass", False),
                                 force=getattr(args, "force", False))

    row["status"]       = "in_progress"
    row["status_label"] = "🔄"
    row["timestamp"]    = now_str
    if args.note:
        row["note"] = resolve_owner_placeholder(args.note)

    state["updated_at"] = now_str

    # 072 F-002/F-003: '다음 액션' 자동 파생(프론티어) + --next-action 오버라이드(비지속, M-3)
    state["next_action"] = getattr(args, "next_action", None) or _derive_next_action(state)
    save_state_json(task_path, state)

    _jw = sync_state_md(task_path, state, now_str, command)
    ok(command, row_id=row["row_id"], stage=row["stage"], item=row["item"],
       status="in_progress", timestamp=now_str,
       auto_approved=auto_approved,
       todo_mirror=build_todo_mirror(state, "update"),
       **(_jw or {}))

# ── 4. mark ───────────────────────────────────────────────────────────────────

def _parse_step(step_str):
    """--step "N/M" → (N, M) 반환. 형식 위반/None이면 None 반환 (보수적 — 기존 done 동작 유지).
    017: 다중 Step 조기 done 가드. 표준 라이브러리만(re) — T-11.
    """
    m = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", step_str or "")
    if not m:
        return None
    n, total = int(m.group(1)), int(m.group(2))
    if total < 1 or n < 0 or n > total:
        return None
    return (n, total)


def _worker_duration_minutes(value):
    """--worker-duration-minutes 값 파서 — 0 이상 정수(분)만 허용 (103 R-15).

    argparse `type=`으로 소비되어 음수(`-5`)·소수(`1.5`)·비수치(`abc`)·공문자열을
    파싱 시점에 거부한다(exit 2). ERROR_CODES를 신설하지 않는 이유는 `--owner`
    choices 위반이나 `--task-step-id` 정수 위반과 동일한 "CLI 인자 형식 오류"
    계열이기 때문이다 — 기존 인자 검증 경로와 동일하게 argparse가 처리한다.

    0은 유효값이다(측정했으나 1분 미만). '측정하지 않음'은 인자 미지정으로
    표현되며 그 경우 행에 필드 자체가 생기지 않는다(집계 기준 16-a 축퇴).
    """
    if not re.fullmatch(r"\d+", str(value).strip()):
        raise argparse.ArgumentTypeError(
            f"0 이상 정수(분)여야 합니다: {value!r}")
    return int(value)


# ─────────────────────────────────────────────────────────────────────────────
# 103 강제 2단 — 차단 코드 카탈로그
#
# ERROR_CODES와 물리적으로 분리한다. 이유는 WARNING_CODES와 동일하다 —
# ERROR_CODES 키 집합은 회귀 테스트가 실측/HEAD 대조로 고정하고 있어 종수를
# 늘리면 계약이 깨진다. `err(..., message=...)`로 문구를 직접 넘기면 카탈로그를
# 늘리지 않고도 전용 코드를 쓸 수 있다.
# ─────────────────────────────────────────────────────────────────────────────
BLOCK_CODES = {
    "worker_duration_undeclared":
        "CLOSE 진입 차단 — 워커 디스패치 규범 단계의 행 {count}건이 워커 소요를 "
        "기록하지도, 미측정을 선언하지도 않았습니다: {rows}. "
        "각 행에 `--worker-duration-minutes <분>`으로 소요를 넣거나, 워커를 돌리지 "
        "않았다면 `--worker-duration-unknown`으로 미측정임을 명시하십시오. "
        "침묵은 통과하지 못합니다 — 워커 완료 알림의 duration_ms는 세션과 함께 "
        "사라지고 행에는 완료 시각만 남아 사후 복구가 불가능하기 때문입니다. "
        "부득이하면 `--force --note <사유>`로 강제 통과할 수 있으며, 그 사실이 "
        "의사결정 로그에 남습니다.",
}

# 워커 디스패치가 **규범**인 단계. 하네스 §1 「디스패치 의무 원칙」이 워커 디스패치로
# 정의한 단계들이며, TASK(TASK.md 작성)·CLOSE(DONE.md 작성)는 PM 직접 수행이 규범이라
# 제외한다. 이 집합과 아래 `_WORKER_DISPATCH_ITEM_PREFIX`가 결합해 **PM의 자발적
# 표시(--as-worker)에 의존하지 않는** 판정 근거를 만든다.
_WORKER_DISPATCH_STAGES = {
    "ANALYSIS", "PLAN", "TEST-SCENARIO", "EXECUTE", "TEST",
    "WIREFRAME", "SPEC", "DESIGN", "REVIEW", "VERIFY", "SCAN", "CHECK",
    "REPORT", "WBS", "DICT", "MODEL", "DDL/MIGRATION",
}

# 같은 단계 안에서도 「작업」 행만 워커 디스패치 지점이다. `PM Gate`·`사용자 확인`·
# `목표-커버 게이트`는 PM/사용자 판정 행이므로 소요를 요구하면 전부 오탐이 된다.
# 실 pipeline.json 10종 실측: 작업 행 item은 "작업" 또는 "작업 (…)" 형태다.
_WORKER_DISPATCH_ITEM_PREFIX = "작업"

# 워커 소요 계측이 도입된 날(`worker_duration_minutes` 필드 신설). 이 날짜 **이전에
# 생성된** 태스크는 선언할 수단 자체가 없었으므로 CLOSE 차단에서 유예한다.
# 이후 생성 태스크에는 예외가 없다 — 캡틴 지시 「반드시 적용」.
_WORKER_MEASUREMENT_EPOCH = "2026-08-26"


def is_worker_dispatch_row(row):
    """이 행이 **워커 디스패치가 규범인 지점**인지 판정한다 (103 강제 2단).

    핵심은 `--as-worker`/`--worker-stage`를 **보지 않는다**는 점이다. 그 인자는 PM이
    자발적으로 붙이는 신호이고, 붙이지 않으면 판정 자체가 성립하지 않아 규범이 통째로
    우회된다(실측: 다른 프로젝트 태스크가 15행 전건 미기록으로 통과). 그래서 근거를
    행의 `stage`·`item`에서 가져온다 — PM 의사와 무관한 파이프라인 구조다.
    """
    if row.get("stage") not in _WORKER_DISPATCH_STAGES:
        return False
    item = (row.get("item") or "").strip()
    if not item.startswith(_WORKER_DISPATCH_ITEM_PREFIX):
        return False
    # 사용자 확인 행은 캡틴 승인 지점이지 워커 디스패치 지점이 아니다.
    return row.get("owner") != "user"


def collect_undeclared_worker_rows(state):
    """워커 소요가 **기록도 선언도 없는** 완료 행을 모은다 (CLOSE 차단 판정 근거).

    「미측정 선언」(`worker_duration_unknown: true`)과 「침묵」(둘 다 부재)을 가른다.
    집계는 둘을 같게 다루지만(축퇴 규칙 16-a), 게이트는 반드시 달리 다뤄야 한다 —
    그러지 않으면 선언할 이유가 사라지고 강제가 무의미해진다.
    """
    out = []
    for row in state.get("rows", []):
        if row.get("status") != "done":
            continue
        if not is_worker_dispatch_row(row):
            continue
        if row.get("worker_duration_minutes") is not None:
            continue
        if row.get("worker_duration_unknown"):
            continue
        out.append(row)
    return out


def check_worker_duration_declared(state, row_index, command, force=False):
    """CLOSE 첫 행 진입 시 워커 소요 미선언 행이 남아 있으면 **차단**한다.

    경고(`worker_duration_missing`)는 조기 발견용이고 이 함수가 최종 방어다.
    경고만으로는 무시하면 그대로 통과하므로, 태스크를 닫는 지점에서 한 번은
    반드시 걸리게 한다. 통과 경로는 「소요 기록」 또는 「미측정 선언」 둘뿐이며,
    `--force`는 의사결정 로그를 남기는 최후 수단이다.

    **소급 유예는 `created_at` 기준이다** — 태스크가 계측 도입 시점
    (`_WORKER_MEASUREMENT_EPOCH`) **이전에 생성**됐으면 통과시킨다. 그 시기의 태스크는
    `worker_duration_minutes` 필드가 존재하지 않아 선언할 방법 자체가 없었고, 그것까지
    막으면 과거 태스크를 영구히 닫을 수 없다.

    「기록이 한 건도 없으면 유예」로 두지 않는 이유가 핵심이다 — 그 규칙은 **워커를
    돌리고도 한 건도 기록하지 않은 신규 태스크**를 그대로 통과시켜(실측 사례 존재)
    강제가 무의미해진다. 생성 시점 기준이면 도입 이후 태스크에는 **예외가 없다**.

    `created_at` 부재·파싱 실패는 유예로 처리한다(fail-safe) — 판정 불가를 차단으로
    바꾸면 정상 태스크가 닫히지 않는 쪽이 더 위험하다.
    """
    if force:
        return
    row = state["rows"][row_index]
    if row.get("stage") != "CLOSE":
        return
    is_first_close = (row_index == 0
                      or state["rows"][row_index - 1].get("stage") != "CLOSE")
    if not is_first_close:
        return

    created = (state.get("created_at") or "")[:10]
    if not created or created < _WORKER_MEASUREMENT_EPOCH:
        return  # 계측 도입 이전 생성 — 소급 유예 (부재·파싱 실패도 fail-safe로 유예)

    missing = collect_undeclared_worker_rows(state)
    if not missing:
        return

    labels = ", ".join(
        f"row {r.get('row_id')} {r.get('stage')}/{r.get('item')}" for r in missing)
    err(command, "worker_duration_undeclared",
        message=BLOCK_CODES["worker_duration_undeclared"].format(
            count=len(missing), rows=labels),
        undeclared_rows=[r.get("row_id") for r in missing])


def build_worker_duration_warning(args, row, worker_minutes):
    """103 R-21 — 워커 디스패치 행을 소요 없이 완료 처리했을 때의 경고를 만든다.

    반환은 경고 dict 1개 또는 None이다. **상태를 만지지 않고 exit code도 바꾸지
    않는다** — 산출물(`state.json`/`STATE.md`)은 경고 유무와 무관하게 바이트 동일이며,
    경고는 오직 `mark` stdout JSON의 `warnings` 배열에만 실린다.

    판정은 4개 관문을 모두 통과해야 성립한다. 오탐(정당한 호출에 뜨는 경고)이
    반복되면 PM이 경고 전체를 무시하게 되므로, 각 관문은 "이 경고가 실제로 유실을
    막는 상황"만 남기도록 좁힌다:

      (1) 이미 값이 실렸으면 경고할 것이 없다.
      (2) `--worker-duration-unknown`으로 미측정을 **명시**했으면 침묵한다
          (§(c) 억제 — 정당한 미측정을 소음으로 만들지 않는다).
      (3) `--as-worker` 또는 `--worker-stage`가 있어야 한다. 이 두 인자는 "이 행은
          워커가 수행했다"는 유일한 기계 판독 신호다. PM 직접 수행 행은 둘 다 없이
          호출되므로 구조적으로 제외된다.
      (4) 이 호출로 행이 실제 `done`이 되어야 한다. `--action-step N/M`(N<M)은 행을
          `in_progress`로 남기며 소요는 마지막 Step에서 합산 기록하는 것이 규범이므로,
          중간 진행 보고마다 경고를 내면 전부 오탐이다.

    추가로 `owner == "user"`인 행은 제외한다. 사용자 확인 행은 캡틴 승인 지점이지
    워커 디스패치 지점이 아니므로, 설령 `--as-worker`가 함께 실렸더라도 여기에 소요를
    요구하는 것은 오탐이다(캡틴 지시 §1(a) 명시 제외 대상).

    093 F-005 재-auto-pass no-op 경로는 이 함수에 도달하기 전에 조기 반환하므로,
    이미 완료된 행을 다시 두드리는 멱등 호출에도 경고가 뜨지 않는다.
    """
    if worker_minutes is not None:
        return None
    if getattr(args, "worker_duration_unknown", False):
        return None
    # (3) 워커 신호 — 인자(PM의 자발적 표시) **또는** 행 구조(파이프라인 규범).
    # 후자를 더한 것이 103 강제 2단의 핵심이다. 인자만 보면 PM이 `--as-worker`를
    # 붙이지 않는 순간 경고가 침묵해 규범이 통째로 우회된다(실측 사례 존재).
    _arg_signal = bool(getattr(args, "as_worker", False)
                       or getattr(args, "worker_stage", None))
    if not (_arg_signal or is_worker_dispatch_row(row)):
        return None
    if row.get("status") != "done":
        return None
    if row.get("owner") == "user":
        return None

    code = "worker_duration_missing"
    return {
        "code": code,
        "message": WARNING_CODES[code].format(
            row_id=row.get("row_id"), stage=row.get("stage")),
    }


def cmd_mark(args):
    """PLAN §2.1, T-7, §2.4, §2.15 G-12, §2.16 G-13 — ⬜/🔄→✅"""
    command = "mark"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    # C-2: --owner / --auto-pass 배타 (§2.19)
    if args.auto_pass and args.owner and args.owner != "auto":
        err(command, "owner_flag_conflict")

    # C-3: --as-worker → --worker-stage 필수 (§2.19)
    if args.as_worker and not args.worker_stage:
        err(command, "worker_stage_required")

    # C-4: --force → --note 필수 (§2.17 트리거 #3, #8)
    if args.force and not args.note:
        err(command, "note_required_for_force")

    row_index = resolve_row_index(state, command,
                                  getattr(args, "task_step", None),
                                  getattr(args, "task_step_id", None),
                                  args.row)
    row       = state["rows"][row_index]

    # 워커 권한 게이트 (§2.4, T-10)
    if args.as_worker:
        allowed_stage = args.worker_stage
        if row["stage"] != allowed_stage:
            if args.force:
                # §2.17 트리거 #3 기재 후 진행
                pass  # 아래 note에서 처리
            else:
                err(command, "worker_scope_violation",
                    worker_stage=allowed_stage,
                    row_id=row["row_id"],
                    stage=row["stage"])

    # 단계 건너뛰기 차단 (PLAN §M-A)
    # PM 경로: 앞 모든 행 검증 (full). 워커 경로: 앞 단계 행만 검증 (prior_stage_only).
    _guard_scope = "prior_stage_only" if args.as_worker else "full"

    # 093 F-002 R-2: 앞 단계 미완 사용자 확인 행 자동 승인 (stage-transition guard보다 먼저)
    now_str = get_kst_datetime(command)
    auto_approved = auto_approve_prior_user_confirmations(
        state, row_index, command,
        as_worker=args.as_worker, force=args.force, now_str=now_str)

    check_stage_transition_guard(state, row_index, command, force=args.force,
                                 scope=_guard_scope)

    # CLOSE 진입 게이트 (§2.16 G-13)
    check_close_gate(state, row_index, command,
                     auto_pass=args.auto_pass, force=args.force, owner=args.owner)

    # 103 강제 2단 (b) — 워커 소요 미선언 행이 남아 있으면 CLOSE 진입을 차단한다.
    # 상태 변경 전 구간이라 거부 시 파일이 오염되지 않는다.
    check_worker_duration_declared(state, row_index, command, force=args.force)

    # 005 명확화 게이트 — TASK→다음 단계 첫 행 진입 차단 (상태 변경 전)
    _run_clarification_hook(task_path, state, row_index, command,
                            auto_pass=args.auto_pass, force=args.force)

    # 106 code-scan 인용 게이트 — EXECUTE 첫 행 진입 차단 (save_state_json() 이전)
    _cs_forced_missing = _run_code_scan_citation_hook(
        task_path, state, row_index, command,
        auto_pass=args.auto_pass, force=args.force)

    # semi-agentic 모드에서 EXECUTE-equivalent 이전 행은 --auto-pass 거부
    # (D-DEC-5, 093 F-003 단일 판정 소비 — PLAN §3.3.2 (2))
    if args.auto_pass:
        _allowed, _deny = can_auto_approve_user_confirmation(row["stage"], state.get("mode"))
        if not _allowed and _deny == "semi_agentic_pre_execute":   # [MUST] 이 사유만 소비 (DEC-E)
            err(command, "semi_agentic_pre_execute_auto_pass_denied",
                row_id=row["row_id"], stage=row["stage"])

    # 091 F-004 R-11: PM Gate 산출물 검증 (H-1 — save_state_json() 이전 검증 구간에 위치)
    _gate_forced_missing = check_gate_artifacts(task_path, row, command, force=args.force)

    # 017: 다중 Step 진행률 파싱 + 조기 done 가드 (R-1, C-1, C-5)
    # 070 R-5: --action-step은 dest="step" 공유 별칭(argparse) — 직접 호출(테스트)
    #   경로에서는 args.step/args.action_step이 분리된 속성일 수 있으므로 폴백 병합한다.
    _step_str = getattr(args, "step", None) or getattr(args, "action_step", None)
    _step_pair = _parse_step(_step_str) if _step_str else None

    # 103 R-15: 워커 소요(분). 미지정(None)이면 행에 필드를 만들지 않는다 — 기존
    #   태스크 무영향(집계 기준 16-a 축퇴). 값 검증(0 이상 정수)은 argparse
    #   type=_worker_duration_minutes가 파싱 시점에 수행한다.
    _worker_minutes = getattr(args, "worker_duration_minutes", None)

    # 093 F-005 R-5 멱등성 — 이미 auto 승인된 행에 대한 재-auto-pass는 상태 변경 없이 성공 반환
    #   (--force·--action-step N/M·owner=user done 행은 조건에서 제외 — 기존 경로 유지)
    # 103 R-15: --worker-duration-minutes가 실린 호출은 기록할 값이 있으므로 no-op
    #   대상에서 뺀다. 기존 호출은 이 값이 항상 None이라 조건이 종전과 동일하다.
    if (args.auto_pass and not args.force and not _step_str
            and _worker_minutes is None
            and row.get("status") == "done" and row.get("owner") == "auto"):
        ok(command, row_id=row["row_id"], stage=row["stage"], item=row["item"],
           status="done", timestamp=row.get("timestamp"), idempotent=True,
           todo_mirror=build_todo_mirror(state, "update"))
        return

    if _step_pair is not None:
        _n, _total = _step_pair
        row["step"] = f"{_n}/{_total}"           # 진행률 영속화
        if _n < _total:
            # 마지막 Step 아님 → done으로 닫지 않고 in_progress 유지 (조기 done 차단)
            row["status"]       = "in_progress"
            row["status_label"] = "🔄"
        else:
            # n == total → 마지막 Step → done (R-2)
            row["status"]       = "done"
            row["status_label"] = "✅"
    else:
        # --step 미지정/비정형 → 기존 즉시 done (C-4 하위 호환)
        row["status"]       = "done"
        row["status_label"] = "✅"
    row["timestamp"]    = now_str

    # 103 R-15: 지정된 경우에만 기록 — 미지정 행은 키 자체가 생기지 않는다(H-1).
    if _worker_minutes is not None:
        row["worker_duration_minutes"] = _worker_minutes
    # 103 강제 2단 (c) — 미측정 **선언**을 행에 남긴다. 남기지 않으면 CLOSE 차단이
    # 「선언했음」과 「침묵」을 구별할 수 없어 강제가 성립하지 않는다.
    if getattr(args, "worker_duration_unknown", False):
        row["worker_duration_unknown"] = True

    # note 소유자 호칭 치환 (PLAN §3.1.2, TASK 054) — 3분기 공용 1회 산출
    note_text = resolve_owner_placeholder(args.note)

    # owner 결정
    if args.auto_pass:
        row["owner"] = "auto"
        # 093 F-005 R-5: 접두 3분기 — 빈 note / 이미 접두 보유(중첩 방지) / 신규 부여
        if not note_text:
            row["note"] = _AUTO_PASS_PREFIX
        elif note_text.startswith(f"{_AUTO_PASS_PREFIX}:"):
            row["note"] = note_text
        else:
            row["note"] = f"{_AUTO_PASS_PREFIX}: {note_text}"
    elif args.owner:
        row["owner"] = args.owner
        if note_text:
            row["note"] = note_text
    else:
        row["owner"] = "PM"
        if note_text:
            row["note"] = note_text

    state["updated_at"] = now_str

    # CLOSE 단계 마지막 행 → current_status = done (§2.11 G-6)
    # 014 Phase 4: 새 표준 구조의 CLOSE 마지막 행은 "DONE.md 생성"이고, 레거시 구조는
    #   "State Gate"였다. 항목명에 의존하지 않고 "CLOSE 단계의 마지막 행" 여부로 판정한다.
    is_close_last = (
        row["stage"] == "CLOSE" and
        (row_index == len(state["rows"]) - 1 or
         state["rows"][row_index + 1]["stage"] != "CLOSE")
    )
    # 017: in_progress(N<M)로 남긴 행은 current_status=done 전환에서 제외 — 다중 Step CLOSE 마지막 행 오판 방지
    if is_close_last and row["status"] == "done":
        state["current_status"] = "done"

    # 072 F-002/F-003: '다음 액션' 자동 파생(프론티어) + --next-action 오버라이드(비지속, M-3)
    state["next_action"] = getattr(args, "next_action", None) or _derive_next_action(state)

    save_state_json(task_path, state)

    # TEST stage done 시 verify 자동 훅 (PLAN 013)
    if row["stage"] == "TEST":
        scenario_path = _find_scenario_file(task_path, None)
        if scenario_path is not None:
            lines = scenario_path.read_text(encoding="utf-8").splitlines()
            mock_lines = _check_mock_patterns(lines)
            if mock_lines:
                err("mark", "mock_in_scenario", lines=mock_lines)
            missing_lines = _check_evidence(lines)
            if missing_lines:
                err("mark", "evidence_missing", lines=missing_lines)

    decision = None
    reason_text = None

    # §2.17 트리거 #2 auto-pass 로그
    if args.auto_pass:
        decision = f"agentic auto-pass at row {row['row_id']}, item={row['item']}"
        reason_text = (args.note or "agentic mode")

    # §2.17 트리거 #3 worker force 로그
    if args.as_worker and args.force:
        requested = args.worker_stage
        actual = row["stage"]
        decision = f"worker_scope_force at row {row['row_id']}, requested_stage={requested}, actual_stage={actual}"
        reason_text = args.note

    # 091 F-004 R-11(H-5): --force로 게이트 아티팩트 미충족을 우회한 경우 강제 기록
    if _gate_forced_missing:
        decision = (f"gate_artifact_force at row {row['row_id']}, key={row.get('key')}, "
                    f"missing={_gate_forced_missing}")
        reason_text = args.note

    # 106: --force로 code-scan 결과 인용 게이트를 우회한 경우 강제 기재 (091 H-5 동형)
    if _cs_forced_missing:
        decision = (f"code_scan_citation_force at row {row['row_id']}, key={row.get('key')}, "
                    f"missing={_cs_forced_missing}")
        reason_text = args.note

    _jw = sync_state_md(task_path, state, now_str, command,
                        decision=decision, reason=reason_text)

    # 088 §2.1: CLOSE 마지막 행 완료 시 메모리 히스토리 자동 연결 (R-1~R-5)
    # state.json·STATE.md 영속화가 완전히 끝난 뒤에만 실행 — 실패해도 mark 응답은
    # 항상 ok:true를 유지한다(비영속·stdout 전용 페이로드, §2.5/§2.9).
    history_link = None
    if is_close_last and row["status"] == "done":
        history_link = link_memory_history(task_path, state)

    _ok_kwargs = dict(row_id=row["row_id"], stage=row["stage"], item=row["item"],
                      status=row["status"], timestamp=now_str, owner=row["owner"],
                      auto_approved=auto_approved,
                      todo_mirror=build_todo_mirror(state, "update"))
    if history_link is not None:
        _ok_kwargs["history_link"] = history_link
    # 103 R-15: 기록한 경우에만 응답에 실어 PM이 반영값을 확인할 수 있게 한다.
    #   미지정 호출의 응답 키 집합은 종전과 완전히 동일하다(H-11 하위호환).
    if _worker_minutes is not None:
        _ok_kwargs["worker_duration_minutes"] = _worker_minutes
    if getattr(args, "worker_duration_unknown", False):
        _ok_kwargs["worker_duration_unknown"] = True
    # 103 R-21: 워커 디스패치 행인데 소요가 비었으면 경고를 실어 보낸다.
    #   경고가 없으면 `warnings` 키 자체를 만들지 않는다 — 기존 mark 호출의 응답
    #   키 집합이 종전과 완전히 동일해야 하기 때문이다(H-11, S-5와 동일 계약).
    _warning = build_worker_duration_warning(args, row, _worker_minutes)
    if _warning is not None:
        _ok_kwargs["warnings"] = [_warning]
    _gate_payload = build_gate_payload(row)
    if _gate_payload is not None:
        _ok_kwargs["gate_checklist"] = _gate_payload
    if _jw:
        _ok_kwargs.update(_jw)
    ok(command, **_ok_kwargs)

# ── 5. block ──────────────────────────────────────────────────────────────────

def cmd_block(args):
    """PLAN §2.17 트리거 #7 — any→❌. current_status → blocked 자동 전환."""
    command = "block"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)
    row_index = resolve_row_index(state, command,
                                  getattr(args, "task_step", None),
                                  getattr(args, "task_step_id", None),
                                  args.row)
    row       = state["rows"][row_index]

    now_str = get_kst_datetime(command)
    row["status"]       = "failed"
    row["status_label"] = "❌"
    row["timestamp"]    = now_str
    row["note"]         = f"block: {resolve_owner_placeholder(args.reason)}"

    # current_status → blocked 자동 전환 (§2.11 G-7)
    prev_status = state["current_status"]
    state["current_status"] = "blocked"
    state["updated_at"]     = now_str

    save_state_json(task_path, state)
    _jw = sync_state_md(task_path, state, now_str, command)

    ok(command, row_id=row["row_id"], stage=row["stage"], item=row["item"],
       status="failed", current_status="blocked", timestamp=now_str,
       todo_mirror=build_todo_mirror(state, "update"),
       **(_jw or {}))

# ── 6. validate ───────────────────────────────────────────────────────────────

def cmd_validate(args):
    """PLAN §2.6, §2.15 G-12 — 정합성 검증 → violations[]"""
    command = "validate"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    violations = []

    # 스키마 기본 필드 검증
    required_fields = ["task_id", "skill", "mode", "schema_version",
                        "created_at", "updated_at", "current_status", "rows"]
    for f in required_fields:
        if f not in state:
            violations.append({"code": "schema_violation", "row_id": None,
                                "detail": f"missing field: {f}"})

    # 행 순서 정합성 (완료되지 않은 행 뒤에 완료된 행 존재 여부는 단순 경고)
    # 사용자 확인 행 owner 검증 (§2.15 G-12)
    mode = state.get("mode", "interactive")
    for row in state.get("rows", []):
        if row.get("item") == "사용자 확인" and row.get("status") == "done":
            owner = row.get("owner")
            if owner not in ("user", "auto"):
                violations.append({
                    "code":   "user_confirmation_owner_mismatch",
                    "row_id": row["row_id"],
                    "detail": f"owner={owner}"
                })
            if owner == "auto":
                # 093 F-003 단일 판정 소비 — CLOSE 축은 평가하지 않는다
                # (H-4: 현행 validate는 CLOSE stage 자체로는 위반을 내지 않는다. 표 B V-7~V-9)
                _allowed, _deny = can_auto_approve_user_confirmation(
                    row.get("stage"), mode, include_close_axis=False)
                if not _allowed and _deny == "interactive_requires_user":
                    violations.append({
                        "code":   "auto_pass_in_interactive_mode",
                        "row_id": row["row_id"],
                        "detail": f"interactive mode but owner=auto"
                    })
                if not _allowed and _deny == "semi_agentic_pre_execute":
                    # PLAN-equivalent 이전 행에 owner=auto는 위반 (D-DEC-5)
                    violations.append({
                        "code":   "semi_agentic_pre_execute_auto_pass_denied",
                        "row_id": row["row_id"],
                        "detail": f"semi-agentic mode but owner=auto on stage={row.get('stage')}"
                    })

    count = len(violations)
    is_ok = count == 0
    print(json.dumps({
        "ok": is_ok, "command": command,
        "violations": violations, "violations_count": count
    }, ensure_ascii=False))
    sys.exit(0 if is_ok else 1)

# ── 6b. spec-validate (070 F-001 R-6) ───────────────────────────────────────

def cmd_spec_validate(args):
    """spec-validate <pipeline.json> — 단일 라인 JSON (070 R-6, DEC-2).
    {ok, command:'spec-validate', violations:[...], violations_count:N}, exit 0/1.
    (cmd_validate 출력 계약과 동일)
    """
    command = "spec-validate"
    spec = load_pipeline_spec(args.spec_path, command)
    violations = validate_pipeline_spec(spec)
    count = len(violations)
    is_ok = count == 0
    print(json.dumps({
        "ok": is_ok, "command": command,
        "violations": violations, "violations_count": count
    }, ensure_ascii=False))
    sys.exit(0 if is_ok else 1)

# ── 7. add-row ────────────────────────────────────────────────────────────────

def _auto_row_key(state, stage, item):
    """{stage_slug}.{item_slug}_{n} 자동 생성 (070 F-004 R-9, PLAN §3.4.2).
    전체 rows[] 스캔 유일성 — 동일 base로 이미 존재하는 key 개수 +1부터 증가,
    충돌 없을 때까지 증가.
    """
    stage_slug = stage_to_slug(stage)
    m = re.match(r"[a-zA-Z][a-zA-Z0-9]*", item or "")
    item_slug = m.group(0).lower() if m else "item"
    base = f"{stage_slug}.{item_slug}"

    existing_keys = {r.get("key") for r in state["rows"] if r.get("key")}
    n = 1
    candidate = f"{base}_{n}"
    while candidate in existing_keys:
        n += 1
        candidate = f"{base}_{n}"
    return candidate


def cmd_add_row(args):
    """PLAN §2.12 G-9 — 추가작업 행 삽입"""
    command = "add-row"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    # stage enum 검증 (§2.12 G-9 단계 5)
    if args.stage not in STAGE_ENUM:
        err(command, "invalid_stage_enum", value=args.stage)

    # 기존 행 식별 (070 F-003 R-4: --after-task-step/--after-task-step-id/--after(deprecated))
    after_index = resolve_row_index(state, command,
                                    getattr(args, "after_task_step", None),
                                    getattr(args, "after_task_step_id", None),
                                    args.after,
                                    addr_label="after")

    # 070 F-004 R-9: --key 명시 지정 또는 자동 생성 (전체 스캔 유일성)
    existing_keys = {r.get("key") for r in state["rows"] if r.get("key")}
    explicit_key = getattr(args, "key", None)
    if explicit_key:
        if not KEY_PATTERN.match(explicit_key):
            err(command, "task_step_key_invalid", key=explicit_key)
        if explicit_key in existing_keys:
            err(command, "task_step_key_duplicate", key=explicit_key)
        new_key = explicit_key
    else:
        new_key = _auto_row_key(state, args.stage, args.item)

    now_str = get_kst_datetime(command)

    new_row = {
        "row_id":       after_index + 2,  # 임시 — 아래서 재정렬
        "stage":        args.stage,
        "item":         args.item,
        "key":          new_key,
        "status":       "pending",
        "status_label": "⬜",
        "timestamp":    None,
        "owner":        None,
        "note":         resolve_owner_placeholder(args.note) or None,
    }

    # 삽입 (G-9 단계 3)
    state["rows"].insert(after_index + 1, new_row)

    # row_id 재정렬 (G-9 단계 4) — 삽입 후 전체 재번호 (기존 key는 불변)
    for i, row in enumerate(state["rows"]):
        row["row_id"] = i + 1

    # current_status 자동 전환 (G-9 단계 8, G-7)
    prev_status = state["current_status"]
    if prev_status == "done":
        state["current_status"] = "additional_work"
    elif prev_status == "additional_work_done":
        state["current_status"] = "additional_work"

    state["updated_at"] = now_str
    save_state_json(task_path, state)

    # §2.17 트리거 #5 의사결정 로그
    decision = f"additional row inserted after row {after_index + 1}: stage={args.stage}, item={args.item}, key={new_key}, new_row_id={after_index + 2}"
    reason   = args.note or "additional work entry"

    _jw = sync_state_md(task_path, state, now_str, command,
                        decision=decision, reason=reason)

    ok(command,
       row_id=after_index + 2,
       key=new_key,
       rows_count=len(state["rows"]),
       current_status=state["current_status"],
       **(_jw or {}))

# ── 8. status ─────────────────────────────────────────────────────────────────

def cmd_status(args):
    """PLAN §2.11 G-7 — current_status 명시 전환"""
    command = "status"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    from_status = state["current_status"]
    to_status   = args.set

    # 전이 그래프 검증 (§2.11 G-7)
    allowed = ALLOWED_TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        err(command, "invalid_status_transition",
            **{"from": from_status, "to": to_status},
            message=f"{from_status} → {to_status} 전이는 허용되지 않음")

    now_str = get_kst_datetime(command)
    state["current_status"] = to_status
    state["updated_at"]     = now_str
    save_state_json(task_path, state)

    # §2.17 트리거 #4
    decision = f"current_status changed: {from_status} → {to_status}"
    reason   = resolve_owner_placeholder(args.note) or "(none)"

    _jw = sync_state_md(task_path, state, now_str, command,
                        decision=decision, reason=reason)

    ok(command, **{"from": from_status, "to": to_status}, timestamp=now_str,
       **(_jw or {}))

# ── 9. gate-pass ──────────────────────────────────────────────────────────────

def cmd_gate_pass(args):
    """PLAN §2.13 G-10 — 4행 Gate 일괄 처리.

    [DEPRECATED — 014 Phase 4] 새 표준 행 구조(opds 10행)에는 "QA Gate"/"State Gate"
    행이 존재하지 않으므로 [QA Gate, State Gate, PM Gate, State Gate] 4행 패턴이 성립할 수
    없다. 신규 태스크는 gate-pass를 사용하지 않으며, PM Gate는 단일 mark로 통과한다.
    이 명령은 아직 옛 행 구조를 보유한 in-flight 레거시 state.json 하위호환을 위해서만
    유지되며, 성공 응답에 deprecated=True를 포함한다. 후속 버전에서 제거 예정.
    """
    command = "gate-pass"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    start_id = args.start
    rows     = state["rows"]

    # start_id 위치 찾기
    start_index = None
    for i, row in enumerate(rows):
        if row["row_id"] == start_id:
            start_index = i
            break
    if start_index is None:
        err(command, "row_not_found", row_id=start_id)

    # 4행 범위 확인
    if start_index + 3 >= len(rows):
        err(command, "gate_pattern_mismatch",
            message=f"rows {start_id}~{start_id+3} out of range (total rows: {len(rows)})",
            expected="QA Gate at row N")

    gate_rows = rows[start_index:start_index + 4]

    # 시작 행 검증 (§2.13 G-10 단계 1)
    if gate_rows[0]["item"] != "QA Gate":
        err(command, "gate_pattern_mismatch",
            expected=f"QA Gate at row {start_id}",
            found=gate_rows[0]["item"])

    # 연속 4행 패턴 검증 (§2.13 G-10 단계 2)
    found_pattern = [r["item"] for r in gate_rows]
    if found_pattern != GATE_PATTERN:
        err(command, "gate_pattern_mismatch",
            expected=GATE_PATTERN,
            found=found_pattern)

    # stage 일관성 검증 (§2.13 G-10 단계 3)
    stages = {r["stage"] for r in gate_rows}
    if len(stages) > 1:
        err(command, "gate_stage_mixed",
            message=f"4행 stage가 혼합됨: {list(stages)}")

    now_str = get_kst_datetime(command)
    stage   = gate_rows[0]["stage"]

    # 순차 ✅ 처리 (§2.13 G-10 단계 4)
    passed_ids = []
    for row in gate_rows:
        row["status"]       = "done"
        row["status_label"] = "✅"
        row["timestamp"]    = now_str
        if not row.get("owner"):
            row["owner"] = "PM"
        passed_ids.append(row["row_id"])

    state["updated_at"] = now_str
    save_state_json(task_path, state)

    # §2.17 트리거 #6
    decision = f"Gate Pass: rows {passed_ids[0]}~{passed_ids[-1]}, stage={stage}"
    reason   = args.note or "(none)"

    _jw = sync_state_md(task_path, state, now_str, command,
                        decision=decision, reason=reason)

    ok(command, rows_passed=passed_ids, stage=stage, timestamp=now_str,
       deprecated=True,
       deprecation_note="gate-pass is deprecated (014 Phase 4): new standard rows have no QA/State Gate rows; use single mark for PM Gate.",
       **(_jw or {}))

# ── 10. verify ───────────────────────────────────────────────────────────────

# 헌법 §4 "Don't fake it" — TEST-SCENARIO.md mock 코드 패턴 검출
# M-2 / (034): 코드 사용 패턴만 정규식 매칭; 단순 "mock" 단어/설명 문구는 제외.
#   'MagicMock' 맨 단어 대안 제거 — 산문(예: PM Gate 표준 문구 "MagicMock 등 부재")을
#   오탐하던 #1 원인. 실제 MagicMock() 호출은 'Mock\(' 대안이 이미 커버한다(잉여 입증: PLAN §2.1.2).
_MOCK_CODE_PATTERNS = re.compile(
    r"unittest\.mock|@patch\b|mock\.patch|Mock\(|@mock\."
)

# Pass 행 결과 키워드
_PASS_KEYWORDS = re.compile(r"^\s*(Pass|PASS|✅)\s*$")


def _find_scenario_file(task_path, scenario_arg):
    """TEST-SCENARIO.md 경로를 결정한다.
    --scenario 인자가 있으면 그 경로를 사용, 없으면 <task_path>/TEST-SCENARIO.md 시도.
    파일이 없으면 None 반환 (doc-only skip 처리).
    """
    if scenario_arg:
        p = pathlib.Path(scenario_arg)
    else:
        p = pathlib.Path(task_path) / "TEST-SCENARIO.md"
    return p if p.exists() else None


def _check_mock_patterns(lines):
    """코드 패턴 검출 — 위반 라인 번호 목록 반환.

    034 #2: 인라인 백틱(`...`) 코드 예시는 문서화/설명 표기이므로 검사 전 제거한다.
            코드펜스(```) 내부·백틱 밖 bare 라인의 실제 mock 코드는 그대로 검출(헌법 §4 유지).
            코드펜스 경계선(```/~~~으로 시작하는 줄) 자체는 검사 제외.
            백틱 미닫힘 시 해당 구간 미제거(fail-safe — 의심 시 검사 방향).
    """
    violations = []
    in_fence = False
    for lineno, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue                          # 펜스 경계선 자체는 검사 제외
        if in_fence:
            target = line                     # 코드펜스 내부 = 실제 코드 → 원문 검사
        else:
            target = re.sub(r"`[^`]*`", "", line)   # 인라인 백틱 구간 제거 후 검사
        if _MOCK_CODE_PATTERNS.search(target):
            violations.append(lineno)
    return violations


def _check_evidence(lines):
    """Pass 시나리오에 실행 증거 누락 검출 — 위반 라인 번호 목록 반환.

    탐지 전략:
    - 마크다운 표의 각 행(| ... |)을 파싱한다.
    - 셀 중 하나가 Pass/PASS/✅인 행에서 "실행 명령" 또는 "결과/출력"에 해당하는
      셀이 비어있으면 (empty or whitespace-only) 위반으로 간주한다.
    - 열 헤더는 "결과", "출력", "실행 명령"을 포함하는 행으로 인식한다.
    - 헤더를 찾기 전에 Pass 행이 나타나면 보수적 판정(위반 아님).
    """
    violations = []
    header_indices = []   # 증거 관련 열 인덱스 (실행 명령/출력)
    result_indices = []   # "결과" 열 인덱스 (Pass 판별용)
    in_header = False

    for lineno, line in enumerate(lines, start=1):
        # 마크다운 표 행 판별
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # 구분선 행(|---|) 스킵
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue

        cells = [c.strip() for c in stripped.split("|")]
        # split 결과는 앞뒤 빈 문자열 포함 → [1:-1] 로 실제 셀만
        cells = cells[1:-1] if len(cells) > 2 else cells

        # 헤더 행 감지: "결과" 또는 "실행 명령" 또는 "출력" 셀 포함
        is_header = any(
            c in ("결과", "실행 명령", "출력", "결과/출력") for c in cells
        )
        if is_header:
            header_indices = [
                i for i, c in enumerate(cells)
                if c in ("실행 명령", "출력", "결과/출력")
            ]
            # "결과" 열 인덱스를 별도로 기억 (Pass 판별용)
            result_indices = [
                i for i, c in enumerate(cells)
                if c == "결과"
            ]
            in_header = True
            continue

        if not in_header:
            continue

        # 데이터 행: 결과 열이 Pass/PASS/✅인지 확인
        is_pass_row = any(
            i < len(cells) and _PASS_KEYWORDS.match(cells[i])
            for i in result_indices
        )
        if not is_pass_row:
            continue

        # 증거 열(실행 명령/결과/출력)이 비어있으면 위반
        for i in header_indices:
            if i < len(cells) and cells[i] == "":
                violations.append(lineno)
                break

    return violations


def _check_red_evidence(lines):
    """RED 증거 누락 검출 (016 RED-first) — 위반 라인 번호 목록 반환.

    탐지 전략 (_check_evidence 패턴 미러):
    - 마크다운 표에서 "RED 증거" 헤더 열을 찾는다.
    - 데이터 행에서 "RED 증거" 셀이 비어있으면(empty/whitespace) 위반으로 간주한다.
    - "RED 증거" 헤더가 없으면 보수적 판정(위반 아님 — RED 게이트 미적용 표).
    근거: PLAN 016 §3.2.2 — RED 단계 실패 출력 증거 선확보. 헌법 §4.
    """
    violations = []
    red_idx = None
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:]+\|", stripped):  # 구분선 행 스킵
            continue
        cells = [c.strip() for c in stripped.split("|")]
        cells = cells[1:-1] if len(cells) > 2 else cells
        if red_idx is None:
            # 헤더 행 탐지: "RED 증거" 셀 포함
            if any(c == "RED 증거" for c in cells):
                red_idx = next(i for i, c in enumerate(cells) if c == "RED 증거")
            continue
        # 데이터 행: RED 증거 셀이 비어있으면 위반
        if red_idx < len(cells) and cells[red_idx] == "":
            violations.append(lineno)
    return violations


def _match_test_files(changed_files, test_globs):
    """changed_files 중 test_globs(fnmatch) 패턴에 매칭되는 파일 목록 반환 (016 테스트 불변성).

    러너/언어/경로 하드코딩 금지 — 패턴은 호출자가 주입(--test-globs, C-2).
    표준 라이브러리 fnmatch만 사용 (T-11).
    """
    matched = []
    for f in (changed_files or []):
        for pat in (test_globs or []):
            if fnmatch.fnmatch(f, pat):
                matched.append(f)
                break
    return matched


# ── 명확화 게이트 헬퍼 (005) ─────────────────────────────────────────────────

# 명확화 4요소 — 행 라벨(첫 셀)에서 키워드로 식별. 순서/표기 변형 흡수.
_CLARIFICATION_ELEMENTS = ["목표", "범위", "제약", "완료기준"]

# "N/A: <사유>" 또는 "NA: <사유>" 는 PASS로 간주 (명시적 해당없음).
_NA_PATTERN = re.compile(r"^N/?A\s*[:：]", re.IGNORECASE)
# 공란 / "TBD"(대소문자 무관) / "-" 단독 → FAIL (미확정으로 간주).
_TBD_PATTERN = re.compile(r"^\s*(TBD|-)?\s*$", re.IGNORECASE)


def _run_clarification_hook(task_path, state, row_index, command, auto_pass=False, force=False):
    """TASK→다음 단계 첫 행 진입 시 명확화 게이트 자동 훅 (005).

    발동 조건:
    - state에 TASK 단계가 존재해야 함 (TASK 행이 없는 파이프라인은 skip).
    - 대상 행이 TASK 단계가 아니어야 함.
    - 대상 행이 자기 stage의 첫 번째 행이어야 함 (is_first_of_stage).
    - 직전 행의 stage == TASK 이어야 함 (= TASK 단계 바로 다음 첫 행).

    정책 A(graceful skip): TASK.md/섹션 부재 시 pass (하위호환).
    --auto-pass 우회 불가 (close_gate 동형, §2.16 G-13 정합).
    --force 시 우회 허용 (긴급 탈출구, --note 필수는 호출자가 이미 보장).
    """
    rows = state["rows"]
    row = rows[row_index]

    # TASK 단계가 파이프라인에 존재하지 않으면 skip
    task_stage_exists = any(r["stage"] == "TASK" for r in rows)
    if not task_stage_exists:
        return

    # 대상 행이 TASK 단계면 skip (TASK 내부 전환은 게이트 대상 아님)
    if row["stage"] == "TASK":
        return

    # 대상 행이 자기 stage의 첫 행인지 확인
    is_first_of_stage = (row_index == 0 or rows[row_index - 1]["stage"] != row["stage"])
    if not is_first_of_stage:
        return

    # 직전 행이 TASK 단계인지 확인 (= TASK 마지막 행 직후 첫 다음 단계 행)
    prev_is_task = (row_index > 0 and rows[row_index - 1]["stage"] == "TASK")
    if not prev_is_task:
        return

    # --auto-pass 우회 거부 (close_gate 동형)
    if auto_pass:
        err(command, "clarification_gate_unmet",
            missing=["auto-pass cannot bypass clarification gate"])

    # --force 시 우회 허용
    if force:
        return

    # 하위호환: TASK.md 부재 → skip
    task_md = _find_task_md(task_path, None)
    if task_md is None:
        return

    # 명확화 게이트 검사
    missing = _check_clarification_gate(task_md)
    if missing is None:
        return  # 하위호환: "## 명확화 결과" 섹션 부재 → skip

    if missing:
        err(command, "clarification_gate_unmet", missing=missing)


# ─────────────────────────────────────────────────────────────────────────────
# 106 F-004/F-005: code-scan 결과 인용 게이트 (PLAN §3.4.2 (1)~(5))
# ─────────────────────────────────────────────────────────────────────────────

# code-scan.js DEFAULT_CONFIG.extensions(code-scan.js:43) 사본 — 프로젝트
# .opal/code-scan.json이 extensions를 생략했을 때의 폴백이다. code-scan.js:351이
# `user.extensions || DEFAULT_CONFIG.extensions`로 **치환**(병합 아님)하므로 동형으로 둔다.
_CODE_SCAN_DEFAULT_EXTENSIONS = (
    ".py", ".js", ".ts", ".vue", ".jsx", ".tsx", ".svelte",
    ".kt", ".kts", ".java", ".swift",
)

# pm-review-gate.md 항목 14 Pass 조건 토큰 — 판정 기준을 **신설하지 않고** 그 문서의
# 조건(조회 계열 결과 필드 / code-map 계열 결과 필드 / 명령 인용)을 그대로 집행한다.
# 토큰 경계는 `[\w-]` 부재로 잡는다: `depends_on`(Step 의존 필드)이 `depends`로
# 오인되면 전 PLAN이 무조건 통과해 게이트가 무력화된다.
_CODE_SCAN_CITATION_RES = tuple(
    (_tok, re.compile(r"(?<![\w-])" + re.escape(_tok) + r"(?![\w-])"))
    for _tok in (
        "domain", "layer", "depends", "exports",          # 조회 계열 결과 필드
        "write_to", "reason", "coverage", "counts",        # code-map 계열 결과 필드
        "code-scan",                                       # 명령 인용
    )
)

# §4.2 실행 체크리스트 섹션 헤딩 / 각 Step의 '**파일**:' 라인
_PLAN_SECTION_42_RE = re.compile(r"^###\s+4\.2(\s|$)")
_PLAN_TARGET_FILE_RE = re.compile(r"^\s*[-*]\s*\*\*파일\*\*\s*:(.*)$")


def _collect_plan_target_files(plan_md_path):
    """PLAN.md §4.2 각 Step의 '**파일**:' 라인에서 경로 토큰을 수집한다 (PLAN §3.4.2 (1)).

    쉼표·공백으로 분리하고 백틱을 제거한다. 산문 주석 토큰(`(신규)` 등)은 경로가
    아니므로 `_is_safe_artifact_token()`(절대경로·'..' 이탈 차단)을 재사용해 걸러낸다.
    §4.2 섹션 부재·해당 라인 부재 시 [] 반환.
    """
    try:
        lines = pathlib.Path(plan_md_path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    in_section = False
    targets = []
    for line in lines:
        if line.startswith("### "):                     # h3 경계에서만 섹션 판정
            in_section = bool(_PLAN_SECTION_42_RE.match(line))
            continue
        if not in_section:
            continue
        m = _PLAN_TARGET_FILE_RE.match(line)
        if not m:
            continue
        for tok in re.split(r"[,\s]+", m.group(1).replace("`", "")):
            tok = tok.strip()
            if not tok or not os.path.splitext(tok)[1]:  # 확장자 없는 산문 토큰 폐기
                continue
            if not _is_safe_artifact_token(tok):
                continue
            targets.append(tok)
    return targets


def _check_code_scan_citation(plan_md_path):
    """PLAN.md 본문에 code-scan 결과 인용이 있는지 판정한다 (PLAN §3.4.2 (2)).

    판정 기준은 신설하지 않는다 — pm-review-gate.md 항목 14 Pass 조건 토큰 중
    1건 이상이 본문에 존재하면 통과다.
    반환: [] 통과 / ["citation_absent"] 미충족 / None(§4.2 섹션 자체 부재 → 하위호환 skip).
    """
    try:
        body = pathlib.Path(plan_md_path).read_text(encoding="utf-8")
    except OSError:
        return None
    if not any(_PLAN_SECTION_42_RE.match(ln) for ln in body.splitlines()):
        return None                                     # 하위호환: §4.2 섹션 부재
    if any(rx.search(body) for _, rx in _CODE_SCAN_CITATION_RES):
        return []
    return ["citation_absent"]


def _run_code_scan_citation_hook(task_path, state, row_index, command,
                                 auto_pass=False, force=False):
    """EXECUTE 단계 첫 행 진입 시 code-scan 결과 인용 게이트 자동 훅 (PLAN §3.4.2 (3)).

    **게이트 순서 자체가 계약이다.** [MUST] `opal/tools/code-scan/code-map-hook.js:121-124`가
    "이 게이트는 ⑥ code-map 로딩보다 **반드시 위**에 있어야 한다 … 순서 자체가 계약이며,
    게이트 위에서 code-map을 읽어서는 안 된다"로 동형 규율을 못 박고 있다. 아래 순서를
    바꾸면 조용히 이탈해야 할 트리에서 거부·출력이 발생한다:

        ① 발동 조건 → ② force 우회 → ③ 자산 게이트 → ④ 산출물 게이트
        → ⑤ 적용 범위 게이트 → ⑥ auto_pass 거부 → ⑦ 판정

    [MUST] ⑥(auto_pass 거부)은 graceful skip인 ③④⑤ **뒤**에 둔다 — 앞에 두면
    문서 전용 태스크·code-scan 미보급 프로젝트에서 거부가 발생해 R-5 오탐 0건이
    깨진다(H-7). 형제 훅 `_run_clarification_hook`은 auto_pass 거부를 skip보다
    앞에 두므로, 그 배치를 그대로 답습하지 않는다.

    반환: None(발동 안 함/skip/통과) · missing 리스트(force로 우회한 경우 —
    호출자가 의사결정 로그에 기재한다, `check_gate_artifacts` 동형).
    """
    rows = state["rows"]
    row = rows[row_index]

    # ① 발동 조건 — 대상 행이 EXECUTE 단계이고, 자기 stage의 첫 행일 때만 발동
    if row["stage"] != "EXECUTE":
        return
    if row_index > 0 and rows[row_index - 1]["stage"] == "EXECUTE":
        return

    # ② --force 우회 허용 (긴급 탈출구 — --note 필수는 호출자가 이미 보장).
    #    [MUST] force는 **거부(err)만** 무력화하고 조기 반환하지 않는다 — ③④⑤의
    #    graceful skip과 ⑥⑦의 판정을 force에서도 그대로 통과시켜 "실제로 거부될
    #    상태였는지"를 확정한 뒤, 우회 사유를 호출자에게 반환해 의사결정 로그
    #    기재를 강제한다(091 `gate_artifact_force` 동형 — 거부될 상태가 아니면
    #    None을 돌려 무기재). ②의 계약("조용히 이탈해야 할 트리에서 거부·출력
    #    금지")은 ⑥⑦의 err가 force에서 발생하지 않으므로 그대로 보존된다:
    #    `pm-review-gate.md` §표준 검토 항목 14가 단언하는 기재를 도구가 집행한다.

    # ③ 자산 게이트 (F-005) — code-scan 미보급 프로젝트는 조용히 통과(code_scan_unavailable).
    #    code-map 자산(manifest) 존재는 요구하지 않는다: headerSource=inline +
    #    code-map 부재는 정상 상태이며, 이를 조건으로 걸면 inline 프로젝트 전건이
    #    스킵되어 R-4가 무력화된다(PLAN §3.5.2).
    root = find_project_root(task_path)
    if root is None:
        return
    cfg_path = root / ".opal" / "code-scan.json"
    if not cfg_path.is_file():
        return
    try:
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if config.get("headerSource") not in ("inline", "manifest"):
        return

    # ④ 산출물 게이트 — PLAN.md 부재 시 하위호환 skip(plan_md_absent)
    plan_md = pathlib.Path(task_path) / "PLAN.md"
    if not plan_md.is_file():
        return

    # ⑤ 적용 범위 게이트 (F-005) — §4.2 대상 파일에 code-scan 적용 확장자가
    #    0건이면 순수 문서 태스크다(doc_only_task).
    extensions = config.get("extensions") or list(_CODE_SCAN_DEFAULT_EXTENSIONS)
    if not any(os.path.splitext(t)[1] in extensions
               for t in _collect_plan_target_files(plan_md)):
        return

    # ⑥ --auto-pass 우회 거부 (close_gate·clarification_gate 동형) — [MUST] ③④⑤ 뒤
    if auto_pass:
        _missing = ["auto-pass cannot bypass code-scan citation gate"]
        if force:
            return _missing
        err(command, "code_scan_citation_unmet", missing=_missing)

    # ⑦ 판정 — None(§4.2 섹션 부재)·[](통과) 모두 통과, 그 외 거부
    missing = _check_code_scan_citation(plan_md)
    if missing:
        if force:
            return missing                        # 우회 — 호출자가 의사결정 로그에 기재
        err(command, "code_scan_citation_unmet", missing=missing)


def _find_task_md(task_path, task_md_arg):
    """TASK.md 경로 결정. --task-md 우선, 없으면 <task_path>/TASK.md. 부재 시 None."""
    p = pathlib.Path(task_md_arg) if task_md_arg else pathlib.Path(task_path) / "TASK.md"
    return p if p.exists() else None


def _locate_clarification_table(lines):
    """"## 명확화 결과" 섹션의 표를 "위치"만 탐색한다 (H-8 — 표 탐색은 공유,
    셀 해석·판정은 호출자별로 분리).

    반환: (section_lines, header_cells, header_line_idx) 튜플.
    섹션/표 부재 시 None (호출자가 graceful skip 정책 적용).
    """
    # 1) "## 명확화 결과" 헤더 위치 탐색
    section_start = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+명확화\s*결과", line.strip()):
            section_start = i
            break
    if section_start is None:
        return None  # 섹션 부재

    # 2) 다음 ## 헤더 직전까지 섹션 추출
    section_lines = []
    for line in lines[section_start + 1:]:
        if re.match(r"^##\s+", line.strip()):
            break
        section_lines.append(line)

    # 3) 표 헤더 행 탐색 — "|" 로 시작하고 구분선이 아닌 첫 행
    header_cells = None
    header_line_idx = None
    for idx, line in enumerate(section_lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue  # 구분선 행 스킵
        cells = [c.strip() for c in stripped.split("|")]
        cells = cells[1:-1] if len(cells) > 2 else cells
        header_cells = cells
        header_line_idx = idx
        break

    if header_cells is None:
        return None  # 표 부재
    return section_lines, header_cells, header_line_idx


# "## 확정된 설계 방향" 불릿 파서 상수 (100 F-007, PLAN §3.7.2)
_DIRECTION_HEADING_RE = re.compile(r"^##\s+확정된\s*설계\s*방향")
# 최상위 불릿 = 들여쓰기 0칸에서 시작하는 `- ` / `* ` / `+ `
_TOP_LEVEL_BULLET_RE = re.compile(r"^[-*+]\s+")


def _locate_confirmed_direction_items(lines):
    """"## 확정된 설계 방향" 섹션의 **최상위 불릿**을 항목으로 수집한다
    (100 F-007, PLAN §3.7.2).

    `## 명확화 결과`는 표지만 이 섹션은 불릿 리스트다 — 탐색 단위가 다르므로
    `_locate_clarification_table`(표 탐색)을 재사용하지 않는 **형제 함수**로
    둔다(H-8: 표 탐색은 공유, 불릿 탐색은 분리).

    반환: [{"element", "confirmed", "dependency", "source"}] 리스트.
      - 섹션 부재 → None (호출자 graceful skip — 레거시 TASK.md 회귀 없음)
      - 섹션은 있으나 최상위 불릿 0건 → [] (분모 0 나눗셈은 호출자가 회피)

    불릿에는 확정값/의존 사실 열 구분이 없으므로 `confirmed`·`dependency`에
    같은 불릿 본문을 넣는다 — 태그(`[결정]`/`[사실]`) 판정과 인용 추출이 같은
    문자열을 대상으로 수행된다. verdict 판정은 프로젝트 루트(`root`)를 쥔
    호출자(`_check_evidence_gate`) 몫이다.

    [계약] `element`는 불릿 본문 원문을 그대로 담는다 — 인덱스형 불투명 라벨은
    PM이 어떤 항목이 미확정인지 식별할 수 없게 하므로 계약 위반이다.
    중첩(들여쓴) 불릿과 그 이어쓰기 행은 항목으로 수집하지 않는다.
    """
    section_start = None
    for i, line in enumerate(lines):
        if _DIRECTION_HEADING_RE.match(line.strip()):
            section_start = i
            break
    if section_start is None:
        return None  # 섹션 부재

    texts = []
    in_nested = False
    for line in lines[section_start + 1:]:
        stripped = line.strip()
        if re.match(r"^##\s+", stripped):
            break  # 다음 ## 헤더 직전까지
        if not stripped:
            continue
        m = _TOP_LEVEL_BULLET_RE.match(line)
        if m:
            in_nested = False
            texts.append(line[m.end():].strip())
            continue
        if _TOP_LEVEL_BULLET_RE.match(stripped):
            in_nested = True  # 들여쓴 중첩 불릿 — 최상위가 아니므로 비수집
            continue
        if texts and not in_nested and line[:1].isspace():
            texts[-1] = (texts[-1] + " " + stripped).strip()  # 최상위 불릿 이어쓰기

    return [{"element": t, "confirmed": t, "dependency": t,
             "source": "confirmed_direction"} for t in texts]


def _parse_clarification_table(lines):
    """TASK.md "## 명확화 결과" 섹션의 표를 파싱.

    반환: {element_label: confirmed_value_cell_text} 딕셔너리.
    섹션/표 부재 시 None 반환 (호출자가 graceful skip).
    "확정값" 열을 헤더에서 식별; 없으면 라벨 다음(2번째) 셀을 확정값으로 폴백.

    [098] `_locate_clarification_table`(표 탐색)을 호출하는 얇은 래퍼 — 기존
    dict 반환 계약은 그대로 유지한다(H-8, 하위호환 파서 무접촉).
    """
    located = _locate_clarification_table(lines)
    if located is None:
        return None
    section_lines, header_cells, header_line_idx = located

    # "확정값" 열 인덱스 식별. 미발견 시 폴백: 라벨 다음(인덱스 1) 셀
    confirmed_col_idx = None
    for ci, cell in enumerate(header_cells):
        if "확정값" in cell:
            confirmed_col_idx = ci
            break
    if confirmed_col_idx is None and len(header_cells) >= 2:
        confirmed_col_idx = 1
    if confirmed_col_idx is None:
        return None  # 표 부재(열 2개 미만)

    # 데이터 행 파싱 — 첫 셀이 4요소 키워드를 포함하면 {라벨: 확정값셀}
    result = {}
    for line in section_lines[header_line_idx + 1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue
        cells = [c.strip() for c in stripped.split("|")]
        cells = cells[1:-1] if len(cells) > 2 else cells
        if not cells:
            continue
        label = cells[0]
        # 4요소 중 하나와 매칭되는지 확인
        for elem in _CLARIFICATION_ELEMENTS:
            if elem in label:
                confirmed_val = cells[confirmed_col_idx] if confirmed_col_idx < len(cells) else ""
                result[elem] = confirmed_val
                break

    return result


def _check_clarification_gate(task_md_path):
    """4요소 잠금 검증. 반환: missing[] (빈 리스트면 PASS).

    None 반환 = 섹션/표 부재 (호출자가 하위호환 정책 적용 — graceful skip).
    각 요소: 확정값 셀이 공란/"TBD"/"-"이면 미충족. "N/A: <사유>"는 충족.
    """
    lines = task_md_path.read_text(encoding="utf-8").splitlines()
    table = _parse_clarification_table(lines)
    if table is None:
        return None  # 섹션/표 부재 신호

    missing = []
    for elem in _CLARIFICATION_ELEMENTS:
        cell = table.get(elem)
        if cell is None:                        # 요소 행 자체가 표에 없음
            missing.append(elem)
        elif _NA_PATTERN.match(cell.strip()):
            continue                             # N/A: <사유> → PASS
        elif _TBD_PATTERN.match(cell):          # 공란 / TBD / "-" → FAIL
            missing.append(elem)
    return missing


# ─────────────────────────────────────────────────────────────────────────────
# 근거 등급 확정/미확정 판정 (098 F-003, PLAN §3.3.2)
# ─────────────────────────────────────────────────────────────────────────────

# 인용 토큰 추출 — 인라인 코드 스팬(백틱)·마크다운 링크·단축 참조(→ D-N ...) 3종.
# 백틱 스팬에 괄호 주석이 바로 동반되면(예: `path`(`func`)) 앞뒤 백틱 스팬과 그
# 괄호를 통째로 소비해 괄호 내용은 별도 토큰으로 취급하지 않는다.
_CITATION_TOKEN_RE = re.compile(
    r"\[[^\]]*\]\([^)]+\)"      # ③ 마크다운 링크
    r"|\(→[^)]*\)"               # ④ 단축 참조
    r"|`[^`]+`(?:\([^)]*\))?"    # ①·② 인라인 코드 스팬 (+ 선택적 괄호 주석 폐기)
)

# 형식① `경로:N` / `경로:N-M` 판별
_CITATION_LINE_RE = re.compile(r"^(.+):(\d+)(?:-\d+)?$")

# 등급 패턴 기본 세트(1차, PLAN §3.3.2) — E1(실행 관측)·E3(생성 코드)은 경로
# 패턴으로 판별 불가하므로 자동 부여 대상이 아니다(unknown으로 귀결, H-11).
_EVIDENCE_GRADE_PATTERNS = (
    ("E5", (".opal/brain/**", ".opal/code-scan.json", "*code-map*")),
    ("E4", ("docs/**", "*.md")),
    ("E2", ("**/tests/**", "test_*.py", "*.py", "*.ts", "*.tsx", "*.js", "*.sh", "*.json")),
)


def _extract_citations(cell):
    """'의존 사실' 셀에서 인용 토큰 원문 목록을 추출한다.
    백틱 밖 산문·단독 괄호 주석은 경로 후보가 아니다 — 백틱 안 경로 스팬 또는
    마크다운 링크·단축 참조만 취한다. 셀이 비었거나 '-'이면 [] 반환."""
    if not cell or not cell.strip() or cell.strip() == "-":
        return []
    tokens = []
    for m in _CITATION_TOKEN_RE.finditer(cell):
        text = m.group(0)
        if text.startswith("`"):
            tokens.append(re.match(r"`[^`]+`", text).group(0))  # 앞 스팬만(괄호 주석 폐기)
        else:
            tokens.append(text)
    return tokens


def _grade_path_pattern(path):
    """경로 문자열 → 등급('E5'|'E4'|'E2'|'unknown'). 매칭 패턴 없으면 'unknown'."""
    for grade, patterns in _EVIDENCE_GRADE_PATTERNS:
        if any(fnmatch.fnmatch(path, pat) for pat in patterns):
            return grade
    return "unknown"


def _resolve_citation_exists(path, line_no, root=None):
    """프로젝트 루트(`root`) 기준 경로 존재 판정.
    line_no 지정(형식①): 파일 존재 AND line_no <= 파일 총 줄수.
    line_no 미지정(형식②): 경로 존재만(파일/디렉토리 무관), §N 유효성은 미검사.
    절대경로·'..' 이탈 토큰은 `_is_safe_artifact_token` 재사용으로 미존재 처리
    (fail-safe — PLAN §5.4 보안 요구). `root`는 호출자(`_check_evidence_gate`)가
    1회 계산해 전달한다(098 ADD-2 — 배포 경로에서도 등가 판정). `root`가
    None이면(호출자 전달 실패) 기존 fail-safe대로 미존재 처리한다."""
    if not _is_safe_artifact_token(path):
        return False
    if root is None:
        return False
    target = root / path
    if line_no is None:
        return target.exists()
    if not target.is_file():
        return False
    try:
        with target.open("r", encoding="utf-8", errors="replace") as f:
            total_lines = sum(1 for _ in f)
    except OSError:
        return False
    return line_no <= total_lines


def _grade_citation(raw, root=None):
    """인용 토큰 원문 → (grade, exists). PLAN §3.3.2 인용 형식별 파싱 계약 4종.

    ① `경로:N`/`경로:N-M` — 경로 패턴 매핑 등급 + 파일·줄 실존 검사.
    ② `` `경로` §N `` (및 §N 없는 바른 백틱 경로) — 경로 패턴 매핑 등급 + 경로
       존재만(§N 유효성 미검사).
    ③ `[사이트명](URL)` — 네트워크 접근 금지, grade:'unknown' exists:None.
    ④ `(→ D-N §N)` 단축 참조 — 테이블 역참조 미해석, grade:'unknown' exists:None.
    디렉토리 없는 파일명 단독 토큰(경로에 '/' 없음)은 저장소 탐색을 수행하지
    않고 grade:'unknown' exists:None으로 반환한다. `root`는 호출자가 1회
    계산한 프로젝트 루트를 그대로 `_resolve_citation_exists`로 릴레이한다
    (098 ADD-2)."""
    if raw.startswith("[") or raw.startswith("(→"):
        return "unknown", None

    inner = raw[1:-1] if raw.startswith("`") and raw.endswith("`") else raw
    m = _CITATION_LINE_RE.match(inner)
    if m:
        path, line_no = m.group(1), int(m.group(2))
    else:
        path, line_no = inner, None

    if "/" not in path:
        return "unknown", None

    grade = _grade_path_pattern(path)
    exists = _resolve_citation_exists(path, line_no, root)
    return grade, exists


def _has_decision_tag(cell):
    """확정값 셀에 사용자의 `[결정]` 태그가 있는지 확인 — 결정은 근거 판정
    대상이 아니다(PLAN §3.3.2, TASK.md §확정된 설계 방향 (5))."""
    return "[결정]" in (cell or "")


def _has_fact_tag(cell):
    """확정값 셀/불릿 본문에 `[사실]` 태그가 있는지 확인 — 상류에서 이미 대조
    확인된 사실이라는 표식이다(100 F-007, PLAN §3.7.2)."""
    return "[사실]" in (cell or "")


# confirmed로 계수하는 verdict 집합 — `확정`(근거 판정 통과·[결정] 면제)과
# `승계`([사실] 상류 대조 확인 승계) 둘 다 confirmed다(PLAN 100 §3.7.2).
_CONFIRMED_VERDICTS = ("확정", "승계")


def _evaluate_evidence_item(confirmed_cell, dependency_cell, root=None):
    """항목 1건 판정 — 도구 4축(① 인용 존재 ② 인용 유효 ③ 등급 부여 ④ E5 단독
    아님). 반환: (verdict, reasons, citations).

    [결정] 태그가 확정값 셀에 있으면 근거 없이도 확정 유지(축 판정을 건너뛴다).
    ③④ 및 grade:'unknown' 토큰은 "E5 아닌 근거"로 계수해 e5_sole_citation
    오탐을 방지한다. `root`는 호출자가 1회 계산한 프로젝트 루트를
    `_grade_citation`으로 릴레이한다(098 ADD-2).

    100 F-007: `[사실]` 태그가 있는 항목이 유효 인용(E2/E4 + 실존)으로 4축을
    통과하면 verdict는 `확정`이 아니라 `승계`다 — 상류에서 대조 확인된 사실을
    승계했음을 표시하며(재확인 면제), 계수상으로는 `확정`과 동등하다
    (`_CONFIRMED_VERDICTS`). 태그가 없는 기존 명확화 표 항목의 판정 결과는
    그대로 `확정`이다(하위호환)."""
    if _has_decision_tag(confirmed_cell):
        return "확정", [], []

    raws = _extract_citations(dependency_cell)
    if not raws:
        return "미확정", ["citation_missing"], []

    citations = []
    for raw in raws:
        grade, exists = _grade_citation(raw, root)
        citations.append({"raw": raw, "grade": grade, "exists": exists})

    # 인용 중 하나라도 "유효 등급(E2/E4) + 실존"이면 그 인용 하나로 확정된다 —
    # E5는 단독으로 확정시키지 못하고(④), 다른 인용의 존재 실패는 확정 인용이
    # 있으면 전체를 끌어내리지 않는다(S-35 양성 대조군).
    if any(c["grade"] in ("E2", "E4") and c["exists"] is True for c in citations):
        return ("승계" if _has_fact_tag(confirmed_cell) else "확정"), [], citations

    reasons = []
    if any(c["exists"] is False for c in citations):
        reasons.append("citation_path_not_found")

    non_unknown = [c for c in citations if c["grade"] != "unknown"]
    if not non_unknown:
        reasons.append("grade_unknown")

    e5_citations = [c for c in citations if c["grade"] == "E5"]
    non_e5_evidence = [c for c in citations if c["grade"] != "E5"]
    if e5_citations and not non_e5_evidence:
        reasons.append("e5_sole_citation")

    return "미확정", reasons, citations


def _check_evidence_gate(task_md_path):
    """TASK.md '## 명확화 결과' 표를 근거 등급 4축으로 판정한다(PLAN §3.3.2).

    반환: {"items":[{element,verdict,reasons,citations,source}],
    "confirmed_ratio": float, "direction_confirmed_ratio": float|None,
    "unconfirmed": [element,...]}. 섹션/표/'의존 사실' 열 부재 시 None(호출자가
    graceful skip). `unknown` 등급은 confirmed_ratio에서 미확정으로 계상한다
    (분자 제외·분모 포함) — 도구는 차단하지 않는다(exit 0 유지).

    100 F-007(PD-1 분리형): '## 확정된 설계 방향' 최상위 불릿을
    `_locate_confirmed_direction_items`로 함께 수집해 `items[]`에 병합하고,
    각 항목의 출처를 `source`(`clarification` | `confirmed_direction`)로
    구분한다. 두 소스는 **비율 분모를 공유하지 않는다** — 기존
    `confirmed_ratio`의 분모는 '## 명확화 결과' 항목 수로 불변이고(소비자
    계약 보호), 방향 항목 비율은 신규 키 `direction_confirmed_ratio`로 따로
    낸다(섹션 부재·항목 0건이면 None — 분모 0 나눗셈 없음).

    098 ADD-2: 인용 실존 판정용 프로젝트 루트를 여기서 1회 계산해 각 항목으로
    전달한다 — `task_md_path`(실제 태스크 경로) 기준 파생을 우선 시도하고
    (배포본이 `~/.opal/tools/state-tool/`에 있어도 태스크 경로는 항상 실제
    프로젝트 안에 있으므로 정상 판정), 실패 시 기존 `__file__` 기준 파생으로
    폴백한다(테스트 픽스처처럼 태스크 경로가 프로젝트 밖 임시 디렉토리인
    경우의 하위호환)."""
    root = (find_project_root(task_md_path)
            or find_project_root(str(pathlib.Path(__file__).resolve())))
    lines = task_md_path.read_text(encoding="utf-8").splitlines()
    located = _locate_clarification_table(lines)
    if located is None:
        return None
    section_lines, header_cells, header_line_idx = located

    confirmed_col_idx = None
    dependency_col_idx = None
    for ci, cell in enumerate(header_cells):
        if confirmed_col_idx is None and "확정값" in cell:
            confirmed_col_idx = ci
        if dependency_col_idx is None and "의존" in cell:
            dependency_col_idx = ci
    if confirmed_col_idx is None and len(header_cells) >= 2:
        confirmed_col_idx = 1
    if confirmed_col_idx is None or dependency_col_idx is None:
        return None  # 확정값/의존 사실 열 부재 — 레거시 스키마, graceful skip

    items = []
    for line in section_lines[header_line_idx + 1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue
        cells = [c.strip() for c in stripped.split("|")]
        cells = cells[1:-1] if len(cells) > 2 else cells
        if not cells:
            continue
        label = cells[0]
        elem = next((e for e in _CLARIFICATION_ELEMENTS if e in label), None)
        if elem is None:
            continue
        confirmed_cell = cells[confirmed_col_idx] if confirmed_col_idx < len(cells) else ""
        dependency_cell = cells[dependency_col_idx] if dependency_col_idx < len(cells) else ""
        verdict, reasons, citations = _evaluate_evidence_item(confirmed_cell, dependency_cell, root)
        items.append({
            "element": elem, "verdict": verdict, "reasons": reasons, "citations": citations,
            "source": "clarification",
        })

    if not items:
        return None  # 데이터 행 부재 — graceful skip

    # [MUST] PD-1 — 기존 confirmed_ratio의 분모는 여기서 확정되며(명확화 결과
    # 항목 수), 아래 방향 항목 병합의 영향을 받지 않는다. 분모 확대는 이 키를
    # 읽는 소비자를 조용히 깨뜨린다.
    confirmed_count = sum(1 for it in items if it["verdict"] in _CONFIRMED_VERDICTS)
    ratio = confirmed_count / len(items)
    unconfirmed = [it["element"] for it in items
                   if it["verdict"] not in _CONFIRMED_VERDICTS]

    # 100 F-007 — '## 확정된 설계 방향' 불릿 병합(별도 분모)
    direction_ratio = None
    direction_rows = _locate_confirmed_direction_items(lines)
    if direction_rows:  # None(섹션 부재)·[](항목 0건) 모두 graceful skip
        direction_items = []
        for row in direction_rows:
            verdict, reasons, citations = _evaluate_evidence_item(
                row["confirmed"], row["dependency"], root)
            direction_items.append({
                "element": row["element"], "verdict": verdict,
                "reasons": reasons, "citations": citations,
                "source": row["source"],
            })
        direction_confirmed = sum(1 for it in direction_items
                                  if it["verdict"] in _CONFIRMED_VERDICTS)
        direction_ratio = direction_confirmed / len(direction_items)
        unconfirmed += [it["element"] for it in direction_items
                        if it["verdict"] not in _CONFIRMED_VERDICTS]
        items += direction_items

    return {"items": items, "confirmed_ratio": ratio,
            "direction_confirmed_ratio": direction_ratio,
            "unconfirmed": unconfirmed}


def cmd_verify(args):
    """PLAN 013 §verify — TEST-SCENARIO.md mock 코드 패턴 + 증거 누락 검사.
    016 확장: --red-check(RED 증거 게이트) / --fix-mode(테스트 불변성).
    005 확장: --clarification-check(TASK 4요소 잠금 게이트).
    098 확장: --evidence-check(근거 등급 확정/미확정 판정 라우터, 차단 없음).
    106 확장: --code-scan-citation-check(PLAN.md code-scan 결과 인용 게이트, unmet 시 exit 1).
    대상 파일 부재 시 doc-only skip (ok).
    """
    command = "verify"
    task_path = args.task_path
    scenario_arg = getattr(args, "scenario", None)
    red_check = getattr(args, "red_check", False)
    fix_mode = getattr(args, "fix_mode", False)
    changed_files = getattr(args, "changed_files", None) or []
    test_globs = getattr(args, "test_globs", None)
    clarification_check = getattr(args, "clarification_check", False)
    evidence_check = getattr(args, "evidence_check", False)
    code_scan_citation_check = getattr(args, "code_scan_citation_check", False)
    task_md_arg = getattr(args, "task_md", None)

    # 098/106 — 게이트 플래그 동시 지정 거부 (무성 무시 방지, PLAN §3.3.2 / §3.4.2 (5))
    _gate_flags = [_n for _n, _v in (
        ("--clarification-check", clarification_check),
        ("--evidence-check", evidence_check),
        ("--code-scan-citation-check", code_scan_citation_check),
    ) if _v]
    if len(_gate_flags) > 1:
        err(command, "evidence_check_flag_conflict", flags=_gate_flags)

    # 005 — TASK 4요소 잠금 게이트 (fix_mode와 같은 조기 반환 패턴 — 독립 분기)
    if clarification_check:
        task_md_path = _find_task_md(task_path, task_md_arg)
        if task_md_path is None:
            # 정책 A(graceful skip): TASK.md 파일 부재 → skip ok
            print(json.dumps({
                "ok": True, "command": command,
                "clarification_check": "skipped",
                "reason": "TASK.md not found (backward-compat skip)",
            }, ensure_ascii=False))
            sys.exit(0)
        missing = _check_clarification_gate(task_md_path)
        if missing is None:
            # 정책 A(graceful skip): 섹션/표 부재 → skip ok
            print(json.dumps({
                "ok": True, "command": command,
                "clarification_check": "skipped",
                "reason": "no '## 명확화 결과' section (backward-compat skip)",
            }, ensure_ascii=False))
            sys.exit(0)
        if missing:
            err(command, "clarification_gate_unmet", missing=missing)
        print(json.dumps({
            "ok": True, "command": command,
            "clarification_check": "pass",
        }, ensure_ascii=False))
        sys.exit(0)

    # 098 — 근거 등급 확정/미확정 판정 라우터 (clarification_check 뒤·fix_mode 앞,
    # 기존 조기 반환 순서 불변)
    if evidence_check:
        task_md_path = _find_task_md(task_path, task_md_arg)
        if task_md_path is None:
            # 정책 A(graceful skip): TASK.md 파일 부재 → skip ok
            print(json.dumps({
                "ok": True, "command": command,
                "evidence_check": "skipped",
                "reason": "TASK.md not found (backward-compat skip)",
            }, ensure_ascii=False))
            sys.exit(0)
        gate = _check_evidence_gate(task_md_path)
        if gate is None:
            # 정책 A(graceful skip): 섹션/표/'의존 사실' 열 부재 → skip ok
            print(json.dumps({
                "ok": True, "command": command,
                "evidence_check": "skipped",
                "reason": "no '## 명확화 결과' section or '의존 사실' column (backward-compat skip)",
            }, ensure_ascii=False))
            sys.exit(0)
        status = "pass" if gate["confirmed_ratio"] >= 1.0 else "routed"
        print(json.dumps({
            "ok": True, "command": command,
            "evidence_check": status,
            "items": gate["items"],
            "confirmed_ratio": gate["confirmed_ratio"],
            "direction_confirmed_ratio": gate["direction_confirmed_ratio"],
            "unconfirmed": gate["unconfirmed"],
        }, ensure_ascii=False))
        sys.exit(0)

    # 106 — code-scan 결과 인용 판정 라우터 (evidence_check 뒤·fix_mode 앞,
    #   기존 조기 반환 순서 불변). [MUST] 게이트 순서는 _run_code_scan_citation_hook의
    #   ③④⑤⑦와 동일하다 — 같은 입력에 두 집행 지점(verify / advance·mark)이 다른
    #   판정을 내면 게이트가 신뢰를 잃는다. reason은 훅과 동일 3값으로 닫는다.
    if code_scan_citation_check:
        plan_md = pathlib.Path(task_path) / "PLAN.md"
        reason = None
        root = find_project_root(task_path)
        config = None
        cfg_path = (root / ".opal" / "code-scan.json") if root is not None else None
        if cfg_path is not None and cfg_path.is_file():
            try:
                config = json.loads(cfg_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                config = None
        if (not isinstance(config, dict)
                or config.get("headerSource") not in ("inline", "manifest")):
            reason = "code_scan_unavailable"        # ③ 자산 게이트 (F-005)
        elif not plan_md.is_file():
            reason = "plan_md_absent"               # ④ 산출물 게이트 (하위호환)
        targets = _collect_plan_target_files(plan_md) if reason is None else []
        if reason is None:
            extensions = config.get("extensions") or list(_CODE_SCAN_DEFAULT_EXTENSIONS)
            if not any(os.path.splitext(t)[1] in extensions for t in targets):
                reason = "doc_only_task"            # ⑤ 적용 범위 게이트 (F-005)
        if reason is not None:
            print(json.dumps({
                "ok": True, "command": command,
                "code_scan_citation_check": "skipped",
                "reason": reason,
                "target_files": targets,
                "matched_tokens": [],
            }, ensure_ascii=False))
            sys.exit(0)
        # ⑦ 판정 — None(§4.2 섹션 부재)·[](통과) 모두 통과
        body = plan_md.read_text(encoding="utf-8")
        matched = [tok for tok, rx in _CODE_SCAN_CITATION_RES if rx.search(body)]
        missing = _check_code_scan_citation(plan_md)
        if missing:
            err(command, "code_scan_citation_unmet",
                code_scan_citation_check="unmet", missing=missing,
                target_files=targets, matched_tokens=matched)
        print(json.dumps({
            "ok": True, "command": command,
            "code_scan_citation_check": "pass",
            "reason": None,
            "target_files": targets,
            "matched_tokens": matched,
        }, ensure_ascii=False))
        sys.exit(0)

    # 016 — fix 루핑 테스트 불변성 검사 (산출물 무관, 명시 입력 기반 deterministic)
    if fix_mode:
        if not test_globs:
            # deterministic 입력(test-globs) 없음 → 검사 skip (오탐 방지)
            print(json.dumps({
                "ok": True, "command": command,
                "immutability_check": "skipped (no test-globs)",
            }, ensure_ascii=False))
            sys.exit(0)
        matched = _match_test_files(changed_files, test_globs)
        if matched:
            err(command, "test_modified_in_fix", files=matched)
        print(json.dumps({
            "ok": True, "command": command,
            "immutability_check": "pass", "matched_test_files": [],
        }, ensure_ascii=False))
        sys.exit(0)

    scenario_path = _find_scenario_file(task_path, scenario_arg)
    if scenario_path is None:
        # doc-only / 인프라 부재: TEST-SCENARIO.md 없음 → skip ok (graceful skip)
        print(json.dumps({
            "ok": True, "command": command,
            "skipped": True, "reason": "TEST-SCENARIO.md not found (doc-only skip)"
        }, ensure_ascii=False))
        sys.exit(0)

    lines = scenario_path.read_text(encoding="utf-8").splitlines()

    # 검사 1 — mock 코드 패턴
    mock_lines = _check_mock_patterns(lines)
    if mock_lines:
        err(command, "mock_in_scenario", lines=mock_lines)

    # 검사 2 — 증거 누락
    missing_lines = _check_evidence(lines)
    if missing_lines:
        err(command, "evidence_missing", lines=missing_lines)

    # 검사 3 (016) — RED 증거 게이트 (--red-check 시에만; 미지정 시 하위 호환)
    checks = {"mock_in_scenario": "pass", "evidence_missing": "pass"}
    if red_check:
        red_lines = _check_red_evidence(lines)
        if red_lines:
            err(command, "red_evidence_missing",
                detail="빈 RED 증거 행: {}".format(red_lines))
        checks["red_evidence_missing"] = "pass"

    print(json.dumps({
        "ok": True, "command": command,
        "scenario": str(scenario_path),
        "checks": checks,
    }, ensure_ascii=False))
    sys.exit(0)


# ─────────────────────────────────────────────────────────────────────────────
# argparse 설정 (PLAN §2.19 E-2 매트릭스 그대로)
# ─────────────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="state-tool",
        description="OPAL 파이프라인 현황판 JSON SSOT 관리 CLI (PLAN §2.19 E-2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
서브 명령 (10종):
  init          state.json + STATE.md 생성
  show          현황판 출력 (md/json/full)
  advance       ⬜→🔄 전환
  mark          ⬜/🔄→✅ 전환 (--done 필수)
  block         any→❌ 전환 + current_status=blocked
  validate      정합성 검증 → violations[]
  add-row       추가작업 행 삽입
  status        current_status 명시 전환
  spec-validate pipeline.json 스펙 검증 (070 R-6)
  gate-pass     [DEPRECATED] Gate 4행 일괄 ✅ 처리 (레거시 state.json 전용)

행 주소(070): --task-step <key> / --task-step-id <n> / --row <n>[deprecated] 중 하나만 지정.
호출 형식: ~/.opal/tools/state-tool/run.sh <command> <task-path> [options]
종료 코드: 0=ok  1=violation/scope_error  2=internal_error
"""
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── init ──
    p_init = sub.add_parser("init", help="state.json + STATE.md 생성 (§2.11 G-8)")
    p_init.add_argument("task_path", metavar="<task-path>")
    p_init.add_argument("--skill", required=True,
                        choices=["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd","oppl","opdd"])
    p_init.add_argument("--mode", required=True,
                        choices=["interactive","semi-agentic","agentic"])
    p_init.add_argument("--task-title")
    p_init.add_argument("--next-action")
    rows_group = p_init.add_mutually_exclusive_group()  # C-1
    rows_group.add_argument("--rows-spec", metavar="<inline-json>")
    rows_group.add_argument("--rows-from", metavar="<path>",
                        help="SKILL.md(레거시, deprecated 경고) 또는 pipeline.json(070 신규, 확장자로 분기)")
    p_init.add_argument("--rows-acts", metavar="<inline-json>",
                        help="opsdd ACT 동적 주입 (시그니처만, 미구현 — R-13)")
    p_init.add_argument("--force", action="store_true")
    p_init.add_argument("--note")
    # 094 D-2: 저널화로 파싱 대상(파이프라인 표)이 소멸 — cmd_init이 즉시 거부.
    # 인자 정의는 하위 호환을 위해 유지하되 help는 감춘다(§3.2.2 (2)).
    p_init.add_argument("--import-existing", action="store_true", dest="import_existing",
                        help=argparse.SUPPRESS)
    p_init.add_argument("--worktree", metavar="<path>",
                        help="worktree 코드 작업본 절대경로 (092). 미지정 시 state.json에 키를 생성하지 않는다.")
    p_init.set_defaults(func=cmd_init)

    # ── show ──
    p_show = sub.add_parser("show", help="현황판 출력 (§2.14 G-11)")
    p_show.add_argument("task_path", metavar="<task-path>")
    p_show.add_argument("--format", dest="format", choices=["md","json","full"], default="md")
    p_show.set_defaults(func=cmd_show)

    # ── advance ──
    p_adv = sub.add_parser("advance", help="⬜→🔄 전환 (T-7)")
    p_adv.add_argument("task_path", metavar="<task-path>")
    p_adv.add_argument("--task-step", dest="task_step", metavar="<key>",
                       help="070: task-step key 주소 (예: plan.pm_gate)")
    p_adv.add_argument("--task-step-id", dest="task_step_id", type=int, metavar="<n>",
                       help="070: task-step 숫자 주소(신규, row_id와 동일 의미)")
    p_adv.add_argument("--row", type=int, metavar="<n>",
                       help="[deprecated] --task-step / --task-step-id 사용 권장")
    p_adv.add_argument("--note")
    p_adv.add_argument("--next-action",
                       help="072: '다음 액션' per-transition 오버라이드(비지속, M-3) — "
                            "미지정 시 프론티어에서 자동 파생")
    p_adv.set_defaults(func=cmd_advance)

    # ── mark ──
    p_mark = sub.add_parser("mark", help="⬜/🔄→✅ 전환 (T-7, §2.4, §2.15)")
    p_mark.add_argument("task_path", metavar="<task-path>")
    p_mark.add_argument("--task-step", dest="task_step", metavar="<key>",
                       help="070: task-step key 주소 (예: plan.pm_gate)")
    p_mark.add_argument("--task-step-id", dest="task_step_id", type=int, metavar="<n>",
                       help="070: task-step 숫자 주소(신규, row_id와 동일 의미)")
    p_mark.add_argument("--row", type=int, metavar="<n>",
                       help="[deprecated] --task-step / --task-step-id 사용 권장")
    p_mark.add_argument("--done", action="store_true", required=True)
    p_mark.add_argument("--note")
    p_mark.add_argument("--as-worker", action="store_true", dest="as_worker")
    p_mark.add_argument("--worker-stage",
                        choices=STAGE_ENUM,
                        dest="worker_stage")
    # 070 R-5: --action-step은 --step의 신규 별칭 — dest 공유로 _parse_step/row["step"] 로직 무변경
    p_mark.add_argument("--step", dest="step", metavar="N/M")
    p_mark.add_argument("--action-step", dest="step", metavar="N/M",
                        help="EXECUTE 액션 진행률 (구 --step 별칭, 070 R-5)")
    # 103 R-21: 소요 '값'과 소요 '미상 선언'은 동시에 성립할 수 없으므로 배타 그룹으로
    #   묶는다. 둘 다 주면 argparse가 exit 2로 거부한다 — `--owner`/`--auto-pass`와
    #   동일 계열의 CLI 인자 형식 오류이므로 ERROR_CODES를 신설하지 않는다(45종 불변).
    duration_group = p_mark.add_mutually_exclusive_group()
    duration_group.add_argument("--worker-duration-minutes", dest="worker_duration_minutes",
                        type=_worker_duration_minutes, metavar="<minutes>",
                        help="103 R-15: 이 행에서 워커가 실제 실행한 시간(분, 0 이상 정수). "
                             "원천은 하네스 duration_ms — 분으로 환산해 전달한다. "
                             "지정 시에만 rows[].worker_duration_minutes에 기록되며, "
                             "미지정 시 필드를 만들지 않는다(기존 태스크 무영향)")
    duration_group.add_argument("--worker-duration-unknown", action="store_true",
                        dest="worker_duration_unknown",
                        help="103 R-21: 이 행의 워커 소요를 알 수 없음을 명시한다"
                             "(중단된 워커·PM 직접 수행·소급 불가 과거 데이터). "
                             "worker_duration_missing 경고를 억제하며, 행에 필드를 "
                             "만들지 않는다 — 기록 결과는 인자 미지정과 완전히 동일하다")
    owner_group = p_mark.add_mutually_exclusive_group()  # C-2
    owner_group.add_argument("--owner", choices=["PM","worker","user","auto"])
    owner_group.add_argument("--auto-pass", action="store_true", dest="auto_pass")
    p_mark.add_argument("--force", action="store_true")
    p_mark.add_argument("--next-action",
                        help="072: '다음 액션' per-transition 오버라이드(비지속, M-3) — "
                             "미지정 시 프론티어에서 자동 파생")
    p_mark.set_defaults(func=cmd_mark)

    # ── block ──
    p_blk = sub.add_parser("block", help="any→❌ 전환 + current_status=blocked (§2.17 트리거 #7)")
    p_blk.add_argument("task_path", metavar="<task-path>")
    p_blk.add_argument("--task-step", dest="task_step", metavar="<key>",
                       help="070: task-step key 주소 (예: plan.pm_gate)")
    p_blk.add_argument("--task-step-id", dest="task_step_id", type=int, metavar="<n>",
                       help="070: task-step 숫자 주소(신규, row_id와 동일 의미)")
    p_blk.add_argument("--row", type=int, metavar="<n>",
                       help="[deprecated] --task-step / --task-step-id 사용 권장")
    p_blk.add_argument("--reason", required=True)
    p_blk.set_defaults(func=cmd_block)

    # ── validate ──
    p_val = sub.add_parser("validate", help="정합성 검증 → violations[] (§2.6, F-10)")
    p_val.add_argument("task_path", metavar="<task-path>")
    p_val.set_defaults(func=cmd_validate)

    # ── add-row ──
    p_add = sub.add_parser("add-row", help="추가작업 행 삽입 (§2.12 G-9)")
    p_add.add_argument("task_path", metavar="<task-path>")
    p_add.add_argument("--after-task-step", dest="after_task_step", metavar="<key>",
                       help="070: 앵커 행 key 주소")
    p_add.add_argument("--after-task-step-id", dest="after_task_step_id", type=int, metavar="<n>",
                       help="070: 앵커 행 숫자 주소(신규, row_id와 동일 의미)")
    p_add.add_argument("--after", type=int, metavar="<n>",
                       help="[deprecated] --after-task-step / --after-task-step-id 사용 권장")
    p_add.add_argument("--stage", required=True, choices=STAGE_ENUM)
    p_add.add_argument("--item", required=True)
    p_add.add_argument("--key", metavar="<key>",
                       help="070 R-9: 신규 행 key 명시 지정 (미지정 시 자동 생성)")
    p_add.add_argument("--note")
    p_add.set_defaults(func=cmd_add_row)

    # ── status ──
    p_sts = sub.add_parser("status", help="current_status 명시 전환 (§2.11 G-7)")
    p_sts.add_argument("task_path", metavar="<task-path>")
    p_sts.add_argument("--set", dest="set", required=True,
                       choices=["in_progress","done","blocked",
                                "additional_work","additional_work_done"])
    p_sts.add_argument("--note")
    p_sts.set_defaults(func=cmd_status)

    # ── gate-pass ──
    p_gp = sub.add_parser("gate-pass",
                          help="[DEPRECATED] Gate 4행 일괄 ✅ 처리 — 레거시 state.json 전용 (§2.13 G-10, 014 Phase 4)")
    p_gp.add_argument("task_path", metavar="<task-path>")
    p_gp.add_argument("--start", type=int, required=True)
    p_gp.add_argument("--note")
    p_gp.set_defaults(func=cmd_gate_pass)

    # ── spec-validate (070 R-6) ──
    p_spec = sub.add_parser("spec-validate", help="pipeline.json 스펙 검증 (070 R-6, DEC-2)")
    p_spec.add_argument("spec_path", metavar="<pipeline.json>")
    p_spec.set_defaults(func=cmd_spec_validate)

    # ── verify ──
    p_vfy = sub.add_parser(
        "verify",
        help="TEST-SCENARIO.md mock 코드 패턴 + 증거 누락 검사 (PLAN 013, 헌법 §4)"
    )
    p_vfy.add_argument("task_path", metavar="<task-path>")
    p_vfy.add_argument("--scenario", metavar="<path>",
                       help="TEST-SCENARIO.md 경로 명시 (기본: <task-path>/TEST-SCENARIO.md)")
    # 016 RED-first 게이트
    p_vfy.add_argument("--red-check", action="store_true", dest="red_check",
                       help="RED 증거(실패 출력) 게이트 — 누락 시 red_evidence_missing")
    p_vfy.add_argument("--changed-files", nargs="*", default=[], dest="changed_files",
                       help="fix 루핑 변경 파일 목록 (테스트 불변성 입력)")
    p_vfy.add_argument("--test-globs", nargs="*", default=None, dest="test_globs",
                       help="테스트 파일 식별 glob 패턴 (프로젝트 탐지값 주입 — 하드코딩 금지)")
    p_vfy.add_argument("--fix-mode", action="store_true", dest="fix_mode",
                       help="fix 루핑 컨텍스트 — 테스트 파일 수정 시 test_modified_in_fix")
    # 005 명확화 게이트
    p_vfy.add_argument("--clarification-check", action="store_true", dest="clarification_check",
                       help="TASK 4요소 잠금 게이트 — 미충족 시 clarification_gate_unmet (PRINCIPLES §1 집행)")
    p_vfy.add_argument("--task-md", metavar="<path>", dest="task_md",
                       help="TASK.md 경로 명시 (기본: <task-path>/TASK.md)")
    # 098 근거 등급 확정/미확정 판정 게이트
    p_vfy.add_argument("--evidence-check", action="store_true", dest="evidence_check",
                       help="근거 등급 확정/미확정 판정 라우터 — 항목별 판정+사유를 "
                            "반환하되 차단하지 않음(exit 0 유지, PLAN §3.3.2)")
    # 106 code-scan 결과 인용 게이트
    p_vfy.add_argument("--code-scan-citation-check", action="store_true",
                       dest="code_scan_citation_check",
                       help="PLAN.md code-scan 결과 인용 게이트 — 미충족 시 "
                            "code_scan_citation_unmet(exit 1). 자산·산출물·적용 범위 "
                            "3조건 미해당 시 skipped(exit 0, PLAN §3.4.2)")
    p_vfy.set_defaults(func=cmd_verify)

    return parser

# ─────────────────────────────────────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args   = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
