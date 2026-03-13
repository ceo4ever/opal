# QA: TASK — wireframe-builder 개선 및 ui-designer 스킬 신규 개발

> 검토일: 2026-03-13 | 판정: ⚠️ Needs Revision

## 1. 요약

wireframe-builder 스킬을 현재의 단일 HTML 와이어프레임 직접 생성 방식에서, 정책서/요구사항을 분석하여 구조화된 wireframe.md를 산출하는 UI 분석·설계 도구로 전환하고, 이를 입력으로 받아 shadcn/ui + Next.js 기반 UI를 구현하는 ui-designer 스킬을 신규 개발하는 것이 목표이다. 분석→설계→구현의 체계적 파이프라인 구축을 지향하며, 기존 프레임워크 스킬 구조와 설치 체계를 준수한다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| T-1 | 작업 목표 명확성 | ✅ Pass | "분석→설계→구현 파이프라인 구축"이라는 목표가 한 문장으로 명확히 정의됨 |
| T-2 | 요구사항 완전성 | 🟡 Warning | wireframe.md 산출물의 구체적 스키마/포맷이 정의되지 않음. ui-designer의 출력물 품질 기준 미정의 |
| T-3 | 모호성 여부 | 🟡 Warning | "shadcn 컴포넌트 매핑을 포함"의 범위 불명확, "단일 HTML 출력 모드"와 기존 wireframe-builder 산출물 간의 관계 불명확 |
| T-4 | 제약 조건 식별 | ✅ Pass | 스킬 구조, 파싱 가능한 산출물, shadcn 규칙 준수, 설치 호환성이 적절히 기술됨 |
| T-5 | 성공 기준 | 🔴 Critical | 명시적 성공 기준(완료 판단 기준) 섹션이 누락됨 |
| T-6 | 작업 유형 적절성 | ✅ Pass | "신규 개발 + 기능 개선" 복합 유형이 정확함 (ui-designer 신규 + wireframe-builder 개선) |

## 3. 지적 사항

### 🔴 Critical

**[T-5] 성공 기준 누락**: TASK.md에 "성공 기준" 또는 "완료 기준" 섹션이 없다. 다음과 같은 기준이 명시되어야 한다:
- wireframe-builder가 정책서 입력으로부터 wireframe.md를 정상 생성하는지
- ui-designer가 wireframe.md를 파싱하여 shadcn/ui 기반 UI를 출력하는지
- 두 스킬의 파이프라인 연결이 end-to-end로 동작하는지
- 레지스트리(skills.md, CLAUDE.md) 업데이트가 완료되었는지

### 🟡 Warning

**[T-2] wireframe.md 산출물 스키마 미정의**: wireframe-builder의 핵심 산출물인 wireframe.md가 "구조화된" 형태라고만 기술되어 있고, 실제 포맷(섹션, 필수 필드, 마크다운 구조)이 정의되지 않았다. 이 스키마는 ui-designer의 파싱 로직에 직접적 영향을 미치므로, RESEARCH 단계에서 반드시 구체화해야 한다.

**[T-3] "단일 HTML 출력 모드"의 위치 모호**: ui-designer가 "단일 HTML 출력 모드"를 지원한다고 되어 있는데, 이것이 기존 wireframe-builder의 산출물(단일 HTML 와이어프레임)을 대체하는 것인지, 별개의 프로덕션용 HTML인지 불명확하다. 기존 wireframe-builder의 HTML 산출물이 완전히 폐기되는 것인지도 명시가 필요하다.

### 🔵 Info

**[참고] shadcn 스킬 연계**: 관련 문서에 `~/.opal/community-skills/vercel-labs/shadcn/SKILL.md`가 포함되어 있으며, 요구사항에도 shadcn 스킬 연계가 명시되어 있다. RESEARCH 단계에서 해당 스킬의 Critical Rules를 구체적으로 분석하여 ui-designer 설계에 반영해야 한다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| `skills/wireframe-builder/SKILL.md` | 현재 스킬의 "단일 HTML + 외부 의존성 없음" 원칙이 개선 후 어떻게 변경되는지 TASK에 기술되었는가 | 🟡 기존 원칙의 폐기/변경 범위가 명시되지 않음 |
| `skills/wireframe-builder/SKILL.md` | "화면 도출 규칙"이 개선된 wireframe-builder에도 계승되는지 | ✅ 요구사항의 "화면 목록, 화면별 레이아웃·구조·기능 도출"이 해당 기능을 포괄함 |
| `~/.opal/references/skills.md` | wireframe-builder의 현재 설명("단일 HTML 인터랙티브 와이어프레임")이 TASK 목표와 일치하는지 | ✅ 레지스트리 업데이트가 요구사항에 포함됨 |
| `~/.opal/references/skills.md` | ui-designer가 기존 스킬과 트리거 키워드 충돌이 없는지 | 🔵 RESEARCH에서 트리거 키워드를 설계할 때 anthropics/frontend-design, vercel-labs/web-design-guidelines 등과의 역할 구분 필요 |

## 5. 판정

**⚠️ Needs Revision**

- 🔴 Critical 1건: 성공 기준 섹션 누락
- 🟡 Warning 2건: wireframe.md 스키마 미정의, 단일 HTML 출력 모드의 위치 모호

**권고**: TASK.md에 "성공 기준" 섹션을 추가하고, wireframe.md 산출물 포맷에 대한 방향성과 기존 HTML 산출물의 처리 방침을 명시한 뒤 다음 단계로 진행할 것을 권장한다. Warning 항목은 RESEARCH 단계에서 구체화할 수 있으나, 성공 기준 누락은 이후 모든 단계의 완료 판단에 영향을 미치므로 반드시 보완이 필요하다.
