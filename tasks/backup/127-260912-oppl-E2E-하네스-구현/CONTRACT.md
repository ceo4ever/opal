# CONTRACT: OPAL 범용 E2E 하네스

> 대상 태스크: `tasks/127-260912-oppl-E2E-하네스-구현/TASK.md`
> 입력: `tasks/127-260912-oppl-E2E-하네스-구현/PRD.md`(R-1~R-19, NR-1~NR-7), `tasks/127-260912-oppl-E2E-하네스-구현/TRD.md`(TD-1~TD-19)
> 구조 근거: `~/.opal/skills/opal-pilot-project-loop/references/contract.md` §2 — 계약 본문 3파트(스키마·시그니처·경계) + 기계검증절 + 루브릭절
> 기계가독 표면 인벤토리: 같은 폴더의 `surfaces.json` (§D.1)

---

## 0. 개요와 적용 범위

### 0.1 이 문서가 확정하는 것

TRD가 "무엇을 어디에 만들지"까지 정했고(`TRD.md` §범위 경계: "함수 시그니처·JSON 필드의 확정 스키마는 D4 `CONTRACT.md`가 소유한다"), 이 문서는 그 경계에서 **오가는 값의 형태**를 확정한다.

| 파트 | 내용 | 위치 |
|---|---|---|
| 스키마 | E2E 하네스가 읽고 쓰는 모든 JSON 산출물의 필드·타입·필수/선택·enum·기본값 | §A |
| 시그니처 | CLI 서브명령·driver 연산·executor 연산의 호출 형태와 반환·exit | §B |
| 경계 | 모듈 간 소유권 분리선, 인증 표면 부재, origin 선언 | §C |
| 기계검증절 | 코드로 결정론 검증 가능한 항목 + `surfaces.json` | §D |
| 루브릭절 | Evaluator가 판정하는 주관적 품질 기준(앵커 척도) | §E |

### 0.2 적용 범위 밖

- 태스크 125가 소유한 profile·상태·exit code 계약의 **재정의**(§1). 본 계약은 참조·소비만 한다.
- `test-scenario.json` 스키마 변경. `TRD.md` TD-12 결정 1에 따라 v2 필드를 그대로 쓴다.
- `opal/tools/test-tool/lib/scenario.py`·`e2e_contract.py`의 기능 변경(`TRD.md` §8 "변경 0").
- Playwright 제거 작업(TD-19)의 문서·설치 변경. 계약 표면을 만들지 않는 정리 작업이다.

### 0.3 값 표기 규약

- `필수`: 해당 산출물이 존재하면 반드시 있는 필드. 누락은 계약 위반이다.
- `선택`: 조건부. 조건을 함께 적는다.
- `실측 의존(Q-N)`: **필드의 존재와 타입은 이 문서가 확정하고, 값의 범위만 실측에서 확정**되는 항목(`TRD.md` §9 Q-2·Q-3·Q-6·Q-7). 구현은 필드를 반드시 만든다.
- 시간 표기는 전부 ISO-8601 UTC 문자열(`2026-09-12T05:00:00Z`)이다.
- 경로 표기는 전부 절대경로 문자열이다.

---

## 1. 전제 계약 — 태스크 125 소유분 (참조만, 재정의 금지)

[MUST] `tasks/127-260912-oppl-E2E-하네스-구현/TASK.md` C-1: "태스크 125가 확정한 profile·final status 5종·`awaiting_human`·exit code(0/6/7/18/19/20) 계약을 재정의하지 않고 소비한다."

아래 값은 전부 `opal/tools/test-tool/lib/e2e_contract.py`가 **소유**하며, 본 계약은 그 모듈을 import해 참조한다. 이 표는 소유권 소재를 밝히기 위한 것이지 재선언이 아니다.

| 계약 요소 | 소유 지점 | 소비 방식 |
|---|---|---|
| 스키마 버전 `"2.0"` | `e2e_contract.py:37` `E2E_CONTRACT_SCHEMA_VERSION` | 산출물 `schema_version` 필드에 그대로 기록 |
| profile 5종 | `e2e_contract.py:38` `PROFILES` | `run.json.profile` enum의 원천 |
| 최종 상태 5종 | `e2e_contract.py:39` `FINAL_STATUSES` | `run.json.status` enum의 원천 |
| 운영 상태 `awaiting_human` | `e2e_contract.py:40` `OPERATIONAL_STATUSES` | `run.json.operational_status` enum의 원천 |
| executor 3종 | `e2e_contract.py:41` `EXECUTOR_TYPES` | `actions.jsonl.executor` enum의 원천 |
| 상태→exit | `e2e_contract.py:42-49` `STATUS_EXIT_CODES` | `status_to_exit()`(`:125`) 호출로만 취득 |
| 상태→error code | `e2e_contract.py:50-56` `STATUS_ERROR_CODES` | `status_to_error()`(`:129`) 호출로만 취득 |
| profile→executor 행렬 | `e2e_contract.py:57-66` `EXECUTOR_MATRIX` | `executor_contract()`(`:133`) 호출 |
| handoff 필수 8필드 | `e2e_contract.py:67-76` `HANDOFF_REQUIRED_FIELDS` | §A.9 handoff 스키마의 필수 집합 |
| profile 해석 | `e2e_contract.py:137` `resolve_profile` | `surfaces.json` 조회 결과를 입력으로 호출 |
| 다음 후보 전환 판정 | `e2e_contract.py:269` `can_try_next_provider` | 전환 여부의 **유일한** 판단 지점 |
| pass 게이트 | `e2e_contract.py:292` `validate_pass_requirements` | 최종 판정의 **유일한** 관문 |
| verdict 조립 | `e2e_contract.py:375` `build_verdict` | 하네스가 verdict를 직접 조립하지 않음 |
| 시나리오 v2 검증 | `e2e_contract.py:418` `_validate_v2_scenario`, `:504` `validate_scenario_contract` | `e2e run` 진입 시 호출 |
| resume 검증 | `opal/tools/test-tool/lib/scenario.py:482-528` | `e2e resume`이 재사용(TD-18) |

**계약 규칙 C-125-1**: 신규 모듈은 상태 문자열·exit 정수·error code 문자열을 **리터럴로 작성하지 않는다.** 반드시 위 함수·상수의 반환값을 사용한다(`TRD.md` RK-8 완화).

**계약 규칙 C-125-2**: `e2e run`은 `schema_version != "2.0"`인 시나리오를 실행 대상으로 받지 않는다. v1 spec은 `validate_scenario_contract(legacy_defaults=True)`(`e2e_contract.py:504-548`) 경로로 **읽기만** 가능하다(`TRD.md` TD-12 결정 4).

---

## §A 스키마

산출물 배치는 `TRD.md` §7을 따른다. 루트는 `${OPAL_E2E_ARTIFACT_ROOT:-${TMPDIR}/opal-e2e-runs}`이고, run 단위 디렉터리는 `{artifact_root}/{project_id}/{run_id}/` = `$OPAL_E2E_ARTIFACT_DIR`이다(`TRD.md` TD-10).

### A.0 공통 식별자 형식

| 식별자 | 형식 | 비고 |
|---|---|---|
| `run_id` | `e2e-{YYYYMMDD}-{NNN}` (`^e2e-\d{8}-\d{3}$`) | `docs/proposals/opal-e2e-harness.md` §10.1 예시(`e2e-20260912-001`)를 형식으로 승격 |
| `project_id` | 경로 안전 slug (`^[A-Za-z0-9._-]+$`) | 저장소 basename 기반. 경로 구분자 금지 |
| `scenario_id` | `test-scenario.json`의 `id` 원문 | 하네스가 변형하지 않음 |
| `resume_token` | opaque run-scoped 문자열(길이 ≥ 32) | 제안서 §7.5 `opaque-run-scoped-token` |
| `handoff_id` | `^H-\d{3,}$` | 제안서 §7.5 예시 `H-001` |

### A.1 `run.json` — 실행 증명 (공통 필수)

경로: `$OPAL_E2E_ARTIFACT_DIR/run.json`. 근거: `docs/proposals/opal-e2e-harness.md` §10.1 최소 필드 + `PRD.md` R-5 기록 항목 + `TRD.md` TD-4 기록 항목.

| 필드 | 타입 | 필수/선택 | enum·기본값 | 근거 |
|---|---|---|---|---|
| `schema_version` | string | 필수 | `"2.0"` 고정 | `e2e_contract.py:37` |
| `run_id` | string | 필수 | A.0 형식 | 제안서 §10.1 |
| `scenario_id` | string | 필수 | — | 제안서 §10.1 |
| `profile` | string | 필수 | `PROFILES` 5종 | `e2e_contract.py:38` |
| `actors` | string[] | 필수 | 원소는 `EXECUTOR_TYPES` | `e2e_contract.py:41` |
| `surface_kind` | string | 필수 | 시나리오 `surface_kind` 원문 | `e2e_contract.py:297` 소비 |
| `target` | string | 필수 | `source-main` \| `source-worktree` \| `installed` | `TRD.md` TD-4 |
| `project_root` | string(path) | 필수 | — | R-5 |
| `worktree_root` | string(path) \| null | 필수(값은 nullable) | `target != source-worktree`면 `null` | `TRD.md` TD-4 |
| `opal_home` | string(path) \| null | 필수(값은 nullable) | `target == installed`일 때만 비-null | `TRD.md` TD-9 |
| `commit` | string | 필수 | `git rev-parse HEAD` 결과 40자 | `TRD.md` TD-4(읽기 전용 git) |
| `dirty` | boolean | 필수 | `git status --porcelain` 비어있지 않으면 `true` | R-5 |
| `dirty_files` | string[] | 필수 | `dirty=false`면 `[]` | R-5 "미커밋 변경 여부" |
| `urls` | object | 필수 | `{frontend: string\|null, backend: string}` | 제안서 §10.1 |
| `executors` | object[] | 필수 | A.1.1 | 제안서 §10.1 |
| `candidates` | object[] | 필수 | A.1.2. 제외·실패 후보 포함 전건 | T07·T08 완료 기준, MV-38 |
| `state` | string | 필수 | A.2.1 상태 enum의 **최종 도달 상태** | `TRD.md` §5.2 |
| `status` | string \| null | 필수(값은 nullable) | `FINAL_STATUSES` 5종. `awaiting_human` 중이면 `null` | `e2e_contract.py:39` |
| `operational_status` | string \| null | 필수(값은 nullable) | `"awaiting_human"` 또는 `null` | `e2e_contract.py:40` |
| `error` | string \| null | 필수(값은 nullable) | `status_to_error()` 반환값 | `e2e_contract.py:129` |
| `exit_code` | integer | 필수 | `status_to_exit()` 반환값 | `e2e_contract.py:125` |
| `assertion_summary` | object | 필수 | `{passed: int, failed: int, missing: int}` | 제안서 §10.1 |
| `required_evidence` | string[] | 필수 | 시나리오 원문 | `e2e_contract.py:357` 대조 대상 |
| `observed_evidence` | string[] | 필수 | 실제 수집된 증적 키 | `e2e_contract.py:358` |
| `missing_evidence` | string[] | 필수 | 누락 항목. 없으면 `[]` | R-14 "무엇이 빠졌는지 명시" |
| `evidence_complete` | boolean | 필수 | `missing_evidence == []` | 제안서 §10.1 |
| `fidelity` | string | 필수 | `mock` \| `real-http` \| `real-usage` | `scenario.py:119` `FIDELITY_ORDER` 소유 |
| `cleanup` | string | 필수 | `complete` \| `warning` \| `failed` | `TRD.md` §5.2 |
| `artifact_dir` | string(path) | 필수 | — | `TRD.md` TD-4 |
| `started_at` / `ended_at` | string(ISO-8601) | 필수 / 선택 | `ended_at`은 종료 시에만 | R-15 |

**A.1.1 `executors[]` 원소**

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `type` | string | 필수 | `EXECUTOR_TYPES` (`browser`\|`api`\|`human`) |
| `driver` | string \| null | 필수(nullable) | `type=browser`일 때 `ego-lite`\|`agent-browser`\|`cmux`\|`playwright` |
| `session_mode` | string \| null | 필수(nullable) | `orca-managed` \| `owned-surface` \| `standalone` \| `null` |
| `driver_version` | string \| null | 필수(nullable) | 후보가 `probe`로 반환한 값. 하네스가 `--version` 문자열을 자체 파싱해 채우지 않는다(NR-7) |
| `client` | string \| null | 선택 | `type=api`일 때 HTTP 클라이언트 식별자 |

**A.1.2 `candidates[]` 원소 — 후보 탐색 기록 (공통 필수)**

`run.json`의 최상위 `candidates` 배열. 선택된 executor뿐 아니라 **제외·실패한 후보 전건**을 순서대로 기록한다. T07 완료 기준 5번("선택·제외된 전 후보의 binary path·version·resolution_source·제외 사유가 candidates[]에 기록된다")·T08 완료 기준 2번·4번의 검증 대상이며, MV-38이 `infra_error` 이후 후보 시도 여부를 판정하는 대상도 이 배열이다.

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `order` | integer | 필수 | 1부터의 시도 순서 |
| `type` | string | 필수 | `EXECUTOR_TYPES` |
| `driver` | string \| null | 필수(nullable) | `type=browser`일 때 후보 driver 이름 |
| `session_mode` | string \| null | 필수(nullable) | A.1.1과 동일 enum |
| `binary_path` | string(path) \| null | 필수(nullable) | 해석된 실행 파일 경로 |
| `resolution_source` | string \| null | 필수(nullable) | `path` \| `orca-bundle` \| `managed-cache` \| `installed` \| `null` |
| `version` | string \| null | 필수(nullable) | 후보가 반환한 원문. 미실행 제외면 `null` 가능 |
| `outcome` | string | 필수 | `selected` \| `excluded` \| `provider_unavailable` \| `infra_error` |
| `excluded_by` | string \| null | 필수(nullable) | `outcome=excluded`일 때 `minimum_version` \| `capability_missing`. **`tested_range` 밖 binary의 probe 실패는 `excluded`가 아니라 `outcome=infra_error`다**(§A.15·§C.7·제안서 §11) |
| `reason` | string \| null | 필수(nullable) | 후보가 반환한 error code 원문. 하네스가 재작문하지 않는다(NR-7) |

[MUST] `outcome=selected`인 원소는 **필요 executor 타입마다 정확히 0개 또는 1개**다. 필요 타입 집합은 `e2e_contract.EXECUTOR_MATRIX[profile]["required"]`가 소유한다 — 단일 타입 profile(`browser`·`api`·`manual`)에서는 배열 전체가 0개 또는 1개이고, `hybrid`(`api`+`browser`)처럼 복수 타입을 요구하는 profile에서는 타입별로 1개씩이므로 배열에 2개가 올 수 있다. 필요 타입 중 하나라도 selected가 0개이면 `status`는 `executor_unavailable`이어야 한다(`e2e_contract.py:269-273` `can_try_next_provider` 소진 경로).

> **개정 경위(PM, 2026-09-15)**: 최초 문언은 배열 전체를 0/1로 규정해 `EXECUTOR_MATRIX["hybrid"]["required"] == ("api","browser")`와 충돌했다. `EXECUTOR_MATRIX`는 `e2e_contract.py:57`에 있고 C-1이 이 파일을 변경 0으로 동결하므로 hybrid의 2종 요구는 움직일 수 없다. 태스크 125가 확정한 상위 계약이 이 태스크 문서보다 우선하므로 이 문서를 타입별 규정으로 정정한다. 타입별 상한 1개라는 제약 자체는 약화되지 않는다.

`run.json`에 새 상태값이나 새 exit 값이 등장하지 않는 것이 NR-1 준수의 관측 지점이다(`TRD.md` §5.1).

### A.2 `journal.json` — 상태 전이 이력 (공통 필수)

경로: `$OPAL_E2E_ARTIFACT_DIR/journal.json`. `awaiting_human` 재개의 입력이다(`TRD.md` §7).

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `schema_version` | string | 필수 | `"2.0"` |
| `run_id` | string | 필수 | A.0 |
| `transitions` | object[] | 필수 | A.2.2 |
| `resume` | object \| null | 필수(nullable) | `awaiting_human`일 때만 비-null. A.2.3 |

**A.2.1 상태 enum** (`TRD.md` §5.2 = 제안서 §5.2 채택)

`created` → `context_resolved` → `ports_leased` → `sut_starting` → `sut_ready` → `profile_resolved` → `executor_ready` → `scenario_running` ↔ `awaiting_human` → `evidence_captured` → `{pass|fail|executor_unavailable|blocked|infra_error}` → `{cleanup_complete|cleanup_warning}`

**A.2.2 `transitions[]` 원소**

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `from` | string \| null | 필수(nullable) | 최초 전이는 `null` |
| `to` | string | 필수 | A.2.1 enum |
| `at` | string(ISO-8601) | 필수 | — |
| `detail` | object | 선택 | 전이 사유·오류 정보 |

[MUST] 중간 상태를 건너뛴 `pass`는 허용하지 않는다(`TRD.md` §5.2). `to="pass"` 전이는 직전에 `evidence_captured`가 기록되어 있을 때만 유효하다 — §D.2 MV-06이 검증한다.

**A.2.3 `resume` 객체**

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `resume_token` | string | 필수 | A.0 |
| `issued_at` | string(ISO-8601) | 필수 | — |
| `expires_at` | string(ISO-8601) | 필수 | `issued_at + handoff.timeout_seconds` |
| `expired` | boolean | 필수 | timeout 종료 시 기록. R-13 "재개 가능 여부가 기록된다" |
| `server_policy` | string | 필수 | `keep` \| `terminate` (§A.9) |
| `resumed_at` | string(ISO-8601) \| null | 필수(nullable) | 재개 전 `null` |

### A.3 `owned.json` — 소유 자원 대장 (공통 필수)

경로: `$OPAL_E2E_ARTIFACT_DIR/owned.json`. 근거: `TRD.md` TD-15 — "정리는 이 대장에 있는 것만 대상으로 한다."

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `schema_version` | string | 필수 | `"2.0"` |
| `run_id` | string | 필수 | A.0 |
| `process_groups` | object[] | 필수 | `{pgid: int, role: "backend"\|"frontend", started_at: string}` |
| `leases` | object[] | 필수 | A.7 lease record의 `lease_id` 참조 배열: `{lease_id, port, role}` |
| `browser_pages` | object[] | 필수 | `{page_id, driver, session_mode, user_owned: boolean}` |
| `browser_profiles` | string[] | 필수 | 삭제 대상 profile 경로. R-16 "브라우저 프로필은 run 종료 후 삭제" |
| `cmux_surfaces` | object[] | 필수 | `{surface_handle, user_owned: boolean}` |
| `api_fixtures` | object[] | 필수 | `{fixture_id, namespace, endpoint}` — `namespace`는 `run_id` |

[MUST] `user_owned == true`인 원소는 정리 대상에서 **제외**한다(`TASK.md` C-2, R-8). 패턴 매칭·전역 스캔으로 정리 대상을 넓히지 않는다.

### A.4 `actions.jsonl` 1행 — 행동 기록 (공통 필수)

경로: `$OPAL_E2E_ARTIFACT_DIR/actions.jsonl`. 파일은 JSON Lines이며 **1행 = 1 action**이다.

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `seq` | integer | 필수 | 1부터 증가 |
| `at` | string(ISO-8601) | 필수 | — |
| `step_id` | string | 필수 | 시나리오 `steps[].id` |
| `executor` | string | 필수 | `EXECUTOR_TYPES` (`e2e_contract.py:41`) |
| `step_role` | string | 필수 | `verify` \| `setup` \| `cleanup` — 기본값 `verify` |
| `action` | string | 필수 | driver/executor 연산명 (§B.2·§B.3) |
| `wait_kind` | string \| null | **조건부 필수** | `action == "wait"`이면 필수. `navigation_ready` \| `transport` \| `assertion_condition` |
| `request` | object \| null | 조건부 필수 | `executor == "api"`이면 필수. `{method, url, headers, body_ref, timeout_ms}` — headers/body는 redaction 후 |
| `response` | object \| null | 조건부 필수 | `executor == "api"`이면 필수. `{status, body_ref, elapsed_ms}` |
| `result` | string | 필수 | `ok` \| `error` |
| `error_code` | string \| null | 필수(nullable) | 후보가 반환한 error code 원문. 하네스가 재해석하지 않음 |
| `current_url` | string \| null | 선택 | browser action 이후 URL |
| `elapsed_ms` | integer | 필수 | — |

[MUST] `step_role`은 §C.4 surface fidelity 집행의 입력이다. `TRD.md` TD-17: "setup·cleanup API와 검증 대상 API를 step 단위로 구분 표시한다."

[MUST] `wait_kind` 누락은 `fail`이 아니라 `infra_error`로 fail-safe된다 — `e2e_contract.py:229-231`이 `wait_kind == "assertion_condition"`일 때만 `fail`을 반환하기 때문이다(`TRD.md` TD-11, RK-6).

### A.5 `assertions.json` — 기대값·실제값 (공통 필수)

경로: `$OPAL_E2E_ARTIFACT_DIR/assertions.json`. `validate_pass_requirements`가 `expected`/`actual` 존재와 일치를 직접 검사한다(`e2e_contract.py:337-355`).

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `schema_version` | string | 필수 | `"2.0"` |
| `run_id` | string | 필수 | A.0 |
| `results` | object[] | 필수 | A.5.1. 최소 1개 — 0개면 `assertion_required`로 `fail`(`e2e_contract.py:330-337`) |

**A.5.1 `results[]` 원소**

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `id` | string | 필수 | 시나리오 `assertions[].id`와 동일. `e2e_contract.py:284-290`가 이 키로 대조 |
| `verifier` | string | 필수 | `ui` \| `response` \| `state` \| `human` |
| `executor` | string | 필수 | `EXECUTOR_TYPES` |
| `expected` | any | 필수 | **키 자체가 없으면** `assertion_expected_actual_missing`(`e2e_contract.py:341-347`) |
| `actual` | any | 필수 | 같음 |
| `passed` | boolean | 필수 | `expected == actual` |
| `at` | string(ISO-8601) | 필수 | — |
| `evidence_refs` | string[] | 선택 | 이 assertion을 뒷받침하는 artifact 상대경로 |

[MUST] `expected`/`actual`은 `null`일 수 있으나 **키는 반드시 존재**해야 한다. `e2e_contract.py:340`은 `"expected" not in observed`로 키 존재를 본다.

### A.6 `cleanup.json` — 정리 결과 (공통 필수)

경로: `$OPAL_E2E_ARTIFACT_DIR/cleanup.json`.

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `schema_version` | string | 필수 | `"2.0"` |
| `run_id` | string | 필수 | A.0 |
| `result` | string | 필수 | `complete` \| `warning` \| `failed` |
| `released` | object[] | 필수 | `{kind, id}` — `kind`는 `process_group`\|`lease`\|`browser_page`\|`browser_profile`\|`cmux_surface`\|`api_fixture` |
| `leaked` | object[] | 필수 | 같은 형태. 비어있지 않으면 A.6.1 승격 규칙 적용 |
| `skipped_user_owned` | object[] | 필수 | `user_owned=true`라 건너뛴 자원. C-2 집행 증적 |
| `escalated_to_infra_error` | boolean | 필수 | A.6.1 결과 |

**A.6.1 승격 규칙**: cleanup 결과는 verdict를 바꾸지 않는다. 단 `leaked[]`에 `kind ∈ {process_group, lease}`가 있으면 다음 실행을 오염시키므로 run 상태를 `infra_error`로 **승격**한다(`TRD.md` TD-15, 제안서 §5.2). 승격은 `escalated_to_infra_error=true`로 기록된다. `browser_page`·`api_fixture` 누출은 승격 대상이 아니며 `cleanup="warning"`으로 남는다.

### A.7 lease record — 포트 임대 (`TRD.md` TD-3)

경로: `{artifact_root}/.leases/{lease_id}.json`. allocator lock 파일은 `{artifact_root}/.leases/.lock`이다.

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `schema_version` | string | 필수 | `"2.0"` |
| `lease_id` | string | 필수 | `{run_id}-{role}` |
| `run_id` | string | 필수 | A.0 |
| `owner_pid` | integer | 필수 | 하네스 프로세스 PID |
| `port` | integer | 필수 | 1024–65535 |
| `role` | string | 필수 | `backend` \| `frontend` |
| `state` | string | 필수 | `reserved` \| `confirmed` \| `released` — 기본값 `reserved` |
| `created_at` | string(ISO-8601) | 필수 | — |
| `confirmed_at` | string(ISO-8601) \| null | 필수(nullable) | health 통과 시각 |
| `attempt` | integer | 필수 | 1부터. 최대 `5`(기본값, `TRD.md` TD-3 5번) |

**계약 규칙 C-LEASE-1**: allocator lock은 `os.open(lock_path, O_CREAT|O_EXCL)`로만 취득한다. `fcntl.flock`은 금지된다 — 플랫폼 분기를 낳고 `TASK.md` C-7을 어긴다(`TRD.md` TD-3).

**계약 규칙 C-LEASE-2**: `state="reserved"` 레코드가 있으나 `owner_pid`가 살아 있지 않으면 다음 실행이 회수한다(R-2). PID 생존 판정은 `lib/e2e/process.py`의 단일 어댑터 함수로만 수행한다(`TRD.md` TD-16).

**계약 규칙 C-LEASE-3**: 기동은 strict port다. uvicorn은 지정 포트 점유 시 기동 실패하고, vite는 `--strictPort`를 명시한다. 기동 실패(EADDRINUSE)면 레코드를 폐기하고 `attempt`를 올려 재할당한다(`TRD.md` TD-3).

### A.8 capability probe 결과 (`docs/proposals/opal-e2e-harness.md` §7.7)

**저장 경로**: `$OPAL_E2E_ARTIFACT_DIR/probe.json` — 객체가 아니라 **후보별 probe 결과 배열**(`{"schema_version":"2.0","probes":[<A.8 객체>, ...]}`)로 저장한다. run 1회에 복수 후보를 probe하므로 단일 객체로는 후보 소진 경로를 기록할 수 없다. MV-14의 검사 대상 파일이 이 경로다.

driver/executor의 `probe` 연산 반환값. 하네스는 이 객체 **외의 어떤 근거로도 가용성을 판정하지 않는다**(NR-7).

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `driver` | string | 필수 | `ego-lite` \| `agent-browser` \| `cmux` \| `playwright` \| `opal-http` \| `human` |
| `session_mode` | string \| null | 필수(nullable) | `orca-managed` \| `owned-surface` \| `standalone` \| `null` |
| `available` | boolean | 필수 | — |
| `version` | string \| null | 필수(nullable) | 후보가 반환한 원문 |
| `unavailable_reason` | string \| null | 필수(nullable) | `available=false`일 때 후보가 반환한 error code 원문 |
| `capabilities` | object | 필수 | key → A.8.1. key 집합: `snapshot`, `screenshot`, `console`, `errors`, `network_har`, `isolated_profile` |

**A.8.1 capability 원소**

| 필드 | 타입 | 필수/선택 | 기본값 |
|---|---|---|---|
| `available` | boolean | 필수 | `false` |
| `route` | string | 필수 | `native` \| `exec` |
| `probed` | boolean | 필수 | `false` |

[MUST] `probed == false`인 optional capability는 보수적으로 `available=false`다(제안서 §7.7, `TRD.md` §9 Q-3). help 문자열·번들 파일 존재로 승격하지 않는다.

**실측 의존(Q-2/Q-3)**: `console`·`errors`·`network_har`의 `route`와 `available` **값**은 E3 비파괴 probe 실측에 의존한다. 그러나 **세 키의 존재와 A.8.1 형태는 이 계약이 확정**한다 — 미확인 상태에서도 `{available:false, route:"exec", probed:false}`로 반드시 존재한다.

**capability ↔ artifact 고정 매핑** (`TRD.md` TD-10, 제안서 §5.3):

| capability | artifact 상대경로 |
|---|---|
| `snapshot` | `browser/before.snapshot`, `browser/after.snapshot` |
| `screenshot` | `screenshots/{scenario_id}-{step_id}.png` |
| `console` | `browser/console.jsonl` |
| `errors` | `browser/errors.jsonl` |
| `network_har` | `browser/network.har` |

capability 요구는 시나리오의 `required_evidence` 원소로 표현하며 별도 `requires` 필드를 만들지 않는다(`TRD.md` TD-12 결정 3).

### A.9 `handoff.json` — 사람 단계 인계 (collaborative·manual 필수)

경로: `$OPAL_E2E_ARTIFACT_DIR/human/handoff.json`. **필수 8필드는 `e2e_contract.py:67-76` `HANDOFF_REQUIRED_FIELDS`가 소유한다.**

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `handoff_id` | string | 필수(계약) | A.0 형식 |
| `instruction` | string | 필수(계약) | 사람이 수행할 일. 비어있으면 검증 실패(`e2e_contract.py:495-500`) |
| `expected_observation` | string | 필수(계약) | 기대 관찰 결과 |
| `required_evidence` | string[] | 필수(계약) | 비어 있으면 실패. 예: `["final_url","screenshot"]`(제안서 §7.5) |
| `timeout_seconds` | integer | 필수(계약) | > 0 |
| `resume_token` | string | 필수(계약) | A.0 |
| `server_policy` | string | 필수(계약) | **`keep` \| `terminate`** — 이 계약이 enum을 확정한다 |
| `submission_path` | string(path) | 필수(계약) | 사람이 제출물을 쓸 절대경로. 기본 `$OPAL_E2E_ARTIFACT_DIR/human/submission.json` |
| `actor` | string | 필수 | `"human"` 고정(제안서 §7.5) |
| `run_id` | string | 필수 | A.0. `scenario.py:504-513` resume 검증 입력 |
| `step_id` | string | 필수 | 인계 시점의 step |
| `issued_at` | string(ISO-8601) | 필수 | — |

**`server_policy` 의미**(`TRD.md` TD-18):
- `keep`: 대기 중 lease와 프로세스 그룹을 **살린 채** exit 20으로 제어를 넘긴다.
- `terminate`: 정리한 뒤 exit 20으로 넘기고, 재개 시 재기동한다. 재기동은 새 포트를 임대하며 `run.json.urls`를 갱신한다.

### A.10 `submission.json` — 사람 제출물 (collaborative·manual 필수)

경로: `handoff.submission_path`.

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `run_id` | string | 필수 | `scenario.py:482-528`이 handoff와 **일치 검증**한다 |
| `resume_token` | string | 필수 | 같음 |
| `handoff_id` | string | 필수 | — |
| `completed` | boolean | 필수 | 사람의 완료 선언 |
| `observations` | object | 필수 | `required_evidence` 키별 관찰값. 예: `{"final_url": "..."}` |
| `evidence_paths` | object | 필수 | `required_evidence` 키별 artifact 절대경로 |
| `note` | string | 선택 | 자유 기술 |
| `submitted_at` | string(ISO-8601) | 필수 | — |

[MUST] `completed: true`는 **pass 선언이 아니다.** 제출 후에도 `validate_pass_requirements`를 다시 통과해야 pass로 기록된다(`scenario.py:504-513`, R-13, 제안서 §7.5).

### A.11 API 증적 (`api`·`hybrid` profile 필수)

경로: `$OPAL_E2E_ARTIFACT_DIR/api/requests.jsonl`, `api/responses.jsonl`. 1행 = 1 호출이며 `actions.jsonl`의 `seq`로 상호 참조한다.

| `requests.jsonl` 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `seq` | integer | 필수 | `actions.jsonl.seq`와 동일 |
| `method` | string | 필수 | HTTP method |
| `url` | string | 필수 | **redaction 통과 후** (query secret 마스킹) |
| `headers` | object | 필수 | redaction 통과 후 |
| `body` | any \| null | 필수(nullable) | 기본 미수집(`null`). 시나리오 allowlist endpoint만 수집(제안서 §10.3) |
| `timeout_ms` | integer | 필수 | — |
| `step_role` | string | 필수 | `verify` \| `setup` \| `cleanup` |

| `responses.jsonl` 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `seq` | integer | 필수 | — |
| `status` | integer | 필수 | HTTP status |
| `headers` | object | 필수 | redaction 통과 후 (`Set-Cookie` 포함) |
| `body` | any \| null | 필수(nullable) | allowlist만 |
| `elapsed_ms` | integer | 필수 | — |
| `redacted` | boolean | 필수 | redaction 적용 여부 |

### A.12 redaction 결과

모든 증적 쓰기는 `lib/e2e/evidence.py`를 거치고, `evidence.py`는 저장 직전 반드시 `lib/e2e/redaction.py`를 통과시킨다(`TRD.md` TD-14).

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `artifact_path` | string(path) | 필수 | — |
| `redacted_fields` | string[] | 필수 | 마스킹된 위치 목록 |
| `redaction_failed` | boolean | 필수 | — |

**대상**: `Authorization`·`Cookie`·`Set-Cookie` 헤더, URL query의 비밀값. HAR 포함(`TASK.md` C-6, 제안서 §10.3).

[MUST] redaction 또는 안전한 저장에 실패하면 **원문을 남기지 않고** 해당 run을 `infra_error`로 판정한다(`TASK.md` C-6). `TRD.md` TD-13에 따라 전환 없이 중단한다.

### A.13 Console PID 레코드 (`opal-cli` 소유, 문서 계약)

[MUST] **경로·문자열 필드의 허용 문자 집합** (BLOCKED-4, PM 확정): `opal_home`·`app_dir`·`host`는 큰따옴표(`"`)·역슬래시(`\`)·제어문자(`[[:cntrl:]]` 전체 — 개행·탭·CR·ESC 포함)를 **포함할 수 없다**. 순수 셸 파서가 이스케이프를 수행하지 않으므로, writer는 위반 값을 만나면 파일을 만들지 않고 실패한다(fail-safe). `start`도 **같은 한 벌의 검사**로 기동 전에 차단해 "데몬은 떴는데 레코드만 없어 종료 불가능한 고아"가 생기지 않게 한다. `port`는 10진 정수다.

#### A.13.1 `pid` 안전 조건 (B-1, PM 확정)

[MUST] 레코드의 `pid`가 **2 이상의 10진 정수가 아니면 종료 대상으로 삼지 않는다.** POSIX `kill(1)`에서 `0`은 호출자의 프로세스 그룹 전체, 음수는 그 절대값의 프로세스 그룹, `1`은 init이다. 검증 실패 값은 새 분기를 만들지 않고 **"레코드 해석 불가" 분기로 합류**해 아무것도 종료하지 않는다(`stopped=false pid=- reason=unreadable_record`). writer·stop·status 세 경로가 같은 검증 함수를 공유한다.

근거: T02 보안 검사가 `"pid": 0` 레코드로 실증했다 — 정규식 추출·비어있지 않음·`app_dir` 일치·`kill -0 0` 성공(POSIX상 항상)을 차례로 통과해 `kill 0`에 도달하며, 이는 `console stop`을 호출한 셸의 잡 전체를 종료한다. 레코드는 `$OPAL_HOME/run/`의 평문 JSON이고 `install-mac.sh`가 이 경로를 무인 호출하므로 침묵 종료가 성립한다. 광역 `pkill`을 제거한 자리에 "의도치 않게 광역인 kill"을 남기지 않기 위한 조건이다.

경로: `$OPAL_HOME/run/console.pid` (JSON). 이 파일 포맷은 `test-tool`과 `opal-cli`가 공유하는 **유일한** 것이며 런타임 의존은 0이다(`TRD.md` §3.1, §C.1).

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `pid` | integer | 필수 | `console.sh` start의 `$!` |
| `opal_home` | string(path) | 필수 | 기동 시점 `${OPAL_HOME:-$HOME/.opal}` (`console.sh:32`) |
| `app_dir` | string(path) | 필수 | `$opal_home/dashboard-server` (`console.sh:37`) |
| `host` | string | 필수 | `"127.0.0.1"` (`console.sh:39`) |
| `port` | integer | 필수 | `7823` (`console.sh:40`) |
| `started_at` | string(ISO-8601) | 필수 | — |

[MUST] E2E 하네스는 이 파일을 **읽지도 쓰지도 않는다.** 자기 프로세스는 `$OPAL_E2E_ARTIFACT_DIR/server/*.pid`로만 추적한다(`TRD.md` TD-5 "하네스 쪽 대칭 규칙").

### A.14 환경 변수 계약 (`TRD.md` TD-8)

`e2e run`이 child 프로세스에 주입하는 변수. 기존 변수는 재정의하지 않는다.

| 변수 | 타입 | 주입 주체 | 기본값 |
|---|---|---|---|
| `OPAL_E2E_RUN_ID` | string | 하네스 → child | 없음(필수) |
| `OPAL_E2E_TARGET` | enum string | 하네스 → child | 없음(필수) |
| `OPAL_E2E_BACKEND_PORT` | integer string | 하네스 → child | 없음(필수) |
| `OPAL_E2E_FRONTEND_PORT` | integer string | 하네스 → child | frontend 미기동 시 미주입 |
| `OPAL_E2E_ARTIFACT_DIR` | path | 하네스 → child | 없음(필수) |
| `OPAL_E2E_ARTIFACT_ROOT` | path | 사용자 → 하네스 | `${TMPDIR}/opal-e2e-runs` |
| `VITE_API_BASE_URL` | string | 하네스 → vite | dev 파일 기본값 `http://127.0.0.1:7823`, production `""` |
| `OPAL_CONSOLE_CORS_ORIGINS` | 쉼표 구분 string | 하네스 → backend | 미설정 시 코드 기본 dev origin 2종만 |
| `OPAL_HOME` | path | 하네스 → child 한정 | `target=installed`일 때만 격리값 주입 |

[MUST] `VITE_API_BASE_URL`은 Vite 시작·build 시점 설정으로만 쓰고 base에 `/api` prefix를 넣지 않는다(`TASK.md` C-8). production/installed는 빈 문자열 + 동일 오리진이다.

[MUST] `AGENT_BROWSER_*` 계열은 standalone 실행 시 child env에서 **제거한 뒤** 하네스 소유 값만 주입한다(`TRD.md` TD-8 규칙 2, 제안서 §8.3 ambient config 차단).

### A.15 driver manifest (`lib/e2e/drivers/manifest.json`)

driver별 버전 정책의 **단일 SSOT**다(`TRD.md` §6.3·TD-11, 제안서 §8.3 "버전 SSOT는 driver manifest 한 곳"). 저장소에 커밋되는 소스 파일이며 run artifact가 아니다. T05 완료 기준 4번(`minimum_version` 미만 binary를 probe 없이 제외하고 `candidates[]`에 `excluded_by`·version 기록)의 판정 근거가 이 파일이다.

```json
{
  "schema_version": "1.0",
  "drivers": {
    "agent-browser": { "minimum_version": "0.27.0", "tested_range": "0.27.x", "ci_pin": "0.27.0" }
  }
}
```

| 필드 | 타입 | 필수/선택 | 값 |
|---|---|---|---|
| `schema_version` | string | 필수 | `"1.0"` 고정 |
| `drivers` | object | 필수 | key = driver 이름(`A.8 driver` enum과 같은 집합) |
| `drivers.<name>.minimum_version` | string | 필수 | semver. 미만 binary는 **probe 없이** 후보에서 제외하고 `candidates[].excluded_by = "minimum_version"`으로 기록 |
| `drivers.<name>.tested_range` | string | 필수 | semver range. 범위 밖 binary는 탈락시키지 않고 warning + version metadata를 남긴 뒤 필수 capability probe로 판정하며, **그 probe 실패는 `infra_error`로 승격**한다(제안서 §8.3·§11) |
| `drivers.<name>.ci_pin` | string | 필수 | OPAL managed cache와 CI만 exact 적용. 자동 upgrade 금지 |

[MUST] 버전 비교는 문자열 비교가 아니라 semver 비교로 수행한다. 초기값(`0.27.0` / `0.27.x` / `0.27.0`)은 2026-09-12 로컬 Orca 번들 실측치이며, 값 갱신은 이 파일에서만 한다 — 코드·문서에 버전 리터럴을 복제하지 않는다.

---

## §B 시그니처

### B.1 `test-tool e2e` CLI

진입점은 `opal/tools/test-tool/run.sh`로 단일 유지되며 exit code 계약이 갈라지지 않는다(`TRD.md` TD-1).

#### B.1.1 `test-tool e2e run`

```
test-tool e2e run --scenario <scenario-id> --task-path <path> --target <source-main|source-worktree|installed>
                  [--worktree-root <path>] [--opal-home <path>]
                  [--artifact-root <path>] [--run-id <id>]
```

| 인자 | 필수/선택 | 제약 |
|---|---|---|
| `--scenario` | 필수 | `test-scenario.json`의 `id`. `schema_version="2.0"` 필요(C-125-2) |
| `--task-path` | 필수 | 태스크 폴더 절대경로 |
| `--target` | 필수 | 3종 enum |
| `--worktree-root` | 조건부 필수 | `--target=source-worktree`일 때. 미지정 시 `git rev-parse --show-toplevel` |
| `--opal-home` | 조건부 필수 | `--target=installed`일 때. **사용자 실제 `~/.opal`과 경로가 같으면 거부**(§C.5) |
| `--artifact-root` | 선택 | 기본 `${OPAL_E2E_ARTIFACT_ROOT:-${TMPDIR}/opal-e2e-runs}` |
| `--run-id` | 선택 | 미지정 시 A.0 형식으로 생성 |

**stdout(JSON)**: `{run_id, scenario_id, profile, status, operational_status, error, exit_code, run_json_path, artifact_dir}`
**exit**: `status_to_exit(status)` (`e2e_contract.py:125`). 값은 0/6/7/18/19/20 중 하나이며 새 값을 배정하지 않는다.

[MUST] `e2e run`은 **1회 실행**이며 재시도 루프를 내장하지 않는다(`test_tool.py:25-26` 계약, `TRD.md` TD-1). 재시도 루프는 오케스트레이터 책임이다.

#### B.1.2 `test-tool e2e resume`

```
test-tool e2e resume --run-id <id> --token <resume-token> --submission <path> [--artifact-root <path>]
```

- 세 인자 모두 필수. `--submission`은 A.10 스키마 JSON 파일 경로.
- 판정은 새 경로를 만들지 않고 `scenario.py:482-528`의 기존 resume 검증을 호출한다(`TRD.md` TD-18).
- `run_id` 불일치·`resume_token` 불일치·제출물 내부 `run_id`/`resume_token` 불일치는 전부 거부된다.
- **stdout(JSON)**: `e2e run`과 동일 형태 + `{verifier_results: [...]}`.
- **exit**: `status_to_exit(status)`.

[MUST] 사람 제출만으로는 `pass`가 되지 않는다. 재개 후 `validate_pass_requirements`를 다시 통과해야 최종 판정이 난다(R-13).

#### B.1.3 `test-tool e2e status`

```
test-tool e2e status (--run-id <id> | --artifact-dir <path>) [--artifact-root <path>]
```

- **stdout(JSON)**: `{run_id, scenario_id, profile, target, state, status, operational_status, urls, artifact_dir, journal_tail}` — `journal_tail`은 최근 전이 N개.
- **exit**: 항상 `0`(조회 명령). 대상 run을 찾지 못하면 `{"error": "run_not_found"}`와 exit `0`이 아니라 기존 도구의 usage 오류 코드를 쓴다 — 새 exit 값을 배정하지 않는다.

#### B.1.4 `test-tool e2e clean`

```
test-tool e2e clean (--run-id <id> | --stale) [--artifact-root <path>] [--dry-run]
```

- `--stale`: `owner_pid`가 살아 있지 않은 lease record와 그에 딸린 프로세스 그룹을 회수(C-LEASE-2).
- **stdout(JSON)**: `{reclaimed_leases: [...], terminated_process_groups: [...], removed_artifact_dirs: [...], skipped: [...]}`.
- `skipped[]`에는 `user_owned=true`라 제외한 자원이 들어간다.
- **exit**: `0`.

[MUST] `clean`은 `$OPAL_HOME/run/console.pid`를 보지 않으며 프로세스 이름 패턴을 쓰지 않는다(§C.1).

### B.2 Browser driver 연산 (`kind: driver-op`)

제안서 §7.6이 "구현 언어의 클래스나 프로토콜을 먼저 확정하지 않는다. 우선 JSON 입출력 계약을 고정한다"고 했으므로, 아래 JSON 입출력이 실제 계약 표면이다.

| 연산 | 입력 | 최소 출력 |
|---|---|---|
| `probe` | `{runtime_context, required_capabilities[]}` | A.8 capability probe 결과 전체 |
| `open` | `{url, isolation_key}` | `{handle, owned: boolean, current_url}` |
| `snapshot` | `{handle, label}` | `{snapshot, current_url, artifact_path}` |
| `act` | `{handle, action:{kind, target, value?}}` | `{ok, action_result, current_url}` |
| `wait` | `{handle, condition, wait_kind, timeout_ms}` | `{satisfied, wait_kind, elapsed_ms}` |
| `assert` | `{handle, assertion:{id, verifier, expected}}` | `{id, expected, actual, passed}` |
| `capture` | `{handle, evidence_spec[]}` | `{artifacts:{name→path}, redacted, redaction_failed}` |
| `close` | `{handle}` | `{closed, released[], leaked[]}` |

**계약 규칙 C-DRV-1** [MUST]: `wait`의 `wait_kind`는 **필수 인자**다(`TRD.md` TD-11, RK-6). 호출자가 생략하면 driver는 실행하지 않고 오류를 반환한다. 이것이 `e2e_contract.py:229-231`의 `fail`/`infra_error` 분기를 살리는 유일한 경로다.

**계약 규칙 C-DRV-2** [MUST]: 가용성 판정은 `probe` 반환값만 소비한다. 하네스가 `uname`·`--version` 문자열 파싱·번들 파일 존재로 가용성을 추정하지 않는다(NR-7). 이는 `opal/tools/test-tool/lib/e2e_adapter.py:18`이 이미 명문화한 [MUST]이며 새 driver에도 그대로 적용한다.

**계약 규칙 C-DRV-3**: 기본 후보 순서는 `agent-browser/orca-managed` → `cmux/owned surface` → `agent-browser/standalone` → `ego-lite/standalone` → `playwright(opt-in)`이다(`TRD.md` TD-11).

> **개정 경위(PM, ADD-1)**: 최초 순서에는 `ego-lite`가 없었다. main의 태스크 129가 Ego Lite를 브라우저 후보로 도입했으므로 driver 체인에도 등재한다.
>
> **1순위가 아니라 `agent-browser/standalone` 다음에 두는 이유**: `ego-lite`는 **부분 driver**다 — `ego-browser-tool`의 `smoke`가 open과 텍스트 assert를 융합해 제공할 뿐 `act`·`wait`·`snapshot`·`capture`가 없다. 앞에 두면 UI 조작이 필요한 시나리오에서도 먼저 `selected`되고 실행 도중 `driver_operation_unimplemented`로 `blocked`가 되어, **더 완전한 driver를 가리는 기본값**이 된다. 현재 후보 게이트는 capability(§A.8.1 6키)만 보고 "이 시나리오가 `act`를 쓰는가"를 표현할 수단이 없으므로 순서로 방어한다. 태스크 129가 legacy `integration` 경로에 둔 Ego Lite 우선순위는 그 경로에서 유지된다 — 그쪽은 애초에 smoke 전용이다.
>
> 순서는 **기본값**이며 `resolve_candidates(candidate_order=...)`로 재정의할 수 있다. smoke 형태만 도는 프로젝트는 이 수단으로 `ego-lite`를 1순위에 올린다. 전환 허용 조건(`can_try_next_provider()`)은 순서와 무관하게 불변이다. 전환 허용은 `can_try_next_provider()`(`e2e_contract.py:269`) 판정에만 의존하며 adapter가 자체 전환 조건을 만들지 않는다(`TASK.md` C-3).

**계약 규칙 C-DRV-4**: `open`·`act`만으로는 `pass`가 될 수 없다. `assertion_results`가 비면 `validate_pass_requirements`가 `assertion_required`로 `fail`을 반환한다(`e2e_contract.py:330-337`). cmux driver 이관의 본질은 assertion·증적을 실제로 채우는 것이다(`TRD.md` TD-11).

**계약 규칙 C-DRV-5**: cmux driver는 mode A를 강제하고(`e2e_adapter.py:21`, `:169-170` `--surface` 미전달), `user_owned` surface를 정리하지 않는다.

### B.3 API·Human executor 연산 (`kind: executor-op`)

제안서 §7.3 공통 인터페이스의 API executor 구현분.

| 연산 | 입력 | 최소 출력 |
|---|---|---|
| `probe` | `{runtime_context, required_capabilities[]}` | `{executor, available, version, capabilities}` (A.8 형태) |
| `prepare` | `{run_id, target, isolation_key}` | `{handle, owned[], setup_evidence[]}` |
| `act` | `{handle, action:{method, url, headers?, body?, timeout_ms, step_role}}` | `{ok, status, response_ref, observed_state}` |
| `assert` | `{handle, assertion:{id, verifier, expected}}` | `{id, expected, actual, passed}` |
| `capture` | `{handle, evidence_spec[]}` | `{artifacts:{name→path}, redacted, redaction_failed}` |
| `cleanup` | `{handle}` | `{released[], leaked[], skipped_user_owned[]}` |

Human handoff 연산:

| 연산 | 입력 | 최소 출력 |
|---|---|---|
| `handoff` | `{run_id, scenario_id, step_id, handoff_spec}` | A.9 `handoff.json` 전체 |
| `resume` | `{run_id, resume_token, submission_path}` | `{accepted, status, error, verifier_results[]}` |

**계약 규칙 C-API-1** [MUST]: 실제 SUT의 공개 HTTP endpoint를 호출한다. mock server로 대체한 결과는 E2E가 아니다(제안서 §7.4, R-11).

**계약 규칙 C-API-2**: retry는 **같은 후보 안의 명시된 일시적 transport 오류**에만 적용한다. 허용 목록은 다음으로 확정한다 — 연결 거부(`ECONNREFUSED`), 연결 초기화(`ECONNRESET`), DNS 일시 실패, TCP 연결 타임아웃. **제품의 4xx/5xx는 절대 포함하지 않는다**(제안서 §7.4, `TRD.md` TD-13 "허용되는 유일한 재시도"). 재시도 상한은 기본 3회.

**계약 규칙 C-API-3**: API fixture는 `run_id`로 namespace하고 자기 것만 정리한다. DB 직접 조회는 후속 state verifier로만 쓰고 공개 API 행동을 대체하지 않는다(제안서 §7.4, `TRD.md` TD-17).

**계약 규칙 C-HUM-1**: `manual`도 자유 형식 응답을 받지 않는다. instruction·expected observation·evidence·verifier를 반드시 갖는다(제안서 §7.5).

**계약 규칙 C-HUM-2**: timeout은 자동 `fail`이 아니라 `blocked`(exit 19)로 종료하고 resume token 만료 여부를 `journal.json.resume.expired`에 기록한다(`TRD.md` TD-18, R-13).

### B.4 `opal-cli console` 변경 시그니처

| 서브명령 | 현행 동작 | 변경 후 계약 |
|---|---|---|
| `console start` | `nohup uvicorn ... &` 후 PID를 **메시지로만 출력**(`console.sh:75-81`) | 기동 직후 A.13 PID 레코드를 `$opal_home/run/console.pid`에 기록. 인자·포트는 불변(`127.0.0.1:7823`) |
| `console stop` | `pkill -f "dashboard.backend.main:app"`(`console.sh:88`) | **`pkill` 제거.** 레코드의 `pid`가 살아 있고 `app_dir`가 이 `$OPAL_HOME`의 `dashboard-server`와 일치할 때만 종료. 레코드 없음·identity 불일치면 **아무것도 죽이지 않고** 경고로 종료 |
| `console status` | health 응답만 출력(`console.sh:95-106`) | health + 레코드의 `pid`·`app_dir` 함께 출력(소유권 관측, R-15) |

**변경 지점 2** — `scripts/install-mac.sh:1844`의 폴백 `pkill`도 같은 레코드 기반 종료로 교체한다. **두 지점 모두** 교체해야 R-4가 성립한다(`TRD.md` RK-1: "어느 하나라도 남기면 완화되지 않는다").

**계약의 근거가 되는 실측**: source E2E backend도 같은 ASGI 경로 문자열 `dashboard.backend.main:app`으로 기동될 수밖에 없으므로(패키지 절대 import 구조), 현행 `pkill -f` 패턴은 E2E backend를 **반드시 오탐 종료**한다(`TRD.md` §2.3). 이것이 AC-3 불성립의 직접 원인이다.

[MUST] **`console-*` 표면의 출력 표현 형식** (BLOCKED-1, PM 확정): `surfaces.json`의 `console-*` 3표면 `response_shape`는 **stdout의 `key=value` 사람용 라인**이지 JSON이 아니다. `console` 계열에서 stdout JSON 1줄 계약을 갖는 것은 `scan` 하나뿐이다(`opal/tools/opal-cli/lib/console.sh` C-6). 커버리지·conformance 게이트는 이 표면의 출력을 JSON으로 파싱하지 않는다.

`console-stop` 값 계약: 성공은 `stopped=true pid=<N>`, 실패는 `stopped=false reason=<사유>`이며 **pid를 아는 분기는 `pid=<N>`, 모르는 분기는 `pid=-`를 함께 낸다** — 필드가 항상 존재하도록 "미상"을 값으로 표현한다.

[MUST] **`start`의 "레코드 없음 + 포트 응답" 동작** (BLOCKED-2, PM 확정): 레코드가 없는데 `127.0.0.1:7823`이 응답하면 그것은 **소유권을 증명할 수 없는 프로세스**다. `start`는 (a) 아무것도 종료하지 않고 (b) 신규 기동도 하지 않으며 (c) 수동 조치 안내를 출력한다. 포트 소유자 탐색(`lsof` 등)으로 대상을 추정해 종료하는 폴백은 **채택하지 않는다** — 소유권 없는 종료를 금지한 §C.1의 취지를 우회하기 때문이다.

이 상태는 구버전에서 업그레이드한 전 사용자에게 **1회** 발생한다(레코드를 쓰지 않던 daemon이 떠 있는 동안). 데이터 손실은 없고 health는 계속 200이며, 사용자가 안내대로 수동 종료 후 재기동하면 해소된다. 포트가 7823로 고정돼 있고 C-2가 사용자 daemon 조작을 금지하므로 이 경로의 실행 검증은 구조적으로 불가능하며, 안내 문구의 존재는 정적 단언으로 검증한다.

### B.5 SUT HTTP 표면 (`kind: http`)

E2E가 실제로 관통해야 하는 Console 표면이다. 전수 목록과 요청/응답 형태는 `surfaces.json`이 소유한다(§D.1). 이 절은 계약 성격만 기술한다.

- `GET /health` → `{status, version}` (`dashboard/backend/main.py:102-105`). 하네스의 health gate가 이 표면을 사용한다.
- `/api/*` 16개 표면은 `dashboard/backend/routers/`의 실제 라우터 선언에서 실측 등재했다 — `brain.py`(5), `config.py`(2), `dashboard.py`(1), `doctor.py`(1), `memory.py`(1), `projects.py`(3), `tasks.py`(3).
- 이 표면들은 이번 태스크가 **계약을 바꾸지 않는다.** 검증 대상(SUT)으로서 등재되며, 커버리지 게이트의 분모가 된다(`.opal/brain/pages/concept/oppl-coverage-conformance-axis-split.md`: `surfaces.json`이 분모, 읽기 전용).
- 정적 SPA fallback(`main.py:125`, `@app.get("/{full_path:path}")`)은 API 표면이 아니라 정적 서빙 경로이므로 인벤토리에 등재하지 않는다.

---

## §C 경계

### C.1 `test-tool` ↔ `opal-cli` 무의존

```text
[test-tool]  E2E 판정·실행 SSOT
  e2e_contract.py   계약 owner (태스크 125, 변경 0)
  e2e/orchestrator  run 수명주기·상태 머신·최종 verdict 호출
  e2e/runtime       target 해석·SUT 기동·health·종료
  e2e/ports         포트 임대
  e2e/drivers/*     Browser 실행 후보
  e2e/executors/*   API · Human
  e2e/evidence      증적 수집 관문
  e2e/redaction     민감정보 마스킹
  e2e/process       OS·실행기 분기 (유일)
  scenario.py       시나리오 spec/result SSOT (변경 0)

[opal-cli]   사용자 상시 Console 소유
  console.sh        $OPAL_HOME 배포 daemon 1개만 소유·종료
```

[MUST] 두 도구는 **서로를 호출하지 않는다.** 공유하는 것은 A.13 "PID 레코드 파일 포맷" 문서 계약뿐이며 런타임 의존은 0이다(`TRD.md` §3.1).

경계의 집행 형태:
- Console stop은 `$OPAL_HOME/run/console.pid`만 본다. E2E의 `server/*.pid`를 보지 않는다.
- 하네스는 `$OPAL_E2E_ARTIFACT_DIR/owned.json`과 `server/*.pid`만 본다. `console.pid`를 읽지도 쓰지도 않는다.
- **어느 쪽도 프로세스 이름 패턴을 쓰지 않는다.** 이것이 R-4 양방향 비간섭의 구조적 근거다.

### C.2 `e2e_contract` 소유분 vs 신규 모듈 소유분

| 소유자 | 소유 대상 | 신규 모듈이 할 수 없는 것 |
|---|---|---|
| `e2e_contract.py`(125) | profile·상태·exit·error code·executor 행렬·handoff 필수 필드·pass 게이트·verdict 조립·시나리오 v2 검증 | 상태 문자열 리터럴 작성, exit 값 배정, 자체 pass 판정 |
| `scenario.py`(기존) | 시나리오 spec/result 기록·resume 검증·fidelity 게이트 | 새 resume 판정 경로 신설, `_normalize_scenario` 필드 추가 |
| `lib/e2e/*`(신규) | run 수명주기·포트 임대·SUT 기동·증적 수집·redaction·정리·driver/executor 실행 | 위 두 모듈의 기능 변경 |

[MUST] 상태·exit·error 생성은 `e2e_contract` 함수 호출로만 허용한다(C-125-1, `TRD.md` RK-8).
[MUST] 모든 증적 쓰기는 `evidence.py`를 거친다. driver·executor가 파일을 직접 쓰지 않는다 — redaction 우회 경로를 만들지 않기 위한 구조 제약이다(`TRD.md` TD-14).
[MUST] OS·실행기 분기는 `lib/e2e/process.py`가 **유일한 분기 지점**이다. 그 외 모듈은 OS 조건문을 갖지 않는다(`TRD.md` TD-16). 근거: `.opal/AGENT.md` §금지사항 "하드코딩된 플랫폼 분기 추가 금지 — 어댑터 계층에서만 수행".

### C.3 executor가 소유하는 자원 범위

| executor | 소유 | 비소유(정리 금지) |
|---|---|---|
| Browser driver | run이 만든 page/profile, `user_owned=false` cmux surface | 사용자 브라우저 탭, `user_owned=true` surface, 사용자 Orca worktree |
| API executor | `run_id` namespace의 fixture | 기존 제품 데이터, 사용자 설정 |
| Human executor | handoff/submission artifact | 사람의 브라우저 세션·인증 상태 |
| Runtime Manager | 자기 프로세스 그룹, 자기 lease | 사용자 Console daemon(`127.0.0.1:7823`), 사용자 `~/.opal` |

[MUST] `TASK.md` C-2: "사용자 소유 자원(`127.0.0.1:7823` Console daemon, 사용자 브라우저 탭·cmux surface·Orca worktree, 사용자 `~/.opal`)을 종료·삭제·재설치하지 않는다."

정리는 A.3 `owned.json` 대장에 있는 것만 대상으로 한다. 패턴 매칭·전역 스캔·사용자 소유 표시 자원은 제외한다(`TRD.md` TD-15).

### C.4 surface fidelity 경계 — API가 UI를 대체할 수 없는 지점

집행은 두 지점에서 일어난다(`TRD.md` TD-17):

1. **실행 전(정적)**: `_validate_v2_scenario`가 `steps[].executor`를 `EXECUTOR_MATRIX`와 대조해 거부한다(`e2e_contract.py:476-482`). `browser` profile 시나리오에 browser step이 없으면 `executor contract mismatch`다.
2. **실행 후(동적)**: `validate_pass_requirements`가 `observed_executors`를 행렬과 대조한다(`e2e_contract.py:311-321`). 실제로 browser executor가 동작하지 않은 `hybrid` run은 pass가 되지 않는다.

하네스가 추가로 집행할 것: `actions.jsonl.step_role`(A.4)로 setup·cleanup API와 검증 대상 API를 구분하고, **핵심 UI 행동에 대응하는 assertion이 `step_role="verify"`인 API step만으로 충족되면 거부**한다(R-12, AC-8). 이 구분 표시는 기존 `steps[]` 필드로 표현하며 신규 최상위 필드를 만들지 않는다(TD-12).

### C.5 target 경계

| target | 입력 | 금지 |
|---|---|---|
| `source-main` | 프로젝트 루트 | — |
| `source-worktree` | canonical worktree root | — |
| `installed` | `--opal-home`으로 받은 **이미 배포된 격리 `OPAL_HOME`** | 하네스가 설치 스크립트를 호출하는 것 |

[MUST] `installed` target은 배포를 수행하지 않고 사전 배포본을 입력으로 받는다(`TRD.md` TD-9). 근거: `install_dashboard()`가 FE를 **소스 트리 안에서** 빌드하고(`scripts/install-mac.sh:1772`) `:1798`에서 사용자 `~/.opal/console.config.json`을 갱신하므로, 하네스가 호출하면 R-6·C-2·C-5와 정면 충돌한다.

[MUST] 사용자의 실제 `~/.opal`을 target으로 지정하는 것은 **경로 동일성 검사로 거부**한다. 이것이 C-2의 집행 지점이다.

git 조회는 읽기 전용 명령만 사용한다(`rev-parse`, `status --porcelain`). 하네스가 저장소 상태를 바꾸지 않는다(R-6).

### C.6 산출물 경계

[MUST] 산출물은 `${OPAL_E2E_ARTIFACT_ROOT:-${TMPDIR}/opal-e2e-runs}` 하위에만 쓴다. **저장소 내부 `.e2e-runs/`·`.test-run/`을 지원하지 않는다**(`TRD.md` TD-10). 그 결과 `.gitignore` 변경이 불필요하다.

[MUST] source E2E 기본은 Vite dev server이며 `dist/`를 만들지 않는다. production asset 검증이 필요한 별도 경로만 `--outDir ${OPAL_E2E_ARTIFACT_DIR}/dist`로 빌드한다. 저장소 공유 `dist/`와 backend의 `../../dist`(`dashboard/backend/main.py:117`)에는 E2E 포트가 bake된 산출물을 쓰지 않는다.

### C.7 오류 분류 경계와 전환 금지

| 분류 | 판정 주체 | 다음 후보 전환 |
|---|---|---|
| `provider_unavailable` | driver 후보가 반환 → `can_try_next_provider`(`e2e_contract.py:269`) | **허용** (유일) |
| `executor_unavailable` | Orchestrator(후보 소진) | 없음 |
| `fail` | assertion·제품 동작 | 없음 |
| `infra_error` | 서버·포트·redaction·driver 실행 오류 | **없음 — 예외 목록 없음** |
| `blocked` | 인증·외부 승인·handoff timeout | 없음 |
| `awaiting_human` | handoff 발행 | resume(전환 아님) |

[MUST] `TASK.md` C-3: "다음 실행 후보로의 전환은 `provider_unavailable`에만 허용하고, 제품 실패·assertion 실패·인증 실패를 다른 mode 성공으로 덮지 않는다."

[MUST] `infra_error`에서 다음 후보로의 전환은 **전면 금지**하며 예외 목록을 두지 않는다(`TRD.md` TD-13). 근거: `can_try_next_provider()`는 `provider_unavailable`에만 `True`를 반환하고(`e2e_contract.py:269-273`), 예외를 두려면 이 함수를 고쳐야 하는데 그것은 C-1·NR-1이 금지한 계약 재설계다.

진단 목적 재실행은 금지하지 않는다. 단 **별도 run으로 저장**하고 최초 실패를 덮어쓰지 않는다(제안서 §11).

`tested_range` 밖 binary의 호환성 probe 실패도 `infra_error`이며 조용한 fallback 없이 중단한다(제안서 §8.3).

### C.8 인증 표면 — **부재 선언**

[MUST] `~/.opal/skills/opal-pilot-project-loop/references/contract.md` §2.2: "각 표면은 `id`·`resource`·`auth(required|none)`·요청/응답 형태를 선언하며, 인증 표면(로그인) 자체도 표면으로 등재한다."

**이 프로젝트에는 인증 표면이 없다.** 이는 누락이 아니라 부재이며, 아래 실측이 그 근거다.

- Console backend는 로그인·토큰·세션 엔드포인트를 선언하지 않는다. `dashboard/backend/routers/` 7개 라우터의 경로 선언 16건과 `main.py:102-105`의 `GET /health` 1건을 합한 17건이 `surfaces.json`의 `sut-*` 17개 표면과 1:1 대응하며, 그 중 인증 엔드포인트는 0건이다.
- CORS 등록부는 `allow_credentials=False`로 설정되어 있다(`dashboard/backend/main.py:81-87`). 자격 증명 기반 인증을 전제하지 않는 구성이다.
- backend는 `127.0.0.1`에만 바인딩된다(`main.py:142-146`, `console.sh:39`). 외부 노출이 없어 네트워크 경계가 인증을 대신한다.
- CLI·driver-op·executor-op 표면은 로컬 프로세스 호출이므로 인증 개념이 적용되지 않는다.

따라서 `surfaces.json`의 40개 표면 전체가 `auth: "none"`이다. 향후 인증 표면이 생기면 그 로그인 표면 자체를 `auth: "none"`(로그인 요청 자체는 미인증)으로, 보호 대상 표면을 `auth: "required"`로 등재해야 하며 이 계약의 §C.8을 갱신한다.

**보안 경계의 실체**: 인증이 아니라 (a) `127.0.0.1` 바인딩, (b) `allow_credentials=False`, (c) `allow_methods=["GET","POST"]` 제한, (d) path traversal 차단(`dashboard/backend/routers/projects.py:117-118`)이다. 이번 태스크는 이 중 어느 것도 완화하지 않는다.

### C.10 `kind: "cli"` 표면의 profile·executor 매핑 규칙 (PM 확정)

`surfaces.json`의 7개 `cli` 표면(`e2e-run`·`e2e-resume`·`e2e-status`·`e2e-clean`·`console-start`·`console-stop`·`console-status`)에는 대응하는 profile도 executor도 없다. `PROFILES`는 `browser`·`api`·`hybrid`·`collaborative`·`manual` 5종뿐이고(`e2e_contract.py:38`), `EXECUTOR_TYPES`는 `browser`·`api`·`human` 3종뿐이며(`:41`), `_SURFACE_TO_PROFILE`에 `cli` 키가 없다. **`TASK.md` C-1이 이 계약의 재정의를 금지하므로 `cli` profile이나 `cli` executor를 신설하지 않는다.**

대신 아래 규칙으로 기존 5 profile에 매핑한다.

**[MUST] profile은 호출 수단이 아니라 단언 수단이 결정한다.** CLI는 actor의 행위이지 검증되는 공개 계약이 아니다. 제안서 §4.8("요구사항의 공개 표면이 profile을 결정한다")의 직접 적용이다.

| 그 시나리오의 단언이 관찰하는 것 | profile | observed_executors |
|---|---|---|
| SUT의 HTTP 응답·후속 상태 (예: 두 서버의 `GET /health` 생존·연결 실패) | `api` | `["api"]` |
| 사용자에게 보이는 UI 상태 | `browser` | `["browser"]` |
| UI 결과와 backend 상태를 함께 | `hybrid` | `["api","browser"]` |
| 자동화 불가 단계가 포함됨 | `collaborative` / `manual` | `human` 포함 |

- 프로세스 생존·파일 시스템 상태처럼 HTTP가 아닌 관찰도 **그 run이 SUT를 기동해 HTTP로 최종 확인한다면** `api`로 기록한다. SUT를 전혀 띄우지 않는 순수 셸 단위 검사는 애초에 E2E가 아니므로 `scenario-mark` 대상이 아니라 단위 테스트다.
- **[MUST] 편의로 `manual`을 고르지 않는다.** `manual`은 `human` executor를 요구하므로(`EXECUTOR_MATRIX`, `e2e_contract.py:57-66`) 자동 실행 결과에 붙이면 증적이 거짓이 된다.
- 선택한 profile과 그 근거(무엇을 단언했는가)를 `verdict-json`의 assertion `expected`/`actual`에 드러낸다. 워커가 시나리오마다 임의로 고르지 않는다.

**적용 선례**: T02의 `console-*` 3표면은 `console stop` 호출(CLI 행위) 뒤 두 서버의 `GET /health`(200 / 연결 실패)로 생존·종료를 단언하므로 `profile: "api"`·`observed_executors: ["api"]`로 기록했다. 이 절은 그 판단을 계약으로 승격한 것이며, `e2e-*` 4표면(T03·T04·T10 소유)도 같은 규칙을 따른다.

### C.9 `origins` 선언 — 동적 포트 표현 결정

Console FE가 웹 클라이언트이므로 허용 origin을 선언한다([MUST] `contract.md` §2.1: "웹 클라이언트가 존재하는 프로젝트는 허용 origin(개발·운영)을 경계절에 선언한다(`surfaces.json` `origins`) — CORS 결정론 검사의 계약 근거").

```json
"origins": {
  "dev": ["http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:${OPAL_E2E_FRONTEND_PORT}"],
  "prod": []
}
```

**`dev` 앞 2개** — `dashboard/backend/main.py:76-79`의 현행 모듈 상수 `["http://localhost:5173", "http://127.0.0.1:5173"]` 실측값이다. TD-7이 이 기본값을 유지하므로 계약에 그대로 남는다.

**`dev` 3번째 항목의 표기 결정 (워커 결정 + 근거)**: E2E는 포트를 실행 시점에 임대하므로 고정 문자열을 쓸 수 없다. 세 가지 후보를 검토했다.

| 후보 | 채택 여부 | 사유 |
|---|---|---|
| 와일드카드 `http://127.0.0.1:*` | **탈락** | [MUST] `PRD.md` NR-4: "서버의 허용 출처는 검증용 화면 출처만 실행 시점에 추가하고 전체 허용을 도입하지 않는다." `TRD.md` TD-7도 "와일드카드·정규식·전체 허용을 도입하지 않는다"로 명시 금지. 게이트가 이 문자열을 그대로 CORS 설정으로 읽으면 금지된 전체 허용이 된다 |
| dev 항목 생략(런타임 전용) | **탈락** | 생략하면 CORS 결정론 검사가 "E2E origin이 어디서 오는가"를 계약에서 확인할 수 없다. 부재와 누락이 구분되지 않아 §C.8과 같은 명시적 선언 원칙에 어긋난다 |
| **환경 변수 플레이스홀더 `${OPAL_E2E_FRONTEND_PORT}`** | **채택** | 표면의 **형태**(scheme·host 고정, port만 변수)를 계약에 고정하면서, 값의 확정은 런타임으로 미룬다. 변수명이 A.14 환경 변수 계약의 실제 키와 일치하므로 게이트가 "무엇이 이 자리를 채우는지"를 기계적으로 추적할 수 있다 |

**전개 규칙(계약)**: 이 문자열은 CORS 설정에 리터럴로 들어가지 않는다. 하네스가 포트 임대 확정 후 `${OPAL_E2E_FRONTEND_PORT}`를 실제 정수로 치환한 **정확한 origin 문자열 하나**를 만들어 `OPAL_CONSOLE_CORS_ORIGINS`(A.14)로 backend에 주입한다. backend는 정확한 origin 문자열 추가만 지원하며 패턴 매칭을 수행하지 않는다(`TRD.md` TD-7).

**`prod`가 빈 배열인 이유 (부재 선언)**: production/installed는 `VITE_API_BASE_URL` 미설정 → base `""` → **동일 오리진**이다(`TRD.md` TD-6, `TASK.md` C-8). 동일 오리진 요청은 CORS 대상이 아니므로 허용해야 할 cross-origin이 존재하지 않는다. `prod: []`는 "선언 누락"이 아니라 "허용 대상 0건"이라는 확정 선언이다. `dashboard/backend/main.py:119-132`의 SPA 정적 서빙이 이 구성의 실측 근거다.

---

## §D 기계검증절

[MUST] `~/.opal/skills/opal-pilot-project-loop/references/contract.md` §2.2: "기계검증절의 항목은 test-tool의 계약 conformance 테스트로 T4a에서 자동 검증된다. Evaluator는 이 절을 판정하지 않는다."

따라서 이 절에는 **코드로 판정 가능한 항목만** 넣는다. 주관 판단이 필요한 항목은 전부 §E에 있다.

### D.1 표면 인벤토리

기계가독 표면 인벤토리는 같은 폴더의 **`surfaces.json`**이다(`contract.md` §2.2.1 구조 스펙 준수).

- `schema_version`: `"1.0"`
- `origins`: §C.9
- `surfaces[]`: 40건. 각 항목이 `id`·`resource`·`auth`·`request_shape`·`response_shape`·`kind`를 선언한다.

| `kind` | 건수 | 출처 |
|---|---:|---|
| `cli` | 7 | `test-tool e2e {run,resume,status,clean}`(TD-2) + `opal-cli console {start,stop,status}`(TD-5) |
| `driver-op` | 8 | Browser driver 계약 연산(TD-11, 제안서 §7.6) |
| `executor-op` | 8 | API executor 6(제안서 §7.3) + Human handoff/resume 2(제안서 §7.5) |
| `http` | 17 | SUT Console 표면 — `GET /health` + `/api/*` 16 (`dashboard/backend/routers/` 실측) |

이 인벤토리는 커버리지·conformance 게이트가 소비하는 **유일한** 파일이다. 게이트 도구는 OpenAPI(YAML)나 마크다운 표를 파싱하지 않는다(`contract.md` §2.2.1 "게이트 소비 인터페이스(단일·파서 분기 없음)"). 이 프로젝트는 비-API 프로젝트(하네스·CLI)이므로 `surfaces.json`을 직접 작성하는 경로를 택했다(같은 절 "작성 SSOT(조건부 이원화)").

### D.2 결정론 검증 항목

| # | 검증 항목 | 판정 방법 | 계약 근거 |
|---|---|---|---|
| MV-01 | `surfaces.json`이 유효 JSON이고 `schema_version`·`origins`·`surfaces` 3키를 갖는다 | `json.load` 후 키 검사 | `contract.md` §2.2.1 |
| MV-02 | 모든 `surfaces[]` 원소가 6필드(`id`,`resource`,`auth`,`request_shape`,`response_shape`,`kind`)를 갖고 `id`가 유일하다 | 집합 비교 | `contract.md` §2.2 |
| MV-03 | 모든 `auth` 값이 `required`\|`none` enum 안에 있다 | 값 집합 검사 | `contract.md` §2.2 |
| MV-04 | `surfaces.json`의 `kind="http"` 표면 집합이 `dashboard/backend` 실제 라우트 선언과 일치한다(SPA fallback 제외) | FastAPI `app.routes` 추출 후 대조 | §B.5 |
| MV-05 | `run.json`이 A.1 필수 필드를 전부 갖고, `status`∈`FINAL_STATUSES`∪`{null}`, `profile`∈`PROFILES`, `exit_code`==`status_to_exit(status)` | 스키마 검증 + `e2e_contract` 함수 비교 | C-125-1 |
| MV-06 | `journal.json.transitions`가 A.2.1 enum만 쓰고, `to="pass"` 직전에 `evidence_captured`가 있다 | 전이 시퀀스 검사 | A.2.2 |
| MV-07 | `actions.jsonl`의 모든 `action=="wait"` 행이 `wait_kind`∈`{navigation_ready,transport,assertion_condition}`를 갖는다 | 행 단위 검사 | C-DRV-1 |
| MV-08 | `actions.jsonl`의 모든 `executor=="api"` 행이 `request`·`response`·`step_role`을 갖는다 | 행 단위 검사 | A.4 |
| MV-09 | `assertions.json.results[]`의 모든 원소가 `expected`·`actual` **키**를 갖는다(값 null 허용) | 키 존재 검사 | `e2e_contract.py:340` |
| MV-10 | `assertions.json.results[].id` 집합이 시나리오 `assertions[].id` 집합을 포함한다 | 집합 포함 검사 | `e2e_contract.py:284-290` |
| MV-11 | `owned.json`의 모든 배열 키(A.3 7종)가 존재한다(빈 배열 허용) | 키 존재 검사 | A.3 |
| MV-12 | `cleanup.json.leaked[]`에 `kind∈{process_group,lease}`가 있으면 `run.json.status=="infra_error"`이고 `escalated_to_infra_error==true` | 조건부 일치 검사 | A.6.1 |
| MV-13 | lease record가 A.7 필수 필드를 갖고 `attempt`≤5, `role`∈`{backend,frontend}` | 스키마 검증 | A.7 |
| MV-14 | `$OPAL_E2E_ARTIFACT_DIR/probe.json`의 `probes[]` 각 원소가 A.8의 6개 capability 키를 전부 갖고 각 원소가 `available`·`route`·`probed` 3필드를 갖는다 | 키 존재 검사 | A.8 (Q-2/Q-3 미확정 상태에서도 형태는 고정) |
| MV-15 | `probed==false`인 capability는 `available==false`다 | 함의 검사 | 제안서 §7.7 |
| MV-16 | `handoff.json`이 `HANDOFF_REQUIRED_FIELDS` 8필드를 전부 갖고 어느 값도 `None`/`""`/`[]`가 아니다 | `e2e_contract.HANDOFF_REQUIRED_FIELDS` 대조 | `e2e_contract.py:67-76`, `:460-467` |
| MV-17 | `handoff.server_policy`∈`{keep,terminate}` | 값 검사 | A.9 |
| MV-18 | `submission.json.run_id`·`resume_token`이 `handoff.json`과 일치한다 | 값 비교 | `scenario.py:482-528` |
| MV-19 | (a) `lib/e2e/` 소스에 `FINAL_STATUSES`·`OPERATIONAL_STATUSES`·`PROFILES` 값의 **문자열 리터럴**이 등장하지 않는다. (b) exit 정수는 리터럴 유무로 판정하지 않고 — 인덱스·상한·타임아웃과 구분 불가 — **프로세스 종료 인자가 `status_to_exit()` 호출 결과인지**를 AST로 검사한다(`sys.exit`/`SystemExit`/반환 exit 값의 인자 노드가 해당 호출이어야 한다) | (a) grep (b) AST 호출부 검사 | C-125-1, `TRD.md` RK-8 |
| MV-20 | `lib/e2e/` 중 `process.py` 외 모듈에 `sys.platform`·`os.name`·`platform.system()` 분기가 없다 | AST 검사 | `TRD.md` TD-16 |
| MV-21 | `opal/tools/opal-cli/lib/console.sh`와 `scripts/install-mac.sh`에 `pkill -f "dashboard.backend.main:app"`이 **0건**이다 | grep 검사 | `TRD.md` TD-5, RK-1 |
| MV-22 | `$OPAL_HOME/run/console.pid` 문자열이 `opal/tools/test-tool/` 전체에서 **0건**이다 | grep 검사 | §C.1 |
| MV-23 | A.13 PID 레코드가 6필드를 갖고 `app_dir`가 `opal_home + "/dashboard-server"`와 일치한다 | 스키마·경로 비교 | A.13 |
| MV-24 | `dashboard/frontend/src/lib/api.ts`에 `http://127.0.0.1:7823` 리터럴이 없고 `import.meta.env.VITE_API_BASE_URL`을 참조한다 | grep 검사 | `TRD.md` TD-6 |
| MV-25 | `dashboard/frontend/src/vite-env.d.ts`와 `.env.development`가 둘 다 존재한다 | 파일 존재 검사 | `TRD.md` RK-2 (둘 중 하나만 있으면 회귀) |
| MV-26 | backend CORS 미들웨어의 **`allow_origins`에 `"*"`가 없고 `allow_origin_regex`가 설정되지 않으며**, `allow_credentials==False`, `allow_methods==["GET","POST"]`가 유지된다 | 설정 검사 | `TRD.md` TD-7, NR-4 |
| MV-27 | `OPAL_CONSOLE_CORS_ORIGINS`로 주입된 값이 정확한 origin 문자열만 포함하고 `${...}` 플레이스홀더가 남아 있지 않다 | 문자열 검사 | §C.9 전개 규칙 |
| MV-28 | source target run 종료 후 `git status --porcelain`이 실행 전과 동일하다 | diff 검사 | R-6, AC-13 |
| MV-29 | run artifact 경로가 전부 `artifact_root` 하위이며 저장소 경로·`~/.opal` 경로를 포함하지 않는다 | 경로 prefix 검사 | `TRD.md` TD-10, C-5 |
| MV-30 | 증적의 `Authorization`·`Cookie`·`Set-Cookie` 헤더 값이 원문으로 남아 있지 않다(HAR 포함) | 패턴 검사 | C-6, A.12 |
| MV-31 | `redaction_failed==true`인 run은 `status=="infra_error"`이고 해당 원문 artifact가 존재하지 않는다 | 조건부 검사 | C-6 |
| MV-32 | `--opal-home`이 사용자 실제 `~/.opal`과 같은 경로면 `e2e run`이 거부한다 | 경로 동일성 케이스 | §C.5, C-2 |
| MV-33 | `test-tool e2e *`가 반환하는 exit 값이 `{0,6,7,18,19,20}` 밖으로 나가지 않는다 | exit 집합 검사 | NR-1, `TRD.md` §5.1 |
| MV-34 | `e2e run`이 `schema_version != "2.0"` 시나리오를 실행 대상으로 받지 않는다 | 거부 케이스 | C-125-2 |
| MV-35 | assertion 0건 또는 `required_evidence` 누락 run이 어떤 경로로도 `pass`가 되지 않는다 | 부정 케이스 | R-14, AC-6, `e2e_contract.py:330-337`·`:357-366` |
| MV-36 | main 1 + worktree 2 동시 실행에서 backend/frontend 포트·프로세스 그룹이 서로 겹치지 않는다 | 동시 실행 케이스 | R-3, AC-1 |
| MV-37 | E2E 실행 중 `opal-cli console stop`을 실행해도 E2E backend PID가 살아 있고, E2E 종료 후 `127.0.0.1:7823` health가 계속 응답한다 | 양방향 케이스 | R-4, AC-3 |
| MV-38 | `run.json.candidates[]`(A.1.2)에서 `outcome=infra_error`인 원소의 `order`보다 **큰 `order`를 가진 원소가 존재하지 않는다** — 즉 `infra_error` 이후 후보 시도 기록이 0건이다 | `candidates[]` order 검사 | `TRD.md` TD-13, C-3, A.1.2 |
| MV-39 | `user_owned==true`인 자원이 `cleanup.json.released[]`에 없고 `skipped_user_owned[]`에 있다 | 집합 검사 | C-2, R-8 |
| MV-40 | `hybrid` run에서 `observed_executors`에 `browser`가 없으면 `pass`가 되지 않는다 | 부정 케이스 | R-12, AC-8, `e2e_contract.py:311-321` |
| MV-41 | `run.json.candidates[]`에서 `outcome=="selected"`인 원소가 **필요 executor 타입마다 0개 또는 1개**이고(필요 타입 집합은 `EXECUTOR_MATRIX[profile]["required"]`), 필요 타입 중 하나라도 0개이면 `run.json.status == "executor_unavailable"`이다 | 타입별 개수·상호 검사 | A.1.2 [MUST], `e2e_contract.py:269-273` |
| MV-42 | `lib/e2e/drivers/manifest.json`이 `schema_version`과 `drivers.<name>.{minimum_version, tested_range, ci_pin}`를 갖고, 세 버전 값이 semver로 파싱된다 | 키 존재 + semver 파싱 | A.15 [MUST] |

### D.3 게이트 실행 시점

- **T4a(구현 후)**: test-agent가 MV-01~MV-40을 계약 conformance 테스트로 실행한다(`contract.md` §2.2, §5).
- 이 절의 항목은 Evaluator 판정 대상이 아니다.

---

## §E 루브릭절

[MUST] `~/.opal/skills/opal-pilot-project-loop/references/contract.md` §2.3: 루브릭절은 기계로 판정할 수 없는 주관적 품질 기준을 **앵커된 척도**로 명시한다.

SPEC §04 Base 루브릭 6축(계약 완전성·계약 일관성·설계 정합·drift 필요성·컨벤션 정신·아키텍처 적합, Likert 1–5)을 이 프로젝트의 사실에 맞게 앵커링했다. **통과선은 전 축 ≥4**이며, 어느 한 축이라도 3 이하면 해당 산출물은 G 게이트·D6를 통과하지 못한다.

Evaluator는 이 절만으로 판정할 수 있어야 한다. 판정 대상은 **구현 전 명세**(PLAN.md·test-scenario.json·USER_FLOW.md)이며, §D 기계검증절 항목은 판정하지 않는다.

### E.1 계약 완전성 (Contract completeness)

> 판정 질문: 이 명세가 다루는 표면이 §A 스키마·§B 시그니처로 **빠짐없이** 환원되는가.

| 점수 | 앵커 |
|---:|---|
| 1 | 명세가 건드리는 표면 중 `surfaces.json`에 없는 것이 있고, 그 표면의 입출력 형태가 어디에도 정의되지 않았다. 구현자가 형태를 지어내야 한다 |
| 3 | 표면은 `surfaces.json`에 있으나 명세가 그 표면의 **선택 필드·오류 경로·경계값**(빈 배열, `null`, timeout, 재시도 상한)을 다루지 않아 구현 시 판단이 필요하다 |
| 5 | 명세가 다루는 모든 표면이 `surfaces.json`에 등재되어 있고, 각 표면의 정상 경로·오류 경로·경계값이 §A 스키마 필드로 1:1 환원된다. **실측 의존(Q-2/Q-3) 항목도 "값 미확정"으로 명시되고 필드의 존재·타입은 확정되어 있다** |

**증적 요구**: 명세의 각 단계가 `surfaces.json`의 어느 `id`를 관통하는지 추적 가능해야 한다.

### E.2 계약 일관성 (Contract consistency)

> 판정 질문: 명세가 태스크 125 소유 계약과 이 문서의 경계를 **재정의하거나 우회**하지 않는가.

| 점수 | 앵커 |
|---:|---|
| 1 | 명세가 상태 문자열·exit 값·profile 이름을 **자체 정의**하거나, `validate_pass_requirements`를 거치지 않는 판정 경로를 만든다. C-1 위반 |
| 3 | 재정의는 없으나 명세가 `e2e_contract`의 어느 함수를 호출해 그 값을 얻는지 밝히지 않아, 구현이 리터럴로 떨어질 여지를 남긴다(C-125-1 위반 표면 존재) |
| 5 | 명세의 모든 상태·exit·error·profile·executor 값이 §1 표의 소유 지점을 명시적으로 참조하고, 판정은 `build_verdict`/`validate_pass_requirements` 단일 관문을 통과한다. §C.1 무의존 경계와 §C.7 전환 금지가 명세 안에서 유지된다 |

**즉시 감점 사유**(자동 2점 이하): `infra_error`에서 다른 후보로 넘어가는 경로를 명세가 허용한다 / 하네스가 `console.pid`를 읽거나 쓴다 / `scenario.py`·`e2e_contract.py`에 필드·기능을 추가한다.

### E.3 설계 정합 (Design alignment)

> 판정 질문: 명세가 TRD의 TD 결정을 **집행**하는가, 아니면 우회하는가.

| 점수 | 앵커 |
|---:|---|
| 1 | 명세가 TD 결정과 **반대 방향**으로 설계되어 있다. 예: 포트 임대를 `worktree-tool`에 넣는다(TD-3 반대), `installed` target에서 install 스크립트를 호출한다(TD-9 반대), 저장소 내부에 산출물을 쓴다(TD-10 반대) |
| 3 | TD와 충돌하지는 않으나 명세가 어느 TD를 집행하는지 밝히지 않아, 집행 지점 누락(예: `install-mac.sh:1844` 미포함으로 RK-1 미완화)을 검출할 수 없다 |
| 5 | 명세의 각 단계가 TD-1~TD-19 중 어느 것을 집행하는지 명시하고, **한 TD가 여러 집행 지점을 요구하면 전부 포함한다**(`pkill` 2지점, `api.ts`+`vite-env.d.ts`+`.env.development` 3파일 동시 변경). RK-1~RK-8의 완화책이 명세 안에 실재한다 |

**증적 요구**: RK-1(두 `pkill` 지점), RK-2(FE 3파일 동시), RK-6(`wait_kind` 필수 인자)는 명세에 개별 확인 가능한 형태로 존재해야 한다.

### E.4 drift 필요성 (Drift necessity)

> 판정 질문: 명세가 이 CONTRACT의 변경을 요구한다면, 그 변경이 **불가피**한가.

| 점수 | 앵커 |
|---:|---|
| 1 | 명세가 계약 변경을 요구하는데 그 이유가 구현 편의다. 기존 계약으로 동일 결과를 낼 수 있는데도 스키마·시그니처를 바꾸려 한다 |
| 3 | 변경 요구에 근거는 있으나 실측 인용이 없고, `contract.md` §4 오너십 계층 4단계 중 어디에 해당하는지 분류되지 않았다 |
| 5 | 계약 변경을 요구하지 않거나(drift=no), 요구한다면 **실측 근거(`{경로}:{라인}`)를 제시하고 오너십 계층(#1 무변경 / #2 내부 조정 / #3 인터페이스 변경 / #4 외부 노출)을 명시**하며, #3 이상이면 영향 슬라이스를 열거한다 |

**판정 규칙**: Q-2·Q-3·Q-6·Q-7의 실측 결과가 **값**만 확정하는 경우는 drift가 아니다(§0.3). 필드의 존재나 타입을 바꿔야 할 때만 drift다.

### E.5 컨벤션 정신 (Convention spirit)

> 판정 질문: 명세가 프로젝트의 금지사항과 규칙의 **문구가 아니라 의도**를 지키는가.

| 점수 | 앵커 |
|---:|---|
| 1 | 금지사항 직접 위반: `~/.opal/` 직접 편집, 수기 누적 변경이력 절 추가, 어댑터 밖 플랫폼 분기, `state.json` 직접 편집 |
| 3 | 직접 위반은 없으나 우회가 보인다. 예: 플랫폼 분기를 `process.py` 밖에 두면서 "분기가 아니라 설정"으로 부르기, 인용 없는 사실 주장, 사용자 자원을 "정리 대상이 아님"으로만 쓰고 판별 근거를 명시하지 않기 |
| 5 | `.opal/AGENT.md` §금지사항과 `docs/CONVENTIONS.md` §구현 규칙을 의도까지 지킨다. 모든 사실 주장에 `{경로}:{라인}` 또는 `문서명 §섹션` 근거가 있고(`opal/core/references/harness/citation-rules.md`), 플랫폼 분기가 `lib/e2e/process.py` 한 곳에만 있으며, 사용자 소유 자원 판별이 `owned.json`의 `user_owned` 플래그라는 **관측 가능한 근거**로 이뤄진다 |

### E.6 아키텍처 적합 (Architecture fit)

> 판정 질문: 명세가 §C의 소유권 경계 안에 **머무는가**.

| 점수 | 앵커 |
|---:|---|
| 1 | 경계를 무너뜨린다: 신규 독립 도구 신설(TD-1 반대), `test-tool`↔`opal-cli` 런타임 의존 도입, 증적을 `evidence.py` 밖에서 직접 쓰기(redaction 우회) |
| 3 | 경계 안에 있으나 책임 배치가 §C.2 소유 표와 다르다. 예: 포트 임대 로직을 `runtime.py`에 섞기, target 해석을 `orchestrator.py`가 직접 수행하기 — 동작하지만 경계가 흐려진다 |
| 5 | 각 책임이 §C.1 구조도의 지정 모듈에 배치되고, `e2e_contract`·`scenario.py`는 소비만 되며, 증적 쓰기가 `evidence.py` 단일 관문을 통과하고, executor의 소유 자원 범위(§C.3)를 넘지 않는다 |

**즉시 감점 사유**(자동 2점 이하): 새 CLI 도구를 만든다 / driver·executor가 artifact 파일을 직접 쓴다 / 정리가 `owned.json` 대장이 아니라 패턴 매칭으로 이뤄진다.

### E.7 판정 산출 형태

Evaluator는 축별로 `{item, result, reason, suggestion}`을 반환한다(`contract.md` §3). 3 이하 축에는 어느 앵커에 해당하는지와 5로 올리기 위한 최소 변경을 적는다. Evaluator는 이 문서를 직접 수정하지 않는다 — 반영은 PM 소관이다(`contract.md` §3, §4).

---

## §F TD·R 역추적

### F.1 TD → 계약 항목

| TD | 계약 항목 |
|---|---|
| TD-1 | §C.1 무의존 구조도, §C.2 소유 표, B.1.1 "1회 실행" 규칙, E.6 "신규 도구 신설 금지" |
| TD-2 | §B.1.1~B.1.4 CLI 4종, `surfaces.json` `e2e-run`/`e2e-resume`/`e2e-status`/`e2e-clean`, MV-33 |
| TD-3 | §A.7 lease record, C-LEASE-1~3, MV-13, MV-36 |
| TD-4 | §A.1 `run.json` 전 필드, §C.5 target 경계, MV-05 |
| TD-5 | §A.13 PID 레코드, §B.4 console 3서브명령, `surfaces.json` `console-*`, MV-21~MV-23, MV-37 |
| TD-6 | §A.14 `VITE_API_BASE_URL`, MV-24, MV-25 |
| TD-7 | §C.9 origins, §A.14 `OPAL_CONSOLE_CORS_ORIGINS`, MV-26, MV-27 |

> **MV-26 적용 범위 주석(T01 drift #2, PM 반영)**: 검사 대상은 **오리진 축**(`allow_origins`·`allow_origin_regex`)에 한정한다. `allow_headers=["*"]`(`dashboard/backend/main.py:122`)는 T01 이전부터 존재한 헤더 축 설정이며 이번 범위의 변경 대상이 아니다(`main.py:80` "allow_credentials/allow_methods/allow_headers는 변경하지 않는다"). 오리진 검증용 정규식(`main.py:86` `_ORIGIN_PATTERN`)도 CORS 허용 패턴이 아니라 **입력 형식 검사**이므로 금지 대상이 아니다. 축을 구분하지 않으면 이 항목은 어떤 구현으로도 충족 불가다.
| TD-8 | §A.14 환경 변수 계약 전체 |
| TD-9 | §C.5 `installed` 경계, B.1.1 `--opal-home`, MV-32 |
| TD-10 | §C.6 산출물 경계, §A.8 capability↔artifact 매핑, MV-29 |
| TD-11 | §B.2 driver 8연산, C-DRV-1~5, §A.8 probe, §A.15 driver manifest, §A.1.2 candidates, MV-07, MV-14, MV-15 |
| TD-12 | §0.2 범위 밖, C-125-2, §A.8 "별도 `requires` 필드 없음", MV-34 |
| TD-13 | §C.7 전환 금지표, C-API-2 retry 허용 목록, MV-38 |
| TD-14 | §A.12 redaction, §C.2 evidence 단일 관문, MV-30, MV-31 |
| TD-15 | §A.3 `owned.json`, §A.6.1 승격 규칙, §C.3 소유 범위, MV-11, MV-12, MV-39 |
| TD-16 | §C.2 `process.py` 유일 분기, C-LEASE-2, MV-20 |
| TD-17 | §A.4 `step_role`, §C.4 fidelity 경계, C-API-3, MV-08, MV-40 |
| TD-18 | §A.9 `server_policy` enum, §A.10 submission, §B.1.2 resume, C-HUM-2, MV-16~MV-18 |
| TD-19 | 계약 표면 없음 — 문서·설치 정리 작업(§0.2). `real-usage` 정의는 `scenario.py:119` 소유를 §A.1 `fidelity` 행이 참조로 기술 |

### F.2 R/NR → 계약 항목

| ID | 계약 항목 |
|---|---|
| R-1 | §C.5 target 3종, §A.1 `target`/`project_root`/`worktree_root`/`opal_home` |
| R-2 | §A.7 lease record, C-LEASE-2 stale 회수, B.1.4 `--stale` |
| R-3 | C-LEASE-3 strict port, §C.9 동적 origin, MV-36 |
| R-4 | §C.1 무의존, §A.13 PID 레코드, §B.4, MV-21, MV-37 |
| R-5 | §A.1 `run.json` 전 필드, §A.1.1 executors |
| R-6 | §C.6 산출물 경계, §C.5 읽기 전용 git, MV-28, MV-29 |
| R-7 | §B.2 driver 연산, C-DRV-4 (open·act만으로 pass 불가) |
| R-8 | §A.3 `user_owned`, §C.3, MV-39 |
| R-9 | C-DRV-3 후보 순서(standalone 포함), §A.8 probe |
| R-10 | §C.7 분류표, C-DRV-2, A.4 `wait_kind`, MV-07, MV-38 |
| R-11 | C-API-1 mock 금지, §B.3 `act`/`assert` |
| R-12 | §C.4 fidelity 경계, A.4 `step_role`, MV-40 |
| R-13 | §A.9 handoff, §A.10 submission, §B.1.2, C-HUM-2, MV-16~MV-18 |
| R-14 | §A.1 `missing_evidence`/`evidence_complete`, MV-35 |
| R-15 | §A.2 journal, §A.4 actions, §A.5 assertions, §A.6 cleanup, §B.4 console status |
| R-16 | §A.12 redaction, §A.3 `browser_profiles`, MV-30, MV-31 |
| R-17 | 계약 표면 없음(TD-19) |
| R-18 | 계약 표면 없음(TD-19) |
| R-19 | §A.1 `fidelity` 행이 `scenario.py:119` 소유를 참조 — 정의를 복제하지 않음 |
| NR-1 | §1 전제 계약 전체, C-125-1, MV-19, MV-33 |
| NR-2 | 계약 순서 제약 없음 — D5 백로그 순서로 집행 |
| NR-3 | §C.2 플랫폼 분기, 본 문서에 변경이력 절 미작성, MV-20 |
| NR-4 | §C.9 origins, §A.14 env, MV-26, MV-27 |
| NR-5 | §C.6, MV-29 |
| NR-6 | §B.2 driver 후보 계약, §C.2 `process.py` 단일 분기 |
| NR-7 | C-DRV-2, §A.8 probe 단독 소비 |

---

## §G 실측 의존 항목 (형태 확정 · 값 미확정)

| # | 미확정 값 | 확정된 형태 | 해소 시점 |
|---|---|---|---|
| Q-2 | Orca 관리 세션에 실행 범위 격리 설정을 적용할 수 있는지 | §A.8 `capabilities.isolated_profile.{available, route, probed}` — 키와 3필드는 확정. 미확인이면 `{false,"exec",false}` | E3 비파괴 probe |
| Q-3 | `console`·`errors`·`network_har`의 수집 가능 실행 경로 | §A.8 세 capability 키 + A.8 artifact 매핑 표 — 키·경로명은 확정. `available`·`route` 값만 미확정 | E3 probe |
| Q-6 | opt-in Playwright driver 유지 기간 | `surfaces.json`의 driver-op 표면은 driver 중립이다 — Playwright 제거 여부가 표면 목록을 바꾸지 않는다 | E6 |
| Q-7 | 과거 도구 우선순위 결정 기록(`.opal/brain/pages/concept/e2e-cmux-first-playwright-fallback.md`) 대체 시점 | 계약 표면 없음. C-DRV-3 후보 순서가 현행 결정을 소유 | E4 완료 후 |

[MUST] 설계는 이들이 미확정인 상태에서도 성립한다. capability 미확인은 `available=false`로 보수 판정되어 해당 시나리오가 실행되지 않을 뿐, 다른 경로의 판정을 바꾸지 않는다(`TRD.md` §9).
