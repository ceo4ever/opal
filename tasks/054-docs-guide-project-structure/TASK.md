# TASK: docs-guide PROJECT.md 프로젝트 구조 섹션 역할 분리

> 작성일: 2026-03-30 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

docs-guide.md의 PROJECT.md "프로젝트 구조" 섹션이 ARCHITECTURE.md, CONVENTIONS.md와 중복되지 않도록 **관점별 역할 분리**를 명확히 정의한다.

## 배경

다른 프로젝트의 PM이 기획+개발 프로젝트에서 기획 문서 탐색을 위해 PROJECT.md에 "프로젝트 구조"(폴더 구조맵 + 네이밍 규칙) 섹션을 추가 제안했다. 이미 docs-guide.md에 반영되었으나, ARCHITECTURE.md의 "디렉토리 구조"와 CONVENTIONS.md의 "네이밍 규칙"과 정보가 겹칠 수 있다.

캡틴과 논의한 결과, **관점 분리** 방식으로 중복을 해소하기로 결정:

| 문서 | 관점 | 독자 | 질문 |
|------|------|------|------|
| PROJECT.md 프로젝트 구조 | PM 탐색 맵 | PM, 오케스트레이터 | "이 문서 어디서 찾지?" |
| ARCHITECTURE.md | 기술 구조 | 개발 워커 | "코드가 어떻게 구성되어 있지?" |
| CONVENTIONS.md | 작성 규칙 | 코드 작성자 | "파일명을 어떻게 짓지?" |

## 요구사항

- [ ] docs-guide.md의 PROJECT.md "프로젝트 구조" 섹션에 **PM 탐색 맵** 역할을 명시
- [ ] 폴더 구조맵: PM/오케스트레이터가 "어떤 폴더에 어떤 종류의 문서가 있는지" 파악하는 용도로 한정
- [ ] 네이밍 규칙: PM이 Glob으로 기획 문서를 동적 탐색하는 데 필요한 패턴만 기재
- [ ] ARCHITECTURE.md, CONVENTIONS.md와의 역할 경계를 가이드에 명확히 기술
- [ ] 기존 ai-framework 프로젝트의 PROJECT.md에 프로젝트 구조 섹션 추가 (가이드에 맞춰)

## 제약 조건

- 기존 ARCHITECTURE.md, CONVENTIONS.md의 구조는 변경하지 않음
- docs-guide.md 외 파일은 최소한으로 변경
- 가이드에 이미 있는 "파일 단위 레지스트리는 만들지 않는다" 원칙 유지

## 기술 스택

- 마크다운 문서

## 관련 문서

- `~/.opal/skills/opal-project-init/references/docs-guide.md` — 수정 대상
- `docs/PROJECT.md` — 기존 프로젝트 정의 문서
- `docs/ARCHITECTURE.md` — 기존 아키텍처 문서
- `docs/CONVENTIONS.md` — 기존 컨벤션 문서
