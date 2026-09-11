---
type: concept
title: 프로젝트 세션 행동 필요 브리핑
tags:
- bootstrap
- session
- state
- memory
sources:
- task:116
related:
- state-tool
- memory-tool
- bootstrap-marker-skip-ladder
- conditional-precheck-over-unconditional-alibi-call
created: '2026-09-11'
updated: '2026-09-11'
status: active
---
## 개요

프로젝트 세션의 첫 응답은 이미 로드된 운영 상태 중 즉시 행동이 필요한 정보만 짧게 보여준다. 진행 중이거나 차단된 최신 작업은 재개 지점으로, 검토 후보 메모리는 판단 대기 항목으로 분리해 제시한다. (근거: task:116 DONE.md §결과)

## 결정 배경 (WHY)

부트스트랩에서 메모리와 프로젝트 문서를 읽고도 사용자가 다음 행동을 다시 찾아야 하는 재개 비용이 있었다. (근거: task:116 TASK.md §Problem)

상태와 메모리는 서로 다른 SSOT이므로 각각의 전용 도구가 읽기 전용 요약을 제공하도록 분리했다. (근거: task:116 PLAN.md §Decisions and contracts)

## 결정 내용

- `state-tool boot-summary`는 프로젝트 태스크 중 `in_progress` 또는 `blocked`인 최신 작업 하나만 제목·현재 단계·다음 행동으로 반환한다. 완료·추가 작업·손상 입력은 제외한다. (`opal/tools/state-tool/state_tool.py:4007`)
- `memory-tool --boot-brief`는 기존 요약 키를 보존하면서 `review_rows`를 추가한다. `candidate`를 우선하고 active 피드백·이슈·개선 항목을 결정론적으로 최대 두 건 선택한다. (`opal/tools/memory-tool/memory_tool.py:1352`)
- 두 조회는 `session.project`에서 상태→메모리 순서로만 소비하고, 성공 결과가 있을 때만 `이어보기`와 `우선 검토`를 표시한다. 전체 직렬화 출력은 UTF-8 1,024바이트 이내다. (`opal/bootstrapper/codex-bootstrap.md:35`)

## 영향 범위

Codex·Claude·Cursor·Gemini 부트스트랩 소스와 state-tool/memory-tool의 additive CLI 출력 계약에 적용된다. 일반 assistant/worker 세션, disabled 세션, 기존 부트 응답의 빈 결과 동작은 변경하지 않는다. (근거: task:116 PLAN.md §Decisions and contracts, DONE.md §검증)

## 관련 페이지

- [[state-tool]]
- [[memory-tool]]
- [[bootstrap-marker-skip-ladder]]
- [[conditional-precheck-over-unconditional-alibi-call]]
