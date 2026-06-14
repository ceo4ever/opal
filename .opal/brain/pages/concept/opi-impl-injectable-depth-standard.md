---
type: concept
title: opi 문서 깊이 기준 — "구현 시 주입 가능 수준"
tags:
- opi
- opal-project-init
- docs-quality
- architecture-decision
sources:
- task:020
related: [[skill-opal-project-init]]
created: '2026-06-14'
updated: '2026-06-14'
status: active
---

## 개요

opi(`opal-project-init`)가 생성하는 프로젝트 문서의 목표 수준을 "WHERE(지도)" 수준에서 **"WHERE+HOW(맵과 나침반)"** 수준으로 정의한다. 구체적 기준: 이 문서만 읽고 해당 프로젝트 규약대로 새 도메인/API/화면을 구현할 수 있어야 한다.

## 결정 배경 (WHY)

기존 opi는 ARCHITECTURE.md에 시스템 구성·기술 스택·디렉토리 트리만 기술하고(WHERE만), 레이어 규칙·의존 방향·데이터 흐름·트랜잭션 경계·새 기능 추가 절차(HOW)가 없었다. 결과적으로 문서를 읽은 개발자가 구체적 구현 판단을 내릴 수 없었다.

정답지(`pointail/backend/docs/`): layer-rules · transaction-patterns · state-transitions · reviewer-checklist 등이 다이어그램+표+명령형 규칙+코드 예시+체크리스트로 HOW를 기술하는 구조 = "맵과 나침반"의 구체적 형태.

## 결정 내용

**[MUST] 작성 기준 문구** (docs-guide.md 각 문서 작성 규칙에 명문화):

> "각 HOW 섹션은 *구현 시 주입 가능 수준*으로 작성한다 — 이 문서만 읽고 해당 프로젝트 규약대로 새 도메인/API/화면을 구현할 수 있어야 한다. 추상적 서술('적절히 분리한다') 금지, 실제 코드에서 추출한 규칙·경로·패턴(예시 코드/표 포함)으로 기술한다."

ARCHITECTURE.md에 추가된 5종 HOW 섹션:
- `## 레이어 규칙 및 의존 방향` — 레이어 정의·책임·의존 방향 규칙
- `## 데이터 흐름 (요청 생명주기)` — 요청 진입→응답까지 경로
- `## 트랜잭션·상태 전이` — 트랜잭션 경계·상태 enum·전이 패턴
- `## 명명 규칙 (구조 차원)` — 레이어/모듈/엔티티 접두사 규칙
- `## 새 기능 추가 절차` — 새 도메인/API/화면 추가 step-by-step

## 영향 범위

- `opal/skills/opal-project-init/references/docs-guide.md` — 템플릿 심화
- 모든 opi 실행 프로젝트 산출 ARCHITECTURE.md/BACKEND.md/FRONTEND.md

## 관련 페이지

- [[skill-opal-project-init]]
- [[opi-v42-architecture-decisions]]
