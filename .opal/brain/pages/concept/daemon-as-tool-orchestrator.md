---
type: concept
title: 데몬은 도구 오케스트레이터 — 데이터 SSOT는 프로젝트 파일
tags: [architecture, dashboard, ssot]
sources: [task:021]
related: [opal-console, opal-architecture, opal-conventions]
created: 2026-06-15
updated: 2026-06-15
status: active
---

## 개요

OPAL Console 백엔드 데몬은 **도구 오케스트레이터** 역할만 수행한다. 새로운 데이터 저장소를 만들지 않고, 각 프로젝트 파일(`state.json`, `MEMORY.md`, `tasks/*/` 등)이 데이터 SSOT로 유지된다. (PLAN C-9)

## 결정 배경 (WHY)

데몬이 별도 DB나 캐시 파일을 데이터 SSOT로 삼으면 두 개의 진실 원천이 생겨 동기화 문제가 발생한다. 로컬 OPAL 환경에서는 각 도구(state-tool, code-scan, skill-registry 등)가 이미 정규화된 데이터를 관리하므로, 데몬은 그것을 읽어 화면에 제공하는 역할로 한정하는 것이 가장 단순하다.

## 결정 내용

- 데몬은 OPAL 도구의 **read-only 커맨드만** 래핑하는 어댑터 계층을 사용한다
- 데몬은 프로젝트 파일을 **변형·이동·캐시 오염시키지 않는다** (open(read)만)
- 쓰기 커맨드(`init`, `advance`, `mark`, `add-page` 등)는 1차 뷰어에서 **절대 호출 금지**
- TTL 캐시(30초 + mtime 무효화)는 성능 캐시일 뿐 — SSOT는 항상 원본 파일

## 영향 범위

- `dashboard/backend/adapters/` — read-only 어댑터 5종
- `dashboard/backend/parsers/` — 마크다운 파서 4종
- 보안 검증: pytest에서 파일 mtime 불변 확인 (TS-301, TS-302)

## 관련 페이지

- [[opal-console]]
- [[opal-architecture]]
