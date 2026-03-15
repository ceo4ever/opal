# QA: PLAN -- EXECUTE 완료 시 QA 체크리스트 갱신 + 완료 리포트 생성 규칙 추가

> 검토일: 2026-03-15 | 판정: Pass

## 1. 요약

EXECUTE 완료 시 QA 체크리스트(Full: TODO.md Part B / Short: PLAN.md 섹션 4)의 체크박스를 워커가 직접 검증하고 갱신하는 규칙을 추가하고, 태스크 완료 시 DONE.md 완료 리포트를 생성하는 규칙을 task-flow에 정식 반영하는 계획이다. 변경 대상은 SKILL.md, execute-guide.md, CLAUDE.md 3개 파일이며, 기존 워크플로우 흐름(게이트 체크포인트, QA 에이전트 호출 순서)은 변경하지 않는다. DONE.md 템플릿은 기존 tasks/011 실례를 기반으로 표준화한다. QA 체크리스트 갱신 시점은 "모든 실행 Step 완료 후, QA 에이전트 호출 전"으로 설정하여 QA 에이전트가 갱신 결과를 참조할 수 있게 한다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| SP-1 | 코드 분석 충분성 | Pass | 3개 파일 모두 라인 번호 수준까지 실독. SKILL.md의 Full 단순/복잡/Short 모드, execute-guide.md의 체크리스트 갱신/실행 흐름/품질 체크리스트, CLAUDE.md 산출물 구조까지 구체적으로 분석. 영향 범위(상위: 오케스트레이터, 하위: 워커, 참조: CLAUDE.md)도 식별됨 |
| SP-2 | 구현 계획 구체성 | Pass | 3개 파일 각각의 변경 내용이 (a)(b)(c)... 수준으로 세분화되어 있음. DONE.md 템플릿, QA 체크리스트 갱신 규칙, 생성 시점/주체가 모두 명시됨 |
| SP-3 | 체크리스트 완전성 | Pass | TASK.md R1(QA 체크리스트 갱신) -> Step 1/3, R2(DONE.md 생성 규칙) -> Step 2/3, R3(DONE.md 템플릿) -> Step 2, R4(산출물 구조에 DONE.md 추가) -> Step 2/4. 4개 요구사항이 모두 4개 Step에 분해됨 |
| SP-4 | QA 항목 커버리지 | Pass | 기능 9항목(3개 모드별 QA 갱신, DONE.md 규칙/템플릿/저장구조, guide 연동 3항목), 회귀 3항목(게이트 흐름 보존, 기존 체크리스트 유지, 기존 DONE.md 호환), 품질 3항목(Full/Short 일관성, guide-SKILL 정합성, CLAUDE-SKILL 정합성) 총 15항목 |
| SP-5 | Short Task 적정성 | Pass | 변경 파일 3개, 모두 문서 수정(마크다운), 단일 모듈(task-flow) 내 작업. Short Task에 적합 |

## 3. 지적 사항

지적 사항 없음

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | R1(QA 체크리스트 갱신 규칙) -- PLAN 섹션 2 "QA 체크리스트 갱신 규칙" + Step 1/3에서 커버 | Pass |
| TASK.md | R2(DONE.md 생성 규칙) -- PLAN 섹션 2 "DONE.md 생성 규칙" + Step 2/3에서 커버 | Pass |
| TASK.md | R3(DONE.md 템플릿 정의) -- PLAN 섹션 2 "DONE.md 템플릿"에 전체 구조 명시 | Pass |
| TASK.md | R4(산출물 저장 구조에 DONE.md 추가) -- Step 2(SKILL.md), Step 4(CLAUDE.md)에서 커버 | Pass |
| TASK.md | 제약 조건: 기존 워크플로우 흐름 변경 금지 -- PLAN 영향 범위 분석에서 "QA 에이전트 호출, 게이트 체크포인트 순서는 변경하지 않음" 명시 | Pass |
| TASK.md | 제약 조건: QA 체크리스트 갱신은 워커 수행 -- PLAN에서 주체를 "EXECUTE 워커"로 명시, DONE.md 생성 주체는 "오케스트레이터"로 분리 | Pass |
| tasks/011 DONE.md | DONE.md 템플릿 호환성 -- 기존 실례의 섹션(완료 요약, 변경 파일, 핵심 변경, QA 결과, 산출물 목록)이 템플릿에 모두 포함됨 | Pass |

## 5. 판정

**Pass**

5개 Short Task PLAN 검증 항목 모두 통과. TASK.md의 4개 요구사항과 2개 제약 조건이 빠짐없이 반영되어 있으며, 기존 tasks/011 DONE.md와의 호환성도 확인됨.
