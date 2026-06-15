---
type: concept
title: 절대경로 프로젝트 식별자를 query param으로 전달
tags: [api, routing, url-design]
sources: [task:021]
related: [opal-console, daemon-as-tool-orchestrator]
created: 2026-06-15
updated: 2026-06-15
status: active
---

## 개요

OPAL Console에서 프로젝트 식별자(절대경로)를 URL에 포함할 때 path segment 대신 **query param**으로 전달한다. 슬래시(`/`)가 포함된 절대경로를 path segment에 넣으면 라우터가 다중 세그먼트로 인식하여 매칭에 실패하기 때문이다.

## 결정 배경 (WHY)

프로젝트 식별자는 `/Volumes/Data/AIStudio/workspace/ai-framework`처럼 OS 절대경로다. 이를 FastAPI/React Router path segment에 넣으면 슬래시 인코딩 문제로 라우팅이 깨진다. 실제로 태스크 021 동작검증에서 path segment 방식 시도 시 404 및 매칭 실패가 발생했다.

## 결정 내용

- 프로젝트 조회 API: `/api/tasks?project=<절대경로>`, `/api/memory?project=<절대경로>`
- FE 라우팅: `/tasks?project=<절대경로>` (React Router query string)
- path parameter 방식 (`/api/projects/{id}`) 에서는 인코딩된 짧은 ID 또는 인덱스 기반 참조를 사용

## 영향 범위

- `dashboard/backend/routers/tasks.py`, `memory.py`, `doctor.py` — query param 수신
- `dashboard/frontend/src/pages/*/` — useSearchParams() 또는 Zustand contextProject 구독

## 관련 페이지

- [[opal-console]]
- [[daemon-as-tool-orchestrator]]
