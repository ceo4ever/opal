## 개요

TASK의 Acceptance criteria는 별도 요구사항 절이 없는 sdlc-v2에서 검증 가능한 핵심 요구사항 역할을 함께 맡는다(`opal/skills/op-task/references/task-guide.md:26`).

## 결정 배경

같은 요구를 구현 방법이나 검증 환경별 AC로 나누면 새로운 수용 결과 없이 PLAN과 TEST의 추적 분모만 늘어난다(`opal/skills/op-task/references/task-guide.md:43`). 따라서 개수 제한 대신 수용 결정의 의미가 겹치는지를 판정 기준으로 채택했다(`opal/skills/op-task/references/task-guide.md:53`).

## 결정 내용

하나의 AC는 다른 AC와 겹치지 않는 독립적인 수용 결정 하나를 표현하며, 출처성·필수성·관찰성·해법 독립성·비중복성을 모두 만족해야 한다(`opal/skills/op-task/references/task-guide.md:28`). 구현 방법은 PLAN으로, 검증 방법과 환경은 TEST-SCENARIO로 분리한다(`opal/skills/op-task/references/task-guide.md:61`).

## 적용 범위

신규 sdlc-v2 TASK 작성과 검토에 적용하며 기존 TASK에는 소급하지 않는다(`tasks/165-260928-oppm-AC-핵심-요구사항-작성-기준/TASK.md`).

## 관련 페이지

- [[op-task]]
