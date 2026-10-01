---
name: opal-pilot-dev2
description: >-
  AI-native SDLC 파일럿 opd2. 아이디어·변경·인시던트를 intent, spec, plan,
  구현, 독립 검증, 리뷰, 승인된 배포와 관측으로 연결한다.
  opd2 또는 opal-pilot-dev2 요청에 적용하며 semi-agentic, agentic, wt를 지원한다.
  기존 opd 호출이나 설명만 요청한 작업에는 적용하지 않는다.
---
# OPAL Pilot Dev 2

자체 AI-native 생명주기를 실행한다. 기존 opd에서는 진행 모드의 의미와 워크트리
생성·기동·소유권·체크포인트·마감 절차를 가져온다. 기존 opd Full profile로 전체
작업을 넘기거나 intent/spec을 TASK/PLAN으로 대체하지 않는다.

## 진입

1. 프로젝트 지침, 사용자 목표, 신규/재개 여부를 읽는다. **delivery=release 요청은
   이 통합에서 미지원이다** — 배포·관측(RELEASE/OBSERVE) 경로는 범위 밖이므로 명시
   거부하고 delivery=build(리뷰 완료·머지 대기)로 진행할지 사용자에게 확인한다. 별도
   배포 요청이 없으면 delivery=build로 한다. 아래 단계 이벤트 게이트와 state-tool
   연동(pipeline.json 행 mark, CLOSE)은 delivery=build 경로만 대상이다 — `lifecycle.py`의
   기존 `--delivery release` 아티팩트 경로 자체는 그대로 남아 있지만 이번 통합 대상이
   아니다.
2. **[MUST — pilot.start 이벤트 게이트]** 파일럿의 첫 작업 전에
   `~/.opal/tools/event-loader/run.sh load --event pilot.start > <pilot-receipt-path>`를
   호출해 응답 `documents[].content` 전문을 적용하고,
   `~/.opal/tools/state-tool/run.sh event-verify --event pilot.start --receipt <pilot-receipt-path>`가
   성공한 뒤에만 다음 단계로 진행한다.
3. [실행 연결](references/execution.md)로 mode/workspace를 확정한다. 신규 기본은
   agentic + wt. semi-agentic/agentic과 wt/no-wt는 독립 축이다.
4. wt면 OPAL이 발급한 canonical task path와 작업본을 사용한다. 생성 실패는 중단한다.
5. [생명주기](references/lifecycle.md), [아티팩트](references/artifacts.md)를 읽고
   scripts/lifecycle.py로 초기화한다. 재개는 status 결과로 이어간다.

호출은 python3 <skill-dir>/scripts/lifecycle.py <command> <task>다.

**[MUST — 단계 이벤트 게이트]** 각 단계 진입 시(첫 작업이나 `lifecycle.py transition`
직전) 아래 매핑의 이벤트를 load하고 응답 문서 전문을 적용한 뒤 같은 event id로
`state-tool event-verify`를 통과해야 한다.

| 단계 | 이벤트 |
|---|---|
| TASK | stage.task |
| DESIGN | stage.design |
| PLAN | stage.plan |
| EXECUTE | stage.execute |
| VERIFY | stage.test |

VERIFY는 `events.json`에 전용 `stage.verify`가 없어 기존 `stage.test`(test-cycle.md 등)를
재사용한다 — 새 이벤트를 신설하지 않는다. 호출 형식은
`~/.opal/tools/event-loader/run.sh load --event <event-id> > <stage-receipt-path>` 다음
`~/.opal/tools/state-tool/run.sh event-verify --event <event-id> --receipt <stage-receipt-path>`
다. 문서 집합은 `events.json`만 SSOT로 쓰며 이 SKILL에 파일 목록을 복제하지 않는다. load
실패, 필수 문서 누락, stale receipt, wrong-event receipt는 해당 단계 진입을 즉시 중단하는
blocker다.

- init: --repo <git-root> --change-id <id> --mode agentic --workspace worktree --worktree-receipt <json>
- status: 저장 상태와 현재 단계를 조회한다.
- transition: --actor coordinator. 도구가 전이를 허용할 때만 다음 단계로 이동한다.

## 필요한 시점에 읽기

| 시점 | 문서 | 역할 |
|---|---|---|
| 시작·재개 | agents/coordinator.md, references/lifecycle.md | Coordinator |
| intent/spec/plan | references/artifacts.md, references/risk-model.md | Coordinator + 사용자 |
| 구현 | agents/builder.md, references/testing.md | Builder |
| 독립 검증 | agents/verifier.md, references/testing.md | Verifier |
| 리뷰 | agents/reviewer.md, references/governance.md | Reviewer |
| 배포·관측 | references/rollout.md, references/metrics.md | 승인된 실행자·운영 담당자 |

Builder/Verifier/Reviewer를 디스패치할 때, Coordinator는 해당 `agents/*.md`의 frontmatter
`model` 값(light/standard/advanced)을 현재 플랫폼의 모델 매핑
(`opal/core/references/opal-model-mapping.md`, 원문 복제 없이 참조만)으로 변환해 디스패치
호출에 전달한다.

## PLAN 사전심사

PLAN 작성 완료 후 BUILD 진입 전, Layer 1(`ac_coverage`가 `intent.acceptance` 전체를
커버하는지 `lifecycle.py`가 기계적으로 검사)과 Layer 2(Reviewer의 Call A/B 독립 의미
심사가 둘 다 현재 fingerprint에서 pass로 기록됨)를 모두 통과해야 PLAN→BUILD 전이가
허용된다. Coordinator는 Layer 1을 먼저 자체 확인하고, 통과하면 Call A·Call B를 한 메시지
안에서 병렬 디스패치하며, 실패한 축만 표적 재검증한다. 절차 전문은 `agents/coordinator.md`
§PLAN 사전심사(BUILD 진입 전), 각 Call이 보는 축은 `agents/reviewer.md` §PLAN
사전심사(BUILD 진입 전)를 참조한다(원문 복제 없음).

에이전트 문서는 디스패치 계약이다. 해당 단계에서 실제 독립 에이전트를 호출하고 role
문서·아티팩트·소유 파일·검증 명령을 전달한다. Builder는 Verifier/Reviewer를 겸하지 않는다.
역할 문자열이 다르다는 것만으로 독립 실행 증거가 되지는 않는다.

**[MUST — worker.dispatch 이벤트 게이트]** Builder/Verifier/Reviewer를 호출하기 직전마다
`pm/dispatch-process.md` §Step 0의 `worker.dispatch` load·전문 적용·`state-tool
event-verify` 절차를 새로 수행한다 — 이전 역할이나 이전 시점의 receipt를 재사용하지
않는다. Builder는 `docs/PROJECT.md` "프로젝트 구성" 매칭 결과에 따라 전문 에이전트
(opal-fe-agent/opal-be-agent/opal-db-agent)를 우선 선택하고, 매핑이 없거나
`docs/PROJECT.md`가 없으면 `opal-task-agent`로 폴백한다. Verifier/Reviewer는 계약이
`lifecycle.py collect-evidence`·리뷰 판정 기반이라 FW 전문 에이전트 매핑 대상이 아니므로
항상 `opal-task-agent`다(`AGENTS.md` §폴백 규칙 2 "매핑 테이블에 해당 단계/영역 없음 →
해당 단계는 기존 방식").
Agent 도구로 역할마다 매번 새로 호출하고, 호출 대상 역할 문서(`agents/builder.md`·
`agents/verifier.md`·`agents/reviewer.md`) 본문을 `pm/dispatch-process.md` §워커 컨텍스트
주입 템플릿의 `[WORKER]` 프롬프트에 그대로 주입한다. 같은 역할을 위해 이전 호출의 대화
컨텍스트를 넘기지 않는다 — Builder≠Verifier≠Reviewer는 매번 독립 Agent 세션이다
(`lifecycle.py`의 기존 builder≠verifier·builder≠reviewer 게이트와 정합). 각 역할의
입력·수정 권한·출력 계약 자체는 해당 agents/*.md 본문이 그대로 정의하며, 이 절은
디스패치 방식만 규정한다. Coordinator가 매 디스패치 전 `pm/dispatch-process.md` §Step
1~4(프로젝트 문서 선별·에이전트 선택)를 수행한 뒤 위 절차로 디스패치한다.

플랫폼별 분기(Claude/Cursor/Codex 등)는 이 스킬이나 역할 문서에 두지 않는다. 필요하면
어댑터 계층(`AGENTS.md` §플랫폼 sub-agent 어댑터 변환 규칙)에만 둔다. 파이프라인 행 상태
편집은 `state-tool` CLI 호출로만 하고, 배포·머지·push 승인 경계는 `harness/guards.md`
§커밋 규칙을 그대로 따른다 — 이 스킬은 별도 승인 경로를 만들지 않는다.

## 진행 계약

- semi-agentic: intent, spec, plan/시나리오까지 사용자 검토, 이후 정상 개발·검증·리뷰·마감 자율.
- agentic: 정상 단계 자율 진행. 미결정 요구·외부 계약·고위험 승인·권한 부족·재시도 상한은 대기.
- 상태 변경은 state-tool을 통해서만 한다. state.json(state-tool)이 단계 진행 상태(task_steps)의 SSOT이고, lifecycle.py 원장(opd2-ledger.json)은 전이마다 자체 게이트를 먼저 판정한 뒤 `state-tool mark`로 그 SSOT에 커밋한다 — 실패 시 원장도 커밋하지 않는다.
- 테스트 명령은 실제 실행한다. 실패·환경 부재·타임아웃은 통과가 아니다.
- 증거 뒤 코드/아티팩트가 바뀌면 재검증한다. merge/push/배포는 자율 모드만으로 승인되지 않는다.
- 구조·해시·증거 연결은 도구가, 요구 의미와 품질은 독립 에이전트가 검사한다.

## 완료

build는 REVIEW 통과 후 DONE.md와 함께 CLOSED/ready_for_merge로 끝난다.
release는 RELEASE·OBSERVE 실행 증거와 승인 후 CLOSED/observed로 끝난다.
배포하지 않은 결과를 배포 완료라고 보고하지 않는다.

패키지 검사: python3 -m unittest discover -s <skill-dir>/tests -v.
행동 평가는 [evals.md](references/evals.md)를 사용한다.
현재 검증 범위와 미실행 영역은 [validation.md](references/validation.md)에 기록한다.
전역 //opd2 별칭 등록은 별도 통합이며 현재 폴더는 직접 사용할 스킬 원본이다.
