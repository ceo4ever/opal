# RESEARCH: wireframe-builder 개선 및 ui-designer 스킬 신규 개발

> 작성일: 2026-03-13 | 참조: TASK.md

## 1. 기존 코드 분석

### 관련 파일 목록

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/wireframe-builder/SKILL.md` | 소스 저장소. 현재 HTML 와이어프레임 생성 스킬 | 수정 (UI 분석·설계 스킬로 전환) |
| `skills/ui-designer/SKILL.md` | 소스 저장소. (미존재) ui-designer 신규 스킬 | 신규 |
| `opal/core/references/skills.md` | 소스 저장소. 스킬 레지스트리 소스 | 수정 (wireframe-builder 설명 변경 + ui-designer 추가) |
| `CLAUDE.md` | 소스 저장소. 프레임워크 아키텍처 정의 | 수정 (소스 구조에 ui-designer 반영) |
| `scripts/install-mac.sh` | 소스 저장소. 설치 스크립트 | 확인 (스킬 개수 하드코딩 여부) |
| `~/.opal/community-skills/vercel-labs/shadcn/SKILL.md` | 배포 경로. shadcn 스킬 (참조만) | 없음 |
| `~/.opal/community-skills/vercel-labs/shadcn/rules/composition.md` | 배포 경로. 컴포넌트 구성 규칙 (참조만) | 없음 |
| `~/.opal/community-skills/vercel-labs/shadcn/rules/forms.md` | 배포 경로. 폼 패턴 규칙 (참조만) | 없음 |
| `community-skills/anthropics/web-artifacts-builder/SKILL.md` | 소스 저장소. React+Vite+shadcn 단일 HTML 번들링 스킬 (참조) | 없음 |
| `community-skills/anthropics/web-artifacts-builder/scripts/bundle-artifact.sh` | 소스 저장소. Parcel+html-inline 번들링 스크립트 (참조) | 없음 |

### 현재 wireframe-builder 구현 패턴

현재 스킬은 **단일 HTML 파일 생성**에 초점:
- 사이드바+콘텐츠 레이아웃 구조 정의
- 페이지 전환 JS 시스템 (`showPage()`)
- UI 컴포넌트 패턴: 대시보드, CRUD, 모달, 드릴다운을 ASCII로 정의
- 화면 도출 규칙 테이블 (기획 요소 → 도출 화면)
- 그레이스케일, 외부 의존성 없음, 반응형 불필요

**보존할 자산**: 화면 도출 규칙, 화면 유형별 레이아웃 패턴 (ASCII), 서브 에이전트 활용 패턴
**제거 대상**: HTML/CSS/JS 코드 생성 로직, 그레이스케일 원칙, showPage 함수 등

### 프레임워크 스킬 공통 패턴

기존 스킬들의 공통 구조를 분석한 결과:

| 패턴 | 설명 | 적용 스킬 |
|------|------|----------|
| YAML frontmatter | `name`, `description` (트리거 키워드 포함) | 전체 |
| 단계별 프로세스 | Phase/Step으로 실행 절차 명시 | api-analyzer(7단계), interview(4단계) |
| 산출물 템플릿 | 마크다운 코드블록으로 최종 산출물 구조 정의 | api-analyzer, doc-writer |
| 문서 헤더 표준 | `# 제목` + `> 작성일 | 버전` | doc-writer 기반 전체 |
| 변경이력 테이블 | 하단에 버전/날짜/변경내용 | doc-writer, version-mgr |
| 서브 에이전트 위임 | 대규모 작업 시 서브 에이전트 활용 규칙 | wireframe-builder, task-flow |

### 의존성 맵

```
wireframe-builder (수정)
  ← skills.md 레지스트리가 참조
  ← CLAUDE.md 소스 구조가 참조
  → interview 스킬 (입력 부족 시 호출)
  → version-mgr (산출물 버전 관리)

ui-designer (신규)
  ← skills.md 레지스트리에 등록 필요
  ← CLAUDE.md 소스 구조에 반영 필요
  → wireframe.md (wireframe-builder 산출물을 입력으로 사용)
  → shadcn 스킬 (컴포넌트 규칙 참조, Next.js 모드에서 직접 연계)
  → web-artifacts-builder (단일 HTML 번들링 파이프라인 참조)
  → version-mgr (산출물 버전 관리)
```

## 2. 외부 조사 결과

### shadcn/ui 컴포넌트 체계

shadcn 스킬을 분석한 결과, ui-designer가 매핑해야 할 컴포넌트 카테고리:

| 카테고리 | 컴포넌트 | 용도 |
|---------|---------|------|
| **레이아웃** | Sidebar, Card, Separator, Resizable, ScrollArea, Accordion, Collapsible | 페이지 구조 |
| **네비게이션** | NavigationMenu, Breadcrumb, Tabs, Pagination | 화면 이동 |
| **데이터 표시** | Table, Badge, Avatar, Chart(Recharts) | 정보 표현 |
| **폼 입력** | Input, Select, Combobox, Switch, Checkbox, RadioGroup, Textarea, InputOTP, Slider | 사용자 입력 |
| **폼 구조** | FieldGroup, Field, FieldLabel, InputGroup, FieldSet | 폼 레이아웃 |
| **오버레이** | Dialog, AlertDialog, Sheet, Drawer, Popover, HoverCard | 모달/패널 |
| **피드백** | sonner(toast), Alert, Progress, Skeleton, Spinner | 상태 표시 |
| **메뉴** | DropdownMenu, ContextMenu, Menubar | 컨텍스트 액션 |
| **기타** | Button, Tooltip, Command, Empty, ToggleGroup | 범용 |

### shadcn Critical Rules (ui-designer 준수 사항)

ui-designer가 코드 생성 시 반드시 따라야 할 규칙:

1. **스타일링**: `className`은 레이아웃용만, `gap-*` 사용 (space-x/y 금지), 시맨틱 컬러 사용
2. **폼**: `FieldGroup` + `Field` 구조 필수, raw div 금지
3. **구성**: Items는 반드시 Group 안에, Dialog/Sheet는 Title 필수
4. **아이콘**: `data-icon` 속성 사용, 수동 사이징 금지
5. **컴포넌트 우선**: 커스텀 마크업 전에 기존 컴포넌트 확인 (Alert, Empty, Badge, Skeleton 등)

### 단일 HTML 출력 모드 기술 조사

#### 기존 접근법 (재검토)

초기 분석에서는 shadcn/ui가 React 기반이므로 단일 HTML 직접 출력이 불가하다고 판단하여, Tailwind CDN + vanilla JS로 shadcn 스타일을 재현하는 방식을 검토했다. 그러나 이 접근은 **React 코드와 완전히 별개의 코드베이스**를 만들게 되어, Next.js 프로젝트 모드와 코드 재사용이 불가능하다는 근본적 문제가 있다.

| 방식 (기존 검토) | 장점 | 단점 |
|-----------------|------|------|
| Tailwind CDN + shadcn CSS 변수 | 외부 의존성 최소, 즉시 확인 | React/shadcn 코드와 완전 별개, vanilla JS로 인터랙션 재구현 필요 |
| React CDN (esm.sh) | 실제 컴포넌트 동작 | 로딩 느림, 복잡도 높음 |
| Static HTML + Tailwind | 가장 단순 | shadcn 스타일 재현 어려움, JS 인터랙션 수동 구현 |

#### 새로운 접근: React + shadcn 코드를 빌드 후 단일 HTML로 번들링

**핵심 발상 전환**: 단일 HTML 모드와 Next.js 모드에서 **동일한 React + shadcn 코드**를 사용하고, 출력 방식만 다르게 한다.

```
wireframe.md → ui-designer → React + shadcn 컴포넌트 코드 (공통)
                                 ├→ Vite 빌드 + 단일 HTML 번들링 (프로토타입)
                                 └→ Next.js 프로젝트 (프로덕션)
```

#### 프레임워크 내 기존 자산: web-artifacts-builder

`community-skills/anthropics/web-artifacts-builder`가 이미 이 파이프라인을 구현하고 있다:

- **스택**: React + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **번들링**: Parcel + `html-inline`으로 단일 `bundle.html` 생성
- **파이프라인**: `init-artifact.sh` (스캐폴드) → 개발 → `bundle-artifact.sh` (단일 HTML 번들링)
- **소스 위치**: `community-skills/anthropics/web-artifacts-builder/` (스크립트 포함)

이 스킬의 번들링 파이프라인을 ui-designer에서 직접 활용하거나 참조할 수 있다.

#### 단일 HTML 번들링 도구 비교

| 도구 | 유형 | 방식 | 장점 | 단점 |
|------|------|------|------|------|
| **vite-plugin-singlefile** | Vite 플러그인 | 빌드 시 JS/CSS를 index.html에 인라인 | 가장 깔끔, 설정 최소, 활발히 유지보수 (2025) | public/ 폴더 외부 에셋 미포함 |
| **Parcel + html-inline** | 빌드 도구 + CLI | Parcel 번들 후 html-inline으로 인라인 | web-artifacts-builder에서 검증됨 | 2단계 파이프라인 필요 |
| **single-file-cli** | CLI (헤드리스 브라우저) | Chrome DevTools Protocol로 렌더링된 페이지 캡처 | 실행 중인 앱 그대로 캡처 | 헤드리스 브라우저 필요, 느림 |
| **monolith** | Rust CLI | CSS/이미지/JS를 data URL로 변환하여 단일 HTML | 빠름, 단순 | 서빙 중인 페이지 대상 |

#### 권장 전략: web-artifacts-builder 파이프라인 활용

**1순위 — web-artifacts-builder 파이프라인 (채택)**
- 이미 프레임워크에 검증된 React + Vite + Tailwind + shadcn/ui → 단일 HTML 번들링 파이프라인
- `init-artifact.sh`로 프로젝트 스캐폴드 → React + shadcn 코드 작성 → `bundle-artifact.sh`로 단일 HTML 생성
- Parcel + `html-inline`으로 모든 JS/CSS를 인라인하여 `bundle.html` 출력
- ui-designer가 이 파이프라인을 직접 활용하면 추가 도구 도입 불필요

**대안 — vite-plugin-singlefile**
- Vite 빌드 시 JS/CSS를 index.html에 인라인하는 플러그인
- web-artifacts-builder와 유사하지만, 프레임워크에 이미 검증된 파이프라인이 있으므로 우선순위 낮음

**대안 — Next.js static export + 후처리**
- `next build` (`output: 'export'`) → `out/` 디렉토리 (다중 파일) 생성
- `single-file-cli`로 후처리하여 단일 HTML 변환
- 가장 복잡하지만 Next.js 기능(라우팅, SSG 등)을 유지

#### Next.js static export 분석

Next.js 14/15의 `output: 'export'` 모드:

```js
// next.config.js
const nextConfig = { output: 'export' }
```

- **출력**: `out/` 디렉토리 (라우트별 HTML + `_next/` 에셋 번들)
- **지원**: Server Components(빌드 타임 렌더링), Client Components(프리렌더 + 하이드레이션)
- **미지원**: Server Actions, Cookies, Rewrites, ISR, Draft Mode
- **shadcn 호환성**: 문제 없음 (표준 React 컴포넌트). `next/image`만 커스텀 로더 필요
- **핵심**: 다중 파일 디렉토리를 생성하므로 단일 HTML이 아님 → 추가 번들링 필요

#### ui-designer 출력 모드 재설계

| 모드 | 용도 | 빌드 방식 | 산출물 |
|------|------|----------|--------|
| **프로토타입** (기본) | 빠른 시각 확인, 피드백 수집 | web-artifacts-builder 파이프라인 (Parcel + html-inline) | 단일 `bundle.html` |
| **프로덕션** (선택) | 실제 서비스 배포용 | Next.js App Router + shadcn 스킬 연계 | Next.js 프로젝트 디렉토리 |

두 모드 모두 **동일한 React + shadcn 컴포넌트 코드**를 공유한다. 프로토타입에서 작성한 컴포넌트를 프로덕션 Next.js 프로젝트로 그대로 이식할 수 있다. 차이는 빌드 도구와 라우팅 방식뿐이다.

## 3. wireframe.md 스키마 설계

### 설계 원칙

1. **기계 파싱 가능**: 일관된 헤딩 레벨, 테이블 구조, ID 체계로 ui-designer가 프로그래매틱하게 파싱 가능
2. **사람이 읽기 쉬움**: ASCII 다이어그램, 테이블, 명확한 한국어 설명
3. **shadcn 매핑 내장**: 각 UI 요소에 shadcn 컴포넌트를 직접 명시하여 ui-designer가 바로 코드 생성 가능
4. **확장 가능**: 화면 추가/수정 시 해당 섹션만 Edit으로 수정 가능

### wireframe.md 스키마 정의

```
wireframe.md
├── 헤더 (서비스명, 작성일, 버전)
├── 1. 서비스 개요
│   ├── 서비스명, 유형, 대상 사용자
│   └── 핵심 기능 목록
├── 2. 전체 구조
│   ├── 2.1 레이아웃 유형 + 설명
│   ├── 2.2 네비게이션 구조 (메뉴 트리)
│   └── 2.3 화면 흐름도 (화면 간 이동)
├── 3. 화면 목록 (마스터 테이블)
│   └── ID | 화면명 | 유형 | 경로 | 메뉴그룹 | 설명
├── 4. 화면별 상세 설계
│   └── (화면 수만큼 반복)
│       ├── 메타 정보 (유형, 경로, 진입점)
│       ├── 레이아웃 (ASCII 다이어그램)
│       ├── 구성 요소 테이블 (영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명)
│       ├── 기능 목록
│       └── 인터랙션 목록 (이벤트 → 동작 → 결과)
├── 5. 공통 컴포넌트
│   └── 컴포넌트 | shadcn 기반 | 사용 화면 | 설명
└── 6. shadcn 설치 목록
    └── 컴포넌트 | 사용 화면 + 설치 명령
```

### 핵심 컨벤션

#### 화면 ID 체계
- `SCR-{NNN}` 형식 (예: SCR-001, SCR-002)
- 3자리 순번, 도출 순서대로 부여
- 화면 목록(섹션 3)과 상세 설계(섹션 4)에서 동일 ID 사용

#### 화면 유형 분류
| 유형 코드 | 설명 | 대표 레이아웃 |
|----------|------|-------------|
| `dashboard` | 현황/통계 대시보드 | KPI 카드 + 차트 + 테이블 |
| `crud` | 엔티티 관리 (목록+등록/수정) | 검색/필터 + 테이블 + 모달/페이지 폼 |
| `detail` | 상세 보기 | 정보 카드 + 탭 + 관련 데이터 |
| `form` | 독립 폼 (등록/수정 전용 페이지) | 섹션별 필드 그룹 + 액션 버튼 |
| `settings` | 설정 | 탭 메뉴 + 섹션별 토글/입력 |
| `report` | 보고서/분석 | 필터 + 차트 + 데이터 테이블 |
| `auth` | 인증 (로그인/회원가입) | 중앙 정렬 카드 폼 |
| `monitor` | 실시간 모니터링 | 상태 카드 + 실시간 차트/로그 |

#### 구성 요소 테이블 규칙
- **영역**: 화면 내 위치 (header, filter, content, sidebar, footer, modal 등)
- **UI 요소**: 사용자에게 보이는 요소 (검색바, 데이터 테이블, 등록 버튼 등)
- **shadcn 컴포넌트**: 해당 요소를 구현할 shadcn 컴포넌트명 (정확한 컴포넌트명 사용)
- **데이터/설명**: 표시할 데이터 필드명이나 동작 설명

#### 레이아웃 유형별 표준 구조

**사이드바 + 콘텐츠 (기본)**
```
shadcn 컴포넌트: Sidebar + 메인 영역
┌──────────┬──────────────────────────┐
│ Sidebar  │ Header (Breadcrumb)      │
│          ├──────────────────────────┤
│ 메뉴그룹1 │                          │
│ 메뉴그룹2 │ Content 영역              │
│ 메뉴그룹3 │                          │
│          │                          │
│          │                          │
└──────────┴──────────────────────────┘
```

**탑바 + 콘텐츠**
```
shadcn 컴포넌트: NavigationMenu + 메인 영역
┌─────────────────────────────────────┐
│ NavigationMenu (로고 + 메뉴 + 유저)  │
├─────────────────────────────────────┤
│                                     │
│ Content 영역                         │
│                                     │
└─────────────────────────────────────┘
```

**인증 (풀페이지 중앙)**
```
shadcn 컴포넌트: Card (중앙 배치)
┌─────────────────────────────────────┐
│                                     │
│         ┌───────────────┐           │
│         │  Card (로그인)  │           │
│         │  폼 필드들      │           │
│         │  [로그인 버튼]  │           │
│         └───────────────┘           │
│                                     │
└─────────────────────────────────────┘
```

#### 화면 유형별 shadcn 매핑 기본값

| 화면 유형 | 핵심 컴포넌트 | 보조 컴포넌트 |
|----------|-------------|-------------|
| `dashboard` | Card, Chart | Badge, Table, Select(필터), Tabs |
| `crud` | Table, Pagination | Input(검색), Select(필터), Dialog/Sheet(폼), DropdownMenu(행 액션), AlertDialog(삭제 확인), Badge(상태) |
| `detail` | Card, Tabs | Badge, Button, Separator, Table |
| `form` | FieldGroup, Field, Input, Select | Button, Combobox, Textarea, Switch |
| `settings` | Tabs, Switch | Input, Select, Button, Separator |
| `report` | Chart, Table | Select(필터), Button(다운로드), DatePicker |
| `auth` | Card, Input, Button | FieldGroup, Field, Checkbox |
| `monitor` | Card, Badge | Chart, Table, ScrollArea, Alert |

## 4. 영향 범위

### 직접 영향

| 대상 | 영향 내용 |
|------|----------|
| `skills/wireframe-builder/SKILL.md` | 전체 재작성 (HTML 생성 → wireframe.md 생성) |
| `skills/ui-designer/SKILL.md` | 신규 생성 |
| `~/.opal/references/skills.md` | wireframe-builder 설명 변경 + ui-designer 행 추가 |
| `CLAUDE.md` | 소스 구조 테이블에 ui-designer 추가 |

### 간접 영향

| 대상 | 영향 내용 |
|------|----------|
| `install-mac.sh` | skills/ 디렉토리를 통째로 복사하므로 ui-designer 자동 포함. 단, 스킬 개수 표기("스킬 (6개)")가 하드코딩되어 있으면 7개로 변경 필요 — 확인 후 수정 |
| 기존 wireframe-builder 사용자 | HTML 직접 생성 기능이 없어짐 → ui-designer로 대체 안내 필요 |
| shadcn 스킬 | 참조만 하므로 변경 없음 |

## 5. 핵심 발견 사항

1. **wireframe.md 스키마가 파이프라인의 핵심 계약**: wireframe-builder의 출력과 ui-designer의 입력이 정확히 일치해야 하므로, 스키마를 엄격하게 정의해야 한다. 특히 화면 ID 체계(`SCR-NNN`), 구성 요소 테이블 형식, shadcn 컴포넌트명이 일관되어야 한다.

2. **shadcn 컴포넌트 매핑은 화면 유형별 기본값으로 자동화 가능**: 화면 유형(dashboard, crud, detail 등)별로 사용되는 shadcn 컴포넌트 패턴이 일정하므로, wireframe-builder가 화면 유형만 결정하면 기본 매핑을 자동 적용하고 상세 조정만 하면 된다.

3. **단일 HTML 모드는 web-artifacts-builder 파이프라인 활용이 최적**: 초기에 검토한 Tailwind CDN + vanilla JS 방식은 React 코드와 별개의 코드베이스를 만들어 컴포넌트 재활용이 불가능하다. 프레임워크 내 `web-artifacts-builder` 스킬이 이미 React + Vite + shadcn → Parcel + html-inline → 단일 HTML 번들링 파이프라인을 검증해두었으므로, 이를 그대로 활용한다. 프로토타입에서 작성한 React + shadcn 컴포넌트를 프로덕션 Next.js 프로젝트로 그대로 이식할 수 있어 코드 재활용이 보장된다.

4. **기존 wireframe-builder의 화면 도출 규칙과 ASCII 패턴은 보존 가치가 높음**: 엔티티→화면 도출 규칙, 대시보드/CRUD/모달 ASCII 패턴은 wireframe-builder에 그대로 가져갈 수 있다.

5. **ui-designer는 shadcn 스킬의 Critical Rules를 내재화해야 함**: 직접 코드를 생성하는 스킬이므로, `FieldGroup+Field` 폼 패턴, `gap-*` 스타일링, 컴포넌트 구성 규칙 등을 스킬 내부에 참조 경로로 포함해야 한다.

## 6. 제약/리스크

| 리스크 | 심각도 | 대응 |
|--------|--------|------|
| wireframe.md 스키마 변경 시 양쪽 스킬 동시 수정 필요 | 🟡 중간 | 스키마를 별도 references 파일로 분리하는 것도 고려 (현재는 스킬 내 인라인으로 충분) |
| 단일 HTML 번들링 시 외부 에셋(폰트, 이미지) 누락 가능 | 🔵 낮음 | `vite-plugin-singlefile`이 JS/CSS는 인라인하지만 public/ 에셋은 별도 처리 필요. 프로토타입 단계에서는 CDN 폰트 + 인라인 SVG로 대응 |
| shadcn 스킬 업데이트 시 ui-designer 규칙과 불일치 가능 | 🟡 중간 | ui-designer가 shadcn SKILL.md를 런타임에 참조하도록 설계 |
| 대규모 서비스(20+ 화면) 시 wireframe.md가 매우 길어짐 | 🔵 낮음 | 서브 에이전트 위임으로 대응, 필요 시 화면별 분할 고려 |
