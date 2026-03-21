# Chat App 가이드

서버의 `{{CHAT_API_ENDPOINT}}` 엔드포인트를 사용하는 Chat 앱 예제입니다.

## 구조

### API 연동 (OpenAPI)

1. **타입 정의**: `lib/api/types.ts`
   - OpenAPI 스펙 기반 타입 정의
   - 서버 API 엔드포인트와 일치하는 타입

2. **API 클라이언트**: `lib/api/client.ts`
   - `openapi-fetch` 사용
   - 타입 안전한 API 호출

3. **환경 설정**: `lib/config/env.ts`
   - API URL 설정: `{{API_URL_LOCAL}}`

### 상태 관리 (Zustand)

`stores/chat-store.ts`에서 Chat 상태 관리:

```typescript
interface ChatState {
  chats: Chat[];
  loading: boolean;
  error: string | null;
  fetchChats: () => Promise<void>;
  createChat: (data) => Promise<void>;
  updateChat: (chatNo, data) => Promise<void>;
  deleteChat: (chatNo) => Promise<void>;
}
```

### 화면 구성

1. **Chat 관리 페이지**: Chat 목록 조회, 필터링, 통계
2. **Chat 목록 컴포넌트**: 항목 표시, 수정/삭제
3. **Chat 폼 다이얼로그**: 추가/수정 모달

## 주요 기능

### Chat CRUD

```typescript
// 목록 조회
await fetchChats();

// 생성
await createChat({ title: "제목", description: "설명" });

// 수정
await updateChat(1, { title: "수정", completed: "Y" });

// 삭제
await deleteChat(1);
```

## 사용 방법

### 1. 서버 실행

```bash
cd backend/App/{{DOMAIN_NAME}}
uv run python main.py
```

서버가 `{{API_URL_LOCAL}}`에서 실행됩니다.

### 2. 클라이언트 실행

```bash
cd frontend
npm run dev
```

클라이언트가 `http://localhost:{{CLIENT_PORT}}`에서 실행됩니다.

## 확장 가이드

### 새 API 엔드포인트 추가

1. **타입 생성**: `pnpm run openapi:regen`
2. **API 클라이언트에 함수 추가**: `lib/api/client.ts`
3. **Service 생성**: `services/your_service.ts`
4. **View에서 호출**: `app/views/your-page/your-view.tsx`

## 문제 해결

### CORS 에러

서버에서 CORS 설정 확인:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:{{CLIENT_PORT}}"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API 연결 실패

1. 서버가 실행 중인지 확인
2. 환경 변수 확인 (`.env.local`)
3. 네트워크 콘솔에서 요청/응답 확인

## 참고 자료

- [클라이언트 아키텍처](../client/ARCHITECTURE.md)
- [OpenAPI 가이드](../client/OPENAPI_GUIDE.md)
- [환경 변수](../client/ENVIRONMENT.md)
