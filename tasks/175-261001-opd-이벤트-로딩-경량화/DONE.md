# DONE: 이벤트 로딩 경량화 1차

## 결과

이벤트 응답의 중복 본문을 없애고, `worker.dispatch`는 대상 에이전트에 필요한 본문만 전달하도록 바꿨다. 검증은 실제 대상·역할·디스패치 식별자·반환 본문·선택된 에이전트 문서에 연결된다. 시나리오 17건이 모두 통과했고(RED 9건 포함), 컨벤션 검사는 위반 0건, 보안 검사는 차단 지적 없음(`PASS_WITH_ADVISORIES`)으로 끝났다.

**달라진 것**

- **응답 중복 제거(AC-1).** 모든 이벤트 load 응답이 `response_version: 2`를 갖고 본문은 `documents[].content`에 한 번만 담긴다. `required_documents`·`optional_documents`는 `id`·`token`·`path`·`sha256`·`bytes` 메타데이터만 담는다. 실측(설치본): `session.assistant` 응답 26,912 → 14,730바이트, `pm.activate` 148,614 → 76,229바이트(문서 본문 합계는 같음).
- **대상별 디스패치(AC-2).** `worker.dispatch`는 코드 펜스 바깥 헤딩만 절 경계로 보고 대상 에이전트 항목 1종만 보낸다. 플랫폼 어댑터 규칙·매핑 테이블·폴백·탐색 경로는 전문을 유지한다. `에이전트 추가 가이드`·`향후 추가 에이전트`는 제외한다. 담당을 배정하는 역할(`opal-plan-agent`)과 하위 디스패치 3종은 항목 전체를 받는다. 일반 대상 본문 합계 46,244 → 32,499~32,697바이트(약 29% 감소), 응답 바이트 98,203 → 약 39.6K.
- **새 호출 계약(AC-3).** PM·워커 진입·하위 디스패치 모두 `--contract-version 2 --agent --role --dispatch-id`(`--role-doc` 선택)로 load·verify한다. 대상·역할·식별자 불일치, 반환 본문 변조, 에이전트 문서의 경로·해시·출처(프로젝트↔프레임워크) 변경, 필수 인자 누락과 형식 위반을 거부한다. 계약 인자를 `contract` 선언이 없는 이벤트에 주면 `contract_not_declared`, receipt가 다른 매니페스트를 가리키면 `stale_receipt`로 거부한다.
- **버전·호환(AC-4).** 매니페스트의 `worker.dispatch.contract`(`current`·`supported`·`legacy_accepted`)가 계약 버전과 호환 종료를 소유한다. 인자 없는 구형 호출은 전환 기간 동안 전체 전송 + `legacy_dispatch_contract` 경고 + 구형 검증 표시로 통과하며 `legacy-dispatch.jsonl` 원장에 기록된다. 새 계약 요청은 구형으로 자동 전환되지 않는다. 지원하지 않는 버전은 `unsupported_contract_version`, `legacy_accepted: false`에서는 `legacy_dispatch_rejected`·`legacy_receipt_rejected`다.
- **측정(AC-5).** `measure`가 `payload_bytes`·`source_payload_bytes`·`response_bytes`를 따로 출력하고 `load-report`가 `load_id`로 중복을 제거해 합산한다(재검증 미합산). 비용·시간은 로더가 만들지 않고 `MEASURE.md`의 별도 열에 둔다.
- **소비자 갱신.** `state-tool event-verify`가 다섯 인자를 그대로 전달한다. 에이전트 16종의 진입 게이트와 하위 디스패치 3종의 `load`·`verify` 줄을 새 계약으로 바꿨다. 게이트 성공 조건은 `ok: true`, `contract == 2`, `dispatch_id`·`agent.name`·`role` 일치다. `dispatch-process.md`는 대상·역할 확정(Step 1~4) 뒤 Step 0 게이트를 수행하는 순서로 바꿨다. `static-check`가 구형 호출(`dispatch_contract_args_missing`)과 게이트의 에이전트 이름 불일치(`dispatch_gate_agent_mismatch`)를 찾는다. `agent-index` 서브명령이 대상 선택용 가벼운 목록을 낸다.

**유지한 것:** 이벤트별 필수 문서 집합(`events.json`이 SSOT), 다른 이벤트의 receipt `schema_version: 1`, 구형 호출의 전체 전송, `session.*`·`pm.activate`·`stage.*`의 필수 규칙 전문.

**제외한 범위:** P2(조건부 문서 분리)·P3(지연 절 로딩)는 하지 않았다. 호환 종료(구형 거부 전환)는 이번에 켜지 않았다.

## 변경 파일

- `opal/agents/*/AGENT.md` (16종)
- `opal/core/references/agents.md`
- `opal/core/references/events.json`
- `opal/core/references/opal-pm.md`
- `opal/core/references/pm/dispatch-process.md`
- `opal/skills/opal-pilot-dev2/SKILL.md`
- `opal/tools/event-loader/README.md`
- `opal/tools/event-loader/agent_sections.py`
- `opal/tools/event-loader/event_loader.py`
- `opal/tools/event-loader/tests/conftest.py`
- `opal/tools/event-loader/tests/test_event_loader_agent_sections.py`
- `opal/tools/event-loader/tests/test_event_loader_dispatch_contract.py`
- `opal/tools/event-loader/tests/test_event_loader_extended.py`
- `opal/tools/event-loader/tests/test_event_loader_static_and_index.py`
- `opal/tools/opal-agent/README.md`
- `opal/tools/state-tool/state_tool_parts/cli.py`
- `opal/tools/state-tool/state_tool_parts/gates.py`
- `opal/tools/state-tool/tests/test_event_verify.py`

## 검증

- 시나리오: `test-scenario.json` 17/17 PASS (RED 대상 S-1~S-9 확인·잠금). S-17(opst `smoke-version-flag`, `//opds`)은 변경 후 1회 PASS(숨은 테스트 2건, 16.0분, $9.03)이며 변경 전 기록이 없어 동등성은 입증하지 못했다.
- 회귀: `pytest opal/tools/event-loader/tests opal/tools/state-tool/tests` — 762 passed, 4 failed(전부 변경 전 HEAD에서도 같은 실패: `test_static_check_ok`의 `opal-pilot-dev2/SKILL.md` 기존 위반, `test_project_brief_cli_preserves_inputs_and_multitask_counts`, 세션 환경 테스트 2건). 보안 수정 이후 event-loader·state-tool 관련 묶음 108 passed(같은 기존 실패 2건 제외).
- 정적 검사: `static-check --manifest-only` 위반 0건, `--event worker.dispatch` 위반 0건. 저장소 전체는 기존 `event_contract_missing` 3건(`opal-pilot-dev2/SKILL.md`)만 남음.
- 컨벤션: 최종 검사 Critical 0·High 0·전체 0건. 커밋 전이라 변경 구간 검사는 하지 못했고 `@header`·컴파일 중심으로 확인했다.
- 보안: 최초 검사 FAIL(GC-001 high, GC-002 medium) → 수정 → 재검사 FAIL(GC-008 medium) → 수정 → 최종 `PASS_WITH_ADVISORIES`(차단 0건, low 4건).
- 설치: `scripts/install-mac.sh` 메뉴 [1]로 설치(최초 2026-10-01T14:28Z, 최종 재설치 2026-10-01T15:17Z). 설치 직후 설치본 `event-loader`·`state-tool`이 소스와 동일하고 `session.assistant`·`pm.activate`·`stage.plan` load가 성공함을 확인했다. 설치 전 백업은 `/private/tmp/claude-501/.../scratchpad/opal-backup/`(세션 임시 영역)에 있다. 단, CLOSE 직전인 2026-10-02 00:28(KST) 허브의 다른 세션이 `main` 기준으로 재설치해 현재 설치본은 `main`과 동일하며 이 태스크의 변경(contract v2, `agent_sections.py`)을 포함하지 않는다. merge 후 install 재실행이 필요하다.
- 측정표: `MEASURE.md`.

## 회고적 학습 후보

.opal/brain/pages/concept/event-response-single-body.md
.opal/brain/pages/concept/worker-dispatch-target-section-selection.md
.opal/brain/pages/concept/worker-dispatch-contract-v2-binding.md
.opal/brain/pages/concept/legacy-dispatch-compat-sunset-observation.md
.opal/brain/pages/entity/agent-sections.md

## 참고

**호환 종료 판정(후속 운영 조치).** 전환 기준 시점은 원장 오염을 막은 최종 설치 시각 `2026-10-01T15:17:22Z`다. 호환 종료는 `legacy-report --since 2026-10-01T15:17:22Z` 건수 0이 연속 168시간 이어지고, `static-check` 구형 호출 0건, 직접·하위 검증 시나리오 통과를 확인한 뒤 `events.json`의 `contract.legacy_accepted`를 `false`로 바꾼다. 설치본 원장 `~/.opal/state/event-loader/legacy-dispatch.jsonl`의 처음 6줄(14:29:01Z~15:11:34Z)은 시험(S-14 구형 확인 2줄, 직접 확인 1줄)과 `conftest.py` 도입 전 테스트 실행이 남긴 것이라 판정에서 제외한다.

**알려진 한계·후속 후보 (보안 advisory).**

- GC-004: `--role-doc`이 임의 파일 경로를 받아 존재·해시를 receipt에 남긴다(내용은 노출 안 됨).
- GC-006: `OPAL_EVENT_LOADER_LEDGER`·`OPAL_EVENT_LOADER_NOW` 환경변수로 원장 경로·시각을 바꿀 수 있어 호환 종료 판정이 과소 집계될 수 있다.
- GC-011: `events.json`이 심볼릭 링크이면 기본 매니페스트 경로를 `resolve()`하지 않아 정당한 receipt가 거부된다(현재 설치는 일반 파일).
- GC-012: `OPAL_DEPLOYED_ROOT`·`--deployed-root`·`--source-root`·`--manifest`를 제어하는 쪽이 검증 경계 매니페스트를 정할 수 있다(같은 사용자 권한 전제). 게이트 성공 조건에 결과의 `manifest_path` 확인을 더하는 방안이 있다.

**기존 이슈(이번 변경과 무관).** `opal/skills/opal-pilot-dev2/SKILL.md`의 `stage.analysis`·`stage.test_scenario`·`stage.close` 이벤트 계약 누락 3건, `test_project_brief_cli_preserves_inputs_and_multitask_counts` 실패, `--path opal/agents`로 훑을 때 personas 파일 6건의 `event_contract_missing`.

**설계 대비 차이.** PLAN D-6의 에이전트 항목 판정 정규식(`-(agent|checker)`)과 달리 구현은 `opal-`로 시작하는 H3를 에이전트 항목으로 본다. 실제 `agents.md`에서 차이는 `### opal-task-qa-agent (역할 한정 …)` 한 건뿐이며 구현이 더 관대하게 동작한다.

**제안서 처리.** `docs/proposals/opal-event-loading-economy.md`는 2차(P2)·P3가 남아 있어 아카이브하지 않는다. 후속 태스크 종료 때 판정한다. 1차 결정(D-1·D-2~D-12)의 WHY는 위 회고적 학습 후보 5건으로 brain에 반영했고, P2·P3 결정은 후속 태스크의 ingest가 보탠다.
