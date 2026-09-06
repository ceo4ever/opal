---
type: concept
title: 비-tty 설치 스크립트 강제 분기 우회 패턴
tags:
- install-script
- non-tty
- bash-source
- technique
sources:
- task:108
related:
- removal-task-boundary-unification
created: '2026-09-06'
updated: '2026-09-06'
status: draft
---
## 개요

비-tty(non-interactive) 환경에서 실행하면 원치 않는 함수까지 강제로 동반 실행하는 설치 스크립트를, 의사 터미널(pty) 할당 없이 필요한 함수만 안전하게 호출하는 패턴이다. 원본과 **같은 디렉토리**에 `main` 호출을 제거한 임시 런처를 두는 방식으로 우회한다(근거: task:108 DONE.md §6 M-4).

## 결정 배경 (WHY)

- (근거: task:108 PLAN.md 결정 M-4, `scripts/install-mac.sh:2192-2197`) 이 설치 스크립트는 표준입력이 tty가 아니라는 조건(`! -t 0`)이 참이면 메뉴 선택 없이 `install_opal` + `install_mcp`를 강제로 함께 실행한다. 워커(에이전트)가 비-tty 환경에서 이 스크립트를 그대로 실행하면 원치 않는 `install_mcp`까지 동반 실행되어 버린다.
- (추론: 코드패턴) `script` 명령으로 pty를 할당해 대화형 메뉴를 흉내 내는 방법도 시도할 수 있으나, 표준입력 레이스 컨디션 때문에 안정적으로 동작하지 않는 사례가 확인됐다(task:108 PLAN.md).
- (추론: 코드패턴) 이 스크립트의 `detect_framework_root` 함수는 `BASH_SOURCE`(자기 자신의 경로)를 기준으로 프레임워크 루트를 "부모의 부모" 디렉토리로 추론한다(`scripts/install-mac.sh:103-106`). 따라서 이 함수에 의존하는 다른 함수(`install_opal` 등)를 호출하려면, 호출부 스크립트가 원본과 **같은 디렉토리 구조상 위치**(또는 상대적으로 동일한 깊이)에 있어야 경로 추론이 깨지지 않는다.

## 결정 내용

- 원본 스크립트를 복사하되 `main "$@"` 호출 라인만 제거한 "임시 런처"를 만든다.
- 이 임시 런처는 원본 스크립트와 **같은 디렉토리**(이번 사례에서는 worktree의 `scripts/`)에 둔다 — `detect_framework_root`의 `BASH_SOURCE` 기반 경로 추론이 위치에 의존하기 때문이다.
- 임시 런처를 source하거나 실행한 뒤, 필요한 함수(예: `install_opal`)만 직접 호출한다. `install_mcp` 등 원치 않는 함수는 호출하지 않는다.
- 이 방식은 pty 할당이나 입력 스푸핑 없이, 비-tty 환경에서도 스크립트가 강제하는 전체 흐름을 우회해 원하는 부분만 안전하게 실행할 수 있게 한다.

## 영향 범위

대화형 메뉴 전제로 작성된 설치·배포 스크립트를 에이전트(비-tty)가 실행해야 하는 모든 상황에 재사용 가능한 패턴이다. `BASH_SOURCE` 기반 경로 추론을 쓰는 스크립트라면 임시 런처의 배치 위치가 특히 중요하다.

## 관련 페이지

- [[removal-task-boundary-unification]]
