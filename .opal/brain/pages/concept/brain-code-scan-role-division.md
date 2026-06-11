---
type: concept
title: brain↔code-scan 역할 분담 — 선별·신선도·깊이 축 (010)
tags:
- brain
- code-scan
- architecture
- policy
sources:
- task:010
related: [wiki-intelligence-decisions-016, brain-tool, code-scan-mandatory-policy]
created: '2026-06-11'
updated: '2026-06-11'
status: active
---

## 개요

opal-brain과 code-scan은 코드 정보를 중복 보관하는 것이 아니라 **선별·신선도·깊이** 3개 축에서 역할이 나뉜다. 016(opal-brain 도입)에서 두 도구가 생겼고, 010에서 그 경계를 명문화했다.

## 결정 배경 (WHY)

016 이후 opal-brain이 도입됐지만, brain과 code-scan의 코드 정보 경계가 문서화되지 않았다:

- PM이 어느 도구를 먼저 써야 하는지, 어느 경우에 어느 도구로 충분한지 불명확.
- `brain-tool analyze`(init 동적 제안 입력)가 code-scan @header 정량 집계에 의존한다는 사실이 명문화되지 않아, code-scan 저보급률이 brain 품질을 낮추는 구조가 방치됐다.
- "brain이 있으니 code-scan 안 써도 된다"는 오해가 code-scan 미사용의 새 원인이 될 위험이 있었다.

## 결정 내용 (HOW)

### 역할 분담 4축 표

| 축 | code-scan | opal-brain |
|----|-----------|------------|
| 코드 정보 범위 | **전수** (전 파일 @header) | **선별** 핵심 모듈만 |
| 신선도 | **실시간** (호출 시점 스캔) | **stale 가능** (ingest/sync 시점 스냅샷) |
| 깊이/성격 | WHAT — 구조·exports·depends | WHY/HOW — 설계 배경 + @header 스냅샷 |
| 원천 | 파일 @header (SSOT) | code-scan @header에서 파생 |

> 코드 정보의 차이는 "포함 여부"가 아니라 **선별·신선도·깊이**다.

### 사용 순서 규약

- 코드 작업 디스패치 전: **brain search → code-scan** 순서 (brain 검색으로 WHY 파악 후 code-scan으로 실시간 WHAT 확인).
- `brain-tool analyze`(init 제안 입력)는 code-scan @header 집계에 의존 → code-scan 보급률이 brain 지식 품질의 상한.

### 사용자 오버라이드

사용자가 "grep으로 해"·"직접 찾아" 등 특정 도구를 명시하면, code-scan 우선 원칙을 보류하고 지정 도구로 즉시 전환한다(소유자 주도성 원칙).

### 적용 위치

- `opal/core/AGENT.md` v3.3 §code-scan 활용 규칙 — 역할 분담 표 + 오버라이드
- `opal/core/references/pm/dispatch-process.md` v1.4 §Step 1.5 — brain→code-scan 순서 + analyze 의존 1줄

## 영향 범위

- `opal/core/AGENT.md` — §code-scan 활용 규칙에 역할 분담 표 신설
- `opal/core/references/pm/dispatch-process.md` — §Step 1.5에 analyze 의존 1줄

## 관련

- [[wiki-intelligence-decisions-016]] — 016 opal-brain 도입 결정 (M-4/M-5 이름·git 추적 포함)
- [[brain-tool]] — analyze/sync-header의 code-scan @header 의존 상세
- [[code-scan-mandatory-policy]] — 이 분담 결정과 연동된 무조건화 규약 (010)
