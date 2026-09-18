# op-task

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-dev`, `opal-pilot-dev-wireframe`, `opal-pilot-project`가 TASK 단계에서 디스패치합니다.

사용자 요청을 sdlc-v2 TASK.md로 구조화하는 범용 단계 스킬입니다. 문제·목표 결과·영향 범위·제약·완료 기준을 짧고 검증 가능하게 고정합니다.

## 역할

`op-task`는 개발 파일럿 전용인 `op-dev-*` 계열과 달리 도메인에 무관한 범용 단계 스킬 계열(`op-task`·`op-task-plan`·`op-task-qa`·`op-task-execute`)에 속하며, 여러 파일럿이 공통으로 TASK 단계에서 재사용합니다.

이 스킬은 호출자인 PM이 **직접 수행**합니다. TASK 작성을 위해 워커나 다른 스킬을 별도로 호출하지 않습니다. `pilot_key`·`mode`·태스크 폴더 채번·`state init`은 호출자/하네스가 소유하며, 이 스킬은 이를 재추천하거나 TASK.md에 복제하지 않습니다. 프로젝트 문서와 런타임 capability 선별도 PM dispatch가 소유하므로 이 스킬은 고정 기술 스택·스킬·MCP 카탈로그를 탐색하지 않습니다.

사용자 발화와 프로젝트 맥락에서 `Problem`·`Proposed outcome`·`Affected users and systems`·`Constraints`·`Acceptance criteria` 다섯 항목을 추출해 TASK.md를 작성합니다. 목표·범위·제약·완료 기준을 바꿀 정보가 없을 때만 사용자에게 질문하며, 구현 방식·기술 스택·대안 비교처럼 ANALYSIS/PLAN에서 결정할 내용은 묻지 않습니다.

## 입력

- 사용자 요청
- `task_path`

## 출력

`task_path/TASK.md` — 첫 YAML frontmatter가 정확히 `template: sdlc-v2`이고, 다섯 필수 절이 모두 비어 있지 않으며, `Constraints`는 고유 `C-N`, `Acceptance criteria`는 고유 `AC-N` 식별자를 갖습니다. 단계·승인·gate·pilot·mode 상태는 적지 않으며(`state.json` 소유), 기술 스택·관련 문서 목록·대안표는 별도 절로 만들지 않습니다.

작성 후 `~/.opal/tools/state-tool/run.sh verify <task-path> --clarification-check`로 `template=sdlc-v2`와 필수 절·AC/C 식별자 검사를 통과시켜야 완료로 간주합니다.

## 호출 시점

개발 오케스트레이터가 TASK 단계를 수행할 때 디스패치됩니다. 상세 필드 규칙과 형식은 `references/task-guide.md`를 따릅니다.

## 관련 문서

- `opal/skills/op-task/references/task-guide.md`
