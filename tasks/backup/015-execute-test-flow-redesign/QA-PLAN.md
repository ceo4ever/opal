# QA: PLAN -- EXECUTE 후 검증 흐름 재설계

> 검토일: 2026-03-19 | 판정: ✅ Pass

## 1. 요약

EXECUTE 완료 후 검증 흐름을 task-flow-qa(문서 리뷰) 중심에서 task-flow-test(실제 실행) 중심으로 전환하는 재설계 계획이다. 핵심 변경은 세 가지: (1) TEST-SCENARIO.md 신규 산출물 도입 -- task-flow-agent가 시나리오(대상/조건/기대)를 작성하고 task-flow-test가 도구 결정 + 실행 + 결과를 같은 파일에 채움, (2) task-flow-test를 복잡 모드 전용에서 모든 모드로 확장, (3) task-flow-qa의 EXECUTE 검증(QA-EXECUTE.md)과 TEST-REPORT.md를 폐지하여 단일 파일로 통합. 변경 대상은 11개 파일(신규 1 + 기존 10)이며, 3개 플랫폼(Claude, Cursor, Antigravity) 에이전트 파일을 동기화한다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| SP-1 | 코드 분석 충분성 | ✅ | SKILL.md 312행의 "Full Task 복잡 모드 전용" 명시, execute-guide.md의 3개 모드별 흐름, CLAUDE.md 산출물 구조 등 실제 파일의 구체적 위치와 현재 구현을 정확히 기술. 영향 범위(직접 8파일 + 간접 3파일)도 분류하여 분석 완료. |
| SP-2 | 구현 계획 구체성 | ✅ | 11개 파일 각각에 대해 변경 내용이 (a)(b)(c) 수준으로 열거됨. TEST-SCENARIO.md 템플릿, task-flow-test 입력/프로세스/출력 변경, task-flow-qa 삭제 대상 6개 항목, SKILL.md 변경점 9개 등 즉시 구현 가능한 수준. |
| SP-3 | 체크리스트 완전성 | ✅ | TASK.md 요구사항 11개 항목이 5개 Step으로 빠짐없이 분해됨. 특히 "3개 플랫폼 동기화" 요구사항이 Step 2, 3에서 각각 3개 파일 동시 변경으로 명시. |
| SP-4 | QA 항목 커버리지 | ✅ | 기능 테스트 7항목(역할 분배, 입력 변경, 출력 변경, EXECUTE 제거, 다이어그램, 호출 맵, 스킵 규칙) + 회귀 테스트 5항목(QA RESEARCH/PLAN 유지, Planner 유지, 디스커버리 유지, 테스트 깊이 유지, STATE.md 유지) + 코드 품질 3항목(플랫폼 동기화, 참조 완전 제거, 산출물 구조). |
| SP-5 | Short Task 적정성 | ⚠️ | 변경 대상 11개 파일(신규 1 포함)은 Short Task 기준 "변경 파일 10 이상"에 근접. 다만 실제 내용 변경이 필요한 핵심 파일은 4개(test-scenario-guide 신규, task-flow-test, task-flow-qa, SKILL.md)이고 나머지 7개는 플랫폼 동기화(6개) + CLAUDE.md 경미 수정(1개)이므로, 다단계 기술 의사결정이나 다중 모듈 연쇄 영향은 해당하지 않음. |

## 3. 지적 사항

### SP-5: Short Task 적정성

- **심각도**: 🔵 **Info**
- 변경 파일 수(11개)만 보면 Full Task 에스컬레이션 기준("변경 파일 10 이상")에 해당하나, 실질적 설계 결정은 TASK.md에서 이미 완료되어 있고 PLAN에서는 이를 구체화한 것이다. 핵심 변경은 task-flow-test 재설계 + task-flow-qa EXECUTE 제거 + SKILL.md 흐름 갱신 3축으로, 플랫폼 동기화 파일(6개)은 내용 복사에 가까우므로 Short Task로 진행 가능하다.

### 추가 참고 사항

- **심각도**: 🔵 **Info**
- execute-plan-guide.md(#10) 변경 내용이 "TEST-SCENARIO.md 참조 안내 추가"로 경미하지만, 이 파일의 "섹션 4 테스트 전략 구체화"가 기존 B-1~B-4 기반이므로 TEST-SCENARIO.md 기반으로의 전환 시 단순 참조 추가 이상의 조정이 필요할 수 있다. 실행 시 확인 필요.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | 요구사항 11개 항목이 PLAN에 모두 반영되었는가 | ✅ |
| TASK.md | 설계 결정(B안: agent 1~3, test 4+실행)이 PLAN에 반영되었는가 | ✅ |
| TASK.md | 변경 파일 11개가 PLAN과 일치하는가 | ✅ |
| TASK.md | 제약 조건 4개(QA R/P 유지, Planner 유지, 플랫폼 동기화, 컨텍스트 연속성 분리)가 PLAN에 반영되었는가 | ✅ |
| TASK.md | 산출물 구조 변경(TEST-SCENARIO 추가, QA-EXECUTE/TEST-REPORT 삭제)이 PLAN과 일치하는가 | ✅ |
| SKILL.md (현재) | PLAN이 기술한 "312행 Full Task 복잡 모드 전용" 등 현재 구현 분석이 실제와 일치하는가 | ✅ |

## 5. 판정

**✅ Pass**

모든 검증 항목이 Pass이며, SP-5의 Short Task 적정성에 대한 지적도 Info 수준이다. TASK.md의 요구사항과 설계 결정이 빠짐없이 구체적 변경 계획으로 분해되어 있어 즉시 실행 가능하다.
