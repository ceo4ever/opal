# OpenAPI 자동 생성 가이드

서버의 OpenAPI 스펙에서 자동으로 TypeScript 타입을 생성하는 방법입니다.

## 개요

이 프로젝트는 **FastAPI 서버의 OpenAPI 스펙**을 기반으로 클라이언트의 **TypeScript 타입을 자동 생성**합니다.

### 사용 도구

- **openapi-typescript**: OpenAPI 스펙을 TypeScript 타입으로 변환
- **openapi-fetch**: 타입 안전한 fetch 클라이언트

## NPM 스크립트

### 1. openapi:pull

서버에서 OpenAPI JSON 스펙을 가져옵니다.

```bash
npm run openapi:pull
```

**동작**:
- `{{API_URL_LOCAL}}/openapi.json`에서 OpenAPI 스펙 다운로드
- 프로젝트 루트에 `openapi.json` 파일 생성

**전제 조건**:
- 서버가 `{{API_URL_LOCAL}}`에서 실행 중이어야 함

### 2. openapi:gen

OpenAPI JSON에서 TypeScript 타입을 생성합니다.

```bash
npm run openapi:gen
```

**동작**:
- `openapi.json` 파일을 읽어서 TypeScript 타입 생성
- `lib/api/types.ts` 파일 생성

### 3. openapi:clean

생성된 파일을 삭제합니다.

```bash
npm run openapi:clean
```

**동작**:
- `openapi.json` 삭제
- `lib/api/types.ts` 삭제

### 4. openapi:regen

전체 프로세스를 한 번에 실행합니다 (권장).

```bash
npm run openapi:regen
```

**동작**:
1. 서버에서 OpenAPI 스펙 다운로드 (`openapi:pull`)
2. TypeScript 타입 생성 (`openapi:gen`)

## 사용 방법

### 1. 서버 실행

먼저 백엔드 서버를 실행합니다:

```bash
cd backend/App/{{DOMAIN_NAME}}
uv run python main.py
```

서버가 `{{API_URL_LOCAL}}`에서 실행되어야 합니다.

### 2. OpenAPI 스펙 확인

브라우저에서 OpenAPI 문서를 확인할 수 있습니다:
- **Swagger UI**: {{API_URL_LOCAL}}/docs
- **OpenAPI JSON**: {{API_URL_LOCAL}}/openapi.json

### 3. 타입 생성

```bash
cd frontend
npm run openapi:regen
```

### 4. 생성된 타입 사용

```typescript
import createClient from "openapi-fetch";
import type { paths } from "./types";

const client = createClient<paths>({
  baseUrl: "{{API_URL_LOCAL}}",
});

// 타입 안전한 API 호출
const { data, error } = await client.GET("/api/v1/sample/todos");
```

## 워크플로우

### 서버 API 변경 시

1. **서버에서 API 엔드포인트 수정**
   ```python
   # backend/App/{domain}/controller/SampleController.py
   @router.post(f"{basePath}/new-endpoint")
   async def newEndpoint(self, ...):
       ...
   ```

2. **서버 재시작**
   ```bash
   cd backend/App/{{DOMAIN_NAME}}
   uv run python main.py
   ```

3. **클라이언트 타입 재생성**
   ```bash
   cd frontend
   npm run openapi:regen
   ```

4. **서비스 레이어에서 사용**
   ```typescript
   // services/your_service.ts
   import { apiClient } from "@/lib/api/client";

   export async function yourServiceFunction() {
       const { data } = await apiClient.POST("/api/v1/sample/todos/new-endpoint", {
           body: { ... }
       });
       return data;
   }
   ```

5. **View에서 서비스 호출**
   ```typescript
   import { yourServiceFunction } from "@/services/your_service";

   const result = await yourServiceFunction();
   ```

### 자동화 (선택사항)

개발 중 자동으로 타입을 생성하려면:

```bash
# 서버 변경 감지 시 자동으로 타입 재생성
npm run dev & watch -n 60 'npm run openapi:regen'
```

또는 `nodemon`을 사용:

```bash
npm install -D nodemon
```

`nodemon.json`:
```json
{
  "watch": ["../backend/App"],
  "ext": "py",
  "exec": "npm run openapi:regen"
}
```

## 파일 구조

```
frontend/
├── openapi.json              # 서버에서 가져온 OpenAPI 스펙 (gitignore)
├── lib/
│   └── api/
│       ├── types.ts          # 자동 생성된 TypeScript 타입 (gitignore)
│       └── client.ts         # API 클라이언트 설정
├── services/                 # 서비스 레이어 (비즈니스 로직)
└── package.json              # OpenAPI 스크립트 정의
```

## 타입 예시

생성된 `lib/api/types.ts`:

```typescript
export interface paths {
  "/api/v1/sample/todos": {
    get: {
      parameters: {
        query?: {
          memberNo?: number;
          completed?: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": {
              status: number;
              messageCode: string;
              message: string;
              data: Todo[];
            };
          };
        };
      };
    };
    post: {
      requestBody: {
        content: {
          "application/x-www-form-urlencoded": {
            title: string;
            description?: string;
          };
        };
      };
      responses: {
        200: {
          content: {
            "application/json": {
              status: number;
              data: Todo;
            };
          };
        };
      };
    };
  };
}

export interface components {
  schemas: {
    Todo: {
      todoNo: number;
      title: string;
      description?: string;
      completed: string;
      createDt: string;
    };
  };
}
```

## API 클라이언트 사용

### GET 요청

```typescript
const { data, error } = await apiClient.GET("/api/v1/sample/todos", {
  params: {
    query: {
      completed: "N",
    },
  },
});

if (error) {
  console.error("Error:", error);
} else {
  console.log("Todos:", data.data);
}
```

### POST 요청

```typescript
const formData = new URLSearchParams();
formData.append("title", "New Todo");
formData.append("description", "Description");

const { data, error } = await apiClient.POST("/api/v1/sample/todos", {
  body: formData,
  headers: {
    "Content-Type": "application/x-www-form-urlencoded",
  },
});
```

### PUT 요청

```typescript
const { data, error } = await apiClient.PUT("/api/v1/sample/todos/{todoNo}", {
  params: {
    path: { todoNo: 1 },
  },
  body: formData,
});
```

### DELETE 요청

```typescript
const { data, error } = await apiClient.DELETE("/api/v1/sample/todos/{todoNo}", {
  params: {
    path: { todoNo: 1 },
  },
});
```

## 문제 해결

### 1. 서버 연결 실패

**에러**: `curl: (7) Failed to connect to server port {{SERVER_PORT}}`

**해결**:
```bash
# 서버가 실행 중인지 확인
cd backend/App/{{DOMAIN_NAME}}
uv run python main.py
```

### 2. OpenAPI 스펙이 없음

**에러**: `404 Not Found`

**해결**:
- FastAPI 앱이 OpenAPI를 제공하는지 확인
- 브라우저에서 `{{API_URL_LOCAL}}/docs` 접속 가능한지 확인

### 3. 타입 생성 실패

**에러**: `Error parsing openapi.json`

**해결**:
```bash
# openapi.json이 유효한 JSON인지 확인
cat openapi.json | jq .

# 재생성
npm run openapi:regen
```

### 4. 타입이 업데이트되지 않음

**해결**:
```bash
# 캐시 삭제 후 재생성
npm run openapi:clean
npm run openapi:regen

# 개발 서버 재시작
npm run dev
```

## Best Practices

### 1. 정기적인 타입 업데이트

서버 API가 변경될 때마다 타입을 업데이트하세요:

```bash
npm run openapi:regen
```

### 2. Git에 커밋하지 않기

`openapi.json`과 `lib/api/types.ts`는 자동 생성 파일이므로 `.gitignore`에 포함:

```gitignore
# OpenAPI
/openapi.json
/lib/api/types.ts
```

### 3. CI/CD 파이프라인

빌드 시 자동으로 타입 생성:

```yaml
# .github/workflows/build.yml
- name: Generate OpenAPI types
  run: |
    npm run openapi:pull
    npm run openapi:gen
```

### 4. 타입 검증

TypeScript 컴파일러로 타입 에러 확인:

```bash
npm run build
```

## 참고 자료

- [openapi-typescript 공식 문서](https://openapi-ts.dev/)
- [openapi-fetch 공식 문서](https://openapi-ts.dev/openapi-fetch/)
- [FastAPI OpenAPI 문서](https://fastapi.tiangolo.com/advanced/extending-openapi/)

## 요약

```bash
# 1. 서버 실행
cd backend/App/{{DOMAIN_NAME}} && uv run python main.py

# 2. 타입 생성 (새 터미널)
cd frontend && npm run openapi:regen

# 3. 클라이언트 개발
npm run dev
```

이제 서버 API와 클라이언트가 항상 동기화된 타입으로 개발할 수 있습니다.
