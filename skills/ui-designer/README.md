# ui-designer (uid)

`wireframe.md` 또는 `PLAN.md`의 화면 설계를 입력받아 React + shadcn/ui 기반 UI를 실제로 구현하는 스킬.

## 개요

두 가지 모드를 지원합니다.

| 모드 | 입력 | 용도 |
|------|------|------|
| **scaffold** | wireframe.md | 새 프로젝트를 처음부터 생성 (프로토타입 또는 프로덕션) |
| **plan-driven** | PLAN.md §3.N.2 FE 화면 설계 | 기존 프로젝트에 화면을 추가/수정 |

입력 형식으로 모드가 자동 판별됩니다: wireframe.md가 입력이면 scaffold, opal-pilot EXECUTE 단계에서 호출되면 plan-driven입니다. 사용자가 "프로토타입"이라고 명시하면 scaffold, "프로젝트에 화면 추가/수정"이라고 명시하면 plan-driven이 적용됩니다.

## 언제 쓰나

- "UI 구현", "UI 만들어줘", "화면 구현", "wireframe 구현", "프로토타입 만들어줘"를 요청받았을 때
- `wireframe-builder`로 만든 `wireframe.md`를 실제 화면으로 만들어야 할 때
- PLAN.md 기반 FE 화면 구현이 필요할 때 (opal-pilot EXECUTE 단계)

## 사용법

호출: `//uid`

### scaffold 모드

| 항목 | 내용 |
|------|------|
| 입력 | `wireframe.md` (필수 — 없으면 wireframe-builder 스킬 사용을 안내) |
| 출력 모드 | "프로토타입", "빠르게 확인" 언급 시 프로토타입(기본) / "프로덕션", "Next.js" 언급 시 프로덕션 |

1. wireframe.md의 6개 필수 섹션(서비스 개요/전체 구조/화면 목록/화면별 상세 설계/공통 컴포넌트/shadcn 설치 목록)을 확인합니다.
2. **프로토타입 모드**: `web-artifacts-builder` 스킬의 `init-artifact.sh`로 Vite + React + shadcn 프로젝트를 `wireframe-prototype/{서비스명}/`에 생성합니다.
3. **프로덕션 모드**: `npx shadcn@latest init`으로 Next.js App Router 프로젝트를 생성합니다.
4. 공통 컴포넌트(레이아웃, 네비게이션)를 먼저 구현한 뒤, 화면을 화면 목록 순서대로 구현합니다. 화면이 5개 이상이면 서브 에이전트에 화면별 구현을 위임합니다.
5. 프로토타입은 `bundle-artifact.sh`로 단일 HTML로 번들링합니다.

### plan-driven 모드

| 항목 | 내용 |
|------|------|
| 입력 | PLAN.md §3.N.2의 `##### 화면: {화면명}` 서브섹션 (ID, 유형, action, 경로, 파일, shadcn 컴포넌트, UI 작업, API 연동 필드 포함) |
| 폴백 입력 | (PLAN.md에 해당 섹션이 없는 과거 태스크용) execution-plan.json의 screen 객체 |

1. 입력을 파악하고 기존 프로젝트 구조(디렉토리 구성, 컴포넌트 패턴, shadcn 설치 여부, 라우팅 방식)를 확인합니다. 기존 패턴과의 일관성을 최우선으로 합니다.
2. `action: new`이면 지정된 파일들을 새로 생성, `action: modify`이면 기존 파일을 Read한 뒤 명시된 변경사항을 적용합니다.
3. 명시된 shadcn 컴포넌트가 미설치면 `npx shadcn@latest add {component}`로 설치합니다.
4. shadcn Critical Rules 준수와 기존 프로젝트 패턴 일관성, TypeScript 타입 안전성을 검증합니다.

## 화면 유형별 구현 패턴 (공통)

| 유형 | 핵심 shadcn 컴포넌트 |
|------|---------------------|
| dashboard | Card, Chart, Badge, Table |
| crud | Table, Pagination, Dialog/Sheet, Input, DropdownMenu |
| detail | Card, Tabs, Badge, Separator |
| form | FieldGroup, Field, Input, Select, Button |
| settings | Tabs, Switch, Input, Separator |
| report | Chart, Table, Select(필터) |
| auth | Card, FieldGroup, Field, Input, Button |
| monitor | Card, Badge, Chart, ScrollArea |

주요 규칙(shadcn Critical Rules): `FieldGroup`+`Field`로 폼 구성(raw div 금지), `gap-*` 레이아웃(space-x/y 금지), 시맨틱 컬러 토큰 사용(raw 색상 금지), `data-icon` 속성으로 아이콘 배치, 리스트형 Item은 반드시 Group 안에 배치, Dialog/Sheet/Drawer에는 Title 필수.

## 동작 흐름

```
입력 판별 (wireframe.md → scaffold / PLAN.md §3.N.2 → plan-driven)
  │
  ├─ scaffold: 입력 파싱 → 프로젝트 초기화 → 공통 컴포넌트 → 화면별 구현 → 빌드/번들링
  │
  └─ plan-driven: 입력 파악+구조 확인 → action별 실행(new/modify) → 컴포넌트 설치 확인 → 검증
```

## 산출물

| 모드 | 산출물 위치 |
|------|-----------|
| scaffold · 프로토타입 | `{프로젝트}/wireframe-prototype/{서비스명}/bundle.html` (브라우저에서 바로 열기 가능한 단일 HTML) |
| scaffold · 프로덕션 | `{프로젝트}/{서비스명}/` 아래 Next.js 프로젝트 전체 (`app/`, `components/` 등) |
| plan-driven | 기존 프로젝트 내 생성/수정된 파일 목록 (별도 번들링 없음, 기존 빌드 시스템 사용) |

완료 시 구현한 화면 목록(SCR-ID, 화면명, 유형)과 산출물 경로를 보고합니다.

## FAQ

### wireframe.md 없이 실행할 수 있나요?
아니요. wireframe.md가 없으면 실행을 중단하고 `wireframe-builder` 스킬 사용을 안내합니다.

### wireframe.md에 없는 shadcn 컴포넌트명이 있으면 어떻게 되나요?
존재하지 않는 컴포넌트명이 있으면 임의로 대체하지 않고 사용자에게 확인합니다.
