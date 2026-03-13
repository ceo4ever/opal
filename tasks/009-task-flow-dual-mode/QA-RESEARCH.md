# QA: RESEARCH — task-flow Full Task / Short Task 듀얼 모드 분리

> 검토일: 2026-03-13 | 판정: ⚠️ Needs Revision

## 1. 요약

task-flow 스킬을 Full Task(5단계)와 Short Task(3단계) 듀얼 모드로 분리하기 위한 코드베이스 분석 결과이다. SKILL.md를 단일 파일 내 분기 방식(선택지 A)으로 설계하고, Short Task는 RESEARCH+PLAN+TODO를 하나의 PLAN.md로 통합하는 구조를 제안한다. QA 에이전트 호출 시점을 Full/Short 모드별로 차별화하며, TASK/TODO 단계의 QA를 양쪽 모두 생략한다. 변경 대상은 SKILL.md(전면), QA 에이전트(3개 플랫폼), references 가이드(4개), CLAUDE.md이며, task-flow-planner와 task-flow-test는 변경 불필요로 판단하였다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R-1 | TASK 커버리지 | ⚠️ | R1~R5 전체를 다루고 있으나, R1.6의 Full Task 체크리스트 갱신 형식을 TASK와 다르게 해석함 (아래 지적 사항 참조) |
| R-2 | 코드 실독 여부 | ✅ | 12개 파일에 대해 줄 수를 기재하여 실제 파일 읽기를 입증. 줄 수가 실측치와 1줄 이내로 일치 (SKILL.md 472 vs 실측 471 등) |
| R-3 | 변경 파일 완전성 | ✅ | SKILL.md, references 4개, QA 에이전트 3개 플랫폼, CLAUDE.md를 모두 식별. 간접 영향으로 opal/core/references/skills.md도 언급 |
| R-4 | 영향 범위 분석 | ✅ | 직접 영향(SKILL.md, QA 에이전트, references, CLAUDE.md)과 간접 영향(planner, test, opal skills.md)을 구분하여 분석. 의존성 맵 다이어그램도 제공 |
| R-5 | 리스크 식별 | ✅ | 3가지 리스크(SKILL.md 회귀, 3개 플랫폼 동기화 누락, 모드 판별 오류)를 영향도와 대응 방안까지 기술 |
| R-6 | 분석 깊이 적정성 | ✅ | 기능 개선 작업에 맞는 중간 깊이. 현재 구현 패턴 분석, 설계 선택지 비교, QA 호출 맵 변경 전/후 비교 등 적절한 수준 |

## 3. 지적 사항

### 🔴 Critical

**R1.6 체크리스트 갱신 형식 불일치**

TASK.md R1.6은 Full Task에서 TODO.md 체크리스트를 `[ ]` -> `[x]`로 갱신하라고 명시한다. 그러나 RESEARCH.md 섹션 3.4에서는 Full Task가 기존 방식(`- **상태**: ⬜ 대기` -> `- **상태**: ✅ 완료`)을 유지한다고 기술하였다. 이는 TASK 요구사항과 직접 충돌한다.

TASK.md의 의도는 Full Task도 Short Task와 동일한 `[ ]`/`[x]` 마크다운 체크박스 형식으로 통일하여 TODO.md 포맷을 간소화하는 것으로 읽힌다. RESEARCH가 이를 "기존 방식 유지"로 해석한 것은 TASK 요구사항을 놓친 것이다.

**수정 필요**: 섹션 3.4의 Full Task 체크리스트 갱신 규칙을 TASK.md R1.6에 맞춰 `[ ]` -> `[x]` 형식으로 수정하거나, TASK.md의 의도가 다르다면 TASK.md와의 합의가 필요하다. 이 결정은 TODO.md Part A의 Step 포맷 설계에도 영향을 미치므로 PLAN 진행 전 확정해야 한다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | R1(Full Task) 요구사항 7개 항목 반영 여부 | ⚠️ R1.6 체크리스트 형식 불일치 |
| TASK.md | R2(Short Task) 요구사항 6개 항목 반영 여부 | ✅ 통합 PLAN 구조, 체크리스트 갱신 규칙 모두 분석됨 |
| TASK.md | R3(모드 판별) 요구사항 4개 항목 반영 여부 | ✅ 판별 위치, 오버라이드, 에스컬레이션 규칙 모두 설계됨 |
| TASK.md | R4(산출물 구조) 요구사항 3개 항목 반영 여부 | ✅ 파일 목록에서 모드별 산출물 구분 확인 가능 |
| TASK.md | R5(파일 변경 범위) 요구사항 5개 항목 반영 여부 | ✅ 관련 파일 목록 테이블에서 모두 식별됨 |
| TASK.md | 제약 조건 4개 항목 반영 여부 | ✅ 핵심 원칙 유지, 에이전트 호환성, 3개 플랫폼, references 수정 모두 언급 |

## 5. 판정

**⚠️ Needs Revision**

R1.6 Full Task 체크리스트 갱신 형식이 TASK 요구사항과 충돌하는 Critical 이슈 1건이 존재한다. TODO.md의 Step 포맷 설계에 직접 영향을 미치므로, PLAN 단계 진행 전 해소가 필요하다. 해당 항목 수정 후 나머지 분석 품질은 양호하다.
