# op-dev-test-scenario

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-dev`가 TEST-SCENARIO 단계에서 디스패치합니다.

개발 태스크의 실행 전 검증 기준을 TEST-SCENARIO.md로 작성하는 단계입니다.

## 역할

TASK의 AC/C와 PLAN Risks의 실제 위험(H)만 검증 대상에 연결해, 관찰 가능한 조건·행동·기대 결과로 시나리오를 작성합니다. 작성자는 **PM**이며 PLAN 작성자와 분리됩니다(생성자·평가자 분리 원칙). 목표 커버 판정과 반복 재작성은 이 스킬이 아니라 다음 단계인 `op-scenario-gate`가 소유합니다.

## 입력

- `{task_folder}/TASK.md`, `{task_folder}/PLAN.md`
- PM이 선별한 프로젝트 문서와 실행 capability

## 출력

- `{task_folder}/TEST-SCENARIO.md`
- sdlc-v2 문서는 `Setup / Scenarios` 두 절만 사용
- 한 시나리오가 여러 토큰을 검증할 수 있으며, 요구사항별 시나리오 수 하한은 두지 않음
- 실행 결과·증거·RED 대상 여부는 `test-tool`이 관리하는 `test-scenario.json`이 소유하고, 단계·승인 상태는 `state.json`이 소유함 (이 문서에는 결과를 기재하지 않음)

## 호출 시점

`opal-pilot-dev`가 TEST-SCENARIO 단계를 디스패치할 때 호출됩니다. 사용자 검토 시점은 pilot의 진행 모드가 결정하며, 이 스킬은 승인이나 pipeline 상태를 변경하지 않습니다.

## 관련 문서

- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
