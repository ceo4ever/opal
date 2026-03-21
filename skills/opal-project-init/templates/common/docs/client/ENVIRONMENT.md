# 환경 변수 설정 가이드

클라이언트 프로젝트는 환경별로 다른 설정을 사용할 수 있습니다.

## 환경 변수 파일

프로젝트 루트(`frontend/`)에 다음 환경 변수 파일을 생성할 수 있습니다:

- `.env.local` - 로컬 개발 환경 (Git에 커밋되지 않음)
- `.env.dev` - 개발 서버 환경 (Git에 커밋되지 않음)
- `.env.production` - 프로덕션 환경 (Git에 커밋되지 않음)
- `.env.example` - 환경 변수 템플릿 (Git에 커밋됨)

## 환경 변수 우선순위

Next.js는 다음 순서로 환경 변수를 로드합니다:

1. `.env.production.local` (프로덕션 빌드 시)
2. `.env.local` (모든 환경, `.gitignore`에 포함)
3. `.env.production`, `.env.development`, `.env` (환경별)
4. `.env.example` (템플릿 파일)

## 사용 가능한 환경 변수

### NEXT_PUBLIC_API_URL

API 서버의 기본 URL입니다.

```env
NEXT_PUBLIC_API_URL={{API_URL_LOCAL}}
```

**주의**: 클라이언트에서 사용할 환경 변수는 반드시 `NEXT_PUBLIC_` 접두사가 필요합니다.

### NEXT_PUBLIC_ENV

현재 환경을 지정합니다. (`local`, `dev`, `production`)

```env
NEXT_PUBLIC_ENV=local
```

### NEXT_PUBLIC_DEBUG

디버그 모드를 활성화/비활성화합니다.

```env
NEXT_PUBLIC_DEBUG=true
```

## 환경별 설정 예시

### 로컬 개발 환경 (`.env.local`)

```env
NEXT_PUBLIC_API_URL={{API_URL_LOCAL}}
NEXT_PUBLIC_ENV=local
NEXT_PUBLIC_DEBUG=true
```

### 개발 서버 환경 (`.env.dev`)

```env
NEXT_PUBLIC_API_URL=https://api-dev.example.com
NEXT_PUBLIC_ENV=dev
NEXT_PUBLIC_DEBUG=true
```

### 프로덕션 환경 (`.env.production`)

```env
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_ENV=production
NEXT_PUBLIC_DEBUG=false
```

## 환경 변수 사용 방법

### 코드에서 사용

```tsx
// 직접 사용
const apiUrl = process.env.NEXT_PUBLIC_API_URL;

// env 설정 파일 사용 (권장)
import { env } from "@/lib/config/env";

const apiUrl = env.apiUrl;
const isDebug = env.debug;
```

### 빌드 시 환경 변수 설정

```bash
# 프로덕션 빌드
NEXT_PUBLIC_API_URL=https://api.example.com npm run build

# 개발 서버 빌드
NEXT_PUBLIC_API_URL=https://api-dev.example.com npm run build
```

## 환경 변수 설정 파일

`lib/config/env.ts`에서 환경 변수를 중앙 관리합니다:

```tsx
import { env } from "@/lib/config/env";

// API URL 사용
const response = await fetch(`${env.apiUrl}/api/v1/sample/todos`);

// 환경 확인
if (env.isDevelopment) {
  console.log("개발 모드");
}

// 디버그 모드 확인
if (env.debug) {
  console.log("디버그 정보:", data);
}
```

## 주의사항

1. **NEXT_PUBLIC_ 접두사**: 클라이언트에서 사용할 환경 변수는 반드시 `NEXT_PUBLIC_` 접두사가 필요합니다.
2. **보안**: 민감한 정보(API 키, 비밀번호 등)는 환경 변수에 저장하지 마세요. 서버 사이드에서만 사용 가능한 환경 변수를 사용하세요.
3. **Git 커밋**: `.env.local`, `.env.dev`, `.env.production` 파일은 Git에 커밋되지 않습니다. `.env.example`만 커밋하여 템플릿으로 사용하세요.
4. **빌드 시점**: 환경 변수는 빌드 시점에 번들에 포함되므로, 빌드 후 변경해도 반영되지 않습니다.

## 배포 시 환경 변수 설정

### Vercel

Vercel 대시보드에서 환경 변수를 설정할 수 있습니다:

1. 프로젝트 설정 → Environment Variables
2. 환경별로 변수 추가
3. 재배포

### 기타 플랫폼

각 플랫폼의 환경 변수 설정 방법을 따라 설정하세요.

## 문제 해결

### 환경 변수가 적용되지 않는 경우

1. 변수명에 `NEXT_PUBLIC_` 접두사가 있는지 확인
2. 개발 서버를 재시작 (`npm run dev`)
3. 빌드 캐시 삭제 후 재빌드 (`rm -rf .next && npm run build`)

### 환경 변수 타입 에러

TypeScript에서 환경 변수를 사용할 때 타입 에러가 발생할 수 있습니다. `lib/config/env.ts`에서 타입을 명시적으로 정의하여 사용하세요.
