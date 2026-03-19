# QA: PLAN — 테스트 도구 레지스트리 설계 및 TEST-SCENARIO 통합

> 검토일: 2026-03-19 | 판정: ⚠️ Needs Revision

## 1. 요약

프로젝트별 테스트 도구를 선언적으로 관리하는 `.opal/test-tools.yaml` 레지스트리를 신규 설계하고, TEST-SCENARIO 작성 시점(task-flow-agent)에 도구를 사전 결정하도록 현행 흐름을 개선하는 계획이다. 변경 대상 파일은 4개(스키마 신규 2개, 가이드 수정 1개, 에이전트 수정 1개)로 Short Task 범위에 부합한다. 핵심 설계인 YAML 스키마 전체 구조, 도구 매핑 테이블, Step 1-b 추가 내용, fallback 로직이 모두 구체적으로 명시되어 있다. 단, 스키마 내 `global` 섹션과 `tools.security` 섹션의 gitleaks 중복 정의가 설계 의도를 명확히 하지 않으며, Step 4 산출물의 저장 위치가 섹션 간 불일치한다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| SP-1 | 코드 분석 충분성 | ✅ | 3개 파일 실독 확인, 현재 문제점 4가지 및 영향 범위(호출자/피호출자) 명시 |
| SP-2 | 구현 계획 구체성 | ⚠️ | 변경 파일 4개 명시, 각 설계 상세 기술됨. 단, gitleaks 중복 정의 설계 의도 불명확; TEST-SCENARIO.md 템플릿 도구 필드 변경이 체크리스트에 미기재 |
| SP-3 | 체크리스트 완전성 | ⚠️ | TASK.md 요구사항 3개 모두 Step으로 대응됨. 단, 실행 체크리스트에 TEST-SCENARIO.md 템플릿 수정 항목이 명시적으로 없음 (Step 2에 암묵 포함 추정) |
| SP-4 | QA 항목 커버리지 | ✅ | 기능(5개)/회귀(4개)/코드 품질(3개) 테스트 항목이 요구사항을 충분히 커버 |
| SP-5 | Short Task 적정성 | ✅ | 변경 파일 4개, Step 4개 — Short Task 기준(5개 이하) 충족 |

## 3. 지적 사항

### 심각도 분류

#### 🟡 Warning 1: gitleaks 중복 정의

PLAN 섹션 2의 `.opal/test-tools.yaml` 스키마 예시에서 `global` 섹션과 `tools.security` 섹션에 gitleaks가 동일하게 정의되어 있다.

```yaml
global:
  - name: gitleaks
    ...
tools:
  security:
    - name: gitleaks
      purpose: 시크릿 스캔 (global 참조)  # "global 참조"라고 표기되어 있으나 중복 선언
```

설계 의도가 "global은 스택 무관 필수 도구, tools.security는 카테고리별 참조 포인터" 라면, `tools.security`에서 gitleaks를 별도 선언하지 않고 global 참조 방식을 스키마에 명세해야 한다. 현재 예시는 중복 선언으로 보이며, 이를 그대로 구현하면 task-flow-test가 동일 도구를 두 번 실행할 가능성이 있다. 스키마 레퍼런스 문서(Step 4)에 이 관계를 명확히 정의해야 한다.

#### 🟡 Warning 2: TEST-SCENARIO.md 템플릿 수정이 실행 체크리스트에 누락

PLAN 섹션 2 핵심 설계에 TEST-SCENARIO.md 템플릿의 "도구" 필드 변경이 명시되어 있다.

- 기존: `| 도구 | _{task-flow-test가 채움}_ |`
- 변경: `| 도구 | {task-flow-agent가 결정 / task-flow-test가 검증} |`

그러나 실행 체크리스트(섹션 3)에서 이 변경 작업이 명시적으로 없다. Step 2(test-scenario-guide.md 수정)에 암묵적으로 포함될 수 있지만, `test-scenario-guide.md`와 TEST-SCENARIO.md 템플릿은 동일 파일 내에 있으므로 실질적으로 포함된다. 그러나 체크리스트 항목이 명시적이지 않아 EXECUTE 시 누락 위험이 있다.

**권장**: Step 2 체크리스트 항목에 "TEST-SCENARIO.md 템플릿 '도구' 필드 힌트 변경" 명시 추가.

#### 🔵 Info 1: Step 4 산출물 저장 위치 표현 불일치

섹션 2 변경 파일 목록에는 `opal/core/references/` 하위 `test-tools-schema.yaml`로 명시되어 있으나, 실행 체크리스트 Step 4에는 "적절한 위치에"라고 추상적으로 표현되어 있다. EXECUTE 단계에서 혼선 없이 `opal/core/references/`를 선택하면 충분하나, 현재 `opal/core/references/`는 에이전트/MCP/스킬 목록용 파일들이 위치한 공간이므로 스키마 레퍼런스를 같은 위치에 두는 것이 아키텍처 정합성 측면에서 재검토 여지가 있다. (`opal/core/schemas/` 또는 `opal/templates/` 하위도 고려 가능)

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | 요구사항 3개 (.opal/test-tools.yaml 스키마, test-scenario-guide.md 개선, task-flow-test AGENT.md 개선) 모두 PLAN에 반영됨 | ✅ |
| TASK.md 제약 조건 | 기존 TEST-SCENARIO.md 구조 유지(하위 호환) — PLAN에서 "기존 구조 유지" 명시됨 | ✅ |
| TASK.md 제약 조건 | 도구 자동 설치 사용자 확인 후 수행 — PLAN Step 1-b 및 task-flow-test 변경 포인트에 "사용자에게 install 명령 제안 후 확인 요청" 명시됨 | ✅ |
| TASK.md 제약 조건 | 글로벌 기본값 + 프로젝트 오버라이드 구조 — 우선순위(프로젝트 파일 > 글로벌 기본값 > 추론 fallback) 명시됨 | ✅ |
| test-scenario-guide.md (실독) | 현재 "도구" 필드가 `_{task-flow-test가 채움}_`으로 되어 있음 확인 — PLAN의 변경 계획과 정합 | ✅ |
| task-flow-test AGENT.md (실독) | Step 1의 "프로젝트 설정 파일 기반" 표현 모호성 확인 — PLAN의 문제 진단과 정합 | ✅ |

## 5. 판정

**⚠️ Needs Revision**

🟡 Warning 2개가 존재한다. gitleaks 중복 정의 의도가 스키마 레퍼런스 문서에 명확히 문서화되어야 하고, 실행 체크리스트 Step 2에 TEST-SCENARIO.md 템플릿 필드 변경이 명시적으로 추가되어야 한다. 두 항목 모두 EXECUTE 중 누락 또는 설계 오류로 이어질 수 있으므로 수정 권장. 단, 캡틴 판단에 따라 현행 계획으로 진행도 가능하다.
