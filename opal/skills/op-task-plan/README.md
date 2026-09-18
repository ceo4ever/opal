# op-task-plan

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-project`가 PLAN 단계에서 디스패치합니다.

TASK.md를 분석하여 도메인 무관 실행 계획(PLAN.md)을 작성하는 범용 계획 수립 스킬입니다.

## 역할

워커 에이전트의 컨텍스트에서 실행되며, `personas/generalist-architect.md` 페르소나를 사용합니다. 개발 파일럿 전용인 `op-dev-plan`과 달리 코드·문서·설정 등 도메인을 가리지 않으며, ANALYSIS.md 유무에 따른 분기나 `execution-plan.json` 생성, FE/BE 영역 태그, 단순/복잡 모드 판별이 없습니다. 항상 direct 실행 방식으로 동작합니다.

Glob/Grep/Read뿐 아니라 WebSearch, 관련 OPAL 스킬 SKILL.md, 프로젝트 docs, context7 등 모든 수단을 동원해 추측 없이 실제 현황을 조사한 뒤, 신규 생성/수정/삭제 파일 목록과 의존성 기반 구현 순서를 확정합니다. 파일별 핵심 변경 사항과 설계 결정을 명세하고, 실행 체크리스트(Step 단위, 파일·작업 내용·완료 기준·테스트·의존 명시)와 QA 체크리스트(기능/일관성/문서 품질)를 작성합니다.

워커는 검증을 직접 수행하지 않습니다. 문서 QA(요구사항→설계 검토)는 별도 QA Gate 단계 없이 PM이 PM Gate에서 `op-task-qa`를 검증 기준 라이브러리로 참조해 직접 수행합니다.

## 입력

- TASK.md

## 출력

`PLAN.md` — 다음 절로 구성됩니다.

1. 현황 조사(참조 문서 표, 관련 파일 표, 현재 상태, 영향 범위)
2. 구현 계획(파일 변경 계획, 구현 순서, 핵심 설계)
3. 실행 체크리스트(Step별 파일·작업 내용·완료 기준·테스트·의존)
4. QA 체크리스트(기능/일관성/문서 품질)
5. 리스크 및 대응

인용은 `opal/core/references/harness/citation-rules.md`를 따르며, 재해석 여지가 있는 제약은 `[MUST]` 포맷으로 기재합니다.

## 호출 시점

오케스트레이터(`opal-pilot-project`)가 PLAN 단계를 디스패치할 때 실행됩니다. 서브 에이전트 사용이 불가능한 플랫폼에서는 오케스트레이터가 직접 이 스킬을 따릅니다.

## 관련 문서

- `opal/skills/op-task-plan/references/plan-guide.md`
- `opal/skills/op-task-plan/personas/generalist-architect.md`
