# EXECUTE 범용 에이전트 가이드

> 대상: opal-task-agent (범용) / 기타·미지정 에이전트 (폴백)
> 사전 로드: references/execute-guide.md (공통 규칙)

## 1. 페르소나 처리 (FE/BE/공통 분기)

범용 에이전트는 작업 유형에 따라 페르소나를 **동적 Read**한다:

- **FE 작업** (PLAN.md §4.2 Step의 `영역: FE` 또는 파일 경로상 FE 판정 시):
  `opal/skills/op-dev-execute/personas/frontend-engineer.md` Read
- **BE 작업** (`영역: BE`):
  `opal/skills/op-dev-execute/personas/backend-engineer.md` Read
- **공통/환경/배치/문서 작업**: 페르소나 Read 불필요 — 범용 원칙만 적용

페르소나 파일이 없으면 아래 내장 역할을 따른다:
- FE: 시니어 프론트엔드 엔지니어 (React, shadcn/ui, 접근성 중시)
- BE: 시니어 백엔드 엔지니어 (API 설계, 데이터 모델링, 보안 중시)

## 2. Scope

- 단일 워커가 **디스패치 범위 전체를 순차 처리**한다.
- PLAN.md §4.2 Step을 Phase 그룹핑 → 의존 순서 준수 → 전체 완료까지 수행.
- 다중 영역(FE+BE) 혼합 Step도 동일 워커 내부에서 순차 처리.

## 3. FE 역할 분담 — ui-designer vs op-dev-execute

FE 태스크에서 UI 구현과 비UI 작업을 명확히 구분한다.

### ui-designer 담당 (UI 구현)

shadcn/ui + React 컴포넌트 전문. 화면에 보이는 것을 만드는 작업.

| 작업 | 예시 |
|------|------|
| 페이지 레이아웃 | 전체 화면 구조, 헤더/사이드바/콘텐츠 배치 |
| UI 컴포넌트 구현 | 버튼, 폼, 테이블, 카드, 다이얼로그 등 |
| shadcn 컴포넌트 조합 | shadcn MCP 조회 → 설치 → 조합 |
| 스타일링 | Tailwind CSS, 반응형 레이아웃 |
| 인터랙션 UI | 탭, 아코디언, 드롭다운, 모달 등 |
| 폼 UI | 입력 필드, 유효성 표시, 에러 메시지 표시 |

**호출 방법**: PLAN.md §3.N.2 `##### 화면: {화면명}` 서브섹션을 Read하여 ui-designer plan-driven 모드 입력으로 전달.

탐색 경로: `{프로젝트}/.opal/skills/ui-designer/SKILL.md` → `~/.opal/skills/ui-designer/SKILL.md`

### op-dev-execute 담당 (비UI FE 작업)

화면 뒤에서 동작하는 것.

| 작업 | 예시 |
|------|------|
| API 연동 | fetch/axios, API 클라이언트, 에러 처리 |
| 상태 관리 | zustand, context, React Query 설정 |
| 라우팅 설정 | Next.js app router, 페이지 구조 |
| 타입 정의 | TypeScript 인터페이스, OpenAPI 타입 생성 |
| 유틸리티 | 헬퍼 함수, 포맷터, 밸리데이터 |
| 환경 설정 | .env, 빌드 설정, 패키지 설치 |
| 인증/인가 로직 | 토큰 관리, 가드, 미들웨어 |

### 실행 순서 (FE 태스크)

PLAN.md §4 실행 체크리스트 기반:

1. 비UI 작업 먼저 (op-dev-execute): 라우팅·타입 정의·API 클라이언트·상태 관리
2. UI 구현 (ui-designer): PLAN.md §3.N.2 FE 화면 설계 섹션을 ui-designer plan-driven 모드 입력으로 전달
3. 통합 (op-dev-execute): API 연결·이벤트 핸들러 바인딩·최종 조립
4. 각 Step 완료 후 QA 체크리스트 검증

## 4. 활용 스킬/MCP

### FE

| 스킬/MCP | 담당 | 용도 |
|----------|------|------|
| **ui-designer** (plan-driven) | UI 구현 | 화면 레이아웃 + shadcn 컴포넌트 구현 |
| shadcn MCP | UI 구현 | 컴포넌트 검색·조회·설치 (ui-designer가 사용) |
| vercel-labs/shadcn | UI 구현 | shadcn Critical Rules, 폼/레이아웃 패턴 |
| vercel-labs/react-best-practices | 비UI | React 패턴 (상태 관리, 훅 등) |
| vercel-labs/next-best-practices | 비UI | Next.js 패턴 (라우팅, RSC 등) |
| vercel-labs/composition-patterns | 공통 | 컴포넌트 조합 패턴 |
| anthropics/frontend-design | 공통 | FE 아키텍처/UX 설계 참조 |
| context7 | 비UI | 라이브러리 문서 조회 |

### BE

| MCP | 용도 | 사용 시점 |
|-----|------|----------|
| context7 | 라이브러리 문서 조회 (Python, Flutter, Kotlin, Go 등) | 외부 라이브러리 API 확인 시 |

## 5. 공통 규칙 참조

금지 행동·보안 가드레일·블로커 처리·결과 반환은 **references/execute-guide.md**를 따른다.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-23 11:39 | 초기 작성 — 범용 에이전트 EXECUTE 지침 분리 (기존 SKILL.md L22-37 페르소나, L130-175 FE 역할, L178-194 MCP 이관) (129) |
