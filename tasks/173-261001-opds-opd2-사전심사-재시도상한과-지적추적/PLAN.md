---
template: sdlc-v2
---
# PLAN: opd2 PLAN 사전심사 — 재검증 절차 정합·회차 상한·지적 해소 추적

> 입력: [TASK.md](TASK.md)

## Approach

세 가지 결함을 서로 다른 층에서 고친다. 도구가 이미 올바르게 집행하는 규칙은 바꾸지 않고(C-1), 도구가 비어 있는 곳만 채운다.

1. **재검증 절차(AC-1)는 문서만 고친다.** 지문(fingerprint)에 plan 해시와 저장소 트리가 들어가고 전이가 두 Call 모두 "현재 지문에서 pass"를 요구하는 현재 도구 동작(`opal/skills/opal-pilot-dev2/scripts/lifecycle.py:225-230`, `:310-314`)이 옳다. 이 결합을 풀어 통과한 Call 기록을 유지하면 아티팩트 지문 결합이라는 기존 기계 게이트가 약해지므로(C-1) 도구는 두고, "실패한 Call만 재실행"이라는 틀린 안내(`opal/skills/opal-pilot-dev2/agents/coordinator.md:34-36`)를 "수정 후에는 A·B를 모두 다시 디스패치한다"로 바꾼다.
2. **회차 상한(AC-2)은 도구에 새로 넣는다.** PLAN 사전심사의 fail 기록 수를 도구가 세어 3회에 이르면 재심사 기록·BUILD 전이·되돌리기를 거부하고 사용자 결정 대기 상태(`blocked`)로 둔다. 사용자의 명시 해제 명령으로만 풀린다. 현재 도구는 되돌리기(rewind)만 세므로(`lifecycle.py:542-543`) 사전심사 재시도는 무한히 반복될 수 있다.
3. **지적 해소 추적(AC-3)은 도구가 기록 형식을 집행한다.** fail 기록은 `{id, location, remaining_choice}` 항목을 남기고, 같은 Call의 다음 기록은 직전 미해소 지적 전건에 대해 `{id, status, evidence}`를 보고해야 한다. id 집합이 맞지 않으면 기록을 거부한다. 태스크 170이 opd·opds 설계 게이트에 넣은 `previous_gaps`·`resolved_gaps` 패턴을 opd2 원장 모델(JSON 기록·CLI 인자)에 맞게 옮긴 것이다.

기존 원장은 그대로 읽힌다(C-2): 새 필드가 없는 기록은 상한 집계와 지적 추적에서 제외하고, 통과 판정 규칙은 바꾸지 않는다.

## Findings

### 직접 변경
- `opal/skills/opal-pilot-dev2/scripts/lifecycle.py` — `Store`에 사전심사 상한·지적 추적 헬퍼 추가, `review --call` 분기에 형식·해소 검증과 상한 판정 추가, `_check_artifact_stage`의 plan 분기·`rewind`·`unblock`에 상한 대기 거부 추가, `plan-review-reset` 서브커맨드와 `--findings`·`--resolutions` 인자 추가.
- `opal/skills/opal-pilot-dev2/schemas/plan-review.schema.json` — 사전심사 기록(지적·해소 포함) 스키마 신규.
- `opal/skills/opal-pilot-dev2/tests/test_lifecycle.py` — 재검증 절차·상한·해제·지적 형식·해소 보고·기존 원장 호환 테스트 추가.

### 회귀 확인
- `opal/tools/state-tool/state_tool.py` — `apply_opd2_gate_mark_guard()`가 opd2 `verify-mark` 서브커맨드를 호출하는 경로(`plan.plan_md` 키)가 상한 대기 상태에서도 같은 JSON 오류 계약으로 거부되는지만 확인하고 수정하지 않는다.
- `opal/skills/opal-pilot-dev2/references/pipeline.json` — 행 구성과 task-step 키는 바뀌지 않는다.
- `opal/skills/opal-pilot-dev2/scripts/opd2.py` — 진입점 CLI는 사전심사 서브커맨드 목록에 의존하지 않음을 확인하고 수정하지 않는다.
- `scripts/install-mac.sh` — 스킬 디렉터리를 통째로 복사하는 기존 경로(새 `schemas/` 파일 포함)만 확인하고 수정하지 않는다.

### 문서 갱신
- `opal/skills/opal-pilot-dev2/agents/coordinator.md` — §PLAN 사전심사의 재검증 절차(3번)와 상한 공유 문장(4번)을 도구 동작에 맞게 교체하고, 지적 전달·상한 대기·해제 절차를 추가한다.
- `opal/skills/opal-pilot-dev2/agents/reviewer.md` — §PLAN 사전심사에 지적 항목 형식, 해소 보고 의무, `review` 명령의 새 인자를 추가한다.
- `opal/skills/opal-pilot-dev2/SKILL.md` — §PLAN 사전심사 단락의 "실패한 축만 표적 재검증"을 교체하고 상한·지적 추적을 한 문장씩 가리킨다.
- `opal/skills/opal-pilot-dev2/references/lifecycle.md` — 사전심사 상한·해제·원장 필드를 기록하는 소절을 추가한다.

### 미확인 가정
- Reviewer가 형식에 맞는 지적·해소 JSON을 매번 정확히 작성하는지는 H-1 참조.
- `resolved` 보고의 내용상 진위는 도구가 검증하지 못한다는 한계는 H-2 참조.
- 설치 후 검증을 전체 install 실행 없이 스크래치 배포 루트로 대신해도 되는지는 H-3 참조.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| AC-1은 문서만 고치고 지문·전이 규칙은 바꾸지 않는다 | 절차 문서는 "fail을 고치려고 plan 또는 저장소 파일을 바꾸면 지문이 바뀌어 이전에 통과한 Call 기록도 무효가 되므로 A·B를 모두 다시 디스패치한다"고 안내한다. "통과한 Call은 재실행하지 않는다"·"표적 재검증으로 비용을 줄인다"·"기존 재작업 상한(`retries <= 3`)을 공유한다"는 문장은 삭제한다 | 지문 결합 완화는 C-1(아티팩트 지문 결합 유지) 위반이다. 도구 동작이 이미 일관되므로 문서가 도구에 맞춘다 |
| 사전심사 상한 집계 단위는 fail 기록 1건이다 | `PLAN_REVIEW_FAIL_LIMIT = 3`. fail 수 = `state['plan_reviews'][plan_review_floor:]` 중 `findings` 키를 가진 `verdict: fail` 기록의 수다(`plan_review_floor`가 없으면 0). `rewind`는 `plan_reviews`를 비울 때 `plan_review_floor`도 0으로 되돌린다(그 외 rewind 동작·상한은 그대로). 한 회차에서 A·B가 모두 fail이면 2로 센다. 같은 지문에서 같은 Call을 다시 fail로 기록해도 센다 | "회차"를 지문이나 시점으로 정의하면 같은 지문 재기록 같은 경로가 상한을 우회한다. 기록 단위로 세면 모든 fail이 예외 없이 상한에 반영된다 |
| 상한 대기 상태는 `stage == 'PLAN'`이고 fail 수가 3 이상인 것으로만 판정한다 | 상한 대기 중에는 (a) `review --call`(pass·fail 모두), (b) PLAN→BUILD 전이 — 상한 대기 검사를 `advance()`의 맨 첫 줄(기존 `blocked` 검사보다 앞)과 `verify-mark`가 쓰는 `_check_artifact_stage` plan 분기 맨 앞에 둔다. 그래서 다른 사유의 `blocked`가 있어도 `transition` 오류는 항상 아래 상한 대기 문구로 시작한다, (c) `rewind`(모든 gate), (d) `unblock`이 거부된다. 거부 오류 문구는 `await_user: PLAN pre-review fail limit (3) reached; user release required`로 시작하며 원장은 바뀌지 않는다. 기존 `main()`의 `await_user` 문자열 판정에 따라 응답은 `transition_action: await_user`·`report_type: decision_request`다 | AC-2의 "재심사 기록과 BUILD 전이 거부". rewind는 원장의 `blocked`와 사전심사 기록을 지우는 기존 탈출구라 상한 대기 중 열어 두면 사용자 결정을 우회한다. rewind 상한(3회)·동작은 상한 대기 밖에서 그대로다(C-1) |
| 3번째 fail 기록 자체는 정상 기록되고 같은 저장에서 `blocked`를 표시한다 | 3번째 fail 기록은 거부되지 않고 저장되며, `state['blocked']`가 비어 있을 때만 위 `await_user: ...` 문구로 채운다. 그 명령의 응답은 기존 로직대로 `transition_action: blocked`·`report_type: decision_request`다. 이미 다른 사유의 `blocked`가 있으면 덮어쓰지 않는다 | `status`가 상한 대기를 사용자 결정 대기로 보여야 한다(AC-2). 상한 대기 판정은 `blocked` 값이 아니라 fail 수가 소유하므로 다른 사유가 있어도 게이트는 동일하다 |
| 해제는 새 서브커맨드 `plan-review-reset`뿐이다 | `plan-review-reset <task> --actor <실명 사용자> --reference <실제 사용자 메시지> --reason <사유>`. `--actor`가 `coordinator`·`builder`·`verifier`·`reviewer`이면 거부(`approve`와 같은 목록). 상한 대기가 아니면 `no plan review hold to reset`으로 거부. 성공하면 `plan_review_floor`를 현재 사전심사 기록 수로 올리고, `blocked`가 상한 대기 문구와 같을 때만 비운다. 사전심사 기록 이력은 보존한다. 해제 뒤 fail 수는 0이며 3회까지 다시 허용한다. 원장 이벤트 종류는 `plan_review_reset`이다 | "사용자가 명시적으로 해제해야만"(AC-2). `unblock`은 사용자 신원 검사가 없어 해제 수단으로 쓸 수 없다. 설계 게이트의 `reset --owner user`와 같은 취지다 |
| 지적 항목 형식은 JSON 객체 `{id, location, remaining_choice}`다 | `review --call A\|B --verdict fail`은 `--findings '<JSON 배열>'`을 받는다. 항목 세 필드는 모두 공백이 아닌 문자열이다. `id`는 `<Call>-<n>`(Call 문자 + 하이픈 + 앞에 0이 없는 양의 정수, 예: `A-1`)이고 해당 Call 문자와 일치해야 한다. 한 기록 안에서, 그리고 같은 Call의 이번 되돌리기 이후 모든 이전 기록의 지적 id와 겹치지 않아야 한다. `location`은 지적이 가리키는 위치(문서·필드·AC 번호), `remaining_choice`는 고치지 않으면 구현자에게 남는 선택이다 | "위치와 남은 선택이 드러나는 정해진 형식"(AC-3). 원장과 CLI가 이미 JSON(`--argv` 선례)이라 문자열 파싱 모호성이 없다. 태스크 170의 `{axis}-{n}: {위치} — {남은 선택}`과 같은 정보를 담는다 |
| 이전 지적은 같은 Call의 최신 기록에서만 가져온다 | 같은 Call의 최신 사전심사 기록(지문·`plan_review_floor`와 무관)이 `verdict: fail`이고 `findings` 키가 있으면 그 기록의 `open_findings`가 이번 기록이 해소를 보고해야 할 "이전 지적"이다. 그렇지 않으면 이전 지적은 없다. 도구가 원장에서 직접 구하며 Coordinator가 전달한 값을 신뢰하지 않는다 | "다음 회차 같은 Call의 심사 기록은 직전 fail 지적 전건"(AC-3). Call별 독립을 유지해 한 Call이 상대 Call의 지적을 알게 되지 않는다 |
| 해소 보고는 JSON 객체 `{id, status, evidence}`다 | `--resolutions '<JSON 배열>'`. `id` 집합은 이전 지적 id 집합과 정확히 같아야 한다(누락·초과·중복 모두 거부). `status`는 `resolved`·`unresolved`, `evidence`는 공백이 아닌 문자열이다. 이전 지적이 없으면 비어 있어야 한다. 불일치 오류는 `resolutions must cover exactly the previous findings [<id>, ...]`로 기대 id를 알려 준다 | "누락되거나 지적 집합과 맞지 않으면 그 기록이 거부"(AC-3). 기대 id를 오류에 실어 Reviewer가 한 번에 고칠 수 있게 한다 |
| 기록의 판정과 미해소 지적은 일관되어야 한다 | 기록에는 도구가 계산한 `open_findings`(= 이전 지적 중 `unresolved`로 보고된 항목 원본 + 이번 `findings`)를 함께 저장한다. `pass`는 `findings`가 비어 있고 모든 해소가 `resolved`여야 한다(= `open_findings`가 비어 있음). `fail`은 `open_findings`가 1건 이상이어야 한다. 위반하면 기록을 거부한다 | 미해소 지적을 둔 채 pass하거나, 지적 없이 fail하는 기록은 다음 회차 추적을 끊는다. `open_findings`를 저장하면 미해소 지적이 새 지적으로 다시 적히지 않아도 다음 회차에 이어진다 |
| 형식·해소 위반 기록은 거부되고 상한을 소비하지 않는다 | 모든 위반은 기록 전에 `ValueError`로 거부된다(exit 2, 원장 불변). 거부된 시도는 fail 수에 들어가지 않는다. 사전심사 기록은 저장 전에 새 스키마로 검증한다. 스키마 검증기가 정규식을 지원하지 않으므로 id 형식·중복·집합 비교는 코드에서 한다 | 형식 오류가 상한을 먹으면 도구 오류로 사용자 결정을 부르게 된다. 기존 `validate()` 부분집합만 쓴다(`lifecycle.py:69-94`) |
| 기존 원장 호환은 "새 키가 있는 기록만 새 규칙 대상"이다 | `findings` 키가 없는 기록(변경 전 원장)은 fail 수에서 제외하고 이전 지적으로도 쓰지 않는다. `plan_review_floor`가 없으면 0으로 읽고, `rewind`는 이 키를 0으로 써 넣는다. pass 판정 조건(현재 지문의 같은 Call 최신 기록이 pass)은 바꾸지 않으므로 변경 전 원장의 pass 기록으로도 BUILD 전이가 된다. 원장을 다시 쓰는 이행 단계는 없다 | C-2. 변경 전 원장은 상한이 없던 규칙 아래 만들어졌으므로 소급 집계하지 않는다. 롤백 시 새 필드는 이전 코드가 읽지 않고 무시한다 |
| 지적 전달은 Coordinator가 `status`로 한다 | 새 조회 서브커맨드는 만들지 않는다. Coordinator는 Call 디스패치마다 `status`의 사전심사 기록에서 그 Call의 최신 기록을 찾아, `fail`이면 그 `open_findings`를 Reviewer 프롬프트에 그대로 싣는다. 틀려도 도구가 거부하므로 검증은 도구가 소유한다 | 단일 사용처의 조회 명령은 과설계다(PRINCIPLES §2). 진위 판정은 도구의 id 집합 검사가 소유한다 |
| 상한은 PLAN 사전심사(`review --call`)에만 적용한다 | REVIEW 단계의 독립 리뷰, Layer 1(`ac_coverage`) 검사, rewind 상한(`retries <= 3`)은 바꾸지 않는다 | TASK 제외 범위와 C-1 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 재검증·해소 추적·상한 테스트 작성(RED) | opal-test-agent (red mode) | `opal/skills/opal-pilot-dev2/tests/test_lifecycle.py` | 기존 `LifecycleTests`의 헬퍼(`call`·`artifact`·`plan_ready`)를 재사용해 TEST-SCENARIO S-1, S-3~S-8을 검증하는 테스트를 추가한다(기존 테스트는 수정하지 않는다). 사전심사 기록 헬퍼 `review_plan(call, verdict, findings, resolutions, ok)`를 추가한다. 변경 전 원장 재현은 `Store.state()`에서 꺼낸 state의 `plan_reviews`에 `findings` 키 없는 기록을 직접 넣어 `Store.save(state, 'plan_review', report)`로 저장해 만든다 | 없음 | P1 | AC-1, AC-2, AC-3, C-1, C-2 |
| W-2. 절차·참조 문서 갱신 | opal-task-agent | `opal/skills/opal-pilot-dev2/agents/coordinator.md`, `opal/skills/opal-pilot-dev2/agents/reviewer.md`, `opal/skills/opal-pilot-dev2/SKILL.md`, `opal/skills/opal-pilot-dev2/references/lifecycle.md` | coordinator.md §PLAN 사전심사: 3번을 "하나라도 fail이면 findings를 반영해 plan을 고친 뒤 A·B를 모두 새로 디스패치한다(지문에 plan 해시가 들어가 수정 시 이전 통과 기록이 무효)"로, 4번을 "fail 기록이 3건이 되면 도구가 상한 대기로 전환해 재심사·BUILD 전이·rewind를 거부하며 Coordinator는 사용자에게 결정을 요청하고 사용자 명시 해제(`plan-review-reset`) 전에는 진행하지 않는다. 이 상한은 rewind 상한과 별개다"로 교체한다. Call 디스패치마다 `status`에서 그 Call의 최신 fail 기록 `open_findings`를 찾아 Reviewer 프롬프트에 실으라는 단계를 추가한다. reviewer.md §PLAN 사전심사: 기록 명령 예시에 `--findings`·`--resolutions`를 추가하고 지적 항목 형식(`id`·`location`·`remaining_choice`), 해소 보고 의무(이전 지적 전건, `resolved`/`unresolved`와 근거), pass 조건(지적 없음·전건 resolved), fail 조건(미해소 지적 1건 이상)을 적는다. SKILL.md §PLAN 사전심사: "실패한 축만 표적 재검증한다"를 "수정 뒤 A·B를 모두 다시 디스패치한다"로 바꾸고 상한·지적 추적을 coordinator.md·reviewer.md 절 참조로 한 문장씩 덧붙인다. lifecycle.md: PLAN 사전심사 상한(3회 fail, 상한 대기 시 거부되는 명령 4종, `plan-review-reset`)과 사전심사 기록 필드(`findings`·`resolutions`·`open_findings`, 원장의 `plan_review_floor`)를 한 소절로 추가한다. 도구·PLAN 결정 문구를 그대로 옮기고 새 정책을 만들지 않는다 | 없음 | P1 | AC-1, AC-2, AC-3, C-3 |
| W-3. 상한·지적 추적 구현(GREEN) | opal-task-agent | `opal/skills/opal-pilot-dev2/scripts/lifecycle.py`, `opal/skills/opal-pilot-dev2/schemas/plan-review.schema.json` | Decisions 표의 계약대로 구현한다. `PLAN_REVIEW_FAIL_LIMIT = 3`과 상한 대기 오류 문구 상수를 두고 `Store`에 헬퍼 4개(fail 수, 상한 대기 판정, 이전 지적 조회, 상한 대기 거부)를 추가한다. `advance()` 첫 줄(기존 `blocked` 검사보다 앞), `_check_artifact_stage` plan 분기 맨 앞, `review --call` 분기 맨 앞, `rewind`, `unblock`에서 상한 대기를 거부한다. `rewind`가 `plan_reviews`를 비울 때 `plan_review_floor`를 0으로 되돌린다. `review --call`은 신원 확인 뒤 `--findings`·`--resolutions`를 파싱해 id 형식·중복·집합 일치·판정 일관성을 검사하고 `open_findings`를 계산해 기록(`call`·`actor`·`verdict`·`reason`·`fingerprint`·`findings`·`resolutions`·`open_findings`)을 새 스키마로 검증한 뒤 저장한다. 3번째 fail 저장 시 `blocked`가 비어 있으면 상한 대기 문구로 채운다. `plan-review-reset` 서브커맨드와 argparse 선택지·`--findings`·`--resolutions` 인자를 추가한다. 스키마는 기록 필드를 `additionalProperties: false`로 정의하고 기존 `validate()`가 지원하는 키워드만 쓴다. 플랫폼·모델별 분기는 만들지 않는다 | W-1 | P2 | AC-2, AC-3, C-1, C-2, C-3 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. Reviewer(독립 Agent)가 `--findings`·`--resolutions` JSON을 형식대로 작성하지 못해 기록이 반복 거부된다 | AC-3의 집행이 심사 진행을 막는 마찰이 될 수 있다 | 사전심사가 지연되고 Coordinator 개입이 늘어난다 | 거부는 상한을 소비하지 않고, 오류가 기대 id 집합을 알려 주며, reviewer.md에 완성된 명령 예시를 둔다(W-2). S-5·S-6이 거부 사유별 오류 문구를 확인한다 |
| H-2. `resolved` 보고의 진위는 도구가 검증할 수 없다 | 독립 Reviewer가 고쳐지지 않은 지적을 `resolved`로 보고할 수 있다 | AC-3이 보증하는 것은 보고의 완전성(전건 보고·id 일치)까지이고 내용 정확성이 아니다 | 이 한계를 lifecycle.md 소절에 명시하고(W-2), 다음 회차 Reviewer가 직전 `evidence`를 입력으로 받아 재검토하게 한다. 미해소 지적을 둔 pass는 도구가 거부한다 |
| H-3. 전체 `scripts/install-mac.sh` 실행 없이 스크래치 배포 루트로 설치 후 검증을 대신한다 | "설치본에서도 동작" 증거의 범위 | install-mac.sh의 스킬 배포가 `install_dir`(디렉터리 복사)와 `strip_deploy_md_recursive`(`## 변경이력` 절 제거)뿐이라는 가정(`scripts/install-mac.sh:1368-1378`)이 틀리면 설치본과 스크래치 결과가 다를 수 있다 | 같은 함수 정의를 `install-mac.sh`에서 그대로 잘라 스크래치 `skills/`·`tools/` 형제 구조에 적용하고 그 사본에서 전체 테스트를 실행한다. 공유 `~/.opal/`은 건드리지 않으며 실제 install은 merge 이후 사용자 권한이다 |

## Release and recovery

- 적용 순서: W-1(RED 테스트)과 W-2(문서)는 파일이 겹치지 않아 P1에서 병렬로 진행하고, RED 증거가 잠금된 뒤 W-3(구현)을 P2로 진행한다. W-3 완료 뒤 전체 테스트와 스크래치 배포 검증을 한다.
- 검증 범위: 도구 동작은 `python3 -m unittest discover -s opal/skills/opal-pilot-dev2/tests`(기준선 36건 통과)에 추가 테스트를 포함해 실제 `lifecycle.py` CLI 호출로 결정론 검증한다. 문서 정합은 정적 검사(삭제 문구 부재·교체 문구 존재)로 확인한다. 설치 후 검증은 `install_dir`·`strip_deploy_md_recursive` 정의를 `scripts/install-mac.sh`에서 잘라 스크래치 루트(`skills/opal-pilot-dev2` + `tools/` 복사본)에 적용하고 그 사본에서 전체 테스트를 실행한다. 실제 사전심사 Reviewer를 디스패치하는 연동 검증은 이 태스크 범위 밖이며 도구 CLI 수준의 계약 검증으로 한정한다.
- 실측 경계: 시간·품질 목표 없음.
- 실패 시: 구현 커밋을 되돌리면 이전 동작으로 복귀한다. 새 필드(`findings`·`resolutions`·`open_findings`·`plan_review_floor`)가 이미 기록된 원장도 이전 코드가 해당 키를 읽지 않으므로 계속 동작한다. 설치·배포 전에 되돌릴 수 있고 데이터 이행은 없다.
