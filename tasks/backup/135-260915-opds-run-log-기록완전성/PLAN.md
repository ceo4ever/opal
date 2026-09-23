---
template: sdlc-v2
---
# PLAN: run-log 기록 완전성

> 입력: [TASK.md](TASK.md)

## Approach

기존 run-log 코어의 폐쇄형 사건 스키마와 append-only 저장 계약은 유지하고, 누락의 원인인 생산 경로를 보강한다. 핵심 변경은 `state-tool`이 한 번의 명령에서 발생한 관측 가능한 사건을 단일 `state.changed`로 축약하지 않고, 자동 승인·대상 상태 변경·PM activity·gate 사건을 각각 표준 사건으로 outbox에 적재하게 만드는 것이다. 그 다음 `state.json`과 JSONL을 대조하는 완전성 검증을 추가해, 구조 검증은 통과하지만 의미 사건이 빠진 상태를 실패로 드러낸다.

code-scan 근거: `code-scan scan opal/tools/run-log-tool opal/tools/state-tool`에서 `run_log_core.py`는 event vocabulary, schema/provenance validation, append/validate/import를 소유하고 `state_tool.py`는 `run_log_commit`, `build_state_changed_event`, `auto_approve_prior_user_confirmations`, `run_log_diagnose`, completion profile 경계를 소유하는 것으로 확인했다. `rg`로 확인한 직접 표면은 `opal/tools/state-tool/state_tool.py:844`, `opal/tools/state-tool/state_tool.py:898`, `opal/tools/state-tool/state_tool.py:1548`, `opal/tools/run-log-tool/run_log_core.py:68`, `opal/tools/run-log-tool/run_log_core.py:789`, `opal/tools/run-log-tool/run_log_core.py:801`이다.

[MUST] `docs/CONVENTIONS.md` §Guards: "사용자가 명시적으로 \"승인\", \"진행해\", \"구현해\" 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다." 이 PLAN 뒤에도 실행 승인이 오기 전까지 구현 파일은 변경하지 않는다.

[MUST] `docs/run-log/CONTRACT.md` §1.2: "`activity` | worker / PM"와 "`gate.requested` | PM", "`gate.resolved` | PM / user / auto"가 표준 사건 enum에 이미 들어 있다. 이번 변경은 새 사건 종류를 늘리지 않고 기존 enum의 생산 보장을 회복한다.

[MUST] `opal/core/PRINCIPLES.md` §Core Stance: "Platform-independent: keep Claude/Cursor/Gemini branches in adapters, never in logic." shadow/active 차이를 플랫폼별 분기로 넣지 않고 mode와 provenance 계약으로만 처리한다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. shadow/active의 사건 인벤토리는 동일하게 유지 | `mode`는 기록할 사건 종류를 줄이지 않는다. `run.started`, `state.changed`, `activity`, `worker.*`, `gate.*`, `run.completed`의 관측 가능 사건은 두 모드 모두 같은 표준 payload를 사용한다. 차이는 shadow의 비차단 진단과 active의 완료 게이트 기여 여부뿐이다 | TASK AC-1. `docs/run-log/CONTRACT.md` §1.2는 사건 enum을 mode별로 분리하지 않고, §1.5만 완료 판정 등급과 active gate를 분리한다 |
| D-2. PM 의사결정은 `activity`로 기록하되 raw prompt와 내부 사고는 금지 | PM decision/validation/retry/progress는 `actor.kind=PM`, `provenance.type=direct`, `data.kind ∈ {decision, validation, retry, progress}`, `summary`, `reason`, `refs`를 갖는다. `reason`은 감사 가능한 사유 요약이며 원본 프롬프트·chain-of-thought·비밀값은 어떤 필드에도 저장하지 않는다 | TASK AC-2, C-3. CONTRACT §1.2 `activity`와 §1.3 A4가 PM direct 조합을 허용한다 |
| D-3. 복합 상태 전이는 사건 목록으로 커밋 | `run_log_commit()`은 단일 event 인자를 하위호환 유지하면서 내부적으로 event list를 받는다. `advance`/`mark`가 자동 승인한 각 사용자 확인 행과 대상 행 전이를 모두 별도 `state.changed`로 만들고, 같은 상태 원자 쓰기 안에서 pending_events에 함께 적재한다 | TASK AC-3, C-4. 현재 `auto_approve_prior_user_confirmations()`는 여러 row를 in-place 변경하지만 `run_log_commit()` 호출은 대상 행 `state.changed` 1건만 만든다 |
| D-4. 선언만 있고 미구현인 gate 표면을 신규 구현해 드리프트를 닫는다 | `docs/run-log/surfaces.json`이 선언한 `state-tool.gate-request`·`state-tool.gate-resolve`를 구현 계약으로 삼되, **두 서브커맨드는 현재 `state_tool.py`에 존재하지 않으므로 신규 구현이다**(실측: `add_parser("gate-request"\|"gate-resolve")` 0건. 유사 이름 `event-verify`는 receipt 검증용 별개 기능). PM 요청은 `gate.requested`, 사용자/auto/PM 해결은 `gate.resolved`를 같은 outbox/admission/drain 경로로 기록한다. 요청 없는 resolved와 중복 resolved는 active/shadow 모두 계약 위반으로 진단한다 | TASK AC-4. surfaces.json이 공개 CLI 표면을 선언했으나 구현이 따라오지 않은 문서→구현 드리프트이며, CONTRACT §1.2는 gate_id 필수와 requested 선행을 요구한다 |
| D-5. shadow의 누락은 비차단 진단, active의 누락은 기존 완료 거부 | shadow에서는 기록 실패·관측 불가·state/log 불일치를 `warnings` 또는 verify 진단으로 드러내되 상태 전이 완료 여부를 뒤집지 않는다. active에서는 선택된 `completion_profile`이 요구하는 trusted worker/gate/state 증거가 부족하거나 모순되면 기존 completion gate가 거부한다 | TASK AC-5, AC-6, C-1, C-2. CONTRACT §1.5는 shadow와 active의 completion profile 허용·게이트 차이를 이미 분리한다 |
| D-6. run-log 구조 검증과 상태 대조 검증을 분리하고, 관측 중단 지점을 구조화 필드로 반환 | `run-log-tool validate-run`은 조각 자체의 순번·스키마·provenance 검증을 유지한다. `state-tool verify --run-log-completeness-check`는 `state.json` 현재 행과 run-log의 `state.changed`/gate/activity 사건을 대조해 자동 승인 포함 누락을 탐지하고, 누락 4종과 함께 `last_observed_decision`·`last_observed_state_change`·`last_observed_boundary` 3필드(각 `event_id`·`ts`·`row_key`\|`gate_id`\|`worker_run_id`, 부재 시 `null`)를 반환해 AC-7을 사람 판단이 아닌 결정론 조회로 판정한다 | TASK AC-7, AC-8. `run-log-core`는 상태 파일을 읽지 않는다는 TRD D-5 단방향 계약 때문에 상태 대조는 state-tool 소유여야 한다 |
| D-7. 문서 개정은 책임 경계와 표면 드리프트만 보강하되, 의미 계약 조문은 RED보다 먼저 확정 | `docs/run-log/CONTRACT.md`는 mode별 기록 인벤토리 동일성 및 PM activity/gate payload 계약을, `TRD.md`는 생산 경로와 state/log 대조 책임을, `PRD.md`는 단일 이력 원천 목표의 보강 설명만 소유한다. `surfaces.json`은 이미 선언된 `state-tool.log-event`, `state-tool.gate-request`, `state-tool.gate-resolve`와 실제 구현의 일치 검증 및 필요 최소 정정만 소유한다. **단 D-1·D-2의 의미 계약 조문(mode별 인벤토리 동일성, PM activity 허용 필드 화이트리스트)은 RED가 무엇을 고정하는지의 판정 원천이므로 W-0에서 먼저 확정한다** — 이는 surfaces.json 신규 표면 추가와 무관하며, 나머지 문서 정합화는 구현 완료 뒤(W-5)에만 수행한다 | TASK C-7. `docs/PROJECT.md` 레지스트리가 CONTRACT를 "구현 전 명세 심판의 판정 기준 원천"으로 규정한다. PRD/TRD/CONTRACT frontmatter가 각각 무엇/어떻게/인터페이스 경계를 선언하고, surfaces.json은 공개 CLI 표면 목록을 소유한다 |
| D-8. 외부 재현 로그는 fixture로만 사용 | opal-studio의 실제 JSONL은 원인 재현 근거로 참조하되, 테스트는 저장소 내부 임시 fixture와 공개 CLI 실호출로 재현한다. 외부 프로젝트 파일을 수정하거나 소급 변환하지 않는다 | TASK 제외 범위와 C-6. 기존 태스크 로그 일괄 변환은 범위 밖이다 |

폐기한 대안: `shadow`에서만 activity를 더 많이 남기고 `active`에서 adapter 사건만 믿는 방식은 기각한다. 이 방식은 기록 인벤토리와 완료 신뢰도를 섞어 AC-1을 깨고, 사용자가 요구한 "무조건 기록" 계약을 모드별 선택 사항으로 만든다.

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-0. D-1·D-2 의미 계약 조문 확정 | `opal-task-agent` | `docs/run-log/CONTRACT.md` | D-1의 "mode는 기록할 사건 종류를 줄이지 않는다" 조문과 D-2의 PM `activity` 허용 필드 화이트리스트(`actor.kind=PM`·`provenance.type=direct`·`data.kind` 4종·`summary`·`reason`·`refs`만 허용, 그 외 필드·원문·chain-of-thought·비밀값 금지)를 CONTRACT §1.2/§1.3에 확정한다. 신규 event enum과 신규 CLI 표면은 추가하지 않는다. 나머지 문서 정합화는 W-5가 소유한다 | 없음 | P0 | AC-1, AC-2, C-3, C-7 |
| W-1. RED 완전성 계약 고정 | `opal-test-agent` (red mode; 구현 워커와 다른 인스턴스) | `opal/tools/state-tool/tests/test_state_tool_run_log.py`, `opal/tools/run-log-tool/tests/test_run_log_tool.py`, `scripts/tests/` | 공개 CLI와 실제 파일 I/O만 사용해 ① 자동 승인 2건+대상 전이 1건이 각각 `state.changed`로 남는 시나리오, ② 기존 `state-tool.log-event` 표면의 PM decision/validation/retry activity, ③ 기존 `state-tool.gate-request`/`state-tool.gate-resolve` 표면의 requested/resolved 쌍과 요청 없는 resolved 거부, ④ shadow 누락 진단 비차단, ⑤ active completion profile 증거 부족 거부, ⑥ opal-studio 재현형 "TASK 보고 후 중단" fixture에서 `last_observed_decision`·`last_observed_state_change`·`last_observed_boundary` 3필드 반환을 RED로 고정한다. mock/patch/MagicMock은 쓰지 않는다. **각 RED 케이스에는 이를 GREEN으로 만드는 work item 번호(①→W-2, ②③→W-3, ④⑤⑥→W-4)를 주석으로 태깅해, 중간 단계의 잔여 실패가 미구현인지 회귀인지 구분되게 한다** | W-0 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-4, C-6 |
| W-2. 복합 state.changed 생산 경로 구현 | `opal-task-agent` | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/tests/test_state_tool_run_log.py` | `run_log_commit()`을 event list admission/drain으로 확장하되 단일 event 호출은 유지한다. `advance`/`mark`에서 `auto_approve_prior_user_confirmations()`가 반환한 row마다 `from`/`to`/`row_key`/`note`를 담은 `state.changed`를 만들고 대상 행 전이와 같은 상태 원자 쓰기에 적재한다. 1.0/1.1 또는 run_log 블록 없는 태스크의 save/응답 경로는 바꾸지 않는다. `state_tool.py` @header의 단일 state.changed 서술을 현재 계약으로 갱신한다 | W-1 | P2 | AC-3, AC-8, C-1, C-4, C-5, C-6 |
| W-3. 선언·미구현 상태인 PM activity와 gate 표면 신규 구현 | `opal-task-agent` | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/tests/test_state_tool_run_log.py`, `opal/tools/run-log-tool/tests/test_run_log_tool.py`, `docs/run-log/surfaces.json` (검증/필요 최소 정정) | surfaces.json이 선언했으나 `state_tool.py`에 서브커맨드가 없는(실측 `add_parser` 0건) `state-tool.log-event`·`state-tool.gate-request`·`state-tool.gate-resolve` **3종을 신규 구현한다 — 기존 코드 연결이 아니라 CLI 파서·핸들러·응답 계약을 새로 만드는 작업이다.** PM direct `activity` builder와 gate requested/resolved builder를 구현하고 같은 outbox 경로로 기록한다. 허용 필드는 W-0이 CONTRACT에 확정한 화이트리스트만 수용하고 그 외 키는 거부한다. `summary`·`reason`·`refs`는 CONTRACT §1.1의 "`refs`: 프로젝트 상대 경로만. 절대 경로·원문 금지"와 surfaces.json의 `--refs <path>...` 표면에 맞춰 task/project 상대 참조로 정규화하거나 계약상 허용 형식만 수용한다. 외부 재현 JSONL의 절대경로는 raw log에 그대로 저장하지 않는다. `gate_id` 선행 관계와 중복 resolved를 검증한다. `activity.data.kind`는 기존 4종 enum만 사용하고 새 event enum은 추가하지 않는다 | W-2 | P3 | AC-1, AC-2, AC-4, C-3, C-4, C-5, C-7 |
| W-4. 완전성 진단과 mode별 enforcement 정리 | `opal-task-agent` | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/tests/test_state_tool_run_log.py`, `opal/tools/run-log-tool/run_log_core.py`, `opal/tools/run-log-tool/tests/test_run_log_tool.py` | `state-tool verify --run-log-completeness-check`를 추가해 `state.json`의 완료 행·자동 승인 행·게이트 상태와 JSONL 사건을 대조한다. shadow는 누락 목록(`missing_state_changed`, `missing_pm_activity`, `missing_gate_event`, `unobserved_worker_boundary`)을 진단으로 반환하고 완료 상태는 뒤집지 않는다. **누락 목록과 함께 `last_observed_decision`·`last_observed_state_change`·`last_observed_boundary` 3필드를 항상 반환한다**(각 `{event_id, ts, ref}`, 해당 사건이 없으면 `null`) — AC-7의 "마지막 의사결정·마지막 상태 전이·관측 중단 지점" 구분을 사람 판독이 아니라 이 필드 조회로 판정한다. active는 기존 `validate-worker`/completion profile 결과를 약화하지 않고 부족·모순 증거를 완료 거부로 연결한다. `run-log-tool validate-run`은 상태 파일을 읽지 않는 구조 검증으로 유지한다 | W-3 | P4 | AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-5, C-6 |
| W-5. run-log 계약 문서와 표면 정합화 | `opal-task-agent` | `docs/run-log/PRD.md`, `docs/run-log/TRD.md`, `docs/run-log/CONTRACT.md`, `docs/run-log/surfaces.json`, `opal/tools/run-log-tool/README.md`, `opal/tools/state-tool/README.md` | D-3~D-8의 변경 후 계약을 각 문서의 책임 경계에 맞춰 최소 반영한다. **D-1·D-2의 의미 계약 조문은 W-0이 이미 CONTRACT에 확정했으므로 여기서 다시 기재하지 않는다**(H-5 중복 소유 방지). `surfaces.json`에는 신규 표면을 추가하지 않고, 이미 선언된 `state-tool.log-event`·`state-tool.gate-request`·`state-tool.gate-resolve`와 W-3 구현의 request/response/err 집합이 일치하는지 검증하고 드리프트가 있으면 필요 최소 정정만 한다. PRD는 목표 설명, TRD는 생산/진단 흐름, CONTRACT는 필드·enum·명령 표면만 소유하게 하고 같은 문장을 중복 소유시키지 않는다 | W-4 | P5 | AC-1, AC-2, AC-4, AC-5, AC-8, C-7 |
| W-6. 회귀·보안·legacy 검증 | `opal-test-agent` | `opal/tools/state-tool/tests/`, `opal/tools/run-log-tool/tests/`, `scripts/tests/` (실행 전용) | state-tool/run-log-tool 관련 스위트와 새 완전성 검사를 전건 실행한다. append-only, 순번 연속성, 멱등성, 배타 락, 마스킹, 경로 방어, legacy 1.0/1.1 경로가 기존대로 통과하는지 확인한다. 실패가 있으면 FAIL/BLOCKED 증거와 재현 명령을 PM에 반환하며, 테스트 에이전트가 구현 파일을 수정하지 않는다 | W-5 | P6 | AC-8, C-2, C-5, C-6 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. event list 커밋이 원자성을 깨면 state와 JSONL이 더 쉽게 갈라진다 | 상태 변경과 pending_events 적재가 한 번의 원자 쓰기여야 한다 | 자동 승인 누락을 고치려다 일부 사건만 기록되는 새 결함이 생긴다 | D-3. W-2는 여러 사건을 한 pending_events 묶음으로 admission한 뒤 기존 drain을 멱등 재사용한다 |
| H-2. PM activity가 내부 사고나 원문 프롬프트 저장으로 오해될 수 있다 | 감사 가능한 사유 요약과 비저장 정보의 경계 | 민감 정보 저장 또는 불필요한 대화 원문 보존이 발생한다 | D-2. W-3은 summary/reason/refs만 받고 raw prompt와 chain-of-thought 저장을 금지한다. refs는 CONTRACT §1.1의 프로젝트 상대 경로 계약에 맞춰 정규화/수용 여부를 테스트한다 |
| H-3. state/log 대조를 run-log-core에 넣으면 단방향 의존이 깨진다 | run-log-core는 상태 파일을 읽지 않는다 | 기록 도구가 상태 도구에 결합되어 기존 AC-19 계열 회귀가 발생한다 | D-6. 완전성 대조는 state-tool verify가 소유하고 run-log-tool validate-run은 구조 검증으로 둔다 |
| H-4. active 미배포 상태에서 active 완료 게이트를 과확장하면 승인 경계가 흐려진다 | profiles.json 없는 채널의 active 초기화는 `profile_not_found`로 거부된다 | 미승인 active rollout이나 가짜 profile 수용으로 C-2가 깨진다 | D-5. active profile 배정은 만들지 않고, 기존 거부와 completion evidence 검증을 약화하지 않는 테스트만 추가한다 |
| H-5. 문서가 같은 규칙을 중복 소유하면 다음 태스크에서 다시 드리프트가 생긴다 | PRD/TRD/CONTRACT 책임 경계 | mode 계약이 문서마다 다르게 갱신되어 구현자가 어느 문서를 따라야 할지 모호해진다 | D-7. W-5는 각 문서의 owner 역할별로 최소 문장만 추가하고 surfaces는 공개 CLI 표면만 소유한다 |

## Release and recovery

- 적용 순서: P0 D-1·D-2 CONTRACT 조문 확정 → P1 RED 계약 → P2 복합 `state.changed` → P3 PM activity/gate 표면 신규 구현 → P4 완전성 진단과 enforcement → P5 나머지 문서·표면 정합화 → P6 회귀 검증. 같은 실행 그룹 안의 구현 작업은 없으므로 파일 충돌 없이 직렬 진행한다.
- 검증 범위: 결정론 검증은 event list admission/drain, 자동 승인 row별 `state.changed`, PM activity payload, gate 선행 관계, state/log 완전성 대조를 포함한다. 회귀 검증은 기존 state-tool/run-log-tool 스위트, legacy 1.0/1.1 경로, append-only·순번·멱등·락·마스킹·경로 방어를 포함한다. 실제 연동은 opal-studio 재현형 fixture와 신규 임시 태스크 CLI 실호출로 판정한다.
- 실측 경계: shadow 누락은 exit 0과 진단 payload가 함께 있는지로 판정하고, active 누락은 기존 profile/evidence gate가 exit 1로 거부하는지로 판정한다. 두 결과를 같은 테스트에서 분리해 "기록 범위 동일, enforcement만 다름"을 확인한다.
- 실패 시: 배포·install은 수행하지 않으므로 복구는 저장소 소스 변경을 역순으로 되돌리는 것으로 끝난다. 단 문서 정합화(W-5)는 공개 CLI가 실제로 구현된 뒤에만 반영하며, 구현이 막히면 문서를 먼저 넓히지 않고 blocker로 반환한다.
