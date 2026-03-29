---
name: ui-designer
description: |
  **UI 구현 스킬**. 두 가지 모드를 지원합니다:
  1. **scaffold 모드**: wireframe.md를 입력으로 받아 전체 프로젝트를 새로 생성
  2. **plan-driven 모드**: execution-plan.json의 screen 객체를 입력으로 받아 기존 프로젝트에 화면을 추가/수정
  반드시 이 스킬을 사용해야 하는 상황: "UI 구현", "UI 만들어줘", "화면 구현",
  "wireframe 구현", "프로토타입 만들어줘", wireframe.md 기반 UI 생성 요청,
  execution-plan.json 기반 FE 화면 구현.
---

# UI Designer 스킬

wireframe.md 또는 execution-plan.json을 입력으로 받아 React + shadcn/ui 기반 UI를 구현한다.

## 모드 판별

| 모드 | 입력 | 파이프라인 파일 | 용도 |
|------|------|--------------|------|
| **scaffold** | wireframe.md | `modes/scaffold.md` | 새 프로젝트 생성 (프로토타입/프로덕션) |
| **plan-driven** | execution-plan.json screen 객체 | `modes/plan-driven.md` | 프로젝트에 화면 추가/수정 |

**판별 규칙**:
- wireframe.md가 입력 → scaffold 모드
- opal-pilot EXECUTE에서 호출 → plan-driven 모드
- 사용자 명시 ("프로토타입") → scaffold 모드
- 사용자 명시 ("프로젝트에", "화면 추가", "화면 수정") → plan-driven 모드
- 명시하지 않으면 입력물로 판별

모드 판별 후 해당 파이프라인 파일을 Read하여 프로세스를 따른다.

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

## 화면 유형별 구현 패턴

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

## 주의사항

1. **wireframe.md 없이 실행 금지**: wireframe.md가 없으면 wireframe-builder 스킬 사용을 안내한다.
2. **shadcn 컴포넌트명 정확성**: wireframe.md의 구성 요소 테이블에 명시된 shadcn 컴포넌트명을 그대로 사용한다. 존재하지 않는 컴포넌트명이 있으면 사용자에게 확인한다.
3. **더미 데이터 원칙**: 프로토타입 모드에서는 현실적인 한국어 더미 데이터를 사용한다 (lorem ipsum 금지).
4. **코드 재사용성**: 프로토타입에서 작성한 컴포넌트가 프로덕션에서도 동작하도록, React + shadcn 표준 패턴만 사용한다.
5. **AI Slop 방지**: 지나친 중앙 정렬, 보라색 그라디언트, 균일한 둥근 모서리, Inter 폰트 남용을 피한다.
