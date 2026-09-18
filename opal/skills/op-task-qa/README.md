# op-task-qa

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-project`가 PM Gate 문서검증 시 참조합니다.

도메인 무관 산출물(TASK.md, PLAN.md 등)의 문서 QA 검증 기준을 제공하는 범용 문서 QA 검증 기준 라이브러리입니다.

## 역할

`op-task`·`op-task-plan`·`op-task-execute`와 함께 범용 단계 스킬 계열에 속하지만, 이 스킬은 별도 워커로 디스패치되어 실행되는 것이 아니라 **PM Gate 문서검증을 수행하는 PM(오케스트레이터)이 참조하는 검증 기준 라이브러리**입니다. 별도 QA Gate 단계나 QA 에이전트 디스패치 없이, PM이 PM Gate에서 직접 이 스킬의 기준을 적용합니다.

동작 검증(TEST / TEST-SCENARIO / verify, 독립·불변 영역)과는 무관하며, 요구사항→설계 검토라는 문서 QA만 다룹니다. 코드 개발 문서 QA는 `op-dev-qa`가 별도로 담당합니다.

PM은 `references/qa-general-guide.md`를 읽고, 검증 대상 산출물과 이전 단계 산출물(TASK 단계는 TASK.md, PLAN 단계는 PLAN.md+TASK.md, EXECUTE 단계는 실행 결과+PLAN.md+TASK.md)을 모두 읽어 완전성·정합성·명확성·실행 가능성 원칙으로 항목별 판정을 수행합니다. TASK는 T-1~T-4, PLAN은 GP-1~GP-6, EXECUTE는 GE-1~GE-3 검증 ID를 사용합니다. 검증 통과 항목은 해당 시점 체크리스트(PLAN 단계는 TASK.md 요구사항 체크박스, EXECUTE 단계는 PLAN.md §3·§4 체크리스트)를 `[x]`로 갱신합니다.

## 입력

| 입력 | 설명 |
|------|------|
| `stage` | 검토 대상 단계(`TASK` / `PLAN` / `EXECUTE`) |
| `task_path` | 태스크 폴더 경로 |
| `artifact_path` | 검증 대상 산출물 경로 |

## 출력

`tasks/{NNN}-{태스크명}/QA-{단계}.md` — 요약, 검증 결과 표, 지적 사항(Critical/Warning/Info), 교차 참조 검증, 최종 판정(Pass / Needs Revision)으로 구성됩니다. Critical 1개 이상 또는 Warning 3개 이상이면 Needs Revision입니다.

## 호출 시점

PM이 PM Gate에서 TASK/PLAN/EXECUTE 단계 산출물의 문서 QA를 수행할 때 참조합니다. 검증 결과는 QA-{단계}.md로 기록되어 PM Gate 판정에 반영됩니다.

## 관련 문서

- `opal/skills/op-task-qa/references/qa-general-guide.md`
- `opal/skills/op-task-qa/personas/qa-engineer.md`
