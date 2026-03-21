# {{DOMAIN_NAME}} 도메인 아키텍처 가이드

{{PROJECT_NAME}} 프로젝트의 {{DOMAIN_NAME}} 도메인 아키텍처와 구조를 설명합니다.

## 목차

1. [도메인 개요](#도메인-개요)
2. [계층 구조](#계층-구조)
3. [디렉토리 구조](#디렉토리-구조)
4. [데이터 흐름](#데이터-흐름)
5. [확장 가이드](#확장-가이드)

---

## 도메인 개요

### {{DOMAIN_NAME}} 도메인

- **도메인 코드**: `{{DOMAIN_NAME}}`
- **아키텍처**: Controller → Service → Repository 계층형

---

## 계층 구조

### Controller → Service → Repository 패턴

```
사용자 요청
    ↓
Controller (요청 검증, 응답 생성)
    ↓
Service (비즈니스 로직)
    ↓
Repository (데이터 접근)
    ↓
Database
```

### 각 계층의 역할

1. **Controller**: REST API 엔드포인트 정의, 요청/응답 처리
2. **Service**: 비즈니스 로직 구현, 트랜잭션 관리
3. **Repository**: 데이터베이스 CRUD, 쿼리 실행
4. **Model**: SQLAlchemy 엔티티 정의
5. **DTO**: Pydantic 모델 (요청/응답 스키마)

---

## 디렉토리 구조

```
backend/
├── App/{{DOMAIN_NAME}}/                # 애플리케이션 계층
│   ├── main.py                        # FastAPI 앱 초기화
│   ├── config/                        # 환경 설정
│   └── controller/                    # API 컨트롤러
│       ├── SampleController.py
│       └── ...
│
└── Core/domains/{{DOMAIN_NAME}}/       # 비즈니스 로직
    ├── model/                          # DB 엔티티
    ├── dto/                            # 데이터 전송 객체
    ├── repository/                     # 데이터 접근 계층
    └── service/                        # 비즈니스 로직
```

### 계층별 역할

#### App/{{DOMAIN_NAME}} (애플리케이션 계층)
- **main.py**: FastAPI 앱 초기화, CORS 설정, 라우터 등록
- **config/**: 환경 변수, 보안 설정
- **controller/**: REST API 엔드포인트

#### Core/domains/{{DOMAIN_NAME}} (비즈니스 로직)
- **model/**: SQLAlchemy 엔티티
- **dto/**: Pydantic 모델 (요청/응답)
- **repository/**: 데이터베이스 CRUD
- **service/**: 비즈니스 로직

---

## 데이터 흐름

### 사용자 요청 → 응답

```
Client Request
    ↓
Controller (요청 검증)
    ↓
Service (비즈니스 로직)
    ↓
Repository (데이터 접근)
    ↓
Database
    ↓
Repository (결과 반환)
    ↓
Service (비즈니스 로직 처리)
    ↓
Controller (응답 생성)
    ↓
Client Response
```

---

## 데이터베이스 스키마

### 주요 테이블

- **{{DOMAIN_NAME}}_***: {{DOMAIN_NAME}} 도메인 테이블 (접두사 규칙)

### 네이밍 규칙

- 테이블명: `{도메인}_{엔티티}` (snake_case)
- 컬럼명: camelCase
- PK: `{엔티티}No` (예: `memberNo`, `todoNo`)

---

## 확장 가이드

### 새 기능 추가 순서

1. **Model 생성**: `Core/domains/{{DOMAIN_NAME}}/model/`에 SQLAlchemy 엔티티
2. **DTO 생성**: `Core/domains/{{DOMAIN_NAME}}/dto/`에 요청/응답 Pydantic 모델
3. **Repository 생성**: `Core/domains/{{DOMAIN_NAME}}/repository/`에 데이터 접근 로직
4. **Service 생성**: `Core/domains/{{DOMAIN_NAME}}/service/`에 비즈니스 로직
5. **Controller 생성**: `App/{{DOMAIN_NAME}}/controller/`에 API 엔드포인트
6. **main.py에 라우터 등록**

자세한 내용: [HOW_TO_REQUEST_NEW_DOMAIN.md](./HOW_TO_REQUEST_NEW_DOMAIN.md)

---

## 참고 문서

- [새 도메인 추가 가이드](./HOW_TO_REQUEST_NEW_DOMAIN.md)
- [프로젝트 구조](./PROJECT_STRUCTURE.md)
- [환경 변수](./ENVIRONMENT.md)
