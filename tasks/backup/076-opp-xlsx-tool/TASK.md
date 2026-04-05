# TASK: OPAL xlsx-tool — 스킬 공용 xlsx 읽기/쓰기 도구

> 작성일: 2026-04-03 | 작업 유형: 신규 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL 스킬들이 공통으로 호출하여 xlsx 파일을 읽고 쓸 수 있는 CLI 도구를 `opal/core/tools/xlsx-tool/`에 생성한다.

## 배경

OPAL 프레임워크에서 xlsx 핸들링 요구가 빈번하다 (WBS, 로드맵, 외부 데이터 분석, 산출물 저장 등). 현재는 스킬마다 개별적으로 openpyxl/pandas 코드를 작성해야 하며, 일관성이 없고 에이전트가 매번 코드를 생성하느라 오류가 많다. 커뮤니티 xlsx 스킬(`community-skills/anthropics/xlsx/`)은 "사용 가이드"이지 재사용 가능한 도구가 아니다.

## 요구사항

### 읽기 (Read)
- [ ] 단일 시트 xlsx 파일을 읽어 구조화된 데이터(JSON)로 출력
- [ ] 멀티 시트 xlsx 파일 지원 (전체 시트 또는 특정 시트 선택)
- [ ] 엑셀 내용 분석 모드 — 시트 목록, 행/열 수, 헤더 정보 등 메타데이터 제공
- [ ] 특정 범위/조건 검색 — 키워드나 셀 범위로 빠르게 내용 찾기

### 쓰기 (Write)
- [ ] 신규 xlsx 파일 생성 — JSON/CSV 데이터를 입력받아 xlsx로 저장
- [ ] 기존 xlsx 파일 수정 — 특정 셀/범위 값 업데이트
- [ ] 멀티 시트 쓰기 지원
- [ ] 기본 서식 적용 — 헤더 볼드, 열 너비 자동 조정, 테두리 등

### 도구 인터페이스
- [ ] CLI 스크립트로 제공 (`python xlsx-tool.py {command} {args}`)
- [ ] 입출력은 JSON 기반 (에이전트가 파싱하기 용이)
- [ ] 에러 시 구조화된 JSON 에러 응답 반환

## 제약 조건

- 배포 경로: `~/.opal/tools/xlsx-tool/` (install-mac.sh 통해 배포)
- 소스 경로: `opal/core/tools/xlsx-tool/`
- OPAL 공용 가상환경: `~/.opal/.venv/` — install-mac.sh에서 생성 및 패키지 설치
- `run.sh` 래퍼 스크립트로 venv python 호출 (에이전트는 run.sh만 호출)
- `opal/core/tools/requirements.txt` — OPAL 전체 Python 의존성 통합 관리
- 기존 tools 구조(skill-registry 등)와 일관된 디렉토리 구조
- 커뮤니티 xlsx 스킬 원본 수정 금지

## 기술 스택

### Python (venv)
- Python 3.x
- openpyxl — 서식 유지 읽기/쓰기, 셀 단위 조작
- pandas — 데이터 분석, 대량 읽기/쓰기

### OPAL 통합 requirements.txt (신규)
전체 커뮤니티 스킬 전수 조사 결과, 아래 의존성을 통합 관리한다:

```
# Office XML (docx / pptx / xlsx 공통)
openpyxl>=3.1.0
pandas>=2.0.0
lxml>=5.0.0
defusedxml>=0.7.0

# PDF
pypdf>=4.0.0
pdf2image>=1.17.0
pdfplumber>=0.11.0

# Image / GIF
Pillow>=10.0.0
imageio>=2.31.0
imageio-ffmpeg>=0.4.9
numpy>=1.24.0

# AI / MCP
anthropic>=0.39.0
mcp>=1.1.0
PyYAML>=6.0.0

# Web Testing
playwright>=1.40.0
```

### 시스템 의존성 (pip 외, brew로 설치)
- `LibreOffice` — pptx/docx/xlsx 렌더링 (`brew install --cask libreoffice`)
- `poppler` — pdf2image 필수 (`brew install poppler`)

> pptx 스킬은 python-pptx를 사용하지 않음. ZIP/XML 직접 조작 방식 + soffice subprocess.

## 관련 문서

- `community-skills/anthropics/xlsx/SKILL.md` — 커뮤니티 xlsx 스킬 (참고용)
- `docs/ARCHITECTURE.md` — 배포 모델, 도구 위치
- `docs/CONVENTIONS.md` — 네이밍/구조 컨벤션
