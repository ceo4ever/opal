# QA: PLAN -- wireframe-builder 개선 및 ui-designer 스킬 신규 개발

> 검토일: 2026-03-13 | 판정: ✅ Pass

## 1. 요약

wireframe-builder를 HTML 생성 도구에서 wireframe.md 설계 도구로 전환하고, 신규 ui-designer 스킬이 wireframe.md를 입력받아 React+shadcn/ui 기반 UI를 생성하는 2단계 파이프라인을 구축하는 계획이다. ui-designer는 프로토타입 모드(web-artifacts-builder 번들링 -> 단일 HTML)와 프로덕션 모드(Next.js App Router)를 지원하며, 두 모드에서 동일한 React+shadcn 컴포넌트 코드를 재활용한다. 구현 순서는 wireframe-builder 재작성 -> ui-designer 신규 -> 레지스트리/문서 업데이트 순이며, 변경 파일 5개(신규 1 + 수정 4)로 구성된다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| P-1 | 즉시 구현 가능성 | ✅ | YAML frontmatter, 프로세스 단계, wireframe.md 스키마, shadcn 규칙 참조 경로, web-artifacts-builder 연계 방식 등이 모두 구체적으로 명세되어 있어 바로 코딩 진입 가능 |
| P-2 | 의존성 순서 정합 | ✅ | wireframe-builder(스키마 정의) -> ui-designer(스키마 소비) -> 레지스트리/문서 순서가 올바름. 하위 레이어(계약)부터 상위 레이어(소비자) 순 |
| P-3 | RESEARCH 반영 | ✅ | RESEARCH의 5개 핵심 발견 사항(wireframe.md 스키마 계약, shadcn 매핑 자동화, web-artifacts-builder 활용, 기존 자산 보존, Critical Rules 내재화)이 PLAN에 모두 반영됨. 리스크 5건 중 4건이 PLAN 섹션 6에 대응 방안과 함께 포함 |
| P-4 | 파일 목록 일치 | ✅ | RESEARCH의 변경 필요 파일 5건(wireframe-builder, ui-designer, skills.md, CLAUDE.md, install-mac.sh)이 PLAN 섹션 1에 모두 포함. RESEARCH에서 "참조만"으로 표기된 파일(shadcn, web-artifacts-builder)도 PLAN에서 "영향 확인" 파일로 적절히 분류 |
| P-5 | 핵심 설계 구체성 | ✅ | wireframe-builder 4단계 프로세스, ui-designer 5단계 프로세스, wireframe.md 스키마 6개 섹션, shadcn 참조 경로 4단계, 서브 에이전트 위임 규칙이 모두 함수/클래스 수준의 명세에 해당하는 구체성을 갖춤 |
| P-6 | 테스트 전략 커버리지 | ⚠️ | T-1~T-8(문서/레지스트리 검증)은 충실하나, T-9~T-11(E2E 파이프라인)은 "현재 태스크에서는 검증하지 않음"으로 제외됨. TASK.md 성공 기준 5번째 항목인 "파이프라인 E2E: 정책서 -> wireframe-builder -> wireframe.md -> ui-designer -> 동작하는 UI 산출물"의 검증이 현 태스크 범위에서 빠져 있음 |

## 3. 지적 사항

### 3-1. install-mac.sh 행 번호 오차 (🔵 Info)

PLAN 섹션 3.3에서 install-mac.sh의 변경 대상 행을 "234행, 243행, 252행"으로 명시했으나, 실제 파일에서는 235행, 244행, 253행이다. 각각 1행씩 차이가 있다. 구현 시 행 번호가 아닌 패턴 매칭으로 수정하면 문제없으므로 경미한 사항이다.

### 3-2. E2E 파이프라인 테스트 제외 (🟡 Warning)

TASK.md 성공 기준에 "파이프라인 E2E: 정책서 -> wireframe-builder -> wireframe.md -> ui-designer -> 동작하는 UI 산출물"이 명시되어 있다. PLAN의 테스트 전략에서 T-9~T-11로 정의는 했으나 "현재 태스크에서는 검증하지 않음"으로 스코프 밖으로 뺐다. 이 태스크가 스킬 문서(.md) 작성만을 범위로 하므로 E2E 실행 테스트를 제외한 판단 자체는 합리적이나, TASK.md 성공 기준과의 괴리를 TODO 단계에서 명시적으로 정리할 필요가 있다(예: "E2E 검증은 별도 태스크 또는 수동 검증으로 수행" 등).

### 3-3. opal/core/references/skills.md vs ~/.opal/references/skills.md 경로 혼재 (🔵 Info)

TASK.md와 RESEARCH.md에서는 `~/.opal/references/skills.md`(배포 경로)를 참조하고, PLAN.md에서는 `opal/core/references/skills.md`(소스 경로)를 사용한다. PLAN이 소스 저장소 기준으로 작성한 것이므로 올바른 판단이지만, RESEARCH에서도 이 파일을 "소스 저장소"와 "배포 경로" 양쪽으로 기재하고 있어 혼동 여지가 있다. 구현 시 소스 경로를 수정하면 install-mac.sh가 배포 경로로 복사하므로 실질적 문제는 없다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | wireframe-builder 개선 요구사항 5건(분석 수행, 화면 목록 도출, 네비게이션 흐름, shadcn 매핑, wireframe.md 생성) -> PLAN 3.1의 4단계 프로세스에 모두 포함 | ✅ |
| TASK.md | ui-designer 요구사항 7건(wireframe.md 파싱, React 코드 생성, 프로토타입 모드, 프로덕션 모드, 컴포넌트 재활용, shadcn 규칙 준수, web-artifacts-builder 활용) -> PLAN 3.2의 5단계 프로세스에 모두 포함 | ✅ |
| TASK.md | 레지스트리 업데이트 요구사항 3건(skills.md wireframe-builder 변경, skills.md ui-designer 추가, CLAUDE.md 반영) -> PLAN 3.3에 모두 포함 | ✅ |
| TASK.md | 제약 조건 4건(스킬 구조 준수, wireframe.md 구조화, shadcn Critical Rules 참조, install-mac.sh 호환) -> PLAN에 모두 반영 | ✅ |
| RESEARCH.md | 변경 필요 파일 5건 -> PLAN 구현 범위에 모두 포함 | ✅ |
| RESEARCH.md | wireframe.md 스키마 6개 섹션 -> PLAN 3.1에 동일하게 반영 | ✅ |
| RESEARCH.md | 핵심 발견 사항 5건 -> PLAN에 모두 설계로 구체화 | ✅ |
| RESEARCH.md | 리스크 4건 -> PLAN 섹션 6에 4건 반영 + 기존 사용자 마이그레이션 리스크 1건 추가 | ✅ |
| RESEARCH.md | web-artifacts-builder 파이프라인 채택 결정 -> PLAN의 ui-designer Phase 2/5에 반영 | ✅ |

## 5. 판정

**✅ Pass**

6개 검증 항목 중 5개 Pass, 1개 Warning이다. Warning 항목(E2E 테스트 제외)은 스킬 문서 작성이라는 태스크 특성상 합리적인 스코프 결정이며, TODO 단계에서 E2E 검증 계획을 명시적으로 정리하면 충분하다. TASK.md의 모든 요구사항과 RESEARCH.md의 분석 결과가 PLAN에 빠짐없이 반영되어 있고, 즉시 구현에 착수할 수 있는 수준의 구체성을 갖추고 있다.
