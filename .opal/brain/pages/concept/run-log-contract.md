---
type: concept
title: 태스크 실행 로그 CONTRACT — 사건 스키마·인터페이스 계약
tags:
- run-log
- contract
- docs
sources:
- doc:docs/run-log/CONTRACT.md
related: [run-log-prd, run-log-trd, state-tool]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

태스크 실행 로그의 인터페이스 계약(사건 스키마·명령 시그니처·경계·기계검증절)을 확정하는 문서이며, 구현 전 명세 심판의 판정 기준 원천이다. 필드명·열거값·명령명을 직접 쓰는 것이 이 문서의 정상 형태이고, 기계가독 표면 인벤토리(`surfaces.json`)를 필수 구성요소로 포함한다(`docs/run-log/CONTRACT.md:4-9`, `docs/PROJECT.md:288`).

## 핵심 결정

- 모든 표준 사건은 사건 계약 버전, 사건·요청 식별자, 실행 전역 순번과 주체별 순번, UTC 밀리초 시각, 태스크·실행 식별자를 갖는다. 같은 실행 안에서 요청 식별자가 같으면 한 번만 기록되는 멱등 키가 된다(`docs/run-log/CONTRACT.md:19-31`).
- 실행 전역 순번은 기록 조각이 바뀌어도 리셋하지 않고, 로컬 시각 저장은 금지한다(`docs/run-log/CONTRACT.md:24-26`).
- 원인 관계는 직접 관계가 있을 때만 기록하고 추정하지 않으며, 참조 경로는 프로젝트 상대 경로만 허용한다(`docs/run-log/CONTRACT.md:31`, `:45`).
- 사건 종류는 14종 폐쇄 목록이고 종류별 추가 필수 조건을 둔다(`docs/run-log/CONTRACT.md:36`, `:91`).

## 관련 페이지

- [[run-log-prd]] · [[run-log-trd]]
- [[state-tool]]
