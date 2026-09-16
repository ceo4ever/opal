---
type: concept
title: Mode-aware execution continuity contract
tags:
- mode
- state
- pipeline
- agentic
- close
sources:
- task:136
related:
- state-tool-next-action-auto-derivation
- pipeline-user-confirmation-single-status-axis
- pipeline-step-internal-mode-not-a-state-row
- close-related-doc-update-before-ingest
created: '2026-09-16'
updated: '2026-09-16'
status: draft
---
## 개요

모드별 실행 지속성 계약은 단계 산출물 작성과 응답 종료를 분리하는 공통 전이 규칙이다. `interactive`, `semi-agentic`, `agentic` 모드는 모두 `continue`, `await_user`, `blocked`, `complete` 중 하나의 전이 결과를 소비하며, 진행 보고는 전이 정지 신호가 아니다.

## 결정 배경 (WHY)

Pilot 단계 문서에는 단계 완료 후 사용자 승인을 요청하는 문구와 agentic 자동 진행 규칙이 함께 존재할 수 있었다. 이 충돌은 TASK나 PLAN 같은 중간 산출물을 만든 뒤 실제 차단 사유가 없어도 실행이 멈추는 원인이 된다.

CLOSE도 DONE.md 생성만으로 완료 상태가 되면 문서 동기화, brain ingest, 회고, worktree finalize 같은 후속 절차가 누락될 수 있다. 완료 판정은 산출물 하나가 아니라 tail 절차 전체가 끝났다는 결정론적 상태에서만 내려야 한다.

## 결정 내용

전이 판정은 산문 보고가 아니라 state-tool의 구조화 출력과 pipeline 상태가 소유한다. 진행 보고는 `progress_report`로 남기고 계속 진행하며, 사용자 판단이 필요한 요청만 `decision_request`로 분리해 `await_user`를 만든다.

모드별 기본값은 다르게 유지한다. `interactive`는 단계 경계마다 사용자 확인을 기다리고, `semi-agentic`은 Pilot별 자율성 경계 이후 예외가 없으면 계속하며, `agentic`은 파괴적 행위, 중대한 모호성, 권한·사람 전용 검증, CLOSE 진입 승인 같은 공통 예외를 제외하면 계속한다.

CLOSE는 DONE.md 생성, 문서 동기화, brain ingest, 회고, worktree finalize 또는 attribution, final state row를 분리된 tail 행으로 관리한다. 마지막 CLOSE 행만 전체 완료 또는 merge 대기 상태를 만들 수 있다.

플랫폼별 Stop guard는 스킬 본문이 아니라 어댑터와 설치 경계가 소유한다. 지원 가능한 플랫폼은 `continue` 상태에서 조기 종료를 경고하거나 재개 안내를 제공하고, 지원 지점이 없는 플랫폼은 state-tool next action과 resume 정보를 보존한다.

## 영향 범위

- state-tool 전이 출력과 CLOSE 완료 판정
- Pilot pipeline JSON의 CLOSE tail 구조
- 공통 하네스 문서와 Pilot 스킬의 진행 보고 문구
- 플랫폼 hook과 설치 검증 경계
- 모드별 단계 전이·중단 재개 회귀 테스트

## 관련 페이지

- [[state-tool-next-action-auto-derivation]]
- [[pipeline-user-confirmation-single-status-axis]]
- [[pipeline-step-internal-mode-not-a-state-row]]
- [[close-related-doc-update-before-ingest]]
