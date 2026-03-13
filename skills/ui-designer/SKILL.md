---
name: ui-designer
description: |
  **UI 구현 스킬**. wireframe.md를 입력으로 받아 shadcn/ui 기반 React UI를 구현합니다.
  반드시 이 스킬을 사용해야 하는 상황: "UI 구현", "UI 만들어줘", "화면 구현",
  "wireframe 구현", "프로토타입 만들어줘", wireframe.md 기반 UI 생성 요청.
  wireframe-builder 스킬과 파이프라인을 구성합니다 (wireframe-builder → wireframe.md → ui-designer → UI).
---

# UI Designer 스킬

wireframe.md를 입력으로 받아 React + shadcn/ui 기반 UI를 구현한다.

## 파이프라인 위치

```
wireframe-builder → wireframe.md → [ui-designer] → UI
                    (입력)           (이 스킬)       (산출물)
```

- **입력**: wireframe-builder 스킬이 생성한 `wireframe.md`
- **산출물**: React + shadcn/ui 컴포넌트 코드 (프로토타입 또는 프로덕션)

## 출력 모드

| 모드 | 용도 | 빌드 방식 | 산출물 |
|------|------|----------|--------|
| **프로토타입** (기본) | 빠른 시각 확인, 피드백 수집 | web-artifacts-builder 파이프라인 (Parcel + html-inline) | 단일 `bundle.html` |
| **프로덕션** (선택) | 실제 서비스 배포용 | Next.js App Router + shadcn 스킬 연계 | Next.js 프로젝트 디렉토리 |

두 모드 모두 **동일한 React + shadcn 컴포넌트 코드**를 공유한다. 프로토타입에서 작성한 컴포넌트를 프로덕션 Next.js 프로젝트로 그대로 이식할 수 있다.

사용자가 명시적으로 모드를 지정하지 않으면 **프로토타입 모드**를 기본으로 사용한다.

---

## Phase 1: 입력 파싱

### 1.1 wireframe.md 읽기 및 구조 검증

wireframe.md를 Read 도구로 읽고, 아래 필수 섹션이 존재하는지 확인한다:

| 섹션 | 필수 | 용도 |
|------|------|------|
| 1. 서비스 개요 | O | 서비스명, 유형, 핵심 기능 파악 |
| 2. 전체 구조 | O | 레이아웃 유형, 네비게이션 구조, 화면 흐름도 |
| 3. 화면 목록 | O | 마스터 테이블 (ID, 화면명, 유형, 경로, 메뉴그룹) |
| 4. 화면별 상세 설계 | O | 메타 정보, ASCII 레이아웃, 구성 요소, 인터랙션 |
| 5. 공통 컴포넌트 | O | 재사용 컴포넌트 목록 |
| 6. shadcn 설치 목록 | O | 필요한 shadcn 컴포넌트 + 설치 명령 |

누락된 섹션이 있으면 사용자에게 보고하고, wireframe-builder로 보완을 안내한다.

### 1.2 핵심 정보 추출

wireframe.md에서 추출할 정보:

```
서비스명           ← 섹션 1
레이아웃 유형       ← 섹션 2.1 (사이드바+콘텐츠 / 탑바+콘텐츠 / 풀페이지 등)
네비게이션 구조     ← 섹션 2.2 (메뉴 트리)
화면 목록          ← 섹션 3 (마스터 테이블)
화면별 상세 설계    ← 섹션 4 (화면 수만큼)
공통 컴포넌트 목록  ← 섹션 5
shadcn 설치 목록   ← 섹션 6
```

### 1.3 출력 모드 결정

- 사용자가 "프로토타입", "빠르게 확인", "bundle" 등을 언급 → **프로토타입 모드**
- 사용자가 "프로덕션", "Next.js", "실제 프로젝트" 등을 언급 → **프로덕션 모드**
- 명시하지 않으면 → **프로토타입 모드** (기본)

---

## Phase 2: 프로젝트 초기화

### 프로토타입 모드

web-artifacts-builder 스킬의 `init-artifact.sh`로 Vite + React + shadcn 프로젝트를 생성한다.

#### 스크립트 탐색 경로 (우선순위)

```
1. {프로젝트}/.opal/community-skills/anthropics/web-artifacts-builder/scripts/
2. ~/.opal/community-skills/anthropics/web-artifacts-builder/scripts/
```

> **[MUST]** 위 경로에서 `init-artifact.sh`를 찾을 수 없으면 사용자에게 안내한다:
> "web-artifacts-builder 스킬이 설치되어 있지 않습니다. `install-mac.sh`를 실행하거나, 프로덕션 모드로 전환하세요."

#### 초기화 실행

```bash
# 프로젝트 생성
bash {web-artifacts-builder-path}/scripts/init-artifact.sh {서비스명}

# 생성 경로
{프로젝트}/wireframe-prototype/{서비스명}/
```

`init-artifact.sh`가 생성하는 프로젝트 구조:

```
{서비스명}/
├── index.html           ← Parcel 번들링 진입점
├── package.json
├── tsconfig.json
├── vite.config.ts
├── src/
│   ├── main.tsx         ← React 엔트리
│   ├── App.tsx          ← 루트 컴포넌트
│   ├── index.css        ← Tailwind + shadcn 테마 CSS
│   ├── lib/
│   │   └── utils.ts     ← cn() 유틸리티
│   └── components/
│       └── ui/          ← shadcn 컴포넌트 (40+ 프리인스톨)
├── .parcelrc
└── tailwind.config.js
```

### 프로덕션 모드

shadcn 스킬을 연계하여 Next.js App Router 프로젝트를 생성한다.

```bash
# Next.js 프로젝트 생성 + shadcn 초기화
npx shadcn@latest init --name {서비스명} --preset base-nova --template next

# 생성 경로
{프로젝트}/{서비스명}/   또는   사용자 지정 경로
```

> shadcn 스킬 참조: `~/.opal/community-skills/vercel-labs/shadcn/SKILL.md`
> `npx shadcn@latest info --json`으로 프로젝트 컨텍스트를 확인하고, aliases, isRSC, tailwindVersion 등을 반영한다.

#### shadcn 컴포넌트 설치

wireframe.md 섹션 6(shadcn 설치 목록)에 명시된 컴포넌트를 설치한다:

```bash
# 예시: wireframe.md 섹션 6에서 추출한 목록
npx shadcn@latest add sidebar card table button input select dialog badge tabs chart
```

---

## Phase 3: 공통 컴포넌트 생성

wireframe.md 섹션 5(공통 컴포넌트)를 React 컴포넌트로 구현한다.

### 3.1 구현 순서

1. **레이아웃 컴포넌트**: 전체 레이아웃 쉘 (Sidebar/NavigationMenu + 메인 영역)
2. **네비게이션 컴포넌트**: 메뉴 구조 (섹션 2.2 기반)
3. **재사용 컴포넌트**: 섹션 5 테이블의 각 컴포넌트

### 3.2 레이아웃 유형별 구현

wireframe.md 섹션 2.1의 레이아웃 유형에 따라 루트 레이아웃을 생성한다.

**사이드바 + 콘텐츠** (가장 일반적):

```tsx
// components/layout/app-layout.tsx
import { SidebarProvider, Sidebar, SidebarContent, SidebarGroup,
         SidebarGroupLabel, SidebarMenu, SidebarMenuItem,
         SidebarMenuButton } from "@/components/ui/sidebar"
import { Breadcrumb, BreadcrumbList, BreadcrumbItem,
         BreadcrumbLink } from "@/components/ui/breadcrumb"

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarContent>
          {/* 섹션 2.2 네비게이션 구조에서 메뉴그룹별 생성 */}
          <SidebarGroup>
            <SidebarGroupLabel>메뉴그룹1</SidebarGroupLabel>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton>화면명</SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroup>
        </SidebarContent>
      </Sidebar>
      <main className="flex flex-1 flex-col gap-4 p-4">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/">홈</BreadcrumbLink>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        {children}
      </main>
    </SidebarProvider>
  )
}
```

**탑바 + 콘텐츠**:

```tsx
// components/layout/app-layout.tsx
import { NavigationMenu, NavigationMenuList, NavigationMenuItem,
         NavigationMenuLink } from "@/components/ui/navigation-menu"

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <NavigationMenu>
          <NavigationMenuList>
            {/* 섹션 2.2 네비게이션 구조에서 생성 */}
          </NavigationMenuList>
        </NavigationMenu>
      </header>
      <main className="flex-1 p-4">{children}</main>
    </div>
  )
}
```

### 3.3 공통 컴포넌트 파일 배치

```
src/components/
├── layout/
│   └── app-layout.tsx        ← 전체 레이아웃
├── common/
│   ├── data-table.tsx        ← 테이블 + 페이지네이션 래퍼 (공통 사용 시)
│   ├── stat-card.tsx         ← KPI 카드 (대시보드 공통)
│   ├── status-badge.tsx      ← 상태 배지 (공통 사용 시)
│   └── ...                   ← wireframe.md 섹션 5에 명시된 컴포넌트
└── ui/                       ← shadcn 기본 컴포넌트 (설치됨)
```

---

## Phase 4: 화면별 구현

wireframe.md 섹션 4(화면별 상세 설계)를 순서대로 구현한다.

### 4.1 화면 구현 절차 (화면당)

각 화면(SCR-NNN)에 대해:

1. **메타 정보 확인**: 유형, 경로, 진입점
2. **ASCII 레이아웃 분석**: 영역 배치 파악
3. **구성 요소 테이블 → React 코드 변환**:
   - 영역별로 컴포넌트 그룹화
   - shadcn 컴포넌트 컬럼의 컴포넌트명을 직접 import하여 사용
   - 데이터/설명 컬럼을 props 또는 더미 데이터로 반영
4. **인터랙션 목록 → 이벤트 핸들러 구현**:
   - 이벤트(클릭, 입력 등) → 동작(API 호출, 상태 변경 등) → 결과(화면 갱신, 모달 표시 등)
   - 프로토타입 모드: 더미 데이터 + 상태 변경만 구현
   - 프로덕션 모드: API 호출 인터페이스까지 정의
5. **shadcn Critical Rules 검증**: 아래 인라인 규칙 준수 확인

### 4.2 화면 유형별 구현 패턴

#### dashboard (대시보드)

```tsx
// pages/dashboard.tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Chart } from "@/components/ui/chart"

export function DashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      {/* KPI 카드 영역 */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>총 주문</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">1,234</p>
          </CardContent>
        </Card>
        {/* ... 구성 요소 테이블의 KPI 항목만큼 반복 */}
      </div>
      {/* 차트 영역 */}
      {/* 테이블 영역 */}
    </div>
  )
}
```

#### crud (엔티티 관리)

```tsx
// pages/{entity}-list.tsx
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { DropdownMenu, DropdownMenuContent, DropdownMenuGroup,
         DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Pagination, PaginationContent, PaginationItem,
         PaginationNext, PaginationPrevious } from "@/components/ui/pagination"

export function EntityListPage() {
  return (
    <div className="flex flex-col gap-4">
      {/* 필터/검색 영역 */}
      <div className="flex items-center gap-2">
        <Input placeholder="검색..." />
        <Button>
          <PlusIcon data-icon="inline-start" />
          등록
        </Button>
      </div>
      {/* 데이터 테이블 */}
      <Table>
        <TableHeader>
          <TableRow>
            {/* 구성 요소 테이블의 데이터 필드명으로 컬럼 생성 */}
          </TableRow>
        </TableHeader>
        <TableBody>
          {/* 더미 데이터 행 */}
        </TableBody>
      </Table>
      <Pagination>
        <PaginationContent>
          <PaginationItem><PaginationPrevious /></PaginationItem>
          <PaginationItem><PaginationNext /></PaginationItem>
        </PaginationContent>
      </Pagination>
    </div>
  )
}
```

#### form (독립 폼)

```tsx
// pages/{entity}-form.tsx
import { FieldGroup, Field, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Select, SelectTrigger, SelectValue, SelectContent,
         SelectGroup, SelectItem } from "@/components/ui/select"
import { Button } from "@/components/ui/button"

export function EntityFormPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <FieldGroup>
        <Field>
          <FieldLabel htmlFor="name">이름</FieldLabel>
          <Input id="name" />
        </Field>
        <Field>
          <FieldLabel htmlFor="type">유형</FieldLabel>
          <Select>
            <SelectTrigger>
              <SelectValue placeholder="선택" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="a">유형 A</SelectItem>
                <SelectItem value="b">유형 B</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </Field>
      </FieldGroup>
      <div className="flex justify-end gap-2 pt-4">
        <Button variant="outline">취소</Button>
        <Button>저장</Button>
      </div>
    </div>
  )
}
```

#### auth (인증)

```tsx
// pages/login.tsx
import { Card, CardHeader, CardTitle, CardDescription,
         CardContent, CardFooter } from "@/components/ui/card"
import { FieldGroup, Field, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>로그인</CardTitle>
          <CardDescription>계정에 로그인하세요</CardDescription>
        </CardHeader>
        <CardContent>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="email">이메일</FieldLabel>
              <Input id="email" type="email" />
            </Field>
            <Field>
              <FieldLabel htmlFor="password">비밀번호</FieldLabel>
              <Input id="password" type="password" />
            </Field>
          </FieldGroup>
        </CardContent>
        <CardFooter>
          <Button className="w-full">로그인</Button>
        </CardFooter>
      </Card>
    </div>
  )
}
```

> 기타 화면 유형(detail, settings, report, monitor)도 동일한 방식으로 구성 요소 테이블의 shadcn 컴포넌트를 조합하여 구현한다.

### 4.3 프로토타입 모드: 라우팅 구성

프로토타입 모드에서는 단일 `App.tsx`에서 탭 또는 간단한 상태 기반 라우팅으로 전체 화면을 구성한다:

```tsx
// src/App.tsx
import { useState } from "react"
import { AppLayout } from "@/components/layout/app-layout"

// 각 화면 import
import { DashboardPage } from "@/pages/dashboard"
import { EntityListPage } from "@/pages/entity-list"
// ...

const PAGES: Record<string, React.ComponentType> = {
  "dashboard": DashboardPage,
  "entity-list": EntityListPage,
  // wireframe.md 섹션 3 화면 목록의 경로를 키로 사용
}

export default function App() {
  const [currentPage, setCurrentPage] = useState("dashboard")
  const PageComponent = PAGES[currentPage] ?? DashboardPage

  return (
    <AppLayout onNavigate={setCurrentPage} currentPage={currentPage}>
      <PageComponent />
    </AppLayout>
  )
}
```

### 4.4 프로덕션 모드: App Router 매핑

wireframe.md 섹션 3의 경로 필드를 Next.js App Router 파일 구조로 매핑한다:

```
wireframe.md 경로    →  Next.js 파일
/                    →  app/page.tsx
/dashboard           →  app/dashboard/page.tsx
/users               →  app/users/page.tsx
/users/[id]          →  app/users/[id]/page.tsx
/settings            →  app/settings/page.tsx
```

레이아웃 컴포넌트는 `app/layout.tsx`에 배치한다.

> **[MUST]** `isRSC`가 true인 프로젝트에서 `useState`, `useEffect`, 이벤트 핸들러를 사용하는 컴포넌트에는 반드시 파일 최상단에 `"use client"`를 추가한다.

### 4.5 서브 에이전트 위임 (5화면 이상)

화면 수가 5개 이상일 경우, 서브 에이전트에 화면별 구현을 위임한다.

#### 위임 규칙

- **메인 에이전트 담당**: Phase 1~3 (입력 파싱, 프로젝트 초기화, 공통 컴포넌트)
- **서브 에이전트 위임**: Phase 4 화면별 구현

#### 서브 에이전트에 전달할 컨텍스트

```
1. wireframe.md의 해당 화면 섹션 (섹션 4의 SCR-NNN 부분)
2. 공통 컴포넌트 경로: src/components/common/, src/components/layout/
3. shadcn Critical Rules (아래 인라인 요약)
4. 프로젝트 경로 (절대 경로)
5. 출력 모드 (프로토타입/프로덕션)
```

#### 서브 에이전트 프롬프트 템플릿

```
## 태스크
wireframe.md의 화면 {SCR-NNN} {화면명}을 React + shadcn/ui로 구현하라.

## 입력
- wireframe.md 화면 섹션: [해당 섹션 내용 붙여넣기]
- 공통 컴포넌트 경로: {프로젝트 경로}/src/components/
- shadcn 컴포넌트 경로: {프로젝트 경로}/src/components/ui/

## shadcn Critical Rules
- FieldGroup + Field 폼 구조 (raw div 금지)
- gap-* 레이아웃 (space-x/y 금지)
- 시맨틱 컬러 변수 사용 (raw 컬러 금지)
- data-icon 속성 사용 (수동 아이콘 사이징 금지)
- Items는 반드시 Group 안에 배치
- Dialog/Sheet/Drawer는 Title 필수

## 산출물
- 파일 경로: {프로젝트 경로}/src/pages/{화면명}.tsx
- import는 @/ alias 사용
```

---

## Phase 5: 빌드 및 산출물 생성

### 프로토타입 모드

web-artifacts-builder의 `bundle-artifact.sh`로 단일 HTML을 생성한다.

#### 스크립트 탐색 경로 (우선순위)

```
1. {프로젝트}/.opal/community-skills/anthropics/web-artifacts-builder/scripts/
2. ~/.opal/community-skills/anthropics/web-artifacts-builder/scripts/
```

#### 번들링 실행

```bash
# 프로젝트 디렉토리로 이동
cd {프로젝트}/wireframe-prototype/{서비스명}/

# 번들링 실행
bash {web-artifacts-builder-path}/scripts/bundle-artifact.sh
```

`bundle-artifact.sh`가 수행하는 작업:

1. 번들링 의존성 설치 (parcel, @parcel/config-default, parcel-resolver-tspaths, html-inline)
2. `.parcelrc` 생성 (path alias 지원)
3. Parcel 빌드 (no source maps)
4. html-inline으로 모든 에셋을 단일 HTML에 인라인

#### 산출물

```
{프로젝트}/wireframe-prototype/{서비스명}/bundle.html
```

> 브라우저에서 `bundle.html`을 직접 열어 확인할 수 있다.

### 프로덕션 모드

프로젝트 디렉토리를 `next dev`로 실행 가능한 상태로 완성한다.

```bash
# 개발 서버 시작 안내
cd {프로젝트}/{서비스명}/
npm run dev   # 또는 pnpm dev
```

#### 산출물

```
{프로젝트}/{서비스명}/              ← Next.js 프로젝트 전체
├── app/
│   ├── layout.tsx               ← 공통 레이아웃
│   ├── page.tsx                 ← 메인 페이지
│   └── {경로별}/page.tsx         ← wireframe.md 화면별 페이지
├── components/
│   ├── layout/                  ← 레이아웃 컴포넌트
│   ├── common/                  ← 공통 컴포넌트
│   └── ui/                      ← shadcn 컴포넌트
└── ...
```

### 완료 보고

```
[ui-designer] 완료 보고

출력 모드: {프로토타입 / 프로덕션}
서비스명: {서비스명}
구현 화면: {N}개
  - SCR-001 {화면명} ({유형})
  - SCR-002 {화면명} ({유형})
  - ...

산출물 경로:
  - 프로토타입: {프로젝트}/wireframe-prototype/{서비스명}/bundle.html
  - 프로덕션: {프로젝트}/{서비스명}/

{빌드 오류 또는 주의사항이 있으면 여기에 기재}
```

---

## shadcn Critical Rules (인라인 요약)

> **전체 규칙 참조 경로** (우선순위):
> 1. `{프로젝트}/.opal/community-skills/vercel-labs/shadcn/SKILL.md`
> 2. `~/.opal/community-skills/vercel-labs/shadcn/SKILL.md`
> 3. `~/.opal/community-skills/vercel-labs/shadcn/rules/composition.md`
> 4. `~/.opal/community-skills/vercel-labs/shadcn/rules/forms.md`
>
> 위 경로에서 shadcn 스킬을 찾으면 해당 파일의 규칙을 우선 적용한다.
> 찾을 수 없는 경우 아래 인라인 요약을 적용한다.

### 스타일링

- **`className`은 레이아웃 전용**: 컴포넌트의 색상/타이포그래피를 className으로 오버라이드하지 않는다.
- **`gap-*` 사용, `space-x/y-*` 금지**: 수직 스택은 `flex flex-col gap-*`.
- **`size-*` 사용**: 가로/세로가 동일하면 `size-10` (not `w-10 h-10`).
- **시맨틱 컬러 사용**: `bg-primary`, `text-muted-foreground` (not `bg-blue-500`).
- **수동 `dark:` 오버라이드 금지**: 시맨틱 토큰 사용.
- **`cn()`으로 조건부 클래스**: 템플릿 리터럴 삼항 연산 금지.

### 폼

- **`FieldGroup` + `Field` 필수**: raw `div` + `space-y-*`로 폼 레이아웃 금지.
- **`InputGroup` 안에서 `InputGroupInput`/`InputGroupTextarea` 사용**: raw `Input`/`Textarea` 금지.
- **2~7개 선택지는 `ToggleGroup`**: `Button` 반복 + 수동 active 상태 금지.
- **`FieldSet` + `FieldLegend`로 관련 체크박스/라디오 그룹화**.
- **유효성 검사**: `Field`에 `data-invalid`, 컨트롤에 `aria-invalid`.

### 컴포넌트 구조

- **Items는 반드시 Group 안에**: `SelectItem` → `SelectGroup`, `DropdownMenuItem` → `DropdownMenuGroup`, `CommandItem` → `CommandGroup`.
- **Dialog/Sheet/Drawer에 Title 필수**: 접근성. 시각적으로 숨기려면 `className="sr-only"`.
- **Card 풀 컴포지션**: `CardHeader`/`CardTitle`/`CardDescription`/`CardContent`/`CardFooter`.
- **`TabsTrigger`는 `TabsList` 안에**: `Tabs` 직접 하위에 배치 금지.
- **`Avatar`에 `AvatarFallback` 필수**.

### 아이콘

- **`data-icon` 속성 사용**: `data-icon="inline-start"` 또는 `data-icon="inline-end"`.
- **컴포넌트 내 아이콘에 사이징 클래스 금지**: 컴포넌트가 CSS로 처리.
- **아이콘은 객체로 전달**: `icon={CheckIcon}` (not string).

### 컴포넌트 우선

- **커스텀 마크업 전에 기존 컴포넌트 확인**: `Alert`(콜아웃), `Empty`(빈 상태), `Badge`(상태 태그), `Skeleton`(로딩), `Separator`(구분선), `sonner`(토스트).

---

## wireframe.md 입력 스키마

ui-designer가 입력으로 받는 wireframe.md의 구조:

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

### 화면 ID 체계

- `SCR-{NNN}` 형식 (예: SCR-001, SCR-002)
- 3자리 순번, 도출 순서대로 부여
- 섹션 3(화면 목록)과 섹션 4(화면별 상세 설계)에서 동일 ID 사용

### 화면 유형

| 유형 코드 | 설명 | 핵심 shadcn 컴포넌트 |
|----------|------|---------------------|
| `dashboard` | 현황/통계 대시보드 | Card, Chart, Badge, Table |
| `crud` | 엔티티 관리 (목록+등록/수정) | Table, Pagination, Dialog/Sheet, Input, DropdownMenu |
| `detail` | 상세 보기 | Card, Tabs, Badge, Separator |
| `form` | 독립 폼 | FieldGroup, Field, Input, Select, Button |
| `settings` | 설정 | Tabs, Switch, Input, Separator |
| `report` | 보고서/분석 | Chart, Table, Select(필터) |
| `auth` | 인증 (로그인/회원가입) | Card, FieldGroup, Field, Input, Button |
| `monitor` | 실시간 모니터링 | Card, Badge, Chart, ScrollArea |

### 구성 요소 테이블 규칙

| 컬럼 | 설명 | ui-designer 사용 방법 |
|------|------|---------------------|
| 영역 | 화면 내 위치 (header, filter, content 등) | 컴포넌트 그룹화 및 배치 기준 |
| UI 요소 | 사용자에게 보이는 요소명 | 변수명/주석으로 반영 |
| shadcn 컴포넌트 | 해당 요소 구현에 사용할 shadcn 컴포넌트명 | 직접 import하여 코드 생성 |
| 데이터/설명 | 표시할 데이터 필드명 또는 동작 설명 | props/더미 데이터/핸들러로 반영 |

---

## web-artifacts-builder 연계 상세

### 참조 경로 (우선순위)

```
1. {프로젝트}/.opal/community-skills/anthropics/web-artifacts-builder/
2. ~/.opal/community-skills/anthropics/web-artifacts-builder/
```

### 호출 스크립트

| 스크립트 | 용도 | 호출 시점 |
|---------|------|----------|
| `scripts/init-artifact.sh <프로젝트명>` | React + Vite + Tailwind + shadcn 프로젝트 스캐폴드 | Phase 2 (프로토타입 모드) |
| `scripts/bundle-artifact.sh` | Parcel + html-inline → 단일 bundle.html | Phase 5 (프로토타입 모드) |

### init-artifact.sh 요구사항

- Node.js 18+ 필수
- pnpm 미설치 시 자동 설치
- 40+ shadcn/ui 컴포넌트 프리인스톨 (tar.gz에서 추출)
- Tailwind CSS 3.4.1 + shadcn 테마 시스템

### bundle-artifact.sh 요구사항

- 프로젝트 루트에 `package.json`, `index.html` 존재 필수
- pnpm 사용 (의존성 설치 및 빌드)
- 산출물: 프로젝트 루트에 `bundle.html` 생성

---

## 주의사항

1. **wireframe.md 없이 실행 금지**: wireframe.md가 없으면 wireframe-builder 스킬 사용을 안내한다.
2. **shadcn 컴포넌트명 정확성**: wireframe.md의 구성 요소 테이블에 명시된 shadcn 컴포넌트명을 그대로 사용한다. 존재하지 않는 컴포넌트명이 있으면 사용자에게 확인한다.
3. **더미 데이터 원칙**: 프로토타입 모드에서는 현실적인 한국어 더미 데이터를 사용한다 (lorem ipsum 금지).
4. **코드 재사용성**: 프로토타입에서 작성한 컴포넌트가 프로덕션에서도 동작하도록, React + shadcn 표준 패턴만 사용한다.
5. **AI Slop 방지**: 지나친 중앙 정렬, 보라색 그라디언트, 균일한 둥근 모서리, Inter 폰트 남용을 피한다.
