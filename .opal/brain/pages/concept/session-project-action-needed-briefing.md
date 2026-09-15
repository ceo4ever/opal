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
- task:133
related:
- state-tool
- memory-tool
- bootstrap-marker-skip-ladder
- conditional-precheck-over-unconditional-alibi-call
- worktree-task-root-allocator-root-split
created: '2026-09-11'
updated: '2026-09-15'
status: active
---
## 개요

프로젝트 세션의 첫 응답은 이미 로드된 운영 상태 중 즉시 행동이 필요한 정보만 짧게 보여준다. 진행 중이거나 차단된 작업은 재개 지점으로, 검토 후보 메모리는 판단 대기 항목으로 분리해 제시한다. 허브에서 직접 수행하는 태스크와 워크트리 레지스트리가 발급한 정규 태스크 경로를 한 목록으로 합쳐, 실행 위치가 달라도 진행 작업을 놓치지 않는다. (근거: task:116 DONE.md §결과, task:133 DONE.md §결과)

## 결정 배경 (WHY)

부트스트랩에서 메모리와 프로젝트 문서를 읽고도 사용자가 다음 행동을 다시 찾아야 하는 재개 비용이 있었다. (근거: task:116 TASK.md §Problem)

상태와 메모리는 서로 다른 SSOT이므로 각각의 전용 도구가 읽기 전용 요약을 제공하도록 분리했다. (근거: task:116 PLAN.md §Decisions and contracts)

초기 상태 요약은 허브의 `tasks/`만 조회해 정규 워크트리에서 진행 중인 작업을 누락했고, 한 건만 표시해 동시에 진행되는 작업을 충분히 드러내지 못했다. 조회 대상을 워크트리만으로 바꾸면 허브 직접 수행 태스크가 반대로 누락되므로 두 실행 경로를 통합하되, 경로는 추론하지 않고 레지스트리 발급값으로 검증하도록 확정했다. (근거: task:133 TASK.md §Problem·Constraints, task:133 PLAN.md D-1·D-2)

## 결정 내용

- 상태 요약은 허브 직접 태스크와 활성 레지스트리의 정규 태스크 경로를 함께 읽고, 진행 중·차단 상태만 최신순으로 모은다. 완료 상태나 손상된 상태는 진행 후보에서 제외한다. (`opal/tools/state-tool/state_tool.py:2541`)
- 동일 태스크의 허브 사본과 활성 워크트리 사본이 함께 있거나 레지스트리·경로가 손상된 경우에는 임의 경로를 정상 후보로 선택하지 않는다. 경로 이상을 별도 진단 목록으로 제한해 노출한다. (`opal/tools/state-tool/state_tool.py:2446`, `opal/tools/state-tool/state_tool.py:2525`)
- 최신 후보는 최대 세 건까지 반환하고 초과분은 잔여 건수로 보존한다. 세션 브리핑은 후보 목록과 `그 외 N건`, 경로 이상 건수를 짧게 렌더링한다. (`opal/tools/state-tool/state_tool.py:2387`, `opal/tools/state-tool/state_tool.py:2533`, `opal/tools/event-loader/event_loader.py:525`)
- 상태와 메모리 조회는 서로 실패를 격리하고, 성공 결과가 있을 때만 `이어보기`와 `우선 검토`를 표시한다. 상태 JSON과 최종 브리핑은 각각 UTF-8 1,024바이트 이내다. (근거: task:133 DONE.md §결과·검증)

## 영향 범위

프로젝트 세션 부트 요약의 상태 수집과 렌더링 계약에 적용된다. 직접 수행 프로젝트의 기존 첫 후보 소비와 빈 결과 동작, 입력 파일 read-only 경계, 메모리 검토 후보의 저장 의미는 유지된다. (근거: task:133 PLAN.md D-1·D-5, task:133 DONE.md §결과)

## 관련 페이지

- [[state-tool]]
- [[memory-tool]]
- [[bootstrap-marker-skip-ladder]]
- [[conditional-precheck-over-unconditional-alibi-call]]
- [[worktree-task-root-allocator-root-split]]
