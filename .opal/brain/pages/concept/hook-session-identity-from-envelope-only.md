---
type: concept
title: 훅의 세션 신원은 이벤트 봉투로만 정한다
tags:
- ownership
- hook
- task
sources:
- task:153
related: [ownership-tool, worktree-session-launch-order-and-ownership]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

부모 세션의 환경변수를 물려받은 자식 CLI(예: MCP 조회 명령)가 끝날 때 부모 태스크의 작업 소유권과 세션 등록이 해제되던 결함을 막기 위해, 소유권 도구의 훅이 세션을 이벤트 봉투의 세션 식별자로만 식별하도록 바꾼 결정이다(`tasks/153-260923-opds-훅-세션-식별-분리/DONE.md:5`).

## 핵심 결정

- 훅 세션 식별 함수는 봉투의 세션 식별자가 공백이 아닌 문자열일 때만 그 값을 쓰고 환경변수는 받지 않는다. 세션 시작·종료·생존 신호·도구 사용 전 가드·종료 판정의 여섯 지점이 이 함수를 쓴다(`tasks/153-260923-opds-훅-세션-식별-분리/DONE.md:7-8`, `opal/tools/ownership-tool/ownership_tool/ownership_core.py`).
- 봉투 신원이 없으면 진단만 남기고 소유권·세션·영수증 파일을 쓰지 않는다. 도구 사용 전 가드는 차단 없이 통과(기존 fail-open 유지)한다(`tasks/153-260923-opds-훅-세션-식별-분리/DONE.md:9`).
- 일반 CLI의 세션 식별(명시 인자 우선, 그다음 환경변수)과 상태 도구의 환경 기반 식별은 그대로 둔다 — 훅 경로에만 적용되는 경계다(`tasks/153-260923-opds-훅-세션-식별-분리/DONE.md:12`).
- 실 CLI 재현에서 구현 전에는 부모 소유권이 해제되고, 구현 후에는 유지됨을 확인했다(`tasks/153-260923-opds-훅-세션-식별-분리/DONE.md:33`).

## 관련 페이지

- [[ownership-tool]]
- [[worktree-session-launch-order-and-ownership]]
