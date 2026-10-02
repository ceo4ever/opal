---
type: concept
title: Console 진입 token — 파일 기반 1회 소비 채널
tags:
- console
- auth
- opal-cli
sources:
- task:175
related: [opal-console, console-auth-default-deny-gate, console-open-health-readiness]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

브라우저가 Console 세션을 얻는 유일한 경로는 `opal-cli console open`이 발급한 1회성 진입 token이다. token은 URL fragment로만 전달되고, 서버와 CLI는 파일 하나로 발급·소비 계약을 공유한다. (`dashboard/backend/entry_token.py`, `tasks/175-261001-opd-콘솔-POST-인증-게이트/DONE.md:6`)

## 설계 배경 (WHY)

발급·소비를 사용자 전용 0700 디렉터리의 해시명 0600 파일로 만든 것은 서버 협조 없이 CLI와 테스트 하네스가 같은 계약으로 발급할 수 있고 데몬 재시작과 무관하기 때문이다. 원문은 디스크에 남지 않고 해시만 남는다. (근거: task:175 PLAN§D-9)

소비는 파일 이름 변경으로 원자적 1회만 성공하고, 만료·위조·부재를 구별하지 않아 실패 사유가 새지 않는다. (근거: task:175 PLAN§D-9, D-10)

fragment는 서버로 전송되지 않으며, 브라우저는 교환 요청 전에 주소창에서 지운다. (근거: task:175 PLAN§D-13)

`/health` 응답에 인증 마커를 추가해, 인증 게이트가 없는 구버전 데몬에는 `open`이 브라우저를 열지 않고 재기동만 안내한다. (근거: task:175 PLAN§D-11, D-12)

## 결정 내용

- 기본 유효 60초, 상한 300초. 발급 때 만료 파일을 청소한다.
- 디렉터리 소유자·권한·symlink를 확인하지 못하면 발급·소비를 거부한다.
- 잔여 위험: token이 `open` 명령 인자에 실려 다중 사용자 호스트에서 60초 내 선점 가능. (근거: task:175 DONE§참고)

## 관련 페이지

- [[opal-console]]
- [[console-auth-default-deny-gate]]
- [[console-open-health-readiness]]
