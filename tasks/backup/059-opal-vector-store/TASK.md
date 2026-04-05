# TASK: OPAL 프로젝트 문서 벡터 스토어

> 작성일: 2026-04-01 | 작업 유형: 신규
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

sqlite-vector를 활용하여 OPAL 프로젝트 문서를 임베딩하고, 시맨틱 검색/CRUD가 가능한 벡터 스토어 도구를 OPAL 프레임워크에 추가한다.

## 배경

현재 OPAL 에이전트가 프로젝트 문서를 찾으려면 레지스트리 순회나 정확한 경로를 알아야 한다. 프로젝트 규모가 커질수록 관련 문서를 찾는 비용이 증가한다. 벡터 임베딩 기반 시맨틱 검색을 도입하면 자연어로 관련 문서를 즉시 검색할 수 있다.

- **sqlite-vector**: SQLite 확장으로, 별도 서버 없이 로컬 파일 하나로 벡터 저장/검색 가능
- **적용 대상**: `opi`로 초기화된 각 프로젝트의 전체 문서 (docs/, skills/, agents/, .opal/ 등)
- **참조**: https://github.com/sqliteai/sqlite-vector

## 요구사항

### 핵심 기능

- [ ] 프로젝트 문서를 청킹하여 로컬 임베딩 모델로 벡터 생성
- [ ] sqlite-vector 기반 DB에 벡터 + 메타데이터 저장
- [ ] 시맨틱 검색 (자연어 쿼리 → 유사 문서/청크 반환)
- [ ] CRUD 도구 (저장, 조회, 수정, 삭제)

### 저장 구조

- [ ] 글로벌 DB 위치: `~/.opal/vector.db` (git 영향 없음)
- [ ] 프로젝트별 네임스페이스 분리 (테이블 또는 컬럼으로 프로젝트 식별)
- [ ] 메타데이터: 파일 경로, 청크 위치, 프로젝트명, 갱신 일시

### 도구 형태

- [ ] Node.js 또는 Python 함수로 구현
- [ ] 소스 위치: `opal/tools/vector-store/`
- [ ] 배포 위치: `~/.opal/tools/vector-store/` (install-mac.sh 경유)
- [ ] CLI 실행 가능: `node ~/.opal/tools/vector-store/vector-store.js <command>` 또는 Python 동등

### 배포/설치

- [ ] `install-mac.sh`에서 sqlite-vector 바이너리(macOS arm64 `.dylib`)를 자동 다운로드/배치
- [ ] 임베딩 모델 런타임 의존성도 install-mac.sh에서 설치 (pip/npm)

### 임베딩 모델

- [ ] 로컬 모델 사용 (외부 API 의존 없음)
- [ ] 후보: @xenova/transformers (Node.js) 또는 Ollama 연동 또는 sentence-transformers (Python)
- [ ] 임베딩 provider 플러거블 구조 권장 (향후 다른 모델 교체 용이)

## 제약 조건

- OPAL 프레임워크 위에서 작동해야 함 (`opal/tools/` 소스 구조, `~/.opal/tools/` 배포 구조)
- 기존 `install-mac.sh` 배포 파이프라인과 호환
- sqlite-vector 바이너리는 macOS arm64 지원 필수 (캡틴 환경: darwin arm64)
- 외부 서버/API 의존 없이 완전 로컬 동작
- sqlite-vector 상용 라이선스 확인 필요 (오픈소스 프로젝트 사용은 자유)

## 기술 스택

- **벡터 DB**: sqlite-vector (SQLite 확장)
- **임베딩**: 로컬 모델 (PLAN 단계에서 확정)
- **런타임**: Node.js 또는 Python (PLAN 단계에서 확정)
- **배포**: install-mac.sh

## 관련 문서

- `docs/ARCHITECTURE.md` — 2-레이어 모델, 배포 구조
- `docs/CONVENTIONS.md` — 네이밍/파일 구조 컨벤션
- `~/.opal/references/mcps.md` — MCP 서버 등록 형식 (향후 MCP 확장 시)
- https://github.com/sqliteai/sqlite-vector — sqlite-vector 공식 저장소
