---
type: concept
title: Console API 인증 게이트 — 단일 미들웨어 기본 거부
tags:
- console
- auth
- security
sources:
- task:172
related: [opal-console, console-entry-token-channel, console-write-exception-router-isolation]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

Console 백엔드의 모든 `/api/` 요청은 라우터에 닿기 전에 단일 미들웨어에서 검사되고, 세션이 없으면 거절된다. 예외는 진입 token 교환과 세션 조회 2종뿐이다. 거절된 요청은 핸들러에 진입하지 않으므로 LLM 실행·설정 쓰기가 일어나지 않는다. (`dashboard/backend/auth.py`, `tasks/172-261001-opd-콘솔-POST-인증-게이트/DONE.md:5`)

## 설계 배경 (WHY)

인증을 라우터별 의존성으로 붙이면 새 라우터가 추가될 때 누락될 수 있어, 라우팅 앞의 한 지점에서 기본 거부로 두었다. (근거: task:172 PLAN§D-1)

기존 읽기 경로도 프로젝트·설정·태스크·문서를 돌려주므로 개별 판정하지 않고 `/api/` 전체를 세션 뒤에 두었다. 상태 확인(`/health`)과 정적 화면은 잠금 화면이 떠야 하므로 세션 없이 응답한다. (근거: task:172 PLAN§D-2)

Origin과 CSRF 헤더는 쿠키의 SameSite 속성과 독립된 방어선으로 두었다. 상태 변경 요청과 WebSocket 연결은 Origin이 없어도 거절한다. (근거: task:172 PLAN§D-4, D-6, D-7)

## 결정 내용

- 검사 순서는 호스트, 출처, 세션, CSRF다. 호스트는 loopback 이름과 명시 허용 목록만 통과하며 포트는 비교하지 않는다(DNS rebinding 방어).
- 세션은 HttpOnly·SameSite=Strict 쿠키로 12시간 유지되고 서버 재시작 시 모두 소멸한다. CSRF 값은 브라우저 메모리에만 둔다.
- WebSocket 연결은 같은 지점에서 수락 전에 닫는다. 새 라우트는 자동으로 이 보호를 받는다.
- CORS는 정확 일치 목록을 유지하되 자격 증명 허용으로 바꾸고, CORS가 바깥·인증이 안쪽에 놓여 preflight는 세션 없이 응답한다. (근거: task:172 PLAN§D-8)
- 잔여 위험(보안 점검 Medium): 개발용 CORS 기본 출처가 항상 허용됨, API 문서 경로가 세션 없이 응답함. (근거: task:172 DONE§참고)

## 영향 범위

`dashboard/backend/auth.py`, `dashboard/backend/main.py`, 프런트엔드 잠금 화면과 부트스트랩(`dashboard/frontend/src/lib/auth.ts`).

## 관련 페이지

- [[opal-console]]
- [[console-entry-token-channel]]
- [[console-write-exception-router-isolation]]
