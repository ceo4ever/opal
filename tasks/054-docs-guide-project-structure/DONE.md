# DONE: docs-guide PROJECT.md 프로젝트 구조 섹션 역할 분리

> 완료일: 2026-03-30

## 작업 요약

docs-guide.md의 PROJECT.md "프로젝트 구조" 섹션이 ARCHITECTURE.md, CONVENTIONS.md와 중복되지 않도록 관점별 역할 분리를 명확히 정의했다.

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `~/.opal/skills/opal-project-init/references/docs-guide.md` | 프로젝트 구조 섹션에 PM 탐색 맵 관점 선언, 3문서 역할 분리 테이블, 범위 한정 문구, 작성 규칙 역할 경계 추가 |
| `docs/PROJECT.md` | PM 탐색 관점의 프로젝트 구조 섹션(폴더 구조맵 + 네이밍 규칙) 추가 |

## 핵심 설계 결정

| 문서 | 관점 | 독자 | 핵심 질문 |
|------|------|------|----------|
| PROJECT.md "프로젝트 구조" | PM 탐색 맵 | PM, 오케스트레이터 | "이 문서 어디서 찾지?" |
| ARCHITECTURE.md "디렉토리 구조" | 기술 구조 | 개발 워커 | "코드가 어떻게 구성되어 있지?" |
| CONVENTIONS.md "네이밍 규칙" | 작성 규칙 | 코드 작성자 | "파일명을 어떻게 짓지?" |
