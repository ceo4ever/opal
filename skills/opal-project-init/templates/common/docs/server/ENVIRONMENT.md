# 서버 환경 변수 관리 가이드

## 개요

이 프로젝트는 `.env` 파일을 사용하여 환경 변수를 관리합니다. 코드에 민감한 정보(DB 비밀번호, JWT 시크릿, AWS 키 등)를 하드코딩하지 않고, 환경별로 다른 설정을 쉽게 관리할 수 있습니다.

## 환경 변수 파일 구조

```
backend/
├── .env.example        # 템플릿 (Git 포함)
├── .env.local         # 로컬 개발 (Git 제외)
├── .env.dev           # 개발 서버 (Git 제외)
└── .env.production    # 운영 서버 (Git 제외)
```

### .env 파일 우선순위

1. `.env.{PROFILES_ACTIVE}` (예: `.env.local`, `.env.dev`)
2. `.env.local` (기본값)
3. `.env`
4. 코드 내 기본값

## 빠른 시작

### 1. .env 파일 생성

```bash
cd backend

# .env.example을 복사하여 .env.local 생성
cp .env.example .env.local
```

### 2. .env.local 파일 수정

`.env.local` 파일을 열어 필요한 값을 수정합니다:

```bash
# 환경 프로필
PROFILES_ACTIVE=local

# 데이터베이스 모드
IS_LOCAL_DB=True  # True: 로컬 DB (SQLite 등), False: 원격 DB

# DB 설정 (IS_LOCAL_DB=False 일 때 사용)
DB_HOST=your_db_host
DB_PORT={{DB_PORT}}
DB_NAME={{PROJECT_NAME}}
DB_USER=appusr
DB_PASSWORD=your_password_here

# JWT 인증 설정
JWT_ADM_SECRET=your_admin_secret_here
JWT_API_SECRET=your_api_secret_here
JWT_ALGORITHM=HS256

# AWS 설정
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=ap-northeast-2
AWS_S3_BUCKET=your-bucket-name
```

### 3. 서버 실행

환경 변수는 자동으로 로드됩니다:

```bash
cd App/{{DOMAIN_NAME}}
uv run python main.py
```

출력 예시:
```
Loaded environment from: /path/to/backend/.env.local
```

## 주요 환경 변수

### 필수 환경 변수

| 변수명 | 설명 | 예시 | 기본값 |
|--------|------|------|--------|
| `PROFILES_ACTIVE` | 환경 프로필 | `local`, `dev`, `production` | `local` |
| `IS_LOCAL_DB` | DB 모드 | `True` (로컬), `False` (원격) | `True` |

### 데이터베이스 설정

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `DB_HOST` | DB 호스트 | `localhost` |
| `DB_PORT` | DB 포트 | `{{DB_PORT}}` |
| `DB_NAME` | 데이터베이스 이름 | `{{PROJECT_NAME}}` |
| `DB_USER` | 데이터베이스 사용자 | `appusr` |
| `DB_PASSWORD` | 데이터베이스 비밀번호 | `your_password` |
| `LOCAL_DB_PATH` | 로컬 DB 파일 경로 | `../../Core/domains/{{DOMAIN_NAME}}/model/local.db` |

### 인증 설정

| 변수명 | 설명 |
|--------|------|
| `JWT_ADM_SECRET` | 관리자 JWT 시크릿 키 (최소 32자) |
| `JWT_API_SECRET` | API JWT 시크릿 키 (최소 32자) |
| `JWT_ALGORITHM` | JWT 알고리즘 (기본: `HS256`) |

### AWS 설정

| 변수명 | 설명 |
|--------|------|
| `AWS_ACCESS_KEY_ID` | AWS 액세스 키 |
| `AWS_SECRET_ACCESS_KEY` | AWS 시크릿 키 |
| `AWS_DEFAULT_REGION` | AWS 리전 (기본: `ap-northeast-2`) |
| `AWS_S3_BUCKET` | S3 버킷 이름 |
| `AWS_S3_LINK_URL` | S3 링크 URL (선택사항) |

### 로깅 설정

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `LOG_FILE_PATH` | 로그 파일 경로 | `/tmp/logs/` |
| `LOG_BATCH_FILE_PATH` | 배치 로그 경로 | `/tmp/logs/batch/` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |

### 서버 URL 설정

| 변수명 | 설명 |
|--------|------|
| `SERVICE_URL` | 프론트엔드 URL |
| `SERVICE_API_URL` | API 서버 URL |
| `BATCH_API_URL` | 배치 서버 URL (선택사항) |

## 환경별 설정

### 로컬 개발 환경 (.env.local)

```bash
PROFILES_ACTIVE=local
IS_LOCAL_DB=True  # 로컬 DB 사용

# 개발용 키
JWT_API_SECRET=dev_secret_key_for_local

SERVICE_URL=http://localhost:{{CLIENT_PORT}}
SERVICE_API_URL={{API_URL_LOCAL}}
```

### 개발 서버 환경 (.env.dev)

```bash
PROFILES_ACTIVE=dev
IS_LOCAL_DB=False  # 원격 DB 사용

# 실제 DB 정보
DB_HOST=dev-db.example.com
DB_NAME={{PROJECT_NAME}}_dev
DB_PASSWORD=secure_dev_password

# 개발 서버용 키
JWT_API_SECRET=dev_server_secret_key

SERVICE_URL=https://dev.example.com
SERVICE_API_URL=https://api-dev.example.com
```

### 운영 서버 환경 (.env.production)

```bash
PROFILES_ACTIVE=production
IS_LOCAL_DB=False  # 원격 DB 사용

# 운영 DB 정보
DB_HOST=prod-db.example.com
DB_NAME={{PROJECT_NAME}}
DB_PASSWORD=super_secure_production_password

# 운영 서버용 키 (매우 강력하게!)
JWT_API_SECRET=production_very_secure_secret_key_min_32_chars

SERVICE_URL=https://www.example.com
SERVICE_API_URL=https://api.example.com
```

## 보안 주의사항

### 절대 하지 말아야 할 것

1. **Git에 .env 파일 커밋하지 않기**
   - `.env.local`, `.env.dev`, `.env.production`은 Git에 포함하지 않음
   - `.gitignore`에 이미 설정되어 있음

2. **코드에 민감 정보 하드코딩하지 않기**
   - DB 비밀번호, JWT 시크릿, AWS 키 등
   - 모두 `.env` 파일에서 관리

3. **운영 환경 키를 개발 환경에 사용하지 않기**
   - 환경별로 다른 키 사용

### 해야 할 것

1. **.env.example 업데이트**
   - 새로운 환경 변수를 추가할 때마다 `.env.example`도 업데이트
   - 실제 값 대신 `your_value_here` 형태로 작성

2. **강력한 시크릿 키 사용**
   ```bash
   # 랜덤 시크릿 키 생성 (Python)
   python -c "import secrets; print(secrets.token_hex(32))"

   # 또는 OpenSSL 사용
   openssl rand -hex 32
   ```

3. **환경 변수 검증**
   - 서버 시작 시 필수 환경 변수가 설정되었는지 확인

## 문제 해결

### .env 파일이 로드되지 않음

**증상:**
```
No .env file found, using default values
```

**해결 방법:**
```bash
# 1. .env 파일이 올바른 위치에 있는지 확인
ls -la backend/.env*

# 2. .env 파일 권한 확인
chmod 644 backend/.env.local

# 3. .env 파일 생성
cd backend
cp .env.example .env.local
```

### 환경 변수가 적용되지 않음

**원인:**
- `.env` 파일의 형식이 잘못됨
- 주석 처리되어 있음
- 공백이나 따옴표 문제

**해결 방법:**
```bash
# 올바른 형식
KEY=value

# 잘못된 형식
KEY = value      # 등호 양옆 공백 X
KEY="value"      # 따옴표 불필요
# KEY=value      # 주석 처리됨
```

### 환경 변수 로드 확인

```bash
cd backend
uv run python -c "
import sys
sys.path.insert(0, 'Core')
from framework.config.env import getConfig
config = getConfig()
print(f'Profile: {config.profile}')
print(f'IS_LOCAL_DB: {config.IS_LOCAL_DB}')
print(f'JWT_API_SECRET 설정됨: {bool(config.JWT_API_SECRET)}')
"
```

## 참고 문서

- [프로젝트 구조](./PROJECT_STRUCTURE.md)
- [클라이언트 환경 변수](../client/ENVIRONMENT.md)

## 추가 정보

### python-dotenv 라이브러리

이 프로젝트는 `python-dotenv` 라이브러리를 사용하여 `.env` 파일을 로드합니다.

```python
# backend/Core/framework/config/env.py
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = BASE_DIR / f".env.{os.getenv('PROFILES_ACTIVE', 'local')}"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
```

### 환경 변수 우선순위 예시

1. 명령줄: `PROFILES_ACTIVE=dev uv run python main.py`
   - `.env.dev` 로드

2. 환경 변수 없음: `uv run python main.py`
   - `.env.local` 로드 (기본값)

3. `.env` 파일 없음
   - 코드 내 기본값 사용
