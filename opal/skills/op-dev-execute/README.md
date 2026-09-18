# op-dev-execute

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-dev`·`opal-pilot-dev-wireframe`가 EXECUTE 단계에서 디스패치합니다.

sdlc-v2 PLAN.md의 배정된 Work items를 구현하고 검증 증거를 반환하는 코드 실행 단계입니다.

## 역할

디스패치된 Work item(W)만 수행합니다. 병렬 배치와 파일 소유권은 PM이 PLAN의 `Work items`로 이미 확정한 값이며, 워커는 이를 재배정하지 않습니다. RED-first 계약을 따라 RED 테스트 작성자(`opal-test-agent` red mode)와 GREEN 구현자를 분리하고, RED 테스트 파일을 수정하지 않습니다(reward hacking 방어).

전문 에이전트인지 범용 에이전트인지에 따라 추가로 읽는 가이드가 다릅니다.

## 입력

- `task_folder`, `plan_source`, `scenario_source`, `work_items`
- PM이 `## 실행 capability`에 주입한 스킬·MCP·외부 도구 (state-tool·test-tool 명령은 선택형 capability가 아니라 EXECUTE 단계의 구조적 workflow이며, 실행 불가 시 환경 블로커로 보고)

## 출력

- 코드·문서 변경 (구현으로 내용이 달라지는 문서만 수정, 참조 전용 문서는 수정하지 않음)
- `changed_files`, 수행한 W, 실제 검증 명령과 결과, blocker

## 호출 시점

`opal-pilot-dev`와 `opal-pilot-dev-wireframe`가 EXECUTE Work item을 워커에게 디스패치할 때 호출됩니다. 진행 모드의 사용자 확인·자동 승인·CLOSE 경계는 워커가 변경하지 않습니다.

## 관련 문서

- `opal/skills/op-dev-execute/references/execute-guide.md` (공통 실행 절차)
- `opal/skills/op-dev-execute/references/execute-specialist-guide.md` / `execute-generalist-guide.md`
- `opal/skills/op-dev-execute/references/checkpoint-guide.md`
