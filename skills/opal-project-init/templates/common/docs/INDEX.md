# 문서 인덱스

> 이 프로젝트의 모든 문서를 한눈에 확인할 수 있습니다.

---

## 시작하기

| 문서 | 설명 | 대상 |
|------|------|------|
| **[QUICK_START.md](../QUICK_START.md)** | 빠른 시작 가이드 (5분 안에 실행) | 모든 개발자 |
| **[README.md](../README.md)** | 프로젝트 전체 가이드 | 모든 개발자 |

---

## 서버 문서 (backend/)

### 필수 문서

| 문서 | 설명 | 우선순위 |
|------|------|---------|
| **[ENVIRONMENT.md](./server/ENVIRONMENT.md)** | 환경 변수 관리 (.env 파일) | 높음 |
| **[PROJECT_STRUCTURE.md](./server/PROJECT_STRUCTURE.md)** | 서버 프로젝트 구조 | 중간 |
| **[README.md](./server/README.md)** | 서버 시작 가이드 | 중간 |

### 개발 워크플로우

```
새 서비스 개발 시:
1. PROJECT_STRUCTURE.md 읽기
2. 새 도메인 디렉토리 생성 (App/{domain}/, Core/domains/{domain}/)
3. 구조에 맞게 Model → DTO → Repository → Service → Controller 순서로 생성
```

---

## 클라이언트 문서 (frontend/)

### 필수 문서

| 문서 | 설명 | 우선순위 |
|------|------|---------|
| **[ARCHITECTURE.md](./client/ARCHITECTURE.md)** | Routing/View 분리 원칙 | 높음 |
| **[OPENAPI_GUIDE.md](./client/OPENAPI_GUIDE.md)** | OpenAPI 자동 타입 생성 | 높음 |
| **[PROJECT_STRUCTURE.md](./client/PROJECT_STRUCTURE.md)** | 클라이언트 프로젝트 구조 | 중간 |
| **[ENVIRONMENT.md](./client/ENVIRONMENT.md)** | 환경 변수 설정 | 중간 |
| **[COMMON_ISSUES.md](./client/COMMON_ISSUES.md)** | 문제 해결 가이드 | 낮음 |
| **[README.md](./client/README.md)** | 클라이언트 시작 가이드 | 중간 |

### 개발 워크플로우

```
새 화면 개발 시:
1. ARCHITECTURE.md 읽기 (Routing/View 분리 원칙)
2. app/{path}/page.tsx 생성 (Routing)
3. app/views/{name}/{name}-view.tsx 생성 (View)
4. npm run openapi:regen (타입 생성)
```

---

## 상황별 문서 찾기

### 처음 프로젝트를 체크아웃한 경우
1. [QUICK_START.md](../QUICK_START.md) - 빠른 시작
2. [README.md](../README.md) - 프로젝트 전체 개요

### 새 서비스를 만들고 싶은 경우
1. [PROJECT_STRUCTURE.md](./server/PROJECT_STRUCTURE.md) - 서버 구조
2. [ENVIRONMENT.md](./server/ENVIRONMENT.md) - 환경 설정

### 클라이언트 화면을 추가하는 경우
1. [ARCHITECTURE.md](./client/ARCHITECTURE.md) - Routing/View 분리
2. [OPENAPI_GUIDE.md](./client/OPENAPI_GUIDE.md) - 타입 생성

### 환경 설정이 필요한 경우
1. [ENVIRONMENT.md](./server/ENVIRONMENT.md) - 서버 환경 변수
2. [ENVIRONMENT.md](./client/ENVIRONMENT.md) - 클라이언트 환경 변수

### 문제가 발생한 경우
1. [COMMON_ISSUES.md](./client/COMMON_ISSUES.md) - 문제 해결

---

## 문서 디렉토리 구조

```
{{PROJECT_NAME}}/
├── QUICK_START.md              # 빠른 시작 가이드 (진입점)
├── README.md                   # 프로젝트 전체 가이드
├── CHANGELOG.md                # 변경 이력
│
├── backend/
│   ├── README.md               # 서버 README
│   └── CLAUDE.md               # 서버 AI 가이드
│
├── frontend/
│   └── README.md               # 클라이언트 README
│
└── docs/
    ├── INDEX.md                # 이 문서
    │
    ├── server/                 # 서버 문서
    │   ├── README.md
    │   ├── PROJECT_STRUCTURE.md
    │   ├── ENVIRONMENT.md
    │   └── UV_SETUP.md
    │
    └── client/                 # 클라이언트 문서
        ├── README.md
        ├── ARCHITECTURE.md
        ├── OPENAPI_GUIDE.md
        ├── PROJECT_STRUCTURE.md
        ├── ENVIRONMENT.md
        └── COMMON_ISSUES.md
```

---

## 팁

### 문서 읽기 순서
1. **[README.md](../README.md)** - 프로젝트 전체 개요
2. **[QUICK_START.md](../QUICK_START.md)** - 실행 방법
3. 해당 워크스페이스 문서 - 서버 또는 클라이언트

### 자주 참조하는 문서
- **새 화면 만들기**: [ARCHITECTURE.md](./client/ARCHITECTURE.md)
- **타입 생성**: [OPENAPI_GUIDE.md](./client/OPENAPI_GUIDE.md)
- **환경 설정**: [ENVIRONMENT.md](./server/ENVIRONMENT.md)

---

이 인덱스를 북마크하여 필요한 문서를 빠르게 찾으세요!
