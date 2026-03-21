# 클라이언트 일반적인 문제 해결

클라이언트 개발 중 자주 발생하는 문제와 해결 방법입니다.

## UI/스타일 문제

### 1. 라이트 모드가 어둡게 표시됨

**증상**: 라이트 모드인데 배경이 어둡게 표시됨

**원인**: Tailwind V4에서 `oklch()` 색상 공간 사용 시 색상 값 해석 오류

**해결**:
```css
/* globals.css */

/* Bad */
--color-background: oklch(var(--background));

/* Good */
--color-background: hsl(var(--background));
```

### 2. 모달 배경이 투명하여 뒤 내용과 겹침

**증상**: 모달을 열었을 때 배경이 투명하여 뒤 내용이 보임

**원인**: Tailwind V4에서 `bg-background` 클래스가 제대로 적용되지 않음

**해결**:
```tsx
/* Bad */
<div className="bg-background">

/* Good */
<div style={{ backgroundColor: 'hsl(var(--background))' }}>
```

완전한 예시:
```tsx
<div
  className="fixed inset-0 z-50 flex items-center justify-center p-4"
  style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
  onClick={onClose}
>
  <div
    className="w-full max-w-md rounded-lg border p-6"
    style={{
      backgroundColor: 'hsl(var(--background))',
      borderColor: 'hsl(var(--border))'
    }}
    onClick={(e) => e.stopPropagation()}
  >
    {/* 모달 내용 */}
  </div>
</div>
```

### 3. 입력 필드 배경이 투명함

**증상**: 다크 모드에서 입력 필드 배경이 투명하여 보이지 않음

**해결**:
```tsx
<input
  className="w-full rounded-md border px-3 py-2"
  style={{
    backgroundColor: 'hsl(var(--background))',
    borderColor: 'hsl(var(--border))',
    color: 'hsl(var(--foreground))'
  }}
/>
```

### 4. 다크 모드가 작동하지 않음

**증상**: 테마 토글 버튼을 눌러도 다크 모드가 적용되지 않음

**해결 1**: ThemeProvider 확인
```tsx
// app/layout.tsx
import { ThemeProvider } from "@/components/providers/theme-provider";

<ThemeProvider
  attribute="class"
  defaultTheme="system"
  enableSystem
  disableTransitionOnChange
>
  {children}
</ThemeProvider>
```

**해결 2**: tailwind.config.ts 확인
```typescript
// Tailwind V4에서는 config 파일이 필요 없음!
// tailwind.config.ts 파일이 있다면 삭제하세요.
```

**해결 3**: globals.css 확인
```css
/* :root와 .dark 클래스 확인 */
.dark {
  --background: 0 0% 3.9%;
  --foreground: 0 0% 98%;
}
```

## API 연동 문제

### 1. CORS 에러

**증상**:
```
Access to fetch at '{{API_URL_LOCAL}}/api/...' from origin 'http://localhost:{{CLIENT_PORT}}' has been blocked by CORS policy
```

**해결**: 서버의 CORS 설정 확인
```python
# backend/App/{domain}/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:{{CLIENT_PORT}}",
        "http://127.0.0.1:{{CLIENT_PORT}}"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
```

### 2. 서버 연결 실패 (Failed to fetch)

**증상**: `Failed to fetch` 에러

**해결**:
1. 서버가 실행 중인지 확인:
   ```bash
   curl {{API_URL_LOCAL}}/docs
   ```

2. 환경 변수 확인:
   ```bash
   cat frontend/.env.local
   # NEXT_PUBLIC_API_URL={{API_URL_LOCAL}}
   ```

3. 개발 서버 재시작:
   ```bash
   cd frontend
   npm run dev
   ```

### 3. OpenAPI 타입 에러

**증상**: TypeScript 타입 에러 발생

**해결**:
```bash
# 1. 서버가 실행 중인지 확인
cd backend/App/{{DOMAIN_NAME}} && uv run python main.py

# 2. 타입 재생성
cd frontend
npm run openapi:regen

# 3. 개발 서버 재시작
npm run dev
```

### 4. 타입이 업데이트되지 않음

**증상**: 서버 API를 변경했는데 클라이언트 타입이 업데이트되지 않음

**해결**:
```bash
# 캐시 삭제 후 재생성
cd frontend
npm run openapi:clean
npm run openapi:regen

# .next 캐시 삭제
rm -rf .next

# 개발 서버 재시작
npm run dev
```

## 빌드 및 배포 문제

### 1. 빌드 실패

**증상**: `npm run build` 실패

**해결**:
```bash
# 1. 타입 에러 확인
npm run build 2>&1 | grep error

# 2. OpenAPI 타입 재생성
npm run openapi:regen

# 3. 의존성 재설치
rm -rf node_modules package-lock.json
npm install

# 4. 재빌드
npm run build
```

### 2. 환경 변수가 빌드에 포함되지 않음

**증상**: `process.env.NEXT_PUBLIC_*`가 undefined

**원인**: 빌드 시점에 환경 변수가 번들에 포함됨

**해결**:
```bash
# 빌드 시 환경 변수 설정
NEXT_PUBLIC_API_URL=https://api.example.com npm run build

# 또는 .env.production 파일 사용
npm run build
```

## 의존성 문제

### 1. npm install 실패

**해결**:
```bash
# Node.js 버전 확인
node --version  # v18 이상 권장

# 캐시 삭제
npm cache clean --force

# 재설치
rm -rf node_modules package-lock.json
npm install
```

### 2. openapi-typescript 설치 에러

**해결**:
```bash
npm install -D openapi-typescript
```

## 런타임 에러

### 1. Hydration 에러

**증상**: `Hydration failed because the initial UI does not match what was rendered on the server`

**원인**: 서버/클라이언트 렌더링 불일치

**해결**:
1. `"use client"` 디렉티브 추가 (동적 컴포넌트)
2. `useEffect`에서 클라이언트 전용 로직 실행
3. `suppressHydrationWarning` 속성 추가 (필요 시)

```tsx
// 해결 예시
"use client";

export function MyComponent() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return <div>...</div>;
}
```

### 2. localStorage/sessionStorage 에러

**증상**: `localStorage is not defined`

**원인**: SSR에서 localStorage 접근 불가

**해결**:
```tsx
// Bad
const value = localStorage.getItem("key");

// Good
useEffect(() => {
  const value = localStorage.getItem("key");
}, []);
```

## Zustand 관련 문제

### 1. Store가 업데이트되지 않음

**증상**: API 호출 후 화면이 업데이트되지 않음

**해결**:
```typescript
// Store에서 set() 호출 확인
export const useTodoStore = create((set) => ({
  todos: [],
  fetchTodos: async () => {
    const response = await apiClient.GET("/api/v1/sample/todos");
    set({ todos: response.data?.data || [] }); // set() 호출 필수
  },
}));
```

### 2. useEffect 무한 루프

**증상**: 화면이 계속 리렌더링됨

**원인**: fetchTodos가 의존성 배열에 있지만 매번 새로 생성됨

**해결**:
```tsx
// Bad
useEffect(() => {
  fetchTodos();
}, [fetchTodos]);  // fetchTodos는 매번 새 함수

// Good
useEffect(() => {
  fetchTodos();
}, []); // 빈 배열 - 마운트 시 한 번만

// 또는 useCallback 사용
const handleFetch = useCallback(() => {
  fetchTodos();
}, [fetchTodos]);
```

## 추가 리소스

- [Next.js 공식 문서](https://nextjs.org/docs)
- [Tailwind CSS 문서](https://tailwindcss.com/docs)
- [Zustand 문서](https://zustand-demo.pmnd.rs/)
- [OpenAPI-Fetch 문서](https://openapi-ts.dev/openapi-fetch/)
- [Radix UI 문서](https://www.radix-ui.com/)

문제가 해결되지 않으면 GitHub Issues에 문의하세요.
