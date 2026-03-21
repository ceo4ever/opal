# SQLite 로컬 개발 환경 설정 가이드

## 개요

이 프로젝트는 **IS_LOCAL_DB** 환경 변수를 통해 {{DB_TYPE}}과 SQLite 데이터베이스를 선택할 수 있습니다.

- `IS_LOCAL_DB=True`: **SQLite** 사용 (로컬 개발용, DB 서버 불필요)
- `IS_LOCAL_DB=False`: **{{DB_TYPE}}** 사용 (기본값, 서버 환경)

## 장점

### SQLite 모드 (`IS_LOCAL_DB=True`)
- DB 서버 불필요: 별도 설치 없이 바로 개발 가능
- 빠른 시작: 데이터베이스 설정 없이 즉시 실행
- 자동 테이블 생성: 서버 시작 시 자동으로 테이블 생성
- 파일 기반: `.db` 파일로 데이터 관리

### {{DB_TYPE}} 모드 (`IS_LOCAL_DB=False`)
- 운영 환경과 동일
- 고성능: 대용량 데이터 처리에 적합
- 트랜잭션 격리: 고급 기능 사용 가능

## 환경 변수 설정

### .env 파일 사용 (권장)

```bash
cd backend
cp .env.example .env.local

# .env.local 파일에서 수정
# IS_LOCAL_DB=True
# PROFILES_ACTIVE=local
```

### 명령줄에서 직접 설정

```bash
# SQLite 모드 (로컬 개발)
export IS_LOCAL_DB=True
export PROFILES_ACTIVE=local

# {{DB_TYPE}} 모드 (기본)
export IS_LOCAL_DB=False
export PROFILES_ACTIVE=local
```

## SQLite 모드 실행하기

### 1. 환경 변수 설정

```bash
export IS_LOCAL_DB=True
export PROFILES_ACTIVE=local
```

### 2. 서버 실행

```bash
cd backend/App/{{DOMAIN_NAME}}
uv run python main.py
```

### 3. 서버 시작 시 로그 확인

```
INFO:     Using SQLite database: sqlite+aiosqlite:///{{SQLITE_DB_PATH}}
INFO:     Creating tables for SQLite...
INFO:     Tables created successfully for SQLite
```

### 4. 데이터베이스 파일 확인

```bash
ls -lh {{SQLITE_DB_PATH}}
```

## SQLite 데이터베이스 관리

### SQLite CLI로 데이터 확인

```bash
sqlite3 {{SQLITE_DB_PATH}}

# 테이블 목록 확인
.tables

# 데이터 조회
SELECT * FROM {{DOMAIN_NAME}}_sample;

# 종료
.quit
```

### 데이터베이스 초기화

```bash
rm {{SQLITE_DB_PATH}}
# 서버 재시작 시 자동으로 테이블 재생성
```

## 주의사항

### SQLite 제한 사항

1. **동시성**: 동시 쓰기 작업이 제한적 (개발/테스트 용도)
2. **데이터 타입**: {{DB_TYPE}}과 일부 타입이 다를 수 있음
3. **파일 기반**: `.gitignore`에 `*.db` 추가 권장

### {{DB_TYPE}}로 전환하기

```bash
export IS_LOCAL_DB=False
cd backend/App/{{DOMAIN_NAME}}
uv run python main.py
```

## 요약

| 항목 | SQLite 모드 | {{DB_TYPE}} 모드 |
|------|------------|-----------------|
| **환경 변수** | `IS_LOCAL_DB=True` | `IS_LOCAL_DB=False` |
| **DB 서버 필요** | 불필요 | 필요 |
| **테이블 자동 생성** | 자동 | 수동 |
| **사용 용도** | 개발, 테스트 | 개발, 운영 |

**권장**: 빠른 개발이 필요하면 SQLite 모드로 시작하고, 실제 서비스는 {{DB_TYPE}} 모드로 전환하세요.
