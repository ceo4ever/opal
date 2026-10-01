---
type: concept
title: OPPB run records follow task lifecycle
tags:
- oppb
- run-root
- lifecycle
- cache
sources:
- opal/tools/oppb-runtime-tool/oppb_runtime_tool.py
- docs/proposals/260913_OPPB_프로젝트_빌드_Pilot.md
- task:158
related: []
created: '2026-09-26'
updated: '2026-10-02'
status: draft
---
<!--
@header {
  "module": "oppb-run-records-follow-task-lifecycle",
  "layer": "knowledge",
  "domain": "oppb-runtime",
  "description": "OPPB 실행 기록은 태스크 수명에, 공유 cache는 allocator 수명에 귀속한다는 설계 결정과 종료·legacy 호환 경계를 설명한다.",
  "exports": []
}
-->

## 결정

OPPB의 실행 운영 기록은 공유 허브가 아니라 해당 OPPB 태스크의 `.oppb-run/<run_id>/`에 귀속한다. 여러 태스크가 재사용하는 content-addressed cache만 allocator의 `.opal-cache/oppb/`에 둔다.

## 이유

run 기록은 workgraph, acceptance, attempt 결과, evidence처럼 한 태스크의 목표와 감사 맥락을 설명한다. 따라서 태스크와 수명을 같이해야 발견·보존·정리가 예측 가능하다. 반대로 cache는 여러 실행이 재사용하므로 태스크 수명에 묶으면 중복과 재생성 비용이 커진다.

## 종료 경계

성공 실행은 worktree 회수 전에 cleaned retained bundle을 허브 canonical 태스크의 동일 경로에 게시한다. 로그·결과·증거·최종 상태는 보존하고 lock, Supervisor identity, 임시 index, 검증 sandbox는 제거한다. 실패·중단 실행은 재개를 위해 원본 전체를 유지한다.

## 호환 경계

신규 실행은 허브 `.opal-runs`를 만들지 않는다. 기존 `.opal-runs/<run_id>`는 데이터 이동 없이 조회·재개 호환으로만 수용한다. 이 결정은 OPPB에만 적용하며 OPPL `.oppl-run`, 표준 run-log, 경로 비의존 `opal-agent --run-dir` 계약에는 전파하지 않는다.
