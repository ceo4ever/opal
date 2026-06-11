---
type: concept
title: Linux 설치 스크립트 신설 (단순 위임 전략)
tags:
- install
- linux
- deploy
- task
sources:
- task:006
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

`scripts/install/linux.sh`를 신규 신설하고 `install-mac.sh`에 exec 위임하는 "전략 A(단순 위임)"로 Linux 설치 지원을 추가했다. macOS 전용 코드는 1줄(Playwright 캐시 경로)뿐이라는 분석 결과에 근거했다.

## 배경·문제 (WHY)

Linux 환경에서 OPAL 설치 시 fallback 안내만 표시되고 실제 설치가 불가능했다. `install-mac.sh` 1345줄을 분석하자 OS 종속 코드가 Playwright 캐시 경로 1줄뿐이라는 사실이 밝혀졌다.

## 결정 내용 (HOW)

- 전략 A(단순 위임): `linux.sh` → `exec install-mac.sh`. `install-mac.sh`에 `uname -s` 분기로 캐시 경로 1줄 OS 분기 추가.
- 지원 배포판: Ubuntu/Debian 명시 + RHEL/Fedora best effort + Alpine 비지원(musl libc).
- 의존성 처리: 안내만, 자동 설치 없음(기존 graceful skip 패턴 유지).
- 후속 로드맵: `install-core.sh`로 리네이밍(v0.6 검토).

## 영향·관계

- 변경 파일: `scripts/install/linux.sh`(신규), `scripts/install.sh`, `scripts/install-mac.sh`.
- [[opal-architecture]] 배포 채널에 Linux 경로 추가.

## 근거 출처

`sources: task:006` — DONE.md §2~§3 참조.
