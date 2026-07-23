---
type: concept
title: install hook 소유권-마커 멱등 upsert (외부 hook clobber 해소)
tags:
- install
- deploy
- hook
- idempotent
- ownership-marker
sources:
- task:076
related:
- opal-adapter-platform-isolation
- active-platform-dir-install-target-lesson
created: '2026-07-23'
updated: '2026-07-23'
status: draft
---
## 개요

설치기가 사용자 전역 설정의 hook 구성을 갱신할 때, 이벤트 배열을 통째로 교체하는 대신 소유권 마커로 자기 소유 항목만 선별 갱신하는 멱등 upsert 방식이다. 이로써 외부 도구가 심어둔 hook을 지우지 않으면서 프레임워크 hook을 반복 재배포해도 중복이 쌓이지 않는다.

## 결정 배경 (WHY)

- 기존 설치기는 hook 이벤트를 통째로 덮어써서, 사용자 설정에 이미 존재하던 외부 도구의 PostToolUse hook을 지워버리는 clobber 결함이 있었다 (근거: task:076 TASK.md 배경, PLAN 리스크 H-8).
- 재배포를 여러 번 하면 프레임워크 소유 항목이 중복 누적될 위험이 있어, 몇 번을 실행해도 결과가 같은 멱등성이 필요했다 (근거: task:076 PLAN§3.3.2 DEC-10).
- 병합 로직이 설치 스크립트 인라인 코드에 매몰되어 결정론 단위 검증이 불가능했으므로, 호출 가능한 별도 파일로 분리해 회귀 사각을 없앴다 (근거: task:076 PLAN 리스크 H-11).

## 결정 내용

- 프레임워크가 심는 각 매처 블록에 소유권 마커(`_opal_managed`)를 스탬프한다. 병합 시 마커가 없는 항목(외부 소유)은 보존하고, 마커가 있는 기존 항목은 제거한 뒤 새 항목을 덧붙인다. 결과적으로 외부 hook은 유지되고 프레임워크 hook만 upsert되며, N회 재실행 결과가 동일하다 (`scripts/merge-hooks.py`의 `merge_hooks`).
- 병합 로직을 설치 스크립트에서 분리해 별도 파이썬 파일로 두고, 설치기는 이 파일에 위임 호출한다. 로직이 파일로 분리되어 보존·upsert·멱등을 각각 단위 테스트로 검증한다 (`scripts/install-mac.sh` merge_hooks_config → 위임).
- 소유권 마커는 매처 블록의 형제 키로 두며, 설정을 읽는 플랫폼이 미지 키를 무시한다는 전제 위에 선다. 위험 시 폴백은 마커를 hook 명령 내 주석 시그니처로 이동하는 것이다 (task:076 PLAN§3.3.2 DEC-11).
- 병합 파일은 프레임워크 소스에만 생성하고 설치기가 실행하며, 배포 산출물을 직접 편집하지 않는 배포 경계를 지킨다.

## 영향 범위

- `scripts/merge-hooks.py` — 소유권-마커 멱등 upsert 로직(테스트 seam)
- `scripts/install-mac.sh` — merge_hooks_config 인라인 로직을 위임 호출로 전환
- `~/.claude/settings.json` — 재배포 시 외부 hook 보존 + 프레임워크 hook upsert

## 관련 페이지

- [[pipeline-todo-mirror-hook-enforcement]]
- [[opal-adapter-platform-isolation]]
- [[active-platform-dir-install-target-lesson]]
- [[config-file-concurrent-write-defense-standard]]
