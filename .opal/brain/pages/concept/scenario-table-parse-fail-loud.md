---
type: concept
title: 시나리오 표 파싱은 조용히 버리지 않고 거부한다
tags:
- test-tool
- determinism
- task
sources:
- task:151
related: [test-tool, silent-success-defect-class, scenario-goal-coverage-gate-loop]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

태스크 149에서 나온 FW 개선 후보 6건을 실제 계약·코드와 대조해 4건만 채택한 결정이다. 나머지 2건은 이미 의도된 계약이거나 표면이 제공되고 있어 제외했다(`tasks/151-260923-oppm-FW-검토개선-결정론화/DONE.md:5-7`).

## 핵심 결정

- 시나리오 커버리지 표를 만들 때 셀 안의 이스케이프된 세로선은 내용으로 보존하고, 선택 사항인 양끝 테두리 세로선이 없어도 시나리오 행으로 인식한다(`tasks/151-260923-oppm-FW-검토개선-결정론화/DONE.md:9-10`, `opal/tools/test-tool/lib/scenario.py`).
- 인식한 행의 열 수가 헤더와 다르면 조용히 버리지 않고 문제 행을 포함한 입력 오류로 거부한다. 이전에는 잘못된 행이 빠진 채 성공으로 오판됐다(`tasks/151-260923-oppm-FW-검토개선-결정론화/DONE.md:11-12`, `:33-34`).
- 작업본 루트의 조상 탐색과 허브 루트의 추론 금지가 서로 다른 계약임을 대칭적으로 명시하고, 테스트 집행 주장에는 레포 상대 경로와 정확한 심볼을 근거로 요구하며, PM Gate가 인용한 필수 규칙의 적용 대상을 현재 변경과 대조하게 했다(`tasks/151-260923-oppm-FW-검토개선-결정론화/DONE.md:13-16`).
- 1차 수정 뒤 독립 검증자가 테두리 없는 행 누락을 추가로 찾아냈다(`tasks/151-260923-oppm-FW-검토개선-결정론화/DONE.md:35-36`).

## 관련 페이지

- [[test-tool]]
- [[silent-success-defect-class]] — 조용한 성공 결함 유형
- [[scenario-goal-coverage-gate-loop]]
