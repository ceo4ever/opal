---
template: sdlc-v2
---
# TASK: 부트 요약 실행 경로 통합

## Problem
프로젝트 세션의 `이어보기` 브리핑이 허브의 직접 수행 태스크만 조회하여, registry가 canonical 경로를 발급한 `--wt` 진행 태스크를 누락한다. 반대로 워크트리만 조회하도록 바꾸면 허브에서 직접 수행하는 태스크가 누락되므로 두 실행 경로를 함께 다뤄야 한다. 현재 최대 1건 표시 계약도 여러 태스크가 동시에 진행되는 운영 상태를 충분히 드러내지 못한다 (`opal/tools/state-tool/state_tool.py:2384-2432`, `opal/tools/event-loader/event_loader.py:525-568`).

## Proposed outcome
세션 시작 브리핑이 허브 직접 수행 태스크와 registry 기반 워크트리 태스크를 하나의 최신 진행 목록으로 합쳐 표시한다. 동일 태스크의 복수 사본이나 손상된 registry 상태는 임의 선택하거나 조용히 누락하지 않고 canonical 소유권 계약에 따라 처리하며, 표시 한도를 넘는 진행 태스크는 잔여 건수로 드러낸다.

## Affected users and systems
OPAL 프로젝트에 진입해 세션 브리핑으로 진행 작업을 복원하는 사용자와 PM이 영향을 받는다. 변경 범위는 `state-tool boot-summary`, `event-loader project-brief`, 관련 테스트·공개 계약 문서와 설치 배포 동치이며, 태스크 상태 쓰기·worktree 생성/회수·메모리 인덱스의 저장 의미는 변경하지 않는다.

## Constraints
- C-1: 허브 직접 수행 태스크와 `--wt` 태스크를 모두 포함하며 어느 한 실행 방식에 종속시키지 않는다.
- C-2: `--wt` 태스크 경로는 `.opal-worktrees` 문자열이나 cwd로 추측하지 않고 worktree registry가 발급한 canonical 메타데이터를 사용한다 (`opal/core/references/harness/worktree.md` §canonical path 발급 계약).
- C-3: 등록된 활성 워크트리와 허브 사본이 충돌하면 임의 선택하지 않으며, canonical 소유권 이상을 사용자에게 관찰 가능하게 만든다 (`opal/core/references/harness/worktree.md` §상태 의존 해석).
- C-4: 진행 후보는 `state.json`의 `current_status`, `updated_at`, 파이프라인 행과 `next_action`을 SSOT로 사용하고 파일을 변경하지 않는다.
- C-5: 전체 브리핑은 UTF-8 1,024바이트 이하의 결정론적 출력과 기존 세션 이벤트 분기를 유지한다.
- C-6: 기존 비워크트리 프로젝트와 `state-tool show`·메모리 검토 후보 동작을 회귀시키지 않는다.
- C-7: 프로젝트 소스만 수정하고 `~/.opal/` 배포본은 install 경유로 갱신하며 source와 installed 동치를 검증한다.
- C-8: 기존 사용자 변경과 다른 활성 워크트리의 파일을 수정하지 않고 태스크 133의 canonical worktree 안에서만 작업한다.

## Acceptance criteria
- AC-1: 허브에 직접 수행 중인 태스크만 존재하면 해당 태스크가 `이어보기` 후보로 반환된다.
- AC-2: registry가 가리키는 canonical 워크트리에 진행 중 태스크만 존재하면 해당 태스크가 `이어보기` 후보로 반환된다.
- AC-3: 직접 수행 태스크와 `--wt` 태스크가 함께 존재하면 두 경로의 후보가 통합되고 `updated_at` 최신순으로 정렬된다.
- AC-4: 동일 `task_folder`의 중복 사본은 canonical 소유권 상태에 따라 한 번만 처리되며 임의 경로 선택이 발생하지 않는다.
- AC-5: registry 누락·경로 소실·활성 중복처럼 canonical 판정이 불가능한 태스크가 정상 진행 항목으로 오인되지 않고 진단 정보로 노출된다.
- AC-6: 진행 태스크가 표시 상한보다 많으면 최신 항목들과 `그 외 N건`이 함께 표시되어 누락 사실을 알 수 있다.
- AC-7: `done`, `completed_unmerged`, `additional_work_done` 및 손상되거나 필수 필드가 없는 상태 파일은 진행 후보에서 제외된다.
- AC-8: `project-brief` 결과는 상태·메모리 블록 조합과 무관하게 UTF-8 1,024바이트 이하이며 입력 파일의 바이트가 변하지 않는다.
- AC-9: 기존 state-tool, event-loader, worktree 관련 회귀 테스트와 신규 혼합 실행 경로 테스트가 모두 통과한다.
- AC-10: 실제 태스크 123·127·129·132가 있는 허브에서 source와 installed `project-brief`가 워크트리 진행 상태를 포함한 동일 결과를 반환한다.
- AC-11: 프로젝트 문서와 도구 설명이 직접 수행+registry 기반 워크트리 통합 조회 계약을 가리키며 중복 SSOT를 만들지 않는다.
