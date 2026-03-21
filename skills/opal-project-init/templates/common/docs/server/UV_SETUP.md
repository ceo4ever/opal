# uv 설정 가이드

이 프로젝트는 **Python {{PYTHON_VERSION}}**와 **uv** 패키지 관리자를 사용합니다.

## uv란?

uv는 Astral에서 개발한 빠르고 현대적인 Python 패키지 관리자입니다. pip와 pip-tools를 대체할 수 있는 도구로, Rust로 작성되어 매우 빠릅니다.

## 설치 방법

### macOS/Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### pip로 설치

```bash
pip install uv
```

## Python {{PYTHON_VERSION}} 설치

### uv로 Python 설치 (권장)

```bash
# Python {{PYTHON_VERSION}} 설치
uv python install {{PYTHON_VERSION}}

# 설치된 Python 버전 확인
uv python list
```

### 수동 설치

Python {{PYTHON_VERSION}}를 직접 다운로드하여 설치할 수도 있습니다:
- 공식 사이트: https://www.python.org/downloads/

## 프로젝트 설정

### 1. 의존성 설치

```bash
# 기본 의존성 설치
uv sync

# 개발 의존성 포함 설치
uv sync --dev
```

### 2. 가상환경 활성화 (선택사항)

uv는 자동으로 가상환경을 관리하지만, 수동으로 활성화하려면:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Python 버전 확인

```bash
# 현재 프로젝트의 Python 버전 확인
python --version  # Python {{PYTHON_VERSION}}.x 여야 함

# 또는 uv로 확인
uv python pin {{PYTHON_VERSION}}
```

## 주요 명령어

### 패키지 관리

```bash
# 의존성 설치
uv sync

# 패키지 추가
uv add fastapi

# 개발 의존성 추가
uv add --dev pytest

# 패키지 제거
uv remove package-name

# 패키지 업데이트
uv sync --upgrade
```

### 스크립트 실행

```bash
# Python 스크립트 실행
uv run python script.py

# 서버 실행
uv run uvicorn main:app --reload
```

### 가상환경 관리

```bash
# 가상환경 생성
uv venv

# 특정 Python 버전으로 가상환경 생성
uv venv --python {{PYTHON_VERSION}}
```

## pyproject.toml

이 프로젝트는 `pyproject.toml` 파일을 사용하여 의존성을 관리합니다.

```toml
[project]
requires-python = ">={{PYTHON_VERSION}}"
dependencies = [
    "fastapi>=0.104.0",
    # ...
]
```

## 문제 해결

### Python {{PYTHON_VERSION}}를 찾을 수 없는 경우

```bash
# uv로 Python {{PYTHON_VERSION}} 설치
uv python install {{PYTHON_VERSION}}

# 또는 시스템에 설치된 Python 경로 지정
uv python pin {{PYTHON_VERSION}} --python /usr/local/bin/python{{PYTHON_VERSION}}
```

### 가상환경 문제

```bash
# 기존 가상환경 삭제 후 재생성
rm -rf .venv
uv sync
```

### 의존성 충돌

```bash
# lock 파일 재생성
rm uv.lock
uv sync
```

## requirements.txt와의 차이점

이 프로젝트는 `pyproject.toml`을 사용하지만, 기존 `requirements.txt`도 유지됩니다.

- **pyproject.toml**: uv 및 최신 Python 도구에서 사용 (권장)
- **requirements.txt**: 기존 pip 환경에서도 사용 가능

## 추가 리소스

- uv 공식 문서: https://github.com/astral-sh/uv
- Python 공식 다운로드: https://www.python.org/downloads/
