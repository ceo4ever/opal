# 클라이언트 프로젝트 구조 상세 가이드

## 디렉토리 구조 및 역할

### app/ (Next.js App Router)

#### layout.tsx
- 루트 레이아웃
- ThemeProvider 설정
- 전역 스타일 및 폰트 설정

#### page.tsx
- 홈 페이지
- DefaultLayout 사용

#### admin/
- Admin 관련 페이지들
- `layout.tsx`: AdminLayout 적용
- `page.tsx`: Admin 대시보드
- `todos/page.tsx`: Todo 관리 페이지
- `settings/page.tsx`: 설정 페이지

#### views/
- 화면 컴포넌트 (View Layer)
- 페이지별 비즈니스 로직이 있는 컴포넌트
- `home-view.tsx`: 홈 화면
- `todos/todo-form-dialog.tsx`: Todo 폼 다이얼로그

### components/ (재사용 가능한 컴포넌트)

#### layout/
- **header.tsx**: 헤더 컴포넌트 (다크모드 토글 포함)
- **footer.tsx**: 푸터 컴포넌트
- **sidebar.tsx**: 사이드바 컴포넌트 (Admin 전용)
- **default-layout.tsx**: 기본 레이아웃 (헤더/본문/푸터)
- **admin-layout.tsx**: Admin 레이아웃 (헤더/사이드바/본문)

#### providers/
- **theme-provider.tsx**: 다크모드 Theme Provider

### lib/ (유틸리티 및 라이브러리)

#### api/
- **client.ts**: OpenAPI 클라이언트 설정
- **types.ts**: API 타입 정의

#### utils.ts
- 유틸리티 함수 (cn 함수 등)

### stores/ (Zustand 스토어)

#### todo-store.ts
- Todo 관련 전역 상태 관리
- 서비스 레이어 호출

### services/ (서비스 레이어)

도메인별 서비스 파일을 여기에 작성합니다.
- API 클라이언트 호출 및 데이터 가공
- View에서 직접 호출

## 데이터 흐름

```
사용자 액션
    ↓
View Component (views/)
    ↓
Service Layer (services/)
    ↓
API Client (lib/api/)
    ↓
서버 API (backend)
    ↓
응답 처리
    ↓
View 리렌더링
```

## 컴포넌트 계층 구조

```
RootLayout (app/layout.tsx)
  └── ThemeProvider
      └── DefaultLayout 또는 AdminLayout
          ├── Header
          ├── Sidebar (AdminLayout만)
          ├── Main Content
          │   └── View Component
          └── Footer (DefaultLayout만)
```

## 상태 관리 패턴

### Zustand Store 구조

```tsx
interface TodoState {
  todos: Todo[];
  loading: boolean;
  error: string | null;
  fetchTodos: () => Promise<void>;
  createTodo: (data) => Promise<void>;
  // ...
}

export const useTodoStore = create<TodoState>((set) => ({
  // 상태 및 액션 정의
}));
```

### 사용 예시

```tsx
"use client";

import { useTodoStore } from "@/stores/todo-store";

export function MyComponent() {
  const { todos, loading, fetchTodos } = useTodoStore();

  useEffect(() => {
    fetchTodos();
  }, [fetchTodos]);

  // ...
}
```

## API 클라이언트 패턴

### OpenAPI 클라이언트 사용

```tsx
import { apiClient } from "@/lib/api/client";

// GET 요청
const { data, error } = await apiClient.GET("/api/v1/sample/todos", {
  params: {
    query: { memberNo: 1 },
  },
});

// POST 요청
const formData = new URLSearchParams();
formData.append("title", "새 Todo");
const { data, error } = await apiClient.POST("/api/v1/sample/todos", {
  body: formData,
  headers: {
    "Content-Type": "application/x-www-form-urlencoded",
  },
});
```

## 스타일링

### Tailwind CSS

유틸리티 우선 CSS 프레임워크 사용

### 다크 모드

`next-themes`를 사용하여 다크 모드 지원

```tsx
import { useTheme } from "next-themes";

const { theme, setTheme } = useTheme();
```

## 개발 가이드

### 새 페이지 추가

1. `app/{route}/page.tsx` 생성
2. 필요시 `app/views/{view-name}.tsx` 생성
3. 적절한 Layout 선택 (DefaultLayout 또는 AdminLayout)

### 새 컴포넌트 추가

1. `components/{category}/{component-name}.tsx` 생성
2. 재사용 가능한 컴포넌트로 설계

### 새 Store 추가

1. `stores/{store-name}.ts` 생성
2. Zustand 패턴 따라 구현

### 새 API 엔드포인트 연동

1. `npm run openapi:regen`으로 타입 재생성
2. `lib/api/client.ts`에 편의 함수 추가 (필요시)
3. `services/`에 서비스 함수 추가
4. View에서 서비스 호출

## 주의사항

1. **클라이언트 컴포넌트**: 상호작용이 필요한 컴포넌트는 `"use client"` 지시어 필요
2. **서버 컴포넌트**: 기본적으로 서버 컴포넌트이므로 클라이언트 기능 사용 시 주의
3. **환경 변수**: `NEXT_PUBLIC_` 접두사가 있어야 클라이언트에서 접근 가능
4. **API URL**: `.env.local`에서 설정 필요
