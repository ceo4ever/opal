# TASK: AC 핵심 요구사항 작성 기준 명확화

## 요청과 목표

`op-task`가 작성하는 Acceptance criteria가 검증 단계나 구현 방법에 따라 중복되지 않고, 각 AC가 서로 겹치지 않는 핵심 수용 요구사항 하나를 표현하도록 작성 기준을 명확히 한다.

원 요청은 태스크 164의 AC/C 과다 여부 검토에서 시작했으며, 캡틴은 개수 제한보다 AC의 작성·중복 판별 기준을 명확히 하는 방향과 알투의 직접 수정을 승인했다.

## 완료 조건

- AC의 역할을 현재 sdlc-v2에서 요구사항 역할까지 겸하는 핵심 수용 요구사항으로 명확히 설명한다.
- AC 입장 조건에 출처성·필수성·관찰성·해법 독립성·비중복성을 반영한다.
- 동일 요구를 구현 방식·테스트 환경·배포 단계별 AC로 중복 분리하지 않도록 한다.
- AC에서 제외한 정보가 PLAN, TEST-SCENARIO, Work item, 프로젝트 규칙 중 어디로 가는지 명시한다.
- 관련 `op-task` 문서가 같은 계약을 설명하고 기존 구조 검사가 통과한다.

## 작업 계약

1. 목표/완료조건: 위 AC 작성·중복 판별 기준을 `op-task` 규범에 반영하고 정합성을 검증한다.
2. 포함/제외 범위: `opal/skills/op-task/`의 상세 가이드·실행 지시·README를 포함한다. state-tool 파서 변경, 기존 TASK 소급 수정, 태스크 164 산출물 변경은 제외한다.
3. 변경 대상: `opal/skills/op-task/references/task-guide.md`, `opal/skills/op-task/SKILL.md`, `opal/skills/op-task/README.md`.
4. 결정/가정: 개수 제한은 두지 않는다. 한 AC의 단위는 관찰 하나가 아니라 독립적인 수용 결정 하나이며, 불가분한 성공·거부 경계는 한 AC에 함께 둘 수 있다. 남은 가정 없음.
5. 검증 방법: 문구·중복 정적 검색, 관련 state-tool 계약 테스트, `code-scan validate --changed`.
6. 예상 영향: TASK 작성 규범과 사용자 대면 설명을 갱신하고, 결정 배경은 brain concept로 동기화한다. 기획·아키텍처·보안·도구 스키마·기존 태스크에는 동작 변경이 없다.

## 승인 근거

- 방향 승인: “개수 제한보다는 AC를 작성하는 기준을 명확하게 해서 … AC 마다 겹치지 않은 핵심 요구사항으로 표현”
- 실행 승인: “알투가 직접 수정해줘”
- 지식 동기화 보정: “기존 하네스를 수정하는건데, 지식에 반영이 되어야 하지 않나?”

## 참조 문서와 제약

- `docs/PROJECT.md` — Framework 영역 문서 작업으로 분류한다.
- `docs/CONVENTIONS.md` — 규범은 owner 문서에만 두고 중복 원문을 만들지 않는다.
- `opal/skills/op-task/SKILL.md` — TASK 작성 실행 계약.
- `opal/skills/op-task/references/task-guide.md` — AC/C 상세 작성 기준 owner.
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` — AC/C를 검증 시나리오에 연결하는 소비자.
- `opal/core/references/harness/design-gate.md` — 모든 AC/C를 Work item과 시나리오에 연결하는 게이트 소비자.
- 배포본 `~/.opal/`을 직접 수정하지 않는다.

## 실행 기록

- 실행 ID: `run_77f77507-37e3-46a6-90e7-6c718bbdbce5`
- 현재 기록: `.opal/self-pm/run_77f77507-37e3-46a6-90e7-6c718bbdbce5.json`, `run/run-log-run_77f77507-37e3-46a6-90e7-6c718bbdbce5-*.jsonl`
- 상태: 실행 승인됨
