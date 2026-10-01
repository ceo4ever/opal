---
type: concept
title: opd2 state-tool 통합
tags:
- opd2
- state-tool
- gate-guard
- ssot
- task-168
sources:
- task:168
related: [state-tool]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

자체 상태 관리 Pilot이었던 opd2(`opal-pilot-dev2`)가 `state-tool`의 `state.json` 단일 SSOT로 편입됐다. opd2는 자신의 기계 게이트(아티팩트 결합 해시 체인·계획 파일 범위·실행 증거·역할 분리·재작업 상한)를 그대로 유지하면서, 판정 결과를 매 전이마다 `state-tool mark`로 커밋하도록 바뀌었고, 그 게이트는 lifecycle 엔진을 우회해 `state-tool mark --force`를 직접 호출해도 뚫리지 않는다.

## 결정 배경 (WHY)

opd2는 원래 태스크별 자체 journal(`.sdlc/events.jsonl`, sdlc 버전 `state.json`/`STATE.md`/`AGENTIC-LOG.md`)로 단계 상태를 관리하는 독립 생명주기 엔진이었다. 이 구조는 FW 공통 계약과 실행 안전장치에 연결되지 않아 다음 문제가 있었다(근거: `opal/tools/state-tool/tests/test_pilot_shared_contract.py` 실패 5건, 태스크 TASK.md Problem).

- FW 공통 Pilot 계약 테스트가 opd2 때문에 실패했다 — `references/pipeline.json` 없음, `opal-skills-registry.json` 미등재, `state-tool spec-validate` 실패.
- 레지스트리에 없어 `//opd2`로 호출할 수 없었다.
- 세션 종료를 막는 Stop 판정과 태스크 lease 확보가 모두 `<task>/state.json`만 읽는데(`opal/tools/ownership-tool/ownership_tool/resolver.py:107-108`), opd2의 자체 상태 도구는 그 파일을 쓰지 않아 종료 차단·재개 안내·lease 보호를 받지 못했다.
- `pilot.start`·`stage.*`·`worker.dispatch` 이벤트 게이트가 없었고, Builder/Verifier/Reviewer가 등록된 FW 워커가 아닌 스킬 내부 문서로만 호출됐다.

소유자가 선택한 방향은 "기존 게이트 판정 로직은 그대로 두고 영속 위치만 FW SSOT로 옮긴다"였다(근거: 태스크 PLAN.md Approach·Decisions "상태 SSOT는 state-tool(A안)"). 판정 로직 자체를 재구현하면 이미 검증된 아티팩트 해시·범위·역할 분리 로직을 다시 증명해야 하는 부담이 생기기 때문이다.

## 결정 내용

- **SSOT 이전**: opd2 태스크의 단계 상태는 `state-tool`이 관리하는 태스크 루트 `state.json` 한 곳에만 존재한다. `.sdlc/` journal·projection은 더 이상 생성하지 않는다. 원장(아티팩트 결합 해시·evidence·approvals·reviews·baseline·retries)은 `<task>/run/opd2-ledger.json`(+evidence 로그)로 옮겼다(`opal/skills/opal-pilot-dev2/scripts/lifecycle.py`). `Store.save()`는 전이가 성공할 때만 대응 `state-tool mark`를 호출하고, 그 호출이 실패하면 원장도 커밋하지 않아 두 저장소가 어긋나지 않는다.

- **우회 불가 게이트 — 가드 재사용**: `state_tool.py`에 `apply_opd2_gate_mark_guard()`(`opal/tools/state-tool/state_tool.py:6746`)를 신설했다. 이 함수는 opd/opds가 이미 쓰던 `apply_scenario_gate_mark_guard()`(`opal/tools/state-tool/state_tool.py:6699`)와 완전히 같은 시그니처·호출 위치(`cmd_mark` 저장 직전, `opal/tools/state-tool/state_tool.py:4338`)를 그대로 복제한 동형 패턴이다. 대상 행의 `skill == "opd2"`이고 `row.key`가 `OPD2_GATE_ROW_KEYS`(`task.intent_md`·`design.spec_md`·`plan.plan_md`·`execute.implement`·`verify.verifier_evidence`·`verify.review`, `opal/tools/state-tool/state_tool.py:6549`)에 속하며 완료 전이일 때, 형제 스크립트 `lifecycle.py verify-mark`(opd2 스킬 루트)를 subprocess로 호출해 opd2 자체 게이트 통과 여부를 재검사한다. 통과하지 못하면 `opd2_gate_record_required`로 거부하며, 이 거부는 `--force`·`--auto-pass`·`--as-worker` 어떤 조합으로도 우회되지 않는다(저장 전 호출이라 거부 시 `state.json`은 불변). `skill` 조건으로 스코프를 한정해 다른 Pilot의 동명 키(`execute.implement`·`plan.plan_md` 등) 전이에는 전혀 관여하지 않는다.

  이 확장은 태스크 Constraint C-1의 문자 그대로 범위("opd2 식별자·신규 기본값 등록")를 넘어서는 결정이라, 소유자가 세션 중 직접 확인해 승인했다(opd/opds의 `scenario_gate` 가드와 동형 패턴이라는 근거로 제시).

- **단계 이름을 기존 STAGE_ENUM에 매핑**: opd2는 자체 6단계(TASK/DESIGN/PLAN/EXECUTE/VERIFY/CLOSE, `opal/skills/opal-pilot-dev2/references/pipeline.json`)를 쓰지만, `state-tool`의 `STAGE_ENUM`(`opal/tools/state-tool/state_tool.py:69-77`)은 손대지 않고 기존 값만 재사용한다. lifecycle 엔진의 내부 전이 `INTENT→DESIGN→PLAN→BUILD→VERIFY→REVIEW→CLOSED`는 각각 `task.intent_md`(TASK stage)·`design.spec_md`(DESIGN)·`plan.plan_md`(PLAN)·`execute.implement`(EXECUTE)·`verify.verifier_evidence`(VERIFY)·`verify.review`(VERIFY)·`close.done_md`(CLOSE)로 대응한다.

  REVIEW 전이는 행 stage를 `REVIEW`가 아니라 `VERIFY`에 둔다. 그 이유는 `STAGE_ENUM`에 `REVIEW`가 이미 등재돼 있지만, 동시에 `MODE_BOUNDARY_STAGES`(`opal/tools/state-tool/state_tool.py:90-97`)라는 semi-agentic 경계 상수에도 속해 있기 때문이다. 행 stage를 `REVIEW`로 두면 semi-agentic 모드에서 리뷰 단계까지 사용자 확인 경계로 강제되는데, opd2 자체 설계는 "intent/spec/plan까지만 사용자 검토, 이후(리뷰 포함) 자율"이라 기존 설계와 어긋난다. `VERIFY`는 `MODE_BOUNDARY_STAGES`에 속하지 않으므로, 같은 stage 안에 독립 검증 행(`verify.verifier_evidence`)과 리뷰 행(`verify.review`)을 함께 두는 방식으로 경계를 피했다.

- **RELEASE/OBSERVE 미지원**: `delivery=release` 요청은 opd2 SKILL.md 진입 절차에서 명시적으로 거부한다(`opal/skills/opal-pilot-dev2/SKILL.md`). `lifecycle.py`의 기존 `--delivery release` 아티팩트 경로 자체는 이미 커밋된 계약이라 건드리지 않았지만, 이번 state-tool 연동(pipeline.json·checkpoint·CLOSE)은 build 배포만 대상으로 한다. build 배포 태스크는 독립 리뷰 통과 후 opd와 동일한 CLOSE 절차(`close.done_md`~`close.final`)로 마감되어 `completed_unmerged`가 된다.

- **등록 FW 워커로 디스패치**: opd2의 Coordinator/Builder/Verifier/Reviewer 호출은 각 역할 직전 `worker.dispatch` 이벤트를 load·verify한 뒤, 매번 새 Agent 호출로 등록된 FW 워커에게 디스패치하도록 바뀌었다 — 이전 역할의 대화 컨텍스트를 재사용하지 않아 "같은 워커가 구현과 검증·리뷰를 겸하지 않는다"는 요건을 물리적으로 보장한다. 후속 추가 작업(ADD-1)에서 Builder는 `docs/PROJECT.md` "프로젝트 구성"과 `plan.files` 경로를 매칭해 `opal-fe-agent`/`opal-be-agent`/`opal-db-agent`를 우선 선택하고, 매핑이 없으면 `opal-task-agent`로 폴백하는 라우팅이 추가됐다. Verifier/Reviewer는 계약(`lifecycle.py collect-evidence`·리뷰 판정)이 FW 전문 에이전트와 매핑되지 않아 항상 `opal-task-agent`를 쓴다.

## 영향 범위

- `opal/tools/state-tool/state_tool.py` — `NEW_TASK_DEFAULTS`·skill enum 2곳·`validate_pipeline_spec()`에 `opd2` 식별자 추가, `apply_opd2_gate_mark_guard()`·`OPD2_GATE_ROW_KEYS`·`OPD2_GATE_ERROR_CODES`(`opd2_gate_record_required`) 신설. `STAGE_ENUM`·`MODE_BOUNDARY_STAGES`·다른 Pilot의 `NEW_TASK_DEFAULTS` 항목·`cmd_mark` 분기는 변경하지 않았다(회귀 확인: `opal/tools/state-tool/tests/test_pilot_shared_contract.py` 전건).
- `opal/skills/opal-pilot-dev2/` — `references/pipeline.json`(신규), `scripts/lifecycle.py`(영속 계층을 state-tool 호출 기반으로 전환 + `verify-mark` 서브커맨드 신설), `scripts/opd2.py`, `SKILL.md`, `agents/coordinator.md`·`builder.md`·`verifier.md`·`reviewer.md`(이벤트 게이트·디스패치 계약, model frontmatter), `references/execution.md`·`references/lifecycle.md`, `README.md`(신규).
- `opal/core/references/opal-skills-registry.json` — `opal-pilot-dev2`/`opd2` 항목 등재.
- `opal/core/references/harness/modes.md`·`harness/worktree.md`·`harness/skill-commands.md`·`docs/PROJECT.md` — opd2 신규 기본값(agentic·worktree, actor 미지원)·컴포넌트 등재.
- `opal/core/references/harness/actor.md` §지원 Pilot 폐쇄 목록은 변경하지 않았다 — opd2는 actor=coordinator 축을 쓰지 않고 자체 Coordinator/Builder/Verifier/Reviewer 역할 분리 구조를 그대로 쓴다.

## 관련 페이지

- [[state-tool]]
