---
type: entity
title: OPAL Console
tags:
- tool
- dashboard
- frontend
- backend
sources:
- task:021
- task:115
related:
- daemon-as-tool-orchestrator
- project-id-query-param-pattern
- deploy-artifact-verification-lesson
- opal-architecture
- brain-tool
- state-tool
source_ref: dashboard/
created: 2026-06-15
updated: '2026-09-12'
status: active
---
## 개요

로컬에서 OPAL로 작업하는 모든 프로젝트를 한 화면에서 조망하고 실행 흐름을 관찰하는 콘솔이다. 초기 형태는 FastAPI 데몬과 React 화면으로 구성된 읽기 전용 대시보드였고, 태스크 115에서는 Electron 기반 Workbench 목업으로 확장되어 Project 계층, TASK 조율, 실행 작업공간을 함께 검증한다.

## 설계 배경 (WHY)

여러 프로젝트의 태스크 현황·메모리·환경을 개별 CLI로 확인하는 불편을 줄이기 위해 OPAL Console이 출발했다. (근거: task:021)

태스크 115에서는 Pug·Blend·MAMS처럼 각자 PM과 TASK를 가진 독립 Project들을 다시 상위 Project로 묶어 Main PM이 조율하는 업무 구조를 목업으로 확정했다. (근거: task:115)

TaskGroup, 별도 미니 프로젝트 엔티티, 평면 Project 선택기는 실제 사용자가 원하는 책임 경계와 맞지 않아 제거하고, Project 계층과 TASK 단일 모델로 정리했다. (근거: task:115)

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
- 초기 5화면: 대시보드 / 프로젝트 / 태스크 칸반 / 메모리 / 환경(doctor)
- Workbench: Project 트리 / TASK / PM Coordination Surface / Agent Terminal / 독립 Terminal / Files / Changes
- 전역 `contextProject` (Zustand) — 프로젝트 스위처와 5화면이 구독
- 디자인 토큰: `:root` 시그니처 3색 (`--brand-primary/secondary/tertiary`)
- 공통 `MarkdownView`: prose + @header 아코디언 + TOC

## Workbench 모델

Project는 PM·TASK·문서·의사결정의 책임 경계다. Project는 자체 관리 repo와 PM Agent를 가지며, 부모가 없는 최상위 Project이거나 다른 Project의 자식일 수 있다.

단순 Project와 복합 Project는 고정 타입이 아니라 자식 Project 존재 여부로 파생된다. 복합 Project 안에는 다시 복합 Project를 둘 수 있고, 정본 부모는 하나만 허용한다.

Repository Component는 Project가 관리하는 실제 코드 repo 또는 monorepo 내부 영역이다. Component는 독립 PM·TASK·의사결정을 갖지 않으며, Project의 작업 대상 범위를 구분하는 단위다.

모든 업무 단위는 TASK 하나로 통일한다. 업무 규모와 수행 방식은 TASK의 Pilot 속성으로 표현하고, `oppl`·`opsdd` 같은 대형 수행도 Project 트리의 별도 엔티티로 펼치지 않는다.

## Execution Workspace

Execution Workspace는 선택한 TASK를 수행·조율·관찰하는 중앙 작업영역이다. TASK별 PM Coordination Room, Sub PM Workspace, Worker Agent Terminal, 사용자가 직접 조작하는 독립 Terminal을 동적 탭과 split pane으로 배치한다.

조율 TASK마다 하나의 PM Coordination Room을 만든다. 사용자는 Main PM에게만 지시하고, Main PM은 필요한 Sub PM을 Room에 초대해 업무를 배정한다.

Sub PM 초대는 Room 참여자와 Sub PM Workspace Terminal을 함께 만든다. Sub PM이 Worker Agent를 호출하면 부모 PM과 연결된 관찰 전용 Worker Terminal이 생성되고, 사용자는 이 터미널에 직접 입력하지 않는다.

Main PM Room에는 원시 실행 로그가 아니라 하위 TASK의 상태, 블로커, 결정, 결과 요약만 상향된다. Main PM의 최종 통합 판단과 각 Sub PM의 개별 결과는 구분해 보여준다.

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
- [[brain-tool]]
- [[state-tool]]
