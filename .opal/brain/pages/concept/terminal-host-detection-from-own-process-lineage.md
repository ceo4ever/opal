---
type: concept
title: 터미널 호스트는 자기 프로세스 계보로 판별한다
tags:
- bootstrap
- terminal
- task
sources:
- task:152
related: [worktree-session-launch-order-and-ownership, opal-adapter-platform-isolation, bootstrap-marker-skip-ladder]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

OPAL 부트스트랩이 현재 프로세스가 실행 중인 터미널 호스트를 결정론적으로 판별해 세션 컨텍스트로 쓰고, 워크트리 세션 기동이 그 결과로 어댑터를 고르도록 한 결정이다(`tasks/152-260923-opds-터미널-호스트-부트스트랩-감지/DONE.md:5`).

## 핵심 결정

- 판별 도구(`terminal-context`)는 호스트·멀티플렉서·확신도·근거 네 키만 돌려준다. 우선순위는 명시 호스트 신호 → 프로세스 조상 → tmux 클라이언트 조상 → 터미널 프로그램 환경값 → 알 수 없음이다(`tasks/152-260923-opds-터미널-호스트-부트스트랩-감지/DONE.md:5`, `opal/tools/terminal-context/terminal_context.py`).
- 네 플랫폼 부트스트래퍼는 설정·마커 게이트를 통과한 일반·프로젝트 세션에서만 판별기를 한 번 호출하며, 부트스트랩 끔과 워커 세션의 무로드 계약은 유지한다(`tasks/152-260923-opds-터미널-호스트-부트스트랩-감지/DONE.md:7`).
- 워크트리 기동은 감지한 호스트에 맞는 지원 어댑터만 명시 주입하고, 알 수 없거나 미지원인 호스트는 다른 앱으로 추측해 넘어가지 않고 허브 세션을 유지한 채 비차단 실패로 끝낸다(`tasks/152-260923-opds-터미널-호스트-부트스트랩-감지/DONE.md:9`).
- 실물 cmux 응답을 대조해 보니 응답 형식이 fixture와 달랐고, 어댑터 파싱과 fixture를 실측 형식으로 고쳤다(`tasks/152-260923-opds-터미널-호스트-부트스트랩-감지/DONE.md:11`).

## 관련 페이지

- [[worktree-session-launch-order-and-ownership]]
- [[opal-adapter-platform-isolation]]
- [[bootstrap-marker-skip-ladder]]
