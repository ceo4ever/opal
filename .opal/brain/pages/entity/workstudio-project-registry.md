---
type: entity
title: WorkStudio Project Registry
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: '<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>'
header_synced: <YYYY-MM-DD>
tags:
- desktop
- workstudio
- project-registry
sources:
- task:128
related:
- electron-main-owned-project-registry
created: '2026-09-13'
updated: '2026-09-13'
status: draft
---
## 개요

WorkStudio Project Registry는 사용자가 등록한 Project를 앱 재실행 후에도 최근 접근 순으로 찾고 다시 열 수 있게 하는 데스크톱 저장 컴포넌트다.

## 책임 (WHAT)

- schema version을 갖는 JSON으로 Project 항목을 원자적 저장하고 최근 접근 순으로 반환한다 (`workstudio/electron/project-registry.cjs:90`).
- 실제 경로를 기준으로 중복 등록을 합치고, 유실 경로의 열기를 차단하며, 기존 ID를 유지한 경로 복구를 제공한다 (`workstudio/electron/project-registry.cjs:141`, `workstudio/electron/project-registry.cjs:168`, `workstudio/electron/project-registry.cjs:183`).
- 목록 제거는 registry 항목만 제거하고 Project 폴더는 보존한다 (`workstudio/electron/project-registry.cjs:206`).
- 손상되었거나 지원하지 않는 저장 데이터를 보존한 뒤 빈 목록과 복구 신호를 반환한다 (`workstudio/electron/project-registry.cjs:80`, `workstudio/electron/project-registry.cjs:99`).

## 설계 배경 (WHY)

Project 목록을 화면의 일시 상태가 아닌 데스크톱 저장 경계에 두어야 재실행·유실 경로·손상 데이터를 일관되게 처리할 수 있다. (근거: task:128 PLAN§Decisions and contracts)

사용자의 Project 폴더를 레지스트리 목록과 동일한 생명주기로 다루지 않아야 목록 정리가 디스크 데이터 삭제로 이어지지 않는다. (근거: task:128 PLAN§Decisions and contracts)

## 관계 (HOW)

Electron main이 저장을 소유하고 renderer는 preload IPC를 통해 목록·열기·복구·제거를 요청한다 (`workstudio/electron/preload.cjs:13`).

- [[electron-main-owned-project-registry]]

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|---|---|---|
| `PROJECT_REGISTRY_SCHEMA_VERSION` | `workstudio/electron/project-registry.cjs:15` | 저장 schema version |
| `createProjectRegistry` | `workstudio/electron/project-registry.cjs:75` | registry 작업 생성 경계 |
| `list`, `open`, `register`, `repair`, `remove` | `workstudio/electron/project-registry.cjs:217` | Project registry 사용 인터페이스 |
