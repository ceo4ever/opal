# op-dev-wireframe

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-dev-wireframe`가 WIREFRAME 단계에서 디스패치합니다.

TASK.md와 입력물(정책서/이미지/구두 요청)을 기반으로 `wireframe-builder` 스킬에 위임해 wireframe.md를 생성하는 단계입니다.

## 역할

시니어 서비스 기획자 페르소나로 사용자 관점의 화면 구성과 흐름을 설계하되, 기술 구현 가능성을 고려합니다. 이 스킬 자체가 wireframe을 직접 그리지 않고 실제 작성은 `wireframe-builder` 스킬에 위임합니다.

## 입력

- `tasks/{NNN}-{태스크명}/TASK.md`
- 입력물: 정책서(.md/.docx/.pdf), 이미지(.png/.jpg), 구두 요청(TASK.md 본문)
- 입력물이 부족하면 `interview` 스킬로 요구사항을 추가 수집

## 출력

- `tasks/{NNN}-{태스크명}/wireframe.md`
- 자체 검증 체크리스트: 요구사항 반영, ASCII 레이아웃, 컴포넌트 계층, 인터랙션 명세, shadcn/ui 매핑, ui-designer로 바로 구현 가능한 수준인지

## 호출 시점

`opal-pilot-dev-wireframe`가 WIREFRAME 단계를 디스패치할 때 호출됩니다. 완료 후 워커는 QA를 직접 호출하지 않고 오케스트레이터가 QA 단계 실행 여부를 결정합니다.

## 관련 문서

- 페르소나: `opal/skills/op-dev-wireframe/personas/service-planner.md`
- 위임 대상: `wireframe-builder` 스킬 SKILL.md
- 보완 도구: `interview` 스킬
