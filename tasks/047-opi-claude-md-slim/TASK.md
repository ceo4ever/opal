# TASK: 플랫폼 파일 슬림화 + PM 컨텍스트 로드 최적화

> 작성일: 2026-03-30 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

CLAUDE.md에서 docs/와 중복되는 내용을 제거하고, PM 컨텍스트 로드에서 불필요한 자동 Read를 제거하여 부트스트랩 효율을 높인다.

## 배경

- CLAUDE.md에 소스 구조(78줄), 배포 구조(37줄) 등 203줄이 직접 기재되어 매 세션마다 컨텍스트 소비
- 이 정보는 docs/PROJECT.md, docs/ARCHITECTURE.md에 이미 존재 (이중 로딩)
- PM 컨텍스트에서 CONVENTIONS.md를 자동 Read하지만, PROJECT.md 문서 테이블에서 PM이 필요 시 읽으면 충분

## 요구사항

- [ ] opal CLAUDE.md를 부트스트래퍼 + docs/ 참조 포인터만으로 슬림화
- [ ] AGENT.md PM 컨텍스트 로드에서 CONVENTIONS.md 자동 Read 제거
