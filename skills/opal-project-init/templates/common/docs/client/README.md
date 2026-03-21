# 클라이언트 프로젝트 가이드

{{TECH_STACK_FRONTEND}} 기반 웹 클라이언트 보일러플레이트입니다.

## 기술 스택

- **Next.js**: React 기반 풀스택 프레임워크
- **TypeScript**: 타입 안정성
- **Tailwind CSS**: 유틸리티 우선 CSS 프레임워크
- **Zustand**: 경량 상태 관리 라이브러리
- **Radix UI**: 접근성 우선 UI 컴포넌트
- **Lucide React**: 아이콘 라이브러리
- **next-themes**: 다크 모드 지원
- **openapi-fetch**: OpenAPI 클라이언트

## 프로젝트 구조

```
frontend/
├── app/                    # Next.js App Router
│   ├── admin/             # Admin 페이지 (Admin Layout 사용)
│   │   ├── layout.tsx    # Admin Layout 적용
│   │   ├── page.tsx      # Admin 대시보드
│   │   ├── todos/        # Todo 관리 페이지
│   │   └── settings/     # 설정 페이지
│   ├── views/            # 화면 컴포넌트 (UI 로직)
│   │   ├── home-view.tsx
│   │   └── todos/
│   ├── layout.tsx        # 루트 레이아웃
│   └── page.tsx         # 홈 페이지 (Default Layout 사용)
│
├── services/             # 서비스 레이어 (비즈니스 로직)
│
├── components/           # 재사용 가능한 컴포넌트
│   ├── layout/          # 레이아웃 컴포넌트
│   │   ├── header.tsx   # 헤더 (다크모드 토글 포함)
│   │   ├── footer.tsx   # 푸터
│   │   ├── sidebar.tsx  # 사이드바
│   │   ├── default-layout.tsx  # 기본 레이아웃
│   │   └── admin-layout.tsx     # Admin 레이아웃
│   └── providers/       # Context Provider
│       └── theme-provider.tsx
│
├── lib/                  # 유틸리티 및 라이브러리
│   ├── api/             # API 클라이언트
│   │   ├── client.ts    # OpenAPI 클라이언트
│   │   └── types.ts     # API 타입 정의 (자동 생성)
│   └── utils.ts         # 유틸리티 함수
│
└── stores/               # Zustand 스토어
    └── todo-store.ts     # Todo 상태 관리
```

## 레이어 구조

```
View (app/views/) → Service (services/) → API Client (lib/api/) → Server
```

## 시작하기

### 1. 의존성 설치

```bash
cd frontend
npm install
```

### 2. 환경 변수 설정

`.env.example` 파일을 참고하여 환경별 설정 파일을 생성하세요:

```bash
# 로컬 개발 환경
cp .env.example .env.local

# 또는 직접 생성
echo "NEXT_PUBLIC_API_URL={{API_URL_LOCAL}}" > .env.local
```

환경별 설정:
- `.env.local` - 로컬 개발 환경
- `.env.dev` - 개발 서버 환경
- `.env.production` - 프로덕션 환경

자세한 내용은 [환경 변수 가이드](./ENVIRONMENT.md)를 참고하세요.

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 http://localhost:{{CLIENT_PORT}} 을 열어 확인하세요.

## 레이아웃

### Default Layout

기본 레이아웃은 헤더, 본문, 푸터로 구성됩니다.

```tsx
<DefaultLayout>
  {children}
</DefaultLayout>
```

### Admin Layout

Admin 레이아웃은 헤더, 왼쪽 사이드바, 오른쪽 본문으로 구성됩니다.

```tsx
<AdminLayout>
  {children}
</AdminLayout>
```

## 다크 모드

다크 모드는 `next-themes`를 사용하여 구현되었습니다. 헤더의 아이콘을 클릭하여 라이트/다크 모드를 전환할 수 있습니다.

## 상태 관리

Zustand를 사용하여 전역 상태를 관리합니다.

예시: `stores/todo-store.ts`

```tsx
import { useTodoStore } from "@/stores/todo-store";

function MyComponent() {
  const { todos, fetchTodos } = useTodoStore();

  useEffect(() => {
    fetchTodos();
  }, [fetchTodos]);

  return <div>{/* ... */}</div>;
}
```

## API 클라이언트

OpenAPI를 사용하여 서버 API를 호출합니다.

### 설정

`lib/api/client.ts`에서 API 클라이언트를 설정합니다.

```tsx
import { apiClient } from "@/lib/api/client";

const { data, error } = await apiClient.GET("/api/v1/sample/todos");
```

### Todo 샘플

`/admin/todos` 페이지에서 Todo CRUD 샘플을 확인할 수 있습니다.

- **GET** `/api/v1/sample/todos` - Todo 목록 조회
- **GET** `/api/v1/sample/todos/{todoNo}` - Todo 상세 조회
- **POST** `/api/v1/sample/todos` - Todo 생성
- **PUT** `/api/v1/sample/todos/{todoNo}` - Todo 수정
- **DELETE** `/api/v1/sample/todos/{todoNo}` - Todo 삭제

## 빌드 및 배포

### 빌드

```bash
npm run build
```

### 프로덕션 실행

```bash
npm start
```

## 문서

### 필수 문서
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Routing과 View 분리 (필독!)
- **[OPENAPI_GUIDE.md](./OPENAPI_GUIDE.md)** - OpenAPI 자동 타입 생성 (필독!)

### 참고 문서
- **시작하기**: 이 문서 (README.md)
- **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** - 프로젝트 구조
- **[ENVIRONMENT.md](./ENVIRONMENT.md)** - 환경 변수 설정
- **[COMMON_ISSUES.md](./COMMON_ISSUES.md)** - 문제 해결

### 전체 문서
- **[문서 인덱스](../INDEX.md)** - 모든 문서 목록

## 참고 자료

- [Next.js 공식 문서](https://nextjs.org/docs)
- [Zustand 공식 문서](https://zustand-demo.pmnd.rs/)
- [Radix UI 공식 문서](https://www.radix-ui.com/)
- [Tailwind CSS 공식 문서](https://tailwindcss.com/)
- [Lucide Icons](https://lucide.dev/)
