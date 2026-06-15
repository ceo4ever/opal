---
type: entity
title: OPAL Console
tags: [tool, dashboard, frontend, backend]
sources: [task:021]
related: [opal-architecture, brain-tool, state-tool]
source_ref: dashboard/
created: 2026-06-15
updated: 2026-06-15
status: active
---

## 개요

로컬에서 OPAL로 작업하는 모든 프로젝트를 한 웹 화면에서 조망하는 **읽기 전용 대시보드**. FastAPI 데몬이 OPAL 도구의 read-only 커맨드와 마크다운 파서로 데이터를 수집하고, React+shadcn/ui가 5개 화면을 렌더한다.

## 설계 배경 (WHY)

여러 프로젝트의 태스크 현황·메모리·환경(doctor)을 개별 CLI로 확인하는 불편을 해소하기 위해 구축. 1차는 전체 뷰어(읽기 전용)로 한정하고, 쓰기·편집·브레인 화면은 2차로 분리 (C-2, C-11).

## 구성

### 백엔드 (`dashboard/backend/`)
- **scanner.py**: `.opal/AGENT.md` 마커 스캔으로 OPAL 프로젝트 발견
- **adapters/**: read-only 도구 어댑터 5종 (`base`, `state`, `scan`, `skill`, `doctor`)
- **parsers/**: 마크다운 파서 4종 (`memory`, `memory_file`, `project`, `markdown_reader`)
- **routers/**: API 라우터 5종 (`dashboard`, `projects`, `tasks`, `memory`, `doctor`)
- **main.py**: FastAPI app, 127.0.0.1:7823 바인딩, SPA 정적 서빙
- **cache.py**: TTL 30초 + mtime 무효화 인메모리 캐시

### 프론트엔드 (`dashboard/frontend/`)
- React 19 + TypeScript + Vite + Tailwind 4 + shadcn/ui
- 5화면: 대시보드 / 프로젝트 / 태스크 칸반 / 메모리 / 환경(doctor)
- 전역 `contextProject` (Zustand) — 프로젝트 스위처와 5화면이 구독
- 디자인 토큰: `:root` 시그니처 3색 (`--brand-primary/secondary/tertiary`)
- 공통 `MarkdownView`: prose + @header 아코디언 + TOC

## 인터페이스

```
opal-cli console start    # 127.0.0.1:7823 기동
opal-cli console stop     # 종료
opal-cli console status   # /health 확인
opal-cli console open     # 브라우저 열기
```

- CLI 구현: `opal/tools/opal-cli/lib/console.sh`
- 배포 경로: `~/.opal/dashboard-server/` (install-mac.sh `install_dashboard()` 함수)
- 기본 포트: **7823**

## 관련 페이지

- [[daemon-as-tool-orchestrator]]
- [[project-id-query-param-pattern]]
- [[deploy-artifact-verification-lesson]]
- [[opal-architecture]]
