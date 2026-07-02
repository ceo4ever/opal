---
type: entity
title: git-sync-tool
module: git_sync_tool
layer: tool
domain: workspace
exports: [sync]
source_ref: 'opal/tools/git-sync-tool/git_sync_tool.py'
header_synced: 2026-07-02
tags:
- tool
- git
- workspace
- safety
sources:
- task:052
related:
- opal-workspace-sync
- fallback-approval-detached-head-precedence
created: '2026-07-02'
updated: '2026-07-02'
status: active
---

## 개요

워크스페이스 아래 여러 독립 git 저장소를 순회하며 "건드려도 안전한 저장소만" 자동으로 최신화하는 결정론 도구다. 사람이 매번 여러 저장소를 수동으로 pull하는 반복 작업을 없애면서도, 로컬 미커밋 변경을 덮어쓰거나 충돌 잔재를 남기는 사고를 방지하기 위해 신설되었다 (근거: task:052 TASK§배경).

## 책임 (WHAT)

- 대상 경로가 그 자체로 단일 git 루트이면 그 1개를, 아니면 직속 자식 디렉토리 1단계(재귀 없음)를 순회 대상으로 삼는다 (`opal/tools/git-sync-tool/git_sync_tool.py`).
- 저장소별로 fetch 후 다섯 가지 skip 사유(dirty / diverged / detached HEAD / no-upstream / fetch-failed)를 판정하고, clean이면서 fast-forward 가능한 경우에만 fast-forward 전용 pull로 최신화한다 (근거: task:052 PLAN§3.1.2(d)).
- 저장소별 결과(브랜치, upstream, status, reason, ahead/behind, prev/new head)를 하나의 JSON으로 반환한다. `run.sh` 래퍼 + `ok/error` 계약을 따른다.

## 설계 배경 (WHY)

- pull 정책을 fast-forward 전용으로 고정한 것은 "문제가 있는 저장소는 판단 없이 skip한다"는 원칙을 git 명령 레벨에서 강제하기 위해서다. diverged 저장소를 병합할지 말지는 사람의 판단 영역이며, 도구가 자동으로 병합·리베이스·강제push를 수행하지 않는다 (근거: task:052 TASK§확정 설계 방향 "알투 자율 실행 절대 금지").
- 결정론 로직을 도구로, 오케스트레이션(대상 결정·보고·승인)을 스킬로 분리한 것은, "무엇을 할지 결정하는 판단"과 "정해진 일을 안전하게 집행하는 실행"을 분리해 자율 조치 위험을 구조적으로 차단하기 위해서다 (근거: task:052 PLAN§1.1 "enforce, don't advise").
- 판정 순서는 원래 no-upstream을 detached보다 먼저 검사하도록 설계됐으나, 실제 git 동작 검증 중 결함이 발견되어 순서가 교정되었다 — 상세는 [[fallback-approval-detached-head-precedence]] 참조 (근거: task:052 AGENTIC-LOG #6·#7).

## 관계 (HOW)

- [[opal-workspace-sync]] — 이 도구를 호출하는 오케스트레이션 스킬. 대상 경로 결정과 5섹션 보고서·승인 게이트를 담당하고, 이 도구는 결정된 경로 하나만 받아 순회를 집행한다.
- state-tool의 run.sh 래퍼 패턴을 그대로 재사용했다 (`opal/tools/state-tool/run.sh` 참조 원본).

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `run.sh` | `opal/tools/git-sync-tool/run.sh` | venv 검사 → python 위임 래퍼 |
| `git_sync_tool.py` | `opal/tools/git-sync-tool/git_sync_tool.py` | 순회·판정·JSON 조립 본체 |
| `sync <path>` | `opal/tools/git-sync-tool/git_sync_tool.py` argparse 서브명령 | 유일한 서브명령, 경로 인자 하나 |
