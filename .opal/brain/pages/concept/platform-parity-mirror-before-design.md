---
type: concept
title: 플랫폼 규약 편측 존재 — 새 설계보다 미러링 우선
tags:
- install
- platform
- lesson
- mirroring
sources:
- task:087
related:
- opal-adapter-platform-isolation
- linux-install-script
created: '2026-08-10'
updated: '2026-08-10'
status: draft
---
## 개요

플랫폼별 설치 규약(자동 설치·옵트아웃·폴백 안내)은 한 플랫폼에서만 만들어지고 다른 플랫폼에는 이식되지 않는 채로 남는 경향이 있다. 결함을 발견했을 때 그 자리에서 새로 설계하기보다, 다른 플랫폼에 이미 해법이 있는지 먼저 확인해야 한다.

## 결정 배경 (WHY)

Windows 설치기(`scripts/install/windows.ps1`)에는 winget을 통한 Python 자동 설치·옵트아웃 환경변수·폴백 안내가 이미 완비되어 있었지만, macOS/Linux 설치기(`scripts/install-mac.sh`, `scripts/install/linux.sh`)에는 Python 버전 확인 코드 자체가 없었다(근거: task:087 TASK.md 배경 분석 §C). 소유자 머신에서는 Homebrew Python 3.14가 PATH에 먼저 잡혀 결함이 드러나지 않았을 뿐, macOS 기본 인터프리터(3.9.6)만 있는 클린 환경에서는 100% 재현된다(근거: task:087 DONE.md §2).

이 결함을 "신규 기능 설계"로 접근했다면 옵트아웃 환경변수명이 플랫폼마다 갈라져 사용자 인터페이스가 분열됐을 것이다. 실제로는 "기존 규약을 찾아 미러링"하는 문제였다 — 하한 판정 로직은 플랫폼 공통으로 두고, 설치 수단(winget/brew/안내)만 어댑터로 분기했다(근거: task:087 DONE.md §3, PLAN.md F-1·F-5).

## 결정 내용

- 여러 플랫폼에 동일한 기능이 필요한 결함을 발견하면, 먼저 다른 플랫폼에 이미 구현된 규약이 있는지 확인한다. 있으면 그 규약을 SSOT로 삼아 미러링하고, 신규 설계를 시작하지 않는다.
- 옵트아웃 변수명·상수값 등 사용자에게 노출되는 인터페이스는 기존 플랫폼의 명칭을 그대로 재사용한다(예: `OPAL_AUTO_INSTALL_PYTHON=0`을 macOS에도 재사용).
- 판정 로직(하한 비교 등)은 플랫폼 공통 함수로 유지하고, 플랫폼별 차이(패키지 매니저 호출 등)만 어댑터 함수 1개 내부에 격리한다.

## 영향 범위

여러 플랫폼 대칭 설치기를 갖는 프로젝트 전반에 적용된다. 한 플랫폼에서 결함·개선이 발견되면 다른 플랫폼 동등 코드를 함께 점검하는 습관이, 사용자 인터페이스 분열과 재설계 비용을 동시에 줄인다.

## 관련 페이지

- [[opal-adapter-platform-isolation]]
- [[linux-install-script]]
