---
type: concept
title: 동작검증은 배포 산출물+실 브라우저 기준으로 수행해야 한다
tags: [verification, qa, deployment, lesson]
sources: [task:021]
related: [opal-console, opal-conventions]
created: 2026-06-15
updated: 2026-06-15
status: active
---

## 개요

빌드 성공·pytest 통과만으로는 배포본에서 발생하는 결함(import 크래시, 레이아웃 겹침, 패키지 버전 불일치, URL 라우팅 실패)을 잡을 수 없다. 동작검증은 반드시 **배포 산출물 기준 + 실 브라우저(cmux)** 에서 재현해야 한다.

## 결정 배경 (WHY)

태스크 021(OPAL Console) 동작검증에서 자동검증(build 성공, pytest 76 passed)만으로는 아래 결함들이 누락되었다:
- **배포본 import 크래시**: 소스 트리에서는 정상이나, `~/.opal/dashboard-server/`에 배포 후 모듈 경로 불일치로 크래시
- **레이아웃 겹침**: 빌드 결과물에서만 나타나는 CSS 충돌
- **resizable 버전 불일치**: 소스 `package.json`과 배포 dist가 다른 shadcn 버전 참조
- **식별자 path segment 슬래시 매칭 실패**: 실 브라우저 + 배포 서버에서만 재현

캡틴 실테스트(cmux)로 배포본 기준 검증을 도입한 뒤 결함을 정확히 잡아냈다.

## 결정 내용

- 자동검증(빌드·pytest·lint)은 필요조건이지 충분조건이 아니다
- QA 최종 단계는 반드시 `install_dashboard()` 배포 후 실 브라우저에서 수행한다
- "소스 트리 기준 검증"만으로 통과 처리하는 self-confirming 패턴을 방지해야 한다
- cmux 실렌더 검증 항목: 5화면 렌더·전역 컨텍스트 전환·칸반 정렬·오른쪽 패널 스크롤·@header 아코디언·TOC 클릭

## 영향 범위

이 교훈은 OPAL Console 한정이 아니라, **배포 단계가 있는 모든 컴포넌트** (FE 빌드, Python 패키지, shell 스크립트 배포 등)의 QA 프로세스에 적용된다.

## 관련 페이지

- [[opal-console]]
- [[opal-conventions]]
