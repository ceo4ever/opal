---
type: concept
title: Electron main-owned Project Registry
tags:
- electron
- security
- workstudio
sources:
- task:128
related:
- workstudio-project-registry
created: '2026-09-13'
updated: '2026-09-13'
status: draft
---
## 개요

WorkStudio의 영속 Project 정보는 Electron main이 소유하고 renderer는 typed preload IPC로만 접근한다. 이 경계는 저장 일관성과 데스크톱 보안 설정을 함께 유지한다.

## 결정 배경 (WHY)

Renderer에 파일 시스템 권한을 주면 Project 선택 UI와 저장 정책이 결합되고 `contextIsolation` 경계가 약해진다. 기존 앱이 사용하는 main/preload/renderer 분리를 유지하면 경로 검증, 원자적 저장, 손상 복구를 하나의 신뢰 경계에 둘 수 있다. (근거: task:128 PLAN§Decisions and contracts)

## 결정 내용

- Electron main이 registry JSON의 읽기·쓰기와 Project 경로 검사를 전담한다 (`workstudio/electron/project-registry.cjs:75`).
- preload는 Project 작업별 IPC 메서드만 renderer에 노출한다 (`workstudio/electron/preload.cjs:13`).
- renderer는 Node API나 registry 파일을 직접 사용하지 않는다 (`workstudio/src/workstudio/ipc.ts:74`).
- BrowserWindow의 `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true` 설정을 유지한다 (`workstudio/electron/main.cjs:260`).

## 영향 범위

인트로의 최근 Project 목록, Project 열기, 유실 경로 복구, 목록 제거와 Files root 전환이 이 경계를 통과한다. 저장 오류는 구조화된 결과로 반환되어 UI가 비정상 종료 없이 대응한다.

## 관련 페이지

- [[workstudio-project-registry]]
