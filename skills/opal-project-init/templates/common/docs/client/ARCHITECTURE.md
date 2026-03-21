# 클라이언트 아키텍처 가이드

Next.js 기반 클라이언트의 아키텍처 및 디렉토리 구조에 대한 상세 가이드입니다.

## 핵심 원칙

### 1. Routing과 View 분리

**원칙**: Next.js의 App Router(`app/`)는 라우팅만 담당하고, 실제 화면 로직은 `app/views/`에서 관리합니다.

**장점**:
- 코드의 책임이 명확하게 분리됨
- 뷰 컴포넌트를 여러 라우트에서 재사용 가능
- 테스트가 용이함
- 비즈니스 로직과 라우팅 로직의 분리

**구조**:
```
app/
├── page.tsx                    # "/" - 라우팅만
├── admin/
│   ├── page.tsx               # "/admin" - 라우팅만
│   ├── todos/
│   │   └── page.tsx          # "/admin/todos" - 라우팅만
│   └── settings/
│       └── page.tsx          # "/admin/settings" - 라우팅만
└── views/
    ├── home-view.tsx          # 홈 화면 뷰
    ├── admin/
    │   └── admin-dashboard-view.tsx  # Admin 대시보드 뷰
    ├── todos/
    │   ├── todos-view.tsx     # Todo 목록 뷰
    │   ├── todo-list.tsx      # Todo 목록 컴포넌트
    │   └── todo-form-dialog.tsx  # Todo 폼 컴포넌트
    └── settings/
        └── settings-view.tsx  # 설정 뷰
```

### 2. 컴포넌트 계층

```
Page (Routing)
  ↓
View (UI 로직, 사용자 상호작용)
  ↓
Service (비즈니스 로직, 데이터 가공)
  ↓
API Client (서버 통신)
```

**예시**:
```tsx
// app/admin/todos/page.tsx (Routing)
import { TodosView } from "@/app/views/todos/todos-view";

export default function TodosPage() {
  return <TodosView />;
}

// app/views/todos/todos-view.tsx (View)
"use client";

import { useTodoStore } from "@/stores/todo-store";
import { TodoList } from "./todo-list";

export function TodosView() {
  const { todos, fetchTodos } = useTodoStore();
  // 비즈니스 로직 및 상태 관리

  return <TodoList todos={todos} />;
}

// app/views/todos/todo-list.tsx (Component)
interface TodoListProps {
  todos: Todo[];
}

export function TodoList({ todos }: TodoListProps) {
  // UI 렌더링만
  return <div>...</div>;
}
```

## 디렉토리 구조 상세

### `/app` - Next.js App Router

**역할**: 라우팅 정의 및 레이아웃 구성

```
app/
├── layout.tsx              # 루트 레이아웃
├── page.tsx               # 홈 페이지 (라우팅)
├── globals.css            # 글로벌 스타일
├── admin/
│   ├── layout.tsx        # Admin 레이아웃
│   ├── page.tsx          # Admin 대시보드 (라우팅)
│   ├── todos/
│   │   └── page.tsx     # Todo 관리 페이지 (라우팅)
│   └── settings/
│       └── page.tsx     # 설정 페이지 (라우팅)
└── views/                # 뷰 컴포넌트 (아래 참조)
```

**규칙**:
- `page.tsx`는 라우팅만 담당
- 비즈니스 로직은 `views/`로 분리
- `layout.tsx`는 레이아웃 구조만 정의

### `/app/views` - View Components

**역할**: 화면별 비즈니스 로직 및 상태 관리

```
app/views/
├── home-view.tsx          # 홈 화면
├── admin/
│   └── admin-dashboard-view.tsx  # Admin 대시보드
├── todos/
│   ├── todos-view.tsx     # Todo 목록 화면
│   ├── todo-list.tsx      # Todo 목록 컴포넌트
│   └── todo-form-dialog.tsx  # Todo 폼 컴포넌트
└── settings/
    └── settings-view.tsx  # 설정 화면
```

**규칙**:
- `"use client"` 디렉티브 사용 (상태 관리 필요 시)
- Zustand 스토어를 통한 상태 관리
- 하위 컴포넌트에 props 전달
- `-view` 접미사 사용 (화면 단위 뷰)

### `/components` - Shared Components

**역할**: 재사용 가능한 공통 컴포넌트

```
components/
├── layout/
│   ├── header.tsx         # 헤더
│   ├── footer.tsx         # 푸터
│   ├── sidebar.tsx        # 사이드바
│   ├── default-layout.tsx # 기본 레이아웃
│   └── admin-layout.tsx   # Admin 레이아웃
└── providers/
    └── theme-provider.tsx # 테마 프로바이더
```

**규칙**:
- 도메인 로직에 의존하지 않음
- props를 통해 데이터 전달
- 재사용 가능하도록 설계

### `/stores` - State Management

**역할**: Zustand를 사용한 전역 상태 관리

```
stores/
├── todo-store.ts          # Todo 상태 관리
└── auth-store.ts          # 인증 상태 관리 (예시)
```

**규칙**:
- 각 도메인별로 별도 스토어 생성
- 서비스 레이어 호출
- UI 상태 관리

### `/services` - Service Layer

**역할**: 비즈니스 로직 및 API 호출 추상화

```
services/
└── {domain}_service.ts    # 도메인별 서비스
```

**규칙**:
- API 클라이언트 호출 및 데이터 가공
- View에서 직접 호출
- 에러 처리 및 변환 로직

### `/lib` - Utilities and Libraries

**역할**: 유틸리티 함수, API 클라이언트, 설정 등

```
lib/
├── api/
│   ├── client.ts          # OpenAPI 클라이언트
│   └── types.ts           # API 타입 정의
├── config/
│   └── env.ts             # 환경 변수
└── utils.ts               # 유틸리티 함수
```

**규칙**:
- 순수 함수로 구성
- 도메인 로직과 독립적
- 타입 안전성 보장

## 데이터 흐름

### 1. 사용자 액션 → 서비스 호출 → UI 렌더링

```
User Action (View)
  ↓
Service Layer (services/)
  ↓
API Call (lib/api)
  ↓
UI Re-render (View)
```

**예시**:
```tsx
// 1. View에서 사용자 액션
export function TodosView() {
  const { createTodo } = useTodoStore();

  const handleSubmit = async (data) => {
    await createTodo(data);  // 2. Store 액션 호출
  };
}

// 2. Store에서 API 호출 및 상태 업데이트
export const useTodoStore = create((set) => ({
  todos: [],
  createTodo: async (data) => {
    const response = await apiClient.POST("/api/v1/sample/todos", {
      body: data,
    });  // 3. API 호출

    set({ todos: response.data });  // 4. 상태 업데이트
  },
}));

// 5. View가 자동으로 리렌더링
```

## 파일 네이밍 규칙

### 1. 라우팅 파일 (app/)
- `page.tsx` - 페이지 라우트
- `layout.tsx` - 레이아웃
- `loading.tsx` - 로딩 상태
- `error.tsx` - 에러 상태
- `not-found.tsx` - 404 페이지

### 2. 뷰 컴포넌트 (app/views/)
- `{name}-view.tsx` - 화면 단위 뷰 컴포넌트
- `{name}-list.tsx` - 목록 컴포넌트
- `{name}-form.tsx` - 폼 컴포넌트
- `{name}-dialog.tsx` - 다이얼로그 컴포넌트

### 3. 공통 컴포넌트 (components/)
- `{name}.tsx` - 일반 컴포넌트
- `{name}-layout.tsx` - 레이아웃 컴포넌트
- `{name}-provider.tsx` - Provider 컴포넌트

### 4. 스토어 (stores/)
- `{name}-store.ts` - Zustand 스토어

## Best Practices

### 1. Routing과 View 분리
```tsx
// BAD: 라우팅 파일에 비즈니스 로직
export default function TodosPage() {
  const [todos, setTodos] = useState([]);
  // 많은 비즈니스 로직...
  return <div>...</div>;
}

// GOOD: 라우팅과 뷰 분리
export default function TodosPage() {
  return <TodosView />;
}
```

### 2. Props를 통한 데이터 전달
```tsx
// BAD: 하위 컴포넌트에서 직접 Store 접근
export function TodoList() {
  const { todos } = useTodoStore();  // 재사용성 저하
  return <div>...</div>;
}

// GOOD: Props를 통한 데이터 전달
export function TodoList({ todos }: { todos: Todo[] }) {
  return <div>...</div>;
}
```

### 3. 단일 책임 원칙
```tsx
// BAD: 하나의 컴포넌트가 너무 많은 책임
export function TodosView() {
  // 목록, 폼, 필터, 통계 모두 처리
}

// GOOD: 책임 분리
export function TodosView() {
  return (
    <>
      <TodoStats />
      <TodoFilter />
      <TodoList />
      <TodoFormDialog />
    </>
  );
}
```

### 4. 타입 안전성
```tsx
// BAD: any 타입 사용
const handleSubmit = (data: any) => { ... };

// GOOD: 명확한 타입 정의
interface TodoFormData {
  title: string;
  description?: string;
  completed: string;
}

const handleSubmit = (data: TodoFormData) => { ... };
```

## 새 기능 추가 시 체크리스트

1. **라우팅 추가**
   - [ ] `app/{path}/page.tsx` 생성
   - [ ] 필요시 `layout.tsx` 추가

2. **뷰 컴포넌트 생성**
   - [ ] `app/views/{name}/{name}-view.tsx` 생성
   - [ ] 비즈니스 로직 구현

3. **하위 컴포넌트 생성**
   - [ ] 재사용 가능한 컴포넌트 분리
   - [ ] Props 인터페이스 정의

4. **상태 관리**
   - [ ] Zustand 스토어 생성 (필요시)
   - [ ] API 호출 로직 구현

5. **타입 정의**
   - [ ] `lib/api/types.ts`에 타입 추가
   - [ ] 인터페이스 및 타입 정의

6. **문서화**
   - [ ] 코드 주석 추가
   - [ ] README 업데이트 (필요시)

## 참고 자료

- [Next.js App Router 공식 문서](https://nextjs.org/docs/app)
- [Zustand 공식 문서](https://zustand-demo.pmnd.rs/)
- [React 컴포넌트 설계 패턴](https://react.dev/learn/thinking-in-react)
