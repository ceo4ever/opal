---
type: concept
title: OPAL 코드 컨벤션
tags:
- convention
- naming
- commit
- guard
- state
sources:
- doc:docs/CONVENTIONS.md
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OPAL 프레임워크 구성요소(스킬·에이전트·도구·하네스)를 작성할 때 따르는 네이밍·파일 구조·커밋·구현 규칙의 단일 진입점 문서다.

## 핵심 결정

- **언어**: 문서 본문은 한국어, 코드·필드명·파일명은 English kebab-case (Python은 snake_case).
- **네이밍 체계**: 접두사 규약 — `opal-pilot-*`(오케스트레이터), `op-dev-*`(dev 단계), `op-task-*`(범용 단계), `opal-{domain}-agent`(전문 워커).
- **구현 Guards**: 승인 전 코드 생성 금지, 커밋은 사용자 명시 요청 시에만, 디스패치 의무(워커 직접 대체 금지).
- **State 관리**: STATE.md 편집은 `state-tool run.sh`로만 수행 — LLM 직접 편집 절대 금지.

## 적용 범위

OPAL 소스 전체(`opal/`, `skills/`, `agents/`); 워커 에이전트가 코드/문서 작성 시 직접 참조.

## 참조

`file_path: docs/CONVENTIONS.md`
