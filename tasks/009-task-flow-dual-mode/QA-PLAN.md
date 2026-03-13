# QA: PLAN -- task-flow Full Task / Short Task 듀얼 모드 분리

> 검토일: 2026-03-13 | 판정: Pass

## 1. 요약

task-flow 스킬을 Full Task(5단계)와 Short Task(3단계) 듀얼 모드로 분리하는 구현 계획이다. SKILL.md를 단일 파일 내 분기 방식(선택지 A)으로 재구성하고, Short Task 전용 통합 PLAN 템플릿을 정의한다. 구현 순서는 SKILL.md(핵심) -> references 가이드 4개 -> QA 에이전트 3개 플랫폼 -> CLAUDE.md 순이며, 총 9개 파일을 수정한다. Full Task의 TASK/TODO 단계에서 QA를 생략하고, Short Task에서는 RESEARCH/TODO를 PLAN에 통합하여 오버헤드를 줄인다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| P-1 | 즉시 구현 가능성 | Pass | SKILL.md 구조 트리, Short Task PLAN 템플릿(전체 마크다운), TODO 체크박스 전후 비교, QA 에이전트 변경 설계가 구체적으로 명세되어 바로 구현 가능 |
| P-2 | 의존성 순서 정합 | Pass | SKILL.md(핵심) -> references 가이드 -> QA 에이전트(claude 우선) -> 동기화(cursor/antigravity) -> CLAUDE.md 순서로 하위부터 상위로 진행 |
| P-3 | RESEARCH 반영 | Pass | RESEARCH의 3가지 리스크(회귀, 동기화 누락, 판별 오류)와 설계 결정(선택지 A)이 PLAN 섹션 6에 모두 반영됨 |
| P-4 | 파일 목록 일치 | Pass | RESEARCH의 "변경 필요" 9개 파일이 PLAN 수정 파일 9개와 정확히 일치. RESEARCH 간접 영향의 opal/core/references/skills.md는 아래 Info 참조 |
| P-5 | 핵심 설계 구체성 | Pass | 문서 수정 태스크에 맞게 구조 트리, 템플릿, 검증 기준 테이블 등으로 명세. 함수 시그니처 대신 마크다운 구조가 제시된 것이 적절 |
| P-6 | 테스트 전략 커버리지 | Pass | 6개 검증 항목이 TASK.md R1~R5 요구사항을 모두 커버. 동적 테스트 대신 문서 정합성 검증으로 대체한 판단이 타당 |

## 3. 지적 사항

### [Info] opal/core/references/skills.md 업데이트 미언급

RESEARCH 섹션 2 "간접 영향"에서 `opal/core/references/skills.md`의 task-flow 스킬 설명 업데이트 가능성이 언급되었으나, PLAN의 수정 파일 목록이나 영향 확인 목록에 포함되지 않았다. RESEARCH 자체에서도 "트리거 키워드 동일"로 변경 불필요에 가까운 것으로 판단했으므로 진행에 영향은 없으나, EXECUTE 완료 후 해당 파일의 description 갱신 필요 여부를 최종 점검하는 것을 권장한다.

### 심각도 분류
- [Info] opal/core/references/skills.md -- 참고 사항, 진행에 영향 없음

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | R1(Full Task 파이프라인)이 PLAN 3.2 다이어그램 및 3.6 QA 호출 시점에 반영 | Pass |
| TASK.md | R2(Short Task 파이프라인)가 PLAN 3.2 다이어그램 및 3.4 통합 PLAN 템플릿에 반영 | Pass |
| TASK.md | R3(모드 판별)이 PLAN 3.3 모드 판별 로직에 5개 조건 + 오버라이드 + 에스컬레이션 포함 | Pass |
| TASK.md | R4(산출물 구조)가 PLAN 3.1 SKILL.md 구조의 "산출물 저장 구조 (Full/Short 분기)"에 반영 | Pass |
| TASK.md | R5(파일 변경 범위)가 PLAN 수정 파일 9개에 모두 포함 | Pass |
| RESEARCH.md | 설계 결정(선택지 A: 단일 SKILL.md 분기)이 PLAN 3.1에 채택 | Pass |
| RESEARCH.md | 3가지 리스크가 PLAN 섹션 6에 동일 항목으로 반영 | Pass |
| RESEARCH.md | 변경 불필요 파일(planner, test, execute-plan-guide)이 PLAN "영향 확인" 목록에 포함 | Pass |

## 5. 판정

**Pass**

6개 검증 항목 모두 Pass이며, Info 수준 지적 1건(opal/core/references/skills.md 갱신 여부)만 존재한다. TASK.md의 모든 요구사항(R1~R5)과 RESEARCH.md의 설계 결정 및 리스크가 빠짐없이 PLAN에 반영되었다. 다음 단계(TODO)로 진행 가능하다.
