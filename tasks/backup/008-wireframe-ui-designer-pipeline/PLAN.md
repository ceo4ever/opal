# PLAN: wireframe-builder 개선 및 ui-designer 스킬 신규 개발

> 작성일: 2026-03-13 | 참조: TASK.md, RESEARCH.md

## 1. 구현 범위

### 신규 생성 파일

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `skills/ui-designer/SKILL.md` | ui-designer 스킬 정의 (wireframe.md → React+shadcn UI 구현) |

### 수정 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 2 | `skills/wireframe-builder/SKILL.md` | 전체 재작성: HTML 생성 → wireframe.md 설계 도구로 전환 |
| 3 | `opal/core/references/skills.md` | wireframe-builder 설명 변경 + ui-designer 행 추가 |
| 4 | `CLAUDE.md` | 소스 구조에 ui-designer 추가, 스킬 개수 반영 |
| 5 | `scripts/install-mac.sh` | 스킬 개수 표기 "6개" → "7개" (3곳) |

### 영향 확인 (변경 없지만 참조 필요)

| # | 파일 경로 | 확인 사항 |
|---|----------|----------|
| - | `community-skills/anthropics/web-artifacts-builder/SKILL.md` | ui-designer가 번들링 파이프라인으로 참조 |
| - | `community-skills/anthropics/web-artifacts-builder/scripts/` | init-artifact.sh, bundle-artifact.sh 호출 방식 확인 |
| - | `community-skills/vercel-labs/shadcn/SKILL.md` | ui-designer가 Critical Rules 참조 |

## 2. 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | wireframe-builder SKILL.md 재작성 | `skills/wireframe-builder/SKILL.md` | 🟡 중간 |
| 2 | ui-designer SKILL.md 신규 작성 | `skills/ui-designer/SKILL.md` | 🔴 높음 |
| 3 | 스킬 레지스트리 업데이트 | `opal/core/references/skills.md` | 🟢 낮음 |
| 4 | CLAUDE.md 소스 구조 업데이트 | `CLAUDE.md` | 🟢 낮음 |
| 5 | install-mac.sh 스킬 개수 수정 | `scripts/install-mac.sh` | 🟢 낮음 |

**순서 근거**: wireframe-builder가 wireframe.md 스키마를 정의하고, ui-designer가 그 스키마를 입력으로 받으므로 wireframe-builder를 먼저 확정해야 한다. 레지스트리/문서 업데이트는 스킬 구현 후 수행.

## 3. 핵심 설계

### 3.1 wireframe-builder (재작성)

현재 HTML 와이어프레임 생성 스킬을 **UI 분석·설계 도구**로 전환한다.

#### YAML frontmatter

```yaml
name: wireframe-builder
description: |
  **UI 분석·설계 스킬**. 정책서/요구사항을 분석하여 구조화된 wireframe.md를 생성합니다.
  반드시 이 스킬을 사용해야 하는 상황: "와이어프레임", "화면 설계", "UI 설계", "화면 구조",
  "화면 도출", 정책서/기획서 기반 화면 분석 요청.
  ui-designer 스킬과 파이프라인을 구성합니다 (wireframe-builder → wireframe.md → ui-designer → UI).
```

#### 스킬 프로세스 (4단계)

```
Phase 1: 입력 분석
  - 정책서/요구사항 문서를 읽고 핵심 기능, 엔티티, 사용자 역할을 식별
  - 입력이 부족하면 interview 스킬 참조하여 질문

Phase 2: 화면 도출
  - 화면 도출 규칙 테이블 적용 (기존 wireframe-builder의 자산 계승)
  - 각 화면에 ID(SCR-NNN), 유형(dashboard/crud/detail/form/settings/report/auth/monitor) 부여
  - 화면 간 네비게이션 흐름 정의

Phase 3: 화면별 상세 설계
  - 화면 유형별 기본 레이아웃 적용 (ASCII 다이어그램)
  - 구성 요소 테이블 작성: 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명
  - 화면 유형별 shadcn 기본 매핑 자동 적용 후 상세 조정
  - 인터랙션 목록 정의: 이벤트 → 동작 → 결과

Phase 4: 산출물 생성
  - wireframe.md 스키마에 따라 구조화된 마크다운 생성
  - version-mgr 규칙에 따라 버전 관리
```

#### wireframe.md 산출물 스키마 (RESEARCH에서 확정)

스킬 내부에 스키마를 인라인으로 포함한다:

- 헤더 (서비스명, 작성일, 버전)
- 1. 서비스 개요 (서비스명, 유형, 대상 사용자, 핵심 기능)
- 2. 전체 구조 (레이아웃 유형, 네비게이션 구조, 화면 흐름도)
- 3. 화면 목록 (마스터 테이블: ID | 화면명 | 유형 | 경로 | 메뉴그룹 | 설명)
- 4. 화면별 상세 설계 (메타 정보, ASCII 레이아웃, 구성 요소 테이블, 기능, 인터랙션)
- 5. 공통 컴포넌트 (컴포넌트 | shadcn 기반 | 사용 화면 | 설명)
- 6. shadcn 설치 목록 (컴포넌트 | 사용 화면 + 설치 명령)

#### 보존하는 기존 자산

- **화면 도출 규칙 테이블**: 기획 요소 → 도출 화면 매핑
- **화면 유형별 ASCII 레이아웃 패턴**: 대시보드, CRUD, 모달, 드릴다운
- **서브 에이전트 위임 패턴**: 대규모 설계(5화면 이상) 시 서브 에이전트 활용

#### 제거하는 항목

- HTML/CSS/JS 코드 생성 로직 전체
- showPage 함수, 그레이스케일 원칙, 반응형 불필요 원칙
- 단일 HTML 파일 출력 관련 모든 규칙

### 3.2 ui-designer (신규)

wireframe.md를 입력으로 받아 React + shadcn/ui 기반 UI를 구현하는 스킬.

#### YAML frontmatter

```yaml
name: ui-designer
description: |
  **UI 구현 스킬**. wireframe.md를 입력으로 받아 shadcn/ui 기반 React UI를 구현합니다.
  반드시 이 스킬을 사용해야 하는 상황: "UI 구현", "UI 만들어줘", "화면 구현",
  "wireframe 구현", "프로토타입 만들어줘", wireframe.md 기반 UI 생성 요청.
  wireframe-builder 스킬과 파이프라인을 구성합니다 (wireframe-builder → wireframe.md → ui-designer → UI).
```

#### 스킬 프로세스 (5단계)

```
Phase 1: 입력 파싱
  - wireframe.md를 읽고 구조 검증 (필수 섹션 존재 여부)
  - 화면 목록, 화면별 설계, shadcn 설치 목록 추출
  - 출력 모드 결정: 프로토타입(기본) / 프로덕션(사용자 지정)

Phase 2: 프로젝트 초기화
  [프로토타입 모드]
  - web-artifacts-builder의 init-artifact.sh로 Vite+React+shadcn 프로젝트 생성
  - 경로: {프로젝트}/wireframe-prototype/{서비스명}/

  [프로덕션 모드]
  - shadcn 스킬 연계: npx shadcn@latest init + 필요 컴포넌트 설치
  - Next.js App Router 프로젝트 구조 생성
  - 경로: 사용자 지정 또는 {프로젝트}/{서비스명}/

Phase 3: 공통 컴포넌트 생성
  - wireframe.md 섹션 5(공통 컴포넌트)를 React 컴포넌트로 구현
  - shadcn Critical Rules 준수:
    → FieldGroup + Field 폼 구조 (raw div 금지)
    → gap-* 레이아웃 (space-x/y 금지)
    → 시맨틱 컬러 변수 사용
    → data-icon 속성 사용
  - 이 컴포넌트들은 두 모드에서 동일하게 재활용됨

Phase 4: 화면별 구현
  - wireframe.md 섹션 4(화면별 상세 설계)를 순서대로 구현
  - 각 화면: ASCII 레이아웃 → 구성 요소 테이블의 shadcn 컴포넌트 → React 코드
  - 인터랙션 목록에 따른 이벤트 핸들러 구현
  - 대규모(5화면 이상): 서브 에이전트에 화면별 위임

  [프로토타입 모드]
  - 단일 App.tsx에 탭/라우팅으로 전체 화면 구성
  - 더미 데이터로 화면 채움

  [프로덕션 모드]
  - Next.js App Router 페이지별 파일 생성
  - wireframe.md 경로 필드를 App Router 경로로 매핑

Phase 5: 빌드 및 산출물 생성
  [프로토타입 모드]
  - web-artifacts-builder의 bundle-artifact.sh 실행
  - 단일 bundle.html 생성 → 브라우저에서 바로 확인 가능

  [프로덕션 모드]
  - 프로젝트 디렉토리 완성 (next dev로 실행 가능 상태)
  - version-mgr 규칙에 따라 버전 관리
```

#### shadcn Critical Rules 참조 방식

ui-designer가 코드 생성 시 참조할 규칙을 스킬 내부에 명시:

```
참조 경로 (우선순위):
1. {프로젝트}/.opal/community-skills/vercel-labs/shadcn/SKILL.md
2. ~/.opal/community-skills/vercel-labs/shadcn/SKILL.md
3. ~/.opal/community-skills/vercel-labs/shadcn/rules/composition.md
4. ~/.opal/community-skills/vercel-labs/shadcn/rules/forms.md
```

핵심 규칙을 스킬 내 인라인 요약으로도 포함하여, shadcn 스킬이 없어도 기본 품질을 보장한다.

#### web-artifacts-builder 연계 방식

```
참조 경로 (우선순위):
1. {프로젝트}/.opal/community-skills/anthropics/web-artifacts-builder/
2. ~/.opal/community-skills/anthropics/web-artifacts-builder/

호출 스크립트:
- init-artifact.sh <프로젝트명>  → React+Vite+Tailwind+shadcn 프로젝트 스캐폴드
- bundle-artifact.sh             → Parcel+html-inline → 단일 bundle.html
```

#### 서브 에이전트 위임 규칙

대규모 UI 구현(5화면 이상) 시:
- 공통 컴포넌트(Phase 3)는 메인 에이전트가 직접 구현
- 화면별 구현(Phase 4)을 서브 에이전트에 위임
- 각 서브 에이전트에 전달: wireframe.md의 해당 화면 섹션 + 공통 컴포넌트 경로 + shadcn 규칙

### 3.3 레지스트리 업데이트

#### skills.md 변경

```markdown
# 프레임워크 스킬 테이블에서:

# 기존 행 수정:
| wireframe-builder | "와이어프레임", "화면 설계", "UI 설계", "화면 구조", "화면 도출" | UI 분석·설계 → 구조화된 wireframe.md 생성 |

# 신규 행 추가:
| ui-designer | "UI 구현", "UI 만들어줘", "화면 구현", "프로토타입 만들어줘" | wireframe.md → shadcn/ui 기반 React UI 구현 (프로토타입/프로덕션) |
```

#### CLAUDE.md 소스 구조 변경

```
skills/                          ← 프레임워크 스킬 (단일 소스, 3개 플랫폼 공용)
├── task-flow/                   핵심 오케스트레이터: TASK → RESEARCH → PLAN → TODO → EXECUTE
├── api-analyzer/                외부 API 7단계 분석 및 명세서 생성
├── doc-writer/                  기술 문서 표준 템플릿 (모든 문서 스킬의 베이스)
├── interview/                   구조화된 Q&A 요구사항 수집
├── ui-designer/                 wireframe.md → shadcn/ui 기반 UI 구현  ← 신규
├── version-mgr/                 산출물 버전 관리 (v{Major}.{Minor}, 덮어쓰기 금지)
└── wireframe-builder/           정책서/요구사항 → 구조화된 wireframe.md 생성  ← 설명 변경
```

컴포넌트 유형 테이블: `skills/` 6개 → 7개

#### install-mac.sh 변경

3곳의 `"스킬 (6개)"` → `"스킬 (7개)"` 변경:
- 234행: `install_claude` 내
- 243행: `install_cursor` 내
- 252행: `install_antigravity` 내

## 4. 의존성 및 환경 변경

### 추가 패키지

없음. ui-designer는 web-artifacts-builder의 init-artifact.sh가 필요한 패키지를 설치한다.

### 환경 변경

없음. 스킬 파일(.md)만 추가/수정하므로 환경 변경 불필요.

### 런타임 의존성 (ui-designer 실행 시)

| 의존성 | 용도 | 설치 방법 |
|--------|------|----------|
| Node.js 18+ | React+Vite 프로젝트 빌드 | 사전 설치 필요 |
| pnpm | 패키지 매니저 (web-artifacts-builder가 사용) | init-artifact.sh가 자동 설치 |
| web-artifacts-builder 스킬 | 프로토타입 모드 번들링 | ~/.opal/community-skills/에 설치 (install-mac.sh) |
| shadcn 스킬 | Critical Rules 참조 | ~/.opal/community-skills/에 설치 (install-mac.sh) |

## 5. 테스트 전략

### 스킬 문서 검증

| # | 테스트 항목 | 성공 기준 |
|---|-----------|----------|
| T-1 | wireframe-builder SKILL.md 구조 | YAML frontmatter 유효, 4단계 프로세스 정의, wireframe.md 스키마 인라인 포함 |
| T-2 | ui-designer SKILL.md 구조 | YAML frontmatter 유효, 5단계 프로세스 정의, 두 출력 모드 정의 |
| T-3 | wireframe.md 스키마 일관성 | wireframe-builder 출력 스키마 = ui-designer 입력 스키마 (섹션, ID 체계, 테이블 형식 동일) |
| T-4 | shadcn 규칙 참조 | ui-designer에서 shadcn Critical Rules 참조 경로와 인라인 요약이 모두 존재 |
| T-5 | web-artifacts-builder 연계 | ui-designer에서 init-artifact.sh, bundle-artifact.sh 호출 방식이 정확 |

### 레지스트리/문서 검증

| # | 테스트 항목 | 성공 기준 |
|---|-----------|----------|
| T-6 | skills.md 정합성 | wireframe-builder 설명 변경됨, ui-designer 행 추가됨, 트리거 키워드 충돌 없음 |
| T-7 | CLAUDE.md 정합성 | 소스 구조에 ui-designer 포함, 스킬 개수 7개 반영 |
| T-8 | install-mac.sh | "스킬 (7개)" 3곳 반영, 문법 검사 통과 |

### E2E 파이프라인 검증 (수동)

| # | 테스트 항목 | 성공 기준 |
|---|-----------|----------|
| T-9 | wireframe-builder 실행 | 샘플 정책서 → wireframe.md 생성, 스키마 준수 |
| T-10 | ui-designer 프로토타입 모드 | wireframe.md → web-artifacts-builder → bundle.html 생성, 브라우저 동작 |
| T-11 | 컴포넌트 재활용 | 프로토타입에서 작성한 React 컴포넌트를 Next.js 프로젝트로 복사 시 동작 |

> T-9 ~ T-11은 스킬 작성 후 실제 사용 시 검증. 현재 태스크에서는 T-1 ~ T-8까지 검증.

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| wireframe.md 스키마 변경 시 양쪽 스킬 동시 수정 필요 | 🟡 중간 | 스키마를 양쪽 스킬에 인라인으로 동일하게 포함하고, 변경 시 양쪽 업데이트 체크리스트 추가 |
| web-artifacts-builder 스킬 미설치 환경에서 프로토타입 모드 실패 | 🟡 중간 | ui-designer에서 스킬 존재 여부 확인 후, 없으면 안내 메시지 출력 + 수동 설치 가이드 제공 |
| shadcn 스킬 업데이트 시 ui-designer 인라인 규칙과 불일치 | 🔵 낮음 | ui-designer가 런타임에 shadcn SKILL.md를 먼저 참조하고, 없을 때만 인라인 규칙 사용 |
| 대규모 서비스(20+ 화면) 시 wireframe.md가 너무 길어짐 | 🔵 낮음 | 서브 에이전트 위임으로 대응. 필요 시 wireframe.md를 화면별 분할하는 옵션 고려 |
| 기존 wireframe-builder 사용자가 HTML 직접 생성 기능 상실 | 🟡 중간 | wireframe-builder SKILL.md에 마이그레이션 안내 포함: "HTML 생성은 ui-designer 스킬로 이관됨" |
