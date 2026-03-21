# API Server

{{TECH_STACK_BACKEND}} 기반 웹 서비스 서버입니다.

## 시작하기

### 1. 의존성 설치

```bash
# backend 디렉토리에서 실행
cd backend
uv sync
```

### 2. 서버 실행

```bash
# 애플리케이션 실행
cd App/{{DOMAIN_NAME}}
uv run python main.py
```

### 3. API 문서 확인

- Swagger UI: {{API_URL_LOCAL}}/docs
- ReDoc: {{API_URL_LOCAL}}/redoc

## 프로젝트 구조

```
backend/
├── App/              # 애플리케이션 진입점
│   └── {domain}/     # 도메인별 애플리케이션
│       ├── main.py
│       ├── config/
│       └── controller/
│
└── Core/             # 핵심 비즈니스 로직
    ├── framework/    # 프레임워크 기반 클래스
    └── domains/      # 도메인별 비즈니스 로직
        └── {domain}/
            ├── model/
            ├── dto/
            ├── repository/
            ├── service/
            └── process/
```

## 주요 파일

- `pyproject.toml`: 프로젝트 설정 및 의존성
- `requirements.txt`: Python 패키지 목록 (레거시)
- `pyrightconfig.json`: Python 타입 체크 설정

## 문서 가이드

- **시작하기**: 이 문서 (README.md)
- **환경 변수 설정**: [ENVIRONMENT.md](./ENVIRONMENT.md)
- **프로젝트 구조**: [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)
- **전체 문서 인덱스**: [docs/INDEX.md](../INDEX.md)

## 프로젝트 루트

- 전체 프로젝트 가이드: 프로젝트 루트의 `README.md` 참고
