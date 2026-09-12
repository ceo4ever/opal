---
template: sdlc-v2
---
# TASK: WorkStudio Project Registry

## Problem

WorkStudio의 프로젝트 목록이 목업 데이터와 일시적인 화면 상태에 의존해, 사용자가 등록한 프로젝트를 앱 재실행 후 다시 찾고 열 수 없다. 경로가 이동되거나 삭제된 프로젝트도 정상 항목과 구분되지 않아 복구 행동을 안내할 수 없다.

## Proposed outcome

사용자가 프로젝트를 등록하면 최근 접근 순서와 함께 로컬에 안전하게 보존되고, 앱을 다시 실행해 인트로의 최근 프로젝트 목록에서 재열 수 있다. 유실된 경로는 명시적으로 표시되며 사용자는 디스크의 원본을 삭제하지 않고 목록에서만 제거하거나 새 경로로 복구할 수 있다.

## Affected users and systems

WorkStudio 데스크톱 앱 사용자와 `workstudio/`의 Electron main, typed preload IPC, renderer 프로젝트 선택 화면 및 관련 테스트가 영향받는다. 새 프로젝트 폴더 생성, PM Agent 실행, 실제 PTY Terminal, Agent 대화는 포함하지 않는다.

## Constraints

- C-1: 영속 프로젝트 레지스트리의 읽기·쓰기는 Electron main이 소유하고 renderer는 typed preload IPC만 사용한다.
- C-2: `contextIsolation: true`, `nodeIntegration: false` 보안 경계를 유지한다.
- C-3: 목록 제거는 레지스트리 항목만 제거하며 디스크의 프로젝트 폴더나 파일을 삭제하지 않는다.
- C-4: 저장 데이터에는 schema version을 두고 손상되거나 지원하지 않는 데이터에서 앱이 종료되지 않도록 안전한 빈 상태로 복구한다.
- C-5: WS-F102 이후 기능인 새 폴더 생성과 `.opal` 초기화는 구현하지 않는다.

## Acceptance criteria

- AC-1: 선택한 기존 폴더를 프로젝트로 등록하면 앱 재실행 후에도 같은 항목이 최근 프로젝트 목록에 나타난다.
- AC-2: 프로젝트를 열 때마다 마지막 접근 시각이 갱신되고 최근 접근한 프로젝트부터 정렬된다.
- AC-3: 최근 프로젝트 항목을 선택하면 해당 프로젝트가 현재 WorkStudio 작업 공간으로 열린다.
- AC-4: 디스크에 존재하지 않는 등록 경로는 유실 상태로 표시되고 일반 열기 동작이 차단된다.
- AC-5: 유실 항목을 사용자가 선택한 새 폴더 경로로 복구하면 동일 프로젝트 항목이 정상 상태로 전환된다.
- AC-6: 프로젝트를 목록에서 제거해도 디스크의 폴더와 파일은 보존된다.
- AC-7: 정상·취소·중복 등록·손상 저장 데이터 흐름이 자동 테스트로 검증된다.
- AC-8: 기존 WorkStudio 최초 실행, 프로젝트 선택, 파일 트리 목업 동작의 회귀 테스트가 통과한다.
