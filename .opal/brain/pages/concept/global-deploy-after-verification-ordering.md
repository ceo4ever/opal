---
type: concept
title: 검증 미완 규칙의 전역 배포 차단 — 배포는 검증의 결과여야 한다
tags:
- deploy
- install
- pipeline-order
- framework
- task-095
sources:
- task:095
related:
- active-platform-dir-install-target-lesson
- deploy-artifact-verification-lesson
- strip-deploy-runtime-token-neutral
- scenario-prewrite-goal-series-track
created: '2026-08-19'
updated: '2026-08-19'
status: draft
---
## 개요

프레임워크 규칙 문서를 전역 홈으로 배포하는 설치 스크립트는 모든 프로젝트의 런타임을 즉시 갈아엎는다. 따라서 검증이 끝나지 않은 규칙은 배포하지 않는다 — 실행 계획에서 배포 단계를 테스트 전건 통과 **뒤로** 옮기는 것이 옳다.

## 결정 배경 (WHY)

- 설치 스크립트는 프로젝트 소스의 규칙 문서를 전역 홈으로 복사해 덮어쓴다. 배포 직후부터 그 규칙은 이 계정의 모든 프로젝트에서 활성 규칙이 된다(근거: task:095 DONE.md §6, PLAN.md §4.2).
- 최초 계획은 문서 수정 직후 배포하고 그 뒤에 테스트를 두었다. 이 순서는 검증 미완 규칙이 다른 프로젝트에서 먼저 적용되는 창을 만든다 — 테스트가 실패하면 이미 퍼진 규칙을 회수해야 한다(근거: task:095 DONE.md §6 install 순서 변경 제기).
- 배포본과 소스의 정합 검증 자체도 배포 후에만 가능하므로, "배포 → 정합 확인"과 "규칙 검증 → 배포"의 순서 충돌을 명시적으로 풀어야 했다(근거: task:095 PLAN.md 리스크 가설 H-g).

## 결정 내용

- 실행 계획을 재구성해 **테스트 전건 통과 후 배포**로 순서를 바꿨다. PM이 문제를 제기하고 소유자 승인을 받아 반영했으며, 파이프라인 행 구조는 건드리지 않았으므로 단계 구성 불변 제약을 위반하지 않는다(근거: task:095 DONE.md §6, PLAN.md §4.2 재구성).
- 배포 후 정합 검증은 설치 스크립트의 변경이력 절 제거 특성을 반영해 수행한다 — 제거 후 비교에서 대상 5파일 전건 일치, 배포본 런타임 채택 지점 5곳 전건 확인(근거: task:095 DONE.md §4, → [[strip-deploy-runtime-token-neutral]]).
- 일반 원칙: 배포 대상이 전역 공유 공간(모든 프로젝트가 읽는 홈 디렉토리)이면 배포는 검증의 **결과**여야 하고 검증의 **전제**가 될 수 없다. 계획 단계에서 배포 단계의 위치를 검증 단계와의 순서로 명시한다.

## 영향 범위

- `scripts/install-mac.sh:219-232` — 변경이력 절을 제거하고 전역 홈으로 복사하는 배포 경로(본 태스크에서 변경하지 않음).
- 배포 대상 5문서 — 강제 검증 트랙 규칙, 시나리오 작성 가이드, 게이트 규칙, 오케스트레이터 2종(근거: task:095 DONE.md §3).

## 관련 페이지

- [[active-platform-dir-install-target-lesson]]
- [[deploy-artifact-verification-lesson]]
- [[strip-deploy-runtime-token-neutral]]
- [[scenario-prewrite-goal-series-track]]
