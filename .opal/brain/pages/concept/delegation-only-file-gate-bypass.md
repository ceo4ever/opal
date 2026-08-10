---
type: concept
title: 위임 전용 파일에 게이트를 두면 우회된다 — 진입경로 역추적
tags:
- gate
- architecture
- lesson
- call-graph
sources:
- task:087
related:
- code-scan-gate-deadlock-init-placement
created: '2026-08-10'
updated: '2026-08-10'
status: draft
---
## 개요

위임만 하고 자체 로직이 없는 파일에 게이트(버전 검사 등)를 배치하면, 그 파일을 거치지 않는 진입 경로에서 게이트가 통째로 우회된다. 게이트를 배치하기 전에는 파일의 코드 줄 수가 아니라 호출 그래프 — 모든 진입 경로 — 를 먼저 역추적해야 한다.

## 결정 배경 (WHY)

`scripts/install/linux.sh`는 `exec bash "${INSTALLER}"` 한 줄로 `scripts/install-mac.sh`에 위임하는 얇은 래퍼다(근거: task:087 PLAN.md D-4, `:39`). 원 요구사항(TASK.md R-6)은 Python 버전 게이트를 이 파일에 두라고 지정했다.

그런데 실제 호출 그래프를 추적하자 `opal/tools/opal-cli/lib/update.sh:394-397`이 `install/macos.sh → install-mac.sh` 순서로만 폴백하고 **linux.sh를 전혀 호출하지 않는다**는 사실이 드러났다(근거: task:087 PLAN.md D-8, DONE.md §3). linux.sh에 게이트를 두면 Linux 사용자의 `opal-cli update` 경로에서 게이트가 100% 우회된다 — 얇다는 것이 문제가 아니라, **일부 진입 경로가 그 파일을 아예 거치지 않는다**는 것이 진짜 문제였다.

결정타는 게이트를 macOS/Linux 공용 본체인 `install-mac.sh`의 `install_opal_venv()` 진입부로 옮긴 것이다. 이 함수의 호출부는 대화형 전체 설치(`:1223`)와 메뉴 [4](`:1883`) 두 곳뿐이라, 여기 한 지점에 두면 대화형·비대화형·update 경로가 전부 덮인다(근거: task:087 DONE.md §3).

## 결정 내용

- 게이트를 배치하기 전에 그 파일로 들어오는 **모든 진입 경로**를 역추적한다. 판단 기준은 파일 크기·로직 줄 수가 아니라 호출 그래프다.
- "위임만 하는 파일"(단순 exec/폴백 래퍼)은 그 자체가 게이트 배치 지점이 될 수 없다 — 위임하는 대상 쪽, 혹은 모든 진입 경로가 공유하는 병목 함수에 게이트를 둔다.
- 요구사항 문서가 지정한 파일이 위임 전용임이 드러나면, 실제 배치 위치를 바꾸는 이탈(deviation)을 근거와 함께 명시하고 승인받는다 — 원 파일에는 실제 게이트 소재를 가리키는 주석만 남긴다.

## 영향 범위

여러 진입 경로(대화형 CLI·비대화형 스크립트·업데이트 도구 등)를 갖는 시스템에서 검증·차단 로직을 추가할 때 일반적으로 적용된다. 게이트를 얇은 래퍼에 두면 그 래퍼를 우회하는 경로마다 결함이 재발한다.

## 관련 페이지

- [[code-scan-gate-deadlock-init-placement]]
