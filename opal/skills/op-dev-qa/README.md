# op-dev-qa

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-dev`·`opal-pilot-dev-wireframe`가 PM Gate 문서검증 시 참조합니다.

Dev 문서 QA(요구사항→설계 검토)의 검증 기준을 제공하는 라이브러리 스킬입니다.

## 역할

동작 검증(TEST/TEST-SCENARIO/verify)과는 무관한 **문서 QA**의 검증 기준을 정의합니다. 별도 QA Gate 단계나 QA 에이전트 디스패치 없이, PM(오케스트레이터)이 PM Gate 문서검증 시 이 스킬의 검증 기준을 직접 참조합니다. 산출물 작성자와 독립된 시니어 QA 엔지니어 관점에서 완전성·정합성·명확성·실행 가능성을 검토합니다.

## 입력

- `stage` (`ANALYSIS`/`PLAN`/`WIREFRAME`/`EXECUTE-UI`), `mode`, `task_path`, `artifact_path`
- `changed_files` (EXECUTE-UI 검증 시 필수)
- 단계별로 `qa-dev-guide.md`(ANALYSIS/PLAN) 또는 `qa-wireframe-guide.md`(WIREFRAME/EXECUTE-UI) 참조

## 출력

- PM Gate 판정 (`Pass` / `Needs Revision`)
- `tasks/{NNN}-{태스크명}/QA-{단계}.md`는 pipeline이 명시 요구하거나 legacy 태스크일 때만 생성
- 신규 sdlc-v2 태스크에서는 체크리스트를 갱신하지 않음 (단계 상태는 `state.json`, 시나리오 결과·증거는 `test-scenario.json`이 소유)
- 검증 ID: sdlc-v2 ANALYSIS는 RA-1~RA-6, PLAN은 PP-1~PP-7, TEST-SCENARIO는 TS-1~TS-6, WIREFRAME은 W-1~W-5, EXECUTE-UI는 E-1~E-6

## 호출 시점

`opal-pilot-dev`·`opal-pilot-dev-wireframe`의 PM Gate 문서검증 시점에 참조됩니다.

## 관련 문서

- `opal/core/references/harness/citation-rules.md`
- 페르소나: `opal/skills/op-dev-qa/personas/qa-engineer.md`
- `opal/skills/op-dev-qa/references/qa-dev-guide.md`, `qa-wireframe-guide.md`
